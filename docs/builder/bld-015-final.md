# Build: final test-run gate (spec-015 residual-completion cycle)

Spec reference: [`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`][spec-015] (whole file); rationale
companion [`docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md`][spec-015-rationale]
Status: final-accepted

Procedural-closure shape per [`docs/builder/BUILD.md`][build-md] `### Procedural-closure slices`, the
same disposition R1 and R2 carried: dispatched to Worker 1 alone. This artifact carries a combined
Plan + Final-verification block.

> **Closeout note (2026-08-17).** The two round artifacts this file reads and cites throughout —
> `bld-015-r1-rationale_and_spec_reconciliation.md` and `bld-015-r2-doc_completion_archive_audit.md`
> — were **retired at closeout**, along with the cycle's two `worker-memory/spec-015-worker-*.md`
> scratch files. Every reference to them below is preserved as written and de-linked rather than
> rewritten, because this file's findings are traceable only through the rounds that produced them.
> Both remain readable at the commit that landed them:
> `git show 01b011ea:docs/builder/bld-015-r1-rationale_and_spec_reconciliation.md` and
> `git show 01b011ea:docs/builder/bld-015-r2-doc_completion_archive_audit.md`. The surviving pair for
> this cycle is this file and [`docs/builder/build-015-relay_interfaces-0_0_5.md`][build-015], whose
> `## Post-gate disposition of the deferred catalog` records what happened to the catalog below —
> including that **item 1 (F13) was subsequently falsified and its CSV row reverted**, so the
> `### Deferred work catalog` entry for it is superseded.

**This pass changed no spec, no companion, no source, and no test.** Its only writes are this file and
`docs/builder/worker-memory/spec-015-worker-1.md`.

**No `bld-integration.md` exists for this cycle**, by the plan's `## Artifact list` decision: the
cycle lands no source, so there is no cross-slice DRY surface. The integration pass's two live
obligations — [`docs/builder/BUILD.md`][build-md] `## Cross-slice integration pass` step 1 (read every
closed artifact in full) and step 6 (the staged-anchor sweep) — are folded into this gate and
discharged under `### Every closed artifact read` and `### Staged-anchor sweep` below.

## Baseline re-derived

The plan's snapshot is moving, so it was re-derived rather than quoted
([`AGENTS.md`][agents] rule 34, [`START.md`][start] `## Concurrent sessions`).

- `git rev-parse HEAD` -> `4c9e4e0dd66f64b6eb3e29dcf481a9bfb4ec6eae`, re-checked at the start and the
  end of the pass. **Unchanged** — the plan's, R1's, and R2's `HEAD` all still hold.
- `git status --porcelain | wc -l` -> **195** (189 at plan time, 192 during R1, 194 during R2). The
  drift is two concurrent maintainer sessions' work.
- **A concurrent session is running its own `pytest` against this tree while this gate runs.**
  `ps aux | grep pytest` shows a second interpreter under
  `…/dfcff2aa-…/scratchpad/venvs/py3.13-dj52/bin/python -m pytest -o addopts='-n auto --dist
  loadscope' -p no:cacheprovider`, i.e. another session's matrix cell in its own isolated venv. It is
  not this gate's run and was not interfered with; it is recorded because a second suite executing
  against the same working tree is a live variable in any failure attribution below.
- **No baseline-dirty path was edited, reverted, staged, or `git checkout`ed.** No `git stash`,
  `git checkout`, `git restore`, or `git worktree` was used anywhere in this pass.

### This cycle's diff, path by path

Re-derived with `git status --porcelain` plus `git diff --numstat`, filtered to this cycle's own
paths. Everything else under `docs/SPECS/` and `docs/builder/` — `spec-014-*`, `bld-014-*`,
`build-014-*`, and the two `D docs/builder/bld-013-r*.md` deletions — belongs to concurrent cycles and
was neither read as authority nor touched.

| Path | State | Size / delta |
|---|---|---|
| `docs/SPECS/spec-015-relay_interfaces-0_0_5.md` | modified | `+162 / -192`; 66,926 bytes, 596 lines |
| `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md` | new (untracked) | 70,697 bytes, 1,001 lines |
| `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-terms.csv` | modified | `+1 / -0`; 20 lines (header + 19 rows) |
| `docs/builder/build-015-relay_interfaces-0_0_5.md` | new (untracked) | Worker 0's plan |
| `docs/builder/bld-015-r1-rationale_and_spec_reconciliation.md` | new (untracked) | closed `final-accepted` |
| `docs/builder/bld-015-r2-doc_completion_archive_audit.md` | new (untracked) | closed `final-accepted` |
| `docs/builder/bld-015-final.md` | new (untracked) | this file |
| `docs/builder/worker-memory/spec-015-worker-0.md` | new, **gitignored** | Worker 0's memory |
| `docs/builder/worker-memory/spec-015-worker-1.md` | new, **gitignored** | Worker 1's memory |

**Seven committable paths plus two gitignored scratch files.** The two worker-memory files are not
part of the maintainer's diff at all — `git check-ignore -v` reports
`.gitignore:188:docs/builder/worker-memory/`, which is why `git status --porcelain` never lists them.

**Six Markdown files, one CSV row, and two ignored Markdown scratch files. Not one `.py` file, in the
package, in `tests/`, or in `examples/`.** That is the mechanical basis for the attribution in
`### Failure attribution` below: this cycle's diff cannot have caused a Python test failure, because
it contains no Python and no test.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately not run, on the same ground R1 and R2
  recorded. This pass writes one Markdown artifact and one Markdown memory file; it adds no package
  source and proposes no helper, shared constant, validation branch, coercion utility, or test helper.
  [`docs/builder/worker-1.md`][worker-1] `### Package-wide helper inventory before helper planning`
  gates *helper planning*, and there is none here — running the AST inventory over
  `django_strawberry_framework/` would emit ~1,600 lines of index for a pass that cannot write a
  helper. Package source and tests were read anyway, read-only from `HEAD`, as the subject of the
  claims being re-derived.
