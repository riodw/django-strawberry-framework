# Package build plan: transport_security / 0.0.15 (046)

Spec source: `docs/spec-046-transport_security-0_0_15.md`
Target release: `0.0.15`
Date created: 2026-07-25
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Ownership partition: declared per phase below (`## Ownership partition`).
Hot-path declaration: **open escalation** — see `## Open maintainer decisions`.
Floor-verification scope: **open escalation** — see `## Open maintainer decisions`.

Pre-flight: passed on 2026-07-25; baseline: dirty with unrelated concurrent work (recorded
below, NOT in scope); cleanup: no prior `build-*.md` / `bld-*.md` artifacts existed (clean
slate), `docs/builder/worker-memory/` + `docs/builder/temp-tests/` empty and seeded,
`docs/shadow/` holds only this build's own `review_inspect.py` output.
`scripts/review_inspect.py` smoke-ran against `django_strawberry_framework/routers.py`.
`scripts/check_spec_glossary.py --spec docs/spec-046-transport_security-0_0_15.md` exits 0
(`OK: 37 terms`).

## Baseline-dirty, OUT OF SCOPE — do not edit, do not revert

> **Baseline moved at review round 1.** The maintainer committed slices 1-4 *and* the concurrent
> row-preserving filter work together as `537e4951`, so the original pre-flight list below is now
> historical: those files are committed, not dirty. The review-round-1 baseline is a clean tree
> except `docs/feedback.md` (modified — the maintainer replaced the filter review with the
> transport review; **never touch or revert it**) and the untracked `drys.md` / `vulns.md`
> (maintainer scoping notes; **never touch**). The concurrent-writer hazards on
> `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` still stand
> in full — they remain tracked, generated, and writable by parallel maintainer sessions.

These files were already modified when this build started. They are another dev's / the
maintainer's concurrent in-flight work (the row-preserving-predicates remediation) plus this
program's own card/spec authoring. Per `AGENTS.md` #"Unexpected file modifications" they are
presumptively concurrent work: **never auto-revert, never `git checkout --` them, and do not
edit them unless this build's own slice contract names them.**

- `django_strawberry_framework/filters/sets.py` — row-preserving remediation (concurrent)
- `tests/filters/test_sets.py` — row-preserving remediation (concurrent)
- `docs/row-preserving-predicates-part1-plan.md` — concurrent
- `docs/feedback.md` — the prior review, maintainer-owned (never touch)
- `drys.md`, `vulns.md` (untracked) — maintainer scoping notes (never touch)
- `docs/GLOSSARY.md` — **generated** from the glossary DB; currently carries the concurrent
  row-preserving FilterSet edit. Slice 5 legitimately adds to it, but ONLY via the DB +
  `scripts/build_glossary_md.py` re-render, applied ON TOP of the concurrent state.
- `examples/fakeshop/db.sqlite3` — **concurrent-writable tracked binary.** Carries this
  program's card rows + the concurrent glossary edit. Never reset. Apply writes on top.
- `KANBAN.md` / `KANBAN.html` — **generated exports** of that DB (this program's card
  creation + SpecDoc link are already exported into them).
- `docs/spec-046-transport_security-0_0_15.md` + `-terms.csv` — this build's input contract
  (authored by the NEXT.md flow). Only Worker 1 may mutate the spec.

### Tracked binary / generated files that a concurrent writer can rewrite mid-build

`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`. A dirty
report on any of these is **not** proof this build caused it, and a same-size binary diff is
**not** proof of a no-op. Diff semantic content (`iterdump()` for the DB, a fresh regenerate
for a rendered doc) before treating churn as revertible. DB-backed slices verify by
**two-consecutive-regenerate byte-stability**, not by a clean `git diff`.

## Build-wide context flags

- **Joint version cut — the bump is NOT ours.** Card `TODO-ALPHA-050-0.0.19` is a non-Done
  card sharing target version `0.0.15`, so per `docs/SPECS/NEXT.md` Step 3 the version
  quintet (`pyproject.toml` `[project].version`, `django_strawberry_framework/__init__.py`
  `__version__`, `tests/base/test_init.py`, and the `CHANGELOG.md` entry) is owned by the
  **last card of the `0.0.15` line to land**. Card 046 is built first, so **no slice in this
  build moves the version quintet and no slice edits `CHANGELOG.md`**
  (spec Decision 15).
- **Known stale prose, NOT this build's to fix:** `spec-050` Decision 7 and `spec-051`
  Decision 11 each assert they are the "only card" at `0.0.15` / `0.0.16`. Cards 046 / 047
  joined those lines, so that justification is now stale — though the *conclusion* (045 owns
  the `0.0.15` cut, as the last to land) remains correct and is exactly what spec-046 defers
  to. Surfaced to the maintainer; out of scope here.
- **Breaking change, deliberately.** This build breaks the shipped `0.0.14`
  `DjangoGraphQLProtocolRouter` constructor contract three ways (required
  `django_application`, `url_pattern` -> `websocket_url_pattern`, no Channels HTTP mode).
  The API freeze begins at `1.0.0`; spec Decision 5 authorizes the break. Worker 3's
  public-surface check must measure the diff against **spec Decision 5**, not against
  "no API breakage".
- **Coverage is the maintainer's gate.** No worker runs `--cov`. `--no-cov` is the only
  permitted coverage-shaped flag.
- **Only the maintainer commits.** No worker commits, branches, stashes, or `git add`s.

## One slice at a time

Build only one slice at a time. Do not start the next slice until the current slice's
plan / build / review / verification / spec-reconciliation cycle is complete. After all
in-spec slices are built, run the cross-slice integration pass, then the final test-run gate.

## DRY first

Every plan, implementation, and review answers one question before anything else: is this the
maximally DRY shape that stays readable? Duplicated logic, parallel data flows, near-copies
between modules, and repeated string/key/tuple literals are build-time defects.

## Artifact list

- `docs/builder/bld-slice-1-protocol_split.md`
- `docs/builder/bld-slice-2-body_cap.md`
- `docs/builder/bld-slice-3-utf8_wire.md`
- `docs/builder/bld-slice-4-ws_revalidation.md`
- `docs/builder/bld-review-1-http_boundary.md`
- `docs/builder/bld-review-1-ws_boundary.md`
- `docs/builder/bld-review-1-w3_review.md`
- `docs/builder/bld-review-2-ws_revocation.md`
- `docs/builder/bld-review-2-http_boundary.md`
- `docs/builder/bld-review-2-ws_host_boundary.md`
- `docs/builder/bld-review-2-w3_review.md`
- `docs/builder/bld-review-2-w3_residual.md`
- `docs/builder/bld-slice-5-docs_foldin.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-custodian-3-claim_audit.md` — the concurrent spec-custodian cohort's
  artifact (nine corrections from the out-of-band claim audit). Declared here after the fact:
  W3's integration review found it absent from this list (its B-L2), and the name predates the
  finding, so the list is corrected rather than the file renamed.
