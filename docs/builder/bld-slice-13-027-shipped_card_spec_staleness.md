# Build: Catalog cohort H — a falsified Decision mechanism, two shipped cards described as unshipped, and the last wrapped citation (027)

Spec reference: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] owns the catalog this cohort discharges, but no corrected surface points at spec-027. The four dispatched defects belong to other cards: [`spec-040-auth_mutations-0_0_13.md`][spec-040] `### Decision 9` (the falsified subsystem-clear mechanism, and its blast radius across the spec), [`spec-033-connection_optimizer-0_0_9.md`][spec-033] and [`spec-037-upload_file_image_mapping-0_0_11.md`][spec-037] (openers and `Status:` lines describing shipped cards as unshipped), and [`spec-004-optimizer_beyond-0_0_3-rationale.md`][spec-004-rationale] (the last wrapped citation in the two spec directories). The dispatch is [`build-027-filters-0_0_8.md`][plan] `### Four further in-fence spec defects, verified by Worker 0, not yet dispatched`.
Status: final-accepted

## Plan (Worker 1)

### Planning lives in the build plan; this cohort's fence came from the dispatch

The dispatch's four items are this cohort's four tasks. Three of them came out of cohort G's `### Notes for Worker 1 / Worker 0 — findings left in place` ([`bld-slice-12-027-wrapped_citations_in_specs.md`][slice-12] items 1, 3, 4); the fourth (item 2) is the Decision 9 mechanism.

**Ownership partition (declared, disjoint):** `spec-033`, `spec-037`, `spec-040`, `appx/spec-004-optimizer_beyond-0_0_3-rationale.md`, plus this artifact. All four were edited.

Cohort F is writing `.py` files concurrently; a separate session holds `spec-028` and its rationale; cohort D's `spec-055` landing sits in the tree. No `.py` file, no `spec-028` surface, no `spec-055` surface and no `spec-027` surface was read for edit, written, or reverted (`AGENTS.md` rule 34). Three of this cohort's four files were already `M` at task start **from cohort G**, which is a completed hand-off rather than a live party: `bld-slice-12`'s `### Files touched` names `spec-033`, `spec-037` and `spec-040` explicitly, and the hunks are separable (below).

### Dispatched findings checklist

Authored by Worker 1 (this cohort has no separate planning spawn). Each tick is re-derivable from the sections below.

- [x] Task 1: re-derive the real subsystem-clear contract from source — `register_subsystem_clear`, `iter_subsystem_clears`, `TypeRegistry.clear`, the finalizer's pre-bind reset, and **every** call site — before writing a word
- [x] Task 1: determine whether the distinction Decision 9 draws survives under a different mechanism or has collapsed
- [x] Task 1: sweep the whole spec for every sentence depending on the false mechanism, and fix the blast radius rather than the one line
- [x] Task 1: check whether a `spec-040` rationale companion exists; do not create one
- [x] Task 2: verify `DONE-033-0.0.9` against `KANBAN.md` rather than assuming the number is stable
- [x] Task 2: derive the archive convention by measurement, match the dominant one, tick no box
- [x] Task 3: confirm `spec-037`'s real card state, and measure whether the archive corrects an opener or removes it
- [x] Task 4: classify the wrapped citation by measurement (resolve / zero-hit / non-unique), checking symbol enclosure and not only the hit count
- [x] Task 4: census the whole file with an instrument that scans **every** `#"` per line, not the first
- [x] Postcondition measured, not assumed: 0 wrapped citations in the two spec directories, with a control proving the instrument still finds the originals

---

## Build report (Worker 1, acting as the cohort's only pass)

### Files touched

- `docs/SPECS/spec-040-auth_mutations-0_0_13.md` — sixteen text corrections across the blast radius of the falsified mechanism, plus one link definition added.
- `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` — opener and `Status:` line realigned to the shipped record; one stale card id in Decision 11's filename derivation corrected.
- `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` — opener and `Status:` line realigned to the shipped record.
- `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` — one wrapped citation reflowed, text unchanged (zero-hit; see the determination).

### Tests added or updated

None. The diff adds no executable statement and changes no contract a test can pin.

---

## Task 1 — `spec-040` Decision 9's mechanism

### The re-derivation, from source, at `HEAD`

Read against a `git archive HEAD` snapshot outside the repo and cross-checked against the working tree, which agree on every line quoted here.

**One seam, not two.** [`registry.py::register_subsystem_clear`][registry] has the signature `register_subsystem_clear(clear, *, owner, before_bind=False)` and stores `_subsystem_clears[owner] = (clear, before_bind)`. It is the only registration path for a registry-wide co-clear.

**The phase filter is the flag, not the list.** [`registry.py::iter_subsystem_clears`][registry] takes `before_bind: bool = False` and returns `tuple(clear for clear, runs_before_bind in _subsystem_clears.values() if not before_bind or runs_before_bind)`. So:

- [`registry.py::TypeRegistry.clear`][registry] calls `iter_subsystem_clears()` with no argument and replays **every** registered row.
- [`types/finalizer.py::finalize_django_types`][types-finalizer] calls `iter_subsystem_clears(before_bind=True)` and replays only the flagged subset. Its own comment states the contract: #"phase filter selects emitted namespaces and per-pass caches, never declaration".

**`_clear_if_importable` is not the seam's replay mechanism.** Its docstring at `HEAD` says so outright — it is the cycle-safe local-import shape for a **per-type** co-clear, with `TypeRegistry.unregister`'s connection-class cache eviction as its only caller, and it explicitly records that `clear()`'s registry-wide co-clears "do not go through this helper".

**Every call site, with its flag.** Seventeen rows at `HEAD`; seven carry `before_bind=True`, ten do not.

| Owner | Site | `before_bind` |
|---|---|---|
| `filters.input_namespace` | `filters/inputs.py:996` | **True** |
| `orders.input_namespace` | `orders/inputs.py:384` | **True** |
| `mutations.input_namespace` | `mutations/inputs.py:205` | **True** |
| `forms.input_namespace` | `forms/inputs.py:167` | **True** |
| `rest_framework.input_namespace` | `rest_framework/inputs.py:162` | **True** |
| `rest_framework.shape_cache` | `rest_framework/inputs.py:1752` | **True** |
| `auth.current_user_alias` | `auth/queries.py:60` | **True** |
| `mutations.declarations` | `mutations/sets.py:657` | default (False) |
| `forms.declarations` | `forms/sets.py:130` | default (False) |
| `auth.declarations` | `auth/mutations.py:167` | default (False) |
| `mutations.shape_cache` | `mutations/sets.py:522` | default (False) |
| `forms.shape_cache` | `forms/sets.py:157` | default (False) |
| `connection.type_cache` | `connection.py:1292` | default (False) |
| `relay.node_fields` | `relay.py:95` | default (False) |
| `filters.helper_references` | `filters/__init__.py:55` | default (False) |
| `orders.helper_references` | `orders/__init__.py:48` | default (False) |
| `rest_framework.choice_enums` | `rest_framework/serializer_converter.py:267` | default (False) |

