# Build: Final test-run gate — spec-009 residual cycle (009)

Spec reference: `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` (archived; this cycle is a residual reconciliation, not a spec-slice build)
Build plan: [`build-009-rich_schema_architecture-0_0_4.md`][build-009]
Status: final-accepted

## Plan (Worker 1)

This is the cycle's last pass. Its contract is `BUILD.md` `## Final test-run gate`: run the six gate
commands, record each one's **real** result, confirm the one declared floor verification actually ran,
and author the `### Deferred work catalog`.

### Dispatched findings checklist

The gate has no findings cohort. Its obligations are the gate's own, one box each.

- [x] `uv run pytest --no-cov` run and its real result recorded
- [x] `uv run python examples/fakeshop/manage.py check` run and recorded
- [x] `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` run and recorded
- [x] `uv run ruff format --check .` run and recorded (never `--fix`)
- [x] `uv run ruff check .` run and recorded (never `--fix`)
- [x] `git diff --check` run and recorded
- [x] Every failure attributed mechanically — file named, ownership proved against pristine `HEAD`, never by `git status` alone and never by mtime
- [x] Floor-verification backstop: confirm R1c's declared floor run happened and is recorded
- [x] `### Deferred work catalog` authored, R4's assembled input consumed and R4's own finds folded in
- [x] `### Maintainer hand-off` separating the concurrent-session breakage from the mixed DB/board diff

### Baseline exception, as the plan records it

[`build-009-rich_schema_architecture-0_0_4.md`][build-009] `## Baseline-dirty out-of-scope files`
carries a pre-flight baseline exception for exactly this gate. Every command below reads the **whole
tree**, and this tree carries a concurrent package-source session, a REVIEW cycle, a DRY cycle, a
concurrent `spec-010` residual cycle and a concurrent `spec-014` residual cycle. **A failure
attributable to a file this cycle never wrote does not block `final-accepted` and does not route back
through a residual item's loop; it is reported to the maintainer.**

The exception governs what a result **blocks**, never whether it is recorded honestly. Every command's
real result is below, and every failure carries its attribution work.

**This cycle's writable set, enumerated** — the population every attribution below is tested against:

| Path | Item | What this cycle wrote |
|---|---|---|
| `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` | R1, R1b | the six scrubs, Group B reconciliation, whole-spec clause sweep |
| `docs/SPECS/appx/spec-009-…-rationale.md` | R1, R1b, R4 | appended reasoning; one clause corrected by R4 |
| `docs/SPECS/spec-028-orders-0_0_8.md` | R2 | `### Decision 12` and its in-file echo sites |
| `docs/SPECS/spec-054-fieldset-0_1_1.md` | R4 | one "Stale card reference" bullet, past-tensed |
| `tests/test_connection.py` | R1c | **one added test row** |
| `django_strawberry_framework/orders/sets.py` | R2 | **one docstring clause** |
| `django_strawberry_framework/orders/inputs.py` | R2 | **two sites** (docstring clause + the `del` comment below it) |
| `examples/fakeshop/db.sqlite3` | R3 | **two `CardItem.text` rows** on card `TODO-BETA-054-0.1.1` |
| `KANBAN.md`, `KANBAN.html` | R3 | regenerate output of those two rows |
| `docs/builder/bld-009-*.md`, `docs/builder/build-009-*.md` | all | cycle artifacts |

Nothing else. No other source file, test file, sibling spec, card, or generated doc.

---

## Gate run (Worker 1)

Environment, **as read rather than stated from memory** (`BUILD.md` `## Floor verification`):
`uv pip list` over the shared `.venv` → `django 6.1`, `strawberry-graphql 0.323.2`, `asgiref 3.11.1`,
`channels 4.3.2`, `django-filter 25.2`; `.venv/bin/python -V` → `Python 3.14.2`.

`HEAD` at the gate is **`1abba7a4`** ("Share column-less form and serializer relation annotation."). It
**moved during this cycle**: R4 recorded `6f8bf818`, and three package-source commits have landed since
(`bd7df65b`, `e473adf0`, `1abba7a4`). Re-derived here rather than trusted from the plan, per
`## Baseline-dirty out-of-scope files`. Tree dirty count at the gate: **196**.

### Command results

| # | Command | Result | Blocks `final-accepted`? |
|---|---|---|---|
| 1 | `uv run pytest --no-cov` | **FAIL** — `31 failed, 5857 passed, 40 skipped, 93 errors in 104.36s` | **No** — every failing node attributed to a concurrent session (below) |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).`, exit 0 | — |
| 3 | `… makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit 0 | — |
| 4 | `uv run ruff format --check .` | **PASS** — `423 files already formatted`, exit 0 | — |
| 5 | `uv run ruff check .` | **PASS** — `All checks passed!`, exit 0 | — |
| 6 | `git diff --check` | **PASS** — no output, exit 0 | — |

