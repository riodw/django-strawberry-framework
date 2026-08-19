# Package build plan: django_trac_37064_hardening / 0.0.7 (024)

Spec source: `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` (already archived; this cycle rewrites it in place)
Rationale companion (to be authored): `docs/SPECS/appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md`
Target release: `0.0.7` (shipped; card `DONE-024-0.0.7`)
Date created: 2026-08-18
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

## Cycle type and scope

This is a **residual reconciliation cycle** over already-shipped work, not a feature build. Same
shape as the spec-020/021/022/023 residual cycles. Three deliverables and nothing else:

1. **Prove the code did not deviate, drop, or forget a feature** from the contract that was planned
   for card `DONE-024-0.0.7`.
2. **Rewrite the spec** so it states the contract that actually exists at HEAD — including every
   later correction and every change made to serve later work. The spec is a *contract*, never a
   changelog: it never narrates its own history (`docs/builder/BUILD.md` `## Spec rationale
   extraction`).
3. **Author the rationale companion**, which is where every explanation, rejected alternative,
   change record, and no-longer-true claim lives.

**Maintainer scope restriction for this cycle (overrides the default doc-update surface):** spec
files and `.py` source only. No closeout / agentflow edits — no `KANBAN.md`, `KANBAN.html`,
`docs/GLOSSARY.md`, `CHANGELOG.md`, `docs/TREE.md`, `docs/README.md`, no `examples/fakeshop/db.sqlite3`
ORM writes, no card wrap. Anything those surfaces owe is recorded in the deferred-work catalog
instead of being fixed here.

**Artifact naming:** every path this cycle creates carries the issue number `024`.

## The input contract (recovered, not invented)

The archived spec is a 1,618-byte card-snapshot **stub** — it carries a card snapshot, a one-word
planning note, and two `## Other` bullets. It has no slice checklist, no decisions, no test plan, no
DoD. Its own preamble says so and instructs a later author to expand it.

The real input contract survives in two deleted planning documents, recovered read-only from git and
staged in this session's scratchpad:

- `docs/PLAN-trac-37064-database-teardown.md` — deleted at `d1d19ca2`; recovered from `d1d19ca2^`.
  Carries the Context, the fix description, **5 named implementation decisions**, 4 risks/open
  questions, a **9-item Definition of done**, an Out-of-scope list, and a Phase-4 update adding the
  consumer-facing helper.
- `docs/TEMP-trac-37064-test-plan.md` — deleted at `d1d19ca2`; recovered from `d1d19ca2^`. Carries
  the sources checked, the test-placement decision, the **required-test list**, the mixed-strategy
  argument, and the verification commands.

Both are read-only inputs. Neither is restored to the tree.

## Pre-flight

Pre-flight: passed on 2026-08-18 with two recorded deviations (below); baseline: **dirty with a
concurrent cycle's uncommitted work** (see baseline-dirty list); cleanup: shadow + temp-tests
cleared, `worker-memory/worker-{0,1,2,3}-024.md` seeded empty.

| Step | Outcome |
|---|---|
| 1. Working-tree baseline explicit | Done — see baseline-dirty list. Not escalated: the maintainer's instruction for this cycle is "ignore others concurrent work". |
| 2. `scripts/review_inspect.py` runs | Passed — `uv run python scripts/review_inspect.py django_strawberry_framework/_django_patches.py --output-dir docs/shadow` exits 0. |
| 3. Build artifacts reset | **Deviation (deliberate).** The spec-023 residual cycle's `bld-*-023.md` / `build-023-*.md` artifacts are present and **uncommitted**. Deleting them is the one irreversible pre-flight mistake (`worker-0.md` `## Pre-flight procedure` step 3) and would clobber concurrent work protected by `AGENTS.md` rule 34. They are left in place and listed as baseline-dirty. Every path this cycle creates was collision-checked and is free. |
| 4. `.gitignore` lists scratch paths | Passed — `docs/builder/worker-memory/`, `docs/shadow/`, `docs/builder/temp-tests/` all listed. |
| 5. Scratch directories cleared | Done. |
| 6. Spec-doc consistency check | Passed — `check_spec_glossary.py --spec docs/SPECS/spec-024-…md` reports `OK: 2 terms`. |
| 7. Spec rationale extracted | **Not applicable as written.** A stub spec has no deliberative layer to MOVE. The rationale companion is therefore an **authoring deliverable of Slice 2**, reconstructed from the recovered planning documents and the commit history, not a pre-flight cut-and-paste. Recorded here so the omission is deliberate and visible rather than skipped. |