- `docs/builder/bld-review-3-integration.md` — W3's adversarial review of the integration +
  custodian cohorts.
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: S1 — the protocol split (Django owns HTTP) -> `docs/builder/bld-slice-1-protocol_split.md`
- [x] Slice 2: S2 — the cumulative request-body cap -> `docs/builder/bld-slice-2-body_cap.md`
- [x] Slice 3: S9 — one UTF-8 wire contract -> `docs/builder/bld-slice-3-utf8_wire.md`
- [x] Slice 4: S11 — WebSocket actor revalidation through an injection seam -> `docs/builder/bld-slice-4-ws_revalidation.md`
- [x] **Review round 1** (maintainer review of slices 1-4) -> see below
- [x] **Review round 2** (maintainer review of the round-1 tree) -> see below
- [x] Round-2 residual review of the M1/M2/M3 remediation -> `docs/builder/bld-review-2-w3_residual.md`
- [x] Slice 5: S12 transport slice — migration note, deployment guidance, doc fold-in -> `docs/builder/bld-slice-5-docs_foldin.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`

## Review round 1 — maintainer adversarial review of slices 1-4

Slices 1-4 were **committed by the maintainer at `537e4951`**, which also swept in the
concurrent row-preserving filter work. The maintainer then replaced `docs/feedback.md` with a
fresh adversarial review of *this* card's transport implementation (S1 / S2 / S9 / S11).
Slice 5 is explicitly **not** judged missing by that review while this plan marks it unbuilt.

The review closes S1's architecture as strong and lists twelve properties as satisfactorily
closed. It does **not** close S2. Findings, all five substantive ones independently confirmed
against the committed source by Worker 0 before dispatch (the numeric one reproduced directly:
`math.isfinite(10**10000)` raises `OverflowError`, so it escapes as a raw exception instead of
the promised `ConfigurationError`):

| # | Severity | Finding | Cohort |
|---|---|---|---|
| 1 | **Blocker** | The counted body cap reaches `len(request.body)`, which materializes the whole spooled body before rejecting it. No seekable-size check exists on the required Django 5.2.0 floor, so an absent/understated `Content-Length` buys an unbounded allocation — and the async view does that read on the event loop. Detection after an unbounded allocation is not a memory bound. | HTTP |
| 2 | High | The permanent strict-UTF-8 wire policy lives inside `_patched_parse_json`, so `APPLY_UPSTREAM_PATCHES=False` (or `{"strawberry": False}`) silently reopens UTF-16/32 acceptance. A security policy must not share a temporary patch's lifecycle. | HTTP |
| 3 | High | `_websocket_application` returns `candidate(schema=schema)` unvalidated, so a factory yielding `None`, a scalar, or a coroutine is mounted as a route callback and fails inside routing instead of raising `ConfigurationError`. | WS |
| 4 | Medium | `consumers.py` imports `.auth.sessions`, which executes `auth/__init__.py` and eagerly pulls in `auth.mutations` + `auth.queries` — importing the whole opt-in auth subsystem on the event loop just to resolve a session-store class. Current tests mask the cold path. | WS |
| 5 | Medium | The revocation acceptance row's "separate request" is direct ORM/session-store mutation, so it never proves a real second HTTP request's session lifecycle invalidates the open socket's cookie/session shape. | WS |
| 6 | Low | A huge int escapes `resolved_revalidation_window` as `OverflowError`, not `ConfigurationError`. | WS |
| 7 | Low | Spec/test prose says an explicit zero revalidation window is a construction error; the implementation accepts an explicit `0.0`. The implementation is judged reasonable — the **spec** must say "positive window" everywhere. | spec |
| 8 | Low | The spec's multi-database claim ("pinned to the operation's own resolved alias") overstates the code, which delegates to Django's routers. | spec |

Cohorts are grouped by **file ownership**, not by severity, so two builders can run in parallel
without colliding: every consumer/revalidation test lives in `tests/test_routers.py`, so findings
3-6 must share one owner.

- `docs/builder/bld-review-1-http_boundary.md` — findings 1 + 2 (`views.py`, the new bounded-read
  compatibility helper, `_strawberry_patches.py`, and their tests)
- `docs/builder/bld-review-1-ws_boundary.md` — findings 3 + 4 + 5 + 6 (`routers.py`,
  `consumers.py`, `auth/sessions.py`, the relocated session-store resolver, `tests/test_routers.py`)
- Findings 7 + 8, plus every amendment the two builders report, are **custodian-only** work on
  `docs/spec-046-transport_security-0_0_15.md`. Builders report required wording; they never edit
  the spec.

Neither builder may touch the other's files. The adversarial review of both cohorts runs in a
separate isolated worker, and must confirm each fix is a real bound rather than a relabelled
detection, and that every new regression can actually fail for the reason it claims.

### W3 adversarial review and residual remediation

`docs/builder/bld-review-1-w3_review.md` closed every dispatched finding and raised six
residuals (W3-1 Medium through W3-6 informational). The HTTP builder remediated W3-1 through
W3-4 and W3-6 in a second pass, recorded at `bld-review-1-http_boundary.md` #"W3 residual
remediation"; W3-5 is note-only and no action was taken.

Two of those fixes changed the card's *contract*, not just its code, and are the ones the
spec now states:

- **W3-1.** `_request_body.py::_measured_remaining` no longer clamps with
  `max(end - position, 0)`. The guard is on the answer, not on one spelling of an incoherent
  pair: a probed count of zero or less returns `None`, i.e. "ask the bounded read instead".
  The clamp was a fail-open — an incoherent `tell()` / `seek()` pair read as "empty body,
  allowed" with no byte read and no package bound left at the Django 5.2.0 floor.
- **W3-2.** `views.py::_RawBodyRequestAdapter`, installed as
  `DjangoGraphQLView.request_adapter_class`, gives the package view its own sync body source.
  Before it, `APPLY_UPSTREAM_PATCHES = False` left the sync package view answering `500` to a
  BOM'd UTF-16 / UTF-32 body, because upstream's adapter decoded inside its own property and
  the view's `parse_json` was never entered. The wire contract's two halves are now both
  view-owned.

