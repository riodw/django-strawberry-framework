# Build: Cross-slice integration pass (spec-023 multi_db)

Spec reference: `docs/SPECS/spec-023-multi_db-0_0_7.md` (whole file) and its companion `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md`
Status: final-accepted

Run by Worker 1 per `docs/builder/BUILD.md` `## Cross-slice integration pass`. This cycle's entire diff is Markdown and CSV: `docs/SPECS/spec-023-multi_db-0_0_7.md`, `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md` (new, untracked), and `docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv`. No source, no tests, no Python of any kind.

## Required reading discharged

Standing docs (`W1` column of `docs/builder/BUILD.md` `## Required reading per worker`): `AGENTS.md`, `START.md`, `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, `docs/builder/worker-1.md`, `GOAL.md`, `docs/GLOSSARY.md`, `CHANGELOG.md`. Cycle files: the build plan `docs/builder/build-023-multi_db-0_0_7.md`, the spec, the rationale, the terms CSV, and **both** prior artifacts in slice order — `docs/builder/bld-slice-1-023-rationale_extraction.md`, `docs/builder/bld-slice-2-023-spec_reconciliation.md`. Memory: `docs/builder/worker-memory/worker-1-023.md` read first, appended at the end. `docs/builder/worker-memory/worker-1.md` (the concurrent cycle's notebook) and the other workers' memory files were neither read nor written.

## Spec status-line re-verification (per-spawn obligation)

`docs/SPECS/spec-023-multi_db-0_0_7.md:1-6` read this spawn. Title, `Target release: 0.0.7 (per the KANBAN.md card DONE-023-0.0.7)`, `Status: shipped (0.0.7); implementation complete and committed. … Its deliberative layer … lives in [spec-023-multi_db-0_0_7-rationale.md]`, `Owner:`, `Predecessors:`. All five describe the build's current state; the `Status:` line names the rationale companion Slice 1 created, and the `Predecessors:` line's `[Decision 9](#decision-9--joint-007-cut)` uses the corrected slug. **No edit required.**

## Preconditions, applied honestly to a docs-only cycle

`docs/builder/BUILD.md` `## Cross-slice integration pass` lists six preconditions. Three are shaped for a code build and are recorded as non-applicable with the reason, not silently skipped.

| # | Precondition | Disposition |
|---|---|---|
| 1 | Read every prior `bld-slice-*` artifact in slice order | **Done.** Both read end to end; findings from both are walked below. |
| 2 | Confirm `scripts/review_inspect.py` ran, or was skipped with a reason, for every Python file with review-worthy logic the build touched | **Non-applicable — the empty set.** The build touched zero Python files. `git status --short` filtered to `*.py` returns nothing; the cycle's whole diff is two `.md` and one `.csv`. There is no file for the helper to inspect, so this is a vacuous rather than a waived obligation. (Worker 0 ran a pre-flight smoke of the helper on `django_strawberry_framework/types/resolvers.py`, exit 0, recorded in the plan's `## Pre-flight outcome`.) |
| 3 | Compare **Repeated string literals** across shadow overviews | **Non-applicable.** No shadow overview exists because no Python file was inspected. The Markdown analogue — material restated across the spec/rationale pair — *is* applicable and was run instead; see `### Cross-file duplication`. |
| 4 | Compare **Imports** across shadow overviews for one-way dependency direction | **Non-applicable.** No Python surface, therefore no import graph. The Markdown analogue is the two files' cross-reference direction, which was resolved in both directions; see `### Cross-file anchor and reference resolution`. |
| 5 | Walk every accepted artifact's `What looks solid` / `DRY findings` for deferred follow-up | **Done.** Neither slice artifact carries a Worker 3 review block (no Worker 3 was dispatched — the plan authorizes dispatch only if a slice needs a code change, and none did), so the sections walked are their `### Handed to Slice 2`, `### Notes for the next pass (integration)`, `### Deliberately not changed`, and `### Spec changes made (Worker 1 only)` blocks. See `### Deferred follow-up walked`. |
| 6 | Sweep the whole tree for staged anchors naming this build's spec or card | **Done, clean.** See `### Staged-anchor sweep`. |