### Baseline-dirty, out-of-scope (never edit, never revert)

`CHANGELOG.md`, `KANBAN.html`, `KANBAN.md`, `docs/GLOSSARY.md`, `docs/feedback.md`,
`examples/fakeshop/db.sqlite3`, `docs/SPECS/spec-021-apps-0_0_7.md`,
`docs/SPECS/spec-022-export_schema-0_0_7.md`, `docs/SPECS/spec-023-multi_db-0_0_7.md`,
`docs/SPECS/appx/spec-021-apps-0_0_7-terms.csv`, `docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv`,
`docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md`,
`docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md`, every `docs/builder/*-023*.md`, every
`docs/builder/DONE/build-02*.md`, and the four staged deletions under `docs/builder/`.

### Tracked binary / generated files that a concurrent writer can rewrite

`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`. This cycle writes
none of them. Churn on any of them during this cycle is a concurrent writer's and is left alone.

## Declarations

- **Ownership partition:** Slice 1 runs as **two concurrent read-only audit cohorts** under a
  disjoint partition; Slice 2 is sequential after both and consumes their measured findings.
  Per-cohort writable sets are named in each dispatch and repeated here:
  - Slice 1a — writes `docs/builder/bld-slice-1a-024-planned_vs_head.md` only. Read-only on all
    source. Question: did anything planned get skipped, dropped, or silently changed?
  - Slice 1b — writes `docs/builder/bld-slice-1b-024-divergence_and_floor.md` only. Read-only on all
    source. Question: what changed after the ship, why, and which changes flipped a contract? Also
    owns the floor run.
  - The two cohorts share `docs/builder/worker-memory/worker-2-024.md`, which is **append-only and
    gitignored** — not a production file, so it does not serialize them. No other file is written by
    both. Neither reads the other's artifact, so the two verdicts are independent by construction.
  - Slice 2 — writes `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md`,
    `docs/SPECS/appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md`, and
    `docs/builder/bld-slice-2-024-spec_reconciliation.md`.
  - A code-repair cohort is dispatched **only if** Slice 1 finds a genuine gap between the planned
    contract and HEAD. Its writable set is declared at that point and its files are removed from
    Slice 2's set.
- **Hot-path declaration:** none. The subject is an app-load-time monkey-patch and a test-time wrap
  helper; neither runs per request, per resolver, per row, or per outbound message.
- **Floor-verification scope:** **Slice 1b owns one focused floor run.** The subject is a Django
  integration seam (a private `django.test.testcases` symbol, its classmethod descriptor, and the
  exact source text of its body), and the patch's audited-body set claims to span Django
  `5.2.16`–`6.1`. The floor is Django **5.2.16** on Python **3.10** with strawberry-graphql
  **0.316.0** (`docs/builder/BUILD.md` `## Floor verification`, the single canonical statement).
  Focused scope: `tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py`.
  A body pin that only ever executes against the shared `.venv`'s Django is a pin whose floor claim
  was never run.

## Artifact list

- `docs/builder/bld-slice-1a-024-planned_vs_head.md`
- `docs/builder/bld-slice-1b-024-divergence_and_floor.md`
- `docs/builder/bld-slice-2-024-spec_reconciliation.md`
- `docs/builder/bld-slice-3-024-rename_rot_sweep.md`
- `docs/builder/bld-slice-4-024-docstring_fragment.md`
- `docs/builder/bld-integration-024.md`
- `docs/builder/bld-final-024.md`

## Slice 1 outcome (both cohorts returned `built`)

**No code gap.** Two independent cohorts, working from disjoint angles and neither reading the
other's artifact, both concluded that nothing planned for `DONE-024-0.0.7` is missing from HEAD
without deliberate retirement. What the audits found is that the **spec** is wrong, not the code:
a reversed decision, contract flips with tests pinning each new state, and two stale citations.

