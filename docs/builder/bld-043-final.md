# Build: Final test-run gate (spec-043 post-ship reconciliation cycle)

Spec reference: `docs/SPECS/spec-043-test_client-0_0_14.md` (archived; `Status:` line 72)
Build plan: `docs/builder/build-043-test_client-0_0_14.md`
Cohorts gated: A (spec + rationale), B (code verification), C (guard respell + contract text), D (nine live conversions), plus the cross-cohort integration pass
Status: final-accepted

## Plan (Worker 1)

The last pass before the maintainer takes the tree. `BUILD.md` `## Final test-run
gate` is deliberately narrow: four commands plus floor verification, each
recorded with its pass/fail **and the command as run**, plus the
`### Deferred work catalog` this document is the only author of.

### Required reading, completed

`AGENTS.md`, `START.md`, `docs/builder/BUILD.md` (`## Final test-run gate`,
`## Floor verification`, `## Claims are proven mechanically`, `## Coverage is the
maintainer's gate, not a worker's tool`, `## Severity definitions`,
`## Cross-slice integration pass`), `docs/builder/ARTIFACT.md`,
`docs/builder/worker-1.md`, the build plan in full (including
`## Final-gate scoping (recorded ahead of the gate)`, written at plan time for
this pass), `docs/builder/bld-043-integration.md`, all four cohort artifacts
(`bld-043-review-1..4`) and all three escalations
(`bld-043-escalation-1..3`), and `docs/builder/worker-memory/043-worker-1.md`.
`043-worker-2.md` / `043-worker-3.md` were not read.

### Spec status-line re-verification (every Worker 1 spawn)

`docs/SPECS/spec-043-test_client-0_0_14.md` line 72 reads
`Status: **COMPLETE (card DONE-043-0.0.14) — all three slices built and the
card-wrap landed; the 0.0.14 version release rode the joint cut.**` That still
describes the build's state: this is a post-ship reconciliation cycle, and
nothing in it shipped contract. The opener's joint-cut sentence and the
`0.0.14`-ownership paragraph above the status line are unchanged and still true.
**No edit owed; none made.** See `### Spec changes made (Worker 1 only)`.

### The three authors in this tree, and how a red line is read

Three sources are interleaved here: this cycle, a live concurrent **spec-050**
session, and the maintainer's own baseline-dirty files. Per `START.md` a failure
is attributed **by diff content** before being called a regression, and
`BUILD.md` `## Claims are proven mechanically` makes "pre-existing at HEAD" not
worker-verifiable in a dirty tree — the evidence is recorded and escalated, never
"fixed" here and never routed to a cohort that does not own the code. Nothing in
this pass reverted, deleted, stashed, checked out, restored, or worktree'd
anything. No `git stash`, no `checkout --`, no `restore`, no worktree.

