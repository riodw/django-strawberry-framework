# Build: R1 — Spec rationale extraction for spec-002

Spec reference: `docs/SPECS/spec-002-optimizer-0_0_2.md` (whole file; 7,398 bytes / 113 lines at pass start)
Build plan: `docs/builder/build-002-optimizer-0_0_2.md` (residual item R1)
Status: final-accepted

**Deviation 3 of the build plan governs this artifact.** R1 has no Worker 2 pass — `BUILD.md`
`## Spec rationale extraction` makes Worker 1 the only role that performs the move and states that
Worker 2 never reads the rationale file. So this single Worker 1 pass **wrote the plan below AND
performed the move**, and `Status: planned` here means "dispatch Worker 3 for the audit", not
"dispatch a builder". The `## Move performed` section stands in for the Worker 2 build report and
keeps its subsection names so Worker 3 reads a familiar shape.

## Plan (Worker 1)

### Spec status-line re-verification

`spec-002-optimizer-0_0_2.md` has **no status/header block** — no target-release, status, owner, or
predecessor line adjacent to the title. Line 1 is `# Spec: Optimizer & Reverse-Relation Resolution`,
line 2 blank, line 3 `## Purpose`. Nothing to re-verify or falsify; recorded so the next spawn does
not re-derive the absence. Identical to the spec-001 cycle's finding on its own spec.

The spec's stale-by-tense *body* claims — `## Current state`, `## Shipped slices`,
`## Visibility status`, `## Implementation checklist` — are item **R2**'s axis, not this pass's, and
were deliberately left untouched (see `### What deliberately STAYED, and why`).

### DRY analysis

**Helper inventory checked.** Not applicable in the form `worker-1.md` `### Package-wide helper
inventory before helper planning` defines it: that step exists to prevent duplicated *code* helpers,
and this item writes no `.py` file and plans none. The package-wide AST inventory would answer a
question R1 does not ask. The DRY question R1 *does* ask is the build plan's own preamble rule —
"a fact told twice across the spec and its rationale sibling goes stale in one of them" — and it is
answered per moved passage below and measured mechanically in `### Move-not-copy proof`.

- **Existing patterns reused.** The rationale file's shape is taken from the two archived siblings
  that already exist: `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` (the immediate
  precedent, same cycle shape, spec-002's own parent document) and
  `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`. Title line, companion preamble,
  `## How to read this file`, `## Provenance of this record`, `## Entries keyed to the spec` with a
  `Spec: [heading][ref]` line and italic `*Moved — …*` / `*Alternative rejected — …*` leads, a
  `**Claims the spec no longer makes.**` line per entry, and a link-definitions block whose `docs/`
  targets resolve `../../` and whose `docs/SPECS/` siblings resolve `../`. A reader who has read one
  rationale file can read this one.
- **New helpers justified.** None. No source, no test, no script.
- **Duplication risk avoided.** Three, all real in this spec:
  1. **The same fact left in both files.** Every passage moved was *cut*, not copied — proved
     mechanically in `### Move-not-copy proof`, which also measures the longest shared prose run
     between the two files (12 words, one occurrence, and it is a labelled quotation).
  2. **The spec already duplicated itself.** `## Purpose` and `## O4 extraction` each carried half
     of one two-sentence fact (the O4 ownership pointer in both; the "high level only" scope rule in
     the section only). Two statements of one fact in a 113-line document is the mechanism by which
     a spec goes stale in one place and not the other. The section was cut and the scope rule folded
     into the surviving `## Purpose` paragraph — a fold, not a deletion, because the scope rule is
     the sentence that stops R2 rewriting this parent spec into a summary of spec-003 / 004 / 033 /
     035.
  3. **Pointer inflation.** `worker-1.md` rule 1 requires every decision keep a one-line pointer
     naming what moved and where. Written naively that is one pointer per removed paragraph — five
     here, on a 7.4KB spec where the pointers would have cost more bytes than the narration they
     replace. This pass uses **one global pointer** (`## Purpose`, naming all four moves) plus **two
     section-local pointers** where a section kept text and lost text (`## Problem statement`,
     `## Architecture decision`), the second of them a single appended clause rather than its own
     paragraph. Three pointer sites, not five.

### Implementation steps

Pin-at-write-time line numbers are from the pre-move spec.

1. `## Purpose` (6): cut the "O4 was extracted out of this document during implementation"
   chronology; fold in `## O4 extraction`'s scope rule so the surviving paragraph carries both the
   scope rule and the ownership pointer; append the global rationale pointer as a new paragraph.
2. `## Problem statement` (9): cut the spec-001-prediction chronology and the "Two concrete failures
   pushed the optimizer story into its own subsystem" framing; restate the lead-in as what the two
   bullets are (the problems that define the subsystem). **Leave bullet 1 (11) untouched — it is the
   sole carrier of the `djangotype` anchor.** Add a section-local pointer after the seam sentence.
3. `## Architecture decision` (33): split the justification paragraph — restate the two conditions
   as a requirement on the resolvers (contract), move the "remain necessary even with the optimizer"
   derivation, append the section-local pointer as a clause.
4. Cut `## O4 extraction` (53-54) entire.
5. Cut `## Open questions` (66-69) entire.
6. Add `[spec-002-rationale]: appx/spec-002-optimizer-0_0_2-rationale.md` under the spec's
   `<!-- docs/SPECS/ -->` group.
7. Write `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` **directly** at `appx/` (the spec
   is already archived; there is no later move step), one keyed entry per spec heading, with all ten
   canonical link-definition group headers.
8. Run every verification command and quote it; prove the move mechanically.

**Sections deliberately not opened:** `## Current state`, `## Shipped slices` (all six O-slices),
`## Coordination with spec-001…`, `## Visibility status`, `## References`,
`## Implementation checklist`. Reasons in `### What deliberately STAYED, and why`.

### Test additions / updates

None, and none possible: this item writes no `.py` file. The executable checks that stand in for
tests are the four commands in `### Validation run` plus the two throwaway scripts in
`### Temp tests used`. Every one has a recorded pre-move baseline in the build plan (`OK: 3 terms
…` exit 0; trailing-commas exit 0; `OK: 49 done cards …` exit 0; the raw-`path:NN` grep with no
match).

### Implementation discretion items

None delegated — there is no Worker 2 pass to delegate to. Every judgement call this item raised is
decided in `### Implementation notes`.

### Dispatched findings checklist

R1 is neither a spec slice (spec-002's slices O1-O6 shipped at `0.0.2`) nor a review round, so there
is no `## Slice checklist` to copy verbatim. Per `BUILD.md` `## Review rounds`,
`### Dispatched findings checklist` is the named substitute in this position; the boxes are R1's
obligations as the build plan's checklist line and the maintainer's dispatch state them. **Ticked by
Worker 1 in this pass** because Deviation 3 gives it the performer's role; Worker 3 audits the ticks,
Worker 1 re-audits at final verification.

- [x] The deliberative layer is **moved**, not copied and not summarized: text landing in
      `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` leaves the spec. Proved passage by
      passage in `### Move-not-copy proof`, against the read-only HEAD copy of the spec.
- [x] `## O4 extraction` is gone from the spec (pure self-narration plus a duplicate), with the one
      contract sentence it carried folded into `## Purpose` rather than lost.
- [x] `## Open questions` is gone from the spec; both questions are recorded in the rationale
      verbatim, in the spec's own tense.
- [x] The spec no longer narrates its own history: no "was extracted … during implementation", no
      "predicted … confirmed it", no "pushed the optimizer story into its own subsystem".
- [x] Every entry in the rationale file names the spec section it belongs to **by heading and
      anchor**, and carries the alternatives rejected and why each lost, the changes the decision has
      undergone, and the claims it may no longer make.
- [x] Every decision that lost text keeps a one-line pointer naming what moved and where (one global
      + two section-local).
- [x] The rationale file is written **directly** to `docs/SPECS/appx/`, never to `docs/` first.
- [x] Both files use reference-style links with one `<!-- LINK DEFINITIONS -->` block and all ten
      canonical group headers in `START.md` order; every path is disk-exists-checked and every
      in-page anchor resolves against a surviving spec heading.
- [x] The **3-anchor constraint** holds: `check_spec_glossary.py --spec …spec-002…` exits 0 with
      `OK: 3 terms - all have glossary entries and at least one spec link.` and the per-anchor link
      counts are **identical to HEAD** (1 / 1 / 1), so the move is anchor-neutral rather than merely
      non-fatal. The terms CSV was not touched.
- [x] `import_spec_terms --check` exits 0 with `OK: 49 done cards have glossary links.`
- [x] `check_trailing_commas.py --check` exits 0 on **both** files; neither file gains a raw
      `path:NN` reference (`AGENTS.md` rule 27).
- [x] Spec byte count reported before and after, by two independent measurements that agree.
- [x] R2's work was **not** done here: no claim was reconciled against HEAD, no drift row D1-D15 was
      touched, and every removed status-shaped claim is recorded in the rationale as a claim the spec
      *made*, not as one HEAD falsifies.

---

## Move performed (Worker 1, in place of the Worker 2 build pass)

### Files touched

- `docs/SPECS/spec-002-optimizer-0_0_2.md` — the five removals/restatements and the new
  `[spec-002-rationale]` link definition.
- `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` — **created**, 13,077 bytes.
- `docs/builder/bld-002-r1-rationale_move.md` — this artifact.
- `docs/builder/worker-memory/worker-1.md` — one appended entry under the existing
  `## spec-002 residual cycle` heading (gitignored; not part of the diff).
- `docs/builder/temp-tests/r1-spec002/` — two throwaway verification scripts (gitignored).

Nothing else. `docs/SPECS/appx/spec-002-optimizer-0_0_2-terms.csv` is byte-untouched.

### Byte counts

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-002-optimizer-0_0_2.md` | 7,398 | **7,093** | **-305 (-4.1%)** |
| `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` | 0 (absent) | 13,077 | +13,077 |

Two independent measurements of the spec delta agree, which is what pins it rather than a single
`wc`: `wc -c` against the working tree minus the build plan's recorded 7,398, and a per-line sum
over `git diff -U0` (**1,458 bytes removed, 1,153 added, net -305**). Line count 113 -> 110.

**-4.1% is a small number and it is the honest one.** The mechanism's byte argument was measured on
a 247KB spec whose deliberation was 48% of one section; spec-002's deliberative layer is thin and
interleaved, and three pointer sites plus one restated contract paragraph cost 1,153 of the 1,458
bytes removed back. What this move buys on a spec this size is the *other* half of the rule — the
spec no longer narrates its own history, and a reader can no longer reconstruct what is currently
true by applying a chronology to it. A pass that inflated the removal by cutting `## Current state`
or `## Shipped slices` would have bought bytes with R2's work and with the two glossary anchors
those sections carry.

The rationale file is larger than the bytes removed, and that is expected rather than a copy leak:
it carries its own preamble, `## How to read this file`, `## Provenance of this record`, a
`Spec: [heading]` line and a framing sentence per entry, and the *why each alternative lost*
reasoning the spec mostly did not state at all. The mechanical evidence that it is not a copy is
`### Move-not-copy proof`: the longest shared prose run between the two files is **12 words**, one
occurrence, and it is a quotation explicitly labelled as text that stayed.

### What moved, by spec heading

| Spec heading | What left it |
|---|---|
| `## Purpose` | "O4 was extracted out of this document during implementation." (chronology) |
| `## Problem statement` | The `spec-001` prediction, what confirmed it, where the prediction is recorded, and the "Two concrete failures pushed the optimizer story into its own subsystem" framing. |
| `## Architecture decision` | The justification for keeping generated relation resolvers alongside the optimizer ("remain necessary even with the optimizer because …"). The two conditions it named were restated as a requirement; the framing moved. |
| `## O4 extraction` | **Whole section.** Its ownership pointer was already duplicated in `## Purpose`; its scope rule was folded there. |
| `## Open questions` | **Whole section**, both questions verbatim. |

### What deliberately STAYED, and why

- **`## Current state`, `## Shipped slices` (O1-O6), `## Visibility status`, and
  `## Implementation checklist`.** These are status claims, not deliberation. Moving a status claim
  is neither a legitimate rationale entry nor the deletion `worker-1.md` rule 2 prescribes for
  falsified prose — that deletion is R2's call, made against HEAD, which this pass is forbidden to
  make. They are also drift rows D1-D14's home, i.e. already on R2's list. Same call the spec-001
  cycle made on its own `## Current state`, and Worker 3 accepted it there.
- **`## Architecture decision`'s first two paragraphs.** The root-gate mechanism
  (`info.path.prev is None`, plan-once-then-apply, non-root and non-`QuerySet` pass-through) is
  mechanism, not deliberation — and it is drift row D11, R2's axis.
- **The `B2/B3 runtime sentinels` sentence.** It states what the resolver layer is *for*, consumed
  by O6 and by later optimizer behavior. Moving it would have taken a mechanism out of the spec.
- **`## Coordination with `spec-001-django_types-0_0_1.md``, entire.** It states the division of
  ownership normatively (which symbols belong to the type system, which to the optimizer) rather
  than narrating how that division was reached. `worker-1.md`: when it is unclear whether a sentence
  is deliberation or instruction, it stays — and here it is not even unclear.
- **`## References`, entire**, including the issue #572 / PR #583 bullet. References are contract
  scaffolding; the spec-001 cycle kept its own `## References` on the same reasoning. The #572/#583
  bullet in particular was **already assessed** by the spec-001 cycle's R3 pass, which established
  that what the sentence names as its locator is the upstream issue and PR — not spec-001's moved
  bundling argument — so it does not dangle and is not R1's to touch.
- **Both `## Problem statement` bullets and the seam sentence.** The bullets are
  implementation-relevant "why": *"Strawberry's default resolver returns a Django `RelatedManager`,
  which is not directly iterable"* is why O1 exists and shapes how it is built; *"before relation
  resolvers evaluate model attributes"* is why O3's gate is at the root. This is the carve-out
  `worker-1.md` names as the one place the move can itself cause a defect. Bullet 1 is also the sole
  carrier of the `djangotype` anchor.

### Minimal repairs made to keep surviving prose coherent

Three. Each is the smallest edit that leaves a parsing sentence; none introduces a claim the spec did
not already make.

1. **`## Problem statement` lead-in restated.** The cut sentence ended in the colon that introduces
   the two bullets, so removing it would have orphaned them. `"Two concrete failures pushed the
   optimizer story into its own subsystem:"` -> `"Two concrete problems in relation resolution
   define this subsystem:"`. The bullets are unchanged. "failures" -> "problems" is deliberate: they
   are stated in the spec as standing properties of Strawberry and of selection-tree timing, not as
   events that once occurred.
2. **`## Purpose` paragraph 2 folded.** `"O4 was extracted out of this document during
   implementation. The O4 design record remains in `spec-003…`; keep detailed O4 rationale there
   rather than duplicating it here."` -> `"It records that behavior at a high level only: the
   detailed O4 design and implementation record belongs to `spec-003…`; keep detailed O4 rationale
   there rather than duplicating it here."` The chronology is gone, the ownership pointer is
   verbatim, and the scope rule that `## O4 extraction` carried alone is now stated here. This is
   the one place the pass rewrote rather than cut, and it is deliberate: cutting the section without
   the fold would have left the scope rule stated nowhere.
3. **`## Architecture decision` paragraph 3 split.** `"Generated relation resolvers remain necessary
   even with the optimizer because they provide correct behavior when the optimizer is disabled or
   when a relation is not already loaded."` -> `"Generated relation resolvers are required
   independently of the optimizer: they must return correct results when the optimizer is disabled
   and when a relation is not already loaded."` Descriptive-past to normative-present, the same
   direction the spec-001 cycle's repair 2 took and Worker 3 blessed there as "the correct direction
   for a contract". The proposition is unchanged: the two conditions are the same two conditions, and
   `or` -> `and` is a conjunction of *requirements* replacing a disjunction of *reasons*, which is
   the same claim in the normative voice (a resolver that worked in only one of the two would not
   have satisfied the original sentence either). The derivation — that the question "does the
   optimizer make these redundant?" was asked and answered — moved.

**No glossary link needed re-siting.** All three anchors sit in prose this pass did not open:
`only-projection` in `## Purpose` sentence 1, `djangotype` in `## Problem statement` bullet 1,
`djangooptimizerextension` in `## Current state`. This was a plan constraint, not luck — steps 1-5
were chosen so that the two anchors the build plan flagged as sitting "in sections R1 and R2 are
most likely to rewrite" stayed inside untouched sentences.

### Validation run

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md
OK: 3 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-002-optimizer-0_0_2.md \
    docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md
exit=0

$ grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+' docs/SPECS/spec-002-optimizer-0_0_2.md \
    docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md
exit=1        # no match, in either file — rule 27 preserved, not established

$ git diff --check
exit=0
```

Every one matches the build plan's recorded pre-move baseline exactly. No `ruff` run: no `.py` file
was touched. No `pytest` run: no test exists for a markdown move, none was in the plan, and
`AGENTS.md` rule 15 forbids one.

**Anchor counts, before and after** (shortest distinctive token, occurrences counted, not matching
lines):

```
$ grep -o '\]\[glossary-[a-z0-9_-]*\]' docs/SPECS/spec-002-optimizer-0_0_2.md | sort | uniq -c
   1 ][glossary-djangooptimizerextension]
   1 ][glossary-djangotype]
   1 ][glossary-only-projection]
