# Build: R1 — spec rationale extraction (card 044, debug_extension / 0.0.14)

Spec reference: `docs/spec-044-debug_extension-0_0_14.md` (whole file read; the move touched lines 110-325, 1319-1328, 1355-1361, 1404-1417, 1502-1504, 1564-1576, 1645-1659, 1736-1751, 1797-1814, 1886-1897, 1929-1934, 1965-1981, 2020-2027, 2061-2065, 2091, 2296, 2478, 2721, 2856-2866, 2916-2927, 2956, 3123 as numbered before the edit)
Status: final-accepted

Item R1 of the residual-completion cycle in `docs/builder/build-044-debug_extension-0_0_14.md`. Per that plan's **Deviation 3** this item skips the `built` state: `BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role that performs the move and states that Worker 2 never reads the rationale file, so the chain is **Worker 1 (plan + perform) -> Worker 3 (audit) -> Worker 1 (final verification)**. `Status: planned` on return therefore means "dispatch Worker 3", not "dispatch Worker 2".

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately so: this item writes no `.py` file. `### Package-wide helper inventory before helper planning` exists to stop a plan proposing duplicate production helpers, and R1's whole diff is two markdown files. The plan's own declaration (`Hot-path declaration: none. No residual item changes package source.`) is the governing statement. No inventory was refreshed and none is owed.
- **Existing patterns reused.** The move's shape is taken wholesale from the one existing instance in the tree, `docs/spec-046-transport_security-0_0_15-rationale.md` (read in full for its framing, its `## How to read this file` contract, its `Spec: [Decision N][...]` keying line, its `## Change record for the spec's non-decision sections` pattern, and its link-definition layout), and from the pointer-line convention its spec carries at `docs/spec-046-transport_security-0_0_15.md:881` and below (`*Rejected alternatives and change record: [rationale companion, Decision N][rationale-dN].*`). Nothing about the shape was invented.
- **New helpers justified.** None. The one thing this pass could have introduced and did not is a *second* convention for keying a rationale entry to its spec decision; spec-046's is reused verbatim so that a reader of either file reads the same contract.
- **Duplication risk avoided.** The move is the DRY act: a fact told in two files goes stale in one of them, which is exactly what a *copy* of the deliberative layer would guarantee. Every block below left the spec in the same edit that added it here. Two specific near-copies were refused:
  - **No summary anywhere.** The rationale carries moved text verbatim; the only new prose is framing that says where a block came from and why it moved, plus the `### Which revision changed which decision` index, which is an index of the moved chronology rather than a restatement of it.
  - **No re-statement of a moved claim back into the spec.** Where a moved bullet's reason was needed in the spec, it was already there normatively (checked per block — see the checklist), so nothing was written back.

### Implementation steps

Performed in this pass, in this order. Line numbers are pin-at-write-time and refer to the pre-edit spec.

1. Read the whole spec (3,173 lines) before classifying anything, plus `AGENTS.md`, `START.md`, `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, `docs/builder/worker-1.md`, `GOAL.md`, `CHANGELOG.md` `## [0.0.14]`, the build plan, and `docs/spec-046-transport_security-0_0_15-rationale.md` as the shape precedent. `docs/GLOSSARY.md` was read at the entries the terms CSV names rather than end to end (1,915 lines; the 42 anchors are what this pass can falsify).
2. **Computed the glossary-anchor exposure of the move before making it.** For each of the 42 terms in `docs/spec-044-debug_extension-0_0_14-terms.csv`, listed every line in the spec that links its anchor, then intersected those lines with the proposed move ranges. This is what turned Decision 4 from a routine move into the judgement call recorded below: `django-trac-37064-hardening` has exactly **one** link in the whole spec, and it sits inside Decision 4's first rejected alternative.
3. Created `docs/spec-044-debug_extension-0_0_14-rationale.md`: title, deliberative-companion intro, `## How to read this file` (including `### What deliberately stayed in the spec, and why`), `## Change record — revision history` + the per-decision index, `## Change record for the spec's non-decision sections`, `## Decision entries` (one `### Decision N` per spec decision, each opening with a `Spec: [Decision N][s44-dN].` line), `## Change record for Risks and open questions`, and the `<!-- LINK DEFINITIONS -->` block with all ten canonical group headers in order.
4. Cut the spec's **`Revision history`** block (lines 110-325, all eight revisions) and pasted it verbatim under `## Change record — revision history`. Replaced it in the spec with a six-line pointer naming the companion file.
5. Cut the **rejected-alternatives block of every one of the twelve decisions** (Decision 4 partially — see the judgement calls) and pasted each verbatim under its own decision entry. Replaced each with a one-line italic pointer naming what moved.
6. Cut the two pieces of **round provenance** out of `## Helper-reuse obligations (DRY)` — the preamble's "two independent, simultaneously-written reviews ... (2026-07-11)" attribution and obligation D3's "Sharpened by the DRY review:" lead-in — recorded both in the rationale's non-decision change record, and left every claim they introduced in the spec.
7. Cut the two moved items out of `## Risks and open questions`: the **resolved** card-title-vs-shipped-shape conflict, and Revision 8's **retraction** of the async follow-on's false universal premise. Added one pointer line at the end of the section.
8. De-narrated the two surviving cross-references into the moved chronology (`## Test plan`'s "the Revision-8 additions 17-21" scope line and its "**Revision-8 additions ...**" group heading), because a reference into moved text that does not name the rationale file is exactly what rule 3 of the move forbids.
9. Rewrote every in-page anchor inside the moved text (`](#decision-7--…)` and the six section anchors) into reference-style links back into the spec (`[Decision 7][s44-d7]`), since the text now lives in a different file. This is the only alteration made to moved text; no wording changed.
10. Added the `[rationale]` / `[rationale-d1..d12]` / `[rationale-nondecision]` / `[rationale-risks]` definitions to the spec's `<!-- docs/ -->` group, alphabetically.
11. Ran the verification set in `### Test additions / updates`.

### Test additions / updates

No tests: the move touches no code, and per the plan no `pytest` runs in this cycle. The verification set that stands in for it, all run after the edit:

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-044-debug_extension-0_0_14.md` -> `OK: 42 terms - all have glossary entries and at least one spec link.`, **exit 0** (unchanged from pre-flight).
- **Every in-page anchor in both files resolves.** Mechanical, not by eye: fences stripped line by line, headings slugified GitHub-style (backticks stripped, `_` kept, punctuation dropped, each space to one hyphen), then every `](#…)` use checked against the heading set. Spec: 0 broken. Rationale: 0 broken.
- **Every `][ref]` use has a definition and every definition is used**, both files. Spec: 0 undefined, 0 unused. Rationale: 0 undefined, 0 unused. The one apparent hit in the spec (`]["sql"]`) is the `res.extensions["debug"]["sql"]` code span at what is now line 2204 — a pre-existing false positive of the `][…]` probe, not a link.
- **Every cross-file definition target exists on disk, and every cross-file `#anchor` resolves in the target file.** The rationale's 18 `s44-*` definitions all resolve to real spec headings; the spec's 15 new `rationale-*` definitions all resolve to real rationale headings.
- **No surviving history narration in the spec:** `grep -n "Revision [0-9]\|Revision-8\|review round\|Worker \|DRY review\|Two independent"` returns nothing.
- `uv run python scripts/check_trailing_commas.py --check docs/spec-044-debug_extension-0_0_14.md docs/spec-044-debug_extension-0_0_14-rationale.md` -> exit 0 (explicit paths only; run pathless it rewrites unrelated `docs/` scratch files).
- **Byte counts:** spec **205,905 -> 185,272** (-20,633; 3,173 -> 2,836 lines); rationale **0 -> 41,407** (new file, 649 lines). The rationale is larger than the bytes the spec lost because roughly 19KB of it is framing and keying prose — the `## How to read this file` contract, the `### What deliberately stayed in the spec, and why` rulings, the per-entry `Spec:` keying lines, and the `### Which revision changed which decision` index — none of it duplicated deliberation. See the DRY analysis.
- No `ruff` run: no `.py` file was touched.

### Implementation discretion items

None. Two shape choices were assessed and decided rather than delegated, and both follow the one existing precedent instead of introducing an alternative: the rationale's section order and its per-entry `Spec:` keying line come from `docs/spec-046-transport_security-0_0_15-rationale.md`, and the spec-side pointer wording comes from the same cycle's spec. There is no Worker 2 pass to hold discretion in any case (Deviation 3).

### Judgement calls — every sentence that was ambiguous between deliberation and instruction, and which way it was ruled

The prompt names this as the most important part of the artifact, so it is complete rather than representative. The governing rule in every case: *when it is unclear, it stays.*

1. **Decision 4's first rejected alternative ("Port graphene's cursor wrap") — STAYS.** Three independent reasons, any one sufficient. (a) It carries the one link in the entire spec to the `Django Trac #37064 hardening` glossary anchor, which is one of the 42 terms `check_spec_glossary.py` requires the **spec** to link; moving it would have failed the check, and the only repairs would have been to write the clause back into the spec (a copy) or to drop a term from the CSV (out of R1's scope). (b) The hazard clause binds a future writer at the site: it is why no later fidelity upgrade may reach for a cursor wrapper. (c) It states the structural constraint that keeps a richer capture source "one private function swap away", which is a design instruction about how the capture core must be factored.
2. **Decision 4's third rejected alternative ("Wrap with `CaptureQueriesContext` instances directly") — STAYS.** It is the canonical carve-out shape: three constraints an implementer who never read them would rediscover as defects (`ensure_connection()` opening every configured alias, the process-global `request_started -> reset_queries` signal toggle, and the refcount-free single-context restore), plus the normative closing sentence that the extension reuses the class's *semantic contract* without its side effects. Independently, **Decision 10 cites it by position** ("per Decision 4's third alternative, no connection is force-opened"), so moving it would have left a surviving cross-reference pointing out of the spec.
3. **Decision 4's second rejected alternative ("read bare `connection.queries`") — MOVED.** Ruled pure deliberation because the trap it names is stated normatively **twice** in text that stays: in Decision 4's own body ("bare `connection.queries` is empty under `DEBUG=False` — which is every `pytest-django` run and every production-shaped deployment") and in `## Current state` ("an implementation that read bare `connection.queries` without the bracket would capture nothing ... the trap the bracket exists to close"). Nothing a builder needs left the spec.
4. **Every numbered `Grounds:` list — STAYS, as a class ruling.** Two grounds are pure derivation on their own merits (Decision 3's and Decision 4's "The card pre-picked it"), and moving them was considered and refused: the moved alternative bullets cite grounds **by number** ("everything in ground 2", "Rejected per ground 1", "Rejected per ground 2"), so the numbering is load-bearing across the new file boundary and renumbering it to save two sentences is a bad trade. Recorded as a class ruling so a later pass does not go ground-hunting.
5. **`## Current state` — STAYS WHOLE.** It reads like a survey of deliberation and is not: every bullet is a source-verified premise a decision cites (the engine's verified `get_results` call ordering that Decision 7 ground 2 depends on; the `queries_logged` / `CursorDebugWrapper` mechanics behind Decision 4; the old floor's `_sync_extensions` cache behind Decision 6), and the `DEBUG=False`-silent-empty paragraph is the spec's clearest instance of instruction-shaped "why". Separately, several of its bullets are now **historically false** post-release ("No `extensions/` subpackage exists", "The version line reads `0.0.13`"). Rule 3 of the move deletes prose *the current decisions have falsified* — these were falsified by shipping, not by a decision, and the section is explicitly dated ("as this spec is authored"). Deleting or re-tensing them is not R1's call; flagged to R2/R3 in `### Notes for Worker 1 (spec reconciliation)` rather than acted on.
6. **`## Borrowing posture`, including `### Explicitly do not borrow` — STAYS WHOLE.** "Do not borrow X" is a must-not, and each bullet's reason is what stops a later card re-borrowing the refused mechanism; the section is the card's parity contract, which `## Non-goals` cites.
7. **`## Problem statement` and `## Goal and cookbook cross-reference` — STAY WHOLE.** The first is the spec's framing, not a rejected path. The second is a doc obligation (it is where Slice 2's `GOAL.md` criterion-7 clarification is specified) plus the consumer-facing migration recipe and its two diffs.
8. **`## Risks and open questions` preferred-answer / fallback pairs — STAY.** Instruction cites them: DRY D4 requires the two serializers to be module-level *so that* the section's `_debug`-facade fallback can import them, and the Test plan pins the overlap-safety suite against the same fallback. Only two items moved, both settled rather than open: the resolved card-title conflict (settled normatively in `## Non-goals` and in the spec's own title) and the retraction.
9. **The retracted async premise — MOVED, with its live obligation named in the pointer.** The parenthetical is a textbook retraction ("an earlier draft's categorical rejection ... rested on a **false universal premise**"), which `worker-1.md` moves. But it also carries one forward-binding sentence: the follow-on must be decided against a real ASGI-request prototype rather than prose. Rather than copy that sentence back into the spec, the section's pointer line states it, so the obligation is discoverable from the spec in one line and stated in full in exactly one place.
10. **The DRY section's headline claim — STAYS; only its attribution moved.** "Almost nothing in `utils/` is directly callable from `debug.py`, and that is the correct outcome, not a gap", the utils-charter reason, and the (a)/(b)/(c) map of where the real DRY work lives are instruction — a builder who never reads them re-derives the wrong reuse. What moved is *who* said it and when, which changes nothing about what must be built. Same ruling for D3's "Sharpened by the DRY review:" lead-in: the specifics it introduces all stayed.
11. **Decision 2's "Justification:" paragraph — MOVED.** Ruled deliberation: it argues why three named pieces are out of scope ("the card is an M and each excluded piece has its own owner"), while the exclusions themselves — and the Slice-2 docstring rewrite one of them requires — are stated normatively in the three bullets above it, which stay.
12. **The `## Test plan` scenario numbering rule — STAYS; only the revision labels changed.** "Numbering appends rather than renumbers so every existing scenario reference stays stable" is instruction and was left untouched; the two labels that named Revision 8 were reworded because they were cross-references into moved text.
13. **The header opener and `Status:` line — NOT TOUCHED.** The move falsified neither. Line 3's stale ``Planned for `0.0.14` (card [`WIP-ALPHA-044-0.0.14`][kanban])`` is item **R2**'s declared contract; `worker-1.md`'s per-spawn status-line duty is discharged by verifying it and leaving it to its owner rather than by editing across an item boundary.

