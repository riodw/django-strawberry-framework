# Package build plan: transport_security / 0.0.15 (065)

Spec source: `docs/spec-065-transport_security-0_0_15.md`
Target release: `0.0.15`
Date created: 2026-07-25
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

Pre-flight: passed on 2026-07-25; baseline: dirty with unrelated concurrent work (recorded
below, NOT in scope); cleanup: no prior `build-*.md` / `bld-*.md` artifacts existed (clean
slate), `docs/builder/worker-memory/` + `docs/builder/temp-tests/` empty and seeded,
`docs/shadow/` holds only this build's own `review_inspect.py` output.
`scripts/review_inspect.py` smoke-ran against `django_strawberry_framework/routers.py`.
`scripts/check_spec_glossary.py --spec docs/spec-065-transport_security-0_0_15.md` exits 0
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
- `docs/spec-065-transport_security-0_0_15.md` + `-terms.csv` — this build's input contract
  (authored by the NEXT.md flow). Only Worker 1 may mutate the spec.

### Tracked binary / generated files that a concurrent writer can rewrite mid-build

`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`. A dirty
report on any of these is **not** proof this build caused it, and a same-size binary diff is
**not** proof of a no-op. Diff semantic content (`iterdump()` for the DB, a fresh regenerate
for a rendered doc) before treating churn as revertible. DB-backed slices verify by
**two-consecutive-regenerate byte-stability**, not by a clean `git diff`.

## Build-wide context flags

- **Joint version cut — the bump is NOT ours.** Card `TODO-ALPHA-045-0.0.15` is a non-Done
  card sharing target version `0.0.15`, so per `docs/SPECS/NEXT.md` Step 3 the version
  quintet (`pyproject.toml` `[project].version`, `django_strawberry_framework/__init__.py`
  `__version__`, `tests/base/test_init.py`, and the `CHANGELOG.md` entry) is owned by the
  **last card of the `0.0.15` line to land**. Card 065 is built first, so **no slice in this
  build moves the version quintet and no slice edits `CHANGELOG.md`**
  (spec Decision 15).
- **Known stale prose, NOT this build's to fix:** `spec-045` Decision 7 and `spec-046`
  Decision 11 each assert they are the "only card" at `0.0.15` / `0.0.16`. Cards 065 / 066
  joined those lines, so that justification is now stale — though the *conclusion* (045 owns
  the `0.0.15` cut, as the last to land) remains correct and is exactly what spec-065 defers
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
- `docs/builder/bld-slice-5-docs_foldin.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: S1 — the protocol split (Django owns HTTP) -> `docs/builder/bld-slice-1-protocol_split.md`
- [x] Slice 2: S2 — the cumulative request-body cap -> `docs/builder/bld-slice-2-body_cap.md`
- [x] Slice 3: S9 — one UTF-8 wire contract -> `docs/builder/bld-slice-3-utf8_wire.md`
- [x] Slice 4: S11 — WebSocket actor revalidation through an injection seam -> `docs/builder/bld-slice-4-ws_revalidation.md`
- [x] **Review round 1** (maintainer review of slices 1-4) -> see below
- [ ] Slice 5: S12 transport slice — migration note, deployment guidance, doc fold-in -> `docs/builder/bld-slice-5-docs_foldin.md`
- [ ] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [ ] Final test-run gate -> `docs/builder/bld-final.md`

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
  `docs/spec-065-transport_security-0_0_15.md`. Builders report required wording; they never edit
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
