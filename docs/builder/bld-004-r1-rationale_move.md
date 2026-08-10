# Build: R1 — Spec rationale extraction (spec-004)

Spec reference: `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` (whole file; the move touched lines 1-3, 7, 15-46, 48-76, 80-113, 113-155, 156-177, 179-215, 217-235, 237-267, 269-301, 345-346 of the pre-move file)
Rationale file created: `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`
Status: final-accepted

**Shape note.** Per `docs/builder/build-004-optimizer_beyond-0_0_3.md` Deviation 2, R1 has no Worker 2 pass: `BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role that performs the move and states that Worker 2 never reads the rationale file. So the `## Build report (Worker 2)` section of `docs/builder/ARTIFACT.md` is not applicable here and the performance record lives under `## Move report (Worker 1)` below, carrying the same fields Worker 3 would otherwise read from a build report. `Status:` is `planned` on return, which Worker 0 reads as "dispatch Worker 3" for this item.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable, and deliberately so. `worker-1.md` `### Package-wide helper inventory before helper planning` gates *helper-like logic*; R1 changes no package source and adds no helper, shared constant, validation branch, coercion utility, or test helper. The build plan's `## Build-wide context flags` declares package source, `tests/`, and `examples/` read-only for the whole cycle. No inventory was refreshed and none was needed.
- **Existing patterns reused.** The three archived precedents at the same `docs/SPECS/appx/` depth supplied the file shape: `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md:1-90` (the H1 with the `(deliberation, rejected alternatives, change record)` suffix, the "Deliberative companion to …" opener, the "**The move happened long after the release, not before the build.**" provenance paragraph, `## How to read this file`, `## Provenance of this record`, `## Entries keyed to the spec`, `## Standing notes`, and the three-way *Moved* / *Cut* / *Deleted* provenance vocabulary its own Worker 3 pass forced it to adopt) and `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md:22-28` (the em-dash sub-heading anchor hazard and its parent-anchor workaround). The in-spec companion-pointer paragraph follows `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md:3` in form. The link-definition scaffold at this depth (`../` for a `docs/SPECS/` sibling, `../../` for `docs/` and `docs/builder/`, `../../../` for a root file) is copied from `spec-003-…-rationale.md`'s block.
- **New helpers justified.** None; no code was written.
- **Duplication risk avoided.** Three live risks, all named by the build plan and all handled explicitly and measured, not asserted:
  - **Against the `spec-002` and `spec-003` rationales.** Both already narrate the optimizer-family split. This file does not retell it: `## How to read this file` carries a bullet pointing at both and saying outright that the argument is not duplicated on this side of the split, and the spec's own new pointer paragraph carries the same clause for `spec-002`. Measured below.
  - **Against the spec.** The move is a cut, so no moved block exists in both files. Measured below (49 shared 8-word shingles between the rationale and the post-move spec, every one attributable).
  - **Against the later optimizer specs.** `spec-033` / `spec-035` / `spec-029` own most of the surface the drift table names. Every entry that touches one **points** at the owning spec rather than restating its rules — the build plan's `**The scope trap specific to this spec.**` rule, applied to the rationale as well as the spec.

### Implementation steps

Line numbers are pin-at-write-time; all are against the **pre-move** spec unless stated.

1. Insert the companion-file pointer paragraph after the H1 (spec:1-2). Done.
2. `## Problem statement` — re-point the "recommended sequence in "Priority and ordering"" clause at the rationale file, since step 9 deletes that section (spec:7). Done.
3. `### B1` — delete `**The win.**` (spec:17); cut the `**Cache lifetime (spike completed 2026-04-30)**` narrative and relabel the surviving two rules `**Cache storage.**`, re-siting the `djangooptimizerextension` link into it (spec:23); rescue the `(name, value)` pair shape and the omit-rather-than-default rule into `**Directive-variable extraction.**` (spec:21); delete the fence (spec:25-40); add a pointer. Done.
4. `### B2` — delete `**The win.**` (spec:50) and the fence (spec:56-68); add a pointer. Done.
5. `### B3` — delete `**The win.**` (spec:82) and fold its one API sentence into `**Mechanism.**`; rescue the `dst_optimizer_planned` context key into `**Mechanism.**` (spec:84); cut approach (b) and the profiling instruction from the path-construction prerequisite (spec:90); cut the rejected `strict=True` kwarg sentence (spec:107); delete the fence (spec:92-105); add a pointer. Done.
6. `### B4` — delete `**The win.**` (spec:115); cut the rejected untyped hint-value shapes from the typed-wrapper lead-in (spec:119); cut the DRF-analog positioning sentence (spec:128); delete the fence (spec:132-148); add a pointer. Done.
7. `### B5` — delete `**The win.**` (spec:158); cut the "B5 should land first" clause (spec:162) and the "afternoon project" estimate (spec:177); delete the fence (spec:164-173); add a pointer. Done.
8. `### B6` — trim `**The win.**` to its public-API sentence and relabel it `**Public API.**` (spec:181); delete the fence (spec:194-211); add a pointer. Done.
9. Delete `## Priority and ordering` in full (spec:217-235). Done.
10. `### B7` — delete `**The win.**` (spec:239) and the "complementary to B1" derivation (spec:241), rescuing the snake-cased map keying into `**Mechanism.**` (spec:243); delete the fence (spec:247-263); add a pointer. Done.
11. `### B8` — put the `queryset-diffing` link on the heading (spec:269); drop the `**The win.**` label and keep its paragraph verbatim; delete the fence (spec:281-295); add a pointer. Done.
12. Add `[spec-004-rationale]` to the spec's `<!-- docs/SPECS/ -->` link-definition group (spec:345). Done.
13. Write the rationale file with one entry per section cut from, plus two entries keyed to text that no longer has a heading. Done.

### Test additions / updates

None. R1 adds no test and changes no code path. The verification for this item is the command set recorded under `### Validation run` below, and `AGENTS.md` rule 15 forbids a `pytest` run that was not asked for.

### Implementation discretion items

None reserved. R1 has no downstream builder, so nothing is delegable.

### Dispatched findings checklist

There is no `## Slice checklist` in spec-004 and this is not a review round, so — per `worker-1.md` planning step 8, which puts a `### Dispatched findings checklist` in this position when no spec slice checklist exists — the boxes below are the R1 obligations drawn from `docs/builder/BUILD.md` `## Spec rationale extraction`, `worker-1.md` `### Performing the rationale move`, and the build plan's R1 constraints. Worker 1 both performs and ticks here because Deviation 2 removes the Worker 2 pass; the ticks are audited at Worker 1's own final verification after Worker 3.

- [x] The move is a cut-and-paste, not a copy and not a summary: text that lands in the rationale left the spec.
- [x] Every decision cut from keeps a one-line pointer in the spec naming what was moved and where.
- [x] The rationale file is keyed to the spec: every entry names the spec section it belongs to by heading and links a resolving anchor.
- [x] Rejected alternatives are recorded with the one-line reason each lost.
- [x] Every change a decision has undergone is recorded with the round or later spec that caused it.
- [x] Every claim the spec may no longer make is recorded, per entry.
- [x] Prose the current decisions have falsified was **deleted, not moved** (rule 2).
- [x] Implementation-relevant rationale — the "why" that changes HOW a thing is built — **stayed in the spec** (the load-bearing carve-out).
- [x] The spec narrates no history: no amendment block, no retraction paragraph, no "as of round N" hedge was added.
- [x] `check_spec_glossary.py --spec …` still exits 0 and all 10 anchors still carry exactly one body link.
- [x] `check_trailing_commas.py --check` passes on the spec and the new rationale file.
- [x] `import_spec_terms --check` still exits 0 — the card-wrap chain the 10-anchor constraint protects is intact.
- [x] Every in-page anchor the rationale targets resolves against a real post-move spec heading.
- [x] Reference-style links only; `<!-- LINK DEFINITIONS -->` block present with all 10 canonical group headers in order; every definition target disk-checked.
- [x] `AGENTS.md` rule 27 holds in both files: no raw `path:NN`.
- [x] The rationale file is written directly to `docs/SPECS/appx/`, tracked and durable.
- [x] Spec byte count before and after reported.
- [x] The `spec-002` and `spec-003` rationales are pointed at, not duplicated.
- [x] No source, test, example, sibling spec, terms CSV, `CHANGELOG.md`, `KANBAN*`, `docs/GLOSSARY.md`, or DB file was written.

---

## Move report (Worker 1)

### Files touched

- `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` — 28 insertions, 171 deletions (`git diff --stat`). Eight fenced pseudo-code blocks, eight `**The win.**` paragraphs, one whole section, one dated spike narrative, and six argument clauses cut; four rules restated in prose; one companion pointer paragraph and eight per-section pointers added; two glossary links re-sited; one link definition added.
- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — new, 728 lines / 50,703 bytes.

### Byte count (required report)

| | lines | bytes |
|---|---|---|
| spec **before** | 359 | 33,928 |
| spec **after** | 216 | 26,409 |
| delta | -143 | **-7,519 (-22.2%)** |
| rationale file (new) | 728 | 50,703 |

Re-measured before the first edit with `python3 -c "d=open(...,'rb').read(); print(len(d), d.count(b'\n'))"`: **33,928 bytes** — matching the build plan's pre-flight figure exactly — and **359** newline-terminated lines. The plan's "360 lines" is one high; the file ends with a single trailing newline after `<!-- External -->` on line 216 (was 359), so `wc -l`, `splitlines()`, and a newline count all agree on 359. Fence markers before: **16** (`grep -c '^```'`), i.e. 8 blocks. After: **0**.

### What moved, what stayed, what was deleted

**Cut, with a prose account kept in the rationale.** All **8** fences (one per slice, confirmed by the 16→0 marker count); all **8** `**The win.**` paragraphs, of which one survived whole and one survived in part (below); the whole of `## Priority and ordering` (19 lines, 9 paragraphs); the `**Cache lifetime (spike completed 2026-04-30)**` narrative in `### B1`; and six argument clauses — B3's second path-construction approach and its profiling instruction, B3's rejected `strict=True` kwarg, B4's rejected untyped hint-value shapes, B4's DRF-analog positioning sentence, B5's "should land first" ordering clause and its "afternoon project" estimate, and B7's "complementary to B1" derivation.

**Stayed in the spec under the load-bearing carve-out.** This is the part of the job the prompt names as the whole job, so each is listed with the defect its loss would cause:

1. **The cache key's variable frozenset holds `(name, value)` pairs, and a collected name with no supplied value is omitted rather than defaulted** (`### B1` `**Directive-variable extraction.**`). Both rules lived only inside the deleted fence; the prose above it said only "extract just those values". A set of bare names cannot distinguish two executions of one document that resolved the same directive variable differently — which is the entire property the component exists to provide, so the fence's loss would have silently deleted the component's point. Verified at HEAD: `optimizer/extension.py::_collect_cache_relevant_var_names` docstring #"``_build_cache_key`` folds one name set through its single ``(name, value)`` comprehension" and `::_hashable_variable_value` docstring #"stores cache-relevant ``(name, value)`` pairs in a ``frozenset``".
2. **The strictness sentinel is stashed under the context key `dst_optimizer_planned`** (`### B3` `**Mechanism.**`). The fence was its only carrier; the prose said the sentinel goes "on `info.context`" and never named the key. It is half of a two-sided protocol — the extension writes it, `types/resolvers.py` reads it — so a builder implementing either end needs the other end's spelling, and B5 states its own key the same way, which is why the omission read as an oversight rather than a policy. Exact at HEAD: `optimizer/_context.py #"DST_OPTIMIZER_PLANNED = \"dst_optimizer_planned\""`.
3. **The precomputed field map is keyed by the snake-cased field name** (`### B7` `**Mechanism.**`). Its only two carriers — the fence and the `**The win.**` paragraph — were both being cut in the same pass, which is the exact shape a sweep loses. `**Mechanism.**` said "build a `dict[str, FieldMeta]`" without saying what the string is; a map keyed on the raw Django field name misses every camelCase selection the schema exposes. Verified at HEAD: `types/base.py #"field_map = {snake_case(f.name): FieldMeta.from_django_field(f) for f in fields}"`.
4. **The `check_schema` public-API sentence** (`### B6`, relabelled `**Public API.**`). It is the only statement anywhere in the document of the audit entry point's name, receiver, and argument. Cutting the `**The win.**` class wholesale would have removed the API from a spec that then specifies its behaviour for four more paragraphs. Only its closing positioning went. The word "classmethod" in it is **false at HEAD** (`optimizer/extension.py::DjangoOptimizerExtension.check_schema` is a `@staticmethod`) and was kept verbatim on purpose — it is a status claim and belongs to R2.

Also kept whole: **B8's opening paragraph**, the one `**The win.**` of the eight that names no competitor. It states the package's own pre-B8 behaviour and why a duplicate matters, which is the slice's problem statement rather than positioning. Its label was dropped and not one word else, so its present tense stays R2's.

**Deleted rather than moved (rule 2).** The fences' bodies — statement sequences, signatures, privacy, and file placements. Their falsified symbol names are *named* in the rationale where naming them is what makes a departure legible (`build_dotted_path`, `planned_relation_paths`, `_collect_reachable_types`, `mark_fk_id_elided`, `cls._optimizer_field_map`, `getattr(type_cls, "_optimizer_hints", {})`, `delta.apply(queryset)`), but nothing reconstructs how a fence was written and the file carries **zero** code fences. Also deleted outright: the spike's `_sync_extensions` / `_async_extensions` findings and its bolded consumer recommendation, both falsified in `strawberry-graphql 0.316.0` — recorded in the rationale as a superseded claim keyed to B1, with `spec-029` Decision 3 named as the successor, because deleting it with no account would erase the only record of why this package ever told consumers to pass an instance.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` → `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**. Baseline (build plan pre-flight step 6) was character-identical.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` → **exit 0** on both files. Both carry `<!-- LINK DEFINITIONS -->` and all 10 canonical group headers in the canonical order.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0** — the card-wrap chain the 10-anchor constraint protects is intact, and the run left no DB churn (see `git status` below).
- `grep -c '^```'` → spec **0**, rationale **0**. Sixteen markers at HEAD, zero now.
- Anchor resolution: a run of `scripts/check_spec_glossary.py::github_anchor` over the post-move spec's 15 headings gives **0 duplicate slugs**; the rationale's 2 anchor-bearing definitions (`#proposed-improvements`, `#problem-statement`) both resolve. Reference integrity, both files: rationale **19 definitions / 19 distinct uses**, spec **11 / 11**, with **0** undefined references and **0** unused definitions in either.
- Link targets: all 19 rationale definition targets and the 1 new spec definition target disk-checked present (`[ -e ]` per path, resolved from the source file's directory).
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files → **no match** (exit 1). Rule 27 preserved, not merely unbroken.
- `grep -P '\]\((?!#|https?:)'` over both files → **no match** (exit 1). No inline `](path)` link in either.
- `git status --short` → `M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`, `?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`, plus Worker 0's `?? docs/builder/build-004-optimizer_beyond-0_0_3.md` and the baseline-dirty `M docs/spec-068-graph_substrate-0_1_1.md`. **`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` are all clean**, as the build plan's `## Concurrent-writable tracked binary / generated files` expects for R1.
- No `pytest` run (`AGENTS.md` rule 15); no `ruff` run (no `.py` file touched); no coverage-shaped flag in any form.
- No `git stash`, `git checkout`, `git restore`, or `git worktree` at any point. The read-only HEAD reference was obtained with `git show HEAD:docs/SPECS/spec-004-optimizer_beyond-0_0_3.md > <scratchpad outside the repo>/spec-004-HEAD.md`.

### The 10-anchor constraint — per-anchor result

All 10 survive at exactly **1 body use + 1 definition** each (`grep -o "\[glossary-<anchor>\]" | wc -l` → 2 for every one). Two of the ten sat inside text this pass cut and were re-sited; the other eight were not touched and the terms CSV was never opened.

| Anchor | Carrier at HEAD | Carrier after the move | Re-sited? |
|---|---|---|---|
| `djangooptimizerextension` | `### B1` `**Cache lifetime (spike completed 2026-04-30)**` | `### B1` `**Cache storage.**` — "a dict on the `DjangoOptimizerExtension` instance" | **yes** |
| `queryset-diffing` | `## Priority and ordering` "B8 last …" | the `### B8` heading itself | **yes** |
| `only-projection` | `## Current state` | unchanged | no |
| `fk-id-elision` | `## Current state` | unchanged | no |
| `metaoptimizer_hints` | the `### B4` heading | unchanged | no |
| `djangotype` | `### B4` `**Mechanism.**` | unchanged | no |
| `optimizerhint` | `### B4` `**Mechanism.**` | unchanged | no |
| `configurationerror` | `### B4` `**Validation.**` | unchanged | no |
| `metafields` | `### B6` exposed-fields paragraph | unchanged | no |
| `metaexclude` | `### B6` exposed-fields paragraph | unchanged | no |

**Neither re-siting kept narration alive to hold a link.** `djangooptimizerextension` landed in a surviving contract sentence that already had to name the extension instance (it is the object the cache lives on, and therefore the reason `spec-029`'s singleton-factory form is required). `queryset-diffing` landed on the `### B8` heading, matching what `### B4` already does with `metaoptimizer_hints`; the heading's rendered anchor is unchanged (`b8-queryset-optimization-diffing` under the repo slugger) because both the repo's slugger and GitHub render a heading down to its visible text before slugging — confirmed by running `github_anchor` on the post-move heading. The build plan flagged `djangooptimizerextension` as the highest-risk anchor in the cycle; it is one of the two that moved.

### The move is a cut, not a copy — measured

8-word shingles, link-definition blocks stripped, punctuation folded to whitespace, lowercased. HEAD copy obtained read-only as above.

| measure | value |
|---|---|
| shingles at HEAD | 4,646 |
| shingles post-move | 3,643 |
| shingles that left the spec | 1,685 |
| of those, present in the rationale | **129 (7.7%)** |
| of those, present in neither file | **1,556** |
| rationale x post-move-spec overlap | 49 |
| fenced blocks: HEAD spec / post-move spec / rationale | 8 / **0** / **0** |

Every one of the 129 surviving runs was inspected individually and every one is an explicit quotation inside quotation marks or a code span — a rejection's own stated reason (`### B3`'s `strict=True` sentence, 20 shingles), a claim the package falsified (`## Priority and ordering`'s "pure polish item" sentence, 9 shingles), or a cut `**The win.**` clause being quoted as the thing under discussion. The rationale's `## Provenance of this record` labels exactly this category **Moved** and states the 129 / 1,556 split in the file itself, so a later reader can tell "the text is here" from "the text is gone" without re-running this measurement. The 49-shingle rationale-versus-post-move-spec overlap is section headings, the deliberately mirrored pointer vocabulary, and the rationale quoting surviving spec prose as the claim it is discussing.

### Failability proofs

None; this pass introduced no new boundary. R1 changes no package source — `git diff -- django_strawberry_framework/` is empty.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **Where the boundary against R2 was drawn, and why.** R1 cut the *deliberative* layer — competitive argument, proposal code, build order, effort estimates, and one superseded spike. It left every present-tense **status claim** about the codebase standing, even the ones HEAD plainly falsifies (D1, D2, D3, D16, D17, D21, D22, D23, D27). The precedent is the spec-002 and spec-003 extraction passes, both of which recorded that a status claim moved into a rationale file is neither a legitimate entry there nor the deletion the move prescribes for falsified prose. The rationale's `## Standing notes` states the boundary **in the durable file** rather than only here, and enumerates nine specific survivals, so R2 does not have to infer it from an artifact that closes with the cycle.
- **Why the `**The win.**` class was cut rather than kept.** The build plan names it as the largest uniform block of deliberation and as the class most tempting to keep. The applied test is `worker-1.md`'s: does an implementer need the sentence to build the thing. For six of the eight the factual content is restated verbatim in the same slice's `**Mechanism.**`; what remains once the restatement is subtracted is the argument for why the package exists, which is `GOAL.md`'s and `README.md`'s subject. The two that did not pass that test are listed above and both survived. The rejected alternative — keep the paragraphs and strike only the competitor's name — is recorded in the rationale's first entry.
- **Two fences contradicted their own sections' prose, and the contradiction is why cutting beat correcting.** `### B6`'s fence walked `model._meta.get_fields()` while the paragraph two above it requires walking only Meta-exposed fields, and says why (a hidden or `SKIP`-hinted relation must not be flagged). `### B2`'s fence keyed the elision on a bare field name while the paragraph three below it rejects exactly that with the aliased query that breaks it. In both cases the prose is what shipped. Cutting removes the contradiction; correcting the fence would have left two statements of one rule to keep in step.
- **The `## Priority and ordering` deletion closed a document-structure defect as a side effect (D24).** B7 and B8 were orphaned *below* that section, so a reader working down `## Proposed improvements` found six of the eight slices. Removing the section put all eight under one heading with no slice text moved. This is disclosed as a consequence rather than claimed as a reconciliation edit, and it is recorded in the rationale's `## Standing notes` so R2 does not spend a pass hunting a defect that is already gone.
- **One clause was re-pointed rather than left dangling.** `## Problem statement` referred to "the recommended sequence in "Priority and ordering"", which step 9 deleted. `worker-1.md` rule 3 forbids a surviving cross-reference into moved text that does not name the rationale file, so the clause now points there. The `**Depends on.**` half of the same sentence is untouched: a dependency is a constraint and stayed in the spec; a recommended sequence is an opinion and left. This is the only sentence R1 rewrote for a reason other than the move itself, and it is the direct analogue of the one retense the spec-003 R1 pass disclosed.
- **Anchors were computed, not eyeballed.** `spec-002`'s rationale records that the two sluggers in play disagree on how many hyphens an em dash produces, and spec-004's eight slice headings all carry one. Confirmed by running the repo's own `check_spec_glossary.py::github_anchor`: it collapses the whitespace run to **one** hyphen (`b1-ast-cached-plans`) where GitHub emits **two**. So every slice entry keys to the unambiguous parent `#proposed-improvements` anchor and names its own heading in the entry title, which is the disposition `spec-002`'s rationale already took for the identical hazard. Both anchor-bearing definitions were then checked to resolve against a real heading slug.
- **Verified against source rather than trusted from the drift table.** The build plan says Worker 1 re-verifies each row. Re-verified for this pass: `DST_OPTIMIZER_PLANNED = "dst_optimizer_planned"` and the five-key family in `optimizer/_context.py`; the snake-cased `field_map` build in `types/base.py`; `check_schema` as a `@staticmethod`; `_plan_cache` as an `OrderedDict` with `_MAX_PLAN_CACHE_SIZE = 256`; `_collect_cache_var_families` / `_hashable_variable_value` and the `(name, value)` comprehension; `diff_plan_for_queryset -> tuple[OptimizationPlan, Any]`; `prune_unsupportable_select_related`; `OptimizationPlan.finalize` / `_assert_under_construction`; `OptimizerHint.strategy` and `__post_init__`; `walker.py::_resolve_field_map` / `::_resolve_optimizer_hints`; `types/definition.py::DjangoTypeDefinition.field_map`; and **zero** occurrences of the `cls._optimizer_field_map` / `cls._optimizer_hints` attribute form package-wide (`grep -rnE '\b(cls|self|type_cls|target_type)\._optimizer_(field_map|hints)\b' django_strawberry_framework/` → 0). A loose `grep` for the bare substrings returns 13 hits, all of them the unrelated `_meta_optimizer_hints` / `_validate_optimizer_hints` / `_resolve_optimizer_hints` symbols — worth recording because that grep is the obvious one and it reads as contradicting D22.
- **The rationale's provenance labels were corrected before this artifact was written.** The first draft filed the quoted sentences under "nothing was moved", which is the same mislabelling Worker 3 raised as a Low finding on the spec-003 rationale. The three-way vocabulary (*Moved* / *Cut, with a prose account kept here* / *Deleted with no account kept*) is now stated in the file's opening paragraph before the list uses it, and the *Deleted* bullet no longer claims the falsified symbol names are unrecorded when the entries name several of them.

### Notes for Worker 3

- **The review question that matters here is over-cut, not under-cut.** A rewrite performed by its own author is reviewed by someone with no memory of why a sentence was cut, which is the only vantage point from which an over-cut is visible. **Two classes deserve the attention, and the second is the novel one this cycle introduced:** the eight fences (the spec-003 shape, one carve-out per fence), and the eight `**The win.**` paragraphs removed in a single sweep. A sweep is how a carve-out gets lost, and the spec-003 cycle's own Medium finding was exactly one rule that lived only inside one deleted fence and was missed while five of identical shape were caught. The four rescued rules are listed under `### What moved, what stayed, what was deleted`; for each, the test is to read the post-move spec and ask whether a builder who never sees the rationale could still write the code correctly.
- **The specific place to look for a ninth rescue.** B7's snake-cased map keying was rescued precisely because *both* its carriers (the fence and the win) were being cut in the same pass. That is the only intersection of the two classes I found. If a second exists, it is in `### B1` or `### B3`, whose win paragraphs carried the most technical content.
- **The rationale file is the review instrument.** `BUILD.md` `### Who reads it, and when` makes Worker 3 a reader of it during review. Every entry names the spec section it serves and links a resolving anchor, so each claim is checkable in one hop.
- **Do not treat surviving falsified status claims as R1 findings.** `## Current state`'s mid-build snapshot, `## Proposed improvements`' framing, `### B1`'s three-tuple-over-a-hash key sentence, the four present-tense `cls._optimizer_field_map` sites, `_validate_meta`, `check_schema`'s "classmethod", the `check_optimizer` follow-up, and `## References`' dangling B1 clause are all deliberately untouched and are R2's, per the boundary above and the 28-row drift table in the build plan. The rationale's `## Standing notes` enumerates them.
- **Two claims in this artifact are worth re-deriving rather than reading**, because both are counts and both are load-bearing: the 129 / 1,556 shingle split (the proof the move is a cut) and the per-anchor count of 1 body use each (the proof the 10-anchor constraint held). Commands for both are in `### Validation run` and `### The move is a cut, not a copy — measured`.
- **The staged-anchor grep is no longer silent, and that is not a regression.** `grep -rEn 'TODO\(spec-004|TODO-(ALPHA|BETA|STABLE)-004' .` returned zero hits at pre-flight and returns **two** now, both in `docs/builder/build-004-optimizer_beyond-0_0_3.md` (Worker 0's own description of the sweep R3 will run). Neither is a staged anchor; both are prose quotations of the anchor string. Source, tests, examples, the spec, and the rationale carry **zero**. R3's backstop sweep should distinguish a quotation from an anchor rather than treating the grep count as the signal.
- Nothing was staged for a later pass without being written down; there are no temp tests and no shadow files for this item.

### Notes for Worker 1 (spec reconciliation) — carried into R2

Six items R1 surfaced that belong to R2's sweep, none of them pre-empted here.

1. **D5 leaves the spec with no extension-lifecycle statement at all.** R1 deleted the falsified spike and its inverted recommendation rather than replacing them, because writing the corrected contract is a rewrite and rewrites are R2's. The open question for R2 is whether the spec should state the current construction form (module-level singleton wrapped in a factory) or simply point at `spec-029` Decision 3, which owns it. The build plan's anti-absorption rule and the fact that `docs/README.md` and `docs/GLOSSARY.md` already carry the guidance both argue for the pointer.
2. **D24 is already discharged** by the `## Priority and ordering` deletion — all eight slices now sit under `## Proposed improvements` in order. R2 should verify rather than perform.
3. **`### B6` `**Public API.**` says "classmethod"; HEAD ships a `@staticmethod`.** Kept verbatim on purpose. It is a one-word correction and it is R2's.
4. **`## Implementation checklist` bullet 2 is now the last in-spec trace of the cache-lifetime spike** ("B1 cache-lifetime spike (10-min investigation, precedes B1 implementation)"). A checklist is contract scaffolding so R1 left it, but its parenthetical "precedes B1 implementation" is a sequencing claim about work eleven versions shipped, and the section it once pointed at is gone. R2's call whether it is trimmed.
5. **`## References`' third paragraph was dangling before this pass and still is** (D27): it cites a "skip Strawberry conversion" optimization "noted in B1's implementation" that `### B1` never noted, at HEAD or at any commit R1 read. R1 did not create the dangle and did not repair it. The thing that did land — the deferred-conversion thunk, so a cache hit never pays for AST-to-selection conversion — is a different mechanism.
6. **`### B7`'s "No `_meta.get_fields()` call ever appears in the request path" was cut, but its contradiction survives elsewhere.** The claim was inside the derivation paragraph R1 removed; the sentence that contradicts it — `**Walker needs registry lookup.**`'s unregistered-model fallback — is still in the spec and is still true, and D23 records that the fallback is now a documented dual contract the walker warns about in place. Nothing is owed; R2 should simply not "restore" the deleted claim.

### Spec changes made (Worker 1 only)

Cited against the **post-move** spec unless a pre-move range is given.

| Spec location (post-move) | Change | Reason |
|---|---|---|
| `:3` | Added the companion-file pointer paragraph | `BUILD.md` `## Spec rationale extraction`; form copied from `spec-003:3`. Names the two cuts that have no heading left to carry a pointer (the `**The win.**` class and `## Priority and ordering`) and the do-not-duplicate clause for `spec-002`'s rationale. |
| `:9` (was `:7`) | Re-pointed the "recommended sequence in "Priority and ordering"" clause at the rationale | Rule 3 — the section it named is gone. The `**Depends on.**` half is untouched. |
| `:19-31` (was `:17-46`) | Cut B1's `**The win.**` and the fence; cut the spike narrative and relabelled the survivors `**Cache storage.**`; restated the `(name, value)` pair shape and the omit-not-default rule; re-sited `djangooptimizerextension`; added a pointer | Rule 2 for the spike (falsified in both halves by `strawberry-graphql 0.316.0`) and the fence (hash-vs-printed-AST); carve-out for the pair shape; anchor preservation. |
| `:35-47` (was `:48-76`) | Cut B2's `**The win.**` and the fence; added a pointer | Rule 2 — the fence's elision key is the flat field-name flag the section's own prose rejects. |
| `:53-63` (was `:80-109`) | Cut B3's `**The win.**` (folding its API sentence into `**Mechanism.**`), approach (b) and its profiling instruction, the rejected `strict=True` kwarg, and the fence; restated the `dst_optimizer_planned` key; added a pointer | Rule 2 for the fence; carve-out for the context key; the rest is recorded deliberation. |
| `:71-90` (was `:115-152`) | Cut B4's `**The win.**`, the rejected untyped hint-value shapes, the DRF-analog sentence, and the fence; added a pointer | Rule 2 for the fence (`cls._optimizer_hints` is retired); the rejections are deliberation. |
| `:96-104` (was `:156-177`) | Cut B5's `**The win.**`, the "should land first" clause, the "afternoon project" estimate, and the fence; added a pointer | Rule 2 for the fence; sequencing and effort estimates are deliberation. |
| `:108-125` (was `:179-215`) | Trimmed B6's `**The win.**` to its API sentence and relabelled it `**Public API.**`; cut the fence; added a pointer | Public API stays; the fence contradicts the section's own exposed-fields rule. |
| (was `:217-235`) | Deleted `## Priority and ordering` in full | A recommended build order for work released eleven versions ago is deliberation by construction; its one contract content (the dependency graph) is stated per slice in `**Depends on.**`. Half-retensed already (D28) and carrying a falsified claim (D25). |
| `:127-137` (was `:237-267`) | Cut B7's `**The win.**` and the "complementary to B1" derivation and the fence; restated the snake-cased map keying; added a pointer | Rule 2 for the fence (`cls._optimizer_field_map` is retired); carve-out for the keying, whose only two carriers were both being cut. |
| `:139-157` (was `:269-301`) | Put the `queryset-diffing` link on the `### B8` heading; dropped the `**The win.**` label, keeping its paragraph verbatim; cut the fence; added a pointer | Anchor preservation; the paragraph names no competitor so it is the slice's problem statement, not positioning; rule 2 for the fence (the shipped diff returns a `(plan, queryset)` pair). |
| `:202` | Added the `[spec-004-rationale]` link definition under `<!-- docs/SPECS/ -->` | The nine pointer sites; target disk-checked. |

**Spec status-line re-verification** (`worker-1.md` `## Spec status-line re-verification`): spec-004 carries **no** `Status:` / owner / target-release / predecessor header block — its first lines are the title and `## Problem statement`. Nothing in lines 1-5 is a status line the build could falsify, so no header edit was owed. The line-3 companion paragraph this pass added is a pointer, not a status line. Confirmed against the read-only HEAD copy.

---

## Review (Worker 3)

Read as review inputs: `AGENTS.md`, `START.md`, `docs/builder/BUILD.md` (full), `docs/builder/ARTIFACT.md`, `docs/builder/worker-3.md`, `docs/README.md`, `examples/fakeshop/test_query/README.md`, `docs/builder/build-004-optimizer_beyond-0_0_3.md` (full, including the 28-row drift table, `### The 10-anchor constraint`, and `### What R1 inherits that spec-003 did not`), `worker-1.md` `### Performing the rationale move`, the post-move spec, the new rationale file, and the pristine HEAD spec obtained read-only as `git show HEAD:docs/SPECS/spec-004-optimizer_beyond-0_0_3.md > <scratchpad outside the repo>/spec-004-HEAD.md`. No `git stash` / `checkout` / `restore` / `worktree` at any point. HEAD moved during this cycle (now `c62e990a`, was `20a9752f` at plan time); the HEAD spec blob is byte-identical to the plan's pre-flight figure (33,928 bytes / 359 lines), so the baseline the move was measured against is still the baseline.

### High:

None.

### Medium:

#### B1's eviction discipline was over-cut: the spec no longer states what a bounded plan cache evicts, and the rationale does not record it either

`### B1`'s `**The win.**` paragraph at HEAD opened `An LRU cache keyed on (document_hash, directive_vars, target_model) turns 99% of repeated queries into a dictionary lookup.` That sentence's subject — **LRU** — is the document's only statement anywhere of the plan cache's eviction discipline. It was removed with the rest of the `**The win.**` sweep, and what replaced it says nothing about eviction:

```docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:23
**Cache storage.** Use `self._plan_cache` — a dict on the [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] instance. Use a simple bounded-size dict (not `functools.lru_cache`, since the cache key includes a model class which is not hashable by `lru_cache`'s default).
```

This is the fifth carve-out the pass's own `### Notes for Worker 3` invited a search for, and it is in one of the two sections that note named (`### B1`). It meets every part of `worker-1.md`'s load-bearing test:

- **It changes HOW the thing is built.** A bounded cache must decide what to drop when it is full. With the word gone, `**Cache storage.**` says only "bounded-size dict" — a builder implementing it picks an eviction policy from nothing, and clear-all or insert-order eviction satisfies the surviving sentence exactly as well as LRU does.
- **The surviving sentence pushes actively the wrong way.** `not functools.lru_cache` reads as a rejection of LRU semantics, not just of the stdlib decorator; only the reason clause ("model class is not hashable") narrows it, and a reader has to supply that inference. The build plan's `D6` exists precisely because "a simple bounded-size dict" already drifts from what shipped, and cutting the word "LRU" widens that gap rather than leaving it where R2 found it.
- **The shipped code is an LRU**, so this is a rescue of correct design intent, not a restatement of falsified prose: `D6` records `_plan_cache` as an `OrderedDict` with `_MAX_PLAN_CACHE_SIZE = 256`, `move_to_end` promotion on hit, and least-recent-quarter eviction. Rule 2 (delete falsified prose) does not apply — the cut clause was true.
- **It is not recoverable from the rationale.** `grep -niE 'lru|evict|bounded'` over the rationale returns three hits, all of them the `functools.lru_cache` rejection or an unrelated "depth-bounded". The rationale's `### B1` entry records what the cut spike said and what the fence spelled; neither it nor the `**The win.**` entry mentions eviction, and the B1 entry's **Claims the spec no longer makes** list does not carry it. So the rule is in neither file: it is only in git history, which rule 2 reserves for prose the decisions falsified.

The move report's own justification for the sweep — "for six of the eight the factual content is restated verbatim in the same slice's `**Mechanism.**`" — has B1 as its counterexample. `### B1` `**Mechanism.**` restates the three-part key and the `target_model` argument; it does not restate "LRU", and nothing else in the section does.

**Recommended change.** Restate the eviction discipline as prose in `**Cache storage.**` under the same carve-out the other four rescues used — one clause naming least-recently-used eviction of the bounded dict, sited so the `functools.lru_cache` rejection reads as "not the decorator" rather than "not the policy". Keep it a rule, not a narrative: no reference to the cut paragraph, no "10,000 times/second" motivation, no percentage. Then add the corresponding line to the rationale's `### B1` entry under *"Kept in the spec"*, so the file's own account of what was rescued stays complete.

**Test expectation.** None; no behavior changes. The verification is the same one the other four rescues carry: read `### B1` end to end with no access to the rationale and confirm a builder can now state what the cache drops when it reaches its bound.

### Low:

#### The rationale attributes the card-import chain to the wrong tool, in a durable file

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:658
The spec's ten glossary anchors are each carried by exactly one link, and
`scripts/check_spec_glossary.py` is what a Done card's glossary-link set is rebuilt from, so
dropping one breaks the card's import chain.
```

Both halves are wrong, and the build plan states the correct mechanism twice (`### The 10-anchor constraint`: "`import_spec_terms` is what a DONE card's glossary-link set is rebuilt from"; and the pre-dispatch fact list: "a green `check_spec_glossary` alone does not prove this"). Verified at source: `examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py` #"Import spec companion CSVs into glossary mentions and done-card links" resolves the card's `SpecDoc` path to the companion `*-terms.csv` (`::_terms_path`) and rebuilds the links from the **CSV rows**, never from the spec body. `scripts/check_spec_glossary.py` is the gate that each CSV term has a glossary entry **and at least one spec link** — so dropping a spec-body link breaks that gate, not the import.

It matters because this is the sentence a future reader (R2 first) will act on: as written it implies the spec body feeds the DB, which is the premise under which someone "fixes" a dropped anchor by editing the CSV instead of re-siting the link. Not load-bearing for this diff — the discipline it justifies was followed correctly — hence Low.

**Recommended change.** Name `import_spec_terms` as the rebuilder and `check_spec_glossary.py` as the gate the dropped link trips, in one sentence.

#### The B2 entry restates the invariant it says it is not restating, duplicating spec-003's rationale

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:285
*Changed — the FK-column append is shared, ordered, and gated.* … an elided branch plans no join
and the resolver serving the elision reads the source row's FK column, so appending the column
after the short-circuit leaves it unprojected and silently reintroduces the N+1 the elision
removes. [`spec-003`][spec-003] owns that invariant and states it; it is not restated here.
```

The clause "it is not restated here" is false in its own sentence: the invariant is stated in full immediately before it, and near-verbatim against `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md:143` ("elision reads the source row's FK column, so appending the column after the short-circuit leaves it unprojected and silently reintroduces the very N+1 the elision removes"). Measured: a 17-shingle contiguous run, the longest substantive (non-scaffolding) overlap between this file and either sibling rationale. The build plan's own DRY rule applies — "a fact told twice across the spec and its rationale sibling goes stale in one of them" — and the same reasoning holds across two rationale siblings.

**Recommended change.** Pick one: keep the pointer and cut the restatement to the fact of the departure (the append is now a shared, ordered, gated helper — see spec-003 for the ordering invariant), or keep the restatement and delete the false disclaimer. The first is the DRY-correct one and matches what the surrounding entries do with `spec-033` / `spec-035`.

#### The two pointer paragraphs carry a chronological retraction clause, which is the one thing the spec may not do

`BUILD.md` `## Spec rationale extraction`: "The spec stays the heart, and it never narrates its own history … no amendment block, no retraction paragraph." Two of the added pointers assert, inside the spec, that a recommendation was inverted after the fact:

```docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:3
… the 2026-04-30 extension-lifecycle spike and the recommendation a later Strawberry release inverted, …
```

```docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:29
… the extension-lifecycle spike behind the cache-storage decision together with the consumer recommendation a later Strawberry release inverted, …
```

Rule 1 requires the pointer to **name what was moved and where**; "the extension-lifecycle spike behind the cache-storage decision" already does that, and the surviving clause is a chronology — it tells the reader a prior claim was retracted and by what. It is mild (nothing currently true has to be reconstructed from it) and it is the pointer class, not the contract prose, which is why this is Low rather than Medium. No other added text narrates history: `grep -niE 'as of (review )?round|amendment|retract'` over the post-move spec returns nothing, and the surviving 2026-04-30 trace is `## Implementation checklist` bullet 2, which pre-dates this pass.

**Recommended change.** Trim the four words in both sites, or record a rejection reason if the pass judges the retraction signal worth the deviation — it is a judgement call and Worker 1 owns it.

#### `## Standing notes`' `cls._optimizer_field_map` enumeration undercounts the sites R2 has to sweep

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:638
- `cls._optimizer_field_map` survives in the present tense at three prose sites (`### B4`,
  `### B6`, `### B7`) naming a retired class attribute, …
```

Measured on the post-move spec: five mentions across four sentences in three sections — `:84` (B4, "shared with B7 (`_optimizer_field_map`)"), `:112` (B6, "present in `cls._optimizer_field_map`"), `:129` (B7, "Stash it as … / The walker reads `target_type._optimizer_field_map`" — two in one sentence), `:131` (B7, "read `_optimizer_field_map`"), and `:135` (B7 `**Test surface.**`, "Assert `_optimizer_field_map` is populated"). The drift table's `D22` counts four sites and does not include the `**Test surface.**` one. Since `## Standing notes` is explicitly written as R2's do-not-miss list, a count that reads as three locations will leave sites behind — `BUILD.md` `## Claims are proven mechanically` is the standing reason a stated count in a durable file is re-derived rather than asserted.

**Recommended change.** State it as "three sections / five mentions" or drop the number and name the sections plus `**Test surface.**`.

### DRY findings

- **Scaffolding duplication across the three optimizer rationale files — measured, and judged acceptable.** 8-word shingle overlap between this file and its two siblings, link-definition blocks stripped: 540 shingles against `spec-003-…-rationale.md` and 175 against `spec-002-…-rationale.md` (7,725 shingles in this file). Every run of 20+ is the shared file form — the opener, `## How to read this file`, `## Provenance of this record`'s three-way *Moved* / *Cut* / *Deleted* vocabulary, `## Standing notes`' framing. The longest is 89 shingles, and it is the "what the rationale-extraction pass did NOT do" paragraph. This is house form for a file class, not a fact told twice: each rationale is a standing doc that has to be readable without its siblings, and the three now describe their own provenance in one consistent vocabulary. **No change recommended** — recorded so the next cycle's reviewer does not re-derive it, and so the maintainer can see the cost if a fourth sibling makes it worth hoisting into `BUILD.md`.
- **The one substantive cross-file duplication is the B2 ordering invariant**, filed as a Low above. It is the only non-scaffolding run over 8 shingles.
- **Against the spec: no duplication.** Re-derived below; 92.3% of what left the spec exists in neither file, and every surviving run is a short marked quotation.
- **Against the later optimizer specs: no restatement.** Every entry touching `spec-016` / `spec-018` / `spec-029` / `spec-032` / `spec-033` / `spec-035` / `spec-047` names the owning spec and states the departure rather than transplanting its rules — the build plan's `**The scope trap specific to this spec.**` rule, correctly applied. `spec-003`'s ordering invariant is the one place the rule slipped.
- **Existence challenge: none raised.** The pass adds no abstraction, helper, registry, or indirection; it moves prose between two files.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → empty. `git diff --stat -- django_strawberry_framework/ tests/ examples/` → empty. `__all__` and the re-export list are unchanged, and the build plan's `## Build-wide context flags` declares package source, `tests/`, and `examples/` read-only for the whole cycle. No public export changed and none was authorized to.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applies — the diff is entirely docs, and one of the two files is an archived spec. Read both end to end.

- **Version strings / card IDs.** The spec carries no version or status header (confirmed against the HEAD copy: lines 1-5 are the title and `## Problem statement`), so nothing could drift. The rationale names `DONE-004-0.0.3` and "eleven patch versions ago", both matching the plan's Worker-0-verified card facts and `pyproject.toml`'s `0.0.14`.
- **KANBAN movement.** None; no card moved, and `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `docs/TREE.md` / `examples/fakeshop/db.sqlite3` are all clean in `git status --short`.
- **Every link resolves on disk, checked individually rather than eyeballed.** All 11 spec definitions and all 19 rationale definitions were `[ -e ]`-tested with the target resolved from the source file's own directory: `../GLOSSARY.md` ×10 and `appx/spec-004-…-rationale.md` from the spec; `../../../GOAL.md`, `../../README.md`, `../../GLOSSARY.md`, `../../builder/BUILD.md`, `../../builder/worker-1.md`, eight `../spec-NNN-….md` siblings, and two same-directory `appx/` rationale siblings. **30/30 present, 0 missing.** The two-level depth is handled correctly throughout. Reference integrity: spec 11 definitions / 11 distinct uses, rationale 19 / 19, **0 undefined references and 0 unused definitions** in either. Both files carry `<!-- LINK DEFINITIONS -->` and all ten canonical group headers in order (`check_trailing_commas.py --check` exit 0 on the spec, the rationale, and this artifact); the archived companions correctly file under `<!-- docs/SPECS/ -->` per `START.md`'s closed-list rule.
- **In-page anchors resolve.** Run through the repo's own slugger (`scripts/check_spec_glossary.py::github_anchor`) over the post-move spec's 15 headings: **0 duplicate slugs**, and both anchor-bearing rationale definitions land on a real heading — `#proposed-improvements` → `## Proposed improvements`, `#problem-statement` → `## Problem statement`. The em-dash hazard the pass avoided is real and the avoidance is correct. No file anywhere in the tree links to a `spec-004-…md#<anchor>` target, so the deleted `## Priority and ordering` heading left no external rot (`grep -rn 'spec-004-optimizer_beyond-0_0_3.md#'` → no hit outside the rationale itself).
- **Verbatim quotation is character-exact.** Every long quoted run in the rationale was tested against the whitespace-folded HEAD spec by exact substring match — the `strict=True` rejection sentence, the smoke-alarm clause, B6's "Fail-fast at startup…" closing, `## Priority and ordering`'s "Django handles duplicates gracefully…" sentence, B4's "works but reads awkwardly…" clause, and B3's profiling instruction. **All present verbatim in both HEAD and the rationale.** No fenced-code drop-in exists in either file (`grep -c '^```'` → 0 / 0), so the four-backtick outer-fence rule has nothing to apply to.
- **Archival.** Already performed before this cycle; the rationale was written **directly** to `docs/SPECS/appx/`, which is the archived-companion location `AGENTS.md` rule 26 names, rather than to `docs/` and moved. The terms CSV was not touched: `git diff docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-terms.csv` is empty and the path is absent from `git status --short docs/SPECS/appx/` (which shows only the new rationale as `??`).
- **No script-rendered doc regenerated**, so the staging-docstring check has no subject. No obsolete "coming soon" / "planned" wording was introduced; `## Proposed improvements`' proposal framing is pre-existing and is `D1`, explicitly left for R2.
- **`AGENTS.md` rule 27 holds in both files.** `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` → no match (exit 1) on both. Every source reference in the rationale is symbol-qualified or a bare symbol name; raw `path:NN` appears only in this per-cycle artifact, where `START.md` permits it.
- **No inline `](path)` link in either file** (`grep -P '\]\((?!#|https?:)'` → no match), so the reference-style convention is preserved, not merely unbroken.

### What looks solid

- **The move is a genuine cut, and every number in the report reproduces exactly.** I re-derived the shingle measurement independently (8-word shingles, link-definition blocks stripped, punctuation folded to whitespace, lowercased, HEAD copy read-only): HEAD **4,646**, post-move **3,643**, left the spec **1,685**, of those in the rationale **129 (7.7%)**, in neither file **1,556**, rationale × post-move-spec overlap **49**. Six figures, six exact matches. `BUILD.md` makes a stated count a claim to re-derive rather than accept, and this one survives re-derivation without a single discrepancy.
- **The qualitative half of that claim survives too, which is the part a count cannot establish.** I reconstructed the 129 surviving shingles as contiguous runs against the HEAD word stream: **26 runs, longest 20 shingles (~27 words), median 3.** Every one is a marked quotation in the rationale — the `strict=True` rejection sentence (20), the smoke-alarm win clause (17), B6's "Fail-fast at startup…" (11), the "pure polish item" sentence (9), the re-pointed ordering clause (9), and twenty short backticked fragments. **No paragraph, section, or fence survived as prose in both files.** This is the check `BUILD.md` warns a long grep phrase cannot do, and it passes on the run structure rather than on the total.
- **The 10-anchor constraint held, and I confirmed it per anchor rather than on the checker's exit code.** `grep -o "\[glossary-<anchor>\]" | wc -l` → **2 for every one of the ten** (1 body use + 1 definition), matching the report's table exactly. `check_spec_glossary.py --spec …` → `OK: 10 terms - all have glossary entries and at least one spec link.` exit 0, and `import_spec_terms --check` → `OK: 49 done cards have glossary links.` exit 0 with the DB still clean afterwards, so the card-wrap chain the constraint protects is intact end to end.
- **Both re-sitings landed in surviving contract prose, not in narration kept alive to hold a link** — the check the prompt asked me to make independently, and the one that would have been easiest to fake. `djangooptimizerextension` sits in `**Cache storage.**`'s "a dict on the `DjangoOptimizerExtension` instance": that sentence had to name the instance regardless of the link, because the instance is the thing the cache lives on, and it is the same sentence my Medium asks to extend. `queryset-diffing` sits on the `### B8` heading, matching what `### B4` already does with `metaoptimizer_hints`, and the rendered anchor is provably unchanged — I ran the repo's slugger on both spellings and `B8 — Queryset optimization diffing` and `B8 — [Queryset optimization diffing][glossary-queryset-diffing]` both produce `b8-queryset-optimization-diffing`. Neither re-siting added a word of narration.
- **The four disclosed rescues are all real and all verified against HEAD.** The `(name, value)` pair shape plus the omit-rather-than-default rule, the `dst_optimizer_planned` context key, the snake-cased field-map key, and the `check_schema` public-API sentence each lived only inside cut text, each is instruction rather than deliberation, and each is now stated as prose. The B7 rescue is the sharpest one: **both** of its carriers (the fence and the win paragraph) were being cut in the same pass, which is the exact intersection where a sweep loses a rule, and the pass caught it unaided.
- **Cutting the two self-contradicting fences was the right call and is argued correctly.** `### B6`'s fence walked `model._meta.get_fields()` while the paragraph two above it requires walking only Meta-exposed fields and says why; `### B2`'s fence keyed the elision on a bare field name while the paragraph three below it rejects exactly that with the aliased query that breaks it. In both cases the prose is what shipped. Correcting the fences would have left two statements of one rule to keep in step; cutting removes the contradiction. The rationale records both, which is where a reader who wonders what the fence said should find it.
- **Scope discipline against R2 is clean, and I walked all 28 drift rows to confirm it.** Every present-tense status claim the drift table names is still standing in the post-move spec, verbatim: `D1` (`:9`, `:15`), `D2` (`:13`), `D3`'s three-tuple-over-a-hash (`:19`), `D6` (`:23`), `D7` (`:25`), `D8` (`:27`), `D10` (`:39`), `D11`'s "clean fallback" (`:43`), `D14`'s two-arm probe (`:55`), `D15`'s four members (`:75`-`:78`), `D16` (`:84`), `D17`'s `_validate_meta` (`:86`), `D18`'s single key (`:98`), `D21`'s `check_optimizer` (`:123`), `D22`'s prose sites (`:84`, `:112`, `:129`, `:131`, `:135`), `D23` (`:131`), `D26`'s cache-safety **requirement** (`:149`), and `D27`'s dangling reference (`:169`). Nothing was quietly reconciled. The two drift rows the pass did discharge (`D5`'s falsified spike under rule 2, `D24`'s document structure as a side effect of the `## Priority and ordering` deletion) are both disclosed in the move report **and** recorded in the rationale's `## Standing notes`, which is the durable half.
- **The spec does not narrate its own history in its contract prose.** No amendment block, no retraction paragraph, no "as of round N" (`grep -niE 'as of (review )?round|amendment|retract'` → no hit). The only history-shaped text added is the two pointer clauses filed as a Low above, and both sit in pointer paragraphs rather than in a decision.
- **The pointer discipline is complete.** Eleven `[spec-004-rationale]` uses: one companion paragraph, one re-pointed `## Problem statement` clause, eight per-slice pointers, one definition. Every section that lost content carries one; the two cuts with no heading left (`**The win.**` and `## Priority and ordering`) are both named in the companion paragraph. `## Current state`, `## Non-goals`, `## References`, and `## Implementation checklist` lost nothing and correctly carry none.
- **The rationale is keyed to the spec and works as a review instrument.** Every entry opens with its spec section and a resolving anchor, and each carries the three things `BUILD.md` requires: the alternatives rejected with the reason each lost, every change the decision has undergone with the spec that caused it, and an explicit **Claims the spec no longer makes** list. I spot-checked B1, B3, B6, and B8 by reading the entry and then the section it names; each claim was checkable in one hop. The `## Provenance of this record` three-way vocabulary is the right correction to the mislabelling the spec-003 pass was pulled up on, and it is stated before the list uses it.
- **The disclosed hint was honest.** `### Notes for Worker 3` said a ninth rescue, if one exists, is in `### B1` or `### B3`. It is in `### B1`. A pass that names the place its own sweep is weakest, and is right about it, is doing the thing the isolation rule exists to force.

### Temp test verification

None. No temp test was written and none was warranted: the diff changes no code path, so there is nothing a test could exercise. `docs/builder/temp-tests/r1/` was not created. Every verification in this review is a read-only command over the two changed files, the read-only HEAD copy, or the repo's own checker scripts, and each is quoted above.

**Static helper.** `scripts/review_inspect.py` was **not** run, and the skip is recorded here per `worker-3.md` `## Static helper use`. `BUILD.md` `### When to run the helper during build` triggers it on a new `.py` file, a touched file under `optimizer/` or `types/`, or 30+/50+ new lines of logic. This diff adds no `.py` file and touches none — `git diff --stat -- django_strawberry_framework/ tests/ examples/` is empty — so no trigger fires. No shadow file was read or written for this item.

**Failability proofs.** The move report's `None; this pass introduced no new boundary.` is correct and verified rather than accepted: `git diff -- django_strawberry_framework/` is empty, so there is no boundary, guard, gate, or rejection path to prove. `worker-3.md`'s mandatory re-run floor is satisfied by an **empty re-run set**, which it permits only when the diff introduces no boundary meeting the floor — that condition holds here by measurement. **No boundary was re-run and none was accepted on a builder's record, because none exists.** Worker 3's source carve-out was correspondingly not exercised: no production file was mutated at any point in this pass.

**Hot-path budget.** Not owed. The plan declares `none`, the report says so, and the declaration is correct — nothing in this diff runs per request, per resolver, per row, per connection, or per outbound message.

**Floor verification.** Not owed. The plan declares scope `none`, and correctly: the diff touches no Django / Strawberry / channels integration seam.

**Coverage.** No `pytest` run, no `--cov*` flag in any form, at any point in this pass.

### Notes for Worker 1 (spec reconciliation)

The six items the move report carries into R2 all stand as written, and none was pre-empted — I verified each against the post-move spec. Adding to them:

1. **The Medium above is R1's, not R2's.** It is an over-cut caused by the move, so it is fixed by re-siting the rule in `**Cache storage.**` and completing the rationale's `### B1` *"Kept in the spec"* list, not by an R2 reconciliation edit. It interacts with `D6`, though: once `**Cache storage.**` states LRU eviction, `D6`'s reconciliation is narrower than the drift table anticipated — the remaining drift is the `256` bound and the quarter-eviction batching, not the policy. Worth carrying into R2's note.
2. **`D25` and `D28` are discharged and the move report does not say so.** Both lived inside `## Priority and ordering` and went with it: `D25`'s "B8 last … pure polish item" and `D28`'s half-retensed section. The rationale's `### The former ## Priority and ordering` entry records `D25` correctly as a claim the section may no longer make, and `D28` as the rejected retense alternative — so the durable record is complete. But `### Notes for Worker 1 (spec reconciliation) — carried into R2` lists only `D24` as already discharged, so R2 will go looking for two sentences that are gone. One line in that list closes it.
3. **`D5` left the spec with no extension-lifecycle statement, and I agree with the move report's read that the pointer is the right answer.** Recording the agreement rather than a second opinion: the build plan's anti-absorption rule, `spec-029` Decision 3's ownership, and the fact that `docs/README.md` and `docs/GLOSSARY.md` already carry the singleton-factory guidance all point the same way. What R2 should not do is transplant the corrected recommendation into spec-004 — that is the "summary of all three later specs" failure the plan warns about at `**The scope trap specific to this spec.**`.
4. **Escalated (contract-level, maintainer's call): `## Problem statement`'s surviving competitive positioning.** `:7` still reads "But strawberry-graphql-django stopped there — every request re-walks the tree, every forward FK emits a JOIN even when the parent row already carries the answer, and the optimizer's behavior is invisible to consumers outside of raw SQL logs." That is the B1, B2, and B5 win arguments in miniature, in the same document that just cut all eight for being competitive positioning. I am **not** filing it as an over- or under-cut finding, because `worker-1.md` puts "goals, non-goals" in the stays column and a problem statement is standard spec furniture, and because the document's own H1 is "Beyond strawberry-graphql-django" — the comparison is the spec's subject, not a digression from it. But whether a spec's problem statement may argue against a named competitor after the per-slice arguments were cut for doing exactly that is a consistency question about what this document is, which `BUILD.md` `### Contract-level findings are escalated as maintainer decisions` puts above a worker. **Resolution paths:** (a) leave it — a problem statement states the problem and this is the problem, and the sentence is load-bearing for why the eight slices exist; (b) trim the sentence to the package's own behaviour and move the comparison to the rationale's `**The win.**` entry, which already holds the same argument eight times over; (c) leave it and add one clause to the rationale's `**The win.**` entry recording that the problem statement was deliberately kept, so the next reader does not read it as a missed sweep. My own read is (a) or (c); (b) would leave `## Problem statement`'s first sentence naming the architecture it inherits with no statement of what it lacks.

### Review outcome

`revision-needed`.

One Medium and four Lows, none of them addressed or rejected. `worker-3.md`'s acceptance gate requires every High, Medium, and Low to be addressed or intentionally rejected with a recorded reason before `review-accepted`, and the Medium is the finding class this pass was dispatched to catch: a rule that lived only inside the uniformly-swept `**The win.**` class, is now stated in neither file, and is exactly the fifth rescue the move report itself predicted might exist in `### B1`.

Everything else in the pass is clean and unusually well evidenced. The move is a verified cut, not a copy — every one of the six shingle figures reproduced exactly on an independent re-derivation, and the 129 survivors decompose into 26 short marked quotations with no paragraph surviving in both files. All ten glossary anchors hold at one body link each, both re-sitings landed in surviving contract prose, all thirty link definitions resolve on disk at the two-level `appx/` depth, both in-page anchors resolve, the terms CSV was never opened, `import_spec_terms --check` still passes with the DB clean, rule 27 holds in both files, and all 28 drift rows were left standing for R2 except the two the pass discharged and disclosed. The revision is narrow: one clause restored to `### B1` `**Cache storage.**`, one line added to the rationale's B1 entry, and four small corrections in the rationale and the two pointer paragraphs.

Per the build plan's `### Deviation 2` corollary, this routes to **Worker 1**, not Worker 2 — the same two rules that remove Worker 2 from the perform pass remove it from the fix. Worker 1 applies the changes, sets `Status: planned` again, and returns the artifact here for a pass-2 review.

### Working-tree churn observed during this review — reported, not reverted

`git status --short` at the start of this pass matched the move report exactly. It changed mid-pass, and per `BUILD.md` `### Tracked binary / generated files` and `AGENTS.md` rule 34 nothing was reverted:

- **`M examples/fakeshop/db.sqlite3` — a concurrent session's kanban work, definitively not this cycle's.** Verified semantically rather than by file bytes: `git show HEAD:examples/fakeshop/db.sqlite3` into a scratch path outside the repo, then `sqlite3.iterdump()` on both. HEAD 9,593 statements, working tree 9,736; 172 statements only in the working tree, 29 only at HEAD. The added rows are `kanban_carditem` / `kanban_cardreference` / `kanban_card_labels` inserts timestamped `2026-08-07 19:53:06` whose text is about `PredicatePlan` and the graph substrate — i.e. card work for `docs/spec-068-graph_substrate-0_1_1.md`, the baseline-dirty file this cycle's plan already attributes to a concurrent session. **No spec-004 row, no glossary-link row, and no card-4 row is among them.** The build plan's `## Concurrent-writable tracked binary / generated files` premise that "all four are clean at pre-flight, so a diff here IS presently attributable" no longer holds; R3 should re-derive rather than inherit it, and must re-run `import_spec_terms --check` **after** the concurrent write rather than trusting either the pre-flight reading or this pass's.
- **`?? db.sqlite3` — a stray 0-byte untracked file at the repo root**, mtime `15:49`, no tables, not covered by `.gitignore` (which lists only `db.sqlite3-journal`). It is not a fakeshop database: `examples/fakeshop/config/settings.py` #"NAME": _kanban_db or (BASE_DIR / "db.sqlite3")" resolves `BASE_DIR` to `examples/fakeshop`, so no `manage.py` invocation from the repo root writes here. Its mtime precedes every command this pass ran that touches sqlite, but one read-only inspection command in this pass did open the path by name from the repo root, which would have created it had it not already existed — so **attribution is genuinely uncertain and is reported as uncertain rather than guessed.** Left in place either way: it is untracked, empty, and reverting a file that may be a concurrent session's is the failure `AGENTS.md` rule 34 exists to prevent. The maintainer may want it deleted and `.gitignore` widened; that is a decision, not a worker's tidy-up.

Neither file is in any residual item's writable set, and neither affects any finding above. `docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, and `KANBAN.html` remained clean throughout.

---

## Build report (Worker 1, apply-changes pass)

Per the build plan's `### Deviation 2` corollary, an R1 `revision-needed` routes to Worker 1: the same two rules that make Worker 1 the only role that may perform the move make it the only role that may fix it. `Status:` is `planned` on return, which Worker 0 reads as "dispatch Worker 3" for a pass-2 review. Worker 3's `## Review (Worker 3)` section above is untouched, as is every prior entry.

**One Medium and four Lows, all five fixed; none rejected.** The Medium's destination decision is argued below rather than asserted, because the prompt and the finding both make it the pass's substantive call.

### The Medium — where the fix landed, and which side of the R1/R2 line it sits on

**Restated in the spec, in `**Cache storage.**`, under the load-bearing carve-out.** Not in the rationale, and not in both.

The line the prompt draws is between *restoring a true statement the sweep dropped* (R1's) and *restating the contract against HEAD* (R2's). The eviction discipline is unambiguously the first:

- **It is instruction, not deliberation.** `worker-1.md`'s test is whether an implementer needs the sentence to build the thing. A bounded cache must decide what it drops; "bounded-size dict" alone leaves that choice unmade, and clear-all or insert-order eviction satisfies the surviving sentence as well as LRU does. A rationale entry cannot carry it, because Worker 2 never reads the rationale — that is the whole point of the move — so a builder's copy of the rule has to be the spec's.
- **Rule 2 does not reach it.** The clause was **true** when cut and is true at HEAD, so "delete falsified prose" has no application; the deletion was a sweep artifact, and git history is reserved for prose the decisions falsified.
- **It is the same class as the four disclosed rescues**, and it is the fifth one this pass's own `### Notes for Worker 3` invited a search for, in one of the two sections that note named. Treating it differently from the `(name, value)` pair shape or the `dst_optimizer_planned` key would be inconsistent on the same test.

**What was deliberately NOT written, so R2 is not pre-empted.** `D6`'s reconciliation is R2's, and the restored clause states the **policy only** — no `_MAX_PLAN_CACHE_SIZE = 256`, no `OrderedDict`, no `move_to_end`, no quarter-batch eviction, no percentage, no reference to the cut paragraph. Those are present-tense claims about HEAD and belong to the reconciliation item under the same boundary this pass drew for the other nine surviving status claims. Worker 3's own note is right that `D6` is now **narrower** than the drift table anticipated: the remaining drift is the bound and the eviction batching, not the policy. The rationale's B1 entry says so in the durable file, in one sentence, so R2 does not have to infer it from an artifact that closes with the cycle.

**The siting.** The finding asked that the `functools.lru_cache` rejection read as "not the decorator" rather than "not the policy". The eviction rule is now stated **before** the rejection, and the rejection opens `Hand-roll the LRU rather than reaching for functools.lru_cache` — so the word LRU appears on the policy side of the sentence and the rejection is scoped to the decorator by its own verb. The `djangooptimizerextension` glossary link sits in the untouched first sentence of the paragraph and was not disturbed; it still holds at exactly one body use.

### Findings, one row each

| Finding | Disposition | Where |
|---|---|---|
| **Medium** — B1's eviction discipline over-cut | **Fixed.** Restated as a rule in `**Cache storage.**`; the rationale's `### B1` entry gains a `**Kept in the spec**` block recording the rescue, why it is instruction, and that the bound and batching are R2's | spec `:23`; rationale `### B1` |
| **Low** — card-import chain misattributed to `check_spec_glossary.py` | **Fixed.** `import_spec_terms` is now named as the rebuilder (from the companion CSV, never the spec body) and `check_spec_glossary.py` as the gate a dropped body link trips; the "re-site the link, never edit the CSV" consequence is stated | rationale `## Standing notes` |
| **Low** — B2 entry restates spec-003's invariant then denies it | **Fixed** by the DRY-correct branch the finding named: the restatement is cut to the fact of the departure and the false disclaimer goes with it. The entry now names the departure and points at the owning spec, matching what the neighbouring entries do with `spec-033` / `spec-035` | rationale `### B2` |
| **Low** — two pointer paragraphs carry a chronological retraction | **Fixed at both sites.** "the recommendation a later Strawberry release inverted" → "the consumer recommendation it reached". Rule 1's obligation (name what was moved and where) is still discharged by the surviving noun phrase; the chronology is gone | spec `:3`, `:29` |
| **Low** — `cls._optimizer_field_map` enumeration undercounts R2's worklist | **Fixed** by the finding's second option rather than its first, deliberately — see below | rationale `## Standing notes` |

**Why the count was dropped rather than corrected to five.** The finding offered "three sections / five mentions" or "drop the number and name the sections plus `**Test surface.**`". Re-derived mechanically: `grep -o '_optimizer_field_map' | wc -l` returns **6**, across **5** sites, in **3** sections — `### B7` `**Mechanism.**` names it twice in two sentences. So "five mentions" is itself off by one under a literal count, and a durable file asserting a number that changes with how you count it re-creates the defect. The bullet now states **five sites across three sections**, names every one including `**Test surface.**`, tells the reader to count rather than trust the list (`BUILD.md` `## Claims are proven mechanically`), and records that `**Test surface.**` is absent from the build plan's own `D22` row.

### Files touched

- `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` — 3 edits, all in-line replacements of text this cycle already changed: the `**Cache storage.**` eviction rule, and the two pointer-paragraph retraction clauses. `git diff --stat` is **unchanged at 28 insertions / 171 deletions**, which is itself the evidence that no new line was added or removed.
- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — 7 edits: the two Medium blocks (B1 entry, `**The win.**` entry), the two Low rewrites, and three consistency corrections the Medium forced, listed next.

**Three corrections the Medium forced elsewhere in the rationale**, made because leaving them would have introduced a fresh inaccuracy into a durable file:

1. `## Provenance of this record`'s **Restated in the spec, not moved** bullet said "four rules … all four stayed". It is five, and the eviction discipline is now listed among them.
2. `## Standing notes`' `### The **The win.** cut …` said "Three rules were rescued". It is four, and the fourth is named.
3. That same note gained two sentences on **why** the fourth hid where it did — `### B1`'s was the class's most technical member, so the uniformity that justified a wholesale cut is what buried an instruction inside it — with the generalisable rule stated: a class cut uniformly is read member by member for the one sentence that is not of its class.

**On `worker-1.md` rule 4 (`the rationale file is append-only during the build`).** These seven edits rewrite text this same pass wrote hours earlier, not settled deliberation from an earlier round. Rule 4 governs a review round's *new decisions* appending beside old ones; correcting the current pass's own draft after its own review is what the apply-changes pass is for, and the alternative — appending a correction block that contradicts the paragraph above it — is the "half-reconciled, reader cannot tell which half is current" failure `worker-1.md` `## Review-round custody` names. Recorded rather than assumed.

### Validation run — every result quoted verbatim

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` → `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**. Character-identical to the baseline. Re-run a second time after the mid-pass working-tree churn (below); same result.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md docs/builder/bld-004-r1-rationale_move.md` → **exit 0** on all three files.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0**. Read-only form only; the writing form was never invoked. Re-run after the churn; same result.
- **Per-anchor 10-anchor constraint, re-derived not inherited.** `grep -o "\[glossary-<anchor>\]" | wc -l` → **2 for every one of the ten** (1 body use + 1 definition). The Medium's fix landed in `**Cache storage.**` beside `djangooptimizerextension`, the anchor the build plan flagged as the cycle's highest-risk, and it still reads 2.
- **Byte / line count.**

| | lines | bytes |
|---|---|---|
| spec at Worker 3's review | 216 | 26,409 |
| spec **now** | **216** | **26,480** (+71) |
| spec at HEAD (pre-move) | 359 | 33,928 |
| net move + revision | **-143** | **-7,448 (-21.9%)** |
| rationale at Worker 3's review | 728 | 50,703 |
| rationale **now** | **762** | **53,505** (+2,802) |

  The spec's line count is **unchanged at 216** — all three spec edits replaced text inside existing lines.
- `grep -c '^```'` → spec **0**, rationale **0**. No fence was introduced.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files → **no match** (exit 1). Rule 27 still holds.
- `grep -nP '\]\((?!#|https?:)'` over both files → **no match** (exit 1). No inline `](path)` link; reference-style preserved.
- **Reference integrity and disk-check, re-run after the churn:** spec **11 definitions / 11 distinct uses**, rationale **19 / 19**, **0 undefined references, 0 unused definitions**, and **0 of 30 definition targets missing on disk** with each path resolved from its own source directory. This re-run matters this pass: the concurrent session renumbered and moved several `docs/SPECS/` files while the pass was running, and the rationale links eight `../spec-NNN-….md` siblings.
- **In-page anchors.** The rationale still uses exactly two, `#problem-statement` and `#proposed-improvements`, and no new one was added — deliberately, because the em-dash slugger ambiguity this file documents applies to its own `### B1 — AST-cached plans` heading. The `**The win.**` entry's cross-reference to the B1 entry is therefore a **named textual pointer, not a link**. Run through the repo's own `check_spec_glossary.py::github_anchor` over the post-revision spec's 15 headings: **0 duplicate slugs**, and both targets resolve.
- `grep -niE 'as of (review )?round|amendment|retract|inverted|a later strawberry'` over the spec → **no match** (exit 1). The Low-3 fix is verified by absence, not asserted: the spec now narrates no history anywhere, pointer paragraphs included.
- `git diff --stat -- django_strawberry_framework/ tests/` → **empty**. No source, test, or example file was touched; no `pytest`, no `ruff` (no `.py` file changed), no coverage-shaped flag in any form.
- No `git stash`, `checkout`, `restore`, `worktree`, `commit`, or branch operation at any point.

### Working-tree churn observed during this pass — reported, not reverted

The baseline-dirty set grew a **third** time, mid-pass, and per `AGENTS.md` rule 34 nothing was reverted or `git checkout`-ed. Worker 0 owns appending it to the plan; this is the report.

Beyond the plan's `### Second growth` list, `git status --short` now also carries: `M BACKLOG.md`, `M TODAY.md`, `M multi-root-schedule-graph-reproduction.md`, `M examples/fakeshop/apps/products/schema.py`, `M examples/fakeshop/test_query/test_products_api.py`, and — the significant one — **the concurrent `NEXT.md` flow completed its spec renumber**: `D docs/SPECS/spec-053-fieldset-0_1_1.md`, `D docs/SPECS/spec-054-search_fields-0_1_2.md`, `D docs/spec-068-graph_substrate-0_1_1.md` and its terms CSV, against new `?? docs/SPECS/spec-053-graph_substrate-0_1_1.md`, `?? spec-054-fieldset-0_1_1.md`, `?? spec-055-search_fields-0_1_2.md` and a new terms CSV. HEAD also moved to `c62e990a`.

Two consequences a later pass must not inherit from an earlier reading:

- **The rationale's eight `../spec-NNN-….md` sibling links are now exposed to that renumber.** They were re-disk-checked *after* the churn and all 30 definition targets resolve — none of this cycle's links points at a renumbered file. R2 and R3 must re-run that check themselves rather than quoting this one; the renumber is live.
- **`examples/fakeshop/db.sqlite3` is dirty from the concurrent writer**, as Worker 3 already established semantically. `import_spec_terms --check` was therefore re-run **after** the churn rather than before, and still returns `OK: 49 done cards have glossary links.`

`docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md`, and `KANBAN.html` remained clean throughout. The stray 0-byte untracked `db.sqlite3` at the repository root is still present, still untracked, still empty, and still left alone.

### Notes for Worker 3 (pass 2)

- **The one judgement to audit is the Medium's destination**, not whether a clause was added. The argument is in `### The Medium — where the fix landed` above; the check is to read `### B1` end to end with no access to the rationale and confirm a builder can now state what the cache drops when it fills, then confirm the same reading yields **no** claim about the bound or the eviction batch size, which are `D6`'s and R2's.
- **Three edits were made that no finding asked for**, all in the rationale, all forced by the Medium: the provenance count four → five, the standing-note count three → four, and the two sentences on why the fourth rescue hid. They are listed under `### Files touched` and are the place to look for an over-correction.
- **The Low-4 fix deviates from the finding's first option and takes its second**, because the stated count of five does not survive a literal `grep -o` (six occurrences across five sites). The reasoning is recorded above; if the deviation is wrong the fix is one sentence.
- **Two claims worth re-deriving rather than reading**, both cheap: the per-anchor count of 2 (the proof the 10-anchor constraint survived a second edit in the same paragraph as the highest-risk anchor), and the 30/30 link-target disk check, which is no longer a formality now that the sibling specs are being renumbered underneath it.
- The six items carried into R2 in the first move report all still stand, plus Worker 3's own two additions (`D25` / `D28` are discharged; `D6` is now narrower). Nothing from this pass was staged for later without being written down.

### Spec changes made (Worker 1 only)

Cited against the post-revision spec. All three are in-line replacements; no line was added or removed.

| Spec location | Change | Reason |
|---|---|---|
| `:3` | "the recommendation a later Strawberry release inverted" → "the consumer recommendation it reached" | Worker 3 Low — `BUILD.md` `## Spec rationale extraction`: the spec never narrates its own history. Rule 1's "name what was moved and where" is still satisfied. |
| `:23` | `**Cache storage.**` now states least-recently-used eviction at the bound and scopes the `functools.lru_cache` rejection to the decorator | Worker 3 Medium — restoring a true clause the `**The win.**` sweep dropped, under `worker-1.md`'s load-bearing carve-out. Policy only; the bound and eviction batching are `D6`/R2's. |
| `:29` | "the consumer recommendation a later Strawberry release inverted" → "the consumer recommendation it reached" | Same as `:3`. |

**Spec status-line re-verification** (`worker-1.md` `## Spec status-line re-verification`, re-run this spawn): spec-004 still carries **no** `Status:` / owner / target-release / predecessor header block — lines 1-5 are the title, the companion-pointer paragraph, and `## Problem statement`. Nothing in them is a status line this build has falsified, so no header edit was owed. The `:3` edit is to the pointer paragraph's content, not to a status line.

---

## Review (Worker 3, pass 2)

Read in order, as the prompt directs: `docs/builder/worker-3.md` (full), `AGENTS.md`, `START.md`, `docs/builder/BUILD.md` (`## Spec rationale extraction` and `### Who reads it, and when` re-read verbatim), `docs/builder/ARTIFACT.md`, `docs/README.md`, `examples/fakeshop/test_query/README.md`, `docs/builder/build-004-optimizer_beyond-0_0_3.md` **including the new `### Third growth` section**, `worker-1.md` `### Performing the rationale move`, this artifact end to end (Worker 1's plan, the move report, my own pass-1 `## Review (Worker 3)`, then `## Build report (Worker 1, apply-changes pass)`), the post-revision spec, the post-revision rationale, and the pristine HEAD spec obtained read-only as `git show HEAD:docs/SPECS/spec-004-optimizer_beyond-0_0_3.md > <scratchpad outside the repo>/spec-004-HEAD.md`. No `git stash` / `checkout` / `restore` / `worktree` at any point, and no prior entry was edited.

`HEAD` re-derived this spawn rather than quoted: **`c62e990a545ed8690f4672c3bf298b466e8ada51`**. The HEAD spec blob is still **33,928 bytes / 359 lines**, so the baseline the move was measured against has not moved under the cycle. `git log -1 -- <path>` over the four cycle paths shows the newest commit reaching `spec-004` is still `20a9752f`, and the rationale, this artifact, and the build plan are still untracked — this cycle's work was **not** swept into `c62e990a`.

**Nothing in this section is quoted from the apply-changes report.** Every figure below was re-derived from the files on disk this spawn.

### High:

None.

### Medium:

None.

#### Disposition of the pass-1 Medium — closed, and the destination argument holds

**Closed.** `### B1` `**Cache storage.**` now reads, in full:

```docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:23
**Cache storage.** Use `self._plan_cache` — a dict on the [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] instance. Use a simple bounded-size dict that evicts its **least-recently-used** entries once it reaches its bound. Hand-roll the LRU rather than reaching for `functools.lru_cache`, since the cache key includes a model class which is not hashable by `lru_cache`'s default.
```

**The destination, graded rather than confirmed.** All three legs of Worker 1's argument check out, and the third is the decisive one:

1. *The clause was true when cut, so rule 2 never reached it.* Verified against the read-only HEAD copy: `### B1` `**The win.**` opened `An LRU cache keyed on (document_hash, directive_vars, target_model) turns 99% of repeated queries into a dictionary lookup.` The drift table's `D6` records HEAD as an `OrderedDict` LRU. True when written, true now — `worker-1.md` rule 2 ("delete, do not move, prose the current decisions have falsified") has no purchase.
2. *It is instruction, not deliberation.* `worker-1.md` `### Performing the rationale move`, "What STAYS": *"Implementation-relevant rationale — the 'why' that changes HOW a thing is built"*, closing with **"When it is unclear whether a sentence is deliberation or instruction, it stays."** A bounded cache must decide what it drops; the surviving sentence without the policy is satisfied equally by clear-all and by insert-order eviction.
3. *Worker 2 never reads the rationale, so a builder's copy of a rule must be the spec's.* This is not Worker 1's inference — it is `BUILD.md` `### Who reads it, and when` verbatim: **"Worker 2 never reads it. That is the point of the move."** A rationale entry is structurally incapable of carrying an instruction to an implementer. This leg alone decides the destination, and it decides it correctly: the fix could not have gone in the rationale, and putting it in both would be the "fact told twice goes stale in one of them" defect the build plan's DRY rule names.

**The policy-only line was actually held — verified by absence, mechanically.** `grep -niE 'lru|evict|bounded|\b256\b|ordereddict|move_to_end|quarter'` over the post-revision spec returns exactly **two** lines: `:23` above, and `:27`, whose `lru_cache.cache_info()` mention is pre-existing HEAD text this cycle never touched. **No `_MAX_PLAN_CACHE_SIZE`, no `256`, no `OrderedDict`, no `move_to_end`, no batch or quarter eviction anywhere in the spec.** So the fix restates a policy the spec already carried at HEAD and adds no present-tense claim about HEAD that the pre-move spec did not already make. It has **not** pre-empted `D6`; it has narrowed it, by exactly the amount stated under `### Notes for Worker 1` below.

One residue worth naming rather than filing: `**Cache storage.**`'s plural — "evicts its least-recently-used **entries**" — is generic and is compatible with both single-entry and batch eviction, so it neither states nor forecloses `D6`'s batching half. Recorded in the R2 handoff, not as a finding.

**The siting the finding asked for landed.** The finding asked that the `functools.lru_cache` rejection read as "not the decorator" rather than "not the policy". The policy now precedes the rejection and the rejection opens `Hand-roll the LRU rather than reaching for functools.lru_cache` — the word LRU is on the policy side and the rejection is scoped to the decorator by its own verb. The `djangooptimizerextension` glossary link sits in the paragraph's untouched first sentence and still resolves at exactly one body use (re-derived below).

The rationale's half of the fix is present and complete: a `**Kept in the spec — the eviction discipline, which lived only in the cut `**The win.**` opening.**` block at `:224`-`:234`, which states why it is instruction and hands the bound and the batching to the reconciliation item in its closing sentence.

### Low:

#### The `**The win.**` standing note's survival summary is wrong about both survivals, in the sentence this pass edited

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:710
Four rules were rescued out of that class and its neighbouring fences — the snake-cased field-map
key, the `dst_optimizer_planned` context key, the cache key's `(name, value)` pair shape, and the
plan cache's least-recently-used eviction discipline — plus one whole paragraph kept because it
carried a public API.
```

The four-rule list is now correct — that is the unasked-for edit, and it is right. The clause after the dash is not, and it is wrong about **both** paragraphs that survived the sweep. Verified against the read-only HEAD copy:

- **HEAD `### B6` `**The win.**` is one paragraph of three sentences.** Only the first survived, as `**Public API.**` at spec `:108`; sentences two and three (`Fail-fast at startup instead of N+1-fast in production. None of the existing libraries ship this.`) were cut. So the public-API survival is **a sentence, not a whole paragraph** — which is what this file's own `**The win.**` entry says at `:128` ("**B6's first sentence**, relabelled `**Public API.**`").
- **HEAD `### B8` `**The win.**` is one paragraph of two sentences, and both survive verbatim** at spec `:141`. It *is* the whole paragraph — but it was kept because it names no competitor and is the slice's problem statement, **not** because it carried a public API. This file says so itself at `:124`.

So the note collapses two distinct survivals with two distinct justifications into one item that describes neither, and B8's whole-paragraph survival drops out of the note entirely. That matters because the same entry flags B8's surviving paragraph as carrying a **present-tense status claim the reconciliation item owns** (`:127`), and `## Standing notes` is the file's own durable do-not-miss list for that item — its status-claim enumeration at `:649`-`:677` does not list B8's paragraph either, so after this note it appears in no R2-facing list at all.

It is also the same defect class this pass's own Low-4 fix closed two lines earlier, under the principle that fix established: *a durable file asserting a summary that does not survive re-derivation re-creates the defect.* Three tallies of one set now coexist in the file — `## Provenance of this record` says **five** restated rules (counting `check_schema`), this note says **four rules plus one paragraph**, and the `**The win.**` entry says **two paragraphs survived, one whole and one in part**. They reconcile only if the reader already knows which is loose.

**Recommended change.** One clause: `… — plus two of the eight paragraphs, B8's whole (it names no competitor) and B6's first sentence (it is the only statement of the audit's public API).` Or drop the summary and point at the `**The win.**` entry, which is already correct.

**Test expectation.** None; no behavior changes. The verification is the one applied above: read the `**The win.**` entry and the HEAD paragraphs side by side and confirm the note's summary matches both.

#### Disposition of the four pass-1 Lows — all four closed, one by the deviation, and the deviation is right

**Low-1, card-import chain misattributed — closed, and the replacement is correct against source.** `## Standing notes` `:681`-`:686` now reads that `import_spec_terms` is what a Done card's glossary-link set is rebuilt from and that **it reads the companion `*-terms.csv`, never the spec body**, with `scripts/check_spec_glossary.py` named as the gate a dropped body link trips, and the "re-site the link, never edit the CSV" consequence stated. Verified at source rather than accepted: `examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py` #"Import spec companion CSVs into glossary mentions and done-card links" resolves the card's `SpecDoc` path through `::_terms_path` (sibling `*-terms.csv` first, then `appx/`) and builds each `CardPlan` from `self._load_rows(terms_path)` — CSV rows, never the spec body. The gate's own output confirms the other half: `OK: 10 terms - all have glossary entries and at least one spec link.`

**Low-2, the B2 entry restating spec-003's invariant then denying it — closed, by the DRY-correct branch, and the closure is measurable.** The restatement and the false disclaimer are both gone; `:305`-`:311` now names the departure (shared helper, ordering invariant, projection gate) and points at `spec-003` for the rule. Re-measured independently — 8-word shingles, link-definition blocks stripped, punctuation folded, lowercased — overlap with `spec-003-…-rationale.md` fell **540 → 521**, and the 17-shingle contiguous run I filed the finding on is **gone**. Reconstructing the overlap as contiguous runs over this file's word stream gives **36 runs, longest 89, then 63 / 59 / 47 / 37 / 30 / 29 / 17 / 16 / 14** — and every one of those is the shared file form (`## How to read this file`, the *Moved* / *Cut* / *Deleted* vocabulary, the "what the pass did NOT do" paragraph, `## Standing notes`' framing). **There is now no substantive non-scaffolding run against either sibling rationale.**

**Low-3, the pointer paragraphs' chronological retraction — closed at both sites, and verified by absence.** Both now read "the consumer recommendation it reached". `grep -niE 'as of (review )?round|amendment|retract|inverted|a later strawberry|later release|no longer|used to |formerly|previously|has since|once (said|read|recommended)'` over the whole post-revision spec returns **one** line — `:3`, whose only hits are "the **former** `## Priority and ordering` section" and "every claim the spec once made and may **no longer** make". Both are rule-1 pointer vocabulary naming what was moved and where, and both match `spec-003:3`'s form. **No retraction, no amendment block, no chronology survives anywhere in the spec.**

**Low-4, the `_optimizer_field_map` undercount — closed, and Worker 1's deviation from my finding is correct.** I re-derived it this spawn rather than reading either number:

| unit | value | command |
|---|---|---|
| **occurrences** | **6** | `grep -o '_optimizer_field_map' <spec> \| wc -l` |
| **sites (matching lines)** | **5** | `grep -c '_optimizer_field_map' <spec>` — `:84`, `:112`, `:129`, `:131`, `:135` |
| **sections** | **3** | `### B4`, `### B6`, `### B7` |

Per-line occurrence counts: `:84` → 1, `:112` → 1, **`:129` → 2**, `:131` → 1, `:135` → 1. Spellings: `cls._optimizer_field_map` ×2, `target_type._optimizer_field_map` ×1, bare `_optimizer_field_map` ×3.

**My pass-1 count of "five mentions across four sentences" was itself wrong**, and wrong in exactly the way `BUILD.md` `## Claims are proven mechanically` warns about: `:129` carries the symbol twice, in **two** sentences (`Stash it as cls._optimizer_field_map.` and `The walker reads target_type._optimizer_field_map instead of …`), and I collapsed them into one. Worker 1 re-derived rather than accepting my number, found the discrepancy, and took the finding's *second* option — the corrected bullet at `:657`-`:664` states **five sites across three sections**, names every one including the `**Test surface.**` site, tells the reader to count rather than trust the list, and records that `**Test surface.**` is absent from the build plan's own `D22` row. That is the right call: "five mentions" was the ambiguous unit, and a durable file asserting a number that changes with the counting rule re-creates the defect it was fixing. **The bullet's list matches my re-derivation exactly, site for site.**

### DRY findings

- **The one substantive cross-file duplication is gone.** Measured above: 540 → 521 shingles against `spec-003-…-rationale.md`, the 17-shingle ordering-invariant run eliminated, and every remaining run of 8+ against either sibling is house form for the rationale file class. The pass-1 DRY judgement that the scaffolding overlap is acceptable stands unchanged and is not re-litigated here.
- **The revision introduced no new duplication against the spec — re-derived, not inferred.** This is the check that matters, because the fix restates a rule in the spec *and* explains it in the rationale, which is the shape most likely to tell a fact twice. Re-running the full shingle measurement against the read-only HEAD copy:

| measure | pass-1 reading | now | note |
|---|---|---|---|
| shingles at HEAD | 4,646 | **4,646** | HEAD blob unmoved |
| shingles post-move | 3,643 | **3,657** | +14, the B1 restatement |
| left the spec | 1,685 | **1,692** | the reword broke 7 runs across its own seam |
| **of those, present in the rationale** | 129 | **129** | **unchanged** |
| of those, present in neither file | 1,556 | **1,563** | +7, matches |
| **rationale × post-move-spec overlap** | 49 | **49** | **unchanged** |
| rationale total shingles | 7,725 | 8,203 | +478, the new prose |

  The two load-bearing figures — surviving-in-the-rationale and rationale-versus-spec overlap — are **bit-for-bit unchanged across 478 new rationale shingles and 71 new spec bytes.** The revision copied nothing back into the spec and restated nothing of the spec into the rationale. The spec states the rule; the rationale states why it is a rule; the two share no 8-word run.
- **The rationale's `:232` sentence names the drift category it hands off ("its bound, and that it evicts a batch rather than one entry … belongs to the reconciliation item, not here") without stating the values.** This is superficially the shape of the Low-2 defect — describing a thing while saying it is not described here — but it is not the same thing and is not filed: naming a category to hand off is `## Standing notes`' declared job and it does so for nine other items, whereas Low-2 stated a full invariant near-verbatim from a sibling rationale and then denied it. Recorded so the next reviewer does not re-derive the distinction.
- **Existence challenge: none raised.** The revision adds no abstraction, helper, registry, or indirection; it edits prose in two files.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are unchanged, and no public export was authorized to change: the build plan's `## Build-wide context flags` declares package source, `tests/`, and `examples/` read-only for the whole cycle.

**`git diff --stat -- django_strawberry_framework/ tests/ examples/` is no longer empty, and every entry is attributable to the concurrent session, not to R1.** Each was opened and read:

| path | change | attribution |
|---|---|---|
| `django_strawberry_framework/optimizer/predicates.py` | 1 line, a module-docstring reference `docs/SPECS/spec-054-search_fields-0_1_2.md` → `spec-055-search_fields-0_1_2.md` | the concurrent `NEXT.md` spec renumber (`### Third growth`) |
| `examples/fakeshop/apps/products/schema.py` | 1 line, `TODO-BETA-060-0.1.5` → `TODO-BETA-061-0.1.5` | the concurrent card-id sweep (`### Second growth`) |
| `examples/fakeshop/test_query/test_products_api.py` | 1 line, the same `060` → `061` token | same |
| `examples/fakeshop/db.sqlite3` | binary | the concurrent kanban writer — semantics below |

**Reported, never reverted** (`AGENTS.md` rule 34). None of the three text changes touches optimizer behaviour, spec-004's surface, or anything this cycle wrote; `predicates.py` in particular is `### Third growth`'s named concurrent source edit, and its diff is a renumbered spec filename in a docstring, so it is not evidence about spec-004 in either direction.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed clean in `git status --short`.

### Documentation / release sanity

Applies — the diff is entirely docs and one of the two files is an archived spec. Both were read end to end this spawn.

- **The three baseline checkers, re-run rather than quoted.**
  - `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` → `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0** — character-identical to the build plan's pre-flight baseline.
  - `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md docs/builder/bld-004-r1-rationale_move.md` → **exit 0** on all three.
  - `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0**. **Read-only form only**; the writing form was never invoked in this pass, and the run happened *after* the concurrent DB churn rather than before it.
- **The 10-anchor constraint, re-derived per anchor rather than on the checker's exit code.** `grep -o "\[glossary-<anchor>\]" | wc -l` → **2 for every one of the ten** (1 body use + 1 definition): `configurationerror`, `djangooptimizerextension`, `djangotype`, `fk-id-elision`, `metaexclude`, `metafields`, `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `queryset-diffing`. All ten are single-carrier, as the build plan requires. **The Medium's fix landed in `### B1` `**Cache storage.**` — the same paragraph, one sentence away from the re-sited `djangooptimizerextension` link the build plan flagged as the cycle's highest-risk anchor — and that anchor still reads 2.** The terms CSV is untouched: `git status --short docs/SPECS/appx/` shows only the new rationale as `??`, and the CSV's ten rows still match the ten anchors one-to-one.
- **Every link definition resolves on disk — re-run this spawn, because the reading has an expiry.** Resolved from each source file's own directory with an existence test per path: spec **11 definitions / 11 distinct uses**, rationale **19 / 19**, **0 undefined references, 0 unused definitions, 0 of 30 targets missing**. This is the live hazard the prompt names, and it is now confirmed against a tree where the renumber has **completed and committed** (`c62e990a`): `spec-053-fieldset` and `spec-054-search_fields` are gone, `spec-053-graph_substrate` / `spec-054-fieldset` / `spec-055-search_fields` are new. **None of the rationale's eight `../spec-NNN-….md` sibling links points at a renumbered file** — they are 002, 003, 004, 016, 018, 029, 032, 033, 035, 047, all stable and all present. R2 and R3 re-run this rather than quoting it; the renumber is still live.
- **In-page anchors resolve, and the em-dash hazard is still avoided.** Running the repo's own `scripts/check_spec_glossary.py::github_anchor` over the post-revision spec's **15** headings: **0 duplicate slugs**. Both anchor-bearing rationale definitions land on real headings — `#proposed-improvements` → `## Proposed improvements`, `#problem-statement` → `## Problem statement`. No new in-page anchor was added, which is correct: the eight slice headings still slug to one hyphen under the repo's slugger (`b1-ast-cached-plans`) where GitHub emits two.
- **Pointer discipline is intact after the revision.** Eleven `[spec-004-rationale]` occurrences: the companion paragraph (`:3`), the re-pointed `## Problem statement` clause (`:9`), eight per-slice pointers (`:29`, `:47`, `:63`, `:90`, `:100`, `:121`, `:133`, `:151`), and the definition (`:202`). Every section that lost content carries one; `## Current state`, `## Non-goals`, `## References`, and `## Implementation checklist` lost nothing and correctly carry none.
- **The spec's structural properties survived a second edit.** 216 lines / **26,480 bytes** (was 26,409 at my pass-1 review; **+71**, and the line count is unchanged, so all three edits are in-line replacements). `git diff --stat` is still **28 insertions / 171 deletions** — the same hunk shape, which is independent evidence that no line was added or removed. All **24** added lines were read individually and every one is accounted for by the move plus the three revision edits; `grep -c '^```'` → **0 / 0** in both files, so no fence was reintroduced.
- **`AGENTS.md` rule 27 and the reference-style convention hold in both files.** `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` → no match (exit 1). `grep -nP '\]\((?!#|https?:)'` → no match (exit 1). Raw `path:NN` appears only in this per-cycle artifact, where `START.md` permits it.
- **Version strings / card IDs / KANBAN.** The spec carries no version or status header, so nothing could drift; the rationale's `DONE-004-0.0.3` and "eleven patch versions ago" still match `pyproject.toml`'s `0.0.14`. **No card moved and this cycle wrote no DB.** `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, and `examples/fakeshop/db.sqlite3` are all dirty *from the concurrent session* — the build plan's `### Third growth` already records that `## Concurrent-writable tracked binary / generated files` now has no clean member, so their dirtiness proves nothing either way and I established attribution semantically instead (below). `docs/GLOSSARY.md` is **clean**.
- **No script-rendered doc was regenerated**, so the staging-docstring check has no subject, and no obsolete "coming soon" / "planned" wording was introduced — `## Proposed improvements`' proposal framing is pre-existing `D1` and is deliberately R2's.
- **Archival unchanged.** The rationale was written directly to `docs/SPECS/appx/`, which is the archived-companion location `AGENTS.md` rule 26 names. Its definitions correctly file under `<!-- docs/SPECS/ -->` per `START.md`'s closed-list rule.

**Concurrent-writer attribution, re-derived semantically rather than by file bytes.** `git show HEAD:examples/fakeshop/db.sqlite3` into a scratch path outside the repo, then `sqlite3.iterdump()` on both: HEAD **9,593** statements, working tree **9,736**; **173** only in the working tree, **30** only at HEAD. The added rows are `kanban_uuidmodel` (69), `kanban_trackedpath` (35), `kanban_carditem` (25), `kanban_card` (17), `kanban_cardreference` (7), `kanban_cardpathlink` (5), `kanban_card_labels` (5), `kanban_specdoc` (3). **Zero statements in the delta mention `spec-004`, `DONE-004`, or `optimizer_beyond`**; the six statements containing the string "glossary" are all `kanban_card` / `kanban_carditem` prose about the graph-substrate spec and a card renumber (`54 → 55`, `55 → 56`), not glossary-table rows. **The card-4 glossary-link chain the 10-anchor constraint protects is untouched**, which is what `import_spec_terms --check` independently confirms.

**Two changes to the baseline-dirty set since my pass-1 review, reported for Worker 0 to append rather than edited into the plan:**

- **The stray 0-byte untracked `db.sqlite3` at the repository root is GONE.** It is absent from `git status --short` and `ls` finds no such path. My pass-1 review recorded its attribution as genuinely uncertain and left it in place; something outside this cycle removed it. Recorded so a later pass reading that entry does not go looking for it.
- **`docs/SPECS/NEXT.md` is no longer dirty**, and `docs/spec-068-graph_substrate-0_1_1.md` (+ its terms CSV) is now `D` rather than `M` — the concurrent `NEXT.md` flow archived it into `docs/SPECS/spec-053-graph_substrate-0_1_1.md`. Both are `### Third growth`'s subject and neither is in any residual item's writable set.

### What looks solid

- **All five pass-1 findings are closed by the diff and none was rejected**, which is the outcome the artifact's own findings table claims and which I confirmed one by one against the files rather than against that table. The Medium's fix is in the right file for a reason `BUILD.md` states in so many words, and the four Lows are each closed by the branch the finding recommended — except Low-4, where the deviation is better-grounded than the finding was.
- **Worker 1 re-derived my count instead of implementing it, and was right to.** This is the behaviour `BUILD.md` `## Claims are proven mechanically` asks for, applied in the direction that is hardest to do — against a reviewer's own stated number, in a pass whose job was to obey that reviewer. My "five mentions across four sentences" collapsed two sentences on `:129`; `grep -o` returns 6 and `grep -c` returns 5, and the corrected bullet states the unit and tells the reader to count. **A pass that finds its reviewer's arithmetic wrong, says so plainly, and fixes the durable file rather than the finding is doing the thing the isolation rule exists to force.**
- **The three unasked-for edits were flagged rather than hidden, and two of the three are correct.** The provenance count four → five is right: I walked all five "Kept in the spec" blocks (`:211`, `:224`, `:268`, `:373`, `:495`, `:535`) and every one of the five named rules has an entry carrying it, so the number reproduces. The standing-note count three → four is right for the four rules it lists. The third — the two sentences on why the fourth rescue hid — is honest and within the file's remit as a change record; it names no worker, no review document, and no artifact, and its payload is a generalisable rule ("a class cut uniformly must be read member by member for the one sentence that is not of its class") that a future reader can act on. **The one thing that did not survive scrutiny is the clause the count edit sits next to**, filed as the Low above — which is exactly why "new text is new surface" is the right instruction.
- **The revision is measurably a restatement, not a re-import.** 129 surviving shingles and a 49-shingle rationale-versus-spec overlap, both bit-for-bit unchanged while the rationale grew by 478 shingles and the spec by 71 bytes. It is rare to be able to prove a prose edit added no duplication; here the numbers do it.
- **The policy/status boundary against R2 was drawn precisely where the pass said it would be**, and I verified it by absence over the whole spec rather than by reading `**Cache storage.**` alone: the two words `256` and `OrderedDict` appear nowhere, `evict` appears once, and the only other `lru` in the file is pre-existing HEAD text. R2's `D6` is narrower by exactly one component and no more.
- **The spec narrates no history anywhere**, pointer paragraphs included — the Low-3 fix is verified by a twelve-alternation grep returning a single line whose only hits are rule-1 pointer vocabulary.
- **Every invariant that had to survive the edit did.** Ten anchors at one carrier each, 30/30 link targets resolving at the two-level `appx/` depth *after* the renumber committed, 0 duplicate heading slugs, both in-page anchors resolving, the terms CSV never opened, `import_spec_terms --check` green after the concurrent DB write, rule 27 holding in both files, zero fences in either, and 216 lines unchanged.

### Temp test verification

None. No temp test was written and none was warranted: the diff changes no code path, so there is nothing a test could exercise. `docs/builder/temp-tests/r1/` was not created in this pass either. Every verification above is a read-only command over the two changed files, the read-only HEAD copy, a read-only copy of the HEAD database, or the repo's own checker scripts.

**Static helper.** `scripts/review_inspect.py` was **not** run, and the skip is recorded here per `worker-3.md` `## Static helper use`. `BUILD.md` `### When to run the helper during build` triggers it on a new `.py` file, a touched file under `optimizer/` or `types/`, or 30+/50+ new lines of logic. **This cycle's diff adds no `.py` file and touches none** — the three `.py` files dirty in the tree are the concurrent session's one-line renumber sweep, attributed in `### Public-surface check` above, and they are not this item's diff. No trigger fires. No shadow file was read or written.

**Failability proofs.** The report's `None; this pass introduced no new boundary.` is verified rather than accepted: this cycle changes no package source, so there is no boundary, guard, gate, or rejection path to prove. `worker-3.md`'s mandatory re-run floor is satisfied by an **empty re-run set**, which it permits only when the diff introduces no boundary meeting the floor — that condition holds by measurement. **No boundary was re-run and none was accepted on a builder's record, because none exists.** Worker 3's source carve-out was not exercised: no production file was mutated at any point in this pass.

**Hot-path budget.** Not owed. The plan declares `none`, and correctly — nothing in this diff runs per request, per resolver, per row, per connection, or per outbound message.

**Floor verification.** Not owed. The plan declares scope `none`, and correctly — the diff touches no Django / Strawberry / channels integration seam.

**Coverage.** No `pytest` run, no `--cov*` flag in any form, at any point in this pass.

### Notes for Worker 1 (spec reconciliation)

**This is the consolidated R2 handoff.** R2 is the very next item and is the same role, so nothing below lives only in a closed section: items 1-6 are the move report's original six, items 7-9 are my pass-1 additions, and items 10-14 are this pass's. Items 1-6 all still stand — I re-verified each against the post-revision spec — and none was pre-empted by the revision.

1. **`D5` leaves the spec with no extension-lifecycle statement at all.** R1 deleted the falsified spike and its inverted recommendation rather than replacing them. The open question is whether the spec states the current construction form (module-level singleton wrapped in a factory) or points at `spec-029` Decision 3, which owns it. The build plan's anti-absorption rule, `docs/README.md`, and `docs/GLOSSARY.md` all argue for the pointer; I agree, and record agreement rather than a second opinion. **What R2 must not do is transplant the corrected recommendation into spec-004** — that is the `**The scope trap specific to this spec.**` failure.
2. **`D24` is already discharged** by the `## Priority and ordering` deletion — all eight slices now sit under `## Proposed improvements` in heading order. Verify, do not perform.
3. **`### B6` `**Public API.**` says "classmethod"; HEAD ships a `@staticmethod`.** Kept verbatim on purpose; it is a one-word correction and it is R2's. Still present at spec `:108`.
4. **`## Implementation checklist` bullet 2 is the last in-spec trace of the cache-lifetime spike** (`B1 cache-lifetime spike (10-min investigation, precedes B1 implementation)`, spec `:174`). A checklist is contract scaffolding so R1 left it, but its parenthetical is a sequencing claim about work eleven versions shipped, and the section it pointed at is gone. R2's call whether it is trimmed.
5. **`## References`' third paragraph is still dangling** (`D27`, spec `:169`): it cites a "skip Strawberry conversion" optimization "noted in B1's implementation" that `### B1` never noted, at HEAD or now. R1 neither created nor repaired it. The thing that did land is the deferred-conversion thunk, a different mechanism.
6. **`### B7`'s "No `_meta.get_fields()` call ever appears in the request path" was cut, but its contradiction survives elsewhere.** The contradicting sentence — `**Walker needs registry lookup.**`'s unregistered-model fallback at spec `:131` — is still there and still true, and `D23` records it as a documented dual contract. Nothing is owed; **R2 should simply not "restore" the deleted claim.**
7. **`D25` and `D28` are discharged and the move report's own handoff does not say so.** Both lived inside `## Priority and ordering` and went with it: `D25`'s "B8 last … pure polish item" and `D28`'s half-retensed section. The rationale's `### The former ## Priority and ordering` entry records both correctly, so the durable record is complete — but the original list named only `D24`, so an R2 working from it will hunt two sentences that no longer exist.
8. **`D6` is narrower than the drift table anticipated, and here is exactly how much.** The drift row says the spec claims "a simple bounded-size dict" where HEAD ships an LRU with `_MAX_PLAN_CACHE_SIZE = 256`, `move_to_end` promotion, and least-recent-quarter batch eviction. **The policy half is now stated in the spec and is off R2's list.** What remains for `D6` is precisely three things, none of which appears anywhere in the spec (verified by the absence grep above): the **bound** (`256`), the **storage mechanism** (`OrderedDict` + `move_to_end`, and the `suppress(KeyError)` guard against the concurrent-eviction race), and the **batch size** (a quarter, rather than one entry). Two further notes for that row: `**Cache storage.**`'s plural "entries" is generic and **neither states nor forecloses** the batching, so R2 has a free hand there; and the `lru_cache`-is-unusable reasoning the row itself calls "worth keeping" is preserved verbatim.
9. **Escalated (contract-level, maintainer's call): `## Problem statement`'s surviving competitive positioning.** Spec `:7` still reads "But strawberry-graphql-django stopped there — every request re-walks the tree, every forward FK emits a JOIN even when the parent row already carries the answer, and the optimizer's behavior is invisible to consumers outside of raw SQL logs." That is the B1, B2, and B5 win arguments in miniature, in the document that just cut all eight for being competitive positioning. I am **not** filing it as an over- or under-cut finding — `worker-1.md` puts goals and non-goals in the stays column, a problem statement is standard spec furniture, and the document's H1 is "Beyond strawberry-graphql-django", so the comparison is the spec's subject. But whether a spec's problem statement may argue against a named competitor after the per-slice arguments were cut for doing exactly that is a consistency question about what this document is, which `BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch` puts above a worker. **Resolution paths:** (a) leave it — the sentence is load-bearing for why the eight slices exist; (b) trim it to the package's own behaviour and move the comparison to the rationale's `**The win.**` entry, which already holds the argument eight times over; (c) leave it and add one clause to that entry recording that the problem statement was deliberately kept, so the next reader does not read it as a missed sweep. My read is (a) or (c); (b) would leave the first sentence naming the inherited architecture with no statement of what it lacks.
10. **The Low above is R1's, not R2's** — it is a one-clause correction to the rationale's `### The **The win.** cut …` standing note, and it is the only thing holding this item at `revision-needed`.
11. **R2's `_optimizer_field_map` worklist is the rationale's bullet, not the build plan's `D22` row.** Re-derived this spawn: **6 occurrences across 5 sites in 3 sections** — `:84` (B4 `**Walker needs registry lookup.**`), `:112` (B6's exposed-fields paragraph), `:129` (B7 `**Mechanism.**`, **twice**), `:131` (B7 `**Walker needs registry lookup.**`), `:135` (B7 `**Test surface.**`). **`D22` counts four sites and omits `**Test surface.**`.** Two riders on the same sweep: `:112` is the sole carrier of **both** `metafields` and `metaexclude`, so it must be rewritten with the links re-sited rather than dropped; and `:84` additionally still says the walker reads `_optimizer_hints` off the type class, which is `D16`'s retired mirror in the same sentence.
12. **`### B8`'s surviving opening paragraph carries a present-tense status claim, and it is in no R2-facing list.** It was kept whole from the `**The win.**` class (spec `:141`) and describes the package's own **pre-B8** behaviour in the present tense — "the optimizer blindly stacks another `.select_related("category")` on top" — which B8 shipping made false. The rationale's `**The win.**` entry hands it to R2 at `:127`, but `## Standing notes`' status-claim enumeration (`:649`-`:677`) does not list it, and neither does the drift table (`D25` is about the deleted ordering section, not this paragraph). **Do not let it fall between the two.**
13. **The link-target disk check has an expiry and mine is now the current reading, not the last word.** I re-ran it after the renumber committed at `c62e990a`: 30/30 resolve, and none of the rationale's eight `../spec-NNN-….md` siblings points at a renumbered file. **R2 and R3 re-run it themselves rather than quoting this one.** Same for `import_spec_terms --check`, which must be re-run *after* any further concurrent DB write.
14. **Baseline-dirty deltas for Worker 0 to append** (reported, never reverted): the stray 0-byte untracked `db.sqlite3` at the repository root is **gone**; `docs/SPECS/NEXT.md` is no longer dirty; `docs/spec-068-graph_substrate-0_1_1.md` and its terms CSV are now `D` (archived into `docs/SPECS/spec-053-graph_substrate-0_1_1.md`); and `django_strawberry_framework/optimizer/predicates.py`, `examples/fakeshop/apps/products/schema.py`, and `examples/fakeshop/test_query/test_products_api.py` are each one line of the concurrent renumber sweep, read and attributed above.

### Review outcome

`revision-needed`.

One Low, unaddressed and unrejected, and `worker-3.md`'s acceptance gate requires every High, Medium, and Low to be addressed or intentionally rejected with a recorded reason. The escalation carve-out does not reach it — that is for Medium-or-higher findings needing spec context, and this needs neither.

**The revision is one clause.** The `**The win.**` standing note's closing summary describes neither surviving paragraph correctly: B6's survival is a sentence and B8's whole-paragraph survival — the one carrying a present-tense status claim R2 has to handle — is absent from the note entirely.

**Everything the prompt sent me to grade came back clean.** The Medium's destination is the spec and the argument for it is `BUILD.md`'s own; the policy-only line was held, verified by an absence grep over the whole file rather than by reading the changed paragraph; `D6` is narrowed by exactly one component and pre-empted in none. The `_optimizer_field_map` deviation is correct and my own pass-1 number was the wrong one — 6 occurrences, 5 sites, 3 sections, and the rationale's bullet now matches site for site. Of the three unasked-for edits, two reproduce on re-derivation and the third is within the file's remit; only the clause beside the second failed. Both remaining Lows closed measurably — the 17-shingle sibling-rationale run is gone and the retraction clauses are verified absent — and every invariant that had to survive did: ten single-carrier anchors, 30/30 link targets resolving after the renumber committed, 0 duplicate slugs, `import_spec_terms --check` green after the concurrent DB write, and 129 / 49 shingle figures unmoved across 478 new rationale shingles.

Per the build plan's `### Deviation 2` corollary this routes to **Worker 1**, not Worker 2. Worker 1 applies the change, sets `Status: planned` again, and returns the artifact here for a pass-3 review.

### Working-tree churn observed during this review — reported, not reverted

The baseline changed a **fourth** time, in the closing minutes of this pass. Nothing was reverted and no `git checkout` / `restore` / `stash` was used (`AGENTS.md` rule 34). Worker 0 owns appending it to the plan; this is the report.

**`HEAD` moved again: `c62e990a` → `346d6731`.** The concurrent session committed the whole of its `### Third growth` working set — the renumbered live specs (`spec-053-graph_substrate`, `spec-054-fieldset`, `spec-055-search_fields`), the `TODO-BETA-060` → `061` sweep through `optimizer/predicates.py`, `products/schema.py`, and `test_products_api.py`, the archived `docs/spec-068-…`, `KANBAN.md` / `KANBAN.html` / `docs/TREE.md` / `BACKLOG.md` / `TODAY.md`, and `examples/fakeshop/db.sqlite3`. **`git status --short` is now four entries: this cycle's `M docs/SPECS/spec-004-…` and its three untracked artifacts, and nothing else.**

Every figure in this review was re-derived **before** that commit and re-checked **after** it. What was re-run rather than assumed, and what it returned:

- `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` → still **`20a9752f`**. **This cycle's work was not swept into `346d6731`** — the standing hazard check, done with `git log`, never `git status` alone.
- `git diff --stat -- docs/SPECS/spec-004-…` → still **28 insertions / 171 deletions**, and the rationale, this artifact, and the build plan are all still `??`. Nothing this cycle wrote was committed by someone else.
- `check_spec_glossary.py --spec …` → `OK: 10 terms - all have glossary entries and at least one spec link.`
- `import_spec_terms --check` → `OK: 49 done cards have glossary links.` **Read-only form; re-run after the commit, not before it.**
- Link-target disk check re-run against the committed tree: spec **11/11**, rationale **19/19**, **0 missing**. The renumber is now committed rather than in flight, and none of the rationale's sibling links points at a renumbered file.

**Two consequences for R2 and R3.** First, `## Concurrent-writable tracked binary / generated files` has flipped again — `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, and `examples/fakeshop/db.sqlite3` are all **clean** at `346d6731`, so R3's archive audit can once more read a `git diff` on them as attributable, but it must re-derive that rather than inherit either this reading or `### Third growth`'s. Second, **`django_strawberry_framework/optimizer/predicates.py` is no longer dirty** — the concurrent source edit inside the subpackage this cycle reads is now committed history, so `git diff --stat -- django_strawberry_framework/ tests/ examples/` is empty again and the attribution table under `### Public-surface check` above describes files that were dirty at the time it was written.

The stray 0-byte untracked `db.sqlite3` at the repository root remains **gone**. No finding above depends on any of this churn, and the outcome is unchanged.

---

## Build report (Worker 1, apply-changes pass 2)

Per the build plan's `### Deviation 2` corollary, an R1 `revision-needed` routes to Worker 1: the
same two rules that make Worker 1 the only role that may perform the move make it the only role that
may fix it. `Status:` is `planned` on return, which Worker 0 reads as "dispatch Worker 3" for a
pass-3 review. Every prior entry — including both of Worker 3's review sections — is untouched.

**One Low, fixed; nothing rejected.** The spec was **not** reopened: the fix is entirely inside
`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`, and the spec is byte-identical to
the file Worker 3 read at pass 2 (216 lines / 26,480 bytes, `git diff --stat` still 28 insertions /
171 deletions). Worker 3's 14-item `### Notes for Worker 1 (spec reconciliation)` was read and is
R2's; nothing in it was acted on, item 9's escalated contract-level question included.

### The Low — both halves closed, and the second half is the one that mattered

The finding names two consequences and says the fix should resolve them rather than correct the
wording. Both are addressed, in two different places, because they are two different defects.

**Half one — the wrong summary.** The `**The win.**` standing note closed with "plus one whole
paragraph kept because it carried a public API", which describes neither survival. Verified against
the read-only HEAD copy this spawn, not inherited:

- HEAD `### B6` `**The win.**` is one paragraph of **three** sentences. Only the first survives, as
  `**Public API.**` at spec `:108`; "Fail-fast at startup instead of N+1-fast in production. None of
  the existing libraries ship this." was cut. So that survival is a **sentence**.
- HEAD `### B8` `**The win.**` is one paragraph of **two** sentences, and spec `:141` carries both
  verbatim with only the label dropped. That survival **is** a whole paragraph — kept because it
  names no competitor, not because it carried a public API.

**Taken by dropping the summary rather than by rewriting the clause**, which is the finding's own
second option and the one that answers its first consequence. Three tallies of one set coexisted;
correcting the clause would have left three tallies, one of them merely less wrong. The note now
re-tallies nothing: it points at the `**The win.**` entry for what survived the class and at
`## Provenance of this record` for the full restated set, and states the rule that made this a
defect in the first place — a tally written twice is a tally to keep in step. The paragraph that
followed it opened "The fourth is the one worth studying", an ordinal into the list just removed, so
it now names its subject directly (the plan cache's least-recently-used eviction discipline); its
generalisable lesson is unchanged.

This is also the lesson my own prior pass recorded and then did not apply — the pass-1 apply-changes
report's own three unasked-for consistency edits were the symptom of the same duplicated tally.

**Half two — B8's paragraph reaching no R2-facing list.** This is the half the finding says actually
matters, and a corrected clause does not fix it: the note is a "test this first" note, not R2's
worklist. `## Standing notes`' `### The status claims were left standing` **is** that worklist — it
is the file's durable, do-not-miss enumeration and the reconciliation item's entry point. B8's
surviving paragraph now has a bullet there, alongside the other nine, naming the claim in quotation
("the optimizer blindly stacks another `.select_related("category")` on top"), why B8 shipping is
what falsified it, and that the build plan's drift table does not cover it.

That last clause was measured rather than asserted, and the measurement changed it: `grep '^| D'`
over the plan's drift table returns **three** rows mentioning B8 — `D24` (document structure),
`D25` (the deleted ordering section), `D26` (the cut fence) — where my first draft of the bullet
said "its two B8 rows". None of the three covers the opening paragraph, so the finding's claim holds;
the count beside it did not. It is now stated as a list of what those rows name, with no number.

### Files touched

- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — 2 edits: the `**The win.**`
  standing note's summary sentence and its following ordinal, and one new bullet in
  `### The status claims were left standing`. 762 -> 768 lines, 53,505 -> 54,107 bytes (+547).
- `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` — **not touched this pass.** The finding required
  no spec edit and the scope discipline forbids a discretionary one.
- `docs/builder/bld-004-r1-rationale_move.md` — this section appended; `Status:` set to `planned`.

### Validation run — every result quoted verbatim

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
  -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**. Character-
  identical to the build plan's pre-flight baseline.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md docs/builder/bld-004-r1-rationale_move.md`
  -> **exit 0** on all three files.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have
  glossary links.` **exit 0**. Read-only form only; the writing form was never invoked.
- **Every link definition re-resolved on disk this spawn, not quoted.** Each target resolved from its
  own source file's directory and existence-tested: spec **11 definitions / 11 distinct uses**,
  rationale **19 / 19**, **0 undefined references, 0 unused definitions, 0 of 30 targets missing.**
  The renumber is now committed rather than in flight (HEAD `346d6731`), and none of the rationale's
  `../spec-NNN-….md` siblings points at a renumbered file. **R2 and R3 re-run this rather than
  quoting it.**
- **Per-anchor 10-anchor constraint, re-derived.** `grep -o "\[glossary-<anchor>\]" | wc -l` -> **2
  for every one of the ten** (1 body use + 1 definition): `configurationerror`,
  `djangooptimizerextension`, `djangotype`, `fk-id-elision`, `metaexclude`, `metafields`,
  `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `queryset-diffing`. The spec was not
  edited this pass, so this is a confirmation rather than a risk that was run.
- **Byte / line count.**

| | lines | bytes |
|---|---|---|
| spec at Worker 3's pass-2 review | 216 | 26,480 |
| spec **now** | **216** | **26,480** (unchanged — not touched) |
| spec at HEAD (pre-move) | 359 | 33,928 |
| net move + revisions | **-143** | **-7,448 (-21.9%)** |
| rationale at Worker 3's pass-2 review | 762 | 53,505 |
| rationale **now** | **768** | **54,107** (+602 over two edits) |

- `git diff --stat -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **28 insertions / 171
  deletions**, the same hunk shape Worker 3 recorded — independent evidence the spec is untouched.
- `grep -c '^```'` -> spec **0**, rationale **0**. No fence introduced.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files -> **no match** (exit 1). Rule 27 holds.
- `grep -nP '\]\((?!#|https?:)'` over both files -> **no match** (exit 1). Reference-style preserved.
- `grep -niE 'as of (review )?round|amendment|retract|inverted|a later strawberry'` over the spec ->
  **no match** (exit 1). The pass-1 Low-3 fix is still held.
- In-page anchors: the repo's own `scripts/check_spec_glossary.py::github_anchor` over the spec's
  **15** headings -> **0 duplicate slugs**; `#proposed-improvements` and `#problem-statement` both
  resolve. **No new in-page anchor was added** — the note's cross-reference to the `**The win.**`
  entry is a named textual pointer, as the file's other intra-file pointers are, because the em-dash
  slugger ambiguity this file documents applies to its own `###` headings.
- `git diff --stat -- django_strawberry_framework/ tests/ examples/` -> **empty**. No source, test,
  or example file touched; no `pytest`, no `ruff` (no `.py` file changed), no coverage-shaped flag in
  any form.
- No `git stash`, `checkout`, `restore`, `worktree`, `commit`, or branch operation at any point. The
  read-only HEAD reference was `git show HEAD:docs/SPECS/spec-004-optimizer_beyond-0_0_3.md >
  <scratchpad outside the repo>/spec-004-HEAD.md` (33,928 bytes / 359 lines — the baseline the move
  was measured against has still not moved).

### Duplication introduced by this pass: zero, measured

The bullet added to `## Standing notes` quotes a sentence that is **still in the spec**, which is the
one shape this edit could plausibly have duplicated. It did not, because the same words were already
quoted in the `**The win.**` entry's eight-quotation list, so the quotation adds no run the file did
not already carry. Measured by reconstructing the pre-pass rationale from this pass's own two edits
(the reconstruction reproduces 53,505 bytes / 762 lines exactly, which is what validates it) and
differencing 8-word shingle sets against the read-only HEAD copy:

| measure | before this pass | after |
|---|---|---|
| rationale total shingles | 8,377 | 8,473 (+96) |
| left-the-spec shingles present in the rationale | 161 | **161 (unchanged)** |
| rationale x post-move-spec overlap | 52 | **52 (unchanged)** |
| overlap shingles this pass added | — | **0** |

**Method disclosure, because the absolutes differ from Worker 3's.** My normalization (strip from
`<!-- LINK DEFINITIONS -->`, fold every non-alphanumeric run to whitespace, lowercase, 8-word
shingles) yields 4,934 at HEAD where Worker 3's pass-2 reading gives 4,646 — a different
normalization, not a different file (both readings are of the same 33,928-byte blob). The absolutes
are therefore **not** comparable across the two passes and I make no claim that they are; what is
load-bearing here is the before/after delta under one consistent method, and it is zero on both
duplication measures.

### Notes for Worker 3 (pass 3)

- **The judgement to audit is the disposition, not the wording.** The finding offered a replacement
  clause; I took its second option instead and dropped the summary. The check is to read the
  standing note headed *The `**The win.**` cut is the one an over-cut review should test first* and
  confirm (a) it now states no tally of its own, (b) each pointer
  it substitutes lands on a place that is correct — the `**The win.**` entry for the class's
  survivals, `## Provenance of this record` for the five restated rules — and (c) the second
  paragraph's subject survived the loss of the ordinal it used to depend on.
- **The half worth checking hardest is the new bullet's placement**, not its prose: it is in
  `### The status claims were left standing` because that is R2's do-not-miss list, and the finding's
  own second consequence is that B8's paragraph reached no such list. If that is the wrong list, the
  fix is to move the bullet, not to re-word the note.
- **One claim inside the new bullet was corrected by measuring it as it was written** (three drift
  rows mention B8, not two). It is stated as a list rather than a count for that reason. Re-derive it
  with `grep -n '^| D[0-9]' docs/builder/build-004-optimizer_beyond-0_0_3.md | grep -i b8`.
- **Nothing else was edited.** No unasked-for consistency edit was needed this pass, because the
  fix removed a duplicate tally rather than changing a number that other passages restate — which is
  exactly the failure mode the pass-1 report's three forced corrections illustrated.
- **Two claims worth re-deriving rather than reading:** the 30/30 link-target disk check (the
  renumber is committed now, but the check still expires) and the zero-new-overlap measurement above
  — reconstruct the pre-pass file from the two edits and difference the shingle sets, or simply
  confirm the quoted B8 sentence already appears in the `**The win.**` entry.
- The consolidated R2 handoff is Worker 3's own 14-item list in `## Review (Worker 3, pass 2)`, plus
  item 12 of that list, which this pass has now discharged **into the durable file** rather than
  leaving it in a section that closes with the cycle. Nothing from this pass was staged for later
  without being written down.

### Spec changes made (Worker 1 only)

**None.** The spec was not edited this pass. `git diff --stat` on it is unchanged at 28 insertions /
171 deletions and its byte count is identical to Worker 3's pass-2 reading, so the three pass-1
revision edits recorded above remain the whole of this cycle's spec delta.

**Spec status-line re-verification** (`worker-1.md` `## Spec status-line re-verification`, re-run
this spawn as every Worker 1 spawn must): spec-004 carries **no** `Status:` / owner / target-release
/ predecessor header block — lines 1-5 are the title, the companion-pointer paragraph, and
`## Problem statement`. Nothing in them is a status line this build has falsified, so no header edit
was owed.

### Working-tree churn observed during this pass — reported, not reverted

The concurrent session's commit landed before this pass started, so the baseline **shrank** rather
than grew. `git status --short` is **four entries and nothing else**, for the first time since
pre-flight:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
```

`HEAD` is **`346d6731`**, re-derived this spawn rather than quoted, and it did **not** sweep this
cycle's work: `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns
**`20a9752f`**, and the rationale, this artifact, and the build plan are all still untracked. That is
the standing hazard check, done with `git log` rather than `git status` alone.

For Worker 0 to append to the plan rather than a worker editing it: `KANBAN.md`, `KANBAN.html`,
`docs/TREE.md`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3`, and
`django_strawberry_framework/optimizer/predicates.py` are **all clean again** at `346d6731`, so
`## Concurrent-writable tracked binary / generated files` has recovered every member it lost across
`### Second growth` through `### Fourth change`. R3's archive audit may once more read a `git diff`
on them as attributable — but it re-derives that itself rather than inheriting this reading, since
the concurrent session has already reversed this state four times in one cycle.

---

## Build report (Worker 1, maintainer-decision pass)

**This pass is not a response to a Worker 3 finding.** Worker 3 escalated a contract-level question
at its pass-2 review (`## Review (Worker 3, pass 2)` `### Notes for Worker 1 (spec reconciliation)`
item 9) and correctly declined to decide it. The maintainer has now ruled, and `BUILD.md`
`### Contract-level findings are escalated as maintainer decisions before dispatch` governs: the
decision, its reasoning, and **the rejected alternatives each with the reason it lost** are recorded
in `docs/builder/build-004-optimizer_beyond-0_0_3.md`, section *Maintainer decision — the surviving
competitive positioning in `## Problem statement`*, which is the canonical record. It is pointed at
rather than restated here, because a copy in a per-cycle artifact goes stale. Nothing in it was
re-litigated. `Status:` is `planned` on return, which Worker 0 reads as "dispatch Worker 3" for a
pass-3 review; every prior entry, both of Worker 3's review sections included, is untouched.

**What was decided, in one line for a reader who has the plan open:** the `## Problem statement`
sentence stays **byte-for-byte**, and **two** recording edits land in the rationale — because the
escalation surfaced a defect nobody had filed, namely that the rationale's `**The win.**` entry
asserted under **Claims the spec no longer makes** that the spec no longer claims the per-request
re-walk or the needless id-only-FK JOIN, which are claims the surviving `## Problem statement`
demonstrably still makes. One recording clause was ruled insufficient for exactly that reason: it
would have left the retracted-claims list standing and the record at war with itself.

### The two edits, as applied

Both are in `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`. Both use link references
already defined in that file's block (`spec-004-problem`, `worker-1`), so no definition was added,
and the maintainer's prose was re-flowed to the file's existing wrap rather than pasted as one line.

| # | Site | Change |
|---|---|---|
| 1 | the entry *The eight `**The win.**` paragraphs — a competitive argument, not a contract*, its closing **Claims the spec no longer makes** block | Retitled to **"as any slice's own argument"**; the two claims the `## Problem statement` still makes are removed from the retracted list and **positively recorded as surviving**, with the reason the survival is deliberate rather than a missed sweep, and the reason the sentence was kept whole rather than name-stripped |
| 2 | the entry *`## Problem statement` — the pointer into the ordering section*, its closing paragraph | The first paragraph's description now names the "But strawberry-graphql-django stopped there" sentence as included and kept deliberately over the eight-paragraph cut, pointing at the `**The win.**` entry |

The two halves are what make this a record rather than an assertion: edit 1 stops the file claiming
the spec retracted something it did not, and edit 2 puts the keep in the entry a reader lands on
when they read `## Problem statement` and wonder why the comparison survived. Neither adds an
in-page anchor: edit 1's back-reference to the trim-the-name rejection is a **named textual
pointer**, as this file's other intra-file pointers are, because the em-dash slugger ambiguity the
file documents applies to its own `###` headings.

### The integration duty: is there a third site the decision now contradicts?

The pass owns the integration even though it does not own the wording, so the file was swept for a
third site that would reproduce the defect at a new address. **There is none, and the search is
recorded so pass 3 does not re-derive it.** Four candidates were opened and each was resolved
against the file, not against intuition:

- **The other ten `**Claims the spec no longer makes.**` blocks.** `grep -n` returns eleven such
  blocks; all ten others were read in full. **None covers the competitor-comparison material** —
  they retract elision keying, dotted strictness paths, `_optimizer_hints` as a class attribute,
  B5 sequencing, `_meta.get_fields()` iteration, the plan-alone diff return, and the recommended
  build sequence. Edit 1's block was the only one at war with the surviving sentence.
- **`## Provenance of this record`'s "Deliberately left in the spec by this pass" bullet.** It
  enumerates the present-tense status claims and the out-of-fence symbol names; it does not claim
  its list is everything the pass left standing, and it makes no assertion about the competitor
  comparison in either direction. **Deliberately not extended**: the keep is now recorded in two
  places, and a third would be a third tally of one set — the exact defect this cycle's pass-2 Low
  was filed for and the exact reason its fix *deleted* a duplicate tally rather than correcting it.
- **`## Standing notes` `### The status claims were left standing`**, whose opener reads "This pass
  cut the *deliberative* layer: competitive argument, proposal code, build order …". This is the
  closest call and it was decided on the distinction the decision itself turns on: the sentence
  describes **which classes the pass acted on**, and the pass did cut competitive argument — eight
  paragraphs of it. It does not assert what the spec now contains. The defect in edit 1's old text
  was of the other kind: an affirmative claim about the spec's **current** content that the spec
  falsifies. Left as written.
- **`## Standing notes`' note headed *The `**The win.**` cut is the one an over-cut review should
  test first*** — the one that standing-orders a future sweep of this class. It already points at
  the `**The win.**` entry for the class's survivals and re-tallies nothing, so edit 1 lands inside
  the entry that note sends a sweeper to. Left as written, and for the same reason: it is a pointer,
  not a tally.

### Files touched

- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — the two edits above.
  768 -> 776 lines, 54,107 -> 54,865 bytes (+758).
- `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` — **not touched.** The decision's first clause is
  that it changes nothing, and it is not in this pass's writable set.
- `docs/builder/bld-004-r1-rationale_move.md` — this section appended; `Status:` confirmed `planned`
  (it was already `planned` from the pass-2 apply, so no transition was owed and none was faked).

### Validation run — every result quoted verbatim

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
  -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**. Character-
  identical to the build plan's pre-flight baseline.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md docs/builder/bld-004-r1-rationale_move.md`
  -> **exit 0** on all three files.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have
  glossary links.` **exit 0**. Read-only form only; the writing form was never invoked.
- **Every link definition re-resolved on disk this spawn — re-run, not quoted, because the prior
  30/30 readings have an expiry.** Each target resolved from its own source file's directory and
  existence-tested: spec **11 definitions / 11 distinct uses**, rationale **19 / 19**, **0 undefined
  references, 0 unused definitions, 0 of 30 targets missing.** Edit 1 adds a **second use** of
  `spec-004-problem` and of `worker-1`, both already defined and already used, so the definition
  count and the distinct-use count are both unchanged — no definition was added and none went
  unused. HEAD is `346d6731`, the commit that landed the concurrent renumber.
- **Byte / line count.**

| | lines | bytes |
|---|---|---|
| spec at Worker 3's pass-2 review | 216 | 26,480 |
| spec **now** | **216** | **26,480** (unchanged — not touched) |
| spec at HEAD (pre-move) | 359 | 33,928 |
| net move + revisions | **-143** | **-7,448 (-21.9%)** |
| rationale before this pass | 768 | 54,107 |
| rationale **now** | **776** | **54,865** (+758) |

- `git diff --stat -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **28 insertions / 171
  deletions**, the hunk shape Worker 3 recorded at both reviews — independent evidence the spec is
  byte-identical to the file pass 2 read, as the decision requires.
- **Per-anchor 10-anchor constraint, re-derived.** `grep -o "\[glossary-<anchor>\]" | wc -l` -> **2
  for every one of the ten** (1 body use + 1 definition): `configurationerror`,
  `djangooptimizerextension`, `djangotype`, `fk-id-elision`, `metaexclude`, `metafields`,
  `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `queryset-diffing`. The spec was not
  edited, so this is a confirmation rather than a risk that was run. **The terms CSV was not
  opened**: `git status --short docs/SPECS/appx/` shows only the rationale, as `??`.
- In-page anchors: the repo's own `scripts/check_spec_glossary.py::github_anchor` over the spec's
  **15** headings -> **0 duplicate slugs**; `#proposed-improvements` and `#problem-statement` both
  resolve. No new in-page anchor was added.
- `grep -c '^```'` -> spec **0**, rationale **0**. No fence introduced.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files -> **no match** (exit 1). Rule 27 holds.
- `grep -nP '\]\((?!#|https?:)'` over both files -> **no match** (exit 1). Reference-style
  preserved; the one link edit 1 adds is reference-style and wraps across a line, which is this
  file's own established form (`## How to read this file` already wraps
  `[`## Proposed improvements`][spec-004-improvements]` the same way).
- `git diff --stat -- django_strawberry_framework/ tests/ examples/` -> **empty**. No source, test,
  or example file touched; no `pytest`, no `ruff` (no `.py` file changed), no coverage-shaped flag
  in any form.
- No `git stash`, `checkout`, `restore`, `worktree`, `commit`, or branch operation at any point. The
  read-only HEAD reference was `git show HEAD:docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` piped
  in-process (33,928 bytes / 359 lines — the baseline the move was measured against has not moved).

### Duplication introduced by this pass: zero, measured as it was written

Edit 2 names a spec sentence by quoting five of its words, which is the one shape these edits could
have duplicated. It did not, and it could not have: five words is under the 8-word shingle floor.
Measured rather than argued, by reconstructing the pre-pass rationale from this pass's own two
replacements — **the reconstruction reproduces 54,107 bytes / 768 lines exactly, which is what
validates it as the baseline** — and differencing 8-word shingle sets against the read-only HEAD
copy:

| measure | before this pass | after |
|---|---|---|
| rationale total shingles | 8,473 | 8,595 (+122) |
| left-the-spec shingles present in the rationale | 161 | **161 (unchanged)** |
| rationale x post-move-spec overlap | 52 | **52 (unchanged)** |
| overlap shingles this pass added | — | **0** |

**Method note.** The normalization is the same one the pass-2 apply used (strip from
`<!-- LINK DEFINITIONS -->`, fold every non-alphanumeric run to whitespace, lowercase, 8-word
shingles), which yields 4,934 at HEAD where Worker 3's readings give 4,646 — a different
normalization of the same 33,928-byte blob, not a different file. **The absolutes are therefore not
comparable across the two roles and no claim is made that they are**; the before/after delta under
one consistent method is what is load-bearing, and the two duplication figures reproduce the pass-2
report's 161 / 52 exactly, which is the continuity check that the method really is the same one.

### Notes for Worker 3 (pass 3)

- **What to audit is the integration, not the wording.** The two replacement paragraphs are the
  maintainer's ruling and are not this pass's to re-argue, so grading them against a worker's
  judgement is the wrong test. What *is* this pass's is `### The integration duty` above: whether a
  third site in the rationale now contradicts the decision. Four candidates are named there with
  the reason each was left; the check is to look for a fifth.
- **The judgement most open to challenge is the third candidate** — `## Standing notes`'
  "This pass cut the *deliberative* layer: competitive argument, …". It was left on the distinction
  between describing which classes the pass acted on and asserting what the spec now contains. If
  that distinction is judged too fine, the fix is one qualifying clause there, not a re-edit of
  either maintainer-authored paragraph.
- **Two claims worth re-deriving rather than reading:** the 30/30 link-target disk check (the
  renumber is committed now, but the reading still expires and edit 1 adds a link use), and the
  zero-new-overlap measurement — reconstruct the pre-pass file from the two replacements, confirm it
  lands on 54,107 bytes / 768 lines, and difference the shingle sets.
- **Nothing was acted on from Worker 3's 14-item `### Notes for Worker 1 (spec reconciliation)`.**
  That list is R2's worklist. Item 9 is the escalation this pass discharges, and it is now closed by
  the maintainer's ruling rather than by a worker's call; the other thirteen stand untouched.
- Nothing from this pass was staged for later without being written down. No temp test, no shadow
  file, no `docs/builder/temp-tests/` directory.

**Failability proofs.** None; this pass introduced no new boundary. `git diff --
django_strawberry_framework/` is empty, so there is no boundary, guard, gate, or rejection path to
prove.

**Hot-path budget.** Not applicable; the plan declares `none`, and correctly — nothing in this diff
runs per request, per resolver, per row, per connection, or per outbound message.

**Floor verification.** Not applicable; the plan declares floor-verification scope `none`, and
correctly — the diff touches no Django / Strawberry / channels integration seam.

**Coverage.** No `pytest` run, no `--cov*` flag in any form, at any point in this pass.

### Spec changes made (Worker 1 only)

**None, by the decision's own first clause.** `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` was
not in this pass's writable set and was not edited: `git diff --stat` on it is unchanged at 28
insertions / 171 deletions and its byte count is identical to Worker 3's pass-2 reading (216 lines /
26,480 bytes), so the three pass-1 revision edits remain the whole of this cycle's spec delta.

**Spec status-line re-verification** (`worker-1.md` `## Spec status-line re-verification`, re-run
this spawn as every Worker 1 spawn must): spec-004 carries **no** `Status:` / owner / target-release
/ predecessor header block — lines 1-5 are the title, the companion-pointer paragraph, and
`## Problem statement`. Nothing in them is a status line this build has falsified, so no header edit
was owed, and none could have been made this pass in any case.

### Working-tree churn observed during this pass — reported, not reverted

**None.** `git status --short` was the same four entries at the start and at the end of the pass,
for the second consecutive pass:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
```

`HEAD` is **`346d6731`**, re-derived this spawn rather than quoted, and it did **not** sweep this
cycle's work: `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns
**`20a9752f`**, and the rationale, this artifact, and the build plan are all still untracked. That
is the standing hazard check, done with `git log` rather than `git status` alone. `KANBAN.md`,
`KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, and `examples/fakeshop/db.sqlite3` are all still
clean — but pass 3 re-derives that rather than inheriting this reading, since the concurrent session
reversed that state four times earlier in this cycle.

---

## Review (Worker 3, pass 3)

Read in order, as the prompt directs: `docs/builder/worker-3.md` (full), `AGENTS.md`, `START.md`,
`docs/builder/BUILD.md` (`## Spec rationale extraction`, `### Who reads it, and when`,
`### Contract-level findings are escalated as maintainer decisions before dispatch`,
`## Claims are proven mechanically`, `## Severity definitions`, `## The corpus ratchet` re-read
verbatim), `docs/builder/ARTIFACT.md`, `docs/README.md`, `examples/fakeshop/test_query/README.md`,
`docs/builder/build-004-optimizer_beyond-0_0_3.md` **in full, including the new
`## Maintainer decision — the surviving competitive positioning in `## Problem statement``**, this
artifact end to end in the prescribed order (plan, move report, `## Review (Worker 3)`,
`## Build report (Worker 1, apply-changes pass)`, `## Review (Worker 3, pass 2)`,
`## Build report (Worker 1, apply-changes pass 2)`, `## Build report (Worker 1,
maintainer-decision pass)`), the spec, the rationale, and the pristine HEAD spec obtained read-only
as `git show HEAD:docs/SPECS/spec-004-optimizer_beyond-0_0_3.md > <scratchpad outside the
repo>/spec-004-HEAD.md`. No `git stash` / `checkout` / `restore` / `worktree` at any point, and no
prior entry was edited.

`HEAD` re-derived this spawn rather than quoted: **`346d67312599c0536980969caa39085ab3885ae8`**.
`git log -1 -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns **`20a9752f`**, and the
rationale, this artifact, and the build plan are still untracked, so the concurrent session's three
commits this cycle did not sweep this cycle's work. `git status --short` is the same four entries
the prior two passes recorded and nothing else.

**Nothing below is quoted from any build report.** Every figure was re-derived from the files on
disk this spawn.

### High:

None.

### Medium:

None.

### Low:

#### `## Provenance of this record`'s shingle figures were falsified by this cycle's own pass-1 spec revision, and no pass refreshed them

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:56
**No section, paragraph, or fence was moved whole**: of the 1,685 eight-word shingles that left the
spec, 129 (7.7%) survive here and 1,556 survive in neither file.
```

Those three figures were true of the spec as it stood when the move report was written. The pass-1
apply-changes revision then rewrote `**Cache storage.**` — the one spec edit that replaced HEAD
text rather than adding new text — and that rewrite moves the population the sentence counts.
Proven mechanically rather than argued, against the read-only HEAD copy:

- HEAD `### B1` closes with `Use a simple bounded-size dict (not `functools.lru_cache`, since the
  cache key includes a model class which is not hashable by `lru_cache`'s default).` That sentence
  contributes **20** eight-word shingles, and **all 20 are present at HEAD**.
- The move carried it into the post-move spec verbatim (the move only relabelled the paragraph;
  `### Spec changes made` records the surviving two rules being relabelled `**Cache storage.**`), so
  all 20 were *surviving-in-the-spec* shingles when the count was written.
- In the spec on disk today, **13** of the 20 survive. The other **7** are now
  *left-the-spec* shingles.

So `1,685` is now `1,692`, `1,556` is now `1,563`, and `7.7%` is now `7.6%`. `129` is unaffected,
which is why the figure that carries the qualitative claim still holds. This is not a re-derivation
of a prior pass's arithmetic: the +7 is derived here from the 20/13 sentence measurement alone, and
it happens to equal the delta my own pass-2 review table recorded and did not file.

**A second defect sits under the same number: no normalization is stated, and the two disclosed
ones disagree by 288 shingles on the same 33,928-byte blob.** My reviews measured HEAD at 4,646;
the pass-2 and maintainer passes measured the same blob at 4,934 and said so explicitly. A reader
of the durable file has neither method, so the figure is not re-derivable by anyone — which is the
condition `BUILD.md` `## Claims are proven mechanically` treats as the defect ("prefer any form
whose count the reader can re-derive"). Under the normalization the maintainer pass disclosed
(strip from `<!-- LINK DEFINITIONS -->`, fold every non-alphanumeric run to whitespace, lowercase,
8-word shingles, distinct), my independent implementation gives the triple as **1,853 / 161 /
1,692** — a third set of numbers, all internally consistent, none matching the file.

**Why Low and not Medium.** `BUILD.md` makes an *unverified* stated count a Medium; this one was
measured when written, and the qualitative claim it supports ("no section, paragraph, or fence was
moved whole") is independently true — I confirmed it again by run structure, not by total. It is
`## Severity definitions`' Low: stale but not load-bearing. It is filed at all because this is a
durable file, every later pass treats a number as measured, and the same section was edited twice
in this cycle for exactly this reason (four to five, three to four) while the bullet three lines
above it went unrefreshed.

**Recommended change.** Refresh the three figures **and** add the normalization in one clause, so
the number becomes re-derivable rather than merely current — the root cause is the missing method,
not the staleness. Dropping the figures instead would follow this cycle's own drop-the-tally
precedent, but they are doing work the prose cannot (they are what lets a later reader tell "the
text is here" from "the text is gone" without re-running the measurement), so refresh-and-disclose
is the better branch. If they are refreshed, re-measure **after** any further spec edit, not
before.

**Test expectation.** None; no behaviour changes.

#### The `**Cut**` provenance bullet files the eight `**The win.**` paragraphs under a label the same file defines as "exists in neither file", and two of them are verbatim in the spec

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:59
- **Cut, with a prose account kept here** — the eight `**The win.**` paragraphs that opened each
  slice; all **eight** fenced pseudo-code blocks (one per slice); the whole of
  `## Priority and ordering`; …
```

The label is defined 40 lines above it: *"**Cut** means the text exists in **neither** file: what
follows the label is an account of what it said and why it went, and git history is the only record
of the wording."* Two of the eight are in the spec, verified by exact string comparison against the
read-only HEAD copy rather than by reading:

- **B8's whole paragraph.** HEAD `:271` with its `**The win.** ` prefix removed is **byte-equal** to
  the current spec `:141`. Two sentences, not one word changed.
- **B6's first sentence.** HEAD `:181` with the prefix removed **starts with** the current spec
  `:108`'s text after its `**Public API.** ` label — i.e. the surviving sentence is a verbatim
  prefix of the HEAD paragraph.

The contradiction is also internal to the one section: `## Provenance of this record`'s
**Restated in the spec, not moved** bullet at `:78`-`:84` lists "the `check_schema` public-API
sentence" among the five, so B6's sentence is filed under two mutually exclusive labels 26 lines
apart. The entry itself is correct (`:122` "two of the eight paragraphs survived, one whole and one
in part") — it is the index a reader consults first that is wrong.

This matters for the same reason the pass-2 Low mattered, and it is the same class of defect the
maintainer decision was issued to remove: a record asserting an absence the spec falsifies. The
concrete harm is that B8's surviving paragraph is precisely the reconciliation-item worklist entry
the pass-2 Low was filed to protect, and a reader who resolves "did the win paragraphs leave the
spec?" against the provenance index is told all eight did. It is compounded by the pass-2 fix
itself: `## Standing notes`' `### The `**The win.**` cut …` note now deliberately re-tallies
nothing and **points at `## Provenance of this record`** — so the substituted pointer lands on a
section carrying this defect and the one above.

**Why Low.** No builder acts on it, and the entry supplies the correct account one hop away.

**Recommended change.** One qualifying phrase on the Cut bullet, as a pointer and not a fourth
tally — e.g. "the eight `**The win.**` paragraphs that opened each slice, apart from the survivals
its entry records". Do not restate what survived here; that is the tally-in-two-places failure the
pass-2 fix removed.

**Test expectation.** None; no behaviour changes.

### Disposition of the apply-changes pass — the pass-2 Low is closed, and the deviation is right

**Half one, the wrong summary — closed by deletion, and the deletion is the better branch.** The
standing note at `:721`-`:735` now states **no tally of its own**. I ran W1's own three checks:

- **(a) It re-tallies nothing.** "What survived it is enumerated once and deliberately not
  re-tallied here" — confirmed by reading; no count of survivals, rescues, or paragraphs appears in
  the note.
- **(b) Each substituted pointer lands on a place that is correct — with one exception, which is my
  second Low.** The `**The win.**` entry is correct for the class's survivals (`:122`-`:133`
  describes both survivals accurately, B8's as whole and B6's as a first sentence). The five
  restated rules pointer resolves: I walked all five from `## Provenance of this record` `:78`-`:84`
  to their entries — `(name, value)` pair shape at `:276`, `dst_optimizer_planned` at `:381`,
  snake-cased field-map key at `:543`, LRU eviction discipline at `:232`, `check_schema` sentence at
  `:503`. Five named, five carried. What the pointer's **target section** now carries is the two
  Lows above.
- **(c) The second paragraph survived losing the ordinal it depended on.** It opens "The rescue
  worth studying is the plan cache's least-recently-used eviction discipline" — the subject is
  named directly, the generalisable rule ("a class cut uniformly must be read member by member for
  the one sentence that is not of its class") is intact, and nothing in it references a list
  position.

Taking the finding's *second* option rather than its first was correct on the finding's own
reasoning: correcting the clause would have left three tallies of one set, one merely less wrong,
and the file's stated principle ("a tally written twice is a tally to keep in step") is what the
deletion enacts.

**Half two, B8's paragraph reaching an R2-facing list — closed, and the placement is right, not
just defensible.** The new bullet is at `:680`-`:685` in `### The status claims were left standing`.
That is the correct list and I did not accept it on the pass's say-so: the section's own opener
declares it the enumeration of present-tense claims handed to the reconciliation item, B8's
surviving paragraph *is* a present-tense status claim about the package's own pre-B8 behaviour, and
the alternative site (the "test this first" note) is a standing order for a future sweep, not a
worklist. The bullet quotes the claim ("the optimizer blindly stacks another
`.select_related("category")` on top" — present in the spec at `:141`, checked), states that
shipping B8 falsified it, and states the drift-table gap as a list rather than a number.

**The draft-count correction, re-derived as the prompt requires.** `grep -n '^| D' docs/builder/
build-004-optimizer_beyond-0_0_3.md | grep -i b8` returns **three** rows — `D24` (document
structure), `D25` (the deleted `## Priority and ordering` claim), `D26` (the cut `### B8` fence).
Worker 1's "three, not the two my draft said" reproduces exactly, and I read all three: **none**
covers B8's opening paragraph. So the bullet's claim holds and its decision to state a list rather
than a count is the right one — the number would have been the third thing in this cycle to be
wrong by one.

### Disposition of the maintainer-decision pass — implemented faithfully; the integration sweep found a fifth site

The ruling is the maintainer's and is not re-litigated here. What follows grades only implementation
and integration.

**Fidelity — both edits present, in the ruled shape.**

- **Edit 1** is at `:143`-`:152`. The block is retitled **"Claims the spec no longer makes as any
  slice's own argument."** The surviving comparisons are **removed from the retracted list and
  positively recorded**: "The B1, B2, and B5 comparisons — the per-request re-walk, the needless
  JOIN for an id-only FK selection, the SQL-log-only observability — survive in one compressed
  sentence in `## Problem statement`, and that survival is deliberate, not a missed sweep". Both
  ruled reasons are present: the goal/STAYS reading plus the H1 making the comparison the document's
  subject, and the kept-whole-rather-than-name-stripped reason tied back to the trim-the-name
  rejection above it.
- **Edit 2** is at `:166`-`:169`, in the `## Problem statement` entry's closing paragraph, naming
  the "But strawberry-graphql-django stopped there" sentence as included and "kept deliberately over
  the eight-paragraph cut (see the `**The win.**` entry above)".
- **Re-flowed, not pasted.** Lines `:143`-`:152` run 79-101 characters and `:166`-`:169` run 69-98,
  against a file whose own body wrap tops out at 103 (excluding the H1). No single-line paste.
- **The two link refs are pre-existing and no definition was added.** `spec-004-problem` and
  `worker-1` are both defined in the file's own block; totals now stand at **19 definitions / 19
  distinct uses / 0 undefined / 0 unused**, with **30 of 30** definition targets present on disk
  when resolved from each source file's own directory.
- **One correction to the report, not a finding.** It records edit 1 as adding "a **second use**" of
  each ref. Re-derived: `spec-004-problem` is used at `:96`, `:148` (the edit), `:156`, `:592` and
  `worker-1` at `:68`, `:109`, `:150` (the edit), `:213` — **four uses each, and the edit is the
  fourth, not the second**. The load-bearing half of the claim (already defined, already used, so
  definition and distinct-use counts are unchanged) is exactly right and reproduces.
- **One place the implementation is more complete than the ruling's summary, checked rather than
  assumed.** The plan's decision text names **two** claims at war with the spec; the file records
  **three**. I resolved this against the spec sentence rather than the plan: `## Problem statement`
  `:7` carries three clauses — the per-request re-walk (B1), the id-only FK JOIN (B2), and
  observability outside raw SQL logs (B5) — and the plan's own question section describes the
  survival as "the B1, B2, and B5 win arguments in miniature". Three is the correct population; the
  file is right.

**The spec is byte-identical, and the decision's first clause holds.** Re-derived: **216 lines /
26,480 bytes**, `git diff --stat` **28 insertions / 171 deletions**, `git log -1` on the spec still
`20a9752f`. I went further than the counts, because equal byte counts are not identity: I extracted
every one of the 28 added lines and accounted for each (the companion pointer, the re-pointed
`## Problem statement` clause, the `**Cache storage.**` restatement, eight per-slice pointers, four
restated-rule sentences, the relabelled `**Public API.**` and `**Mechanism.**` lines, the
link-carrying `### B8` heading, B8's de-labelled paragraph, and the `[spec-004-rationale]`
definition, plus four blank lines) — nothing beyond the move and the three pass-1 revision edits is
in the diff. Separately, `## Problem statement`'s first paragraph is **byte-equal to the HEAD
copy's**, which is the decision's actual subject. HEAD reference obtained with `git show HEAD:… >
<scratchpad outside the repo>/…`; no `git stash` / `checkout` / `restore` / `worktree`.

**Completeness — I re-opened the pass's four candidates independently and then swept for my own.**

The four, each resolved against the file rather than against the pass's account of it:

1. **The other ten `**Claims the spec no longer makes.**` blocks.** `grep -n 'Claims the spec'`
   returns **eleven**; I read all ten others (`:171`, `:285`, `:328`, `:388`, `:431`, `:469`,
   `:508`, `:550`, `:587`, `:641`). None retracts a competitor comparison; and specifically, the B1,
   B2 and B5 entries — the three whose comparisons survive — retract only the sync/async accessor
   split and instance-passing (B1), the bare-field-name elision key and the inline predicate (B2),
   and B5 sequencing plus the single-key stash (B5). The pass's finding reproduces.
2. **`## Provenance of this record`'s deliberate-keeps bullet** (`:85`-`:89`). It enumerates
   "every present-tense status claim about the pre-implementation codebase and every symbol name
   outside a fence"; a claim about **upstream's** behaviour is in neither category, and the bullet
   makes no assertion about the comparison in either direction. Not extending it is right, and for
   the reason given — a third recording of one keep is the defect the pass-2 fix removed.
3. **`## Standing notes`' "This pass cut the *deliberative* layer: competitive argument, …"**
   (`:653`), which the pass flags to me as its most challengeable judgement. **I agree with leaving
   it, and the deciding evidence is a path rather than a distinction.** The sentence's grammatical
   object is what the pass acted on, and the pass did cut competitive argument — eight paragraphs of
   it; its very next sentence scopes the exception to "the spec's present-tense claims about the
   codebase", which is a different category from an upstream comparison, so it neither asserts nor
   denies what the spec now contains. More decisively: the reader this could mislead is a sweeper of
   this class, and the file's standing order for that sweep is the separate note at `:721`, which
   sends the sweeper to the `**The win.**` entry — where edit 1 lives. The sweeper's path lands on
   the record. A qualifying clause here would be the third recording of one keep.
4. **The `### The `**The win.**` cut …` note** (`:721`). Correct as described: a pointer, no tally,
   and edit 1 lands inside the entry it points at.

**My own sweep, run independently.** I enumerated every site in the file that asserts an absence
from the spec — `grep -niE 'no longer|nowhere|neither file|left the spec|not restated'` plus a read
of `## How to read this file`, `## Provenance of this record`, and `## Standing notes` end to end —
and tested each against the spec on disk. Two further sites came out of it, both in
`## Provenance of this record`, both filed as Lows above: the stale/unreproducible shingle triple,
and the **Cut** bullet, which is the ruling's own defect shape (an asserted absence the spec
falsifies) at an address the pass did not open. Two more candidates were opened and **resolved as
clean**, recorded so pass 4 does not re-derive them:

- **Edit 1's retained retraction "That `strawberry-graphql-django` ships no schema audit"** against
  the spec's surviving `## Problem statement` `:9` "eight improvements that the existing libraries
  do not ship", which entails it for B6. This is the closest thing to a genuine third contradiction
  I found, and the **retitle is exactly what disposes of it**: the retraction is scoped to "as any
  slice's own argument", and B6 no longer argues it. The entailing sentence is a different, document-
  level claim, and it is already `D1`'s and handed to the reconciliation item at `:660`-`:661`.
- **`## How to read this file` `:33`**, which calls the `**The win.**` labels "headings that no
  longer exist in the spec at all". True as written: `grep 'The win\.'` over the spec returns
  nothing — B8's label was dropped and B6's replaced.

### DRY findings

- **The two edits added no duplication against the spec — re-derived, not accepted.** Implementing
  the maintainer pass's disclosed normalization independently, I get **rationale x post-move-spec
  overlap 52** and **left-the-spec shingles present in the rationale 161**, reproducing its "after"
  column exactly on both, against a rationale that now measures 8,595 distinct shingles. Edit 2's
  only quotation of live spec text is the five-word "But strawberry-graphql-django stopped there",
  which is **structurally incapable** of contributing an 8-word overlap shingle — so the zero is not
  merely measured, it is forced.
- **The keep is now recorded in exactly two places, which is the ruling's own count.** Edit 1 (the
  class entry) and edit 2 (the section entry). No third site records it, and candidates 2 and 3
  above were correctly left alone rather than extended — a third recording would be the tally defect
  this cycle has now filed twice.
- **Against the sibling rationales: unchanged and still clean.** The two edits add no run against
  `spec-002-…-rationale.md` or `spec-003-…-rationale.md`; the 17-shingle ordering-invariant run that
  was pass-1's Low-2 is still gone.
- **Existence challenge: none raised.** The pass adds no abstraction, helper, registry, or
  indirection; it edits prose in one file.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list
are unchanged, and none was authorized to change: the build plan's `## Build-wide context flags`
declares package source, `tests/`, and `examples/` read-only for the whole cycle.
`git diff --stat -- django_strawberry_framework/ tests/ examples/` → **empty**, so unlike pass 2
there is no concurrent-session entry to attribute; the one-line renumber sweep that was dirty then
is committed history now.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed clean in `git status --short`.

### Documentation / release sanity

Applies — the diff is entirely docs and one of the two files is an archived spec. Both were read end
to end this spawn.

- **The three baseline checkers, re-run rather than quoted.**
  - `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
    → `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**, character-
    identical to the build plan's pre-flight baseline.
  - `uv run python scripts/check_trailing_commas.py --check` on the spec, the rationale, and this
    artifact → **exit 0** on all three.
  - `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have
    glossary links.` **exit 0**. **Read-only form only**; the writing form was never invoked.
- **All ten anchors are single-carrier, re-derived per anchor rather than on the checker's exit
  code.** `grep -o "\[glossary-<anchor>\]" | wc -l` → **2** for every one of `configurationerror`,
  `djangooptimizerextension`, `djangotype`, `fk-id-elision`, `metaexclude`, `metafields`,
  `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `queryset-diffing` (1 body use + 1
  definition). The spec was not edited this pass, so this is a confirmation. The terms CSV was not
  opened: `git status --short docs/SPECS/appx/` shows only the rationale, as `??`.
- **Every link definition resolves on disk — re-run this spawn, because the reading expires and
  edit 1 adds a use.** Each target resolved from its own source file's directory and existence-
  tested: spec **11 / 11**, rationale **19 / 19**, **0 undefined, 0 unused, 0 of 30 missing**. None
  of the rationale's `../spec-NNN-….md` siblings points at a file the concurrent renumber moved.
- **In-page anchors resolve and the em-dash hazard is still avoided.** The repo's own
  `scripts/check_spec_glossary.py::github_anchor` over the spec's **15** headings → **15 unique
  slugs, 0 duplicates**; `#problem-statement` and `#proposed-improvements` both land on real
  headings. No new in-page anchor was added.
- **Structural properties.** Spec **216 lines / 26,480 bytes**; rationale **776 lines / 54,865
  bytes** (matching the report's post-edit figures). `grep -c '^```'` → **0 / 0**; no fence anywhere
  in either file. `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` → **no match** (exit 1) in both, so
  `AGENTS.md` rule 27 holds. `grep -nP '\]\((?!#|https?:)'` → **no match** (exit 1), so the
  reference-style convention is preserved, not merely unbroken. Both files carry
  `<!-- LINK DEFINITIONS -->` with all ten canonical group headers in order, and the archived
  companions correctly file under `<!-- docs/SPECS/ -->`.
- **The spec narrates no history.** `grep -niE 'as of (review )?round|amendment|retract|inverted|a
  later strawberry|no longer|used to |formerly|previously|has since'` returns **one** line, `:3`,
  whose only hits are "the former `## Priority and ordering` section" and "may no longer make" —
  rule-1 pointer vocabulary naming what was moved and where. The pass-1 Low-3 fix still holds at
  both sites.
- **Version strings / card IDs / KANBAN.** The spec carries no version or status header, so nothing
  could drift; the rationale's `DONE-004-0.0.3` and "eleven patch versions ago" still match
  `pyproject.toml`'s `0.0.14`. No card moved and this cycle wrote no DB. `KANBAN.md`, `KANBAN.html`,
  `docs/TREE.md`, `docs/GLOSSARY.md`, and `examples/fakeshop/db.sqlite3` are **all clean** at
  `346d6731` — re-derived this spawn rather than inherited, since the concurrent session reversed
  that state four times earlier in the cycle.
- **No script-rendered doc was regenerated**, so the staging-docstring check has no subject, and no
  obsolete "coming soon" / "planned" wording was introduced.
- **Archival unchanged.** The rationale lives directly at `docs/SPECS/appx/`, the archived-companion
  location `AGENTS.md` rule 26 names.
- **Verbatim survivals checked by comparison, not by reading.** B8's spec paragraph is byte-equal to
  its HEAD source with the `**The win.** ` prefix removed; B6's `**Public API.**` sentence is a
  verbatim prefix of its HEAD paragraph. Both are cited in the second Low.

### What looks solid

- **The ruling was implemented, not paraphrased.** Both edits are present, both carry every clause
  the decision specifies including the two reasons for the keep, both are re-flowed to the file's
  own wrap, and neither added a link definition or an in-page anchor. Where the file departs from
  the decision's summary it departs by being **more** complete (three surviving comparisons, not
  two), and I confirmed that against the spec sentence rather than against the plan's shorthand.
- **The spec really is untouched.** Not just equal in bytes: the whole 28-line insertion set was
  enumerated and accounted for against the move plus the three pass-1 edits, and
  `## Problem statement`'s first paragraph is byte-equal to HEAD. The decision's first clause is
  the one that would be cheapest to violate silently, and it was not.
- **The integration duty was taken seriously rather than performed.** Four candidates, each with a
  reason, and the one most open to challenge flagged to me by name. I disagree with none of the four
  dispositions after re-deriving them independently; the two sites I did find are in a section none
  of the four opened, and one of them long predates the decision.
- **The pass-2 Low was closed by deletion rather than by a better sentence, and that was the right
  branch.** Three tallies of one set became two records and a pointer, the ordinal-dependent
  paragraph now names its own subject, and B8's status claim reached the durable list R2 actually
  reads instead of a "test this first" note.
- **Measuring the number as it was written caught an error in it.** The apply-changes pass's "two B8
  rows" became "three" because the pass ran the grep while writing the sentence, and stated a list
  rather than a count as a result. I re-derived it: D24, D25, D26, none covering B8's opening
  paragraph. That is `BUILD.md` `## Claims are proven mechanically` working as designed, and it is
  the third time in this cycle a count has been wrong by one — which is the pattern behind both of
  my Lows.
- **Every invariant that had to survive did.** Ten single-carrier anchors, 30/30 link targets
  resolving after the renumber committed, 15/15 unique heading slugs, both in-page anchors
  resolving, the terms CSV never opened, `import_spec_terms --check` green, rule 27 holding in both
  files, zero fences in either, and no source, test, or example file changed by this cycle.

### Temp test verification

None. No temp test was written and none was warranted: this cycle changes no code path, so there is
nothing a test could exercise. `docs/builder/temp-tests/r1/` was not created in this pass either.
Every verification above is a read-only command over the two changed files, the read-only HEAD copy,
or the repo's own checker scripts.

**Static helper.** `scripts/review_inspect.py` was **not** run, and the skip is recorded here per
`worker-3.md` `## Static helper use`. `BUILD.md` `### When to run the helper during build` triggers
it on a new `.py` file, a touched file under `optimizer/` or `types/`, or 30+/50+ new lines of
logic. `git diff --stat -- django_strawberry_framework/ tests/ examples/` is empty, so no trigger
fires. No shadow file was read or written.

**Failability proofs.** The report's `None; this pass introduced no new boundary.` is verified
rather than accepted: `git diff -- django_strawberry_framework/` is empty, so there is no boundary,
guard, gate, or rejection path to prove. `worker-3.md`'s mandatory re-run floor is satisfied by an
**empty re-run set**, which it permits only when the diff introduces no boundary meeting the floor —
that condition holds by measurement. **No boundary was re-run and none was accepted on a builder's
record, because none exists.** Worker 3's source carve-out was not exercised: no production file was
mutated at any point in this pass.

**Hot-path budget.** Not owed. The plan declares `none`, and correctly — nothing in this diff runs
per request, per resolver, per row, per connection, or per outbound message.

**Floor verification.** Not owed. The plan declares scope `none`, and correctly — the diff touches
no Django / Strawberry / channels integration seam.

**Coverage.** No `pytest` run, no `--cov*` flag in any form, at any point in this pass.

### Notes for Worker 1 (spec reconciliation)

**This is the complete, current R2 handoff and it supersedes the pass-2 list.** R2 is the next item
and the same role, so nothing lives only in a closed section. Items 1-6 are the move report's
original six, 7-9 my pass-1 additions, 10-14 my pass-2 additions, and 15 is this pass's. Every item
was re-verified against the spec and the rationale on disk this spawn; the spec has not changed
since pass 2, so 1-8 and 11 stand at the same line numbers.

1. **`D5` leaves the spec with no extension-lifecycle statement at all.** R1 deleted the falsified
   spike and its recommendation rather than replacing them. The open question is whether the spec
   states the current construction form or points at `spec-029` Decision 3, which owns it. The build
   plan's anti-absorption rule, `docs/README.md` #"The optimizer is a module-level singleton wrapped
   in a factory", and `docs/GLOSSARY.md` all argue for the pointer; I agree. **What R2 must not do
   is transplant the corrected recommendation into spec-004** — that is the
   `**The scope trap specific to this spec.**` failure.
2. **`D24` is already discharged** by the `## Priority and ordering` deletion — all eight slices now
   sit under `## Proposed improvements` in heading order. Verify, do not perform.
3. **`### B6` `**Public API.**` says "classmethod"; HEAD ships a `@staticmethod`.** Kept verbatim on
   purpose; a one-word correction and R2's. Still present at spec `:108` (re-checked).
4. **`## Implementation checklist` bullet 2 is the last in-spec trace of the cache-lifetime spike**
   (spec `:174`, `- [x] B1 cache-lifetime spike (10-min investigation, precedes B1
   implementation)`). A checklist is contract scaffolding so R1 left it, but its parenthetical is a
   sequencing claim about work eleven versions shipped and the section it pointed at is gone. R2's
   call whether it is trimmed.
5. **`## References`' third paragraph is still dangling** (`D27`, spec `:169`): it cites a "skip
   Strawberry conversion" optimization "noted in B1's implementation" that `### B1` never noted, at
   HEAD or now. R1 neither created nor repaired it. The thing that did land is the deferred-
   conversion thunk, a different mechanism.
6. **`### B7`'s "No `_meta.get_fields()` call ever appears in the request path" was cut, but its
   contradiction survives elsewhere.** The contradicting sentence — `**Walker needs registry
   lookup.**`'s unregistered-model fallback at spec `:131` — is still there and still true, and
   `D23` records it as a documented dual contract. Nothing is owed; **R2 should simply not "restore"
   the deleted claim.**
7. **`D25` and `D28` are discharged and the move report's own handoff does not say so.** Both lived
   inside `## Priority and ordering` and went with it. The rationale's
   `### The former `## Priority and ordering`` entry records both correctly, so the durable record
   is complete — but an R2 working from the original list will hunt two sentences that no longer
   exist.
8. **`D6` is narrower than the drift table anticipated, and here is exactly how much.** The policy
   half is now stated in the spec (`**Cache storage.**`, spec `:23`) and is off R2's list. What
   remains is precisely three things, none of which appears anywhere in the spec — re-verified this
   spawn by absence grep, which returns only `:23` and the pre-existing `:27`: the **bound**
   (`256`), the **storage mechanism** (`OrderedDict` + `move_to_end`, and the `suppress(KeyError)`
   guard against the concurrent-eviction race), and the **batch size** (a quarter rather than one
   entry). `**Cache storage.**`'s plural "entries" is generic and neither states nor forecloses the
   batching, so R2 has a free hand there.
9. **Decided — do not re-open.** The escalated contract-level question (`## Problem statement`'s
   surviving competitive positioning) was ruled on by the maintainer. The canonical record, with the
   reasoning and the rejected alternatives each with its reason, is
   `docs/builder/build-004-optimizer_beyond-0_0_3.md` `## Maintainer decision — the surviving
   competitive positioning in `## Problem statement``. **Read it there rather than re-deriving it.**
   Its operative consequences for R2 are only these: the `## Problem statement` sentence at spec
   `:7` **stays byte-for-byte** and is not R2's to trim; the keep is recorded in the rationale at
   `:143`-`:152` and `:166`-`:169`, so a sweeper who finds a competitor comparison in the spec has
   already been answered; and the second paragraph's "This spec covers eight improvements that the
   existing libraries do not ship" framing is a **separate** claim, is `D1`'s, and is still R2's.
10. **Both Lows above are R1's, not R2's.** They are two one-clause corrections inside
    `## Provenance of this record` in the rationale, and they are the only things holding this item
    at `revision-needed`. No spec edit is owed by either.
11. **R2's `_optimizer_field_map` worklist is the rationale's bullet, not the build plan's `D22`
    row.** Re-derived this spawn: **6 occurrences across 5 sites in 3 sections** — spec `:84` (B4
    `**Walker needs registry lookup.**`), `:112` (B6's exposed-fields paragraph), `:129` (B7
    `**Mechanism.**`, **twice**), `:131` (B7 `**Walker needs registry lookup.**`), `:135` (B7
    `**Test surface.**`). `D22` counts four sites and omits `**Test surface.**`. Two riders on the
    same sweep: `:112` is the sole carrier of **both** `metafields` and `metaexclude`, so it must be
    rewritten with the links re-sited rather than dropped; and `:84` additionally still says the
    walker reads `_optimizer_hints` off the type class, which is `D16`'s retired mirror in the same
    sentence.
12. **`### B8`'s surviving opening paragraph is now on an R2-facing list — here is where.** It is
    the tenth bullet of the rationale's `## Standing notes` `### The status claims were left
    standing` (`:680`-`:685`). It states the package's own **pre-B8** behaviour in the present tense
    ("the optimizer blindly stacks another `.select_related("category")` on top", spec `:141`), and
    shipping B8 is what falsified it. The build plan's drift table carries **no** row for it: its
    three B8 rows (`D24`, `D25`, `D26`) name the document structure, the deleted ordering section,
    and the cut fence. **Work this item from the rationale bullet, not from the drift table.**
13. **The link-target disk check has an expiry and mine is the current reading, not the last word.**
    30/30 resolve at `346d6731`, with the concurrent renumber now committed. **R2 and R3 re-run it
    themselves rather than quoting this one**, and re-run `import_spec_terms --check` after any
    further concurrent DB write.
14. **Baseline state for Worker 0 to append** (reported, never reverted): `git status --short` was
    the same four cycle paths at the start and end of this pass — no churn at all, for the third
    consecutive pass. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`,
    `examples/fakeshop/db.sqlite3`, and `django_strawberry_framework/optimizer/predicates.py` are
    all clean at `346d6731`, so `## Concurrent-writable tracked binary / generated files` has
    recovered every member it lost — but R3 re-derives that rather than inheriting it.
15. **A standing hazard this cycle demonstrated three times, worth carrying into R2's own writing.**
    Three separate counts in this cycle were wrong by one (`_optimizer_field_map` "five mentions";
    the survival summary; "two B8 rows"), and a fourth — the rationale's shingle triple — was
    correct when written and falsified by a later edit in the same cycle. R2 rewrites more prose
    than R1 did, in the same durable files. **State the unit beside any count, state the method
    beside any measurement, and re-measure after the last edit rather than while making it.**

### Review outcome

`revision-needed`.

Two Lows, neither addressed nor rejected, and `worker-3.md`'s acceptance gate requires every High,
Medium, and Low finding to be addressed or intentionally rejected with a recorded reason. The
escalation carve-out does not reach them — that is for Medium-or-higher findings needing spec
context, and these need neither. Both are one-clause corrections inside one section of the
rationale; no spec edit is owed by either, and the spec must stay byte-identical.

**Everything the prompt sent me to grade came back clean.** The apply-changes pass closed both
halves of the pass-2 Low, took the finding's second option for the right reason, put B8's status
claim on the list R2 actually reads, and corrected its own draft count by measuring it as it wrote
it — which I re-derived: three B8 drift rows, none covering the paragraph. The maintainer-decision
pass implemented the ruling faithfully and completely: both edits present in the ruled shape,
re-flowed to the file's wrap, no link definition added, the spec byte-identical with all 28 added
lines individually accounted for, and the record now more complete than the ruling's own summary
(three surviving comparisons, not two — checked against the spec sentence). Its integration sweep
was honest: I re-derived all four candidates independently and disagree with none, including the
third, which it correctly flagged as its most challengeable call.

**What holds the item open is a fifth and sixth site, both in `## Provenance of this record`, and
neither of them the decision's fault.** One is the ruling's own defect shape at a new address — the
**Cut** label applied to eight paragraphs, two of which are byte-verbatim in the spec. The other is
a measurement this cycle's own pass-1 spec revision falsified and nobody refreshed, stated without
the normalization that would make it re-derivable at all. Both are in the section the pass-2 fix
substituted a pointer to, which is why they are worth closing now rather than carrying.

Per the build plan's `### Deviation 2` corollary this routes to **Worker 1**, not Worker 2. Worker 1
applies the two corrections, sets `Status: planned` again, and returns the artifact here.

### Working-tree churn observed during this review — reported, not reverted

**None.** `git status --short` was the same four entries at the start and at the end of the pass:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
```

`HEAD` is **`346d6731`**, re-derived this spawn, and it did not sweep this cycle's work:
`git log -1 -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns **`20a9752f`** and the
three artifacts are still untracked. That is the standing hazard check, done with `git log` rather
than `git status` alone. No stray untracked file appeared, and nothing was reverted.

---

## Build report (Worker 1, apply-changes pass 3)

Per the build plan's `### Deviation 2` corollary, an R1 `revision-needed` routes to Worker 1: the
same two rules that make Worker 1 the only role that may perform the move make it the only role
that may fix it. `Status:` is `planned` on return, which Worker 0 reads as "dispatch Worker 3" for
a pass-4 review. Every prior entry — all three of Worker 3's review sections included — is
untouched.

**Two Lows, both fixed; nothing rejected.** The spec was **not** reopened: both fixes are entirely
inside `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`, and the spec is byte-
identical to the file Worker 3 read at passes 2 and 3 (216 lines / 26,480 bytes, `git diff --stat`
still 28 insertions / 171 deletions). Worker 3's 15-item `### Notes for Worker 1 (spec
reconciliation)` was read and is R2's; nothing in it was acted on, item 9's settled maintainer
ruling included.

**Both Lows and the two further sites the sweep found have one root cause**, which is why the fix
is two edits and not five: `## Provenance of this record` states absolute claims about *where text
is* — "exists in neither file", "exist here and nowhere else", a shingle triple keyed to the
current spec — while the labels it states them under are an **index over items**. An index entry
cannot be absolute about every sentence inside its item, and each place it tried to be is a place
the spec falsifies.

### Low 1 — the `**Cut**` bullet, fixed at the label definition rather than on the bullet

**The finding reproduces, verified by comparison rather than by reading.** Against the read-only
HEAD copy, with each `**The win.** ` label prefix stripped: HEAD `:271` (B8) is **byte-equal** to
the current spec `:141`, and HEAD `:181` (B6) has the current spec `:108` as a **verbatim prefix**.
Of the eight HEAD `**The win.**` paragraphs those are the only two with any presence in the current
spec — the other six match nothing, exactly or as a prefix.

**The fix went to `## How to read this file`'s two-labels bullet, not to the `**Cut**` bullet the
finding cites.** The finding's own recommendation was a qualifying pointer on the bullet; this is a
deviation and the reason is the sweep below. The `**Cut**` list is not wrong *once the label is
honest* — it is wrong only under a definition that says "the text exists in **neither** file", and
that definition is the defect. Fixing the bullet and leaving the definition absolute would leave
the next item added to that list reproducing the defect, and would put a qualifier on one of three
list entries that need one. `AGENTS.md` rule 5 makes the root-cause fix the required one.

The label now reads as what it is: *Moved* and *Cut* file an **item** by where the bulk of it went;
both are index entries over whole sections, paragraphs, and clauses, so a cut item can still leave
a sentence standing in the spec, and a quotation here can be of surviving spec prose the entry is
discussing rather than of moved text; and **where the index and an item's own entry disagree about
a sentence, the entry is the accurate one.** That last clause is the direct answer to the finding's
statement of harm — a reader who resolves "did the win paragraphs leave the spec?" against the
index is now sent to the entry, which `## Review (Worker 3, pass 3)` confirms is correct.

**No tally was added anywhere.** The survivals are still enumerated once, in the `**The win.**`
entry, which is where `## Standing notes` already points a sweeper.

### The integration sweep — three further sites in the same section, two fixed by the same edits

The prompt makes the integration mine, and two prior sweeps had never opened this section. Every
site below was found by testing the section's assertions against the files on disk, not by reading.

1. **The `**Moved**` bullet asserted the same absence, and the spec falsifies it at seven
   addresses.** It read "Those wordings left the spec, so they exist here and nowhere else."
   Measured: of the **42** runs of 25+ characters this file reproduces inside quotation marks,
   **7** are present verbatim in the post-move spec — "blindly stacks another `.select_related(",
   "the optimizer blindly stacks another `.select_related(", "But strawberry-graphql-django stopped
   there", "This spec covers eight improvements", "a cache hit from one root field would return the
   wrong plan for another", "extract just those values from `info.variable_values`", and "build a
   `dict[str, FieldMeta]`". Every one is the file quoting live spec prose as the subject its entry
   is discussing. **Fixed in the same edit as Low 2**, by saying so.
2. **Three items are filed under both labels at once**, which the `**Moved**` bullet does in its own
   sentence: `### B3`'s `strict=True` sentence and `### B4`'s untyped-shapes clause are named there
   as quoted, and their items are listed six lines below under `**Cut**`; `## Priority and
   ordering`'s "pure polish item" sentence is named there while the whole section is listed under
   `**Cut**`. **Fixed by the Low-1 edit**, and this is the second reason it went to the definition:
   a per-item qualifier would have had to be written three times.
3. **`## How to read this file` said the section files every item under three labels; it has
   five.** The two extra — `**Restated in the spec, not moved**` and `**Deliberately left in the
   spec by this pass**` — are precisely the fates that resolve a survival, so undercounting them is
   what left the reader with only "moved or gone". **Fixed by the Low-1 edit**, which now names all
   five.

**Two candidates opened and deliberately left, recorded so pass 4 does not re-derive them.**

- **`## How to read this file` `:38`** — "Two entries key to headings that no longer exist in the
  spec at all (`## Priority and ordering` and the eight `**The win.**` paragraphs)". It is a claim
  about *headings and labels*, and no spec paragraph carries a `**The win.**` label. Left.
- **`### The eight `**The win.**` paragraphs` entry `:96`** — "The `**The win.**` label no longer
  appears in the spec." Worth naming because `## Review (Worker 3, pass 3)` supports a neighbouring
  judgement with "`grep 'The win\.'` over the spec returns nothing", and **it returns one line**:
  spec `:3`, the companion-pointer paragraph naming the class that moved. That is a mention, not a
  label on a paragraph, so the sentence is true as written and no reader is misled — but the grep
  behind it is not, and a pass-4 reviewer re-running it should not read the hit as a new finding.
  Left unedited; recorded instead.

### Low 2 — the shingle triple, re-keyed rather than refreshed

**The finding reproduces on both halves.** The triple was falsified by this cycle's own pass-1
`**Cache storage.**` revision, and it is not re-derivable: the file states no normalization, and
the two disclosed ones disagree by **288** shingles on the same 33,928-byte blob (4,646 against
4,934 at HEAD). Implementing the maintainer pass's disclosed normalization independently, I get the
triple as **1,853 / 161 / 1,692** — reproducing Worker 3's own re-derivation exactly, and a third
set of numbers none of which is in the file.

**The options, weighed rather than defaulted.** The prompt is right that "update the numbers" is the
wrong default here, and the decisive fact is not the staleness:

- **Refresh the triple and disclose the method** (the finding's preference) makes it re-derivable
  and *guarantees* it goes stale again immediately. R2 is the very next item, it is a spec-
  reconciliation pass, and Worker 3's own handoff item 15 says it "rewrites more prose than R1 did".
  A figure keyed to the **current spec** is falsified by design by the next item in the same cycle.
  This bullet has now been falsified once already by a **single sentence** of spec edit.
- **Drop the figures** honours this cycle's drop-the-tally precedent, but the finding is right that
  they do work the prose cannot: they are what lets a reader tell "the text is here" from "the text
  is gone" without re-running anything, and dropping them leaves "No section, paragraph, or fence
  was moved whole" as an unbacked assertion in a durable file, which is the shape `BUILD.md`
  `## Claims are proven mechanically` distrusts most.
- **Re-key the measurement to inputs that cannot move, and state the method** — taken. The pre-move
  spec is a frozen 33,928-byte blob git holds unchanged; this file is the other input. So the
  bullet now reports that this file reproduces **192 of the pre-move spec's 4,934** eight-word
  shingles, in **41** contiguous runs whose longest is **27 words** and whose median is **three
  shingles**, with the four-step method stated in one clause. Nothing in it is keyed to the current
  spec, so R2 cannot falsify it by editing the spec at all.

**The run structure is what carries the claim, which is why it is now stated.** "No section,
paragraph, or fence was moved whole" is *proved* by a longest run of 27 words, not by a total —
a percentage is consistent with one moved paragraph plus a lot of divergence, and a longest run of
27 words is not. The old form asserted the claim and then offered a number that could not support
it; the new form offers the number that does.

### Measured as written — and the first draft of the method clause falsified its own measurement

The method clause originally read "strip each file from `<!-- LINK DEFINITIONS -->`". Running the
method **as written** against the edited file is what caught it: the marker now appeared in the
body, so the split truncated the file at that very sentence and the run returned **848** shingles
and **0** reproduced, against 8,775 and 192. A disclosed method whose statement breaks any faithful
implementation of it is worse than no disclosure. Reworded to "drop each file's bottom link-
definition block", which names the same block without embedding its marker; `grep -c "LINK
DEFINITIONS"` over the rationale returns **1**, the real block. Every figure in the bullet was then
re-measured against the **final** file, after the last edit rather than while making it — the
standing hazard Worker 3's handoff item 15 names, hit and caught inside one pass.

### Files touched

- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — 2 edits: the two-labels bullet in
  `## How to read this file`, and the `**Moved**` bullet in `## Provenance of this record` (plus the
  one-clause correction of the method wording, inside the second edit). 776 -> 786 lines,
  54,865 -> 55,918 bytes (+1,053).
- `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` — **not touched this pass.** Neither finding owed
  a spec edit and the scope forbids a discretionary one.
- `docs/builder/bld-004-r1-rationale_move.md` — this section appended; `Status:` set to `planned`.

**No unasked-for edit was made.** The `**Cut**` bullet's list, the `**Deleted**` bullet, the
`**Restated in the spec, not moved**` bullet's five rules, and every `## Standing notes` entry are
byte-unchanged: the fix removed the false absolutes rather than re-stating any set, so nothing
elsewhere had to be kept in step. That is the pass-2 lesson applied rather than re-learned.

### Validation run — every result quoted verbatim

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
  -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**. Character-
  identical to the build plan's pre-flight baseline.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md docs/builder/bld-004-r1-rationale_move.md`
  -> **exit 0** on all three files.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have
  glossary links.` **exit 0**. **Read-only form only**; the writing form was never invoked.
- **Every link definition re-resolved on disk this spawn, not quoted.** Each target resolved from
  its own source file's directory and existence-tested: spec **11 definitions / 11 distinct uses**,
  rationale **19 / 19**, **0 undefined references, 0 unused definitions, 0 of 30 targets missing.**
  No definition was added or removed by either edit. **R2 and R3 re-run this rather than quoting
  it.**
- **Per-anchor 10-anchor constraint, re-derived.** `grep -o "\[glossary-<anchor>\]" | wc -l` -> **2
  for every one of the ten** (1 body use + 1 definition): `configurationerror`,
  `djangooptimizerextension`, `djangotype`, `fk-id-elision`, `metaexclude`, `metafields`,
  `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `queryset-diffing`. The spec was not
  edited this pass, so this is a confirmation. **The terms CSV was not opened**:
  `git status --short docs/SPECS/appx/` shows only the rationale, as `??`.
- **Byte / line count.**

| | lines | bytes |
|---|---|---|
| spec at Worker 3's pass-3 review | 216 | 26,480 |
| spec **now** | **216** | **26,480** (unchanged — not touched) |
| spec at HEAD (pre-move) | 359 | 33,928 |
| net move + revisions | **-143** | **-7,448 (-21.9%)** |
| rationale before this pass | 776 | 54,865 |
| rationale **now** | **786** | **55,918** (+1,053 over two edits) |

- `git diff --stat -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **28 insertions / 171
  deletions**, the hunk shape Worker 3 recorded at all three reviews — independent evidence the
  spec is byte-identical to the file pass 3 read.
- In-page anchors: the repo's own `scripts/check_spec_glossary.py::github_anchor` over the spec's
  **15** headings -> **15 unique slugs, 0 duplicates**; `#problem-statement` and
  `#proposed-improvements` both resolve. **No new in-page anchor was added** — the two-labels
  bullet's cross-reference to `## Provenance of this record` is a named textual pointer, as this
  file's other intra-file pointers are, because the em-dash slugger ambiguity the file documents
  applies to its own `###` headings.
- `grep -c '^```'` -> spec **0**, rationale **0**. No fence introduced.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files -> **no match** (exit 1). Rule 27 holds.
- `grep -nP '\]\((?!#|https?:)'` over both files -> **no match** (exit 1). Reference-style
  preserved.
- `grep -niE 'as of (review )?round|amendment|retract|inverted|a later strawberry'` over the spec ->
  **no match** (exit 1). The pass-1 Low-3 fix still holds.
- `grep -c "LINK DEFINITIONS"` over the rationale -> **1**. The method clause no longer embeds the
  marker it tells the reader to split on.
- `git diff --stat -- django_strawberry_framework/ tests/ examples/` -> **empty**. No source, test,
  or example file touched; no `pytest`, no `ruff` (no `.py` file changed), no coverage-shaped flag
  in any form.
- No `git stash`, `checkout`, `restore`, `worktree`, `commit`, or branch operation at any point. The
  read-only HEAD reference was `git show HEAD:docs/SPECS/spec-004-optimizer_beyond-0_0_3.md >
  <scratchpad outside the repo>/spec-004-HEAD.md` (**33,928 bytes / 359 lines** — the baseline the
  move was measured against has not moved).

### Duplication introduced by this pass: zero, measured

Both edits are new prose about the file's own labels, so neither could plausibly import spec text;
the one shape that could have is the `**Moved**` bullet's new clause about quotations, and it names
no wording it did not already name. Measured against the read-only HEAD copy under the **same**
normalization the pass-2 and maintainer passes disclosed, which is now also the normalization the
file itself states:

| measure | before this pass | after |
|---|---|---|
| rationale total shingles | 8,595 | 8,775 (+180) |
| left-the-spec shingles present in the rationale | 161 | **161 (unchanged)** |
| rationale x post-move-spec overlap | 52 | **52 (unchanged)** |
| overlap shingles this pass added | — | **0** |

Both duplication figures reproduce the maintainer pass's 161 / 52 exactly, which is the continuity
check that the method really is the same one. **The absolutes are still not comparable with Worker
3's readings** (4,934 against 4,646 at HEAD, a different normalization of the same blob) and no
claim is made that they are — but that gap is now closed for future readers, because the method is
in the durable file rather than only in this artifact.

### Notes for Worker 3 (pass 4)

- **The judgement to audit on Low 1 is the site, not the wording.** The finding asked for a
  qualifying phrase on the `**Cut**` bullet; I fixed the label definition instead, and left the
  `**Cut**` list byte-unchanged. The check is to read `## How to read this file`'s two-labels bullet
  and then the `**Cut**` bullet under it, and confirm the list is no longer making a false claim —
  then confirm the same correction covers the two further sites named under
  `### The integration sweep`, which is the reason a single site was chosen over three qualifiers.
- **The judgement to audit on Low 2 is the choice of inputs.** The bullet no longer measures against
  the current spec at all. The check is whether the new figure is (a) re-derivable from the stated
  method — re-run it — and (b) invariant to R2's spec edits, which is the property the old triple
  lacked and the reason a refresh was rejected.
- **The one place to look for an over-correction** is the `**Moved**` bullet's "Most of those
  wordings left the spec and exist here and nowhere else; a few quote spec prose that survived."
  That is deliberately qualitative: the population is 7 of 42 quoted runs of 25+ characters today,
  and a number there would be a fourth count in this file for a later pass to keep in step.
- **Two claims worth re-deriving rather than reading:** the 192 / 4,934 / 41-run measurement (run
  the stated method; it is four lines) and the 30/30 link-target disk check, which still expires.
- **One correction to a pass-3 supporting grep, filed as a note rather than a finding**, under
  `### The integration sweep`: `grep 'The win\.'` over the spec returns **one** line, not nothing.
  The judgement it supported is unaffected.
- The consolidated R2 handoff is Worker 3's own 15-item list in `## Review (Worker 3, pass 3)`.
  Nothing in it was acted on and nothing from this pass was staged for later without being written
  down. No temp test, no shadow file, no `docs/builder/temp-tests/` directory.

**Failability proofs.** None; this pass introduced no new boundary. `git diff --
django_strawberry_framework/` is empty, so there is no boundary, guard, gate, or rejection path to
prove.

**Hot-path budget.** Not applicable; the plan declares `none`, and correctly — nothing in this diff
runs per request, per resolver, per row, per connection, or per outbound message.

**Floor verification.** Not applicable; the plan declares floor-verification scope `none`, and
correctly — the diff touches no Django / Strawberry / channels integration seam.

**Coverage.** No `pytest` run, no `--cov*` flag in any form, at any point in this pass.

### Spec changes made (Worker 1 only)

**None.** The spec was not edited this pass. `git diff --stat` on it is unchanged at 28 insertions /
171 deletions and its byte count is identical to Worker 3's pass-2 and pass-3 readings (216 lines /
26,480 bytes), so the three pass-1 revision edits remain the whole of this cycle's spec delta.

**Spec status-line re-verification** (`worker-1.md` `## Spec status-line re-verification`, re-run
this spawn as every Worker 1 spawn must): spec-004 carries **no** `Status:` / owner / target-release
/ predecessor header block — lines 1-5 are the title, the companion-pointer paragraph, and
`## Problem statement`. Nothing in them is a status line this build has falsified, so no header edit
was owed, and none could have been made this pass in any case.

### Working-tree churn observed during this pass — reported, not reverted

**None.** `git status --short` was the same four entries at the start and at the end of the pass,
for the fourth consecutive pass:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
```

`HEAD` is **`346d67312599c0536980969caa39085ab3885ae8`**, re-derived this spawn rather than quoted,
and it did **not** sweep this cycle's work: `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-
0_0_3.md` still returns **`20a9752f`**, and the rationale, this artifact, and the build plan are
all still untracked. That is the standing hazard check, done with `git log` rather than
`git status` alone. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, and
`examples/fakeshop/db.sqlite3` are all still clean — but pass 4 re-derives that rather than
inheriting this reading, since the concurrent session reversed that state four times earlier in
this cycle.

---

## Review (Worker 3, pass 4)

Read in order, as the prompt directs: `docs/builder/worker-3.md` (full), `AGENTS.md`, `START.md`,
`docs/builder/BUILD.md` (full), `docs/builder/ARTIFACT.md`, `docs/README.md`,
`examples/fakeshop/test_query/README.md`, `docs/builder/build-004-optimizer_beyond-0_0_3.md`
including its settled `## Maintainer decision — the surviving competitive positioning in
`## Problem statement``, this artifact end to end in the prescribed order (plan, move report,
`## Review (Worker 3)`, apply-changes, `## Review (Worker 3, pass 2)`, apply-changes 2,
maintainer-decision pass, `## Review (Worker 3, pass 3)`, apply-changes 3), the spec, the rationale,
and the pristine HEAD spec obtained read-only as `git show
HEAD:docs/SPECS/spec-004-optimizer_beyond-0_0_3.md > <scratchpad outside the repo>/spec-004-HEAD.md`.
No `git stash` / `checkout` / `restore` / `worktree` at any point, and no prior entry was edited.

`HEAD` re-derived this spawn rather than quoted: **`346d67312599c0536980969caa39085ab3885ae8`**;
the HEAD spec blob is `fa50bb7e0d77357715b1c798648a4691ccee5cc5`, **33,928 bytes / 359 lines**, 16
fence markers. `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns
**`20a9752f`** and the three artifacts are still untracked, so no concurrent commit has swept this
cycle's work. `git status --short` is the same four cycle paths and nothing else.

**Nothing below is quoted from any build report.** Every figure was re-derived from the files on
disk this spawn.

### High:

None.

### Medium:

#### Three `**Claims the spec no longer makes**` blocks retract claims the spec demonstrably still makes — the ruled-on defect class, at addresses no sweep has tested

The maintainer decision was issued because the `**The win.**` entry's retracted-claims list named
two claims the surviving `## Problem statement` still makes, and its stated reason is general: a
list like that "would leave the record at war with itself". The ruling fixed that one block by
scoping its title. **The same defect stands, unscoped, in at least three of the other ten blocks.**
The two integration sweeps that opened those blocks (the maintainer pass's candidate 1 and my own
pass-3 re-derivation of it) both tested them for *competitor-comparison material* only — a narrower
question than "does the spec still make this claim?" — so the general case has never been tested.

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:560
**Claims the spec no longer makes.** That `_meta.get_fields()` never appears in the request path.
That the walker reads a `_optimizer_field_map` class attribute.
```

The spec still says exactly that, at three sites inside `### B7` alone — `:129` ("Stash it as
`cls._optimizer_field_map`. The walker reads `target_type._optimizer_field_map` instead of calling
`model._meta.get_fields()`."), `:131` ("read `_optimizer_field_map`"), `:135` ("Assert
`_optimizer_field_map` is populated"). The first half of the same bullet is correct: `_meta.get_fields()`
"never appears in the request path" *was* cut, and I confirmed the spec no longer carries it.

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:441
**Claims the spec no longer makes.** That hints are read off a `_optimizer_hints` class attribute.
That the hint kinds are dispatched in a defined order.
```

Spec `:84`: "To read `_optimizer_hints`, it must look up the type class via `registry.get(model)`."

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:597
**Claims the spec no longer makes.** That the diff returns a plan alone. That not mutating the
cached plan is a discipline the builder must maintain by hand.
```

Spec `:149` still states it as exactly that discipline — "B8 must not modify `plan.select_related`
or `plan.prefetch_related` in place … Instead, build a new plan (or a shallow copy)" — and the same
entry's own body says so four lines earlier: "The **requirement** stayed in the spec."

**Why this is a defect a reader acts on, not a wording preference.** The retracted-claims list is one
of the three things `BUILD.md` `## Spec rationale extraction` requires every entry to carry, and R2
is the item that reads them. The `_optimizer_field_map` sweep is the single largest item on R2's
worklist (handoff item 11; the build plan's `D22`), and `### B7`'s entry tells R2 that retraction is
already done. **The file contradicts itself on it**: `## Standing notes` `:675`-`:682` enumerates
those very sites as claims left standing, in the durable do-not-miss list, and adds that `### B4`'s
`**Walker needs registry lookup.**` "additionally still says the walker reads `_optimizer_hints` off
the type class" — the exact sentence `:441` says the spec no longer carries.

It also interacts with this pass's own edit 1. The new tie-break rule reads "**Where the index and
an item's own entry disagree about a sentence, the entry is the accurate one.**" For this class the
entry is the *in*accurate one and `## Standing notes` is right, so a reader who follows the new rule
is routed to the wrong source. That is the concrete answer to the question the rule invites, and it
is why I am filing rather than noting.

**Two weaker members, named so the fix is scoped once rather than three times.** `### B3` `:400`
retracts "That the lazy-load probe has exactly two arms" while spec `:55` still names two and only
two (the entry's own body says "The section names two"); `### B5` `:480` retracts "That the
optimizer stashes one key on the context" while spec `:98` still presents one key as B5's mechanism
(the build plan's `D18` is that row). Neither is as clean as the three above — the spec never writes
the word "exactly", and B5's key count is arguable across sections — but both are the same shape and
both fall out of one root-cause fix.

**Recommended change.** One decision, applied once, not five per-entry rewrites. Either (a) scope
the label the way the ruling scoped edit 1 — state at the label's definition that a
`**Claims the spec no longer makes**` block records the claims a decision is no longer **entitled**
to make (`BUILD.md`'s own wording is "any claim the decision once made and **may** no longer make",
and this file's H1 and spec `:3` both use "may no longer make"), with surviving sites pointed at
`## Standing notes`; or (b) remove from each block the items the spec still states, which loses
nothing because each entry's body already records the departure and `## Standing notes` already
lists the live sites. **(a) is the DRY branch and matches the ruling's own instinct** (retitle plus a
positive record, rather than a per-item qualifier). Whichever branch is taken, do not add a tally.

Note for the fixer: (a) is a *reading* of the heading that the maintainer decision resolved in the
opposite direction for the `**The win.**` block, so if (a) is chosen the ruling's premise should be
re-checked against it rather than assumed compatible. Worker 1 owns that call; it needs no spec
context Worker 2 could not supply, so it is not escalated.

**Test expectation.** None; no behaviour changes. The verification is the one applied above: take
each `**Claims the spec no longer makes**` bullet and grep the post-move spec for the claim it
retracts.

### Low:

#### `## Standing notes` tells R2 that `_validate_meta` "does not exist"; it exists, and it is the symbol the spec's `**Validation.**` sentence names

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:683
- `### B4` `**Validation.**` names a `_validate_meta` symbol that does not exist, and understates
  what the shipped gates reject.
```

Verified at source rather than reasoned about: `django_strawberry_framework/types/base.py::_validate_meta`
is a live function, called from the type metaclass path —
`django_strawberry_framework/types/base.py #"validated = _validate_meta(cls, meta)"` — and its own
docstring lists `optimizer_hints` declaration-shape validation among its numbered steps. What is
actually true is narrower and different: `_validate_meta` normalizes `Meta.optimizer_hints` (through
`::_meta_optimizer_hints`), while the two rejections the spec attributes to it — unknown hint field
names and non-`OptimizerHint` values — live in `::_validate_optimizer_hints`, called on the next
line from the same `__init_subclass__`.

The claim is inherited uncritically from the build plan's `D17` row, which says the same thing and is
wrong on the same point. The move report's own list of rows re-verified against source does not
include this one, and no review pass checked it either: my pass-1 walk of all 28 drift rows confirmed
that the *spec sentences* still stand, not that the table's characterization of HEAD is right.

**Why it matters, and why Low rather than Medium.** It is the durable R2 worklist, and the sentence
it describes (spec `:86`) is the **sole carrier of the `configurationerror` glossary anchor** — the
highest-risk anchor-bearing sentence R2 still has to rewrite. A rewrite starting from "the symbol is
a phantom" produces a different and wrong correction from one starting from "the symbol exists; the
gate it names is the sibling function called beside it". But nothing in R1's own output turns on it —
R1 correctly left the sentence standing either way — which is what keeps it at Low, exactly as the
pass-1 card-import-chain Low was.

**Recommended change.** One sentence: name `_validate_meta` as the existing entry point that
normalizes the hints and `_validate_optimizer_hints` as the gate that performs the two rejections the
spec attributes to `_validate_meta`. The build plan's `D17` row carries the same error; it is Worker
0's file, so it is routed under `### Notes for Worker 1` below rather than fixed here.

**Test expectation.** None; no behaviour changes.

### DRY findings

- **The two edits added no duplication against the spec, and I re-derived it under the file's own
  now-stated method rather than under mine.** Rationale x post-move-spec overlap **52**;
  left-the-spec shingles present in the rationale **161**; rationale total **8,775** distinct
  shingles. Both duplication figures reproduce the apply-changes pass's "after" column exactly. The
  method is now in the durable file, so this is the first pass where a reviewer and a builder measure
  the same way — the 4,646-versus-4,934 gap that made three passes' absolutes incomparable is closed
  at the source rather than papered over in an artifact.
- **Against the sibling rationales: unchanged and still clean.** The two edits add no run against
  `spec-002-…-rationale.md` or `spec-003-…-rationale.md`; the 17-shingle ordering-invariant run that
  was pass-1's Low-2 is still gone.
- **No tally was added by either edit, which was the constraint most likely to be violated.** The
  `**Cut**` bullet's list, the `**Deleted**` bullet, the `**Restated in the spec, not moved**`
  bullet's five rules and every `## Standing notes` entry are byte-unchanged; the fix removed
  absolutes rather than restating any set, so nothing elsewhere had to be kept in step. That is the
  pass-2 lesson applied rather than re-learned, and it is the reason the +1,053 bytes buy no new
  maintenance surface.
- **The Medium above is not a DRY finding but it is a DRY-shaped fix**: three (or five) per-entry
  rewrites collapse to one statement at the label, which is the same root-cause shape this pass used
  for Low 1.
- **Existence challenge: none raised.** The pass adds no abstraction, helper, registry, or
  indirection; it edits prose in one file.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list
are unchanged, and none was authorized to change: the build plan's `## Build-wide context flags`
declares package source, `tests/`, and `examples/` read-only for the whole cycle.
`git diff --stat -- django_strawberry_framework/ tests/ examples/` → **empty**, so there is no
concurrent-session entry to attribute this pass.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed clean in `git status --short`.

### Documentation / release sanity

Applies — the diff is entirely docs and one of the two files is an archived spec. Both were read end
to end this spawn.

- **The three baseline checkers, re-run rather than quoted.**
  - `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
    → `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**,
    character-identical to the build plan's pre-flight baseline.
  - `uv run python scripts/check_trailing_commas.py --check` on the spec, the rationale, and this
    artifact → **exit 0** on all three.
  - `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have
    glossary links.` **exit 0**. **Read-only form only**; the writing form was never invoked.
- **All ten anchors are single-carrier**, re-derived per anchor rather than on the checker's exit
  code: `grep -o "\[glossary-<anchor>\]" | wc -l` → **2** for every one of `configurationerror`,
  `djangooptimizerextension`, `djangotype`, `fk-id-elision`, `metaexclude`, `metafields`,
  `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `queryset-diffing`. The spec was not
  edited this pass. The terms CSV was not opened: `git status --short docs/SPECS/appx/` shows only
  the rationale, as `??`.
- **Every link definition resolves on disk — re-run this spawn, because the reading expires.** Each
  target resolved from its own source file's directory and existence-tested: spec **11 definitions /
  11 distinct uses** (20 total uses), rationale **19 / 19** (48 total uses), **0 undefined, 0 unused,
  0 of 30 targets missing.** None of the rationale's ten `../spec-NNN-….md` sibling links points at a
  file the concurrent renumber moved.
- **In-page anchors resolve and the em-dash hazard is still avoided.** The repo's own
  `scripts/check_spec_glossary.py::github_anchor` over the spec's **15** headings → **15 unique
  slugs, 0 duplicates**; `#problem-statement` and `#proposed-improvements` both land on real
  headings. No new in-page anchor was added.
- **Structural properties.** Spec **216 lines / 26,480 bytes**, `git diff --stat` **28 insertions /
  171 deletions** — the same hunk shape recorded at all three prior reviews, so the spec is
  byte-identical to what pass 3 read. Rationale **786 lines / 55,918 bytes**. `grep -c '^```'` →
  **0 / 0**; `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` → **no match** (exit 1) in both, so `AGENTS.md`
  rule 27 holds; `grep -nP '\]\((?!#|https?:)'` → **no match** (exit 1), so the reference-style
  convention is preserved. Both files carry `<!-- LINK DEFINITIONS -->` with all ten canonical group
  headers in order.
- **The spec narrates no history.** `grep -niE 'as of (review )?round|amendment|retract|inverted|a
  later strawberry|no longer|used to |formerly|previously|has since'` returns **one** line, `:3`,
  whose only hits are "the former `## Priority and ordering` section" and "may no longer make" —
  rule-1 pointer vocabulary. The pass-1 Low-3 fix still holds at both sites.
- **Version strings / card IDs / KANBAN.** The spec carries no version or status header, so nothing
  could drift; the rationale's `DONE-004-0.0.3` and "eleven patch versions ago" match
  `pyproject.toml`'s `0.0.14` (0.0.3 → 0.0.14 is eleven). No card moved and this cycle wrote no DB.
  `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, and `examples/fakeshop/db.sqlite3`
  are **all clean** — re-derived this spawn rather than inherited.
- **No script-rendered doc was regenerated**, so the staging-docstring check has no subject, and no
  obsolete "coming soon" / "planned" wording was introduced.
- **Archival unchanged.** The rationale lives directly at `docs/SPECS/appx/`, the archived-companion
  location `AGENTS.md` rule 26 names.

### What looks solid

**The five graded items, each re-derived rather than confirmed.**

1. **Low 1 — the redefinition, graded as a redefinition and not as a symptom.** The finding's own
   recommendation was a qualifying pointer on the `**Cut**` bullet; the pass instead rewrote the
   label definition in `## How to read this file` `:19`-`:27` and left the `**Cut**` list
   byte-unchanged. **The argument for the deviation holds and the deviation is the better fix.** The
   bullet was only wrong under a definition asserting absolute location, so the definition is where
   the defect lived; and the same edit closes two of the three further sites, which a per-bullet
   qualifier could not have done without being written three times. I re-derived the symptom rather
   than reading it: stripping each `**The win.** ` prefix from the read-only HEAD copy, of the eight
   HEAD paragraphs (`:17`, `:50`, `:82`, `:115`, `:158`, `:181`, `:239`, `:271`) exactly two have any
   presence in the current spec — HEAD `:271` is **byte-equal** to spec `:141`, and spec `:108` is a
   **verbatim prefix** of HEAD `:181`. The other six match nothing, exactly or as a prefix. The
   redefinition — labels file an *item* by where its bulk went, both are index entries over sections
   / paragraphs / clauses, a cut item can still leave a sentence standing in the spec — makes the
   `**Cut**` list honest for that population without restating what survived.
2. **The tie-break rule is sound as scoped, and I tested it rather than assenting to it.** "Where
   the index and an item's own entry disagree about a sentence, the entry is the accurate one" does
   **not** license a wrong index indefinitely, because it is paired with a change to what the index
   *asserts*: the absolutes became declared item-level coarseness, so the index is no longer making a
   claim the entries falsify — it is making a coarser claim, and saying so. A precedence rule that
   resolves declared coarseness is sound; one that excused an undeclared falsehood would not be, and
   that is the version this is not. It is also correctly narrow — scoped to a disagreement "about a
   sentence", so it does not excuse an item filed under the wrong label outright. Its one real cost
   is that it makes an index-versus-entry mismatch unfileable by any future reader, and the Medium
   above is the case where that bites: there the *entry* is the wrong one, and the rule points at it.
   That is a finding about those entries, not about the rule.
3. **The integration sweep's three further sites — re-derived, and two of the three reproduce
   exactly.** The **7** is exact: implementing the extraction that produces it (quoted runs paired
   within a paragraph, ≥25 characters, tested verbatim against the flattened post-move spec), I get
   **the same seven strings, character for character**, including the two that truncate at
   `` `.select_related( `` — "blindly stacks another `` `.select_related( ``", "the optimizer blindly
   stacks another `` `.select_related( ``", "But strawberry-graphql-django stopped there", "This spec
   covers eight improvements", "a cache hit from one root field would return the wrong plan for
   another", "extract just those values from `info.variable_values`", and "build a `dict[str,
   FieldMeta]`". **The denominator does not reproduce under the method that yields the numerator: I
   get 37, not 42.** 42 is what I get from a different pairing (code-span-aware, whole-body), whose
   numerator is 1. This is recorded rather than filed, and deliberately: the figure lives **only in
   this per-cycle artifact**, the durable `**Moved**` bullet carries no number at all — "Most of those
   wordings left the spec and exist here and nowhere else; a few quote spec prose that survived" —
   which is the right call, and the seven counterexamples that do the argumentative work are exact.
   Nothing a reader acts on turns on 37 versus 42. The **label count reproduces**:
   `## Provenance of this record` carries five labels (**Moved**, **Cut**, **Deleted with no account
   kept**, **Restated in the spec, not moved**, **Deliberately left in the spec by this pass**) and
   `## How to read this file` now names all five — two plus three, as written.
4. **Low 2 — all four re-keyed figures reproduce exactly from the file's own stated method, on a
   first independent implementation.** This is the point of stating a method and this was its first
   test by a reader who did not write it. Following "drop each file's bottom link-definition block,
   fold every non-alphanumeric run to whitespace, lowercase, take distinct 8-word shingles": the
   pre-move blob carries **4,934** distinct shingles, the rationale reproduces **192** of them, in
   **41** contiguous runs over the HEAD word stream whose longest is **20 shingles = 27 words** and
   whose median is **3 shingles**. Four figures, four exact matches, written from the four-line method
   with no reference to any prior pass's arithmetic. **The choice of inputs is the right one and I
   tested the property, not just the numbers:** both inputs are outside R2's reach — the 33,928-byte
   blob git holds unchanged, and the rationale itself — so no spec edit can falsify this the way a
   single sentence falsified the old triple. The run structure is also what actually carries "no
   section, paragraph, or fence was moved whole": a longest run of 27 words proves it where a
   percentage never could, which is a real improvement over the form it replaced rather than a
   refresh of it.
5. **The self-falsifying method clause was caught and the rewording holds.** `grep -c "LINK
   DEFINITIONS"` over the rationale returns **1** — the real bottom block. Running the method as
   written no longer truncates the file at its own description of itself, which is why my
   implementation of it landed on the file's own numbers rather than on 848 / 0. Finding this by
   *running* a disclosed method rather than by reading it is the behaviour that makes a disclosure
   worth having.

**And the pass-3 grep correction is right; mine was the wrong reading.** `grep 'The win\.'` over the
spec returns **one** line, not nothing: spec `:3`, the companion-pointer paragraph naming the class
that moved. The judgement it supported is unaffected and I re-verified that independently — no spec
paragraph carries a `**The win.**` label, so `## How to read this file` `:38` ("headings that no
longer exist in the spec at all") and the entry's `:106` ("The `**The win.**` label no longer appears
in the spec") are both true as written; `:3` is a mention inside a code span, not a label. That is
the fourth count in this cycle to be corrected by re-measurement, and the second of mine.

**My own sweep, run independently rather than confirming the pass's five.** I enumerated every
assertion of absence in the rationale (`grep -niE 'no longer|nowhere|neither file|left the spec|not
restated|does not exist|never built|no such|carries no'`) and tested each against the spec or against
package source. Everything held except the two findings above. Specifically verified at source, none
of which any pass had checked: `build_dotted_path`, `planned_relation_paths` and
`_collect_reachable_types` are absent package-wide; no `cls._optimizer_hints` / `cls._optimizer_field_map`
attribute form exists; `optimizer/_context.py` owns exactly **five** keys; `optimizer/plans.py::diff_plan_for_queryset`
returns `tuple[OptimizationPlan, Any]`; `optimizer/hints.py::OptimizerHint.strategy` exists;
`optimizer/extension.py::DjangoOptimizerExtension.check_schema` is a `@staticmethod`, dedupes on a
`set[tuple[type[models.Model], str]]`, and recurses into interface implementations;
`optimizer/field_meta.py #"and not has_composite_pk(related_model)"` is the composite-pk exclusion the
`### B2` entry claims; no `check_optimizer` command exists anywhere, `KANBAN.md` / `KANBAN.html`
included; and the HEAD `### B1` section never mentioned the "skip Strawberry conversion" optimization
`## References` attributes to it, so that reference was dangling on arrival exactly as recorded.

**Everything else that had to survive did.** Ten single-carrier anchors, 30/30 link targets resolving,
15/15 unique heading slugs, both in-page anchors resolving, the terms CSV never opened,
`import_spec_terms --check` green, rule 27 holding in both files, zero fences in either, the spec
byte-identical for a third consecutive pass, and no source, test, or example file changed by this
cycle.

### Temp test verification

None. No temp test was written and none was warranted: this cycle changes no code path, so there is
nothing a test could exercise. `docs/builder/temp-tests/r1/` was not created in this pass either.
Every verification above is a read-only command over the two changed files, the read-only HEAD copy,
package source, or the repo's own checker scripts; the two measurement scripts I wrote live in a
scratchpad **outside the repository** and are not build artifacts.

**Static helper.** `scripts/review_inspect.py` was **not** run, and the skip is recorded here per
`worker-3.md` `## Static helper use`. `BUILD.md` `### When to run the helper during build` triggers it
on a new `.py` file, a touched file under `optimizer/` or `types/`, or 30+/50+ new lines of logic.
`git diff --stat -- django_strawberry_framework/ tests/ examples/` is empty, so no trigger fires. The
package source I read this pass was read-only evidence for the Low, not a diff. No shadow file was
read or written.

**Failability proofs.** The report's `None; this pass introduced no new boundary.` is verified rather
than accepted: `git diff -- django_strawberry_framework/` is empty, so there is no boundary, guard,
gate, or rejection path to prove. `worker-3.md`'s mandatory re-run floor is satisfied by an **empty
re-run set**, which it permits only when the diff introduces no boundary meeting the floor — that
condition holds by measurement. **No boundary was re-run and none was accepted on a builder's record,
because none exists.** Worker 3's source carve-out was not exercised: no production file was mutated
at any point in this pass.

**Hot-path budget.** Not owed. The plan declares `none`, and correctly — nothing in this diff runs per
request, per resolver, per row, per connection, or per outbound message.

**Floor verification.** Not owed. The plan declares scope `none`, and correctly — the diff touches no
Django / Strawberry / channels integration seam.

**Coverage.** No `pytest` run, no `--cov*` flag in any form, at any point in this pass.

### Notes for Worker 1 (spec reconciliation)

**This is the complete, current R2 handoff and it supersedes the pass-3 list.** R2 is the next item
and the same role, so nothing lives only in a closed section. Items 1-8 and 10-15 are re-issued from
pass 3 with every line reference re-checked against the files on disk this spawn (the spec has not
changed since pass 2, so its references are unmoved; the rationale grew 776 → 786 lines, so its
references have). Item 9 is **decided**. Items 16-18 are this pass's.

1. **`D5` leaves the spec with no extension-lifecycle statement at all.** R1 deleted the falsified
   spike and its recommendation rather than replacing them. The open question is whether the spec
   states the current construction form or points at `spec-029` Decision 3, which owns it. The build
   plan's anti-absorption rule, `docs/README.md` #"The optimizer is a module-level singleton wrapped
   in a factory", and `docs/GLOSSARY.md` all argue for the pointer; I agree. **What R2 must not do is
   transplant the corrected recommendation into spec-004** — that is the
   `**The scope trap specific to this spec.**` failure.
2. **`D24` is already discharged** by the `## Priority and ordering` deletion — all eight slices now
   sit under `## Proposed improvements` in heading order. Verify, do not perform.
3. **`### B6` `**Public API.**` says "classmethod"; HEAD ships a `@staticmethod`.** Kept verbatim on
   purpose; a one-word correction and R2's. Spec `:108`, re-checked, and I re-confirmed the
   `@staticmethod` at `optimizer/extension.py::DjangoOptimizerExtension.check_schema` this spawn.
4. **`## Implementation checklist` bullet 2 is the last in-spec trace of the cache-lifetime spike**
   (spec `:174`, `- [x] B1 cache-lifetime spike (10-min investigation, precedes B1 implementation)`).
   A checklist is contract scaffolding so R1 left it, but its parenthetical is a sequencing claim
   about work eleven versions shipped and the section it pointed at is gone. R2's call whether it is
   trimmed.
5. **`## References`' third paragraph is still dangling** (`D27`, spec `:169`): it cites a "skip
   Strawberry conversion" optimization "noted in B1's implementation" that `### B1` never noted. I
   re-verified against the read-only HEAD copy this spawn — the HEAD `### B1` section carries no such
   mention either, so the reference was dangling on arrival. R1 neither created nor repaired it.
6. **`### B7`'s "No `_meta.get_fields()` call ever appears in the request path" was cut, but its
   contradiction survives elsewhere.** The contradicting sentence — `**Walker needs registry
   lookup.**`'s unregistered-model fallback at spec `:131` — is still there and still true, and `D23`
   records it as a documented dual contract. Nothing is owed; **R2 should simply not "restore" the
   deleted claim.**
7. **`D25` and `D28` are discharged and the move report's own handoff does not say so.** Both lived
   inside `## Priority and ordering` and went with it. The rationale's `### The former `## Priority
   and ordering`` entry (`:600`-`:653`) records both correctly, so the durable record is complete —
   but an R2 working from the original list will hunt two sentences that no longer exist.
8. **`D6` is narrower than the drift table anticipated, and here is exactly how much.** The policy
   half is stated in the spec (`**Cache storage.**`, spec `:23`) and is off R2's list. What remains is
   precisely three things, none of which appears anywhere in the spec — re-verified this spawn by
   absence grep, which returns only `:23` and the pre-existing `:27`: the **bound** (`256`), the
   **storage mechanism** (`OrderedDict` + `move_to_end`, and the `suppress(KeyError)` guard against
   the concurrent-eviction race), and the **batch size** (a quarter rather than one entry — I
   confirmed `optimizer/extension.py #"to_remove = max(1, _MAX_PLAN_CACHE_SIZE // 4)"` at HEAD).
   `**Cache storage.**`'s plural "entries" is generic and neither states nor forecloses the batching.
9. **Decided — do not re-open.** The escalated contract-level question (`## Problem statement`'s
   surviving competitive positioning) was ruled on by the maintainer. The canonical record — the
   decision, its reasoning, and the rejected alternatives each with the reason it lost — is
   `docs/builder/build-004-optimizer_beyond-0_0_3.md` `## Maintainer decision — the surviving
   competitive positioning in `## Problem statement``. **Read it there; it is not restated here and it
   is not R2's to re-derive.** Its operative consequences for R2 are only these: the sentence at spec
   `:7` **stays byte-for-byte**; the keep is recorded in the rationale at `:153`-`:162` and
   `:176`-`:179`, so a sweeper who finds a competitor comparison in the spec has already been
   answered; and `## Problem statement`'s "eight improvements that the existing libraries do not ship"
   framing is a **separate** claim, is `D1`'s, and is still R2's.
10. **The Medium and the Low above are R1's, not R2's.** Both are corrections inside the rationale;
    neither owes a spec edit, and the spec must stay byte-identical.
11. **R2's `_optimizer_field_map` worklist is the rationale's bullet, not the build plan's `D22`
    row.** Re-derived this spawn: **6 occurrences across 5 sites in 3 sections** — spec `:84` (B4
    `**Walker needs registry lookup.**`), `:112` (B6's exposed-fields paragraph), `:129` (B7
    `**Mechanism.**`, **twice**), `:131` (B7 `**Walker needs registry lookup.**`), `:135` (B7
    `**Test surface.**`). `D22` counts four sites and omits `**Test surface.**`. Two riders on the
    same sweep: `:112` is the sole carrier of **both** `metafields` and `metaexclude`, so it must be
    rewritten with the links re-sited rather than dropped; and `:84` additionally still says the
    walker reads `_optimizer_hints` off the type class, which is `D16`'s retired mirror in the same
    sentence. **See the Medium above before working this item** — `### B7`'s and `### B4`'s
    retracted-claims lists currently say this retraction is already made.
12. **`### B8`'s surviving opening paragraph is on an R2-facing list — here is where.** It is the
    tenth bullet of the rationale's `## Standing notes` `### The status claims were left standing`
    (`:690`-`:695`). It states the package's own **pre-B8** behaviour in the present tense ("the
    optimizer blindly stacks another `.select_related("category")` on top", spec `:141`), and shipping
    B8 is what falsified it. The build plan's drift table carries **no** row for it: its three B8 rows
    (`D24`, `D25`, `D26`) name the document structure, the deleted ordering section, and the cut
    fence. **Work this item from the rationale bullet, not from the drift table.**
13. **The link-target disk check has an expiry and mine is the current reading, not the last word.**
    30/30 resolve at `346d6731`. **R2 and R3 re-run it themselves rather than quoting this one**, and
    re-run `import_spec_terms --check` after any further concurrent DB write.
14. **Baseline state for Worker 0 to append** (reported, never reverted): `git status --short` was the
    same four cycle paths at the start and end of this pass — no churn at all, for the fourth
    consecutive pass. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`,
    `examples/fakeshop/db.sqlite3`, and `django_strawberry_framework/optimizer/predicates.py` are all
    clean at `346d6731` — but R3 re-derives that rather than inheriting it, since the concurrent
    session reversed that state four times earlier in the cycle.
15. **A standing hazard this cycle has now demonstrated five times, worth carrying into R2's own
    writing.** Counts wrong by one or unreproducible: `_optimizer_field_map` "five mentions"; the
    survival summary; "two B8 rows"; the shingle triple falsified by a later edit; and this pass's
    "42" quoted runs, which does not reproduce under the method that yields its own numerator. R2
    rewrites more prose than R1 did, in the same durable files. **State the unit beside any count,
    state the method beside any measurement, and re-measure after the last edit rather than while
    making it** — and prefer the durable file's own solution here, which was to state the population
    qualitatively and let the named counterexamples carry the argument.
16. **The build plan's `D17` row is wrong and R2 will read it.** It says "`_validate_meta` does not
    exist as a symbol"; `django_strawberry_framework/types/base.py::_validate_meta` exists and is
    called from the `__init_subclass__` path. The row's *other* content is right — the gates are
    `::_meta_optimizer_hints` and `::_validate_optimizer_hints`, and they reject more than the spec's
    two rules. The plan is Worker 0's file and I did not edit it; the Low above fixes the durable
    copy of the error, and this note is so the row itself gets corrected before R2's dispatch quotes
    it. The sentence it governs (spec `:86`) is the **sole carrier of the `configurationerror`
    anchor**, so this is the anchor-bearing rewrite with the least margin for a wrong premise.
17. **A small factual imprecision in the rationale, offered as an R2 touch-up rather than a finding.**
    The `### B1` entry `:200`-`:201` calls it "the locked `strawberry-graphql 0.316.0`". `0.316.0` is
    the **declared floor** (`pyproject.toml` #"strawberry-graphql>=0.316.0"); `uv.lock` resolves
    **0.323.2**. The substantive claim is correct at both versions — I confirmed the single
    per-request `Schema.get_extensions` accessor and the `__init__` deprecation path in the installed
    0.323.2, and `docs/GLOSSARY.md` independently records that the `_sync_extensions` cache was a
    pre-0.316.0 shape. Only the word "locked" is loose. No reader acts wrongly on it, which is why it
    is a note and not a Low.
18. **Do not "fix" the two candidates the apply-changes pass opened and left, and do not re-derive
    them.** `## How to read this file` `:37`-`:38` ("headings that no longer exist in the spec at
    all") and the entry's `:106` ("The `**The win.**` label no longer appears in the spec") are both
    **true as written** — I tested them independently this spawn. The single `grep 'The win\.'` hit at
    spec `:3` is a mention inside a code span naming the class that moved, not a paragraph label.

### Review outcome

`revision-needed`.

One Medium and one Low, neither addressed nor rejected, and `worker-3.md`'s acceptance gate requires
every High, Medium, and Low finding to be addressed or intentionally rejected with a recorded reason.
Both are corrections inside the rationale; no spec edit is owed by either, and the spec must stay
byte-identical.

**Everything the prompt sent me to grade came back clean, and the two graded judgements are both
right.** Low 1 was fixed at the label definition rather than on the bullet, and the argument for that
site holds: the bullet is wrong only under an absolute definition, so the definition is the defect,
and one edit closes two of the three further sites where three qualifiers would have been needed. The
tie-break rule it installs is sound, because it is paired with a change to what the index *asserts*
rather than being a disclaimer bolted onto an unchanged absolute — and it is correctly scoped to a
sentence-level disagreement. Low 2 was re-keyed rather than refreshed, to inputs R2 cannot move, and
**all four figures reproduced exactly on a first independent implementation of the file's own stated
method** — 192 of 4,934, 41 runs, longest 27 words, median 3 — which is the method's first test by a
reader who did not write it and is the strongest evidence in this cycle that a disclosed measurement
is worth more than a correct one. `grep -c "LINK DEFINITIONS"` returns 1, so the self-falsifying draft
is really gone. The seven verbatim counterexamples reproduce character for character; only the
denominator beside them does not, and that figure lives nowhere but this artifact. The pass's
correction of my own pass-3 grep is right and I was wrong.

**What holds the item open is a class the ruling already decided and the implementation did not carry
across.** Three `**Claims the spec no longer makes**` blocks — `### B4`, `### B7`, `### B8` — retract
claims the spec still makes, at sites the same file's `## Standing notes` enumerates as live; two
further blocks are the same shape more weakly. That is verbatim the defect the maintainer decision was
issued to remove, and both integration sweeps that opened those blocks tested them only for
competitor-comparison material, which is why it survived three passes. Separately, the durable R2
worklist tells R2 that `_validate_meta` does not exist, and it does. Neither is the fault of the two
edits under review; both are in the file those edits are correcting, and both are one decision away
from closed.

Per the build plan's `### Deviation 2` corollary this routes to **Worker 1**, not Worker 2. Worker 1
applies the corrections, sets `Status: planned` again, and returns the artifact here.

### Working-tree churn observed during this review — reported, not reverted

**None.** `git status --short` was the same four entries at the start and at the end of the pass:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
```

`HEAD` is **`346d67312599c0536980969caa39085ab3885ae8`**, re-derived this spawn, and it did not sweep
this cycle's work: `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns
**`20a9752f`** and the three artifacts are still untracked. That is the standing hazard check, done
with `git log` rather than `git status` alone. No stray untracked file appeared, and nothing was
reverted. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, and
`examples/fakeshop/db.sqlite3` are all clean.

---

## Build report (Worker 1, apply-changes pass 4)

Per the build plan's `### Deviation 2` corollary, an R1 `revision-needed` routes to Worker 1: the
same two rules that make Worker 1 the only role that may perform the move make it the only role
that may fix it. `Status:` is `planned` on return, which Worker 0 reads as "dispatch Worker 3" for
a pass-5 review. Every prior entry — all four of Worker 3's review sections included — is
untouched.

**One Medium and one Low, both fixed; nothing rejected.** The spec was **not** reopened: every fix
is inside `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`, and the spec is
byte-identical to the file Worker 3 read at passes 2, 3, and 4 (216 lines / 26,480 bytes,
`git diff --stat` still 28 insertions / 171 deletions). Worker 3's 18-item `### Notes for Worker 1
(spec reconciliation)` was read and is R2's; nothing in it was acted on, item 9's settled
maintainer ruling included, and items 16-18 are routed onward below rather than enacted.

### The Medium — the class exists because one word was dropped, and the label is where it was dropped

**The finding reproduces at all three cited addresses**, verified by grep against the spec rather
than by reading:

- `### B7`'s "That the walker reads a `_optimizer_field_map` class attribute" — spec `:129`
  ("Stash it as `cls._optimizer_field_map`. The walker reads `target_type._optimizer_field_map`"),
  `:131` ("read `_optimizer_field_map`"), `:135` ("Assert `_optimizer_field_map` is populated").
- `### B4`'s "That hints are read off a `_optimizer_hints` class attribute" — spec `:84` ("To read
  `_optimizer_hints`, it must look up the type class via `registry.get(model)`").
- `### B8`'s "That not mutating the cached plan is a discipline the builder must maintain by hand"
  — spec `:149` (`**Cache-safety: do not mutate the cached plan.**` … "B8 must not modify … in
  place … Instead, build a new plan (or a shallow copy)").

**Why the class exists, and it is not "R1 ran before R2" in the loose sense — it is one missing
word.** The block's label is the *only* place in the whole corpus that states this obligation
without the word **may**:

- `BUILD.md` `## Spec rationale extraction`: "any claim the decision once made and **may** no
  longer make".
- This file's own opening paragraph: "every claim the spec once made and **may** no longer make".
- The spec's own companion-pointer paragraph at `:3`: the same sentence, the same word.
- This file's own entry bodies already use the modal form twice in italic leads (`### B1`'s "The
  claim the decision **may** no longer make — the recommendation is now inverted"; the ordering
  entry's "The claim the section **may** no longer make").

Dropping **may** turns a statement of *entitlement* into a statement of *fact about the current
spec* — and R1 cannot make that statement, because R1 moved the deliberation out and deliberately
did not reconcile the spec against the package. A pass that only removes text can only retract what
it removed. So the list is a **worklist** (what the decision is no longer entitled to claim) that
was labelled as a **receipt** (what the spec has stopped claiming); wherever the surviving prose
independently carries a listed claim, the two diverge. Every divergence found is a drift-table row
— `D14`, `D16`, `D18`, `D22`, `D26`, `D1` — i.e. exactly the material R2 owns, which is why the
label told R2 its own work was done.

**The fix, one decision applied once.** Restore the corpus word in the label, and define the block
where the file defines its other labels. Concretely:

1. **`## How to read this file` gains the block's missing definition** — that it is a worklist and
   not a receipt; that a claim is listed because the decision is no longer entitled to it (its text
   was cut, or the package falsified it, or both); that several listed claims are still stated in
   the spec's surviving prose and every one of those is the reconciliation item's to retract; and
   where the reader meets them (the blocks themselves, with `## Standing notes` carrying the ones a
   sweep meets first). This is the site the finding's option (a) names, and the same site pass 3
   chose for the `**Cut**` label, for the same reason: a per-entry qualifier would have to be
   written at every address the class has, including the ones added later.
2. **The label reads `**Claims the spec may no longer make.**`** at each of the ten class-default
   blocks. This is the load-bearing half: it is what a reader of a single entry sees, and the tie-
   break rule below makes the entry the thing a reader lands on.

**Every item in every block was then re-tested against the spec under the restored label.** The
question asked was the general one the finding says was never asked — "does the spec still make
this claim?" — followed by "is the decision still entitled to it?". Per block, the items whose
claim the spec's **surviving prose** still carries, in whole or in part:

| Block | Items the spec still carries | Under the restored label |
|---|---|---|
| `**The win.**` (the ruling's) | none — both are absent from the spec (`grep -ci 'None of the existing libraries\|DRF\|smoke alarm\|per-field decorator'` → 0) | left byte-unchanged; see below |
| `## Problem statement` | none — spec `:9` points the sequence at this file | accurate |
| `### B1` | none of the five | accurate |
| `### B2` | none — spec `:41` explicitly rejects the bare-field-name key | accurate |
| `### B3` | "the lazy-load probe has exactly two arms" — spec `:55` names two and only two | accurate: `D14`'s third arm (`kind == "connection_to_attr"`, verified at HEAD) is what the decision is no longer entitled to exclude |
| `### B4` | "hints are read off a `_optimizer_hints` class attribute" — spec `:84` | accurate: `D16`, and the class-attribute form has **zero** occurrences package-wide |
| `### B5` | "B5 must land before its dependents" — spec `:49` and `:67`; and "the optimizer stashes one key on the context" — spec `:98` | the second is accurate (`D18`; `optimizer/_context.py` owns five keys, verified). **The first is not, under either label — rewritten, see below** |
| `### B6` | none of the three | accurate |
| `### B7` | "the walker reads a `_optimizer_field_map` class attribute" — spec `:129`, `:131`, `:135` | accurate: `D22` |
| `### B8` | "not mutating the cached plan is a discipline the builder must maintain by hand" — spec `:149` | accurate: `D26`; `OptimizationPlan.finalize` / `_assert_under_construction` enforce it structurally at HEAD |
| the former `## Priority and ordering` | partially: `:9` names a recommended build sequence as existing (in this file), and `## Proposed improvements`' framing (`D1`) still reads as work ahead of implementation | accurate — the spec may no longer state a sequence, and may no longer frame shipped work as proposed |

Item counts are deliberately not given: the items are sentences whose own text contains periods
(`_meta.get_fields()`), so a mechanical count depends on the splitting rule — the hazard Worker 3's
handoff item 15 names. The sites are listed instead; count them against the file.

**The one member the relabel does not repair, and why it needed its own clause.** `### B5`'s "That
B5 must land before its dependents" is false under **both** labels. What the entry cut was the
*recommendation* ("B5 should land first so the context-stash pattern is proven before…"); what the
spec kept is the *dependency* — `:49` "implemented after O5+O6+B5" and `:67` "B5 (context stashing
mechanism)" — and the `## Problem statement` entry states in this same file that the
`**Depends on.**` paragraphs are contract and stayed on purpose. Left as written, the restored
label would have made it worse, not better: it would invite R2 to strip a dependency the pass
deliberately preserved. It now retracts the recommendation and names the dependency as contract, in
one clause.

**Compatibility with the maintainer's ruling — checked, not assumed**, because Worker 3's note says
option (a) is a reading the ruling resolved the other way for the `**The win.**` block.

- **The ruling's premise survives intact.** Its stated defect was that the block asserted the spec
  no longer claims the per-request re-walk and the needless id-only-FK JOIN, "claims the surviving
  `## Problem statement` demonstrably still makes". Under the restored label those two items would
  still have been defects, and worse ones: the ruling **decided the sentence stays**, so listing
  them on a worklist of things the spec may no longer say would have asked R2 to undo a settled
  ruling. The ruling's fix — remove them from the list, record the survival positively, scope the
  title — is the right fix under either reading. Nothing in it is re-argued or re-litigated here.
- **That block was therefore left byte-unchanged.** Its label is the maintainer's text; it is
  already scoped by its own clause; and it is **true as written** — both of its remaining items are
  absent from the spec, measured above. "No longer makes" is a stronger true statement than "may no
  longer make", not a competing one, so no reader is misled by the two spellings. The new
  definition closes the gap with one general sentence — *a block whose label says more than that has
  been checked against the spec sentence by sentence and scopes the stronger claim in its own words*
  — rather than with a special case naming that block, which would be a tally for a later pass to
  keep in step.

**The tie-break rule, revisited as the prompt invites.** Pass 3 added "**Where the index and an
item's own entry disagree about a sentence, the entry is the accurate one.**" Worker 3 produced a
concrete case where it routes a reader wrong, and it does — but the rule's defect is *scope*, not
direction. It was written to settle **provenance** (did this text move, or is it gone?), where the
entry is genuinely the better source; the finding's case is a different question (**does the spec
still say this?**), where neither the index nor an entry is an authority. The rule now says so: it
is scoped to "where a piece of text went", and the sentence after it states that whether the spec
still *makes* a claim is settled by the spec itself. The rule is narrowed rather than reversed,
because reversing it would break the case pass 3 fixed it for.

### The Low — `_validate_meta` exists, and the correction says what is actually true

**Verified at source rather than reasoned about**, and it reproduces exactly:
`django_strawberry_framework/types/base.py::_validate_meta` is a live function called from the type
metaclass path (`base.py #"validated = _validate_meta(cls, meta)"`, line 535). It normalizes the
hints mapping through `::_meta_optimizer_hints`; the two rejections the spec's `**Validation.**`
sentence attributes to it — unknown hint field names and non-`OptimizerHint` values — live in
`::_validate_optimizer_hints`, called on the **next line** (537) from the same `__init_subclass__`,
whose docstring also records that it rejects an excluded field and a selected scalar field, which
the spec does not state.

The `## Standing notes` bullet now says that, names both symbols, and keeps the two facts a
rewriter needs: the shipped gates reject more than the spec's two rules, and the sentence is the
sole carrier of the `configurationerror` anchor. It also states the consequence the finding gives
as its reason for filing — a rewrite starting from "the symbol is a phantom" produces a different
and wrong correction.

**The build plan's `D17` row carries the same error and was not touched.** The plan is Worker 0's
file. It is routed under `### Notes for Worker 3 (pass 5)` and repeated in the R2 handoff below,
per Worker 3's own note 16.

### The integration sweep — four candidates opened, none edited, recorded so pass 5 does not re-derive them

The prompt makes the integration mine. Each was resolved against the files, not against intuition.

1. **A `## Standing notes` bullet for the three surviving claims the list does not name** —
   `### B8`'s cache-safety instruction (spec `:149`), `### B3`'s two-arm probe (`:55`), `### B5`'s
   single context key (`:98`). **Deliberately not added.** The section's own opener scopes it ("The
   ones a sweep will notice first"), so no completeness claim is broken; all three are drift-table
   rows (`D26`, `D14`, `D18`), so R2 has them from the plan; and under the restored label each
   block is now its own in-situ worklist entry, so a second list of the same set would be the
   pass-2 duplicate-tally defect. This is the distinction the pass-2 fix turned on and it is the
   opposite reading from that case: there, Worker 3 established the drift table carried **no** row
   for `### B8`'s opening paragraph, so the rationale was the whole record and a bullet was owed.
2. **`## Provenance of this record`'s five labels.** None makes any assertion about the
   retracted-claims blocks — they file items by where the text went. Untouched, and its `**Moved**`
   bullet's measurement is unaffected (re-measured below).
3. **`## Standing notes` `### The status claims were left standing`'s opener** ("This pass cut the
   *deliberative* layer: competitive argument, proposal code, build order…"). Describes which
   classes the pass acted on, not what the spec now contains — the distinction the maintainer pass
   drew for the same sentence and the reason it was left then. Left again, for the same reason.
4. **The file's opening paragraph and the spec's `:3` companion pointer.** Both already say "may no
   longer make". They were *right* and the label was wrong, which is the evidence the label is the
   defect. Neither needed an edit — and the spec's is not writable this pass in any case.

### Files touched

- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — 4 edits: the scoped tie-break
  sentence plus the new label definition in `## How to read this file` (one replacement); the label
  itself at the ten class-default blocks (one mechanical replacement); `### B5`'s first item; and
  the `_validate_meta` bullet in `## Standing notes`. 786 -> 806 lines, 55,918 -> 57,790 bytes
  (+1,872).
- `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` — **not touched this pass.** Neither finding owed
  a spec edit and the scope forbids a discretionary one.
- `docs/builder/bld-004-r1-rationale_move.md` — this section appended; `Status:` set to `planned`.

**No unasked-for edit was made, and none was forced.** No count anywhere in the file changed, so
nothing elsewhere had to be kept in step — the fix restored a word and added a definition rather
than restating any set. `## Provenance of this record`, the `**Cut**` / `**Moved**` / `**Deleted**`
/ `**Restated in the spec, not moved**` / `**Deliberately left in the spec by this pass**` bullets,
and every other `## Standing notes` entry are byte-unchanged.

### Validation run — every result quoted verbatim

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
  -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**.
  Character-identical to the build plan's pre-flight baseline.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md docs/builder/bld-004-r1-rationale_move.md`
  -> **exit 0** on all three files.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have
  glossary links.` **exit 0**. **Read-only form only**; the writing form was never invoked.
- **Every link definition re-resolved on disk this spawn, not quoted.** Each target resolved from
  its own source file's directory and existence-tested: spec **11 definitions / 11 distinct uses**,
  rationale **19 / 19**, **0 undefined references, 0 unused definitions, 0 of 30 targets missing.**
  The new definition bullet reuses `[build]`, already defined and already used, so both counts are
  unchanged. **R2 and R3 re-run this rather than quoting it.**
- **Per-anchor 10-anchor constraint, re-derived.** `grep -o "\[glossary-<anchor>\]" | wc -l` -> **2
  for every one of the ten** (1 body use + 1 definition): `configurationerror`,
  `djangooptimizerextension`, `djangotype`, `fk-id-elision`, `metaexclude`, `metafields`,
  `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `queryset-diffing`. The spec was not
  edited this pass, so this is a confirmation. **The terms CSV was not opened**:
  `git status --short docs/SPECS/appx/` shows only the rationale, as `??`.
- **Byte / line count.**

| | lines | bytes |
|---|---|---|
| spec at Worker 3's pass-4 review | 216 | 26,480 |
| spec **now** | **216** | **26,480** (unchanged — not touched) |
| spec at HEAD (pre-move) | 359 | 33,928 |
| net move + revisions | **-143** | **-7,448 (-21.9%)** |
| rationale before this pass | 786 | 55,918 |
| rationale **now** | **806** | **57,790** (+1,872 over four edits) |

- `git diff --stat -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **28 insertions / 171
  deletions**, the hunk shape Worker 3 recorded at all four reviews — independent evidence the spec
  is byte-identical to the file pass 4 read. `git show HEAD:<spec> | wc -l -c` -> **359 / 33,928**,
  so the baseline the move was measured against has not moved.
- **Label spellings, enumerated rather than asserted.** `grep -o '^\*\*Claims the spec[^.]*\.\*\*'`
  -> **10** `**Claims the spec may no longer make.**` and **1** `**Claims the spec no longer makes
  as any slice's own argument.**` (the ruling's, unchanged). Eleven blocks, as before.
- In-page anchors: the repo's own `scripts/check_spec_glossary.py::github_anchor` over the spec's
  **15** headings -> **15 unique slugs, 0 duplicates**; `#problem-statement` and
  `#proposed-improvements` both resolve. **No new in-page anchor was added** — the new bullet's
  cross-references to `## Provenance of this record` and `## Standing notes` are named textual
  pointers, as this file's other intra-file pointers are.
- `grep -c '^```'` -> spec **0**, rationale **0**. No fence introduced.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files -> **no match** (exit 1). Rule 27 holds;
  the two symbol names the Low fix adds are bare backticked names, matching this file's style (it
  carries no `::` paths).
- `grep -nP '\]\((?!#|https?:)'` over both files -> **no match** (exit 1). Reference-style
  preserved.
- `grep -niE 'as of (review )?round|amendment|retract|inverted|a later strawberry'` over the spec ->
  **no match** (exit 1). The pass-1 Low-3 fix still holds; the word "retract" enters the rationale
  only, in the new definition.
- `grep -c "LINK DEFINITIONS"` over the rationale -> **1**. The pass-3 method clause still does not
  embed the marker it tells the reader to split on.
- `git diff --stat -- django_strawberry_framework/ tests/ examples/` -> **empty**. No source, test,
  or example file touched; no `pytest`, no `ruff` (no `.py` file changed), no coverage-shaped flag
  in any form.
- No `git stash`, `checkout`, `restore`, `worktree`, `commit`, or branch operation at any point. The
  read-only HEAD reference was `git show HEAD:docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` piped
  in-process.

### Duplication introduced by this pass: zero — and the durable measurement did not move

Measured under the normalization the file itself now states (drop each file's bottom
link-definition block, fold every non-alphanumeric run to whitespace, lowercase, distinct 8-word
shingles), by reconstructing the pre-pass rationale from this pass's own four edits — **the
reconstruction reproduces 55,918 bytes / 786 lines exactly, which is what validates it as the
baseline**:

| measure | before this pass | after |
|---|---|---|
| rationale total shingles | 8,775 | 9,085 (+310) |
| left-the-spec shingles present in the rationale | 161 | **161 (unchanged)** |
| rationale x post-move-spec overlap | 52 | **52 (unchanged)** |
| overlap shingles this pass added | — | **0** |

**The `**Moved**` bullet's own figure was re-measured after the last edit rather than assumed, and
it is unchanged: 192 of the pre-move spec's 4,934 shingles, in 41 contiguous runs, longest 20
shingles (27 words), median 3.** That is the property pass 3 re-keyed it for — both its inputs are
frozen, so four edits to this file moved nothing — and this is its first test by a pass that edited
the file after it was written. It needs no refresh and none was made.

### Notes for Worker 3 (pass 5)

- **The judgement to audit is the diagnosis, not the wording.** The claim is that the class had one
  cause — a missing modal in the label — and the check is cheap: confirm that `BUILD.md`
  `## Spec rationale extraction`, this file's opening paragraph, spec `:3`, and this file's own two
  italic entry leads all carry "may no longer make", and that the label was the only place in the
  corpus that did not. If that holds, the fix is at the cause; if it does not, the fix is a
  euphemism and should be called one.
- **The place to look for an over-correction is the restored label's other direction.** "May no
  longer make" asks R2 to retract; a listed claim that must **stay** would now be an instruction to
  break the spec. I found exactly one (`### B5`'s ordering item, whose dependency form is contract)
  and rewrote it. The test to re-run is the one in the table above, in the other direction: for each
  item, ask whether the spec is still *entitled* to the claim.
- **The maintainer-ruling compatibility argument is the second thing to grade**, and Worker 3's
  pass-4 note is right to flag it. The claim is that the ruling's premise holds unchanged under the
  restored label and that its block needed no edit because it is true as written. Both halves are
  checkable: re-read the ruling's stated defect, and grep the spec for its two remaining items.
- **The tie-break was narrowed, not reversed.** Confirm the narrowed rule still covers the pass-3
  case it was written for (`**Cut**` versus the entry, on where text went) while no longer covering
  the case it mis-routed.
- **Two claims worth re-deriving rather than reading:** the zero-new-overlap table (reconstruct the
  pre-pass file from the four edits; it must land on 55,918 bytes / 786 lines) and the 192 / 4,934 /
  41-run measurement, which this pass re-ran and which must still reproduce.
- **Three items routed onward, not enacted**, all Worker 3's pass-4 notes 16-18: the build plan's
  `D17` row is wrong and is Worker 0's file; the `### B1` entry's "locked `strawberry-graphql
  0.316.0`" is the declared floor rather than the lock, offered as an R2 touch-up; and the two
  candidates the pass-3 sweep opened and left are true as written and must not be "fixed".
- The consolidated R2 handoff is Worker 3's own 18-item list in `## Review (Worker 3, pass 4)`, with
  its items 10, 11, and 16 amended by this pass: item 10's two findings are closed; item 11's
  warning that `### B7`'s and `### B4`'s lists "say this retraction is already made" no longer
  applies, because the label now says the opposite; item 16's `D17` correction now exists in the
  durable file and is still owed in the plan. Nothing from this pass was staged for later without
  being written down. No temp test, no shadow file, no `docs/builder/temp-tests/` directory.

**Failability proofs.** None; this pass introduced no new boundary. `git diff --
django_strawberry_framework/` is empty, so there is no boundary, guard, gate, or rejection path to
prove.

**Hot-path budget.** Not applicable; the plan declares `none`, and correctly — nothing in this diff
runs per request, per resolver, per row, per connection, or per outbound message.

**Floor verification.** Not applicable; the plan declares floor-verification scope `none`, and
correctly — the diff touches no Django / Strawberry / channels integration seam.

**Coverage.** No `pytest` run, no `--cov*` flag in any form, at any point in this pass.

### Spec changes made (Worker 1 only)

**None.** The spec was not edited this pass. `git diff --stat` on it is unchanged at 28 insertions /
171 deletions and its byte count is identical to Worker 3's pass-2, pass-3, and pass-4 readings (216
lines / 26,480 bytes), so the three pass-1 revision edits remain the whole of this cycle's spec
delta.

**Spec status-line re-verification** (`worker-1.md` `## Spec status-line re-verification`, re-run
this spawn as every Worker 1 spawn must): spec-004 carries **no** `Status:` / owner / target-release
/ predecessor header block — lines 1-5 are the title, the companion-pointer paragraph, and
`## Problem statement`. Nothing in them is a status line this build has falsified, so no header edit
was owed. The `:3` companion paragraph's "every claim the spec once made and may no longer make"
was re-read this pass as part of the Medium and is accurate as it stands; it is a pointer, not a
status line, and needed no change.

### Working-tree churn observed during this pass — reported, not reverted

**None.** `git status --short` was the same four entries at the start and at the end of the pass,
for the fifth consecutive pass:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
```

`HEAD` is **`346d67312599c0536980969caa39085ab3885ae8`**, re-derived this spawn rather than quoted,
and it did **not** sweep this cycle's work: `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-
0_0_3.md` still returns **`20a9752f`**, and the rationale, this artifact, and the build plan are
all still untracked. That is the standing hazard check, done with `git log` rather than
`git status` alone. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, and
`examples/fakeshop/db.sqlite3` are all still clean — but pass 5 re-derives that rather than
inheriting this reading, since the concurrent session reversed that state four times earlier in
this cycle.

---

## Review (Worker 3, pass 5)

Read in order, as the prompt directs: `docs/builder/worker-3.md` (full), `AGENTS.md`, `START.md`,
`docs/builder/BUILD.md` (full), `docs/builder/ARTIFACT.md`, `docs/README.md`,
`examples/fakeshop/test_query/README.md`, `docs/builder/build-004-optimizer_beyond-0_0_3.md`
including its settled `## Maintainer decision — the surviving competitive positioning in
`## Problem statement`` and its **corrected `D17` row**, this artifact end to end in the prescribed
order (plan, move report, `## Review (Worker 3)`, apply-changes, `## Review (Worker 3, pass 2)`,
apply-changes 2, maintainer-decision pass, `## Review (Worker 3, pass 3)`, apply-changes 3,
`## Review (Worker 3, pass 4)`, apply-changes 4), the spec, the rationale, and the pristine HEAD
spec obtained read-only as `git show HEAD:docs/SPECS/spec-004-optimizer_beyond-0_0_3.md >
<scratchpad outside the repo>/spec-004-HEAD.md`. No `git stash` / `checkout` / `restore` /
`worktree` at any point, and no prior entry was edited.

`HEAD` re-derived this spawn rather than quoted: **`346d67312599c0536980969caa39085ab3885ae8`**; the
HEAD spec blob is **33,928 bytes / 359 lines**. `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-
0_0_3.md` still returns **`20a9752f`** and the three artifacts are still untracked, so no concurrent
commit has swept this cycle's work. `git status --short` is the same four cycle paths and nothing
else.

**Nothing below is quoted from any build report.** Every figure was re-derived from the files on
disk this spawn.

### High:

None.

### Medium:

None.

### Low:

#### The `**The win.**` entry's survival criterion is false at the source: three of the eight paragraphs name no competitor, not one

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:148
- **B8's, whole.** It is the only one of the eight that names no competitor. It describes the
  package's own pre-B8 behaviour and why the duplicate matters, which is the slice's problem
  statement rather than positioning.
```

The same claim is made a second time, as the entry's framing sentence:

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:122
*Cut — one paragraph per slice, eight in all.* Each opened its slice by naming what
`strawberry-graphql-django` does and why this package would do better: …
```

**Measured against the read-only HEAD copy, not read.** The eight `**The win.**` paragraphs are at
HEAD `:17`, `:50`, `:82`, `:115`, `:158`, `:181`, `:239`, `:271`. Grepping each line for a
competitor token (`strawberry-graphql-django`, `existing libraries`, `django-debug-toolbar`, `DRF`):

| HEAD line | slice | competitor named |
|---|---|---|
| `:17` | B1 | `strawberry-graphql-django` |
| `:50` | B2 | `strawberry-graphql-django` |
| `:82` | B3 | `strawberry-graphql-django`, `django-debug-toolbar` |
| `:115` | B4 | `strawberry-graphql-django`, `DRF teams` |
| `:158` | **B5** | **none** |
| `:181` | B6 | `existing libraries` |
| `:239` | **B7** | **none** |
| `:271` | **B8** | **none** |

B5's reads "Stash the computed `OptimizationPlan` on `info.context` so consumers can write tests
like … Makes the optimizer's behavior observable instead of magic." B7's reads "The O2 walker
rebuilds `{f.name: f for f in model._meta.get_fields()}` on every walk … The walker reads the cached
map instead of rebuilding it." Both describe **this package's own** behaviour — B7's names `O2`,
which is `spec-002`'s walker — exactly as B8's does. So "the only one of the eight" is wrong by two,
and the framing sentence at `:122` is wrong for the same three.

**Why a reader acts on it.** This is not the summary defect the pass-2 Low closed (that one was a
tally). It is the **criterion** the file offers for why one paragraph was kept and seven were cut —
and `## Standing notes` `### The `**The win.**` cut is the one an over-cut review should test first`
standing-orders a future sweeper at exactly this class and points it at this entry for the
survivals. A sweeper who applies the stated criterion to the eight HEAD paragraphs finds it does not
discriminate, and the wrong action available is a spec edit: restoring B5's or B7's cut paragraph on
the grounds the file itself supplies. That is the one edit this file exists to prevent.

**The disposition is right; only the reason is wrong, and the right reason is already in the entry.**
The test that actually discriminates is the one stated twelve lines above at `:135` — "every factual
claim inside them is restated in the same slice's `**Mechanism.**` paragraph". I applied it to the
three:

- **B7** — spec `:129` `**Mechanism.**` carries "The walker reads `target_type._optimizer_field_map`
  instead of calling `model._meta.get_fields()`", which is the win paragraph's whole factual content.
  Restated; correctly cut.
- **B5** — spec `:96` `**Mechanism.**` carries the stash and "Consumers and test code access it
  directly", and the observability motive survives at document level in `## Problem statement` `:7`,
  which the maintainer ruling identifies as the surviving B5 comparison. Correctly cut.
- **B8** — spec `:143` `**Mechanism.**` opens "Before applying the plan in `_optimize`, inspect the
  queryset's existing optimization state" and restates **nothing** of the problem. Cutting `:141`
  would have left the slice with no statement of what it fixes. Correctly kept.

So the file reached the right three dispositions on the right test and then wrote down a different,
false one.

**Recommended change.** One clause, and **no tally** — the constraint the pass-2 fix established
holds. Replace the criterion with the discriminating one, disposing of B5 and B7 inside it rather
than in a second list: e.g. "B8's, whole. It names no competitor — and unlike B5's and B7's, which
also name none, none of its content is restated in the section's own `**Mechanism.**`, so cutting it
would have left the slice with no statement of the problem it solves." The framing sentence at
`:122` needs the same softening ("most opened…", or "each opened its slice by naming the behaviour
the slice improves on — upstream's for five of the eight, this package's own for B5, B7 and B8"),
since it introduces a quotation list that includes all three.

**Test expectation.** None; no behaviour changes. The verification is the one applied above: grep
each of the eight HEAD `**The win.**` lines for a competitor token, then apply the `:135`
restated-in-`**Mechanism.**` test to the three that carry none.

### The five graded items — each re-derived, not confirmed

**1. The Medium's root cause: the modal. The fix is at the cause; the stated universal that supports
it is not true.**

The four positive sites all check out, verbatim: `BUILD.md` `## Spec rationale extraction` (line 98)
— "any claim the decision once made and **may** no longer make"; this file's opening paragraph
(`:7`-`:8`) — "every claim the spec once made and may no longer make"; the spec's `:3` companion
pointer — the same sentence, the same word; and this file's two italic entry leads (`:213` "The
claim the decision **may** no longer make", `:646` "The claim the section **may** no longer make").

**The universal does not reproduce.** `BUILD.md` `## Claims are proven mechanically` says to
re-derive a stated count rather than accept it, and this one is a stated count of one. Sweeping the
repository's `.md` corpus for the block label in its non-modal form
(`grep -coE '^\*{1,2}Claims? the spec no longer makes'`):

| file | non-modal labels | modal labels |
|---|---|---|
| `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` | **17** | 0 |
| `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` | **8** | 0 |
| `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` | **22** | 0 |

Plus one site of the *other* shape the pass cites as carrying the modal:
`docs/SPECS/spec-002-optimizer-0_0_2.md:8`, spec-002's own companion-pointer paragraph — the direct
analogue of spec-004's `:3` — reads "every claim it once made **and no longer makes**". So the label
is not the only site that drops the modal; it is the **fourth** file to drop it, and the form it
dropped it in is the house form of all three sibling rationales.

**Graded: the fix is still at the cause, and it is not a euphemism.** The pass set that test itself
("if it does not [hold], the fix is a euphemism and should be called one"), so it is worth answering
directly rather than by the universal's failure. A euphemism would soften the wording while leaving
what the file asserts unchanged. This does not: the load-bearing half of the fix is the **new
definition** at `:30`-`:41`, which positively states the thing the old label denied — "Several
listed claims are still stated in the spec's surviving prose, and every one of those is the
reconciliation item's to retract rather than a retraction already made" — and re-routes the reader
to `## Standing notes`. That is the same shape pass 4 graded as sound for the `**Cut**`
redefinition: a precedence/scope rule is sound when paired with a change to what the index
*asserts*, and a disclaimer when it is not. Here it is paired.

**What the corrected causal account is, because it matters to R2 and to the next cycle.** The label
was not a one-off slip; it is inherited house form from three sibling rationales, and in *those*
files it is defensible — each of spec-001, spec-002 and spec-003 ran an R2 spec-reconciliation pass
(`docs/builder/bld-003-r2-spec_reconciliation.md` is that cycle's artifact), so by the time their
labels were finalized the retractions had in fact been performed. Spec-004's R1 has no R2 yet, which
is precisely the pass's own argument. The consequence is durable and belongs on the R2 list: this
file now diverges from all three siblings on that label, deliberately, and a future harmonizing
sweep must not "fix" it back. Recorded as handoff item 19.

**2. The sixth member, and my own independent walk of all eleven blocks.**

`### B5`'s ordering item reproduces as described. I did not confirm the pass's table; I took each
item in each of the eleven blocks and asked the two questions in order — does the spec's surviving
prose still carry the claim, and is the decision still entitled to it.

Items the spec still carries, verified by grep against the spec: `### B3` `:400`'s two-arm probe
(spec `:55` names two; `D14`'s third arm ships); `### B4` `:455`'s `_optimizer_hints` class
attribute (spec `:84`); `### B5` `:495`'s single context key (spec `:98`); `### B7` `:576`'s
`_optimizer_field_map` class attribute (spec `:129`, `:131`, `:135`); `### B8` `:613`'s
maintain-by-hand discipline (spec `:149`). Each is a live drift row and each is accurate under the
restored modal.

Items the spec no longer carries, verified by absence: B1's five (`_sync_extensions` /
`_async_extensions` / `get_extensions` / `extensions=[` / `bare class` → **0 hits**); B2's two (the
only `field_name`-keyed occurrence in the spec is `:41`, where the spec **rejects** it); B3's
`build_dotted_path` / `planned_relation_paths` / dotted path → **0**; B6's `_collect_reachable_types`
→ **0**; B7's `_meta.get_fields()`-never claim; the ordering block's four; `## Problem statement`'s
one (spec `:9` now points the sequence at this file).

**The other-direction test, which is the one that matters under a restored "may".** For each item I
asked whether a listed claim must **stay**. Two came close and both are protected:

- `### B5`'s ordering item — the case the pass found and rewrote. It reproduces: the *recommendation*
  was cut, the *dependency* stayed as contract at spec `:49` ("implemented after O5+O6+B5") and
  `:67` ("**Depends on.** … B5 (context stashing mechanism)"). The rewritten item now retracts the
  recommendation and names the dependency as contract in the same clause, so the restored label
  cannot invite R2 to strip it. Correct, and it is a real find: under the restored label the
  un-rewritten item would have been an instruction to break the spec.
- `### B8`'s maintain-by-hand item — the same hazard, already protected before this pass: the
  entry's own body four lines above states "The **requirement** stayed in the spec, because a
  requirement whose enforcement lives in another document is still this document's requirement."
  Only the by-hand *characterisation* is retracted. No edit owed; recorded so pass 6 does not
  re-derive it.

**3. Maintainer-ruling compatibility — the block, and the two greps.**

The block is intact. I cannot run a byte-diff of a file with no prior version on disk, and I do not
claim one: what I ran is a fragment-exact comparison against every string `## Review (Worker 3, pass
3)` quoted from it when the ruling landed, whitespace-folded and matched as exact substrings. All
reproduce — the retitle "**Claims the spec no longer makes as any slice's own argument.**", the
"The B1, B2, and B5 comparisons — … survive in one compressed sentence in [`## Problem
statement`][spec-004-problem], and that survival is deliberate, not a missed sweep" clause, the
kept-whole-rather-than-name-stripped reason, and edit 2's "the 'But strawberry-graphql-django
stopped there' sentence included, kept deliberately over the eight-paragraph cut (see the
`**The win.**` entry above)". The label enumeration is independent corroboration:
`grep -o '^\*\*Claims the spec[^.]*\.\*\*'` returns **10** `**Claims the spec may no longer make.**`
and **1** `**Claims the spec no longer makes as any slice's own argument.**` — eleven blocks, and
the ruling's is the one untouched by the mechanical replacement.

**The two greps return zero.** `grep -cE 'None of the existing libraries|smoke (alarm|detector)|
per-field decorator|DRF|opt-out|schema audit'` over the whole post-move spec → **0**. Both remaining
items of that block are absent from the spec, so "no longer makes" is a true statement there and the
stronger spelling is not a competing claim. Leaving it byte-unchanged is right, and the general
sentence the new definition closes with — "A block whose label says more than that has been checked
against the spec sentence by sentence and scopes the stronger claim in its own words" — covers it
without a special case naming it, which would have been a fourth tally.

**4. The tie-break was narrowed, and the narrowing closes my pass-4 case.**

The rule now reads: "**Where the index and an item's own entry disagree about where a piece of text
went, the entry is the accurate one** — that tie-break settles provenance and nothing else; whether
the spec still *makes* a claim is settled by the spec itself, and neither the index nor an entry is
an authority on that."

I tested it in both directions rather than assenting.

- **The case I produced is closed by scope, not by disclaimer.** My pass-4 case was that for the
  retracted-claims class the *entry* was the inaccurate one and `## Standing notes` was right, so
  the rule routed a reader to the wrong source. The rule no longer reaches that question at all: it
  is scoped to "where a piece of text went", and the sentence after it names the spec as the
  authority on whether a claim is still made. That is the correct authority — not `## Standing
  notes`, which is itself a derived list, and not the entry. Narrowing to the right question is a
  better fix than the one my finding implied.
- **It still covers the pass-3 case it was written for.** That case was the `**Cut**` bullet versus
  the `**The win.**` entry disagreeing about whether B8's paragraph left the spec — a pure
  provenance question, squarely inside the narrowed scope. Nothing pass 3 fixed is lost.
- **Reversing it would have broken that case**, which is the pass's stated reason for narrowing
  rather than reversing, and it is right.

**5. The Low: `_validate_meta`, and the plan and the rationale now agree.**

Verified at source rather than from either document: `django_strawberry_framework/types/base.py`
defines `_validate_meta` at line 1073 and calls it at line 535
(`base.py #"validated = _validate_meta(cls, meta)"`); `_validate_optimizer_hints` is defined at line
1232 and called at line **537**, from the same `__init_subclass__`, one line after. The two
rejections spec `:86` attributes to `_validate_meta` — unknown hint field names and
non-`OptimizerHint` values — are the sibling's; `_validate_meta` normalizes the hints mapping through
`::_meta_optimizer_hints` (line 1160).

**Worker 0's corrected `D17` row was read and it agrees with the rationale bullet**, point for
point: the symbol exists, the drift is narrower than the row first claimed, the two rejections live
in `::_validate_optimizer_hints` called from the same caller one line later, the mapping-shape gate
is `::_meta_optimizer_hints`, the shipped gates reject more than the spec's two rules, and the
sentence is the **sole carrier of `configurationerror`**. The row also names the extra rejections
concretely (a hint on an excluded field, on a selected scalar field, and under an empty field
selection), which the rationale bullet summarises as "the shipped gates reject more than the spec's
two rules". No contradiction between the two, and R2 can work from either.

One imprecision worth naming and not filing: the bullet's "it only normalizes the hints mapping" is
true of `_validate_meta`'s **hints** handling and false of the function, whose docstring lists eight
validation steps (model, `fields`/`exclude` exclusivity, deferred keys, the typo guard, declaration
shapes, interfaces, `connection`, `relation_shapes`). Read in its sentence — whose subject is the two
hint rejections — the scope is clear, and the plan's `D17` states the same fact without the word
"only". No reader reaches a wrong rewrite from it, so it is a phrasing I would tighten rather than a
defect. Recorded so pass 6 does not re-derive it.

### DRY findings

- **No duplication was introduced against the spec, re-derived under the file's own stated method.**
  Implementing `## Provenance of this record`'s four-line method independently (drop each file's
  bottom link-definition block, fold every non-alphanumeric run to whitespace, lowercase, distinct
  8-word shingles): rationale total **9,085** distinct shingles; **rationale x post-move-spec overlap
  52**; **left-the-spec shingles present in the rationale 161**. Both duplication figures reproduce
  the apply-changes pass's "after" column exactly, across four edits and +1,872 bytes.
- **The `**Moved**` bullet's durable measurement still reproduces after the pass that edited the file
  around it.** From the same method: the pre-move blob carries **4,934** distinct shingles, this file
  reproduces **192** of them, in **41** contiguous runs over the HEAD word stream whose longest is
  **20 shingles = 27 words** and whose median is **3**. Four figures, four exact matches, on a second
  independent implementation by a reader who did not write the method. Re-keying it to two frozen
  inputs was the right call and it is now demonstrated rather than argued: four edits to this file
  moved none of it.
- **Against the sibling rationales: unchanged and still clean.** The 17-shingle ordering-invariant run
  that was pass-1's Low-2 is still gone; the remaining overlap is house form for the file class.
- **One deliberate divergence from that house form, measured and judged correct.** The block label is
  now `**Claims the spec may no longer make.**` here against **47** non-modal labels across the three
  sibling rationales (17 / 8 / 22). This is a divergence in a file class whose consistency pass 1
  recorded as deliberate, so it is worth stating rather than leaving to be discovered: it is the
  right divergence, because the siblings' R2 reconciliation had already run when their labels were
  finalized and spec-004's has not. **No change recommended**; carried to the R2 list as item 19 so a
  harmonizing sweep does not reverse it.
- **Existence challenge: none raised.** The pass adds no abstraction, helper, registry, or
  indirection; it edits prose in one file.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list
are unchanged, and none was authorized to change: the build plan's `## Build-wide context flags`
declares package source, `tests/`, and `examples/` read-only for the whole cycle.
`git diff --stat -- django_strawberry_framework/ tests/ examples/` → **empty**, so there is no
concurrent-session entry to attribute this pass. The package source I read this pass
(`types/base.py`, `optimizer/extension.py`, `optimizer/plans.py`, `optimizer/_context.py`,
`utils/context.py`) was read-only evidence, not a diff.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed clean in `git status --short`.

### Documentation / release sanity

Applies — the diff is entirely docs and one of the two files is an archived spec. Both were read end
to end this spawn.

- **The three baseline checkers, re-run rather than quoted.**
  - `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
    → `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**,
    character-identical to the build plan's pre-flight baseline.
  - `uv run python scripts/check_trailing_commas.py --check` on the spec, the rationale, and this
    artifact → **exit 0** on all three.
  - `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have
    glossary links.` **exit 0**. **Read-only form only**; the writing form was never invoked.
- **All ten anchors are single-carrier**, re-derived per anchor rather than on the checker's exit
  code: `grep -o "\[glossary-<anchor>\]" | wc -l` → **2** for every one of `configurationerror`,
  `djangooptimizerextension`, `djangotype`, `fk-id-elision`, `metaexclude`, `metafields`,
  `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `queryset-diffing`. The spec was not
  edited this pass. **The terms CSV was not opened**: it is absent from `git status --short` and
  still carries a header plus ten rows, one per anchor.
- **Every link definition resolves on disk — re-run this spawn, because the reading expires.** Each
  target resolved from its own source file's directory and existence-tested: spec **11 definitions /
  11 distinct uses**, rationale **19 / 19**, **0 undefined references, 0 unused definitions, 0 of 30
  targets missing.** All ten `../spec-NNN-….md` siblings the rationale links (002, 003, 004, 016,
  018, 029, 032, 033, 035, 047) are present; none points at a file the concurrent renumber moved.
  Both files carry `<!-- LINK DEFINITIONS -->` with all ten canonical group headers in the canonical
  order, and the archived companions correctly file under `<!-- docs/SPECS/ -->`.
- **In-page anchors resolve and the em-dash hazard is still avoided.** The repo's own
  `scripts/check_spec_glossary.py::github_anchor` over the spec's **15** headings → **15 unique
  slugs, 0 duplicates**; `#problem-statement` and `#proposed-improvements` both land on real
  headings. No new in-page anchor was added; the eight slice headings still slug to one hyphen under
  the repo's slugger (`b1-ast-cached-plans`) where GitHub emits two.
- **Structural properties.** Spec **216 lines / 26,480 bytes**, `git diff --stat` **28 insertions /
  171 deletions** — the same hunk shape recorded at all four prior reviews, so the spec is
  byte-identical to what pass 4 read and has now been unchanged for four consecutive passes.
  Rationale **806 lines / 57,790 bytes**. `grep -c '^```'` → **0 / 0**;
  `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` → **no match** (exit 1) in both, so `AGENTS.md` rule 27
  holds; `grep -nP '\]\((?!#|https?:)'` → **no match** (exit 1), so the reference-style convention is
  preserved, not merely unbroken.
- **The spec narrates no history.** `grep -niE 'as of (review )?round|amendment|retract|inverted|a
  later strawberry|no longer|used to |formerly|previously|has since'` returns **one** line, `:3`,
  whose only hits are "the former `## Priority and ordering` section" and "may no longer make" —
  rule-1 pointer vocabulary. The pass-1 Low-3 fix still holds at both sites.
- **The policy/status boundary against `D6` still holds, verified by absence over the whole file.**
  `grep -niE 'lru|evict|bounded|\b256\b|ordereddict|move_to_end|quarter'` returns `:23`
  (`**Cache storage.**`) and `:27` (the pre-existing `lru_cache.cache_info()` mention this cycle
  never touched). No `_MAX_PLAN_CACHE_SIZE`, no `256`, no `OrderedDict`, no `move_to_end`, no batch
  eviction anywhere in the spec.
- **The four restated rules are still exact at HEAD**, re-verified at source rather than inherited:
  `optimizer/extension.py::DjangoOptimizerExtension._build_cache_key` returns a five-tuple whose
  `relevant_vars` is `frozenset((k, _hashable_variable_value(variable_values[k])) for k in
  relevant_var_names if k in variable_values)` — the `(name, value)` pair shape **and** the
  omit-rather-than-default guard, both as spec `:21` now states them;
  `optimizer/_context.py #"DST_OPTIMIZER_PLANNED"` for spec `:53`'s key; the snake-cased field-map
  build in `types/base.py` for spec `:129`; and `check_schema` as a `@staticmethod`, which is why
  spec `:108`'s "classmethod" is still R2's.
- **Pointer discipline is intact.** Eleven `[spec-004-rationale]` occurrences: the companion
  paragraph (`:3`), the re-pointed `## Problem statement` clause (`:9`), eight per-slice pointers
  (`:29`, `:47`, `:63`, `:90`, `:100`, `:121`, `:133`, `:151`), and the definition (`:202`).
  `### B8`'s pointer correctly omits "the competitive argument for this slice", because B8's win
  paragraph stayed.
- **Version strings / card IDs / KANBAN.** The spec carries no version or status header, so nothing
  could drift; the rationale's `DONE-004-0.0.3` and "eleven patch versions ago" match
  `pyproject.toml` and `django_strawberry_framework/__init__.py`, both `0.0.14` (0.0.3 → 0.0.14 is
  eleven). No card moved and this cycle wrote no DB. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`,
  `docs/GLOSSARY.md`, and `examples/fakeshop/db.sqlite3` are **all clean** — re-derived this spawn
  rather than inherited, since the concurrent session reversed that state four times earlier in the
  cycle.
- **No script-rendered doc was regenerated**, so the staging-docstring check has no subject, and no
  obsolete "coming soon" / "planned" wording was introduced.
- **Archival unchanged.** The rationale lives directly at `docs/SPECS/appx/`, the archived-companion
  location `AGENTS.md` rule 26 names.

### What looks solid

- **The Medium's fix is a redefinition, not a relabel, and it survives the pass's own test even
  though the universal supporting it does not.** All ten class-default blocks now carry an accurate
  label, I walked every item in all eleven against the spec, and the new definition at `:30`-`:41`
  states in the durable file the fact the old label denied. The pass's own note invited exactly this
  audit and named the right thing to check.
- **`### B5` is a genuine find, and it is the kind a relabel-only pass would have shipped broken.**
  Under a restored "may", an item retracting "B5 must land before its dependents" would have invited
  R2 to strip a dependency the spec states twice as contract. The pass caught it by re-testing every
  item rather than only the three the finding cited, and rewrote it with its own clause instead of
  dropping it — which keeps the recommendation retracted while naming the dependency as contract.
- **The maintainer's block was left alone, and the reason given is the right one.** Both of its
  remaining items grep to zero in the spec, so "no longer makes" is true there; the new definition
  covers the stronger spelling with one general sentence rather than a special case, which would have
  been a fourth tally of one set.
- **The tie-break narrowing is a better fix than my finding implied.** It removes the mis-routing by
  scoping the rule to provenance and naming the spec — not `## Standing notes` — as the authority on
  whether a claim is still made, while keeping the pass-3 case it was written for.
- **The `D17` correction landed in both files and they agree.** Worker 0 corrected the plan's row and
  Worker 1 corrected the durable bullet, independently, to the same narrower fact; I verified the
  fact at source (`base.py:1073` / `:535` / `:537` / `:1232`) rather than against either document.
  That closes my pass-4 items 10 and 16 together.
- **No count anywhere in the file changed, so nothing had to be kept in step.** The `**Cut**`,
  `**Moved**`, `**Deleted**`, `**Restated in the spec, not moved**` and `**Deliberately left in the
  spec by this pass**` bullets and the other nine `## Standing notes` entries carry no new tally, and
  the `**Moved**` measurement re-reproduces unchanged. That is the pass-2 lesson applied rather than
  re-learned, for the second consecutive pass.
- **Two candidates opened and resolved as clean**, recorded so pass 6 does not re-derive them.
  `## How to read this file` `:17`-`:18` — "A section this pass cut nothing from has no entry here …
  it means the whole section is contract" — reads at first like the absolute-assertion class this
  cycle has filed three times, since `## Standing notes` hands four entry-less sections (`## Current
  state`, `## Proposed improvements`, `## References`, `## Implementation checklist`) to the
  reconciliation item. It is not: "contract" is this file's standing antonym for "deliberation"
  (`:186` "the dependency **contract**", `:721` "a checklist is contract scaffolding"), not a claim
  of correctness, and the same section's last bullet sends the reader to `## Standing notes` before
  editing the spec. Left as written. And the `### Two glossary anchors were re-sited` note's
  mechanism claim is correct at source: `import_spec_terms` rebuilds a Done card's links from the
  companion `*-terms.csv`, `check_spec_glossary.py` is the gate a dropped body link trips.
- **Everything that had to survive did.** Ten single-carrier anchors, 30/30 link targets resolving,
  15/15 unique heading slugs, both in-page anchors resolving, the terms CSV never opened,
  `import_spec_terms --check` green, rule 27 holding in both files, zero fences in either, the spec
  byte-identical for a fourth consecutive pass, and no source, test, or example file changed by this
  cycle.

### Temp test verification

None. No temp test was written and none was warranted: this cycle changes no code path, so there is
nothing a test could exercise. `docs/builder/temp-tests/r1/` was not created in this pass either.
Every verification above is a read-only command over the two changed files, the read-only HEAD copy,
package source, or the repo's own checker scripts; the two measurement scripts I wrote ran from a
scratchpad **outside the repository** and are not build artifacts.

**Static helper.** `scripts/review_inspect.py` was **not** run, and the skip is recorded here per
`worker-3.md` `## Static helper use`. `BUILD.md` `### When to run the helper during build` triggers
it on a new `.py` file, a touched file under `optimizer/` or `types/`, or 30+/50+ new lines of logic.
`git diff --stat -- django_strawberry_framework/ tests/ examples/` is empty, so no trigger fires. No
shadow file was read or written.

**Failability proofs.** The report's `None; this pass introduced no new boundary.` is verified rather
than accepted: `git diff -- django_strawberry_framework/` is empty, so there is no boundary, guard,
gate, or rejection path to prove. `worker-3.md`'s mandatory re-run floor is satisfied by an **empty
re-run set**, which it permits only when the diff introduces no boundary meeting the floor — that
condition holds by measurement. **No boundary was re-run and none was accepted on a builder's record,
because none exists.** Worker 3's source carve-out was not exercised: no production file was mutated
at any point in this pass.

**Hot-path budget.** Not owed. The plan declares `none`, and correctly — nothing in this diff runs
per request, per resolver, per row, per connection, or per outbound message.

**Floor verification.** Not owed. The plan declares scope `none`, and correctly — the diff touches no
Django / Strawberry / channels integration seam.

**Coverage.** No `pytest` run, no `--cov*` flag in any form, at any point in this pass.

### Notes for Worker 1 (spec reconciliation)

**This is the complete, current R2 handoff and it supersedes the pass-4 list.** R2 is the next item
and the same role, so nothing lives only in a closed section. Items 1-9 and 11-15 are re-issued with
every reference re-checked against the files on disk this spawn; item 10 is replaced (both pass-4
findings are closed); item 16 is **discharged**; items 17-18 stand; item 19 is new. The spec has not
changed since pass 2, so its references are unmoved; the rationale grew 786 → 806 lines, so its
references have.

1. **`D5` leaves the spec with no extension-lifecycle statement at all.** R1 deleted the falsified
   spike and its recommendation rather than replacing them. The open question is whether the spec
   states the current construction form or points at `spec-029` Decision 3, which owns it. The build
   plan's anti-absorption rule, `docs/README.md` #"The optimizer is a module-level singleton wrapped
   in a factory", and `docs/GLOSSARY.md` #"Use a module-level singleton wrapped in a factory" all
   argue for the pointer; I agree, and re-confirmed both documents this spawn. **What R2 must not do
   is transplant the corrected recommendation into spec-004** — that is the
   `**The scope trap specific to this spec.**` failure.
2. **`D24` is already discharged** by the `## Priority and ordering` deletion — all eight slices now
   sit under `## Proposed improvements` in heading order. Verify, do not perform.
3. **`### B6` `**Public API.**` says "classmethod"; HEAD ships a `@staticmethod`.** Kept verbatim on
   purpose; a one-word correction and R2's. Spec `:108`; I re-confirmed the `@staticmethod` at
   `optimizer/extension.py::DjangoOptimizerExtension.check_schema` this spawn.
4. **`## Implementation checklist` bullet 2 is the last in-spec trace of the cache-lifetime spike**
   (spec `:174`, `- [x] B1 cache-lifetime spike (10-min investigation, precedes B1 implementation)`).
   A checklist is contract scaffolding so R1 left it, but its parenthetical is a sequencing claim
   about work eleven versions shipped and the section it pointed at is gone. R2's call whether it is
   trimmed.
5. **`## References`' third paragraph is still dangling** (`D27`, spec `:169`): it cites a "skip
   Strawberry conversion" optimization "noted in B1's implementation" that `### B1` never noted, at
   HEAD or now. R1 neither created nor repaired it. The thing that did land is the
   deferred-conversion thunk, a different mechanism.
6. **`### B7`'s "No `_meta.get_fields()` call ever appears in the request path" was cut, but its
   contradiction survives elsewhere.** The contradicting sentence — `**Walker needs registry
   lookup.**`'s unregistered-model fallback at spec `:131` — is still there and still true, and `D23`
   records it as a documented dual contract. Nothing is owed; **R2 should simply not "restore" the
   deleted claim.**
7. **`D25` and `D28` are discharged and the move report's own handoff does not say so.** Both lived
   inside `## Priority and ordering` and went with it. The rationale's `### The former `## Priority
   and ordering`` entry (`:615`-`:668`) records both correctly, so the durable record is complete —
   but an R2 working from the original list will hunt two sentences that no longer exist.
8. **`D6` is narrower than the drift table anticipated, and here is exactly how much.** The policy
   half is stated in the spec (`**Cache storage.**`, spec `:23`) and is off R2's list. What remains
   is precisely three things, none of which appears anywhere in the spec — re-verified this spawn by
   absence grep, which returns only `:23` and the pre-existing `:27`: the **bound** (`256`), the
   **storage mechanism** (`OrderedDict` + `move_to_end`, and the `suppress(KeyError)` guard against
   the concurrent-eviction race), and the **batch size** (a quarter rather than one entry).
   `**Cache storage.**`'s plural "entries" is generic and neither states nor forecloses the batching.
9. **Decided — do not re-open.** The escalated contract-level question (`## Problem statement`'s
   surviving competitive positioning) was ruled on by the maintainer. The canonical record — the
   decision, its reasoning, and the rejected alternatives each with the reason it lost — is
   `docs/builder/build-004-optimizer_beyond-0_0_3.md` `## Maintainer decision — the surviving
   competitive positioning in `## Problem statement``. **Read it there; it is not restated here and
   it is not R2's to re-derive.** Its operative consequences for R2: the sentence at spec `:7`
   **stays byte-for-byte**; the keep is recorded in the rationale at `:167`-`:176` and `:190`-`:193`,
   so a sweeper who finds a competitor comparison in the spec has already been answered; and
   `## Problem statement`'s "eight improvements that the existing libraries do not ship" framing is a
   **separate** claim, is `D1`'s, and is still R2's.
10. **The Low above is R1's, not R2's**, and it is the only thing holding this item at
    `revision-needed`. It is one clause in the rationale's `**The win.**` entry (`:148`, with the
    framing sentence at `:122`); no spec edit is owed and the spec must stay byte-identical. **Both
    pass-4 findings are closed** — the retracted-claims class by the restored label plus its new
    definition, and `_validate_meta` in both the rationale and the plan.
11. **R2's `_optimizer_field_map` worklist is the rationale's bullet (`:690`-`:697`), not the build
    plan's `D22` row.** Re-derived this spawn: **6 occurrences across 5 sites in 3 sections** — spec
    `:84` (B4 `**Walker needs registry lookup.**`), `:112` (B6's exposed-fields paragraph), `:129`
    (B7 `**Mechanism.**`, **twice**), `:131` (B7 `**Walker needs registry lookup.**`), `:135` (B7
    `**Test surface.**`). `D22` counts four sites and omits `**Test surface.**`. Two riders on the
    same sweep: `:112` is the sole carrier of **both** `metafields` and `metaexclude`, so it must be
    rewritten with the links re-sited rather than dropped; and `:84` additionally still says the
    walker reads `_optimizer_hints` off the type class, which is `D16`'s retired mirror in the same
    sentence. **The pass-4 warning that `### B7`'s and `### B4`'s retracted-claims lists say this
    retraction is already made no longer applies** — the restored label says the opposite.
12. **`### B8`'s surviving opening paragraph is on an R2-facing list — here is where.** The tenth
    bullet of the rationale's `## Standing notes` `### The status claims were left standing`
    (`:710`-`:715`). It states the package's own **pre-B8** behaviour in the present tense ("the
    optimizer blindly stacks another `.select_related("category")` on top", spec `:141`), and
    shipping B8 is what falsified it. The build plan's drift table carries **no** row for it: its
    three B8 rows (`D24`, `D25`, `D26`) name the document structure, the deleted ordering section,
    and the cut fence. **Work this item from the rationale bullet, not from the drift table.**
13. **The link-target disk check has an expiry and mine is the current reading, not the last word.**
    30/30 resolve at `346d6731`. **R2 and R3 re-run it themselves rather than quoting this one**, and
    re-run `import_spec_terms --check` after any further concurrent DB write.
14. **Baseline state for Worker 0 to append** (reported, never reverted): `git status --short` was the
    same four cycle paths at the start and end of this pass — no churn at all, for the fifth
    consecutive pass. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`,
    `examples/fakeshop/db.sqlite3`, and `django_strawberry_framework/optimizer/predicates.py` are all
    clean at `346d6731` — but R3 re-derives that rather than inheriting it.
15. **A standing hazard this cycle has now demonstrated six times, worth carrying into R2's own
    writing.** Counts or universals wrong or unreproducible: `_optimizer_field_map` "five mentions";
    the survival summary; "two B8 rows"; the shingle triple falsified by a later edit; "42" quoted
    runs; and this pass's "the only place in the whole corpus", which fails by 48 counterexamples.
    R2 rewrites more prose than R1 did, in the same durable files. **State the unit beside any count,
    state the population beside any universal, state the method beside any measurement, and
    re-measure after the last edit rather than while making it** — and prefer the durable file's own
    solution, which was to state the population qualitatively and let named counterexamples carry the
    argument.
16. **Discharged: the build plan's `D17` row is corrected and agrees with the rationale.** Worker 0
    rewrote the row; I read it and verified the underlying fact at source (`types/base.py`:
    `_validate_meta` defined 1073 / called 535, `_validate_optimizer_hints` defined 1232 / called
    537). Nothing further is owed on it. The sentence it governs (spec `:86`) is still the **sole
    carrier of the `configurationerror` anchor**, so it remains the anchor-bearing rewrite with the
    least margin for a wrong premise.
17. **A small factual imprecision in the rationale, still an R2 touch-up rather than a finding — with
    one new fact.** The `### B1` entry `:214`-`:215` calls it "the locked `strawberry-graphql
    0.316.0`". `0.316.0` is the **declared floor** (`pyproject.toml` #"strawberry-graphql>=0.316.0");
    `uv.lock` resolves **0.323.2**. New this spawn: **`spec-029` uses the same word** —
    `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` #"P1.1 — stale extension-lifecycle model" says
    Decision 3 was "re-derived against 0.316.0 and pinned to the locked version". So spec-004's
    rationale inherited the phrasing from the spec that owns the correction. If R2 tightens it, it
    should decide for both rather than leave the two documents disagreeing.
18. **Do not "fix" the candidates prior passes opened and left, and do not re-derive them.**
    `## How to read this file` `:51`-`:52` ("headings that no longer exist in the spec at all") and
    the `**The win.**` entry's `:120` ("The `**The win.**` label no longer appears in the spec") are
    both **true as written** — the single `grep 'The win\.'` hit at spec `:3` is a mention inside a
    code span naming the class that moved, not a paragraph label. Add to that list, from this pass:
    `## How to read this file` `:17`-`:18` ("the whole section is contract"), which is a statement in
    this file's deliberation/contract vocabulary and not a correctness claim, and `### B8`'s
    maintain-by-hand retracted item, whose entry body already protects the surviving requirement.
19. **New — the block label now diverges from all three sibling rationales, deliberately.**
    `**Claims the spec may no longer make.**` here, against **47** non-modal
    `**Claims the spec no longer makes.**` labels in `spec-001` (17), `spec-002` (8) and `spec-003`
    (22) rationales, and against `docs/SPECS/spec-002-optimizer-0_0_2.md:8`'s companion pointer
    ("every claim it once made and no longer makes"). The divergence is correct: those three ran an
    R2 spec-reconciliation pass before their labels were finalized, so the factual spelling was
    earned there; spec-004's R2 has not run. **R2 must not harmonize spec-004's label back to the
    sibling form, and if R2 does perform the retractions it should decide deliberately whether the
    label then earns the factual spelling** — the file's own definition at `:30`-`:41` is what makes
    either spelling readable, so that definition is the thing to keep in step, not the label alone.

### Review outcome

`revision-needed`.

One Low, neither addressed nor rejected, and `worker-3.md`'s acceptance gate requires every High,
Medium, and Low finding to be addressed or intentionally rejected with a recorded reason. The
escalation carve-out does not reach it — that is for Medium-or-higher findings needing spec context,
and this needs neither. It is one clause in the rationale; no spec edit is owed, and the spec must
stay byte-identical.

**Everything the prompt sent me to grade came back sound, and the two judgements it flagged are both
right.** The Medium's fix is a redefinition paired with a restored modal, not a relabel, and it
survives the pass's own euphemism test on the strength of the new definition rather than the word.
`### B5` is a real sixth member and its rewrite is the one edit that stops the restored label
instructing R2 to strip a dependency the spec states twice. The maintainer's block is intact — every
string pass 3 quoted from it reproduces, and both its remaining items grep to zero in the spec, so
leaving it byte-unchanged is right. The tie-break narrowing closes the case I produced by scoping the
rule to provenance and naming the spec as the authority on what the spec claims, while keeping the
pass-3 case it was written for. And `_validate_meta` is now correct in both the rationale and the
plan, verified at source rather than from either.

**One claim in the report does not survive re-derivation, and I report it as a correction rather than
a finding**, because it lives only in this per-cycle artifact and the durable file asserts nothing of
the kind: "the block's label is the *only* place in the whole corpus that states this obligation
without the word **may**". It is the fourth file to drop it, after 47 non-modal labels across the
three sibling rationales and spec-002's own companion pointer. The corrected account is better than
the one it replaces — the label is inherited house form, defensible in siblings whose R2 had already
run — and it is on the R2 list as item 19 so the divergence is not reversed by a harmonizing sweep.

**What holds the item open is one clause in a place no sweep had opened.** Four passes have argued
about how many `**The win.**` paragraphs survived and why; none tested the criterion the entry gives
for the survival. Three of the eight name no competitor, not one, so the stated criterion does not
discriminate — and the file's own standing note sends an over-cut sweeper at exactly this entry, where
the wrong action available is restoring a paragraph that was correctly cut. The right criterion is
already in the entry twelve lines above, and applying it reproduces all three dispositions.

Per the build plan's `### Deviation 2` corollary this routes to **Worker 1**, not Worker 2. Worker 1
applies the correction, sets `Status: planned` again, and returns the artifact here.

### Working-tree churn observed during this review — reported, not reverted

**None.** `git status --short` was the same four entries at the start and at the end of the pass:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
```

`HEAD` is **`346d67312599c0536980969caa39085ab3885ae8`**, re-derived this spawn, and it did not sweep
this cycle's work: `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns
**`20a9752f`** and the three artifacts are still untracked. That is the standing hazard check, done
with `git log` rather than `git status` alone. No stray untracked file appeared, and nothing was
reverted. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, and
`examples/fakeshop/db.sqlite3` are all clean.

---

## Build report (Worker 1, apply-changes pass 5)

Per the build plan's `### Deviation 2` corollary, an R1 `revision-needed` routes to Worker 1: the
same two rules that make Worker 1 the only role that may perform the move make it the only role
that may fix it. `Status:` is `planned` on return, which Worker 0 reads as "dispatch Worker 3" for
a pass-6 review. Every prior entry — all five of Worker 3's review sections included — is
untouched.

**One Low, fixed; nothing rejected.** The spec was **not** reopened: every edit is inside
`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`, and the spec is byte-identical to
the file Worker 3 read at passes 2, 3, 4, and 5 (216 lines / 26,480 bytes, `git diff --stat` still
28 insertions / 171 deletions). Worker 3's 19-item `### Notes for Worker 1 (spec reconciliation)`
was read and is R2's; nothing in it was acted on, item 9's settled maintainer ruling and item 19's
deliberate divergence included.

### The count, re-derived before anything was written

The finding's own instruction, and the standing one in `BUILD.md` `## Claims are proven
mechanically`. Against the read-only HEAD copy (`git show HEAD:<spec>` into a scratchpad outside the
repository; **33,928 bytes / 359 lines**), the eight `**The win.**` paragraphs are the whole lines
at HEAD `:17`, `:50`, `:82`, `:115`, `:158`, `:181`, `:239`, `:271`. Each was read in full, not
grepped for a token list chosen in advance:

| HEAD line | slice | competitor named |
|---|---|---|
| `:17` | B1 | `strawberry-graphql-django` |
| `:50` | B2 | `strawberry-graphql-django` |
| `:82` | B3 | `strawberry-graphql-django`, `django-debug-toolbar` |
| `:115` | B4 | `strawberry-graphql-django`, "DRF teams" |
| `:158` | **B5** | **none** — "Stash the computed `OptimizationPlan` on `info.context` … Makes the optimizer's behavior observable instead of magic." |
| `:181` | B6 | "None of the existing libraries ship this" |
| `:239` | **B7** | **none** — "The O2 walker rebuilds …"; `O2` is this package's own walker |
| `:271` | **B8** | **none** |

**Three of eight, not one.** The finding reproduces exactly, and the framing sentence at `:122`
was wrong for the same three. The one thing worth adding to the finding's derivation: B7's paragraph
does name a walker, but it is *this package's* O2 walker (`spec-002`'s), which is why a token grep
alone could mislead — the paragraphs were read, and the naming is of the package's own behaviour.

**The dispositions are right on the test the entry already states**, and I re-derived that too
rather than taking it from the finding, against the post-move spec:

- **B7** — `**Mechanism.**` carries "The walker reads `target_type._optimizer_field_map` instead of
  calling `model._meta.get_fields()`", which is the win paragraph's whole factual content. Cut
  correctly.
- **B5** — `**Mechanism.**` carries the stash and "Consumers and test code access it directly". Cut
  correctly.
- **B8** — `**Mechanism.**` opens "Before applying the plan in `_optimize`, inspect the queryset's
  existing optimization state" and restates nothing of the problem. Kept correctly: cutting the
  opening paragraph would have left the slice with no statement of what it fixes.

### The fix, and the integration line it was scoped on

The finding names two sites. My integration sweep found **two more writable copies of the same
characterization, and one in the spec, which is frozen this pass.** All four writable ones are
fixed in this pass; the fifth is recorded durably and routed.

The line the sweep was scoped on, stated so pass 6 can grade it rather than re-derive it: **fix
where the text quantifies over the eight; leave where it names a class of material.** A sentence
that says "each" or "the only one" is an assertion a reader takes as fact; a sentence that lists
"competitive argument" among the classes this pass cut is a description of what was acted on, and
competitive argument *was* cut, five paragraphs of it.

| # | Site | Was | Now | Flagged? |
|---|---|---|---|---|
| 1 | the entry's `**Kept in the spec**` bullet | "It is the only one of the eight that names no competitor." | B5's and B7's name none either, so naming none is not what kept it — what kept it is the test above: their content is restated in their own `**Mechanism.**` paragraphs and B8's is not | **yes** (`:148`) |
| 2 | the entry's framing sentence | "Each opened its slice by naming what `strawberry-graphql-django` does" | "Each opened its slice by naming the behaviour it improves on … — `strawberry-graphql-django`'s in most of them, this package's own in B5, B7 and B8" | **yes** (`:122`) |
| 3 | the file's opening paragraph | "the competitive argument each slice opened with" | "the argument each slice opened with" | no — integration |
| 4 | the entry's own heading | "— a competitive argument, not a contract" | "— a slice-opening argument, not a contract" | no — integration |

**No tally was added**, which is the constraint the pass-2 fix established and which this cycle has
now held for four consecutive passes. Fix 1 disposes of B5 and B7 *inside* the clause rather than in
a second list; fix 2 names the three exceptions rather than counting the rule.

**Why 3 and 4 are in scope rather than an unasked-for edit.** They are not consistency edits forced
by a changed number — they are the same false statement at two more addresses in the same writable
file. Fixing two copies of a false universal and leaving two is the "half-reconciled, the reader
cannot tell which half is current" failure `worker-1.md` `## Review-round custody` names, and both
sit on the path `## Standing notes` sends an over-cut sweeper down: the opening paragraph is the
file's own statement of what it contains, and the heading is the first line of the entry the
standing note points at.

**Why fix 4 is safe.** The heading's operative half is "not a contract", which is true of all eight
and is the disposition's actual ground; only the characterization changed. Nothing depends on the
heading text: the rationale carries **no** in-page anchor to any of its own headings (verified —
`grep -oE '\]\(#[a-z0-9-]+\)|\]: *#[a-z0-9-]+'` returns nothing, and its two anchor-bearing
definitions target spec headings), and every intra-file reference to this entry is the named textual
pointer "the `**The win.**` entry", which is untouched.

**Three candidates opened and deliberately left, recorded so pass 6 does not re-derive them.**

1. **`## Standing notes` `### The status claims were left standing`'s opener** — "This pass cut the
   *deliberative* layer: competitive argument, proposal code, build order …". Names classes acted
   on, quantifies over nothing. The maintainer pass and pass 3 both opened it and left it on that
   exact distinction, and Worker 3's handoff item 18 says not to "fix" the candidates prior passes
   left. Left again.
2. **The entry's `*Alternative rejected — keep them and cut only the competitor's name.*` block.**
   It records an option that was actually formulated that way and the reason it lost; it asserts no
   universal and states no disposition criterion. The alternative bites only on the members that
   name a competitor, and the disposition it explains is now grounded by the corrected criterion
   four paragraphs below it.
3. **The `*Why they went.*` paragraph's "for seven of the eight the answer is no".** Read as a claim
   about paragraphs — seven did not survive whole — it is true, and the two carve-outs (B6's
   sentence, B1's LRU clause) are documented in the two blocks immediately beneath it. It is also
   the sentence the finding itself identifies as carrying the discriminating test. Left.

### The site that could not be fixed: the spec's own companion pointer

The spec's `:3` companion-pointer paragraph — text **this cycle wrote** — describes what moved as
"the per-slice `**The win.**` arguments *against* `strawberry-graphql-django`". B5's and B7's did
move and name no competitor at all, so it carries the same defect at the one address this pass may
not touch: the prompt freezes the spec byte-for-byte and four consecutive reviews have rested their
structural check on that.

**It is recorded in the durable file rather than only here**, as a closing paragraph of
`## Standing notes` `### The `**The win.**` cut is the one an over-cut review should test first` —
the note that standing-orders the sweep this class attracts, so a sweeper meets the correction on
the path it is already sent down. The pass-2 rule decides the placement: the build plan's drift
table carries no row for a sentence this cycle wrote, so a note living only in this artifact dies
with the cycle. It is on the R2 handoff below as item 20.

### The correction to my own pass-4 report — a correction, not a finding

`docs/builder/ARTIFACT.md` `## Re-pass sections` forbids editing a prior entry, so
`## Build report (Worker 1, apply-changes pass 4)` is untouched and the correction is stated here.

That report claimed the non-modal `**Claims the spec no longer makes.**` label was "the *only* place
in the whole corpus that states this obligation without the word **may**". **It is not**, and I
re-derived Worker 3's counterexamples rather than accepting them:

| file | non-modal labels |
|---|---|
| `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` | 17 |
| `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` | 8 |
| `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` | 22 |

plus `docs/SPECS/spec-002-optimizer-0_0_2.md`'s own companion pointer ("every claim it once made and
no longer makes") — 48 counterexamples, and the label is the fourth file to drop the modal, not the
first.

**Two things follow, and both matter more than the erratum.**

- **The fix stands and was graded sound.** Worker 3's own grading turns on the new definition, not
  on the word: it "positively states the thing the old label denied" and re-routes the reader. The
  false universal was the *causal story*, and the corrected story is better — the label is inherited
  house form, defensible in the three siblings because each ran an R2 spec-reconciliation pass
  before its labels were finalized, and wrong here because spec-004's R2 has not run.
- **The false universal did not leak into the durable file, which is why this is a report line and
  not a defect I had to fix.** Checked rather than assumed: `grep -niE 'only (place|site|one|file|
  statement|source)|whole corpus|in the corpus|nowhere else|no other'` over the rationale returns
  seven hits and **none** asserts corpus-wide uniqueness for the label. The nearest, the new
  definition at `## How to read this file`, says the block holds a claim "in the corpus's own
  words" — a statement about `BUILD.md`'s wording, which is true and which I re-read this spawn. The
  other hits are about the eight paragraphs (now corrected), B6's API sentence, B1's LRU clause, and
  the `**Moved**` bullet's quotation clause, and each is scoped to this document.

The generalisable rule, which is Worker 3's handoff item 15 with one more instance: **state the
population beside any universal.** "The label is the only site in the corpus" was a universal over a
corpus I had grepped for the *modal* form and not for the *non-modal* one — the inverse sweep, which
is the same omission the pass-4 relabel itself had to correct for in the other direction.

### Files touched

- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — 5 edits: the four in the table
  above, plus the new closing paragraph of the `**The win.**` standing note recording the spec's
  companion-pointer clause. One further line-wrap reflow of the quotation list the framing sentence
  introduces, because fix 2 lengthened its lead-in; no word of the quotations changed. 806 -> 815
  lines, 57,790 -> 58,432 bytes (+642).
- `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` — **not touched.** Not writable this pass, and the
  finding owed no spec edit.
- `docs/builder/bld-004-r1-rationale_move.md` — this section appended; `Status:` set to `planned`.
- `docs/builder/worker-memory/worker-1.md` — **consolidated before appending**, as
  `worker-1.md` `## Memory entry` requires beyond ~50 lines: the five per-pass entries (45 lines)
  became one cycle-shape block plus two pattern blocks, then this pass's entry.

**No count anywhere in the rationale changed, so nothing had to be kept in step.**
`## Provenance of this record`'s five label bullets, the `**Moved**` measurement, and every other
`## Standing notes` entry are byte-unchanged.

### Validation run — every result quoted verbatim

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
  -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**.
  Character-identical to the build plan's pre-flight baseline.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md docs/builder/bld-004-r1-rationale_move.md`
  -> **exit 0** on all three files.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have
  glossary links.` **exit 0**. **Read-only form only**; the writing form was never invoked.
- **Every link definition re-resolved on disk this spawn, not quoted.** Each target resolved from
  its own source file's directory and existence-tested: spec **11 definitions / 11 distinct uses**,
  rationale **19 / 19**, **0 undefined references, 0 unused definitions, 0 of 30 targets missing.**
  No definition was added or removed. **R2 and R3 re-run this rather than quoting it.**
- **Per-anchor 10-anchor constraint, re-derived.** `grep -o "\[glossary-<anchor>\]" | wc -l` -> **2
  for every one of the ten** (1 body use + 1 definition): `configurationerror`,
  `djangooptimizerextension`, `djangotype`, `fk-id-elision`, `metaexclude`, `metafields`,
  `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `queryset-diffing`. The spec was not
  edited this pass, so this is a confirmation. **The terms CSV was not opened**: it is absent from
  `git status --short`.
- **Byte / line count.**

| | lines | bytes |
|---|---|---|
| spec at Worker 3's pass-5 review | 216 | 26,480 |
| spec **now** | **216** | **26,480** (unchanged — not touched) |
| spec at HEAD (pre-move) | 359 | 33,928 |
| net move + revisions | **-143** | **-7,448 (-21.9%)** |
| rationale before this pass | 806 | 57,790 |
| rationale **now** | **815** | **58,432** (+642 over five edits) |

- `git diff --stat -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **28 insertions / 171
  deletions**, the hunk shape Worker 3 recorded at all five reviews. `git show HEAD:<spec> | wc -l -c`
  -> **359 / 33,928**, so the baseline the move was measured against has not moved.
- **Label spellings, enumerated rather than asserted.** `grep -o '^\*\*Claims the spec[^.]*\.\*\*'`
  -> **10** `**Claims the spec may no longer make.**` and **1** `**Claims the spec no longer makes
  as any slice's own argument.**` (the ruling's) — unchanged by this pass.
- In-page anchors: the repo's own `scripts/check_spec_glossary.py::github_anchor` over the spec's
  **15** headings -> **15 unique slugs, 0 duplicates**; `#problem-statement` and
  `#proposed-improvements` both resolve. **No in-page anchor was added or invalidated** — the
  rationale carries none to its own headings, which is what makes the heading edit safe.
- `grep -c '^```'` -> spec **0**, rationale **0**. No fence introduced.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files -> **no match** (exit 1). Rule 27 holds.
- `grep -nP '\]\((?!#|https?:)'` over both files -> **no match** (exit 1). Reference-style
  preserved.
- `grep -c "LINK DEFINITIONS"` over the rationale -> **1**. The pass-3 method clause still does not
  embed the marker it tells the reader to split on.
- **Line wrap.** Longest rationale body line (excluding the H1, which is 121 at HEAD of this cycle)
  is **103**, unchanged; every line this pass wrote is 88-99.
- `git diff --stat -- django_strawberry_framework/ tests/ examples/` -> **empty**. No source, test,
  or example file touched; no `pytest`, no `ruff` (no `.py` file changed), no coverage-shaped flag
  in any form.
- No `git stash`, `checkout`, `restore`, `worktree`, `commit`, or branch operation at any point.

### Duplication: the overlap figure moved for the first time this cycle, by 3, and keeping it was the call

Measured under the normalization the file itself states (drop each file's bottom link-definition
block, fold every non-alphanumeric run to whitespace, lowercase, distinct 8-word shingles):

| measure | before this pass | after |
|---|---|---|
| rationale total shingles | 9,085 | 9,201 (+116) |
| left-the-spec shingles present in the rationale | 161 | **161 (unchanged)** |
| rationale x post-move-spec overlap | 52 | **55 (+3)** |

**The +3 is one quotation and it is disclosed rather than suppressed.** It is the new standing-note
paragraph quoting the spec's live companion-pointer clause — "the per-slice `**The win.**` arguments
*against* `strawberry-graphql-django`" — which normalizes to ten words and therefore three shingles.
That is exactly the category the file's own `**Moved**` bullet names and permits: *"a few quote spec
prose that survived, because what the spec still says is the entry's subject."* The alternative was
to paraphrase the clause under the 8-word floor, which is what the maintainer pass's edit 2 happened
to do — but shortening a quotation to hold a metric constant would make the item harder to act on,
and the item's whole purpose is to let R2 find and judge that exact clause. **Four prior passes
reported this figure unchanged at 52; this pass is the one that moved it, and this is the reason.**

**The `**Moved**` bullet's durable measurement did not move, re-measured after the last edit:
192 of the pre-move spec's 4,934 shingles, in 41 contiguous runs, longest 20 shingles (27 words),
median 3.** Both its inputs are frozen, and this pass's quotation is of *post-move* spec text, which
cannot reach it. Second consecutive pass in which the re-keying holds under editing.

### Notes for Worker 3 (pass 6)

- **The judgement to audit is the integration line, not the two flagged fixes.** The flagged sites
  are mechanical once the count is re-derived. What is mine is the rule under
  `### The fix, and the integration line it was scoped on`: quantifies-over-the-eight gets fixed,
  names-a-class-of-material does not. The check is to sweep the file for every site characterizing
  the `**The win.**` class and confirm each landed on the right side — and if the line is judged
  wrong, say which direction, because both over- and under-reach are available here.
- **The place to look for an over-correction is the heading edit.** It is the one edit no finding
  asked for that changes a structural element rather than prose. The safety argument is in the
  report (no in-page anchor targets it; every intra-file reference is the named pointer "the
  `**The win.**` entry"); re-derive it rather than reading it.
- **The `52 -> 55` overlap delta is deliberate and is the first movement in five passes.** Confirm
  the cause is the single quoted clause and nothing else — reconstruct the pre-pass file from this
  pass's five edits (it must land on 57,790 bytes / 806 lines) and difference the shingle sets.
- **Two claims worth re-deriving rather than reading:** the three-of-eight count (read the eight
  HEAD `**The win.**` lines in full rather than grepping a token list — B7's names `O2`, this
  package's own walker, which a token grep will not catch), and the 192 / 4,934 / 41-run measurement.
- **The correction to my pass-4 report is stated in this section and the pass-4 section is
  untouched**, per `ARTIFACT.md` `## Re-pass sections`. The check that matters is the second half:
  that the false universal never reached the durable file. The grep is in the report.
- **One item is routed, not enacted:** the spec's `:3` companion-pointer clause carries the same
  defect and the spec is frozen this pass. It is recorded durably in `## Standing notes` and is
  R2 handoff item 20. If pass 6 judges that it should have been fixed in the spec instead, that is a
  scope question for Worker 0, not a rewording.
- Nothing from this pass was staged for later without being written down. No temp test, no shadow
  file, no `docs/builder/temp-tests/` directory.

**Failability proofs.** None; this pass introduced no new boundary. `git diff --
django_strawberry_framework/` is empty, so there is no boundary, guard, gate, or rejection path to
prove.

**Hot-path budget.** Not applicable; the plan declares `none`, and correctly — nothing in this diff
runs per request, per resolver, per row, per connection, or per outbound message.

**Floor verification.** Not applicable; the plan declares floor-verification scope `none`, and
correctly — the diff touches no Django / Strawberry / channels integration seam.

**Coverage.** No `pytest` run, no `--cov*` flag in any form, at any point in this pass.

### The R2 handoff — item 20, added to Worker 3's 19

Worker 3's pass-5 `### Notes for Worker 1 (spec reconciliation)` is the complete current list and is
not restated here. Two amendments:

- **Item 10 is closed.** The Low is fixed, and the fix reached three further sites, one of which
  became item 20.
- **20. New — the spec's companion-pointer paragraph mischaracterizes the class it points at.**
  Spec `:3` describes what moved as "the per-slice `**The win.**` arguments *against*
  `strawberry-graphql-django`". B5's and B7's did move and name no competitor at all; the rationale
  is now correct on this and the spec is not. It is a clause-width widening, it was written by this
  cycle rather than inherited, and **the build plan's drift table carries no row for it**, so it
  exists only in the rationale's `## Standing notes` and here. The corrected characterization is in
  the rationale's `**The win.**` entry and its framing sentence.

### Spec changes made (Worker 1 only)

**None.** The spec was not writable this pass and was not edited. `git diff --stat` on it is
unchanged at 28 insertions / 171 deletions and its byte count is identical to Worker 3's pass-2
through pass-5 readings (216 lines / 26,480 bytes), so the three pass-1 revision edits remain the
whole of this cycle's spec delta.

**Spec status-line re-verification** (`worker-1.md` `## Spec status-line re-verification`, re-run
this spawn as every Worker 1 spawn must): spec-004 carries **no** `Status:` / owner / target-release
/ predecessor header block — lines 1-5 are the title, the companion-pointer paragraph, and
`## Problem statement`. Nothing in them is a status line this build has falsified, so no header edit
was owed, and none could have been made this pass in any case. The `:3` paragraph's inaccuracy found
this pass is a mischaracterization of moved content, not a status line, and is routed as handoff
item 20.

### Working-tree churn observed during this pass — reported, not reverted

**None.** `git status --short` was the same four entries at the start and at the end of the pass,
for the sixth consecutive pass:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
```

`docs/builder/worker-memory/worker-1.md` was rewritten this pass and correctly does not appear
above: `.gitignore:188` ignores `docs/builder/worker-memory/`, confirmed this spawn with
`git check-ignore -v`. Worker memory is untracked by design, so a four-entry `git status` is not
evidence the memory entry was skipped.

`HEAD` is **`346d67312599c0536980969caa39085ab3885ae8`**, re-derived this spawn rather than quoted,
and it did **not** sweep this cycle's work: `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-
0_0_3.md` still returns **`20a9752f`**, and the rationale, this artifact, and the build plan are all
still untracked. That is the standing hazard check, done with `git log` rather than `git status`
alone. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, and
`examples/fakeshop/db.sqlite3` are all clean — but pass 6 re-derives that rather than inheriting
this reading.

---

## Review (Worker 3, pass 6)

Read in order, as the prompt directs: `docs/builder/worker-3.md` (full), `AGENTS.md`, `START.md`,
`docs/builder/BUILD.md` (full), `docs/builder/ARTIFACT.md`, `docs/README.md`,
`examples/fakeshop/test_query/README.md`, `docs/builder/build-004-optimizer_beyond-0_0_3.md`
including its settled `## Maintainer decision` (not re-opened) and its corrected `D17` row, this
artifact end to end in the prescribed order (plan, move report, `## Review (Worker 3)`,
apply-changes, `## Review (Worker 3, pass 2)`, apply-changes 2, maintainer-decision pass,
`## Review (Worker 3, pass 3)`, apply-changes 3, `## Review (Worker 3, pass 4)`, apply-changes 4,
`## Review (Worker 3, pass 5)`, apply-changes 5), the spec, the rationale, and the pristine HEAD
spec obtained read-only as `git show HEAD:docs/SPECS/spec-004-optimizer_beyond-0_0_3.md >
<scratchpad outside the repo>/spec-004-HEAD.md`. No `git stash` / `checkout` / `restore` /
`worktree` at any point, and no prior entry was edited.

`HEAD` re-derived this spawn rather than quoted: **`346d67312599c0536980969caa39085ab3885ae8`**; the
HEAD spec blob is **33,928 bytes / 359 lines**. `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-
0_0_3.md` still returns **`20a9752f`** and the three artifacts are still untracked, so no concurrent
commit has swept this cycle's work. `git status --short` is the same four cycle paths and nothing
else.

**Nothing below is quoted from any build report.** Every figure was re-derived from the files on
disk this spawn.

### High:

None.

### Medium:

None.

### Low:

#### The integration sweep found one unfixable spec site; there are three, and the durable note that carries them says "One clause"

The pass's own account of the site it could not fix:

```docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:771
One clause about this class is still inaccurate, and it is in the spec rather than here: the
companion-pointer paragraph describes what moved as "the per-slice `**The win.**` arguments
*against* `strawberry-graphql-django`", and B5's and B7's, which did move, name no competitor at
all. The reconciliation item owns that clause.
```

That clause is real and correctly characterised. It is not the only one. **The eight per-slice
pointer paragraphs this cycle added to the spec carry the same characterization**, and two of them
carry it about the two paragraphs the same pass had just established name no competitor:

```docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:100
The competitive argument for this slice, the ordering argument for landing it before its
dependents, and the stash sequence it proposed are in the [rationale file][spec-004-rationale].
```

```docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:133
The competitive argument for this slice, its relationship to B1's plan cache, and the map
construction and lookup it proposed are in the [rationale file][spec-004-rationale].
```

Measured, not read. `grep -n 'competitive argument' <spec>` returns **seven** lines — `:29`, `:47`,
`:63`, `:90`, `:100`, `:121`, `:133` — one per slice except B8, whose pointer at `:151` correctly
omits the clause because B8's win paragraph stayed. Of the seven, **B5's (`:100`) and B7's (`:133`)
name material that names no competitor**: B5's `**The win.**` (HEAD `:158`) is "Stash the computed
`OptimizationPlan` on `info.context` … Makes the optimizer's behavior observable instead of magic",
and B7's (HEAD `:239`) is "The O2 walker rebuilds `{f.name: f for f in model._meta.get_fields()}` on
every walk" — this package's own walker. Neither pointer's other named items absorb the clause: B5's
"ordering argument" is the cut sequencing clauses and B7's "relationship to B1's plan cache" is the
cut derivation, both listed separately in the same sentence, so "the competitive argument for this
slice" can only denote the `**The win.**` paragraph.

So the same false characterization sits at **three** spec addresses — `:3`, `:100`, `:133` — where
the record names one. And it is the record, not the spec, that is this pass's to get right: the spec
is frozen, so the whole remedy for an unfixable site is that it is enumerated completely somewhere
R2 will read.

**Why a reader acts on it.** `## Standing notes` is the durable half of the handoff by this pass's
own argument ("a note living only in this artifact dies with the cycle"), and R2 handoff item 20 is
built from it. As written, R2 corrects `:3` and leaves `:100` and `:133` — after which the spec's
per-slice pointers assert of B5 and B7 exactly what the rationale four hundred lines away denies of
them, both written by this cycle. That is the "half-reconciled, the reader cannot tell which half is
current" failure the pass invoked as its own reason for fixing writable sites 3 and 4; the same
reason reaches these two. It is also, exactly, the shape this cycle has now filed three times: a
durable enumeration that undercounts the sites R2 has to sweep (the pass-1 `_optimizer_field_map`
Low; the pass-2 Low, whose load-bearing half was that B8's paragraph reached no R2-facing list).

**Why Low and not Medium.** No builder acts wrongly on it, nothing in R1's own output turns on it,
and the spec pointers still resolve to the right file and the right entry. It is the pass-1
card-import-chain Low's severity, for the pass-1 undercount Low's reason.

**Recommended change.** One clause in the same closing paragraph, and **no tally** — name the sites
rather than count them, per the constraint the pass-2 fix established: state that the
characterization is in the companion-pointer paragraph **and** in the per-slice pointers for B5 and
B7, all three of which the reconciliation item owns. Then widen R2 handoff item 20 to the same three.
No spec edit is owed by this pass, and the spec must stay byte-identical.

**Test expectation.** None; no behaviour changes. The verification is the one applied above:
`grep -n 'competitive argument' <spec>`, then read each named slice's HEAD `**The win.**` line in
full and ask whether it names a competitor.

### The five graded items — each re-derived, not confirmed

**1. The count, and the added observation about `O2`.**

**Three of eight reproduces exactly.** I read the eight HEAD `**The win.**` lines in full rather
than grepping a token list, as the pass's own note asks:

| HEAD line | slice | competitor named |
|---|---|---|
| `:17` | B1 | `strawberry-graphql-django` |
| `:50` | B2 | `strawberry-graphql-django` |
| `:82` | B3 | `strawberry-graphql-django`, `django-debug-toolbar` |
| `:115` | B4 | `strawberry-graphql-django`, "DRF teams" |
| `:158` | **B5** | **none** |
| `:181` | B6 | "None of the existing libraries ship this" |
| `:239` | **B7** | **none** |
| `:271` | **B8** | **none** |

**The added claim about B7 checks out and is worth the space it takes.** B7's paragraph does name a
walker — "The **O2** walker rebuilds `{f.name: f for f in model._meta.get_fields()}` on every walk"
— and `O2` is this package's own: `docs/SPECS/spec-002-optimizer-0_0_2.md` `### O2 — Selection-tree
walker`, shipped, and named as shipped in spec-004's own `## Current state`. A reviewer grepping the
eight lines for a competitor **token** gets the right answer here by luck; a reviewer grepping for
"walker" or for any named-subject heuristic gets the wrong one. The observation is a correct
strengthening of my own pass-5 derivation, not a restatement of it.

**2. The four writable fixes, and the integration line they were scoped on.**

All four are present and correct, verified against the files:

- `:149` — "B5's and B7's name no competitor either, so naming none is not what kept it — what kept
  it is the test above: their factual content is restated in their own slices' `**Mechanism.**`
  paragraphs and B8's is not". Disposes of B5 and B7 **inside** the clause, adding no second list.
- `:122` — "Each opened its slice by naming the behaviour it improves on and why this package would
  do better — `strawberry-graphql-django`'s in most of them, this package's own in B5, B7 and B8".
- `:5` — the opening paragraph now reads "the argument each slice opened with".
- `:117` — the entry heading now reads "— a slice-opening argument, not a contract".

**The heading edit is safe and I re-derived the safety argument rather than reading it.**
`grep -oE '\]\(#[a-z0-9-]+\)|\]: *#[a-z0-9-]+'` over the rationale returns nothing, and its two
anchor-bearing definitions (`spec-004-improvements`, `spec-004-problem`) target **spec** headings,
both of which still resolve under the repo's own slugger (15 headings, 15 unique slugs). Every
intra-file reference to this entry is the named textual pointer "the `**The win.**` entry", which is
untouched. Nothing targets the heading.

**Grading the line itself — `fix where the text quantifies over the eight; leave where it names a
class of material`.** The line is right, and I tested it in both directions.

- *Over-reach?* No. Fixes 3 and 4 are not consistency edits forced by a changed number; they are the
  same false statement at two further addresses in the same writable file, and both sit on the path
  `## Standing notes` sends an over-cut sweeper down. Calling them out of scope would have left two
  of four copies current.
- *Under-reach inside the rationale?* No. `grep -niE 'competit'` over the rationale returns five
  lines and every one lands on the right side of the line: `:149` and `:773` are corrected, `:171`
  is the maintainer's block (unchanged, and its scoping clause is the ruling's own text), `:142` is
  the rejected-alternative record, `:682` names classes acted on.
- *Under-reach in the spec?* **Yes — that is the Low above.** The line is sound; its application
  reached one of three spec sites. A sound line applied to an incomplete population is the same
  defect as a wrong line, which is why I am filing the coverage and not the rule.

**The three candidates it opened and left are all correctly left, and I tested each rather than
inheriting the reasons.**

- `:682` `## Standing notes`' opener ("This pass cut the *deliberative* layer: competitive argument,
  proposal code, build order …"). Names classes acted on; quantifies over nothing; competitive
  argument **was** cut, in five paragraphs. Three prior passes left it on the same distinction.
- `:142` the `*Alternative rejected — keep them and cut only the competitor's name.*` block. It
  records an option as it was formulated and why it lost. It asserts no universal and states no
  disposition criterion; the alternative bites only on the members that name a competitor, and the
  corrected criterion sits seven lines below it.
- `:135` `*Why they went.*`'s "for seven of the eight the answer is no". Read as a claim about
  paragraphs it is true. Its supporting clause ("every factual claim inside them is restated in the
  same slice's `**Mechanism.**` paragraph") is overstated for B1 — whose LRU clause was **not** in
  `**Mechanism.**`, which is this cycle's own pass-1 Medium — but the file states that exception
  under a bold lead **twenty-five lines below, in the same entry** ("One further clause was restated
  rather than cut, from a paragraph that otherwise went whole"). A reader who applies the clause to
  B1 and finds it wanting reads on and finds precisely that case documented. No wrong action is
  available, so this is a phrasing I would tighten and not a defect. Recorded so pass 7, if there is
  one, does not re-derive it.

**3. The fifth site, in the spec — real, correctly routed, and correctly left.**

Confirmed at all three legs.

- **The site is real.** Spec `:3` reads "the per-slice `**The win.**` arguments *against*
  `strawberry-graphql-django`", and B5's and B7's did move and name none. It is text this cycle
  wrote: it is added line 1 of the 28 in `git diff`.
- **The routing is where R2 will find it.** The correction is a closing paragraph of
  `## Standing notes` `### The `**The win.**` cut is the one an over-cut review should test first`
  (`:771`-`:774`) — the note that standing-orders a sweep of this exact class, so a sweeper meets it
  on the path it is already sent down — and it is R2 handoff item 20 below. The placement is right
  for the pass-2 reason: the build plan's drift table carries no row for a sentence this cycle
  wrote, so an artifact-only note dies with the cycle. Verified: `grep -n '^| D' <plan> | grep -i
  'companion\|pointer'` returns nothing.
- **Leaving it was correct, not convenient.** The prompt freezes the spec and five consecutive
  reviews have rested their structural check on `216 lines / 26,480 bytes` and `28 insertions / 171
  deletions`; editing it here would retire that check at the last pass, for a clause R2 must open
  anyway (it is a clause-width widening in the same paragraph R2 is already reconciling for `D1`).
  The remedy for an unfixable site is a complete record — which is the one thing the Low says is not
  yet true.

**4. The correction to the pass-4 report, and its negative check verified with a better
instrument.**

The correction is right. Re-derived rather than accepted:
`grep -coE '^\*{1,2}Claims? the spec no longer makes'` gives **17 / 8 / 22** across the spec-001,
spec-002 and spec-003 rationales, plus `docs/SPECS/spec-002-optimizer-0_0_2.md`'s own
companion pointer ("every claim it once made and no longer makes") — 48, and the label is the fourth
file to drop the modal, not the first. The pass-4 entry is untouched, per `ARTIFACT.md`
`## Re-pass sections`.

**The negative check — "the false universal did not leak into the durable file" — holds, and I did
not test it with the instrument that produced it.** The report's grep
(`only (place|site|one|file|statement|source)|whole corpus|in the corpus|nowhere else|no other`)
reproduces at seven hits. It is also the wrong shape to trust on its own: it enumerates spellings of
"only", which is the same "sample the vocabulary rather than establish the population" failure
`BUILD.md` `## Claims are proven mechanically` names, and the sweep it is checking *for* went wrong
in exactly that way. I ran a superset over the rationale —
`\bsole\b|\bunique\b|\bthe one (place|site|file|document|statement)\b|\balone\b|anywhere
else|across the corpus|corpus-wide|\bfirst\b.*\bto (drop|state)\b|sibling|spec-00[123]` — and read
every hit. **No claim of corpus-wide uniqueness for the label exists in the file, in any spelling.**
The `sole` / `alone` / `unique` hits are about glossary-anchor carriers, the plan context key, and
one fence's contents; the `spec-00[123]` and `sibling` hits are the family-provenance bullets. The
nearest thing, the new definition's "in the corpus's own words", is a claim about `BUILD.md`'s
wording, and `BUILD.md` `## Spec rationale extraction` does read "any claim the decision once made
and **may** no longer make" — re-read this spawn. The negative finding survives a better instrument.

**5. The `52 -> 55` overlap delta — the stated cause accounts for the whole of it, proved by
subtraction.**

Implementing the file's own four-line method independently (drop each file's bottom link-definition
block, fold every non-alphanumeric run to whitespace, lowercase, distinct 8-word shingles):

| measure | value |
|---|---|
| rationale x post-move-spec overlap | **55** |
| the same, with `## Standing notes`' new closing paragraph (`:771`-`:774`) removed | **52** |
| shingles contributed only by that paragraph | **3** |

The three are `the per slice the win arguments against strawberry`, `per slice the win arguments
against strawberry graphql`, and `slice the win arguments against strawberry graphql django` — the
ten normalized words of the spec's live companion-pointer clause and nothing else. **52 is the
figure four prior passes reported**, so the delta is fully explained: the other four edits of this
pass contribute zero. Keeping the quotation whole was the right call for the reason given — the
item's purpose is to let R2 find and judge that exact clause, and shortening a quotation to hold a
metric constant is optimising the metric.

**The durable measurement reproduced a third time, on my own implementation of the method:** the
pre-move blob carries **4,934** distinct shingles, the rationale reproduces **192** of them, in
**41** contiguous runs over the HEAD word stream whose longest is **20 shingles = 27 words** and
whose median is **3**. Left-the-spec shingles present in the rationale: **161**, unchanged. Rationale
total: **9,201**. Re-keying that measurement to two frozen inputs is now demonstrated across nine
edits by three different passes.

### DRY findings

- **No duplication was introduced against the spec.** The only figure that moved is the disclosed
  `+3`, isolated above to one quoted clause the file's own `**Moved**` bullet explicitly permits
  ("a few quote spec prose that survived, because what the spec still says is the entry's subject").
  Left-the-spec-in-rationale is unchanged at 161.
- **No tally was added by any of the five edits**, which is the constraint the pass-2 fix
  established and which this cycle has now held for five consecutive passes. Fix 1 disposes of B5
  and B7 inside the clause; fix 2 names the three exceptions rather than counting the rule. The
  `**Cut**` / `**Moved**` / `**Deleted**` / `**Restated in the spec, not moved**` /
  `**Deliberately left in the spec by this pass**` bullets and the other `## Standing notes` entries
  needed no keeping in step, and none was made.
- **The Low is not a DRY finding but its fix is the DRY branch**: name the class of sites in the one
  paragraph that already owns them, rather than adding a second enumeration elsewhere.
- **Against the sibling rationales: unchanged and still clean.** The 17-shingle ordering-invariant
  run that was pass-1's Low-2 is still gone; the remaining overlap is house form for the file class.
  The deliberate label divergence recorded as handoff item 19 stands: 10 modal labels here, 47
  non-modal across the three siblings.
- **Existence challenge: none raised.** The pass adds no abstraction, helper, registry, or
  indirection; it edits prose in one file.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty** (0 lines). `__all__` and the
re-export list are unchanged, and none was authorized to change: the build plan's
`## Build-wide context flags` declares package source, `tests/`, and `examples/` read-only for the
whole cycle. `git diff --stat -- django_strawberry_framework/ tests/ examples/` -> **empty**, so
there is no concurrent-session entry to attribute this pass.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed absent from `git status --short`.

### Documentation / release sanity

Applies — the diff is entirely docs and one of the two files is an archived spec. Both were read end
to end this spawn.

- **The three baseline checkers, re-run rather than quoted.**
  - `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
    -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**,
    character-identical to the build plan's pre-flight baseline.
  - `uv run python scripts/check_trailing_commas.py --check` on the spec, the rationale, and this
    artifact -> **exit 0** on all three.
  - `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have
    glossary links.` **exit 0**. **Read-only form only**; the writing form was never invoked.
- **All ten anchors are single-carrier**, re-derived per anchor rather than on the checker's exit
  code: `grep -o "\[glossary-<anchor>\]" | wc -l` -> **2** for every one of `configurationerror`,
  `djangooptimizerextension`, `djangotype`, `fk-id-elision`, `metaexclude`, `metafields`,
  `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `queryset-diffing`. The spec was not
  edited this pass. **The terms CSV was not opened**: it is absent from `git status --short`.
- **Every link definition resolves on disk — re-run this spawn, because the reading expires.** Each
  target resolved from its own source file's directory and existence-tested: spec **11 definitions /
  11 distinct uses**, rationale **19 / 19**, **0 undefined references, 0 unused definitions, 0 of 30
  targets missing.** All ten `../spec-NNN-….md` siblings the rationale links (002, 003, 004, 016,
  018, 029, 032, 033, 035, 047) are present; none points at a file the concurrent renumber moved.
  Both files carry `<!-- LINK DEFINITIONS -->` with all ten canonical group headers in order, and
  the archived companions correctly file under `<!-- docs/SPECS/ -->`.
- **In-page anchors resolve and the em-dash hazard is still avoided.** The repo's own
  `scripts/check_spec_glossary.py::github_anchor` over the spec's **15** headings -> **15 unique
  slugs, 0 duplicates**; `#problem-statement` and `#proposed-improvements` both land on real
  headings. No in-page anchor was added or invalidated by the heading edit — the rationale carries
  none to its own headings.
- **The spec is byte-identical, and not merely equal in bytes.** **216 lines / 26,480 bytes**;
  `git diff --stat` **28 insertions / 171 deletions**, the hunk shape recorded at all five prior
  reviews; the HEAD blob is still **359 lines / 33,928 bytes**. I extracted all **28** added lines
  and accounted for each against the move plus the three pass-1 revision edits: the companion
  pointer, the re-pointed `## Problem statement` clause, the `**Cache storage.**` restatement, the
  restated `**Directive-variable extraction.**` rules, eight per-slice pointers, the relabelled
  `**Public API.**` / `**Mechanism.**` / `**Strictness API.**` / `**OptimizerHint** typed wrapper`
  lines, the link-carrying `### B8` heading, B8's de-labelled paragraph, the `[spec-004-rationale]`
  definition, and four blank lines. **Nothing beyond the move and the three pass-1 edits is in the
  diff.** Rationale: **815 lines / 58,432 bytes**.
- **Structural properties.** `grep -c '^```'` -> **0 / 0** in both files;
  `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` -> **no match** in both, so `AGENTS.md` rule 27 holds;
  `grep -nP '\]\((?!#|https?:)'` -> **no match**, so the reference-style convention is preserved,
  not merely unbroken.
- **The spec narrates no history.** `grep -niE 'as of (review )?round|amendment|retract|inverted|a
  later strawberry|no longer|used to |formerly|previously|has since'` returns **one** line, `:3`,
  whose only hits are "the former `## Priority and ordering` section" and "may no longer make" —
  rule-1 pointer vocabulary. The pass-1 Low-3 fix still holds at both sites.
- **The policy/status boundary against `D6` still holds**, verified by absence over the whole spec:
  `grep -niE 'lru|evict|bounded|\b256\b|ordereddict|move_to_end|quarter'` returns `:23`
  (`**Cache storage.**`) and `:27` (the pre-existing `lru_cache.cache_info()` mention).
- **Pointer discipline is intact** — eleven `[spec-004-rationale]` occurrences: the companion
  paragraph (`:3`), the re-pointed `## Problem statement` clause (`:9`), eight per-slice pointers
  (`:29`, `:47`, `:63`, `:90`, `:100`, `:121`, `:133`, `:151`), and the definition (`:202`).
  Discipline is not content: the Low above is about what two of those eight *say*, which is the
  question five passes of counting them never asked.
- **Version strings / card IDs / KANBAN.** The spec carries no version or status header, so nothing
  could drift; the rationale's `DONE-004-0.0.3` and "eleven patch versions ago" match
  `pyproject.toml` and `django_strawberry_framework/__init__.py`, both `0.0.14`. No card moved and
  this cycle wrote no DB. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, and
  `examples/fakeshop/db.sqlite3` are **all clean** — re-derived this spawn rather than inherited.
- **No script-rendered doc was regenerated**, so the staging-docstring check has no subject, and no
  obsolete "coming soon" / "planned" wording was introduced.
- **Archival unchanged.** The rationale lives directly at `docs/SPECS/appx/`, the archived-companion
  location `AGENTS.md` rule 26 names.

### What looks solid

- **The fix is right, the count reproduces, and the one thing it added to my derivation is worth
  having.** Three of eight, read in full rather than token-grepped; B7's `O2` is this package's own
  spec-002 walker, which is the case a token grep gets right only by accident. All four writable
  sites are corrected, the correction disposes of B5 and B7 inside the clause instead of opening a
  second list, and no tally was added for the fifth consecutive pass.
- **The integration line is the right line, and stating it was the right thing to do.** Naming the
  rule the sweep was scoped on is what made it gradeable in one pass instead of re-derivable in
  three, and both of its calls hold under test: fixes 3 and 4 belong in scope, and all three left
  candidates are correctly left. My finding is that the line's *application* stopped at the writable
  file's boundary, not that the line is wrong.
- **The heading edit is the one structural change no finding asked for, and it is safe by
  measurement rather than by argument.** The rationale carries no in-page anchor to any of its own
  headings, so nothing could break; every intra-file reference is the named textual pointer, which
  is untouched. This is the shape most likely to be an over-correction and it is not one.
- **The unfixable site was handled the way an unfixable site should be** — recorded in the durable
  file on the path a sweeper is already sent down, routed as a numbered handoff item, and left
  rather than fixed under a freeze that five reviews' structural check depends on. The judgement is
  right; only its enumeration is short.
- **`52 -> 55` is the first movement of that figure in five passes and it is fully explained.**
  Removing the one new paragraph returns it to exactly 52, and the three shingles are the ten
  normalized words of the quoted clause. Disclosing a metric that moved, with its cause, beats
  holding a metric constant by trimming a quotation — and the durable 192 / 4,934 / 41-run
  measurement did not move at all, which is the third independent reproduction of it.
- **The pass-4 correction is stated in the current section with the prior entry untouched, and its
  negative check survives a better instrument than the one that produced it.** I did not accept the
  "only-shaped" grep; a superset over synonyms, uniqueness idioms, and sibling references finds no
  corpus-wide claim about the label anywhere in the durable file, and `BUILD.md`'s modal wording
  reads as the definition says it does.
- **Every invariant that had to survive did.** Ten single-carrier anchors, 30/30 link targets
  resolving, 15/15 unique heading slugs, both in-page anchors resolving, the terms CSV never opened,
  `import_spec_terms --check` green, rule 27 holding in both files, zero fences in either, all 28
  added spec lines individually accounted for, the spec byte-identical for a fifth consecutive pass,
  and no source, test, or example file changed by this cycle.

### Temp test verification

None. No temp test was written and none was warranted: this cycle changes no code path, so there is
nothing a test could exercise. `docs/builder/temp-tests/r1/` was not created in this pass either.
Every verification above is a read-only command over the two changed files, the read-only HEAD copy,
package source, or the repo's own checker scripts; the three measurement scripts I wrote ran from a
scratchpad **outside the repository** and are not build artifacts.

**Static helper.** `scripts/review_inspect.py` was **not** run, and the skip is recorded here per
`worker-3.md` `## Static helper use`. `BUILD.md` `### When to run the helper during build` triggers
it on a new `.py` file, a touched file under `optimizer/` or `types/`, or 30+/50+ new lines of
logic. `git diff --stat -- django_strawberry_framework/ tests/ examples/` is empty, so no trigger
fires. No shadow file was read or written.

**Failability proofs.** The report's `None; this pass introduced no new boundary.` is verified
rather than accepted: `git diff -- django_strawberry_framework/` is empty, so there is no boundary,
guard, gate, or rejection path to prove. `worker-3.md`'s mandatory re-run floor is satisfied by an
**empty re-run set**, which it permits only when the diff introduces no boundary meeting the floor —
that condition holds by measurement. **No boundary was re-run and none was accepted on a builder's
record, because none exists.** Worker 3's source carve-out was not exercised: no production file was
mutated at any point in this pass.

**Hot-path budget.** Not owed. The plan declares `none`, and correctly — nothing in this diff runs
per request, per resolver, per row, per connection, or per outbound message.

**Floor verification.** Not owed. The plan declares scope `none`, and correctly — the diff touches
no Django / Strawberry / channels integration seam.

**Coverage.** No `pytest` run, no `--cov*` flag in any form, at any point in this pass.

### Notes for Worker 1 (spec reconciliation)

**This is the complete, current R2 handoff and it supersedes the pass-5 list.** R2 is the next item
and the same role, so nothing lives only in a closed section. Items 1-9, 11-15 and 17-19 are
re-issued with every reference re-checked against the files on disk this spawn; item 10 is replaced;
item 16 stays discharged; item 20 is re-issued **widened**. Neither the spec nor the rationale
changed line numbering since pass 5 except the rationale, which grew 806 -> 815 lines.

1. **`D5` leaves the spec with no extension-lifecycle statement at all.** R1 deleted the falsified
   spike and its recommendation rather than replacing them. The open question is whether the spec
   states the current construction form or points at `spec-029` Decision 3, which owns it. The build
   plan's anti-absorption rule, `docs/README.md` #"The optimizer is a module-level singleton wrapped
   in a factory", and `docs/GLOSSARY.md` all argue for the pointer; I agree, and re-confirmed
   `docs/README.md` this spawn. **What R2 must not do is transplant the corrected recommendation
   into spec-004** — that is the `**The scope trap specific to this spec.**` failure.
2. **`D24` is already discharged** by the `## Priority and ordering` deletion — all eight slices now
   sit under `## Proposed improvements` in heading order. Verify, do not perform.
3. **`### B6` `**Public API.**` says "classmethod"; HEAD ships a `@staticmethod`.** Kept verbatim on
   purpose; a one-word correction and R2's. Spec `:108`.
4. **`## Implementation checklist` bullet 2 is the last in-spec trace of the cache-lifetime spike**
   (spec `:174`, `- [x] B1 cache-lifetime spike (10-min investigation, precedes B1
   implementation)`). A checklist is contract scaffolding so R1 left it, but its parenthetical is a
   sequencing claim about work eleven versions shipped and the section it pointed at is gone. R2's
   call whether it is trimmed.
5. **`## References`' third paragraph is still dangling** (`D27`, spec `:169`): it cites a "skip
   Strawberry conversion" optimization "noted in B1's implementation" that `### B1` never noted, at
   HEAD or now. R1 neither created nor repaired it. The thing that did land is the
   deferred-conversion thunk, a different mechanism.
6. **`### B7`'s "No `_meta.get_fields()` call ever appears in the request path" was cut, but its
   contradiction survives elsewhere.** The contradicting sentence — `**Walker needs registry
   lookup.**`'s unregistered-model fallback at spec `:131` — is still there and still true, and
   `D23` records it as a documented dual contract. Nothing is owed; **R2 should simply not "restore"
   the deleted claim.**
7. **`D25` and `D28` are discharged and the move report's own handoff does not say so.** Both lived
   inside `## Priority and ordering` and went with it. The rationale's `### The former `## Priority
   and ordering`` entry records both correctly, so the durable record is complete — but an R2
   working from the original list will hunt two sentences that no longer exist.
8. **`D6` is narrower than the drift table anticipated, and here is exactly how much.** The policy
   half is stated in the spec (`**Cache storage.**`, spec `:23`) and is off R2's list. What remains
   is precisely three things, none of which appears anywhere in the spec — re-verified this spawn by
   absence grep, which returns only `:23` and the pre-existing `:27`: the **bound** (`256`), the
   **storage mechanism** (`OrderedDict` + `move_to_end`, and the `suppress(KeyError)` guard against
   the concurrent-eviction race), and the **batch size** (a quarter rather than one entry).
   `**Cache storage.**`'s plural "entries" is generic and neither states nor forecloses the
   batching.
9. **Decided — do not re-open.** The escalated contract-level question (`## Problem statement`'s
   surviving competitive positioning) was ruled on by the maintainer. The canonical record — the
   decision, its reasoning, and the rejected alternatives each with the reason it lost — is
   `docs/builder/build-004-optimizer_beyond-0_0_3.md` `## Maintainer decision — the surviving
   competitive positioning in `## Problem statement``. **Read it there; it is not restated here and
   it is not R2's to re-derive.** Its operative consequences for R2: the sentence at spec `:7`
   **stays byte-for-byte**; the keep is recorded in the rationale at `:171`-`:180` and `:194`-`:197`;
   and `## Problem statement`'s "eight improvements that the existing libraries do not ship" framing
   is a **separate** claim, is `D1`'s, and is still R2's.
10. **The Low above is R1's, not R2's**, and it is the only thing holding this item at
    `revision-needed`. It is one clause in the rationale's `## Standing notes` closing paragraph
    (`:771`-`:774`); no spec edit is owed and the spec must stay byte-identical. **The pass-5 Low is
    closed** — the survival criterion is corrected at all four writable sites.
11. **R2's `_optimizer_field_map` worklist is the rationale's bullet (`:694`-`:701`), not the build
    plan's `D22` row.** Re-derived this spawn: **6 occurrences across 5 sites in 3 sections** — spec
    `:84` (B4 `**Walker needs registry lookup.**`), `:112` (B6's exposed-fields paragraph), `:129`
    (B7 `**Mechanism.**`, **twice**), `:131` (B7 `**Walker needs registry lookup.**`), `:135` (B7
    `**Test surface.**`). `D22` counts four sites and omits `**Test surface.**`. Two riders on the
    same sweep: `:112` is the sole carrier of **both** `metafields` and `metaexclude`, so it must be
    rewritten with the links re-sited rather than dropped; and `:84` additionally still says the
    walker reads `_optimizer_hints` off the type class, which is `D16`'s retired mirror in the same
    sentence.
12. **`### B8`'s surviving opening paragraph is on an R2-facing list — here is where.** The tenth
    bullet of the rationale's `## Standing notes` `### The status claims were left standing`
    (`:714`-`:719`). It states the package's own **pre-B8** behaviour in the present tense ("the
    optimizer blindly stacks another `.select_related("category")` on top", spec `:141`), and
    shipping B8 is what falsified it. The build plan's drift table carries **no** row for it: its
    three B8 rows (`D24`, `D25`, `D26`) name the document structure, the deleted ordering section,
    and the cut fence. **Work this item from the rationale bullet, not from the drift table.**
13. **The link-target disk check has an expiry and mine is the current reading, not the last word.**
    30/30 resolve at `346d6731`. **R2 and R3 re-run it themselves rather than quoting this one**,
    and re-run `import_spec_terms --check` after any further concurrent DB write.
14. **Baseline state for Worker 0 to append** (reported, never reverted): `git status --short` was
    the same four cycle paths at the start and end of this pass — no churn at all, for the sixth
    consecutive pass. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`,
    `examples/fakeshop/db.sqlite3`, and `django_strawberry_framework/optimizer/predicates.py` are
    all clean at `346d6731` — but R2 re-derives that rather than inheriting it.
15. **A standing hazard this cycle has now demonstrated seven times, worth carrying into R2's own
    writing.** Counts or universals wrong or unreproducible: `_optimizer_field_map` "five mentions";
    the survival summary; "two B8 rows"; the shingle triple falsified by a later edit; "42" quoted
    runs; "the only place in the whole corpus"; and now "One clause … in the spec", which is three.
    R2 rewrites more prose than R1 did, in the same durable files. **State the unit beside any
    count, state the population beside any universal, state the method beside any measurement, and
    re-measure after the last edit rather than while making it** — and prefer the durable file's own
    solution, which was to name the sites and let them be counted rather than to assert a number.
16. **Discharged: the build plan's `D17` row is corrected and agrees with the rationale.** Verified
    at source (`types/base.py`: `_validate_meta` defined 1073 / called 535,
    `_validate_optimizer_hints` defined 1232 / called 537). Nothing further is owed. The sentence it
    governs (spec `:86`) is still the **sole carrier of the `configurationerror` anchor**, so it
    remains the anchor-bearing rewrite with the least margin for a wrong premise. One phrasing worth
    tightening but not filing: the bullet's "it only normalizes the hints mapping" is true of
    `_validate_meta`'s *hints* handling and loose about the function, whose docstring lists eight
    validation steps; the plan's row states the same fact without the word "only".
17. **A small factual imprecision in the rationale, an R2 touch-up rather than a finding.** The
    `### B1` entry calls it "the locked `strawberry-graphql 0.316.0`". `0.316.0` is the **declared
    floor** (`pyproject.toml` #"strawberry-graphql>=0.316.0"); `uv.lock` resolves 0.323.2.
    `spec-029` uses the same word, so spec-004's rationale inherited the phrasing from the spec that
    owns the correction. If R2 tightens it, it should decide for both rather than leave the two
    documents disagreeing.
18. **Do not "fix" the candidates prior passes opened and left, and do not re-derive them.**
    `## How to read this file` `:51`-`:52` ("headings that no longer exist in the spec at all") and
    the `**The win.**` entry's `:120` ("The `**The win.**` label no longer appears in the spec") are
    both true as written — the single `grep 'The win\.'` hit at spec `:3` is a mention inside a code
    span, not a paragraph label. Also on that list: `## How to read this file` `:17`-`:18` ("the
    whole section is contract"), a statement in this file's deliberation/contract vocabulary and not
    a correctness claim; `### B8`'s maintain-by-hand retracted item, whose entry body already
    protects the surviving requirement; the `*Alternative rejected — keep them and cut only the
    competitor's name.*` block (`:142`); the `## Standing notes` opener's "competitive argument,
    proposal code, build order" class list (`:682`); and `*Why they went.*`'s "for seven of the
    eight" (`:135`), whose supporting clause is overstated for B1 but whose exception is documented
    under a bold lead in the same entry.
19. **The block label diverges from all three sibling rationales, deliberately.** `**Claims the spec
    may no longer make.**` here (10 blocks), against **47** non-modal labels in the spec-001 (17),
    spec-002 (8) and spec-003 (22) rationales and `docs/SPECS/spec-002-optimizer-0_0_2.md`'s
    companion pointer — 48 counterexamples, re-derived this spawn. The divergence is correct: those
    three ran an R2 spec-reconciliation pass before their labels were finalized; spec-004's has not.
    **R2 must not harmonize spec-004's label back to the sibling form**, and if R2 performs the
    retractions it should decide deliberately whether the label then earns the factual spelling —
    the file's own definition at `## How to read this file` is what makes either spelling readable,
    so that definition is the thing to keep in step, not the label alone.
20. **Widened — the mischaracterization of the `**The win.**` class is at three spec sites, not
    one.** All three are text this cycle wrote, all three describe moved material as an argument
    against `strawberry-graphql-django`, and B5's and B7's `**The win.**` paragraphs name no
    competitor at all:
    - spec `:3`, the companion-pointer paragraph — "the per-slice `**The win.**` arguments *against*
      `strawberry-graphql-django`";
    - spec `:100`, `### B5`'s pointer — "The competitive argument for this slice, the ordering
      argument for landing it before its dependents, …";
    - spec `:133`, `### B7`'s pointer — "The competitive argument for this slice, its relationship
      to B1's plan cache, …".
    The other five per-slice pointers (`:29`, `:47`, `:63`, `:90`, `:121`) are accurate, and B8's
    (`:151`) correctly carries no such clause because B8's win paragraph stayed. The build plan's
    drift table carries **no** row for any of the three, so the rationale's `## Standing notes`
    closing paragraph and this list are the whole of the record — which is why the Low above asks
    that paragraph to name all three. The corrected characterization R2 should match is the
    rationale's `**The win.**` entry and its framing sentence.

### Review outcome

`revision-needed`.

One Low, neither addressed nor rejected, and `worker-3.md`'s acceptance gate requires every High,
Medium, and Low finding to be addressed or intentionally rejected with a recorded reason. The
escalation carve-out does not reach it — that is for Medium-or-higher findings needing spec context,
and this needs neither. It is one clause in the rationale; no spec edit is owed by it, and the spec
must stay byte-identical.

**I want to be plain about proportionality, because this is the sixth review of a docs-only diff.**
Everything the prompt sent me to grade came back sound and I filed none of it. The three-of-eight
count reproduces and its added `O2` observation is correct. The integration line is the right line
and both of its calls hold — fixes 3 and 4 belong in scope, all three left candidates are correctly
left, and the heading edit is safe by measurement. The fifth site is real, correctly routed to a
note a sweeper is already sent to, and correctly left rather than fixed under a freeze five reviews
depend on. The pass-4 correction is right and its negative check survives a wider instrument than
the one that produced it. The `52 -> 55` delta is fully explained: removing the one new paragraph
returns it to exactly 52. Where what remained was wording I would have chosen differently — the
overstated "every factual claim inside them is restated in `**Mechanism.**`", the loose "it only
normalizes the hints mapping" — I have said so in `What looks solid` and in the handoff and filed
neither.

**What holds the item open is a defect a reader acts on, in the one class this cycle never opened.**
Five passes swept the rationale for false assertions of *absence*. Nobody tested the spec's *added*
text against what actually moved — and seven of the 28 lines this cycle added to the spec are one
sentence, "The competitive argument for this slice", written once per slice. Two of the seven point
at paragraphs the same pass had just established name no competitor. Pass 5 came within a line of
it: its own review section notes that B8's pointer "correctly omits" the clause, and never asked the
inverse question of B5's and B7's. Since the spec is frozen, the whole remedy for those sites is
that the durable record enumerates them, and it says "One clause". That is a one-clause fix, it adds
no tally, and without it R2 corrects one of three and leaves the spec and its companion contradicting
each other at two addresses this cycle wrote.

Per the build plan's `### Deviation 2` corollary this routes to **Worker 1**, not Worker 2. Worker 1
applies the correction, sets `Status: planned` again, and returns the artifact here.

### Working-tree churn observed during this review — reported, not reverted

**None.** `git status --short` was the same four entries at the start and at the end of the pass:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
```

`docs/builder/worker-memory/worker-3.md` was consolidated and appended to this pass and correctly
does not appear above: `docs/builder/worker-memory/` is gitignored. `HEAD` is
**`346d67312599c0536980969caa39085ab3885ae8`**, re-derived this spawn, and it did not sweep this
cycle's work: `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns
**`20a9752f`** and the three artifacts are still untracked. That is the standing hazard check, done
with `git log` rather than `git status` alone. No stray untracked file appeared, and nothing was
reverted. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, and
`examples/fakeshop/db.sqlite3` are all clean.

---

## Build report (Worker 1, apply-changes pass 6)

Per the build plan's `### Deviation 2` corollary, an R1 `revision-needed` routes to Worker 1: the
same two rules that make Worker 1 the only role that may perform the move make it the only role
that may fix it. `Status:` is `planned` on return, which Worker 0 reads as "dispatch Worker 3" for
a pass-7 review. Every prior entry — all six of Worker 3's review sections included — is untouched.

**One Low, fixed; nothing rejected.** The fix is in **both** files, and the spec half is a scope
call this pass had to make first. It is argued below rather than asserted, because it is the only
pass in six to reopen the spec and the finding itself did not ask for it.

### The scope call — the spec was reopened, and only for text this cycle wrote

**Decision: R1 fixes all three sites in the spec.** The finding's own recommended change was to
widen the durable note and R2 handoff item 20 to name all three and leave the spec. That
recommendation is correct *under a freeze*, and the freeze is the thing this pass had to test
rather than inherit.

**What the freeze is for.** Five passes ran under "the spec is NOT writable" and it held
byte-identical throughout — 216 lines / 26,480 bytes, `git diff --stat` 28 insertions / 171
deletions. Its purpose is to stop R1 performing R2's spec-versus-HEAD reconciliation: the 28-row
drift table is R2's input, and an R1 that starts correcting present-tense claims about the package
has taken the next item's work. Nothing about that purpose reaches a sentence R1 itself wrote about
R1's own move.

**Four things establish that these three sentences are R1's own defect, and each was measured:**

1. **They are this cycle's text, not spec contract.** All three are among the 28 added lines —
   `git diff -U0 | grep '^+'` shows the companion paragraph, `### B5`'s pointer, and `### B7`'s
   pointer as insertions. Nothing at HEAD carries any of them.
2. **No drift row covers them, and none could.** `grep -n '^| D' <plan>` piped through
   `grep -i 'companion\|pointer\|competitive argument'` returns **zero**. The table was written at
   pre-flight against the pre-move spec; the sentences did not exist yet. Worker 3 verified the same
   absence independently at pass 6.
3. **They are not status claims about the package.** Every survival the R1/R2 boundary protects is a
   present-tense claim about what HEAD does (`## Standing notes` enumerates them). These three make
   no claim about the package at all: they describe **what this pass moved**, which only this pass
   can be wrong about and only this pass authored.
4. **The maintainer already ruled on the identical question.** The build plan's
   `## Maintainer decision` closes with *"This is **R1's** work, not R2's — the file is R1's
   deliverable and the defect is in R1's own output."* That was said of a defect in the rationale;
   the reasoning is about **whose output carries the defect**, not about which file it sits in, and
   these three sentences are as much R1's output as the rationale is.

**What the alternative would have cost.** Leaving a sentence R1 wrote factually wrong, with a
handoff item as the remedy, is the defer-the-real-fix sequencing `AGENTS.md` rule 5 forbids — and
the remedy is weaker than it looks: it ships a spec whose companion pointers misdescribe what they
point at, and rests entirely on R2 reading a durable note and correcting three sentences it did not
write. The cycle has now filed the "durable enumeration undercounts the sites" defect four times
(`_optimizer_field_map`, B8's paragraph, "One clause", and this one). A fourth enumeration is a
fourth thing to keep in step; a correct sentence is not.

**What the freeze still governs, and it is untouched.** The edit corrects the pass's own
characterization of what moved and nothing else. No contract changed, no drift row was discharged,
no present-tense status claim was reconciled, no glossary link moved, and the maintainer-ruled
`## Problem statement` sentence is **byte-identical to HEAD** — verified by `diff` of that line
against the read-only HEAD copy, not by byte count. Everything else in Worker 3's 20-item handoff is
still R2's, item 9's settled ruling included.

**The structural check five reviews rested on is not retired, it is re-baselined**, and the delta is
accounted for to the byte below. `git diff --stat` is **unchanged at 28 insertions / 171
deletions**, which is the same independent evidence it always was: all three edits are in-line
replacements of lines the diff already counted.

### The three spec edits, and the count they rest on

**Re-derived before anything was written**, against the read-only HEAD copy (`git show HEAD:<spec>`
into a scratchpad outside the repository; **33,928 bytes / 359 lines**). The eight `**The win.**`
paragraphs at HEAD `:17`, `:50`, `:82`, `:115`, `:158`, `:181`, `:239`, `:271` were read in full,
not grepped for a token list: B1, B2, B3, B4 and B6 name a competitor; **B5, B7 and B8 name none** —
B7's names `O2`, this package's own spec-002 walker, which is why a token grep is the wrong
instrument here. Three of eight, reproducing Worker 3's derivation and my own pass-5 one.

`grep -n 'competitive argument' <spec>` returned **seven** lines — `:29`, `:47`, `:63`, `:90`,
`:100`, `:121`, `:133` — one per slice except B8, whose pointer correctly carries no such clause
because B8's paragraph stayed. Of the seven, B5's (`:100`) and B7's (`:133`) name material that
names no competitor, and neither pointer's other clauses absorb it: B5's "ordering argument" is the
cut sequencing clauses and B7's "relationship to B1's plan cache" is the cut derivation, both listed
separately in the same sentence.

| # | Site | Was | Now |
|---|---|---|---|
| 1 | `:3`, the companion-pointer paragraph | "the per-slice `**The win.**` arguments against `strawberry-graphql-django`" | "the per-slice `**The win.**` arguments" — the label already names the class; the false qualifier is simply gone |
| 2 | `:100`, `### B5`'s pointer | "The competitive argument for this slice" | "The opening argument for this slice" |
| 3 | `:133`, `### B7`'s pointer | "The competitive argument for this slice" | "The opening argument for this slice" |

**Why the other five pointers were left, and why that asymmetry is the accurate state.** Their
paragraphs *do* name a competitor, so "the competitive argument for this slice" is true of each.
Levelling all seven to one neutral phrase would edit five accurate sentences to buy uniformity, and
would erase real information: the difference between the two spellings now tracks a real difference
between the paragraphs. "Opening argument" is the corpus's own corrected vocabulary — the rationale's
entry heading reads "a slice-opening argument, not a contract" and its opening paragraph reads "the
argument each slice opened with", both set by pass 5.

**Every other added line was re-checked against what actually moved**, since this pass owns the rule
that no sentence may misdescribe the move. The five accurate pointers' remaining clauses, B8's
pointer (`:151`), and the re-pointed `## Problem statement` clause (`:9`) each name material that
was in fact cut — the spike, the fences, approach (b), the `strict=True` kwarg, the untyped shapes,
the "complementary to B1" derivation, the sequencing clauses, the ordering section. No further
mischaracterization exists.

### The rationale edit — the durable note that said "One clause"

`## Standing notes` `### The `**The win.**` cut is the one an over-cut review should test first`
closed with "One clause about this class is still inaccurate, and it is in the spec rather than
here… The reconciliation item owns that clause." After the spec edit that sentence is false three
ways over — the count, the tense, and the owner — so it was replaced rather than widened.

The replacement records that the characterization reached the spec's own pointer text, that it was
corrected there in the same pass **because a pointer that misdescribes what it points at is this
pass's own defect**, and names the sites: the companion paragraph, and `### B5`'s and `### B7`'s
per-slice pointers. It closes with the one thing a future reader needs and cannot re-derive — that
the two-spelling asymmetry is deliberate and a harmonizing sweep must not level it back. That is the
same shape as handoff item 19's warning about the block label, and it is there for the same reason.

**No tally was added**, for the sixth consecutive pass. The sites are named; the reader counts them.

### The integration sweep — three candidates opened, none edited

The prompt makes the integration mine. Each was resolved against the files.

1. **`## Standing notes`' opener** (`:682`) — "This pass cut the *deliberative* layer: competitive
   argument, proposal code, build order…". Names classes acted on, quantifies over nothing, and
   competitive argument **was** cut. The maintainer pass, pass 3, pass 4 and pass 5 all opened it and
   left it on that distinction, and Worker 3's handoff item 18 says not to "fix" it. Left again.
2. **The `*Alternative rejected — keep them and cut only the competitor's name.*` block** (`:142`)
   and the maintainer's `**Claims the spec no longer makes as any slice's own argument.**` block
   (`:171`). The first records an option as it was formulated; the second is the ruling's own text
   and turns on `## Problem statement` `:7`, which this pass did not touch. Both unaffected by the
   spec edit. Left.
3. **`:3`'s surviving list of what the rationale carries** — it names "the per-slice `**The win.**`
   arguments" among the things the rationale holds, and two of the eight paragraphs did survive in
   the spec (B8's whole, B6's first sentence). Opened and **left**: the sentence says what the
   rationale *covers*, and the entry does cover all eight including why two stayed; `## How to read
   this file` already states that a cut item can leave a sentence standing and sends a reader who
   needs the disposition to the entry. Recorded so pass 7 does not re-derive it.

The full `grep -ni 'competit'` over the rationale now returns six lines across five sites: `:142`
and `:171` (left, above), `:149` and `:682` (corrected or left at pass 5), and the two lines of the
new paragraph. Every one lands on the right side of the pass-5 line — fix where the text quantifies
over the eight, leave where it names a class of material.

### Files touched

- `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` — 3 edits, all in-line replacements within lines
  this cycle already added. **216 -> 216 lines, 26,480 -> 26,436 bytes (-44).**
- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — 1 edit, the standing note's
  closing paragraph. 815 -> 819 lines, 58,432 -> 58,828 bytes (+396).
- `docs/builder/bld-004-r1-rationale_move.md` — this section appended; `Status:` set to `planned`.
- `docs/builder/worker-memory/worker-1.md` — entry appended (gitignored, so absent from
  `git status`).

**The -44 accounted for line by line, so a changed count cannot read as drift:**

| site | change | bytes |
|---|---|---|
| `:3` | drop `_against `strawberry-graphql-django`_ (1 space + 7 + 1 space + 27 with its code-span backticks) | **-36** |
| `:100` | `competitive` (11) -> `opening` (7) | **-4** |
| `:133` | `competitive` (11) -> `opening` (7) | **-4** |
| | | **-44 exactly** |

26,480 - 44 = **26,436**, which is what `wc -c` returns. No other byte moved.

**No count anywhere in either file changed**, so nothing elsewhere had to be kept in step. In the
rationale, `## Provenance of this record`'s five label bullets — the `**Moved**` measurement
included — and every other `## Standing notes` entry are byte-unchanged.

### Validation run — every result quoted verbatim

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
  -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**.
  Character-identical to the build plan's pre-flight baseline. **This is the check that mattered
  most this pass**, because it is the first pass in five to edit the spec.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md docs/builder/bld-004-r1-rationale_move.md`
  -> **exit 0** on all three files.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have
  glossary links.` **exit 0**. **Read-only form only**; the writing form was never invoked.
- **Per-anchor 10-anchor constraint, re-derived rather than read off the checker's exit code.**
  `grep -o "\[glossary-<anchor>\]" | wc -l` -> **2 for every one of the ten** (1 body use + 1
  definition): `configurationerror`, `djangooptimizerextension`, `djangotype`, `fk-id-elision`,
  `metaexclude`, `metafields`, `metaoptimizer-hints`, `only-projection`, `optimizerhint`,
  `queryset-diffing`. **None of the three edited sentences carried a glossary link**, which is why
  the risk was low — but it was run, not assumed. **The terms CSV was not opened**: it is absent
  from `git status --short`.
- **Every link definition re-resolved on disk this spawn, not quoted.** Each target resolved from
  its own source file's directory and existence-tested: spec **11 definitions / 11 distinct uses**,
  rationale **19 / 19**, **0 undefined references, 0 unused definitions, 0 of 30 targets missing.**
  No definition was added or removed by any edit. **R2 and R3 re-run this rather than quoting it.**
- **Byte / line count, before and after.**

| | lines | bytes |
|---|---|---|
| spec at HEAD (pre-move) | 359 | 33,928 |
| spec **before this pass** (passes 2-6 baseline) | 216 | 26,480 |
| spec **now** | **216** | **26,436** (-44, accounted above) |
| net move + revisions | **-143** | **-7,492 (-22.1%)** |
| rationale before this pass | 815 | 58,432 |
| rationale **now** | **819** | **58,828** (+396) |

- `git diff --stat -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **28 insertions / 171
  deletions**, the hunk shape Worker 3 recorded at all six reviews — independent evidence that every
  edit is an in-line replacement of a line the diff already counted, and that no line was added or
  removed. `git show HEAD:<spec> | wc -l -c` -> **359 / 33,928**: the baseline the move was measured
  against has not moved.
- **The added-line population is still 28**, re-derived: `grep -c '^+[^+]'` -> **24** non-blank,
  `grep -c '^+$'` -> **4** blank.
- **The maintainer-ruled sentence is byte-identical to HEAD**, and I proved it by `diff` of the line
  rather than by the file's byte count: the `## Problem statement` first paragraph at HEAD `:5` and
  at the current spec `:7` compare **identical**. The decision's first clause holds.
- **The competitor is still named in the spec** where the ruling and house style require it: the H1
  ("Beyond strawberry-graphql-django"), `## Problem statement` `:7`, and `## References` `:165`.
  The `:3` edit removed a false characterization, not the comparison.
- In-page anchors: the repo's own `scripts/check_spec_glossary.py::github_anchor` over the spec's
  **15** headings -> **15 unique slugs, 0 duplicates**; `#problem-statement` and
  `#proposed-improvements` both resolve. No heading was touched and no in-page anchor was added.
- `grep -c '^```'` -> spec **0**, rationale **0**. No fence introduced.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files -> **no match** (exit 1). Rule 27 holds.
- `grep -nP '\]\((?!#|https?:)'` over both files -> **no match** (exit 1). Reference-style preserved.
- `grep -niE 'as of (review )?round|amendment|retract|inverted|a later strawberry|no longer|used to |formerly|previously|has since'`
  over the spec -> **one** line, `:3`, whose only hits are "the former `## Priority and ordering`
  section" and "may no longer make" — rule-1 pointer vocabulary, unchanged by this pass. The spec
  still narrates no history.
- `grep -c "LINK DEFINITIONS"` over the rationale -> **1**. The pass-3 method clause still does not
  embed the marker it tells the reader to split on.
- `git diff --stat -- django_strawberry_framework/ tests/ examples/` -> **empty**. No source, test,
  or example file touched; no `pytest`, no `ruff` (no `.py` file changed), no coverage-shaped flag
  in any form.
- No `git stash`, `checkout`, `restore`, `worktree`, `commit`, or branch operation at any point. The
  read-only HEAD reference was `git show HEAD:docs/SPECS/spec-004-optimizer_beyond-0_0_3.md >
  <scratchpad outside the repo>/spec-004-HEAD.md`.

### Duplication: the overlap figure returned to 52, and that is the fix proving itself

Measured under the normalization the rationale itself states (drop each file's bottom
link-definition block, fold every non-alphanumeric run to whitespace, lowercase, distinct 8-word
shingles):

| measure | before this pass | after |
|---|---|---|
| rationale total shingles | 9,201 | 9,267 (+66) |
| left-the-spec shingles present in the rationale | 161 | **161 (unchanged)** |
| rationale x post-move-spec overlap | 55 | **52 (-3)** |

**The -3 is the +3 pass 5 disclosed, and it closed itself.** That delta was the standing note
quoting the spec's live companion-pointer clause — "the per-slice `**The win.**` arguments *against*
`strawberry-graphql-django`", ten normalized words and therefore three shingles. Correcting the spec
sentence removed the thing being quoted, so the quotation went with the paragraph that carried it
and the figure is back at the **52** four earlier passes reported. Nothing was trimmed to hold a
metric; the metric moved because the defect it was tracking is gone.

**The `**Moved**` bullet's durable measurement did not move, re-measured after the last edit:
192 of the pre-move spec's 4,934 shingles, in 41 contiguous runs, longest 20 shingles (27 words),
median 3.** Its two inputs are the frozen 33,928-byte blob and this file; the spec edit cannot reach
it by construction, and the rationale edit added no HEAD wording. **Third consecutive pass in which
the re-keying holds under editing, and the first in which the spec itself moved underneath it —
which is precisely the falsification the old triple could not survive.**

### Notes for Worker 3 (pass 7)

- **The judgement to audit is the scope call, not the wording.** The finding asked for a wider note
  and no spec edit; I reopened the spec. The argument is under `### The scope call` and it rests on
  four measurable claims: the three sentences are among the 28 added lines, no drift row covers
  them, they make no claim about the package, and the maintainer's own ruling puts a defect in R1's
  output on R1. **Re-derive all four**; if any fails, the edit is out of scope and the remedy is the
  finding's original one.
- **The place to look for an over-reach is the five pointers I did NOT edit.** Leaving them saying
  "the competitive argument" while B5's and B7's say "the opening argument" is a deliberate
  asymmetry, argued above and now recorded in the durable file. If the call is judged wrong the fix
  is one word in five sentences, not a revert of the three.
- **The delta is the thing to re-derive rather than read.** -44 bytes, itemized to the character in
  `### Files touched`; 216 lines unchanged; `git diff --stat` unchanged at 28/171. And check the
  maintainer-ruled sentence by `diff` against HEAD, not by the file's byte count — equal counts are
  not identity, and this pass is the first in which the count is not equal.
- **`52` is not a regression, it is the +3 unwinding.** Confirm by locating the quotation pass 5
  added and finding it gone with its paragraph.
- **Two claims worth re-deriving rather than reading:** the three-of-eight count (read the eight
  HEAD `**The win.**` lines in full — B7's names `O2`, this package's own walker, which a token grep
  will not catch) and the 192 / 4,934 / 41-run measurement, which this pass re-ran after its last
  edit and which must still reproduce now that the spec has moved.
- Nothing from this pass was staged for later without being written down. No temp test, no shadow
  file, no `docs/builder/temp-tests/` directory.

**Failability proofs.** None; this pass introduced no new boundary. `git diff --
django_strawberry_framework/` is empty, so there is no boundary, guard, gate, or rejection path to
prove.

**Hot-path budget.** Not applicable; the plan declares `none`, and correctly — nothing in this diff
runs per request, per resolver, per row, per connection, or per outbound message.

**Floor verification.** Not applicable; the plan declares floor-verification scope `none`, and
correctly — the diff touches no Django / Strawberry / channels integration seam.

**Coverage.** No `pytest` run, no `--cov*` flag in any form, at any point in this pass.

### The R2 handoff — item 20 is discharged

Worker 3's pass-6 `### Notes for Worker 1 (spec reconciliation)` is the complete current list and is
not restated here. Two amendments, and nothing else in it was acted on — item 9's settled maintainer
ruling and item 19's deliberate divergence included.

- **Item 10 is closed.** The Low is fixed, in the rationale and in the spec.
- **Item 20 is DISCHARGED, not widened.** All three sites — spec `:3`, `:100`, `:133` — are
  corrected in this pass. R2 owes nothing on them. What R2 inherits instead is one standing
  instruction, now recorded in the rationale's `## Standing notes` rather than only here: **the
  two-spelling asymmetry across the seven per-slice pointers is deliberate** — `### B5`'s and
  `### B7`'s read "the opening argument for this slice" because their `**The win.**` paragraphs name
  no competitor, and the rest read "the competitive argument" because theirs do. A harmonizing sweep
  must not level it. This joins item 19 as the second deliberate divergence R2 must not reverse.

### Spec changes made (Worker 1 only)

Cited against the post-edit spec. All three are in-line replacements; no line was added or removed,
and `git diff --stat` is unchanged at 28 insertions / 171 deletions.

| Spec location | Change | Reason |
|---|---|---|
| `:3` | "the per-slice `**The win.**` arguments against `strawberry-graphql-django`" -> "the per-slice `**The win.**` arguments" | Worker 3 pass-6 Low. B5's and B7's paragraphs moved and name no competitor, so the qualifier is false of the class it quantifies over. Text this cycle wrote; no drift row covers it. |
| `:100` | `### B5`'s pointer: "The competitive argument for this slice" -> "The opening argument for this slice" | Same finding. B5's `**The win.**` (HEAD `:158`) names no competitor; the pointer's other clauses name the cut sequencing clauses and the fence, so this clause can only denote the paragraph. |
| `:133` | `### B7`'s pointer: "The competitive argument for this slice" -> "The opening argument for this slice" | Same finding. B7's (HEAD `:239`) names `O2`, this package's own spec-002 walker. |

Nothing else in the spec was touched. No contract changed, no drift row was discharged, no
present-tense status claim was reconciled, and the maintainer-ruled `## Problem statement` sentence
is byte-identical to HEAD.

**Spec status-line re-verification** (`worker-1.md` `## Spec status-line re-verification`, re-run
this spawn as every Worker 1 spawn must): spec-004 carries **no** `Status:` / owner / target-release
/ predecessor header block — lines 1-5 are the title, the companion-pointer paragraph, and
`## Problem statement`. Nothing in them is a status line this build has falsified, so no header edit
was owed. The `:3` edit is to the pointer paragraph's content — a characterization of moved
material, not a status line — and after it the paragraph describes the move accurately.

### Working-tree churn observed during this pass — reported, not reverted

**None.** `git status --short` was the same four entries at the start and at the end of the pass,
for the seventh consecutive pass:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
```

`docs/builder/worker-memory/worker-1.md` was appended to this pass and correctly does not appear
above: `.gitignore:188` ignores `docs/builder/worker-memory/`, confirmed this spawn with
`git check-ignore -v`.

`HEAD` is **`346d67312599c0536980969caa39085ab3885ae8`**, re-derived this spawn rather than quoted,
and it did **not** sweep this cycle's work: `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-
0_0_3.md` still returns **`20a9752f`**, and the rationale, this artifact, and the build plan are all
still untracked. That is the standing hazard check, done with `git log` rather than `git status`
alone. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, and
`examples/fakeshop/db.sqlite3` are all clean — but pass 7 re-derives that rather than inheriting
this reading.

---

## Review (Worker 3, pass 7)

Read in order, as the prompt directs: `docs/builder/worker-3.md` (full), `AGENTS.md`, `START.md`,
`docs/builder/BUILD.md` (full), `docs/builder/ARTIFACT.md`, `docs/README.md`,
`examples/fakeshop/test_query/README.md`, `docs/builder/build-004-optimizer_beyond-0_0_3.md` (full,
including its settled `## Maintainer decision`, not re-opened), this artifact's plan, move report and
every review / apply-changes section in order, `worker-1.md` `### Performing the rationale move`, the
spec, the rationale, and the pristine HEAD spec obtained read-only as
`git show HEAD:docs/SPECS/spec-004-optimizer_beyond-0_0_3.md > <scratchpad outside the repo>/spec-004-HEAD.md`.
No `git stash` / `checkout` / `restore` / `worktree` at any point, and no prior entry was edited.

`HEAD` re-derived this spawn rather than quoted: **`346d67312599c0536980969caa39085ab3885ae8`**; the
HEAD spec blob is **359 lines / 33,928 bytes**. `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-
0_0_3.md` still returns **`20a9752f`** and the three artifacts are still untracked, so no concurrent
commit has swept this cycle's work. `git status --short` is the same four cycle paths and nothing
else, for the eighth consecutive pass.

**Nothing below is quoted from any build report.** Every figure was re-derived from the files on disk
this spawn, on my own implementations of the stated methods.

### High:

None.

### Medium:

None.

### Low:

None.

### The scope call — all four claims re-derived, and a fifth ground the pass did not cite

The pass reopened the spec after five frozen passes. The finding it was answering asked for a wider
durable note and **no** spec edit, so the scope call is the thing to audit. All four supporting
claims were re-derived independently; each holds.

**1. All three sites are among the 28 added lines.** `git diff -U0 -- <spec> | grep '^+'` returns 28
lines (24 non-blank + 4 blank, re-counted). I numbered them and located each site: added line **1**
is the companion-pointer paragraph (`:3`), added line **19** is `### B5`'s pointer (`:100`), added
line **24** is `### B7`'s pointer (`:133`). Nothing at HEAD carries any of the three — they cannot,
since the pointers are the move's own output. **Reproduces exactly.**

**2. No drift row covers them, and none could.** `grep -c '^| D' <plan>` -> **28** rows;
`grep -n '^| D' <plan> | grep -ic 'companion\|pointer\|competitive argument'` -> **0**. The table was
written at pre-flight against the pre-move spec, in which these three sentences did not exist. This
is the third independent derivation of that absence (pass 5, pass 6, mine). **Reproduces exactly.**

**3. They make no claim about the package.** The conclusion holds and I confirmed it site by site:
each of the three describes *what this pass moved*, which only this pass authored and only this pass
can be wrong about. One caveat on the supporting clause rather than the conclusion — the pass states
it as a universal ("every survival the freeze protects is a present-tense claim about HEAD"), and the
rationale's own `### The status claims were left standing` list contains at least one member that is
not: `## Implementation checklist` bullet 2's parenthetical "(10-min investigation, precedes B1
implementation)" (spec `:174`) is a **sequencing** claim about the build, not a claim about HEAD, and
it is handoff item 4. The universal over-reaches; the conclusion does not rest on it, because the
discriminating property is **authorship**, which claim 1 establishes by measurement. Recorded in
`### What looks solid` rather than filed, for that reason.

**4. The maintainer already ruled the shape.** The quoted sentence is real and at plan `:210`:
*"This is **R1's** work, not R2's — the file is R1's deliverable and the defect is in R1's own
output."* It is an **analogous** ruling rather than a literally identical one — it was made of a
defect in the rationale, and its stated reason has a file-ownership conjunct that does not transfer
to the spec. What makes the transfer sound is the ruling's own two-sided treatment: it protects a
spec sentence R1 did **not** write (`## Problem statement`, kept byte-for-byte) while ordering the
fix of rationale text R1 **did** write. The axis the ruling actually turns on is authorship, not
file, which is exactly what the pass claims. **Holds.**

**5. The ground the pass did not cite, and it is stronger than claim 4.** `worker-1.md`
`### Performing the rationale move` **rule 1** is *"Every decision keeps a one-line pointer **naming
what was moved and where**."* Writing those pointers is R1's own checklist obligation — it is
`### Dispatched findings checklist` box 2 in this artifact's plan, ticked by this pass. A pointer
that misnames what was moved is a defective discharge of that box, so correcting it completes R1's
deliverable rather than pre-empting R2's, whose box is *"reconcile the spec with HEAD"* and whose
input is the 28-row table. Rule 2 points the same way (*"a false sentence belongs in neither
file"*), as does the custody rule the pass invoked (*"a half-reconciled spec is worse than an
un-updated one"*). **The edit is in scope.**

### Grading the edit itself

**The asymmetry is right, and it is the accurate state rather than an unfinished sweep.** I read all
eight HEAD `**The win.**` paragraphs in full rather than grepping a token list:

| HEAD line | slice | competitor named |
|---|---|---|
| `:17` | B1 | `strawberry-graphql-django` |
| `:50` | B2 | `strawberry-graphql-django` |
| `:82` | B3 | `strawberry-graphql-django`, `django-debug-toolbar` |
| `:115` | B4 | `strawberry-graphql-django`, "DRF teams" |
| `:158` | **B5** | **none** |
| `:181` | B6 | "None of the existing libraries ship this" |
| `:239` | **B7** | **none** (`O2` is this package's own spec-002 walker) |
| `:271` | **B8** | **none** |

Three of eight, reproducing the pass's derivation and pass 6's. The current spec carries **5**
`competitive argument` and **2** `opening argument` pointers — `:29`, `:47`, `:63`, `:90`, `:121`
against `:100`, `:133` — which maps exactly onto the table's five competitor-naming paragraphs and
B5's / B7's. B8's pointer (`:151`) correctly carries no such clause because B8's paragraph stayed.
Levelling all seven would have edited five true sentences and erased a distinction that now tracks a
real property of the material. **The call is right.** The replacement vocabulary is the corpus's own:
the rationale's entry heading (`:117`) reads "a slice-opening argument, not a contract" and its
opening paragraph (`:5`) reads "the argument each slice opened with", so spec and companion now use
one word for one thing.

**It is durably recorded, and the recording is in the right file.** Rationale `:771`-`:777`, the
closing paragraph of `## Standing notes` `### The `**The win.**` cut is the one an over-cut review
should test first`, names the three sites, states which spelling each pointer now carries and why,
and closes: *"The asymmetry is deliberate: a harmonizing sweep must not level it back."* That is in
the **durable** companion, not only in this artifact, which is what the prompt asked me to confirm.
The routing holds too: `## How to read this file` `:64`-`:67` standing-orders *"Read `## Standing
notes` before editing the spec"*, so a spec editor meets the instruction on the path it is already
sent down. I re-read the enumeration in that bullet and it previews three of the section's four
entries — a pre-existing shape, not one this pass created, and the imperative it carries is
unconditional, so no wrong action is available to a reader who follows it. Noted below, not filed.

**The numbers all reproduce, and the changed byte count is fully accounted.**

| measure | re-derived this spawn |
|---|---|
| spec | **216 lines / 26,436 bytes** |
| `git diff --stat` | **28 insertions / 171 deletions** (unchanged) |
| HEAD blob | 359 lines / 33,928 bytes |
| arithmetic | 359 - 171 + 28 = **216** |
| added-line population | 24 non-blank + 4 blank = **28** |
| rationale | 819 lines / 58,828 bytes |

The -44: dropping ` against \`strawberry-graphql-django\`` from `:3` is **36** bytes measured on the
byte string, and `competitive`(11) -> `opening`(7) is **-4** at each of two sites. 36 + 4 + 4 = 44,
and 26,480 - 44 = **26,436**, which is what `wc -c` returns. The itemization is also what proves the
pre-edit figure was 26,480 and not something else, so the five earlier reviews' structural check is
re-baselined rather than retired — and `git diff --stat` staying at 28/171 is the independent
evidence that every edit is an in-line replacement of a line the diff already counted.

**The maintainer-ruled sentence is byte-identical to HEAD, verified independently and not by byte
count.** I extracted HEAD `:5` and current `:7` to separate files and compared: `diff` exit 0,
**584 bytes each**, `md5` **a236d060acf135d69af06a01cf43646a** on both. The whole `## Problem
statement` section diffs to exactly one changed line — the "This spec covers eight improvements"
paragraph, which is R1's own re-pointed clause (added line 3) and not the ruled sentence. The
competitor is still named in three places (`:1` H1, `:7`, `:165` `## References`), so the `:3` edit
removed a false characterization and not the comparison, which is the ruling's `## Scope` reading.

**The overlap delta closes.** Implementing the file's own four-line method independently (drop each
file's bottom link-definition block, fold every non-alphanumeric run to whitespace, lowercase,
distinct 8-word shingles):

| measure | value |
|---|---|
| rationale x post-move-spec overlap | **52** |
| left-the-spec shingles present in the rationale | **161** (unchanged) |
| rationale total shingles | 9,267 |
| `**Moved**` measurement: HEAD shingles reproduced in the rationale | **192 of 4,934**, in **41** runs, longest **20** shingles (27 words), median **3** |

52 is the figure four passes before pass 6 reported, so the disclosed +3 has unwound. I also ran the
inverse test the build report did not: restoring the old `:3` wording against the **current**
rationale still gives 52, which shows the two edits are each independently sufficient to close the
delta rather than jointly necessary — the report attributes it to the spec edit, and that attribution
is a correct sufficient cause. The durable `**Moved**` measurement reproduced on my own
implementation to every digit, and this is the first pass in which the spec moved underneath it: its
deliberate re-keying to the two frozen inputs (the 33,928-byte blob and the rationale) is what let it
survive, which is precisely the falsification the earlier current-spec-keyed triple could not.

**Item 20 is discharged, not widened — confirmed at all three sites.** `:3` no longer carries
`against \`strawberry-graphql-django\``; `:100` and `:133` now read "The opening argument for this
slice". `grep 'The win'` over the spec returns exactly one line, `:3`, inside a code span. Nothing
is left for R2 on those sites, and what replaced the item — the do-not-level standing instruction —
is in the rationale, as verified above.

**My own sweep of the new surface: every added line re-tested against what actually moved.** The
pass claims "no further mischaracterization exists"; I tested it rather than accepting it. Of the 28
added lines, exactly **ten** describe the move (`:3`, the re-pointed `## Problem statement` clause
`:9`, and the eight per-slice pointers); the other eighteen are restated contract, structural, or
status claims already routed to R2. I walked every clause of the ten against the rationale's entries
and every promise is kept: B1's spike + consumer recommendation (`:205`, `:217`) and key-construction
fence (`:272`); B2's elision predicate (`:322`); B3's second path-construction approach (`:363`),
rejected `strict=True` kwarg (`:381`) and detection loop (`:387`); B4's untyped hint-value shapes
(`:424`) and hint dispatch (`:439`); B5's "should land first" ordering clause (`:466`) and stash
sequence (`:472`); B6's audit loop (`:505`); B7's "complementary to B1" derivation (`:545`) and map
construction (`:558`); B8's "B8 last" ordering argument (in the `## Priority and ordering` entry) and
delta construction (`:586`); and the re-pointed `:9` clause's recommended build sequence. **No
further mischaracterization exists** — independently confirmed, not inherited.

### DRY findings

- **No duplication introduced against the spec.** The overlap **fell** to 52 and left-the-spec-in-
  rationale is unchanged at 161, so the edit removed a shared run rather than adding one. The
  `**Moved**` / `**Cut**` / `**Deleted**` / `**Restated in the spec, not moved**` / `**Deliberately
  left in the spec**` bullets needed no keeping in step and none was made.
- **No tally was added, for the sixth consecutive pass.** The replaced standing-note paragraph names
  its three sites and lets the reader count them; the durable file's own solution to this cycle's
  recurring count defect is applied to the fix for that defect.
- **One enumeration was retired rather than duplicated.** Replacing the "One clause" sentence instead
  of widening it means there is no second list of the three sites to keep in step — which is the
  branch that would have made a fifth enumeration, the shape this cycle has filed four times.
- **Against the sibling rationales: unchanged and clean.** The deliberate label divergence (handoff
  item 19) stands, re-derived this spawn: **10** modal labels here against **17 + 8 + 22 = 47**
  non-modal across the spec-001 / spec-002 / spec-003 rationales, plus `spec-002`'s own companion
  pointer — 48 counterexamples.
- **Existence challenge: none raised.** The pass adds no abstraction, helper, registry, or
  indirection; it replaces one clause in each of four sentences across two prose files.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty** (0 lines). `__all__` and the
re-export list are unchanged, and no change was authorized: the build plan's `## Build-wide context
flags` declares package source, `tests/`, and `examples/` read-only for the whole cycle.
`git diff --stat -- django_strawberry_framework/ tests/ examples/` -> **empty**.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed absent from `git status --porcelain
CHANGELOG.md`.

### Documentation / release sanity

Applies — the diff is entirely docs and one of the two files is an archived spec. Both were read end
to end this spawn.

- **The three baseline checkers, re-run rather than quoted.**
  - `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
    -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**,
    character-identical to the build plan's pre-flight baseline. **This is the check that mattered
    most this pass**, because the spec moved for the first time in six.
  - `uv run python scripts/check_trailing_commas.py --check` on the spec, the rationale, and this
    artifact -> **exit 0** on all three.
  - `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have
    glossary links.` **exit 0**. **Read-only form only**; the writing form was never invoked.
- **All ten anchors are single-carrier**, re-derived per anchor rather than on the checker's exit
  code: `grep -o "[glossary-<anchor>]" | wc -l` -> **2** for every one of `configurationerror`,
  `djangooptimizerextension`, `djangotype`, `fk-id-elision`, `metaexclude`, `metafields`,
  `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `queryset-diffing`. None of the three
  edited sentences carried a glossary link, but the constraint was measured rather than assumed.
  **The terms CSV was not opened** — `git status --porcelain` on it is empty.
- **Every link definition resolves on disk — re-run this spawn, because the reading expires.** Each
  target resolved from its own source file's directory and existence-tested: spec **11 definitions /
  11 distinct uses**, rationale **19 / 19**, **0 undefined references, 0 unused definitions, 0 of 30
  targets missing.** No definition was added or removed by any edit. Both files carry `<!-- LINK
  DEFINITIONS -->` with all ten canonical group headers in order.
- **In-page anchors resolve and the em-dash hazard is still avoided.** The repo's own
  `scripts/check_spec_glossary.py::github_anchor` over the spec's **15** headings -> **15 unique
  slugs, 0 duplicates**; `#problem-statement` and `#proposed-improvements` both land on real
  headings. No heading was touched this pass.
- **Structural properties.** `grep -c '^```'` -> **0 / 0** in both files;
  `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` -> **no match** in both, so `AGENTS.md` rule 27 holds;
  `grep -nP '\]\((?!#|https?:)'` -> **no match**, so the reference-style convention is preserved,
  not merely unbroken.
- **The spec narrates no history.** `grep -niE 'as of (review )?round|amendment|retract|inverted|a
  later strawberry|no longer|used to |formerly|previously|has since'` returns **one** line, `:3`,
  whose only hits are "the former `## Priority and ordering` section" and "may no longer make" —
  rule-1 pointer vocabulary, unchanged by this pass. The change record for the edit lives in the
  rationale, which is where a change record belongs.
- **Pointer discipline is intact** — eleven `[spec-004-rationale]` occurrences: the companion
  paragraph (`:3`), the re-pointed `## Problem statement` clause (`:9`), eight per-slice pointers
  (`:29`, `:47`, `:63`, `:90`, `:100`, `:121`, `:133`, `:151`), and the definition (`:202`).
- **Version strings / card IDs / KANBAN.** The spec carries no version or status header. `KANBAN.md`,
  `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, `CHANGELOG.md`, `examples/fakeshop/db.sqlite3`
  and the terms CSV are **all clean** — re-derived this spawn with `git status --porcelain` over that
  exact path list, not inherited. No card moved and this cycle wrote no DB.
- **No script-rendered doc was regenerated**, so the staging-docstring check has no subject, and no
  obsolete "coming soon" / "planned" wording was introduced.
- **Archival unchanged.** The rationale lives directly at `docs/SPECS/appx/`, the archived-companion
  location `AGENTS.md` rule 26 names.

### What looks solid

- **The scope call is right, and it is right for a reason the pass under-claimed.** Its four grounds
  all re-derive, but the decisive one is `worker-1.md` rule 1: the pointers are R1's own checklist
  obligation ("naming what was moved and where"), so a pointer that misnames what moved is an
  incompletely discharged box, not R2's reconciliation input. That reading needs no analogy to the
  maintainer's ruling at all. Reopening a frozen file to correct one's own output is exactly the
  judgement a self-reviewing pass gets wrong in the permissive direction, and this one argued it
  before making it, measured every premise, and confined the edit to text it wrote.
- **The asymmetry is the hardest part of the call and it is correct.** Levelling seven pointers to
  one phrase is the tidier-looking move and would have edited five true sentences into vaguer ones.
  Keeping two spellings preserves a real property of the material, uses the vocabulary the rationale
  had already settled on, and is protected by a standing instruction in the durable file rather than
  in a closing artifact.
- **The `-44` is the model for how a moved number should be reported.** Itemized to the byte at three
  named sites, cross-checked against `wc -c`, and paired with an independent invariant (`git diff
  --stat` unchanged at 28/171) that could not have held if a line had been added or removed. A
  changed count after six frozen passes is exactly what reads as drift, and this one cannot.
- **The `**Moved**` measurement survived the event it was designed for.** It was deliberately re-keyed
  to two frozen inputs after an earlier current-spec-keyed triple was falsified by a later edit; this
  is the first pass in which the spec actually moved, and 192 / 4,934 / 41 runs / longest 20 / median
  3 reproduced on my own implementation to every digit. That is the design paying off, not luck.
- **The overlap returned to 52 by the defect disappearing, not by trimming a quotation.** Disclosing
  a moved metric with its cause, then watching it unwind when the cause was removed, is a better
  record than a metric that never moved.
- **Every invariant that had to survive did.** Ten single-carrier anchors, 30/30 link targets
  resolving, 15/15 unique heading slugs, both in-page anchors resolving, the terms CSV never opened,
  `check_spec_glossary` and `import_spec_terms --check` green and character-identical to the
  pre-flight baselines, rule 27 holding in both files, zero fences in either, all 28 added lines
  individually re-accounted, the maintainer-ruled sentence proved identical by `diff` and `md5`, and
  no source, test, or example file changed by this cycle.

Three things I would have worded differently and am **not** filing, recorded so pass 8 — if there is
one — does not re-derive them:

- **Claim 3's supporting universal over-reaches** ("every survival the freeze protects is a
  present-tense claim about HEAD"). `## Implementation checklist` bullet 2's parenthetical is a
  sequencing claim, is on the rationale's own left-standing list, and is handoff item 4. The
  conclusion rests on authorship, which claim 1 measures, so no wrong action is available. It lives
  only in this artifact, which closes with the cycle.
- **Claim 4 is an analogy, not an identity.** The maintainer's ruling was made of a rationale defect
  and its stated reason has a file-ownership conjunct that does not transfer. What does transfer is
  the axis, demonstrated by the ruling's own two-sided treatment. "Ruled an analogous shape on the
  same axis" would have been exact.
- **`## How to read this file` `:64`-`:67` previews three of `## Standing notes`' four entries**, and
  the omitted one is now where the do-not-level instruction lives. The bullet's operative imperative
  is unconditional ("Read `## Standing notes` before editing the spec"), so a reader who follows it
  meets the instruction; the enumeration does not gate the read. Pre-existing shape, not created by
  this pass. One clause would tighten it if R2 is editing that file anyway.

### Temp test verification

None. No temp test was written and none was warranted: this cycle changes no code path, so there is
nothing a test could exercise. `docs/builder/temp-tests/r1/` was not created in this pass either.
Every verification above is a read-only command over the two changed files, the read-only HEAD copy,
the build plan, or the repo's own checker scripts; the two measurement scripts I wrote (a shingle
counter and a link-definition resolver) ran from a scratchpad **outside the repository** and are not
build artifacts.

**Static helper.** `scripts/review_inspect.py` was **not** run, and the skip is recorded here per
`worker-3.md` `## Static helper use`. `BUILD.md` `### When to run the helper during build` triggers
it on a new `.py` file, a touched file under `optimizer/` or `types/`, or 30+/50+ new lines of logic.
`git diff --stat -- django_strawberry_framework/ tests/ examples/` is empty, so no trigger fires. No
shadow file was read or written.

**Failability proofs.** The report's `None; this pass introduced no new boundary.` is verified rather
than accepted: `git diff -- django_strawberry_framework/` is empty, so there is no boundary, guard,
gate, or rejection path to prove. `worker-3.md`'s mandatory re-run floor is satisfied by an **empty
re-run set**, which it permits only when the diff introduces no boundary meeting the floor — that
condition holds by measurement. **No boundary was re-run and none was accepted on a builder's record,
because none exists.** Worker 3's source carve-out was not exercised: no production file was mutated
at any point in this pass.

**Hot-path budget.** Not owed. The plan declares `none`, and correctly — nothing in this diff runs
per request, per resolver, per row, per connection, or per outbound message.

**Floor verification.** Not owed. The plan declares scope `none`, and correctly — the diff touches no
Django / Strawberry / channels integration seam.

**Coverage.** No `pytest` run, no `--cov*` flag in any form, at any point in this pass.

### Notes for Worker 1 (spec reconciliation)

**This is the complete, current R2 handoff and it supersedes the pass-6 list.** R2 is the next item
and the same role, so nothing lives only in a closed section. Items 1-9, 11-15 and 17-19 are
re-issued with every reference re-checked against the files on disk this spawn; items 10, 16 and 20
are closed or discharged and are re-issued in that state so a dispatcher building R2's prompt from
this list cannot mistake a closed item for a dropped one. Spec line numbers are unchanged (216 lines,
all three edits in-line); rationale line numbers below `:771` are unchanged and the file grew
815 -> 819 lines.

1. **`D5` leaves the spec with no extension-lifecycle statement at all.** R1 deleted the falsified
   spike and its recommendation rather than replacing them. The open question is whether the spec
   states the current construction form or points at `spec-029` Decision 3, which owns it. The build
   plan's anti-absorption rule, `docs/README.md` #"The optimizer is a module-level singleton wrapped
   in a factory", and `docs/GLOSSARY.md` all argue for the pointer; I agree, and re-confirmed
   `docs/README.md` this spawn. **What R2 must not do is transplant the corrected recommendation into
   spec-004** — that is the `**The scope trap specific to this spec.**` failure.
2. **`D24` is already discharged** by the `## Priority and ordering` deletion — all eight slices now
   sit under `## Proposed improvements` in heading order. Verify, do not perform.
3. **`### B6` `**Public API.**` says "classmethod"; HEAD ships a `@staticmethod`.** Kept verbatim on
   purpose; a one-word correction and R2's. Spec `:108`, re-checked this spawn.
4. **`## Implementation checklist` bullet 2 is the last in-spec trace of the cache-lifetime spike**
   (spec `:174`, `- [x] B1 cache-lifetime spike (10-min investigation, precedes B1 implementation)`).
   A checklist is contract scaffolding so R1 left it, but its parenthetical is a sequencing claim
   about work eleven versions shipped and the section it pointed at is gone. R2's call whether it is
   trimmed.
5. **`## References`' third paragraph is still dangling** (`D27`, spec `:169`): it cites a "skip
   Strawberry conversion" optimization "noted in B1's implementation" that `### B1` never noted, at
   HEAD or now. R1 neither created nor repaired it. The thing that did land is the deferred-conversion
   thunk, a different mechanism.
6. **`### B7`'s "No `_meta.get_fields()` call ever appears in the request path" was cut, but its
   contradiction survives elsewhere.** The contradicting sentence — `**Walker needs registry
   lookup.**`'s unregistered-model fallback at spec `:131` — is still there and still true, and `D23`
   records it as a documented dual contract. Nothing is owed; **R2 should simply not "restore" the
   deleted claim.**
7. **`D25` and `D28` are discharged and the move report's own handoff does not say so.** Both lived
   inside `## Priority and ordering` and went with it. The rationale's `### The former `## Priority
   and ordering`` entry records both correctly, so the durable record is complete — but an R2 working
   from the original drift table will hunt two sentences that no longer exist.
8. **`D6` is narrower than the drift table anticipated, and here is exactly how much.** The policy
   half is stated in the spec (`**Cache storage.**`, spec `:23`) and is off R2's list. What remains is
   precisely three things, none of which appears anywhere in the spec — re-verified this spawn by
   absence grep (`lru|evict|bounded|\b256\b|ordereddict|move_to_end|quarter` returns only `:23` and
   the pre-existing `lru_cache.cache_info()` mention at `:27`): the **bound** (`256`), the **storage
   mechanism** (`OrderedDict` + `move_to_end`, and the `suppress(KeyError)` guard against the
   concurrent-eviction race), and the **batch size** (a quarter rather than one entry).
   `**Cache storage.**`'s plural "entries" is generic and neither states nor forecloses the batching.
9. **Decided — do not re-open.** The escalated contract-level question (`## Problem statement`'s
   surviving competitive positioning) was ruled on by the maintainer. The canonical record — the
   decision, its reasoning, and the rejected alternatives each with the reason it lost — is
   `docs/builder/build-004-optimizer_beyond-0_0_3.md` `## Maintainer decision — the surviving
   competitive positioning in `## Problem statement``. **Read it there; it is not restated here and it
   is not R2's to re-derive.** Its operative consequences for R2: the sentence at spec `:7` **stays
   byte-for-byte** — I proved this spawn that it still is, by `diff` and `md5` of that line against
   the read-only HEAD copy, **not** by the file's byte count, which changed at pass 6 for unrelated
   reasons; the keep is recorded in the rationale at `:171`-`:180` and `:194`-`:197`; and
   `## Problem statement`'s "eight improvements that the existing libraries do not ship" framing is a
   **separate** claim, is `D1`'s, and is still R2's.
10. **CLOSED — the pass-6 Low is fixed in both files.** The rationale's `## Standing notes` closing
    paragraph no longer says "One clause"; it names the sites and carries the standing instruction
    re-issued as item 20. Nothing is owed here.
11. **R2's `_optimizer_field_map` worklist is the rationale's bullet (`:694`-`:701`), not the build
    plan's `D22` row.** Re-derived this spawn by occurrence count, not by matching lines:
    **6 occurrences of `_optimizer_field_map` across 5 sites in 3 sections** — spec `:84` (B4
    `**Walker needs registry lookup.**`), `:112` (B6's exposed-fields paragraph), `:129` (B7
    `**Mechanism.**`, **twice**), `:131` (B7 `**Walker needs registry lookup.**`), `:135` (B7
    `**Test surface.**`). `D22` counts four sites and omits `**Test surface.**`. Two riders on the
    same sweep: `:112` is the sole carrier of **both** `metafields` and `metaexclude`, so it must be
    rewritten with the links re-sited rather than dropped; and `:84` additionally still says the
    walker reads `_optimizer_hints` off the type class (the spec's **only** occurrence of that
    spelling), which is `D16`'s retired mirror in the same sentence.
12. **`### B8`'s surviving opening paragraph is on an R2-facing list — here is where.** The tenth
    bullet of the rationale's `## Standing notes` `### The status claims were left standing`
    (`:714`-`:719`). It states the package's own **pre-B8** behaviour in the present tense ("the
    optimizer blindly stacks another `.select_related("category")` on top", spec `:141`), and
    shipping B8 is what falsified it. The build plan's drift table carries **no** row for it: its
    three B8 rows (`D24`, `D25`, `D26`) name the document structure, the deleted ordering section,
    and the cut fence. **Work this item from the rationale bullet, not from the drift table.**
13. **The link-target disk check has an expiry and mine is the current reading, not the last word.**
    30/30 resolve at `346d6731`, spec 11/11 and rationale 19/19 with zero undefined references and
    zero unused definitions. **R2 and R3 re-run it themselves rather than quoting this one**, and
    re-run `import_spec_terms --check` after any further concurrent DB write.
14. **Baseline state for Worker 0 to append** (reported, never reverted): `git status --short` was the
    same four cycle paths at the start and end of this pass — no churn at all, for the eighth
    consecutive pass. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, `CHANGELOG.md`,
    `examples/fakeshop/db.sqlite3`, the spec-004 terms CSV, and
    `django_strawberry_framework/optimizer/predicates.py` are all clean at `346d6731` — but R2
    re-derives that rather than inheriting it.
15. **A standing hazard this cycle has now demonstrated seven times, worth carrying into R2's own
    writing.** Counts or universals wrong or unreproducible: `_optimizer_field_map` "five mentions";
    the survival summary; "two B8 rows"; the shingle triple falsified by a later edit; "42" quoted
    runs; "the only place in the whole corpus"; "One clause … in the spec", which was three. R2
    rewrites more prose than R1 did, in the same durable files. **State the unit beside any count,
    state the population beside any universal, state the method beside any measurement, and re-measure
    after the last edit rather than while making it** — and prefer the durable file's own solution,
    which was to name the sites and let them be counted rather than to assert a number.
16. **DISCHARGED: the build plan's `D17` row is corrected and agrees with the rationale.** Verified at
    source (`types/base.py`: `_validate_meta` defined 1073 / called 535, `_validate_optimizer_hints`
    defined 1232 / called 537). Nothing further is owed. The sentence it governs (spec `:86`) is still
    the **sole carrier of the `configurationerror` anchor**, so it remains the anchor-bearing rewrite
    with the least margin for a wrong premise. One phrasing worth tightening but not filing: the
    rationale bullet's "it only normalizes the hints mapping" is true of `_validate_meta`'s *hints*
    handling and loose about the function, whose docstring lists eight validation steps; the plan's
    row states the same fact without the word "only".
17. **A small factual imprecision in the rationale, an R2 touch-up rather than a finding.** The
    `### B1` entry calls it "the locked `strawberry-graphql 0.316.0`". `0.316.0` is the **declared
    floor** (`pyproject.toml` #"strawberry-graphql>=0.316.0"); `uv.lock` resolves higher. `spec-029`
    uses the same word, so spec-004's rationale inherited the phrasing from the spec that owns the
    correction. If R2 tightens it, it should decide for both rather than leave the two documents
    disagreeing.
18. **Do not "fix" the candidates prior passes opened and left, and do not re-derive them.**
    `## How to read this file` `:51`-`:52` ("headings that no longer exist in the spec at all") and
    the `**The win.**` entry's `:120` ("The `**The win.**` label no longer appears in the spec") are
    both true as written — the single `grep 'The win\.'` hit at spec `:3` is a mention inside a code
    span, not a paragraph label, re-confirmed this spawn. Also on that list: `## How to read this
    file` `:17`-`:18` ("the whole section is contract"), a statement in this file's
    deliberation/contract vocabulary and not a correctness claim; `### B8`'s maintain-by-hand
    retracted item, whose entry body already protects the surviving requirement; the `*Alternative
    rejected — keep them and cut only the competitor's name.*` block (`:142`); the `## Standing notes`
    opener's "competitive argument, proposal code, build order" class list (`:682`); `:3`'s surviving
    list of what the rationale carries, which says what the file *covers* rather than where each
    paragraph ended up; and `*Why they went.*`'s "for seven of the eight" (`:135`), whose supporting
    clause is overstated for B1 but whose exception is documented under a bold lead in the same entry.
19. **The block label diverges from all three sibling rationales, deliberately.** `**Claims the spec
    may no longer make.**` here (**10** blocks), against **47** non-modal labels in the spec-001 (17),
    spec-002 (8) and spec-003 (22) rationales plus `docs/SPECS/spec-002-optimizer-0_0_2.md`'s
    companion pointer — 48 counterexamples, re-derived this spawn. The divergence is correct: those
    three ran an R2 spec-reconciliation pass before their labels were finalized; spec-004's has not.
    **R2 must not harmonize spec-004's label back to the sibling form**, and if R2 performs the
    retractions it should decide deliberately whether the label then earns the factual spelling — the
    file's own definition at `## How to read this file` is what makes either spelling readable, so
    that definition is the thing to keep in step, not the label alone.
20. **DISCHARGED and replaced by a standing instruction: the two-spelling asymmetry across the
    per-slice pointers is deliberate and must not be levelled.** All three mischaracterizing sites
    (spec `:3`, `:100`, `:133`) were corrected at pass 6 and I confirmed all three this spawn; R2 owes
    nothing on them. What R2 inherits instead: **`### B5`'s (`:100`) and `### B7`'s (`:133`) pointers
    read "The opening argument for this slice" because their `**The win.**` paragraphs name no
    competitor; the five at `:29`, `:47`, `:63`, `:90`, `:121` read "The competitive argument" because
    theirs do; and B8's (`:151`) carries no such clause because B8's paragraph stayed in the spec.**
    A harmonizing sweep must not level them to one phrase. The instruction is durably recorded in the
    rationale's `## Standing notes` closing paragraph (`:771`-`:777`), not only here. This joins item
    19 as the second deliberate divergence R2 must not reverse.

### Review outcome

`review-accepted`.

**R1's deliverable is complete.** Worker 1's final-verification pass is confirming a two-file docs
change with no open finding: the rationale file exists at `docs/SPECS/appx/`, the spec is 216 lines /
26,436 bytes against a 359-line / 33,928-byte HEAD blob at 28 insertions / 171 deletions, all ten
glossary anchors are single-carrier, `check_spec_glossary` and `import_spec_terms --check` are green
and character-identical to the pre-flight baselines, all 30 link definitions resolve on disk, rule 27
holds in both files, neither file carries a fence, the spec narrates no history, the maintainer-ruled
`## Problem statement` sentence is byte-identical to HEAD by `diff` and `md5`, and no source, test, or
example file was changed by this cycle. Every High, Medium and Low finding raised across seven reviews
is addressed; none is outstanding and none was rejected without a recorded reason.

**On proportionality, since this is the seventh review.** Everything the prompt sent me to grade came
back sound and I filed none of it. All four scope claims re-derive — the three sites are among the 28
added lines, no drift row covers them, they describe the move rather than the package, and the
maintainer's ruling turns on the axis the pass says it does — and there is a fifth ground the pass did
not cite that is stronger than its fourth: `worker-1.md` rule 1 makes the pointer text R1's own
checklist obligation. The asymmetry is right and durably protected. The `-44` is itemized to the byte
and cross-checked two ways. The overlap returned to 52 by the defect disappearing. My own sweep of the
new surface — every one of the ten added lines that describes the move, tested clause by clause
against the rationale entry each promises — found no further mischaracterization. Three things I would
have worded differently are in `### What looks solid` and are not findings: the over-broad universal
in the pass's third claim, the "identical" in its fourth, and the `## How to read this file` bullet
that previews three of four standing notes. None makes a wrong action available to any reader, and
none is durable beyond the entry it sits in.

Per the build plan's `### Deviation 2`, `review-accepted` routes to **Worker 1** for the
final-verification pass, which sets `final-accepted` and returns the item to Worker 0.

### Working-tree churn observed during this review — reported, not reverted

**None.** `git status --short` was the same four entries at the start and at the end of the pass:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
```

`docs/builder/worker-memory/worker-3.md` was consolidated and appended to this pass and correctly does
not appear above: `docs/builder/worker-memory/` is gitignored. `HEAD` is
**`346d67312599c0536980969caa39085ab3885ae8`**, re-derived this spawn, and it did not sweep this
cycle's work: `git log -1 -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns
**`20a9752f`** and the three artifacts are still untracked. That is the standing hazard check, done
with `git log` rather than `git status` alone. No stray untracked file appeared, and nothing was
reverted. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`, `CHANGELOG.md`,
`examples/fakeshop/db.sqlite3`, and the spec-004 terms CSV are all clean.

---

## Final verification (Worker 1)

Read in full before writing anything: `AGENTS.md`, `START.md`, `docs/builder/BUILD.md`,
`docs/builder/ARTIFACT.md`, `docs/builder/worker-1.md`, `GOAL.md`, `docs/GLOSSARY.md`,
`CHANGELOG.md`, `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`,
`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`,
`docs/builder/build-004-optimizer_beyond-0_0_3.md`, this artifact end to end in order (plan, move
report, and all thirteen subsequent pass sections), and `docs/builder/worker-memory/worker-1.md`.
No other worker's memory was opened. The read-only HEAD reference was
`git show HEAD:docs/SPECS/spec-004-optimizer_beyond-0_0_3.md > <scratchpad outside the repo>/spec-004-HEAD.md`;
no `git stash` / `checkout` / `restore` / `worktree` at any point, and no prior entry was edited.

`HEAD` re-derived this spawn: **`346d67312599c0536980969caa39085ab3885ae8`**.
`git log -1 -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` still returns **`20a9752f`** and the
three artifacts are still untracked, so no concurrent commit has swept this cycle's work.
`git status --short` is the same four cycle paths and nothing else, for the ninth consecutive pass.

**Nothing below is quoted from a prior section.** Every figure was re-derived this spawn.

- **Item checklist:** all 19 boxes of the Plan's `### Dispatched findings checklist` are `- [x]`;
  each was audited against the files and each contract landed. No box was un-ticked, none was
  ticked by me, and none needs a deferral reason.
- **DRY check across this item and the rationale it produced:** no duplication introduced. Measured
  below.
- **Existing tests still pass:** this cycle changed no code, so the honest form is the focused
  confirmation that nothing was touched — `git diff --stat -- django_strawberry_framework/ tests/
  examples/` is **empty**. No `pytest` was run (the final gate owns the full sweep, and `AGENTS.md`
  rule 15 forbids an unasked run); no `--cov*` flag in any form at any point.
- **Spec reconciliation:** the spec needs no further Worker 1 edit **for R1's scope**. Everything
  still owed against HEAD is R2's, and none of it was pre-empted here.
- **Final status:** `final-accepted`.

### The item's contract, walked

R1 has no `### Spec slice checklist (verbatim)` because spec-004 carries no `## Slice checklist`
and this is a residual-completion cycle (build plan `## This is a residual-completion cycle, not a
fresh build`). Its contract is the plan's **R1** bullet plus `BUILD.md` `## Spec rationale
extraction` and `worker-1.md` `### Performing the rationale move`. Every obligation landed:

| Obligation | Where it landed | Confirmed |
|---|---|---|
| The rationale file exists at the archived-companion path | `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`, **819 lines / 58,828 bytes** | written directly to `appx/`, never to `docs/` and moved |
| It is a **cut**, not a copy or a summary | 192 of the pre-move blob's 4,934 shingles survive here, in 41 runs, longest 27 words, median 3 | re-derived exactly (below) |
| Every decision cut from keeps a one-line pointer | eight per-slice pointers (`:29`, `:47`, `:63`, `:90`, `:100`, `:121`, `:133`, `:151`), the companion paragraph `:3`, the re-pointed `## Problem statement` clause `:9` | 11 `[spec-004-rationale]` occurrences; the four sections that lost nothing correctly carry none |
| Keyed to the spec: every entry names its section and links a resolving anchor | 11 entries, each opening `Spec: …[spec-004-improvements]` or `…[spec-004-problem]` | both anchors resolve against real heading slugs |
| Rejected alternatives, each with the reason it lost | nine `*Alternative rejected — …*` blocks | present |
| Every change a decision has undergone, with the spec that caused it | `spec-016` ×3, `spec-018` ×2, `spec-029` ×2, `spec-032` ×2, `spec-033` ×6, `spec-035` ×6, `spec-047` ×2 | present |
| Every claim the spec may no longer make, per entry | 11 blocks — 10 `**Claims the spec may no longer make.**` + the maintainer-ruled `**… no longer makes as any slice's own argument.**` | one per entry |
| Falsified prose **deleted**, not moved (rule 2) | the fences' bodies; the `_sync`/`_async` spike findings and its inverted recommendation | **zero** fences in either file |
| Implementation-relevant rationale **stayed in the spec** (the load-bearing carve-out) | five rules: the `(name, value)` pair shape + omit-not-default rule (`:21`), LRU eviction (`:23`), `dst_optimizer_planned` (`:53`), the `check_schema` public-API sentence (`:108`), the snake-cased field-map key (`:129`) | all five read in the spec this spawn |
| The spec narrates no history | one grep hit, `:3`, both matches rule-1 pointer vocabulary | verified by absence over twelve alternations |
| Spec byte count reported before and after | 359 lines / 33,928 bytes → **216 lines / 26,436 bytes**, **-143 / -7,492 (-22.1%)** | `wc` this spawn; `359 - 171 + 28 = 216` |
| `spec-002` / `spec-003` rationales pointed at, not duplicated | `## How to read this file`'s family bullet + the spec's own `:3` clause | overlap is house form only (below) |
| Nothing outside the writable set was written | `git status --short` is four entries | source, tests, examples, sibling specs, terms CSV, `CHANGELOG.md`, `KANBAN*`, `docs/GLOSSARY.md`, `docs/TREE.md`, `db.sqlite3` all clean |

**Staged-anchor sweep**, run here as a cheap backstop rather than pre-empting R3:
`grep -rEn 'TODO\(spec-004|TODO-(ALPHA|BETA|STABLE)-004' .` returns **two** hits, both in
`docs/builder/build-004-optimizer_beyond-0_0_3.md` and both prose quotations of the anchor string
in Worker 0's own description of the sweep. Source, tests, examples, the spec, and the rationale
carry **zero**.

### Verification, each result quoted

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
  -> `OK: 10 terms - all have glossary entries and at least one spec link.` **exit 0**,
  character-identical to the build plan's pre-flight baseline.
- `uv run python scripts/check_trailing_commas.py --check` on the spec, the rationale, and this
  artifact -> **exit 0** on all three.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards have
  glossary links.` **exit 0**. **Read-only form only**; the writing form was never invoked, and the
  DB is clean afterwards.
- **Per-anchor, not on the checker's exit code.** `grep -o "\[glossary-<anchor>\]" | wc -l` -> **2**
  for every one of `configurationerror`, `djangooptimizerextension`, `djangotype`, `fk-id-elision`,
  `metaexclude`, `metafields`, `metaoptimizer-hints`, `only-projection`, `optimizerhint`,
  `queryset-diffing` — 1 body use + 1 definition each. The terms CSV was never opened.
- **Every link definition resolves on disk**, each target resolved from its own source file's
  directory with the anchor fragment stripped and an existence test per path: spec **11 definitions
  / 11 distinct uses**, rationale **19 / 19**, **0 undefined references, 0 unused definitions, 0 of
  30 targets missing.** All ten `../spec-NNN-….md` siblings (002, 003, 004, 016, 018, 029, 032,
  033, 035, 047) are present; none points at a file the concurrent renumber moved.
- **In-page anchors.** The repo's own `scripts/check_spec_glossary.py::github_anchor` over the
  spec's **15** headings -> **15 unique slugs, 0 duplicates**; `#problem-statement` and
  `#proposed-improvements` both land on real headings.
- **Final counts.** Spec **216 lines / 26,436 bytes**; rationale **819 lines / 58,828 bytes**;
  `git diff --stat -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **28 insertions / 171
  deletions**; HEAD blob **359 lines / 33,928 bytes** with **16** fence markers against **0** in
  both current files. Added-line population re-counted: **24 non-blank + 4 blank = 28**.
- **The maintainer-ruled sentence is byte-identical to HEAD**, proved by `diff` of the line and not
  by the file's byte count: HEAD `:5` and current `:7` compare identical at **584 bytes** each.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` and `grep -nP '\]\((?!#|https?:)'` over both files ->
  **no match** (exit 1) in each case. Rule 27 and the reference-style convention hold in both, and
  each file carries `<!-- LINK DEFINITIONS -->` with all **10** canonical group headers.

### The measurements, re-derived on my own implementation

Under the method the rationale itself states (drop each file's bottom link-definition block, fold
every non-alphanumeric run to whitespace, lowercase, distinct 8-word shingles):

| measure | re-derived |
|---|---|
| pre-move blob distinct shingles | **4,934** |
| post-move spec | 3,784 |
| rationale total | 9,267 |
| left the spec | 1,853 |
| of those, present in the rationale | **161** |
| of those, present in neither file | 1,692 |
| rationale x post-move-spec overlap | **52** |
| `**Moved**` bullet: HEAD shingles reproduced here | **192**, in **41** runs, longest **20 shingles = 27 words**, median **3** |

Every durable figure reproduces to the digit on a fourth independent implementation, and this is the
first reading taken **after** the spec moved underneath it — which is the falsification the earlier
current-spec-keyed triple could not survive and the re-keying was performed for. The qualitative
claim the numbers support holds on run structure rather than on the total: a longest contiguous run
of 27 words is what proves "no section, paragraph, or fence was moved whole".

### DRY check

- **Against the spec: none.** Overlap 52 shingles, and the longest contiguous HEAD run reproduced
  anywhere in the rationale is 27 words. The five rules restated in the spec are stated **once**
  each, in the spec, with the rationale carrying only why they are rules — the spec states the
  rule, the companion states the reason, and the two share no 8-word run.
- **Against the sibling rationales: house form only, and the one substantive run is gone.** Overlap
  with `spec-003-…-rationale.md` decomposes into 31 runs (89 / 63 / 59 / 47 / 30 / 29 / 20 / 17 / …)
  and with `spec-002-…-rationale.md` into 20 (30 / 23 / 18 / 17 / …). I read every run of 15+: all
  are the shared file form — the opener, `## How to read this file`, `## Provenance of this
  record`'s *Moved* / *Cut* / *Deleted* vocabulary, the "what the pass did NOT do" paragraph,
  `## Standing notes`' framing. **The 17-shingle B2 ordering-invariant run that was pass-1's Low-2
  is absent**, confirmed by string test as well as by run structure.
- **Against the later optimizer specs: no restatement.** Every entry touching `spec-016` /
  `spec-018` / `spec-029` / `spec-032` / `spec-033` / `spec-035` / `spec-047` names the owning spec
  and states the departure rather than transplanting its rules — the build plan's
  `**The scope trap specific to this spec.**` rule, correctly applied.
- **Existence challenge: none raised.** The item adds no abstraction, helper, or indirection.

### The R2 handoff — complete and accurate as R2's input

Worker 3's pass-7 `### Notes for Worker 1 (spec reconciliation)` is the 20-item list R2's dispatch
will be built from. I walked all twenty against the files on disk rather than against the list.

**All thirteen open items name real, still-open reconciliation work**, each re-verified:

- **1 (`D5`)** — the spec carries no extension-lifecycle statement at all: `_sync_extensions`,
  `_async_extensions`, `get_extensions`, `extensions=[` all return **0** hits. Genuinely open, and
  the pointer-versus-transplant question is genuinely R2's.
- **3** — spec `:108` reads "classmethod"; `optimizer/extension.py::DjangoOptimizerExtension.check_schema`
  is decorated `@staticmethod` at HEAD. Both halves confirmed at source.
- **4** — spec `:174` still carries `- [x] B1 cache-lifetime spike (10-min investigation, precedes
  B1 implementation)`. Present.
- **5** — spec `:169` still carries the dangling "skip Strawberry conversion" reference, and the
  HEAD copy confirms `### B1` never noted it, so it was dangling on arrival.
- **6** — the contradicting fallback sentence is still at spec `:131` and still true.
- **8 (`D6` narrowed)** — the absence grep over the whole spec returns only `:23` and the
  pre-existing `:27`. No `256`, no `OrderedDict`, no `move_to_end`, no batch eviction anywhere. The
  three remaining components are correctly stated and the policy half is correctly off the list.
- **11** — re-derived by occurrence, not by matching line: **6 occurrences across 5 sites in 3
  sections** (`:84`, `:112`, `:129` ×2, `:131`, `:135`), and `:84` is the spec's **only**
  occurrence of the `_optimizer_hints` class-attribute spelling. Both riders hold: `:112` is the
  sole carrier of `metafields` and `metaexclude`.
- **12** — spec `:141` carries the pre-B8 present-tense claim, and the rationale bullet is where the
  item says it is. The build plan really does carry no drift row for it.
- **13, 14** — the link-target and baseline readings are current as of this spawn (30/30, four
  cycle paths, every generated doc and the DB clean) and correctly flagged as expiring.
- **15** — the standing count/universal hazard. Advice rather than work, and correctly labelled.
- **17** — "the locked `strawberry-graphql 0.316.0`" is at rationale `:218`; `0.316.0` is the
  declared floor. Real, small, correctly not filed.
- **18, 19** — see below.

**The three closed items are unambiguously marked** and cannot be mistaken for dropped ones: **10**
opens `**CLOSED — the pass-6 Low is fixed in both files.**`, **16** opens `**DISCHARGED:**`, and
**20** opens `**DISCHARGED and replaced by a standing instruction:**`. Each states what replaced it.
I confirmed all three closures independently: the `## Standing notes` closing paragraph no longer
says "One clause"; `_validate_meta` exists at `types/base.py` and the plan's `D17` row now matches
the rationale bullet; and all three mischaracterizing spec sites read correctly
(`:3` no longer carries `against \`strawberry-graphql-django\``, `:100` and `:133` read "The
opening argument for this slice"). **Item 9 is marked `Decided — do not re-open`** and correctly
points at the plan's `## Maintainer decision` as the canonical record rather than restating it.

**Nothing R1 surfaced lives only in a closed artifact section.** The two things that would have —
`### B8`'s surviving present-tense paragraph and the pointer mischaracterization — were both driven
into the durable rationale during the cycle (`## Standing notes` `### The status claims were left
standing`'s tenth bullet, and the `### The `**The win.**` cut …` note's closing paragraph). Every
other item is either a spec sentence R2 will meet by reading the spec, a drift-table row, or a
rationale bullet.

**The two standing do-not-reverse instructions — one fully durable, one partly.**

- **Item 20, the two-spelling asymmetry across the per-slice pointers: fully durable.** Rationale
  `:771`-`:778` states which pointers carry which spelling, why, and closes *"The asymmetry is
  deliberate: a harmonizing sweep must not level it back."* That is in the companion, not only
  here, and `## How to read this file` standing-orders *"Read `## Standing notes` before editing the
  spec"*, so a sweeper meets it on the path it is already sent down. Confirmed on disk.
- **Item 19, the modal-label divergence: its *reason* is durable, its *cross-sibling comparison and
  do-not-harmonize sentence* are not.** The rationale's `## How to read this file` bullet at
  `:30`-`:41` durably states what `**Claims the spec may no longer make.**` is — a worklist, not a
  receipt, in `BUILD.md`'s own modal wording, and why it could not be a receipt — which is the whole
  reason the label diverges. What is **not** in the durable file is the comparison itself (10 modal
  labels here against 47 non-modal across the spec-001 / spec-002 / spec-003 rationales plus
  `spec-002`'s own companion pointer — I re-derived all four counts: 17 / 8 / 22 / 1) or the
  sentence telling a harmonizing sweep to leave it alone. Those live in this artifact and in the
  handoff list only.

  **I judge that non-blocking and am not re-looping for it, for three reasons that are about this
  instruction specifically rather than about proportionality.** First, R2 is the very next item and
  its dispatch is built verbatim from this list, so the instruction reaches the one reader whose
  action it governs with certainty. Second, unlike item 20's — which tracks a permanent property of
  the eight HEAD paragraphs — item 19's instruction is **conditional and expires with R2**: the item
  itself says that if R2 performs the retractions it should decide deliberately whether the label
  then earns the factual spelling, so a permanent "never harmonize" written into the durable file
  today could be wrong tomorrow. Third, item 19 names its own durable protection: *"the file's own
  definition at `## How to read this file` is what makes either spelling readable, so that
  definition is the thing to keep in step, not the label alone"* — and that definition is present,
  reviewed, and unambiguous. Recorded here so R2 makes the call knowingly; if R2 leaves the label
  modal, one clause in that bullet is the right place to make the divergence durable, and R2 is
  editing that file anyway.

**One precision note on the durable paragraph that carries item 20**, recorded rather than filed and
not fixed. Rationale `:771`-`:772` reads *"The same characterization was in the spec's own pointer
text — the companion-pointer paragraph and the eight per-slice pointers"*. It was in **seven** of
the eight: B8's pointer (`:151`) carries no such clause at all, because B8's `**The win.**`
paragraph stayed in the spec. The paragraph is self-correcting two sentences later — it names
exactly which pointers now read which spelling — and its operative instruction is unaffected, so no
reader reaches a wrong action from it. I am not editing it: the fix is not required to accept, and
putting unreviewed prose into a durable file at the final gate would both bypass the isolation rule
and move byte figures seven passes rest on. It is the same "state the population beside any
universal" class the handoff's item 15 already carries, and R2 can tighten it in one clause if it
opens that paragraph.

### Spec reconciliation

**No further Worker 1 edit is owed by R1, and none was made this pass.** R1's own scope is the move
and the pointers it wrote; both are now accurate. I re-checked the ten added lines that describe the
move against the rationale entries they promise and every promise is kept — the spike and consumer
recommendation, the eight fences' departure accounts, the second path-construction approach, the
rejected `strict=True` kwarg, the untyped hint shapes, the hint dispatch, the audit loop, the map
construction, the "complementary to B1" derivation, B5's sequencing clauses, and the whole
recommended build sequence (B5, B1, B7, B3, B4, B2, B6, B8) are all in the companion.

**This is sharply distinct from R2's work and I did not touch it.** Every falsified present-tense
status claim the plan's 28-row drift table names is still standing in the spec, verbatim, including
`## Proposed improvements`' proposal framing (`D1`), `## Current state`'s mid-build snapshot (`D2`),
`### B1`'s three-tuple-over-a-hash key (`D3`), the `_optimizer_hints` mirror (`D16`), `_validate_meta`
(`D17`), the `check_optimizer` follow-up (`D21`), the five `_optimizer_field_map` sites (`D22`), the
dual-contract fallback (`D23`), and `## References`' dangling clause (`D27`). **R2 owns the
spec-versus-HEAD reconciliation and nothing here pre-empts it.** The two drift rows this item did
discharge — `D5`'s falsified spike under rule 2, and `D24`'s document-structure defect as a side
effect of the `## Priority and ordering` deletion — are both disclosed in the move report and
recorded in the durable `## Standing notes`, and `D25` / `D28` went with that section.

**Spec status-line re-verification** (`worker-1.md` `## Spec status-line re-verification`, run this
spawn as every Worker 1 spawn must): spec-004 carries **no** `Status:` / owner / target-release /
predecessor header block — lines 1-5 are the title, the companion-pointer paragraph, and
`## Problem statement`. Nothing in them is a status line this build has falsified, so no header edit
was owed. The `:3` paragraph is a pointer and, after pass 6, describes the move accurately.

### Failability proofs / hot-path budget / floor verification / coverage

**Failability proofs.** None owed and none exist: `git diff -- django_strawberry_framework/` is
empty, so this item introduced no boundary, guard, gate, or rejection path. Verified rather than
accepted, and no fail-open shape could have landed because no expression did.

**Hot-path budget.** Not applicable; the plan declares `none`, and correctly — nothing in this diff
runs per request, per resolver, per row, per connection, or per outbound message.

**Floor verification.** Not applicable; the plan declares floor-verification scope `none`, and
correctly — the diff touches no Django / Strawberry / channels integration seam. Nothing is owed to
the final gate on this item's behalf.

**Coverage.** No `pytest` run and no `--cov*` flag in any form, at any point in this pass.

### Working-tree churn observed during this pass — reported, not reverted

**None.** `git status --short` was the same four entries at the start and at the end:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
```

`docs/builder/worker-memory/worker-1.md` was appended to and correctly does not appear: the
directory is gitignored. `KANBAN.md`, `KANBAN.html`, `docs/TREE.md`, `docs/GLOSSARY.md`,
`CHANGELOG.md`, `examples/fakeshop/db.sqlite3`, and the spec-004 terms CSV are all clean. No file
was reverted and none was created outside the writable set.

### Summary

R1 shipped the deliverable the released cycle never produced: `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`,
819 lines, carrying one entry per spec section this pass cut from — eleven in all, each keyed to a
resolving spec anchor and each closing with the alternatives it rejected, the changes the decision
has undergone with the spec that caused each, and the claims the decision may no longer make. The
spec came down from **359 lines / 33,928 bytes to 216 / 26,436** (-22.1%): eight fenced
implementation proposals, eight slice-opening argument paragraphs, the whole `## Priority and
ordering` section, a dated extension-lifecycle spike whose premise `spec-029` retired, and six
argument clauses left it, while **five rules that lived only inside cut text were restated in the
spec** because a builder never reads the companion. The move is a verified cut rather than a copy —
of the 1,853 eight-word shingles that left the spec, 161 survive in the rationale and 1,692 in
neither file, and the longest contiguous run of pre-move text reproduced anywhere in the companion
is 27 words.

All ten glossary anchors survived at exactly one body link each, two of them re-sited into surviving
contract prose rather than into narration kept alive to hold a link, and the card-wrap chain the
constraint protects is intact. Seven review rounds ran; the last found nothing. Everything the
package falsifies about spec-004 is still standing in the spec, deliberately, for the reconciliation
item — which is the next thing to dispatch.

### Spec changes made (Worker 1 only)

`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` was written in **three** episodes across the cycle;
the dispatch's "twice" is the move plus the pass-6 correction, and the pass-1 in-line revision is
the third. Net across all three: **359 lines / 33,928 bytes -> 216 / 26,436**, `git diff --stat`
**28 insertions / 171 deletions**.

**Episode 1 — the move itself** (`## Move report (Worker 1)`, 28 insertions / 171 deletions):

| Spec location (post-move) | Change | Reason |
|---|---|---|
| `:3` | Added the companion-file pointer paragraph | `BUILD.md` `## Spec rationale extraction`; names the two cuts with no heading left to carry a pointer. |
| `:9` | Re-pointed the "recommended sequence" clause at the rationale | Rule 3 — the section it named was deleted. The `**Depends on.**` half is contract and was untouched. |
| `:19`-`:31` | Cut B1's opening argument, the fence, and the spike narrative; relabelled the survivors `**Cache storage.**`; restated the `(name, value)` pair shape and the omit-not-default rule; re-sited `djangooptimizerextension`; added a pointer | Rule 2 for the spike (falsified in both halves) and the fence (hash vs printed AST); carve-out for the pair shape; anchor preservation. |
| `:35`-`:47` | Cut B2's opening argument and fence; added a pointer | Rule 2 — the fence's elision key is the flat field-name flag the section's own prose rejects. |
| `:53`-`:63` | Cut B3's opening argument, approach (b) and its profiling instruction, the rejected `strict=True` kwarg, and the fence; restated the `dst_optimizer_planned` key; added a pointer | Rule 2 for the fence; carve-out for the context key; the rest is recorded deliberation. |
| `:71`-`:90` | Cut B4's opening argument, the rejected untyped hint-value shapes, the DRF-analog sentence, and the fence; added a pointer | Rule 2 for the fence (`cls._optimizer_hints` is retired); the rejections are deliberation. |
| `:96`-`:104` | Cut B5's opening argument, the "should land first" clause, the effort estimate, and the fence; added a pointer | Rule 2 for the fence; sequencing and estimates are deliberation. |
| `:108`-`:125` | Trimmed B6's opening argument to its API sentence, relabelled `**Public API.**`; cut the fence; added a pointer | Public API stays; the fence contradicts the section's own exposed-fields rule. |
| (pre-move `:217`-`:235`) | Deleted `## Priority and ordering` in full | A build order for work released eleven versions ago is deliberation by construction; its only contract content is stated per slice in `**Depends on.**`. |
| `:127`-`:137` | Cut B7's opening argument, the "complementary to B1" derivation, and the fence; restated the snake-cased map keying; added a pointer | Rule 2 for the fence; carve-out for the keying, whose only two carriers were both being cut in the same sweep. |
| `:139`-`:157` | Put `queryset-diffing` on the `### B8` heading; dropped the `**The win.**` label keeping the paragraph verbatim; cut the fence; added a pointer | Anchor preservation; the paragraph names no competitor and is the slice's problem statement; rule 2 for the fence. |
| `:202` | Added the `[spec-004-rationale]` link definition under `<!-- docs/SPECS/ -->` | The eleven pointer uses; target disk-checked. |

**Episode 2 — pass-1 apply-changes**, three in-line replacements, no line added or removed:

| Spec location | Change | Reason |
|---|---|---|
| `:23` | `**Cache storage.**` now states least-recently-used eviction at the bound and scopes the `functools.lru_cache` rejection to the decorator | Worker 3 Medium — restoring a **true** clause the uniform sweep dropped, under the load-bearing carve-out. Policy only; the bound, the storage mechanism, and the batch size are `D6`'s and R2's. |
| `:3`, `:29` | "the recommendation a later Strawberry release inverted" -> "the consumer recommendation it reached" | Worker 3 Low — the spec never narrates its own history; rule 1's "name what was moved and where" is still discharged by the surviving noun phrase. |

**Episode 3 — pass-6 apply-changes**, three in-line replacements, no line added or removed:

| Spec location | Change | Reason |
|---|---|---|
| `:3` | dropped ` against \`strawberry-graphql-django\`` from the companion paragraph's description of the moved class | Worker 3 pass-6 Low. B5's and B7's paragraphs moved and name no competitor, so the qualifier was false of the class it quantified over. Text this cycle wrote; no drift row covers it, and none could. |
| `:100`, `:133` | `### B5`'s and `### B7`'s pointers: "The competitive argument for this slice" -> "The opening argument for this slice" | Same finding. The other five pointers were deliberately left reading "the competitive argument" because their paragraphs do name one — the asymmetry tracks a real property and is durably recorded. |

**The maintainer decision's first clause holds and I proved it independently.** The ruling on
`## Problem statement`'s surviving competitive positioning (build plan `## Maintainer decision — the
surviving competitive positioning in `## Problem statement``) is that **the spec changes nothing**
and two recording edits land in the rationale. The sentence at spec `:7` is byte-identical to HEAD
`:5` — `diff` exit 0, **584 bytes** on both sides — verified by comparing the line itself and not by
the file's byte count, which did change at pass 6 for unrelated reasons. The two recording edits are
present in the rationale at `:171`-`:180` and `:194`-`:197`, and the competitor is still named where
house style requires it (the H1, `:7`, and `## References` `:165`), so the `:3` edit removed a false
characterization and not the comparison.

**Final status: `final-accepted`.** The R1 contract landed in full, every checklist box is ticked
and audited, no obligation was deferred, no DRY finding remains, no code was touched, and the
twenty-item R2 handoff is complete and accurate as the next item's input.