Spec reconciliation for this pass is complete and custodian-only: Decision 9 renamed (its
anchor moved, all three cross-references with it) and rewritten around the two view-owned
halves, including a new rejected alternative for the reversed decision; Decision 7 and a new
Edge-case bullet state the zero-or-less probe as a measurement failure; Decision 11 discloses
the accepted astronomical window and its Decision-12 rationale; the Slice 3 checklist, the
Implementation-plan Slice-3 row, test-plan rows 15 and 24, Decision 13's placement paragraph,
and two Definition-of-done items follow. `scripts/check_spec_glossary.py` stays at
`OK: 37 terms`, exit 0. `docs/TREE.md` needs no new row for `_RawBodyRequestAdapter` — the
render is per-module and `views.py` is already on Slice 5's list — but still needs
`_request_body.py` at Slice 5's doc-wrap regenerate.

## Review round 2 — maintainer adversarial review of the round-1 tree

Round 1 was **committed by the maintainer at `511aec8a`**, who then replaced `docs/feedback.md`
again with a second adversarial review of this card. It confirms round 1's findings as
materially fixed and lists seven properties as satisfactorily closed, but does not close the
card: the strongest S11 claim is false for an *already-running* subscription, and the multipart
path sits outside both the strict UTF-8 boundary and the claimed pre-parse declared-size
boundary. Both are architectural gaps rather than test wording.

Slice 5 was mid-flight when this review landed and is explicitly deferred by its own
recommended correction order (step 6: finish Slice 5's prose/integration sweep only after the
behavior is stable). The partial `README.md` / `docs/README.md` edits already on disk are
therefore **unfinished Slice 5 work**, not round-2 work.

All six findings were independently confirmed against source by Worker 0 before dispatch.

| # | Severity | Finding | Cohort |
|---|---|---|---|
| 1 | **Blocker** | `build_revalidating_consumer_class` overrides only `handle_subscribe` / `handle_start`, i.e. operation *admission*. An admitted subscription keeps iterating upstream's `run_operation` / `handle_async_results` loop and keeps emitting results after its session is revoked, so "a revoked session stops executing" is false. `Subscription.tick` yields exactly once, so no existing row can detect it. | WS revocation |
| 2 | High | Multipart `operations` / `map` reach the package as `str` from `request.POST`, after Django's `MultiPartParser` has already `force_str(..., errors="replace")`-decoded them (`multipartparser.py:254`; per-part `charset` is honored only in the FILE branch). Live probes: explicit Latin-1 -> 200, malformed UTF-8 (`0x80`) -> 200. "Request JSON is UTF-8-only" held only for the ordinary JSON body. | HTTP |
| 3 | High | `CsrfViewMiddleware._check_token` reads `request.POST` (`csrf.py:368`) from `process_view` (:414) for every cookie-bearing POST, before the view's `run` reaches `_enforce_request_body_limit` (`views.py:407` / :433). On multipart the declared gate runs *after* Django's parser and upload handlers. The live test uses plain `Client()`, whose CSRF checks are disabled, so it never exposed the ordering. | HTTP |
| 4 | Medium | `AllowedHostsOriginValidator` is a factory for `OriginValidator(settings.ALLOWED_HOSTS)`, and `OriginValidator.__call__` reads only `Origin` — never `Host`. A probe with allowed `Origin` and `Host: evil.example` connected. The router and spec both promise "Host/Origin validation". | WS host |
| 5 | Medium | `routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT` still advertises `strawberry-graphql>=0.262.0` while the dependency and minimum CI node pin `>=0.316.0`; `tests/test_routers.py:91` pins the stale text. Following the error's own advice installs a version the metadata rejects. | WS host |
| 6 | Low | `_measured_remaining` guards `tell()` but calls `seekable()`, both `seek()`s and `end - position` unguarded, so an odd middleware/server stream escapes as an unrelated 500 and a failed restore can leave the position corrupted. | HTTP |

### The four contract decisions

Findings 1-4 each turned on a contract choice, and each was decided by the maintainer rather
than by a worker. Recorded here because the *rejected* options are load-bearing:

- **Finding 1 — connection-scoped revocation through the derived WebSocket adapter.** The seam
  is `GraphQLWSConsumer.websocket_adapter_class`, which upstream instantiates *by name* at
  `strawberry/http/async_base_view.py:310`, and through whose `send_json` both protocols funnel
  every frame. The factory derives one private adapter and installs it on the generated consumer
  exactly as it already installs the two handler classes — a class-level extension seam, not
  per-instance patching. Two checkpoints: the existing admission hooks, plus an adapter gate on
  the information-bearing frames (`next`, `data`, and operation-scoped `error`). On failure:
  mark revoked, suppress the frame, close the socket, cancel, and let upstream's own teardown
  finish. One connection-local lock spans validation, the revoked transition, *and* the send —
  held through the send deliberately, at the cost of per-connection head-of-line blocking on the
  outbound hot path, because that is what makes "no sibling payload escapes after revocation is
  observed" true. `websocket_revalidation_window` keeps its meaning, now spanning both
  checkpoints: the maximum age of a successful validation that may authorize a new operation or
  an information-bearing frame. **Rejected:** a polling monitor at any cadence (not immediate,
  merely a detection interval, and multiplies reads by idle connection count); a send-time guard
  on `handler.send_message` (that funnel also carries connection-control frames, and no
  symmetric payload-only gate exists because transport-ws's payload send lives on `Operation`,
  constructed by name inside `handle_subscribe`); per-operation cancellation without closing;
  and a package maximum-connection-lifetime timer, which would disconnect valid and revoked
  clients indiscriminately and reintroduce the timer machinery the polling design was rejected
  for.
- **Finding 2 — Django-owned parsing with a strict loss-detection guard.** Django keeps sole
  ownership of multipart framing, limits and file streaming. The package adds two conditions
  before `operations` / `map` are parsed as JSON: the effective form encoding must canonicalize
  to UTF-8, and the serialized control values must contain no literal U+FFFD. Since Django
  replacement-decodes every malformed sequence to U+FFFD, that detects exactly the information
  loss that made malformed UTF-8 look valid, while preserving genuine multibyte UTF-8 including
  normal browser `JSON.stringify` output. **Rejected:** ASCII-only control fields (breaks
  `JSON.stringify` for any non-ASCII variable); a raw-preserving pre-decode seam (no narrow
  strict-field hook exists, so it means copying the parser); `receive_data_chunk` (files only);
  and `handle_raw_input` (takes over the whole parse).
