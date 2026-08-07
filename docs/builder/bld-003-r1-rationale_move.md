# Build: R1 — Spec rationale extraction (spec-003)

Spec reference: `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` (whole file; the move touched lines 1-3, 27-41, 79-114, 125-183, 186-188, 203-227, 239-265, 331-336, 350-415, 433-435 of the pre-move file)
Rationale file created: `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md`
Status: final-accepted

**Shape note.** Per `docs/builder/build-003-optimizer_nested_prefetch_chains-0_0_2.md` Deviation 2, R1 has no Worker 2 pass: `BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role that performs the move and states that Worker 2 never reads the rationale file. So the `## Build report (Worker 2)` section of `docs/builder/ARTIFACT.md` is not applicable here and the performance record lives under `## Move report (Worker 1)` below, carrying the same fields Worker 3 would otherwise read from a build report. `Status:` is `planned` on return, which Worker 0 reads as "dispatch Worker 3" for this item.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable, and deliberately so. `worker-1.md` `### Package-wide helper inventory before helper planning` gates *helper-like logic*; R1 changes no package source, adds no helper, constant, validation branch, coercion utility, or test helper. The build plan's `## Build-wide context flags` declares package source, `tests/`, and `examples/` read-only for the whole cycle. No inventory was refreshed and none was needed.
- **Existing patterns reused.** The two archived precedents at the same `docs/SPECS/appx/` depth: `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md:1-97` and `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md:1-60` supplied the file shape (H1 with the `(deliberation, rejected alternatives, change record)` suffix; the "Deliberative companion to …" opener; the "**The move happened long after the release, not before the build.**" provenance paragraph; `## How to read this file`; `## Provenance of this record`; `## Entries keyed to the spec`; `## Standing notes`). The in-spec pointer wording follows `docs/SPECS/spec-001-django_types-0_0_1.md:43` and `docs/SPECS/spec-002-optimizer-0_0_2.md:8` verbatim in form ("Deliberation for this spec lives in its companion [rationale file][…] … Read the spec for what holds; read that file for why it holds."). The link-definition scaffold at this depth (`../` for a `docs/SPECS/` sibling, `../../` for `docs/` and `docs/builder/`) is copied from `spec-002-optimizer-0_0_2-rationale.md:499-538`.
- **New helpers justified.** None; no code was written.
- **Duplication risk avoided.** Two live risks, both named by the build plan and both handled explicitly:
  - **Against `spec-002`'s rationale.** That file already narrates why the O4 record was extracted into `spec-003`, under *"`## Purpose` and the former `## O4 extraction`"*. This file does **not** retell it: `## How to read this file` carries a bullet pointing at it and saying outright that the argument is not duplicated on this side of the split, and the spec's own new pointer paragraph carries the same clause. Grep-verified: this file contains no account of the extraction decision itself.
  - **Against the spec.** The move is a cut, so no moved sentence exists in both files. Verified mechanically below.

### Implementation steps

Line numbers are pin-at-write-time; all are against the **pre-move** spec unless stated.

1. Insert the companion-file pointer paragraph after the H1 (spec:2-3). Done.
2. `## Current state` — delete the "Concretely, …" lead-in and the pre-O4 dispatch fence (spec:27-41), replacing them with a one-line pointer. Done.
3. `### Same-query recursion for single-valued paths` — restate the FK-column-before-elision ordering invariant on the existing bullet (spec:79), then delete the proposed-branch fence (spec:85-114) and add a one-line pointer. Done.
4. `### Prefetch-boundary recursion …` — restate the empty-`only_fields` guard on the connector bullet (spec:125) and the mark-uncacheable-before-build ordering on the cacheable bullet (spec:132); delete both fences (spec:134-183); add a one-line pointer. Done.
5. `### Lookup-path flattening` — restate the return-shape and separator-composition properties in prose, delete the fence (spec:205-227), add a one-line pointer. Done.
6. `### Resolver sentinel keys` — restate the key format and the resolver-side membership test in prose; delete both fences (spec:239-265); add a one-line pointer. Done.
7. `## Documentation updates when O4 ships` — delete the three discharged bullets and the discharged half of the fourth (spec:331-336), keep the one open obligation, add a one-line pointer. Done.
8. Delete `## Implementation insertion points (O4)` and `## Anchor and lint notes` in full (spec:350-414). Done.
9. Add `[spec-002-rationale]` and `[spec-003-rationale]` to the spec's `<!-- docs/SPECS/ -->` link-definition group. Done.
10. Write the rationale file with one entry per section cut from, plus two entries keyed to headings that no longer exist. Done.

### Test additions / updates

None. R1 adds no test and changes no code path. The verification for this item is the four commands recorded under `### Validation run` below, and `AGENTS.md` rule 15 forbids a `pytest` run that was not asked for.

### Implementation discretion items

None reserved. R1 has no downstream builder, so nothing is delegable.

### Dispatched findings checklist

There is no `## Slice checklist` in spec-003 and this is not a review round, so — per `worker-1.md` planning step 8, which puts a `### Dispatched findings checklist` in this position when no spec slice checklist exists — the boxes below are the R1 obligations drawn from `docs/builder/BUILD.md` `## Spec rationale extraction`, `worker-1.md` `### Performing the rationale move`, and the build plan's R1 constraints. Worker 1 both performs and ticks here because Deviation 2 removes the Worker 2 pass; the ticks are audited at Worker 1's own final verification after Worker 3.

- [x] The move is a cut-and-paste, not a copy and not a summary: text that lands in the rationale left the spec.
- [x] Every decision cut from keeps a one-line pointer in the spec naming what was moved and where.
- [x] The rationale file is keyed to the spec: every entry names the spec section it belongs to by heading and links its anchor.
- [x] Rejected alternatives are recorded with the one-line reason each lost.
- [x] Every claim the spec may no longer make is recorded, per entry.
- [x] Prose the current decisions have falsified was **deleted, not moved** (rule 2).
- [x] Implementation-relevant rationale — the "why" that changes HOW a thing is built — **stayed in the spec** (the load-bearing carve-out).
- [x] `check_spec_glossary.py --spec …` still exits 0 and all 8 anchors still carry a link.
- [x] `check_trailing_commas.py --check` passes on both files.
- [x] Every in-page anchor the rationale targets resolves against a real spec heading.
- [x] Reference-style links only, `<!-- LINK DEFINITIONS -->` block present with all 10 canonical group headers in order, every definition target disk-checked.
- [x] `AGENTS.md` rule 27 holds in both files: no raw `path:NN`.
- [x] The rationale file is written directly to `docs/SPECS/appx/`, tracked and durable.
- [x] Spec byte count before and after reported.
- [x] `spec-002`'s rationale content is pointed at, not duplicated.

---

## Move report (Worker 1)

### Files touched

- `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` — 17 insertions, 224 deletions. Seven fenced pseudo-code blocks, two whole sections, and three-and-a-half documentation bullets cut; five rules restated in prose; one companion pointer paragraph and six per-section pointers added; two link definitions added.
- `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` — new, 453 lines / 30,545 bytes.

### Byte count (required report)

| | lines | bytes |
|---|---|---|
| spec **before** | 447 | 34,030 |
| spec **after** | 240 | 25,008 |
| delta | -207 | **-9,022 (-26.5%)** |
| rationale file (new) | 453 | 30,545 |

The pre-flight figure in the build plan (34,030 / 447) was re-measured before the first edit and matched exactly.

### What moved, what stayed, what was deleted

**Moved to the rationale (7 fences + 2 sections + 3.5 bullets).** The plan's `### What R1 inherits that spec-002 did not` says "five fenced pseudo-code blocks" and then parenthetically names six locations; the actual count of *proposal* fences is **six**, plus a seventh fence in `## Current state` quoting the pre-O4 code, which the plan flags separately in its staged-anchor sweep. Seven total, all cut. Also cut in full: `## Implementation insertion points (O4)` (63 lines) and `## Anchor and lint notes`. Also cut: three of the four `## Documentation updates when O4 ships` bullets, plus the discharged half of the fourth.

**Stayed in the spec under the load-bearing carve-out — five rules that existed only inside a fence.** This is the part of the job the prompt names as the whole job, so each is listed with the defect its loss would cause:

1. **FK column appended before the elision short-circuit** (`### Same-query recursion …`). The fence encoded it only by statement order; the bullets listed both steps unordered. Losing it silently reintroduces the N+1 the elision exists to remove, and there is **no automated guard** at HEAD (`optimizer/walker.py::_record_relation_access`, docstring only — this is the build plan's correctness-audit observation 4).
2. **`if not plan.only_fields: return` on connector injection** (`### Prefetch-boundary recursion …`). Existed only in the helper fence's body plus its comment. Losing it turns a full-row fetch into a one-column projection — data loss wearing an optimization's clothes. Survives verbatim at HEAD (`optimizer/walker.py::_ensure_connector_only_fields`).
3. **Mark the parent uncacheable *before* building the child** (same section). The fence ordered it; the bullet stated the rule without the order. Losing it caches a request-scoped visibility result when a child build degrades. Survives at HEAD (`optimizer/walker.py::_plan_prefetch_relation #"if has_custom_get_queryset:"`).
4. **The resolver-key format** `<ParentType>.<field>@<a.b.c>` and its no-parent fallback (`### Resolver sentinel keys`). D13 confirms the proposed format is correct verbatim, so the *spelling* is contract here even though its wrapper's name, privacy, and module are falsified. Verified at `optimizer/plans.py::resolver_key`.
5. **The resolver side reconstructs the same key and tests membership in `info.context.dst_optimizer_fk_id_elisions`** (same section). The other half of a two-sided protocol; the fence was its only statement of the check itself.

Also restated in prose, from the flattening fence: the return is the union of `select_related` strings and every flattened prefetch path, with nested levels joined onto the parent under the lookup separator. It was already implied by `### B8 queryset diffing`; stating it once where the helper is specified costs a clause and removes the implication.

**Deleted rather than moved (rule 2).** The fences' symbol names, signatures, privacy, and file placements wherever HEAD contradicts them (`_collect_scalar_only_fields`, `_append_unique`, `_resolver_key`, `_is_fk_id_elided`, `_runtime_path_from_info`, `_build_child_queryset`'s direct `get_queryset` call, `Prefetch(field_name, …)`); the `TODO(spec-003…)` anchor inside the `## Current state` fence; the insertion-point section's line-number framing; and the whole of `## Anchor and lint notes`, which D15 records as false in its entirety. What each proposal *meant* is in the rationale; what it *spelled* is not, except for the key format.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` → `OK: 8 terms - all have glossary entries and at least one spec link.` **exit 0** (baseline was identical).
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0** on both files.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0** — the card-wrap chain the 8-anchor constraint protects is intact.
- Anchor resolution: a slugger run over the post-move spec's headings confirms **all 13** in-page anchors the rationale targets resolve; the spec itself carries no in-page anchors.
- Link targets: all 8 rationale definition targets and both new spec definition targets disk-checked present.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files → **no match**. Rule 27 preserved, not merely unbroken.
- No inline `](path)` link in either file (URL/in-page-anchor exclusions applied); no double blank line; both files end with a newline.
- `git status --short` → only the two intended paths plus Worker 0's build plan. `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` are all **clean** — the `import_spec_terms --check` run is read-only and left no churn.
- No `pytest` run (`AGENTS.md` rule 15); no `ruff` run (no `.py` file touched).

### The 8-anchor constraint — per-anchor result

All 8 survive. The four the build plan flagged as sitting in sections R1/R2 rewrite hardest were checked individually rather than trusted to the green check:

| Anchor | Carrier after the move | Touched by R1? |
|---|---|---|
| `queryset-diffing` | `## End-goal context`, `### B8 queryset diffing` | no |
| `schema-audit` | `## End-goal context` (single carrier) | no |
| `plan-cache` | `## End-goal context`, `## Current state` `cacheable` bullet | no — only the fence below it was cut |
| `metaoptimizer_hints` | `## End-goal context` (single carrier) | no |
| `fk-id-elision` | `## End-goal context` (single carrier) | no |
| `only-projection` | `### Prefetch-boundary recursion …` lead-in prose | no — the fences were cut, the prose carrier is above them |
| `optimizerhint` | `### Hints are leaf operations` | no |
| `djangotype` | `## Lookup paths vs resolver sentinel keys` | no |

R1 cut no link-bearing prose, so no anchor needed re-siting and the terms CSV was not opened.

### Failability proofs

None; this pass introduced no new boundary. R1 changes no package source.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **Where the boundary against R2 was drawn, and why.** R1 cut the *deliberative* layer — proposal code, build instructions, discharged history. It left every present-tense **status claim** about the pre-implementation codebase standing, even the ones HEAD plainly falsifies. The precedent is explicit: `spec-002`'s extraction pass recorded that a status claim moved into a rationale file "is neither a legitimate entry here nor the deletion the move prescribes for falsified prose, and their disposition against the shipped package is item R2's call". The rationale's `## Standing notes` states this boundary in the file itself so R2 does not have to infer it.
- **Why `## Documentation updates when O4 ships` was trimmed rather than deleted.** The plan describes it as "wholly discharged", but D14(ii) is precise that one rider survives, and `### The one authorized sibling-spec edit` makes discharging it R3's work "with the spec-003 clause that licenses it". Deleting the section would have deleted that clause, leaving the R3 edit to be justified from a `bld-*.md` artifact that closes with its cycle. Three bullets and the discharged half of the fourth were cut; the open obligation stayed, and its lead-in was retensed from "When implementation lands:" to "One obligation from this list is still open:" because the original is now false. That retense is the only sentence R1 rewrote for tense rather than for the move.
- **The three in-spec `TODO(spec-003` survivors are now zero.** The build plan assigns them to R2 ("R2 owns the three in-spec survivors"), but all three rode inside text R1 was cutting anyway — one in the `## Current state` fence, one in the `## Documentation updates` bullet 3, one in `## Anchor and lint notes`. The **spec now carries zero**, and source and tests carried zero at baseline. `grep -rn 'TODO(spec-003' .` is not silent, but every surviving hit is a *quotation* of the anchor string in prose — this artifact, the build plan's drift table, and the rationale's record of what the anchors were — not a staged anchor. R2 verifies rather than performs; R3's backstop sweep should distinguish the two rather than treat the grep count as the signal.
- **The design/insertion-point contradiction is recorded, not silently resolved.** The design section said to locate `lookup_paths` "next to `OptimizationPlan`"; the insertion-point section said "End of file". They contradicted each other in one document, and deleting one of the two makes the disagreement invisible. The rationale records it under the flattening entry.
- **Anchors were verified against a slugger, not eyeballed.** `spec-002`'s rationale keys its sub-headings to parent anchors because em dashes in `### O` slice headings slug ambiguously. spec-003's sub-headings carry no em dash, so direct sub-heading anchors are safe and were used.

### Notes for Worker 3

- **The review question that matters here is over-cut, not under-cut.** A rewrite performed by its own author is reviewed by someone with no memory of why a sentence was cut, which is the only vantage point from which an over-cut is visible. The five carve-out rules under `### What moved, what stayed, what was deleted` are the specific things to test: for each, read the post-move spec and ask whether a builder who never sees the rationale could still write the code correctly.
- **The rationale file is the review instrument.** `BUILD.md` `### Who reads it, and when` makes Worker 3 a reader of it during review. Every entry names the spec section it serves and links its anchor, so each claim is checkable in one hop.
- **Do not treat surviving falsified status claims as R1 findings.** `## Problem statement`'s "The remaining O-slice is O4", `## Current state`'s planner signature and five-field plan inventory, `## Desired behavior`'s query counts, and `## End-goal context`'s "future" framing of shipped work are all deliberately untouched and are R2's, per the boundary above and the 22-row drift table in the build plan.
- Nothing was staged for a later pass without being written down; there are no temp tests and no shadow files for this item.

### Notes for Worker 1 (spec reconciliation) — carried into R2

Four items R1 surfaced that belong to R2's sweep, none of them pre-empted here:

1. **`## Definition of done` bullet 8 is now an orphaned reference as well as a false one.** It ends "…with TODO-anchored pseudo-code findings left untouched"; its referent was `## Anchor and lint notes`, which R1 deleted. D19 already records the clause as moot, so this is not a regression R1 introduced — but R2 should not have to rediscover the dangling half. Recorded in the rationale's `## Standing notes`.
2. **`### Hints are leaf operations` still names `_collect_scalar_only_fields`** ("The current implementation calls `_collect_scalar_only_fields` for `force_select`; that line should also switch to `_walk_selections`"), as does `### Same-query recursion`'s trailing paragraph and `## Problem statement`. The symbol has zero occurrences package-wide (D1). Left standing deliberately — it is prose outside a fence and a status claim, so it is R2's call whether each becomes contract, a pointer, or a deletion.
3. **`## Missing `.py` files` is true of the change and false as a map** (D22). Untouched by R1; the whole section is R2's.
4. **The one open `spec-004` rider is now the only bullet in `## Documentation updates when O4 ships`.** R3 discharges it; the spec still carries the clause that licenses the edit, and the rationale's entry 6 records what discharged the other three.

### Spec changes made (Worker 1 only)

Cited against the **post-move** spec unless a pre-move range is given.

| Spec location (post-move) | Change | Reason |
|---|---|---|
| `:3` | Added the companion-file pointer paragraph | `BUILD.md` `## Spec rationale extraction`; form copied from `spec-001`/`spec-002`. Also carries the do-not-duplicate clause pointing at `spec-002`'s rationale. |
| `:29` (was `:27-41`) | Cut the pre-O4 dispatch fence and its lead-in; added a pointer | Rule 2 — every line quotes deleted code; carried a `TODO(spec-003…)` anchor. |
| `:67` (was `:79`) | Restated the FK-column-before-elision ordering as a requirement with its reason | Carve-out — the fence was its only carrier and there is no automated guard. |
| `:71` (was `:83-114`) | Cut the proposed same-query fence; added a pointer | Rule 2 — inline-branch shape and private helper name both falsified. |
| `:82` (was `:125`) | Restated the empty-`only_fields` guard on the connector bullet | Carve-out — existed only in the deleted helper body. |
| `:89` (was `:132`) | Added the mark-uncacheable-before-child-build ordering | Carve-out — the fence ordered it; the bullet did not. |
| `:93` (was `:134-185`) | Cut both prefetch-boundary fences; added a pointer | Rule 2. |
| `:111` (was `:203-227`) | Cut the flattening fence; restated its return shape and separator composition; added a pointer | Rule 2 + carve-out. |
| `:123` (was `:239-265`) | Cut both resolver-key fences; restated the key format, the no-parent fallback, and the resolver-side membership test; added a pointer | Rule 2 for the wrappers; carve-out for the format, which D13 confirms shipped verbatim. |
| `:189-193` (was `:330-336`) | Cut three discharged bullets and the discharged half of the fourth; retensed the lead-in; added a pointer | Discharged instructions are history. The open rider stays because R3 needs the licensing clause in the spec. |
| (was `:350-415`) | Deleted `## Implementation insertion points (O4)` and `## Anchor and lint notes` in full | The largest block of falsified present-tense prose (D21) and a section false in its entirety (D15). |
| `:225-226` | Added `[spec-002-rationale]` and `[spec-003-rationale]` link definitions | Both pointer paragraphs; alphabetical within `<!-- docs/SPECS/ -->`; targets disk-checked. |

