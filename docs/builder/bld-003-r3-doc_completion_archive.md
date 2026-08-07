# Build: R3 — Finish the documentation and audit the archive (spec-003)

Spec reference: `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` (whole file; the one open obligation is `## Documentation updates when O4 ships`, `:191-196`)
Rationale companion: `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` (read-only for Worker 2; Worker 1 appends if a spec edit lands)
Status: final-accepted

**Shape note — R3 runs the FULL unmodified worker chain.** Unlike R1 and R2 (`docs/builder/build-003-optimizer_nested_prefetch_chains-0_0_2.md` Deviation 2), R3 has real Worker 2 work: a read-only durable-doc audit whose remedy, if drift is found, is an ORM edit plus a regenerate, plus the three-direction cross-reference sweep, the DB/CSV verification, and the staged-anchor sweep. So `Status: planned` on this artifact routes to **Worker 2**, then Worker 3, then Worker 1 for final verification — the ordinary mapping, not Deviation 2's.

**One step is reserved to Worker 1 and Worker 2 must not attempt it:** the single authorized `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` sentence edit (`### Implementation steps` step B below). Only Worker 1 may edit a spec (`docs/builder/worker-1.md` `## Scope`), and it is performed at Worker 1's **final-verification** pass, after Worker 3 accepts. Worker 2 that finds the `spec-004` sentence still reading `once those land` has found the expected state, not a defect.

**Standing constraint for the whole item.** "Make sure the code is correct" is a read-only audit obligation. No package source and no test file changes: a factually-false module docstring, a genuine optimizer defect, or any other source-level finding is **recorded and escalated**, never fixed here. The build plan's `## Build-wide context flags` allows a docstring correction to route through Worker 2; this dispatch narrows that to record-and-escalate, because a documentation cycle that silently becomes a source cycle is exactly what `## Build-wide context flags` and `### Residual scope` exist to prevent. Worker 1 decides at final verification whether to hand it to the maintainer.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** **Not applicable — no helper-like logic is planned, and that is stated rather than skipped** (`worker-1.md` `### DRY analysis shape`: silence on DRY is not acceptance). `worker-1.md` `### Package-wide helper inventory before helper planning` gates the inventory on *proposing a new helper, shared constant, validation branch, coercion utility, or test helper*. R3 proposes none: it lands no package source, no test, and no script. The only executable artifacts it may produce are throwaway read-only verification one-liners and, conditionally, ORM writes through `manage.py shell` — neither is package-resident logic that a future call site could duplicate. No package-wide AST inventory was refreshed and none is owed.
- **Static inspection helper (`scripts/review_inspect.py --output-dir docs/shadow`) — EXPLICITLY SKIPPED, with reason.** `docs/builder/BUILD.md` `### When to run the helper during build` requires it at planning when the plan **adds logic** to a file under `optimizer/` or `types/`, or to any existing `.py` of 150+ source lines. This plan adds logic to no `.py` file at all. R2 ran it over nine optimizer/types modules one item ago and its **Symbols** sections are the symbol-name reference R3 would want; nothing under `django_strawberry_framework/` has changed since (`git diff --name-only -- django_strawberry_framework/` is empty and `HEAD` has not moved into that tree), so that output is current. Recorded as a skip-with-reason rather than passed over in silence.
- **Existing patterns reused.** Three, all procedural rather than code:
  - The **durable-doc audit shape** is the spec-002 residual cycle's (`docs/builder/build-002-optimizer-0_0_2.md`), which is this cycle's declared precedent throughout.
  - The **DB-backed edit procedure** is `docs/builder/BUILD.md` `### Generated docs are DB-backed: edit the DB, then regenerate`, restated for Worker 2 in `### Implementation steps` step A4 because Workers 1-3 do not read `worker-0.md`.
  - The **cross-reference verification** reuses the build plan's already-verified `### Every reference TO spec-003` table as its input list rather than re-deriving the population from scratch; the sweep that *confirms* the table is re-run, per the plan's own instruction that it "is re-run by R3, not trusted from this table".
- **New helpers justified.** None. No helper, module, constant, or fixture is created.
- **Duplication risk avoided.** Three risks, each named and each pre-decided rather than left to Worker 2:
  - **Spec versus durable doc.** The single largest temptation in this item is to "improve" `docs/GLOSSARY.md`'s `DjangoOptimizerExtension` entry by importing spec-003's newly-reconciled contract prose into it. That would create a second statement of the same contract in a file the spec does not own, which rots. The audit question is **narrow and factual**: does the shipped-behaviour bullet list describe the O4 surface *accurately*, not *completely*. Accurate-but-terse is a pass.
  - **R3 versus card `TODO-ALPHA-052-0.1.0`.** Card 052 already owns four spec-003 stale-site notes and the `GLOSSARY.md` / `CHANGELOG.md` `0.0.2`-versus-`0.0.3` dating question (`KANBAN.md:317`, `:320`). R3 must not restate, partial-fix, or pre-empt any of them. See `### The one thing that must NOT be silently reconciled` below.
  - **R3 versus the final gate.** Every deferred item R3 surfaces goes into this artifact's `### Notes for Worker 1 (spec reconciliation)` **once**, and the final gate's `### Deferred work catalog` is the only place they are consolidated. R3 does not open its own catalog.

### Boundary count — the split question, answered in writing

**Zero boundaries.** `worker-1.md` `### Boundary count is a split trigger` requires the count be written down and the split question answered even when the diff would be small, so: R3 introduces no guard, no cap, no rejection path, and no validation branch, because it changes no executable code. `BUILD.md` `### Slice splitting`'s boundary-count trigger therefore does not fire, and neither does its diff-shape trigger — the worst-case diff is one sibling-spec sentence plus, conditionally, a DB row and three regenerated files.

The item is nevertheless **one unit and is not split**, for a positive reason rather than by default: its four workstreams are four *directions of the same audit* over one document's published surface, and the only meaningful output is the joint verdict "the O4 record is complete and consistent everywhere it appears". Splitting it would produce two partial verdicts, neither of which is the deliverable, and would risk the surface-consistency failure `worker-0.md` `## Closing out a kanban card` warns about — a partial fix across multiple surfaces is worse than uniformly-unfixed.

### Implementation steps

Paths are exact; line numbers are **pin-at-write-time navigational hints** — re-derive against the current file before acting, since `HEAD` has moved twice mid-cycle and a concurrent session writes this tree.

Working-tree state as read at planning: `git rev-parse HEAD` -> `4d1c512a`; `git status --porcelain` carries **only this cycle's five paths** (` M docs/SPECS/spec-003-…md` plus four untracked `docs/SPECS/appx/spec-003-…-rationale.md`, `docs/builder/bld-003-r1-…`, `bld-003-r2-…`, `build-003-…`). The build plan's baseline-dirty list is empty in both directions. **If churn reappears, report it and never revert it** (`AGENTS.md` rule 34) — Worker 0 appends it to the plan.

#### A. Durable-doc audit of the O4 surface (Worker 2)

**A0. Read the reconciled spec first.** `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` at its current 240 lines, end to end. The audit compares each durable doc against **what is now true**, not against the pre-R2 text; auditing against a stale mental model is the one way this step produces a false finding.

**A1. `docs/GLOSSARY.md` — GENERATED, never hand-edited.** Audit these sites, read-only:

| Site | What to confirm |
|---|---|
| `## \`DjangoOptimizerExtension\`` entry, "Shipped behavior" list (`:712`-`:748` at planning) | The bullet `- nested prefetch chains for nested GraphQL selections` accurately names the shipped O4 surface. Also confirm the four adjacent O4-adjacent bullets are true as written: `select_related` for safe single-valued relation chains; `prefetch_related` for many-side relations; generated `Prefetch` objects for child querysets; connector-column inclusion |
| The same entry's `**Status:** shipped (\`0.0.2\`)` line | **Read it, do not touch it.** The `0.0.2`-versus-`0.0.3` dating question is card `TODO-ALPHA-052-0.1.0`'s by that card's own words (`KANBAN.md:320`, "This card owns the CHANGELOG promotion, so the decision belongs on it"). Confirm only that it is unchanged and record it as out of scope |
| `#fk-id-elision`, `#only-projection`, `#plan-cache`, `#queryset-diffing`, `#optimizerhint`, `#metaoptimizer_hints`, `#schema-audit`, `#djangotype` | The eight anchors card 3 links. Confirm each anchor still **exists** as a heading (the spec's eight link definitions target them) and that nothing in the entry contradicts the reconciled spec. A terse entry is not drift |

**A2. `docs/TREE.md` — script-rendered from module docstrings** (`scripts/build_tree_md.py`). Audit the `optimizer/` subtree (`:249`-`:262` and its duplicate rendering at `:371`-`:384` at planning): `walker.py`, `plans.py`, `nested_planner.py`, `join_taxonomy.py`, `selections.py`, `extension.py`. Two questions only: (i) does any docstring render now-shipped O4 behaviour as unbuilt — `planned`, `Slice N`, `after Slice N`, `TODO(` (`ARTIFACT.md` `### Documentation / release sanity`); (ii) is any docstring **factually false** about the O4 surface. **Do not edit a docstring.** A hit on either question is recorded in `### Notes for Worker 1 (spec reconciliation)` with the symbol-qualified site and escalated — see the standing constraint above.

**A3. `docs/README.md` — hand-authored.** Audit `:53`, `:55`, `:87-88`, `:106` (the `DjangoOptimizerExtension` bullet) for accuracy about nested-selection planning. Note this file was dirty from a concurrent session earlier in the cycle and is now committed; read it at its **current** content.

**A4. `KANBAN.md` — GENERATED.** Audit `:41` (the O1-O6 line naming "nested prefetch chains"), `:144` (the spec link row), and the `DONE-003-0.0.2` card body at `:4812`ff including the `Spec:` line at `:4819`. Confirm the card's five `CardItem`s read correctly against the reconciled spec.

**A5. Disposition.** Two outcomes, and **only these two**:

- **Audit found no drift, no DB write.** State it in that form, per site, in `### Files touched` (`None; the audit found no drift and wrote nothing.`) and in the build report. This is the expected outcome — the build plan's `## Concurrent-writable tracked binary / generated files` already records that "no residual item is expected to write" the DB, `KANBAN.md`, `KANBAN.html`, or `docs/GLOSSARY.md`.
- **Audit found drift in a GENERATED doc.** The fix is an **ORM edit plus a regenerate**, never a hand-edit of the rendered markdown (`BUILD.md` `### Generated docs are DB-backed: edit the DB, then regenerate`; a hand-edit is silently reverted by the next render, and a raw SQL insert skips the `post_save` side-row the render needs). Procedure:
  1. Edit through `uv run python examples/fakeshop/manage.py shell` using the Django ORM (`.save()` / `.objects.create()`), never raw SQL. `GlossaryTerm.body` for a glossary entry; `CardItem.text` for card prose. Change only what the audit proved false.
  2. Regenerate all three from the repo root: `uv run python scripts/build_kanban_md.py`, `uv run python scripts/build_kanban_html.py`, `uv run python scripts/build_glossary_md.py`.
  3. **Verify by two-consecutive-regenerate byte-stability plus spot-checks of the rendered result, NOT by "`git diff` is clean"** (`BUILD.md` `### Tracked binary / generated files`). Hash each regenerated doc after two consecutive runs; the hashes must match.
  4. Apply the writes **on top of** any concurrent state without reverting it, and hand the mixed diff to the maintainer. For the DB compare `iterdump()` semantics, never file bytes.
  5. Re-run `uv run python examples/fakeshop/manage.py import_spec_terms --check` **after** the write, and `uv run python examples/fakeshop/manage.py check`.

#### B. The one authorized sibling-spec edit — **WORKER 1's, at final verification. Worker 2 does not perform this step.**

`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:154`, the B4 `**Depends on.**` line, currently reads:

> **Depends on.** O3 (shipped). The `SKIP` hint is independent of O4-O6. The `.prefetch(Prefetch(...))` hint composes naturally with O4 (nested chains) and O6 (downgrade rule) once those land.

Both O4 and O6 landed at `0.0.2`. The trailing `once those land` is the last undischarged item of spec-003's own `## Documentation updates when O4 ships` (`spec:191-196`: "Remove the `not yet implemented` rider on the `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` B-slices that depend on nested resolver-key sentinels"), and that surviving in-spec clause is what licenses the edit.

Scope, exactly: **retire the `once those land` rider on that one sentence and nothing else.** No other sentence in `spec-004` is in scope; no other sibling spec is opened. The other three `Depends on.` lines that mention O4-O6 (`:46`, `:111`, `:215`, `:267`, `:301`) say "Independent of O4-O6", which is a true statement of independence, not a rider — leave them.

After the edit, Worker 1: re-runs `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` and `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`; confirms `AGENTS.md` rule 27 still holds in the edited line; and records the change under `### Spec changes made (Worker 1 only)` citing the spec-003 clause that licenses it. Whether spec-003's `## Documentation updates when O4 ships` section itself then changes (the list becomes empty) is a Worker-1 custody decision made in the same pass, with the reasoning appended to the rationale under its `` ### `## Documentation updates when O4 ships` `` entry — not restated in the spec.

#### C. The three-direction cross-reference sweep and archive verification (Worker 2)

**C1. Inbound — every reference TO spec-003.** Re-run the sweep rather than trusting the table:

```shell
grep -rn 'spec-003' . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=shadow
```

Then confirm each row of the build plan's `### Every reference TO spec-003` table (`build-003-…:242-256`) still reads correctly. **This is a verification list, not a rewrite list** — report per row; edit only a row the audit proves wrong, and for a GENERATED row (`KANBAN.md`, `KANBAN.html`) the fix is step A5's ORM route. The five rows: `KANBAN.md:144` / `:4819` (+ `KANBAN.html`); `KANBAN.md:240` / `:317` (card 052's scope items — see `### The one thing that must NOT be silently reconciled`); `docs/SPECS/spec-002-optimizer-0_0_2.md:6` `## Purpose` (read-only, correct and load-bearing); the two prior rationale files (read-only); `docs/builder/build-002-optimizer-0_0_2.md` (historical, correct as history).

Expect the sweep to also return spec-003's and the rationale's own self-references and this cycle's `bld-003-*` / `build-003-*` artifacts. Those are not table rows; decompose them out and say so.

**C2. Outbound — every link definition resolves on disk.** For **both** `docs/SPECS/spec-003-…md` (10 definitions at planning) and `docs/SPECS/appx/spec-003-…-rationale.md` (19), partition the file at `<!-- LINK DEFINITIONS -->`, parse each `[ref-id]: path` definition, resolve the path **from that file's own directory**, and `exists()`-check it. Confirm additionally: zero undefined references (a `][ref-id]` in the body with no definition), zero unused definitions, and every `#anchor` fragment resolving against a real heading in the target file. The rationale sits two levels below `docs/`, so its definitions correctly read `../../GLOSSARY.md` for a `docs/` target and `../spec-NNN-….md` for a `docs/SPECS/` sibling — a wrong depth here is exactly the link-rot shape a same-named file one level up can mask, so `exists()` is the test, not eyeballing.

**C3. The kanban DB.** Read-only unless C4 finds a mismatch. Verified at planning and to be re-confirmed by Worker 2 (state moves; a concurrent session writes this DB):

| Check | Value read at planning |
|---|---|
| `Card.objects.get(number=3)` | `card_id` `DONE-003-0.0.2`, `status.key` `done`, `target_version.number` `0.0.2`, title `Optimizer O4 nested prefetch chains` |
| Its `SpecDoc` — **the reverse accessor is `card.spec`, not `card.spec_doc`** (`getattr(card, "spec_doc", None)` returns `None` and reads as a missing row) | name `spec-003-optimizer_nested_prefetch_chains-0_0_2`, `path` `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` — the **archived** path. `SpecDoc.path` is the writable column; `SpecDoc.url` is a read-only `@property` deriving from it, so assigning `url=` raises |
| `card.glossary_links.count()` and their anchors | **8**: `djangotype`, `fk-id-elision`, `metaoptimizer_hints`, `only-projection`, `optimizerhint`, `plan-cache`, `queryset-diffing`, `schema-audit` |
| `card.items` | 5 `CardItem`s — `scope` x3 (complete), `verified_upstream` x1 (incomplete), `note` x1 (complete). The single unticked row is the board's convention (card 2 matches); **not drift, no edit** |

**Additionally confirm the `GlossarySpecMention` rows for spec-003 point at the ARCHIVED path.** `KANBAN.md` card 052 records that `import_spec_terms::_sync_spec_mentions` orphans mention rows at a pre-archive `docs/` path on every archive, and that the accumulated orphans were reaped but the cause is unfixed. Spec-003 is already archived, so this is precisely the surface where a stale `docs/spec-003-…md` mention row would still sit. A stale row found here is **reported, not fixed** — the cause is card 052's and a partial fix of one card's rows is the multi-surface half-fix `worker-0.md` warns against.

**C4. The terms-CSV importability chain.** Compare the 8 `CardGlossaryTerm` anchors against `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-terms.csv` — **one row per anchor**, which is what `import_spec_terms` requires and what a green `check_spec_glossary` does *not* prove (the checker is anchor-keyed and tolerates a many-term-to-one-anchor CSV the importer rejects on its unique constraint). The CSV carries 8 rows / 8 distinct anchors at planning and matches the DB exactly. **Never open the CSV for writing** — it is on this item's do-not-touch list.

Then re-run, quoting each result:

```shell
uv run python examples/fakeshop/manage.py import_spec_terms --check
  # baseline at planning: OK: 49 done cards have glossary links.   exit 0
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md
  # baseline at planning: OK: 8 terms - all have glossary entries and at least one spec link.   exit 0
```

Both were re-run at planning **after** the concurrent session's DB commit, so these are current baselines, not pre-flight readings. If step A5 wrote the DB, re-run both **after** the write as well.

#### D. The staged-anchor sweep (Worker 2)

`BUILD.md` `## Cross-slice integration pass` step 6, folded into R3 because this cycle produces no `bld-integration.md`:

```shell
grep -rEn 'TODO\(spec-003|TODO-(ALPHA|BETA|STABLE)-003' . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=shadow
```

**Publish the decomposition, never the bare count** — a raw count reads as a failure signal and it is not one. R2's final verification measured **21 hits decomposing to zero staged anchors**; re-measured at R3 planning: still **21 hits across exactly four `.md` files** — the rationale, `bld-003-r1-rationale_move.md`, `bld-003-r2-spec_reconciliation.md`, and `build-003-…md`. Zero in the spec, zero anywhere else.

**How to distinguish a staged anchor from a quotation of one** — the discrimination this step exists to perform, stated mechanically so it is not a judgement call:

1. **A staged anchor is a source-site marker**, per `AGENTS.md` rule 26: a `# TODO(spec-NNN slice N): …` comment in a `.py` file (optionally beside a `raise NotImplementedError`), or the `TODO-<MILESTONE>-<NNN>-<ver>` card-id form in source. It is *instructional* — it tells a future builder that work is unbuilt at that site.
2. **A quotation is prose about an anchor** in a `.md` file — inside a code span, a blockquote, or a sentence whose subject is the anchor convention itself ("no `TODO(spec-003…)` anchor survives"). It is *descriptive*.
3. **The mechanical test, run first and reported first:**

   ```shell
   grep -rEn 'TODO\(spec-003|TODO-(ALPHA|BETA|STABLE)-003' django_strawberry_framework/ tests/ examples/ scripts/
   ```

   This must return **0**. A staged anchor can only live in source; a zero here means every remaining hit is by construction a `.md` hit and the classification question is closed for source.
4. **Then classify the `.md` hits by file, not by line.** All four expected files are per-cycle scratchpads (`START.md` "Temp artifact conventions") or the durable rationale, and every hit in them is an account of anchors that were removed. Read each hit and confirm it is descriptive; report the per-file counts so the decomposition is re-derivable.
5. **`KANBAN.md`, `KANBAN.html`, and `BACKLOG.md` are excluded by `BUILD.md` step 6 itself** — `TODO-<MILESTONE>-<NNN>` legitimately names unshipped board cards there. A hit in those files is never a finding.

Any hit that survives steps 3-4 as a genuine source-site anchor is `revision-needed` and routes back through this item, not to the final gate.

### The one thing that must NOT be silently reconciled

`KANBAN.md` card `TODO-ALPHA-052-0.1.0` names four stale spec-003 sites (`KANBAN.md:317`, with a related note at `:240`). **Three are now closed by R2** — the `plan_optimizations` arity and `_collect_scalar_only_fields` present tense; the discharged when-O4-ships instruction naming a `## Current state` section that no longer exists; and the request that a later pass update the parent spec's older O4 references, which the spec-002 cycle did.

The fourth is a **divergence, not a defect**. The card prescribes replacing the spec's opening claim so that "the replacement states that O4 is shipped and that its record is this spec's". **R2 deliberately rejected that disposition** and recorded its reasoning in the rationale under `` ### `## Problem statement` ``. That is an editorial call between a board scope note and a shipped reconciliation, and it is the maintainer's, not a worker's.

`worker-0.md` `## Closing out a kanban card` is explicit: when a reference is wrong or divergent **across multiple surfaces**, do not partial-fix one surface — record the cluster as a maintainer / next-spec-author follow-up and leave every surface consistent. So:

- **Do NOT** edit `KANBAN.md` or the card-052 `CardItem.text` to retire the three closed sites. Retiring a discharged scope item on card 052 is **card 052's own closeout**, and the build plan's `### Every reference TO spec-003` table already sets that default explicitly.
- **Do NOT** edit spec-003's `## Problem statement` toward the card's prescription. R2 settled it and Worker 3 accepted the settlement.
- **DO** record the whole cluster — three closed, one divergent — once, in `### Notes for Worker 1 (spec reconciliation)`, as a **deferred maintainer decision**. Worker 1 carries it to the final gate's `### Deferred work catalog`.

This is the fourth independent on-disk carrier of the divergence (R2's Worker 3 pass-1 note 3, pass-2 note 4, R2's final verification, and now this plan). It is written down four times because the failure mode is a worker "helpfully" reconciling it in passing.

### Test additions / updates

**None; this item lands no source and no test.** Stated explicitly rather than omitted.

- No test file is added, changed, or deleted. `tests/`, `examples/`, and `django_strawberry_framework/` are read-only for the whole cycle (`build-003-…` `## Build-wide context flags`).
- **No `pytest` run.** `AGENTS.md` rule 15 forbids an unrequested run, and no `--cov*` flag is permitted in any pass (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). The full-suite run belongs to the final gate, not here.
- **No temp/scratch tests** are appropriate; there is nothing executable to develop against. Worker 3 has no temp-test opportunity to inherit and should record `None.` rather than inventing one.
- What replaces tests as this item's evidence: the four quoted verification commands (`import_spec_terms --check`, `check_spec_glossary.py --spec`, `check_trailing_commas.py --check` on every file written, `manage.py check` if the DB was written), the per-site audit table, the per-anchor link-resolution result, and the staged-anchor decomposition.
- If step A5 writes the DB, its evidence is the two-consecutive-regenerate hash equality plus rendered spot-checks — **not** `git diff` cleanliness.

### Implementation discretion items

Assessed and delegated; none is architectural.

- **The order of workstreams A, C, and D.** They are independent. Any order is fine; C4's `import_spec_terms --check` must run *after* an A5 DB write if one happens.
- **The exact form of the read-only verification code** — a `manage.py shell -c` one-liner versus a heredoc, a Python link-resolver versus a shell loop. Any form whose output the reader can re-derive is acceptable; quote the command beside its result (`BUILD.md` `## Claims are proven mechanically`).
- **Whether to write scratch verification scripts to disk.** If so, write them **outside the repository** (the session scratchpad), never into `docs/` or `scripts/`.
- **The wording of the "no drift" statement** per site in `### Files touched`, provided it is per-site and not a single blanket sentence.

Not discretionary, and not delegable: the `spec-004` edit (Worker 1's), any spec edit at all, any hand-edit of a generated doc, any source or test change, and the card-052 disposition.

### Spec slice checklist (verbatim)

**Spec-003 has no `## Slice checklist` section** — it is a single-slice spec that shipped twelve releases ago, and this is not a review round either. Per `worker-1.md` planning step 8 and the same substitution R1 and R2 used, the boxes below are the equivalent, derived one-per-workstream from item R3's contract in `docs/builder/build-003-optimizer_nested_prefetch_chains-0_0_2.md` `### Residual scope`. Every box is `- [ ]` at planning. **Worker 2 ticks a box `- [x]` in the same build report that lands its contract, and only a box whose contract actually landed**; a deferred or unperformed check stays `- [ ]` with the reason in the build report. **Worker 1 audits every tick at final verification** — over-ticked and silently-un-ticked boxes both block `final-accepted`.

- [x] `docs/GLOSSARY.md` audited against the reconciled spec: the `DjangoOptimizerExtension` entry's `nested prefetch chains for nested GraphQL selections` bullet and its four O4-adjacent siblings describe the shipped surface accurately, and all eight card-3 anchors still exist as headings.
- [x] `docs/TREE.md`'s `optimizer/` subtree audited: no docstring renders shipped O4 behaviour as unbuilt (`planned` / `Slice N` / `TODO(`), and none is factually false about the O4 surface. Any hit recorded and escalated, never edited.
- [x] `docs/README.md` audited at its current content for accuracy about nested-selection planning.
- [x] `KANBAN.md` audited: the O1-O6 line, the spec-link row, and the `DONE-003-0.0.2` card body read correctly against the reconciled spec.
- [x] Audit disposition stated in the required form — either "audit found no drift, no DB write", per site, or an ORM-edit-plus-regenerate with two-consecutive-regenerate byte-stability evidence. No hand-edit of any generated markdown.
- [x] The `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` B4 `**Depends on.**` rider retired — **Worker 1 only, at final verification**; Worker 2 leaves it untouched and records that it did.
- [x] Inbound direction verified: the `grep -rn 'spec-003'` sweep re-run and every row of the build plan's `### Every reference TO spec-003` table confirmed to still read correctly, reported per row.
- [x] Outbound direction verified: every link definition in the spec and in the rationale resolves on disk from its own file's directory, with zero undefined references, zero unused definitions, and every `#anchor` fragment resolving to a real heading.
- [x] DB direction verified: card 3 is Done, its `SpecDoc.path` (via `card.spec`) points at the archived path, its 8 `CardGlossaryTerm` rows match the terms CSV one-row-per-anchor, and the spec-003 `GlossarySpecMention` rows point at the archived path (a stale row reported, not fixed).
- [x] `import_spec_terms --check` and `check_spec_glossary.py --spec` both re-run and quoted, after any DB write rather than before.
- [x] Staged-anchor sweep run and its **decomposition** published: the source-tree grep returns 0, and every remaining hit is classified per file as a descriptive `.md` quotation.
- [x] The card-052 cluster — three sites closed by R2, one genuine divergence — recorded **once** as a deferred maintainer decision, with no surface partial-fixed and neither `KANBAN.md` nor spec-003 edited toward the card's prescription.
- [x] No package source, test file, sibling spec (beyond the one authorized `spec-004` sentence), terms CSV, `CHANGELOG.md`, or rendered markdown hand-edit in the diff.
- [x] `check_trailing_commas.py --check` passes on every file this item wrote, and `AGENTS.md` rule 27 holds in each (no raw `path:NN` outside this `bld-*.md`).

---

## Build report (Worker 2)

**Verdict.** The O4 record is complete and consistent across `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/README.md`, and `KANBAN.md`, in all three cross-reference directions, in the kanban DB, and in the terms-CSV importability chain — with **one exception**, which was drift and was fixed through the ORM: card `DONE-003-0.0.2`'s `Verified in upstream` `CardItem` named a walker binding (`full_path`) that `_plan_prefetch_relation` no longer has, and in doing so asserted the pre-D11 field-name lookup vocabulary the package deliberately abandoned. So the disposition is A5's **second** branch, not the expected first.

Working tree re-derived at the start of the pass rather than trusted: `git rev-parse HEAD` -> `4d1c512aaaa4338c96341542d94509f34555854e` (unchanged from the plan); `git status --porcelain` carried exactly this cycle's five paths and nothing else. **No mid-pass churn from a concurrent session appeared**, so nothing is reported under `AGENTS.md` rule 34.

### Files touched

Per-site disposition, in the form the plan requires — never one blanket sentence.

- `examples/fakeshop/db.sqlite3` — **written, one row.** `CardItem` pk `950` (card 3, section `verified_upstream`), through `uv run python examples/fakeshop/manage.py shell` and the Django ORM (`.save()`), never raw SQL. The single substitution, asserted to match exactly once before applying: `` `Prefetch(full_path, queryset=child_queryset)` `` -> `` `Prefetch(lookup_path, queryset=child_queryset)` ``. Nothing else in the row, the card, or the DB was changed.
- `KANBAN.md` — **regenerator output only** (`scripts/build_kanban_md.py`). `git diff --stat -- KANBAN.md` -> `1 file changed, 1 insertion(+), 1 deletion(-)`; the one changed line is `:4851`, the `Verified in upstream` bullet. No hand-edit.
- `KANBAN.html` — **regenerator output only** (`scripts/build_kanban_html.py`). Carries the same one-token change (`grep -c 'lookup_path, queryset=child_queryset' KANBAN.html` -> `1`). Its hand-edited Vue shell was not touched.
- `docs/GLOSSARY.md` — **no drift, no write.** `scripts/build_glossary_md.py` was re-run for completeness and the file is byte-identical to `HEAD`: `git diff --stat -- docs/GLOSSARY.md` returns **0 lines**.
- `docs/TREE.md` — **no drift, no DB write, no regenerate needed.** `uv run python scripts/build_tree_md.py --check` -> `docs/TREE.md is up to date.` exit 0.
- `docs/README.md` — **no drift, nothing written.** Hand-authored; read at its current (post-`1f4b3265`) content.
- `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` — **deliberately untouched.** The B4 rider still reads `once those land` at `:154`, and `git diff --stat` over that path returns 0 lines. That is step B's expected state, reserved to Worker 1 at final verification.
- `docs/builder/bld-003-r3-doc_completion_archive.md` — this build report, the `Status: built` transition, and the checklist ticks.
- `docs/builder/worker-memory/worker-2.md` — memory entry (gitignored).

Not in the diff, confirmed by `git status --short`: any package source, any test file, any spec file, `docs/SPECS/appx/spec-003-…-terms.csv`, `CHANGELOG.md`, `docs/builder/build-003-…md`, `bld-003-r1-…`, `bld-003-r2-…`.

### The audit, per site

**A1. `docs/GLOSSARY.md` — GENERATED. No drift.**

| Site | Result |
|---|---|
| `## \`DjangoOptimizerExtension\`` "Shipped behavior" list (`:725`-`:741`, **15** bullets — `sed -n '725,742p' docs/GLOSSARY.md \| grep -c '^- '` -> `15`) | The bullet `- nested prefetch chains for nested GraphQL selections` (`:733`) accurately names the shipped O4 surface. All four O4-adjacent siblings are true as written: `select_related` for safe single-valued relation chains (`:730`, matches `walker.py::_plan_select_relation #"append_unique(plan.select_related, full_path)"`); `prefetch_related` for many-side relations (`:731`); generated `Prefetch` objects for child querysets (`:732`, `::_plan_prefetch_relation #"append_prefetch_unique("`); connector-column inclusion (`:735`, `::_ensure_connector_only_fields`). **Accurate; terse by design and therefore a pass** per the plan's DRY note — no spec prose was imported into it |
| The entry's `**Status:** shipped (\`0.0.2\`)` line (`:714`) | **Read, not touched.** Unchanged. The `0.0.2`-versus-`0.0.3` dating question is card `TODO-ALPHA-052-0.1.0`'s by that card's own words; recorded as out of scope |
| The eight card-3 anchors | All eight exist as real headings, checked by slugging every `^#{1,6}` heading in the file rather than by eye: `fk-id-elision` -> `FK-id elision`; `only-projection` -> `` `only()` projection ``; `plan-cache` -> `Plan cache`; `queryset-diffing` -> `Queryset diffing`; `optimizerhint` -> `` `OptimizerHint` ``; `metaoptimizer_hints` -> `` `Meta.optimizer_hints` ``; `schema-audit` -> `Schema audit`; `djangotype` -> `` `DjangoType` ``. Zero missing. Nothing in the entry contradicts the reconciled spec |

**A2. `docs/TREE.md` — script-rendered. No drift.** Both renderings of the `optimizer/` subtree (`:249`-`:262` and `:371`-`:384`) were read, and the six named modules' module docstrings were read at source.

- (i) *Staging language:* `sed -n '249,262p;371,384p' docs/TREE.md | grep -nEi 'planned|slice [0-9]|TODO\(|not yet|deferred|will be|future'` -> **no match**. At source, `grep -rnEi 'planned|Slice [0-9]|TODO\(|not yet implemented' django_strawberry_framework/optimizer/*.py` returns hits that are **all** the `planned_resolver_keys` / `DST_OPTIMIZER_PLANNED` runtime vocabulary or the strategy-protocol "planned" verdict — none is staging language. `grep -rn 'TODO(' django_strawberry_framework/optimizer/*.py` returns exactly three: `selections.py:377` `TODO(BACKLOG polymorphic_interface_connections`, and `walker.py:464` / `:1131`, both `TODO(spec-035)`. **Zero `TODO(spec-003`.**
- (ii) *Factual falseness about the O4 surface:* none found in `walker.py`, `plans.py`, `nested_planner.py`, `join_taxonomy.py`, `selections.py`, or `extension.py`. `walker.py`'s `::_plan_prefetch_relation` docstring states the instance-accessor rule (D11) correctly and at length; `plans.py`'s module docstring enumerates the eleven-field plan including `planned_resolver_keys` and the `finalized_*` metadata (D5); `extension.py`'s docstring states the root gate and the O6 `Prefetch` downgrade correctly.
- **No docstring was edited.** Nothing needed one, so the record-and-escalate path was not exercised.
- The render is current: `uv run python scripts/build_tree_md.py --check` -> `docs/TREE.md is up to date.` exit 0.

**A3. `docs/README.md` — hand-authored. No drift.** Read at current content. `:53` (singleton-in-a-factory / plan cache), `:55` ("the optimizer extension turns nested selections into Django ORM `select_related`, `prefetch_related`, and `only` calls"), `:87`-`:89` (root queryset; one walk at the root; "Nested relations become joins, prefetches, projections, and strictness checks without replacing your queryset"), and `:106` (the `DjangoOptimizerExtension` bullet, including the `0.0.9` connection-aware and `0.0.10` G1/G2 riders) are all accurate about nested-selection planning against the reconciled spec. Nothing written.

**A4. `KANBAN.md` — GENERATED. One drift, fixed via the ORM.**

| Site | Result |
|---|---|
| `:41` (the O1-O6 line) | Correct: "O1 through O6 are implemented: relation resolvers, root-gated planning, **nested prefetch chains**, `only()` projection, and `get_queryset`-aware `Prefetch` downgrade." No edit |
| `:144` (spec-link row) and `:4819` (card `Spec:` line) | Both point at the **archived** path `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md`. Correct. No edit |
| Card body `Scope` x3 | All three read correctly against the reconciled spec's `## Implementation design` / `## Definition of done`. No edit |
| Card body `Note` x1 | "Design record for the O4 slice split out from the broader optimizer foundation" — correct, and matches `spec-002 ## Purpose`. No edit |
| Card body `Verified in upstream` x1 | **DRIFT — fixed.** See below |
| The single unticked `CardItem` (`Verified in upstream`, `is_complete=False`) | Board convention, card 2 matches. **Not drift, no edit**, exactly as the plan pre-decided |

*The one drift, and why it is drift rather than terseness.* The `Verified in upstream` item claimed, in the present tense about current source, that `` _plan_prefetch_relation` emits `Prefetch(full_path, queryset=child_queryset)` ``. `_plan_prefetch_relation` has **no `full_path` binding at all** — neither parameter nor local (`django_strawberry_framework/optimizer/walker.py::_plan_prefetch_relation`, whose signature is `(sel, django_field, target_type, plan, prefix, info, runtime_paths, resolver_identities, *, enable_only=True)`); it computes `lookup_path = f"{prefix}{instance_accessor(django_field)}"` and emits `append_prefetch_unique(plan.prefetch_related, Prefetch(lookup_path, queryset=child_queryset))`. `full_path` **does** exist elsewhere in the module (`::_plan_select_relation` and `::_walk_selections`) and is **field-name** vocabulary — which is precisely the vocabulary the D11 bug fix (`2d3f5fad`) removed from the prefetch lookup, because a reverse relation without `related_name` has field name `book` and accessor `book_set`. The reconciled spec states the corrected contract directly in `### Prefetch-boundary recursion for many-side and downgraded paths`: "Wrap the result in a `Prefetch` whose lookup segment is the relation's **instance accessor**, not its field name". So the card asserted, of current source, the exact shape the spec now forbids. The fix is the minimal one-token correction that makes the sentence true while leaving the upstream-parity claim (which is about `Prefetch(path, queryset=field_qs)` on the strawberry-django side) untouched.

**A5. Disposition — ORM edit plus regenerate, with byte-stability evidence.**

1. **ORM, never raw SQL, never a hand-edit of rendered markdown.** `manage.py shell` -> `CardItem.objects.get(pk=950)`, `assert i.text.count(old) == 1` before substituting, `i.save()`. The `post_save` side-row the render needs is therefore intact.
2. **Regenerated all three from the repo root**, in the plan's order: `build_kanban_md.py`, `build_kanban_html.py`, `build_glossary_md.py`.
3. **Two-consecutive-regenerate byte-stability, NOT "`git diff` is clean".** Both regenerate rounds produce identical `shasum -a 256`:

   ```text
   01ccc223e993141d736e5c6ce085cf8d94eb272e22064c772ab9201b5a79607e  KANBAN.md
   d0cbf1823ed519c17348d0d874a4241e86f48be9d9a992d1df0dd6c2dd6ed093  KANBAN.html
   563206856eabd961f2ded7035c1a6b275a9b2a74694e5051ad5aa361b03a3cbe  docs/GLOSSARY.md
   ```

   Spot-checks of the rendered result: `grep -n 'lookup_path, queryset=child_queryset' KANBAN.md` -> one hit at `:4851`; `grep -c … KANBAN.html` -> `1`.
   Pre-write freshness was established first, so the diff is attributable: before any DB write, all three `--check` modes exited **0** (`build_kanban_md.py --check`, `build_kanban_html.py --check`, `build_glossary_md.py --check`), i.e. the rendered docs were already in sync with the DB and every byte that moved afterwards is this pass's.
4. **Applied on top of concurrent state, nothing reverted.** No concurrent state existed to apply on top of this pass — the DB was clean at `HEAD` when the write began. The DB was compared by **`iterdump()` semantics, never file bytes** (`git show HEAD:examples/fakeshop/db.sqlite3` into the session scratchpad **outside** the repo, then a statement-level diff): **2 differing statements**, both halves of the single `kanban_carditem` row `950` (its `text` and its `updated_at`). Zero other rows, zero schema change. The mixed-nothing diff is handed to the maintainer.
5. **Both checks re-run AFTER the write** (quoted in `### Validation run`), plus `manage.py check`.

### The three-direction sweep and archive verification

**C1. Inbound.** `grep -rn 'spec-003' . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=shadow` -> **227 hits across 12 files**, decomposing as: `bld-003-r1-rationale_move.md` 56, `bld-003-r2-spec_reconciliation.md` 51, the rationale 30, `bld-003-r3-doc_completion_archive.md` 28, `build-003-…md` 27, `build-002-optimizer-0_0_2.md` 10, `spec-002-…-rationale.md` 9, spec-003 itself 8, `KANBAN.md` 5, `spec-002-optimizer-0_0_2.md` 1, `spec-001-…-rationale.md` 1, `KANBAN.html` 1.

**Decomposed out as not table rows,** as the plan requires I say so explicitly: spec-003's own 8 self-references (all `[rationale file][spec-003-rationale]` uses plus the one link definition), the rationale's 30 self/parent references, and this cycle's four `bld-003-*` / `build-003-*` artifacts (162 hits) — per-cycle scratchpads that close with the cycle.

Every row of the build plan's `### Every reference TO spec-003` table, re-verified per row:

| Table row | Verified | Edited? |
|---|---|---|
| `KANBAN.md:144`, `:4819` (+ `KANBAN.html`) | Both name the archived path verbatim; `KANBAN.html` carries 1 hit, same path | No |
| `KANBAN.md:240`, `:317` — card 052 scope items | Present and unchanged. `:317` still names all four stale sites; see `### The card-052 cluster` below | **No — deliberately** |
| `docs/SPECS/spec-002-optimizer-0_0_2.md` `## Purpose` (`:6`) | "the detailed O4 design and implementation record belongs to `docs/SPECS/spec-003-…`" — correct and load-bearing; it is the clause that makes spec-003 the O4 record | No (read-only sibling) |
| the two prior rationale files | `spec-002-…-rationale.md` **9** hits, `spec-001-…-rationale.md` **1** hit (`:341`). Both narrate the optimizer split as history; correct | No (read-only) |
| `docs/builder/build-002-optimizer-0_0_2.md` | **10** hits (the plan's table said 5 — restated here as measured, not as recorded). Correct as history | No |

**One row the plan's table does not carry, reported rather than fixed:** `KANBAN.md:314` is a **fifth** `KANBAN.md` occurrence of `spec-003`, in a card-052-adjacent scope item about `spec-002`'s `## Visibility status`. Its closing clause — "`spec-003-…`'s 'current state, visibility status, and checklist' instruction is now stale in wording: it is a discharged when-O4-ships note naming a section that no longer exists" — describes a spec-003 site that **R2 closed**. It belongs to the same card-052 cluster and is routed there, not fixed here.

**C2. Outbound — every link definition resolves.** Both files were partitioned at `<!-- LINK DEFINITIONS -->`, each `[ref-id]: path` parsed, each path resolved **from that file's own directory** and `exists()`-checked, each `#anchor` fragment slugged against the target's real headings, and body references cross-checked against definitions (fenced code stripped first, so a fenced example cannot manufacture a phantom reference).

- `docs/SPECS/spec-003-…md`: **10 definitions, 10 distinct references, 0 unresolved, 0 undefined, 0 unused.** The eight `../GLOSSARY.md#…` targets all resolve to real headings; `appx/spec-002-…-rationale.md` and `appx/spec-003-…-rationale.md` both exist.
- `docs/SPECS/appx/spec-003-…-rationale.md`: **19 definitions, 19 distinct references, 0 unresolved, 0 undefined, 0 unused.** The two-levels-below depth is correct in both shapes the plan warned about — `../../../AGENTS.md` and `../../builder/BUILD.md` for out-of-`docs/SPECS/` targets, `../spec-NNN-….md` for `docs/SPECS/` siblings, bare `spec-002-…-rationale.md` for an `appx/` sibling. **All nine `#anchor` fragments into spec-003 resolve to real headings**, including `#plan-shape` (R2's rename of `## Current state`) and `#documentation-updates-when-o4-ships`. This is the exact shape a same-named file one level up can mask, so it was `exists()`-tested rather than eyeballed.

**C3. The kanban DB — re-confirmed, all four checks, read-only.** Read through the ORM using the **`card.spec`** reverse accessor the plan pinned (not `card.spec_doc`, which returns `None` and reads as a missing row):

| Check | Read now | Matches plan |
|---|---|---|
| `Card.objects.get(number=3)` | `card_id` `DONE-003-0.0.2`, `status.key` `done`, `target_version.number` `0.0.2`, title `Optimizer O4 nested prefetch chains` | Yes |
| `card.spec` | name `spec-003-optimizer_nested_prefetch_chains-0_0_2`, `path` `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` — the **archived** path. `url` is the derived read-only property and was not assigned | Yes |
| `card.glossary_links.count()` | **8**: `djangotype`, `fk-id-elision`, `metaoptimizer_hints`, `only-projection`, `optimizerhint`, `plan-cache`, `queryset-diffing`, `schema-audit` | Yes |
| `card.items` | **5** `CardItem`s — `Scope` x3 complete, `Verified in upstream` x1 incomplete, `Note` x1 complete. The unticked row is board convention; **not drift, no edit** (its *text* was corrected, its completion flag was not) | Yes |

**`GlossarySpecMention` rows for spec-003:** **8 rows, every one at `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md`** — the archived path. **Zero orphans at a pre-archive `docs/spec-003-…md` path.** The `import_spec_terms::_sync_spec_mentions` orphaning behaviour card 052 records did not leave residue here; nothing to report, and nothing was fixed either way.

**C4. The terms-CSV importability chain.** `docs/SPECS/appx/spec-003-…-terms.csv` carries **8 rows / 8 distinct anchors** — one row per anchor, which is what `import_spec_terms`'s unique constraint requires and what a green `check_spec_glossary` does not prove. The anchor set is **identical** to the DB's 8 `CardGlossaryTerm` anchors, element for element. The CSV was opened **read-only** and never written.

### D. Staged-anchor sweep — the decomposition, not a bare count

1. **The mechanical source-tree test, run and reported first:**

   ```shell
   grep -rEn 'TODO\(spec-003|TODO-(ALPHA|BETA|STABLE)-003' django_strawberry_framework/ tests/ examples/ scripts/ | wc -l
   ```

   -> **0**. A staged anchor can only live in source, so the classification question is closed for source and every remaining hit is by construction a `.md` hit.

2. **Whole-tree sweep:** `grep -rEn 'TODO\(spec-003|TODO-(ALPHA|BETA|STABLE)-003' . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=shadow` -> **22 hits across exactly five `.md` files**: the rationale 6, `bld-003-r1-rationale_move.md` 7, `bld-003-r2-spec_reconciliation.md` 4, `build-003-…md` 4, `bld-003-r3-doc_completion_archive.md` 1.

   The plan measured **21 across four files** at planning time. The delta is **+1, in `bld-003-r3-doc_completion_archive.md` itself** — Worker 1's own step-D prose, which quotes the anchor form while defining the discrimination test. Measured now, not carried forward.

3. **Every hit read and classified descriptive.** The rationale's six are accounts of anchors that were removed ("the `TODO(spec-003…)` anchor marking where recursion", "**Claims the spec no longer makes.** That the relation-dispatch block carries a `TODO(spec-003…)`", "*Why it went.* Every sentence is false at HEAD. No `TODO(spec-003…)` anchor survives anywhere"). The four scratchpad files' hits are the same account plus the discrimination rule itself. **Zero instructional anchors.** `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` return no hit at all, so the plan's step-5 exclusion never had to be applied.

**Zero staged anchors survive.** `BUILD.md` `## Cross-slice integration pass` step 6 is discharged for this cycle.

### The card-052 cluster — recorded once, no surface partial-fixed

Recorded here and carried into `### Notes for Worker 1 (spec reconciliation)` as a deferred **maintainer** decision. Nothing was edited toward it in either direction.

- **Three sites closed by R2**, per the plan: the `plan_optimizations` arity plus `_collect_scalar_only_fields` present tense (`KANBAN.md:317`); the discharged when-O4-ships instruction naming a `## Current state` section that no longer exists (`:317`, and again in the `:314` clause reported under C1); the request that a later pass update the parent spec's older O4 references, which the spec-002 cycle did.
- **The fourth is a divergence, not a defect.** Card 052 prescribes replacing spec-003's opening claim so that "the replacement states that O4 is shipped and that its record is this spec's"; **R2 deliberately rejected that disposition** and recorded its reasoning in the rationale under `` ### `## Problem statement` ``. Editorial call between a board scope note and a shipped reconciliation — the maintainer's.
- **Neither `KANBAN.md` nor spec-003 was edited toward the card's prescription**, and retiring the three discharged scope items on card 052 was left to card 052's own closeout. The one `CardItem` this pass did write (`Verified in upstream`, pk 950) is **not** one of card 052's four named sites and is on a different card entirely.

### Tests added or updated

**None; this item lands no source and no test.** Stated explicitly rather than omitted, per the plan's `### Test additions / updates`. `tests/`, `examples/` code, and `django_strawberry_framework/` were read-only for the whole pass. No `pytest` was run (`AGENTS.md` rule 15), and no `--cov*` flag was used in any form. No temp/scratch test was created — there is nothing executable to develop against, so Worker 3 inherits **None.** rather than an invented one.

What replaces tests as this item's evidence is the four quoted verification commands, the per-site audit tables, the per-anchor link-resolution result, the staged-anchor decomposition, and the two-consecutive-regenerate hash equality.

### Validation run

- `uv run ruff format` / `uv run ruff check --fix` — **not run, correctly.** No `.py` file was touched this pass; `git status --short` shows zero `.py` paths. Running either would reformat files outside the slice, and that churn is not this pass's to revert.
- `git status --short` after all writes:

  ```text
   M KANBAN.html
   M KANBAN.md
   M docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md
   M examples/fakeshop/db.sqlite3
  ?? docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md
  ?? docs/builder/bld-003-r1-rationale_move.md
  ?? docs/builder/bld-003-r2-spec_reconciliation.md
  ?? docs/builder/bld-003-r3-doc_completion_archive.md
  ?? docs/builder/build-003-optimizer_nested_prefetch_chains-0_0_2.md
  ```

  Every entry is slice-intended: three are this pass's (`KANBAN.md`, `KANBAN.html`, `db.sqlite3`), and the rest are the cycle's own five paths, unchanged. **No unexplained churn, so no stop-and-report and nothing reverted.**
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` — **after the DB write**: `OK: 49 done cards have glossary links.` **exit 0** (baseline preserved).
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` — **after the DB write**: `OK: 8 terms - all have glossary entries and at least one spec link.` **exit 0**. The 8-anchor constraint holds with zero margin, so the DONE-card wrap chain for card 3 is intact.
- `uv run python examples/fakeshop/manage.py check` — `System check identified no issues (0 silenced).` **exit 0**.
- `uv run python scripts/check_trailing_commas.py --check KANBAN.md` — **exit 0** (the only `.md` this pass wrote whose content it does not author; the artifact and memory file are re-checked below).
- `uv run python scripts/build_tree_md.py --check` — `docs/TREE.md is up to date.` **exit 0**.
- Focused test commands: **none run.**

### Failability proofs

**None; this pass introduced no new boundary.** Explicitly, rather than by omission: R3 changes no executable code at all — its entire diff is one `CardItem.text` row, two regenerator outputs, and this artifact — so it adds no guard, gate, rejection path, cap, or validation branch, and `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to exactly those. The plan's `### Boundary count` independently answered **zero**, and the diff confirms it.

### Hot-path budget

**Not applicable; plan declares no hot path.** The build plan's preamble declares `Hot-path declaration: none` cycle-wide, on the ground that no residual item changes package source. This pass changed none, so nothing runs per request, per resolver, per row, per connection, or per outbound message, and no before/after number is owed.

### Floor verification

**Not applicable; plan declares floor-verification scope none.** No residual item touches a Django / Strawberry / channels integration seam, and this pass touched no framework surface whatsoever. No floor venv was built; the shared `.venv` was not mutated.

### Implementation notes

- **Why the drift was fixed rather than escalated.** The dispatch's standing constraint routes a **source-level** finding (a false docstring, an optimizer defect) to record-and-escalate. This finding is neither: it is a factually-false present-tense sentence in a **generated durable doc**, which is precisely the case plan step A5's second branch exists for, and its remedy is an ORM row edit rather than a source change. No source file was opened for writing at any point.
- **Minimal substitution over a rewrite.** The bullet's upstream half (`Prefetch(path, queryset=field_qs)` on strawberry-django's side) is correct and was left alone; only the package-side binding name was wrong. Replacing one token makes the sentence true without re-litigating the parity claim, and keeps the diff auditable to a single line in the rendered doc.
- **Pre-write freshness check before the write, not after.** Running all three regenerators in `--check` mode *before* touching the DB is what makes the post-write diff attributable to this pass. Had any returned non-zero, the DB would already have diverged from the rendered docs and a "byte-stable after two regenerates" result would have proved nothing about ownership.
- **`iterdump()` semantics for the DB comparison**, against a `git show HEAD:` copy written to the session scratchpad **outside** the repository. No `git stash`, `git checkout`, `git restore`, or `git worktree` was used anywhere in this pass.
- **The link resolver was written to the scratchpad, outside the repo**, per the plan's discretion item — never into `docs/` or `scripts/`. It strips fenced blocks before collecting body references so a fenced example cannot register as an undefined reference.

### Notes for Worker 3

- **The diff is three files plus this artifact.** `KANBAN.md` and `KANBAN.html` are **regenerator output**, not hand-edits; the only hand-authored change in the whole cycle-item is one `CardItem.text` row in `examples/fakeshop/db.sqlite3`, reachable as `CardItem.objects.get(pk=950)`. To re-derive the render independently, run the three `--check` modes: all three should exit 0 against the current DB.
- **The `spec-004` B4 rider at `:154` still reads `once those land`. That is expected, not a finding** — the edit is Worker 1's, at final verification, and `git diff` over that path is empty by design.
- **Card 3's `Verified in upstream` `CardItem` remains `is_complete=False`.** Its text was corrected; its completion flag was deliberately not touched, because the unticked row is board convention (card 2 matches) rather than drift.
- No shadow file was generated or read this pass; `scripts/review_inspect.py` was not re-run (the plan skipped it with reason, and nothing under `django_strawberry_framework/` changed).
- No temp test exists to inherit. Record `None.` under `### Temp test verification` rather than inventing one.
- The `### Documentation / release sanity` review section **is** applicable here: the diff touches KANBAN and generated docs.

### Notes for Worker 1 (spec reconciliation)

Written on disk, not only in the return report (`BUILD.md` `### Cohorting, naming, and closure`).

**Escalations and deferrals — for the final gate's `### Deferred work catalog`:**

- **Escalated: the card-052 cluster, four sites, one decision.** *Where it lives:* `KANBAN.md` card `TODO-ALPHA-052-0.1.0`, the scope items rendered at `:314` and `:317`, versus `docs/SPECS/spec-003-…md` `## Problem statement`. *Current wording (card, `:317`):* "`:4` still says the remaining O-slice is O4, though O4 shipped; the replacement states that O4 is shipped and that its record is this spec's." *Recommended disposition:* **no spec edit and no card edit by any worker.** Three of the card's four named sites are closed by R2 (the `plan_optimizations` arity and `_collect_scalar_only_fields` present tense; the when-O4-ships instruction naming a now-deleted `## Current state`; the parent-spec O4 references, done by the spec-002 cycle), and retiring them is card 052's own closeout. The fourth is a genuine divergence: the card prescribes a disposition **R2 deliberately rejected**, with the reasoning recorded in the rationale under `` ### `## Problem statement` ``. Editing either surface toward the other leaves the cluster inconsistent. **Route to the maintainer as a decision.** *(This is the fifth on-disk carrier of the divergence; it is written down repeatedly because the failure mode is a worker reconciling it in passing.)*
- **Deferred: `KANBAN.md:314` is a fifth card-052-adjacent `spec-003` site the build plan's `### Every reference TO spec-003` table does not carry.** Its clause "`spec-003-…`'s 'current state, visibility status, and checklist' instruction is now stale in wording" describes a site R2 closed. Same disposition as above: card 052's, not this cycle's. *Recommended action:* add it to the deferred catalog beside the other three closed sites so card 052's closeout sweeps five sites, not four.
- **Deferred (unchanged from the build plan, restated here only because R3 is the last item before the gate): the `docs/GLOSSARY.md` `**Status:** shipped (\`0.0.2\`)` versus `CHANGELOG.md` `[0.0.3]` optimizer dating question.** Card 052 owns it by its own words. Read and confirmed unchanged at `docs/GLOSSARY.md:714`; **not touched**.

**Two measured corrections to counts the build plan records** — reported so the final gate quotes measured numbers rather than carried-forward ones (`BUILD.md` `## Claims are proven mechanically`):

- *Where it lives:* build plan `### Every reference TO spec-003`, the `docs/builder/build-002-optimizer-0_0_2.md` row. *Current wording:* "`docs/builder/build-002-optimizer-0_0_2.md` (5 hits)". *Recommended replacement:* "(10 hits)" — `grep -c 'spec-003' docs/builder/build-002-optimizer-0_0_2.md` -> `10`. The row's *disposition* ("historical artifact; correct as history") is unaffected.
- *Where it lives:* this artifact's `### Implementation steps` step D. *Current wording:* "re-measured at R3 planning: still **21 hits across exactly four `.md` files**". *Recommended replacement:* "**22 hits across exactly five `.md` files**" — the fifth file is this artifact, which acquired one hit when Worker 1 wrote the discrimination rule into it. Zero staged anchors either way.

**No spec amendment is owed by this pass.** The reconciled spec's `### Prefetch-boundary recursion for many-side and downgraded paths` already states the instance-accessor contract correctly, and it is what proved the KANBAN card wrong — the spec was the authority here, not the thing that needed correcting.

**No source-level finding to escalate.** The read-only correctness obligation was discharged over the six `optimizer/` modules the plan named: no factually-false docstring, and no defect. The build plan's `### The read-only correctness audit` observations 1-4 were re-read and none was mistaken for drift; observation 4 (the unguarded `_record_relation_access`-before-elision ordering invariant) remains a maintainer-facing catalog note, unchanged by this pass.

---

## Review (Worker 3)

Working tree re-derived, not trusted: `git rev-parse HEAD` -> `4d1c512aaaa4338c96341542d94509f34555854e` (unmoved); `git status --porcelain` carries exactly the nine paths the build report lists and nothing else. **No mid-pass churn from a concurrent session appeared**, so nothing is recorded under `AGENTS.md` rule 34.

Nothing was written outside this review section and `docs/builder/worker-memory/worker-3.md`. **No regenerator was run in write mode** — my role permits writing only the artifact, my memory, and `docs/builder/temp-tests/r3/`, and `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` are Worker 2's. The byte-stability obligation was discharged by a strictly stronger read-only route; see `#### The regenerate is provably faithful, by a stronger test than two-consecutive-regenerate` below. No `git stash`, `git checkout`, `git restore`, or `git worktree` anywhere in this pass; the one HEAD reference used was `git show HEAD:` into the session scratchpad outside the repo.

### High:

None.

### Medium:

None. Every load-bearing claim in the build report re-derived true, including both halves of the corrected `CardItem` sentence and all four "no drift" negative findings.

### Low:

#### L1 — The C1 decomposition counts matching LINES and labels them "hits", and the one number it prescribes writing into the build plan is 10 where the occurrence count is 11

`BUILD.md` `## Claims are proven mechanically, never accepted on prose`, third bullet, names this exact failure mode and prescribes the remedy: "search the shortest distinctive token and count *occurrences*, not matching lines". Worker 2 used the shortest distinctive token (`spec-003`) but counted with `grep -c` / `grep -rn … | wc -l`, which counts lines.

Re-derived side by side (`grep -c 'spec-003' <f>` vs `grep -o 'spec-003' <f> | wc -l`):

| File | lines | occurrences |
|---|---|---|
| `docs/builder/build-002-optimizer-0_0_2.md` | 10 | **11** (`:127` carries two) |
| `KANBAN.md` | 5 | **7** |
| `KANBAN.html` | 1 | **6** (one long data line) |
| `docs/SPECS/spec-003-…md` | 8 | **9** |
| `docs/SPECS/appx/spec-003-…-rationale.md` | 30 | **42** |

The build report's 12-file set and its whole-tree total are **internally exact as line counts** — I summed the decomposition (56+51+30+28+27+10+9+8+5+1+1+1) to 227 and re-measured every non-self-referential file at the same value, so nothing here is a guess. Why it is Low and not Medium: no per-row *disposition* changes, and the C1 purpose (enumerate reference **sites** to verify) is arguably better served by a per-line unit than a per-occurrence one.

Why it is a finding at all: `### Notes for Worker 1 (spec reconciliation)` prescribes a verbatim replacement string — *"Recommended replacement: `(10 hits)`"* — that Worker 1 will paste into the build plan and the final gate will quote. **The correct occurrence count for that row is 11.** *Recommended change:* Worker 1 writes `(11 occurrences across 10 lines)` rather than `(10 hits)`, or `(10 lines)` if the line unit is intended — either is re-derivable; `hits` is not.

#### L2 — A second plan number is silently corrected in the C1 table but omitted from the "two measured corrections" list

The build plan's `### Every reference TO spec-003` prior-rationale row reads *"(8 hits)"* for the two files jointly. The build report's C1 table measures them correctly and separately (`spec-002-…-rationale.md` **9**, `spec-001-…-rationale.md` **1**), which I re-derived exact — but the joint total is **10 lines / 10 occurrences**, not 8, and this row is **not** listed under *"Two measured corrections to counts the build plan records"*, which names only the `build-002` row. A reader of that list concludes the rationale row was accurate.

Low, not Medium: the correct numbers **are** on disk in the C1 table, so nothing is unrecoverable. *Recommended change:* Worker 1 folds this into the same plan-number correction — the corrections list should carry two rows, not one.

#### L3 — The `CardItem`'s upstream-parity clause is imprecise about which upstream function performs the rebasing; recorded, and deliberately NOT routed back for a second ORM edit

Dispatch asked whether the untouched half of the sentence is still true, on the ground that a one-token fix leaving a second false clause is a half-fix. I traced all three of its sub-claims against `~/projects/strawberry-django-main/strawberry_django/optimizer.py` (`AGENTS.md` line 2):

- *"recursing through `_get_model_hints(..., level=level + 1)`"* — **true**, `::_get_hints_from_django_relation #"level=level + 1"`.
- *"emitting `Prefetch(path, queryset=field_qs)` for many-side branches"* — **true**, verbatim, `::_get_hints_from_django_relation #"field_prefetch = Prefetch(path, queryset=field_qs)"`.
- *"rebasing the child `OptimizerStore`'s `only`/`select_related` under the relation path"* — **imprecise.** The block in this function (`#"extra_only = ["`) moves entries **out of** the local `store` and **into** `field_store` with the `path__` prefix **stripped** — the opposite direction from "under the relation path" — and it is additionally inert here, because the local `store` is constructed empty (`#"store = OptimizerStore()"`) and nothing appends to its `only` / `select_related` before that block, so both `if` guards are false on every path. The prefix-adding rebase the clause evokes lives in the **sibling** function `::_get_hints_from_django_field #"store |= f_store.with_prefix(path, info=strawberry_info)"`.

*Why it is Low and is intentionally rejected rather than looped.* The clause is about **upstream's** internals, not the package's, and the parity argument the `CardItem` exists to make rests entirely on the two sub-claims that verify exact. It is also pre-existing text this diff did not introduce; R3's contract is "does the new text describe HEAD truthfully", and the new text — the package half — does. Correcting it means a second ORM write re-litigating a Done card's historical parity note for no reader-visible gain, which is precisely the "improve it while I'm here" widening the plan's `### DRY analysis` pre-decided against. **Recorded here and escalated to Worker 1** so the decision is the custodian's; it is not grounds to hold the item.

Worker 2's stated reason for leaving it — *"the upstream half … is correct and was left alone"* — is therefore right in its conclusion and one clause too strong in its wording. Naming that is what makes this an accepted residue rather than a missed defect.

### DRY findings

None, and this is a measured negative rather than a skipped section. The diff contains no executable logic: `git diff -- django_strawberry_framework/ tests/ examples/fakeshop/apps examples/fakeshop/test_query` returns **0 lines** and `git status --porcelain | grep -c '\.py$'` returns **0**. There is no duplicated logic, repeated literal, misplaced helper, or parallel data flow to flag, and no new abstraction for the **existence challenge** to interrogate. `scripts/review_inspect.py` was **explicitly skipped, with reason**: `BUILD.md` `### When to run the helper during build` triggers Worker 3 on a new `.py` file, a touched `optimizer/` or `types/` file, or 30+ new logic lines under the package — the diff meets none, because it touches no `.py` file at all. No shadow file was generated or read.

### Verification of the build report's claims

#### The DB write is correct on its merits

Re-derived at source, not accepted:

- `django_strawberry_framework/optimizer/walker.py::_plan_prefetch_relation` has **no `full_path` binding** — its signature is `(sel, django_field, target_type, plan, prefix, info, runtime_paths, resolver_identities, *, enable_only=True)` and no local of that name appears in its body. It computes `#"lookup_path = f\"{prefix}{instance_accessor(django_field)}\""` and emits `#"append_prefetch_unique(plan.prefetch_related, Prefetch(lookup_path, queryset=child_queryset))"`. **The corrected text is true of HEAD; the prior text named a binding that does not exist.**
- `full_path` **is** live elsewhere in the module and **is** field-name vocabulary — `::_dispatch_single_relation` threads it, and `::_plan_select_relation`'s own docstring says so outright (*"``full_path`` (field-name vocabulary) is correct here … the accessor swap is a ``_plan_prefetch_relation`` concern only"*). So the pre-fix sentence did not merely name the wrong local; it asserted, of the prefetch path, the exact vocabulary `::_plan_prefetch_relation`'s docstring documents as the D11 bug. Worker 2's diagnosis is confirmed, including its severity.
- The sentence's two other package-side clauses are true: `::_build_prefetch_child_queryset` does recurse one level deeper (via `::_build_prefetch_child_queryset_from_base #"_walk_selections("` on `sel.selections` into a fresh `OptimizationPlan`), and `::_plan_select_relation` does recurse through single-valued chains preserving `select_related` + `only()` (`#"append_unique(plan.select_related, full_path)"`, `#"prefix=f\"{full_path}__\""`, projection via `::_record_relation_access`).
- The upstream half is verified above under **L3**: two of three sub-claims exact, one imprecise and recorded.

The ORM row itself, read back read-only: `CardItem.objects.get(pk=950)` is on card **3**, section `verified_upstream`, `is_complete=False` (deliberately unchanged), `'full_path' in text` -> **False**, `'lookup_path' in text` -> **True**.

#### The ORM route was actually used, and the regenerate hides no hand-edit

`BUILD.md` `### Generated docs are DB-backed` exists to catch exactly a hand-edit riding inside a regenerate diff. Three independent lines of evidence, none of them the build report's own assertion:

1. `git diff -- KANBAN.md` is **one changed line** (`:4851`) and its content is the `CardItem` text.
2. `git diff --word-diff=porcelain -- KANBAN.html` reduces the whole 3.5 MB single-line data-block diff to **exactly two token changes**: `` `Prefetch(full_path,`` -> `` `Prefetch(lookup_path,``, and `"updatedDate":"2026-06-09T17:39:26.033235+00:00"` -> `"2026-08-07T17:35:25.389707+00:00"` on the same row. **That second token is affirmative proof of the ORM route**: an `auto_now` bump is produced by `Model.save()` and by nothing else — raw SQL would not have moved it, and a hand-edit of the rendered markdown could not have moved it in the HTML data block while leaving `createdDate` alone. `KANBAN.md` does not render `updatedDate`, which is why the two files' diffs differ in size by exactly one token.
3. The Vue shell `START.md` flags as hand-edited is untouched — the entire `KANBAN.html` delta is inside the data block.

#### The regenerate is provably faithful, by a stronger test than two-consecutive-regenerate

I did not re-run the regenerators in write mode (not my files). Instead I ran all three in `--check` mode, which is read-only and answers a **stronger** question than hash-equality across two writes — two consecutive regenerates agreeing proves the renderer is deterministic; `--check` proves the **on-disk file equals what the current DB renders**, which is what "no hand-edit survives" actually means:

```text
uv run python scripts/build_kanban_md.py  --check  -> KANBAN.md is up to date.        exit 0
uv run python scripts/build_kanban_html.py --check -> KANBAN.html is up to date.      exit 0
uv run python scripts/build_glossary_md.py --check -> docs/GLOSSARY.md is up to date. exit 0
```

The three `shasum -a 256` values I read match the build report's three recorded hashes **character for character** (`01ccc223…` / `d0cbf182…` / `56320685…`), so the byte-stability record is re-derivable rather than asserted. `uv run python scripts/build_tree_md.py --check` -> `docs/TREE.md is up to date.` exit 0.

#### The negative findings — sampled independently, since "no drift" at four sites is a claim

- **`docs/GLOSSARY.md` `DjangoOptimizerExtension`.** Heading at `:712`, `**Status:** shipped (\`0.0.2\`)` at `:714` (**read, unchanged, correctly out of scope** — card 052's). The "Shipped behavior" list is **15** bullets, re-counted. `- nested prefetch chains for nested GraphQL selections` accurately names the shipped O4 surface, and the four O4-adjacent siblings each trace to real code: `select_related` for safe single-valued chains -> `::_plan_select_relation`; `prefetch_related` for many-side -> `::_plan_prefetch_relation`; generated `Prefetch` objects -> `#"Prefetch(lookup_path, queryset=child_queryset)"`; connector-column inclusion -> `::_ensure_connector_only_fields`. **Terse and accurate; the entry imports no spec prose, which is the DRY outcome the plan wanted.** All eight card-3 anchors exist as real headings — checked by slugging every `^#{1,6}` heading in the file with a markup-rendering slugger, not by eye: `fk-id-elision`, `only-projection`, `plan-cache`, `queryset-diffing`, `optimizerhint`, `metaoptimizer_hints`, `schema-audit`, `djangotype` -> 8/8 `True`.
- **`docs/TREE.md` optimizer block** (`:249`-`:262`, duplicated at `:371`-`:384`). `--check` exit 0 already proves the rendered block equals the modules' real docstrings, so the only open question is the docstrings themselves. I re-ran the staging sweep at source and subtracted the runtime vocabulary: every surviving `planned` hit under `optimizer/*.py` is `planned_resolver_keys` / `DST_OPTIMIZER_PLANNED` / the strategy protocol's `PLANNED` / `UNPLANNED` verdicts. `grep -rn 'TODO(' django_strawberry_framework/optimizer/*.py` returns three, all `TODO(spec-035)` or `TODO(BACKLOG …)`. **Zero `TODO(spec-003`, zero staging language.** Worker 2's negative finding here is confirmed at the source, not at the render.
- **`docs/README.md`.** Read at current content. `:55` ("the optimizer extension turns nested selections into Django ORM `select_related`, `prefetch_related`, and `only` calls"), `:88` ("Nested relations become joins, prefetches, projections, and strictness checks without replacing your queryset"), and the `:106` `DjangoOptimizerExtension` bullet are accurate about nested-selection planning against the reconciled spec. No drift.
- **`KANBAN.md`.** `:41`, `:144`, `:4819` re-read; all correct, all naming the archived path.

#### The card-052 cluster was NOT silently reconciled

- **`KANBAN.md` untouched at both card-052 surfaces.** The whole-file diff is one line at `:4851`; `:314` and `:317` are byte-identical to HEAD and `:317` still names all four stale sites verbatim.
- **`spec-003` untouched toward the prescription.** `## Problem statement` still opens with the framing card 052 asked to replace ("O4 is the slice that plans nested relation paths"), i.e. R2's rejection stands and no worker moved either surface toward the other.
- **The escalation is on disk**, under `### Notes for Worker 1 (spec reconciliation)`, with the card's current wording quoted, the three-closed/one-divergent decomposition, and an explicit *"Route to the maintainer as a decision"* — satisfying `BUILD.md` `### Cohorting, naming, and closure` (detail living only in a return report does not reach the next worker).
- The `:314` fifth site is reported, not fixed, and routed to the same cluster. Re-derived: `grep -n 'spec-003' KANBAN.md` returns exactly **five** lines — `:144`, `:240`, `:314`, `:317`, `:4819` — so `:314` is genuinely a site the plan's table omits.

#### Archive chain, re-derived rather than accepted

- **Outbound links, re-resolved with my own parser** (scratchpad, outside the repo; fenced blocks stripped before collecting body references): `docs/SPECS/spec-003-…md` -> **10 definitions / 10 references / 0 undefined / 0 unused / 0 unresolved**; `docs/SPECS/appx/spec-003-…-rationale.md` -> **19 / 19 / 0 / 0 / 0**. Every path `exists()`-checked from its own file's directory, so the depth trap (`../../../AGENTS.md`, `../../builder/BUILD.md`, `../spec-NNN-….md`, bare `spec-002-…-rationale.md`) is tested rather than eyeballed. **All nine `#anchor` fragments into spec-003 resolve to real headings, `#plan-shape` included**, plus the eight `../GLOSSARY.md#…` fragments. Matches the build report exactly.
- **DB chain, read read-only through the ORM:** card 3 -> `DONE-003-0.0.2` / `done` / `0.0.2` / `Optimizer O4 nested prefetch chains`; `card.spec` -> `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md`, the **archived** path; `card.glossary_links` -> **8 rows, 8 distinct anchors**; `card.items` -> **5**, `(scope, True) x3`, `(verified_upstream, False)`, `(note, True)`; `GlossarySpecMention` for spec-003 -> **8 rows, every one at the archived path, zero pre-archive orphans**. All four match the build report.
- **Terms CSV:** 8 data rows, **8 distinct anchors**, element-for-element identical to the DB anchor set. `git status` shows the CSV is not modified — it was opened read-only, as required.
- **Validation commands, re-run by me after the write:** `import_spec_terms --check` -> `OK: 49 done cards have glossary links.` exit 0; `check_spec_glossary.py --spec …spec-003…` -> `OK: 8 terms - all have glossary entries and at least one spec link.` exit 0. Both reproduce the build report's quoted output verbatim.
- **Staged-anchor sweep, re-run:** the mechanical source-tree test `grep -rEn 'TODO\(spec-003|TODO-(ALPHA|BETA|STABLE)-003' django_strawberry_framework/ tests/ examples/ scripts/` -> **0**, confirmed. Whole tree now returns **24** across the same five `.md` files; the delta from the build report's 22 is **+2 in this artifact**, both introduced by Worker 2's own step-D prose (`1` -> `3` hits in `bld-003-r3-…md`), so 22 was correct when measured. Worker 2's correction of the plan's "21 across four files" to "22 across five" is re-derived **exact**, self-growth accounted for. **Zero instructional anchors survive**; `BUILD.md` `## Cross-slice integration pass` step 6 is discharged.
- `check_trailing_commas.py --check` -> exit 0 on `docs/builder/bld-003-r3-doc_completion_archive.md` and `KANBAN.md`. A rule-27 sweep for raw `path:NN` refs across the spec and the rationale returns **zero** (raw refs are legal only inside this `bld-*.md`).

#### Checklist walk — all 14 boxes

| # | Box | Verdict |
|---|---|---|
| 1 | `docs/GLOSSARY.md` audited | `[x]` **justified** — 15 bullets, O4 bullet + 4 siblings traced to code, 8/8 anchors |
| 2 | `docs/TREE.md` optimizer subtree audited | `[x]` **justified** — `--check` 0 + source-level staging sweep clean |
| 3 | `docs/README.md` audited | `[x]` **justified** — four cited sites re-read, accurate |
| 4 | `KANBAN.md` audited | `[x]` **justified** — `:41` / `:144` / `:4819` / card body |
| 5 | Disposition in the required form | `[x]` **justified** — A5 branch two, ORM + regenerate, byte-stability evidence reproduced |
| 6 | `spec-004` B4 rider retired | `[ ]` **correctly open** — `sed -n '154p'` still reads `once those land`; `git diff --stat` over that path is empty. Worker 1's, at final verification. Not a defect, and not an undeferred box: the plan and the build report both state the reservation |
| 7 | Inbound verified | `[x]` **justified** — sweep re-run, every table row reported per row (count unit is L1) |
| 8 | Outbound verified | `[x]` **justified** — independently re-derived 10/10 and 19/19 with 0/0/0 |
| 9 | DB direction verified | `[x]` **justified** — all four checks plus the 8 archived-path mentions re-read |
| 10 | Both checks re-run after the write | `[x]` **justified** — I re-ran both; identical output, exit 0 |
| 11 | Staged-anchor decomposition published | `[x]` **justified** — source grep 0 re-derived; whole-tree delta explained |
| 12 | Card-052 cluster recorded once, no partial fix | `[x]` **justified** — both surfaces byte-unmoved, escalation on disk |
| 13 | No source / test / sibling spec / CSV / CHANGELOG / rendered hand-edit | `[x]` **justified** — source+test diff 0 lines, 0 dirty `.py`, CSV and `CHANGELOG.md` and `spec-004` unmodified, generated docs proven pure by `--check` |
| 14 | `check_trailing_commas --check` + rule 27 | `[x]` **justified** — exit 0 on both written `.md` files; rule-27 sweep clean |

**No over-tick and no silently-unaddressed box.** The single `- [ ]` is the one the plan and the dispatch both reserve to Worker 1.

#### Reporting obligations

- **`### Failability proofs`** — the statement *"None; this pass introduced no new boundary"* is present and **verified rather than assumed**: `git diff -- django_strawberry_framework/ tests/` returns 0 lines, so the diff introduces no guard, gate, cap, or rejection path anywhere. Per `worker-3.md` "Reading is necessary, not sufficient", **an empty re-run set is legal only when the diff introduces no boundary meeting the floor** — that condition holds here mechanically, so **I re-ran no proof and accepted none on Worker 2's record; there were none to do either with.** The plan's independent `### Boundary count` of zero agrees.
- **`### Hot-path budget`** — explicit statement present (`Not applicable; plan declares no hot path`), and correct: the plan preamble declares `Hot-path declaration: none`, and no code runs per request / resolver / row / connection / message because no code changed.
- **`### Floor verification`** — explicit statement present and correct; no framework seam touched, shared `.venv` unmutated.
- **No `.py` file was touched** — 0 dirty `.py` paths; skipping `ruff format` / `ruff check --fix` was right, and running them would have churned files outside the slice.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returns **0 lines** — `__all__` and the re-export list are unchanged. No new public exports, as the item's contract requires.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify `CHANGELOG.md`. Confirmed by `git status --porcelain`.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Applicable — the diff touches KANBAN and generated docs.

- **Version strings and card IDs.** `DONE-003-0.0.2` / target version `0.0.2` / archived spec filename ending `-0_0_2.md` all still agree; nothing in the diff moved any of them. The `docs/GLOSSARY.md` `0.0.2`-versus-`CHANGELOG.md` `0.0.3` dating question was read and left untouched, correctly — card 052 owns it by that card's own words.
- **No card moved sections**, so the removed-from-old / appears-once-in-target check is vacuous; the write was a `CardItem.text` substitution on a card already in `DONE`.
- **Markdown links.** Every link in both spec-003 files resolves on disk with its fragment (10/10 and 19/19 above). The diff introduced no new link.
- **Archival.** The archived-path record is intact in all three of its carriers — `SpecDoc.path`, the eight `GlossarySpecMention` rows, and `KANBAN.md:144` / `:4819` — and the live follow-up source of truth stays in `KANBAN.md` card 052, which was deliberately not edited.
- **Script-rendered docs.** `docs/TREE.md` is script-rendered; its feeding docstrings carry **no** staging language (verified at source above), and the render is current (`--check` exit 0). Distinguishing staging language from provenance was needed and performed: the `TODO(spec-035)` and `TODO(BACKLOG …)` anchors under `optimizer/` are other specs' live stages, out of this cycle's scope, and the `planned` / `PLANNED` tokens are runtime vocabulary, not staging.
- **No obsolete "coming soon" / "planned" / old-version wording** remains in any file the slice deliberately updated.
- **No verbatim spec copy** in the diff, so the character-for-character `diff`-against-spec check does not apply; the corrected `CardItem` text is card prose, not spec text.

### What looks solid

- **The drift itself is a genuinely good catch, and it is the kind an audit usually misses.** The stale sentence was on the one `CardItem` a reader is least likely to re-check — a shipped Done card's upstream-parity note, twelve releases old — and it was wrong in the most specific way available: it named a binding that does not exist, in the exact vocabulary the D11 fix removed from that code path, which is to say it asserted of current source the shape the reconciled spec now forbids. Finding it required reading the walker rather than reading the card.
- **The remedy was scoped to what was false.** One token, no rewrite of the parity claim, no import of spec prose into the durable doc. The plan's DRY analysis named "improve the entry while I'm here" as this item's single largest temptation; the build resisted it at the glossary and at the card alike.
- **Pre-write `--check` freshness on all three renderers, before touching the DB.** This is the step that makes the post-write diff attributable, and it is not one the plan spelled out — it is Worker 2's own addition, recorded with its reasoning under `### Implementation notes`. Without it, byte-stability after the write would have proved determinism and nothing about ownership.
- **Every negative finding is stated per site with the evidence attached**, which is what made this review re-derivable instead of a re-audit. Four "no drift" sites, four different verification instruments (`--check`, source grep, heading slug, read).
- **`iterdump()` semantics against a `git show HEAD:` copy outside the repo**, with no banned git verb anywhere in the pass. The concurrent-writer discipline held end to end.
- **The card-052 divergence survived a fifth pass unreconciled.** That is the whole point of writing it down five times, and the temptation to "just fix the wording" is highest on the last item before the gate.

### Temp test verification

**None.** No temp test was created, and none was inherited. `docs/builder/temp-tests/r3/` was not used: the item lands no executable code, so there is nothing a temp test could pin that reading and the read-only verification commands do not already establish. The one scratch script this pass wrote (the independent link resolver) lives in the session scratchpad **outside the repository**, per `BUILD.md`'s scratch-path rule, and is not a test.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (L3): the `CardItem` pk 950 upstream clause is imprecise about which upstream function rebases.** *Where it lives:* `KANBAN.md:4851` / `CardItem.objects.get(pk=950)`, the clause "rebasing the child `OptimizerStore`'s `only`/`select_related` under the relation path". *Evidence:* in `::_get_hints_from_django_relation` the movement is out of the local store and into the child with the `path__` prefix **stripped**, and both its `if` guards are inert because the local `store` is constructed empty and never gains `only` / `select_related` entries; the prefix-adding rebase lives in `::_get_hints_from_django_field #"store |= f_store.with_prefix(path, info=strawberry_info)"`. *Resolution paths:* **(a)** leave it — my recommendation; the parity argument rests on the two verified sub-claims, the clause describes upstream rather than this package, and a second ORM write on a Done card's historical note buys no reader anything; **(b)** fold a one-clause correction into card 052's closeout, where the other spec-003 record work already lives; **(c)** correct it now via a second ORM edit plus regenerate. I did **not** hold the item on this.
- **Two plan-number corrections, superseding the build report's one (L1 + L2).** The build report's `### Notes for Worker 1` prescribes replacing the plan's `build-002` row with `(10 hits)`. Use **`(11 occurrences across 10 lines)`** instead — `grep -c` counts lines, and `BUILD.md` `## Claims are proven mechanically` prescribes occurrences. And the **prior-rationale row** needs the same treatment: the plan says `(8 hits)`, measured is `9 + 1 = 10` lines / 10 occurrences, correct in the build report's C1 table but absent from its corrections list. Two rows to correct, not one.
- **Carried forward unchanged, not re-adjudicated:** the card-052 four-site cluster (three closed by R2, one a genuine divergence R2 deliberately rejected), the `KANBAN.md:314` fifth site, and the `docs/GLOSSARY.md` `0.0.2` / `CHANGELOG.md` `0.0.3` dating question. I verified all three are recorded on disk with their evidence and that **neither surface was moved toward the other**. Route to the maintainer as the build report recommends; nothing in this review changes that disposition.
- **The `spec-004` B4 rider is the one live obligation left in this cycle.** `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:154` still reads `once those land`; spec-003's `## Documentation updates when O4 ships` still carries it as the single open item ("One obligation from this list is still open"). Worker 2 correctly left both alone. When the rider is retired, the spec's own section becomes empty — the plan already flags that as a custody decision to record in the rationale, not in the spec.
- **No spec amendment is owed by this review.** The reconciled spec was the authority that proved the card wrong, not a thing needing correction — `### Prefetch-boundary recursion for many-side and downgraded paths` already states the instance-accessor contract, and `::_plan_prefetch_relation`'s docstring states the same rule at source. Spec, docstring, and (now) card agree.

### Review outcome

`review-accepted`.

Three Lows, all recorded with their evidence and their disposition: **L1** and **L2** are count-unit corrections whose corrected numbers are now on disk in this section, positioned so no reading order reaches Worker 1 uncorrected; **L3** is intentionally rejected in-place with its reason and escalated to Worker 1 for the custody call. No High and no Medium survived verification: both halves of the corrected sentence were traced to source, the ORM route was proved affirmatively by the `auto_now` token in the `KANBAN.html` data block, the regenerate was proved faithful by a stronger read-only test than the one the plan asked for, all four "no drift" negatives were re-sampled with independent instruments, both card-052 surfaces are byte-unmoved, and all 14 checklist boxes carry the work they claim.

---

## Final verification (Worker 1)

Working tree re-derived, never trusted from the dispatch: `git rev-parse HEAD` -> `4d1c512aaaa4338c96341542d94509f34555854e` (unmoved across all three items). `git status --porcelain` before my edits carried exactly the nine paths Worker 2 and Worker 3 both list; **no concurrent-session churn appeared during this pass**, so nothing is recorded under `AGENTS.md` rule 34 and nothing was reverted. No `git stash`, `git checkout`, `git restore`, or `git worktree` anywhere in this pass; the one HEAD reference used was `git show HEAD:examples/fakeshop/db.sqlite3` into the session scratchpad **outside** the repository.

### Summary

R3 discharged the cycle's last obligation. The `spec-004` B4 rider is retired, spec-003's now-empty `## Documentation updates when O4 ships` section was resolved deliberately rather than left asserting an open item, and the durable-doc / cross-reference / DB / terms-CSV / staged-anchor audit is confirmed complete. Worker 2's one genuine drift find — card `DONE-003-0.0.2`'s `Verified in upstream` `CardItem` naming a `full_path` binding `_plan_prefetch_relation` does not have — is verified correct at source and verified to have reached `KANBAN.md` / `KANBAN.html` through the ORM and a regenerate, with nothing else riding in the diff. `final-accepted`.

### The one piece of work this pass owed — performed

**`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:154`, the B4 `**Depends on.**` line.** One clause retired; nothing else in `spec-004` opened. `git diff --numstat` over that path -> `1  1`, i.e. a single line changed:

```text
-**Depends on.** O3 (shipped). The `SKIP` hint is independent of O4-O6. The `.prefetch(Prefetch(...))` hint composes naturally with O4 (nested chains) and O6 (downgrade rule) once those land.
+**Depends on.** O3 (shipped). The `SKIP` hint is independent of O4-O6. The `.prefetch(Prefetch(...))` hint composes naturally with O4 (nested chains) and O6 (downgrade rule).
```

The clause is **retired, not rewritten to announce the landing**. `BUILD.md` `## Spec rationale extraction` forbids a spec narrating its own history, so "and both have since landed" or "as of `0.0.2`" would have replaced one falsified sentence with a chronological one; and `spec-004`'s own `## Current state` already records O4 and O6 as shipped, so a second statement of that fact is the copy that rots. What holds now is that the hint composes — stated directly.

Post-edit verification, both quoted:

```text
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
  -> OK: 10 terms - all have glossary entries and at least one spec link.   exit 0
uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
  -> (no output)   exit 0
```

`AGENTS.md` rule 27 holds in the edited line: `awk 'NR==154' … | grep -cE '[a-zA-Z_/]+\.(py|md):[0-9]+'` -> **0**. And `grep -c 'once those land' docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **0**, so no second instance of the rider survives anywhere in the file.

The plan's other observation is confirmed rather than assumed: the remaining `Depends on.` lines that mention O4-O6 say "Independent of O4-O6", a true statement of independence rather than a rider, and none was touched.

### The custody decision the rider edit forced

Retiring the rider made spec-003's own `## Documentation updates when O4 ships` read falsely — its body said *"One obligation from this list is still open"*, which my edit is exactly what closes. R2 handed this decision forward by name (*"R3 should pick one deliberately rather than leaving an empty section behind"*), and the build plan reserved it to this pass. Leaving it would have shipped a spec asserting an open obligation that is discharged, which is worse than either resolution.

**Decision: keep the heading, replace the body with a one-line pointer.** The section now reads:

```text
## Documentation updates when O4 ships
Every obligation this section declared is discharged. Each of the four, and what discharged it, is recorded in the [rationale file][spec-003-rationale].
```

**Alternative rejected: delete the section outright.** It is the tidier end state and a wholly discharged instruction is history, which is the rationale's. It lost on two mechanical grounds, both checked rather than argued: the rationale's entry is keyed to this heading by `[spec-003-docs]: ../spec-003-…md#documentation-updates-when-o4-ships`, so deleting the heading orphans that key and breaks the one link-integrity property this cycle has verified three times; and `worker-1.md` `### Performing the rationale move` rule 1 requires **every decision keep a one-line pointer** naming what moved and where — deleting the section removes the pointer, leaving a reader of the spec alone with no signal the obligations ever existed.

### Spec changes made (Worker 1 only)

| File | Site | Change | Reason |
|---|---|---|---|
| `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` | `:154`, B4 `**Depends on.**` | `… O6 (downgrade rule) once those land.` -> `… O6 (downgrade rule).` | The one authorized sibling-spec edit. **Licensing clause, quoted from the spec as it read before this pass:** spec-003 `## Documentation updates when O4 ships` -> *"Remove the `not yet implemented` rider on the `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` B-slices that depend on nested resolver-key sentinels."* Both O4 and O6 landed at `0.0.2`, so the rider was false |
| `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` | `## Documentation updates when O4 ships` (`:191`-`:196` before, `:191`-`:192` after) | Body replaced by a one-line pointer to the rationale; heading kept | The edit above discharged the section's last open item, so its "One obligation from this list is still open" lead-in became false **because of this pass**. See `### The custody decision the rider edit forced` |
| `docs/SPECS/appx/spec-003-…-rationale.md` | entry `` ### `## Documentation updates when O4 ships` `` | Heading corrected (`— three obligations discharged, one still owed` -> `— all four obligations discharged`); item 2 retensed to record the two-step discharge; appended a *Changed in the documentation-completion pass* paragraph, an *Alternative rejected* paragraph, and a fourth **Claims the spec no longer makes** clause | The entry **asserted** the fact this pass falsified, in its heading and in item 2's present tense. Appending a correction beneath an uncorrected assertion leaves the document explaining a change while restating the error. Rule 4's append-only protects a settled entry from a **later round**; the R3 custody pass is the pass that owns this entry's decision. Nothing anchors to a rationale heading (`grep -rn '…-rationale\.md#'` -> no hit), so the rename moves no link |

**Deferral reasons for boxes left `- [ ]`:** none — all 14 boxes are `- [x]` after this pass.

### Checklist audit — all 14 boxes, re-derived against the diff

I re-derived each `- [x]` rather than reading Worker 3's walk as discharge. **No over-tick found, so nothing was un-ticked.** Box 6 was the one open box and I ticked it, having discharged it above.

| # | Box | My verdict |
|---|---|---|
| 1 | `docs/GLOSSARY.md` audited | `[x]` — the file is byte-unchanged (`git status --porcelain -- docs/GLOSSARY.md` -> 0 entries) and `build_glossary_md.py --check` exits 0, so the audit's "no drift, no write" disposition is provable both ways. All 8 card-3 anchors re-slugged by me: 8/8 `True` |
| 2 | `docs/TREE.md` optimizer subtree audited | `[x]` — `build_tree_md.py --check` -> `docs/TREE.md is up to date.` exit 0; `grep -rEn 'TODO\(spec-003…' django_strawberry_framework/` -> 0 |
| 3 | `docs/README.md` audited | `[x]` — file unmodified; the cited sites re-read |
| 4 | `KANBAN.md` audited | `[x]` — `grep -n 'spec-003' KANBAN.md` -> exactly `:144`, `:240`, `:314`, `:317`, `:4819`; `:144` and `:4819` both name the archived path |
| 5 | Disposition in the required form | `[x]` — A5 branch two. Proven below under `### The mechanical claims, proven by me` |
| 6 | `spec-004` B4 rider retired | **`[x]` — ticked by me this pass.** Discharged above; `git diff --numstat` -> `1  1` |
| 7 | Inbound verified | `[x]` — sweep re-run; every table row confirmed. Count unit corrected below |
| 8 | Outbound verified | `[x]` — I re-ran my own resolver over the rationale **after my edits**: 19 defs / 19 distinct refs / 0 undefined / 0 unused / 0 unresolved, every `#anchor` slugged against the target's real headings |
| 9 | DB direction verified | `[x]` — `import_spec_terms --check` green post-edit; the `iterdump()` diff proves the DB carries exactly the one intended row change and nothing else |
| 10 | Both checks re-run after the write | `[x]` — re-run a third time by me, post-my-edits; both quoted in `### Validation commands, re-run by me` |
| 11 | Staged-anchor decomposition published | `[x]` — re-measured by me; decomposition below |
| 12 | Card-052 cluster recorded once, no partial fix | `[x]` — `KANBAN.md`'s whole diff is one line at `:4851`; `:240`, `:314`, `:317` are byte-unmoved. spec-003's `## Problem statement` is unmoved toward the card's prescription (my only spec-003 edit is 60 lines later and unrelated) |
| 13 | No source / test / sibling spec beyond the one clause / CSV / CHANGELOG / rendered hand-edit | `[x]` — `git diff -- django_strawberry_framework/ tests/` -> **0 lines**; `git status --porcelain \| grep -c '\.py$'` -> **0**; `CHANGELOG.md`, `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, and `…-terms.csv` all show **0** dirty entries; `spec-004`'s diff is the one authorized clause |
| 14 | `check_trailing_commas --check` + rule 27 | `[x]` — exit 0 on all three `.md` files this pass wrote; rule-27 grep -> **0** in each |

### The mechanical claims, proven by me

`worker-1.md` `### Verifying relocation / promotion claims` requires I run the proof myself rather than read Worker 3's acceptance as discharge. Three claims carry this item.

**1. The DB write is scoped to the single `CardItem` row.** Proven by `iterdump()` semantics against a `git show HEAD:` copy in the session scratchpad **outside** the repo, comparing statement **sets** in both directions:

```text
HEAD statements: 9583   WORKTREE statements: 9583
statements only in HEAD:      1
statements only in worktree:  1
HEAD-ONLY: INSERT INTO "kanban_carditem" VALUES(950,'2026-06-09 17:39:26.033229','2026-06-09 17:39:26.033235','…
WT-ONLY  : INSERT INTO "kanban_carditem" VALUES(950,'2026-06-09 17:39:26.033229','2026-08-07 17:35:25.389707','…
```

Exactly **2 differing statements, both halves of row `950`** — its `text` and its `updated_at`. Equal statement totals and a symmetric one-in-one-out difference together rule out an added or dropped row anywhere in the DB, and the identical schema statements rule out a migration. This reproduces Worker 0's independent measurement and Worker 2's, by a third instrument.

**2. The corrected text is true of `walker.py::_plan_prefetch_relation`.** Proven by AST rather than grep, so a substring in a neighbouring function cannot answer for this one:

```text
args: ['sel','django_field','target_type','plan','prefix','info','runtime_paths','resolver_identities','enable_only']
'full_path' in names/args: False
    lookup_path = f"{prefix}{instance_accessor(django_field)}"
    append_prefetch_unique(plan.prefetch_related, Prefetch(lookup_path, queryset=child_queryset))
```

Collecting every `ast.Name` **and** every argument in the function's own subtree returns no `full_path`, while `grep -c 'full_path' …/walker.py` -> **20** module-wide. So the pre-fix sentence named a binding that exists in the module and not in the function it attributed it to, and the corrected sentence is exact. The reconciled spec's `### Prefetch-boundary recursion for many-side and downgraded paths` states the same instance-accessor rule, so spec, docstring, and card now agree.

**3. `KANBAN.md` / `KANBAN.html` are pure regenerator output — nothing in their diffs the DB write does not explain.** This is the claim `BUILD.md` `### Generated docs are DB-backed` exists to police, and a hand-edit hiding inside a regenerate diff is the failure mode. Three independent instruments, none of them the build report's assertion:

- `git diff -U0 -- KANBAN.md` -> **one hunk, `@@ -4851 +4851 @@`**, and the two lines differ in exactly one token: `` `Prefetch(full_path,`` -> `` `Prefetch(lookup_path,``. I read the full before/after line; nothing else moved in it.
- `git diff --word-diff=porcelain -- KANBAN.html` reduces the whole single-line data block to **exactly two token changes**: the same `Prefetch(` token, and `"updatedDate":"2026-06-09T17:39:26.033235+00:00"` -> `"2026-08-07T17:35:25.389707+00:00"`. That second token is **affirmative** proof of the ORM route rather than absence-of-evidence: `auto_now` is bumped by `Model.save()` and by nothing else — raw SQL would not move it, and a hand-edit of rendered markdown could not move it inside the HTML data block while leaving `createdDate` byte-identical. It matches the `iterdump()` row's new `updated_at` to the microsecond.
- All three regenerators in read-only `--check` mode exit **0** *after* the write: `KANBAN.md is up to date.`, `KANBAN.html is up to date.`, `docs/GLOSSARY.md is up to date.` This answers the stronger question than two-consecutive-regenerate byte-stability does — it says the on-disk file equals what the **current DB** renders, which is precisely "no hand-edit survives". A hand-edited token would have to also be a token the DB renders, and the `iterdump()` set difference shows the DB carries exactly one changed row.

Taken together the three are closed: the only semantic delta in the DB is row `950`'s text, both rendered files' only delta is that text (plus the HTML's `auto_now` echo), and both files re-render byte-identically from the DB.

### Worker 3's L3 — judged, and accepted

**Accepted as recorded-and-rejected-in-place.** I re-verified the evidence at `~/projects/strawberry-django-main/strawberry_django/optimizer.py` (`AGENTS.md` line 2) rather than accepting the finding's own account, by AST-extracting both functions:

- `::_get_hints_from_django_relation #"level=level + 1"` — **exact**, confirmed.
- `::_get_hints_from_django_relation #"field_prefetch = Prefetch(path, queryset=field_qs)"` — **exact**, confirmed verbatim.
- The rebasing block: `store = OptimizerStore()` is constructed empty in that function, and the block reads `extra_only = [o for o in store.only or [] if o.startswith(path_lookup)]` then `field_store.only.extend(o[len(path_lookup):] for o in extra_only)`. So the movement is **out of** the local store, **into** the child, with the prefix **stripped** — the opposite direction from "rebasing … under the relation path" — and inert, because the guard's source list is always empty here. Worker 3's reading is confirmed in full.

**Why accepted in one line:** the clause describes **upstream's** internals rather than this package, the parity argument the `CardItem` exists to make rests entirely on the two sub-claims that verify exact, and a second ORM write plus a second regenerate on a shipped Done card's twelve-release-old historical note buys no reader anything — which is the "improve it while I'm here" widening the plan's `### DRY analysis` pre-decided against, on the item where the temptation is highest because it is the last before the gate.

It is **not dropped**: it goes to the deferred catalog on Worker 3's resolution path **(b)** — fold a one-clause correction into card 052's closeout, where the other spec-003 record work already lives. Worker 2's stated reason for leaving the upstream half (*"is correct and was left alone"*) is right in its conclusion and one clause too strong in its wording; naming that is what makes this accepted residue rather than a missed defect.

### The count-unit corrections — re-measured by me, both units given

`BUILD.md` `## Claims are proven mechanically` prescribes counting **occurrences**, not matching lines; `grep -c` and `grep -rn … | wc -l` count lines. Worker 3 raised this and its two corrected numbers; I re-derived both side by side (`grep -c 'spec-003' <f>` vs `grep -o 'spec-003' <f> | wc -l`) so the final gate quotes a measured figure with its unit named. **Six stated counts have been wrong in this cycle; these are stated with the command that produces them.**

| Where | As the build plan records it | Measured now |
|---|---|---|
| `### Every reference TO spec-003`, `docs/builder/build-002-optimizer-0_0_2.md` row | `(5 hits)` | **11 occurrences across 10 lines** (the build report's proposed `(10 hits)` is the line count, not the occurrence count) |
| `### Every reference TO spec-003`, prior-rationale row (the two files jointly) | `(8 hits)` | **10 occurrences across 10 lines** — `spec-002-…-rationale.md` 9/9, `spec-001-…-rationale.md` 1/1. Correct in the build report's C1 table but absent from its one-row corrections list, which is Worker 3's L2 |

Neither row's **disposition** changes: `build-002` is a historical artifact correct as history, and both prior rationales are read-only and correct. The recommended plan wording carries both units — `(11 occurrences across 10 lines)` and `(10 occurrences across 10 lines)` — since `hits` is the word that is not re-derivable. The plan is Worker 0's file and neither row was edited by me.

For the record, the same distinction over the other C1 files, measured: `KANBAN.md` 5 lines / **7** occurrences; `KANBAN.html` 1 line / **6** occurrences (one long data line); `docs/SPECS/spec-002-optimizer-0_0_2.md` 1 / 1.

### Failability and fail-open — confirmed mechanically, not assumed

- **No boundary was introduced, so no proof is owed.** Confirmed rather than accepted from the plan's declaration or the build report's statement: `git diff -- django_strawberry_framework/ tests/` -> **0 lines**, and `git status --porcelain | grep -c '\.py$'` -> **0**. The cycle's entire diff is one `CardItem.text` row, its two regenerator outputs, two spec sentences, and the artifacts. `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to new boundaries, guards, gates, and rejection paths; there are none, and the required `### Failability proofs` statement is present in the build report.
- **No fail-open shape landed.** Vacuous for the same mechanical reason — a fail-open shape is an expression in executable code and the diff contains none. Stated because `worker-1.md` `### Failability and fail-open checks` asks for the confirmation, not the assumption.
- **`### Hot-path budget` and `### Floor verification`** both carry their required explicit statements and both are correct: the plan declares `Hot-path declaration: none` and `Floor-verification scope: none` cycle-wide, no code runs per request / resolver / row / connection / message because no code changed, and no framework seam was touched. The shared `.venv` was not mutated by this pass.

### Staged-anchor sweep — this cycle's doc-wrap obligation, re-measured

`BUILD.md` `## Cross-slice integration pass` step 6, folded into R3 because this cycle produces no `bld-integration.md`.

**The mechanical test first**, which closes the classification question by construction:

```shell
grep -rEn 'TODO\(spec-003|TODO-(ALPHA|BETA|STABLE)-003' django_strawberry_framework/ tests/ examples/ scripts/ | wc -l
```

-> **0**. A staged anchor is a source-site marker (`AGENTS.md` rule 26), so zero here means every remaining hit is by construction a `.md` hit.

**Whole-tree sweep, with its decomposition — never the bare count**, since a raw number reads as a failure signal and is not one:

```shell
grep -rEn 'TODO\(spec-003|TODO-(ALPHA|BETA|STABLE)-003' . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=shadow
```

-> **25 matching lines across exactly five `.md` files**: the rationale **6**, `bld-003-r1-rationale_move.md` **7**, `bld-003-r2-spec_reconciliation.md` **4**, `build-003-…md` **4**, `bld-003-r3-doc_completion_archive.md` **4**.

The trajectory is entirely self-growth in one file and is reported rather than smoothed: plan-time **21/4 files**, build report **22/5**, review **24/5**, now **25/5** — every increment is in `bld-003-r3-…md` itself, as each pass quotes the anchor form while writing about the discrimination rule. **Zero in the spec** (`grep -c` -> 0), zero in any source or test file, zero in `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` (so `BUILD.md` step 6's exclusion never had to be applied). Every `.md` hit is descriptive — an account of anchors that were removed, or the discrimination rule itself — not instructional.

**Zero staged anchors survive. `BUILD.md` `## Cross-slice integration pass` step 6 is discharged for this cycle.**

### Spec status-line re-verification (owed by every Worker 1 spawn)

Read `docs/SPECS/spec-003-…md` lines 1-6 at their current content. The spec carries **no `Status:` / owner / target-release / predecessor header block** — R1 established this and it still holds; its opening is the title, the companion-rationale pointer, then `## Problem statement`. Nothing in those lines is falsified by this pass:

- Line 3's pointer enumerates what the rationale carries, including *"the documentation obligations it declared and discharged"* — **more** true after this pass, not less, since the fourth obligation's account now lives there too.
- Line 3's closing clause about why the O4 record was split from `spec-002` is unchanged and still accurate.

A governing-principle sweep over the whole spec after my edit returns clean: `grep -niE 'amendment|retract|as of (spec|review|round)|originally|used to|formerly|previously|no longer|superseded|since land|have since'` -> **no match**. The spec still never narrates its own history, and my replacement sentence did not reintroduce it.

The spec is **236 lines / 28,472 bytes** (was 240 / 28,634 at R2's close); its diff against HEAD is now **75 insertions / 286 deletions** (was 78 / 285). The delta is exactly my four-line net removal in one section, and I state it because R2's final verification pinned `78/285` as its own no-line-appended proof.

### The 8-anchor constraint — re-verified per anchor, not via the green exit

The constraint has zero margin and a dropped anchor breaks the DONE-card wrap chain for card 3, so a green `check_spec_glossary` — which passes on one anchor as readily as on eight — is not the proof. Counted per anchor over the spec **after** my edit (each returns `2` = one link definition + one body use):

```text
glossary-djangotype 2   glossary-fk-id-elision 2   glossary-metaoptimizer-hints 2   glossary-only-projection 2
glossary-optimizerhint 2   glossary-plan-cache 2   glossary-queryset-diffing 2   glossary-schema-audit 2
```

Note the ref-id is `glossary-metaoptimizer-hints` (hyphenated) while its **target anchor** is `#metaoptimizer_hints` (underscored) — counting by the anchor spelling returns 0 and reads as a dropped link. All eight targets were then re-slugged against `docs/GLOSSARY.md`'s real headings: **8/8 `True`**.

### Validation commands, re-run by me

Every command below was run **after** my three file edits, so these supersede the build report's and the review's readings rather than restating them.

```text
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-003-…-0_0_2.md
  -> OK: 8 terms - all have glossary entries and at least one spec link.        exit 0
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
  -> OK: 10 terms - all have glossary entries and at least one spec link.       exit 0
uv run python examples/fakeshop/manage.py import_spec_terms --check
  -> OK: 49 done cards have glossary links.                                     exit 0
uv run python examples/fakeshop/manage.py check
  -> System check identified no issues (0 silenced).                            exit 0
uv run python scripts/check_trailing_commas.py --check <each of the three .md written>
  -> exit 0 on spec-003, spec-004, and the rationale
uv run python scripts/build_kanban_md.py    --check -> KANBAN.md is up to date.        exit 0
uv run python scripts/build_kanban_html.py  --check -> KANBAN.html is up to date.      exit 0
uv run python scripts/build_glossary_md.py  --check -> docs/GLOSSARY.md is up to date. exit 0
uv run python scripts/build_tree_md.py      --check -> docs/TREE.md is up to date.     exit 0
```

`manage.py check` is run because the DB was written this item. `ruff format` / `ruff check` were **not** run and correctly so — zero `.py` paths are dirty and running either would churn files outside this cycle. **No `pytest` was run** (`AGENTS.md` rule 15), and no `--cov*` flag in any form.

Final working-tree state, every entry accounted for:

```text
 M KANBAN.html                                              (Worker 2, regenerator output)
 M KANBAN.md                                                (Worker 2, regenerator output)
 M docs/SPECS/spec-003-…-0_0_2.md                           (R1 + R2, plus this pass's section edit)
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md            (this pass, the one authorized clause)
 M examples/fakeshop/db.sqlite3                             (Worker 2, CardItem row 950)
?? docs/SPECS/appx/spec-003-…-rationale.md                  (R1, plus this pass's entry correction)
?? docs/builder/bld-003-r1-…  bld-003-r2-…  bld-003-r3-…  build-003-…
```

### DRY check across the cycle

**No new duplication, and this is a measured negative.** The cycle's whole diff contains no executable logic (`git diff -- django_strawberry_framework/ tests/` -> 0 lines), so there is no helper, literal, or data flow to duplicate. On the documentation axis, the one live risk the plan named — importing the reconciled spec's contract prose into `docs/GLOSSARY.md`'s entry, creating a second statement of one contract in a file the spec does not own — did not materialize: `docs/GLOSSARY.md` is byte-unchanged. My own two spec edits are subtractive; neither restates a fact stated elsewhere, and the spec-003 replacement sentence deliberately **points** at the rationale rather than summarising it.

Against the prior accepted items: R1 moved deliberation out, R2 restated contracts in place, R3 removed a discharged instruction. No item re-stated another's output. `scripts/review_inspect.py` was correctly skipped by all three passes with a recorded reason (nothing under `django_strawberry_framework/` changed in the entire cycle).

### Maintainer escalations — confirmed on disk where the final gate will find them

`BUILD.md` `### Cohorting, naming, and closure`: detail living only in a return report does not reach the next worker. I confirmed each of the following is on disk, and I read the two closed artifacts in full to catch anything their own catalogs dropped.

**In this artifact**, `### Notes for Worker 1 (spec reconciliation)` (Worker 2) and the same-named section under the review (Worker 3):

1. **The card-052 divergence — a maintainer decision, neither surface partial-fixed.** Card `TODO-ALPHA-052-0.1.0` prescribes replacing spec-003's opening claim; R2 deliberately rejected that disposition with its reasoning in the rationale under `` ### `## Problem statement` ``. Three of the card's four named sites are closed by R2; retiring them is card 052's own closeout. **Verified unmoved in both directions by me**: `KANBAN.md`'s entire diff is one line at `:4851`, and spec-003's `## Problem statement` still opens with the framing the card asked to replace. This is now its **sixth** on-disk carrier.
2. **`KANBAN.md:314`, the fifth card-052-adjacent site the build plan's table omits.** Re-derived: `grep -n 'spec-003' KANBAN.md` returns exactly five lines — `:144`, `:240`, `:314`, `:317`, `:4819` — so `:314` is genuinely absent from the plan's four-row table. Reported, not fixed; card 052's closeout should sweep five sites.
3. **Worker 3's L3**, accepted in place above; carried on resolution path (b).
4. **The two count-unit corrections**, re-measured above with both units.
5. **The `docs/GLOSSARY.md` `**Status:** shipped (`0.0.2`)` versus `CHANGELOG.md` `[0.0.3]` optimizer dating question.** Card 052 owns it by that card's own words; read and confirmed unchanged, not touched.

**Carried from R1 and R2** — I re-read both closed artifacts to verify these are on disk rather than trusting the dispatch:

6. **The unguarded ordering invariant.** `optimizer/walker.py::_record_relation_access` must run before the elision check in `_plan_select_relation`, because it appends the FK `attname` the elided resolver later reads; reversing them silently reintroduces an N+1. Protected by the helper's docstring and now the spec, with **no automated guard**. On disk in `bld-003-r1-rationale_move.md` `### Deferred work` and again in `bld-003-r2-spec_reconciliation.md` `### Deferred work carried to the final gate's catalog`. **Note for the gate: the two carriers cite different spec line numbers** (`spec:67` in R1, `spec:70` in R2 after R2's edits shifted it) — one item, not two, and a catalog deduplicating by line number would double-count it.
7. **The rationale-file template is on its third hand-reproduced instance** (`spec-001`, `spec-002`, `spec-003`). Whether it becomes a documented template is a standing-docs question, not a defect. **This item is on disk only in `bld-003-r1-rationale_move.md` `### Deferred work` — R2's catalog does not carry it forward**, so a gate walking only the most recent catalog would lose it. Flagged here for that reason.

**Three further R2-catalogued items the gate must also carry**, confirmed on disk in `bld-003-r2-spec_reconciliation.md` `### Deferred work carried to the final gate's catalog`:

8. A forward `ManyToManyField` appends a field name rather than a column to the parent's `only_fields`. Harmless (Django drops it from the compiled `SELECT`), deliberately undocumented, recorded in the rationale's `## Standing notes`.
9. `optimizer/plans.py::_prefetch_lookup_paths` recurses with no depth cap while its sibling `::runtime_path_from_path` is bounded at `_MAX_PATH_DEPTH = 1024`. Theoretical only — the walker cannot construct a cyclic `Prefetch` graph.
10. **Package-wide:** should `scripts/check_spec_glossary.py` strip code spans in `REF_USE_PATTERN`? Spec-003 no longer depends on the answer (R2's L5 closed it here), but every spec whose only carrier for an anchor sits in inline code does.

**One residue inside a closed artifact, reported and not edited.** `bld-003-r2-spec_reconciliation.md`'s final-verification `### Summary` re-asserts "**19 rationale entries**", the figure its own L3 found wrong and superseded in the same file (15 `###` headings: 14 keyed to spec sections plus the closing). Prior sections of a closed artifact are never edited (`ARTIFACT.md` `## Re-pass sections`), so it stands where written; recorded here so the gate quotes the superseded figure, not the summary's.

**No source-level finding to escalate beyond item 6.** The read-only correctness obligation was discharged over the six `optimizer/` modules; no factually-false docstring and no defect. `AGENTS.md` rule 5 is not engaged: nothing here is a deferred real fix, because nothing here is a defect.

### Final status

`final-accepted`.

The item's one owed deliverable is performed and verified, all 14 checklist boxes carry the work they claim, all three mechanical claims were re-proved by me with instruments independent of the build report, Worker 3's three Lows are resolved (two re-measured and restated with their units, one accepted in place with its reason and routed onward), and ten maintainer-facing items are confirmed on disk for the final gate's `### Deferred work catalog` — two of them flagged because the most recent catalog would have dropped or double-counted them.

---

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
