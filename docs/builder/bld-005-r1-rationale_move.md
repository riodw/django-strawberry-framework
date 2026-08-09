# Build: R1 — Spec rationale extraction (spec-005)

Spec reference: `docs/SPECS/spec-005-django_type_contract-0_0_3.md` (whole file; the move touched lines 1-2, 49-66, 76-82, 115-117, and 140 of the pre-move file)
Rationale file created: `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`
Status: final-accepted

**Shape note.** Per `docs/builder/build-005-django_type_contract-0_0_3.md` Deviation 2, R1 has no Worker 2 pass: `BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role that performs the move and states that Worker 2 never reads the rationale file. So the `## Build report (Worker 2)` section of `docs/builder/ARTIFACT.md` is not applicable here and the performance record lives under `## Move report (Worker 1)` below, carrying the same fields Worker 3 would otherwise read from a build report. `Status:` is `planned` on return, which Worker 0 reads as "dispatch Worker 3" for this item.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable, and deliberately so. `worker-1.md` `### Package-wide helper inventory before helper planning` gates *helper-like logic*; R1 changes no package source and adds no helper, shared constant, validation branch, coercion utility, or test helper. The build plan's `## Build-wide context flags` declares package source, `tests/`, and `examples/` read-only for the whole cycle. No inventory was refreshed and none was needed.
- **Existing patterns reused.** The archived precedents at the same `docs/SPECS/appx/` depth supplied the file shape: `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md:1-61` (the H1 with the `(deliberation, rejected alternatives, change record)` suffix, the "Deliberative companion to …" opener, the "**The move happened long after the release, not before the build.**" provenance paragraph, `## How to read this file`, `## Provenance of this record`, `## Entries keyed to the spec`, the *Moved* / *Deliberately left in the spec* vocabulary, and the per-entry `*Claims the spec no longer makes.*` closer) and `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` (the single-definition `[spec-NNN-rationale]` pointer form used from the spec side). The link-definition scaffold at this depth — `../` for a `docs/SPECS/` sibling, bare filename for an `appx/` sibling, `../../builder/` for `BUILD.md` — is copied from `spec-001-…-rationale.md`'s block.
- **New helpers justified.** None; no code was written.
- **Duplication risk avoided.** Three live risks, each named by the build plan and each handled explicitly and **measured**, not asserted:
  - **Against the spec.** The move is a cut, so no moved block may exist in both files. Measured: **0** non-scaffold 8-word shingles shared between the post-move spec and the rationale (15 total, all of them the `<!-- LINK DEFINITIONS -->` group-header scaffold both files are required to carry). Two copies were caught by that measurement mid-pass and removed — see `### Two copies caught by measurement`.
  - **Against `spec-001`'s rationale.** It already narrates the type-generation foundation, including the registry's own many-to-one correction. `## How to read this file` carries a bullet pointing at it and saying outright that the argument is not retold here.
  - **Against `spec-018` / `spec-019`.** They own the two mechanisms this spec predicted. Every entry **points** at the owning decision by number and states only *what spec-005 predicted and how it fared* — the build plan's `### What R1 inherits` instruction, applied literally. No decision text from either spec is restated.

### Implementation steps

Line numbers are pin-at-write-time; all are against the **pre-move** spec unless stated.

1. Measure the pre-move spec (bytes, lines, fence count) and take a read-only `git show HEAD:` copy into the scratchpad **outside** the repo as the verbatim-quote reference. Done.
2. Re-derive the true anchor carrier for each of the 7 terms rather than trusting the build plan's `### The 7-anchor constraint` table. Done — the table is wrong in three places; see `### The 7-anchor constraint — per-anchor result`.
3. Insert the companion-file pointer paragraph after the H1 (spec:1-2). Done.
4. `### One-model-one-type (alpha constraint)` — cut the "real friction" paragraph (spec:49), the whole `**Future direction.**` block including its four rules, its "belongs to its own future spec" lead-in, and its three sub-question bullets (spec:53-64), and the closing first-registered-wins rejection paragraph (spec:66); add a one-line pointer. Keep the opening paragraph and `**Decision for 0.0.3.**` untouched. Done.
5. `### Consumer override semantics` — cut the whole `**Future direction.**` block including the three numbered candidate approaches and the closing "None of these belongs in this spec …" paragraph (spec:76-82); add a one-line pointer. Keep the three surviving paragraphs untouched. Done.
6. Delete `## Open questions` in full (spec:115-117). Done.
7. Add `[spec-005-rationale]` to the spec's `<!-- docs/SPECS/ -->` link-definition group (spec:140). Done.
8. Write the rationale file: one entry per section cut from, plus one entry keyed to the removed `## Open questions` heading, plus a closing standing note on the asymmetry between the two predictions. Done.
9. Run the full verification set and record every command with its result. Done — `### Validation run`.

### Test additions / updates

None. R1 adds no test and changes no code path. The verification for this item is the command set recorded under `### Validation run`; `AGENTS.md` rule 15 forbids a `pytest` run that was not asked for, and the build plan declares no residual item touches source, tests, or `examples/`.

### Implementation discretion items

None reserved. R1 has no downstream builder, so nothing is delegable.

### Dispatched findings checklist

There is no `## Slice checklist` in spec-005 and this is not a review round, so — per `worker-1.md` planning step 8, which puts a `### Dispatched findings checklist` in this position when no spec slice checklist exists — the boxes below are the R1 obligations drawn from `docs/builder/BUILD.md` `## Spec rationale extraction`, `worker-1.md` `### Performing the rationale move`, and the build plan's R1 constraints. Worker 1 both performs and ticks here because Deviation 2 removes the Worker 2 pass; the ticks are audited at Worker 1's own final verification after Worker 3.

- [x] The move is a cut-and-paste, not a copy and not a summary: text that lands in the rationale left the spec (measured: 0 non-scaffold shared shingles).
- [x] Every section cut from keeps a one-line pointer in the spec naming what was moved and where.
- [x] The rationale file is keyed to the spec: every entry names the spec section it belongs to by heading and links a resolving anchor.
- [x] Rejected alternatives are recorded with the one-line reason each lost.
- [x] Every change a section has undergone is recorded with the later spec that caused it.
- [x] Every claim a section may no longer make is recorded, per entry.
- [x] Prose the **current spec decisions** have falsified was deleted rather than moved (rule 2) — vacuous here, and the entry saying why is in the rationale's `## Provenance of this record`.
- [x] Implementation-relevant rationale — the "why" that changes HOW a thing is built — stayed in the spec (the load-bearing carve-out); the two passages it kept are named in `## Provenance of this record`.
- [x] The spec narrates no history: no amendment block, no retraction paragraph, no "as of review round N" hedge was added.
- [x] `check_spec_glossary.py --spec …` still exits 0 and all 7 anchors still carry exactly one body link.
- [x] `check_trailing_commas.py --check` passes on the spec and the new rationale file.
- [x] `import_spec_terms --check` still exits 0 — the card-wrap chain the 7-anchor constraint protects is intact.
- [x] Every in-page anchor the rationale targets resolves against a real post-move spec heading.
- [x] Reference-style links only; `<!-- LINK DEFINITIONS -->` block present with all 10 canonical group headers in order; every definition target disk-checked.
- [x] `AGENTS.md` rule 27 holds in both files: no raw `path:NN`.
- [x] The rationale file is written directly to `docs/SPECS/appx/`, tracked and durable — never to `docs/` and moved after.
- [x] Spec byte count before and after reported.
- [x] The `spec-001` rationale is pointed at, not duplicated; `spec-018` / `spec-019` reasoning is pointed at, not restated.
- [x] No source, test, example, sibling spec, terms CSV, `CHANGELOG.md`, `KANBAN*`, `docs/GLOSSARY.md`, or DB file was written.
- [x] R2's scope was not pre-empted: no falsified contract statement was rewritten, and every hand-off is recorded under `### Notes for Worker 1 (spec reconciliation)`.

---

## Move report (Worker 1)

### Files touched

- `docs/SPECS/spec-005-django_type_contract-0_0_3.md` — 5 insertions, 27 deletions (`git diff --stat`). Two `**Future direction.**` blocks, one derivation paragraph, one rejected-alternative paragraph and one whole section cut; one companion pointer paragraph and two per-section pointers added; one link definition added.
- `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md` — new, 275 lines / 19,056 bytes.

### Byte count (required report)

| | lines | bytes |
|---|---|---|
| spec **before** | 154 | 13,346 |
| spec **after** | 132 | 11,002 |
| delta | -22 | **-2,344 (-17.6%)** |
| rationale file (new) | 275 | 19,056 |

Re-measured before the first edit with `python3 -c "d=open(...,'rb').read(); print(len(d), d.count(b'\n'))"`: **13,346 bytes / 154 newline-terminated lines**, matching the build plan's pre-flight figure exactly. Fence markers (`grep -c '^```'`): **0** before, **0** after, in both files — spec-005 carried no pseudo-code, which is the structural difference from the three predecessor cycles and is why this move's whole risk sat in prose judgement rather than in fence disposal.