No spec status/header line needed a `worker-1.md` `## Spec status-line re-verification` edit: spec-003 has no `Status:` / owner / target-release header block — its lines 1-5 are the title and the opening of `## Problem statement`, whose claims are status prose and R2's per the boundary above.

---

## Review (Worker 3)

**What this pass reviewed and how.** The diff under review is Worker 1's own (build plan Deviation 2 — no Worker 2 pass exists for R1), so every claim in `## Move report (Worker 1)` was re-derived rather than read. Read-only HEAD reference obtained per `BUILD.md` `## Claims are proven mechanically, never accepted on prose`: `git show HEAD:docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md > <scratch outside repo>/spec-003-HEAD.md`. No `git stash`, `git checkout`, `git restore`, or `git worktree` was run at any point.

### High:

None.

### Medium:

#### A sixth load-bearing rule lived only inside a deleted fence and was not rescued: the parent-side FK-column append at the prefetch boundary

The move report names five rules rescued from inside the seven deleted fences. There is a sixth, and it is the same shape as the five: a rule the spec stated **only** inside a fence, which is instruction rather than deliberation, and whose absence changes how the thing is built.

Pre-move spec, inside the deleted `### Prefetch-boundary recursion …` fence (`spec-003-HEAD.md:136-139`):

```docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md@HEAD:136
if relation_kind == "prefetch":
    runtime_path = (*runtime_prefix, sel.alias or sel.name)
    if django_field.attname is not None:
        _append_unique(plan.only_fields, f"{prefix}{django_field.attname}")
```

That append goes to the **parent** plan's `only_fields`, not the child's. The post-move spec never states it. `### Prefetch-boundary recursion for many-side and downgraded paths` (`docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md:76-93`) opens at "Build a child queryset for the related model" and its only connector bullet (`:82-85`) is explicitly scoped to the **child** plan — a different queryset and a different column (`parent_field.target_field.attname` on the target side, versus `prefix + attname` on the source side). `### Same-query recursion …:66` states the rule, but only for the select branch. Grep confirms no other carrier: the surviving spec's five `attname` / `connector` mentions are all child-side or `## Desired behavior` illustration.

**Why it matters.** The rule is real and live at HEAD: `django_strawberry_framework/optimizer/walker.py::_plan_prefetch_relation` opens with a call to `::_record_relation_access`, which is the shared implementation of exactly this append (`walker.py::_record_relation_access #"append_unique(plan.only_fields, f\"{prefix}{attname}\")"`). It is the same helper whose *ordering* the move report rescued as rule 1 — so the spec now documents when that helper must run on the select path while never saying the prefetch path calls it at all.

It is not a no-op. Django introspection against the fakeshop graph (read-only, `Category` / `Item`):

```text
Category   items       ManyToOneRel   attname=None
Item       category    ForeignKey     attname='category_id'
```

`attname` is `None` on a reverse relation, so the guard makes the append fire for exactly one case: a **forward FK / OneToOne downgraded to a `Prefetch` by O6**. In that case Django matches the prefetched rows by reading `obj.<field>_id` off the parent, so a parent queryset carrying a `.only(...)` projection that omits the column takes a deferred-column load per parent row — the N+1 this slice exists to remove, reappearing on the one branch the slice added.

**Where it survives today.** Only in the rationale file, as part of the prose description of the fence (`…-rationale.md:144`, "append the parent FK column"). `BUILD.md` `### Who reads it, and when` puts Worker 2 outside that file by design, so the carve-out is doing precisely the job it was written for and this rule fell through it. `worker-1.md` `### Performing the rationale move`: "When it is unclear whether a sentence is deliberation or instruction, **it stays**" — and this one is not unclear.

**Recommended change.** One clause in `### Prefetch-boundary recursion for many-side and downgraded paths`, mirroring `### Same-query recursion …`'s first bullet, e.g. a new leading bullet: *"Add the source FK column to the **parent** plan's `only_fields` using the current prefix, exactly as the same-query branch does. A reverse FK or M2M has no such column, so this fires only for a forward relation downgraded to a `Prefetch` by O6 — whose parent rows Django matches on that column, so omitting it from the parent projection reintroduces a per-row load."*

**Test expectation.** None. This is a spec-completeness defect against already-shipped, already-correct code; no behavior changes and no test is owed.

### Low:

#### `## Provenance of this record`'s **Moved** list names artifacts that did not move, contradicting the same file's **Deleted** bullet

Mechanically measured (6-word shingles, link-definition blocks and markdown punctuation stripped):

| measure | value |
|---|---|
| shingles that left the spec (HEAD minus post-move) | 1,608 |
| of those, preserved in the rationale | 87 (5.4%) |
| of those, present in neither file | 1,521 |
| fenced blocks: HEAD spec / post-move spec / rationale | 7 / 0 / **0** |

The rationale contains **no code fences at all**. What landed there for each of the seven fences and for `## Implementation insertion points (O4)` is a prose account, not the text. That disposition is defensible and I am not challenging it — the build plan authorizes it directly (`build-003-…:123`: proposed code that landed under a different name "is not deliberation and it is not contract", so `worker-1.md` rule 2 deletes rather than moves), and each per-entry body in the rationale is honest that it is describing.

The **label** is what is wrong, in the one section a later reader uses to learn what happened. `…-rationale.md:12-13` states "Text marked *Moved* below was cut out of the spec, not copied: it exists here and nowhere else", and `:43-50` puts "all **seven** fenced pseudo-code blocks" and "the whole of `## Implementation insertion points (O4)`" under **Moved**. For those items the sentence is false — the text exists nowhere. `:58-65` (**Deleted rather than moved**) then discloses the deletion of the same seven fences, so the two bullets read as contradicting each other about the same objects. The three-and-a-half `## Documentation updates when O4 ships` bullets *are* a genuine verbatim move and are correctly labelled.

**Recommended change.** Either split the fences and the insertion-point section out of **Moved** into a third category ("Deleted, with a prose account kept here"), or reword the **Moved** bullet to name what actually landed and drop "it exists here and nowhere else" for those items.

#### A stated count in `### Validation run` is wrong: 13 in-page anchors

`### Validation run` records "a slugger run over the post-move spec's headings confirms **all 13** in-page anchors the rationale targets resolve". The conclusion holds; the number does not. Measured with an independent slugger honouring the four `KANBAN.md`-catalogued defects (code spans masked to their inner text rather than deleted, `_` preserved as a word character, whitespace runs collapsed, reference-link headings unwrapped):

- rationale link definitions carrying an in-page anchor: **9**
- in-page anchor **uses** in the rationale body: **10**
- all 9 resolve against a real post-move spec heading; **0** unresolved, **0** duplicate heading slugs, **0** unused definitions, **0** undefined references

Neither 9 nor 10 is 13 and I could not derive 13 from any other population in the file. `BUILD.md` `## Claims are proven mechanically, never accepted on prose` — "A number reads as measured and every later pass treats it as measured" — so the fix is to replace it with a re-derivable figure (9 definitions / 10 uses).

### DRY findings

**None.** Both duplication risks the plan named were checked mechanically and both are clean.

- **Against `spec-002`'s rationale** (the risk `build-003-…:216` flags): 231 shared 8-word shingles out of ~4,600, and every one is the shared file *shape* the move report cites as its reused precedent — the H1 suffix, the "Deliberative companion to …" opener, `## How to read this file`, `## Provenance of this record`, the provenance paragraph. Filtering that scaffold out leaves **zero** shingles touching the O4-extraction argument. `## How to read this file` bullet 4 points at `spec-002`'s rationale for it and does not retell it, as claimed.
- **Against the spec** (copy rather than move): 39 shared 8-word shingles, all attributable — the rationale explicitly quoting surviving spec prose as the argument it is rejecting ("The pseudocode anchors now live in both `optimizer/walker.py` and `types/resolvers.py`", "either preserve the response aliases on merged nodes or record resolver keys from the original selections before merging", "walks scalar children only and silently drops any nested relation"), plus section headings and the deliberately mirrored pointer wording. **No moved block exists unmarked in both files.**

One observation rather than a finding: this rationale-file template is now on its third instance (`spec-001`, `spec-002`, `spec-003`) and is reproduced by hand each time. Whether it should become a documented template is a standing-docs question for the maintainer, not a defect in this item.

### Verification of the move report's claims

Every claim re-derived; command output quoted.

| Claim | Result |
|---|---|
| spec 34,030 → 25,008 bytes | **confirmed** — `wc -c` on the HEAD copy and the working tree |
| spec 447 → 240 lines | **confirmed** |
| rationale 453 lines / 30,545 bytes | **confirmed** |
| 17 insertions / 224 deletions | **confirmed** — `git diff --stat` reports exactly `17 insertions(+), 224 deletions(-)` |
| `check_spec_glossary.py --spec …` exit 0 | **confirmed** — `OK: 8 terms - all have glossary entries and at least one spec link.` exit 0 |
| all 8 anchors individually carry a link | **confirmed independently** — per-anchor use count is **1 at HEAD and 1 post-move for all eight** (`djangotype`, `fk-id-elision`, `metaoptimizer_hints`, `only-projection`, `optimizerhint`, `plan-cache`, `queryset-diffing`, `schema-audit`). Zero attrition; the terms CSV's 8 rows are unchanged and were not opened |
| `import_spec_terms --check` exit 0 | **confirmed** — `OK: 49 done cards have glossary links.` exit 0 |
| `check_trailing_commas --check` on all three files | **confirmed** — exit 0 (spec, rationale, and this artifact) |
| 10 link definitions disk-checked | **confirmed** — 8 distinct rationale targets + the 2 new spec definitions; all present. All 17 rationale definitions resolve, none unused, none undefined |
| 13 rationale in-page anchors resolve | **substance confirmed, count wrong** — see Low finding above (9 definitions / 10 uses) |
| no raw `path:NN` in either file | **confirmed** — `grep -nE '[a-zA-Z_/]+\.(py\|md):[0-9]+'` exits 1 on both |
| no inline `](path)` in either file | **confirmed** — PCRE grep excluding `#`/`http(s):` exits 1 on both |
| DB / `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` clean | **confirmed** — `git status --short` shows only the two intended paths plus the two Worker-0/Worker-3 builder files, after my own `import_spec_terms --check` run |
| the spec now carries zero `TODO(spec-003` anchors | **confirmed** — repo-wide sweep of `TODO\(spec-003\|TODO-(ALPHA\|BETA\|STABLE)-003` returns hits only in the rationale, the build plan, and this artifact, every one a prose quotation of the anchor string. Zero in source, tests, examples, or the spec |

### The five rescued rules, each checked against HEAD source

Each was read in the post-move spec and then traced to HEAD, asking the move report's own test: could a builder who never sees the rationale still write this correctly?

1. **FK column appended before the elision short-circuit** (`spec:67`). Matches `walker.py::_plan_select_relation`, which calls `::_record_relation_access` first and only then evaluates the four-part elision predicate. `::_record_relation_access`'s docstring carries the same invariant ("MUST run before `_can_elide_fk_id` fires … would silently drop the FK column on the elided path and reintroduce the N+1"). The spec's added closing sentence "Nothing enforces the order but the order itself" is accurate — there is no assertion or test guarding the call order, only the docstring. **Rescued correctly, and it was worth rescuing.**
2. **`if not plan.only_fields: return` on connector injection** (`spec:82`). Survives verbatim at `walker.py::_ensure_connector_only_fields`. HEAD carries an additional `if not enable_only: return` above it, which is spec-035 Decision 4 and correctly out of R1's scope. **Correct.**
3. **`cacheable = False` before the child queryset is built** (`spec:89`). `walker.py::_plan_prefetch_relation` sets `plan.cacheable = False` on the `has_custom_get_queryset` test before calling `::_build_prefetch_child_queryset`. **Correct.**
4. **The resolver-key format** (`spec:123`). `plans.py::resolver_key` is character-equivalent to the restated prose, no-parent fallback included. **Correct**, and D13's "correct verbatim, keep it" is confirmed.
5. **The resolver-side membership test** (`spec:123`). `types/resolvers.py #"if elisions and key in elisions:"` reads the context under `optimizer/_context.py #"DST_OPTIMIZER_FK_ID_ELISIONS = \"dst_optimizer_fk_id_elisions\""`. The spec's literal `info.context.dst_optimizer_fk_id_elisions` matches the constant's value. **Correct.**

Beyond these, I walked all seven deleted fences line by line against the surviving spec. Everything else in them is carried: the `sel.alias or sel.name` runtime-path convention (`spec:121`), the four-part B2 predicate (`spec:149`), the elision `continue` semantics (`spec:67`), the `prefix=""` child reset (`spec:81`), the connector-then-apply ordering (`spec:82-86`), the child-`cacheable` propagation (`spec:89`, `spec:135`), the string-and-`Prefetch` handling and `prefetch_to` composition in the flattening helper (`spec:111`, `spec:153-158`). The parent-side append above is the only gap.

### The two flagged discrepancies, adjudicated

**(a) "five fenced pseudo-code blocks" versus seven.** **Worker 1's count of seven is right; the build plan is wrong.** Mechanically: the HEAD spec carries **14** ` ``` ` markers, i.e. **7** fenced blocks, and the post-move spec carries **0**. The plan's own parenthetical at `build-003-…:123` names six locations (`### Same-query recursion`, `### Prefetch-boundary recursion` ×2, `### Lookup-path flattening`, `### Resolver sentinel keys` ×2) against a lead-in that says five, and it separately acknowledges the seventh — the `## Current state` pre-O4 quote — in its staged-anchor sweep at `:98`. So the plan is internally inconsistent and undercounts by two. **The correct number is 7**, and the rationale's `## Provenance of this record` already states seven. No action beyond recording it; `build-003-…` is Worker 0's file and I do not edit it.

**(b) `## Documentation updates when O4 ships` trimmed rather than deleted.** **The right call.** The plan calls the section "wholly discharged" at `:27` and `:124`, but its own D14 row says "(ii) **discharged but for one rider**", and `### The one authorized sibling-spec edit` (`:128-134`) both scopes that rider into R3 and grounds it on "spec-003's *own* declared documentation obligation". Deleting the section would delete the clause that licenses R3's `spec-004` edit, leaving it justified only by a `bld-*.md` artifact that `START.md` "Temp artifact conventions" says closes with its cycle — and `BUILD.md` `## Review rounds`, "Decisions live in the spec", pushes the same way. Where the plan's loose summary and its precise drift row disagree, the drift row wins. The retense of the lead-in from "When implementation lands:" to "One obligation from this list is still open:" is a necessary consequence of cutting three of the four bullets, is disclosed in `### Implementation notes`, and is not an R2 over-reach.

### The R1/R2 boundary

**Neither over-reached nor half-done.** All 17 added lines are one of: a pointer (7), a rescued rule (4), a link definition (2), or blank/lead-in (4). Not one is a status-claim rewrite. The pre-move claims R2 owns are visibly still standing, including inside sentences R1 edited — `## Current state:29` still asserts "the final relation-dispatch block still has O4 TODO anchors instead of recursing into `sel.selections`" in the very line where the fence pointer was appended, which is exactly the discipline the artifact and the rationale's `## Standing notes` describe.

Two refinements for the record rather than findings:

- The move report's `### Notes for Worker 1 … carried into R2` lists **four** items, and they are not the complete set of what R1 left standing — but the artifact does not claim they are. It frames them as "four items R1 surfaced", and `### Notes for Worker 3` bullet 3 routes the rest to the build plan's 22-row drift table by name. That partition is stated and holds: I checked D1/D2/D3/D5/D6/D12/D16/D18/D20/D22 and every one is still standing in the spec and already tabled. I found **no** surviving falsified claim that is in neither the four nor the drift table.
- R1 removed the three in-spec `TODO(spec-003` survivors the plan assigned to R2 (`build-003-…:98`). This is not an over-reach: all three rode inside fenced or sectioned text R1 was cutting, and a fence cannot be cut while keeping an anchor inside it. It is disclosed in `### Implementation notes` bullet 3. R2's assigned work is correspondingly smaller.

### Pointer coverage (rule 1)

Eight cut sites, eight pointers, all resolving. Six per-section pointers (`spec:29`, `:71`, `:93`, `:111`, `:123`, `:193`) plus the companion pointer at `spec:3`. The two sections deleted outright — `## Implementation insertion points (O4)` and `## Anchor and lint notes` — have no section left to carry a pointer, and the companion paragraph at `:3` covers both by name ("the per-file insertion-point guidance it carried for its builder, the staging convention its TODO anchors served"). Every pointer's claim lands on a real rationale entry; every rationale entry is reachable from the spec. The two entries keyed to now-deleted headings each name the surviving section their argument bears on, as `BUILD.md` `## Spec rationale extraction` requires.

### Deletions versus moves (rule 2)

No false prose was carried into the rationale as reasoning. Every factual assertion the rationale makes about HEAD was independently verified:

- "`_collect_scalar_only_fields` has **zero occurrences** package-wide" — 0 hits across `django_strawberry_framework/`, `tests/`, `examples/`.
- "the append is `append_unique`" — `walker.py::_plan_select_relation #"append_unique(plan.select_related, full_path)"`.
- "`_prefetch_lookup_paths` keeps the proposed name and its `(entries, prefix="")` signature" — `plans.py::_prefetch_lookup_paths(entries: Iterable[Any], prefix: str = "")`, exact.
- "a short-circuit on a precomputed frozenset once the plan is finalized" and "a single named reader for the Django-private `_prefetch_related_lookups`" — `plans.py::lookup_paths #"plan.finalized_lookup_paths"` and `::_consumer_prefetch_lookups`.
- "Both helpers landed **public and shared**, in the plans module" — `plans.py::resolver_key`, `::runtime_path_from_info`.
- "The path walk is depth-bounded at HEAD, which the fence's version was not" — `plans.py #"_MAX_PATH_DEPTH = 1024"`.
- "neither symbol exists" (`_is_fk_id_elided`, `_get_relation_field_name`) and "the string `O4` does not appear anywhere in the package source" — 0 hits each.
- "the rules themselves moved out to a join-taxonomy module … the reverse-one-to-one arm was also added" — `optimizer/join_taxonomy.py::_parent_join_column`, whose first arm is `if getattr(field, "one_to_many", False) or kind == "reverse_one_to_one":`.
- "Two rules that existed *only* here were checked before the cut and were both already carried elsewhere" — confirmed: `prefetch_obj`-is-a-leaf survives at `spec:96` and `:146`, and `lookup_paths`-is-not-for-strictness at `spec:129` and `:203`.