- **Existing patterns reused.** The artifact shape is [`docs/builder/ARTIFACT.md`][artifact]'s
  template, in the final-gate arrangement the sibling residual cycles used. No invented shape.
- **New helpers justified.** None.
- **Duplication risk avoided.** One shape, and it shaped the catalog: copying R2's six deferred bullets
  forward verbatim would make this artifact a second, unverified source for the same six facts. Every
  catalog item below was **re-derived from `HEAD` in this pass** and cites the measurement, so the
  catalog is a reading rather than a transcription — which is how it grew from six items to eight.

### Implementation steps

1. Re-derive the baseline, `HEAD`, and this cycle's diff.
2. Run every command in [`docs/builder/BUILD.md`][build-md] `## Final test-run gate`, in that order,
   and record each one's exact invocation and pass/fail.
3. Diagnose and attribute every failing row; for anything not this cycle's, record the evidence and
   escalate rather than fix, mask, skip, or `xfail`.
4. Discharge floor verification against the plan's declared scope.
5. Run the staged-anchor sweep.
6. Read both closed artifacts in full and write the `### Deferred work catalog`.
7. Write `## Cycle outcome`, set `Status:`, append a memory entry.

### Test additions / updates

None. This pass writes no code and no test. No `--cov*` flag was used anywhere in it; `--no-cov` is
the only coverage-shaped flag that appears, and only because `pytest.ini`'s `addopts` auto-applies
`--cov` ([`docs/builder/BUILD.md`][build-md] `## Coverage is the maintainer's gate, not a worker's
tool`). No line-coverage figure was inspected or asserted.

### Implementation discretion items

- **Whether the two "looseness items" R2 recorded outside its deferred list belong in the catalog.
  Decided, not delegated: they do.** [`docs/builder/BUILD.md`][build-md] `## Final test-run gate`
  scopes the catalog to "every item explicitly deferred to a future slice, future spec, or maintainer
  follow-up", and both were assessed, left unfixed, and are surviving inaccuracies in this cycle's own
  output. Leaving them only inside a count-corrections table would lose them at the next spec author's
  reading, which is the one thing the catalog exists to prevent. They are catalogued at the bottom,
  marked as the low-severity pair they are.
- **Whether the Test plan's illustrative-query mismatch is `revision-needed` on R2.** Decided: **no.**
  It is an illustrative example inside a `## Test plan` bullet, not a normative statement; the
  invariant each bullet describes is the one its named row actually asserts, which is the load-bearing
  half and holds. Re-looping a closed, twice-verified round over an example query name would cost more
  than it buys. Catalogued with its re-derivation instead.

### Dispatched findings checklist

The gate's own required rows, one box per item this pass owes
([`docs/builder/BUILD.md`][build-md] `## Final test-run gate`, `## Floor verification`, and
`## Cross-slice integration pass` steps 1 and 6).

- [x] `uv run pytest --no-cov` — full sweep across all three test trees, run and recorded.
- [x] `uv run python examples/fakeshop/manage.py check`.
- [x] `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`.
- [x] Lint / format / diff gate, read-only: `uv run ruff format --check .`, `uv run ruff check .`,
      `git diff --check`.
- [x] `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-015-relay_interfaces-0_0_5.md`
      and `uv run python scripts/check_trailing_commas.py --check`.
- [x] Floor verification: the plan's declared scope is `none`; the declaration re-verified as correct
      and **no floor venv built**.
- [x] Staged-anchor sweep for `TODO(spec-015` / `TODO-<MILESTONE>-015`.
- [x] Both closed artifacts read in full (integration-pass step 1, folded in).
- [x] `### Deferred work catalog` written, re-derived rather than copied.
- [x] `## Cycle outcome` written.

---

## Final verification (Worker 1)

### Gate results

Every command as invoked, in [`docs/builder/BUILD.md`][build-md] `## Final test-run gate` order.

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **pass** — `6085 passed, 40 skipped in 475.33s (0:07:55)`, exit 0. **Zero failures, zero errors.** |
| 2 | `uv run python examples/fakeshop/manage.py check` | **pass** — `System check identified no issues (0 silenced).`, exit 0 |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **pass** — `No changes detected`, exit 0 |
| 4a | `uv run ruff format --check .` | **pass** — `423 files already formatted`, exit 0 |
| 4b | `uv run ruff check .` | **pass** — `All checks passed!`, exit 0 |
| 4c | `git diff --check` | **pass** — no output, exit 0 |
| 5a | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-015-relay_interfaces-0_0_5.md` | **pass** — `OK: 19 terms - all have glossary entries and at least one spec link.`, exit 0 |
| 5b | `uv run python scripts/check_trailing_commas.py --check` | **fail, exit 1 — 2 rows, both outside this cycle's five paths** (see below) |
| 6 | Floor verification | **scope `none` as declared; declaration re-verified correct; no floor venv built** |
| 7 | Staged-anchor sweep | **pass** — no matches |

Rows 2, 3, 4a, 4b, and 4c pass over the **whole tree**, concurrent sessions' ~195 dirty paths included.
That is a stronger result than the gate requires and is worth stating plainly: no dirty file in the
tree carries a formatting, lint, whitespace, or conflict-marker error right now.

Row 5a is the figure R2 moved: `OK: 18 terms` before this cycle, `OK: 19 terms` after its one CSV row.

#### Row 5b — the two `check_trailing_commas --check` rows, separated as required

```text
.claude/projects/-Users-riordenweber-projects-django-strawberry-framework/memory/
  one-spec-owns-each-feature.md:20: should carry the canonical LINK-DEFINITIONS footer scaffold
