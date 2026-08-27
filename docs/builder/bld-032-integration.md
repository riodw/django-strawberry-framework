# Build: Cross-slice integration pass — spec-032 residual reconciliation

Spec reference: `docs/SPECS/spec-032-full_relay-0_0_9.md` (shipped record, card `DONE-032-0.0.9`)
Companion: `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md`
Status: final-accepted

Worker-1-only pass per `BUILD.md` `## Cross-slice integration pass`, run after Slices 0-3 closed
`final-accepted` and review round 1 closed `final-accepted`. **This pass changed zero bytes in any
file it audits** — the only edit this spawn made anywhere is the seven M-2 removals recorded in
`docs/builder/bld-032-review-1-spec_diff.md` `## Final verification (Worker 1)`, which belong to the
review round, not here.

## Plan + Final verification (Worker 1)

### Spec status-line re-verification

Recorded under the review round's final-verification section (no edit owed; the reason is a
measurement there, not an omission here). Not repeated.

### Required reading

Every prior artifact was read **in full and in slice order**, per the strict-reading rule that allows
no "as needed": `bld-032-slice-0-rationale_extraction.md`, `bld-032-slice-1-root_field_surface.md`,
`bld-032-slice-2-relation_shapes.md`, `bld-032-slice-3-cross_spec_residue.md`,
`bld-032-review-1-spec_diff.md`, plus `build-032-full_relay-0_0_9.md`, the spec, the companion,
`BUILD.md`, `ARTIFACT.md`, `worker-1.md`, `AGENTS.md`, `START.md`, `GOAL.md`, `CHANGELOG.md`, and
`docs/GLOSSARY.md`. No other worker's memory file was read.

---

## The required steps, adapted honestly

`BUILD.md` `## Cross-slice integration pass` numbers six required steps written for a code build.
Three have a strong analogue in a documentation-reconciliation cycle and are this pass's real work;
three have none. **A step recorded as not-applicable with a reason is a decided answer; silence is
not**, so all six are answered.

| Step | Verdict | Where |
| --- | --- | --- |
| 1. Read every prior artifact in slice order | **performed** | above |
| 2. Static-inspection helper ran or was skipped with a reason, per Python file with review-worthy logic | **not applicable, with reason** | below |
| 3. Compare **Repeated string literals** across shadow overviews | **no analogue; substituted** | `### Step 3 analogue` |
| 4. Compare **Imports** to confirm one-way dependency direction | **no analogue; substituted** | `### Step 4 analogue` |
| 5. Walk every artifact's deferred follow-up | **performed** | `### Step 5` |
| 6. Staged-anchor sweep | **performed** | `### Step 6` |

**Step 2 — not applicable, and the reason is measurable rather than asserted.** The rule scopes the
helper to "every Python file with review-worthy logic the build touched". This build touched seven
`.py` files and added **zero logic** to any of them: `git diff HEAD -- '*.py'` is comment and
docstring text only, and Slice 3 proved that mechanically per file (AST normalized with docstrings
blanked and every node's lineno flattened, byte-identical to `git show HEAD:<path>`; the checker was
proved failable by an executable-change control and a renamed-arg control, and Worker 0 re-verified
it with a second independent instrument). A file with no logic change has no review-worthy logic for
the helper to inspect. The plan's pre-flight records a successful smoke invocation of
`scripts/review_inspect.py` against `django_strawberry_framework/relay.py`, so the tool was
exercised; no per-slice run was owed and none was skipped silently.

---

## Step 3 analogue — one contract, one vocabulary

A repeated string literal in two modules is a code build's duplication. **This document's equivalent
is a contract restated in two vocabularies**: four slices rewrote roughly 60 prose sites in one spec,
and each could have named the same thing differently. Checked mechanically across the spec **and**
the companion.

| Thing | Spelling(s) found | Verdict |
| --- | --- | --- |
| the default relation shape | `"connection"` at every home; `"both"` only ever as the explicit opt-in | one vocabulary |
| the synthesized field | `<field>_connection` (7, Python attribute) / `<field>Connection` (8, SDL) | **deliberate pair**, bridged in the spec at the Slice checklist (`rendered <field>Connection by Strawberry's camel-casing`) and again in Decision 6 |
| the page bound | `relay_max_results` under `resource_policy.py::ResourcePolicy.max_page_size` | one telling, 5 sites |
| the batch bound | `resource_policy.py::ResourcePolicy.max_node_ids` | one telling |
| the policy module | `resource_policy.py::ResourcePolicy.<field>` + the `[resource-policy]` link def, at every site in both files | one vocabulary |
| the coercion contract | noun `id-slot pre-coercion` (6); verb `pre-coerce … against the concrete field behind the target's resolve_id_attr()` (4) | one telling; the bare verb is qualified in place at every occurrence |
| the id strategies | `model-label` (28/8), `type-name` (12/1) | one vocabulary; the 3 unhyphenated uses are prose noun phrases (`an unresolvable model label / type name`), not identifiers |
| `Meta.cursor_field` / `keyset.py` | one spelling each | one vocabulary |

**Stale-vocabulary sweep, run as a negative control on its own subject:**
`implicit .?.?both`, `"both" is the (implicit )?default`, `defaults? to .?.?both`,
`both.{0,12}default`, and `model._meta.pk.to_python`-as-the-contract all return **zero** in the spec.
The single companion hit is a `**Post-ship:**` note quoting the retired sentence in order to record
that it was retired — labelled, at its correct address.