No `--cov`, `--cov-report`, or `--cov-config` was passed in any pass of this gate, and no line coverage
was inspected or asserted (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`).
`--no-cov` is carried because `pytest.ini`'s `addopts` auto-applies `--cov`.

### Command 1 — the `pytest` failure, attributed

**Two full sweeps were run.** The `FAILED` set was **identical across both** (31 nodes, same ids); the
`ERROR` count and the *files* it landed in **differed** — run 1: `104 errors`, run 2: `93 errors`, with
run 1 erroring in `test_error_policy_api.py` / `apps/kanban/tests/test_mutations.py` /
`test_debug_toolbar_api.py` and run 2 in `test_kanban_mutations_api.py` / `test_auth_api.py` /
`test_debug_extension_api.py`. That instability is itself diagnostic, and it is explained below. The
recorded run is run 2, saved in full to the session scratchpad.

**Single root cause, mechanically established.** `tests/types/test_relay_interfaces.py:1569` defines an
adversarial fixture: a `str` subclass whose `__format__` raises `RuntimeError("hostile model format")`,
monkeypatched over a model's `__name__`. It fails in two ways at once:

1. **Direct** — production code formats a model name through an f-string
   (`django_strawberry_framework/types/base.py::_validate_globalid_strategy`, and ~24 sibling f-strings
   on `meta.model.__name__` throughout `_validate_meta`), so the hostile `__format__` fires and every
   assertion in the fixture's own file explodes. This is the stable 31-row `FAILED` set.
2. **Leaked** — the monkeypatch **cannot be undone** on this interpreter:
   `TypeError: cannot delete '__name__' attribute of immutable type 'Category'` from
   `_pytest/monkeypatch.py::MonkeyPatch.undo`. The hostile name therefore **survives teardown and
   persists in the shared model for the rest of that xdist worker's session**, so every later test in
   that worker which formats a model name — schema reload, mutation input-type-name generation — errors
   out. Which tests land after the leak is decided by `pytest-randomly`'s shuffle, which is exactly why
   the two runs erred in different files.

**Attribution: NOT this cycle's, proved against pristine `HEAD`.** Per `BUILD.md`
`## Claims are proven mechanically`, `git show HEAD:<path>` into a scratch path **outside** the repo —
no `git stash`, `git checkout`, `git restore`, or `git worktree` was used anywhere in this gate.

- `git show HEAD:tests/types/test_relay_interfaces.py | grep -n 'hostile model format'` → **0
  occurrences**. `grep -n` on the working tree → **1 occurrence, at `:1569`**. **The fixture does not
  exist at `HEAD`.** Without it there is no monkeypatch, no leak, and no direct assertion — so the
  entire failure population is causally downstream of uncommitted lines.
- The five implicated files are all ` M` (uncommitted) and **none is in this cycle's writable set**:
  `django_strawberry_framework/types/base.py`, `django_strawberry_framework/relay.py`,
  `tests/types/test_relay_interfaces.py`, `tests/test_relay_node_field.py`, `tests/testing/test_relay.py`.
  All five sit in the plan's `## Baseline-dirty out-of-scope files` package-source group.
- **The population was enumerated, not grep-counted** (`## Method warning`). Every per-test report block
  in the `ERRORS` and `FAILURES` regions was split out and classified by content:
  **31 of 31 `FAILURES` blocks** and **41 of 41 `ERRORS` blocks** trace to `hostile model format` or to
  the `cannot delete '__name__'` undo failure. **Blocks not tracing to it: 0.** (41 report blocks cover
  93 error node ids; pytest groups repeated setup errors under shared headers. Blocks and node ids are
  reported separately rather than conflated.)

**Positive verification that this cycle's own work is green** — attribution is not only "not ours", it
is "ours passes":

- R1c's added row and its sync sibling:
  `uv run pytest tests/test_connection.py::test_async_execution_default_connection_async_get_queryset_raises_sync_misuse tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse --no-cov -p no:randomly`
  → **`2 passed in 5.98s`**.
- R2's touched module: `uv run pytest tests/orders/ --no-cov -p no:randomly` → **`141 passed in 7.17s`**.
- R1/R1b/R4 wrote Markdown only; R3 wrote two DB rows and their regenerate. None is executable.
- No commit swept this cycle's work: `git log -1` per writable path returns `f3c94642` (spec-009 and its
  rationale), `40e4754a` (spec-028), `947f7494` (spec-054), `567cc6d0` (`tests/test_connection.py`),
  `5851bb59` (`orders/sets.py`), `5d27a13b` (`orders/inputs.py`), `6f8bf818` (`KANBAN.md`,
  `KANBAN.html`, `db.sqlite3`) — every one predating this cycle's edits, each of which is still ` M` and
  unstaged. Proved with `git log` per path, **never with `git status` alone**.

**Disposition: does NOT block `final-accepted`.** It is squarely inside the plan's recorded baseline
exception, and it does not route back through any residual item's loop — no residual item owns any of
the five files. **It is reported to the maintainer** in `### Maintainer hand-off`. Per `AGENTS.md` rule
34 and the plan's standing instruction, **nothing was reverted, reformatted, or "fixed"**: the fixture
is a concurrent session's in-flight work, and the correct owner of the production-vs-fixture
reconciliation is that session, not this gate.

### Commands 4-6 — the lint/format/diff gate

All three pass on the whole tree. Nothing was run in write mode: no `ruff format .`, no
`ruff check --fix`, no formatter scoped or unscoped was applied to any file, this cycle's own included.

**The known concurrent-session lint blocker is now RESOLVED, and that is a measurement, not an
assumption.** `bld-009-r1c` recorded that `scripts/check_trailing_commas.py` would fail on
`tests/test_connection.py:1062` — a concurrent session's uncommitted single-line
`async def __call__(self, prefix, root, info):` inside `_Resolver`, which Worker 2 correctly refused to
auto-fix over another session's work. Re-measured at final state:
`grep -n 'async def __call__(self, prefix, root, info)' tests/test_connection.py` → **0 occurrences**;
the signature now stands exploded across `:1061-1066` in the required layout. **The concurrent session
fixed its own line.** The stale item is retired here rather than carried forward.