- **Finding 3 — view-local CSRF re-entry after the body gate.** Outer `csrf_exempt` on the
  dispatch callback so the global middleware's `process_view` skips it before touching
  `request.POST`; inside the view, the body gate runs first and an over-cap multipart returns
  413 before `request.POST` / `request.FILES` / any upload handler; a passing request then
  enters a package-owned continuation wrapped in Django's public `csrf_protect`. The exemption
  is an *ordering mechanism, not a bypass* — full CSRF still runs, and the endpoint stays
  protected even if a consumer omits the global middleware. **Rejected:** a pre-CSRF package
  middleware plus ordering system check, which adds a required deployment entry and cuts against
  this card's thesis that Django owns the HTTP stack.
- **Finding 4 — a Django-backed WebSocket Host boundary.** One private ASGI middleware projects
  the handshake's host metadata into a minimal `HttpRequest` and calls public
  `request.get_host()`, so Django exclusively owns syntax, ports, IPv6, trailing dots,
  `ALLOWED_HOSTS`, wildcards and DEBUG defaults; only `DisallowedHost` is caught, and the denial
  precedes authentication and consumer construction. Composed outermost:
  `DjangoWebSocketHostValidator(AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(...))))`.
  Host and Origin stay separate checks and neither substitutes for the other. **Rejected:**
  narrowing every claim to Origin-only, which leaves the handshake accepting a hostile Host with
  nothing else owning it, since Django never sees the WS handshake.

### Cohorts

Grouped by **file ownership** again, so workers cannot collide:

- `docs/builder/bld-review-2-ws_revocation.md` — finding 1 (`consumers.py`, `tests/test_routers.py`)
- `docs/builder/bld-review-2-http_boundary.md` — findings 2 + 3 + 6 (`views.py`,
  `_request_body.py`, `tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py`)
- `docs/builder/bld-review-2-ws_host_boundary.md` — findings 4 + 5 (`routers.py`, the new private
  host validator, `tests/test_routers.py`). **Serialized after the revocation cohort**, because
  both own `tests/test_routers.py`.
- Spec work is custodian-only on `docs/spec-046-transport_security-0_0_15.md`, and this round it
  also reconciles the historical `0.262.0` language in the shipped
  `docs/SPECS/spec-041-channels_router-0_0_14.md`.

Process correction carried into every round-2 prompt: builders must write their
`## Required spec amendments` list **into their artifact on disk**, not only into their report to
Worker 0. Round 1's custodian had to re-derive that list because the detail never reached disk.

### W3 adversarial review of round 2, and the custodian pass that followed

`docs/builder/bld-review-2-w3_review.md` returned **revision-needed** with five Medium findings.
M1 / M2 / M3 were remediated in source and tests and committed (`10c50722`); M4 and M5 are process
calibrations escalated to the maintainer and are recorded under `## Open maintainer decisions`.

**A custodian pass ran on 2026-07-28 and closed a real spec/code divergence** that the round-2
amendment pass had left open. It is recorded here because the *code* was already right and only
the contract document was wrong — the failure mode a `Status:` chain does not catch:

- **Decision 17's condition 1 still stated a fallback chain** (`declared charset, else
  request.encoding, else DEFAULT_CHARSET`), which is precisely the reading M1 identified as the
  bypass and which the W3 review's `## Notes for Worker 1` item 1 warned must not land. The spec
  therefore documented the bug as the contract while `views.py::_form_encoding_is_utf8` implemented
  the correct **conjunctive** form. Now stated as three independent requirements, explicitly "not
  rungs of a fallback chain", with the outcome table extended 6 rows -> 10 to cover the
  unusable-declared-codec case and both `DEFAULT_CHARSET` directions.
- **The `"unknown"` / `"0"` host fallback is now named** in Decision 19 and test-plan row 46,
  with the `"unknown:0"` denial verdict it produces (W3 note 3). Code and a behavioral row already
  pinned it; only the spec left it underivable.
- **Five further falsified sentences** were found that no dispatched finding named, one of them
  **inverted**: the edge-case bullet claimed the guard *accepts* a document containing a literal
  `U+FFFD` where Decision 17 refuses it. Also a "two refusal causes" count that is three, a
  "must declare an effective UTF-8 encoding" that requires no declaration, a DoD box carrying the
  same understatement, and test-plan row 39's 5 live shapes against the shipped 9.
- Decision 12's "Why not enforce it" paragraph moved to the rationale companion; the `why not`
  blocks at Decision 7, Decision 11 and Decision 19 were ruled **implementation-relevant and stay**,
  per `worker-1.md` `### Performing the rationale move`'s load-bearing carve-out.

Spec `219,609 -> 224,788` bytes; rationale companion `57,694 -> 63,520`.
`check_spec_glossary.py` holds at `OK: 37 terms`, exit 0. The spec contains **zero** references to
review rounds, passes, or workers — `BUILD.md` `## Spec rationale extraction`'s "the spec never
narrates its own history" verified by grep, not by assertion.

**Worker 0 ruling on the one item the custodian escalated.** The Slice-checklist sub-bullet at
`:203-208` still says the multipart helper "accepts only an effective form encoding that
canonicalizes to UTF-8" — incomplete against requirement 2, but not false, and it is copied
verbatim into the closed Slice 3 artifact's `### Spec slice checklist (verbatim)`. It **stays**:
Slice 3 is built, reviewed and committed, and its artifact is the record of what was built against.
Editing a closed slice's checklist to chase a non-falsified sentence desyncs the evidence for no
correctness gain. Decision 17 now carries the full contract two hundred lines away, and the
checklist points at it.

## Ownership partition

Declared before dispatch, per `worker-0.md` `### Ownership partition`. Each file belongs to exactly
one concurrent cohort; a cohort may read anything.

**Phase R2-close + Slice 5 planning (concurrent, disjoint):**

| Cohort | May write |
|---|---|
| Round-2 residual review (Worker 3) | `docs/builder/bld-review-2-w3_residual.md`, `docs/builder/worker-memory/worker-3.md`, `docs/builder/temp-tests/` |
| Slice 5 planning (Worker 1) | `docs/builder/bld-slice-5-docs_foldin.md`, `docs/builder/worker-memory/worker-1.md` |