Conversely, nothing genuinely deliberative was deleted outright. The insertion-point section's two design-grade clauses — "`_build_child_queryset` should be the only place that calls target `get_queryset`" and the alias-preservation-before-`_merge_aliased_selections` requirement — both survive in the spec's own prose (`:79`, `:121`). I also checked the one conditional test obligation that existed only in the deleted section ("if `OptimizationPlan` gains a resolver-key collection, add focused tests for `is_empty` behavior and construction defaults"): it is discharged at HEAD — `tests/optimizer/test_plans.py` carries `TestOptimizationPlanIsEmpty`, `::test_plan_default_lists_use_indexed_append_unique`, and 25 `planned_resolver_keys` assertions.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**. `__all__` and the re-export list are unchanged. R1 touches no package source at all.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applicable — R1 writes a spec and an archived spec companion.

- **Version strings / statuses / card IDs:** none touched. Spec-003 carries no `Status:` / owner / target-release header, as the move report states; verified against the HEAD copy.
- **KANBAN cards:** none moved; `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, and `examples/fakeshop/db.sqlite3` are all clean in `git status --short`.
- **Links introduced by the slice point at existing files:** all 17 rationale definitions and both new spec definitions disk-checked present; all 9 anchor-bearing definitions resolve against a real post-move spec heading.
- **Archive placement:** the rationale was written directly to `docs/SPECS/appx/`, the location `AGENTS.md` rule 26 names for an archived spec's companions, never to `docs/` first. Its definitions in the spec sit under `<!-- docs/SPECS/ -->`, correct per `START.md`'s closed-list rule that a subdirectory shares its parent's group.
- **Verbatim copies from the spec:** the rationale quotes the four `## Documentation updates when O4 ships` bullets. Diffed against the HEAD copy: bullets 1 and 2 are verbatim (bullet 2 adds `**and**` emphasis inside the quotation, marking the half-discharge); bullets 3 and 4 are elided with a clearly-marked `…`. Bullet 3's elided tail ("Also update the older parent-spec O4 references in `docs/SPECS/spec-002-optimizer-0_0_2.md`") is a distinct obligation the entry does not separately address, though it is substantively discharged and covered by the entry's own item 1 — noted for Worker 1 below, not raised as a finding.
- **Obsolete "planned"/"coming soon" wording:** present and **deliberately so** — the spec's present-tense claims about the pre-implementation codebase were left standing by design, disclosed in `### Implementation notes` and in the rationale's `## Standing notes`, and assigned to R2. Correct scoping, not stale-doc drift.
- **Script-rendered docs:** none touched, so no docstring-staging check applies.

### Failability proofs

**No proof was owed and none is missing.** R1 introduces no boundary, guard, gate, or rejection path — it changes no package source (`git diff -- django_strawberry_framework/` is empty). Per `worker-3.md` "Reading is necessary, not sufficient", an **empty re-run set is legal exactly when the diff introduces no boundary that meets the floor**, which is the case here. **No boundary was re-run and none was accepted on a builder's record, because none exists.** No source mutation was made; the narrow carve-out was not exercised.

### Hot-path budget

Not applicable; the plan declares no hot path, and the item changes no runtime code.

### Static helper use

`scripts/review_inspect.py` **skipped, with reason**: `worker-3.md` "Static helper use" triggers on a slice adding a `.py` file, touching `optimizer/` or `types/` `.py`, or adding 30+/50+ lines of logic. R1's diff is two Markdown files and zero `.py` files, so no trigger fires and there is no repeated-literal or import-boundary evidence to gather. No shadow file was read or produced by this pass.

### What looks solid

- **The move is provably not a copy.** Zero unmarked shared blocks between the rationale and the post-move spec; the 39 shared shingles are all explicit quotation, headings, or the deliberately mirrored pointer wording.
- **The five rescued rules are the right five, correctly stated, and all five match HEAD.** Three of them existed only as statement order inside a fence, which is the hardest class to notice, and the reasons attached to each (why the order matters, what breaks without it) are exactly the "why that changes HOW a thing is built" the carve-out asks for.
- **The 8-anchor trap was fully avoided.** Per-anchor counts are unchanged at 1 for all eight; the CSV was not opened; the card-wrap chain (`import_spec_terms --check`) still exits 0. `build-003-…:104-117` flagged four anchors as high-risk and none of them was touched.
- **The R1/R2 boundary is drawn explicitly and held in both directions**, including inside a sentence R1 edited, and it is stated in the rationale file itself (`## Standing notes`) rather than only in a per-cycle artifact — the right place for a boundary the *next* pass has to respect.
- **The design/insertion-point contradiction over where `lookup_paths` belongs was recorded rather than silently resolved.** Deleting one of two contradicting sections is exactly where a disagreement becomes invisible; the rationale's flattening entry preserves it.
- **The pointer at `spec:3` earns its length** by enumerating the two whole sections that no longer have a heading to carry a pointer, which is what keeps rule 1 satisfied for a wholesale deletion.
- **`spec-002`'s rationale is pointed at, not duplicated** — verified mechanically, not accepted on the claim.

### Temp test verification

None created. `docs/builder/temp-tests/r1/` was not used: R1 lands no executable behavior, so there is nothing a temp test could demonstrate that reading plus the four validation commands does not. No `pytest` was run (`AGENTS.md` rule 15), and no coverage-flagged command was run in any form.

### Notes for Worker 1 (spec reconciliation)

1. **The Medium finding is a one-clause spec edit and only Worker 1 may make it.** Under Deviation 2 there is no Worker 2, so `revision-needed` routes back to Worker 1 for a fix pass rather than to a builder. The recommended clause is drafted in full under the finding.
2. **Correct the fence count wherever it is restated.** `build-003-…:27` and `:123` say "five"; the measured number is **7** (14 fence markers at HEAD). The plan is Worker 0's file — flagging it here so the correction reaches the closeout rather than being re-derived.
3. **Bullet 3's elided tail is unaddressed on its own terms.** The rationale's `## Documentation updates …` entry quotes bullet 3 truncated, dropping "Also update the older parent-spec O4 references in `docs/SPECS/spec-002-optimizer-0_0_2.md`". D14(i) records that as discharged and the entry's item 1 covers `spec-002` substantively, so nothing is owed — but if the entry is being edited anyway for the Low finding, folding the clause in costs a sentence and closes the last unaccounted-for line of that section.
4. **Carried forward to R2, unchanged:** the four items in `### Notes for Worker 1 … carried into R2` are confirmed still open and still un-pre-empted, and I found nothing that belongs to R2 outside the union of those four and the 22-row drift table.
5. **For the deferred-work catalog:** the ordering invariant now stated at `spec:67` has no automated guard at HEAD — which the build plan's correctness-audit observation 4 already records. R1 promoting it from a docstring-only invariant to a spec-level requirement is the strongest form available inside a docs cycle; whether it earns a test is the maintainer's call and out of scope here.

### Review outcome

`revision-needed`.

One Medium finding — a sixth load-bearing rule that lived only inside a deleted fence and was not rescued into the spec — plus two Low findings, none of them rejected with a recorded reason. Per `worker-3.md` "Acceptance gate", a Medium with no recorded rejection blocks acceptance; and the escalation route (`review-accepted` with the finding handed to Worker 1) is not the right instrument here, because it exists to spare a Worker 2 who lacks spec context, and this item has no Worker 2 — the fixer and the final verifier are the same worker either way. All three findings are small, mechanically specified, and confined to the two files Worker 1 already owns.

Everything else in the item verified clean: the move is provably a cut and not a copy, all 8 glossary anchors survive with zero attrition, all four validation commands re-run green, every pointer resolves, every factual claim the rationale makes about HEAD is true, and the R1/R2 boundary held in both directions.

---

## Move report (Worker 1, pass 2) — apply changes