`scripts/check_trailing_commas.py --check` is **not** one of the six gate commands, but it was run
read-only since R1c had flagged it. It exits **1** on exactly **one** violation, and that violation is
**outside the repo's corpus entirely**:
`.claude/projects/…/memory/one-spec-owns-each-feature.md` — an agent memory file, **gitignored**
(`git check-ignore -v` → `.gitignore:170:.claude/`) and unknown to git
(`git ls-files --error-unmatch` → `did not match any file(s) known to git`). Not this cycle's, not any
cycle's, and not a repo source file. Recorded, not fixed.

## Floor verification — backstop confirmation

The plan declares floor scope `none` at its preamble line 10, with the reason stated: no item changes
package behavior at any version. **`### Maintainer decision 5` amends that declaration for R1c alone**,
because R1c's row exercises a Django/Strawberry async-execution seam.

**Worker 1's job here is to confirm it happened, not to own it.** It happened, and it is properly
recorded — a planned floor verification no pass ran would be grounds for `revision-needed`, and this is
not that case.

Read from [`bld-009-r1c-async_syncmisuse_test_row.md`][bld-r1c], which carries the run **twice**: Worker
2's `### Floor verification` (the declared owner) and Worker 3's independent reproduction.

- **Venv outside the repo**, at the session scratchpad path; built with an explicit `--python` on every
  install, per `BUILD.md` `### How to build the floor venv`.
- **Resolved versions recorded by that pass:** `django 5.2.16`, `strawberry-graphql 0.316.0`,
  `asgiref 3.12.1`, interpreter `Python 3.10.19` — matching `BUILD.md` `## Floor verification`'s
  canonical floor (Django 5.2.16 / Python 3.10 / strawberry-graphql 0.316.0) exactly.
