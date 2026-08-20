# Build: Cross-slice integration pass — orders / 0.0.8 (028)

Spec reference: `docs/SPECS/spec-028-orders-0_0_8.md` (1,162 lines / 247,470 bytes) plus its rationale companion `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md` (697 lines / 131,529 bytes). Read-only this pass.
Status: final-accepted

## Plan (Worker 1)

### Worker-1-only artifact shape

The integration pass is Worker 1's alone ([`BUILD.md`][build] `## Cross-slice integration pass`), so this artifact carries `## Plan (Worker 1)` and `## Final verification (Worker 1)` with no `## Build report` / `## Review` between them — the shape Slices 1 and 3 used, authorized by the build plan's `Ownership partition: none; sequential slices` line. Every box in `### Dispatched findings checklist` is ticked by the same worker that audits it, so each tick names its measurement rather than resting on a builder's report.

### What this pass is, in one paragraph

Three slices closed `final-accepted`. Slice 1 moved 64KB of deliberative layer out of the spec; Slice 2 retired twelve classes of unresolvable citation across sixteen `.py` files over three build passes and three review passes; Slice 3 landed 101 count-asserted replacements so the spec states the shipped contract. **Not one executable statement changed anywhere in the cycle.** This pass runs `BUILD.md`'s six preconditions, the cross-slice DRY/naming/export/story checks, and the one question no slice could answer from its own side: whether the `spec-028`-family citations Slice 2 wrote against the *old* spec still resolve against the *rewritten* one.

### Diff-reading state, re-measured rather than inherited

The concurrent `spec-027` residual cycle has fully committed. HEAD is `5447c9eb`; the relevant commits are `8a9840dc`, `8bab7ea8`, `5447c9eb`. **The dispatch brief's file split is wrong in three ways and the corrected split is below**, because a later pass reading it would look for Slice 2's work in the wrong place.

`git diff --name-only 5c6fdd71 HEAD` over the sixteen returns **11 paths, not 8 or 9**; `git diff HEAD --name-only` over the sixteen returns **7**; and **two paths are in BOTH lists**, which the brief's two-column split cannot express.