## Staged-anchor sweep (step 6, verbatim command)

```shell
grep -rEn 'TODO\(spec-023|TODO-(ALPHA|BETA|STABLE)-023' . --exclude-dir=.git --exclude-dir=.venv
```

**0 matching lines, before any exclusion.** The `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` carve-out never had to be applied — there is nothing to exclude.

The instrument is proven live rather than assumed: the same regex relaxed to `TODO\(spec-[0-9]+` returns hits across the tree (`tests/test_connection.py` `TODO(spec-033`, `tests/test_permissions.py` and `tests/mutations/__init__.py` `TODO(spec-036`, `tests/optimizer/test_extension.py` and `tests/optimizer/test_walker.py` `TODO(spec-035`, plus spec and `docs/dry/` sites). A sweep that finds other cards' anchors and none of `023`'s is a measurement, not a silent regex failure.

No finding. Nothing routes back to a slice.

## Cross-file anchor and reference resolution

Slice 2 renamed Decision 7's heading and rewrote 15 anchor uses across the pair. That is the shape that leaves a dangling key, so every `#fragment` was re-resolved in both directions this pass with a resolver, not by spot-checking.

Method: a scratch script (outside the repo) that strips fenced blocks and inline code spans, computes each file's heading slugs, then checks (a) every in-page `](#…)`, (b) every `[text][ref-id]` against the file's definitions, (c) every definition against its used-set, (d) every definition path against disk, and (e) every cross-file `#fragment` against the **target** file's real headings.

Result after this pass's edits, both files:

```
=== docs/SPECS/spec-023-multi_db-0_0_7.md ===
in-page unresolved: none
used-not-defined: none
defined-not-used: none

=== docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md ===
in-page unresolved: none
used-not-defined: none
defined-not-used: none
```

No `MISSING PATH` and no `BAD FRAGMENT` line was emitted for either file.

The dotted-version slug trap holds: `### Decision 9 — Joint \`0.0.7\` cut` slugs to `decision-9--joint-007-cut`, and `grep -o '#decision-9--joint-0_0_7-cut' docs/SPECS/spec-023-multi_db-0_0_7.md | wc -l` returns **0** — all seven of Slice 2's rewrites survive.

Decision-heading correspondence is 1:1 and exact. The rationale's nine `## Decision N — …` headings reproduce the spec's nine `### Decision N — …` heading texts character for character, Decision 7's new title included, so the two files' anchors mirror. The spec carries nine `Rationale companion —` pointers (`grep -c 'Rationale companion'` -> 9), one per Decision.

### Symbol-qualified `#"substring"` citations

`AGENTS.md`'s citation form is only as good as the substring, and a `#"substring"` breaks on reflow as well as reword. Every one was resolved against the cited file.

- Spec: **47** citations. **1 broken**, fixed this pass (below).
- Rationale: **23** citations before this pass, **22** after. **1 broken**, left with a recorded reason (below).

## Findings

### F1 (fixed here) — five of the rationale's Slice-1 forward pointers were falsified by Slice 2

Slice 1 wrote its record while Slice 2 was still ahead of it, so it correctly used forward-pointing language ("reconciliation is Slice 2's", "correcting them is Slice 2's", "recorded here for Slice 2"). Slice 2 then did all of it and appended its own record **without closing those pointers**. The result is the precise defect `docs/builder/worker-1.md` `## Review-round custody` names: "A half-reconciled spec is worse than an un-updated one: the reader cannot tell which half is current." Five sentences told a reader that spec defects were still live which are demonstrably not.

Each was re-derived against the current spec before being touched — a claim about the spec is not a measurement of it:

