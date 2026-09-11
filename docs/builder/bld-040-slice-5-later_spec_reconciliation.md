# Build: Slice 5 — later-spec reconciliation (Decision 11 and the transport contract)

Spec reference: `docs/SPECS/spec-040-auth_mutations-0_0_13.md` (`### Decision 11` at 1684-1823 post-edit; the swept transport claims are enumerated row by row in `### Conformance matrix` below, each cited by heading rather than by line so the addresses survive the edits this slice itself made)
Status: final-accepted

## Plan (Worker 1)

The **last spec slice** of the `040` retrospective reconciliation cycle, and cohort A
of the declared Slice 5 / Slice 6 partition. It ships no source change and no test.
Its input is the eleven transport hand-offs Slices 2, 3 and 4 deliberately did not
discharge in place, plus the single largest known divergence in the document:
`### Decision 11` states a contract the code inverted after `0.0.13`.

The instrument is the same as Slices 2-4 — decompose the in-scope text into individual
normative statements, grade each against source read directly, edit the spec for every
`SPEC-STALE` row, and append the *why* to the rationale companion keyed by heading and
anchor. What is new here is that the rewrite is **constructive as well as corrective**:
eight of Decision 11's nine claims are false, so grading alone leaves a hole, and the
slice owes the shipped contract in the Decision's place.

### DRY analysis

**Helper inventory checked.** Refreshed package-wide for this pass against the working
tree by sweeping every symbol the transport surface is built from, rather than
re-running the AST dump — the surface is small and closed, and the recurring defect of
this cycle is a named private helper that died while its invariant survived, which only
a symbol sweep catches:

```shell
for s in classify_transport require_session login_supported logout_supported \
  scope_session_lock session_store_class uses_signed_cookie_sessions \
  require_channels _safe_transport_label _require_mutable_scope \
  _transport_prologue _login_authenticate _django_http_login_establish \
  _channels_http_login_establish _login_resolve_body _login_resolve_body_async \
  _logout_prologue _logout_observation _django_http_logout _channels_logout \
  _logout_resolve_body _logout_resolve_body_async _WEBSOCKET_LOGIN_UNSUPPORTED \
  _WEBSOCKET_LOGOUT_UNSUPPORTED _authenticated_actor_or_none request_from_info \
  ChannelsRequestAdapter actor_transition actor_lease scope_singleton scope_key \
  Transport; do
  n=$(rg -c --glob '*.py' -- "$s" . | awk -F: '{s+=$2} END {print s+0}')
  printf "%-34s %s\n" "$s" "$n"
done
```

**32 symbols swept; 32 resolve, none returns 0.** Unlike Slices 2, 3 and 4 — each of
which found exactly one dead name — the transport surface carries no stale symbol at
all, because none of it was ever *in* the spec: the divergence here is not a renamed
helper but a whole module the document never knew existed.

- **Existing patterns reused.** The fence Slices 2-4 built: Decisions 2, 4, 5, 7, the
  three `## Edge cases` bullets and the `## Out of scope` bullet were each converted to
  **pointers** at Decision 11 rather than restatements, so this slice writes the
  transport contract exactly once and none of those six sites needed a second edit for
  it. That fence is what makes a 140-line Decision affordable; without it the same
  content would have had to be kept true in seven places.
- **New helpers justified.** None — a docs-only pass. One new *shape*: the per-surface
  support table, chosen over prose because the answers are a 5x3 matrix and prose had
  already demonstrably drifted across four sections.
- **Duplication risk avoided.** Two, both live. (1) **`spec-046`.** The actor lease, the
  outbound-frame checkpoints, the positive-window cache, the `4403` close and the
  derivation of the lock order are that card's and are **cited, not restated**; what
  `spec-040` states is the effect on its own surface. (2) **`docs/README.md`.** Its
  five-row transport table is the consumer-facing form of the same content and is
  out of scope for this cycle in any case; the spec's table is deliberately a different
  cut of it (a `register` / `current_user` column the consumer table has no use for),
  so neither is a copy of the other.

### Implementation steps

1. Re-verify the spec's status/header lines (`docs/SPECS/spec-040-auth_mutations-0_0_13.md:1-111`).
2. Read `auth/sessions.py` end to end, then every named `auth/mutations.py` transport
   symbol, `utils/sessions.py`, `utils/permissions.py::ChannelsRequestAdapter`,
   `consumers.py`'s session-actor section, `tests/auth/test_sessions.py`,
   `tests/auth/test_mutations.py`'s transport rows, and `spec-046` plus its companion.
3. Decompose old Decision 11 into individual claims; grade each.
4. Sweep the whole spec for transport claims
   (`rg -n -i 'channels|websocket|asgi|middleware|transport|scope'`) and grade every
   hit, including the ones that are not transport claims at all.
5. Rewrite Decision 11 to the shipped contract, including the per-surface table and the
   reason each refusal is a refusal.
6. Discharge the eleven inherited items; verify each pointer now resolves to something
   true.
7. Append the history to the rationale companion, keyed by heading and anchor.
8. Sweep every anchor the two heading renames strand, in both files.

Line numbers in this artifact are pin-at-write-time navigational hints (per-cycle
scratchpad; raw `path:NN` is permitted here and nowhere else).

### Test additions / updates

None — this pass writes no test and may not. One `## Test plan` **row** was added as
spec contract (the transport block), which is a description of coverage that already
exists, not a new obligation: `tests/auth/test_sessions.py` carries 51 rows and
`tests/auth/test_mutations.py` carries 23 Channels / WebSocket rows. No `TEST-GAP` was
recorded, and none is owed. Focused read-only run performed as evidence:

- `uv run pytest tests/auth examples/fakeshop/test_query/test_auth_api.py --no-cov -q`
  → **210 passed** in 9.15s (8 workers). No `--cov*` flag.