### Dispatched findings checklist

One box per discrete obligation of the move. A box is `- [x]` only where its contract landed in this pass's diff.

- [x] The rationale file exists at `docs/spec-044-debug_extension-0_0_14-rationale.md`, is tracked (not scratch), and carries the `<!-- LINK DEFINITIONS -->` block with all ten canonical group headers in order, present even when empty, paths resolved from `docs/`.
- [x] Every entry in the rationale names the spec decision or section it belongs to by heading, and opens with a `Spec:` line linking that decision's anchor — no entry that cannot be looked up.
- [x] The spec's `Revision history` block (all eight revisions) moved verbatim and left the spec.
- [x] Decision 1's rejected alternatives moved; a one-line pointer replaced them.
- [x] Decision 2's scope justification and rejected alternative moved; pointer added.
- [x] Decision 3's two rejected exposures moved; pointer added.
- [x] Decision 4's **second** rejected alternative moved; the first and third stay under the carve-out (judgement calls 1-3); pointer added naming both halves.
- [x] Decision 5's three rejected homes moved; pointer added.
- [x] Decision 6's three rejected opt-in shapes moved; pointer added.
- [x] Decision 7's three rejected hook shapes moved; pointer added.
- [x] Decision 8's four rejected row shapes moved; pointer added.
- [x] Decision 9's three rejected capture shapes moved; pointer added.
- [x] Decision 10's two rejected bracket scopes moved; pointer added.
- [x] Decision 11's three rejected placements moved; pointer added.
- [x] Decision 12's two rejected cut owners moved; pointer added.
- [x] `## Helper-reuse obligations (DRY)`: the preamble's review attribution and D3's "Sharpened by the DRY review:" lead-in moved; every claim they introduced stayed; pointer added at the end of the section.
- [x] `## Risks and open questions`: the resolved card-title conflict and the retracted async premise moved; pointer added naming both, including the retraction's one surviving obligation.
- [x] Every change each decision has undergone is recorded with the revision that caused it — the chronology in full, plus a per-decision index so the record is reachable from the decision.
- [x] Every claim a decision may no longer make is recorded as a retraction. **Assertion corrected in pass 2** — the parenthetical read "(one: the async follow-on's universal-executor premise)" and the count is **three**: Revision 2's retraction of the bounded-log clamp *guarantee* (Decision 4), Revision 8's retraction of the byte-identical / off-by-default overclaim (Decision 6), and the async follow-on's universal-executor premise (Risks). All three were already in the chronology verbatim; pass 2 marked the first two in the per-decision index and pointed the index at the third.
- [x] Prose the current decisions have falsified was deleted rather than moved: **none found.** Every block classified as move material is still true as history; the two labels that were false-by-construction after the move (the `Revision-8 additions` cross-references) were reworded in the spec, not carried into the rationale.
- [x] No surviving cross-reference points into moved text without naming the rationale file. **Assertion corrected in pass 2** — the parenthetical read "(the two `Revision-8` labels were the only ones; both fixed)" and that was false. There were **five**: the two `Revision-8` labels (pass 1), plus three the pass-1 grep could not see because they cite by list position or by list slot rather than by chronology vocabulary — Decision 10's "Decision 4's **third** alternative" (`:1613`), Decision 9 ground 1's `([Decision 7] alternatives)` (`:1562`), and DRY D-N4's `[Decision 8]'s rejected alternative` (`:1921`). All three fixed in pass 2; the box holds only with that correction.
- [x] `check_spec_glossary.py --spec docs/spec-044-debug_extension-0_0_14.md` exits 0 at `OK: 42 terms`.
- [x] Every in-page anchor still resolves, in both files, checked mechanically.
- [x] Every `][ref]` has a definition and every definition is used, in both files; every cross-file definition target and `#anchor` resolves.
- [x] `check_trailing_commas.py --check` passes on both files with explicit paths.
- [x] The spec's byte count before and after is reported. **Figure corrected at final verification** — the parenthetical read "(205,905 -> 185,272)", which is the pass-1 measurement; the current figures are **205,905 (HEAD) -> 185,272 (pass 1) -> 185,518 (pass 2)**, all three re-measured with `wc -c` in the final-verification pass. The box's contract (the counts are reported) held throughout; only the parenthetical was stale.
- [x] No package source, test, `examples/`, `scripts/`, `pyproject.toml`, `uv.lock`, `CHANGELOG.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.*`, or other `docs/spec-*.md` file was touched; no commit, no branch.

---

## Build report (Worker 2)

Not applicable. Per the build plan's **Deviation 3** no Worker 2 pass exists for this item — `BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role that performs the move, and Worker 2 never reads the rationale file. The record of what landed is the `## Plan (Worker 1)` section above; the diff is `docs/spec-044-debug_extension-0_0_14.md` (`git diff --numstat`: **54 insertions, 391 deletions**; 3,173 -> 2,836 lines) plus the new `docs/spec-044-debug_extension-0_0_14-rationale.md` (649 lines).

### Failability proofs

None; this pass introduced no new boundary. It writes two markdown files and no executable code.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

---

## Review (Worker 3)

*To be written by Worker 3. `BUILD.md` names Worker 3 as a reader of the rationale file during review, and names this move as "the one place this move can itself cause a defect" — a reviewer with no memory of the pass is the only party positioned to catch implementation-relevant rationale that left the spec.*

The three checks this pass most wants re-run independently, because a self-convincing verification is thinnest exactly here:

1. **Re-read the thirteen judgement calls above against the diff, not against this artifact's summary of it.** The question for each is only: could a builder implementing spec-044 from scratch, reading the post-move spec and never the rationale file, write something wrong? A "yes" on any of them is `revision-needed`.
2. **Confirm nothing was copied rather than moved.** Every block in the rationale should be absent from the spec. A `diff`-style probe over the moved blocks is cheap; whitespace-normalized substring search is the reliable form (line-oriented `grep` misses a re-wrapped copy).
3. **Re-run the four mechanical checks** (`check_spec_glossary.py`, in-page anchors, ref-def symmetry both directions, `check_trailing_commas.py --check`) rather than reading their recorded results. The glossary check in particular is what constrains judgement call 1.

### Audit scope and what does not apply

Reviewed: the whole working-tree diff of `docs/spec-044-debug_extension-0_0_14.md` (22 hunks, 54 insertions / 391 deletions), the new `docs/spec-044-debug_extension-0_0_14-rationale.md` in full (649 lines), the pre-move file at HEAD (`git show HEAD:docs/spec-044-debug_extension-0_0_14.md`, read-only), and the post-move spec at every site the diff touches plus every site a moved sentence cited.

- **`### Failability proofs` — does not apply.** This pass introduced no boundary, guard, gate, or rejection path; it writes two markdown files. `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to boundaries. Re-run floor population is therefore genuinely **zero**, not a subset I chose: an AST/behaviour probe has nothing to mutate.
- **`### Hot-path budget` — does not apply.** Plan declares `Hot-path declaration: none.` and the diff contains no executable line.
- **No `pytest` run, deliberately.** Nothing this pass changed is executable, so a run would confirm only that the tree at large is green — a claim this pass cannot affect and the final gate owns. Every check below is instead a mechanical probe over the two files and their HEAD version.

Probes written for this pass (all under `docs/builder/temp-tests/044-r1/`, gitignored, disposition in `### Temp test verification`): `loss_check.py`, `loss_check2.py` (nothing-lost, whitespace- and link-normalized), `copy_check.py` (move-not-copy, 12-word sliding window), `order_check.py` (per-hunk verbatim-and-in-order), `token_check.py` (every backticked token that left the spec entirely), `link_check.py` (in-page anchors, ref/def symmetry, cross-file targets and anchors), `verbatim_check.py`.

### High:

None.

The defect this pass exists to catch — implementation-relevant rationale leaving the spec — was hunted three independent ways and did not appear:

1. **Token exposure (mechanical, exhaustive).** `token_check.py` extracted all 123 backticked tokens from the removed text and intersected them with the post-move spec: 28 are absent from the spec entirely. Twenty-seven are deliberation-only (`::DjangoDebugContext`, `get_debug_result()`, `_implements_resolve`, `connections["default"]`, `{ _debug { sql } }`, the two rejected filenames, the slug-style examples, `ThreadSensitiveContext` / `sync_to_async(thread_sensitive=True)` / `schema.execute()` from the retraction) or survive in another spelling (`exc.__traceback__` at `:1789`, `-o addopts="-v -n0"` at `:2187-2188`). The 28th is the `**kwargs` clause — Low 1 below, and it never lived outside the chronology.
2. **Revision-history pin sweep.** The chronology was moved wholesale, so every implementation pin it names was grepped against the post-move spec. All present normatively: the reference-counted overlap-safe bracket (`:1407`, `:1743`), the coordinator's two seams and the "single ownership, not the callable shape" pin (`:1808-1810`), connection-**object-identity** keying and the never-match-`connections.all()`-by-position rule (`:1813`, `:1824`), the `errors is None` guard, `get_results` write-purity (`:1418`), the `None` sentinel, the immutable class-level `_payload` (`:1408`), D-N8's premature-abstraction rejections (`:1937`), the never-sort schema-construction seam (`:1767`), `queries_log` / no-`callproc()`, `ATOMIC_REQUESTS` exclusion (`:2468`), the 64-hop ceiling with deterministic stop (`:1531-1537`), the two-phase failure policy (`:1062-1067`), the visibility-safe two-query `Prefetch` shape **and** its `test_products_api.py` assertion precedent (`:719-725`, `:2227-2235`), the module-local `_optimizer` singleton via `lambda: _optimizer` (`:2215-2216`), the single-sited `pytestmark = pytest.mark.urls(__name__)` activation **with** its never-per-test `override_settings(ROOT_URLCONF=__name__)` / `clear_url_caches()` prohibition (`:1771-1776`), the workflow CI floor node, and the replacement claims for both retracted overclaims (`:1018`, `:1370`, `:2282`; `:1827-1828`, `:1981`).
3. **The three grounds under judgement calls 1-2, tested independently.** (a) `django-trac-37064-hardening` is row 41 of the 42-row terms CSV, and `grep -n 'django-trac-37064'` finds exactly one spec-body use — `:1258`, inside Decision 4's first rejected alternative. `scripts/check_spec_glossary.py` resolves anchors from `--spec` only (`spec_link_anchors(args.spec)`), so the rationale file's copy of that link could not have satisfied it: moving the bullet would have failed the check. The anchor-exposure argument is correct as stated. (b) The hazard clause does bind at the site — it is the only statement in the spec of *why* cursor wrapping is refused, and `## Non-goals` / `## Out of scope` do not restate it. (c) Decision 10 does cite that alternative, at `:1612-1613` — see Medium 1, which is the consequence of the citation rather than a refutation of it.

Judgement call 3 also checks out: the moved bare-`connection.queries` trap is stated normatively twice in retained text — `## Current state` `:643-644` and Decision 4's body `:1195-1196`. Judgement call 11 checks out: Decision 2's three exclusions and the Slice-2 docstring-rewrite obligation are all normative at `:1117-1134`; only the "the card is an M" justification moved. Judgement calls 4 (grounds stay) is verified by the numbering surviving intact — D3 grounds 1-5, D5 1-3, D7 1-3, D9 1-3 — so the moved bullets' "everything in ground 2" / "Rejected per ground 1" citations all still resolve.

### Medium:

#### The move falsified Decision 10's ordinal citation of "Decision 4's third alternative"

`docs/spec-044-debug_extension-0_0_14.md:1612-1613` reads:

```docs/spec-044-debug_extension-0_0_14.md:1611:1613
per
[Decision 4](#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port)'s
third alternative, no connection is force-opened.
```

At HEAD, Decision 4 listed three rejected alternatives — cursor-wrap port, bare `connection.queries`, `CaptureQueriesContext` — and the citation was correct (`git show HEAD:…` `:1921` citing the third of three). The move removed the **second** bullet, so the spec's Decision 4 now lists exactly two (`:1252` and `:1265`) and the cited "third alternative" does not exist. The intended target is now the second, `**Wrap with CaptureQueriesContext instances directly.**`; the surviving pointer line at `:1285` says "the two alternatives above", confirming the count internally while `:1613` still says three.

Why it matters: this is precisely the class rule 3 of the move exists to catch — a surviving cross-reference the move invalidated — and it is the one the pass reasoned about most and still missed, because judgement call 2 treated the citation as a *reason to retain* the target without asking what the removal did to the ordinal. The Plan's checklist box "No surviving cross-reference points into moved text without naming the rationale file (the two `Revision-8` labels were the only ones; both fixed)" is literally true (this reference points at retained text) and its sweep is what came up short: the falsified-by-ordinal case was not in scope of the grep that found the two labels.