The 17.6% cut is the smallest of the four residual cycles (spec-004's was 22.2%) and that is the correct outcome, not a shortfall: spec-005 is a contract spec whose four `## Topics` are decisions rather than slices, so its deliberative layer is two prediction blocks and one release-gating sentence, not eight per-slice arguments.

### What moved, what stayed, what was deleted

**Moved — cut from the spec, verbatim, and now only in the rationale.**

1. **The "real friction" paragraph** under `### One-model-one-type` — the DRF / `graphene-django` / `strawberry-graphql-django` precedent argument plus the three-file `registry.clear()` workaround inventory. It is the derivation for the `Meta.primary` prediction below, not a statement of the contract. Its per-topic competitive comparison moves under the maintainer decision recorded at `docs/builder/build-004-optimizer_beyond-0_0_3.md:192-208` (`## Maintainer decision — the surviving competitive positioning in ## Problem statement`), whose scope clause is explicit: per-topic competitive argument moves, a **problem statement's** statement of the competitor gap stays when the comparison is the document's subject. Spec-005's `## Problem statement` item 1 names the same three libraries and was **not touched** — it is the only surviving sentence saying why the constraint was flagged, and it is the sole carrier of two glossary anchors.
2. **The whole `**Future direction.**` block under `### One-model-one-type`** — the `Meta.primary: bool = False` prediction, its four rules, the "belongs to its own future spec" lead-in, and its three sub-question bullets.
3. **The first-registered-wins rejection paragraph** (spec:66) — the one rejected alternative the spec stated as a rejection, with its reason.
4. **The whole `**Future direction.**` block under `### Consumer override semantics`** — the three numbered candidate approaches and the closing "None of these belongs in this spec … Until then: limited, not guaranteed."
5. **The whole of `## Open questions`** — "None blocking 0.0.3 …", a sentence whose entire meaning is a release-gating judgement about a release that shipped eleven minor versions ago.

Each of the five was verified present at HEAD and absent from the post-move spec by normalized-whitespace substring match against the read-only `git show HEAD:` copy; the check is in `### Validation run`.

**Stayed in the spec under the load-bearing carve-out.** This is the part of the job the dispatch names as the whole job, so each is listed with the defect its loss would cause:

1. **`### One-model-one-type`'s opening paragraph** — the collision rule *and its reason* (an unambiguous `model_for_type` reverse lookup, a single `convert_relation` target). The reason is attached to a live rule and explains what the rule buys; a reader who loses it cannot tell whether the constraint was arbitrary. It is also falsified by HEAD (drift row D2), which makes it R2's sentence and not R1's — moving it would have pre-empted R2 and left the correction with no anchor.
2. **`### Consumer override semantics`'s `**Decision for 0.0.3.**`, including its merge-code-can-stay clause.** That clause is a standing instruction not to rip the merge out. A builder never reads the rationale, so moving it would have put a "do not delete this code" instruction where no builder can see it — the exact failure the carve-out exists to prevent.
3. **`## Problem statement` in full**, including item 1's competitor comparison and the closing "unifying thread" paragraph. `worker-1.md` puts **goals** on the STAYS list verbatim, and the unifying-thread paragraph is this spec's goal statement — the only sentence saying why the four topics exist.
4. **`### Accepted vs deferred Meta keys`'s promotion rule**, including the parenthetical naming the original `Meta.interfaces` mistake. The rule is normative and the parenthetical is what gives it teeth: it names the failure shape a builder has to recognise.

**Deleted rather than moved (rule 2): nothing.** Rule 2 deletes prose **the current decisions have falsified**, and nothing in spec-005 is falsified by spec-005 — the document is internally consistent. What falsified it is the package, which is a different question and item R2's. The rationale records that reasoning explicitly under `## Provenance of this record` so a reviewer does not read the absence of deletions as a skipped step.

### Two copies caught by measurement

The shingle measurement under `### DRY analysis` is not decoration: it caught **two** places where the first draft of the rationale quoted a spec sentence that is **staying** in the spec — a copy, not a move, and one that would go stale the moment R2 rewrote either sentence.

- The `### Consumer override semantics` entry quoted the spec's "the skipped test stays as a contract pin and unskips when the real mechanism ships" promise in order to key `spec-019` Decision 5's rejection to it. Rewritten to describe the promise and cite the section, quoting nothing.
- `## Provenance of this record` quoted the merge-code-can-stay clause to explain why it stayed. Rewritten to name the clause without reproducing it.

Both fixes were re-measured; the non-scaffold overlap is now 0. Recorded because the failure mode is invisible to reading — both quotes were *correct*, *attributed*, and *illustrative*, and neither looks wrong until you ask which file owns the sentence.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-005-django_type_contract-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` **exit 0**. Character-identical to the build plan's pre-flight step-6 baseline.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-005-django_type_contract-0_0_3.md docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md` → **exit 0** on both files. Both carry `<!-- LINK DEFINITIONS -->` and all 10 canonical group headers in the canonical order.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0** — the card-wrap chain the 7-anchor constraint protects is intact, and the run left no DB churn (see `git status` below).
- **Cut-not-copy, measured.** 8-word shingle intersection between the post-move spec and the rationale: **15 total, 0 non-scaffold** (all 15 are the `<!-- LINK DEFINITIONS -->` group-header run both files must carry).
- **Verbatim-move check, all five moved blocks.** Seventeen distinct quoted spans normalized for whitespace and tested three ways each — present at HEAD, present in the rationale, absent from the post-move spec. **17/17 pass.** The HEAD reference was obtained read-only with `git show HEAD:docs/SPECS/spec-005-django_type_contract-0_0_3.md > <scratchpad outside the repo>/spec-005-HEAD.md`.
- **Reference integrity.** Spec: **8 definitions / 8 distinct uses**, 0 undefined references, 0 unused definitions. Rationale: **8 / 8**, 0 undefined, 0 unused.
- **Link targets disk-checked.** All 8 rationale definition targets and all 8 spec definition targets resolve on disk from their own file's directory. The 4 anchor-bearing targets were additionally slug-checked with `scripts/check_spec_glossary.py::github_anchor` against the target file's real headings: `#non-goals`, `#one-model-one-type-alpha-constraint`, `#consumer-override-semantics-deferred-to-a-future-spec` (all into the post-move spec) and the 7 `GLOSSARY.md` anchors — **all resolve**.
- **Duplicate heading slugs:** **0** in the spec (12 headings, `grep -c '^#'`), **0** in the rationale (8 headings). No in-page anchor is ambiguous. Both counts were re-measured when this line was written — the first draft carried 13 and 11 from memory and both were wrong.
- `grep -c '^```'` → spec **0**, rationale **0**. Zero at HEAD and zero now.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files → **no match** (exit 1). Rule 27 preserved, not merely unbroken.
- `grep -P '\]\((?!#|https?:)'` over both files → **no match** (exit 1). No inline `](path)` link in either.
- `git status --short` → adds exactly `M docs/SPECS/spec-005-django_type_contract-0_0_3.md` and `?? docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md` to the recorded baseline. **`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` are all clean**, as the build plan's `## Concurrent-writable tracked binary / generated files` expects for R1. The baseline-dirty spec-004 entries and the four deleted `bld-003-*.md` files are unchanged and untouched.
- No `pytest` run (`AGENTS.md` rule 15); no `ruff` run (no `.py` file touched); no coverage-shaped flag in any form.
- No `git stash`, `git checkout`, `git restore`, `git worktree`, branch creation, or commit at any point.

### The 7-anchor constraint — per-anchor result

All 7 survive at exactly **1 body use + 1 definition** each (`grep -o "\[glossary-<anchor>\]" | wc -l` → 2 for every one), and **no anchor needed re-siting**: every carrier sits in text this pass did not touch. The terms CSV was never opened.

**The build plan's `### The 7-anchor constraint` table is wrong in three places**, found by re-deriving rather than trusting it (`worker-1.md` step 2 above). The table over-counts carriers because it reads a plain code span as a link: only a reference-style use — a bracketed code-span label followed immediately by a bracketed `glossary-…` reference id — is a carrier.

| Anchor | Plan's claimed carrier(s) | **Actual carrier at HEAD** | After the move |
|---|---|---|---|
| `configurationerror` | `## Problem statement` item 1 **+ `### Invalid …` body** | item 1 **only** — the `### Invalid …` body's `ConfigurationError` is an unlinked code span | unchanged (line 9) |
| `djangotype` | `## Problem statement` item 1 | item 1 | unchanged (line 9) |
| `metafields`, `metaexclude` | item 3 **+ the `### Invalid …` heading** | item 3 **only** — the heading's `Meta.fields` / `Meta.exclude` are unlinked code spans | unchanged (line 11) |
| `metainterfaces` | `## Problem statement` item 4 | item 4 | unchanged (line 12) |
| `metaprimary` | `## Current state` final paragraph **+ `### One-model-one-type` Future direction** | `## Current state` final paragraph **only** — the Future direction block's `Meta.primary: bool = False` is an unlinked code span | unchanged (line 31) |
| `metamodel` | `### Invalid …` body | `### Invalid …` body | unchanged (line 67) |

The correction matters in one direction and matters a lot: the plan rated `metaprimary` **"Highest risk — both carriers are D2/D3 material"**, and the real position is worse, not better. It has **one** carrier, not two, and that carrier is `## Current state`'s final paragraph — a falsified status sentence R2 is very likely to rewrite or delete. `metaprimary` is now a **single point of failure held entirely inside R2's write set**. Carried to `### Notes for Worker 1 (spec reconciliation)` as the cycle's top anchor risk.

### Hot-path budget

Not applicable; plan declares no hot path. No residual item in this cycle changes package source.

### Floor verification

Not applicable; plan declares floor-verification scope `none`. R1 touches no Django / Strawberry / channels integration seam.

### Failability proofs

None; this pass introduced no new boundary. R1 writes two Markdown files and adds no guard, gate, or rejection path.

### Implementation notes

- **One link definition, not four.** The spec's three pointers all resolve through a single `[spec-005-rationale]` definition rather than deep-linking each pointer to its own rationale heading. Follows the spec-004 precedent, and the reason is anchor rot: the rationale is append-only across the rest of this cycle, so a spec-side anchor into one of its headings is a cross-file dependency this cycle would have to re-verify at every later item. The rationale side deep-links **into the spec** freely, because that direction is verified by the same slug check that already runs.
- **The `## Open questions` deletion got no per-section pointer.** There is no surviving decision in the spec to hang one on. The companion paragraph after the H1 names the removed section explicitly instead, so rule 1's requirement — a reader can see the deliberation exists — is met by the one pointer that can still be read.
- **The moved predictions are recorded against HEAD, and that is not R2's work leaking into R1.** A prediction's whole content is a claim about the future, so "what became of it" is the only fact worth recording about it; recording it does not restate or correct any sentence still standing in the spec. The build plan's `### What R1 inherits` asks for exactly this, and it is the one class where the two items' scopes touch by design rather than by accident.
- **`## Standing note` is the file's payload.** The build plan calls the two-prediction asymmetry "the single most valuable thing this rationale can record"; the note names the mechanism behind it rather than just the outcome — the `Meta.primary` block predicted a **contract** (configurations and required outcomes, so an implementation had to satisfy it), the consumer-overrides block predicted **implementations** (three techniques, all downstream of a diagnosis that was already wrong). A prediction stated as a required outcome survives a wrong diagnosis; one stated as a technique inherits every error in it.

### Notes for Worker 3

- The rationale file is **new**, so there is no HEAD version to diff it against. The verifiable claims about it are the measurements in `### Validation run`; every one names its command and is re-runnable at the recorded scope.
- The read-only HEAD copy of the pre-move spec is at `<scratchpad>/spec-005-HEAD.md` outside the repo. Re-derive it with `git show HEAD:` rather than trusting that file's contents.
- The judgement calls most worth attacking, in the order I would attack them: (a) whether the `### One-model-one-type` opening paragraph's *reason* clause should have moved with the friction paragraph — I kept it under the carve-out and because it is D2's anchor for R2; (b) whether the friction paragraph's competitive comparison is really covered by the spec-004 maintainer decision's scope clause, or whether it needed its own escalation; (c) whether recording the two predictions' fates against HEAD pre-empts R2.
- The build plan's anchor table is wrong in three places (`### The 7-anchor constraint — per-anchor result`). If you re-verify one thing mechanically, verify that — it changes the risk assessment R2 inherits.

### Notes for Worker 1 (spec reconciliation)

Hand-offs to R2. None of these was acted on by R1.

1. **`metaprimary` is a single-carrier anchor and its only carrier is falsified prose.** Corrected from the build plan's two-carrier reading. The carrier is `## Current state`'s final paragraph ("… the registry uniqueness resolution is deferred to a future `Meta.primary` spec") — drift rows D1/D2/D17 all bear on it. **R2 must re-site the reference-style link that carries the `glossary-metaprimary` anchor into surviving contract prose before or in the same edit that rewrites that paragraph**, never by keeping narration alive to hold a link, and never by editing the CSV. This is the cycle's top anchor risk and it now sits entirely inside R2's write set.
2. **Four other anchors also sit in falsified prose.** `configurationerror` and `djangotype` are both sole-carried by `## Problem statement` item 1 (D2 material); `metainterfaces` is sole-carried by item 4 (D13). Only `metafields` / `metaexclude` (item 3) and `metamodel` (`### Invalid …` body, D16 — the one topic true at HEAD) sit in prose HEAD does not falsify. R2 re-runs `check_spec_glossary.py` after every edit and quotes the result.
3. **D15 is discharged by R1 and needs no R2 edit.** The `registry.clear()`-workaround sentence left the spec with the friction paragraph. The rationale records the claim in the spec's own tense **and** records that its stated reason inverted at `0.0.6` (the calls now buy test isolation, not collision avoidance). R2 should confirm rather than re-do it.
4. **D3, D4 and D8 are partially discharged by R1**, in one direction only. The prediction text those rows quote is gone from the spec, so there is nothing left in the spec for R2 to correct on those rows; the record of what the predictions were and how they fared is in the rationale. What R2 still owns is every *other* sentence those mechanisms falsify — notably `## Non-goals` (D17, "the **future** `Meta.primary` mechanism … the **future** consumer-overrides mechanism") and `## Current state`.
5. **The `## Open questions` removal leaves `## Non-goals` carrying the deferral alone.** The removed section said the two follow-on specs are "deliberately deferred"; `## Non-goals` now carries the whole of that statement, in a sentence D17 marks false on the word "future". R2 should treat `## Non-goals` as load-bearing rather than incidental.
6. **`## Coordination …`'s "must update this contract spec" instruction is untouched and is the cycle's root cause (D18).** It reads as a live obligation that no spec has ever discharged. R1 left it because it is normative prose, not deliberation. The rationale's `## Open questions` entry records the bet-that-did-not-pay framing so R2's decision — keep the instruction, or point at `ALLOWED_META_KEYS` as the single source — has the argument available without re-deriving it.
7. **Retitling `### Accepted vs deferred Meta keys` is an inbound break.** `docs/SPECS/spec-006-public_surface-0_0_3.md` cites that section **by title** and is read-only this cycle. R1 did not touch the heading. If R2 retitles it, the break is recorded and escalated, not silently accepted.
8. **The two `**Decision for 0.0.3.**` blocks now sit directly above their rationale pointers.** Both are normative and both are stale in their second halves (D6: `docs/README.md` has no `## Current surface` section; D7: the skipped test was deleted). R2 owns both; R1 deliberately left them intact so the correction lands as one coherent rewrite rather than being half-done by two items.

### Review outcome

Not applicable — this is the Worker 1 move pass. `Status: planned` on return, which Worker 0 reads as "dispatch Worker 3" per Deviation 2.

---

## Review (Worker 3)

Every number below was re-derived in this pass. Nothing in the move report, and nothing in the build plan, was accepted on its prose — including the corrections the move report itself makes to the plan. The read-only HEAD reference was taken with `git show HEAD:docs/SPECS/spec-005-django_type_contract-0_0_3.md > <scratchpad outside the repo>/spec-005-HEAD.md`; `HEAD` re-derived as `346d67312599c0536980969caa39085ab3885ae8`. No `git stash` / `checkout` / `restore` / `worktree`, no branch, no commit, no `pytest`, no coverage-shaped flag.

### High:

None.

### Medium:

#### One cut sentence exists in neither file, and two statements in the durable rationale are false as a result

The move report and the rationale both assert that the whole `**Future direction.**` block under `### One-model-one-type` moved, and the rationale's `## Provenance of this record` states outright that **"Nothing was deleted outright by this pass."** Both are false by one sentence. Pre-move spec line 60 — the lead-in that introduces the three sub-questions — was cut from the spec and does **not** appear in the rationale in any form:

```docs/SPECS/spec-005-django_type_contract-0_0_3.md:60 (pre-move)
This work belongs to its own future spec (`spec-meta_primary.md` or similar) which will need to address:
```

Proof, at line granularity rather than by span sampling:

```shell
git diff -U0 -- docs/SPECS/spec-005-django_type_contract-0_0_3.md   # 18 removed non-empty lines
# each removed line, whitespace-normalized, tested against HEAD / post-move spec / rationale
```

17 of the 18 removed lines are present at HEAD, absent from the post-move spec, and present in the rationale. The 18th (above) is present at HEAD, absent from the post-move spec, and **absent from the rationale**. (Two further apparent misses in the raw run resolve on inspection: `**Future direction.**` and `## Open questions` are label/heading text the rationale reproduces without the marker, and the three sub-question bullets are quoted with an opening `"` inside the bullet, which the naive substring test does not span. Only line 60 is a genuine loss.)

Why it matters, in three separate ways:

1. **The rationale's contract is that moved text "exists here and nowhere else."** A sentence in neither file breaks that promise for the one reader the file exists to serve — someone reconstructing what spec-005 actually predicted.
2. **`worker-1.md` rule 2 does not license the deletion.** It permits deleting only prose *the current decisions have falsified*, and this pass's own recorded reasoning is that nothing in spec-005 is falsified by spec-005 (`### What moved, what stayed, what was deleted`, "Deleted rather than moved (rule 2): nothing"). By that reasoning this sentence had to move.
3. **The lost content is on-thesis, not filler.** The sentence is the spec predicting the mechanism would get *its own spec*, with a guessed name (`spec-meta_primary.md`). It shipped as `docs/SPECS/spec-018-meta_primary-0_0_6.md` — the topic slug matched. The entry's "right on every point but the detection point" list does not currently carry that point, and `## Standing note`'s argument (a prediction stated as a required outcome survives) is strengthened by it.

**Root cause is the verification method, not the judgement.** `### Validation run` proves "seventeen distinct quoted spans … 17/17 pass". The spans were hand-chosen, so a sentence never made into a span cannot fail its own check — the population was sampled rather than established (`BUILD.md` `## Claims are proven mechanically`, "A stated count"). The `0` non-scaffold shingle overlap is a true and useful measurement but is blind in this direction: it proves nothing was *copied*, never that everything was *moved*.

**Recommended change (Worker 1, apply-changes pass — Deviation 2 routes R1 fixes to Worker 1, not Worker 2):** either quote the lead-in inside the `*Moved — the three sub-questions …*` block, or record it explicitly as a deletion with its reason in `## Provenance of this record` and correct the "Nothing was deleted outright" bullet. Quoting it is preferred: it costs one line, keeps the "nowhere else" promise literally true, and lets the entry add the matched-slug point. Then re-run the check at **line** granularity over `git diff -U0`, not over hand-chosen spans, and record that command.

### Low:

#### The "deliberately left in the spec" list names three passages; a fourth qualifies

`## Provenance of this record` enumerates "three passages that read like deliberation and are not this pass's to touch". A fourth was also left and is not named: `### Consumer override semantics`'s first two paragraphs — the `@strawberry.type`-rewrites-`cls.__annotations__` diagnosis and the "skipped `test_consumer_annotation_overrides_synthesized` … pins the failure mode" sentence. The same rationale entry says that diagnosis "was already wrong when it was written", and drift rows D5 / D7 confirm both are falsified at HEAD (the test does not exist; `grep -rn test_consumer_annotation_overrides_synthesized tests/ examples/ django_strawberry_framework/` returns nothing).

Leaving them is correct — they are falsified *factual* claims, which is R2's row, not deliberation to move. The defect is only that the provenance list reads as exhaustive and is not, so a later reader cannot tell whether the surviving diagnosis was considered or overlooked. One clause fixes it.

#### Two malformed reference-style link uses in this artifact

`docs/builder/bld-005-r1-rationale_move.md:143` and `:186` use `` `[`X`][glossary-…]` `` and `` `[`Meta.primary`][glossary-metaprimary]` `` as illustrations of a link's shape. The backtick nesting closes and reopens mid-token, so both render as a broken code span rather than as the literal link text they are demonstrating, and both are undefined reference uses in a file with no `[glossary-…]` definitions (0 definitions, 2 distinct uses). `check_trailing_commas.py --check` passes on the artifact, so this is cosmetic — but `:186` sits inside hand-off item 1, the instruction R2 acts on. Suggest a single code span with the backticks escaped, or wording that names the link without reproducing its syntax.

### DRY findings

- **No consolidation recommended, and one measurement recorded so it is not re-derived.** The rationale shares a large front-matter surface with its siblings: **197** non-scaffold 8-word shingles with `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` and **99** with `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`. Every one is house-style boilerplate (the H1 suffix, the "Deliberative companion to …" opener, `## How to read this file`, `## Provenance of this record`, the *Moved* / *Deliberately left* vocabulary). Filtering the intersection for substantive tokens (`registry|model|annotat|Meta\.|Strawberry|convert|primary|lazy_ref`) returns **0**. The two sibling rationale files overlap each other by the same amount, so this is a template, not a copy this pass introduced. **Existence challenge deliberately not raised:** the boilerplate is per-file navigational front matter that each file specializes (spec-005's version carries "This spec has no numbered Decisions" and the two-predictions framing), and hoisting it into a shared doc would put the reader's orientation one hop away from the file being read.
- **Against the two owning specs: 0 non-scaffold 8-word overlap** with `docs/SPECS/spec-018-meta_primary-0_0_6.md` and `0` with `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`. The "point at, do not restate" instruction in the build plan's `### What R1 inherits` is met mechanically, not just in intent. Every reference to those specs is a pointer plus a spec-005-specific comparison.
- **Against the post-move spec: 0 non-scaffold 8-word overlap** (15 total, all `<!-- LINK DEFINITIONS -->` group headers both files must carry). Independently re-derived; matches the move report. At 6-word width the only non-scaffold overlaps are `Consumer override semantics (deferred to a` / `override semantics (deferred to a future` — the section heading the keying rule *requires* the rationale to reproduce.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are unchanged. `git status --short` over `django_strawberry_framework/`, `tests/`, `examples/` source, `CHANGELOG.md`, and `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-terms.csv` shows no entry from this pass. The build plan's `## Build-wide context flags` declares the whole cycle source-free; R1 honoured it.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

The item touches `docs/SPECS/` and its `appx/` companion, so this applies. Everything below re-run in this pass.

- **`check_spec_glossary.py`, re-run and quoted:** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-005-django_type_contract-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` **exit 0**. Character-identical to the pre-flight step-6 baseline.
- **Per-anchor carrier count, re-measured independently at HEAD and after** (`grep -o "\]\[glossary-<anchor>\]"`, reference-style uses only — a plain code span is not a carrier):

  | Anchor | HEAD uses | post-move uses | defs | carrier |
  |---|---|---|---|---|
  | `configurationerror` | 1 | 1 | 1 | `## Problem statement` item 1 (spec:9) |
  | `djangotype` | 1 | 1 | 1 | `## Problem statement` item 1 (spec:9) |
  | `metafields` | 1 | 1 | 1 | `## Problem statement` item 3 (spec:11) |
  | `metaexclude` | 1 | 1 | 1 | `## Problem statement` item 3 (spec:11) |
  | `metainterfaces` | 1 | 1 | 1 | `## Problem statement` item 4 (spec:12) |
  | `metaprimary` | 1 | 1 | 1 | `## Current state` final paragraph (spec:31) |
  | `metamodel` | 1 | 1 | 1 | `### Invalid …` body (spec:67) |

  **Worker 1's correction of the build plan is confirmed, and I confirm it rather than inherit it.** The plan's `### The 7-anchor constraint` table is wrong in exactly the three rows the move report names, for exactly the reason it gives: it counted plain code spans as links. Every anchor was already single-carrier **at HEAD**, so the move dropped nothing — and six of seven now sit in prose the drift table marks falsified. `metaprimary`'s sole carrier is `## Current state`'s final paragraph, entirely inside R2's write set, which makes the plan's "Highest risk" rating an understatement rather than an overstatement. Worker 0's appended CORRECTION is accurate as written.
- **`import_spec_terms --check`, re-run:** `OK: 49 done cards have glossary links.` **exit 0** — the card-wrap chain the 7-anchor constraint protects is intact.
- **`check_trailing_commas.py --check`, re-run on all three files:** spec **exit 0**, rationale **exit 0**, this artifact **exit 0**. All carry `<!-- LINK DEFINITIONS -->` and the 10 canonical group headers in order.
- **Every link definition disk-checked from its own file's directory, both files:** spec **8 defs / 8 distinct uses**, 0 undefined, 0 unused; rationale **8 / 8**, 0 undefined, 0 unused. All 16 targets exist on disk. The depth convention is right in both directions — the rationale uses `../../builder/BUILD.md` for a `docs/builder/` target, `../spec-NNN-….md` for a `docs/SPECS/` sibling, and a bare filename for an `appx/` sibling; the spec uses `appx/spec-005-…-rationale.md`. Re-checked against the live tree rather than R1's reading, since a concurrent session moves specs.
- **Every anchor-bearing target slug-checked against the target file's real headings:** `#non-goals`, `#one-model-one-type-alpha-constraint`, `#consumer-override-semantics-deferred-to-a-future-spec` (rationale → post-move spec) and all 7 `docs/GLOSSARY.md` anchors — **all resolve**. Duplicate heading slugs: **0** in the spec (12 headings), **0** in the rationale (8 headings). Both counts re-measured here, and both match the move report's re-measured figures.
- **Format hygiene:** `grep -nE '[a-zA-Z_/]+\.(py|md|csv):[0-9]+'` over both files → no match (rule 27 preserved). No inline `](path)` link outside in-page anchors in either file. `grep -c '^```'` → **0** in both, and 0 at HEAD — the "no fenced blocks to dispose of" claim holds.
- **Byte/line counts independently re-measured:** spec 13,346 B / 154 lines at HEAD → 11,002 B / 132 lines now (**-2,344 B, -17.6%**); rationale 19,056 B / 275 lines. `git diff --stat` → `5 insertions(+), 27 deletions(-)`. Every figure in `### Byte count (required report)` reproduces.
- **The archive is untouched and no version string moved.** The spec stays at its already-archived `docs/SPECS/` path, the rationale was written directly to `docs/SPECS/appx/` (never to `docs/` and moved), and no `0.0.3` / `0.0.14` / card-id string was altered.

### What looks solid

- **The move is a move.** Verified in both directions and independently: 17 of 18 removed lines are present at HEAD, absent from the post-move spec, and present in the rationale; the reverse direction is 0 non-scaffold shared shingles. The one exception is the Medium above.
- **Quote fidelity.** Every moved line matches HEAD character-for-character modulo line-wrapping whitespace — including the `->` arrows in the four `Meta.primary` rules and the parenthesised sub-question text, which are the easiest things to smooth while re-typing.
- **Every external factual claim in the rationale checks out against source**, and I checked all of them: `types/finalizer.py::_audit_primary_ambiguity` exists (finalizer.py:131); `registry.py`'s `get` docstring does say callers cannot distinguish the ambiguous case from "no type registered" without `types_for(model)` (registry.py:348, corroborated by spec-018:469); spec-018 Decision 5's first table row is the single-type backward-compat allowance and its last row puts ambiguity-by-omission at `finalize_django_types`, exactly as the entry says; Decision 6 does remove the eager-bind shortcut in `_build_annotations`; Decision 9 is origin-type propagation; spec-019's `## Problem statement` does contain "describes a pre-foundation-slice state" and its Decision 5 is "Test placement and the skipped test's fate"; `KANBAN.md:4030` carries "No new public API. No `Meta.field_overrides = {...}`-style key." verbatim; `consumer_annotated_scalar_fields` (base.py:574) is unioned into `consumer_authored_fields` (base.py:613-616) which short-circuits the per-field loop (base.py:1750, 1783); `tests/types/test_base.py::test_has_custom_get_queryset_inherits_through_intermediate_base` exists (test_base.py:1380); `registry.clear()` still appears 15 / 2 / 6 times in `test_converters.py` / `test_resolvers.py` / `test_base.py`, matching the drift table's D15 counts.
- **Nothing load-bearing was over-cut, and I looked for it as the primary job.** Both `**Future direction.**` blocks are predicted design for mechanisms other specs now own, so no builder loses an instruction. The three carve-out keeps are each correct and each would have caused a real defect if moved: the `### One-model-one-type` opening paragraph's reason clause is attached to a live (if falsified) rule *and* is D2's anchor for R2; the merge-code-can-stay clause is a standing "do not rip this out" instruction and a builder never reads the rationale; `## Problem statement` is the goal statement `worker-1.md` puts on the STAYS list verbatim.
- **No dangling reference survives the cut.** Swept the post-move spec for referential deixis (`above|below|the three|these|those|as noted|earlier|previously|the future spec|Future direction|first-registered`): the only hits are the two new pointer sentences, `## Problem statement` item 1, line 79's self-contained "both of these are true", and `## References`. `Meta.primary` is still named in surviving prose (`## Current state`, `## Non-goals`, `## Coordination …`), so the `### One-model-one-type` decision's "temporary alpha constraint" still has a visible successor. The spec reads as a standalone document.
- **Nothing deliberative was under-cut.** Walked all 12 surviving sections. What remains that is not plainly normative is exactly the set R1 named and left for R2: `## Current state`'s status lists, the `### Consumer override semantics` diagnosis (the Low above), and the falsified rosters in `### Accepted vs deferred Meta keys`. All are false *facts*, not argument, and correcting a fact is R2's contract, not R1's.
- **The competitive-comparison judgement is within an already-decided scope and needs no fresh escalation.** Worker 1 flagged it as attackable. I read the cited decision at `docs/builder/build-004-optimizer_beyond-0_0_3.md:192-208` (read-only; that file is baseline-dirty and out of scope): it decides that **per-topic competitive argument moves, while a problem statement's statement of the competitor gap stays when the comparison is the document's subject**, and states explicitly that it "generalizes as a reading of rules the repository already has, not as a new rule". R1's split is that decision applied literally — the `### One-model-one-type` friction paragraph is per-topic argument for lifting a constraint, and it moved; `## Problem statement` item 1's three-library sentence is the only surviving statement of why the constraint was flagged, and it stayed byte-for-byte. Recorded here so the question is not re-fought at R2.
- **Scope discipline held, and all four hand-off claims verify.** The diff is cuts, two pointers, one companion paragraph, and one link definition — no falsified contract statement was rewritten. **D15 is fully discharged**: the `registry.clear()`-workaround sentence left the spec with the friction paragraph (`grep registry.clear` over the post-move spec → no hit), and the rationale records both the original claim and its inversion at `0.0.6`. **D3 / D4 / D8 are half-discharged exactly as claimed**: the quoted prediction text is gone from the spec in all three cases, and what remains for R2 is every *other* sentence the two shipped mechanisms falsify (`## Non-goals`' "future", `## Current state`, `## References`). Recording a prediction's fate in the rationale changes no spec sentence and is what the build plan's `### What R1 inherits` asks for; it does not pre-empt R2.
- **The rationale is keyed as `BUILD.md` requires, entry by entry.** All three entries name their spec section by heading and carry a resolving anchor (the `## Open questions` entry cannot anchor a removed heading and says so, anchoring `## Non-goals` instead, with the exception declared up front in `## How to read this file`). Each carries rejected alternatives with the reason each lost (first-registered-wins; the three candidate approaches; spec-019 Decision 5's unskip-and-keep), the later spec that caused each change (spec-018, spec-019, spec-010/`DONE-010-0.0.4`), and a closing `*Claims the section no longer makes.*`. `## Standing note` is cross-cutting synthesis rather than an unkeyed entry, and both blocks it compares are keyed above it.
- **`### Two copies caught by measurement` is the most valuable paragraph in the move report.** Both caught quotes were correct, attributed, and illustrative — the class of defect that reading cannot find. The self-report is what makes the 0-overlap figure credible rather than convenient.

### Temp test verification

None. No temp test was created under `docs/builder/temp-tests/r1/`: the item's whole diff is three Markdown files, every claim in it is verifiable by measurement over those files plus a read-only HEAD copy, and no runtime behavior is asserted anywhere in the pass. `scripts/review_inspect.py` was **not** run and the skip is recorded here with its reason: `BUILD.md` `### When to run the helper during build` conditions every Worker 3 trigger on a `.py` file being added or touched, and this item touches none.

### Notes for Worker 1 (spec reconciliation)

1. **Baseline growth, mid-pass, reported and not touched.** Between this pass's first and last `git status --short` the baseline grew twice. First wave: `M KANBAN.md` (mtime 09:50:42), `M KANBAN.html` (09:50:45), `M examples/fakeshop/db.sqlite3` (09:50:22), `?? docs/SPECS/spec-063-structural_templates-0_1_6.md` (09:44:04) — a concurrent session's card-wrap, a DB write followed by both kanban regenerates. Second wave, by the close of the pass: `M BACKLOG.md`, `M multi-root-schedule-graph-reproduction.md`, and `M` on `spec-041-channels_router-0_0_14.md`, `spec-042-debug_toolbar-0_0_14.md`, `spec-043-test_client-0_0_14.md`, `spec-052-beta_release-0_1_0.md`. None is in this cycle's writable set. The only DB-touching command in this pass was `import_spec_terms --check`, which cannot regenerate `KANBAN.md` / `KANBAN.html`, so those renders are not this cycle's. **Nothing was reverted or `git checkout`-ed** (`AGENTS.md` rule 34). Worker 0 should append all of it to the plan's `## Baseline-dirty out-of-scope files`; the plan's own "expect this list to grow" note anticipated it. Two consequences: the build plan's `## Concurrent-writable tracked binary / generated files` premise that "all four are clean" is **no longer true**, so R3 re-verifies the DB / KANBAN / GLOSSARY state itself and compares `iterdump()` semantics rather than bytes; and the final gate's whole-tree commands will see six dirty sibling specs this cycle never wrote, which the plan's recorded baseline exception already covers. This item's own two files were re-verified byte-identical at the close of the pass (11,002 / 19,056 bytes; `git diff --stat` still `5 insertions(+), 27 deletions(-)`), so nothing reviewed above was overwritten underneath the review.
2. **`metaprimary` remains the cycle's top anchor risk, and I confirm it independently.** One carrier, in `## Current state`'s final paragraph, inside R2's write set, in prose D1 / D2 / D17 all bear on. R2 re-sites the link in the same edit that rewrites the paragraph — never by keeping narration alive to hold a link, never by editing the CSV — and quotes `check_spec_glossary.py` after every edit. Four more anchors (`configurationerror`, `djangotype`, `metainterfaces`, and by extension `metafields` / `metaexclude`) are also single-carrier; only `metamodel` and the item-3 pair sit in prose HEAD does not falsify.
3. **The Medium above is R1's to fix, not R2's**, and per Deviation 2's corollary the apply-changes pass is Worker 1's, returning `Status: planned`. It is one added quotation or one corrected provenance bullet plus a re-run of the line-granularity check. Do not fold it into R2 — the rationale file is append-only across the rest of the cycle, and leaving a false "nothing was deleted" statement in it through R2 makes the record harder to trust exactly where R2 will be adding to it.
4. **No contract-level finding was surfaced by this pass**, so nothing is escalated to the maintainer. The one question that looked contract-level — whether the friction paragraph's competitive comparison needed its own escalation — resolves against the already-recorded spec-004 maintainer decision, whose scope clause covers it explicitly (see `### What looks solid`). It is decided, not open.
5. **Method note for R2's own verification.** The 17-span check passed while missing a cut sentence. When R2 verifies its own rewrite, drive the check off `git diff -U0` line by line rather than off spans chosen by the worker that made the edits; the span set is written by the same reasoning that made the cut, so it inherits its blind spots.

### Review outcome

`revision-needed`. One Medium (a cut sentence in neither file, plus the two record statements it falsifies) and two Lows (an incomplete "deliberately left" enumeration; two malformed illustrative link uses in this artifact). None of the three is a judgement disagreement — the move's editorial calls are all sound, and every one I could attack mechanically held. Routing per Deviation 2: back to **Worker 1**, not Worker 2.

---

## Move report (Worker 1, pass 2) — apply-changes

Fresh invocation with no memory of the move pass; the artifact, the working-tree diff, and a read-only HEAD copy are the whole record. `HEAD` re-derived as `346d67312599c0536980969caa39085ab3885ae8` — unchanged since the review closed. The HEAD reference was taken with `git show HEAD:docs/SPECS/spec-005-django_type_contract-0_0_3.md > <scratchpad outside the repo>/spec-005-HEAD.md`; no `git stash` / `checkout` / `restore` / `worktree`, no branch, no commit, no `pytest`, no coverage-shaped flag, no source / test / example / sibling-spec / CSV / DB write.

### Findings disposition

**Medium — a cut sentence in neither file. CLOSED, by the reviewer's preferred remedy, and I reach it independently.**

A prescribed fix is a hypothesis (`BUILD.md` `## Review rounds`), so the two options were re-decided here rather than inherited. The choice was between (a) quoting the lead-in in the rationale, and (b) recording it as a deliberate deletion and correcting the "Nothing was deleted outright" bullet. **(a) wins, and (b) is not merely weaker but wrong**, for a reason the review states as a preference and which is actually dispositive: `worker-1.md` rule 2 licenses deleting only prose *the current decisions have falsified*, and this pass's own recorded reasoning — re-verified below — is that nothing in spec-005 is falsified by spec-005. Option (b) would have made the record honest about an act rule 2 does not permit; option (a) makes the act permitted. Recording a deletion is a way of describing a rule violation accurately, not a way of resolving it.

The fix is in the `### One-model-one-type` entry's sub-question block, which now quotes the lead-in verbatim before the three bullets it introduces. Two consequential secondary edits followed from it:

- The lead-in's content is on-thesis and the entry now says so: the spec predicted the mechanism would get **its own spec**, guessed the slug `spec-meta_primary.md`, and it shipped as `spec-018-meta_primary-0_0_6.md`. The review is right that this strengthens the entry's own thesis and `## Standing note`'s argument that a prediction stated as a required outcome survives.
- **The point is recorded once, not twice.** It was tempting to also add it to the `*How the prediction fared*` paragraph's "right on every point" list, where the review noticed its absence. Deliberately not done: that list and the sub-question block sit four paragraphs apart in one entry, and the build plan's own DRY rule is that a fact told twice goes stale in one of the two. The telling lives where the sentence itself is recorded.
- `## Provenance of this record`'s *Moved* bullet now enumerates the lead-in explicitly ("its four rules, the lead-in naming the future spec, the three sub-questions, and the closing first-registered-wins rejection"), so the bullet no longer stands on the reader trusting that "the whole block" covered it. **"Nothing was deleted outright by this pass" is now true as written**, and it carries a clause saying the claim is measured at line granularity rather than asserted — which is the durable half of the root cause.

**Low — the "deliberately left in the spec" list was not exhaustive. CLOSED.** The list now names four passages, says outright that it is exhaustive, and adds `### Consumer override semantics`'s first two paragraphs (the `@strawberry.type`-rewrites-`cls.__annotations__` diagnosis and the skipped-test sentence) **with the reason they were left, which is a different reason from the other three**: they are falsified *facts*, not deliberation, so correcting them is R2's contract. Accepted without reservation — the review's diagnosis that "the list reads as exhaustive and is not" is exactly the defect, and a reader could not otherwise tell whether the surviving diagnosis was weighed or overlooked. Verified again this pass that the test is gone: `grep -rn test_consumer_annotation_overrides_synthesized tests/ examples/ django_strawberry_framework/` → no match (exit 1).

**Low — two malformed illustrative reference-link uses in this artifact. CLOSED, by rewording rather than by escaping.** The review offered both. Rewording wins: an escaped code span would still put a live-looking `glossary-` reference id in a file that defines none, and the more important of the two sites (hand-off item 1, which R2 acts on) reads better as an instruction than as a syntax demonstration. Both now name the link by its anchor and its reference-style shape without reproducing the bracket syntax. Measured after: this artifact carries **0 defs / 0 distinct uses** of reference-style links, down from 0 defs / 2 undefined uses. (Worker 3's own review paragraph describing the defect still contains the syntax, correctly escaped inside double-backtick spans; prior entries are never edited, and a double-backtick span is not a reference use.)

### The verification method the findings actually indicted, re-run at line granularity

The review's root-cause call is correct and is the part of this pass worth reading: proving "17 hand-chosen verbatim spans, 17/17 pass" **cannot** detect a sentence nobody made into a span, because the population was sampled by the same reasoning that made the cut. The replacement drives the check off the diff itself, so the population is established rather than chosen:

```shell
git diff -U0 -- docs/SPECS/spec-005-django_type_contract-0_0_3.md
# -> 18 removed non-empty lines; each whitespace-normalized and tested three ways:
#    present at HEAD / absent from the post-move spec / present in the rationale
```

Normalization strips quotation marks and leading list markers (`- `, `1. `) and the `**Future direction.**` label prefix, because the rationale legitimately re-frames a moved line as a quotation inside a bullet — those are re-framings, not losses, and a naive substring test reports them as misses.

- **Before this pass's edit: 18 removed lines, 17 accounted for, 1 not** — the lead-in sentence beginning "This work belongs to its own future spec", quoted in full in the review above: present at HEAD, absent from the spec, absent from the rationale. The review's finding reproduces exactly.
- **After: 18 of 18 accounted for.** One line still reports a raw miss and it is a **false positive, disambiguated rather than waved through**: `## Open questions` fails only the *absent-from-the-spec* leg, because the new companion paragraph at spec line 3 names the removed section by name. The heading itself is gone — `grep -n '^## Open questions' docs/SPECS/spec-005-django_type_contract-0_0_3.md` → no match (exit 1); the only occurrence of the string is the pointer sentence, which rule 1 requires. The review reached the same disambiguation independently.

The 0-non-scaffold shingle measurement stays in the record and stays useful, but the review's characterisation of it is right and belongs on the permanent record: **it proves nothing was copied, never that everything was moved.** The two checks are opposite directions and neither substitutes for the other.

### A third partial overlap, surfaced by a stricter tokenizer than either prior pass used

Recorded because it corrects a number in this artifact rather than confirming one, and because "measure as you write it" is what the earlier passes got right.

Re-running the cut-not-copy intersection with punctuation stripped **before** shingling (the move pass and the review both left it in) gives **17 total 8-word shingles, 14 scaffold, 3 non-scaffold** between the post-move spec and the rationale, not 0:

- `### Consumer override semantics deferred to a future` and `Consumer override semantics deferred to a future spec` — the section heading the keying rule *requires* the rationale to reproduce. Worker 3 surfaced this pair at 6-word width and judged it required; a comma-stripping tokenizer surfaces it at 8. Not a copy.
- `strawberry.type rewrites cls.__annotations__ after the merge so the` — a pre-existing partial overlap between the rationale's condensed quotation of the override diagnosis ("…after the merge**,** so the consumer's annotation loses") and `## Problem statement` item 2 ("…after the merge so the override doesn't actually hold"). The comma is the only reason both prior passes measured 0.

**Judged acceptable and deliberately kept**, which is the opposite call from the two copies the move pass deleted, and the distinction is the point: those two quoted sentences that stay in the spec **as current contract**. This one quotes a claim `BUILD.md` `## Spec rationale extraction` positively requires the rationale to carry — "any claim the decision once made and may no longer make" — and the surrounding paragraph is unreadable without it, since its whole argument is that all three candidate approaches answered *this* diagnosis. It is also a condensation of two spec sentences rather than a verbatim lift of either.

The correct reading of the number is therefore: **0 moved blocks exist in both files; one falsified claim is quoted in both, by design.** Consequence for R2 in the hand-offs below.

### Validation run (re-run in full this pass; nothing carried over)

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-005-django_type_contract-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` **exit 0**. Character-identical to the pre-flight step-6 baseline and to both prior passes.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-005-django_type_contract-0_0_3.md docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md docs/builder/bld-005-r1-rationale_move.md` → **exit 0** on all three. Run over every file this pass touched plus the untouched spec.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0**, re-run rather than inherited because the DB was already dirty from a concurrent card-wrap when this pass started.
- **Line-granularity move check:** 18/18 removed non-empty lines accounted for; the one raw miss disambiguated above.
- **Reference integrity, all three files.** Spec **8 defs / 8 distinct uses**, 0 undefined, 0 unused. Rationale **8 / 8**, 0 undefined, 0 unused — the new `spec-018` use in the sub-question block resolves against the definition already present, so no definition was added. This artifact **0 / 0** (was 0 defs / 2 undefined uses). Every non-anchor definition target disk-checked from its own file's directory: **16/16 exist**.
- **Anchor-bearing targets slug-checked** against the post-move spec's real headings: `#non-goals`, `#one-model-one-type-alpha-constraint`, `#consumer-override-semantics-deferred-to-a-future-spec` — all resolve. Duplicate heading slugs: **0** in the spec (12 headings), **0** in the rationale (8 headings).
- `grep -c '^```'` → spec **0**, rationale **0**. Unchanged; this pass added no fenced block to either.
- `grep -nE '[a-zA-Z_/]+\.(py|md|csv):[0-9]+'` over the spec and the rationale → **no match** (exit 1). Rule 27 still preserved in both durable files.
- `grep -P '\]\((?!#|https?:)'` over the spec and the rationale → **no match** (exit 1). No inline `](path)` link in either.
- `git status --short` adds nothing beyond the recorded baseline; `docs/GLOSSARY.md` is still clean, and `KANBAN.md` / `KANBAN.html` / `examples/fakeshop/db.sqlite3` carry only the concurrent card-wrap's churn that was already dirty at the start of this pass. **One further baseline growth to report, untouched:** `docs/SPECS/spec-063-structural_templates-0_1_6-terms.csv` (`??`) has appeared alongside the already-recorded `spec-063` spec — the same concurrent `NEXT.md` flow. Nothing reverted (`AGENTS.md` rule 34).
- **Not swept into a concurrent commit.** `git log --oneline -1 -- docs/SPECS/spec-005-django_type_contract-0_0_3.md` → `ff65666d docs: normalize review citations to their durable records`, which predates this cycle; `git log -- ` over the rationale and this artifact is empty (never committed). `git status` alone was not used for this.

### The 7-anchor constraint — re-measured after the edit

**This pass did not touch the spec**, which is the strongest form the guarantee can take: `git diff --stat` over the spec is still `5 insertions(+), 27 deletions(-)`, byte-identical to the move pass's output at 11,002 bytes / 132 lines. The anchors were re-measured anyway rather than argued from the absence of a diff, because the obligation names a measurement:

| Anchor | uses | defs | carrier | change this pass |
|---|---|---|---|---|
| `configurationerror` | 1 | 1 | `## Problem statement` item 1 | none |
| `djangotype` | 1 | 1 | `## Problem statement` item 1 | none |
| `metafields` | 1 | 1 | `## Problem statement` item 3 | none |
| `metaexclude` | 1 | 1 | `## Problem statement` item 3 | none |
| `metainterfaces` | 1 | 1 | `## Problem statement` item 4 | none |
| `metaprimary` | 1 | 1 | `## Current state` final paragraph | none |
| `metamodel` | 1 | 1 | `### Invalid …` body | none |

All seven stand at exactly 1 use + 1 definition. `metaprimary` remains a single point of failure inside R2's write set; six of seven are single-carrier and four of those sit in prose the drift table marks falsified. Nothing about the risk profile moved.

### Byte count

| | lines | bytes | delta this pass |
|---|---|---|---|
| spec | 132 | 11,002 | **unchanged** |
| rationale | 285 | 20,086 | +10 lines / +1,030 bytes |

The rationale is append-only across the rest of the cycle (`worker-1.md` rule 4), and this pass is a fix to R1's own output rather than a later round's addition, so the growth is inside R1's own scope. The spec's `-17.6%` figure stands untouched.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope `none`.

### Failability proofs

None; this pass introduced no new boundary. It edits two Markdown files and adds no guard, gate, or rejection path.

### Notes for Worker 3

- **The three edits are small and the reasoning is the reviewable part.** The two judgement calls I would attack, in order: (a) whether recording the matched slug **once**, in the sub-question block rather than also in the `*How the prediction fared*` list, leaves the entry's summary paragraph incomplete — I decided the DRY rule wins over locality; (b) whether the third shingle overlap should have been cut rather than kept, since the move pass cut two overlaps that looked similar. My distinction is *what the quoted sentence is* — current contract (cut) versus a claim the spec may no longer make (keep, because `BUILD.md` requires the rationale to carry exactly those).
- **Re-derive the line-granularity check rather than reading its result.** It is three commands and it is the check that found the Medium. Note the normalization it needs (quotes, list markers, the `**Future direction.**` prefix) and the one false positive it produces (`## Open questions`, named by the pointer sentence rule 1 requires).
- The prior pass's `### Validation run` reports **0** non-scaffold shingle overlap; this pass reports **3** at a stricter tokenization, and explains all three. If you re-measure, say which tokenizer you used — the number is not tokenizer-independent, and treating it as if it were is how both prior passes landed on 0.
- The spec was not opened for writing this pass. Any spec-side change you find is not this pass's.

### Notes for Worker 1 (spec reconciliation)

The eight hand-offs recorded by the move pass were re-read against the current files and **all eight remain accurate**; item 1's wording changed only to drop the malformed link syntax, and its instruction is unchanged. Three additions:

9. **A falsified claim is now quoted in both files, and R2 must not "fix" that.** The rationale's `### Consumer override semantics` entry condenses and quotes the override diagnosis in order to explain why all three candidate approaches missed. `## Problem statement` item 2 and `### Consumer override semantics`'s first paragraph state the same diagnosis and are **R2's to correct** (D5). When R2 corrects them, the rationale's quotation stays exactly as it is — it is the record of a claim the spec may no longer make, which is what `BUILD.md` `## Spec rationale extraction` requires the file to carry. Syncing it would delete the record.
10. **`## Provenance of this record`'s "deliberately left" list is now exhaustive at four passages and names the two R2 owns.** If R2's rewrite of `### Consumer override semantics` removes or restates the diagnosis paragraphs, that bullet's fourth item becomes a statement about what R1 left rather than about what the spec currently says — which is correct and needs no edit, but R2 should read it before assuming the rationale needs an append.
11. **Use the line-granularity check on R2's own diff.** It is the method that caught what seventeen hand-chosen spans could not, and R2's diff will be far larger than R1's. Drive it off `git diff -U0`; for R2 the useful legs are *present at HEAD* and *the removal is either restated in the spec or recorded in the rationale*, since R2 legitimately rewrites rather than only cuts.

### Review outcome

Not applicable — this is Worker 1's apply-changes pass. `Status: planned` on return, which Worker 0 reads as "dispatch Worker 3" per Deviation 2's corollary.


---

## Review (Worker 3, pass 2) — re-review

Fresh invocation with no memory of pass 1's review or of the move pass. The artifact, the working-tree diff, and a read-only HEAD copy are the whole record; every number below was re-derived in this pass, including the ones this artifact reports as already re-derived. HEAD reference taken with `git show HEAD:docs/SPECS/spec-005-django_type_contract-0_0_3.md > <scratchpad outside the repo>/spec-005-HEAD.md`. No `git stash` / `checkout` / `restore` / `worktree`, no branch, no commit, no `pytest`, no coverage-shaped flag, no write outside this cycle's set.

**`HEAD` has moved and must not be quoted from this artifact's earlier passes.** It is now `ff03c1372365edcad488ff4671389d88ae145276` ("docs(kanban),docs(specs): card the structural-templates and sidecar-batching foundation"), not `346d6731`. `git merge-base --is-ancestor 346d6731 HEAD` → exit 0, so this is a fast-forward by a concurrent session, and `git diff --name-status 346d6731 HEAD` lists **twelve** paths, **none of them this cycle's**: the concurrent commit swept exactly the baseline-dirty set the plan's `### First growth` section records (`BACKLOG.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`, `multi-root-schedule-graph-reproduction.md`, specs 041 / 042 / 043 / 052 / 053, and the two `spec-063` files). Two consequences checked rather than assumed: `git diff 346d6731 HEAD -- docs/SPECS/spec-005-django_type_contract-0_0_3.md` is **empty**, so every measurement in this artifact taken against the old HEAD is still valid against the new one; and `git log --oneline -1 -- docs/SPECS/spec-005-django_type_contract-0_0_3.md` is still `ff65666d`, with the rationale and this artifact still untracked — **this cycle's work was not swept into the concurrent commit** (checked with `git log` / `git diff --name-status`, never `git status` alone).

### High:

None.

### Medium:

None.

### Low:

None.

### Findings from pass 1 — closure audited in the diff, not in prose

**Medium (a cut sentence in neither file). CLOSED, verified at line granularity by re-derivation.** The fix is present in the diff of the durable file, not merely claimed: the rationale's `### One-model-one-type` entry now opens its sub-question block with the lead-in quoted verbatim — "This work belongs to its own future spec (`spec-meta_primary.md` or similar) which will need to address:" — and follows it with the matched-slug observation. I re-derived the whole check rather than reading its result:

```shell
git diff -U0 -- docs/SPECS/spec-005-django_type_contract-0_0_3.md
# -> 18 removed non-empty lines; each whitespace-normalized and tested three ways
#    (present at HEAD / absent from the post-move spec / present in the rationale),
#    with leading list markers, the `**Future direction.**` label prefix, and
#    quotation marks stripped as normalization variants
```

**18 removed non-empty lines; 17 clean; 1 raw miss — and the raw miss is `## Open questions`, not the lead-in.** The lead-in now passes all three legs. The disambiguation of the remaining raw miss reproduces exactly as pass 2 of the move report states it: `## Open questions` fails only the *absent-from-the-spec* leg, `grep -n '^## Open questions' docs/SPECS/spec-005-django_type_contract-0_0_3.md` → **no match, exit 1**, and `grep -n 'Open questions'` returns **one** line — spec line 3, the companion pointer paragraph that rule 1 requires. So **18/18 accounted**, and the count is one a reader can re-derive rather than one asserted.

The added-side arithmetic checks too: the diff's five insertions are the companion paragraph, its blank line, the two per-section pointers, and the one link definition — nothing else was added under cover of the fix.

**Low (the "deliberately left in the spec" list was not exhaustive). CLOSED.** `## Provenance of this record` now enumerates four passages, says outright that the list is exhaustive, and adds `### Consumer override semantics`'s first two paragraphs **with the reason they were left stated as a different reason from the other three** — falsified facts rather than deliberation, so R2's row. That distinction is the part that makes the addition worth having; without it the fourth entry would read as a fourth carve-out keep. The supporting fact re-verified here: `grep -rn test_consumer_annotation_overrides_synthesized tests/ examples/ django_strawberry_framework/` → **no match, exit 1**.

**Low (two malformed illustrative reference-link uses). CLOSED, by rewording.** Both sites now name the anchor and the link's reference-style shape without reproducing bracket syntax. Measured rather than eyeballed: stripping double-backtick spans first and then single-backtick spans, this artifact carries **0 reference-link definitions and 0 distinct reference uses**; the only surviving raw `[glossary-` occurrences are inside code spans at `:141` and `:269` and inside pass 1's own review paragraph at `:248`, which is correct — the review paragraph is a prior entry and prior entries are not edited. I confirm it was **not** edited: it still describes the defect in the double-backtick form pass 1 wrote it in.

One consequence worth stating so it is not later read as drift: the rewording shifted line numbers inside the pass-1 move report, so pass 1's citations `:143` / `:186` now point at `:141` / `:186`. Raw `path:NN` refs are licensed in a per-cycle scratchpad and the next cycle regenerates it; no action.

### The new self-reported finding: the 3 non-scaffold overlaps, re-derived and judged independently

**The 3 reproduce exactly, and only under one tokenizer at one width.** I ran the intersection at three tokenizations × two widths over the two files' **bodies** (everything before `<!-- LINK DEFINITIONS -->`, which removes the scaffold by construction rather than by a filter that has to be trusted):

| tokenizer | n=8 | n=6 |
|---|---|---|
| punctuation kept (passes 1 and the move pass) | **0** | 2 |
| punctuation stripped, `.` and `#` retained (move report pass 2) | **3** | 12 |
| punctuation stripped, nothing retained | 4 | 13 |

So the move report's **3** is reproducible and its three members are exactly the ones it names — `### Consumer override semantics deferred to a future`, `Consumer override semantics deferred to a future spec`, and `strawberry.type rewrites cls.__annotations__ after the merge so the`. Its own warning is the right one to carry forward: **the number is not tokenizer-independent, and neither prior pass's `0` was wrong — it was measured with a tokenizer in which a comma is a token.** Reporting the tokenizer alongside the number is what makes the figure auditable, and this pass reports its own above.

**The acceptance argument holds, and I reach it independently rather than inheriting it.** Three separate legs, each checked:

1. **It is not a moved block.** The cut-not-copy invariant governs the text the move relocated. The override diagnosis was never moved — it is one of the four passages `## Provenance of this record` records as deliberately left. At every tokenizer and width above, **zero** shingles trace to any of the five moved blocks. The move report's formulation is precisely right: *0 moved blocks exist in both files; one falsified claim is quoted in both, by design.*
2. **`BUILD.md` positively requires the carry.** `## Spec rationale extraction` requires each entry carry "any claim the decision once made and may no longer make". The three candidate approaches are only legible against the diagnosis they answer — the entry's whole thesis is that a candidate list is only as good as the diagnosis that generated it — so describing the diagnosis without stating it would leave the moved block less useful than it was in the spec.
3. **It is a condensation, not a lift.** Checked against both source sentences: the spec's `## Problem statement` item 2 reads "…after the merge so the override doesn't actually hold", and `### Consumer override semantics` reads "…regenerates `cls.__annotations__` from its own field metadata after the merge, and the consumer-declared annotation loses…". The rationale's "…rewrites `cls.__annotations__` after the merge, so the consumer's annotation loses" is neither verbatim. The staleness risk the move pass cut two quotes over is answered by hand-off 9 rather than left open: when R2 corrects the spec's copies, the rationale's becomes the record, which is what the file is for.

**Where the stated distinction is slightly stronger than its own history, said plainly rather than filed as a finding.** The move report frames the call as *current contract (cut) versus a falsified claim (keep)*, describing both prior cuts as "sentences that stay in the spec as current contract". That is exactly right for the merge-code-can-stay clause and imprecise for the other: the skipped-test promise is a **falsified** promise (D7 — the test is gone) sitting inside a normative Decision block, so under the rule as stated it would have been quotable too. The operative rule that actually explains all three calls is narrower and better: *a quotation of surviving spec prose is licensed when the quotation is itself the record of something whose disposition R2 owns, and is attributed in the rationale as still standing in the spec.* No durable file changes either way — describing rather than quoting loses nothing, and both cut sites read fine — so this is recorded, not charged.

**A fourth overlap of the same class exists and is not in the move report's accounting.** At 6-word width with punctuation stripped, `must update this contract spec accordingly` appears in both files: the rationale's `## Open questions` entry quotes that clause of `## Coordination …`'s instruction, which is still in the spec (spec:94) and is D18 — explicitly R2's decision. Same class, same justification, and the rationale already attributes it ("That sentence is still in the spec and is item R2's to decide on"), so it needs no edit. It is below the width the move report measured at, so its absence is not a false count. It matters for one reason only, carried to `### Notes for Worker 1` below: hand-off 9's instruction is written in the singular and names one quotation.

### The fix disturbed nothing — both halves verified

- **The spec was not opened for writing.** `git diff --stat` → `1 file changed, 5 insertions(+), 27 deletions(-)`; the file measures **11,002 bytes / 132 lines**, byte-identical to the move pass's figure. The `-2,344 B / -17.6%` cut stands.
- **All seven anchors stand at exactly 1 body use + 1 definition**, measured as reference-style uses only (`]\[glossary-<anchor>]` over the body, code spans excluded) at HEAD **and** now:

  | anchor | HEAD body uses | now | defs |
  |---|---|---|---|
  | `configurationerror` / `djangotype` | 1 / 1 | 1 / 1 | 1 / 1 |
  | `metafields` / `metaexclude` | 1 / 1 | 1 / 1 | 1 / 1 |
  | `metainterfaces` / `metaprimary` / `metamodel` | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 |

  Single-carrier for all seven at HEAD too, so the move dropped none — the build plan's `### The 7-anchor constraint` table remains wrong in the three rows the move report names, and Worker 0's appended CORRECTION remains accurate. `metaprimary`'s sole carrier is still `## Current state`'s final paragraph, inside R2's write set.
- **Nothing outside the writable set moved.** `git status --porcelain` scoped to `django_strawberry_framework/`, `tests/`, `examples/`, `CHANGELOG.md`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, and the spec-005 terms CSV returns **nothing**. The rationale grew to **20,086 bytes / 285 lines** (+1,030 B / +10 lines), consistent with the three recorded edits and with nothing else.

### The plan's checklist — walked

Every box in `### Dispatched findings checklist` is `- [x]` and every one has a matching artifact contract; I re-verified the four that a re-review can actually falsify: cut-not-copy (above), the 7-anchor / `check_spec_glossary` box (re-run below), the reference-style / 10-group-header box (re-derived below), and rule 27 (`grep -nE '[a-zA-Z_/]+\.(py|md|csv):[0-9]+'` over both durable files → **no match, exit 1**). The last box — "R2's scope was not pre-empted" — is audited under `### Notes for Worker 1` below.

One box carries a parenthetical that pass 2 of the move report has since superseded: box 1 reads "(measured: 0 non-scaffold shared shingles)". The box's **contract** landed and the tick is correct; only the parenthetical figure is tokenizer-conditional. Routed to Worker 1's final verification rather than charged, since Worker 1 audits its own ticks there.

### DRY findings

- **No consolidation recommended; no existence challenge raised.** This item writes Markdown, adds no helper, registry, indirection layer, or constant, and deletes none, so the challenge has no target. The sibling-boilerplate measurement pass 1 recorded (≈197 shingles with the `spec-001` rationale, ≈99 with `spec-004`'s, **0** substantive after filtering) is unchanged by this pass — the three edits add no front matter — and is not re-derived here for that reason.
- **The one live DRY judgement in this pass is the move report's own**, and it is right: the matched-slug point was recorded **once**, in the sub-question block where the sentence itself lives, and deliberately not also in the `*How the prediction fared*` list four paragraphs above. The build plan's own rule (`DRY rule`, plan:7) is that a fact told twice goes stale in one of the two; the entry is one screen long and the two sites are within it, so locality buys nothing that would pay for a second copy R2 could falsify half of.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are unchanged. The build plan's `## Build-wide context flags` declares the whole cycle source-free; this pass wrote three Markdown files and honoured it.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

The item touches `docs/SPECS/` and its `appx/` companion, so this applies. Every command below was run in this pass.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-005-django_type_contract-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` **exit 0**. Character-identical to the pre-flight step-6 baseline.
- `uv run python scripts/check_trailing_commas.py --check <file>`, run on each of the three files separately: spec **exit 0**, rationale **exit 0**, this artifact **exit 0**.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0** — re-run rather than inherited, because a concurrent commit has landed on the DB since the last reading. The card-wrap chain the 7-anchor constraint protects is intact.
- **Reference integrity, all three files, re-derived with code spans stripped:** spec **8 defs / 8 distinct uses**, rationale **8 / 8**, artifact **0 / 0**; **0 undefined and 0 unused in all three**. All 16 definition targets in the two durable files resolve on disk from their own file's directory, checked against the live tree. Depth convention correct in both directions (`../../builder/BUILD.md`, `../spec-NNN-….md`, bare `spec-001-…-rationale.md`, and `appx/…` from the spec side).
- **Anchor-bearing targets slug-checked against the target file's real headings:** the rationale's `#non-goals`, `#one-model-one-type-alpha-constraint`, and `#consumer-override-semantics-deferred-to-a-future-spec` all resolve against the post-move spec's 12 headings, and all 7 `docs/GLOSSARY.md` anchors resolve against that file's real headings. **Duplicate heading slugs: 0** in the spec (12 headings) and 0 in the rationale (8 headings) — re-derived by slugging, not counted from memory.
- **Format hygiene:** `grep -nE '[a-zA-Z_/]+\.(py|md|csv):[0-9]+'` over both durable files → no match (exit 1); `grep -P '\]\((?!#|https?:)'` over both → no match (exit 1); `grep -c '^```'` → **0** in both, and 0 at HEAD.
- **No archival, version, or card-id movement.** The spec stays at its archived `docs/SPECS/` path, the rationale sits at `docs/SPECS/appx/`, and no `0.0.3` / `0.0.14` / `DONE-005` string was altered. `### Accepted vs deferred Meta keys (shipped in 0.0.3)` is byte-identical to HEAD, so the inbound title-level dependency at `docs/SPECS/spec-006-public_surface-0_0_3.md:108` is intact — verified against the sibling, which this cycle did not open.

### What looks solid

- **The Medium's fix is the right one of the two the review offered, for the reason the apply pass gives.** Recording the cut as a deliberate deletion would have made the record accurate about an act `worker-1.md` rule 2 does not license — rule 2 deletes prose *the current decisions have falsified*, and this spec is internally consistent. Quoting the lead-in makes the act permitted rather than merely disclosed. That is a real re-decision, not an inherited preference, and it is the correct one.
- **The durable half of the fix is the method, and it landed in the file that keeps it.** `## Provenance of this record`'s "Nothing was deleted outright by this pass" now carries the clause saying the claim is measured at line granularity rather than asserted — so the next reader of the rationale learns the check as well as the result, and the `*Moved*` bullet now enumerates the block's parts instead of resting on "the whole block".
- **The self-report is the most valuable thing in pass 2.** The third overlap corrects a number this artifact already carried, was found by tightening the pass's own tokenizer rather than by anything the review asked for, and was reported with its judgement attached instead of quietly re-measured back to 0. `BUILD.md` `## Claims are proven mechanically` warns that a stated count propagates silently; a builder that re-measures its own accepted figure and reports the disagreement is the behaviour that rule wants.
- **Quote fidelity of the new material.** The lead-in matches HEAD character-for-character modulo line-wrapping whitespace, including the parenthesised `` `spec-meta_primary.md` `` slug and the trailing colon; the surrounding claim (that it shipped as `spec-018-meta_primary-0_0_6.md`) resolves — the file exists at the path the rationale's `[spec-018]` definition names.
- **No pre-emption of R2, checked against the spec rather than against the claim.** The spec is byte-unchanged this pass, so no falsified contract statement was rewritten. The three edits are all inside the rationale and all record rather than correct.
- **The `## Open questions` false positive is genuinely a false positive**, and the pointer sentence that causes it is required rather than incidental: rule 1 asks each section cut from to keep a pointer, and a removed section has no surviving heading to hang one on, so the companion paragraph naming it is the only pointer that can exist.

### Temp test verification

None. No temp test was created under `docs/builder/temp-tests/r1/`: the pass's whole diff is Markdown, every claim in it is verifiable by measurement over those files plus a read-only HEAD copy, and no runtime behavior is asserted anywhere. `scripts/review_inspect.py` was **not** run, and the skip is recorded with its reason: `BUILD.md` `### When to run the helper during build` conditions every Worker 3 trigger on a `.py` file being added or touched, and this item touches none. No failability proof is owed — `### What needs a proof, and what does not` scopes the obligation to new boundaries, guards, gates, and rejection paths, and this pass introduces none; the artifact's `### Failability proofs` heading is present and correctly filled.

### Notes for Worker 1 (spec reconciliation)

1. **Hand-offs 1-8 re-verified against the current spec, and all eight still hold.** Checked individually rather than in aggregate: `metaprimary`'s sole carrier is spec:31 (`## Current state` final paragraph); `configurationerror` / `djangotype` are sole-carried by item 1 (spec:9), `metafields` / `metaexclude` by item 3 (spec:11), `metainterfaces` by item 4 (spec:12), `metamodel` by the `### Invalid …` body (spec:67); `grep -n registry.clear` over the post-move spec → no match, so D15 is discharged as claimed; `## Non-goals` still carries both "future" words (spec:43) and `## Coordination …`'s "must update this contract spec accordingly" is untouched (spec:94); `grep -n 'Current surface' docs/README.md` → **no match, exit 1**, so D6's first leg holds; both `**Decision for 0.0.3.**` blocks (spec:51, spec:61) sit directly above their pointers (spec:53, spec:63), intact.
2. **Hand-offs 9, 10, and 11 are genuine hand-offs, not R2 work performed early.** None of the three edits the spec, and the spec is byte-unchanged. 9 is an instruction *not* to act (do not sync the rationale's quotation when the spec's copy is corrected); 10 is a statement about what R1 left, explicitly saying it needs no edit; 11 is a verification-method note. All three are the right shape for this section and none anticipates a reconciliation decision.
3. **Hand-off 9 is written in the singular and should be read as a class.** A second surviving spec sentence is quoted in the rationale for the same reason: `## Coordination …`'s "must update this contract spec accordingly" (spec:94) appears verbatim inside the rationale's `## Open questions` entry, which is what makes that entry's bet-that-did-not-pay framing legible. When R2 decides D18 — keep the instruction, or point at `ALLOWED_META_KEYS` as the single source — **the rationale's quotation of it stays exactly as it is**, on hand-off 9's own reasoning: it is then the record of an instruction the spec no longer issues. Recorded here rather than charged as a finding because the durable files need no edit and the rationale already attributes the clause as still standing in the spec; what needed fixing was the hand-off record's coverage, and this note is that record.
4. **The cut-not-copy figure needs its tokenizer quoted wherever it is re-measured.** Later passes (R2's own diff, R3, the final gate) will re-run this intersection over a much larger diff. The table above gives 0, 3, or 4 non-scaffold overlaps at 8 words depending only on whether a comma and a `#` are tokens, so a bare number carries no information. Recommend the body-only form used here — intersect the text **before** `<!-- LINK DEFINITIONS -->` in both files, which removes the scaffold by construction instead of by a filter — and report the tokenizer beside the count.
5. **Box 1 of the plan's checklist carries a superseded parenthetical.** "(measured: 0 non-scaffold shared shingles)" was true under the tokenizer the move pass used and is not under pass 2's. The box's contract landed and the tick is correct; the figure is the thing that moved. Worker 1 audits its own ticks at final verification and can note the supersession there — no re-loop is warranted for it.
6. **Baseline: a concurrent session has COMMITTED, and the plan's baseline-dirty list is now partly historical.** `HEAD` is `ff03c137`, not `346d6731`; the concurrent commit landed the whole `### First growth` set (`BACKLOG.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`, `multi-root-schedule-graph-reproduction.md`, specs 041 / 042 / 043 / 052 / 053, both `spec-063` files), so those paths are now **clean** rather than dirty. Two things are unchanged and still need the maintainer: the four `docs/builder/bld-003-*.md` deletions are **still staged-deleted** and were not restored by that commit, and the spec-004 cycle's five entries are still dirty/untracked. Nothing was reverted or `git checkout`-ed by this pass (`AGENTS.md` rule 34). **Every later pass in this cycle must re-derive `HEAD` rather than quoting `346d6731` from this artifact or from the plan** — the plan's own instruction, now with a concrete instance behind it. Worker 0 should append this event to `## Baseline-dirty out-of-scope files`.
7. **No contract-level finding was surfaced by this pass, so nothing is escalated to the maintainer.** The one question that could have been — whether the rationale may quote a spec sentence that stays — resolves inside `BUILD.md` `## Spec rationale extraction`'s own requirement that the file carry claims the decision may no longer make. It is a reading of an existing rule, not a choice about which contract the package offers.

### Review outcome

`review-accepted`. All three pass-1 findings are closed by changes visible in the durable files, not by prose: the Medium's fix re-derives at line granularity (18 removed non-empty lines, 18/18 accounted, the single raw miss disambiguated by `grep -n '^## Open questions'` exiting 1), and both Lows landed as described. The self-reported third overlap re-derives to exactly 3 under the tokenizer and width the move report names, and its acceptance argument holds on all three legs I could test independently. The spec was not opened, all seven anchors stand at 1 use + 1 definition, `check_spec_glossary` / `check_trailing_commas` / `import_spec_terms` all exit 0, and the three new hand-offs are hand-offs rather than R2 work. Nothing is left open; the notes above are records for Worker 1's final verification, not unresolved findings.


---

## Final verification (Worker 1)

Fresh invocation with no memory of the move pass, the apply-changes pass, or either review. The artifact, the working-tree diff, and a read-only HEAD copy are the whole record; **every number below was re-derived in this pass**, including the ones this artifact reports as already re-derived twice. HEAD reference taken with `git show HEAD:docs/SPECS/spec-005-django_type_contract-0_0_3.md > <scratchpad outside the repo>/spec-005-HEAD.md`. No `git stash` / `checkout` / `restore` / `worktree`, no branch, no commit, no `pytest`, no coverage-shaped flag, no write outside this cycle's set.

**`HEAD` re-derived, not quoted.** It is `ff03c1372365edcad488ff4671389d88ae145276`, unchanged since the re-review closed. `git merge-base --is-ancestor 346d6731 HEAD` → exit 0, and `git diff --stat 346d6731 HEAD -- docs/SPECS/spec-005-django_type_contract-0_0_3.md` is **empty**, so every measurement this artifact records against either commit is valid against both.

### Spec status-line re-verification

Spec lines 1-5 are the H1, the companion-pointer paragraph, and the opening of `## Problem statement`. Spec-005 predates the status/owner/predecessor header convention and carries no such lines, so there is none for this build to have falsified. The falsified status content — `## Current state`'s "0.0.3 shipped (in flight)" — is drift row D1 and sits in R2's declared write set; correcting it here would pre-empt R2 **and** would disturb `metaprimary`'s sole carrier, which hand-off 1 requires be re-sited in the same edit that rewrites the paragraph. Left, deliberately, and already handed off.

### R1's contract, verified end to end rather than accepted

The deliverable is the rationale file existing, keyed to the spec, with the deliberative layer **moved** out. Each leg proven separately:

- **The file exists at the archived-companion path**, written directly there and never to `docs/` and moved: `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`, `??` untracked, **285 lines / 20,086 bytes**.
- **Keyed to the spec.** Three entries plus one cross-cutting standing note. Each entry names its spec section by heading and carries a resolving anchor — `#one-model-one-type-alpha-constraint`, `#consumer-override-semantics-deferred-to-a-future-spec`, and (for the removed `## Open questions`) `#non-goals`, the substitution declared up front in `## How to read this file`. All three slug-checked against the post-move spec's **12** real headings with `scripts/check_spec_glossary.py::github_anchor`: **all resolve**. Duplicate heading slugs: **0** in the spec, **0** in the rationale.
- **Moved, not copied — proven in both directions.** Forward, at line granularity off `git diff -U0` (never off hand-chosen spans): **18 removed non-empty lines, 17 clean, 1 raw miss**, the miss being `## Open questions`, which fails only the *absent-from-the-spec* leg. Disambiguated: `grep -n '^## Open questions'` → **no match, exit 1**; `grep -n 'Open questions'` returns **one** line, spec:3, the companion pointer rule 1 requires. **18/18 accounted.** Reverse, by shingle intersection over both file bodies: no moved block appears in the spec at all, which the forward check establishes directly rather than by sampling.
- **The added side is pointers only.** The diff's five insertions are the companion paragraph, its blank line, the two per-section pointers (spec:53, spec:63), and the one `[spec-005-rationale]` definition. Nothing else rode in.
- **Rule 1 discharged for every section that lost text.** The deletion hunks touch exactly four regions (`@@ -49,2`, `@@ -53,14`, `@@ -76,7`, `@@ -115,4`): `### One-model-one-type`, `### Consumer override semantics`, and `## Open questions`. The first two carry per-section pointers; the third has no surviving heading to hang one on and is named in the companion paragraph instead. No other spec region lost a byte, so no section is missing a pointer it owed.
- **Byte count, re-measured.** Spec **13,346 B / 154 lines** at HEAD → **11,002 B / 132 lines** now (**-2,344 B, -17.6%**); `git diff --stat` → `5 insertions(+), 27 deletions(-)`. Fences, counted with `grep -c` against a start-of-line three-backtick anchor: **0** at HEAD, **0** in the spec, **0** in the rationale.

### Gates re-run and quoted

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-005-django_type_contract-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` **exit 0**. Character-identical to the plan's pre-flight step-6 baseline.
- `uv run python scripts/check_trailing_commas.py --check <file>`, run on each of the three files separately: spec **exit 0**, rationale **exit 0**, this artifact **exit 0**.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0** — re-run rather than inherited. The card-wrap chain the 7-anchor constraint protects is intact.
- **The 7 anchors, re-measured** as reference-style body uses only (`]\[glossary-<anchor>]` over the text before `<!-- LINK DEFINITIONS -->`; a plain code span is not a carrier), with each carrier's line located rather than asserted:

  | anchor | uses | defs | carrier |
  |---|---|---|---|
  | `configurationerror` | 1 | 1 | spec:9 (`## Problem statement` item 1) |
  | `djangotype` | 1 | 1 | spec:9 (`## Problem statement` item 1) |
  | `metafields` | 1 | 1 | spec:11 (`## Problem statement` item 3) |
  | `metaexclude` | 1 | 1 | spec:11 (`## Problem statement` item 3) |
  | `metainterfaces` | 1 | 1 | spec:12 (`## Problem statement` item 4) |
  | `metaprimary` | 1 | 1 | spec:31 (`## Current state` final paragraph) |
  | `metamodel` | 1 | 1 | spec:67 (`### Invalid …` body) |

  All seven at exactly 1 use + 1 definition, carriers matching both prior passes. **The build plan's `### The 7-anchor constraint` table remains wrong in the three rows the move report names**, and Worker 0's appended CORRECTION remains accurate. `metaprimary` is still a single point of failure entirely inside R2's write set.
- **Reference integrity, all three files, code spans stripped:** spec **8 defs / 8 distinct uses**, rationale **8 / 8**, this artifact **0 / 0**; **0 undefined and 0 unused in all three**. All **16** definition targets in the two durable files resolve on disk from their own file's directory, checked against the live tree.
- **Format hygiene:** `grep -nE '[a-zA-Z_/]+\.(py|md|csv):[0-9]+'` over both durable files → no match (exit 1, rule 27 preserved); `grep -P '\]\((?!#|https?:)'` over both → no match (exit 1). All three files carry `<!-- LINK DEFINITIONS -->` and the 10 canonical group headers in canonical order.
- **Focused tests:** none. The plan's `### Test additions / updates` records that R1 adds no test and changes no code path, and `AGENTS.md` rule 15 forbids an unasked `pytest` run. No `--cov*` flag in any form, in any pass of this item.
- **Staged-anchor sweep** (`grep -rEn 'TODO\(spec-005|TODO-(ALPHA|BETA|STABLE)-005' .`): the only two hits are in `build-005-…md` describing the sweep R3 owns. **No real anchor anywhere in the tree**, matching the plan's pre-flight reading. R3 re-runs it as its backstop.

### Checklist audit — every tick examined, none inherited

All 20 boxes in `### Dispatched findings checklist` are `- [x]`. **Every tick stands; none was over-ticked, none was left un-ticked with its contract landed, and nothing remains `- [ ]`, so no deferral reason is owed.** The four a final pass can actually falsify were re-derived above (cut-not-copy; `check_spec_glossary` + the 7 anchors; the reference-style / 10-group-header scaffold; rule 27). Of the rest, box 2's pointer coverage was re-derived from the deletion hunks, box 9's "no history narration" was swept (`amendment|retraction|as of (review )?round|superseded by|previously stated|this spec used to` over the spec → the *only* hit is the companion pointer at spec:3, which rule 1 requires and which is a pointer rather than a chronology), box 19's no-out-of-scope-write was re-derived from `git status --porcelain` scoped to the forbidden paths (**empty**), and box 20's no-pre-emption follows from the diff's added side being pointers only.

**One tick carries a superseded parenthetical, recorded rather than re-looped.** Box 1 reads "(measured: 0 non-scaffold shared shingles)". The box's **contract** — the move is a cut, not a copy — landed and is proven by the line-granularity check, so **the tick is correct and stays**. The figure is what moved. I re-derived the intersection over both file *bodies* (everything before `<!-- LINK DEFINITIONS -->`, which removes the scaffold by construction rather than by a filter) at three tokenizations:

  | tokenizer | n=8 | n=6 |
  |---|---|---|
  | punctuation kept | **0** | 2 |
  | punctuation stripped, `.` and `#` retained | **3** | 12 |
  | punctuation stripped, nothing retained | **4** | 13 |

  The move report's `3` reproduces exactly, and its three members are exactly the ones it names. **Neither figure is wrong; the number is tokenizer-dependent and a bare count carries no information.** The three overlaps were audited by pass 2 and re-audited independently here, and none of them is a moved block: the forward check proves every one of the 18 removed lines is absent from the post-move spec, so the cut-not-copy invariant holds unconditionally, at every tokenizer. Two overlaps are the section heading the keying rule *requires* the rationale to reproduce; the third is a condensation of a falsified diagnosis that `BUILD.md` `## Spec rationale extraction` positively requires the file to carry. **Supersession recorded here; the box is not un-ticked and no re-loop is warranted**, which is the disposition Worker 3 routed to this pass.

**A second figure in this artifact is superseded the same way, and I found it by applying the same lesson.** The pass-1 `### DRY findings` state "**0** non-scaffold 8-word overlap" against `spec-018` and `spec-019`. Under a punctuation-stripping tokenizer that is 0 against spec-018 and **6 against spec-019**, of which 3 are substantive. Both survive inspection and neither is a restatement of spec-019's reasoning, which is what box 18's contract actually is:

- `types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"` — a symbol-qualified source reference. `AGENTS.md` rule 27 **mandates** this exact spelling, so every document citing that line matches every other by construction. A shared citation is not a shared argument.
- The card sentence declaring no new public API and no `Meta.field_overrides`-style key — a quotation of KANBAN card `DONE-019-0.0.6`, which the rationale attributes to the card by name (rationale:183) and which `spec-019:234` carries from the same source. Two documents quoting one card is not one restating the other.

  **Box 18 stands ticked.** Recorded because a stated count propagates silently and this one had been re-stated across two passes.

### Hand-off list audit — R1's most load-bearing output

Eleven items under `### Notes for Worker 1 (spec reconciliation)` (1-8 from the move pass, 9-11 from the apply-changes pass). **All eleven are accurate, and I re-verified each against the current spec rather than against the claim**: `metaprimary` sole-carried at spec:31; `configurationerror` / `djangotype` at spec:9, `metainterfaces` at spec:12, `metafields` / `metaexclude` at spec:11, `metamodel` at spec:67; `grep -n registry.clear` over the post-move spec → no match, so D15 is discharged; `## Non-goals` still carries both "future" words; `## Coordination …`'s "must update this contract spec accordingly" is untouched at spec:94; exactly **two** `**Decision for 0.0.3.**` blocks exist (spec:51, spec:61) and both sit directly above their pointers (spec:53, spec:63); `### Accepted vs deferred Meta keys (shipped in 0.0.3)` is byte-identical to HEAD, so `spec-006`'s by-title citation is intact.

Each item names the spec section it applies to, with two correct exceptions: item 3 (D15) names removed text and states outright that no R2 edit is owed, so there is no surviving section to name; item 11 is a verification-method hand-off rather than a spec-amendment one. Neither is ambiguous.

**One completeness extension, and it is the reason this audit is worth running.** Worker 3's re-review note 3 observed that hand-off 9 is written in the singular while the class has a second member. I did not take that on prose — I **established the population** rather than sampling it, by extracting every double-quoted span of 25+ characters from the rationale (**20** spans) and testing each, whitespace-normalized, against the post-move spec body. Exactly **one** is a verbatim quotation of surviving spec prose:

> `## Coordination …`'s "must update this contract spec accordingly" (spec:94), quoted in the rationale's `## Open questions` entry.

The override diagnosis hand-off 9 names is a *condensation*, so it never appears in a verbatim scan at all — which is precisely why the two members had to be found by two different methods, and why neither method alone establishes the class. **Hand-off 9 is hereby extended to the class, and this paragraph is the record R2 reads:**

> **Extended hand-off 9 (Worker 1, final verification).** The rationale quotes or condenses **two** claims that are still standing in the spec, both deliberately, and R2 must not sync either when it corrects the spec's copies. (a) The `@strawberry.type`-rewrites-`cls.__annotations__` override diagnosis — condensed in the `### Consumer override semantics` entry; the spec's copies are `## Problem statement` item 2 and `### Consumer override semantics`'s first paragraph (D5). (b) `## Coordination …`'s "must update this contract spec accordingly" — quoted verbatim in the `## Open questions` entry; the spec's copy is spec:94 (D18). In both cases the rationale's copy becomes **the record of a claim the spec may no longer make**, which is what `BUILD.md` `## Spec rationale extraction` requires the file to carry; deleting or rewriting it to match a corrected spec would delete the record. The population is exhaustive at two, established by a full quoted-span scan plus the shingle table above, not by sampling.

**One reading clarification so R2 does not mistake two consistent lists for a contradiction.** The move report's `### What moved, what stayed, what was deleted` names **four carve-out keeps** (`### One-model-one-type`'s opening paragraph, the merge-code-can-stay clause, `## Problem statement` in full, `### Accepted vs deferred Meta keys`'s promotion rule and its parenthetical). The rationale's `## Provenance of this record` names **four deliberately-left passages** and calls that list exhaustive — a *different* set (it adds `## Current state`'s status lists and the `### Consumer override semantics` diagnosis paragraphs, and omits the last two of the move report's four). Both are correct under their own criterion: the rationale's list enumerates passages **that read like deliberation**, and `## Problem statement` and the promotion rule are normative contract. The deletion hunks confirm neither lost a byte, so `## How to read this file`'s own rule covers them — "a section with no entry here lost nothing". `## Problem statement` item 1's competitive comparison, the one genuinely argumentative survivor, is explicitly considered at rationale:85. No edit is owed; a reader who takes the two lists as one will otherwise conclude a passage went unexamined.

### Relocation / promotion claims, proven rather than read

`BUILD.md` `## Claims are proven mechanically, never accepted on prose` names three shapes, and this item makes two of them. Both re-proven here rather than discharged by reading Worker 3's acceptance:

- **Relocated / carried over unchanged** — the whole move. Proven by the line-granularity check above against a read-only `git show HEAD:` copy in a scratch path **outside** the repo. Quote fidelity of the material spot-checked at the two places re-typing most easily smooths: the four `Meta.primary` rules' `->` arrows and the parenthesised `` `spec-meta_primary.md` `` slug in the lead-in the apply pass added.
- **Stated counts** — every figure this artifact carries was re-measured: 18 removed lines, 17/18 then 18/18 accounted, 13,346 → 11,002 bytes, 5 insertions / 27 deletions, 7 anchors at 1+1, 8/8 and 8/8 and 0/0 reference integrity, 16/16 targets on disk, 12 and 8 headings with 0 duplicate slugs, 285 lines / 20,086 bytes. **All reproduce.** The two that did not survive re-derivation unchanged are the two tokenizer-conditional shingle figures, both recorded above as supersessions rather than corrections, since neither was measured wrong.

### DRY and duplication

No prior accepted item exists in this cycle, so the cross-item scan has one side. Against the siblings the position is unchanged and is a template rather than a copy this pass introduced: ~195 non-scaffold 8-word shingles with `spec-001-…-rationale.md` and ~99 with `spec-004-…-rationale.md`, **0 substantive** in both after filtering for the domain vocabulary (`registry|model|annotat|Meta\.|Strawberry|convert|primary|lazy_ref|optimiz`) — re-derived here, not inherited. The existence challenge has no target: this item writes Markdown and adds no helper, constant, or indirection layer. **No DRY opportunity remains open, so nothing blocks acceptance on this ground.**

### Failability, fail-open, hot path, floor

- **Failability proofs.** None owed. `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to new boundaries, guards, gates, and rejection paths; this item introduces none. Both build reports carry the heading, correctly filled with the literal.
- **Fail-open shapes.** None possible — the item touches no executable code. `git diff -- django_strawberry_framework/__init__.py` → **empty**; `git status --porcelain` over `django_strawberry_framework/`, `tests/`, `examples/`, `CHANGELOG.md`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `scripts/`, and the spec-005 terms CSV returns **nothing**.
- **Hot-path budget.** The plan declares `none` build-wide; correctly recorded as not applicable in both build reports.
- **Floor verification.** The plan declares scope `none`; correctly recorded as not applicable in both build reports. Nothing in this item reasons about version-dependent behavior, so there is no unrun floor claim to close.

### Tree hygiene — no leftovers from this item

- **No scratch file inside the repo.** The read-only HEAD copy lives in the session scratchpad outside the working tree. `find` over the tree for `dsf-proof*`, `*.orig`, and `spec-005-HEAD*` → **nothing**. `docs/builder/temp-tests/` is **empty**.
- **No mutation left in place.** No `ACTIVE-MUTATION.json` anywhere, and no mutation was ever applied — this item introduced no boundary to mutate.
- **Nothing written outside the writable set.** The item's whole footprint is `M docs/SPECS/spec-005-django_type_contract-0_0_3.md`, `?? docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`, and `?? docs/builder/bld-005-r1-rationale_move.md`.
- **Baseline-dirty out-of-scope entries untouched and unreverted** (`AGENTS.md` rule 34): the five spec-004-cycle files and the four staged-deleted `bld-003-*.md` entries are exactly as the plan records them. The four deletions still await the maintainer. Nothing was `git checkout`-ed, stashed, or restored at any point in this pass.

### Not swept into a concurrent commit — proven with `git log --stat`

`git log --stat` over this cycle's four paths: the newest commit reaching **any** of them is `ff65666d` ("docs: normalize review citations to their durable records", 2026-07-30), which predates the cycle and touched the spec by one line. `git log` over the rationale, this artifact, and the build plan is **empty** — all three are still untracked and have never been committed. `git status` alone was not used for this determination at any point.

### Summary

R1 delivered its contract in full. The spec's deliberative layer — two `**Future direction.**` prediction blocks, the "real friction" derivation, the first-registered-wins rejection, and all of `## Open questions` — was **moved** to `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`, keyed entry-by-entry to the spec sections it came from, with rejected alternatives, the later spec that caused each change, and a per-entry record of claims the section may no longer make. The spec shrank 13,346 → 11,002 bytes (-17.6%) and gained three pointers and one link definition, nothing else. All 7 glossary anchors survive at 1 use + 1 definition; all three gates exit 0.

The item's durable contribution beyond the file itself is methodological and belongs on the record: **a span-sampled move check cannot detect a sentence nobody made into a span**, and the line-granularity check off `git diff -U0` that replaced it is what found the one cut sentence two earlier verifications missed. Its companion lesson is that **the cut-not-copy shingle count is tokenizer-dependent and means nothing unquoted** — two figures in this artifact are superseded on exactly that ground, neither by being wrong.

Nothing is deferred and nothing re-loops. R2 inherits eleven verified hand-offs, one of them extended here to its full class of two.

### Spec changes made (Worker 1 only)

**None.** The spec was not opened for writing by this pass, and `git diff --stat` over it is still `5 insertions(+), 27 deletions(-)` at 11,002 bytes / 132 lines — byte-identical to the move pass's output.

R1 required no reconciliation edit of its own. Every sentence the build could have licensed editing is a **falsified factual claim** rather than an R1-revealed gap, and each is drift-table material inside R2's declared write set: `## Current state`'s "in flight" framing (D1), `## Problem statement` items 1/2/4 (D2/D5/D13), `## Non-goals`' two "future"s (D17), both `**Decision for 0.0.3.**` blocks' second halves (D6/D7), `### Accepted vs deferred Meta keys`' rosters (D9/D10), `## Coordination …`'s never-followed instruction (D18), and `## References` (D19). Editing any of them here would be R2's work performed early, would fragment a correction R2 must land coherently, and — for `## Current state` — would disturb `metaprimary`'s sole anchor carrier outside the edit hand-off 1 requires it be re-sited within. Left as hand-offs, deliberately.

**No checklist box is deferred**, so no deferral reason is owed under `docs/builder/ARTIFACT.md`. The two supersessions recorded above are corrections to *figures inside* ticked boxes, not deferrals of their contracts.

### Final status

`final-accepted`.

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
