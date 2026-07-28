# Worker 3 adversarial review — spec-065 review round 2

Reviewer: Worker 3 (isolated from all three builder cohorts).
Subject: the combined round-2 tree — `docs/builder/bld-review-2-ws_revocation.md`,
`bld-review-2-http_boundary.md`, `bld-review-2-ws_host_boundary.md`, against `docs/feedback.md`
(round-2 maintainer review) and `docs/spec-065-transport_security-0_0_15.md`.

Status: **revision-needed** — five Medium findings (three from the primary pass, two from the
obligations `worker-3.md` / `BUILD.md` gained mid-pass; see the Addendum), one of which reopens the
round's own High 2 in a deployment the shipped code documents itself as covering.

Baseline reproduced myself: `uv run pytest --no-cov` = **5072 passed, 40 skipped**;
`tests/test_routers.py` + `tests/test_views.py` = 240 passed; `ruff format --check` = 380 files
already formatted; `ruff check` = All checks passed; `git diff --check` clean.
`scripts/check_trailing_commas.py --check` reports 2 violations, both in `drys.md` / `vulns.md`
(maintainer files, out of this round's scope and untouched).

Method: source reading against the installed Django 6.0.5 / Strawberry 0.316.0 / Channels 4.3.2
sources, **23 independent production mutants** (every one anchored on an exact string, applied from
a pristine backup, reverted and `cmp`-verified), and five throwaway probes under
`docs/builder/temp-tests/review-2/` (gitignored). I did not run `--cov`. I ran no `git` command
that writes.

---

## Findings by severity

### Blocker

None.

### High

None.

### Medium

#### M1 — the multipart form-encoding gate lets a client-declared `charset` mask Django's real effective encoding, reopening review High 2

`django_strawberry_framework/views.py:225-226` (`_form_encoding_is_utf8`):

```python
declared = (request.content_params or {}).get("charset")
encoding = declared or request.encoding or settings.DEFAULT_CHARSET
```

The docstring at `views.py:196-198` claims these are "the three rungs ... read in the order Django
applies them". **Django applies no such order.** `MultiPartParser` is constructed at
`django/http/request.py::HttpRequest.parse_file_upload` #"MultiPartParser(META, post_data,
self.upload_handlers, self.encoding)", and `MultiPartParser.__init__` resolves
`encoding or settings.DEFAULT_CHARSET`. Django never re-reads `content_params` at parse time. The
declaration matters exactly once, at `HttpRequest._set_content_type_params`, which *promotes* a
**usable** charset onto `request.encoding` — so normally the two agree, and the package's `or`
chain is harmless.

They stop agreeing the moment a consumer middleware assigns `request.encoding`, which is Django's
documented per-request override and is the *only* justification the docstring gives for rung 2
existing at all (`views.py:207-209`). In that deployment Django decodes with the middleware's
value and the package validates the client's declaration instead — so the client picks which rung
is consulted.

Proved end to end at `docs/builder/temp-tests/review-2/test_encoding_rung_order.py::test_real_parse_confirms_the_bypass`
(PASSES, i.e. the bypass is real):

- request declares `charset=utf-8`; middleware sets `request.encoding = "iso-8859-1"`;
- `view._enforce_multipart_form_encoding(request)` **accepts**;
- `request.POST["operations"]` comes back with the raw `0xe9` decoded as latin-1 `é`, with **no
  `U+FFFD`**, so `_reject_lossy_multipart_control_fields` cannot see it either;
- a non-UTF-8-decoded control document reaches `json.loads`.

That is exactly `docs/feedback.md` High 2's "an `operations` field declared with
`charset=iso-8859-1` and carrying a raw Latin-1 byte executed successfully with HTTP `200`",
re-achievable behind one line of consumer middleware.

Not client-only: an *unusable* declared name leaves `request.encoding` at `None`, and rung 1
correctly refuses it (mutant `encoding-drop-declared-rung` → 3 failures, so that half is pinned).
So the trigger is a third-party middleware, which is why this is Medium rather than High.

**Recommended change.** Both conditions, joined with `and`, not `or`:

1. if a `charset` was declared at all, it must canonicalize to UTF-8 (this is what refuses the
   name Django silently dropped, and it is the only reason rung 1 exists); **and**
2. the effective encoding Django will actually use — `request.encoding or
   settings.DEFAULT_CHARSET`, verbatim what `parse_file_upload` hands over — must canonicalize to
   UTF-8.

Then correct the docstring: rung 1 is not "Django's order", it is a *second, independent*
condition that exists because Django's own fallback is what the package refuses to inherit.

**Test expectation.** `tests/test_views.py::test_an_undeclared_form_encoding_falls_through_request_encoding_to_default_charset`
(`tests/test_views.py:1610`) only ever sets `request.encoding` with **no** declared charset. Add
the combination row — declared `utf-8` **plus** `request.encoding = "iso-8859-1"` → `400` — and a
live sibling in `test_transport_api.py` behind a middleware that sets `request.encoding`, since
that is the deployment the contract claims.

#### M2 — the `run_task` guard's one production path has no test, and the recorded reason it has none is factually wrong

`django_strawberry_framework/consumers.py:404-406`:

```python
task = asyncio.current_task()
if task is not consumer.run_task:
    task.cancel()
```

`bld-review-2-ws_revocation.md` §6 and "Things the review did not mention" #5 record this as
untestable: *"which needs `max_subscriptions_per_connection` operations in flight and cannot be
reached through the router (it exposes no such knob)"*, and propose an injected-consumer row as
the only honest route.