Recommended change (Worker 1 owns both files):

- `:1611-1613` — replace the ordinal with a name-based reference, e.g. "per [Decision 4]'s rejection of wrapping `CaptureQueriesContext` directly, no connection is force-opened." A name is stable under any future move; an ordinal is not.
- `docs/spec-044-debug_extension-0_0_14-rationale.md:50-52` repeats the ordinal as a quotation ("cites it by position (\"per Decision 4's third alternative, no connection is force-opened\")"). Once the spec no longer says that, this quotation is stale too — reword it to state that Decision 10 cites the alternative (by name, after the fix) so the two files do not disagree about what the spec says.

No test expectation: nothing executable is affected.

### Low:

#### 1. The "no `**kwargs` sink" constraint now exists only in the rationale

`git show HEAD:docs/spec-044-debug_extension-0_0_14.md` `:241` carried "the no-`__init__` rule keeps the first review's default with the second's constrained escape (`execution_context` passthrough only, no `**kwargs` sink)" — and that was its **only** occurrence in the pre-move spec, i.e. it lived inside the Revision-5 chronology and never in the normative D6 rule. Post-move, `grep -icE 'kwargs'` over the spec finds only the unrelated "sidecar kwargs" at `:1897`.

D6's surviving escape (`:1836-1845`) says "If future configuration requires an explicit constructor, initialize only that configuration and do not claim that `super().__init__(execution_context=...)` performs the binding", which arguably subsumes it. And the shipped rule is **no `__init__` at all**, so no builder of `0.0.14` could have needed the clause — it binds a future writer, which is exactly the carve-out's own test. Flagged rather than suppressed because `BUILD.md`'s tie-break is "when it is unclear, it stays", and this one is unclear.

Recommended change: append the clause to D6's escape ("initialize only that configuration — `execution_context` passthrough only, never a `**kwargs` sink — and do not claim …"), **or** record a rejection reason (subsumed by "initialize only that configuration"). Both are equal-cost; either closes the finding.

#### 2. `### Which revision changed which decision` under-reports two retracted claims, and the checklist box says "one"

`BUILD.md` `## Spec rationale extraction` requires each entry to carry "any claim the decision once made and may no longer make". The chronology preserves three such claims verbatim, but the per-decision index — the reachability aid a reader of a decision actually follows — surfaces only the async premise:

- Revision 2 "replaced the inaccurate bounded-log clamp guarantee with Django's actual best-effort length-snapshot semantics" (rationale `:140-141`) is a retracted claim on the log-slice contract, and the Decision 4 row (`:304`) lists Revision 2 only as "the lock-protected reference-counted flag bracket".
- Revision 8 "the byte-identical / off-by-default overclaim replaced with the narrow no-instrumentation/no-key claim" (rationale `:249-250`) is a retracted claim, and the Decision 6 row (`:306`) lists Revision 8 only as "the release-wide migration notes and the durable CI floor node".

Nothing is lost — both claims are in the file and both **replacements** are normative in the spec (`:1018`, `:1370`, `:2282`; `:1827-1828`, `:1981`) — so this is reachability plus a count, not content. But the Plan's checklist box "Every claim a decision may no longer make is recorded as a retraction (one: the async follow-on's universal-executor premise)" reads as an exhaustive audit and is not one.

Recommended change: add both to their index rows, marked as retractions, and correct the box's parenthetical from "one" to name all three.

#### 3. Two quoted spec lines in the non-decision change record are not character-exact

`docs/spec-044-debug_extension-0_0_14-rationale.md:322-325` quotes the two retired Test-plan labels as `"scenarios 8-15 and the Revision-8 additions 17-21 live in …"` and `"**Revision-8 additions (16 live-sharded; 17-21 mechanics):**"`. Both used en dashes in the spec (`8–15`, `17–21`, verified against HEAD). A change record whose whole value is preserving the retired wording should reproduce it character-for-character; the surrounding new prose can keep ASCII hyphens. (Cosmetic only — the ASCII-only rule is `.py`-source scope, so nothing forced the substitution.)

#### 4. Two non-decision entries name their spec section without linking its anchor

The file's own `## How to read this file` promises every entry opens with a `Spec:` line linking what it belongs to, and every decision entry plus `## Change record for Risks and open questions` (`:560`) does. The two entries at `:322` (`## Test plan`) and `:328` (`## Helper-reuse obligations (DRY)`) name their section only in a code span. `[s44-test-plan]` and `[s44-dry]` are already defined and already used elsewhere in the file, so the fix is two links; without them those entries are the only ones a reader cannot jump from.

### DRY findings

- **The move itself is the DRY act and it was performed as one.** `copy_check.py` slid a 12-normalized-word window over the whole rationale against the whole spec: the only shared fragments are the twelve `### Decision N — …` headings (required — the entry names its decision by heading) and one deliberately-quoted spec sentence at rationale `:585-586`, framed as "The spec's surviving fallback sentence (…) is what remains there." No moved block exists in both files. `order_check.py` further confirms all 22 hunks' removed prose appears in the rationale **verbatim and in original order** (213/213 lines for the revision history, 9/9, 7/7, 13/13, 3/3, 12/12, 14/14, 15/15, 17/17, 11/11, 6/6, 16/16, 7/7, 11/11, 11/12 for the decisions and risks), with the only unmatched lines being the four deliberate rewordings and one split line, each independently accounted for below.
- **One duplication observed, and rejected as correct:** the Decision 4 entry's framing (rationale `:391-395`) restates the "stated normatively twice" ruling that `### What deliberately stayed in the spec, and why` (`:42-52`) already makes. Two tellings in one file is normally a stale-in-one-of-them risk, but here they serve different entry points (the index a reader lands on first vs. the entry a spec pointer jumps to) and the shorter one carries no fact the longer one lacks. No action.
- No new abstraction, helper, registry, or convention was introduced: the file's shape, its `Spec:` keying line, its `## How to read this file` contract, and the spec-side pointer wording are all reused from `docs/spec-046-transport_security-0_0_15-rationale.md`. The existence challenge does not arise — the rationale file is mandated by `BUILD.md`, not invented here.

### Public-surface check

Confirmed mechanically, not assumed: `git diff -- django_strawberry_framework/__init__.py` prints **0 lines**, so `__all__` and the re-export list are untouched. `git status --short` at review time is `M docs/feedback.md`, `M docs/spec-044-debug_extension-0_0_14.md`, `D to-many-search-optimizer-reproduction.md`, plus the three untracked cycle files — no package source, no test, no `examples/`, no `scripts/`, no `pyproject.toml` / `uv.lock` / `CHANGELOG.md` / `docs/GLOSSARY.md` / `docs/TREE.md` / `KANBAN.*`, and no other `docs/spec-*.md`. The two baseline-dirty entries match the plan's declared list and were neither edited nor reverted by this review.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

This pass touches docs and an active spec, so the check applies. Re-run rather than accepted:

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-044-debug_extension-0_0_14.md` → `OK: 42 terms - all have glossary entries and at least one spec link.`, **exit 0**. Reproduces Worker 1's record.
- `uv run python scripts/check_trailing_commas.py --check docs/spec-044-debug_extension-0_0_14.md docs/spec-044-debug_extension-0_0_14-rationale.md` → **exit 0**. Reproduces Worker 1's record, explicit paths as recorded.
- **In-page anchors, independently re-derived** (fences stripped, GitHub-style slugs): spec 26 uses / **0 broken**; rationale 1 use / **0 broken**.
- **Ref/def symmetry both directions:** spec 103 `][ref]` uses against 102 definitions, **0 unused**, one "undefined" hit — `]["sql"]`, the `res.extensions["debug"]["sql"]` code span, i.e. the same pre-existing false positive of the `][…]` probe Worker 1 recorded. Rationale: 28 uses / 28 definitions, **0 undefined, 0 unused**.
- **Cross-file targets and anchors:** every definition in both files resolves to a file that exists on disk, and every `#anchor` resolves to a real heading in that file — the rationale's 18 `s44-*` into the spec, the spec's 15 new `rationale-*` into the rationale, and `GLOSSARY.md#django-trac-37064-hardening` in both. The single non-file target is the strawberry issue URL, as expected.
- **Link scaffold:** the rationale carries `<!-- LINK DEFINITIONS -->` with all ten canonical group headers in order, empty ones present, and definitions alphabetical within each group. Paths resolve from `docs/` — correct for today; R3 re-relativizes them, so not flagged.
- **Byte counts verified independently:** HEAD spec **205,905**, post-move spec **185,272**, rationale **41,407** — matching the plan's pre-move figure and Worker 1's report exactly.
- **The spec reads as a clean current contract.** `grep -niE 'revision|amendment|retract|earlier draft|previously|review round|round [0-9]|as of |originally|no longer permitted'` returns only the two pointer lines (`:110-115`, `:2601`) and three incidental uses of "previously acquired" / "a later revision needs a raise" / "if a future revision insists" — none of which narrates this spec's own history. No amendment block, no retraction paragraph, no "as of review round N" hedge, no chronology a reader must apply.
- **Every decision keeps its pointer:** all twelve `### Decision N` sections carry a one-line italic pointer naming what moved and where (`:1109`, `:1136`, `:1179`, `:1285`, `:1325`, `:1394`, `:1471`, `:1517`, `:1589`, `:1621`, `:1652`, `:1691`), plus the header (`:110-115`), the DRY section (`:1960-1961`), and Risks (`:2601-2604`). Every moved block therefore has a discoverable pointer, and no pointer names a block that did not move.
- **No obsolete "coming soon" / "planned" / old-version wording introduced by this pass.** The stale wording that *is* in the spec is pre-existing and is R2's declared contract — routed below, not suppressed.
- No script-rendered doc, no KANBAN movement, no archival in this diff.

### What looks solid

- **The classification held up under exhaustive rather than sampled checking.** Thirteen recorded judgement calls, and the two the audit was most likely to overturn — Decision 4's retained first and third alternatives — survive all three of their grounds on independent evidence, including the one that is mechanically falsifiable (the sole spec-side `django-trac-37064-hardening` link).
- **The retained/moved boundary is drawn at the right place in the hard cases.** Decision 2 keeps its exclusions and loses only "the card is an M"; the DRY section keeps its headline, its utils-charter reason and its (a)/(b)/(c) map and loses only *who said it and when*; the async retraction moves while its one forward-binding obligation (decide against a real ASGI prototype) is stated in the spec-side pointer instead of copied back. That last one is the sharpest call in the pass and is the correct shape: discoverable from the spec in one line, stated in full in exactly one place.
- **Nothing was lost and nothing was deleted.** Every one of the 391 removed lines is accounted for: in the rationale verbatim (367), still in the spec re-wrapped with only the attribution stripped (7, the DRY preamble), or a deliberate reword whose retired text the change record quotes (4) plus one line split between the two files. The "deleted nothing under rule 2" claim is therefore verified, not accepted.
- **The rationale works as a review instrument, not an archive.** Every decision entry opens with a linked `Spec:` line, states what stayed and why before what moved, and the per-decision index makes each decision's chronology reachable from the decision. Spot-checking the index against the chronology, the "D3 vs Decision 3" trap — Revisions 5 and 6 say "D3" meaning DRY obligation D3 — was navigated correctly and not mis-attributed to Decision 3.

### Temp test verification

- Temp files used: `docs/builder/temp-tests/044-r1/spec.diff`, `loss_check.py`, `loss_check2.py`, `copy_check.py`, `order_check.py`, `token_check.py`, `link_check.py`, `verbatim_check.py`.
- Disposition: **kept for the cycle, not promoted.** None catches a code behaviour bug, so `worker-3.md`'s promotion rule does not fire — they are doc-integrity probes over one pair of files, and a permanent test of them would pin this cycle's file names. Worth noting for Worker 1 and R3: `link_check.py` (in-page anchors + ref/def symmetry + cross-file anchor resolution in one pass) is directly reusable for R3's post-archive link sweep, where every definition path changes at once and the visible diff is only a rename.
- No source file was mutated at any point in this pass; the failability carve-out was not exercised because no boundary exists to mutate.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Medium 1) is not escalated** — it is a direct correction to this pass's own output, routed back through `revision-needed` rather than through this section, because the fix needs no spec context I cannot supply: two sentences, one in each file, named exactly above.
- **For R2, confirming and extending R1's hand-off.** The `## Current state` bullets Worker 1 flagged are the visible half. `:104-108` also still reads that `docs/GLOSSARY.md` "carries [Response-extensions debug middleware] as `planned for 0.0.14`; Slice 2 updates the entry body … and Slice 3 flips the status" — future tense for three slices that shipped, in the header paragraph immediately above the new deliberative-layer pointer. Same class as the stale opener at `:3` and squarely R2's declared contract; recorded here so R2's audit rules on the whole header region rather than only line 3. R1 correctly did not touch it.
- **For R3, one item the R1 hand-off does not name.** The rationale's `<!-- External -->` group carries three `../../django-graphene-filters/…` definitions and `<!-- examples/ -->` one `../examples/…`, i.e. the file has **four** `../`-prefixed paths that gain a level on the move to `docs/SPECS/`, and `<!-- docs/SPECS/ -->` carries `[next]: SPECS/NEXT.md` + `[spec-038]: SPECS/spec-038-…` which **shorten**. Both directions are in the plan's inversion list for the spec; they apply identically to the rationale file, and one of them (`[glossary-django-trac-37064]: GLOSSARY.md#…`) is load-bearing for a `check_spec_glossary.py`-adjacent anchor, so it is worth re-running an anchor-resolution pass on both files after the move rather than only checking file existence.
- **For R3, a caution on the Medium above.** If Medium 1 is fixed as recommended (ordinal → name), R3's cross-reference sweep should not "restore" the ordinal when re-relativizing; the whole point of the reword is that a name survives relocation.