**`main` moved under this cycle.** HEAD at the gate is `96b9e047`
(2026-09-12 13:16). The session-start snapshot named `aadca5a2`;
`git merge-base --is-ancestor aadca5a2 HEAD` succeeds, so this is a
fast-forward, not a history rewrite (`START.md` "Other session may rewrite main
history … Prove your commit landed"). The commits in between are the
maintainer's own doc/test reconciliation and a board render; **none touches a
file this cycle authored**, and every one of this cycle's hunks is still in the
working tree, uncommitted — proved per file in
`## What the maintainer is receiving`.

---

## The gate

Every command below was run from the repo root in the shared `.venv`, in the
order `BUILD.md` gives. No `--cov*` flag was passed anywhere in this pass and no
coverage figure was read (`BUILD.md` `## Coverage is the maintainer's gate, not a
worker's tool`); `--no-cov` opts out entirely and is required because
`pytest.ini`'s `addopts` auto-applies `--cov`.

| # | Command as run | Result |
| --- | --- | --- |
| 1 | `uv run pytest --no-cov` | **PASS**, exit 0 |
| 2a | `uv run python examples/fakeshop/manage.py check` | **PASS**, exit 0 |
| 2b | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS**, exit 0 |
| 3a | `uv run ruff format --check .` | **PASS**, exit 0 |
| 3b | `uv run ruff check .` | **PASS**, exit 0 |
| 3c | `git diff --check` | **PASS**, exit 0 |
| 4 | Floor verification | **`none` declared, `none` owed** — see below |

**Zero failures. Zero collection or setup errors. No re-runs: the full sweep was
run exactly once and is recorded from that one run**, per the instruction not to
re-run a slow sweep to "check" a flake without saying so.

### 1. `uv run pytest --no-cov`

```
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
django: version: 6.1, settings: config.test_settings (from ini)
rootdir: /Users/riordenweber/projects/django-strawberry-framework
configfile: pytest.ini
testpaths: tests, examples/fakeshop/tests, examples/fakeshop/test_query, examples/fakeshop/apps
plugins: cov-7.1.0, xdist-3.8.0, asyncio-1.4.0, Faker-40.36.0, django-4.14.0
8 workers [7813 items]
...
================= 7775 passed, 40 skipped in 88.54s (0:01:28) ==================
```

Exit 0. All four test trees swept in one invocation (`testpaths` above covers
`tests/`, `examples/fakeshop/tests/`, `examples/fakeshop/test_query/`,
`examples/fakeshop/apps/`). `FAILED` and `ERROR` occur **0 times** in the whole
output, counted as occurrences over the captured log rather than read off the
summary line.

**Two instruments on the same run, and the small disagreement stated rather than
reconciled away.** The per-worker progress stream carries 7775 `PASSED` + 38
`SKIPPED` = 7813, exactly the collected item count; the summary line reports 40
skipped. The two-node difference is collection-time skipping that emits no
progress line (the sharded / Postgres-gated modules). The load-bearing fact is
the same on both readings and on the exit code: **0 failed, 0 errored.** The
difference is recorded because a number that does not reconcile is worth a
sentence, not a silent rounding.

**No attribution work was owed.** The plan's `## Final-gate scoping` pre-recorded
the handling for a failure belonging to the concurrent session; no row failed, so
nothing was attributed, recorded-and-escalated, or routed. In particular the
plan's `## Concurrent-session files that will reach the final gate` item 2 — the
untracked `print()`-based probe `examples/fakeshop/test_query/test_zz_probe_api.py`
that would have been collected by this sweep — **did not appear**: the concurrent
session removed its own scratch, the integration pass verified that, and this
gate re-confirms it (`ls` reports no such file; the file appears in neither
`git status` nor the sweep's collected 7813). It was not deleted by this cycle.

### 2. Django consistency checks against the example project

```
$ uv run python examples/fakeshop/manage.py check
System check identified no issues (0 silenced).

$ uv run python examples/fakeshop/manage.py makemigrations --check --dry-run
No changes detected
```

Both exit 0. No model / admin / url-config drift. Expected: this cycle changed
one predicate, one docstring, and test-tier call sites — no model, admin, or
URLconf was opened by any cohort.

### 3. The lint / format / diff gate — read-only, never `--fix`

```
$ uv run ruff format --check .
444 files already formatted                                    # exit 0
$ uv run ruff check .
All checks passed!                                             # exit 0
$ git diff --check                                             # exit 0, no output
```

`ruff format --check` emits its standing `COM812`-vs-formatter advisory; that is
configuration noise, present at HEAD, not a finding, and the exit code is 0.

**All three sweep the whole tree, so the separation matters:** `ruff` read all
444 formattable files. Of the 21 dirty `.py` files it covered, **8** are this
cycle's, **12** the concurrent spec-050 session's, and **1**
(`examples/fakeshop/apps/kanban/tests/test_mutations.py`) the maintainer's
baseline-dirty — separated by diff content, enumerated in
`## What the maintainer is receiving`. Nothing was found in any of them. Had a whitespace error or conflict marker existed in a
concurrent-session file it would have been recorded and attributed here, never
fixed; none exists, so there is nothing to attribute. **Neither `--fix` nor
`ruff format` (write mode) was run in this pass**, and
`scripts/check_trailing_commas.py` was not run at all — its repo-wide default
auto-fixes and would rewrite the concurrent session's files.

**`git diff --check`'s blind spot, closed on a second instrument.** It compares
the working tree against the index and therefore cannot see **untracked** files —
which is every artifact this cycle created. Re-run to cover them:
`git diff --check HEAD` (exit 0), `git diff --cached --check` (exit 0, and the
index is empty), and a per-file
`git diff --no-index --check /dev/null <path>` over every untracked path from
`git ls-files --others --exclude-standard` — **10** examined at the time of the
run, 0 with whitespace errors or conflict markers. (The population is 11 once
this file lands; it is written by the same hand and under the same rules.)

### 4. Floor verification

**`No floor-verification scope declared.`**

The build plan's preamble declares floor-verification scope **`none`**, on the
module's position rather than on "no executable code changed": no cohort changes
a Django / Strawberry / channels integration seam. The clients *call*
`django.test.Client` and subclass `strawberry.test.BaseGraphQLTestClient`, but
this cycle's fence forbade changing that seam's shape — A edits spec prose, B is
read-only, C's two production hunks are one predicate inside the package's own
owned builder plus one docstring, and D's hunks are test-file call sites.

**The declaration was honored.** The cross-cohort integration pass recorded the
same `none` after reading the whole diff at once, and Cohort B independently
confirmed it from the code side: no branch in `testing/client.py` is gated on
interpreter or framework version, so the Python-3.10 divergence class
(`SpooledTemporaryFile.seekable`, and similar) has nothing to bite on here. **No
floor venv was built, and the shared `.venv` was not mutated** — this pass
installed nothing.

The floor numbers, quoted from `BUILD.md` `## Floor verification` (the single
canonical statement) and not from memory: Django **5.2.16**, Python **3.10**,
strawberry-graphql **0.316.0**. The plan's one recorded floor caveat — finding
**F6**, the spec naming `strawberry-graphql 0.262.0` as the pinned floor against
that section's `0.316.0` — was discharged by Cohort A as a **text** correction:
the spec now names `pyproject.toml` and that section instead of restating a
number. A text correction owes no floor run, and the floor-*presence* question it
gated is separately settled (`client.py` imports
`strawberry.test.BaseGraphQLTestClient` and `strawberry.test.client.Response`,
and the focused suite is green).

---

## Deferred work catalog

The next spec author's reading list. Built by walking every per-cohort and
integration artifact's `### Notes for Worker 1 (spec reconciliation)`,
`### What looks solid`, `### Dispositions`, and per-cohort deferral sections, and
by re-deriving the integration pass's consolidated list rather than inheriting it
(`START.md` "Round's self-reported deferral = claim"). **Every item carries a
named owner** — `AGENTS.md` `## Past mistakes`: an item routed forward without a
named owner dies.

**Nine items, as the integration pass consolidated them: seven deferrals below,
plus the two maintainer decisions recorded separately after them** — those two
are carried *out* of this cycle for a decision, not queued as backlog, and are
kept under their own heading so no reader files them as either.

Each was re-verified against the tree at gate time; where re-verification changed
or extended what the integration pass recorded, that is said in the bullet.

1. **No gate fails a raw `.post(` / `.generic(` on a Django client in
   `examples/fakeshop/test_query/` that carries no exemption declaration.**
   Source: `bld-043-escalation-3-exemption_declarations.md` `## Recommendation`
   item 5; `bld-043-review-3` catalog item 3; `bld-043-review-4`
   `### Deferred work for the final gate`; integration item 3. Licensing: none —
   the rule is the spec's (Decision 11) and has never had a gate, which is why
   five files drifted in two months (`START.md` "Rule w/o gate rots", whose
   root-cause fix is the gate, not the sites). Re-verified here: nothing in
   `scripts/` or `.pre-commit-config.yaml` inspects live-tier HTTP call shapes.
   Out of this cycle's fence in both halves — a `scripts/` + hook change plus a
   KANBAN DB edit. **Owner: maintainer**, to home on a card; escalation 3
   nominates `TODO-ALPHA-053-0.0.15`, which already owns `.pre-commit-config.yaml`
   / CI changes and carries live-tier debt. **Homed 2026-09-13** on
   `TODO-ALPHA-053-0.0.15` as a scope bullet (board-DB `CardItem`, scope order 67;
   `KANBAN.md` / `KANBAN.html` regenerated) after the maintainer lifted the fence.

2. **Undeclared raw-request posture in three live files, pre-existing at HEAD**
   (the integration pass and this file's first version said four — see the
   post-gate correction at the end of this item).
   Source: `bld-043-review-4` `### Notes for Worker 1` item 4 and its deferral
   list; integration item 4. `test_transport_api.py`, `test_auth_api.py`,
   `test_debug_toolbar_api.py`, `test_list_field_async_api.py` retain raw client
   requests whose declaration names a different regime or nothing at all —
   re-verified at gate time: `test_transport_api.py` and `test_auth_api.py`
   declare the **`graphql_client.py` raw-envelope** exemption (the right
   declaration for a suite whose subject *is* the envelope, but not a spec-043
   one), `test_list_field_async_api.py` declares the **sync-only** exemption, and
   `test_debug_toolbar_api.py` declares **nothing** — but see below: it has no raw
   post at all. Only `test_products_api.py`'s three sites carry a comment naming
   spec-043. Same
   population as item 1, spanning files in no cohort's write set. Named
   explicitly so a future DoD sentence is not written as though it were
   discharged — which is exactly why Cohort C rewrote the DoD as a **rule over
   the switchover's own population** rather than a tree census any file could
   falsify on its own date. **Owner: maintainer**, with item 1's gate.
   **Post-gate correction, 2026-09-13:** `test_debug_toolbar_api.py` carries
   **zero** `.post(` / `.generic(` calls; its five raw calls are
   `.get("/graphql/", HTTP_ACCEPT="text/html")` GraphiQL and toolbar-panel fetches,
   not GraphQL operations, so the file sits outside Decision 11's population and
   outside item 1's gate. It entered this item through escalation 3's separate
   `.get(`-on-a-client census being folded into the `.post(` item. Population is
   three files. **Homed 2026-09-13** on `TODO-ALPHA-053-0.0.15`, in item 1's
   bullet.

3. **`examples/fakeshop/test_query/test_list_field_async_api.py`'s conversion.**
   Source: escalation 3 `## Recommendation` item 4 and its row-10 analysis;
   `bld-043-review-4` deferral list; integration item 5. One undeclared raw async
   post survives there (`AsyncClient()`, re-verified at gate time). Excluded from
   this cycle by the applied ownership partition and by `AGENTS.md` rule 34 — the
   file is the concurrent spec-050 cycle's, appears in five of its artifacts, and
   its last three commits are that cycle's. **The spec text as now written needs
   no amendment when it lands** (that is what item 2's rule-not-census rewrite
   bought). Escalation 3 has a drafted replacement docstring paragraph on disk for
   whoever converts it, so the wording does not have to be re-derived.
   **Owner: the concurrent spec-050 cycle.**

4. **Escalation 2's two optional endpoint rows — absent by decision, not by
   omission.** Source: `bld-043-escalation-2-endpoint_validation.md`;
   `bld-043-review-3` `### Dispositions` and catalog item 5; integration item 6.
   Both would make the restated endpoint claim mechanically failable: (a) a
   package-tier row in `tests/base/test_conf.py` asserting
   `conf.py::testing_endpoint_setting` returns a non-`str` verbatim, and (b) a
   live parametrization of the wrong-endpoint row over `None`. Neither landed;
   both are recorded durably in the rationale under Decision 7 as
   considered-and-not-taken **with the reason** (the claim they would pin is about
   *Django's own* `str()` coercion, already established by reading every cached
   wheel across `5.2.0` → `6.1.0`), so a later pass knows they are absent by
   decision. **The integration pass's bullet named only (a); (b) is named here so
   the pair is not split** — it sits in Cohort C's own live file and is the half a
   one-line summary would strand. `tests/base/` may grow rows but no files
   (`AGENTS.md`). **Owner for (a): whichever card next opens
   `tests/base/test_conf.py`. (b) needs no owner** — it was rejected on evidence,
   and the rationale is its record. **(a) homed 2026-09-13** on
   `TODO-BETA-072-0.1.8` (scope order 11): no card opens `test_conf.py`, and that
   card already carries missing-pin rows of the same shape.

5. **`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` carries a count
   this cycle falsified.** Source: `bld-043-review-1`
   `### Notes for Worker 1 / Worker 0` item 1; integration item 7. Its line 35
   states "three sentences in `spec-043` citing 'spec-042 Revision 8' by name".
   Re-measured at gate time on the shortest distinctive token: **0** occurrences
   in the spec and **1** in the spec-043 rationale. The claim's substance survives
   — the citations found the destination that same sentence predicted — its
   arithmetic does not. Non-writable this cycle: the fence covers only spec-043's
   own companions. **Owner: maintainer.** **Homed 2026-09-13** on
   `TODO-ALPHA-056-0.0.17` (scope order 95), beside its `spec-012` rationale twin.

6. **Two concurrent cohorts shared the three
   `docs/builder/worker-memory/043-worker-{1,2,3}.md` files.** Source:
   `bld-043-review-3` catalog item 6; build plan `## Items Cohort D routed to
   Worker 0` item 2; integration item 8. Not a partition defect — `BUILD.md`
   `### Worker memory` scopes the notebook **per role**, not per cohort — but it
   made the ~50-line consolidation cap unsafe (consolidating would clobber a
   concurrent pass's entry, and nearly did: Cohort C's planning entry landed
   between Cohort D's planner's read and its write), and it makes role memory a
   real cross-cohort channel — the one place information moves between concurrent
   cohorts without passing through an artifact. Both cohorts appended rather than
   consolidating, which is the right handling. **Owner: Worker 0**, for the next
   partition's memory-stem naming.

7. **The cycle's instrument failures, for the closeout retrospective.** Source:
   build plan `## The cycle's instrument failures` and `## Instrument failure,
   continued`; integration item 9. Consolidated in
   `## The cycle's instrument failures, consolidated` below, where the count is
   re-derived by counting members rather than inherited from a headline.
   **Owner: Worker 0's closeout job**, after the maintainer commits.

### Maintainer decisions carried out of this cycle — not backlog

Two items reach the maintainer as **decisions to take**, not work queued behind a
card. They are the last two of the integration pass's nine; kept apart here so a
reader scanning the catalog does not file a pending contract choice as debt.

- **The async live-tier post helper — a contract decision, escalated, not a
  deferral on a trigger.** Source: `bld-043-review-4`
  `### The async-helper deferral — escalated to Worker 0, not decided here`;
  build plan `## Escalation pending: the async-helper extraction`; integration
  item 2. Five near-identical `AsyncTestClient().query(...)` bodies now sit across
  four live modules, with a sixth unconverted raw post in the concurrently-owned
  `test_list_field_async_api.py` (all six re-verified at gate time — and a
  **seventh** the census missed, corrected 2026-09-13: a committed
  `AsyncTestClient()` + `await client.query(...)` site at HEAD in
  `test_kanban_mutations_api.py`, a fifth module; it is a native async test under
  `async with client.login(user)`, not the five-near-copy shape, so the DRY count
  of near-copies stands at five while "four modules" does not). Cohort D's
  custodian **retired** its own plan's "defer until a sixth async site" trigger on
  finding the sixth already existed the day it was written — a trigger that cannot
  fire is worse than none — kept the DRY reading, and escalated the extraction
  itself. Correctly: extracting a shared async post helper **reverses**
  `examples/fakeshop/graphql_client.py`'s stated sync-only contract, the live-tier
  README's `Async` bullet, and `AGENTS.md`'s rule that async suites owe a stated
  exemption from `graphql_client.py`. That is a contract choice, not a worker's
  (`BUILD.md` `### Contract-level findings are escalated as maintainer decisions
  before dispatch`). Both options and their costs are on disk in
  `bld-043-review-4-live_conversion.md`. **It blocks nothing** — the sixth site is
  the concurrent cycle's file and out of bounds either way.
  **Owner: maintainer**, to decide and then home (nominee
  `TODO-ALPHA-053-0.0.15`). **Homed 2026-09-13** on `TODO-ALPHA-053-0.0.15`
  (scope order 68) as a decision bullet carrying both options' location.

- **The falsified live-tier `README.md` `Async` bullet — the cycle's one
  genuinely undischargeable item.** Source: `bld-043-review-4` Plan note 1, build
  report note 2, review Low 3, and `### Notes for Worker 1` item 5 (which carries
  the corrected replacement wording); `bld-043-review-3` catalog item 1; build
  plan `## Items Cohort D routed to Worker 0` item 1; integration item 1.
  `examples/fakeshop/test_query/README.md` **line 918** names
  `django.test.AsyncClient` and a helper exemption for *both*
  `test_list_field_async_api.py` and `test_relations_async_api.py`; after D7 the
  second drives `AsyncTestClient` and declares no exemption, and the bullet names
  neither `test_products_visibility_api.py` nor the other converted files.
  **Outside the maintainer's own fence in both halves:** the file is a `.md`, and
  homing it on a card needs a KANBAN DB edit the same fence excludes. Corrected
  replacement wording is on disk — and Cohort D's custodian **rejected** Worker
  3's first recommended wording, which would have falsified the half of the bullet
  that is still accurate (`test_list_field_async_api.py` really does still drive
  `AsyncClient` and really does still declare the sync-only exemption).
  **Owner: maintainer.** **Homed 2026-09-13** in the same
  `TODO-ALPHA-053-0.0.15` bullet as the async-helper decision, because the
  bullet's correct text depends on that decision; the bullet names
  `TODO-ALPHA-056-0.0.17` as the fallback home if the decision is "no helper".

  **Re-verified at gate time, with one thing the integration pass could not have
  seen:** that file was clean when Cohort C and the integration pass checked it,
  and it is **now dirty** — `git diff` shows two suite-map row descriptions
  rewritten for `test_products_visibility_api.py` and `test_keyset_api.py`,
  subject matter squarely the concurrent spec-050 session's planner and keyset
  work. **Line 918 is untouched and the bullet is still falsified.** Recorded so
  the maintainer does not read that file's appearance in the dirty list as this
  cycle discharging the item, or as this cycle having edited a file outside its
  fence. It did neither.

---

## The cycle's instrument failures, consolidated

Recorded here because nothing else will, and because they are this cycle's most
transferable output: **every one was caught only by a second instrument**, and
several were committed *inside* a section whose own subject was measurement.

The integration pass's item 9 says "Nine now" and lists nine. Counting the
members rather than trusting the headline — this cycle's own repeated lesson, and
`BUILD.md`'s named failure — the population is **eleven**: the nine below, plus
**two the numbered list drops**, marked `†`. Both are real, both are already
written down somewhere in the cycle, and both fall out of every published count.

1. **Worker 0's F3 dispatch table graded prose with the code's vocabulary.** It
   asserted two of F3's six behaviour families were unlanded on the strength of
   `grep -c 'list, tuple'` and `grep -c 'unreadable'` returning 0 against the
   spec. Both were already landed — the spec read "both lists and tuples" and "an
   array whose length cannot be read", which is how a contract *should* be written
   and is exactly what those greps cannot see. `BUILD.md`'s named failure,
   committed by the dispatcher, in a table handed to a worker as fact. Caught only
   because the dispatch also said to re-derive.
2. **A pre-flight gate reading went stale inside its own cycle.** Pre-flight
   recorded `check_spec_glossary` → `OK: 22 terms`; by the time the recovery agent
   inherited it, a partial pass had moved spec text and the gate was **failing**.
   A gate result is evidence for the tree that produced it.
3. **Cohort B's `.post(`-blind live-tier census** missed a
   `client.generic("POST", ...)` site — a textual sweep over one spelling of a
   population with several.
4. **The same census counted a ninth *file* outside its own stated population**,
   found by escalation 3 rebuilding the census AST-first from `os.listdir` with an
   asserted population size.
5. **Cohort D's planner's live node count moved under its author.** The concurrent
   spec-050 session appended two rows to `test_products_visibility_api.py`
   mid-pass (8 → 10 nodes, four-file total 85 → 87). `START.md`'s self-falsifying
   instrument in its purest form — a live count of a population the counter is
   editing, in a tree a second session is also editing. The fix was to instruct
   the builder to verify "post-edit count equals its own pre-edit baseline", never
   to match a published number. Its sibling: "84 nodes" was a count of `def test_`
   lines where a node count is `--collect-only` output; the two differ silently
   (85, because one row is parametrized).
6. **A `variables={}` census blind to a positional argument.** It swept keyword
   spellings and reported 0 occurrences; the one real site passes it positionally.
7. **"15 callers" that is 17** — the count of a None-passing *subset* promoted to
   the count of the population.
8. **"Two helpers forward under `is not None`" — there is one.** Found by the
   paragraph's own author after the review had already corrected 6 and 7 in it:
   three published figures in one paragraph, all three wrong, under the headline
   "measured not assumed". A reviewer's finding list is a sample of a paragraph's
   defects, not its census.
9. **Cohort D's `### Notes for Worker 1` item 7 premise** ("D8 is the first live
   row driving `TestClient._assert_file_placeholders`") — false: an AST sweep of
   all 26 `files=` call sites in both test trees found three earlier live drivers,
   all clean at HEAD. Its *conclusion* survives and gets stronger. It was also the
   one Cohort D note that Cohort C's "discharged item by item" list did not name,
   which is the tell: a discharge list that skips an item is often skipping the one
   whose premise did not hold.

`†` 10. **Cohort C's enumeration, built expressly so the deferred pass "cannot
miss one", had three holes** — and the reviewer found only one of them. Re-deriving
the population from scratch turned up the Test-plan/DoD `retained raw client.post`
pair (making the exemption family four sites, not two) and — found by no pass —
`## Test plan` scenario 8 describing `_RecordingTestClient`, the double the same
cohort **deleted**, as the current mechanism. The hole no vocabulary sweep could
reach was a *mechanism description*: a deletion's stranded sites are described,
not named. Treat a reviewer's "your list has a hole" as a verdict on the
**instrument**, and re-derive the whole population rather than patching the named
line. Named in the integration pass's item 9 prose but standing outside its count.

`†` 11. **A green `git status` is not proof a crashed proof-runner left nothing
behind.** It happened to be true, but what established it was a mutation-marker
sweep plus three independent byte-identity instruments — not the dirty list.
Recorded in the build plan's own `## The cycle's instrument failures` as item 3,
then silently dropped when that section was renumbered to five.

`†` 12. **Post-gate, 2026-09-13: catalog item 2's four-file population was
three.** `test_debug_toolbar_api.py` has no raw post; escalation 3's `.get(`
census (23 sites, 4 files) was folded into the `.post(` / `.generic(` item by
file name, and every later pass inherited the file list without re-running the
grep it was built from. Caught by re-grepping `.post(\|.generic(` per file
before homing.

`†` 13. **Post-gate, 2026-09-13: "five async bodies across four live modules"
undercounted the modules.** `test_kanban_mutations_api.py` holds a committed
`AsyncTestClient()` site at HEAD that no cohort's census reached, because every
census was run over the four files Cohort D was converting. The near-copy count
(five) survives; the module count and the "sixth site is the only other one"
framing do not. Caught by `grep -c 'AsyncTestClient()'` over the whole directory
rather than the write set.

With 12 and 13 the population is **thirteen**.

**The shape they share.** Six of the eleven (1, 3, 4, 5, 6, 7) are a *sample of a
claim's vocabulary* mistaken for its *population*; three (2, 5, 11) are a reading
that was true when taken and false when used; and the two most expensive to catch
(9, 10) are false *premises* and *descriptions* rather than false facts — which is
why the integration pass, the only pass that reads the whole diff at once, is
where they surfaced. A further pattern worth carrying: `START.md`'s partial-claim
residual fired repeatedly this cycle — a recommended replacement sentence was
itself the defect on **three** separate occasions, at up to the third level down
(Worker 3's fix to Worker 2's text, corrected by Worker 1). `BUILD.md`'s "a
prescribed fix is a hypothesis, never an instruction" held every time it was
tested.

---

## What the maintainer is receiving

**Nothing is committed.** `git diff --cached --name-status` is empty; the index
holds nothing. No worker in this cycle committed, staged, branched, or pushed.
HEAD is `96b9e047`.

Attribution is by **diff content**, not by "files my cohorts touched"
(`START.md`), and was re-derived at gate time rather than inherited from the
integration pass's table.

### This cycle's work — 9 modified tracked files, 11 new untracked files

Counted at gate time from `git status --short`: 9 of the 31 modified tracked
paths are this cycle's, and all 11 untracked paths are (the retroactive rationale
companion plus the 10 builder artifacts, this file included).

| Path | Cohort | What is in the diff |
| --- | --- | --- |
| `django_strawberry_framework/testing/client.py` | C | one hunk: `_build_body`'s guard predicate `if not variables:` → `if "variables" not in body:`, message unchanged, comment restating the invariant |
| `django_strawberry_framework/conf.py` | C | one hunk: `testing_endpoint_setting`'s docstring; body untouched |
| `tests/testing/test_client.py` | C | +14 node ids; `_RecordingTestClient` deleted |
| `examples/fakeshop/test_query/test_client_api.py` | C | probe marker header + two assertions |
| `examples/fakeshop/test_query/test_error_policy_api.py` | D | conversions |
| `examples/fakeshop/test_query/test_relations_async_api.py` | D | conversions |
| `examples/fakeshop/test_query/test_resource_policy_api.py` | D | conversions |
| `examples/fakeshop/test_query/test_products_visibility_api.py` | **MIXED** | D's four conversion hunks **+** the concurrent spec-050 session's trailing append (`_PLANNED_LIST_QUERY`, `_hide_every_item_under_the_first_parent`, `_planned_item_names`, two `test_a_planned_*` rows) |
| `docs/SPECS/spec-043-test_client-0_0_14.md` | A, C, integration | the reconciliation itself |
| `docs/SPECS/appx/spec-043-test_client-0_0_14-rationale.md` | A, C, integration | **new file** (untracked), 64,014 bytes — the retroactive `-rationale.md` companion F1 owed |
| `docs/builder/build-043-*.md`, `bld-043-*.md` (10 untracked paths, this file included) | the cycle | plan, four cohort artifacts, three escalations, integration, final |

**Re-proved at gate time that the maintainer's own commits during this cycle did
not swallow any of it.** `main` advanced while the cycle ran, and two of those
commits (`18f2446f`, `8b3b9ae1`) touched live-tier files this cycle also edits.
Per file, counting the package test clients at HEAD versus the working tree:
`test_products_visibility_api.py` 0 → 6, `test_resource_policy_api.py` 0 → 4,
`test_error_policy_api.py` 0 → 5, `test_relations_async_api.py` 0 → 2. Every one
of Cohort D's conversions is still in the working tree and **uncommitted**;
`test_client_api.py` is 10 → 10 because Cohort C's hunks there are a marker header
and two assertions, not client call sites.

### The concurrent spec-050 session's — do not read as this cycle's

`django_strawberry_framework/connection.py`, `keyset.py`, `list_field.py`,
`optimizer/nested_planner.py`, `optimizer/walker.py`, `orders/sets.py`;
`tests/optimizer/test_walker.py`, `tests/orders/test_sets.py`,
`tests/test_connection.py`, `tests/test_keyset_connection.py`,
`tests/test_list_field.py`; `examples/fakeshop/test_query/test_keyset_api.py`;
the spec-050 append inside `test_products_visibility_api.py`;
`docs/spec-050-list_field_arguments-0_0_15.md`,
`docs/builder/build-050-list_field_arguments-0_0_15.md`, and the **unprefixed**
`docs/builder/bld-final.md`.

**New since the integration pass:** `examples/fakeshop/test_query/README.md` is
now dirty with that session's two suite-map row rewrites (see the second
maintainer-decision bullet above). Its `Async` bullet is untouched.

**Never edited, never reverted, never deleted by this cycle.** The unprefixed
`bld-final.md` and `bld-integration.md` are that cycle's filenames; this cycle's
are `bld-043-*`.

### Added 2026-09-13, after the maintainer lifted the board fence

`examples/fakeshop/db.sqlite3` (four new `CardItem` rows: cards 053 ×2, 056, 072
— the DB was already dirty with the concurrent session's rows, so carve per the
standing method), `KANBAN.md` (+4 lines) and `KANBAN.html` (data block), both
regenerated from the DB and `--check`-clean. `check_kanban_anchors` OK;
`check_citations --check` OK: 999 (171 in `KANBAN.md`, one new).

### Baseline-dirty, maintainer's own

`START.md`, `docs/GLOSSARY.md`, `docs/TREE.md`,
`examples/fakeshop/apps/kanban/tests/test_mutations.py`,
`examples/fakeshop/db.sqlite3`, and one further maintainer-owned review-input
`.md` under `docs/` (not named, per `AGENTS.md`). Untouched by every cohort — the
cycle's fence excluded all of them.

---

## Final verification (Worker 1)

- **Every gate command passed**, each recorded above with the command as run and
  its exit code. No failure, so nothing routed back to a cohort — which is the
  only thing a gate failure may do here (`BUILD.md` `## Final test-run gate`).
- **Coverage.** No `--cov*` flag in this pass; `--no-cov` on the one sweep; no
  coverage figure inspected or asserted (`BUILD.md` `## Coverage is the
  maintainer's gate, not a worker's tool`).
- **Floor verification.** Scope `none`, declared in the plan, confirmed honored by
  the integration pass and re-confirmed here. No venv built; the shared `.venv`
  was not mutated.
- **Every cohort artifact's `Status:` walked.** A `final-accepted`,
  B `revision-needed`, C `final-accepted`, D `final-accepted`, integration
  `final-accepted`. Nothing is left at `planned`, `built`, or `review-accepted`.
  B's `revision-needed` is the correct terminal value for a pure verification
  cohort whose whole product was a finding list — the build plan's
  `### Why Cohort B's box stays unticked` records why, and Cohorts C and D are
  where its findings were discharged. **Not a gate failure and not a blocker.**
- **Deferred work catalog written**, above: nine consolidated items — seven
  deferrals, each with a named owner, plus two maintainer decisions recorded
  under their own heading. Re-derived, not inherited; item 4 was extended to name
  the second of escalation 2's pair, which a one-line inheritance would have
  stranded. One item the cohorts routed forward needed **no** catalog entry and is
  recorded here instead so it is not looked for: Cohort B's
  `### Notes for Worker 1` item 7 (`client.py`'s import of
  `exceptions::_safe_arg_repr` absent from the spec's
  `## Helper-reuse obligations (DRY)`) **landed this cycle** — the spec now
  carries it as obligation **D5**, verified against `git show HEAD:` where the
  symbol occurs 0 times.
- **Public surface.** Unchanged, and the gate is not the first pass to say so:
  `git diff -- django_strawberry_framework/__init__.py` and
  `… testing/__init__.py` are both empty.
- **Nothing committed, nothing staged, no branch created or switched.**

### Summary

The spec-043 post-ship reconciliation cycle passes the final gate on every
command: the full sweep is green at **7775 passed, 40 skipped, 0 failed, 0
errored** across all four test trees, `manage.py check` and
`makemigrations --check --dry-run` report no drift, and `ruff format --check`,
`ruff check`, and `git diff --check` are all clean over the whole tree — this
cycle's eight dirty `.py` files, the concurrent spec-050 session's twelve, and
the maintainer's baseline-dirty ones alike, so no failure needed attributing and
none was fixed or routed. Floor verification was declared `none` at plan time on
the module's runtime position, confirmed honored by the integration pass, and no
floor venv was built. Nine items are catalogued for the next reader — seven
deferrals with named owners (the missing raw-post gate and the four files it
would have caught, both to the maintainer; the sixth async conversion to the
spec-050 cycle; escalation 2's two endpoint rows, absent by decision, one owned by
whichever card next opens `tests/base/test_conf.py`; a falsified count in
spec-042's rationale; the shared worker-memory stem to Worker 0; the instrument
failures to the closeout) — plus two maintainer decisions carried out of the
cycle: the async-helper extraction, which reverses `graphql_client.py`'s sync-only
contract, and the live-tier README's `Async` bullet, the cycle's one genuinely
undischargeable item, outside the maintainer's own fence as a `.md` and again as a
board edit. Eleven instrument failures are consolidated for the retrospective,
two of them dropped by every published count in the cycle. Nothing is committed;
HEAD is `96b9e047` and the index is empty.

Final status: **final-accepted**.

### Spec changes made (Worker 1 only)

**None.** This pass edited no spec and no rationale. The status line was
re-verified per `worker-1.md` `## Spec status-line re-verification (every Worker 1
spawn)` and still describes the build's state, so no edit was owed; the last
custodian edits are the integration pass's five label-only prose changes, recorded
in `bld-043-integration.md`. No checkbox was marked — only Worker 0 marks plan
checkboxes.