- **Focused scope and result recorded:** the two node ids of `### Decision 5` and nothing wider →
  **`2 passed`** (Worker 2: `6.23s`; Worker 3's reproduction: `3.67s`).
- **The shared `.venv` was not mutated**, verified in that artifact by reading the shared environment
  rather than by asserting it.

**Backstop re-run performed here**, because the venv is still on disk and re-confirming cost nothing:
`uv pip list --python <venv>/bin/python` → `django 5.2.16`, `strawberry-graphql 0.316.0`,
`asgiref 3.12.1`; `<venv>/bin/python -V` → `Python 3.10.19`; the same two node ids with `--no-cov
-p no:randomly` → **`2 passed in 6.20s`**. Three independent runs, same result.

**The shared `.venv` was never mutated by this gate.** Read-only `uv pip list` only; every floor
invocation used `<venv>/bin/python` directly.

**No other floor scope is owed.** No other item touched a framework seam: R1, R1b, R2 and R4 are
Markdown-only, and R3's writes are two DB rows and a regenerate.

## Spec status-line re-verification

Per `worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`. `spec-009`'s header
lines were re-read at final state. The opener points at the rationale companion and enumerates the six
scrubbed mechanisms accurately; there is no falsified status line, no "not yet shipped" or "remains to
be" wording, and no reference to a deleted predecessor. **No spec edit was needed or made by this
pass.** This gate wrote exactly one file: this artifact.

## What the cycle established

Sufficient for the maintainer to review without rereading six artifacts.

**The load-bearing result is a negative: no correctness defect and no silent omission in shipped
source.** The layer-by-layer audit of `spec-009` against `django_strawberry_framework/` found that every
layer with a shipped subsystem is implemented **at or beyond** its spec text — the nested-connection
optimizer, the visibility-aware related filter branches, and the keyset cursor surface all exceed what
the spec asked for. Nothing was quietly dropped.

- **8 of 11 success criteria met.** The three unmet are each **carded for beta**, none silently dropped:
  full-text search (`TODO-BETA-055-0.1.2`), aggregate output on connections (`TODO-BETA-057-0.1.3`),
  field-level permission masking (`TODO-BETA-054-0.1.1`).
- **Six spec'd-but-never-built items adjudicated `DROP AND SCRUB` on parity grounds, and scrubbed.**
  `DjangoModelField`, `OptimizerStore` + Info-scoped callable hints, `get_strawberry_annotations`,
  `DjangoField(...)`, the `DjangoModelType` fallback, and `ASC_DISTINCT`/`DESC_DISTINCT` +
  `DISTINCT ON`. **Not six missed features**: five are upstream *internal mechanisms* whose consumer
  capability this package already delivers through a different grain, and one is a reference-only
  surface whose motivating problem shipped under a better design (the row-preserving `Min`/`Max`
  ordering). A card would have promised a capability that already exists — which is why the disposition
  is scrub-not-card.
- **The spec now reads as a usable contract rather than a museum piece.** Group B's falsified names and
  shapes were corrected in place: `AdvancedFilterSet` → `FilterSet`, `Meta.filter_fields` → `Meta.fields`,
  the node field's nullability, the `DjangoConnection` shape, the `Meta` example, the `Ordering`
  directions. Decision and Phase numbering was held stable so no sibling spec's heading anchor dangles.
- **The whole spec was swept clause-by-clause**, all 1,096 lines, not only the ~112 this cycle added
  (`### Maintainer decision 4`).
- **One coverage gap was closed with a real test rather than a card** (R1c): no permanent row pinned
  `async def get_queryset` → `SyncMisuseError` for a *default* `DjangoConnectionField` under
  `await schema.execute`. It now has one, with a failability proof and a floor run.
- **Every inbound reference the cycle falsified was fixed in the same cycle** — `spec-028`'s orphaned
  `DISTINCT ON` deferral, card 054's two stale references, and the two clauses those fixes falsified in
  the `spec-009` rationale and in `spec-054`. That standing instruction ("since we did not fix every
  inbound reference in the same change last time, do that now") is what drove three enumerated scope
  widenings, and the cycle stopped at the declared ceiling rather than arguing past it.

**The method lesson, recorded because it is the cycle's real signature.** The failure mode here was
never missed facts; it was **false descriptions of findings** — counts, denominators, populations, and
section pointers, each written correctly and falsified by the next revision. Eight such corrections were
themselves wrong, and ten grep-shape traps were catalogued. The durable rules: **for a population,
enumerate rather than grep-count; for occurrences, report occurrences and files separately; treat corpus
definition as an explicit parameter; describe by content, not by shape.** This gate's own attribution
work was done that way — 31 of 31 and 41 of 41 report blocks classified by content, not by a grep count.

## Deferred work catalog

The next spec author's reading list. `worker-1.md` makes Worker 1 its only author.

**Provenance.** [`bld-009-r4-docs_archive_audit.md`][bld-r4] carries an assembled
`### Deferred work catalog` that Worker 3 independently confirmed complete against **all five closed
artifacts**, having walked every `Notes for Worker 1`, `Recorded for the maintainer / R4`, escalation
and plan-decision block. That input is **consumed, not re-derived**. Because it is scoped to the five
*closed* artifacts, **R4's own finds sit outside it and are folded in here** — marked **[R4-new]** —
along with one item this gate measured.

### A. Cross-spec rot into `spec-010` (a concurrent cycle's file; read-only all cycle)

1. **`spec-010:8`** still lists "custom field classes" among what `spec-009` describes — exactly the
   `DjangoModelField` claim D1 scrubbed. Carried unrepaired for ten consecutive passes. Fix: drop the
   phrase; `spec-009` no longer describes it. — `bld-009-r1` `### Escalations carried forward`;
   `bld-009-r1b`.
2. **`spec-010:491`** still names `get_strawberry_annotations` as "the right helper for the day a stable
   consumer-override contract lands". That borrow was scrubbed as D3, and `spec-009` now states the
   opposite (provenance is solved structurally by the `consumer_*_fields` frozensets on
   `types/definition.py::DjangoTypeDefinition`). Fix: retire the sentence. — `bld-009-r1` (found at pass
   3), `bld-009-r1b`.
3. **`spec-010:67`** — the anchor into `spec-009` `### Layer 3: Finalization trigger` resolves and the
   claim holds, but the cited section no longer states the direction; the line also carries a
   near-verbatim twin of `spec-009`'s single-threaded-setup-window sentence. Right owner is `spec-010`,
   not this cycle. — `bld-009-r1`, `bld-009-r1b`.

### B. Board -> spec falsification

4. **[R4-new] `KANBAN.md:336`** asserts that `spec-009` `### Layer 3: Finalization trigger` *"still
   presents hybrid auto-finalization as the preferred direction"*. **Verified false**: that section now
   opens *"The trigger is the explicit consumer call, and nothing else."* and records the auto-trigger
   direction as **rejected** — landed at `f3c94642`, the **first** residual cycle, not this one. A live
   board→spec falsification, and the corpus direction `## R4 inherits` names. `KANBAN.md` is DB-backed,
   so the fix is an **ORM edit of the card item plus a regenerate**, never a hand-edit of the rendered
   file. The bullet's *disposition* half is still accurate — it prescribes exactly the residual cycle
   that has now run. Not fixed here: not this cycle's falsification, R3 closed the DB, and it would be a
   fourth unilateral widening past the declared ceiling. — `bld-009-r4` `### Recorded for the maintainer`
   item 1.

### C. Renumber residue — the 2026-07-30 card rotation

5. **[R4-new] `docs/SPECS/spec-034-permissions-0_0_10.md` carries 4 `TODO-BETA-046-0.1.1` citations**
   (`:14`, `:220`, `:224`, `:307`). Post-renumber, card 046 is `DONE-046-0.0.14` (transport); the live
   FieldSet owner is `TODO-BETA-054-0.1.1`. **New — no prior pass recorded these**, and no declared
   sweep covers them (`spec-054` Slice 4 owns only `apps/products/schema.py`'s 7). **The count is 4 and
   the disposition splits 3 + 1. Whichever sweep takes these MUST honour the split:**
   - **3 live-claim sites — `:220`, `:224`, `:307` — repoint at `TODO-BETA-054-0.1.1`.** Present-tense
     assertions that are false today: `:220` "`_bind_fieldsets` lands with `TODO-BETA-046-0.1.1`";
     `:224` "the live kanban card is `046`"; `:307` "`TODO-BETA-046-0.1.1` codifies `FieldSet` as the
     field-level tier". `:224` is the sharpest — its whole purpose was correcting a card number, so it
     has rotted in exactly the way it was written to prevent.
   - **1 revision-log bullet — `:14` — a DECIDED NON-EDIT, not a fourth rot site.** It is the
     `**Revision 2**` accuracy-pass log dated 2026-06-14, whose `(L1)` clause records that the FieldSet
     card number *was pinned to* the then-live `TODO-BETA-046-0.1.1`. **It is true as history**: `046`
     genuinely was the live id on 2026-06-14, six weeks before the 2026-07-30 renumber; only its subject
     moved since. `bld-009-r2` settled this exact shape at `spec-028:41` — *a revision-log bullet records
     what a review round did, and rewording it would desync it from the text it quotes.* **A sweep handed
     an undifferentiated "4 stale citations" would destroy a true historical record.** — `bld-009-r4`
     `### Recorded for the maintainer` item 2.
6. **`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`'s `fields_class` docstring**
   reserves the slot for `TODO-BETA-046-0.1.1` — the same renumber residue, in **shipped source**.
   Uncovered by any declared sweep. Source was read-only this cycle. — `bld-009-r1`, `bld-009-r1b`;
   re-measured and confirmed still present by `bld-009-r4`.

### D. Orphaned deferrals — the central hand-off

7. **`spec-028:195` / `:1191`** defer **`DjangoListField` orderBy-argument integration** to `0.0.9`.
   `list_field.py` has **zero** occurrences of `order_by` / `orderset` / `filterset`, and no card in
   `KANBAN.md` or `BACKLOG.md` carries it. `0.0.9` shipped five versions ago. — `bld-009-r2`
   `### Recorded for the maintainer / R4`.
8. **`spec-028:734`** (`### Decision 8` step 4) defers the position-side-channel leak-closing design
   "likely to a sibling `0.0.9` ordering-permissions card". Zero card hits. **A second site at `:41` is
   a revision-log bullet and a decided non-edit**, same grading as item 5's `:14`. — `bld-009-r2`.
9. **`spec-027` #"Auto-generation of `FilterSet` from `Meta.fields`"** reads "Deferred; … lands when
   `DjangoConnectionField` ships in `0.0.9`". `DjangoConnectionField` shipped; implicit generation did
   not. This is the verbatim twin of the sentence R2 fixed at `spec-028:200`. — `bld-009-r2`.
10. **ONE repo-wide sweep, recommended in place of N separate fixes: "does any archived spec's `0.0.X`
    deferral have a card?"** Sized by R2 at **56 archived specs, ~34 carrying a deferral-plus-version
    line, ~190-200 candidate lines**. It **folds in** items 5, 6, 7, 8, 9 and 11 of this catalog, plus:
    the `WIP-ALPHA-*` stale card-state prefixes in `connection.py`, `types/finalizer.py` and
    `types/relay.py`; **[R4-new]** `spec-028`'s **7** `WIP-ALPHA-*` citations (`WIP-ALPHA-028-0.0.8` ×6,
    `WIP-ALPHA-022-0.0.8` ×1) for cards now `DONE-028-0.0.8` / `DONE-022-0.0.7`; and the 8 raw
    `Decision N line NN` refs in package source that violate `AGENTS.md` rule 27. **Surfaced as a single
    maintainer item deliberately** — it would edit dozens of sibling specs, and running it as N
    one-clause widenings is precisely the pattern this cycle hit three times and stopped. Two cautions
    for whoever runs it: honour item 5's 3+1 split, and do **not** mistake item 16's word "deferred" for
    an orphaned deferral. — `bld-009-r2`, extended by `bld-009-r4`.

### E. Recorded-not-repaired sites

11. **`KANBAN.md:3680`** (card `DONE-028-0.0.8`) still says Layer 6 is "deferred to `0.0.9` … per
    Decision 12". `### Decision 12` now records it as a standing non-goal. DB-backed; fix is an ORM edit
    plus regenerate. — `bld-009-r2`.
12. **`spec-028:1159` and `:1166`** — `## Doc updates` blockquotes of that card body and of a
    `CHANGELOG.md` bullet the shipped changelog never carried. **Left verbatim deliberately**: editing a
    quote so it no longer matches its target is a worse defect than the staleness. — `bld-009-r2`.
13. **Orphaned link definitions.** `[relay]` in `spec-028`'s bottom block (0 uses at HEAD); **[R4-new]**
    4 more in `spec-054` — `[backlog]`, `[goal]`, `[spec-030]`, `[spec-050]` (down from 5; R4's edit
    consumed `[kanban]`). All pre-existing at HEAD; **none is flagged by the scaffold gate**, which is
    the reusable finding. — `bld-009-r2`, `bld-009-r4`.
14. **`docs/GLOSSARY.md`'s `OrderSet` entry** closes "so no dynamic order factory is shipped". Verified
    imprecise since `fd0c7327`: `orders/factories.py` defines `get_orderset_class` and
    `_dynamic_orderset_cache`, so a dynamic order factory **is** shipped — it simply has **no production
    consumer**. The entry's substance is right; only the closing clause overstates "not consumed" into
    "not shipped". `docs/GLOSSARY.md` is DB-generated, so the fix is a DB edit plus regenerate, owned by
    whichever cycle next has the glossary DB open. — `bld-009-r2`; dispositioned by `bld-009-r4`.
15. **Both dynamic-set factories are production-unconsumed**, not just the order half:
    `get_orderset_class` / `_dynamic_orderset_cache` and the filter twin `get_filterset_class` have no
    package consumer — the only importers are `tests/`. **Dead code or deliberately symmetric skeleton
    is a contract-level question, not a worker's call; answer both halves together.** — `bld-009-r2`.
16. **`orders/factories.py` says "standing *deferred* Non-goal" where `spec-028:988` says "standing
    non-goal".** Two sites: the module docstring #"remains a standing deferred" (**the phrase wraps
    across a line, which is why a multi-word grep misses it** — trap 10) and
    `get_orderset_class` #"is a standing deferred Non-goal". **Graded agreeing at every pass that opened
    them**, because "deferred" there names no version and no owner. Recorded so a later pass does not
    re-raise it, and specifically so item 10's sweep does not mistake the word for an orphaned deferral.
    — `bld-009-r2`.
17. **`spec-028:1171`'s `Ordering`-enum fallback offers what `### Decision 12` rejects** — the
    `## Risks and open questions` bullet still says a follow-up card "can add `ASC_DISTINCT` /
    `DESC_DISTINCT`". **Graded a non-finding, not a defect**: that section's own preamble declares every
    item carries "a fallback if implementation reveals the preferred answer is wrong", so a
    demand-contingent revisit of a rejection is the section's declared shape and asserts nothing false
    about shipped code. **Graded identically four times; please do not open it a fifth.** — `bld-009-r2`.
18. **`spec-028` `### Decision 3`'s heading still reads "Five-layer port plus a *deferred* Layer 6"**
    while its own `### Decision 12` records Layer 6 auto-generation as a standing non-goal. **Kept
    deliberately**: the heading's slug carries **6 in-file uses** (`:10`, `:16`, `:126` ×2, `:130`,
    `:1205`), all of which a retitle would dangle, and the word carries no version and no phantom owner.
    Heading-vs-body agreement here is a maintainer **preference**, not a defect. — `bld-009-r2`.