### Review outcome

`revision-needed`.

One Medium (a cross-reference the move falsified, in the spec, with the exact remedy specified) and four Lows, each carrying a named fix and, where legitimate, an equal-cost "record a rejection reason instead" path. Nothing in the move's classification is rejected: the High tier is empty on evidence rather than on absence of looking, and no moved passage needs to come back. Per the plan's **Deviation 3** this routes to **Worker 1**, not Worker 2.

To be explicit about the acceptance arithmetic: had the Medium been absent, Lows 1-4 alone would still block `review-accepted` under `worker-3.md`'s gate until each is addressed **or** carries a recorded rejection reason — three of the four are one clause each, and Low 1 is legitimately rejectable on the record.

---

## Final verification (Worker 1)

*Pending — runs after Worker 3's audit, per Deviation 3.*

### Spec changes made (Worker 1 only)

Every spec edit in this pass, with the line range as numbered **before** the edit and a one-line reason. All are the removal half of the move, its pointer lines, or a cross-reference the move falsified.

- `docs/spec-044-debug_extension-0_0_14.md:110-325` — the whole `Revision history` block moved to the rationale file; replaced by a six-line pointer. `BUILD.md`: the spec never narrates its own history.
- `:1319-1328`, `:1355-1361`, `:1404-1417`, `:1564-1576`, `:1645-1659`, `:1736-1751`, `:1797-1814`, `:1886-1897`, `:1929-1934`, `:1965-1981`, `:2020-2027` — the rejected-alternatives blocks of Decisions 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12 moved; each replaced by a one-line pointer naming what moved and where.
- `:1502-1504` — Decision 4's second rejected alternative moved (only that one; judgement calls 1-3). A pointer was added after the two surviving alternatives, naming both what moved and that the others deliberately stay.
- `:2061-2065` — the DRY preamble's review attribution removed; the headline claim, the utils-charter reason, and the (a)/(b)/(c) map kept verbatim.
- `:2091` — D3's "Sharpened by the DRY review:" lead-in became "Sharpened to specifics:"; the attribution is history, the specifics are instruction.
- `:2296` — pointer line added at the end of the DRY section.
- `:2478`, `:2721` — the two `Revision-8 additions` labels in `## Test plan` reworded; they were cross-references into text that no longer lives in the spec.
- `:2856-2866` — the resolved card-title-vs-shipped-shape risk moved.
- `:2916-2927` — the retracted async-follow-on premise moved; the bullet's surviving sentence ends at "async consumers report gaps."
- `:2956` — pointer line added at the end of `## Risks and open questions`.
- `:3123` — fifteen `rationale*` link definitions added to the `<!-- docs/ -->` group, alphabetically.

Status-line re-verification (`worker-1.md` `## Spec status-line re-verification`): read lines 1-108 at the start of the pass. The `Status:` line (**COMPLETE**, card `DONE-044-0.0.14`, all three slices built, the joint cut applied) is accurate and the move did not falsify it. The **opener at line 3 is stale** (``Planned for `0.0.14` (card [`WIP-ALPHA-044-0.0.14`][kanban])``) and was deliberately left: it is item R2's declared contract, and the move did not falsify it — it was already stale at pre-flight.

### Notes for Worker 1 (spec reconciliation)

Carried forward for R2 and R3 rather than acted on here.

- **For R2:** several `## Current state` bullets are historically false after the release — "No `extensions/` subpackage exists", the `docs/TREE.md` "planned by TODO-ALPHA-044-0.0.14" reservation, the `config/schema.py` "no direct Strawberry analogue" docstring quote, and "The version line reads `0.0.13`". The section is explicitly dated ("A true description of the repo as this spec is authored"), so this may well be correct as a snapshot; the point is that R2's `## Doc updates` / `## Definition of done` audit is the pass that should rule on it, and it should rule deliberately rather than by omission. R1 did not touch them (judgement call 5).
- **For R3:** the rationale file's link block resolves from `docs/`. Its `<!-- docs/ -->` group holds 18 `s44-*` definitions plus `[spec-044]` and one `GLOSSARY.md` anchor, all sibling-relative; `<!-- docs/SPECS/ -->` holds `[next]` and `[spec-038]` as `SPECS/…`; `<!-- Root -->`, `<!-- examples/ -->`, and `<!-- External -->` hold `../`-prefixed paths. On the move to `docs/SPECS/` the sibling-relative ones stay sibling-relative (the spec moves with it), `SPECS/…` **shortens** to `…`, and the `../` ones gain a level — the same inversion the build plan already flags for the spec. **The spec now also carries fifteen `rationale*` definitions**, which the R3 sweep must include; they stay sibling-relative through the move.
- **For R3:** `docs/spec-050-debug_extraction-0_0_19.md` cites spec-044 three times (its own line 127, 472, and the `[spec-044]` definition at 554). None of those citations points into text this pass moved, so R3's rewrite is still a pure path repoint. The new rationale file is a **third** file R3 must move and re-relativize, exactly as the plan's R3 entry says.

### Baseline / concurrent-work note

`git status --short` at the end of this pass: `M docs/feedback.md`, `M docs/spec-044-debug_extension-0_0_14.md`, `D to-many-search-optimizer-reproduction.md`, `?? docs/builder/build-044-debug_extension-0_0_14.md`, `?? docs/spec-044-debug_extension-0_0_14-rationale.md`.

Two entries are not this pass's and were neither edited nor reverted (`AGENTS.md` rule 34):

- `to-many-search-optimizer-reproduction.md` — the plan's declared baseline-dirty deletion.
- **`docs/feedback.md` — new since the plan's baseline.** It is a maintainer adversarial review of **spec-046** (its opening line reads "Adversarial review: spec-046 transport security"; 133 insertions, 109 deletions, replacing the previous pass's review with a hostile-boundary pass on connection actor state). Its mtime precedes this pass's first write. It is a concurrent session's or the maintainer's work on the preserved spec-046 cycle, is not referenced by spec-044, and is out of scope for every residual item. Reported, not touched.

---

## Build report (Worker 1, pass 2 — custodian apply)

Worker 3 set `revision-needed` on the move. Under the plan's **Deviation 3** this item has no Worker 2, so the apply pass is Worker 1's in the builder's seat; the section therefore carries the `## Build report` shape from `docs/builder/ARTIFACT.md` with Worker 1 named. Placed at the end of the file so the artifact still reads as a linear pass / review / pass sequence and no prior entry — Worker 1's plan, Worker 3's review, or the pass-1 `### Spec changes made` record — is edited. The two exceptions are the two `### Dispatched findings checklist` boxes whose *assertions* the review falsified; correcting those is the audit discipline `BUILD.md` `### Dispatched findings checklist` assigns to Worker 1, and each correction is marked inline as pass 2's.

**`Status:` on return is `planned`, not `built`.** Deviation 3 makes `planned` this item's "ready for review" value — `built` belongs to Worker 2, which R1 has none of — so `planned` routes Worker 0 to dispatch Worker 3 for a re-review. A reader who finds a `planned` artifact that has now been built twice should read it as "re-review R1", not as "unplanned work".

### Files touched