No knob is needed. `strawberry/channels/handlers/ws_handler.py::GraphQLWSConsumer.__init__`
defaults `max_subscriptions_per_connection: int | None = **100**`, not `None`. 100 in-flight
operations plus one more reaches upstream's subscription-limit `error` frame
(`strawberry/subscriptions/protocols/graphql_transport_ws/handlers.py::BaseGraphQLTransportWSHandler.handle_subscribe`
#"Subscription limit reached", and the legacy twin in `graphql_ws/handlers.py::handle_start`),
which is sent from the connection's own `run_task` through `send_message` → `websocket.send_json`.

Proved at `docs/builder/temp-tests/review-2/test_runtask_guard_reachable.py` — **1 passed in
1.62s** against the shipped router with the shipped consumer. It asserts
`entered_from == [("error", True)]`, i.e. the outbound checkpoint was entered exactly once, with
an `error` frame, from `asyncio.current_task() is consumer.run_task`; that no frame reached the
wire; and that the socket closed `4403` / `"Forbidden"`. The whole path — suppression, revocation,
close, main-task branch — works. It simply has nothing pinning it.

So the guard is **not** dead code (rule requested: keep it), and no seam is missing. What is
missing is a row. Under AGENTS.md L4 and worker-3.md's gap-finding discipline, a production
security path whose only recorded justification for having no test is a false premise is a
Medium.

One honest caveat the row should record rather than over-claim: the guard's *direction* is not
observable in this harness. Mutant `no-runtask-guard` (unconditional `asyncio.current_task().cancel()`)
passes **all 104** shipped rows **and** my own probe, because `channels.testing`'s app future
absorbs the self-cancellation of `run_task`. The row therefore pins the *path* (suppression +
close on the limit frame), and the guard's rationale — not aborting the disconnect/shutdown path
that has to cancel and await the remaining operations — stays a production-reasoning claim, which
the code comment at `consumers.py:398-403` already states correctly. Say so in the row's docstring
so a later reader does not delete the guard on the strength of a green suite.

**Test expectation.** One row per protocol: 100 controlled in-flight operations, a revalidation
instrumented to invalidate on the read that the 101st operation's *outbound* checkpoint takes
(admission read 101 still valid), then assert no `error` frame on the wire, the `4403` /
`"Forbidden"` close, and that the checkpoint was entered from `consumer.run_task`. My probe file
is the working shape and should be promoted.

#### M3 — the Host projection's no-`server` fallback is a fail-closed default with zero behavioral pinning (the round-1 defect shape, again)

`django_strawberry_framework/consumers.py:720-722`:

```python
else:
    request.META["SERVER_NAME"] = "unknown"
    request.META["SERVER_PORT"] = "0"
```

This else-arm is what decides the verdict for a handshake carrying **no** `Host`, **no**
`X-Forwarded-Host` and **no** `scope["server"]` — the exact shape
`channels.testing.WebsocketCommunicator` produces by default, and the shape a non-conformant ASGI
server can produce. Today it is correct: `_get_raw_host` reconstructs `"unknown"` (port `0 != 80`,
so `"unknown:0"`), `split_domain_port` yields domain `"unknown"`, `validate_host` refuses, the
handshake is denied. Confirmed at
`docs/builder/temp-tests/review-2/test_host_fallback_gap.py::test_a_handshake_with_no_host_information_at_all_is_denied`
(passes), with the control connecting.

Mutant `server-fallback-permissive` — `"unknown"` → `"testserver"` (an allowed host in this test
environment) — **104 passed, 0 failed.** Nothing in the suite reads that value.

`bld-review-2-ws_host_boundary.md` §3.2 claims the arm is covered *"by every other WebSocket row
in the module (none carries a `server` key)"*. It is **executed** by them and **consulted** by
none: every one of those rows also supplies an allowed `Host` header, so `_get_raw_host` takes the
`HTTP_HOST` branch and `SERVER_NAME` is never read. That is statement coverage without behavioral
coverage — structurally the same blindness as round 1's `max(end - position, 0)`, which
`fail_under = 100` also could not see because the defect lived in an *expression*.

The builder's own §5 note 1 makes this worse, not better: it observes that the suite was blind to
the whole Host question because the communicator synthesizes no host information — and then the
one handshake shape that still carries no host information is the one left unpinned.

**Recommended change.** Add a row: a handshake with no `Host`, no `X-Forwarded-Host` and no
`scope["server"]` is **denied**, and the projection's reconstructed `SERVER_NAME` / `SERVER_PORT`
are asserted as `"unknown"` / `"0"` against `django/core/handlers/asgi.py::ASGIRequest.__init__`'s
own literals (the projection's stated contract). Note that `_django_http_host_verdict` cannot be
the oracle here — `RequestFactory` always installs `SERVER_NAME = "testserver"`, so the Django
side of that comparison cannot express "no server" (I hit this while writing the probe).

### Low

#### L1 — the multipart form-encoding gate is not GET-scoped, and the mixin docstring's "**GET.** A no-op" is now false

`views.py:450-465` (`_enforce_multipart_form_encoding`) has no method guard, while its sibling
`_enforce_request_body_limit` explicitly returns for GET (`views.py:440`). Both run from
`_enforce_request_boundary` (`views.py:424-425`).

Consequence, measured at
`docs/builder/temp-tests/review-2/test_get_multipart_content_type.py`: a plain
`GET /graphql/?query={__typename}` carrying a stray
`Content-Type: multipart/form-data; boundary=B; charset=iso-8859-1` is answered
**`400 Unable to parse request body as JSON`**, even though the view reads no body on GET, Django
never parses a form, and upstream would have served the query params. The control (same GET, no
header) is `200`.

That makes `views.py:355-356` false as written:

> **GET.** A no-op: the view reads no body on GET.

Direction is fail-closed, and the class of client that attaches a stale `Content-Type` to a GET is
narrow, so this is Low rather than Medium. Recommended: add `request.method == "GET"` to the
early return (or hoist one `is_multipart and method != "GET"` discriminator into
`_enforce_request_boundary`), and either way correct the GET sentence.

#### L2 — the CORRUPTED-stream `413` is silent server-side and carries a reason the package has just admitted it cannot substantiate

`_request_body.py:197-198` → `views.py:447-448`. See the Q3 ruling below for why the **status** is
defensible. The gap is that this is the only fail-closed path in the round that logs nothing:
`consumers.py:452-456` emits `logger.exception(...)` on its fail-closed revalidation, and the
package has a logger. A request that is not oversized receives
`"Request body exceeded the configured GraphQL request-body limit."` with no server-side record,
so an operator debugging it will hunt `MAX_REQUEST_BODY_BYTES` rather than the middleware or ASGI
server that installed an incoherent stream. Recommended: a `logger.warning` / `logger.exception`
at the `_Probe.CORRUPTED` site naming the probe outcome — server-side only, no wire change, which
keeps the non-attributability property intact.

#### L3 — `sends_under_lock` measures a whole-lock property, not "held by this task"

`tests/test_routers.py:860` records `consumer._revocation_lock.locked()`. That is a real
measurement of the production lock at the production call site (see Q1), but `locked()` is true
whenever *anyone* holds it. In the four rows that read it, no sibling contends, so it
discriminates; under contention a sibling that acquired the lock in the window the mutant opens
would satisfy the assertion and the row would pass on a regressed tree. Also worth recording: all
four failures under mutant `lock released before the send` come from this one assertion — there is
no second, independent discriminator. Recommended: keep the assertion, and add either
(a) a sibling-cannot-enter assertion on the same row, or (b) an explicit docstring line that this
is the assertion's known limit, so it is not later "strengthened" into something weaker.

#### L4 — `getattr(consumer, "revalidation_window", _DEFAULT_REVALIDATION_WINDOW)` is dead defensiveness at a security decision

`consumers.py:435`. `GraphQLWebSocketConsumer.__init__` (`consumers.py:642`) always assigns the
attribute before `super().__init__`, and the class is not exported, so the default can never be
taken. It is fail-*safe* (`0.0` = revalidate always), so this is not a fail-open — but it is a
`getattr` default on the one line that decides whether a session read happens, and if a future
refactor dropped the attribute the package would silently switch to "revalidate every checkpoint"
(a performance cliff, invisible to `fail_under = 100` because it lives in an expression).
Recommended: plain attribute access.

#### L5 — the DEBUG Host/Origin divergence is real and fail-closed, but nothing pins it

Confirmed at `docs/builder/temp-tests/review-2/test_debug_divergence.py` (3 passed). See Q6.
`test_the_debug_localhost_default_matches_djangos_own_websocket_side` covers `localhost` allowed /
`evil.example` refused; the divergent value (`sub.localhost`) is not exercised on either side.
Because the Host check is the *permissive* one there, a future change to the Origin wrapper would
open `sub.localhost` under `DEBUG` with no failing row. Recommended: one parametrized row
asserting Host-accepts / Origin-refuses / net-verdict-denies for `sub.localhost`.

#### L6 — "private" is true by `__all__` convention only, not in fact

`consumers.py:729` calls `DjangoWebSocketHostValidator` "A PRIVATE, package-owned ASGI middleware"
and `:744` "Not exported"; `consumers.py:586`'s `GraphQLWebSocketConsumer` is likewise
"deliberately **not** exported" (`consumers.py:100-104`). Both carry public names, so
`from django_strawberry_framework.consumers import DjangoWebSocketHostValidator` works, while
every other new symbol in the same factory (`_RevalidatingTransportWSHandler`,
`_RevalidatingGraphQLWSHandler`, `_RevocationGatedWebSocketAdapter`) is underscore-prefixed. The
public-surface check below passes (`__init__.py` unchanged, `routers.py::__all__` unchanged), so
this is naming consistency, not a leak — but the docstrings assert a stronger property than the
code carries.

#### L7 — the async CSRF-ordering row runs against repaired scaffolding; only the sync one runs against a shipped mount

`test_an_over_cap_multipart_request_is_refused_before_djangos_parser_runs`
(`examples/fakeshop/test_query/test_transport_api.py:1922`) deliberately drives fakeshop's real
`/graphql/` — correct, and the strongest available evidence. Its async twin
(`test_the_async_view_also_refuses_before_djangos_parser_runs`) drives
`_async_capped_multipart_view`, a probe mount decorated with
`_carrying_the_packages_csrf_mark` (`test_transport_api.py:196`), i.e. exactly the
`__dict__`-dropping wrapper shape that loses the ordering, repaired by copying the mark off the
package. That is honestly documented in the helper's docstring and there is no shipped async
fakeshop mount to use instead, so this is a note, not a defect: record it as a known asymmetry so
nobody later reads the async row as deployment-shape evidence.

#### L8 — `docs/README.md` still carries the two claims round-2 Blocker 1 was raised against, and both READMEs still describe two wrappers

Slice 5's fold-in is unbuilt, so this is not chargeable to this round — but the sentences are on
disk and are now false about shipped behavior, so they belong in the report:

- `docs/README.md:360` — "revalidates the session actor **before every operation**" (the
  admission-only framing the review called false);
- `docs/README.md:390` — "the freshness bound is the revalidation window rather than the
  connection lifetime" (the exact sentence `bld-review-2-ws_revocation.md` B1 identifies as false
  in **both** halves);
- `docs/README.md:128`, `:283`, `:390` — the WebSocket composition as two wrappers;
- `docs/README.md:316`, `:398` — "the router's origin defence is `AllowedHostsOriginValidator`,
  not a CSRF token" with no mention that `ALLOWED_HOSTS` is now enforced on the handshake `Host`
  too;
- `README.md:62` — same two-wrapper sentence.

Both builders flagged these (`ws_revocation` A8, `ws_host_boundary` D1-D5); recorded here so the
Slice 5 sweep has one list. I edited none of them.

Additionally: `examples/fakeshop/test_query/README.md` (assigned reading for this role) never
mentions `test_transport_api.py` at all — its sibling-suite inventory at line 15 predates it, and
the file grew ~880 lines this round. (`test_keyset_api.py`,
`test_single_parent_fastpath_api.py` and `test_optimizer_auto_api.py` are missing from the same
inventory, so the gap is pre-existing and wider than this card.) Slice 5.

### nits

- `views.py:445` and `views.py:462` each re-derive `request.content_type == _MULTIPART_CONTENT_TYPE`
  in adjacent methods called from the same `_enforce_request_boundary`. One discriminator computed
  once in `_enforce_request_boundary` and passed down would also make L1 a one-line fix.
- `routers.py:192` and `routers.py:251` both build `"The factory {describe_value(factory)} ..."`
  around the shared `_FACTORY_CONTRACT_HINT`; the shared part is already extracted, the residual
  duplication is two words. Not worth changing.

---

## The seven rulings

### Q1 — is the lock actually held through the send in production, and does the test genuinely pin placement?

**Yes to both, with one stated limit.**

Production: `consumers.py:392-396` is a single `async with consumer._revocation_lock:` whose body
runs the revoked-flag read, `await _actor_is_current(consumer)` (which reaches
`channels.auth.get_user` behind `database_sync_to_async`, i.e. an executor hop that *does*
suspend) and `await send(message)`. `send` is the adapter's `super().send_json`
(`consumers.py:583`) → `ChannelsWebSocketAdapter.send_json` → `self.ws_consumer.send(...)` →
Channels' `AsyncConsumer.send` → `base_send`. On a real ASGI server that is a transport write and
suspends. So the critical section genuinely spans an await that can suspend, and the interleaving
the design closes (sibling A passes validation, sibling B observes revocation and closes, A emits
anyway) is genuinely closed.

I tried to falsify it four ways:

- **Deadlock/re-entry.** `_revoke_connection` (`consumers.py:476-493`) is awaited *inside* the
  lock and calls `websocket.close()` → `consumer.close()` → `base_send`. It never re-enters
  `send_json`, so no self-deadlock. The keep-alive `ka` and every control frame bypass the lock
  entirely (`consumers.py:580-582`), so a stalled protected send cannot starve the connection's
  own liveness frames.
- **Cancellation inside the critical section.** `_actor_is_current` catches `Exception`, not
  `BaseException` (`consumers.py:445-451`), so a `CancelledError` delivered during the session read
  propagates and `async with` releases the lock in its `__aexit__`. No stuck lock.
- **`send` raising.** Propagates with the lock released and `_revocation_observed` already `True`,
  so every later checkpoint denies. Fail-closed.
- **Second connection.** The lock is per-instance (`consumers.py:643`) and Channels builds one
  consumer per connection, so blast radius is one socket. Pinned by
  `test_the_connection_lock_never_serializes_a_second_connection`.

Test strength: `_record_outbound_gate` (`tests/test_routers.py:830-866`) monkeypatches the
module-global `send_revalidated_operation_frame`, wraps the checkpoint's **own** `send` argument,
and records `consumer._revocation_lock.locked()` at the instant the *production* code invokes it,
then delegates to the real function. So it is a measurement of the real lock at the real call
site — **not** an assertion the production code volunteers; nothing in `consumers.py` records or
exposes lock state.

I re-ran the mutant. `lock released after validation, before the send` → **4 failed**
(`..._keeps_a_running_subscription_emitting_every_result[graphql-transport-ws]`,
`[graphql-ws]`, `..._never_serializes_a_second_connection`,
`..._control_frames_never_reach_the_outbound_checkpoint`), all with `assert [False] == [True]`.
More than the 2 the builder reported, and it genuinely bites.

Limit, recorded as **L3**: every one of those four failures is the *same* assertion, and
`Lock.locked()` is a property of the lock rather than of the holder, so the pin is single-source
and would be satisfiable by a contending sibling. Adequate, worth documenting as the assertion's
known edge.

### Q2 — is the `task is not consumer.run_task` guard dead code, or a real path needing a seam?

**A real path. No seam is needed, and it is testable today.** See **M2**. Upstream's
`max_subscriptions_per_connection` defaults to **100**, not `None`, so the shipped router reaches
the subscription-limit `error` frame from `run_task` with 101 operations and no injected consumer.
I built the row: 1 passed in 1.62s, asserting `entered_from == [("error", True)]`, no frame on the
wire, `4403` / `"Forbidden"`. The guard stays; the row must be added; "leave it untested" is
correctly rejected, and the recorded reason for leaving it untested is false.

Secondary ruling: a row on that path pins the *path*, not the guard's *direction* — mutant
`no-runtask-guard` passes all 104 shipped rows and my probe, because `channels.testing` absorbs a
self-cancelled `run_task`. Do not let that turn into an argument for deleting the guard; the
production consequence (aborting the disconnect/shutdown path that must cancel and await the
remaining operations, and surfacing `CancelledError` out of the ASGI application) is real and
`consumers.py:398-403` states it correctly.

### Q3 — is `413` the right answer for a corrupted-position stream?

**The status is defensible; the silence is not.**

For the status: the package's own doctrine on this endpoint is non-attributability — Decision 9's
whole point, and the reason `_JSON_PARSE_REASON` is upstream's literal reproduced verbatim
(`views.py:102-113`). Introducing a *third* status for "the probe moved a stream it could not
prove it put back" would hand a caller a discriminator for an internal condition, which is the one
thing the rest of the boundary refuses to do. `500` was the other candidate and is worse:
`_request_body.py:92-96` deliberately commits to reporting a stream failure as a `bool` in the
fail-closed direction precisely so this module cannot turn an unusual stream into an unrelated
`500`, and a `500` also converts a bounded refusal into an exception the consumer's error handling
has to absorb. `400` would be a lie about the client. `413` is the package's own controlled
rejection, and it is reached without reading a byte — which is the property that matters.

The honest cost, and it is real: a request that is not oversized is told it is. Recorded as **L2**;
the fix is not the status but a server-side log record at the `_Probe.CORRUPTED` site, matching
what `consumers.py:452` already does for the WebSocket fail-closed path. Wire behavior stays
identical.

Falsification attempts: mutant `corrupted-fail-open` (`return True` → `return False`) → 4 failed;
`restore-unverified` (drop the verifying `tell()`) → 2 failed; `probe-zero-fail-open` (restore
round 1's fail-open shape) → 4 failed; `seekable-raise-fail-open` → 2 failed. The three-state model
is properly pinned in both directions.

### Q4 — the `csrf_exempt` `__dict__` footgun

**The claim is true: protection is never lost. The mechanism is what it says it is, and a system
check is the root-cause answer for the ordering — but the residual exposure is narrow enough that
this is Low.**

Verified, not assumed:

- `django/middleware/csrf.py:414-415` — `process_view` returns immediately on
  `getattr(request, "csrf_processing_done", False)`, which `_accept` sets at `:206`. So with the
  global middleware present and the mark lost, CSRF runs as middleware first (and rejects there if
  it fails), and the view's own `csrf_protect` short-circuits. Protection intact.
- With the global middleware **absent** and the mark lost, the view's own `csrf_protect` is the
  only check and it runs. Protection intact. Pinned by
  `test_the_endpoint_stays_csrf_protected_with_the_global_middleware_removed`, which fails under
  both `no-csrf-reentry-sync` (4 failures) and `no-csrf-reentry-async` (2 failures).
- Dropping the mark (`no-csrf-exempt`) fails 2 rows plus errors the whole live module at import —
  the mark's presence is pinned.
- The exposure is narrower than the docstring implies: `functools.wraps` copies `__dict__`
  (`WRAPPER_UPDATES = ('__dict__',)`), and every Django view decorator uses it, so
  `login_required(...)`, `ensure_csrf_cookie(...)` and a consumer subclass overriding `dispatch`
  all keep the mark. Only a **hand-written non-`wraps` wrapper** loses it. Notably, every probe
  mount in `test_transport_api.py` is exactly that shape, which is why
  `_carrying_the_packages_csrf_mark` exists — so the footgun is real enough that the round's own
  tests tripped it.

Ruling: **documentation is what shipped and it is accurate and complete** (`views.py:636-645`
names the shape, the loss, and the retained protection). A Django system check is nonetheless the
right root-cause answer and the one `docs/feedback.md` High 3 itself proposed — the failure mode is
*silent* and the property it silently drops is the entire subject of Decision 18. A
`register(Tags.urls)` check can walk the resolver and warn when a callback whose `view_class` is a
package view lacks `csrf_exempt`, without rebuilding any part of Django's stack. Because protection
is verifiably never lost, I do not hold the round open for it: record it as a follow-up rather than
a remediation, and do not "fix" it by changing the mechanism — no attribute-based mechanism can
survive an arbitrary wrapper, and the alternatives (stamping `dispatch`, a middleware) are strictly
worse or were already rejected.

### Q5 — did the unified close silently drop coverage?

**No. Every deletion is unreachable, and no assertion got weaker.**

Deletions verified by grep over the whole tree (excluding `.venv` and the builder artifacts):
`_REVOKED_SESSION_MESSAGE`, `_REVOKED_SUBSTRING`, `_assert_rejected` and `errors_as_list` survive
only in prose — `docs/builder/bld-slice-4-ws_revalidation.md` (historical),
`bld-review-1-w3_review.md` (historical) and `docs/spec-065-...md:2822` (custodian's, spec wording,
out of scope). No `graphql` import remains in `consumers.py` at any level; the module's only
non-stdlib module-level imports are `django.core.exceptions.DisallowedHost`, `django.http.HttpRequest`,
`. logger` and `.exceptions`, with `channels.auth.get_user`
(`consumers.py:520`), `.utils.sessions` (`:522`) and `channels.security.websocket.WebsocketDenier`
(`:772`) function-local. `revalidate_operation_actor` has exactly two callers, both in
`build_revalidating_consumer_class`, and neither passes an operation id.

Test-side, mechanically: exactly **one** `def test_` was removed
(`test_a_revoked_session_is_denied_on_the_next_operation_without_reconnecting`, renamed to
`..._closes_the_socket_...`) plus the `_assert_rejected` helper; 24 test functions were added; the
module went 84 → 104 collected. Reading the five rewritten rows against
`git show HEAD:tests/test_routers.py`:

| Row | What it asserted | What it asserts now |
|---|---|---|
| 26 `..._closes_the_socket_...` | `error` frame, id, list-vs-dict payload shape, revoked substring, stable third denial | `frames == []`, the exact `4403` / `"Forbidden"`, `reads == 2` (one per checkpoint), and a pipelined op 3 refused with **no extra read** and `not started.is_set()` |
| 28 `..._window_defers_the_denial_...` | `_assert_rejected(..., errors_as_list=True)` | the close, `frames == []`, **and `probe.reads == 1` across two complete operations** (four checkpoints on one read — the window's expanded meaning, which the old row could not express) |
| 29 `..._legacy_graphql_ws_...` | `_assert_rejected(..., errors_as_list=False)` | the close, `frames == []` |
| 30 `..._store_failure_denies...` | the error frame + the log record | the close, `frames == []`, **exactly one** `ERROR` record, `exc_info is not None`, and a third operation proving no read storm behind the revoked flag |
| 34 `..._real_second_request_logout...` | the error frame | the close; the request block extracted to `_logout_through_a_real_second_request` and reused by row 35 |

What was lost is the *subject*, not the strength: the per-protocol payload shape and the rejection
message no longer exist on the wire, and `message["id"] == op_id` scoping is meaningless for a
connection-level close. Every row gained at least one assertion it did not have.

Independent confirmation that the surviving rows still bite: `revoked-flag-never-set` → 5 failed;
`admission-revoked-check-dropped` → 4 failed; `gated-set-drop-error` → 3 failed;
`fail-open-revalidation-error` → 1 failed; `ack-guard-fail-open` → 1 failed;
`no-writeback` → 1 failed. One weak spot worth naming: `outbound-revoked-check-dropped`
(dropping the `not consumer._revocation_observed` short-circuit at `consumers.py:393`) fails only
**1** row, via `probe.reads == 3` — correctly so, because dropping it changes only the read count,
not the verdict. Adequately pinned.

### Q6 — the DEBUG divergence

**Confirmed, and the code handles it honestly and fail-closed.**

`django/http/request.py::HttpRequest.get_host` #"allowed_hosts = [\".localhost\", \"127.0.0.1\", \"[::1]\"]"
versus `channels/security/websocket.py::AllowedHostsOriginValidator`
#"allowed_hosts = [\"localhost\", \"127.0.0.1\", \"[::1]\"]" — Django's list carries the leading
dot, Channels' does not, and Channels' `match_allowed_origin` uses `is_same_domain`, which only
matches subdomains for a dot-prefixed pattern.

Measured at `docs/builder/temp-tests/review-2/test_debug_divergence.py` (3 passed) under
`DEBUG=True, ALLOWED_HOSTS=[]`:

- `_host_validation_request({"headers": [(b"host", b"sub.localhost")]}).get_host()` returns
  `"sub.localhost"` — **accepted** as a Host;
- `AllowedHostsOriginValidator(None).valid_origin(urlparse("http://sub.localhost"))` is `False` —
  **refused** as an Origin;
- a full handshake carrying both is **denied**; the `localhost` control connects; `evil.example`
  is refused on the Host side too.

Honest? Yes, in the code. Each check delegates to its own owner and the package reconciles nothing,
which is the stated design; the net verdict is the *stricter* of the two, so the divergence never
opens anything. `consumers.py:144-148` scopes its claim correctly ("the `DEBUG`-with-empty-`ALLOWED_HOSTS`
localhost defaults all stay exclusively Django's" — true of the **Host** decision, which is all
that sentence is about) and `:150-152` keeps Host and Origin explicitly separate. No code finding.
The misleading sentence is the spec's "one configuration, one matcher, two transports", which is
out of scope and already flagged by the builder as A3. Test gap recorded as **L5**.

### Q7 — independently re-run mutation claims

Every mutant applied from a pristine backup of the file, run, restored, and the restore verified
by `shasum` / `cmp`. Counts are against `tests/test_routers.py` (104) or
`tests/test_views.py` + `examples/fakeshop/test_query/test_transport_api.py` (240 → 201 for that
pair) as noted.

| Mutant | Claimed | Measured | Verdict |
|---|---|---|---|
| `websocket_adapter_class` removed from the generated consumer | 13 | **16 failed** | stronger than claimed |
| lock released after validation, before the send | 2 | **4 failed** | stronger, but single-assertion (L3) |
| `DjangoWebSocketHostValidator(...)` removed from the composition | 25 | **25 failed** | exact; ~10 behavioral, ~15 structural, as the builder itself broke down |
| `except DisallowedHost` → `except Exception` | 1 | **1 failed** (`test_only_disallowed_host_becomes_a_websocket_denial`) | weakly pinned but adequate — one row for one one-line semantic, and the row is precisely targeted |

Mutants I added, none of them claimed by any builder:

| Mutant | Failures | Note |
|---|---|---|
| `_measured_remaining` zero → fail-open (round-1 shape restored) | 4 | pinned |
| `_position_restored` returns `True` unverified | 2 | pinned |
| `_Probe.CORRUPTED` → allow | 4 | pinned |
| `seekable()` raising → treated as seekable | 2 | pinned |
| `_read_started` guard removed | 1 | pinned |
| `_enforce_multipart_form_encoding` no-op | 13 | strongly pinned, both transports, live + package |
| `_reject_lossy_multipart_control_fields` no-op | 8 | strongly pinned |
| `csrf_exempt` dropped from `as_view` | 2 + 8 collection errors | pinned |
| CSRF re-entry removed (sync) | 4 | pinned |
| CSRF re-entry removed (async) | 2 | pinned |
| declared-charset rung dropped | 3 | pinned |
| `request.encoding` rung dropped | 1 | pinned |
| `DEFAULT_CHARSET` rung dropped | 1 | pinned |
| declared-length gate removed | 4 | pinned |
| strict UTF-8 decode removed | 47 | pinned |
| `"error"` dropped from the gated set | 3 | pinned |
| fail-closed revalidation → fail-open | 1 | pinned |
| `connection_acknowledged` guard neutered | 1 | pinned |
| `scope["user"]` write-back removed | 1 | pinned |
| revoked flag never set | 5 | pinned |
| admission revoked-check dropped | 4 | pinned |
| outbound revoked-check dropped | 1 | read-count only; correct |
| `host` dropped from `_HOST_META_KEYS_BY_HEADER` | 41 | pinned |
| **`SERVER_NAME` fallback `"unknown"` → an allowed host** | **0** | **finding M3** |
| **`task is not consumer.run_task` guard removed** | **0** (and 0 against my own probe) | **finding M2 / the guard's direction is unobservable in this harness** |

Two zero-failure mutants out of 23. Both are recorded as findings.

---

## Fail-open hunt (the round-1 `max(end - position, 0)` shape)

Every fallback, `getattr` default, `or` chain and broad `except` in the four touched files, graded
on which direction it converts "cannot determine" into:

| Site | Shape | Direction |
|---|---|---|
| `consumers.py:435` | `getattr(..., _DEFAULT_REVALIDATION_WINDOW)` | safe (`0.0` = always revalidate) — but dead, **L4** |
| `consumers.py:440` | `scope.get(_REVALIDATED_AT_SCOPE_KEY, -math.inf)` | safe (reads as "never validated") |
| `consumers.py:432` | `actor is None or not actor.is_authenticated` → `True` | correct: no session actor to revoke; the router always applies `AuthMiddlewareStack` |
| `consumers.py:445-457` | `except Exception` → `refreshed = None` | fail-**closed**; `BaseException` deliberately not caught |
| `consumers.py:712` | `scope.get("headers", ())` | safe (no host info → the `"unknown"` reconstruction → denied) |
| `consumers.py:717-722` | `if server := ... else "unknown"/"0"` | fail-closed but **unpinned — M3** |
| `consumers.py:762` | `except DisallowedHost` only | correct; everything else propagates, which is the stated contract |
| `views.py:189-191` | `except (TypeError, ValueError)` → `None` | safe for non-multipart (falls to the counted read); for multipart it means **no cap at all**, which is Decision 7 step 3's decided and documented gap (`views.py:373-376`) |
| `views.py:226` | `declared or request.encoding or DEFAULT_CHARSET` | **fail-open — M1** |
| `views.py:229-230` | `except (LookupError, TypeError)` → `False` | fail-closed |
| `_request_body.py:194` | `stream is None or _read_started` → `False` | permits, but neither state is a size bypass: `HttpRequest.body` then raises `RawPostDataException` / `AttributeError`, so the request cannot be processed downstream either. Documented at `_request_body.py:183-189`. Accepted. |
| `_request_body.py:317-308` | `remaining <= 0` → `UNMEASURABLE` | the round-1 fix, and it holds (mutant → 4 failures) |
| `_request_body.py:322-328` | `_declares_seekable` returns `True` when `seekable` is absent | correct and load-bearing (Python 3.10 `SpooledTemporaryFile`); the coherence + verified-restore pair is what makes poking such a stream safe |
| `_request_body.py:290-306` | four `except Exception` guards | each routed by whether the position is known: `UNMEASURABLE` only when nothing moved or the restore was **verified**, `CORRUPTED` otherwise |

Rejection messages built from untrusted values all route through `exceptions.py::describe_value`
(`consumers.py:240`, `views.py:174-175`, `routers.py:192/240/251/292`) — the round-1 lesson is
held. The only `str()` of a foreign value is `str(server[1])` at `consumers.py:719`, a socket port
from the ASGI scope (server-side, bounded), not client-controlled.

Checks that run after the resource is consumed: none new. `_reject_lossy_multipart_control_fields`
necessarily runs after Django's decode — that is Decision 17's stated and correct boundary, and
the docstring at `views.py:490-502` names the escalation path (an upstream strict-field-decode
hook) rather than pretending otherwise.

---

## Concurrency review

- **Two operations, one socket.** Serialized by the per-connection lock; `test_the_connection_lock_stops_a_sibling_payload_escaping_after_revocation` records the sibling queuing at the lock, `locked()`, and zero reads of its own.
- **Two sockets.** Independent `_revocation_lock` / `_revocation_observed` per consumer instance; revoking socket 1 does not close socket 2, whose own next checkpoint fails validation. `test_the_connection_lock_never_serializes_a_second_connection` pins the blast radius.
- **Revocation racing teardown.** `_revoke_connection` sets the flag before awaiting the close (`consumers.py:492-493`), so a sibling acquiring the lock next takes neither a second read nor a second close. If `close()` raises (socket already gone), the flag is already set, the lock releases through `__aexit__`, and every later checkpoint denies — fail-closed.
- **Cancellation during the critical section.** `_actor_is_current` catches `Exception`, not `BaseException`, so a `CancelledError` from `cleanup_operation`/`shutdown` propagates and releases the lock. No path leaves the lock held.
- **Self-cancellation ordering.** `task.cancel()` is deliberately outside the lock (`consumers.py:404-406`), so the cancelled operation cannot be holding it while unwinding. Cancelling rather than raising means the `CancelledError` lands in `result_source.__anext__()`, so the subscription generator's `finally` runs — asserted via `controller.finalized`.
- **Re-entrancy.** No path inside the lock reaches `_RevocationGatedWebSocketAdapter.send_json`: the checkpoint is handed `super().send_json`, and `_revoke_connection` goes through `websocket.close()` → `consumer.close()`. Control frames (`complete`, acks, ping/pong, `ka`) bypass the lock entirely at `consumers.py:580-582`, so a stalled protected send cannot block the connection's liveness.

One consequence worth one sentence in `consumers.py` rather than left for a reader to derive: the
outbound gate prevents **disclosure**, not **execution** — a mutation admitted while the actor was
valid still runs to completion against the connection's actor, and only its result frame is
suppressed. `consumers.py:618-623` says "Detection is event-boundary-driven, not an asynchronous
promise to interrupt an idle resolver", which implies it; naming the mutation case makes it
explicit. (Informational, not a finding — this is the decided contract.)

---

## DRY review

Substantively clean. Cross-file constant-literal analysis over the four files (AST, docstrings
excluded) finds **zero** literals shared between them. The static helper reports `consumers.py`
2× (`SERVER_NAME`, `SERVER_PORT` — a dict key and its fallback assignment, irreducible),
`routers.py` 2× (`DjangoGraphQLProtocolRouter`, `"The factory"`), `views.py` 0, `_request_body.py`
0.

Near-copies I examined and am **not** flagging, with the reason:

- `handle_subscribe` / `handle_start` (`consumers.py:554-566`) — two two-line bodies differing only
  in the upstream method name they delegate to; the shared decision is already one function.
- the two admission call sites vs the outbound checkpoint — genuinely one shared decision
  (`_actor_is_current`) and one shared response (`_revoke_connection`); the split between
  `revalidate_operation_actor` and `send_revalidated_operation_frame` is forced by the fact that
  the latter must hold the lock **across** a `send` the former does not have.
- `DjangoGraphQLView.run` / `AsyncDjangoGraphQLView.run`, the two `parse_multipart` overrides, and
  `_run_after_csrf_check` / `_async_run_after_csrf_check` — sync/async duality; the async
  continuation exists because `csrf_protect` branches on `iscoroutinefunction(view_func)`, which I
  confirmed in `django/utils/decorators.py`. The *policy* lives once on the mixin in all three
  cases.
- `_JSON_PARSE_REASON` (`views.py:114`) duplicated as `_UPSTREAM_JSON_PARSE_REASON`
  (`_strawberry_patches.py:337`) — deliberate, with a lifecycle rationale (permanent package policy
  vs a retiring workaround) and a pinning test named in the comment. Pre-existing.
- the new Host projection against anything else resolving headers — nothing else in the package
  reads `scope["headers"]`, decodes latin-1, or builds `META` keys. `_host_validation_request` is
  the only such site.

The one duplication I do flag is a nit, not a build defect: the multipart discrimination computed
twice in adjacent mixin methods (see nits, and L1's fix folds into it).

---

## Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list
are unchanged; no spec authorization needed.

Round 2 added one class and one derived adapter. Neither leaked:
`routers.py::__all__` remains `("DjangoGraphQLProtocolRouter",)`; `DjangoWebSocketHostValidator` is
imported into `routers.py` for composition only and appears in no `__all__`;
`_RevocationGatedWebSocketAdapter`, `_RevalidatingTransportWSHandler` and
`_RevalidatingGraphQLWSHandler` are function-local classes inside
`build_revalidating_consumer_class` and unreachable by name from outside.

"Private in fact" holds for the three underscore-prefixed classes and holds only *by convention*
for `DjangoWebSocketHostValidator` and `GraphQLWebSocketConsumer`, both of which carry public names
while their docstrings assert privacy — recorded as **L6**.

---

## Documentation / release sanity

- **No staging language** in any of the four touched production files: zero hits for `TODO(`,
  "planned", "not yet", `Slice [0-9]`, `NotImplementedError`.
- **What a `docs/TREE.md` regenerate would pick up** (I did **not** regenerate):
  `consumers.py`'s rendered first line changes to *"The WebSocket Host boundary, the GraphQL
  consumer, and its two revalidation checkpoints."*; `routers.py`'s changes to *"Channels ASGI
  router: Django owns HTTP, the package composes WebSocket (spec-065)."*, replacing the stale
  spec-041 text currently on lines 207 and 316 of `TREE.md`; and **`consumers.py` and
  `_request_body.py` would be added as new rows — neither appears in `docs/TREE.md` at all today.**
  All four first lines are shipped-behavior descriptions with no staging language, so the
  regenerate is safe whenever Slice 5 runs.
- **Standing docs that are now false about shipped behavior**: recorded as **L8** (Slice 5's).
- `docs/GLOSSARY.md` / `docs/TREE.md` untouched, correctly (DB-generated / script-rendered).

## Static helper use

`uv run python scripts/review_inspect.py <file> --output-dir docs/shadow` run for all four files
that clear BUILD.md's 30-lines-of-new-logic bar: `consumers.py`, `views.py`, `_request_body.py`,
`routers.py`. None skipped. Outputs under `docs/shadow/` (gitignored, regenerable; the script owns
that folder per AGENTS.md L23).

The two sections flagged for attention:

- **Control-flow hotspots.** The densest new code is `_request_body.py::_measured_remaining`
  (10 branch nodes) and `consumers.py::_actor_is_current` (9). I walked every branch of both
  against a mutant; all are pinned except the ones recorded as findings. `views.py`'s hotspots are
  all docstring-dominated (`_run_after_csrf_check`: 82 lines, **0** branch nodes).
- **Repeated string literals.** Covered under DRY above; no cross-cohort literal duplication
  exists.

All line references in this artifact are original-source line numbers, never shadow lines.

## Temp test verification

Five probe files under `docs/builder/temp-tests/review-2/` (gitignored, per worker-3.md):

| File | Result | Disposition |
|---|---|---|
| `test_encoding_rung_order.py` | 2 passed / 1 failed — the failing row **is** the bug | **Promote** the combination row to `tests/test_views.py` + a live sibling (M1) |
| `test_runtask_guard_reachable.py` | 1 passed in 1.62s | **Promote** to `tests/test_routers.py`, both protocols (M2) |
| `test_host_fallback_gap.py` | 2 handshake rows passed (code correct); the projection row is the missing pin | **Promote** to `tests/test_routers.py` (M3) |
| `test_debug_divergence.py` | 3 passed | **Promote** the `sub.localhost` row (L5) |
| `test_get_multipart_content_type.py` | 1 passed / 1 failed — the failing row **is** the over-refusal | **Promote** after the L1 fix, as the GET carve-out's regression |

None of these is left as the only proof of shipped behavior; each maps to a recorded finding whose
remediation includes a permanent row.

## What looks solid

- **The `websocket_adapter_class` seam** is the right one and is used correctly: read off
  `base_consumer_cls`, installed as a class attribute on the generated consumer, never an instance
  patch, no upstream module imported. Verified against
  `strawberry/http/async_base_view.py:310` #"self.websocket_adapter_class(self, request, websocket_response)"
  and both protocol handlers' `send_message` funnel. Removing it fails 16 rows.
- **The gated set is exactly right.** `next` / `data` / `error` covers every information-bearing
  frame both handlers emit; `complete`, `connection_ack`, `connection_error`, `ping`, `pong`, `ka`
  are all connection-scoped or announce an ending, and `connection_error` cannot carry a
  post-revocation payload because it is only sent from `handle_connection_init`.
- **The unified close is the correct derivation, not a taste choice.** An admission-time `error`
  frame is itself a gated type, so it would be validated against the already-revoked actor and
  suppressed. That converts a style argument into a proof, and reusing upstream's own `4403` /
  `"Forbidden"` makes revocation wire-indistinguishable from every other refusal.
- **The Host boundary genuinely delegates.** I compared `_host_validation_request` item by item
  against `django/core/handlers/asgi.py::ASGIRequest.__init__`: casing normalization, latin-1
  decode, comma-join order, and the `scope["server"]` / `"unknown"` / `"0"` fallback all match, and
  the underscore-skip rule is reproduced *by construction* (matching exact names) rather than
  omitted. The two unprojected keys (`HTTP_X_FORWARDED_PORT`, `SECURE_PROXY_SSL_HEADER`) are
  provably verdict-neutral: both feed only `_get_raw_host`'s no-host branch, and only to decide a
  `":port"` suffix that `get_host()` strips via `split_domain_port` before matching. I also
  checked the one thing that would have been a crash — `_get_raw_host`'s no-host branch calls
  `is_secure()` → `scheme` → `_get_scheme()`, which on a bare `HttpRequest` returns `"http"`
  rather than raising, so the fallback path is sound.
- **Asserting against Django's own answer** (`_django_http_host_verdict` building a real
  `WSGIRequest` and calling `get_host()`) instead of a hand-typed expectation is the right test
  design for a delegating boundary — a hand-typed table would pass against a package-local
  reimplementation of `ALLOWED_HOSTS` matching, which is precisely what Decision 19 refuses to
  write.
- **The three-state probe.** Naming `UNMEASURABLE` vs `CORRUPTED` is the actual root-cause fix for
  round 1's collapsed sentinel, the restore is *verified* with a second `tell()` rather than
  inferred, and the deliberate behavior change (an over-reporting stream is now refused rather than
  silently handed to Strawberry as an empty body) is both correct and honestly recorded.
- **The CSRF re-entry.** Two module-level continuations decorated once at import, one long-lived
  `CsrfViewMiddleware` per transport, the ordering claim scoped correctly, and all three of its
  limits written into the code documentation rather than left emergent. The sync ordering row runs
  against fakeshop's real `/graphql/` mount with an upload-handler sentinel — that is the strongest
  form of evidence available for an ordering property, and `Client(enforce_csrf_checks=True)` with
  a real token means `process_view` genuinely wanted the form.
- **`controller.emitted` as the load-bearing observable.** Asserting that result 2 was *produced by
  the resolver* and never delivered is what distinguishes a suppressed payload from one that was
  never generated. Combined with `controller.finalized` for the generator's `finally`, these are
  the two observables that actually exist for this contract.
- **Floor discipline.** Both WS/HTTP cohorts re-ran at Python 3.10.19 / Django 5.2.0 /
  Strawberry 0.316.0 in isolated venvs, never the shared `.venv`. The projection carries no
  version-sensitive assertion by construction.

## Notes for Worker 1 (spec reconciliation)

The spec is being amended in a later pass, so I raise no spec-wording findings. Three items the
custodian will need that no builder can supply:

1. **M1's fix changes Decision 17's condition 1.** The amendment `bld-review-2-http_boundary.md`
   §1 proposes ("the declared top-level `charset`, else `request.encoding`, else
   `settings.DEFAULT_CHARSET`") describes the **shipped bug**, not the contract. Decision 17 should
   say: an accepted multipart request must satisfy *both* — any declared `charset` canonicalizes to
   UTF-8, **and** the effective encoding Django will use (`request.encoding or DEFAULT_CHARSET`,
   the pair `parse_file_upload` hands `MultiPartParser`) canonicalizes to UTF-8. Do not land that
   amendment as written.
2. **`bld-review-2-ws_revocation.md` §6 / note 5 must be corrected before it becomes spec prose.**
   "cannot be reached through the router (it exposes no such knob)" is false; upstream's default
   limit is 100. Any test-plan row derived from it would be built on the wrong premise.
3. **M3 needs a test-plan row of its own.** Decision 19's projection is described "item by item";
   the item that decides the no-host-information verdict currently has no behavioral row, and its
   value is not derivable from the spec (it is Django's ASGI adapter's literal). Name it.

## Review outcome

**revision-needed.** Round 2 is a large, genuinely good round: the two architectural gaps the
maintainer named (Blocker 1's running-subscription revocation, High 3's ordering) are closed with
the right seams rather than relabelled, the Host boundary calls Django instead of reimplementing
it, and the three-state probe is the root-cause fix for round 1's residual. 21 of my 23 mutants
failed, most of them hard.

It is not ready to close:

- **M1** reopens the round's own High 2 in the one deployment its docstring cites as the reason
  that code path exists, and the docstring's justification for it is factually wrong about Django.
- **M2** leaves a production security path with no test, on a stated premise that is false.
- **M3** leaves a security-boundary default with zero behavioral pinning, in exactly the shape
  round 1's worst defect took.
- **M4** and **M5** are the two findings the mid-pass role-file rewrite adds: twelve boundaries
  pinned by 0-1 rows, and a per-outbound-message serialization point landed with no number. See
  the Addendum.

None requires a redesign. M1 is an `or` → `and`; M2, M3 and most of M4 are rows (three of which I
have already written as probes and can be promoted); M5 is one measurement over an instrument that
already exists. One more remediation pass, then close.

---

## Tree integrity

The tree is byte-identical to how I found it apart from my artifact, my gitignored probe files, and
the `docs/shadow/` outputs the coordinator mandated (also gitignored, and regenerable — the script
owns that folder).

```
### tracked-file byte-identity (start-of-review backups vs live)
IDENTICAL django_strawberry_framework/consumers.py
IDENTICAL django_strawberry_framework/routers.py
IDENTICAL django_strawberry_framework/views.py
IDENTICAL django_strawberry_framework/_request_body.py

### git status --porcelain diff (start vs now)
(no differences)

### tracked-file hash diff (start vs now), excluding gitignored dirs
(no differences: every .py in the tree is byte-identical)

### public surface
$ git diff --stat -- django_strawberry_framework/__init__.py
(empty = unchanged)

### full suite, after every mutant was reverted
$ uv run pytest --no-cov -q
5072 passed, 40 skipped in 72.37s
```

**Mid-pass concurrent writes, not mine.** Five process documents appeared as modified during this
pass — `docs/builder/BUILD.md` (12:58), `docs/builder/worker-0.md` (12:59),
`worker-1.md` (12:59), `worker-2.md` (12:56) and `worker-3.md` (12:56). None carries an edit of
mine: I read `worker-3.md` and never opened `worker-0/1/2.md` (forbidden reads) or `BUILD.md` for
writing. They are the coordinator's own rewrite of the process docs, arriving while I was executing
mutants, and are treated as concurrent work per AGENTS.md L34. My two writes this pass are
`docs/builder/bld-review-2-w3_review.md` (this file) and an append to
`docs/builder/worker-memory/worker-3.md` (gitignored, mine by role).

Every one of the 23 mutations was applied from a pristine backup taken before the review began,
reverted by copying that backup back, and the revert verified by `shasum -a 256` (each batch) and
`cmp` (final). No `git commit`, `git add`, `git stash`, `git branch`, `git checkout`, `git switch`
or `git restore` was run. No file on the never-touch list was read for modification or written.

---

# Addendum — obligations added to `docs/builder/worker-3.md` and `BUILD.md` mid-pass

`docs/builder/worker-3.md` (12:56), `worker-0/1/2.md` (12:56-12:59) and `docs/builder/BUILD.md`
(12:58) were rewritten by the coordinator while this pass was running — after I had read the role
file and while I was executing mutants. None of those edits are mine (see Tree integrity). The
sections above were written against the earlier role file; everything below covers the obligations
the new one adds. Nothing above is retracted.

## Review-round duties: is each dispatched finding closed by a real bound?

Per the new `## Review-round duties`: the test is not "did code move", it is "name the input that is
now refused and was previously accepted".

| `docs/feedback.md` finding | Input now refused that was previously accepted | Real bound? |
|---|---|---|
| **Blocker 1** — revocation does not stop a running subscription | a `next` / `data` / operation-`error` frame whose actor no longer validates. Previously emitted; now suppressed and the socket closed `4403`. Verified: mutant removing the adapter fails 16 rows, and `controller.emitted` proves the resolver *produced* the payload that never reached the wire | **yes** |
| **High 2** — multipart `operations` / `map` bypass strict UTF-8 | (a) a multipart request whose effective form encoding is not UTF-8 — `charset=iso-8859-1`, `utf-16`, `utf-8-sig`, an unloadable codec name; (b) an `operations` / `map` value carrying `U+FFFD`. Both `400`. Mutants: 13 and 8 failures | **partially** — refused for the shapes the review probed, but **M1**: a client-declared `charset=utf-8` still masks a middleware-set `request.encoding`, so the Latin-1 direction the review actually demonstrated is re-achievable. Not closed. |
| **High 3** — the multipart cap runs after CSRF parsed the body | an over-declared-length multipart POST, refused with `413` **before** `handle_raw_input` / `new_file` / `receive_data_chunk` fire, under `Client(enforce_csrf_checks=True)` with a real token, against the shipped `/graphql/` mount. The upload sentinel is empty on the refusal and fires on the under-cap control — so the emptiness is evidence, not an absent instrument | **yes** — and this is an ordering bound, not a relabelled status: the `413` was already there before the round; what is new is *when* |
| **Medium 4** — `AllowedHostsOriginValidator` does not validate `Host` | a handshake with an allowed `Origin` and a `Host` Django's `get_host()` refuses. Previously connected (`(True, None)` in the review's probe); now denied by `WebsocketDenier`, before the auth stack and before consumer construction (two sentinels). Mutant removing the wrapper: 25 failures | **yes** |
| **Medium 5** — the broken-Strawberry hint advertises `>=0.262.0` | not a bound; a string. `routers.py:86` now says `>=0.316.0`, matching `pyproject.toml`, and `_STRAWBERRY_FLOOR_SUBSTRING` is a re-typed literal so drift fails loudly | **n/a — correctly closed** |
| **Low 6** — stream capability failures escape as raw errors | a stream whose `seekable()` / `tell()` / end-seek / restore fails, and a stream whose restore cannot be **verified**. Previously a `500` or a silent empty-body substitution; now `UNMEASURABLE` → bounded read, or `CORRUPTED` → the package's own `413`. Four mutants, 2-4 failures each | **yes** — a real change of answer, not a rename |

One finding not closed (**M1**), one closed but under-pinned (**Medium 4**, see M4 below), four closed.

## Failability-proof acceptance rule: the weakly-pinned census

The new `### Acceptance rule: weakly pinned is revision-needed` makes any boundary whose removal
fails 0 or 1 rows a blocker on acceptance. Recording the census literally, from the 23 mutants above
plus the three single-row mutants the WS-host builder reported and I did not re-run:

### 0 rows — nothing pins these at all

| Boundary | Mutation | Finding |
|---|---|---|
| `consumers.py:720-722` — the no-`server` `SERVER_NAME` fallback | `"unknown"` → an allowed host | **M3** |
| `consumers.py:405` — `task is not consumer.run_task` | guard removed | **M2** |

### 1 row — single-source pinning

| Boundary | Sole pinning row | Merit assessment |
|---|---|---|
| `consumers.py:762` `except DisallowedHost` (not `Exception`) | `test_only_disallowed_host_becomes_a_websocket_denial` | **needs a second row.** The single row monkeypatches the projection to raise `RuntimeError`. A second, *naturally occurring* shape exists and would be a better pin: a `scope["headers"]` entry whose name is `str` rather than `bytes` raises `AttributeError` inside `_host_validation_request`, which must propagate rather than read as a refused Host. |
| `views.py:226` rung 2 (`request.encoding`) **and** rung 3 (`DEFAULT_CHARSET`) | `test_an_undeclared_form_encoding_falls_through_request_encoding_to_default_charset` — **the same row pins both** | **worst case in the round.** Two independent rungs, one package-tier row, no live sibling. M1's fix restructures this function anyway; split into two rows plus one live row per rung. |
| `consumers.py:445-457` the fail-closed revalidation degrade | `test_a_revalidation_store_failure_denies_the_operation_and_is_logged` | **needs a second row.** This is the WS boundary's fail-closed direction pinned by one monkeypatch target (`utils/sessions.py::session_store_class`). Add a second failure shape — `channels.auth.get_user` raising — so the property is not pinned to one injection point. |
| `consumers.py:470` the `scope["user"]` write-back | `test_a_valid_session_keeps_executing_and_the_next_operation_sees_the_refreshed_actor` | acceptable on merit (one contract, one freshness probe reading two identity fields), but single-source. |
| `consumers.py:341-342` the `connection_acknowledged` guard | `test_a_subscribe_before_connection_init_is_closed_by_upstream_without_revalidating` | acceptable on merit — it is the only row asserting a pre-init client sees upstream's `4401`, and that is one narrow contract. |
| `_request_body.py:194` the `_read_started` deferral | `test_the_cap_defers_on_a_stream_some_other_component_already_consumed` | acceptable on merit — one documented deferral, one row. |
| `consumers.py:393` the outbound `_revocation_observed` short-circuit | `test_the_connection_lock_stops_a_sibling_payload_escaping_after_revocation` (via `probe.reads == 3`) | **correctly** single-row: dropping it changes only the read count, never the verdict. It is a read-storm guard, not a bound. |
| `views.py:225` rung 1 (declared charset) | 3 rows | not weakly pinned |
| `consumers.py:661` `x-forwarded-host` key | builder-reported 1 row (`..._x_forwarded_host_is_honoured_only_under_the_django_setting[True]`) | single-source |
| `consumers.py:716` the comma-join | builder-reported 1 row (`test_duplicate_and_odd_cased_host_headers_fail_closed`) | single-source, **and shared** with the next item |
| `consumers.py:713` the `.lower()` on the header name | builder-reported 1 row — **the same row** | single-source; two projection items, one row |

#### M4 (Medium) — the Host projection's four items and the two fail-closed directions are single-source pinned

Consolidating the table above into one actionable finding, because they share a cause: the Host
projection promises to reproduce `ASGIRequest.__init__` "item by item" (`consumers.py:668-687`), and
five of its items — the `host` key, the `x-forwarded-host` key, the comma-join, the `.lower()`, and
the no-`server` fallback — are pinned by **three rows between them**, one of which (M3) pins nothing.
Same shape on the HTTP side: two encoding rungs share one row. Recommended: one row per projection
item asserted against `ASGIRequest.__init__`'s own `META` output for the same scope (the module
already has `_django_http_host_verdict` as the *verdict* oracle; the projection needs a `META`
oracle beside it), and one row per encoding rung.

I am reporting these under the new rule rather than re-litigating merit: my own judgement is that
four of the twelve single-row boundaries (the two encoding rungs, the fail-closed degrade, and
`except DisallowedHost`) deserve a second row regardless of the rule, and the remaining eight are
adequate on merit. The maintainer owns whether the rule is applied literally.

## Hot-path budget

#### M5 (Medium) — the round added a per-connection serialization point to an outbound hot path with no number

`BUILD.md`'s new `## Hot-path budget` defines a hot path as one that runs "per request, per
resolver, per row, per connection, **or per outbound message**". `send_revalidated_operation_frame`
runs per outbound information-bearing message and now takes a connection-local lock **and holds it
across a session-store read**, so every concurrent operation waiting to emit on that socket queues
behind that read.

- `docs/builder/build-065-transport_security-0_0_15.md` carries **no hot-path declaration** (the
  requirement postdates the plan).
- `docs/builder/bld-review-2-ws_revocation.md` has **no `### Hot-path budget` subsection and no
  number**. §3.3 states the cost qualitatively and bounds its *blast radius* three ways by test row
  — one connection only, protected frames only, priced by the window — which is good engineering
  and is not a measurement.
- `docs/spec-065-transport_security-0_0_15.md:2166` and `consumers.py:67-77` both describe it as
  "a per-connection serialization point on the outbound hot path", i.e. the round is already aware
  it is one.

Per the rule I verify only that the number **exists**; it does not. Whether the trade is acceptable
is the maintainer's call and I take no position — the point is that it must not be accepted
silently, and right now it would be.

Reproducible metric available at no design cost, since the instrument already exists:
`tests/test_routers.py::_instrument_revalidation`'s `probe.reads` is a *count* on exactly this path.
A before/after pair of (session reads per N delivered frames, added awaits per protected frame)
over a stated iteration count would satisfy the rule without inventing a benchmark harness. Escalated
to Worker 1 below, because the plan's missing declaration is Worker 1's to add.

## The existence challenge

Raised, as required, for the two largest new abstractions.

**`DjangoWebSocketHostValidator` + `_host_validation_request` — must it exist?** *Yes, and in this
shape.* Deleting it and inlining nothing is not available: Django never sees the handshake, so with
it gone there is no owner for the Host question at all, and that is the finding it closes. The
narrower question — could it be a function instead of a class? — answers itself: Channels'
composition contract is `app = Wrapper(inner)`, so an ASGI middleware class is the shape. The
question worth recording is whether `_host_validation_request` should exist *separately* from the
validator's `__call__`, since it has exactly one caller. It should: it is the entire
package-owned half of the boundary and the only part with a compatibility contract against
`ASGIRequest.__init__`, so it is the unit that must be independently readable and independently
testable — and M4 asks for more tests against it, not fewer. Twelve lines of projection with sixty
lines of docstring is the correct ratio for a private-Django compatibility seam.

**`_Probe` (the enum) — must it exist?** *Yes.* This is the one abstraction in the round I would
normally challenge — a two-member enum for what a `bool` or two sentinels could carry. It survives
because the enum **is** the round-1 fix: the previous code collapsed "measure it by reading instead"
and "nothing may read this stream now" into one `None`, and that collapse was the fail-open. A
`bool` reintroduces it; two module-level `object()` sentinels would work but read worse at the three
comparison sites. Recorded as examined so it is not "simplified" back to a sentinel.

Third, smaller: `_INFORMATION_BEARING_FRAME_TYPES` as a named `frozenset` rather than an inline
tuple. It must exist, for a reason the builder states and I confirm: `ka` and the other control
frames have no behavioral row available, so the constant *is* their contract, and
`test_only_information_bearing_frames_reach_the_outbound_checkpoint` asserts it against a re-typed
literal set.

## Cross-cohort duplication review

The specific risk the new section names — "three cohorts independently added rejection paths and
controlled 400/413 responses to overlapping boundaries ... the set was three near-copies of one
shape" — **did not materialize this round**, and I checked it directly rather than assuming:

- HTTP cohort: 4 raise sites, 2 shapes (`HTTPException(400, _JSON_PARSE_REASON)`,
  `HTTPException(413, _BODY_LIMIT_REASON)`), both funnelling to constants declared once.
- WS-revocation cohort: 1 shape, `_revoke_connection` → `4403` / `"Forbidden"`, and it is explicitly
  the ONE response both checkpoints share.
- WS-host cohort: 1 shape, Channels' own `WebsocketDenier` — deliberately not package-authored, so
  a refused Host is byte-identical to a refused Origin.

Three transports, three rejections that cannot share a shape (an HTTP exception translated by
upstream's `dispatch`, a WebSocket close code, a Channels denier application). Each cohort correctly
reduced to one shape *within* its own boundary. The mechanical half agrees: zero string literals are
shared between the four touched files.

What the cohorts **did** converge on, and nobody could have seen from inside one cohort:

#### L9 — three fail-closed paths landed this round; one logs, two are silent

| Path | Server-side signal |
|---|---|
| `consumers.py:452-456` — revalidation read failed | `logger.exception(...)`, asserted by test |
| `consumers.py:772-774` — `Host` denied | **nothing** (builder's own A4 flags it as a maintainer decision) |
| `_request_body.py:197-198` → `views.py:448` — stream position corrupted | **nothing** (my L2) |

All three answer a client identically-by-design; none of them should change on the wire. But two of
the three leave an operator with a `1000` close or a false `413` and no record, while the third
establishes that the package is willing to log a fail-closed decision. That inconsistency is a
cross-cohort finding by construction: each builder made a locally defensible choice about its own
path and neither could see the third. Recommended: one decision for all three — I would log all
three at `warning` / `exception` with no wire change, which is what `consumers.py:452` already
demonstrates is acceptable to this package.

## Fixture-first check ("suspect the fixture before accepting untestable")

Applied, and it produced two of my three Mediums:

- **M2** — "cannot be reached through the router" was a claim about the code; the fixture-first
  question ("what does upstream actually default `max_subscriptions_per_connection` to?") answered
  it in one grep, and the path turned out to be a 1.6-second test.
- **M3** — the WS-host builder correctly applied this rule to *find* the Host gap
  (`WebsocketCommunicator` synthesizes no host information), and then left the one handshake shape
  that still carries no host information unpinned. The rule caught its own residue.
- Also checked and clean: the multipart rows do supply real raw multipart bodies (a hand-built
  builder, not `RequestFactory.post`, precisely so an unusable codec name can be expressed — see
  `tests/test_views.py:1560`'s docstring, which is correct about why `post` cannot); the CSRF rows do
  supply real tokens under `enforce_csrf_checks=True`; the stream rows do supply stand-ins that
  actually misbehave rather than mocks that assert they were called.

## Revised finding roll-up

| # | Severity | Finding |
|---|---|---|
| M1 | Medium | `_form_encoding_is_utf8` rung order reopens review High 2 behind a middleware-set `request.encoding`; docstring's "the order Django applies them" is false |
| M2 | Medium | the `run_task` guard's production path is untested and the recorded reason is false (upstream default is 100, not `None`) |
| M3 | Medium | the no-`server` `SERVER_NAME` fallback is unpinned (0-row mutant) — round-1's fail-open-expression shape |
| M4 | Medium | five Host-projection items and two encoding rungs are single-source pinned; four of them need a second row on merit |
| M5 | Medium | a per-outbound-message serialization point landed with no hot-path number, and the plan carries no hot-path declaration |
| L1-L8 | Low | as recorded above |
| L9 | Low | three fail-closed paths, one logs, two silent — cross-cohort inconsistency |
| nits | nit | duplicated multipart discrimination; `routers.py`'s two-word message overlap |

## Notes for Worker 1 (spec reconciliation) — additions

4. **Escalated: the plan needs a hot-path declaration, and this round owes a number.** `M5`.
   `build-065-...md`'s preamble predates `BUILD.md`'s `## Hot-path budget`; the WS-revocation slice
   meets the definition ("per outbound message", "per connection") and the spec itself already calls
   it a hot path at `:2166`. Resolution paths: (a) declare the slice hot-path and re-loop the
   cohort for a before/after number — `_instrument_revalidation`'s `probe.reads` is already the
   instrument, so this is cheap; or (b) record an explicit maintainer waiver naming the number as
   not-required for this card. Do not let it pass by omission.
5. **Escalated: whether the weakly-pinned rule is applied literally.** `M4`. Twelve boundaries in
   this round fail 0-1 rows. Two of them (M2, M3) are genuine gaps I would hold the round for on
   merit; four more deserve a second row on merit; the remaining six are adequate on merit and only
   fail the rule as written. Applying the rule literally re-loops all twelve. That is a process
   calibration decision, not a review finding, so it is yours.