| Rationale site | Claim as written | Re-derived against the spec | Instrument |
|---|---|---|---|
| Intro paragraph | "Slice 2 … appends to this file and had NOT run when this text was written" | `## Slice 2 — spec reconciliation` is present at line 351 of the same file | `grep -n '^## Slice 2'` |
| `## Decision 1` -> `### Claims this Decision may no longer make` | "The spec's prose still lags — reconciliation is Slice 2's" | 0 occurrences of the active path `docs/spec-023-multi_db-0_0_7.md` in the spec | `grep -c 'docs/spec-023-multi_db-0_0_7\.md'` -> 0 |
| `## Decision 3` -> `### Claims this Decision may no longer make` | "Adding the qualifier is Slice 2's, not this pass's" | the plan-time/fetch-time qualifier is present at all seven sites Slice 2 names | read at `### Decision 3` axis 3, `## Key glossary references`, `## Problem statement`, `## Goals` 1(c), `## User-facing API`, `## Edge cases and constraints`, `## Risks and open questions` |
| `## Deliberation moved from non-Decision sections`, CSV bullet | "The CSV's surviving `notes` column **still carries** two `rev2 H2` / `rev2 H6` attributions" | 0 | `grep -oE 'rev[0-9]' docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv \| wc -l` -> 0 |
| `## Claims the spec may no longer make`, preamble + item 4 | "Item 4 is a live inconsistency this pass observed and did not fix"; item 4 cites `## Risks and open questions` #"the test in Slice 1 (g) sets `root._state.db`" | 0 occurrences of `(g)` in the spec, and the cited substring no longer exists there — a **dangling `#"substring"` citation**, not merely stale prose | `grep -oE '\(g\)' \| wc -l` -> 0 |

All five rewritten to state the closed outcome. **No moved deliberation was touched**: every edit lands in a sentence Slice 1 authored as its own process scaffolding, never inside a `### Justification (moved from the spec)` or `### Alternatives considered (and rejected)` block or the `## Revision history`. `docs/builder/worker-1.md` rule 4's append-only discipline protects the moved record from rewriting; a forward pointer to a slice that has since run is neither moved text nor deliberation, and rule 2 ("delete — do not move — prose the current decisions have falsified") points the same way.

While closing item 4 the letter population was re-derived rather than inherited. Slice 2 reported "8 letter sites total". The actual population of letter references in the spec is **40** occurrences (`grep -oE '\([a-g]\)' | wc -l`), distributed `(a)` 8, `(b)` 7, `(c)` 7, `(d)` 6, `(e)` 5, `(f)` 7, `(g)` **0**. Slice 2's instrument was a four-alternative phrase grep (`'test (f)\|test (g)\|(f) consumer\|Slice 1 (g)'`) — the "long grep phrase samples a claim's vocabulary rather than establishing its population" trap `docs/builder/BUILD.md` `## Claims are proven mechanically` names. Slice 2's **outcome** is nonetheless correct: all 40 references were read at their nine distinct lines (36, 88, 211, 212, 374, 375, 476, 479, 497) and every one resolves to the shipped six-test a-f layout — (e) = the strictness test in `tests/types/test_resolvers.py`, (f) = the consumer-`Prefetch` test in `tests/optimizer/test_multi_db.py`. Coherent; no further edit. The corrected figure is now in the rationale.

### F2 (fixed here) — the rationale carried a stale `.using(` count contradicted by its own later section

`## Decision 2` -> the **Time-scope warning on the second bullet** said `.using(` "now appears across ten package modules". `### Populations measured for this pass`, ~200 lines below in the same file, says 9 call sites out of 13 mentioning modules. One file asserting two different populations of the same thing is this pass's clearest cross-slice DRY-of-fact defect.

Re-derived rather than copied from either: `grep -rl '\.using(' django_strawberry_framework/ | wc -l` -> **13** modules, `grep -rn '\.using(' django_strawberry_framework/ | wc -l` -> **32** occurrence lines. The four modules that mention the token only in docstrings or error strings were read line by line and confirmed: `utils/querysets.py` (6 lines, all docstring/`f"…"` message), `optimizer/lateral_fetch.py` (2, both docstring), `optimizer/nested_fetch.py` (2, both docstring), `optimizer/nested_planner.py` (2, both docstring/comment). **13 mention, 9 call.** Slice 2's figures stand; Slice 1's "ten" does not.