**`"both"` occurrence count re-derived:** 22 in the spec, on 18 lines. Every one was read in context:
3 are the `{"list", "connection", "both"}` vocabulary enumeration, 19 name `"both"` as the explicit
opt-in / an explicit request / a shipped fakeshop key value. **Zero assert or assume it is the
default.** This confirms Slice 2's post-pass 22 against a later state of the file, and confirms the
counter-intuitive shape Slice 2 recorded: a pass whose whole job is to stop calling `"both"` the
default ends with *more* `"both"` occurrences, not fewer.

**The `.py` comment story, read as one story rather than twelve edits.** Slice 3's twelve
comment/docstring rewrites across seven files agree with each other and with the spec: every one says
the default drops the list and `"both"` opts it back in, and the two that state the consumer-authored
skip rule state it **value-independently** (`whatever that default's value is`), which is the same fix
Slice 2 applied to the spec's Decision 7. No file contradicts another. One cosmetic artifact survives
(the `# WITHOUT the` orphan line — review round L-2, routed).

---

## Step 4 analogue — the one-way dependency, spec -> companion

A builder never reads the companion. So the direction that must hold is: **the spec depends on
nothing; the companion may cite the spec freely.** Both halves checked mechanically.

**Keying, both directions, 13/13.** Every one of the spec's 13 `### Decision N` headings carries a
`Rationale companion — …: [Decision N][rationale-dN]` pointer with the **matching numeral** (0
missing, 0 misnumbered), plus the header pointer and the `## Risks and open questions` pointer. Every
one of the companion's 13 `## Decision N` headings is immediately followed by
`Spec: [Decision N — <heading>][spec-032-dN]` with the matching numeral (0 unkeyed, 0 miskeyed). The
two non-Decision companion sections (`## Risks and open questions`, `## Non-Decision deliberation`)
each state what they belong to. An entry that cannot be looked up from either side does not exist
here.

**No normative or implementation-relevant sentence lives only in the companion.** Swept the companion
for `must` / `never` / `always` / `cannot` / `may not` / `is required` — **45 lines**, a deliberately
different and wider net than the review round's marker list. Grouped: 7 in
`### Alternatives considered` (rejected paths, correctly companion-only), 14 in
`### Changes this Decision underwent`, 5 in `### Justification`, 19 in the header / revision history /
Risks / Non-Decision sections. Every candidate that states a live contract was traced to a spec home:

| Companion sentence | Spec home |
| --- | --- |
| the no-Node-types check *must* live at finalization | `### Error shapes` (`ConfigurationError` at finalization) + `## Key glossary references` + `## Slice checklist` |
| the synthesis step *must* survive being run twice | Decision 6 `**The step is re-entrant, and that is a contract**` + `## Edge cases` `Re-entering Phase 2.5 after a partial finalize` + DoD 6 |
| `is_type_of` injection alone cannot route a multi-type model | Decision 4's stamp contract + `## Test plan` + DoD 3 |
| a connection page has a second bound | `## Key glossary references` L38, Decision 9 lead-in, `## Edge cases` L423 and L428 |
| both root fields gained a deadline check | `## Edge cases` `Cooperative execution deadline` + `### Error shapes` + Decision 3 + DoD 3 |
| `relay.py`'s scope broadened to the whole typed-`GlobalID` contract | Decision 11's Source bullet |
| the default shape flipped to `"connection"` | every home swept above |
| never trust the client's claim of which type an id belongs to | `## Slice checklist` Slice 2 + Decision 3 |

Several private symbols appear **only** in the companion (`_check_nodes_result`, `_interleave`,
`check_deadline`, `DEFAULT_RELATION_SHAPE`, `_NODE_TYPE_HINT_ATTR`, `_decode_or_graphql_error`,
`reject_async_in_sync_context`). That is the correct direction, not a gap: in each case the spec
states the **contract behaviorally** and the companion adds the symbol that implements it. A builder
handed only the spec builds each one correctly.

---

## Step 5 — every artifact's deferred item, walked and dispositioned

Nothing new lands in this pass; the routing below is the pass's output.