django_strawberry_framework/utils/inputs.py:723: should collapse (< threshold, over-exploded)
```

**Rows in this cycle's own paths: zero.** Neither path is writable by this cycle, and neither is
Markdown this cycle authored. Both reproduce R2's identical baseline reading, so neither is drift this
gate introduced.

- `.claude/projects/…/memory/one-spec-owns-each-feature.md` — **not in the repository at all.**
  `git ls-files --error-unmatch` reports `did not match any file(s) known to git`, and
  `git check-ignore -v` reports `.gitignore:170:.claude/`. It is an agent memory file under an ignored
  directory; the layout script simply walks the filesystem rather than the index.
- `django_strawberry_framework/utils/inputs.py` — **dirty with a concurrent session's uncommitted
  work** (`git status --porcelain` -> ` M`), last committed at `4c9e4e0d`. Proven not to be a baseline
  defect and not this cycle's, read-only:
  `git show HEAD:django_strawberry_framework/utils/inputs.py` was written to a scratch path outside
  the repo and checked directly — `check_trailing_commas.py --check inputs.py` on the `HEAD` copy
  **exits 0**. The violation exists only in the working-tree version, so a concurrent session's
  in-flight edit introduced it. Not fixed, not `--fix`ed, not reverted ([`AGENTS.md`][agents]
  rule 34); recorded and escalated.

**Neither row blocks `final-accepted`**, per the dispatch's rule that only rows inside this cycle's own
paths can.

### Failure attribution

**There is nothing to attribute on the `pytest` row. The full sweep is green: `6085 passed, 40
skipped`, zero failures and zero collection or setup errors, across all three test trees.**

That outcome was not the expected one and is worth recording as a result rather than a non-event. The
dispatch anticipated failures this cycle does not own, because the sweep runs ~195 uncommitted paths
belonging to two concurrent maintainer sessions — and the sibling spec-014 cycle's plan records its
own gate closing on `2 failed, 5964 passed`, both failures attributed to a concurrent session's dirty
`filters/sets.py` pair. (That figure is read from the concurrent cycle's document as precedent only;
this pass neither verified nor could verify it, and does not rely on it.) What this gate measured is
that the concurrent hardening cycle's in-flight work is, at this moment, self-consistent and green.

Two things follow, and both are worth stating explicitly because the dispatch asked for them:

- **This cycle's diff could not have caused a test failure in any case.** Its paths are
  enumerated under `### This cycle's diff, path by path`: eight Markdown files and one CSV row. No
  `.py` file in `django_strawberry_framework/`, `tests/`, or `examples/` is in the diff, so no test
  and no code under test changed. Saying so is not a hedge here — it is the standing attribution that
  would have carried any failing row straight to a concurrent session, and it holds independently of
  the run's outcome.
- **No test was fixed, masked, skipped, or `xfail`ed**, and none needed to be
  ([`AGENTS.md`][agents] rule 34). The 40 skips are the suite's standing skips — the
  `FAKESHOP_SHARDED`-gated rows skip under the default invocation by design
  ([`AGENTS.md`][agents] rule 30), alongside soft-dependency and vendor-gated rows. The 40 were not
  broken down by reason and no claim is made about their composition; the load-bearing fact is that
  **this pass added no test and skipped none**, so no skip in that count is attributable to it. No
  `--cov*` flag was used and no line-coverage figure was read.

**One live variable is recorded rather than dismissed.** A concurrent session was running its own
`pytest` against this same working tree throughout (its own isolated
`…/scratchpad/venvs/py3.13-dj52` interpreter, `-n auto --dist loadscope -p no:cacheprovider`). Two
suites executing concurrently against one checkout can in principle interfere through the tracked
sqlite databases; this run shows no sign of it, and `examples/fakeshop/db.sqlite3` is clean at `HEAD`
and was not written by this pass. Recorded so that a *future* gate seeing an unreproducible failure on
this tree has the precedent to check for a second runner before attributing it to code.

**Nothing is escalated to the maintainer from the `pytest` row.** The only escalation this gate raises
is the `check_trailing_commas` row above — a concurrent session's uncommitted `utils/inputs.py` edit,
proven read-only against the `HEAD` blob to be that session's and not a baseline defect.

### Floor verification