The same warning's router-call claim was re-derived and is correct: `grep -rn 'router\.db_for_' django_strawberry_framework/` returns 7 lines, of which 3 are prose (`consumers.py:743`, `optimizer/nested_planner.py:104`, `utils/write_transaction.py:152` docstrings) and **4 are calls** — `types/resolvers.py:135`, `utils/write_transaction.py:160`, `utils/write_transaction.py:689`, `utils/permissions.py:288`. The warning's `django_strawberry_framework/utils/permissions.py` path was checked against the decoy: both `django_strawberry_framework/permissions.py` and `django_strawberry_framework/utils/permissions.py` exist, and the `db_for_read` call is in the `utils/` one. The citation is right.

The warning now states 4 call sites and the 9-of-13 split explicitly.

### F3 (fixed here) — a broken `#"substring"` citation in the spec's `## Doc updates`

`docs/TREE.md #"tests/optimizer/"` does not resolve: `docs/TREE.md` renders the tests tree with bare directory nodes, so the literal `tests/optimizer/` appears nowhere in it (`grep -c 'tests/optimizer/' docs/TREE.md` -> 0). **Pre-existing at HEAD** — `git show HEAD:docs/SPECS/spec-023-multi_db-0_0_7.md | grep -c 'docs/TREE.md #"tests/optimizer/"'` -> 1 — so neither slice introduced it, but the sentence is live contract text in a file this cycle owns and the pass that finds it is the pass that fixes it.