| Source | Item | Disposition |
| --- | --- | --- |
| Slice 0 note 1 | `spec-033` foreign citation repair -> Slice 3 | **discharged** (Slice 3, one sentence + one link def, +230 bytes) |
| Slice 0 note 2 | two `.py` `Revision 7 PN` citations, named owner required -> Slice 3 | **discharged** (re-cited as `Decision 4` / `Decision 5`; both target contracts confirmed present) |
| Slice 0 note 3 | three `recorded at final verification` -> review round | **discharged this cycle** (review round M-2; population re-measured as **seven**, all removed) |
| Slice 0 note 4 | two companion post-ship notes for Slices 1-3 to discharge | **discharged** (Risks items 1 and 7; spec DoD item 1 and the uncapped Edge case both corrected) |
| Slice 1 note 1 | `docs/GLOSSARY.md` `## DjangoNodesField` "deliberately uncapped" | **routed onward**, catalog entry 1 |
| Slice 1 note 2 | pre-archive `docs/spec-032-…` prose paths -> Slice 3 | **discharged** (routed as five sites; measured population six sites / seven occurrences) |
| Slice 1 note 3 | A3 bucket correction on record in the companion | informational; no action owed |
| Slice 2 note 1 | three `.py` `"both"`-default comment sites -> Slice 3 | **discharged** (the routed three were **five**) |
| Slice 2 note 2 | `ItemType.properties` -> `CategoryType.properties` -> Slice 3 | **discharged** |
| Slice 2 note 3 | build plan's B7 names the wrong owning type | Worker 0's file; informational, corrected in Slice 2's evidence table |
| Slice 3 note 1 | `spec-033` `### Decision 9` dangling anchor, 5 sites | **routed onward**, catalog entry 3 |
| Slice 3 note 2 | nine `docs/spec-<NNN>` `.py` docstring paths for other specs | **routed onward**, catalog entry 4 |
| Slice 3 note 3 | degenerate `parametrize` id | **routed onward**, catalog entry 5 (with review-round L-2) |
| Slice 3 notes 4-5 | `BACKLOG.md` `stable_cursor_field` + missing `## Meta.cursor_field` glossary heading | **already carded in `KANBAN.md`**; deliberately NOT routed, re-confirmed here so the next audit does not re-route it |
| Review M-1 | `docs/GLOSSARY.md` `## Meta.relation_shapes` default claim | **routed onward**, catalog entry 2 |
| Review M-2 | seven chronology parentheticals | **applied this pass** |
| Review L-1 / L-2 / L-3 / L-4 / L-5 | | decided in writing in the review artifact; L-1+L-2 and L-5 routed, L-3 and L-4 rejected |

**Nothing found in a prior artifact should have landed in this pass rather than the catalog.** Every
open item names a file this cycle's maintainer-set scope forbids (`docs/GLOSSARY.md`, `TODAY.md`) or
an executable-byte edit the scope authorizes only on a code-gap finding — and across four slices and
one review round, **no code gap was found**.

---

## Step 6 — staged-anchor sweep (required, and recorded even though it is empty)

```
$ grep -rEn 'TODO\(spec-032|TODO-(ALPHA|BETA|STABLE)-032' . --exclude-dir=.git --exclude-dir=.venv
docs/SPECS/spec-032-full_relay-0_0_9.md:417            (prose: the anchor discipline, `TODO(spec-032 Slice 3)` as its worked example)
docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md:351   (a PRE-RENUMBER card id in a was-planned-as/shipped-as table; that `032` is today's `DONE-044-0.0.14`)
docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md:32,48,382 (companion prose recording that the discipline was adopted)
```

Restricted to shipped source, tests, and comments:

```
$ grep -rEn 'TODO\(spec-032|TODO-(ALPHA|BETA|STABLE)-032' . --include='*.py' --include='*.html' \
    --include='*.txt' --include='*.toml' --include='*.cfg' --exclude-dir=.git --exclude-dir=.venv
EXIT=1   (no matches)
```

**Zero staged anchors survive.** `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` were excluded per the
rule; none of the five hits above is in them anyway.

**The zero was proved to be a measurement, not an instrument failure.** The same grep form run for
any spec finds live anchors in `.py`:

```
$ grep -rEn 'TODO\(spec-[0-9]{3}' . --include='*.py' --exclude-dir=.git --exclude-dir=.venv | head -5
tests/test_connection.py:1588:# TODO(spec-033 Slice 1-2): root-connection no-regression fence. ...
tests/test_permissions.py:43:# TODO(spec-036 Slice 3): ...
tests/optimizer/test_extension.py:5342:# TODO(spec-035 Slice 3): ...
tests/optimizer/test_walker.py:4888:# TODO(spec-035 Slice 3): ...
tests/mutations/__init__.py:3:# TODO(spec-036 Slice 1): ...
```

A control that cannot fire reads exactly like a passing proof; this one fires.

---

## Cross-slice consistency of the reconciliation itself

The failure mode this pass exists to catch is not duplication but **contradiction between slices** —
Slice 1 owning the root-field half, Slice 2 the relation half, Slice 3 the cross-spec residue, each
internally consistent and jointly incoherent at the seam. Every contract crossing a slice boundary
was walked home by home.

