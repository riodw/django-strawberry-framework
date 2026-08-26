# Build: Cross-slice integration pass (`030` residual reconciliation cycle)

Spec reference: `docs/SPECS/spec-030-connection_field-0_0_9.md` (whole file, read end to end)
Rationale companion: `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md` (whole file, read end to end; I own it)
Terms companion: `docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv` (`notes` column only, per the plan's `## Mid-cycle scope amendment`)
Build plan: `docs/builder/build-030-connection_field-0_0_9.md`, checklist item "Cross-slice integration pass"
Status: final-accepted

**Closure path: Worker-1-only, `final-accepted` in this single pass.** Five cross-slice defects were found and all five are inside the fence (spec / rationale / the authorized CSV `notes` column), so they were fixed here rather than recorded. **No defect needs a `.py` change**, so no Worker 2 / Worker 3 dispatch is owed and `Status: planned` is not the right outcome. `BUILD.md` routes a found DRY opportunity to "Worker 1 records them and asks Worker 0 to dispatch Worker 2 for a consolidation pass" — in a prose-only cycle the consolidation *is* Worker 1's, because the duplication is spec text only Worker 1 may touch, so it is performed here and recorded under `### Spec changes made (Worker 1 only)`.

- **Hot-path declaration: none.** Stated explicitly rather than left to be read out of a silence. This pass writes three files — the spec, the companion, and the terms CSV — and no `.py` file at all, so no code runs differently and no number can move. The build plan's conditional clause (a change inside `connection.py::_pipeline_sync` / `::_pipeline_async` / `::_resolve_from_window` / `::_finalize_queryset` or `optimizer/extension.py::apply_connection_optimization`) is not triggered.
- **Floor verification: none.** Stated explicitly. The plan's conditional clause fires only on a `.py` change under `connection.py`, `types/base.py`, `types/definition.py`, or `optimizer/extension.py`. No floor venv was built, none is owed, and the shared `.venv` was not mutated.
- **Boundary count: 0.** No guard, cap, rejection path, or validation branch is added, so no failability proof is owed and the `### Slice splitting` question does not arise.
- **Environment.** `uv run` worked all pass; the concurrent dynamic-version migration that broke it during the rationale pass has settled. `.venv/bin/python` was used for the throwaway instruments only, and is noted per command.
- **No `ruff`.** Both `ruff format` and `ruff check` are no-ops against `.md` / `.csv`, and running them repo-wide would touch a concurrent session's dirty `.py` files. Not run, deliberately.
- **No `--cov*` flag** was used in any invocation this pass, in any form.

## Working-tree baseline re-read (`git status --short`, start and end of pass)

The build plan's baseline list is a snapshot and has moved again. Dirty-and-out-of-scope, never edited and never reverted (`AGENTS.md` rule 34): `AGENTS.md`, `pyproject.toml`, `uv.lock`, and **23** dirty `.py` files — `django_strawberry_framework/__init__.py`, `exceptions.py`, `scalars.py`, plus two the earlier slices' lists do not name (`django_strawberry_framework/_request_body.py`, `middleware/request_body.py`), `scripts/bug_hunt.py`, and the `tests/**` set (`base/test_init.py`, `filters/test_base.py`, `filters/test_factories.py`, `filters/test_inputs.py`, `forms/test_converter.py`, `forms/test_inputs.py`, `forms/test_sets.py`, `test_bug_hunt.py`, `test_exceptions.py`, `test_resource_policy.py`, `test_scalars.py`, `test_schema.py`, `test_sets_mixins.py`, `test_strawberry_patches.py`, `test_views.py`, `mutations/test_operations.py` untracked) — plus `docs/review/**`, `docs/dry/**`, `docs/bug_hunt/**`.

My own footprint at the end of the pass is exactly four paths, none of them a `.py` file:

```text
 M docs/SPECS/spec-030-connection_field-0_0_9.md
 M docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv
?? docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
?? docs/builder/bld-integration-030.md
```

(plus `docs/builder/worker-memory/worker-1.md`, which is `.gitignore`d.)

---

## Plan (Worker 1)

### Spec status-line re-verification

Read on entry: spec lines 1-11 (title, shipped-in line, `Status:`, owner, Predecessors, the rationale-companion pointer). All still describe the build's current state. Slice 3 already corrected line 5's Slice-3 summary and line 9's Predecessors tail; line 5's `## [0.0.9]` release-heading clause is true and is what Slice 5 aligned the DoD with. **No status-line edit was needed or made.** One header-adjacent Key-glossary bullet *was* edited (`:29`), but as part of this pass's own shipped-sibling-status population, not as a status-line repair — recorded as I6.

### The six mandatory pre-writing steps (`BUILD.md` `## Cross-slice integration pass`)

Each ran; each is recorded, including the ones that come back N/A with the reason.

**Step 1 — read every prior artifact in slice order. DONE, all six, in full.** `bld-rationale-030.md` (510 lines), then `bld-slice-1-030-connection_base.md` (295), `bld-slice-2-030-connection_field.md` (305), `bld-slice-3-030-optimizer_cooperation.md` (351), `bld-slice-4-030-live_http_export.md` (301), `bld-slice-5-030-doc_wrap_audit.md` (345). No "as needed" reading; the cross-slice scan below is only possible from the whole set, and three of the five defects were found precisely at the seam between two artifacts' recorded populations.

**Step 2 — confirm the static inspection helper ran or was explicitly skipped, for every Python file with review-worthy logic the build touched. N/A, and the claim is VERIFIED rather than asserted.** The inverse proof: this cycle's own dirty footprint contains **no `.py` file at all**.

```shell
$ git status --short -- docs/SPECS/ docs/builder/ | grep -c '\.py$'
0
$ git status --short -- docs/SPECS/ docs/builder/
 M docs/SPECS/spec-030-connection_field-0_0_9.md
 M docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv
?? docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
?? docs/builder/bld-rationale-030.md … bld-slice-5-030-doc_wrap_audit.md, build-030-connection_field-0_0_9.md
```

Every one of the cycle's nine version-controlled paths is `.md` or `.csv`. The 23 dirty `.py` files all belong to the concurrent session and are out of scope (`AGENTS.md` rule 34). Each slice recorded its own skip with the trigger named — Slice 3's is the sharpest, because `optimizer/` makes the helper *mandatory* when a plan adds logic there and that slice's whole subject is `optimizer/extension.py`; it added none. So the helper's obligation never attached, and this step's N/A rests on a measurement, not on the absence of a finding.

**Step 3 — compare the "Repeated string literals" sections across every shadow overview. N/A: no shadow overview was generated by this cycle.** The reason is step 2's: `review_inspect.py` emits an overview per `.py` file it is pointed at, and this cycle pointed it at none (the pre-flight smoke run on `connection.py` predates the artifact reset and is not a slice's output). **What the cross-file DRY scan would have covered had there been code:** the literals shared across the three modules `030`'s contract spans — `connection.py`'s guard messages (`mutually exclusive`, the pre-sliced and non-queryset `GraphQLError` texts), the `_TOTAL_COUNT_ATTR` private-attribute name shared between `_set_total_count` and the generated `total_count` resolver, the `edges` / `node` / `pageInfo` / `totalCount` selection-path strings shared between `connection.py::_total_count_requested` and `optimizer/selections.py::connection_total_count_selected`, and the `<TypeName>Connection` name-suffix literal shared between the generator and its tests. That is where a cross-slice literal would sit, and it is worth naming because the shipped code already single-sites all four (the count predicate delegates rather than re-deriving, per Slice 2's sub-check 6 and Slice 4's S6) — so a shadow comparison would have confirmed the DRY shape rather than found a violation. **The prose analogue of this step is what this pass actually ran**; see `### The DRY question in this cycle's terms`.

