# Build: R4 — documentation obligations, four-direction cross-reference audit, archive audit, staged-anchor sweep

Spec reference: `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` (archived; audited, not edited — R1/R1b closed it `final-accepted`)
Contract: `docs/builder/build-009-rich_schema_architecture-0_0_4.md` `## R4 inherits` and `### Maintainer decision 8`
Status: final-accepted

Combined plan + perform pass (this cycle's `### Deviation 3`): Worker 1 is the only role that may edit a spec or its rationale companion, so there is no Worker 2 phase. Worker 0 reads `planned` on this artifact as "dispatch Worker 3".

---

## Plan (Worker 1)

### Spec status-line re-verification

`worker-1.md` `## Spec status-line re-verification` runs every spawn. R4 does not own `spec-009`, so this is a read-only confirmation rather than a custody act.

- `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` — header re-read; R1b left it `final-accepted` and nothing in R2, R3, or R4 falsifies a header line. **No edit owed, and none made.**
- `docs/SPECS/spec-054-fieldset-0_1_1.md` — R4's authorized clause sits in `## Risks and open questions`, not the header. Header untouched.

### The two findings, re-verified at source before planning

`### Maintainer decision 8` names two clauses. This cycle closed seventeen-plus findings of one class — a sentence asserting a mechanism, cause, or population the code does not have — and several corrections written to fix that class were themselves false. So each falsification was re-derived here rather than accepted from the dispatch.

**Site 1 — `docs/SPECS/appx/spec-009-…-rationale.md:511-512`.** Claim under test: `spec-028` `### Decision 12` "still defers `DISTINCT ON` to `0.0.9`".

- `grep -n "^### Decision 12" docs/SPECS/spec-028-orders-0_0_8.md` → `979:### Decision 12 — No Layer 6 auto-generation and no DISTINCT ON surface`.
- Body read in full at `:979-1010`. It states **"the ordering surface carries neither"**, and its `Alternatives considered (and rejected)` block lists the `ASC_DISTINCT` / `DESC_DISTINCT` + `apply_distinct` port and the `Meta.distinct` / `distinct_on:` surface as **Rejected**.
- **Falsification CONFIRMED.** Not merely stale by date: the cited Decision now says the opposite. R2 authored that change, so this cycle created the contradiction.

**Site 2 — `docs/SPECS/spec-054-fieldset-0_1_1.md:800-803`.** Claim under test: card `TODO-BETA-054-0.1.1`'s Foundation-slice seam *cites* "BACKLOG.md item 38 for the `DjangoModelField` custom Strawberry field class" (present tense).

- Card 054's rendered region located mechanically: `KANBAN.md:475-551` (bounded by the next `^### [` heading at `:552`).
- `item 38` / `DjangoModelField` / `BACKLOG` over that region → **`item 38` absent**; `DjangoModelField` survives once, inside R3's replacement text as a *recorded rejection* ("a custom `DjangoModelField` field class is unnecessary machinery for the same reason").
- The card now records the answer directly (region line 47: "That question is settled without one: spec-054 pins **resolver wrapping** as the mechanism (Decision 11 …)").
- Board-wide `item 38` survives at `KANBAN.md:79` — a **different** card's correct citation, and `BACKLOG.md:1914` is the definition it points at.
- **Falsification CONFIRMED**, and `spec-054` is the only document in the repo still asserting the citation. R3 authored that change, so again this cycle created the contradiction.

**The predicate is written against the intended end state, not against the token.** `DjangoModelField` deliberately survives on card 054 as a recorded rejection, so the check is "zero `item 38` on card 054" — a check written the other way fails on a correct result.

### DRY analysis

**Helper inventory checked.** Refreshed for the **whole package**, not `utils/` alone, per `worker-1.md` `### Package-wide helper inventory before helper planning`. R4 writes no Python, so the inventory was used only to answer whether any *audit* instrument this pass needs already exists in `scripts/`: `scripts/check_spec_glossary.py` (term → anchor → glossary-heading chain) and `scripts/check_trailing_commas.py` (link-definition scaffold + the 10 canonical group headers) both exist and are the supported instruments. Shapes searched: `anchor`, `glossary`, `link`, `slug`, `spec`, `terms`, `validate`. **No new helper is justified and none was written** — a one-off audit script belongs in the pass, not in `scripts/`, and the condition that would change the answer is the repo-wide deferral sweep below being adopted as a standing gate.

- **Existing patterns reused.** `scripts/check_spec_glossary.py` for the terms chain; `scripts/check_trailing_commas.py --check` for the markdown scaffold; `git show HEAD:<path>` into an out-of-repo scratch path for every read-only HEAD reference (`git stash` / `checkout` / `restore` / `worktree` are banned repo-wide in this cycle).
- **New helpers justified.** None.
- **Duplication risk avoided.** The recommended shape for site 2 is a **near-copy** of card 054's own rejection text. `### Maintainer decision 8` states plainly: **do not de-duplicate** — the board renders for readers who do not hold the spec, so the near-copy is load-bearing rather than a DRY defect. The plan therefore preserves it deliberately and records the reason here so a later pass does not "fix" it.

### The four-direction audit — design

`## R4 inherits` transfers the corpus lesson, not just the item: this cycle swept **spec→spec**, **spec→source**, and **spec→board**, and was bitten twice by the corpora it did not sweep — **spec→permanent-companion** (site 1) and **board→spec** (site 2). Both authorized fixes were born that way. So all four directions are enumerated and swept explicitly, **including the reverse of every edit this cycle made**, because every fix creates a potential inbound falsification at the other end.

| # | Direction | Corpus | Instrument |
|---|---|---|---|
| 1 | spec ↔ spec | 620 tracked permanent files, per-cycle scratch (`bld-`, `build-`, `docs/review/`, `docs/dry/`) excluded | filename sweep + repo-wide `<basename>#<fragment>` anchor resolver, with a HEAD control |
| 2 | spec ↔ source | `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/` | retired-token occurrence sweep; symbol existence checks on every clause this pass writes |
| 3 | spec ↔ board | `KANBAN.md`, `KANBAN.html`, `BACKLOG.md`, the kanban DB | card-id resolver: every card id cited in this cycle's four permanent documents, resolved against the board's id set |
| 4 | spec ↔ permanent companion | rationale files, `*-terms.csv`, `docs/GLOSSARY.md`, `docs/TREE.md`, `CHANGELOG.md`, `README.md`, `TODAY.md`, `GOAL.md` | terms chain; retired-token sweep; the same anchor resolver |

Seven grep-shape traps are catalogued on this cycle — wrapped phrases, `\b` against `_`, filtered output printed under an unfiltered command, multi-line parenthesized imports, function-body-indented imports, the alternate `Spec Decision 12` spelling, and a wrapped citation defeating a whole-line match. Three method rules follow and are binding on this pass:

1. **Produce every population mechanically and paste the command output** — never type an enumeration.
2. **Prefer moving the corpus over widening one pattern.** Widening tokens inside one corpus cannot reach another; that is how R2 found citation four and how site 1 was found at all.
3. **`grep -o | wc -l` where the unit is occurrences**, `grep -c` only where the unit is lines, and **report a denominator**.

### Implementation steps

1. Re-verify both falsifications at their source (above). Done before any edit.
2. Record byte/line baselines for both writable files, and the rationale's append-only baseline (`-`-line count in the full diff; `head -166` `cmp` against `git show HEAD:` in an out-of-repo scratch path).
3. Fix site 1 in place. It is text **this cycle added**, so an in-place correction preserves append-only against HEAD — re-prove it mechanically rather than asserting it.
4. Fix site 2: past-tense rewrite keeping the live rejection rationale, plus a back-pointer to card 054. Use the existing `[kanban]` reference-style definition (`START.md` "Markdown link convention"; `AGENTS.md` rule 28).
5. Run the four-direction audit; report a denominator per direction.
6. Run the archive audit — **re-derive, do not accept** Worker 0's pre-flight reading. The DB has been written since (R3) and a concurrent `spec-014` cycle also wrote it.
7. Run the staged-anchor sweep with a control proving the pattern matches something.
8. Assemble the deferred-work inventory from all five closed artifacts.
9. Gates; `Status: planned`.

**Ceiling, stated before the audit runs so it cannot be rationalized afterwards.** `### Maintainer decision 8`'s scope limit is **exactly two clauses**. A third instance of the falsified-by-this-cycle class is **RECORDED FOR THE MAINTAINER, NOT FIXED** — three unilateral widenings on one standing instruction is the ceiling, and a fourth needs the maintainer's own word. The widening is **clause-scoped, not file-scoped**: `spec-054` becoming partly writable does not make its other defects writable.

### Test additions / updates

None. R4 writes no source and no test. `AGENTS.md` rule 15 and the plan's `## Build-wide context flags` both hold; no `pytest` was run, and no `--cov*` flag was used anywhere in this pass.

### Implementation discretion items

- The exact wording of both replacement clauses, within the constraints that each asserts only what is verifiable at the symbol or heading it cites, and that site 2 keeps the rejection rationale intact. **Assessed and decided**: the fix quotes the target's own vocabulary rather than inventing new phrasing — site 1 adopts `spec-028` Decision 12's own "no `DISTINCT ON` surface ships", so the correction asserts nothing new.
- Line re-wrapping inside the edited bullet, to match the file's existing ~72-column style.

### Dispatched findings checklist

Self-derived from `## R4 inherits` and `### Maintainer decision 8`. Boxes ticked by the perform half of this pass; Worker 3 walks the list; a later Worker 1 pass audits every tick.

- [x] **R4-1** — Fix `docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md`'s claim that `spec-028` `### Decision 12` "still defers `DISTINCT ON`", falsified by R2 (`### Maintainer decision 8` site 1). Falsification verified at `docs/SPECS/spec-028-orders-0_0_8.md` `### Decision 12`; replacement verified at the same heading.
- [x] **R4-2** — Fix `docs/SPECS/spec-054-fieldset-0_1_1.md` #"BACKLOG.md item 38"'s present-tense claim that card 054 cites the item, falsified by R3 (`### Maintainer decision 8` site 2). Past-tense rewrite, live rejection rationale kept, back-pointer to card 054 added, **not** de-duplicated.
- [x] **R4-3** — Perform (not merely record) the four-direction cross-reference audit, enumerating all four directions explicitly and including the reverse direction of every edit this cycle made. Denominator reported per direction.
- [x] **R4-4** — Audit the `spec-009` archive in all three cross-reference directions, in the kanban DB, and in the terms-CSV chain. Re-derived, not accepted from pre-flight.
- [x] **R4-5** — Run the staged-anchor sweep `grep -rEn 'TODO\(spec-009|TODO-(ALPHA|BETA|STABLE)-009' .`, excluding `KANBAN.md` / `KANBAN.html` / `BACKLOG.md`. Re-derived with a control.
- [x] **R4-6** — Decide and record disposition for `tests/test_connection.py`'s module docstring citing `docs/spec-030-connection_field-0_0_9.md` (the file lives at `docs/SPECS/`).
- [x] **R4-7** — Record `docs/GLOSSARY.md`'s now-imprecise "so no dynamic order factory is shipped" (DB-generated, not writable here).
- [x] **R4-8** — Assemble the deferred-work inventory from all five closed artifacts' `### Notes for Worker 1` and escalation sections, one bullet per item with its source artifact named, for the final gate's `### Deferred work catalog`.

---

## Final verification (Worker 1)

### Gates

| Gate | Result |
|---|---|
| `check_spec_glossary.py --spec docs/SPECS/spec-009-…-0_0_4.md` | **exit 0** — `OK: 23 terms - all have glossary entries and at least one spec link.` |
| `check_spec_glossary.py --spec docs/SPECS/spec-054-fieldset-0_1_1.md` | **exit 2**, unchanged from baseline — `error: missing file: docs/SPECS/spec-054-fieldset-0_1_1-terms.csv`. **Pre-existing, not caused by this edit**: `git ls-tree -r HEAD --name-only \| grep 054` returns only `spec-054-search_fields-0_1_2-terms.csv` and `spec-054-fieldset-0_1_1.md`, so no such CSV exists at HEAD or in the tree. Recorded below; creating one is outside R4's writable set. |
| `check_trailing_commas.py --check` on both edited files | **exit 0**, re-run after the final reflow |
| In-page anchors resolve | **0 unresolved** across all four permanent documents (below) |
| No orphaned link definitions introduced | **none introduced; one retired** (below) |
| `AGENTS.md` rule 27 (symbol-qualified refs) | every reference this pass wrote is a heading or a symbol path; **no raw `path:NN` added to either permanent document** |
| `AGENTS.md` rule 28 / `START.md` link convention | site 2's back-pointer uses the existing reference-style `[kanban]` def; scaffold and all 10 canonical group headers intact (the trailing-commas gate enforces this) |

**The anchor checker is itself a claim, and the first one written here was wrong.** A slug function collapsing `\s+` to a single dash reported **9** false unresolved anchors in `spec-054`; GitHub maps each space to its own dash, so `### Decision 2 — The three-declaration contract` slugs to `decision-2--the-three-declaration-contract` with **two** dashes. Run against `git show HEAD:` as a control, the broken checker returned the identical 9 at HEAD — proving the defect was the instrument, not the file. Corrected instrument, with the same HEAD control:

```
spec-054 HEAD      anchor uses=  14  unresolved=0  []
spec-054 TREE      anchor uses=  14  unresolved=0  []
rationale TREE     anchor uses=   0  unresolved=0  []
spec-009 TREE      anchor uses=   0  unresolved=0  []
spec-028 TREE      anchor uses= 159  unresolved=0  []
```

`spec-028`'s 159 uses / 0 unresolved reproduces R2's recorded figure exactly.

**Link definitions.** `spec-054` carried **five** orphaned definitions at HEAD (`backlog`, `goal`, `kanban`, `spec-030`, `spec-050`). Site 2's back-pointer consumes `[kanban]`, so the tree now carries **four** — one retired as a side effect of the authorized edit, none introduced. The remaining four are pre-existing and out of scope; recorded below. The rationale carries **11 defs, 0 orphans**.

### Byte and line counts

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/appx/spec-009-…-0_0_4-rationale.md` | 60,351 bytes / 828 lines | **60,361 bytes / 829 lines** | +10 bytes / +1 line |
| `docs/SPECS/spec-054-fieldset-0_1_1.md` | 54,632 bytes / 959 lines | **54,785 bytes / 962 lines** | +153 bytes / +3 lines |

Measured with `wc -c -l` before the first edit and after the last. R4's own footprint, `git diff --numstat`: `spec-054` → `10 7`. The rationale's `621 0` is the **whole cycle's** footprint on that file, not R4's — stated as the cycle figure rather than as R4's, per the standing rule that a footprint claim names its scope.

### Append-only re-proved mechanically

`worker-1.md` `### Performing the rationale move` rule 4 makes the rationale append-only during the cycle. Site 1 is an in-place correction of text **this cycle added**, which preserves that — and the proof is mechanical, not asserted:

- `git diff -- <rationale> | grep -c '^-'` → **1**, both before and after the edit. The single `-` line is the `--- a/docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md` diff header; **no HEAD line is deleted**.
- `git diff --numstat` → `621 0`. **Zero deletions** against HEAD, up from 620 additions before this pass — exactly the +1 line the edit added.
- HEAD is 208 lines, the tree 829. `cmp <(head -166 HEAD-copy) <(head -166 tree)` → **exit 0, clean**. (`head -208` differs only because insertions from line ~167 shift HEAD's tail down — consistent with pure insertion, and independently confirmed by the zero-deletion numstat.)
- The HEAD copy was obtained with `git show HEAD:<path>` into an out-of-repo scratch path. No `git stash`, `checkout`, `restore`, or `worktree` was used anywhere in this pass.

### Direction 1 — spec ↔ spec

**Inbound anchor links into this cycle's four edited permanent documents: 0 occurrences, 0 unresolved.** Instrument: repo-wide regex `(<basename>)#([A-Za-z0-9_\-]+)` over every readable file outside `.git/` and `.venv/`, catching both inline links and reference-style *definitions* (where the fragment lives under this convention).

**Control, because a zero from a sweep is worthless without one.** The same instrument run against every `.md` target repo-wide returns **2,809 occurrences across 30 targets** (`GLOSSARY.md` 2,558; `spec-046-transport_security-0_0_14.md` 26; `KANBAN.md` 23; …). The instrument works; the zero is a measurement.

This matters because seven headings were renamed or removed by this cycle — six in `spec-009` (`### Borrow \`OptimizerStore\`, but keep the current optimizer's strengths`, `### Borrow \`get_strawberry_annotations\``, `### Decision 3: custom Strawberry field class`, `### Layer 4: Strawberry-native field class`, `### Phase 3: DjangoModelField`, `### Should generic fallback exist?`) and one in `spec-028` (`### Decision 12 — Layer 6 and DISTINCT ON deferred to \`0.0.9\``). **None of the seven had an inbound anchor from any document**, so no rename dangled a cross-reference. The `### Constraint binding R1 and R2` renumbering ban held: every surviving Decision number and heading text is stable, and `spec-010` #"### Decision 6: fail loudly" still resolves.

**Inbound-by-name**, permanent documents only (per-cycle scratch excluded and listed separately): `spec-009` ← `spec-010` (5), `KANBAN.md` (3), `spec-008` (2), `spec-010`-rationale (2), `spec-008`-rationale (2). `spec-028` ← `KANBAN.md` (5), `spec-029` (4), `spec-030` / `spec-034` / `spec-036` / `spec-038` / `spec-039` (2 each), `CHANGELOG.md` (2), `spec-001` / `spec-010` (1 each), three `appx/` rationales, and `examples/fakeshop/test_query/test_glossary_api.py` (3). `spec-054-fieldset` ← `spec-009` (3), `KANBAN.md` (3), `spec-009`-rationale (2), `spec-053` (1), `KANBAN.html` (1). Every permanent hit was opened. **One live falsification found — `KANBAN.md:336`, graded below.**

### Direction 2 — spec ↔ source

Retired-claim token sweep over the **permanent corpus: 620 tracked files** (757 tracked, minus 137 under `docs/builder/bld-`, `docs/builder/build-`, `docs/review/`, `docs/dry/`). **Caveat — this path-prefix rule is NOT the rule `### Direction 3` applied**, and the `DjangoModelType` row below is the one figure in this table that differs between the two readings (27 / 9 here, 26 / 8 under the basename rule): see `### Recorded for the maintainer — NOT repaired here` item 8. Counted as **occurrences**, in Python — the first attempt, a shell loop over a 603-file argument list, returned **0 for every token on a corpus that provably contains them** (`grep -o DjangoModelField KANBAN.md | wc -l` → 1). A false denominator that reads exactly like a clean result; discarded and re-run mechanically.

| Retired token | Occurrences / files | Grade |
|---|---|---|
| `DjangoModelField` | 17 / 6 | **`spec-009` itself: 0** — the D1 scrub is complete. Survivors are the rationale's deliberation record (8), card 054's *recorded rejection* (`KANBAN.md`/`KANBAN.html`/DB, 3), `spec-054` (3), and `spec-010` (3, concurrent cycle — standing item) |
| `OptimizerStore` | 11 / 4 | `spec-009`: 0. Board + rationale only — deliberation and a board record |
| `with_hints` | 1 / 1 | `spec-009`: 0. The one occurrence is the rationale's own record of the scrubbed D2 claim |
| `with_prefix` | 3 / 2 | `spec-009`: 0. `tests/optimizer/test_selections.py`'s 2 are an unrelated local symbol — the test names `test_node_children_with_runtime_prefix_clones_with_prefix` (`:203`) and `test_connection_node_children_unwraps_edges_node_with_prefixes` (`:211`), not `OptimizerStore.with_prefix` |
| `get_strawberry_annotations` | 3 / 3 | `spec-009`: 0. `spec-010:491` is a known standing item |
| `DjangoModelType` | 27 / 9 | `spec-009` retains 6 — correct: D5's scrub replaced the "keep it as a fallback" claim with the error-only contract, which names the class to reject it |
| `ASC_DISTINCT` / `DESC_DISTINCT` | 14 + 14 / 2 | `spec-009`: 0. All in `spec-028` (12 each, the rejection record) and the rationale (2 each) |
| `AdvancedFilterSet` / `AdvancedOrderSet` / `AdvancedAggregateSet` | 18 + 30 + 13 | Survivors in `orders/sets.py`, `filters/sets.py`, and the example apps are **upstream-cookbook citations**, not this package's own names — correctly out of scope |
| `DISTINCT ON` | 28 / 5 | `orders/sets.py` (2) and `orders/inputs.py` (1) are R2's **corrected** clauses, now reading "no DISTINCT ON surface ships". **`permissions.py:511` opened and graded: an error-message f-string about SQL `DISTINCT ON` row semantics, not a citation of Decision 12** — R2's `orders/`-only scope holds |
| `item 38` | 9 / 6 | Card 054's region: **0**. `BACKLOG.md:1914` is the definition; `KANBAN.md:79` / `KANBAN.html` / DB are a *different* card's correct citation; `docs/GLOSSARY.md:2116` opened and graded — `` `BETTER` item 38 ``, an unrelated backlog reference |

**Reverse of R2's source edits.** `orders/inputs.py:197` and `orders/sets.py:278-279` now cite `spec-028 Decision 12` for "no DISTINCT ON surface ships"; the heading they name was re-verified to exist at `spec-028:979` and to say exactly that. The citation and its target agree.

**Reverse of R4's own edits.** Site 1 cites `spec-028` `### Decision 12` — verified present and consistent. Site 2 cites `KANBAN.md` and `TODO-BETA-054-0.1.1` — both verified (card id on the board; `[kanban]` def target exists on disk).

### Direction 3 — spec ↔ board

Every card id cited in this cycle's four permanent documents, resolved against `KANBAN.md`'s **70 distinct card ids**:

| Document | Occurrences / distinct | Unresolved |
|---|---|---|
| `spec-009` | 18 / 5 | **0** |
| `spec-009`-rationale | 5 / 5 | **0** |
| `spec-028` | 46 / 10 | 2 — `WIP-ALPHA-028-0.0.8` (6×), `WIP-ALPHA-022-0.0.8` (1×) |
| `spec-054-fieldset` | 17 / 9 | 1 — `TODO-BETA-046-0.1.1` (1×) |

All three unresolved ids were **opened and graded**, and two of the three grade out:

- `spec-028`'s `WIP-ALPHA-*` pair — historical in-flight state labels for cards the board now carries as `DONE-028-0.0.8` and `DONE-022-0.0.7`. Same class as the `WIP-ALPHA-033-0.0.9` / `WIP-ALPHA-032-0.0.9` prefixes R2 found in shipped source, and it folds into the same recommended sweep. **Pre-existing; not falsified by this cycle; recorded.**
- **`spec-054:128` is CORRECT as written and is a false positive of the resolver.** It reads "retarget every pre-renumber `TODO-BETA-046-0.1.1` fieldset comment in `apps/products/schema.py` (7 occurrences) to the shipped `054` id" — it names the id *as* pre-renumber and owns the sweep as a Slice 4 obligation. Its stated population of 7 was re-measured and is **exactly 7**. The same inversion R3 met on card 054: a scrubbed name may deliberately survive as a recorded rejection or a named target, which inverts the verification predicate.

**But grading that site opened a real one.** The full `TODO-BETA-046-0.1.1` population, measured over the permanent corpus, is **15 occurrences / 5 files** — correct on the merits, and measured under a **basename** exclusion rather than the path-prefix rule `### Direction 2` states; under that stated rule it reads 17 / 6, the difference being one archived per-cycle build plan (`### Recorded for the maintainer — NOT repaired here` item 8) — and the 2026-07-30 renumber made `046` the transport card (`DONE-046-0.0.14`), with `TODO-BETA-054-0.1.1` the live FieldSet owner:

```
 1  django_strawberry_framework/types/definition.py
 4  docs/SPECS/spec-034-permissions-0_0_10.md
 1  docs/SPECS/spec-054-fieldset-0_1_1.md
 7  examples/fakeshop/apps/products/schema.py
 2  tests/test_build_tree_md.py
```

Graded: **7 carded** (`apps/products/schema.py`, owned by `spec-054` Slice 4's declared sweep), **2 not rot** (`tests/test_build_tree_md.py` constructs a synthetic `PlannedPath` fixture and asserts the rendered description echoes the id it was *given*; it never reads the board, so it is renumber-agnostic), **1 correct as written** (`spec-054:128`), leaving **4 edit-owed rot sites across 2 files plus 1 decided non-edit** — `types/definition.py` (the known standing item, 1) and **`spec-034-permissions-0_0_10.md`, 4 occurrences which no sweep covers and which no prior pass recorded: 3 live-claim rot sites (`:220`, `:224`, `:307`) and 1 revision-log bullet (`:14`) that is a decided non-edit.** So the 15-occurrence partition is **7 + 3 + 1 + 4**, the `3` counting `tests/test_build_tree_md.py`'s 2 alongside `spec-034:14`. `### Recorded for the maintainer — NOT repaired here` item 2 carries the grading; the `spec-034` *occurrence* count is still 4 and the population is still 15 / 5. Recorded below as a new find.

### Direction 4 — spec ↔ permanent companion

This is the corpus that produced site 1, so it was swept first-class rather than as a residue.

- **Terms chain** — audited end to end below (`### Archive audit`).
- **Rationale ↔ spec** — the rationale's 11 link definitions all resolve on disk; 0 orphans; 0 in-page anchor uses. Its `spec-028` citation is now consistent with `spec-028`.
- **`docs/GLOSSARY.md`** — `item 38` and the `OrderSet` entry both opened; the latter is a live imprecision, recorded below.
- **`docs/TREE.md`, `CHANGELOG.md`, `README.md`, `TODAY.md`, `GOAL.md`** — swept by the retired-token instrument in Direction 2. `docs/TREE.md` carries five `spec-046` references, all to the *transport* spec (correct post-renumber), and **no** `TODO-BETA-046-0.1.1`.

### Archive audit — re-derived, not accepted

Worker 0 verified this at pre-flight. The DB has been written since (R3) and a concurrent `spec-014` cycle also wrote it, so every figure was re-derived from the live DB through the ORM.

| Check | Re-derived result |
|---|---|
| `Card.objects.get(number=9).status.key` | `done` |
| Card title | `Rich schema architecture` |
| `SpecDoc.path` | `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` |
| That path exists on disk | **yes** |
| `card.glossary_links.count()` | **23** |
| `…-terms.csv` rows | **23** (24 lines incl. header) |
| Distinct anchors in the CSV | **23** |
| CSV anchors resolving to a `docs/GLOSSARY.md` heading | **23 / 23, 0 unresolved** |
| `check_spec_glossary.py` | **exit 0**, `OK: 23 terms` |

**The chain closes exactly**: 23 CSV rows → 23 distinct anchors → 23 GLOSSARY headings → 23 DB `glossary_links`. The three rows whose CSV `term` differs from the glossary entry name are the expected term-vs-entry cases and were checked individually — `input type` → `Input type generation`, `Relay node` → `Relay Node integration`, `schema audit` → `Schema audit`. No term is orphaned, no glossary entry is unlinked, and no anchor dangles.

**A false-positive was caught here too.** A first anchor check scanned `docs/GLOSSARY.md` for literal `id="…"` attributes and reported **23 / 23 missing** — the wrong instrument, since the glossary uses markdown headings whose anchors are slugs. Re-run against slugged headings: 154 headings, 0 unresolved.

**Archive completeness in all three cross-reference directions:** the spec is at its archived path with both companions under `docs/SPECS/appx/`; the DB points at that path; and no document anywhere cites a pre-archive `docs/spec-009-…` path — with the sole exception recorded below, which is `spec-030`'s, not `spec-009`'s.

### Staged-anchor sweep

`grep -rEn 'TODO\(spec-009|TODO-(ALPHA|BETA|STABLE)-009' .`, `.git/` excluded — **3 raw hits, 0 in shipped source, tests, or comments**:

```
docs/builder/bld-009-r3-card054_db_references.md:1379   (prose describing this sweep as R4's)
docs/builder/bld-009-r1c-async_syncmisuse_test_row.md:1687 (prose recording the sweep as not R1c's)
docs/builder/build-009-rich_schema_architecture-0_0_4.md:39 (the plan's statement of R4's contract)
```

All three are **self-referential**: per-cycle build documents naming the sweep, not staged anchors. As occurrences: `TODO(spec-009` → **3**; `TODO-(ALPHA|BETA|STABLE)-009` → **0**.

**Control, because a zero sweep needs one.** The same pattern generalized to `TODO\(spec-[0-9]+` finds anchors repo-wide, including in shipped source — `django_strawberry_framework/optimizer/walker.py` carries 2 × `TODO(spec-035`. The pattern matches real anchors; spec-009 simply has none.

**The prescribed exclusion never engages.** `grep -cE` over `KANBAN.md`, `KANBAN.html`, and `BACKLOG.md` → **0, 0, 0**, so the carve-out for board cards contributes nothing either way. Stated because an exclusion that is never exercised should not be reported as though it removed hits. Worker 0's pre-flight result is reproduced: **no anchor left to discharge.**

### Item 5 — the two known documentation defects: disposition

**5a. `tests/test_connection.py:3` cites `docs/spec-030-connection_field-0_0_9.md`; the file exists only at `docs/SPECS/spec-030-connection_field-0_0_9.md`.** Verified both ways (`ls` on the cited path → `No such file or directory`; on the archived path → present).

**Disposition: RECORDED, NOT FIXED.** Three independent grounds, each sufficient:

1. `### Maintainer decision 8`'s scope limit is **exactly two clauses**, both enumerated and neither this. Fixing it is a **third** unilateral widening on one standing instruction, which that decision names as the ceiling.
2. It is **pre-existing at HEAD**, so it fails the Decision 7 / 8 test entirely — that test is "this cycle's own edit falsified a line", and this cycle did not.
3. It is in a **module docstring in a file a concurrent package-source session is actively editing** (`tests/test_connection.py` is ` M`), and the plan's `## Build-wide context flags` keep source and tests read-only.

**5b. `docs/GLOSSARY.md:1434`'s `OrderSet` entry closes "so no dynamic order factory is shipped".** Verified imprecise: `django_strawberry_framework/orders/factories.py` defines `get_orderset_class` (`:143`) and `_dynamic_orderset_cache` (`:58`), so a dynamic order factory **is** shipped — it simply has **no production consumer** (every reference outside that module is in `tests/`). The entry's *substance* is right (the connection field resolves ordering from the already-resolved `Meta.orderset_class` sidecar and never auto-generates); only the closing clause overstates it to "not shipped" from "not consumed".

**Disposition: RECORDED, NOT FIXED.** `docs/GLOSSARY.md` is DB-generated (`scripts/build_glossary_md.py`), is not in R4's writable set, and R3 closed the DB — a regenerate would publish whatever the DB currently holds, including a concurrent session's unrendered work. The fix is a DB edit plus a regenerate, owned by whichever cycle next has the glossary DB open.

### Recorded for the maintainer — NOT repaired here

Everything below was found by this pass, verified, and deliberately left. None is inside `### Maintainer decision 8`'s two-clause authorization.

1. **`KANBAN.md:336` asserts a claim the *first* residual cycle falsified.** It reads that `spec-009` #"### Layer 3: Finalization trigger" *"still presents hybrid auto-finalization as the preferred direction"*. Verified false: that section now opens **"The trigger is the explicit consumer call, and nothing else."** and records the auto-trigger direction as **rejected** — landed at `f3c94642`, the prior cycle, not this one. **A genuine board→spec falsification, and exactly the corpus direction `## R4 inherits` names.** Not fixed on three grounds: it is not this cycle's falsification (fails the Decision 7/8 test), `KANBAN.md` is DB-backed with R3 closed and a standing "never regenerate" instruction, and it would be a third widening. The bullet's *disposition* half is still accurate — it prescribes exactly the residual cycle that has now run.
2. **`docs/SPECS/spec-034-permissions-0_0_10.md` carries 4 `TODO-BETA-046-0.1.1` citations** (`:14`, `:220`, `:224`, `:307`) — **3 of them naming card 046 as the live FieldSet owner in the present tense, and 1 recording it in the past tense as history.** Post-renumber card 046 is `DONE-046-0.0.14` (transport); the live owner is `TODO-BETA-054-0.1.1`. **New — no prior pass recorded these**, and no declared sweep covers them (`spec-054` Slice 4 owns only `apps/products/schema.py`'s 7). Pre-existing, sibling spec, out of scope. **The count stays 4; the disposition splits 3 + 1, and whichever sweep eventually takes these must honour the split:**
   - **3 live-claim sites — `:220`, `:224`, `:307`.** Present-tense assertions that are false today: `:220` "`_bind_fieldsets` lands with `TODO-BETA-046-0.1.1`"; `:224` "the live kanban card is `046`"; `:307` "`TODO-BETA-046-0.1.1` codifies `FieldSet` as the field-level tier". `:224` is the sharpest of the three — its whole purpose is correcting a card number ("the card body's open question still quotes the older `044`; but the live kanban card is `046`"), so it has rotted in exactly the way it was written to prevent.
   - **1 revision-log bullet — `:14` — a DECIDED NON-EDIT, not a fourth rot site.** It is the `**Revision 2**` accuracy-pass log (2026-06-14), whose `**(L1)**` clause records that "the FieldSet card number **was pinned to** the live `TODO-BETA-046-0.1.1`". `bld-009-r2` settled this exact shape one item down this same list, at `spec-028:41`: *"a revision-log bullet records what a review round did, and rewording it would desync it from the text it quotes."* It is also **not false as history** — `046` *was* the live id on 2026-06-14, six weeks before the 2026-07-30 renumber; only its subject moved since. A sweep that rewrites it destroys a historical record and manufactures a claim the 2026-06-14 pass never made.
3. **`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`'s `fields_class` docstring reserves the slot for `TODO-BETA-046-0.1.1`** — the same renumber residue, in shipped source. Already a standing item from R1/R1b; re-measured here and confirmed still present. Uncovered by any declared sweep.
4. **`spec-028` carries 7 `WIP-ALPHA-*` card-state citations** (`WIP-ALPHA-028-0.0.8` ×6, `WIP-ALPHA-022-0.0.8` ×1) for cards now `DONE-028-0.0.8` / `DONE-022-0.0.7`. Same class as the `WIP-ALPHA-033-0.0.9` / `WIP-ALPHA-032-0.0.9` prefixes R2 found in shipped source; folds into the same recommended sweep.
5. **`spec-054-fieldset-0_1_1.md` has no `-terms.csv` companion**, so `check_spec_glossary.py` exits **2** on it (`missing file`). Confirmed pre-existing at HEAD. It is an in-flight (unshipped) spec, so this may be intentional under `AGENTS.md` rule 26 — but the checker cannot distinguish "not yet authored" from "lost in an archive move", and `docs/SPECS/appx/` does carry a `spec-054-search_fields-0_1_2-terms.csv` from the pre-renumber numbering. Worth one maintainer look.
6. **`spec-054` carries 4 remaining orphaned link definitions** — `[backlog]`, `[goal]`, `[spec-030]`, `[spec-050]` (down from 5; site 2 consumed `[kanban]`). All pre-existing at HEAD, none flagged by the scaffold gate. Same shape as the pre-existing `[relay]` orphan R2 recorded in `spec-028`, which also survives.
7. **The repo-wide orphaned-deferral sweep R2 recommended is still unrun**, and this pass adds two more inputs to it (items 2-4 above). R2 sized it at **56 archived specs, ~34 carrying a deferral-plus-version line, ~190-200 candidate lines**. R4's audit is shaped to run it but is not authorized to: it would edit dozens of sibling specs. Recommended as one maintainer-scoped sweep rather than N one-clause widenings — which is precisely the pattern this cycle has now hit three times.

8. **This artifact's two token sweeps measured over DIFFERENT permanent corpora, and the corpus rule as written is imprecise.** `### Direction 2` states the rule as a **path prefix** — "757 tracked, minus 137 under `docs/builder/bld-`, `docs/builder/build-`, `docs/review/`, `docs/dry/`" = **620 files** — but `### Direction 3`'s population was measured under a **basename** reading (per-cycle build documents excluded wherever they live) = **606 files**. **The two corpora differ by 14 files — the count the item's own 620 / 606 already implies — and every one of them sits under `docs/builder/DONE/`**, whose paths begin `docs/builder/DONE/build-` and so escape the `docs/builder/build-` prefix. The divergence is a **directory**, not a file. Of those 14, exactly **two carry any swept token, and they are different files explaining different deltas**: `build-046-transport_security-0_0_15.md` (2 x `TODO-BETA-046-0.1.1`, at `:793` and `:841`) produces `17 / 6` -> `15 / 5`, and **`build-008-definition_order_independence-0_0_4.md` (1 x `DjangoModelType`, at `:362`) produces `27 / 9` -> `26 / 8`**. The other 12 carry none. Measured side by side across the **14 distinct tokens these two sweeps use** — `### Direction 2`'s table is 10 rows covering 13 tokens (eight rows carry one token each; `ASC_DISTINCT` / `DESC_DISTINCT` carries two and `AdvancedFilterSet` / `AdvancedOrderSet` / `AdvancedAggregateSet` carries three — 8 + 2 + 3 = 13), plus `### Direction 3`'s `TODO-BETA-046-0.1.1` — **12 of the 14 are identical either way**; the two that are not are `TODO-BETA-046-0.1.1` (**17 / 6** under the path rule vs **15 / 5** under the basename rule) and `DjangoModelType` (**27 / 9** vs **26 / 8**) — and this artifact records **15 / 5** in Direction 3 and **27 / 9** in Direction 2, i.e. one figure from each rule. **Both figures are correct under the rule each was actually computed with, and 15 / 5 is right on the merits**: the divergent file's 2 occurrences (`:793`, `:841` — "the `TODO-BETA-046-0.1.1` cluster stays as it is (V9)") are a **closed cycle's archived build plan** discussing this very renumber cluster, i.e. per-cycle scratch under `START.md` "Temp artifact conventions", correctly outside the rot partition. **Not tree drift, and proved so on the directory's real history rather than on an assumption about its age**: `docs/builder/DONE/` did **not** exist before `054de9dd` (`git cat-file -t 054de9dd^:docs/builder/DONE` -> the path is not in that tree). `054de9dd` — this cycle's own pre-flight HEAD, 2026-08-15 16:47 — **creates** the directory with **12** files, and `973d00b2` (22:59 the same evening, i.e. after pre-flight) brings it to **14**. The figures are nonetheless drift-free, and for a sharper reason than age: **both token-bearing files were among `054de9dd`'s original 12**, and the two later additions (`build-010-foundation-0_0_4.md`, `build-012-version_release_alignment-0_0_4.md`) carry **zero** swept tokens — verified per file, not inferred. So no figure in either direction was ever exposed to the post-pre-flight change, and both token-bearing files sat in the corpus under the path rule from the very first sweep. **The part a future pass most needs: BOTH prior instruments applied the rules inconsistently and neither noticed** — R4's own Direction 2 / Direction 3 sweeps, and Worker 3's two independent re-derivations, which reproduced each figure exactly because each matched whichever rule that direction had used. Two independent agreeing measurements did **not** catch it; only running one population under both readings did. **Recorded, not repaired** (`### Maintainer decision 8` — pre-existing and not authored by this cycle): repairing it means re-running Direction 2 under the basename rule and restating `DjangoModelType`, which is a sweep this item does not authorize. The durable fix is to state corpus exclusions by **basename**, since a path prefix silently fails on an archived copy.

### Deferred work catalog — input for `bld-009-final.md`

Assembled from all five closed artifacts' `### Notes for Worker 1` and escalation sections. One bullet per item, source artifact named. `worker-1.md` `## Final test-run gate` makes Worker 1 the catalog's only author; this is its input, not the catalog itself.

**Cross-spec rot into `spec-010` (concurrent cycle's file; read-only all cycle)**

- `spec-010:8` still lists "custom field classes" among what `spec-009` describes — exactly what D1 scrubbed. Carried unrepaired for ten consecutive passes. — `bld-009-r1` `### Escalations carried forward…`; `bld-009-r1b` same.
- `spec-010:491` still names `get_strawberry_annotations` as "the right helper for the day a stable consumer-override contract lands" — D3's scrubbed borrow; `spec-009` now states the opposite. — `bld-009-r1` (found at pass 3), `bld-009-r1b`.
- `spec-010:67` — the anchor into `spec-009` #"### Layer 3: Finalization trigger" resolves and the claim holds, but the cited section no longer states the direction; plus a near-verbatim twin of `spec-009`'s single-threaded-setup-window sentence. Right owner is `spec-010`. — `bld-009-r1`, `bld-009-r1b`.

**Source docstrings (source read-only this cycle)**

- `types/definition.py::DjangoTypeDefinition`'s `fields_class` docstring cites the pre-renumber `TODO-BETA-046-0.1.1`; live owner is `TODO-BETA-054-0.1.1`. — `bld-009-r1`, `bld-009-r1b`; **re-confirmed by R4**.
- `filters/sets.py`'s in-place `Meta` mutation (`meta_class.fields = meta_class.filter_fields`) mutates the consumer's `Meta`, and the `hasattr(meta_class, "fields")` guard sees inherited attributes. Pre-existing, shipped, tested. — `bld-009-r1` `### Notes for Worker 1`.
- `tests/test_connection.py:3`'s module docstring cites `docs/spec-030-connection_field-0_0_9.md`; the file lives at `docs/SPECS/`. In a file a concurrent session is editing. — `bld-009-r1c`; **disposition decided by R4 above: recorded, not fixed**.

**Deliberately-stale text**

- The rationale's `## Standing notes` "three sites" bullet (`:649`) is **deliberately stale** — correcting it would break the cycle's append-only constraint; the staleness is stated in-file five lines above it, and the spec's own opener was corrected to "four sites". Correct it in the first pass that has the rationale open without that constraint. — `bld-009-r1`, `bld-009-r1b`.

**Orphaned deferrals (the central hand-off)**

- `spec-028:195` / `:1191` defer **`DjangoListField` orderBy-argument integration** to `0.0.9`; `list_field.py` has zero occurrences of `order_by` / `orderset` / `filterset`; no card in `KANBAN.md` / `BACKLOG.md`. — `bld-009-r2` `### Recorded for the maintainer / R4`.
- `spec-028:734` (`### Decision 8` step 4) defers the position-side-channel leak-closing design "likely to a sibling `0.0.9` ordering-permissions card", **plus a second site at `:41`** (a revision-log bullet quoting it — a decided non-edit). Zero card hits. — `bld-009-r2`.
- `spec-027` #"Auto-generation of `FilterSet` from `Meta.fields`" reads "Deferred; … lands when `DjangoConnectionField` ships in `0.0.9`". `DjangoConnectionField` shipped; implicit generation did not. The verbatim twin of the sentence R2 fixed at `spec-028:200`. — `bld-009-r2`.
- **One repo-wide sweep is recommended in place of N separate fixes**: "does any archived spec's `0.0.X` deferral have a card?" — **56 archived specs, ~34 carrying a deferral-plus-version line, ~190-200 candidate lines**. Folds in the `WIP-ALPHA-*` stale card-state prefixes in `connection.py`, `types/finalizer.py`, `types/relay.py` **and (new, R4) `spec-028`'s 7**, plus the 8 raw `Decision N line NN` refs in package source that violate `AGENTS.md` rule 27, **plus (new, R4) `spec-034`'s 4 `TODO-BETA-046-0.1.1` citations — 3 live-claim sites (`:220`, `:224`, `:307`) to repoint at `TODO-BETA-054-0.1.1`, and 1 revision-log bullet (`:14`) that is a DECIDED NON-EDIT** (`### Recorded for the maintainer — NOT repaired here` item 2 carries the grading; rewriting `:14` would falsify a true historical record). — `bld-009-r2`, extended by R4.

**Recorded-not-repaired sites**

- `KANBAN.md:3680` (card `DONE-028-0.0.8`) still says Layer 6 "deferred to `0.0.9` … per Decision 12". DB-backed, out of scope. — `bld-009-r2`.
- `spec-028:1159` and `:1166` — `## Doc updates` blockquotes of that card body and of a `CHANGELOG.md` bullet the shipped changelog never carried. Left verbatim: editing a quote so it no longer matches its target is a worse defect. — `bld-009-r2`.
- Pre-existing orphaned link definition `[relay]` in `spec-028`'s bottom block, 0 uses at HEAD, not flagged by the scaffold gate. — `bld-009-r2`. **R4 adds 4 more in `spec-054`.**
- `docs/GLOSSARY.md`'s `OrderSet` entry: "so no dynamic order factory is shipped" — imprecise since `fd0c7327`. — `bld-009-r2`; **re-verified and dispositioned by R4 above**.
- **Both dynamic-set factories are production-unconsumed**, not just the order half: `get_orderset_class` / `_dynamic_orderset_cache` and the filter twin `get_filterset_class` have no package consumer; the only importers are `tests/`. Dead code or deliberately symmetric skeleton is a **contract-level** question — answer both halves together. — `bld-009-r2`.
- Residual retired-rationale sites in `orders/inputs.py` (`_build_input_fields` #"reserved -- see" and #"future-extension"): neither false today, but the same rationale's third and fourth instances in one module. — `bld-009-r2`.
- Card 054's `#### Definition of done` opens "Add `docs/spec-054-fieldset-0_1_1.md`" but the spec lives at `docs/SPECS/`. Pre-existing. — `bld-009-r3`.
- `spec-009:592-597`'s registry-state sentence is satisfied across two objects (registry-global `is_finalized` vs per-type `DjangoTypeDefinition.finalized`). Not false; a future tightening should say which object holds which half. — `bld-009-r1b`.
- Rationale `:533` ("the one place in this pass where a spec claim was kept") and `:359-360` (three appliers of the colored runner pair where four measured — `filters/sets.py` is the fourth) — both graded notes in `final-accepted` regions. — `bld-009-r1b`.
- `spec-009:654`'s "Phase 2 is the only window" is true only under its resolver scope; `:649`'s three-applier enumeration is correct as scoped; `:930`'s "across every cardinality" is an examined-and-not-raised absolute. All recorded so a later pass does not re-open them as new. — `bld-009-r1b`.
- **`spec-028` `### Decision 3`'s heading still reads "Five-layer port plus a *deferred* Layer 6"** while its own `### Decision 12` now records Layer 6 auto-generation as a **standing non-goal** rather than a deferral. Kept deliberately, and the cost of changing it is the reason: the heading's slug `#decision-3--five-layer-port-plus-a-deferred-layer-6` carries **6 in-file uses** (`spec-028:10`, `:16`, `:126` ×2, `:130`, `:1205`), all of which a retitle dangles, and the word carries no version and no phantom owner. Heading-vs-body agreement here is a maintainer *preference*, not a defect. — `bld-009-r2` `### Recorded for the maintainer / R4` item 8.
- **`spec-028:1171`'s `Ordering`-enum fallback offers what `### Decision 12` rejects.** The `## Risks and open questions` bullet still says "if consumers report wanting the cookbook's `DISTINCT` modifiers in the same enum, a follow-up card can add `ASC_DISTINCT` / `DESC_DISTINCT`", while Decision 12 rejects that port outright. **Graded a non-finding, not a defect**: that section's own preamble (`spec-028:1167`) declares every item carries "a fallback if implementation reveals the preferred answer is wrong", so a demand-contingent revisit of a rejection is the section's declared shape and asserts nothing false about shipped code. R2 records it as graded identically **four** times (`bld-009-r2:534`, `:1160`, `:1853`, plus the apply pass's re-grade) and asks that it not be opened a fifth. — `bld-009-r2`.
- **`orders/factories.py` says "standing *deferred* Non-goal" where `spec-028:988` says "standing non-goal".** Two sites: the module docstring #"remains a standing deferred" (the phrase wraps across a line, which is why a multi-word grep misses it) and `get_orderset_class` #"is a standing deferred Non-goal". Graded **agreeing** at every pass that opened them (`bld-009-r2:584-585`, `:1357-1358`, `:1782`, `:1928`) because "deferred" there names no version and no owner. Recorded so a later pass does not re-raise it — and specifically so the still-unrun repo-wide deferral sweep does not mistake the word for an orphaned deferral. — `bld-009-r2`.
- **Card 054 carries a promotion-owner conflict in its own text.** The `#### Definition of done` promotes `Meta.fields_class` out of `DEFERRED_META_KEYS` "(per `TODO-BETA-058-0.1.3`)" while the same card's Foundation-slice seam says this card "populates the slot and promotes the key end-to-end". `spec-054` `## Risks and open questions` #"Promotion-owner ambiguity (card-text conflict)" records it with a pinned preferred answer (Decision 8: promote on 054; 058 owns only the later dispatch generalization) and a one-line fallback. **A maintainer contract call, not a defect** — untouched because `### Maintainer decision 3`'s scope limit reaches only card 054's two `DjangoModelField` / item-38 references. It sits one bullet above the very text R4 rewrote in that section. — `bld-009-r3` `### Decision 3`.

**Commit-gate blockers (not this cycle's, but they will bite)**

- `scripts/check_trailing_commas.py` runs in pre-commit and **will fail on `tests/test_connection.py:1062`** (`async def __call__(self, prefix, root, info):` inside `_Resolver`) — a **concurrent session's** uncommitted line, absent at HEAD and outside R1c's range. Running the script's default auto-fix would rewrite another session's work. — `bld-009-r1c`.
- `docs/GLOSSARY.md` is dirty with **no backing change in the database** — all ten `glossary_*` tables byte-identical to HEAD, yet the rendered file carries a one-line diff. Either a hand edit of a generated file or a DB write since rolled back. Flagged as unbacked at commit time. — `bld-009-r3`.
- The concurrent **`spec-014` residual cycle** shares `examples/fakeshop/db.sqlite3`, `KANBAN.md`, and `KANBAN.html` with R3; `KANBAN.html`'s single-line data block carries both cycles' text at once. Nothing may be reverted to tidy either diff; the maintainer sequences them at commit. — `bld-009-r3`.
- **One card-renumber `grep` is owed at the commit gate.** Every card id cited across this cycle's documents resolves today (**R4 re-derived this: 86 occurrences across four documents; 29 distinct *per document* — the `### Direction 3` table's own column, summed 5+5+10+9 — and 20 distinct *overall* once the four documents' id sets are unioned; 3 unresolved, all 3 graded above**), but a renumber landing before commit would silently falsify them. — `bld-009-r1`; re-measured by R4.

**Closed in-cycle, listed so the final gate does not re-defer them**

- The async `SyncMisuseError` coverage gap — escalated across seven passes as "needs carding", **promoted to a permanent test in-cycle as R1c** per `### Maintainer decision 5`. Not deferred.
- `spec-028` `### Decision 12`'s DISTINCT ON / Layer 6 deferral — **fixed by R2**, reconciled as *discharged by an alternative*, not postponed.
- Card 054's two stale references — **fixed by R3**.
- The two clauses those two fixes falsified — **fixed by R4** (this artifact).

### Non-sweep proof

`git log --stat` over both writable paths, per gate 6 — **`git status` alone was not used as the proof**:

- `docs/SPECS/appx/spec-009-…-rationale.md` — newest commit touching it is still **`f3c94642`** ("docs(specs): reconcile spec-009 and spec-010, and give each a rationale companion"), `208 +++` — i.e. the file has had no commit since the one that created it, and none landed during this cycle.
- `docs/SPECS/spec-054-fieldset-0_1_1.md` — newest is **`947f7494`** ("docs(kanban),docs(specs): retarget cards 050 and 051 onto 0.0.15"), predating this pass.
- Both paths read ` M` (modified, **unstaged**); neither was swept into a concurrent commit. Both edits verified still present in the working tree by content grep.
- HEAD is **`6f8bf818`** and did not move during the pass. Tree dirty count moved **192 → 193**, the +1 being `spec-054` itself, which was **clean** before this pass — so R4's footprint on the tree is exactly its two files, with no third path touched.

### Summary

R4 closed the two contradictions this cycle authored. The `spec-009` rationale no longer tells a reader that `spec-028` `### Decision 12` defers `DISTINCT ON` — the Decision now rejects it outright, in the Decision's own words, so the correction asserts nothing new. `spec-054`'s "Stale card reference" bullet no longer claims in the present tense that card 054 makes a citation R3 removed; it reads as the resolved conflict it is, keeps every line of the live rejection rationale, and points back at the card. The near-copy between spec and board was **preserved deliberately**: the board renders for readers who do not hold the spec.

The four-direction audit was performed, not recorded. Its load-bearing negative: **no rename this cycle made dangled a single inbound anchor** — 0 inbound anchor occurrences into all four edited documents, against a control of 2,809 such occurrences repo-wide, so the zero is a measurement rather than a broken instrument. The archive is complete and the terms chain closes exactly at 23 in all four places it is recorded. The staged-anchor sweep is clean, with a control proving the pattern finds real anchors elsewhere in shipped source.

What the audit added that no prior pass had: **`KANBAN.md:336` still asserts that `spec-009`'s Layer 3 presents auto-finalization as preferred**, which the *first* residual cycle falsified at `f3c94642` — a live board→spec falsification, the very corpus `## R4 inherits` names, found by sweeping the direction rather than the document. And grading a card-id false positive opened a second: **4 edit-owed stale `TODO-BETA-046-0.1.1` sites survive the 2026-07-30 renumber**, 3 of them in `spec-034` and recorded by nobody, alongside a fifth **site** in that enumeration, `spec-034:14`, which is a revision-log bullet and a decided non-edit (`### Recorded for the maintainer` item 2). `spec-034` carries exactly **4** occurrences in total, not five — the fifth is a site of this enumeration, not an occurrence of the token. Both are pre-existing rather than authored here, so both fail the Decision 7/8 test and both are **recorded, not fixed** — `### Maintainer decision 8` sets that ceiling explicitly, and this pass reached it rather than arguing past it.

Three instruments this pass wrote were themselves wrong and were caught by controls rather than by care: a shell corpus sweep that returned 0 for every token on a corpus that provably contained them, an anchor slug that collapsed `\s+` and invented 9 unresolved anchors, and a glossary scan that looked for `id="…"` in a heading-anchored document. Each was discarded and re-run mechanically. That is three more instances of this cycle's standing lesson, and all three were in **this pass's own** work.

### Spec changes made (Worker 1 only)

- `docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md:511-513` — the clause claiming `spec-028` `### Decision 12` "still defers `DISTINCT ON` to `0.0.9`" replaced with a past-tense statement that the sibling site has since been reconciled and now records the port as rejected. Reason: falsified by R2, which this cycle authored (`### Maintainer decision 8` site 1). Append-only preserved and re-proved mechanically (0 deletions against HEAD; `head -166` `cmp` clean).
- `docs/SPECS/spec-054-fieldset-0_1_1.md:800-809` — the "Stale card reference" bullet rewritten to past tense, keeping the full rejection rationale and adding a back-pointer to card 054 via the existing `[kanban]` definition. Reason: falsified by R3, which this cycle authored (`### Maintainer decision 8` site 2). Not de-duplicated, per that decision.
- **No other file was edited.** `spec-009`, `spec-028`, the kanban DB, `KANBAN.md` / `KANBAN.html`, `docs/GLOSSARY.md`, the build plan, and every source and test file are unmodified by this pass.

**Final status:** `planned` (Worker 0 reads this as "dispatch Worker 3").

---

### Round final verification (Worker 1) — closing the Deviation 3 chain

Appended after four review passes and six apply rounds. **Every check below was generated at final state,
not inherited**: nothing here is carried from a prior pass's prose, from Worker 3's re-derivations, or from
the fix history. Where a claim was verified before, it was re-run.

#### 1. Every finding across all four review passes is closed

| Pass | Finding | Disposition |
|---|---|---|
| 1 | **M1** — catalog drops four recorded items | **Closed.** Four bullets in `**Recorded-not-repaired sites**`; all four verified present at final state by lead phrase (`spec-028` `### Decision 3`, `spec-028:1171`, `orders/factories.py`, Card 054 promotion-owner), three naming `bld-009-r2` and one `bld-009-r3`. Nothing refused |
| 1 | **L1** — impossible `1 / 3` cell; `29 distinct across` | **Closed.** Row split per token (`with_hints` 1/1, `with_prefix` 3/2); catalog line names 29 per-document and 20 union |
| 1 | **L2** — `spec-034`'s 4 sites undifferentiated | **Closed.** 3 live-claim + 1 decided non-edit, at recorded item 2 **and** at the catalog's sweep bullet (the second site found by re-checking my own sentence) |
| 2 | **L3** — the split reached 2 of 4 partition sites | **Closed.** Enumerated rather than patched: three remained, all corrected, **no fifth**; partition re-derived as 7 + 3 + 1 + 4 = 15 |
| 2 | **L4** — M1's diagnosis contradicted by its own item 1 | **Closed.** Both my hypothesis and Worker 3's replacement refuted mechanically, plus a third I tested unprompted; replaced with the weaker true statement and the method that survives it |
| 3 | **M2** — item 8 misidentifies the divergence | **Closed.** Two clauses rewritten, **plus a third defect found here and unnamed by the review** (the "eleven tokens" population) |
| 3 | **L5** — stale `:NN` refs, "a fifth occurrence", doubled em dash | **Closed.** Refs converted to content anchors; "fifth **site**" with the 4-occurrence count stated; em dash fixed at my site, **deliberately not** at Worker 3's quotation of it |
| 4 | **L6** — "three rows carry two or three tokens each" | **Closed opportunistically.** Worker 3 recorded a rejection reason and did not hold on it; fixed anyway at both of my sites |

**No finding carries an unrecorded rejection, and none is left open.** The one item deliberately not
changed — the doubled em dash inside `## Review (Worker 3, pass 3)` — is a non-edit on two independent
grounds, the second of which Worker 3 supplied and I had not claimed: **a Worker 3 section is not Worker 1's
to edit**, quite apart from `bld-009-r2`'s `spec-028:41` quotation precedent. `grep -- '— —'` returns
exactly one hit and it is that quotation.

**Checklist audit** (`## Final verification job` step 3): all **8** `### Dispatched findings checklist`
boxes read `- [x]` and **0** read `- [ ]`. R4-8 was the one contested tick — un-ticking it was the M1
remedy considered — and it is now true on evidence rather than on assertion, since Worker 3's pass-2
completeness walk matched every forward-travelling item in all five closed artifacts against the catalog
and found nothing further missing.

#### 2. Item 8 re-verified END TO END at final state

The highest-risk content in the file: it produced **three** self-falsifying clauses across two rounds, so it
was re-derived whole rather than checked clause-by-clause against the fix history. Every claim it now makes,
re-measured this pass from `git ls-files` with both corpora built in one run:

```
757 tracked                                          PASS
path rule excludes 137 -> 620                        PASS
basename rule -> 606                                 PASS
A-B = 14 files, B-A = 0, all under docs/builder/DONE/ PASS
14 distinct tokens swept                             PASS
exactly 2 divergent files carry a token              PASS
   build-008-definition_order_independence-0_0_4.md  DjangoModelType x1  (:362)
   build-046-transport_security-0_0_15.md            TODO-BETA-046-0.1.1 x2 (:793, :841)
12 of 14 identical, 2 differ                         PASS
the 2 differing tokens are exactly those two         PASS
TODO-BETA-046-0.1.1  A=17/6  B=15/5                  PASS
DjangoModelType      A=27/9  B=26/8                  PASS
Advanced{Filter,Order,Aggregate}Set invariant        PASS  (18/7, 30/6, 13/7)
DONE/ absent from 054de9dd^                          PASS
054de9dd creates it with 12; 973d00b2 -> 14          PASS
both token-bearing files in the original 12          PASS
later additions build-010 / build-012 carry ZERO     PASS
```

**All 20 checks pass. Item 8 is factually clean at final state**, including the exposure-not-age provenance
argument and the two per-file line citations. The L6 parenthetical is now countable against the table
itself: 8 single-token rows + 2 + 3 = 13 tokens over 10 rows, +1 from `### Direction 3` = 14.

**Every bar the round was forbidden to move is unmoved**, re-checked here rather than assumed: `### Direction
3` still reads "**15 occurrences / 5 files**"; `### Direction 2`'s table still records `DjangoModelType`
**27 / 9**; the two directions are **not** reconciled; item 8 still closes **recorded, not repaired**, naming
the re-run it does not authorize; `### Maintainer decision 8`'s ceiling is untouched and was never approached.

#### 3. Scope held across the whole round

Proved by content identity, never by `git status` alone and never by mtime (four of this cycle's files still
carry an identical `09:08:22` mtime with zero byte change):

| Path | Final state | Expected |
|---|---|---|
| `…spec-009-…-rationale.md` | 60,361 B / 829 L, `--numstat 621 0`, newest commit `f3c94642` | unchanged since the perform half ✓ |
| `spec-054-fieldset-0_1_1.md` | 54,785 B / 962 L, `--numstat 10 7`, newest commit `947f7494` | unchanged since the perform half ✓ |
| `spec-034-permissions-0_0_10.md` | **clean** | never writable ✓ |
| `docs/builder/DONE/` | **clean** | read-only subject of M2 ✓ |

**Only two paths were written across the entire round**: this artifact (untracked, so it has no HEAD
baseline and cannot have been swept into a commit) and `docs/builder/worker-memory/spec-009-worker-1.md`
(gitignored). **No spec, source, or test file was modified by this round.** Nothing was committed, no branch
was created or switched, and no `git stash` / `checkout` / `restore` / `worktree` was used in any pass.
HEAD is **`1abba7a4`** and has not moved since Worker 3's pass-2 review recorded it.

#### 4. The three R4 finds the final gate must fold into `bld-009-final.md`

Stated here in one place, consumable without rereading this artifact. All three are **pre-existing, not
authored by this cycle**, so all three are recorded-not-repaired under `### Maintainer decision 8`.

1. **`KANBAN.md:336`** asserts that `spec-009` `### Layer 3: Finalization trigger` "still presents hybrid
   auto-finalization as the preferred direction". **False**: that section opens "The trigger is the explicit
   consumer call, and nothing else." and records the auto-trigger direction as rejected — falsified by the
   *first* residual cycle at `f3c94642`. A live board→spec falsification. DB-backed, so the fix is an ORM
   edit plus a regenerate.
2. **`docs/SPECS/spec-034-permissions-0_0_10.md`'s four `TODO-BETA-046-0.1.1` citations — and the
   3 + 1 split must travel with them.** `:220`, `:224`, `:307` are **live-claim rot** and should be
   repointed at `TODO-BETA-054-0.1.1`. **`:14` is a `**Revision 2**` revision-log bullet and a DECIDED
   NON-EDIT** — it reads "the FieldSet card number *was pinned to* the live `TODO-BETA-046-0.1.1`", which is
   **true as history** (`046` was the live id on 2026-06-14; the renumber landed 2026-07-30). Rewriting it
   destroys a true historical record. A sweep handed "4 stale citations" would do exactly that.
3. **Item 8, whose durable half is: state corpus exclusions by BASENAME, since a path prefix silently fails
   on an archived copy.** The measured evidence is in item 8; the gate needs only the rule.

#### 5. Ledger closes against disk

The byte ledger is verified against `wc -c -l` at final state and every row reconciles, including the two
reviewer sections that landed mid-round and the **8-byte `Status:` transitions** each reviewer pass wrote —
a reviewer's status change is itself bytes, which is what made an earlier row miss by exactly 8.

#### Final status

**`final-accepted`.** Nothing failed. Every finding across four review passes is closed or carries a
recorded rejection with its reason; item 8 — the file's highest-risk content — passes all 20 checks at final
state; every forbidden figure is unmoved; scope held to two paths; and the three finds the final gate must
consume are stated in one place.

**The one thing this round should be remembered for is not a fix but a rate.** Across six apply rounds this
artifact produced eight corrections that were themselves wrong, in a cycle whose entire subject is stale
claims — and the last three were caught only because each pass was told to *enumerate the population rather
than patch the named instances*. Two of the eight (L4's replacement diagnosis, item 8's "eleven tokens")
were found by testing a prescribed fix instead of applying it. That is the transferable result, and it is
recorded in `### M2 + L5` and `### L4` rather than only here.

---

## Review (Worker 3)

Fresh Worker 3 spawn, no in-context memory of R4's reasoning. **Every number below was re-derived at my
own desk from the live tree; nothing was accepted on the artifact's prose.**

**HEAD moved during this review and the artifact's non-sweep proof is now stale.** The artifact records
HEAD as `6f8bf818` "and did not move during the pass" — true when written. HEAD is now **`bd7df65b`**
("Share batched relation-id decode, IntegrityError envelope, and serializer entries"), one commit, and
`git log --stat` over it shows **nine source/test paths and not one of this cycle's**. Both R4 edits
survive byte-identical: `git diff --numstat` still reads `621 0` and `10 7`, and the two content greps
(#"was the same claim's sibling site and has since been", #"item 38 (retired)") each return 1. Tree
dirty count is now **191** (was 193), the drop being that commit's own paths. Nothing was swept.

### High:

None.

### Medium:

#### M1 — the deferred-work inventory drops four items the closed artifacts recorded for forward travel

Checklist box **R4-8** is ticked as "one bullet per item with its source artifact named", and
`### Deferred work catalog` is the final gate's input. Walking all five closed artifacts independently,
the catalog reproduces the R1/R1b escalation spine, R1c's two items, R2's items 1-13 and R3's hand-off
faithfully — but **four recorded items have no bullet**, verified absent from the whole artifact by
`grep -in "spec-028:1171\|1171\|standing deferred\|promotion owner\|058-0.1.3"` → no output:

1. **`bld-009-r2:795` item 8 — `spec-028` `### Decision 3`'s kept heading.** R2's own words:
   *"`### Decision 3`'s heading residue (Worker 3's L3). Kept deliberately — 6 in-file anchor uses, no
   version, no phantom owner"*, and at `:531` *"residue you should surface to the maintainer, not
   re-fix."* It is addressed to the maintainer and the catalog is the vehicle.
2. **`bld-009-r2:534` / `:1160` — `spec-028:1171`'s `Ordering`-enum demand-contingent fallback.**
   Recorded verbatim as *"Non-finding, recorded so it is not re-raised"*, and graded identically by
   **four** passes. Dropping it destroys the only thing it was written to do.
3. **`bld-009-r2:30-31` — `orders/factories.py`'s "standing deferred Non-goal" wording**, graded as
   agreeing with the spec's "standing non-goal" and recorded for the same reason as (2).
4. **`bld-009-r3:199` — card 054's promotion-owner ambiguity.** The `#### Definition of done` promotes
   `Meta.fields_class` "per `TODO-BETA-058-0.1.3`" while the Foundation-slice seam says card 054
   promotes the key end-to-end. R3 graded it a maintainer contract call and recorded it. It sits one
   bullet above the very text R4 rewrote in `spec-054` `## Risks and open questions`, which is why its
   absence is easy to miss and worth naming.

**Why this is Medium rather than Low.** The catalog already carries the *analogous* spec-009 trio
(`:654` / `:649` / `:930`) under the explicit rationale *"All recorded so a later pass does not re-open
them as new"*, so the omission is an inconsistency inside R4's own inventory rather than a considered
exclusion — and this cycle has measured what re-opening costs: item (2) alone was re-graded four times.

**Recommended change:** add four bullets under `### Deferred work catalog`, (1)-(3) into
`**Recorded-not-repaired sites**` naming `bld-009-r2`, (4) into the same block naming `bld-009-r3`.
No spec edit, no widening, entirely inside R4's writable artifact.

### Low:

#### L1 — Direction 2's `with_hints` / `with_prefix` row states an arithmetically impossible pair

```docs/builder/bld-009-r4-docs_archive_audit.md:167
| `with_hints` / `with_prefix` | 1 / 3 | `spec-009`: 0. `tests/optimizer/test_selections.py`'s 2 are an unrelated local symbol |
```

The column header is `Occurrences / files`, and every other row obeys it (17/6, 11/4, 3/3, 27/9, 28/5,
9/6 — all reproduced exactly, see `### What looks solid`). Re-measured over the same 620-file corpus:
`with_hints` = **1 occurrence / 1 file**; `with_prefix` = **3 occurrences / 2 files**; combined
**4 / 2**. `1 / 3` is impossible on its face — one occurrence cannot span three files.
`tests/optimizer/test_selections.py` is **clean** (`git status --porcelain` empty for it), so this is
not tree drift between the two runs.

The row's *grade* is unaffected and correct: `spec-009` = 0, and the file's 2 are `with_prefix` on an
unrelated local symbol. But this pass made **"report a denominator"** one of three binding method rules
and caught three of its own instruments by control; a wrong denominator inside the table those rules
govern is the same class one level up.

**Second, milder instance.** `### Deferred work catalog`'s re-measurement reads *"86 occurrences / 29
distinct across four documents"*. 86 reproduces exactly; **29 is the sum of the per-document distinct
counts (5+5+10+9), not the distinct union across the four documents, which is 20.** The Direction 3
table's own column is per-document, so 29 is right for the table and the word "across" makes it read as
a union in the catalog line.

**Recommended change:** correct the row to `4 / 2` (or split the two tokens onto their own rows), and
spell the catalog figure as "29 distinct per document / 20 distinct overall".

#### L2 — recorded item 2 does not separate a revision-log site from three live-claim sites

```docs/builder/bld-009-r4-docs_archive_audit.md:273
2. **`docs/SPECS/spec-034-permissions-0_0_10.md` carries 4 stale `TODO-BETA-046-0.1.1` citations** (`:14`, `:220`, `:224`, `:307`) naming card 046 as the live FieldSet owner.
```

All four were opened. `:220` (*"`_bind_fieldsets` lands with `TODO-BETA-046-0.1.1`"*), `:224`
(*"the live kanban card is `046`"*) and `:307` (*"`TODO-BETA-046-0.1.1` codifies `FieldSet` as the
field-level tier"*) are present-tense claims and are rot exactly as described. **`:14` is a
`**Revision 2**` revision-log bullet** recording what a 2026-06-14 accuracy pass did: *"**(L1)** the
FieldSet card number was pinned to the live `TODO-BETA-046-0.1.1`"*.

R2 established the disposition for precisely this shape one item down the same list: `spec-028:41`,
*"a revision-log bullet quoting it — **a decided non-edit**"*, which the catalog itself carries. Since
item 2 hands the four sites to the recommended repo-wide sweep, an undifferentiated "4 stale citations"
invites that sweep to rewrite a historical revision log — the defect R2 named and declined.

**Recommended change:** split item 2 into "3 live-claim sites (`:220`, `:224`, `:307`) and one
revision-log bullet (`:14`), the latter a decided non-edit on `bld-009-r2`'s `spec-028:41` precedent".
The count itself stays 4; only its disposition splits.

### DRY findings

**None, and the one duplication in the diff is correctly protected.** `spec-054`'s rewritten bullet is a
deliberate near-copy of card 054's own rejection text. `### Maintainer decision 8` states *"Do not
de-duplicate — the board renders for readers who do not hold the spec"*, R4's `### DRY analysis` records
the reason in-file so a later pass does not "fix" it, and the rewrite preserves it. Verified: the
rejection rationale survives whole (`resolver wrapping (upstream-parity, zero-config, zero-overhead on
unmanaged fields)`, the `BasePermission.has_permission` rejection, the `DjangoModelField` "unnecessary
machinery" clause) and the diff is **one hunk**.

**No abstraction was created**, so the existence challenge has no target: R4 wrote no Python, and its
`### DRY analysis` correctly answers the prior question — whether an audit instrument belonged in
`scripts/` — with *no*, since `check_spec_glossary.py` and `check_trailing_commas.py` already cover the
chain and the scaffold. I re-ran both and they are the right instruments. My own three sweep scripts
were written under `docs/builder/temp-tests/r4/` and are gitignored, which is the correct home for a
one-off.

**One consolidation opportunity, recorded not raised.** Directions 1 and 3 both build a
document-population resolver (`<basename>#<fragment>` and the card-id regex). Two ~30-line one-off
scripts in a scratch directory that clears with the cycle is not a DRY defect; it would only become one
if the repo-wide deferral sweep (catalog item, still unrun) is adopted as a standing gate, which is
exactly the condition R4's own `### DRY analysis` names.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are
unchanged. R4 touches no Python at all, so no authorization is needed.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md` (`git diff --stat -- CHANGELOG.md` → empty).

### Documentation / release sanity

**Applies** — the item is entirely documentation and archived specs. Both changed files read end to end.

- **Card IDs match the board.** `TODO-BETA-054-0.1.1` is the live FieldSet card
  (`KANBAN.md:475`); `spec-054`'s back-pointer names it correctly. Re-derived over `KANBAN.md`'s **70**
  distinct card ids, all four permanent documents: `spec-009` 18/5 → 0 unresolved, rationale 5/5 → 0,
  `spec-028` 46/10 → `WIP-ALPHA-028-0.0.8`×6 + `WIP-ALPHA-022-0.0.8`×1, `spec-054` 17/9 →
  `TODO-BETA-046-0.1.1`×1. **86 occurrences total — the artifact's table reproduces row for row.**
- **Version strings / statuses.** Neither edit touches a version, a shipped/planned status, or release
  metadata. No `spec-009` reference exists in `docs/README.md`, `README.md`, `TODAY.md`, `GOAL.md`, or
  `CHANGELOG.md`, so no release surface is implicated.
- **Links introduced point at existing files.** The only new link is `spec-054`'s `[kanban]`, defined at
  `:901` as `../../KANBAN.md`, which resolves from `docs/SPECS/` to `KANBAN.md` — **exists on disk**.
- **No orphan introduced; one retired.** `spec-054` at HEAD: `[backlog]`, `[goal]`, `[kanban]`,
  `[spec-030]`, `[spec-050]` = **5** orphans. In tree: `[backlog]`, `[goal]`, `[spec-030]`, `[spec-050]`
  = **4**; `[kanban]` is now consumed. **0 undefined refs.** Rationale: 11 defs, **0 orphans, 0
  undefined**. Reproduces the artifact exactly.
- **No script-rendered doc regenerated.** `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md` and
  `docs/TREE.md` are untouched by R4 (R3's standing "never regenerate" held). No staging language was
  introduced anywhere.
- **No obsolete "planned"/"coming soon" wording survives in the edited regions.** The whole point of
  both edits is retiring present-tense claims; both now read past-tense and both survive the rewrite
  with their live rationale intact.
- **Archive record preserved.** `spec-009` sits at its archived path with both companions under
  `docs/SPECS/appx/`; nothing in either edit disturbs the historical record.

### What looks solid

**The two authorized clause fixes are true, complete, and assert nothing new.**

- **Site 1.** `spec-028` `### Decision 12` re-read in full at `:979-1010`. Heading: *"No Layer 6
  auto-generation and no DISTINCT ON surface"*; body: *"the ordering surface carries neither"*;
  `Alternatives considered (and rejected)` lists **both** the `ASC_DISTINCT` / `DESC_DISTINCT` +
  `apply_distinct` port **and** the `Meta.distinct` / `distinct_on:` surface as **Rejected**.
  Falsification confirmed independently — the cited Decision now says the opposite. The replacement at
  `rationale:511-513` reads *"no `DISTINCT ON` surface ships, and that spec now records the port as
  rejected rather than deferred"*: "no DISTINCT ON surface" is the Decision's own heading, "ships" is
  its own body (*"No declaration surface ships for it"*), and "rejected" is the Alternatives block's own
  verdict. **Every clause traces to the target's own vocabulary.**
- **Site 2.** Card 054's rendered region bounded mechanically at **`KANBAN.md:475-551`** (next
  `^### [` heading at `:552`) — reproduced exactly. Over that region `item 38` is **absent**;
  `DjangoModelField` survives once, inside R3's recorded rejection. Board-wide `item 38` survives only
  at `KANBAN.md:79`, a **different** card's citation, pointing at `BACKLOG.md:1914` (*"Layered manual
  relation override test policy (item 38)"*). The falsification was real. The rewrite's surviving
  present-tense clause is also true: `grep -c DjangoModelField BACKLOG.md` → **0**, so *"no
  `DjangoModelField` entry exists anywhere in the file"* holds.

**The two-clause ceiling held.** `spec-054`'s diff is **exactly one hunk** (`10 7`). The rationale's
site-1 clause is the only text of its shape in the file — `grep -n "has since been\|was the same claim"`
returns one R4 line (`:511`) and five R1-authored `may no longer make` deliberation headers. Both new
finds were correctly **recorded, not fixed**.

**`KANBAN.md:336` — both halves of the reasoning verified independently.** (a) The claim is false:
`spec-009` `### Layer 3: Finalization trigger` (`:631`) opens *"The trigger is the explicit consumer
call, and nothing else."* (b) It is pre-existing, not this cycle's: `git show HEAD:` of `spec-009` shows
the corrected Layer 3 already at `:672-675`, and `git log -1 --` on that path returns **`f3c94642`** —
the *first* residual cycle. So the falsification predates this cycle's edits and fails the Decision 7/8
test exactly as recorded. The two supporting grounds (DB-backed board, third widening) also hold.

**The `TODO-BETA-046-0.1.1` classification re-derived from scratch and it is right.** Corpus denominator
reproduces exactly: `git ls-files` → **757 tracked**, **137** under `docs/builder/bld-` /
`docs/builder/build-` / `docs/review/` / `docs/dry/`, **620 permanent**. Population **15 occurrences /
5 files** — `types/definition.py` 1, `spec-034` 4, `spec-054` 1, `apps/products/schema.py` 7,
`tests/test_build_tree_md.py` 2. Each grade re-derived:

- **7 carded.** `spec-054:128` owns the sweep as a Slice 4 obligation and its stated population of 7 is
  **exactly 7** in that file.
- **2 not rot.** `tests/test_build_tree_md.py:43,48` construct a synthetic `PlannedPath(card_id=...)`
  and assert the rendered description **echoes the id it was given**. It never reads the board; the
  sibling test in the same file uses the plainly-synthetic `TODO-BETA-099-0.9.9`. Renumber-agnostic.
- **1 correct as written.** `spec-054:128` names the id *as* pre-renumber. A false positive of the
  resolver, correctly graded — the same predicate inversion R3 met on card 054.
- **5 genuine rot / 2 files**, 4 of them in `spec-034` and recorded by no prior pass. Confirmed no board
  card carries `TODO-BETA-046-0.1.1`; card 046 is `DONE-046-0.0.14` (transport) at `KANBAN.md:1713`.
  (See L2 for the one disposition nuance inside those four.)

**The load-bearing negative reproduces, and independently.** I wrote my own resolver
(`docs/builder/temp-tests/r4/anchor_sweep.py`, regex `([\w\-\.]+\.md)#([\w\-]+)` over 6,173 files,
`.git` / `.venv` excluded): **0 inbound anchor occurrences into all four edited documents**, against a
control of **2,843 occurrences across 30 targets** (`GLOSSARY.md` 2,588; `spec-046` 26; `KANBAN.md` 23).
The artifact recorded 2,809 / 30 — the +34 is almost entirely `GLOSSARY.md`, which is dirty under a
concurrent writer; **the control moved and the measurement did not**, which is the stronger result. I
then checked the seven renamed/removed headings by literal text: all seven exist at HEAD (6 in
`spec-009`, 1 in `spec-028`); four are now at **0** occurrences repo-wide, and the three survivors are
each **one line inside the rationale's own old-heading → new-heading mapping** (`:420`, `:246`, `:381`)
— a deliberation record, not a dangling cross-reference. **No rename dangled anything.**

**All three discarded instruments were genuinely discarded, and the re-runs are the ones reported.**

- *Shell corpus sweep.* Its stated control reproduces: `grep -o DjangoModelField KANBAN.md | wc -l`
  → **1**, so a corpus sweep returning 0 was provably wrong. The reported Python re-run is what stands,
  and I reproduced its table row for row: `DjangoModelField` 17/6, `OptimizerStore` 11/4,
  `get_strawberry_annotations` 3/3, `DjangoModelType` 27/9 with `spec-009` retaining **6**,
  `ASC_DISTINCT` 14/2, `DESC_DISTINCT` 14/2, `AdvancedFilterSet` 18, `AdvancedOrderSet` 30,
  `AdvancedAggregateSet` 13, `DISTINCT ON` 28/5, `item 38` 9/6 — **every one exact** (the sole
  exception is L1's row).
- *Anchor slugger.* Confirmed the defect: a `\s+`-collapsing slug maps
  `### Decision 2 — The three-declaration contract` to one dash where GitHub emits **two**. My own
  per-space slugger returns **spec-054 14/0, rationale 0/0, spec-009 0/0, spec-028 159/0** — identical
  to the corrected table, including `spec-028`'s 159 reproducing R2's figure.
- *Glossary `id="…"` scan.* `grep -c 'id="' docs/GLOSSARY.md` → **0**, so the 23/23-missing output was
  the instrument, not the file. The reported slug-based re-run is what stands: I get 0 unresolved
  (my heading count is 157 to the artifact's 154 — a slugger difference on a file two sessions are
  writing; the load-bearing zero is identical).

**Archive audit re-derived from the live DB opened `mode=ro`**, as instructed, after R3 and the
concurrent `spec-014` cycle wrote it: `Card(number=9)` → status key **`done`**, title
**`Rich schema architecture`**; `SpecDoc.path` =
`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`, **present on disk**;
`kanban_cardglossaryterm` count = **23**. **The chain closes at 23 in all four places**: CSV **23** data
rows (24 lines with header) → **23** distinct anchors → **23** resolving `docs/GLOSSARY.md` headings,
**0 unresolved** → **23** DB links.

**Staged-anchor sweep.** `TODO-(ALPHA|BETA|STABLE)-009` → **0 occurrences**. `TODO(spec-009` → **4** in
my run against the artifact's 3 — the fourth is `bld-009-r4:248`, the artifact's own line recording the
result, written after the sweep ran. **All self-referential per-cycle build prose; 0 in shipped source,
tests, or comments.** The control reproduces and is stronger than reported: `TODO(spec-[0-9]+` finds
real anchors in shipped source at `optimizer/walker.py:462` and `:1129` (`TODO(spec-035`) **and**
`filters/sets.py:1377` (`TODO(spec-027`). The prescribed exclusion is confirmed inert — `KANBAN.md` /
`KANBAN.html` / `BACKLOG.md` → 0, 0, 0.

**Append-only re-proved.** `git diff --numstat` → **`621 0`**, zero deletions. The single `-` line is
literally `--- a/docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md`. HEAD is **208**
lines, tree **829** — and 208 + 621 = 829 exactly. `cmp <(head -166 HEAD-copy) <(head -166 tree)` →
**exit 0**; `head -167` differs at line 167, consistent with pure insertion from there. HEAD copy taken
with `git show HEAD:` into an out-of-repo scratch path; **no `git stash` / `checkout` / `restore` /
`worktree` used anywhere in this review.**

**Counts.** Rationale **60,361 bytes / 829 lines** ✓. `spec-054` **54,785 / 962** in tree against
**54,632 / 959** at HEAD ✓ = +153 / +3, and `spec-054` was clean at HEAD so HEAD *is* its "before".
The rationale's stated "before" of **60,351 / 828** is independently corroborated by
`bld-009-r1b`'s own closing ledger (*"rationale 60,351 / 828"*), and 208 + 620 = 828 checks it a second
way. **The artifact is right to state `621 0` as the cycle's footprint rather than R4's** — R4's
contribution to that file is not isolable by diff, since the whole file post-dates HEAD; the +1 line /
+10 bytes are the tightest available bound and the artifact says so rather than over-claiming.

**Gates.**

| Gate | My result |
|---|---|
| `check_spec_glossary.py --spec spec-009` | **exit 0** — `OK: 23 terms - all have glossary entries and at least one spec link.` |
| `check_spec_glossary.py --spec spec-054` | **exit 2**, `missing file: …spec-054-fieldset-0_1_1-terms.csv`. **Pre-existing confirmed**: `git ls-tree -r HEAD` under `054` returns only `spec-054-search_fields-0_1_2-terms.csv` and the spec itself. Not caused by, and not fixable within, R4 |
| `check_trailing_commas.py --check` both edited files | **exit 0** |
| 10 canonical link-def group headers | **10 / 10** in both files |
| In-page anchors | **0 unresolved** in all four permanent documents |
| Orphaned link definitions | **none introduced; one retired** (5 → 4 on `spec-054`) |
| `AGENTS.md` rule 27 | **0** raw `path:NN` added — every added line greps clean for `\.(py\|md):[0-9]+`; both new refs are a heading (`### Decision 12`) and a card id |
| `AGENTS.md` rule 28 / `START.md` link convention | site 2 uses the pre-existing reference-style `[kanban]` def; no inline `](path)` introduced |
| Public surface | `git diff -- django_strawberry_framework/__init__.py` **empty** |

**One check the artifact does not name, run here because it is the one cycle edit whose reverse
direction is unswept.** R1c added a permanent test row; its reverse is "does any permanent document
still assert that gap is open?" Swept the 620-file corpus for `SyncMisuseError` claims of an uncovered
async row — **none**. A test addition creates no inbound citation, so the direction is vacuous rather
than skipped, but it is now measured rather than assumed. Every other cycle edit's reverse **is**
explicitly swept: R1/R1b's by Direction 1's inbound-by-name (which is what found `KANBAN.md:336`),
R2's by Direction 2's `### Reverse of R2's source edits` (I re-verified `orders/inputs.py:197` and
`orders/sets.py:278-279` now read "no DISTINCT ON surface ships" and that `spec-028:979` says exactly
that), R3's by the board→spec sweep that produced site 2, and R4's own by
`### Reverse of R4's own edits`.

**Two recorded gradings spot-checked and both correct.** `permissions.py:511` is
`f"which would change which rows DISTINCT ON keeps."` — an error-message fragment about SQL row
semantics, **not** a Decision 12 citation, so R2's `orders/`-only scope genuinely holds.
`docs/GLOSSARY.md:1434`'s *"so no dynamic order factory is shipped"* is imprecise exactly as recorded:
`orders/factories.py` defines `get_orderset_class` at `:143` and `_dynamic_orderset_cache` at `:58`.

**The `### Failability proofs` and `### Hot-path budget` sections do not apply, and I audited that
rather than accepting it.** Failability: the proof obligation attaches to *every new boundary, guard,
gate, or rejection path in the diff*. I read both hunks whole — they are **two prose clauses in
Markdown**. The diff contains **zero executable lines** (`git diff --numstat` covers only
`docs/SPECS/*.md`; `git diff -- django_strawberry_framework/` and `-- tests/` are empty of R4's work),
therefore zero boundaries, therefore the boundary count is **0**, the mandatory re-run floor is
**empty**, and an empty re-run set is legal on that basis rather than by assertion. **Boundaries I
re-ran: none (none exist). Boundaries accepted on the builder's record: none (none exist).** Hot-path
budget: `build-009-…` `Hot-path declaration: none` — *"No item touches an executable line"* — and R4 in
fact touches none, so no before/after number is owed.

### Temp test verification

No permanent or temp **tests** were needed — R4 ships no code, so there is no behavior to pin. Three
read-only sweep scripts were written under `docs/builder/temp-tests/r4/` (gitignored per `.gitignore`
line 192) purely as review instruments:

- `anchor_sweep.py` — the independent `<basename>#<fragment>` resolver behind the inbound-anchor
  negative and its 2,843-occurrence control.
- `corpus.py` — the independent 620-file permanent-corpus builder and retired-token occurrence counter;
  **this is the instrument that caught L1**.
- `cardids.py` — the independent card-id resolver behind the 70-id board population and the 86/29 table.

**Disposition: deleted with the cycle, none promoted.** None catches a behavior bug (there is no
behavior), so `worker-3.md`'s promotion rule is not engaged. Two of the three are, however, exactly the
shape the still-unrun repo-wide deferral sweep would need — recorded under `### DRY findings` so the
maintainer can decide whether that sweep earns a real `scripts/` home. **No `pytest` was run in this
review and no `--cov*` flag was used anywhere.**

### Notes for Worker 1 (spec reconciliation)

- **No spec edit is owed and no spec finding was raised.** Both authorized clauses are correct as
  written; `spec-009` and `spec-028` were read but not touched. All three findings are defects in
  **R4's own artifact record**, all fixable inside R4's writable set with no widening.
- **Re-derive HEAD and the non-sweep proof before the final gate.** HEAD is now `bd7df65b`; the
  artifact's `### Non-sweep proof` states `6f8bf818` "did not move during the pass". It did not move
  *during* the pass — it moved after. I re-ran the proof: the new commit touches nine source/test
  paths, none of this cycle's; `git log -1 --` on the two writable paths still returns `f3c94642` and
  `947f7494`; both edits present; dirty count 193 → 191. **Nothing is owed but a refreshed hash line**,
  and this cycle's own standing rule is that a quoted hash is re-derived rather than trusted.
- **The `spec-054` `-terms.csv` gate (recorded item 5) is worth the maintainer's look, not a fix here.**
  Confirmed exit 2 and confirmed pre-existing at HEAD. R4's framing is right: the checker cannot
  distinguish "not yet authored" from "lost in an archive move", and the pre-renumber
  `spec-054-search_fields-0_1_2-terms.csv` sitting in `docs/SPECS/appx/` is what makes the ambiguity
  real rather than theoretical.
- **Not escalated, stated for the record:** I found **no** contract-level question, no existence
  challenge with a target, and nothing requiring spec context. This review is closable by four bullets
  and two numbers.

### Review outcome

`revision-needed`.

The two authorized edits are correct, complete, minimal, and hold at every gate; the four-direction
audit was genuinely **performed** and its two headline results — the 0-inbound-anchor negative and the
23-term chain — reproduce independently, one of them against a control that has since grown. The two
new finds are correctly recorded rather than fixed, and the two-clause ceiling held.

What does not hold is R4-8. `### Deferred work catalog` is the final gate's input and its box is ticked
as complete; four items the closed artifacts recorded for forward travel have no bullet, two of them
written verbatim *so that a later pass would not re-derive them* — and one of those was already
re-graded four times. That is a ticked checklist box the work does not cover, which
`worker-3.md`'s acceptance gate makes a Medium, and both Lows are unaddressed corrections in the same
record. Per `### Deviation 3`'s corollary the apply-changes pass is Worker 1's and returns the artifact
to `planned`.

Every finding is confined to R4's own artifact. **No spec edit, no source edit, no widening, and no
maintainer decision is required to reach `review-accepted`.**

---

## Apply changes (Worker 1)

Per `### Deviation 3`'s corollary, the apply-changes pass for a Worker-1-exclusive item is Worker 1's and
returns the artifact to `planned`. Both dispatched findings are entirely inside this artifact: **no spec
file, no source file, and no test file was opened for writing, and no scope widened.** Worker 3's
recommended fixes were treated as hypotheses, not instructions — every one of the six sites was opened at
its cited location and re-measured before a word was written.

### M1 — the four dropped deferred-work items

**Method.** Worker 3 cited four artifact locations. Each was opened and read at the citation, then traced
to the strongest recording of the item rather than the first — three of the four have a later, more
authoritative record than the line the review named, and the bullets are written from that.

| # | Cited by W3 | What is actually recorded there | Strongest record | Forward-travelling? |
|---|---|---|---|---|
| 1 | `bld-009-r2:795` | `### Recorded for the maintainer / R4` item 8 — `### Decision 3`'s heading residue, "recorded so no later pass re-opens it as a fresh finding" | same (`:795-798`), reinforced at `:1855` | **yes** — the section is literally titled "for the maintainer / R4" |
| 2 | `bld-009-r2:534` / `:1160` | W3 `### Notes for Worker 1` item 5, "Non-finding, recorded so it is not re-raised" | `:1853-1854`, "recorded so they are not re-raised a **fourth** time" | **yes** |
| 3 | `bld-009-r2:30-31` | those two lines are the **Plan's evidence bullets**, not a recording — W3's citation is one layer short | `:1855-1857`, the same item-5 grouping, "graded agreeing in the prior pass and I concur" | **yes**, but on a different line than cited |
| 4 | `bld-009-r3:199` | `### Decision 3 — what else on card 054 is falsified`, first out-of-scope bullet: "It is a genuine card-text conflict … resolving it is a maintainer contract call. Not touched; **recorded here**." | same (`:197-201`) | **yes** |

**One correction to the review's own citation, recorded rather than passed through.** Item 3's cited lines
`bld-009-r2:30-31` are the *plan's* evidence for the rewrite, not a deferral record. The recording exists —
`bld-009-r2:1853-1857` groups all three of items 1-3 as "**Non-findings, recorded so they are not re-raised
a fourth time**", which is the single strongest source for the whole trio and is where the bullets are
sourced from. The finding stands; only its pointer was off by one layer.

**Nothing was refused: all four are genuinely forward-travelling and none was already covered.** Absence
re-verified independently before writing (`grep -in "1171\|Decision 3'\|standing deferred\|promotion.owner\|058-0\.1\.3"`
over this artifact returned only Worker 3's own M1 write-up at `:388-403`, no catalog bullet). The nearest
existing bullet under a different wording was checked in each case and is a different item:

- item 1 vs the catalog's `spec-028:1159` / `:1166` bullet — those are `## Doc updates` **blockquotes**, not a heading;
- item 3 vs the catalog's `orders/inputs.py` "residual retired-rationale sites" bullet — a different module and a different clause (`reserved -- see` / `future-extension`, not "standing deferred Non-goal");
- item 4 vs the catalog's existing card-054 bullet — that one is the `#### Definition of done`'s **path** error (`docs/spec-054-…` vs `docs/SPECS/`), not the promotion owner.

**Independently measured at source, so each bullet is actionable without its origin artifact:**

- **Item 1.** `docs/SPECS/spec-028-orders-0_0_8.md:460` reads `### Decision 3 — Five-layer port plus a deferred Layer 6`; `### Decision 12` (`:979`) now records Layer 6 auto-generation as a standing non-goal (`:988`, bolded). The heading's slug `#decision-3--five-layer-port-plus-a-deferred-layer-6` has **6 in-file uses over 5 lines** — `:10`, `:16`, `:126` (×2), `:130`, `:1205` — counted as occurrences with `grep -o`, not as matching lines, precisely because `:126` carries two. R2's recorded "6 in-file anchor uses" reproduces exactly.
- **Item 2.** `spec-028:1171`'s `Ordering`-enum bullet reads "if consumers report wanting the cookbook's `DISTINCT` modifiers in the same enum, a follow-up card can add `ASC_DISTINCT` / `DESC_DISTINCT` as additional enum members"; the section preamble at `:1167` reads "Each item names a preferred answer for the current cut **and a fallback if implementation reveals the preferred answer is wrong**". The non-finding grade is correct and is re-affirmed here rather than re-derived a fifth time.
- **Item 3.** `django_strawberry_framework/orders/factories.py` — module docstring `:20-22` and `get_orderset_class` `:149`, both "standing deferred Non-goal (spec-028 Decision 12)", against `spec-028:988`'s "**standing non-goal**". The module-docstring instance **wraps across a line** ("standing deferred\nNon-goal"), so `grep -n "standing deferred Non-goal"` finds only one of the two — the cycle's first grep-shape trap, live again, and the bullet says so. The file is **clean** (`git status --porcelain` empty for it), so this is shipped text, not a concurrent session's.
- **Item 4.** `KANBAN.md` card-054 region: the `#### Definition of done` box reads "Promote `Meta.fields_class` from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS` only when the resolver-binding pipeline applies end-to-end (per `TODO-BETA-058-0.1.3`)", while the Foundation-slice seam in the same card reads "This card's `_bind_fieldsets` is what populates the slot and promotes the key end-to-end." `docs/SPECS/spec-054-fieldset-0_1_1.md:790-798` records the conflict as "**Promotion-owner ambiguity (card-text conflict)**" with the pinned Decision-8 answer and a fallback. It does sit one bullet above the "Stale card reference" bullet R4 rewrote at `:800`, exactly as the review states.

**Exact edit.** Four bullets appended to `### Deferred work catalog` → `**Recorded-not-repaired sites**`,
after the existing `spec-009:654` bullet and before `**Commit-gate blockers**`. Items 1-3 name `bld-009-r2`
and item 4 names `bld-009-r3`, as recommended. Shape matched to the surrounding bullets: bolded lead claim,
the site by symbol-qualified path or per-cycle `path:NN`, the measured evidence, the reason it was left, and
a trailing `— \`bld-009-rN\`` attribution. **No existing bullet was reworded, reordered, or removed**, and
checklist box **R4-8** stays `- [x]` — it is now true.

### L1 — the two conflated denominators

**Both numbers were re-measured from the tree before the cell was touched; neither of Worker 3's figures was
copied.** Instrument: an independent Python corpus builder
(`scratchpad/corpus_l1.py`, out-of-repo) rebuilding the same 620-file permanent corpus from `git ls-files`
minus `docs/builder/bld-`, `docs/builder/build-`, `docs/review/`, `docs/dry/`, counting **occurrences**
(`str.count`) and **files** separately — never `grep -c`, which counts lines.

- **Corpus denominator reproduces:** 757 tracked − 137 excluded = **620 permanent**.
- **Instrument control, because a re-measurement that only reproduces the disputed row proves nothing:** the same script re-derives `OptimizerStore` = **11 / 4** and `DjangoModelField` = **17 / 6**, matching the table's other rows exactly. So a disagreement on the disputed row is the row, not the instrument.
- **`with_hints` = 1 occurrence / 1 file** — `docs/SPECS/appx/spec-009-…-rationale.md:423`, the rationale's own record of the scrubbed D2 claim.
- **`with_prefix` = 3 occurrences / 2 files** — the same rationale line (1) and `tests/optimizer/test_selections.py` (2).
- Combined the pair is **4 occurrences / 2 files**. The recorded `1 / 3` was impossible in the stated direction: one occurrence cannot span three files. The true reading is that `1` was `with_hints`'s occurrence count and `3` was `with_prefix`'s occurrence count, printed under an `Occurrences / files` header — a token-pair collapsed into one cell.

**The grade was confirmed before the cell was touched, and it is preserved unchanged.** `spec-009` itself:
`grep -c "with_hints\|with_prefix" docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` → **0**. The two
`tests/optimizer/test_selections.py` hits are test **function names** —
`test_node_children_with_runtime_prefix_clones_with_prefix` (`:203`) and
`test_connection_node_children_unwraps_edges_node_with_prefixes` (`:211`, matching as a substring of
`with_prefixes`) — about the optimizer's own runtime prefix handling, **not** `OptimizerStore.with_prefix`.
The file is clean, so this is not tree drift between the two runs.

**Exact edit.** The single row split into **two rows, one per token**, rather than corrected to a combined
`4 / 2`. Worker 3 offered both; the split is chosen because a combined cell re-commits the exact defect the
finding names — two tokens' populations in one number pair — and because this pass's own binding method rule
is "state occurrences and files separately". Each row now satisfies its column header on its own, and both
grades carry forward verbatim with the two test names added so the "unrelated local symbol" claim is
re-derivable without opening the file.

**Second instance — confirmed wrong and corrected.** The catalog's commit-gate bullet read "86 occurrences
/ 29 distinct **across** four documents". Re-derived with an independent card-id resolver
(`scratchpad/cardids_l1.py`, regex `\b(?:TODO|DONE|WIP|BLOCKED)(?:-(?:ALPHA|BETA|STABLE))?-\d{3}-\d+\.\d+\.\d+`,
resolved against `KANBAN.md`'s id set):

```
board distinct ids: 70
spec-009   occ= 18 distinct=  5 unresolved={}
rationale  occ=  5 distinct=  5 unresolved={}
spec-028   occ= 46 distinct= 10 unresolved={'WIP-ALPHA-028-0.0.8': 6, 'WIP-ALPHA-022-0.0.8': 1}
spec-054   occ= 17 distinct=  9 unresolved={'TODO-BETA-046-0.1.1': 1}
TOTAL occurrences: 86
SUM of per-document distinct: 29
DISTINCT UNION across the four: 20
```

**86 and 29 are both correct numbers of different things, and "across" is what makes the pair read as one
thing.** 29 is the sum of the per-document distinct column — right for the `### Direction 3` table, whose
column *is* per-document — and the distinct **union** is **20**. The whole `### Direction 3` table
reproduces row for row, including the 70-id board population and all three unresolved ids, so only the
catalog's summary wording was wrong. Corrected in place to name both figures and label each. Worker 3's
20 was independently re-derived, not accepted.

### L2 — initially out of dispatch scope; escalated, authorized, and now CLOSED

**Recorded in sequence, because the routing is the point.** Worker 3's review raised **three** findings;
this pass's original dispatch named two. **L2** — that recorded item 2's four `spec-034`
`TODO-BETA-046-0.1.1` sites should split into three live-claim sites (`:220`, `:224`, `:307`) and one
revision-log bullet (`:14`), the latter a decided non-edit on `bld-009-r2`'s `spec-028:41` precedent — was
therefore **left untouched on the first sweep of this pass**, because the dispatch limited edits to "the
specific cells/bullets the two findings name" and L2 names a third.

It was neither rejected nor closed: it was a live Worker 3 finding inside this artifact's own writable set,
and `### Deviation 3`'s corollary loops until Worker 3 has no unresolved finding. So it was **escalated to
Worker 0** rather than silently absorbed (which would widen past a dispatch constraint) or silently dropped
(which would lose a finding). Worker 0 confirmed the omission was the dispatch's, re-read
`## Review (Worker 3)`, and **authorized L2 into scope** under the same constraints — artifact-only, no spec
/ source / test file, no widening beyond L2.

**L2 is closed in `### L2 — the disposition split` below.** The prescribed fix was re-verified at source
rather than applied on the review's word; all four sites hold the shape Worker 3 assigns them and the count
stays 4. This block is left standing as the record of the routing, not as an open item.

### L2 — the disposition split

**Why verification mattered more here than anywhere else in this pass.** The whole purpose of the fix is to
stop a downstream repo-wide sweep from rewriting a historical revision log. If Worker 3's shape assignment
were wrong in either direction, the corrected bullet would *cause* the defect it exists to prevent — either
by shielding a live rot site from the sweep, or by handing the sweep a fourth site to rewrite. So all four
were opened at source and graded individually, not spot-checked.

**Population re-measured first, as occurrences.** `grep -on "TODO-BETA-046-0.1.1" docs/SPECS/spec-034-permissions-0_0_10.md | wc -l`
→ **4**, on four distinct lines (`:14`, `:220`, `:224`, `:307`) — `grep -o` rather than `grep -c` because the
unit is occurrences, and here the two agree only because no line carries two. `git status --porcelain` over
that path is **empty** and `git log -1 --` returns `ff65666d` ("docs: normalize review citations to their
durable records"), so this is committed text, not a concurrent session's edit. **Worker 3's "the count stays
4" is confirmed, not assumed.**

| Site | Text as read | Shape | Grade |
|---|---|---|---|
| `:14` | `**Revision 2**` accuracy-pass log (2026-06-14); its `**(L1)**` clause reads "the FieldSet card number **was pinned to** the live `TODO-BETA-046-0.1.1` (the card body's open question still quotes the older `044`)" | **revision log** | **decided non-edit** |
| `:220` | "…`Meta.fields_class` remains rejected at validation (still in `DEFERRED_META_KEYS`), and `_bind_fieldsets` **lands with** `TODO-BETA-046-0.1.1`" (`### Decision 2`) | present-tense claim | **rot** |
| `:224` | "…under the beta FieldSet card ([`TODO-BETA-046-0.1.1`][kanban]; the card body's open question still quotes the older `044`, but **the live kanban card is `046`**)" (`### Decision 2`) | present-tense claim | **rot** |
| `:307` | "`TODO-BETA-046-0.1.1` **codifies** `FieldSet` as the field-level tier." (`### Decision 6`) | present-tense claim | **rot** |

**Worker 3's assignment holds at every site, and two details it did not carry are worth the sweep's
attention:**

- **`:14` is not merely a non-edit by precedent — it is not false as history.** `046` genuinely *was* the
  live FieldSet id on 2026-06-14; the renumber landed 2026-07-30, six weeks later. The bullet records what a
  review round did at the time it did it, so rewriting it would replace a true historical statement with a
  claim that pass never made. That is a strictly stronger ground than `bld-009-r2`'s `spec-028:41` reasoning
  ("rewording it would desync it from the text it quotes"), and both apply.
- **`:224` is the sharpest of the three live sites**, because its own subject is a card-number correction —
  it exists to say "the card body quotes the older `044`, but the live card is `046`". Post-renumber that
  corrective clause is itself false. A claim written to prevent exactly this rot has rotted, which is the
  clearest single argument that the repo-wide sweep is worth running.

**Nothing refused.** All three live sites are genuine rot, the one revision-log site is a genuine non-edit,
and the split is 3 + 1 with the count unchanged at 4 — so Worker 3's recommendation is adopted whole, on
re-derived evidence rather than on its word.

**Exact edit.** Recorded item 2 under `### Recorded for the maintainer — NOT repaired here` gained a
two-bullet sub-list splitting the disposition, plus a lead-in sentence binding the sweep to it ("The count
stays 4; the disposition splits 3 + 1, and whichever sweep eventually takes these must honour the split").
**The item's opening sentence, its count, its four line numbers, its "New — no prior pass recorded these"
claim, and its out-of-scope disposition are all unchanged** — only the disposition is elaborated, exactly as
Worker 3 scoped it. No `spec-034` file was opened for writing; the sites remain recorded, not repaired.

**A second edit WAS required, and finding that out cost me a false sentence first.** This subsection
originally closed by asserting that the `### Deferred work catalog`'s repo-wide-sweep bullet "still points at
this item, so the split reaches the sweep through the existing pointer and needed no second edit." **That was
written before it was checked, and it is false.** The catalog bullet does not point at item 2 at all — it
inlines the claim, reading "**plus (new, R4) `spec-034`'s 4 stale `TODO-BETA-046-0.1.1` citations**", and
**that line is the sweep's actual input**, not item 2. Leaving it would have reproduced L2's defect verbatim
at the one site where it does damage: an undifferentiated "4 stale citations" handed straight to a sweep
authorized to rewrite them. The bullet now carries the split inline (3 live-claim sites named, `:14` marked
a decided non-edit) plus a pointer back to item 2's grading. Two sites, one finding — which is the same
"a fix is not one site until you have measured it" shape `bld-009-r2` hit on `orders/inputs.py`, and it
landed in **my own prose**, one paragraph after I had finished congratulating the split for being thorough.

### L3 — the rot partition, re-derived and enumerated rather than patched at the two named sites

**Worker 3 named two sites; the dispatch asked for the whole population. I enumerated it and it is three,
not two — and the third is the one Worker 3 explicitly declined to change.**

Enumerated mechanically over my own writable ranges (`## Plan`, `## Final verification`,
`## Apply changes`; Worker 3's two review sections are off-limits and excluded), searching
`genuine rot|genuine stale|not rot|carded|correct as written|rot site|4 of them|4 sites|4 stale`:

| Site | State before this pass | Action |
|---|---|---|
| `:206` `### Direction 3` grading | "**5 genuine rot sites across 2 files** … `spec-034…`, **4 sites**" | **corrected** |
| `:274` recorded item 2, opening sentence | "carries **4 stale** … citations … naming card 046 as the live FieldSet owner" (present tense) | **corrected** |
| `:308` catalog sweep bullet | already split by the L2 pass | unchanged ✓ |
| `:356` `### Summary` | "**5 genuine stale** … sites … **4 of them** in `spec-034`" | **corrected** |

**`:274` is the one Worker 3 saw and left.** Its review calls it "the third instance of the same residue …
though there the correction is adjacent and self-limiting, which is why the two remote sites are the ones
worth changing". That is a fair reading, and I corrected it anyway: the sub-bullet immediately below it
denies for `:14` exactly what the opening sentence asserts for all four, and an internal contradiction
resolved only by reading two lines further is still an internal contradiction in the record the maintainer
reads. The count in that sentence is unchanged at 4; only "stale … naming card 046 as the live owner" became
"3 … in the present tense, and 1 recording it in the past tense as history".

**No fifth site.** Everything else the sweep returned falls in one of three classes, **cited by content
rather than by line number** — the first draft of this parenthetical carried four stale `:NN` refs, because
this artifact's own line numbers have moved on every round, which is precisely the defect that produced
them:

- an *occurrence* count that must not move — `### Direction 3`'s population sentence #"is **15 occurrences / 5 files**" and the per-file listing in the fenced block directly below it;
- a site already carrying the split — `### L2 — initially out of dispatch scope` #"should split into three live-claim sites", `### L2 — the disposition split` #"Population re-measured first", its #"All three live sites are genuine rot" close, and `### Summary` #"were re-read at source before the split was written";
- a **deliberate verbatim quotation of the pre-fix wording**, used as evidence in the L2 near-miss record — the two in `### L2 — the disposition split` #"inlines the claim, reading" and #"an undifferentiated \"4 stale citations\" handed straight to a sweep", plus the three inside this subsection's own enumeration table. Those must stay as quoted or they stop being quotations.

**Partition re-derived from the tree, not from the artifact.** 15 occurrences / 5 files:
`apps/products/schema.py` 7, `spec-034` 4, `tests/test_build_tree_md.py` 2, `types/definition.py` 1,
`spec-054` 1. Under the accepted grading that partitions as **7 carded + 3 not rot + 1 correct as written +
4 edit-owed rot = 15** — the `3` being `test_build_tree_md.py`'s 2 plus `spec-034:14`, and the `4` being
`types/definition.py`'s 1 plus `spec-034`'s 3 live-claim sites. Worker 3's arithmetic confirmed.

#### A real find L3's re-derivation turned up: Directions 2 and 3 used DIFFERENT corpus rules

Re-measuring the population under the corpus rule **as this artifact states it** — "757 tracked, minus 137
under `docs/builder/bld-`, `docs/builder/build-`, `docs/review/`, `docs/dry/`" — returns **17 occurrences /
6 files**, not 15 / 5. The extra file is
`docs/builder/DONE/build-046-transport_security-0_0_15.md` (2 occurrences): an **archived per-cycle build
plan**, whose path starts `docs/builder/DONE/build-`, which the stated `docs/builder/build-` prefix does not
match. Both rules measured side by side:

```
A  path-prefix, as the artifact's prose states it   corpus=620   TODO-BETA-046-0.1.1 = 17 / 6
B  basename-prefix (per-cycle build docs wherever
   they live), i.e. the rule as intended            corpus=606   TODO-BETA-046-0.1.1 = 15 / 5
```

**Rule B reproduces 15 / 5 exactly**, which is what R4's Direction 3 and both Worker 3 reviews independently
recorded — so the *intent* is unambiguous and the recorded population is right. But the same comparison run
across Direction 2's whole token list shows the two directions did not use the same rule: nine of eleven
tokens are identical under both, and **two are not** — `DjangoModelType` is **27 / 9 under A** and 26 / 8
under B, and the artifact's Direction 2 table records **27 / 9**. So **Direction 2 was measured under A and
Direction 3 under B.**

- Provenance checked before blaming the tree, and re-derived after a later pass caught this clause asserting the wrong thing: **`docs/builder/DONE/` is not long-tracked — it did not exist before `054de9dd`** (`git cat-file -t 054de9dd^:docs/builder/DONE` reports the path absent from that tree). That commit, this cycle's own pre-flight HEAD (2026-08-15 16:47), **creates** the directory with 12 files; `973d00b2` at 22:59 the same evening brings it to 14. **The anti-drift conclusion survives on stronger evidence than the age claim it replaces:** both token-bearing files were among the original 12, and the two post-pre-flight additions (`build-010-foundation-0_0_4.md`, `build-012-version_release_alignment-0_0_4.md`) carry **zero** swept tokens, verified per file. So no figure in either direction was ever exposed to drift; the divergence is purely a rule defect, and two independent instruments silently applied B here and A there.
- Its 2 occurrences are a closed cycle's build plan discussing this very renumber cluster (`:793`, `:841` — "the `TODO-BETA-046-0.1.1` cluster stays as it is (V9)"). **Per-cycle scratch by nature**, so excluding them is right on the merits; `START.md` "Temp artifact conventions" is the authority, and an archived per-cycle document does not stop being one by moving into `DONE/`.

**RECORDED, NOT FIXED, and the restraint is deliberate.** Rewriting Direction 2's `DjangoModelType` row or
every "620 permanent files" figure is outside L3 and L4, and both numbers are *correct under the rule each
was actually computed with*. What is wrong is only that the artifact states one rule and applies two.

**Routing, recorded because the restraint and its resolution are both part of the record.** This find was
first filed only under `### New findings from this pass` and **deliberately withheld** from
`### Recorded for the maintainer — NOT repaired here`, on the reading that adding an item there was a
structural addition outside the two dispatched findings — and flagged to Worker 0 rather than placed
unilaterally. **Worker 0 authorized it in and corrected the reading**: `### Maintainer decision 8`'s ceiling
is *recorded, not repaired*, so adding a bullet to the block whose whole purpose is recording sits **inside**
that ceiling rather than widening it — R4 already carries two items there on exactly this basis. What would
widen it is repairing the rule or restating the figure, and neither was done: **15 / 5 stands, unmoved.** The
find is now `### Recorded for the maintainer — NOT repaired here` **item 8**, cross-referenced from both
`### Direction 2`'s and `### Direction 3`'s statements of their corpus rule so a reader arriving at either
figure meets the caveat.

### L4 — a false diagnosis replaced by a weaker true one, after testing the replacement too

**The thing under repair was itself a false hypothesis, so adopting the prescribed replacement on its word
would have been the same error one turn later.** Worker 3's counter-hypothesis was tested against all four
items before adoption, and it does not hold either. Both refutations are mechanical:

- **My original claim** — the catalog walked `### Recorded for the maintainer / R4` but not the reviewer-authored `### Notes for Worker 1` blocks. **Refuted by item 1**: an `awk` scan for the nearest `^#{2,4}` heading above each recording puts `bld-009-r2:795` under `:774 ### Recorded for the maintainer / R4` and `:1543` under `:1532 ### Recorded for the maintainer / R4`. Item 1 sat in the walked class and was dropped anyway.
- **Worker 3's replacement** — the four are the items graded non-finding / preference / maintainer contract call. **True of all four, but it does not discriminate**: the catalog already carries `spec-028:1159`/`:1166` (a decided non-edit), `orders/inputs.py`'s residual sites ("neither false today"), `spec-009:592-597` ("Not false"), and the `spec-009:654`/`:649`/`:930` trio ("recorded so a later pass does not re-open them as new") — four groups of identical grade that **were** included. Worker 3's own M1 write-up cites that trio as the reason the omission was an inconsistency rather than a considered exclusion, so the counter-example is already in the record.
- **A third candidate I tested unprompted** — that they cluster by source artifact. **Refuted**: `bld-009-r2` supplied three of the four omissions and two of the four included groups.

**So I wrote the weaker statement rather than a third guess**, exactly as the dispatch licenses. What
survives measurement is: items 1-3 were dropped as a block because they share one recording site; item 4 is
separate and sits in a plan section; and **no observable predicate — heading class, grade, or artifact of
origin — separates the omissions from the included items of identical grade.** The transferable half is
therefore a *method* and not a rule about which blocks to read: enumerate every forward-travelling item in
every closed artifact and match each against the catalog one by one. Worker 3's pass-2 completeness walk did
precisely that and found nothing further, which is the evidence that exhaustive matching works where both
shortcuts failed.

**Nothing refused on either finding.** Both are closed; L4's fix is a replacement rather than a deletion,
and it is longer than what it replaces because a refuted hypothesis is only safely retired by recording why.

### M2 + L5 — item 8's own measurement defects, enumerated rather than patched at the two named

**The irony is the reason this was enumerated rather than patched.** Item 8's entire subject is a stated
count that survived independent replication; the item then made the same class of error three times. Worker 3
named two. The dispatch's instruction was to check every clause for the shape "a specific claim its own
adjacent arithmetic contradicts" rather than assume two was the population. **It was not: there are three.**

Everything below was re-derived at my own desk from `git ls-files`, with both corpora built in one run so
the corpus is an explicit parameter rather than an assumption.

| # | Clause as written | Measured truth | Named by |
|---|---|---|---|
| 1 | "diverge on exactly **one file**, `…build-046…`" | **14 files**, all under `docs/builder/DONE/`; **2** carry a swept token, and they explain *different* deltas | Worker 3 |
| 2 | "`docs/builder/DONE/` is **long-tracked**" (`### L3`) | The directory **did not exist** before `054de9dd`; that commit creates it with 12 files | Worker 3 |
| 3 | "across the **eleven** tokens these sweeps use, **9 of 11** identical" | The sweeps use **14 distinct tokens**; **12 of 14** are identical | **found here** |

**1 — the divergence is a directory, and the `DjangoModelType` delta had no attributed cause.**
`620 − 606 = 14`, which the item's own clause states one sentence earlier, so "exactly one file" was
contradicted by its own arithmetic. Rebuilt: 757 tracked; path rule excludes 137 → **620**; basename rule
excludes 151 → **606**; `A − B` = **14**, `B − A` = **0**, all 14 under `docs/builder/DONE/`
(`build-0{01..08,10,12,44,45,46,48}-*.md`). Swept per file, exactly two carry any token:

```
docs/builder/DONE/build-046-transport_security-0_0_15.md   TODO-BETA-046-0.1.1 x2  (:793, :841)  -> 17/6 -> 15/5
docs/builder/DONE/build-008-definition_order_independence-0_0_4.md   DjangoModelType x1  (:362)  -> 27/9 -> 26/8
```

The other 12 carry none. **This is the consequential half**: item 8 reported two divergent figures and
explained both with one file, so a reader following it would reproduce `15 / 5` and fail to reproduce
`26 / 8`. `build-008:362` is a table row quoting `### Generic fallback questions` — a closed cycle's build
plan discussing the D5 material, per-cycle scratch on exactly the same footing as `build-046`'s two.

**2 — the provenance clause was reaching for a true sentence and grabbed a false one.**
`git cat-file -t 054de9dd^:docs/builder/DONE` → the path is absent from that tree. `054de9dd` *creates* the
directory with **12** files; `973d00b2` (22:59 the same evening, after the 16:47 pre-flight) brings it to
**14**; the two additions are `build-010-foundation-0_0_4.md` and `build-012-version_release_alignment-0_0_4.md`.
**The anti-drift conclusion is stronger without the age claim, not weaker**: both token-bearing files were
among the original 12, and both later additions carry **zero** swept tokens (verified per file, not
inferred), so no figure in either direction was ever exposed to the post-pre-flight change. Rewritten in
item 8 and at its `### L3` source clause.

**3 — the third instance, which is the one this dispatch's instruction was for.** "The eleven tokens these
sweeps use" was a population asserted about my own instrument, and it was wrong in the same direction as
everything else this item corrects: my token list silently omitted `AdvancedFilterSet` / `AdvancedOrderSet` /
`AdvancedAggregateSet`. `### Direction 2`'s table is **10 rows covering 13 distinct tokens** (eight rows carry one token each;
`ASC_DISTINCT` / `DESC_DISTINCT` carries two and `AdvancedFilterSet` / `AdvancedOrderSet` / `AdvancedAggregateSet` carries three — 8 + 2 + 3 = 13), plus `### Direction 3`'s `TODO-BETA-046-0.1.1` = **14 distinct tokens**.
Re-swept across all 14 under both rules: **12 identical, 2 differ** — the same two, so **no figure moves and
no conclusion changes**; only the denominator was understated. All three `Advanced*` tokens are identical
either way (18 / 7, 30 / 6, 13 / 7).

**Nothing refused, nothing re-measured that did not need it, nothing widened.** `15 / 5` did not move,
Direction 2's `27 / 9` did not move, the two directions were not reconciled, and the item's disposition
(recorded, not repaired) and ceiling are untouched. The fix is three clauses inside item 8 plus its one
source clause in `### L3`.

**L5, closed in the same pass as Worker 3 asked.** (a) `### L3`'s "no fifth site" parenthetical carried four
stale `:NN` refs — `:186` is the Direction 3 table's `spec-009` row, not the population sentence; `:928` is
blank; `:991` is prose; `:308` had become `:310`. **Rewritten to cite by content (`#"…"` anchors) instead of
by line**, because this artifact's line numbers have moved on every round and that is exactly what produced
the staleness; the enumeration itself is unaffected and its `:206` / `:274` / `:356` were exact. (b)
`### Summary`'s "a fifth `spec-034` occurrence" asserted a fifth occurrence of a token that has exactly four
— corrected to "a fifth **site** in that enumeration", with the occurrence count stated so the two readings
cannot be confused again. (c) The doubled em dash at the `### Direction 3` cross-reference is fixed; Worker
3's verbatim quotation of it in `### Review (Worker 3, pass 3)` is deliberately left intact, since editing a
quotation to remove the defect it quotes is the same error `bld-009-r2` recorded at `spec-028:41`.

### New findings from this pass

**None in the artifact's substance.** The M1 and L1 re-measurements reproduced every figure they touched
except the two the findings name, and the instrument control (`OptimizerStore` 11/4, `DjangoModelField`
17/6, corpus 620) rules out an instrument disagreement. Two smaller observations, recorded not raised:

- **NEW (M2 pass) — item 8, the correction whose subject IS a measurement defect, contained three of its own.** "Exactly one file" (the corpora differ by 14, a directory not a file, and a *second* file — `build-008-definition_order_independence-0_0_4.md:362` — is what produces the `DjangoModelType` delta item 8 reported but never attributed); "`docs/builder/DONE/` is long-tracked" (it did not exist before this cycle's own pre-flight HEAD); and **"the eleven tokens these sweeps use" — found here, not by the reviewer — where the real population is 14 distinct tokens and 12 of 14 are identical.** All three are the same shape: a stated count over an unstated or unchecked population. **No figure moved and no conclusion changed**; the anti-drift conclusion in fact got stronger evidence. Enumerated rather than patched at the two named, per the dispatch — which is the only reason the third was found.
- **NEW (L3 pass) — `### Direction 2` and `### Direction 3` measured their populations over DIFFERENT corpora, and the artifact states only one rule.** As written the rule is a path prefix (`docs/builder/build-`), which does not match archived plans under `docs/builder/DONE/build-`; as applied in Direction 3 it is effectively a basename rule. Nine of eleven swept tokens are identical either way, but `TODO-BETA-046-0.1.1` is 17/6 vs **15/5** and `DjangoModelType` is **27/9** vs 26/8 — and the artifact records 15/5 in Direction 3 (basename rule, corpus 606) and 27/9 in Direction 2 (path rule, corpus 620). Both figures are correct under the rule each was computed with; only the stated rule is imprecise. **Recorded, not fixed**, as `### Recorded for the maintainer — NOT repaired here` **item 8** (placed there on Worker 0's authorization after being routed rather than filed unilaterally), cross-referenced from both directions' corpus-rule statements; `### L3` carries the side-by-side measurement and the provenance check that rules out concurrent drift. **The part worth carrying: two independent agreeing measurements did not catch this** — Worker 3 reproduced both figures exactly, because each matched whichever rule that direction had used. Only running one population under **both** readings exposed it.
- **L2's fix had a second site, and my own first draft of `### L2 — the disposition split` asserted it did not.** The `### Deferred work catalog`'s repo-wide-sweep bullet inlines "4 stale citations" rather than pointing at recorded item 2, and it is the line the sweep actually reads. Caught by checking a sentence I had already written; recorded in that subsection rather than quietly fixed, because the near-miss is the transferable part. **A one-site fix claim is a population claim** — this cycle's own standing lesson, landing this time inside the pass that was closing a finding about undifferentiated populations.
- **Worker 3's citation for M1 item 3 (`bld-009-r2:30-31`) points at the plan's evidence, not at the recording.** Corrected above; the finding itself is right.
- **All three of M1's items 1-3 come from one place** — `bld-009-r2:1853-1857`, a single "recorded so they are not re-raised a fourth time" grouping — so they were dropped as a **block**, one missed read rather than three independent judgements. Item 4 is separate: its strongest record is `bld-009-r3:190-209`, a **plan** `### Decision 3` section.
- **No mechanism explains the omission, and two candidate diagnoses were tested and refuted. The weaker true statement is the honest one, and it is the useful one.** Stated at length because this bullet is offered forward to the final gate, and a confident wrong diagnosis propagates further than no diagnosis.
  - **Refuted — "the reviewer-authored `### Notes for Worker 1` blocks went unwalked"** (this bullet's own earlier claim). Item 1 is *also* recorded under `### Recorded for the maintainer / R4` at `bld-009-r2:774 → :795` and again at `:1532 → :1543` (section headers confirmed by an `awk` scan for the nearest `^#{2,4}` above each line). It sat in the class the claim says *was* walked, so the claim cannot explain its own omission.
  - **Refuted — "the four are the items graded non-finding / preference / maintainer contract call"** (Worker 3's replacement). The predicate is true of all four, but it does not *discriminate*: the catalog already carries four further groups of exactly that grade — `spec-028:1159`/`:1166` ("Left verbatim: editing a quote … is a worse defect", a decided non-edit), `orders/inputs.py`'s residual sites ("neither false today"), `spec-009:592-597` ("Not false"), and the `spec-009:654`/`:649`/`:930` trio ("recorded so a later pass does not re-open them as new"). A predicate satisfied by both the omitted and the included set explains neither. **Worker 3's own M1 write-up supplies the counter-example itself**, citing that trio as proof the omission was "an inconsistency inside R4's own inventory rather than a considered exclusion".
  - **Refuted — "they cluster by source artifact."** `bld-009-r2` contributed three of the four omissions *and* two of the four included groups above.
  - **What survives:** items 1-3 were dropped together because they share one recording site, and nothing observable separates the four omissions from the items of identical grade that were included. **The transferable half for the final gate is therefore a method, not a rule about which blocks to read:** no heading-class, grade, or artifact-of-origin filter is safe, so the catalog is assembled by enumerating every forward-travelling item in every closed artifact and matching each against the catalog one by one. That is what Worker 3's pass-2 completeness walk did, and it found nothing further missing — which is the evidence that exhaustive matching works where both shortcuts failed.

### Gates re-run after the edits

| Gate | Result |
|---|---|
| `uv run python scripts/check_trailing_commas.py --check docs/builder/bld-009-r4-docs_archive_audit.md` | **exit 0** |
| `git diff --check` over this artifact | clean (untracked; whitespace/conflict-marker scan clean) |
| No spec / source / test file opened for writing | **The only two paths this pass wrote are this artifact and `docs/builder/worker-memory/spec-009-worker-1.md`.** The `M` entries under `docs/SPECS/`, `django_strawberry_framework/`, and `tests/` are prior items' output and concurrent sessions' work, untouched here and never reverted (`AGENTS.md` rule 34). Stated as what this pass wrote, not as a whole-tree before/after — the tree moves under several concurrent writers and a snapshot comparison would be the weaker claim |
| `AGENTS.md` rule 27 | raw `path:NN` refs used only inside this per-cycle artifact, which `START.md` "Temp artifact conventions" exempts; **no permanent document was touched** |
| `pytest` / `--cov*` | **none run, none used** — `AGENTS.md` rule 15 and `BUILD.md` `## Coverage is the maintainer's gate` |
| `git stash` / `checkout` / `restore` / `worktree` | **not used anywhere in this pass** |

### Byte and line delta

| Stage | Bytes | Lines (`wc -l`) |
|---|---|---|
| At dispatch (`Status: revision-needed`) | 73,343 | 731 |
| After M1 + L1 edits, before this section | 76,736 | 736 |
| After this section, at the first `planned` | 94,129 | 914 |
| After L2 closed, at the second `planned` | 104,542 | 997 |
| + Worker 3's pass-2 re-review appended (not this pass's bytes) | 126,198 | 1,293 |
| After L3 + L4 closed, at the third `planned` | 141,876 | 1,417 |
| After item 8 recorded, at the fourth `planned` | 146,651 | 1,428 |
| + Worker 3's pass-3 re-review appended (not this pass's bytes) | 165,950 | 1,694 |
| After M2 + L5 closed, at the fifth `planned` | 176,534 | 1,776 |
| + Worker 3's pass-4 re-review appended (not this pass's bytes) | 188,306 | 1,947 |
| **Final, L6 closed + round final verification, `final-accepted`** | **198,733** | **2,075** |

- **M1 + L1 alone: +3,393 bytes / +5 lines.** The four catalog bullets (+4 lines) and the split table row (+1 line); the two corrected cells widened in place, adding bytes but no line. `+5` is the arithmetic sum of the two structural additions, so it is checkable rather than asserted.
- **This section: +17,393 bytes / +178 `wc -l` lines.** One of those 178 is an artefact of measurement, not content: the file carried **no trailing newline** at dispatch, so `wc -l` under-counted by one throughout (731 `wc -l` = 732 content lines), and appending terminated it. In content lines the pass is 732 → 914, i.e. **+182 overall**.
- **L2, added after Worker 0 authorized it into scope: +10,413 bytes / +83 lines.** Recorded item 2's disposition sub-list, the sweep bullet's inline split, this addendum, and the rewrite of the `### L2` block from "unresolved" to "closed".
- **L3 + L4, the second re-review round: +15,678 bytes / +124 lines** — measured against the **126,198 / 1,293** start-of-round state, NOT against the 104,542 row. Worker 3's pass-2 re-review (**21,656 bytes / 296 lines**) landed in between and is not this pass's footprint; differencing against the older row would have credited me with it. The three rot-partition clauses (`:206`, item 2's opener, `### Summary`), the refuted-hypotheses replacement of M1's diagnosis bullet, and this addendum with the corpus-rule find.
- **Item 8 and its two cross-references: +4,775 bytes / +11 lines**, differenced against the **141,876 / 1,417** start-of-round state. No reviewer section landed between that row and this one, so the two rows are adjacent — stated rather than assumed, because the previous round's delta was wrong for exactly the opposite reason.
- **M2 + L5: +10,584 bytes / +82 lines**, differenced against the **165,950 / 1,694** start-of-round state. Worker 3's pass-3 re-review (**19,291 bytes / 266 lines** of new section, plus the **8** bytes its `Status: planned` → `revision-needed` transition added, = 19,299 exactly) landed between that row and the 146,651 one and is **not** this pass's footprint — checked explicitly this time rather than assumed either way, since the last two rounds got this wrong in both directions (once crediting me with a reviewer's section, once needing to confirm no section had landed).
- **L6 + the round's final verification: +10,427 bytes / +128 lines**, differenced against the **188,306 / 1,947** start-of-round state. Worker 3's pass-4 re-review contributed **11,764 bytes / 171 lines** of new section plus the **8** bytes of its `planned` → `review-accepted` transition = 11,772 exactly, and is **not** this pass's footprint. **A reviewer's `Status:` change is itself bytes** — the third round in a row where reconciling it to the byte was what made the ledger close.
- **Whole artifact: 73,343 → 198,733 bytes, +125,390** — of which **79,755** are Worker 3's four review sections and the remainder Worker 1's plan, perform, six apply rounds, and this final verification. Every byte is inside this per-cycle artifact, which closes with the cycle; `BUILD.md`'s corpus ratchet governs the six standing workflow files and none was touched.
- **On measuring a file's size from inside the file** (`### Non-sweep proof (apply pass)` records the first occurrence): the figures above were emitted by a fixed-point pass — the section was written with fixed-width placeholders, the true values solved for by iterating "substitute, re-measure" until the length stopped moving, then substituted once. Earlier stages' figures are historical states and are **not** re-derived by that pass, so no figure in this file contradicts another.

### Non-sweep proof (apply pass)

- HEAD at the start of this pass: **`e473adf0`** ("Share form and serializer SCALAR / RELATION / FILE decode handlers"), re-derived rather than taken from the dispatch, which quoted the same hash. Worker 3 recorded `bd7df65b`; HEAD has moved again since that review, which is this cycle's standing expectation.
- `docs/builder/bld-009-r4-docs_archive_audit.md` is **untracked** (`??`), so it has no HEAD baseline and cannot have been swept into a concurrent commit; `git log --stat` over it returns nothing, as it must.
- The two permanent files R4 owns were **not reopened** by this pass. `git log --stat` over them still returns `f3c94642` (rationale) and `947f7494` (`spec-054`) as the newest commits touching them, and both remain ` M` and unstaged.
- **HEAD moved once during the L2 addendum**, to **`1abba7a4`** ("Share column-less form and serializer relation annotation"), re-derived rather than carried forward from the top of this section — this cycle's standing rule is that a quoted hash is re-derived, and it has now moved three times across this artifact's life (`6f8bf818` → `bd7df65b` → `e473adf0` → `1abba7a4`). `git log -1 --name-only` over it lists five `django_strawberry_framework/` and `tests/` paths and **none of this pass's**, so nothing was swept.
- `docs/SPECS/spec-034-permissions-0_0_10.md` — L2's and L3's subject — was **read only** throughout both addenda. It is clean and its newest commit is still `ff65666d`.
- **HEAD did NOT move during the L3 + L4 round**: still `1abba7a4`, the same commit Worker 3's pass-2 review recorded, so no re-derivation of the chain was needed beyond confirming it. `git log --stat -1` lists the same five `django_strawberry_framework/` and `tests/` paths and none of this cycle's.
- **`docs/builder/DONE/build-046-transport_security-0_0_15.md`, which L3's corpus find names, was read only and is clean.** Provenance proved with `git log`, not `git status` alone: added at `054de9dd` (2026-08-15 16:47, this cycle's own pre-flight HEAD) and untouched by the later `973d00b2`. So its 2 occurrences were in the corpus from the start and are **not** concurrent-session drift — which is what makes the finding a rule-precision defect rather than a stale measurement.
- **Worker 3's mtime trap re-confirmed and honoured.** Four of this cycle's files still carry an identical `09:08:22` mtime with zero byte change; every provenance claim in this pass is a content or `--numstat` identity, never an mtime.
- Nothing was reverted and no concurrent session's file was touched.

### Summary

Both dispatched findings are closed inside this artifact, with no spec edit, no source edit, and no
widening. **M1:** all four dropped items were verified genuinely forward-travelling at their own sources —
none was closed by a later round and none was already carried under a different wording — and four bullets
now sit in `**Recorded-not-repaired sites**`, three naming `bld-009-r2` and one `bld-009-r3`, each written
from the artifact text rather than from the review's paraphrase and each carrying enough measured detail to
be actionable by a reader who has not opened its origin. Nothing was refused. **L1:** `with_hints` is
1 occurrence / 1 file and `with_prefix` is 3 / 2, both re-measured against a 620-file corpus whose other
rows reproduce exactly; the impossible `1 / 3` cell is now two rows, one per token, with the grade
(`spec-009` = 0, the two hits an unrelated local symbol) confirmed and preserved. The catalog's second
instance is genuinely wrong in the same way and is corrected to name **29 distinct per document** and
**20 distinct overall** — the union figure independently re-derived, not copied.

**L2**, which Worker 3 raised and the original dispatch did not name, was escalated to Worker 0 rather than
silently absorbed or silently dropped; Worker 0 authorized it into scope and it is now closed too. All four
`spec-034` sites were re-read at source before the split was written: `:220`, `:224`, `:307` are live
present-tense claims and are rot, `:14` is a `**Revision 2**` log bullet and a decided non-edit — on
`bld-009-r2`'s `spec-028:41` precedent and on the stronger ground that it is **not false as history**, since
`046` really was the live id six weeks before the renumber. The count stays 4 and only the disposition
splits, as Worker 3 said. Nothing was refused.

**L3 and L4** closed a second re-review round, both inside this artifact. **L3:** the L2 split had reached
2 of the 4 sites carrying the undifferentiated claim; I enumerated the population over my own writable
ranges rather than fixing the two named, found **three** still open (`:206`, recorded item 2's opening
sentence, `### Summary`) including the one Worker 3 judged self-limiting, corrected all three, and confirmed
**no fifth**. The partition is re-derived from the tree as **7 + 3 + 1 + 4 = 15**; no occurrence count moved.
**L4:** the diagnosis under repair was itself a false hypothesis, so the prescribed replacement was tested
before adoption — and it fails too, because the catalog already carries four groups of the same
non-finding/preference grade that *were* included. A third candidate (clustering by source artifact) fails
as well. The bullet now records all three refutations and states the weaker true thing: nothing observable
separates the omissions, so the transferable half is exhaustive enumerate-and-match, not a rule about which
blocks to read.

**L3's re-derivation turned up a genuine new find:** `### Direction 2` and `### Direction 3` measured over
**different corpora** — 620 files under the path-prefix rule the artifact states, 606 under the basename
rule Direction 3 actually applied — which is invisible on nine of eleven swept tokens and visible on two
(`TODO-BETA-046-0.1.1` 17/6 vs 15/5, `DjangoModelType` 27/9 vs 26/8). Both recorded figures are right under
the rule each used; only the stated rule is imprecise. Recorded, not fixed, as `### Recorded for the maintainer`
**item 8** — routed to Worker 0 rather than placed unilaterally, and authorized in on the reading that a block whose purpose is recording
sits inside `### Maintainer decision 8`'s ceiling rather than widening it. **15 / 5 did not move.**

**Item 8 then failed at its own subject three times over, and the enumeration is why all three were found.**
Worker 3 caught two — "exactly one file" (the corpora differ by **14**, a whole directory, and a *second*
file is what produces the `DjangoModelType` delta item 8 reported but never attributed) and a false
"long-tracked" provenance clause. Checking every remaining clause for the same shape rather than
patching the two named turned up a **third**, unnamed: "the eleven tokens these sweeps use" is a
population of **14**, of which 12 are identical. **No figure moved, no conclusion changed, and the
anti-drift argument came out stronger** — both token-bearing files predate the only post-pre-flight
change to that directory, and both files added after it carry zero swept tokens.

**The pass closed with one self-inflicted near-miss worth more than the finding it sat next to.** The first
draft of the L2 subsection claimed the fix needed no second site; checking that sentence showed the
`### Deferred work catalog`'s sweep bullet inlines "4 stale citations" and **is** the line the sweep reads,
so leaving it would have handed a revision log to a sweep licensed to rewrite it — L2's exact defect,
reproduced by the pass closing L2. Both sites now carry the split. The near-miss is recorded rather than
quietly fixed, because "a one-site fix claim is a population claim" is this cycle's own standing lesson and
this is its clearest instance.

**Final status:** `planned` (Worker 0 reads this as "dispatch Worker 3", per `### Deviation 3`).

---

## Review (Worker 3, pass 2) — re-review

Fresh Worker 3 spawn, no in-context memory of the apply pass. **Every figure below was re-derived from the
live tree; nothing was accepted on the apply pass's prose, and its recommended readings were treated as
hypotheses.** HEAD is **`1abba7a4`** ("Share column-less form and serializer relation annotation", 09:08:19)
and **did not move during this review**; the chain the artifact records (`6f8bf818` → `bd7df65b` →
`e473adf0` → `1abba7a4`) is verified by `git log --oneline 6f8bf818..1abba7a4`, three commits in that
order. `git log -1 --name-only 1abba7a4` lists five `django_strawberry_framework/` and `tests/` paths and
**none of this cycle's**. Tree dirty count 195. No `git stash` / `checkout` / `restore` / `worktree`, no
`pytest`, no `--cov*` flag anywhere in this pass.

### High:

None.

### Medium:

None. **The completeness question closes clean** — see `### What looks solid`, which records an independent
walk of all five closed artifacts rather than a spot-check of the four bullets.

### Low:

#### L3 — the L2 split did not reach the two sites that *derive* the "5 genuine rot" count

The apply pass corrected two sites (recorded item 2 and the catalog's sweep bullet). Two further sites in
the same document still partition `:14` as rot, and they are the sites the count comes from:

```docs/builder/bld-009-r4-docs_archive_audit.md:206
Graded: **7 carded** …, **2 not rot** …, **1 correct as written** (`spec-054:128`), leaving **5 genuine rot sites across 2 files** — `types/definition.py` … and **`spec-034-permissions-0_0_10.md`, 4 sites**
```

```docs/builder/bld-009-r4-docs_archive_audit.md:356
**5 genuine stale `TODO-BETA-046-0.1.1` sites survive the 2026-07-30 renumber**, 4 of them in `spec-034`
```

Recorded item 2 now says, in the artifact's own words, that `:14` is **"a DECIDED NON-EDIT, *not a fourth
rot site*"**. `:206` and `:356` still count it as one, so the 15-occurrence partition (`7 + 2 + 1 + 5`) no
longer matches the grading the same document records; under the accepted split it is `7 + 3 + 1 + 4`. Item
2's own opening sentence is the third instance of the same residue — it still says all four sites name card
046 "as the live FieldSet owner" (present tense), which the sub-bullet immediately below it denies for
`:14` — though there the correction is adjacent and self-limiting, which is why the two remote sites are
the ones worth changing.

This is the *same shape* the apply pass caught in itself one paragraph after congratulating the split for
being thorough ("a one-site fix claim is a population claim"): the population of sites carrying the
undifferentiated claim was measured at two, and it is four. It does not reach the recommended sweep — the
sweep's input is the catalog bullet, which now carries the split — so the damage L2 exists to prevent is
already prevented. What is left is an internal contradiction in the record the maintainer reads.

**Recommended change:** one clause at `:206` and one at `:356` naming the edit-owed count (4 rot + 1
revision-log non-edit) and pointing at recorded item 2's grading. No count moves; the population is still
15 occurrences / 5 files and the `spec-034` occurrence count is still 4.

#### L4 — M1's stated diagnosis is contradicted by its own item 1

```docs/builder/bld-009-r4-docs_archive_audit.md:930
which suggests the original catalog assembly walked `### Recorded for the maintainer / R4` sections but not Worker 3's `### Notes for Worker 1` sections in the same artifacts. **That is the transferable half for the final gate**
```

The first half of the bullet is right and I verified it: all three of M1's items 1-3 are recorded together
at `bld-009-r2:1853-1857`, inside `## Review (Worker 3, pass 3)` → `### Notes for Worker 1 (spec
reconciliation)` (heading positions confirmed by an `awk` scan of that file's `^#{2,4}` lines).

The causal half does not survive its own evidence. **Item 1 — `spec-028` `### Decision 3`'s kept heading —
is *also* recorded in two `### Recorded for the maintainer / R4` sections** (`bld-009-r2:795-798`, restated
at `:1543-1544`, and standing under `:2129`'s "Items 1-10 stand as written"), i.e. in exactly the section
class the bullet says *was* walked. So "the Notes blocks went unwalked" cannot explain why item 1 was
dropped. Item 4's strongest record is `bld-009-r3:190-209`, a **plan** `### Decision 3` section, which is
neither class. What the four omissions do share is their *grade*: all four are items the closed artifacts
graded **non-finding / preference / maintainer contract call** rather than deferred defect — a predicate
that covers all four and does not depend on which heading they sat under.

It matters because the bullet is offered forward ("the transferable half for the final gate"), and a gate
that adopts a section-based rule inherits a rule its own counter-example already broke.

**Recommended change:** replace the causal clause with the observation it can actually support — the four
dropped items are the four graded non-findings/preferences, independent of section — or state it as an
unresolved question. My independent walk (below) found nothing further missing either way, so the
completeness result does not rest on this.

### DRY findings

**None.** The apply pass wrote no code and created no abstraction, so the existence challenge has no
target. The two scratch instruments it used (`corpus_l1.py`, `cardids_l1.py`) live outside the repo, which
is the right home for a one-off; I rebuilt both independently rather than reading them. The deliberate
near-copy between `spec-054`'s bullet and card 054's rejection text is still protected and still
un-de-duplicated, per `### Maintainer decision 8`. The four new catalog bullets were checked against every
neighbouring bullet for overlap and none duplicates one: item 1 vs the `spec-028:1159`/`:1166` blockquote
bullet (a heading vs two quotations), item 3 vs the `orders/inputs.py` residual-rationale bullet (a
different module and a different clause), item 4 vs the existing card-054 bullet (promotion owner vs the
`docs/spec-054-…` path error) — the apply pass's own three distinctions, re-derived at source.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are
unchanged. This pass wrote no Python.

### CHANGELOG sanity

Not applicable; the pass did not modify `CHANGELOG.md`.

### Documentation / release sanity

**Applies.** The two permanent documents R4 owns are **byte-unchanged since my first review**, so the
substance re-verified there stands untouched:

- rationale **60,361 bytes / 829 lines**, `git diff --numstat` **`621 0`**, deletions against HEAD = **1**
  (the `--- a/…` diff header), i.e. append-only holds and the site-1 clause is present at `:512`.
- `spec-054` **54,785 / 962**, `--numstat` **`10 7`**, the site-2 bullet present at `:800` reading
  "**Stale card reference — `BACKLOG.md` item 38 (retired).**".
- `check_trailing_commas.py --check` → **exit 0** on both, and on this artifact.
- No script-rendered doc regenerated: `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md`
  untouched by this pass.

### What looks solid

**The citation correction is right, and I re-derived both halves.** `bld-009-r2:30-31` are two evidence
bullets inside the plan's `### The finding, re-verified at HEAD before planning` (they quote
`orders/factories.py`'s two docstring sites as input to the rewrite); they are not a deferral record, so
my prior citation was one layer short. `bld-009-r2:1853-1857` is the real recording — W3 pass 3's item 5,
"**Non-findings, recorded so they are not re-raised a fourth time**" — and it does carry all three of items
1-3. Sourcing the bullets from there rather than from my pointer was the correct call.

**All four M1 bullets are actionable without their origin artifact, and every measurement in them
reproduces:**

- **Item 1.** `docs/SPECS/spec-028-orders-0_0_8.md:460` reads `### Decision 3 — Five-layer port plus a
  deferred Layer 6`; `grep -on` on the slug returns **6 occurrences over 5 lines** — `:10`, `:16`, `:126`
  ×2, `:130`, `:1205` — exactly as the bullet states, and `:126` really does carry two, which is why
  `grep -c` would have said 5. `### Decision 12` at `:979` records the Layer 6 surface as a **standing
  non-goal** (bolded, `:988`).
- **Item 2.** `spec-028:1171` is the `Ordering`-enum fallback bullet and `:1167` is the section preamble
  declaring "a fallback if implementation reveals the preferred answer is wrong" — both read at source, so
  the non-finding grade is re-confirmed rather than re-derived a fifth time. The four prior gradings exist
  at `bld-009-r2:534`, `:1160`, `:1853`, plus the apply pass's re-grade named at `:1160`.
- **Item 3.** `orders/factories.py` carries `standing deferred` at **`:21`** (module docstring, wrapping as
  `standing deferred` / `Non-goal (spec-028 Decision 12).`) and **`:149`** (`get_orderset_class`). The wrap
  is real: `grep -n "standing deferred Non-goal"` finds only the second. The file is **clean**
  (`git status --porcelain` empty), so this is shipped text. Both agree with `spec-028:988`, matching the
  gradings at `bld-009-r2:584-585`, `:1782`, `:1928`.
- **Item 4.** `KANBAN.md:511` carries the DoD clause "Promote `Meta.fields_class` … (per
  `TODO-BETA-058-0.1.3`)"; `docs/SPECS/spec-054-fieldset-0_1_1.md:789-798` carries
  "**Promotion-owner ambiguity (card-text conflict)**" with the pinned Decision-8 answer and a fallback,
  and it does sit **one bullet above** the "Stale card reference" bullet at `:800` that R4 rewrote.

**The catalog is now complete, and that is an independent finding rather than an audit of the four
bullets.** I walked every `### Notes for Worker 1` block, every `### Recorded for the maintainer / R4`
section, every `### Escalations carried forward` block and the plan-level decision sections across all five
closed artifacts, and matched each forward-travelling item against the catalog:

- **`bld-009-r1`** — `spec-010:8` / `:491` / `:67` (+ its near-duplicate sentence), `types/definition.py`'s
  `fields_class` docstring, the rationale's "three sites" bullet, `filters/sets.py`'s in-place `Meta`
  mutation, the commit-gate card-renumber grep, and the async `SyncMisuseError` gap: **all present** (the
  last as closed-in-cycle, correctly — R1c shipped it). Its `:610` `relation_kind` hand-off and the
  `:930` / `:1002` scoping hand-off were **closed by R1b** (`:610` now reads `relation_kind: RelationKind`),
  so their absence is correct. Its artifact-internal notes (a byte-split arithmetic slip, an mtime
  observation, a lesson-shaped rule) are per-cycle scratch that closes with the cycle — correctly excluded
  under the same principle that excludes R1b's six artifact-only Lows.
- **`bld-009-r1b`** — `spec-009:592-597`, `rationale:533`, `rationale:359-360`, `spec-009:654` / `:649` /
  `:930`: **all present**. Its instrument carry-forwards (report line coverage, the gap-size caveat, the
  footprint-spelling rule) were addressed to R2/R4, which have now run; nothing outstanding.
- **`bld-009-r1c`** — `tests/test_connection.py:3`'s stale spec path and the `check_trailing_commas`
  commit-gate row at `tests/test_connection.py:1062`: **both present**, the first with R4's decided
  disposition attached.
- **`bld-009-r2`** — items 1-13 walked one by one against the catalog: `KANBAN.md:3680` ✓, `spec-028:1159`
  / `:1166` ✓, the GLOSSARY `OrderSet` entry ✓, `spec-028:195` / `:1191` ✓, the `[relay]` orphan ✓, the
  `orders/inputs.py` fourth citation (fixed in-cycle) ✓, `:734` + `:41` ✓, **`### Decision 3`'s heading (was
  missing — now bullet 1)** ✓, the repo-wide sweep ✓, the residual `orders/inputs.py` sites ✓, `spec-027` ✓,
  the rationale clause (fixed by R4) ✓, both factories unconsumed ✓ — plus the two W3 non-findings that are
  now bullets 2 and 3.
- **`bld-009-r3`** — the escalated `spec-054:800-803` Medium (became R4-2) ✓, the unbacked `docs/GLOSSARY.md`
  dirty file ✓, the `spec-014` concurrency hand-off ✓, card 054's `#### Definition of done` path error ✓,
  and **the promotion-owner conflict (was missing — now bullet 4)** ✓. Its three artifact-only imprecisions
  are per-cycle scratch, correctly excluded.

**Nothing further is missing.** One item deserves a sentence so a later reader does not read it as a gap:
`KANBAN.md:336` — R4's own headline board→spec find — has **no catalog bullet**, and that is correct as the
block is scoped ("Assembled from all five *closed* artifacts"), since it is R4's own find and lives in
`### Recorded for the maintainer — NOT repaired here` item 1. The final gate must fold R4's own two finds in
when it writes `bld-009-final.md`'s catalog; noted for Worker 1 below rather than filed as a finding.

**L1's numbers are right and the split resolves the conflation rather than relocating it.** Rebuilt the
corpus independently from `git ls-files` (757 tracked − 137 under `docs/builder/bld-`, `docs/builder/build-`,
`docs/review/`, `docs/dry/` = **620**) and counted occurrences and files separately with `str.count`:
`with_hints` **1 / 1**, `with_prefix` **3 / 2**. Every other row of the Direction 2 table reproduces
exactly — `DjangoModelField` 17/6, `OptimizerStore` 11/4, `get_strawberry_annotations` 3/3,
`DjangoModelType` 27/9, `ASC_DISTINCT` 14/2, `DESC_DISTINCT` 14/2, `AdvancedFilterSet` 18,
`AdvancedOrderSet` 30, `AdvancedAggregateSet` 13, `DISTINCT ON` 28/5, `item 38` 9/6 — so the instrument
agrees on everything and the disputed cell was the cell. Two rows rather than one combined `4 / 2` is the
right call for the reason the apply pass gives: a combined cell re-commits the defect. Both preserved
grades hold — `grep -c "with_hints\|with_prefix"` on `spec-009` → **0**, and
`tests/optimizer/test_selections.py:203` / `:211` are `test_node_children_with_runtime_prefix_clones_with_prefix`
and `test_connection_node_children_unwraps_edges_node_with_prefixes` (the second matching as a substring of
`with_prefixes`), a local runtime-prefix symbol and not `OptimizerStore.with_prefix`.

**The second L1 instance is corrected correctly.** My own resolver over `KANBAN.md`'s **70** distinct card
ids returns `spec-009` 18/5, rationale 5/5, `spec-028` 46/10 (`WIP-ALPHA-028-0.0.8` ×6,
`WIP-ALPHA-022-0.0.8` ×1), `spec-054` 17/9 (`TODO-BETA-046-0.1.1` ×1): **86 occurrences, per-document
distinct summing to 29, distinct union 20, 3 unresolved.** The corrected catalog line at `:332` now labels
both figures and the `### Direction 3` table's per-document column is untouched — right on both counts.

**L2's grading is correct at all four sites, verified verbatim rather than on the review's word.**
`grep -on "TODO-BETA-046-0.1.1" docs/SPECS/spec-034-permissions-0_0_10.md` → **4**, on `:14`, `:220`,
`:224`, `:307`; the file is **clean** and its newest commit is `ff65666d` (2026-07-30), so it is committed
text. `:14` is the `**Revision 2**` accuracy-pass log and its `**(L1)**` clause reads, character for
character, "the FieldSet card number was pinned to the live `TODO-BETA-046-0.1.1` (the card body's open
question still quotes the older `044`)" — **past tense, and true as history**: `046` was the live FieldSet
id on 2026-06-14 and the renumber landed 2026-07-30. The apply pass's second ground is therefore real and
is stronger than the `spec-028:41` precedent, as it says. `:220`, `:224`, `:307` are present-tense and are
rot; `:224`'s own subject is a card-number correction, so it has rotted in the way it was written to
prevent. The count stays 4 and only the disposition splits.

**The second site the apply pass found by re-checking its own sentence is the sweep's real input, and the
split reached it.** `### Deferred work catalog`'s repo-wide-sweep bullet (`:308`) now names the three
live-claim sites and marks `:14` a decided non-edit with a pointer back to item 2's grading. Recording the
near-miss instead of quietly fixing it is the right disposition and is the most transferable thing in the
pass. (Two further sites still carry the undifferentiated claim — L3 — but neither is sweep input.)

**Scope held exactly, and I proved it by content rather than by `git status`.** The only paths this pass
wrote are this artifact (untracked, so it has no HEAD baseline and cannot have been swept) and
`docs/builder/worker-memory/spec-009-worker-1.md` (gitignored). Every other file this cycle has ever
touched is byte-unchanged from its owning item's closing ledger:

| Path | Now | Owning item's recorded close |
|---|---|---|
| rationale | `621 0`, 60,361 / 829 | R4 perform half ✓ |
| `spec-054-fieldset-0_1_1.md` | `10 7`, 54,785 / 962 | R4 perform half ✓ |
| `spec-009-…-0_0_4.md` | `114 172`, 61,170 / 1,096 | `bld-009-r1b:3499` `114 / 172` ✓ |
| `spec-028-orders-0_0_8.md` | `49 57`, 289,179 / 1,354 | `bld-009-r2:2111` ✓ |
| `orders/inputs.py` | `5 6`, 16,327 / 354 | `bld-009-r2:2016` ✓ |
| `orders/sets.py` | `1 1` | R2 ✓ |
| `spec-034-permissions-0_0_10.md` | **clean** | never writable ✓ |

So no prior item's deliverable was reopened, no spec, source, or test file was written, nothing was
reverted, and nothing was committed. Note for any later pass reading mtimes: `spec-009`, `spec-028`,
`spec-054` and the rationale all carry an identical `09:08:22` mtime, three seconds after HEAD moved —
**mtime is not a write signal in this tree**; the byte and `--numstat` identities above are.

**The byte ledger's fixed-point solve checks out, and it matches disk.** `73,343 → 76,736 → 94,129 →
104,542` with deltas `+3,393`, `+17,393`, `+10,413` summing to **+31,199** ✓; line counts `731 → 736 → 914
→ 997` with `+5`, `+178`, `+83` ✓. `wc -c -l` on disk right now: **104,542 / 997** ✓. The file **does** end
with a newline (`tail -c 1` → `0a`), which is what the "appending terminated it" clause claims, and the
content-line reading `732 → 914 = +182` follows from it. No earlier figure in the file contradicts a later
one.

**Failability proofs and hot-path budget: neither applies, and I audited that rather than accepting it.**
The pass's whole diff is Markdown inside a per-cycle artifact — `git diff` over
`django_strawberry_framework/` and `tests/` carries no line of this pass's — so the boundary count is
**0**, the mandatory re-run floor is empty, and an empty re-run set is legal on that basis rather than by
assertion. **Boundaries re-run: none (none exist). Boundaries accepted on the builder's record: none (none
exist).** The plan declares `Hot-path declaration: none`, and no executable line was touched.

### Temp test verification

No tests, temp or permanent — the pass ships no behavior. Two read-only instruments were rebuilt for this
review (a permanent-corpus occurrence counter and a card-id resolver) under the session scratchpad
**outside the repository**, so nothing was added under `docs/builder/temp-tests/` and there is nothing to
promote or delete. `worker-3.md`'s promotion rule is not engaged: neither instrument catches a behavior bug,
because there is no behavior.

### Notes for Worker 1 (spec reconciliation)

- **No spec edit is owed and no spec finding was raised.** Both Lows are one-clause corrections inside this
  per-cycle artifact — no widening, no permanent document, no source, no test. `### Maintainer decision 8`'s
  two-clause ceiling is untouched and was not approached.
- **The final gate must fold R4's own two recorded-for-maintainer finds into `bld-009-final.md`'s
  `### Deferred work catalog`** — `KANBAN.md:336` (the board→spec falsification) and `spec-034`'s four
  `TODO-BETA-046-0.1.1` citations with their 3 + 1 disposition. This artifact's catalog block is correctly
  scoped to the five *closed* artifacts, so R4's own finds are outside it by design; they live in
  `### Recorded for the maintainer — NOT repaired here` items 1 and 2. If L3 is applied, the gate should
  take the corrected partition.
- **Re-derive HEAD at the gate.** It is `1abba7a4` as of this review and has moved four times across this
  artifact's life. The `### Non-sweep proof (apply pass)` is accurate as written; only the hash ages.
- **Not escalated, stated for the record:** no contract-level question, no existence challenge with a
  target, nothing requiring spec context. This review is closable by two clauses.

### Review outcome

`revision-needed`.

Everything the dispatch put in doubt came back **confirmed**: the citation correction is right, all four M1
bullets are genuine, correctly sourced and independently actionable, the catalog is complete on an
independent five-artifact walk, L1's numbers reproduce to the occurrence against a control that reproduces
the whole table, L2's four-site grading holds verbatim including the historical-truth ground for `:14`, the
scope held to two writable paths proved by content, and the byte ledger matches disk with no internal
contradiction.

What blocks acceptance is small and of this round's own characteristic shape: the L2 fix corrected two of
the four sites carrying the undifferentiated claim (**L3**), and M1's stated diagnosis is contradicted by
its own item 1 (**L4**). Neither reaches the sweep and neither touches a permanent document, but
`worker-3.md`'s acceptance gate does not permit accepting an unresolved Low without a recorded rejection,
and both are one clause. Per `### Deviation 3`'s corollary the apply-changes pass is Worker 1's and returns
the artifact to `planned`.

---

## Review (Worker 3, pass 3) — re-review

**Scope: the delta only.** Pass 2's conclusions on R4's substance stand and were not re-derived — the
citation correction, all four M1 bullets at source, every L1 row, L2's four-site grading, the catalog's
completeness against all five closed artifacts, the byte ledger, and scope discipline. Nothing in this
round's delta undermines any of them.

The delta was established by content, not by reading the file end to end and not by `git status` (the
artifact is untracked, so it has no HEAD baseline): the subsections answering pass-2's findings
(`### L3` `:924-999`, `### L4` `:1001-1021`), the three corrected rot-partition sites (`:206`, `:274`,
`:356`), the two cross-references (`:161`, `:196`), recorded item **8** (`:283`), and the three ledger /
proof rows that close them (`:1059-1066`, `:1077-1078`). Every figure below was measured this pass with my
own instruments under the session scratchpad — `corpus.py` (both corpus rules built independently from
`git ls-files`) and `tokens.py` (occurrence + file counts per token under each rule, `str.count`, both
corpora in one run so the corpus is an explicit parameter rather than an assumption).

### High:

None.

### Medium:

#### M2 — item 8's central identification is false: the two corpora diverge on 14 files, not one, and the file it names does not explain the `DjangoModelType` delta it reports

`:283`, `### Recorded for the maintainer — NOT repaired here` item 8:

> The two readings diverge on exactly **one file**, `docs/builder/DONE/build-046-transport_security-0_0_15.md`

**The sentence is contradicted by its own arithmetic, in the clause immediately before it.** It states the
two corpora as **620** and **606**; 620 − 606 = **14**. I rebuilt both from `git ls-files`:

```
tracked total: 757
excluded by path rule (docs/builder/bld-, docs/builder/build-, docs/review/, docs/dry/): 137  corpus: 620
excluded by base rule (basename bld-/build-, docs/review/, docs/dry/):                    151  corpus: 606
in path-corpus but not base-corpus: 14   (all under docs/builder/DONE/)
in base-corpus but not path-corpus: 0
```

All 14 are `docs/builder/DONE/build-0{01..08,10,12,44,45,46,48}-*.md`. The divergence is a **directory**,
not a file.

**The consequential half is the mis-attribution.** Item 8 reports two divergent figures and then explains
both with one file — "the divergent file's 2 occurrences (`:793`, `:841`) are a closed cycle's archived
build plan". Measured per file, **two** of the 14 carry any swept token, and they are not the same one:

| divergent file | token | occurrences | explains |
|---|---|---|---|
| `docs/builder/DONE/build-046-transport_security-0_0_15.md` | `TODO-BETA-046-0.1.1` (`:793`, `:841`) | 2 | `17 / 6` → `15 / 5` |
| `docs/builder/DONE/build-008-definition_order_independence-0_0_4.md` | `DjangoModelType` (`:362`) | 1 | **`27 / 9` → `26 / 8`** |

The other 12 carry none. So the `DjangoModelType` divergence item 8 itself records is produced by a file
item 8 never names, and a reader following the item's own account — exclude `build-046`, re-measure —
reproduces `15 / 5` and **fails** to reproduce `26 / 8`. Item 8 exists precisely so that a later pass can
re-derive this without re-falling into the trap; as written it hands that pass a partial cause.

**Why Medium.** `BUILD.md` `## Claims are proven mechanically` — "exactly one file" is a **stated count**,
it reads as measured, and every later pass will treat it as measured. It is also the one class this round
was dispatched to guard against, in the round's largest new claim.

**Recommended change — two clauses, no re-measurement, no widening.** The disposition (recorded, not
repaired), the ceiling, `15 / 5`, and Direction 2's `27 / 9` are all untouched by this fix.

1. `:283` — replace "diverge on exactly **one file**, `…build-046…`" with the measured shape: the two
   corpora differ by **14 files, every one under `docs/builder/DONE/`** (which the item's own 620 / 606
   already implies), of which **two carry any swept token** — `build-046-transport_security-0_0_15.md`
   (2 × `TODO-BETA-046-0.1.1`, `:793`, `:841`) and `build-008-definition_order_independence-0_0_4.md`
   (1 × `DjangoModelType`, `:362`) — **and it is the second, not `build-046`, that produces the
   `27 / 9` → `26 / 8` delta.** The durable lesson the item draws (state exclusions by basename, because a
   path prefix silently fails on an archived copy) is strengthened, not weakened, by naming the directory.
2. `:982` — "`docs/builder/DONE/` is **long-tracked**" is false, and it is the provenance clause. The
   directory **did not exist** before `054de9dd`: `git cat-file -t 054de9dd^:docs/builder/DONE` →
   `fatal: … exists on disk, but not in '054de9dd^'`; that commit creates it with **12** files, and
   `973d00b2` (same evening, 22:59, i.e. **after** this cycle's 16:47 pre-flight) brings it to 14. The
   rebuttal of concurrent drift survives on stronger evidence than the false clause: **both**
   token-bearing files were among `054de9dd`'s 12, and the two post-pre-flight additions
   (`build-010-foundation-0_0_4.md`, `build-012-version_release_alignment-0_0_4.md`) carry **none** of the
   swept tokens — so no figure in either direction is drift-affected. That is the sentence the clause was
   reaching for, and it is true.

### Low:

#### L5 — three record-precision residues in this round's own edits; recorded with disposition, not held

Filed so they are fixed in the same pass as M2 rather than becoming a fifth round on their own. **None
blocks acceptance on its own account**, and I am recording that disposition here rather than leaving it to
be inferred.

1. **`### L3`'s "no fifth site" parenthetical cites stale line numbers** (`:948-952`). `:186` is the
   Direction 3 table's `spec-009` row (`18 / 5`), not "15 occurrences / 5 files" — that is `:196`; the
   population listing is `:198-204`, not `:196-203`; `:928` is a **blank line** and `:991` is prose in the
   routing paragraph, not quotations. The four true quotation sites are `:916` and the L3 table's own
   `:935` / `:936` / `:938`, and the catalog bullet it cites as `:308` is now `:310`. The quoted text
   disambiguates every one, and the table's own `:206` / `:274` / `:356` are exact — which is why this is
   Low and not a challenge to the enumeration (see `### What looks solid`).
2. **`### Summary` `:358` reads "alongside a fifth `spec-034` occurrence (`:14`)".** `spec-034` carries
   exactly **4** occurrences (`:14`, `:220`, `:224`, `:307`, re-measured this pass), so on the literal
   reading the phrase asserts a fifth that does not exist; the intended reading is "the fifth **site** in
   this enumeration, a `spec-034` occurrence". `:206` and item 2 both state the count correctly, so the
   record is not internally contradictory — only this phrase is. Suggested: "alongside a fifth site,
   `spec-034:14`".
3. **`:196` carries a doubled em dash** (`… item 8) — — and the 2026-07-30 renumber …`), an artefact of the
   cross-reference insertion. Cosmetic.

### DRY findings

None. This round added no abstraction, no helper, and no duplicated instrument; item 8's cross-references
at `:161` / `:196` are the DRY-correct shape — one statement of the caveat in the recording block, pointed
at from both figures, rather than the caveat restated at each. The heading they name resolves **exactly
once** in the artifact (`grep -c '^### Recorded for the maintainer — NOT repaired here$'` → `1`).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. No `__all__` or re-export change. R4
writes no source at all.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

The two permanent documents R4 owns were **not reopened** by this round, proved by content rather than by
`git status` or mtime: `60,361 bytes / 829 lines` (rationale) and `54,785 / 962` (`spec-054`), byte-identical
to the `### Byte and line counts` table's post-edit row; `git diff --numstat` still `621 0` and `10 7`;
newest commits still `f3c94642` and `947f7494`; both ` M` and unstaged. `spec-034` — this round's subject —
is **clean**, newest commit `ff65666d`. `docs/builder/DONE/build-046-…` and `build-008-…` were read only and
are clean. No KANBAN, glossary, DB, or archive surface was touched.

### What looks solid

**Item 8's central claim is CONFIRMED, and independently sharpened against my own prior work.** Every
figure it states reproduces exactly under my own two-rule instrument:

| token | path rule (620) | basename rule (606) |
|---|---|---|
| `TODO-BETA-046-0.1.1` | **17 / 6** | **15 / 5** |
| `DjangoModelType` | **27 / 9** | **26 / 8** |
| `DjangoModelField`, `OptimizerStore`, `with_hints`, `with_prefix`, `get_strawberry_annotations`, `ASC_DISTINCT`, `DESC_DISTINCT`, `Advanced{Filter,Order,Aggregate}Set`, `DISTINCT ON`, `item 38` | identical | identical |

I measured **all 14 distinct tokens** the two sweeps use, not the 11 rows: **exactly two differ**, so
"9 of 11 identical either way" holds under any grouping of the rows. `757` / `137` / `620` / `606` all
reproduce. `15 / 5` **is** right on the merits — `build-046`'s two occurrences are a closed cycle's
archived build plan discussing this very renumber cluster, per-cycle scratch under `START.md` "Temp
artifact conventions".

And the conclusion the round was told to distrust is **true of my own passes**: pass 1 (`:565-568`) states
the corpus as "757 tracked, 137 under `docs/builder/bld-` / `docs/builder/build-` / `docs/review/` /
`docs/dry/`, **620 permanent**" and in the **same sentence** reports the population as "**15 occurrences /
5 files**" — a combination I have now shown is impossible, since rule A over 620 files yields 17 / 6. Pass 2
(`:1317-1323`) rebuilt the same 620-file rule-A corpus and reproduced `DjangoModelType` **27 / 9** exactly.
So both of my re-derivations did match whichever rule the direction under review had used, neither noticed,
and the mismatch sat inside a single sentence of my own record. Two independent agreeing measurements did
not catch it; only running one population under both readings did. That is exactly what item 8 says, and it
is the most valuable thing in this round.

**Provenance holds.** `docs/builder/DONE/build-046-transport_security-0_0_15.md`: added at `054de9dd`
(2026-08-15 16:47, this cycle's pre-flight HEAD), the **only** commit touching it, clean, and untouched by
the later `973d00b2` — verified with `git log --diff-filter=A` and `git log --format` over the path, never
`git status` alone and never mtime. So its occurrences sat in the rule-A corpus from the first sweep.

**`15 / 5` did not move and the two directions were not reconciled** — both bars held. `:196` still reads
"**15 occurrences / 5 files**", `:206` still closes "the population is still 15 / 5", `### Direction 2`'s
table still records `DjangoModelType` **27 / 9** at `:170`, and neither direction was re-run. The only
additions are the caveat at `:161`, the cross-reference at `:196`, and item 8 itself.

**L3's third site was correctly in scope, and the population is exhausted.** `:274`'s opening sentence did
assert for all four citations ("naming card 046 as the live FieldSet owner") what its own sub-bullet at
`:276` denies for `:14`; correcting it is right, and my pass-2 "adjacent and self-limiting" was the weaker
call. I enumerated rather than grep-counted: over Worker 1's writable ranges (`1-371`, `744-1135`), every
line matching `genuine rot|genuine stale|not rot|rot site|4 of them|4 sites|4 stale|5 genuine|edit-owed` or
`spec-034` is one of — corrected (`:206`, `:274`+`:276`, `:358`), already split (`:310`, `:871`, `:901`,
`:918`, `:1030`, `:1126`), an occurrence count that must not move (`:196`, `:199-204`, `:874`), the sweep
regex itself (`:931`), a quotation of pre-fix wording (`:916`, `:935`, `:936`, `:938`), or partition
arithmetic (`:955-958`). **No fifth undifferentiated site.** The two remaining hits (`:455`, `:578`) are in
my own pass-1 review section and correctly off-limits to Worker 1.

**The "deliberate verbatim quotation" sites are genuine quotations, not uncorrected instances** — the
substance of the claim holds even though its line numbers do not (L5.1). `:916` quotes the catalog bullet's
pre-fix wording ("plus (new, R4) `spec-034`'s 4 stale `TODO-BETA-046-0.1.1` citations") and the live bullet
at `:310` now carries the split inline; the L3 table's `:935` / `:936` / `:938` quote the pre-fix wording of
`:206` / `:274` / `:356`, and all three live sites are corrected. Editing any of them would destroy the
evidence of what was fixed. Confirmed by opening each live target, not by trusting the table.

**The partition re-derives from the tree.** `TODO-BETA-046-0.1.1` = 15 occurrences / 5 files:
`apps/products/schema.py` 7, `spec-034` 4 (`:14`, `:220`, `:224`, `:307`, re-grepped at source),
`tests/test_build_tree_md.py` 2, `types/definition.py` 1, `spec-054` 1 → **7 carded + 3 not rot + 1 correct
as written + 4 edit-owed rot = 15**, files 5. No occurrence count moved.

**L4's weaker statement is true.** The counter-example set is real and is in the catalog: `spec-028:1159` /
`:1166` (`:315`, "Left verbatim … a worse defect"), `orders/inputs.py`'s residual sites (`:319`, "neither
false today"), `spec-009:592-597` (`:321`, "Not false"), and the `:654` / `:649` / `:930` trio (`:323`,
"recorded so a later pass does not re-open them as new") — four groups carrying the same
non-finding / decided-non-edit grade as the four M1 bullets now at `:324-:327`. The predicate is satisfied
by the included set and the omitted set alike, so it does not discriminate, and my pass-2 hypothesis fails
on its own evidence. The source-artifact hypothesis fails too and the catalog's own attributions confirm the
count: `bld-009-r2` supplied 2 of the 4 included groups (`:315`, `:319`) and, per `:1032`, 3 of the 4
omissions. Replacing a false diagnosis with a method (exhaustive enumerate-and-match) rather than a third
guess is the right shape, and it is the shape that closed M1.

**Ledger and integrity.** Every row of `### Byte and line delta` closes: +3,393/+5, +17,393/+178,
+10,413/+83, +21,656/+296, +15,678/+124, +4,775/+11; total +73,308; final row **146,651 bytes / 1,428
lines**, which is `wc -c -l` on disk. The one row that describes my work is exact: lines `1136-1428` measure
21,650 bytes / 293 lines, and with the `---` separator and its two blank lines that is **21,656 / 296**;
pass 1 (`372-743`) is **27,044**, so the stated 48,700 for my two sections is exact, not rounded. `Status:`
read exactly `planned` at dispatch. The artifact is untracked (`??`), so nothing was committed; HEAD is
`1abba7a4`, unmoved since my pass-2 review recorded it. Only two paths were written this round — this
artifact and `docs/builder/worker-memory/spec-009-worker-1.md`.

### Temp test verification

- Instruments live outside the repo, in the session scratchpad: `corpus.py` (both corpus rules built
  independently from `git ls-files`, with the symmetric difference printed) and `tokens.py` (per-token
  occurrences and files under both rules in one run, plus a per-file breakdown of the 14 divergent files).
- No temp test under `docs/builder/temp-tests/` was needed: the item under review is a Markdown record and
  every claim in it is a measurement over tracked files.
- Disposition: deleted with the session; nothing to promote. No source file was opened for writing, so the
  failability carve-out was not exercised.
- `### Failability proofs` / `### Hot-path budget` remain genuinely inapplicable and I audited that rather
  than assuming it: this round's delta adds **0 executable lines** — no `.py`, no test, no boundary, guard,
  gate, or rejection path — so the boundary set is empty by enumeration and the re-run floor is met by an
  empty set legally.

### Notes for Worker 1 (spec reconciliation)

- **No spec edit is owed and no spec finding was raised.** M2 and L5 are corrections inside this per-cycle
  artifact — no permanent document, no source, no test, no widening. `### Maintainer decision 8`'s
  two-clause ceiling is untouched and is not approached: M2's fix records a measurement more precisely and
  repairs nothing, which is the same footing on which Worker 0 authorized item 8 into the recording block.
- **The final gate now has THREE R4 finds to fold into `bld-009-final.md`'s `### Deferred work catalog`**,
  not two: `KANBAN.md:336`, `spec-034`'s four `TODO-BETA-046-0.1.1` citations with their 3 + 1 split, and
  **item 8's corpus-rule imprecision** — whose durable half is "state corpus exclusions by basename". The
  artifact's own catalog block stays correctly scoped to the five *closed* artifacts.
- **Carry the corrected corpus statement, not the file name.** If any later pass re-runs either sweep, the
  parameter it must fix first is the corpus rule; `docs/builder/DONE/` grew by two files *during this cycle*
  (`973d00b2`), both token-free today, so the corpus is demonstrably not stable across a cycle.
- **Re-derive HEAD at the gate.** `1abba7a4` as of this review; it has moved four times across this
  artifact's life and the `### Non-sweep proof` blocks are accurate as written — only the hashes age.
- Not escalated, stated for the record: no contract-level question, no existence challenge with a target,
  nothing requiring spec context. This review is closable by the two M2 clauses plus three optional L5
  clauses.

### Review outcome

`revision-needed`.

Everything the dispatch put in doubt about this round came back **confirmed except one clause**: all four of
item 8's figures reproduce exactly, its 9-of-11 invariance holds when measured across all 14 tokens, its
provenance check is right, `15 / 5` did not move, the two directions were not reconciled, L3's third site
was correctly in scope, the population is exhausted with no fifth site, the four quotation sites are genuine
quotations, L4's weaker statement is true and its counter-example set is real, the ledger closes to the byte
against disk, and scope held to two written paths proved by content. Item 8's **central claim — that two
independent agreeing measurements failed to catch a corpus-rule mismatch — is true**, and it is true of my
own two passes in a way my pass-1 record shows inside a single sentence.

What blocks acceptance is that the same item's identification of *where* the corpora diverge is false, is
contradicted by its own 620 / 606 arithmetic, and mis-attributes the `DjangoModelType` delta to a file that
does not contain the token — leaving a reader who follows it unable to reproduce half of what the item
reports (**M2**, Medium). That is this round's characteristic failure mode landing, once again, inside the
correction written to close it. `worker-3.md`'s acceptance gate does not permit accepting an unresolved
Medium without a recorded rejection, and the fix is two clauses that make the record strictly stronger
without moving a figure or widening a scope. Per `### Deviation 3`'s corollary the apply-changes pass is
Worker 1's and returns the artifact to `planned`.

---

## Review (Worker 3, pass 4) — re-review

**Scope: the delta since `## Review (Worker 3, pass 3)` landed.** Nothing my passes 1-3 confirmed was
re-derived. The delta, established by content (the artifact is untracked, so there is no HEAD baseline):
`### M2 + L5` (`:1026-1090`), the rewritten item 8 (`:283`), its source clause in `### L3` (`:948-955`), the
`### Summary` correction (`:358`), the `### Direction 3` cross-reference, the new `### New findings` bullet
(`:1098`), and two ledger rows (`:1131-1132`, `:1139`). All 82 added lines sit above my pass-3 section,
which shifted intact from `1428→1694` to `1514→1776`.

### High:

None.

### Medium:

None.

### Low:

#### L6 — the new 14-token clause brackets its correct counts with a false description of the table

`:283` (item 8) and `:1070` (`### M2 + L5`), identical wording:

> `### Direction 2`'s table is 10 rows covering 13 tokens (**three rows carry two or three tokens each**)

The table carries **two** such rows, not three — `` `ASC_DISTINCT` / `DESC_DISTINCT` `` (2 tokens, `:171`)
and `` `AdvancedFilterSet` / `AdvancedOrderSet` / `AdvancedAggregateSet` `` (3 tokens, `:172`). The other
eight rows (`:165-170`, `:173`, `:174`) carry one token each: 8 + 2 + 3 = **13**.

**Why this is Low and non-blocking, stated rather than left to be inferred.** It is the one class of clause
this round was dispatched to hunt, so it is filed — but it moves nothing. Both figures it brackets are
correct and independently countable from the table itself (10 rows, 13 tokens), the token population of 14
is right, and 12-of-14 is right. It does not even self-contradict arithmetically: 7 single-token rows plus
three 2-token rows would also give 10 / 13, so a reader cannot catch it from the sentence — only from the
table, where it is immediate.

**Its cause is worth more than the clause, and it is diagnosable.** The description is exactly one revision
stale: **before this artifact's own L1 fix** the table had `with_hints` / `with_prefix` as one combined row —
9 rows, three multi-token rows (2 + 2 + 3), 13 tokens. L1 split that row (`### L1`, "Two rows rather than one
combined `4 / 2`"), which moved the table to 10 rows / two multi-token rows and left the prose describing the
pre-split shape. So this is not a fourth invented count; it is a description that stopped tracking a table
the same artifact corrected two rounds earlier — the same "the fix moved the thing the prose describes"
shape as L5's stale `:NN` refs, and answered the same way: **describe by content, not by shape**.

**Disposition — recorded, not held.** Fix opportunistically at both sites if any pass reopens item 8
("two rows carry two and three tokens respectively", or simply drop the parenthetical, since 10 rows /
13 tokens is checkable without it). I am recording the rejection reason here so the finding is closed
rather than unresolved: no figure moves, no conclusion changes, and a fifth round to delete four words
would cost more than the words.

### DRY findings

None. The round added no instrument, no abstraction, and no restated figure; the L5(a) fix **removed** a
duplication class rather than adding one, by replacing four line-number pointers with content anchors that
cannot go stale as the file grows.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. No `__all__` or re-export change; R4
writes no source.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`.

### Documentation / release sanity

No permanent surface was touched. Proved by content, not `git status` or mtime: the two documents R4 owns
are byte-identical to their post-edit state (`60,361 / 829` and `54,785 / 962`), `git diff --numstat` still
`621 0` and `10 7`. `docs/SPECS/spec-034-permissions-0_0_10.md` and `docs/builder/DONE/` — both this round's
subjects — are **clean**. No KANBAN, glossary, DB, or archive surface involved.

### What looks solid

**The 14-token claim is right, and it is the one thing this round newly measured.** Counted from the table's
own first column: 10 rows, 13 distinct tokens, plus Direction 3's `TODO-BETA-046-0.1.1` = **14**. The three
tokens item 8's earlier "eleven" silently dropped are the `Advanced*` triple, and they are invariant under
both corpus rules — **`AdvancedFilterSet` 18 / 7, `AdvancedOrderSet` 30 / 6, `AdvancedAggregateSet` 13 / 7**,
matching Worker 1's figures exactly and matching the 14-token sweep I ran in pass 3, where exactly two of the
14 differed. So **12 of 14** is correct, the two that differ are the same two, and no figure moves — the
denominator was understated and nothing else. Worker 1 found this itself, in the clause I passed over: my
pass 3 measured all 14 tokens and reported "9 of 11 holds under any grouping" instead of noticing that the
stated population was wrong. That is the same defect I graded as L1 two rounds ago — a table's row count is
not its token count, exactly as occurrences are not files — and I reproduced it as a reader.

**M2's rewrite is accurate on every checkable clause.** Re-derived at this pass: `A − B = 14`, `B − A = 0`,
all 14 under `docs/builder/DONE/`; exactly two carry a swept token and they are different files explaining
different deltas (`build-046…:793`, `:841` → `17 / 6` → `15 / 5`; `build-008-definition_order_independence-0_0_4.md:362`
→ `27 / 9` → `26 / 8`); the other 12 carry none.

**The replacement provenance argument — exposure, not age — holds.** `docs/builder/DONE/` is absent from
`054de9dd^`; `054de9dd` creates it with 12 files; `973d00b2` (22:59, after the 16:47 pre-flight) brings it to
14 with `build-010-foundation-0_0_4.md` and `build-012-version_release_alignment-0_0_4.md`. I checked the
load-bearing half rather than accepting it: **both token-bearing files are in `054de9dd`'s original 12**
(`git ls-tree 054de9dd:docs/builder/DONE` lists `build-008` and `build-046`), and both later additions carry
**zero** of the 14 tokens. So no figure was ever exposed to the post-pre-flight change. This is a stronger
argument than the false age claim it replaces, and it survives the fact — which it now states — that the
corpus moved mid-cycle.

**Every bar held.** `:196` still reads "**15 occurrences / 5 files**"; `:206` still closes "the population is
still 15 / 5"; `### Direction 2`'s table still records `DjangoModelType` **27 / 9** at `:170`; neither sweep
was re-run and the two directions are not reconciled; item 8 still closes **recorded, not repaired**, naming
the re-run it does not authorize; `### Maintainer decision 8`'s ceiling is untouched.

**L5's three fixes are correct, including the deliberate non-edit.** (a) The "no fifth site" parenthetical
now cites by content anchor rather than line — the right fix rather than a renumber, since the numbers moved
again this very round; the three classes and the enumeration are unchanged, so my pass-3 finding that the
population is exhausted still stands on the same evidence. (b) `:358` now reads "a fifth **site** in that
enumeration, `spec-034:14`", which removes the only reading on which it asserted a fifth occurrence of a
4-occurrence token. (c) Leaving the doubled em dash inside my own L5 write-up is the **right call on two
independent grounds**: `bld-009-r2`'s `spec-028:41` precedent (editing a quotation to remove the defect it
quotes desyncs it from what it quotes), and the plain fact that a Worker 3 section is not Worker 1's to edit.
`grep -- '— —'` now returns exactly one hit, and it is that quotation.

**The ledger reconciliation is exact.** My pass-3 section measures **19,291 bytes / 266 lines** from its
`---` separator to EOF (19,285 / 263 from the heading), and the `Status: planned` → `revision-needed`
transition I wrote adds **8** bytes — `19,291 + 8 = 19,299 = 165,950 − 146,651`. Worker 1 reconciled a real
8-byte discrepancy instead of leaving it, and it is the first round where the reviewer's footprint was
checked in both directions rather than assumed. Every other row closes: `+10,584 / +82` for this round
against `165,950 / 1,694`; total `+103,191`; `27,044 + 21,656 + 19,291 = 67,991` for my three sections; final
row **176,534 / 1,776**, which is `wc -c -l` on disk.

**Scope and integrity.** `Status:` read exactly `planned` at dispatch. The artifact is untracked, so nothing
was committed; HEAD is `1abba7a4`, unmoved since my pass-2 review recorded it. The artifact and
`docs/builder/worker-memory/spec-009-worker-1.md` are the only paths written — every other file in this
cycle's writable set is byte-identical or clean, checked individually.

### Temp test verification

No new instrument was needed: pass 3's two scratch programs (both corpora built from `git ls-files` in one
run; per-token occurrences and files under each rule, with the per-file breakdown of the 14 divergent files)
already carried every measurement this round's claims required, and the only new question — the table's row
and token counts — is answered by counting the table. Nothing under `docs/builder/temp-tests/`; nothing to
promote; no source file opened, so the failability carve-out was not exercised. `### Failability proofs` and
`### Hot-path budget` remain inapplicable by enumeration: this round's delta adds **0** executable lines and
introduces no boundary, guard, gate, or rejection path, so the re-run floor is met by an empty set legally.

### Notes for Worker 1 (spec reconciliation)

- **No spec edit is owed and no spec finding was raised.** L6 is four words inside this per-cycle artifact;
  no permanent document, source, or test is implicated, and `### Maintainer decision 8`'s two-clause ceiling
  is neither touched nor approached.
- **The final gate still has three R4 finds to fold into `bld-009-final.md`'s `### Deferred work catalog`** —
  `KANBAN.md:336`, `spec-034`'s four `TODO-BETA-046-0.1.1` citations with their 3 + 1 split, and item 8,
  whose durable half is "state corpus exclusions by **basename**". Item 8's content is now correct; carry it
  as it reads, minus L6's parenthetical if the gate quotes that sentence.
- **Re-derive HEAD at the gate.** `1abba7a4` as of this review.
- Not escalated, and stated for the record: no contract-level question, no existence challenge with a target,
  nothing needing spec context.

### Review outcome

`review-accepted`.

Every claim this round put on the table came back verified. The 14-token correction is right on its own
terms and right about my pass 3, which measured all fourteen and still repeated the artifact's understated
denominator — Worker 1 found a defect in a clause the reviewer had read past, which is the division of
labour working rather than failing. M2's two clauses are rewritten accurately, and the provenance argument
that replaced the false one is stronger than what it replaced: it rests on **exposure** — both token-bearing
files in `054de9dd`'s original 12, both later additions token-free — rather than on the directory's age,
which was the part that was false. L5's three fixes are correct, and the one instance deliberately left is
left for the right reason. Every bar held: `15 / 5` unmoved, `27 / 9` unmoved, the directions unreconciled,
the disposition and the ceiling untouched, no permanent surface reopened, nothing committed.

The single open item is **L6**, four false words describing a table whose two figures either side of them are
correct and countable in place — recorded above with its rejection reason and its cause (a description left
behind by this artifact's own L1 split), and not a reason to spend a fifth round. R4's record is now
internally consistent everywhere I can measure it, and it is ready for Worker 1's final verification.