**The plan declares floor-verification scope `none`**
([`docs/builder/build-015-relay_interfaces-0_0_5.md`][build-015] preamble: "Floor-verification scope:
**none.** No item touches a Django / Strawberry / channels integration seam — no item touches
executable code at all.").

**The declaration was re-verified rather than accepted, and it is correct.** The gate is the backstop
that confirms a declared floor run happened ([`docs/builder/BUILD.md`][build-md]
`## Floor verification`), so the thing to check here is whether `none` was the right declaration. It
was: `### This cycle's diff, path by path` above enumerates every path, and every one is Markdown
or a CSV row. None of `## Floor verification` `### When it is required`'s seams — request/response
handling, view or ASGI plumbing, upload or body parsing, session/auth, queryset or expression
compilation, schema and type construction against Strawberry internals, consumer or middleware wiring
— is reachable from a diff containing no executable code.

**No floor venv was built**, as instructed, and the shared `.venv` was neither installed into nor
otherwise mutated.

### Staged-anchor sweep

[`docs/builder/BUILD.md`][build-md] `## Cross-slice integration pass` step 6, folded into this gate.

```shell
grep -rEn 'TODO\(spec-015|TODO-(ALPHA|BETA|STABLE)-015' . \
  --exclude-dir=.git --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md
```

-> **no matches** (exit 1). Nothing staged under this spec's or this card's name survives in shipped
source, tests, comments, or docs.

Re-run **without** the three board exclusions, the sweep still returns nothing: `KANBAN.md`,
`KANBAN.html`, and `BACKLOG.md` carry no `TODO-<MILESTONE>-015` row either, because card 015 shipped
long ago as `DONE-015-0.0.5` and its number is not reused. The exclusion is therefore vacuous here
rather than load-bearing, which is worth stating so a future reader does not assume it hid something.
This reproduces R2's independent sweep.

### Every closed artifact read

[`docs/builder/BUILD.md`][build-md] `## Cross-slice integration pass` step 1 — no "as needed".

- `docs/builder/bld-015-r1-rationale_and_spec_reconciliation.md` — read in full, 282
  lines. `Status: final-accepted`. Its `### Dispatched findings checklist` carries F1-F12 plus W1a-W1c,
  every box `- [x]`, no box deferred.
- `docs/builder/bld-015-r2-doc_completion_archive_audit.md` — read in full, 587 lines.
  `Status: final-accepted`. Its `### Dispatched findings checklist` carries F13-F16 plus the
  adversarial re-derivation box, every box `- [x]`, no box deferred.

**Neither artifact has a `What looks solid` section**, and correctly so: that heading belongs to
[`docs/builder/ARTIFACT.md`][artifact]'s `## Review (Worker 3)` block, and neither item had a Worker 3
review — both were procedural-closure items dispatched to Worker 1 alone. The equivalent content in
this cycle lives in R2's `### Adversarial re-derivation of R1`, which was walked line by line for this
catalog. Likewise there are no `### Failability proofs`, `### Hot-path budget`, or `### Floor
verification` build-report subsections to audit: no Worker 2 pass ran, because the cycle introduces no
boundary, no hot path, and no executable code.

### Checklist audits carried forward

The final-verification duty in [`docs/builder/worker-1.md`][worker-1] `## Final verification job`
step 3 was discharged inside each round by that round's own combined block, and both are re-confirmed
here by reading:

- R1: 15 boxes, all `- [x]`, none deferred.
- R2: 5 boxes, all `- [x]`, none deferred. F14's box is ticked as **verified and catalogued**, which is
  exactly what the plan dispatched it as ("recorded, not dispatched"), not as a repair claim.

**The spec's own `## Slice checklist` boxes remain `- [ ]`, and that is correct, not an un-ticked
deferral.** Spec-015 is an archived, shipped spec for card `DONE-015-0.0.5`; its `Status:` line is the
source of truth for shipped state, and the checklist is preserved as the historical build sequence.
This cycle did not tick them and should not have.

### Verifications this pass re-derived rather than inherited

Nothing below was accepted from R1 or R2 on prose. Every source and test reading was taken read-only
via `git show HEAD:<path>` into
`/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/<session>/scratchpad/`,
per [`docs/builder/BUILD.md`][build-md] `## Claims are proven mechanically, never accepted on prose`.

| Claim | Re-derivation | Verdict |
|---|---|---|
| Spec is 66,926 bytes / 596 lines after R2 | `wc -c` / `wc -l` | **exact** |
| Rationale companion, post-addendum | 70,697 bytes / 1,001 lines (R1 recorded 63,860 / 910 pre-addendum) | **consistent** |
| Terms CSV is one row per anchor, 19 rows | read in full: 20 lines, header + 19 rows, no duplicate `term`, no duplicate `anchor`, `public-exports` present in alphabetical position | **holds** |
| R2-a's three restored anchors resolve | see the substring sweep below | **holds** |
| "All 13 substrings resolve" (R2) | sweep below: 18 citation sites, 11 distinct substrings, 0 dangling | **holds, and re-stated as a population** |
| 20 `path::Symbol` refs in the spec, none dead (R2) | sweep below | **exact — 20, none dead** |
| F15's link audit (both files clean, ten headers in order) | sweep below | **holds** |
| F14 is 8 occurrences in 4 files | sweep below | **exact** |
| The A/B row is genuinely absent at `HEAD` | `git grep -c test_relay_target_relation_planning_unchanged HEAD -- tests/ examples/` -> no output | **absent, as recorded** |
| The stale test-docstring cross-reference | read at `HEAD`; **sharpened** — see catalog item 5 | **holds, with a correction** |
| The two non-unique anchors (R2-d) | `#"version ="` -> 2 in `pyproject.toml`; `#"_attach_relation_resolvers"` -> 3 in `types/finalizer.py` | **exact** |
| The Test plan's illustrative queries | **newly re-derived here** — see catalog item 7 | **R2's looseness note holds, and is worse than stated** |

#### Substring-citation sweep

Every `spec-015 … #"substring"` citation in shipped source, tests, and examples at `HEAD`, resolved
against the reconciled spec and its companion:

- **18 citation sites**, **11 distinct substrings**, **0 dangling**.
- 16 of the 18 resolve **exactly once in the spec**; the remaining two — both quoting
  ``surface any `TypeError` as a `ConfigurationError` `` from `types/relay.py::apply_interfaces` and
  its test row — resolve in the **rationale companion**, which is precisely the disposition R2
  recorded and catalogued (item 2 below). No citation is broken.
- **One observation the sweep produced that neither round could have seen.** In the *working tree*
  (not at `HEAD`), the concurrent hardening session has re-wrapped that same comment in
  `django_strawberry_framework/types/relay.py`, so the substring is now split across a line break and
  a plain grep for it no longer matches. The citation still points at real text and nothing is
  falsified; it is recorded because a line-wrapped `#"substring"` anchor is invisible to the very
  grep-sweep [`AGENTS.md`][agents] rule 27 relies on. It is in a dirty file owned by another session,
  so it is not this cycle's to touch, and it strengthens rather than weakens catalog item 2.

#### `path::Symbol` sweep

Every repo-local `path::Symbol` reference in the reconciled spec, resolved against `HEAD` blobs
(upstream `strawberry_django/…` and `django_graphene_filters/…` refs excluded — they name local
comparison checkouts, not repo paths): **20 distinct refs, 0 dead.** R2-b's correction from
`types/resolvers.py::_is_fk_id_elided` to `::_build_fk_id_stub` holds at `HEAD`.

#### Link / anchor audit (F15, re-derived)

Both Markdown files, resolving each definition to its **resolved** target rather than testing
existence, with the depth-masking trap in mind:

| | spec | rationale |
|---|---|---|
| link definitions | 20 | 37 |
| distinct refs used in the body | 20 | 37 |
| undefined refs | 0 | 0 |
| orphaned defs | 0 | 0 |
| targets missing on disk | 0 | 0 |
| dead heading anchors | 0 | 0 |
| ten canonical group headers, in order | yes | yes |

One methodological note so the numbers are re-derivable: a naive slug function that strips `_` reports
three false "dead anchor" hits in the spec (`#apply_cascade_permissions`, `#finalize_django_types`,
`#metaoptimizer_hints`), and a sweep that does not strip code spans reports one false "undefined ref"
in the rationale (a `` `[apply_cascade_permissions][glossary-…]` `` written inside backticks as prose
about the link pattern). Both are artifacts of the checker, not of the files; `check_spec_glossary`
exiting 0 on 19 terms independently confirms the anchors.

#### F14, re-derived

`git grep` over `django_strawberry_framework/`, `tests/`, and `examples/` at `HEAD`, counting
**occurrences** rather than matching lines:

| File | Occurrences |
|---|---|
| `django_strawberry_framework/types/base.py` | 5 |
| `django_strawberry_framework/types/resolvers.py` | 1 |
| `tests/types/test_base.py` | 1 |
| `tests/filters/test_sets.py` | 1 |

**8 occurrences across 4 files** — Worker 0's, R1's, and R2's figure, reproduced a fourth time
file-for-file. The raw `git grep -oh … | wc -l` reports 9; the extra row is git's
`Binary file … matches` line for `examples/fakeshop/db.sqlite3`, whose own hits are kanban card text
and out of scope. R2 recorded that same discrepancy, and it reproduces.

### DRY check across the whole cycle

[`docs/builder/worker-1.md`][worker-1] `## Final verification job` step 4. The cycle produced **no
code**, so there is no duplicated helper, repeated literal, or inconsistent helper shape to find. The
one DRY question the cycle actually faced was documentary and both rounds answered it the same way:
a moved deliberative passage must live in exactly one of the two files. R2's disposition on R2-a's
fourth anchor — quote the moved sentence in the companion rather than un-move it into the spec — is
the correct application, and it is why the spec and its companion do not now hold two copies of one
risk bullet. Verified by the substring sweep above: the sentence occurs 0 times in the spec and 2
times in the companion.

### Deferred work catalog

[`docs/builder/BUILD.md`][build-md] `## Final test-run gate` requires this subsection and Worker 1 is
its only author. Every item below was walked out of the two closed artifacts' `### Notes for Worker 1
(spec reconciliation)`, `### Adversarial re-derivation of R1`, and count-correction sections, and then
**re-derived from `HEAD` in this pass** rather than copied. R2 reported six; re-derivation yields
**eight**, the two additions being the pair R2 recorded as "looseness items" outside its own numbered
list (items 7 and 8), which the catalog's purpose says belong in it.

None of the eight is a code defect. **Nothing spec-015 promised is missing from the shipped code.**

1. **`DONE-015-0.0.5`'s card-side glossary sync — the open half of F13.** *Source:*
   `bld-015-r2` `### F13`, and its `### Notes for Worker 1` item 1. *Licensing:* none in
   the spec; it is a board-state obligation, not a spec obligation. *Description:* R2 closed the
   file-side half by adding the `public exports,public-exports,…` row, so the terms CSV now carries 19
   rows and `check_spec_glossary` reads `OK: 19 terms`. The card still renders **18** glossary terms
   and `import_spec_terms --check` will report this card's mention set short by one until the DB is
   synced. **This cycle is barred from the write**: `docs/GLOSSARY.md` and `docs/TREE.md` are dirty
   with concurrent work, so a regenerate would publish rows that have not landed, and
   `examples/fakeshop/db.sqlite3` is clean at `HEAD` — a partial write now hands the maintainer a
   mixed diff. **Precondition state, measured at gate close** (the sibling spec-014 cycle's F14 shows
   this can clear mid-flight, so it is recorded precisely rather than as "blocked"):
   `examples/fakeshop/db.sqlite3` **clean**, `KANBAN.md` **clean**, `KANBAN.html` **clean**,
   `docs/GLOSSARY.md` **dirty**, `docs/TREE.md` **dirty**. The two kanban regenerates would therefore
   produce an attributable diff today; the bar is the dispatch's own — **this cycle makes no database
   write** — plus the fact that `import_spec_terms` processes *every* done card, so its `db.sqlite3`
   diff legitimately spans more than card 015. **Exact recipe**, from
   [`docs/builder/worker-0.md`][worker-0]
   `## Closing out a kanban card` (its steps 5, 7, and 8; steps 1-4 and 6 are already satisfied —
   the card is Done, its `SpecDoc` exists, the `GlossaryTerm` row for `public-exports` exists, proven
   by `## Public exports` being a heading in the `HEAD` blob of `docs/GLOSSARY.md`):
   1. `uv run python examples/fakeshop/manage.py import_spec_terms` — processes every done card and
      creates the `CardGlossaryTerm` + `GlossarySpecMention` rows from each CSV. Run through the
      Django ORM, never raw SQL, so the `post_save` that creates the `UUIDModel` side-row fires.
   2. `uv run python scripts/build_kanban_md.py` and `uv run python scripts/build_kanban_html.py`
      from the repo root. `build_glossary_md.py` is **not** required — no `GlossaryTerm` row changes,
      only card links — and should be skipped while `docs/GLOSSARY.md` is dirty.
   3. Verify: `import_spec_terms --check` reports OK for **all** done cards (a `--check` failure on an
      *earlier* card whose mentions still point at a pre-archive `docs/` path is expected and is
      reconciled by the plain sync, so the `db.sqlite3` diff legitimately spans more than card 015 —
      flag the wider diff to the maintainer); `KANBAN.md` renders 19 glossary terms under
      `### [DONE-015-0.0.5 …]` `#### Glossary terms`; two consecutive regenerates hash identically;
      `uv run python examples/fakeshop/manage.py check` passes.

2. **Re-anchor the one source citation the rationale move legitimately stranded.** *Source:*
   `bld-015-r2` finding R2-a (the fourth row) and its `### Notes for Worker 1` item 2.
   *Licensing:* [`docs/builder/BUILD.md`][build-md] `## Spec rationale extraction` — the section that
   carried the sentence was deliberative and correctly left the spec. *Description:*
   `django_strawberry_framework/types/relay.py::apply_interfaces` and the matching
   `ConfigurationError`-wrap row in `tests/types/test_relay_interfaces.py` cite
   ``spec-015 Risk note #"surface any `TypeError` as a `ConfigurationError`"``, and
   `## Risks and open questions` now lives in the companion. R2 quoted the bullet **verbatim** in the
   companion's addendum so the citation resolves inside spec-015's own file family — confirmed by this
   pass's sweep (0 in the spec, 2 in the companion). The ideal repair retargets the two comments at
   `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md` or at Decision 1's own
   `ConfigurationError`-wrap sentence. Both files are dirty with the concurrent hardening cycle, so it
   is a source/test edit outside this cycle's writable set. **Newly relevant:** that same comment has
   since been line-wrapped in the working tree by the concurrent session, so the substring no longer
   matches a plain grep there — one more reason to retarget it rather than leave it.

3. **The `[spec-011]` renumber cluster — plan F14.** *Source:* the plan's `### R2 findings` F14 and its
   three-bullet ownership argument; `bld-015-r1` `### Notes for Worker 1` item 3;
   `bld-015-r2` `### F14`. *Licensing:* none in the spec — it is a citation defect
   created by the `81e4704d` renumber, outside spec-015's contract. *Description:* commit `81e4704d`
   renamed `spec-011-relay_interfaces-0_0_5.md` to `spec-015-…` without sweeping the citations, so **8
   occurrences across 4 files** now point at `spec-011-stale_placeholder_cleanup-0_0_4.md`, a
   different document (5 in `types/base.py`, 1 in `types/resolvers.py`, 1 in `tests/types/test_base.py`,
   1 in `tests/filters/test_sets.py`). Re-derived a fourth time in this pass, file-for-file.
   **It stays on `TODO-ALPHA-051-0.0.15` and was deliberately not stolen, for two reasons:**
   - *The card's explicit boundary.* `TODO-ALPHA-051-0.0.15` ("Boundary hardening and system-wide DRY
     squeeze") already carries the cluster with the correct population and target, and states in
     terms: "fold into whichever WP batch legitimately opens the file and retarget the citations —
     widening into a documentation sweep is the error to avoid; the documentation half of the cluster
     is owned by `TODO-ALPHA-052-0.1.0`." This cycle's writable set opens none of those four files, so
     it is not such a batch. [`docs/builder/worker-0.md`][worker-0] #"When a reference is wrong across
     multiple surfaces" prescribes cataloguing over a one-surface partial fix.
   - *The concurrent session is rewriting those exact bodies.* All four files are dirty with the
     in-flight hostile-input hardening cycle, whose diff rewrites the `_validate_interfaces` and
     `apply_interfaces` bodies carrying four of the eight citations. Editing them now collides head-on
     with [`AGENTS.md`][agents] rule 34 and [`START.md`][start] `## Concurrent sessions`.
   **Worth batching with item 2** — same defect class, and two of the same files.

4. **The A/B relation-planning row.** *Source:* `bld-015-r1`
   `### The adversarial obligation` and its `### Notes for Worker 1` item 1; `bld-015-r2`
   `### Notes for Worker 1` item 4. *Licensing:* spec-015 Decision 7's relation-traversal invariant,
   as reconciled — the spec now states the invariant without claiming a specific ORM verb, which is
   what makes the missing row visible. *Description:* `test_relay_target_relation_planning_unchanged`
   was the A/B row (a Relay target under a **non-Relay** root, asserting `"category" in
   plan.select_related`); it was built at `e6907fa8` and retired at `4f4db722` in favour of live
   coverage. Confirmed absent at `HEAD` by this pass. Its live replacements pin planning **across**
   Relay targets, but not planning **unchanged relative to a non-Relay target** — and since spec-034's
   cascade every `products` type carries a `get_queryset`, so all of them take the `Prefetch`
   downgrade path and no comparison survives. **Nothing regressed**; the comparative assertion is
   simply no longer pinned. Writing it is a test change no item of this cycle was authorized to make.

5. **A stale cross-reference inside a shipped test docstring.** *Source:* `bld-015-r1`
   `### Notes for Worker 1` item 2; `bld-015-r2` `### Notes for Worker 1` item 5.
   *Licensing:* none — it is a source-comment defect, not a spec claim. *Description:*
   `tests/types/test_relay_interfaces.py::test_relay_node_strips_django_id_annotation` closes with
   "End-to-end coverage of the same suppression path lives in
   `tests/types/test_definition_order_schema.py`". **Sharpened by re-reading in this pass:** both
   rounds described that file as the one whose Relay extensions `be9130e3` retired, which is right but
   under-states the trap — **the file still exists at `HEAD`**, so the reference does not fail a
   file-existence check; it simply carries **zero** Relay coverage now (`grep -niE 'relay|node|
   global_id'` over its `HEAD` blob returns nothing). A reader following the pointer lands on a real
   file that cannot support the sentence. The end-to-end coverage now lives in
   `examples/fakeshop/test_query/test_library_api.py`'s two live twins. Test-file edit, outside the
   writable set; the file is dirty with the concurrent cycle.

6. **Two non-unique `#"substring"` anchors in the spec.** *Source:* `bld-015-r2` finding
   R2-d and its `### Notes for Worker 1` item 6. *Licensing:* [`AGENTS.md`][agents] rule 27's "unique
   substring" requirement. *Description:* `pyproject.toml #"version ="` matches **2** times and
   `django_strawberry_framework/types/finalizer.py #"_attach_relation_resolvers"` matches **3** —
   both re-measured here, both exact. Both **predate this cycle** (identical in the `HEAD` spec) and
   both point at the right place, so R2 recorded them and deliberately did not "fix" them: rewriting a
   working anchor to buy uniqueness is exactly how finding R2-a's breakage starts. A future custodian
   pass may tighten them, and must sweep the citing source in the same change if it does.

7. **The Test plan's projection bullets illustrate a query the shipped rows do not send.** *Source:*
   `bld-015-r2` `### R1's counts, re-derived`, closing "looseness items" paragraph —
   recorded there and deliberately not treated as a defect. *Licensing:* none; the mismatch is
   illustrative, not normative. *Description:* re-derived independently here and it is **slightly
   worse than R2 stated**. The spec's `## Test plan` describes
   `test_relay_id_only_projection_includes_pk_attname` as "selecting `{ allItems { id } }`" and
   `test_relay_id_does_not_trigger_lazy_load` as "selecting `{ allItems { id otherScalar } }`"; the
   shipped rows in `tests/optimizer/test_relay_id_projection.py` send `{ allCategories { id } }` and
   `{ allCategories { id name } }` respectively — so both the root field **and** the second selection
   name are wrong, and `allItems` does appear in that module, but in a **different** test
   (`test_relay_id_with_custom_pk_attname_avoids_lazy_load`), which is what makes the error look
   plausible on a grep. The invariant each bullet describes is the one its named row actually asserts,
   which is the load-bearing half and holds. Deliberately not routed back as `revision-needed` (see
   `### Implementation discretion items`); a one-line spec correction for a future custodian pass.

8. **The risk register is summarized, not reproduced verbatim, in the companion.** *Source:*
   `bld-015-r2` `### R1's counts, re-derived`, same closing paragraph. *Licensing:*
   [`docs/builder/worker-1.md`][worker-1] `### Performing the rationale move` — the move's obligation
   is that moved text leaves the spec, not that it is transcribed word for word. *Description:*
   R1's rationale marks `## Risks and open questions` "*Moved, all eleven bullets*", and all eleven
   are present — but as a three-column summary table rather than the original prose, so the marker is
   true of the substance and not of the wording. The one bullet a source comment cites is now verbatim
   in the addendum (item 2), which closes the only case where the difference was load-bearing.
   Recorded so a future reader does not diff the companion against `git show HEAD:` the old spec and
   conclude text was lost. No action required unless a later citation needs another bullet verbatim.

**Plan-side bookkeeping for Worker 0** (not deferred work; recorded because
[`docs/builder/build-015-relay_interfaces-0_0_5.md`][build-015] is Worker 0's file and this pass may
not edit it):

- The plan's `### R2 findings` F13 row reads "the terms CSV carries **18**". Correct as history and at
  the time of writing; the CSV now carries 19 and the finding's file-side half is closed. The row
  should read as closed, with the card-side half pointing at catalog item 1.
- The plan's `## Checklist` third box — `Final test-run gate -> docs/builder/bld-015-final.md` — is
  ready to mark `- [x]` on the strength of this artifact.
- R1's two plan corrections (V12's evidence sentence; the `4f4db722` / `be9130e3` row order) are
  already folded into `## Corrections to this plan, recorded` and were re-confirmed by R2. No further
  plan correction is owed by this pass: every figure in `## Corrections to this plan, recorded` that
  this gate re-measured (F14's population, the spec's byte and line counts, `OK: 19 terms`)
  reproduced exactly.