**Step 4 — compare the "Imports" sections across every shadow overview. N/A, same disposition and same reason.** **What it would have covered:** the one-way dependency direction between the four packages `030`'s seam crosses — `connection.py` → `optimizer/extension.py`, `optimizer/plans.py`, `utils/querysets.py`, `filters/`, `orders/` — and specifically whether any of those imports back into `connection.py`. Two facts this pass established by reading instead make the answer visible without the tool: `optimizer/plans.py::ends_in_unique_column` is imported *by* `connection.py` and re-exported there under the old private name (Slice 1's D7, Slice 2's S5), which is a one-way edge with a deliberate alias rather than a cycle; and the `filters` / `orders` edge is a **function-local** import inside `connection.py::_synthesized_signature`, deliberately not module-scope, to keep a bare `import django_strawberry_framework` from eagerly pulling in those subpackages. The second of those is the fact this pass had to put into the spec (I3) — an imports-section comparison is exactly the instrument that would have surfaced it, which is worth recording as the cost of the N/A.

**Step 5 — walk every accepted slice artifact's `What looks solid` and `DRY findings` sections for deferred follow-up. DONE, and this is where the pass's real work came from.** The cycle's artifacts use the procedural-closure shape, so they carry no `## Review (Worker 3)` block and therefore no literal `### What looks solid` / `### DRY findings` headings; their functional equivalents are `### Handed forward to …`, `### CODE GAP list`, `### DRY analysis`, and Slice 5's `### Maintainer findings`. All were walked, and every handed-forward item is dispositioned under `### Carried items 1-9` below. Nothing was dropped silently.

**Step 6 — sweep the whole tree for staged anchors naming this build's spec or card. DONE, re-derived rather than inherited from Slice 5.**

```shell
$ grep -rEn 'TODO\(spec-030|TODO-(ALPHA|BETA|STABLE)-030' . --include='*.py' --include='*.md' \
      --include='*.csv' --include='*.html' --include='*.toml' --include='*.txt' --include='*.cfg' \
    | grep -v '^\./KANBAN\.md' | grep -v '^\./KANBAN\.html' | grep -v '^\./BACKLOG\.md' | grep -v '/\.venv/'
(no output)   EXIT=1
$ grep -cE 'TODO\(spec-030|TODO-(ALPHA|BETA|STABLE)-030' KANBAN.md KANBAN.html BACKLOG.md
BACKLOG.md:0
KANBAN.md:0
KANBAN.html:0
```

**Zero hits, and zero in the excluded board files either** — so the exclusion did not hide anything, which is worth stating: an exclusion that is doing no work reads identically to one that is suppressing a finding. Slice 5's measurement holds. Nothing is routed back to an owning slice and the build does not close on an undischarged anchor.

### The DRY question in this cycle's terms

`BUILD.md`'s DRY-first rule and Worker 3's existence challenge applied to prose. Five independent passes rewrote overlapping regions of one 137KB document, so the question is not "is a contract stated twice" — the spec's **designed** redundancy states each contract in up to five homes (a Decision, a `## Slice checklist` sub-bullet, an `## Edge cases` bullet, a `## Test plan` row, a `## Definition of done` item, plus `## User-facing API` and `### Error shapes` as further contract homes). The question is whether any two of those homes now say **different** things. **This is the one check no single slice could perform**, because each slice saw only its own region, and it produced three of the five defects.

**Was the same shipped-but-unspec'd behavior contracted twice, in different words?** No. Checked both named candidates directly. `_guard_source_not_pre_sliced` (Slice 2's S4) lands at exactly six sites and they are the six designed homes, each stating the same rejection: `## User-facing API`'s contract list (`:268`), `### Error shapes` (`:278`), Decision 7 (`:368`), `## Edge cases` (`:468`), the Test plan (`:497`), and DoD item 5 (`:577`). Two instruments — `already-sliced` (7 occurrences, the extra being `:268`'s parenthetical `pre-sliced`) and the bare stem `slic` — agree, and no site duplicates another's wording as a second contract. The directive-resolved selection gate (Slice 4's S6-S9) lands at exactly four sites, all four chosen deliberately and recorded in that artifact's population table, with the other five selection-gating mentions left alone on a stated reason. **Neither landed twice.**

**Does the companion carry two entries for one decision?** No. Checked the two populations most at risk of a double entry, because two slices each touched them: the symbol-relocation population (Slice 1 opened `### Post-ship: symbol citations the Relay-foundation relocations invalidated`; Slice 2 **extended** it rather than opening a second, and said so) and the empty-plan population (Slice 3 opened a **new** subsection rather than extending, and said why — the populations are disjoint and the first is closed). Both judgements are right and both are recorded at the point of decision. The 14 per-Decision `### Changes this Decision underwent` sections carry one bullet per finding with no duplicate subject.

**Is the same contract now stated in two places in two different ways? YES, three times.** All three are fixed. They are I1, I2, and I3 below, and their common shape is the finding this pass exists to produce: **a contract restated in five homes is a contract only while all five agree, and a partial fix is invisible from inside any one region.**

### CODE GAP list

**Empty.** No cross-slice defect needs a `.py` change. Every one of the five is a spec-text, companion-text, or CSV-`notes` divergence, all inside this pass's fence. Nothing is dispatched to Worker 2, nothing owes a failability proof, and `Status: final-accepted` follows directly rather than `planned`.

### Implementation steps

None. No `.py` step exists to plan. This pass's work is the reconciliation recorded under `### Spec changes made (Worker 1 only)`.

### Test additions / updates

None. No executable surface changed. No temp test was written under `docs/builder/temp-tests/integration-030/`; none would have anything to demonstrate, since every claim this pass makes about shipped behavior is verified by reading source or by an existing pinned test named in the audit below.

### Implementation discretion items

None. Every judgement call is decided and recorded, including the four that could have gone either way: whether to fix the illustrative fence at `:259` alongside `:247` (decided: no, with the reason stated in I1), whether to add the second mechanism fact to the spec or delete the companion's claim about it (decided: add, I3), whether to re-quote the eight CSV rows I was not otherwise editing (decided: yes, I11), and whether to touch `:247`'s directive-gating half while editing its count half (decided: no — Slice 4 decided that question explicitly and a settled point is not re-litigated).

---

## Final verification (Worker 1)

### The reconciled spec, read end to end — the cross-slice consistency verdict

I am the first reader of the reconciled whole; every slice saw only its own region. Read in full (724 lines), then the companion in full (502 lines).

**Verdict: the spec now reads as one coherent current contract, after the three designed-redundancy repairs below.** Before them it did not — two of its five count-mechanism homes contradicted the other three, and one of five rejection-path enumerations was short by one member. Neither is a small mismatch in a place nobody reads: `## User-facing API` is the section a consumer reads first, and `### Error shapes` is the section an implementer reads when writing a guard.

What holds, checked rather than assumed:

- **The five slices' voices are one voice.** No slice left an amendment block, a chronology, a "as of `033`" hedge, or a `(the review round's PN)` parenthetical: `Unreleased`, `Scope honesty`, `flat walker`, `flat-walker`, `connection-unaware`, `empty in 0.0.9`, `currently empty`, `deferred sibling`, `where observable`, `Relay-foundation`, `apply_connection_plan`, `bare \`DjangoConnection`, and `docs/spec-030` are each **0** occurrences in the spec, re-derived this pass rather than inherited from the slice that closed them.
- **The two surviving old-symbol citations are exactly the two licensed ones.** `_apply_get_queryset` = 4 occurrences and `_initial_queryset` = 1, all confined to `:103` and `:104` — the `## Current state` dated observations three slices independently re-derived at the spec's authoring commit `eaaf1385`. No contract statement anywhere names a symbol that does not resolve.
- **No slice's rewrite contradicts another's.** Checked the four seams where two slices edited adjacent or coupled text. Slice 1 renamed Decision 9's heading and Slice 2 renamed Decision 10's; both anchor sets resolve and neither rename left the other's link definitions stale (110 defs, 110 used, zero dangling). Slice 2 edited Decision 11's `Fix:` paragraph while Slice 3 replaced its `Scope honesty` paragraph; read together the Decision states the core-plus-entry-point split, the two short-circuit conditions, the derived plan, and the nested boundary once each, with no repetition and no disagreement. Slice 3's `Aggregate-ordering coexistence` paragraph and Slice 2's ordering-step rewrite both describe the `GROUP BY` interaction and are consistent (Slice 2 states the ordering rule, Slice 3 states what the plan may add on top of it). Slice 4's Decision-4 clause-(b) edit sits inside the same clause Slice 1 rewrote for the count mechanism; both survive in the reconciled clause and neither overwrote the other.
- **The Decision headings and the anchors that name them are in sync across both files.** Every `#decision-N--…` in-page anchor resolves in its own file, and every `[rationale-dN]` / `[spec-030-dN]` cross-file def resolves to a real heading, across both renamed Decisions.