**1. The `relation_shapes` default (Slice 2 owns; Slices 1 and 3 edited adjacent text).** Ten homes
read in full — `## Key glossary references`, `## Slice checklist`, `## Problem statement`,
`## Goals` goal 2, `## User-facing API` (prose **and** the code sample's inline comment), Decision 6
(lead-in, three shape bullets, the why-suppress paragraph), Decision 7 (the `None`-absent row and the
consumer-authored bullet), `## Edge cases`, `## Test plan`, `## Definition of done` item 6.
**One consistent telling in all ten**: `"connection"` is the default and removes the generated list;
`"both"` is the explicit opt-in that keeps it, row-bounded; `"list"` suppresses the connection. The
consumer-authored skip rule is stated **value-independently** in both the spec and the two `.py`
docstrings, which is what makes it survive the next default flip.

**2. The `nodes(ids:)` cap — the designated cross-slice seam.** Slice 1 rewrote the Edge-case entry
(`max_node_ids`, default 200, charged pre-decode); Slice 3 rewrote the sibling entry
(`relay_max_results` under `max_page_size`, default 100) and then went **back into Slice 1's entry**
to add the cross-reference. Read together at `HEAD` they state one contract: two deliberately
independent policy fields, so raising a page size never raises a batch size. Both defaults verified
against source (`resource_policy.py` `max_page_size: int = 100`, `max_node_ids: int = 200`). The
`### Error shapes` bullet Slice 1 added covers both rejections in one sentence and points at the Edge
cases section rather than restating either number — the correct shape, since a number restated is a
number that drifts. `grep -c uncapped` on the spec = **0**.

**3. The pk-coercion contract (Slice 1 owns, seven homes).** `### Error shapes`, Decision 5 (bullet +
two sub-bullets), `## Implementation plan`, `## Edge cases`, `## Test plan` (two bullets), DoD item 3.
All seven name the **id slot** — the concrete field behind `resolve_id_attr()` — and `to_python` then
`run_validators`. Zero surviving `model._meta.pk.to_python`-as-the-contract sites; the only
`model._meta.pk` mentions are the correct `"pk"` -> `model._meta.pk` mapping and the explicit
`not model._meta.pk` contrast in the Test plan.

**4. Every place `resource_policy` is named.** Six sites in the spec, three in the companion, all
spelled `resource_policy.py::ResourcePolicy.<field>` and all resolving through the single
`[resource-policy]` link definition. No second spelling, no second link def.

**5. The designed-redundancy cross-check, DoD against Decisions.** `## Definition of done` items 3 and
6 are the densest restatements in the file and were edited by Slices 1, 2 **and** 3. Read clause by
clause against Decisions 3/4/5/6/7/11: item 3 carries all five of Slice 1's additions (stamp, 1:1
override return, the second `SyncMisuseError` source, id-slot coercion, the deadline at the pre-decode
seam) and item 6 carries all of Slice 2's (default `"connection"`, `"both"` as opt-in, the resolver's
three arguments, re-entrancy, identity-safe teardown). **No clause contradicts its Decision and none
contradicts the other item.**

**Result: no cross-slice contradiction found.** No consolidation loop is owed, so no Worker 2 / Worker
3 dispatch is requested and the pass closes on its first iteration.

---

## Re-derived rather than accepted

### The byte-count chain closes to the byte

| Stage | spec | companion | `spec-033` |
| --- | --- | --- | --- |
| `HEAD` (measured `git show HEAD:<path> \| wc -c`) | **188,525** | did not exist | **173,810** |
| Slice 0 (rationale move) | 145,056 | 75,855 | — |
| Slice 1 (root-field surface) | 157,923 | 85,123 | — |
| Slice 2 (relation shapes) | 165,828 | 97,055 | — |
| Slice 3 (cross-spec residue) | 170,612 | 108,497 | 174,040 |
| Review round M-2 (this spawn) | **170,378** | 108,497 (untouched) | 174,040 (untouched) |

Every reported handoff number is reproduced by the file on disk today: `wc -c` gives 170,378 /
108,497 / 174,040, and `git show HEAD` gives 188,525 / 173,810. `174,040 - 173,810 = 230`, exactly
Slice 3's claimed `spec-033` delta. Net across the cycle: spec **-18,147 bytes (-9.6%)**, companion
**+108,497 net-new**, `spec-033` **+230**. Lines: spec 794 -> 710, companion 471.

The chain's shape is worth naming because it inverts mid-cycle: the move took 43,469 bytes out, then
three reconciliation slices put 25,322 back. **A residual cycle's spec gets smaller once and then
grows**, and the companion grows faster than the spec exactly when the finding is a reversal rather
than an addition (Slice 2: spec +7,905, companion +11,932).

### The citation census, re-derived and spot-checked

Instrument: a classifier over `docs/`, `django_strawberry_framework/`, `tests/`, `examples/`,
`scripts/` plus repo-root `.md`, asserted against **eight fixtures** — one per class plus the two
near-misses that broke earlier instruments (`Decisions 6/7` plural-slash, and
`docs/SPECS/spec-032-…` which must classify as contract, not pre-archive-path). 8/8 pass before any
number was believed.

**483 occurrences across 58 files: A-contract 154, B-chronology 24, C-pre-archive-path 18, D-identity
287.**

Reconciling to Slice 3's 369 rather than declaring a discrepancy: `-80` for
`bld-032-slice-3-cross_spec_residue.md` (64) and `bld-032-review-1-spec_diff.md` (16), both written
**after** Slice 3 measured; `-11` for repo-root `KANBAN.md`, outside Slice 3's declared walk roots;
`-29` for `docs/builder/DONE/`, which Slice 0 excluded as closed-cycle history. `483 - 120 = 363`, and
the residual **+6** is `docs/builder/worker-memory/` growth after the measurement. **The total is not
a stable quantity and never was** — more than half its population lives in per-cycle scratchpads that
the cycle itself writes, which is exactly why Slice 3 recorded the *classification* as the
deliverable. What is stable is the ratio: **~1% of a spec's inbound references are at risk in a
rationale move.**

**Class B (chronology) — the class the move breaks — is now empty outside its two legitimate homes.**
All 24 occurrences enumerated: **4** in the companion, which *is* the revision history and self-owns
them; **20** in `docs/builder/` per-cycle scratchpads (the build plan, Slices 0 and 3, the review
artifact) describing the finding, which `START.md` exempts and which close with the cycle. **Zero in
shipped source, zero in tests, zero in any sibling spec, zero in any standing doc.**