### Spec changes made (Worker 1 only)

**None.** This pass changed no spec, no rationale companion, no terms CSV, no source, and no test, per
its dispatch. The spec's status/header lines were re-verified at the start of the pass as
[`docs/builder/worker-1.md`][worker-1] `## Spec status-line re-verification (every Worker 1 spawn)`
requires — `Status: shipped. Primary spec for the 0.0.5 Relay foundation and the single source of
truth for card DONE-015-0.0.5.`, `Predecessors:` pointing at `DONE-015-0.0.5`, and the
`Rationale companion:` line R1 added — and **the build falsified none of them**, so no edit was owed
and none was made.

No `- [ ]` box in either closed artifact's checklist is un-ticked, so no deferral reason is owed here
either.

### Validation run

- Writable files this pass touched: `docs/builder/bld-015-final.md` (this file) and
  `docs/builder/worker-memory/spec-015-worker-1.md`. Both Markdown.
- `uv run python scripts/check_trailing_commas.py --check` scoped to those two files -> exit 0 (the
  Markdown link-def scaffold gate).
- `ruff format` / `ruff check --fix` were **not** run: neither writable file is Python, so both would
  be no-ops on them, and a repo-wide invocation would rewrite ~195 dirty paths belonging to two
  concurrent sessions.
- `git status --porcelain` after the pass shows this cycle's seven committable paths and nothing else
  newly changed by it; the count moved **195 -> 196**, the one entry being this artifact. `HEAD` is
  still `4c9e4e0d`, re-checked at close. Nothing was staged. **Nothing was committed** — only the
  maintainer commits.