Neither cohort writes source, tests, or the spec. The spec is **frozen** for the duration of both
passes: the custodian pass above is complete, and rewriting a contract under a worker reading it is
a recognized defect class in this build. Slice 5's own doc fold-in is a later, serialized phase —
it owns `README.md`, `docs/README.md`, `docs/TREE.md`, the glossary DB and the kanban DB, and it
runs alone because those are generated or concurrent-writable surfaces.

### Three Worker-0 dispatch findings the Slice 5 planning pass refuted

Recorded because the correction matters more than the findings did. Worker 0 pre-verified a set of
facts into the Slice 5 planning prompt to save the planner re-deriving them; **three were wrong**,
and the planner caught all three by re-verifying rather than trusting them. Each has been
re-confirmed by Worker 0 against the tree.

- **`TODAY.md` is NOT concurrent maintainer work — it is this slice's own unfinished work.**
  `git diff -- TODAY.md` is exactly two hunks: the `**Channels ASGI router**` bullet at `:384`
  rewritten to the post-Slice-1 shape (naming `django_application`, `websocket_url_pattern`,
  `r"^graphql/?$"`, `websocket_consumer_class=`), plus one added `[readme-docs]` link definition.
  That is verbatim the "`README.md` / `TODAY.md` transport wording" sub-check. It had been carried
  on the baseline-dirty do-not-touch list since pre-flight, which is where the misclassification
  came from. It is Worker 2's to complete — and the rewritten bullet still describes the
  **two-wrapper** composition, so it is wrong for the same round-2 reason as the two READMEs.
- **`docs/TREE.md` is missing four rows, not two-and-a-half.** `docs/TREE.md:214` / `:324` are
  `auth/sessions.py` inside the `auth/` block, not `utils/sessions.py`; the `utils/` blocks at
  `:280-293` list 13 modules and `sessions.py` is not among them; and `views.py` at `:75` belongs to
  a `graphene_django` comparison tree, not the package. `build_tree_md.py --check` **fails today**,
  which is the slice's own work and not a pre-existing defect to report.
- **Seven net-new glossary terms ARE required; the DB insertion work is not skippable.** Worker 0's
  "seeding is a no-op" finding was true only of the terms CSV's 37 anchors, all of which do exist as
  `GlossaryTerm` rows. The spec's `## Doc updates` separately requires the seven terms *this card
  authors* — the package Django view, the body cap, the UTF-8 wire contract, the consumer-injection
  seam, the revalidation window, the connection-scoped revocation contract, and the WebSocket Host
  boundary — and none of the seven exists in `docs/GLOSSARY.md` today.

**Retrospective candidate for closeout:** a finding stated in a dispatch prompt is a *hypothesis to
re-verify*, exactly like a review's prescribed remediation. `BUILD.md` already says a worker may not
treat a review's prescription as authority; it does not say the same of Worker 0's own pre-verified
findings, and it should. The saving grace here was that pre-verification is offered to save
re-derivation, not to forbid it.

### Round 2 is CLOSED — `bld-review-2-w3_residual.md` reads `final-accepted`

The closing sequence, for the record: Worker 3 residual review (`revision-needed`, new finding M6)
-> Worker 2 apply-changes (`built`) -> Worker 3 pass 2 (`review-accepted`) -> Worker 1 final
verification (`final-accepted`). Suite **5202 passed, 40 skipped**; the +3 over 5199 is exactly M6's
three parametrized rows.

- **M6** — `views.py::_canonicalizes_to_utf8`'s `except (LookupError, TypeError)` had its `TypeError`
  half pinned by **zero** rows. `codecs.lookup` raises `TypeError` for every non-`str` including
  `bytes`, and `HttpRequest.encoding` is publicly settable, so `b"utf-8"` from consumer middleware
  reached it. Direction was fail-**closed** (removal turns the controlled `400` into an unhandled
  `500`), so it was a missing row, not a reopened bypass — closed with three test rows and **no
  production change**, `views.py` proved byte-identical to `HEAD` by sha256.
- **Worker 1's final verification earned its keep**, finding a divergence two prior passes had no
  reason to look for because it was outside the decisions the round amended: **Decision 7 step 3**
  claimed a `MultiPartParser` hand-off for "a multipart request", which is false for any method
  other than POST — `_is_multipart_form_post` is POST-scoped by design, so a stray multipart
  `Content-Type` on a GET takes the **counted** path, and the spec never said GET sits outside the
  multipart carve-out at all. Decision 17 was likewise unscoped. Both now state the method scoping;
  spec 224,788 -> 226,343 bytes, glossary still `OK: 37 terms`.
- **Nine builder amendments were enrichments that had never landed and carried no disposition.**
  Now each has one: A3/A4/A5/A11 declined with reasons, A6/A7/A9 recommended as one short custodian
  pass (three test-plan sentences, no code), A10 folded into M5's substance. Recording the
  disposition is what discharges the obligation — `revision-needed` would have routed to Worker 2,
  which cannot edit the spec.

**Two prose corrections are routed into Slice 5** rather than a spawn of their own, because Slice 5
already owns prose edits in both files: a false claim in the M6 row's docstring in
`tests/test_views.py` ("a row asserting only `is False` would still pass" — measured false, since
removing the arm makes the helper *raise*), and the first Worker 3 pass's open nit on
`views.py::_form_encoding_is_utf8`'s docstring numbering its conditions in the reverse of the code's
evaluation order. **Worker 1's caveat on that routing is load-bearing and Slice 5's dispatch must
carry it:** the Slice 5 plan scopes `views.py` to "the one authorized docstring re-word" and
`tests/test_views.py` to "the docstring first line", so each of these is a *second* edit in its
file — this round's builder correctly declined the `views.py` nit on exactly that ground. Naming
both edits explicitly in the build dispatch is what makes the routing real.

## Slice 5 and the integration pass — closed, and what they routed forward

Slice 5 is `final-accepted` (plan -> build -> review -> final verification, every `Status:` a single
bare legal value). All ten sub-checks landed or were legitimately verify-only; ten of them were
verify-only or partially satisfied on disk before the pass began, six beyond the four Worker 0
pre-verified. `DONE-046-0.0.15` renders in `## Done` and is absent from `## In progress`;
`import_spec_terms --check` moved `OK: 45` -> `OK: 46 done cards`; all four generated docs proved
byte-stable across two consecutive regenerates; `build_tree_md.py --check` now passes, having failed
before the slice. The version quintet is untouched and `pyproject.toml` correctly still reads
`0.0.14` — card 050 is still `todo` at `0.0.15`, so the joint cut owns it (Decision 15).

