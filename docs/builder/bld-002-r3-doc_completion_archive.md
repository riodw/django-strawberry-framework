# Build: R3 — Documentation completion and archive audit for spec-002

Spec reference: `docs/SPECS/spec-002-optimizer-0_0_2.md` (whole file; 9,844 bytes / 103 lines measured
at this pass's open, `wc -c` / `wc -l`) plus its companions
`docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` (33,620 bytes / 487 lines) and
`docs/SPECS/appx/spec-002-optimizer-0_0_2-terms.csv` (323 bytes, 3 data rows)
Build plan: `docs/builder/build-002-optimizer-0_0_2.md` (residual item R3)
Status: final-accepted

**R3 runs the full unmodified chain.** R1 and R2 were collapsed to Worker 1 + Worker 3 by the build
plan's Deviation 3, because their whole deliverable was spec mutation. R3 is different: it has real
Worker 2 work — one kanban-DB edit plus three regenerates, and the read-only audit legs. So
`Status: planned` here means **dispatch Worker 2**, and the chain is
Worker 1 (plan) -> Worker 2 (build, `built`) -> Worker 3 (review) -> Worker 1 (final verification).

**There is no interstitial Worker 1 pass, and that is a decision rather than an omission.** The
spec-001 cycle's R3 needed one because it carried two open `spec-002` edit obligations; R3 here
carries none — every obligation below lands in the kanban DB, the three generated docs, or a
recorded measurement. **The condition that would create one:** if Worker 2's audit finds something
that must change in `docs/SPECS/spec-002-optimizer-0_0_2.md` or its rationale, Worker 2 records it
under `### Notes for Worker 1 (spec reconciliation)` and **stops** — Worker 0 then dispatches an
interstitial Worker 1 pass **after `built` and before the review**, so Worker 3 reviews one combined
diff. Naming the condition and the timing here is what stops it being improvised later.

---

## Plan (Worker 1)

### Spec status-line re-verification

Re-read `docs/SPECS/spec-002-optimizer-0_0_2.md` lines 1-10 at this pass's open, not inherited from
R1 or R2. Line 1 is `# Spec: Optimizer & Reverse-Relation Resolution`, line 2 blank, line 3
`## Purpose`. **There is no status / target-release / owner / predecessor block**, so there is
nothing for this obligation to falsify and R3 deletes no predecessor doc a header could point at. No
edit owed.

Two consequences specific to R3, stated so no later pass re-derives them:

- The spec and its rationale are **not in R3's Worker 2 write set at all**. The 3-anchor constraint
  (`build-002-optimizer-0_0_2.md` `### The 3-anchor constraint`) is therefore only re-owed if a
  Worker 1 pass edits one of them for a reason it does not currently have.
- `## Visibility status` is cited by `spec-006-public_surface-0_0_3.md` twice **and** by the
  rationale's `[spec-002-visibility]` link definition. Nothing in R3 rewords that heading.

### Measured baseline at this pass's open

Every number was produced by the command beside it, at planning time. It is a baseline for Worker 2
to **re-derive, never inherit** — the concurrent session has moved several of these already.

| Fact | Value | Command |
|---|---|---|
| HEAD | `faebd949` | `git rev-parse --short HEAD` |
| Spec | 9,844 bytes / 103 lines | `wc -c` / `wc -l` |
| Rationale | 33,620 bytes / 487 lines | same |
| Terms CSV | 323 bytes, **3 data rows, 3 distinct anchors** (`djangooptimizerextension`, `djangotype`, `only-projection`) | `cat` + read |
| `check_spec_glossary.py --spec …spec-002…` | `OK: 3 terms - all have glossary entries and at least one spec link.`, exit 0 | as written |
| `import_spec_terms --check` | `OK: 49 done cards have glossary links.`, exit 0 | as written |
| `build_tree_md.py --check` | `docs/TREE.md is up to date.`, exit 0 | as written |
| `Card.objects.get(number=2)` | `DONE-002-0.0.2`, `done`, `0.0.2`, `Optimizer O1-O6 foundation` | fakeshop ORM, read-only |
| `SpecDoc` for card 2 | name `spec-002-optimizer-0_0_2`, **`path` = `docs/SPECS/spec-002-optimizer-0_0_2.md`**, file exists on disk | fakeshop ORM, read-only |
| `card.glossary_links.count()` | **3**, `raw_text` values `DjangoOptimizerExtension` / `DjangoType` / `only()` — one per CSV row | fakeshop ORM, read-only |
| Spec anchor budget | **1 / 1 / 2** — `only-projection` 1, `djangotype` 1, `djangooptimizerextension` 2 | `grep -o '\]\[glossary-[a-z0-9_-]*\]' … \| sort \| uniq -c` |
| Spec link defs | **4 defs / 4 used**, 0 undefined, 0 orphaned, 0 broken on-disk paths, 0 inline cross-file links | scratch script over the file |
| Rationale link defs | **19 / 19**, same zeros; all **7** `…spec-002-optimizer-0_0_2.md#<frag>` fragments resolve against a surviving spec heading | same script |
| Card 52 target item | `CardItem` pk **1260**, section `Scope`, `order` 8, `text` length **606**, `created_date` 2026-08-07T03:48:30; **exactly 1** item on the card matches the substring | fakeshop ORM, read-only |
| Staged anchors | **2 occurrences**, both on `docs/builder/build-002-optimizer-0_0_2.md:222` (the plan's own checklist line, which contains both patterns) | `grep -rEo 'TODO\(spec-002\|TODO-(ALPHA\|BETA\|STABLE)-002' .` |

### Working-tree baseline, re-measured (concurrent session)

`git status --porcelain` at this pass's open — **14 paths, the same 14 both R2 passes recorded**:

```
 M KANBAN.html                                        <- concurrent
 M KANBAN.md                                          <- concurrent
 M docs/SPECS/spec-002-optimizer-0_0_2.md             <- THIS CYCLE (R2)
 M docs/SPECS/spec-042-debug_toolbar-0_0_14.md        <- concurrent
 M docs/SPECS/spec-043-test_client-0_0_14.md          <- concurrent
 M docs/SPECS/spec-044-debug_extension-0_0_14.md      <- concurrent
 M docs/SPECS/spec-050-debug_extraction-0_0_19.md     <- concurrent
 M docs/SPECS/spec-051-boundary_dry_squeeze-0_0_20.md <- concurrent
 M examples/fakeshop/db.sqlite3                       <- concurrent
 M examples/fakeshop/test_query/README.md             <- concurrent
?? docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md  <- THIS CYCLE (R1 + R2)
?? docs/builder/bld-002-r1-rationale_move.md              <- THIS CYCLE
?? docs/builder/bld-002-r2-spec_reconciliation.md         <- THIS CYCLE
?? docs/builder/build-002-optimizer-0_0_2.md              <- THIS CYCLE
```

Nine concurrent-session paths, one this cycle's modified spec, four this cycle's untracked files.
That is the build plan's `## Baseline-dirty out-of-scope files` list unchanged. Three facts bind
Worker 2:

- **`docs/GLOSSARY.md` is CLEAN** and is not in the list. If a regenerate dirties it, that is **drift
  to investigate and report**, not build output (`build-002-optimizer-0_0_2.md`
  `## Concurrent-writable tracked binary / generated files`).
- **`examples/fakeshop/db.sqlite3`, `KANBAN.md`, and `KANBAN.html` are already dirty from the
  concurrent session.** Worker 2 writes all three — but only by ORM edit plus regenerate, applied
  **on top** of the concurrent state, **never reverting anything**, and never by hand-editing a
  rendered file. `AGENTS.md` rule 34: no `git checkout`, `git restore`, `git stash`, `git worktree`
  on any path, tracked binary or otherwise.
- **The concurrent session is actively writing card 52 right now.** Two of its `Scope` items
  (`order` 9 and 10) were created at 2026-08-07T04:13:51, twenty-five minutes after the target item.
  That is why step 3 locates the item **by substring and asserts exactly one match**, never by the
  pk recorded above.

### What R3 is, restated from the maintainer's framing

*"Finish the documentation and audit the archive."* The archive **already landed** before this cycle
opened, and every leg of it re-verified green at plan time (table above): the spec is at
`docs/SPECS/`, the terms CSV and R1's rationale at `docs/SPECS/appx/`, `SpecDoc.path` already reads
the archived path, both `KANBAN.md` path references already resolve, and every link definition inside
both companions resolves at its archived depth. **R3 is a documentation-completion and archive-audit
item, not a move.**

The one thing this cycle genuinely broke is on a **durable board**. R1 removed `## Open questions`
and R2 removed `## Current state`; a `KANBAN.md` card bullet describes those sections as present and
accurate, and its load-bearing claim that nothing cites spec-002 by `#anchor` was falsified by R2's
own rationale link definition. That bullet is the only mutation R3 performs. Everything else is
measurement — and the honest discharge of a measurement is **reporting the zeros**, because an
unstated absence is indistinguishable from an unrun check.

### Findings already verified at plan time — Worker 2 acts on these, it does not re-discover them

Worker 2 still re-derives each against source (`BUILD.md` `## Claims are proven mechanically`), but
the sweeps that found them have run, so the build pass starts from real targets.

#### F1 — the `KANBAN.md:310` card bullet is stale in three particulars (the one DB edit)

Rendered at `KANBAN.md:310`; stored as `CardItem.text` on card `TODO-ALPHA-052-0.1.0`, section
`Scope`, `order` 8. Current text (606 chars, verified on disk and in the DB):

> `docs/SPECS/spec-002-optimizer-0_0_2.md` carries four status-shaped sections: `## Current state`,
> `## Shipped slices`, `## Visibility status`, `## Open questions`. All four are accurate at HEAD
> today, so nothing is wrong now - the deferral is the standing-promise shape itself, which spec-001
> retired by retitling `## Current state` to `## Prior art` on the reasoning that a section named for
> the present is a promise no shipped spec can keep. Nothing anywhere cites spec-002 by `#anchor`, so
> retitling breaks no link, but `spec-003-optimizer_nested_prefetch_chains-0_0_2.md` names those
> sections in prose.

Four claims are now wrong or spent, each re-verified at this pass:

1. **the count** — `## Open questions` (removed by R1) and `## Current state` (removed by R2) are
   both absent; `grep -n '^## ' docs/SPECS/spec-002-optimizer-0_0_2.md` returns `Purpose`,
   `Problem statement`, `Architecture decision`, `Shipped slices`, `Coordination with …`,
   `Visibility status`, `References`, `Implementation checklist`;
2. **two of the four named sections** do not exist;
3. **"All four are accurate at HEAD today, so nothing is wrong now"** — the whole argument for
   deferring — is spent: the deferral has been **discharged**, not rescheduled;
4. **"Nothing anywhere cites spec-002 by `#anchor`"** is false. `grep -rn
   'spec-002-optimizer-0_0_2.md#' .` returns **7 link definitions**, every one in
   `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` (lines 458-464), one of them
   `[spec-002-visibility]: ../spec-002-optimizer-0_0_2.md#visibility-status`, added by R2 itself.

R2 decided the bullet is **replaced, not patched**, and its final verification corrected the
replacement's fourth clause. The corrected text is reproduced verbatim in
`### The replacement `CardItem.text`, verbatim` below.

**Counter-reading, written out so Worker 3 attacks it rather than rediscovering it.** Grepping the
whole tree, the literal string `spec-002-optimizer-0_0_2.md#` also appears in
`docs/builder/bld-002-r1-rationale_move.md`, `docs/builder/bld-002-r2-spec_reconciliation.md`, and
(once this plan lands) in this artifact. Those are **prose describing the grep**, not citations, and
they are per-cycle builder artifacts. The replacement text's claim — that the rationale is the only
file that *cites* spec-002 by `#anchor` — holds. Do not read an artifact's own description of a
search as a counterexample to the search.

#### F2 — `docs/GLOSSARY.md` says `0.0.2`, `CHANGELOG.md` says `0.0.3`, for the same behavior

R2's hand-off item 10, escalated here. Measured at this pass; all four sites quoted so the
escalation is neither short nor overlong:

| Site | Text | Says |
|---|---|---|
| `docs/GLOSSARY.md:714` | `## `DjangoOptimizerExtension`` -> `**Status:** shipped (`0.0.2`).` | `0.0.2` |
| `docs/GLOSSARY.md:1382` | `## `only()` projection` -> `**Status:** shipped (`0.0.2`).` | `0.0.2` |
| kanban DB | card 2 = `DONE-002-0.0.2`, `target_version.number` `0.0.2`; sibling card 3 (O4) = `DONE-003-0.0.2` | `0.0.2` |
| `CHANGELOG.md:292-297` (`## [0.0.2]`) | *"**Early** `DjangoOptimizerExtension` Strawberry schema extension for **depth-1** N+1 prevention"* | partial at `0.0.2` |
| `CHANGELOG.md:283-285` (`## [0.0.3]`) | *"`DjangoOptimizerExtension` is now effective end-to-end for root `QuerySet` resolvers: selection-tree planning, `select_related`, nested `Prefetch` chains, same-query recursion, `only()` projection, and `get_queryset`-aware `Prefetch` downgrade."* | O4/O5/O6 at `0.0.3` |

**Ruling: the GLOSSARY side is NOT in R3's scope. The whole disagreement routes to the maintainer as
ONE item, and R3 makes zero DB edits for it.** Four reasons, so the next pass does not re-open it:

1. **The GLOSSARY status is not independently correctable.** It is one of three surfaces that must
   agree — `GlossaryTerm.body`, the kanban card's `target_version`, and `CHANGELOG.md`. The card's
   own identity string encodes the version (`DONE-002-0.0.2`), as does the spec filename (`0_0_2`).
   Flipping the glossary entry to `0.0.3` while the card stays `DONE-002-0.0.2` **creates** a
   disagreement rather than closing one.
2. **The surface that could settle it is closed.** `AGENTS.md` rule 21 forbids editing
   `CHANGELOG.md`; the build plan repeats it as a build-wide context flag. A cycle that cannot edit
   the authoritative record of release history cannot decide which reading of it is right.
3. **The build plan already fenced version metadata out.** *"`0.0.2` shipped and the version quintet
   is at `0.0.14`. No residual item touches … the GLOSSARY package-version line."*
4. **Read charitably the two are not contradictory** — the extension and the walker existed at
   `0.0.2` (the CHANGELOG's own word is "early … depth-1"), and became end-to-end effective at
   `0.0.3`. Choosing which of those a `**Status:** shipped (X)` line should name is an editorial call
   about how the glossary dates a multi-release subsystem. That is a maintainer's call, not a drift
   a worker can measure its way out of.

Worker 2's obligation is therefore **to record, not to fix**: quote all four sites with line numbers,
state both readings, and hand it up. `AGENTS.md` rule 21 and the standing rule that a changelog may
correctly carry the sentence a spec must not — correct as **history**, wrong as a standing contract —
both apply. Do not "fix" the changelog, and do not open a `GlossaryTerm.body` edit.

#### F3 — the terms-CSV completeness question (R2 hand-off item 11), and a premise in it that is wrong

R2 asked whether card 2's three-anchor set is complete "for the spec as it now reads", naming
`FK-id elision`, `Plan cache`, and `Meta.optimizer_hints` as glossary-backed terms the spec names
without linking.

**Two of those three do not appear in the spec at all.** Measured:
`grep -nio 'plan cache\|optimizer_hints' docs/SPECS/spec-002-optimizer-0_0_2.md` returns **nothing**.
The actual unlinked-but-glossary-backed set is **four**, found by matching every `## ` heading in
`docs/GLOSSARY.md` against the spec body:

| Term | Glossary anchor | Spec line |
|---|---|---|
| `DjangoConnectionField` | `#djangoconnectionfield` | 25 |
| `finalize_django_types` | `#finalize_django_types` | 31 |
| FK-id elision | `#fk-id-elision` | 33 |
| Visibility boundary | `#visibility-boundary` | 48 |

(A fifth raw match, `DjangoConnection`, is a substring artifact of `DjangoConnectionField` and is not
a separate occurrence. Worker 2 re-derives the whole set rather than trusting this table — an
inherited count is what this cycle keeps getting wrong.)

**Ruling: the three-anchor set stands. R3 reports it as deliberate, with the measurement, and adds no
CSV row.** Reasons:

1. `check_spec_glossary.py` validates that the terms a spec **links** resolve to real anchors. It
   does not require exhaustiveness, and it passes at 3.
2. The CSV is what `import_spec_terms` rebuilds a **DONE** card's glossary-link set from. Adding a
   row retroactively changes card 2's shipped board record twelve releases after it closed — a
   board-history edit, not a documentation completion.
3. `AGENTS.md` rule 26 puts glossary fold-in in **the completing spec's Slice 5**. Spec-002's
   completing slice ran at `0.0.2`. The memory rule is explicit: do not enrich a spec's glossary
   entry during authoring.
4. Mechanically, adding an anchor also needs a **link in the spec body** for
   `check_spec_glossary.py` to keep passing — and the spec is Worker 1's, not Worker 2's, so the
   "small CSV addition" is really an R2-shaped spec edit inside an item that owns no spec write.
5. R2 already assessed and declined it. R3 seconding that **with the measurement written down** is
   the discharge; re-opening it is new scope.

**Never edit a CSV to make a check pass.** Nothing here needs one to pass — everything is already
green.

#### F4 — read-only sibling staleness: the scope is wider than R2's hand-off says

R2's hand-off named `spec-003…:333` and "spec-003's opening `_optimizer_field_map` constraint". The
plan-time sweep finds the same class in **four** places in that one sibling, all read-only:

| Site | Text | Why it is stale |
|---|---|---|
| `spec-003…:4` | *"O1, O2, O3, O5, and O6 have shipped … The remaining O-slice is O4"* | O4 shipped; correct as a record of spec-003's authoring moment, present-tense at HEAD |
| `spec-003…:27` | `plan_optimizations(selected_fields, model, info=None)` and `_collect_scalar_only_fields` | the pre-D4 arity; `_collect_scalar_only_fields` is absent from the package |
| `spec-003…:333` | *"Update `docs/SPECS/spec-002-optimizer-0_0_2.md` current state, visibility status, and checklist to mark O4 shipped"* | a discharged when-O4-ships instruction naming a section that no longer exists |
| `spec-003…:335` | *"Also update the older parent-spec O4 references in `docs/SPECS/spec-002-optimizer-0_0_2.md`"* | same discharged `## Documentation updates when O4 ships` block; **R2's hand-off missed this one** |

Also live and **correct**, so it must not be swept up in a fix: `spec-006-public_surface-0_0_3.md:136`
and `:147` name `## Visibility status` by title and by description. That heading survives precisely
because of them.

**All of these are read-only siblings owned by other cards** (`build-002-optimizer-0_0_2.md`
`## Build-wide context flags`). Worker 2 records them and edits none. Bounding the escalation is part
of the job: an escalation that is short is a defect, and one that is long in the wrong direction is
another — so name what is **not** in it too (the `spec-002` survivals in `CHANGELOG.md` and
`KANBAN.md` prose are correct as history and are not on this list).

### DRY analysis

**Helper inventory checked.** Refreshed for the **whole package** at this pass, not scoped to
`utils/`, per `worker-1.md` `### Package-wide helper inventory before helper planning`. Shapes
searched, chosen for what R3 actually touches: `glossary`, `spec`, `kanban`, `render`, `anchor`,
`slug`. **No package-level candidate exists and none is in prospect** — R3 writes no `.py` file under
`django_strawberry_framework/`, and every generator it invokes (`scripts/build_kanban_md.py`,
`scripts/build_kanban_html.py`, `scripts/build_glossary_md.py`, `scripts/build_tree_md.py`) already
lives in `scripts/`, outside the package and outside the coverage gate. The inventory still ran
rather than being skipped, because it is what establishes that no package helper duplicates the
rendering path R3 depends on.

- **Existing patterns reused.** Four, none of them code:
  1. **The generator is the single source of truth for every rendered doc.** `KANBAN.md`,
     `KANBAN.html`, and `docs/GLOSSARY.md` come from `examples/fakeshop/db.sqlite3`. Every statement
     R3 changes on those surfaces is changed **in the DB**, then rendered. A hand-edit is a second
     copy of the generator's output that the next render silently deletes.
  2. **The replacement bullet is R2's text, copied verbatim** — not re-derived, not re-worded, not
     re-wrapped. `BUILD.md`'s verbatim-drop-in rule (`ARTIFACT.md` `### Documentation / release
     sanity`) applies to any text copied from a preceding pass's decision, and the length and hash
     below make it checkable.
  3. **The `SpecDoc` / terms-CSV / `glossary_links` chain is read from the DB, never from a
     document.** Plan text and spec text can both carry a stale reference; the DB is what
     `import_spec_terms` actually reads.
  4. **The spec-001 R3 audit's leg structure** (three cross-reference directions, then the
     CSV/`SpecDoc` chain, then the staged-anchor sweep) is reused wholesale from
     `docs/builder/bld-001-r3-doc_completion_archive.md`. The two cycles are the same shape; a second
     invented structure would be the duplication.
- **New helpers justified.** **None.** No source, no test, no `scripts/` addition. Worker 2 may write
  a throwaway link/anchor checker under `docs/builder/temp-tests/r3-spec002/` (gitignored) and must
  **not** add one to `scripts/`. Promoting a shared spec/rationale consistency checker is R2's
  hand-off item 8, already owned by the final gate's `### Deferred work catalog` and a maintainer
  call; R3 does not open it.
- **Duplication risk avoided.** Three, all real here:
  1. **Restating the spec's contract on the kanban board.** The replacement bullet states the
     residual *constraint* (which pointers would break) and points at the files; it does not restate
     what the spec says about O1-O6. A card bullet that mirrors spec prose goes stale the next time
     the spec moves.
  2. **A count written onto a durable surface.** The replacement text names the mechanism (a link
     definition targets `#visibility-status`) and carries **no number** — "seven" drifts the next
     time the companion gains an entry, where the grep is re-derivable forever. Worker 2 must not
     "helpfully" add the count back.
  3. **A fourth copy of the `0.0.2`-vs-`0.0.3` reasoning.** F2's escalation is recorded **once**, in
     the build report, with the four quoted sites. It does not also get written into a card bullet,
     the glossary, or the spec.

### Implementation steps

Pin-at-write-time. Every line number here is from the working tree at this pass's open and **must be
re-verified** — the concurrent session is writing `KANBAN.md`, `KANBAN.html`, the DB, and card 52
specifically.

1. **Re-measure `git status --porcelain` and re-attribute before touching anything.** Record what
   came back; do not quote this plan's snapshot as current. Confirm `docs/GLOSSARY.md` is still
   clean, and say so — a clean result is a result.
2. **Re-derive F1 against the DB and the disk**, not against this plan: read the spec's `^## `
   headings and confirm `## Current state` / `## Open questions` are absent; run
   `grep -rn 'spec-002-optimizer-0_0_2.md#' .` and classify each hit as a citation or as
   grep-describing prose. State the numbers you measured.
3. **Locate the target `CardItem` by substring, not by pk.**

   ```
   uv run python examples/fakeshop/manage.py shell -c "..."
   ```

   - `Card.objects.get(number=52)` must exist and read `TODO-ALPHA-052-0.1.0` / `todo` / `0.1.0`.
   - Filter that card's `CardItem`s for the distinctive substring `status-shaped sections`.
   - **Assert exactly one match.** Zero or more than one is a stop-and-report, never a guess: the
     concurrent session created two further `Scope` items on this card 25 minutes after the target
     one, so the pk in the baseline table may not be current.
   - Record the matched item's pk, `section`, `order`, and old `text` length before mutating.
4. **Apply the replacement via the Django ORM only** — set `.text` to the verbatim string in
   `### The replacement `CardItem.text`, verbatim` and call `.save()`. **Never raw SQL:** the build
   scripts run an in-process `/graphql/` query requesting `uuid { id }`, and only a `.save()` fires
   the `post_save` that creates the `UUIDModel` side-row. Change nothing else on the card — the
   sibling `Scope` bullet at `order` 7 (the spec/rationale consistency checker, rendered at
   `KANBAN.md:309`) is untouched and stays.
5. **Verify the stored text is byte-identical to the plan's** before regenerating:
   `len(item.text)` must be **1268** and `hashlib.sha256(item.text.encode()).hexdigest()` must be
   `041f0354993a32ad8b687dae00636544f761ad8edab7f2534c545a50f4971040`. A mismatch means the copy
   picked up the artifact's blockquote markers or line wrapping — fix the copy, never the assertion.
6. **Regenerate, from the repository root, all three:**

   ```
   uv run python scripts/build_kanban_md.py
   uv run python scripts/build_kanban_html.py
   uv run python scripts/build_glossary_md.py
   ```

   `KANBAN.html`'s Vue shell is hand-edited and only its data block regenerates (`START.md`
   "Rendered docs"); the script owns that, so do not touch the shell.
7. **Verify by two-consecutive-regenerate byte-stability, never by "`git diff` is clean".** The
   concurrent session has made a clean diff meaningless here (`BUILD.md` `### Tracked binary /
   generated files`). Hash `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md`, run the three scripts
   a second time, hash again, and record both sets — they must be identical. Then **spot-check the
   rendered bullet**: re-read the card 052 `Scope` block in `KANBAN.md` and confirm it reads
   correctly and that the sibling bullet is unchanged. Then re-run
   `uv run python examples/fakeshop/manage.py import_spec_terms --check` and quote it: **exit 0 is
   the contract; the done-card number is not** (it moves with the concurrent session).
8. **Classify the `docs/GLOSSARY.md` result explicitly.** It was clean at plan time and R3 changes no
   glossary row, so the expected outcome is that it stays clean after the regenerate. **If it goes
   dirty, that is drift to investigate and report** — diff it, say what changed, and hand it up.
   Never revert it.
9. **Durable-doc audit — `docs/README.md`.** Read the spec-002 optimizer surface end to end and
   re-derive each claim against the symbols named, reporting the zeros. The passages, by line at plan
   time: `:53` (the singleton-in-a-factory rule and the [Plan cache] pointer), `:55` ("the optimizer
   extension turns nested selections into `select_related`, `prefetch_related`, and `only` calls"),
   `:87`-`:88` (the root-resolver/one-plan statement — the O3 gate), `:105` (`get_queryset` visibility
   cooperating via `Prefetch` downgrade — O6), `:106` (the long shipped-surface paragraph naming the
   O2 walk, the O5 `only()` plan, the O6 downgrade, the `0.0.10` evaluated-queryset and
   non-`QUERY` guards). Symbols to re-derive against: `optimizer/extension.py::DjangoOptimizerExtension.resolve`
   (the `info.path.prev is not None` gate), `optimizer/walker.py::plan_optimizations`,
   `optimizer/plans.py::OptimizationPlan.apply`, `optimizer/walker.py::_target_has_custom_get_queryset`,
   `utils/querysets.py::normalize_query_source`. `docs/README.md` is hand-authored and **clean** in
   `git status`, so a correction there is a direct edit with no attribution hazard — but only if the
   sweep finds a falsified claim. It found none at plan time.
10. **Durable-doc audit — `docs/TREE.md`.** Run `uv run python scripts/build_tree_md.py --check` and
    record the output (`up to date`, exit 0, at plan time). Then scan the feeding module docstrings
    for the O1-O6 modules — `optimizer/__init__.py`, `extension.py`, `walker.py`, `plans.py`,
    `types/base.py`, `types/resolvers.py`, `types/finalizer.py` — for **staging** language that would
    render shipped behavior as unbuilt: `planned`, `Slice N`, `after Slice N`, `TODO(`. At plan time
    every `planned` hit under `optimizer/` is the domain noun (`planned_resolver_keys`, "fully
    unplanned"), not staging language, and there is no `TODO(spec-002` anywhere.
    **Boundary, stated because it is the one place R3 could quietly become a code cycle:** package
    source is **read-only in this cycle** (`build-002-optimizer-0_0_2.md` `## Build-wide context
    flags`). If a docstring genuinely does need fixing, that is an **escalation recorded under
    `### Notes for Worker 1 (spec reconciliation)`, not an edit** — and the docstring fix plus its
    regenerate would then land together in whatever pass the maintainer authorizes. Never hand-edit
    the rendered tail of `docs/TREE.md`.
11. **Durable-doc audit — `docs/GLOSSARY.md`.** Read the three entries card 2's CSV anchors resolve
    to and confirm each describes the shipped O1-O6 surface: `## `DjangoOptimizerExtension``
    (`:712`-`:748`), `## `only()` projection` (`:1380`-`:1389`), `## `DjangoType``.
    `check_spec_glossary.py` proves the *heading exists*; whether the prose is true is a read. Then
    record F2 exactly as `### Findings already verified at plan time` F2 specifies — **quote the four
    sites, state both readings, change nothing.**
12. **Durable-doc audit — `KANBAN.md` card `DONE-002-0.0.2`** (rendered around `:4850`-`:4905` at
    plan time). Walk its `#### Glossary terms` table (3 rows, matching the CSV), `#### Package files`
    (12 paths — **all 12 verified to exist on disk at plan time**; note that a `(historical)` marker
    is `TrackedPath.is_current = False` and is legitimate), `#### Scope` (the seven O1-O6 bullets),
    `#### Files likely touched`, and `#### Verified in upstream`. Also confirm `KANBAN.md:145`
    (the spec index row) and `:2560` (*"our O3 root gate (`info.path.prev is None`, spec-002)"*) are
    still accurate. If any of it needs a change, it is an ORM edit plus a regenerate under the same
    rules as steps 4-7; if none does, **say so and record what was read**.
13. **Cross-reference sweep, direction 1 — inbound.** Re-run the grep; the build plan's
    `### Every reference TO spec-002` table is a **verification list, not to be trusted** — its line
    numbers have already moved (`KANBAN.md:2556`->`:2560`, `:4855`->`:4859`, from the concurrent
    session's card writes). Plan-time result, for Worker 2 to reproduce or correct: `KANBAN.md`
    **7 occurrences** on lines 145, 310, 2560, 4859; `KANBAN.html` **6**, all in the `:97` data block;
    `spec-003` 4; `spec-004` 1; `spec-005` 5; `spec-006` 3; `spec-033` 4; `spec-035` 8; `spec-001` 4;
    `spec-001`'s rationale 23; plus the per-cycle `docs/builder/` artifacts. **Zero** in `README.md`,
    `GOAL.md`, `TODAY.md`, `AGENTS.md`, `START.md`, `BACKLOG.md`, `CHANGELOG.md`, `docs/README.md`,
    `docs/TREE.md`, `docs/GLOSSARY.md` — report the zeros. Also confirm **no pre-archive
    `docs/spec-002…` path survives anywhere** (zero at plan time). Sibling specs are read-only: a
    staleness found there is F4's maintainer item, never an edit.
14. **Cross-reference sweep, direction 2 — outbound.** Every link definition the spec and the
    rationale emit, resolved on disk from its **own file's** directory with the fragment stripped,
    plus every in-page fragment resolved against a surviving heading in the target. Plan-time result:
    spec **4/4 used, 0 undefined, 0 orphaned, 0 broken paths, 0 inline cross-file links**; rationale
    **19/19** with the same zeros and all **7** `#<frag>` targets resolving. Re-derive; do not
    inherit. **Slugger trap, live:** `check_spec_glossary.py::github_anchor` fed a raw reference-link
    heading gives a false negative, and it also collapses whitespace runs where GitHub replaces
    spaces one at a time — so a checker must strip link markup **before** slugging and must **not**
    collapse runs. Three passes in the sibling cycle copied the broken method before it was caught.
15. **Cross-reference sweep, direction 3 — internal.** The spec<->rationale pair's own consistency:
    every rationale entry names the spec decision it belongs to by heading **and** anchor
    (`BUILD.md` `## Spec rationale extraction`, the reader's rule); the three entries keyed to
    removed headings (`## O4 extraction`, `## Open questions`, `## Current state`) say so in their
    own lead and their link definitions point at **surviving** headings; the spec's own pointer
    sentences (`## Purpose` line 8, `## Problem statement` line 18, `## Architecture decision`
    line 27) resolve. Confirm the rationale is at `docs/SPECS/appx/` alongside the terms CSV, that
    nothing spec-002-related is stranded at the `docs/` root, and that the spec's companion
    reference carries the `appx/` prefix (`AGENTS.md` rule 26).
16. **`SpecDoc` / terms-CSV chain.** Confirm from the DB, read-only: `SpecDoc` for card 2 reads
    `path` = `docs/SPECS/spec-002-optimizer-0_0_2.md` and that file exists on disk;
    `Card.objects.get(number=2)` is `DONE-002-0.0.2` / `done` / `0.0.2`; `card.glossary_links.count()`
    is 3 and its `raw_text` values match the CSV's three rows. (`SpecDoc.url` is a read-only
    `@property` deriving from `path` — assigning `url=` raises.) Confirm the CSV is **one row per
    anchor** (3 rows / 3 distinct anchors; `check_spec_glossary` tolerates many terms per anchor,
    `import_spec_terms` does not tolerate a duplicate anchor). Then quote both constraint commands:

    ```
    uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md
    uv run python examples/fakeshop/manage.py import_spec_terms --check
    ```

    Both must exit 0. Then discharge F3 by **recording the measurement and the decision** — the
    four unlinked-but-glossary-backed terms, and that the set stands at three deliberately.
17. **Staged-anchor sweep** (`BUILD.md` `## Cross-slice integration pass` step 6, folded into R3 by
    the build plan's artifact list):

    ```
    grep -rEn 'TODO\(spec-002|TODO-(ALPHA|BETA|STABLE)-002' .
    ```

    excluding `KANBAN.md` / `KANBAN.html` / `BACKLOG.md`, where `TODO-<MILESTONE>-<NNN>` legitimately
    names an unshipped board card. **Count occurrences of the shortest distinctive token, never
    matching lines.** Plan-time result: **2 occurrences, both on
    `docs/builder/build-002-optimizer-0_0_2.md:222`** — the build plan's own checklist line, which
    contains both patterns. Expect the count to rise once this artifact lands, for the same reason:
    per-cycle `docs/builder/` artifacts describing the sweep are not shipped source. **Any anchor in
    package source, `tests/`, or `examples/` is `revision-needed`.** Report the classification, not
    just the number.
18. **Format and validate.** `uv run python scripts/check_trailing_commas.py --check <the .md files
    this pass touched>` and `git diff --check` over the same set. **Never `.`** — a repo-wide run
    would sweep the concurrent session's files. No `ruff` at all: R3 touches no `.py` file. No
    `pytest`, with or without flags.

### The replacement `CardItem.text`, verbatim

Copied character-for-character from `docs/builder/bld-002-r2-spec_reconciliation.md`
`### The `KANBAN.md:310` decision, written for R3 to execute` — the **corrected** version R2's final
verification produced after Worker 3's Medium 1, not the build pass's original. Reproduced here so
Worker 2 does not have to hunt for it.

**It is one paragraph on one line.** The blockquote line breaks in R2's artifact are its own
formatting; the stored `CardItem.text` is a single unwrapped string, exactly as the current 606-char
value is. The fenced block below is the string to store:

```text
`docs/SPECS/spec-002-optimizer-0_0_2.md` carries one status-shaped section left: `## Visibility status`. The spec-002 residual cycle discharged the rest - `## Open questions` and `## Current state` are gone, and `## Shipped slices` and `## Implementation checklist` survive the argument on their merits, since a past-tense fact about what shipped is not a promise about the present. `## Visibility status` stays because two live pointers would break with it. First, `spec-006-public_surface-0_0_3.md` names it **twice** - once as the quoted section title "Visibility status", once as "the local visibility-status amendment" - as the place the optimizer-visibility decision is recorded. Second, the companion `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` is the only file that cites spec-002 by `#anchor` at all, and one of its link definitions targets `#visibility-status`, so a retitle must re-point that definition in the same change. Retire the heading in the cycle that owns `spec-006`, not this one, and re-point the companion there. `spec-003-optimizer_nested_prefetch_chains-0_0_2.md`'s "current state, visibility status, and checklist" instruction is now stale in wording: it is a discharged when-O4-ships note naming a section that no longer exists.
```

Verification handles, measured at this pass by reconstructing the string from R2's blockquote (strip
the leading `> ` from each of its 15 lines, join with single spaces):

- length **1268** characters (the current value is 606);
- `sha256` = `041f0354993a32ad8b687dae00636544f761ad8edab7f2534c545a50f4971040`;
- pure ASCII (`str.isascii()` is `True`) — no em dashes, no smart quotes.

Every claim in it was re-verified at this pass: one status-shaped heading survives; `## Open
questions` and `## Current state` are both absent; `spec-006…:136` names the quoted title
`"Visibility status"` and `:147` names *"the local visibility-status amendment"*, two sites and two
different spellings; the rationale's `[spec-002-visibility]` def targets `#visibility-status`;
`spec-003…:333` names a section that no longer exists.

### Test additions / updates

**None owed, and none possible.** R3 changes no package behavior — it writes DB rows, three generated
Markdown/HTML files, and this artifact. There is no `.py` file in its write set and therefore no
branch a test could pin. `AGENTS.md` rule 15 forbids a `pytest` run after edits, and the full sweep
is the final gate's, not R3's. The executable checks standing in for tests are all already named
above:

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md` (exit 0)
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` (exit 0)
- `uv run python scripts/build_tree_md.py --check`
- `uv run python scripts/check_trailing_commas.py --check <touched .md files>`
- `git diff --check`
- the two-consecutive-regenerate byte-stability check on `KANBAN.md`, `KANBAN.html`, and
  `docs/GLOSSARY.md`

**Coverage:** no worker runs `pytest` with any `--cov*` flag in any pass. `--no-cov` is the only
permitted coverage-shaped flag, and R3 invokes `pytest` at all in neither form.

Temp-test opportunity for Worker 3: the link / anchor / on-disk-path checker this cycle family has
now hand-written several times belongs under `docs/builder/temp-tests/r3-spec002/` (gitignored, and
deliberately suffixed — `r3-spec001` exists from the prior cycle and is neither reused nor deleted).
Promoting it to `scripts/` is hand-off item 8 and a maintainer call; R3 does not open it.

### Implementation discretion items

Assessed and delegated to Worker 2 — each is a shape choice between equally valid options, not an
architectural question:

- **The shape of the ORM shell invocation** — a `manage.py shell -c` one-liner, a heredoc, or a
  throwaway script under `docs/builder/temp-tests/r3-spec002/`. The constraints are fixed (Django
  ORM, `.save()`, never raw SQL, locate by substring, assert exactly one match); the spelling is
  Worker 2's.
- **The order of the read-only verification legs** (steps 9-17). They are independent of each other
  and of the DB edit, and any order that records every result is correct. The DB edit and its
  regenerate (steps 3-8) stay in the order given.
- **The hashing tool for byte-stability** — `shasum -a 256`, `md5`, `cmp` against a copy in the
  scratch dir. Any of them proves the property, provided both runs are hashed and both results are
  recorded.
- **The scratch checker's implementation** for step 14, provided it strips reference-link markup
  **before** slugging a heading and does **not** collapse whitespace runs. Both traps are live in
  `check_spec_glossary.py::github_anchor` today.
- **How the F2 escalation is laid out in the build report** — a table, a list, or prose. The content
  is fixed (four quoted sites with line numbers, both readings, zero edits); the presentation is not.

**Not delegated, stated so no pass improvises:** which role may edit a spec file (only Worker 1 —
`BUILD.md` `## Spec reconciliation`); whether a generated doc is ever fixed by hand (never); and
whether F2 or F3 becomes an edit (neither does).

### Boundary count, hot path, floor verification, failability

Answered here so no later pass guesses, per `worker-1.md` `### Boundary count is a split trigger` and
`### Hot-path declaration`. Silence on any of these would read as an omission, so each is stated:

- **New runtime boundaries added by R3: zero.** R3 adds no guard, cap, gate, rejection path, or
  validation branch — it edits one DB text column, regenerates three files, and records measurements.
  The slice-splitting question therefore does not arise. **`### Failability proofs` will legally be
  empty:** the correct entry is `None; this pass introduced no new boundary.` Worker 2 keeps the
  heading and writes that line rather than omitting the section or inventing a proof.
- **Hot path: none**, for this cycle and for this item. The build plan declares
  `Hot-path declaration: none`, and R3 changes nothing that runs per request, per resolver, per row,
  per connection, or per outbound message. Worker 2 writes
  `Not applicable; plan declares no hot path.`
- **Floor verification: none**, for this cycle and for this item. The build plan declares
  `Floor-verification scope: none`; R3 touches no Django / Strawberry / channels integration seam.
  Worker 2 writes `Not applicable; plan declares floor-verification scope none.`
- **Static inspection helper (`scripts/review_inspect.py`): skipped, with the reason recorded.**
  `BUILD.md` `### When to run the helper during build` triggers on `.py` files; R3's diff contains
  none.

### Files Worker 2 may write

Everything else in the tree is read-only for Worker 2.

- `examples/fakeshop/db.sqlite3` — **via the Django ORM only**, and only the one `CardItem.text`
  named in F1 (plus any additional DB row a durable-doc finding forces, which routes through steps
  11-12's same verification rules).
- `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md` — **via regenerate only**, never by hand.
- `docs/builder/bld-002-r3-doc_completion_archive.md` — this artifact (build report sections).
- `docs/builder/worker-memory/worker-2.md`.
- Throwaway scratch under `docs/builder/temp-tests/r3-spec002/` (gitignored).

Explicitly **read-only for Worker 2**: all package source under `django_strawberry_framework/`; all
three test trees; `CHANGELOG.md`; every sibling spec; the active spec
`docs/SPECS/spec-002-optimizer-0_0_2.md` and its rationale (Worker 1 owns both);
`docs/SPECS/appx/spec-002-optimizer-0_0_2-terms.csv`; `docs/builder/build-002-optimizer-0_0_2.md`;
`docs/TREE.md`, `docs/README.md`, `README.md`, `GOAL.md`, `TODAY.md` (audited; a correction in one of
the hand-authored ones is licensed **only** if the sweep proves a falsified spec-002-surface claim,
and the plan-time sweep found none).

**Baseline-dirty concurrent-session paths Worker 2 must never edit or revert** (`AGENTS.md` rule 34):
`docs/SPECS/spec-042-debug_toolbar-0_0_14.md`, `spec-043-test_client-0_0_14.md`,
`spec-044-debug_extension-0_0_14.md`, `spec-050-debug_extraction-0_0_19.md`,
`spec-051-boundary_dry_squeeze-0_0_20.md`, `examples/fakeshop/test_query/README.md` — plus
`examples/fakeshop/db.sqlite3`, `KANBAN.md`, and `KANBAN.html`, which Worker 2 *does* write, but only
by ORM edit and regenerate, **on top** of the concurrent state, never by revert.

### Spec slice checklist (verbatim)

R3 is neither a spec slice nor a review round. Spec-002's `## Implementation checklist` is the
shipped O1-O6 roster — six boxes, all already `- [x]` at `0.0.2` — so there is nothing to copy
verbatim. The boxes below are therefore built from **R3's own scope**, one per verifiable obligation,
in the position `BUILD.md`'s `### Dispatched findings checklist` also occupies; both discipline
statements govern unchanged.

**Boxes stay `- [ ]` at planning.** Worker 2 ticks `- [x]` **only** what actually landed in its own
diff or was actually measured, and states any deferral in the build report rather than ticking. A
verification obligation with a clean result is discharged by **recording the measurement** and
ticking. Worker 3 walks the list: a box the diff does not address with no recorded deferral is a
Medium finding, and so is a box ticked with no matching evidence. Worker 1 re-audits every tick at
final verification.

**A — the kanban-DB edit and its regenerate (the only mutation in R3)**

- [x] **A1** — Card `TODO-ALPHA-052-0.1.0` and its target `CardItem` verified to exist **before**
      mutating, located by the substring `status-shaped sections` with **exactly one** match asserted
      (never by the plan's recorded pk — the concurrent session created two further `Scope` items on
      this card at 2026-08-07T04:13:51). Old pk / `section` / `order` / text length recorded.
- [x] **A2** — `CardItem.text` replaced with the verbatim string in
      `### The replacement `CardItem.text`, verbatim`, applied through the **Django ORM** with
      `.save()` (never raw SQL — only `.save()` fires the `post_save` that creates the `UUIDModel`
      side-row the render needs). Byte-identity proved after the write: length **1268** and `sha256`
      `041f0354993a32ad8b687dae00636544f761ad8edab7f2534c545a50f4971040`.
- [x] **A3** — `scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`, and
      `scripts/build_glossary_md.py` all re-run from the repository root, applied **on top** of the
      concurrent session's dirty state with nothing reverted and no rendered file hand-edited.
- [x] **A4** — Verified by **two-consecutive-regenerate byte-stability** (all three outputs hashed
      twice, both sets recorded and identical) plus a **spot-check** that card 052's rendered bullet
      reads correctly and its sibling bullet at `order` 7 is unchanged — never by "`git diff` is
      clean". The mixed diff is handed to the maintainer.
- [x] **A5** — `import_spec_terms --check` re-run after the regenerate and quoted; **exit 0 is the
      contract**, not the done-card number. `docs/GLOSSARY.md`'s post-regenerate state explicitly
      classified: clean (expected) or dirty-and-therefore-drift-to-investigate-and-report.

**B — durable-doc audit of the spec-002 optimizer surface**

- [x] **B1** — `docs/README.md` audited at `:53`, `:55`, `:87`-`:88`, `:105`, `:106`, each claim
      re-derived against `optimizer/extension.py::DjangoOptimizerExtension.resolve`,
      `optimizer/walker.py::plan_optimizations`, `optimizer/plans.py::OptimizationPlan.apply`,
      `optimizer/walker.py::_target_has_custom_get_queryset`, and
      `utils/querysets.py::normalize_query_source`. Zeros reported.
- [x] **B2** — `docs/TREE.md` re-verified with `uv run python scripts/build_tree_md.py --check`, and
      the O1-O6 feeding module docstrings scanned for **staging** language (`planned`, `Slice N`,
      `after Slice N`, `TODO(`). Package source is read-only this cycle, so a genuinely needed
      docstring fix is an **escalation under `### Notes for Worker 1`, not an edit**; the rendered
      tail is never hand-edited.
- [x] **B3** — `docs/GLOSSARY.md`'s three card-2 entries (`## `DjangoOptimizerExtension``,
      `## `only()` projection`, `## `DjangoType``) read end to end and confirmed to describe the
      shipped O1-O6 surface, not merely to exist.
- [x] **B4** — `KANBAN.md` card `DONE-002-0.0.2` audited (`#### Glossary terms`, `#### Package files`
      and their on-disk existence, `#### Scope`, `#### Files likely touched`, `#### Verified in
      upstream`), plus `KANBAN.md:145` and `:2560`. What was read is recorded even when nothing
      changed.
- [x] **B5** — The `0.0.2`-versus-`0.0.3` disagreement **recorded and escalated as ONE maintainer
      item, with zero edits**: all four sites quoted with line numbers (`docs/GLOSSARY.md:714`,
      `:1382`; the kanban card's `target_version`; `CHANGELOG.md`'s `[0.0.2]` and `[0.0.3]` entries),
      both readings stated. `CHANGELOG.md` is closed by `AGENTS.md` rule 21; the GLOSSARY side is
      **out of scope** per this plan's F2 ruling and no `GlossaryTerm` row is touched.

**C — the three-direction cross-reference sweep**

- [x] **C1** — *Inbound.* Every reference TO spec-002 re-derived by grep, the build plan's table
      treated as a verification list rather than trusted (two of its line numbers have already
      moved). Occurrences counted, not matching lines. The confirmed-zero set reported explicitly,
      and the absence of any pre-archive `docs/spec-002…` path confirmed.
- [x] **C2** — *Outbound.* Every link definition the spec (4) and the rationale (19) emit resolved
      on disk from its own file's directory with the fragment stripped, plus every in-page fragment
      resolved against a surviving heading. Undefined refs, orphaned defs, and inline cross-file
      links all reported as counts.
- [x] **C3** — *Internal.* The spec<->rationale pair's own consistency: every entry keyed to a spec
      decision by heading **and** anchor; the three entries keyed to removed headings saying so and
      pointing at surviving ones; the spec's three pointer sentences resolving; both companions at
      `docs/SPECS/appx/` with nothing stranded at the `docs/` root.
- [x] **C4** — Read-only sibling staleness recorded and **not edited**: `spec-003…` at `:4`, `:27`,
      `:333`, and `:335` (R2's hand-off named only two of the four), and the confirmation that
      `spec-006…:136` / `:147` are **live and correct** so a later sweep does not "fix" them. What is
      **not** in the escalation is named too — the `spec-002` survivals in `CHANGELOG.md` and
      `KANBAN.md` prose are correct as history.

**D — `SpecDoc` / terms-CSV verification and the staged-anchor sweep**

- [x] **D1** — `SpecDoc` for card 2 confirmed to read `path` =
      `docs/SPECS/spec-002-optimizer-0_0_2.md` with the file present on disk;
      `Card.objects.get(number=2)` is `DONE-002-0.0.2` / `done` / `0.0.2`; `glossary_links.count()`
      is 3 and matches the CSV rows. (`SpecDoc.url` is a read-only `@property`; assigning it raises.)
- [x] **D2** — Both constraint commands quoted and both exit 0:
      `check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md` and
      `import_spec_terms --check`. The terms CSV confirmed **one row per anchor** (3 rows / 3
      distinct anchors), which `import_spec_terms` requires and `check_spec_glossary` does not.
- [x] **D3** — The terms-CSV completeness question **decided and recorded**: the set stands at three
      deliberately, with the measured list of glossary-backed terms the spec names without linking
      (four at plan time: `DjangoConnectionField`, `finalize_django_types`, FK-id elision, Visibility
      boundary — and **not** `Plan cache` or `Meta.optimizer_hints`, which R2's hand-off named but
      which do not appear in the spec). **No CSV row added; no CSV edited to make any check pass.**
- [x] **D4** — Staged-anchor sweep run:
      `grep -rEn 'TODO\(spec-002|TODO-(ALPHA|BETA|STABLE)-002' .`, excluding `KANBAN.md` /
      `KANBAN.html` / `BACKLOG.md`. **Occurrences counted, not matching lines**, and each classified.
      Plan-time result: 2, both on `docs/builder/build-002-optimizer-0_0_2.md:222`, a per-cycle
      artifact. Any anchor in package source, `tests/`, or `examples/` is `revision-needed`.

### Notes for Worker 2

- **You may not edit any spec file, the terms CSV, `CHANGELOG.md`, package source, or a test.** If
  your audit finds something wrong in one, record it under
  `### Notes for Worker 1 (spec reconciliation)` — that is the hand-over, and a recommendation with
  no named owner dies in an artifact. Say which pass you are handing it to.
- **Never `git checkout`, `git restore`, `git stash`, or `git worktree` anything.** Nine paths carry
  a concurrent session's uncommitted work, three of them files you will write. Unexpected churn is a
  stop-and-report, never a tidy-up. Read HEAD read-only with `git show HEAD:<path>` into a scratch
  path **outside** the repo.
- **Scope every write-mode tool run to your own files.** `check_trailing_commas.py` without an
  explicit file list, or any `ruff --fix .`, would sweep the concurrent session's work.
- **Count occurrences of the shortest distinctive token, never matching lines, and measure as you
  write the number.** This is the cycle's dominant practice failure: R1 and R2 lost several asserted
  counts to re-derivation, and in two of them the *premise* was wrong as well as the arithmetic. Fix
  a bad count by **re-forming** the claim — name the symbol, list the line numbers — not by
  renumbering it, because a renumber leaves the false premise standing behind a true number. This
  plan's own F3 is an instance: two of R2's three named terms do not exist in the spec.
- **Re-measure `git status` at your open AND your close, and report both.** The set has moved between
  passes in this cycle family, and `import_spec_terms --check`'s done-card number moved 48 -> 49
  mid-cycle in the sibling one.
- **Report the zeros.** A sweep that found nothing is a result. An unstated absence is
  indistinguishable from an unrun check, and Worker 3 is instructed to treat it that way.

### Notes for Worker 3

- **The sharpest question for this item is completeness, not correctness.** R3's one mutation is
  small and mechanically checkable; what it can silently get wrong is **stopping too early**. Re-run
  the sweeps yourself — particularly C1 (inbound) and B1/B4 (the durable-doc reads) — and treat a
  reported absence with no stated command as an unrun check.
- **Re-derive the replacement text's byte-identity independently.** Reconstruct it from
  `bld-002-r2-spec_reconciliation.md`'s blockquote yourself and compare against what is stored in the
  DB; do not accept the length or the hash from this plan or from the build report.
- **Attribution before conclusion, in both directions.** A `KANBAN.md` / `KANBAN.html` /
  `db.sqlite3` diff is largely the concurrent session's and is not R3's to explain — but a
  **missing** correction cannot be excused as concurrent-session territory, because the target
  `CardItem` is tracked content the concurrent session is not writing.
- **The acceptance evidence for the DB-backed work is two consecutive regenerates producing
  byte-identical output plus spot-checks**, never a clean `git diff`. If the build report offers a
  clean diff as proof, that is a finding.
- **Check that F2 and F3 stayed escalations.** A `GlossaryTerm.body` edit, a `CHANGELOG.md` edit, or
  a new terms-CSV row would each be a scope violation this plan explicitly ruled out, with reasons.
- Temp tests belong under `docs/builder/temp-tests/r3-spec002/` (gitignored). `r3-spec001` exists
  from the prior cycle — do not reuse or delete it.

### Notes for Worker 1 (spec reconciliation)

Carried into R3's final verification and the final gate. This list **updates R2's consolidated
hand-off keys** rather than starting a third set.

1. **Hand-off item 1 (`KANBAN.md:310`) — R3 EXECUTES IT.** Owner is this item's Worker 2, per steps
   3-8 and boxes A1-A5. Final verification confirms the stored text is byte-identical and that the
   render carries it.
2. **Hand-off item 10 (the `0.0.2`/`0.0.3` disagreement) — RULED OUT OF SCOPE HERE, ESCALATED.**
   F2 carries the ruling and its four reasons. For the final gate's `### Deferred work catalog`, as
   one maintainer item covering all four sites.
3. **Hand-off item 11 (terms-CSV completeness) — DECIDED AND CLOSED.** The set stands at three; F3
   carries the reasoning and the corrected measurement. Note for the record that R2's item named two
   terms (`Plan cache`, `Meta.optimizer_hints`) that do not appear in the spec — the premise, not
   just the count, was wrong.
4. **Hand-off item 4's sibling staleness — SCOPE CORRECTED.** `spec-003…` is stale in **four**
   places (`:4`, `:27`, `:333`, `:335`), not the one R2 named. All read-only. Owner: the maintainer /
   whoever next opens `spec-003`. `spec-006…:136` / `:147` are live and correct and must not be
   swept up with them.
5. **Hand-off item 8 (the spec/rationale consistency checker) — STILL OPEN, still unowned, carried
   to the final gate's `### Deferred work catalog`.** R3 does not open it; step 14's slugger traps
   are the third and fourth measured arguments for it.
6. **Hand-off item 9 (the `_optimizer_field_map` four-site rename-sweep residue) — UNCHANGED,
   maintainer-owned.** `tests/optimizer/test_field_meta.py` (three test names) and
   `scripts/review_inspect.py` are outside every residual item's write set. Not re-opened here.
7. **The interstitial-pass condition, restated so the final verification can check it happened if it
   was triggered:** any needed edit to the spec or its rationale is a Worker 1 pass dispatched
   **after `built`, before the review**. If Worker 2 recorded such a need and no interstitial pass
   ran, the review saw an unreviewable gap and the item is `revision-needed`.
8. **`docs/GLOSSARY.md` was CLEAN at this pass's open.** If it is dirty at final verification,
   attribute it positively (`git show HEAD:docs/GLOSSARY.md` into a scratch path outside the repo,
   then diff) before concluding anything — this cycle changes no glossary row.

---

## Build report (Worker 2)

Every number below was measured at this pass, with the command quoted. Nothing is inherited from the
plan's baseline table; where a plan number moved, the move is named and attributed.

### Files touched

Grounded in `git status --short` at this pass's close, not in memory.

- `examples/fakeshop/db.sqlite3` — **one** `CardItem.text` replaced, via the Django ORM and `.save()`
  (never raw SQL, so the `post_save` that creates the `UUIDModel` side-row fired). Card
  `TODO-ALPHA-052-0.1.0`, section `Scope`, `order` 8, pk 1260. Nothing else on the card, and no other
  row in any table, was written. The file was **already dirty** from the concurrent session; this
  write lands on top of that state with nothing reverted.
- `KANBAN.md` — regenerated by `scripts/build_kanban_md.py`. The only semantic change this pass
  contributes is the card 052 bullet at `:310`; the rest of the diff is the concurrent session's.
- `KANBAN.html` — regenerated by `scripts/build_kanban_html.py` (data block only; the Vue shell is
  hand-edited and the script owns the boundary — it was not touched).
- `docs/GLOSSARY.md` — regenerated by `scripts/build_glossary_md.py` and **byte-unchanged**; see
  `### Validation run`. It is not a modified path in `git status`.
- `docs/builder/bld-002-r3-doc_completion_archive.md` — this build report, the 18 checklist ticks,
  and `Status: built`. No prior section was edited.
- `docs/builder/worker-memory/worker-2.md` — one appended entry under `## spec-002 residual cycle`,
  after consolidating the file's earlier entries.
- `docs/builder/temp-tests/r3-spec002/` — four throwaway scripts plus one generated
  `replacement.txt` (gitignored). `r3-spec001` from the prior cycle was neither read, reused, nor
  deleted.

**Not touched, deliberately:** no `.py` under `django_strawberry_framework/`, no test in any of the
three trees, no spec, no rationale, no terms CSV, `CHANGELOG.md`, `docs/README.md`, `docs/TREE.md`,
`README.md`, `GOAL.md`, `TODAY.md`. The durable-doc audit (B1) licensed an edit to `docs/README.md`
only on a falsified claim and found none, so none was made.

### Tests added or updated

**None, and none are owed.** R3 changes no package behavior: its write set holds one DB text column,
three generated documents, this artifact, and a gitignored memory file. There is no `.py` file in the
diff and therefore no branch a test could pin. Saying so explicitly rather than writing a test that
pins nothing is the discharge. `AGENTS.md` rule 15 forbids a `pytest` run after edits and none was
run, with or without flags; no `--cov*` flag was used anywhere in this pass.

The executable checks standing in for tests are all in `### Validation run` below.

### Validation run

**No `ruff` invocation of either kind.** This pass touched **zero** `.py` files in the repository, so
`ruff format` and `ruff check --fix` have no files to scope to. Running either against `.` would be a
repo-wide write-mode run over the concurrent session's six dirty files, which
`worker-2.md` `## Build job` step 5 forbids for exactly that reason. The four scratch scripts live
under the gitignored `docs/builder/temp-tests/` and are not slice output.

| Check | Command | Result |
|---|---|---|
| Terms importability | `uv run python examples/fakeshop/manage.py import_spec_terms --check` | `OK: 49 done cards have glossary links.` **exit 0** |
| Spec/glossary anchors | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md` | `OK: 3 terms - all have glossary entries and at least one spec link.` **exit 0** |
| Rendered tree | `uv run python scripts/build_tree_md.py --check` | `docs/TREE.md is up to date.` **exit 0** |
| Layout gate | `uv run python scripts/check_trailing_commas.py --check docs/builder/bld-002-r3-doc_completion_archive.md` | **exit 0** (scoped to this pass's one tracked `.md`; never `.`) |
| Whitespace | `git diff --check` (repo-wide, read-only) | **exit 0**, no output |
| Whitespace, this artifact | direct scan — it is **untracked**, so `git diff --check` structurally cannot see it | 0 trailing-whitespace lines, 0 tabs, 0 conflict markers |

**Byte-stability of the three generated documents** — the acceptance evidence for DB-backed work,
because a clean `git diff` is impossible here and would prove nothing if it were possible
(`BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`). All three
were hashed before the write, after one full regenerate, and after a second identical regenerate:

| File | Before the ORM edit | After regenerate 1 | After regenerate 2 |
|---|---|---|---|
| `KANBAN.md` | `28b12543cffec50b…` | `bf4de38b29307849…` | `bf4de38b29307849…` |
| `KANBAN.html` | `6a5df8ab4d4a72d0…` | `fd45a0f5b363a617…` | `fd45a0f5b363a617…` |
| `docs/GLOSSARY.md` | `563206856eabd961…` | `563206856eabd961…` | `563206856eabd961…` |

Full digests, `shasum -a 256`:

```
28b12543cffec50b7c471b0c9277dd60dd8757ff7dec828d4a5b3420d1f11d0d  KANBAN.md      (pre-edit)
bf4de38b2930784970df631a1b506a78ba91b510dac8108e93735bd9fd5abd58  KANBAN.md      (both regenerates)
6a5df8ab4d4a72d0d9bfaa8ba7e6b048c050f90af3a38ca3e052a771443815b9  KANBAN.html    (pre-edit)
fd45a0f5b363a6179913a6e4d61fd53384d63aa7cc55a8b5803dd96556b2c577  KANBAN.html    (both regenerates)
563206856eabd961f2ded7035c1a6b275a9b2a74694e5051ad5aa361b03a3cbe  docs/GLOSSARY.md (all three readings)
```

Regenerate 1 and regenerate 2 produce **byte-identical** output for all three files. The generators
reported `67 cards (excluded 1 backlog cards) and 15 board docs`, `68 cards, 15 board docs, and 11
lookup arrays`, and `142 terms, 146 category memberships, 1042 spec mentions across 49 specs` on both
runs.

**`docs/GLOSSARY.md` classification: CLEAN, as expected.** Its digest is identical before the ORM
edit and after both regenerates, and it does not appear in `git status --porcelain` at this pass's
close. R3 changed no glossary row, so there is no drift to investigate and nothing to hand up on this
point. Recording the null result rather than omitting it is deliberate: an unstated absence is
indistinguishable from an unrun check.

**`git status --porcelain` at this pass's close — 15 paths:**

```
 M KANBAN.html                                        <- SLICE-INTENDED (regenerate) + concurrent
 M KANBAN.md                                          <- SLICE-INTENDED (regenerate) + concurrent
 M docs/SPECS/spec-002-optimizer-0_0_2.md             <- THIS CYCLE (R2), untouched by R3
 M docs/SPECS/spec-042-debug_toolbar-0_0_14.md        <- concurrent
 M docs/SPECS/spec-043-test_client-0_0_14.md          <- concurrent
 M docs/SPECS/spec-044-debug_extension-0_0_14.md      <- concurrent
 M docs/SPECS/spec-050-debug_extraction-0_0_19.md     <- concurrent
 M docs/SPECS/spec-051-boundary_dry_squeeze-0_0_20.md <- concurrent
 M examples/fakeshop/db.sqlite3                       <- SLICE-INTENDED (ORM edit) + concurrent
 M examples/fakeshop/test_query/README.md             <- concurrent
?? docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md  <- THIS CYCLE (R1 + R2)
?? docs/builder/bld-002-r1-rationale_move.md              <- THIS CYCLE
?? docs/builder/bld-002-r2-spec_reconciliation.md         <- THIS CYCLE
?? docs/builder/bld-002-r3-doc_completion_archive.md      <- THIS CYCLE (R3, this artifact)
?? docs/builder/build-002-optimizer-0_0_2.md              <- THIS CYCLE
```

Every path is either slice-intended and listed in `### Files touched`, or one of the nine known
concurrent-session paths the build plan's `## Baseline-dirty out-of-scope files` already names.
**Nothing unexpected appeared, and nothing was reverted.** The set is the same 15 the plan recorded
(its snapshot listed 14 because this artifact did not yet exist when it was written). The mixed
`KANBAN.md` / `KANBAN.html` / `db.sqlite3` diff is handed to the maintainer to reconcile at commit;
no attempt was made to separate it.

### Failability proofs

None; this pass introduced no new boundary.

R3 adds no guard, cap, gate, rejection path, or validation branch. It writes one DB text column,
regenerates three documents, and records measurements. The heading is kept rather than omitted so the
absence is legible as a judgement rather than an oversight.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

The plan's `### Implementation discretion items` delegated five shape choices. Each is recorded with
its reason.

- **ORM shell invocation: a throwaway script piped through `manage.py shell -c "$(cat …)"`**, not a
  one-liner. Three scripts landed under `docs/builder/temp-tests/r3-spec002/` — `inspect_card52.py`
  (read-only census), `apply_card52.py` (the mutation), `verify_chain.py` (the `SpecDoc` chain). Why
  this shape: the locate-by-substring assertion, the pre-write census, and the post-write hash check
  are one logical unit, and a file keeps them re-runnable and reviewable rather than reconstructable
  from shell history. The constraints the plan fixed were honoured exactly — Django ORM, `.save()`,
  never raw SQL, located by substring with `assert len(matches) == 1`.
- **The replacement string is derived, not transcribed.** `build_replacement.py` extracts it from
  **two independent sources** and asserts they agree: the fenced ```` ```text ```` block in this
  artifact's `### The replacement `CardItem.text`, verbatim`, and R2's own blockquote in
  `bld-002-r2-spec_reconciliation.md` reconstructed by stripping the leading `> ` from each of its
  **15** lines and joining with single spaces. Both produce length **1268** and `sha256`
  `041f0354993a32ad8b687dae00636544f761ad8edab7f2534c545a50f4971040`, both are pure ASCII, and
  `src_a == src_b` is `True`. Why two sources: a hand-copied 1268-character paragraph is exactly the
  operation that silently picks up a blockquote marker or a re-wrap, and the plan's instruction was
  to fix the copy rather than the assertion. Deriving it programmatically means there is no copy.
- **Hashing tool: `shasum -a 256`** for the generated files (plain, re-derivable by the reviewer) and
  `hashlib.sha256` inside the ORM scripts for the stored text (it must hash the column value, not a
  file).
- **Verification-leg order: B (durable docs) -> C (cross-reference) -> D (chain and anchors)**, run
  after the A block. The plan declared legs 9-17 independent; this order groups the two DB reads
  (B4's card walk and D1's `SpecDoc` chain) at the ends rather than interleaving them with the file
  sweeps, which kept the ORM invocations down to three.
- **The scratch link checker (`linkcheck.py`) strips link markup before slugging and does not
  collapse whitespace runs**, per the plan's two named traps. One further trap surfaced while writing
  it and is worth recording because it is the same class: **deleting** code spans before matching
  reference links destroys the link. A reference link here is routinely spelled ``[`only()`][ref]``,
  so removing the span leaves `[][ref]`, which the `\[([^\]]+)\]` pattern cannot match — the first
  run reported 3 spec orphans and 12 rationale orphans, all false. The fix is to **mask the span's
  content to same-length filler** rather than delete it, which preserves the brackets. That is a
  third live defect in the same family as `check_spec_glossary.py::github_anchor`'s two, and it
  strengthens hand-off item 8's case rather than opening it.

**Plan-vs-implementation drift: none.** No plan-level architectural call changed, so `Status:` is
`built` and not `revision-needed`. The plan's steps were executed as written; the only measured
divergences from its **baseline numbers** are the four in `### Notes for Worker 3` below, and each is
a number that moved for a named reason, not a contract that moved.

**Checklist ticks: all 18 boxes** (A1-A5, B1-B5, C1-C4, D1-D4 — five plus five plus four plus four).
Every one is ticked, and none is ticked on a plan claim: each rests on a command run in this pass.
There are no deferrals to state. (For the record, since the dispatch brief called it a 16-box list:
the enumeration `A1-A5, B1-B5, C1-C4, D1-D4` is 18 boxes, and the artifact carries 18. The
enumeration, not the count, was followed.)

#### A — the one mutation, in detail

The card and item were verified to exist **before** the write. `Card.objects.get(number=52)` returns
`TODO-ALPHA-052-0.1.0` / `todo` / `0.1.0` / *"Beta release (cleanup, verification, alpha → beta)"*.
The card carries **36** `CardItem`s across six sections; **8** of them are in `Scope`, at `order` 1,
4, 5, 6, 7, 8, 9, 10. Filtering on the distinctive substring `status-shaped sections` returned
**exactly one** row — pk **1260**, section `Scope`, `order` 8, old length **606**, old `sha256`
`ddf5ea0b9ac148cb93df8c841cb85ba5ceb413872eb3c9245865e4c99fddea77`.

The plan's warning was live and correct: the concurrent session's two later `Scope` items are
present, at `order` 9 (pk 1265, len 601) and `order` 10 (pk 1266, len 349), both `created_date`
2026-08-07T04:13:51 — twenty-five minutes after pk 1260's 03:48:30. It also added an `Open question`
item (pk 1267, same timestamp). The recorded pk **did** still resolve to the right row this time, but
that is a fact measured after the substring match, never the way the row was found.

After `.save()`, the row was re-read from the database: length **1268**, `sha256`
`041f0354…4971040`, matching the plan's handles exactly. The sibling `Scope` bullet at `order` 7
(pk 1259, the spec/rationale consistency checker, rendered at `KANBAN.md:309`) is **unchanged** — its
`sha256` is `4b9ca4703c9618a189d5ada4da5b6269bd696cbb3de79d3fb242a6ee98e4936a` both before and after
the write.

**Rendered spot-check.** After the regenerates, `KANBAN.md:310` carries the new bullet in full, and
`:309` still carries the consistency-checker bullet verbatim. The whole card 052 `Scope` block was
re-read; the other six bullets are unchanged.

**Occurrence accounting for the mutation, so the delta is a reading rather than an assurance.**
`grep -o 'spec-002' | wc -l` over `KANBAN.md` gives **9** at this close against the plan's **7**, and
over `KANBAN.html` gives **8** against **6**. Both deltas are `+2`, and both are exactly this
mutation: the old bullet named `spec-002` twice (the filename, and *"cites spec-002 by `#anchor`"*);
the new one names it four times (the filename, *"The spec-002 residual cycle"*, the rationale
filename, and *"cites spec-002 by `#anchor`"*). No third surface moved.

#### B — durable-doc audit

**B1 — `docs/README.md`, five passages, each re-derived against source.** Every claim holds; **zero**
falsified, so **zero** edits.

| Passage | Claim | Re-derived against | Verdict |
|---|---|---|---|
| `:53` | module-level singleton in a factory preserves the instance-bound Plan cache | `optimizer/extension.py::DjangoOptimizerExtension.__init__` #"self._plan_cache" — an **instance** attribute, so a per-request instance would lose it; `:40`-`:50`'s example does wrap it as `lambda: _optimizer` | holds |
| `:55` | the extension turns nested selections into `select_related`, `prefetch_related`, `only` | `optimizer/plans.py::OptimizationPlan.apply` applies all three, in the order `only()` -> `select_related()` -> `prefetch_related()` | holds |
| `:87` | returning a `QuerySet` from the root resolver gives the optimizer something to shape | `utils/querysets.py::normalize_query_source` returns `(source, isinstance(source, models.QuerySet))`; a `Manager` is coerced via `_coerced_manager_queryset` | holds |
| `:88` | walks the selected fields **once at the root** and applies **one** ORM plan | `optimizer/extension.py::DjangoOptimizerExtension.resolve` #"if info.path.prev is not None" returns the result untouched — the O3 gate | holds |
| `:105` | `get_queryset` cooperates with the optimizer via `Prefetch` downgrade, through one shared hardened boundary | `optimizer/walker.py::_target_has_custom_get_queryset` drives the branch; `utils/querysets.py::apply_type_visibility_sync` and `::apply_type_visibility_async` both exist | holds |
| `:106` | plan caching, FK-id elision, downgrade, strictness, `0.0.9` connection-aware, `0.0.14` strategy seam, `0.0.10` G1 + G2 | `_plan_cache` / `_execution_plan_cache`; `OptimizationPlan.fk_id_elisions`; `nested_connection_strategy=` kwarg on `__init__`; `_optimize` #"_result_cache" pass-through (G1); `walker.py` #"operation is OperationType.QUERY" gating projection (G2) | holds |

**B2 — `docs/TREE.md`.** `uv run python scripts/build_tree_md.py --check` -> `docs/TREE.md is up to
date.`, exit 0. The seven O1-O6 feeding modules (`optimizer/__init__.py`, `extension.py`,
`walker.py`, `plans.py`, `types/base.py`, `types/resolvers.py`, `types/finalizer.py`) were scanned
for `planned`, `Slice N`, `after Slice N`, and `TODO(`. Findings:

- **Zero** staging-language hits. Every `planned` occurrence is the domain noun —
  `planned_resolver_keys`, `finalized_planned_resolver_keys`, `DST_OPTIMIZER_PLANNED`, "unplanned",
  "fully-unplanned". `optimizer/__init__.py` and `types/base.py` have **no** hit of any pattern.
- **Zero** `Slice N` / `after Slice N` hits in all seven.
- **Two** `TODO(` hits, both `TODO(spec-035)` in `optimizer/walker.py` (at `:464` and `:1131`). Both
  are **inline body comments, not module docstrings**, so neither reaches `docs/TREE.md`, which
  renders from docstrings; both name spec-035, not spec-002, so neither is in D4's sweep either. **No
  escalation owed** — recorded so a later sweep does not read them as new.
- `docs/TREE.md`'s own `planned` occurrences (`:337`, `:346`, `:390`, `:709`, `:710`, `:855`, plus
  the two section preambles) are all the renderer's deliberate predicted-path feature — `planned by
  TODO-BETA-NNN-0.1.x` rows fed from the kanban DB. Not staging language, and not a defect.

Package source stayed read-only. Nothing needed a docstring fix, so no escalation was recorded under
`### Notes for Worker 1` for this leg.

**B3 — `docs/GLOSSARY.md`'s three card-2 entries, read end to end.**

- `## `DjangoOptimizerExtension`` (`:712`-`:748`) — its shipped-behavior list names all six slices:
  root-gated optimization (O3), `Manager` coercion and non-root/non-`QuerySet` passthrough (O3),
  `select_related` and `prefetch_related` and generated `Prefetch` objects (O1/O2), nested prefetch
  chains (O4), `only` projection with connector-column inclusion (O5), and the custom `get_queryset`
  downgrade from join to `Prefetch` (O6). It additionally carries the `0.0.10` G1 and G2 riders. It
  **describes** the shipped surface, not merely exists.
- `## `only()` projection` (`:1380`-`:1389`) — states the O5 contract plus the `0.0.10` G2 gate and
  the `0.0.11` live-test discharge. Accurate.
- `## `DjangoType`` (`:761`-) — `**Status:** shipped (`0.0.5`)`, which is correct for its **own**
  card; card 2 links it because spec-002's `## Problem statement` names `DjangoType` as the type that
  exposes the reverse relations O1 resolves. Its shipped-capability list is the type-system surface,
  not the optimizer's, and that is right.

**B4 — `KANBAN.md` card `DONE-002-0.0.2`** (rendered at `:4852`-`:4915` after the regenerate; the
plan's `:4850`-`:4905` moved with the concurrent session's writes and this pass's longer bullet).
Read in full; **nothing needed changing**, so no second ORM edit was made. What was read:

- `#### Glossary terms` — **3** rows, matching the CSV one-for-one:
  `DjangoOptimizerExtension` (shipped `0.0.2`), `DjangoType` (shipped `0.0.5`),
  `only()` projection (shipped `0.0.2`).
- `#### Package files` — **12** paths, and **all 12 exist on disk** (checked individually with
  `[ -f ]`; `MISSING=0`). No `(historical)` marker appears on this card, so the
  `TrackedPath.is_current = False` case does not arise here.
- `#### Scope` — **7** bullets: generated relation resolvers, selection-tree walker, root-gated
  optimizer extension, nested `Prefetch` chains, same-query `select_related` recursion, `only()`
  projection, custom `get_queryset` downgrade to `Prefetch`. That is O1-O6 with O4 split across two
  bullets. Accurate at HEAD.
- `#### Files likely touched` (6 entries), `#### Verified in upstream` (the strawberry-django
  `optimizer.py::DjangoOptimizerExtension` parity note), and `#### Note` (2 bullets) — all read; all
  still accurate.
- `KANBAN.md:145` — the spec index row, `| `DONE-002-0.0.2` - Optimizer O1-O6 foundation |
  [spec-002-optimizer-0_0_2.md](docs/SPECS/spec-002-optimizer-0_0_2.md) |`. Path resolves.
- `KANBAN.md:2560` — *"our O3 root gate (`info.path.prev is None`, spec-002)"*. Still at `:2560`
  after the regenerate, and still accurate: `extension.py::DjangoOptimizerExtension.resolve` returns
  early on `info.path.prev is not None`, the same gate stated in the positive.
- `KANBAN.md:4859` — the card's own `Spec:` line, pointing at the archived path. Resolves.

**B5 — the `0.0.2`-versus-`0.0.3` disagreement: RECORDED AND ESCALATED, with ZERO edits.** All four
sites, quoted with line numbers measured at this pass:

| Site | Exact text | Says |
|---|---|---|
| `docs/GLOSSARY.md:714` (under `## `DjangoOptimizerExtension``) | `**Status:** shipped (`0.0.2`).` | `0.0.2` |
| `docs/GLOSSARY.md:1382` (under `## `only()` projection`) | `**Status:** shipped (`0.0.2`).` | `0.0.2` |
| kanban DB, card 2 | `card_id` `DONE-002-0.0.2`, `target_version.number` `0.0.2` (read via the ORM this pass) | `0.0.2` |
| `CHANGELOG.md:292`-`:295` (`## [0.0.2] - 2026-04-30`) | *"**Early** `DjangoOptimizerExtension` Strawberry schema extension for **depth-1** N+1 prevention."* | partial at `0.0.2` |
| `CHANGELOG.md:283`-`:285` (`## [0.0.3] - 2026-05-05`) | *"`DjangoOptimizerExtension` is now effective end-to-end for root `QuerySet` resolvers: selection-tree planning, `select_related`, nested `Prefetch` chains, same-query recursion, `only()` projection, and `get_queryset`-aware `Prefetch` downgrade."* | O4/O5/O6 at `0.0.3` |

**Both readings, stated.** *Reading one:* the glossary is wrong — the surface it describes (nested
chains, `only()`, downgrade) is the surface `CHANGELOG.md` dates to `0.0.3`, so `**Status:** shipped
(`0.0.3`)` would be the truthful line. *Reading two:* the glossary is right — the extension and its
walker existed and shipped at `0.0.2` (the changelog's own words are "early … depth-1"), and a
`**Status:** shipped (X)` line dates when a capability **first** shipped, not when it became
complete; on that reading `0.0.2` is correct and the changelog is simply narrating two releases of
one subsystem.

**No edit was made on either side, and none may be made here.** `CHANGELOG.md` is closed by
`AGENTS.md` rule 21. The glossary side is out of R3's scope per the plan's F2 ruling, and
independently it is not unilaterally correctable: `GlossaryTerm.body`, the card's `target_version`,
the card id `DONE-002-0.0.2`, and the spec filename `…-0_0_2.md` must agree, so flipping only the
glossary entry would *create* a disagreement. Routed to the maintainer as **one** item covering all
four sites — see `### Notes for Worker 1 (spec reconciliation)`.

#### C — the three-direction cross-reference sweep

**C1 — inbound.** Re-derived by grep; the build plan's `### Every reference TO spec-002` table was
treated as a verification list and **two of its line numbers had indeed moved**. Occurrences of the
shortest distinctive token `spec-002` counted per file with
`grep -rlo | while read f; do grep -o … | wc -l; done` (never `grep -rn`, which dumps `KANBAN.html`'s
single enormous data line):

| File | Occurrences |
|---|---|
| `docs/builder/bld-001-r2-spec_reconciliation.md` | 97 |
| `docs/builder/bld-001-r3-doc_completion_archive.md` | 88 |
| `docs/builder/bld-002-r2-spec_reconciliation.md` | 76 |
| `docs/builder/bld-002-r1-rationale_move.md` | 66 |
| `docs/builder/bld-002-r3-doc_completion_archive.md` | 56 (this artifact, pre-report) |
| `docs/builder/build-002-optimizer-0_0_2.md` | 38 |
| `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` | 32 |
| `docs/builder/bld-001-r1-rationale_move.md` | 29 |
| `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` | 23 |
| `docs/builder/bld-001-final.md` | 20 |
| `KANBAN.md` | **9** (lines 145, 310, 2560, 4859) |
| `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` | 8 |
| `KANBAN.html` | **8** |
| `docs/SPECS/spec-005-django_type_contract-0_0_3.md` | 5 |
| `docs/SPECS/spec-002-optimizer-0_0_2.md` (self) | 5 |
| `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | 4 |
| `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` | 4 |
| `docs/SPECS/spec-001-django_types-0_0_1.md` | 4 |
| `docs/builder/build-001-django_types-0_0_1.md` | 3 |
| `docs/SPECS/spec-006-public_surface-0_0_3.md` | 3 |
| `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` | 1 |

**The confirmed zeros, reported because an unstated absence reads as an unrun check.** `spec-002`
occurs **0** times in each of: `README.md`, `GOAL.md`, `TODAY.md`, `AGENTS.md`, `START.md`,
`BACKLOG.md`, `CHANGELOG.md`, `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`.

**No pre-archive `docs/spec-002…` path survives anywhere.** `grep -rn 'docs/spec-002'` returns 2
lines, **both** in this artifact's own plan prose (`:419` and `:666`) describing this very check.
Real surviving pre-archive paths: **zero**. (Same class as the plan's own counter-reading: an
artifact's description of a search is not a counterexample to it.)

Two plan numbers moved, both attributed: `KANBAN.md` 7 -> 9 and `KANBAN.html` 6 -> 8, `+2` each,
entirely from this pass's own bullet replacement (decomposed under `#### A` above). No sibling spec's
count changed.

**C2 — outbound.** A scratch checker resolved every link definition from **its own file's**
directory, with the fragment stripped, and resolved every in-page fragment against a surviving
heading in the *target* file:

| File | defs | uses | undefined | orphaned | broken on disk | inline cross-file links | duplicate defs | fragment targets |
|---|---|---|---|---|---|---|---|---|
| `docs/SPECS/spec-002-optimizer-0_0_2.md` | 4 | **4** | 0 | 0 | 0 | 0 | 0 | 3 / 3 resolve |
| `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` | 19 | **19** | 0 | 0 | 0 | 0 | 0 | 8 / 8 resolve |

The rationale's 8 fragment targets are the **7** `../spec-002-optimizer-0_0_2.md#<frag>` definitions
(`#architecture-decision`, `#coordination-with-spec-001-django_types-0_0_1md`, `#problem-statement`,
`#purpose`, `#references`, `#shipped-slices`, `#visibility-status`) plus `../../GLOSSARY.md
#djangooptimizerextension`. All eight resolve against a real heading. The spec's 3 are its three
`../GLOSSARY.md#…` glossary anchors; all three resolve.

**C3 — internal.** The spec<->rationale pair is self-consistent:

- **Every one of the rationale's 8 entries** under `## Entries keyed to the spec` opens with a
  `Spec:` line naming the spec decision **by heading text and by reference-style anchor** — verified
  mechanically by pairing each `### ` heading with the `Spec:` line that follows it (lines 98, 138,
  162, 195, 258, 310, 334, 368). Not one entry is unkeyed.
- **The three entries keyed to removed headings say so in their own lead**, and their link
  definitions point at **surviving** headings: `## O4 extraction` -> *"The `## O4 extraction` heading
  no longer exists"*, keyed to `[Purpose][spec-002-purpose]`; `## Open questions` -> *"The `## Open
  questions` heading no longer exists"*, keyed to `[Shipped slices][spec-002-shipped]`;
  `## Current state` -> *"The `## Current state` heading no longer exists"*, keyed to
  `[Shipped slices][spec-002-shipped]` **and** `[Visibility status][spec-002-visibility]`.
- **The spec's three pointer sentences resolve** — `:8`, `:18`, and `:27` all use
  `[rationale file][spec-002-rationale]`, defined at `:89` as
  `appx/spec-002-optimizer-0_0_2-rationale.md`, which exists (C2's `broken_on_disk=0` covers it).
- **Both companions sit at `docs/SPECS/appx/`** — `spec-002-optimizer-0_0_2-rationale.md` (33,620
  bytes) and `spec-002-optimizer-0_0_2-terms.csv` (323 bytes) — and **nothing spec-002-related is
  stranded at the `docs/` root** (`ls docs/ | grep -i spec-002` is empty). The spec's own companion
  reference carries the `appx/` prefix, per `AGENTS.md` rule 26.

**C4 — read-only sibling staleness: RECORDED, NOT EDITED.** All four `spec-003` sites re-measured at
their plan-time line numbers, and all four still stale:

| Site | Text | Why stale |
|---|---|---|
| `spec-003…:4` | *"O1, O2, O3, O5, and O6 have shipped … The remaining O-slice is O4"* | O4 shipped; correct as a record of spec-003's authoring moment, wrong read as present tense at HEAD |
| `spec-003…:27` | `plan_optimizations(selected_fields, model, info=None)` and `_collect_scalar_only_fields` | the pre-D4 arity (HEAD adds keyword-only `runtime_prefixes` / `source_type`); `_collect_scalar_only_fields` measured **0** occurrences in `django_strawberry_framework/` |
| `spec-003…:333` | *"Update `docs/SPECS/spec-002-optimizer-0_0_2.md` current state, visibility status, and checklist to mark O4 shipped."* | a discharged when-O4-ships instruction naming `## Current state`, a section that no longer exists |
| `spec-003…:335` | *"Also update the older parent-spec O4 references in `docs/SPECS/spec-002-optimizer-0_0_2.md`."* | same discharged `## Documentation updates when O4 ships` block; R2's hand-off named only `:333` |

**Live and correct, so a later sweep must NOT "fix" them:** `spec-006-public_surface-0_0_3.md:136`
names the section by quoted title — *"amended into `spec-002-optimizer-0_0_2.md` "Visibility status""*
— and `:147` names it by description — *"carries the local visibility-status amendment that this spec
governs"*. `## Visibility status` survives in the spec precisely because of these two.

**What is deliberately NOT in this escalation**, so it is not over-scoped: the `spec-002` survivals
in `CHANGELOG.md` prose and in `KANBAN.md`'s historical card text are **correct as history** and are
not staleness. (`CHANGELOG.md` in fact contains **0** `spec-002` references at all — measured above.)

#### D — chain, anchors, and the staged-anchor sweep

**D1 — the `SpecDoc` / card / glossary-link chain**, read from the DB (never from a document), all
read-only:

- `Card.objects.get(number=2)` -> `DONE-002-0.0.2` / `done` / `0.0.2` / *"Optimizer O1-O6
  foundation"*.
- `SpecDoc` for card 2 -> name `spec-002-optimizer-0_0_2`, `path`
  `docs/SPECS/spec-002-optimizer-0_0_2.md`, and `pathlib.Path(sd.path).exists()` is `True`. `sd.url`
  was **read** (it renders the GitHub blob URL from `path`) and never assigned — it is a read-only
  `@property`.
- `card.glossary_links.count()` -> **3**, `raw_text` values `DjangoOptimizerExtension` ->
  `djangooptimizerextension`, `DjangoType` -> `djangotype`, `only()` -> `only-projection`. One per
  CSV row, in the same order.

**D2 — both constraint commands, quoted, both exit 0** (also in `### Validation run`). The terms CSV
is **3 data rows / 3 distinct anchors** — one row per anchor, which `import_spec_terms` requires and
`check_spec_glossary` merely tolerates. 323 bytes, unchanged.

**D3 — the terms-CSV completeness question: DECIDED, RECORDED, NO ROW ADDED.** Re-derived from
scratch by matching every `## ` heading in `docs/GLOSSARY.md` (**147** headings) against the spec
**body** (link-definition block excluded), then subtracting the three anchors the spec links. The
unlinked-but-glossary-backed set is **four**:

| Term | Glossary anchor | Spec line |
|---|---|---|
| `DjangoConnectionField` | `#djangoconnectionfield` | 25 |
| `finalize_django_types` | `#finalize_django_types` | 31 |
| FK-id elision | `#fk-id-elision` | 33 |
| Visibility boundary | `#visibility-boundary` | 48 |

Two measurement notes, because both are the kind of thing that silently changes a count. `##
DjangoConnection` also matches, at the same line 25 — it is a **substring artifact** of
`DjangoConnectionField`, not a fifth term. And `Visibility boundary` is invisible to a case-sensitive
scan: the spec spells it lowercase in prose (*"the package's shared visibility boundary"* at `:48`)
while the glossary heading is `## Visibility boundary` at `:2040`. A case-sensitive first pass
returned **three**; the case-insensitive re-derivation returns **four**, matching the plan.

**R2's hand-off premise is confirmed wrong, not merely miscounted.** `Plan cache` and
`Meta.optimizer_hints` occur **0** times each in the spec body (case-insensitive, both spellings
probed). Two of the three terms R2 named as unlinked do not appear in the spec at all.

**The set stands at three, deliberately.** No CSV row was added and the CSV was not edited — nothing
needs one to pass, since `check_spec_glossary.py` exits 0 at 3 and does not require exhaustiveness;
adding a row would retroactively change a DONE card's shipped board record twelve releases after it
closed; and it would additionally require a link in the spec **body**, which is Worker 1's file, not
Worker 2's.

**D4 — staged-anchor sweep.** `grep -rEn 'TODO\(spec-002|TODO-(ALPHA|BETA|STABLE)-002' .`, excluding
`KANBAN.md`, `KANBAN.html`, and `BACKLOG.md` where `TODO-<MILESTONE>-<NNN>` legitimately names an
unshipped board card. **Occurrences counted, not matching lines:**

| File | Occurrences | Classification |
|---|---|---|
| `docs/builder/build-002-optimizer-0_0_2.md:222` | **2** | the build plan's own R3 checklist line, which names both patterns in one sentence — per-cycle artifact, not shipped source |
| `docs/builder/bld-002-r3-doc_completion_archive.md:389` | **1** | this artifact's plan prose describing the sweep — per-cycle artifact |

**3 occurrences / 2 lines / 2 files** when the sweep ran, up from the plan's 2 for exactly the reason
the plan predicted: a per-cycle `docs/builder/` artifact that describes the sweep contains the
pattern. Re-measured **after** this build report landed, it reads **4 occurrences / 3 lines / 2
files** — the extra one is the `grep -rEn 'TODO\(spec-002|…'` command quoted two paragraphs above.
Measured rather than left as a prediction, since the paragraph that would have predicted it is the
paragraph that causes it.

**The load-bearing number is the other one: `grep -rEn … django_strawberry_framework/ tests/
examples/` returns 0.** No anchor in package source, in any of the three test trees, or in the
example project. Nothing here is `revision-needed`.

### Notes for Worker 3

- **The completeness question is the sharp one, per the plan, so here is what to re-run.** Every
  absence above carries its command. The three worth re-deriving independently are C1 (the inbound
  census — use the per-file `grep -o | wc -l` form, not `grep -rn`, or `KANBAN.html`'s single data
  line will flood the output), B1 (the five `docs/README.md` claims against the five symbols), and B4
  (the 12 package-file paths).
- **Re-derive the replacement text yourself; do not accept 1268 / `041f0354…` from this report.**
  `docs/builder/temp-tests/r3-spec002/build_replacement.py` reconstructs it from R2's blockquote
  independently of this artifact's fenced block and asserts the two are equal — run it, or
  reconstruct by hand (strip `> ` from the 15 blockquote lines at
  `bld-002-r2-spec_reconciliation.md:765`-`:779`, join with single spaces) and compare against
  `CardItem.objects.get(pk=1260).text`.
- **Attribution runs both ways.** The `KANBAN.md` / `KANBAN.html` / `db.sqlite3` diff is mixed and
  mostly the concurrent session's; it is not R3's to explain. But card 052's `CardItem` is **not**
  something the concurrent session is writing, so a *missing* correction there could not be excused
  as concurrent territory. The bullet is at `KANBAN.md:310`.
- **The acceptance evidence is the two-regenerate hash table plus the spot-checks, never a clean
  `git diff`.** This report offers no clean diff as proof anywhere; if you find one, it is a defect.
- **F2 and F3 stayed escalations.** No `GlossaryTerm.body` row, no `CHANGELOG.md` line, and no
  terms-CSV row was touched. `git status --porcelain` at close contains no `CHANGELOG.md` and no
  `docs/SPECS/appx/…-terms.csv`.
- **Four plan baseline numbers moved; all four are attributed above and none is a contract change:**
  `KANBAN.md` `spec-002` occurrences 7 -> 9 and `KANBAN.html` 6 -> 8 (this pass's own bullet, `+2`
  each); the staged-anchor count 2 -> 3 (this artifact); the card-052 block's render position
  (`:4850` -> `:4852`). `import_spec_terms --check` still reports 49 done cards — the number did
  **not** move this time, but exit 0 is the contract either way.
- **Scratch lives at `docs/builder/temp-tests/r3-spec002/`** (gitignored): `inspect_card52.py`,
  `apply_card52.py`, `build_replacement.py` (+ its generated `replacement.txt`), `verify_chain.py`,
  `csv_completeness.py`, `linkcheck.py`. `r3-spec001` from the prior cycle was not reused, read, or
  deleted.
- **A third slugger-family defect is documented in `### Implementation notes`** (deleting code spans
  before matching reference links produces false orphans). It bit this pass's first checker run and
  is worth knowing before you write your own.

### Notes for Worker 1 (spec reconciliation)

**No spec or rationale edit is owed by this pass, so the plan's interstitial-pass condition did NOT
trigger.** Every audit leg either came back clean or produced a finding whose owner is outside this
cycle. `docs/SPECS/spec-002-optimizer-0_0_2.md` and
`docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` were read but not written; both are byte-
unchanged by R3. Worker 0 need not dispatch an interstitial Worker 1 pass between `built` and the
review.

Updating R2's consolidated hand-off keys, per the plan's numbering:

1. **Item 1 (`KANBAN.md:310`) — EXECUTED AND CLOSED.** The `CardItem` on card
   `TODO-ALPHA-052-0.1.0` now carries the corrected 1268-character text, `sha256`
   `041f0354993a32ad8b687dae00636544f761ad8edab7f2534c545a50f4971040`, and the render carries it at
   `KANBAN.md:310`. At final verification, re-read the stored column rather than the rendered line —
   the render is derived, and only the column is the source of truth.
2. **Item 10 (`0.0.2` versus `0.0.3`) — ESCALATED, ZERO EDITS, ONE MAINTAINER ITEM.** For the final
   gate's `### Deferred work catalog`. All four sites are quoted with line numbers under `#### B` /
   B5 above, with both readings written out. **Recommended catalog wording:** *"`docs/GLOSSARY.md`
   dates `DjangoOptimizerExtension` (`:714`) and `only()` projection (`:1382`) to `0.0.2`, matching
   card `DONE-002-0.0.2`'s `target_version`; `CHANGELOG.md` `[0.0.2]` calls the extension 'early …
   depth-1' and `[0.0.3]` dates the end-to-end surface — nested chains, `only()`, downgrade — to
   `0.0.3`. Deciding which release a `**Status:** shipped (X)` line should name for a subsystem that
   shipped across two is an editorial call about the glossary's dating convention, and it cannot be
   settled without `CHANGELOG.md`, which `AGENTS.md` rule 21 closes. Maintainer decision; if `0.0.3`
   wins, the card id, the card's `target_version`, and the spec filename `…-0_0_2.md` all move with
   it."*
3. **Item 11 (terms-CSV completeness) — DECIDED AND CLOSED.** The set stands at **three**. The
   corrected measurement is in `#### D` / D3: the unlinked-but-glossary-backed set is **four**
   (`DjangoConnectionField` `:25`, `finalize_django_types` `:31`, FK-id elision `:33`, Visibility
   boundary `:48`), `DjangoConnection` is a substring artifact of the first, and **R2's premise was
   wrong as well as its count** — `Plan cache` and `Meta.optimizer_hints` occur **0** times in the
   spec body. Worth carrying into the record, because a corrected number behind a false premise still
   misleads.
4. **Item 4's sibling staleness — SCOPE CORRECTED AND CONFIRMED AT FOUR SITES.**
   `spec-003-optimizer_nested_prefetch_chains-0_0_2.md` at `:4`, `:27`, `:333`, `:335`, all quoted
   under C4. All read-only this cycle; owner is the maintainer or whoever next opens `spec-003`.
   `spec-006-public_surface-0_0_3.md:136` / `:147` are **live and correct** and must not be swept up
   with them. **Recommended amendment for whoever opens `spec-003`** — section
   `## Documentation updates when O4 ships`, current wording *"Update
   `docs/SPECS/spec-002-optimizer-0_0_2.md` current state, visibility status, and checklist to mark
   O4 shipped"*, recommended replacement: *"O4 is shipped and recorded in
   `docs/SPECS/spec-002-optimizer-0_0_2.md` `## Shipped slices` and `## Implementation checklist`;
   that spec no longer carries a `## Current state` section."* And section `## Purpose`, current
   wording *"O1, O2, O3, O5, and O6 have shipped … The remaining O-slice is O4"*, recommended
   replacement: *"O1 through O6 have all shipped; this spec records the O4 design and implementation
   history."*
5. **Item 8 (a spec/rationale consistency checker in `scripts/`) — STILL OPEN, still unowned,
   carried to the final gate's `### Deferred work catalog`.** R3 did not open it. It now has a
   **third** measured argument: alongside `check_spec_glossary.py::github_anchor`'s two known traps
   (a reference-style heading slugged without rendering the markup first; whitespace runs collapsed
   where GitHub replaces spaces one at a time), a third defect in the same family bit this pass —
   **deleting** code spans before matching reference links turns ``[`only()`][ref]`` into `[][ref]`
   and produces false orphans. Three passes in the sibling cycle copied the first two; this pass
   reproduced the third from scratch. A shared checker is the only thing that stops the fourth.
6. **Item 9 (the `_optimizer_field_map` rename-sweep residue) — UNCHANGED, maintainer-owned.**
   `tests/optimizer/test_field_meta.py` and `scripts/review_inspect.py` are outside every residual
   item's write set. Not re-opened. Corroborating measurement from this pass: `_collect_scalar_only_fields`
   is likewise **absent** from `django_strawberry_framework/` (0 occurrences) while
   `spec-003…:27` still names it — the same shape of residue, in a read-only sibling.
7. **`docs/GLOSSARY.md` was CLEAN at this pass's open and is CLEAN at its close**, byte-identical
   across the pre-edit reading and both regenerates
   (`563206856eabd961f2ded7035c1a6b275a9b2a74694e5051ad5aa361b03a3cbe`). If it is dirty at final
   verification, that is a change made after this pass and must be attributed positively before
   anything is concluded from it.
8. **New, and small: two `TODO(spec-035)` anchors live in `optimizer/walker.py`** at `:464` and
   `:1131`. They are outside R3's `TODO(spec-002` sweep and outside every residual item's write set,
   and they are body comments rather than docstrings so they do not reach `docs/TREE.md`. Recorded
   only so a future spec-035 closeout can find them without a fresh sweep; **no action is
   recommended in this cycle.**

---

## Review (Worker 3)

Every number below was re-derived at this pass with the command beside it. Where the build report
already carried a number, it was re-measured and the two are compared; nothing is accepted on prose
(`BUILD.md` `## Claims are proven mechanically, never accepted on prose`). Read-only HEAD references
were obtained with `git show HEAD:<path>` into a scratch path **outside** the repository; no
`git stash` / `checkout` / `restore` / `worktree` was run on anything.

### The load-bearing verification: the one mutation

**Re-derived independently, not accepted.** The replacement string was reconstructed from R2's
blockquote by this pass's own script (`docs/builder/temp-tests/r3-spec002-w3/verify_db.py`): strip
the leading `> ` from each of the **15** blockquote lines at
`bld-002-r2-spec_reconciliation.md:765`-`:779`, join with single spaces. That reconstruction is
**1268** characters, `sha256` `041f0354993a32ad8b687dae00636544f761ad8edab7f2534c545a50f4971040`,
`str.isascii()` `True`, and it compares **equal** to the fenced ```` ```text ```` block in this
artifact's `### The replacement `CardItem.text`, verbatim`. The value **read back out of the
database** (`CardItem` pk 1260) is byte-equal to that reconstruction. Three independent sources
agree.

**The mutation is exactly one row, proved against HEAD rather than asserted.** `git show
HEAD:examples/fakeshop/db.sqlite3` into scratch, then a table-by-table content comparison of the
whole database:

| Table | Rows only at HEAD | Rows only now |
|---|---|---|
| `kanban_carditem` | 1 | 5 |
| `kanban_uuidmodel` | 0 | 4 |
| `sqlite_sequence` | 1 | 1 (the autoincrement counter) |

**Every other table in the database is content-identical.** The one `kanban_carditem` row that
changed is pk **1260**: at HEAD it is **606** characters, `sha256`
`ddf5ea0b9ac148cb93df8c841cb85ba5ceb413872eb3c9245865e4c99fddea77` — exactly the old value the build
report recorded — and now it is the 1268-character replacement. The four added rows are pks 1265,
1266, 1267 (card 52) and **1268 (card 21)**; all four carry `created_date` 2026-08-07T04:13:51 and
none is R3's. The build report named the first three because its census was card-52-scoped; 1268 sits
on another card and is correctly absent. `kanban_uuidmodel` grew by exactly 4, one per new item.

**A1's "exactly one match" is true at HEAD, not just now.** `select id from kanban_carditem where
text like '%status-shaped sections%'` against the HEAD database returns exactly one row, pk 1260,
`order` 8, length 606 — **tree-wide**, not merely on card 52. The substring was a safe locator.

**The `UUIDModel` side-row is intact.** `CardItem.objects.get(pk=1260).uuid.id` resolves to
`c154d22a-182d-4049-8a0d-7033aba57e41`. Stronger: a sweep over **every** `CardItem` in the database
finds **zero** rows missing a side-row, so the `.save()` path preserved the one-hot registry
invariant everywhere, not only on the edited row.

**Siblings undisturbed.** All 36 items on card 52 were hashed. `Scope` `order` 7 (pk 1259) is
`4b9ca4703c9618a189d5ada4da5b6269bd696cbb3de79d3fb242a6ee98e4936a`, matching the build report's
before-and-after value; it does not appear in the HEAD-versus-now changed set at all, which is a
stronger statement than a matching hash. Card 52 carries 36 items across 6 sections with 8 in
`Scope` at `order` 1, 4, 5, 6, 7, 8, 9, 10 — as recorded.

**Is the replacement TRUE?** Every factual claim in it was verified independently:

| Claim | Verification | Verdict |
|---|---|---|
| `## Open questions` and `## Current state` are gone | `grep -nic 'current state\|open questions' docs/SPECS/spec-002-optimizer-0_0_2.md` -> **0**; `grep -n '^## '` returns Purpose, Problem statement, Architecture decision, Shipped slices, Coordination…, Visibility status, References, Implementation checklist | true |
| `## Shipped slices` and `## Implementation checklist` survive | present at `:29` and `:71` | true |
| `spec-006…` names "Visibility status" **twice** | `:136` *"amended into `spec-002-optimizer-0_0_2.md` "Visibility status""* (quoted title) and `:147` *"carries the local visibility-status amendment"* (description); `grep -nic` -> **2** | true, two sites, two spellings |
| the rationale is the only file citing spec-002 by `#anchor` | `grep -rn 'spec-002-optimizer-0_0_2.md#'` -> 7 in `docs/SPECS/appx/…-rationale.md`, and hits only in per-cycle `docs/builder/` artifacts otherwise (1 / 7 / 6), each of which is prose *describing* the grep | true among durable files |
| one of its defs targets `#visibility-status` | `…-rationale.md:464` `[spec-002-visibility]: ../spec-002-optimizer-0_0_2.md#visibility-status` | true |
| `spec-003`'s instruction is now stale in wording | `:333` *"Update … current state, visibility status, and checklist to mark O4 shipped."* — names a section that no longer exists | true |

**The one clause that needed a derivation rather than a grep, recorded so a later pass cannot "fix"
it into a falsehood.** "carries one status-shaped section left" is *not* a claim that only one
section with a status-shaped title exists — `## Shipped slices` and `## Implementation checklist`
plainly do, and the very next clause names both. The category is the rationale's, at
`…-rationale.md:293`: *"the argument the deferral makes is against a section named for **now**, and
after this pass the spec has exactly one such heading left."* `## Shipped slices` is a past-tense
fact and `## Implementation checklist` a closed record; neither is named for the present. The
sentence is true as written under the taxonomy its own second clause establishes, and it is faithful
to the rationale it is checked against. **Do not rewrite it to "one standing-promise section".**

The prior text's sin is not repeated. The old bullet asserted *"Nothing anywhere cites spec-002 by
`#anchor`"* — falsified by the rationale def added in the same cycle. The replacement asserts the
opposite and names the mechanism without a count, so the next entry the companion gains cannot
falsify it.

### Regeneration hygiene

**A third regenerate, run by this pass, is byte-identical to Worker 2's second.** Both `--check`
(non-mutating) and a full re-render into scratch were used:

```
uv run python scripts/build_kanban_md.py --check     -> "KANBAN.md is up to date."         exit 0
uv run python scripts/build_kanban_html.py --check   -> "KANBAN.html is up to date."       exit 0
uv run python scripts/build_glossary_md.py --check   -> "docs/GLOSSARY.md is up to date."  exit 0
```

then, into a scratch path outside the repository (`--md` / `--html`), a third full render:

```
bf4de38b2930784970df631a1b506a78ba91b510dac8108e93735bd9fd5abd58  KANBAN.md
fd45a0f5b363a6179913a6e4d61fd53384d63aa7cc55a8b5803dd96556b2c577  KANBAN.html
563206856eabd961f2ded7035c1a6b275a9b2a74694e5051ad5aa361b03a3cbe  docs/GLOSSARY.md
```

`cmp` against the in-tree files: **identical for all three**, and all three digests match the build
report's regenerate-1 / regenerate-2 column exactly. The `--check` exit 0 is the stronger of the two
results: it is precisely the assertion that **nothing was hand-edited** into the rendered files —
every byte on disk is what the DB renders.

**The `KANBAN.md` diff against HEAD is 6 lines and every one is accounted for.** One replaced line
(`:310`, R3's bullet) plus five added lines that are the concurrent session's four new `CardItem`s
(three of them wrapping onto the `Scope` block). No hand-edit anywhere in the file.

**`docs/GLOSSARY.md` is genuinely clean.** Absent from `git status --porcelain`, and `cmp` against
`git show HEAD:docs/GLOSSARY.md` (scratch, outside the repo) is byte-identical. Not merely
unreported — unchanged.

`uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have
glossary links.`, **exit 0**. `check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md`
-> `OK: 3 terms - all have glossary entries and at least one spec link.`, **exit 0**.
`build_tree_md.py --check` -> `docs/TREE.md is up to date.`, **exit 0**.

### The 18-box checklist

18 `- [x]`, 0 `- [ ]` (`grep -c` on the artifact). Every box was walked and tested against evidence
rather than against the plan's claim. **No box rests on a plan claim; every one has a command whose
result this pass reproduced.**

| Box | Independent evidence found | Verdict |
|---|---|---|
| A1 | HEAD-DB query: exactly one row tree-wide matched the locator substring, pk 1260 / `order` 8 / 606 chars | landed |
| A2 | three-source byte-identity above; `.save()` proved by the intact side-row and by the fact that a raw-SQL path would have left the row's registry entry unchanged while the ORM path did not need one | landed |
| A3 | `--check` exit 0 on all three generators; third render byte-identical | landed |
| A4 | third-regenerate hashes match; sibling `order` 7 absent from the HEAD-vs-now changed set; `KANBAN.md:309` still the consistency-checker bullet, `:310` the new one | landed |
| A5 | `import_spec_terms --check` exit 0 re-run here; `docs/GLOSSARY.md` proved byte-identical to HEAD | landed |
| B1 | all five passages re-derived against source (table below) | landed |
| B2 | `build_tree_md.py --check` exit 0; `TODO(spec-035)` at `walker.py:464` / `:1131` confirmed to be indented body comments, not docstrings | landed |
| B3 | `docs/GLOSSARY.md:712` / `:761` / `:1380` headings confirmed; entries read | landed |
| B4 | all **12** package paths exist (`[ -f ]` each, 0 missing); `KANBAN.md:145` path resolves; `:2560` does carry *"our O3 root gate (`info.path.prev is None`, spec-002)"* on a long line; card renders at `:4852` | landed |
| B5 | all four sites re-read: `docs/GLOSSARY.md:714` and `:1382` both `**Status:** shipped (`0.0.2`).`; `CHANGELOG.md:285` end-to-end at `[0.0.3]`, `:295` "Early … depth-1" at `[0.0.2]`; **zero** edits in `git status` | landed |
| C1 | full census re-run; every per-file count reproduced (table below); ten zeros reproduced | landed |
| C2 | own checker: spec 4 defs / 4 uses, rationale 19 / 19, 0 undefined, 0 orphaned, 0 duplicate defs, 0 broken paths, 0 inline cross-file links, 3 + 8 fragments all resolving | landed |
| C3 | 8 `###` entries each with a `Spec:` line at `:98`, `:138`, `:162`, `:195`, `:258`, `:310`, `:334`, `:368` — the exact lines recorded; the three removed-heading entries confirmed | landed |
| C4 | `spec-003…` `:4`, `:27`, `:333`, `:335` all re-read and all still stale; `_collect_scalar_only_fields` **0** occurrences in `django_strawberry_framework/`; both files unmodified in `git status` | landed |
| D1 | ORM read: card 2 `DONE-002-0.0.2` / done / `0.0.2`; `SpecDoc.path` resolves on disk; `glossary_links.count()` 3 matching the CSV | landed |
| D2 | both commands re-run, both exit 0; CSV re-read: 3 data rows, 3 distinct anchors, 323 bytes, unmodified | landed |
| D3 | set re-derived from scratch (147 `## ` glossary headings vs the spec body): **four** unlinked-but-glossary-backed terms at spec `:25` / `:31` / `:33` / `:48`, `DjangoConnection` confirmed a substring artifact at the same line 25, and `plan cache` / `optimizer_hints` **0** occurrences | landed |
| D4 | sweep re-run: **4 occurrences / 3 lines / 2 files**, all in per-cycle `docs/builder/` artifacts; `django_strawberry_framework/ tests/ examples/` -> **0** | landed |

The dispatch brief's "16 boxes" versus the artifact's 18 is a Worker 0 miscount already acknowledged;
Worker 2 followed the enumeration and flagged it. Not raised as a finding.

### The `+2` arithmetic

`grep -o 'spec-002' | wc -l`: `KANBAN.md` **9**, `KANBAN.html` **8** now; against `git show
HEAD:KANBAN.md` / `HEAD:KANBAN.html` in scratch, **7** and **6**. Both deltas are `+2`. Decomposed at
the source rather than at the render: the HEAD `CardItem.text` contains `spec-002` **2** times, the
replacement **4** times. `+2` exactly, once per rendered surface, and the `KANBAN.md` occurrences sit
on lines 145, 310, 2560, 4859 — the same four lines as at HEAD. **No third surface moved.**

### The audit sweeps' own correctness

**B1 — `docs/README.md`, all five passages re-derived against the named symbols.** Every one holds;
zero falsified, so zero edits was the correct outcome.

| Passage | Re-derived against | Verdict |
|---|---|---|
| `:53` instance-bound Plan cache | `optimizer/extension.py` #"self._plan_cache" — an **instance** attribute assigned in `__init__`, so a per-request instance would lose it; the doc's own example wraps it as `lambda: _optimizer` | holds |
| `:55` `select_related` / `prefetch_related` / `only` | `optimizer/plans.py::OptimizationPlan.apply` applies exactly those three, in the order `only()` -> `select_related()` -> `prefetch_related()` | holds |
| `:87` returning a `QuerySet` gives the optimizer something to shape | `utils/querysets.py::normalize_query_source` coerces a `Manager` via `_coerced_manager_queryset` and passes everything else through | holds |
| `:88` one walk at the root, one plan | `optimizer/extension.py::DjangoOptimizerExtension.resolve` #"if info.path.prev is not None" — the O3 early return | holds |
| `:105` `get_queryset` cooperates via `Prefetch` downgrade through one shared boundary | `optimizer/walker.py::_target_has_custom_get_queryset`; `utils/querysets.py::apply_type_visibility_sync` / `::apply_type_visibility_async` both present | holds |
| `:106` plan caching, FK-id elision, downgrade, `0.0.14` strategy seam, `0.0.10` G1 + G2 | `_plan_cache` / `_execution_plan_cache`; `plans.py` `fk_id_elisions`; `nested_connection_strategy=` kwarg on `__init__`; `extension.py` #"_result_cache" pass-through; `walker.py` #"operation is OperationType.QUERY" | holds |

**C1 — the inbound census reproduced exactly**, including the zeros. `README.md`, `GOAL.md`,
`TODAY.md`, `AGENTS.md`, `START.md`, `BACKLOG.md`, `CHANGELOG.md`, `docs/README.md`, `docs/TREE.md`,
`docs/GLOSSARY.md` -> **0** each. Durable-file counts: `spec-035` 8, `spec-005` 5, `spec-002` (self)
5, `spec-033` 4, `spec-003` 4, `spec-001` 4, `spec-006` 3, `spec-004` 1, spec-002 rationale 32,
spec-001 rationale 23 — every one matching the build report. No pre-archive `docs/spec-002…` path
survives: the only hits are this artifact's own prose describing the check.

**C2 — the link scaffold re-derived with a checker written from scratch** for this review
(`docs/builder/temp-tests/r3-spec002-w3/linkaudit.py`), masking code-span content to same-length
filler rather than deleting it, and not collapsing whitespace runs. Result identical to the build
report's table: spec 4/4 and rationale 19/19, all four zero columns zero, 3 and 8 fragment targets
all resolving. **A fourth defect in the same slugger family bit this pass's own checker** — see the
DRY finding.

**D4 — the staged-anchor sweep reproduced at 4 / 3 / 2**, all in per-cycle `docs/builder/` artifacts,
and **0** in `django_strawberry_framework/`, `tests/`, `examples/`. Confirmed as recorded.

**Completeness, since the plan named it the sharp question.** The reported absences were treated as
unrun until re-run; every one above was re-run. One additional sweep this pass ran that the checklist
did not require: `grep -rn` across all `.md` outside `docs/builder/` for any surviving claim that
spec-002 carries `## Current state` or `## Open questions`. The only durable hit is `KANBAN.md:310` —
the corrected bullet, stating they are gone — plus the rationale entry that says the heading no
longer exists. **The stale claim survives nowhere.** `README.md`, `GOAL.md`, and `TODAY.md` carry
zero `spec-002` references and zero references to the removed sections, so nothing this cycle
falsified reaches them.

### High:

None.

### Medium:

None.

### Low:

#### Layout gate scoped narrower than the plan's step 18

`### Validation run`'s layout-gate row runs `check_trailing_commas.py --check` against this artifact
only, while the plan's step 18 says "`<the .md files this pass touched>`" and the pass also
regenerated `KANBAN.md`. Re-run here over `KANBAN.md` and `docs/GLOSSARY.md`: **exit 0**, so nothing
turns on it, and the file is generator-owned anyway. Recorded rather than held: the correct scope for
a generated file is arguable, and the result is green either way. No change required.

#### `docs/GLOSSARY.md` listed under `### Files touched` though byte-unchanged

The bullet itself says "byte-unchanged" and "not a modified path in `git status`", both of which this
pass confirmed, so the entry is honest. It is listed because the generator ran against it, not
because it changed. Recorded only so a later reader scanning the bullet list alone does not conclude
the glossary moved. No change required — over-listing is the safe direction for that section.

### DRY findings

- **The spec/rationale link-and-anchor checker is now on its fourth independent hand-roll, and the
  fourth one reproduced a fresh defect from the same family.** Sites: R1's, R2's, this cycle's
  `docs/builder/temp-tests/r3-spec002/linkcheck.py`, and this review's
  `docs/builder/temp-tests/r3-spec002-w3/linkaudit.py`. The build report documents the third family
  defect (deleting code spans before matching reference links turns ``[`only()`][ref]`` into
  `[][ref]`, producing false orphans). **This review's own checker hit a fourth**: stripping `_` as an
  emphasis marker before slugging destroys `django_types`, so
  `#coordination-with-spec-001-django_types-0_0_1md` reported as an unresolved fragment on the first
  run — a **false positive against a correct link definition**, which is the dangerous direction,
  because the "fix" would have been to edit a good link. Four hand-rolls, four different
  implementations, three distinct slugger defects between them
  (`check_spec_glossary.py::github_anchor`'s raw-reference-heading and whitespace-run traps, the
  code-span-deletion trap, the underscore-strip trap). This is the definition of a duplication that
  should be one helper. Escalated below rather than opened here: `scripts/` is outside this cycle's
  write set and promotion is a maintainer call (hand-off item 8).
- **No other duplication introduced.** R3's diff adds no `.py` file, no test, and no `scripts/`
  entry; its one durable text addition deliberately carries no count and does not restate spec prose
  on the board, which is the duplication the plan set out to avoid. Confirmed by reading the stored
  column: it states the constraint and points at the files, and mentions no number.
- **Existence challenge:** none raised. R3 introduces no abstraction, registry, indirection layer, or
  helper — there is nothing whose existence could be challenged.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` produces **no output**: `__all__` and the
re-export list are untouched. There is no source diff at all in this item — `git status --porcelain`
carries no path under `django_strawberry_framework/` and none under any of the three test trees.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md. (Confirmed: `CHANGELOG.md` is absent from
`git status --porcelain`, and `AGENTS.md` rule 21 closes it for this cycle. The B5 escalation quotes
it read-only.)

### Documentation / release sanity

The slice touches KANBAN, generated docs, and the archived-spec surface, so this section is the main
axis. Read end to end and confirmed:

- **Version strings, statuses and card IDs match.** Card 2 is `DONE-002-0.0.2` / `done` /
  `target_version` `0.0.2` in the DB and renders as `DONE-002-0.0.2` at `KANBAN.md:4852`; the spec
  filename carries `0_0_2`; the terms CSV's three anchors match `card.glossary_links` one-for-one.
  The one disagreement — the glossary dating O2/O4/O5/O6 behavior to `0.0.2` where `CHANGELOG.md`
  dates the end-to-end surface to `0.0.3` — is correctly escalated rather than patched, because it is
  not unilaterally correctable: `GlossaryTerm.body`, `target_version`, the card id, and the spec
  filename must move together, and the authoritative record is closed by `AGENTS.md` rule 21.
- **No KANBAN card moved**, and the one changed card body appears exactly once. Card
  `TODO-ALPHA-052-0.1.0` stays in its section; the replaced bullet renders once, at `KANBAN.md:310`,
  and `grep` finds the replacement's distinctive opening in exactly one rendered location. The
  retired text survives nowhere in a durable file (the build plan's `:149` blockquote is a per-cycle
  artifact recording the bullet as it stood at plan time — provenance, not a live claim; leave it).
- **Verbatim text confirmed character-for-character**, and by three independent derivations rather
  than one `diff`: R2's blockquote reconstructed here, this artifact's fenced block, and the stored
  column, all equal at 1268 bytes / `041f0354…`. The fenced block uses three backticks with no inner
  fence, so no fence-nesting hazard arises.
- **Every markdown link introduced or moved points at a file that exists.** The C2 audit resolves
  every definition in both companions from its own file's directory with the fragment stripped: 0
  broken on disk, 0 undefined refs, 0 orphaned defs, 0 duplicate defs, 0 inline cross-file links, and
  all 11 fragment targets resolving against a surviving heading. `KANBAN.md:145` and `:4859` both
  resolve to `docs/SPECS/spec-002-optimizer-0_0_2.md`.
- **Archived-spec handling preserves the record and leaves the live follow-up in the durable doc.**
  The spec sits at `docs/SPECS/`, both companions at `docs/SPECS/appx/`, nothing spec-002-related is
  stranded at the `docs/` root, `SpecDoc.path` reads the archived path and the file exists, and the
  spec's companion reference carries the `appx/` prefix per `AGENTS.md` rule 26. The live follow-up
  constraint — that retiring `## Visibility status` must re-point `spec-006` and the rationale def —
  now lives on `KANBAN.md`, the durable board, which is the correct home for it.
- **Script-rendered docs: the feeding docstrings carry no staging language.** `build_tree_md.py
  --check` exits 0, so no hand-edit sits in the rendered tail. Every `planned` occurrence under
  `optimizer/` is the domain noun (`planned_resolver_keys`, `finalized_planned_resolver_keys`,
  `DST_OPTIMIZER_PLANNED`, "unplanned"), not staging language; zero `Slice N` / `after Slice N` hits.
  The two `TODO(` hits are `TODO(spec-035)` at `optimizer/walker.py:464` and `:1131`, and both are
  **indented body comments inside function bodies**, so neither reaches the docstring render.
- **No obsolete "coming soon" / "planned" / old-version wording** remains in the one file the slice
  deliberately updated: the replacement bullet states the discharged position and the surviving
  constraint, with no deferral language and no version claim.

### What looks solid

- **The mutation is provable end to end, and the proof is stronger than the build report claimed.**
  A whole-database HEAD-versus-now content comparison shows exactly one changed row, and its HEAD
  content is exactly the value the report recorded as "old". That converts "nothing else was written"
  from an assurance into a measurement, and it also independently confirms the locate-by-substring
  discipline: at HEAD the substring matched one row in the entire table.
- **`--check` was available on all three generators and is the sharper instrument than a third
  write.** It asserts directly that the on-disk bytes are what the DB renders, which is exactly the
  "nothing hand-edited" property, without touching the tree. Worth reusing in the next DB-backed
  cycle in place of a third regenerate.
- **The escalations are real, correctly scoped, and correctly declined.** All five re-verified:
  (1) the `0.0.2`/`0.0.3` disagreement is genuine at all four quoted sites and is not unilaterally
  correctable, so recording both readings and handing it up is the only honest move; (2) the
  terms-CSV set is correctly left at three — `check_spec_glossary` passes at 3 and does not require
  exhaustiveness, and adding a row would rewrite a DONE card's shipped record and additionally
  require a spec-body link this item cannot write; (3) `spec-003` is stale at all four sites and is
  read-only; (4) the code-span-deletion slugger trap is real and I reproduced a sibling of it; (5)
  the two `TODO(spec-035)` anchors are correctly left alone — `BUILD.md` `## Cross-slice integration
  pass` step 6 scopes the sweep to anchors naming **this** build's spec or card, these name another
  spec, they are body comments outside the `docs/TREE.md` render, and package source is read-only
  this cycle. "No action recommended" is right; recording them so a spec-035 closeout finds them
  without a fresh sweep is a genuine contribution.
- **The corrected D3 measurement is right on both halves.** Re-derived from scratch: the
  unlinked-but-glossary-backed set is four, `DjangoConnection` is a substring artifact at the same
  spec line, and `Plan cache` / `Meta.optimizer_hints` occur **0** times in the spec body. R2's
  premise, not merely its count, was wrong — and re-forming the claim rather than renumbering it is
  the correct repair.
- **The replacement text's category shift is deliberate and derivable**, not a slip. Recorded above
  under the mutation section with the rationale line that licenses it, specifically so a later pass
  does not "correct" it into something weaker.

### Temp test verification

- `docs/builder/temp-tests/r3-spec002-w3/verify_db.py` — reconstructs the replacement from R2's
  blockquote, compares it against this artifact's fenced block and against the stored column, censuses
  every `CardItem` on card 52 with per-item hashes, and sweeps every `CardItem` in the database for a
  missing `UUIDModel` side-row.
- `docs/builder/temp-tests/r3-spec002-w3/linkaudit.py` — an independent link-scaffold auditor written
  for this review (code-span **masking**, no whitespace-run collapse, underscores preserved).
- **Disposition: kept as scratch, not promoted.** Neither caught a behavior bug — both reproduced the
  build report's results. `linkaudit.py`'s own initial slugger defect is recorded as evidence under
  `### DRY findings` and escalated to hand-off item 8; it is not a defect in the diff under review.
- `docs/builder/temp-tests/r3-spec002/` (Worker 2's) and `r3-spec001/` (the prior cycle's) were
  neither read, reused, nor deleted.
- **Static inspection helper (`scripts/review_inspect.py`): skipped.** `BUILD.md` `### When to run
  the helper during build` triggers on `.py` files; this diff contains none. No shadow file was used
  or generated by this review.

### Notes for Worker 1 (spec reconciliation)

1. **The interstitial-pass condition did NOT trigger, and that is verified rather than accepted.**
   `docs/SPECS/spec-002-optimizer-0_0_2.md` shows in `git status` from R2 only; the rationale is
   untracked from R1/R2. Neither was written by R3 — every heading, link definition, and entry-keying
   line this review re-measured is exactly where the R2 artifact left it. No Worker 1 pass is owed
   between `built` and this review.
2. **Escalated: hand-off item 8 (a spec/rationale consistency checker in `scripts/`) now has a fourth
   hand-roll and a fourth distinct slugger defect.** Resolution paths for the maintainer: (a) promote
   one checker into `scripts/` with the four known traps encoded as tests — reference-style heading
   slugged before rendering, whitespace runs collapsed, code spans deleted rather than masked,
   underscores stripped as emphasis; (b) fix `check_spec_glossary.py::github_anchor` in place and have
   documentation passes call it rather than hand-rolling; (c) leave it, and accept that each cycle
   re-derives a checker with a fresh defect. Note the failure direction: this pass's defect produced a
   **false positive against a correct link**, so the natural next step would have been to "fix" a good
   definition. Already `KANBAN.md:309` as a board card; this is a fifth measured argument, not a new
   item.
3. **Escalations 1-5 in the build report are confirmed as stated and need no correction.** For the
   final gate's `### Deferred work catalog`, the recommended wording under item 2 there is accurate
   against the four sites as re-read here; the `spec-003` recommended replacements under item 4 are
   accurate against `:4` and `:333` as re-read here.
4. **One provenance note, so no later pass "fixes" it:** `docs/builder/build-002-optimizer-0_0_2.md`
   `:149` and this artifact's `:132` still quote the **retired** bullet verbatim. Both are per-cycle
   artifacts recording what the bullet said at plan time. They are correct as provenance and must not
   be updated to the new text.
5. **Failability proofs: none owed, and the empty re-run set is legal.** R3 introduces no boundary,
   guard, gate, or rejection path — one DB text column, three regenerates, and read-only
   measurements. `worker-3.md`'s mandatory re-run floor is computed over boundaries meeting it; there
   are none, so the re-run subset is empty by arithmetic rather than by choice. **Boundaries re-run:
   none. Boundaries accepted on Worker 2's record: none.** Hot-path budget: none declared, none owed.
   Floor verification: none declared, none owed.
6. **No `pytest` was run in this review**, with or without flags, and no `--cov*` flag was used
   anywhere. The diff carries no source and no test, so there is nothing a focused run could confirm
   that the checks above do not.

### Review outcome

`review-accepted`. Zero High, zero Medium, two Low — both recorded with a reason and neither
requiring a change. One DRY finding, escalated to Worker 1 rather than opened, because its target
(`scripts/`) is outside this cycle's write set and promotion is a maintainer call with an existing
board card. Every claim in the build report that this review could re-derive was re-derived, and
every one reproduced.

---

## Final verification (Worker 1)

Every number below was measured at this pass. Where a prior pass recorded one, it was re-measured and
the two compared; nothing is accepted on prose (`BUILD.md` `## Claims are proven mechanically, never
accepted on prose`). The HEAD reference went to a scratch path **outside** the repository; no
`git stash` / `checkout` / `restore` / `worktree` was run on anything, and nothing was reverted.

### Spec status-line re-verification

Re-read at this pass's open: `docs/SPECS/spec-002-optimizer-0_0_2.md:1` is
`# Spec: Optimizer & Reverse-Relation Resolution`, `:2` blank, `:3` `## Purpose`. **There is no
status / target-release / owner / predecessor block**, so this obligation has nothing to falsify and
no edit is owed. Same reading the R3 plan recorded, re-derived rather than inherited.

### Checklist audit — all 18 boxes, audited against evidence I produced

`grep -c` on the artifact: **18** `- [x]`, **0** `- [ ]`. R3's boxes are mostly *verification*
obligations, so the failure mode being hunted is a tick resting on a plan claim rather than on a run.
**Every box was tested by re-running its check here.** None rests on a plan claim; none is
over-ticked; none was un-ticked; nothing is left `- [ ]`, so no deferral reason is owed under
`### Spec changes made (Worker 1 only)`.

| Box | What I ran, independently of the build report and the review | Verdict |
|---|---|---|
| A1 | `CardItem` census on card 52 via the ORM: 36 items across 6 sections, 8 in `Scope` at `order` 1, 4, 5, 6, 7, 8, 9, 10 — exactly as recorded. The locator substring `status-shaped sections` now returns **0** matches, which is the *expected* post-mutation reading: the replacement says "one status-shaped section left" (singular), so the locator is consumed by its own success. pk 1260 is `Scope` / `order` 8 | tick stands |
| A2 | Three-source byte identity re-derived from scratch: I reconstructed the string from `bld-002-r2-spec_reconciliation.md`'s blockquote myself (start line **765**, **15** lines, strip `> `, join with single spaces) -> length **1268**, `sha256` `041f0354993a32ad8b687dae00636544f761ad8edab7f2534c545a50f4971040`, `isascii()` `True`; the stored column at pk 1260 is byte-equal to it. The `UUIDModel` side-row resolves (`c154d22a-182d-4049-8a0d-7033aba57e41`), which is what proves the `.save()` path rather than raw SQL | tick stands |
| A3 | `build_kanban_md.py --check`, `build_kanban_html.py --check`, `build_glossary_md.py --check` -> `is up to date.`, **exit 0** each. This is the stronger assertion than a third write: it says every byte on disk is what the DB renders, i.e. nothing was hand-edited | tick stands |
| A4 | The three `--check` runs above, plus a rendered spot-check: `KANBAN.md:309` still carries the consistency-checker bullet and `:310` carries the new text. Sibling `Scope` `order` 7 (pk 1259) hashes `4b9ca4703c96…`, matching the value recorded before *and* after the write | tick stands |
| A5 | `import_spec_terms --check` -> `OK: 49 done cards have glossary links.`, **exit 0**. `docs/GLOSSARY.md` is absent from `git status --porcelain` **and** `cmp` against `git show HEAD:docs/GLOSSARY.md` (scratch, outside the repo) is byte-identical — clean by measurement, not by omission | tick stands |
| B1 | All five `docs/README.md` passages re-derived against source myself: `:53` `self._plan_cache` is assigned in `__init__` (an **instance** attribute, so the factory claim holds); `:55` `plans.py::OptimizationPlan.apply` applies `only()` -> `select_related()` -> `prefetch_related()`; `:87` `querysets.py::normalize_query_source` + `_coerced_manager_queryset`; `:88` `extension.py:951` `if info.path.prev is not None` — the O3 gate; `:105` `walker.py::_target_has_custom_get_queryset` + `apply_type_visibility_sync` / `_async`; `:106` `_execution_plan_cache`, `fk_id_elisions`, `nested_connection_strategy=`, `_result_cache` pass-through, `operation is OperationType.QUERY`. **Zero falsified, so zero edits was the right outcome** | tick stands |
| B2 | `build_tree_md.py --check` -> `docs/TREE.md is up to date.`, **exit 0**. I read both `TODO(spec-035)` sites in `optimizer/walker.py` (`:464`, `:1131`) in context: both are **indented `#` comments inside function bodies**, not module docstrings, so neither reaches the docstring render; both name spec-035, so neither is in D4's sweep | tick stands |
| B3 | `docs/GLOSSARY.md:712` / `:1380` / `:761` headings confirmed and their entries read; the `DjangoType` entry's `0.0.5` is correct for **its own** card, not a spec-002 claim | tick stands |
| B4 | All **12** `#### Package files` paths `[ -f ]`-checked: **0 missing**. `#### Glossary terms` is 3 rows matching the CSV; `#### Scope` is 7 bullets = O1-O6 with O4 split across two; `KANBAN.md:145`'s spec-index link and the card's own `Spec:` line both point at `docs/SPECS/spec-002-optimizer-0_0_2.md`, which exists; `:2560` still carries *"our O3 root gate (`info.path.prev is None`, spec-002)"* | tick stands |
| B5 | All four sites re-read at this pass: `docs/GLOSSARY.md:714` and `:1382` both `**Status:** shipped (`0.0.2`).`; `CHANGELOG.md:285` (`[0.0.3]`) the end-to-end sentence, `:295` (`[0.0.2]`) *"Early … depth-1"*; card 2's `target_version` `0.0.2` read via the ORM. **Zero edits**: `CHANGELOG.md` and the terms CSV are both absent from `git status` | tick stands |
| C1 | Inbound census re-run per file, counting occurrences of the shortest distinctive token rather than matching lines. All **ten** zeros reproduced (`README.md`, `GOAL.md`, `TODAY.md`, `AGENTS.md`, `START.md`, `BACKLOG.md`, `CHANGELOG.md`, `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`). Durable counts reproduced: `KANBAN.md` **9**, `KANBAN.html` **8**, `spec-035` 8, `spec-006` 3, `spec-003` 4, rationale 32. No pre-archive `docs/spec-002…` path survives outside `docs/builder/` prose describing the check | tick stands |
| C2 | Re-derived with a **fifth, independently written** checker that avoids all four known slugger traps (masks code spans to same-length filler, preserves whitespace runs, preserves `_`, renders reference-link markup out of headings before slugging). Result identical to both prior passes: spec **4 defs / 4 uses**, rationale **19 / 19**, 0 undefined, 0 orphaned, 0 duplicate defs, 0 broken on-disk paths, 0 inline cross-file links, **3 / 3** and **8 / 8** fragments resolving | tick stands |
| C3 | The rationale's **8** entries each carry a `Spec:` line naming the decision by heading text and by reference-style anchor, at `:98`, `:138`, `:162`, `:195`, `:258`, `:310`, `:334`, `:368` — the exact lines recorded. The three entries keyed to removed headings each say so in their own lead and point at surviving headings. A listing of `docs/` filtered for `spec-002` is empty: nothing stranded at the `docs/` root | tick stands |
| C4 | All four `spec-003` sites re-read and all four still stale. Note on the fourth: `:335` is one line whose **trailing clause** is *"Also update the older parent-spec O4 references in `docs/SPECS/spec-002-optimizer-0_0_2.md`."* — the artifact quotes the clause, not the whole line, and the citation is accurate. `_collect_scalar_only_fields`: **0** occurrences in `django_strawberry_framework/`. `spec-006…:136` / `:147` re-read and confirmed **live and correct**. Both siblings are absent from `git status` — read-only was honoured | tick stands |
| D1 | ORM read: card 2 is `DONE-002-0.0.2` / `Done` / `0.0.2` / *"Optimizer O1-O6 foundation"*; its `SpecDoc` reads `path` `docs/SPECS/spec-002-optimizer-0_0_2.md` and `Path(path).exists()` is `True`; `glossary_links.count()` is **3** with `raw_text` `DjangoOptimizerExtension` / `DjangoType` / `only()` | tick stands |
| D2 | Both commands re-run here, both **exit 0** (quoted below). Terms CSV re-read: **323 bytes, 3 data rows, 3 distinct anchors** — one row per anchor, which `import_spec_terms` requires. Byte-untouched | tick stands |
| D3 | Set re-derived from scratch by matching all **147** `## ` `docs/GLOSSARY.md` headings against the spec **body**: the unlinked-but-glossary-backed set is **four** — `DjangoConnectionField` `:25`, `finalize_django_types` `:31`, `FK-id elision` `:33`, `Visibility boundary` `:48`. `DjangoConnection` matches at the same line 25 and is a substring artifact. `plan cache` and `optimizer_hints` occur **0** times in the spec body. My ruling on the set is below | tick stands |
| D4 | Sweep re-run: **4 occurrences / 3 lines / 2 files**, all in per-cycle `docs/builder/` artifacts (`build-002-…:222` carries both patterns; this artifact carries two more). The load-bearing run — `grep -rEn … django_strawberry_framework/ tests/ examples/` — returns **0**. Nothing is `revision-needed` | tick stands |

**Boundary and staged-anchor sweep (`## Final verification job` step 6).** Independently: **0**
anchors of either pattern in package source, in any of the three test trees, or in the example
project. Every survivor is a per-cycle `docs/builder/` artifact describing the sweep. Measured at
this section's close rather than before writing it, because the paragraph that would have predicted
the number is the paragraph that changes it — an earlier draft of this very sentence named both
patterns literally and pushed the tree-wide count to 5. As it now stands the count is **4
occurrences / 3 lines / 2 files**, unchanged from Worker 3's reading: the build plan's `:222`
checklist line carries both patterns, and this artifact carries one in its plan prose and one in
Worker 2's D4 table. The load-bearing number, `0` in the three shipped trees, is unmoved either
way.

### Disposition of Worker 3's findings — each addressed or rejected with a recorded reason

#### Low 1 — the layout gate was scoped narrower than the plan's step 18: ACCEPTED AS CLOSED, no tick disturbed

**No checklist box is at stake.** The 18 boxes are A1-A5 / B1-B5 / C1-C4 / D1-D4, and none of them is
the layout gate — step 18 is a plan *step* with no box, so there is no tick that could be resting on
it and nothing to un-tick. The obligation itself is real and is now discharged three times over:
Worker 2 ran it against the artifact, Worker 3 widened it to `KANBAN.md` + `docs/GLOSSARY.md`, and I
re-ran it here across **five** files — the spec, the rationale, the artifact, `KANBAN.md`, and
`docs/GLOSSARY.md` — **exit 0** on every one, plus `git diff --check` exit 0 repo-wide.

That a reviewer rather than the builder closed the gap does not invalidate the discharge, and the
rule that governs it is worth stating so the next pass does not re-argue it: **a verification
obligation is discharged by the measurement existing in the artifact with its command, not by which
worker's hands ran it.** The opposite rule would make every reviewer re-run a `revision-needed`
trigger, which would invert the point of the review pass. The narrow scope was also defensible on its
own terms — `KANBAN.md` is generator-owned, so its layout is the generator's contract, not the
pass's.

#### Low 2 — `docs/GLOSSARY.md` listed under `### Files touched` though byte-unchanged: REJECTED, no change

Intentionally rejected, with the reason recorded. The bullet **states its own status** ("byte-
unchanged", "not a modified path in `git status`"), so it misleads nobody who reads it, and both
clauses are true by measurement here (`cmp` against `git show HEAD:docs/GLOSSARY.md` is identical).
More: the entry is **load-bearing evidence**, not noise. A5 required the post-regenerate state of
`docs/GLOSSARY.md` to be explicitly classified as clean-or-drift; the generator did run against that
file, and listing it is what records that it ran. Deleting the bullet would delete the evidence for
the classification and leave the reader unable to distinguish "the generator ran and changed nothing"
from "the generator was never pointed at it" — which is precisely the unstated-absence failure this
plan set out to avoid. Over-listing is the safe direction, as Worker 3 said. **No change.**

#### DRY escalation — the link-and-anchor checker, now on its fifth measured argument: CONSOLIDATED, not opened

Correctly escalated rather than built: `scripts/` is outside every write set in this cycle, and
promotion is a maintainer call already tracked at `KANBAN.md:309`. I did not open it. What I owe
instead is the consolidation, and it is in the catalog below as **item 5**, written so the next
author does not rediscover the defects one at a time.

One fact sharpens the case beyond "five hand-rolls". The **underscore-strip** defect is not a fifth
distinct trap — it is a **recurrence**. R1 measured it, named it, and wrote it into its hand-off item
8 (*"a GitHub slugger must keep the underscore — stripping it turned
`#coordination-with-spec-001-django_types-0_0_1md` into a false DANGLING report in this very pass"*);
two rounds later R3's Worker 3, writing a checker from scratch, reproduced the identical defect
against the identical link definition. A written-down trap in a closed artifact did not stop the next
implementation from re-introducing it. **That is the argument for a checker with regression tests, and
prose in a hand-off is measurably not a substitute for one.**

### The terms-CSV ruling — mine to make, and it stands at three

This is the one escalation where Worker 1 is the right authority, because the only mechanism that
could grow the set requires a **spec-body link**, which no other role may write. I re-derived the
measurement rather than adopting it (D3 above): four glossary-backed terms are named in the spec body
without a link — `DjangoConnectionField` (`:25`), `finalize_django_types` (`:31`), `FK-id elision`
(`:33`), `Visibility boundary` (`:48`) — and `Plan cache` / `Meta.optimizer_hints`, which R2's
hand-off named, occur **0** times in the spec body. R2's premise was wrong, not merely its count.

**Decision: the set stands at three. No CSV row added, no spec-body link added, no edit made.** Four
independent reasons, any one sufficient:

1. **Nothing is broken.** `check_spec_glossary.py` validates that the terms a spec *links* resolve to
   real anchors; it does not require exhaustiveness, and it exits 0 at three. **Never edit a CSV to
   make a check pass** — and no check needs one to pass here.
2. **The CSV is a DONE card's shipped board record.** It is what `import_spec_terms` rebuilds card
   2's `glossary_links` from. Adding a row rewrites what card `DONE-002-0.0.2` shipped, twelve
   releases after it closed. That is a board-history edit wearing a documentation-completion costume.
3. **`AGENTS.md` rule 26 puts fold-in in the completing spec's Slice 5.** Spec-002's completing slice
   ran at `0.0.2`. Enriching a shipped spec's glossary linkage outside its own completing slice is
   the thing the rule exists to prevent.
4. **The addition is not small.** A new anchor needs a matching **link in the spec body** or
   `check_spec_glossary` starts failing on the very row that was added — so "add a CSV row" is really
   "edit the shipped contract of a closed card", and it would move the anchor map off the deliberate
   1/1/2 R2 built by adding destinations before removing sources.

**Stated in a form the next author can act on**, since a ruling nobody can execute against is just an
opinion: *the set should grow only in a cycle that is already editing spec-002's body for another
reason, and only if that cycle also owns card 2's board record. The four candidate terms and their
spec lines are listed above. The mechanical preconditions are: add the spec-body reference-style link
first, then the CSV row (one row per anchor — `import_spec_terms` rejects a duplicate anchor where
`check_spec_glossary` tolerates one), then re-run both commands, then re-render `KANBAN.md` so the
card's `#### Glossary terms` table matches.* Adding a `## Terms` note to the spec or the rationale to
record this decision would be narration, not contract; declining it with the assessment written down
here is the discharge.

### The five escalations R3 recorded — each confirmed real, correctly scoped, and given an owner

1. **`docs/GLOSSARY.md` (`0.0.2`) vs `CHANGELOG.md` (`0.0.3`).** Confirmed at all four sites by my own
   reading. Confirmed **not unilaterally correctable**: `GlossaryTerm.body`, card 2's `target_version`,
   the card id `DONE-002-0.0.2`, and the spec filename `…-0_0_2.md` must move together, and the
   authoritative record is closed by `AGENTS.md` rule 21. R3's ruling to escalate as **one** item with
   both readings written out is right. **Owner: maintainer.** Catalog item 2.
2. **Terms-CSV completeness.** Decided above. **Owner: closed by this pass**; reopening owner named in
   the ruling. Catalog item 3.
3. **`spec-003` stale at four sites.** All four re-read and still stale; `spec-006:136` / `:147`
   re-read and confirmed live and correct. R3's recommended replacement wording is accurate against
   the current text. **Owner: maintainer / whoever next opens `spec-003`.** Catalog item 4.
4. **The slugger-defect catalog.** Consolidated as catalog item 5. **Owner: maintainer**, tracked at
   `KANBAN.md:309`.
5. **Two `TODO(spec-035)` anchors in `optimizer/walker.py` (`:464`, `:1131`).** Reasoning confirmed on
   all three legs, each checked here rather than accepted: `BUILD.md` `## Cross-slice integration
   pass` step 6 scopes the sweep to anchors naming **this** build's spec or card (spec-002 / card
   002) and these name spec-035; both are indented `#` comments **inside function bodies**, so neither
   reaches `docs/TREE.md`'s docstring render; and package source is read-only this cycle. **No action
   in this cycle is correct.** Recording them is a genuine contribution, and it is preserved as
   catalog item 8 so a future sweep reads them as spec-035's debt rather than this cycle's.

### DRY check across R1, R2, and R3

- **Within R3: none introduced.** The diff adds no `.py`, no test, no `scripts/` entry. Its one
  durable text addition deliberately carries **no count** — it names the mechanism (a link definition
  targets `#visibility-status`) so a later companion entry cannot falsify it — and does not restate
  spec prose on the board. I read the stored column to confirm both properties rather than taking the
  review's word.
- **Across the three rounds, two duplications are real and both are already routed.** The
  link-and-anchor checker (five hand-rolls across two cycles: R1's, R2's, R3's Worker 2's, R3's Worker
  3's, and mine at C2 above — catalog item 5), and the rationale-file preamble that is a de-facto
  template with no single source (R1's final verification, catalog item 6). Neither is fixable from
  inside any residual item's write set, which is why both are catalog items rather than findings.
- **Within the spec/rationale pair: unchanged from R2's measurement.** R3 wrote neither file, so the
  one labelled 12-word quotation at 2.9% shingle overlap is exactly what R2's final verification
  accepted. Re-measuring it here would compare a new scanner's number against another scanner's —
  which `worker-1.md`'s standing lesson says is not a comparable quantity — so I re-confirmed the
  inputs (both files byte-unchanged) instead.

### Tests

**R3 touched no source and no test, so the run is skipped, per the dispatch.** Confirmed rather than
asserted: `git status --porcelain` carries **no** path under `django_strawberry_framework/`, none
under `tests/`, none under `examples/fakeshop/apps/*/tests/` or `examples/fakeshop/test_query/`
(`examples/fakeshop/test_query/README.md` is dirty, but it is a baseline concurrent-session path and
is not a test module). `git diff -- django_strawberry_framework/__init__.py` is empty, so no public
surface moved. No `pytest` was invoked in this pass, with or without flags, and no `--cov*` flag was
used anywhere in it.

### Failability, hot path, floor verification

All three were pre-declared `none` for this item and the declaration holds by inspection: R3 adds no
guard, cap, gate, rejection path, or validation branch; it touches nothing that runs per request, per
resolver, per row, per connection, or per outbound message; and it touches no Django / Strawberry /
channels integration seam. `### Failability proofs` correctly reads `None; this pass introduced no new
boundary.` with the heading kept. Nothing owed, and their absence is not a finding.

### Spec reconciliation

**Nothing R3 surfaced requires a spec or rationale edit, and the interstitial Worker 1 pass correctly
never triggered.** Verified positively, not accepted:

- `docs/SPECS/spec-002-optimizer-0_0_2.md` is **9,844 bytes / 103 lines** — byte-identical to what R2's
  final verification closed at and to what Worker 3 accepted. `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`
  is **33,620 bytes**, likewise unchanged. R3 wrote neither.
- The three audit findings that could have forced an edit each land **outside** both files: the
  version disagreement is on the glossary/changelog/board surfaces, the sibling staleness is in
  read-only `spec-003`, and the checker is a `scripts/` item.
- One leg the audit did not explicitly cover, checked here because an archive audit is where it
  belongs: **every sibling-spec path the spec names in prose resolves on disk** — `spec-003`,
  `spec-004`, `spec-033`, `spec-035`, `spec-045`, `spec-047` under `docs/SPECS/`, and
  `spec-001-django_types-0_0_1.md` as a bare sibling filename. These are code-span mentions rather
  than markdown links, so C2's link audit structurally cannot see them; all seven exist. **Zero
  broken.** No edit owed.
- The spec's own status/header obligation: no status block exists, so nothing to falsify.

### Re-verified commands, quoted exactly

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md
OK: 3 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-002-optimizer-0_0_2.md
exit=0
$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md
exit=0
$ uv run python scripts/check_trailing_commas.py --check docs/builder/bld-002-r3-doc_completion_archive.md
exit=0
$ uv run python scripts/check_trailing_commas.py --check KANBAN.md docs/GLOSSARY.md
exit=0        # Low 1's widened scope, run a third time

$ git diff --check
exit=0

$ grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+' docs/SPECS/spec-002-optimizer-0_0_2.md
exit=1        # no match
$ grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+' docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md
exit=1        # no match

$ grep -o '\]\[glossary-[a-z0-9_-]*\]' docs/SPECS/spec-002-optimizer-0_0_2.md | sort | uniq -c
   2 ][glossary-djangooptimizerextension]
   1 ][glossary-djangotype]
   1 ][glossary-only-projection]

$ uv run python scripts/build_kanban_md.py --check
KANBAN.md is up to date.                exit=0
$ uv run python scripts/build_kanban_html.py --check
KANBAN.html is up to date.              exit=0
$ uv run python scripts/build_glossary_md.py --check
docs/GLOSSARY.md is up to date.         exit=0
$ uv run python scripts/build_tree_md.py --check
docs/TREE.md is up to date.             exit=0

$ grep -rEn 'TODO\(spec-002|TODO-(ALPHA|BETA|STABLE)-002' django_strawberry_framework/ tests/ examples/
exit=1        # zero anchors in shipped source, tests, or the example project
```

**Anchor map 1 / 1 / 2** — unchanged, and better than the 1/1/1 the constraint requires.
**Terms CSV byte-untouched** — 323 bytes, 3 data rows, 3 distinct anchors, absent from `git status`.
**Spec byte count: 9,844, unchanged** (I made no spec edit). Rationale: 33,620, unchanged.

**`git status --short` -> 15 paths**, at this pass's open and again at its close. Identical both
times, and identical to the set Worker 2 recorded: the nine baseline-dirty concurrent-session paths,
this cycle's one modified spec, and this cycle's five untracked files. Nothing unexpected appeared;
nothing was reverted; no path was edited outside my write set. The mixed
`KANBAN.md` / `KANBAN.html` / `examples/fakeshop/db.sqlite3` diff carries R3's one `CardItem.text`
edit plus the concurrent session's work, and goes to the maintainer to reconcile at commit — no
attempt was made to separate it.

### Final status

`final-accepted`.

### Summary

R3 finished the documentation and audited the archive, and found the archive already sound. Its **one
mutation** is a single `CardItem.text` on card `TODO-ALPHA-052-0.1.0` — the `KANBAN.md:310` deferral
bullet that this cycle itself falsified, R1 by removing `## Open questions`, R2 by removing
`## Current state`, and R2 again by adding the very `#anchor` citation the old bullet swore did not
exist. The replacement was applied through the ORM with `.save()`, proved byte-identical to R2's
decided text by **four** independent derivations (R2's blockquote reconstructed by three different
passes including mine, this artifact's fenced block, and the stored column), and carried onto the
board by regenerating `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md`. The new text states the
surviving constraint — `## Visibility status` is held by two `spec-006` citations and by the
companion rationale's `#visibility-status` link definition — and deliberately carries **no count**, so
the next entry the companion gains cannot falsify it the way the old bullet was falsified.

Everything else R3 did was measurement, and the honest discharge of a measurement is reporting the
zeros: `docs/README.md`'s five optimizer claims all hold against source (zero edits); `docs/TREE.md`
is up to date with zero staging language in the seven feeding docstrings; the three glossary entries
describe the shipped O1-O6 surface rather than merely existing; card `DONE-002-0.0.2` renders 3
glossary rows, 12 package files that all exist, and 7 accurate scope bullets; ten standing docs
contain zero `spec-002` references and no pre-archive `docs/spec-002…` path survives anywhere; the
spec and its companion emit 4/4 and 19/19 link definitions with zero undefined, orphaned, duplicated,
or broken, and all eleven fragments resolving; the `SpecDoc` / card / CSV chain is intact at three
anchors; and zero staged anchors naming this build's spec or card survive in package source, tests, or
the example project. Five findings were escalated with zero edits, each now carrying a named owner in
the catalog below.

`docs/GLOSSARY.md` is byte-identical to HEAD, proved by `cmp` rather than by absence from
`git status`. The spec and the rationale are byte-unchanged by R3, which is why the plan's
interstitial Worker 1 pass correctly never ran.

### Spec changes made (Worker 1 only)

**`docs/SPECS/spec-002-optimizer-0_0_2.md` — no change.** 9,844 bytes / 103 lines, byte-identical to
the file Worker 3 accepted and to R2's close. No finding reached it: the three audit findings that
could have forced an edit all land outside the file (glossary/changelog/board dating, read-only
`spec-003`, a `scripts/` promotion), and the terms-CSV question was ruled closed at three rather than
grown, which is what would have required a new spec-body link.

**`docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` — no change.** 33,620 bytes, byte-identical
to R2's close. R3 surfaced no rejected alternative, retraction, or decision change to append.

**No deferral reason is owed under this heading: the checklist audit left no box `- [ ]`,** and no box
was un-ticked. The deferrals this cycle does carry are not checklist boxes — they are the eight
catalog items below, every one with a named owner.

### Notes for Worker 1 (spec reconciliation) — the consolidated `### Deferred work catalog` for `bld-002-final.md`

This is the direct input to the final gate's `### Deferred work catalog`, walked out of R1's, R2's,
and R3's spec-reconciliation notes, `What looks solid` sections, and final-verification dispositions.
**Written to be read by someone who was not here.** Every item names its source artifact section, the
spec line that licenses the deferral where one exists, a one-line description, and an owner. This
cycle plainly has deferrals, so the no-deferrals literal does not apply.

1. **The `KANBAN.md:310` card bullet — CLOSED, not deferred.** *Source:* R1 hand-off item 1 -> R2 item
   1 -> R3 `#### A`. *Licensing spec line:* none; the build plan pre-authorized a DB write when the
   audit found real drift. R3 executed it; the stored column is 1268 chars / `041f0354…4971040` and
   the render carries it. **Owner: none — discharged.** Listed so the next author does not re-open a
   closed key.
2. **The `0.0.2`-versus-`0.0.3` release-dating disagreement.** *Source:* R2 hand-off item 10 -> R3
   `#### B` / B5 and Notes item 2. *Licensing spec line:* none — `AGENTS.md` rule 21 closes
   `CHANGELOG.md` to every worker, which is what makes it undecidable inside a build.
   `docs/GLOSSARY.md:714` and `:1382` date `DjangoOptimizerExtension` and `only()` projection to
   `0.0.2`, matching card `DONE-002-0.0.2`'s `target_version`; `CHANGELOG.md` `[0.0.2]` calls the
   extension *"early … depth-1"* while `[0.0.3]` dates the end-to-end surface (nested chains, `only()`,
   downgrade) to `0.0.3`. Whether a `**Status:** shipped (X)` line names **first shipped** or
   **complete** is an editorial call about the glossary's dating convention for a subsystem that
   shipped across two releases. It is not unilaterally correctable: `GlossaryTerm.body`, the card's
   `target_version`, the card id, and the spec filename `…-0_0_2.md` must move together. **Owner:
   maintainer.**
3. **Card 2's terms-CSV set — DECIDED at three, with the reopening conditions written down.**
   *Source:* R2 hand-off item 11 -> R3 `#### D` / D3 -> this pass's ruling above. *Licensing spec
   line:* none; `AGENTS.md` rule 26 (fold-in belongs to the completing spec's Slice 5) is what closes
   it. Four glossary-backed terms are named in the spec body without a link —
   `DjangoConnectionField` (`:25`), `finalize_django_types` (`:31`), `FK-id elision` (`:33`),
   `Visibility boundary` (`:48`) — and that gap is deliberate. **Owner: closed.** Reopening requires a
   cycle that already owns both spec-002's body and card 2's board record; the mechanical sequence is
   in the ruling above. For the record: R2's premise was wrong as well as its count — `Plan cache` and
   `Meta.optimizer_hints` occur **0** times in the spec.
4. **`spec-003-optimizer_nested_prefetch_chains-0_0_2.md` is stale at four sites.** *Source:* R2
   hand-off item 4 (which named one) -> R3 `#### C` / C4 (which found four). *Licensing spec line:*
   none; the file is a read-only sibling owned by another card, per the build plan's
   `## Build-wide context flags`. `:4` says O4 has not shipped (it has); `:27` publishes
   `plan_optimizations` at the pre-D4 arity and names `_collect_scalar_only_fields`, which is absent
   from the package (**0** occurrences); `:333` and `:335` are discharged when-O4-ships instructions,
   `:333` naming `## Current state`, a section that no longer exists. R3 supplies recommended
   replacement wording for `:4` and `:333` in its Notes item 4. **Owner: maintainer / whoever next
   opens `spec-003`.** **Do not sweep up `spec-006-public_surface-0_0_3.md:136` and `:147`** — both
   name `## Visibility status` and both are live and correct; that heading survives in spec-002
   precisely because of them.
5. **Promote one spec/rationale link-and-anchor checker into `scripts/`, with the four known slugger
   defects encoded as regression tests.** *Source:* R1 hand-off item 8 -> R2 item 8 -> R3 Notes item 5
   and Worker 3's `### DRY findings` -> this pass's consolidation. *Licensing spec line:* none;
   `scripts/` is outside every write set in this cycle. Already tracked as a board card at
   `KANBAN.md:309` — this is a **fifth measured argument for an existing item, not a new one.** The
   checker has now been hand-rolled five times across two cycles (R1's, R2's, R3's builder's, R3's
   reviewer's, and this pass's at C2), and the four defects measured between them are:
   - **(a) A heading that is itself a reference link, slugged without rendering the markup out
     first.** `check_spec_glossary.py::github_anchor` turns
     `## [Scalar field conversion][glossary-…]` into `…conversionglossary-scalar-field-…`. **False
     dangling.**
   - **(b) Whitespace runs collapsed.** GitHub replaces spaces **one at a time**, so a heading with a
     double space slugs to a double hyphen; a checker that collapses runs reports a **false PASS**.
     The only **silent** defect of the four, which makes it the most dangerous to leave unencoded.
   - **(c) Code spans deleted rather than masked before matching reference links.** A reference link
     here is routinely spelled ``[`only()`][ref]``; deleting the span leaves `[][ref]`, which
     `\[([^\]]+)\]` cannot match. R3's builder's first run reported 3 spec + 12 rationale **false
     orphans** from this alone. The fix is to mask the span's content to **same-length filler**,
     preserving the brackets.
   - **(d) `_` stripped as an emphasis marker before slugging.** It destroys `django_types`, so
     `#coordination-with-spec-001-django_types-0_0_1md` reports unresolved **against a correct link
     definition** — a false positive whose natural "fix" is to corrupt a good link. **This one is a
     recurrence:** R1 measured it and wrote it into its hand-off, and R3's reviewer re-introduced it
     from scratch two rounds later. A trap recorded in prose demonstrably did not prevent its own
     repetition; only a test can.
   **What a real checker must do**, so the requirement list is not re-derived either: render
   reference-link markup out of a heading before slugging; keep alphanumerics, `-` and `_` and drop
   the rest; replace each space with one hyphen without collapsing runs; mask code-span content to
   same-length filler; resolve every definition target from the **source file's own directory** with
   the fragment stripped; resolve every `#frag` against the **target** file's headings; and report
   defs, uses, undefined, orphaned, duplicate-defs, broken-on-disk, and inline cross-file links as
   separate counts. **Owner: maintainer**, via `KANBAN.md:309`.
6. **The rationale-file preamble is a de-facto template with no single source.** *Source:* R1's
   `### Disposition of the escalated DRY observation` and Worker 3's escalation there. *Licensing spec
   line:* none. 266 words / 13.0% of the body are shared with
   `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`, entirely in the preamble and framing —
   **zero shared words in the entries section**, which is where review value lives. R1 trimmed the one
   run with a canonical home elsewhere (the `**Who reads it.**` bullet, now a pointer at `BUILD.md`)
   and kept the rest, because unilaterally trimming a shared template would make the two siblings
   diverge and `spec-001`'s rationale belongs to a closed cycle. The natural fix is to **emit** the
   preamble, which folds into item 5's tool rather than standing alone. **Owner: maintainer.**
7. **The `_optimizer_field_map` rename-sweep residue — four live-code sites on a deleted symbol.**
   *Source:* R2 hand-off item 9 (scope-corrected at its final verification) -> R3 Notes item 6.
   *Licensing spec line:* none; `tests/` and `scripts/` are outside every residual item's write set.
   Three test **function names** in `tests/optimizer/test_field_meta.py` plus the token in
   `scripts/review_inspect.py` still name a symbol the package does not have. The prose survivals in
   `CHANGELOG.md` / `KANBAN.md` / `spec-010` / `spec-016` are **correct as history and are not in the
   sweep**. R3 corroborated the shape with a second instance: `_collect_scalar_only_fields` is
   likewise absent from the package (**0** occurrences) while `spec-003:27` still names it in the
   present tense. **Owner: maintainer / a future test-hygiene card.**
8. **Two `TODO(spec-035)` anchors in `django_strawberry_framework/optimizer/walker.py` (`:464`,
   `:1131`) — recorded, with no action owed.** *Source:* R3 `#### B` / B2 and Notes item 8, confirmed
   here. *Licensing spec line:* `BUILD.md` `## Cross-slice integration pass` step 6, which scopes the
   staged-anchor sweep to anchors naming **this** build's spec or card. These name spec-035, they are
   indented `#` comments inside function bodies so they never reach `docs/TREE.md`'s docstring render,
   and package source is read-only this cycle. **Owner: whoever closes spec-035.** Recorded so a
   future sweep reads them as that spec's debt rather than as this cycle's, and does not spend a pass
   re-deriving why they were left.

**One hand-off that is not a deferral, for the maintainer at commit time.** The
`KANBAN.md` / `KANBAN.html` / `examples/fakeshop/db.sqlite3` diff is **mixed**: R3's one
`CardItem.text` edit plus a concurrent session's work on card 52 (three new items) and card 21 (one),
all timestamped 2026-08-07T04:13:51. No worker attempted to separate it, per `BUILD.md`
`### Tracked binary / generated files`. The acceptance evidence that R3's own contribution is exactly
one row is the whole-database HEAD-versus-now content comparison in the review section, plus
`--check` exit 0 on all three generators, which asserts that every byte on disk is what the DB
renders — i.e. that nothing was hand-edited into a generated file.

**Closed and re-verified this cycle — do not re-raise.** R1's `## References` chronology clause
(removed); D15's four upstream locators (verified present in the checkouts `AGENTS.md` line 2 names,
with the two URLs honestly recorded as unfetched rather than claimed verified); drift rows D3 and
D13 (routed on "whose contract is the answer"); the retitle question (`## Current state` removed,
`## Visibility status` held by `spec-006` and the companion, `## Shipped slices` and
`## Implementation checklist` surviving on their merits); the missing blank line before `### O4`; and
the `## Coordination` framing tension.