## Cycle outcome

**The cycle's diff is seven committable paths, and not one of them is executable.** The reconciled
spec (`+162 / -192`, now 66,926 bytes / 596 lines), its new 70,697-byte rationale companion, one CSV
row, Worker 0's plan, and three `bld-015-*` artifacts — plus two namespaced worker-memory files that
are gitignored and never reach the maintainer's diff. **No package source and no test file was
written, and no database write was made.** That is the mechanical answer to the only question this
gate could have raised about its own dirty-tree failures: a diff with no Python in it cannot break a
Python test.

**Nothing was skipped in the code, and the verdict rests on three independent derivations rather than
one.** Worker 0's V1-V15 verification pass found every promise of spec-015 present at `HEAD`; R1
re-derived all fifteen from `git show HEAD:` blobs rather than accepting them; R2 then re-read the
bodies a third time and reports that **every R1 claim about what the code does survived**. Three tests
the Test plan names are absent under their own names, and all three were proven **built then
relocated**, never skipped — two schema rows to live twins at `be9130e3`, one optimizer row to live
products coverage at `4f4db722`. The one thing that changed is that the spec now says so.

**What the adversarial passes caught that the dispatched finding lists did not.** The F1-F16 list
Worker 0 handed over was not exhaustive, and this is the argument for the second pass stated as
evidence rather than as principle:

- *R1 found three, all fixed in its own writable set:* three `README.md #"For the current capability
  snapshot"` citations for a public-surface promise that paragraph does not make; an
  `id: relay.NodeID[str] = strawberry.field(...)` recourse offered twice that `0.0.6`'s Relay id guard
  now **refuses**; and a Decision-1 citation of a `types/base.py` block comment deleted when the pass
  landed.
- *R1 also found the cycle's sharpest drift, and it was in Worker 0's own evidence.* The plan's V12
  cited the live suite as pinning forward-FK `select_related`.
  `test_products_optimizer_selects_nested_forward_fk_depth_2_over_http` **kept its name while its
  assertion was inverted** — spec-034's cascade gave `ItemType` and `CategoryType` custom
  `get_queryset` methods, so the optimizer now downgrades that chain to a windowed `Prefetch`, and the
  row pins a 3-query Prefetch chain with no JOIN. V12's *conclusion* was unaffected. This is the third
  consecutive residual cycle whose one real drift is a test whose name outlived its assertion, and the
  first in which the false sentence was the plan's own.
- *R2 found four more that R1's own artifact does not name, one of them High.* **R1's reconciliation
  retired four `spec-015 #"substring"` anchors that seven shipped source and test sites quote** —
  rewording a cited sentence breaks a citation exactly the way renaming a symbol breaks a
  `::QualifiedName`, and the causes were an inserted "the", a dropped "explicitly", a dropped
  parenthetical, and one section legitimately moved. R2 restored three and quoted the fourth verbatim
  in the companion. It also caught a dead `::QualifiedName` (`_is_fk_id_elided`, absent at `HEAD`)
  carried forward inside the one Decision R1 otherwise rewrote, and a Decision-3 code fence missing the
  shipped `existing_func is not None` guard — as written it would silently overwrite a consumer
  override that carries no `__func__`, which is contract-relevant, not cosmetic. Five of R1's counts
  did not re-derive and were corrected.
