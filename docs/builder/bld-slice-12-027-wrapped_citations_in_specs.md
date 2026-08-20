# Build: Catalog cohort G — wrapped `#"substring"` citations in SPEC files (027)

Spec reference: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] owns the catalog this cohort discharges (item 1 Form A, the markdown half its package-only census could not see), but no repaired citation points at spec-027. The three corrected surfaces belong to other cards: [`spec-033-connection_optimizer-0_0_9.md`][spec-033] `## Revision history` Revision 3 finding (4) (the false completion claim), and [`spec-015-relay_interfaces-0_0_5-rationale.md`][spec-015-rationale], its addendum section on the four retired anchors and the seven citations that quote them (the prescribed method and the uniqueness claim). The eighteen citation repairs span nine files across seven cards.
Status: final-accepted

## Plan (Worker 1)

### Planning lives in the build plan; this cohort's fence came from the dispatch

The contract is [`build-027-filters-0_0_8.md`][plan] `### Three further in-fence classes surfaced by cohort E`. Its three items are this cohort's three tasks. The determination method is cohort A's three-outcome scheme (resolve / zero-hit / non-unique) extended by cohort E's fourth outcome (mis-paired: a substring that resolves once but sits inside a different symbol than the one cited).

**Ownership partition (declared, disjoint):** `docs/SPECS/NEXT.md`, `spec-033`, `spec-037`, `spec-039`, `spec-040`, `spec-041`, `spec-045`, `spec-046`; `docs/SPECS/appx/` `spec-001-rationale`, `spec-009-rationale`, `spec-015-rationale`; plus this artifact. Nine of the eleven were edited; `NEXT.md` needed no edit (its census entry is a false positive, below) and `spec-033` carries only the Task 2 correction.

Cohort F is writing `.py` files concurrently and a separate session holds `spec-028` and its rationale; a further session's `spec-055` landing sat in the tree throughout. No `.py` file, no `spec-028` surface, no `spec-055` surface, and no `spec-027` surface was written or reverted.

### Dispatched sites checklist

Authored by Worker 1 (this cohort has no separate planning spawn). Each tick is re-derivable from `### Per-site determinations`, `### Task 2`, or `### Task 3`.