Slice 3 is opened on the strength of exactly one in-scope `.py` defect, verified by Worker 0 before
dispatch rather than taken on the cohort's word (`docs/builder/BUILD.md` `### Worker 0 verifies every
finding against source before dispatching`): `django_strawberry_framework/_strawberry_patches.py`
cites `_django_patches._UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE`, renamed away at `eb2a1764` — 1
occurrence repo-wide outside `docs/builder/`, 0 in the target module. `AGENTS.md`'s rename-sweep rule
makes the repair card 024's own, since 024's rename is what broke it.

Not opened as repairs, and why:

- `safe_wrap_connection_method` not following `apply()` into fail-loud on a missing private
  `_DatabaseFailure` is **deliberate and pinned by a test** — the helper degrades rather than making
  the public `django_strawberry_framework.testing` import crash. It is a contract the rewritten spec
  must state, not a defect.
- The `CHANGELOG.md` `0.0.7` entry's false "no settings key" / "log-once sentinel" claims, the stale
  `docs/GLOSSARY.md` Trac #37064 entry, and `docs/TREE.md`'s two module summary lines are all real
  and all **outside this cycle's maintainer-set scope** (spec files and `.py` only). They go to the
  deferred-work catalog in `bld-final-024.md`.

## Slice 1 review outcome (both artifacts `revision-needed`, one apply-changes pass dispatched)

The independent Worker 3 pass **reproduced both load-bearing verdicts** — no code gap, and the floor
pass including the discriminator table, re-derived with its own probe — and rejected both artifacts
on the **change record**, which is the part Slice 2 copies into a permanent archived document.

The central finding is one this repo has hit before (`AGENTS.md` rule 34's world: the maintainer runs
concurrent sessions and main's history is rewritten under a running cycle). Two commit hashes cited
8 times across artifact 1a — `8e86e777` and `e69ff4f9` — **exist in the object store but are not
ancestors of HEAD**. Worker 0 verified before dispatching the fix: `git merge-base --is-ancestor`
fails for both and passes for their reachable equivalents `0d655bde` and `136c5476`. Root cause was
measured rather than guessed: the derivation returns 10 commits at HEAD and 23 with `--all`, and the
table was built from `--all`, so the dedup step swept orphans **in** rather than out.

The subtlest finding is why a blanket hash substitution would have made things worse: one row's
attribution translates correctly to `0d655bde` and another's does not, because the fail-loud reversal
is `48f9f65d` (2026-07-11) — a commit appearing **0 times** in the artifact, which Worker 0 confirmed
touches both the patch module and its tests. Translating the two together fixes one row and leaves
the other wrong under a now-reachable hash, which no longer announces itself as broken.

**Escalated to Worker 1 as spec custodian, deliberately not resolved by any Slice 1 pass:** the two
cohorts adopted opposite defaults for where the rationale's change record starts — 1a treats
`7014125a` as the recovered plan's baseline, 1b catalogues that same commit as four ship corrections
and two contract flips. Both readings are internally sound. The fact that decides it is the plan
document's upper bound, which neither cohort established: `PLAN-024.md` lists 10 tests while the test
file held 11 by `744fd28d`. The apply-changes pass measures that bound and attaches it; the choice is
Worker 1's (`docs/builder/BUILD.md` `## Spec reconciliation`).

Also recorded: the deferred-work catalog is the **union** of the two cohorts' near-disjoint lists —
neither is complete on its own.

## Slice 1 apply-changes outcome (both artifacts back to `built`; re-review dispatched)

Every finding closed, and the pass did two things worth more than compliance:

- **It found a second wrong count the review did not catch.** Re-checking the counts the M2
  re-attribution touched, entry 13's "12 -> 13 at `48f9f65d`" is really 13 -> 13 — `c7cb5f5c` took
  12 -> 13 and `48f9f65d` is net -2/+2. That is the `## Claims are proven mechanically` failure mode
  reproducing one layer up: a reviewer's own stated number, asserted while illustrating a lesson.
- **It disagreed with the review and logged the disagreement instead of silently applying it**
  (1a note 24), correctly leaving the review section unedited since a reviewer's findings are the
  record of what was found (`docs/builder/BUILD.md` `### The review document is evidence, not
  contract`). The re-review adjudicates it.

The orphan sweep was widened from the two named hashes to **every 8-hex token in both artifacts**:
34 distinct, 32 commits, 30 HEAD-reachable, exactly 2 orphans, both now at 0 body occurrences —
with `d7618b47` / `ed7790a1` identified as patch-ids and `e2765ff3` as a tag object peeling to
`72f6cd9b`. Equivalence proved by `git patch-id --stable`, never by message or date. The derivation
was rebuilt rather than its output patched.