**Class C (pre-archive `docs/spec-032-…` paths) — 15 occurrences enumerated, and one is a new
finding.** 1 in the spec (Decision 1's deliberate survivor: the subject of a sentence about where the
file *was*, correct as written); 1 in the companion's own census write-up; 9 in per-cycle
scratchpads; **4 in `KANBAN.md` / `KANBAN.html`** — see the finding below. **Zero in `.py`**: Slice 3
repaired all three module docstrings and the sweep confirms it.

**Classification spot-checked, not accepted.** Over the `.py` tree the population is 56 occurrences —
**41 class-A, 15 class-D, zero class-B, zero class-C**. Eight class-A hits sampled at random and read
in context: every one names a real contract section (`Decision 8` ×3, `Decision 6` ×2, `Decision 7`,
`Edge cases`, plus a plural `Decisions 6/7` — the spelling that broke Slice 3's first classifier and
now classifies correctly). Every `Decision N` / `Goal N` citation into spec-032 from a sibling spec
was resolved against the spec's actual heading set: **0 unresolvable** (13 Decisions, 7 Goals present).

---

## The completeness question: what is missing?

Stated explicitly, because a pass that does not ask it reports its own coverage as complete by
construction. Worker 3 named two things it did **not** examine. Both are closed here rather than
routed.

**(a) The companion's eight `## Revision history` entries — verified structurally, never re-derived.**
Closed, after reframing the question into one that is both answerable and load-bearing. Re-deriving
eight authoring-era review passes against git history asks whether the spec's own account of its past
is accurate — unfalsifiable in practice and depended on by nobody. The property that *is* load-bearing
is **faithfulness of the move**: did the block arrive in the companion unchanged? Proved mechanically
against `git show HEAD:docs/SPECS/spec-032-full_relay-0_0_9.md`: the HEAD inline block is 31 non-blank
lines / 22,033 bytes carrying 8 `Revision N` entries; the companion's section carries **8** entries
and **27 of the 31 lines byte-identically**. The four that differ were diffed opcode by opcode and
differ **only** in a mandatory anchor conversion:

```
HEAD='(#edge-cases-and-constraints)'  COMP='[spec-032-edge-cases]'
HEAD='(#non-goals)'                   COMP='[spec-032-non-goals]'
HEAD='(#test-plan)'                   COMP='[spec-032-test-plan]'
HEAD='(#edge-cases-and-constraints)'  COMP='[spec-032-edge-cases]'
```

An in-page anchor **must** become a cross-file reference once the text lives in another file, so all
four differences are required by the move rather than introduced by it. The one companion-only line is
the new framing sentence. **Nothing was invented, nothing dropped, nothing reworded.**

**(b) Sibling specs other than `spec-033` were not swept.** Closed here. Every file under
`docs/SPECS/` was classified: **14 sibling files cite `spec-032`, 68 occurrences — 15 class-A contract
citations and 53 class-D bare identity mentions, with zero class-B and zero class-C.** The rationale
move therefore broke **nothing** in any sibling spec beyond the single `spec-033` site Slice 3
repaired, which is what "contract citations survive by construction" predicts and what an unrun sweep
could only have assumed. Files: `spec-004` (+ rationale), `spec-005-rationale`, `spec-008` (+
rationale), `spec-010` (+ rationale), `spec-014-rationale`, `spec-029-rationale`, `spec-030-rationale`,
`spec-033` (+ its terms CSV), `spec-034`, `spec-051`.

**(c) One boundary this pass crossed, recorded rather than hidden.** The census walk over `docs/`
initially included `docs/builder/worker-memory/`, so the classifier counted the `spec-032` token in
`worker-0.md` and `worker-3.md` (1 occurrence each). **No content was read or surfaced** — the script
emitted counts only, and the numbers appear here solely as the +6 reconciliation residue above — but
the forbidden-read rule is about the file, not the reading method, so the walk was re-scoped to
exclude `worker-memory/` for every subsequent measurement. Recorded because a boundary crossed
silently is one the next pass repeats.

---

## New finding this pass: `KANBAN.md` carries the same pre-archive path rot, and no census had it in scope

Not a contradiction between slices — a **gap between their census roots**, which is the same class of
miss one level up.

Slice 0's census grammar was `spec-032 Decision N` and missed the `Revision N PN` spelling. Slice 3
fixed the grammar and widened the population to 369 — but declared its walk roots as `docs/`,
`django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`. **The repository root was in no
slice's population**, so `KANBAN.md` was never swept for the pre-archive path class even though Slice
1 had already proved that a DB-generated closeout doc (`docs/GLOSSARY.md`) carries this card's
falsified claims.

Measured before calling it rot, per the standing rule: **`KANBAN.md` carries 17 `docs/spec-<NNN>`
prose spellings against 160 correct `docs/SPECS/spec-<NNN>` ones.** Of the 17, **four legitimately
name in-flight specs** not yet written (`057`, `058` ×2, `060`) — `docs/` *is* a working spec's correct
location. The other **13 name archived specs and resolve to files that do not exist**: `028` ×3,
`029` ×2, `030` ×2, **`032` ×2**, `033`, `034`, `035`, `045`. Every one was disk-checked; all 13 are
`MISSING`. `KANBAN.html` carries the same two `spec-032` occurrences (it renders the same card body).

Two of the 13 are **this card's own residue**, so they belong to this cycle's routing rather than to
someone else's. `KANBAN.md` / `KANBAN.html` are DB-generated and on the plan's do-not-touch list — the
fix is a `SpecDoc` / card-body DB edit re-rendered via `scripts/build_kanban_md.py` +
`scripts/build_kanban_html.py`, never a hand edit — so it is **routed, not taken**.