- [x] Re-derive the census over the whole tracked markdown surface and report the real number rather than accepting the dispatch's 19
- [x] Per site: read the citation across its lines, verify the substring against the target at `HEAD`, classify resolve / zero-hit / non-unique / mis-paired
- [x] Confirm every hit count of 1 also falls inside the symbol the citation names (cohort E's trap)
- [x] Reflow every in-fence site onto one line; introduce no new wrapped citation
- [x] Task 2: verify spec-033's Revision 3 finding (4) against `HEAD` and correct the claim to a present-tense contract
- [x] Task 3: replace spec-015's line-scoped prescribed method with one that sees a wrapped citation
- [x] Task 3: verify and correct the companion's "resolves inside this companion" claim
- [x] Postcondition measured, not assumed: the census returns 0 in this cohort's files, with a control proving the instrument still finds the originals

---

## Build report (Worker 1, acting as the cohort's only pass)

### Files touched

- `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` — four citations reflowed, text unchanged (all four zero-hit; see below).
- `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` — one wrapped citation retargeted and reflowed, plus its unwrapped sibling at the same substring retargeted for consistency.
- `docs/SPECS/spec-040-auth_mutations-0_0_13.md` — six citations: two reflow-only, one retargeted, three reflowed with text unchanged.
- `docs/SPECS/spec-041-channels_router-0_0_14.md` — one citation reflowed, resolves.
- `docs/SPECS/spec-045-visibility_boundary-0_0_14.md` — one citation reflowed, resolves.
- `docs/SPECS/spec-046-transport_security-0_0_14.md` — one citation retargeted and reflowed.
- `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` — one citation reflowed, resolves.
- `docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md` — one citation retargeted and reflowed.
- `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md` — one citation reflowed; the prescribed sweep method replaced; the retired-anchor table row corrected; one link definition added.
- `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` — Revision 3 finding (4) restated as a contract.

`docs/SPECS/NEXT.md` was not edited: see the census.

### Tests added or updated

None. The diff adds no executable statement and no contract to any package surface. Nothing in it is testable by the suite.

### The census, and its real number

The instrument is cohort E's, re-implemented for markdown: a per-line scan of every tracked `.md` file, flagging each occurrence of `#` immediately followed by a double quote that has no further double quote later on the same line. Classification order matters and is cohort E's corrected order — **test closure first**, because a citation opened after `(` is still a citation; only then test the preceding character, where a non-whitespace predecessor means a `"#"` / `"##"` string literal rather than a rule-27 anchor. Script under this session's private `cohortG-027/` scratchpad subdirectory, outside the repo.

Measured over both the working tree and a `git archive HEAD` snapshot, which agree:

| Scope | Files | Wrapped |
|---|---|---|
| Every tracked `.md` file, at `HEAD` | 394 | **26** |
| `docs/SPECS/` | — | 14 |
| `docs/SPECS/appx/` | — | 5 |
| `docs/builder/` (per-cycle artifacts, out of fence) | — | 7 |

So the two spec directories carry **19** — the dispatch's number — but **not the dispatch's 19 sites**. Two members differ, and both differences are measurements rather than opinions:

- **`docs/SPECS/NEXT.md:143` is not a citation and not wrapped.** The line is `` rg -n "^##|^###" <path> ``. The `#` + quote sequence is the tail of the grep pattern `^###"`, its predecessor character is `#`, and the instrument classifies it as a string-literal false positive on rule 2. The one real citation in `NEXT.md` is on line 151 and closes on its own line. `NEXT.md` therefore needed no edit.
- **`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:1252` is a real wrapped citation the dispatch's list omits.** `` #"plan immutability, the `` opens on 1252 and closes on 1253 (`projection gate"`). The file is not in this cohort's writable set, so it is reported, not repaired.

The two cancel, which is why the count is right and the membership is not. **In-fence and repairable: 18** — the 19 minus `spec-004-rationale`, with `spec-015-rationale:883` inside the 18 but discharged as Task 3 (it is a `git grep` pattern for this very defect class quoted in prose, the same false-positive shape cohort E named, and rewriting it is the task rather than reflowing it).

### Per-site determinations

Every substring was flattened across its lines and measured against the named target **before** editing, with `grep -oF <substring> <target> | wc -l` — occurrences, not matching lines. Nine of the eighteen resolve; nine do not.

| # | Site | Cited at `HEAD` | Hits | Determination | After |
|---|---|---|---|---|---|
| 1 | `spec-037:15` | `mutations/inputs.py` + `#"Upload staged seam (TODO-ALPHA-037-0.0.11)"` | **0** | **zero-hit — the card's own shipping removed the pinned line** | reflowed, text unchanged; reported |
| 2 | `spec-037:486` | same | **0** | same | same |
| 3 | `spec-037:1122` | same | **0** | same | same |
| 4 | `spec-037:1655` | `scalars.py` + `#"Future scalars (e.g. ``Upload`` per TODO-ALPHA-035-0.0.11) land here."` | **0** | same class — this card's Slice 2 rewrote the docstring | reflowed, text unchanged; reported |
| 5 | `spec-039:2347` | `forms/resolvers.py` `_run_modelform_pipeline_sync` + `#"Authorize BEFORE decoding relations"` | **0** | **zero-hit AND mis-paired** — the named symbol does not exist and the phrase is reworded | `` #"Authorize runs BEFORE the relation decode" ``, **1** hit, module-level form |
| 6 | `spec-040:734` | `KANBAN.md` + `#"Decision: Alpha cards must claim upstream parity"` | **1** | **resolves** | reflowed only |
| 7 | `spec-040:782` | `registry.py` + `#"The declaration-registry resets and the per-pass shape-cache resets are NOT pre-bind input clears"` | **0** | **zero-hit — the mechanism the comment described was retired** | reflowed, text unchanged; reported |
| 8 | `spec-040:884` | as #6 | **1** | **resolves** | reflowed only |
| 9 | `spec-040:1795` | `mutations/sets.py::_resolve_primary_type` + `#"which has no registered DjangoType"` | **0** | **zero-hit — the target's own text wraps mid-phrase** | `` #"the mutation has no type to return" ``, **1** hit, inside the named symbol |
| 10 | `spec-040:1898` | as #7 | **0** | same as #7 | reflowed, text unchanged; reported |
| 11 | `spec-040:1951` | `registry.py::TypeRegistry.clear` + `#"The DECLARATION-registry resets"` | **0** | same as #7 | reflowed, text unchanged; reported |
| 12 | `spec-041:673` | as #6 | **1** | **resolves** | reflowed only |
| 13 | `spec-045:294` | `utils/querysets.py::apply_type_visibility_sync` + `#"No identity fast path"` | **2** file-wide, **1** in the named symbol | **resolves, symbol-scoped** | reflowed only |
| 14 | `spec-046:409` | `docs/README.md` + `#"the Channels GraphQL consumers do not enforce CSRF"` | **0** | **zero-hit — this card rewrote the sentence it cites** | `` #"runs no `CsrfViewMiddleware`, so on that protocol" ``, **1** hit |
| 15 | `appx/spec-001-rationale:669` | `optimizer/plans.py` + `#"including the FK columns required to materialize"` | **1** | **resolves**, module docstring, correct module-level form | reflowed only |
| 16 | `appx/spec-009-rationale:280` | `spec-054-fieldset-0_1_1.md` + `` #"a custom `DjangoModelField` field class is unnecessary machinery" `` | **0** | **zero-hit — the target's own text wraps mid-phrase** | `` #"field class is unnecessary machinery" ``, **1** hit |
| 17 | `appx/spec-015-rationale:680` | `worker-0.md` + `#"Verify card/glossary references against the DB"` | **1** | **resolves** | reflowed only |
| 18 | `appx/spec-015-rationale:883` | not a citation — a `git grep` pattern quoted in prose | n/a | **false positive of the instrument's known class** | rewritten as Task 3 |

**Extension, measured and deliberate: one unwrapped sibling.** `spec-039:357` cited the same zero-hit `#"Authorize BEFORE decoding relations"` substring on a single line, so the wrap census could not see it. Repairing 2347 alone would have left one spec spelling the same citation two ways, one resolving and one not — the half-reconciled defect. It carries the identical retarget. The population inherits its instrument's blind spot: `spec-037:347` carries a fourth unwrapped occurrence of the seam substring, and because sites 1-4 were left verbatim it is already consistent with them, so it was not touched.

#### The five zero-hit sites that were left with their text, and why

Sites 1-4, 7, 10 and 11 are zero-hit for one reason: a **later change removed the line the citation pins**, and no live substring carries the sentence's claim. The dispatch's constraint governs here — a citation pointing at a contract the tree no longer has is a finding, not a spec rewrite. Each was reflowed so the anchor is visible to any future instrument, and the sentence around it was not touched.

- **Sites 1-4 (`spec-037`).** The card is `DONE-037-0.0.11`. Its own Decision 6 mandates removing the `spec-036` staged seam, and `mutations/inputs.py` now types file columns through `model_column_write_annotation` (`if kind == FILE: return Upload`), with `model_column_input_annotation` and `build_mutation_input` both recording that `spec-037` lifted the `spec-036` carve-out. The seam comment the four sites pin is gone by design, as is the `scalars.py` "Future scalars" line site 4 pins. Sites 1, 2 and 4 sit under the spec's opening prose, `## Current state`, and `## Risks and open questions` — authoring-time snapshots whose tense is the spec's own design, not a defect this cohort may rewrite.
- **Sites 7, 10, 11 (`spec-040`).** Commit `48f9f65d` ("Refactor subsystem clear registration and handling") replaced the `(module_path, attr)` string-tuple subsystem-clear ledger with `register_subsystem_clear(clear, *, owner, before_bind=False)`, and both comments spec-040 quotes went with it. The retirement is not only textual — see `### Notes for Worker 1 / Worker 0`, where the Decision 9 mechanism is now falsified.

### Task 2 — spec-033's Revision 3 finding (4)

**The measurement, re-derived independently of cohort E.** Finding (4) reads, at `HEAD`, "production/test comments no longer cite the per-cycle review artifact". Grepping `git show HEAD:tests/test_relay_connection.py` for review-round and build-step vocabulary returns **six** live sites: lines 385 (`Revision 3 P3`), 867 (`Revision 2 P1`), 940 (`Revision 6 P3:`), 1620 (`the deterministic regression, Revision 3`), 2569 (`Implementation step 5`), 2588 (`Implementation step 2`). That file is spec-033's own contracted live-connection test surface, so the claim asserted a completed sweep its own surface falsified six times over. `Implementation step N` is the sharper half: it resolves in no spec at all, only in the `docs/builder/ARTIFACT.md` / `worker-1.md` `### Implementation steps` template section, a surface no spec has ever had.

Cohort E's uncommitted working-tree edits bring the same grep to **0**, which is why the correction states a contract rather than a completion: a spec must be true of its surface at any commit, and "no longer cite" was a claim about one pass.

**The correction** (spec-033 line 15, `## Revision history` Revision 3, finding (4)). Present tense, normative, no narration of the correction and no reference to the cycle that made it:

> (4) **doc-reference hygiene** — a production or test comment on this card's surface cites a spec, a card, or a symbol path, never a per-cycle review artifact, a review-round or finding id (`Revision N`, `P<n>`), or a build-plan step (`AGENTS.md`). Findings 1–3 are behavior corrections; 4 is a comment-hygiene contract.

Nothing else in spec-033 restates the claim: `grep -n "no longer cite\|per-cycle review artifact\|doc-reference hygiene"` returns line 15 alone, so the reconciliation is complete rather than partial.

### Task 3 — the spec-015 companion's two defects

**3a. The prescribed method could not see the defect it exists to catch.** The companion prescribed a single-quoted `git grep` pattern for the anchor shape as the standing sweep. `git grep` matches within a line, so a citation whose opening quote sits on one line and whose closing quote sits on the next is invisible to it — and that is the population this whole cohort repairs. The prescription now names flattening as the load-bearing step and carries a runnable shape (flatten each tracked file's newlines to single spaces, then match the anchor pattern), plus the companion wrap detector stated as a rule: an occurrence of `#` immediately followed by a double quote with no further double quote later on the same line. It also records why no gate covers this — `scripts/check_citations.py` matches `path::Symbol` within a single line and holds `docs/` out of scope by its own design statement — via a new `[check-citations]` reference-style definition under the file's `<!-- scripts/ -->` group.

**3b. The "resolves inside this companion" claim failed rule 27's uniqueness, and its citing-site column was stale.** Measured before editing: `` surface any `TypeError` as a `ConfigurationError` `` occurred **twice** in the companion — once in the retired-anchor table's first cell (line 878) and once in the verbatim risk bullet quoted below it (line 891). Two occurrences is not "the citation resolves inside this companion".

The table cell is the only removable duplicate: the verbatim bullet is the resolution site the row promises, and a catalogue that reproduces an anchor verbatim becomes a second occurrence of it by construction. The cell now carries the anchor with an elided middle, the disposition states the contract (the verbatim bullet is the anchor's one occurrence, so the citation resolves there, and this row elides the middle so the catalogue is not a second one), and the count is now **1**.

The same row's "Cited from" column named two sites. Only one is live: `tests/types/test_relay_interfaces.py::test_apply_interfaces_wraps_typeerror_as_configuration_error` still cites the anchor, while `types/relay.py::apply_interfaces` cites Decision 1 `#"never as a raw layout error"` at `HEAD`. The column now names the live citer, and records where `apply_interfaces` points instead.

### Census postcondition, with a control

| Run | Scope | Wrapped |
|---|---|---|
| Precondition | every tracked `.md`, at `HEAD` and in the working tree (agreeing) | **26** |
| Postcondition | every tracked `.md`, working tree | **8** |
| Postcondition, this cohort's nine edited files | — | **0** |
| Control | the same instrument over the `git archive HEAD` snapshot, re-run after the edits | **26** — the instrument still finds the originals, so the 0 is the tree changing, not the instrument breaking |

The surviving 8 are the 7 `docs/builder/` per-cycle artifacts the dispatch places out of fence, plus `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:1252`, outside this cohort's writable set.

**No reflow created a new wrapped citation.** The postcondition is the proof, and it is a repo-wide re-run rather than a spot check of the edited lines. Two paragraphs needed re-joining after a reflow left a two-word orphan line (spec-040 lines 783 and 1899); no other prose was rewrapped, so no unrelated citation in an edited paragraph was disturbed.

### Validation run

| Command | Result |
|---|---|
| `uv run python scripts/check_citations.py` | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md).` |
| the same gate over a `git archive HEAD` snapshot (baseline) | `OK: 743 citations resolve (666 in 422 .py files, 77 in KANBAN.md).` |
| `uv run python scripts/check_spec_glossary.py --spec <each of the 7 specs edited>` | all `OK`; 38 / 20 / 38 / 30 / 30 / 9 / 37 terms for `033` / `037` / `039` / `040` / `041` / `045` / `046` |
| `uv run python scripts/check_trailing_commas.py --check <all 10 files>` | exit 0, no output |
| markdown wrapped-citation census | 26 → 8; 0 in this cohort's files (table above) |

**The +39 citation delta is not this cohort's.** The gate's own module docstring states `docs/` is deliberately out of scope, and every file this cohort touched is under `docs/`, so its edits cannot move the count in either direction. The whole delta is `.py` (666 → 705) with `KANBAN.md` unchanged at 77, which is cohort F's concurrently-written surface. Both numbers are reported so neither has to be trusted alone.

### `git status --porcelain` classification

Before and after, the tree carried three other workstreams. After this cohort's edits, the ten `M` paths under `docs/SPECS/` and `docs/SPECS/appx/` that belong to this cohort are the nine edited files plus `spec-033`; every other path classifies as follows:

- **Cohort F (`.py`, concurrent):** 32 modified files under `django_strawberry_framework/`, 2 under `examples/fakeshop/apps/`, and 18 under `tests/` — including `tests/test_relay_connection.py`, which carries cohort E's item-8 removals verified above.
- **The concurrent `spec-028` session:** `docs/SPECS/spec-028-orders-0_0_8.md` (M), `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md` (??), `docs/builder/bld-slice-{1,2}-028-*.md` (??), `docs/builder/build-028-orders-0_0_8.md` (??). Never read for edit, never reverted (`AGENTS.md` rule 34).
- **Cohort D, landed:** `docs/SPECS/spec-055-search_fields-0_1_2.md` (M). Untouched; measured as carrying no wrapped citation, so the dirty state does not perturb the census.
- **Worker 0 and earlier cohorts:** `docs/builder/build-027-filters-0_0_8.md` (M) and `docs/builder/bld-slice-{4,5,6,7,8,9,10}-027-*.md` (??).
- **`docs/SPECS/NEXT.md`:** clean. In the writable set, needed no edit.

### Implementation notes

- **Reflow direction was chosen per site to keep the paragraph's shape.** Where the citation's own line was short, the continuation moved up; where the whole `#"..."` was long, the following words moved down. Markdown carries no line-length gate (`scripts/check_trailing_commas.py` reads `line_length()` only to decide whether a *construct* fits inline), so width was an aesthetic constraint, not a rule, and it was never allowed to argue for splitting a citation across lines.
- **Retargeted substrings reproduce the target's own backtick spelling**, which is cohort A's lesson and the reason site 14's anchor carries single backticks around `` `CsrfViewMiddleware` `` inside a paragraph that otherwise uses none. Matching the paragraph would break the anchor again.
- **`spec-045`'s sync/async pair was graded on symbol-scoped uniqueness, not file-wide.** `No identity fast path` occurs twice in `utils/querysets.py`, once in `apply_type_visibility_sync` (line 3002) and once in `apply_type_visibility_async` (line 3242). Each `path::Symbol #"substring"` citation names a line *inside* its symbol, so each resolves uniquely within the claim it makes. A file-wide count of 2 read as "non-unique" would have destroyed a correct, deliberate pair.
- **Every hit count of 1 was checked for enclosure, not just for count** (cohort E's trap). Sites 9, 13 and 15 are the ones where it mattered: site 9's retarget lands at `mutations/sets.py:1291`, inside `_resolve_primary_type` (1263-1292); site 15's single hit is at `optimizer/plans.py:12`, inside the module docstring, which is why the module-level `path #"substring"` form is correct there and a `::Symbol` would have been wrong. Site 5's retarget is the mirror image: the phrase moved *into* the module docstring, so its symbol half was dropped rather than corrected.

### Notes for Worker 1 / Worker 0 — findings left in place

Each is measured, each is outside this cohort's fence, and none was repaired.

1. **`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:1252` carries a real wrapped citation** — the anchor `plan immutability, the projection gate` opens on 1252 and closes on 1253. Not in this cohort's writable set. It is the last wrapped citation in the two spec directories.
2. **`spec-040` Decision 9's mechanism is falsified at `HEAD`, not merely its citations.** The spec states the auth declaration ledger is "a hand-written `_clear_if_importable` row … **not** `register_subsystem_clear`", and that declaration registries "are hand-rowed in `TypeRegistry.clear()` only (`clear_mutation_registry` / `clear_form_mutation_registry`)". At `HEAD`, `auth/mutations.py:167` is `register_subsystem_clear(clear_auth_mutation_registry, owner="auth.declarations")` and `forms/sets.py:130` is `register_subsystem_clear(clear_form_mutation_registry, owner="forms.declarations")`. Commit `48f9f65d` moved the distinction from *which list a row is in* to the `before_bind` flag, so the **contract** (auth declarations survive the pre-bind reset) still holds while the **mechanism** the Decision pins does not. Repairing that is a spec reconciliation for card `040`, not a citation repair.
3. **`spec-033`'s opener and `Status:` line are stale.** Line 3 reads "Planned for `0.0.9` (card `WIP-ALPHA-033-0.0.9`). **This spec is an open build plan, not a shipped record.** The card is the only card in the `## In progress` column", and line 5 reads "Status: in progress". `KANBAN.md` carries `DONE-033-0.0.9`, shipped, "closing out the cohort". This is the same defect class as Task 2 on the same spec, and larger; it was left because the dispatch fences this cohort to references, one false completion claim, and one prescribed method.
4. **`spec-037`'s opener reads "Planned for `0.0.11`" on a `DONE-037-0.0.11` card.** Openers are not house style across the archive (`040` says "Shipped in", `045` "Built for", `046` "Targeted at"), so this is staleness rather than convention.
5. **`spec-039:2347`'s quoted block is a paraphrase inside quotation marks.** Its tail, *"Matches the `036` model path's locate → authorize → decode order"*, does not appear in `forms/resolvers.py`; the module docstring says "(matching the ``036`` model path)" and "exactly as the model path locates first". The citation is now correct; the quotation around it is approximate. Quotation accuracy is outside a reference repair.
6. **`spec-046:409`'s sentence survives its retarget, but narrowly.** The pre-`046` README conceded the HTTP gap; at `HEAD` only the WebSocket half is conceded, which is the "half of this" the sentence claims — so the retarget is true. A card-`046` reconciliation may still want to read the paragraph.

### Notes for Worker 3

No Worker 2 / Worker 3 cycle: the diff touches no `.py` file, adds no executable statement, and changes no contract that a test can pin. If one runs anyway, the two claims worth re-deriving mechanically are the census postcondition (with its control run) and the six spec-033 sites at `HEAD`, both of which are single commands.

---

## Final verification (Worker 1)

Deferred to Worker 1's final pass per the dispatch: this artifact stays `Status: built`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

[spec-015-rationale]: ../SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md
[spec-027]: ../SPECS/spec-027-filters-0_0_8.md
[spec-033]: ../SPECS/spec-033-connection_optimizer-0_0_9.md

<!-- docs/builder/ -->

[plan]: build-027-filters-0_0_8.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
