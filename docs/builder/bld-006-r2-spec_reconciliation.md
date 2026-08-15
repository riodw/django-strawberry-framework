# Build: R2 — Spec reconciliation, and the coordinated retirement of spec-002's `## Visibility status`

Spec reference: `docs/SPECS/spec-006-public_surface-0_0_3.md` (whole document, 177 lines at pass start) plus `docs/SPECS/spec-002-optimizer-0_0_2.md` (retirement sites only)
Status: final-accepted

## Plan (Worker 1)

### The split question, answered in writing

`worker-1.md` `### Boundary count is a split trigger` requires the answer, not the split.

**Boundary count: zero.** No guard, cap, rejection path, or validation branch is added by any part of this item — it edits four markdown files and no executable code. The count-based trigger does not fire.

**Diff shape: reviewable as one unit.** `git diff --numstat` over the writable set is `52 62` (spec-006), `0 3` (spec-002), `57 3` (spec-002's rationale), plus the append to spec-006's rationale. Five hunks in spec-006, one in spec-002, three in spec-002's rationale.

**Answer: do NOT split into R2a (reconciliation) / R2b (retirement), and the reason is the item's own subject.** The retirement's two spec-006-side sites are `## Coordination with other specs` bullet 3 and `## References` bullet 3 — both inside sections the reconciliation rewrites for independent reasons (D14 sits in the same bullet list as the coordination bullet D13 corrects; the References bullet sits beside the one D15 deletes). Splitting would put the requesting bullets in one sub-item and the requested copy in another, which is **precisely the failure mode the maintainer's instruction names** ("since we did not fix every inbound reference in the same change last time, do that now"). A retirement whose inbound fixes land in a different change than the removal is the defect, not a smaller unit of work. The two halves are one decision and therefore one unit.

**One thing the answer costs, stated so it is not discovered later.** A single Worker 3 pass must audit two spec families. That is mitigated by ownership being unambiguous — spec-002 and its rationale are touched at exactly the sites `### The coordinated retirement — every inbound site` names and nowhere else — and by this artifact recording each edit against the row that triggered it.

### DRY analysis

- **Helper inventory checked.** Not applicable in its literal form and declared rather than skipped: this item adds no helper, constant, validation branch, coercion utility, or test helper, and writes no `.py` file at all. The package-wide AST inventory exists to prevent duplicated *code* shapes; this item's duplication risk is prose, and it is measured below with the shingle instrument instead. No inventory was generated, and none would have informed a markdown-only diff.
- **Existing patterns reused.** The reconciliation's shape is taken from the four prior residual cycles rather than invented: `spec-002`'s own rationale companion (the "removed `## Current state`" entry) is the model for a keyed entry that states what was changed, which alternatives lost, and which claims the section may no longer make; `spec-005`'s cycle is the precedent for deleting an unresolvable `## References` locator (D15); `spec-001`'s `## Current state` → `## Prior art` retitle is the precedent weighed and rejected for D1.
- **New shared shape justified.** None. Every spec section this pass writes is stated once, in one document.
- **Duplication risk avoided — measured, not asserted.** Two live risks, both measured with a tokenizer on `[A-Za-z0-9_]+`, case-folded (a whitespace tokenizer fails **open** here, which is how R1's pass-1 Medium happened):
  - **Spec vs its own rationale.** First draft measured **31** non-scaffold 8-shingles — a genuine defect, my rationale reproducing sentences that still stand in the spec. Nine rationale passages were rewritten to *name* the corrected claim rather than reproduce it, and three spec phrasings were decoupled from R1's append-only `## Standing note`. Final figure: **3 at n=8, all three the section heading `### When a subsystem is top-level vs subpackage-only`**, which the rationale is required to cite by heading. n=6 residue 18, every one a heading, the link-def group header line, or a 6-word technical phrase.
  - **Spec-006's rationale vs spec-002's rationale**, since this pass writes a retirement entry in both. `(006 ∩ 002) − 005 − 001` isolated **59** shingles unique to the pair; of those, four clusters were mine and were split by ownership (spec-006's entry now records only why it stopped requesting a copy; spec-002's entry owns the section's own disposition and both alternatives about the heading). Post-fix the pair-unique figure is **46**, and every remaining one is R1's move-record boilerplate — append-only, not this pass's to edit. Pair total **189**, against a control of **252** for spec-006's rationale versus spec-005's: the pair is *less* coupled than an unrelated control, which is the house-template signature R1 established.

### Implementation steps

Line numbers are pin-at-write-time. Every one below was re-derived against the file at edit time; the `### Spec changes made (Worker 1 only)` table carries the ranges as they landed.

1. Re-derive all 19 drift rows against source and HEAD before touching anything (`### Re-derivation of every drift row`).
2. Re-sweep the retirement's site list independently of the plan's table (`### The retirement re-sweep`).
3. **Re-site the threatened glossary anchors BEFORE removing their carriers**, so the file is never on disk with an uncarried anchor.
4. Rewrite spec-006 section by section, in the order the anchors allow.
5. Perform the retirement: spec-002's section, spec-006's two back-pointers, spec-002's rationale sites (sentence, link definition, appended discharge entry).
6. Append the reconciliation record to spec-006's rationale, keyed by heading and anchor; add the six new anchor definitions the new headings need.
7. Re-run `check_spec_glossary` (both specs), `check_trailing_commas --check` (all four files), the read-only `import_spec_terms --check`, the anchor-resolution sweep, the rule-27 sweep, and the shingle measurements.

### Test additions / updates

None, and this is a declaration rather than an omission: **this cycle is source-read-only, tests included.** No test proves a spec sentence. The executable pin this reconciliation points *at* — `tests/base/test_init.py::test_public_api_surface_is_pinned` — is deliberately untouched, because the cycle reconciles the spec to `__all__` and never `__all__` to the spec.

No temp tests are appropriate. Nothing here is executable.

### Implementation discretion items

None. Every choice in this item is a spec-custody choice, which is Worker 1's by definition; there is no builder pass to delegate to (build plan `### Deviation 2`).

### Dispatched findings checklist

Spec-006 has no `## Slice checklist`, so this section stands in its position per `BUILD.md` `### Dispatched findings checklist`: one box per drift row D1-D19, one per row of `### The coordinated retirement — every inbound site`, plus the two sites the dispatch names beyond that table. Worker 1 both performs and ticks here (Deviation 2 removes Worker 2); the ticks are audited at Worker 1's own final verification after Worker 3.

**Every tick below cites evidence re-derived in this pass.** R1's passes twice found substance correct while a box's cited evidence was false, so each box that asserts something is *recorded in* a durable file was grep-verified in that file.

Drift rows:

- [x] **D1** — `## Current state`'s five-name surface list is gone. The section is retitled `## Where the public surface is defined` and carries pointers, not a roster: the exported tuple, the test that pins it verbatim, and the documented per-name locus. Re-derived: `__all__` has **37** entries and `[n for n in p.__all__ if not hasattr(p, n)]` is `[]`. The two out-of-`__all__` categories are stated as categories, without naming the six families.
- [x] **D2** — the fenced five-name `0.0.3` `__all__` tuple is deleted. Fence-line count in spec-006 went **6 → 4** (two import-form blocks survive), measured with `grep -c '^```'`.
- [x] **D3** — discharged **by removal of the claim, not by restatement**: spec-006 no longer summarizes `docs/README.md`'s structure anywhere. Re-derived against that file at 2026-08-14T15:14:15Z (see `### Re-derivation of every drift row`).
- [x] **D4** — the Layer-3 mismatch paragraph is gone with the section. Re-derived on disk: `filters/`, `orders/`, `management/`, `apps.py`, `permissions.py`, `connection.py` all exist; `aggregates/` and `fieldset.py` do not, and `docs/TREE.md` carries them as `aggregates/    # planned by TODO-BETA-057-0.1.3` and `fieldset/    # planned by TODO-BETA-054-0.1.1` — a package, not the module the spec named.
- [x] **D5** — condition 3 now reads `docs/GLOSSARY.md` `## Public exports` and the per-feature entry's status marker. The section it used to name is confirmed absent (18 `^## ` headings in `docs/README.md`, none of them `## Current surface`).
- [x] **D6** — the biconditional is gone. `iff` occurs **0** times in spec-006 (`grep -c` on the token). The gate now states that the four conditions are requirements and never entitlements, and hands the second half of the question to the promotion-path section. **The retraction is recorded** in the rationale under `### `### Top-level re-export rule` — the gate stops being a biconditional`, with the claim named by shape and consequence rather than quoted, and listed under that entry's *Claims the spec no longer makes* — which is the obligation R1's hand-off flagged as still open and this box closes.
- [x] **D7** — the dotted-path paragraph now states both readings (fallback and contract) and says the import form does not distinguish them.
- [x] **D8** — `### docs/README.md structure` is retitled `### How status is published` and rewritten to the loci that exist. **The inbound anchor was fixed in the same change**: `[spec-006-readme]` in the rationale now targets `#how-status-is-published`, verified resolving by the anchor sweep.
- [x] **D9** — the seven-marker list is replaced by a delegation to `docs/GLOSSARY.md` `## Status legend`. Re-measured occurrence counts across the four governed documents: `experimental` 0/0/0/0, `aspirational` 0/0/0/0, `in flight` 0/0/1/0. `GlossaryStatus` rows: exactly `shipped` and `planned`. **A finding the plan's row did not have** — the legend is a DB-backed document (`GlossaryDocument` key `status-legend`, rendered by `scripts/build_glossary_md.py::render_markdown`), which makes it a genuine single source and is what the corrected rule delegates to.
- [x] **D10** — the `partial` exemplar describing the optimizer's end-to-end hook as in flight is gone. The neighbouring shipped-tense citation was re-verified rather than assumed: `convert_choices_to_enum` is defined at `django_strawberry_framework/types/converters.py::convert_choices_to_enum`.
- [x] **D11** — the future-tense exemplars are replaced by the *language patterns* themselves, attached to no named feature. `FilterSet` is re-sited into the shipped-tense bullet, which is where it now belongs. **Sole carrier of `filterset` preserved.**
- [x] **D12** — the eight-subsystem list is gone with `### When to amend this spec`. **Sole carrier of `metaprimary` re-sited** into `## Where the public surface is defined`, in a contract sentence about `Meta` keys being consumer-visible without being exported names.
- [x] **D13** — the amendment-obligation and the "vocabulary is single-sourced here" claim are both retired. The replacement section states four obligations, each discharged inside the subsystem's own change against an artifact something else checks, and says outright that an obligation to return to this document cannot be checked. This is the cycle's root cause and the box that closes it.
- [x] **D14** — both back-pointers removed. `grep -rni 'visibility.status'` returns **0** hits in spec-006 and **0** in spec-002.
- [x] **D15** — the alpha-review bullet is deleted. R1 declined the cut and argued the reason; as a claim-level decision the answer is deletion, recorded with the rejected alternative and with what the bullet was worth (already held in the rationale's `## Problem statement` entry).
- [x] **D16** — **no change owed; verified closed.** R1 removed `## Open questions`; `grep -c 'Open questions'` in spec-006 is **0**. Ticked as verification, not as a change in this diff.
- [x] **D17** — the `## Non-goals` pointer now names `docs/TREE.md`. Re-derived: no `## Package architecture` heading exists in `docs/README.md`.
- [x] **D18** — **verified TRUE at HEAD; no correction invented.** `types/`, `optimizer/`, `filters/`, `orders/`, `mutations/`, `forms/`, `auth/`, `extensions/`, `testing/`, `utils/` all exist as subpackages and the promotion path holds. The section keeps its rule and *gains* the third outcome the gate needed (see D6).
- [x] **D19** — **verified TRUE at HEAD; no correction invented.** No factory, walker, converter, or set primitive is in `__all__` (checked against the 37-name tuple).

Retirement sites (`### The coordinated retirement — every inbound site`):

- [x] **Row 1** — spec-002's `## Visibility status` heading and both sentences removed (`0 3` in `git diff --numstat`). **The merged `__init__`-export precision's disposition is explicit: no restatement in spec-002**, with Worker 0's alternative (one contract sentence inside `## Shipped slices`) recorded as rejected and why, in spec-002's own rationale.
- [x] **Row 2** — spec-006's `## Coordination` bullet 3 removed; spec-002 stays named as an implementation spec by the bullet that always named it.
- [x] **Row 3** — spec-006's `## References` bullet 3 restated so it names spec-002 as the subsystem the `0.0.3` decision applies the rule to, with the amendment claim gone.
- [x] **Row 4** — the rationale sentence no longer links the retired section, and it still names what absorbed the removed `## Current state` (the roster, the context stash, and O2's module path all went to `## Shipped slices`).
- [x] **Row 5** — the deferral record is **left standing and answered**, not deleted: a new top-level `## The discharged deferral — Visibility status retired by the spec-006 cycle` records the discharge, so the deferral and its discharge both stand.
- [x] **Row 6** — `[spec-002-visibility]` definition removed. Verified no dangling and no unused definition remains in either rationale (sweep below), and `check_trailing_commas --check` exits 0 on all four files.
- [x] **Row 7 (verify only)** — the four narrative mentions about the *removed* `## Current state` were re-read and are correct as written. Only the one the retirement falsified (row 4's link sentence) was touched; the rest are untouched, as the table requires.
- [ ] **Row 8** — `KANBAN.md` card-052 Scope prose. **Deferred to R3 by the plan's own assignment** (ORM `CardItem.text` then regenerate; `KANBAN.md` is never hand-edited). Verified still present and now falsified: the standing deferral it states is discharged by this diff.
- [ ] **Row 9** — same card's "both are live and correct" sentence about spec-006's two sites. **Deferred to R3**, same route. Verified falsified by this diff: both sites are gone.
- [x] **Row 10 (verify only)** — `docs/SPECS/appx/spec-003-…-rationale.md`'s verbatim quotation of spec-003's discharged when-O4-ships instruction. Confirmed a quotation, not a reference; untouched.
- [x] **Row 11 (verify only)** — prior cycles' `build-002-*`, `build-003-*`, `bld-003-final.md` verification tables. Confirmed historical artifacts of closed cycles; untouched.

The two sites beyond that table:

- [x] **The twelfth, conditional site (`spec-005:89`)** — **the citation survives, so spec-005 needs nothing, and this pass records which it was.** `### Status-marker vocabulary` still names `spec-005-django_type_contract-0_0_3.md` "Accepted vs deferred Meta keys" **by title**, which is exactly what that spec's `## References` bullet asserts. Keeping it was a deliberate choice: dropping it would have falsified a sibling this cycle has no licence to edit.
- [x] **A site the plan's table does not carry, found by the re-sweep** — `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md`, in R1's `## Provenance of this record`, names `## Visibility status` as one of the three sections spec-002's extraction pass drew its line around. **Verify-only, untouched:** it is a true statement about that pass, the rationale is append-only, and the appended reconciliation record states the retirement plainly a few hundred lines below it.

---

## Move report (Worker 1)

### Files touched

- `docs/SPECS/spec-006-public_surface-0_0_3.md` — the reconciliation, plus the retirement's two spec-006-side sites. 177 → **168** lines, 11,019 → **14,656** bytes.
- `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` — appended `## Reconciliation against the shipped package` (13 keyed entries plus a preamble and a measurement note); re-pointed one anchor definition and added six new ones. 233 → **654** lines, 15,935 → **46,814** bytes.
- `docs/SPECS/spec-002-optimizer-0_0_2.md` — retirement row 1 only. 103 → **100** lines, 9,844 → **9,647** bytes.
- `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` — retirement rows 4, 5, 6, plus the appended discharge entry. 538 → **592** lines, 37,030 → **41,291** bytes.
- `docs/builder/bld-006-r2-spec_reconciliation.md` — this artifact (new).
- `docs/builder/worker-memory/spec-006-worker-1.md` — memory entry.

Nothing else. No source file, test, example, terms CSV, `CHANGELOG.md`, `KANBAN*`, `docs/GLOSSARY.md`, or DB file was written.

### Byte count (required report), and the direction explained rather than gamed

| File | Before | After | Delta |
|---|---|---|---|
| `spec-006-public_surface-0_0_3.md` | 177 lines / 11,019 B | 168 lines / 14,656 B | **-9 lines / +3,637 B** |
| `appx/spec-006-…-rationale.md` | 233 / 15,935 | 654 / 46,814 | +421 / +30,879 |
| `spec-002-optimizer-0_0_2.md` | 103 / 9,844 | 100 / 9,647 | -3 / **-197** |
| `appx/spec-002-…-rationale.md` | 538 / 37,030 | 592 / 41,291 | +54 / +4,261 |

**The spec lost lines and gained bytes, and the arithmetic is worth stating rather than hiding.** Nine lines went (a five-bullet roster, a two-line README summary, a nine-line fenced tuple, a seven-marker list, a four-bullet amendment list), and what replaced them is denser prose per line. Three drivers, in order of size:

1. **The gate needed a rule it never had.** D6 is not a wording fix: "necessary and never sufficient" is only actionable if the document also says *what decides the other half*, so the promotion-path section gained a third outcome. That is new normative content — roughly 900 bytes — and it is the single most consequential edit in the item.
2. **Pointers cost more than rosters.** A five-name list is short; naming the executable pin, the documented locus, and the rule that all three must agree is longer and does not rot. Same trade R1 recorded at +85 for rule 1's pointers.
3. **D13's replacement is four obligations where the original was four requests.** An obligation has to say what discharges it and where, or it is the same unenforceable ask in firmer language.

**I deliberately did not compress to make the number look better**, and I did trim where the prose was arguing rather than instructing: four passages that duplicated the rationale's argument were cut from the spec after the first draft (14,931 → 14,656 B), which is also what took the spec-vs-rationale shingle overlap from 31 to 3. The corpus ratchet is not in scope here — it governs `BUILD.md`, `ARTIFACT.md`, and the four role files, none of which this item touches — but the ratchet's *reason* (every spawn re-reads the spec) is why the trimming happened at all.

### Re-derivation of every drift row

The plan's table is Worker 0's verified floor and is explicitly non-exhaustive. Every row was re-derived here.

**The four `docs/README.md` rows (D3, D5, D8, D17) — measured at `2026-08-14T15:14:15Z`, against the file on disk at that moment**, per the plan's `### First growth`, because a concurrent spec-007 cycle may edit exactly that file. Command: `grep -n '^## \|^### ' docs/README.md`.

- **18 `^## ` headings**, in order: Installation, Quick start, What just happened?, Today and coming next, File and image output, Nested connection indexing, Schema setup boundary, Transport, Session-auth deployment boundary, Production security profile, Form mutation contracts, Model mutation write contracts, Serializer mutation contracts, Filter membership semantics, Development debug responses, Testing GraphQL endpoints, Running the example project, Using the package in your own project.
- **`## Current surface`, `## Planned surface`, `## Package architecture` — zero occurrences each.** D5, D8, and D17 confirmed.
- `## Today and coming next` carries `**Shipped today** (`0.0.14`)` plus a per-release roadmap and points at `docs/GLOSSARY.md` for per-feature status. D3 and D8 confirmed. Positioning and status live in the root `README.md` (`## Why this package exists`, `## Status`, `## Project documentation`).
- **Consequence worth stating: after this pass, spec-006 makes no structural claim about `docs/README.md` at all.** The read collision with the concurrent cycle is not merely managed, it is eliminated — the only two mentions that remain are the vocabulary scope list and a `## References` entry, neither of which depends on that file's shape.

**D1/D2 (the surface and the pin).** `len(p.__all__)` → **37**; `[n for n in p.__all__ if not hasattr(p, n)]` → `[]`, under `PYTHONPATH=examples/fakeshop DJANGO_SETTINGS_MODULE=config.test_settings`. The lazy DRF category and the `logger` category were re-read in `django_strawberry_framework/__init__.py` (`#"Consumer-facing: the name is the key"` and the PEP 562 `__getattr__` docstring, which states the deliberate absence from `__all__` itself). Both are categories the old binary gate could not express, and both are now stated as categories rather than as names.

**D9 (the vocabulary), measured per document, counting occurrences not matching lines.**

| Marker | `docs/README.md` | `docs/TREE.md` | `docs/GLOSSARY.md` | `TODAY.md` |
|---|---|---|---|---|
| `experimental` | 0 | 0 | 0 | 0 |
| `aspirational` | 0 | 0 | 0 | 0 |
| `in flight` | 0 | 0 | 1 | 0 |
| `shipped` | 11 | 1 | 285 | 14 |
| `planned` | 6 | 16 | 39 | 5 |
| `deferred` | 2 | 2 | 20 | 2 |

`partial`'s hits (9/6/18/5) are the ordinary word — "partial implementation", "a partial surface" — not a marker, checked by reading them. The rendered `**Status:**` values are exactly two shapes: `shipped (<version>)` (131) and `planned for|through <version>` (11). `GlossaryStatus.objects.all()` → `[('shipped', 'Shipped'), ('planned', 'Planned')]`.

**The finding the plan's row did not carry, and the reason D9's correction is a delegation rather than a pruning:** `docs/GLOSSARY.md` `## Status legend` is itself a DB-backed document (`GlossaryDocument` key `status-legend`, emitted by `scripts/build_glossary_md.py::render_markdown` ahead of `public-exports`), and it carries five markers — `shipped`, `planned for X.Y.Z`, `deferred`, `alpha constraint`, `post-1.0.0`. So the "single named status vocabulary" spec-006 asked for **does exist**; it just landed somewhere generated instead of here. That is why the corrected section points at it rather than restating any of its five entries, and why `### Alpha signaling rules`' third case keys to `alpha constraint`.

**D6 (the six families).** Re-verified that each is a real, reachable surface with its own owning spec: `views.py`, `routers.py`, `extensions/`, `middleware/`, `testing/`, `auth/` all exist under `django_strawberry_framework/`; `docs/SPECS/spec-046-transport_security-0_0_14.md #"never a package-root export"` and `docs/SPECS/spec-043-test_client-0_0_14.md #"The family stays under"` both resolve, and `django_strawberry_framework/__init__.py #"Do not import or root-export DjangoDebugExtension here"` is present. `docs/GLOSSARY.md` documents them with their import paths — three under explicit "Symbols available from the … subpackage" headings, and the view / router families with their dotted paths in-entry (two occurrences each). **The corrected spec names none of them**, per the single-ownership law; it states the rule and leaves the register to the glossary.

**D10-D12.** `convert_choices_to_enum` exists at `django_strawberry_framework/types/converters.py::convert_choices_to_enum`, so the surviving shipped-tense citation resolves. `FilterSet`, `permissions.py`, `Meta.primary`, relay interfaces, the connection field, orders, and consumer overrides are all shipped surfaces with glossary entries; only aggregates remains, carded on the beta line, which is why no unshipped feature is named as an exemplar.

**D13.** `grep -rn 'spec-006' docs/SPECS/*.md` finds exactly one inbound spec reference, `spec-005`'s companion bullet — no later spec cites spec-006's rules, in either direction. Confirmed as stated.

**D18/D19 — verified TRUE, and the plan is right that nothing should be invented.** The promotion path and the never-promote-a-helper rule both hold at HEAD. The only edit inside D18's section is the *addition* the gate required (D6), which changes nothing the row verified.

### The retirement re-sweep

Run by this pass rather than trusted from the table: `grep -rn 'Visibility status\|visibility-status' --include='*.md' .`, then again case-insensitively (`grep -rni 'visibility.status'`) because the table's row 10 is a lower-case quotation the plan's own pattern would miss.

**What the table predicted versus what the sweep found:**

- Rows 1-9 and 11: found exactly as tabled.
- Row 10: **found only by the case-insensitive sweep.** The plan's stated command is case-sensitive and would not have found it. Recorded because the plan's table was built from that command, so the row's presence in the table means Worker 0 found it another way — and a pass that trusted the command alone would have missed the one site the table marks "do not fix".
- **One site the table does not carry:** `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md`, in R1's provenance list. Verify-only; see the checklist.
- `docs/builder/build-007-…md` acquired a line naming spec-002 and its rationale as dirty files — the concurrent cycle recording **this pass's** working-tree changes as its own baseline growth. Not a reference to the section; reported under `### Concurrent work`.

**Post-retirement state, measured:** 0 occurrences in `docs/SPECS/spec-002-optimizer-0_0_2.md`, 0 in `docs/SPECS/spec-006-public_surface-0_0_3.md`. The remaining occurrences outside `docs/builder/` are: `KANBAN.md:319`/`:322` (R3's, rows 8-9), the spec-003 rationale quotation (row 10), spec-002's rationale (history plus this pass's discharge entry), and spec-006's rationale (R1's provenance line plus this pass's record).

### The 7-anchor constraint — per-anchor result

This item's declared High-severity risk, and R2 carried all of it: every one of the seven was single-carrier and every carrier sat in prose this pass rewrote.

**Method that made it safe: re-site first, remove second.** The three `## Current state` carriers were re-homed in earlier edits, and `check_spec_glossary` was run *between* edits rather than only at the end — it reported `OK: 7 terms` mid-rewrite, which is the check that proves the file was never on disk uncarried.

| Anchor | Old carrier (R1's hand-off) | New carrier | Result |
|---|---|---|---|
| `glossary-djangotype` | `## Current state` list, line 15 | `### Alpha signaling rules`, the shipped-tense bullet | re-sited |
| `glossary-djangooptimizerextension` | same list, line 16 | `#### Decision for 0.0.3`, opening sentence | re-sited |
| `glossary-optimizerhint` | same list, line 17 | `#### Decision for 0.0.3`, same sentence | re-sited |
| `glossary-schema-audit` | `#### Decision for 0.0.3`, line 55 | same section, rewritten sentence | preserved in place |
| `glossary-queryset-diffing` | same sentence | same sentence | preserved in place |
| `glossary-filterset` | falsified future-tense exemplar, line 119 | `### Alpha signaling rules`, the **shipped**-tense bullet | re-sited, and the tense corrected with it |
| `glossary-metaprimary` | `### When to amend this spec` list, line 125 | `## Where the public surface is defined`, the `Meta`-key sentence | re-sited |

No link was re-sited by re-adding narration this pass removed, and **the terms CSV was never opened for writing** — `docs/SPECS/appx/spec-006-public_surface-0_0_3-terms.csv` does not appear in `git status --short`.

**spec-002's anchors were the retirement's own version of the same risk, and it was checked rather than assumed.** The retired section carried the **second** of two `glossary-djangooptimizerextension` uses in spec-002 (the other is in the O3 slice paragraph), so the removal leaves the anchor carried. `check_spec_glossary --spec docs/SPECS/spec-002-optimizer-0_0_2.md` → `OK: 3 terms`.

### Validation run

Every command run from the repository root at the close of the pass, output quoted verbatim.

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md
OK: 7 terms - all have glossary entries and at least one spec link.

$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md
OK: 3 terms - all have glossary entries and at least one spec link.

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-006-public_surface-0_0_3.md \
    docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md \
    docs/SPECS/spec-002-optimizer-0_0_2.md \
    docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md
(no output; exit 0)

$ (cd examples/fakeshop && PYTHONPATH=. DJANGO_SETTINGS_MODULE=config.test_settings \
     uv run python manage.py import_spec_terms --check)
OK: 49 done cards have glossary links.
```

`import_spec_terms --check` is read-only and is the one link in card `DONE-006-0.0.3`'s chain that `check_spec_glossary` cannot see; it was run **after** the writes, not trusted from pre-flight.

**Anchor resolution — every `#anchor` definition in both rationale companions, resolved against the live headings** (GitHub slugification, code spans stripped):

- spec-006's rationale: 12 definitions into spec-006, **all resolve**, including the re-pointed `[spec-006-readme]` → `#how-status-is-published` and the six new ones (`#coordination-with-other-specs`, `#non-goals`, `#references`, `#alpha-signaling-rules`, `#when-a-subsystem-is-top-level-vs-subpackage-only`, `#where-the-public-surface-is-defined`, `#status-marker-vocabulary`, `#what-a-subsystem-spec-owes-these-rules`).
- spec-002's rationale: 6 definitions into spec-002, **all resolve**. `[spec-002-visibility]` is gone.
- **Unused-definition sweep: zero** in either file. A definition with no `][ref]` use would be dead weight and, for the removed one, a broken link.

**`AGENTS.md` rule 27:** `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over all four durable files → **no match** (exit 1). The property was preserved, not established; raw `path:NN` appears only in this artifact, where it is legal.

**Link scaffold:** reference-style only in all four files, one `<!-- LINK DEFINITIONS -->` block each, all 10 canonical group headers present and in order, alphabetical within group (the eight new `spec-006-*` definitions were interleaved alphabetically, not appended), `../../GLOSSARY.md` form for a `docs/` target and `../spec-NNN-….md` for a `docs/SPECS/` sibling at `appx/` depth. Every rewritten target disk-checked.

### Spec changes made (Worker 1 only)

Line ranges as they stand in the finished files.

| # | File | Lines | Trigger | Reason |
|---|---|---|---|---|
| 1 | `spec-006` | 7 | D1/D2 | drop the release-dated status clause and the claim that this spec records the surface |
| 2 | `spec-006` | 11-21 | D1, D3, D4 | replace `## Current state` with `## Where the public surface is defined`: pointers to the three authoritative surfaces, the `Meta`-key sentence (re-sites `metaprimary`), and the two deliberate out-of-`__all__` categories |
| 3 | `spec-006` | 34 | D17 | point the layout non-goal at `docs/TREE.md`, which exists |
| 4 | `spec-006` | 40, 44, 47, 49 | D5, D6, D7 | `iff` → "only when"; condition 3 reads the glossary locus; the necessary-not-sufficient rule added; the dotted-path paragraph states both readings |
| 5 | `spec-006` | 53, 66 | D2 | rewrite the decision's evidence without spec-002's roster labels (re-sites `djangooptimizerextension` + `optimizerhint`); delete the fenced `0.0.3` tuple, replaced by the promotion sentence |
| 6 | `spec-006` | 70, 76 | D4, D6 | drop "future" from two shipped subpackages; add the third promotion outcome the gate needs |
| 7 | `spec-006` | 80-91 | D8 | retitle `### docs/README.md structure` → `### How status is published` and rewrite to the loci that exist; inbound anchor fixed in the same change |
| 8 | `spec-006` | 95-102 | D9, D13 | delegate the vocabulary to `## Status legend`; keep the two load-bearing legend properties; keep the spec-005 by-title citation |
| 9 | `spec-006` | 108-110 | D10, D11 | replace both falsified exemplars with language patterns (re-sites `filterset` into the shipped-tense bullet) |
| 10 | `spec-006` | 114-123 | D12, D13 | retitle `### When to amend this spec` → `### What a subsystem spec owes these rules`; four checkable obligations replace four unenforceable requests |
| 11 | `spec-006` | 129-130 | D14 row 2, D13 | remove the bullet that requested spec-002's copy; restate the single-ownership boundary and the plug-in bullet |
| 12 | `spec-006` | 134-137 | D15, D14 row 3 | delete the alpha-review locator; restate the spec-002 and consumer-prose entries |
| 13 | `spec-002` | (removed at 57-58) | retirement row 1 | delete `## Visibility status`; both facts are owned elsewhere, and no restatement is left behind |
| 14 | `appx/spec-002-…-rationale` | 261-266 | row 4 | the sentence names what absorbed the removed `## Current state` without linking the retired section |
| 15 | `appx/spec-002-…-rationale` | 514 | row 6 | `[spec-002-visibility]` definition removed |
| 16 | `appx/spec-002-…-rationale` | 503-552 | row 5 | appended `## The discharged deferral …`: the disposition, the export-precision decision, and two rejected alternatives |
| 17 | `appx/spec-006-…-rationale` | 216-227 | D8 + new headings | `[spec-006-readme]` re-pointed; six definitions added, alphabetically placed |
| 18 | `appx/spec-006-…-rationale` | 206-565 | all of the above | appended `## Reconciliation against the shipped package`: 13 keyed entries, each naming the change, its cause, the alternatives rejected with the reason each lost, and the claims the section may no longer make |

**Two records this pass owed beyond the drift table, both discharged:**

- **R1's box-8 gap.** The provenance argument (spec-006's coordination bullet is what *requested* spec-002's copy, which under the single-ownership law makes spec-002's the duplicate) lived only in the build plan, which closes with the cycle. It is now in spec-006's rationale, in the appended section's preamble, quoting both retired bullets — verified by grep in the file rather than asserted.
- **D6's open retraction obligation.** R1's `## Standing note` records the biconditional as analysis *about* the document; the retraction proper — the biconditional as a claim the spec no longer makes — is now in the D6 entry's *Claims the spec no longer makes*, which is a different obligation and was untouched before this pass.

**One deliberate non-action, recorded so it is not read as an oversight.** R1 adopted Worker 3's resolution (b) for the Low escalation about its own `### docs/README.md structure` paragraph's present-tense framing: R2's entry notes that the reason clause was restated. That note is in the D8 entry, and R1's paragraph was **not** reopened — the rationale is append-only from this item onward, and a move record legitimately describes the document as it stood at the move. The one place that would genuinely mislead a later reader (the fenced-block count) is corrected by an appended sentence rather than by editing the record.

### Hot-path budget

Not applicable; the plan declares hot-path **none** for every item in this cycle, and this item runs no code — it edits four markdown files. Declared explicitly rather than omitted.

### Floor verification

Not applicable; the plan declares floor-verification scope **none**. No Django / Strawberry / channels integration seam is touched, and no version-sensitive behavior is depended on. Declared explicitly rather than omitted.

### Failability proofs

None; this pass introduced no new boundary, guard, gate, or rejection path, and could not — it wrote no executable code. **No fail-open shape is possible** for the same reason: there is no expression to evaluate. Declared explicitly rather than omitted.

### Implementation notes

- **Retitle-versus-delete was decided per section, not by policy.** `## Current state` was retitled *and* rewritten because the gate's rules refer to the roster and a reader needs somewhere to look; `### docs/README.md structure` and `### When to amend this spec` were retitled because their rules survived and only their targets died; `## Visibility status` and the alpha-review bullet were deleted because nothing survived them. Every one of the four is argued in a rationale entry with the alternative that lost.
- **`#### Decision for 0.0.3` keeps its heading deliberately.** It is the rule's only worked instance, R1 kept it as load-bearing, and the rationale's `[spec-006-decision]` definition targets its anchor. A retitle would have dangled that link for no gain — the heading names a decision made for a release, which is past-tense-safe in a way `## Current state` is not.
- **The spec now names four sibling specs and restates none of them.** `spec-001`, `spec-002`, `spec-005`, `spec-039`. Each is a pointer to an owner (implementation, optimizer record, `Meta`-key contract, the soft-dependency mechanism); the single-ownership law permits the reference and forbids the copy, and the six boundary families are deliberately *not* named anywhere in the spec for exactly that reason.
- **`## Goal` is untouched, and that is a judgement rather than an oversight.** Its four bullets are the spec's own objectives, not claims about the package, and all four still read true — including "a single named status vocabulary", which the reconciliation makes *more* true by naming the source rather than being the source.

### Notes for Worker 3

- **The two highest-value things to re-derive independently** are (a) the seven anchors, by running `check_spec_glossary` yourself rather than reading the table above, and (b) the four `docs/README.md` claims, against the file **at your reading time** — a concurrent spec-007 cycle owns that file and my timestamp is 2026-08-14T15:14:15Z. If that file changed under you, note that spec-006 now makes no structural claim about it, so the exposure is limited to the vocabulary scope list and one `## References` entry.
- **The shingle instrument must tokenize on `[A-Za-z0-9_]+` and case-fold.** A whitespace tokenizer fails **open** here — markdown emphasis sits inside the window — and that is how R1's pass-1 Medium happened. My figures: spec vs rationale **3 at n=8** (all one heading), 18 at n=6; spec-006's rationale vs spec-002's rationale **189** total, **46** pair-unique after subtracting two controls, all 46 in R1's append-only boilerplate. Controls: 006-vs-005 = 252, 002-vs-005 = 180, so the pair is less coupled than a control. **Do not read the raw pair total as a finding** — measure, then control, then judge.
- **Where a reviewer is most likely to disagree with me, named so it is argued rather than discovered.** Retitling `### docs/README.md structure` required re-pointing an anchor definition inside a file that is append-only during the build. I read the append-only rule as governing *reasoning* (the dispatch's rule 3 mandates fixing every inbound reference by title **and** by `#anchor` in the same change, and retirement table row 6 prescribes exactly this move on the sibling rationale). The alternative — keep a heading named for a document whose structure the section no longer discusses — trades an honest heading for a rule read more literally than its purpose.
- The four `docs/review/` deletions and the source-file churn in `git status` are other sessions'. I did not read into `docs/review/`, restore anything, or run `git checkout`.

### Notes for Worker 1 (spec reconciliation)

- **Rows 8 and 9 are the only un-ticked boxes and both are R3's by the plan's own assignment.** They are now *falsified* rather than merely stale: card 052's Scope says spec-006's two sites are "live and correct" and they no longer exist, and says `## Visibility status` "stays" when it does not. R3 must rewrite both `CardItem.text` values through the ORM and regenerate; a hand edit of `KANBAN.md` would be reverted by the next render.
- **R3 inherits one more site than the plan's table gives it:** `bld-003-final.md` item 7 records `KANBAN.md:314` as a fifth card-052-adjacent site the prior plan's table omitted. Not this item's, and not `docs/builder/`-editable, but the card-052 closeout should sweep five sites.
- **A live contract violation stands, deliberately unfixed here.** Condition 3 now reads the glossary's `## Public exports` list, and that list carries **34** bullets against 37 `__all__` entries — `DjangoSchema` and `DjangoMutationExecutionContext` have no bullet at all, and `DEFAULT_ERROR_POLICY` / `DEFAULT_RESOURCE_POLICY` are named inline inside neighbouring bullets rather than carrying their own. Maintainer decision 2 assigns the fix to R3. **The condition was deliberately not weakened to match the gap** — a gate rewritten to accommodate its own violation is the failure this cycle is repairing.
- **No source defect was found**, and none was edited. The read-only audit's two "do not mistake for drift" observations (`logger` public but out of `__all__`; `SerializerMutation` documented but out of `__all__`) were both re-read in source and are now *expressible* in the spec as the two deliberate out-of-`__all__` categories, which is the reconciliation the plan predicted rather than a source change.

### Concurrent work — reported, not touched

HEAD re-derived: **`947f7494`**, unmoved since plan time. Nothing of this pass was swept into another session's commit: `git log --oneline -1` per path gives `ff65666d` for spec-006, `d613887c` for spec-002, and `a76da376` for spec-002's rationale — all predating this cycle — and `git diff --cached --name-only` is empty.

**Third growth event, beyond the plan's two.** Newly dirty and out of scope, reported for Worker 0 to append to the plan:

- `django_strawberry_framework/_boundary_ordering.py`, `django_strawberry_framework/middleware/request_body.py`, `tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py` (`M`) and `docs/review/rev-_boundary_ordering.md` (`??`) — another session doing **source and test** work. This cycle is source-read-only and wrote none of them.
- `docs/SPECS/spec-007-…md` shows `2 5` in `git diff --numstat` and its cycle's artifacts remain untracked; its build plan has grown a line recording *this* pass's dirty spec-002 files as its own baseline growth.
- The five deleted committed `docs/review/rev-*.md` files and untracked `docs/review/review-0_0_14.md` persist. Still escalated to the maintainer, still untouched: not read, not restored, no `git checkout`.

### Review outcome

Awaiting Worker 3. `Status: planned` per `### Deviation 2` — Worker 0 reads `planned` on this artifact as "dispatch Worker 3".

---

## Review (Worker 3)

Reviewed the whole of `docs/SPECS/spec-006-public_surface-0_0_3.md` end to end (not only the diff), the
retirement's four durable files, and every drift-row citation, against `git diff` and against source.
Every number below is mine, re-measured; where it differs from the pass's, both are given.

### High:

None.

### Medium:

#### `## Public exports` is characterized as the export roster, but the generated section also contains the deliberately-non-exported subpackage lists — which falsifies the new boundary clause for three of the six families it governs

`docs/SPECS/spec-006-public_surface-0_0_3.md:17`, `:44`, `:76`.

Line 17 defines the locus as "`docs/GLOSSARY.md` `## Public exports` — the documented surface: one
bullet per exported name". Condition 3 (`:44`) then tests membership against it, and the new
promotion-boundary clause (`:76`) says a boundary family "is documented in `docs/GLOSSARY.md` with the
import path stated, **rather than under `## Public exports`**".

Measured against the generated document: `## Public exports` runs from its heading to the next `## `
heading and contains **four** bullet groups, not one — the roster under "Symbols re-exported from
`django_strawberry_framework`:" (**34** bullets), plus "Symbols available from the
`…extensions` subpackage" (`DjangoDebugExtension`), "…`testing` subpackage" (8 bullets incl. the
`testing.relay` note), and "…`auth` submodule" (the four field factories). Those three groups are
exactly three of the six families D6 names. So:

- `:76`'s "rather than under `## Public exports`" is **false** for `extensions.DjangoDebugExtension`,
  `testing`, and `auth`: all three *are* documented under that heading, with their import paths, in
  sub-lists whose lead-in sentence names the subpackage. It holds only for `views`, `routers`, and
  `middleware.debug_toolbar`, which carry their dotted paths in-entry (verified at
  `docs/GLOSSARY.md` #"django_strawberry_framework/views.py", #"django_strawberry_framework/routers.py",
  #"django_strawberry_framework/middleware/debug_toolbar.py").
- Condition 3's literal test is therefore satisfiable by names that are deliberately not exported:
  `TestClient`, `DjangoDebugExtension`, and `login_mutation` each "carry a bullet in
  `docs/GLOSSARY.md` `## Public exports` linking a per-feature entry". `:47` keeps the gate's *outcome*
  correct (requirements, never entitlements), so nothing is inverted — but a reader auditing condition 3
  mechanically mis-classifies three families, and a future subsystem author following `:76` would file a
  new boundary family's glossary docs outside the section where the three existing ones live.

Why it matters: this is a milder re-instance of D5 — a gate condition naming a documentation locus whose
real shape does not match the spec's description — in the one item whose whole purpose is removing that
class. Worker 0's plan carries the same simplification ("`## Public exports` (34 bullets, each linking a
per-feature entry)"), so the pass inherited it rather than invented it; the correction is still owed
because R2 re-derived the section and had the evidence in hand (its own escalation counts the 34).

Recommended change (wording is Worker 1's): make the spec's own usage name the roster rather than the
heading — e.g. at `:17` say the section carries the re-exported roster *plus* per-subpackage lists for
the families whose import path is the boundary, and at `:44`/`:76` refer to the roster (the
"Symbols re-exported from …" list) rather than to `## Public exports` as a whole. No test expectation:
no executable behavior is affected. **Do not** resolve it by weakening the gate; the same reasoning R2
gives for not weakening condition 3 to fit the 34-vs-37 gap applies here.

### Low:

#### D16's cited evidence is false as written

`docs/builder/bld-006-r2-spec_reconciliation.md:74` states "`grep -c 'Open questions'` in spec-006 is
**0**". Measured: it returns **1** — `spec-006:3`, R1's H1 pointer ("the release-gating judgement an
`Open questions` section once recorded"). The correct evidence for the box's substance is
`grep -c '^## Open questions'` → **0**, which I ran and which passes. The box's outcome is right and no
durable file is wrong; the citation is not. This is the third instance of the class in this cycle, and
`bld-006-r1-rationale_move.md:303` had already documented this exact trap ("the words 'Open questions'
survive in the spec only inside the H1 pointer") — so the checklist preamble's promise at `:55` that
"each box that asserts something is *recorded in* a durable file was grep-verified in that file" is not
met for this box. Recommended change: restate the box's command as the heading-anchored form.

#### The link-definition count is understated: nine definitions were added, not six

`:226` ("the re-pointed `[spec-006-readme]` and the **six** new ones") and table row 17 (`:256`, "six
definitions added") are both wrong, and `:226`'s own parenthetical enumerates **eight** anchors, which
contradicts its count in the same sentence. Measured: `appx/spec-006-…-rationale.md` carried **7**
definitions after R1 (`bld-006-r1-rationale_move.md:169`, "Rationale: 7 / 7") and carries **16** now, so
**nine** were added. Attributing by region (split at the appended `## Reconciliation against the shipped
package`, line 206), the nine used only below the cut are `spec-006-coordination`, `-nongoals`, `-owes`,
`-reexport`, `-references`, `-signaling`, `-subsystem`, `-surface`, `-vocabulary`; `:226`'s list omits
`spec-006-reexport` → `#top-level-re-export-rule`. The definitions themselves are correct — all 16
resolve, none unused, alphabetical within group (independently verified below) — so only the record is
wrong. Related but *correct*: "12 definitions into spec-006" is right if read as anchor-bearing
definitions (13 target the file; one, `[spec-006]`, has no anchor).

#### `:89`'s "prose does not repeat the markers" is stated absolutely, and `docs/README.md` repeats one at section scope

`docs/SPECS/spec-006-public_surface-0_0_3.md:89` reads "Prose elsewhere in the documentation — the
onboarding README, the capability snapshot — does not repeat the markers." `docs/README.md`
`## Today and coming next` carries `**Shipped today** (`0.0.14`)` over roughly thirty capabilities, and
this pass's own D9 table counts `shipped` **11** times in that file and **14** in `TODAY.md`. Read as a
*rule*, `:89` composes with `:100` ("a section boundary is not a marker and does not substitute for
one") and the README's summary stamp is a non-conformance in a file `spec-007` owns; read as a
*description*, `:89` is false. Either reading is defensible, which is the defect — and the pass
escalated the other live violation it found (34-vs-37) rather than leaving its disposition implicit.
Recommended change: one clause distinguishing a per-feature marker from a pointer-plus-summary, or an
`Escalated:` line recording the README stamp as a known non-conformance owned by `spec-007`. Note `:95`
lists `docs/README.md` and `TODAY.md` inside the vocabulary scope while `:89` says their prose carries no
markers; whichever way `:89` is settled should make those two sentences read as one rule.

### DRY findings

None. Re-derived rather than accepted:

- **Spec vs its own rationale, `[A-Za-z0-9_]+` tokenizer, case-folded, scaffold (the `<!-- LINK
  DEFINITIONS -->` block and below) excluded:** **3 distinct shingles at n=8**, all three windows over
  the section heading `### When a subsystem is top-level vs subpackage-only`, which rule 1 obliges the
  rationale to cite by heading — tuple-for-tuple identical to the pass's figure. At n=6 I get **17**
  against the pass's 18 (boundary handling of the scaffold cut is the likely 1); every one is a heading,
  a document path pair, or a 6-word technical phrase. The two n=6 windows that are genuine near-restatements
  of surviving spec text — `appx/spec-006-…-rationale.md:527` (`docs/TREE.md` "keeps the on-disk and target
  shapes side by side" vs `spec-006:34`) and `:298` (soft-dep names "stay reachable on the package while
  staying out of" vs `spec-006:21`) — are entries whose job is to record what the corrected sentence now
  says, they diverge before n=8, and neither is a second site that can go stale independently. Judged from
  their sites, not the count, per the standard R1 established.
- **The two rationale companions:** pair total **182 at n=8** (pass: 189) against a `spec-005` control of
  **247** (pass: 252). Same magnitude, same ordering — the pair is *less* coupled than the control, so the
  raw total is house template, exactly as the pass warns.
- No helper, constant, or code shape exists to consolidate; the existence challenge has no target in a
  markdown-only diff.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — `__all__` and the re-export list are
unchanged, as this source-read-only cycle requires. Re-verified independently by import:
`len(__all__)` → **37**, `[n for n in __all__ if not hasattr(p, n)]` → `[]`.

The concurrent session's source and test churn (`django_strawberry_framework/_boundary_ordering.py`,
`django_strawberry_framework/middleware/request_body.py`, `tests/test_views.py`,
`examples/fakeshop/test_query/test_transport_api.py`) is baseline-dirty, out of scope, and **not** this
cycle's work. I did not read it, did not revert it, and ran no `git checkout`. The five deleted committed
`docs/review/rev-*.md` files and the two untracked `docs/review/` files are likewise another session's,
still escalated, untouched.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. (`git status --porcelain CHANGELOG.md` empty.)

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Applies in full — the whole item is archived-spec and rationale editing. Confirmed:

- **No version string or release metadata moved.** `pyproject.toml` and
  `django_strawberry_framework/__init__.py` are both clean in `git status`; `__version__` stays `0.0.14`.
  The spec's one release-dated heading, `#### Decision for 0.0.3`, is a decision made *for* a release, not
  a section named for the present — kept deliberately, and it is the target of the rationale's
  `[spec-006-decision]`, which still resolves.
- **Card IDs and statuses.** No card ID appears in the four durable files; `DONE-006-0.0.3`'s glossary
  chain is intact (`import_spec_terms --check` → `OK: 49 done cards have glossary links.`, run read-only
  after the writes). No `KANBAN*` file, `docs/GLOSSARY.md`, or `db.sqlite3` was written by this pass.
- **Every markdown link introduced or moved points at a file on disk.** Re-parsed all four files
  independently: definitions 8 / 16 / 4 / 18, **0 undefined uses and 0 unused definitions in each**,
  every target file present, and every `#anchor` into a spec resolving against that spec's live headings
  under GitHub slugification with code spans stripped — including the re-pointed
  `[spec-006-readme]` → `#how-status-is-published` and all nine new ones. `[spec-002-visibility]` is gone
  and nothing dangles in its place. **No in-page `](#…)` link exists in any of the four files**, so no
  in-page anchor can dangle. Bare-filename spec references all resolve on disk (`spec-001`, `spec-002`,
  `spec-005`, `spec-039`; spec-039's Decision 12 is indeed the soft-`djangorestframework` decision the
  soft-dep sentence leans on).
- **Scaffold and rule 27, all four files.** `check_trailing_commas.py --check` exits **0**; all 10
  canonical group headers present and in the canonical order in each file; `grep -nE
  '[a-zA-Z_/]+\.(py|md):[0-9]+'` over the four → **no match** (raw `path:NN` appears only in this
  artifact, where it is legal).
- **No obsolete "coming soon"/"planned"/old-version wording left in the rewritten sections.** `iff` is
  **0** occurrences as a token; the fenced-block count is **4** lines / two import examples, matching the
  removal of the `0.0.3` tuple.
- **No script-rendered doc was regenerated**, and none needed to be — no module docstring, `docs/TREE.md`,
  `docs/GLOSSARY.md`, or `KANBAN*` file is in the diff.
- **The archived record is preserved, not rewritten.** `spec-002`'s rationale keeps the deferral paragraph
  at `:302-306` verbatim and answers it in an appended top-level entry; the falsified present-tense clauses
  inside the older entry are covered by a forward pointer added *above* them at `:263-266` and by the new
  entry quoting them, so a reader arriving at the old paragraph is not left with an uncorrected claim. That
  is the right shape for an append-only file.

### Failability proofs / hot-path / floor verification

Declared not-applicable rather than omitted, and I confirm each independently:

- **Failability proofs — none owed.** The diff contains no executable line: `git diff --stat` over the
  writable set is three markdown files plus one untracked markdown file. No boundary, guard, gate, or
  rejection path is introduced, so the mandatory re-run floor is computed over an empty set and an empty
  re-run set is legal here. No fail-open shape is possible for the same reason — there is no expression to
  evaluate.
- **Hot-path budget — not applicable.** The plan declares hot-path `none` cycle-wide and this item runs no
  code, so there is no before/after number to carry.
- **Floor verification — not applicable.** The plan declares floor scope `none`; no Django / Strawberry /
  channels seam is touched and no version-sensitive behavior is depended on.
- **`scripts/review_inspect.py` — not run, and the skip is recorded with its reason:** the helper's outputs
  (repeated string literals, import boundaries, control-flow hotspots) are AST facts about `.py` files, and
  this diff contains none. Its evidence could not inform a markdown-only review.

### What looks solid

- **The 7-anchor constraint held, re-derived by measurement rather than read.** Reference-style
  `[text][ref-id]` uses only, code spans stripped first: exactly **7** glossary refs, each used **once**
  (so each is still a sole carrier), at `spec-006:19` (`metaprimary`, in `## Where the public surface is
  defined`), `:53` (`djangooptimizerextension`, `optimizerhint`, `schema-audit`, `queryset-diffing`, all in
  `#### Decision for 0.0.3`), `:108` (`djangotype`, `filterset`, in `### Alpha signaling rules`) — the
  per-anchor table is correct in all seven rows, including which two were preserved in place.
  `check_spec_glossary.py` → `OK: 7 terms` for spec-006 and `OK: 3 terms` for spec-002 (the retirement
  removed the *second* of two `glossary-djangooptimizerextension` uses; the surviving one is at
  `spec-002:39`). `appx/spec-006-…-terms.csv` is byte-unchanged — absent from `git status --porcelain`
  while tracked by `git ls-files`.
- **The retirement is complete.** My own case-insensitive sweep, `grep -rni 'visibility.status'
  --include='*.md' .`, returns **0** occurrences in `spec-006` and **0** in `spec-002`, and every survivor
  falls in a licensed class: `KANBAN.md:319`/`:322` (rows 8/9, R3's ORM work, correctly left un-ticked),
  `appx/spec-003-…-rationale.md:328` (row 10's verbatim quotation of a historical instruction),
  `appx/spec-002-…-rationale.md` (the pre-existing `## Current state` narrative at `:60`/`:83`/`:84`/`:273`/
  `:278`, the standing deferral at `:302`, and this pass's own row-4 rewrite and discharge entry),
  `appx/spec-006-…-rationale.md` (R1's provenance line plus this pass's record), and prior/current cycles'
  `docs/builder/` artifacts. **No `#visibility-status` link definition or in-page anchor survives anywhere**
  in the repository. `spec-002`'s own scaffold still validates and its heading sequence reads coherently
  (`## Coordination` → `## References` → `## Implementation checklist`), with no status-shaped
  named-for-now heading left.
- **The third promotion outcome is reconciliation, not invention — tested against all six families and
  their owning specs.** Each family is out of `__all__` (verified by import), and each owning spec states
  the decision *and* a reason the new clause's three exemplars actually cover:
  `spec-046-transport_security-0_0_14.md` #"never a package-root export" ("matching the established posture
  for every integration surface"), `spec-041-channels_router-0_0_14.md` #"No package-root re-export" plus
  its explicitly rejected lazy-root-export alternative, `spec-040-…` Decision 3 #"no root re-export"
  ("the root would also eagerly import `auth/` (and `django.contrib.auth`)" — the clause's second
  exemplar, near-verbatim), `spec-043-test_client-0_0_14.md` #"The family stays under", and
  `django_strawberry_framework/__init__.py` #"Do not import or root-export DjangoDebugExtension here". The
  practice is real, uniform, and older than the clause; writing it down says nothing those specs do not.
  The clause also stays clear of the soft-dependency category `:21` keeps separate — "pulling in an
  optional distribution" reads on `middleware.debug_toolbar` and `routers` (the `channels` guard), not on
  the PEP 562 DRF names.
- **The single-ownership law holds in both directions.** `spec-002`'s duplicate is gone with no
  restatement left behind, and `spec-006` acquired none: it names `spec-001`, `spec-002`, `spec-005`, and
  `spec-039` as pointers only, delegates the `Meta`-key contract to `spec-005` by title (which is exactly
  what `spec-005:89`'s own `## References` bullet asserts, so the twelfth conditional site is correctly
  left alone), and names none of the six boundary families. **The resulting rule is still usable by a
  reader who cannot see those specs**: `:76` tells a subsystem author what to do and where to record it,
  and tells a reader of an existing family where the decision lives (the owning spec, plus the glossary's
  per-subpackage lists) — a roster would have been the copy the law forbids. `grep -rn 'spec-006'
  docs/SPECS/*.md` confirms `spec-005:89` is still the only inbound spec reference, as D13 says.
- **The four `docs/README.md` dispositions still hold, re-derived at my reading time.** That file is
  **clean** in `git status` and HEAD is unmoved at `947f7494`, so it has not moved under the pass's
  `2026-08-14T15:14:15Z` measurement: **18** `^## ` headings, and `## Current surface` / `## Planned
  surface` / `## Package architecture` at **zero** occurrences each. D3/D5/D8/D17 confirmed. Discharging
  them by *removing* the structural claim rather than restating it is the robust shape, and it is why the
  concurrent-cycle exposure is now limited to `:95`'s vocabulary scope list and one `## References` entry.
- **The 34-vs-37 gap is exactly as reported, and leaving it standing is the right call.** Re-derived
  independently: **34** bullets in the re-exported roster against **37** `__all__` entries; the four without
  their own bullet are `DjangoSchema`, `DjangoMutationExecutionContext`, `DEFAULT_ERROR_POLICY`,
  `DEFAULT_RESOURCE_POLICY`, the last two named inline inside the `ErrorPolicy` / `ResourcePolicy` bullets;
  `SerializerMutation` carries a bullet while deliberately outside `__all__`. Deferring it is not this
  pass's improvisation — `### Maintainer decision 2` assigns the fix to R3 and records why card 052 was
  rejected as the owner, and the fix is a glossary-DB write plus a regenerate, which is outside R2's
  writable set by construction. Refusing to weaken condition 3 to fit its own violation is the correct
  direction: a gate rewritten to accommodate its violation would recreate D5.
- **Every other drift-row citation checks out.** D2 fence lines **4** (from 6); D4's `aggregates/` and
  `fieldset/` present in `docs/TREE.md`'s target tree with their beta cards while the on-disk tree lists
  neither; D5's heading absence; D6's `iff` **0**; D9's legend confirmed DB-backed (`GlossaryDocument` key
  `status-legend`, emitted by `scripts/build_glossary_md.py::render_markdown`) and carrying `alpha
  constraint`, which is what makes `:110`'s third signaling case grounded rather than invented;
  D10's `convert_choices_to_enum` present at
  `django_strawberry_framework/types/converters.py::convert_choices_to_enum`; D14's zero hits; D18/D19
  verified true with nothing invented; `tests/base/test_init.py::test_public_api_surface_is_pinned` exists,
  so `:16` names a real pin. Rows 8/9 are the only un-ticked boxes and both carry a recorded deferral with
  the route (ORM then regenerate), which is a deferral, not a silent gap.
- **The spec reads as a clean current contract end to end.** No amendment block, no retraction, no
  "originally … now", no "as of", no round or date anywhere in the 168 lines. The one clause that refers to
  a section that no longer exists — `:3`'s "the release-gating judgement an `Open questions` section once
  recorded" — is **R1's H1 pointer, byte-unchanged** (line 3 measures 269 bytes; R1 recorded 270 for the
  paragraph plus its blank line), it was weighed and cleared in R1's review as the minimum that discharges
  rule 1's pointer obligation, and R2 correctly did not reopen it. Nothing R2 added narrates history.
- **The +3,637-byte growth survives the "narration absorbed into the contract" suspicion.** I read every
  added passage against rule 1 and found no explanation of a correction. The growth is accounted for by
  three things I can point at in the file: the new `## Where the public surface is defined` pointer triple
  (`:15-17`), which is longer than the five-name roster it replaced and does not rot; the third promotion
  outcome (`:47` plus `:76`), which is new *normative* content the gate needed once it stopped being a
  biconditional; and `:116-123`'s four discharge-shaped obligations replacing four unenforceable requests.
  The inverse check found nothing either: at n=8 the spec restates its rationale in one heading citation
  only.

### Temp test verification

- `docs/builder/temp-tests/r2/shingle.py` — the punctuation-insensitive n-gram instrument used for the DRY
  re-derivations above (`[A-Za-z0-9_]+`, case-folded, scaffold cut at `<!-- LINK DEFINITIONS -->`).
- Disposition: **kept as a temp file only** (the directory is gitignored). Nothing to promote — it measures
  documents, not package behavior, and no permanent test tree owns prose measurement. No temp test caught a
  behavior bug, because the diff contains no behavior.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: the Medium is a one-clause spec fix, and it is R2's own to make** — `worker-0.md`'s
  per-slice route sends a `revision-needed` to Worker 2, and `### Deviation 2`'s corollary says that route
  does not exist for R2, so the apply-changes pass is Worker 1's and re-sets `Status: planned`. Resolution
  paths, in my order of preference: (a) rename the spec's own usage so it refers to the *roster* rather than
  to the `## Public exports` heading at `:17`, `:44`, and `:76` — smallest change, keeps all three sentences
  true; (b) keep the phrase and add one clause at `:17` saying the section also carries per-subpackage lists
  for the boundary families, so `:76`'s contrast is explicit rather than implied; (c) reject with a recorded
  reason if you judge `:17`'s definition sufficient to bind the phrase for the whole document — in which
  case say so in the rationale, because the next reader will re-derive the 34 bullets and hit the same
  contradiction. **Not (d):** do not weaken condition 3.
- **Escalated: the `:89` Low needs a disposition, not necessarily an edit.** Either settle it as a rule
  (and record `docs/README.md`'s `**Shipped today**` section stamp as a known non-conformance owned by
  `spec-007`, mirroring how the 34-vs-37 violation is handled) or narrow the sentence. Do not leave it as a
  present-tense description, which is what makes it false.
- **The two artifact-record Lows are corrections to this artifact, not to any durable file.** Restate D16's
  command as `grep -c '^## Open questions'`, and correct "six" to **nine** at `:226` and `:256` (adding
  `spec-006-reexport` → `#top-level-re-export-rule` to the enumeration). Both are record accuracy, and this
  artifact is what your final verification audits ticks against.
- **`### Notes for Worker 3`' three flagged judgement calls are all decided correct**, so R3 need not
  re-litigate them: re-pointing `[spec-006-readme]` inside the append-only rationale is prescribed by
  retirement row 6's own shape and is the only reading under which "fix every inbound site by title **and**
  by `#anchor` in the same change" is satisfiable; keeping `#### Decision for 0.0.3` is right (a decision
  made *for* a release is not a section named for now, and the anchor is cited); and `## Goal` being
  untouched is right — its four bullets are objectives, not claims about the package.
- **R3's inherited scope, confirmed:** rows 8/9 plus `bld-003-final.md` item 7's `KANBAN.md:314` — five
  card-052-adjacent sites, ORM-then-regenerate, never a hand edit of `KANBAN.md`. Both rows are now
  *falsified* rather than merely stale, so R3's edit is a correction and not a tidy-up.
- **No source defect found**, independently: all 37 `__all__` names resolve, none is helper-shaped, and the
  two "do not mistake for drift" observations (`logger`; `SerializerMutation`) are both deliberate and both
  now expressible as the spec's two out-of-`__all__` categories.

### Review outcome

`revision-needed`. One Medium stands in a durable file — the spec states, as part of a new contract clause,
that the boundary families are documented somewhere other than `## Public exports`, and three of the six are
documented exactly there. Everything else in the item is sound and independently re-derived: the retirement
is complete with no dangling anchor anywhere, all seven glossary carriers survive as sole carriers with both
`check_spec_glossary` runs and the read-only `import_spec_terms --check` green, the terms CSV is
byte-unchanged, the scaffold and rule-27 gates pass on all four files, the third promotion outcome is
reconciliation rather than invention against all six families and their five owning specs, the spec narrates
no history, and the spec-vs-rationale overlap is 3 shingles at n=8 — all one required heading citation.
Three Lows accompany it: one falsified box citation, one understated definition count, and one sentence whose
rule/description ambiguity needs settling. The fix is a small, well-bounded Worker 1 pass under
`### Deviation 2`'s corollary.

---

## Apply-changes pass (Worker 1, pass 2)

`### Deviation 2`'s corollary: R2 has no Worker 2 route, so the apply-changes pass is Worker 1's and
re-sets `Status: planned`. This is a fresh invocation — the artifact above and the working-tree diff were
the contract, and every number below was re-derived rather than read off the review.

### The section as it actually exists, measured before writing

`docs/GLOSSARY.md`, read from `## Public exports` (line 22) to the next `## ` heading (line 82, `## Index`),
parsed by lead-in sentence:

| Lead-in sentence | Bullets |
|---|---|
| "Symbols re-exported from `django_strawberry_framework`:" | **34** |
| "Symbols available from the `django_strawberry_framework.extensions` subpackage (opt-in schema extensions):" | **1** (`DjangoDebugExtension`) |
| "Symbols available from the `django_strawberry_framework.testing` subpackage (consumer test utilities):" | **8** (the eighth pairs `global_id_for` / `decode_global_id` at the `testing.relay` path) |
| "Symbols available from the `django_strawberry_framework.auth` submodule ..." | **1** bullet naming the four session-auth field factories |
| the closing `_Note:_` paragraph on the clean import path | 0 |

**Four bullet groups, and the review's reading is confirmed in every particular.** One refinement to its
wording, since it matters to how the corrected spec is phrased: the `auth` group is a *single* bullet
listing four factories, not four bullets, so the section's unit of documentation is the bullet and its
unit of placement is the group. That is the distinction the fix is built on.

The three families the section does **not** group — `views`, `routers`, `middleware.debug_toolbar` — carry
their dotted paths inside their own entries. They are card 052's per `### Maintainer decision 2`'s appended
correction, and nothing here touches them. The four missing roster bullets (`DjangoSchema`,
`DjangoMutationExecutionContext`, `DEFAULT_ERROR_POLICY`, `DEFAULT_RESOURCE_POLICY`) remain R3's under the
same decision. `docs/GLOSSARY.md` was opened read-only; it is absent from `git status --porcelain`.

### The Medium — closed at all three sites

The rule written is the review's option (a) and (b) merged, because neither alone carries the whole
distinction: **a bullet is what documents a name; the group the bullet sits in is what states which import
surface the name is on.** Condition 3 was not weakened — it now reads a *narrower* locus than before.

| Spec line | Was | Now |
|---|---|---|
| `:17` | the locus described as "one bullet per exported name" | the locus described as grouped by import path — a package-root roster group plus per-subpackage groups — with the bullet/group distinction stated once, here, for the whole document |
| `:44` | condition 3 tests against the section as a whole | condition 3 reads the root re-export group, and says outright that a per-subpackage bullet documents the symbol while recording the *opposite* placement |
| `:76` | a boundary family is documented "rather than under `## Public exports`" | a boundary family documents its names under the import path that is the boundary — as a per-subpackage group of that section, or with the dotted path in its own entry — never in the root re-export group |

**Falsification re-run at the three sites the review used to prove the defect.** `TestClient` and
`DjangoDebugExtension` sit in per-subpackage groups and `login_mutation` inside the `auth` group's bullet,
so all three now fail condition 3 as read, and each is placed exactly where `:76` sends it. The six-family
set stays unnamed in the spec, per the single-ownership law, and no family count appears in it.

**Not done, deliberately:** condition 3 was not relaxed to "documented anywhere in the glossary" (a
condition that cannot fail is not a gate), the spec does not assert the section is root-export-only (that
document is generated; the spec cannot make such a claim true), and no family register was added.

### Low 1 — D16's citation, corrected here rather than in the prior section

The box at `:74` cites `grep -c 'Open questions'` → **0**. Re-derived: that command returns **1** (the H1
pointer at `spec-006:3`). The heading-anchored form, which is the box's actual subject, returns **0**:

```
$ grep -c "Open questions" docs/SPECS/spec-006-public_surface-0_0_3.md
1
$ grep -c '^## Open questions' docs/SPECS/spec-006-public_surface-0_0_3.md
0
```

**The box's substance is unchanged and stays ticked**; only its evidence is restated, as
`grep -c '^## Open questions'` → 0. The prior section is not edited (`ARTIFACT.md` `## Re-pass sections`).
The class-level lesson is in the memory file: an evidence command must anchor on the shape the box claims,
because a heading's words survive in prose that legitimately mentions it.

### Low 2 — the definition count, corrected to nine

Re-derived, not accepted. `bld-006-r1-rationale_move.md:169` records the rationale at **7 definitions / 7
uses** after R1; the file carries **16** now, and this pass added none — so R2 added **nine**. Attributing
by region (uses appearing only below the appended `## Reconciliation against the shipped package` cut):
`spec-006-coordination`, `-nongoals`, `-owes`, `-reexport`, `-references`, `-signaling`, `-subsystem`,
`-surface`, `-vocabulary`. The review is right that `:226`'s parenthetical enumerates eight and omits
`spec-006-reexport` → `#top-level-re-export-rule`.

**Corrected record: nine definitions were added, not six** — `:226` and table row 17 (`:256`) both
understate it, and `:226`'s count contradicts its own list. The definitions themselves were re-verified
correct: 16 definitions, **0 undefined uses, 0 unused definitions**, every target on disk, every `#anchor`
resolving against spec-006's live headings. `:226`'s separate "12 definitions into spec-006" is right read
as anchor-bearing definitions (13 target the file; `[spec-006]` carries no anchor).

### Low 3 — `:89` settled as a rule, and written as one

**Decision: it is a rule, not a description**, and the sentence now says so. The rewritten clause states
the prohibition (prose publishes no marker of its own), keeps the pointer obligation, and answers the
scope question inside itself: a status word in such prose comes from the legend, and a release-scoped
summary over a group of capabilities is not a per-feature marker for anything inside it.

Three things that reading buys, each checked rather than asserted:

- **`docs/README.md`'s `**Shipped today** (`0.0.14`)` stamp is conforming**, so no non-conformance is
  escalated into a file `spec-007` owns. It is a release-scoped summary that points at the glossary for
  per-feature status — measured in this cycle's own D9 table and re-confirmed here: that file is still
  clean in `git status` and still carries `## Today and coming next` with the stamp.
- **`:95` and `:89` now read as one rule.** `:95` puts `docs/README.md` and `TODAY.md` inside the
  vocabulary's scope (their status words come from the legend); `:89` says those documents are not a second
  locus for markers. Same rule from two sides, no residue.
- **`:100` is what makes it non-arbitrary.** A marker attaches to a feature's own entry, never to a
  document or a section — so a section-scope summary never was a marker for its contents. `:89` now states
  the consequence instead of leaving it to be inferred.

The reasoning, both rejected alternatives (escalate the README stamp as a known non-conformance; narrow
`:89` into a description of two files this spec does not own), and the claim the spec no longer makes are in
the rationale's appended `## Documented is not the same as exported`, keyed by heading.

### Byte count (required report), against the R2 figures

| File | R2 close | This pass | Delta |
|---|---|---|---|
| `docs/SPECS/spec-006-public_surface-0_0_3.md` | 168 lines / 14,656 B | 168 lines / **15,661 B** | **0 lines / +1,005 B** |
| `docs/SPECS/appx/spec-006-…-rationale.md` | 654 / 46,814 | 734 / **52,621** | +80 / +5,807 |

**Line count is unchanged because all four spec edits are in-place sentence replacements** inside existing
paragraphs and list items — no heading, bullet, or fence moved, which is also why the seven glossary
carriers stayed at their measured lines. The +1,005 B is measured per line, not apportioned by estimate:
`:17` **+285**, `:44` **+219**, `:76` **+141**, `:89` **+360** (byte deltas of the replaced lines, summing
to 1,005). Three of the four now carry a distinction the sentence previously left implicit; the largest,
`:89`, carries both the prohibition and the scope clause that settles it. No compression was attempted to
improve the number.

`docs/SPECS/spec-002-optimizer-0_0_2.md` and its rationale were **not reopened** — the retirement is
finished and verified, and closing this Medium did not require them. Both are byte-identical to their R2
figures (9,647 / 41,291).

### Validation run

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md
OK: 7 terms - all have glossary entries and at least one spec link.
(exit 0)

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-006-public_surface-0_0_3.md \
    docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md
(no output; exit 0)

$ (cd examples/fakeshop && PYTHONPATH=. DJANGO_SETTINGS_MODULE=config.test_settings \
     uv run python manage.py import_spec_terms --check)
OK: 49 done cards have glossary links.
```

**The 7-anchor constraint: no carrier was threatened, and that was verified rather than assumed.** The four
edited sentences carry no glossary reference. Re-derived by parsing reference-style uses: exactly **7**
glossary refs, each used **once**, at `spec-006:19` (`metaprimary`), `:53` (`djangooptimizerextension`,
`optimizerhint`, `schema-audit`, `queryset-diffing`), `:108` (`djangotype`, `filterset`) — the same three
lines R2 landed them on and the review confirmed. The terms CSV was never opened; it is absent from
`git status --porcelain` while tracked by `git ls-files`.

**Scaffold:** both files pass `--check`; all 10 canonical group headers present and in canonical order; the
appended rationale section adds **no** link definition (it reuses `[spec-006-surface]`, `[spec-006-reexport]`,
`[spec-006-subsystem]`, `[spec-006-readme]`), so the count stays 16 with 0 undefined uses and 0 unused
definitions, every target on disk.

**`AGENTS.md` rule 27:** `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both durable files → **no match**
(exit 1). Raw `path:NN` appears only in this artifact, where it is legal.

**Rule 1 — the spec still narrates no history.** The four rewritten sentences are present-tense contract
statements; no amendment block, retraction, "as of", round, or date was added, and every explanation of the
change went to the rationale keyed by heading.

### DRY re-derivation after the edits

`docs/builder/temp-tests/r2/shingle.py`, `[A-Za-z0-9_]+` tokenizer, case-folded, scaffold cut at
`<!-- LINK DEFINITIONS -->`:

- **Spec vs its own rationale: 3 distinct shingles at n=8**, all three windows over the section heading
  `### When a subsystem is top-level vs subpackage-only`, which rule 1 obliges the rationale to cite. Same
  figure and same tuples as R2's close and as the review's independent run.
- **The first draft measured 4**, and the fourth was mine: a *Claims the spec no longer makes* line that
  reproduced the spec's own phrase for a boundary family instead of naming it. Rewritten to name the
  subject; back to 3. Recorded because it is the third time in this cycle that explaining a correction by
  reproducing the corrected sentence was the DRY defect.
- n=6 residue **26** (R2: 18 for a smaller pair): every added one is a heading, a document-path pair, or a
  technical phrase that diverges before n=8. The two that read closest to restatement — the rationale
  naming the bullet/group distinction and the per-feature-marker phrase — are the entries whose job is to
  record what the corrected sentences now say, and neither is a second site that can go stale
  independently.

### Declarations

- **Hot-path budget:** none. The plan declares hot-path `none` cycle-wide and this pass runs no code.
- **Floor verification:** none. No Django / Strawberry / channels seam is touched.
- **Failability proofs:** not applicable — no executable line is written, so no boundary, guard, or
  rejection path exists to fail, and no fail-open shape is possible.
- **No `pytest --cov*` was run**, and no test was run at all: the diff is two markdown files.
- **Source and tests: untouched.** `git diff --name-only` over the writable set is the two durable files;
  `django_strawberry_framework/__init__.py` is clean.

### Concurrent work — reported, not touched

HEAD unmoved at **`947f7494`**. The concurrent session's source and test churn
(`_boundary_ordering.py`, `middleware/request_body.py`, `tests/test_views.py`,
`examples/fakeshop/test_query/test_transport_api.py`) is baseline-dirty and out of scope: not read, not
reverted, no `git checkout`. `KANBAN.md` / `KANBAN.html` / `db.sqlite3` remain the card-wrap's, and
`docs/SPECS/spec-007-…md` plus its untracked rationale remain the other cycle's. The five deleted committed
`docs/review/rev-*.md` files and the two untracked `docs/review/` files are still escalated and still
untouched.

### Review outcome

`Status: planned` per `### Deviation 2`'s corollary — Worker 0 reads `planned` on this artifact as
"dispatch Worker 3". One Medium closed at all three sites, two artifact-record Lows corrected in this
section, one judgement Low settled as a rule with its reasoning in the rationale. Nothing widened: the
glossary document, the four missing roster bullets (R3's), the three ungrouped boundary families (card
052's), and spec-002's finished retirement were all left alone.

---

## Review (Worker 3, pass 2)

Fresh invocation. I read the prior review section as another worker's findings and re-derived every number
in the apply-changes pass rather than accepting it. Scope held to the fix: four in-place spec sentences
(`:17`, `:44`, `:76`, `:89`) plus one appended rationale section. Accepted ground from pass 1 was not
reopened.

### High:

None.

### Medium:

None. **The pass-1 Medium is closed at all three sites**, re-derived rather than read off the fix report.

`docs/GLOSSARY.md` read from `## Public exports` (line 22) to the next `## ` heading (line **83**,
`## Index`; the fix report says 82, off by one and immaterial): **44 bullets in four groups** — root
roster 34 (lines 26-59), `extensions` 1 (`DjangoDebugExtension`), `testing` 8 (lines 67-74, the eighth
pairing `global_id_for` / `decode_global_id`), `auth` 1 bullet naming four field factories (line 79).

**The `auth` refinement is correct and I adopt it.** My pass-1 wording ("four bullets") was wrong on the
count: the four factories share one bullet. It matters to the fix rather than being pedantry, because the
sentence the fix writes at `:17` rests on the bullet-vs-group distinction, and a group whose single bullet
carries four names is what proves the *group* is the placement unit while the *bullet* is the documentation
unit. Had the `auth` group been four bullets, "one bullet per name" would still have been salvageable as
the section's shape and the correction could have been narrower.

**The decisive test, re-run at the three sites pass 1 used to prove the defect:** `TestClient` (testing
group), `DjangoDebugExtension` (extensions group), and `login_mutation` (inside the `auth` group's bullet)
all now **FAIL** condition 3 as written — none carries a bullet in the root re-export group, and `:44`
states outright that a per-subpackage bullet documents the symbol while recording the opposite placement.
`:76` is now **true for all six families**: `extensions.DjangoDebugExtension`, `testing`, and `auth` are
documented as per-subpackage groups of that section (the placement `:76` now sends them to, instead of
asserting they are *not* there); `views`, `routers`, and `middleware.debug_toolbar` carry their dotted
paths inside their own entries (`docs/GLOSSARY.md` #"django_strawberry_framework/views.py",
#"django_strawberry_framework/routers.py", #"django_strawberry_framework/middleware/debug_toolbar.py"),
which is `:76`'s second licensed placement. Neither branch of `:76` is now vacuous.

### Low:

None. The three pass-1 Lows are closed:

- **D16's citation** — re-derived: `grep -c "Open questions"` → **1**, `grep -c '^## Open questions'` →
  **0**. The corrected command is recorded in the new section, the box stays ticked, and the prior section
  is untouched.
- **The definition count** — re-derived independently, not from the fix report:
  `bld-006-r1-rationale_move.md:169` records the rationale at **7 / 7** after R1; the file carries **16**
  definitions now with 16 uses, so **nine** were added. The corrected number is recorded and the omitted
  `spec-006-reexport` → `#top-level-re-export-rule` is named.
- **`:89`** — settled as a rule; see the coherence and conformance findings under "What looks solid".

### DRY findings

None. Re-derived with my own instrument (`docs/builder/temp-tests/r2/shingle.py`, `[A-Za-z0-9_]+`,
case-folded, scaffold cut at `<!-- LINK DEFINITIONS -->`):

- **Spec vs its own rationale: 3 distinct shingles at n=8**, and **1 at n=10** — all windows over the
  section heading `### When a subsystem is top-level vs subpackage-only`, which rule 1 obliges the rationale
  to cite by heading. Tuple-for-tuple identical to the fix report's figure and to my pass-1 run, so the two
  new rationale entries added no restatement of surviving spec text at the gate width. The fix report's
  account of catching a **fourth** at draft time (a *Claims the spec no longer makes* line reproducing the
  spec's phrase instead of naming its subject) is consistent with what is on disk: both new entries name
  their subject and neither reproduces a corrected sentence.
- **n=6 residue: 23 distinct.** The fix report says 26. Same instrument, so the 3-window gap is a counting
  difference, not a measurement I can reconcile from the artifact; it is not load-bearing, because n=6 residue
  is judged from its sites and every one I read is a heading, a document-path pair, or a technical phrase that
  diverges before n=8. Recorded as a record note, not a finding (see `### Notes for Worker 1`).
- No helper, constant, or code shape exists to consolidate; the existence challenge still has no target in a
  markdown-only diff.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — `__all__` and the re-export list are
unchanged, as this source-read-only cycle requires. Re-verified by import: `len(__all__)` → **37**,
`[n for n in __all__ if not hasattr(p, n)]` → `[]`.

The concurrent session's source and test churn (`django_strawberry_framework/_boundary_ordering.py`,
`django_strawberry_framework/middleware/request_body.py`, `tests/test_views.py`,
`examples/fakeshop/test_query/test_transport_api.py`) is baseline-dirty, out of scope, and **not this
cycle's work**: not read, not reverted, no `git checkout`. `KANBAN.md` / `KANBAN.html` / `db.sqlite3` remain
the card-wrap's and `docs/SPECS/spec-007-…md` plus its untracked companion the other cycle's. The five
deleted committed `docs/review/rev-*.md` files and the two untracked `docs/review/` files are still
escalated to the maintainer and still untouched.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. (`git status --porcelain CHANGELOG.md` empty.)

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Applies in full — the pass edits an archived spec and its rationale. Confirmed:

- **Nothing widened.** `docs/GLOSSARY.md` is **absent from `git status --porcelain`** (opened read-only, as
  the fix report states); the terms CSV is absent while tracked by `git ls-files`; no source, test,
  `KANBAN*`, or DB file was written by this pass. The four missing roster bullets (`DjangoSchema`,
  `DjangoMutationExecutionContext`, `DEFAULT_ERROR_POLICY`, `DEFAULT_RESOURCE_POLICY`) are **still absent**
  from the root group, and the three ungrouped boundary families are **still ungrouped** — both left where
  `### Maintainer decision 2` assigns them (R3 and card 052).
- **`spec-002` and its rationale were not reopened.** Byte-identical to what I verified in pass 1: **100
  lines / 9,647 B** and **592 / 41,291**, with `git diff --numstat` still `0 3` and `57 3`.
- **The spec's change is bounded to lines R2 had already rewritten.** `git diff --numstat` on spec-006 is
  still exactly **`52 62`** — the R2 figure — at an unchanged 168 lines, which is only possible if every
  line pass 2 replaced was already inside R2's changed set. That is a mechanical bound on the claim that no
  heading, bullet, fence, or unreviewed line moved, and it is why the seven glossary carriers stayed on
  their measured lines. The byte arithmetic checks: 14,656 → **15,661** = **+1,005**, equal to the sum of
  the four recorded per-line deltas (285 + 219 + 141 + 360).
- **Links and anchors, re-parsed independently.** Rationale: **16 definitions / 16 uses, 0 undefined, 0
  unused**, every target on disk, every `#anchor` resolving against spec-006's live headings under GitHub
  slugification with code spans stripped, alphabetical within each canonical group. The appended section
  adds no definition (it reuses `[spec-006-surface]`, `[spec-006-reexport]`, `[spec-006-subsystem]`,
  `[spec-006-readme]`), which is what keeps the count at 16. Spec: **8 definitions / 8 uses**, 0 undefined,
  0 unused. No in-page `](#…)` link exists in either file, so nothing can dangle.
- **Gates, run by me and quoted below.** `check_spec_glossary` → `OK: 7 terms`, exit 0;
  `check_trailing_commas --check` exit 0 on both durable files; read-only `import_spec_terms --check` →
  `OK: 49 done cards have glossary links.`; rule-27 sweep `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` over both
  → **no match** (exit 1).
- **No obsolete staging wording, and no script-rendered doc regenerated** — none needed to be; no module
  docstring, `docs/TREE.md`, `docs/GLOSSARY.md`, or `KANBAN*` file is in the diff.

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md
OK: 7 terms - all have glossary entries and at least one spec link.
(exit 0)

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-006-public_surface-0_0_3.md \
    docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md
(no output; exit 0)

$ (cd examples/fakeshop && PYTHONPATH=. DJANGO_SETTINGS_MODULE=config.test_settings \
     uv run python manage.py import_spec_terms --check)
OK: 49 done cards have glossary links.
```

### Failability proofs / hot-path / floor verification

Declared not-applicable rather than omitted, and I confirm each independently:

- **Failability proofs — none owed.** The pass writes no executable line; the diff is two markdown files.
  No boundary, guard, gate, or rejection path exists, so the mandatory re-run floor is computed over an
  empty set and an empty re-run set is legal here. No fail-open shape is possible — there is no expression
  to evaluate.
- **Hot-path budget — not applicable.** The plan declares hot-path `none` cycle-wide and this pass runs no
  code.
- **Floor verification — not applicable.** The plan declares floor scope `none`; no Django / Strawberry /
  channels seam is touched.
- **`scripts/review_inspect.py` — not run, skip recorded with its reason:** its outputs are AST facts about
  `.py` files and this diff contains none.

### What looks solid

- **The gate was narrowed, not weakened, and it is still mechanically applicable.** The failure mode I
  hunted for — a condition 3 that can no longer fail, or one that excludes nothing — is absent. A reader
  takes a symbol, finds its bullet in `## Public exports`, and asks which group the bullet sits in; the
  group's lead-in sentence answers it. The condition now **excludes strictly more** than before: the three
  per-subpackage families (previously satisfiable on the literal text) plus the four roster names with no
  bullet at all. `:47`'s "requirements, never entitlements" keeps `SerializerMutation` coherent — it carries
  a root bullet and stays out of `__all__` under the soft-dependency category at `:21`, satisfying a
  requirement without being entitled to promotion. The fix report's three named non-actions are the right
  three: no "documented anywhere in the glossary" relaxation, no claim about a generated document the spec
  cannot make true, no family register.
- **`:89`, `:95`, and `:100` now read as one rule, and I re-derived the composition rather than accepting
  it.** `:95` sources the *vocabulary* ("no synonyms, no improvisation") and `:89`'s new clause names that
  section explicitly for the words prose may use; `:86`-`:89` fix the *locus* (two generated documents
  publish markers, prose points at them); `:100` fixes the *attachment* (a marker attaches to a feature's
  own entry, never to a document or section). The one reading that would have left residue — `:95`'s "every
  consumer-visible feature mention … uses a marker from that legend" taken as an obligation to stamp every
  mention, which `:89` says prose may not do — is closed inside `:89` itself ("Any status word such prose
  does use comes from the legend"). Three sentences, three distinct jobs, no overlap left to arbitrate.
- **`docs/README.md`'s stamp is conforming under the rule as written, so no non-conformance is exported
  into the concurrent cycle's file.** Verified against that file as it stands: it is **clean** in
  `git status`, and `## Today and coming next` opens by pointing at `TODAY.md` and `docs/GLOSSARY.md` for
  per-feature status before `**Shipped today** (`0.0.14`):` (line 97) heads a group of roughly thirty
  capabilities. That is exactly the shape `:89` licenses — a release-scoped summary over a group, read at
  the scope it is written at, pointing at the per-feature locus — and `:100` independently forbids reading a
  section's claim as a marker for its contents. Worker 1's stated reason for the framing holds: settling
  `:89` as a rule leaves `spec-007`'s file conforming rather than handing it a defect this spec invented in
  its own wording. The alternative it rejected (escalate the stamp as a known non-conformance) would have
  done exactly that, and its rejection is recorded in the rationale.
- **No self-narration entered the new text.** Every added byte is inside four replaced sentences, and I read
  all four as present-tense contract statements. A token sweep over the whole spec for `as of`,
  `previously`, `used to`, `formerly`, `no longer`, `retract`, `amend(ed|ment)`, `originally`, `this
  (pass|round|cycle)`, a `202x-` date, `R1`/`R2`, and `correction` returns **no match** (exit 1). No
  amendment block, no retraction, no chronology, no explanation of a correction; all of that went to the
  rationale keyed by heading, where the two new entries carry the changed premise, three rejected
  alternatives on the first and two on the second, and a *Claims the spec no longer makes* line each — the
  shape the surviving entries use.
- **The two record corrections landed as corrections, not rewrites.** Both appear in the new appended
  section; the prior review and move-report sections are untouched; box counts are unchanged at **30**
  `- [x]` and **2** `- [ ]`, the two being rows 8 and 9 (R3's ORM work), so nothing was un-ticked and no
  deferral was quietly converted.
- **The retirement is complete — final sweep, mine.** `grep -rni 'visibility.status' --include='*.md' .`
  returns **0** occurrences in `docs/SPECS/spec-006-public_surface-0_0_3.md` and **0** in
  `docs/SPECS/spec-002-optimizer-0_0_2.md`. Every survivor is in a licensed class, by file:
  `docs/builder/build-006-*` (14), this artifact (11), `appx/spec-002-…-rationale.md` (11: the
  `## Current state` narrative plus the standing deferral and this cycle's row-4 rewrite and discharge
  entry), `bld-006-r1-rationale_move.md` (7), `appx/spec-006-…-rationale.md` (7: R1's provenance line plus
  this cycle's record), `build-002-optimizer-0_0_2.md` (5), **`KANBAN.md` (2** — rows 8/9, card-052 prose,
  correctly un-ticked and still falsified, which also proves this pass did not touch it), and one each in
  `build-007-…`, `build-003-…`, `bld-007-r1-rationale_move.md`, `bld-003-final.md`, and
  `appx/spec-003-…-rationale.md` (row 10's verbatim quotation). No `#visibility-status` **link definition**
  survives in any durable file — the three remaining hits on that string are card-052 prose, this artifact,
  and the build plan's own table row.
- **The seven anchors are intact and still sole carriers.** Re-parsed reference-style uses: exactly **7**
  glossary refs, each used **once**, at `spec-006:19` (`metaprimary`), `:53` (`djangooptimizerextension`,
  `optimizerhint`, `schema-audit`, `queryset-diffing`), `:108` (`djangotype`, `filterset`) — the same three
  lines as at R2 close, and none of the four edited sentences carries a glossary reference, so no carrier
  was ever at risk. `check_spec_glossary` → `OK: 7 terms`, so card `DONE-006-0.0.3`'s `import_spec_terms`
  chain is unbroken (verified read-only, after the writes).

### Temp test verification

- `docs/builder/temp-tests/r2/shingle.py` — my pass-1 instrument, reused unmodified for the n=8 / n=10 / n=6
  re-derivations above.
- Disposition: **kept as a temp file only** (the directory is gitignored). Nothing to promote — it measures
  documents, not package behavior, and no temp test caught a behavior bug because the diff contains no
  behavior.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Low, accepted — not blocking): `__version__` is a fifth instance of the roster gap, and one
  clause of the fix makes it visible.** `:17` now says "Every bullet links the per-feature entry that
  carries that name's status marker", and the root group's last bullet is
  `` - `__version__` — package version string. `` — a bullet with **no link and no marker**, for a name that
  **is** in `__all__` (verified: `'__version__' in p.__all__` → `True`, 37 names). So condition 3 as written
  is failed by an exported name, exactly as it is failed by the four names with no bullet at all. Resolution
  paths: (a) fold it into `### Maintainer decision 2`'s R3 assignment — the same glossary-DB write plus
  regenerate that adds the four missing roster bullets, making it five sites rather than four; (b) one clause
  in the spec carving out the package metadata name (`__version__` is not a capability and has no per-feature
  entry to link), which is a spec-custody call and yours; (c) reject with a recorded reason if you judge the
  sentence's "every bullet" to be the rule the glossary owes rather than a description of it — in which case
  say so, because the next reader will find the bullet. **Not** by softening `:44`. I am not holding the item
  for this: the fix's own defect is closed, the direction of this residue is the gate being stricter than
  practice (never the reverse), and it is the class this cycle has already escalated once rather than a new
  one.
- **Record note, not a finding: the n=6 shingle residue.** The apply-changes pass reports **26**; the same
  instrument gives me **23**. n=8 and n=10 agree tuple-for-tuple, and n=6 is judged from sites rather than
  counts, so nothing rests on it — but the artifact's number is what your final verification audits, and
  this is the fourth counting discrepancy in the cycle's records (after D16's grep, "six" definitions, and my
  own pass-1 box tally). The class, not any single number, is what deserves the note.
- **Two smaller record slips in the new section, both immaterial and neither worth a pass:** the glossary
  section's next `## ` heading is at line **83**, not 82 (`## Index`); and the four per-line byte deltas are
  recorded as exact figures whose sum (1,005) I can confirm against the file total but whose individual
  values I cannot re-derive, since the pre-pass version of the spec is not on disk or at HEAD. Both are
  scratchpad accuracy, not durable-file accuracy.
- **Nothing else in the item was reopened, and I confirm that as a positive result rather than assuming it.**
  `spec-002` and its rationale are byte-identical to my pass-1 verification, `docs/GLOSSARY.md` and the terms
  CSV are unwritten, R3 still owns the four roster bullets, and card 052 still owns the three ungrouped
  boundary families. The narrowest correct fix was made and nothing rode along with it.

### Review outcome

`review-accepted`. The pass-1 Medium is closed at all three sites and the closure is a **narrowing**: I
re-derived the glossary section's four-group structure myself, adopted the pass's `auth`-group refinement as
correct and load-bearing, and confirmed `TestClient`, `DjangoDebugExtension`, and `login_mutation` all now
fail condition 3 as written while `:76` reads true for all six families with neither placement branch
vacuous. `:89` is settled as a rule that composes cleanly with `:95` and `:100` and leaves
`docs/README.md`'s `**Shipped today**` stamp conforming, so no non-conformance is exported into the
concurrent cycle's file. The two record Lows are corrected in the new section with the prior sections
untouched and no box un-ticked; both numbers were re-derived (`grep -c "Open questions"` → 1 versus
`^## Open questions` → 0; 7 → 16 definitions, so nine added). Nothing widened, no narration entered the four
replaced sentences, the retirement is complete with every survivor licensed, the seven anchors are intact
sole carriers, and every mechanical gate is green. One Low residue — `__version__`'s marker-less bullet — is
escalated with resolution paths rather than blocking, because it is the gate being stricter than the
glossary in the same class already assigned to R3.

---

## Final verification (Worker 1)

Fresh invocation. The artifact above and the working-tree diff were the contract; every number below is
mine, re-derived from the files and the DB rather than read off a prior section. No prior section was
edited. Adapted to a documentation item: where a `## Final verification job` step cannot apply, it is
declared with its reason rather than omitted.

### Summary

R2 is **accepted**. The reconciliation landed as recorded, the retirement is complete and independently
re-swept, the seven single-carrier glossary anchors survive as sole carriers with every mechanical gate
green, the twelfth conditional site is settled by measurement (the citation survives; `spec-005` needed
and got nothing), and the two open boxes are R3's by the plan's own assignment with the deferral recorded
below. I made **no spec edit** — verification found no defect requiring one. The escalated `__version__`
Low is settled as an instruction to R3 rather than a spec carve-out, reasoned below.

### Dispatched findings checklist — box-by-box audit

Box count re-derived first, then box truths: **30 `- [x]`, 2 `- [ ]`**, 32 total, matching the section's
own arithmetic (19 drift rows + 11 retirement rows + 2 beyond-table sites). Every `[x]` was checked for
both substance and the truth of its cited evidence.

**Drift rows D1-D19 — all 19 confirmed, no over-tick.**

- D1 — `__all__` **37** entries; `[n for n in p.__all__ if not hasattr(p, n)]` → `[]` under
  `PYTHONPATH=. DJANGO_SETTINGS_MODULE=config.test_settings`. `## Where the public surface is defined`
  carries pointers and no roster; the two out-of-`__all__` categories are stated at `:21` and no family
  is named (`grep -nE '\b(views|routers|debug_toolbar|testing|extensions\.)\b'` over the spec → no match).
- D2 — `grep -c '^```'` → **4** (two import blocks); the fenced `0.0.3` tuple is gone from the file, and
  gone from HEAD's copy by diff.
- D3, D5, D8, D17 — re-measured at **my** reading time, since a concurrent cycle owns that file:
  `docs/README.md` is **clean** in `git status`, carries **18** `^## ` headings, and
  `## Current surface` / `## Planned surface` / `## Package architecture` are **0** each. The spec makes
  no structural claim about the file; `:34` points the layout non-goal at `docs/TREE.md`.
- D4 — on disk: `filters/`, `orders/`, `management/`, `apps.py`, `permissions.py`, `connection.py` all
  exist; `aggregates/` and `fieldset.py` do not. (`permissions` exists as the module `permissions.py`,
  not a package — which is what the box claims.)
- D6 — `grep -ow iff` → **0**. `:47` states requirements-never-entitlements and `:76` carries the third
  outcome. The retraction is in the rationale's D6 entry under *Claims the spec no longer makes* ("That
  satisfying the four conditions is sufficient for a root export") — read in the file, the one obligation
  R1's hand-off flagged as still open.
- D7 — `:49` states both readings and says the import form does not distinguish them.
- D9 — occurrence counts re-derived per document: `experimental` 0/0/0/0, `aspirational` 0/0/0/0,
  `in flight` 0/0/1/0 across `docs/README.md` / `docs/TREE.md` / `docs/GLOSSARY.md` / `TODAY.md`.
  `GlossaryStatus` → exactly `[('shipped','Shipped'), ('planned','Planned')]`. The legend **is** a
  DB-backed document and it carries five markers including `alpha constraint`, which is what grounds
  `:110`. One record correction below.
- D10 — `convert_choices_to_enum` defined at
  `django_strawberry_framework/types/converters.py::convert_choices_to_enum`.
- D11, D12 — `filterset` now sits in the shipped-tense bullet at `:108`; `metaprimary` at `:19` in the
  `Meta`-key sentence. Both measured, not read (anchor table below).
- D13 — `grep -ln 'spec-006' docs/SPECS/*.md` → spec-006 itself and `spec-005` only. Confirmed.
- D14 — `grep -ci 'visibility.status'` → **0** in spec-006 and **0** in spec-002.
- D15 — the alpha-review bullet is absent from `## References`; the deletion, the rejected alternative,
  and what the bullet was worth are all in the rationale's `## References` entry.
- D16 — verification-only box. Evidence as corrected by the apply-changes pass:
  `grep -c '^## Open questions'` → **0** (the loose form returns **1**, the H1 pointer at `:3`). Correct
  as restated; the box stays ticked.
- D18, D19 — all ten named subpackages declare `__all__`; nothing factory-, walker-, or converter-shaped
  is in the 37-name tuple (regex sweep over `__all__` → empty). Nothing was invented in either section.

**Retirement rows 1-11 — nine confirmed `[x]`, two correctly `[ ]`.**

- Row 1 — proven mechanically (below): exactly three lines deleted from `spec-002`, no restatement added.
  `spec-002` now contains **zero** occurrences of `public`, `export`, or `__init__`, so the disposition
  ("no restatement in spec-002") is a measurement rather than a claim.
- Rows 2, 3 — spec-006's coordination bullet 3 is gone and the `## References` spec-002 entry is restated
  at `:135` naming spec-002 as the subsystem the `0.0.3` decision applies the rule to.
- Rows 4, 5, 6 — proven by diff against HEAD: `:261-262` replaced by a six-line sentence that names
  `## Shipped slices` as what absorbed the content and forward-points to the appended entry; the appended
  `## The discharged deferral …` at `:502-553`; `[spec-002-visibility]` deleted. The deferral paragraph
  the row-5 box says is "left standing" is **untouched** in the diff — verified positively, not inferred.
- Rows 7, 10, 11 (verify-only) — untouched in the diff; the spec-003 rationale hit is the verbatim
  historical quotation, and the `docs/builder/` hits are closed cycles' artifacts.
- Rows 8, 9 — correctly `[ ]`. Both `KANBAN.md` sites are still present and now **falsified**: `:319`
  says `## Visibility status` "stays because two live pointers would break with it" and `:322` says
  spec-006's two sites "are live and correct". Deferral recorded under `### Spec changes made` below.
- The twelfth conditional site and the extra site found by R2's re-sweep — both confirmed; see the
  dedicated sections below.

**No box needed un-ticking and no landed box was left open.** The two `[ ]` boxes carry a route, an owner,
and now a deferral line, so neither is a silent gap.

### Spec status / header-line re-verification (mandatory every spawn)

`spec-006` carries **no** `Status:` / target-release / owner / predecessor header — it never did
(`git show HEAD:` lines 1-8 are the H1 then `## Problem statement`). So there is no status line to
falsify, and the step's real content here is the one header-adjacent line the cycle created:

- **The H1 companion pointer at `:3` is accurate and resolves.** Target
  `appx/spec-006-public_surface-0_0_3-rationale.md` exists (52,621 B on disk). Its three named contents
  each resolve to a real keyed entry: "where the alignment problem came from" → rationale `:87`, "the
  three-section README shape this spec declined" → `:112`, "the release-gating judgement an
  `Open questions` section once recorded" → `:140`. `:91`'s second pointer to the same file is also
  accurate.
- **The release-dated status clause HEAD carried in `## Problem statement`** ("As of 0.0.3, the Layer 2
  optimizer is effective end-to-end, so this spec records … the current exported surface") is gone, which
  is change #1 and is the one genuinely status-shaped sentence the spec had. Verified against HEAD's copy.

### The retirement — confirmed complete, independently

`grep -rni 'visibility.status' --include='*.md' .`, counting **occurrences** per file:

- `docs/SPECS/spec-002-optimizer-0_0_2.md` **0**, `docs/SPECS/spec-006-public_surface-0_0_3.md` **0**.
- Survivors, all licensed: `build-006-…` 15 and this artifact 15 (current cycle's scratchpads);
  `appx/spec-002-…-rationale.md` 11 (the pre-existing `## Current state` narrative, the standing deferral,
  this cycle's row-4 rewrite and discharge entry); `bld-006-r1-…` 7; `appx/spec-006-…-rationale.md` 7
  (R1's provenance line plus this cycle's record); `build-002-…` 5; `KANBAN.md` **6 occurrences on 2
  lines** (rows 8/9, R3's); one each in `build-007-…`, `build-003-…`, `bld-007-r1-…`, `bld-003-final.md`,
  and `appx/spec-003-…-rationale.md` (the verbatim quotation). `KANBAN.html` carries 1, the same card-052
  prose. Nothing outside those classes.
- **No `#visibility-status` link definition and no in-page anchor survives.** `grep -rno` finds the string
  at four sites only: `KANBAN.md:319`, this artifact twice, and the build plan's table row — and the
  `KANBAN.md` one is *prose describing* the removed definition inside card-052 Scope, not a definition or
  an anchor target. Both rationale companions were re-parsed: 16/16 and 18/18 definitions/uses, **0
  undefined, 0 unused**, every target on disk, every `#anchor` resolving against live headings under
  GitHub slugification with code spans stripped, and **no** inline `](#…)` link in either file.
- **`spec-002` reads coherently end to end with the section gone.** Heading sequence `## Purpose` →
  `## Problem statement` → `## Architecture decision` → `## Shipped slices` (O1-O6) →
  `## Coordination with spec-001` → `## References` → `## Implementation checklist`; no status-shaped
  heading left, no gap where the section was. Its own link scaffold has 4 uses / 4 defs, 0 undefined and
  0 unused, and `check_spec_glossary` → `OK: 3 terms`. Nothing else in the file dangles.

### The twelfth site, settled with the measurement

**The citation survives, so `spec-005` needed nothing and I changed nothing in it.** Measured both sides:

- `spec-005:89` claims spec-006's *status-marker vocabulary* cites `### Accepted vs deferred Meta keys`
  **by title**.
- At HEAD that citation sat at `spec-006:108`, inside the old `deferred` marker definition. After the
  reconciliation it sits at **`spec-006:102`** — still inside `### Status-marker vocabulary` (heading
  `:93`, next heading `### Alpha signaling rules` at `:104`) — and still cites the section **by title**:
  "is the contract of `spec-005-django_type_contract-0_0_3.md` \"Accepted vs deferred Meta keys\" and not
  this spec's."

So `spec-005:89` is true in both of its parts (which spec cites, and from which section), and the
conditional licence never opened. `git status --porcelain docs/SPECS/spec-005-…md` is empty: the file was
read, never written.

### Move / edit claims proven mechanically

`git show HEAD:<path>` into a scratch directory **outside** the repository, then `diff`. No `git stash`,
`checkout`, `restore`, or `worktree` was used anywhere in this pass.

| File | HEAD | On disk | Artifact's figure | Match |
|---|---|---|---|---|
| `spec-006-public_surface-0_0_3.md` | 178 / 10,934 | **168 / 15,661** | 168 / 15,661 | yes |
| `spec-002-optimizer-0_0_2.md` | 103 / 9,844 | **100 / 9,647** | 100 / 9,647 | yes |
| `appx/spec-002-…-rationale.md` | 538 / 37,030 | **592 / 41,291** | 592 / 41,291 | yes |
| `appx/spec-006-…-rationale.md` | (new) | **734 / 52,621** | 734 / 52,621 | yes |

`git diff --numstat` is `52 62` / `0 3` / `57 3`, exactly as recorded. The `spec-002` diff is the whole
retirement and nothing else: three deleted lines (`## Visibility status`, its one sentence, the blank),
zero added. The `spec-002` rationale diff is exactly rows 4, 5, 6 — one replaced sentence, two appended
blocks, one deleted link definition — and touches nothing else in a 538-line file.

### The 7-anchor constraint — re-derived, then gated

Reference-style `[text][ref-id]` uses only, code spans masked, scaffold excluded: **7** glossary refs,
each used **exactly once**, at `spec-006:19` (`metaprimary`), `:53` (`djangooptimizerextension`,
`optimizerhint`, `schema-audit`, `queryset-diffing`), `:108` (`djangotype`, `filterset`). All seven are
still sole carriers and the per-anchor table's re-siting claims are correct in all seven rows. The spec's
own scaffold: 8 definitions, 8 used, 0 unused, no inline in-page links.

```
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md
OK: 7 terms - all have glossary entries and at least one spec link.   (exit 0)

$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md
OK: 3 terms - all have glossary entries and at least one spec link.   (exit 0)

$ uv run python scripts/check_trailing_commas.py --check <all four durable files>
(no output; exit 0)

$ (cd examples/fakeshop && PYTHONPATH=. DJANGO_SETTINGS_MODULE=config.test_settings \
     uv run python manage.py import_spec_terms --check)
OK: 49 done cards have glossary links.
```

`docs/SPECS/appx/spec-006-public_surface-0_0_3-terms.csv` is **byte-unchanged**: absent from
`git status --porcelain` while `git ls-files --error-unmatch` confirms it is tracked. The writing form of
`import_spec_terms` was not run. `AGENTS.md` rule 27 sweep over all four durable files → **no match**
(exit 1).

### Failability, fail-open, hot-path, floor, tests — declared, not omitted

- **Failability proofs — not applicable, no boundary.** The item's diff contains no executable line; the
  writable set is four markdown files. No guard, cap, gate, or rejection path was added, so the mandatory
  per-boundary proof set is empty by construction rather than by sampling.
- **Fail-open shapes — not applicable, no executable code.** There is no expression whose value could be
  returned on the permissive side. I read the diff for the catalogued shapes anyway and there is nothing
  to read: markdown only, confirmed by `git diff --numstat` over the writable set.
- **Hot-path budget — none.** The plan declares hot-path `none` cycle-wide and nothing here runs per
  request, resolver, row, connection, or message.
- **Floor-verification scope — none.** The plan declares none; no Django / Strawberry / channels seam is
  touched and no version-sensitive behavior is depended on, so there is no floor claim to close.
- **Focused test run — none applies, and this is a declaration.** No test pins a spec sentence; the plan
  declares the cycle source-and-test-read-only. I ran no `pytest` and, per `worker-1.md` `## Scope`, no
  `--cov*` flag in any form. The executable pin the reconciliation points at
  (`tests/base/test_init.py::test_public_api_surface_is_pinned`) is deliberately untouched — verified by
  its absence from `git status`.

### DRY check across R1's and R2's output — re-derived

Own instrument, tokenizing on `[A-Za-z0-9_]+`, case-folded, scaffold cut at `<!-- LINK DEFINITIONS -->`:

- **Spec vs its own rationale: 3 distinct shingles at n=8, 1 at n=10, 23 at n=6.** All three n=8 windows
  are over the section heading `### When a subsystem is top-level vs subpackage-only`, which rule 1
  obliges the rationale to cite by heading — quoted as measured:
  `a subsystem is top level vs subpackage only`, `when a subsystem is top level vs subpackage`, and
  `tuple when a subsystem is top level vs` (the n=10 window is `tuple when a subsystem is top level vs
  subpackage only`). Nothing else in the rationale restates surviving spec prose at the gate width. No
  DRY finding.
- **Spec-006's rationale vs `appx/spec-002-…-rationale.md`: 182 shingles at n=8**, against controls of
  **247** (006-vs-005) and **167** (002-vs-005), and 44 pair-unique after subtracting the 005 and 001
  companions. The pair is *less* coupled than the 006/005 control, so the raw total is house template.
- **Judged by claim, not by phrasing, as required.** The two retirement records are ownership-split and
  neither restates the other's claims: spec-006's entry records only why this spec stopped requesting a
  copy and says outright that the section's own disposition is argued in spec-002's companion, declining
  to restate the two heading alternatives; spec-002's entry owns the section's disposition, the merged
  `__init__`-export precision's deliberate loss, and both rejected alternatives about the heading. The one
  fact both must state — that the copy existed because spec-006 asked for one — is each record's own
  premise, stated from its own side with a pointer to the other for the detail. It is a single fact about
  a bullet that no longer exists, so it cannot go stale in one file and not the other, and dropping it
  from either record would make that record unreadable alone.

### The escalated Low — settled

**Decision: it is a fifth roster site handed to R3 as an instruction, and the spec is not edited.**
Re-derived first: the root re-export group carries **34** bullets, the four names with no bullet are
`DjangoSchema`, `DjangoMutationExecutionContext`, `DEFAULT_ERROR_POLICY`, `DEFAULT_RESOURCE_POLICY`,
`SerializerMutation` is the one roster bullet outside `__all__`, and **exactly one** of the section's 44
bullets carries no link at all — `` - `__version__` — package version string. `` at `docs/GLOSSARY.md:59`
— for a name that is in `__all__` (`'__version__' in p.__all__` → `True`). Worker 3's escalation is
correct in every particular.

Why an instruction rather than a spec change:

- **The residue's direction is the gate being stricter than the glossary**, which is the correct
  direction and the same class the cycle already assigned to R3 for the four missing bullets. The
  honest repair is to make the generated document satisfy the condition, not to carve a name out of it.
- **A carve-out would be the move this pass's own fix refused.** Pass 2 closed its Medium by narrowing
  the locus rather than asserting a shape the generated file lacks or relaxing the condition; exempting
  `__version__` at `:44` would resolve a document gap by editing the gate, which is the failure this
  cycle exists to repair. Condition 3 at `:44` is untouched, as the dispatch requires.
- **Rejected — (b) a spec carve-out for package metadata.** Defensible on the merits (a version string is
  not a capability and has no per-feature entry) but it buys one sentence of tidiness at the cost of the
  first exception in a gate this cycle just finished de-exceptioning, and the exception would be
  permanent while the glossary gap is a one-line write.
- **Rejected — (c) reject with a recorded reason.** The next reader re-derives the 44 bullets and finds
  the unlinked one, exactly as Worker 3 did; leaving it unassigned recreates the cycle's root cause (an
  obligation nothing checks and nobody owns).
- **No rationale edit is owed**, because this decision changes no decision's meaning and produces no spec
  edit. R3 inherits an instruction with a conditional route (below), not a question.

### Spec changes made (Worker 1 only)

**No spec edit was made in this pass.** Verification found no defect requiring one, and the item's own
apply-changes pass had already closed the Medium at all three sites; a further edit would have been more
than corrective, which `worker-1.md` `## Spec custody` routes to `revision-needed` rather than to a late
silent change. Nothing in `spec-005` was touched either — item 4's measurement closed the conditional
licence without opening it.

Deferral reasons for the two boxes still `- [ ]`:

- **Row 8** — `KANBAN.md:319` card-052 Scope, the standing deferral of the retirement. Deferred to **R3**
  by the plan's own assignment (`### The coordinated retirement — every inbound site`, Item column). It is
  a `CardItem.text` ORM write plus a regenerate; `KANBAN.md` is generated and a hand edit would be
  reverted by the next render. Now falsified rather than stale.
- **Row 9** — `KANBAN.md:322`, same card, the "both are live and correct" sentence about spec-006's two
  sites. Deferred to **R3**, same route and same reason. Also falsified: both sites are gone.

**Record corrections, none of them durable-file defects and none warranting a re-pass** (the prior
sections are not edited; these are the audit's findings about them):

1. **D9's evidence names a model that does not exist.** The box and `### Re-derivation of every drift row`
   cite "`GlossaryDocument` key `status-legend`". There is no `GlossaryDocument` model: the row is
   `apps.kanban.models.BoardDoc` with `namespace='glossary'`, `key='status-legend'`, and
   `GlossaryDocumentType` is the *GraphQL type* over it (`apps/glossary/schema.py`). The box's substance
   is true and independently verified — the legend is DB-backed, rendered by
   `scripts/build_glossary_md.py::render_markdown` (which emits `status-legend` before `public-exports`),
   and the row's body carries the five markers including `alpha constraint`. The spec sentence that rests
   on it (`:95`, "it renders from the glossary database") is accurate, so the imprecision is confined to
   this scratchpad. Box stays ticked. **Fourth instance of the cycle's recurring class**: right substance,
   loose citation.
2. **The n=6 shingle residue is 23, not 26.** Same instrument and tokenizer; n=8 and n=10 agree
   tuple-for-tuple with both the apply-changes pass and the review. n=6 is judged from sites, so nothing
   rests on the count, but the artifact's number is not reproducible and 23 is.
3. **Worker 3's pass-2 survivor tally counts `KANBAN.md` as 2** — that is matching *lines*; the file
   carries **6 occurrences** on those 2 lines (plus 1 in `KANBAN.html`). Both lines are rows 8/9, so the
   classification is right and only the unit is wrong.
4. Two immaterial ranges: the appended spec-002 rationale entry spans `:502-553`, recorded as `503-552`;
   the glossary section's next `## ` heading is line **83**, as Worker 3 corrected.

### Hand-off to R3

R3 owns the DB work, the durable-doc audit, the three-direction cross-reference sweep, and the
staged-anchor sweep. What it inherits, with the measurements it therefore need not re-derive from scratch
(but should re-confirm, since it writes a DB two other sessions also write):

**1. The `docs/GLOSSARY.md` `## Public exports` roster bullets — five sites, not four.** The section runs
`docs/GLOSSARY.md:22` to `:83` (`## Index`) and holds **four** bullet groups: the root roster (34 bullets,
`:25-59`), `extensions` (1), `testing` (8), `auth` (1 bullet naming four factories). All five sites below
belong in the **root re-export group**, because that group is what condition 3 reads:

- `DjangoSchema` — no bullet at all. Add one.
- `DjangoMutationExecutionContext` — no bullet at all. Add one.
- `DEFAULT_ERROR_POLICY` — named inline inside the `ErrorPolicy` bullet; owes its own bullet.
- `DEFAULT_RESOURCE_POLICY` — named inline inside the `ResourcePolicy` bullet; owes its own bullet.
- **`__version__` — has a bullet, at `docs/GLOSSARY.md:59`, with no link and no marker.** This is the
  fifth site, added by this final verification. Give the bullet a link to an existing anchor so it carries
  a marker, under the many-bullets-to-one-anchor shape the `SerializerMutation` and
  `RESOURCE_LIMIT_ERROR_CODE` bullets already establish. **Conditional route, so this is an instruction
  and not a question:** I measured no version-related glossary term or anchor today, so if no existing
  anchor is a defensible target, do **not** author a new entry — authoring one is an entry-granularity
  call and `### Maintainer decision 2` assigns that family to card 052. In that case record `__version__`
  on card 052's list beside the open `DjangoSchema`-entry question, state the residue in the R3 artifact,
  and change nothing in the spec. Either way `:44` is not to be weakened.
- Whether `DjangoSchema` earns a **full entry with its own anchor** remains card 052's, per the plan. A
  bullet may point at an existing anchor.

**2. The two `KANBAN.md` line references, and what each must come to say.** ORM `CardItem.text` on card
`TODO-ALPHA-052-0.1.0`, then regenerate; never a hand edit of `KANBAN.md` or `KANBAN.html`.

- **`KANBAN.md:319`** (retirement row 8) currently says spec-002 "carries one status-shaped section left:
  `## Visibility status`", that it "stays because two live pointers would break with it", names spec-006's
  two citations as those pointers, notes the companion's `#visibility-status` link definition, and
  instructs "Retire the heading in the cycle that owns `spec-006`, not this one". Every clause of that is
  now discharged. It must come to say: the heading **is retired**, by the spec-006 residual cycle, as a
  cross-spec duplicate under the single-ownership law; spec-006's two citing bullets are gone; the
  companion's `#visibility-status` definition is removed and the sentence that used it now names
  `## Shipped slices` as what absorbed the content; the discharge is recorded in
  `appx/spec-002-…-rationale.md`'s appended `## The discharged deferral …`. spec-002 now carries **no**
  status-shaped section.
- **`KANBAN.md:322`** (row 9) currently ends "Do not sweep up `spec-006-public_surface-0_0_3.md:136` and
  `:147` in the same pass: both name `## Visibility status`, and both are live and correct." That
  sentence is falsified — both sites are gone and the spec is now 168 lines, so neither line number
  resolves. It must come to say the two sites were retired with the heading in the spec-006 cycle, so
  nothing in spec-006 names the section; the rest of that bullet (the live spec-003 divergence this card
  must settle) is unaffected and stays.
- **`bld-003-final.md` item 7 records `KANBAN.md:314` as a fifth card-052-adjacent site** the plan's table
  omits. Not this cycle's to write beyond noting it: the card-052 closeout should sweep five sites.

**3. Every claim R2 made about `docs/GLOSSARY.md` that the regenerate must not break.** These are what the
spec's gate now reads, so a regenerate that changes any of them changes the spec's meaning:

- The section keeps **four groups distinguished by lead-in sentence**, with the root roster first. `:17`'s
  bullet-vs-group distinction, `:44`'s "root re-export group", and `:76`'s two licensed placements all
  rest on that shape.
- `extensions` / `testing` / `auth` stay as **per-subpackage groups inside the section** — `:76` now sends
  boundary families there, so demoting them out of the section would falsify it.
- `views`, `routers`, `middleware.debug_toolbar` keep their dotted paths **in-entry**; adding group
  listings for them is card 052's, explicitly not R3's (the plan's `CORRECTION`).
- `SerializerMutation` keeps its root bullet while staying out of `__all__`, and the bullet keeps saying
  why: `:47`'s requirements-never-entitlements plus `:21`'s soft-dependency category is what makes it
  coherent.
- `## Status legend` stays the single source of the vocabulary and keeps carrying `alpha constraint` —
  `:95` delegates to it and `:110`'s third signaling case keys to that marker. It renders from the
  `status-legend` document row (`apps.kanban.models.BoardDoc`, `namespace='glossary'`), emitted by
  `scripts/build_glossary_md.py::render_markdown` ahead of `public-exports`.
- After R3's writes, re-run the **read-only** `import_spec_terms --check` (mine: `OK: 49 done cards have
  glossary links.`) and both `check_spec_glossary` runs. Verify by two-consecutive-regenerate byte
  stability against a baseline regenerate-to-temp taken **before** any DB edit, per the plan — `db.sqlite3`,
  `KANBAN.md`, and `KANBAN.html` are all dirty from a concurrent card-wrap, so "`git diff` is clean" is
  available as a verification for none of them. Apply on top; revert nothing.

**4. The plan's `CORRECTION` boundary, restated so it is not re-litigated.** The three missing
boundary-family groups (`views`, `routers`, `middleware.debug_toolbar`) are **card 052's, not R3's**. R3's
glossary scope is the five roster sites in item 1 and nothing else.

**5. Sweeps R3 still owns**, with my baseline: `grep -rEn 'TODO\(spec-006|TODO-(ALPHA|BETA|STABLE)-006' .`
was zero outside `KANBAN*` at pre-flight and I did not re-run it; the three-direction cross-reference
sweep should confirm `spec-005:89` remains the only inbound spec reference (mine:
`grep -ln 'spec-006' docs/SPECS/*.md` → spec-006 and spec-005 only) and that `SpecDoc.path` still reads
the archived path. `docs/SPECS/appx/spec-006-…-terms.csv` is byte-unchanged and must stay so — the anchor
set is 7 and `import_spec_terms` rebuilds card `DONE-006-0.0.3`'s links from it.

### Concurrent work — reported, not touched

HEAD re-derived: **`947f7494`**, unmoved. **This cycle's work was not swept into another session's
commit**, proven with `git log --stat` over the cycle's four durable paths, not `git status`: the newest
commits touching them are `a76da376` (spec-002 rationale) and `d613887c` (spec-002), both 2026-08-07, and
`ff65666d` for spec-006 — all predating this cycle; the rationale companion is untracked. All four remain
dirty/untracked as expected.

**Fourth growth event**, reported for Worker 0 to append to the plan; nothing reverted, nothing read into:

- `docs/builder/bld-007-r2-spec_reconciliation.md` (`??`) is new since R2's pass — the concurrent spec-007
  residual cycle is now at its own R2. `docs/SPECS/spec-007-…md` (`M`) and
  `appx/spec-007-…-rationale.md` (`??`) persist. That cycle owns `docs/README.md`; I re-measured every
  claim about that file at my own reading time and it is **clean** in `git status`.
- The source and test churn (`_boundary_ordering.py`, `middleware/request_body.py`, `tests/test_views.py`,
  `examples/fakeshop/test_query/test_transport_api.py`) and `docs/review/rev-_boundary_ordering.md` /
  `review-0_0_14.md` are the transport session's: not read, not reverted, no `git checkout`.
- The five deleted committed `docs/review/rev-*.md` files persist, still escalated to the maintainer,
  still untouched. Content is safe at `947f7494`.
- `KANBAN.md` / `KANBAN.html` / `examples/fakeshop/db.sqlite3` remain the card-wrap's. This pass wrote
  none of them, and read `KANBAN.md` only.

### Review outcome

`final-accepted`. The 32-box checklist audits clean: 30 ticks each confirmed for substance **and** cited
evidence, 2 correctly open with a route, an owner, and a recorded deferral. The retirement is complete and
independently re-swept — 0 occurrences in either spec, every survivor licensed, no `#visibility-status`
definition or in-page anchor anywhere durable, and `spec-002` coherent end to end with nothing dangling.
The twelfth conditional site is settled by measurement: the by-title citation survives at `spec-006:102`,
still inside `### Status-marker vocabulary`, so `spec-005:89` is true and `spec-005` was never written.
Every move claim was proven against `git show HEAD:` copies outside the repository. All seven glossary
anchors are sole carriers at `:19` / `:53` / `:108`, both `check_spec_glossary` runs and the read-only
`import_spec_terms --check` are green, the terms CSV is byte-unchanged, and the scaffold and rule-27 gates
pass on all four durable files. DRY re-derives to 3 shingles at n=8, all one obligatory heading citation,
and the two retirement records are ownership-split with no duplicated claim. Failability, fail-open,
hot-path, floor, and focused-test are each declared not-applicable with the reason. The escalated
`__version__` Low is settled as R3's fifth roster site with a conditional route, leaving `:44`
untouched — the four record corrections are scratchpad accuracy, not durable-file defects, and none of
them is worth a re-pass.
