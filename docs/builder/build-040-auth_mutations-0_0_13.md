# Package build plan: auth_mutations / 0.0.13 (040) — retrospective reconciliation cycle

Spec source: `docs/SPECS/spec-040-auth_mutations-0_0_13.md` (archived; shipped in `0.0.13`)
Rationale companion (to be created): `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`
Terms companion (existing): `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-terms.csv`
Target release: `0.0.13` (shipped; this cycle ships no version change)
Date created: 2026-09-10
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Ownership partition: sequential for Slices 1-4. **Slices 5 and 6 run as two concurrent cohorts
under the partition declared in `## Ownership partition for the Slice 5 / Slice 6 cohorts` below.**
Worker 1 is the sole writer of the spec and the rationale companion.
Hot-path declaration: none by default. A slice that lands a code fix on the per-request auth
resolver path (`django_strawberry_framework/auth/mutations.py` resolver bodies,
`django_strawberry_framework/auth/sessions.py` transport classification) re-declares hot-path in its
own artifact and owes a before/after number.
Floor-verification scope: none by default. A slice that lands a code fix touching the Django
session / auth / Channels seam re-declares its own focused floor scope and names the owning pass.

## What this cycle is

This is **not** a fresh build of `spec-040`. The card shipped in `0.0.13` and the spec is already
archived under `docs/SPECS/`. The maintainer commissioned a **retrospective reconciliation cycle**
with three deliverables:

1. **The rationale extraction that never ran.** `spec-040` is the one archived spec of its
   generation with a `-terms.csv` companion and **no** `-rationale.md`
   (`docs/SPECS/appx/` carries rationale files for `036`, `037`, `038`, `039`, `044`–`048`, but not
   `040`). `docs/builder/BUILD.md` `## Spec rationale extraction` is the contract; Worker 1 performs
   the move per `docs/builder/worker-1.md` `### Performing the rationale move`.
2. **A conformance audit of the shipped code against every normative claim in the spec** —
   the maintainer's stated goal: *make sure the code didn't deviate or drop, or that we did not
   simply forget to implement a feature that was planned*. A contract the spec states and the code
   does not honour is a **code gap** and routes through Worker 2 + Worker 3.
3. **Reconciliation of the spec with what actually landed**, including every correction later work
   made to the auth surface. The spec must read as the **current** contract. Per
   `docs/builder/BUILD.md` `## Spec rationale extraction`, the spec never narrates its own history:
   the *explanation* of every change — what it was before, what changed it, why — lands in the
   rationale companion, never in the spec.

### Scope fence (maintainer-set)

- **In scope:** `docs/SPECS/spec-040-auth_mutations-0_0_13.md`,
  `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md` (new),
  `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-terms.csv` (only if the audit falsifies a row),
  and `.py` source/test files when the audit proves a code gap.
- **Out of scope:** `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `docs/TREE.md` /
  `docs/README.md` / `README.md` / `TODAY.md` / `GOAL.md` / `CHANGELOG.md` / the kanban DB, and the
  closeout agentflow (`docs/builder/BUILD.md` `## Closeout`). No worker edits them, no worker
  reverts them.
- **Fence amendment, maintainer-set 2026-09-11 (Slice 7 only).** The kanban DB
  (`examples/fakeshop/db.sqlite3`) and the two exports it generates (`KANBAN.md`, `KANBAN.html`) are
  moved **in scope** for the sole purpose of homing two deferred-work catalog entries on existing
  `TODO` cards. Everything else in the out-of-scope list stands unchanged — in particular
  `docs/GLOSSARY.md` stays **out** (it is a separate generator and a separate, concurrently-dirty
  file), and the closeout agentflow stays **out**: this amendment adds card rows, it does not close
  a card, bump a version, or touch `CHANGELOG.md`.
- **Every file this cycle creates carries the `040` infix**, including the worker-memory files
  (`docs/builder/worker-memory/worker-<N>-040.md`) and any temp-test directory
  (`docs/builder/temp-tests/040-<slice>/`).

## Pre-flight

Pre-flight: passed on 2026-09-10 with two recorded deviations; baseline: **clean**
(`git status --porcelain` = 0 lines at HEAD `d3b91c8d`); cleanup: see deviations.