**The lesson, stated as a rule rather than an anecdote:** a census is bounded by its **roots** as well
as its **grammar**, and the roots are the half nobody re-derives because they look like configuration
rather than a claim. Slice 3 wrote its roots down, which is why this was findable; had they been
implicit, the gap would have been invisible.

---

## Notes for the final gate's deferred-work catalog

Six entries, each with a **named owner**. An item routed forward without one does not survive.

1. **`docs/GLOSSARY.md` `## DjangoNodesField` — the falsified "deliberately uncapped" claim.**
   Exact text: "The batch is deliberately uncapped in `0.0.9` (parity with both upstreams;
   request-size limiting belongs to the consumer's transport layer)." Falsified by
   `resource_policy.py::ResourcePolicy.max_node_ids = 200`, charged pre-execution against the `ids`
   argument. Source: Slice 1 `### Notes for Worker 1` item 1. **Owner: the final gate's
   `### Deferred work catalog`** -> maintainer follow-up (glossary-DB edit +
   `scripts/build_glossary_md.py` re-render).
2. **`docs/GLOSSARY.md` `## Meta.relation_shapes` — the falsified `"both"`-is-the-default claim.**
   Source: review round M-1. Worker 3's corrected sentence, to be used verbatim:
   > `Meta.relation_shapes` is a `dict[str, str]` with values `"list"` / `"connection"` / `"both"`
   > (`"connection"` is the implicit default since `0.0.14`): the default emits the connection alone
   > and suppresses the `list[T]` field, `"both"` is the explicit opt-in that keeps that list beside
   > it, and `"list"` suppresses the connection.

   **Entries 1 and 2 are siblings in one file** — the same card's falsified claims, in two entries of
   `docs/GLOSSARY.md`, which is DB-generated. **They must be discharged together**, in one DB edit and
   one re-render. Splitting them is how one gets fixed and the other survives; the file already
   contradicts itself (its `## Relay Node integration` entry states the `0.0.14` flip correctly),
   which is worse than either claim alone because a reader cannot tell which half is current. Same
   owner as entry 1.
3. **`docs/SPECS/spec-033-connection_optimizer-0_0_9.md` — `### Decision 9` in-page anchor dangling at
   five use sites.** Independently re-measured this pass: 5 broken, and it is the only anchor of this
   shape under `docs/`. Replace every
   `#decision-9--the-edgesnode-selection-helpers-consolidate-into-the-walker` with
   `#decision-9--the-edges--node--selection-helpers-consolidate-into-the-walker` (GitHub drops the
   code span's braces and hyphenates each remaining space, so the double hyphens are the resolving
   form). **The heading itself is correct and must not be changed.** Sites: the `Status:` line, the
   `## Slice checklist` Slice-1 entry, the `## Current state` selection-unwrap bullet,
   `### Decision 11`'s build-proper source bullet, `## Definition of done` item 2. Pre-existing at
   `HEAD` and `spec-033`-internal — **not** caused by this cycle's rationale move. Source: Slice 3
   note 1. **Owner: the final gate's `### Deferred work catalog`** -> `spec-033`'s own residual cycle.