### The determination: the distinction survives, the mechanism does not

Worker 0's measurement is confirmed and is the whole story. Decision 9's **contract** — the auth declaration ledger survives the finalizer's pre-bind reset, beside the mutation and form declaration ledgers, while the auth emit artifacts are drained and rebuilt — holds exactly, and is enforced by the `auth.declarations` row carrying no `before_bind` while `auth.current_user_alias` carries `before_bind=True`.

The **mechanism** the Decision pins does not hold, in four separate ways:

1. The declaration registries are **not** excluded from `register_subsystem_clear`; all three go through it.
2. The seam's signature is not `register_subsystem_clear(module_path, attr)`; it takes a resolved callable plus a keyword `owner`.
3. Its rows are not iterated via `_clear_if_importable`, which is a per-type helper with one unrelated caller.
4. The pre-bind reset does not drain "every `register_subsystem_clear` row"; it drains the `before_bind=True` subset.

So the distinction moved from *which list a row is in* onto the `before_bind` phase flag, and the correct vocabulary — taken from the archive rather than invented, [`spec-027`][spec-027] `### Decision 9` already spelling it as "`before_bind=True` additionally marks the input-namespace reset as generated state the finalizer re-runs … the helper-reference ledger is a full-clear-only callback" — is **full-clear-only row** versus **pre-bind row**.

### The blast radius, and the before/after for each site

Sixteen sentences depended on the false mechanism. Line numbers are the pre-edit ones.

| # | Site | Before | After |
|---|---|---|---|
| 1 | 190 (Revision 3 preamble) | the `` `registry.py` `_subsystem_clears` "pre-bind INPUT-namespace clears only, NOT declaration registries" contract `` | `` the `registry.py` `_subsystem_clears` phase contract — the finalizer's pre-bind reset replays only the `before_bind=True` rows, never a declaration registry `` |
| 2 | 199-204 (Revision 3, P1 A) | "the auth **declaration** ledger clear is moved OFF `register_subsystem_clear` (that seam is documented as pre-bind INPUT-namespace clears only …) onto a `TypeRegistry.clear()` hand row …; the only new `register_subsystem_clear` row is the `current_user` generated-alias namespace" | "the auth **declaration** ledger clear is a **full-clear-only** `register_subsystem_clear` row — registered without `before_bind`, so `TypeRegistry.clear()` replays it while the finalizer's pre-bind reset … never reaches it — beside the `mutations.declarations` / `forms.declarations` rows; … the only net-new **pre-bind** row is the `current_user` generated-alias namespace" |
| 3 | 413 (Revision 7 summary) | "declaration ledger drained by the `TypeRegistry.clear()` hand row" | "declaration ledger drained by its full-clear-only row" |
| 4 | 593-598 (`## Slice checklist` sub-bullet) | "ledger cleared by a `TypeRegistry.clear()` hand row beside `clear_mutation_registry` / `clear_form_mutation_registry` — **not** [`register_subsystem_clear`][registry] (that seam is drained by the pre-bind reset, which must not touch declarations)" | "ledger cleared by a full-clear-only [`register_subsystem_clear`][registry] row beside `clear_mutation_registry` / `clear_form_mutation_registry` — registered **without** `before_bind`, so the pre-bind reset, which must not touch declarations, never reaches it" |
| 5 | 778-787 (`## Current state`) | "ships `register_subsystem_clear(module_path, attr)` for the **pre-bind INPUT-namespace / emit ledgers** — its rows are iterated via `_clear_if_importable` from both `TypeRegistry.clear()` and the … pre-bind reset block — and its own comment … **excludes declaration registries**, which are hand-rowed in `TypeRegistry.clear()` only" | "ships one registration seam, `register_subsystem_clear(clear, *, owner, before_bind=False)`, and the `before_bind` flag is what splits the two lifecycles … `TypeRegistry.clear()` replays **every** registered row through `iter_subsystem_clears()`; the … pre-bind reset block replays only the `before_bind=True` subset … the declaration registries are **full-clear-only** rows" (three fresh citations, below) |
| 6 | 1486 (Decision 6) | "declaration ledger itself, drained by the `TypeRegistry.clear()` hand row**" | "declaration ledger itself, drained by its full-clear-only row**" |
| 7 | 1893-1900 (Decision 9, step 1) | "(`iter_subsystem_clears()` in …) drains every [`register_subsystem_clear`][registry] row — which are, by that seam's own contract, the **emit / input-namespace ledgers only, never the declaration registries** … This is why the auth **declaration** ledger must NOT be a `register_subsystem_clear` row" | "(`iter_subsystem_clears(before_bind=True)` in …) drains the `before_bind=True` [`register_subsystem_clear`][registry] rows — which are, by that flag's own contract, the **emit / input-namespace ledgers and per-pass caches only, never the declaration registries** … This is why the auth **declaration** ledger must NOT carry `before_bind=True`" |
| 8 | 1945-1950 (Decision 9, clear paths) | "a hand-written `_clear_if_importable` row beside the existing `clear_mutation_registry` / `clear_form_mutation_registry` declaration-clear rows (…), **not** `register_subsystem_clear`" | "a full-clear-only [`register_subsystem_clear`][registry] row (owner `auth.declarations`, no `before_bind`) beside the existing … declaration-clear rows (…), **never** `before_bind=True`" |
| 9 | 1961-1965 (Decision 9, emit path) | "follow the pre-bind seam … ride the **existing** `mutations.inputs` `register_subsystem_clear` row … The **only** net-new `register_subsystem_clear` row is" | "follow the pre-bind phase … ride the **existing** `mutations.inputs` `before_bind=True` row … The **only** net-new `before_bind=True` row is" |
| 10 | 1977-1978 (Decision 9, justification) | "routing the declaration ledger through the pre-bind seam breaks both the first finalize" | "giving the declaration ledger `before_bind=True` breaks both the first finalize" |
| 11 | 1996-2003 (rejected alternative) | "**Route the auth declaration ledger through `register_subsystem_clear`** … Rejected …: that seam is drained by the pre-bind reset loop … The declaration-clear belongs in `TypeRegistry.clear()`" | "**Register the auth declaration ledger with `before_bind=True`** … Rejected …: those rows are drained by the pre-bind reset loop … The declaration-clear is a full-clear-only row" |
| 12 | 2148 (slice table, Slice 1) | names `` [`registry.py`][registry] `` as a file the slice touches, "(the auth **declaration** ledger's `TypeRegistry.clear()` hand row … — NOT `register_subsystem_clear`; …)" | the `registry.py` entry is **removed** (the row lives with the ledger in `auth/mutations.py`, already listed) and the contract folded into that file's parenthetical: "the ledger's own full-clear-only [`register_subsystem_clear`][registry] row … — no `before_bind`; `LoginPayload` / `LogoutPayload` ride the existing `mutations.inputs` pre-bind row, so no new pre-bind row lands here" |
| 13 | 2224-2226 (DoD, D15) | "the current_user alias uses the pre-bind `register_subsystem_clear` seam; the auth declaration ledger uses a `TypeRegistry.clear()` hand row" | "the current_user alias's `register_subsystem_clear` row carries `before_bind=True`; the auth declaration ledger's row carries no `before_bind`" |
| 14 | 2329 (edge cases) | "declaration ledger drained by the `TypeRegistry.clear()` hand row," | "declaration ledger drained by its full-clear-only row," |
| 15 | 2372-2374 (edge cases, reload) | "(its `TypeRegistry.clear()` hand row, beside the mutation / form declaration clears — NOT the pre-bind seam," | "(its full-clear-only row, beside the mutation / form declaration clears — no `before_bind`," |
| 16 | 2449-2450 (test plan) + 2674-2678 (DoD, Slice 1) | "the **declaration** ledger clears via the `TypeRegistry.clear()` hand row (NOT the pre-bind seam)"; "(no new `register_subsystem_clear` row in Slice 1), the auth **declaration** ledger cleared by a `TypeRegistry.clear()` hand row … (NOT the pre-bind seam" | "clears via its full-clear-only row (no `before_bind`)"; "(no new pre-bind `register_subsystem_clear` row in Slice 1), the auth **declaration** ledger cleared by a full-clear-only [`register_subsystem_clear`][registry] row … (no `before_bind`" |