**The companion's verdict: it tells one coherent story of how the contract got there, after the two repairs below.** Its structure holds — provenance, the verbatim revision history, one section per Decision with justification / rejected alternatives / changes-underwent, the non-Decision groupings, and the verbatim Risks body — and the append convention it documents at `:7` was followed by every slice without exception. The moved text still carries claims the Decisions later retracted (Decision 11's rejected alternative calls the plan "(currently empty)"; Risks item 4 says "the derived plan is empty in `0.0.9`"; Decision 7's justification calls the keyset work "deferred"; Decision 9's justification routes stable cursors to `BACKLOG.md` item 39). **That is correct and deliberate, not a defect**: this is the chronology file, the passages are moved text under append-only custody, and every one of them is explicitly retracted by a `**Post-ship:**` bullet in the same Decision's `### Changes this Decision underwent`. Slice 1 established the rule and every later slice honored it. What the companion got *wrong* was two claims about state outside itself, both fixed (I3's source, and I10).

### Populations swept, instruments used, and counts

Every number is an **occurrence** count re-derivable by running the named token against the named file, never a matching-line count, so a claim wrapped across two lines cannot hide. Every population carries a second instrument on genuinely disjoint vocabulary, and every count was measured as it was written.

| Population | Instrument A | Instrument B, disjoint | Union of sites | Post-edit |
|---|---|---|---|---|
| The **count-mechanism** contract | the method names: `.count()` **8** occ (`:63`, `:247`, `:259`, `:279`, `:313`, `:368`, `:399`, `:467`), `.acount()` **6** occ | the reconciled vocabulary, which names no method: `cardinality` **2** occ (`:63`, `:313`) + `own count` / `re-counted` / `already carries` **2** occ (same two lines) | **4 mechanism-claim sites** (`:63`, `:247`, `:259`, `:313`) + DoD item 2 (`:571`, states the value not the method). The other four `.count()` sites are the non-queryset rejection (`:279`, `:368`, `:467`) and Decision 10's materialization sentence (`:399`) — a different claim | `cardinality` **3** occ; the unconditional prose spelling **0**; `:259` retained on a stated reason |
| The `_validate_connection` **rejection-path enumeration** | the number word: `three` / `the three` — **0** occ post-Slice-1, i.e. the instrument that fixed three sites now reports the population closed | the shipped guard body read against each enumeration in turn: `awk` over `types/base.py::_validate_connection` = **4** `raise ConfigurationError`; then every enumeration site found via `non-dict` **4** occ (`:64`, `:275`, `:378`, `:572`) + the Test-plan row (`:487`) | **5 homes**; four listed four rejections, `:275` listed **three** | all 5 list four; `:275` now also states the number, so a count-word sweep has a token next time |
| The **shipped-sibling-status** claim | the status word `planned` — **30** occ, of which the claim sites are `:29`, `:150`, `:154` (the rest are `030`'s own three glossary entries, the `[alpha]` planned tag, `planning`, or `unplanned`) | the future-tense vocabulary carrying no status word: `will (close\|land\|be\|…)` / `lands with` / `after this card` / `not this card` — **4** lines (`:29`, `:37`, `:129`, `:427`) | **4 claim sites**: `:29`, `:37`, `:150`, `:154`. `:129` (`FieldSet` at `0.1.1`) and `:427` (Decision 13 scope) graded not-drift | all 4 reconciled; `the planned root single-node` **0**, `after this card lands` **0**, `planned (\`0.0.9\` — [\`DONE-032` **0**, `planned (\`0.0.10\`)` **0** |
| The **finalize auto-trigger routing** | the spec-side token `uto-trigger` — **12** occ over 8 lines (`:29`, `:30`, `:35`, `:133`, `:419`, `:421`, `:558`, `:666`) | the package-side question, from the other direction: `finalize_django_types(` call sites outside its own definition = **0** in any field factory, and an `auto.trigger|auto_finalize|autofinalize` sweep over `django_strawberry_framework/` = **0** hits; `spec-032-full_relay-0_0_9.md` mentions an auto-trigger **0** times | **1 drifted site** (`:558`, the routing claim). `:133` / `:419` / `:421` are pure scope ("this card does not build it"), true then and now | `deferred to \`032\`` **0** |
| The **`[goal]` orphan** | `\]\[goal\]` inline uses — **0** | the bare token `goal` anywhere in the spec — **1** occ, at `:122`, which is the words `## Non-goals` | **1 site**: the definition itself, at `:600` | definition removed; the file now reports 110 defs / 110 used, zero unused |
| The terms CSV's `notes` **drift** | `WIP-03` card ids — **5** occ over 5 rows | the status vocabulary with no `WIP` token: `stays planned` / `status flips` / `flat-selection` / `Relay-foundation` / `when permissions land` / `after this card lands` / `Planned root` — **9** rows | **12 rows** | both instruments **0** |
| The CSV's **unreadable notes** (new; no slice measured it) | `csv.DictReader` restkey non-empty — **8 of 50 rows** | the raw text: rows with an unquoted `,` inside the third field | **8 rows** (`DjangoListField`, `DjangoNodeField`, `Relay Node integration`, `Meta.connection`, `get_queryset visibility hook`, `ConfigurationError`, `Meta.primary`, `OptimizerHint`) | **0** rows truncate |

**Where the instruments mattered, and how each failed.**

- **The rejection-path row is this pass's sharpest instrument lesson.** Slice 1 closed that population with a sweep for the number word `three`, and post-edit that sweep returns **0** — a clean result on a population that still had a member. `:275` never says "three"; it simply lists three items. **An enumeration is a count claim with no number in it**, so no count-word sweep can establish its population; the only instrument that works is the shipped guard list read against each enumeration in turn. This is a new shape in this cycle's collection: not a claim carried by a heading with no symbol (Slice 2), not one inside a fence (Slice 2), not a positively-spelled census (a prior cycle's) — a claim whose *arithmetic* is the assertion and whose vocabulary contains no number at all.
- **The shipped-sibling-status row needed both instruments and neither alone would do.** `planned` cannot see `:37` (`after this card lands`, no status word); the future-tense sweep cannot see `:150` / `:154` (one-word table cells with no verb). Only the union is the population.
- **The fourth site in that row has a different shape from the first, which is why five passes missed it.** Slice 3 fixed the `033` parity cell and handed the `032` cell forward, describing the defect as "a `planned` status inside a `DONE-` card id". That description became the instrument, and `apply_cascade_permissions`'s row is a `planned` status beside a bare **version number** with no card id — invisible to it. Found only by the row-by-row walk of all nine data rows the task asked for, which is cheap and is exactly the parallel-site discipline this repo keeps relearning. **A finding's own shape is not its population's shape**, the same lesson as "a finding's grep vocabulary is not its population" applied one level up.
- **The finalize-auto-trigger row could not be settled from the spec side at all.** Every spec-side instrument returns the same 8 lines and none of them says whether `032` took the work up. The answer came from the package (`0` call sites, `0` auto-trigger machinery), from `spec-032` (`0` mentions), and from a third document neither the task nor any slice named — `KANBAN.md:358` records that a prior residual cycle already repaired `spec-010`'s finalization-trigger anchor to say the direction "was not adopted", with a do-not-re-raise note. **Three documents, none of them `spec-030`, were needed to grade one `spec-030` sentence.**
- **One instrument was validated on a known-good file first, and this time the validation was carried through to a diagnosis rather than stopping at "explainable".** My markdown link/anchor checker (throwaway, in the scratchpad **outside** the repo) reports exactly two problems on `START.md`: `undefined refs: ['ref-id']` and `unused defs: ['build']`. The first is that file's own literal `[text][ref-id]` convention example. The second I could have waved through as "documentation artifact" — the shape Slice 3 and Slice 4 accepted — but chasing it found a **real bug in my own instrument**: `START.md` contains the literal string `<!-- LINK DEFINITIONS -->` **twice**, once in the prose that documents the convention (line 65) and once as the actual delimiter, and my `split(…, 1)` cut at the first, dumping 40 lines of live prose into the definitions block where its `][build]` use was never counted. The spec and the companion contain that string exactly **once** each, so the split is correct there and their clean results stand — but the general lesson is the one this cycle keeps paying for: **an explainable hit and a diagnosed hit are not the same evidence.** I also found and fixed a second latent blind spot while validating (fence stripping by a DOTALL `` ```.*?``` `` regex mispairs on an odd fence count; replaced with line-based tracking). Both files carry an even fence count (spec 10, companion 0), so neither result changed — a control that did not need to fire, said out loud.

### The `## Current state` licence and the state-vs-scope test, applied explicitly

Both grading tests the slices established were applied to this pass's own candidates rather than re-derived.

- **`## Current state`: no site in this pass's scope.** `:102`, `:103`, `:104`, `:110`, `:111` are the section's `030`-relevant bullets and all five were graded and re-derived at `eaaf1385` by Slices 1-4. None of my five defects sits in that section, so the licence is not engaged. Stated rather than left silent, because a silent absence reads like an unperformed check.
- **The state-vs-scope test decided three of the five.** `:150` and `:154` assert an artifact's **state** (a capability is planned) → drifted, fixed. `:29` and `:37` likewise, in their status-word and future-tense spellings → fixed. `:129` (`FieldSet` is `0.1.1`) and `:427` (Decision 13's version-file scope) are the same shapes and are **TRUE** — verified against the glossary (`FieldSet` reads `planned for 0.1.1`) and against `030`'s own commits (Slice 5's audit) — so both stay untouched. `## Out of scope`'s other nine bullets and `## Non-goals`' twelve were re-read row by row: every one names an owner or a version rather than a status, and only `:558` asserted something about another card's scope.
- **`:558` is the test applied to a new sub-shape: a ROUTING claim.** "Deferred to `032`" reads as scope — it says what this card does not build — but its second half asserts that a *different card holds the work*, which is a state claim about that card's scope and drifts exactly as any other state claim does when the card closes without taking it up. Naming that sub-shape is the reason this item was worth auditing rather than leaving: Slice 3's stated reason for leaving the `032` parity cell ("changing it would assert an unverified claim") is a good reason to verify, never a good reason to leave, and the same applies here.