| Step | Outcome |
|---|---|
| 1. Working-tree baseline explicit | **Clean.** `git status --porcelain` returned 0 lines. No baseline-dirty out-of-scope files exist; the dirty set recorded in this session's opening context was committed by the concurrent session at `d3b91c8d` before this cycle began. |
| 2. `scripts/review_inspect.py` runs | **Pass.** `uv run python scripts/review_inspect.py django_strawberry_framework/auth/queries.py --output-dir docs/shadow --stdout` emitted a full overview. |
| 3. Build artifacts reset | **Deviation — deliberately skipped.** The on-disk `docs/builder/build-050-list_field_arguments-0_0_15.md` and its `bld-*.md` artifacts are the committed record of the **concurrently active `spec-050` cycle** and are out of scope per `AGENTS.md` rule 34 (never revert or delete another session's work). Every path this cycle creates carries the `040` infix, so no path collision exists; each was verified absent before creation. |
| 4. `.gitignore` lists the scratch paths | **Pass.** `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/` are all ignored. |
| 5. Scratch directories cleared | **Deviation — scoped.** `docs/builder/worker-memory/` was empty and was seeded with four `worker-<N>-040.md` files. `docs/builder/temp-tests/` retains `039-*` directories from an earlier cycle and `docs/shadow/` retains another cycle's overviews; neither was cleared, for the rule-34 reason above. This cycle writes only under `docs/builder/temp-tests/040-*` and overwrites only its own shadow stems. |
| 6. Spec-doc consistency check | **Pass.** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md` → `OK: 30 terms - all have glossary entries and at least one spec link.` |
| 7. Spec rationale extracted | **Deviation — it IS Slice 1 of this cycle**, not a pre-flight gate, because the extraction is the work the maintainer commissioned. The rule's purpose is preserved: Slice 1 runs first and every later spawn reads the post-extraction spec. |

Baseline-dirty out-of-scope files: **none at plan time**; updated mid-cycle — see the Slice 3 log
entry. The tree is worked concurrently, so this list is a snapshot, not an invariant.

## Build-wide context flags

- **The spec is archived.** It lives at `docs/SPECS/spec-040-auth_mutations-0_0_13.md`, not at the
  active `docs/spec-*.md` location every `BUILD.md` path template names. Its companions live in
  `docs/SPECS/appx/` (`AGENTS.md` rule 26), so the rationale file this cycle creates goes to
  `docs/SPECS/appx/`, **not** beside the spec.
- **The active in-flight spec is `spec-050`**, owned by a concurrent session. `docs/` currently
  holds `spec-050-list_field_arguments-0_0_15.md` and its companions; the one-WIP-spec invariant is
  that session's, and this cycle does not touch it.
- **Post-release drift is expected, not exceptional.** `git log --follow` on
  `django_strawberry_framework/auth/mutations.py` shows ~19 commits after `3a294082 Release 0.0.13`,
  several of which changed auth behaviour the spec describes (`c8346750 feat(auth): harden the
  session lifecycle across transports` created `auth/sessions.py`, which the spec never names;
  `44b33e9f fix(auth): enhance logout handling for anonymous requests and session flushing`;
  `a6f5a6cb fix(auth): reject unencodable credentials`; `6873dac6 fix(auth): fail closed on a
  hostile authentication state`; `5e0c53b2`, `c537b2dc`, `48f9f65d`, `31625ac7`, `a8f31a2d`).
  These are the "later corrections" the reconciliation must fold in — the shipped behaviour is the
  contract, the spec is what must move.
- **Decision 11 is the largest known suspect.** It states the Channels fallback is **not** borrowed
  and names `SessionMiddleware` + `AuthenticationMiddleware` as the only supported transport;
  `django_strawberry_framework/auth/sessions.py` and `docs/README.md`'s transport-support table
  describe a materially wider and stricter contract (Channels HTTP scope supported, WebSocket
  `login` rejected before authentication, WebSocket `logout` rejected on the signed-cookie engine).
- **Coverage is the maintainer's gate.** No worker runs `pytest` with any `--cov*` flag in any pass
  (`docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`).
- **Workers never commit.** Only the maintainer commits.

## Rules carried into every dispatch

- **One slice at a time.** Do not start the next slice until the current one's
  plan / build / review / verification / spec-reconciliation cycle is complete.
- **DRY first.** Every plan, implementation, and review answers "is this the maximally DRY shape
  that stays readable?" before anything else. A code fix that duplicates an existing helper is
  rejected in review.
- **The spec is the contract, never a changelog.** Worker 1 rewrites a falsified decision to state
  the corrected contract directly — no amendment block, no "as of round N" hedge. The history goes
  to the rationale companion.
- **Isolation is non-waivable.** If a slice lands a code change, Worker 2 writes it and Worker 3
  reviews it as separate spawns.

## Artifact list

- `docs/builder/bld-040-slice-1-rationale_extraction.md`
- `docs/builder/bld-040-slice-2-audit_substrate_login_logout.md`
- `docs/builder/bld-040-slice-3-audit_register_current_user.md`
- `docs/builder/bld-040-slice-4-audit_obligations_edges_tests.md`
- `docs/builder/bld-040-slice-5-later_spec_reconciliation.md`
- `docs/builder/bld-040-integration.md`
- `docs/builder/bld-040-final.md`
- `docs/builder/bld-040-slice-7-deferral_routing.md` (added post-final under the Slice 7 fence amendment)

Any code-gap cohort spawned out of an audit slice appends to that slice's own artifact (a
`## Build report (Worker 2, pass <N>)` / `## Review (Worker 3, pass <N>)` pair), rather than
creating a new artifact file — the gap belongs to the contract the audit slice owns.

## Checklist

- [x] Slice 1: Spec rationale extraction into `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md` -> `docs/builder/bld-040-slice-1-rationale_extraction.md`
- [x] Slice 2: Conformance audit A — Decisions 1-5, 9 and 10 (module surface, `login` / `logout`, the bind lifecycle, sync/async). **Decision 11 is Slice 5's**, so the transport rewrite happens once, in one place. -> `docs/builder/bld-040-slice-2-audit_substrate_login_logout.md`
- [x] Slice 3: Conformance audit B — Decisions 6-8 and 12 (`register_mutation`, `current_user`, the user-primary-type validation, the version cut) -> `docs/builder/bld-040-slice-3-audit_register_current_user.md`
- [x] Slice 4: Conformance audit C — helper-reuse obligations (D1-D19 / P1-P4 / D-N1-D-N3), `## Edge cases and constraints`, `## Test plan`, `## Definition of done` -> `docs/builder/bld-040-slice-4-audit_obligations_edges_tests.md`
- [x] Slice 5: Later-spec reconciliation — Decision 11 plus every other post-`0.0.13` correction to the auth surface, folded into the spec as current contract, with the history in the rationale companion -> `docs/builder/bld-040-slice-5-later_spec_reconciliation.md`
- [x] Slice 6 (cohort B): Code remediation — the one `CODE-GAP`, four `TEST-GAP`s, and the two stranded-citation findings -> `docs/builder/bld-040-slice-6-code_remediation.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-040-integration.md`
- [x] Final gate -> `docs/builder/bld-040-final.md`
- [x] Slice 7 (post-final, fence-amended): route three `bld-040-final.md` deferred-work entries to their owners — the bug-hunt provenance in `tests/auth/test_sessions.py` fixed in place, and the subprocess-idiom and glossary-auth-entry entries homed as `CardItem` scope rows on `TODO-ALPHA-053-0.0.15` and `TODO-ALPHA-056-0.0.17` -> `docs/builder/bld-040-slice-7-deferral_routing.md`

## Slice log (Worker 0)

### Slice 1 — closed 2026-09-10, `final-accepted`

One Worker-1-only pass; no Worker 2 / Worker 3 dispatch (no source change). Status-line
hygiene checked before the box was ticked: the artifact reads exactly `final-accepted`, and
`git status --short` shows the pass touched only the spec, the new rationale companion, and its
own artifact.

Spec `207,790 B / 2,879 lines` -> `164,391 B / 2,302 lines`; companion
`84,865 B / 1,249 lines`. Cut 47,313 B, reproduced 45,936 B, deleted 1,377 B as falsified (the
revision-history preamble line, 38 chronology attributions whose `Revision-N` / bare `P1`-`P3`
halves decoded against blocks the move removed, and Decision 10's stale `Build note` amendment
block whose contract was already stated two other ways, one of them wrong).

Two contradictions the pass named without acting on them, both already routed:

- `django_strawberry_framework/auth/sessions.py` exists at HEAD and Decision 11 names it
  nowhere while still asserting `SessionMiddleware` + `AuthenticationMiddleware` is the only
  supported transport. **Slice 5 owns it.**
- The `## Slice checklist` blockquote points at `bld-slice-*.md` / `bld-integration.md` /
  `bld-final.md`, all retired when the `0.0.13` cycle closed. **Slice 4 owns it** (it audits the
  checklist and the definition of done).

### Slice 2 — closed 2026-09-11, `final-accepted`

One Worker-1-only pass. Status-line hygiene checked (`final-accepted`, exactly); `git status
--short` shows only writable-list paths. No Worker 2 / Worker 3 dispatch was owed, because the
audit produced **0 `CODE-GAP` rows**.

Spec-slice checklist: **7 of 7 ticked**, each with a symbol-qualified proof — the `0.0.13` build
dropped nothing it planned. Conformance matrix: 63 rows, 52 `CONFORMS`, 11 `SPEC-STALE`,
0 `CODE-GAP`, 0 `UNPROVABLE`. Every divergence runs one direction: the code moved forward after
release and the spec did not. 12 spec edits landed, each with its history appended to the
rationale companion.

Carry-forward Worker 0 is tracking:

- `c8346750` deleted `_resolve_auth_async`, the private helper Decision 10 named as its contract.
  The invariant survived, the sentence did not — the same shape is likely in the `D17` / `P3`
  helper-reuse obligation. **Routed to Slice 4.**
- The finalizer's `loaded_attr` already-loaded-only reach is pinned by **no test**: swap it for a
  plain function-local import and every auth row stays green while Decision 3's opt-in import
  contract is silently void. Not a code gap (the code is right) — a `## Test plan` gap, and the
  one place this cycle could still produce real source work. **Routed to Slice 4**, which owns the
  test plan.
- Six transport findings to Slice 5, two to Slice 3, four to Slice 4. Decision 11 was never read
  or edited this slice, and Decisions 2 / 4 / 5 now point at it rather than restating it, so
  Slice 5's rewrite needs no second pass over them.

Spec `164,391 B` -> `169,338 B` (the reconciliation adds contract the spec never carried);
companion `84,865 B` -> `93,607 B`.

### Slice 3 — closed 2026-09-11, `final-accepted`

One Worker-1-only pass; `Status:` reads exactly `final-accepted`. No Worker 2 / Worker 3 dispatch
owed — **0 `CODE-GAP` rows** again.

Checklist **12 of 12**: the spec's Slice-2 block (`register_mutation` + `current_user`) 5 of 5 with
symbol-qualified proofs, and its Slice-3 block (docs + version cut + card wrap) 6 of 6, audited
read-only at `3a294082 Release 0.0.13`. **Every doc obligation was honoured at the cut** — all five
version-quintet members read `0.0.13` and every `039`-deferred joint-cut flip landed. Conformance
matrix: 91 rows, 83 `CONFORMS`, 8 `SPEC-STALE`, 0 `CODE-GAP`, 0 `UNPROVABLE`. 9 spec edits.

**Decision 6's pipeline was graded step by step at the release tree and every step it specifies is
present**, including the narrowest ones (the four-tuple decode hand-off, the provided-marker
exclusion seam, `set_password` before `full_clean`, the plaintext-never-persisted assertion on both
paths). Nothing was dropped on this half either.

The dispatch told this pass not to inherit Slice 2's prior that every divergence is post-release
drift, and that earned its keep: **two of the eight stale rows were inaccurate on their own date**,
verified identical at the release commit — Decision 6's three-way kwarg-partition claim about the
shared signature helper, and Decision 7's claim that the whole resolve/gate/session/inject
dispatcher is single-sited in one helper. Neither was ever true.

Baseline-dirty update: `docs/feedback.md` is now modified in the tree by the concurrent session.
It is **out of scope — never edited, never reverted** (`AGENTS.md` rule 34).

Three findings the pass recorded without acting on, now Worker 0's to route:

- **F1** — `docs/GLOSSARY.md`'s auth entry repeats a framing this slice's edit 1 falsified and omits
  `is_active` from the refused-auto-expose list. The glossary is DB-backed and **outside this
  cycle's scope fence**; it goes to the maintainer, not to a worker.
- **F2** — five `spec-040 Revision N` citations in `.py` and test files now decode against nothing,
  because Slice 1 moved the revision history into the rationale companion. **This cycle caused
  them**, they are in `.py` files, and `check_citations.py` cannot see them (it is `path::Symbol`
  only). **Code work — routed to the code-fix cohort.**
- **F3** — three `mutations/*.py` docstrings still name `_bind_mutation`, removed by `ab821ae0`
  (`AGENTS.md` rule 27's rename sweep was missed at the time). **Code work — routed to the code-fix
  cohort.**

Handed on: 5 items to Slice 4 (two `## Test plan` gaps, and a re-grade of the `D6`/`D7` and
`D12`/`P1`/`P2` helper-reuse obligations against these edits), 1 to Slice 5 (`current_user` is
transport-neutral and belongs in Decision 11's per-surface table).

### Slice 4 — closed 2026-09-11, `final-accepted`

One Worker-1-only pass; `Status:` reads exactly `final-accepted`. 122 rows: 93 `CONFORMS`,
20 `SPEC-STALE`, 2 `CODE-GAP` rows (one finding), 5 `TEST-GAP` rows (four findings),
2 `UNPROVABLE`. 17 spec edits. All seven inherited items discharged; four transport hand-offs to
Slice 5.

DoD checklist **6 of 7**. Item 6 stays open on purpose: half of it is a coverage claim no worker
may verify (`docs/builder/BUILD.md` forbids every `--cov*` flag) and the other half is falsified by
`CG-1`.

Across the cycle's three audits, **276 graded rows produced exactly one code gap**. The `0.0.13`
build did not drop a planned feature. What it did leave behind is thinner: one missing comment and
four assertions that do not pin what they claim to.

**`CG-1` and `TG-1` were re-verified by Worker 0 against source before dispatch**, per
`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`:
`rg 'D-N1|D-N2|D-N3' django_strawberry_framework/` returns three hits and none is `D-N3`; and
`tests/auth/test_mutations.py::test_registry_clear_does_not_import_the_auth_subsystem`'s docstring
claims it covers the finalizer's bind while its subprocess body only calls `registry.clear()` and
never finalizes. Both hold.

## Ownership partition for the Slice 5 / Slice 6 cohorts

Declared **before dispatch**, per `docs/builder/BUILD.md` `### Parallel cohorts under a declared
ownership partition`. The two cohorts share no file and no shape: one writes English about
transports, the other writes Python comments and test rows. The multi-cohort precondition — a
Worker 1 planning pass that names the shared shapes before builders run — is satisfied twice over:
Slice 4's artifact is the Worker-1-authored fix specification for `CG-1` and `TG-0`..`TG-3`, and
cohort B opens with its own Worker 1 planning pass that folds in the two stranded-citation findings.
**Shared shapes between the cohorts: none.**

| Cohort | Files it may write |
|---|---|
| **A — Slice 5** (Worker 1) | `docs/SPECS/spec-040-auth_mutations-0_0_13.md`; `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`; `docs/builder/bld-040-slice-5-later_spec_reconciliation.md`; `docs/builder/worker-memory/worker-1-040.md` |
| **B — Slice 6** (Workers 1, 2, 3) | `django_strawberry_framework/auth/mutations.py`; `django_strawberry_framework/auth/queries.py`; `django_strawberry_framework/mutations/sets.py`; `django_strawberry_framework/mutations/resolvers.py`; `tests/auth/test_mutations.py`; `tests/auth/test_queries.py`; `examples/fakeshop/test_query/test_auth_api.py`; `docs/builder/bld-040-slice-6-code_remediation.md`; `docs/builder/worker-memory/worker-1-040-codefix.md`, `worker-2-040.md`, `worker-3-040.md`; `docs/builder/temp-tests/040-slice-6/` |

Cohort B's planner writes `worker-1-040-codefix.md` rather than the shared `worker-1-040.md`,
because two Worker 1 spawns appending to one file concurrently lose writes. Cohort B **may not
edit the spec or the rationale companion**: a spec finding it turns up goes into its artifact for
the integration pass, never into cohort A's files.

### Slice 6 declarations

- Hot-path: **none.** The only production edit is one comment; every other change is a test row.
- Floor verification: **none.** No production behaviour changes, so there is no version-dependent
  seam for a floor run to exercise; the added rows are pinned by failability proof instead.
- Failability: the slice introduces no new boundary, so `docs/builder/BUILD.md`'s new-boundary rule
  does not fire. It nevertheless **owes a proof per `TEST-GAP` fix**, because the finding IS that
  the boundary is unpinned: mutate the boundary the new row claims to pin, confirm the row fails,
  revert, prove the revert by byte comparison. A fix whose mutation still fails 0 or 1 rows is
  weakly pinned and is `revision-needed` — it has not closed the gap it was dispatched against.

### Slice 6 planning pass — closed 2026-09-11, `Status: planned`

Cohort B's Worker 1 planning pass re-verified all seven findings at HEAD before planning; none was
moot and no severity moved. **One grew:** `F3`'s population is five mentions across three
docstrings, not three — the same docstrings also name `_bind_form_mutation`, equally removed by
`ab821ae0`. Slice 3's grep had searched one spelling of a two-spelling population, which is the
`START.md` `## Instruments that lie` shape exactly: a vocabulary sample read as a census.

Three corrections the planner made to Slice 4's own fix specifications, each of which would
otherwise have shipped a fix that did not fix anything:

- **`TG-1` as specified was itself weakly pinned** — one subprocess row fails exactly 1 row under
  its mutation, which `docs/builder/BUILD.md` `### Acceptance rule: weakly pinned is
  revision-needed` rejects. The plan parametrizes it into two real consumer entries into phase 2.5
  (bare finalize, and a full `DjangoSchema` build) rather than padding the count.
- **`TG-3`'s query shape would not have worked.** The `groups` M2M surfaces as `groupsConnection`,
  so `{ me { groups { … } } }` is a GraphQL **validation** error, not a strictness raise — a row
  that would have looked like it pinned the contract while pinning a typo. The planner probed both
  surfaces and pinned the verified diagnostic.
- **`TG-0`'s Channels twin already exists** (`tests/auth/test_sessions.py` carries four direct
  `require_session` rows), so Slice 4's conditional resolves to *no*.

**Partition widening, authorized by Worker 0, transient-only.** Two failability mutations must be
applied to files outside cohort B's writable list — `django_strawberry_framework/types/finalizer.py`
(`TG-1`) and `django_strawberry_framework/types/resolvers.py` (`TG-3`) — because that is where the
boundaries under proof live. `docs/builder/BUILD.md` `## Failability proofs` licenses exactly this
and nothing more. Conditions: run them through `scripts/prove_failability.py`, which names any live
mutation in `ACTIVE-MUTATION.json` and refuses the shortcuts; **one mutation live at a time,
reverted before the next**, never across a `Status:` transition; each revert proved by byte
comparison; **net zero change to both files** at the end of the pass, confirmed by
`git diff --stat`. These files are shared with a concurrent session, so a mutation left live would
poison their test run, not just this one.

Also authorized: `docs/builder/temp-tests/040-slice-6/` scratch (already holds the planner's
verified probes and an AST-identity checker for the comment-only findings, which owe the inverse
proof rather than a failability proof).

Baseline-dirty grew again during the pass: `docs/GLOSSARY.md` and `examples/fakeshop/db.sqlite3`
are now modified by the concurrent session. Out of scope, not edited, not reverted.

### Slice 5 — closed 2026-09-11, `final-accepted`

Cohort A, one Worker-1-only pass, run concurrently with cohort B under the declared partition with
no collision. `Status:` reads exactly `final-accepted`.

51 rows: 33 `CONFORMS`, 18 `SPEC-STALE`, 0 `CODE-GAP`, 0 `TEST-GAP`, 0 `UNPROVABLE`. **Cycle total:
327 graded rows, one code gap.**

Decision 11 made nine claims and **eight were false**. It asserted one supported transport, no
pre-flight probe of any kind, and a deliberate non-borrow of the Channels path on the grounds the
code would be dead and untestable. `auth/sessions.py` classifies into three explicit modes,
`require_session` *is* the probe it ruled out, and `channels.auth`'s login / logout are used. **Two
of the false claims were in the heading**, so the heading itself was renamed and all 16 in-page
anchor uses, both reference labels, and the companion's mirrored heading were swept with it — a
rename, not an edit, and it was treated as one.

The rewritten Decision states the prologue's fixed classify -> capability -> session order, a 5x3
per-surface table (`register` and `current_user` get their own column, because transport-neutrality
is a contract nothing in `auth/queries.py` may branch on), and each refusal **with the reason that
makes it a refusal rather than a gap**.

**Five cross-slice corrections into decisions Slices 2-4 had closed**, each recorded explicitly
rather than overwritten silently — including two Decisions that disagreed with each other about a
classification they share (Decision 5's anonymity enumeration missed the adapter shape that
Decision 7's twin sentence had). That disagreement was invisible to every slice that read only one
of them, which is the case for treating the five-homes redundancy as an instrument rather than
noise.

Spec `194,963 B`; companion `130,270 B`.

Open for the integration pass:

- `docs/builder/bld-040-slice-1-rationale_extraction.md` holds one link to the retired Decision 11
  anchor. It is another slice's artifact and per-cycle scratch; the integration pass may repair it.
- Slice 4's two un-edited `WIP-ALPHA-040-0.0.13` sites in the spec: the card is `DONE-040-0.0.13`
  now.
- No per-slice byte delta is asserted anywhere in this cycle's log, because Slices 3 and 4 recorded
  no closing figure to difference against. The figures above are measured, not derived.

### Slice 6 — build / review / final-verification round 1, `revision-needed`

Dispatch chain so far: Worker 1 (plan) -> Worker 2 (build, `built`) -> Worker 3 (review,
`review-accepted`, one Medium escalated) -> Worker 1 (final verification, **`revision-needed`**).
Per `docs/builder/worker-0.md` `## Per-slice dispatch` step 6, that routes to a Worker 2
apply-changes pass and then a Worker 3 re-review.

Worker 3's four independent failability re-runs returned **node-id sets identical** to Worker 2's on
all four boundaries, at the recorded scope, with `types/` left byte-clean. The mechanism worked.

Worker 1 **upheld** the escalated Medium rather than accepting it, on a ground worth recording: the
landed `D-N3` comment is not a compression of the spec sentence, it is **the retired sentence** —
the exact proposition Slice 4 deleted this same cycle because it contradicts the Custom-user-models
edge case, and the comment is contradicted by its own next conjunct one line later. Worker 3's
stated reason for escalating instead of holding (cohort A was still moving that wording) **expired
when Slice 5 closed**, before the verification pass ran.

Worker 1 also **re-graded one Low to Medium** after finding what the review missed: the inaccurate
"can regress independently" claim is not only in the build report, it is in the **shipped test
docstring** — which makes it `CG-1`'s own defect class rather than artifact hygiene. Worker 3 read
the sentence in the artifact and did not follow it into the source.

Both remaining Lows fold into this re-loop rather than the integration pass, because a Worker 2 pass
is now opening the exact file they live in.

### Worker 0 dispatch error, corrected by the worker

The Worker 2 apply-changes dispatch listed the spec's `-rationale.md` companion in that pass's
required reading. `docs/builder/worker-1.md`'s required-reading matrix marks the rationale file
**never** for Worker 2 — that is the entire point of the rationale move
(`docs/builder/BUILD.md` `### Who reads it, and when`). The worker declined the read, cited the
rule, and recorded the refusal in the artifact. It was right and the dispatch was wrong; nothing
was lost, because the replacement text was pinned verbatim and the worker read `D-N3` and the
Custom-user-models edge case at source in the spec itself.

Recorded here because a dispatcher error that a worker silently complies with is invisible
afterwards — `docs/builder/worker-0.md` `### Spawn-prompt contents` exists to prevent exactly this,
and walking the matrix column by column is what would have caught it.

### Slice 6 — closed 2026-09-11, `final-accepted`

Full chain: Worker 1 (plan) -> Worker 2 (build) -> Worker 3 (review) -> Worker 1 (final
verification, `revision-needed`) -> Worker 2 (apply-changes) -> Worker 3 (re-review) -> Worker 1
(final verification pass 2, `final-accepted`). Seven boxes ticked, none over-ticked, nothing
deferred. Isolation held throughout: the agent that wrote each fix never approved it.

The `TG-1` failing set is now stable across **four independent measurements** (builder pass 1,
builder pass 2 after the parametrization changed, reviewer, and the record audit), `types/` left
byte-clean by every one of them.

**The closing pass found one more residual, and its shape is the lesson.** Re-asking the spec
question against the *changed* comment text overturned the previous pass's `None`: the retired
`D-N3` reason clause was still live at its parallel site inside **Decision 6's own body**. Slice 3
had graded Decision 6's normative clause; Slice 4 had graded the reason, but at `D-N3`. Neither
held both halves of one claim at once, and a fix applied at one site with a live parallel site is
`START.md`'s dominant-residual shape exactly. Scoped in Decision 6 with two retraction bullets
appended to the companion.

**Worker 0's dispatch error cost nothing, and that was verified rather than assumed:** Worker 2's
task was applying three verbatim-pinned blocks, all of which landed character-identical, so the
declined read had no output it could have changed — and Worker 3, for whom the companion *is*
permitted reading, performed the `D-N3` content check. Compliance with the erroneous instruction
would itself have been the defect.

**Hazard the integration dispatch must handle:** `docs/builder/BUILD.md`'s integration step 1 names
`docs/builder/bld-slice-*.md`. That glob currently matches the concurrent `spec-050` cycle's five
artifacts and **none** of this cycle's `bld-040-slice-*` files — a literal reading would report a
clean sweep of the wrong cycle. The integration dispatch names this cycle's artifacts explicitly.

### Integration pass — round 1, `revision-needed` (one consolidation loop)

The divergence inventory was the deliverable and it earned the pass. **Twelve contracts live in
more than one of the spec's five homes; five of them disagreed.** The instrument that found them
was sweeping the spec against the companion's twelve `**No longer claims:**` retractions — an
instrument that exists only because Slice 1 built the companion in the first place.

The largest: the retired privilege claim was live at **three further homes** — `## Goals` item 4,
`### Decision 8`, and `## Definition of done` item 4 — none of which any slice's scope covered.
Slice 3 retired it from Decision 6; Slice 6 found it again in Decision 6's body; the integration
pass found the other three. `## Goals` also named four of the five protected columns, omitting
`is_active` — the same defect Slice 3 filed against the glossary as `F1`, sitting in the spec all
along.

**A per-line `rg` reports 2 of those 3 sites.** In `## Goals` the phrase wraps across two source
lines, so only a whitespace-normalized count recovers it — `START.md` `## Instruments that lie`,
demonstrated on this cycle's own evidence rather than in the abstract.

Also settled: `### Decision 10` said `auth/` imports `SyncMisuseError` while the `D18` / `D19`
obligation it cross-references said it does not. Neither sentence is wrong on its own page. Source
settles it — 2 docstring mentions, 0 imports — and the obligation was right.

Ten spec repairs landed, each with a companion entry. `-terms.csv` untouched; no row was falsified.

**Ruling on `tests/auth/_helpers.py`: do not open it.** The `_declare_group_type` duplication is
deliberate, self-documenting in both copies, and outside the cycle's fence for a ten-line saving;
`_helpers.py`'s stated contract is side-effect-free callables, not registry-mutating declarations.
That closes the cross-file item as accepted duplication and collapses the rest to **one loop, one
file**: three file-local duplicates in `tests/auth/test_mutations.py`, all failing the
single-edit-site test, readers grepped, none dead code.

Staged anchors: population **5**, all Markdown prose about the anchor discipline, **zero in source,
tests or comments**. Instrument controlled — the same invocations without the number return 152 and
471, so the 5 is a measurement rather than a broken pattern.

### Integration consolidation — built and reviewed, `review-accepted`

All three consolidations landed in `tests/auth/test_mutations.py` with no other file opened.

**Node ids: 116 before, 116 after, `diff` empty — identical id for id.** Both the builder and the
reviewer hit and documented the same instrument trap: `pytest.ini`'s `addopts` carries `-v`, so a
single `-q` nets to verbosity 0 and prints tree lines containing **no** `::`. The grep writes an
empty file and **two empty files diff clean** — a collect-only comparison structurally incapable of
failing. `-q -q` emits node ids; the 116 line counts are the control. The reviewer reproduced the
trap deliberately (single `-q` -> 0 lines) and then corroborated with a second, AST-derived
instrument.

**No assertion weakened, proved by mutant rather than by reading.** With `require_session` weakened
to a `getattr` default a sessionless request meets Django's raw `AttributeError` — the superseded
path `TG-0` was dispatched to remove. A helper that had kept only the `"session"` substring would
hold under that mutant and show 0 rows. It showed the same 2. The reviewer also named the one link
it could **not** re-derive — Slice 6's second privilege regex has no HEAD version, existing only
between that slice and this pass — and stated the substitute rather than asserting the identity.

DRY-3's ground was verified at source rather than accepted: `_CH_LOGIN` genuinely differs from
`_LOGIN_Q`, `_CH_ME` has no twin, and all three former `_CH_LOGOUT` readers are Channels-path rows
for which `_LOGOUT_Q` is the right document. The merge erased no distinction.

Three Low findings stand for Worker 1's disposition, one of which is a **stated count that is
wrong** — the `_LOGOUT_Q` reader tally is 12->15, not the 11->14 recorded in the ruling and the
build report, because `grep -c` counts lines and not occurrences. That is the exact failure mode
`docs/builder/BUILD.md` `## Claims are proven mechanically` names, caught inside this cycle.

### Worker 0 fence imprecision, corrected by the worker (second instance)

The apply-changes dispatch set the transient-mutation fence as "`git diff --stat --
django_strawberry_framework/` empty at the end". That condition **cannot hold and was never the
right one**: the package directory legitimately carries Slice 6's three comment-only files plus the
concurrent session's production edits. The worker reported the diff plainly, explained why it is
non-empty, and proved the actual invariant the fence exists to enforce — the mutated file restored,
byte-compared and AST-identical to HEAD, with no `ACTIVE-MUTATION.json` surviving — instead of
reporting a clean empty diff it could not honestly claim.

The precise condition, for any later dispatch: **the mutated file** is byte-identical to its
pre-mutation copy, not **the directory** is clean. On a tree three sessions are writing, a
directory-level cleanliness check is unsatisfiable by construction, and a worker that satisfied it
would have had to revert somebody else's work to do so.

Second dispatcher error this cycle, both caught by the worker rather than by Worker 0. Both are
recorded rather than quietly fixed, because a dispatch instruction a worker silently complies with
leaves no trace.

### Integration pass — closed 2026-09-11, `final-accepted`

Two consolidation rounds (Worker 2 -> Worker 3 -> Worker 1, twice). Every finding closed; no spec
or companion repair owed at the close.

**Four unmeasured stated counts surfaced inside this cycle's own artifacts**, and the closing pass
characterized the shape rather than just fixing them: each was a *supporting* tally attached to a
conclusion that holds at any value, so nothing downstream forces it right — which is exactly why it
would have reached the maintainer unchallenged. Every **load-bearing** figure held (node-id sets,
979 citations, 216 tests, 30 terms, 12/12 Decision headings, 16/16 retractions, the five-member
protected set). Each error was caught only by a later pass re-deriving it **with the population
named**, never by reading — so `docs/builder/BUILD.md` `## Claims are proven mechanically` is
correct and is not self-enforcing.

**The fourth one had a consequence and is why this pass mattered.** Worker 3's pass-2 fence
paragraph attributed `django_strawberry_framework/mutations/sets.py` and `mutations/resolvers.py`
to the concurrent `spec-050` session. They are **this cycle's** Slice 6 `F3` docstring fixes, proved
from diff content rather than from which files a session happened to touch (`START.md`: attribute
dirty files by DIFF CONTENT). **Staging from that paragraph would have dropped two landed fixes.**
The corrected staging list is in the artifact.

`L4` (the pinned local name `model` diverging from `user_model` at three sites) was accepted rather
than routed, and the closing pass recorded that the divergence is **the pin's — Worker 1's own** —
not the builder's, so it does not read as a builder defect later. Its condition is recorded: rename
if any later pass opens that file.

Deferred-work catalog final at **12 entries in two blocks** — 7 genuinely deferred, 5 closed items
and corrections recorded so the gate does not re-open them.

### Final gate — closed 2026-09-11, `final-accepted`. Cycle complete; handed to the maintainer.

All seven gate commands recorded. `manage.py check`, `makemigrations --check --dry-run`,
`ruff format --check .`, `ruff check .` and `git diff --check` are clean **repo-wide**, so no
pre-flight baseline exception was claimed.

`uv run pytest --no-cov`: **2 failed, 7675 passed, 40 skipped**. Both failures are the concurrent
`spec-050` session's, and the attribution is mechanical rather than asserted: **neither node id
exists at HEAD** — `git show HEAD:<path>` into an outside-repo scratch gives 0 occurrences of either
test name, the worktree gives 2 — and a row absent at HEAD cannot be a regression of committed code.
Both reproduce alone under `-n0`, so neither is selection pollution. This cycle's own scope: 216 auth
rows, 0 failed, in the same sweep. Escalated to the maintainer, not routed and not repaired; no
`stash` / `checkout` / `restore` / `worktree` ran at any point in the cycle.

Floor verification: `none` **confirmed rather than accepted** — AST identity with docstrings stripped
proves all three package files executable-token identical to HEAD, behind two controls, one of them
the same instrument returning `DIVERGES` on the other session's files. No floor venv was built for a
comment-only diff.

**A fifth unmeasured count, and the first wrong in its SUBJECT rather than its arithmetic:** the
integration artifact's headline "7 files, 391 insertions / 94 deletions" sums only the six non-spec
rows of its own table while still saying "7 files"; the true totals are 1,084 / 970. The per-file
table a stager actually reads was right throughout. This is `START.md`'s "count right in every
digit, wrong in SUBJECT" shape, caught by the last pass that could catch it.

The gate's own catalog work hit the census trap twice more and recovered both times by naming the
population: the subprocess idiom first measured 7 files (`tests/base/test_init.py` builds argv into
a local, invisible to the regex; the bare `sys.executable` token recovers it at 8), and the bug-hunt
provenance sweep first returned 0 because the spelling is `(hunt 0_0_14)`.

**Handover:** 7 tracked files (1,084 / 970) plus the rationale companion, this plan, and the eight
`bld-040-*` artifacts as new tracked material. `mutations/sets.py` and `mutations/resolvers.py` are
**this cycle's** Slice 6 docstring fixes — the corrected attribution is in both the integration and
final artifacts, and a stager working from the superseded paragraph would drop them.

### Slice 7 — closed 2026-09-11, `final-accepted`

Post-final slice opened on the maintainer's fence amendment, which moved the kanban DB and its two
exports in scope for the sole purpose of homing deferred-work entries. Landed: two block-header
comments in `tests/auth/test_sessions.py` (2/2), and two new `Scope` `CardItem` rows — card 53
(`TODO-ALPHA-053-0.0.15`, order 64) for the subprocess idiom, card 56 (`TODO-ALPHA-056-0.0.17`,
order 91) for the `docs/GLOSSARY.md` auth entry. `KANBAN.md` 2/0, `KANBAN.html` 1/1. No spec byte
moved (still 693/876); `docs/GLOSSARY.md` still the concurrent session's 1/1 and
`build_glossary_md.py` never run.

Full round: W1 plan → W2 build → W3 `revision-needed` (1 Medium, 3 Low) → W2 apply-changes →
W3 `review-accepted` → W1 `final-accepted`. Isolation held; W2 and W3 were never the same spawn.

**Three Worker-0 figures were wrong and each was caught by a worker re-deriving with the population
named**, which is the same failure mode this cycle logged five times before Slice 7 opened:

1. The dispatch said the subprocess population was "8 files, 9 call sites". Worker 1 corrected it to
   9 occurrences / 8 files / **8 call sites** — `tests/test_scalars.py:319` is a docstring mention.
   Wrong in its subject, right in its arithmetic.
2. The dispatch's HEAD and baseline-dirty list were stale: the maintainer committed the concurrent
   session's work mid-cycle, moving HEAD `301bf450` → `d3b91c8d`. Worker 1 re-measured and
   diff-attributed the baseline rather than building against the stale list.
3. The card-53 bullet as Worker 1 pinned it said four of the files configure Django (five do —
   `tests/filters/test_sets.py`'s `child` local carries the prologue) and named three inline
   re-spellings (four), which also broke the sentence's arithmetic. Worker 3 found it; Worker 0
   verified it at source before dispatching; Worker 2 fixed it. Root cause, one sentence: that file
   was counted and never read. Recorded as `C3` in the slice artifact.

**A fourth of the same shape, and the one that cost a round:** Worker 1's own plan predicted
`check_citations.py` at 980 / 166; the measured green reading is **981 / 167**, because the card-53
bullet carries two `path::Symbol` citations. Worker 2 measured the real value, reported it loudly,
and did not bend the pinned bytes to fit. Worker 1 kept the tick and corrected the figure, on the
ground that a prediction about a measurement was never a contract a builder could fail.

**Deferred entries 3 and 5 were correctly NOT homed.** Entry 3 (`spec-042 Revision N` ×5) is not
stranded: `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` still carries `Revision 5` ×9, `Revision 7`
×2 and `Revision 8` ×1 with no rationale companion, so all five citations resolve today.
`bld-040-final.md` item 3 misclassifies them as `F2`'s defect class; that artifact is a closed
record and was not edited — the correction lives in the Slice 7 artifact as `C2`. Entry 5 was
already homed on card 56 (`KANBAN.md`'s `Revision N` grading item names the same five lines).

**Handover hazard this slice adds, and it fires only on a split commit:** the card-53 row cites
`tests/auth/test_mutations.py::_auth_free_subprocess`, which has **0** occurrences at HEAD and 3 in
the worktree. `scripts/check_citations.py` is pre-commit hook 6 and runs whole-tree, so a board-only
commit goes red for everyone including the concurrent session. The citation is correct about the
tree this cycle hands over and must not be removed. Safe minimum unit: `KANBAN.md` + `KANBAN.html` +
`examples/fakeshop/db.sqlite3` + `tests/auth/test_mutations.py` in one commit.