Three sites carrying the seam vocabulary were **verified true and left alone**: line 135 (Decision 9's summary naming "the [`register_subsystem_clear`][registry] rows" — accurate, and more accurate than before), line 1722 ("the alias namespace's pre-bind [`register_subsystem_clear`][registry] row" — `auth.current_user_alias` does carry `before_bind=True`), and line 316 ("the declaration-ledger-on-`TypeRegistry.clear()` vs emit-ledger-on-pre-bind split" — a statement of the phase contract, not of seam membership). The Decision 9 **heading** was not touched: every in-page anchor in the spec targets it.

Post-edit sweep for the retired vocabulary returns nothing: `grep -n "hand row\|hand-rowed\|_clear_if_importable\|pre-bind seam\|module_path, attr"` over the spec is empty.

### Three citations added, each measured for uniqueness at `HEAD` and in the tree

| Citation | Occurrences (`grep -oF`) | Enclosure |
|---|---|---|
| `registry.py::register_subsystem_clear` #"marks generated-state resets that the finalizer also" | 1 / 1 | line 78, inside `register_subsystem_clear` (68-91) |
| `types/finalizer.py::finalize_django_types` #"phase filter selects emitted namespaces and per-pass caches" | 1 / 1 | line 1068, inside `finalize_django_types` (opens 803) — nearest enclosing `def`, confirmed by scanning every top-level `def`/`class` above it |
| `mutations/sets.py` #"register_subsystem_clear(clear_mutation_registry" and `forms/sets.py` #"register_subsystem_clear(clear_form_mutation_registry" and `auth/mutations.py` #"register_subsystem_clear(clear_auth_mutation_registry" | 1 / 1 each | module-level statements, so the module-level `path #"substring"` form is the correct one |

Substrings were chosen to carry no inner double quote, which is why the citations name the call rather than the `owner="…"` keyword: a `#"…"` anchor containing `"` cannot close.

One candidate was **rejected on measurement**: an `auth/queries.py` #"clear_current_user_alias_namespace," anchor for the alias row. It occurs **twice** in that file (the trio unpack at line 52 and the registration at 61), and rule 27 requires uniqueness, so the sentence carries no citation rather than a non-unique one. This is the fourth-outcome discipline applied as a precondition instead of a postcondition.

The three retargeted sites replace the three zero-hit `registry.py` citations cohort G reflowed and reported (its sites 7, 10 and 11) — those anchors quoted the very comments the seam refactor retired, so the mechanism repair discharges them as a side effect rather than leaving them zero-hit.

### One link definition added

`[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py`, under the file's existing `<!-- django_strawberry_framework/ -->` group, alphabetically first. It is used once (site 8). No definition was removed; `[registry]`, `[types-finalizer]`, `[mutations-sets]` and `[forms-sets]` were already defined and already in use.

### The rationale companion does not exist, and was not created

`ls docs/SPECS/appx/` carries `spec-040-auth_mutations-0_0_13-terms.csv` but **no** `spec-040-auth_mutations-0_0_13-rationale.md`. Per the dispatch, creating one is a structural decision outside this cohort's fence, so the correction is recorded here and not in a new companion. **This leaves spec-040 with its deliberative layer still inline** — its `## Revision history` block, and a `Justification:` / `Alternatives considered (and rejected):` pair under each Decision — which is the same condition `spec-027` was in before this cycle's Slice 1. Reported below as work for Worker 0 to card, not guessed at here.

The consequence for this task: the corrected Decision 9 could not close with a `Rationale companion — …` pointer the way [`spec-027`][spec-027] `### Decision 9` does. Its justification and rejected alternatives stay in place, with the one falsified alternative restated (site 11) rather than deleted, because the alternative it names is a real one the card really rejected — only its spelling was wrong.

---

## Task 2 — `spec-033`'s opener and `Status:` line

### The card id, verified rather than assumed

`grep -c "DONE-033-0.0.9" KANBAN.md` returns **11**. `grep -n "033-0.0.9" KANBAN.md | grep -v DONE` returns nothing, so no `WIP-` or `TODO-` spelling survives on the board and the renumber left this id stable. The board's own prose (line 64) reads "`DONE-033-0.0.9` (connection-aware optimizer planning) has shipped, closing out the cohort".

### The archive convention, measured

Two questions had to be answered separately, because the archive answers them differently.

**Where the release/card statement lives.** 17 of the 56 archived specs carry a `Target release:` header line; **39 do not** and instead open with a prose paragraph on line 3. The `Target release:` family is the `001`-`027` era exactly (and is what the dispatch's four named records — `020`, `023`, `026`, `027` — use). `spec-033` has no `Target release:` line at all, so importing that shape would be adopting a superseded era's header block rather than matching a convention. The prose opener is the dominant form and is `spec-033`'s own era's form, so the opener was **corrected in place, not removed**.

**How a realigned shipped record spells it.** Among the 028+ era, the openers diverge on verb — `040` "Shipped in", `042`/`043`/`044`/`045` "Built for", `046`/`047` "Targeted at", and `030`/`031`/`034`/`035`/`036`/`037` still "Planned for" on `DONE-` cards. The signal is not the verb census but the **comparable population**: the only two specs in the era whose opener has already been realigned to a shipped record are `spec-028` ("Shipped in `0.0.8` (card [`DONE-028-0.0.8`][kanban] …). **This spec is the final implementation record, not an open build plan.**") and `spec-040` ("Shipped in `0.0.13` (card [`DONE-040-0.0.13`][kanban])."). Both use `Shipped in`, and `spec-028` supplies the exact clause that replaces "not a shipped record". That is the convention matched.

**The checklist rule, from the archive's own words.** [`spec-045`][spec-045]'s `Status:` line states it: "The Slice checklist boxes below stay unticked because the `Status:` line is the completion source of truth (the shipped-spec convention)". `spec-047`, `spec-048` and `spec-049` carry the same sentence, and `spec-033`'s own opener already declared its checklist unticked. **No box was ticked in any file this cohort touched.**

### Before / after

**Opener (line 3), first sentence.** Before: "Planned for `0.0.9` (card [`WIP-ALPHA-033-0.0.9`][kanban]). **This spec is an open build plan, not a shipped record.** The card is the only card in the `## In progress` column and the **last open member of the `0.0.9` Relay cohort**: it closes the performance gap the cohort deliberately left open". After: "Shipped in `0.0.9` (card [`DONE-033-0.0.9`][kanban]). **This spec is the final implementation record, not an open build plan.** The card is the **last member of the `0.0.9` Relay cohort** and closes the performance gap the cohort deliberately left open".

**Opener, checklist clause.** Before: "The [Slice checklist](#slice-checklist) below stays unticked as the contract record (build progress is tracked in the build plan, not here);". After: "The [Slice checklist](#slice-checklist) below stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention; build progress is tracked in the build plan, not here);".

**`Status:` line (line 5), leading portion.** Before: "Status: in progress — all seven slices (…) accepted, and the cross-slice integration pass and the final test-run gate have both passed; the build's functional and gate work is complete and the card now awaits maintainer handoff and commit (…). The `WIP-ALPHA-033-0.0.9` card has moved to `DONE-033-0.0.9` and the on-disk version remains `0.0.8` (…). The [Slice checklist](#slice-checklist) below stays unticked as the contract record regardless of build progress (…)." After: "Status: **SHIPPED (`0.0.9`) — all seven slices (…) final-accepted; cross-slice integration pass + final test-run gate green.** Card [`DONE-033-0.0.9`][kanban]. The `0.0.9` version bump and the `CHANGELOG.md` release-heading promotion belong to the joint cut, not to this card, per [Decision 12](…). The [Slice checklist](#slice-checklist) below stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention; progress is tracked in the build plan, not here)." The seven-slice enumeration that follows was not touched.

Two claims were **deleted rather than restated**, per `BUILD.md`'s rule that prose the current state has falsified belongs in neither file: "the card now awaits maintainer handoff and commit" (the card is Done and `0.0.9` is released), and "the on-disk version remains `0.0.8`" (`pyproject.toml` is at `0.0.14`). The surviving authoring-time snapshot in the opener, "(the on-disk version is still `0.0.8` at spec-authoring time)", is explicitly tense-marked and stays.

**One further stale card id, same class, corrected.** Line 228, inside Decision 11's filename derivation, asserted "The card is `WIP-ALPHA-033-0.0.9`, so `<NNN>` is `033` and `<0_0_X>` is `0_0_9`." — a bare present-tense claim about the card's identity. Now "The card is `DONE-033-0.0.9`, …". The `<NNN>` / `<0_0_X>` derivation is unchanged and still correct.

Line 564's Slice-7 doc-updates instruction ("move [`WIP-ALPHA-033-0.0.9`][kanban] to Done with the next `DONE-NNN-0.0.9` id") was **left**: it is an imperative slice step whose subject is legitimately the pre-move id, not a status claim, and rewriting it would be editing the plan record rather than reconciling a falsehood.

Line 106's quotation of a `connection.py` docstring is repaired in the follow-up pass below, together with a second site the first pass did not reach. The claim made here in the first pass — that the quotation was "accurate at `HEAD`" — was **wrong, and wrong because it sampled the card id rather than reading the quoted sentence**; see `### Follow-up pass`.

---

## Task 3 — `spec-037`'s opener

### The card state, verified

`grep -c "DONE-037-0.0.11" KANBAN.md` returns **8**, and `grep -n "037-0.0.11" KANBAN.md | grep -v DONE` returns nothing. `CHANGELOG.md` carries `## [0.0.11] - 2026-06-19`, so the release itself shipped, not merely the card.

### Correct the opener, do not remove it

The measurement is the one under Task 2: `spec-037` has no `Target release:` line, and 39 of 56 archived specs carry the prose opener instead. Removing the opener would leave the spec with no release or card statement anywhere in its header. Cohort G's observation is confirmed — the *verb* is not house style — but the *form* is, and among realigned shipped records in this era the verb is `Shipped in`. Corrected, not removed.

### Before / after

**Opener (line 3).** Before: "Planned for `0.0.11` (card [`DONE-037-0.0.11`][kanban]). This card". After: "Shipped in `0.0.11` (card [`DONE-037-0.0.11`][kanban]). This card". Nothing else in the paragraph changed.

**`Status:` line, extended beyond the dispatch's letter and why.** The dispatch names only the opener, but line 38 read `Status: **IN PROGRESS** — authored for `TODO-ALPHA-037-0.0.11` …` on the same card. Correcting the opener alone would have left one spec asserting both states — the half-reconciliation that is worse than no fix, and the same reasoning cohort G used to extend into `spec-039`'s unwrapped sibling. Before: "Status: **IN PROGRESS** — authored for `TODO-ALPHA-037-0.0.11` via the [`docs/SPECS/NEXT.md`][next] flow; **all four slices final-accepted** (the in-spec build is complete; the cross-slice integration pass + final gate still follow). The `docs/TREE.md` summary anchor that blocked Slice 4 was discharged (summaries updated, anchor removed); see the Slice 4 build artifact." After: "Status: **SHIPPED (`0.0.11`)** — card [`DONE-037-0.0.11`][kanban], released under the [`CHANGELOG.md`][changelog] `## [0.0.11]` heading; authored via the [`docs/SPECS/NEXT.md`][next] flow, **all four slices final-accepted**. The [Slice checklist](#slice-checklist) below stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention)."

Three things were deliberately dropped rather than restated: the stale `TODO-ALPHA-037-0.0.11` id, the "integration pass + final gate still follow" claim (falsified by the released `0.0.11`), and the `docs/TREE.md`-anchor sentence pointing at "the Slice 4 build artifact" — a `bld-*` per-cycle reference, which the hard constraints put out of a spec entirely. The new `Status:` claims only what is grounded: the card id, the `CHANGELOG.md` release heading, and the four-slice acceptance the previous line already asserted. **No gate colour was asserted for `037`**, because no `037` gate artifact survives to measure against (`docs/builder/DONE/` carries none; the artifacts were deleted in commits `998ff42c` / `64a5e47c`).

`[changelog]`, `[kanban]`, `[next]` and the `#slice-checklist` anchor were all confirmed present in the file before use.

The nine remaining `TODO-ALPHA-037-0.0.11` occurrences (lines 15, 101, 345, 347, 486, 563, 1122, 1566, 1659) were **left**. Four are the zero-hit citations cohort G measured and deliberately reflowed-without-rewriting; the rest are revision-history entries, `## Current state` authoring snapshots, and a Slice-5 board-move instruction. Cohort G's determination stands: a citation pinning a line the card's own shipping removed is a finding, not a spec rewrite.

---

## Task 4 — the last wrapped citation in the two spec directories

### The instrument, and the bug it does not inherit

Worker 0's census tested only the first `#"` per line, which is precisely why this site went unseen. This cohort's instrument walks **every** `#"` occurrence on each line with `str.find` in a loop. An occurrence is wrapped when no further `"` appears later on that line. Classification order is cohort E's corrected order — **test closure first**, because a citation opened after `(` or `[` is still a citation; only then the predecessor character, where a non-whitespace, non-`(`, non-`[` predecessor marks a `"#"` / `^###"` string-literal false positive. Script under this session's private `cohortH-027/` scratchpad subdirectory, outside the repo.

### The determination: zero-hit, and no retarget exists

`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md:1252` carried two citations. Both are bare `#"substring"` anchors quoted in prose against a target named two sentences earlier, [`spec-003`'s rationale][spec-003-rationale].

| Citation | Flattened substring | Occurrences in the target | Determination |
|---|---|---|---|
| closes on 1252 | `the plan is finalized before handoff` | **1** (line 955) | resolves |
| wraps onto 1253 | `plan immutability, the projection gate` | **0**, and **0** with the target's own newlines flattened to spaces | **zero-hit** |

The zero is not a wrap on the target's side (the flattened count rules that out) and no retarget exists: the target sentence the anchor quoted has been replaced by one that no longer makes the claim. At `HEAD` the target's line 522 reads "[`spec-035`][spec-035] (the projection gate)" inside a list of four extending specs — and "the projection gate" is exactly the item the finding itself exempts as sound. The `path::Symbol` fallback does not apply either: the target is a Markdown file, not code.

So neither remedy the three-outcome scheme offers is available, and the discharge is cohort G's for the same class: **reflow so the anchor is visible to any future instrument, leave the sentence untouched, report the finding.**

**Before** (lines 1252-1254):

```
    #"the plan is finalized before handoff" hands it the tuple swap; #"plan immutability, the
    projection gate" lists it among that spec's extensions (only the projection-gate item on that
    line is sound — it is [`spec-035`][spec-035] Decision 4).
```

**After:**

```
    #"the plan is finalized before handoff" hands it the tuple swap;
    #"plan immutability, the projection gate" lists it among that spec's extensions (only the
    projection-gate item on that line is sound — it is [`spec-035`][spec-035] Decision 4).
```

### The file-wide census, and what it found beyond the wrap

The file carries **six** citations on five lines (1250, 1252 ×2, 1255, 1256, 1257) — every one an anchor into the same target, all part of one finding. Exactly **one** is wrapped, the one dispatched. Measuring the other five as well, because a wrapped-only sweep would have inherited its instrument's blind spot:

| Line | Substring | Occurrences in the target |
|---|---|---|
| 1250 | `Both are later hardening` | 1 (line 252) |
| 1252a | `the plan is finalized before handoff` | 1 (line 955) |
| 1252b | `plan immutability, the projection gate` | **0** |
| 1255 | `each already stated once in its own document` | **0** |
| 1256 | `for the rest` | **0** |
| 1257 | `'s to state` | **0** |

Four of six are zero-hit, and the two that resolve now say the opposite of what the finding reports: the target's line 252 reads "Both are later hardening (`optimizer/plans.py::OptimizationPlan.finalize` and `::_consumer_prefetch_lookups`; **no sibling spec states either discipline**)" and its line 955 reads "the plan is finalized before handoff (`optimizer/plans.py::OptimizationPlan.finalize`; **no sibling spec states that enforcement**)". Both name the enforcing symbol and explicitly deny a sibling-spec owner, which is the correction the finding asked for.

The finding's census is stale on top of that: it claims the target carries "six body uses plus the definition" of `[spec-035]`, each carrying the error. At `HEAD` `grep -n '\]\[spec-035\]\|spec-035-optimizer'` over the target returns **one** body use (line 522) plus the definition (line 1055), and that one body use is the item the finding exempts.

**Not repaired, and the reason is the dispatch's own escape hatch.** Rewriting the finding means deciding whether it is discharged, still open, or should be deleted — a claim about another card's reconciliation state, in a rationale companion where a record of what a review pass found is legitimate content. That is a decision this cohort cannot ground in measurement, so it is reported rather than guessed at. The measurement itself is complete and is above.

### Census: precondition, postcondition, control

| Run | Scope | Wrapped |
|---|---|---|
| Precondition | every tracked `.md`, working tree | **8** (cohort G's postcondition, independently re-measured) |
| Precondition | every tracked `.md`, `git archive HEAD` snapshot | **26** |
| Precondition | `docs/SPECS/` + `docs/SPECS/appx/`, at `HEAD` | **19** |
| Postcondition | every tracked `.md`, working tree | **7** |
| Postcondition | `docs/SPECS/` + `docs/SPECS/appx/`, working tree | **0** |
| Control | the same instrument over the `HEAD` snapshot, re-run after the edits | **26** — the instrument still finds the originals, so the 0 is the tree changing, not the instrument breaking |

**Zero wrapped citations remain in the two spec directories.** The surviving 7 are all `docs/builder/` per-cycle artifacts — `bld-slice-4-027-broken_substring_citations.md` ×5 (lines 224, 304, 744, 1211, 1383), `bld-slice-5-027-retired_mechanism_docstrings.md:330`, and `docs/builder/DONE/build-046-transport_security-0_0_15.md:177` — which the dispatch places out of fence and `START.md` exempts from the symbol-qualified path rule.

**No reflow created a new wrapped citation**, and the proof is the repo-wide postcondition rather than a spot check of the edited lines. Run directly against this artifact the instrument reads 20 citation occurrences and **one** wrap — the `**Before**` fenced block above, which reproduces the defect verbatim as its own evidence. It is deliberate; a future sweep must not "repair" it, and `bld-*` artifacts are out of fence in any case. Task 1's rewrite of the `## Current state` bullet left a two-word orphan line, which was re-joined into the preceding line; no other prose was rewrapped, so no unrelated citation in an edited paragraph was disturbed.

---

## Validation run

| Command | Result |
|---|---|
| `uv run python scripts/check_citations.py` | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md).` |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | `OK: 38 terms - all have glossary entries and at least one spec link.` |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` | `OK: 20 terms …` |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md` | `OK: 30 terms …` |
| `uv run python scripts/check_trailing_commas.py --check <all four files>` | exit 0, no output |
| markdown wrapped-citation census | 8 → 7 tree-wide; **0** in `docs/SPECS/` + `appx/`; control 26 (table above) |

**The citation count is identical to cohort G's `782` and this cohort cannot have moved it.** The gate's own module docstring holds `docs/` out of scope, and all four files this cohort touched are under `docs/`. The number matching cohort G's exactly, across a window in which cohort F is actively writing `.py` files, is a measured coincidence rather than evidence — the point is only that the gate is green and the delta is not ours.

No `pytest` was run: the diff adds no executable statement.

## `git status --porcelain` classification

Captured before the first edit, after the last, and again after this artifact was written; each pair diffed rather than eyeballed. Before: **80** paths. After the spec edits: **81** — exactly one line differs, and it is this cohort's:

```
> M docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
```

The other three files this cohort edited were already `M` from cohort G, so no new path appeared for them. After this artifact: **83** — two further lines, `?? docs/builder/bld-slice-13-027-shipped_card_spec_staleness.md` (this file) and `M tests/test_routers.py`, the latter cohort F landing a file mid-pass. Every path in the final state classifies as:

- **This cohort (5):** `docs/SPECS/spec-033-…`, `spec-037-…`, `spec-040-…` (all three shared with cohort G), `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` (newly dirty, this cohort alone), and this artifact (??).
- **Cohort G, shared surface:** `docs/SPECS/spec-039-…`, `spec-041-…`, `spec-045-…`, `spec-046-…`, `appx/spec-001-…-rationale`, `appx/spec-009-…-rationale`, `appx/spec-015-…-rationale`. Untouched here.
- **Cohort F (`.py`, concurrent), 56 paths:** 32 under `django_strawberry_framework/`, 3 under `examples/fakeshop/apps/`, 2 under `examples/fakeshop/test_query/`, 19 under `tests/`. Untouched.
- **The concurrent `spec-028` session:** `docs/SPECS/spec-028-orders-0_0_8.md` (M), `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md` (??), `docs/builder/bld-slice-{1,2}-028-*.md` (??), `docs/builder/build-028-orders-0_0_8.md` (??). Read for the opener convention only; never written, never reverted (`AGENTS.md` rule 34).
- **Cohort D, landed:** `docs/SPECS/spec-055-search_fields-0_1_2.md` (M). Untouched.
- **Worker 0 and earlier cohorts:** `docs/builder/build-027-filters-0_0_8.md` (M, and observed changing mid-pass — Worker 0 is editing it) plus `docs/builder/bld-slice-{6,7,8,9,10,11,12}-027-*.md` (??). `bld-slice-4-027` and `bld-slice-5-027` are **tracked and clean** (already committed), which is why the census reads them from `HEAD` but `git status` does not list them.

Byte counts, `HEAD` → working tree: `spec-033` 173,813 → 173,689 (−124); `spec-037` 116,063 → 116,067 (+4); `spec-040` 207,230 → 207,794 (+564); `spec-004`-rationale 94,744 → 94,744 (unchanged, a pure reflow). The `spec-037` and `spec-040` deltas include cohort G's reflows as well as this cohort's edits.

### Implementation notes

- **The corrected vocabulary was taken from the archive, not invented.** "Full-clear-only" is [`spec-027`][spec-027] `### Decision 9`'s own word for a callback the finalizer's phase filter does not select, and `registry.py`'s docstring is the source for the pre-bind half. Coining a new pair here would have left two spellings of one contract across two specs.
- **Substring choice was constrained by the anchor's own quoting.** A `#"…"` citation cannot contain a double quote, so every new anchor names the `register_subsystem_clear(<callable>` call rather than the adjacent `owner="…"` keyword, even where the owner string would have read better.
- **Hit counts were checked for enclosure, not only for count** (cohort E's trap). It mattered for the finalizer anchor: line 1068 sits inside `finalize_django_types`, whose `def` opens 265 lines earlier at 803, and the two `def`s numerically nearest above it in the file (`_synthesize_relation_connections` at 612, a nested `teardown` at 569) are both *before* it — so the enclosing symbol had to be established by scanning every top-level definition rather than by taking the closest match.
- **Reflow direction was chosen per site to keep the paragraph's shape**; Markdown carries no line-length gate, so width was aesthetic and was never allowed to argue for splitting a citation across lines.
- **Every measurement was taken twice**, against a `git archive HEAD` snapshot outside the repo and against the working tree, because cohort F is rewriting the very modules Task 1 depends on. All twelve substrings agree across both, so no conclusion here rests on a concurrently-edited line.

### Notes for Worker 3

No Worker 2 / Worker 3 cycle: the diff touches no `.py` file and changes no contract a test can pin. If one runs anyway, the three claims worth re-deriving mechanically are the seventeen-row call-site table (one `grep -rn "^register_subsystem_clear(" -A 4`), the census postcondition with its control, and the six-citation determination table for Task 4 (six `grep -oF … | wc -l` invocations).

### Notes for Worker 1 / Worker 0 — findings left in place

Each is measured; each is outside this cohort's fence; none was repaired.

1. **`spec-040` has no rationale companion, and its deliberative layer is still inline.** `docs/SPECS/appx/` carries the `-terms.csv` but no `-rationale.md`. The spec is 207KB with a full `## Revision history` chronology (Revisions 1-7+) and a `Justification:` / `Alternatives considered (and rejected):` pair under each of twelve Decisions — the same condition `spec-027` was in before this cycle's Slice 1, and `BUILD.md` `## Spec rationale extraction` makes the move the first substantive action of a build. Creating the companion is a structural decision; carding it is Worker 0's.
2. **The same staleness class survives on five more specs' openers.** `spec-030`, `spec-031`, `spec-034`, `spec-035` and `spec-036` all read "Planned for `0.0.X` (card [`DONE-NNN-0.0.X`][kanban])" — a `DONE-` id inside a "Planned for" sentence. `spec-029` and `spec-032` are worse: both still carry a live `WIP-ALPHA-` id in the opener plus a `Status: in progress` / `in build` line, and `spec-029`'s Status says the KANBAN move is "pending". `spec-038` reads "Planned for `0.0.12` (card `TODO-ALPHA-038-0.0.12`)" and `spec-039` "Implemented on main; release deferred to the joint `0.0.13` cut" — `0.0.13` shipped. `spec-028` is in the same class but is the concurrent session's file.
3. **Two live `.py` sites still carry the pre-ship card id `WIP-ALPHA-033-0.0.9`**: `connection.py:1885` ("reachable as the cooperation seam ``WIP-ALPHA-033-0.0.9``'s") and `types/finalizer.py:660` ("connection pipeline is ``WIP-ALPHA-033-0.0.9``'s scope"). Both name a card that shipped as `DONE-033-0.0.9`. `.py` is another cohort's surface, so they were reported rather than touched. **Partly discharged:** cohort I repaired `connection.py:1885`, and the `### Follow-up pass` above then repaired the spec side. `types/finalizer.py:660` is **still open** — this cohort could not verify it against a spec quotation because no spec quotes it, so it needs a `.py`-side owner.
4. **`spec-004`'s rationale carries a stale finding, not just a stale citation.** Its "It credits spec-035 with the work" / "It asserts spec-035 has already stated it" / "It instructs a future pass to make it true" catalogue reports six erroneous `[spec-035]` uses in [`spec-003`'s rationale][spec-003-rationale]; at `HEAD` that file has **one** body use plus its definition, four of the six quoted anchors are zero-hit, and the two that resolve now explicitly deny a sibling-spec owner. The finding appears to have been discharged by a later pass on the target. Measurement is in Task 4; the disposition is a decision about another card's reconciliation state.
5. **`spec-033:564`'s Slice-7 instruction still names `WIP-ALPHA-033-0.0.9`** as the card to move to Done. Left deliberately (an imperative slice step, not a status claim), but a card-`033` closeout may want to restate it.
6. **Nine `TODO-ALPHA-037-0.0.11` references survive in `spec-037`**, four of them the zero-hit citations cohort G reflowed. They are consistent with each other, so the spec is not half-reconciled; a card-`037` pass would need to decide the whole population at once.

---

## Follow-up pass (Worker 1) — the `spec-033` docstring quotations

Dispatched by Worker 0 after cohort I landed the `.py` half this cohort's finding 3 said had to land first. Scope: `spec-033` only.

### The board count, re-derived — and the first pass's 11 was wrong

`grep -oF "DONE-033-0.0.9" KANBAN.md | wc -l` returns **15**; `grep -n "033-0.0.9" KANBAN.md | grep -v DONE` returns nothing, so no `WIP-`/`TODO-` spelling survives on the board. The first pass reported **11**, and the cause is not the card token but the instrument: `grep -c` counts **matching lines**, and four of the fifteen occurrences share a line with another. That is `BUILD.md` `## Claims are proven mechanically` verbatim — "search the shortest distinctive token and count *occurrences*, not matching lines" — and the first pass reproduced the exact failure the rule names while quoting the rule elsewhere in this artifact. The `spec-037` figure was re-derived the same way and is unaffected: **8** occurrences of `DONE-037-0.0.11`, on 8 distinct lines.

### The code text, read rather than assumed

`django_strawberry_framework/connection.py::_build_relation_connection_resolver`, working tree (cohort I's edit is dirty; `HEAD` differs only in the id):

```
    reachable as the cooperation seam ``DONE-033-0.0.9``'s
    window-pagination planning uses - instead of
```

Measured with the docstring's line wraps flattened to single spaces, counting occurrences in `connection.py`:

| Candidate, in the code's own RST spelling | tree | `HEAD` |
|---|---|---|
| `the cooperation seam ``DONE-033-0.0.9``'s window-pagination planning uses` | **1** | 0 |
| `the cooperation seam ``WIP-ALPHA-033-0.0.9``'s window-pagination planning uses` | 0 | **1** |
| the spec's text as it stood — `…``WIP-ALPHA-033-0.0.9``'s window-pagination planning will use` | **0** | **0** |

**The spec's quotation matched nothing at `HEAD` either**, which settles Worker 0's second point by measurement: the tense had drifted (`will use` where the code says `uses`) **before this cycle touched anything**, so the renumber and the misquotation are two independent defects that happened to sit in one pair of quotation marks. This is also why the first pass's "accurate at `HEAD`" was wrong — it grepped `WIP-ALPHA-033` in `.py`, found the id, and read a matching *token* as a verified *quotation*. A long quoted phrase samples its own vocabulary; only the whole phrase establishes fidelity.

### The second fragment is not drifted — it is gone

`git grep "Deliberately ABSENT"` over the whole tracked tree returns **two hits, both inside `spec-033` itself** (lines 106 and 371) and **none in any `.py` file**, at `HEAD` or in the tree. Neither do any of its distinctive tokens: `Deliberately ABSENT`, `DST_OPTIMIZER_STRICTNESS`, `DST_OPTIMIZER_PLANNED` and `wires it` are each 0/0 in `connection.py`. Worker 0's instruction not to assume anything about the second half of a drifted pair was the right call, and the answer is stronger than drift: **the sentence does not exist.** The reason is this card — its Slice 4 wired strictness for connection paths, so the docstring stopped disclaiming what it now does. The two sentinel *names* remain live symbols (`optimizer/_context.py:35,37`), which is exactly what makes the stale quotation plausible on a skim.

**A second site, in the same file and the same defect, that the dispatch did not name.** Line 371, a `Justification:` bullet under Decision 8, asserted "the `_build_relation_connection_resolver` docstring's \"Deliberately ABSENT\" block names this card" — the same false fidelity claim. Repairing 106 alone would have left one spec asserting the block twice and quoting it once, so both were fixed in this pass. The bullet's other half was checked before touching it and **verifies exactly**: `spec-032`'s Revision 6 P2 reads "`connection.py` never consults the `DST_OPTIMIZER_STRICTNESS` / `DST_OPTIMIZER_PLANNED` sentinels, so the synthesized connection resolver's nested access is silent", and it does place the wiring in `033`. Only the docstring clause was false, so only the docstring clause changed.

### Before / after

**Site A — line 106** (inside `## Current state`, whose preamble marks the whole section "A true description of the repo as of this writing"). Before:

> its docstring documents both the seam ("the cooperation seam `WIP-ALPHA-033-0.0.9`'s window-pagination planning will use") and the deliberate strictness blindness ("Deliberately ABSENT: any `DST_OPTIMIZER_STRICTNESS` / `DST_OPTIMIZER_PLANNED` consultation … until `033` wires it").

After:

> its docstring names the seam ("the cooperation seam `DONE-033-0.0.9`'s window-pagination planning uses"), and the resolver consults neither the `DST_OPTIMIZER_STRICTNESS` nor the `DST_OPTIMIZER_PLANNED` sentinel, so its nested access is silent — the gap [Decision 8](#decision-8--strictness-mode-wiring-for-connection-paths) closes.

The surviving quotation is character-exact against the code, verified mechanically rather than by eye: the quoted string was extracted from the spec by regex, its markdown single backticks re-spelled as the docstring's RST double backticks, and counted in the flattened source — **1 occurrence**. Single-vs-double backticks are the only difference, and that is this line's own established rendering (`DST_OPTIMIZER_STRICTNESS` and every symbol on it already render RST double backticks as markdown single). The vanished quotation is **not** re-quoted anywhere: it becomes a plain statement of the resolver's behavior, in the same terms `spec-032` source-verified, plus a pointer to the Decision that closes it. `#decision-8--strictness-mode-wiring-for-connection-paths` was confirmed to be the slug already in use elsewhere in the file.

**Site B — line 371.** Before: "…established that nothing implements strictness for connections and assigned the wiring here; the `_build_relation_connection_resolver` docstring's \"Deliberately ABSENT\" block names this card." After: "…established that nothing implements strictness for connections — the synthesized connection resolver reaches neither the `DST_OPTIMIZER_STRICTNESS` nor the `DST_OPTIMIZER_PLANNED` sentinel, so its nested access goes unflagged — and assigned the wiring here."

### Two decided non-edits, stated so a later sweep leaves them alone

Both are historical records where the retired id is the *correct* word, and rewriting either would replace something true with something false.

- **Line 13 — `**Revision 1** — initial draft authored from the [`WIP-ALPHA-033-0.0.9`][kanban] card body…`.** The id was the card's id when that draft was authored. A revision-history entry naming the id as it stood is accurate; "corrected" to `DONE-033-0.0.9` it would claim the draft was authored from a card that did not yet exist under that name. **Decided non-edit.**
- **Line 564 — the Slice-7 instruction to "move [`WIP-ALPHA-033-0.0.9`][kanban] to Done with the next `DONE-NNN-0.0.9` id".** An imperative step, carried out, whose subject is necessarily the pre-move id — the sentence is unintelligible if its object is the post-move id. The first pass left it and it **stays left**, now on the record as a decision rather than an omission.

Post-pass sweep: `grep -n "Deliberately ABSENT\|will use\|WIP-ALPHA-033"` over `spec-033` returns **lines 13 and 564 only** — the two decided non-edits, and nothing else.

### Case-sensitivity caveat on this cohort's measurements

Cohort I's sixth spelling, capital-S `Spec-NNN`, was checked against every number in this artifact. **No measurement here rests on a case-sensitive `spec-NNN` match**, so none needs revising: Task 1's call-site census matched the symbol `register_subsystem_clear` and the retired mechanism vocabulary (`hand row`, `_clear_if_importable`, `module_path, attr`); Tasks 2 and 3 matched the uppercase card tokens `DONE-033-0.0.9` / `DONE-037-0.0.11` and the literal header `Target release:`; Task 4's census matches `#"` and its six determinations are literal prose substrings. The one number that was wrong (the board count) was wrong for the lines-vs-occurrences reason above, not for case.

Re-deriving cohort I's own figures: `.py` reproduces exactly at **52** occurrences. `docs/` does **not** reproduce at 182 — `git grep` over tracked `docs/` returns **167**, and `grep -r` over the working tree returns **183**. The gap is scope, not disagreement: 16 occurrences live in untracked in-flight `bld-*` artifacts that `git grep` cannot see, and with five cohorts writing artifacts concurrently that number moves between measurements (this artifact contributes 0 of them, checked). **167 is the reproducible figure**; any working-tree count of `docs/` is valid only for the instant it was taken. The two capital-S occurrences in this cohort's own `spec-004` rationale (lines 818, 1239) are sentence-initial prose, not references, and affect nothing.

### Validation, follow-up pass

| Command | Result |
|---|---|
| `uv run python scripts/check_citations.py` | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md).` — unchanged, and `docs/` is out of its scope |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | `OK: 38 terms - all have glossary entries and at least one spec link.` |
| `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | exit 0, no output |
| wrapped-citation census, every `#"` per line | **0** in `docs/SPECS/` + `appx/` (89 files); 7 tree-wide, all `docs/builder/` per-cycle artifacts — unchanged, so this pass introduced no wrap |

No new path appeared in `git status --porcelain`: `spec-033` was already `M`. Nothing committed.

---

## Final verification (Worker 1)

Deferred to Worker 1's final pass per the dispatch: this artifact stays `Status: built`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[changelog]: ../../CHANGELOG.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

[next]: ../SPECS/NEXT.md
[spec-003-rationale]: ../SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md
[spec-004-rationale]: ../SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
[spec-027]: ../SPECS/spec-027-filters-0_0_8.md
[spec-033]: ../SPECS/spec-033-connection_optimizer-0_0_9.md
[spec-037]: ../SPECS/spec-037-upload_file_image_mapping-0_0_11.md
[spec-035]: ../SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-040]: ../SPECS/spec-040-auth_mutations-0_0_13.md
[spec-045]: ../SPECS/spec-045-visibility_boundary-0_0_14.md

<!-- docs/builder/ -->

[plan]: build-027-filters-0_0_8.md
[slice-12]: bld-slice-12-027-wrapped_citations_in_specs.md

<!-- django_strawberry_framework/ -->

[registry]: ../../django_strawberry_framework/registry.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