- `docs/spec-044-debug_extension-0_0_14.md` — four edits: three cross-references that cited moved text by list position or by list slot, now citing by name; and one clause returned to `## Helper-reuse obligations (DRY)` D6. Enumerated under `### Spec changes made (Worker 1 only), pass 2` below.
- `docs/spec-044-debug_extension-0_0_14-rationale.md` — six edits: de-ordinalized the two places that quoted or restated the falsified citation, marked the two under-reported retractions in the per-decision index and pointed it at the third, linked the two non-decision entries that named their section without linking it, restored the two quoted Test-plan labels to their character-exact en dashes, and added two change-record bullets (the cross-reference class; the D6 clause's return).
- `docs/builder/bld-044-r1-rationale_move.md` — this section, the two checklist-assertion corrections, `Status:`.
- `docs/builder/worker-memory/worker-1.md` — memory entry.

No package source, no test, no `examples/`, no `scripts/`, no `pyproject.toml` / `uv.lock` / `CHANGELOG.md` / `docs/GLOSSARY.md` / `docs/TREE.md` / `KANBAN.*`, no other `docs/spec-*.md`, no `bld-*.md` from the preserved spec-046 cycle, and no commit or branch.

### Worker 3's findings, one by one

**Medium 1 — the move falsified Decision 10's ordinal citation of "Decision 4's third alternative". FIXED, and the prescription was assessed before it was applied.**

Verified independently rather than accepted: `git show HEAD:…` `:1918-1921` carries `per [Decision 4](#…)'s / third alternative, no connection is force-opened`, and HEAD's Decision 4 listed three alternatives in the order cursor-wrap port / bare `connection.queries` / `CaptureQueriesContext`. So the citation was correct at HEAD, the move removed the middle bullet, and the ordinal now names a bullet that does not exist while the pointer line at `:1282` says "the two alternatives above". Finding confirmed exactly as filed.

The prescription — name the alternative instead of numbering it — is **correct, and correct for the right reason**, which is why it was accepted rather than applied blindly. The claim at the citation site is "no connection is force-opened"; that guarantee comes from ground (a) of the `CaptureQueriesContext` rejection (`__enter__` calls `connection.ensure_connection()` eagerly on every alias). So the intended target really is the `CaptureQueriesContext` bullet, and naming it makes the citation true under any future reordering, including R3's relocation. Applied:

- `docs/spec-044-debug_extension-0_0_14.md` `:1611-1614` — `third alternative` -> "rejection of wrapping `CaptureQueriesContext` directly".
- `docs/spec-044-debug_extension-0_0_14-rationale.md` — both places that carried the ordinal: the `### What deliberately stayed in the spec, and why` Decision-4 bullet (which named the alternatives as "first and third" / "second" and quoted the spec's ordinal citation) and the `### Decision 4` entry's opening line ("Only the second of three rejected alternatives moved"). Both now name the alternatives; the entry line still records that Decision 4 originally listed three, because that is what makes the *move* legible. The "stayed" bullet closes with the rule, so R3 does not undo it: a name survives a move, an ordinal does not.

**The class sweep found three more instances, and this is the finding's real size.** Worker 3 found this one by inspection and said so; `worker-1.md` `### Performing the rationale move` rule 3 exists for the class, so the whole class was swept rather than the reported instance patched. Two greps, both mechanical:

1. Ordinals and positional words in both files (`first|second|third|fourth|fifth|sixth|last`, `above`, `below`, `ground [0-9]`), each hit resolved against what it names.
2. The *vocabulary of moved text* in the spec (`reject`, `alternativ`, `justificat`, `derivation`, `considered`) — because a citation can be falsified without containing an ordinal at all, simply by naming a list that left the file.

That second grep is what pass 1 did not run, and it is where the two new instances live:

- **`:1562`** — Decision 9 ground 1 read `re-implementation with a hot-path cost ([Decision 7](#…) alternatives).` Decision 7's alternatives block moved **in full**, so the spec's Decision 7 no longer has one. Now: ``([Decision 7](#…)'s rejected `resolve` hook: [rationale companion][rationale-d7]).`` — names the alternative and names the file, which is what rule 3 requires.
- **`:1921`** — DRY D-N4 read `the keys are a wire contract — [Decision 8](#…)'s rejected alternative`. Decision 8's four alternatives all moved. Now: `[Decision 8](#…)'s wire-casing table, with the casing-helper rejection recorded in the [rationale companion][rationale-d8]` — the retained table is what the claim actually rests on, and the moved argument is linked.

Both use `[rationale-d7]` / `[rationale-d8]`, already defined and already used by the two decisions' own pointer lines, so no definition was added and none went unused.

**Nine further hits of the same shape were verified and rejected as already-resolving**, recorded so a later pass does not re-flag them: `:273` and `:2543` ("Decision 3's rejection of a permanent schema surface" — Decision 3's title and grounds 1-5 stayed); `:741` ("rejected with reasons in [Decision 3]" — same); `:856` and `:1884` ("rejected in [Decision 4]" / "([Decision 4] alternatives)" — Decision 4 **retains** the cursor-wrap-port bullet, which is exactly what both cite); `:1217` and `:2410` ("the rejected cursor wrap" — same retained bullet); `:1574` ("the rejected per-field wrapper" — stated normatively in Decision 9 ground 1, which stayed); `:2083` ("Considered and rejected." — self-contained). Every `[Risks](#risks-and-open-questions)` reference was also re-resolved against the six surviving risks: `:272` / `:1796` / `:2176` reach the `_debug`-facade fallback, `:769` the knobs, `:791` the async follow-on, `:1263` the fidelity-card fallback. None points at either moved item.

**Every numbered `Grounds:` citation across the new file boundary re-verified, because pass 1 made it a class ruling.** The ruling holds, and it is now checked rather than reasoned: all eight `Grounds:` lists survive with contiguous numbering (Decision 3 → 1-5, Decision 4 → 1-4, Decision 5 → 1-3, Decision 6 → 1-4, Decision 7 → 1-3, Decision 9 → 1-3, plus Decisions 8 and 10's prose grounds), and each moved bullet's citation was resolved to the ground's *text*, not just its number: Decision 3's `_debug`-field rejection → ground 2 "No schema pollution and no `Meta` growth"; Decision 5's package-root rejection → ground 2 "The subpackage-not-root export…", and the rationale's "Ground 3's eager-re-export instruction stayed" → ground 3 "Eager re-export, no lazy machinery"; Decision 7's `get_results` rejection → ground 2 "Teardown is the only point that is both complete and ordered", and its async-twin rejection → ground 1 "A sync generator serves both execution colors"; Decision 9's per-field rejection → ground 1 and its ungated-errors rejection → ground 2. The rationale's one other numbered citation, "[Decision 7] ground 2" for the verified `get_results` call ordering, resolves to that ground's `[Current state](#current-state)` sentence. Zero drift.

**One in-page positional reference inside moved text was ruled and left.** The moved bare-`connection.queries` bullet ends "the `DEBUG=False` silent-empty trap **above**", and in the rationale there is no spec body above it. Moved text is verbatim by contract — link rewrites are the only permitted alteration — so the fix is not to edit the bullet but to make the referent explicit in the framing that a reader hits first: the `### Decision 4` entry now closes with "Its closing 'trap above' therefore points at those two statements, which the sentence before this list names." The two statements are the ones the framing already cited (Decision 4's body and `## Current state`), so nothing new was asserted.

**Low 1 — the "no `**kwargs` sink" constraint existed only in the rationale. FIXED rather than rejected**, though Worker 3 correctly identified it as rejectable.

The finding is exact: `git show HEAD:…` `:241` is the clause's only pre-move occurrence, inside the Revision-5 chronology, and `grep -c 'kwargs'` over the post-move spec found only the unrelated "sidecar kwargs" at `:1897`. Two reasons to close it by adding the clause rather than by recording a rejection, both stronger than the equal-cost framing suggests. First, `BUILD.md` `## Spec rationale extraction`'s carve-out tie-break is "when it is unclear, it stays", and Worker 3's own analysis is that it is unclear. Second, this is the exact shape of a rule that belongs at its site: it binds a **future** writer (the one who adds the constructor D6 currently forbids), and D6's surviving escape says only "initialize only that configuration", which does not by itself forbid widening the signature. Applied at `:1841-1844`: "initialize only that configuration — `execution_context` passthrough only, never a `**kwargs` sink — and do not claim that…".

This creates the one thing pass 1 refused throughout — a sentence in both files — so it is recorded as a change rather than left to look like a copy: `docs/spec-044-debug_extension-0_0_14-rationale.md` `## Change record for the spec's non-decision sections` gains a bullet stating that D6's escape regained the clause, that Revision 5's account is its *provenance* and not a second copy of the rule, and why the move had briefly taken it out of the spec entirely. The spec now carries the rule; the rationale carries who decided it and when.

**Low 2 — the retraction index under-reported two claims and the checklist box said "one". FIXED, both halves.**

Verified both against the chronology: Revision 2 "replaced the inaccurate bounded-log clamp guarantee with Django's actual best-effort length-snapshot semantics", and Revision 8 "the byte-identical / off-by-default overclaim replaced with the narrow no-instrumentation/no-key claim" — each is a claim a decision may no longer make, and each replacement is normative in the spec (the length-snapshot semantics at `:1981-1984` and DRY D5 `:1827-1829`; the narrow claim under Decision 6). Applied in the rationale:

- `### Which revision changed which decision` gains a lead-in defining **Retracted**, stating the count is three, and linking the third (the async premise) to `## Change record for Risks and open questions`, which is where it lives because it is a Risks item and not a decision row.
- The Decision 4 row and the Decision 6 row each gain their retraction, marked **retracted** and naming the replacement's home so the row is usable without re-reading the chronology.

The checklist box's parenthetical is corrected in place, marked as pass 2's, and names all three.

**Low 3 — two quoted spec lines were not character-exact. FIXED.** Confirmed against HEAD (`:2477-2478`, `:2721`): both retired Test-plan labels used en dashes (`8–15`, `17–21`). The rationale's change record had them as ASCII hyphens. Restored inside the quotation marks only; the surrounding new prose keeps ASCII. Worker 3's reasoning is right that nothing forced the substitution — the ASCII-only rule is `.py`-scope — and a change record whose value is preserving retired wording has to reproduce it exactly.

**Low 4 — two non-decision entries named their spec section without linking it. FIXED.** `## Test plan` and `## Helper-reuse obligations (DRY)` in the non-decision change record are now ``[`## Test plan`][s44-test-plan]`` and ``[`## Helper-reuse obligations (DRY)`][s44-dry]``. Both definitions already existed and were already used elsewhere, so ref/def symmetry is unchanged. The section's opener also lost its now-wrong count ("Three corrections outside any numbered decision") because pass 2 adds two bullets and one of them spans decision sections — it now reads "Corrections made by this move rather than by a review round, kept here because they belong to no single decision entry".

**Nothing was rejected.** All five findings are fixed. Worker 3's two forward-looking notes are honoured rather than absorbed: the R2 hand-off (the stale opener at `:3` and the future-tense header at `:104-108`) is untouched, and the R3 caution is now written into the rationale itself so the name-based citations survive re-relativization.

### Validation run

No `ruff` run: no `.py` file was touched. No `pytest`: nothing this pass changed is executable, and the plan forbids `--cov*` in any pass regardless.

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-044-debug_extension-0_0_14.md` → `OK: 42 terms - all have glossary entries and at least one spec link.`, **exit 0**. Re-run after the edits, not carried over.
- **In-page anchors, both files, mechanically** (fences stripped line by line, GitHub-style slugs — backticks stripped, `_` kept, punctuation dropped, **each** space to one hyphen, duplicate headings suffixed): spec **200 uses / 0 broken**; rationale **2 uses / 0 broken**. The count differs from Worker 3's recorded 26 because this probe counts every `](#…)` in the spec rather than a filtered subset; the result that matters — zero broken — agrees.
- **Ref/def symmetry, both directions:** spec 103 `][ref]` uses / 102 definitions, **0 unused**, one "undefined" hit `]["sql"]` — the `res.extensions["debug"]["sql"]` code span, the same pre-existing false positive of the `][…]` probe both prior passes recorded. Rationale **28 uses / 28 definitions, 0 undefined, 0 unused**.
- **Cross-file definition targets and anchors:** every non-URL definition in both files resolves to a file that exists on disk, and every `#anchor` resolves to a real heading in the target file. No definition was added or removed by this pass in either file.
- `uv run python scripts/check_trailing_commas.py --check docs/spec-044-debug_extension-0_0_14.md docs/spec-044-debug_extension-0_0_14-rationale.md` → **exit 0**. Explicit paths only; run pathless it rewrites unrelated `docs/` scratch files.
- **No surviving history narration in the spec:** `grep -n "Revision [0-9]\|Revision-8\|review round\|Worker \|DRY review\|Two independent"` returns nothing. Re-run because this pass edited the spec.
- **Ordinal sweep, re-run after the edits:** `grep -nE "(first|second|third|fourth) alternative|alternatives\)\.|\) alternatives|rejected alternative"` over the spec returns exactly one line — `:110`, the deliberative-layer pointer, which names the rationale file. That is the intended sole survivor.
- **`git status --short`** unchanged in shape from the review: `M docs/feedback.md`, `M docs/spec-044-debug_extension-0_0_14.md`, `D to-many-search-optimizer-reproduction.md`, plus the three untracked cycle files. Both baseline-dirty entries were neither edited nor reverted.

### Byte counts

| File | Pre-move (HEAD) | After pass 1 | After pass 2 |
|---|---|---|---|
| `docs/spec-044-debug_extension-0_0_14.md` | 205,905 | 185,272 | **185,518** (+246; 2,836 → 2,840 lines) |
| `docs/spec-044-debug_extension-0_0_14-rationale.md` | — | 41,407 | **43,859** (+2,452; 666 → 672 lines) |

The spec is **20,387 bytes** below HEAD, so the move's purpose is intact: the +246 is three reworded citations and one restored clause. `git diff --numstat` on the spec now reads **63 insertions, 396 deletions**.

The rationale's +2,452 is the price of the corrections being recorded rather than made silently: the de-ordinalized rulings, the retraction definitions and two marked table rows, and two new change-record bullets. None of it duplicates deliberation.

### Failability proofs

None; this pass introduced no new boundary. It edits two markdown files and no executable code. `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to boundaries.

### Hot-path budget

Not applicable; plan declares `Hot-path declaration: none.`

### Floor verification

Not applicable; plan declares `Floor-verification scope: none.` No residual item touches a Django / Strawberry / channels integration seam, so this pass owes no floor run and no version-dependent reasoning.

### Dispatched findings checklist — audit of this pass

All 27 boxes were already `- [x]` when this pass opened, and none is deferred, so nothing needed ticking. Two boxes' **assertions** were falsified by the review and are corrected in place, each marked inline as pass 2's: the cross-reference-sweep box (two instances claimed, five actual) and the retraction box (one claimed, three actual). Every other box's contract was re-checked against the current working-tree diff and still holds — in particular the "deleted nothing under rule 2" box, since this pass moved no further text and deleted no prose; and the "no package source / test / generated doc touched" box, re-confirmed against `git status --short`.

### Spec changes made (Worker 1 only), pass 2

Line ranges as numbered **after** the edits, since the pre-edit file is the pass-1 working tree rather than HEAD.

- `docs/spec-044-debug_extension-0_0_14.md:1611-1614` — Decision 10's citation of Decision 4 changed from `third alternative` to "rejection of wrapping `CaptureQueriesContext` directly". The move removed the second of three bullets and falsified the ordinal (Worker 3, Medium 1).
- `:1560-1562` — Decision 9 ground 1's `([Decision 7] alternatives)` now names the rejected `resolve` hook and links `[rationale-d7]`. Decision 7's alternatives block moved out of the spec in full; a reference into moved text must name the rationale file (rule 3).
- `:1919-1923` — DRY D-N4's `[Decision 8]'s rejected alternative` now cites Decision 8's retained wire-casing table and links the casing-helper rejection at `[rationale-d8]`. Same reason.
- `:1841-1844` — DRY D6's no-`__init__` escape regained the clause "`execution_context` passthrough only, never a `**kwargs` sink". Its only pre-move home was the Revision-5 chronology, so the move took a future-writer constraint out of the spec entirely (Worker 3, Low 1).

Rationale-file edits are Worker 1's too but are not spec changes; they are enumerated under `### Files touched` and per finding above.

Status-line re-verification (`worker-1.md` `## Spec status-line re-verification`): re-read `:1-115`. The `Status:` line at `:74` (**COMPLETE**, card `DONE-044-0.0.14`, three slices built, the joint cut applied) is accurate and this pass did not falsify it. The stale opener at `:3` and the future-tense Slice-2/Slice-3 narration at `:104-108` are **item R2's declared contract** and were verified-and-left, exactly as pass 1 ruled; the per-spawn duty is discharged by verifying and recording, never by editing across an item boundary.

### Notes for Worker 3 (re-review)

- The three checks Worker 3 named for pass 1 all still apply, and two now have a wider target: the ordinal/positional sweep should be re-run over **both** files with the second grep this pass added (the vocabulary of moved text — `reject`, `alternativ`, `justificat`, `considered` — not only chronology vocabulary), because that grep is what found instances 3-5 and its absence is what let the first one through review.
- Two claims in this report are the cheapest to falsify and the most worth distrusting: that the nine verified-and-rejected references genuinely resolve to **retained** text, and that every numbered ground citation resolves to the ground's text rather than merely to a surviving number. Both were checked by reading each target; neither is mechanically provable by a grep.
- `link_check.py` from Worker 3's pass-1 probe set covers anchors, ref/def symmetry, and cross-file anchor resolution in one pass and is directly re-runnable here; this pass wrote an equivalent probe in its own scratchpad rather than reaching into `docs/builder/temp-tests/`.

### Notes for Worker 1 (spec reconciliation) — carried forward unchanged

Pass 1's R2 and R3 hand-offs stand, and Worker 3's additions to them stand. Nothing in this pass changes them, with one addition for R3: the spec now carries **three name-based citations** (`:1562`, `:1613`, `:1921`) that exist precisely because an ordinal did not survive a move. R3 must not convert any of them back to a positional form while re-relativizing, and the reason is recorded in the rationale's non-decision change record so it survives this artifact.

---

## Review (Worker 3, pass 2)

Re-review of the custodian apply pass. Same method as pass 1: every claim re-derived mechanically, none accepted on prose. Where pass 2's report says a thing was "verified rather than trusted", that is exactly the sentence this pass re-verifies.

**One new instrument this pass.** Pass 1's probes compared the working tree against HEAD, which cannot isolate what pass 2 changed. So the pass-1 spec was **reconstructed** — `git show HEAD:… > spec.head.md`, `cp` to `spec.pass1.md`, `patch` with the pass-1 diff captured last review, byte-count confirmed at **185,272** — and diffed against the current file. That makes pass 2's spec delta exactly auditable rather than inferred from a byte total, and it is what answers claim 4 directly.

### Audit scope and what does not apply

- **`### Failability proofs` — does not apply.** No boundary, guard, gate, or rejection path exists in a two-file markdown diff; the re-run floor is arithmetically zero, not a chosen subset.
- **`### Hot-path budget` — does not apply.** Plan declares `none`; the delta contains no executable line.
- **No `pytest`.** Nothing changed is executable. Pass 2 reaching the same conclusion for the same stated reason is correct, not a skipped obligation.
- Probes: pass 1's `loss_check2.py`, `copy_check.py`, `link_check.py`, `order_check.py` re-run against the pass-2 diff, plus `spec.head.md` / `spec.pass1.md` / `spec.pass2.diff` and inline `python3` probes, all under `docs/builder/temp-tests/044-r1/`.

### High:

None.

### Medium:

None. The pass-1 Medium is closed, and closed wider than filed.

**Claim 1 — the class was four instances, verified.** `:1613` now reads "rejection of wrapping `CaptureQueriesContext` directly"; the two the pass-1 sweep could not see are real and both now resolve to **retained** text with the rationale named: `:1560-1562` (Decision 9 ground 1 → "Decision 7's rejected `resolve` hook: [rationale companion]") and `:1919-1923` (DRY D-N4 → "Decision 8's wire-casing table, with the casing-helper rejection recorded in the [rationale companion]"). Both targets exist: Decision 7's rationale entry carries the `resolve`-hook rejection, and Decision 8 retains the six-key table whose `isSlow` / `isSelect` rows are precisely what D-N4's wire-contract claim rests on. `[rationale-d7]` / `[rationale-d8]` were already defined and already used, and `link_check.py` confirms **no definition was added, removed, or left unused** in either file. The post-edit ordinal sweep reproduces exactly: `grep -nE "(first|second|third|fourth) alternative|alternatives\)\.|\) alternatives|rejected alternative"` over the spec returns **one line, `:110`**, the deliberative-layer pointer.

**The grounds class ruling — re-derived, not accepted, because pass 1 took it from the mover.** Enumerated every `N. **` list inside every decision section programmatically: Decision 3 → 1-5, Decision 4 → 1-4, Decision 5 → 1-3, Decision 6 → 1-4, Decision 7 → 1-3, Decision 9 → 1-3, all **contiguous**, plus Decisions 8 and 10's prose grounds — the "all eight" of the report. Then resolved every ground citation in the rationale to the ground's **text**: D3's `_debug`-field rejection → ground 2 "No schema pollution and no `Meta` growth. A `_debug` field would need…" (the ground argues against that exact field, so "everything in ground 2" is true, not merely numerically valid); D5's package-root rejection → ground 2 "The subpackage-not-root export…", and "Ground 3's eager-re-export instruction stayed" → ground 3 "Eager re-export, no lazy machinery"; D7's `get_results` rejection → ground 2 "Teardown is the only point that is both complete and ordered", its async-twin rejection → ground 1 "A sync generator serves both execution colors"; D9's per-field rejection → ground 1, its ungated-errors rejection → ground 2; and the rationale's `## Current state` premise citation "[Decision 7] ground 2" → that ground's body, which does carry the verified call ordering with its `[Current state]` link. Also confirmed as a by-product: the Test plan's scenario list is contiguous 1-21, so judgement call 12's append-never-renumber rule is intact. **Zero drift.** The claim is true and is now checked.

**The nine already-resolving references — spot-checked all nine, all resolve to retained text.** `:272-273` / `:2543` and `:741` land on Decision 3's retained title and grounds (ground 2 is itself an argument against a `_debug` field, so "rejected with reasons in Decision 3" is not a dangling promise); `:856`, `:1217`, `:1884`, `:2410` land on Decision 4's **retained** cursor-wrap-port bullet — `:1884`'s "`([Decision 4] alternatives)`" is the same *shape* as the two that were fixed and is correctly classified differently, because Decision 4 still has alternatives and one of them is exactly the `sql/tracking.py` port D-N3 cites; `:1574`'s "the rejected per-field wrapper" is stated normatively in Decision 9 ground 1 and in the decision's own title; `:2087` "Considered and rejected." is self-contained.

**The moved-text in-page reference ("the trap above")** is handled correctly. Moved text is verbatim by contract, so editing the bullet was not available; making the referent explicit in the framing a reader hits first is the right remedy, and it asserts nothing new — the two statements it names (Decision 4's body at `:1195-1196`, `## Current state` at `:643-644`) are the two the framing already cited and both are retained.

### Low:

Two, both about the **artifact record only** — neither touches the spec or the rationale, and neither blocks acceptance (disposition stated in `### Review outcome`).

#### 1. The Risks-reference enumeration reads as exhaustive but lists 6 of 11, and three line pins drift

`### Worker 3's findings, one by one` says "Every `[Risks](#risks-and-open-questions)` reference was also re-resolved against the six surviving risks" and then enumerates six sites. The spec carries **eleven** such references: `:272`, `:769`, `:791`, `:1263`, `:1797`, `:2009`, `:2104`, `:2132`, `:2180`, `:2628`, `:2630`. I resolved the five unlisted ones myself and **none dangles** — `:2009` and `:2630` reach the surviving "Cross-operation SQL attribution" risk (the one whose retraction moved and whose fallback sentence stayed, i.e. the most exposed of the eleven), `:2104` / `:2132` / `:2628` reach the payload-size / knobs risk. So the conclusion is sound; the enumeration is partial while worded as complete. Three pins are also off by 1-4 lines against the current file: `:1796` → `:1797`, `:2176` → `:2180`, `:2083` → `:2087` (raw `path:NN` is permitted in a per-cycle scratchpad, and each hit's quoted text is unambiguous, so this is accuracy not ambiguity).

Recommended: reword to "the six that name a moved-item candidate; the remaining five resolve to the payload-size / attribution risks", and re-pin the three. **Or** record a rejection reason — the finding is about how the record reads, not what it concluded.

#### 2. The byte-count checklist box still carries the pass-1 figure

`### Dispatched findings checklist` `:99` reads "The spec's byte count before and after is reported (205,905 -> 185,272)." Pass 2 moved the after-count to **185,518** and corrected two neighbouring boxes' assertions in place, marked as pass 2's — so an untouched parenthetical in the same list now reads as current when it is a pass-1 measurement. The box's *contract* still holds (the counts are reported, in the pass-2 byte table), which is why this is Low and not a mis-tick.

Recommended: extend the parenthetical to "205,905 -> 185,272 (pass 1) -> 185,518 (pass 2)", in the same marked-inline style as the other two corrections. Or record a rejection reason.

### DRY findings

- **The one duplication pass 2 deliberately created is the right one, and is recorded as a change rather than left to look like a copy.** The `**kwargs` clause now exists as a **rule** in the spec (`:1841-1844`, imperative, at the site that binds a future writer) and as a ~14-word **quotation** in the rationale's new change-record bullet, framed explicitly as "Revision 5's account above is the provenance, not a second copy of the rule". That is the correct split: the shorter quotation is what makes the bullet falsifiable, and dropping it would make the record unverifiable. Verified the spec's clause is not a lift of the chronology sentence — the chronology says "the no-`__init__` rule keeps the first review's default with the second's constrained escape (…)", which is a narration; the spec says "initialize only that configuration — `execution_context` passthrough only, never a `**kwargs` sink — and do not claim that …", which is a rule.
- **Move integrity re-verified after pass 2's edits, all three directions.** `copy_check.py` (12-word sliding window over the whole rationale against the whole spec) still finds only the twelve legal overlaps — eleven mirrored `### Decision N` headings plus the one quoted surviving fallback sentence the rationale explicitly labels as "what remains there". So the rationale's **+2,452 bytes brought no spec text back into it**. `loss_check2.py` against the pass-2 diff shows the only newly-unaccounted removed lines are the four pass-2 edits' own retired text (`   alternatives).`, `third alternative…`, `  configuration and do not claim that`, `  rejected alternative); …`), each with its replacement in the added set — nothing lost, nothing deleted.
- No new abstraction, convention, or link definition was introduced by either file's pass-2 edits.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **0 lines**; `__all__` and the re-export list untouched. `git status --short` is unchanged in shape from pass 1 — `M docs/feedback.md`, `M docs/spec-044-debug_extension-0_0_14.md`, `D to-many-search-optimizer-reproduction.md`, plus the three untracked cycle files. No package source, test, `examples/`, `scripts/`, `pyproject.toml` / `uv.lock` / `CHANGELOG.md` / `docs/GLOSSARY.md` / `docs/TREE.md` / `KANBAN.*`, no other `docs/spec-*.md`, no preserved spec-046 `bld-*.md`. Both baseline-dirty entries neither edited nor reverted by this review.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

**Claim 4 — the growth is exactly the four edits, proven by reconstruction rather than by arithmetic.** `diff -u spec.pass1.md docs/spec-044-debug_extension-0_0_14.md` returns **four hunks and nothing else**: the `:1562` citation, the `:1613` de-ordinalization, the `:1841` restored clause, and the `:1921` citation. No deliberation returned, no block re-appeared, no pointer changed. The spec is **185,518** bytes — 20,387 below HEAD, so the move's purpose is intact — and `git diff --numstat` reads 63 insertions / 396 deletions. Rationale **43,859**.

Every other recorded verification re-run and reproduced:

- `uv run python scripts/check_spec_glossary.py --spec …` → `OK: 42 terms - all have glossary entries and at least one spec link.`, **exit 0**.
- `uv run python scripts/check_trailing_commas.py --check` on **all three** touched `.md` files (spec, rationale, this artifact) → **exit 0**.
- **In-page anchors:** spec **200 occurrences across 26 distinct targets, 0 broken**; rationale **2 uses, 0 broken** (the new one is the index's link into the Risks change record). This reconciles pass 2's "200" against my pass-1 "26" exactly as its note predicted — occurrences vs distinct targets — and both passes agree on zero broken, which is the number that matters.
- **Ref/def symmetry both directions:** spec 103 uses / 102 defs, 0 unused, one "undefined" hit `]["sql"]` — the `res.extensions["debug"]["sql"]` code span, the same pre-existing probe false positive all three passes have recorded. Rationale **28 / 28, 0 undefined, 0 unused**. Every non-URL definition in both files resolves to a file on disk and every `#anchor` to a real heading, `GLOSSARY.md#django-trac-37064-hardening` included — so Low 1 of pass 1 being fixed did not disturb the anchor the glossary check depends on.
- **No history narration in the spec:** the recorded grep returns nothing, re-run after the edits.
- **Low 3 fixed and character-exact, verified against HEAD rather than by eye.** Both quoted Test-plan labels — `"scenarios 8–15 and the Revision-8 additions 17–21 live in \`tests/extensions/test_debug.py\`"` and `"**Revision-8 additions (16 live-sharded; 17–21 mechanics):**"` — are now present in the rationale **and** present in the HEAD spec under whitespace-flattening, and none of the three ASCII-hyphen variants remains anywhere in the file.
- **Low 4 fixed:** the two non-decision entries now read `` [`## Test plan`][s44-test-plan] `` and `` [`## Helper-reuse obligations (DRY)`][s44-dry] ``, and the section opener's now-wrong "Three corrections" count was dropped rather than left to rot — a correction I had not asked for and which is right.
- **Low 2 fixed, both halves, counts confirmed against the chronology.** The index gains a lead-in defining **Retracted**, stating three, and linking the third to `## Change record for Risks and open questions`; the Decision 4 row carries the bounded-log clamp *guarantee* retraction and the Decision 6 row the byte-identical / off-by-default overclaim, each naming where the replacement is normative. I re-confirmed there is no fourth: the only other Revision-2/7/8 "replaced/corrected" entries change contracts rather than retract claims a decision may no longer make.
- **Checklist boxes (claim 3):** both corrected assertions are right — five cross-reference instances (two `Revision-8` labels from pass 1 plus the three citations) and three retractions — and both are marked inline as pass 2's. Walked all 27 boxes against the current diff: **no box is ticked whose contract did not land**, and none is deferred. One box's parenthetical is stale, which is Low 2 above, not a mis-tick.
- No script-rendered doc, no KANBAN movement, no archival, and no obsolete "coming soon" / "planned" wording introduced by this pass.

### What looks solid

- **The apply pass treated a filed instance as a filed *class*, and that is what a rule-3 sweep is for.** The second grep — the vocabulary of moved text (`reject`, `alternativ`, `justificat`, `considered`) rather than chronology vocabulary — is the correct generalization of my finding, and it is the grep whose absence let the first instance through my own pass 1. Finding one defect and returning four fixes, with nine near-misses enumerated as verified-and-rejected so a later pass does not re-flag them, is the shape that makes a re-review cheap.
- **Every prescription was assessed before it was applied, and one was upgraded.** Medium 1's fix was accepted only after confirming the citation's claim ("no connection is force-opened") traces to ground (a) of the `CaptureQueriesContext` rejection, i.e. that the *named* target is the right one. Low 1 was fixed where I had judged it rejectable, and the reasoning is better than mine: D6's "initialize only that configuration" genuinely does not forbid widening the signature, and the clause binds the future writer at the one site that writer will read.
- **The de-ordinalization was made self-defending.** Both files now close the ruling with why a name is used, and the R3 note repeats it — so the next pass, which will rewrite every path in both files, has the reason in front of it rather than in a closed artifact.
- **Two claims flagged as "cheapest to falsify" were the two I re-derived hardest**, and both held. A pass that names its own weakest evidence and is then right about it is the opposite of the self-convincing verification this review exists to catch.

### Temp test verification

- Files used, all under `docs/builder/temp-tests/044-r1/` (gitignored): `spec.head.md`, `spec.pass1.md` (reconstructed by `patch`, byte-verified at 185,272), `spec.pass2.diff`, plus pass 1's `loss_check2.py` / `copy_check.py` / `link_check.py` / `order_check.py` re-run and one-off inline probes for grounds contiguity, quoted-label fidelity, and anchor-occurrence reconciliation.
- Disposition: **kept for the cycle, not promoted.** None catches a code-behaviour bug, so the promotion rule does not fire. The reconstruct-the-prior-pass technique (`git show HEAD` + `patch` with the previous pass's captured diff) is the transferable part and is worth reaching for whenever an untracked or multi-pass file has to be diffed against its own earlier state — recorded in worker memory.
- No source file mutated; the failability carve-out was not exercised, there being no boundary to mutate.

### Notes for Worker 1 (spec reconciliation)

- **Nothing escalated.** No Medium-or-higher finding remains; both Lows are artifact-record corrections Worker 1 owns and can fold into final verification (see `### Review outcome`).
- **R2 and R3 hand-offs unchanged, and no new instance of R2's class surfaced in this pass's delta.** The four spec edits touch Decision 9's grounds, Decision 10's prose, DRY D6, and DRY D-N4 — none of them narrates shipped work in future tense. The stale opener at `:3`, the future-tense Slice-2/Slice-3 narration at `:104-108`, and the `## Current state` bullets shipping falsified all remain R2's, verified-and-left, exactly as both prior passes ruled.
- **For R3, one addition to the existing caution.** Beyond not re-ordinalizing the three name-based citations, the archive sweep should re-run an **anchor-resolution** pass (not just a file-exists pass) over both files afterwards: the rationale's `[glossary-django-trac-37064]` definition is what keeps `check_spec_glossary.py`'s 42nd term reachable from the spec side's sibling link, and `[s44-*]` / `[rationale-*]` are 33 in-file-to-sibling anchors that a path-only rewrite can leave pointing at a real file and a dead heading. `link_check.py` does both in one run.

### Review outcome

`review-accepted`.

All five pass-1 findings are fixed — one Medium and four Lows — and the Medium came back as four instances plus nine enumerated near-misses. Nothing was rejected, no moved passage needs to return, and the two claims pass 2 itself named as least mechanically provable (the nine already-resolving references; the grounds-by-text resolution) were both re-derived independently and both hold. The spec's pass-2 delta is provably the four edits and nothing else.

The two new Lows are **recorded as addressed at final verification rather than by a re-loop**, and this is the recorded reason: both are corrections to this artifact's own prose — a partial enumeration worded as exhaustive, and a stale parenthetical in a checklist box — not to the spec or the rationale, which are the deliverables. I verified the substantive claim behind Low 1 myself (all eleven Risks references resolve; none dangles), so re-looping Worker 1 for the wording would buy no correctness. Worker 1 owns this artifact at the very next pass and can correct both in the same marked-inline style already used for the two box assertions, or record a rejection reason; either closes them.

---

## Final verification (Worker 1)

The accepting pass. A same-named heading already stands at the pass-1 position above, carrying that pass's `### Spec changes made (Worker 1 only)` record under a `*Pending*` placeholder; it is **left unedited** (`docs/builder/ARTIFACT.md` `## Re-pass sections`: never edit prior entries), so the artifact still reads as a linear plan / review / apply / review / final-verification sequence. This section is the pass that rules.

**Nothing in this pass was accepted on prose.** `worker-1.md` `### Verifying relocation / promotion claims` makes R1 wholly a relocation claim and gives this pass an explicit delta — run the proof yourself rather than reading Worker 3's acceptance as discharge — so every gate, every count, and the move-not-copy proof below were re-derived from the working tree. Where a re-derivation disagrees with a recorded figure, the disagreement is stated rather than reconciled silently.

### The relocation proof, re-run

`git show HEAD:docs/spec-044-debug_extension-0_0_14.md` into a scratch path **outside** the repo (never `git stash` / `checkout` / `restore` / `worktree` — `BUILD.md` `## Verifying a pre-existing-at-HEAD claim`, and the maintainer runs concurrent sessions against this tree). HEAD spec measures **205,905** bytes; the working tree measures **185,518**; the rationale **43,859**. `git diff --numstat` reads **63 insertions / 396 deletions** across **27 hunks**.

**Every one of the 396 removed lines is accounted for**, by a whitespace- and link-normalized probe over both files (in-page `](#…)` and `][ref]` syntax flattened, en/em dashes folded, so a rewritten anchor still matches its source):

| Disposition of a removed line | Count |
|---|---|
| Present in the rationale (moved) | 366 |
| Still present in the spec (re-wrapped, attribution stripped) | 7 |
| Too short to be distinguishing (blank, `-`, fragments < 8 normalized chars) | 14 |
| Unaccounted by the line probe, resolved individually below | 9 |

The nine are the retired halves of the four pass-2 edits (`   alternatives).`; `third alternative, no connection is force-opened…`; `  configuration and do not claim that`; `  rejected alternative); \`errors.field_error\`…`), the two DRY-preamble attribution lines, the D3 `Sharpened by the DRY review:` lead-in, the one Test-plan label whose retired text the rationale quotes, and the one Risks bullet **split** between the two files. Each was resolved by phrase probe rather than by line match, and each has exactly one home:

- `Two independent, simultaneously-written reviews` / `(2026-07-11)` — absent from the spec, **present in the rationale's non-decision change record**, quoted inside the bullet that records the attribution's move. Box 16's "moved" therefore holds; the probe missed it only on sentence case.
- `schema fixture depends on` — **retained in the spec**; only `Sharpened by the DRY review` left it (now `Sharpened to specifics`, and the retired lead-in is quoted in the rationale). The specifics the lead-in introduced all stayed.
- `initialize only that configuration` + `never a **kwargs** sink` — **both in the spec** at `:1841-1844`, and the clause is a ~14-word quotation in the rationale framed as provenance. The one deliberate two-file sentence, recorded as such.
- `async consumers report gaps.` — **retained in the spec**; `An earlier draft's categorical rejection` — **only in the rationale**. The split is exactly where the pass-1 record says it is.
- `third alternative` — present in **neither** file. The falsified ordinal is gone rather than relocated, which is the correct outcome for text a move invalidated.

**Move, not copy — re-derived, and my count differs from Worker 3's.** A 12-normalized-word sliding window over the whole rationale against the whole spec (fences stripped, link syntax flattened, punctuation folded) finds **30 shared runs**, not the "twelve legal overlaps" the pass-2 review records. Every one is legitimate, so the *verdict* is identical and the *characterisation* was understated:

- **11 mirrored `### Decision N — …` headings** — required by the keying contract (Decision 1's is under the window length).
- **11 `[s44-dN]` link-definition lines** plus 3 more definition-block runs (`[next]` / `[spec-038]`, the two upstream-cookbook paths, the graphene debug-middleware path). Anchor slugs are *derived from* the headings and shared targets are shared by construction; a link definition is not prose.
- **5 framed quotations**, each labelled in the rationale as what stayed: the DRY headline (`almost nothing in utils/ is directly callable…`), the Test-plan numbering rule, the surviving Risks fallback sentence, Decision 10's now-name-based citation, and the `**kwargs` clause.
- **1 chronology-vs-normative clause** — the coordinator's two-seam pin (`as methods or as one per-connection context manager (the pin is …)`), where the rationale's Revision-4 narration and the spec's `:1810` rule share a clause. Two different sentences, one an account and one a rule; the same shape already ruled correct for `**kwargs`.

**No moved block exists in both files.** That is the claim step 4 exists to catch, and it holds. Since R1 is the cycle's first item there are no prior accepted slices to check for cross-slice duplication, so step 4's question was the internal one and this is its answer.

### Failability and fail-open checks

Confirmed from the diff rather than assumed. The diff contains **no `.py` file, no executable line, and no new boundary, guard, gate, or rejection path** — `git status --short` shows exactly two markdown deliverables plus this artifact, and the 27 hunks are prose, pointer lines, and link definitions. `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to boundaries, so **no failability proof is owed** and the re-run floor is arithmetically zero rather than a chosen subset. Read for the catalogued **fail-open shapes** as well (clamp, `getattr` default, `or` fallback, bare `except`, truthiness on an absent value): none can exist, there being no expression in the diff to carry one.

### Step 3 — the `### Dispatched findings checklist` audit

All 27 boxes read `- [x]` and none is deferred, so nothing needed ticking and nothing was un-ticked. **Every box's contract was confirmed against the working tree, not against the prior passes' reports.** No `- [ ]` remains, so `### Spec changes made (Worker 1 only)` owes no deferral reason. What each confirmation rested on:

- **File, scaffold, keying (boxes 1-2).** The rationale exists, is **not** matched by `git check-ignore` (so it is tracked-on-commit, not scratch), and carries `<!-- LINK DEFINITIONS -->` plus all ten canonical group headers in the exact prescribed order, empty ones present. Twelve `### Decision N` entries and the Risks change record open with a linked `Spec:` line — 13 in all. The two change-record sections carry no `Spec:` line of their own by construction (one is keyed to revisions, one to no single section) and every bullet inside them now names *and links* its spec section, except the revision-history bullet, whose subject is the spec's header block and has no anchor to link. "No entry that cannot be looked up" holds.
- **The chronology (boxes 3, 18).** All eight revisions are present in the rationale as `- **Revision 1**` … `- **Revision 8**`, and `grep -nE 'Revision [0-9]|Revision-8|review round|DRY review|Two independent'` over the spec returns **nothing** — the block left the spec entirely. `### Which revision changed which decision` indexes all twelve decisions.
- **The twelve decisions (boxes 4-15).** Twelve italic pointer lines survive in the spec (`:1109`, `:1136`, `:1179`, `:1282`, `:1325`, `:1394`, `:1471`, `:1517`, `:1589`, `:1622`, `:1653`, `:1692`), and **each box's count matches the pointer's own enumeration and the rationale entry's bullets**: D1 2, D2 1 + the justification, D3 2, D4 1-of-3, D5 3, D6 3, D7 3, D8 4, D9 3, D10 2, D11 3, D12 2. Decisions 2 and 10 carry their alternatives as inline bold prose rather than list items — verbatim, as they stood in the spec — which is why a bullet count alone under-reads them.
- **Decision 4's carve-out (box 8, judgement calls 1-3).** Re-derived mechanically, because it is the one box a glossary check can falsify: `grep -n 'django-trac-37064'` over the spec finds **exactly one** body use, `:1258`, inside the retained `Port graphene's cursor wrap` bullet, and row 41 of the terms CSV names it ("the cursor-wrapping hazard precedent in Decision 4's rejection"). `check_spec_glossary.py` resolves anchors from `--spec` only, so moving that bullet would have failed the check. Decision 4 now retains exactly **two** alternatives, so the surviving pointer's "the two alternatives above" is accurate.
- **DRY and Risks (boxes 16-17).** The DRY pointer stands at `:1960-1961` and the Risks pointer at `:2605-2608`, the latter naming both moved items **and** the retraction's one surviving obligation (decide the follow-on against a real ASGI-request prototype). The rationale's Risks change record carries both moved items in full.
- **Retractions (box 19, pass 2's corrected assertion).** Three, as corrected: the index lead-in defines **Retracted**, states three, marks the Decision 4 row (bounded-log clamp *guarantee*) and the Decision 6 row (byte-identical / off-by-default overclaim), and links the third (the async universal-executor premise) into the Risks change record. All three verified present in the chronology.
- **Deleted nothing (box 20).** The 396/396 accounting above is the proof: no removed line lacks a home. Rule 2 was correctly not exercised — the move deleted no prose, because nothing classified as move material had been falsified by a *decision*.
- **Cross-references (box 21, pass 2's corrected assertion).** Five, as corrected. Verified by a **whitespace-flattened** sweep rather than the line-oriented one the prior passes ran, which matters: the recorded grep "returns exactly one line, `:110`" is line-oriented and therefore **structurally blind to a citation broken across a line wrap**. Flattened, the spec carries one more hit — `([Decision 4] alternatives)` at DRY D-N3, `:1884-1886` — and it is the instance the pass-2 report classified as correctly retained. That classification is right: Decision 4 keeps the cursor-wrap-port bullet, and that bullet is the one naming `sql/tracking.py`, which is exactly what D-N3 cites. So the *conclusion* survives the better probe; the probe recorded as proving it does not, and that is worth carrying forward. The three name-based citations all read correctly at `:1562`, `:1613`, `:1924`, each resolving to retained text and the latter two naming the rationale file. No `ground [0-9]` positional citation survives anywhere in the spec.
- **The four gates (boxes 22-25).** Re-run, below.
- **Byte counts (box 26).** Corrected in place; see Low 2.
- **Scope (box 27).** `git status --short` confirms it: `M docs/feedback.md`, `M docs/spec-044-debug_extension-0_0_14.md`, `D to-many-search-optimizer-reproduction.md`, `?? docs/builder/bld-044-r1-rationale_move.md`, `?? docs/builder/build-044-debug_extension-0_0_14.md`, `?? docs/spec-044-debug_extension-0_0_14-rationale.md`. No package source, test, `examples/`, `scripts/`, `pyproject.toml` / `uv.lock` / `CHANGELOG.md` / `docs/GLOSSARY.md` / `docs/TREE.md` / `KANBAN.*`, no other `docs/spec-*.md`, no preserved spec-046 `bld-*.md`. No commit, no branch. The two baseline-dirty entries are the plan's declared ones and were neither edited nor reverted (`AGENTS.md` rule 34).

### The verification gates, re-run in this pass

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-044-debug_extension-0_0_14.md` -> `OK: 42 terms - all have glossary entries and at least one spec link.`, **exit 0**.
- **In-page anchors, both files** (fences stripped line by line, GitHub-style slugs — backticks stripped, `_` kept, punctuation dropped, each space to one hyphen, duplicate headings suffixed): spec **200 occurrences across 26 distinct targets, 0 broken**, against 35 headings; rationale **2 occurrences, 0 broken**, against 20 headings. Reconciles both prior figures — 200 is occurrences, 26 is distinct targets — and agrees on the number that matters.
- **Ref/def symmetry, both directions:** spec **102 definitions, 0 unused**, one "undefined" hit `"sql"` — the `res.extensions["debug"]["sql"]` code span, the same pre-existing false positive of the `][…]` probe all three prior passes recorded. Rationale **28 definitions, 0 undefined, 0 unused**.
- **Cross-file definition targets and anchors:** every non-URL definition in **both** files resolves to a file that exists on disk **and** to a real heading in that file, `GLOSSARY.md#django-trac-37064-hardening` included. The spec's fifteen `rationale*` definitions sit in correct alphabetical position inside the `<!-- docs/ -->` group, between `[glossary-testclient]` and `[tree]`; the bare `[glossary]` entry sitting after the `glossary-*` block is a **pre-existing** ordering at HEAD, not this pass's doing.
- `uv run python scripts/check_trailing_commas.py --check docs/spec-044-debug_extension-0_0_14.md docs/spec-044-debug_extension-0_0_14-rationale.md docs/builder/bld-044-r1-rationale_move.md` -> **exit 0**. Explicit paths only; run pathless it rewrites unrelated `docs/` scratch files.
- **Test-plan scenario numbering contiguous 1-21**, so judgement call 12's append-never-renumber rule is intact after the two label rewordings.

### Step 5 — focused tests: none to run, and the reasoning rather than a run

The plan declares **floor-verification scope `none`** and **hot-path `none`**, and nothing R1 touched is executable: the diff is two markdown files. A `pytest` invocation here would confirm only that the tree at large is green — a property this item cannot affect and the final gate owns — so the honest record is the reasoning, not a run performed for form. No `--cov*` flag was used in this pass, as `BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool` requires of every pass. No `ruff` run: no `.py` file was touched.

### Step 6 — the staged-anchor sweep

`grep -rEn 'TODO\(spec-044|TODO-(ALPHA|BETA|STABLE)-044' .` (correct milestone spellings; `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` excluded, where `TODO-<MILESTONE>-<NNN>` legitimately names a board card).

**Confirmed: no staged anchor survives in package source or tests.** Zero hits under `django_strawberry_framework/`, `tests/`, `examples/`, or `scripts/` — Worker 0's pre-flight finding, independently reproduced. Card 044 shipped, so that is the required result and no anchor is owed removal by this cycle.

Every surviving hit is documentation, in three classes:

1. **Historical, correct.** `docs/SPECS/spec-041-…`, `spec-042-…`, `spec-043-…` and the two archived terms CSVs reference `TODO-ALPHA-044-0.0.14` as the sibling card's id **at the time those specs were authored**. Archived specs are the historical record; nothing is owed.
2. **spec-044's own prose, R2's to rule on.** `:428`, `:431` (the `## Slice checklist` steps that *created* the anchors) and `:453`, `:577`, `:579` (the `docs/TREE.md` `planned by TODO-ALPHA-044-0.0.14` reservation, in `## Doc updates` and `## Current state`). R1 falsified none of these; they are exactly the shipping-falsified `## Current state` / `## Doc updates` surface item **R2** owns, and pass 1's hand-off already routed them.
3. **A live sibling spec asserting something 044's shipping falsified — outside this pass's writable set.** `docs/spec-050-debug_extraction-0_0_19.md:390` and `docs/spec-051-boundary_dry_squeeze-0_0_20.md:556` both read that "the version-quintet sites **currently carry** `TODO(spec-044 Slice 3)` anchors owned by the **in-flight** `0.0.14` cut", and each conditions its own anchor-staging on 044's cut landing "and removing them". The cut landed on 2026-07-20, the anchors are gone, and the caveat's precondition is discharged — so both sentences are now false in tense and in fact, and each is load-bearing for a future author deciding when to stage anchors. Neither file is writable by this pass (the plan and the prompt both scope R1 to spec-044 and its rationale), so this is **recorded for the `### Deferred work catalog`** in `bld-044-final.md`, not acted on. It is not R2's either: R2's contract is spec-044's own documentation.

### Worker 3's two pass-2 Lows — disposition

Both were routed here deliberately rather than re-looped, and both are **fixed**. Neither touches the spec or the rationale.

**Low 2 (the stale byte-count parenthetical) — FIXED IN PLACE.** The `### Dispatched findings checklist` is this pass's audit surface, so correcting the figure there is licensed exactly as pass 2's two assertion corrections were. The box now carries all three measurements, marked as final verification's, and each was re-measured with `wc -c` rather than copied: 205,905 / 185,272 / 185,518.

**Low 1 (the Risks-reference enumeration reads exhaustive but lists 6 of 11; three pins drift) — FIXED HERE, NOT IN PLACE, and the placement is the ruling.** The stale prose sits in `## Build report (Worker 1, pass 2 — custodian apply)`. `ARTIFACT.md` `## Re-pass sections` forbids editing a prior entry, and the licensed exceptions are the checklist boxes and the byte-count figure — not a prior build report's body. So the correction is **published here**, where the artifact as a whole carries the accurate record and the pass sequence stays readable. Worker 3's substantive claim was **re-verified independently rather than accepted**:

- The spec carries **eleven** `](#risks-and-open-questions)` references, at `:272`, `:769`, `:791`, `:1263`, `:1797`, `:2009`, `:2104`, `:2132`, `:2180`, `:2628`, `:2630` — exactly the set Worker 3 lists.
- **Six risks survive** in `## Risks and open questions` (`:2525` exposure selectivity, `:2538` the cookbook migration, `:2559` cross-operation SQL attribution, `:2575` engine ordering coupling, `:2589` `queries_log` eviction, `:2598` payload size).
- **All eleven resolve to a surviving risk; none points at either moved item.** Read in context: `:272`, `:1797`, `:2180` reach the exposure-selectivity risk's `_debug`-facade fallback; `:769`, `:2104`, `:2132`, `:2628` reach the payload-size / knobs pair; `:791`, `:2009`, `:2630` reach cross-operation SQL attribution (the async follow-on — the most exposed of the eleven, since it is the risk whose *retraction* moved while its fallback sentence stayed); `:1263` reaches the `queries_log`-eviction risk's "a separate fidelity card that changes the capture source" fallback.
- **The corrected sentence** the pass-2 report should have carried: *every `[Risks]` reference was re-resolved — the six that name a moved-item candidate are enumerated there; the remaining five (`:2009`, `:2104`, `:2132`, `:2628`, `:2630`) resolve to the cross-operation-attribution and payload-size / knobs risks. None of the eleven dangles.*
- **The three drifted pins, re-measured against the current file:** `:1796` -> **`:1797`**; `:2176` -> **`:2180`**; `:2083` -> **`:2087`** (`:2083` is the `Introspection is not special-cased.` bullet; `Considered and rejected.` is at `:2087`). The other nine verified-and-rejected pins in that paragraph — `:273`, `:741`, `:856`, `:1217`, `:1574`, `:1884`, `:2410`, `:2543` — all land on the quoted text as recorded.

### Summary

R1 delivered the deliverable the shipped `0.0.14` cycle skipped: spec-044's deliberative layer now lives in `docs/spec-044-debug_extension-0_0_14-rationale.md` (**43,859** bytes, 672 lines, keyed decision-by-decision to the spec), and the spec is **185,518** bytes against **205,905** at HEAD — **20,387 bytes lighter**, a 10% cut off every future spawn's read of it — while remaining a clean current contract that narrates none of its own history.

The move is verified as a **move**: all 396 removed lines have exactly one home, no moved block survives in both files, and the only two-file sentences are five framed quotations and one clause the rationale explicitly labels as provenance. The carve-out the mechanism exists to protect held under mechanical rather than argued test — Decision 4's two retained alternatives, the `django-trac-37064` glossary link that makes one of them unmovable, and the `**kwargs` clause pass 2 returned to DRY D6 after the move had briefly taken a future-writer rule out of the spec entirely. Thirteen judgement calls, one Medium and six Lows across two review passes, all closed. `Status: final-accepted`.

Two things this pass adds to the record rather than inherits. First, the recorded ordinal sweep is **line-oriented and therefore cannot see a citation broken across a line wrap** — a flattened sweep finds one more `([Decision 4] alternatives)` hit, correctly classified but not by the probe credited with classifying it. Second, the recorded copy-check figure ("twelve legal overlaps") is **understated**: there are 30, all legitimate. Both are characterisation gaps rather than defects, and neither changes a verdict — but a relocation is accepted on its proofs, so a proof that is weaker than its record says is worth naming.

### Spec changes made (Worker 1 only)

**None in this pass.** Final verification made no edit to `docs/spec-044-debug_extension-0_0_14.md` or to `docs/spec-044-debug_extension-0_0_14-rationale.md`. Nothing R1 falsified remains unreconciled: the four sites the move invalidated were fixed in pass 2 and re-verified above, and every other candidate belongs to another item.

No box is `- [ ]`, so no deferral reason is owed under `## Final verification job` step 3.

**Deliberately not reconciled, with the reason, so the omission is a ruling and not a silence:**

- **The stale opener at `:3`** (``Planned for `0.0.14` (card [`WIP-ALPHA-044-0.0.14`][kanban])``) and the **future-tense Slice-2 / Slice-3 narration at `:104-108`** are item **R2's** declared contract. `worker-1.md` `## Spec status-line re-verification` obliges me to *verify and record*, not to edit across an item boundary — and R2 is the pass with the `## Doc updates` / `## Definition of done` audit context to rule on the whole header region at once.
- **The `## Current state` bullets shipping falsified** — "No `extensions/` subpackage exists", the `docs/TREE.md` `planned by TODO-ALPHA-044-0.0.14` reservation, the `config/schema.py` docstring quote, "The version line reads `0.0.13`" — same owner. Rule 2 of the move deletes prose *a decision* falsified; shipping is not a decision, and the section is explicitly dated ("as this spec is authored"). Pass 1's judgement call 5 ruled this and it stands.
- **The relative paths in both files' link blocks** resolve correctly from `docs/` today. R3 owns the re-relativization; pre-adjusting them now would break them.

**Status-line re-verification (`worker-1.md` `## Spec status-line re-verification`).** Read `:1-115` at the start of this pass. The `Status:` line at `:74` — **COMPLETE (card `DONE-044-0.0.14`)**, all three slices built, the card-wrap landed, the joint `0.0.14` cut owned and applied — is accurate against HEAD and this pass falsified nothing in it. The opener at `:3` is stale and is R2's, as above.

### Notes for R2 and R3 — carried forward, not acted on

Pass 1's and pass 2's hand-offs stand unchanged, plus:

- **For R2**, the staged-anchor sweep's class 2 above is the full list of spec-044-internal `TODO(spec-044` / `TODO-ALPHA-044` mentions: `:428`, `:431` in `## Slice checklist`, `:453` in `## Doc updates`, `:577`, `:579` in `## Current state`. R2's audit should rule on all five, deliberately rather than by omission, alongside the opener and the header narration.
- **For R3**, an anchor-resolution pass is required after re-relativizing, not merely a file-exists check. Measured this pass: the two files carry **33** cross-file `#anchor` targets between them — the rationale's 18 `s44-*` into the spec, the spec's 15 `rationale-*` into the rationale — plus the `[glossary-django-trac-37064]` definition in **both** files, which is what keeps `check_spec_glossary.py`'s 42nd term reachable. A path rewrite can leave any of them pointing at a real file and a dead heading, and the visible diff is only a rename. Also: the rationale's `<!-- External -->` and `<!-- examples/ -->` groups hold four `../`-prefixed paths that gain a level, while `<!-- docs/SPECS/ -->`'s `[next]` and `[spec-038]` shorten — the same inversion the plan flags for the spec.
- **For R3**, do not convert the three name-based citations at `:1562`, `:1613`, `:1924` back to a positional form while re-relativizing. The reason is written into the rationale's non-decision change record so it survives this artifact.

### For the `### Deferred work catalog` in `bld-044-final.md`

- **`docs/spec-050-debug_extraction-0_0_19.md:390` and `docs/spec-051-boundary_dry_squeeze-0_0_20.md:556` each assert that the version-quintet sites "currently carry `TODO(spec-044 Slice 3)` anchors owned by the in-flight `0.0.14` cut".** Card 044 shipped on 2026-07-20 and this pass's sweep confirms zero such anchors survive in source or tests, so both sentences are false and both caveats' preconditions are discharged. Source: this section, `### Step 6 — the staged-anchor sweep`, class 3. Both files are outside every residual item's writable set — a live spec is its own author's or a future cycle's to edit — so it reaches the maintainer through the catalog.

### Baseline / concurrent-work note

`git status --short` is **unchanged in shape** across this pass, at six entries: the two deliverables and this artifact, the plan, and the two baseline-dirty out-of-scope files. `docs/feedback.md` (a maintainer adversarial review of **spec-046**, the preserved cycle) and the `to-many-search-optimizer-reproduction.md` deletion were neither edited nor reverted, and no `git checkout` / `restore` / `stash` / `worktree` ran at any point (`AGENTS.md` rule 34).

### Final status

**`final-accepted`.**

No box is over-ticked, none is silently un-ticked, the relocation is proven mechanically in both directions, all four gates pass in this pass's own run, and both routed Lows are closed. Under Deviation 3 a `revision-needed` here would route back to Worker 1; nothing requires it.

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