- *This gate found one more, on the same theme.* The concurrent session has since **line-wrapped** one
  of those cited comments in the working tree, so the substring no longer matches a plain grep there.
  Nothing is falsified, but the anchor is now invisible to the sweep [`AGENTS.md`][agents] rule 27
  depends on — which is an argument for retargeting it (catalog item 2) rather than leaving it.
- *This gate also sharpened two catalog items by reading rather than inheriting.* The stale test
  docstring points at a file that **still exists** and merely no longer carries the coverage it names
  — worse than "the file is gone", because no existence check catches it. And the Test plan's
  projection bullets are wrong on both the root field and the selected field, with the wrong root
  field appearing in a *different* test in the same module, which is what makes the error survive a
  grep.

**The gate itself ran clean on everything this cycle owns — and, unusually for this tree, on
everything else too.** `uv run pytest --no-cov` returned **`6085 passed, 40 skipped in 475.33s`, zero
failures and zero errors**, despite executing ~195 uncommitted paths belonging to two concurrent
maintainer sessions; there is no failure to attribute and nothing escalated from that row.
`manage.py check`, `makemigrations --check --dry-run`, `ruff format --check .`, `ruff check .`, and
`git diff --check` all pass **over the whole tree**, ~195 dirty paths included.
`check_spec_glossary` reads `OK: 19 terms`, the figure R2's single CSV row moved.
`check_trailing_commas --check` exits 1 on exactly two rows, **zero of them in this cycle's paths**:
one is an agent memory file under a gitignored directory that is not in the repository at all, and the
other is a concurrent session's uncommitted edit to `utils/inputs.py`, proven not to be a baseline
defect because the `HEAD` blob of that file passes the same check. Floor-verification scope was `none`,
the declaration re-verified as correct, and no floor venv was built. The staged-anchor sweep finds
nothing under `TODO(spec-015` or `TODO-*-015` anywhere in the tree, board files included.

**What remains open is eight catalogued items, none of them a code defect.** The load-bearing one is
the half-closed F13: the terms CSV is complete at 19 rows, but `DONE-015-0.0.5` still renders 18
glossary terms until `import_spec_terms` and the two kanban regenerates run — database work this cycle
was barred from, carried in the catalog with its exact recipe. Two more (items 2 and 3) are the same
citation-hygiene defect class in the same two dirty files and should be batched into whichever work
package legitimately opens them. The remaining five are a missing A/B test row, a stale test docstring,
two deliberately-untouched non-unique anchors, and two spec-text looseness items.

### Final status

`final-accepted`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

[spec-015]: ../SPECS/spec-015-relay_interfaces-0_0_5.md
[spec-015-rationale]: ../SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md

<!-- docs/builder/ -->

[artifact]: ARTIFACT.md
[build-015]: build-015-relay_interfaces-0_0_5.md
[build-md]: BUILD.md
[worker-0]: worker-0.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