### Spec changes made (Worker 1 only)

Line numbers are **post-edit**. Cause for every entry: this integration pass, `docs/builder/build-030-connection_field-0_0_9.md` "Cross-slice integration pass". Every "what changed and why" record went to the rationale companion; the spec carries only the corrected contract, in the present tense, with no chronology and no amendment block.

**I1 — the count-mechanism contract was reconciled in three of its five homes and left unconditional in the other two.** 1 site edited (`:247`). Slice 1's D3 established that `.count()` / `.acount()` is the **ordinary offset path's means**, not the whole contract — a prepared source that already carries its own count (an optimizer-planned window's conditional count annotation, or a keyset page counted through the package's own slicer) is read rather than re-counted — and fixed the Slice-1 checklist sub-bullet (`:63`), Decision 4 clause (c) (`:313`), and DoD item 2 (`:571`). `## User-facing API`'s `### Opt-in totalCount (per type)` paragraph still read "it runs `qs.count()` (sync) / `qs.acount()` (async) on the **unpaginated post-filter** queryset", unconditionally. It now states the cardinality as the contract with the two methods as the offset path's means, matching Decision 4. **This is the highest-value finding of the pass** and the one no slice could have made: Slice 1 owned the Decision and the checklist, Slice 2 read the same section but was hunting a symbol (`apply_connection_plan`, in the fence eleven lines below), and Slice 4 explicitly listed `:247` as untouched — correctly, for the *directive* property it was reconciling. Three passes read the sentence; none was looking at that clause.

**`:259` was deliberately NOT changed**, and the reason is a decision rather than an omission: it is the last line of the `### Composing with get_queryset, filter, and order` fenced sketch, and every step in that block is spelled for one concrete sync-offset walkthrough (`GenreFilter.apply_sync`, `GenreOrder.apply_sync`, `apply_connection_optimization(GenreType, qs, info)`). `qs.count()` is correct for the path the block illustrates; qualifying it would make the illustration describe a dispatch the surrounding nine lines do not. `:247`'s directive-gating half was also left alone — Slice 4 decided that question explicitly and recorded the reason, and a settled point is not re-litigated.

**I2 — a fourth enumeration of the four `_validate_connection` rejections listed only three.** 1 site (`:275`). Slice 1's D5 fixed three sites; `### Error shapes`' `Meta.connection` bullet listed non-Relay-Node, non-dict, and unknown sub-key and stopped, dropping the non-bool `total_count` path that `tests/types/test_base.py::test_meta_connection_non_bool_total_count_raises` has pinned since the slice landed. It now lists all four and **states the number**, so the next sweep has a token to find. Verified against the shipped guard rather than against the other enumerations: `awk` over `types/base.py::_validate_connection` counts exactly **4** `raise ConfigurationError` sites.

**I3 — the companion claimed the spec states two mechanism facts; the spec stated one.** 1 site (`:68`). Slice 2's S1 deleted the never-taken `FieldExtension` fallback from the Slice-2 checklist sub-bullet and recorded in the companion that "two mechanism details went into the spec in its place". Only one did — that calling `filter_input_type` / `order_input_type` to build the annotations IS the ledger registration. The second, that both helpers are imported **at call time** rather than at module scope, exists only in the companion. It is genuinely load-bearing under `worker-1.md`'s implementation-relevant-rationale carve-out, verified in the source: `connection.py::_synthesized_signature` imports both inside the function, `connection.py` has **no** module-level `filters` / `orders` import, and the code's own comment names the consequence — `connection.py` is reached by a bare `import django_strawberry_framework` through `__init__.py`, so a module-level import eagerly pulls in both subpackages and breaks a lazy-subpackage contract pinned by `tests/filters/test_finalizer.py` and `tests/orders/test_inputs.py`. A builder reading only the spec writes the module-level import. The spec now carries it beside the registration fact, which is the repair that makes the companion's sentence true; correcting the companion's count instead would have left the load-bearing fact unstated in the only file a builder reads.

**I4 — the `DONE-032-0.0.9` parity-table row, carried by three slices and now verified.** 1 site (`:150`). `planned (0.0.9 — DONE-032-0.0.9)` → `sibling card (0.0.9 — DONE-032-0.0.9)`, matching its `033` neighbour that Slice 3 fixed one line below. Slice 3 left it because `032`'s shipped surface was in no slice's audit scope; audited here from four independent directions, all agreeing: `django_strawberry_framework/relay.py` defines `DjangoNodeField` (`:423`) and `DjangoNodesField` (`:490`); `django_strawberry_framework/__init__.py` imports both and carries both in `__all__`; `KANBAN.md:3090` carries the card as `### [DONE-032-0.0.9 - Full Relay story …]` in Done; and `docs/GLOSSARY.md`'s `DjangoNodeField` entry reads `**Status:** shipped (0.0.9).`.

**I5 — a SECOND wrong parity-table Status cell, found by the row-by-row check.** 1 site (`:154`). `apply_cascade_permissions`: `planned (0.0.10)` → `shipped (0.0.10)`. Verified three ways: `django_strawberry_framework/permissions.py:557` defines `apply_cascade_permissions`, the package `__init__` exports it and its async twin, and `CHANGELOG.md:80` documents both at length. The glossary entry reads `**Status:** shipped (0.0.10).`. This row is the reason a row-by-row table walk was worth doing rather than a targeted sweep — see the instrument note above. **The two rows that are still genuinely planned were confirmed and left alone**: `FieldSet` (glossary `planned for 0.1.1`) and `AggregateSet` (glossary `planned for 0.1.3`). And the table carries **no row for `DONE-031-0.0.9`**, which the task asked me to check: the upstream `django_graphene_filters` cookbook has no GlobalID counterpart, so there is no pair to make and the absence is correct, not an omission.

