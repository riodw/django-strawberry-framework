# Builder artifact — review round 2, Medium 4 + Medium 5: the WebSocket Host boundary

Cohort: **WS host**. Files touched: `django_strawberry_framework/consumers.py`,
`django_strawberry_framework/routers.py`, `tests/test_routers.py`, and this artifact. Nothing
else was edited (see [Files I did not touch](#files-i-did-not-touch)).

Result: `uv run pytest tests/test_routers.py --no-cov` → **104 passed** (84 before this change,
+20 rows). Full suite `uv run pytest --no-cov` → **5072 passed, 40 skipped** (5051 / 40 before;
see [§7](#7-counts-and-the-delta) for the +1 that is not mine). `ruff format` / `ruff check` /
`scripts/check_trailing_commas.py --check` clean on all three files. The supported floor
(Python 3.10.19 + Django 5.2.0 + strawberry-graphql 0.316.0 + channels 4.3.2, isolated venv)
gives the **same 104 passed**.

## 1. What was wrong

**Medium 4.** `channels.security.websocket.OriginValidator.__call__` loops `scope["headers"]`
for `b"origin"` and reads nothing else; `AllowedHostsOriginValidator` is only a factory for
`OriginValidator(settings.ALLOWED_HOSTS)`. The name was never evidence of behavior. Meanwhile
`routers.py` and `spec-065` both promised that an injected consumer "cannot escape Host/Origin
validation" — so a handshake carrying `Origin: http://testserver` and `Host: evil.example`
connected, and nothing else in the WebSocket stack owned the question (Django never sees the
handshake at all, so unlike HTTP there was no second owner).

I re-confirmed the mechanism before building, and the shipped test suite's blind spot is
structural rather than accidental: `WebsocketCommunicator` synthesizes **no** `Host` header and
**no** `scope["server"]`, so before this change every WebSocket row in the repo drove a
handshake with no host information at all. There was no row that *could* have caught it.

**Medium 5.** `routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT` told the reader to install
`strawberry-graphql>=0.262.0`, which `pyproject.toml` (`>=0.316.0`) rejects and the minimum CI
matrix node (`strawberry: 0.316.0`) no longer runs. `tests/test_routers.py`'s
`_STRAWBERRY_FLOOR_SUBSTRING` deliberately pinned the stale text.

## 2. What I built

### 2.1 `consumers.py::DjangoWebSocketHostValidator` — a boundary that *calls* Django

| Symbol | Role |
| --- | --- |
| `consumers.py::_HOST_META_KEYS_BY_HEADER` | the two ASGI header names that participate, and the `META` keys `_get_raw_host` reads them under |
| `consumers.py::_host_validation_request(scope)` | the whole package-owned half: scope → minimal `HttpRequest` |
| `consumers.py::DjangoWebSocketHostValidator` | the ASGI middleware: call `get_host()`, delegate or deny |

- The package **parses and matches no hostnames**. `HttpRequest.get_host()` exclusively owns
  syntax checking, port removal, IPv4/IPv6, trailing dots, `ALLOWED_HOSTS`, wildcards, and the
  `DEBUG`-with-empty-`ALLOWED_HOSTS` localhost defaults. No new setting; WebSocket now follows
  the same Django configuration HTTP already follows.
- The projection reproduces `django/core/handlers/asgi.py::ASGIRequest.__init__` item by item
  for the headers it covers: name casing normalized rather than trusted, duplicates
  **comma-joined** (`#"join(value) for name"`), values decoded **Latin-1**, and
  `scope["server"]` → `SERVER_NAME` / `SERVER_PORT` with Django's own `"unknown"` / `"0"`
  fallback.
- A minimal `HttpRequest`, not an `ASGIRequest` — Decision 19's rejected alternative, for the
  reason it gives (`ASGIRequest.__init__` wants an HTTP scope and a body file).
- **Only `DisallowedHost`** becomes a denial. Every other exception propagates.
- The denial is Channels' own `WebsocketDenier`, imported function-locally in the denial arm, so
  a refused `Host` is byte-identical on the wire to a refused `Origin` (both close `1000`).
- `channels` stays absent from this module's import surface; Django is a hard dependency and its
  two names (`HttpRequest`, `DisallowedHost`) are imported at module level. The module docstring's
  dependency inventory was corrected accordingly.

### 2.2 `routers.py` — composition only

```python
"websocket": DjangoWebSocketHostValidator(
    AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter([re_path(websocket_url_pattern, websocket_application)])),
    ),
),
```

`routers.py` names the wrapper and implements no policy, which is the shape it already had for
the other two wrappers. Host **outside** Origin: Host answers which server authority was
addressed, so it runs before Channels' Origin check, before the session middleware, and before
any consumer is constructed.

### 2.3 The one thing I decided that the brief left open

**No log record on a Host denial.** Django's HTTP path logs `DisallowedHost` to
`django.security.DisallowedHost` via `django.core.handlers.exception`; Channels' Origin denial
logs nothing. Decision 19 says nothing about logging, and its explicit requirement is wire
*indistinguishability*, which logging does not affect. I therefore matched Channels' Origin
denial (silent) rather than Django's HTTP handler (logged), because adding an unrequested
observability surface to a fixed design is the maintainer's call, not a builder's. It is raised
as amendment **A4** below rather than built.

### 2.4 Medium 5

`_STRAWBERRY_CHANNELS_BROKEN_HINT` now says `strawberry-graphql>=0.316.0`, and
`tests/test_routers.py::_STRAWBERRY_FLOOR_SUBSTRING` moves with it (still a RE-TYPED literal, so
a future drift fails the test instead of asserting itself). **The `channels>=4.3.2` half of the
same hint is accurate** — I checked it against `pyproject.toml`'s `channels[daphne]>=4.3.2` dev
row, which is the floor the two other hints (`_CHANNELS_INSTALL_HINT`, `_CHANNELS_BROKEN_HINT`)
already name. No change there. `docs/SPECS/spec-041-channels_router-0_0_14.md` untouched, as
instructed.

## 3. Tests

All in `tests/test_routers.py`. Every row that asks *"which hosts are allowed"* asserts the
socket's verdict against **Django's own answer for the same value over HTTP** —
`_django_http_host_verdict` builds a real `WSGIRequest` through `RequestFactory` and calls
`HttpRequest.get_host()` on it — never against a second expectation typed out in the test. A
hand-written expectation would pass just as happily against a package-local reimplementation of
`ALLOWED_HOSTS` matching, which is precisely what Decision 19 refuses to write.

| Row | Spec row | Proves |
| --- | --- | --- |
| `test_the_websocket_host_and_origin_checks_are_independent` (×5) | 43 | the finding (allowed `Origin` + hostile `Host` → denied), its converse (hostile / missing `Origin` with an allowed `Host`), both-allowed, both-hostile; plus that every denial closes with the SAME code, so the two checks are indistinguishable on the wire |
| `test_django_owns_the_websocket_host_matching` (×7) | 44 | wildcard, leading-dot subdomain, explicit port, IPv6 literal, trailing dot, an RFC-forbidden underscore, and an empty header — each asserted `is (django_verdict is not None)` |
| `test_the_debug_localhost_default_matches_djangos_own_websocket_side` | 44 | `DEBUG` + empty `ALLOWED_HOSTS` (fakeshop's own shape): localhost allowed, `evil.example` still refused, both by delegation |
| `test_duplicate_and_odd_cased_host_headers_fail_closed` | 45 | Django's ASGI adapter's own `META["HTTP_HOST"]` is read to prove the joined form is `"a,b"`, that Django refuses it, that the socket is denied — and that a `Host:`-cased header still reaches the boundary |
| `test_x_forwarded_host_is_honoured_only_under_the_django_setting` (×2) | 46 | `USE_X_FORWARDED_HOST` on/off with the two headers deliberately DISAGREEING, matching HTTP either way |
| `test_with_no_host_header_the_scope_server_supplies_djangos_fallback` | 46 | `scope["server"]` is Django's normal fallback, allowed and hostile directions |
| `test_only_disallowed_host_becomes_a_websocket_denial` | 47 | a `RuntimeError` raised inside the projection propagates out of the ASGI application instead of being reported as a rejected host |
| `test_a_hostile_host_is_denied_before_the_auth_stack_and_the_consumer` | — (Decision 19 prose; no spec row — see **A5**) | two sentinels: `CookieMiddleware.__call__` (the auth stack's outermost layer, patched to record and DELEGATE) and an injected ASGI application. Both silent on a hostile `Host`, both fire on the control |
| `test_an_injected_consumer_is_denied_by_both_handshake_boundaries` | 28 + Decision 19 | the behavioral half of the injection-seam guarantee: hostile `Host` denied, hostile `Origin` denied, both-allowed reaches the injected app |

Existing rows changed (subjects preserved):

| Row | Change |
| --- | --- |
| `test_websocket_branch_wraps_origin_validator_outside_the_auth_stack` | both original assertions kept verbatim; the walk gains ONE outer unwrap (`unwrap_host_validator`), exactly as Decision 13 specifies |
| `test_an_injected_consumer_class_still_sits_inside_both_wrappers` | renamed `..._inside_all_three_wrappers`; same assertions through the new walk |
| `test_websocket_handshake_origin_directions` | the parametrized headers stay the ORIGIN directions; an allowed `Host` is appended so the outer check is not a second reason for the denial |
| `test_default_websocket_url_pattern_matches_exactly`, `_ws_communicator` | gained an allowed `Host` header (the communicator synthesizes none) |
| `_mounted_ws_callback`, `test_custom_websocket_url_pattern_...`, `test_schema_object_passes_through_unchanged...` | now walk through the shared `_ws_url_router` helper |

Machinery added: `unwrap_host_validator`, `_ws_url_router` (the one three-wrapper walk),
`_django_http_host_verdict` (the Django oracle), `_ws_handshake` (one handshake, returns
`(connected, detail)`, optional `scope["server"]`), `_recording_websocket_application` (the
consumer-side sentinel), `_DENIED_HANDSHAKE_CLOSE_CODE`.

### 3.1 Mutation testing (how I know the rows bite)

Every mutant was applied to the production code, measured, and reverted; the three files were
byte-compared against their pre-mutation copies afterwards, and the suite re-run green.

| Mutant | Result |
| --- | --- |
| `DjangoWebSocketHostValidator(...)` removed from the router composition | **25 failed** — 10 behavioral (`[hostile-host]`, `[malformed]`, `[empty]`, duplicate/cased, DEBUG, `USE_X_FORWARDED_HOST[False]`, `scope["server"]`, only-`DisallowedHost`, before-auth, injected-consumer) + 15 structural (the unwrap walk) |
| `except DisallowedHost:` widened to `except Exception:` | **1 failed** (`test_only_disallowed_host_becomes_a_websocket_denial`) |
| `x-forwarded-host` dropped from `_HOST_META_KEYS_BY_HEADER` | **1 failed** (`test_x_forwarded_host_is_honoured_only_under_the_django_setting[True]`) |
| comma-join replaced by last-value-wins | **1 failed** (`test_duplicate_and_odd_cased_host_headers_fail_closed`) |
| `.lower()` dropped from the header-name decode | **1 failed** (`test_duplicate_and_odd_cased_host_headers_fail_closed`) |

Worth stating plainly: the five *allowed*-direction rows of `test_django_owns_the_websocket_host_matching`
(wildcard, dot, port, IPv6, trailing dot) do **not** fail when the validator is removed, and that
is correct — their job is to prove the boundary does not over-refuse what Django accepts, which
a missing boundary trivially satisfies. The deny directions of the same delegation
(`[malformed]`, `[empty]`, plus `[hostile-host]` and the DEBUG row) are the ones that bite.

### 3.2 Coverage

I did not run `--cov` (per the brief). Statically, every statement added to `consumers.py` is
executed by the rows above, including both arms of the `scope["server"]` branch: the truthy arm
by `test_with_no_host_header_the_scope_server_supplies_djangos_fallback`, the `"unknown"` / `"0"`
arm by every other WebSocket row in the module (none carries a `server` key). No
`pragma: no cover` was added and none is needed.

## 4. The floor check

An isolated venv under the scratchpad (never the shared `.venv`):
`uv venv --python 3.10` + `uv pip install --python <path> django==5.2.0
strawberry-graphql==0.316.0 channels[daphne]>=4.3.2 …`. Reported versions: Python **3.10.19**,
Django **5.2**, strawberry-graphql **0.316.0**, channels **4.3.2**.
`python -m pytest tests/test_routers.py -o addopts="-q"` → **104 passed**, identical to the
current matrix (Python 3.14.2 / Django 6.0.5 / strawberry 0.316.0). Nothing in the projection is
version-sensitive by construction — every Django-behavior assertion is made against the Django
under test, so the rows cannot encode one version's answer.

## 5. Things the review did not mention that I found

1. **The suite could not have caught this, and the reason generalizes.**
   `channels.testing.WebsocketCommunicator` builds its scope from `path` + `headers` +
   `subprotocols` only: no `host` header, no `server` key. Every WebSocket row in the repo was
   therefore driving handshakes with zero host information. Any future check that reads a
   handshake header the communicator does not synthesize will be equally invisible until a row
   supplies it explicitly.
2. **`ALLOWED_HOSTS` and Channels' origin list are not the same list under `DEBUG`.** Django's
   empty-`ALLOWED_HOSTS` fallback is `[".localhost", "127.0.0.1", "[::1]"]`;
   `AllowedHostsOriginValidator`'s is `["localhost", "127.0.0.1", "[::1]"]` — no leading dot, so
   Django accepts `sub.localhost` as a Host while Channels rejects `http://sub.localhost` as an
   Origin. Delegating means the package inherits both behaviors rather than reconciling them,
   which is right, but it is a real asymmetry a reader of "one configuration, one matcher, two
   transports" would not expect. Amendment **A3**.
3. **Neither `USE_X_FORWARDED_PORT` nor `SECURE_PROXY_SSL_HEADER` can change the verdict.** Both
   feed only the no-host-header branch of `_get_raw_host`, and only to decide whether a `":port"`
   suffix is appended — which `get_host()` strips straight back off via `split_domain_port` before
   matching `ALLOWED_HOSTS` against the domain alone. So the projection omits them deliberately
   and provably, rather than by oversight. Recorded in the docstring so nobody "completes" the
   projection on symmetry grounds, and offered as amendment **A1**.
4. **`ASGIRequest` skips any header name containing `_`** ("prevent spoofing via ambiguity
   between underscores and hyphens"). The projection reaches the same outcome by construction —
   it matches the exact names `host` / `x-forwarded-host`, so `x_forwarded_host` simply never
   matches — which is why no underscore rule appears in it. Noted because its absence looks like
   a divergence from Django's adapter until you check.
5. **A Host denial is silent server-side**, whereas the same refusal on HTTP produces a
   `django.security.DisallowedHost` log record. See §2.3 and amendment **A4**.
6. **`docs/README.md` and `README.md` both describe the WebSocket composition as two wrappers.**
   Slice 5's files, listed in the amendments below so the custodian's sweep has them.

## 6. Files I did not touch

Confirmed with `git diff --stat`. The other dirty paths in the tree — `views.py`,
`_request_body.py`, `conf.py`, `auth/*`, `README.md`, `docs/README.md`, `docs/feedback.md`,
`docs/spec-065-*`, `docs/builder/build-065-*`, `TODAY.md`, `drys.md`, `vulns.md`,
`tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py` — are concurrent
maintainer / other-builder work and carry none of my edits. I ran no `git` command that writes.
`docs/GLOSSARY.md` and `docs/TREE.md` are script-generated and were not regenerated (Slice 5's
job); note that `consumers.py`'s docstring first line — the line
`scripts/build_tree_md.py` renders — **did** widen, to
`"The WebSocket Host boundary, the GraphQL consumer, and its two revalidation checkpoints."`

## 7. Counts and the delta

| Scope | Before | After | Delta |
| --- | --- | --- | --- |
| `tests/test_routers.py` | 84 passed | **104 passed** | +20, all mine |
| Full suite | 5051 passed, 40 skipped | **5072 passed, 40 skipped** | +21 |

The +21 against my +20 is one row I did not write. `tests/test_views.py` and
`examples/fakeshop/test_query/test_transport_api.py` were modified at 11:57 and 11:59 today by
the builder still active in those files, after the 5051 figure was recorded; I touched neither,
and `tests/test_routers.py` accounts for exactly +20 on its own. Skips are unchanged at 40.

## Required spec amendments

Checked against `docs/spec-065-transport_security-0_0_15.md` as of this writing. The custodian
had already written Decision 19, its checklist boxes, its edge cases and its test-plan rows
before I started, and I found **no sentence in the spec that my implementation makes false** —
everything below is incompleteness, or a divergence between the spec's prose and what the code
can actually be held to. I edited none of it.

### A. `docs/spec-065-transport_security-0_0_15.md`

**A1 — the projection's item-by-item list is missing the two `META` keys that are deliberately
NOT projected, and the reason they are verdict-neutral.** The list reads as exhaustive, so a
later reader "completing" it is the likely next edit.

- Current, `docs/spec-065-transport_security-0_0_15.md:2466`:
  > "- decode header bytes with the **Latin-1** Django/ASGI transport convention, the same codec
  > Django's adapter and Channels' `OriginValidator` both use."
- Recommended: keep, and add one bullet after it:
  > "- and deliberately project **nothing else**: `HTTP_X_FORWARDED_PORT`
  > (`USE_X_FORWARDED_PORT`, read by `HttpRequest.get_port`) and the header named by
  > `SECURE_PROXY_SSL_HEADER` (read by `HttpRequest.scheme`, answered by `is_secure()`) feed
  > **only** the no-host-header branch of `_get_raw_host`, and there they decide one thing:
  > whether the reconstructed host carries a `":port"` suffix. `get_host()` splits that suffix
  > straight back off (`split_domain_port`) and matches `ALLOWED_HOSTS` against the **domain**
  > alone, so neither setting can change the allow/deny outcome — only a string this boundary
  > discards. The omission is provably verdict-neutral, not an oversight."
- Why: without it, the honest-looking symmetry argument ("we honour `USE_X_FORWARDED_HOST`, so
  we should honour `USE_X_FORWARDED_PORT`") wins on its own, and the projection grows surface
  for no behavior. The reason is now in
  `consumers.py::_host_validation_request`; the spec should carry it too, because that is where
  the "item by item" promise is made.

**A2 — "the minimum `META` `get_host()` reads" should say which keys those are**, so the
projection is checkable against the spec rather than against Django's source.

- Current, `docs/spec-065-transport_security-0_0_15.md:2516`:
  > "The projection supplies the minimum `META` `get_host()` reads, which is a smaller and more
  > auditable compatibility surface than a request object built out of a scope it was not written
  > for."
- Recommended: > "The projection supplies the minimum `META` `get_host()` reads — `HTTP_HOST`,
  > `HTTP_X_FORWARDED_HOST`, `SERVER_NAME` and `SERVER_PORT`, and nothing else — which is a
  > smaller and more auditable compatibility surface than a request object built out of a scope it
  > was not written for."
- Why: four named keys is the whole compatibility surface, and naming them is what makes
  "auditable" true for a reader who does not have `django/http/request.py` open.

**A3 — the "one configuration, one matcher, two transports" claim is true for `ALLOWED_HOSTS`
and false for the `DEBUG` fallback, where Django's list and Channels' differ.**

- Current, `docs/spec-065-transport_security-0_0_15.md:2748` (Edge cases, `ALLOWED_HOSTS = []`
  with `DEBUG=True`):
  > "which is the point of delegating: one configuration, one matcher, two transports."
- Recommended: append: > "One caveat, because the two checks are separate and stay separate:
  > under `DEBUG` with an empty `ALLOWED_HOSTS`, Django's fallback list is
  > `[".localhost", "127.0.0.1", "[::1]"]` while `AllowedHostsOriginValidator`'s is
  > `["localhost", "127.0.0.1", "[::1]"]` — no leading dot. `sub.localhost` is therefore an
  > acceptable **Host** and an unacceptable **Origin** in a development configuration. The
  > package inherits both behaviors rather than reconciling them, which is what delegating means;
  > it is recorded here so the divergence is not later read as a projection bug."
- Why: the sentence invites a reader to expect one answer from two transports. In the one
  configuration where the two allowed-lists diverge, they get two — and the `DEBUG` row is the
  row the spec explicitly asks for.

**A4 — a Host denial is silent server-side, while the identical refusal on HTTP is logged.
Decision 19 should state the choice either way; I did not build a log line because the decision
did not ask for one.**

- Current, `docs/spec-065-transport_security-0_0_15.md:2474`:
  > "**Only `DisallowedHost` becomes a denial.** The validator catches `DisallowedHost` and
  > denies the handshake **before authentication and before the consumer is constructed**."
- Recommended: append: > "The denial is not logged, matching Channels' `Origin` denial rather
  > than Django's HTTP handler — which logs `DisallowedHost` to the `django.security.DisallowedHost`
  > logger from `django/core/handlers/exception.py`. Wire indistinguishability is a requirement;
  > server-side silence is not, and if a deployment needs the signal the honest home for it is a
  > package `logger.warning` in the denial arm (the shape `consumers.py`'s fail-closed
  > revalidation already uses), not a wire change."
- Why: this is the one place where "WebSocket now follows the same Django configuration already
  used by HTTP" is incomplete in a way an operator will notice — a handshake that closes with
  `1000` and no log entry is hard to diagnose. It is a maintainer decision, not a builder one, so
  it is flagged rather than built.

**A5 — the ordering requirement ("before authentication and before the consumer is
constructed") has no test-plan row, though it is the sharpest half of the decision.**

- Current, `docs/spec-065-transport_security-0_0_15.md:3043`-`3058` (rows 43-47): rows for the
  direction matrix, delegation, ambiguity, `X-Forwarded-Host` and the propagating exception —
  none for the ordering.
- Recommended: add a row:
  > "47b. The ordering is behavioral, not merely structural: on a hostile `Host`, neither the
  > auth stack's outermost layer (`CookieMiddleware.__call__`) nor an injected consumer
  > application is ever entered, and both fire on the allowed control. A denial that arrived
  > after the session middleware had already loaded a session would look identical on the wire,
  > which is why the wire is not what this row reads."
- Why: that is where I put it (`test_a_hostile_host_is_denied_before_the_auth_stack_and_the_consumer`).
  Without a row, "outermost" is only ever asserted as composition shape, and composition shape is
  exactly what a later refactor changes.

**A6 — the injection seam's Host guarantee is listed as structural ("by construction") only;
name the behavioral row so it is not later deleted as redundant.**

- Current, `docs/spec-065-transport_security-0_0_15.md:237`:
  > "whatever is injected still sits inside all three router-applied wrappers —
  > `DjangoWebSocketHostValidator`, `AllowedHostsOriginValidator`, and `AuthMiddlewareStack` — by
  > construction"
- Recommended: append: > "— proven structurally by the unwrap walk and behaviorally by
  > `test_an_injected_consumer_is_denied_by_both_handshake_boundaries`, which drives a hostile
  > `Host` and a hostile `Origin` at an injected consumer and shows the consumer is never
  > reached."
- Why: "by construction" is the claim most likely to be trusted without measurement, and the
  seam's entire safety argument rests on it.

**A7 — Decision 13's test-inventory paragraph should record that the shipped WebSocket rows all
had to gain a `Host` header**, because that is a change to ~40 existing rows and it is not a
consequence a reader would predict.

- Current, `docs/spec-065-transport_security-0_0_15.md:1966`-`1973` (the entry for
  `test_websocket_branch_wraps_origin_validator_outside_the_auth_stack`, which correctly predicts
  the extra unwrap).
- Recommended: add a sibling entry:
  > "`channels.testing.WebsocketCommunicator` synthesizes no `Host` header and no
  > `scope["server"]`, so before Decision 19 every WebSocket row in the repo drove a handshake
  > carrying no host information at all — which is why no shipped row could have detected the
  > gap. The module's one handshake helper (`_ws_communicator`) and the two rows that build a
  > communicator directly gain an allowed `Host`; no assertion changes."
- Why: it explains a wide, otherwise-unexplained diff, and it records the reason the suite was
  blind — which is more durable than the fix.

### B. `routers.py` — sentences that were false or incomplete, all FIXED in this change

Recorded with their previous wording so the custodian can confirm the replacements.

**B1 — the module docstring described a two-wrapper composition.**

- Was, `django_strawberry_framework/routers.py` module docstring:
  > "The `"websocket"` value is the package's Channels composition:
  > `AllowedHostsOriginValidator` (the origin check) wrapping `AuthMiddlewareStack` … The two
  > wrappers are the ROUTER's either way, so an injected consumer cannot escape Host/Origin
  > validation or authentication."
- Now (`routers.py:13`-`30`): three named wrappers, the Host check attributed to
  `consumers.py::DjangoWebSocketHostValidator` and to `HttpRequest.get_host()`, "all three
  wrappers are the ROUTER's", and "two separate checks, in that order, neither standing in for
  the other". The old sentence was the one `docs/feedback.md` Medium 4 quoted.

**B2 — the class docstring's Origin-only paragraph.**

- Was, `routers.py::DjangoGraphQLProtocolRouter`:
  > "The WebSocket branch carries `AuthMiddlewareStack` … inside `AllowedHostsOriginValidator`,
  > which denies cross-origin - and missing-`Origin` - handshakes against `ALLOWED_HOSTS`."
- Now (`routers.py:379`-`388`): the same, plus the outer `DjangoWebSocketHostValidator` and the
  one-sentence statement of what each of the two checks answers.

**B3 — the injection seam's own promise.**

- Was: > "Whatever is injected, the two wrappers above are applied by the ROUTER around it, so
  > an injected consumer opts out of the package's revalidation but never out of Host/Origin
  > validation or authentication."
- Now (`routers.py:398`-`402`): "the three wrappers above … never out of the Host check, the
  Origin check, or authentication."

**B4 — both construction-time hint strings named two wrappers.**

- Was, `routers.py::_UNUSABLE_WEBSOCKET_CONSUMER_HINT` and `routers.py::_FACTORY_CONTRACT_HINT`:
  > "the router still wraps the result in AllowedHostsOriginValidator and AuthMiddlewareStack"
- Now (`routers.py:118`, `routers.py:132`): "in DjangoWebSocketHostValidator,
  AllowedHostsOriginValidator and AuthMiddlewareStack". These are user-facing error text, so the
  count mattered. No test asserted the tail beyond `_FACTORY_CONTRACT_SUBSTRING =
  "factory(schema=schema)"`, which is unaffected.

**B5 — the Strawberry floor in the broken-install hint (Medium 5).**

- Was, `routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT`:
  > "requires both `channels>=4.3.2` and `strawberry-graphql>=0.262.0`"
- Now (`routers.py:86`): `strawberry-graphql>=0.316.0`. The `channels>=4.3.2` half is correct
  against `pyproject.toml` and unchanged.

### C. `consumers.py` — sentences that were incomplete, all FIXED in this change

**C1 — the module docstring's first line named only the consumer**, and
`scripts/build_tree_md.py` renders exactly that line.

- Was: > "The package's WebSocket GraphQL consumer and its two actor-revalidation checkpoints."
- Now: > "The WebSocket Host boundary, the GraphQL consumer, and its two revalidation
  > checkpoints." — plus an opening paragraph stating that the module owns two independent things,
  and a closing `**The Host boundary**` section. **`docs/TREE.md` is not regenerated here**
  (Slice 5 owns the regenerate).

**C2 — the module-level dependency inventory omitted Django.**

- Was: > "the module level reaches only for the standard library, this package's logger, and
  > `exceptions.ConfigurationError` / `exceptions.describe_value`."
- Now (`consumers.py:106`-`118`): adds "Django's own `HttpRequest` / `DisallowedHost` (a HARD
  dependency …)" and records that
  `channels.security.websocket.WebsocketDenier` is imported **inside** the validator's denial
  arm — the same discipline `channels.auth.get_user` already follows, and the property that lets
  `routers.py` import this module above its soft-dependency guard.

### D. Slice 5's files (flagged, not edited)

**D1 — `docs/README.md:128`** describes the `"websocket"` value as
> "`AllowedHostsOriginValidator` over `AuthMiddlewareStack` over a `URLRouter` holding one
> exact-matched `re_path` onto a GraphQL WebSocket consumer"

— now incomplete; the outermost `DjangoWebSocketHostValidator` is missing.

**D2 — `docs/README.md:283`**, inside the migration snippet's comment:
> "# AllowedHostsOriginValidator > AuthMiddlewareStack > URLRouter > the consumer."

Recommended: > "# DjangoWebSocketHostValidator > AllowedHostsOriginValidator >
> AuthMiddlewareStack > URLRouter > the consumer."

**D3 — `docs/README.md:390`**:
> "An injected consumer still sits inside `AllowedHostsOriginValidator` and
> `AuthMiddlewareStack` by construction"

Recommended: name all three wrappers. (This line's second half is also the subject of the WS
revocation builder's amendment A8, so the two edits meet here.)

**D4 — `docs/README.md:316` and `docs/README.md:398`** both say the WebSocket origin defence "is
`AllowedHostsOriginValidator`, not a CSRF token — keep `ALLOWED_HOSTS` tight". That is still
true, and now under-sells the boundary: `ALLOWED_HOSTS` is enforced on the WebSocket **Host** as
well, by the package's own validator. Recommended: add ", and since spec-065 the handshake's
`Host` is validated against `ALLOWED_HOSTS` too, by the package's own
`DjangoWebSocketHostValidator` — two separate checks, both reading the same setting."

**D5 — `README.md:62`** carries the same two-wrapper composition sentence in the status
paragraph. Root `README.md` is explicitly outside my file list; flagged for the same sweep.

---

# Build report (Worker 2, pass 2) — W3 review remediation: M3, M4 (Host projection), L5, L6

Cohort: **WS host**, second pass. Input: `docs/builder/bld-review-2-w3_review.md` (Worker 3
adversarial review, `revision-needed`). Files touched this pass:
`django_strawberry_framework/consumers.py`, `tests/test_routers.py`, and this artifact.
`django_strawberry_framework/routers.py` was in my file list and needed **no edit** — verified
byte-identical to its pre-pass copy after every mutation was reverted (`cmp` clean).

Result: `uv run pytest tests/test_routers.py --no-cov` -> **122 passed** (104 before this pass,
+18 rows). Full suite -> **5099 passed, 40 skipped**. See
[§7.2](#72-counts-and-the-delta-pass-2) for the delta attribution.

## 1. Findings closed in this pass

| Finding | Verdict | What landed |
| --- | --- | --- |
| **M3** — the no-`server` `SERVER_NAME` fallback is a 0-row boundary | accepted; the review is right and its premise checked out | `test_a_handshake_carrying_no_host_information_at_all_is_denied` + the `no-host-and-no-server` param of the new projection oracle. Mutant now fails **7** rows (was 0) |
| **M4** (my half) — five projection items sharing three rows | accepted | one independently-failing row per item; every mutation measured separately below |
| **M4** (extra, my files) — `except DisallowedHost` pinned by one monkeypatched row | accepted | `test_a_non_conformant_header_shape_propagates_instead_of_denying` — the naturally-occurring shape the review itself proposed. Mutant now fails **2** rows (was 1) |
| **L5** — the `DEBUG` Host/Origin divergence is unpinned | accepted | `test_the_debug_host_and_origin_defaults_diverge_on_a_localhost_subdomain`, parametrized over two subdomain depths. Narrow mutant fails **2** rows (was 0) |
| **L6** — "private" is true by convention only | accepted **in part**; the review is half wrong (see [§4](#4-where-i-disagree-with-the-review)) | docstrings corrected to state the property the code actually carries, for BOTH classes. No rename |
| **L9** (Host half) — a Host denial is silent server-side | **not built**, reasoned deferral | it is amendment **A4**, a maintainer decision about adding an observability surface. See [§5](#5-l9-the-silent-host-denial-recorded-not-built) |

### 1.1 M3 — I verified fail-closed BEFORE writing the assertion

The brief required this, and it is the one thing that would have turned M3 into a Blocker. It is
**fail-closed**, and the mechanism is Django's:

- `django/core/handlers/asgi.py::ASGIRequest.__init__` #"self.META[\"SERVER_NAME\"] = \"unknown\""
  is where `"unknown"` / `"0"` come from — they are Django's own literals for the same
  no-`server` scope, not the package's invention. Confirmed by reading the installed source at
  both 6.0.5 and, via the floor run, 5.2.0.
- `HttpRequest._get_raw_host` takes its third option (`SERVER_NAME` + `get_port()`), and
  `get_port()` returns `"0"`; `is_secure()` on a bare `HttpRequest` answers `False` (base
  `_get_scheme` returns `"http"`), so the expected port is `"80"` and the reconstruction is
  `"unknown:0"`.
- `split_domain_port` yields domain `"unknown"`, and `validate_host("unknown", ALLOWED_HOSTS)` is
  `False` for every `ALLOWED_HOSTS` that does not literally contain `"unknown"` or `"*"` —
  including the `DEBUG` fallback `[".localhost", "127.0.0.1", "[::1]"]`.

So the arm denies, and it denies *because Django refuses `"unknown"`*, which is the delegation the
decision promises. `ALLOWED_HOSTS = ["*"]` allows it, and that is correct: Django's HTTP path
allows it too, and delegating means inheriting that.

**The oracle problem the review flagged is real, and it needed a new oracle.** `RequestFactory`
unconditionally installs `SERVER_NAME = "testserver"`, so `_django_http_host_verdict()` with no
arguments answers `"testserver"` — I hit exactly that (the row failed with
`assert 'testserver' is None`) before adding `_django_asgi_host_verdict`, which takes the `META`
from Django's own ASGI adapter and asks the public `HttpRequest.get_host()` about it. Nothing
package-owned participates, so it is still an oracle: the only difference from the production path
is where the four `META` keys came from, and that is the thing under test.

### 1.2 M4 — one row per projection item, plus a `META` oracle beside the verdict oracle

The review's recommended shape, implemented as recommended: the module already had
`_django_http_host_verdict` as the **verdict** oracle; the projection needed a **`META`** oracle
beside it. `tests/test_routers.py::_django_asgi_host_meta` builds a real
`ASGIRequest` from the same scope and returns the four Host-related `META` keys;
`test_the_host_projection_matches_djangos_asgi_adapter_key_for_key` asserts the projection equals
it, one param per item.

Two properties are asserted per param, and the second is new:

- **equality** against Django's constructor — no hand-typed table, which is the whole point of a
  delegating boundary;
- **`set(projected) <= _HOST_META_KEYS`** — the *negative* half of the "item by item" promise. The
  projection must produce nothing beyond the four keys `get_host()` reads, so a later edit that
  "completes" it with `HTTP_X_FORWARDED_PORT` or the `SECURE_PROXY_SSL_HEADER` header (both
  provably verdict-neutral, per this artifact's A1) fails here instead of silently widening a
  security boundary's input surface. Nothing pinned that before.

The behavioral rows were also split and extended:

| Item | Behavioral row | Oracle param |
| --- | --- | --- |
| `.lower()` on the decoded header name | `test_an_odd_cased_host_header_still_reaches_the_boundary` (NEW — split out of the duplicate-header row) | `odd-cased-header-name` |
| comma-join of duplicates | `test_duplicate_host_headers_fail_closed_in_djangos_comma_joined_form` (renamed; the casing tail removed) | `duplicate-host-headers` |
| `x-forwarded-host` key | `..._x_forwarded_host_is_honoured_only_under_the_django_setting[True]` + `test_a_hostile_x_forwarded_host_is_refused_even_behind_an_allowed_host` (NEW — the DENY direction) | `forwarded-host-only` |
| Latin-1 value decode | `test_a_latin_1_only_host_header_is_decoded_rather_than_crashing` (NEW) | `latin-1-only-host-bytes` |
| `scope["server"]` / `"unknown"` fallback | `..._scope_server_supplies_djangos_fallback` + `test_a_handshake_carrying_no_host_information_at_all_is_denied` (NEW) | `server-only`, `host-and-server`, `no-host-and-no-server` |

The Latin-1 item deserves one note, because its shape is different from the other four: the codec
choice **cannot change a verdict**. `split_domain_port`'s `host_validation_re` admits only
`[a-z0-9.-]`, so any non-ASCII host is refused either way. What the codec changes is whether the
boundary *reaches a decision at all* — `b"caf\xe9.example"` decodes under Latin-1 and raises
`UnicodeDecodeError` under UTF-8, and that exception deliberately does NOT become a denial
(Test 47), so the handshake would fail with a traceback out of the ASGI application instead of a
verdict. That is what the row pins, and it is why the row's subject is "decoded rather than
crashing".

## 2. Failability proofs

Procedure for every proof: the file was copied to
`<scratchpad>/w2/consumers.PRISTINE.py` / `routers.PRISTINE.py` **before** any mutation; each
mutation was applied by exact-string replacement from that copy (asserting exactly one anchor
match); the focused suite was run; the file was restored by copying the pristine file back; and the
restore was proved with `cmp` (exit 0, no output). One boundary at a time, reverted before the next.
**No `git` write command was run at any point** — no `checkout`, `restore`, `stash`, `add`,
`commit`, `branch` or `switch` — and no revert was ever verified by an "empty `git diff`", which
would have been impossible on a legitimately dirty tree and whose obvious workaround would have
destroyed this slice's and the maintainer's work.

Counts are against `uv run pytest tests/test_routers.py --no-cov` (122 rows).

| Boundary (symbol-qualified) | Mutation applied | Rows failed | Was | Revert |
| --- | --- | --- | --- | --- |
| `consumers.py::_host_validation_request` #"raw_name.decode(\"latin1\").lower()" | `.lower()` deleted from the decoded header name | **2** (`..._odd_cased_host_header_still_reaches_the_boundary`, oracle `[odd-cased-header-name]`) | 1, shared | `cmp` rc=0 |
| `consumers.py::_host_validation_request` #"\",\".join(values)" | comma-join replaced with `values[-1]` (last-value-wins) | **2** (`..._duplicate_host_headers_fail_closed_...`, oracle `[duplicate-host-headers]`) | 1, shared | `cmp` rc=0 |
| `consumers.py::_HOST_META_KEYS_BY_HEADER` | `"x-forwarded-host"` entry removed | **3** (`..._x_forwarded_host_is_honoured_only_under_the_django_setting[True]`, `..._hostile_x_forwarded_host_is_refused_...`, oracle `[forwarded-host-only]`) | 1 | `cmp` rc=0 |
| `consumers.py::_host_validation_request` #"raw_value.decode(\"latin1\")" | codec changed to `utf-8` | **2** (`..._latin_1_only_host_header_is_decoded_...`, oracle `[latin-1-only-host-bytes]`), both via `UnicodeDecodeError` at the production line | 0 | `cmp` rc=0 |
| `consumers.py::_host_validation_request` #"request.META[\"SERVER_NAME\"] = \"unknown\"" | `"unknown"` / `"0"` -> `"testserver"` / `"80"` (the review's own mutation) | **7** (`..._handshake_carrying_no_host_information_at_all_is_denied` + 6 oracle params) | **0** | `cmp` rc=0 |
| `consumers.py::DjangoWebSocketHostValidator.__call__` #"except DisallowedHost:" | widened to `except Exception:` | **2** (`..._only_disallowed_host_becomes_a_websocket_denial`, `..._non_conformant_header_shape_propagates_...`) | 1 | `cmp` rc=0 |
| the composed Origin check (`routers.py::_build_router_class` #"from channels.security.websocket import AllowedHostsOriginValidator") | replaced with `OriginValidator(app, list(settings.ALLOWED_HOSTS) or [\".localhost\", \"127.0.0.1\", \"[::1]\"])` — i.e. the Origin side adopts Django's dot-prefixed `DEBUG` list, the exact regression L5 names | **2** (`..._debug_host_and_origin_defaults_diverge_...[sub.localhost]`, `[deep.sub.localhost]`) | 0 | `cmp` rc=0 |

Two notes on the last one, because it is the only proof where I had to iterate:

- A **broader** mutation (`OriginValidator(app, ["*"])`) fails 6 rows, but 5 of those are the
  pre-existing origin-direction rows — it does not demonstrate that anything pins the *divergence*.
  The narrow mutation above is the honest one, and against the single-row version of the L5 row it
  failed exactly **1** row, i.e. weakly pinned under the new rule. Parametrizing over two subdomain
  depths (`sub.localhost`, `deep.sub.localhost`) makes it 2, and the parametrization is not padding:
  dot-prefixed matching is depth-independent, so both depths are genuine instances of the property
  and a partial fix cannot satisfy one and not the other.
- No other row in the module can see that mutation. Every other origin row uses
  `evil.example.com` or a missing `Origin`, both of which a dot-prefix change leaves refused.

### 2.1 Changes that are NOT boundaries, and therefore carry no proof

- `consumers.py::_actor_is_current` #"window = consumer.revalidation_window" (L4, recorded in the
  revocation artifact's pass 2) — the REMOVAL of unreachable defensiveness, not a new boundary.
- Every docstring correction in this pass (L6, the module docstring's export claim).
- The three row renames / splits. Renaming a row is not a boundary change; the mutations above are
  what prove the renamed rows still bite.

## 3. Hot-path budget

Not applicable to this cohort's diff: nothing in this pass touches a per-request, per-connection or
per-outbound-message path. `DjangoWebSocketHostValidator.__call__` runs **once per handshake**, and
this pass did not change it beyond a docstring.

The round's actual hot-path obligation (M5) belongs to the outbound revocation checkpoint and is
captured with numbers in `bld-review-2-ws_revocation.md`'s pass-2 report.

One number worth recording anyway, because it is the one thing a reader might worry about: the
projection performs no IO and allocates one `HttpRequest` plus one small dict per handshake, and the
122-row module (which drives ~40 real handshakes) runs in the same ~5.7 s it did before the boundary
existed.

## 4. Where I disagree with the review

**L6 is half wrong, and the half that is wrong matters.** The review states that
`GraphQLWebSocketConsumer` "carries a public name, so
`from django_strawberry_framework.consumers import DjangoWebSocketHostValidator` works" and groups
the two classes together. `GraphQLWebSocketConsumer` is **not importable at all**: its `class`
statement is function-local to `build_revalidating_consumer_class`, so there is no module attribute
to bind and the import raises `ImportError`. Its docstring's "deliberately not exported" claim was
therefore already *weaker* than the truth, not stronger. I strengthened the module docstring to say
so rather than leaving a correct-but-under-stated claim next to a corrected one.

The other half is right: `DjangoWebSocketHostValidator` **is** importable. I did not rename it, and
that is a deliberate choice rather than a deferral:

- the name appears in **user-facing error text**
  (`routers.py::_UNUSABLE_WEBSOCKET_CONSUMER_HINT`, `::_FACTORY_CONTRACT_HINT`) and in `routers.py`'s
  composition docstrings, so a consumer reads this exact spelling in a `ConfigurationError` and must
  be able to grep for it. An underscore-prefixed name in an error message is worse than an
  underscore-free one that documents its own support status;
- the name is also Decision 19's name in the spec, so renaming it is a spec-level edit, which is
  Worker 1's;
- `_RevalidatingTransportWSHandler` / `_RevalidatingGraphQLWSHandler` /
  `_RevocationGatedWebSocketAdapter` appear in no message and no spec sentence, which is why the
  underscore is right for them and not here.

So the fix is the docstring: "private" now says what it means — **unsupported to import or
subclass**, an `__all__` and documentation contract rather than an import-time one — and states
explicitly that an absent underscore is not a promise of stability. Amendment **A8** below asks the
spec to carry the same distinction.

## 5. L9: the silent Host denial, recorded not built

The review's L9 asks for one decision across three fail-closed paths that landed this round, two of
which log nothing. The Host denial is one of the two silent ones, and I am **not** building a log
line, for the reason §2.3 of pass 1 already gave and which the review does not overturn: Decision 19
requires wire *indistinguishability* and says nothing about server-side observability, so adding an
observability surface to a fixed design is the maintainer's call. It is amendment **A4** (pass 1),
re-endorsed here with L9's cross-cohort argument attached.

What I can add that pass 1 could not: the review establishes that the package is **already willing**
to log a fail-closed decision (`consumers.py::_actor_is_current` #"logger.exception"), which removes
the only real objection — that a log line would be a new kind of surface for this package. That
makes "log all three at `warning` / `exception`, no wire change" the answer I would recommend if
asked. The third path (`_request_body.py` / `views.py`) is another cohort's file, so a builder-side
decision here could only ever have been two-thirds of the fix, which is itself an argument for
routing it through the custodian.

## 6. Files I did not touch (pass 2)

`git status --short` after `ruff format` / `ruff check --fix`: my three paths are
`django_strawberry_framework/consumers.py`, `tests/test_routers.py` and the two `bld-review-2-ws_*.md`
artifacts. `django_strawberry_framework/routers.py` shows dirty, and that is pass 1's work plus the
concurrent tree — after this pass's Origin mutation was reverted, `cmp` against my pre-pass copy is
clean, so **nothing in `routers.py` is a pass-2 edit of mine**.

Untouched and unread-for-modification: `views.py`, `_request_body.py`, `tests/test_views.py`,
`examples/fakeshop/test_query/test_transport_api.py` (the concurrent HTTP-boundary builder's),
`docs/builder/BUILD.md` and `worker-*.md` (the coordinator's), `docs/feedback.md`,
`docs/feedback2.md`, `drys.md`, `vulns.md`, `TODAY.md`, `README.md`, `docs/README.md`, `conf.py`,
`auth/*`, `docs/spec-*`, `docs/SPECS/*`, `db.sqlite3`, `docs/GLOSSARY.md`, `docs/TREE.md`.

One new **gitignored** scratch path was created for the M5 measurement:
`docs/builder/temp-tests/review-2-w2/test_hotpath_budget.py` (outside `pytest.ini`'s `testpaths`, so
it is never collected by the default sweep).

## 7. Validation run and counts

### 7.1 Validation

- `uv run ruff format .` — pass (403 files already formatted after my edits).
- `uv run ruff check --fix .` — pass (`All checks passed!`; 3 auto-fixes on my own file during the
  pass, all trailing-comma/format layout).
- `uv run python scripts/check_trailing_commas.py tests/test_routers.py django_strawberry_framework/consumers.py`
  — pass (explicit paths, as required).
- `uv run pytest tests/test_routers.py --no-cov` — **122 passed**.
- `uv run pytest --no-cov` (full sweep) — **5099 passed, 40 skipped**.
- No `--cov*` flag was used in any run.

### 7.2 Counts and the delta (pass 2)

| Scope | Review's baseline | Now | Delta |
| --- | --- | --- | --- |
| `tests/test_routers.py` | 104 passed | **122 passed** | +18, all mine |
| Full suite | 5072 passed, 40 skipped | **5099 passed, 40 skipped** | +27 |

The +27 against my +18 is **+9 rows I did not write.** They are in `tests/test_views.py` and
`examples/fakeshop/test_query/test_transport_api.py`, the two files the concurrent HTTP-boundary
builder owns; both were modified after the 5072 figure was recorded (`views.py` was rewritten at
13:29, *during* my full-suite run), and I touched neither. `tests/test_routers.py` accounts for
exactly +18 on its own, and `tests/test_routers.py` + `tests/test_views.py` +
`test_transport_api.py` = 332 passed, of which 122 are mine. Skips are unchanged at 40.

Because the concurrent builder was writing during the sweep, the 5099 figure is a snapshot of a
moving tree. My own scope is deterministic: 122, on the shared venv and at the floor.

## 8. Floor verification

The change touches a Django integration seam (`HttpRequest` construction, `get_host()`,
`ASGIRequest`'s `META` contract) and a channels seam (the ASGI middleware and the communicator
harness), so the floor run is required.

- Scratch venv: `<scratchpad>/w2-floor` (outside the working tree; the shared `.venv` was never
  installed into — every install carried an explicit `--python <that venv>/bin/python`).
- Built with `uv venv --python 3.10`, then `uv pip install --python ... -e . --group dev`, then
  `uv pip install --python ... 'django==5.2.0' 'strawberry-graphql==0.316.0' 'channels[daphne]==4.3.2'`.
- Resolved versions (`uv pip list --python ...`): Python **3.10.19**, Django **5.2**,
  strawberry-graphql **0.316.0**, channels **4.3.2**, daphne **4.2.3**, asgiref **3.12.1**,
  pytest **9.1.1**, pytest-django **4.12.0**, pytest-asyncio **1.4.0**.
- `<floor>/bin/python -m pytest tests/test_routers.py --no-cov` -> **122 passed**, identical to the
  shared venv (Python 3.14.2 / Django 6.0.5).

Nothing in the new rows encodes one Django version's answer: the projection rows assert against the
`ASGIRequest` of the Django under test, and the verdict rows against that Django's `get_host()`. The
one place a version divergence could have bitten is `ASGIRequest.__init__`'s `"unknown"` / `"0"`
literals, and the floor run is what confirms 5.2.0 carries them too rather than my having read only
6.0.5's source.

## Required spec amendments (pass 2)

Checked against `docs/spec-065-transport_security-0_0_15.md` as of this writing. Pass 1's A1-A7
still stand and are not restated. I edited no spec.

**A8 — Decision 19 should state what "private" means for `DjangoWebSocketHostValidator`, because
the code cannot carry the stronger reading.** (Review L6, half-accepted.)

- Where it lives: `## Decision 19` (the WebSocket Host boundary), the paragraph introducing the
  validator as package-private.
- Current wording, `docs/spec-065-transport_security-0_0_15.md:2474` region:
  > "**Only `DisallowedHost` becomes a denial.** The validator catches `DisallowedHost` and denies
  > the handshake **before authentication and before the consumer is constructed**."
- Recommended replacement — keep, and add a new bullet beside it:
  > "**What "private" means for this class.** `DjangoWebSocketHostValidator` is absent from every
  > `__all__` and from the package root, and is unsupported to import or subclass - but it is
  > deliberately NOT underscore-prefixed, unlike the three private classes inside
  > `build_revalidating_consumer_class`. It is named in the router's own construction-time hint text
  > (`routers.py::_UNUSABLE_WEBSOCKET_CONSUMER_HINT`, `::_FACTORY_CONTRACT_HINT`) and in this
  > decision, so a consumer reads that exact spelling in a `ConfigurationError` and must be able to
  > grep for it. Privacy here is an `__all__`-and-documentation contract, not an import-time one, and
  > an absent underscore is not a promise of stability. By contrast
  > `GraphQLWebSocketConsumer`, `_RevalidatingTransportWSHandler`, `_RevalidatingGraphQLWSHandler`
  > and `_RevocationGatedWebSocketAdapter` are unreachable by import at all: their `class`
  > statements are function-local to the factory, so no module attribute exists to bind."
- Why: the shipped docstrings previously asserted "PRIVATE" for a name a consumer can import, and
  simultaneously under-stated the consumer class, which is stronger than private. A reader who fixes
  one by renaming breaks the error messages; a reader who fixes the other adds an `__all__` entry for
  a name that does not exist. The distinction has to be written down once.

**A9 — Decision 19's test-plan rows need a row for the no-host-information handshake, and it cannot
use the `RequestFactory` oracle.** (Review M3, and the review's own note 3 to Worker 1.)

- Where it lives: `## Test plan`, the Decision 19 block (rows 43-47).
- Current wording, `docs/spec-065-transport_security-0_0_15.md:3043`-`3058`: rows for the direction
  matrix, delegation, ambiguity, `X-Forwarded-Host` and the propagating exception.
- Recommended replacement — add:
  > "46c. A handshake carrying **no** `Host`, **no** `X-Forwarded-Host` and **no** `scope["server"]`
  > - the default `channels.testing.WebsocketCommunicator` shape, and a shape a non-conformant ASGI
  > server can produce - is **denied**. The value that decides it is
  > `ASGIRequest.__init__`'s own `"unknown"` / `"0"`, not a package constant, so the row asserts the
  > projected `SERVER_NAME` / `SERVER_PORT` against Django's adapter rather than against a literal.
  > Note that `RequestFactory` cannot be the verdict oracle for this row: it unconditionally installs
  > `SERVER_NAME = "testserver"`, so its no-host leg answers a different question. The oracle is
  > Django's ASGI adapter's `META` fed to the public `HttpRequest.get_host()`."
- Why: the arm decides the verdict for that handshake and had zero behavioral coverage; and the next
  author's first instinct will be the `RequestFactory` oracle every other row in the block uses,
  which silently cannot express the input.

**A10 — the projection's "item by item" promise needs its negative half stated: the projection
produces nothing beyond the four keys.**

- Where it lives: `## Decision 19`, the `_host_validation_request` item list (the bullet A1 also
  amends).
- Current wording, `docs/spec-065-transport_security-0_0_15.md:2516`:
  > "The projection supplies the minimum `META` `get_host()` reads, which is a smaller and more
  > auditable compatibility surface than a request object built out of a scope it was not written
  > for."
- Recommended replacement:
  > "The projection supplies the minimum `META` `get_host()` reads - `HTTP_HOST`,
  > `HTTP_X_FORWARDED_HOST`, `SERVER_NAME` and `SERVER_PORT` - and, as a checked property rather than
  > an intention, **nothing else**: a test asserts that the projected `META`'s key set is a subset of
  > those four, so a later edit that grows the projection fails before it can widen this boundary's
  > input surface. That is a smaller and more auditable compatibility surface than a request object
  > built out of a scope it was not written for."
- Why: A1 (pass 1) explains *why* two keys are omitted; nothing said the omission is *enforced*. It
  now is, and the enforced version is the one a reviewer can check.

**A11 — the `DEBUG` divergence caveat A3 asks for should name the row that pins it, and say which
side is the permissive one.**

- Where it lives: `## Edge cases`, the `ALLOWED_HOSTS = []` with `DEBUG=True` entry (the same
  passage pass 1's A3 amends).
- Current wording, `docs/spec-065-transport_security-0_0_15.md:2748`:
  > "which is the point of delegating: one configuration, one matcher, two transports."
- Recommended replacement — A3's appended caveat, plus:
  > "The **Host** side is the permissive one there, which is what makes the divergence worth a row
  > rather than only a note: a change to the Origin side that adopted Django's dot-prefixed list
  > would open every `*.localhost` origin under `DEBUG`, and no other row in the suite could see it.
  > `test_the_debug_host_and_origin_defaults_diverge_on_a_localhost_subdomain` asserts all three legs
  > (Django accepts the Host, Channels refuses the Origin, the socket is denied) at two subdomain
  > depths, because dot-prefixed matching is depth-independent."
- Why: A3 records the fact; this records which direction is dangerous and where the guard is, which
  is what stops the guard being deleted as redundant with the existing `DEBUG` row.

## 9. The `routers.py` nit: reasoned rejection

The review's second nit observes that `routers.py:192` and `routers.py:251` both build
`"The factory {describe_value(factory)} ..."` around the shared `_FACTORY_CONTRACT_HINT`, and
concludes "the shared part is already extracted, the residual duplication is two words. Not worth
changing."

**Agreed, and rejected for one reason beyond size.** The two raise sites answer different mistakes
(the calling convention vs the returned object) and the residual words are the part that differs
*per site*; extracting them would mean either a formatting helper whose only body is an f-string, or
a shared message that stops naming which mistake fired. Both are worse than two words. Recorded here
so the next DRY sweep does not re-open it.

The review's first nit (the multipart discrimination computed twice in `views.py`) is the HTTP
cohort's file and is not mine to work.