`bld-integration.md` is `planned` with a nine-box checklist for a Worker 2 consolidation loop.

**Two inherited items were larger than routed, which is the argument for the pass existing:**

- The inline-`post` DRY item was routed as **6** sites; there are **8**. The routed count was measured
  mid-Slice-3 and a fourth async row landed afterwards.
- **M1's routing record carried a false constraint.** It said the two `websocket_revalidation_window`
  sentences following the false clause were "true and must survive". They carry the same drift:
  `routers.py:409` "revalidates every operation" against `consumers.py:81-83` "every admission **and**
  every frame", and `:411` "per authenticated **operation**" against `consumers.py:269` "per
  authenticated **checkpoint**". The fix spans `:404-411`, four corrections rather than one. A routing
  record is a hypothesis too.

### Seven further spec/code divergences, from a corroborating sweep that returned late

A background sweep dispatched by Slice 5's final verification returned **after** that pass closed, so
it contributed nothing to it — correctly recorded as such at the time. Its findings are real. Worker 0
verified the two substantive ones **by execution**, not by reading:

- **Decision 9 `:1300` overstates, and it is that decision's load-bearing ownership sentence.** It
  calls Strawberry's own view "the only mount the gate can still reach". False:
  `_strawberry_patches.py:594` assigns `BaseView.parse_json = _patched_parse_json`, and
  `views.py:590`'s mixin delegates through `super().parse_json(data)` to that exact attribute — so a
  **package** view rides `APPLY_UPSTREAM_PATCHES` for the body-envelope guard. Executed on a real
  `DjangoGraphQLView(schema=None)`: `parse_json(b"42")` and `parse_json(b"[1,2]")` both raise
  `HTTPException 400`, and under `{"strawberry": False}` they return `42` / `[1, 2]`, which upstream's
  unguarded `data.get("query")` at 0.316.0 turns into an unhandled `500` **on the package view**. The
  narrower claim two paragraphs earlier — that the *wire contract* does not ride the kill switch —
  does hold. The same false scoping is mirrored in `_strawberry_patches.py`'s own docstring and in
  `conf.py`'s `UPSTREAM_PATCH_DEPENDENCIES` comment.
- **Decision 6 `:1015` names a kwarg that does not exist.** It lists `subscriptions_enabled` among
  upstream kwargs that "keep working, unchanged". `grep` over the installed strawberry-graphql
  0.316.0: **zero** occurrences. Executed: `hasattr` is `False` on both views, and
  `DjangoGraphQLView.as_view(schema=None, subscriptions_enabled=True)` raises `TypeError`, while the
  other three are `True`. `views.py`'s own docstring gets this right and lists only the three.

The remaining five are over- or under-statements, all with cited source lines, none behavioral: the
DoD's `limit + 1` allocation bound stated without the already-documented `request._body` carve-out;
the Edge-cases description of the cap branching on `content_type` alone when
`_is_multipart_form_post` is method-**and**-content-type (the same family as L3, different line and
subject); the probe's guarded surface enumerated as four calls where the code guards five, with the
word "Every" making it a factual error rather than shorthand; the cap's own per-request
`ConfigurationError` — the card's only one that surfaces as a `500` rather than a construction
failure, and which rejects `0` rather than reading it as "unlimited" — absent from `### Error shapes`;
and the `DEBUG=True` / empty-`ALLOWED_HOSTS` accepted set given as `localhost` / `127.0.0.1` only,
where Django's `[".localhost", "127.0.0.1", "[::1]"]` accepts every `*.localhost` subdomain and
`[::1]` (a reader designing a hostile-`Host` row from that sentence would pick a host that is
actually accepted).

**Routing.** The source-side halves (`_strawberry_patches.py`'s docstring) join the integration
cohort, which already owns the same defect class — a contract told in several places where one telling
drifted. `conf.py`'s comment is the maintainer's concurrent dirty file: **never edited, never
reverted**, routed as a maintainer item. The seven spec-side corrections are a **custodian pass after
the consolidation**, so the spec reconciles to the settled tellings rather than to a moving target.

**Ownership declaration for the consolidation cohort**, per `worker-0.md` `### Ownership partition`:
`docs/README.md` is declared **into** the cohort. It was closed as Slice 5's, and Slice 5's own final
verification routed one of its lines here; without the declaration the builder would have no
authority over a file its checklist names.

### Six further spec divergences from an out-of-band adversarial claim audit

An independent auditor (not a build worker, no stake in the spec passing) was dispatched **outside**
the `Status:` chain to verify every falsifiable claim in the spec against source, against installed
strawberry `0.316.0` / Django / channels, and against the `strawberry_django` and `graphene_django`
reference checkouts. Two rounds. Worker 0 re-verified **all six** findings independently, by execution
where execution settles it, before recording any of them here. One site the auditor missed is folded
into F3; one severity assessment is overridden with the reason stated.

The audit's own negative results are recorded too, because a verified-clean decision is a build asset:
**Decision 7** (the counted body cap) and **Decision 18** (CSRF re-entry ordering) both came back clean
under executable probes, including the counterfactual for 18 (a non-exempt callback, proving Django's
multipart parser really does run pre-view) and a lying / garbage `Content-Length` matrix for 7.

- **F6 (high) — `## Edge cases` `:2354-2373` and test-plan row 15 `:2548-2552` state the *superseded*
  behavior for an over-reported stream position.** Both say the incoherent pair "in either direction"
  is refused a measurement and falls to the bounded read, and that the over-reporting direction hands
  Strawberry an **empty** body for a `400` at the parse. The built contract refuses that shape as
  `_Probe.CORRUPTED` — `_request_body.py:333-336` verifies the restore **before** the subtraction ever
  runs, so the bullet's "probed difference zero or negative" is unreachable for it — and
  `body_exceeds_limit:229-231` answers the package's own `413` plus an operator WARNING with **nothing
  read**. Worker-0 verification: a purpose-built over-reporting-`tell()` stand-in returns
  `_Probe.CORRUPTED` with `reads performed by probe: []`. `tests/test_views.py:1077-1116` asserts
  exactly that (`413`, `requested == []`, `delivered == 0`, the log record) and its own docstring names
  the Edge bullet's behavior as "what the two-state version did". Only the under-reported-end direction
  behaves as the spec's sentences describe. Row 15's third-outcome list also narrows the refused set to
  a restoring seek that *raises*, excluding the verified-failed restore `_position_restored:373-377`
  refuses identically. **This is the inversion class the round-2 custodian pass already hit once**: an
  edge bullet elaborating a decision it contradicts.
- **F1 (medium) — Decision 16 `:1869-1871` and DRY `:2222-2224` name the wrong owner for the revocation
  state, and it holds none of it.** Both say the lock, the revoked flag and the last-validated timestamp
  are "one set of state on the **adapter** instance". `consumers.py:656-657` puts the lock and the flag
  on the **consumer** (`GraphQLWebSocketConsumer.__init__`; its own docstring at `:610-614` says
  "per-INSTANCE"), and the timestamp is on the **scope** (`_REVALIDATED_AT_SCOPE_KEY`, `:214, 453, 485`).
  Every read reaches them through `consumer.`; nothing is on the adapter. The soundness argument
  survives — the parenthetical's reason ("upstream constructs exactly one per connection") is equally
  true of the consumer — so this is a description defect, not a hole.
- **F3 (low) — "two-line delegate" is wrong at three sites and contradicts the spec's own DRY bullet.**
  `:207`, `:1974` and `:1421` all say two-line; `:2233-2234` says "the sync one two statements, the
  async one three", which matches `views.py:879-888`. `:1421`'s "two two-line subclasses" is the third
  site, found by Worker 0 and missed by the audit: `consumers.py:561-579` shows each admission override
  body is three lines. The rationale's change record at `-rationale.md:124-126` **claims this wording
  was already corrected for both colours**. It was not — which is precisely how F3 came to exist, and
  the reason this correction must land at all three sites in one edit.
- **F5 (low, severity raised by Worker 0) — `AllowedHostsOriginValidator` is not "only a factory for
  `OriginValidator(settings.ALLOWED_HOSTS)`"** (`:420-421`, `:2154-2156`). channels `4.3.2` substitutes
  `["localhost", "127.0.0.1", "[::1]"]` under `DEBUG` with an empty list. Raised above the auditor's
  "low" because the substituted list **differs from Django's** (`"localhost"` vs `".localhost"`, so no
  subdomain match) — a divergence that is *evidence for* Decision 19's premise. Flattening the
  validator to a factory discards a fact that argues for the boundary this card adds. The operative
  claim (Origin-only, never Host) is confirmed **true**.