### Implementation discretion items

None. Every verdict below is decided.

### Spec slice checklist (verbatim)

This slice implements no `## Slice checklist` block of the spec — it is a reconciliation
slice of a shipped card, and the build plan's checklist item for it is a single line. The
**eleven inherited transport hand-offs** stand in, copied verbatim from the three prior
artifacts' `### Notes for Worker 1 (spec reconciliation)` sections, under the identical
tick-and-audit discipline: a box is ticked only where the obligation it states is
discharged in this pass's diff.

From `bld-040-slice-2-audit_substrate_login_logout.md` (six):

- [x] 1. `django_strawberry_framework/auth/sessions.py` is a fourth `auth/` module Decision 11 still names nowhere. Decision 4 now lists its **location and privacy only**; its **contract** — `::Transport`'s three modes, `::classify_transport`, `::require_session`, `::login_supported` / `::logout_supported`, `::scope_session_lock`, `::uses_signed_cookie_sessions` — is unwritten and is Slice 5's.
- [x] 2. Decision 5's resolver steps now say the transport prologue runs first and point at Decision 11. Slice 5 must write what that prologue *does*: classify → capability → `require_session`, all before the gate and before any credential or session work (`auth/mutations.py::_transport_prologue`).
- [x] 3. The two WebSocket rejection constants — `::_WEBSOCKET_LOGIN_UNSUPPORTED` and `::_WEBSOCKET_LOGOUT_UNSUPPORTED` — are `ConfigurationError`s raised *before* any session mutation, deliberately outside the byte-compatible failed-login envelope. Neither appears in the spec, in Decision 5's step list or the `### Error shapes` table. Slice 5 owns both the Decision 11 text and the two `### Error shapes` rows.
- [x] 4. Decision 2's Channels clause was rewritten to point at Decision 11 rather than to state a transport contract. If Slice 5's Decision 11 rewrite changes what the auth surface accepts, Decision 2 needs no second edit — it now carries no transport claim of its own. That is the intent.
- [x] 5. `auth/mutations.py::_login_resolve_body` and `::_logout_resolve_body` take a single `async_to_sync` hop at the private transport boundary for a classified Channels HTTP scope under sync execution. This is a sync→async hop the spec describes nowhere, and Decision 10's "one boundary" claim is about `sync_to_async`, not this. It is a transport behavior: **Slice 5's**.
- [x] 6. `auth/mutations.py::_channels_logout` runs the teardown inside `utils/sessions.py::actor_transition` and documents a two-lock order (scope session lock OUTER, actor lease INNER) against `spec-046` Decision 11's WebSocket revalidation. That cross-spec interaction is stated only in a docstring. Slice 5 should decide whether `spec-040` states it or defers to `spec-046`.

From `bld-040-slice-3-audit_register_current_user.md` (one):

- [x] 7. If Slice 5's Decision 11 rewrite enumerates per-surface transport support, `current_user` belongs in it as "every transport, read-only, no session mutation" — and that is the only place it should be stated.

From `bld-040-slice-4-audit_obligations_edges_tests.md` (four):

- [x] 8. `auth/sessions.py::require_session` now has an `## Edge cases` home that states what it does and points here for the per-transport behaviour. Slice 5 owes Decision 11 the contract: which transports it accepts a missing session on, the Django-vs-Channels `session is None` shapes it collapses, and the `_safe_transport_label` naming in the message. The message's substring promise (`"session"`) is stated in the edge case; do not restate it in Decision 11, restate only what the edge case points at.
- [x] 9. The anonymous-logout and async-contexts edge cases now point at Decision 11 for the per-transport split (which teardown runs; whether the session work rides the sync boundary or is awaited natively after it). Neither carries a transport claim of its own, so Slice 5's rewrite needs no second edit to `## Edge cases`.
- [x] 10. `## Out of scope`'s Channels bullet no longer says the websocket/consumer-scope auth story is out of scope — it now scopes itself to the **router card** and defers the transport contract to Decision 11. If Slice 5's Decision 11 enumerates per-surface transport support, that list is the only place the WebSocket `login` and signed-cookie `logout` rejections should appear.
- [x] 11. Slice 3's item 7 stands unchanged: `current_user` is transport-neutral and belongs in Decision 11's per-surface table as "every transport, read-only, no session mutation". This slice's E.21 and T.18 rows confirm it — `queries.py` has no transport branch.

**How each was discharged** is recorded under `### Notes for Worker 1 (spec reconciliation)`.

---

## Conformance matrix

Verdict vocabulary as Slices 2-4 used it: `CONFORMS` / `SPEC-STALE` / `CODE-GAP` /
`TEST-GAP` / `UNPROVABLE`. Every row is graded against source read directly at the
working tree, and the three rows whose subject is a concurrently-edited file were
re-checked against `git show HEAD:` (see the working-tree note).

### Block D11 — the claims old Decision 11 made

