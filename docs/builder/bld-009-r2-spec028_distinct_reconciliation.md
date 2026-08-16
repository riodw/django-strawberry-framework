# Build: R2 — reconcile `spec-028`'s orphaned `DISTINCT ON` deferral

Spec reference: `docs/SPECS/spec-028-orders-0_0_8.md` (`### Decision 12`, line 979, plus its in-file echo sites)
Contract: `docs/builder/build-009-rich_schema_architecture-0_0_4.md` `### Maintainer decision 3` site 2, widened by `### Maintainer decision 7` as amended (the shipped source citations of Decision 12: the `orders/sets.py` docstring clause, plus `orders/inputs.py`'s docstring clause and its `del`-line comment)
Status: final-accepted

Combined plan + perform pass (this cycle's `### Deviation 3`): Worker 1 is the only role that may edit a spec, so there is no Worker 2 phase.

## Plan (Worker 1)

### Spec status-line re-verification

`docs/SPECS/spec-028-orders-0_0_8.md:1-6` (title / opener / `Status:` / `Owner:` / `Predecessors:`) re-read this pass. The opener already carries the correct posture — "This spec is the final implementation record, not an open build plan", shipped in `0.0.8` as `DONE-028-0.0.8`, with the `0.0.9` version-boundary caveat. Nothing this cycle falsifies. **One clause is now stale by implication** and is in scope only because it names Decision 12's subject: line 6's `Predecessors:` cites the KANBAN card body's "six-layer architecture summary + the Layer 6 fresh-design question, preserved as Decisions without re-litigation". That remains a true statement about what the spec preserved; left unedited.

### The finding, re-verified at HEAD before planning

Worker 0's dispatch was verified independently this pass, and **one half of it is wrong**. Recorded here because the correction changes what Decision 12 may say.

| Claim as dispatched | Verified? | Evidence opened |
|---|---|---|
| `### Decision 12` is titled "Layer 6 and DISTINCT ON deferred to `0.0.9`" and `0.0.9` shipped five versions ago | **yes** | spec:979; `pyproject.toml` version `0.0.14` |
| No card carries `DISTINCT ON` | **yes** | `grep -in "distinct on\|distinct_on" KANBAN.md BACKLOG.md` → 0 lines |
| The to-many fan-out is solved by row-preserving `Min` / `Max` ordering | **yes** | `orders/sets.py::OrderSet._resolve_order_expressions` — `aggregate = models.Min if direction.is_ascending else models.Max`; `annotations[alias] = aggregate(field_path)`; `expressions.append(direction.resolve(alias))`. Gated on `utils/relations.py::path_traverses_to_many`; scalar and to-one paths order directly |
| Shipped `Ordering` is member-for-member strawberry-django's | **yes** | `orders/inputs.py::Ordering` (6 members) vs `~/projects/strawberry-django-main/strawberry_django/ordering.py::Ordering` (same 6 values, different declaration order) |
| graphene-django has no DISTINCT ordering directives | **yes** | `grep -rn "DISTINCT\|distinct_on" .../site-packages/graphene_django/` → 0 lines |
| "Layer 6's other half was … answered by the `0.0.9` connection field's sidecar synthesis" | **PARTLY — the dispatch understates it** | The connection field does consume the sidecar (`connection.py::_synthesized_signature` builds the `orderBy:` argument only `if definition.orderset_class is not None`; `connection.py::_pipeline_sync` / `_pipeline_async` apply it). **But Layer 6's own symbols now exist**: `orders/factories.py::get_orderset_class` + `_dynamic_orderset_cache`, landed at `fd0c7327` (2026-08-16, the DRY cycle) on top of `utils/inputs.py::make_dynamic_set_getter`, replacing the `TODO(spec-028-orders-0_0_8 Decision 12; deferred to 0.0.9)` anchor that stood there since `11d9fbe0`. They have **no source consumer** — `grep -rn "get_orderset_class\|_dynamic_orderset_cache" django_strawberry_framework/` hits only `orders/factories.py` |

**Consequence for the rewrite.** Layer 6 is not "discharged"; it is **decided**. The mechanism shipped as unconsumed plumbing and the *surface* it would serve — auto-generating an `OrderSet` from a field's `Meta`-shaped kwargs without an explicit class — is a **standing non-goal that shipped source cites this Decision for**, twice:

- `orders/factories.py` #"Auto-generation of an ``OrderSet`` from" — "…``Meta.fields`` without an explicit class remains a standing deferred Non-goal (spec-028 Decision 12)."
- `orders/factories.py::get_orderset_class` #"is a standing deferred Non-goal" — "``DjangoConnectionField`` consumes the already-resolved ``Meta.orderset_class`` sidecar directly and does not route through here."

So Decision 12 must **keep** a Layer 6 non-goal (cutting it orphans two source citations) while dropping the version-dated deferral, and must record that the plumbing exists. The DISTINCT ON half, by contrast, is a genuine discharge-by-alternative and stops being a deferral at all.

### DRY analysis

**Helper inventory checked.** Not applicable in the code sense — this pass writes no Python and the writable set contains no `.py` file. The equivalent inventory for a documentation pass was run: every symbol the rewrite names was opened in source (`orders/sets.py`, `orders/inputs.py`, `orders/factories.py`, `connection.py`, `types/base.py`, `utils/relations.py`, `utils/connections.py`) and every claim traced to a line I read, per the cycle's signature-defect rule. Shapes searched: `distinct`, `Min`, `Max`, `orderset_class`, `get_orderset_class`, `_dynamic_orderset_cache`, `DEFERRED_META_KEYS`, `ALLOWED_META_KEYS`, `tiebreak`.

- **Existing patterns reused.** The corrected text reuses `spec-009`'s `### Layer 7` wording for the aggregate rule (`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:731`, R1's `final-accepted` text: "order ascending terms by `Min(path)` and descending terms by `Max(path)`, then order by the alias"), so the two documents assert the same mechanism in the same vocabulary rather than two paraphrases that can drift apart. It also adopts `orders/factories.py`'s own vocabulary for the unconsumed plumbing, so the spec and the module docstring that cites it read as one statement.
- **New shared shape justified.** None. Decision 12 stays the single normative site; every echo site is reduced to a pointer at it, which is the shape the cycle settled on in R1 ("the architecture chapter owns the map, the prior-art chapter cites it").
- **Duplication risk avoided.** The naive fix restates the `Min` / `Max` mechanism at each of the ~10 echo sites. That is exactly how a claim rots unevenly. Only Decision 12 states the mechanism; Non-goals / Borrowing posture / Decision 3 / Decision 4 / Out-of-scope carry one clause plus the anchor.

**Two deliberate non-claims**, cut rather than restated per the cycle's remedy rule:

- *"…and composes with the connection's primary-key tiebreaker."* True at `connection.py` #"as a terminal tiebreaker unless the effective ordering already ends in a", and `spec-009`'s `### Layer 7` says it. It is not load-bearing for Decision 12's contract, and it is precisely the fluent subordinate clause this cycle has been wrong about seventeen times. **Cut.** The two documents do not conflict; spec-028 simply says less.
- *"…decided in `spec-030`'s review round (P1-B)."* Verifiable (`orders/sets.py` docstring cites `spec-030-connection_field-0_0_9 P1-B`; `docs/SPECS/spec-030-connection_field-0_0_9.md:485` confirms). **Cut** anyway: it is provenance, the symbol carries it in its own docstring, and BUILD.md `## Spec rationale extraction` forbids the spec narrating chronology. It would also need a new `[spec-030]` link definition in a file whose link scaffold is otherwise untouched by this pass.

### The heading rename, and why it is safe

The old heading ``### Decision 12 — Layer 6 and DISTINCT ON deferred to `0.0.9` `` is itself the headline false claim, so the rename is the fix, not cosmetics. Renaming moves the anchor, so the blast radius was measured before deciding:

- `grep -c "decision-12--layer-6-and-distinct-on-deferred-to-009" docs/SPECS/spec-028-orders-0_0_8.md` → **20** (the heading is not one of them; it is 20 link uses).
- `grep -rn "spec-028-orders-0_0_8.md#" .` → **0**. No sibling spec, standing doc, terms CSV, or source file cites any spec-028 heading by fragment.
- `grep -rn "decision-12" --include='*.md' …` outside spec-028 → only other specs' own `Decision 12` anchors (`spec-043`, `spec-031`).

So all 20 uses are in-file and update mechanically with the heading. **No Decision is renumbered** (the cycle's standing rule), and `### Decision 3 — Five-layer port plus a deferred Layer 6` keeps its heading: a five-layer port with Layer 6 outside the shipped pipeline is still an accurate description of the ordering pipeline, its body is corrected instead, and renaming it would move a second anchor for no gain.

New heading: `### Decision 12 — No Layer 6 auto-generation and no DISTINCT ON surface`
New anchor: `#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface`

### The revision-log convention — answered

`spec-028` carries a numbered `Revision 1`-`Revision 7` history in its own body, introduced as "kept inline so the spec is self-contained". **This edit does NOT get a revision entry.** Three grounds:

1. Those entries record the spec's **drafting rounds against the maintainer's adversarial reviews**, each naming the finding ids (B1, M3, N-new-3) it closed. A post-ship reconciliation by a residual cycle is not a drafting round and has no finding ids in that series.
2. The build plan's `### Maintainer decision 3` scope limit authorizes "`### Decision 12` and its in-file echo sites" — not a new structural element.
3. `BUILD.md` `## Spec rationale extraction` is explicit that a corrected decision states the contract directly, "no amendment block … as though it had been right from the start". Adding "Revision 8 — the `0.0.9` deferral was reconciled" would re-import exactly the chronology the rewrite removes.

The three existing revision bullets that *describe* Decision 12's contents (lines 10, 34, 43) are a different question and are handled as echo sites below: a bullet stays where it records what a past revision did, and is corrected only where it makes a **present-tense** claim that is false today.

### Sites deliberately NOT edited (recorded, not repaired)

Two are quoted drop-in texts for documents outside the writable set. Editing the quote would break the match with its target, which is a worse defect than the stale claim:

- **spec:1159** — the `## Doc updates` blockquote of the KANBAN past-tense card body, carrying "Layer 6 (dynamic OrderSet generation) deferred to `0.0.9` alongside `DjangoConnectionField` per Decision 12". Verified **verbatim-present** in the live board at `KANBAN.md:3680`, which is DB-backed and out of scope (`### Maintainer decision 3` site 3 authorizes only card 054's two references).
- **spec:1166** — the `## Doc updates` blockquote of the prescribed `CHANGELOG.md` bullet, carrying "(Layer 6 + DISTINCT ON deferred to `0.0.9`)". `CHANGELOG.md` has **0** occurrences of `Layer 6` and **0** of `distinct on`, so the shipped bullet (`CHANGELOG.md:119`) never carried the phrase; the spec quote is a completed build prescription, not a record of shipped text.

Both are reported below for the maintainer / R4.

### Implementation steps

Line numbers are pin-at-write-time; each edit re-anchors on the quoted text.

1. **spec:979 heading** — retitle to `### Decision 12 — No Layer 6 auto-generation and no DISTINCT ON surface`.
2. **spec:981-1015 body** — rewrite as a current contract: keep the KANBAN framing paragraph (it is the question the Decision answers); replace the two "deferral rationale" lists with a Layer 6 half (explicit-`orderset_class` only; `_synthesized_signature` sidecar; unconsumed factory plumbing; the auto-generation non-goal) and a DISTINCT ON half (six-member enum; reference-only `_DISTINCT` members under `START.md`'s parity test; the `Min` / `Max` row-preserving rule; no `Meta.distinct` key, no `distinct_on:` argument); keep an `Alternatives considered (and rejected)` block reframed from deferrals to rejections; **cut** the O1 / O2 forward-compatibility previews (O1 is predicated on a `0.0.9` DISTINCT design that does not exist and additionally mis-states `DEFERRED_META_KEYS`, which no longer contains `orderset_class`; O2's question is answered by the Layer 6 half).
3. **All 20 anchor uses** — `#decision-12--layer-6-and-distinct-on-deferred-to-009` → `#decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface`, applied as one mechanical replacement, count asserted before and after.
4. **Echo sites** — one edit each at 34, 43, 91, 160, 163, 196, 197, 220, 221, 243, 462, 479, 499, 526, 527, 531, 536, 541, 664, 1177, 1178, 1200, 1201, 1214, per the checklist below.
5. **Re-run both gates**, re-derive the anchor set, re-count `path:NN`, and prove non-sweep with `git log --stat`.

### Test additions / updates

None. No source or test file is writable in this cycle, and the pass writes no Python. The mechanism claims are verified by reading the named symbols, which is the only proof available to a documentation pass.

### Implementation discretion items

None. Every wording choice in this pass is a claim about shipped code and was decided against source.

### Dispatched findings checklist

Self-derived: one box per site corrected. Boxes marked **(sweep)** were not in the plan's first enumeration — the shortest-token re-sweep found them after the plan was written, which is why the denominator below is measured rather than asserted.

- [x] spec:979 — heading retitled; "deferred to `0.0.9`" removed from the Decision's own title
- [x] spec:983 — the "**Decision: both Layer 6 and DISTINCT ON ship in `0.0.9`, NOT this card**" line replaced by the current contract
- [x] spec:985-991 — Layer 6 deferral rationale replaced by the explicit-`orderset_class` contract plus the unconsumed-plumbing statement
- [x] spec:993-998 — DISTINCT ON deferral rationale replaced by the row-preserving `Min` / `Max` discharge
- [x] spec:1000-1004 — `Justification` list re-grounded on what shipped
- [x] spec:1006-1010 — `Alternatives considered` reframed from deferrals to rejections
- [x] spec:1012-1015 — O1 / O2 forward-compatibility previews cut (moot; O1 additionally mis-stated `DEFERRED_META_KEYS`, which no longer carries `orderset_class`)
- [x] 20 in-file anchor uses re-pointed at the new fragment (count asserted before, re-counted after: 20 → 0 old / 20 new)
- [x] spec:10 — `Revision 1` bullet: "the **deferred** Layer 6 + DISTINCT ON design questions" → the design questions, un-dated **(sweep)**
- [x] spec:34 — `Revision 2` O1+O2 bullet: present-tense claim about previews that no longer exist
- [x] spec:43 — `Revision 3` N-new-3 bullet: restated `DEFERRED_META_KEYS` contents, false today
- [ ] spec:91 — `Key glossary references`: opened; says the Layer 6 question is "resolved by Decision 12", which is true. **No change needed** (see `### Spec changes made (Worker 1 only)`)
- [x] spec:160 — `Problem statement`: "resolves it by deferring to `0.0.9` alongside the connection field"
- [x] spec:163 — `Problem statement`: "the cookbook's `ASC_DISTINCT` / `DESC_DISTINCT` direction modifiers are deferred to `0.0.9`"
- [x] spec:196 — `Non-goals`: "DISTINCT ON ships as a separate sub-feature in `0.0.9`"
- [x] spec:197 — `Non-goals`: "when `DjangoConnectionField` lands in `0.0.9`, the connection-field card decides"
- [x] spec:200 — `Non-goals`: "Direct consumer-facing implicit generation lands when `DjangoConnectionField` ships in `0.0.9`" **(sweep)**
- [x] spec:220 — `Borrowing posture`: "deferred to `0.0.9` per Decision 12"
- [x] spec:221 — `Borrowing posture`: "Deferred per Decision 12"
- [x] spec:243 — `Explicitly do not borrow`: "deferred … to a separate `Meta.distinct` key + `distinct_on:` argument design in `0.0.9`"
- [x] spec:462 — `Decision 3`: "deferred to `0.0.9` per Decision 12"
- [x] spec:479 — `Decision 3` Layer 6 row: "**DEFERRED TO `0.0.9`**" plus the "`0.0.9` card decides" future tense
- [x] spec:493 — `Decision 3` justification: "Deferring Layer 6 to `0.0.9` is correct because there is no `0.0.8` consumer surface" **(sweep)**
- [x] spec:497 — `Decision 3` rejected alternative: "The `0.0.9` connection field is the consumer; the cache lands with that card" **(sweep)**
- [x] spec:499 — `Decision 3` rejected alternative: "a separate `Meta.distinct` key + `distinct_on:` argument in `0.0.9`"
- [x] spec:524 — `Decision 4` sub-heading "NOT in the parity floor (**deferred**):" **(sweep)**
- [x] spec:526 — `Decision 4` parity table: "deferred per Decision 12"
- [x] spec:527 — `Decision 4` parity table: "deferred per Decision 12"
- [x] spec:531 — `Decision 4` parity table: `_dynamic_orderset_cache` "deferred per Decision 12" — now shipped-but-unconsumed
- [x] spec:536 — `Decision 4` justification: "each deferred item ships in a follow-on card with its own scope"
- [x] spec:541 — `Decision 4` rejected alternative: "the design deserves its own decision space"
- [x] spec:542 — `Decision 4` rejected alternative: "Ship Layer 6 dynamic-factory in **`0.0.8`**" **(sweep)**
- [x] spec:664 — `Decision 5` rejected alternative: "DISTINCT ON deserves its own design space"
- [x] spec:1130 — `Doc updates`, the `docs/GLOSSARY.md` `OrderSet` entry prescription: "five-layer port + Layer 6 deferred to `0.0.9`". **The single most valuable find of the sweep**: the live glossary entry has already been reconciled by a later cycle to "a standing deferred non-goal", so the spec's prescription was stale against its own target. Re-aligned to the shipped wording **(sweep)**
- [x] spec:1177 — `Risks and open questions`: Layer 6 "Preferred answer … deferred to `0.0.9`" plus its fallback
- [x] spec:1178 — `Risks and open questions`: DISTINCT ON "Preferred answer … a separate `Meta.distinct` design lands in `0.0.9`" plus the `0.0.8.1` patch fallback
- [x] spec:1179 — `Risks and open questions`: the enum fallback's "(rather than a separate `Meta.distinct` declaration)" parenthetical, which implied the separate declaration was still the plan **(sweep)**
- [x] spec:1200 — `Out of scope`: Layer 6 "deferred to `0.0.9`"
- [x] spec:1201 — `Out of scope`: DISTINCT ON "deferred to `0.0.9`"
- [x] spec:1214 — `Definition of done` item 5: "`_dynamic_orderset_cache` is **NOT** shipped" — false today; clause cut rather than restated

*Boxes below added by the apply-changes pass (`## Build report (Worker 1, apply-changes pass)`), one per Worker 3 finding. Nothing above this line was altered.*

- [x] **M1** — `orders/sets.py::OrderSet.get_flat_orders` docstring clause corrected under `### Maintainer decision 7`; the inbound-citation population re-derived mechanically and reported at its true size
- [x] **M2** — `spec:1179`'s `_dynamic_orderset_cache` **(deferred)** parenthetical dropped; widened-token sweep re-run over the whole spec and graded
- [x] **L1** — anchor re-count restated as occurrences (20 re-pointed + net-new), corrected in this pass's report rather than in the prior section
- [x] **L2** — the `:34` / `:43` trailing narration removed, resolving the asymmetry with the declined Revision 8 entry
- [x] **L3** — `### Decision 3`'s kept heading: Worker 3's acceptance confirmed; no re-open, residue surfaced to the maintainer

*Boxes below added by apply-changes pass 2 (`## Build report (Worker 1, apply-changes pass 2)`), one per Worker 3 pass-2 finding. Nothing above this line was altered.*

- [x] **M1 (pass 2)** — item 6 corrected on both counts (footprint: a docstring clause **plus** the `del`-line comment, symbol-qualified; framing: Decision 7's "three" was a cardinality about the world, not a scope election), **and** the fix performed at both sites under the amended `### Maintainer decision 7`; the citation population re-derived from a moved corpus (45 occurrences over package + tests + examples + scripts, still four spec-028 citations) with all four now agreeing with the rewritten Decision 12
- [x] **L1 (pass 2)** — the false "the only" reason clause corrected (`spec-028:10` carries a surviving third Decision-12 anchor use in the revision log); the number 27 → 25 stands, re-measured as 25 occurrences on 25 lines
- [x] **L2 (pass 2)** — item 7 now names both sites of the `:734` orphan (`:734` and `:41`), with `:41` recorded as a decided non-edit
- [x] **L3 (pass 2)** — bucket-boundary drift acknowledged; no action requested and none taken (population 109, residual 37, and every total agree between both reconstructions)
- [x] **Note 3 (pass 2)** — the three orphaned deferrals raised as **one** pattern with a sized repo-wide sweep recommendation, not three separate fix requests (item 9 below)

---

## Final verification (Worker 1)

- **Gates.** `check_spec_glossary.py` exit **0** (`OK: 44 terms`), `check_trailing_commas.py --check` exit **0**. Both re-run after the last edit.
- **Glossary term count: 44 → 44.** No cut orphaned a glossary reference.
- **In-page anchors: 161 uses, 21 distinct fragments, 0 unresolved.** Verified with a slug derivation that keeps underscores — the first attempt stripped `_` and produced three false "unresolved" hits (`decision-7--metaorderset_class-…` and two siblings), a reminder that an anchor checker is itself a claim.
- **Link definitions: 103 defs, 0 undefined refs, 1 orphan (`[relay]`).** The orphan is **pre-existing at HEAD** (`grep -c '\]\[relay\]'` over `git show HEAD:<spec>` → 0) and is not flagged by the scaffold gate; not introduced here, and out of this pass's authorized scope to remove. Recorded below.
- **`AGENTS.md` rule 27: raw `path:NN` count 0 → 0.** The spec carried none before and carries none now; every source reference this pass added is symbol-qualified (`path::Qualified.Name`).
- **Byte and line counts: 291,903 → 289,500 bytes (-2,403); 1,362 → 1,354 lines (-8).** Measured with `wc -c -l` before the first edit and after the last.
- **Footprint:** `git diff --numstat -- docs/SPECS/spec-028-orders-0_0_8.md` → `48 56`.
- **Non-sweep proof.** `git log --stat -- docs/SPECS/spec-028-orders-0_0_8.md` → newest commit touching the spec is still `40e4754a` ("docs(specs): move spec companions into docs/SPECS/appx/"), unchanged from the start of the pass; `git log -- <artifact>` is empty. HEAD is `6f8bf818` and did not move during the pass. `git status` alone was not used as the proof.
- **Rationale companion:** `docs/SPECS/appx/` carries `spec-028-orders-0_0_8-terms.csv` and **no** `spec-028-orders-0_0_8-rationale.md`. None was created — this cycle was not authorized to perform a rationale extraction on `spec-028`, and `BUILD.md` `## Spec rationale extraction` makes that its own gated step. The rejected-alternatives blocks therefore **stay in the spec**, reframed in place from deferrals to rejections rather than moved out.
- **Terms CSV:** unchanged and not touched; no term was introduced or retired by this pass (44 → 44).
- **Final status:** `planned` (Worker 0 reads this as "dispatch Worker 3").

### Summary

`spec-028`'s `### Decision 12` no longer promises `DISTINCT ON` and a Layer 6 design to a `0.0.9` release that shipped five versions ago with neither. It now states two contracts that are true today: ordering is **explicit-`Meta.orderset_class` only** — the connection field synthesizes its `orderBy:` argument from the resolved sidecar, the dynamic-`OrderSet` symbols exist as an unconsumed filter-side twin, and auto-generation is a standing non-goal that two source docstrings cite this Decision for — and **no DISTINCT ON surface ships**, because the to-many fan-out it was reached for is prevented inside the ordering itself by the row-preserving `Min` / `Max` aggregate annotation, portably and without `DISTINCT`.

The correction Worker 0's dispatch did not have is that Layer 6's *symbols* landed at `fd0c7327` while its *surface* did not. Writing "the deferral was discharged" for both halves would have replaced one false sentence with another, and would have cut a non-goal that shipped source depends on this Decision to state.

### Spec changes made (Worker 1 only)

**Echo-site sweep denominator (measured, not asserted).** Population = every line in the spec at HEAD matching the shortest distinctive tokens `/distinct|layer[ -]6/i`: **63**. Changed: **46**. Held: **17**. Measured by normalising the anchor rename out of the HEAD text first, so an anchor-only touch is not counted as a substantive change. Every one of the 17 held lines was opened and graded from its matched context, not from its line number. The exact partition, counted after grading: **4** match only the *Decision 3* anchor string (`:16`, `:126`, `:130`, `:1213`; `decision-3--five-layer-port-plus-a-deferred-layer-6` has 6 uses at HEAD and its heading is deliberately kept), **1** is that heading itself (`:460`), **5** are ordinary-English "distinct" / "two distinct" (`:782`, `:1060`, `:1089`, `:1113`, `:1183`), **2** are true comparative statements about the cookbook (`:227`, `:657`), **1** is the KANBAN question quoted inside Decision 12 itself (`:981`), **1** is the `Predecessors:` line (`:6`), **1** is `:91`'s accurate "resolved by Decision 12", and **2** are the quoted drop-ins below (`:1159`, `:1166`). 4+1+5+2+1+1+1+2 = 17.

| Spec site | Change | Reason |
|---|---|---|
| `:979` heading | `Layer 6 and DISTINCT ON deferred to `0.0.9`` → `No Layer 6 auto-generation and no DISTINCT ON surface` | the title was itself the orphaned deferral; 0 inbound external anchor citations, 20 in-file uses updated with it |
| `:981-1007` body | full rewrite as a current contract | `BUILD.md` `## Spec rationale extraction`: no amendment block, no "as of" hedge; every mechanism clause traced to an opened symbol |
| `:1012-1015` (old) | O1 / O2 forward-compatibility previews **deleted** | predicated on a `0.0.9` DISTINCT design that does not exist; O1 additionally asserted `DEFERRED_META_KEYS` carries `orderset_class`, which `types/base.py::DEFERRED_META_KEYS` (`{aggregate_class, fields_class, search_fields}`) contradicts — this card promoted it |
| 20 anchor uses | fragment re-pointed | heading rename |
| `:10`, `:34`, `:43` | revision-log bullets de-dated / re-pointed | see the revision-log answer below |
| `:91` | **no change** | opened; "the one genuinely fresh design question, resolved by [Decision 12]" is true as written. Recorded rather than reworded — a rewrite of accurate text is diff without value |
| `:160`, `:163`, `:196`, `:197`, `:200` | deferral → not-ported / standing-non-goal | the deferral has no target release and no card |
| `:220`, `:221`, `:243` | "deferred per Decision 12" → "not ported per Decision 12" | prior-art chapter cites the architecture chapter; it does not restate the mechanism |
| `:462`, `:479`, `:493`, `:497`, `:499` | Decision 3 body | Layer 6 stated as outside the pipeline with the plumbing named, not as a dated deferral |
| `:524`, `:526`, `:527`, `:531`, `:536`, `:541`, `:542` | Decision 4 parity floor | the sub-heading "NOT in the parity floor (deferred)" and the "each deferred item ships in a follow-on card" justification were both false; the latter clause was **cut**, not rewritten, because any replacement would have been a fresh claim about the decorator surfaces too |
| `:664` | Decision 5 rejected alternative | grounded on reference-only rather than "deserves its own design space" |
| `:1122` | `docs/GLOSSARY.md` prescription re-aligned | the live glossary entry already says "a standing deferred non-goal"; the spec's prescription still said "deferred to `0.0.9`" |
| `:1177`, `:1178`, `:1179` | Risks and open questions | two entries are answered, not open; the third's parenthetical implied a plan that does not exist |
| `:1200`, `:1201` | Out of scope | "tracked elsewhere" was the orphan — nothing tracks either item |
| `:1214` | DoD item 5's `_dynamic_orderset_cache` clause **cut** | false today, and the DoD is not the right home for a Layer 6 statement Decision 12 owns |

**Decisions renumbered: none.** `### Decision 3`'s heading (`Five-layer port plus a deferred Layer 6`) was deliberately kept: its body now states the contract explicitly, "deferred" there carries no version and no phantom owner, and renaming would move a second anchor with 6 in-file uses for no correctness gain.

**Inbound heading-anchored citations to `spec-028`: none.** `grep -rn "spec-028-orders-0_0_8.md#" .` → 0 across the whole repo, so the rename broke nothing outside the file. Source cites this Decision by *name* twice (`orders/factories.py` module docstring and `orders/factories.py::get_orderset_class`), never by anchor, and both citations still resolve because the Decision number is unchanged and its Layer 6 non-goal survives.

**The revision-log convention — answered.** `spec-028` carries `Revision 1`-`Revision 7` inline, introduced as "kept inline so the spec is self-contained". **This edit gets no revision entry.** Those entries record the spec's drafting rounds against the maintainer's adversarial reviews, each naming the finding ids it closed (B1, M3, N-new-3); a post-ship reconciliation by a residual cycle is not such a round and has no ids in that series. `BUILD.md` `## Spec rationale extraction` also forbids re-importing the chronology the rewrite removes. Three existing revision bullets *describe* Decision 12's contents and were treated as echo sites instead: `:10` lost the word "deferred" (a record of the questions rev1 pinned stays true; a record of a deferral does not), and `:34` / `:43` were reworded to record what those reviews did while dropping the present-tense claims about text that no longer exists — `:43`'s in particular restated `DEFERRED_META_KEYS`'s contents, which is false today.

### Recorded for the maintainer / R4 — NOT repaired here

1. **`KANBAN.md:3680`** (card `DONE-028-0.0.8`'s past-tense body) still says "Layer 6 (dynamic OrderSet generation) deferred to `0.0.9` alongside `DjangoConnectionField` per Decision 12 of `docs/spec-028-orders-0_0_8.md`". DB-backed and out of scope — `### Maintainer decision 3` site 3 authorizes only card 054's two references. The spec's `:1159` blockquote of that body was left **verbatim** for the same reason: editing a quote so it no longer matches its target is a worse defect than the stale claim.
2. **`spec-028:1166`**, the prescribed `CHANGELOG.md` bullet, quotes "(Layer 6 + DISTINCT ON deferred to `0.0.9`)". The shipped `CHANGELOG.md:119` never carried the phrase (`grep -ci "layer 6\|distinct on" CHANGELOG.md` → 0), so the quote is a completed build prescription rather than a record of shipped text. Left as-is; `CHANGELOG.md` is not writable this cycle.
3. **`docs/GLOSSARY.md`'s `OrderSet` entry** closes with "so no dynamic order factory is shipped". Since `fd0c7327` that is imprecise: `orders/factories.py::get_orderset_class` and `_dynamic_orderset_cache` **do** exist, with no caller. The reconciled spec says "ships as the filter-side twin … no package path calls either one". The glossary is DB-generated and belongs to item R3.
4. **A second orphaned deferral in `spec-028`, outside R2's scope.** `:195` (`## Non-goals`) and `:1191` (`## Out of scope`) defer **`DjangoListField` orderBy-argument integration** to `0.0.9`. `django_strawberry_framework/list_field.py` contains zero occurrences of `order_by`, `orderset`, or `filterset`, and no card in `KANBAN.md` / `BACKLOG.md` names it — the same defect shape R2 was dispatched for, in the same document. `### Maintainer decision 3`'s scope limit names `### Decision 12` and its echo sites only, so it is reported, not fixed.
5. **Pre-existing orphaned link definition** `[relay]: ../../django_strawberry_framework/types/relay.py` in `spec-028`'s bottom block — 0 uses at HEAD, unrelated to Decision 12, not flagged by the scaffold gate. Left so the diff stays inside the authorized scope.

---

## Review (Worker 3)

Read-only audit at HEAD `6f8bf818` (unmoved across the whole pass; re-derived before and after). Every number
in the plan and `## Final verification` was independently re-measured rather than accepted; the reproductions
are listed under `### What looks solid`. `### Failability proofs` and `### Hot-path budget` are **not
applicable** — this pass writes no Python, introduces no boundary/guard/gate/rejection path, and touches no
hot path, so there is nothing to mutate and no before/after number to carry.

### High:

None.

### Medium:

#### M1 — a THIRD shipped-source citation of Decision 12 exists, and the rewrite falsifies it

`django_strawberry_framework/orders/sets.py:278-279`, inside `orders/sets.py::OrderSet.get_flat_orders`'s
docstring:

```django_strawberry_framework/orders/sets.py:278
- cookbook's DISTINCT ON tuple-half dropped (spec-028 Decision 12
  -- DISTINCT ON deferred to ``0.0.9``).
```

`## Final verification` states: *"Source cites this Decision by **name** twice (`orders/factories.py` module
docstring and `orders/factories.py::get_orderset_class`)."* Measured — `grep -rn "spec-028.*Decision 12"
--include='*.py' django_strawberry_framework/ examples/ tests/ scripts/` returns **three** hits, not two, and
the third is the only one the rewrite breaks. `orders/sets.py` is **clean at HEAD**
(`git status --porcelain django_strawberry_framework/orders/` → empty), so this is shipped text, not a
concurrent session's working copy.

Why it matters: this is the exact shape the pass's own contract calls out. The docstring attributes
"DISTINCT ON deferred to `0.0.9`" to Decision 12; Decision 12 now says the opposite — `:995` *"there is no
`distinct_on:` argument"*, and the rejection *"Ship the cookbook's `ASC_DISTINCT` / `DESC_DISTINCT` plus the
`apply_distinct` port. **Rejected**"*. The docstring's substantive claim ("tuple-half dropped") survives; only
the trailing attribution gloss is now contradicted by the authority it names. The pass verified the inbound
**anchor** population exhaustively and got 0 (correct — see `### What looks solid`), but the inbound **name**
population was asserted at two without the corresponding grep, and it is the name population that the rename
does not protect.

Recommended change (both halves are Worker 1's, and neither edits source — source is not writable this cycle):

1. Correct the "twice" claim in `## Final verification` to three, naming `orders/sets.py::OrderSet.get_flat_orders`.
2. Add a sixth entry to `### Recorded for the maintainer / R4`: the docstring's `-- DISTINCT ON deferred to
   ``0.0.9`` ` gloss should lose that clause (the `(spec-028 Decision 12)` citation itself stays and still
   resolves). Five other unrepairable sites are recorded there; this one is materially more urgent than any of
   them, because it is the only surviving assertion of the retired deferral that a reader meets **inside the
   package** rather than in a doc.

Test expectation: none — documentation-only, no behavior affected.

#### M2 — an in-scope Decision-12 echo site survives, and now contradicts the rewritten spec

`docs/SPECS/spec-028-orders-0_0_8.md:1179` (`## Risks and open questions`, "Glossary entry parity for internal
symbols") still reads:

```docs/SPECS/spec-028-orders-0_0_8.md:1179
`OrderSetMetaclass`, `OrderArgumentsFactory`, `_dynamic_orderset_cache` (deferred), `get_flat_orders` are
internal symbols not currently in [`docs/GLOSSARY.md`][glossary].
```

`_dynamic_orderset_cache` is not deferred. The same document now says so three times, in text this pass wrote:
`:197` ("the dynamic-factory symbols that ship as the filter-side twin have no caller"), `:479`
("`orders/factories.py` carries the dynamic-`OrderSet` symbols as the filter-side twin"), and `:988` ("ship as
the filter-side twin ... No package path calls either one"). The spec now contradicts itself on Decision 12's
own subject.

This is squarely in scope. `### Maintainer decision 3` site 2 authorizes "`### Decision 12` and its in-file
echo sites"; the line is a Decision-12 echo site in the very section whose three neighbours (HEAD `:1177`,
`:1178`, `:1179`) this pass edited, and it is the **same defect** already fixed at HEAD `:1214` — where the
DoD's "`_dynamic_orderset_cache` is **NOT** shipped" clause was correctly cut for exactly this reason.

Root cause, and the reason it is worth naming: the sweep's population is `/distinct|layer[ -]6/i`, and this
line contains neither token — it names only the symbol. So the measured denominator of 63 is a denominator of
*lines carrying those two tokens*, not of Decision-12 echo sites, and the gap is invisible from inside the
sweep. I re-ran the population with a widened token set (`dynamic[ _-]?orderset|orderset_factories|
auto-generat|0\.0\.9|decision.12|apply_distinct|ASC_DISTINCT|DESC_DISTINCT`) and diffed against the 63: **29
lines matched the wider set and fell outside the population**. Twenty-eight are benign (inside the fully
rewritten `:981-1015` body, or `0.0.9` connection-field / `DjangoListField` statements outside Decision 12's
subject, or `DEFERRED_META_KEYS` prose about a real constant). `:1179` is the one live stale site among them.

Recommended change: drop the `(deferred)` parenthetical. The bullet's own point — these are internal symbols
with no glossary entry, keep them internal — is unaffected, and `_dynamic_orderset_cache` still belongs in the
list. No new claim is introduced, which is the cheapest correct fix available here.

Test expectation: none — documentation-only.

### Low:

#### L1 — the anchor re-count in the checklist does not reproduce

`### Dispatched findings checklist`: *"20 in-file anchor uses re-pointed at the new fragment (count asserted
before, re-counted after: 20 → 0 old / 20 new)"*. Measured by occurrence (not by line — `grep -c` counts
lines and the two diverge here):

| Measure | HEAD | Now |
|---|---|---|
| `decision-12--layer-6-and-distinct-on-deferred-to-009` | 20 | 0 |
| `decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface` | 0 | **27** |

All 27 sit on added lines; 20 removed lines carried the old fragment. So the rewrite re-pointed 20 and
**added 7 net-new** links to Decision 12 (the echo sites that previously said "per Decision 12" in bare prose
now link it — a genuine improvement). The spec is correct; the recorded post-count is not. Recommended change:
state it as "20 re-pointed + 7 net-new = 27". Worth correcting because the row reads as a closed
before/after identity, which is the shape a later pass will trust rather than re-derive.

#### L2 — two revision bullets now narrate the reconciliation they were meant to stop narrating

`:34` gained *"Both questions are settled in Decision 12's current text, which carries no preview"* and `:43`
gained *"The preview is gone; Decision 12 states the key-set answer for both names directly."* Both are true
(verified against the current `:979-1007`). But `### The revision-log convention — answered` declines a
Revision 8 entry on the ground that it would *"re-import exactly the chronology the rewrite removes"*, and
these two clauses do a smaller version of the same thing — they tell the reader what the text used to contain
and no longer does.

Recommended change (optional; the call is Worker 1's): end `:34` after "…the then-open Layer 6 path choice."
and `:43` after "…added a staleness caveat." Both then record only what that review round did, which is what a
revision log is for, and "then-open" already signals the historical frame. Filed Low rather than Medium
because nothing false is asserted and the reasoning behind the longer form is legible.

#### L3 — `### Decision 3`'s kept heading reads against its own corrected body

`### Decision 3 — Five-layer port plus a deferred Layer 6` (`:460`) is retained while its body now says
**"Layer 6 — Memoized dynamic `OrderSet` generation — NOT PART OF THE PIPELINE"** (`:479`) and Decision 12
calls auto-generation a standing non-goal. "Deferred" in the heading is therefore softer than the contract
underneath it.

**I accept the decision as made** — the rejection reason is recorded (moving a second anchor with 6 in-file
uses, re-derived below as 6 → 6 unchanged), the word carries no version and no phantom owner, and shipped
source uses the same vocabulary (`orders/factories.py`: "remains a standing **deferred** Non-goal"). Recorded
so a later pass does not re-open it as a fresh finding, and so the maintainer sees the residue explicitly.

### DRY findings

None to consolidate; two to affirm.

- **The one-normative-site shape is right and is the pass's main DRY win.** Decision 12 is the sole site
  stating the `Min` / `Max` mechanism, the six-member enum roster, and the key-set answer; all 27 anchor uses
  are pointers. I checked the alternative the plan rejected — restating the mechanism at each echo site —
  against the evidence in this document: `:1179` (M2) is a live demonstration of what uneven restatement costs,
  and it is the only site in the file that restates a Decision-12 fact in its own words instead of pointing.
- **Two deliberate non-claims, both correctly cut.** The primary-key-tiebreaker clause is true
  (`connection.py` #"as a terminal tiebreaker unless the effective ordering already ends in a") and the
  `spec-030` P1-B provenance is true (`orders/sets.py::OrderSet._resolve_order_expressions` carries it in its
  own docstring). Cutting both is correct on the cycle's own rule: the first is a fluent subordinate clause of
  exactly the class this cycle has been wrong about seventeen times, and the second is provenance the symbol
  already owns. spec-028 saying **less** than spec-009 is agreement, not divergence.
- **Existence challenge — raised and answered against the code, not deferred.** `get_orderset_class` /
  `_dynamic_orderset_cache` are an abstraction with **zero production callers**, which is the exact profile
  that normally earns a deletion recommendation. It does not here: they are not an indirection layer with one
  inlined caller, they are one half of a deliberately symmetric pair whose shared skeleton lives at
  `utils/inputs.py::make_dynamic_set_getter` (the filter twin `get_filterset_class` **is** consumed), so
  deleting the order half re-specialises a currently-generic helper and buys nothing. Not escalated. The spec
  now states this disposition accurately, which is the change under review.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are
unchanged. No source file is writable this cycle and none was written; the pass's entire footprint is
`docs/SPECS/spec-028-orders-0_0_8.md` (`git diff --numstat` → `48 56`, reproduced exactly).

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

Verified separately, since the spec quotes a prescribed CHANGELOG bullet at `:1158`: `grep -ci "layer 6|distinct
on" CHANGELOG.md` → **0**, so the shipped changelog never carried the phrase and the spec's blockquote is a
completed build prescription, not a record of live text. Leaving it verbatim is correct.

### Documentation / release sanity

Applies (the pass touches an archived spec). All checks pass.

- **Version strings / statuses / card IDs.** `Status:` line, the `DONE-028-0.0.8` card reference, and the
  `0.0.8` shipped framing are untouched and remain correct against `pyproject.toml` `0.0.14`. No Decision was
  renumbered: all thirteen `### Decision N` headings are byte-identical to HEAD except `### Decision 12`, and
  every one is at its HEAD line number (only `### Decision 13` shifts, 1017 → 1009, from the O1/O2 deletion).
- **Verbatim drop-ins confirmed against their targets.** `:1151`'s KANBAN blockquote — the exact string
  "Layer 6 (dynamic OrderSet generation) deferred to `0.0.9` alongside `DjangoConnectionField` per Decision 12"
  matches `KANBAN.md:3680` **1 for 1**. Leaving both drop-ins unedited is correct: editing a quote so it no
  longer matches its target is the worse defect, and `KANBAN.md` is DB-backed and out of scope.
- **Prescription vs live target.** The `docs/GLOSSARY.md` `OrderSet` prescription at `:1122` went from
  "five-layer port + Layer 6 deferred to `0.0.9`" to "with Layer 6 (auto-generated ordersets) a standing
  non-goal per [Decision 12]". The live entry (`docs/GLOSSARY.md:1434`) reads "Layer 6 ... is a standing
  deferred non-goal". They now agree. This is a prescription body, not a fenced drop-in, so no
  character-for-character requirement applies. Catching this stale-against-its-own-target prescription was the
  most valuable find of the sweep, as the plan claims.
- **No obsolete staging language introduced.** No script-rendered doc is touched, so the docstring-staging rule
  does not engage.
- **Links.** 103 definitions, **0 undefined refs**, **1 orphan** (`[relay]`) — reproduced with a checker that
  strips fenced blocks and inline code spans. The orphan is **pre-existing at HEAD** (`[relay]:` def present,
  0 uses after code-span stripping) and is not flagged by the scaffold gate, which passes with it in place.
  Correctly recorded rather than repaired.

### What looks solid

Every mechanism claim in the rewritten Decision 12 traces to a symbol I opened. Where a file was dirty from the
concurrent package-source session I re-read the claim at **HEAD** as well, since a claim about shipped code that
holds only in someone's working copy is not shipped:

- **`Min` / `Max` over to-many paths** — `orders/sets.py::OrderSet._resolve_order_expressions`:
  `aggregate = models.Min if direction.is_ascending else models.Max`; `annotations[alias] = aggregate(field_path)`;
  `expressions.append(direction.resolve(alias))`; gated by `if _path_traverses_to_many(model, field_path)`, with
  the `else` arm ordering scalar/to-one paths directly. `orders/sets.py` is clean at HEAD. The symbol path the
  spec cites, `utils/relations.py::path_traverses_to_many`, is the **public** name; `orders/sets.py:42` imports
  it under a `_`-prefixed alias, so the spec cites the right symbol at the right module.
- **Six-member `Ordering`** — `orders/inputs.py::Ordering` = `ASC`, `DESC`, `ASC_NULLS_FIRST`, `ASC_NULLS_LAST`,
  `DESC_NULLS_FIRST`, `DESC_NULLS_LAST`; `~/projects/strawberry-django-main/strawberry_django/ordering.py::Ordering`
  declares the same six values (different order). "The same six members" is exact.
- **No `Meta.distinct` / `distinct_on:` surface** — `types/base.py`: `DEFERRED_META_KEYS` =
  `{aggregate_class, fields_class, search_fields}`; `ALLOWED_META_KEYS` = 17 keys, neither `distinct` nor
  `distinct_class` among them; the typo guard is real (`unknown = sorted(declared - ALLOWED_META_KEYS -
  DEFERRED_META_KEYS)` → raise). Verified at HEAD too, since `types/base.py` is dirty. Zero `distinct_on` /
  `Meta.distinct` / `distinct_class` occurrences package-wide.
- **Sidecar-gated `orderBy:`** — `connection.py::_synthesized_signature`: `if definition.orderset_class is not
  None:` guards the whole `CONNECTION_ORDER_KWARG` parameter append; `_pipeline_sync` / `_pipeline_async` apply
  `definition.orderset_class.apply_sync` / `apply_async`. `connection.py` is dirty; all three re-verified at
  HEAD.
- **`get_orderset_class` has no production consumer** — re-derived independently, not from the plan's grep:
  the only importers repo-wide are `tests/utils/test_inputs.py` and `tests/orders/test_factories.py`. I also
  checked the shapes that defeat a name grep — no `import *` anywhere in `orders/`, and
  `orders/__init__.py` deliberately does not re-export the factory surface. `factories.py` is built on
  `utils/inputs.py::make_dynamic_set_getter` as claimed (verified at HEAD).
- **graphene-django carries no DISTINCT ordering directive** — 0 case-sensitive `DISTINCT` / `distinct_on`
  hits. A case-insensitive sweep finds 6, all `.distinct()` queryset calls in filter/test code; none is an
  ordering directive. The claim survives the stricter grep.
- **The non-goal is preserved** (the check that would have been a High). `orders/factories.py` cites this
  Decision for the auto-generation non-goal twice — module docstring #"Auto-generation of an ``OrderSet`` from"
  and `get_orderset_class` #"is a standing deferred Non-goal" — and the rewrite states it at `:988` in bold,
  plus at `:200` (Non-goals) and `:479` / `:497` (Decision 3). Neither the retitle nor any echo edit removed
  it; both source citations still resolve.
- **The retitle is safe.** `grep -rn "spec-028-orders-0_0_8.md#" .` → 2 hits, **both inside this artifact
  quoting its own grep string**; 0 real inbound fragment citations repo-wide. Old fragment: 0 remaining
  anywhere outside this artifact. `### Decision 3`'s anchor: **6 occurrences at HEAD, 6 now** — unchanged, so
  keeping that heading cost nothing. In-page anchors re-derived with an independent slug function that keeps
  underscores: **161 uses, 21 distinct fragments, 0 unresolved, 0 duplicate heading slugs**.
- **The denominator reproduces member-for-member.** Population `/distinct|layer[ -]6/i` at HEAD = **63**;
  normalising the rename out of HEAD before comparing gives **46 changed / 17 held**. My held set is identical
  to the plan's enumeration line-for-line (`6, 16, 91, 126, 130, 227, 460, 657, 782, 981, 1060, 1089, 1113,
  1159, 1166, 1183, 1213`), and the stated partition (4 + 1 + 5 + 2 + 1 + 1 + 1 + 2) sums correctly. I opened
  and graded all 17 rather than the tally: the five ordinary-English rows are genuinely ordinary ("two distinct
  module-import paths", "two distinct input types", "accidentally `.distinct()`s the queryset"); `:227` and
  `:657` are true comparatives about the cookbook that Decision 12 now agrees with; `:91`'s "resolved by
  Decision 12" is true and re-wording it would be diff without value. **No stale site is misfiled as held.**
- **Agreement with `spec-009`.** `### Layer 7` carries no `ASC_DISTINCT` / `DESC_DISTINCT` / `DISTINCT ON`
  (the whole spec has 3 "distinct" hits, all ordinary English), and states the same rule in the same words:
  *"order ascending terms by `Min(path)` and descending terms by `Max(path)`, then order by the alias"* plus
  the same six-member enum. Neither document claims what the other denies; spec-028 simply says less.
- **The revision-log call is right.** `BUILD.md` `## Spec rationale extraction` is explicit — *"no amendment
  block, no retraction paragraph, no 'as of review round N' hedge ... as though it had been right from the
  start"*. A "Revision 8 — the `0.0.9` deferral was reconciled" entry is precisely an amendment block, and the
  existing Revision 1-7 series records drafting rounds against adversarial reviews with finding ids (B1, M3,
  N-new-3) that a residual cycle has none of. Handling the three present-tense bullets as echo sites is the
  correct disposition; `:10` dropping "deferred" and `:43` dropping the false `DEFERRED_META_KEYS` restatement
  are both improvements. (L2 is a trim on the *execution*, not a challenge to the call.)
- **Rejected-alternatives reframing reads correctly.** With no `-rationale.md` for `spec-028` — correctly not
  created, that being its own gated step — the blocks stay in the spec, and they now read as rejections rather
  than deferrals: "Rejected — no consumer needs it", "Rejected — the enum shape conflates a direction with a
  partition". No "for now", no target version, no phantom owner. The spec reads as a current contract with no
  amendment block and no "as of 0.0.9" hedge anywhere.
- **The four out-of-scope records I could check are all correctly out of scope.** `list_field.py` has zero
  `order_by` / `orderset` / `filterset` occurrences and no card names the deferral (item 4 — a genuinely
  second orphaned deferral, correctly reported not fixed under the scope limit); `KANBAN.md:3680` is DB-backed
  and R3 authorizes only card 054 (item 2); the two drop-ins are verified against their targets above (item 3);
  the GLOSSARY "so no dynamic order factory is shipped" clause is present and is now imprecise exactly as
  described (item 4 in the list / item 3 numbering), and the glossary is DB-generated, so R3 owns it.
- **Gates and provenance.** `check_spec_glossary.py --spec docs/SPECS/spec-028-orders-0_0_8.md` → exit 0,
  `OK: 44 terms`. `check_trailing_commas.py --check` → exit 0. Terms CSV untouched (absent from
  `git status`; 45 lines = 44 terms + header), so 44 → 44 holds by construction. Raw `path:NN`: 0 → 0 with an
  extension-aware regex. Bytes 291,903 → 289,500 and lines 1,362 → 1,354 both reproduce to the byte.
  Non-sweep proof re-derived: newest commit touching the spec is still `40e4754a`, `git log` for this artifact
  is empty, HEAD `6f8bf818` at both ends of my pass.

### Temp test verification

No pytest run — this pass ships no Python and there is no behavior to exercise. Read-only verification scripts
under `docs/builder/temp-tests/r2/` (gitignored):

- `anchors.py` — independent in-page anchor resolver with its own slug derivation (keeps `_`, strips fences,
  code spans, emphasis, and both link forms). Confirmed 161 / 21 / 0 and no duplicate heading slugs.
- `links.py` — link-definition auditor; strips fenced blocks **and** inline code spans before counting uses.
  Confirmed 103 defs / 0 undefined / 1 orphan.
- `denom.py` — reproduces the 63 / 46 / 17 partition by normalising the rename out of the HEAD text, and dumps
  all 17 held lines for grading. This is the instrument that confirmed the held set member-for-member.
- `outside.py` — the check the sweep could not do on itself: widens the token set and reports every line
  matching it that falls **outside** the 63-line population. This is what surfaced M2.
- `diff-u0.txt`, `head.md` — captured `git diff -U0` and the HEAD spec text.

Disposition: **kept under `docs/builder/temp-tests/r2/` for the re-review pass**, then deleted with the cycle
(the directory is gitignored, so nothing leaks into a commit). None is a promotion candidate — there is no
behavior to pin, so none can catch a behavior bug. `outside.py` is the one worth re-running after Worker 1's
revision, since it is the instrument that found M2; its *method* — re-run the sweep population with a widened
token set and grade the difference — is the transferable part and is carried into worker memory.

### Notes for Worker 1 (spec reconciliation)

1. **M1 and M2 are both yours to close** — the first as an artifact correction plus a maintainer record, the
   second as a one-parenthetical spec edit inside the authorized scope. Neither needs a maintainer decision.
2. **Escalated: the source fix behind M1 is out of this cycle's writable set.**
   `orders/sets.py::OrderSet.get_flat_orders`'s docstring gloss "`-- DISTINCT ON deferred to ``0.0.9``.`" is
   now contradicted by the Decision it cites. Resolution paths for the maintainer: **(a)** fold the one-clause
   docstring fix into R2 by widening the scope limit (smallest possible source diff — delete the gloss, keep
   the `(spec-028 Decision 12)` citation); **(b)** card it alongside the `DjangoListField` orphan in item 4,
   both being the same defect shape in the same subsystem; or **(c)** hand it to R4, which already owns the
   cross-reference audit "in all three cross-reference directions" and would naturally sweep source→spec
   citations. My recommendation is **(a)** — the cycle's own thesis is that a claim left un-fixed because it
   sits one document over is how the `0.0.9` deferral survived five versions, and the fix here is one clause.
3. **The sweep-population lesson is worth carrying to R4 explicitly.** R4's staged-anchor sweep will define a
   population the same way. The finding is not "the regex was wrong" — it is that a token-defined population
   and a subject-defined population are different things, and only the second is what a reconciliation
   promises. Cheap remedy: run the population twice with different token sets and grade the difference, which
   is a two-minute check that found M2 here.
4. **`### Decision 3`'s heading (L3) is residue you should surface to the maintainer, not re-fix.** Keeping it
   was the right call on anchor cost; the maintainer may still prefer the body and heading to agree, and that
   is a decision, not a defect.
5. **Non-finding, recorded so it is not re-raised.** `:1171`'s `Ordering`-enum fallback still says a follow-up
   card *could* add `ASC_DISTINCT` / `DESC_DISTINCT` if consumers ask, while Decision 12 rejects them. I graded
   this a **note, not a finding**: the section's own preamble says every item carries "a fallback if
   implementation reveals the preferred answer is wrong", so a demand-contingent revisit of a rejection is the
   section's declared shape, not a competing plan. It asserts nothing false about shipped code.

### Review outcome

`revision-needed` — on M2 (an in-scope, unrepaired, unrecorded stale echo site that leaves the reconciled spec
contradicting itself on Decision 12's own subject) and M1 (a false count in `## Final verification`, and the
one surviving in-package assertion of the retired deferral going unrecorded). Both are small and neither
challenges the pass's substance: the rewritten Decision 12 is correct at every symbol I opened, the retitle is
provably safe, the denominator reproduces member-for-member with all 17 held rows correctly graded, and both
documents now agree. Re-review should be short.

---

## Build report (Worker 1, apply-changes pass)

Both Mediums and all three Lows closed. Per this cycle's `### Deviation 3` corollary the fix pass for a
Worker-1-exclusive deliverable is Worker 1's, so this section replaces a Worker 2 build report; it appends at
top level and edits no prior section. `Status:` returns to `planned`, which Worker 0 reads as "dispatch
Worker 3".

**One correction to a finding, and it is the pass's main result: the inbound-citation population is FOUR, not
three.** M1 is right that the pass asserted a name population without a grep, and right about the site it
names. Its own replacement number was produced by `grep -rn "spec-028.*Decision 12" --include='*.py'`, which
requires the token `spec-028` on the same physical line — and `orders/inputs.py` spells its citation
`Spec Decision 12`. The finding therefore reproduces the very defect it diagnoses one spelling further out.
The whole population is produced below from the shortest distinctive token, as the dispatch required.

### M1 — the Decision-12 citation population, produced mechanically

```shell
$ grep -ro "Decision 12" django_strawberry_framework/ | wc -l
      20
$ grep -rn "Decision 12" django_strawberry_framework/orders/
django_strawberry_framework/orders/inputs.py:196:    forward-compatibility (Spec Decision 12 -- a future DISTINCT ON
django_strawberry_framework/orders/factories.py:22:Non-goal (spec-028 Decision 12).
django_strawberry_framework/orders/factories.py:150:    (spec-028 Decision 12). ``DjangoConnectionField`` consumes the
django_strawberry_framework/orders/sets.py:278:        - cookbook's DISTINCT ON tuple-half dropped (spec-028 Decision 12
```

Twenty package-wide occurrences of the bare token; sixteen belong to **other** specs' Decision 12 (`spec-039`
in `__init__.py` / `rest_framework/`, `spec-046` in `consumers.py`, `spec-032` and `spec-036` in
`types/finalizer.py` / `mutations/sets.py`) and were opened and discarded. **Four cite `spec-028`
`### Decision 12`, all four inside `orders/`.** Graded against the rewritten Decision:

| Citation | Claim | Agrees with the rewritten Decision 12? |
|---|---|---|
| `orders/factories.py` #"Auto-generation of an ``OrderSet`` from" | auto-generation "remains a standing deferred Non-goal" | **yes** — `:988` states the same non-goal in bold; "deferred" here carries no version and no owner, the same reading Worker 3 accepted at L3 |
| `orders/factories.py::get_orderset_class` #"is a standing deferred Non-goal" | the auto-`OrderSet` surface that would call it is a standing deferred non-goal; the connection field consumes the sidecar directly | **yes** — `:986` and `:988` state both halves |
| `orders/sets.py::OrderSet.get_flat_orders` #"cookbook's DISTINCT ON tuple-half dropped" | the tuple-half is dropped because DISTINCT ON is deferred to `0.0.9` | **was no** — corrected in this pass under `### Maintainer decision 7` |
| `orders/inputs.py::convert_order_field_to_input_annotation` #"forward-compatibility (Spec Decision 12" | the two unused parameters are kept because "a future DISTINCT ON extension or per-type direction enum in ``0.0.9`` would consult them" | **NO — still false, and outside the authorized clause.** Recorded below as item 6 |

**The one clause this pass was authorized to write** (`django_strawberry_framework/orders/sets.py`,
`OrderSet.get_flat_orders` docstring, second line of the `- cookbook's DISTINCT ON tuple-half dropped` bullet):

- before: `          -- DISTINCT ON deferred to ``0.0.9``).`
- after: `          -- no DISTINCT ON surface ships).`

The substantive claim ("tuple-half dropped") and the `(spec-028 Decision 12)` citation are untouched; only the
attribution gloss changes, and it now quotes the Decision's own heading vocabulary (`### Decision 12 — No
Layer 6 auto-generation and no DISTINCT ON surface`) rather than asserting anything the Decision does not say.
Footprint `git diff --numstat -- django_strawberry_framework/orders/sets.py` → `1 1`. No behavior change, no
signature change, no test change, no other docstring, no other file.

**Concurrency and lint.** `git status --porcelain django_strawberry_framework/orders/sets.py` → empty both
immediately before and immediately after the edit, so the file was not concurrently dirty and this pass's
1-line diff is the whole of it. `uv run ruff format` and `ruff check --fix` were run **scoped to that one
file** (never `.`): "1 file left unchanged", "All checks passed!".
`uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/orders/sets.py` → exit 0,
so the R1c caveat (stop rather than run the auto-fixing form on a concurrent session's line) never engaged.
Line length: the rewritten line is 42 characters, well inside 100.

### M2 — the widened sweep, re-run and graded by me

The transferable half of the finding is accepted without reservation: a **token-defined population is not a
subject-defined population**, and `/distinct|layer[ -]6/i` could never have contained `:1179`, which names only
the symbol. The fix landed:

```
:1179 before  `OrderSetMetaclass`, `OrderArgumentsFactory`, `_dynamic_orderset_cache` (deferred), `get_flat_orders` are internal symbols …
:1179 after   `OrderSetMetaclass`, `OrderArgumentsFactory`, `_dynamic_orderset_cache`, `get_flat_orders` are internal symbols …
```

Only the parenthetical is removed, so the bullet's own point (these stay internal) is untouched and no new
claim is introduced.

Re-run of the check, with the token set widened **past** Worker 3's — its eight tokens plus bare `distinct`,
`layer 6`, `deferred`, `defer `, and `window`, case-insensitive — over the **current** spec, then every hit
opened and graded from its matched context rather than its line number:

```shell
$ grep -cEi 'dynamic[ _-]?orderset|orderset_factories|auto-generat|0\.0\.9|decision.12|apply_distinct|ASC_DISTINCT|DESC_DISTINCT|distinct|layer[ -]6|deferred|defer |window' docs/SPECS/spec-028-orders-0_0_8.md
109
```

**A first draft of this section put the population at 88 from memory of the earlier list; the measured figure
is 109.** Recorded rather than quietly corrected, because it is this cycle's own signature defect (a number
written before it was measured) reappearing inside the section whose whole subject is measuring populations
properly. Every figure below was emitted by a bucketing script, and the script prints an `UNCLASSIFIED`
residual so no line can be waved through:

```
 15  D12 body (979-1007)
 25  cites the rewritten D12 by anchor
 21  DEFERRED_META_KEYS / Meta-key promotion prose
  9  revision log / header (3-68)
  1  spec-027's own Decision 12 (:1019)
  1  quoted drop-in blockquote (:1158)
 37  UNCLASSIFIED -> opened and graded one by one, below
total=109 population=109
```

The 25-line anchor bucket independently reproduces L1's occurrence count of 25 — one use per line, no line
carrying two. The 37 residual lines, graded from their printed context:

- **11** are `0.0.9` / `0.0.10` version labels on surfaces that genuinely shipped at those versions
  (`:94`, `:161`, `:194`, `:761`, `:875`, `:977`, `:1187`-`:1190`, `:1195`), or rejected alternatives recording
  a `0.0.9` option that lost. Historical and true.
- **21** are ordinary English, cookbook comparatives, slice-checklist rows, and test-plan lines
  (`:105`, `:126`, `:130`, `:227`, `:329`, `:458`, `:536`, `:542`, `:657`, `:749`, `:782`, `:1052`, `:1057`,
  `:1081`, `:1105`, `:1153`, `:1171`, `:1174`, `:1175`, `:1179`, `:1205`). `:1179` is the M2 fix, now benign —
  it stays in the population because it still names `_dynamic_orderset_cache`, which is the point.
  `:1171` is Worker 3's recorded non-finding (the `Ordering`-enum demand-contingent fallback); re-graded here
  and confirmed a note, not a finding.
- **2** are `### Decision 3`'s kept heading (`:460`) and Layer 3's "deferred expansion", which is the shipped
  lazy-expansion mechanism's own name (`:468`) — not a deferral.
- **2** are the `DjangoListField` orderBy orphan already recorded as item 4 (`:195`, `:1191`).
- **1** is a **newly surfaced** orphan at `:734`, below.

11 + 21 + 2 + 2 + 1 = 37. **No second stale Decision-12 site exists.**

**The widened sweep also surfaced one hit the previous sweep could not, and it is out of scope:** `:734`
(`### Decision 8` step 4) defers the position-side-channel leak-closing work "likely to a sibling `0.0.9`
ordering-permissions card". `grep -in "ordering-permission\|position-side-channel\|side-channel" KANBAN.md
BACKLOG.md` → **0 lines**, so no card carries it and `0.0.9` shipped five versions ago. That is the **same
defect shape R2 was dispatched for, in the same document, for the third time** — Decision 8's subject, not
Decision 12's, so `### Maintainer decision 3`'s scope limit does not reach it. Recorded below as item 7. The
line is partly self-aware ("the work has not been carved into a card yet"), which is why it is a report and
not a Medium.

### L1 — the anchor count, restated as occurrences

`grep -c` counts lines; `grep -o | wc -l` counts occurrences, and the two diverge here. Measured both ends:

| Measure | HEAD | After the perform pass | After this pass |
|---|---|---|---|
| `decision-12--layer-6-and-distinct-on-deferred-to-009` | 20 | 0 | 0 |
| `decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface` | 0 | 27 | **25** |

So the perform pass **re-pointed 20 and added 7 net-new** links (`20 + 7 = 27`), not "20 → 20" as its
checklist row read. This pass then removed 2 of those net-new links with the L2 narration trim, leaving
**20 re-pointed + 5 net-new = 25**. The prior section is left exactly as written, per the dispatch.

### L2 — the narration removed, not justified

Removed, on Worker 3's reasoning. The asymmetry was real: `### The revision-log convention — answered`
declines a Revision 8 entry because it would "re-import exactly the chronology the rewrite removes", and a
trailing clause telling the reader what Decision 12 *used to* contain is a smaller instance of the same thing.
Both bullets now record only what their review round did, and "then-open" / past tense already carries the
historical frame:

- `:34` now ends `…the then-open Meta.distinct shape choice and the then-open Layer 6 path choice.`
- `:43` now ends `…rev3 named the then-current contents and added a staleness caveat.`

Neither bullet asserts anything present-tense; neither is now false or incomplete. Side effect, measured
rather than assumed: the two removed clauses carried the only Decision-12 anchor uses in the revision log, so
the fragment count drops 27 → 25 (L1's table).

### L3 — Worker 3's acceptance confirmed, not re-opened

I agree, and record it so a later pass does not re-litigate. `### Decision 3 — Five-layer port plus a deferred
Layer 6` keeps its heading on three grounds, each re-derived here rather than accepted:
`grep -o "decision-3--five-layer-port-plus-a-deferred-layer-6" | wc -l` → **6 at HEAD, 6 now** (renaming moves
a second anchor for no correctness gain); the word carries no version and no phantom owner, unlike the
retitled Decision 12; and shipped source uses the same vocabulary at both surviving `orders/factories.py`
citations ("remains a standing **deferred** Non-goal"), so the heading and the package agree. The residue —
heading softer than its own body — is surfaced to the maintainer as item 8, since making them agree is a
preference call, not a defect.

### Gates

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-028-orders-0_0_8.md` → exit **0**,
  `OK: 44 terms - all have glossary entries and at least one spec link.` (44 → 44; the terms CSV is untouched.)
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-028-orders-0_0_8.md` → exit **0**.
- `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/orders/sets.py` → exit
  **0**; `uv run ruff format` / `ruff check --fix` scoped to that file → unchanged / all checks passed.
- **In-page anchors: 159 uses, 21 distinct fragments, 0 unresolved, 0 duplicate heading slugs**, derived with
  my own slug function (keeps `_`, strips fences, code spans, emphasis, and both link forms) rather than the
  prior pass's. The 161 → 159 delta is exactly the two links L2 removed; no anchor use sits inside a fenced
  block, so fence-stripping changes nothing here.
- **Link definitions: 103 defs, 0 undefined refs, 1 orphan (`[relay]`)** — identical at HEAD, so still
  pre-existing and still out of scope.
- **Raw `path:NN`: 0 → 0**, extension-aware regex over the fence-stripped text. Every source reference this
  pass touched is symbol-qualified (`AGENTS.md` rule 27): the docstring cites a spec Decision by name and the
  artifact rows cite `path::QualifiedName`.
- **No Decision renumbered.** `diff` of `grep -n "^### Decision"` against HEAD reports exactly two differing
  rows: Decision 12's retitle (the perform pass) and Decision 13 shifting `1017` → `1009` from the O1/O2
  deletion. All thirteen numbers and the other twelve heading texts are byte-identical.

### Byte and line counts

| | bytes | lines |
|---|---|---|
| HEAD | 291,903 | 1,362 |
| after the perform pass | 289,500 | 1,354 |
| **after this pass** | **289,179** | **1,354** |

This pass: **-321 bytes, 0 lines** (three clause-level deletions, no structural change). Cumulative against
HEAD: -2,724 bytes, -8 lines. `git diff --numstat` → `49 57` for the spec and `1 1` for `orders/sets.py`.

### Non-sweep proof

`git log --stat` over both writable paths, never `git status` alone:

- `docs/SPECS/spec-028-orders-0_0_8.md` — newest commit touching it is still **`40e4754a`** (2026-07-31,
  "docs(specs): move spec companions into docs/SPECS/appx/"), unchanged from the perform pass.
- `django_strawberry_framework/orders/sets.py` — newest commit touching it is **`5851bb59`** (2026-08-15,
  the DRY cycle's permission-facade consolidation), which predates this cycle's dispatch.
- `git log -- docs/builder/bld-009-r2-spec028_distinct_reconciliation.md` → empty (never committed).
- `git show --stat HEAD` names neither path.
- HEAD is **`6f8bf818`** at both ends of this pass, re-derived rather than trusted from the plan.

### Spec changes made (Worker 1 only)

Three edits, all inside `### Maintainer decision 3`'s scope limit, plus the one source clause
`### Maintainer decision 7` authorizes.

| Site | Change | Reason |
|---|---|---|
| `docs/SPECS/spec-028-orders-0_0_8.md:1179` | `_dynamic_orderset_cache` **(deferred)** → `_dynamic_orderset_cache` | M2. The symbol ships (`fd0c7327`); the spec said so three times in text this cycle wrote, and contradicted itself here. Cheapest correct fix: drop the parenthetical, introduce no new claim |
| `docs/SPECS/spec-028-orders-0_0_8.md:34` | trailing clause "Both questions are settled in [Decision 12]…, which carries no preview" **cut** | L2. Narrates what the Decision used to contain — the chronology `### The revision-log convention — answered` declined a Revision 8 entry to avoid |
| `docs/SPECS/spec-028-orders-0_0_8.md:43` | trailing clause "The preview is gone; [Decision 12] states the key-set answer for both names directly" **cut** | L2, same ground. The surviving text records only what rev3 did |
| `django_strawberry_framework/orders/sets.py::OrderSet.get_flat_orders` | `-- DISTINCT ON deferred to ``0.0.9``).` → `-- no DISTINCT ON surface ships).` | M1, under `### Maintainer decision 7`. Shipped source no longer attributes a retired deferral to the Decision that now rejects the surface |

**Nothing else was touched.** The spec's `Status:` / `Owner:` / `Predecessors:` header block was re-read this
pass and still describes the build's state correctly; no status line is falsified by these three edits.

### Recorded for the maintainer / R4 — NOT repaired here

Items 1-5 stand as written in `## Final verification`. Three more, all found by the mechanical populations
this pass was required to produce:

6. **A FOURTH shipped-source citation of `spec-028` `### Decision 12`, still false.**
   `django_strawberry_framework/orders/inputs.py::convert_order_field_to_input_annotation` justifies keeping
   two unused parameters "for forward-compatibility (Spec Decision 12 -- a future DISTINCT ON extension or
   per-type direction enum in ``0.0.9`` would consult them)". Decision 12 now **rejects** the DISTINCT ON
   surface outright, and `0.0.9` shipped five versions ago, so the stated reason for the parameters no longer
   exists. `### Maintainer decision 7` authorizes **exactly one** docstring clause in `orders/sets.py`, so this
   is reported rather than fixed. It escaped M1 because the review's grep required `spec-028` on the same
   line and this file spells the citation `Spec Decision 12`. Smallest correct fix, if the maintainer widens
   again: the parameters are genuinely kept for shape-symmetry with
   `filters/inputs.py::convert_filter_to_input_annotation`, which the same sentence already says — so the
   DISTINCT ON half of the clause can be cut without inventing a replacement justification.
7. **A THIRD orphaned deferral in `spec-028`, outside R2's scope.** `:734` (`### Decision 8` step 4) defers the
   position-side-channel leak-closing design "likely to a sibling `0.0.9` ordering-permissions card"; no such
   card exists in `KANBAN.md` or `BACKLOG.md` (0 hits) and `0.0.9` shipped. Same shape as the `DjangoListField`
   orphan already recorded as item 4, and as R2's own subject. Decision 8's subject, so the scope limit does
   not reach it.
8. **`### Decision 3`'s heading residue (Worker 3's L3).** Kept deliberately — 6 in-file anchor uses, no
   version, no phantom owner, and shipped source uses the same word. The maintainer may still prefer heading
   and body to agree; that is a preference, not a defect, and it is recorded so no later pass re-opens it as a
   fresh finding.

### Summary

The two Mediums and three Lows are closed. M2 was a one-parenthetical spec edit and its lesson — a
token-defined population is not a subject-defined one — was discharged by re-running the sweep with a wider
token set than the finding used and grading all 109 hits; that found no second stale Decision-12 site and one
out-of-scope orphaned deferral at `:734`. M1's site is fixed in the one clause the maintainer authorized, and
its own number was corrected upward in the process: **four** shipped citations of Decision 12 exist, not
three, and the fourth (`orders/inputs.py`) is still false and outside the authorized clause. The gate this
pass was asked to close therefore closes with a stated exception rather than silently — three of the four
citations now agree with the rewritten Decision, the fourth is recorded for the maintainer as item 6, and no
number in this report was typed rather than measured.

Status: `planned`.

---

## Review (Worker 3, pass 2)

Read-only audit at HEAD `6f8bf818` (re-derived at both ends of this pass; unmoved). Every number in
`## Build report (Worker 1, apply-changes pass)` was re-measured from the tree rather than accepted, and the
two populations that decide this item — the Decision-12 citation population in source, and the widened token
sweep over the spec — were re-derived with **wider instruments than either prior pass used**, on the
principle the pass itself is being graded against.

`### Failability proofs` and `### Hot-path budget` are stated rather than omitted, because the diff now does
include a source line:

- **Failability proofs — not applicable.** The one source line is a docstring body inside
  `orders/sets.py::OrderSet.get_flat_orders`. `git diff -- django_strawberry_framework/orders/sets.py` is
  `1 1` and lands entirely between the `"""` delimiters; no statement, expression, signature, default,
  branch, guard, gate, or rejection path changed. There is no boundary to mutate, so a proof would have
  nothing to remove and no row that could go from pass to fail.
- **Hot-path budget — not applicable.** `### Maintainer decision 7` is explicit that R2 "does **not** become
  a code item"; Worker 1's plan declares no hot path, and a docstring is not executed. There is no
  before/after number to carry.

**Static helper.** `scripts/review_inspect.py` **skipped**, recorded per `BUILD.md`
`### When to run the helper during build`: no new `.py` file, nothing under `optimizer/` or `types/`, and
the source footprint is one docstring line — zero lines of new logic against a 30-line trigger.

### High:

None.

### Medium:

#### M1 (pass 2) — the fourth citation is covered by Decision 7's intent, and the recorded fix is one site short

**The call I was asked to make, plainly: (a).** The fourth citation
(`django_strawberry_framework/orders/inputs.py::convert_order_field_to_input_annotation`) **is** covered by
`### Maintainer decision 7`'s intent and should be consistent with Decision 12 before R2 closes. It is not
separate work.

The reasoning, against the decision's own text rather than its arithmetic:

- Decision 7's operative sentence is *"The three shipped citations of Decision 12 must all be consistent with
  it when R2 closes."* The load-bearing words are **all** and **consistent**; "three" is a cardinality
  asserted about the world, and the world turned out to hold four. A count that was wrong does not narrow a
  predicate — it mis-describes the set the predicate quantifies over. Read as a scope election, "three" would
  mean the maintainer chose three of four sites and declined the fourth, which is exactly what the decision
  record shows did not happen: the fourth was unknown when the decision was written.
- The governing instruction Decision 7 quotes is a completeness instruction with no count in it at all —
  *"since we did not fix every inbound reference in the same change last time, do that now."*
- Decision 7's own test for widening is met here **identically**. It widened for `orders/sets.py` because
  *"this cycle's own edit falsified a line of shipped source"*. Before R2, `orders/inputs.py`'s clause was
  merely stale-by-date (a `0.0.9` that had shipped). After R2 it is **contradicted by the Decision it names**:
  it justifies two parameters by *"a future DISTINCT ON extension ... in ``0.0.9`` would consult them"*, and
  `:1006` now records *"Ship the cookbook's `ASC_DISTINCT` / `DESC_DISTINCT` plus the `apply_distinct` port.
  **Rejected**"*. R2 created that contradiction.
- And Decision 7's stated reason for deciding rather than escalating applies word for word: leaving it
  *"would reproduce precisely the failure this item exists to correct — a stale deferral surviving five
  versions because the claim sat one document over from whoever was editing."* Here it sat one **module** over.

**Worker 1's call is nevertheless correct, and I am not grading it as an error.** Decision 7's scope limit is
enumerated and emphatic — *"exactly one docstring clause ... no other source file, no other docstring"* — and
a worker widening its own authorization is the worse failure. Checked rather than asserted: every scope
widening in this cycle is attributed to the **maintainer** (Decisions 3, 4, 5, 6) or to **Worker 0** on the
maintainer's standing instruction (Decision 7) — never to the pass performing the work. Recording it was the
right mechanism. So this finding does **not** ask Worker 1 to fix the source.

**What it does ask for, and why this is `revision-needed` rather than a note: item 6 mis-states the size of
the fix, in the direction that will make the next authorization repeat this cycle's own defect.**

Item 6 currently reads: *"Smallest correct fix, if the maintainer widens again: ... the DISTINCT ON half of
the clause can be cut without inventing a replacement justification."* Measured — the docstring is not the
only site in that function that carries the retired rationale:

```django_strawberry_framework/orders/inputs.py:201
    del model_field, owner_definition  # reserved for future-extension (see docstring).
```

`orders/inputs.py::convert_order_field_to_input_annotation` #"reserved for future-extension" is a **code
comment**, not a docstring, and it is an explicit pointer *at* the docstring for the future-extension
rationale. Cut the DISTINCT ON clause and the docstring's surviving reason is shape-symmetry with
`filters/inputs.py::convert_filter_to_input_annotation` — at which point the comment points at a docstring
that no longer records any future extension. A maintainer who reads item 6 and re-authorizes "exactly one
docstring clause" a second time will land a fix that leaves a dangling pointer two lines below the one it
corrected. That is a smaller instance of the identical shape: an incomplete fix because the second site sat
just outside the sentence someone was looking at.

`orders/inputs.py` is **clean at HEAD** (`git status --porcelain django_strawberry_framework/orders/` names
only `sets.py`), so both sites are shipped text, not a concurrent working copy.

The citation's spec identity is also worth pinning, since it is what defeated the pass-1 grep: the file
spells it `Spec Decision 12` with no spec number, and the same module writes `Per spec-028 Decision 5` at
`orders/inputs.py::convert_order_field_to_input_annotation` #"Per spec-028 Decision 5" and `(spec-027` /
`(spec-028` elsewhere. Unqualified "Spec Decision N" in this module means spec-028. It is a spec-028
citation.

**Recommended change** (artifact only — no source edit, no scope widening by any worker):

1. Rewrite item 6 so it states the fix's true footprint: **one docstring clause plus the `del`-line comment**,
   in one file, and name both symbol-qualified. The parameters remain justified after the cut — the same
   sentence already gives shape-symmetry as an independent reason — so no replacement justification has to be
   invented for either site; the comment simply has to stop advertising a future extension.
2. Restate the Decision-7 reading explicitly, so the maintainer decides on the intent rather than on the
   arithmetic: the "three" was a measurement of the world, the requirement was *all*, and the fourth citation
   meets Decision 7's own widening test (this cycle's edit falsified shipped source) exactly as the third did.
3. Route it as what it is — a request to amend `### Maintainer decision 7`, which is Worker 0's escalation to
   the maintainer, not a Worker 1 edit. Recording that routing in item 6 is what stops it being read as
   ordinary R4 backlog.

Test expectation: none — documentation and docstring prose, no behavior affected.

### Low:

#### L1 (pass 2) — a reason clause under L2 is false; the number it supports is right

`### L2 — the narration removed, not justified` closes: *"the two removed clauses carried the only
Decision-12 anchor uses in the revision log, so the fragment count drops 27 → 25 (L1's table)."*

The arithmetic is correct and I reproduce it (`25` occurrences now, on `25` distinct lines — no line carries
two). The **reason** is not. The revision log carries a third Decision-12 anchor use, at `:10`, which
survives:

| Measure | HEAD | Now |
|---|---|---|
| D12 anchor uses in the revision-log range (lines 3-68) | 1 (old fragment, `:10`) | 1 (new fragment, `:10`) |

So the correct clause is "the two removed clauses carried the two Decision-12 anchor uses this cycle *added*
to the revision log" — `:10`'s was a re-point, not a net-new, and it is still there.

Filed Low because nothing measurable is wrong: 27 → 25 holds, L1's table holds, and the spec is unaffected.
Filed at all because it is precisely this cycle's seventeen-times-repeated class — a fluent subordinate clause
supplying the *why* behind a correct number, in connective tissue no later reader re-derives. Recommended
change: replace "the only" with "the two ... this pass added", or cut the clause and keep the number.

#### L2 (pass 2) — the `:734` orphan has a second site, and item 7 records only one

I confirm Worker 1's grading of `:734` in full: it is `### Decision 8` step 4's subject, not Decision 12's, so
`### Maintainer decision 3`'s scope limit does not reach it; it is genuinely orphaned (`grep -in
"ordering-permission\|position-side-channel\|side-channel" KANBAN.md BACKLOG.md` → **0 lines in each**,
reproduced); and it is correctly a report rather than a Medium, because the line is self-aware — it says in
its own text that *"the work has not been carved into a card yet"*, so it does not assert a phantom card.

What item 7 does not record is that the same orphan has a **second site**: `:41`, the `Revision 2`
`N-new-1` bullet, which quotes the deferral's before-and-after wording — *"Now reads 'deferred — likely to a
sibling `0.0.9` ordering-permissions card ...'"*. `grep -n "ordering-permissions card"` over the spec returns
exactly two lines, `41` and `734`. A maintainer or R4 pass acting on item 7 as written fixes `:734` and leaves
`:41` quoting the retired phrasing.

This is the same population defect one layer down — a site recorded by the one line the finder happened to
open. Recommended change: name both lines in item 7. (Whether `:41` should change at all is a separate
question the maintainer owns: it is a revision-log bullet recording what rev-2 did, and by the pass's own
`### The revision-log convention — answered` reasoning such a bullet stays where it records history. Worth
saying so in the record so the second site is a decided non-edit rather than an unnoticed one.)

#### L3 (pass 2) — bucket-boundary drift between the report's script and mine (no action)

Recorded so it is not mistaken for a discrepancy later. My independent reconstruction of the 109-line
partition returns `body 15 / anchor 25 / revision-log 11 / (:1019, :1158) 2 / Meta-key prose 19 /
UNCLASSIFIED 37`, against the report's `15 / 25 / 21 / 9 / 1 / 1 / 37`. The two differ only in where two
lines inside 3-68 fall between the "revision log" and "`DEFERRED_META_KEYS` prose" buckets — an artifact of
bucket-application order, not of classification. **The population (109), the residual (37), and every total
agree exactly**, and the residual is the only bucket that carries grading weight. No change requested.

### DRY findings

None to consolidate. Three to affirm, one carried forward.

- **The single-normative-site shape held under a wider instrument.** I re-ran the subject-defined sweep
  across the whole package rather than the spec — `grep -rniE "distinct" --include='*.py'
  django_strawberry_framework/` — and read every hit in `orders/`. Decision 12's DISTINCT ON contract is
  asserted in exactly two source places, both attribution glosses pointing at the Decision
  (`orders/sets.py::OrderSet.get_flat_orders`, `orders/inputs.py::convert_order_field_to_input_annotation`);
  no module restates the mechanism. Every other `DISTINCT` / `distinct` hit package-wide is a real
  `.distinct()` queryset concern (`filters/sets.py`, `optimizer/`, `permissions.py`
  #"which would change which rows DISTINCT ON keeps") or ordinary English. The mechanism is stated once, in
  the spec, and pointed at — which is the shape the cycle settled on.
- **The M1 fix reuses vocabulary instead of paraphrasing it.** `-- no DISTINCT ON surface ships).` is the
  Decision's own words twice over: its heading (`No Layer 6 auto-generation and no **DISTINCT ON surface**`)
  and its body bullet (`**No declaration surface ships for it.**`). Per my standing instrument I graded the
  clause as a *reason* separately from the *rule* it supports: the rule (tuple-half dropped) is pre-existing
  and untouched; the reason (no such surface ships) is what `:1006`'s rejection and `:995`'s "no
  `distinct_on:` argument" both state. The docstring therefore asserts nothing the Decision does not.
  This is the shape to prefer over restatement, and it is the third time this cycle that quoting beat
  paraphrasing.
- **The existence challenge on `get_orderset_class` / `_dynamic_orderset_cache` stays answered.** Pass 1
  raised and closed it against `utils/inputs.py::make_dynamic_set_getter`; nothing in this pass's diff
  changes the code, so it is not re-opened.
- **Carried forward, not raised as a finding here.** `orders/inputs.py::convert_order_field_to_input_annotation`
  takes two parameters it immediately `del`s, and after M1's clause is cut the sole remaining justification is
  shape-symmetry with its filter twin. Whether an unused-parameter pair earns its place on symmetry alone is
  a contract-level question (`BUILD.md` `### Contract-level findings are escalated as maintainer decisions
  before dispatch`) and **not a worker's call** — I raise it only so the maintainer sees it attached to the
  same authorization, since it is the natural next question once the DISTINCT ON reason is gone. It is not a
  reason to hold R2, and it is not part of my recommended fix.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty** (0 bytes of diff). `__all__` and the
re-export list are unchanged, and the file is untouched at the byte level. R2 changed a docstring body inside
`orders/sets.py`, not an export: the whole source footprint is `git diff --numstat --
django_strawberry_framework/orders/sets.py` → `1 1`, and reading the hunk confirms both lines sit between the
`"""` delimiters of `OrderSet.get_flat_orders`.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applies (the pass touches an archived spec and one shipped docstring). All checks pass.

- **Gates, re-run rather than trusted.** `uv run python scripts/check_spec_glossary.py --spec
  docs/SPECS/spec-028-orders-0_0_8.md` → exit **0**, `OK: 44 terms - all have glossary entries and at least
  one spec link.` `check_trailing_commas.py --check` → exit **0** on the spec **and** on
  `django_strawberry_framework/orders/sets.py`.
- **No Decision renumbered.** Thirteen `### Decision N` headings at HEAD and thirteen now; a positional
  diff of the two lists reports **exactly one** differing row — Decision 12's retitle. The other twelve are
  byte-identical.
- **Anchors and links, derived with my own slug function** (keeps `_`, strips fences, code spans, and
  asterisk emphasis only): **159 uses, 21 distinct fragments, 0 unresolved, 0 duplicate heading slugs**;
  **103 link definitions, 0 undefined refs, 1 orphan (`[relay]`)**, and the same 103 / 0 / 1 at HEAD, so the
  orphan is confirmed pre-existing and correctly left alone. A note for the next pass, since it cost me a
  cycle and cost the perform pass one too: an emphasis-stripping regex written as `[*_]{1,3}` eats the
  underscores in `### Decision 11 — `order_input_type(OrderSet)` consumer helper` and reports a **false**
  unresolved anchor. The checker is itself a claim; run it against HEAD as a control before believing a hit.
- **Raw `path:NN`: 0 → 0** (extension-aware regex over fence-stripped text), at HEAD and now.
- **Anchor arithmetic reproduces end to end.** Old fragment `20 → 0`; new fragment `0 → 25`, on 25 distinct
  lines. `### Decision 3`'s anchor: **6 at HEAD, 6 now** — keeping that heading cost nothing, as claimed.
  Inbound external fragment citations: `grep -rn "spec-028-orders-0_0_8.md#" .` → **3 hits, all three inside
  this artifact quoting its own grep string**; 0 real inbound citations repo-wide, so the retitle broke
  nothing outside the file.
- **Bytes and lines reproduce to the byte.** `wc -c -l` → **289,179 bytes / 1,354 lines** now;
  **291,903 / 1,362** at HEAD. `git diff --numstat` → `49 57` for the spec, `1 1` for `orders/sets.py`.
- **The R1c caveat genuinely never engaged.** `orders/sets.py` carries **no** concurrent modification: its
  entire working-tree diff is this pass's 1/1 hunk, and `check_trailing_commas.py --check` exits 0, so the
  auto-fixing form was never reached for. Newest commit touching the file is `5851bb59`, which predates the
  dispatch.
- **Provenance, by `git log --stat` not `git status`.** Newest commit touching the spec is still `40e4754a`;
  `git log -- docs/builder/bld-009-r2-spec028_distinct_reconciliation.md` → **0 commits**. HEAD `6f8bf818` at
  both ends of this pass.

### What looks solid

The substance of the apply-changes pass is right, and its central self-correction is the strongest thing in
it. Reproductions, all independent of the report's own commands:

- **The M1 clause is true, in-scope, and asserts nothing new.** The diff is the one authorized clause and
  nothing else; see `### DRY findings` for the reason-vs-rule grading.
- **The citation population is FOUR, and four is the whole of it — verified with two instruments, not one.**
  `grep -ro "Decision 12" django_strawberry_framework/ | wc -l` → **20**, of which 16 belong to `spec-039`,
  `spec-046`, `spec-032`, `spec-036` (opened and discarded) and **four** cite spec-028, all under `orders/`.
  I then widened past the token: a case-insensitive `decision[ _-]*12|\bD12\b` sweep across
  `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/` surfaces only `spec-040`'s `D12` rows
  besides those already known. And because the lesson under test is that a **token**-defined population is
  not a **subject**-defined one, I ran the subject sweep too — every `distinct` occurrence in package source —
  and found **no fifth site**: no module asserts the retired deferral without naming Decision 12. The
  population is closed at four. Worker 1's number survives the instrument that broke the previous two.
- **Three of the four citations agree with the rewritten Decision.** Both `orders/factories.py` sites say
  "standing deferred Non-goal" with no version and no owner, matching `:988`'s bolded non-goal; the
  `orders/sets.py` site now quotes the Decision's heading. `orders/factories.py` is clean at HEAD, so all
  three are shipped text. The fourth is M1.
- **M2's fix landed and the contradiction is gone.** `:1179` now reads `` `_dynamic_orderset_cache`,
  `get_flat_orders` `` with the `(deferred)` parenthetical removed and the bullet otherwise intact; the
  symbol is still in the list, no new claim was introduced, and it no longer contradicts `:197`, `:479`,
  `:988`.
- **The widened sweep reproduces exactly, and survives a sweep wider still.** Worker 1's token set returns
  **109** on the current spec, to the line. Its bucket totals sum: `15+25+21+9+1+1+37 = 109`, and the residual
  `11+21+2+2+1 = 37`. I verified the residual is a genuine **subset** of the 109 with no duplicates, disjoint
  from the Decision-12 body range and from every anchor-carrying line, and I opened and re-graded a spread of
  it (`:105`, `:329`, `:458`, `:749`, `:1052`, `:1105`, `:1153`, `:1205`) — all ordinary prose, obsolete-work
  strikethroughs, test-plan rows, and true `Decision 3` / `Decision 7` anchor text. Then I ran a set wider
  than Worker 1's (adding `non-goal`, `follow-on`, `follow-up`, `sibling card`, `later card`, `postpone`,
  `punt`, `ships in`, `lands in`, `tracked elsewhere`, `a future`, `out of scope`, `TODO`, `0.0.1[0-9]`) →
  **141**, and opened all **32** lines in the difference. Every one is benign: shipped-version labels,
  obsolete-work records, tie-breaker and multi-database prose, and the already-recorded `DjangoListField`
  orphan. **No second stale Decision-12 site exists**, and the claim now rests on three independently-sized
  populations rather than one.
- **The recorded self-correction is real, and the remedy holds.** The report states plainly that a first
  draft wrote "88 hits" from memory where the measured figure is 109, and does not quietly correct it. That
  is this cycle's signature defect caught inside the section about measuring populations, and naming it is
  worth more than the number. The remedy it installed is structural rather than a promise: a bucketing script
  that emits counts with an `UNCLASSIFIED` residual which must sum, printed in the artifact. I checked the
  remedy actually holds rather than the claim that it does — every figure in the section reconciles, the
  residual is enumerated line by line, and each of its five sub-buckets is itself enumerated and sums.
- **The three Lows each landed as described.** `:34` now ends `…the then-open Layer 6 path choice.` and `:43`
  now ends `…rev3 named the then-current contents and added a staleness caveat.` — exactly where pass 1
  recommended; neither is now false or incomplete. L1's occurrence-vs-line distinction is stated correctly
  and the `20 re-pointed + 5 net-new = 25` arithmetic reproduces. L3 is confirmed, not re-opened, with the
  `6 → 6` anchor count re-derived rather than carried.
- **The `:734` grading is correct** — see L2 (pass 2) for the confirmation and the one site it omits.
- **Nothing outside the authorized footprint moved.** Two writable paths, both accounted for; no test, no
  other source file, no spec header, no terms CSV, no `CHANGELOG.md`, no `KANBAN.md`.

### Temp test verification

No `pytest` run: the diff contains no executable line, so there is no behavior to exercise, and no `--cov*`
flag was used anywhere in this pass. Read-only verification under `docs/builder/temp-tests/r2/` (gitignored):

- `w3p2_check.py` (new this pass) — independent anchor resolver, link-definition auditor, raw-`path:NN`
  counter, and positional `### Decision N` heading differ, each run against **both** the working tree and
  `git show HEAD:<spec>` so every result has its own control. Its first run reported a false unresolved
  anchor from an underscore-eating emphasis regex; the control at HEAD showed the same false hit, which is
  what identified the checker rather than the spec as the defect. Fixed and re-run.
- Ad-hoc set algebra over the 109-line population, the 37-line residual, and the 141-line wider population,
  reconciled with `comm` under a fixed collation. One caution for a later pass: `comm` needs a lexicographic
  sort, and feeding it `sort -n` output silently reports 16 present members as absent — I hit exactly that
  and the "missing" rows were all present. Verify a `comm` result against a direct membership test before
  writing a finding on it.
- Pass 1's `anchors.py`, `links.py`, `denom.py`, `outside.py` were **not** re-used, deliberately: both prior
  passes were shape-defeated by their own instruments, so every population here was re-derived from scratch.

Disposition: kept for the cycle, deleted with it; the directory is gitignored so nothing reaches a commit.
None is a promotion candidate — there is no behavior to pin.

### Notes for Worker 1 (spec reconciliation)

1. **M1 (pass 2) is yours and needs no maintainer decision to close.** The source fix is not yours and I am
   not asking for it. What is yours is item 6's accuracy: state the fix as **a docstring clause plus the
   `del`-line comment**, and state the Decision-7 reading as intent-over-arithmetic. Both are artifact edits
   inside your writable set.
2. **Escalated: `### Maintainer decision 7` should be amended to cover the fourth citation.** Resolution
   paths for the maintainer: **(a)** amend Decision 7 so its requirement reads "every shipped citation of
   Decision 12", authorizing the `orders/inputs.py` clause **and** its `del`-line comment, and close R2 with
   the citation set actually consistent; **(b)** leave Decision 7 as written and card the `orders/inputs.py`
   site with the two orphaned deferrals (items 4 and 7), accepting that R2 closes with shipped source
   contradicting the Decision this cycle rewrote; **(c)** hand it to R4's cross-reference audit. My
   recommendation is **(a)**, for the reason Decision 7 gives in its own body — the failure this item exists
   to correct is a claim left unfixed because it sat one document over, and the fourth citation is that
   failure at module distance instead of document distance. If (a) is taken, the amendment should authorize
   **two sites in one file**, not "one clause": authorizing one clause again is how the same shape recurs a
   fourth time.
3. **Three orphaned deferrals in one spec is a pattern, and it should reach the maintainer as one.** `spec-028`
   now has three recorded: DISTINCT ON / Layer 6 (R2's own subject, fixed), `DjangoListField` orderBy-argument
   integration at `:195` / `:1191` (item 4), and the position-side-channel leak-closing work at `:734` /
   `:41` (item 7, plus L2 above). All three defer to `0.0.9`; all three have **zero** cards in `KANBAN.md` or
   `BACKLOG.md`; `0.0.9` shipped five versions ago. Three independent instances in one document is not three
   oversights — it is evidence that this spec's deferrals were written as prose rather than as tracked work,
   and that nothing in the archive step checks a deferral against the board. The maintainer's useful question
   is not "fix these three" but "does any archived spec's `0.0.X` deferral have a card", which is a
   repo-wide sweep R4 is already shaped to run. Recording the three individually, in three separate numbered
   items, is what hides the pattern.
4. **The sweep-population lesson survives its own re-test, and that is worth carrying to R4 verbatim.** Pass 1
   found M2 by widening the tokens; this pass widened them further and found nothing new; I widened them a
   third time and found nothing new. The population is genuinely closed — but note *which* instrument found
   the fourth citation, because it was not a wider spec sweep: it was moving from the **spec** to the
   **source** and grepping the shortest token there. A reconciliation has two populations, in two different
   corpora, and widening tokens inside one of them cannot reach the other.
5. **Non-finding, recorded so it is not re-raised.** Pass 1's `:1171` note (the `Ordering`-enum
   demand-contingent fallback) was re-graded by the apply pass and confirmed a note. I agree; the section's
   own preamble declares that every entry carries a fallback, so a demand-contingent revisit of a rejection
   is the section's shape and asserts nothing false. Three passes have now graded it the same way — it should
   not be opened a fourth time.

### Review outcome

`revision-needed` — on **M1 (pass 2)** only, and narrowly. The pass's substance is accepted without
reservation: the one authorized clause is correct and quotes the Decision rather than paraphrasing it, M2's
contradiction is gone, all three Lows landed as recommended, every gate re-runs clean, and every number in
the report reproduces from the tree — including the two populations, which now survive instruments wider than
either the report's or pass 1's. The apply pass also caught and published its own signature-defect near-miss
(88 written from memory against a measured 109) and installed a structural remedy for it that I verified
holds rather than accepting the claim.

What holds it open is one artifact-level correction, fully inside Worker 1's writable set: item 6 records the
fourth citation's fix as one docstring clause when it is a clause **plus** a code comment pointing at that
clause, and frames Decision 7 as a count when its requirement is "all". Both matter because item 6 is the
document the maintainer will decide the next authorization from, and as written it will produce another
one-site fix. The two Lows are optional but cheap, and L1 is the cycle's own recurring class — a false reason
clause under a correct number. No source edit is requested of any worker, and the underlying scope question
is escalated to the maintainer under note 2 rather than being held against this pass.

---

## Build report (Worker 1, apply-changes pass 2)

M1 (pass 2) and both Lows are closed. Per this cycle's `### Deviation 3` corollary the fix pass for a
Worker-1-exclusive deliverable is Worker 1's, so this section replaces a Worker 2 build report; it appends at
top level and edits no prior section. `Status:` returns to `planned`, which Worker 0 reads as "dispatch
Worker 3".

**What changed between the review and this pass: the authorization.** `### Maintainer decision 7` now carries
an `**Amendment, 2026-08-16 — the population is FOUR, and the operative word was always "all".**` block that
adopts M1's reading verbatim ("**three**" was a cardinality asserted about the world, not a scope election)
and, in a second paragraph, records the finding M1 supplied: *"**The fourth citation is TWO sites, not one**
... Both are in scope; nothing else in that module is."* So M1's recommendation 3 — route it as an escalation
rather than a Worker 1 edit — was discharged upstream of this pass, and what remains here is recommendations
1 and 2 (item 6's footprint and framing) **plus the fix the amendment now authorizes.**

### M1 (pass 2), part 1 — item 6's footprint and framing, corrected

The false clause, quoted from `## Build report (Worker 1, apply-changes pass)` item 6 (left as written, per
the dispatch):

> Smallest correct fix, if the maintainer widens again: the parameters are genuinely kept for shape-symmetry
> with `filters/inputs.py::convert_filter_to_input_annotation`, which the same sentence already says — so the
> DISTINCT ON half of the clause **can be cut** without inventing a replacement justification.

Two corrections, both of which the amended Decision 7 has now ratified:

- **Footprint — it is two sites, not "the clause".** `orders/inputs.py::convert_order_field_to_input_annotation`
  #"reserved for future-extension" is a code comment on the `del` line two lines below the docstring, and it
  points *at* the docstring for exactly the rationale being cut. Cutting the clause alone leaves it dangling.
  Measured rather than asserted — the module's occurrences of the retired rationale, by its two shortest
  distinctive tokens:

  ```shell
  $ grep -roiE "future[ -]extension|forward[ -]compat[a-z]*" django_strawberry_framework/ tests/ examples/ scripts/ | wc -l
         4
  $ grep -rniE "future[ -]extension|forward[ -]compat[a-z]*" django_strawberry_framework/ tests/ examples/ scripts/
  django_strawberry_framework/orders/inputs.py:196:    forward-compatibility (Spec Decision 12 -- a future DISTINCT ON
  django_strawberry_framework/orders/inputs.py:201:    del model_field, owner_definition  # reserved for future-extension (see docstring).
  django_strawberry_framework/orders/inputs.py:237:        # Spec Decision 5. ``model_field`` discovery is a future-extension
  tests/mutations/test_sets.py:664:    # The bind stashes forward-compat refs for the resolver pipeline.
  ```

  Three of the four occurrences are in this one module — the two Decision 7 authorizes, and a third at
  `orders/inputs.py::_build_input_fields` #"future-extension" which the amendment explicitly excludes
  ("nothing else in that module is"). It is reported below, not touched.
- **Framing — intent, not arithmetic.** Item 6 read Decision 7's "**exactly one** docstring clause" as the
  scope, which made the fourth citation a *widening request*. It is not. Decision 7's requirement is that the
  shipped citations of Decision 12 be **consistent with it** when R2 closes; "three" measured a set, and a
  wrong measurement mis-describes the set a predicate quantifies over rather than narrowing the predicate.
  The instruction the decision rests on carries no count at all. And the widening test Decision 7 applied to
  `orders/sets.py` is met here identically: before R2 the clause was stale-by-date; **after R2 it was
  contradicted by the very Decision it cites**, because this cycle's own rewrite recorded the DISTINCT ON port
  as `**Rejected**` (`spec-028:1006`) while the docstring still justified two parameters by a future DISTINCT
  ON extension "in ``0.0.9``".

Item 6 is therefore **closed, not re-recorded** — part 2 performs it. The one thing that survives item 6 into
this pass's `### Recorded for the maintainer / R4` list is the residual third site the amendment excluded.

### M1 (pass 2), part 2 — the fix, both sites

`django_strawberry_framework/orders/inputs.py::convert_order_field_to_input_annotation`. No behavior change,
no signature change, no `del` statement removed, nothing else in the module. Exact before / after:

**Site 1 — the docstring clause.**

```
before
    The ``model_field`` and ``owner_definition`` arguments are unused at
    the body level today; they are kept in the signature for
    forward-compatibility (Spec Decision 12 -- a future DISTINCT ON
    extension or per-type direction enum in ``0.0.9`` would consult
    them) and for shape-symmetry with
    ``filters/inputs.py::convert_filter_to_input_annotation``.

after
    The ``model_field`` and ``owner_definition`` arguments are unused at
    the body level; they are kept in the signature for shape-symmetry
    with ``filters/inputs.py::convert_filter_to_input_annotation``, not
    for a DISTINCT ON extension -- per spec-028 Decision 12 no DISTINCT
    ON surface ships.
```

**Site 2 — the `del`-line comment.**

```
before
    del model_field, owner_definition  # reserved for future-extension (see docstring).

after
    del model_field, owner_definition  # unused; kept for shape-symmetry (see docstring).
```

Four things about the replacement text, each decided rather than defaulted:

- **The surviving reason is the true one, not a new future.** The parameters are part of the shared
  set-family converter shape: `django_strawberry_framework/utils/inputs.py` #"Domain semantics stay at the
  call sites" states outright that the two `inputs` modules are deliberate mirrors with the neutral scaffold
  single-sited in `utils/inputs.py::emit_set_input_field_triples`, and
  `orders/inputs.py::_build_input_fields` #"Mirror of" says the same at the sibling function.
  `filters/inputs.py::convert_filter_to_input_annotation` takes `(filter_instance, model_field,
  owner_definition, filterset_cls)` — the two parameter names are shared with it verbatim. That reason was
  **already in the sentence**; the fix keeps it and deletes only the withdrawn one, so no replacement
  justification was invented.
- **The negation is scoped to what Decision 12 actually rejects.** "not for a DISTINCT ON extension" —
  not the broader "carries no forward-compatibility promise", which would have asserted more than the spec
  supports: `spec-028:1171` keeps a demand-contingent `ASC_DISTINCT` / `DESC_DISTINCT` enum fallback in
  `## Risks and open questions`, graded a non-finding three times now. A sharper negation would also have
  manufactured a contradiction with the out-of-scope third site.
- **The clause quotes the Decision instead of paraphrasing it.** `no DISTINCT ON surface ships` is
  `### Decision 12`'s own heading vocabulary and the exact wording the `orders/sets.py` clause landed with
  last pass, so the two shipped citations now say the same thing in the same words and the docstring asserts
  nothing the Decision does not.
- **The citation is qualified — `Spec Decision 12` → `spec-028 Decision 12`.** This is the spelling that
  defeated two consecutive greps (a citation's *prefix* is not part of the citation), and the same docstring
  already writes `Per spec-028 Decision 5` four lines above, so qualifying it makes the function internally
  consistent and makes the site reachable by the same instrument that finds the other three. Inside the
  clause Decision 7 authorizes; recorded here because it moves a token the population sweeps key on.

**Lint, concurrency, and rule compliance.** `git status --porcelain django_strawberry_framework/orders/`
named only `sets.py` immediately before the edit, so `inputs.py` was clean at HEAD and this pass's diff is the
whole of it. `uv run ruff format django_strawberry_framework/orders/inputs.py` → "1 file left unchanged";
`uv run ruff check --fix django_strawberry_framework/orders/inputs.py` → "All checks passed!"; both **scoped
to that one file, never `.`**. `uv run python scripts/check_trailing_commas.py --check
django_strawberry_framework/orders/inputs.py` → exit **0**, so the concurrent-line caveat never engaged and
the auto-fixing form was never reached for. `AGENTS.md` rule 17: longest touched line is **89** characters
(the `del` comment), inside 100; `grep -nP '[^\x00-\x7F]'` over the file → **0**, ASCII-only intact.
Rule 27: both sites cite `filters/inputs.py::convert_filter_to_input_annotation` symbol-qualified and a spec
Decision by number — no line number in either.

### The Decision-12 citation population, re-derived one final time

Produced mechanically and pasted, per the dispatch. The corpus was **moved**, not the pattern widened: the
prior passes searched `django_strawberry_framework/` only, so this run searches package + tests + examples +
scripts, from the shortest distinctive token, counting **occurrences** rather than matching lines.

```shell
$ grep -ro "Decision 12" django_strawberry_framework/ tests/ examples/ scripts/ | wc -l
      45
```

Forty-five occurrences across 22 files — more than double the package-only 20 the last two passes worked
from. Every one was opened and graded from its matched context; **41 belong to another spec's Decision 12**
and were discarded by reading, never by narrowing the regex: `spec-046` (`consumers.py`, `tests/test_routers.py`
— maximum connection lifetime), `spec-039` (`__init__.py`, `rest_framework/`, `tests/rest_framework/` — the
DRF soft-import guard), `spec-036` (`mutations/sets.py`, `tests/mutations/test_sets.py` — the mutation `Meta`
key namespace), `spec-032` (`types/finalizer.py`, `examples/…/library/`), `spec-034` (`tests/test_connection.py`,
`tests/test_list_field.py`, `tests/test_relay_node_field.py`, `tests/test_permissions.py`,
`tests/optimizer/test_extension.py` — cascade composition), `spec-038` (`examples/…/products/`), and
`spec-040` (`tests/base/test_init.py`). **Four cite `spec-028`, all four inside `orders/`** — the same four,
so widening the corpus by more than 2x found no fifth.

The cross-check the token population cannot perform, since a subject can be asserted without naming the
Decision:

```shell
$ grep -roiE "distinct on" django_strawberry_framework/ tests/ examples/ scripts/ | wc -l
       5
$ grep -ro "0\.0\.9" django_strawberry_framework/ tests/ examples/ scripts/ | wc -l
      35
```

Of the 5 `DISTINCT ON` occurrences, 3 are the citations below, one is `permissions.py`
#"which would change which rows DISTINCT ON keeps" (a real `.distinct()` concern, not a deferral), and one is
ordinary English in `tests/mutations/test_inputs.py`. Of the 35 `0.0.9` occurrences, **exactly one** was a
forward-looking promise — `orders/inputs.py:197`, now gone; the other 34 are shipped-version labels
(`pre-0.0.9`, `shipped 0.0.9`, `Target release: 0.0.9`, `DONE-030-0.0.9`) or card ids.

**All four shipped citations now agree with the rewritten Decision 12:**

| Citation | Claim | Agrees? |
|---|---|---|
| `orders/factories.py` #"Auto-generation of an ``OrderSet`` from" | auto-generation "remains a standing deferred Non-goal" | **yes** — `spec-028:988` states the same non-goal in bold; "deferred" carries no version and no owner |
| `orders/factories.py::get_orderset_class` #"is a standing deferred Non-goal" | the auto-`OrderSet` surface is a standing deferred non-goal; the connection field consumes the sidecar directly | **yes** — `spec-028:987` and `:988` state both halves |
| `orders/sets.py::OrderSet.get_flat_orders` #"cookbook's DISTINCT ON tuple-half dropped" | the tuple-half is dropped because no DISTINCT ON surface ships | **yes** — corrected in the prior pass; quotes `### Decision 12`'s heading |
| `orders/inputs.py::convert_order_field_to_input_annotation` #"not for a DISTINCT ON extension" | the parameters are kept for shape-symmetry, not for a DISTINCT ON extension; no DISTINCT ON surface ships | **yes** — corrected in this pass; same wording as the `sets.py` clause |

The gate `### Maintainer decision 7` set — *"the shipped citations of Decision 12 must all be consistent with
it when R2 closes"* — now closes **without an exception**, where the prior pass had to close it with one.

### Residual retired-rationale sites in the same module — reported, NOT edited

The amendment's scope limit is explicit ("nothing else in that module is"), so these are recorded:

```shell
$ grep -n "reserved\|future-extension" django_strawberry_framework/orders/inputs.py
232:    del owner_definition  # reserved -- see ``convert_order_field_to_input_annotation``.
236:        # Spec Decision 5. ``model_field`` discovery is a future-extension
269:    are preserved -- the apply pipeline filters them in its
```

- **`orders/inputs.py::_build_input_fields` #"reserved -- see"** points at the function this pass corrected.
  Its pointer still resolves — the docstring still explains why an unused parameter is kept — but its own word
  "reserved" is now the only survivor of the withdrawn vocabulary.
- **`orders/inputs.py::_build_input_fields` #"future-extension"** calls `model_field` discovery "a
  future-extension affordance the converter ignores today". It cites `Spec Decision 5`, not Decision 12, and
  Decision 12 does not falsify it as sharply as it falsified the site just fixed (the `spec-028:1171` fallback
  is demand-contingent and undated). It is vague rather than false, and it is the third instance of one
  rationale in one module.
- `:269` ("are preserved") is an unrelated substring match, opened and discarded.

### L1 (pass 2) — the false reason clause, corrected

The clause, from `### L2 — the narration removed, not justified` (left as written, per the dispatch): *"the
two removed clauses carried **the only** Decision-12 anchor uses in the revision log, so the fragment count
drops 27 → 25."* Worker 3 is right: the number is right and the reason is not. Measured:

```shell
$ awk 'NR>=3&&NR<=68' docs/SPECS/spec-028-orders-0_0_8.md | grep -o "decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface" | wc -l
       1
$ grep -o "decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface" docs/SPECS/spec-028-orders-0_0_8.md | wc -l
      25
$ grep -c "decision-12--no-layer-6-auto-generation-and-no-distinct-on-surface" docs/SPECS/spec-028-orders-0_0_8.md
25
```

`spec-028:10` (the `Revision 1` bullet) carries a third Decision-12 anchor use in the revision log and it
survives, so the corrected clause is **"the two removed clauses carried the two Decision-12 anchor uses this
cycle *added* to the revision log"** — `:10`'s was a re-point, not a net-new. `27 → 25` holds, L1's table
holds, occurrences equal lines (25 = 25, no line carries two), and the spec is unaffected. This is the
cycle's signature class one more time: a fluent subordinate clause supplying the *why* behind a correct
number.

### L2 (pass 2) — item 7's second site, recorded

```shell
$ grep -o "ordering-permissions card" docs/SPECS/spec-028-orders-0_0_8.md | wc -l
       2
$ grep -n "ordering-permissions card" docs/SPECS/spec-028-orders-0_0_8.md   # -> lines 41 and 734
```

The `:734` orphan (`### Decision 8` step 4) has a **second site at `:41`**, the `Revision 2` `N-new-1` bullet,
which quotes the deferral's before-and-after wording. Item 7 recorded only `:734`; both are named in the
corrected item 7 below. `:41` is a **decided non-edit**, not an unnoticed one: by this pass's own
`### The revision-log convention — answered` reasoning a revision-log bullet records what a review round did
and stays put, and rewording it would desync it from the text it quotes. Whether `:734` itself changes is the
maintainer's call under the pattern item below.

### The pattern — three orphaned deferrals in one spec, and the sweep that answers all three

Worker 3 asked for this to reach the maintainer as **one** decision rather than three fixes, and that is
right. `spec-028` now carries three recorded orphaned deferrals:

1. **DISTINCT ON / Layer 6** — R2's own subject. Fixed.
2. **`DjangoListField` orderBy-argument integration** — `:195` (`## Non-goals`) and `:1191` (`## Out of
   scope`), deferred to `0.0.9`. `list_field.py` carries zero occurrences of `order_by` / `orderset`; no card
   names it (item 4).
3. **The position-side-channel leak-closing work** — `:734` and `:41`, deferred to "a sibling `0.0.9`
   ordering-permissions card". `grep -in "ordering-permission\|position-side-channel\|side-channel"
   KANBAN.md BACKLOG.md` → **0 lines in each** (item 7 + L2 above).

All three defer to `0.0.9`; all three have zero cards; `0.0.9` shipped five versions ago. **Three independent
instances in one document is not three oversights** — it is evidence that this spec's deferrals were written
as prose rather than as tracked work, and that nothing in the archive step checks a deferral against the
board. Fixing the three individually would leave the mechanism untouched and would not tell the maintainer
whether spec-028 is unusual.

**Recommendation: one repo-wide sweep, not three fixes.** The useful question is *"does any archived spec's
`0.0.X` deferral have a card?"*, and it is mechanically answerable. Sized here so the decision is not made
blind (evidence only — nothing was edited, and this is the sweep's **input** population, not its finding: most
of these lines will be shipped-version labels or already-carded work):

```
archived specs scanned: 57
specs with >=1 line carrying a deferral verb AND a 0.0.X/0.1.X version token: 34
total candidate lines: 203
  18  spec-027-filters-0_0_8.md
  17  spec-035-optimizer_hardening-0_0_10.md
  17  spec-028-orders-0_0_8.md
  13  spec-032-full_relay-0_0_9.md
  10  spec-034-permissions-0_0_10.md
```

**`spec-028` is not an outlier** — `spec-027` carries more — which is itself the argument for a sweep rather
than three edits. R4's cross-reference audit is already shaped to run it: extract every candidate line, grade
each as *shipped-version label* / *carded* / *orphan*, and report the orphans as one list with a card-or-cut
decision per orphan. Two adjacent findings belong in the same sweep, both measured here:

- **Stale card-state prefixes in shipped source.** `connection.py` #"WIP-ALPHA-033-0.0.9",
  `types/finalizer.py` #"WIP-ALPHA-033-0.0.9", and `types/relay.py` #"WIP-ALPHA-032-0.0.9" name cards that
  `KANBAN.md` now carries as `DONE-033-0.0.9` and `DONE-032-0.0.9`. Not orphaned deferrals — the work shipped
  — but the same failure to re-visit a forward reference after its target moved.
- **Raw spec line numbers in code comments** (`AGENTS.md` rule 27). `grep -roiE "(Decision [0-9]+|Edge cases?)
  line [0-9]+" django_strawberry_framework/ | wc -l` → **8** package-wide, two of them in the very function
  this pass edited (`orders/inputs.py::_column_backed_field_names` #"Decision 3 line 452" and
  `orders/inputs.py::_build_input_fields` #"Edge cases line 980"). A spec line number rots exactly as a
  `path:NN` does.

### Gates

1. `uv run ruff format django_strawberry_framework/orders/inputs.py` → **1 file left unchanged**. Scoped.
2. `uv run ruff check --fix django_strawberry_framework/orders/inputs.py` → **All checks passed!** Scoped.
3. `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/orders/inputs.py` →
   exit **0**. The stop-and-report caveat never engaged: the file was clean at HEAD before the edit
   (`git status --porcelain django_strawberry_framework/orders/` named only `sets.py`), so no concurrent
   session owns any line in it, and the auto-fixing form was never run.
4. `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-028-orders-0_0_8.md` → exit **0**,
   `OK: 44 terms - all have glossary entries and at least one spec link.` (44 → 44.)
5. `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-028-orders-0_0_8.md` → exit **0**.
6. `AGENTS.md` rule 17 — longest touched line **89** chars; non-ASCII count over the whole file **0**.
   Rule 27 — both edited sites cite a symbol path (`filters/inputs.py::convert_filter_to_input_annotation`)
   and a named spec Decision; neither carries a line number.

### Byte and line counts

| File | before (bytes / lines) | after (bytes / lines) | delta |
|---|---|---|---|
| `django_strawberry_framework/orders/inputs.py` | 16,387 / 355 | **16,327 / 354** | -60 bytes, -1 line |
| `docs/SPECS/spec-028-orders-0_0_8.md` | 289,179 / 1,354 | **289,179 / 1,354** | **untouched this pass** |
| `docs/builder/bld-009-r2-spec028_distinct_reconciliation.md` | 103,615 / 1,174 | **133,344 / 1,577** | +29,729 bytes, +403 lines (this section, the 5 new checklist boxes, the `Contract:` / `Status:` header lines). Measured after the last content edit; this row is itself the final edit, so it is line-stable and its own byte delta is the only figure it cannot include |
| `docs/builder/worker-memory/spec-009-worker-1.md` | 18,697 / 47 | **19,028 / 42** | +331 bytes, **-5 lines** — the three R2 entries consolidated into one before appending, per `BUILD.md` `### Worker memory`'s consolidate-before-appending cap |

`git diff --numstat` → `5 6` for `orders/inputs.py`, `49 57` for the spec (unchanged from the prior pass),
`1 1` for `orders/sets.py` (the prior pass's, untouched here). No spec edit was owed: the spec asserts nothing
about the converter's parameters — `grep -niE "forward[ -]compat|future[ -]extension|reserved"` over the spec
returns only the `Predecessors:` line, the two revision-log bullets already corrected, and `:34` / `:43`,
all past-tense and all true.

### Non-sweep proof

`git log --stat` over every writable path, never `git status` alone:

- `django_strawberry_framework/orders/inputs.py` — newest commit touching it is **`5d27a13b`** ("Share
  FilterSet and OrderSet Decision-9 input namespace lifecycle"), which predates this cycle's dispatch. Its
  working-tree diff is this pass's `5 6` hunk and nothing else.
- `docs/SPECS/spec-028-orders-0_0_8.md` — newest commit is still **`40e4754a`**, unchanged across all three
  R2 passes.
- `docs/builder/bld-009-r2-spec028_distinct_reconciliation.md` — `git log --` → **empty** (never committed).
- `docs/builder/worker-memory/spec-009-worker-1.md` — `git log --` → **empty** (gitignored).
- `git show --stat HEAD` names `KANBAN.html`, `KANBAN.md`, `examples/fakeshop/db.sqlite3` — none of mine.
- HEAD is **`6f8bf818`** at both ends of this pass, re-derived rather than trusted.

### Spec changes made (Worker 1 only)

**None.** `docs/SPECS/spec-028-orders-0_0_8.md` was re-read and is byte-identical to its state at the end of
the prior pass (289,179 / 1,354; `--numstat 49 57`). Its `Status:` / `Owner:` / `Predecessors:` header block
was re-verified this spawn per `worker-1.md` `## Spec status-line re-verification` and still describes the
build's state; nothing in this pass falsifies a status line.

One source edit and one artifact-header edit were made:

| Site | Change | Reason |
|---|---|---|
| `django_strawberry_framework/orders/inputs.py::convert_order_field_to_input_annotation` (docstring clause) | forward-compatibility / future DISTINCT ON extension in `0.0.9` → shape-symmetry, "not for a DISTINCT ON extension -- per spec-028 Decision 12 no DISTINCT ON surface ships" | M1 (pass 2), under `### Maintainer decision 7` as amended. Shipped source no longer justifies two parameters by a surface the Decision it cites rejects |
| `django_strawberry_framework/orders/inputs.py::convert_order_field_to_input_annotation` #"kept for shape-symmetry (see docstring)" (`del`-line comment) | `# reserved for future-extension (see docstring).` → `# unused; kept for shape-symmetry (see docstring).` | M1 (pass 2), same authorization. The comment pointed at the docstring for exactly the rationale being cut; it now points at the reason that survives |
| this artifact's `Contract:` header line | "(one source docstring clause)" → the amended scope | the parenthetical described Decision 7 before its amendment and was falsified by it. Header metadata, not a prior section; recorded here rather than left false at the top of the file |

### Recorded for the maintainer / R4 — NOT repaired here

Items 1-5 stand as written in `## Final verification`. Item 6 is **closed** by this pass (the fix landed).
Items 7 and 8 are restated corrected, and two are new:

7. **A THIRD orphaned deferral in `spec-028` — TWO sites, `:734` **and** `:41`.** `:734` (`### Decision 8`
   step 4) defers the position-side-channel leak-closing design "likely to a sibling `0.0.9`
   ordering-permissions card"; `:41` (the `Revision 2` `N-new-1` bullet) quotes that wording. No such card
   exists in `KANBAN.md` or `BACKLOG.md` (0 hits for three token spellings) and `0.0.9` shipped. `:41` is a
   **decided non-edit** — a revision-log bullet records what a review round did, and rewording it would
   desync it from the text it quotes. Decision 8's subject, so `### Maintainer decision 3`'s scope limit does
   not reach either site.
8. **`### Decision 3`'s heading residue.** Unchanged from the prior pass: kept deliberately (6 in-file anchor
   uses, no version, no phantom owner, shipped source uses the same word). A preference, not a defect.
9. **THE PATTERN — three orphaned deferrals in one spec, answered by one sweep rather than three fixes.**
   Stated in full under `### The pattern` above, with the sweep sized (57 archived specs, 34 carrying at
   least one deferral-plus-version line, 203 candidate lines, `spec-027` carrying more than `spec-028`) and
   two adjacent findings folded into the same sweep: three stale `WIP-ALPHA-03x-0.0.9` card prefixes in
   shipped source naming cards that are now `DONE`, and 8 package-wide raw spec-line refs in code comments
   against `AGENTS.md` rule 27. **This item replaces three separate fix requests with one decision.**
10. **The residual third future-extension site in `orders/inputs.py`.** `_build_input_fields`
    #"future-extension" calls `model_field` discovery "a future-extension affordance the converter ignores
    today", and `_build_input_fields` #"reserved -- see" points at the corrected converter. Excluded by the
    amendment's own scope limit ("nothing else in that module is"), so reported. Neither is false today —
    `spec-028:1171`'s enum fallback is demand-contingent and undated — but they are the same rationale's
    third and fourth instances in one module, and they are what the next authorization should cover if the
    maintainer wants the module to speak with one voice.

### Summary

M1 (pass 2) is closed on both halves. Item 6's record is corrected in this pass's own section — the fix is
**two sites, not one docstring clause**, and Decision 7's "three" was a cardinality asserted about the world
rather than a scope election — and the fix itself is performed, because `### Maintainer decision 7` was
amended between the review and this pass to authorize exactly those two sites. Both now state what is true:
the DISTINCT ON extension is rejected, the parameters survive on the shared converter shape they were always
half-justified by, and the clause quotes `### Decision 12`'s own heading vocabulary so it asserts nothing new.

The citation population was re-derived a final time from a **moved corpus** rather than a widened pattern —
package + tests + examples + scripts, 45 occurrences of the shortest token, every one opened, 41 discarded as
other specs' Decision 12 — and it is still four. **All four shipped citations of `spec-028` `### Decision 12`
now agree with the rewritten Decision**, so the gate Decision 7 set closes without the exception the prior
pass had to state. Both Lows are closed: L1's false reason clause is corrected while its number stands
(`spec-028:10` carries the surviving third anchor use), and item 7 now names both `:734` and `:41`. The three
orphaned deferrals reach the maintainer as one pattern with a sized, repo-wide sweep instead of three fixes.

Status: `planned`.

---

## Review (Worker 3, pass 3)

Read-only audit at HEAD `6f8bf818`, re-derived at both ends of this pass rather than carried from the
dispatch. Fresh invocation: no in-context memory of either prior pass's reasoning, only
`docs/builder/worker-memory/spec-009-worker-3.md`. Every number in
`## Build report (Worker 1, apply-changes pass 2)` was re-measured from the tree, and the population that
decides this item was re-derived with a **third instrument** — neither prior pass's grep was run.

`### Failability proofs` and `### Hot-path budget` are stated rather than omitted, because the diff again
includes source lines:

- **Failability proofs — not applicable, proved rather than asserted.** The whole source footprint is
  `git diff --numstat -- django_strawberry_framework/orders/inputs.py` → `5 6`, and
  `docs/builder/temp-tests/r2/w3p3_ast.py` parses HEAD's copy and the working-tree copy, strips every
  module/class/function docstring from both, and compares `ast.dump`: **14,158 chars each, identical.**
  Comments never reach the AST at all. So no statement, expression, signature, default, branch, guard, gate,
  or rejection path changed — there is no boundary to mutate and no row that could go from pass to fail.
- **Hot-path budget — not applicable.** `### Maintainer decision 7` is explicit that R2 "does **not** become
  a code item"; Worker 1's plan declares no hot path; a docstring and a comment are not executed. There is no
  before/after number to carry.

**Static helper.** `scripts/review_inspect.py` **skipped**, recorded per `BUILD.md`
`### When to run the helper during build`: no new `.py` file, nothing under `optimizer/` or `types/`, and the
diff adds zero lines of logic (AST-identical, above), against a 30-line trigger.

### High:

None.

### Medium:

None.

### Low:

#### L1 (pass 3) — the sweep's sizing is right in shape and its ranking clause does not survive a second instrument

`### The pattern` sizes the recommended repo-wide sweep so the maintainer does not decide blind, which is the
right instinct and the reason this item is worth reading. Two of its figures do not reproduce:

- **"archived specs scanned: 57."** `ls docs/SPECS/spec-*.md | wc -l` → **56**. `ls docs/SPECS/*.md | wc -l`
  → **57**, the extra file being `docs/SPECS/NEXT.md`, the archive procedure rather than a spec. Off by one,
  and immaterial to the decision.
- **"`spec-028` is not an outlier — `spec-027` carries more."** This is the load-bearing clause, and it is
  instrument-fragile. Worker 1's set puts `spec-027` at 18 and `spec-028` at 17. A narrow reconstruction
  (`defer(red|s|ral)?` AND `0.[01].N` on one line) returns 56 / 32 / **143** with `spec-035` top at 17,
  `spec-028` at 11 and `spec-027` at **10** — below it. A broader set (adding `non-goal`, `out of scope`,
  `follow-up`, `follow-on`, `postpone`, `punt`, `later card`, `sibling card`, `tracked elsewhere`) returns
  56 / 35 / **297** with **`spec-028` top at 30** and `spec-027` at 24. The rank order flips with the token
  set, over a population the same paragraph correctly says is mostly noise ("most of these lines will be
  shipped-version labels or already-carded work"), so a rank inside it supports neither "outlier" nor "not
  outlier".

Why it matters: the recommendation — one sweep rather than three fixes — is **correct and independently
supported**, by the three orphaned deferrals, their zero cards, and the missing archive-step check. It does
not need the ranking, and the ranking is the kind of fluent supporting clause under a correct conclusion that
this cycle has now produced eighteen times. Recommended change if a later pass touches the item: keep the
recommendation and the candidate-line evidence, drop or hedge the cross-spec comparison, and say 56.

**Disposition — recorded, not held.** No revision is requested and this finding does not hold the pass open.
It is artifact-only prose in a section that labels itself evidence rather than finding; the decision it feeds
is unchanged under all three instruments (the sweep is worth running either way); and a fourth round-trip on a
sizing footnote would cost more than the correction. Recorded here so it is a decided non-edit rather than an
unnoticed one, and repeated under `### Notes for Worker 1` so it travels with the item to the maintainer.

### DRY findings

None to consolidate. One challenge closed, one affirmed, one carried.

- **The pass-2 existence challenge on the two unused parameters is now ANSWERABLE, and the answer is "keep".**
  Pass 2 carried it forward unresolved: once the DISTINCT ON reason is gone, does an unused-parameter pair
  earn its place on symmetry alone? Evidence rather than opinion — the twin **uses both**.
  `filters/inputs.py::convert_filter_to_input_annotation` takes `(filter_instance, model_field,
  owner_definition, filterset_cls)` and reads `model_field` and `owner_definition` on live branches
  (`filters/inputs.py:399`, `:404`, `:406`, `:408`, `:427`, through `_element_annotation` and
  `_owner_type_name`), and the same asymmetry repeats one level up: `filters/inputs.py::_build_input_fields`
  forwards `owner_definition` at `:785` while `orders/inputs.py::_build_input_fields` `del`s it. So the
  mirrored signature is a real family shape whose filter half is load-bearing, not decoration retained by
  habit — which is exactly what `utils/inputs.py` #"Domain semantics stay at the call sites" declares the two
  `inputs` modules to be, with the neutral scaffold single-sited in
  `utils/inputs.py::emit_set_input_field_triples`. I am closing the challenge rather than leaving it hanging
  for the maintainer: deleting the pair would break the deliberate mirror and buy nothing.
- **The single-normative-site shape still holds under the widest instrument yet.** Decision 12's DISTINCT ON
  contract is asserted in exactly two source places, both attribution glosses pointing at the Decision
  (`orders/sets.py::OrderSet.get_flat_orders`, `orders/inputs.py::convert_order_field_to_input_annotation`);
  no module restates the mechanism. Re-confirmed on the subject axis, not just the token axis — see
  `### What looks solid`.
- **Carried, correctly recorded as item 10.** One rationale now has four instances in one module and three
  vocabularies (`shape-symmetry` at the converter, `reserved` at `:232`, `future-extension` at `:236`). That
  is a DRY observation about prose, not code, and the amendment's scope limit excludes it. Item 10 is where it
  belongs.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**; piped to `wc -c` → **0 bytes**, and
`git diff --stat` names the file not at all. `__all__` and the re-export list are unchanged. The converter is
module-private to `orders/inputs.py` in the sense that matters here — the diff changed a docstring body and a
comment, so no export could move even in principle (AST-identical, above).

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applies (the pass touches one shipped docstring; the archived spec is untouched this pass). All checks pass.

- **Gates, re-run rather than trusted, each scoped and none auto-fixing.**
  `uv run ruff format --check django_strawberry_framework/orders/inputs.py` → **1 file already formatted**,
  exit 0. `uv run ruff check django_strawberry_framework/orders/inputs.py` (no `--fix`, so the tree cannot be
  mutated by my audit) → **All checks passed!**, exit 0.
  `check_trailing_commas.py --check` → exit **0** on `orders/inputs.py`, on
  `docs/SPECS/spec-028-orders-0_0_8.md`, and on this artifact.
  `check_spec_glossary.py --spec docs/SPECS/spec-028-orders-0_0_8.md` → exit **0**,
  `OK: 44 terms - all have glossary entries and at least one spec link.`
- **`AGENTS.md` rule 17.** Longest **touched** line is `:200` at **89** characters (the `del` comment); the
  four touched docstring lines are 72 / 69 / 71 / 71. Longest line in the whole file is `:316` at 96, inside
  100 and pre-existing. `grep -cP '[^\x00-\x7F]'` over the file → **0**.
- **`AGENTS.md` rule 27 on the touched lines.** The docstring cites
  `filters/inputs.py::convert_filter_to_input_annotation` symbol-qualified and the spec by Decision number;
  the comment cites the docstring. Neither carries a line number. (Two *untouched* lines in the same module do
  — `:161` and `:222` — and they are two of the 8 the pattern item already routes to the maintainer.)
- **Counts reproduce to the byte.** `orders/inputs.py` **16,327 / 354** now against **16,387 / 355** at HEAD
  (`git show HEAD:` piped to `wc`), `--numstat 5 6`. `docs/SPECS/spec-028-orders-0_0_8.md` **289,179 / 1,354**
  — byte-identical to the value the prior pass recorded, `--numstat 49 57` unchanged, confirming the spec was
  not touched this pass. This artifact was **133,499 / 1,577** immediately before my append, against the
  report's `133,344 / 1,577`: the lines match exactly and the 155-byte gap is the counts row's own text, which
  that row explicitly says it cannot include.
- **No orphan copies of the retired phrase, repo-wide.** Per my standing instrument (a fix at the cited line
  is not a fix), `grep -rniE "reserved for future-extension|forward-compatibility \(Spec Decision 12|a future
  DISTINCT ON"` over `*.py` / `*.md` / `*.csv` / `*.html` across the whole repo returns **two** hits, both in
  `docs/builder/build-009-rich_schema_architecture-0_0_4.md` `### Maintainer decision 7`'s amendment, which
  quotes the before-text deliberately. Zero elsewhere: no standing doc, no glossary, no test, no CSV carried a
  copy.
- **Script-rendered docs are unaffected, attributed rather than assumed.** `docs/TREE.md` renders from
  **module** docstrings; the edit is inside a function. `diff` of the first 40 lines of HEAD's copy against the
  working tree → identical, and `docs/TREE.md:266`'s `orders/` row still matches that module docstring's first
  line. `build_tree_md.py --check` **does** report drift, and it is **not** attributable to R2: `docs/TREE.md`
  itself is clean in the working tree while `git status --porcelain django_strawberry_framework/` names **66**
  dirty source files from the concurrent cycles. Recorded so a later pass does not charge it to this one.
- **Provenance by `git log --stat`, never `git status` alone.** Newest commit touching `orders/inputs.py` is
  **`5d27a13b`**, which predates this cycle's dispatch, so the working-tree diff is this pass's hunk and
  nothing else. `git log -- docs/builder/bld-009-r2-spec028_distinct_reconciliation.md` → **0 commits**.
  HEAD `6f8bf818` at both ends of this pass.
- **Append-only, proved by comparison not by prose.** The artifact was `shasum -a 256`
  `0d80499...3d6595c` at 1,577 lines before this section; the same 1,577-line prefix hashes identically after
  it (`head -1577 | shasum`). No prior section was edited. The only non-append edit is the top-level
  `Status:` line, which the dispatch assigns to me.

### What looks solid

Everything the dispatch put in question holds. Reproductions, all independent of the report's own commands:

- **The diff is comment-and-docstring only, and the `del` still runs — proved by AST, not by reading the
  hunk.** Docstring-stripped `ast.dump` of HEAD's `orders/inputs.py` and the working tree are **identical**
  (14,158 chars each). The converter still carries **exactly one** `ast.Delete`, with targets
  `['model_field', 'owner_definition']`, as the first statement of the body after the docstring and under no
  branch; the signature is still `['model_field', 'owner_definition']` with one default. No behavior change,
  no signature change, no `del` removed, nothing else in the module — each of the four, separately confirmed.
- **The surviving reason is true at the symbol, and materially so.** The docstring now rests entirely on
  shape-symmetry with `filters/inputs.py::convert_filter_to_input_annotation`, and that twin genuinely
  **consumes** both parameters on live branches (see `### DRY findings`). The symmetry is not a rationalisation
  reached for after the real reason was withdrawn: the two parameter names are shared with the twin verbatim,
  the family scaffold is single-sited in `utils/inputs.py::emit_set_input_field_triples`, and both `inputs`
  modules are declared deliberate mirrors by `utils/inputs.py`'s own module docstring. The clause was already
  in the sentence before the fix, so nothing was invented.
- **The replacement text is the Decision's own wording, checked against the Decision.** `no DISTINCT ON
  surface ships` is verbatim `spec-028`'s `## Risks and open questions` answer line, and matches
  `### Decision 12`'s heading and `:995` (`**No declaration surface ships for it.**`). `:1006` records the
  `ASC_DISTINCT` / `DESC_DISTINCT` + `apply_distinct` port as **Rejected**. Per my standing instrument I
  graded the *reason* separately from the *rule*: the rule (the parameters stay) is unchanged and
  AST-identical; the reason (no such surface ships) is the Decision's, quoted rather than paraphrased.
- **Worker 1's scoping of the negation is not merely defensible — it is what keeps the module
  non-contradictory.** Judged, per the dispatch. Two independent supports. (1) `spec-028:1171` really does
  keep a demand-contingent `ASC_DISTINCT` / `DESC_DISTINCT` enum fallback ("if consumers report wanting the
  cookbook's `DISTINCT` modifiers ... a follow-up card can add" them), so a broader "carries no
  forward-compatibility promise" would have asserted more than the spec supports. (2) More decisively, that
  broader negation would have **falsified the out-of-scope site two symbols down**: `orders/inputs.py:236`
  calls `model_field` discovery "a future-extension affordance", about a parameter of the very function being
  corrected. The narrow negation refuses exactly what Decision 12 refuses and nothing more. Correct call.
- **The four-citation gate closes, re-derived with a third instrument on a moved corpus.**
  `docs/builder/temp-tests/r2/w3p3_pop.py` does not grep lines: it reads whole files, strips leading comment
  markers, **normalizes whitespace so a citation wrapped across two source lines is one token**, and matches
  by *number* with an optional prefix word and separator-agnostic spacing
  (`(?:decision|dec\.?|D)[\s_.:\-]*#?\s*12(?!\d)`, case-insensitive) — so `Spec Decision 12`, `spec-046
  Decision 12`, `D12`, `Decision-12` and a line-broken `Decision\n    12` all match, and `Decision 120`
  cannot. Over `django_strawberry_framework/` + `tests/` + `examples/` + `scripts/` it returns **51**
  occurrences across 26 files — six more than the report's 45, i.e. strictly wider — and every one printed
  with context and graded by **reading**. Exactly **four** cite `spec-028`, all under `orders/`:
  `factories.py:22`, `factories.py:150`, `inputs.py:197`, `sets.py:278`. The other 47 are other specs'
  Decision 12 (`spec-039` DRF guard, `spec-046` connection lifetime, `spec-036` mutation `Meta` namespace,
  `spec-032`, `spec-034`, `spec-038`, `spec-040`) or, in one case, my own instrument's false positive
  (`examples/…/library/orders.py:102`, where the `D` alternative matched the "d" of "**and** 12"). **No fifth
  site exists.** Worker 1's number survives an instrument that is wider than its own on both the corpus axis
  and the token axis.
- **And on the subject axis, where no token widening reaches.** `grep -rniE
  "distinct|layer[ -]?6|0\.0\.9|deferr"` over `django_strawberry_framework/orders/` returns 16 lines; every
  one is either a graded citation, real `.distinct()` / distinct-name prose, or `factories.py`'s Layer-6
  cache comments, which say "standing deferred Non-goal" with **no version and no owner** and match `:988`.
  No module asserts the retired deferral without naming the Decision.
- **All four citations agree with the rewritten Decision, checked against the spec text rather than the
  table.** `factories.py:22` / `:150` — "standing deferred Non-goal" against `:988`'s bolded standing
  non-goal. `sets.py:278` — "no DISTINCT ON surface ships", the Decision's own words. `inputs.py:197` — this
  pass's fix, same words. The gate `### Maintainer decision 7` set closes **without an exception**.
- **Item 5's two residual sites are true today, and item 10 is the right disposition.** Verified rather than
  accepted, because the gate depends on it. Neither cites Decision 12 — my sweep finds exactly **one**
  Decision-12 hit in the whole of `orders/inputs.py`, at `:197` — so neither is inside the "all citations
  agree" gate at all. `:232` (`del owner_definition  # reserved -- see ...`) points at the corrected
  docstring, and that docstring still explains why an unused parameter is kept; "reserved" is stale-flavoured
  vocabulary, not a false claim, and it names no version, no card, and no DISTINCT ON. `:236`
  ("`model_field` discovery is a future-extension affordance the converter ignores today") cites **Decision
  5**, which says only that the converter returns `Ordering | None` regardless of field type; nothing in the
  spec forbids a future `model_field`-aware converter, and `:1171`'s fallback is undated and
  demand-contingent. Both vague, neither false. R2 can close.
- **Both Lows landed.** L1: `spec-028:10`'s `Revision 1` bullet does carry a surviving third Decision-12
  anchor use (1 in the revision-log range 3-68 at HEAD, 1 now — a re-point, not a net-new), so "the only" was
  wrong; the number stands, re-derived independently as **25 occurrences on 25 distinct lines** (`grep -o |
  wc -l` = `grep -c` = 25), against **20** old-fragment uses at HEAD. L2: item 7 now names `:734` **and**
  `:41`; `grep -n "ordering-permissions card"` returns exactly those two lines, and `:41`'s status as a
  **decided** non-edit is recorded with its reason.
- **The pattern's substance reproduces.** Three orphaned deferrals, zero cards: `grep -in
  "ordering-permission\|position-side-channel\|side-channel" KANBAN.md BACKLOG.md` → **0**. Both adjacent
  findings reproduce exactly: **3** `WIP-ALPHA-03x-0.0.9` prefixes (`connection.py:2040`,
  `types/finalizer.py:620`, `types/relay.py:694`) against `KANBAN.md`'s `DONE-032-0.0.9` / `DONE-033-0.0.9`,
  and **8** raw spec-line refs in code comments package-wide. One decision rather than three fixes is the
  right packaging — the three instances share one mechanism (a deferral written as prose with nothing
  checking it against the board), and fixing them individually leaves that mechanism untouched.

### Temp test verification

No `pytest` run: the diff contains no executable line (AST-identical), so there is no behavior to exercise,
and no `--cov*` flag was used anywhere in this pass. Read-only verification under
`docs/builder/temp-tests/r2/` (gitignored):

- `w3p3_ast.py` (new) — docstring-stripping AST equivalence between `git show HEAD:` and the working tree,
  plus an AST-level assertion that the `del` statement, its two targets, and the signature survive. Exit 0.
  This is the instrument that turns "the diff looks like comments" into a proof.
- `w3p3_pop.py` / `w3p3_pop_src.py` (new) — the whitespace-normalizing, comment-marker-stripping,
  number-keyed citation sweep described above, with per-file counts and full context lines
  (`pop_src.txt`, `pop_src_summary.txt`).
- Ad-hoc reconstructions of the deferral-sweep sizing under two token sets (L1).
- Pass 1's and pass 2's instruments (`anchors.py`, `links.py`, `denom.py`, `outside.py`, `w3p2_check.py`) were
  **not** re-used, per the dispatch and because three prior sweeps in this cycle were defeated by their own
  greps.

One instrument caution for a later pass, in the cycle's own tradition of publishing them: a citation regex
with `D` as a bare prefix alternative matches the "d" of ordinary words — `and 12`, `used 12` — so a
number-keyed sweep must be graded by reading its context output, never counted. Mine over-reported by one and
the control that caught it was opening the hit.

Disposition: kept for the cycle, deleted with it; the directory is gitignored so nothing reaches a commit.
None is a promotion candidate — there is no behavior to pin.

### Notes for Worker 1 (spec reconciliation)

1. **Nothing is asked of Worker 1 to close R2.** No source edit, no spec edit, no artifact edit is requested.
   L1 (pass 3) carries its own disposition.
2. **Carry L1 (pass 3) with item 9 when it reaches the maintainer.** The sweep recommendation is right and I
   endorse it; its sizing footnote is not load-bearing and its cross-spec ranking flips with the token set
   (`spec-028` is bottom-third under one reconstruction and **top** under another), over a population the item
   itself says is mostly shipped-version labels. The honest framing for the maintainer is "203-ish candidate
   lines across ~34 of 56 archived specs, mostly noise, three known orphans in `spec-028`" — without the
   claim that `spec-028` is or is not typical, which this evidence cannot settle either way.
3. **The pass-2 existence challenge can be closed, not carried.** Pass 2 left "does an unused-parameter pair
   earn its place on symmetry alone" open as a contract-level question for the maintainer. It now has an
   evidence-backed answer — **keep** — because the filter twin consumes both parameters on live branches and
   the mirror is declared in `utils/inputs.py`'s module docstring. Worth removing from the maintainer's queue
   rather than leaving as an open indirection question.
4. **Item 10 is correctly scoped and should stay a report.** Both residual sites are vague rather than false,
   and neither is a Decision-12 citation, so neither blocks the gate. The reason to fix them is that one
   module now uses three vocabularies for one rationale — a legibility argument, not a correctness one. It
   belongs with the pattern sweep, not with R2.
5. **Non-findings, recorded so they are not re-raised a fourth time.** `spec-028:1171`'s demand-contingent
   `Ordering`-enum fallback: a note, graded identically by four passes now. `### Decision 3`'s kept heading:
   confirmed, not re-opened. `factories.py`'s "standing **deferred** Non-goal" wording against the spec's
   "standing non-goal": graded agreeing in the prior pass and I concur — "deferred" there carries no version
   and no owner.

### Review outcome

`review-accepted`.

The two replacement texts are true and the diff is exactly what the amendment authorizes — proved rather than
read: the docstring-stripped AST is byte-for-byte identical to HEAD's, so no behavior, signature, branch, or
`del` changed, and the converter still carries one `ast.Delete` over both parameters as an unconditional first
statement. The surviving reason holds at the symbol, with the filter twin genuinely consuming both parameters,
and the negation is scoped exactly to what Decision 12 rejects — which is not just defensible but load-bearing,
since a broader negation would have falsified a site two symbols below.

The gate `### Maintainer decision 7` set **closes**. I re-derived the citation population with a third
instrument on the moved corpus — whitespace-normalized, comment-marker-stripped, number-keyed, wrap-tolerant —
which returns **51** occurrences where the report's returned 45, and it is still **four** spec-028 citations,
all four now agreeing with the rewritten Decision. The subject axis confirms it independently: no module
asserts the retired deferral without naming the Decision. Item 5's two residual sites were verified rather
than accepted, because the gate depends on them: neither cites Decision 12, both are vague rather than false,
and item 10 is the right disposition. Both Lows landed. Every gate re-runs clean at the recorded values, every
count reproduces to the byte, the public surface is untouched, and the one repo-wide orphan sweep for the
retired phrase finds no copy outside the amendment that quotes it deliberately.

One Low is recorded and explicitly **not held**: the pattern item's cross-spec ranking does not survive a
second token set. The recommendation it supports — one sweep rather than three fixes — is correct without it,
and a fourth round-trip on a sizing footnote would cost more than the correction. It travels to the maintainer
with item 9 under note 2.

Status: `review-accepted`.

---

## Final verification (Worker 1, closing pass)

Titled `closing pass` because `## Final verification (Worker 1)` above is the combined plan+perform pass's own
wrap-up section; a duplicate top-level heading would give this file two identical slugs. Nothing above this
line was edited: this section appends at top level, and the only non-append change is the file's top-level
`Status:`, which the dispatch assigns to me.

Read-only. **Nothing was edited in the spec, in either source file, or in any prior section** — the sixth
consecutive verification pass on this cycle to close having written only its own section. HEAD re-derived at
both ends: **`6f8bf818`**, unmoved.

### What I re-derived rather than accepted

- **The whole diff, read cold in file order at its symbols** — `orders/inputs.py` (5/6), `orders/sets.py`
  (1/1), `docs/SPECS/spec-028-orders-0_0_8.md` (49/57), in that order, before reading any pass's account of it.
- **Comment-and-docstring-only, proved by AST and extended past the proof on file.** Worker 3 pass 3 stripped
  docstrings from `orders/inputs.py` at HEAD and in the tree and compared `ast.dump` (14,158 chars, identical).
  Reproduced exactly — **14,158 = 14,158** — and extended two ways: (a) the same proof run on
  `orders/sets.py`, which no pass had AST-checked, is also identical (**18,101 = 18,101**); (b) the
  *docstring-retaining* dumps of both files differ, which is the control that shows the stripping is what
  produced the equality rather than the files being identical. Comments never reach the AST at all. So no
  statement, signature, default, branch, guard, or rejection path changed in either file.
- **The three changed prose lines, true at their symbols.**
  `orders/inputs.py::convert_order_field_to_input_annotation` — the two parameters are `del`'d as the first
  body statement and read nowhere, and the surviving reason holds:
  `filters/inputs.py::convert_filter_to_input_annotation` takes `(filter_instance, model_field,
  owner_definition, filterset_cls)`, sharing both names verbatim. The `del`-line comment now names the reason
  the docstring actually gives. `orders/sets.py::OrderSet.get_flat_orders` returns
  `list[tuple[str, Ordering | None]]` with no DISTINCT half, and its replacement gloss quotes
  `### Decision 12`'s heading.
- **All four shipped citations, with a fourth instrument.** Mine is wrap-tolerant like Worker 3 pass 3's
  (whole-file read, whitespace normalized, so a citation broken across two source lines is one token) but
  **drops the bare `D` alternative** that made that instrument over-report by one, and it sweeps the **whole
  repository** rather than four directories. Result: **54** occurrences in `.py` across 27 files (7 of them in
  the gitignored `docs/builder/temp-tests/r2/` scratch), every one printed with 150 characters of context and
  graded by reading. Exactly **four** cite `spec-028`, all under `orders/`: `factories.py:22`,
  `factories.py:150`, `inputs.py:197`, `sets.py:278`. The other 50 are `spec-039`, `spec-046`, `spec-036`,
  `spec-032`, `spec-034`, `spec-038`, `spec-040`, or a bare `Decision 12` whose own docstring block names a
  different spec. **No fifth site, and no false positive.** All four agree with the rewritten Decision:
  both `factories.py` sites say "standing deferred Non-goal" with no version and no owner against `:988`'s
  bolded standing non-goal; `sets.py:278` and `inputs.py:197` both say "no DISTINCT ON surface ships", the
  Decision's own words. **The gate `### Maintainer decision 7` set closes.**
- **Decision 12's mechanism claims, each opened at HEAD where the module is concurrent-dirty.**
  `orders/sets.py::OrderSet._resolve_order_expressions` — `models.Min if direction.is_ascending else
  models.Max`, gated by `_path_traverses_to_many`, `else` arm orders directly. `orders/inputs.py::Ordering` —
  six members, matching `~/projects/strawberry-django-main/strawberry_django/ordering.py::Ordering`
  member-for-member. `connection.py::_synthesized_signature` at HEAD — the `CONNECTION_ORDER_KWARG` append is
  guarded by `if definition.orderset_class is not None`, and `_pipeline_sync` / `_pipeline_async` apply it.
  `types/base.py` at HEAD — `DEFERRED_META_KEYS = {aggregate_class, fields_class, search_fields}`,
  `ALLOWED_META_KEYS` is 17 keys with neither `distinct` nor `distinct_class`, and the typo guard
  (`unknown = sorted(declared - ALLOWED_META_KEYS - DEFERRED_META_KEYS)`) raises. Zero `distinct_on` /
  `Meta.distinct` / `distinct_class` occurrences package-wide; graphene-django carries 0 DISTINCT ordering
  directives. `get_orderset_class` / `_dynamic_orderset_cache`: importers repo-wide are
  `tests/utils/test_inputs.py` and `tests/orders/test_factories.py` only.
- **`:479`'s absolute, because this cycle's rule is that absolutes are false by construction.** "Every
  consumer declares an explicit `Meta.orderset_class`" survives: `orders/__init__.py::_helper_referenced_ordersets`
  feeds a finalizer orphan check (`types/finalizer.py` #"helper_ledger=_helper_referenced_ordersets") that
  raises for any `OrderSet` reached through `order_input_type` but never wired via `Meta.orderset_class`. The
  absolute is enforced, not asserted.
- **`spec-009` `### Layer 7` still agrees with the rewritten Decision 12.** Layer 7 states the same rule in
  the same words — *"order ascending terms by `Min(path)` and descending terms by `Max(path)`, then order by
  the alias"* — plus the same six-member enum, and carries no `ASC_DISTINCT` / `DESC_DISTINCT` /
  `DISTINCT ON` (the spec's three `distinct` hits are ordinary English). spec-028 says **less** — it omits the
  primary-key-tiebreaker clause, deliberately — and less is agreement, not divergence.
- **Gates, counts, anchors, and links, all re-run with my own checker.** `check_spec_glossary.py` exit **0**
  (`OK: 44 terms`); `check_trailing_commas.py --check` exit **0** on the spec, both source files, and this
  artifact. `wc -c -l`: spec **289,179 / 1,354** (HEAD 291,903 / 1,362), `orders/inputs.py` **16,327 / 354**
  (HEAD 16,387 / 355) — both reproduce to the byte. `--numstat` `49 57` / `5 6` / `1 1`. In-page anchors
  **159 uses / 21 fragments / 0 unresolved / 0 duplicate heading slugs**; link defs **103 / 0 undefined /
  1 orphan (`[relay]`)**, and the identical 103 / 0 / 1 at HEAD, so the orphan is pre-existing. Raw `path:NN`
  **0**. My slug function collapses only `[*_]{2,}` runs, so it never eats the single underscores that
  produced two prior passes' false unresolved anchors.
- **The anchor arithmetic, closed rather than sampled.** Counting every in-page fragment at HEAD and now,
  the only four that moved are: old D12 fragment **20 -> 0**, new D12 fragment **0 -> 25**,
  `#decision-5--ordering-enum-and-argument-shape` **24 -> 25**, and `#non-goals` **2 -> 0** (both uses sat
  inside text this pass rewrote at `:493` and `:987`). Totals **155 -> 159**. That reconciles `20 re-pointed +
  5 net-new = 25` exactly and explains the whole-file delta, which no prior pass did — the `#non-goals` drop
  is the reason total uses rose by 4 while D12 rose by 5. No heading lost an inbound reference it needed and
  no anchor dangles.
- **Non-sweep proof by `git log --stat`, never `git status` alone.** Newest commit touching the spec is still
  **`40e4754a`**; `orders/sets.py` **`5851bb59`**; `orders/inputs.py` **`5d27a13b`** — all predate this
  cycle's dispatch. `git log --` for this artifact returns **0 commits**. `git status --porcelain
  django_strawberry_framework/orders/` names exactly `inputs.py` and `sets.py`, this item's own two files.
- **No `TODO(spec-028` anchor survives anywhere in source or docs** (the one hit is this artifact quoting the
  retired anchor text). The staged-anchor sweep proper is R4's; this is the one anchor R2's own subject owned.

### No tests were run

**This item changed only prose — two docstring/comment lines in `orders/inputs.py`, one docstring line in
`orders/sets.py`, and spec text.** The AST proof above is what stands in for a test run: there is no
executable line in the diff, so there is no behavior to exercise and no row that could go from pass to fail.
No `pytest` was invoked in this pass, and no `--cov*` flag anywhere. The repo-wide staged-anchor sweep belongs
to R4.

### Dispatched findings checklist — audited against the diff

Self-derived, as a review round requires. **Every box maps to a real edit, and every edit maps to a box.**
Audited mechanically: the hunk headers of `git diff -U0` give the HEAD-side line set, which I compared against
the checklist's cited lines rather than re-reading the checklist against itself.

- **Every ticked box's cited HEAD line is in a hunk.** `:10`, `:34`, `:43`, `:160`, `:163`, `:196`, `:197`,
  `:200`, `:220`, `:221`, `:243`, `:462`, `:479`, `:493`, `:497`, `:499`, `:524`, `:526`, `:527`, `:531`,
  `:536`, `:541`, `:542`, `:664`, `:979`, `:983`, `:985-991`, `:993-998`, `:1002-1004`, `:1008-1015`,
  `:1130`, `:1177-1179`, `:1200`, `:1201`, `:1214` — all present, and I read each replacement's text against
  the box's claim. No box over-ticked.
- **The two hunks not named by a substantive box are both accounted for.** `:91` is touched but its box is
  correctly `- [ ]`: the change there is the anchor fragment only, which the "20 in-file anchor uses
  re-pointed" box owns, and the prose ("the one genuinely fresh design question, resolved by Decision 12") is
  true unchanged. That is consistent with the denominator method, which normalises the rename out before
  grading and lists `:91` among the 17 held. `:1187` is M2's `(deferred)` parenthetical, boxed as **M2**.
- **The one unticked box carries its reason.** `spec:91` records "**No change needed**" in the box and again
  in `### Spec changes made (Worker 1 only)`'s table. That is a decided non-edit with a stated ground, not a
  silent un-tick and not an undeferred gap.
- **Each builder's on-disk required-amendment list is discharged.** `### Maintainer decision 7`'s amendment
  authorizes exactly two sites in one file; both landed, and nothing else in that module moved
  (`orders/inputs.py` `--numstat 5 6`, all inside one function's docstring and its `del` comment).

### Cross-pass consistency — no single pass saw the whole

Checked for duplication and inconsistent shape across the plan, three build reports, and three reviews taken
together:

- **The replacement vocabulary is one shape, not two.** `no DISTINCT ON surface ships` landed byte-identically
  at `orders/sets.py` (pass 1) and `orders/inputs.py` (pass 2), and both quote `### Decision 12`'s heading.
  Two passes, separated by two reviews, converged on one wording rather than two paraphrases — which is the
  outcome the single-normative-site shape exists to produce.
- **The ledger is consistent end to end.** Spec 291,903/1,362 -> 289,500/1,354 -> 289,179/1,354 (untouched by
  pass 2, `--numstat 49 57` at both ends); `orders/inputs.py` 16,387/355 -> 16,327/354. Every figure
  reproduces from the tree.
- **Item numbering holds.** Items 1-5 from the perform pass, 6 (closed by pass 2), 7 and 8 restated corrected,
  9 and 10 added. No item is recorded twice and none was silently dropped.
- **One bookkeeping ambiguity, recorded not repaired.** Two different sites are both called `:1179` in this
  document, in two different line frames: the plan's `:1179` is HEAD-numbered (the `Ordering`-enum fallback
  parenthetical, HEAD `:1177-1179`), while M2's `:1179` is tree-numbered (the glossary-parity bullet, HEAD
  `:1187`). Both are real edits with boxes and both landed; only the label collides. Artifact-only, and the
  artifact closes with the cycle.

### The one Low from pass 3 — I agree, and it is slightly stronger than filed

Measured myself rather than carried: `ls docs/SPECS/spec-*.md | wc -l` -> **56**; `ls docs/SPECS/*.md` -> 57,
the extra being `docs/SPECS/NEXT.md`, the archive procedure. Worker 3 is right on the count.

On the ranking clause, my reconstruction does not merely disagree by instrument — it **fails to reproduce in
the same direction**. Re-running the item's own described token set (a deferral verb AND a `0.[01].N` version
token on one line) over all 56 archived specs returns 34 specs / **186** candidate lines, with
`spec-027`, `spec-028`, and `spec-035` **tied at 17**. So "`spec-028` is not an outlier — `spec-027` carries
more" is not supported even by a close replica of the instrument that produced it, let alone by the narrow and
broad sets pass 3 tried (which put spec-028 below and then top). **A number that inverts under measurement
should not be stated as a fact to a maintainer deciding scope**, so the ranking is dropped here rather than
propagated; the prior section stays as written, per the append-only rule.

The recommendation it sits under is **correct without it**, and I found a better support for it than a rank —
see item 11 below: the identical deferral sentence exists in the sibling spec, which settles "is this shape
specific to spec-028" directly instead of by ordering a mostly-noise population. **The honest sizing for the
maintainer is: 56 archived specs, ~34 carrying at least one deferral-plus-version line, roughly 190-200
candidate lines, most of them shipped-version labels — with three known orphans in `spec-028` and a fourth in
`spec-027`.**

### New findings from this pass — both recorded, neither held

Both are outside R2's writable set, so neither can be closed by re-looping this item; recording them is the
mechanism `### Maintainer decision 3`'s scope limit prescribes.

- **N1 (Medium-shaped, permanent document, not repairable here).** `docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md`
  #"still defers `DISTINCT ON` to `0.0.9`" asserts, in the present tense, that `spec-028` `### Decision 12`
  **still defers** `DISTINCT ON` to `0.0.9`. **R2 falsified that sentence.** It is this cycle's own new text
  (absent from `git show HEAD:` on that file) written by R1, in a document that is tracked, committed with the
  spec, and explicitly **not** a per-cycle scratchpad — so unlike the `bld-*` prose it does not close with the
  cycle. This is exactly the shape `### Maintainer decision 7` widened for at `orders/sets.py`: *this cycle's
  own edit falsified a line in a document one over from whoever was editing.* R1/R1b are `final-accepted` and
  the rationale is outside my writable set, so it is reported, not fixed. The smallest correct fix, if the
  maintainer re-opens: the sentence's second half ("is the same claim's sibling site; reconciling it is a
  separate item") stays true — only the "still defers" clause needs to become past tense or go.
  **How it was found, since three passes swept and missed it:** every prior sweep moved spec -> source or
  widened tokens inside one corpus. This one moved **spec -> other permanent documents**, which is the third
  corpus a reconciliation has and the one nobody had swept.
- **N2 (Low, artifact-only).** `## Review (Worker 3)` `### DRY findings` grounds the keep-don't-delete answer
  on "the filter twin `get_filterset_class` **is** consumed". It is not: `grep -rn "get_filterset_class"
  django_strawberry_framework/` outside `filters/factories.py` returns **nothing**, and repo-wide the only
  importer is `tests/filters/test_factories.py`. **Both** halves of the dynamic-set-factory pair are
  production-unconsumed. The conclusion survives — `utils/inputs.py::make_dynamic_set_getter` stays a shared
  skeleton either way, and pass 3 closed the same challenge on a different and verified ground (the filter
  twin *converter* genuinely reads both parameters on live branches) — so this is the cycle's signature class
  one more time: a false reason clause under a correct conclusion. **Critically, it did not leak.**
  `### Decision 12` claims only that no package path calls the *order* symbols, and `orders/factories.py`'s
  docstrings say the same about their own; neither asserts filter-side consumption. Recorded, not fixed:
  prior sections are never edited, and this document closes with the cycle.

### Summary

**What R2 shipped, for the maintainer at commit time.**

`### Decision 12` is retitled from *"Layer 6 and DISTINCT ON deferred to `0.0.9`"* to
**"No Layer 6 auto-generation and no DISTINCT ON surface"**, and its body now states two contracts that are
true today instead of one promise to a release that shipped five versions ago with neither.

- **Layer 6 is decided, not discharged.** Ordering is **explicit-`Meta.orderset_class` only**: the connection
  field synthesizes its `orderBy:` argument from the already-resolved sidecar
  (`connection.py::_synthesized_signature` appends the parameter only when `definition.orderset_class is not
  None`), and a target type that declares no orderset gets no argument at all. The dynamic-factory symbols
  `orders/factories.py::get_orderset_class` and `_dynamic_orderset_cache` **do exist** — they landed at
  `fd0c7327`, on `utils/inputs.py::make_dynamic_set_getter`, replacing the old `TODO(spec-028 …)` anchor — but
  no package path calls either one. **Auto-generation of an `OrderSet` from a field's `Meta`-shaped kwargs is
  a standing non-goal**, and that matters beyond the spec: two shipped docstrings in `orders/factories.py`
  cite this Decision as the authority for it, so cutting the non-goal would have orphaned live source. Writing
  "the deferral was discharged" for both halves — which the dispatch's own framing invited — would have
  replaced one false sentence with another.
- **DISTINCT ON is discharged by an alternative.** The to-many fan-out the cookbook's `apply_distinct` was
  reached for is prevented **inside the ordering**: `OrderSet._resolve_order_expressions` annotates a to-many
  term with row-preserving `Min` (ascending) / `Max` (descending) and orders by the alias, so the join cannot
  multiply the parent row — portably, with no `DISTINCT` and no PostgreSQL-native construct. The enum stays
  six-membered, and no `Meta.distinct` key or `distinct_on:` argument exists or can be declared (the typo
  guard rejects both). The former deferrals are reframed in place as **rejections**, with reasons.
- **The echo-site sweep's denominator.** Population = every HEAD line matching `/distinct|layer[ -]6/i`:
  **63**. Changed **46**, held **17**, with the anchor rename normalised out first so an anchor-only touch is
  not counted as substantive; all 17 held lines were opened and graded, and a widened-token re-run over 109
  lines (then 141 under a wider set still) found exactly one further stale site, since fixed.
- **All four shipped citations of Decision 12 now agree with it** — `orders/factories.py` x2 (untouched;
  already agreeing), `orders/sets.py::OrderSet.get_flat_orders`, and
  `orders/inputs.py::convert_order_field_to_input_annotation`, the last two corrected under
  `### Maintainer decision 7` as amended. The population was measured four times with four instruments across
  three corpora and is closed at four.
- **Byte and line ledger.** `docs/SPECS/spec-028-orders-0_0_8.md` **291,903 -> 289,179 bytes**, **1,362 ->
  1,354 lines** (`--numstat 49 57`). `django_strawberry_framework/orders/inputs.py` **16,387 -> 16,327
  bytes**, **355 -> 354 lines** (`5 6`). `django_strawberry_framework/orders/sets.py` **1 line changed**
  (`1 1`). No test file, no `CHANGELOG.md`, no `KANBAN.md`, no terms CSV, no spec header line, and no public
  surface moved; `git diff -- django_strawberry_framework/__init__.py` is empty.

### Spec changes made (Worker 1 only)

**None.** `docs/SPECS/spec-028-orders-0_0_8.md` is byte-identical to its state at the end of pass 2
(289,179 / 1,354; `--numstat 49 57`), and no source file was touched. Its `Status:` / `Owner:` /
`Predecessors:` header block was re-read this spawn per `worker-1.md` `## Spec status-line re-verification`:
the opener's "final implementation record, not an open build plan" posture, the `0.0.8` / `DONE-028-0.0.8`
framing, and the `Predecessors:` line all still describe the shipped state, and nothing in this cycle
falsifies them.

Every clean result on this cycle has come from a verification pass that edited nothing, and this is the sixth.

### Recorded for the maintainer / R4 — NOT repaired here

Items 1-10 stand as written in the two prior build reports (item 6 closed, items 7-8 restated corrected,
9-10 added). Three more, all found by this pass:

11. **A FOURTH orphaned deferral, and it is in the SIBLING spec — which is better evidence for the sweep than
    any ranking.** `docs/SPECS/spec-027-filters-0_0_8.md` #"Auto-generation of `FilterSet` from `Meta.fields`"
    reads *"Deferred; … Direct consumer-facing implicit generation lands when `DjangoConnectionField` ships in
    `0.0.9`."* `DjangoConnectionField` shipped in `0.0.9`; implicit generation did not land
    (`get_filterset_class` has **zero** package consumers, only `tests/filters/test_factories.py`); and no
    card names it (`grep -in "auto-generat" KANBAN.md BACKLOG.md` -> 21 hits, all `spec-036` mutation Input
    types; `BACKLOG.md` -> 0). It is the **verbatim twin of the sentence R2 just fixed at `spec-028:200`**,
    which is the point: the shape is not a `spec-028` peculiarity, it is what the two sibling specs were
    written with. Fold into item 9's sweep.
12. **`docs/SPECS/appx/spec-009-…-rationale.md`'s "still defers" sentence is falsified by R2** — N1 above.
    A permanent, tracked, committed document, written by this cycle's own R1, now asserting in the present
    tense that Decision 12 still defers `DISTINCT ON`. Out of my writable set (R1/R1b closed); the fix is one
    clause. This is the same defect class `### Maintainer decision 7` widened for, one document over instead
    of one module over.
13. **Both dynamic-set factories are production-unconsumed, not just the order half** — N2 above. This
    sharpens item 3: `docs/GLOSSARY.md`'s "so no dynamic order factory is shipped" is imprecise for the order
    side, and the same question ("is this pair dead code, or a deliberately symmetric skeleton?") is now
    open for the filter side too. Contract-level, so not a worker's call; recorded because the two halves
    should be answered together rather than one at a time.

Status: `final-accepted`.