Apply-changes pass for the three findings in `## Review (Worker 3)`. Deviation 2's 2026-08-07 corollary routes a `revision-needed` on R1 to Worker 1 rather than Worker 2, and returns the artifact to `planned`. Worker 3's two adjudications (the fence count is **7**, not the plan's five; trimming rather than deleting `## Documentation updates when O4 ships` was the right call) are accepted as recorded and not re-litigated.

### Findings closed

| Finding | Disposition |
|---|---|
| **Medium** — the parent-side FK-column append at the prefetch boundary was never rescued | **Fixed.** New leading bullet in `### Prefetch-boundary recursion for many-side and downgraded paths`, plus a full entry in the rationale's *"Kept in the spec"* list for that section. |
| **Low** — `### Validation run`'s "all 13 in-page anchors" | **Corrected below**, with the re-measurement quoted. The artifact is append-only (`ARTIFACT.md` `## Re-pass sections`), so the pass-1 figure stands where it was written and is superseded here. |
| **Low** — `## Provenance of this record` files deletions under **Moved** | **Fixed.** Three labelled categories now, and the per-entry labels were relabelled to match. |
| Worker 3's note 3 — bullet 3's elided tail | **Folded in**, as suggested, since the entry was open anyway. |

### Files touched

- `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` — one added bullet (the sixth rescued rule).
- `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` — provenance re-labelling (header paragraph + `## Provenance of this record` + eight per-entry labels), the sixth rescued rule's entry, and the `spec-002` clause folded into `## Documentation updates …` bullet 3.

### The Medium: the sixth rescued rule, as written

Added as the **first** bullet of `### Prefetch-boundary recursion for many-side and downgraded paths`, ahead of "Build a child queryset …", because that is the order the branch runs in:

> Add the source FK column to the **parent** plan's `only_fields` using the current prefix, exactly as the same-query branch does. A reverse FK or M2M has no such column on the source row, so this fires only for a forward FK or OneToOne downgraded to a `Prefetch` by O6 — and Django matches those prefetched rows by reading that column off each parent, so omitting it from the parent projection costs a deferred load per parent row and reintroduces on this branch the N+1 the slice exists to remove.

Re-derived against source rather than accepted from the review. `walker.py::_plan_prefetch_relation` opens with a `::_record_relation_access(plan, django_field, prefix, resolver_identities, enable_only=enable_only)` call — the same first statement as `::_plan_select_relation` — and that helper's body is `attname = getattr(django_field, "attname", None)` / `if enable_only and attname is not None: append_unique(plan.only_fields, f"{prefix}{attname}")`. Its docstring states the select-path ordering invariant (rescued as rule 1 last pass) and says nothing about the prefetch path, so the spec was the only place the prefetch-side call could have been recorded, and it was not.

The `enable_only` gate on that append is spec-035 Decision 4 and is deliberately **not** written into the bullet: it is a later spec's contract, and the build plan's scope trap (`build-003-…` `**The scope trap specific to this spec.**`) is explicit that spec-003 must not absorb spec-033 / spec-035 / spec-045 surface.

The rationale's entry for the rescued rule also records that this rule was missed on pass 1 and caught on pass 2 — the five that were caught and the one that was not are the same shape, and that is the most useful thing this file can say about the carve-out.

### No seventh: every deleted fence re-read line by line

`git show HEAD:docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md > <scratch outside repo>/spec-003-HEAD.md`; `grep -n '```'` gives 14 markers, i.e. **7** fences (independently re-measured, matching Worker 3). Each was read statement by statement against the post-move spec. **I did this, and the parent-side append was the only gap.**

| Fence (HEAD lines) | Every statement in it, and where it lands |
|---|---|
| 1 — `## Current state` (29-41) | Quote of pre-O4 code + a `TODO(spec-003…)` anchor. No normative content; the surrounding prose already carries the point. Nothing owed. |
| 2 — `### Same-query recursion` (85-114) | `runtime_path` from `sel.alias or sel.name` → `:122`; FK-column append → `:66`; four-part B2 predicate → `:150`; `continue` on elision → `:67`; `select_related.append(full_path)` → `:68`; recurse at `prefix=f"{full_path}__"` → `:69`; append-before-short-circuit ordering → `:67`. All carried. |
| 3 — prefetch arm (134-158) | `runtime_path` → `:122`; **parent FK-column append → NOWHERE (the Medium; now `:78`)**; `cacheable = False` before the child build → `:90`; `_build_child_queryset` → `:79-80`; fresh child plan at `prefix=""` → `:81-82`; connectors after the walk → `:83`; `child_plan.apply(child_qs)` → `:87`; `cacheable` propagation upward → `:90`; `Prefetch(full_path, queryset=child_qs)` append → `:88-89`. |
| 4 — the two helpers (160-183) | `_build_child_queryset` body (default manager, then `get_queryset` when custom) → `:79`; `if not plan.only_fields: return` → `:83`; `one_to_many` → `parent_field.field.attname` → `:84`; downgraded forward → `parent_field.target_field.attname` → `:85`; M2M → `related_model._meta.pk.attname` → `:86`. All carried. |
| 5 — `### Lookup-path flattening` (205-227) | union of `select_related` with flattened prefetch paths → `:112`; nested levels joined under the lookup separator → `:112`; plain-string vs `Prefetch` entries and the `prefetch_to`-plus-inner composition → `:157-159`; arbitrary depth → `:112`. All carried. |
| 6 — walker-side key (239-254) | Elision bag keyed by resolver key → `:26` + `:124`; `".".join(runtime_path)`, `<ParentType>.<field>@<a.b.c>`, no-parent fallback → `:124`. All carried. |
| 7 — resolver-side check (256-265) | Reads `dst_optimizer_fk_id_elisions` off the context, reconstructs the same key, tests membership → `:124`; `_runtime_path_from_info` behaviour → `:126`. All carried. |

The two wholly-deleted sections were re-walked too, and neither yields an eighth: `## Anchor and lint notes` is instruction with no normative content (D15 records it false in its entirety), and `## Implementation insertion points (O4)`'s only two design-grade clauses survive in the spec's own prose (`_build_child_queryset` as the single `get_queryset` call site → `:79`; alias preservation before `_merge_aliased_selections` → `:122`).

### The Low: `## Provenance of this record` re-labelled

Three categories now, with the vocabulary defined in the file's opening paragraph so a reader meets it before the list:

- **Moved** — text reproduced here and existing nowhere else. Now **only** the three discharged `## Documentation updates when O4 ships` bullets plus the discharged half of the fourth, which Worker 3 confirmed is a genuine verbatim move.
- **Cut, with a prose account kept here** — the seven fences, `## Implementation insertion points (O4)`, `## Anchor and lint notes`. States outright that the file carries no code fence at all and that the text survives in neither file, so a reader wanting it goes to git history. Names `worker-1.md` rule 2 as the prescribed disposition rather than an economy.
- **Deleted with no account kept** — the fences' symbol names, signatures, privacy, and file placements, and the insertion-point section's line-number framing.

The former **Deleted rather than moved** bullet is folded into the third; the contradiction Worker 3 measured (the same seven objects filed under **Moved** and under **Deleted**) is gone. Eight per-entry italic labels were relabelled `*Moved — …*` → `*Cut — …*` so the entries and the provenance section agree; the one genuine move (`## Documentation updates …`) keeps `*Moved*`. The **Restated in the spec, not moved** bullet now reads **six** rules and names the new one.

### The Low: the corrected anchor count

**`### Validation run`'s "all 13 in-page anchors" is wrong and is superseded by this measurement.** Re-measured here with an independent slugger (code spans masked to their inner text, `_` preserved as a word character, whitespace runs collapsed, reference-link headings unwrapped), against the *current* post-fix files:

```text
spec headings: 22 dupes: 0
rationale link definitions: 17
definitions carrying an in-page anchor: 9
in-page anchor USES in body: 10
unresolved: []
undefined refs: [] | unused defs: []
```

**9 anchor-bearing definitions / 10 uses in the body; all 9 resolve against a real post-move spec heading; 0 unresolved, 0 duplicate heading slugs, 0 undefined references, 0 unused definitions.** Matches Worker 3's independent figure exactly. The pass-1 conclusion (they resolve) held; only the number was wrong, and 13 is not derivable from any population in the file.

`BUILD.md` `## Claims are proven mechanically, never accepted on prose`: **measure as you write the number.** Every count in this report was produced by the command quoted beside it, in the same edit that wrote it down.

### Validation run (pass 2)

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` → `OK: 8 terms - all have glossary entries and at least one spec link.` **exit 0**.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0**.
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale> <this artifact>` → **exit 0** on all three.
- Per-anchor re-count in the spec body: all 8 anchors still at **1 body use each** (the added bullet sits in the `only-projection` carrier section and neither displaced nor duplicated its link).
- Link scaffold, both files: `<!-- LINK DEFINITIONS -->` present, all 10 canonical group headers present in the canonical order, no double blank line, trailing newline present. **10** definitions in the spec, **17** in the rationale; every non-URL target disk-checked present — **0 missing**.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files → **no match** (exit 1). Rule 27 holds.
- `grep -nP '\]\((?!#|https?:)'` over both files → **no match** (exit 1). No inline `](path)` link.
- `grep -c '```'` on the rationale → **0**. The "no code fence at all" claim in `## Provenance of this record` is measured, not asserted.
- `git status --short` → the same four paths as pass 1 (this spec, the rationale, this artifact, Worker 0's plan). `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` remain **clean**.
- No `pytest` (`AGENTS.md` rule 15), no `--cov*` flag in any form, no `ruff` (no `.py` touched). No `git stash` / `checkout` / `restore` / `worktree` at any point; the HEAD reference is `git show HEAD:<path>` into a scratch path outside the repo.

### Byte count (required report)

| | lines | bytes |
|---|---|---|
| spec at HEAD | 447 | 34,030 |
| spec after pass 1 | 240 | 25,008 |
| **spec after pass 2** | **241** | **25,510** |
| delta vs HEAD | -206 | **-8,520 (-25.0%)** |
| rationale after pass 1 | 453 | 30,545 |
| **rationale after pass 2** | **483** | **33,374** |

`git diff --stat` on the spec now reports `18 insertions(+), 224 deletions(-)` — one more insertion than pass 1's 17, which is the single rescued bullet.

### Failability proofs

None; this pass introduced no new boundary. R1 changes no package source (`git diff -- django_strawberry_framework/` is empty).

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **Why the artifact's `### Validation run` was not edited in place.** `ARTIFACT.md` `## Re-pass sections` is explicit that prior entries are never edited, and the dispatch for this pass repeats it. So the wrong number is corrected by supersession here rather than by rewriting pass 1 — which is also the honest record: a later reader should be able to see that a stated count was wrong and how it was caught.
- **Why the rationale WAS edited in place.** `worker-1.md` rule 4 makes the rationale append-only *during the build*, which protects settled entries from a later round rewriting them. This is not a later round: it is the same item's fix pass on its own defective output, before R1 has ever been accepted. Rewriting a mis-stated provenance label is the fix; appending a correction beneath it would leave the false label in the one section a future reader consults to learn what happened, which is exactly the defect Worker 3 raised.
- **The R1/R2 boundary was not moved.** The added spec bullet is a rescued rule, not a status-claim rewrite: it states what the branch must do, in the same voice as the sibling bullets, and asserts nothing about what the codebase currently is. Every falsified present-tense claim Worker 3 confirmed still standing is still standing, including the four in `### Notes for Worker 1 … carried into R2`.
- **Nothing in `docs/builder/build-003-…md` was touched** although Worker 3's note 2 asks for the fence count to be corrected there. It is Worker 0's file and outside this pass's writable set; the correction is recorded here and in the memory file so it reaches closeout.

### Notes for Worker 3 (re-review)

- **The one substantive change is the spec's new first bullet** in `### Prefetch-boundary recursion for many-side and downgraded paths`. The test that matters is the same one you applied last pass: could a builder who never reads the rationale write `_plan_prefetch_relation` correctly from the spec alone? It should now also be checkable in the other direction — the select and prefetch sections should read as stating the *same* rule about the *same* helper, differing only in what each says about the elision ordering.
- **The provenance re-label changed vocabulary, not facts.** No measurement in the file changed; "seven fences" is still seven, and the shingle populations you measured are unaffected. Worth re-checking that the *Moved* / *Cut* / *Deleted with no account kept* partition is exhaustive and disjoint over what actually left the spec.
- **The counts in this report were each produced by the command quoted next to them.** The 9/10 anchor figure is the fix for the Low, so it is the one most worth re-deriving independently.

### Notes for Worker 1 (spec reconciliation) — carried into R2

The four items from pass 1 are **unchanged and still open**; Worker 3 confirmed none is pre-empted. Two additions from this pass:

5. **The new bullet is contract, not status prose — leave it alone in R2.** It is the sixth carve-out rescue and states a requirement about the branch, not a claim about the codebase. R2's sweep should not fold it into a "what HEAD does" rewrite of the section.
6. **The fence-count correction belongs in the closeout, not in a spec edit.** `build-003-…:27` and `:123` say "five"; the measured number is **7** (14 fence markers at HEAD, independently confirmed twice). The plan is Worker 0's file.

### Spec changes made (Worker 1 only)

Cited against the **post-pass-2** spec.

| Spec location | Change | Reason |
|---|---|---|
| `:78` | Added the parent-side FK-column append as the first bullet of `### Prefetch-boundary recursion for many-side and downgraded paths` | Worker 3's Medium. Load-bearing carve-out (`worker-1.md` `### Performing the rationale move`): the rule lived only inside a deleted fence, is instruction rather than deliberation, and its loss reintroduces the N+1 on the O6-downgraded branch. Re-derived against `optimizer/walker.py::_plan_prefetch_relation` → `::_record_relation_access`. |

No other spec line changed this pass. No spec status/header line needed a `## Spec status-line re-verification` edit — spec-003 still carries no `Status:` / owner / target-release header block, re-checked against the HEAD copy at the start of this pass.

### Status

`planned` — per the build plan's Deviation 2 corollary, which returns an R1 apply-changes pass to the `planned` → Worker 3 re-review mapping. Not `built`: there is no Worker 2 on this item.

---

## Review (Worker 3, pass 2)

**What this pass reviewed and how.** Fresh invocation, no memory of pass 1; the artifact and the working-tree diff are the record. Every count and every claim in `## Move report (Worker 1, pass 2)` was re-derived, not read. Read-only HEAD reference per `BUILD.md` `## Claims are proven mechanically, never accepted on prose`: `git show HEAD:docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md > <scratch outside repo>/spec-003-HEAD.md`. No `git stash`, `git checkout`, `git restore`, or `git worktree` at any point. No `pytest`, no `--cov*` flag in any form. No source file was mutated; the narrow carve-out was not exercised.

Scope of the pass, as dispatched: the three pass-1 findings, a spot-check of the seven-fence table, the R1/R2 boundary, regression on what pass 1 cleared, and the stated counts.

### High:

None.

### Medium:

**None. The pass-1 Medium is closed.** The parent-side FK-column append is now stated in the spec at `:78`, as the first bullet of `### Prefetch-boundary recursion for many-side and downgraded paths`, ahead of "Build a child queryset ...". Re-derived independently against source rather than accepted from the report:

- `walker.py::_plan_prefetch_relation`'s first statement is `_record_relation_access(plan, django_field, prefix, resolver_identities, enable_only=enable_only)` — the same first statement as `::_plan_select_relation`, and `plan` at that call site is the **parent** plan. Confirmed by reading both function bodies.
- `walker.py::_record_relation_access` body is `attname = getattr(django_field, "attname", None)` / `if enable_only and attname is not None: append_unique(plan.only_fields, f"{prefix}{attname}")`. Its docstring states the select-path ordering invariant and says nothing about the prefetch path, so the spec was indeed the only possible carrier.
- Placement ahead of "Build a child queryset ..." matches the branch's run order at HEAD.
- Bullet `:78` and the same-query bullet `:66` now read as the same rule about the same helper, `:78` cross-referencing `:66` explicitly ("exactly as the same-query branch does"). That is the two-directional check the apply-changes pass asked for, and it holds.

**The `enable_only` omission is correct, in both directions asked.**

- *Does including it cross the scope line?* Yes. `build-003-...:171` names spec-035 and `enable_only` **verbatim** as one of four later specs spec-003 must not absorb, and says "the correct move for each is a pointer to the owning spec, not a transplanted paragraph." Writing the G2 gate into the bullet is exactly the transplant that trap forbids.
- *Is the bullet still true without it?* Yes, at the level spec-003 speaks at. The sibling bullet `:66` — pre-existing HEAD text, unmodified by R1 — also states the append with no mention of the gate, so the two branches stay symmetric, and spec-003 is a `0.0.2`-era contract that predates spec-035. Omitting the gate is the only choice consistent with the section it was added to.

### Low:

#### The new bullet's scope clause is measurably false for a forward M2M, and narrow on the second route into the branch

`spec:78` and the matching rationale entry (`...-rationale.md:192-201`) both assert that the parent-side append "fires only for a forward FK or OneToOne downgraded to a `Prefetch` by O6". The instruction half of the bullet is correct and load-bearing; this is the explanatory clause that scopes it, and it is wrong in two independent ways.

**(a) A forward `ManyToManyField` has a non-`None` `attname`, so the append does fire for M2M.** Django sets `ManyToManyField.attname = name` (there is no separate column, so `attname` falls back to the field name) — it is *not* `None` the way the reverse descriptors are. Measured across the whole fakeshop model graph:

```text
ForeignKey        n= 57  attname = '<name>_id'
OneToOneField     n= 29  attname = '<name>_id'
ManyToManyField   n= 11  attname = '<name>'      <-- NOT None
ManyToOneRel      n= 58  attname = None
ManyToManyRel     n= 12  attname = None
OneToOneRel       n= 29  attname = None
```

And driven through the real helper rather than inferred:

```text
field: ManyToManyField name: genres attname: 'genres' many_to_many: True
plan.only_fields after _record_relation_access on a FORWARD M2M: ['genres']
reverse FK loans attname None -> only_fields: []
```

A forward M2M is a many-side relation, so cardinality dispatch routes it straight to `_plan_prefetch_relation`, and the parent plan gets the *field name* appended to `only_fields`. It is harmless at runtime — `.only('genres')` compiles to `SELECT "auth_group"."id" ...`, i.e. Django silently ignores a non-column name — but the spec sentence claiming it cannot happen is false.

**(b) `force_prefetch` is a second route, not covered by "by O6".** `walker.py::_dispatch_single_relation`'s own docstring names three deciders that reach `_plan_prefetch_relation`: the cardinality dispatch, `force_select`'s custom-`get_queryset` downgrade, and `force_prefetch`. The third is a B4 hint, not O6, and it routes a **forward FK** into this branch — which spec-003 itself contemplates at `:146` ("`force_prefetch` creates a prefetch boundary even when the cardinality dispatch would select; it should follow the same prefetch-boundary recursion path").

**Why it matters, and why it is Low rather than Medium.** No behavior is at risk: the shipped code is correct and unchanged, and the bullet's *instruction* ("add the source FK column ... exactly as the same-query branch does") is right, with the fence's `attname is not None` guard adequately implied by "has no such column on the source row". What is wrong is the inference drawn from that guard — an enumeration of when the append fires, presented as fact in a standing document. `BUILD.md` `## Claims are proven mechanically, never accepted on prose` is the rule it lands under; the semantics were reasoned from and the field objects were never introspected.

**Provenance, stated plainly.** This wording originated in *pass 1's own recommended clause*, which Worker 1 adopted close to verbatim. The reviewer wrote it and the mover carried it, so it survived two passes unmeasured. That is worth recording rather than laundering.

**Recommended change.** Drop the "fires only for" enumeration and state the guard the fence actually encoded. E.g. replace the middle sentence with: *"The append is guarded on the relation having a source-row column at all (`attname is not None`), which excludes every reverse descriptor — reverse FK, reverse OneToOne, and reverse M2M. Where it does fire, Django matches the prefetched rows by reading that column off each parent, so omitting it from the parent projection costs a deferred load per parent row ..."* The same correction applies to the rationale entry's "the append fires for exactly one case" sentence. Optionally name `force_prefetch` alongside the O6 downgrade; the section lead-in at `:76` and the pre-existing connector bullet at `:85` both use the same "by O6" framing at HEAD, so **broadening the section's scope vocabulary is R2's spec-vs-HEAD job, not R1's** — R1 owes only that its own new sentence not assert something false.

**Test expectation.** None. Spec-completeness against already-shipped, already-correct code; no behavior changes and no test is owed.

#### A stated count in the pass-2 report is wrong: "Eight per-entry italic labels were relabelled"

`### The Low: '## Provenance of this record' re-labelled` states: "**Eight** per-entry italic labels were relabelled `*Moved — ...*` → `*Cut — ...*` ... the one genuine move (`## Documentation updates ...`) keeps `*Moved*`." Those two clauses cannot both hold. Measured:

```text
$ grep -noE '\*(Moved|Cut|Deleted)[^*]{0,45}' <rationale>   # per-entry labels only
 92:*Cut — the quoted code.
118:*Cut — the proposed branch.
154:*Cut — two fences.
229:*Cut — the fence.
262:*Cut — two fences.
310:*Moved — three of four bullets, plus the discharged
350:*Cut — the whole section.
374:*Cut — the whole section, 63 lines across six pac
```

Eight per-entry labels in total: **7** `*Cut*` and **1** `*Moved*`. So **seven** were relabelled, not eight — the eighth is the one that kept `*Moved*`. The re-label itself is correct and complete; only the number describing it is wrong.

This matters for the same reason the pass-1 anchor-count Low did, and slightly more here: the same report asserts two lines earlier that "**Every count in this report was produced by the command quoted beside it, in the same edit that wrote it down.**" No command is quoted beside this one, and it is the one that is wrong. `BUILD.md`: "a count asserted in the same breath as the lesson it illustrates is routinely wrong."

**Recommended change.** Supersede it in the pass-3 report (the artifact is append-only) with "seven relabelled `*Cut*`, one kept `*Moved*`, eight labelled entries in total", or restate it as the re-derivable eight-total/seven-Cut/one-Moved split.

### The three pass-1 findings, adjudicated

| Pass-1 finding | Verdict |
|---|---|
| **Medium** — sixth load-bearing rule not rescued | **Closed.** Bullet at `spec:78`, verified against `walker.py::_plan_prefetch_relation` → `::_record_relation_access`. Correct content, correct position, correct symmetry with `:66`. One false clause inside it is the Low above. |
| **Low** — "13 in-page anchors" | **Closed, and supersede-not-rewrite was the right instrument.** See below. |
| **Low** — `## Provenance` **Moved** label | **Closed** on substance; the count describing the fix is the second Low above. See below. |

**The anchor count, re-derived independently.** My own slugger (code spans masked to inner text, `_` kept as a word character, whitespace runs collapsed, reference-link headings unwrapped) reproduces the pass-2 figure exactly:

```text
spec headings: 22 dupes: 0
rationale link definitions: 17
definitions carrying an in-page anchor: 9
in-page anchor USES in body: 10
unresolved: []
undefined refs: [] | unused defs: []
```

**Supersede-not-rewrite was right.** `ARTIFACT.md` `## Re-pass sections` — "never edit prior entries" — is unqualified, and the artifact is the inter-worker contract, so a silently-corrected number would erase the evidence that a stated count was wrong and how it was caught. **Can a reader tell which number is current?** Yes: pass 1's `### Validation run` line and the pass-2 heading `### The Low: the corrected anchor count` both survive, the pass-2 section opens by quoting the superseded sentence and saying outright that it "is wrong and is superseded by this measurement", and the linear pass-1 → review → pass-2 ordering makes the later one current by construction. A reader arriving at the pass-1 line alone would be misled, but the pass-1 **review section sits between them** and flags it, so no reading order reaches the stale number without the correction. Adequate.

**The provenance re-label.** The partition is now exhaustive and disjoint over what left the spec, which is the check the pass-2 report asked for:

- **Moved** — only the three-and-a-half `## Documentation updates when O4 ships` bullets, with "This is the only category to which 'it exists here' applies."
- **Cut, with a prose account kept here** — the seven fences, `## Implementation insertion points (O4)`, `## Anchor and lint notes`; states outright that "This file carries no code fence at all" and that the text "survives in neither file, so a reader looking for it wants git history". Measured: `grep -c '```'` on the rationale returns **0**, so that claim is true.
- **Deleted with no account kept** — symbol names, signatures, privacy, file placements, and the insertion-point section's line-number framing.

The third category decomposes the second **by aspect** (what a proposal *meant* vs what it *spelled*) rather than competing with it for the same objects, and says so explicitly. The pass-1 contradiction — the same seven objects filed under both **Moved** and **Deleted** — is gone. The vocabulary is now defined in the file's opening paragraph, before the list, so a reader meets it first. The **Restated in the spec, not moved** bullet correctly reads **six** and names the new rule.

### No seventh rule: the fence table spot-checked, not accepted

`grep -n '```'` on the HEAD copy returns markers at 29, 41, 85, 114, 134, 158, 160, 183, 205, 227, 239, 254, 256, 265 — **14 markers, 7 fences**, ranges matching the report's table exactly. Post-move spec: **0**. I read fences **1, 4, 5, 6, and 7 in full this pass** (the ones the dispatch flagged as least examined last pass) and re-checked 2 and 3, statement by statement:

- **Fence 1** (`## Current state`, 29-41). Quotes `_collect_scalar_only_fields(... prefix=f"{full_path}__")`, `plan.select_related.append(full_path)`, and a `TODO(spec-003...)` anchor. All three are carried by surviving prose — `:69`, `:68`, `:29` respectively. Table row accurate: nothing owed.
- **Fence 4** (the two helpers, 160-183). `_build_child_queryset` default-manager-then-custom-`get_queryset` → `:79`/`:80`; `if not plan.only_fields: return` and its comment → `:83`; `one_to_many` → `parent_field.field.attname` → `:84`; forward demoted → `parent_field.target_field.attname` with the `to_field` caveat → `:85`; M2M → `related_model._meta.pk.attname` with the through-table note → `:86`. **All five carried.**
- **Fence 5** (flattening, 205-227). Union of `select_related` with flattened prefetch paths → `:112`; `f"{prefix}__{entry}"` separator composition → `:112`; plain-string vs `Prefetch` entries and `prefetch_to` + inner `_prefetch_related_lookups` → `:157-159`; unbounded recursion → `:112`; location next to `OptimizationPlan` → `:112`. **All carried.**
- **Fence 6** (walker-side key, 239-254). `runtime_path = (*runtime_prefix, sel.alias or sel.name)` → `:122`; elision bag keyed by resolver key → `:26` + `:124`; `".".join(runtime_path)`, `<ParentType>.<field>@<a.b.c>`, and the no-parent `<field>@<a.b.c>` fallback → `:124`. **All carried.**
- **Fence 7** (resolver-side check, 256-265). Reads `dst_optimizer_fk_id_elisions` off the context, reconstructs the same key, tests membership → `:124`; `_runtime_path_from_info` walking `info.path.prev`, dropping numeric indexes, keeping response keys → `:126`. **All carried.**
- **Fences 2 and 3** re-checked against the table; every row lands where stated, and `:78` is where the former gap now sits.

**The two wholly-deleted sections re-walked, and neither yields an eighth.** `## Anchor and lint notes` is pure staging instruction (the anchors are "already staged", `ERA001` may fire, leave the findings in place) with no normative content — D15's "false in its entirety" holds. `## Implementation insertion points (O4)` is per-file build instruction under an explicitly approximate line-number framing; its design-grade clauses all survive: `_build_child_queryset` as the single `get_queryset` call site → `:80` (the report cites `:79`; the clause is at `:80` — a navigational off-by-one in a per-cycle scratchpad, not raised), alias preservation before `_merge_aliased_selections` → `:122`, "do not use this helper for B3 resolver strictness" → `:130`, `prefetch_obj` remains a leaf → `:97`/`:147`, and the `hints.py` documentation note → `:147`.

**Conclusion: the report's table is accurate and the parent-side append was the only gap.** Verified independently, not accepted.

### The R1/R2 boundary still holds

All **18** added lines enumerated from `git diff -U0` and classified: 7 carry a pointer to the rationale, 4 are rescued rules (`:67` ordering, `:78` parent append, `:83` empty-`only_fields` guard, `:90` cacheable ordering; the flattening return-shape and the key format ride inside pointer lines `:112` and `:124`), 2 are link definitions, 5 are blank or a lead-in. **Not one is a status-claim rewrite.**

The falsified present-tense claims R2 owns are visibly still standing, including inside lines R1 edited: the `## Current state` line R1 appended a pointer to still asserts "the final relation-dispatch block still has O4 TODO anchors instead of recursing into `sel.selections`". The pass-2 report's own position — that the new bullet is contract and must **not** be swept into R2's status-claim rewrite — is correct and is recorded in both `### Notes for Worker 1 ... carried into R2` item 5 and the rationale's `## Standing notes`. It states a requirement about the branch and asserts nothing about what the codebase currently is.

The one place R1's new sentence brushes R2's territory is the "by O6" scope vocabulary, and the right disposition is to *narrow* R1's claim rather than broaden the section — recorded under the Low above and routed to R2 below.

### Regression check on what pass 1 cleared

Every one re-derived this pass, none disturbed.

| Cleared in pass 1 | Pass-2 result |
|---|---|
| The move is a cut, not a copy | **Holds.** Rationale carries 0 code fences (`grep -c '```'` → 0); the "no code fence at all" claim in `## Provenance` is measured. |
| All 8 glossary anchors, exactly 1 link each, unchanged from HEAD | **Holds, per anchor.** `djangotype`, `fk-id-elision`, `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `plan-cache`, `queryset-diffing`, `schema-audit` — all `1 -> 1` HEAD vs post-move. The new bullet sits inside the `only-projection` carrier section and neither displaced nor duplicated its link. `check_spec_glossary.py --spec ...` → `OK: 8 terms ...` exit 0. |
| Every cut site has a pointer | **Holds.** 7 pointers: companion at `:3` (naming both wholly-deleted sections) plus `:29`, `:71`, `:94`, `:112`, `:124`, `:194`. All resolve. |
| No raw `path:NN` | **Holds.** No match in either file. |
| No inline `](path)` | **Holds.** No match in either file (URL and in-page-anchor exclusions applied). |
| All 10 canonical group headers, in order | **Holds, both files.** `<!-- LINK DEFINITIONS -->` present, all 10 groups present, index order strictly increasing. |
| Link targets on disk | **Holds.** 10 spec definitions, 17 rationale definitions, **0** missing targets. 0 undefined refs, 0 unused defs. |

### Stated counts, re-derived

| Claim | Result |
|---|---|
| spec at HEAD 447 lines / 34,030 bytes | **confirmed** — `wc -lc` on the HEAD copy |
| spec after pass 2 **241 lines / 25,510 bytes** | **confirmed** — `wc -lc` on the working tree |
| `git diff --stat` **18 insertions / 224 deletions** | **confirmed** — reports exactly `18 insertions(+), 224 deletions(-)` |
| one more insertion than pass 1, being the rescued bullet | **confirmed** — `sed -n '78p' \| wc -c` is **502** bytes, and 25,510 − 25,008 = **502**. The pass-2 delta is that single line and nothing else |
| rationale **483 lines / 33,374 bytes** | **confirmed** |
| 14 fence markers at HEAD, 7 fences, 0 post-move, 0 in the rationale | **confirmed** |
| 9 anchor-bearing definitions / 10 body uses, all resolving | **confirmed independently** — reproduced exactly, including 22 headings / 0 dupes |
| 17 rationale definitions / 10 spec definitions, 0 missing | **confirmed** |
| all 8 anchors at 1 body use each | **confirmed per anchor, HEAD and post-move** |
| `check_spec_glossary` / `import_spec_terms --check` / `check_trailing_commas --check` all exit 0 | **confirmed** — `OK: 8 terms ...`, `OK: 49 done cards have glossary links.`, and exit 0 on all three files |
| DB / `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` clean | **confirmed** — `git status --short` shows only the four builder/spec paths, after my own `import_spec_terms --check` run |
| "Eight per-entry italic labels were relabelled" | **wrong** — 7 relabelled `*Cut*`, 1 kept `*Moved*`, 8 labelled entries total. See the Low above |

Fourteen of fifteen re-derive exactly. `BUILD.md` `## Claims are proven mechanically, never accepted on prose`.

### DRY findings

**None.** No new duplication this pass. The one shape worth naming is not a defect in this item: the spec bullet at `:78` and the rationale entry at `:192-201` state the same rule twice, which is correct by design — the spec states the contract, the rationale records why it was nearly lost — but it is also why the single false clause propagated into both files, so both need the same one-sentence correction.

The standing observation from pass 1 stands unchanged: the rationale-file template is now on its third hand-reproduced instance (`spec-001`, `spec-002`, `spec-003`). Whether it should become a documented template is a standing-docs question for the maintainer, not a defect here.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**. `__all__` and the re-export list are unchanged. `git diff -- django_strawberry_framework/` is empty in its entirety; R1 touches no package source.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applicable — R1 writes a spec and an archived spec companion.

- **Version strings / statuses / card IDs:** none touched. Spec-003 still carries no `Status:` / owner / target-release header block; re-verified against the HEAD copy.
- **KANBAN cards:** none moved. `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3` all clean in `git status --short` after my own read-only `import_spec_terms --check`.
- **Links:** all 27 definitions across both files disk-checked present, 0 missing; all 9 anchor-bearing definitions resolve against a real post-move spec heading.
- **Archive placement:** rationale sits at `docs/SPECS/appx/`, the location `AGENTS.md` rule 26 names; its spec-side definitions sit under `<!-- docs/SPECS/ -->` per `START.md`'s closed-list rule.
- **Obsolete "planned"/"coming soon" wording:** present and **deliberately so** — the pre-implementation status claims are R2's, disclosed in both `### Implementation notes` and the rationale's `## Standing notes`. Correct scoping, not stale-doc drift.
- **Script-rendered docs:** none touched; no docstring-staging check applies.

### Failability proofs

**No proof was owed and none is missing.** R1 introduces no boundary, guard, gate, or rejection path — it changes no package source. Per `worker-3.md` "Reading is necessary, not sufficient", an empty re-run set is legal exactly when the diff introduces no boundary that meets the floor, which is the case here. **No boundary was re-run and none was accepted on a builder's record, because none exists.** No source mutation was made.

### Hot-path budget

Not applicable; the plan declares no hot path, and the item changes no runtime code.

### Floor verification

Not applicable; plan declares floor-verification scope `none`.

### Static helper use

`scripts/review_inspect.py` **skipped, with reason**: `worker-3.md` "Static helper use" triggers on a slice adding a `.py` file, touching `optimizer/` or `types/` `.py`, or adding 30+/50+ lines of logic. This pass's diff is two Markdown files and zero `.py` files, so no trigger fires. No shadow file was read or produced.

### What looks solid

- **The Medium's fix is right on content, position, and symmetry**, and was re-derived against `walker.py` rather than accepted. Placing it ahead of "Build a child queryset ..." matches the branch's actual run order, and the select/prefetch bullets now read as one rule about one helper.
- **The `enable_only` judgement is correct and correctly reasoned.** The build plan names spec-035 and `enable_only` verbatim in its scope trap; the sibling bullet at `:66` omits the gate too. Both directions of the question land the same way.
- **The seven-fence walk is real work, honestly reported, and survives an independent spot-check of five fences plus both deleted sections.** Every mapping in the table is accurate.
- **Supersede-not-rewrite was the right call on the anchor count**, and the resulting record is legible: a reader cannot reach the stale number without passing the section that corrects it.
- **The provenance partition is now exhaustive, disjoint, and defined before it is used.** The "no code fence at all" claim is measured (`grep -c` → 0), not asserted — which is exactly the correction the pass-1 Low asked for.
- **The R1/R2 boundary held under a second edit**, including inside a line R1 had already touched, and the pass recorded the boundary for the *next* pass rather than only for this artifact.
- **Zero regression** on all seven items pass 1 cleared, each re-measured rather than carried forward.

### Temp test verification

None created. `docs/builder/temp-tests/r1/` was not used. R1 lands no executable behavior; the two verification scripts this pass ran were read-only introspection under the scratchpad outside the repo (Django field-kind `attname` census, and one direct call to `walker.py::_record_relation_access` with a throwaway `OptimizationPlan`) and are disposable — nothing to promote, and neither touched the database or any tracked file. No `pytest` was run (`AGENTS.md` rule 15).

### Notes for Worker 1 (spec reconciliation)

1. **Both Lows are one-sentence edits in files Worker 1 already owns.** Under Deviation 2 there is no Worker 2, so `revision-needed` routes back to Worker 1. The corrected clause is drafted in full under the first Low; the count correction is a supersession in the pass-3 report.
2. **Fix the false clause in both places.** `spec:78` and `...-rationale.md:192-201` carry the same "fires only for ... by O6" inference. The rationale entry is the better of the two — it at least names the `attname is not None` guard explicitly — but its "the append fires for exactly one case" sentence has the same defect.
3. **Do not broaden the section's scope vocabulary — that is R2's.** `spec:76`'s lead-in ("Reverse FK, M2M, and O6-downgraded forward relations") and the pre-existing connector bullet at `:85` ("forward FK / OneToOne demoted to Prefetch by O6") both carry the same "by O6" framing **at HEAD**, unmodified by R1. `walker.py::_dispatch_single_relation` names `force_prefetch` as a third route into this branch, and spec-003's own `:146` says `force_prefetch` "should follow the same prefetch-boundary recursion path" — so the section under-describes its own population. **Carried to R2 as a new item:** whether `:76` and `:85` should name the `force_prefetch` route alongside the O6 downgrade. R1 owes only that its own new sentence stop asserting something false.
4. **Also for R2, from the same measurement:** the parent-side append fires for a **forward M2M** and puts a non-column field name into `only_fields` (harmless — Django drops it from the compiled `SELECT` — but it is real, shipped, and undocumented). Whether the spec should say so, or whether it is a latent tidiness item for the maintainer, is a reconciliation call and out of R1's scope.
5. **Pass-1's notes 1-4 and pass-2's note 5-6 are unchanged and still open.** I re-checked and found nothing belonging to R2 outside the union of those items and the build plan's 22-row drift table. Note 6 (the fence count is 7, not the plan's five) is confirmed a third time — 14 markers at HEAD — and Worker 0 has already corrected the build plan at both sites, so it needs no further carry.
6. **For the deferred-work catalog, unchanged:** the ordering invariant at `spec:67` has no automated guard at HEAD, only a docstring. R1 promoting it to a spec-level requirement is the strongest form available inside a docs cycle; whether it earns a test is the maintainer's call.

### Review outcome

`revision-needed`.

The pass-1 Medium is **closed** — the sixth load-bearing rule is rescued, correctly placed, and verified against source rather than accepted from the report — and both pass-1 Lows are closed on substance. Two new Lows block acceptance, neither of them a repeat of a pass-1 finding:

1. The new bullet's scope clause is measurably false (a forward M2M's `attname` is its field name, not `None`, so the append does fire for M2M; and `force_prefetch` is a second route into the branch). The instruction is correct; only the enumeration around it is wrong — and the wording originated in pass 1's own recommended clause, so it has now survived two passes unmeasured.
2. "Eight per-entry italic labels were relabelled" is seven, in a report that asserts every count in it was command-produced.