| # | Claim as the spec stated it | Graded against | Verdict |
|---|---|---|---|
| D11.1 | "requires Django's session stack — `django.contrib.sessions` + `SessionMiddleware` + `AuthenticationMiddleware` on the `/graphql/` request path" | `sessions.py::require_session` names `SessionMiddleware` **and** `AuthMiddlewareStack` per transport; the actor loader differs by transport (`AuthenticationMiddleware` vs `AuthMiddlewareStack`); and since `spec-046` the package composes no fixed `/graphql/` ASGI path | **`SPEC-STALE`** |
| D11.2 | "This is documented, not probed … the package does not add a bespoke pre-flight check" | `sessions.py::require_session` IS a bespoke pre-flight check, called from `mutations.py::_transport_prologue` on every `login` / `logout` | **`SPEC-STALE`** |
| D11.3 | "a sessionless deployment hitting `auth.login` gets Django's own error" | it gets the package's `ConfigurationError` naming the transport and the middleware; `tests/auth/test_sessions.py::test_require_session_missing_django_middleware_raises_with_the_session_substring` | **`SPEC-STALE`** |
| D11.4 | "CSRF is the consumer's transport concern exactly as for every existing mutation; nothing auth-specific changes it" | no auth module touches CSRF; `auth.login`'s `rotate_token` is Django's own. Still true | `CONFORMS` |
| D11.5 | "Upstream's two Channels fallbacks … are **deliberately not borrowed**" | half false: `mutations.py::_channels_http_login_establish` imports `channels.auth.login` and `::_channels_logout` imports `channels.auth.logout`. What is not borrowed is the *fallback shape*, not the capability | **`SPEC-STALE`** |
| D11.6 | "The package has no Channels surface until the `0.0.14` [router] card" | the router card shipped (`DONE-041-0.0.14`) and `auth/sessions.py` classifies its scopes | **`SPEC-STALE`** |
| D11.7 | "shipping a fallback no supported transport can reach would be dead, untestable code under the 100% gate" | the premise is void: `tests/auth/test_sessions.py` carries 51 rows and `tests/auth/test_mutations.py` 23 Channels / WebSocket rows | **`SPEC-STALE`** |
| D11.8 | "The router card inherits the question ('does `041` extend auth to consumer-scope sessions?')" | answered in code, not by `041`: extended for HTTP scopes and for server-side-engine WebSocket `logout`, refused for WebSocket `login` and signed-cookie WebSocket `logout` | **`SPEC-STALE`** |
| D11.9 | the **heading**: "Session-transport constraints: `SessionMiddleware` + `AuthenticationMiddleware`; the Channels fallback is NOT borrowed" | both halves falsified by D11.1 and D11.5; a heading is the first thing a decision-list reader sees | **`SPEC-STALE`** |

### Block T — the shipped contract the rewrite now states

Each row is a normative statement the new Decision 11 makes, graded against the source
it is derived from. A row here is `CONFORMS` when the spec text and the code agree
**after** this pass's edit — the point of the block is that every sentence written into
the Decision was read out of the tree, not composed from the commit messages.

| # | Statement now in the spec | Source | Verdict |
|---|---|---|---|
| T.1 | three explicit modes — `DJANGO_HTTP` / `CHANNELS_HTTP` / `CHANNELS_WEBSOCKET` — resolved by an `isinstance` check against the adapter first, then `scope["type"]` | `sessions.py::Transport`, `::classify_transport`; `tests/auth/test_sessions.py::test_classify_django_httprequest_takes_the_native_path`, `::test_classify_channels_http_scope`, `::test_classify_channels_websocket_scope` | `CONFORMS` |
| T.2 | the transport is never detected by catching `AttributeError` from Django's auth functions | `classify_transport` raises `ConfigurationError` for every unrecognized object / scope type; `::test_classify_rejects_an_unknown_transport_object`, `::test_classify_rejects_missing_or_unknown_scope_type` | `CONFORMS` |
| T.3 | importing the module stays `channels`-free; the soft dependency is forced only after a Channels scope is recognized, through the shared install-hint family | `sessions.py::require_channels` over `utils/imports.py::require_optional_module`; `::test_auth_submodule_import_stays_channels_free`, `::test_classify_channels_scope_without_channels_raises_the_install_hint` | `CONFORMS` |
| T.4 | the prologue's fixed order — classify → capability → session — runs before the gate and before any credential or session work | `mutations.py::_transport_prologue` (the `authorize_or_raise` call follows it in both `::_login_authenticate` and `::_logout_prologue`) | `CONFORMS` |
| T.5 | `login` is refused on **any** WebSocket, whatever the engine, because the socket cannot return the rotated cookie | `sessions.py::login_supported`; `::test_login_supported_everywhere_except_websocket` | `CONFORMS` |
| T.6 | `logout` is refused only on a signed-cookie-engine WebSocket, and the check recognizes a **subclassed** signed-cookie engine | `sessions.py::logout_supported` / `::uses_signed_cookie_sessions`; `::test_logout_supported_except_signed_cookie_websocket`, `::test_signed_cookie_detection_follows_a_subclassed_engine` | `CONFORMS` |
| T.7 | both refusals fire before authentication / before any session mutation and are top-level errors outside the failed-login envelope | `mutations.py::_WEBSOCKET_LOGIN_UNSUPPORTED`, `::_WEBSOCKET_LOGOUT_UNSUPPORTED`; `tests/auth/test_mutations.py::test_websocket_login_is_rejected_before_authenticate_is_called`, `::test_websocket_signed_cookie_logout_rejected_before_any_mutation` | `CONFORMS` |
| T.8 | `require_session` collapses the Django no-`session`-attribute shape and the adapter `session is None` shape into one error naming the transport | `sessions.py::require_session` + `::_safe_transport_label`; `::test_require_session_none_channels_session_raises` and its Django twin | `CONFORMS` |
| T.9 | Django HTTP login: native `login` + an explicit `request.session.save()`, `modified` left set so `SessionMiddleware` still emits the rotated cookie | `mutations.py::_django_http_login_establish` | `CONFORMS` |
| T.10 | Channels login: `channels.auth.login` + an explicit `await session.asave()`, because Channels' `login` does not persist the keys it writes | `mutations.py::_channels_http_login_establish`; `tests/auth/test_mutations.py::test_channels_http_login_round_trip_sets_cookie_keys_and_authenticates` | `CONFORMS` |
| T.11 | Channels logout adds no save — the native flush is itself durable | `mutations.py::_channels_logout`; `::test_channels_http_logout_invalidates_cookie_and_durable_session` | `CONFORMS` |
| T.12 | every post-authentication failure is fail-closed: actor anonymized, partial durable state flushed, original error re-raised with cleanup chained via `__context__` | `::_django_http_login_establish`, `::_channels_http_login_establish`, `::_django_http_logout`, `::_channels_logout`; `::test_channels_http_login_cleanup_failure_retains_primary_and_chains_cleanup` and siblings | `CONFORMS` |
| T.13 | one per-scope `asyncio.Lock` stored on the ASGI scope, never a process-global registry or `ContextVar` | `sessions.py::scope_session_lock` over `utils/sessions.py::scope_singleton`; `::test_locks_are_scope_owned_and_independent_across_scopes`, `::test_no_process_global_lock_registry_in_the_sessions_module` | `CONFORMS` |
| T.14 | under sync execution a classified Channels HTTP scope takes a **single** `async_to_sync` bridge at the private transport boundary | `mutations.py::_login_resolve_body`, `::_logout_resolve_body`; `tests/auth/test_mutations.py::test_sync_channels_http_bridge_establishes_and_persists_the_session`, `::test_sync_channels_http_logout_bridge_tears_down_the_session` | `CONFORMS` |
| T.15 | under async execution a Django request rides the existing thread-sensitive boundary and a Channels scope is awaited natively, with no nested `async_to_sync` | `::_login_resolve_body_async`, `::_logout_resolve_body_async` | `CONFORMS` |
| T.16 | classification is pure (no ORM), so it never trips `SynchronousOnlyOperation` | `classify_transport` performs no query; the async bodies classify on the loop before entering any boundary | `CONFORMS` |
| T.17 | lock order — scope session lock OUTER, actor lease INNER — with `::_channels_logout` the only site holding both | `mutations.py::_channels_logout`, `utils/sessions.py::actor_transition`; `spec-046` Decision 16 states the same order | `CONFORMS` |
| T.18 | a same-connection WebSocket `logout` is a connection-scoped revocation event: the socket closes at its next protected checkpoint and the payload does not reach the client | `consumers.py` module docstring #"A same-connection ``logout`` is a revocation event"; `tests/auth/test_mutations.py::test_channels_logout_latches_the_provenance_of_the_actor_it_revoked` | `CONFORMS` |
| T.19 | `current_user` is transport-neutral: no prologue, no classification, no branch | `auth/queries.py::_current_user_resolve_body` — `request_from_info` then `_authenticated_actor_or_none`, and the module imports `sessions` nowhere | `CONFORMS` |
| T.20 | `register` is transport-neutral: it writes a row and never a session | `mutations.py::_run_register_pipeline_sync` / `::_register_write_step` — no `sessions.` reference on the register path | `CONFORMS` |
| T.21 | the package router serves no GraphQL `http` scope, so a `CHANNELS_HTTP` scope reaches the auth boundary only from a consumer-mounted HTTP consumer | `spec-046` Decision 2 #"The package stops *composing* a Channels HTTP GraphQL route"; `dde7c857` put the same sentence in both resolver docstrings | `CONFORMS` |