```

Identical against the read-only HEAD copy. There are no inline `](../GLOSSARY.md#…)` forms in
either version, so the reference-style count is the whole population.

### Move-not-copy proof

`BUILD.md` `## Claims are proven mechanically, never accepted on prose` binds this: "I moved it" is
not the proof. Two throwaway scripts under `docs/builder/temp-tests/r1-spec002/`, both read-only
over the two Markdown files plus a read-only HEAD copy of the spec obtained with
`git show HEAD:docs/SPECS/spec-002-optimizer-0_0_2.md > <scratch outside the repo>` (no `stash`, no
`checkout`, no `restore`).

**Method note worth carrying:** the first run reported 7 of 14 passages "missing from the rationale".
All seven were **line-wrap artifacts** — the rationale wraps at 100 columns and two of the quotations
are blockquotes, so a multi-word grep token spanning a wrap matches nothing. The comparison is run on
whitespace-normalized text with blockquote markers stripped. A phrase-length token samples a claim's
vocabulary rather than establishing its population, in exactly the direction `BUILD.md` warns about.

Every removed passage: present in the HEAD spec, **absent** from the current spec, **present** in the
rationale.

| Passage | in HEAD spec | in spec now | in rationale |
|---|---|---|---|
| problem-statement chronology (`predicted that the optimizer half …`) | 1 | 0 | 1 |
| problem-statement chronology (`running the early DjangoType slice tests confirmed it`) | 1 | 0 | 1 |
| problem-statement framing (`pushed the optimizer story into its own subsystem`) | 1 | 0 | 2 |
| purpose chronology (`O4 was extracted out of this document during implementation`) | 1 | 0 | 1 |
| `## O4 extraction` heading | 1 | 0 | 6 |
| O4 extraction body (`The detailed O4 implementation record lives in`) | 1 | 0 | 1 |
| O4 extraction scope rule, old wording (`only records the shipped behavior at a high level`) | 1 | 0 | 1 |
| architecture justification (`remain necessary even with the optimizer`) | 1 | 0 | 1 |
| architecture justification (`because they provide correct behavior when the optimizer is disabled or when a relation is not already loaded`) | 1 | 0 | 1 |
| `## Open questions` heading | 1 | 0 | 3 |
| open question 1 lead (`Custom resolver opt-out`) | 1 | 0 | 1 |
| open question 1 body (full sentence pair) | 1 | 0 | 1 |
| open question 2 lead (`` `only()` opt-out per consumer field ``) | 1 | 0 | 1 |
| open question 2 body (full sentence pair) | 1 | 0 | 1 |

Eleven surviving-contract tokens confirmed still present in the spec, so nothing load-bearing left
with the cuts: `RelatedManager`, `before relation resolvers evaluate model attributes`, `share one
seam`, `keep detailed O4 rationale there rather than duplicating it here`, `at a high level only`,
`B2/B3 runtime sentinels`, `when the optimizer is disabled`, `when a relation is not already
loaded`, `info.path.prev is None`, `pass through unchanged`, `detailed O4 design and implementation
record belongs to`. 11 checked, 0 failures.

**Longest shared prose run between the two files: 12 words, one occurrence** (link-definition blocks
stripped, blockquote markers stripped, whitespace normalized):

> the framework gets from Strawberry field resolution to the underlying Django model

That is the seam sentence, quoted inside the rationale's statement that it *stayed* in the spec —
quotation-with-attribution, self-labelling about where ownership sits, not duplication. With the
link-definition blocks included the longest run is 18 words and is the ten canonical group headers.
No prose passage exists in both files unlabelled.

### Link-convention and anchor audit

Checked mechanically for both files (`docs/builder/temp-tests/r1-spec002/prove_move.py`):

- Reference-style throughout; no inline `](path)` cross-file links in either body outside code
  fences.
- One `<!-- LINK DEFINITIONS -->` block each, with all 10 canonical group headers in the exact
  `START.md` order, empty groups retained.
- Spec: **4 defs / 4 used refs**, 0 undefined, 0 orphaned. The new `[spec-002-rationale]` def is
  filed under `<!-- docs/SPECS/ -->` (a subdirectory shares its parent's group, per `START.md`'s
  closed-list rule) and the `docs/` glossary group stayed alphabetical.
- Rationale: **10 defs / 10 used refs**, 0 undefined, 0 orphaned; every group alphabetical.
- **Depth is right**: `../spec-00N-….md` for `docs/SPECS/` siblings, a **bare filename** for the
  `docs/SPECS/appx/` sibling `spec-001-django_types-0_0_1-rationale.md`, `../../GLOSSARY.md#…` for
  a `docs/` target, and `../../builder/BUILD.md` for `docs/builder/`.
- **Every path disk-exists-checked** by `os.path.exists` on the normalized join, both files, all 14
  defs: all present.
- Every in-page anchor the rationale cites resolves against a surviving spec `##` heading —
  `#purpose`, `#problem-statement`, `#architecture-decision`, `#shipped-slices`,
  `#coordination-with-spec-001-django_types-0_0_1md`. Computed by slugging the spec's actual
  headings, not by eye. No rationale anchor points at a removed heading.
- **Nothing anywhere in the tree cites spec-002 by `#anchor`** (`grep -rn
  'spec-002-optimizer-0_0_2.md#' .` -> no match), re-confirming the build plan's finding, so removing
  two headings breaks no link.

### Register decision: the rationale pointer is a reference-style link

At HEAD spec-002 carried **eight** spec-filename references and every one was a bare inline code
span (six after this pass: the `spec-001-rationale` path and one of the two `spec-003` mentions left
with the moved text); it carried **zero** inline cross-file links then and now, and its
`<!-- docs/SPECS/ -->` group was empty before this pass. The competing register was to name the
rationale file as a code span too, matching the file's own spelling. **Measured against the
immediate precedent instead:**
`docs/SPECS/spec-001-django_types-0_0_1.md`'s `<!-- docs/SPECS/ -->` group holds exactly one def —
`[spec-001-rationale]` — added by that spec's own R1 pass, and its seven pointer sites all read
`[rationale file][spec-001-rationale]`. Two sibling specs produced by the same cycle should point at
their companions the same way, so this pass took spec-001's shape. The cost is one def in a
previously-empty group; the benefit is that the pointer is navigable, which a code span is not.

### Concurrent-session churn observed (not this pass's, not reverted)

`git status --short` at pass open and at pass close, both measured:

- **Open (10 paths):** the build plan's nine baseline-dirty concurrent-session paths (`KANBAN.md`,
  `KANBAN.html`, `docs/SPECS/spec-042/043/044/050/051`, `examples/fakeshop/db.sqlite3`,
  `examples/fakeshop/test_query/README.md`) plus the untracked
  `docs/builder/build-002-optimizer-0_0_2.md`.