**I6 — the `DjangoNodeField` Key-glossary bullet, moved with I4.** 1 site (`:29`). "the **planned** root single-node lookup field … it lands with the Full Relay story" → the shipped fact plus the unchanged scope boundary, now naming `django_strawberry_framework/relay.py` through the existing `[relay-root]` def Slice 4 added. **I4 and I6 moved in one change on purpose**: they are the same claim in two spellings, and fixing one is exactly the partial-claim-fix defect this cycle keeps finding.

**I7 — the `Relation handling` Key-glossary bullet.** 1 site (`:37`). "the **current** relation-list behavior that the sibling Full Relay story **upgrades** to relation-as-Connection **after this card lands**" → the ownership split with no tense. Two things had drifted: the antecedent ("after this card lands") is long satisfied, and `Meta.relation_shapes` reads `**Status:** shipped (0.0.9)` in the glossary while `Relation handling` reads `shipped (0.0.1)+`, so the upgrade is not pending. `Meta.relation_shapes` is written as plain backticked text rather than a glossary link, matching how the spec already names it at `:132` and `:557` — deliberately, so the term count the amendment fixes at 50 is untouched.

**I8 — the finalize-auto-trigger routing.** 1 site (`:558`), plus 1 new link definition. "deferred to `032`" → not built by this card and not built by any card since, with the current package state and the standing constraint on any future helper. Decision 12's own body (`:419`-`:421`) and the `## Non-goals` twin (`:133`) were **not** touched: both say only that *this card* does not auto-trigger, which is true and permanent. Only the routing half drifted. Evidence: **0** `finalize_django_types()` call sites in any field factory, **0** auto-trigger machinery anywhere in `django_strawberry_framework/`, **0** mentions in `spec-032-full_relay-0_0_9.md`, and `spec-010-foundation-0_0_4.md` #"Layer 3: Finalization trigger" recording the direction as **not adopted** with the single-threaded-setup-window constraint intact. That spec-010 sentence was itself repaired by a prior residual cycle and carries a do-not-re-raise note in `KANBAN.md:358`, so citing it rather than re-deriving it is the correct move.

**I9 — the pre-existing unused `[goal]` link definition, removed.** 1 site (`:600`, deleted). Flagged by three slices as a known orphan and by the rationale pass as pre-existing before this cycle. Measured before removing: `][goal]` inline uses = **0**, and the bare token `goal` occurs exactly once in the whole spec, at `:122`, which is the words `## Non-goals`. So `GOAL.md` is genuinely cited from nowhere in this spec and the definition was dead weight. Post-removal the file reports **110 defs / 110 used, zero unused** — the orphan is gone and nothing was orphaned in its place. (The count is unchanged at 110 because I8 added `[spec-010]`.)

**Not changed, deliberately.** `:259` (the illustrative fence — see I1). `:247`'s directive-gating half (Slice 4's decided answer). `:102` / `:103` / `:104` / `:110` / `:111` (`## Current state`, licence case 1, all re-derived at `eaaf1385` by Slices 1-4). `:129` and `:427` (state-shaped sentences that are TRUE — verified). Decision 12's body and its `## Non-goals` twin (pure scope). The implementation-plan estimate table's line deltas and test counts (explicitly labeled estimates; Slices 3 and 4 corrected their *descriptions* and left the numbers, and nothing this pass found touches them). The `## Risks and open questions` surviving upstream-derivation rule (still true; the floor is still open in `pyproject.toml`). Every `## Out of scope` bullet other than `:558`, and every `## Non-goals` bullet — read row by row, all owner-or-version statements rather than status claims.

### Terms-CSV `notes` reconciliation (the plan's `## Mid-cycle scope amendment`)

**Bounds honored, and proved mechanically rather than asserted.** The `notes` column only; no `term` and no `anchor` value changed; no row added or removed; the row count and the one-row-per-anchor shape untouched.

```shell
$ .venv/bin/python   # compare a pristine pre-edit copy kept OUTSIDE the repo against the edited file
row counts: 51 51 EQUAL
(term,anchor) sequences identical: True
anchors unique (one row per anchor): True
rows whose notes text changed: 12
```