### Block S — transport claims elsewhere in the spec

Population: the 74 hits of
`rg -n -i 'channels|websocket|asgi|middleware|transport|scope' docs/SPECS/spec-040-auth_mutations-0_0_13.md`
at the start of the pass, deduplicated to the 21 distinct claims below. The hits not
listed are non-transport uses of the words — card scope, test scope, `Meta` scope, the
`## Current state` module-layout row, and the "failure *transport*" metaphor in
`## Borrowing posture` — each read and dismissed.

| # | Site | Claim | Verdict |
|---|---|---|---|
| S.1 | `## Key glossary references`, the router / test-client bullet | "Channels / websocket login (upstream's `channels_auth` fallback) waits for the router card" | **`SPEC-STALE`** |
| S.2 | `## Non-goals`, first bullet | "not borrowed **until** the `0.0.14` router card gives the package a Channels story" — a conditional whose condition is met | **`SPEC-STALE`** |
| S.3 | `## Borrowing posture`, the `get_current_user` borrow | "The ASGI-scope fallbacks are **not** borrowed" — true of the fallback shape, false as a claim that `me` does not work over a scope | **`SPEC-STALE`** |
| S.4 | `### Explicitly do not borrow` | "The `channels_auth` fallback and the consumer-scope user extraction. Both are Channels-transport concerns deferred to the `0.0.14` router card" | **`SPEC-STALE`** |
| S.5 | `### Error shapes` | the table maps every documented failure to where it lands and carried **no** row for either WebSocket refusal | **`SPEC-STALE`** (omission) |
| S.6 | Decision 2 heading | "session auth ships; Channels / token auth stay out" — the Channels half contradicts Decision 11 at a glance | **`SPEC-STALE`** |
| S.7 | Decision 2 body | Slice 2's pointer: "which transports the four auth fields accept … is Decision 11's single statement" — **verified**: it now resolves to a Decision that states exactly that | `CONFORMS` |
| S.8 | Decision 4, the `auth/sessions.py` bullet | location + privacy + `channels`-free import, "its contract is Decision 11's" — resolves to something true | `CONFORMS` |
| S.9 | Decision 5 `**Resolver semantics**` lead-in | the prologue runs first and is Decision 11's — resolves; the Decision now says what it does | `CONFORMS` |
| S.10 | Decision 5 step 5 | the anonymity enumeration named "no `user` attribute at all (`SessionMiddleware` without `AuthenticationMiddleware`)" and "a `user` that is unauthenticated" — neither describes the adapter, which has a `user` property returning `None` | **`SPEC-STALE`** |
| S.11 | Decision 7's "otherwise" | already names both shapes (Slice 3's edit) — re-verified against `_authenticated_actor_or_none` | `CONFORMS` |
| S.12 | Decision 7, the no-queryset-work clause | "the returned object is `request.user`, already loaded by `AuthenticationMiddleware`" — one transport's spelling of a transport-neutral invariant | **`SPEC-STALE`** |
| S.13 | Decision 7's "per-transport specialization point" | Slice 3's edit; matches the sync / async body split `c8346750` made | `CONFORMS` |
| S.14 | `## Edge cases`, **Anonymous logout** | "which teardown runs is Decision 11's" — resolves (the per-transport establishment / teardown paragraph) | `CONFORMS` |
| S.15 | `## Edge cases`, **Sessionless / middleware-less** | "the pre-check is single-sited in the shared transport prologue and its per-transport behaviour is Decision 11's" — resolves (prologue step 3); the substring promise stays here and is not restated there | `CONFORMS` |
| S.16 | `## Edge cases`, **Async contexts** | "whether the session work rides that same boundary or is awaited natively afterwards is the transport's business (Decision 11 for the per-transport split)" — resolves (the sync / async paragraph) | `CONFORMS` |
| S.17 | `## Out of scope`, the router bullet | "which transports the four auth fields accept … is stated once in Decision 11 and nowhere else, this list included" — resolves, and the table is that one statement | `CONFORMS` |
| S.18 | `## Doc updates`, the Slice 3 GLOSSARY obligation | the entry must carry "the no-Channels constraint" — honoured at the cut, but stated in a vocabulary the surface outgrew; the entry today describes the opposite | **`SPEC-STALE`** |
| S.19 | `## Test plan`, package-internal | no transport row of any kind, though Decision 4 names `tests/auth/test_sessions.py` and the file carries 51 rows | **`SPEC-STALE`** (omission; a description gap, **not** a `TEST-GAP` — the coverage exists) |
| S.20 | `## Test plan`, the live CSRF row | "`login` and `logout` face Django's real CSRF check over the live transport" — still true of the live fakeshop mount | `CONFORMS` |
| S.21 | `## Current state` | "`middleware/` for `042`, `testing/client.py` for `043`" — a module-layout observation, not a transport claim about this surface | `CONFORMS` |