Rewritten to `docs/TREE.md #"Package tests for optimizer plans"`, which resolves (`docs/TREE.md:516`, the `tests/` tree's `optimizer/` node comment). The companion citation in the same bullet, `docs/TREE.md #"examples/fakeshop/test_query/"`, was checked and **does** resolve (4 occurrences); left alone.

### F4 (fixed here) — seven duplicate reference-id pairs in the rationale's link block

The rationale defined two ref-ids for each of seven identical targets: the short `[spec-023-dN]` form used by Slice 1's Decision entries and Slice 2's append, and a long `[spec-023-decision-N--<full-slug>]` form used only inside the moved `## Revision history`. Measured with `grep -E '^\[[^]]+\]: ' | awk '{print $2}' | sort | uniq -c | awk '$1>1'` -> 7 targets with 2 definitions each. The spec's own block had none.

Two ids for one target is redundancy `START.md`'s convention gains nothing from, and it doubles the rewrite cost of the next heading rename — the exact cost Slice 2 just paid 15 times. Consolidated onto the short form: **28 uses rewritten** (d1 3, d2 2, d3 9, d5 3, d6 7, d7 3, d9 1), each replacement asserting its own occurrence count, and the seven orphaned definitions removed. Only the link scaffolding changed; no sentence of moved text was reworded, which is the same content-preserving class of edit Slice 1 and Slice 2 already made to ref-ids and anchors inside moved blocks. Post-edit the duplicate-target query returns empty for both files and the full resolver re-run is clean.

### F5 (recorded, deliberately not fixed) — a broken `KANBAN.md` citation inside moved-verbatim text

`## Decision 9` -> `### Justification (moved from the spec)` carries `[KANBAN.md][kanban] #"The last \`0.0.7\` card to ship owns the version bump"`. That substring is absent from the current `KANBAN.md` and **also absent at HEAD** (`git show HEAD:KANBAN.md | grep -c 'owns the version bump'` -> 0), so it was already dead when Slice 1 moved the block.

Left in place, for three reasons that compound: the block is moved-verbatim deliberation and rewriting it is what `docs/builder/worker-1.md` rule 4's append-only discipline forbids; `KANBAN.md` is DB-rendered (`scripts/build_kanban_md.py`) and on this cycle's do-not-touch list, so the locator cannot be repaired from the target side either; and the sentence's substance survives independently — the joint-cut policy it quotes is stated normatively in the spec's `### Decision 9` and its true source, `docs/SPECS/spec-020-list_field-0_0_7.md` Decision 10, is named in the same sentence. Carried to the deferred-work catalog in `docs/builder/bld-final-023.md` rather than patched.

### F6 (fixed here) — `### Decision 3`'s out-of-scope lead-in contradicted the paragraph Slice 2 inserted above it

Slice 2 added a closing paragraph to `### Decision 3` absorbing D6's `_visible_related_object` alias re-pin, placed between the four-axis list and the out-of-scope list. The paragraph is careful and ends "The alias comes from the row, never from a plan — which is why none of the four axes needs a clause about it" — so the re-pin is contract, and deliberately not a fifth axis. The very next line then read **"Anything outside these four axes is out of scope for the contract:"**.

Read in sequence, the spec described a behavior as contract and then declared everything of that description out of scope. Under `docs/builder/BUILD.md` `## Cross-slice integration pass`'s "a contract the spec states must not be contradicted" this is the one live spec-internal contradiction the pass found, and it exists only because a new paragraph landed between two sentences that used to be adjacent — precisely the seam a single-slice review cannot see.

Fixed by scoping the lead-in to what it actually introduces: **"Beyond the four axes and the alias-late principle they rest on, the following are out of scope for the contract:"**. The four enumerated out-of-scope items (cross-shard joins, multi-shard aggregates, routing policy, `default_database` / preferred-shard selection) are unchanged.

Measured while checking this: `grep -o 'four axes'` -> **6** occurrences in the spec; `grep -oi 'five axes\|fifth axis'` -> **0**. The load-bearing "four axes" framing shared with the shipped `docs/GLOSSARY.md` entry and `CHANGELOG.md` bullet is intact.

### Cross-file duplication (precondition 3's Markdown analogue)

The rationale is the deliberative layer, the spec is the contract; a passage restated in both is this cycle's DRY defect. Two instruments, both run over the pair with fenced blocks and reference-link syntax stripped:

- **Exact long-sentence overlap** (sentences >= 90 characters, present verbatim in both files): **0**.
- **Word-shingle overlap** at n=14: 38 shared runs, longest **33 words**. Every one was read. They fall into three benign classes: link-definition-block tails that normalize to the same token sequence; the four out-of-scope items (`first class sharding aware planning cross shard joins automatic shard selection based on fk multi shard aggregates`), which the spec states as contract and the rationale quotes when recording why the boundary moved; and short mechanism restatements the rationale needs verbatim to say what a Decision may no longer claim (the `_check_n1` inspection list, the `FieldError` deferred-and-traversed message).

No passage lives in both files. **No DRY finding.**

### Deferred follow-up walked (precondition 5)

Every item in Slice 1's `### Handed to Slice 2` was re-derived against the current tree rather than accepted from Slice 2's report:

| Handed item | Status now | Instrument |
|---|---|---|
| D1-D13 open (D13 discharged by Slice 1) | all closed by Slice 2; D14-D20 added and closed | per-finding, below and in `### Spec changes made` |
| D1's surviving half in `## Current state` bullet 1 | closed; the grep claim is gone, the four call sites are named symbol-qualified | read at `## Current state` |
| D5's null-FK bullet in `## Edge cases and constraints` | closed; all three pre-router exits named | read at `## Edge cases and constraints` |
| `#decision-9--joint-0_0_7-cut` broken at 2 sites | closed; the real population was 7, all rewritten | `grep -o '#decision-9--joint-0_0_7-cut' \| wc -l` -> 0 |
| letter drift wider than D12 stated | closed; population re-derived as 40 refs, `(g)` -> 0 | `grep -oE '\([a-g]\)'` |
| terms CSV carries two rev attributions | closed | `grep -oE 'rev[0-9]'` on the CSV -> 0 |
| rationale is append-only from here | honored; this pass appended nothing to the moved record and edited only Slice 1's own forward pointers, F1/F2/F4 above | — |

Slice 2's `### Notes for the next pass (integration)`, all four items:

1. *"The integration pass should confirm the build plan's dispatch note still says"* Worker 2 must never be handed the rationale. **Confirmed.** `docs/builder/build-023-multi_db-0_0_7.md` `## Cycle shape` still reads "Workers 2 and 3 are dispatched only if a slice turns out to need a **code** change", and `docs/builder/BUILD.md` `## Required reading per worker` still marks the rationale row `**never**` for W2. Neither was edited by this pass — the plan is Worker 0's file and `BUILD.md` is closeout-excluded this cycle.
2. *`## Implementation plan`'s line-delta table checked and deliberately left.* Re-read; the reasoning holds (a planning estimate in the plan record is not a claim about HEAD, and the shipped delta is not one number). Concurred, no edit.
3. *Every `- [ ]` checkbox left unticked.* Confirmed as the house convention; the `Status:` line is source of truth for a shipped card. No edit.
4. *No code change required and none made.* Independently confirmed: `git status --short` filtered to `*.py` is empty, and this cycle's whole diff is the three doc files.

### What looks solid

- **The Decision 7 rename was carried through completely.** The riskiest structural change in the cycle, and the resolver finds no residue: 0 uses of the pre-rename anchor in either file, the rationale's own heading moved with it, `[rationale-d7]` and `[spec-023-d7]` both resolve, and `[test-library-api]` is removed from the spec (orphaned there) while still defined and used in the rationale, which is exactly right for a file that records the superseded posture.
- **The GLOSSARY four-axis constraint was respected without weaseling.** `docs/GLOSSARY.md` is outside the writable set and states four axes flatly. The spec absorbs D2's fetch-time threading as a refinement of axis 3 and D6's `_visible_related_object` re-pin as an instance of the same principle. 6 occurrences of "four axes", 0 of "five axes" / "fifth axis". (The insertion did leave one contradiction at its seam — F6 — but the framing itself never claims five.)
- **No chronology leaked into the spec.** `grep -oE 'rev[0-9]' docs/SPECS/spec-023-multi_db-0_0_7.md | wc -l` -> **0**, and 0 occurrences of `WIP-ALPHA-019-0.0.7`. The spec reads as a current contract.
- **`check_spec_glossary` never regressed across three passes.** `OK: 18 terms` at pre-flight, at Slice 1's close, at Slice 2's close, and again this pass — through a rationale move, a CHANGELOG-pin rewrite, and a Decision rename, each of which could have dropped a term's only spec link.

## No consolidation dispatch

`docs/builder/BUILD.md` `## Cross-slice integration pass` closes by routing DRY opportunities to Worker 0 for a Worker 2 consolidation pass. None is needed: F1-F4 and F6 were confined to the spec, the rationale, and their link blocks — Worker 1's own writable set — and were fixed in this pass. F5 is a decided non-fix. No finding requires a code change, so no Worker 2 or Worker 3 dispatch is requested and no re-loop is opened.

## Spec changes made (Worker 1 only)

| File / section | Change | Reason | Finding |
|---|---|---|---|
| rationale, intro paragraph | "Slice 2 … appends to this file and had NOT run when this text was written" -> names the appended `## Slice 2 — spec reconciliation` section and states that the Slice 1 forward pointers are closed there | The sentence told a reader the reconciliation record does not exist, in a file whose own contents list it | F1 |
| rationale, `## Decision 1` -> `### Claims this Decision may no longer make` | "The spec's prose still lags — reconciliation is Slice 2's" -> states that Slice 2 re-pointed the prose, with the measured 0 occurrences of the active path | Asserted a live spec defect that has 0 occurrences | F1 |
| rationale, `## Decision 3` -> `### Claims this Decision may no longer make` | "Adding the qualifier is Slice 2's, not this pass's" -> points at `### D2 — axis 3 is alias-LATE, not alias-absent` and states the seven sites landed | Same shape | F1 |
| rationale, `## Deliberation moved from non-Decision sections`, terms-CSV bullet | "still carries two `rev2 H2` / `rev2 H6` attributions … recorded here for Slice 2" -> past tense plus the measured 0 | Same shape | F1 |
| rationale, `## Claims the spec may no longer make`, preamble | "Item 4 is a live inconsistency this pass observed and did not fix" -> item 4 was live when Slice 1 recorded it and was closed by Slice 2; all four absent from the spec | Same shape | F1 |
| rationale, `## Claims the spec may no longer make`, item 4 | Rewrote to past tense; replaced the dangling `#"the test in Slice 1 (g) sets \`root._state.db\`"` citation with a `[…][spec-023-risks-and-open-questions]` section reference; added the re-derived population (0 `(g)`, 40 `(a)`-`(f)` refs, all coherent) | The citation's substring no longer exists in the spec — a broken locator, not just stale prose | F1 |
| rationale, `## Decision 2` -> Time-scope warning | "`.using(` now appears across ten package modules" -> "four `router.db_for_*` call sites in all … `.using(` is called in 9 package modules (13 mention the token; four mention it only in docstrings or error strings)" | The file contradicted its own later measured table | F2 |
| spec, `## Doc updates`, `docs/TREE.md` bullet | `docs/TREE.md #"tests/optimizer/"` -> `docs/TREE.md #"Package tests for optimizer plans"` | The substring resolves nowhere in `docs/TREE.md`; pre-existing at HEAD | F3 |
| rationale, link definitions + 28 in-body uses | Consolidated seven duplicate `[spec-023-decision-N--<full-slug>]` ref-ids onto the existing `[spec-023-dN]` form; removed the seven orphaned definitions | Two ids per target is redundant scaffolding and doubles the cost of the next rename | F4 |
| spec, `### Decision 3`, out-of-scope lead-in | "Anything outside these four axes is **out of scope for the contract**:" -> "Beyond the four axes and the alias-late principle they rest on, the following are **out of scope for the contract**:" | The lead-in declared out of scope the very behavior the paragraph immediately above it states as contract | F6 |

Not changed, with the reason recorded: the `KANBAN.md` citation in `## Decision 9`'s moved justification (F5); the `## Implementation plan` line-delta table; every `- [ ]` checkbox; `## Borrowing posture`'s upstream paths; `## Risks and open questions` as a section.

## Verification after this pass's edits

- Anchors / references, both files: `in-page unresolved: none`, `used-not-defined: none`, `defined-not-used: none`; 0 missing definition paths; 0 broken cross-file `#fragment`s.
- Duplicate link-definition targets, both files: **0** (was 7 in the rationale).
- `#"substring"` citations: spec 47, **1 broken before this pass, 0 after**; rationale 22, **1 broken, left with reason (F5)**.
- `grep -oE 'rev[0-9]'`: 0 in the spec, 0 in the terms CSV.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-023-multi_db-0_0_7.md` -> `OK: 18 terms - all have glossary entries and at least one spec link.` exit 0.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-023-multi_db-0_0_7.md docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv` -> exit 0.
- Byte counts after this pass (`wc -c`): spec **113,712**; rationale **107,160**; terms CSV **2,679**.
- No `pytest`, no `--cov*` flag, no source or test file read for anything but verification and none modified, no commit, no branch, no `git stash` / `checkout` / `restore` / `worktree`.

## Concurrent-session state

The tree was dirty throughout with another session's `spec-021` / `spec-022` cycle: modified `KANBAN.html`, `KANBAN.md`, `docs/GLOSSARY.md`, `docs/SPECS/appx/spec-021-apps-0_0_7-terms.csv`, `docs/SPECS/spec-021-apps-0_0_7.md`, `docs/SPECS/spec-022-export_schema-0_0_7.md`, `docs/builder/bld-final.md`, `docs/builder/build-021-apps-0_0_7.md`, `docs/feedback.md`, `examples/fakeshop/db.sqlite3`; deleted `docs/builder/bld-integration.md`, two `bld-review-*.md`, `docs/builder/build-020-list_field-0_0_7.md`; untracked `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md`, `docs/builder/DONE/build-020-list_field-0_0_7.md`, `docs/builder/build-022-export_schema-0_0_7.md`. None was edited, reverted, or read for content. The only paths this pass wrote are `docs/SPECS/spec-023-multi_db-0_0_7.md`, `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md`, this artifact, and the cycle memory file.

## Integration outcome

Clean. Six findings: five fixed in this pass inside Worker 1's writable set, one (F5) decided as a non-fix with its reason and carried to the final gate's deferred-work catalog. No duplicated helper, no inconsistent naming, no misplaced responsibility, no repeated passage across the pair, no staged anchor, no code change required, no re-loop.

`Status: final-accepted`.

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