### The cross-cohort conflict's deciding fact is now measured

`TEMP-024.md` is byte-identical to its `7014125a` blob, and `PLAN-024.md` differs from its `7014125a`
blob by exactly two mechanical reference-rewrite lines. **Both planning documents therefore describe
the tree at exactly `7014125a`** — the guessed window collapses to a point. The consequence for the
rationale: the log-once *sentinel* (`744fd28d`) was never in the planned contract at all; only the
INFO-notice no-op it was later built to make true. The choice of where the change record starts
remains Worker 1's, but it is now a choice with evidence rather than a coin flip.

## Slice 1 closed (all three artifacts `review-accepted`)

Three review passes over 1a, one over 1b, one over 3. Final tally of what review caught that the
builders did not, all of it in the **written record** rather than the code:

1. Two commit hashes cited 8 times that are not ancestors of HEAD (concurrent history rewrite).
2. A wrong-commit attribution that a blanket hash translation would have made *less* visible.
3. A commit table that was not the population it claimed to be, under an "after the ship" heading
   covering six in-tag commits.
4. A count inside the reviewer's own finding (`12 -> 13` at `48f9f65d`, actually `13 -> 13`), caught
   by the builder and upheld on adjudication: the progression reproduced pair-by-pair but omitted
   `c7cb5f5c`, and only a name-set diff can see that.
5. `_PATCH_ORIGINAL` — **a symbol that has never existed at any revision**, cited twice, once in a
   `[SPEC]`-marked note bound for the permanent archived spec.

Item 5 is the one that justifies the whole review chain: had it landed, this cycle would have written
an invented symbol name into an archived document while claiming to have removed exactly that class
of defect from the corpus.

Also settled: the "1,536-byte stub" figure was Worker 0's, corrected to a measured 1,618 concurrently
with the review that raised it. Adjudicated in the builder's favour, with the caveat recorded that
the build plan is untracked and so no read-only check can establish what it said at review time —
the two accounts are compatible and neither worker is convicted of a bad measurement.

## Slice 3 review outcome (`review-accepted`, no High and no Medium findings)

The reviewer re-derived the whole population independently rather than accepting the builder's:
61 revisions, all 9 retired names confirmed retired and at 0 whole-token citations, and the headline
"exactly one retired name had a live citation" confirmed. It also proved its own resolver **failable**
— run against pristine HEAD it flags the pre-repair dangling citation; run against the working tree it
flags nothing on the 024 surface. That is the difference between an instrument and an assertion.

Provenance confirmed as card 024's own: `eb2a1764` takes the old name 3 -> 0 in `_django_patches.py`
and never touches `_strawberry_patches.py`, which still carried its citation at that commit.

Three Low findings, all recorded on disk for Worker 1; one is a **deferred-catalog undercount** worth
carrying because it is the recurring shape in this repo: the stale optimizer-test citation is 3
occurrences in 2 files, not 2 in 1, because that instrument's corpus excluded `examples/` while
sibling bullets in the same list quoted repo-wide counts. **A catalog is a claim; re-derive it before
homing it.**

### Escalated to the maintainer (contract-level, no worker's call)

**No gate in this process resolves a symbol citation.** `eb2a1764` passed tests, ruff, and review and
still shipped a dangling cross-module reference that survived four months and eleven commits.
`AGENTS.md` rule 27 states the obligation ("renaming a symbol means grep-sweep `::OldName` in the same
change") and nothing mechanically enforces it. Three paths, for the maintainer to choose between:

1. Commit the reviewer's `scripts/check_citations.py` and wire it as a pre-commit hook (strongest;
   `scripts/` sits outside the coverage gate, so it adds no coverage obligation).
2. Commit it as a CI-only check (catches it before merge, not before commit).
3. Accept per-cycle re-derivation (status quo; this cycle found 1 in-scope defect and 7 out-of-scope
   ones, which is the measured cost of having no gate).

Out of this cycle's scope either way — recorded here and in the deferred-work catalog rather than
acted on.

### Corrections the cohorts made to Worker 0's own dispatch framing

Recorded because a dispatcher's framing pasted into a spawn prompt travels as fact
(`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`):