### Verdict tally

Row counts are the `len()` of each block above, re-counted as this table was written:
D11 = 9, T = 21, S = 21.

| Verdict | Count |
|---|---|
| `CONFORMS` | 33 |
| `SPEC-STALE` | 18 |
| `CODE-GAP` | **0** |
| `TEST-GAP` | **0** |
| `UNPROVABLE` | 0 |
| **Total rows** | **51** |

The eighteen `SPEC-STALE` rows, listed so the count is re-derivable rather than
asserted: D11.1, D11.2, D11.3, D11.5, D11.6, D11.7, D11.8, D11.9, S.1, S.2, S.3, S.4,
S.5, S.6, S.10, S.12, S.18, S.19. All eighteen are discharged by the twelve edits below
(the eight D11 rows are one rewrite; S.3 and S.4 are two edits in one section).

**Zero code gaps again.** Across the cycle's four graded slices the running total is
**327 rows and one code gap** — the `D-N3` missing source comment Slice 4 found. The
transport surface in particular is the opposite of a dropped deliverable: it is work the
spec never asked for, shipped after the card closed, and never written back.

### Boundary-removal reasoning (read-only)

No mutation was applied — this pass may not mutate source. For each boundary the new
Decision-11 text rests on, whether a test would fail if it were removed, by reading:

- **The capability refusals** (T.5 / T.7): deleting the `login_supported` arm makes
  `test_websocket_login_is_rejected_before_authenticate_is_called` fail on its
  "authenticate was never called" assertion as well as on the raise; deleting the
  `logout_supported` arm fails `test_websocket_signed_cookie_logout_rejected_before_any_mutation`
  and the signed-cookie predicate rows. Strongly pinned on both.
- **The subclass check** (T.6): narrowing `issubclass` to `is` fails
  `test_signed_cookie_detection_follows_a_subclassed_engine` specifically — the row
  exists for exactly this weakening.
- **`require_session`** (T.8): removing it lets a `None` session reach the native
  login; `test_require_session_missing_django_middleware_raises_…` and
  `test_require_session_none_channels_session_raises` both fail, and the sessionless
  `tests/auth/test_mutations.py` row fails on the error class.
- **The scope lock** (T.13): the lock's *serialization* is the boundary
  `START.md` catalogues as harness-impossible in-process — but
  `test_no_process_global_lock_registry_in_the_sessions_module` and
  `test_locks_are_scope_owned_and_independent_across_scopes` pin the **placement**
  claim this spec makes, and both fail if the lock moves to a module-level dict.
  The placement is what Decision 11 states; the ordering argument is `spec-046`'s.
- **The single `async_to_sync` hop** (T.14): removing the bridge makes
  `test_sync_channels_http_bridge_establishes_and_persists_the_session` fail with an
  un-awaited coroutine. Nesting a *second* bridge inside the async path is **not**
  pinned by any row this audit could find — but the spec's claim there is the
  boundary **count**, which is Decision 10's and was graded by Slice 2; no new
  obligation is created here.

---

### Notes for Worker 1 (spec reconciliation)

**The eleven inherited items, discharged.**

1. *(Slice 2 item 1)* `auth/sessions.py`'s contract. **Done** — Decision 11 now states
   every named symbol's invariant: the three `Transport` modes and how
   `classify_transport` resolves them (prologue step 1), `require_session`'s two
   collapsed shapes (step 3), `login_supported` / `logout_supported` as the per-surface
   capability predicate plus the reason each answer is what it is, `scope_session_lock`
   as one scope-owned lock, and `uses_signed_cookie_sessions` as a settings read rather
   than adapter metadata. Rows T.1-T.8, T.13.