- **F4 (low) — `:2415-2416` says `DEBUG` + empty `ALLOWED_HOSTS` accepts "`localhost` / `127.0.0.1`
  only".** Django substitutes `[".localhost", "127.0.0.1", "[::1]"]` (`http/request.py::get_host`,
  identical on 5.2 and 6.0): leading dot ⇒ every `*.localhost` subdomain, plus IPv6 loopback. The
  bullet's own remediation (set `ALLOWED_HOSTS` explicitly with `override_settings`) is unaffected.
- **F2 (low) — `:653-655` says the upstream views' imports are "`django`, `cross_web`, and `strawberry`
  only, verified in the installed 0.316.0".** `strawberry/django/views.py:10` imports
  `asgiref.sync.markcoroutinefunction` at module level, and the list also omits the standard library.
  The package's own `views.py:58-62` docstring gets this **right**, so the spec contradicts the code it
  describes. The conclusion (no optional-import guard) survives: `asgiref` is Django's own hard dep.
- **F7 (low, Worker 0's own, promoted from the audit's sub-threshold note) — the `APPEND_SLASH` bullet
  `:2300-2304` is unqualified where Django's behavior is not.** It states flatly that "a `POST` to
  `/graphql` also gets a `301`". Under `DEBUG=True` Django raises `RuntimeError` instead
  (`middleware/common.py::get_full_path_with_slash`). The auditor left this sub-threshold as deployment
  guidance; overridden because the reader most likely to *test* the claim is running `DEBUG=True`, would
  get a `500`, and would conclude the spec is wrong. One qualifying clause closes it.

**F8 (medium) — Worker 0's own, found while applying the fixes: Decision 6 carried a *sixth* site of
the hook-count defect, and got the placement wrong too.** `### Decision 6` read "That subject is two
questions and **two overridden hooks, both on one shared private mixin**". There are **four**
(`views.py`: `as_view` and `parse_json` on `_RequestBodyBoundaryMixin`; `run` and `parse_multipart`
declared per concrete view), and the two hooks belonging to the two questions the sentence names split
across the boundary it denies — Decision 9's `parse_json` is on the mixin, Decision 7's `run` is not.
So "both on one shared private mixin" was false for one of the two it named. This is the strongest
evidence yet for the F3 lesson: **a count stated in prose replicates, and a correction that fixes the
authoritative telling without sweeping for siblings leaves the falsity alive elsewhere.** The DRY
section had already been corrected to "Four overridden hooks"; Decision 6 was never swept.

**Routing — superseded by the maintainer.** These were recorded as belonging to a custodian pass
**after** the consolidation, so the spec would reconcile to settled tellings. The maintainer directed
both to run **now**, so they run **concurrently** under a declared ownership partition instead:

| Cohort | Owns (writes) | Never writes |
|---|---|---|
| **Worker 1** — spec custodian, nine corrections | the spec, the `-rationale.md`, `bld-custodian-3-claim_audit.md` | all production code, all tests, `docs/README.md`, the DB |
| **Worker 2** — integration consolidation, nine boxes | `routers.py`, `_strawberry_patches.py`, `views.py`, `exceptions.py`, `test_transport_api.py`, `docs/README.md`, the glossary DB rows + regenerated `GLOSSARY.md`, `bld-integration.md` | the spec, the rationale, `conf.py`, `tests/test_views.py` |

The partition is what makes concurrency safe here, because **every spec correction lives in one file** and
`BUILD.md` names *rewriting a contract under a worker reading it* as a recognized defect class. Two
consequences were pushed into the dispatches rather than left to discovery: Worker 1 is told to verify
facts by **anchor string or execution, never by line number**, since Worker 2's edits shift lines in the
very files it reads for evidence; and each is told the other exists, so a wrong sentence found outside
its own cohort is **recorded for the other worker** rather than fixed across the boundary.

Two corrections were applied directly by Worker 0 before dispatch and are excluded from Worker 1's
list: Decision 6's phantom `subscriptions_enabled` kwarg, and F8 above.