- **Close (13 paths):** the same 10, unchanged, plus this pass's three —
  `M docs/SPECS/spec-002-optimizer-0_0_2.md`,
  `?? docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`, and
  `?? docs/builder/bld-002-r1-rationale_move.md` (this artifact).

No baseline-dirty path changed state during the pass, and none was edited, reverted, or
`git checkout`-ed (`AGENTS.md` rule 34). This pass ran exactly two DB-touching commands, both
read-only: `check_spec_glossary.py` (no `--auto-link`) and `import_spec_terms --check`, whose
`--check` flag is documented and implemented as "validate DB rows against the CSVs **without
writing**". `import_spec_terms --check` reads 49 done cards here; the build plan's baseline also
reads 49.

### Temp tests used

Two throwaway scripts under `docs/builder/temp-tests/r1-spec002/` (gitignored), both read-only:

- `prove_move.py` — per-passage move proof (HEAD / spec / rationale counts), surviving-contract
  token check, link-definition audit (undefined refs, orphan defs, group-header order,
  `os.path.exists` per path), and in-page anchor resolution against slugged spec headings.
- `prove_move2.py` — the whitespace-normalized re-run of the move proof after the line-wrap artifact
  was found, plus the longest-shared-shingle scan.

Neither promotes to a permanent test — there is no package behavior to pin and no production code in
the diff. Both are candidates for a `scripts/` helper for future rationale moves; the spec-001 cycle
raised the same suggestion for its own `overlap.py`, so this is now the **second** cycle to hand-roll
a shared-shingle scanner. Raised under `### Notes for Worker 1`, not as a finding.

### Failability proofs

None; this pass introduced no new boundary, guard, gate, or rejection path. It writes no executable
code.

### Hot-path budget