| Disposition | Count | Paths |
| --- | --- | --- |
| **Committed only** (`git diff HEAD` is empty; read at HEAD or via `git diff 5c6fdd71 HEAD`) | 9 | `orders/sets.py`, `orders/factories.py`, `orders/__init__.py`, `utils/inputs.py`, `tests/types/test_base.py`, `tests/orders/test_sets.py`, `tests/orders/test_factories.py`, `tests/orders/test_base.py`, `tests/orders/test_composition.py` |
| **Dirty only** (`git diff HEAD -- <path>` carries all of this cycle's work) | 5 | `types/base.py`, `orders/base.py`, `orders/inputs.py`, `tests/orders/test_inputs.py`, `examples/fakeshop/apps/library/orders.py` |
| **MIXED — part committed, part dirty** | 2 | `tests/test_registry.py`, `examples/fakeshop/test_query/test_library_api.py` |

**The mixed pair proved, not asserted.** `tests/test_registry.py` carries 28+/18- in `5c6fdd71..HEAD` **and** 16+/11- still dirty; its pass-3 L4 wording is absent at HEAD (`git show HEAD:… | grep -c 'imports neither poisoned name'` -> **0**) and present in the working tree (-> **1**). `test_library_api.py` carries 27+/29- in the range **and** 3 insertions still dirty; its C5 banner including both post-ship test names **is** committed (-> **1** at HEAD) while step 19's three trailing comment lines are not. So **for those two paths neither reading alone shows Slice 2's work**, and a pass that picks one will under-read the slice. The brief also states "swept 8" and then lists 9 — its own count disagrees with its own list by one.

Never `git diff -- <path>` (a concurrent `git add` makes it read clean). No `git stash` / `checkout` / `restore` / `worktree` anywhere in this pass; every pristine reference came read-only from `git show` into a scratch path outside the repository. For every present-state claim below the instrument is **the current file**.

### Required reading walked

`AGENTS.md`, `START.md`, [`BUILD.md`][build], [`ARTIFACT.md`][artifact], [`worker-1.md`][worker-1], `GOAL.md`, `CHANGELOG.md`, the active spec, the rationale companion, [`build-028-orders-0_0_8.md`][build-028], and all three slice artifacts in slice order (`bld-slice-1-028` 255 lines, `bld-slice-2-028` 3,430 lines across three build passes / three review passes / two final verifications, `bld-slice-3-028` 441 lines). `docs/GLOSSARY.md`: read the status legend, the public-export list, the full alphabetical Index, the browse-by-category block, and the five Ordering-family entries end to end; the remaining ~120 entries were scanned by heading rather than read line by line, and that is stated rather than implied. Own memory file `docs/builder/worker-memory/worker-1-028.md` read first (four prior entries, 39 lines). No other worker's memory file was opened.

### Boundary count, hot path, floor verification

**Zero boundaries, and this pass adds none** — it writes two Markdown files. **No failability proof is owed, by entitlement rather than omission**: a boundary is an executable expression, and the cycle's executable token stream is identical to two reference points across all sixteen paths (re-derived below, 64 readings, 0 mismatches). No fail-open shape can have landed for the same structural reason. **Hot path: none declared, none owed.** **Floor-verification scope: `none`**; no floor venv was built and the shared `.venv` was not mutated or read for a version claim. (Reference only, from [`BUILD.md`][build] `## Floor verification`: Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0.)

### Spec status-line re-verification (every Worker 1 spawn)

Spec lines 1-8 read as a shipped-state record and **nothing this pass measured falsifies them.** The two claims a moving file could have rotted were both checked at HEAD: the `Status:` line's assertion that `CHANGELOG.md` carries the subsystem's Added and Changed bullets *in the `0.0.8` release section* is true — `## [0.0.8] - 2026-06-03` carries the "Ordering subsystem" Added bullet and the `Meta.orderset_class` promotion Changed bullet, and `grep '^## ' CHANGELOG.md` shows **no `[Unreleased]` heading**; and the Status line's `docs/GLOSSARY.md` claim is true — the Index reads `shipped (0.0.8)` for all five Ordering symbols. The rationale-companion pointer resolves on disk. **No spec edit this pass**, and none owed.

### Dispatched findings checklist

The spec's own `## Slice checklist` describes the six slices of the original card, all shipped and ticked, so [`BUILD.md`][build] `### Dispatched findings checklist` gives the substitute shape: one box per obligation this pass was dispatched with — the six preconditions, the cross-slice check list, the cross-cycle citation question, and the deferred-work consolidation.

- [x] **P1** — every prior `bld-slice-*-028*.md` artifact read in slice order, in full. No "as needed".
- [x] **P2** — `scripts/review_inspect.py` coverage confirmed for every `.py` file the build touched, and the vacuity of the obligation recorded explicitly rather than assumed.
- [x] **P3** — `Repeated string literals` compared across every shadow overview, on the full population rather than the truncated section.
- [x] **P4** — `Imports` compared across every shadow overview; one-way dependency direction confirmed and the two runtime-vs-`TYPE_CHECKING` edges read at source.
- [x] **P5** — every accepted slice artifact's `What looks solid` and `DRY findings` walked for deferred follow-up that belongs in this pass rather than the catalog.
- [x] **P6** — staged-anchor sweep run in the card-id form as well as the `TODO(spec-028` form, tree-wide, and Worker 0's reading confirmed **and corrected**.
- [x] **X1** — every `spec-028`-family citation in `.py` resolved against the **rewritten** spec, on three provably-different instruments.
- [x] **X2** — duplicated helpers, inconsistent naming / error handling, repeated ORM/queryset patterns, misplaced responsibilities, and missing / too-broad exports checked across the three slices.
- [x] **X3** — the one-coherent-story question answered with measurements rather than impressions, and the one place the answer is **no** named with its two sites.
- [x] **X4** — the ~25 routed deferred-work items walked for transcribability; five flagged as not yet actionable without re-derivation.
- [x] **X5** — the zero-executable-change entitlement re-derived independently against the new HEAD, since both concurrent commits landed after Slice 2's last proof.

---

## Final verification (Worker 1)

### Summary

`Status: revision-needed`, for **one** reason, stated up front so it is not buried: **Slice 2 closed 16 of 18 in-family bare-`Decision N` citations in `tests/orders/test_inputs.py`'s own class and left 2, and neither is anaphora.** That is the partial claim fix this cycle exists to close, arriving one spelling over from C12. It is two docstring/comment tokens, it changes no executable statement, and it therefore costs the zero-boundary entitlement nothing — the trade-off that deferred the DRY existence challenge does not apply here.

Everything else holds. No duplicated helper, no inconsistent error handling, no repeated ORM/queryset pattern, no misplaced responsibility, no missing or too-broad export, and **no cross-file repeated literal that is a consolidation candidate** — all 56 are field names, `Meta` keys, wire aliases, or fixture values, and none is new. Every one of the 106 `spec-028`-family citations in `.py` resolves against the rewritten spec. The entitlement holds on two instruments against two baselines across all sixteen paths.

Three record defects are corrected here rather than routed: the brief's committed/dirty split (above), Slice 3's `## Test plan` protect-list population (below), and two catalog items whose populations have moved.

### Precondition 1 — every slice artifact read in slice order

Read in full, in order: `bld-slice-1-028-rationale_extraction.md` (255 lines), `bld-slice-2-028-citation_and_provenance_rot.md` (3,430 lines — plan, three build passes, three review passes, two final verifications, 15 rulings, 22 checklist boxes), `bld-slice-3-028-spec_reconciliation.md` (441 lines). No section skipped.

### Precondition 2 — `review_inspect.py` coverage: the obligation is VACUOUS, and that is the finding

[`BUILD.md`][build] step 2 asks for a run or a recorded skip "for every Python file with **review-worthy logic** the build touched." **This cycle touched zero review-worthy logic.** The executable token stream of all sixteen paths is identical to both `HEAD` and `5c6fdd71` on two independent instruments, so the qualifying population is **empty** and the obligation is discharged by construction, not by sampling. A reader who finds one overview where sixteen files were edited is looking at an entitlement.

Recorded explicitly because the two readings are indistinguishable from the artifact alone:

| Pass | Files in that pass | Helper disposition |
| --- | --- | --- |
| Slice 2, pass 1 | 8 | **1 run** (`types/base.py`, exit 0, 18,542-byte overview) + 7 skips with reasons |
| Slice 2, pass 2 | 13 | pass-level skip, recorded with its trigger reasoning (no file under `types/` or `optimizer/`, no new file, zero logic lines) |
| Slice 2, pass 3 | 4 | skip, all four paths enumerated by name |
| Slices 1 and 3 | 0 `.py` | skip recorded; Markdown only |

The union of the three passes' file sets **is** the sixteen — verified path by path — so every one of the sixteen carries a run or a recorded skip. **One gap in the record, not in the work:** pass 2's skip is stated at *trigger* granularity ("no file under `types/` or `optimizer/`") and never enumerates its 13 paths, so a reader looking for the per-file disposition of e.g. `orders/sets.py` must infer it. Passes 1 and 3 enumerate; pass 2 does not. Noted, not a finding — the trigger reasoning is sound and the population is empty either way.

**This pass generated the missing overviews rather than reason about them**, because preconditions 3 and 4 cannot be performed without them: `review_inspect.py --output-dir docs/shadow` was run for all sixteen paths (exit 0 each). `docs/shadow/` is gitignored regenerable scratch that [`BUILD.md`][build] directs workers to write; only stems belonging to the sixteen were written, so no stem owned by the concurrent cohort (`types/finalizer.py`, `filters/*`) was overwritten.

### Precondition 3 — `Repeated string literals` across every shadow overview

**The shadow section is a truncated instrument and I did not accept its population.** Two of the sixteen overviews end their list with `... (28 more not shown)` and `... (226 more not shown)`. Compared as emitted, 17 literals appear in two or more of the sixteen. Recomputed from the AST over the **full** population — every `Constant` string node with module / class / function docstrings removed, i.e. executable literals only, which is what [`BUILD.md`][build] defines the signal as — the answer is **56**. The truncated section hid 39 of them, and reporting 17 would have been the cycle's recurring defect in its purest form.

**Result: no cross-slice DRY candidate.** Every one of the 56 falls into four classes, and each class is the correct shape rather than a duplication:

- **Model field names** (`'name'` 258x / 9 files, `'title'` 179x / 7, `'code'` 109x / 5, `'subtitle'`, `'shelf'`, `'shelves'`, `'loans'`, `'id'`): the wire and ORM contract itself. A constant cannot name a column better than the column's name.
- **`Meta` key names** (`'orderset_class'`, `'filterset_class'`, `'fields'`, `'exclude'`, `'model'`, `'interfaces'`, `'connection'`, `'relation_shapes'`, `'nullable_overrides'`, `'required_overrides'`, `'cursor_field'`, `'globalid_strategy'`, `'total_count'`, `'filesystem_path_fields'`): production file plus the test asserting on that key. The pairing is the intended shape — a test that imported the key name instead of writing it could not catch a rename.
- **Wire aliases and fixture values** (`'shelf__code'`, `'shelfCode'`, `'ASC'`, `'Alpha'`, `'Beta'`, `'category'`, `'properties'`, `'items'`, `'status'`).
- **Dunders and single characters** (`'__all__'`, `'__annotations__'`, `'__strawberry_definition__'`, `'a'`, `'b'`, `'x'`, `''`, `' '`, `'.'`, `': '`, `'_'`).

Two were examined as the only ones with a genuine argument, and both are **verified-and-rejected**: `'ORDER_PERMISSION_DENIED'` (2x raised in `examples/fakeshop/apps/library/orders.py`, 2x asserted in `test_library_api.py`) is an error-code *wire contract* — importing the constant into the assertion would make the test tautological, which is why the literal is right on both sides; and `'shelf__code'` / `'shelfCode'` (11x and 5x across three files) are the flat-shorthand path and its camelCase alias, i.e. exactly the thing under test.

**And none of the 56 is new.** The population is a property of the executable token stream, which is byte-identical to both baselines, so every literal here predates the cycle. This build introduced no repeated literal at all.

### Precondition 4 — `Imports` across every shadow overview

**One-way dependency direction holds, and the two edges that could have broken it were read at source rather than inferred from the overview.**

The runtime graph under `django_strawberry_framework/` across the touched files:

```
types/base.py ──(in-function only)──> orders/sets.py
orders/sets.py ──> orders/base.py, orders/inputs.py, sets_mixins, utils/{inputs,querysets,relations,strings}, exceptions
orders/factories.py ──> orders/{inputs,sets}, utils/inputs
orders/__init__.py ──> orders/{base,inputs,sets}, registry, utils/inputs
orders/base.py ──> sets_mixins            (one local import, nothing else)
orders/inputs.py ──> registry, utils/{input_values,inputs,strings}
utils/inputs.py ──> exceptions, utils/{imports,strings}     (NOTHING from orders/ or filters/)
```

Three confirmations that matter:

- **The shared substrate does not import either family.** `utils/inputs.py`'s local imports are `..exceptions`, `.imports`, `.strings` — no `orders`, no `filters`. The D5 relocation moved mechanics *down* without creating an upward edge.
- **`orders/inputs.py` -> `.sets` is `TYPE_CHECKING`-only** (read at `orders/inputs.py:50-52`, under `if TYPE_CHECKING:  # pragma: no cover`), while `orders/sets.py` -> `.inputs` is a real runtime import. So the apparent `sets` <-> `inputs` cycle the overview shows is **not** one at runtime; the direction is `sets -> inputs -> utils`. An overview-only reading would have flagged a cycle that does not exist.
- **`types/base.py` -> `orders/sets.py` is in-function only**, at `types/base.py:207` inside `_validate_orderset_class`, carrying the comment `In-function import: dodges the types -> orders -> types module-load cycle. Do NOT hoist to module top.` That is DoD item 9's contract and C1's own repaired site: the invariant is stated with **no citation at all**, which is the durable form C1 chose, and the sibling `_validate_filterset_class` states the same invariant the same way. Symmetric across both families.

**Siblings importing from outside the documented boundary — three, all intended, each verified:** `tests/orders/test_base.py` reaches into `django_strawberry_framework.types.base._validate_orderset_class` (DoD 9 pins that validator, so the order test tree is its correct home); `tests/orders/test_composition.py` imports both `filters` and `orders` plus `sets_mixins.LazyRelatedClassMixin` (it *is* the cross-family composition test, spec Slice 6); `tests/orders/test_sets.py` imports `utils.inputs.promote_set_meta_fields` / `read_set_meta_fields` (the D5 relocation put them there, and C10/C11's restated citations name exactly those symbols). No unintended boundary crossing.

**No missing or too-broad export.** `git diff HEAD -- django_strawberry_framework/__init__.py` and `git diff 5c6fdd71 HEAD -- django_strawberry_framework/__init__.py` are both empty; `orders/__init__.py`'s `__all__` is unchanged on the token instrument, so the three-tier contract DoD 2 pins (`OrderSet`, `OrderSetMetaclass`, `Ordering`, `RelatedOrder`, `order_input_type`, with `OrderArgumentsFactory` deliberately absent) is intact.

### Precondition 5 — deferred follow-up in `What looks solid` / `DRY findings`

Walked all six review sections across the two Worker-3 pass-1/2/3 blocks and the three final verifications. **Exactly one item is a DRY finding rather than a record item, and it is correctly not this pass's:** the existence challenge over three contracts pinned two or three times across one single-sited `utils/` implementation, plus Worker 3's pass-2 observation that `OrderSet._apply_orderings`'s two guards are each pinned twice (once through `apply_sync`, once through `apply_async`) since the sync/async split collapsed into one helper.

**Ruling 7's reasoning is intact and I do not reopen it.** Every resolution path — adding rows to `tests/utils/test_strings.py`, or deleting the two family test copies — changes **executable statements**, which forfeits the zero-executable-change entitlement that four passes and five instruments rest on and newly owes the boundary machinery this cycle is entitled to skip; and both halves sit outside the writable set (`tests/filters/test_inputs.py`, `tests/utils/*`). The integration pass does not edit source either. Worker 3's `_apply_orderings` observation belongs in the **same** maintainer look, not a separate item, and the catalog says so.

Nothing else in those sections is a deferred item that should land here rather than in the catalog.

### Precondition 6 — staged-anchor sweep: Worker 0's reading confirmed on its subject, WRONG on its scope

Command run tree-wide in both forms the precondition names, excluding `KANBAN.md` / `KANBAN.html` / `BACKLOG.md`:

```shell
grep -rEn 'TODO\(spec-028|TODO-(ALPHA|BETA|STABLE)-028' . --exclude-dir=.git \
  --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md
```

**0 hits in source or tests** — Worker 0's first clause is confirmed, and `grep -rn 'TODO(spec-028' .` independently returns nothing outside `docs/builder/`. **Worker 0's second clause is wrong:** "the only matches are prose *inside* Slice 2's own artifact" understates the population by four. There are **8 matches**, in four files:

| File | n | Classification |
| --- | --- | --- |
| `docs/builder/bld-slice-2-028-citation_and_provenance_rot.md` | 4 | prose describing its own sweeps — Worker 0's reading |
| `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv` | **2** | `TODO-ALPHA-028-0.0.11`, **a different card** |
| `docs/builder/DONE/build-025-scalar_map_helper-0_0_7.md` | 2 | that cycle's record of the same two CSV rows |

**The two CSV hits are not this build's anchors and must not be read as such.** `TODO-ALPHA-028-0.0.11` names card 028 *at the `0.0.11` milestone* — a pre-renumber id that shipped as `DONE-037-0.0.11` (the card renumber moved it). This build's card is `DONE-028-0.0.8`. So the card-id form of the sweep produces a **false positive by construction** whenever a renumber has recycled a number, and the two hits are already carded by the `025` cycle, which recorded them and declined to edit one surface of a multi-surface cluster.

Recorded rather than silently dropped because the sweep's own instruction says the card-id form "stages work too": here it stages *another card's* work under this card's number, and a reader who trusts the pattern without reading the milestone segment would either chase a discharged item or, worse, discharge one that belongs to a shipped card. **No anchor of this build's survives anywhere in source, tests, or comments.**

### X1 — the cross-cycle citation question: every code-side citation resolves against the REWRITTEN spec

Slice 2's citations were written against the pre-Slice-3 spec; Slice 3 then rewrote 101 exact strings across all thirteen Decisions plus three whole fenced blocks. Slice 3 proved the protect-list held **from the spec side** (45 headings byte-identical, same order). This pass owes the check **from the code side**, and it is the only gate that exists for it: `scripts/check_citations.py` resolves `path::Symbol` refs only and `docs/` is outside its scope.

**Method.** A resolver built this pass extracts every `spec-028[ \t]+(Decision|DoD|test plan|Edge cases|Slice checklist)[ \t]+N(sub)?(step M|Layer M)?` citation from every non-`.venv` `.py` file (579 files), then resolves it against the spec on disk: a `Decision N` citation must find a non-fenced `### Decision N` heading, and a `step M` / `Layer M` suffix must occur inside that Decision's own body; a `DoD N(x)` citation must find `## Definition of done` and the numbered item **and** its sub-letter; `test plan` / `Edge cases` / `Slice checklist` must find their headings.

**Three instruments, and they are provably different rather than one written twice** — the cycle's own R4 lesson, which this pass obeys because it was written for exactly this measurement:

| Instrument | Whitespace class | Reading |
| --- | --- | --- |
| **A** line-scoped | `[ \t]` only — structurally cannot cross a newline | **106** |
| **B** whitespace-flattened | whole file collapsed `\s+ -> " "` before matching | **106** |
| **C** join-aware | `\n` sits **inside** the pattern, so it matches only WRAPPED sites | **0** |

A == B at every class, so no `spec-028` citation is wrapped; C == 0 confirms it from the opposite direction. **UNRESOLVED: 0.** Spec anchors present: Decisions 1-13 all thirteen, `## Test plan`, `## Definition of done` with 28 numbered items and item 4 carrying `(a)`-`(e)`, `## Edge cases and constraints`, `## Slice checklist`. Both `spec-028 DoD 4(c)` citations resolve against item 4's `(c)`.

Breakdown by kind: 62 `Decision N`, 20 `test plan`, 2 `DoD N`, 1 `Edge cases`, 21 bare `spec-028`.

#### The finding X1 produced: Slice 3's protect-list population was under-measured 3.3x, by CASE

Slice 3's precondition census read `spec-028 test plan` = **6** on all three of its instruments. The true population is **20**. All three of Slice 3's instruments were **case-sensitive**, and there is a second spelling:

```
  91  spec-028   (case-sensitive)          15  Spec-028  (capital S)
 106  spec-028   (case-insensitive)         0  SPEC-028
   6  spec-028 test plan  (cs)             20  spec-028 test plan  (ci)
```

Fourteen of the fifteen are `"""Spec-028 test plan - …` docstring openers in `examples/fakeshop/test_query/test_library_api.py`; the fifteenth is `Spec-028 pinned the mixin's neutral home at` in `tests/orders/test_composition.py`. Slice 2 deliberately preserved that opener form ("Keep the existing `Spec-028 test plan` opener — that is the durable pointer, and it is already there"), so the spelling is pre-existing and intentional.

**The spelling is a coherent convention, and I verified that rather than assuming it.** Measured over every `.py` in the tree: the capital form appears at **0** mid-sentence positions, and the lowercase form appears at **0** docstring-opening positions. The split is purely positional — sentence-initial capitalization, ordinary English. So the *voice* is one voice.

**The instrument is what failed.** The heading-bearing population Slice 3 protected by hand is **85** citations (62 + 2 + 20 + 1), not the 71 its artifact states, and `## Test plan` carried 20 dependents rather than 6. Nothing broke, because Slice 3 protected the heading byte-identically anyway — but a future reconciliation cycle handed "6 test-plan citations" would under-protect by fourteen, and this is the tenth under-measurement in this cycle, arriving through a door none of the nine before it used: not wrap, not vocabulary, not subject — **case**.

The gate-extension card therefore gains a fourth required clause: **the spec-id match must be case-insensitive.** Three clauses were already earned by measured misses (flattened; symbol-joined-to-anchor with the newline inside the pattern; path split mid-segment at a `/`); this is the fourth.

### X2 — the cross-slice check list

| Check | Result |
| --- | --- |
| **Duplicated helpers across slices** | None. Zero helpers were added by any slice; the cycle's executable token stream is unchanged. |
| **Inconsistent naming between slices** | One class, X3 below. Otherwise consistent: `Covers` is the citation verb at **all 22** sites across the four `tests/orders/` files and `"""Closes` returns **0** — Slice 2's discretion item held across two builders and three passes. |
| **Inconsistent error handling between slices** | Not applicable and structurally impossible: no slice changed a raise, a guard, or an exception type. `registry.py` carries **0** `except ImportError`, which is the premise C6/C6c's repaired docstrings now state correctly. |
| **Repeated ORM/queryset patterns to centralize** | None introduced. The relevant *existing* one is already centralized and the slices' job was to say so: `orders/sets.py::OrderSet._apply_orderings` is the single helper both `apply_sync` and `apply_async` route through, and C11 restated three docstrings that had asserted a sync/async split to say exactly that. |
| **Misplaced responsibilities between modules** | None. The D5 shared-substrate direction is one-way (P4), and the three cross-boundary test imports are each intended. |
| **Missing or too-broad exports** | None. Public surface unchanged against both baselines; `orders/__init__.py.__all__` intact. |
| **Repeated literals / dict keys / tuple shapes across slices** | 56 cross-file, all pre-existing, none a candidate (P3). Zero introduced. |
| **Comments telling one coherent story** | X3 — one voice with **one** genuine exception. |

### X3 — one coherent story: yes on four axes, NO on one, with the two sites named

This was the substantive question for the cycle: does a reader moving between `orders/*.py`, `tests/orders/*`, the spec, and the rationale companion find one voice and one set of coordinates?

**Yes on four axes, each measured:**

1. **Citation verb.** `Covers` at 22 of 22 sites; `Closes` at 0. One convention, two builders, three passes.
2. **Citation form.** `path::Symbol` + optional `#"anchor"`, 98 resolved by hand in Slice 2 and re-confirmed here; `path:NN` is **0 tree-wide**, `Test <N>` ordinals **0**, `(spec-028 N3)` **0**, bare `Spec (Decision|DoD|Edge) N` **1** tree-wide (the out-of-family `spec-015` site).
3. **Wrapping.** Instrument C reads **0** wrapped `spec-028` joins; the join-aware repo-wide probe reads exactly **2**, both third-party targets — `orders/sets.py:258` (the cookbook, the concurrent cohort's own hunk) and `test_library_api.py:8014` (Django's own source, pre-existing) — which is Worker 0's reading, independently reproduced.
4. **Capitalization.** Positional and consistent: 0 mid-sentence capitals, 0 docstring-opening lowercase.

**No on the fifth: the spec id is carried at some sites and dropped at others, in the same file, on the same Decision.**

`tests/orders/test_inputs.py` carries **two** `spec-028` citations and **two** unprefixed in-family `Decision N` citations:

```
 62:    """All six members from spec-028 Decision 5 are present."""
 74:    """Members carry string values matching their names (Decision 5)."""
516:    """The materialized class stays on the module dict per spec-028."""
681:    # Module global is left parked (parking is load-bearing per Decision 9).
```

Line 62 and line 74 are **adjacent sibling tests twelve lines apart citing the same spec Decision in two different forms** — one gate-visible and census-visible, one invisible to all four durable-form censuses because it carries no `spec-028` token. Line 681 is the same defect in a body comment, in a function that contains **no** `spec-028` anchor at all, so it is not anaphora either. Verified: `grep -ni 'spec-028' tests/orders/test_inputs.py` returns exactly lines 62 and 516.

**Slice 2's plan chose the wrong normalization axis, and said so in writing without noticing.** C2 step 5's rationale for dropping ` lines 525-532` from line 62 was: *"This also makes the docstring consistent with its own immediate neighbour, `::test_ordering_member_values_are_string_names`, which already reads `(Decision 5)` with no line range."* The two were made consistent in **dropping the line number** and left inconsistent in **carrying the spec id** — and the spec id is the half a census and a heading-rename can see.

Slice 2 note 5 named the unprefixed `Decision N` form, declared it outside C12's decided population, and said re-scoping it is "a plan-level call, not a wording one." **The integration pass is that call**, and the scope is narrow: the out-of-family sites (32 in the sixteen, in `types/base.py`, `tests/types/test_base.py`, `test_library_api.py`) name spec-015 / 030 / 032 / 033 / 037 decisions this cycle never verified, and respelling them would be a worker asserting other cards' contracts — the same ground that fenced the connection/relay registry twins and the `spec-039 P2` / `spec-040 D6` ids. They stay.

**One in-family site is examined and correctly left:** `utils/inputs.py:1301`'s `the Decision 9 lifecycle clause` sits **four lines below** `(spec-027 / spec-028 Decision 9)` at line 1297, inside the same docstring. That is anaphora — a second reference back to an anchor already given — and respelling it would be redundant repetition, not clarity. Decided, not skipped.

**So the consolidation is exactly two tokens**, and it is why this artifact is `revision-needed`:

| Site | Current | Repair |
| --- | --- | --- |
| `tests/orders/test_inputs.py::test_ordering_member_values_are_string_names` #"matching their names (Decision 5)" | `(Decision 5)` | `(spec-028 Decision 5)` |
| `tests/orders/test_inputs.py::test_registry_clear_invokes_clear_order_input_namespace` #"parking is load-bearing per Decision 9" | `per Decision 9` | `per spec-028 Decision 9` |

**The trade-off, stated honestly and it does not bind here.** The reason Slice 2's DRY existence challenge was deferred is that every resolution changes executable statements and forfeits the zero-boundary entitlement all three slices' verification rests on. **This repair changes none.** It is docstring and comment text, exactly what C12 already did at sixteen sites across the same file set while the entitlement was re-proved on five instruments. The postcondition is therefore the same one C12 carried: AST **and** token identity must still read `SAME` for `tests/orders/test_inputs.py` against both `HEAD` and `5c6fdd71`, and the citation must sit unbroken on one line. `AGENTS.md` #"never offer defer-the-real-fix sequencing" is why this is dispatched rather than catalogued: it is 2 of 18 sites of one class, in one file, already in the writable set, verified.

**Also required of the consolidation pass, as postconditions rather than steps:** the four durable censuses re-measured **case-insensitively** (`spec-028` should rise 106 -> 108 and `spec-028 Decision N` 62 -> 64), the join-aware probe still 0 for `spec-028`, and `check_citations.py` exit 0.

### X5 — the entitlement, re-derived against the NEW HEAD

Slice 2's last proof predates both `8bab7ea8` and `5447c9eb`. Re-derived by this pass on two instruments against two reference points, all sixteen paths:

- **A** — docstring-stripped `ast.dump` (structure; blind to a moved non-docstring literal).
- **B** — `tokenize` stream with `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` dropped and **only statement-position** `STRING` tokens collapsed, every other literal kept verbatim (so a reworded or relocated non-docstring string would surface).

```
READINGS: 64  MISMATCHES: 0
```

Baselines `git show HEAD:<path>` and `git show 5c6fdd71:<path>`, extracted read-only into a scratch path outside the repository. **Which baseline carries the claim, per path:** for the 9 committed-only and the 2 mixed paths, HEAD is post-Slice-2 content and the HEAD reading is trivially true, so `5c6fdd71` is what proves anything there; for the 5 dirty-only paths both are non-trivial. Every path therefore has at least one non-trivial baseline. **Boundary count zero is confirmed, the failability re-run floor is empty by entitlement, and no fail-open shape can have landed** — a fail-open shape is an executable expression.

### Slice-local checks run by this pass

| Check | Reading |
| --- | --- |
| `spec-028`-family citations resolved against the rewritten spec | **106** citations, **0** unresolved; instruments A/B/C = 106 / 106 / 0 |
| durable censuses, case-**sensitive** (Slice 3's instrument) | `spec-028` 91, `Decision N` 62, `DoD N` 2, `test plan` 6, `Edge cases` 1 — reproduces Slice 3's closing reading exactly |
| durable censuses, case-**insensitive** (the corrected instrument) | `spec-028` **106**, `Decision N` 62, `DoD N` 2, `test plan` **20**, `Edge cases` 1 |
| `path:NN` citations, line-scoped and flattened | **0 / 0 tree-wide** — better than the postcondition, which was 0 within the sixteen |
| `Test <N>` ordinals | **0 / 0** tree-wide |
| bare `Spec (Decision\|DoD\|Edge) N` | **1 / 1** tree-wide, `tests/types/test_relay_interfaces.py` (`spec-015`, out of family, byte-identical) |
| `(spec-028 N3)` review-item id | **0** tree-wide |
| prose `lines? NN` within the sixteen | **2 / 2**, both the ruled cookbook pair (`tests/orders/test_sets.py:169`, `tests/orders/test_factories.py:251`) |
| review-item ids within the sixteen | **3**, the deliberately-left `spec-039 P2` / `spec-040 D6` in `utils/inputs.py` |
| join-aware wrap probe, repo-wide `.py`, `\n` inside the pattern | **2**, both third-party targets, both as Worker 0 read |
| `orders/base.py` / `orders/factories.py` Layer citations | `Layer 1` and `Layer 5` respectively, as Worker 0 read |
| `library/orders.py` orderset count | docstring reads `Seven ordersets`; AST re-derivation over `ClassDef` nodes with an `OrderSet` base -> **7** |
| `check_spec_glossary.py --spec docs/SPECS/spec-028-orders-0_0_8.md` | `OK: 44 terms - all have glossary entries and at least one spec link.` **exit 0** |
| `check_citations.py` | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md).` **exit 0** — the exit code is the criterion (readings this cycle: 743 / 758 / 772 / 779 / 780 / 782) |
| `check_trailing_commas.py --check` (sixteen `.py` + spec + rationale) | exit 0 |
| `ruff format --check` (the sixteen, never `.`, never `--fix`) | `16 files already formatted` |
| `ruff check` (the sixteen, read-only) | `All checks passed!` |
| `git diff --check` over the sixteen | exit 0 |
| zero-executable-change | 64 readings, 2 instruments, 2 baselines, `MISMATCHES: 0` |
| staged anchors | 0 in source or tests; 8 tree-wide, all classified above |
| rationale structure | `## Discharged by Slice 3` present, `Handed to Slice 3` **0**, **9** `### Corrections this Decision received after ship` sub-sections (Decisions 2, 3, 5, 6, 8, 9, 10, 11, 13) |
| GLOSSARY D11 asymmetry | `## RelatedOrder` carries `Position-side-channel note:`; `## OrderSet` carries none — Slice 3's re-derivation 1 confirmed |
| CHANGELOG state | `## [0.0.8] - 2026-06-03` carries both Ordering bullets; **no `[Unreleased]` heading** — the spec's Status-line claim holds |

No `pytest` was run: [`AGENTS.md`][agents] #"No pytest after edits", and the full sweep belongs to the final gate. **No `--cov*` flag in any command in this pass.** No `.py` file, spec, rationale, or fenced path was edited; no commit, no branch, no amend.

**Two of my own instruments produced false readings and both are recorded against me**, because this cycle's standing lesson is that a differencer proves nothing unless it can fail:

- My first capitalization check used `pre.endswith(('"""', "'''", "#", ""))` as the sentence-initial test. `str.endswith("")` is **True for every string**, so the predicate was a constant and no violation could ever be reported. It read "0 violations" and meant nothing. Re-run with a real predicate it reads 0 for a reason.
- My first count of the rationale's corrections sub-sections used `grep -c`, which counts **lines**, and one line at `rationale:602` *mentions* the heading in prose. It read 10 and I nearly filed a stated-count defect against Slice 3. Parsed structurally, the count is **9** and Slice 3's figure is right.

That is the eleventh and twelfth instance of this cycle's one recurring defect, and both hit the integrator in the pass whose subject is instrument blindness. The generalization is unchanged and now has a third door: **`\s` crosses a newline, `grep -c` counts lines, and `endswith("")` is always true** — three ways to write a check that cannot fail.

### DRY check across this slice and prior accepted slices

**No new duplication, and structurally none possible**: zero executable tokens changed across sixteen paths on two instruments against two baselines, so there is no helper, constant, branch, or literal introduced to consolidate. The prose symmetries in the diff are the fix rather than duplication — C6c/L4's narrowing is deliberately one story across two registry twins (Ruling 5's shape), and `utils/inputs.py`'s two C12 sites use one decided wording.

**One cross-cycle asymmetry that must NOT be tidied, recorded so a later sweep does not "fix" it.** `django_strawberry_framework/utils/inputs.py` now carries two attribution conventions: the **dual-family** `spec-027 / spec-028 Decision N` at lines 6, 75, 400, 1297, 1441 (the concurrent cohort's), and the **single-family** `spec-028 Decision 8` at 1708 and 1733 (Slice 2's C12). The difference is **semantically load-bearing** — 1708 and 1733 state a contract the order family has and the filter family does not ("the order family (no operator bag) can be empty; the filter family never reaches this branch"), so naming only `spec-028` there is correct and adding `spec-027` would make both sentences false. A uniformity sweep would break them. Verified by reading both sentences at source.

### Consolidated deferred-work inputs, graded for transcribability

This pass does **not** write `### Deferred work catalog` — the final gate does. What it owes is a check that each routed item is stated specifically enough for the final gate to transcribe without re-deriving. **25 items routed: 16 from Slice 2's second final verification, 9 from Slice 3.** Twenty are transcribable as written. **Five are not, and each is flagged with the measurement that supersedes it.**

| # | Item | Verdict |
| --- | --- | --- |
| S2-1 | Two cookbook line refs left with reason, at `test_sets.py:169` / `test_factories.py:251` | **OK** — both confirmed present and byte-identical this pass |
| S2-2 | `check_citations.py` gate extension, three instrument clauses | **FLAG — needs a fourth clause.** The match must be **case-insensitive on the spec id**: 15 `Spec-028` occurrences are invisible to every case-sensitive probe, which is what under-read `## Test plan`'s protect-list 20 -> 6 (X1). Slice 3's item 6 also folds in a fifth capability: resolve `spec-NNN <Heading>` against the named spec's heading list. **That resolver now exists** — this pass built and ran it (106 citations, 0 unresolved), so the card can cite a working prototype rather than a design |
| S2-3 | Standing instrument lesson: `\s` crosses a newline, so it cannot be the line-scoped control | **OK, and extend** — two further shapes measured this pass: `grep -c` counts lines (a heading mentioned in prose inflates it), and `endswith("")` is always true |
| S2-4 | `bld-slice-7-027:214` certifies "no wrapped citation" over a wrapped join | **OK** — the join at `orders/sets.py:258` is confirmed present by two independent instruments |
| S2-5 | Split-path wrap at `test_products_api.py:3334` | **OK** — confirmed at that exact line (`` `tests/rest_framework/ `` / newline / `` test_resolvers.py` ``) |
| S2-6 | Two third-party-target wrapped joins deliberately left | **OK** — the join-aware probe returns exactly these two and nothing else |
| S2-7 | Tree-wide raw-line-citation residue outside this cycle's paths | **FLAG — the inventory is stale in BOTH directions.** `mutations/{resolvers,fields,sets}.py` and `test_products_api.py` now read **0** (discharged by the concurrent cohort). The surviving genuine first-party residue is **10 line-scoped / 12 flattened across four files**: `optimizer/walker.py` 1, `tests/optimizer/test_walker.py` 3, `tests/optimizer/test_extension.py` 3+1 wrapped, `tests/mutations/test_sets.py` 3+1 wrapped — all naming `spec-035` / `spec-036`. The tree-wide 14/16 figure also includes **two non-citations** that must not be chased: `scripts/check_trailing_commas.py:910` (prose about the script's own reporting) and `tests/test_export_dry_review.py:153` (`"line 1"` as assert-string fixture data) |
| S2-8 | Two-of-four `except ImportError` twins in `tests/test_registry.py` | **OK** — the two fenced twins confirmed still on the original premise |
| S2-9 | DRY existence challenge, both halves + the `_apply_orderings` pair in the same look | **OK** — Ruling 7's reasoning re-checked and intact (P5) |
| S2-10 | Promotable `_safe_import` pins (cold submodule of a poisoned package; the two-call count) | **OK** — both shapes and their `tests/utils/` home stated |
| S2-11 | Two out-of-family review-item ids in `utils/inputs.py` (`spec-039 P2`, `spec-040 D6`, 3 occurrences) | **FLAG — the population is 5% of what the item describes.** C1's defect class measured tree-wide: **52 line-scoped / 54 flattened across 24 files**, naming ten other cards (`spec-035`, `036`, `039`, `040`, `041`, `044`, `048`, `051`), heaviest at `auth/mutations.py` (6), `mutations/inputs.py` (6), `rest_framework/inputs.py` (4). **Two are WRAPPED** (`mutations/resolvers.py`, `rest_framework/resolvers.py`), so the class carries the wrap defect too. The catalog names 3 of 54 |
| S2-12 | Cross-cycle ownership collision at its current size (80 dirty paths, 12 `027` artifacts) | **FLAG — status changed: it is CLOSED as a live event.** Both cycles' work is now committed; the dirty set is **14 paths** (8 modified + 6 untracked, this artifact included), every one of them this cycle's, and all **18** `027` artifacts are tracked and committed. Nothing was lost in either direction. Restate as a closed record with the lesson, not as a live decision |
| S2-13 | `8a9840dc` carries three `spec-028` hunks under a `spec-027` commit message | **FLAG — the scope is now three commits and eleven paths.** `8a9840dc`, `8bab7ea8` and `5447c9eb` between them carry Slice-2 hunks in **11** of the sixteen, and **two paths are MIXED** (part committed, part dirty) — see the table at the top of this artifact. `git diff HEAD -- <path>` under-reads those two and `git diff 5c6fdd71 HEAD` under-reads them the other way |
| S2-14 | A banner count is unmaintained by construction | **OK** |
| S2-15 | Two plan-text defects (L3's `BUILD.md` misquote; `### Partition correction 1`'s superseded measurements) | **OK** — and add a third: the **dispatch brief's** committed/dirty split is wrong in three ways (S2-13) |
| S2-16 | Slice 3's protect-list scope | **Superseded** — Slice 3 ran. Restate as the *next* cycle's inheritance, with the corrected population: **85** heading-bearing citations (62 `Decision N` + 2 `DoD N` + **20** `test plan` + 1 `Edge cases`), not 71; anchors `### Decision N`, `## Test plan`, `## Definition of done` (there is **no** `### DoD` heading), `## Edge cases and constraints`; and the census must be case-insensitive |
| S3-1 | `KANBAN.md`'s `DONE-028` body carries four retired claims; fold into the carded `KANBAN.md:357` sweep | **OK** |
| S3-2 | `docs/GLOSSARY.md`'s `## OrderSet` lacks the position-side-channel note its `## RelatedOrder` sibling carries | **OK** — asymmetry confirmed at HEAD by reading both entries |
| S3-3 | `docs/TREE.md` omits `__init__.py` by renderer design, so every "five files" spec claim is off by one | **OK** |
| S3-4 | Two orphaned `0.0.9` deferrals already carded at `KANBAN.md:357` | **OK** |
| S3-5 | `[relay]` is a defined-but-unused link definition | **OK** |
| S3-6 | Gate clause: resolve `spec-NNN <Heading>` citations against the named spec's heading list | **OK — merge into S2-2**, which is the same card. The prototype exists (X1) |
| S3-7 | Two `0.0.9` voice statements defensible either way | **OK** |
| S3-8 | The cross-cohort seam widened | **Duplicate of S2-12** — merge; and both are now closed as live events |
| S3-9 | No code finding surfaced, and it was looked for specifically | **OK, and it is a negative result worth keeping** — this pass independently found none either |

**One item this pass adds**, which no slice named: `docs/GLOSSARY.md`'s `## RelatedOrder` entry narrates its own history — *"the neutral shared module per the package's set-family discipline, **not `filters.base` as named in earlier revisions**"*. That is the shape [`BUILD.md`][build] `## Spec rationale extraction` forbids in a spec, appearing in the generated standing doc instead. `docs/GLOSSARY.md` is DB-generated and fenced this cycle; the fix is a glossary-DB edit plus a re-render, and it belongs beside S3-2, which touches the same entry pair.

### Consolidation required — what Worker 0 dispatches

One cohort, one file, two edits, no architectural discretion. `tests/orders/test_inputs.py` is already in Slice 2's authorized writable set.

1. `::test_ordering_member_values_are_string_names` docstring: `(Decision 5)` -> `(spec-028 Decision 5)`.
2. `::test_registry_clear_invokes_clear_order_input_namespace` body comment: `per Decision 9` -> `per spec-028 Decision 9`.

Standing constraints, none discretionary: the citation sits **unbroken on one line**; no line past the 110-column E501 grace; **zero new `spec-028 #"substring"` citations**; **no executable statement changes** — AST and token identity must still read `SAME` for the file against both `HEAD` and `5c6fdd71`, and the entitlement lapses if they do not. `ruff format` / `ruff check --fix` scoped to that one file, never `.`. Do **not** touch the out-of-family unprefixed `Decision N` sites in `types/base.py`, `tests/types/test_base.py`, or `test_library_api.py` (other cards' contracts), and do **not** touch `utils/inputs.py:1301` (anaphora, decided above).

Postconditions: censuses re-measured **case-insensitively** (`spec-028` 106 -> 108, `spec-028 Decision N` 62 -> 64, `test plan` 20, `DoD N` 2, `Edge cases` 1, single-line == flattened at every class); join-aware probe 0 for `spec-028`; the X1 resolver re-run with **0** unresolved; `check_citations.py` exit 0; `check_trailing_commas.py --check` exit 0. Then Worker 3 reviews, and this pass runs again.

### Spec changes made (Worker 1 only)

**None, and none owed.** The spec and its rationale companion closed `final-accepted` at Slice 3 and are read-only to this pass. Per-spawn status-line re-verification is recorded under `### Spec status-line re-verification`; every claim in lines 1-8 was checked against HEAD and holds. Nothing this pass measured is a spec defect: the X1 resolver found **0** unresolved citations, so Slice 3's rewrite broke nothing pointing into it, and the one record correction X1 produced (the `## Test plan` protect-list population) is a defect in **Slice 3's artifact**, not in the spec — the heading it protects is byte-identical either way. No Slice-3 re-loop is needed.

**Deferral reasons for boxes left `- [ ]`: none.** All 11 boxes are `- [x]` and every tick names its measurement.

### Final status

`revision-needed`.

Every precondition is discharged, and two of the six produced findings rather than confirmations: the staged-anchor sweep's card-id form yields a false positive from a pre-renumber card id, and the helper-coverage obligation is vacuous by entitlement rather than satisfied by sampling. The cross-cycle citation question — the one no slice could answer from its own side — closes clean: **106** `spec-028`-family citations in `.py`, **0** unresolved against the rewritten spec, on three provably-different instruments. The zero-executable-change entitlement holds against the new HEAD, 64 readings, 0 mismatches, every path with a non-trivial baseline.

The one thing blocking `final-accepted` is two tokens: `tests/orders/test_inputs.py` cites spec-028 Decision 5 in the durable form on line 62 and drops the spec id on line 74, twelve lines later, on the same Decision, in a sibling test's docstring — and again at line 681 in a function with no anchor at all. That is 2 of 18 sites of C12's own class, in C12's own file, and it is the partial claim fix this cycle exists to close. It changes no executable statement, so the entitlement that deferred the DRY existence challenge does not shelter it.

---

## Pass 2 — the finding is discharged and the pass closes (Worker 1)

`Status: final-accepted`, revised from `revision-needed`. The original sections above are preserved unedited; this section records the discharge and re-confirms the pass's own six preconditions against the **current** tree, since HEAD, the dirty set, and one artifact's location have all moved since the first pass ran.

### The finding, discharged

The two-token Medium this pass raised is closed by the consolidation cohort at [`bld-slice-4-028-decision_citation_consistency.md`][bld-slice-4], which I set `final-accepted` in the pass immediately preceding this one. **I re-derived every load-bearing claim on instruments written for that pass rather than reading its report** — the full evidence is that artifact's `## Final verification (Worker 1)`; the summary that matters here is:

- **Both repairs landed and qualified rather than added.** `tests/orders/test_inputs.py:74` now reads `(spec-028 Decision 5)` and `:681` reads `per spec-028 Decision 9`. Bare in-family `Decision N` in that file goes **2 -> 0** on three provably-different instruments (line-scoped `[ \t]`, `\s+`-flattened, join-flattened) while the **total `Decision N` holds at 3**; a third citation would read 3 -> 4. The reconstruction's byte delta is exactly **18 = 2 x 9**, and `HEAD` reads identically to the reconstruction at every class, so both deltas are wholly the cohort's.
- **Both citations resolve to the subjects they claim in the rewritten spec.** `### Decision 5` at spec:438 (exactly one occurrence) is the six-member enum block whose member *values* equal their names — line 74's claim; `### Decision 9` at spec:641 (exactly one) says verbatim that `registry.clear()` "leaves already-materialized module globals **parked** in `orders.inputs.__dict__`" and that "Parking is **load-bearing**" — line 681's claim. Read at source, not quoted from an artifact.
- **Zero executable change, so the entitlement is intact.** Two independently-written instruments (docstring-stripped `ast.dump`; token stream with only statement-position strings collapsed) against three reference points — `HEAD` `5447c9eb`, `5c6fdd71`, and a reconstruction — read `SAME` in all **6** readings, falsified on **6** controls each asserting its own mutation actually landed, with the redundant-parens control reading `SAME` on one instrument and `DIFFERENT` on the other and so proving the two are two.

**X3's answer therefore flips on its fifth axis.** The one place this pass found "no" — the spec id carried at some sites and dropped at others in the same file on the same Decision — now reads **yes**: the file's bare in-family class is 0 and its two remaining `Decision 5` citations both carry the spec id. The four axes that already read yes are unchanged (`Covers` 22/22, `path:NN` 0 tree-wide, 0 wrapped `spec-028` joins, positional capitalization consistent).

**Two record corrections the cohort produced, both adopted rather than routed**, because both sentences are in documents this role owns:

1. **This artifact's `### X3` and the plan's cohort section describe `tests/orders/test_inputs.py:516` as "165 lines away on a different topic". That is false.** Line 516 is `::test_clear_order_input_namespace_leaves_module_globals_parked` — the **same** parked-globals subject as line 681. The non-anaphora conclusion is unaffected and in fact rests on firmer ground: **516 carries no Decision number**, so it could never have been the antecedent for a bare `Decision 9` at any distance. Distance was never the discriminator; the absence of a number is. This cycle's dominant defect class — a true finding carried by a false description — one more time, and corrected here rather than deferred.
2. **Line 516's own `per spec-028` names no Decision at all**, where the content it asserts is Decision 9's parking clause. It is not a bare `Decision N`, so it sat outside the dispatched class, and qualifying it would have taken the file's `Decision N` total 3 -> 4 — the exact reading the qualified-not-added proof exists to detect. Correctly left byte-identical; catalogued as the adjacent class.

### The escalation the cohort's review raised: ruled DEFERRED, with the discriminator recorded

Worker 3 escalated `tests/orders/test_finalizer.py` #"Decision 6 -- first-bind model compatibility" as the same shape as the site just repaired. Worker 0 answered with a whole-population measurement keyed on **anchor presence rather than distance**, and the ruling is written in full in the cohort artifact. Recorded here because the integration pass is where a residual cycle either stops or regresses:

- **Worker 0's measurement is confirmed on my own instrument, with two refinements.** Tree-wide unprefixed `Decision N` / `DoD N` in package + tests + examples `.py`: **442**, exactly as Worker 0 read it (my first reading of 443 included one occurrence in a prior review cycle's `docs/review/temp-tests/` scratchpad — a **corpus** difference, not a digit, and Worker 0's corpus is the right one). Occurrences in files carrying **no** `spec-NNN` anchor anywhere: **16**, confirmed, **none in the orders family** — though Worker 0's per-file split understates `permissions.py` at 7 where it carries **8**, and its own list sums to 15 against its stated 16. Orders family: **2**, both in `tests/orders/test_finalizer.py`, which carries 3 `spec-028` anchors; every other family file reads 0 unprefixed against 2-20 anchors. (Worker 3's family figure of 3 counts `utils/inputs.py:1300` — a family-boundary definition, not a disagreement.)
- **One refinement strengthens the ruling rather than weakening it: 58 of the 442 are not unprefixed at all.** They are spec-qualified citations **wrapped across two source lines**, the qualifier ending one line and `Decision N` opening the next. Credited, the genuine tree-wide population is **384** — and **15** of those 58 are invisible to a plain `\s+` flatten because a continuation `#` sits between the halves, which is the cohort's fifth blind spot measured tree-wide for the first time. **None of the 58 is in the orders family**, so the family's 2 stand as genuinely unprefixed and Worker 0's family reading is untouched.
- **The ruling, in the form the next reader cannot re-fight:** a bare `Decision N` is a **defect** when nothing a reader passes on the way to it establishes the spec, and **anaphora** when something does. Line 681's only candidate antecedents were a sibling test's docstring twelve lines up (reached only by chance) and line 516, which carries no Decision number. `test_finalizer.py:432`'s antecedent is the **module docstring**, lines 10 and 14, naming both `spec-028` and `Decision 6` in the file's first fourteen lines, which no reader of the file bypasses — so 320 lines of *file* is not 320 lines of *reading order*. The same test disposes of `utils/inputs.py:1300` identically, which is why this pass's decision to leave it was right. **Deferred, catalogued with the 442 / 384 / 16 / 2 measurement attached**, so the next reader re-derives the measurement and not the ruling.

### The six preconditions, re-confirmed against the current tree

HEAD is unchanged at `5447c9eb`. The dirty set is **16 paths** (8 modified `.py`/spec + 7 untracked cycle artifacts and the rationale companion + 1 **staged** rename), all of them this cycle's except the rename. All 18 `027` artifacts are tracked and committed.

| # | Precondition | Re-confirmed reading |
| --- | --- | --- |
| **P1** | every prior `bld-slice-*-028*.md` read in slice order | **Four now, all read in full, in order, in this pass**: `bld-slice-1-028` (255 lines), `bld-slice-2-028` (3,430 — plan, three build passes, three review passes, two final verifications, 15 rulings, 22 boxes), `bld-slice-3-028` (441), `bld-slice-4-028` (its own pre-final-verification state). No section skipped, no "as needed" |
| **P2** | `review_inspect.py` run-or-recorded-skip coverage | **Still vacuous by entitlement, and the entitlement is re-derived against the current tree**: two instruments x two baselines x all sixteen paths -> **64 readings, `MISMATCHES: 0`**. Zero review-worthy logic changed anywhere in the cycle, so the qualifying population is empty. The cohort recorded its own skip with the trigger quoted verbatim, which I read and confirmed against `BUILD.md` `### When to run the helper during build` — no trigger fires (no new file; `tests/orders/` is under neither `optimizer/` nor `types/`; zero logic lines) |
| **P3** | `Repeated string literals` cross-file comparison | **56 reproduced exactly, and the instrument's definition is now recorded so the number is re-derivable.** `review_inspect.py` lists a literal only when its **per-file** count is `> 1` (`_render_literals`, `count > 1`), so `BUILD.md`'s "a literal in two or more files" means: per-file count `> 1`, appearing in `>= 2` of the sixteen. Recomputed from the AST with docstrings stripped, that is **56** — identical at the current tree, at `HEAD`, and at `5c6fdd71`, with **NONE added and none removed by the whole cycle**. A naive "present at all in `>= 2` files" reading gives **123**; both are correct under their own definition, and stating which one the 56 is prevents the next reader re-deriving the other and filing a discrepancy. **The cohort added none, structurally**: the population is a property of the executable token stream, which is unchanged |
| **P4** | `Imports` comparison, one-way direction | **Holds, re-read from the AST rather than the overview.** `utils/inputs.py`'s only relative imports are `..exceptions`, `.imports`, `.strings` — **nothing** from `orders/` or `filters/`. `orders/inputs.py -> .sets` sits under `if TYPE_CHECKING:` (line 52), so the apparent `sets` <-> `inputs` cycle is not one at runtime. `types/base.py -> ..orders.sets` is inside `_validate_orderset_class` (line 207), symmetric with `..filters.sets` inside `_validate_filterset_class` (line 178) — in-function only, both |
| **P5** | accepted artifacts' `What looks solid` / `DRY findings` walked | **Re-walked across all four artifacts, including the cohort's.** The only DRY item is the deferred existence challenge (Ruling 7) plus Worker 3's `_apply_orderings` observation, which belongs in the **same** maintainer look and not a separate one — unchanged, and the cohort's review explicitly declined to reopen it. Nothing else in those sections belongs in this pass rather than the catalog |
| **P6** | staged-anchor sweep, both forms, excluding `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` | **0 in source or tests — confirmed and unchanged.** Tree-wide the count is now **13, not 8**, and the entire delta is *this cycle's own artifact prose describing the sweep*: `bld-slice-2-028` 4, `bld-integration-028` 4 (this file), `build-028` 1, plus the two `TODO-ALPHA-028-0.0.11` rows in `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv` and the two in `docs/builder/DONE/build-025-scalar_map_helper-0_0_7.md` recording them. **The sweep's population includes the artifacts that document the sweep, so it inflates monotonically as the cycle writes itself up — the gating clause (0 in source or tests) is the stable half.** The CSV pair is re-confirmed a false positive: `TODO-ALPHA-028-0.0.11` is a pre-renumber id that shipped as `DONE-037-0.0.11` (`KANBAN.md:110`, Upload scalar / file-image mapping), while this build's card is `DONE-028-0.0.8` (`KANBAN.md:119`) |

### The code-side citation resolver, re-run — and its own figure corrected

Re-run on a resolver written for this pass, case-insensitively, over all **579** non-`.venv` `.py` files, with three provably-different instruments:

| Instrument | Whitespace class | Heading-bearing citations |
| --- | --- | --- |
| **A** line-scoped | `[ \t]` only — structurally cannot cross a newline | **87** |
| **B** flattened | whole file collapsed `\s+ -> " "` | **87** |
| **C** join-aware | `\n` **inside** the pattern, so it matches only WRAPPED sites | **0** |

**UNRESOLVED: 0.** By kind: 64 `Decision N`, 20 `test plan`, 2 `DoD N`, 1 `Edge cases`. Every `Decision N` resolves against a non-fenced `### Decision N` heading (all 13 present); both `spec-028 DoD 4(c)` citations resolve against `## Definition of done` item 4's `(c)`; `## Test plan` and `## Edge cases and constraints` both resolve. A == B at every class and C == 0 confirms it from the opposite direction, so no `spec-028` citation is wrapped.

**Correcting this pass's own figure, because "expect 108" and "106 citations" are two different populations.** The first pass reported "**106** `spec-028`-family citations, 0 unresolved" and then broke it down as `62 Decision N + 20 test plan + 2 DoD N + 1 Edge cases + 21 bare spec-028`. The 21 bare tokens are not citations — they carry no heading — so 106 was the **total `spec-028` token count**, of which **85** were heading-bearing and resolvable. Both halves now read as predicted: total tokens **106 -> 108** (+2, one per repair) and heading-bearing **85 -> 87** (+2), with bare tokens unchanged at **21**. The resolver's population is the 87. Recorded because a later pass differencing against "106 citations" would be differencing a token count against a citation count — the same subject error this cycle has now hit in four separate places.

### Deferred-work consolidation, re-confirmed and extended to 30 items

The pass's grading stands: **25 items, 20 transcribable as written, 5 needing restatement.** Each of the five was re-measured this pass rather than carried forward, and all five restatements are confirmed exact:

- **S2-2** — the case clause: confirmed. The bare `[Ss]pec (Decision|DoD|Edge) N` class is **5** case-insensitively against **1** under a capital-only pattern; the four extra are all lowercase and all other cards'.
- **S2-7** — the inventory is stale both ways: confirmed to the file. Tree-wide `\blines?[ \t]+\d+` reads **line-scoped 14 / flattened 16** across 8 files. The genuine first-party citation residue is **10 / 12 across four files** — `optimizer/walker.py` 1/1, `tests/optimizer/test_walker.py` 3/3, `tests/optimizer/test_extension.py` 3/4, `tests/mutations/test_sets.py` 3/4 — and the remaining four hits are the two ruled cookbook refs in `tests/orders/` plus the two non-citations (`scripts/check_trailing_commas.py`, prose about the script's own reporting; `tests/test_export_dry_review.py`, `"line 1"` as assert-string fixture data). `mutations/{resolvers,fields,sets}.py` and `test_products_api.py` read **0**, discharged by the concurrent cohort.
- **S2-11** — 3 of 54: confirmed. The review-item-id class reads **line-scoped 52 / flattened 54 across 24 files**, heaviest at `auth/mutations.py` 6, `mutations/inputs.py` 6, `rest_framework/inputs.py` 4, and **2 wrapped** (`mutations/resolvers.py`, `rest_framework/resolvers.py`). The catalog names 3.
- **S2-12** — a closed event, not a risk: confirmed, and smaller than when this pass first read it. The dirty set is **16 paths**, every one this cycle's except the staged `027` build-plan rename; all 18 `027` artifacts are tracked and committed. Restate as a closed record with the lesson.
- **S2-13** — the 3-commits / 11-paths / 2-mixed shape: confirmed per path. `git diff --name-only 5c6fdd71 HEAD` over the sixteen returns **11**; `git diff HEAD --name-only` returns **7**; and **2 are both** — `tests/test_registry.py` and `examples/fakeshop/test_query/test_library_api.py`.

**Five items the cohort adds, all stated specifically enough to transcribe** (full wording in `bld-slice-4-028`'s `### Spec changes made (Worker 1 only)`): `tests/orders/test_inputs.py:516`'s `spec-028`-without-a-Decision reference; the four lowercase `spec Decision N` sites naming other cards' decisions (`filters/factories.py:143`, `list_field.py:192`, `tests/test_list_field.py:206`, `tests/types/test_resolvers.py:785`) plus the capital `spec-015` site, with the case-door note; the `#`-comment flattening clause, now measured tree-wide at **15** sites a plain `\s+` flatten cannot see; the control-hygiene clause (a control that did not run reads identically to a passing proof); and the 442 / 384 / 16 / 2 anchor measurement behind the deferral ruling. **Total for the final gate to transcribe: 30 items.** One item this pass added earlier stands unchanged: `docs/GLOSSARY.md`'s `## RelatedOrder` entry narrates its own history ("not `filters.base` as named in earlier revisions") — re-read at source this pass and still present; DB-generated, so out of this cycle's scope and belonging beside S3-2, which touches the same entry pair.

### Boundary count, hot path, floor verification

**Zero boundaries across the whole cycle, and this pass adds none** — it writes two Markdown files. **No failability proof is owed, by entitlement rather than omission**: a boundary is an executable expression, and the cycle's executable token stream is identical to two reference points across all sixteen paths (**64 readings, 0 mismatches**, re-derived this pass against the current tree). No fail-open shape can have landed for the same structural reason. **Hot path: none declared, none owed, none flagged. Floor-verification scope: `none`**; no floor venv was built and the shared `.venv` was not mutated or read for a version claim. (Reference only, from [`BUILD.md`][build] `## Floor verification`: Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0.)

### Gates, re-run read-only

| Command | Result |
| --- | --- |
| `uv run python scripts/check_citations.py` | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md)`, **exit 0** — correctly flat across the cohort: both repairs add prose refs no gate resolves, and a fall would have meant breakage |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-028-orders-0_0_8.md` | `OK: 44 terms - all have glossary entries and at least one spec link.` **exit 0** |
| `uv run python scripts/check_trailing_commas.py --check` (the sixteen + spec + rationale) | exit 0 |
| `uv run ruff format --check` (the sixteen, never `.`, never `--fix`) | `16 files already formatted` |
| `uv run ruff check` (the sixteen, read-only) | `All checks passed!` |
| `git diff --check` | exit 0 |
| `uv run pytest tests/orders/test_inputs.py --no-cov --collect-only -q` | **42 tests collected**, 0 errors. No `--cov*` flag in any command in this pass |

No `pytest` beyond that collection check — the full sweep belongs to the final gate, which runs next. No `.py`, spec, or rationale file was edited by this pass; no commit, no branch, no amend, no `git stash` / `checkout` / `restore` / `worktree`.

### Spec status-line re-verification (this spawn)

Spec lines 1-8 still read as a shipped-state record and nothing this pass measured falsifies them. Both claims a moving file could have rotted were re-checked at source: `CHANGELOG.md` carries the "Ordering subsystem" Added bullet and the `Meta.orderset_class` promotion Changed bullet under `## [0.0.8] - 2026-06-03`, and `grep '^## ' CHANGELOG.md` shows **no `[Unreleased]` heading**; `docs/GLOSSARY.md`'s Index reads `shipped (0.0.8)` for all five Ordering symbols (`OrderSet`, `RelatedOrder`, `Ordering`, `order_input_type`, `Meta.orderset_class`). The rationale-companion pointer resolves on disk. **No spec edit this pass, and none owed** — the resolver found 0 unresolved citations, so Slice 3's rewrite broke nothing pointing into it.

### Final status

`final-accepted`.

The one Medium this pass raised is discharged, verified on instruments this role wrote rather than accepted from the cohort's report: the repair **qualified rather than added** (bare in-family `Decision N` 2 -> 0 on three instruments while the total holds at 3; reconstruction byte delta exactly 18), both citations resolve to headings that exist once each and carry their claims verbatim, and **zero executable change holds on two instruments against three reference points, 6 readings, 0 mismatches, on six controls each asserting its own mutation landed**. So the zero-boundary entitlement the whole cycle rests on is intact and the failability re-run floor is empty **by entitlement, not by omission**.

All six preconditions re-confirmed against the current tree, two of them corrected rather than merely re-read: the staged-anchor sweep's tree-wide population is now 13 and grows with the cycle's own paperwork while its gating clause (0 in source or tests) is stable; and this pass's own "106 citations" was a token count where the resolvable population was 85 — now 108 tokens / **87** heading-bearing, **0 unresolved**, on three provably-different instruments. The 56 cross-file literals reproduce exactly once the instrument's per-file `> 1` threshold is stated, identical at all three reference points, with none added by the cycle. Import direction one-way, re-read from the AST.

Thirty deferred items are stated specifically enough for the final gate to transcribe without re-deriving. **The cross-slice integration pass is closed; the final test-run gate is what runs next.**

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[artifact]: ARTIFACT.md
[bld-slice-4]: bld-slice-4-028-decision_citation_consistency.md
[build]: BUILD.md
[build-028]: build-028-orders-0_0_8.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