F6 remains the one to verify first — a test written from row 15's words fails against the built code.
Worker 2 was also given two **corrections to its own routing record**, because the record understated
the work: the inline-`post` DRY item is **eight** sites rather than six, and M1's record asserts two
neighbouring `routers.py` sentences are "true and must survive" when they carry the same drift, making
it four sentences rather than one. Both were passed as *hypotheses to re-verify*, with the count it
actually finds requested back — per `### Three Worker-0 dispatch findings the Slice 5 planning pass
refuted`, a finding stated in a dispatch prompt is not evidence.
Two audit items stay **open and are not findings**: the Uvicorn and Hypercorn thirds of Decision 8's
"no mainstream ASGI server bounds the total body" (absent from the venv; installing is barred, and the
error direction is safe — if either *did* cap, the spec would be understating protection). Daphne's
third is **closed as true** by Worker 0: `daphne/http_protocol.py:200-210` uses `request_buffer_size`
purely to chunk reads into `more_body` fragments, with no total accumulation bound.

**Process note for the closeout.** This audit ran entirely outside the `Status:` chain and found a
high-severity inversion in a spec that had already passed two review rounds, a custodian pass, and a
Slice 5 final verification. That is the third independent confirmation of `worker-0.md`'s standing
pattern — *a green `Status:` chain does not prove the spec matches the code* — and the first evidence
that an auditor with **no stake in the artifact passing** finds a class of defect the in-flow reviewers
did not. Worth a `BUILD.md` consideration: an out-of-flow claim audit before the final gate.

### W3 adversarial review of the integration + custodian cohorts -> `bld-review-3-integration.md`

Both cohorts' substance verified correct end to end — by execution where execution settles it,
including AST identity (docstrings normalised) of all four production files against `git show
HEAD:`, proving zero executable production change. Both verdicts were nonetheless
`revision-needed`, each resting only on Low findings the acceptance gate cannot wave through:

- **A-L1** (W2 artifact) — "Net -49 lines" for `test_transport_api.py`; measured `-21`
  (39 insertions, 60 deletions).
- **A-L2** (W2 source) — the landed L-A comment in `exceptions.py` self-contradicts within six
  lines ("the spelling its two siblings use" vs "Three spellings of one placeholder"); measured
  three sites, **two** spellings. Inherited from finding L-A's own wording; W2 had in fact landed
  the *correct* site (`_safe_arg_repr`) where the plan mis-attributed `_safe_type_name`.
- **B-L1** (W1 artifact) — not-fixed item 1's "each in its own `try`": six guarded calls,
  **five** `try` blocks (`_position_restored` guards two in one).
- **B-L2** (Worker 0's, closed above) — the custodian artifact was absent from `## Artifact list`.

Two Worker-0 flags were **refuted** and are withdrawn: W1's "zero chronology phrases" claim is
phrase-specific and grep-true (the single hit is `pytest-xdist` in a test-plan row), and
not-fixed item 7's two phrases legitimately describe shipped 0.0.14 behavior — W3 recommends W1
close item 7 as no-change. The partition held; `conf.py:117` remains genuinely open as the
maintainer's; `bld-slice-4-ws_revalidation.md:9`'s `Status: planned` lapse was left alone as
recorded. W3 flagged for the final verification: W2's tenth box (`### Item C`) sits in its build
report rather than the dispatched checklist and should be audited as a tenth tick.

Remediation was dispatched as two concurrent single-finding fixes (disjoint files: W2 owns
`bld-integration.md` + `exceptions.py`; W1 owns its own artifact only).

## Open maintainer decisions (do not let a worker re-litigate these)

Both were escalated by `bld-review-2-w3_review.md` as **process calibrations, not review findings**,
and neither blocks Slice 5. Workers are told they are pending so they do not re-raise them.

- **M5 — the plan carries no hot-path declaration, and the round owes a number.** The WS-revocation
  design holds one connection-local lock **through** the outbound send, which meets `BUILD.md`
  `## Hot-path budget`'s definition ("per outbound message", "per connection"), and the spec itself
  calls it a hot path. Options: (a) declare the slice hot-path and re-loop the cohort for a
  before/after number — `_instrument_revalidation`'s `probe.reads` is already the instrument, so it
  is cheap; or (b) an explicit maintainer waiver naming the number as not required for this card.
- **M4 — whether the weakly-pinned rule is applied literally.** Twelve boundaries in round 2 fail
  the 0-1-row test. The reviewer's own merit ruling: M2 and M3 were genuine gaps (both since
  remediated), four more deserve a second row on merit, and the remaining six are adequate on merit
  and fail only the rule as written. Applying it literally re-loops all twelve. Related: the rule
  says "never a recorded exception" while `bld-review-2-w3_review.md` Q7 records one
  ("weakly pinned but adequate"), so the rule needs either a narrow carve-out or that entry
  becomes `revision-needed`.
- **`AGENTS.md:15` vs. scoped `ruff`.** All four role files now tell workers to scope `ruff format`
  / `ruff check --fix` to their own files, because this tree carries concurrent uncommitted work and
  a repo-wide write-mode run reformats it. `AGENTS.md:15` mandates the repo-wide form and the role
  files defer to `AGENTS.md` on conflict, so **the scoping instruction is inert until this is
  reconciled.** Recorded in commit `84c6075b`'s message as well.

### Artifact `Status:` hygiene lapse in round 2 — recorded, not silently repaired

`worker-0.md` `## Slice status legend` requires exactly one of five legal values, and Worker 0 may
never write the field itself. Round 2 shipped with **four** violations, all of which reached the
maintainer's commit (this section said three until Worker 1's final verification found the fourth —
the count was itself an instance of the record reading cleaner than the run):

- `bld-review-2-ws_revocation.md` — **no `Status:` line at all**
- `bld-review-2-ws_host_boundary.md` — **no `Status:` line at all**
- `bld-review-2-http_boundary.md` — `Status: built (pass 2), dirty, uncommitted.`, the exact
  illegal shape `worker-0.md` names as an example off which no dispatch decision can be read
- `bld-review-2-w3_review.md:8` — a legal value with commentary appended
  (`Status: **revision-needed** — five Medium findings …`), which the legend forbids as explicitly
  as it forbids two values or a paraphrase

The dispatch chain was therefore driven off worker reports rather than off the artifacts, which is
the courier failure the artifact contract exists to prevent. Not retro-fixed: Worker 0 writing those
lines now would be writing `Status:`, and the passes that owed them are closed and committed. The
round is instead closed forward, through the residual review and Worker 1's final verification,
which sets `final-accepted` on its own artifact legitimately.