2. *(Slice 2 item 2)* What the prologue *does*. **Done** — the fixed
   classify → capability → session order, stated as running before the gate and before
   any credential or session work, cited to `::_transport_prologue`. Row T.4.
3. *(Slice 2 item 3)* The two rejection constants. **Done** — named in prologue step 2
   as the pinned per-surface messages, given their reasons in the refusal block, and
   given the two `### Error shapes` rows Slice 2 deliberately withheld. Rows T.7, S.5.
4. *(Slice 2 item 4)* Decision 2 needs no second transport edit. **Confirmed** — its
   body carries a pointer only, and the pointer now resolves to something true (row
   S.7). Its **heading** was a separate defect and was fixed; see the cross-slice note
   below.
5. *(Slice 2 item 5)* The `async_to_sync` hop. **Done** — stated as the one permitted
   sync→async hop at the private transport boundary, with the async side's native await
   stated beside it and Decision 10's count invariant explicitly left intact. Rows
   T.14, T.15.
6. *(Slice 2 item 6)* Whether `spec-040` states the cross-spec lock order or defers.
   **Ruled: both, split by what each spec owns.** `spec-046` owns the lease, the
   checkpoints and the derivation and is cited (Decisions 2 and 16). `spec-040` states
   the two things that bind its own bodies: the lock order, because
   `::_channels_logout` is the only site that holds both and the rule constrains an
   auth-side body; and the consumer-visible effect, that a same-connection `logout` is
   a connection-scoped revocation event whose payload does not reach the client. Rows
   T.17, T.18.
7. *(Slice 3 item 7)* `current_user` in the per-surface table. **Done** — the table's
   third column is `register` / `current_user`, "supported" on every row, and the
   prose above it states the invariant (no prologue, no classification, no branch) with
   the reason it holds. Rows T.19, T.20.
8. *(Slice 4 item 8)* `require_session`'s per-transport contract. **Done** as prologue
   step 3, and the instruction was followed precisely: the substring promise stays in
   `## Edge cases` and Decision 11 restates only what the edge case points at — which
   transports it fires on (all three), the two shapes it collapses, and that the
   message names the transport. Row T.8.
9. *(Slice 4 item 9)* The anonymous-logout and async-contexts edge cases. **Confirmed
   discharged with no edit to `## Edge cases`** — both pointers resolve to new
   paragraphs (rows S.14, S.16). Recorded explicitly so a later pass does not read the
   absence of an edit as an unaudited section.
10. *(Slice 4 item 10)* The `## Out of scope` Channels bullet. **Confirmed** — it
    resolves, and the per-surface table is the single home of both WebSocket
    rejections, which appear in no other list (row S.17).
11. *(Slice 4 item 11)* Slice 3's item 7, restated. **Done** with item 7 above.

**Cross-slice corrections — closed decisions this pass edited.** Recorded explicitly
rather than left as invisible overwrites, per the task fence:

- **Decision 2's heading** (Slice 2's decision, closed). Slice 2 converted the body to a
  pointer but the heading still read "session auth ships; Channels / token auth stay
  out". Renamed to "token auth stays out"; the card-scope framing is unchanged and no
  other clause moved. The rename carried four in-page anchors in the spec, two in the
  companion, and the companion's `[spec-040-d2]` definition and mirrored heading.
  Row S.6, edit 8.
- **Decision 5's step 5** (Slice 2's, closed). Its two-arm anonymity enumeration did not
  cover the adapter shape, while Decision 7's twin sentence did after Slice 3's edit —
  so the two Decisions disagreed about a classification they explicitly share. Row
  S.10, edit 9.
- **Decision 7's no-queryset-work clause** (Slice 3's, closed). "The returned object is
  `request.user`, already loaded by `AuthenticationMiddleware`" is the Django spelling
  of a transport-neutral invariant, and stating it that way weakens the very claim that
  puts `current_user` in Decision 11's table. Row S.12, edit 10.
