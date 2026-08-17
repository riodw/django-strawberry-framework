# Build: Round 3 — documentation completion and archive audit (F9-F13)

Spec reference: `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md`
Rationale companion: `docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md`
Build plan: `docs/builder/build-016-fieldmeta_consolidation-0_0_6.md` (`### R3 findings — documentation completion and archive audit`)
Status: final-accepted

**Procedural-closure shape** per `docs/builder/BUILD.md` `### Procedural-closure slices`: Worker 1 dispatched alone, no Worker 2 build and no Worker 3 review, one combined Plan + Final-verification block. The closure is authorized by the build plan's `## Artifact list` (which names this round Worker-1-only) and by its `Ownership partition: none; sequential rounds`: R3's whole deliverable is spec-side Markdown under Worker 1's exclusive custody (`docs/builder/worker-1.md` `## Spec custody`), and the one thing R3 might have dispatched to a builder — the F11 DB write — is ruled **not owed** below, so no source or DB diff exists for a builder to write or a reviewer to read.

## Plan and final verification (Worker 1)

### Spec status-line re-verification

Performed at spawn per `docs/builder/worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`. `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` lines 1-7 — title; `Target release: 0.0.6 (per KANBAN.md card DONE-016-0.0.6)`; `Status: shipped.`; `Owner: package maintainer.`; the one-line rationale-companion pointer — **still describe the build's current state.** R1 rewrote them this cycle and neither R2 nor R3 falsifies one; the pointer sentence's enumeration of what lives in the companion stays true after this round widens the companion. No edit owed, none made. No reference to a predecessor doc this build deleted survives.

### Certification and baseline

| Fact | Value |
|---|---|
| `git rev-parse HEAD` | `fa248bdf064b3dca52c1e591b6c6444b041bb65f` |
| `HEAD:django_strawberry_framework/optimizer/walker.py` | `1030b037b2db85290eeb45bde92c55b865cf6f42` |
| `HEAD:docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` | `56326e7937883c9acb1f4229bd43f83d57eec2db` |
| `git status --short \| wc -l` | 33 |

**Certified per file blob**, never by commit hash and never by tree object — the corrected method rule R2's final verification established after the commit hash rotted three times and the tree object rotted with it, while `walker.py`'s blob held at `1030b037` across all of it. `git stash`, `git checkout`, `git restore`, `git worktree` used **nowhere** in this pass. Every `HEAD` reading went through `git show HEAD:<path>` into a scratch path outside the repository, `git rev-parse`, `git grep … HEAD`, or `git diff HEAD`.

**The index is still swept by a concurrent session's `add -A`-shaped stage.** `docs/SPECS/spec-016-…md` is `MM`, the companion `AM`, this cycle's artifacts `A `/`AM`. **No `git add`, no `git reset`, no unstage** — every diff in this pass was taken as `git diff HEAD -- <path>`, because the bare form reports a staged file's index half as clean and on a second pass hides the earlier pass's changes entirely. The hazard is unchanged and maintainer-facing: a `git commit` on this index would place this cycle's work inside a commit describing other sessions' work. Flagged, not acted on.

**Baseline-dirty out-of-scope paths untouched.** Every path in the build plan's `## Baseline-dirty out-of-scope files`, plus `django_strawberry_framework/connection.py` (dirtied mid-cycle), is unedited, unreverted, unstaged, and un-`checkout`ed. The count moving down over the cycle (50 -> 58 -> 33) is concurrent sessions committing, not anyone reverting.

### Boundary count, hot path, floor scope, failability