Not applicable; plan declares no hot path (`build-002-optimizer-0_0_2.md` preamble: *"Hot-path
declaration: none. No residual item changes package source"*).

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **One global pointer plus two section-local ones.** Rule 1 wants a pointer per decision; a literal
  reading yields five, which on a 7.4KB spec would have cost more bytes than the narration they
  replace and would have made the pointer the loudest thing in three sections. Whole-section removals
  have no site left to carry a pointer, so those two are named in the one global line in
  `## Purpose`; the two sections that lost only part of their text carry their own, the
  `## Architecture decision` one as an appended clause rather than a paragraph.
- **The rationale keys on headings, not Decisions.** spec-002 predates the numbered-Decision
  convention (as spec-001 does). Two entries key to headings that no longer exist; each names the
  surviving section its argument bears on, so the entry is still lookup-able from the spec.
- **Claims are recorded in the spec's tense.** `BUILD.md`'s reader rule requires "any claim the
  decision once made and may no longer make". This pass records those claims *as the spec made them*
  and states in `## How to read this file` that whether the package still honours them is R2's
  determination. That is the only shape that discharges the reader's rule without doing R2's
  verification. The two open questions are the sharp case: they are recorded as open *because the
  spec left them open*, explicitly not as a claim they are unanswered at HEAD — and the build plan's
  drift row D3 says one of them shipped.
- **`## Open questions` moved rather than being deleted.** `worker-1.md` rule 2 says delete prose the
  current decisions have falsified; `BUILD.md`'s reader rule says carry claims the decision may no
  longer make. They pull in opposite directions here, and the spec-001 cycle hit the same tension and
  resolved it the same way (move it, quote it in the spec's own tense, mark the tense explicitly).
  Moving is the defensible reading: Worker 2 never reads this file, so no builder can implement a
  stale question, and deleting would have destroyed the question a later spec's answer is only
  meaningful against. **Deleting would also have been R2's determination, not R1's** — R1 has not
  read HEAD to establish that either question is answered.
- **Exactly one claim in the rationale rests on something outside the spec**, and it is disclosed:
  the Architecture-decision entry says `DjangoOptimizerExtension` is an extension a consumer adds to
  `strawberry.Schema(..., extensions=[...])`, which is the premise of "the optimizer can be absent".
  Taken from the spec's own `## Current state` ("exported from `django_strawberry_framework.__init__`")
  and from `GOAL.md`'s worked example (`extensions=[lambda: _optimizer]`), not from a HEAD source
  read. It is a statement about why an alternative lost — a rationale-file obligation — not a
  reconciliation of spec text, which stays R2's.
- **The spec's self-duplication was collapsed, in the one direction the move licenses.** `## Purpose`
  and `## O4 extraction` each carried half of one fact. The copy inside the moved section moved; the
  copy inside the surviving section stayed and absorbed the half that would otherwise have been lost.
  Collapsing a duplication whose *both* copies survive would have been an R2 edit; there is no such
  case left in this spec.

### Notes for Worker 3

- **The audit's sharpest question is over-cut, not under-cut.** Read `### What deliberately STAYED,
  and why` first, then the three repairs, then look for a **fourth** place where a cut sentence was
  the only statement of a rule. Repair 2 exists because that check found one (the "high level only"
  scope rule, stated only inside `## O4 extraction`); a second would be a High.
- **Attack repair 3 hardest.** It is the one restatement that changes a sentence's logical shape
  (`or` -> `and`, descriptive -> normative). The claim made in `### Minimal repairs` is that the
  proposition is unchanged. Re-derive that rather than accepting it; if the two readings differ, the
  spec now states a contract the original did not, which is the defect this move is most likely to
  cause.
- The diff to read is `git diff -- docs/SPECS/spec-002-optimizer-0_0_2.md` plus the new untracked
  `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`. **Do not `git stash`, `git checkout`, or
  `git restore` anything** — the tree carries a concurrent session's work
  (`### Concurrent-session churn observed`).
- Re-run all four verification commands yourself rather than accepting the quoted output. The
  3-anchor constraint is this pass's one silent failure mode. Note that **all three** anchors have
  exactly one spec-body link each — there are no spare links anywhere in this spec, so the watchlist
  is every glossary-linked sentence, not a subset. (This is the corrected form of the handoff the
  spec-001 cycle's R3 had to restate; stated correctly here the first time.)
- **The line-wrap trap is real** — see `### Move-not-copy proof`'s method note. If you re-run the
  move proof with un-normalized multi-word tokens you will get seven false "the text is missing"
  hits.
- A passage this pass left in the spec is **not** an R1 finding if the reason it looks wrong is that
  HEAD falsifies it. That is R2, by the build plan's own scoping. It *is* an R1 finding if the
  passage is deliberation or self-narration that should have moved.
- Not a finding, pre-assessed: `## References`'s issue #572 / PR #583 bullet reads as though it
  points into spec-001's moved bundling argument. The spec-001 cycle's R3 established that the
  sentence's locator is the upstream issue and PR themselves, so it does not dangle. Do not re-raise
  it.

### Notes for Worker 1 (spec reconciliation)

Carried into R2, from performing this move:

1. **`KANBAN.md:310` (card `TODO-ALPHA-052-0.1.0`) is now stale in one particular, and R1 caused
   it.** Its deferral reads *"`spec-002…` carries four status-shaped sections: `## Current state`,
   `## Shipped slices`, `## Visibility status`, `## Open questions`."* This pass removed
   `## Open questions`, so the count is three and one named section no longer exists. `KANBAN.md` is
   DB-generated and outside every residual item's write set, so **this is a hand-over, not a fix**,
   and it has a named owner: **R2's Worker 1 pass** decides whether the retitle discharges the
   deferral, and **R3** owns any `CardItem.text` edit + regenerate if the maintainer authorizes one.
   Recorded here rather than left floating because a recommendation with no named owner dies in the
   artifact.
2. **The retitle decision R2 inherits is now over three sections, not four.** The standing-promise
   shape argument (a section named for the present is a promise no shipped spec can keep) still
   applies to `## Current state`, `## Shipped slices`, and `## Visibility status`. The two prose
   constraint sites the build plan tabled are unaffected by this pass:
   `spec-003…:333` names "current state, visibility status, and checklist" and `spec-006…:136`/`:147`
   name "Visibility status" — all three still exist. Re-verified after the move.
3. **Anchor budget for R2, stated in its operative form.** All three anchors have exactly **one**
   spec-body link each — `only-projection` in `## Purpose` sentence 1, `djangotype` in
   `## Problem statement` bullet 1, `djangooptimizerextension` in `## Current state`. There are no
   spare links. Any rewrite, merge, or deletion touching one of those three sentences must re-site
   that anchor's link into surviving **contract** prose in the same edit — never by keeping
   narration, never by editing the terms CSV — and `check_spec_glossary.py` is re-run after every
   spec write, not once at the end. **Two of the three sit in sections R2 is most likely to open**
   (`## Current state` is drift row D14's home; `## Purpose` states the family scope rule).
4. **Drift noticed while moving, beyond D1-D15, and not acted on.** Two, both R2's:
   - `## Shipped slices` has **no blank line** between the end of the O3 paragraph and the
     `### O4 — Nested prefetch chains` heading (spec `:47`/`:48`), unlike every other slice boundary
     in the section. Cosmetic, pre-existing at HEAD, left alone because it is not deliberation.
   - `## Coordination with spec-001…` says spec-001's "Slices 4–6 are superseded by this optimizer
     spec family" while `## Current state` claims O1-O6 shipped under *this* spec. Whether the
     family framing or the this-spec framing is the accurate one at HEAD is exactly D6/D10/D11/D12's
     question, and the build plan's scope trap warns against resolving it by absorbing spec-003 /
     004 / 033 / 035 into this parent. Flagged, not touched.
5. **The precedent this pass sets for R2 on the rule-2-versus-reader-rule tension.** `## Open
   questions` was moved and tense-marked rather than deleted, matching the spec-001 cycle. R2 will
   face the same choice on prose HEAD falsifies. State the resolution once in R2's plan so it is not
   re-decided per row: **move and tense-mark when the claim is deliberation the package later
   answered; delete when the claim is a false assertion about the package.**
6. **A shared-shingle scanner is now the second hand-rolled one.** The spec-001 cycle raised
   `overlap.py` as a `scripts/` candidate and it was not promoted; this pass hand-rolled the same
   thing. The recurring cost is the re-implementation, and the tool the process actually needs
   performs: per-passage HEAD/spec/companion presence counts on whitespace-normalized text, longest
   shared shingle with the link-def block stripped, and a link-definition + in-page-anchor audit.
   Maintainer's call, not a build item; carried into the final gate's `### Deferred work catalog`.

---

## Review (Worker 3)

Audit of a **documentation move**, so most code-review axes do not apply and are stated as absent
rather than padded: no source or test file is in the diff, no new boundary / guard / gate /
rejection path exists, no ORM or async behavior changed, no public surface moved, and
`scripts/review_inspect.py` was **not run** — `BUILD.md` `### When to run the helper during build`
triggers on `.py` files and this diff contains none. No `pytest` was run and none was owed
(`AGENTS.md` rule 15; nothing executable is in the diff). No failability proof is owed and none was
performed. Hot-path and floor-verification scopes are both `none` in the plan preamble.

The diff reviewed is exactly the cycle's three paths: `git diff -- docs/SPECS/spec-002-optimizer-0_0_2.md`
plus the two untracked files. `git status --short` was read at pass open and pass close and is
**13 paths, identical at both ends** — the nine baseline-dirty concurrent-session paths, the
untracked `build-002-optimizer-0_0_2.md`, and this cycle's three. Nothing baseline-dirty was edited,
reverted, or `git checkout`-ed.

**What was re-derived versus accepted on the record.** Every mechanical claim in
`## Move performed` was re-derived independently, from a fresh read-only HEAD copy obtained with
`git show HEAD:docs/SPECS/spec-002-optimizer-0_0_2.md > /tmp/dsf-spec002-head.md` (no `stash`, no
`checkout`, no `restore`, no `worktree`): the per-passage move proof, the surviving-contract token
set, the longest-shared-shingle scan, the glossary-anchor counts against HEAD, the link-definition
scaffold on both files, the in-page anchor resolution, the rule-27 sweep, all four validation
commands, and both byte measurements. Accepted on the record, with the reason: Worker 1's report of
what the two `temp-tests/r1-spec002/` scripts did (gitignored, outside the diff — my own audit
re-implements the same checks independently, which is the stronger evidence), and the spec-001
cycle's prior assessment of the `## References` #572/#583 bullet (a prior artifact I did not read;
I assessed that bullet independently on a *different* ground — see Low 3).

### High:

None.

The failure mode this pass exists to catch is an **over-cut**: a normative sentence leaving with the
narrative around it. I walked every removed block against the current spec and asked, per block,
whether an obligation, constraint, or division-of-labour statement is now unstated anywhere. None
is. Detail under `### What looks solid`; the two claims the dispatch named for verification —
`## Architecture decision`'s two conditions and `## O4 extraction`'s scope rule — both hold, and
both were verified against the text rather than accepted.

The 3-anchor constraint holds and is **anchor-neutral**, not merely non-fatal:
`grep -o '\]\[glossary-[a-z0-9_-]*\]' | sort | uniq -c` gives `1 / 1 / 1` for
`djangooptimizerextension`, `djangotype`, `only-projection` against **both** the HEAD copy and the
current spec, and an independent regex for the inline `](../GLOSSARY.md#…)` form returns the empty
set in both, so the reference-style count is the whole population.

### Medium:

None.

Three Medium-tier questions were asked and each answered negative:

- **Does any rationale entry name no spec decision?** No. All four entries name a surviving spec
  section by heading **and** resolving anchor: `#problem-statement` (+ `#purpose`,
  `#coordination-with-spec-001-django_types-0_0_1md`), `#purpose`, `#architecture-decision`,
  `#shipped-slices`. Every one was slugged from the spec's *actual* headings and checked, not read
  by eye. The two entries keyed to headings that no longer exist say so explicitly and name the
  surviving section their argument bears on, which is what makes them lookup-able.
- **Was any inbound reference left stale and unrouted?** An independent tree-wide sweep for the two
  removed headings (`grep -rn "O4 extraction"`, `grep -rn "Open questions"`, excluding this cycle's
  own artifacts) finds exactly **one** site made stale by this pass: `KANBAN.md:310`. It is routed,
  in the artifact, on disk, with two named owners and their actions. That is what
  `BUILD.md` requires; the residual imprecision in the routing is Low 4, not a Medium.
  `spec-003:333` ("current state, visibility status, and checklist") and `spec-006:136`/`:147`
  ("Visibility status") name only sections that survive — re-verified against the slugged heading
  list, not against the build plan's table.
- **Was R2's work done in R1?** No. The diff touches six sites and no claim about the package was
  reconciled: `## Current state`, `## Shipped slices` (all six O-slices), `## Visibility status`,
  `## Coordination with spec-001…`, `## References`, and `## Implementation checklist` are
  **byte-identical to HEAD**. No drift row D1-D15 was touched. The one edit that changes a
  sentence's grammatical shape (repair 3) changes voice, not proposition — derived below.

### Low:

#### 1. The rationale quotes the O4 scope rule in wording that is verbatim in neither spec version

The rationale carries the scope rule inside quotation marks twice, and neither is a quotation:

- `## Provenance of this record`: `The scope rule ("this parent spec records the shipped behavior at
  a high level only")`
- `### `## Purpose` and the former `## O4 extraction``: `"This parent spec records the shipped
  optimizer behavior at a high level only" is the sentence that stops this document being rewritten…`

HEAD's actual sentence is `This parent spec only records the shipped behavior at a high level.`; the
spec now reads `It records that behavior at a high level only`. Measured: each quoted string occurs
**0** times in the HEAD copy and **0** times in the current spec. The verbatim sentence *is*
recorded correctly one paragraph away, in the full-section quotation of `## O4 extraction`, so
nothing is lost — but a rationale file is a review instrument, and quotation marks around a
paraphrase invite a later pass to "restore" wording that never existed. Recommended change: drop
the quotation marks on both, or replace each with the HEAD wording already quoted below it.

Same tier, same file: the fourth entry opens `Bears on [Shipped slices][spec-002-shipped]…` where
the other three open `Spec: [heading][ref].` The `BUILD.md` requirement is met either way; the
inconsistency is a lookup cost in a file whose value is lookup.

#### 2. Two off-by-one counts in the artifact's own record; every delta and total is correct

`AGENTS.md`-adjacent process rule aside, `BUILD.md` `## Claims are proven mechanically` treats a
stated count as a measurement. Two are off by one, both in argumentative rather than load-bearing
positions — which is exactly where they hide:

- `Line count 114 -> 111` (and the header line's `7,398 bytes / 114 lines at pass start`). Measured:
  the HEAD copy is **113** lines and the current spec **110** (`wc -l` = 113/110; both files end
  with a newline; `splitlines()` agrees). The delta `-3` is right. The `114` is **inherited from the
  build plan's preamble**, so it will be re-quoted by R2 and R3 unless corrected there.
- `### Concurrent-session churn observed` says `the build plan's eight baseline-dirty
  concurrent-session paths` and then enumerates **nine** (five spec files, `test_query/README.md`,
  `db.sqlite3`, `KANBAN.md`, `KANBAN.html`) across the plan's seven bullets. The totals it derives
  from that figure — `Open (10 paths)` and `Close (13 paths)` — are both **correct** and both
  independently re-derived from `git status --short`.

Nothing downstream rests on either number. Recommended change: correct both, and correct the build
plan's `114 lines` so the error does not propagate.

#### 3. One chronology clause survives in the spec, in `## References`

`BUILD.md`: "the spec reads as a clean current contract … a reader must never reconstruct what is
currently true by applying a chronology to it." An independent regex sweep of the spec for
`as of|originally|during implementation|was extracted|predicted|confirmed it|previously|used to|no
longer|since shipped` returns exactly one hit, and it is not one of the passages this pass removed:

```docs/SPECS/spec-002-optimizer-0_0_2.md:76
The visibility-leak / `Prefetch` downgrade discussion that motivated bundling the optimizer with
`spec-001-django_types-0_0_1.md` originally: issue #572 and PR #583 on `strawberry-graphql/strawberry-django`.
```

That the two documents were once bundled is document history, and the rationale's own
*Alternative rejected — leave the optimizer inside `spec-001`* entry already owns it. This is
pre-existing at HEAD, sits in a section the pass deliberately did not open, and the pass records a
reason for keeping `## References` whole — but that recorded reason answers a *different* objection
(whether the #572/#583 locator dangles into spec-001's moved argument), which is why it is raised
here rather than treated as already-rejected. The reference itself is contract scaffolding and
should stay; only the word `originally` and the bundling framing are the finding. Not blocking: the
locator is correct, the sentence parses without it, and this is one clause.

#### 4. The `KANBAN.md:310` hand-off understates the licence R3 already has

The hand-off itself is sound and is the reason this is Low rather than Medium: the staleness is
named, attributed to this pass, and given two owners with two distinct actions. But it reads
`**R3** owns any `CardItem.text` edit + regenerate **if the maintainer authorizes one**`, and the
build plan does not require a maintainer authorization for this. It pre-authorizes exactly this:
`docs/GLOSSARY.md` / DB writes happen when *"R3's audit finds real drift"*, and R1 has now created
real drift in `CardItem.text`. The build plan's R3 checklist line also does not name a `CardItem.text`
edit among R3's obligations, so the only thing carrying this item into R3 is this artifact plus
R2's plan. Recommended change: state in R2's plan that R3's own drift trigger is already met, so
R3 does not stall waiting for an authorization the plan already gave. Escalated below.

### DRY findings

The build plan's own DRY rule — *"a fact told twice across the spec and its rationale sibling goes
stale in one of them"* — **holds, and is now a number rather than an assertion.** Independently
re-derived with a maximal-shared-shingle scan (link-definition blocks stripped, blockquote markers
stripped, whitespace normalized): the longest run shared between the spec and its rationale is
**12 words, one occurrence**, and it is the seam sentence quoted *inside* the rationale's statement
that it stayed in the spec — quotation with attribution, not duplication. With the link-definition
blocks included the longest run is **18 words, one occurrence**, and it is the six trailing
canonical group headers. Both figures match the artifact's exactly. There is no unlabelled prose
passage in both files. The rationale also shares **0 words** with `spec-003`, the document it hands
the O4 detail to.

**Escalated (not held): 281 words of the rationale's scaffolding are a near-verbatim copy of
`spec-001-django_types-0_0_1-rationale.md`.** Measured with `difflib.SequenceMatcher` over
whitespace-normalized, link-def-stripped word lists: **six contiguous shared runs of 12+ words
totalling 281 words = 14% of this file's 1,888-word body**, the largest a single **133-word** block
spanning the closing of the preamble and most of `## How to read this file`, plus a 71-word block in
the opening paragraph and 20 words opening `## Provenance of this record`.

The qualification that matters, and that I checked rather than assumed: **every shared run sits in
the scaffolding, and zero land in `## Entries keyed to the spec`.** All six blocks fall at word
offsets 27-402; the entry section begins after them. The deliberation — the part with review value —
is independently authored.

Why this is escalated and not a rejection:

- One of the copied bullets (*"Worker 3 reads it during review; Worker 1 owns it; Worker 2 never
  reads it"*) is a restatement of `BUILD.md` `### Who reads it, and when`, whose own
  `### Where a mechanism belongs` rule says a mechanism two roles touch lives in `BUILD.md` and is
  **pointed at**, not copied — "a role file is not re-read when a mechanism changes, so a copy there
  goes stale silently". Every future rationale file inherits the copy.
- The consolidation target therefore spans `spec-001`'s rationale, `BUILD.md`, and every rationale
  file not yet written. **None of those is in R1's write set**, and Worker 3 does not hold a unit at
  `revision-needed` on a defect it cannot dispatch.
- Worker 1 recorded the reuse as a deliberate decision with a stated reader benefit ("a reader who
  has read one rationale file can read this one"), and the spec-001 cycle established the precedent
  and had it accepted. Rejecting a pass for following an accepted precedent is the wrong lever.

Existence challenge: not raised. Whether a rationale companion should exist is settled by
`BUILD.md` `## Spec rationale extraction`, not by a reviewer.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list
are unchanged. This pass touches no `.py` file at all: the complete diff is one modified `.md`, one
new `.md`, and this artifact.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

This is the pass's main axis. Every bullet walked against the two changed documents read end to end:

- **Version strings, statuses, card IDs.** The spec carries no status/header block (confirmed:
  line 1 title, line 2 blank, line 3 `## Purpose`), so nothing there can drift. The rationale names
  card `DONE-002-0.0.2` and *"twelve patch versions ago"*; `pyproject.toml` is at `0.0.14`, and
  `0.0.2 → 0.0.14` is twelve increments. Correct. No version string, shipped/planned status, or
  card ID was introduced or changed by the diff.
- **KANBAN movement.** None; no card moved and no DB write occurred. The two DB-touching commands
  the pass ran are read-only (`check_spec_glossary.py` without `--auto-link`;
  `import_spec_terms --check`), and I re-ran both to the same output.
- **Links point at existing files.** All 14 link definitions across both files were
  `os.path.exists`-checked on the normalized join with the fragment stripped: **14/14 present.**
  Depth is right for a file two levels below `docs/` — `../../GLOSSARY.md#…` and
  `../../builder/BUILD.md` for `docs/` and `docs/builder/` targets, `../spec-00N-….md` for
  `docs/SPECS/` siblings, and a bare filename for the `appx/` sibling. Both files carry exactly one
  `<!-- LINK DEFINITIONS -->` delimiter and all **10** canonical group headers in `START.md`'s exact
  order, verified positionally; defs are alphabetical within every group; 4 defs / 4 uses and
  10 defs / 10 uses, **0 undefined and 0 orphaned** in both; **0** inline cross-file `](path)` links
  outside fences in either body. All five in-page anchors the rationale cites resolve against
  surviving spec headings, slugged from the spec's real headings rather than eyeballed. The
  cross-document citation into spec-001's rationale (*"Whole-document scope — the optimizer was
  bundled deliberately"*) resolves to a real heading in that file — checked, because a
  non-resolving cross-doc citation would have been the cheapest way for this entry to look
  well-sourced and be empty.
- **Archival.** No move performed and none owed; the spec and its `-terms.csv` were already at
  their archived paths. The new companion was written **directly** to `docs/SPECS/appx/`, which is
  the location `AGENTS.md` rule 26 names, and its def sits under `<!-- docs/SPECS/ -->` per
  `START.md`'s closed-list rule. `spec-002-optimizer-0_0_2-terms.csv` is untouched.
- **Verbatim-text confirmation by `diff`.** Both moved `## Open questions` entries are verbatim
  against the HEAD copy — checked on whitespace-normalized text with blockquote markers stripped,
  since both are blockquoted and wrapped; the only change is `**bold**` on the two leads. The
  `## O4 extraction` section is quoted verbatim in full. The two non-verbatim quotations are Low 1.
- **No obsolete wording.** No "coming soon" / "planned" / old-version wording was introduced. The
  spec's remaining status-shaped sections are byte-identical to HEAD and are R2's axis by the plan's
  own scoping, not R1 residue.
- **Script-rendered docs.** None regenerated and none needed regenerating; no module docstring is in
  the diff.
- **`AGENTS.md` rule 27.** `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over **both** files returns no
  match. Preserved, as the build plan says, rather than established.
- **Validation commands, all four re-run rather than accepted:**
  `check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md` →
  `OK: 3 terms - all have glossary entries and at least one spec link.` exit 0;
  `manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` exit 0;
  `check_trailing_commas.py --check` → exit 0 on the spec and exit 0 on the rationale, run
  separately so neither result masks the other; `git diff --check` → exit 0. Every one matches the
  build plan's recorded pre-move baseline.
- **Staged-anchor sweep** re-run independently: `grep -rEn 'TODO\(spec-002|TODO-(ALPHA|BETA|STABLE)-002'`
  finds only the build plan's own checklist line describing the sweep. No anchor introduced.

### What looks solid

- **The move is a move, re-derived passage by passage.** I built my own passage list from the
  `git diff` rather than from the artifact's table, and extended it to 18 tokens. Result:
  **HEAD ≥ 1 / spec 0 / rationale ≥ 1** on 16 of 18. The two that did not match resolve on
  inspection and are not defects — both are facts that were *reworded* rather than relocated, and
  both survive: `"The O4 design record remains in"` is now `"the detailed O4 design and
  implementation record belongs to"` **in the spec** (so the fact must not be in the rationale), and
  `"That prediction is recorded in <spec-001 rationale>"` is now carried by the rationale's own
  sentence *"That prediction … [is] recorded in [`spec-001-django_types-0_0_1-rationale.md`]"* with
  a resolving link def. Nothing was copied into both files, and nothing was dropped from both.
- **`## Architecture decision`'s two conditions survive the restatement — verified, not accepted.**
  This is the edit the pass itself flagged as the likeliest to introduce a contract the original did
  not state, so I re-derived it rather than reading it. HEAD asserts correct behavior over the
  *union* of two cases: `∀s. (optimizer-disabled(s) ∨ relation-not-loaded(s)) → correct(s)`. The new
  sentence distributes `when` across two adverbial clauses — "must return correct results **when**
  the optimizer is disabled **and when** a relation is not already loaded" — which is
  `(∀s. disabled(s) → correct(s)) ∧ (∀s. not-loaded(s) → correct(s))`. Those are the same
  proposition; `or` over a domain and `and` over two obligations distribute into each other. The
  simultaneity misreading is not grammatically available here, because it would require
  *"when X and Y"*, not *"when X and when Y"* — the repeated `when` is the disambiguator, and it is
  present. Both condition tokens are still in the spec exactly once each
  (`when the optimizer is disabled`, `when a relation is not already loaded`). The voice moved from
  descriptive to normative, which strengthens a contract rather than narrowing it. **Recorded here
  so a later pass does not "fix" it back.**
- **The `## O4 extraction` fold is real and was the right call.** The cut section carried two facts;
  the ownership pointer was already in `## Purpose` and the scope rule was not. `at a high level
  only` and `detailed O4 design and implementation record belongs to` and `keep detailed O4
  rationale there rather than duplicating it here` are all present in the spec exactly once. Had
  the section been cut without the fold, the scope rule — the one sentence that stops this parent
  spec being rewritten into a summary of `spec-003` / `004` / `033` / `035`, which is precisely the
  trap the build plan warns R2 about — would have been stated nowhere. Finding the fourth
  over-cut the artifact invited me to hunt was the point of this pass; there is no fourth.
- **Removing `## Open questions` removes no obligation.** Both entries are forward-looking
  (*"should eventually"*, *"should be considered in a future optimizer-control spec"*) and neither
  was ever a spec-002 contract — spec-002's own contract is O1-O6, and those sections are untouched.
  Both behaviours have since shipped under other specs, and the current consumer-facing statement of
  the override contract lives in `docs/README.md` (*"generated relation resolvers, with
  annotation-only and `strawberry.field` consumer overrides preserved"*) — checked, so that removing
  the question from a 2026-era archived spec strands no reader.
- **The one rationale claim resting on something outside the spec is disclosed and true.** The
  Architecture entry's premise that `DjangoOptimizerExtension` is an extension a consumer adds to
  `strawberry.Schema(..., extensions=[...])` — the premise of "the optimizer can be absent" — is
  disclosed in `### Implementation notes` and is corroborated by `docs/README.md`'s quick start
  (`extensions=[lambda: _optimizer]`, four call sites). A rationale premise that turned out to be
  false would have been the quiet way for this file to become misleading.
- **Every removed block was checked for a surviving statement of its rule, not just for absence.**
  Fifteen surviving-contract tokens confirmed present in the spec exactly once each, including the
  three the pass did not enumerate (`_is_default_get_queryset`, `has_custom_get_queryset`,
  `TypeRegistry` — the `## Coordination` division-of-labour surface, which a careless cut of the
  adjacent sections could have taken with it).
- **Byte accounting is exact and doubly derived.** Spec `7,398 → 7,093 = -305` by direct `wc`, and
  independently `+1,153 / -1,458 = -305` by summing `git diff -U0` line bytes — both re-run, both
  agreeing with the artifact to the byte. Rationale 13,077 bytes. The pass's own reading of `-4.1%`
  as the honest small number, rather than inflating it by cutting `## Current state` or
  `## Shipped slices` (which would have spent R2's work and both of those sections' glossary
  anchors), is the correct call and is worth preserving as precedent.
- **The pointer-inflation judgement.** Three pointer sites (one global in `## Purpose`, two
  section-local) rather than the five a literal reading of the per-decision pointer rule yields.
  Confirmed: `[spec-002-rationale]` is used exactly 3 times in the spec body plus its one def.
  On a 7.4KB spec, five would have made the pointer the loudest thing in three sections.

### Temp test verification

- `docs/builder/temp-tests/r1-spec002-w3/audit.py` (gitignored; **new directory**, suffix per the
  dispatch — no prior `r1*` directory was reused, read, or deleted). One read-only script over the
  two Markdown files plus the read-only HEAD copy at `/tmp/dsf-spec002-head.md`, independently
  implementing: the 18-passage move proof on whitespace-normalized, blockquote-stripped text; a
  15-token surviving-contract check; the maximal-shared-shingle scan; glossary-anchor counts in both
  reference and inline forms, HEAD versus now; the full link-definition audit (delimiter count,
  10 group headers positionally, alphabetical within group, undefined refs, orphan defs,
  `os.path.exists` per target, inline-cross-file-link sweep); in-page anchor resolution against a
  privately written GitHub slugger; the rule-27 sweep; and the chronology sweep. Two further
  throwaway `python3 -` snippets measured the byte/line counts and the `difflib` cross-rationale
  overlap.
- **The line-wrap trap the artifact flagged is real and I hit it too**: my first pass reported
  passages "missing" purely because the rationale wraps at 100 columns and quotes two of them as
  blockquotes. Normalizing whitespace and stripping `> ` prefixes is mandatory, not optional. The
  slugger was written privately rather than imported from `check_spec_glossary.py::github_anchor`,
  which is known to return garbage on a heading that is itself a reference link.
- **Disposition: none promoted.** There is no package behavior to pin and no production code in the
  diff. But this is now the **third** hand-rolled implementation of the same scanner across two
  cycles — see the note below, which corrects the artifact's account of where that item stands.

### Notes for Worker 1 (spec reconciliation)

1. **`Escalated:` — the 281-word scaffolding copy between rationale files** (`### DRY findings`).
   Resolution paths, for the maintainer: (a) accept as a template and say so once, so no future
   reviewer re-litigates it; (b) reduce the `## How to read this file` "Who reads it" bullet to a
   pointer at `BUILD.md` `### Who reads it, and when`, which is that mechanism's canonical home and
   the one bullet most likely to go stale silently; (c) emit the preamble from a generator, which
   folds naturally into the checker already on the board (note 3). Not held at `revision-needed`:
   the consolidation target is outside R1's write set and the precedent was accepted in the
   spec-001 cycle.
2. **`Escalated:` — R2 inherits two drift rows whose spec-side target no longer exists.** Removing
   `## Open questions` was plan-authorized and correct, but drift rows **D3** (custom-resolver
   opt-out, "shipped") and **D13** (`only()` opt-out, "answered and shipped") were rows against
   *that section*. Their resolution now has no spec text to correct. The rationale already routes
   them — *"the answer belongs in the spec (as contract, if the answer shipped) or in this file's
   change record (as a claim the spec no longer makes)"* — but the artifact's own
   `### Notes for Worker 1` does not say so, and R2's plan should state the routing once rather than
   rediscover it per row. Note that `worker-1.md` gives Worker 1 the rationale file, so R2 *can*
   write that change record; R3 cannot.
3. **Correction to the artifact's note 6, so the final gate's `### Deferred work catalog` does not
   create a third entry for one item.** The artifact says the spec-001 cycle's `overlap.py`
   suggestion "was not promoted". It **was** — `KANBAN.md:309`, in the same card
   `TODO-ALPHA-052-0.1.0` deferral list as the `:310` bullet this pass made stale, already carries
   *"Promote a spec/rationale consistency checker into `scripts/`"* with a richer specification than
   either cycle's hand-rolled script (link scaffold, the 10 group headers positionally, alphabetical
   ordering, on-disk resolution with the fragment stripped, a markup-rendering slugger, the inline
   cross-file sweep, the rule-27 sweep, and the maximal-shared-shingle scan). My `audit.py` is the
   third hand-roll and implements exactly that list. The item is tracked; what it needs is an owner,
   not a third raising.
4. **Low 4's operative form for R2's plan.** R3's own drift trigger for a DB write is already met —
   R1 created real `CardItem.text` drift — so R2's plan should say that plainly rather than leaving
   R3 to read "if the maintainer authorizes one" and stall. Both `:309` and `:310` sit in the same
   card's deferral list, and `:310`'s wording is wrong in two particulars now: the count (`four
   status-shaped sections`) and one named section (`## Open questions`) that no longer exists. Its
   claim *"All four are accurate at HEAD today"* is also load-bearing for the deferral's own
   argument, so a `CardItem.text` edit is a rewrite of that sentence, not a number change.
5. **The retitle decision R2 inherits is over three sections, re-verified.** `## Current state`,
   `## Shipped slices`, `## Visibility status` all survive; `## Implementation checklist` also
   survives and is arguably a fourth status-shaped section the card never counted. The two prose
   constraint sites are unaffected — I re-derived this against the slugged heading list rather than
   against the build plan's table: `spec-003:333` names "current state, visibility status, and
   checklist" and `spec-006:136`/`:147` name "Visibility status"; all three targets exist.
6. **The three Low findings that are one-line fixes** (Low 1's two quotation marks, Low 2's two
   counts including the build plan's inherited `114 lines`, Low 3's `originally` clause) are named
   here so Worker 1 can fold them into R2's spec pass rather than re-looping R1 for them. None
   blocks acceptance.

### Review outcome

`review-accepted`.

No High and no Medium finding. Four Low findings, each a one-line fix, none affecting a contract:
two rationale-precision nits, two artifact-record count slips whose deltas and totals are correct,
one surviving chronology clause in a section the pass deliberately did not open, and one hand-off
that understates a licence the build plan already granted. The DRY finding is escalated to Worker 1
and the maintainer with resolution paths rather than held, because its consolidation target lies
outside R1's write set and its precedent was accepted in the prior cycle.

The move is a move: proved passage by passage against a read-only HEAD copy, with a longest shared
prose run of 12 words which is a labelled quotation. Nothing normative left the spec — the two
claims the audit was pointed at (`## Architecture decision`'s two conditions, `## O4 extraction`'s
scope rule) both hold under re-derivation, and there is no fourth over-cut. The spec no longer
narrates its own history except for one pre-existing clause in `## References`. All three glossary
anchors carry the identical 1/1/1 link counts they carried at HEAD, so the card-wrap chain for card
2 is intact and `import_spec_terms --check` still reads 49 done cards. R1 stayed inside its scope:
every status-shaped section and every drift row D1-D15 is byte-identical to HEAD.

---

## Final verification (Worker 1)

Fresh spawn, no memory of the pass that performed the move. Every mechanical claim below was
re-derived from a read-only HEAD copy obtained with
`git show HEAD:docs/SPECS/spec-002-optimizer-0_0_2.md > <scratch outside the repo>` — no `stash`,
no `checkout`, no `restore`, no `worktree`. Scratch under
`docs/builder/temp-tests/r1-spec002-fv/` (new directory; the two prior `r1-spec002*` siblings were
neither read, reused, nor deleted).

**Four Low findings, each ruled on explicitly. Three were fixed; the DRY escalation was split.**
Three files were edited in this pass: the spec, the rationale, and this artifact.

### Dispatched findings checklist — audit

All 13 boxes were `- [x]` at review-accepted. Each was re-verified against the diff rather than
read; none was un-ticked, none was left `- [ ]`, so no deferral reason is owed.

- Box 1 (**move, not copy**). Re-derived on whitespace-normalized, blockquote-stripped text: six
  removed passages measured HEAD 1 / spec 0 / rationale >= 1, and sixteen surviving-contract tokens
  measured **exactly once each** in the current spec (`RelatedManager`, `before relation resolvers
  evaluate model attributes`, `share one seam`, `keep detailed O4 rationale there rather than
  duplicating it here`, `at a high level only`, `B2/B3 runtime sentinels`, `when the optimizer is
  disabled`, `when a relation is not already loaded`, `info.path.prev is None`, `pass through
  unchanged`, `detailed O4 design and implementation record belongs to`,
  `_is_default_get_queryset`, `has_custom_get_queryset`, `TypeRegistry`, `issue #572 and PR #583`,
  `visibility-leak`). The last two were added to the list by this pass because the `## References`
  edit below opens that sentence. Holds.
- Box 2 (**`## O4 extraction` gone, scope rule folded**). `## O4 extraction` occurs 1x in HEAD,
  **0x** in the spec; its body is verbatim in the rationale; `at a high level only` is in
  `## Purpose` exactly once. Holds.
- Box 3 (**`## Open questions` gone, both questions verbatim**). Heading 1x HEAD / **0x** spec.
  Both question bodies measured **verbatim** against HEAD on normalized text with the two added
  `**bold**` leads stripped. Holds.
- Box 4 (**the spec no longer narrates its own history**). The three phrases the box enumerates are
  gone, but the box's headline claim was **false at review-accepted** — Low 3's `originally` clause
  survived in `## References`. Rather than un-tick a box whose enumerated contract landed, this pass
  **made the headline true**: the clause was moved (see `### Spec changes made (Worker 1 only)` 1
  and 2). The chronology regex Worker 3 used
  (`as of|originally|during implementation|was extracted|predicted|confirmed it|previously|used
  to|no longer|since shipped`) now returns **zero hits** over the whole spec. Holds, and now holds
  for the reason the box states.
- Box 5 (**every entry names its spec section by heading and anchor**). Entry 4 opened `Bears on …`
  where the other three open `Spec: …`; fixed (change 3). All four entries now carry a `Spec:` lead
  line, and all **six** anchor fragments the rationale cites (`#architecture-decision`,
  `#coordination-with-spec-001-django_types-0_0_1md`, `#problem-statement`, `#purpose`,
  `#references`, `#shipped-slices`) resolve against the spec's actual slugged `##` headings. Holds.
- Box 6 (**one-line pointer per decision that lost text**). `[spec-002-rationale]` used exactly
  **3** times in the spec body plus **1** def. Holds.
- Box 7 (**written directly to `docs/SPECS/appx/`**). Holds; no move step exists or is owed.
- Box 8 (**reference-style links, one delimiter, ten headers, disk-checked, anchors resolve**).
  Re-audited after every edit: one `<!-- LINK DEFINITIONS -->` each; the ten canonical group
  headers in `START.md` order, verified positionally; **alphabetical within every group**, verified
  programmatically rather than by eye; spec **4 defs / 4 uses**, rationale **11 defs / 11 uses**
  (10 before this pass added `[spec-002-references]`), **0 undefined and 0 orphaned** in both; every
  def `os.path.exists`-checked on the normalized join with the fragment stripped, **15/15 present**;
  **0** inline cross-file `](path)` links outside fences in either body. Holds.
- Box 9 (**3-anchor constraint, counts identical to HEAD**). `grep -o '\]\[glossary-[a-z0-9_-]*\]'`
  gives `1 / 1 / 1` for `djangooptimizerextension`, `djangotype`, `only-projection` after every
  edit, identical to HEAD. `docs/SPECS/appx/spec-002-optimizer-0_0_2-terms.csv` remains
  byte-untouched. Holds.
- Box 10 (`import_spec_terms --check`). Re-run twice, before and after the edits: `OK: 49 done
  cards have glossary links.` exit 0. Holds.
- Box 11 (`check_trailing_commas --check`, no raw `path:NN`). Re-run on all three files after the
  edits: exit 0. Rule-27 sweep over the spec and the rationale: **no match**. Holds.
- Box 12 (**byte count reported before and after, two agreeing measurements**). The reported byte
  figures were correct; the **line** figures were not, and are corrected below. This pass's own
  spec edit is proved by reinsertion rather than by diff-reading: `len(removed literal)` = **87
  bytes**, `7,093 - 7,006` = **87**, and re-inserting the literal reproduces a **7,093-byte** file.
  Holds, with the corrected numbers now in `### Byte counts`.
- Box 13 (**R2's work was not done here**). Re-confirmed: no claim was reconciled against HEAD, no
  drift row D1-D15 was touched, and every removed status-shaped claim is recorded in the rationale
  in the spec's own tense. `## Current state`, `## Shipped slices`, `## Visibility status`,
  `## Coordination with spec-001…`, and `## Implementation checklist` remain **byte-identical to
  HEAD**. **`## References` no longer is** — see change 1; the edit removes a document-assembly
  chronology, not an upstream pointer, so it is R1's charter and not D15's claim-verification work.
  Holds, with that one correction to Worker 3's byte-identity statement.

### Disposition of the four Low findings

**Low 1 — quotation accuracy. FIXED.** The finding is real and was measured, not accepted. Both
quoted strings occur **0 times in the HEAD spec and 0 times in the current spec**:

```
0 HEAD | 0 spec | 1 rat  :: this parent spec records the shipped behavior at a high level only
0 HEAD | 0 spec | 1 rat  :: This parent spec records the shipped optimizer behavior at a high level only
1 HEAD | 0 spec | 1 rat  :: This parent spec only records the shipped behavior at a high level
0 HEAD | 1 spec | 0 rat  :: It records that behavior at a high level only
```

A quotation mark is a claim about bytes, and in a review instrument a paraphrase inside quotes
invites a later pass to "restore" wording that never existed. Both were replaced with the **current
spec's** verbatim sentence (`"It records that behavior at a high level only"`, measured 1x in the
spec), attributed to `## Purpose`, because both sites are describing what the spec says *now*
rather than what HEAD said; the HEAD wording remains quoted verbatim one paragraph away in the
full-section quotation, which is where it belongs. Entry 4's missing `Spec:` lead line was fixed in
the same pass. Every quotation this pass itself introduces was re-measured against HEAD before
being written — including the moved `## References` clause, verified as a byte-exact substring of
the HEAD sentence.

**Low 2 — off-by-one counts. FIXED, and one copy Worker 3 did not name was found.** Measured:
HEAD is **113** lines and the pre-final-verification spec **110** (`wc -l` 113/110, both files
newline-terminated, `splitlines()` agrees); the `-3` delta was right. Worker 0 had already
corrected the build plan. This pass corrected the four copies inside its own write set:

- header line, `114 lines` -> `113 lines`
- `### DRY analysis` bullet 2, `a 114-line document` -> `a 113-line document`
- `### Byte counts`, `Line count 114 -> 111` -> `113 -> 110`
- `### Concurrent-session churn observed`, `eight baseline-dirty` -> `nine` (the bullet already
  enumerated nine, and its derived totals of 10 and 13 were and are correct)

**The copy Worker 3's finding did not name is in the rationale file itself** —
`## Purpose`/`## O4 extraction` entry, *"Two statements of one fact in one 114-line document"* — and
that one matters more than the artifact's, because the rationale is committed and durable where the
artifact closes with the cycle. Corrected to 113. The five surviving `114` strings in this artifact
are all inside Worker 3's Low 2 finding text, which must keep the number it is a finding about.

**Low 3 — the surviving `originally` chronology clause in `## References`. FIXED NOW, not deferred
to R2.** Three reasons the deferral loses. First, it is **R1's charter, not R2's**: `BUILD.md`
`## Spec rationale extraction` — "a reader must never reconstruct what is currently true by applying
a chronology to it" — is the rule this item exists to enforce, while R2's axis is claim-versus-HEAD
drift, and a document-assembly chronology is not a drift row. D15 covers the four upstream
pointers' verification, and this edit verifies nothing and changes no pointer. Second, the
**destination already exists**: the rationale's *Alternative rejected — leave the optimizer inside
`spec-001`* entry owns the bundling argument, so the clause moves rather than being deleted, which
is what `worker-1.md` rule 2 versus the reader rule resolves to for deliberation. Third, leaving it
would leave box 4 ticked with its headline claim false. The **minimal** edit was taken: only the
clause left, and the sentence now matches the shape of the other four `## References` bullets
(`<topic>: <locator>`), asserting nothing new. Both `issue #572 and PR #583` and `visibility-leak`
were re-measured as still present in the spec exactly once.

**Low 4 — the `KANBAN.md:310` hand-off wording. TIGHTENED, in the hand-off list below, not by
rewriting the prior section.** Worker 3 is right: the build plan pre-authorizes a DB write when
*"R3's audit finds real drift"*, and R1 created real `CardItem.text` drift, so a second maintainer
authorization is not a precondition. The corrected form is carried in
`### Notes for Worker 1 (spec reconciliation)` item 1 below, which supersedes the `if the maintainer
authorizes one` wording in `## Move performed`'s notes. The prior section is left as written — a
performance record is not rewritten to match a later ruling, and the hand-off a later pass actually
reads is this one.

### Disposition of the escalated DRY observation — **split, not accepted and not deferred whole**

Re-measured independently with `difflib.SequenceMatcher` over whitespace-normalized,
link-def-stripped word lists rather than accepted: **6 runs of 12+ words, 281 words shared with
`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`, 14.9% of a 1,888-word body, largest
block 133 words** — Worker 3's figures reproduce (its "14%" is 281/1888 = 14.88% truncated). The
decisive qualification also reproduces: all six runs end by word offset **402** and
`## Entries keyed to the spec` begins at word **646**, so **zero shared words land in the
deliberation**. What has review value is independently authored.

The finding was split on one test: **does the run copy a mechanism with a canonical home
elsewhere, or is it template shape?**

- **Trimmed (one run).** The `**Who reads it.**` bullet — measured inside the 133-word block at word
  offset 189 — restates `BUILD.md` `### Who reads it, and when`. `BUILD.md`
  `### Where a mechanism belongs: this document, pointed at from the role files` governs it
  exactly: "a copy there goes stale silently — and a stale copy is worse than none". It is a
  one-line deletion **inside this item's write set**, replaced by a pointer at the canonical
  heading. It removes text the reviewer named and read, and adds no unreviewed judgement, which is
  the narrow case that distinguishes a legitimate custodian fix from implementing a Worker 3
  finding.
- **Kept, and routed (the other runs).** The title line, the companion preamble, and the
  `## How to read this file` framing have **no canonical home outside these two files**. Trimming
  them here would make the two siblings diverge — `spec-001`'s rationale is outside this item's
  write set, so a unilateral trim is the opposite of the DRY win it looks like — and would spend
  the reader benefit the pass recorded ("a reader who has read one rationale file can read this
  one"). The precedent was accepted in the spec-001 cycle.

Measured effect of the trim: **266 words / 13.0% of a 2,047-word body, largest block 133 -> 87**,
still 0 words in the entries section (max run end 411, entries start 701). The run count moved 6 ->
7 because the trim split the 133-word block, which is the trim working, not new duplication.

**Rejected alternative — trim the whole shared preamble here.** It loses on write-set: five of the
six runs would have to be re-authored in `spec-001`'s rationale too for the files to stay
consistent, and that file belongs to a closed cycle. Rejecting a pass for following a precedent
that was accepted is also the wrong lever, as Worker 3 said. **Rejected alternative — route all six
runs to the catalog and change nothing.** It loses because one of them has a canonical home,
`BUILD.md` names copies of exactly that mechanism as the failure mode, and the fix was a one-line
deletion already in hand: routing a fix you can make now to a catalog is the shortcut, not the
process.

**Carried to the final gate's `### Deferred work catalog`** (maintainer's call, not a build item):
the rationale-file preamble is a de-facto template with no single source, and the natural fix is to
emit it. That folds into the checker `KANBAN.md:309` already tracks — Worker 3's note 3 correctly
established that the item **was** promoted and needs an owner, not a third raising, and this pass's
own scanner is the fourth hand-roll.

### Standing final-verification checks

- **Existing tests still pass.** **Not run, and none is owed.** This item touches no source and no
  test: the complete diff is one modified `.md`, one new `.md`, and this artifact. `AGENTS.md`
  rule 15 forbids an unrequested run, and there is no package behavior a test could pin.
  No `--cov*` flag was passed to anything, because nothing was run.
- **`ruff`.** Not run; no `.py` file exists in the diff. A repo-wide `--fix` run would also sweep
  the concurrent session's files.
- **Failability proofs.** None owed; this item introduces no boundary, guard, gate, or rejection
  path.
- **Hot path / floor verification.** `Not applicable; plan declares no hot path.` and
  `Not applicable; plan declares floor-verification scope none.` Both confirmed against the plan
  preamble.
- **Staged-anchor sweep.** `grep -rEn 'TODO\(spec-002|TODO-(ALPHA|BETA|STABLE)-002'` finds only the
  build plan's own checklist line describing the sweep. No anchor introduced, none to remove.
- **R2 was not started here.** Confirmed by box 13. Everything R2-shaped is carried below.

### Re-verified commands, quoted exactly (run AFTER every edit)

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md
OK: 3 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-002-optimizer-0_0_2.md \
    docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md \
    docs/builder/bld-002-r1-rationale_move.md
exit=0

$ grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+' docs/SPECS/spec-002-optimizer-0_0_2.md \
    docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md
exit=1        # no match, in either file

$ git diff --check
exit=0
```

Both DB-touching commands are read-only (`check_spec_glossary.py` without `--auto-link`;
`import_spec_terms --check`). Every one was also run **before** the edits, to the identical output,
so the edits are proved neutral rather than merely passing.

**`git status --short` — measured at pass open and again at pass close, identical at both ends,
13 paths:**

```
 M KANBAN.html                                     <- concurrent session (baseline-dirty)
 M KANBAN.md                                       <- concurrent session (baseline-dirty)
 M docs/SPECS/spec-002-optimizer-0_0_2.md          <- this cycle
 M docs/SPECS/spec-042-debug_toolbar-0_0_14.md     <- concurrent session (baseline-dirty)
 M docs/SPECS/spec-043-test_client-0_0_14.md       <- concurrent session (baseline-dirty)
 M docs/SPECS/spec-044-debug_extension-0_0_14.md   <- concurrent session (baseline-dirty)
 M docs/SPECS/spec-050-debug_extraction-0_0_19.md  <- concurrent session (baseline-dirty)
 M docs/SPECS/spec-051-boundary_dry_squeeze-0_0_20.md  <- concurrent session (baseline-dirty)
 M examples/fakeshop/db.sqlite3                    <- concurrent session (baseline-dirty)
 M examples/fakeshop/test_query/README.md          <- concurrent session (baseline-dirty)
?? docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md  <- this cycle
?? docs/builder/bld-002-r1-rationale_move.md              <- this cycle (this artifact)
?? docs/builder/build-002-optimizer-0_0_2.md              <- Worker 0's plan
```

Exactly the nine baseline-dirty concurrent-session paths, Worker 0's untracked plan, and this
cycle's three. No path outside that set appeared, none changed state during the pass, and none was
edited, reverted, or `git checkout`-ed (`AGENTS.md` rule 34). No `stash`, `checkout`, `restore`, or
`worktree` was used at any point.

### Corrected measurements (this pass's edits included)

| File | HEAD | after the move | after final verification |
|---|---|---|---|
| `docs/SPECS/spec-002-optimizer-0_0_2.md` | 7,398 bytes / **113** lines | 7,093 / 110 | **7,006 / 110** |
| `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` | absent | 13,077 / 209 | **14,296 / 224** |

Spec total: **-392 bytes, -5.3%**, three lines. The additional -87 is the `## References` clause,
proved by reinsertion (above). The rationale grew 1,219 bytes: the moved clause and its framing,
entry 4's `Spec:` lead, the `[spec-002-references]` def, and the `Who reads it` pointer, minus the
copied mechanism it replaced.

**Longest shared prose run between the spec and its rationale is unchanged at 12 words**, one
occurrence, link-definition blocks and blockquote markers stripped — the seam sentence, quoted
inside the rationale's statement that it stayed in the spec. The build plan's DRY rule holds.

### Spec changes made (Worker 1 only)

1. **`docs/SPECS/spec-002-optimizer-0_0_2.md:76`** (`## References`, final bullet). Removed the
   87-byte chronology clause, leaving the locator untouched:

   ```
   - The visibility-leak / `Prefetch` downgrade discussion that motivated bundling the optimizer
     with `spec-001-django_types-0_0_1.md` originally: issue #572 and PR #583 on ...
   + The visibility-leak / `Prefetch` downgrade discussion: issue #572 and PR #583 on ...
   ```

   **Reason:** Low 3 — the last surviving self-narration in the spec, and `BUILD.md`
   `## Spec rationale extraction` forbids a reader reconstructing the current contract from a
   chronology. Minimal edit: the locator is byte-identical and the bullet now matches the shape of
   the other four. -87 bytes, proved by reinsertion.
2. **`docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`, `### Whole-document scope` entry.**
   Added the *Moved — what the spec recorded as the trigger for that original bundling* paragraph,
   quoting the removed clause verbatim (verified as a byte-exact substring of the HEAD sentence)
   beside the alternative it explains; updated the `**Moved**` and `**Deliberately left**` bullets
   in `## Provenance of this record`; extended the entry's `Spec:` lead and the
   `**Claims the spec no longer makes**` line. **Reason:** change 1 is a *move*, and a moved clause
   with no destination is a deletion. New def `[spec-002-references]` filed alphabetically under
   `<!-- docs/SPECS/ -->`.
3. **Same file, three precision fixes.** Low 1: both fabricated quotations replaced with the spec's
   verbatim `"It records that behavior at a high level only"`; entry 4 given the `Spec:` lead line
   the other three carry. Low 2: `114-line` -> `113-line`. **Reason:** a quotation mark is a claim
   about bytes; a stated count is a measurement.
4. **Same file, `## How to read this file`.** The `**Who reads it.**` bullet's restatement of
   `BUILD.md` `### Who reads it, and when` replaced by a pointer at that heading. **Reason:** the
   DRY escalation, split as recorded above.
5. **This artifact, four count corrections** (header, `### DRY analysis`, `### Byte counts`,
   `### Concurrent-session churn observed`). **Reason:** Low 2. Recorded rather than silent — a
   measured-false number left in the record is re-quoted by the next pass.

No deferral reason is owed under this heading: no checklist box remains `- [ ]`.

### Notes for Worker 1 (spec reconciliation) — consolidated hand-off, R2 unless stated

This list **supersedes** the two scattered `### Notes for Worker 1` sections above; later passes
update these keys rather than appending a third set.

1. **`KANBAN.md:310` is stale in three particulars, and R1 caused two of them. Owner: R2's Worker 1
   pass for the decision, R3 for the `CardItem.text` edit + regenerate.** Card
   `TODO-ALPHA-052-0.1.0`'s deferral reads *"`spec-002…` carries four status-shaped sections:
   `## Current state`, `## Shipped slices`, `## Visibility status`, `## Open questions`. All four
   are accurate at HEAD today."* R1 removed `## Open questions`, so the count is three and one
   named section is gone; the *"all four are accurate"* clause is load-bearing for the deferral's
   own argument, so this is a rewrite of the sentence, not a number change.
   **R3 needs no further authorization** (Low 4): the build plan pre-authorizes a DB write when
   *"R3's audit finds real drift"*, and R1 created real drift. R2's plan states this plainly so R3
   does not stall. `KANBAN.md` is DB-generated and outside every residual item's write set, so the
   edit is `CardItem.text` plus a regenerate, applied **on top of** the concurrent session's DB
   state without reverting it.
2. **Drift rows D3 and D13 have no spec-side target left.** Both were rows against `## Open
   questions`, which R1 removed with plan authorization. The rationale already states the routing
   — the answer belongs in the spec as contract if it shipped, or in the rationale's change record
   as a claim the spec no longer makes — and **R2 can write the rationale file**; R3 cannot. State
   the routing once in R2's plan rather than rediscovering it per row.
3. **Anchor budget: all three anchors carry exactly ONE spec-body link.** `only-projection` in
   `## Purpose` sentence 1, `djangotype` in `## Problem statement` bullet 1,
   `djangooptimizerextension` in `## Current state`. There are **no spare links**, so the watchlist
   is every glossary-linked sentence, not a subset. Any rewrite touching one of those three
   sentences re-sites that anchor's link into surviving **contract** prose in the same edit — never
   into narration, never by editing the terms CSV — and `check_spec_glossary.py` re-runs after
   every edit group, not once at the end. Two of the three sit in sections R2 is most likely to
   open.
4. **The retitle decision R2 inherits is over three sections** (`## Current state`,
   `## Shipped slices`, `## Visibility status`), with `## Implementation checklist` arguably a
   fourth the card never counted. Re-verified against the slugged heading list: the two prose
   constraint sites are unaffected — `spec-003…:333` names "current state, visibility status, and
   checklist", `spec-006…:136`/`:147` name "Visibility status"; all three targets exist. Both
   sibling specs are read-only this cycle.
5. **`## References` is no longer byte-identical to HEAD** (change 1). Every other section R1
   declined to open still is. D15's obligation is untouched: the four upstream pointers remain
   unverified against the checkouts `AGENTS.md` line 2 names, and that verification is R2's.
6. **The rule-2-versus-reader-rule precedent, stated once for R2 to reuse:** move and tense-mark
   when the claim is deliberation a later spec answered; delete when it is a false assertion about
   the package. R1 applied it to `## Open questions` (moved) and to the `## References` chronology
   (moved). R2 will face it per drift row.
7. **Two drift observations R1 noticed and did not act on, both R2's.** `## Shipped slices` has no
   blank line between the O3 paragraph and the `### O4` heading, unlike every other slice boundary
   (cosmetic, pre-existing at HEAD). And `## Coordination with spec-001…` says spec-001's
   "Slices 4-6 are superseded by this optimizer spec **family**" while `## Current state` claims
   O1-O6 shipped under *this* spec — that tension is D6/D10/D11/D12's question, and the plan's
   scope trap warns against resolving it by absorbing spec-003 / 004 / 033 / 035 into this parent.
8. **A spec/rationale consistency checker is tracked at `KANBAN.md:309` and needs an owner, not a
   fifth raising.** This pass hand-rolled the fourth implementation. Two traps worth folding into
   it, both hit live: a multi-word grep token spanning a 100-column wrap or a `> ` blockquote
   prefix matches nothing, so normalize whitespace and strip quote markers first; and a GitHub
   slugger must **keep the underscore** — stripping it turned
   `#coordination-with-spec-001-django_types-0_0_1md` into a false DANGLING report in this very
   pass. (`check_spec_glossary.py::github_anchor` has a separate known defect on a heading that is
   itself a reference link.) Carried to the final gate's `### Deferred work catalog` alongside the
   rationale-preamble template item.

### Summary

R1 shipped the missing rationale companion for spec-002 and cut the spec's deliberative layer into
it. `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` (**14,296 bytes**, four entries keyed to
spec headings and anchors) now carries the chronology of why the optimizer became its own document,
why the O4 record went to `spec-003`, why the optimizer does not subsume generated relation
resolvers, the two questions the spec left open, and the alternatives each decision rejected. The
spec went **7,398 -> 7,006 bytes (-392, -5.3%)** across 113 -> 110 lines — a small number, and the
honest one on a short spec whose deliberation is thin and interleaved. What the move actually buys
here is the other half of the rule: **the spec no longer narrates its own history at all**, and a
chronology regex over the whole file now returns zero hits.

Nothing normative left. Sixteen surviving-contract tokens were measured present exactly once each,
including the three the `## Coordination` division-of-labour surface rests on. The three glossary
anchors ended **1/1/1, identical to HEAD** — anchor-neutral by plan constraint rather than by luck
— so card 2's `import_spec_terms` chain is intact at 49 done cards. The longest prose run shared
between the two files is 12 words and is a labelled quotation.

Final verification fixed all four Low findings rather than deferring three of them: two fabricated
quotations and a missing `Spec:` lead in the rationale, five off-by-one line counts across two
files (one of them in the durable rationale, which Worker 3's finding had not named), the last
surviving `originally` chronology clause in `## References` — moved, not deleted, to the entry that
already owns the bundling argument — and the `KANBAN.md:310` hand-off, tightened to say that R3's
DB-write trigger is already met. The escalated DRY finding was **split**: the one shared run that
copies a `BUILD.md` mechanism was replaced by a pointer (14.9% -> 13.0%, largest block 133 -> 87
words, still zero shared words in the deliberation), and the template-shaped remainder was routed
to the final gate's deferred-work catalog rather than trimmed unilaterally against a sibling file
outside this item's write set.

R2 was not started: no claim was reconciled against HEAD and no drift row D1-D15 was touched. Eight
R2-shaped items are consolidated above with named owners.

**Final status: `final-accepted`.**