Per `worker-3.md` "Acceptance gate", a Low with no recorded rejection blocks acceptance, and the `review-accepted`-with-escalation route is the wrong instrument here: it exists to spare a Worker 2 who lacks spec context, and this item has no Worker 2. The first Low also lands in the **spec** — a standing, durable document — which is where a false sentence is least acceptable and cheapest to fix now.

Everything else re-derived clean: 14 of 15 stated counts exact, all seven fences spot-checked with no eighth rule owed, all 8 glossary anchors at 1 link each with zero attrition, all four validation commands green, every pointer and every link target resolving, the provenance partition exhaustive and disjoint, and the R1/R2 boundary intact in both directions.

### Addendum: concurrent-session churn appeared mid-pass

`git status --short` was clean of everything but the four builder/spec paths for the whole of my verification work, and every measurement above was taken in that state. On the final check, immediately after appending this section, four further files were dirty:

```text
 M CHANGELOG.md
 M GOAL.md
 M README.md
 M TODAY.md
```

None was touched by this pass — R1's writable set is the two spec-side files, this artifact, and `worker-3.md` memory, and this pass wrote only to this artifact. Per `AGENTS.md` rule 34 and `START.md` "Concurrent sessions" this is another session's work: **out of scope, not reverted, not tidied.** Recorded so the next pass does not read it as R1 output. The tracked binary/generated files R1's own checks depend on — `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md` — remain **clean**, so no measurement above is affected.

---

## Move report (Worker 1, pass 3) — apply changes

Apply-changes pass for the two Low findings in `## Review (Worker 3, pass 2)`. Deviation 2's corollary routes an R1 `revision-needed` to Worker 1 and returns the artifact to `planned`. Worker 3's pass-2 adjudications — the pass-1 Medium closed, both pass-1 Lows closed, the `enable_only` omission correct in both directions, the seven-fence table accurate with no eighth rule owed, the R1/R2 boundary intact — are accepted as recorded and not re-litigated.

**Every count below was produced by the command quoted beside it, in the same edit that wrote it down.** Both of this item's counting failures (pass 1's "13 anchors", pass 2's "eight relabelled") were numbers written without a command, so this pass quotes the command for every figure including the ones nothing has challenged.

### Findings closed

| Finding | Disposition |
|---|---|
| **Low** — the rescued bullet's scope clause is measurably false (forward M2M appends; `force_prefetch` is a second route) | **Fixed** in the spec at `:78` and in the matching rationale entry. The enumeration is replaced by the guard the branch actually applies; the two scope questions the measurement raised are handed to R2. |
| **Low** — "Eight per-entry italic labels were relabelled" is seven | **Superseded below** with the command. `ARTIFACT.md` `## Re-pass sections` — the pass-2 figure stands where it was written. |

### Files touched

- `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` — one bullet rewritten (`:78`), the same bullet pass 2 added. No other line changed.
- `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` — the *"Kept in the spec"* entry for the parent-side append corrected to match; a new `## Standing notes` subsection recording the two R2 questions the measurement raised; and one word in that section's lead-in (`Neither` → `None`, which the third subsection falsified).

### The Low: the scope clause, measured rather than reasoned

The bullet pass 2 added asserted the append "fires only for a forward FK or OneToOne downgraded to a `Prefetch` by O6". Both halves of that enumeration are false, and both were re-derived here rather than accepted from the review.

**(a) A forward `ManyToManyField` passes the guard.** A census over the whole fakeshop model graph, driven through `django.apps.apps.get_models()` and reading `hasattr(f, "attname")` per field (script under the scratchpad outside the repo):

```text
ForeignKey           hasattr(attname)=True  n=57   e.g. LogEntry.user -> 'user_id'
OneToOneField        hasattr(attname)=True  n=29   e.g. MembershipCard.patron -> 'patron_id'
ManyToManyField      hasattr(attname)=True  n=11   e.g. Group.permissions -> 'permissions'
ManyToManyRel        hasattr(attname)=False n=12   e.g. Permission.group -> '<ABSENT>'
ManyToOneRel         hasattr(attname)=False n=58   e.g. User.logentry -> '<ABSENT>'
OneToOneRel          hasattr(attname)=False n=29   e.g. Patron.card -> '<ABSENT>'

Book.genres: ManyToManyField hasattr(attname)=True attname='genres' many_to_many=True one_to_many=False
Book.loans:  ManyToOneRel    hasattr(attname)=False attname='<ABSENT>' many_to_many=False one_to_many=True
```

Two corrections fall out. The excluded set is **the three reverse descriptors**, not "a reverse FK or M2M": a forward M2M carries `attname` equal to its own field name and therefore appends. And the reverse descriptors do not carry `attname is None` — they carry **no `attname` attribute at all**, which is why `walker.py::_record_relation_access` reads it as `getattr(django_field, "attname", None)` rather than touching it directly. Both the spec bullet and the rationale entry said `None`.

**(b) `force_prefetch` is a second route into the branch.** `walker.py::_dispatch_single_relation`'s own docstring names three deciders reaching `_plan_prefetch_relation` — "the cardinality dispatch in `_walk_selections` (`plan_relation`'s verdict), and the two hint branches in `_apply_hint` (`force_select`'s custom-`get_queryset` downgrade and `force_prefetch`)". The third routes a **forward FK** across the boundary and is a B4 hint, not O6; this spec describes it at `### B4 optimizer hints` (`:146`).

**What the bullet says now.** The enumeration is gone and the guard is stated in its place, which is what the fence actually encoded:

> Guard the append on the relation carrying a source-row attribute name (`attname`) at all: the reverse descriptors — reverse FK, reverse OneToOne, reverse M2M — carry none, so nothing is appended for them. The case that makes the append load-bearing is a forward FK or OneToOne that reaches this branch instead of the same-query one, whether downgraded to a `Prefetch` by O6 or forced across by a `force_prefetch` hint: Django matches those prefetched rows by reading that column off each parent, so omitting it from the parent projection costs a deferred load per parent row and reintroduces on this branch the N+1 the slice exists to remove.

The **instruction half is untouched** — "Add the source FK column to the **parent** plan's `only_fields` using the current prefix, exactly as the same-query branch does" is the rescued rule and still opens the bullet. Only the sentence scoping it changed.

Two scope guards held, both already adjudicated and neither re-opened:

- **`enable_only` stays out.** It is spec-035 Decision 4, the build plan's scope trap forbids absorbing a later spec's surface, and the sibling bullet at `:66` omits it too. Worker 3 confirmed the omission correct in both directions.
- **`:76` and `:85` were not broadened.** Both carry the same "by O6" framing at HEAD, unmodified by R1, so re-scoping the section's vocabulary is R2's spec-vs-HEAD job. R1 owed only that its own new sentence stop asserting something false, and the new sentence names the second route only as a property of the case it is describing, not as a rewrite of the section's population.

The rationale entry carried the same clause near-verbatim — Worker 3 noted it originated in pass 1's own recommended wording and was adopted into both files — so it was corrected in the same pass, including the `attname is None` error and a sentence recording the forward-M2M append. The entry also now records that the clause was **wrong on pass 2 and measured on pass 3**, and why: the review that drafted it and the custodian that adopted it both reasoned from the guard's semantics instead of introspecting the field objects.

### The Low: the relabelling count, superseded

Pass 2 stated "**Eight** per-entry italic labels were relabelled `*Moved — …*` → `*Cut — …*` … the one genuine move keeps `*Moved*`". Worker 3 is right that those two clauses cannot both hold. Re-measured here, anchored so the population is the per-entry labels and nothing else (the vocabulary definitions in the opening paragraph and the three `## Provenance of this record` bullets are inline, never at column 1):

```text
$ grep -nE '^\*(Moved|Cut|Deleted)' <rationale>
 92:*Cut — the quoted code.* …
118:*Cut — the proposed branch.* …
154:*Cut — two fences.* …
240:*Cut — the fence.* …
273:*Cut — two fences.* …
321:*Moved — three of four bullets, plus the discharged half of the fourth.* …
361:*Cut — the whole section.* …
385:*Cut — the whole section, 63 lines across six package modules and four test modules.* …
$ grep -cE '^\*(Moved|Cut|Deleted)' <rationale>   # 8
$ grep -cE '^\*Cut'                <rationale>   # 7
$ grep -cE '^\*Moved'              <rationale>   # 1
```

**Eight labelled entries in total: seven now read `*Cut*`, one keeps `*Moved*`. Seven were relabelled, not eight.** The re-label itself was correct and complete; only the number describing it was wrong. (Line numbers have shifted from Worker 3's reading because this pass's rationale edits sit above several of them; the population and the split are identical.)

### Validation run (pass 3)

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` → `OK: 8 terms - all have glossary entries and at least one spec link.` **exit 0**.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0**.
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale> <this artifact>` → **exit 0** on all three.
- Per-anchor body-use count in the spec, measured per anchor rather than trusted to the green check: `glossary-djangotype`, `glossary-fk-id-elision`, `glossary-metaoptimizer-hints`, `glossary-only-projection`, `glossary-optimizerhint`, `glossary-plan-cache`, `glossary-queryset-diffing`, `glossary-schema-audit` — **1 body use each**, unchanged. The rewritten bullet sits inside the `only-projection` carrier section and neither displaced nor duplicated its link.
- Anchor resolution, independent slugger (code spans masked to inner text, `_` kept as a word character, whitespace runs collapsed, reference-link headings unwrapped, fenced regions skipped):

```text
spec headings: 22 dupes: []
rationale link definitions: 17
definitions carrying an in-page anchor: 9
in-page anchor USES in body: 10
unresolved: []
undefined refs: [] | unused defs: []
```

- Link scaffold, both files: `<!-- LINK DEFINITIONS -->` present, all 10 canonical group headers present in strictly increasing order, trailing newline present, no double blank line. **10** definitions in the spec, **17** in the rationale; every non-URL target resolved on disk — **0 missing**.
- `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both files → no match (**exit 1**). `AGENTS.md` rule 27 holds; the source references added this pass are symbol-qualified.
- `grep -nP '\]\((?!#|https?:)'` over both files → no match (**exit 1**). No inline `](path)` link.
- `grep -c '```'` on the rationale → **0**. The "no code fence at all" claim in `## Provenance of this record` remains true.
- `git status --short` → the four builder/spec paths plus the concurrent session's four (`CHANGELOG.md`, `GOAL.md`, `README.md`, `TODAY.md`, recorded in the build plan's `## Baseline-dirty out-of-scope files`; neither edited nor reverted). `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md` remain **clean** after this pass's read-only `import_spec_terms --check`.
- No `pytest` (`AGENTS.md` rule 15), no `--cov*` flag in any form, no `ruff` (no `.py` touched). No `git stash` / `checkout` / `restore` / `worktree`; the HEAD reference is `git show HEAD:<path>` into a scratch path outside the repo.