- **`## Test plan`** (Slice 4's, closed). One row added for the transport block. Row
  S.19, edit 11.
- **`## Doc updates`** (Slice 4's, closed). One clause reworded. Row S.18, edit 12.

**Open for the integration pass.**

- **A stranded anchor in another slice's artifact.**
  `docs/builder/bld-040-slice-1-rationale_extraction.md` contains one link to the old
  Decision 11 anchor. It is another slice's artifact and on this slice's do-not-touch
  list, and per-cycle artifacts are exempt from the standing citation rules
  (`START.md` "Per-cycle scratch closes w/ cycle"), so it was **not edited**. The
  integration pass owns whether a closed artifact's in-cycle link is repaired or left
  as the record of what Slice 1 read.
- **Two `WIP-ALPHA-040-0.0.13` sites Slice 4 recorded and did not edit** (`spec-040`
  Decision 1, and the `## Slice checklist` Slice-3 card-wrap sub-bullet) are still
  open. Neither is a transport claim, so neither is this slice's; they remain exactly
  as Slice 4 left them.
- **The spec's own byte delta for this slice is not derivable from the record.**
  Slice 2 recorded `164,391 B → 169,338 B` and Slice 3 and 4 recorded no closing
  figure, so there is no post-Slice-4 measurement to difference against. Measured now:
  the spec is **194,963 B** and the companion **130,270 B**. No per-slice delta is
  asserted, because none was measured — the `START.md` "count right in every digit,
  wrong in subject" hazard.
- **`docs/README.md`'s transport table and `docs/GLOSSARY.md`'s auth entry both already
  carry the current transport contract** and agree with the rewritten Decision 11 on
  every row — checked read-only, three-way, as the one cross-check no single home can
  run. Both are outside this cycle's scope fence, and neither needed a change. Noted so
  a later pass knows the agreement was measured rather than assumed.

**Working-tree note (stop-and-report, no action taken).** `git status --short` at the
end of this pass shows **twenty** modified files this slice did not write —
`docs/feedback.md`, `docs/GLOSSARY.md`, `docs/spec-050-list_field_arguments-0_0_15.md`,
`docs/builder/bld-final.md`, `docs/builder/bld-slice-3-sql_and_unit_contracts.md`,
`examples/fakeshop/db.sqlite3`, and fourteen `.py` files under
`django_strawberry_framework/`, `tests/` and `examples/fakeshop/test_query/` — plus the
other slices' untracked artifacts. The set is the concurrent `spec-050` session's plus
cohort B's, it **grew during this pass** (the mid-pass reading was fifteen), and none is
on this slice's writable list — concurrent work per `AGENTS.md` rule 34. **Not reverted,
not reported as this slice's churn.**

Three files this slice **read as source under audit** are in that set, all cohort B's:
`django_strawberry_framework/auth/mutations.py`, `tests/auth/test_mutations.py` and
`examples/fakeshop/test_query/test_auth_api.py`. They were clean when read (absent from
the mid-pass `git status --short`), and re-checked at the end of the pass:
`git diff --stat HEAD --` on the three reports `14 insertions, 10 deletions` total,
and reading the diff confirms it is exactly what the plan predicted — the `CG-1` `D-N3`
source comment on the rider's `Meta`, and the `Revision-7` citation removals from Slice
3's `F2`. **No transport symbol, docstring or test row this matrix cites is touched by
it**, so every row citing those three files holds against `HEAD`, against the mid-pass
tree, and against the tree as it stands. `django_strawberry_framework/utils/querysets.py`
is dirty and hosts nothing this slice cites.

### Spec changes made (Worker 1 only)

All in `docs/SPECS/spec-040-auth_mutations-0_0_13.md`; line numbers are post-edit. Every
"why" is appended to `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`,
under the owning Decision's `### Changes this Decision underwent` or under
`## Spec sections outside the Decisions — changes they underwent`.

| # | Spec lines | Change | Reason |
|---|---|---|---|
| 1 | 1684-1823 | **Decision 11 rewritten end to end** and **renamed** to "Transport contract: classify first, refuse a transport that cannot honour the surface truthfully": the requirement stated per transport; the prologue's three fixed steps; the per-surface support table; the reason each of the two refusals is a refusal rather than a gap; the per-transport establishment / teardown asymmetry and its fail-closed compensation; the one scope-owned lock; the sync / async hop; the `spec-046` boundary; and what of upstream is still not borrowed | Rows D11.1-D11.9 — eight of nine claims falsified, heading included |
| 2 | 11 spec anchors + 5 companion anchors + `[rationale-d11]` + `[spec-040-d11]` + the companion's mirrored heading and `Spec:` line | the Decision 11 rename's anchor sweep, both files | Row D11.9 — a heading rewrite strands every in-page anchor (`START.md` "Markdown link convention") |
| 3 | 197-202 | `## Key glossary references`: the router / test-client bullet keeps the card-scope fact and hands the transport answer to Decision 11 | Row S.1 |
| 4 | 555-562 | `## Non-goals`: the Channels bullet restated as the card-scope non-goal it is (no router, no consumer, no scope handling) plus the fallback *shape* as the thing still not borrowed on any transport | Row S.2 — its "until the router card" condition has been met |
| 5 | 626-630 | `## Borrowing posture`: the `get_current_user` borrow says the ASGI-scope **fallback** is not borrowed and that `me` needs no scope branch because `request_from_info` resolves either shape | Row S.3 |
| 6 | 651-657 | `### Explicitly do not borrow`: the bullet split — the fallback *shape* is refused, the Channels *capability* is used on an already-classified scope | Row S.4 |
| 7 | 787-788 | `### Error shapes`: two new rows — `login` over any Channels WebSocket, and `logout` over a signed-cookie-engine Channels WebSocket | Row S.5 (Slice 2 hand-off 3) |
| 8 | 816 + 4 in-page anchors | **Decision 2 renamed** to "session auth ships; token auth stays out; no new `Meta` / settings key" | Row S.6 — **cross-slice correction** into a decision Slice 2 closed |
| 9 | 941-945 | Decision 5 step 5: the anonymity enumeration gains the adapter shape and the classification is stated as stable across transports | Row S.10 — **cross-slice correction** (Slice 2's decision) |
| 10 | 1423-1426 | Decision 7: the returned actor restated as "the actor the transport's own middleware already loaded", naming both spellings | Row S.12 — **cross-slice correction** (Slice 3's decision) |
| 11 | 2296-2313 | `## Test plan`: a transport row — the classification / capability / lock obligations in `tests/auth/test_sessions.py`, the two resolver-level refusals and the Channels round trips in `tests/auth/test_mutations.py`, and why the whole block is `tests/auth/` rather than live | Row S.19 — **cross-slice correction** (Slice 4's section) |
| 12 | 2373-2375 | `## Doc updates`: "the no-Channels constraint" → "the session-transport constraint", pointing at Decision 11 | Row S.18 — **cross-slice correction** (Slice 4's section) |

Link definitions added to the spec, each alphabetical within its group and each
verified to resolve from `docs/SPECS/`: `[glossary-channels-request-adapter]` under
`<!-- docs/ -->`; `[spec-046]`, `[spec-046-d2]`, `[spec-046-d16]` under
`<!-- docs/SPECS/ -->`; `[utils-sessions]` under
`<!-- django_strawberry_framework/ -->`.

Rationale companion: a `### Changes this Decision underwent` bullet set appended under
Decision 11 (the inversion itself, the later commits folded into it, the `spec-046`
boundary, why the answers are a table, and a `No longer claims` bullet), plus one bullet
each under Decisions 2, 5 and 7 for the cross-slice corrections, and four new
`###` sub-sections under `## Spec sections outside the Decisions` keyed by spec heading
and anchor (`## Key glossary references`, `## Non-goals`, `## Borrowing posture`,
`### Error shapes`) plus one appended bullet each to the existing `## Test plan` and
`## Doc updates` sub-sections. That section's lead-in, which named Slice 4 as the sole
author, now names the slice per bullet. Every entry names what the text claimed, the
commit that changed it (`c8346750`, `44b33e9f`, `2a62d8b5`, `6873dac6`, `eed67f6c`,
`05a08e31`, `0fa6501d`, `dde7c857`, `c537b2dc`) or the card that did
(`DONE-041-0.0.14`), and what it may no longer claim. Link definitions added there:
`[spec-040-glossary-refs]`, `[spec-040-non-goals]`, `[spec-046]` under
`<!-- docs/SPECS/ -->` and `[bld-040-slice-5]` under `<!-- docs/builder/ -->`.

**No spec edit touched Decisions 1, 3, 4, 6, 8, 9, 10 or 12, the `## Slice checklist`,
`## Current state`, `## Borrowing posture`'s first two subsections, `## Goals`,
`## Implementation plan`, `## Helper-reuse obligations (DRY)`, `## Edge cases and
constraints`, `## Out of scope` or `## Definition of done`.**

---

## Final verification (Worker 1)

No `CODE-GAP` and no `TEST-GAP` row, so this closes as a Worker-1-only slice; no
Worker 2 or Worker 3 pass is owed, and cohort B's Slice 6 is unaffected by anything
here (the partition holds: this pass wrote four files, all on cohort A's list).

- **Inherited-items checklist:** 11 of 11 boxes `- [x]`, each discharged above with the
  spec text that discharges it named. No box left `- [ ]`; no deferral reason owed.
- **Conformance matrix:** 51 rows — 33 `CONFORMS`, 18 `SPEC-STALE`, 0 `CODE-GAP`,
  0 `TEST-GAP`, 0 `UNPROVABLE`. Every `SPEC-STALE` row was discharged by an edit in
  this pass; none deferred.
- **Spec status/header lines re-verified** (`:1-111`): the `Status:` line reads
  **SHIPPED (`0.0.13`)**, the predecessor list and the `docs/GLOSSARY.md` sentence are
  the corrected ones Slice 2 landed, and the rationale-companion pointer resolves. No
  edit owed this spawn.
- **DRY check across this slice and Slices 1-4:** no new duplication. The transport
  contract is stated in exactly one place; the six sites Slices 2-4 converted to
  pointers were re-read and all six still carry pointers only. The one deliberate
  near-duplicate — `docs/README.md`'s consumer table — is a different cut of the same
  matrix in a file outside this cycle's fence, and the spec's table adds a column it
  does not carry.
- **Existing tests still run:**
  `uv run pytest tests/auth examples/fakeshop/test_query/test_auth_api.py --no-cov -q`
  → **210 passed**, 0 failed, 0 errors. No `--cov*` flag (`BUILD.md` `## Coverage is
  the maintainer's gate, not a worker's tool`).
- **Fail-open shapes:** none introduced — this pass writes no executable code. The one
  fail-open-shaped construct in the audited surface,
  `sessions.py::uses_signed_cookie_sessions`, was read: its `except BaseException` arms
  **re-raise** as `ConfigurationError` rather than returning a default, and
  `logout_supported` therefore cannot answer "supported" because a check blew up. The
  spec now states the answer-guarding form (refuse unless the store is provably not
  signed-cookie). No finding.
- **Hot-path:** the plan declares `none` for this slice and no code changed. **Not
  applicable.**
- **Floor verification:** the plan declares `none` for this slice, same reason. **No
  floor scope owed.**
- **Gates run:**
  - `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md`
    → `OK: 30 terms - all have glossary entries and at least one spec link.` (exit 0)
  - In-page anchors, both files: every `](#…)` target resolves against a real heading
    (spec: 34 headings, 0 missing; companion: 32 headings, 0 missing), checked with a
    slug function implementing `START.md`'s GitHub-slug rule rather than by eye — the
    two heading renames make eye-checking exactly the wrong instrument.
  - Reference-style convention, both files: every `][label]` has a definition and every
    definition a use (0 undefined, 0 unused); all ten canonical group headers present
    and unchanged; every new definition alphabetical within its group and resolving on
    disk **from its own file's directory** (the companion sits one level deeper, so its
    `spec-046` definition is `../spec-046-…` where the spec's is `spec-046-…`).
  - `uvx pre-commit run --files …` — see below.
  - `git status --short` — only writable-list paths changed by this pass.
- **Spec reconciliation:** done in-pass; 12 edits recorded above.
- **Final status:** `final-accepted`.

### Summary

`spec-040`'s Decision 11 said the package supports one transport and deliberately
declines the Channels path. Eight of its nine claims were false and the ninth was its
CSRF sentence. The Decision now states the shipped contract directly: every `login` /
`logout` classifies the request into one of three explicit transport modes before the
permission gate and before any credential or session work, checks a per-surface
capability, and pre-checks the session; a WebSocket `login` and a signed-cookie
WebSocket `logout` are **refused**, each with the reason that makes the refusal correct
rather than unfinished; and the per-transport establishment, teardown, compensation,
locking and sync/async behaviour are stated once, with `spec-046` cited where it owns
the mechanism instead of copied. The eleven transport hand-offs Slices 2, 3 and 4 routed
here are all discharged, five closed decisions took a recorded cross-slice correction,
and the `### Error shapes` table gained the two rejection rows Slice 2 withheld so the
rejection contract would be written once. 51 rows graded, 18 stale, **zero code gaps** —
bringing the cycle to 327 rows and one code gap. The spec is a transport contract
again, and it no longer tells a reader anything false about the module it describes.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