- The dispatch called all 13 listed commits post-ship. Measured: tag `0.0.7` is `72f6cd9b`, and 6 of
  them (`300e2811`, `893465a5`, `61973f8d`, `7014125a`, `744fd28d`, `e82df83d`) are **inside the
  release**. 15 of 21 surface commits are post-tag.
- The dispatch listed `7cc163db` / `4a25bf42` / `e145ba36` in the wrong order; actual order is
  `e145ba36` (06-01) -> `7cc163db` (06-10) -> `4a25bf42` (06-12). Read in the dispatch's order the
  ASCII sweep appears to be undone.
- The dispatch said "at least one known flip"; the measured figure is **8**.

## Dispatch deviations (deliberate, recorded)

- **Slice 1 skips its Worker 1 planning pass.** The slice contract a planning pass would produce is
  already written in full in this plan (the cycle scope, the recovered input contract, the two
  cohorts' questions, the ownership partition, the floor scope). The maintainer's instruction for
  this cycle is to dispatch workers only where the work needs them. Isolation is **not** waived:
  Slice 1's two audit cohorts are reviewed by a separate Worker 3 invocation before Slice 2 consumes
  them (`docs/builder/BUILD.md` `### Isolation is non-waivable`).
- **Slice 1 runs read-only.** A cohort that finds a code defect records it as a finding and does not
  repair it, so that the decision to open a repair cohort is Worker 0's and the repair is reviewed on
  its own diff.

## Slice 4 dispatch (post-gate, maintainer-directed)

Dispatched after `bld-final-024.md` reached `final-accepted`, on the maintainer's instruction to
enact the deferred item this cycle's own scope already covered. Of the seven entries in that file's
`## Deferred work catalog`, item 6 is the only one whose `*Deferral licensed by:*` clause reads
**nothing** — it is a `.py` docstring defect and the cycle's maintainer-set scope is spec files and
`.py` files. The other six are licensed out: items 1, 2 and 3 are `CHANGELOG.md` / `docs/GLOSSARY.md`
/ `docs/TREE.md` and outside the file-type scope; item 4 is `.py` but belongs to other cards'
renames, which `AGENTS.md` rule 27 binds to the change that caused them; items 5 and 7 are
maintainer decisions no worker may take.

Item 6's deferral reason at the gate was procedural rather than scope-based — a source edit made at
the gate ships unreviewed — so the enactment is a full Worker 2 / Worker 3 slice under the standing
isolation rule, not a Worker 1 touch-up.

**This re-opens the final gate.** The gate's record covers a diff of two Markdown files plus one
`.py` docstring line; Slice 4 adds a second `.py` docstring line, so the sweep is re-run and appended
to `bld-final-024.md` rather than the existing record being read forward onto a diff it never saw.

## Checklist

- [x] Slice 1a: Planned-vs-HEAD gap audit — prove nothing planned for `DONE-024-0.0.7` was skipped,
      dropped, or silently changed -> `docs/builder/bld-slice-1a-024-planned_vs_head.md`
- [x] Slice 1b: Post-ship divergence catalog + contract flips + floor verification
      -> `docs/builder/bld-slice-1b-024-divergence_and_floor.md`
- [x] Slice 1 review: independent Worker 3 pass over both audit artifacts (folded into the 1a/1b
      `Status:` chain; no separate artifact)
- [x] Slice 3: Rename-rot repair sweep — the one in-scope `.py` defect card 024's own rename caused,
      plus the full population sweep for every symbol/path 024 renamed or deleted
      -> `docs/builder/bld-slice-3-024-rename_rot_sweep.md`
- [x] Slice 2: Spec reconstruction + rationale authoring — rewrite the stub as a contract that
      matches HEAD; author the rationale companion carrying every explanation, rejected alternative,
      change record, and retired claim -> `docs/builder/bld-slice-2-024-spec_reconciliation.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration-024.md`
- [x] Final test-run gate -> `docs/builder/bld-final-024.md`
- [x] Slice 4: Orphaned-docstring-fragment repair — `bld-final-024.md` deferred-catalog item 6,
      the one deferred item the catalog itself licenses no deferral for because it is inside this
      cycle's `.py` scope -> `docs/builder/bld-slice-4-024-docstring_fragment.md`
- [x] Final test-run gate re-run after Slice 4's source change, appended to
      `docs/builder/bld-final-024.md`
