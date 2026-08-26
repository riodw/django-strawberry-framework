# DRY review: `django_strawberry_framework/consumers.py`

Status: fix-implemented → verified

## System trace

`consumers.py` owns two independent things. (1) The handshake-time **WebSocket Host
boundary**: `DjangoWebSocketHostValidator` composes outermost in the router and
`_host_validation_request` projects a scope's `Host` / `X-Forwarded-Host` headers plus
`scope["server"]` into a minimal `HttpRequest`, then calls Django's own
`HttpRequest.get_host()`; only `DisallowedHost` becomes Channels' `WebsocketDenier`,
every other exception propagates. (2) The **consumer factory**
`build_revalidating_consumer_class(GraphQLWSConsumer)` → `GraphQLWebSocketConsumer`
with its two actor-revalidation checkpoints: operation admission (the two protocol
handler subclasses' `handle_subscribe` / `handle_start` overrides) and the outbound
information-bearing frame (`_RevocationGatedWebSocketAdapter.send_json` derived from
the base consumer's own `websocket_adapter_class` attribute). Supporting machinery:
`resolved_revalidation_window` (typed construction-time validation),
`_ConnectionRevocation` (five-state close machine: permitted/decided/closing/closed/
abandoned, bounded close attempts, connection-owned shielded task settled from
`disconnect`), and `_StopAwareSchema` / `_stop_aware_results` — per-connection schema
wrapper over both upstream result-source names (`subscribe` / `stream`) that ends the
loop normally at revocation (termination, deliberately never cancellation) and masks
each result through `extensions/error_policy.py`'s shared helpers.

Consumers: `routers.py` is the ONLY production importer (verified by grep) — it imports
`_DEFAULT_REVALIDATION_WINDOW` for its constructor default, `resolved_revalidation_window`
for validation, builds the class once inside the guarded cached `_ROUTER_CLASS` builder,
and composes `DjangoWebSocketHostValidator(AllowedHostsOriginValidator(AuthMiddlewareStack(
URLRouter(...))))`. `utils/sessions.py` supplies the shared connection-actor lease,
provenance latch, and session-store resolver; `auth/mutations.py::logout` runs on the same
socket through `utils/sessions.py::actor_transition`, holding the SAME lease (lock order:
session lock outer, lease inner). Tests: `tests/test_routers.py` (~5700 lines) exercises
both protocols over real Channels communicators, including the host-projection rows pinned
key-for-key against Django's ASGI adapter. `testing/_wrap.py` is NOT connected to this
file (a Django-Trac-#37064 DB-connection wrap helper; no import edge either way — grep
confirmed). Examples: fakeshop mounts no router/ASGI file; the transport surface lives
entirely in package tests. Docs: GLOSSARY entries "Connection-scoped revocation",
"WebSocket revalidation window", "WebSocket consumer-injection seam", "WebSocket Host
boundary", "DjangoGraphQLProtocolRouter"; TREE.md taglines mirror module/class docstrings.

Lockstep surfaces: an upstream rename of the handler/adapter attributes or of
`subscribe`/`stream`/`execute` is tracked by
`tests/test_routers.py::test_the_stop_aware_schema_passes_every_upstream_schema_read_through`;
the window default is single-sited here and imported by the router; the wire contract
(`4403` / `"Forbidden"`) is pinned against upstream's literal in tests.

## Verification

Axis 1 — cross-flavor policy mirroring (searched). Numeric-boundary validators across
flavors: `views.py::_resolved_max_request_body_bytes` vs `consumers.py::resolved_revalidation_window`
share a PATTERN (typed `ConfigurationError`, exact-type admission rejecting `bool`,
`describe_value` got-tail) but differ in every rule that matters — sentinel semantics
(`None` = defer/disable vs no `None`), predicate (`> 0` int vs finite `float >= 0`),
and the guarded `OverflowError` conversion arm unique to the window. Merging needs mode
flags → REJECTED. Masking: exactly two application sites of ONE classifier/replacer/
shape-gate owned by `extensions/error_policy.py` (`mask_execution_result`,
`is_maskable_result`, `masking_is_active`); the query-teardown seam and the per-event
seam share them by design and neither restates policy → already consolidated. Host
policy: zero package-side hostname matching anywhere (grep: every `ALLOWED_HOSTS` /
`get_host` hit outside consumers.py is prose) — WebSocket delegates to the same
`HttpRequest.get_host()` call HTTP's middleware makes, which is Decision 19's whole
point, not duplication.

Axis 2 — sync and async twins (searched, ruled out). No sync twin exists in the target
(grep `async_to_sync|sync_to_async|database_sync_to_async`: docstring mentions only;
every path is async-native; the one sync boundary crossing is upstream's already-decorated
`channels.auth.get_user`, reused verbatim rather than rewrapped). Closest analogue: the
two protocol-handler admission overrides are PROTOCOL twins, not color twins — their
entire decision lives in the module-level `revalidate_operation_actor` /
`_actor_is_current` / `_revoke_connection`, leaving each subclass body two lines of
super()-glue naming its own upstream hook; a mixin carrying both hook names would add a
dead method to each protocol. Views.py's sync/async CSRF twins are views-owned, forced by
Django's `csrf_protect` coroutine inspection, and already share the boundary mixin — not
this file's surface.

Axis 3 — derived rather than repeated knowledge (searched). `_DEFAULT_REVALIDATION_WINDOW`
spelled once (grep), imported by `routers.py` — clean. Scope keys namespaced once each
across three modules — clean. `_REVOCATION_CLOSE_CODE = 4403` / `"Forbidden"`: upstream's
literal is NOT importable (verified in `.venv`: hardcoded at
`strawberry/subscriptions/protocols/graphql_transport_ws/handlers.py`, and the legacy
graphql-ws protocol never emits it), so the package constant plus the test pin
(`tests/test_routers.py` header block spelling `_REVOKED_CLOSE_CODE = 4403` as "upstream's
own") is the minimal available restatement → REJECTED as candidate. `_HOST_META_KEYS_BY_HEADER`
mirrors Django's ASGI adapter derivation but is pinned key-for-key by
`test_the_host_projection_matches_djangos_asgi_adapter_key_for_key`, projects only two
headers, and records why the two omitted keys are verdict-neutral. The wrapper read-set
`{subscribe, stream}` is re-derived from installed upstream modules by test rather than
trusted — deliberate.

Axis 4 — inverse and round-trip pairs (searched, ruled inapplicable). Every adaptation in
this module is one-way: `_host_validation_request` projects scope→META and nothing parses
back (`consumers.py:1354`), `resolved_revalidation_window` validates with no formatting
inverse anywhere, and the one wrap/unwind pair — `_stop_aware_results` wrapping a result
source and `aclose`-ing it in its own `finally` — lives inside a single function. No
encode/decode grammar is split across modules.

Axis 5 — contracts restated in another medium (searched; one drift found). Searched
standing docs for mechanism prose around revocation/revalidation/cancellation.
FOUND: the GLOSSARY "Connection-scoped revocation" entry still said revocation "unwinds
the current operation through cancellation", but the mechanism changed in 1bb67b43
("own the revoked operation's end and the revocation close") AFTER the glossary fold
(574c4c36): present-day code terminates the detecting operation via the stop-aware
result source and states "Termination is the mechanism, and cancellation is deliberately
not", with the burst tests pinning WHEN it stops
(`test_a_revoked_operation_stops_when_its_every_later_result_is_already_available`).
Code+tests moved; the standing-doc medium did not. Became the finding below. Other media
agree: routers.py docstrings, the revalidation-window and injection-seam GLOSSARY
entries, and TREE.md taglines match present behavior.

Single-edit-site counts (posited changes):
- "Admit `Decimal` for `websocket_revalidation_window`" → `resolved_revalidation_window`
  + its tests only: **1** (pattern-mate in views.py unaffected — different domain).
- "Change the got-value rendering of a rejected config value" →
  `exceptions.describe_value` only (already the single owner for both flavors): **1**.
- "Add a wildcard to `ALLOWED_HOSTS`" → zero package sites (Django owns the match on
  both transports): **0**.
- "Change the operation-admission security rule" → `revalidate_operation_actor` /
  `_actor_is_current` only: **1**.
- "Change how a revoked operation stops" → consumers.py + its burst tests + the
  GLOSSARY paragraph: **2 mediums**, and they had diverged → the finding.

Strongest rejected candidate: promoting the authenticated-actor predicate
(`x is not None and getattr(x, "is_authenticated", False)`). Spellings today:
`auth/mutations.py:400` (`_authenticated_actor_or_none`, request→actor-or-None),
`consumers.py:863` and `consumers.py:900` (actor→bool, inside one function).
The code pre-states its own promotion trigger ("If a THIRD site ever needs this
predicate, promote it to ``utils/permissions.py`` beside ``ChannelsRequestAdapter``"),
but counting by surface gives TWO (auth-mutation surface; the transport decision
function holding both arms), the shapes genuinely differ (request-level anonymity
definition vs actor test feeding the provenance carve-out), the predicate is the
ecosystem-wide Django idiom rather than a package rule, and no plausible change forces
all three to move together short of Django changing its own convention. Promoting into
`utils/permissions.py` would also drag the heavy `utils.querysets` graph into
consumers' deliberately minimal module body; the minimal-graph home
(`utils/sessions.py`) has charter fit but would still be a convenience helper owning no
drifting rule. Kept separate; the documented trigger stands for a future third surface.

Scratch experiments: none needed — every uncertain point was settled by reading the
installed upstream source, the burst/close tests, or import-graph probes.

## Opportunities

### 1. Standing docs restated the retired cancellation stop mechanism

- **Repeated responsibility:** the contract "what happens to the DETECTING operation
  when a checkpoint revokes the connection" was held in production code + tests AND in
  the standing glossary — and the two mediums disagreed.
- **Sites:** `consumers.py` module docstring + `_stop_aware_results`; the subprotocol-
  parameterized burst/close tests in `tests/test_routers.py`; the GLOSSARY
  "Connection-scoped revocation" paragraph.
- **Evidence:** posited change "alter how a revoked operation stops" must move the code,
  its tests, and the glossary paragraph (count 2+). History proves the drift mechanism:
  the glossary fold (574c4c36) predates the stop-aware rewrite (1bb67b43), and the
  medium was not swept when the mechanism changed — the exact lockstep failure axis 5
  exists to catch.
- **Owner:** the GLOSSARY paragraph (the standing-doc medium of a contract whose code
  owner is `consumers.py`).
- **Consolidation:** reworded the clause to state termination-at-next-iteration through
  the stop-aware result source (`consumers.py::_stop_aware_results`), including WHY
  (no suspension point could deliver a cancellation request), while keeping the still-
  true sibling clause about upstream's disconnect path cancelling remaining operations.
- **Proof:** prose carries no executable test; the statement is pinned by the existing
  burst rows cited above, and this artifact records the search that caught the divergence.
- **Risks / non-goals:** spec history under `docs/SPECS/` untouched (period records, not
  live contracts); KANBAN/TODAY carry no restatement of the old wording (grep).

## Implementation (Worker 1)

- `docs/GLOSSARY.md`: replaced the stale "unwinds the current operation through
  cancellation" clause in "Connection-scoped revocation" with the present-day
  termination-via-stop-aware-result-source statement.
- No Python changes; orphan-import sweep not applicable.
- `uv run ruff format .` + `uv run ruff check --fix .`: clean, 429 files unchanged.
- pytest DEFERRED per AGENTS.md (no run without maintainer authorization).

## Judgment

The target is heavily pre-consolidated, and visibly so: the shared decision
(`_actor_is_current`), the shared revocation entry point (`_revoke_connection`), the
shared masking implementation (extension-module-owned), and the shared lease/provenance
primitives (`utils/sessions.py`) each state their rule once, and the module's remaining
look-alikes are protocol twins, pattern-mates, or deliberate delegations to Django and
upstream seams — disproved with counts of one or zero. One real cross-medium divergence
existed and was repaired: the standing glossary still described the retired
cancellation-based stop mechanism. The authenticated-actor predicate stays un-promoted
on the evidence above, with the code's own trigger recorded for the day a third surface
appears.

## Independent verification (Worker 2)

Scope check against the cycle baseline `8753c4e`: under `docs/GLOSSARY.md`,
`django_strawberry_framework/`, and `tests/` this item's only edit is the one
"Connection-scoped revocation" clause in GLOSSARY; the `optimizer/field_meta.py` +
`tests/optimizer/test_field_meta.py` diff in the same range belongs to another item /
concurrent work and touches nothing consumers-related. No `consumers.py`, `routers.py`,
or `tests/test_routers.py` change exists to verify.

Glossary claim independently confirmed against present code:
- `consumers.py::_stop_aware_results` reads `consumer._revocation.revoked` BEFORE each
  pull and RETURNS, so upstream's loop ends normally at its next iteration —
  termination, never cancellation; its `finally` acloses the inner source so the
  subscription generator's cleanup runs at the revocation.
- "the DETECTING operation" is precise, not loose: only the operation that just produced
  the suppressed frame is guaranteed past its pull; siblings parked mid-`anext` are left
  to upstream's disconnect path, exactly the split the clause draws ("...cancel and await
  every remaining registered operation").
- The no-suspension-point rationale matches `consumers.py::_revoke_connection` /
  `send_revalidated_operation_frame` docstrings verbatim, and
  `test_a_revoked_operation_stops_when_its_every_later_result_is_already_available`
  pins WHEN it stops on both protocols (`emitted == ["burst-1"]`, generator finalized at
  the revocation, sibling left to teardown).
- Drift history proven: `574c4c36` (glossary fold) is an ancestor of `1bb67b43`
  (stop-aware rewrite); old clause said "unwinds ... through cancellation".

Rejected candidates re-probed, all stand:
- Validator merge: re-read both bodies. `_resolved_max_request_body_bytes` has
  setting-fallback + disable sentinel semantics and an int-only domain;
  `resolved_revalidation_window` has no None arm, a finite-float >= 0 predicate, and a
  guarded `OverflowError` conversion arm views.py lacks. Shared bits (`describe_value`
  tail) already single-sited in `exceptions.py`. A merge needs mode flags for three
  independent rule differences — rejection correct.
- `_REVOCATION_CLOSE_CODE`: verified in the installed venv that `4403` / `"Forbidden"`
  is hardcoded inline at strawberry's
  `subscriptions/protocols/graphql_transport_ws/handlers.py` (`websocket.close(code=4403,
  reason="Forbidden")`) — genuinely non-importable; constant + test pin is minimal.
- Actor-predicate promotion: confirmed `utils/permissions.py` imports `.querysets`
  (line 46), so promotion there drags the heavy graph into consumers' channels-free /
  strawberry-free module body; the code pre-states its own third-site trigger at
  `consumers.py` lines 856–862. Rejection correct.
- Other-media sweep repeated with fresh terms across GLOSSARY, TREE.md, README, START,
  GOAL, docs/README, KANBAN, TODAY, BACKLOG: every other cancellation/cancel hit concerns
  future backlog cards or unrelated features; no standing medium restates the retired
  stop mechanism. The sibling transport GLOSSARY entries and TREE.md taglines match
  present behavior.

Matrix discharge re-checked on the real surface: axis 2 ruled out correctly (16 async
defs, zero sync twins — the sync mentions are prose about reusing upstream's
already-decorated `channels.auth.get_user`); axis 3 verified (`_DEFAULT_REVALIDATION_WINDOW`
spelled once at `consumers.py:377`, imported by `routers.py`; scope keys namespaced once);
axis 4 inapplicability holds (every adaptation one-way; the wrap/unwind pair lives inside
one function).

Single-edit-site recount with MY posited change: "change the revocation close code or
reason" → forces `consumers.py::_REVOCATION_CLOSE_CODE` / `_REVOCATION_CLOSE_REASON`
(391–392) plus the test pin `tests/test_routers.py` `_REVOKED_CLOSE_CODE = 4403` = **2**
sites, no third (all other 4403 spellings derive from those two). Confirms the counting
method and the axis-3 "minimal available restatement" judgment. pytest deferred per
AGENTS.md. Verdict: verified.