### Byte count (required report)

`wc -lc` on the working tree and on the HEAD copy:

| | lines | bytes |
|---|---|---|
| spec at HEAD | 447 | 34,030 |
| spec after pass 2 | 241 | 25,510 |
| **spec after pass 3** | **241** | **25,786** |
| delta vs HEAD | -206 | **-8,244 (-24.2%)** |
| rationale after pass 2 | 483 | 33,374 |
| **rationale after pass 3** | **511** | **35,645** |

`git diff --stat` on the spec still reports `18 insertions(+), 224 deletions(-)` — unchanged from pass 2, because this pass rewrote a line pass 2 had already added rather than adding one. The whole spec-side delta is that one bullet: `sed -n '78p' <spec> | wc -c` is **778** bytes against pass 2's 502, and 25,786 - 25,510 = **276** = 778 - 502.

The rationale is untracked, so `git diff --stat` does not see it; its figures are `wc -lc` readings.

### Failability proofs

None; this pass introduced no new boundary. R1 changes no package source (`git diff -- django_strawberry_framework/` is empty).

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **Why the fix states a guard rather than a corrected enumeration.** An enumeration of when a guard fires is a second statement of the guard, and it is the one that goes stale — it has now been wrong twice in the same sentence. Stating the guard itself (`attname` present at all) is shorter, is what the deleted fence encoded, and cannot be falsified by a field kind nobody thought to check. The consequence clause still names the case that makes the append load-bearing, because that is the "why that changes HOW a thing is built" the carve-out asks for.
- **Why the forward-M2M observation went to the rationale and R2 rather than into the bullet.** The append is real, shipped, and harmless — `.only('genres')` names no column and Django drops it from the compiled `SELECT`. Documenting a harmless side effect in a contract bullet would broaden the section's population claim, which the dispatch and Worker 3 both reserve to R2. The rationale records the measurement and `## Standing notes` hands the question over, so R2 does not have to re-derive it.
- **Why one word of `## Standing notes`' lead-in changed.** It opened "**Neither** of these is a deferral"; the section already carried three subsections and this pass adds a fourth. The word was falsified by the addition, so it was corrected in the same edit rather than left as a new inaccuracy in a durable file.
- **The rationale was again edited in place, for the reason pass 2 recorded.** `worker-1.md` rule 4's append-only protects settled entries from a *later round*; this is the same item's fix pass on its own defective output, before R1 has been accepted. Appending a correction beneath a false clause would leave the false clause in the entry a future reader consults.
- **Nothing in `docs/builder/build-003-…md` was touched.** Worker 3's pass-2 note 5 records that Worker 0 has already corrected the fence count there; nothing further is owed and the file is outside this pass's writable set in any case.

### Notes for Worker 3 (re-review)

- **The one substantive change is `spec:78`'s scope sentence.** The instruction half is byte-identical to pass 2's; the middle sentence is new. Worth checking in both directions: that it no longer asserts anything a field-kind census contradicts, and that it still tells a builder who never reads the rationale to make the append and why it matters.
- **The rationale's matching entry was corrected in the same terms**, plus a `## Standing notes` subsection carrying the two questions to R2. Worth confirming the two files now say the same thing and that neither has acquired a claim the other lacks.
- **Every count in this report is quoted with its command**, the ones nothing challenged included. The relabel split (8 total / 7 `*Cut*` / 1 `*Moved*`) and the 276-byte spec delta are the two most worth re-deriving, since the first is the finding and the second is the only mechanical check that the pass changed exactly one line.

### Notes for Worker 1 (spec reconciliation) — carried into R2

Pass-1 items 1-4 and pass-2 items 5-6 are unchanged and still open. Two additions, both from this pass's measurement and both explicitly out of R1's scope:

7. **Whether `:76` and `:85` should name the `force_prefetch` route alongside the O6 downgrade.** `### Prefetch-boundary recursion for many-side and downgraded paths`'s lead-in ("Reverse FK, M2M, and O6-downgraded forward relations cross a queryset boundary") and its connector bullet ("forward FK / OneToOne demoted to Prefetch by O6") both carry that framing **at HEAD**, unmodified by R1. `walker.py::_dispatch_single_relation`'s docstring names three deciders, and this spec's own `### B4 optimizer hints` bullet says `force_prefetch` "should follow the same prefetch-boundary recursion path" — so the section under-describes its own population. That is a spec-vs-HEAD call, i.e. R2's.
8. **Whether the spec should document that a forward M2M appends a non-column name to the parent's `only_fields`.** Django sets `ManyToManyField.attname` to the field's own name, so the parent-side append fires for a forward M2M and puts `'genres'`-shaped entries into `only_fields`. Django drops them from the compiled `SELECT`, so nothing is broken — but it is real, shipped, and undocumented. R2 decides whether the spec says so or whether it is a tidiness item for the maintainer. Recorded in the rationale's `## Standing notes` so it survives this artifact.

### Spec changes made (Worker 1 only)

Cited against the **post-pass-3** spec.

| Spec location | Change | Reason |
|---|---|---|
| `:78` | Replaced the scope clause of the parent-side FK-column append bullet: the "fires only for a forward FK or OneToOne downgraded to a `Prefetch` by O6" enumeration becomes a statement of the `attname`-present guard plus the case that makes the append load-bearing, naming both the O6 downgrade and the `force_prefetch` route | Worker 3's pass-2 Low. The enumeration was false in two independent ways, measured here: a forward `ManyToManyField` carries `attname` equal to its field name and therefore appends, and `walker.py::_dispatch_single_relation` names `force_prefetch` as a third decider reaching `::_plan_prefetch_relation`. The instruction half of the bullet — the rescued carve-out rule — is unchanged. |

No other spec line changed this pass. No spec status/header line needed a `worker-1.md` `## Spec status-line re-verification` edit: spec-003 still carries no `Status:` / owner / target-release header block, re-checked against the HEAD copy at the start of this pass.

### Status

`planned` — per the build plan's Deviation 2 corollary, which returns an R1 apply-changes pass to the `planned` → Worker 3 re-review mapping. Not `built`: there is no Worker 2 on this item.

---

## Review (Worker 3, pass 3)

**What this pass reviewed and how.** Fresh invocation, no memory of passes 1 and 2; the artifact and the working-tree diff are the record. Every count and every claim in `## Move report (Worker 1, pass 3)` was re-derived, not read. Read-only HEAD reference per `BUILD.md` `## Claims are proven mechanically, never accepted on prose`: `git show HEAD:docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md > <scratch outside repo>/spec-003-HEAD.md`. No `git stash`, `git checkout`, `git restore`, or `git worktree` at any point. No `pytest`, no `--cov*` flag in any form. No source file was mutated; the narrow carve-out was not exercised.

Scope of the pass, as dispatched: the two pass-2 Lows, the R2 hand-off's presence on disk in both places, regression on everything cleared across passes 1 and 2, and the stated counts.

### High:

None.

### Medium:

None.

### Low:

**None. Both pass-2 Lows are closed, and I am not raising a new one.** This is the third pass on a documentation item; `BUILD.md` `## Severity definitions` reserves Low for issues that are not load-bearing, and nothing surviving this pass would mislead a future reader or a future builder.

### The two pass-2 findings, adjudicated

#### Low 1 — the rescued bullet's scope clause was measurably false. **Closed, and the fix is right on the merits.**

Judged on the three questions the dispatch names, not on the report's account of them.

**Is the surviving sentence still the load-bearing rule that was rescued?** Yes, and byte-identically so. The instruction half of `spec:78` is character-for-character the sentence pass 2 added — re-derived by stripping the `> ` from the pass-2 report's own blockquote (`bld-003-…:423`) and the `- ` from `spec:78`, then comparing the text up to and including `does.`: **identical, 128 characters**. Only the sentence scoping it changed. The rule the Medium rescued — *the parent-side FK-column append happens on this branch too* — is untouched, still the first bullet, still ahead of "Build a child queryset ...", still cross-referencing the same-query branch.

**Is it now true?** Yes, re-derived from the field objects rather than from the report. A census over the whole fakeshop model graph (`django.apps.apps.get_models()`, every `is_relation` field, `hasattr(f, "attname")` per field):

```text
ForeignKey             hasattr=True  attname_is_None=False n= 57  e.g. LogEntry.user -> 'user_id'
GenericForeignKey      hasattr=True  attname_is_None=False n=  1  e.g. TaggedItem.content_object -> 'content_object'
GenericRelation        hasattr=True  attname_is_None=False n=  3  e.g. Branch.tags -> 'tags'
ManyToManyField        hasattr=True  attname_is_None=False n= 11  e.g. Group.permissions -> 'permissions'
ManyToManyRel          hasattr=False attname_is_None=False n= 12  e.g. Permission.group -> '<ABSENT>'
ManyToOneRel           hasattr=False attname_is_None=False n= 58  e.g. User.logentry -> '<ABSENT>'
OneToOneField          hasattr=True  attname_is_None=False n= 29  e.g. MembershipCard.patron -> 'patron_id'
OneToOneRel            hasattr=False attname_is_None=False n= 29  e.g. Patron.card -> '<ABSENT>'
```

Both of the pass-3 report's corrections check out, and the second one — which the pass-2 review did **not** name — is the sharper of the two. The excluded set is exactly the three reverse descriptors, and they carry **no `attname` attribute at all**; `attname is None` never occurs for any relation kind in the graph. That is why `walker.py::_record_relation_access` reads `getattr(django_field, "attname", None)` and why the deleted fence's literal `django_field.attname is not None` would have raised `AttributeError` on every reverse relation. The new bullet describes HEAD's actual guard rather than the fence's spelling, which is a net improvement over what was rescued, not merely a repair.

The second route is real too. `walker.py::_dispatch_single_relation`'s docstring names three deciders, and I read the two hint sites rather than the docstring: `_apply_hint` dispatches `force_prefetch` with `prefer_prefetch=True` unconditionally (no cardinality restriction, so a forward FK reaches `_plan_prefetch_relation`), and `force_select` dispatches with `prefer_prefetch=_target_has_custom_get_queryset(target_type)`, which is the O6 downgrade arriving through a hint. The bullet's "whether downgraded to a `Prefetch` by O6 or forced across by a `force_prefetch` hint" covers both.

**Did deleting the enumeration lose anything a builder needed?** No — and the report's reasoning for deleting rather than repairing it is correct. An enumeration of *when* a guard fires is a second statement of the guard, derived from it, and it is the derived copy that rots: it has now been wrong twice in the same sentence. What a builder needs from this bullet is (i) make the append, (ii) guard it, (iii) know why it matters. All three survive, and (ii) is strictly **more** implementable than before: "guard on `attname` being present" is a line of code, while "fires only for a forward FK or OneToOne downgraded by O6" is a fact a builder would have to re-derive a guard from. The consequence clause — Django matching prefetched rows on that column off each parent, and the deferred load per parent row if it is unprojected — is intact, which is the "why that changes HOW a thing is built" the carve-out asks for.

**The rationale's matching entry says the same thing and has acquired no claim the spec lacks.** `…-rationale.md:191-219` carries the same guard, the same two routes, plus three things that correctly belong only on that side: the `getattr` explanation, the forward-M2M measurement, and the record that the clause was wrong on pass 2 and measured on pass 3. Read in both directions, neither file now asserts something the other contradicts.

One residue, recorded rather than raised: the bullet glosses the guard as "the relation carrying a source-row attribute name (`attname`)", and for a forward M2M `attname` is present but names no source-row column. The operative content — guard on `attname` — is exactly HEAD's code, and the M2M nuance is measured, written into the rationale, and handed to R2 as item 8. That is the correct disposition for a section-population question, not a defect in R1's own sentence.

#### Low 2 — "eight labels relabelled" where it was seven. **Closed, and the anchored population is the right one.**

Re-derived independently, and the methodological note is correct:

```text
$ grep -cE '^\*(Moved|Cut|Deleted)' <rationale>   # 8   (per-entry labels)
$ grep -cE '^\*Cut'                <rationale>    # 7
$ grep -cE '^\*Moved'              <rationale>    # 1
$ grep -coE  '\*(Moved|Cut|Deleted)' <rationale>  # 13  (unanchored)
```

Eight labelled entries, seven now `*Cut*`, one keeping `*Moved*` — so seven were relabelled. Anchoring at column 1 is the right population and not a convenient one: the claim it measures is about **per-entry italic labels**, and I enumerated all five extra hits the unanchored regex picks up to confirm none of them is one. They are the two vocabulary definitions in the opening paragraph (`:14`, `:15`) and the three `## Provenance of this record` category bullets (`:48`, `:52`, `:65`) — all inline mid-sentence, all describing the vocabulary rather than labelling an entry. 8 + 5 = 13 exactly, so the pass-2 review's unanchored 13 and this pass's anchored 8 are reconciled rather than merely different.

Supersede-not-rewrite is again the right instrument, for the reason pass 2 recorded and I re-checked: the pass-2 sentence stands where it was written, the pass-3 section opens by quoting and correcting it, and the pass-2 **review section sits between them**, so no reading order reaches the stale number without the correction.

### The R2 hand-off is on disk in both places

`BUILD.md` `### Cohorting, naming, and closure` is explicit that detail living only in a subagent's return report does not reach the next worker, so this was checked on disk rather than in the report.

| Item | In the artifact | In the rationale (survives this artifact) |
|---|---|---|
| 7 — should `:76` / `:85` name the `force_prefetch` route alongside the O6 downgrade | `### Notes for Worker 1 … carried into R2` item 7 | `## Standing notes` → `### Two scope questions this pass raised and did not answer`, second bullet |
| 8 — should the spec document that a forward M2M appends a non-column name | same section, item 8 | same subsection, first bullet |

Both are present, both name the measurement they fall out of, and both state plainly that the call is the reconciliation item's. The `## Standing notes` lead-in was correspondingly corrected from "**Neither** of these is a deferral" to "**None** of these is a deferral" — the section now carries four subsections, so the pass's own addition had falsified the word. Correcting it in the same edit is right: leaving it would have planted a fresh inaccuracy in a durable file.

### Regression check on everything cleared across passes 1 and 2

Every item re-measured this pass, none carried forward on a prior pass's word.

| Cleared previously | Pass-3 result |
|---|---|
| The move is a cut, not a copy | **Holds.** `grep -c '```'` → **14 markers at HEAD (7 fences)**, **0** in the post-move spec, **0** in the rationale. Shingle census (8-word, link blocks and markdown punctuation stripped): **1,671** shingles left the spec, **78** survive in the rationale, **1,593** in neither. The 57 shared spec/rationale shingles decompose into **12 contiguous runs**, every one attributable — 3 are the repeated section heading, 4 are the rationale explicitly quoting surviving spec prose as the argument it addresses, 2 are the deliberately mirrored pointer wording, 1 is the flattening return-shape description, 1 is the `:67` ordering rule the rationale narrates, and 1 (23 words) is the corrected clause deliberately stated in both files. **No unmarked moved block exists in both files.** |
| All 8 glossary anchors carry exactly 1 link each, unchanged from HEAD | **Holds, per anchor.** `djangotype`, `fk-id-elision`, `metaoptimizer-hints`, `only-projection`, `optimizerhint`, `plan-cache`, `queryset-diffing`, `schema-audit` — **2 → 2** occurrences each (1 body use + 1 definition), HEAD vs post-move. The rewritten bullet sits inside the `only-projection` carrier section and neither displaced nor duplicated its link. |
| Every cut site has a pointer | **Holds.** 7 pointers at `:3`, `:29`, `:71`, `:94`, `:112`, `:124`, `:194` — the same seven positions pass 2 enumerated, which is itself independent evidence that no line was inserted or removed since pass 2. All resolve. |
| The seven-fence walk found no eighth rule | **Holds.** I re-read fences 3 and 4 (the pair that produced the Medium) statement by statement against the current spec: `runtime_path` → `:122`; parent FK append → `:78`; `cacheable = False` before the child build → `:90`; `_build_child_queryset` → `:79`/`:80`; child plan at `prefix=""` → `:81`/`:82`; connectors after the walk → `:83`; `child_plan.apply` → `:87`; `cacheable` propagation → `:90`; `Prefetch(...)` append → `:88`/`:89`; and all five helper-fence rules → `:79`, `:83`, `:84`, `:85`, `:86`. Nothing owed. The other five fences were verified in full by pass 2 and pass 3 changed no fence disposition. |
| The provenance partition is exhaustive and disjoint | **Holds.** *Moved* is now only the three-and-a-half `## Documentation updates` bullets ("This is the only category to which 'it exists here' applies"); *Cut, with a prose account kept here* covers the seven fences and both wholly-deleted sections and states "This file carries no code fence at all" — measured true, `grep -c` → 0; *Deleted with no account kept* decomposes the second by aspect (what a proposal *spelled*) rather than competing for the same objects. The fifth and sixth bullets (*Restated in the spec, not moved*, reading **six** rules, and *Deliberately left in the spec*) close the partition over everything that left or stayed. |
| No raw `path:NN` | **Holds.** `grep -nE '[a-zA-Z_/]+\.(py\|md):[0-9]+'` → no match, exit 1, both files. |
| No inline `](path)` | **Holds.** `grep -nP '\]\((?!#\|https?:)'` → no match, exit 1, both files. |
| All 10 canonical group headers in order, both files | **Holds.** `<!-- LINK DEFINITIONS -->` present in both; all ten headers present with strictly increasing line indexes (spec `:213…:241`, rationale `:476…:511`); trailing newline present, no double blank line. |
| Link targets on disk | **Holds.** 10 spec definitions and 17 rationale definitions, every non-URL target `os.path.exists`-checked from the source file's own directory — **0 missing**. 0 undefined refs, 0 unused defs. |
| The R1/R2 boundary intact in both directions | **Holds.** All 18 added lines re-enumerated from `git diff -U0` and classified: 7 pointers, 4 rescued rules (`:67`, `:78`, `:83`, `:90`), 2 link definitions, 5 blank or lead-in. **Not one is a status-claim rewrite.** The `## Current state` line R1 appended a pointer to still asserts "the final relation-dispatch block still has O4 TODO anchors instead of recursing into `sel.selections`", and `:76` / `:85` still carry their HEAD "by O6" framing unmodified — which is exactly what items 7 and 8 hand to R2. |