**I10 — twelve `notes` cells reconciled** (term named, since the CSV's rows are identified by term):

- `DjangoConnectionField`, `DjangoConnection` — "status flips planned for 0.0.9 -> shipped (0.0.9)" narrated a pending flip that Slice 5 verified is done in both the glossary Index and the entry bodies. Both now read `shipped (0.0.9)`. `DjangoConnection`'s cell also gained the always-concrete resolution Slice 1's D1 put in the spec, since the old cell described the base as what the field is given.
- `DjangoNodeField` — "Planned root single-node lookup … (lands with the Full Relay story, WIP-032)". Same population as spec I4/I6; now the shipped fact plus the module, with the auto-trigger-seam clause kept.
- `Meta.interfaces`, `Meta.connection` — both asserted the gate is `Meta.interfaces relay.Node`, i.e. the single spelling. The shipped gate accepts **either** spelling through `_is_relay_shaped`, which is what the spec says at `:20`, `:275`, and Decision 8, and what `tests/types/test_base.py::test_meta_connection_accepts_direct_relay_node_inheritance` pins. **Neither instrument MF-5 used could see this** — no `WIP` token, no status vocabulary — and no slice listed it; found by reading all 50 cells against the reconciled spec, which is the only instrument for a cell that is simply narrower than the contract.
- `DjangoOptimizerExtension` — "in 0.0.9 rides the existing root-gated flat-selection walker" is the retired empty-plan premise, the exact claim Slice 3 removed from the spec. Now the field-owns-its-cooperation-point contract with the node-level derivation.
- `Strictness mode` — "the seam WIP-033 closes" described the pre-`a3f84ea9` aim; now what the shipped test pins (the connection response shape does not blind the detector), per Slice 3's S7/S15/S17.
- `Connection-aware optimizer planning` — three defects in one cell: "deferred", "recognize edges { node }" (the root unwrap is `030`'s own seam; `033` owns the **nested** recognition), and "stays planned for 0.0.9" (the glossary reads `shipped (0.0.9)`). All three reconciled to Slice 3's S4 wording.
- `Meta.primary` — `WIP-032` → `DONE-032-0.0.9`.
- `SyncMisuseError` — "the **Relay-foundation** get_queryset helpers" is a **fourth site** of the population Slice 2's S7 closed at three spec sites. The spec now has `Relay-foundation` = 0 and the CSV had 1; the cell now names the shared visibility helpers in `utils/querysets.py`. A companion carrying the retired vocabulary of a population declared closed is the partial-claim-fix defect crossing a file boundary.
- `Relation handling` — `WIP-032` plus "after this card lands"; same population as spec I7.
- `apply_cascade_permissions` — "integrates when permissions land" described `0.0.10` as ahead; same population as spec I5.

**I11 — eight rows' `notes` were silently unreadable, and no slice measured it.** This is a new finding and it changes what MF-5 means. Both instruments that read this file — `scripts/check_spec_glossary.py::load_terms` and the fakeshop `import_spec_terms` command — use `csv.DictReader` against a three-column header, so any row whose `notes` field contains an **unquoted comma** has everything after the first comma spilled into the restkey and dropped. Measured: **8 of 50 rows**, including `DjangoNodeField`, where the truncation cut off exactly the `WIP-032` mention MF-5 flagged.

```
line  5 [DjangoNodeField] notes-as-read='Planned root single-node lookup; NOT this card (lands with the Full Relay story'
                          DROPPED=[' WIP-032); shares the finalizer auto-trigger seam Decision 12 declines.']
… and 7 more (DjangoListField, Relay Node integration, Meta.connection, get_queryset visibility hook,
   ConfigurationError, Meta.primary, OptimizerHint)
```

So MF-5's premise — that these cells reach the glossary DB when the maintainer next runs the importer — was true for 42 rows and false for 8. Since the file was rewritten through `csv.writer`, every comma-bearing `notes` value is now properly quoted; the fix is a `notes`-column serialization change only, inside the amendment's bounds, and it is the difference between a drifting column and an unreadable one. Post-fix: **0** rows truncate. Recorded rather than left, because having measured it, leaving 8 rows unreadable would be the silent drop this pass is told not to make.

**`import_spec_terms --check`, run and recorded verbatim** (the amendment requires the run and does not require green; a pre-existing baseline failure on an earlier done card is a known condition of this repo):

```shell
$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
EXIT=0
```

It is **green**. The known baseline failure is not present at this HEAD. **`import_spec_terms` was never run without `--check`**, and `examples/fakeshop/db.sqlite3` is unmodified after the run (`git status --short -- examples/fakeshop/db.sqlite3` → no output). **The consequence for the maintainer, stated:** this edit changes a file, not the database. The reconciled `notes` cells reach the glossary DB only when the maintainer next runs the importer without `--check`.

### Rationale companion appends (Worker 1 only)

The companion is append-only during the build, and every append used its own documented convention — a `**Post-ship:**` bullet under the owning Decision's `### Changes this Decision underwent`, with findings belonging to no single Decision under `## Non-Decision deliberation`. No moved text was rewritten. One **correction** was made to a post-ship bullet rather than an append, and it is called out below.

- **Decision 4** — 1 new bullet, placed directly before the "where observable" bullet so the two count-related entries read together: the count-mechanism fork stated in three of five homes and not the other two, why the spec's designed redundancy is a contract only while all five agree, why no single-region pass can see the mismatch, and why the fenced sketch keeps `qs.count()` deliberately.
- **Decision 6** — 1 new bullet, placed before the fallback bullet whose claim it corrects: only one of the two replacement mechanism facts reached the spec, what the second one is and why it is load-bearing rather than trivia, and the general shape — **a companion bullet that says "the spec now states X" is a claim about another file, and nothing in a per-Decision append discipline checks it.**
- **Decision 8** — 1 new bullet: the fourth stale enumeration, and the instrument lesson that an enumeration is a count claim with no number in it, so a count-word sweep cannot establish its population.
- **Decision 12** — 1 new bullet (the Decision had only a Revision-1 entry): the routing half never taken up, the two-instrument package-side evidence plus `spec-032`'s silence plus `spec-010`'s not-adopted record, and the naming of the **routing claim** as a sub-shape of the state-vs-scope test.
- **`## Non-Decision deliberation`** — 1 new `### Post-ship: the shipped-sibling-surface status claims, and the row-by-row table check that found the second one` subsection. A new subsection rather than an extension of either existing one, because the population (sibling-card status claims) is disjoint from both the symbol-citation population and the empty-plan population, and both of those are closed. It carries the two instruments, the four sites with their per-site grading, the four independent confirmations for `032`, and the finding-shape-is-not-population-shape lesson from the `apply_cascade_permissions` row.
- **One correction, not an append.** The Decision-14 post-ship bullet said "The **two** surviving `[alpha]` mentions are …" and then enumerated three, its own closing clause reading "cannot tell **the three** apart". Measured: `\[alpha\]` = **3** occurrences in the spec (`:83`, `:102`, `:531`), which is what Slice 4's postcondition recorded. The word is now "three". This is an edit to a `**Post-ship:**` bullet rather than to moved text, so the append-only rule (which protects the moved justification / alternatives / revision-history text) is not breached; and a sentence that contradicts itself in its own closing clause is a defect rather than a record.
- **2 new link definitions** in the companion: `[glossary-relation-handling]` under `<!-- docs/ -->` and `[permissions]` under `<!-- django_strawberry_framework/ -->`, both alphabetical within their group, both disk-exists-checked and both resolving (the glossary heading `## Relation handling` exists).

### Postcondition proofs

**1. `check_spec_glossary` holds at exactly the required count** — run after the spec edits, after the companion edits, and again after the CSV edits; identical every time.

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-030-connection_field-0_0_9.md
OK: 50 terms - all have glossary entries and at least one spec link.
EXIT=0
```

**2. Trailing-comma / link-scaffold gate over every file this pass touched.**

```shell
$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-030-connection_field-0_0_9.md \
    docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md \
    docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv
EXIT=0
```

**3. Link / anchor integrity, instrument validated AND diagnosed on a known-good file first** (see the instrument note above for why the diagnosis mattered).

```
== docs/SPECS/spec-030-connection_field-0_0_9.md
 defs=110 used=110
 undefined refs: []      unused defs: []      missing def paths: []
 def anchors not resolving: []   dangling in-page anchors: []   inline cross-file links: []
== docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
 defs=60 used=60
 undefined refs: []      unused defs: []      missing def paths: []
 def anchors not resolving: []   dangling in-page anchors: []   inline cross-file links: []
```

`unused defs: []` on the spec is the postcondition for I9 specifically: every prior slice reported `unused=['goal']`, and this is the first pass where the list is empty. `docs/SPECS/appx/` continues to share its parent's `<!-- docs/SPECS/ -->` group header and the ten headers remain a closed list — no eleventh was earned or attempted.

**4. Inline link TEXT swept, not only def resolution** (carried item 9). Slice 5's method note is correct and the sweep was run in the shape it prescribes: extract every path-shaped **link text**, reconstruct the visible path, and classify it by prefix — a resolution check structurally cannot see stale text. Spec: **40** distinct path-shaped link texts (re-measured after this pass's own edits, which added three — `relay.py`, `permissions.py`, `spec-010-foundation-0_0_4.md`; the pre-edit figure was 37, and asserting that number here would have been the "measure as you write it" hazard this document keeps naming), every one either exact from the repo root or a documented in-package shorthand (`connection.py`, `keyset.py`, `types/base.py`, `utils/querysets.py`, `optimizer/plans.py` — all resolving under `django_strawberry_framework/`, which is the spec's own convention for its home package) or a sibling-spec basename resolving under `docs/SPECS/`. **Zero not-on-disk.** Companion: **21** distinct, exactly one of which the instrument flagged — a link whose text is the bare fragment `-terms.csv` (`:388`, "The `-terms.csv` companion, incidentally, never carried a status word"). Read: it is a deliberate suffix mention in prose whose def resolves to the real CSV, not rot. An instrument hit that is read and explained, and said out loud.

**5. `.py` surface unchanged — the inverse proof, restated at pass end.** The claim is that no executable byte moved, so the proof is a diff empty by construction rather than a green suite. `git status --short -- docs/SPECS/ docs/builder/ | grep -c '\.py$'` = **0**. All 23 dirty `.py` files were dirty at pass start, belong to the concurrent session, and were neither edited nor reverted; none is `connection.py`, `types/base.py`, `types/definition.py`, `optimizer/extension.py`, `optimizer/plans.py`, `utils/querysets.py`, `permissions.py`, `relay.py`, `keyset.py`, or any test file this pass cites.

**6. Focused tests run (no `--cov*` flag in any form).**

```shell
$ uv run pytest tests/test_connection.py tests/types/test_base.py tests/optimizer/test_extension.py --no-cov -q
401 passed in 8.81s
```

Recorded as run-and-passing per `worker-1.md` step 5. This is a sanity confirmation, not evidence for any claim above: nothing executable changed, so a green run here could not have failed differently. The full sweep belongs to the final gate.

**7. Byte counts (measured, `wc -c` / `wc -l`).**

| File | Before this pass | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-030-connection_field-0_0_9.md` | 137,372 B / 722 lines | 138,692 B / 724 lines | **+1,320** B / +2 lines |
| `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md` | 93,103 B / 487 lines | 100,796 B / 502 lines | **+7,693** B / +15 lines |
| `docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv` | 7,554 B / 51 lines | 8,378 B / 51 lines | **+824** B / +0 lines |

The spec grew by five corrected sentences, one added mechanism fact, and one link definition, minus the removed `[goal]` def. Most of the growth is in the companion, which is where a corrected claim's whole explanation belongs. The CSV grew by the reconciled prose plus the quoting characters; its line count is unchanged, which is the amendment's row-count invariant restated as a measurement. The corpus ratchet in `BUILD.md` governs the six workflow documents, none of which this pass touched.

### Carried items 1-9 — every one dispositioned

A silent drop is a finding against this pass, so each item gets **resolved here**, **recorded for the maintainer**, or **explicitly deferred with the reason**. Every count in every item was re-derived rather than inherited.

**1. The authorized terms-CSV `notes` edit — RESOLVED HERE**, plus one finding no slice had measured. 12 rows reconciled; MF-5's 5-row `WIP-03` count and 4-claim inventory both re-derived and both correct as far as they went, but the real population is **12 rows**, because MF-5's two instruments cannot see a cell that is merely *narrower* than the contract (`Meta.interfaces`, `Meta.connection`) or that carries a **retired vocabulary the spec has already dropped** (`SyncMisuseError`'s `Relay-foundation`, a fourth site of a population Slice 2 declared closed). Bounds proved mechanically; `check_spec_glossary` holds at `OK: 50 terms`; `import_spec_terms --check` recorded verbatim above and green; the importer was never run without `--check` and `db.sqlite3` is unmodified. **I11** is the new finding: 8 of 50 `notes` cells were truncated by the only parser that reads them, now 0.

**2. The `DONE-032-0.0.9` parity row — RESOLVED HERE (I4), with two siblings.** Verified against four independent sources before editing, per Slice 3's correct instinct that its own stated reason was a reason to verify rather than to leave. The row-by-row walk of all nine data rows the task asked for found **a second wrong cell** (`apply_cascade_permissions`, I5) that no sweep aimed at the first defect could see, confirmed the two genuinely-planned rows against the glossary, and established that **no `DONE-031-0.0.9` row exists** — correctly, since the upstream cookbook has no GlobalID counterpart.

**3. `:557`/`:558`'s `finalize_django_types()` auto-trigger deferral — RESOLVED HERE (I8).** Audited: `032` did **not** ship it, and no card has. The established grading test was applied and produced a new sub-shape: the sentence asserts both what this card does not build (scope, true, kept) and that `032` holds the work (a state claim about another card's scope, false, fixed). Decision 12's body and the `## Non-goals` twin are pure scope and were correctly left untouched.

**4. The pre-existing unused `[goal]` link def — RESOLVED HERE (I9), removed.** Measured first: zero inline uses, and the only occurrence of the bare token in the whole spec is the words `## Non-goals`. Postcondition: 110 defs / 110 used, `unused defs: []`.

**5. The card-less-provenance pattern at four instances — SWEPT, BOUND, and the result reframes the pattern. Nothing further uncontracted was found, which is a real result.**

*The bound, stated:* `git log --oneline --reverse -S<symbol>` over `django_strawberry_framework/connection.py` and `optimizer/extension.py`, for **ten** symbols — the four `connection.py` guards, the four pipeline / cooperation symbols named in the plan's conditional hot-path clause (`_pipeline_sync`, `_pipeline_async`, `_finalize_queryset`, `apply_connection_optimization`), and the two factory symbols `_connection_type_for` and `_synthesized_signature`. Two files, ten symbols; no wider.

*What it found:* **eleven distinct commits naming no card and no spec** touch those ten symbols — the three the slices already found (`11da7de8`, `a3f84ea9`, `9e864f59`) plus eight the cycle had not seen: `6912ca92` (a DRY pass), `0e864b7e` (a connection-optimizer refactor), `dc00f4a6` (diagnostic-rendering hardening), `ab821ae0` (a single-siting refactor), `e37aef5e` (shared-utility work), `3604ee31` (an optimizer perf round), `b2421085` (optimizer consolidation), and `18567c63`/`faf9fefc`/`75035bdc`/`4b26b94e`/`d418e649` which **do** name a spec and so carry provenance.

*Asking Slice 5's two questions of each hit:* all four `_guard_*` are now contracted (Decisions 3, 7 ×2, and 7 again via Slice 2's S4) and `_require_async_iterable_context` is contracted by Slice 2's S7. Two of the previously-unseen commits were spot-checked because they touch a **guard**, and both are call-site consolidation with no contract change: `6912ca92` collapsed `_guard_first_and_last` from two call sites to one, and `0e864b7e` collapsed `_guard_sidecar_input_against_non_queryset` from two to one. **So the sweep's answer is "nothing further"**: no card-less commit introduced a `030`-seam behavior that is neither contracted nor documented beyond the three already carried.

*The reframing, which is the valuable part.* At four instances the pattern read as an anomaly. Measured over `030`'s own seams it is the **ordinary case** — this repo's normal mode includes refactor, DRY, perf, and hardening passes with no card, and eleven of them touched these ten symbols. So "the commit named no card" is not the risk. The risk is the two questions, and one of them has a sharper form than the cycle had noticed: **Slice 1's load-bearing audit finding — that `_guard_first_and_last` has exactly ONE call site, which is why every slicing path is provably downstream of it — is a property created by `6912ca92`, a card-less DRY commit, four days after the card shipped.** The contract survived; the *invariant an audit rests on* was authored by an uncarded refactor. That is the shape worth carrying: a card-less commit's danger is less that it adds uncontracted surface (measured: it did not) than that it can silently create or destroy the invariant a later audit will lean on.

**6. Slice 2's handoff — sweep `connection.py`'s other guards. DONE, bounded, and it found one population, correctly attributed.** Two instruments over the module: `^def _guard` = **4** (`_guard_first_and_last`, `_guard_total_count_countable`, `_guard_sidecar_input_against_non_queryset`, `_guard_source_not_pre_sliced`), and — disjoint, since it keys on raises rather than names — every `raise GraphQLError | ConfigurationError | SyncMisuseError` site with its enclosing symbol = **9** sites in **7** symbols. The second instrument found three symbols the first cannot: `_keyset_order_state` (3 raises), `_resolve_keyset_connection` (1), and `_require_async_iterable_context` (1).

Attributed carefully, since `connection.py` hosts three later cards' surfaces. All four `_guard_*` and `_require_async_iterable_context` are contracted by `030` Decisions 3, 7, and 10. The **four keyset raise sites are correctly NOT `030`'s** — Decision 9 states that `connection.py` owns the dispatch seam and `keyset.py` owns the codec — and here the finding fires, because **no spec owns them either**: there is no `spec-0NN-keyset` / `-cursor` file, `Meta.cursor_field` is *mentioned* by eight specs and is the *subject* of none, and the feature shipped as `BACKLOG.md` item 39 sub-feature 3 in commit `51421e54`. It is real public surface — `cursor_field` is in `ALLOWED_META_KEYS`, two-stage validated (`types/base.py::_validate_cursor_field` at class creation plus `validate_cursor_field_columns` at finalization), 31 occurrences in `keyset.py`. **Recorded for the maintainer as MF-7**, not fixed: the repair is a spec, and writing one for another card's feature is outside any reading of this cycle's fence. `spec-030` needs no change — Slice 5 already settled that Decision 9's citation of the module rather than a glossary anchor is the correct choice while no anchor exists.

**7. Slice 5's MF-1..MF-6 — CARRIED FORWARD INTACT** into `### Deferred work catalog for the final gate` below, each with its text-edit-vs-DB-regenerate disposition preserved. MF-5's gate question is recorded there as a maintainer proposal, with the fence noted: **proposing a change to `scripts/check_spec_glossary.py` is outside this cycle's fence** (the plan permits spec files and package/test `.py` files; `scripts/**` is on this pass's do-not-touch list), so it is a proposal and nothing more. I11 strengthens it materially — the column is not only ungated but was partially unreadable — and that measurement is folded into the catalog entry.