19. **Residual retired-rationale sites in `orders/inputs.py`** (`_build_input_fields` #"reserved -- see"
    and #"future-extension"): neither is false today, but they are the same rationale's third and fourth
    instances in one module. — `bld-009-r2`.
20. **Card 054 carries a promotion-owner conflict in its own text.** Its `#### Definition of done`
    promotes `Meta.fields_class` out of `DEFERRED_META_KEYS` "(per `TODO-BETA-058-0.1.3`)" while the same
    card's Foundation-slice seam says card 054 "populates the slot and promotes the key end-to-end".
    `spec-054` `## Risks and open questions` records it with a pinned preferred answer (Decision 8:
    promote on 054; 058 owns only the later dispatch generalization). **A maintainer contract call, not a
    defect.** — `bld-009-r3` `### Decision 3`.
21. **Card 054's `#### Definition of done` opens "Add `docs/spec-054-fieldset-0_1_1.md`"** but the spec
    lives at `docs/SPECS/`. Pre-existing; DB-backed. — `bld-009-r3`.
22. **`tests/test_connection.py:3`'s module docstring cites `docs/spec-030-connection_field-0_0_9.md`**;
    the file exists only at `docs/SPECS/spec-030-connection_field-0_0_9.md`. Verified both ways.
    **Recorded, not fixed**: pre-existing at HEAD, source/tests read-only this cycle, and the file is
    being actively edited by a concurrent session. — `bld-009-r1c`; dispositioned by `bld-009-r4`.
23. **`filters/sets.py`'s in-place `Meta` mutation** (`meta_class.fields = meta_class.filter_fields`)
    mutates the **consumer's** `Meta`, and the `hasattr(meta_class, "fields")` guard sees **inherited**
    attributes. Pre-existing, shipped, and tested — recorded as a design question, not a defect claim.
    — `bld-009-r1` `### Notes for Worker 1`.
24. **`spec-009:592-597`'s registry-state sentence is satisfied across two objects** — registry-global
    `is_finalized` vs per-type `DjangoTypeDefinition.finalized`. **Not false**; a future tightening
    should say which object holds which half. — `bld-009-r1b`.
25. **Three examined-and-not-raised absolutes in `spec-009`, recorded so a later pass does not re-open
    them as new**: `:654`'s "Phase 2 is the only window" (true under its resolver scope); `:649`'s
    three-applier enumeration (correct as scoped); `:930`'s "across every cardinality". Plus rationale
    `:533` and `:359-360` (three appliers of the colored runner pair where four measured —
    `filters/sets.py` is the fourth), both graded notes in `final-accepted` regions. — `bld-009-r1b`.
26. **The rationale's `## Standing notes` "three sites" bullet (`:649`) is DELIBERATELY stale.**
    Correcting it would break the cycle's append-only constraint on the rationale file; the staleness is
    stated in-file five lines above it, and the spec's own opener was corrected to "four sites".
    **Correct it in the first pass that has the rationale open without that constraint.** — `bld-009-r1`,
    `bld-009-r1b`.
27. **[R4-new] `spec-054-fieldset-0_1_1.md` has no `-terms.csv` companion**, so
    `scripts/check_spec_glossary.py` exits **2** on it (`missing file`). Confirmed pre-existing at HEAD.
    It is an in-flight (unshipped) spec, so this may be intentional under `AGENTS.md` rule 26 — but **the
    checker cannot distinguish "not yet authored" from "lost in an archive move"**, and `docs/SPECS/appx/`
    does carry a `spec-054-search_fields-0_1_2-terms.csv` from the pre-renumber numbering. Worth one
    maintainer look. — `bld-009-r4` `### Recorded for the maintainer` item 5.

### F. Process finding — corpus definition

28. **[R4-new] State corpus exclusions by BASENAME, not by path prefix — a path prefix silently fails on
    an archived copy.** R4's two token sweeps measured over **different** permanent corpora without
    either noticing: `### Direction 2` stated the rule as a path prefix (757 tracked, minus 137 under
    `docs/builder/bld-`, `docs/builder/build-`, `docs/review/`, `docs/dry/` = **620 files**), while
    `### Direction 3` measured under a basename reading (per-cycle build documents excluded wherever they
    live = **606 files**). **The 14-file difference is a directory, not a file**: every one sits under
    `docs/builder/DONE/`, whose paths begin `docs/builder/DONE/build-` and so escape the
    `docs/builder/build-` prefix. Of the 14, exactly **two** carry any swept token — R4's recorded
    figures are **`15 / 5`** for `TODO-BETA-046-0.1.1` and **`27 / 9`** for `DjangoModelType`, each
    correct under the rule it was computed with, **and those figures must not move**. **The part a
    future pass most needs:** both prior instruments applied the rules inconsistently and *neither
    noticed* — R4's own two sweeps and Worker 3's two independent re-derivations all reproduced their
    figures exactly, because each matched whichever rule that direction had used. **Two independent
    agreeing measurements did not catch it; only running one population under both readings did.**
    — `bld-009-r4` `### Recorded for the maintainer` item 8.

### G. Commit-gate blockers — not this cycle's, but they will bite

29. **[gate-new] The full sweep is RED on a concurrent session's uncommitted adversarial fixture:
    `31 failed, 93 errors`.** `tests/types/test_relay_interfaces.py:1569`'s hostile `__format__` fixture
    is **absent at `HEAD`** and fails twice over — directly against ~25 f-strings on `meta.model.__name__`
    in `types/base.py::_validate_meta`, and by **leaking past teardown**
    (`TypeError: cannot delete '__name__' attribute of immutable type`), which poisons every later test
    in the same xdist worker and makes the error set shuffle-dependent. **The owner is the concurrent
    package-source session**, which must reconcile its new fixture with the production f-strings.
    Full attribution in `### Command 1` above. **Nothing was reverted or fixed here.** — this gate.
30. **`docs/GLOSSARY.md` is dirty with no backing change in the database** — all ten `glossary_*` tables
    are byte-identical to HEAD, yet the rendered file carries a one-line diff. Either a hand edit of a
    generated file or a DB write since rolled back. **Flag at commit time.** — `bld-009-r3`.
31. **One card-renumber `grep` is owed at the commit gate.** Every card id cited across this cycle's
    documents resolves today — R4 re-derived **86 occurrences across four documents; 29 distinct *per
    document* and 20 distinct *overall* once the four id sets are unioned; 3 unresolved, all 3 graded** —
    but a renumber landing before commit would silently falsify them. — `bld-009-r1`, re-measured by
    `bld-009-r4`.

### H. Closed in-cycle — listed so the next author does NOT re-defer them

- **The async `SyncMisuseError` coverage gap** — escalated across seven passes as "needs carding",
  **promoted to a permanent test in-cycle as R1c** per `### Maintainer decision 5`, with a failability
  proof and a floor run. Not deferred.
- **`spec-028` `### Decision 12`'s DISTINCT ON / Layer 6 deferral** — **fixed by R2**, reconciled as
  *discharged by an alternative* (the row-preserving `Min`/`Max` ordering), not postponed.
- **Card 054's two stale `DjangoModelField` / BACKLOG-item-38 references** — **fixed by R3** in the DB,
  with the board regenerated.
- **The two clauses those two fixes falsified** (the `spec-009` rationale's `DISTINCT ON` claim and
  `spec-054`'s "Stale card reference" bullet) — **fixed by R4**.
- **`scripts/check_trailing_commas.py` on `tests/test_connection.py:1062`** — recorded by `bld-009-r1c`
  as a commit-gate blocker; **re-measured at final state by this gate and RESOLVED** (0 occurrences of
  the single-line form; the concurrent session exploded its own signature). Retired, not carried.

**Catalog size: 31 items** across sections A-G, plus 5 closed-in-cycle entries in section H that are
explicitly **not** deferrals. Counted by enumeration at final state, not by grep
(`BUILD.md` `## Claims are proven mechanically`).

## Maintainer hand-off

Two things need explicit separation before commit, plus one gate-new blocker. **Nothing below was
reverted, reformatted, or auto-fixed** (`AGENTS.md` rule 34; `START.md` "Concurrent sessions").

### (a) The concurrent-session test failure — NOT this cycle's

`uv run pytest --no-cov` is **red**: `31 failed, 5857 passed, 40 skipped, 93 errors`. **100% of the
failing population** — 31 of 31 `FAILURES` report blocks and 41 of 41 `ERRORS` report blocks, classified
by content — traces to **one uncommitted adversarial fixture** at
`tests/types/test_relay_interfaces.py:1569`, **proved absent at `HEAD`** by
`git show HEAD:tests/types/test_relay_interfaces.py` (0 occurrences of `hostile model format`) against 1
occurrence in the working tree.

The five files involved — `types/base.py`, `relay.py`, `tests/types/test_relay_interfaces.py`,
`tests/test_relay_node_field.py`, `tests/testing/test_relay.py` — are all ` M` and **all in the plan's
baseline-dirty package-source group**. **None is in this cycle's writable set.** The owner is the
concurrent package-source session, which needs to reconcile the new fixture against the ~25 f-strings on
`meta.model.__name__` in `types/base.py::_validate_meta`. **A second, separable defect rides with it:**
the fixture's monkeypatch **cannot be undone** on Python 3.14 and leaks the hostile name into the shared
model for the remainder of the xdist worker — which is why two runs of the same suite produced different
error sets (104 vs 93). That leak will keep making the suite look nondeterministic until it is fixed,
independently of the direct assertions.

This cycle's own work is **green**, verified positively: R1c's added row + sibling `2 passed`;
`tests/orders/` `141 passed`; and the same two rows `2 passed` at the floor.

Also note: **`HEAD` moved during this cycle**, `6f8bf818` → `1abba7a4`, with three package-source commits
landing (`bd7df65b`, `e473adf0`, `1abba7a4`). **No commit swept any of this cycle's work** — proved with
`git log` per writable path, never `git status` alone; every one of this cycle's edits is still ` M` and
unstaged.

Separately and much smaller: `scripts/check_trailing_commas.py --check` exits 1 on **one** violation, in
`.claude/projects/…/memory/one-spec-owns-each-feature.md` — an agent memory file that is **gitignored**
(`.gitignore:170`) and unknown to git. Outside the repo corpus; nobody's commit gate.

### (b) `db.sqlite3` / `KANBAN.md` / `KANBAN.html` carry a MIXED diff — two cycles, one set of files

Carried forward verbatim in substance from [`bld-009-r3-card054_db_references.md`][bld-r3]
`### Maintainer hand-off`, so the maintainer can separate the two card-body edits at commit.

**R3 wrote exactly three paths**: `examples/fakeshop/db.sqlite3` (two `CardItem.text` values), `KANBAN.md`
(regenerate output), `KANBAN.html` (regenerate output).

**This cycle's two intended `CardItem` changes**, both on card `TODO-BETA-054-0.1.1` (`Card` `pk=16`,
`number=54`), section `foundation_seam`:

- **`CardItem` `pk=316`** (`order=1`) — 307 chars → 296 chars. The `BACKLOG.md` item-38 /
  `DjangoModelField` clause replaced with "no custom Strawberry field class is required for it; spec-054
  Decision 11 pins resolver wrapping as the mechanism that carries the gate".
- **`CardItem` `pk=839`** (`order=4`) — 446 chars → 869 chars. The trailing "See `BACKLOG.md` item 38 for
  the `DjangoModelField` direction" replaced with the settled rationale: resolver wrapping per spec-054
  Decision 11, plus the recorded reason `strawberry.field(permission_classes=...)` was rejected.

**Nothing else on card 054 changed, and no other card, status, `SpecDoc` row, or glossary row was
touched.**

**Every other hunk in those paths belongs to someone else:**

| Path | Hunk | Owner |
|---|---|---|
| `KANBAN.md` | the deleted bullet at `:~4479` opening "remove the tests.fixtures.apps fixture app + unmanaged cardinality fixtures", on a **different card** | the concurrent **`spec-014`** residual cycle — `docs/builder/bld-014-r3-card_body_scope_fix.md`, `Status: final-accepted`, uncommitted |
| `KANBAN.html` | the single data-block line necessarily carries **both** cycles' card text, since it is one line | shared: R3's two strings + `spec-014`'s deletion |
| `docs/GLOSSARY.md` | the whole diff (auth entry, `SessionMiddleware` wording) | another concurrent session; **R3 never opened this file** — see catalog item 30, it has no backing DB change |
| `examples/fakeshop/db.sqlite3` | binary; R3's semantic contribution is the two `kanban_carditem` rows above and **nothing else in that table** (measured by scoped `iterdump()` diff). Other tables were not inspected and may carry concurrent work | mixed |

**The verification limitation, stated plainly and not papered over:** two-consecutive-regenerate
byte-stability **cannot** distinguish this cycle's write from the concurrent session's while theirs is in
flight, so R3 did not offer it as evidence. The substitutes actually run were exact-string identity on
both rows, a scoped semantic DB diff, a per-card `HEAD`-region diff, and the `--check` freshness runs —
the first three authorship-attributable, the last explicitly not.

**Do not revert either diff to tidy the other.** Only the maintainer can sequence the two cycles at
commit.

---

## Final verification (Worker 1)

- **Gate commands:** all six run, each result recorded honestly above. Five pass. One fails.
- **The one failure is fully attributed and is not this cycle's** — proved against pristine `HEAD` via
  `git show HEAD:<path>` into a scratch path outside the repo, with the population **enumerated** (31 of
  31 and 41 of 41 report blocks classified by content) rather than grep-counted, and with this cycle's
  own files positively verified green. It falls squarely inside the plan's recorded baseline exception
  and routes to the maintainer, not back through a residual item's loop.
- **Floor verification:** the one declared scope (R1c, per `### Maintainer decision 5`) **was run and is
  properly recorded** in `bld-009-r1c` by both Worker 2 and Worker 3, with venv path outside the repo,
  resolved versions matching `BUILD.md`'s canonical floor exactly, focused scope, and result.
  Independently re-run here as backstop: `2 passed in 6.20s`. **No unrun floor claim was closed over.**
  The shared `.venv` was never mutated by any pass of this gate.
- **Deferred work catalog:** authored, **31 items**, R4's independently-verified input consumed and R4's
  own finds folded in, each bullet actionable standalone.
- **Nothing was committed; no branch was created or switched;** no `git stash` / `checkout` / `restore` /
  `worktree` was used; `examples/fakeshop/db.sqlite3` was never reset or rebuilt; nothing under
  `docs/review/` was touched; no concurrent session's file was reverted, formatted, or fixed; no
  `CHANGELOG.md` edit was made.
- **Files this pass wrote: exactly one** — `docs/builder/bld-009-final.md`, plus this cycle's namespaced
  Worker 1 memory file.
- **Final status: `final-accepted`.**

### Summary

The gate passes under the plan's recorded baseline exception. Five of six commands are green; the sixth,
the full `pytest` sweep, is red on a concurrent package-source session's uncommitted adversarial test
fixture that does not exist at `HEAD` and that no residual item in this cycle owns. Withholding
acceptance over it would be withholding acceptance over breakage the exception explicitly covers; and
recording it as anything other than a real failure would be papering over it. It is recorded as a
failure, attributed mechanically, and handed to the maintainer.

The cycle closes having established the load-bearing negative — **no correctness defect and no silent
omission in shipped source** — with every layer that has a shipped subsystem implemented at or beyond
spec, 8 of 11 success criteria met and the three unmet each carded for beta, and six spec'd-but-never-built
items adjudicated `DROP AND SCRUB` on parity grounds and scrubbed from the spec.

### Spec changes made (Worker 1 only)

None. This pass made no spec edit. `spec-009`'s status/header lines were re-verified at final state and
required none.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[bld-r1c]: bld-009-r1c-async_syncmisuse_test_row.md
[bld-r3]: bld-009-r3-card054_db_references.md
[bld-r4]: bld-009-r4-docs_archive_audit.md
[build-009]: build-009-rich_schema_architecture-0_0_4.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