### Stated counts, re-derived

Every figure produced by the command beside it, in the same edit that wrote it down.

| Claim | Result |
|---|---|
| spec at HEAD **447 lines / 34,030 bytes** | **confirmed** — `wc -lc` on the HEAD copy |
| spec after pass 3 **241 lines / 25,786 bytes** | **confirmed** — `wc -lc` on the working tree |
| rationale after pass 3 **511 lines / 35,645 bytes** | **confirmed** — `wc -lc` |
| `git diff --stat` **18 insertions / 224 deletions**, unchanged from pass 2 | **confirmed** — reports exactly `18 insertions(+), 224 deletions(-)`; 18 added lines enumerated individually |
| `sed -n '78p' \| wc -c` is **778** against pass 2's **502**, and 25,786 − 25,510 = **276** = 778 − 502 | **confirmed, and the pass-2 term re-derived rather than assumed.** 778 measured directly. The 502 was reconstructed from the pass-2 report's own blockquote of the bullet (`:423`), `> ` stripped: **502 bytes** including the newline (500 characters + 2 for the one em dash's UTF-8 width). 778 − 502 = 276 = 25,786 − 25,510. With the line count unchanged at 241 and all seven pointer positions identical to pass 2's, **the arithmetic does prove that exactly one line changed** |
| 14 fence markers at HEAD, 7 fences, 0 post-move, 0 in the rationale | **confirmed** |
| 8 labelled entries / 7 `*Cut*` / 1 `*Moved*` | **confirmed**, and the 13-vs-8 discrepancy fully reconciled — see Low 2 |
| 9 anchor-bearing definitions / 10 body uses, 22 headings, 0 dupes, all resolving | **confirmed independently** — my own slugger (code spans masked to inner text, `_` kept as a word character, whitespace runs collapsed, reference-link headings unwrapped, fenced regions skipped) reproduces every line of the report's block exactly |
| 17 rationale definitions / 10 spec definitions, 0 missing | **confirmed** |
| all 8 anchors at 1 body use each | **confirmed per anchor, HEAD and post-move** |
| `check_spec_glossary` / `import_spec_terms --check` / `check_trailing_commas --check` all exit 0 | **confirmed** — `OK: 8 terms - all have glossary entries and at least one spec link.`, `OK: 49 done cards have glossary links.`, exit 0 on all three files |
| DB / `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` clean | **confirmed** — all four absent from `git status --short` after my own read-only `import_spec_terms --check` |

**Fifteen of fifteen re-derive exactly.** Both of this item's counting failures were numbers written without a command; this report quotes a command for every figure, and every one holds.

### DRY findings

**None.** No new duplication this pass. The one doubling — the same rule stated at `spec:78` and `…-rationale.md:191-219` — is correct by design (the spec carries the contract, the rationale carries why it was nearly lost) and is precisely why the false clause had to be corrected in both files, which it was, in the same terms.

The standing observation from passes 1 and 2 is unchanged and is not a defect in this item: the rationale-file template is now on its third hand-reproduced instance (`spec-001`, `spec-002`, `spec-003`). Whether it should become a documented template is a standing-docs question for the maintainer.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**. `__all__` and the re-export list are unchanged. `git diff --stat -- django_strawberry_framework/ tests/` is empty in its entirety; R1 touches no package source and no test.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. (`CHANGELOG.md` is dirty from a concurrent session and is in the build plan's `## Baseline-dirty out-of-scope files`; it was neither read into scope, edited, nor reverted.)

### Documentation / release sanity

Applicable — R1 writes a spec and an archived spec companion.

- **Version strings / statuses / card IDs:** none touched. Spec-003 still carries no `Status:` / owner / target-release header block; re-verified against the HEAD copy.
- **KANBAN cards:** none moved. `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3` all clean in `git status --short` after my own read-only `import_spec_terms --check`.
- **Links:** all 27 definitions across both files disk-checked present, 0 missing; all 9 anchor-bearing definitions resolve against a real post-move spec heading.
- **Archive placement:** the rationale sits at `docs/SPECS/appx/`, the location `AGENTS.md` rule 26 names; its spec-side definitions sit under `<!-- docs/SPECS/ -->` per `START.md`'s closed-list rule.
- **Obsolete "planned"/"coming soon" wording:** present and **deliberately so** — the pre-implementation status claims are R2's, disclosed in `### Implementation notes` and in the rationale's `## Standing notes`. Correct scoping, not stale-doc drift.
- **Script-rendered docs:** none touched; no docstring-staging check applies.

### Failability proofs

**No proof was owed and none is missing.** R1 introduces no boundary, guard, gate, or rejection path — it changes no package source. Per `worker-3.md` "Reading is necessary, not sufficient", an empty re-run set is legal exactly when the diff introduces no boundary that meets the floor, which is the case here. **No boundary was re-run and none was accepted on a builder's record, because none exists.** No source mutation was made; the narrow carve-out was not exercised.

### Hot-path budget

Not applicable; the plan declares no hot path, and the item changes no runtime code.

### Floor verification

Not applicable; plan declares floor-verification scope `none`.

### Static helper use

`scripts/review_inspect.py` **skipped, with reason**: `worker-3.md` "Static helper use" triggers on a slice adding a `.py` file, touching `optimizer/` or `types/` `.py`, or adding 30+/50+ lines of logic. This pass's diff is two Markdown files and zero `.py` files, so no trigger fires. No shadow file was read or produced.

### What looks solid

- **Stating the guard instead of enumerating its consequences is the right shape of fix, and the report argues it correctly.** The enumeration was a derived restatement of the guard and had been wrong twice; the surviving sentence is shorter, is what the deleted fence encoded, is directly implementable, and cannot be falsified by a field kind nobody thought to check.
- **The fix is better than the thing it replaced, not merely repaired.** The deleted fence's own literal guard (`django_field.attname is not None`) would raise `AttributeError` on every reverse relation — the census shows `attname is None` never occurs. The bullet now describes HEAD's `getattr(..., None)` presence test, so the rescued rule is stated more accurately than the spec ever stated it.
- **The instruction half is provably untouched.** Byte-identical to pass 2's, verified by reconstructing pass 2's line from the artifact's own blockquote — so the correction demonstrably narrowed the claim without eroding the rescue.
- **The counting discipline finally holds end to end.** Fifteen of fifteen figures re-derive exactly, each with its command; and the anchored-vs-unanchored reconciliation (8 + 5 = 13) means the two passes' apparently conflicting measurements are now a single explained population rather than two numbers a later reader must choose between.
- **The R2 hand-off landed in the durable file, not only in the artifact.** `## Standing notes` is where the next pass will actually look, and both scope questions name the measurement they came from — so R2 inherits evidence rather than a to-do.
- **Zero regression across eleven previously-cleared items**, each re-measured this pass rather than carried forward.

### Temp test verification

None created. `docs/builder/temp-tests/r1/` was not used. R1 lands no executable behavior; the three verification scripts this pass ran (the Django relation-field `attname` census, an independent heading slugger plus link-target disk check, and an 8-word shingle/contiguous-run comparison) all live under the scratchpad **outside** the repository, are read-only, and touched neither the database nor any tracked file. Nothing to promote. No `pytest` was run (`AGENTS.md` rule 15).

### Notes for Worker 1 (spec reconciliation)

1. **Nothing is owed on R1.** Both pass-2 Lows are closed, no new finding was raised, and the item is accepted. Final verification has no finding to adjudicate.
2. **The concurrent-session dirty set grew mid-pass, well beyond the four files in the plan's `## Baseline-dirty out-of-scope files`.** `git status --short` was the expected four (`CHANGELOG.md`, `GOAL.md`, `README.md`, `TODAY.md`) plus this cycle's own paths for the first part of my verification work; by the end it also carried:

   ```text
    M docs/SPECS/spec-030-connection_field-0_0_9.md
    M docs/SPECS/spec-032-full_relay-0_0_9.md
    M docs/SPECS/spec-033-connection_optimizer-0_0_9.md
    M docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
    M docs/SPECS/spec-041-channels_router-0_0_14.md
    M docs/SPECS/spec-042-debug_toolbar-0_0_14.md
    M docs/SPECS/spec-044-debug_extension-0_0_14.md
    M examples/fakeshop/apps/products/schema.py
    M examples/fakeshop/test_query/test_products_api.py
   ```

   The two example-file diffs are a card renumber (`TODO-BETA-053-0.1.5` → `TODO-BETA-060-0.1.5`), so this is a concurrent renumber sweep across `docs/SPECS/` and the example project. **Not touched, not reverted** (`AGENTS.md` rule 34, `START.md` "Concurrent sessions"), and per the plan's own instruction the list is Worker 0's to append rather than a worker's to edit. Two consequences worth passing on: **R3's archive audit sweeps `docs/SPECS/` and will meet this churn**, and it is now false that a diff in a `docs/SPECS/` file is attributable to this cycle. I re-verified after the churn appeared that **spec-003 and its rationale are untouched by it** — `git diff --stat` on the spec is still exactly `18 insertions(+), 224 deletions(-)`, `wc -lc` is still 241 / 25,786 and 511 / 35,645, and neither file contains any `TODO-<MILESTONE>-<NNN>` token at all — so no measurement in this review is affected.
3. **Carried to R2, unchanged and confirmed still open:** pass-1 items 1-4, pass-2 items 5-6, pass-3 items 7-8. I re-checked and found nothing belonging to R2 outside the union of those eight and the build plan's 22-row drift table. Items 7 and 8 are on disk in both the artifact and the rationale's `## Standing notes`, so they survive this artifact's cycle.
4. **The fence count needs no further carry.** Confirmed a fourth time (14 markers at HEAD, 7 fences), and `build-003-…:27` and `:140` both now read seven, with `:140` carrying the correction and its own reason. Closed.
5. **For the deferred-work catalog, unchanged:** the ordering invariant at `spec:67` has no automated guard at HEAD, only a docstring on `walker.py::_record_relation_access`. R1 promoting it to a spec-level requirement is the strongest form available inside a docs cycle; whether it earns a test is the maintainer's call.

### Review outcome

`review-accepted`.

Both pass-2 Lows are closed. The rescued bullet's instruction half is byte-identically intact, its replacement scope sentence is true against a full-graph field-kind census and against both hint dispatch sites read directly, and deleting the enumeration cost a builder nothing — an enumeration of when a guard fires is a derived restatement of the guard, and it was the copy that rotted, twice. The relabel count is superseded with its command, and the anchored population is the right one: all five extra hits the unanchored regex returns were enumerated and none is a per-entry label, so 8 + 5 = 13 reconciles the two passes' figures rather than leaving a reader to pick between them.

Everything else re-derived clean: fifteen of fifteen stated counts exact — including the byte-arithmetic proof, whose pass-2 term I reconstructed from the artifact rather than assumed, so it genuinely proves exactly one line changed — zero regression across all eleven previously-cleared items, the move still provably a cut with no unmarked shared block, all 8 glossary anchors at 1 link each with zero attrition, all four validation commands green, every pointer and every link target resolving, the provenance partition exhaustive and disjoint, the R1/R2 boundary intact in both directions, and the two R2 hand-off items present on disk in both the artifact and the durable file.

`worker-3.md` "Acceptance gate" is met: no High, Medium, or Low finding is outstanding. A fourth loop on a documentation item would buy nothing a future reader or a future builder would notice.


### Addendum: the concurrent sweep reached the DB-backed generated files before this pass closed

`git status --short` at the moment every measurement above was taken carried the plan's four baseline-dirty files plus this cycle's own paths, and `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` were all **clean** — which is what the `### Documentation / release sanity` and `### Stated counts` entries above record, correctly, as of that reading. On the final check the concurrent renumber sweep described in `### Notes for Worker 1` item 2 had also landed:

```text
 M KANBAN.html
 M KANBAN.md
 M examples/fakeshop/db.sqlite3
```

It is unambiguously that session's: `git diff -- KANBAN.md` rewrites a card-052 scope item from "Sweep the dead card id `TODO-BETA-053-0.1.5` …" to "Swept 2026-08-07: all 32 occurrences … now read `TODO-BETA-060-0.1.5`", which is the same sweep as the two example-file diffs, plus unrelated link-definition churn in the generated tail. `Bin 5050368 -> 5050368 bytes` on the DB is exactly the case `BUILD.md` `### Tracked binary / generated files` warns is **not** proof of a no-op — and here it is a real kanban write, the source the two regenerated docs render from. **Not touched, not reverted, not `git checkout`-ed** (`AGENTS.md` rule 34).

Re-verified after it landed, so nothing above rests on the pre-churn reading:

- R1's two files are untouched by it — `git diff --stat` on the spec is still exactly `18 insertions(+), 224 deletions(-)`, `wc -lc` still 241 / 25,786 and 511 / 35,645, `sed -n '78p' | wc -c` still 778, and a `TODO-(ALPHA|BETA|STABLE)-[0-9]+` grep over both files exits 1 (no match), so the sweep's token appears in neither.
- Both DB-dependent checks re-run green **after** the DB write: `check_spec_glossary.py --spec …` → `OK: 8 terms - all have glossary entries and at least one spec link.` exit 0, and `import_spec_terms --check` → `OK: 49 done cards have glossary links.` exit 0. Card 3's glossary-link chain is intact across the concurrent kanban write.
- `docs/GLOSSARY.md` remains clean.

**One plan premise is now false and R3 needs it.** `## Concurrent-writable tracked binary / generated files` states that because all four were clean at pre-flight, "unlike the spec-002 cycle a diff here IS attributable" to this cycle. Three of the four are now dirty from another session, so that attribution no longer holds and R3's archive audit cannot read a `KANBAN.md` / `KANBAN.html` / `db.sqlite3` diff as its own output. Per the plan's own instruction the list is Worker 0's to append, not a worker's to edit; flagged here so it reaches R3 rather than being re-derived. The review outcome is unchanged — no measurement in this section depended on those files.

---

## Final verification (Worker 1)

Fresh invocation, no memory of the three prior passes; the artifact and the working-tree diff are the record. Every count below was produced by the command quoted beside it, in the same edit that wrote it down — two of this item's five findings were miscounts in Worker 1's own reports, so nothing here is carried forward on a prior pass's word, Worker 3's `review-accepted` included.

Read-only HEAD reference per `worker-1.md` `### Verifying relocation / promotion claims` and `BUILD.md` `## Claims are proven mechanically, never accepted on prose`: `git show HEAD:docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md > <scratch outside the repo>/spec-003-HEAD.md`. **No `git stash`, `git checkout`, `git restore`, or `git worktree` at any point.** No `pytest` (`AGENTS.md` rule 15), no `--cov*` flag in any form.

### A correction to this pass's own dispatch: the item DOES carry a `### Dispatched findings checklist`

The dispatch states that R1 has neither a `### Spec slice checklist (verbatim)` nor a `### Dispatched findings checklist`, and directs the audit at the build plan's R1 contract instead. **The first half is right and the second is wrong**: `## Plan (Worker 1)` carries a `### Dispatched findings checklist` at `:45-63`, fifteen boxes, all `- [x]`, written under `worker-1.md` planning step 8's rule that a `### Dispatched findings checklist` goes in that position when no spec slice checklist exists.

So `## Final verification job` step 3 applies in its ordinary form and was performed in full, **in addition to** the build-plan-contract audit the dispatch asked for. Recording the discrepancy rather than silently following one of the two: an audit skipped because a dispatch said the artifact lacked the thing it audits is exactly the gap this step exists to close.

### The relocation claim, proven independently

The claim under `worker-1.md` `### Verifying relocation / promotion claims` is that the move was a **cut, not a copy**: text landing in the rationale left the spec. Run here rather than read from Worker 3's acceptance.

8-word shingle census over all three files, link-definition blocks and markdown punctuation stripped:

```text
HEAD shingles           : 4845
post-move spec shingles : 3831
rationale shingles      : 5553
LEFT the spec           : 1721
  ...preserved in rationale : 81
  ...in neither file        : 1640

*** shingles in BOTH post-move spec AND rationale (copy risk): 59

--- fenced code blocks ---
HEAD spec: 14 markers -> 7 fences
post-move spec: 0 markers -> 0 fences
rationale: 0 markers -> 0 fences
```

**1,721 shingles left the spec; 81 survive in the rationale and 1,640 in neither file.** That distribution is the three-category provenance partition measured rather than asserted: the 81 are the genuinely *Moved* `## Documentation updates when O4 ships` bullets, and the 1,640 are the seven fences and two deleted sections, *Cut* with a prose account and no text.

The copy test is the 59-shingle spec/rationale overlap. Decomposed into contiguous runs it is **11 runs**, each read in full and each attributable:

| # | words | what it is |
|---|---|---|
| 1, 7 | 14, 8 | the deliberately mirrored companion-pointer wording (`spec:3` / rationale opener) |
| 2 | 12 | the mirrored do-not-duplicate clause pointing at `spec-002`'s rationale |
| 3 | 13 | the rationale quoting surviving spec prose it is arguing about (`_collect_scalar_only_fields` walks scalar children only …) |
| 4 | 14 | the `:67` ordering rule, contract in the spec and narrated in the rationale entry |
| 5 | 9 | a section heading |
| 6 | 23 | the corrected `:78` scope clause, deliberately stated in both files |
| 8 | 8 | the flattening return-shape property, contract at `:112` and narrated at rationale `:260` |
| 9 | 16 | the rationale quoting `spec:122`'s two-options sentence to record which option won |
| 10 | 12 | the rationale quoting `spec:132`'s "pseudocode anchors now live in both …" as the premise it addresses |
| 11 | 8 | the surviving `spec-004` rider, quoted in the rationale's bullet-2 entry |

**No unmarked moved block exists in both files. The claim is proven.**

Second, independent form of the same proof — a whole-line check, which a shingle census can miss at a boundary. Of the 163 HEAD lines outside a fence and outside the two wholly-deleted sections, **11 are not present verbatim in the post-move spec**, and every one is accounted for:

- **6** are lines that were *extended* in place, not removed — a pointer or a rescued rule appended to the same line (`:29`, `:67`, `:71`, `:83`, `:90`, `:112`). Present, longer.
- **1** is `When implementation lands:`, retensed to `One obligation from this list is still open:` — disclosed in pass 1's `### Implementation notes`.
- **4** are the `## Documentation updates when O4 ships` bullets: three moved wholesale into the rationale, the fourth split with its open half surviving at `spec:192`.

**Zero unaccounted-for prose loss.** Nothing left the spec that the artifact and the rationale do not name.

### Section-level confirmation of what was removed

`diff` of the HEAD heading list against the post-move heading list returns exactly: the seven fences' comment lines, `## Implementation insertion points (O4)`, and `## Anchor and lint notes`. **No other section heading was removed and no surviving section lost its heading.**

The rationale carries **8 entries** under `## Entries keyed to the spec` — six keyed to surviving sections, two keyed to the deleted headings, each naming the surviving section its argument bears on. That is the coverage `BUILD.md` `## Spec rationale extraction` requires.

### Step 5 — the failability question, confirmed rather than assumed

The dispatch's premise is that no failability proof is owed because the item introduced no boundary and changed no source. **Confirmed by command, not by assumption:**

```text
$ git diff --stat -- django_strawberry_framework/ tests/
(empty)

$ git diff --name-only -- <this cycle's paths>
docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md
$ git ls-files --others --exclude-standard | grep 003
docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md
docs/builder/bld-003-r1-rationale_move.md
docs/builder/build-003-optimizer_nested_prefetch_chains-0_0_2.md
```

This cycle's diff is **one tracked `.md` file plus three untracked `.md` files. Zero `.py`.** No boundary, guard, gate, or rejection path landed, so no failability proof is owed and none is missing. No fail-open shape can have landed either — there is no expression to inspect.

Two `.py` files *are* dirty repo-wide (`examples/fakeshop/apps/products/schema.py`, `examples/fakeshop/test_query/test_products_api.py`). Both are in the plan's `## Baseline-dirty out-of-scope files`, and both were attributed by content before being set aside: each diff is a single `TODO-BETA-053-0.1.5` → `TODO-BETA-060-0.1.5` token change, the concurrent renumber sweep. **Neither edited nor reverted** (`AGENTS.md` rule 34).

### Step 6 — staged-anchor sweep

```text
$ grep -rEn 'TODO\(spec-003|TODO-(ALPHA|BETA|STABLE)-003' . --exclude-dir=docs/shadow --exclude-dir=.git
```

**17 hits, zero of them a staged anchor.** The distinction the dispatch asks for, applied hit by hit:

| Location | hits | what they are |
|---|---|---|
| `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/` | **0** | exit 1. No source or test file carries one. |
| the spec | **0** | HEAD carried **3**; `grep -c` on the HEAD copy returns 3, on the working tree 0. |
| the rationale | 6 | prose quotations inside code spans, recording what the anchors were and that none survives |
| this artifact | 7 | prose quotations in the move report and review sections |
| the build plan | 4 | prose quotations in the D3/D14/D15 drift rows and the R3 checklist item |

A staged anchor under `AGENTS.md` rule 26 is a **source-site** `# TODO(spec-NNN slice N): …` comment. Every surviving hit is in a `.md` file, inside a code span or a quoted instruction, describing an anchor rather than staging one. **Worker 1's pass-1 claim that the spec now carries zero is verified**, and Worker 0's pre-flight finding that source and tests carry zero still holds.

### Step 7 — the four verification commands, re-run

```text
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md
OK: 8 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check <spec> <rationale> <this artifact>
exit=0
```

`import_spec_terms --check` was run **after** the concurrent DB write, not trusted from an earlier reading. `git status --short` at the moment of the run showed `examples/fakeshop/db.sqlite3`, `KANBAN.md`, and `KANBAN.html` all dirty from that session — so this is a genuine post-write reading, and **card 3's glossary-link chain survives the concurrent kanban write intact**. `docs/GLOSSARY.md` remains clean.

Per-anchor, because a green `check_spec_glossary` does not prove per-anchor survival:

```text
ANCHOR                     HEAD   POST
djangotype                 2      2
fk-id-elision              2      2
metaoptimizer-hints        2      2
only-projection            2      2
optimizerhint              2      2
plan-cache                 2      2
queryset-diffing           2      2
schema-audit               2      2
```

**Zero attrition on all eight** (1 body use + 1 definition each). The terms CSV is unopened and clean in `git status --short`, and its 8 rows still map one-to-one onto the 8 anchors — the importability invariant `worker-0.md` `### DONE-card invariants` names.

### The five findings, each confirmed closed in the files

One Medium and four Lows across three review passes. Confirmed in the files, not read as reported closed.

| # | Pass | Finding | Closure verified |
|---|---|---|---|
| 1 | 1 | **Medium** — the parent-side FK-column append lived only in a deleted fence and was not rescued | **Closed.** `spec:78` states it, and I re-derived it against source: `walker.py::_plan_prefetch_relation`'s **first executable statement** is `_record_relation_access(plan, django_field, prefix, resolver_identities, enable_only=enable_only)` — `plan` there is the parent plan — and that helper's body is `attname = getattr(django_field, "attname", None)` / `if enable_only and attname is not None: append_unique(plan.only_fields, f"{prefix}{attname}")`. The rule is real, live, and was stated nowhere else. |
| 2 | 1 | **Low** — `## Provenance of this record` filed deletions under **Moved** | **Closed.** Three named categories at rationale `:48-69`, vocabulary defined in the opening paragraph before first use. `grep -cE '^\*(Moved\|Cut\|Deleted)'` → **8** labelled entries, **7** `*Cut*`, **1** `*Moved*`. Partition is exhaustive and disjoint over what left the spec, and my own shingle census (81 preserved / 1,640 in neither) independently confirms the two categories describe different populations. |
| 3 | 1 | **Low** — `### Validation run`'s "all 13 in-page anchors" (a Worker 1 miscount) | **Closed by supersession.** My own slugger, written independently: `spec headings: 22  dupes: []` / `rationale link definitions: 17` / `definitions carrying an in-page anchor: 9` / `in-page anchor USES in body: 10` / `unresolved: []` / `undefined refs: [] \| unused defs: []`. **9 and 10, not 13** — reproducing both later passes exactly. |
| 4 | 2 | **Low** — the rescued bullet's scope clause was measurably false (forward M2M appends; `force_prefetch` is a second route) | **Closed, and the replacement sentence is true.** Verified two ways, below. |
| 5 | 2 | **Low** — "Eight per-entry italic labels were relabelled" (a Worker 1 miscount) | **Closed by supersession.** `grep -cE '^\*(Moved\|Cut\|Deleted)'` → 8; `^\*Cut` → 7; `^\*Moved` → 1. **Seven relabelled.** The unanchored regex returns **13**, so the pass-2 review's 13 and the pass-3 anchored 8 reconcile as 8 + 5 rather than conflicting. |

**Finding 4 is the one that would matter if it were still open** — a false sentence in a standing document — so it was measured rather than read. The bullet now reads that the append is guarded on the relation carrying an `attname` at all, and that *the reverse descriptors carry none*. A census over the whole fakeshop model graph, my own script:

```text
kind                      n  hasattr(attname)   example
ForeignKey               57  {True}             LogEntry.user -> 'user_id'
GenericForeignKey         1  {True}             TaggedItem.content_object -> 'content_object'
GenericRelation           3  {True}             Branch.tags -> 'tags'
ManyToManyField          11  {True}             Group.permissions -> 'permissions'
ManyToManyRel            12  {False}            Permission.group -> '<ABSENT>'
ManyToOneRel             58  {False}            User.logentry -> '<ABSENT>'
OneToOneField            29  {True}             MembershipCard.patron -> 'patron_id'
OneToOneRel              29  {False}            Patron.card -> '<ABSENT>'

REVERSE descriptors carrying attname (spec:78 says none do):  NONE  <- sentence holds
FORWARD relations lacking attname:                            NONE
```

The sentence holds exactly: the three reverse descriptors carry no `attname` **attribute at all** (which is why HEAD reads it through `getattr`), and every forward relation carries one — including `ManyToManyField`, whose `attname` is its own field name, which is precisely what falsified the pass-2 enumeration.

The bullet's second route was checked at the dispatch sites rather than from the docstring: `walker.py:1049-1051` is `if hint.force_prefetch:` → `prefer_prefetch=True`, unconditional, so a forward FK does reach `_plan_prefetch_relation` by that route; `:1036` is `prefer_prefetch=_target_has_custom_get_queryset(target_type)`, the O6 downgrade. `::_dispatch_single_relation`'s docstring names both plus the cardinality dispatch. **"whether downgraded to a `Prefetch` by O6 or forced across by a `force_prefetch` hint" is true on both halves.**

### Step 3 — the `### Dispatched findings checklist`, audited against the files

All fifteen boxes are `- [x]`. Each verified against the diff and the two files; **no box was over-ticked and none needed un-ticking.**

| Box | Verified by |
|---|---|
| cut, not copy | the shingle census + 11-run decomposition + the whole-line check above |
| every cut site keeps a one-line pointer | **7 pointer sites** — `spec:3`, `:29`, `:71`, `:94`, `:112`, `:124`, `:194` (8 uses of `[spec-003-rationale]`, one of which is the definition). The two wholly-deleted sections have no heading left to carry one and are named explicitly in `:3` |
| rationale keyed to the spec by heading + anchor | 8 entries, each opening `Spec: [<heading>][anchor]`; all 9 anchor-bearing definitions resolve |
| rejected alternatives with a one-line reason each | 13 dispositions: 8 `*Alternative rejected*`, 4 `*Changed*`, 1 `*Not rejected*`, each carrying its reason |
| every claim the spec may no longer make, per entry | `grep -c '\*\*Claims the spec no longer makes\.\*\*'` → **8**, exactly one per entry |
| falsified prose deleted, not moved | `grep -c '```'` on the rationale → **0**; 1,640 shingles in neither file |
| implementation-relevant rationale stayed | **six** rescued rules, each traced to HEAD source: `:67` ordering (`_record_relation_access` docstring), `:78` parent append (verified above), `:83` empty-`only_fields` guard (`_ensure_connector_only_fields`), `:90` cacheable-before-child-build (`plan.cacheable = False` precedes `_build_prefetch_child_queryset` in the source I read), `:124` key format and resolver-side membership test |
| `check_spec_glossary` exit 0, all 8 anchors linked | re-run above; per-anchor 2 → 2 |
| `check_trailing_commas --check` passes | exit 0 on spec, rationale, and this artifact |
| every in-page anchor resolves | 9/9, `unresolved: []` |
| reference-style only, scaffold with all 10 headers in order, targets disk-checked | both files: `<!-- LINK DEFINITIONS -->` present, all 10 canonical headers at strictly increasing line indexes; **27 definitions disk-checked, 0 missing**; 0 undefined refs, 0 unused defs; `grep -nP '\]\((?!#\|https?:)'` exits 1 on both |
| `AGENTS.md` rule 27, no raw `path:NN` | `grep -nE '[a-zA-Z_/]+\.(py\|md):[0-9]+'` exits 1 on both files |
| rationale written directly to `docs/SPECS/appx/` | confirmed by path; definitions sit under `<!-- docs/SPECS/ -->` per `START.md`'s closed-list rule |
| byte count before and after reported | `wc -lc`: HEAD **447 / 34,030**; spec now **241 / 25,786**; rationale **511 / 35,645**. `git diff --numstat` → `18  224`. `sed -n '78p' \| wc -c` → **778** |
| `spec-002`'s rationale pointed at, not duplicated | every "extract" hit in the rationale read: `:33-35` points at `spec-002`'s rationale and says outright the argument "is not duplicated on this side of the split"; the four other hits are code-extraction, a different subject. Shingle run 2 is the mirrored pointer, not the argument |

### Step 2 — every planned step implemented

The plan's ten implementation steps were checked against the files, not against their "Done." markers. All ten landed: the companion pointer (`:3`), the `## Current state` fence cut with a pointer (`:29`), the same-query ordering rescue and fence cut (`:67`, `:71`), the prefetch-boundary rescues and both fence cuts (`:83`, `:90`, `:94`), the flattening restatement and cut (`:112`), the resolver-key restatements and both cuts (`:124`), the documentation-section trim (`:190-194`), both wholesale section deletions (absent from the heading diff), both link definitions (`:226-227`), and the rationale file with 8 entries. **Nothing was rejected, so no rejection reason is owed.**

### Step 4 — DRY across the item

R1 is this cycle's first item, so there is no prior accepted slice to compare against, and no source landed, so no code duplication is possible. The one live risk the plan named — duplicating `spec-002`'s rationale — is verified clean above. The single doubling inside this item (`spec:78` and rationale `:191-219` stating the same rule) is correct by design: the spec carries the contract, the rationale carries why it was nearly lost. **No DRY finding.**

### Step 5 (worker-1.md) — focused tests

The plan's `### Test additions / updates` reads `None`, and R1 lands no executable behaviour, so no focused test scope exists to run. `AGENTS.md` rule 15 forbids an unasked `pytest` run and no `--cov*` flag was used in any form. **Nothing owed, nothing run.**

### Step 8 — spec status-line re-verification

Re-checked against the HEAD copy: spec-003 carries **no** `Status:` / owner / target-release / predecessor header block. Its lines 1-5 are the title, the companion-pointer paragraph R1 added, `## Problem statement`, and that section's opening — whose claims are status prose the R1/R2 boundary assigns to R2.

The one header-adjacent line R1 *did* add is `:3`, so it was audited rather than assumed. It names five things as living in the rationale — the proposed implementation shapes and their departures, the pre-O4 code it quoted, the per-file insertion-point guidance, the staging convention the TODO anchors served, and the documentation obligations declared and discharged. **All five are genuinely there**, in entries 1-8. The line is accurate. **No status-line edit is owed.**

### The R1/R2 boundary

All 18 added lines enumerated from `git diff -U0` and classified: **7 pointers, 6 rescued rules, 2 link definitions, 3 blank, 1 retensed lead-in, 1 preserved documentation rider.** Not one is a status-claim rewrite.

The strongest evidence is added line 3, which is `spec:29` — a line R1 edited. It still asserts, verbatim from HEAD, that "the final relation-dispatch block still has O4 TODO anchors instead of recursing into `sel.selections`", a claim the package plainly falsifies. R1 appended a pointer to that sentence and left the sentence itself untouched. `:76` and `:85` likewise still carry their HEAD "by O6" framing, unmodified — which is exactly what hand-off items 7 and 8 give R2. `:112` still says the flattening helper belongs "next to `OptimizationPlan`" where HEAD put it at end of file, and the rationale records the contradiction rather than resolving it.

**The boundary is intact in both directions: nothing R2 owns was pre-empted, and nothing R1 owed was left.**

### The R2 hand-off is on disk and legible to a fresh spawn

Checked on disk rather than in a return report, per `BUILD.md` `### Cohorting, naming, and closure`.

Eight items, in three `### Notes for Worker 1 (spec reconciliation) — carried into R2` sections at `:157`, `:525`, `:949`: items 1-4 (the orphaned `## Definition of done` clause; `_collect_scalar_only_fields` still named in surviving prose; `` ## Missing `.py` files `` as a false map; the `spec-004` rider), items 5-6 (the new bullet is contract not status prose; the fence-count correction), items 7-8 (whether `:76`/`:85` should name the `force_prefetch` route; whether the forward-M2M append should be documented).

**Three of the eight — not two — additionally survive in the durable rationale's `## Standing notes`**: item 1 under `### One clause this pass orphaned`, and items 7-8 under `### Two scope questions this pass raised and did not answer`, each naming the measurement it fell out of. The remaining five are reachable from the artifact, which `worker-1.md` `## Required reading` makes mandatory reading for R2's planning pass, and items 2 and 3 are additionally D1 and D22 in the build plan's drift table. **Nothing lives only in a return report.**

Item 6 needs no further carry: `build-003-…:27` reads "seven fenced pseudo-code blocks" and `:149` carries the correction with its own reason. Confirmed a fifth time here — `grep -c '```'` on the HEAD copy returns **14** markers, i.e. **7** fences.

### Concurrent-session churn

`git status --short` at this pass carries the full renumber sweep the plan's `## Baseline-dirty out-of-scope files` describes: `CHANGELOG.md`, `GOAL.md`, `README.md`, `TODAY.md`, `docs/README.md`, seven archived `docs/SPECS/spec-0NN` files, the two `examples/` files, plus `examples/fakeshop/db.sqlite3`, `KANBAN.md`, and `KANBAN.html`. **None edited, none reverted, no `git checkout`** (`AGENTS.md` rule 34).

`docs/SPECS/spec-003-…` is the one file in that directory dirty from **this** cycle, re-confirmed by content: its diff is still exactly `18  224` and neither it nor the rationale contains any `TODO-(ALPHA|BETA|STABLE)-[0-9]+` token, so the sweep did not reach either file. `docs/GLOSSARY.md` and the terms CSV are clean. Both DB-dependent checks were re-run after the write and both pass.

### Deferred work

Nothing R1 owed is deferred. Two items are recorded for the cycle's `### Deferred work catalog` rather than for R2:

- The ordering invariant now stated at `spec:67` has **no automated guard** at HEAD — only the docstring on `walker.py::_record_relation_access`. Promoting it to a spec-level requirement is the strongest form available inside a documentation cycle; whether it earns a test is the maintainer's call.
- The rationale-file template is now on its third hand-reproduced instance (`spec-001`, `spec-002`, `spec-003`). Whether it becomes a documented template is a standing-docs question, not a defect in this item.

### Summary

R1 cut spec-003's deliberative layer into a new durable companion at `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md`. The spec went **447 lines / 34,030 bytes → 241 lines / 25,786 bytes** (`-206 lines / -8,244 bytes, -24.2%`) across `18 insertions(+), 224 deletions(-)`; the rationale is **511 lines / 35,645 bytes** with 8 entries keyed to the spec and 4 standing notes.

Seven fenced pseudo-code blocks, `## Implementation insertion points (O4)`, and `## Anchor and lint notes` were cut; three-and-a-half `## Documentation updates when O4 ships` bullets were moved; **six** load-bearing rules that existed only inside a fence were rescued into the spec under the implementation-relevant carve-out. The move is provably a cut — 1,721 shingles left the spec, 81 survive in the rationale, 1,640 in neither, and the 11 shared runs are all quotation, headings, or deliberately mirrored wording. All 8 glossary anchors survive with zero attrition and the card-wrap chain holds across a concurrent kanban write. Zero staged anchors remain in the spec and none ever existed in source or tests. The R1/R2 boundary held across three passes and two spec edits.

All five findings raised across the three review passes are closed in the files, including both Worker 1 miscounts, and the one finding whose failure mode was a false sentence in a standing document was re-measured against a full model-graph census rather than accepted.

### Spec changes made (Worker 1 only)

**None this pass.** Final verification found nothing that must be corrected before acceptance, so neither writable spec-side file was opened for editing. The spec's cumulative changes across the three R1 passes are recorded in the three prior `### Spec changes made (Worker 1 only)` tables at `:166`, `:532`, and `:956`; all were re-verified against the files here and every one is accurately described.

No deferral reason is owed under `## Final verification job` step 3: every box in `### Dispatched findings checklist` is `- [x]` and every one was confirmed landed.

No spec status/header line needed an edit — spec-003 carries no `Status:` / owner / target-release header block, and the one header-adjacent line R1 added (`:3`) was audited against the rationale's contents and is accurate.

### Final status

`final-accepted`.