**8. Slice 4's caution about `test_anonymous_inline_fragment_under_connection_field_resolves` — HONORED.** It is an optimizer selection-walker regression pin whose subject is not a `030` contract, it is correctly absent from `spec-030`'s Test plan, and **this pass did not adopt it**. Verified as a postcondition rather than merely intended: `grep -c 'test_anonymous_inline_fragment' docs/SPECS/spec-030-connection_field-0_0_9.md` = **0**. Carried into the catalog so a later sweep of that live block does not adopt it either.

**9. Slice 5's method note — inline link TEXT, not only def resolution — ACTED ON.** Run in the prescribed shape and recorded as postcondition proof 4 above: 37 path-shaped link texts in the spec and 20 in the companion, reconstructed and classified by prefix, **zero not-on-disk**, and the single flagged hit read and explained. The note's wider point — that the same archival sweep produced every archived spec, so the same latent rot exists in all of them — is beyond this cycle's fence and is carried into the catalog.

### Deferred work catalog for the final gate (`bld-final-030.md`)

Carried forward intact so it survives into `bld-final-030.md`'s `### Deferred work catalog`. Nothing here is fixable inside this cycle's fence.

1. **MF-1 — `docs/GLOSSARY.md`: the three `030` entries never state that `totalCount` selection-gating is directive-resolved.** *(DB-backed regenerate.)* The spec states it at four sites; the glossary has zero directive-vocabulary occurrences in any `030` entry (two instruments, Slice 5's Population C). A consumer reading only the glossary cannot tell whether a `@skip`-ed `totalCount` still costs a query.
2. **MF-2 — `docs/GLOSSARY.md`: `Meta.cursor_field` is shipped public surface with no glossary heading.** *(DB-backed regenerate.)* Every other `Meta` key has one; two entry bodies reference this key as though a reader could look it up. Re-confirmed this pass: a heading sweep over `docs/GLOSSARY.md` returns no `Meta.cursor_field` entry. `spec-030` needs no change.
3. **MF-3 — `CHANGELOG.md`: no entry for the keyset-cursor feature or `Meta.cursor_field`.** *(Text edit.)* `grep -ci keyset` = 0, `grep -c cursor_field` = 0.
4. **MF-4 — `CHANGELOG.md` and `docs/GLOSSARY.md`: the already-sliced-`QuerySet` `GraphQLError` is undocumented.** *(Text edit for `CHANGELOG.md`; DB-backed regenerate for the glossary.)* Consumer-visible error contract on a shipped field, absent from both files under five tested spellings.
5. **MF-5 — the terms CSV's `notes` column asserts statuses no instrument reads, AND 8 of 50 cells were unreadable by the only parser that reads them.** *(Content half RESOLVED this pass — see I10/I11. The gate half is a maintainer proposal.)* The proposal: either the `notes` column is contract text and needs a gate, or it is scratch and should stop asserting statuses. Two measurements now support it — the column drifted to 12 stale cells with no instrument objecting, and `csv.DictReader` silently truncated 8 of them at the first unquoted comma, so part of the column never reached the DB at all. **Fence note: proposing a change to `scripts/check_spec_glossary.py` is outside this cycle's fence**; `scripts/**` is on this pass's do-not-touch list and no edit to it was made or attempted. The 12 cells and the quoting are fixed on disk; nothing reaches the glossary DB until the maintainer runs the importer without `--check`.
6. **MF-6 — the kanban DB: the `DONE-030-0.0.9` card body carries two stale `docs/spec-030` paths.** *(DB-backed regenerate — two ORM row edits plus `build_kanban_md.py` / `build_kanban_html.py`; `KANBAN.html`'s Vue shell is hand-edited and only its data block regenerates.)* `KANBAN.md:3479` (a DoD checkbox) and `:3514` (the description bullet); both render into `KANBAN.html:97`'s JSON payload. The card's `Spec:` field and the board index are correct, so this is half-archived residue inside one card.
7. **MF-7 (NEW this pass) — the keyset-cursor feature has no owning spec.** *(New spec, or a `BACKLOG.md`/card decision.)* `Meta.cursor_field` is real public surface — in `ALLOWED_META_KEYS`, two-stage validated at class creation and finalization, 31 occurrences in `keyset.py`, and four `GraphQLError` raise sites inside `connection.py` (`_keyset_order_state` ×3, `_resolve_keyset_connection`) — and **no numbered spec owns it**: eight specs mention `Meta.cursor_field`, none takes it as its subject, and it shipped as `BACKLOG.md` item 39 sub-feature 3 in `51421e54`. Combined with MF-2 and MF-3 this is one feature missing all three of its documentation homes — spec, glossary entry, changelog entry — which is why it is worth one maintainer decision rather than three.
8. **`test_anonymous_inline_fragment_under_connection_field_resolves`** (`examples/fakeshop/test_query/test_library_api.py`, commit `9e864f59`) is an optimizer selection-walker regression pin living in `030`'s live block. It is correctly absent from `spec-030` and must stay absent; named so a later sweep of that block does not adopt it into `030`. Verified absent as a postcondition this pass.
9. **The archived-spec inline-link-text rot is not `spec-030`-specific.** The archival sweep that re-relativized definitions while leaving visible paths stale produced **every** archived spec, and a link-resolution check reports all of them clean by construction. `spec-030`'s seven sites are closed (Slice 5, re-derived this pass at 0); the same latent population exists in the rest of `docs/SPECS/`. Outside this cycle's fence; worth one sweep in its own pass, with the instrument Slice 5 prescribes (reconstruct the visible path and classify by prefix) rather than a resolution check.
10. **The unrecorded `0.0.9` review round of this spec.** The revision history lists three revisions and one finding round, yet four finding labels (`P1-B`, `P3a`, `P3b`, and an `Open Question`) are cited from live code and tests, and two shipped `030` contracts arrived through rounds the history does not record (`9e864f59` "Finish REVIEW of 0.0.9", and `e2b5b10b` "spec-030 review round"). All four labels and both contracts are now homed in the companion and stated in the spec, so this is a **provenance** gap, not a code or contract gap. Record it; do not invent its contents.

### Summary

The `030` residual cycle's five slices each closed their own region cleanly, and the integration pass's job was the one check none of them could run: whether the spec's **designed** redundancy still agrees with itself across regions. It did not, in three places, and all three are now fixed. The count-mechanism contract had been reconciled in three of its five homes and left unconditional in `## User-facing API`; a fourth enumeration of the four `_validate_connection` rejections listed three, invisible to the number-word sweep that closed the other three because an enumeration is a count claim with no number in it; and the companion asserted the spec carried two mechanism facts when it carried one, leaving a load-bearing call-time-import rule — the thing that keeps a bare `import django_strawberry_framework` from eagerly pulling in `filters` / `orders` — stated only in the file a builder never reads.

Beyond the DRY question, all nine carried items are dispositioned with none dropped. The two verify-or-say-why items were **verified and fixed**: `032` shipped `DjangoNodeField` / `DjangoNodesField` (four independent confirmations) so the parity row's `planned` was wrong, and the row-by-row table walk found a **second** wrong cell whose shape no sweep aimed at the first could match; and the `finalize_django_types()` auto-trigger was **not** taken up by `032` or any card, with the direction already recorded as not adopted, so `## Out of scope` was routing an obligation nobody holds. The `[goal]` orphan is removed after measuring that it had zero inline uses. The card-less-provenance sweep was bounded to ten symbols across two files, found eleven card-less commits, asked both of Slice 5's questions of each, and returned **nothing further uncontracted** — while reframing the pattern: card-less commits are this repo's ordinary mode, and their real hazard is that one of them authored the single-call-site invariant Slice 1's whole guard-reachability audit rests on. The guard sweep found the one genuine no-owning-contract population — four keyset raise sites in a feature no numbered spec owns — and correctly attributed it away from `030`.

**CODE GAP list: empty.** Nine reconciliation items landed in the spec, twelve `notes` cells plus an 8-row unreadability fix landed in the CSV, and five appends plus one self-contradiction correction landed in the companion. `check_spec_glossary` holds at `OK: 50 terms`; `import_spec_terms --check` is green and recorded verbatim; the CSV's row count, `(term, anchor)` sequence, and one-row-per-anchor shape are proved unchanged against a pristine copy kept outside the repo; both link scaffolds validate against an instrument that was validated *and diagnosed* on a known-good file first; inline link text was swept as well as def resolution; the `.py` surface is byte-unchanged by inverse proof; and the focused 401-row scope passes. Hot-path: **none**. Floor verification: **none**. Both stated explicitly.

**Status: `final-accepted`.** No defect needs a `.py` change, so no Worker 2 / Worker 3 dispatch is owed. The prose consolidation `BUILD.md` would route to Worker 2 was performed here, because in a prose-only cycle the duplicated text is spec text only Worker 1 may touch. The final test-run gate may be dispatched.

### Spec changes made (Worker 1 only) — deferral reasons for unticked boxes

Not applicable in the usual form: an integration pass has no `### Spec slice checklist (verbatim)`, because it implements no spec slice. Its equivalent obligation is the six mandatory pre-writing steps and the nine carried items, and every one of the fifteen is discharged above with its outcome recorded — six steps (two N/A with the reason and with the would-have-covered scope named, four performed), and nine carried items (six resolved here, two recorded for the maintainer, one honored-and-verified). Nothing is deferred without a stated reason and nothing is silently dropped.

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