- **Boundary count: zero.** This round writes Markdown only — no guard, cap, rejection path, validation branch, gate, or error message. No split trigger fires (`docs/builder/worker-1.md` `### Boundary count is a split trigger`).
- **Failability proof owed: none**, and by the rule rather than by assertion: `docs/builder/BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a new boundary and exempts doc edits. There is no executable statement in this round's diff at all, so nothing a mutation could remove and no row that could observe its removal. **Fail-open shapes: none** — a Markdown diff carries no expression.
- **Hot-path declaration: none**, from the build plan as written. No executable statement changed.
- **Floor-verification scope: none**, from the build plan as written. Floor facts quoted from `docs/builder/BUILD.md` `## Floor verification` rather than restated from memory: Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**; **the shared `.venv` is not the floor.** Nothing was installed into it and no floor venv was built.
- **No `pytest`, no coverage-shaped flag** anywhere in this pass (`docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). Nothing executable changed, so no assertion in any of the three test trees can change pass/fail.

### DRY analysis

**Helper inventory checked — and correctly answered "not applicable", with the reason.** `docs/builder/worker-1.md` `### Package-wide helper inventory before helper planning` gates *helper planning*: this round proposes no helper, shared constant, validation branch, coercion utility, or test helper, and writes no `.py` file. `docs/shadow/helper-inventory.md` was **not** regenerated — it is a concurrent session's output (the build plan's pre-flight step 5 deviation) and this cycle overwrites no shadow file it did not create.

The equivalent duplication risk for this round's actual medium was swept instead:

- **Existing patterns reused.** The rationale entry added here takes its shape from the companion's own eight existing entries (opening `Bears on [<spec section>][ref]` line, then `*Claim the spec no longer makes.*` / `*Why …*` / `*What the spec says instead.*` / `*Rejected alternative.*` italic leads) and from `docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-rationale.md`'s entry-per-section convention. The spec bullet is the ruling's fixed text, itself the spec-side paraphrase of what landed in source, so no new wording was invented at either end.
- **New shared shape justified.** None. Nothing this round produces is reusable by another round; this is the cycle's last content round.
- **Duplication risk avoided.** Two, both live. (1) **The sentence pair.** The docstring paragraph and the spec bullet are two prose statements of one contract; stating them independently is how they diverged in the first place. Prevented by landing text that was written *as* the spec-side paraphrase of the source-side text, clause for clause, and by putting the explanation in exactly one place — the companion — rather than in both the spec and the companion. (2) **Restating the R2 deliberation inside the "did not fix" list.** The list entry now points at the new companion entry instead of re-arguing it, so the retired premise, the rejected safe-list, and the archived-citation disposition each exist once.

### F9 — the archive move, audited (not performed)

**Verdict: complete and correct.** Re-measured, not restated.

| Element | Measurement |
|---|---|
| Spec location | `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` exists |
| Companion locations | `docs/SPECS/appx/spec-016-…-rationale.md` and `…-terms.csv` both exist |
| DB agreement | `SpecDoc(name='spec-016-fieldmeta_consolidation-0_0_6', path='docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md')` — one row, path matches disk |
| `KANBAN.md` | `:131` (Done table) and `:4306` (card body) both link `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md`; both resolve |

**Link hygiene, every file this cycle wrote or touched.** Measured with a disk-exists loop over every `^[ref]: path` def, plus a group-header order check, plus an in-page anchor check.

| File | Defs | Disk-exists | 10 group headers, in order | Anchors |
|---|---|---|---|---|
| `docs/SPECS/spec-016-…md` | 5 | 5/5 | yes | none used; 10 headings available |
| `docs/SPECS/appx/…-rationale.md` | 16 | 16/16 | yes | 8 cross-file `#anchor` defs into the spec, all 8 resolve; 1 new in-page anchor, resolves |
| `docs/builder/build-016-…md`, `bld-016-r1-…md`, `bld-016-r2-…md`, this file | 0 | n/a | n/a (no cross-file reference-style links; paths are code spans) | n/a |

`uv run python scripts/check_trailing_commas.py --check` exits **0** on all six files, which is the scaffold gate the pre-commit `source-layout` hook runs.

**Depth-rot trap checked explicitly, not assumed.** The companion sits two levels down, so `../../../AGENTS.md` must reach the repo root and `../GLOSSARY.md` (in the spec, one level down) must reach `docs/`. The masking hazard is a same-named file one level up shortening the true path: verified **absent** — no `docs/AGENTS.md`, `docs/SPECS/AGENTS.md`, `docs/SPECS/appx/AGENTS.md`, `docs/SPECS/GLOSSARY.md`, `docs/SPECS/appx/GLOSSARY.md`, `docs/BACKLOG.md`, `docs/KANBAN.md`, `docs/SPECS/BACKLOG.md`, or `docs/SPECS/KANBAN.md` exists. Every def therefore resolves at its intended depth rather than by accident.

**The one-in-page anchor added this round was DANGLING on first write and is fixed.** The companion's `### What this cycle deliberately did not fix` entry now points at the new entry by in-page anchor. My first spelling carried a leading hyphen from the heading's leading backtick, and the anchor check caught it before the round closed. Recorded because it is the same failure mode as the citation breaks below: **an anchor or a citation is verified by running the check, never by deriving the slug in your head.**

#### The orphan `[backlog]` def — resolved, and the resolution is "keep", overturning neither option the dispatch offered

The known issue: the reconciled spec defines `[backlog]: ../../BACKLOG.md` under `<!-- Root -->` and the body no longer references it — the def has **zero** `][backlog]` uses and the body does not mention `BACKLOG` at all.

**Neither "restore a use" nor "drop the def" is right, and the measurement is what decides it.**

- **Restoring a use is refused on contract grounds.** The only candidate use is provenance — the card graduated from `BACKLOG.md` item 35 — and provenance is history. This cycle's obligation 2 is that the spec states the current contract and **never narrates the change**; the item-35 origin already lives in the companion, which is where the cycle's own rules put it. Restoring the link would import history into the contract to satisfy a link convention, which is the tail wagging the dog.
- **Dropping the def is refused on population grounds, and this is the part that had to be measured rather than reasoned.** The orphan is not a spec-016 wart. Swept across `docs/SPECS/spec-0*.md` for files defining `[backlog]` with zero body uses: **eight** archived specs carry exactly this residue — `spec-011`, `spec-012`, `spec-013`, `spec-016`, `spec-024`, `spec-026`, `spec-036`, `spec-054`. (Seven more specs define it *and use it*, so the def is a live convention, not dead weight in general.) Dropping it in spec-016 alone would make one of eight files divergent while fixing none of the class, and would spend a spec-custody edit to create an inconsistency.
- **Cost of keeping is zero, measured.** `scripts/check_trailing_commas.py` does not detect unreferenced defs — its `orphan` concept is a def sitting outside a category group, not a def without a reader — so the scaffold hook is green either way, and the path resolves on disk.

**Ruling: keep, and name the condition.** R1's disposition was right and its reasoning is now measured rather than asserted. The condition that would change the answer: a **repo-wide sweep** that drops the orphan def in all eight archived specs in one change, or a checker that starts flagging unreferenced defs. Catalogued as a deferred item so the next sweep inherits the population rather than re-deriving it.

### F10 — DONE-card invariants, re-verified by reading the DB read-only

**Verdict: they hold.** No DB write performed, none owed. `examples/fakeshop/db.sqlite3` is **clean** (`git status --short` does not list it), which is the evidence no concurrent card-wrap is mid-flight; it stayed clean across this pass, and this pass opened it read-only through the ORM.

| Invariant | Measurement |
|---|---|
| Card 16 exists and is done | `Card(number=16, title='`FieldMeta` single-source-of-truth consolidation and mirror retirement')`, `status.key == "done"`, `milestone.key == "alpha"` |
| `SpecDoc` present and agreeing | one row, name and path as F9 above |
| `CardGlossaryTerm` links | exactly two: `djangotype`, `relation-handling` |
| Terms CSV match | the CSV's two data rows are `DjangoType,djangotype` and `relation shape,relation-handling` — one row per anchor, matching the two links exactly |
| `CardItem` completeness | 26 rows over five sections |

**One correction to F10 as the plan wrote it, and it is a widening, not a defect.** The plan asserts "Every `Scope` / `Why it matters` / `Note` / `Files likely touched` `CardItem` is `is_complete=True`". True as written — but the card carries **five** sections, not four, and the fifth (`verified_upstream`, one row citing `strawberry_django/optimizer.py::_get_model_hints`) is `is_complete=False`. So a literal reading of "every `CardItem` is complete" would be false, and this pass would have restated a wrong count if it had trusted the enumeration.

**It is nonetheless not a defect, proved against the board's own population rather than argued.** Across all 49 `done` cards, `verified_upstream` rows are **82 incomplete to 14 complete** — an incomplete upstream-verification row is the dominant convention on shipped cards, not an unfinished item. Card 16 matches the convention. **No DB edit owed on F10.**

### F11 — the card's `CardItem` bodies: the restatement is NOT owed

**F11 confirmed as a factual matter.** The 26 bodies are a verbatim copy of the spec's pre-reconciliation text, carrying every defect R1 fixed in the spec: the colon-form refs (`django_strawberry_framework/types/base.py:_record_pending_relation`, `types/converters.py:resolved_relation_annotation`, `types/resolvers.py:_make_relation_resolver`, `optimizer/walker.py:_resolve_field_map`, `optimizer/walker.py:_walk_selections` (hints read), `optimizer/extension.py:_collect_schema_reachable_types`, `optimizer/extension.py:check_schema`), the deleted `_record_pending_relation` name, the false sentence "Existing tests pass without modification.", the `~7 sites` tilde, and the classifier framing.

**Ruling: not owed. The plan's default answer is upheld, and on the merits rather than on cost alone.**

The load-bearing argument is not "DB churn is expensive" — that is the second reason, and a second reason cannot carry a ruling. It is that **a card body and a spec are different artifacts answering different questions.** The card body is the board's record of what the card *said when it was written*; the spec is the contract that must be checkable against `HEAD`. R1 fixed the spec precisely because a contract that names symbols which do not exist cannot be audited — that argument applies to a contract and does not transfer to a historical record. Re-writing 26 rows to match a spec they chronologically preceded would replace a faithful record with a retro-fitted one, and would do it in the one place where the drift is *legible as history* because the card is stamped `DONE` at `0.0.6`.

The supporting reasons, each measured:

- **Nothing depends on the bodies as source references.** They render into `KANBAN.md`/`KANBAN.html` as card prose, and nothing greps them: the cycle's own sweeps for `_record_pending_relation` and `optimizer/resolvers` found the DB only as a binary hit, never as a reference a tool resolves. No reader's question is left unanswered by the corrected spec, which the card body links to at `KANBAN.md:4306`.
- **The cost is real and shared.** `examples/fakeshop/db.sqlite3` is a tracked binary two concurrent sessions write (`docs/builder/BUILD.md` `### Tracked binary / generated files`, `AGENTS.md` rule 34); 26 row updates plus a regenerate of `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` is a large churn footprint for zero reader benefit, and the build plan puts all four out of every round's writable set.
- **The rule-27 argument does not reach the DB.** Rule 27 governs "docs and code comments"; a DB row is neither, and the rendered `KANBAN.md` is generated output whose source is the row.

**Consequently no Worker 2 pass is dispatched and this round writes no DB row.** For completeness, had the ruling gone the other way the change would have been: 13 `scope`-section `CardItem.text` values plus 2 `why_it_matters` and 3 `note` values on `Card(number=16)` — 18 rows carrying stale references — followed by `scripts/build_kanban_md.py` and `scripts/build_glossary_md.py`. **The condition that would flip the ruling** is named in the companion: if a card body ever became the only statement of a contract, or if the board began rendering card bodies as current source references.

### F12 — the `CHANGELOG.md` cluster, catalogued for the maintainer and NOT edited

`AGENTS.md` rule 21 forbids `CHANGELOG.md` edits unless told, so this round records and does not touch it. **File verified clean** (`git status --short -- CHANGELOG.md` prints nothing; absent from `git diff HEAD --name-only`).

The cluster is on **one line**, 974 characters, cited by substring rather than by number per rule 27: `CHANGELOG.md` #"Consolidated field metadata onto". Every element re-measured at one occurrence each, and the population is **wider than both F12 and R2's note recorded**:

| # | Element | Current truth |
|---|---|---|
| 1 | `012-fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement-0.0.6` as the link **text** | Pre-renumber id; the card is `016`. Written by `2bd7cb84` as `DONE-ALPHA-012-0.0.6` before the board renumber. |
| 2 | `_record_pending_relation` | Symbol deleted at `f83bb71b`; the canonical read is `types/base.py::_build_annotations`. |
| 3 | `resolved_relation_annotation` named as a `types/` reader | True but the canonical read moved upstream to `types/finalizer.py::finalize_django_types`. |
| 4 | `walker._walk_selections` | The hints read is `optimizer/walker.py::_resolve_optimizer_hints`. |
| 5 | `extension.check_schema` | Bare; the symbol is `optimizer/extension.py::DjangoOptimizerExtension.check_schema`. |
| 6 | **New:** `walker._resolve_field_map`, `walker._walk_selections`, `extension._collect_schema_reachable_types`, `extension.check_schema` are all **dotted `module.symbol`** forms where rule 27 requires `path/file.py::QualifiedName`. Four occurrences, not one. | Wider than "a bare `extension.check_schema`" — the whole four-site list is non-conforming in form as well as three of them being stale in content. |
| — | **Acquitted:** the link **target** | `[card-fieldmeta-…]: KANBAN.md#fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement` **resolves** — `KANBAN.md` carries the explicit `<a id="fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement">` anchor. Only the link text is stale; the link is not broken. Recorded so a maintainer does not go looking for rot that is not there. |

### F13 — durable docs: nothing owed, re-verified rather than assumed

**Verdict: no durable-doc edit is owed.** Each element measured at this pass:

- **`docs/README.md`** owes nothing: the card is an internal metadata-architecture refactor with no consumer-visible surface. Confirmed structurally rather than by reading intent — `git show --name-only de35a622 | grep -c "__init__.py"` is **0** across both shipping commits, so no public export was added, removed, or renamed, and `git diff HEAD -- django_strawberry_framework/__init__.py` produces no output for this cycle either.
- **`docs/GLOSSARY.md`** carries both linked anchors: `#djangotype` and `#relation-handling` resolve, `check_spec_glossary.py` exits **0** (`OK: 2 terms`), and the file is **clean** — this cycle wrote it not at all, correctly, since it is DB-generated.
- **`docs/TREE.md`** renders `optimizer/field_meta.py`, and — the check the plan asked for explicitly rather than by assumption — **would still render byte-identically after this cycle's edits.** `uv run python scripts/build_tree_md.py --check` reports `docs/TREE.md is up to date`, exit **0**. The reason it holds is structural and worth stating: the renderer reads **module** docstrings, and R2 changed a **function** docstring (`_resolve_field_map`), leaving `walker.py`'s module docstring untouched. So no regenerate is owed, and the renderer was not run in write mode.
- `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3` all **clean**; none is in any round's writable set.

### Spec changes made (Worker 1 only)

Spec: `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` (blob at `HEAD` `56326e79`). Companion: `docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md`. Terms CSV: **not edited** — the reconciled body links no anchor the two-row CSV lacks, and `check_spec_glossary.py` exits 0, which is the gate.

| # | File | Cited text | Change | Reason | Finding |
|---|---|---|---|---|---|
| 1 | spec | `### Bounded exceptions to the single-source rule`, first bullet #"The two shapes coexist safely only because every downstream read is" and #"the same divergence is present in" | Bullet replaced whole with the pass-1 ruling's `#### Exact replacement text — the spec bullet`, verbatim. | **Both clauses were false on the same 10-occurrence measurement** and the source half landed in R2, so the spec and the code disagreed until this round. The bullet states the current contract directly and never narrates the correction. The **later** of the two candidate replacements in the R2 artifact was landed; pass 1's earlier recommendation corrects only the closing sentence and leaves the premise standing. | R2's escalated Low, upheld at R2 final verification |
| 2 | companion | `### `## Scope` — "single source of truth" stated without its two bounded exceptions`, #"the docstring says the `getattr(..., default)`" | Clause rewritten: the cost is now "the map is `FieldMeta \| Any`, so a reader must know which attributes are safe to reach for", and the exit condition is cited as `optimizer/walker.py::_resolve_field_map` #"registry-coverage gate lands". | The old clause **restated the false premise as the docstring's claim**, so R2's fix left the companion asserting something the source no longer says. Also replaced a bare prose quotation with a rule-27 citation that greps. | R2 |
| 3 | companion | (new entry) `### `### Bounded exceptions` — the dual contract was stated on a false premise, in both files` | Added after the bounded-exceptions entry, keyed to the same spec section by reference link. | Obligation 3 of this cycle: the explanation goes in the rationale. Records **the retired premise** (both spellings, with the 10-occurrence and three-exit measurements), **what both files say instead**, **two rejected alternatives**, and **the deliberate non-edit of the archived citation**. | R2 |
| 4 | companion | `### What this cycle deliberately did not fix`, the `optimizer/resolvers.py` bullet | Struck through and marked **FIXED** by R2, with a pointer to the new entry instead of a re-argument. | The entry was true when written and false now. Kept rather than deleted because it records what the round was dispatched to do; `docs/builder/worker-1.md` rule 2's delete-don't-move applies to a *falsified claim*, and this is a resolved item, not a false one. | R2 |
| 5 | companion | same section, the `CardItem` bullet | "Whether restating them is owed is the archive-audit round's call" replaced with the ruling, its reasoning, and the condition that would reverse it. | F11 is decided; an open question left open in a standing doc reads as unresolved forever. | F11 |
| 6 | companion | `extension.py:1264-1265`; `connection.py:818`, `filters/sets.py:2031`, `optimizer/join_taxonomy.py:301`, `optimizer/walker.py:185,1026`, `utils/relations.py:305,438`, `optimizer/field_meta.py:155,160,231`; `tests/test_registry.py:504`; `CHANGELOG.md:221` | All **nine at-`HEAD`** raw `path:NN` refs replaced with `path::QualifiedName` or `path #"unique substring"`. | **`AGENTS.md` rule 27**: raw `path:NN` is licensed only in per-cycle scratchpads, and a `-rationale.md` companion is tracked and committed alongside the spec — a standing doc (`docs/builder/worker-1.md` rule 5). This is F2's defect class in the file R1 created to fix it. Measured: the companion had 22 raw refs and 18 of the 22 sibling companions have **zero**, so this is a fixable defect and not a house convention. | rule 27 |
| — | companion | the **13 remaining** raw refs (`types/base.py:73`, `:144`, `:137`, `optimizer/walker.py:86`, `optimizer/extension.py:356`, `:619`, `extension.py:351`, `walker.py:81` x2, `base.py:140`, `converters.py:229`, `resolvers.py:181`, `walker.py:88`) | **Deliberately kept.** | Every one is inside a passage explicitly scoped to a named historical commit (`de35a622` / `de35a622^`). A line number inside an immutable commit **cannot rot**, which is the drift rule 27 exists to prevent, and `path::QualifiedName` cannot cite a shape the commit deleted — it would be less accurate, not more. The companion already argues this at #"already drifted by seven lines when the proposal was written". | rule 27 |

**No spec section heading changed**, so the eight cross-file anchors the companion links into the spec and the heading-name references from this cycle's artifacts all still resolve — verified below rather than assumed.

### Verification runs

| Check | Command | Result |
|---|---|---|
| Glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` | `OK: 2 terms - all have glossary entries and at least one spec link.` exit **0** |
| Markdown scaffold | `uv run python scripts/check_trailing_commas.py --check` on the spec, the companion, and this cycle's four artifacts | exit **0** |
| TREE render | `uv run python scripts/build_tree_md.py --check` | `docs/TREE.md is up to date.` exit **0** |
| Link defs, spec | disk-exists loop over every `^[ref]: path` | **5/5** resolve |
| Link defs, companion | same loop | **16/16** resolve |
| Group headers | all ten canonical headers present and in order, both files | yes, both |
| Cross-file anchors | the companion's 8 `#anchor` defs against the spec's 10 rendered heading slugs | **8/8** resolve |
| In-page anchor | the one new `](#…)` in the companion against its own heading slugs | resolves (dangling on first write, fixed before close) |
| Depth rot | masking-file check at `docs/`, `docs/SPECS/`, `docs/SPECS/appx/` for `AGENTS.md`, `GLOSSARY.md`, `BACKLOG.md`, `KANBAN.md` | none exists; every def resolves at its intended depth |
| `#"substring"` citations | **line-wise** `grep -cF` for every citation in the spec and the companion, in its named file | **11/11 at exactly 1 occurrence** |
| Working tree | `git status --short` | 33 paths; this cycle's are the spec, the companion, and four artifacts; every baseline-dirty path untouched |

**The citation sweep was run as precondition and postcondition, line-wise, and it caught one of my own writes.** The new companion citation for the `_DjangoFieldLike` guarantee was first written as #"guarantees ``name`` and ``is_relation``" — which greps to **zero**, because the Protocol's docstring wraps after `guarantees`. Corrected to #"``name`` and ``is_relation``; the remaining attributes" (one hit). That is the **third** phrase this cycle that was cleared by eye and broken by a line wrap; the discipline is now written into the memory file as a standing rule.

No formatter was run: this round writes Markdown only, and the scaffold check above is the applicable gate (`AGENTS.md` rule 16's `ruff` pair has no Markdown target).

### Notes for Worker 1 (spec reconciliation)

Catalog inputs for the final gate's `### Deferred work catalog` (Worker 1 is its only author). **None is a defect in shipped behavior.** Items 1-12 carry forward from R1 and R2 with the amendments recorded there; 13-16 are this round's.

1. **`tests/test_registry.py::test_finalize_discards_consumer_authored_pending_relation_without_rewriting_annotation` #"``FieldMeta.from_django_field`` and ``_record_pending_relation``"** names a symbol deleted at `f83bb71b`. Tests are outside every round's writable set this cycle. File verified clean.
2. **The `CHANGELOG.md` cluster** — see F12 above for the re-measured six-element population, including the newly-recorded four dotted `module.symbol` forms and the *acquittal* of the link target. `AGENTS.md` rule 21 bars the edit; maintainer decision. File verified clean.
3. **`django_strawberry_framework/registry.py` #"``types.converters.resolved_relation_annotation`` for relation"** — dotted form where rule 27 requires `types/converters.py::resolved_relation_annotation`. Clean, outside every round's writable set.
4. **`django_strawberry_framework/types/converters.py` #"``Meta.required_overrides`` by ``types/base._build_annotations``"** — mixed slash-and-dot form where rule 27 requires `types/base.py::_build_annotations`. Same class, same reason.
5. **`django_strawberry_framework/optimizer/walker.py` #"``utils.relations.instance_accessor``"** — dotted, in the file R2 owned, deliberately left because `instance_accessor` is not a spec-016 symbol and fixing it is scope creep into another card.
6. **The bare-basename cross-folder shorthand is house style, ACQUITTED, ~12 sites** — each resolves because the basename is unique package-wide. R2's own new citation `field_meta.py::_DjangoFieldLike` **uses** the convention, so it is applied here, not breached. Recorded so a later sweep does not "fix" one instance and fracture it.
7. **`docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md` #"ONLY reason the two coexist safely"** is **decided stale by design** (Worker 0), not a deferral by omission. Re-point target, if a maintainer reverses the call: `optimizer/walker.py::_resolve_field_map` #"lets the two shapes coexist" — the **greppable single-line form**, corrected from the longer phrase this cycle's own wrapping broke. Verified untouched and clean.
8. **The Step 3c reference-resolution loop resolves only package-root-relative and `optimizer/`-sibling paths.** Adding a `types/`-sibling candidate root makes all seven rows resolve, which this round measured. Any reuse must either widen the roots or name the expected row, or it reads a correct file as defective forever. The R2 artifact's F8-sweep box now states both provable forms.
9. **`scripts/review_inspect.py`'s output is structurally blind to a docstring change** — it replaces every string-literal token including docstrings with `...`. A clean shadow overview is not evidence about such a diff.
10. **The dual contract's exit condition:** when the registry-coverage gate lands, the walker's fallback disappears, the dual contract ends, and the cross-reference plus the whole `DUAL CONTRACT` paragraph plus the spec's first bounded exception should be **deleted**, not re-pointed. The companion's recorded rejected alternative (make the fallback build `FieldMeta`, delete the resolver fallbacks) stays rejected. No refactor proposed by any round.
11. **A concurrent session has staged this cycle's entire output together with two other sessions' WIP.** Maintainer-facing; no worker may unstage it.
12. **`django_strawberry_framework/optimizer/field_meta.py` #"field shapes on the resolver path (``_field_meta_for_resolver``)"** carries the **bare symbol** with no path, cross-module. Pre-existing at `HEAD`, file clean, outside every round's writable set. The bare-symbol edge of item 6's acquitted convention — found at R2's final verification after three prior censuses missed it.
13. **The orphan `[backlog]` link def is a repo-wide residue class of EIGHT archived specs**, not a spec-016 wart: `spec-011`, `spec-012`, `spec-013`, `spec-016`, `spec-024`, `spec-026`, `spec-036`, `spec-054` each define it with zero body uses (seven other specs define **and use** it, so the def itself is live convention). **Ruled keep** in spec-016 — see F9. A sweep that drops it must drop all eight in one change; dropping one creates the divergence it was meant to remove. Population recorded so the sweep does not re-derive it.
14. **The companion retains 13 raw `path:NN` refs, deliberately**, every one inside a passage scoped to a named historical commit (`de35a622` / `de35a622^`). Recorded as a *decided* exception to rule 27's letter, on the ground that a line number inside an immutable commit cannot drift and a symbol-qualified form cannot cite a deleted shape. A future sweep that mechanically converts them would make the record less accurate. **Four sibling companions carry the same shape** (`spec-010` x2, `spec-012` x8, `spec-014` x37, `spec-016` x13); the other eighteen carry none.
15. **`verified_upstream` `CardItem` rows are `is_complete=False` on 82 of 96 rows across the 49 done cards.** Card 16's single incomplete row matches the board convention. Recorded because F10's four-section enumeration invited the wrong conclusion, and because any future "every card item complete" invariant must exclude this section or it will fail on almost every done card.
16. **F11 is decided, not deferred: the `CardItem` restatement is NOT owed**, with the reasoning and the flip condition recorded in the companion's `### What this cycle deliberately did not fix`. Had it been owed, the change was 18 `CardItem.text` rows on `Card(number=16)` plus three doc regenerates. Recorded so the catalog carries the decision rather than an open question.

### DRY re-check across all three rounds

None owed and none found. R1 wrote the spec and the companion; R2's hunk contains no executable token; R3 writes Markdown only. No round added a helper, constant, repeated literal, or parallel data flow, so there is no shared code shape to consolidate.

The one cross-round shape is the **sentence pair** — `optimizer/walker.py::_resolve_field_map`'s `DUAL CONTRACT` paragraph and the spec's first bounded-exception bullet, two prose statements of one contract. It is now consolidated in the only way prose can be: both texts were authored as paraphrases of each other, clause for clause, from one measurement, and their shared explanation lives once, in the companion. That is what stops the pair diverging again, which is exactly how it diverged the first time.

### Summary

R3 closed the cycle's documentation half. The spec's `### Bounded exceptions to the single-source rule` first bullet now states the contract the source states — `name` and `is_relation` guaranteed on both shapes and read directly, any other attribute read directly only where both shapes carry it, a `FieldMeta`-only attribute never read off the map without a `getattr(..., default)`, and the twin site sharing the policy but not the dual return shape — so the spec and `walker.py` read as one contract for the first time in the cycle. The companion gained the deliberation: the retired false premise in both its spellings, the two rejected alternatives (a closed safe-list, rejected because `related_model` is 6 of the 10 direct reads and is `getattr`-hedged in the same module; and coarse-but-directionally-right prose, rejected because the corrected sentence leans on the premise), and the deliberate non-edit of the archived `DONE/build-004-…` citation with a **greppable** re-point target. F9-F13 were re-measured rather than restated, which corrected three of them: F10's completeness invariant is stated over four of five sections and the fifth's incomplete row is board convention (82/96); F12's population is six elements wide, not four, while its link target is sound; and the orphan `[backlog]` def is an eight-spec class ruled keep rather than a local wart. F11 is decided **not owed** on the merits — a card body is the board's record, not the contract — so no Worker 2 pass and no DB write. Nine at-`HEAD` raw `path:NN` refs in the companion were symbol-qualified under rule 27 and the thirteen commit-scoped historical ones were kept with the reason recorded. `check_spec_glossary.py`, the scaffold check, and `build_tree_md.py --check` all exit 0; every link def disk-exists, every anchor resolves, and all eleven `#"substring"` citations grep to exactly one line.

### Final status

`final-accepted`.