4. **Stale `docs/spec-<NNN>` pre-archive paths naming archived specs — twenty-two occurrences across
   two homes.**
   (a) Nine in `.py` module docstrings: `018` ×4, `020`, `023`, `028` ×2, `030` (Slice 3 note 2).
   (b) **Thirteen in `KANBAN.md`** naming archived specs — `028` ×3, `029` ×2, `030` ×2, `032` ×2,
   `033`, `034`, `035`, `045` — plus the two `spec-032` occurrences mirrored in `KANBAN.html`
   (**this pass's finding**, above). Repair is mechanical (insert `SPECS/` after `docs/`), but
   `KANBAN.md` / `.html` are DB-generated and on the do-not-touch list, so the fix is a card-body DB
   edit plus both re-renders. Measured, not asserted: `.py` carries 26 correct spellings against 12
   stale; `KANBAN.md` carries 160 correct against 17 stale, of which 4 correctly name in-flight specs.
   **The `032` occurrences are this card's own residue and should be discharged with this cycle;
   the rest belong to their own specs' cycles.** **Owner: the final gate's
   `### Deferred work catalog`** -> maintainer follow-up.
5. **`tests/test_relay_connection.py` — two comment-layer items, one file, one touch.**
   (a) The `["both", "connection"]` parametrization feeding `::_shelf_books_connection_schema` is
   **degenerate**: the builder supplies `relation_shapes` only when `shape == "connection"`, so the
   `"both"` arm exercises the package default, which is `"connection"`. Fourteen test ids read
   `[both]` for rows that test no `"both"` shape. **Not a code defect** — no assertion is false and
   the pair still separates default resolution from explicit lookup — but the id is a claim, and
   fixing it changes executable bytes, which this cycle authorizes only on a code-gap finding.
   Suggested: rename the arm `"default"` with the builder's condition inverted, or add a third arm
   passing an explicit `{"books": "both"}`. (b) A comment reflow left the 13-character orphan line
   `# WITHOUT the` in the same file's section banner (review round L-2); cosmetic, `ruff format
   --check` and `check_trailing_commas.py --check` both pass over it. **Deliberately filed as one
   entry**: both live in `tests/test_relay_connection.py`, and one edit discharges both — filed
   separately, the cheaper one gets skipped. Sources: Slice 3 note 3, review round L-1 and L-2.
   **Owner: the final gate's `### Deferred work catalog`** -> maintainer follow-up.
6. **`TODAY.md` — the relation-as-Connection paragraph leads with the retired default.** It opens
   "gains a paginated `<field>Connection` sibling alongside the plain `list[T]` field" and corrects
   itself four sentences later ("Since `0.0.14` the default is the connection **alone**"). Weaker than
   entries 1-2 because the paragraph is self-consistent by its end, but a reader who stops at the
   first sentence gets the retired contract. `TODAY.md` is on the do-not-touch list. Source: review
   round L-5. **Owner: the final gate's `### Deferred work catalog`** -> maintainer follow-up.

**Deliberately NOT routed, so the next audit does not re-raise them:**

- `BACKLOG.md`'s `stable_cursor_field` entry describing a shipped feature in the future tense, and the
  missing `## Meta.cursor_field` glossary heading. **Already carded** — `KANBAN.md` carries both by
  name inside one undecided "where is the shipped keyset feature documented" bullet, alongside the
  absent CHANGELOG entry. Re-derived this cycle rather than inherited (Slice 3 note 4). Routing them
  again would create a duplicate.
- Review round L-3, the six companion `### Justification` bodies opening lowercase. **Rejected, with
  reason** (the rationale file is append-only during the build, and byte-verbatim is the property that
  makes the move auditable). Not routed, because doing it later carries the identical cost — leaving
  it open invites a future pass to "fix" a load-bearing property.
- Review round L-4, `## Current state`'s "as of this writing". **Rejected, with reason** (it scopes a
  section rather than timestamping an edit, and three slices' case-(c) gradings rest on it).

---

## Verification

**1. Glossary gate — exit 0, unchanged term count.**

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-032-full_relay-0_0_9.md
OK: 40 terms - all have glossary entries and at least one spec link.
EXIT=0
```

Same 40 terms Slices 0-3 and the review round measured. Expected: the M-2 cuts removed no
glossary-linked term.

**2. Citation gate — exit 0.**

```
$ uv run python scripts/check_citations.py
OK: 815 citations resolve (731 in 431 .py files, 84 in KANBAN.md).
EXIT=0
```

Identical to the review round's independent run, which is the expected result of a pass that changed
no `.py` file and reflowed no line carrying a rule-27 citation.

**3. Markdown scaffold gate — exit 0.**

```
$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-032-full_relay-0_0_9.md \
    docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md
EXIT=0
```

**4. Anchor / link-definition sweep — and the checker was proved failable in BOTH directions before
any zero was trusted.**

The slugger is asserted against **five known-good** headings and **two known-bad** renderings, and
`sys.exit(2)`s on a fixture mismatch rather than reporting zero problems. The three traps this cycle
has already paid for are each covered by a fixture: ` — ` renders as **two** hyphens (a
run-collapsing `\s+` substitution reports a false dangling on every `decision-N--title` anchor); `_`
is **not** emphasis and is never stripped (`metarelation_shapes-and-the-default`); and code-span
content is **unwrapped before** emphasis stripping, so `` `edges { node }` `` slugs to
`the-edges--node--selection-helpers`, which the negative fixture requires the checker to prefer over
the brace-collapsed spelling.

```
slugger fixtures: 7/7 pass

=== docs/SPECS/spec-032-full_relay-0_0_9.md: headings=44 defs=100 in-page=136 ref-uses=467 -> 0 problem(s)
=== docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md: headings=57 defs=62 in-page=42 ref-uses=130 -> 0 problem(s)
=== docs/SPECS/spec-033-connection_optimizer-0_0_9.md: headings=39 defs=75 in-page=158 ref-uses=315 -> 5 problem(s)
    broken in-page anchor #decision-9--the-edgesnode-selection-helpers-consolidate-into-the-walker   (x5)
```

The `spec-033` result reproduces Worker 3's independently and is catalog entry 3.

**Failability control.** A copy of the spec outside the repo was mutated three ways — one in-page
anchor repointed at a nonexistent heading, the `[keyset]` definition retargeted at a nonexistent path,
and an undefined `[no-such-ref]` use introduced. The checker named all three:

```
broken in-page anchor #decision-6--nope
undefined ref [no-such-ref]
def [keyset] -> missing path .../django_strawberry_framework/NOPE.py
```

Clean copy 100 problems -> mutant 102. The delta is +2 rather than +3 because the `[keyset]` mutation
**replaces** an entry the clean copy already reports. Those 100 baseline entries are an artifact of the
copy's location — every relative definition resolves outside the repo from there — and are named here
because an unexplained count difference between a clean run and a failability run is precisely how an
instrument bug gets read as a finding. In-repo the same files report 0.

**5. Lint / format, read-only (never `--fix` in this pass).**

```
$ uv run ruff format --check .   -> 434 files already formatted        EXIT=0
$ uv run ruff check .            -> All checks passed!                 EXIT=0
```

**6. Byte counts for every file this spawn changed.**

| File | Before | After | Delta |
| --- | --- | --- | --- |
| `docs/SPECS/spec-032-full_relay-0_0_9.md` | 170,612 | **170,378** | **-234** (the seven M-2 cuts) |
| `docs/builder/bld-032-review-1-spec_diff.md` | 37,325 | **47,687** | +10,362 (`## Final verification (Worker 1)` appended; Worker 3's findings text untouched) |
| `docs/builder/bld-032-integration.md` | did not exist | this file | net-new |
| `docs/builder/worker-memory/worker-1.md` | 5,945 | see below | untracked scratch |

Unchanged and verified so: `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` (108,497),
`docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (174,040), all seven `.py` files, and every
closeout / agentflow doc.

**7. No `pytest` was run and no `--cov*` flag was used anywhere in this pass.** Nothing was committed
and no branch was created.

**8. Working tree.** `git status --short` shows the two modified specs, the seven comment-only `.py`
files, this cycle's untracked artifacts and build plan, and the maintainer's concurrent untracked
`0_0_14.md` — which was neither read as instruction nor touched. `docs/GLOSSARY.md`, `KANBAN.md`,
`KANBAN.html`, `CHANGELOG.md`, `TODAY.md`, `README.md`, `GOAL.md`, `docs/TREE.md`, `docs/README.md`,
`BACKLOG.md` and `examples/fakeshop/db.sqlite3` are all **absent** from the list. Nothing was reverted.

---

### DRY analysis

**Helper inventory checked. Not applicable to source, and deliberately so:** this pass writes no
Python and proposes no helper, and the whole cycle changed zero executable bytes. Recorded rather than
skipped so a later pass can see the question was asked. The **prose** DRY question — one contract, one
vocabulary, one home — is the substituted form and is answered in `### Step 3 analogue` and
`### Step 4 analogue` above. The one prose-duplication hazard a reconciliation cycle actually carries
is the **partial fix** (one home corrected, four left stating the old claim), and every contract
crossing a slice boundary was walked home by home to rule it out.

Before recommending any consolidation, `worker-1.md` requires grepping the candidate's **readers**.
Applied to the one live duplication candidate — the `docs/GLOSSARY.md` pair — the readers are real
(both entries are consumer-facing capability documentation and the file already contradicts itself),
so the answer is repair-together rather than delete-and-trim. It is routed rather than taken only
because the file is DB-generated and out of scope.

### Test additions / updates

None. This pass adds no source and no test, and runs no `pytest` per `AGENTS.md` and `worker-1.md`.

### Spec slice checklist (verbatim)

Not applicable. The integration pass is defined by `BUILD.md`, not by an entry in the spec's own
`## Slice checklist` (which carries the seven shipped build slices 1-7). There are no verbatim
sub-checks to copy, tick, or audit. Recorded explicitly rather than omitted, so the absence reads as
a decision.

### Implementation discretion items

None. Every choice in an integration pass is the custodian's; nothing was delegated.

### Summary

Four slices and one review round reconciled roughly 60 prose sites across one spec and produced a
108,497-byte companion, and **the four halves do not contradict each other**. The four contracts that
cross a slice boundary — the `relation_shapes` default (ten homes), the `nodes(ids:)` cap seam where
Slice 1 owns one entry and Slice 3 the sibling, the id-slot pk-coercion contract (seven homes), and
every `resource_policy` naming — each tell one consistent story at `HEAD`, and the densest
designed-redundancy restatements (DoD items 3 and 6, edited by three different slices) agree clause
for clause with the Decisions they restate. The one-way dependency holds in both directions that
matter: 13/13 Decisions keyed spec->companion and 13/13 companion->spec, and no normative or
implementation-relevant sentence lives only in the companion (45 normative-marker lines swept, every
live contract traced to a spec home). The staged-anchor sweep is **empty in shipped source, tests and
comments**, on a grep proved to fire by finding live `TODO(spec-033/035/036 …)` anchors in the same
tree. The byte chain closes to the byte at every handoff (188,525 -> 170,378, `-9.6%`; companion
108,497 net-new; `spec-033` `+230`), and the citation census re-derives with its **chronology class
empty outside the self-owning companion and this cycle's own scratchpads** — the exact property a
rationale move puts at risk.

Both of Worker 3's self-declared blind spots are **closed rather than routed**: the companion's eight
revision entries are proved byte-faithful to `HEAD` (27 of 31 lines identical; the 4 differences are
mandatory in-page-to-cross-file anchor conversions), and every sibling spec was swept (14 files, 68
occurrences, **zero** chronology and **zero** pre-archive-path citations — the move broke nothing
beyond the one `spec-033` site Slice 3 repaired). **One new finding surfaced**, and it is a census
**root** gap rather than a grammar gap: no slice's walk included the repository root, so `KANBAN.md`'s
13 stale `docs/spec-<NNN>` paths — two of them this card's own — were never in any population, in a
file Slice 1 had already implicated by class. Six items are routed to the final gate's catalog, each
with a named owner and the two `docs/GLOSSARY.md` entries filed as one inseparable pair; four are
deliberately not routed with the reason stated. No cross-slice defect was found that this pass could
not close or route, so no consolidation loop is requested and `Status: final-accepted` is set.

### Spec changes made (Worker 1 only)

**None in this pass.** The seven M-2 removals this spawn made are recorded under review round 1's
`## Final verification (Worker 1)` section, where they belong; repeating them here would be the
double-home bookkeeping this cycle exists to remove. No source or test file was edited. No sibling
spec was edited. The companion was not edited. No closeout or agentflow doc was edited.

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
