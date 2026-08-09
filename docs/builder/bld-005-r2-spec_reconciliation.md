# Build: R2 — Reconcile spec-005 with HEAD

Spec reference: `docs/SPECS/spec-005-django_type_contract-0_0_3.md` (whole file; every section except the two headings `## Problem statement` and `## Coordination …` was rewritten, removed, or retitled)
Rationale file appended: `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md`
Status: revision-needed

**Shape note.** Per `docs/builder/build-005-django_type_contract-0_0_3.md` Deviation 2, R2 has no Worker 2 pass: `docs/builder/BUILD.md` `## Spec reconciliation` and `worker-1.md` `## Scope` make Worker 1 the only role that may mutate the spec, and R2's entire deliverable is spec edits. So `docs/builder/ARTIFACT.md`'s `## Build report (Worker 2)` is not applicable and the performance record lives under `## Reconciliation report (Worker 1)` below, carrying the same fields Worker 3 would otherwise read from a build report. `Status:` is `planned` on return, which Worker 0 reads as "dispatch Worker 3" for this item.

`HEAD` re-derived rather than quoted: `ff03c1372365edcad488ff4671389d88ae145276`, unchanged since R1's final verification closed. No `git stash` / `checkout` / `restore` / `worktree`, no branch, no commit, no `pytest`, no coverage-shaped flag, no write to source, tests, `examples/`, a sibling spec, the terms CSV, `CHANGELOG.md`, `KANBAN*`, `docs/GLOSSARY.md`, or the DB.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable, and deliberately so. `worker-1.md` `### Package-wide helper inventory before helper planning` gates *helper-like logic*; R2 changes no package source and adds no helper, shared constant, validation branch, coercion utility, or test helper. The build plan's `## Build-wide context flags` declares package source, `tests/`, and `examples/` read-only for the whole cycle. No inventory was refreshed and none was needed.
- **Existing patterns reused.** The R1 artifact's per-entry vocabulary (`*Moved*`, `*Claims the section no longer makes.*`, one entry keyed by heading plus a resolving anchor) is reused verbatim as the shape of R2's rationale entries, so the two layers of one file read as one file. The `**Contract.**` label replacing `**Decision for 0.0.3.**` follows the sibling-spec convention of a bolded lead-in on a normative block without a version stamp.
- **New helpers justified.** None; no code was written.
- **Duplication risk avoided.** Three live risks, each measured rather than asserted, and the first two are the ones this pass actually tripped and had to fix:
  - **Spec vs. rationale.** The maintainer's framing splits them absolutely — the spec carries the contract, the rationale carries the explanation. The measurement is the shingle intersection over both file **bodies** (everything before `<!-- LINK DEFINITIONS -->`, which removes the scaffold by construction). **First draft: 5 non-scaffold 8-word overlaps punctuation-kept, 15 punctuation-stripped.** Every one was the rationale restating current contract prose. Six rewrites later the figure is **0 at n=8 under both tokenizers**; see `### Eight duplications caught by measurement`.
  - **Against the anti-inventory trap.** The pull named by the build plan is to refresh `ALLOWED_META_KEYS` into the spec. Refusing it *is* the DRY decision for this pass: a roster in a spec is a copy of an executable frozenset. The spec now names the source and the glossary and lists neither roster.
  - **Against the owning siblings.** `spec-018` / `spec-019` / `spec-015` / `spec-027` / `spec-028` own the surfaces that superseded three of the four topics. Every reference to them is a pointer plus a spec-005-specific requirement; no rule of theirs is restated. Measured at 0 substantive overlap (`### Validation run`).

### Implementation steps

Line numbers are pin-at-write-time; pre-edit numbers are against the post-R1 spec (132 lines / 11,002 bytes).

1. Re-derive `HEAD`; take a read-only `git show HEAD:` copy of the spec into the scratchpad **outside** the repo. Done.
2. Re-verify all 20 drift rows against source with symbol-qualified paths rather than trusting the plan's table; sweep for rows the table missed. Done — `### Drift-row disposition`, which adds two rows and corrects one plan citation.
3. Re-run the read-only correctness audit for every claim the rewrite would rely on (17 allowed keys applied, 3 deferred genuinely unshipped, `_select_fields` raises in both arms, the sentinel's stamping order and second consumer). Done — `### The read-only correctness audit, re-verified`.
4. Rewrite `## Problem statement` (spec:5-14) from a dated four-gap report into four durable failure classes, keeping the `djangotype` / `metafields` / `metaexclude` anchors inside it. Done.
5. Remove `## Current state` (spec:16-31) whole, **re-siting the `metaprimary` anchor into `### One model, many types, one primary` in the same edit**, and restating the sentinel's durable half in `## Coordination …`. Done — hand-off 1 discharged.
6. Correct `## Goal` bullet 1 (D11/D20) and `## Non-goals` (D17). Done.
7. Rewrite and retitle the two falsified topics; rewrite the key-partition topic to the rule, not the roster; widen the selection topic to the shared error helper. Done.
8. Rewrite `## Coordination …`'s never-followed instruction (D18) and `## References` (D19). Done.
9. Append the rationale's R2 layer — one entry per rewritten section, keyed by heading and anchor, each carrying what changed, why, the rejected alternatives, and the claims the section may no longer make. Re-key the two entries whose spec headings this pass retitled, and add the six new link definitions their anchors need. Done.
10. Run the full verification set; record every command with its result. Done — `### Validation run`.

### Test additions / updates

None. R2 adds no test and changes no code path. The verification for this item is the command set recorded under `### Validation run`; `AGENTS.md` rule 15 forbids a `pytest` run that was not asked for, and the build plan declares no residual item touches source, tests, or `examples/`.

### Implementation discretion items

None reserved. R2 has no downstream builder, so nothing is delegable.

### Dispatched findings checklist

There is no `## Slice checklist` in spec-005 and this is not a review round, so — per `worker-1.md` planning step 8, which puts a `### Dispatched findings checklist` in this position when no spec slice checklist exists — the boxes below are R2's obligations drawn from the maintainer's framing, `docs/builder/BUILD.md` `## Spec reconciliation` and `## Spec rationale extraction`, the build plan's R2 constraints, and R1's eleven hand-offs plus the extended twelfth. Worker 1 both performs and ticks here because Deviation 2 removes the Worker 2 pass; the ticks are audited at Worker 1's own final verification after Worker 3.

- [x] Every claim the spec makes was checked against source at HEAD, symbol-qualified, and each of the plan's 20 drift rows re-verified rather than inherited.
- [x] The full sweep was run: the 20 rows were treated as a floor, and rows the table missed were found and recorded (two: D21, D22).
- [x] The spec states what holds today. No amendment block, no retraction paragraph, no "as of `0.0.6`" hedge, no chronology anywhere in it.
- [x] `## Current state` — a release-status section by construction — was removed rather than refreshed.
- [x] Every explanation of a change went to the rationale, keyed to the spec section it serves by heading and a resolving anchor.
- [x] Each rationale entry carries the rejected alternatives with the one-line reason each lost.
- [x] Each rationale entry carries the claims its section may no longer make.
- [x] The anti-inventory trap was refused: no `ALLOWED_META_KEYS` / `DEFERRED_META_KEYS` roster is restated in the spec; the source set and `docs/GLOSSARY.md` are named as the single sources.
- [x] The over-absorption trap was refused: spec-018 / spec-019 / spec-010 / spec-015 / spec-027 / spec-028 are named as owners and none of their rules is restated. All read-only; none edited.
- [x] `metaprimary`'s sole carrier was re-sited **in the same edit** that removed `## Current state`, into surviving contract prose, never by re-adding narration and never by editing the CSV (hand-off 1).
- [x] `djangotype` / `configurationerror` / `metainterfaces` / `metafields` / `metaexclude` were likewise re-sited or preserved inside rewritten prose (hand-off 2).
- [x] `check_spec_glossary.py --spec …` re-run after the edits and quoted: `OK: 7 terms`; all 7 anchors at exactly 1 body use + 1 definition.
- [x] `check_trailing_commas.py --check` re-run and quoted on both files.
- [x] `### Accepted vs deferred Meta keys` keeps the title string `spec-006` cites; the inbound reference resolves (hand-off 7).
- [x] Every in-page anchor the rationale targets resolves against a real post-R2 spec heading; the two retitled sections' definitions were updated in this pass.
- [x] Reference-style links only; `<!-- LINK DEFINITIONS -->` present with all 10 canonical group headers in order; every definition target disk-checked; 0 undefined and 0 unused in both files.
- [x] `AGENTS.md` rule 27 holds in both durable files: no raw `path:NN`.
- [x] Extended hand-off 9 obeyed: the rationale's two quotations/condensations of spec claims R2 corrected were **not** synced away (D5's override diagnosis, D18's "must update this contract spec accordingly").
- [x] D15 confirmed discharged by R1 rather than re-done (hand-off 3); D3 / D4 / D8's spec-side residue closed (hand-off 4); `## Non-goals` treated as load-bearing (hand-off 5); D18 decided with the argument R1 recorded available (hand-off 6); both `**Decision for 0.0.3.**` blocks rewritten as one coherent edit each (hand-off 8); hand-offs 10 and 11 acted on as written.
- [x] Cut-not-copy measured in both directions and at more than one tokenizer, and the line-granularity check driven off `git diff -U0` rather than off hand-chosen spans (hand-off 11).
- [x] Spec byte count before and after reported.
- [x] "Make sure the code is correct" discharged as a read-only audit; no source edit; the two documentation defects found in shipped source are recorded as findings and escalated, not fixed here.
- [x] No source, test, example, sibling spec, terms CSV, `CHANGELOG.md`, `KANBAN*`, `docs/GLOSSARY.md`, or DB file was written.

---

## Reconciliation report (Worker 1)

### Files touched

- `docs/SPECS/spec-005-django_type_contract-0_0_3.md` — rewritten. Against HEAD, `git diff --stat` is `45 insertions(+), 77 deletions(-)` (R1's cuts plus R2's rewrite); against R1's output the change is the whole body below the H1 except two heading lines.
- `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md` — appended: a second entry layer (`## Entries keyed to the spec — the R2 reconciliation`, ten entries), two `## How to read this file` bullets, six new link definitions and one corrected one, and a two-clause re-key on the two entries whose spec heading this pass retitled.

### Byte count (required report)

| | lines | bytes |
|---|---|---|
| spec at HEAD (pre-R1) | 154 | 13,346 |
| spec after R1 | 132 | 11,002 |
| **spec after R2** | **122** | **13,025** |
| net vs. HEAD | -32 | **-321 (-2.4%)** |
| rationale after R1 | 285 | 20,086 |
| **rationale after R2** | **640** | **44,958** |

The spec grew 2,023 bytes against R1's output and still ends smaller than it started. That is the expected shape and worth stating so it is not read as scope creep: R1 cut 2,344 bytes of deliberation, and R2 spent most of them back on **contract** — four failure classes stated as durable rules where four dated gaps stood, three `**Contract.**` blocks, and a corrected sentinel description. The document is 10 lines shorter and every line in it is normative. Fences (`grep -c '^```'`): **0** in both files, at HEAD and now.

The rationale more than doubled, which is where the maintainer's rule sends every byte of explanation. Its R2 layer is 355 lines against the spec's 2,023-byte gain — the intended ratio for a pass whose whole instruction was *the explanation of each change goes in the rationale, never in the spec*.

### Drift-row disposition

Every row re-verified against source at HEAD with the symbol-qualified path, not inherited from the plan. **Two rows the plan's table missed are added (D21, D22); one plan citation is wrong and is corrected (D12).**

| Row | Verified? | Disposition in the spec | Rationale entry that carries the why |
|---|---|---|---|
| D1 | yes | `## Current state` **removed whole**; every "in flight" / release framing gone | `## Current state` |
| D2 | yes — `registry.py::TypeRegistry.register` appends to `_types[model]`; raises only `#"is already the primary type"` and `#"primary flag cannot be flipped on re-register"` | topic rewritten and retitled `### One model, many types, one primary` | `### One model, many types, one primary` |
| D3 | yes — `types/finalizer.py::_audit_primary_ambiguity` runs at Phase 1 | prediction text gone at R1; the spec now states the two rejections and that they fire at different points, without restating spec-018's catalog | same |
| D4 | yes | nothing left in the spec to correct (R1); the three answers stay in R1's entry | same (R1 layer) |
| D5 | yes — the merge at `types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"` puts the consumer last; the gate is `consumer_authored_fields` | diagnosis removed from `## Problem statement` item 2 and from the topic; the topic now states the shipped contract and names why the merge order alone is not it | `### Consumer override semantics` |
| D6 | yes — `grep -n 'Current surface' docs/README.md` → no match; `docs/README.md:111` says the opposite and is correct; the `__init_subclass__` docstring is the single line `"""Collect model/type metadata without finalizing the Strawberry type."""` | the README obligation is gone; its durable half is `**Contract.**` in the override topic | same |
| D7 | yes — `grep -rn test_consumer_annotation_overrides_synthesized tests/ examples/ django_strawberry_framework/` → no match | the promise is replaced by the general rule about placeholder tests | same |
| D8 | yes | nothing left in the spec (R1) | same (R1 layer) |
| D9 | yes — 17 keys in `types/base.py #"ALLOWED_META_KEYS: frozenset[str] = frozenset("` | **roster removed, not refreshed**; the source set is named as authoritative | `### Accepted vs deferred Meta keys` |
| D10 | yes — 3 keys in `#"DEFERRED_META_KEYS: frozenset[str] = frozenset("`: `aggregate_class`, `fields_class`, `search_fields` | roster removed, not refreshed | same |
| D11 | yes — `types/base.py::_validate_meta` raises `#"The feature that owns them has not shipped."` | the bucket description now says the message names a *feature*, never a spec document, with the reason | `## Goal` |
| D12 | yes — the third-category comment is at `types/base.py #"are net-new ALLOWED keys, NOT DEFERRED_META_KEYS promotions"`. **Plan citation wrong:** the second pinning test is `tests/types/test_base.py::test_meta_relation_shapes_in_allowed_meta_keys`, not `::test_relation_shapes_is_shipped_not_deferred`, which does not exist | the third route into `ALLOWED_META_KEYS` added to the section, with both real test names | `### Accepted vs deferred Meta keys` |
| D13 | yes — `interfaces` in `ALLOWED_META_KEYS`, validated by `types/base.py::_validate_interfaces`, injected by `types/relay.py::apply_interfaces` from `types/finalizer.py` Phase 2.5 | the `Meta.interfaces` example is inverted from a past mistake to a current-state fact plus its pinning test — and it is where the `metainterfaces` anchor now lives | same |
| D14 | yes — stamped at `types/base.py::DjangoType.__init_subclass__ #"cls._is_default_get_queryset = not has_custom_get_queryset"`, before the `meta is None` return; `_detect_custom_get_queryset` walks the MRO; the authoritative value is `types/definition.py::DjangoTypeDefinition.has_custom_get_queryset` | restated in `## Coordination …`, corrected and extended | `## Current state` |
| D15 | confirmed discharged by R1 — `grep -n registry.clear` over the spec → no match | none owed | R1 layer |
| D16 | yes — `types/base.py::_select_fields` raises in both arms; all three named tests exist; `_format_unknown_fields_error` has five call sites reaching six keys | section kept, retitled (slash → "and"), and widened to the shared-helper rule | `### Invalid Meta.fields and Meta.exclude names` |
| D17 | yes | `## Non-goals` names the owning specs; "future" gone | `## Non-goals` |
| D18 | yes — no sibling spec has ever edited spec-005 | **instruction retired**; replaced by an obligation on the code that is checkable against source | `## Coordination …` |
| D19 | yes — the alpha review resolves nowhere | that bullet removed; the test bullet corrected; four owning specs added | `## References` |
| D20 | yes — first half holds (audit below); second half is D11 | goal bullet 1 restated | `## Goal` |
| **D21 (new)** | yes — `### One-model-one-type`'s `**Decision for 0.0.3.**` required the constraint be documented in `docs/README.md` "Current surface" with a status marker and a back-reference to this spec. `grep -n spec-005 docs/README.md` → **no match, exit 1**, and there is no `## Current surface` section. **Same shape as D6, which covered only the override half of the same obligation** | not restated; its durable half survives as `## Goal`'s third bullet | `### One model, many types, one primary` |
| **D22 (new)** | yes — the topic's opening paragraph cited `convert_relation` as the symbol a relation resolves through. `grep -rn convert_relation django_strawberry_framework/` → **no match**; the only occurrence anywhere is a stale comment at `tests/types/test_base.py`. Relation targets bind at finalization through `registry.py::TypeRegistry.primary_for` | the symbol is gone from the spec; the surviving reverse-lookup sentence names `model_for_type`, which does exist | same |

### The read-only correctness audit, re-verified

Worker 0's audit found no defect. I re-verified every leg the rewrite leans on rather than citing it.

- **All 17 `ALLOWED_META_KEYS` entries are applied.** Thirteen are fields on `types/definition.py::DjangoTypeDefinition`. The other four are applied without a definition field: `exclude` by `_select_fields` (`#"exclude_spec=validated.exclude_spec"`), and `nullable_overrides` / `required_overrides` / `filesystem_path_fields` threaded into `_build_annotations` (`#"filesystem_path_fields=validated.filesystem_path_fields"`) after their own target validators run. **The `Meta.interfaces` mistake this spec exists to prevent is not repeated.**
- **All 3 `DEFERRED_META_KEYS` entries are genuinely unshipped** and rejected before any other shape gate, parametrized over the set by `tests/types/test_base.py::test_meta_rejects_each_deferred_key`. One adjacent shape checked because it looks like a violation and is not: `DjangoTypeDefinition.fields_class` exists as a field but is documented at `types/definition.py` as forward-reserved and is never populated, which is the *reverse* of the failure the promotion rule forbids (applied-without-a-key, not validated-without-application).
- **`_select_fields` raises in both arms**, and `_format_unknown_fields_error` is reached by five call sites covering six keys: `fields`, `exclude`, `optimizer_hints` (×2 sites), and — via `_selected_meta_targets` — `nullable_overrides` / `required_overrides`, `filesystem_path_fields`, `relation_shapes`.
- **The sentinel is hardened past its description**, exactly as D14 says, and its second consumer is **not** what I first wrote. Caught in this pass by reading `types/finalizer.py #"if previous.has_custom_get_queryset or new.has_custom_get_queryset"` in context: it is a shared-`FilterSet` owner check that fails closed when two owners bind one filterset and either carries an override — not a definition merge. The spec sentence was corrected before this artifact was written.

**Two documentation defects in shipped source, recorded and escalated — not fixed here.** Neither is a correctness defect, so neither is a source edit inside a documentation cycle; both are in `django_strawberry_framework/exceptions.py::ConfigurationError`'s docstring example list. See `### Notes for Worker 1 (spec reconciliation)` items 1 and 2.

### Eight duplications caught by measurement

The shingle intersection is not decoration on this pass either. The first draft of the rationale's R2 layer restated the spec's current contract in **eight** places — every one correct, attributed, and readable, and every one a second copy that would go stale the moment either file moved.

| Overlap | Fix |
|---|---|
| "every later `Meta` key whose value names model fields reuses it" | rationale now says how many keys, not what the rule is |
| "a promotion whose end-to-end check was skipped" | rewritten to the count of affected keys |
| "the field name's membership in the consumer-authored set" | rewritten to "the short-circuit ahead of synthesis" |
| "left standing as if it pinned a contract" | rewritten to "what a placeholder test may be allowed to look like" |
| "the feature that owns them has not shipped" (×2 shingles) | rationale now describes the vocabulary change without quoting the message |
| "a consumer … has no access to `docs/SPECS/`" | replaced by "for the reason the section now gives" |
| "the `meta is None` early return" | rewritten to "earlier in `__init_subclass__` than the section described" |
| "has occupied two of the three buckets" | rewritten to "has been in more than one of them" |
| the ambiguity contract, condensed | rewritten to the *decision* (a requirement on the answer vs. the mechanism) |

Recorded because the failure mode is invisible to reading — the last one especially, which is a **condensation** and matches no verbatim scan. It was found only by the shingle table, which is the second half of R1's own lesson that two detection methods are needed and neither is sufficient alone.

### Validation run

Every command run in this pass; nothing carried over from R1.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-005-django_type_contract-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` **exit 0**. Character-identical to the build plan's pre-flight step-6 baseline. Re-run after every edit batch, four times in total; the quoted result is the final one.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-005-django_type_contract-0_0_3.md docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md` → **exit 0** on both. Both carry `<!-- LINK DEFINITIONS -->` and all 10 canonical group headers in canonical order.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0**. The card-wrap chain the 7-anchor constraint protects is intact, and the run left no DB churn (`git status --short` below).
- **Cut-not-copy / no-restatement, measured at three tokenizations over both file bodies** (everything before `<!-- LINK DEFINITIONS -->`, which removes the scaffold by construction rather than by a filter):

  | tokenizer | n=8 | n=6 |
  |---|---|---|
  | punctuation kept | **0** | 3 |
  | punctuation stripped, `.` and `#` retained | **0** | 6 |

  **0 at n=8 under both tokenizers**, which is the figure R1 could only reach under one. The n=6 survivors are three section headings the keying rule *requires* the rationale to reproduce, plus "the rejection of first-registered-wins" — which appears in the spec's rule-1 pointer sentence (required: a pointer must name what was moved) and in the rationale's entry key (required: an entry must name its section). Both are required by the same two rules, so neither is removable.
- **Line-granularity check, driven off `git diff -U0` rather than hand-chosen spans** (hand-off 11). **65 removed non-empty lines against HEAD.** Two (`## Problem statement`, `## Coordination …`) are hunk-boundary artifacts and are present verbatim in the new file. Of the remaining 63, **18 are R1's cuts**, already proven 18/18 accounted at line granularity by R1's own re-derived check. The **45 R2 removals** were walked one by one against the rewritten spec and the rationale's R2 layer; each is either restated as contract or recorded in a `*Claims the section no longer makes.*` list. Three gaps the walk exposed were closed in this pass before the artifact was written: the "until 0.0.3 `_select_fields` did a set intersection" history, the thread paragraph's dropped "alpha-stage" qualifier, and the promoted "checked at every spec slice" sentence — none of which any span I would have chosen myself would have covered, which is the whole reason the check is driven off the diff.
- **Reference integrity, both durable files, code spans stripped:** spec **8 definitions / 8 distinct uses**, rationale **19 / 19**; **0 undefined and 0 unused in both**. All 27 definition targets resolve on disk from their own file's directory, checked against the live tree.
- **Anchor-bearing targets slug-checked** with `scripts/check_spec_glossary.py::github_anchor` against the target file's real headings: all **9** rationale → spec in-page anchors resolve against the post-R2 spec's 11 headings, and all 7 `docs/GLOSSARY.md` anchors resolve. **Duplicate heading slugs: 0** in the spec (11 headings), **0** in the rationale (19 headings).
- `grep -c '^```'` → spec **0**, rationale **0**. Unchanged; this pass added no fenced block to either.
- `grep -nE '[a-zA-Z_/]+\.(py|md|csv):[0-9]+'` over both durable files → **no match** (exit 1). Rule 27 preserved.
- `grep -P '\]\((?!#|https?:)'` over both → **no match** (exit 1). No inline `](path)` link in either.
- `git status --short` adds exactly `M docs/SPECS/spec-005-django_type_contract-0_0_3.md` (already dirty from R1) and this artifact to the recorded baseline. **`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` are all clean** — the concurrent commit at `ff03c137` swept the plan's `### First growth` set, so the baseline is now the five spec-004-cycle entries plus the four staged-deleted `bld-003-*.md` files, exactly as the plan's second-change note records. Nothing reverted (`AGENTS.md` rule 34).
- **Not swept into a concurrent commit.** `git log --stat` over this cycle's paths: the newest commit reaching **any** of them is `ff65666d` ("docs: normalize review citations to their durable records"), which predates the cycle. `git log` over the rationale and both `bld-005-*` artifacts is empty — never committed. `git status` alone was not used for this determination.
- No `pytest` run (`AGENTS.md` rule 15); no `ruff` run (no `.py` file touched); no coverage-shaped flag in any form.

### The 7-anchor constraint — re-measured after the rewrite

Measured as reference-style body uses only (`]\[glossary-<anchor>]` over the text before `<!-- LINK DEFINITIONS -->`; a plain code span is not a carrier). **All seven stand at exactly 1 use + 1 definition, and four moved.**

| Anchor | Carrier after R1 | **Carrier after R2** | Moved? |
|---|---|---|---|
| `djangotype` | `## Problem statement` item 1 | `## Problem statement` opening (spec:7) | re-sited within a rewritten section |
| `configurationerror` | `## Problem statement` item 1 | `### Invalid …` body (spec:52) | **moved to a different section** |
| `metafields` | `## Problem statement` item 3 | `## Problem statement` failure class 3 (spec:11) | re-sited within a rewritten section |
| `metaexclude` | `## Problem statement` item 3 | `## Problem statement` failure class 3 (spec:11) | re-sited within a rewritten section |
| `metainterfaces` | `## Problem statement` item 4 | `### Accepted vs deferred Meta keys` (spec:75) | **moved to a different section** |
| `metaprimary` | `## Current state` final paragraph | `### One model, many types, one primary` (spec:34) | **moved; its old carrier no longer exists** |
| `metamodel` | `### Invalid …` body | `### Invalid …` body (spec:52) | unchanged |

**Hand-off 1 is discharged in the strongest available form.** `metaprimary`'s sole carrier was `## Current state`'s final paragraph, and that paragraph is not merely rewritten — the whole section is gone. The link was placed into `### One model, many types, one primary`'s contract prose **in the same `Write` that removed the section**, so the file was never on disk in a state where the anchor was uncarried. No narration was kept alive to hold a link; `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-terms.csv` was never opened.

`configurationerror` and `metainterfaces` moved for the same reason and by the same rule: their old carriers were falsified sentences, and each anchor's new home is a current-state sentence in the section whose contract the term belongs to. That is a stronger position than the one R2 inherited — after this pass **no anchor sits in prose the drift table marks falsified**, because no such prose survives.

### Hot-path budget

Not applicable; plan declares no hot path build-wide. No residual item in this cycle changes package source.

### Floor verification

Not applicable; plan declares floor-verification scope `none`. R2 touches no Django / Strawberry / channels integration seam and reasons about no version-dependent behavior.

### Failability proofs

None; this pass introduced no new boundary. R2 edits two Markdown files and adds no guard, gate, or rejection path.

### Implementation notes

- **`## Current state` was removed, not refreshed, and that is the pass's largest single call.** A `## Current state` section is a status report by construction, and a status report inside a contract document is precisely the shape the maintainer's framing forbids — a reader has to date it before they can use it. Refreshing it would have been the smaller diff and would have guaranteed a third reconciliation cycle. Its one durable claim (the `get_queryset` sentinel) was restated in `## Coordination …`, where the optimizer half already lived, so the fact now has one home instead of two.
- **`**Decision for 0.0.3.**` became `**Contract.**`.** The label is itself a version hedge, which the governing rule bans. `**Contract.**` keeps the visual weight the two normative blocks need without stamping them with a release. A consequence worth naming: the rationale's `## Provenance of this record` refers to "the `### Consumer override semantics` `**Decision for 0.0.3.**`", which now reads as a statement about what R1 left rather than about what the spec says. R1's hand-off 10 anticipated exactly this shape and says it needs no edit; I agree and left it.
- **Four topics, three retitles, one heading deliberately frozen.** `### Accepted vs deferred Meta keys` lost only its `(shipped in 0.0.3)` suffix, because `docs/SPECS/spec-006-public_surface-0_0_3.md:108` cites the title *string* and is read-only this cycle. The quoted string is a substring of both the old and the new heading, so the inbound reference still resolves — verified by reading the sibling, which this cycle did not open for writing. **No inbound break to defer.**
- **The rationale's append-only rule bent in exactly one direction, and only for keys.** `worker-1.md` rule 4 makes the file append-only during the build. Retitling two spec sections would otherwise leave two dangling in-page anchors and two entry keys naming headings that no longer exist — which rule 3 of the same section explicitly forbids ("every in-page anchor still resolves"). I updated the two link-definition targets and added a one-sentence parenthetical to each entry naming its old title; **no recorded content was rewritten or removed.** A key is not a record, and a dangling anchor is the larger defect. Recorded here so Worker 3 can charge it if it disagrees.
- **The retitles pick durable names, not merely true ones.** `### One-model-one-type (alpha constraint)` was falsified twice over (the constraint is gone, and "alpha" is a phase). `### One model, many types, one primary` states the shape and survives the next registry change that does not alter the shape. Same test applied to dropping `(deferred to a future spec)` and the two `(shipped in 0.0.3)` suffixes.
- **`### Invalid …`'s slash became "and" for a mechanical reason, not a stylistic one.** The old heading slugs ambiguously: dropping the `/` leaves a double space, which GitHub renders as `--` and this repository's own `github_anchor` collapses to `-`. Nothing linked to it, so the ambiguity was removed while it was free. Recorded because the two sluggers disagreeing is a repo-wide trap, not a spec-005 one.
- **D18 was decided rather than escalated, on the plan's own authority.** The build plan's D18 row states outright that the choice is Worker 1's. The decision — retire the instruction, put the obligation on the code — is written into the spec as contract and its two rejected alternatives are in the rationale. The strongest of the two rejections is worth repeating here: *keep the instruction and add a check to enforce it* is tempting and wrong, because whatever the check verified would be that this document's copy of the key set matches the real one, which is the roster problem with tooling attached.

### Notes for Worker 3

- **The judgement calls most worth attacking, in the order I would attack them.** (a) Removing `## Current state` outright rather than restating it as contract — the largest deletion in the pass. (b) Retiring the `## Coordination …` must-update instruction, which is a rule change and not just a correction. (c) Refusing to list the seventeen accepted keys, which makes the spec less immediately useful and (I argue) more durable. (d) Whether the four rewritten `## Problem statement` failure classes are genuinely durable or just a more abstract way of being dated.
- **Re-derive the shingle intersection, and say which tokenizer.** The number is not tokenizer-independent — R1's cycle proved that twice. I report 0 at n=8 punctuation-kept *and* punctuation-stripped, measured over both file **bodies**. If you measure something else, the tokenizer is the first thing to compare.
- **Re-derive the line-granularity check rather than reading its result.** It is the check that found three gaps in this pass, and none of them was in any span I would have chosen. Note that 18 of the 63 removed lines belong to R1 and were already accounted for by R1's own run.
- **Two spec-side claims to attack mechanically first**, because they are the two I got wrong or nearly wrong: the finalizer's second use of `has_custom_get_queryset` (I first described it as a definition merge; it is a shared-`FilterSet` owner check) and D12's second pinning test name (the plan's name does not exist).
- The read-only HEAD copy of the pre-cycle spec is in the session scratchpad outside the repo. Re-derive it with `git show HEAD:` rather than trusting any file.

### Notes for Worker 1 (spec reconciliation)

Hand-offs to R3 and the final gate. Items 1 and 2 are escalations; the rest are records.

1. **ESCALATED — a falsified example in a shipped docstring.** `django_strawberry_framework/exceptions.py::ConfigurationError` lists among its examples "Two `DjangoType` subclasses registering against the same model." That is false at HEAD by the same fact as drift row D2: `registry.py::TypeRegistry.register` appends, and raises only for a duplicate primary claim or a flipped primary flag. It is a **documentation** defect, not a correctness one — no behavior is wrong and no test is wrong — so it is not a source edit inside a documentation cycle and I did not make one. The build plan's `## Build-wide context flags` says R3 "may edit a docstring only if its audit finds a factually-false one, and that routes through Worker 2". This is that case. Route it to R3 or to the maintainer.
2. **ESCALATED — the same docstring uses the spec vocabulary the runtime message deliberately moved away from.** The next example reads "A deferred-surface key (`aggregate_class`, `fields_class`, `search_fields`) declared before **the spec** that owns it has shipped", while `types/base.py::_validate_meta` raises "The **feature** that owns them has not shipped." The key list is correct; the word is the one D11 records as a deliberate consumer-facing correction. Same routing as item 1, and the same one-word fix. Lower severity than item 1 and in the same file, so they are one edit if either is taken.
3. **Plan defect, for Worker 0.** Drift row D12 cites `tests/types/test_base.py::test_relation_shapes_is_shipped_not_deferred`; no such test exists (`grep -rn relation_shapes_is_shipped tests/` → no match, exit 1). The real name is `::test_meta_relation_shapes_in_allowed_meta_keys`, whose docstring names `test_interfaces_is_shipped_not_deferred` as the mirror it follows — which is very likely how the name was constructed. D12's substance is unaffected; the spec cites the correct name.
4. **Two drift rows the plan's table missed, now recorded as D21 and D22** in `### Drift-row disposition`. Both are inside `### One-model-one-type`'s opening and decision: an undischarged `docs/README.md` documentation obligation (the same obligation D6 catches the *override* half of) and a citation of `convert_relation`, a symbol that no longer exists anywhere in the package. The plan says outright that its table is "Worker 0's verified floor, and R2 owns the full sweep"; this is that sweep returning two.
5. **Extended hand-off 9 was obeyed and needs no further action.** The rationale's condensation of the override diagnosis and its verbatim quotation of "must update this contract spec accordingly" both stay exactly as R1 wrote them, now that R2 has corrected the spec's copies of each. Both are attributed in the rationale as claims the spec once made, which is what `BUILD.md` `## Spec rationale extraction` requires the file to carry. Re-verified after the rewrite: neither was touched, and the quoted clause no longer appears in the spec at all, so the record is now the only copy — exactly as intended.
6. **The rationale's `## Provenance of this record` is now partly a statement about what R1 left, not about what the spec says.** Its "deliberately left in the spec" list names four passages, three of which R2 has since rewritten or removed. R1's hand-off 10 anticipated this and says it needs no edit; I agree, and `## How to read this file`'s new two-layer bullet tells a reader how to take it. Flagged so a later pass does not read it as drift and "fix" it.
7. **No contract-level question was escalated to the maintainer, and one was checked before deciding not to.** D18 looked contract-level and is not: the build plan's own D18 row assigns the call to Worker 1. The one genuinely pre-decided question — the spec-004 cycle's maintainer decision on competitive positioning in a `## Problem statement` — was **not** re-fought: the three-library sentence was removed because the gap it names is closed, which is `worker-1.md` rule 2 (delete prose the current decisions have falsified), not a re-reading of that decision's scope clause. The reasoning is recorded in the rationale's `## Problem statement` entry under its own sub-heading so a reviewer can charge it directly if it disagrees.
8. **Baseline: no growth during this pass, and the plan's list is now smaller than recorded.** The concurrent commit at `ff03c137` landed the whole `### First growth` set before this pass began, so `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`, `BACKLOG.md`, the sibling specs, and both `spec-063` files are **clean**. What remains dirty is the five spec-004-cycle entries and the four staged-deleted `bld-003-*.md` files, which still await the maintainer. Nothing was reverted or `git checkout`-ed (`AGENTS.md` rule 34). R3 should re-derive `HEAD` rather than quoting `ff03c137` from here.
9. **For R3's durable-doc audit.** Two facts this pass established that R3's scope will want: `docs/README.md` has no `## Current surface` section and no reference to spec-005 anywhere (D6, D21), and `docs/GLOSSARY.md`'s `Meta.interfaces` (`shipped (0.0.5)`) and `Meta.primary` (`shipped (0.0.6)`) entries are already correct and already carry the full ambiguity table — which is why the spec now points at the glossary rather than restating it. R3 verifies rather than edits.

### Review outcome

Not applicable — this is the Worker 1 reconciliation pass. `Status: planned` on return, which Worker 0 reads as "dispatch Worker 3" per Deviation 2.

### Spec changes made (Worker 1 only)

Line numbers are against the **post-R2** spec (122 lines / 13,025 bytes) unless the change is a removal, in which case the post-R1 line range is given.

| Spec lines | Change | Reason | Trigger |
|---|---|---|---|
| spec:3 | Companion-pointer paragraph rewritten to cover R2's additions and to drop the phrase the rationale's own charter uses | rule 1 requires a pointer; the shared phrasing was a measured duplication | rule 1 + `### Eight duplications caught by measurement` |
| spec:5-14 | `## Problem statement` rewritten from four dated gaps to four durable failure classes; the three-library competitor sentence removed; `djangotype` / `metafields` / `metaexclude` anchors kept inside it | three of the four items stated present-tense facts HEAD falsifies, and the competitor gap they named is closed | D2, D5, D13; `worker-1.md` rule 2 |
| (post-R1 spec:16-31) | `## Current state` **removed whole**; the `metaprimary` anchor re-sited into spec:34 in the same edit; the sentinel's durable half restated at spec:81 | a release-status section cannot exist in a document that must state what holds today | D1, D13, D14; hand-off 1 |
| spec:20 | `## Goal` bullet 1: "rejected with a clear error pointing at the spec that will own it" → "rejected with a clear error naming what it refused" | the shipped rejection names no spec, deliberately | D11, D20 |
| spec:21-22 | `## Goal` bullets 2-3 lightly restated (`README` → `docs/README.md`; the third bullet generalized) | precision, and the third bullet is what survives D21's undischarged obligation | D21 |
| spec:26 | `## Non-goals`: both "future"s removed; the three owning spec paths named | both mechanisms shipped at `0.0.6` | D17; hand-off 5 |
| spec:30 | `### One-model-one-type (alpha constraint)` retitled `### One model, many types, one primary` | the constraint the title names does not exist | D2 |
| spec:32-38 | Section rewritten: the registry's actual shape, the import-order requirement as this spec's own contract, `Meta.primary` named with its owner, both ambiguity rejections stated without restating spec-018's catalog, `**Decision for 0.0.3.**` → `**Contract.**`, the `docs/README.md` obligation dropped, `convert_relation` dropped | D2/D3 falsify the section; D21/D22 falsify its decision and its opening | D2, D3, D21, D22; hand-off 8 |
| spec:40 | `### Consumer override semantics (deferred to a future spec)` retitled `### Consumer override semantics` | the mechanism it deferred has shipped | D5, D8 |
| spec:42-48 | Section rewritten: the four-corner contract stated, the merge's role corrected from "harmless" to "part of the shipped path but not the deciding gate", the two owning specs named, the skipped-test promise generalized into a rule, `**Decision for 0.0.3.**` → `**Contract.**` | D5's diagnosis, D6's README promise and D7's test are all falsified; the merge-can-stay instruction had to survive with a correct reason | D5, D6, D7, D8; hand-off 8 |
| spec:50 | `### Invalid \`Meta.fields\` / \`Meta.exclude\` (shipped in 0.0.3)` retitled `### Invalid \`Meta.fields\` and \`Meta.exclude\` names` | version stamp is chronology; the slash slugs ambiguously under two different sluggers | D16 |
| spec:52 | `ConfigurationError` in the body linked to its glossary anchor | the anchor's old carrier (`## Problem statement` item 1) was rewritten; this is where the term belongs | D2, hand-off 2 |
| spec:56 | New paragraph: the error shape is owned by `_format_unknown_fields_error` and inherited by five further keys | the section claimed the contract for two keys; the package honours it for six | D16 |
| spec:58 | `### Accepted vs deferred Meta keys (shipped in 0.0.3)` — version stamp dropped, **title string preserved** | chronology; and `spec-006:108` cites the string | D9/D10; hand-off 7 |
| spec:60-64 | Both key rosters **removed**, not refreshed; the buckets described by what licenses membership; the deferred message corrected to name a feature, never a spec | a roster is a copy of an executable set and has gone stale eleven times | D9, D10, D11; the plan's anti-inventory trap |
| spec:73 | New paragraph: the third route into `ALLOWED_META_KEYS` (accepted without ever having been deferred) | the two-bucket partition cannot express it, and six of the twelve added keys arrived that way | D12 |
| spec:75 | The `Meta.interfaces` example inverted from a past mistake to a current-state fact plus both real pinning-test names; `metainterfaces` anchor re-sited here | `interfaces` is accepted and applied today; the plan's second test name does not exist | D13, D12; hand-off 2 |
| spec:81 | `## Coordination …` paragraph 2 rewritten: the sentinel's stamping-order invariant, MRO-walk detection, definition-object authority, and the finalizer's shared-`FilterSet` use | D14 is an under-description, and my first draft mis-described the second consumer | D14 |
| spec:83 | The "a future spec must update this contract spec" instruction **retired**, replaced by an obligation on the code | never once followed across eleven-plus specs; unenforceable by construction | D18; hand-off 6 |
| spec:87-92 | `## References`: the unresolvable alpha-review bullet removed, the test bullet corrected, four owning specs added, the `spec-006` by-title dependency recorded | D19; and the by-title dependency is invisible from the citing side | D19; hand-off 7 |

**Rationale file (appended, `worker-1.md` rule 4).** Ten new entries under `## Entries keyed to the spec — the R2 reconciliation`, one per spec section changed, each keyed by heading and a resolving anchor and each carrying what changed, why, the rejected alternatives with the reason each lost, and the claims the section may no longer make; two new `## How to read this file` bullets; six new link definitions plus one corrected slug. Two prior entries were **re-keyed** — link-definition target plus a one-sentence parenthetical naming the old title — because R2 retitled the sections they name; no recorded content was rewritten or removed. The reasoning is under `### Implementation notes`.

**No checklist box is deferred**, so no deferral reason is owed under `docs/builder/ARTIFACT.md`. Two items are escalated rather than deferred (`### Notes for Worker 1 (spec reconciliation)` items 1 and 2): both are documentation defects in shipped source, which a documentation cycle records and routes rather than edits.

---

## Review (Worker 3)

`HEAD` re-derived, not quoted: `ff03c1372365edcad488ff4671389d88ae145276` — unchanged since R2 closed. `git log --oneline -- docs/SPECS/spec-005-django_type_contract-0_0_3.md` still tops out at `ff65666d` ("docs: normalize review citations to their durable records"), which predates the cycle, and `git log` over the rationale and both `bld-005-*` artifacts is empty, so nothing this cycle wrote was swept into a concurrent commit. `git status` alone was not used for that determination. Baseline dirty is exactly the five spec-004-cycle entries plus the four staged-deleted `bld-003-*.md` files, plus this cycle's own three — no growth this pass, nothing reverted.

Read-only HEAD copy of the pre-cycle spec taken with `git show HEAD:… > <scratchpad outside the repo>`. No `git stash` / `checkout` / `restore` / `worktree`, no branch, no commit, no source or test edit, no `pytest`, no coverage-shaped flag.

### High:

None.

### Medium:

#### M1 — `## Problem statement` failure class 1 names the direction that structurally cannot fail

`docs/SPECS/spec-005-django_type_contract-0_0_3.md:9`

```docs/SPECS/spec-005-django_type_contract-0_0_3.md:9
1. **Ambiguous reverse lookup.** Relation targets and the type-to-model reverse lookup are
   answered from the registry. If a model is reachable through more than one type and nothing
   declares which one answers, the answer falls to import order …
```

The failure class is real, but it is hung on the wrong lookup. `registry.py::TypeRegistry.model_for_type` is the type-to-model direction, it is backed by `_models`, and it is one-to-one by construction — a model with fifteen types still resolves each of them to exactly one model. The spec says so itself eighteen lines later:

```docs/SPECS/spec-005-django_type_contract-0_0_3.md:32
… the other direction stays one-to-one, so `model_for_type` resolves every registered type back
to exactly one model …
```

The direction that can be ambiguous is model-to-type (`registry.py::TypeRegistry.get`, `::primary_for`), and `spec:34` names it correctly ("Reverse lookup in the model-to-type direction needs exactly one answer per model"). So within one rewritten document "reverse lookup" denotes both directions, and the class heading plus `spec:9`'s naming point the reader at the one that cannot exhibit the failure. `spec:9` is also the sentence the whole `### One model, many types, one primary` contract cites as its motivation, so the imprecision is load-bearing rather than cosmetic.

Recommended change: name the direction the failure lives in — relation-target resolution and `registry.get(model)`, i.e. model-to-type — and either drop `model_for_type` from the sentence or state it as the direction that is *not* at risk. No behavior claim needs to change; one clause does. This is a Worker 1 edit under Deviation 2.

#### M2 — the rationale's net-new-key count is wrong: nine, not six

`docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md:497` and `:502`

```docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md:497
*Added: the third route in, which the two-bucket partition could not express.* Six of the twelve
keys added since never sat in the deferred set at all …
… otherwise the promotion rule reads as the only entrance, and six of the seventeen accepted keys
then look like they skipped it.
```

Measured rather than read. `ALLOWED_META_KEYS` holds 17 keys at HEAD; the original five were `model` / `fields` / `exclude` / `name` / `description`, so twelve were added. Three of those twelve are promotions (`interfaces`, `filterset_class`, `orderset_class`). The other **nine** are `connection`, `cursor_field`, `filesystem_path_fields`, `globalid_strategy`, `nullable_overrides`, `optimizer_hints`, `primary`, `relation_shapes`, `required_overrides` — and none of them ever sat in `DEFERRED_META_KEYS`: replaying every commit that touched that definition (`git log --format=%h -S'DEFERRED_META_KEYS' -- django_strawberry_framework/types/base.py`, then `git show <c>:…` on each) shows the set only ever held `filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, and `interfaces`.

The "six" is a count of **clauses in the source comment** beside `ALLOWED_META_KEYS`, not of keys. That comment is a recent-provenance note: it folds `nullable_overrides` / `required_overrides` into one clause (so its seven keys read as six clauses) and it omits `primary` and `optimizer_hints` entirely, because neither belongs to the spec-029-onward run it was written to annotate. Reading it as a census is exactly the "a long phrase samples a claim's vocabulary rather than establishing its population" failure `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` names, and the number was inherited from the plan's D12 row rather than re-derived — which the re-verification pass claims it was.

The spec is unharmed: `spec:73` deliberately states no count. Only the rationale asserts one, twice.

Recommended change: nine and nine, or drop the numeral and say "most of the keys added since". Whichever is chosen, the sentence must not be re-derived from the source comment.

#### M3 — the rationale's `## Current state` bullet count is wrong, and one of the three items it names is not a bullet

`docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md:316`

```docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md:316
… and three of its five bullets are now false as present tense — `Meta.interfaces` is accepted
again and applied, the override merge is part of a shipped mechanism rather than a known-broken
path, and `Meta.primary` is not future work.
```

At HEAD (`git show HEAD:docs/SPECS/spec-005-django_type_contract-0_0_3.md`, `## Current state`) the section carried **seven** bullets: four under `0.0.2 shipped:` and three under `0.0.3 shipped (in flight):`. Of those seven, **five** are false as present tense — collision-raises, the known-broken merge, `Meta.interfaces` silently ignored, `Meta.fields` / `Meta.exclude` typos silently dropped, and `Meta.interfaces` moved to `DEFERRED_META_KEYS`; the `_select_fields` and sentinel bullets are the two that survive, and both were restated into the spec. The third falsehood the sentence names (`Meta.primary` is not future work) is not a bullet at all — it comes from the section's closing paragraph.

This one matters more than an arithmetic slip because the removal of `## Current state` is the pass's largest single call, and the rationale is the only surviving record of what the section contained. A reader auditing "did anything true get lost?" is handed the wrong denominator.

Recommended change: seven bullets, five false as present tense, and either move `Meta.primary` to the closing-paragraph clause or name it separately. The removal itself is correct and I am not challenging it — the accounting of it is what is off.

### Low:

#### L1 — `spec:42`'s lead clause is unconditional and the package ships a documented exception

```docs/SPECS/spec-005-django_type_contract-0_0_3.md:42
A field a consumer authors on the class body is authoritative: the generator does not synthesize
over it. This holds across the whole four-corner surface — …
```

`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` #"the \"declare-but-infer\" marker (the fifth corner of the" routes an annotation-only `field: auto` **back into synthesis** — the name is excluded from the consumer-authored union and dropped from `consumer_annotations` so the synthesized annotation wins the final merge. `examples/fakeshop/apps/scalars/schema.py` #"The fifth corner is the inverse of the four overrides" says the same thing from the consumer side. A consumer who writes `name: auto` has authored something on the class body and the generator does synthesize over it.

The second sentence scopes the claim to the four-corner surface and `auto` is by repo vocabulary the fifth corner, so a careful reader lands correctly — which is why this is Low and not Medium. But the spec's own failure class 2 is "a promise the implementation does not keep", and the unconditional lead clause is one. A subordinate clause ("other than the `auto` declare-but-infer marker, which asks for synthesis") closes it without adding a rule spec-019 owns.

#### L2 — `## Goal` bullet 3 keeps the spec-naming obligation bullet 1 was corrected to drop

```docs/SPECS/spec-005-django_type_contract-0_0_3.md:22
- A constraint the package intends to lift is labeled as temporary and names the spec that will lift it.
```

Bullet 1 was corrected this pass precisely because the package deliberately does not name spec documents in consumer-facing text (D11 / D20; `types/base.py::_validate_meta` raises "The feature that owns them has not shipped"). Bullet 3 still requires a spec be named. The nearest live instance is the deferred-key surface, and `docs/GLOSSARY.md`'s `Meta.aggregate_class` / `fields_class` / `search_fields` entries label it by **version** (`**Status:** planned for 0.1.3.`), not by spec. There is no constraint at HEAD that the bullet is satisfied by, so nothing is violated today — but the rationale's `### One model, many types, one primary` entry routes D21's durable half into this bullet without checking it, and the `## Goal` entry discusses only bullet 1. Worth one sentence in the rationale, or aligning the bullet with where the labeling actually lives.

#### L3 — an R1-layer sentence is now flatly false in the present tense, and it is the same class the pass flagged in the singular

```docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md:95
`## Problem statement` item 1 names the same three libraries and is untouched — it is the only
sentence saying why the constraint was flagged at all.
```

Item 1 no longer names them; this pass removed the sentence, correctly. `### Notes for Worker 1` item 6 flags exactly this shape at `## Provenance of this record` and argues (persuasively) that a layer-1 record does not need editing because `## How to read this file` tells the reader layer 1 is R1's state. The same defence covers this sentence — but the pass named one instance and not the other, and this one is load-bearing: it is the stated justification for moving the competitive argument while leaving the problem-statement sentence, which the pass then removed. Either both are flagged or neither is. My own carry-forward from R1's re-review is that hand-off lists name same-class instances in the singular, so this is the predicted miss rather than a new one.

#### L4 — internal arithmetic in the `### Invalid …` rationale entry

```docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md:459
*What was added …* Five more `Meta` keys have since adopted the shared formatter behind this
message. The section claimed the error shape as public contract for two keys; the package honours
that claim for six.
```

Two plus five is seven. Both numbers are defensible in isolation — five further **keys** (`optimizer_hints`, `nullable_overrides`, `required_overrides`, `filesystem_path_fields`, `relation_shapes`) and six distinct **`attr` labels** at the raise sites (`fields`, `exclude`, `optimizer_hints`, `nullable_overrides/required_overrides`, `filesystem_path_fields`, `relation_shapes`) — but they are mixed inside one sentence pair and read as a contradiction. The spec itself (`spec:56`) states no count and enumerates the keys instead, which is the right shape; the rationale should either match it or say which unit it is counting.

#### L5 — a third source-doc defect found in passing, RECORDED not fixed

`django_strawberry_framework/types/base.py::_format_unknown_fields_error`

```django_strawberry_framework/types/base.py:885
    Used by every validator that points at a typo in ``Meta.fields``,
    ``Meta.exclude``, or ``Meta.optimizer_hints``.  Centralizing the
    format keeps the consumer-visible error shape consistent across
    typo-guard sites.
```

Stale: the helper is now also reached for `nullable_overrides` / `required_overrides` (`attr="nullable_overrides/required_overrides"`), `filesystem_path_fields`, and `relation_shapes`, all via `_selected_meta_targets`. The docstring's "every validator that points at a typo in [three keys]" therefore under-states its own reach by three `attr` families — and it is the exact claim `spec:56` now widens on the spec side, so the source doc and the spec disagree in the one place this pass deliberately touched.

**No edit was made.** Same class and same disposition as the two `django_strawberry_framework/exceptions.py::ConfigurationError` items R2 escalated: a documentation defect in shipped source, not a correctness defect, so it is recorded and routed. It is a different file from the one `### THE ONE SOURCE EDIT THIS CYCLE AUTHORIZES` scopes, so it is **not** in R3's authorized edit — Worker 0 decides whether to widen that authorization or hand it to the maintainer. Widening is not a worker's call.

#### L6 — one `### Dispatched findings checklist` box over-ticks

`docs/builder/bld-005-r2-spec_reconciliation.md:57` — "[x] Each rationale entry carries the rejected alternatives with the one-line reason each lost."

Eight of the ten R2-layer entries do. Two do not: `## Non-goals` (which records only the correction and the claim it no longer makes) and `## References` (whose "Nothing is lost by removing it" is a justification, not a weighed-and-rejected alternative). The underlying content is defensible — neither change had a real alternative — so the fix is the tick or one clause per entry saying no alternative was weighed, not manufactured alternatives. `docs/builder/BUILD.md` `### Dispatched findings checklist` fixes a tick with no matching implementation at Medium; I hold it at Low because the box is a self-audit of a Worker-1-performed pass rather than a dispatched finding, and because the shortfall is completeness of a record, not an unbuilt contract.

### DRY findings

None to charge, and the spec-versus-rationale split was re-derived rather than accepted.

- **Shingle intersection re-derived over both file bodies** (text before `<!-- LINK DEFINITIONS -->`), three tokenizers, `n` = 8 / 7 / 6:

  | tokenizer | n=8 | n=7 | n=6 |
  |---|---|---|---|
  | punctuation kept | **0** | 1 | 3 |
  | punctuation stripped, `.` `#` `_` retained | **0** | 2 | 7 |
  | alphanumeric only | 7 | 12 | 23 |

  R2's reported figure — **0 at n=8 under both of its named tokenizers** — reproduces exactly. The n=6 survivors under the first two are the three section headings the keying rule requires the rationale to reproduce plus "the rejection of first-registered-wins", which is the pair R2 named and correctly argued is unremovable.

  The third tokenizer is mine and is the adversarial one: shredding `.` `/` `-` `_` turns every path and version into a word run, and all seven of its n=8 hits are identifier runs — `tests types test base py test interfaces is shipped not deferred`, `spec 005 django type contract 0 0 3`, `spec 018 meta primary 0 0 6 md`. Both files legitimately cite the same test and the same spec paths; citing an identifier twice is not restating prose. Recorded so a later pass does not "discover" these and read them as duplication. The one substantive-looking n=6 hit, `be part of the api contract`, is the rationale's *Moved* verbatim quotation of the prediction block, which is the record itself.
- **Against the owning siblings.** No rule of `spec-010` / `spec-011` / `spec-015` / `spec-018` / `spec-019` / `spec-027` / `spec-028` is restated in either file. `spec:36` states two rejections, but as boundary requirements on the answer rather than as spec-018's catalog: the four-case table with its error strings stays in `docs/GLOSSARY.md`'s `Meta.primary` entry, which I read and confirmed carries all four cases plus both message strings. The over-absorption trap is refused. One accuracy note, not a finding: the checklist box at `:60` says the six owning specs "are named as owners" — in the **rationale** all seven are; the **spec** names only `spec-010`, `spec-018`, and `spec-019`. That is correct behaviour (the other rosters were removed, so there is nothing left for `spec-011` / `015` / `027` / `028` to own in the spec), but the box reads as a claim about the spec.
- **Existence challenge.** Raised and answered without a finding: the candidate abstraction this pass creates is the rationale's second layer. It earns its existence — the R1 layer is a record of a move and the R2 layer is a record of a reconciliation, they key to the same headings from different passes, and collapsing them would require editing R1's record, which `worker-1.md` rule 4 forbids. The `## How to read this file` two-layer bullet is what makes the split legible. No consolidation recommended.
- **Anti-inventory trap refused, verified.** Neither roster appears in the spec; `types/base.py::ALLOWED_META_KEYS` and `types/base.py::DEFERRED_META_KEYS` are named as the authoritative sets and `docs/GLOSSARY.md` as the published per-key status. `::CONSTANT` is established repo form for these two (`docs/SPECS/spec-001-django_types-0_0_1.md`, `spec-028`, `spec-030` all use it), so it is not a rule-27 deviation.

### Source verification — every normative sentence the spec now makes

Read against `django_strawberry_framework/` at HEAD, not against the plan's table. Every claim below **holds**.

- `spec:32` — `registry.py::TypeRegistry.register` appends (`existing_types.append(type_cls)`); `_models` is one-to-one and `register` raises a reverse-collision if the same class is offered a second model.
- `spec:34` / `spec:36` — duplicate primary raises at `register` (#"is already the primary type"); flipped flag on re-register raises (#"primary flag cannot be flipped on re-register"); ambiguity-by-omission raises at `types/finalizer.py::_audit_primary_ambiguity`, which is called from `finalize_django_types` and reads `registry.primary_for(model) is None` over `models_with_multiple_types`; the audit sorts offenders by `model.__name__` **so the error body is deterministic regardless of import order**, which is the source-side confirmation of "no path … breaks a tie by declaration order". Relation targets bind at finalization through `registry.primary_for(target_model)` (`types/finalizer.py` #"registry.primary_for(target_model)`` keyed on the TARGET model"). A single type with no `Meta.primary` still resolves through `TypeRegistry.get`'s `len(candidates) == 1` arm.
- `spec:52` / `spec:54` — `types/base.py::_select_fields` raises in **both** arms (`attr="fields"` and `attr="exclude"`), and `_format_unknown_fields_error` returns `"{model}.Meta.{attr} names unknown fields: [...]. Available: [...]."`, i.e. model + unknowns + available exactly as claimed. All three named tests exist: `tests/types/test_base.py::test_meta_fields_unknown_name_raises` (:1017), `::test_meta_fields_unknown_name_includes_model_and_available` (:1027), `::test_meta_exclude_unknown_name_raises` (:1043).
- `spec:56` — the five further keys all reach the shared formatter. Measured by `attr=` at the raise sites: `optimizer_hints` (two sites), `nullable_overrides/required_overrides`, `filesystem_path_fields`, `relation_shapes` — the last three through `_selected_meta_targets`, which calls `_format_unknown_fields_error` itself.
- `spec:62-64` — `ALLOWED_META_KEYS` holds 17, `DEFERRED_META_KEYS` holds exactly `aggregate_class` / `fields_class` / `search_fields`, `_validate_meta` raises `"Meta keys not supported yet: [...]. The feature that owns them has not shipped."` (names the keys, names a **feature**, names no spec) and `"Unknown Meta keys: [...]"` for the typo guard. The deferred check runs **before** the unknown check and before every shape gate, as the spec's ordering implies.
- `spec:73` — the third route is real; the source comment beside `ALLOWED_META_KEYS` records it. (Its population is M2.)
- `spec:75` — `interfaces` is in `ALLOWED_META_KEYS`, validated by `types/base.py::_validate_interfaces` from `_validate_meta`, and injected into `__bases__` by `types/relay.py::apply_interfaces` at `types/finalizer.py` Phase 2.5. `tests/types/test_base.py::test_interfaces_is_shipped_not_deferred` (:542) exists, and so does the corrected second name `::test_meta_relation_shapes_in_allowed_meta_keys` (:363) — R2's correction of the plan's D12 citation is right, and the name the plan gave returns nothing.
- `spec:81` — the sentinel is stamped at `types/base.py::DjangoType.__init_subclass__` #"cls._is_default_get_queryset = not has_custom_get_queryset", three lines **before** `meta = cls.__dict__.get("Meta")` / `if meta is None: return`; `_detect_custom_get_queryset` walks `cls.__mro__` and returns `False` on reaching `DjangoType`; `has_custom_get_queryset()` returns `definition.has_custom_get_queryset` when the definition exists and the negated classvar otherwise, i.e. the definition is authoritative and the classvar is the pre-definition fallback. The finalizer's second use is `types/finalizer.py::_check_filterset_owner_get_queryset_safety`, whose own docstring calls `definition.has_custom_get_queryset` "exactly the 'carries any override' predicate" and fails closed on either owner — R2's late correction of its own first draft (owner check, not definition merge) is right.
- `spec:26` / `spec:87-92` — every cited path exists on disk: `spec-001`, `spec-002`, `spec-006`, `spec-010`, `spec-018`, `spec-019`.

### Nothing true was lost — re-derived at line granularity off `git diff -U0`

Not read off R2's account. `git diff -U0 -- <spec>` yields **65** removed non-empty lines, matching the report. Two (`## Problem statement`, `## Coordination with …`) are hunk-boundary artifacts and are present verbatim in the new file — confirmed by whitespace-normalized substring match, not by eye. Of the remaining 63, **18 are R1's** (the friction paragraph, both `**Future direction.**` blocks with their bullets / sub-questions / first-registered-wins rejection, and `## Open questions`) and were proved 18/18 accounted at R1; the arithmetic 65 − 2 − 18 = **45** reproduces R2's figure exactly.

Each of the 45 was then classified against both durable files with a squashed-character containment test (which sees a line restated with a link wrapper or a list marker added, where a whole-line match does not), and every survivor walked by hand. Result: **45/45 accounted**, no true normative claim lost.

The two that most deserved the walk, since a status section is where a durable claim hides:

- `_select_fields` raises naming model + unknown names + available field set → restated at `spec:52`, and **widened** at `spec:56`.
- the `_is_default_get_queryset` / `has_custom_get_queryset` bullet → restated and corrected at `spec:81`, where the optimizer half already lived. It is the only durable claim `## Current state` carried, as the report says.

Two further removals I checked specifically because they are the shape a rewrite drops silently: `### Accepted vs deferred Meta keys`' trailing "This rule should be checked at every spec slice that introduces or moves a Meta key" survives, promoted into `spec:83`; and `## Coordination …`'s "keeps the optimizer's `model_for_type` reverse-lookup unambiguous" survives at `spec:32`. Both are restatements, not losses.

### The 7-anchor constraint — independently re-measured

`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-005-django_type_contract-0_0_3.md` →

```text
OK: 7 terms - all have glossary entries and at least one spec link.
```

exit **0**, character-identical to the pre-flight baseline and to R2's quotation.

Carriers re-derived myself as reference-style body uses only (`][glossary-<anchor>]` before `<!-- LINK DEFINITIONS -->`; a plain code span is not a carrier), which is the correction R1 established:

| anchor | body uses | definitions | carrier line |
|---|---|---|---|
| `djangotype` | 1 | 1 | `spec:7` |
| `metafields` | 1 | 1 | `spec:11` |
| `metaexclude` | 1 | 1 | `spec:11` |
| `metaprimary` | 1 | 1 | `spec:34` |
| `configurationerror` | 1 | 1 | `spec:52` |
| `metamodel` | 1 | 1 | `spec:52` |
| `metainterfaces` | 1 | 1 | `spec:75` |

**All seven at exactly 1 use + 1 definition**, and the carrier lines match R2's table row for row. Total definitions 8 / distinct uses 8, 0 undefined, 0 unused.

Every carrier sits in prose I verified true above, so R2's stronger claim — that after this pass **no anchor sits in falsified prose, because none survives** — holds by inspection of the seven sites, not by inference from the section deletions.

On hand-off 1's "same write" claim: single-write atomicity is not observable from outside the pass, so I verify the end state instead, which is what the constraint actually protects. `metaprimary`'s old carrier (`## Current state`'s final paragraph) is gone and its new carrier at `spec:34` is contract prose; the checker passes; `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-terms.csv` is byte-clean at HEAD and still carries the same seven anchors, one row each; and `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` exit 0, so the card-wrap chain the constraint exists to protect is intact. Accepted on end state.

### Rationale keying — all ten R2 entries

Every entry names its spec section by heading and carries a link. All **9** distinct in-page anchors the rationale targets resolve against a real post-R2 spec heading, checked by slugging the spec's 11 headings with `scripts/check_spec_glossary.py::github_anchor` and matching the fragments — including the two re-keyed after the retitles (`#one-model-many-types-one-primary`, `#invalid-metafields-and-metaexclude-names`) and the two entries whose sections no longer exist (`## Open questions` and `## Current state`, each anchored to the surviving section that absorbed it, which is the shape `docs/builder/BUILD.md` `## Spec rationale extraction` asks for).

Per-entry obligations:

- **Claims the section may no longer make** — present in all ten (`## References`' and `### Invalid …`' are the two that legitimately record "none" or a gain rather than a retraction, and both say so explicitly).
- **The change and what caused it** — present in all ten; the owning spec or the shipped mechanism is named in each case where one exists, and `## Goal`'s "a later consolidation pass" is the honest answer where the cause is a doc-consolidation commit rather than a spec.
- **Rejected alternatives with why each lost** — present in eight. The two exceptions are L6.

The re-key mechanism itself (link-definition target updated plus a one-sentence parenthetical naming the old title, no recorded content rewritten) is the right call and I would have charged the alternative: `worker-1.md` rule 3's "every in-page anchor still resolves" and rule 4's append-only are in direct conflict after a retitle, and a dangling anchor is the larger defect. R2 recorded it under `### Implementation notes` and invited the charge; I decline it.

### The competitive-positioning removal — the reasoning charged directly

`## Problem statement` item 1's DRF / `graphene-django` / `strawberry-graphql-django` sentence was removed, and the pass recorded its ground under its own sub-heading in the rationale so it could be attacked. Attacked, and it holds.

The maintainer decision from the spec-004 cycle preserves a **problem statement's statement of the competitor gap** where the comparison is the document's subject. What the removed sentence asserted was a *gap*: those three libraries allow several types per model, and (by the surrounding item) this package does not. `registry.py::TypeRegistry.register` appends, so the package allows it too. There is no gap left for the decision to preserve, and a sentence that states a closed gap is not positioning, it is a false claim — `worker-1.md` rule 2 territory. The competitive argument itself is not lost: R1 moved the friction paragraph, which names the same three libraries, into the rationale.

This is an application of the maintainer decision to a changed fact, not a re-reading of its scope clause. Nothing here re-fights it.

### The inbound title citation

`docs/SPECS/spec-006-public_surface-0_0_3.md:108` reads:

```docs/SPECS/spec-006-public_surface-0_0_3.md:108
- `deferred` — … (or accepted-and-rejected per `spec-005-django_type_contract-0_0_3.md`
  "Accepted vs deferred Meta keys"). Not importable.
```

The quoted substring is `Accepted vs deferred Meta keys`. The post-R2 heading is `### Accepted vs deferred Meta keys` — the string is intact and the parenthetical `(shipped in 0.0.3)` that was dropped sits outside it. **No inbound break.** `spec-006` was read only; it is untouched in `git status`, as are `:135` and `:146`.

### Format and link integrity

- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-005-django_type_contract-0_0_3.md docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md docs/builder/bld-005-r2-spec_reconciliation.md` → exit **0** on all three (this artifact included, after my append).
- **Every link definition disk-exists-checked myself**, resolved from each file's own directory: spec **8/8** resolve (`../GLOSSARY.md` → `docs/GLOSSARY.md`, `appx/…-rationale.md`), rationale **19/19** resolve (`../spec-NNN-….md` → `docs/SPECS/`, `../../builder/BUILD.md` → `docs/builder/`). 0 undefined and 0 unused in both. The two-level relativity the rationale needs is correct in every definition, and no target was lost to the concurrent renumbering — all seven cited sibling specs (`010`, `011`, `015`, `018`, `019`, `027`, `028`) and `spec-001-django_types-0_0_1-rationale.md` are present at the paths given.
- `grep -nE '[a-zA-Z_/]+\.(py|md|csv|txt|json):[0-9]+'` over both durable files → no match. `AGENTS.md` rule 27 holds; raw `path:NN` appears only in this artifact, where it is legal.
- `grep -nP '\]\((?!#|https?:)'` over both → no match. Reference-style only, `<!-- LINK DEFINITIONS -->` present with all 10 canonical group headers in order in both.
- Byte counts confirmed independently: spec **154 lines / 13,346 B** at HEAD → **122 / 13,025** now; rationale **640 / 44,958**; `git diff --stat` = `45 insertions(+), 77 deletions(-)`. Every figure in the report's byte table reproduces.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are unchanged. No spec authorization needed.

### CHANGELOG sanity

Not applicable; item did not modify `CHANGELOG.md`. `git status --short -- CHANGELOG.md` is empty, consistent with `AGENTS.md` rule 21 and the plan's build-wide flag.

### Documentation / release sanity

This item touches an archived spec and its companion, so the check applies.

- No version string, shipped/planned status, or card ID moved: the spec now carries **no** version stamp at all (both `(shipped in 0.0.3)` suffixes and the `(alpha constraint)` / `(deferred to a future spec)` qualifiers are gone), which is the point of the pass. `pyproject.toml` and `docs/GLOSSARY.md`'s package-version line are untouched.
- No KANBAN card moved; `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, and `examples/fakeshop/db.sqlite3` are all **clean** in `git status`, confirming the concurrent `ff03c137` commit swept the plan's `### First growth` set and that this pass wrote none of them.
- Every markdown link introduced or moved by the item points at an existing file (checked above, all 27 definitions).
- The archive is not performed by this item and was not disturbed: `SpecDoc.path`, the terms CSV, and the KANBAN references are unchanged, and `import_spec_terms --check` passes.
- No obsolete "coming soon" / "planned" / old-version wording remains in either changed file. `grep -Ei 'as of|previously|in flight|shipped in|amend|retract'` over the spec returns only the companion-pointer paragraph at `spec:3`, which is required by `worker-1.md` rule 1 and matches the established shape of the sibling reconciled spec `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md:3`. Not a finding.
- No script-rendered doc was regenerated by this item, so the staging-docstring check does not apply.

**On "does the spec narrate its own history":** swept and it does not. There is no amendment block, no retraction paragraph, no "as of `0.0.N`" hedge, no release-status framing, and no section a reader must date before using. The two clauses that touch time are `spec:3` (the required companion pointer, precedent above) and `spec:75`'s "it has occupied two of the three buckets" — the latter is history of the **key**, offered as the reason it is the canonical example, not history of the document; nothing in the contract has to be reconstructed from it. `## Current state` and `## Open questions`, the two sections that were chronology by construction, are gone.

### Static helper use

`scripts/review_inspect.py` **skipped, deliberately, and the reason is recorded per `docs/builder/BUILD.md` `### When to run the helper during build`:** none of its four Worker-3 triggers fires. This item adds no `.py` file, touches no file under `optimizer/` or `types/`, and adds zero lines of logic anywhere — `git status --short -- django_strawberry_framework/ tests/ examples/` is empty. The diff is two Markdown files. Running it would have produced an overview of a file this item did not change.

### Failability proofs

**None owed and none re-run.** This item introduces no boundary, guard, gate, or rejection path — it edits two Markdown files and adds no code. `worker-3.md`'s mandatory re-run floor is satisfied by the empty set, which it explicitly permits when "the diff introduces no boundary that meets the floor". Boundaries re-run: none. Boundaries accepted on the builder's record: none — the build report correctly records `None; this pass introduced no new boundary.`

My source carve-out was therefore not exercised: no production file was mutated, transiently or otherwise, at any point in this review.

### Hot-path budget

Not applicable; the plan declares no hot path build-wide and this item changes no package source. Nothing is owed and nothing is missing.

### Floor verification

Not applicable; the plan declares floor-verification scope `none`, and this item touches no Django / Strawberry / channels integration seam and reasons about no version-dependent behavior. Correctly recorded as such.

### What looks solid

- **The removal of `## Current state` is the right call and is the pass's best work.** A status section in a contract document forces the reader to date it, and refreshing it would have bought a third reconciliation cycle. Its one durable claim did not merely survive — it was corrected on four points against source and now has one home instead of two.
- **The refusal to refresh the two rosters.** The lists have gone stale eleven times and three more moves are already carded on the Beta line. Naming `ALLOWED_META_KEYS` and `docs/GLOSSARY.md` as the sources and keeping the **rule** is the version of this section that does not need a fourth cycle. The rationale's "a copy of an executable set is the second source of truth that silently disagrees with the first" is the correct statement of why.
- **The retirement of the never-followed must-update instruction, and its replacement.** Zero-for-eleven is not carelessness, and the replacement obligation is checkable against source, which is the difference. The rejection of "keep it and add a check" is the strongest single paragraph in the rationale: the check could only verify that the document's copy matches the real set, which is the roster problem with tooling attached.
- **The self-caught error in the finalizer's second sentinel consumer.** The first draft called it a definition merge; it is a shared-`FilterSet` owner check that fails closed. Catching that by reading the call site in context, correcting the spec before writing the artifact, and then telling the reviewer where to attack it first is exactly the behaviour the artifact-as-contract model is for.
- **The eight measured duplications, especially the condensation.** A verbatim scan cannot see a condensation; only the shingle table found it. That the pass reports the tokenizer beside the number — the lesson R1's cycle paid twice for — is why my re-derivation could be a comparison rather than a fresh argument.
- **The escalation discipline.** Two documentation defects in shipped source found, neither edited, both routed with the rule that licenses the routing. A documentation cycle that finds a false docstring and fixes it "while it is here" is how a read-only audit becomes a source change; this one did not.

### Temp test verification

None created. `docs/builder/temp-tests/` is empty and stays empty: every claim under review is a property of two Markdown files or of source read at HEAD, and each was settled by direct measurement — `git diff -U0`, `git log -S` over the historical `DEFERRED_META_KEYS` definitions, the anchor and link-definition scans, and the checker runs quoted above. A temp test could not have said anything those did not. No promotion to the permanent suite is owed.

### Notes for Worker 1 (spec reconciliation)

1. **Routing.** Per the plan's Deviation 2 this `revision-needed` returns to **Worker 1**, not Worker 2. All three Mediums and L1-L4 and L6 are edits to the two durable files this cycle already owns; none needs source, tests, or a sibling spec.
2. **M2 and M3 are the same failure with two faces:** a count read off a nearby artifact (a source comment; a remembered section shape) instead of measured. Both are in the rationale, whose whole value is that a later reader can re-derive it. Worth re-checking the remaining numerals in both files in the same pass — I re-derived every one I quote above, and the rest (17 accepted, 3 deferred, 12 added, 3 promoted, 5 further keys, five call sites) all hold.
3. **M1 is a wording fix, not a re-decision.** The contract at `spec:34` / `spec:36` is right; only failure class 1's naming of the direction is wrong. Nothing about `### One model, many types, one primary` needs reopening.
4. **L5 is out of this cycle's authorized edit and I did not make it.** `django_strawberry_framework/types/base.py::_format_unknown_fields_error`'s docstring under-states its own reach by three `attr` families. `### THE ONE SOURCE EDIT THIS CYCLE AUTHORIZES` scopes R3's Worker 2 to one docstring in `django_strawberry_framework/exceptions.py`; this is a second file. **Worker 0 decides** whether to widen that authorization to a second file or hand L5 to the maintainer — widening a plan-declared scope is not a worker's call, and the same "does not widen it into a sweep of every docstring in the package" constraint should govern whatever is chosen.
5. **No contract-level finding was raised, and I checked before deciding not to.** Every finding above is a defect against an existing contract (a sentence that disagrees with source, a count that disagrees with measurement, a tick that disagrees with the record). None turns on which contract the package *should* offer. In particular the two calls the pass invited attack on — removing `## Current state`, and refusing to list the seventeen keys — I judged and endorsed rather than escalated; both are within the maintainer's already-recorded framing for this cycle, and re-opening either would be re-fighting a decided question.
6. **The spec-004 competitive-positioning decision was not re-fought.** I charged R2's stated ground directly, as the dispatch asked, and it holds on its own terms: the gap the sentence named is closed at HEAD, so the sentence is a false claim rather than a positioning statement, and `worker-1.md` rule 2 governs. Recorded so a later pass does not re-litigate this either.
7. **For R3's durable-doc audit**, two things this review established that its scope will want: `docs/GLOSSARY.md`'s `Meta.primary` entry carries the full four-case ambiguity table **with both error strings**, which is why the spec pointing there instead of restating it is safe; and the three still-deferred keys are labeled by **version** (`planned for 0.1.3` etc.), not by spec, which is the fact L2 turns on.
8. **Baseline unchanged this pass.** No growth, nothing reverted, no `git checkout`. The four staged-deleted `docs/builder/bld-003-*.md` entries still await the maintainer.

### Review outcome

`revision-needed` — three Medium findings (M1, M2, M3) and six Low (L1-L6), none of which carries a recorded rejection. Every one is an edit to `docs/SPECS/spec-005-django_type_contract-0_0_3.md` or its rationale companion except L5, which is escalated to Worker 0 for a scope decision and must not be edited by this cycle, and L6, which is a tick in this artifact.

The reconciliation itself is sound: the spec is true at HEAD on every normative sentence I traced to source but the one named in M1, it narrates no history, nothing true was lost across all 45 R2-removed lines, both named traps are refused, all seven glossary anchors stand at 1 use + 1 definition in verified-true prose, the inbound title citation resolves, and the spec-versus-rationale split measures 0 non-scaffold overlap at n=8 under both of the pass's tokenizers and under my re-derivation. The findings are corrections to a correct pass, not a rejection of its shape.

---

## Reconciliation report (Worker 1, pass 2)

Apply-changes pass for the nine findings above. `HEAD` re-derived rather than quoted: `ff03c1372365edcad488ff4671389d88ae145276`, unchanged since the review closed. No `git stash` / `checkout` / `restore` / `worktree`, no branch, no commit, no `pytest`, no coverage-shaped flag, no write to source, tests, `examples/`, a sibling spec, the terms CSV, `CHANGELOG.md`, `KANBAN*`, `docs/GLOSSARY.md`, or the DB. Two Markdown files under this cycle's ownership were edited, plus this artifact.

Worker 3's diagnosis is accepted in full and is the frame for the whole pass: **all three Mediums are one defect — a number taken from a nearby artifact instead of from its population.** So the remedy is not three edits. Every numeral standing in either durable file was re-derived against its actual population before this block was written, which found two more instances neither the review nor R2 had (`### The measurement sweep` rows 12 and 15) and cleared the rest.

### Disposition of every finding

| Finding | Disposition | What changed |
|---|---|---|
| **M1** | **Closed by edit, as prescribed** | `spec:9` retitled `**Ambiguous model-to-type resolution.**` and its first clause rewritten to name the direction the failure lives in. `model_for_type` is dropped from the sentence rather than restated as the safe direction — `spec:32` already says it is one-to-one, and repeating it inside the failure class would have duplicated `spec:34`'s enumeration. Recorded in the rationale's `## Problem statement` entry with the source evidence, and "that the type-to-model direction of the registry can be ambiguous" added to that entry's *claims the section no longer makes* list. `### One model, many types, one primary` was not reopened. |
| **M2** | **Closed by edit; nine, re-derived from the population** | Both occurrences corrected to **nine**. The rationale now states the population and how it was obtained, so the figure is re-derivable from the sentence rather than from a comment. Two further errors in the same paragraph were fixed with it: the source comment is now described as an annotation of one run of specs rather than as the census, and the claim that the two named tests "pin two instances of it" is corrected — `interfaces` is a promotion, so only `::test_meta_relation_shapes_in_allowed_meta_keys` pins the third route, and its sibling pins the promoted case the net-new one is defined against. |
| **M3** | **Closed by edit; seven bullets, five false** | Rewritten to seven bullets (four under `0.0.2 shipped:`, three under `0.0.3 shipped (in flight):`), five false as present tense with each named, the two survivors named as survivors, and the `Meta.primary` falsehood moved to where it actually sits — the closing paragraph, as a sixth falsehood outside the bullet lists. |
| **L1** | **Closed by edit** | `spec:42` now closes the boundary: the four-corner claim "stops there", and an annotation asking for the model-inferred type (`name: auto`) is routed back into synthesis. Worker 3's suggested shape (a subordinate clause) was adopted but split into a second sentence — the one-sentence version ran to four clauses. No rule the owning specs hold is restated; the spec states only the edge of its own claim. Recorded in the rationale's R2-layer `### Consumer override semantics` entry with the rejected alternative (describing the marker's rules here). |
| **L2** | **Closed by edit, not by a rationale note** | Worker 3 offered either. Aligning the bullet is the better fix: the bullet was demanding a form the package has deliberately decided against, so a note explaining that would have documented a live contradiction instead of removing one. `spec:22` now reads "labeled as temporary where the surface is published, and names what lifting it waits on", which is what `docs/GLOSSARY.md` already does (`planned for 0.1.1` / `0.1.2` / `0.1.3` on the three deferred keys — read, not assumed). Recorded in the `## Goal` entry, whose heading is widened to cover both bullets, with the new retraction in its claims list. |
| **L3** | **Closed, but not the way the finding frames it** | Worker 3 is right that the pass named one instance of a class and not the other, and my own carry-forward says never to answer that by re-reading for a second instance. So the population was **established**: layer 1 was read for present-tense claims about what the spec currently says, and there are **four** — `## Provenance of this record`'s "deliberately left" list, the item-1-is-untouched note, "still in the spec" about the placeholder-test promise, and the same about the must-update instruction. None was edited: rule 4 makes layer 1 append-only and these are records of what that pass did, not claims it is now making. The whole set is named in one `## How to read this file` clause, which is navigation rather than record, and which covers all four at once instead of annotating each. |
| **L4** | **Closed by edit; seven, and a second defect in the same sentence pair** | The unit was mixed, as charged. It is now **seven keys**, with the six `attr` labels explained (`nullable_overrides` and `required_overrides` validate together under one label). The sweep also caught that the same sentence said enumerating them "would have been another roster to keep current" — `spec:56` **does** enumerate them, so the rationale was describing a decision the spec did not make. Replaced with why naming them there is safe where a key roster is not: each name is a consequence of the rule stated beside it. |
| **L5** | **No edit, as required; hand-off recorded** | The source file belongs to R3's Worker 2 under the widened authorization. Checked for the obligation the dispatch names — whether either durable file says anything the two pending docstring corrections would falsify — and **nothing does**: neither file quotes or characterizes either docstring, and `spec:56`'s claim (the helper is the single source, five further keys owe the same shape) becomes *more* true once `_format_unknown_fields_error`'s docstring stops naming three keys. Nothing was pre-written. See hand-off 1 below. |
| **L6** | **Closed by completing the record, not by un-ticking** | Worker 3 offered either and preferred not manufacturing alternatives. Both entries now carry an explicit *no alternative was weighed here, and that is the record rather than an omission* paragraph — `## Non-goals` (a word stating the opposite of what shipped has one disposition; the only real choice inside it was whether to name the owning specs) and `## References` (an unresolvable reference, a bullet naming a deleted test, and three unreachable owners). The tick at `:57` now holds as written, so it stands rather than being un-ticked. |

### The measurement sweep

Every numeric or count-shaped claim standing in either durable file, each verified against its own population. Rows 12 and 15 are new defects this sweep found; rows 3, 4 and 13 are the three Mediums; row 14 is L4.

| # | Claim | Where | Verified against | Result |
|---|---|---|---|---|
| 1 | four failure classes | `spec:7`, `:9-12` | the list | 4 items — holds |
| 2 | three buckets; failure class 4; `Meta.interfaces` has occupied two of three | `spec:60`, `:71`, `:75` | the list; the item; the historical sets | holds — `interfaces` sat in `ALLOWED` pre-`0.0.3`, in `DEFERRED` at `0.0.3-0.0.4`, in `ALLOWED` since |
| 3 | 17 accepted / 3 deferred at HEAD; the section listed 5 and 6 | rationale `### Accepted vs deferred …` | `types/base.py` at HEAD; `git show HEAD:` of the spec | 17 / 3, and the HEAD section lists exactly 5 and 6 — holds |
| 4 | 12 keys added; 3 of the 6 listed deferrals promoted, at `0.0.5` / `0.0.8` / `0.0.8` | same | oldest `ALLOWED_META_KEYS` definition is exactly `model` / `fields` / `exclude` / `name` / `description`; `docs/GLOSSARY.md` status lines | holds |
| 5 | the three still deferred are `fields_class` / `search_fields` / `aggregate_class` | same | `DEFERRED_META_KEYS` at HEAD | holds |
| 6 | eleven minor versions since `0.0.3`; eleven-plus specs; zero-for-eleven | rationale, several | `pyproject.toml` = `0.0.14`; the spec-count claims are hedged with "at least" | holds |
| 7 | four moved rules, three sub-questions, four "deliberately left" passages across three sections | rationale layer 1 | the moved blocks; the Provenance list | 4 / 3 / 4 passages in 3 sections — internally consistent, holds |
| 8 | four concrete gaps at HEAD, three stating falsified present-tense facts | rationale `## Problem statement` | `git show HEAD:` — items 1, 2, 4 are present-tense and falsified; item 3 is self-dated ("Until 0.0.3") and handled separately two paragraphs later | holds |
| 9 | three candidate approaches, wrong three ways out of three, the mechanism is a fourth | rationale, `spec:48` | the moved block | holds |
| 10 | three retitled topics; two re-keyed entries; two entries keyed to removed headings; 9 in-page anchors; 11 spec headings | rationale + spec | measured with `check_spec_glossary.py::github_anchor` | holds; re-measured after this pass's edits |
| 11 | three predecessor cycles had pseudo-code to dispose of | rationale layer 1 | `docs/SPECS/appx/` — `spec-001` (a `plan_relation` pseudocode block), `spec-003` ("all **seven** fenced pseudo-code blocks"), `spec-004` ("all **eight**") | at least three prior cycles disposed of pseudo-code, so the claim's substance holds under every reading of "predecessor" I tested. Recorded rather than edited: which prior cycles count is ambiguous, and the claim is about process history, not about the spec or the package |
| 12 | **the two `**Future direction.**` blocks "are the same length"** | rationale `## Standing note` | measured from the HEAD spec: **245 words vs 112** | **FALSE — corrected.** The sentence carried an argument ("not luck and not effort"), and length is not neutral here: the block that fared worse is also the shorter. Rewritten to say so and to give the reason (a shortlist of three techniques takes fewer words than a table of required outcomes), which strengthens the paragraph's real point about form rather than resting it on a false premise |
| 13 | **six of twelve net-new keys; six of seventeen** | rationale `### Accepted vs deferred …` | full replay, below | **FALSE — nine and nine** |
| 14 | **two keys widened to six** | rationale `### Invalid …` | the call sites | **mixed units — seven keys, six `attr` labels** |
| 15 | **"the four owning specs" added to `## References`** | rationale `## References` | `git show HEAD:` vs now: added paths are `spec-018`, `spec-010`, `spec-019` | **FALSE — three, in two bullets. Corrected.** The same wrong figure is in this artifact's pass-1 `### Spec changes made` row for `spec:87-92`; superseded below |
| 16 | five call sites / three named tests / both `Contract.` blocks / seven anchors | spec + rationale | re-read at HEAD | holds (five direct call sites at `types/base.py` lines within `_validate_optimizer_hints`, `_selected_meta_targets`, and `_select_fields`) |

**How the M2 population was actually obtained, because the method matters more than the number.** `git log -S'DEFERRED_META_KEYS' -- django_strawberry_framework/types/base.py` — the command the review names — returns 11 commits, and it is the wrong instrument: `-S` fires when the *occurrence count of the string* changes, so it tracks references to the identifier (docstrings included) and is blind to membership changes inside the set, which alter no count. Three of the four distinct definitions do not appear in its output. The population is instead every revision of the file: `git log --follow` gives **77** commits touching it, each `git show <c>:<path>` parsed for the `DEFERRED_META_KEYS = frozenset(...)` assignment, yielding **four distinct definitions** whose union is exactly six keys ever — `aggregate_class`, `fields_class`, `filterset_class`, `interfaces`, `orderset_class`, `search_fields`. The same replay over `ALLOWED_META_KEYS` gives 13 distinct definitions, oldest `= {description, exclude, fields, model, name}` and newest 17. So: 12 added, 3 of them ever-deferred (`interfaces`, `filterset_class`, `orderset_class`), **9 net-new** — `connection`, `cursor_field`, `filesystem_path_fields`, `globalid_strategy`, `nullable_overrides`, `optimizer_hints`, `primary`, `relation_shapes`, `required_overrides`. Worker 3's conclusion reproduces exactly; the command it cites would not have established it.

The source comment's six is a clause count, confirmed by reading it: it names `filesystem_path_fields`, `nullable_overrides` / `required_overrides` (one clause, two keys), `connection`, `globalid_strategy`, `relation_shapes`, `cursor_field` — seven keys in six clauses — and omits `primary` and `optimizer_hints`, which predate the run of specs it annotates.

### Files touched

- `docs/SPECS/spec-005-django_type_contract-0_0_3.md` — three edits: `spec:9` (M1), `spec:22` (L2), `spec:42` (L1). No other line changed.
- `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md` — twelve edits across eight R2-layer entries (`## Problem statement`, `## Current state`, `## Goal`, `## Non-goals`, `### Consumer override semantics`, `### Invalid …`, `### Accepted vs deferred …`, `## References`) plus `## How to read this file` and `## Standing note`. Nothing in layer 1 was rewritten or removed.
- `docs/builder/bld-005-r2-spec_reconciliation.md` — the `Status:` line and this appended block. No prior block edited.

### Byte count

| | lines | bytes |
|---|---|---|
| spec at HEAD (pre-cycle) | 154 | 13,346 |
| spec after R2 pass 1 | 122 | 13,025 |
| **spec after R2 pass 2** | **122** | **13,373** |
| net vs. HEAD | -32 | **+27 (+0.2%)** |
| rationale after R2 pass 1 | 640 | 44,958 |
| **rationale after R2 pass 2** | **713** | **51,373** |

The spec now ends 27 bytes *above* HEAD rather than 321 below, which is worth stating plainly rather than letting the earlier "-2.4%" stand: L1's boundary clause is the whole difference, and it is contract. Line count is unchanged, so no section grew a paragraph. The rationale took 6,415 bytes, which is where a pass whose findings are all "the record is wrong about its own population" should spend them. Fences: **0** in both files, unchanged.

### Validation run

Every command re-run in this pass; nothing carried from pass 1 or from the review.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-005-django_type_contract-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` **exit 0**. Character-identical to the pre-flight baseline, to pass 1's quotation, and to the review's.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-005-django_type_contract-0_0_3.md docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md docs/builder/bld-005-r2-spec_reconciliation.md` → **exit 0** on all three, this artifact included after the append.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 49 done cards have glossary links.` **exit 0**; no DB churn (`git status --short -- examples/fakeshop/db.sqlite3` empty).
- **Duplication re-measured over both file bodies** (text before `<!-- LINK DEFINITIONS -->`), same three tokenizers the review used:

  | tokenizer | n=8 | n=7 | n=6 |
  |---|---|---|---|
  | punctuation kept | **0** | 1 | 3 |
  | punctuation stripped, `.` `#` `_` retained | **0** | 1 | 6 |
  | alphanumeric only | 2 | 9 | 21 |

  **0 at n=8 under both named tokenizers**, and the survivors are the same required set: three section headings the keying rule forces the rationale to reproduce, plus "the rejection of first-registered-wins", which two rules jointly require. The stripped n=7 figure improved from 2 to 1 and the adversarial tokenizer's n=8 from 7 to 2 (both remaining hits are identifier runs — `spec 005 django type contract 0 0 3`, `spec 018 meta primary 0 0 6 md`), because the rewrite of the `### Accepted vs deferred …` and `### Invalid …` paragraphs removed prose the review had accepted.

  **The check earned its place again.** The first draft of L1's rationale paragraph opened by quoting `spec:42`'s lead clause verbatim, which put **2 hits punctuation-kept and 4 punctuation-stripped** on the board at n=8 — a quotation of current contract, the exact class R1 and R2 each had to learn. It reads as scrupulous attribution and is a second copy. Replaced with a description of the sentence; the measurement is what caught it, not the reading.
- **Line granularity, re-derived off `git diff -U0`.** **65 removed non-empty lines against HEAD**, byte-identical to the population R2 walked 45/45 and Worker 3 re-derived, so no re-walk was owed — this pass removed no further HEAD line (44 added non-empty lines; `git diff --stat` unchanged at `45 insertions(+), 77 deletions(-)`, its extra insertion being a blank line). The one HEAD line whose disposition this pass changed is `## Goal`'s third bullet ("Hard constraints that look temporary are labeled as such, with a named follow-up spec"): still restated as contract, with the follow-up-spec clause now deliberately not carried, and that retraction added to the `## Goal` entry's claims list so the accounting stays complete.
- **Reference integrity, both files, code spans stripped:** spec **8 definitions / 8 distinct uses**, rationale **19 / 19**, **0 undefined and 0 unused in both**. All 27 targets resolve on disk from their own file's directory. No definition was added or removed this pass.
- **Anchors slug-checked** with `scripts/check_spec_glossary.py::github_anchor`: all **9** rationale → spec in-page fragments resolve against the post-edit spec's **11** headings; duplicate heading slugs **0** in the spec and **0** in the rationale's **19**. The one heading this pass retitled (`### `## Goal` — …`) is a rationale heading with no inbound anchor, checked before changing it.
- `grep -nE '[a-zA-Z_/]+\.(py|md|csv|txt|json):[0-9]+'` over both durable files → no match. `grep -nP '\]\((?!#|https?:)'` over both → no match. `grep -c '^```'` → 0 / 0.
- `git status --short` unchanged in shape: baseline is the five spec-004-cycle entries plus the four staged-deleted `bld-003-*.md`, and this cycle's four (`M spec-005`, `?? rationale`, `?? bld-005-r1`, `?? bld-005-r2`). `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3` all clean. Nothing reverted (`AGENTS.md` rule 34).
- **Not swept into a concurrent commit.** `git log --stat` over the cycle's paths: newest commit reaching the spec is `ff65666d`, which predates the cycle; `git log` over the rationale and both `bld-005-*` artifacts is empty. `git status` alone was not used for this.
- No `pytest`, no `ruff` (no `.py` touched), no coverage-shaped flag.

### The 7-anchor constraint — re-measured after these edits

Reference-style body uses only. **All seven still at exactly 1 use + 1 definition, and no carrier moved**: `djangotype` `spec:7`, `metafields` and `metaexclude` `spec:11`, `metaprimary` `spec:34`, `configurationerror` and `metamodel` `spec:52`, `metainterfaces` `spec:75` — row for row the table Worker 3 independently confirmed. `spec:9` is the one edited line inside a carrier section, and it carries none; `spec:22` and `spec:42` carry none. The terms CSV was not opened.

`docs/SPECS/spec-006-public_surface-0_0_3.md:108`'s by-title citation is untouched: `### Accepted vs deferred Meta keys` was not edited this pass, and `spec-006` is clean in `git status`.

### Corrections to this artifact's own pass-1 record

Recorded here rather than by editing the prior block, which stands as written.

- `### Spec changes made (Worker 1 only)`, row `spec:87-92`: "four owning specs added" is **three** (`spec-018`, `spec-010`, `spec-019`, in two bullets). Same defect as M2/M3, in the artifact rather than in a durable file; the rationale's copy of it is fixed.
- `### Spec changes made (Worker 1 only)`, row `spec:75`: "both real pinning-test names" over-states what landed — `spec:75` names one (`::test_interfaces_is_shipped_not_deferred`). The second name lives in the rationale, correctly, and the spec is right to name one: the paragraph is about `Meta.interfaces`. No spec edit owed; the row is superseded.
- `### Dispatched findings checklist` box at `:60` ("the over-absorption trap was refused … named as owners"): Worker 3's accuracy note is right that the **spec** names three owners and the **rationale** names seven. The tick's contract — no sibling's rules restated, none edited — holds in both, which is what the box is auditing; the phrasing reads as a claim about the spec alone. Superseded, not un-ticked.
- Box at `:57` (rejected alternatives in every entry): held open by L6 during the review, **now true as written** — the two entries that lacked the record carry it explicitly. Tick stands.
- Every other box in `### Dispatched findings checklist` was re-audited against the current state of the two files and still holds; the figures inside boxes 12, 13 and 20 (the checker output, the comma check, the shingle result) are re-quoted above and are unchanged or improved.

### Hot-path budget / Floor verification / Failability proofs

Not applicable, unchanged from pass 1 and for the same reasons: the plan declares no hot path and floor-verification scope `none` build-wide, and this pass edits two Markdown files, introducing no boundary, guard, or rejection path. Nothing is owed.

### Notes for Worker 1 (spec reconciliation)

Hand-offs to R3 and to the final gate.

1. **L5 needs no anticipatory edit and must not get one.** Worker 0 widened `### THE ONE SOURCE EDIT THIS CYCLE AUTHORIZES` to cover `django_strawberry_framework/types/base.py::_format_unknown_fields_error`'s docstring alongside `exceptions.py::ConfigurationError`'s. Both were checked against the two durable files and **nothing in either is falsified by either correction**: no sentence quotes or characterizes either docstring, and `spec:56` (single source, five further keys owe the same shape) is what the widened docstring should be made to agree with, not the reverse. When R3's Worker 2 writes it, the true reach is **seven keys under six `attr` labels** — `fields`, `exclude`, `optimizer_hints`, `nullable_overrides` / `required_overrides` (one label), `filesystem_path_fields`, `relation_shapes` — reached from five direct call sites, three of them via `_selected_meta_targets`. Measured, not read off `spec:56`.
2. **The methodological finding is worth more than M2's number.** `git log -S` over an identifier does not establish set membership over time — it tracks references to the name, and a key added to or removed from a `frozenset` literal changes no occurrence count. Three of the four historical `DEFERRED_META_KEYS` definitions are invisible to it. Replay the definition over `git log --follow` instead. This generalizes to every "which values did this constant ever hold" question in this repository.
3. **A count asserted beside the lesson it illustrates was wrong three times in this artifact and twice more in the sweep.** M2, M3, L4, plus `## References`' "four owning specs" and `## Standing note`'s "same length" — five instances, all in sentences whose *argument* is correct and whose supporting figure was taken from something nearby. `docs/builder/BUILD.md` `## Claims are proven mechanically` names this exactly; the practical rule is that a numeral inside an explanatory sentence needs its population named in the same sentence, which is now how the rationale states the two that matter.
4. **Rule 4 was not bent this pass.** Pass 1 re-keyed two layer-1 entries; this pass edited **no** layer-1 text. L3's four stale present-tense sentences stay exactly as R1 wrote them and are disclosed in `## How to read this file`, which is navigation. If a later pass wants them corrected, that is a decision about whether the rationale's first layer is a record or a description, and it should be taken deliberately rather than as tidy-up.
5. **`## Standing note` is layer-1-adjacent and this pass edited it.** Distinguishing it from L3: it is not a record of what a pass moved, it is an analytical coda, and the clause corrected was a measurable factual premise that measures false (245 words vs 112). Flagged so Worker 3 can charge the distinction if it disagrees; the alternative — leaving a false premise standing under a "record" defence — seemed worse than the edit.
6. **For R3's durable-doc audit**, unchanged from pass 1 and re-confirmed: `docs/README.md` has no `## Current surface` section and no reference to spec-005; `docs/GLOSSARY.md`'s `Meta.interfaces` / `Meta.primary` entries are correct and carry the full ambiguity table; and the three deferred keys are labeled by release (`0.1.1` / `0.1.2` / `0.1.3`), which is the fact `spec:22` now depends on.
7. **Baseline unchanged.** No growth, nothing reverted, no `git checkout`. The four staged-deleted `docs/builder/bld-003-*.md` entries still await the maintainer. Re-derive `HEAD` rather than quoting `ff03c137`.

### Review outcome

Not applicable — this is the Worker 1 apply-changes pass. `Status: planned` on return, which Worker 0 reads as "dispatch Worker 3" per Deviation 2. All three Mediums and all six Lows are closed; none is rejected, and none is deferred. Two additional defects of the same class were found by the sweep and closed with them, and three figures in this artifact's own pass-1 record are superseded above.

---

## Review (Worker 3, pass 2)

Re-review of the apply-changes pass. `HEAD` re-derived, not quoted: `ff03c1372365edcad488ff4671389d88ae145276` — unmoved since pass 1. `git log --oneline -1 -- docs/SPECS/spec-005-django_type_contract-0_0_3.md` still tops out at `ff65666d`, which predates the cycle; `git log` over the rationale and both `bld-005-*` artifacts is empty. Baseline dirty is unchanged in shape: the five spec-004-cycle entries, the four staged-deleted `docs/builder/bld-003-*.md`, and this cycle's four. Nothing reverted, no `git checkout`.

Read-only HEAD copy of the pre-cycle spec taken with `git show HEAD:… > <scratchpad outside the repo>`. No `git stash` / `checkout` / `restore` / `worktree`, no branch, no commit, no source or test edit, no `pytest`, no coverage-shaped flag.

Per the dispatch this pass does **not** re-derive what pass 1 settled (the spec's truth at HEAD across the sentences traced to source, the absence of history narration, the 65-line removal accounting, the 27 link definitions, the `spec-006:108` citation, the untouched source files — the last of which is re-confirmed below because it is a standing scope gate). It concentrates on whether the nine findings closed, on the corrected numbers, and on collateral damage.

### High:

None.

### Medium:

#### M4 — the methodological finding is false as measured, and it is being promoted as a standing repo-wide rule

`docs/builder/bld-005-r2-spec_reconciliation.md:638` and `:712` (hand-off 2)

```docs/builder/bld-005-r2-spec_reconciliation.md:638
… it is the wrong instrument: `-S` fires when the *occurrence count of the string* changes … and is
blind to membership changes inside the set, which alter no count. Three of the four distinct
definitions do not appear in its output. … Worker 3's conclusion reproduces exactly; the command it
cites would not have established it.
```

Re-derived, and it does not hold. `git log --format=%h -S'DEFERRED_META_KEYS' -- django_strawberry_framework/types/base.py` returns **11** commits (matching the report). Running the review's own prescribed second half — `git show <c>:django_strawberry_framework/types/base.py` on each of those 11 and parsing the assignment — yields:

| blob | `DEFERRED_META_KEYS` |
|---|---|
| `f5d03652`, `27d62919`, `b14232fa` | `aggregate_class` `fields_class` `filterset_class` `interfaces` `orderset_class` `search_fields` |
| `70c7bff2`, `e836d72e`, `7e6a7fc4` | `aggregate_class` `fields_class` `filterset_class` `orderset_class` `search_fields` |
| `1694bd2e`, `a4bd4c73` | `aggregate_class` `fields_class` `orderset_class` `search_fields` |
| `11d9fbe0`, `23cb569a`, `46ffc64f` | `aggregate_class` `fields_class` `search_fields` |

That is **all four** distinct definitions and a union of **exactly the six keys**, identical to the 77-revision `--follow` replay. Not three-of-four missing: **zero** of the four missing. The only definition-bearing commit absent from the `-S` output is `084b4643`, and it is absent because it predates the rename and lives at `django_strawberry_framework/types.py`, which the pathspec excludes — a pathspec effect, not an `-S` effect, and `--follow` has the identical exposure (it resolves `<commit>:types/base.py`, which does not exist there either).

Why it matters more than a wrong sentence: hand-off 2 elevates this to a standing rule — "This generalizes to every 'which values did this constant ever hold' question in this repository" — and the pass frames it as "worth more than M2's number". A false method lesson propagates further than a false count, and this one also tells a future reader that the prior review's correct method was unsound when in fact it produced the right population.

The *hazard* is real and worth keeping: `-S` counts occurrences, so a membership change inside a `frozenset` literal **can** be invisible to it, and nothing guarantees an incidental co-change will surface the commit. Recommended change: state it as a hazard that did not bite here (`-S` happened to fire on all four because each definition change rode with a docstring or comment edit that moved the occurrence count), drop "three of the four … do not appear in its output" and "the command it cites would not have established it", and keep the positive recommendation to replay the definition over `git log --follow`. Note when restating it that `--follow` needs the pre-rename path resolved too, or it silently drops the oldest revisions — see L9.

#### M5 — three figures of the corrected class are left standing unmarked in this artifact's own pass-1 record

The pass elected supersession over editing (`### Corrections to this artifact's own pass-1 record`) and applied it to three figures. Three more of exactly the same class were missed, and one of them is the number M2 corrected:

- `docs/builder/bld-005-r2-spec_reconciliation.md:270` — `### Spec changes made (Worker 1 only)`, row `spec:73`: "the two-bucket partition cannot express it, and **six of the twelve added keys arrived that way**". Nine. This is the per-line change record Worker 1's own final verification walks, so the corrected figure lives in the rationale while the uncorrected one lives in the table that says what the rationale was written to explain.
- `:121` — drift row D16: "`_format_unknown_fields_error` has five call sites reaching **six keys**". Seven (L4's own correction).
- `:135` — `### The read-only correctness audit, re-verified`: "reached by five call sites covering **six keys**: `fields`, `exclude`, `optimizer_hints` (×2 sites), and … `nullable_overrides` / `required_overrides`, `filesystem_path_fields`, `relation_shapes`" — the enumeration beside the numeral lists **seven** keys, so the sentence contradicts itself in place.

Recommended change: three more rows under `### Corrections to this artifact's own pass-1 record`, in the same form as the three already there. No durable file is affected and none should be touched.

### Low:

#### L9 — the "oldest `ALLOWED_META_KEYS` definition" is wrong, in the same paragraph as M4, and contradicts the pass's own sweep row 2

`docs/builder/bld-005-r2-spec_reconciliation.md:638`

```docs/builder/bld-005-r2-spec_reconciliation.md:638
The same replay over `ALLOWED_META_KEYS` gives 13 distinct definitions, oldest
`= {description, exclude, fields, model, name}` and newest 17.
```

Replayed over the same population the sentence names — all **77** `git log --follow` revisions, resolving each blob at `types/base.py` and falling back to `django_strawberry_framework/types.py` for the pre-rename commits the follow chain still lists — there are indeed **13** distinct definitions, but the oldest (`084b4643`, 2026-04-29) is **six** keys: `description`, `exclude`, `fields`, **`interfaces`**, `model`, `name`. The five-key set is the *second* definition (`f5d03652`, "Start specs for 0.0.3"), which is where `interfaces` was removed. Reporting 13 and reporting a five-key oldest cannot both be true: dropping `084b4643` gives 12.

This is the pass's own sweep row 2 seen from the other side — "`interfaces` sat in `ALLOWED` pre-`0.0.3`, in `DEFERRED` at `0.0.3-0.0.4`, in `ALLOWED` since" — so the paragraph contradicts a row it verified twelve lines earlier.

**No durable file is affected and none should be edited.** I checked whether the nine survives the correction and it does, robustly: against the true oldest set of six, 17 − 6 = **11** added of which **2** (`filterset_class`, `orderset_class`) were ever deferred → **9**; against the spec's own roster of five, 12 added of which 3 were ever deferred → **9**. And the rationale anchors its "twelve" explicitly on the spec's roster in the same paragraph ("The section listed five accepted keys … twelve keys were added"), which is the correct baseline for an entry about that section. Only the artifact's method record is wrong. Recommended change: state the oldest as six keys including `interfaces`, or drop the "oldest" clause, and record the `--follow` pre-rename-path trap beside it.

#### L10 — hand-off 1's call-site sentence reads false, and it is the specification for a docstring Worker 2 will write into source

`docs/builder/bld-005-r2-spec_reconciliation.md:711`

```docs/builder/bld-005-r2-spec_reconciliation.md:711
… reached from five direct call sites, three of them via `_selected_meta_targets`.
```

Measured at HEAD. `_format_unknown_fields_error` has **five** direct call sites (`django_strawberry_framework/types/base.py:1270`, `:1280`, `:1324`, `:1612`, `:1624`) in **three** functions (`::_validate_optimizer_hints`, `::_selected_meta_targets`, `::_select_fields`). Exactly **one** of the five is inside `_selected_meta_targets`. What routes *via* `_selected_meta_targets` is three `attr` **labels**, from `::_validate_nullability_override_targets` (`attr="nullable_overrides/required_overrides"`), `::_validate_filesystem_path_targets` (`attr="filesystem_path_fields"`) and `::_validate_relation_shape_targets` (`attr="relation_shapes"`), all reaching the single `attr=attr` forwarding site.

The grammatical antecedent of "three of them" is "five direct call sites", and under that reading the clause is false. Everything else in the sentence is right and I re-derived it: **seven keys under six `attr` labels** — `fields`, `exclude`, `optimizer_hints`, `nullable_overrides` / `required_overrides` (one label), `filesystem_path_fields`, `relation_shapes`. Because R3's Worker 2 will turn this sentence into docstring prose, an ambiguity here becomes a false claim in shipped source, which is the defect class the widened authorization exists to remove. Recommended change: "five direct call sites in three functions … ; three of the six labels arrive through `_selected_meta_targets`."

#### L11 — plan defect, for Worker 0: the widening note's `attr` count is the same clause-vs-census error

`docs/builder/build-005-django_type_contract-0_0_3.md:249`

```docs/builder/build-005-django_type_contract-0_0_3.md:249
It has **five call sites passing eight distinct `attr` values** …
```

Five call sites is right; **eight** distinct `attr` values is not — there are **six**. Eight is the number of `attr=` occurrences in `types/base.py` (`:1272`, `:1282`, `:1326`, `:1396`, `:1471`, `:1536`, `:1614`, `:1626`), of which `:1272` and `:1282` carry the same literal `"optimizer_hints"` and `:1326` is the forwarding `attr=attr`, which is not a value at all. Counting occurrences of a token rather than members of the set it names is precisely the failure M2 charged in the rationale and L4 charged in the same helper's arithmetic.

It matters because this note is what scopes the docstring: the plan says eight, R2's hand-off 1 says six labels / seven keys, and Worker 2 is dispatched against both. I do not edit the plan (Worker 0 owns it). Recommended: `six distinct `attr` values covering seven `Meta` keys`, and align it with hand-off 1 as corrected by L10.

### Did each of the nine findings close?

Verified in the diff, not from the disposition table. All nine closed by edit; none rejected, none deferred; the closes address the finding rather than touching the line.

| Finding | Landed at | Verdict |
|---|---|---|
| M1 | `spec:9` retitled `**Ambiguous model-to-type resolution.**`; the class now names relation targets and "every other question of which type stands for a given model"; `model_for_type` gone from the sentence | **Closes.** See "The two edits that removed rather than restated" below. |
| M2 | rationale `:557-570` — **nine**, twice, with the population and its derivation stated in the sentence | **Closes, and the number is right.** Re-derived below. |
| M3 | rationale `:334-342` — seven bullets (four + three), five named false, two named as survivors, the `Meta.primary` falsehood moved to the closing paragraph as a sixth | **Closes, and the numbers are right.** Re-derived below. |
| L1 | `spec:42` — "and it stops there", plus a second sentence routing `name: auto` back into synthesis | **Closes.** Verified against `types/base.py::DjangoType.__init_subclass__` #"``field: auto`` is the \"declare-but-infer\" marker": `auto`-annotated names are excluded from `consumer_annotated_relation_fields` / `consumer_annotated_scalar_fields` and dropped from `consumer_annotations`, so the synthesized annotation wins. No rule `spec-019` owns is restated. |
| L2 | `spec:22` — "labeled as temporary where the surface is published, and names what lifting it waits on" | **Closes.** The spec-naming obligation is gone. Verified against `docs/GLOSSARY.md:154`, `:160`, `:173`: `Meta.aggregate_class` `planned for 0.1.3`, `Meta.fields_class` `0.1.1`, `Meta.search_fields` `0.1.2` — labelled by release, never by spec, exactly as the bullet now asks. |
| L3 | rationale `## How to read this file` `:29-36` — the population established at four and all four named, no layer-1 text edited | **Closes.** Judged below. |
| L4 | rationale `:515-521` — **seven** keys, six `attr` labels, with the one-label pairing explained | **Closes, and both numbers are right.** Re-derived below. The second defect the pass caught with it ("would have been another roster to keep current", contradicted by `spec:56` enumerating them) is real and correctly replaced. |
| L5 | no edit; hand-off recorded | **Correct.** `git status --short -- django_strawberry_framework/ tests/ examples/` is empty and `git diff --stat` over those trees is empty, so **both** authorized docstrings are untouched by this item. |
| L6 | rationale `:410-413` (`## Non-goals`) and `:642-644` (`## References`) — each now carries an explicit *no alternative was weighed here, and that is the record rather than an omission* paragraph | **Closes.** The tick at `:57` now holds as written; completing the record rather than un-ticking was the right of the two options offered. |

### The corrected numbers, re-derived independently

Every figure below was measured from its own population by me, not compared against the report.

**M2's nine — confirmed, by a method that does not depend on `-S` or on `--follow` alone.** I enumerated the `.py` files that ever held either constant with `git log -S… --name-only` (sound for *locating files*: a file that ever contained the identifier must have taken its occurrence count from zero at some commit), which returns `django_strawberry_framework/types.py` and `django_strawberry_framework/types/base.py` and nothing else. I then replayed **every** revision of both paths (78 commits, 77 resolvable blobs) and parsed the balanced literal after each assignment:

- `DEFERRED_META_KEYS` — **four** distinct value-sets across five transitions (the 5-key set recurs after `interfaces` is dropped back out), union **exactly six keys ever**: `aggregate_class`, `fields_class`, `filterset_class`, `interfaces`, `orderset_class`, `search_fields`. Matches the rationale verbatim.
- `ALLOWED_META_KEYS` — 13 distinct definitions, newest **17**, oldest six (L9).
- Therefore: three of the six ever-deferred keys are in `ALLOWED_META_KEYS` today (`interfaces`, `filterset_class`, `orderset_class`); the other nine current keys never sat in `DEFERRED_META_KEYS` at any revision — `connection`, `cursor_field`, `filesystem_path_fields`, `globalid_strategy`, `nullable_overrides`, `optimizer_hints`, `primary`, `relation_shapes`, `required_overrides`. **Nine.** Robust to the baseline question L9 raises.
- The promotion versions hold: `docs/GLOSSARY.md:164` `Meta.interfaces` `shipped (0.0.5)`, `:162` / `:169` `filterset_class` / `orderset_class` `shipped (0.0.8)`.
- The source comment's arithmetic holds: it names `filesystem_path_fields`, `nullable_overrides` / `required_overrides` (one clause), `connection`, `globalid_strategy`, `relation_shapes`, `cursor_field` — **seven keys in six clauses**, all seven among the nine, and it omits `primary` and `optimizer_hints`. "names seven of the nine; counting its clauses gives six" is exact.

**M3's seven-and-five — confirmed against the HEAD section, read from `git show HEAD:`.** `## Current state` carries four bullets under `0.0.2 shipped:` and three under `0.0.3 shipped (in flight):` = **seven**. False as present tense: the collision raise; the known-broken override merge; `Meta.interfaces` accepted-and-silently-ignored; `Meta.fields` / `Meta.exclude` typos silently dropped; `Meta.interfaces` moved to `DEFERRED_META_KEYS` with a rejection pointing at a future relay spec = **five**, and they are the five the entry names. The two survivors are the `_select_fields` raise and the `_is_default_get_queryset` / `has_custom_get_queryset` bullet, both restated into the spec. The closing paragraph's "the registry uniqueness resolution is deferred to a future `Meta.primary` spec" is a sixth falsehood outside the bullet lists, sited exactly where the entry now puts it.

**L4's seven keys / six `attr` labels — confirmed at the raise sites.** Five direct calls at `types/base.py:1270`, `:1280`, `:1324`, `:1612`, `:1624`; distinct labels `optimizer_hints`, `nullable_overrides/required_overrides`, `filesystem_path_fields`, `relation_shapes`, `fields`, `exclude` = **six**; keys covered = **seven** (the paired label is two keys). `2 + 5 = 7` now reads consistently.

**The "5 direct call sites" recorded as hand-off 1 — confirmed as a count**, and it is the figure R3's Worker 2 will write into a docstring, so it was measured rather than inherited: exactly five call expressions, in exactly three enclosing functions. The clause attached to it is L10.

**`## References`' "the four owning specs" → three — confirmed.** Diffing the HEAD `## References` list (five bullets) against the current one (six bullets): the added spec paths are `spec-018`, `spec-010`, `spec-019` = **three**, in **two** bullets, the two override halves sharing one. Exactly as corrected.

**`## Standing note`'s "the two blocks are the same length" → 245 vs 112 — confirmed by measurement.** Whitespace-token count over the HEAD spec: the `Meta.primary` `**Future direction.**` block (HEAD `spec:53`, through the first-registered-wins rejection) is **245** words; the consumer-overrides block (HEAD `spec:76`, through "limited, not guaranteed") is **112**. The shorter is the one that fared worse, which is the direction the corrected sentence asserts.

**Sweep for numerals neither review has checked.** I extracted every number-word from both file bodies and walked the hits. Everything not already covered above holds or is a hedge: "eleven minor versions" against `pyproject.toml` = `0.0.14`; "the three still deferred — `fields_class`, `search_fields`, `aggregate_class`" against `DEFERRED_META_KEYS` at HEAD, and their `0.1.1` / `0.1.2` / `0.1.3` labels in that order against `docs/GLOSSARY.md`; "three buckets"; "four failure classes"; "eleven-plus specs" and "at least eleven" (hedged by construction); "occupied two of the three buckets" (`interfaces`: `ALLOWED` pre-`0.0.3`, `DEFERRED` `0.0.3-0.0.4`, `ALLOWED` since — the replay above shows it directly). The remaining number-words are rhetorical ("fifteen types") or structural ("one entry per section"). **No further numeral in either durable file is unverified.** The three that remain wrong are all in the artifact and the plan: M5, L9, L10, L11.

### Did the fixes disturb anything?

- **Anchors — re-derived, not compared.** Reference-style body uses only (`][glossary-<anchor>]` before `<!-- LINK DEFINITIONS -->`): `djangotype` `spec:7`, `metafields` `spec:11`, `metaexclude` `spec:11`, `metaprimary` `spec:34`, `configurationerror` `spec:52`, `metamodel` `spec:52`, `metainterfaces` `spec:75` — **all seven at exactly 1 use + 1 definition, every carrier line unmoved**, matching the pass's table row for row and pass 1's independently.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-005-django_type_contract-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` exit **0**, character-identical to every prior quotation.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-005-django_type_contract-0_0_3.md docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md docs/builder/bld-005-r2-spec_reconciliation.md` → exit **0** on all three, this artifact included after my append.
- **Duplication re-derived over both file bodies**, my own tokenizers:

  | tokenizer | n=8 | n=7 | n=6 |
  |---|---|---|---|
  | punctuation kept | **0** | 1 | 3 |
  | punctuation stripped (`.` `#` `_` `/` `-` kept) | **0** | 1 | 4 |
  | alphanumeric only (adversarial) | 2 | 10 | 23 |

  **0 at n=8 under both named tokenizers**, reproducing the report exactly; the punctuation-kept column matches it at every width. The adversarial tokenizer's two n=8 hits are `spec 005 django type contract 0 0 3` and `spec 018 meta primary 0 0 6 md` — the same two identifier runs the pass names, down from seven at review pass 1, so the improvement claim holds too. (My n=6 stripped figure is 4 against the report's 6; my tokenizer also keeps `/` and `-`, which is the tokenizer difference, not a change in the files. Reported per R1's standing lesson: the number is meaningless without its tokenizer.)
- **Link integrity.** Spec **8 definitions / 8 distinct uses**, rationale **19 / 19**, **0 undefined and 0 unused in both**; all **27** targets resolve on disk from their own file's directory (code spans stripped before the sweep). No definition added or removed this pass.
- **Anchors into the spec.** All **9** rationale → spec in-page fragments resolve against the spec's **11** headings, slugged with `scripts/check_spec_glossary.py::github_anchor`; duplicate heading slugs **0** in the spec and **0** across the rationale's **19**.
- **Byte counts reproduce.** Spec **122 lines / 13,373 B**, rationale **713 / 51,373**, HEAD spec **154 / 13,346**. Line count unchanged from pass 1 at 122, and the seven anchor carriers sit on the same seven lines as pass 1 recorded — which is the mechanical corroboration of "three edits, no other line changed", since any inserted or deleted line would have shifted at least one carrier.
- `docs/SPECS/spec-006-public_surface-0_0_3.md:108` still reads `… per \`spec-005-django_type_contract-0_0_3.md\` "Accepted vs deferred Meta keys"`; the heading is intact and `spec-006` is clean in `git status`. **No inbound break.**

### The two edits that removed rather than restated

Both judged on their merits, neither charged.

- **M1's fix drops `model_for_type` rather than naming it as the safe direction.** The finding offered both ("either drop `model_for_type` from the sentence or state it as the direction that is *not* at risk"), so dropping is the prescribed remedy, not a narrowing of it. It is also the better of the two: `spec:32` already carries the one-to-one statement in contract prose, and `spec:34` enumerates the model-to-type direction, so restating the safe direction inside a failure class would have put a third copy of one fact in one document — the shape this whole item exists to remove. What the finding actually charged was that the class pointed the reader at the direction that cannot exhibit the failure, and the retitle plus "every other question of which type stands for a given model" fixes exactly that. Verified against source: `registry.py::TypeRegistry.model_for_type`'s own docstring opens "Reverse-lookup: return the Django model for a registered `DjangoType`", and `::get` returns `None` for the ambiguous multi-type case rather than picking a first-registered winner — so nothing in the model-to-type direction breaks a tie by declaration order, and the failure class reads as the hazard the contract excludes rather than as current behaviour. **Not an under-fix.**
- **L3's fix disclosed a population of four without editing layer-1 text.** I established the population myself by reading layer 1 for present-tense claims about what the spec currently says, and it is four, exactly the four named: `## Provenance of this record`'s "Deliberately left in the spec by this pass" list (`:59-72`), the `## Problem statement` item-1-is-untouched note (`:102-103`), "The promise sentence is still in the spec" (`:222`), and "That sentence is still in the spec and is item R2's to decide on" (`:249`). Nothing else in layer 1 makes a present-tense claim about spec content that R2 falsified. The finding's own terms were "either both are flagged or neither is"; naming all four in one navigation clause satisfies that, and it satisfies it in the form my own carry-forward asks for — establish the class, do not chase a second instance. Rule 4's append-only makes editing the four the larger defect, and layer 1 is a record of a pass, not a description of the current spec. **Not an under-fix; it is the better remedy of the two available.**

On the adjacent judgement the pass invited (hand-off 5): editing `## Standing note` was right. It is R1-written but it is an analytical coda rather than a record of what a pass moved, the corrected clause was a measurable factual premise, and it measures false by better than 2:1. Leaving a false premise standing under a record defence would have been worse. One accuracy note, not a finding: hand-off 4 says "this pass edited **no** layer-1 text" and hand-off 5 says a layer-1-adjacent section was edited; the two read as inconsistent, but the second discloses the first, so nothing is concealed.

### Source files — confirmed untouched

`git status --short -- django_strawberry_framework/ tests/ examples/` → empty. `git diff --stat` over the same trees → empty. Both docstrings the widened authorization scopes — `django_strawberry_framework/exceptions.py::ConfigurationError` and `django_strawberry_framework/types/base.py::_format_unknown_fields_error` — are byte-identical to HEAD, so R3's Worker 2 still owns both edits and R2 pre-wrote neither. I re-read both while measuring L10 / L11 and made no edit; my own source carve-out was not exercised at any point in this review.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are unchanged. No spec authorization needed.

### CHANGELOG sanity

Not applicable; item did not modify `CHANGELOG.md`. `git status --short -- CHANGELOG.md` is empty.

### Documentation / release sanity

- No version string, shipped/planned status, or card ID moved. The spec still carries no version stamp; `pyproject.toml` and `docs/GLOSSARY.md` are untouched.
- `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3` all clean in `git status`. No sibling spec written; `spec-006` clean.
- Every link definition in both changed files points at an existing file (all 27 re-checked above).
- No obsolete "coming soon" / "planned" / old-version wording introduced by the three spec edits; none of them adds a time-indexed clause. `spec:22`'s "labeled as temporary where the surface is published" is a rule about labelling, not a label.
- No script-rendered doc regenerated by this item.

### Static helper use

`scripts/review_inspect.py` **skipped, deliberately.** None of its four Worker-3 triggers fires: this pass adds no `.py` file, touches no file under `optimizer/` or `types/`, and adds zero lines of logic — the diff is two Markdown files. Its repeated-string-literal output has no subject here; the duplication question is between two prose documents and was measured with the shingle intersection above.

### Failability proofs

**None owed and none re-run.** This item introduces no boundary, guard, gate, or rejection path; it edits two Markdown files. The mandatory re-run floor is satisfied by the empty set, which `worker-3.md` permits when the diff introduces no boundary meeting it. Boundaries re-run: none. Boundaries accepted on the builder's record: none — the report correctly records that none exists.

### Hot-path budget / Floor verification

Not applicable, and correctly recorded as such: the plan declares no hot path and floor-verification scope `none` build-wide, and this item changes no package source and reasons about no version-dependent behavior.

### Temp test verification

None created; `docs/builder/temp-tests/` stays empty. Every claim under review is a property of two Markdown files, of source read at HEAD, or of git history, and each was settled by direct measurement — a full-history replay of both constants, the `-S` counter-experiment, word counts off the HEAD spec, the anchor and link scans, and the checker runs quoted above. No promotion to the permanent suite is owed.

### What looks solid

- **The corrected numbers are right.** Every one of them re-derives independently: nine, seven-and-five, seven keys under six labels, five call sites, three owning specs, 245 against 112. The pass was asked to re-measure five figures and it re-measured them correctly, plus two it found itself.
- **The M2 sentence now carries its own population.** "The population is every historical definition of `DEFERRED_META_KEYS`, replayed over the file's whole history rather than sampled: the set has held only six keys ever (…)" is the right shape for a numeral inside an explanatory sentence — a later reader can re-derive it from the sentence instead of trusting it, which is what made my check a comparison rather than an investigation. Hand-off 3 states that rule explicitly and it is worth keeping.
- **L2 was closed by aligning the bullet rather than annotating the contradiction.** The finding offered a rationale note; taking the harder option removed a live contradiction instead of documenting one, and the replacement wording matches where the package actually publishes the label.
- **L4's fix caught a second defect in the same sentence pair** — the claim that enumerating the keys "would have been another roster to keep current" while `spec:56` enumerates them. That is the sweep working as intended rather than the finding being patched.
- **The `## Standing note` correction strengthened the paragraph instead of weakening it.** The argument was resting on a false premise about length; giving the real reason for the length difference (a shortlist of techniques against a table of required outcomes) is the same point better supported.
- **No collateral damage at all.** Seven anchors on seven unmoved lines, both checkers at exit 0, 27/27 links resolving, 9/9 anchors, duplication improved on the adversarial tokenizer, and the inbound `spec-006` title citation intact.

### Notes for Worker 1 (spec reconciliation)

1. **Routing.** This `revision-needed` returns to **Worker 1** per Deviation 2, not Worker 2. **The two durable files need no further edit** — every finding above is in `docs/builder/bld-005-r2-spec_reconciliation.md` (M4, M5, L9, L10) or in the build plan (L11, Worker 0's file). Do not reopen the spec or the rationale for any of them; the corrections would be wrong there, not right.
2. **M4 is the one that matters beyond this cycle**, which is exactly why it has to be corrected rather than softened. The dispatch asked me to judge the methodological claim on the grounds that if it holds it generalizes. It does not hold: `-S` over `DEFERRED_META_KEYS` returns 11 commits whose blobs contain all four definitions and the exact six-key union, so the prior review's prescribed method produced the right population by the route it named. Keep the hazard, drop the observation.
3. **The real trap in this area is `--follow`, not `-S`** — and this cycle demonstrated it (L9). `git show <c>:django_strawberry_framework/types/base.py` fails silently on the pre-rename revisions that `--follow` still lists, so a replay that does not fall back to the old path drops the oldest definitions without any error. That is the standing lesson worth carrying: **when replaying a file's history across a rename, resolve each blob at the path it had at that commit.** It is what turns 13 definitions into 12 and a six-key oldest into a five-key one.
4. **L10 and L11 must be reconciled before R3's Worker 2 is dispatched**, because they disagree with each other about the same helper and both are inputs to one docstring. The measured truth is: **five direct call sites, in three functions, passing six distinct `attr` values, covering seven `Meta` keys.** L11 is Worker 0's to fix (`build-005-…:249` says eight values); L10 is this artifact's.
5. **M5 is bookkeeping with one sharp edge.** Two of the three stale figures are harmless duplicates of L4's arithmetic, but `:270`'s "six of the twelve added keys" is the exact number M2 corrected, sitting in `### Spec changes made (Worker 1 only)` — the table the final gate walks row by row. A superseded-figure note there costs one line.
6. **No contract-level finding was raised, and I checked before deciding not to.** M4 and L9 are defects against measurement; M5 is an incomplete record; L10 and L11 are wrong counts. None turns on which contract the package should offer. The spec-004 competitive-positioning decision was not touched; pass 1 charged R2's ground on its own terms and I did not reopen it.
7. **L3 and M1 were judged, not deferred.** Both are recorded above as correct closes with the reasoning, so neither should be reopened by a later pass reading the finding text alone.
8. **Baseline unchanged.** No growth, nothing reverted, no `git checkout`. The four staged-deleted `docs/builder/bld-003-*.md` entries still await the maintainer. Re-derive `HEAD` rather than quoting `ff03c137`.

### Review outcome

`revision-needed` — two Medium (M4, M5) and three Low (L9, L10, L11), none carrying a recorded rejection. **All nine prior findings closed correctly and every corrected number is right**; the spec and the rationale need no further edit and should not be reopened. What remains open is the pass's own record of how it measured: a methodological claim that measures false and is being promoted as a standing rule, three figures of the corrected class left unmarked in the cumulative artifact, a call-site clause that would become a false docstring, and one plan figure that disagrees with all of them.

---

## Reconciliation report (Worker 1, pass 3)

Apply-changes pass for M4, M5, L9, L10 and L11. `HEAD` re-derived rather than quoted: `ff03c1372365edcad488ff4671389d88ae145276`, unmoved since the re-review closed. No `git stash` / `checkout` / `restore` / `worktree`, no branch, no commit, no `pytest`, no coverage-shaped flag, no write to source, tests, `examples/`, a sibling spec, the terms CSV, `CHANGELOG.md`, `KANBAN*`, `docs/GLOSSARY.md`, or the DB.

**Neither durable file was opened for writing this pass, and that is the pass's first decision rather than an omission.** Worker 3 states that the spec and the rationale need no further edit; I re-derived every figure the findings turn on before accepting that, and each one holds where it stands — the rationale's nine, its twelve-against-the-section's-five baseline, its seven-bullets-five-false, its seven keys under six `attr` labels, and `spec:56`'s enumeration. Every one of the five findings is a defect in **this artifact's own record of how it measured**, or in the plan. Reopening a correct document to fix a wrong record of it would be the larger defect, so the whole pass lands in this block.

Prior blocks are not rewritten. Where a superseded figure sits in a table the final gate walks, it is marked here in place of being edited (`### Corrections to this artifact's pass-1 and pass-2 records`).

### Disposition of every finding

| Finding | Disposition | What changed |
|---|---|---|
| **M4** | **Confirmed false, corrected — and the hazard is now demonstrated instead of asserted** | The claim is false as measured and I reproduced Worker 3's counter-experiment exactly: the 11 commits `-S'DEFERRED_META_KEYS'` returns carry **all four** distinct definitions and the exact six-key union. The observation "three of the four distinct definitions do not appear in its output" and the conclusion "the command it cites would not have established it" are both retracted below. I did **not** take Worker 3's recommended softening ("a hazard that did not bite here") — re-derivation found that it *does* bite in this repository, in the same file, on the sibling constant, so the standing rule survives with a measurement under it rather than a false anecdote. See `### M4 re-derived`. |
| **M5** | **Closed by marking; population established rather than the three instances patched** | Worker 3 named three. Sweeping the pass-1 record for the whole corrected class rather than for the reported hits returned **five**: the three named, plus drift row D19's "four owning specs added" (`:124`) — the same wrong figure whose `### Spec changes made` twin was already superseded at `:697` — and drift row D12's "with both real test names" (`:117`), whose `### Spec changes made` twin was already superseded at `:698`. Both misses are the *second copy* of a figure whose first copy was corrected, which is the exact shape M5 charges. All five are marked in `### Corrections to this artifact's pass-1 and pass-2 records`. |
| **L9** | **Confirmed, corrected, and the trap recorded as the standing lesson** | The oldest `ALLOWED_META_KEYS` definition is **six** keys including `interfaces`, at `084b4643`, which lives at the pre-rename path. "13 distinct definitions" and "a five-key oldest" cannot both be true, exactly as charged. Re-derived below with the `git show` behaviour that produces the error, and with the confirmation that M2's nine is unaffected under either baseline. |
| **L10** | **Closed by restating hand-off 1 exactly** | The clause is false under its grammatical antecedent, as charged: exactly **one** of the five direct call sites is inside `_selected_meta_targets`; what routes through it is three of the six `attr` **labels**. Hand-off 1 is restated in full below with every figure measured at HEAD and the call sites and label sources enumerated, so Worker 2 writes the docstring off the enumeration rather than off a count. |
| **L11** | **Verified against source and against Worker 0's correction; no disagreement remains** | Worker 0 has already corrected the plan to "five direct call sites carrying six distinct `attr` labels" and listed them. I measured the same six independently (`exclude`, `fields`, `filesystem_path_fields`, `nullable_overrides/required_overrides`, `optimizer_hints`, `relation_shapes`) and they match the plan's list member for member. The restated hand-off 1 below uses that figure verbatim, so the plan and the hand-off — the two inputs to one docstring — now agree. Nothing further is owed to Worker 0. |

### M4 re-derived

The claim under `### The measurement sweep` (`:638`) and hand-off 2 (`:712`) is that `git log -S` over an identifier cannot establish a constant's historical membership, evidenced by "three of the four distinct definitions do not appear in its output".

**Measured, that evidence is false.** `git log --format=%h -S'DEFERRED_META_KEYS' -- django_strawberry_framework/types/base.py` returns 11 commits. Parsing the balanced `frozenset(...)` literal out of `git show <c>:django_strawberry_framework/types/base.py` for each of the 11:

| blob | `DEFERRED_META_KEYS` |
|---|---|
| `f5d03652`, `27d62919`, `b14232fa` | `aggregate_class` `fields_class` `filterset_class` `interfaces` `orderset_class` `search_fields` |
| `70c7bff2`, `e836d72e`, `7e6a7fc4` | `aggregate_class` `fields_class` `filterset_class` `orderset_class` `search_fields` |
| `1694bd2e`, `a4bd4c73` | `aggregate_class` `fields_class` `orderset_class` `search_fields` |
| `11d9fbe0`, `23cb569a`, `46ffc64f` | `aggregate_class` `fields_class` `search_fields` |

All four distinct value-sets, union exactly the six keys, identical to the full-history replay. **Zero missing, not three.** Worker 3's re-derivation reproduces, and the prior review's prescribed method produced the right population by the route it named. Both sentences are retracted.

**Why it fired, which is the part that decides whether the rule survives.** `-S` is a pickaxe on the *occurrence count* of the string, so it can only see a membership change that happens to ride with a change in how often the identifier is written. It did here, in all four transitions — occurrences of `DEFERRED_META_KEYS` in the file went `6 → 8` at `f5d03652` and `6 → 5` at each of `e836d72e`, `1694bd2e`, `11d9fbe0`, because every one of those commits also edited a docstring line naming the constant. `e836d72e` is the legible instance: alongside dropping `interfaces` from the set it deleted the docstring line `` ``"interfaces"`` remains in ``DEFERRED_META_KEYS``, so this step ``. The pickaxe fired on the docstring, not on the set.

**The hazard is real and this repository demonstrates it — on the sibling constant, in the same file.** `git log --format=%h -S'ALLOWED_META_KEYS' -- django_strawberry_framework/types/base.py` returns 14 commits; replaying their blobs recovers **9 of the 13** distinct definitions, and the union over everything it recovers is **15 keys, not the 17 the set holds at HEAD** — `cursor_field` and `filesystem_path_fields` never appear in any blob `-S` returns. The commits it misses are exactly the membership changes that moved no occurrence count: `dae186a1` (4 occurrences before and after), `8cac3495`, `7d892d6f`, `d418e649` (3 / 3), `51421e54` (4 / 4), `567cc6d0` (4 / 4). Anyone who had asked "did `filesystem_path_fields` ever sit in `ALLOWED_META_KEYS` before now?" off the `-S` list would have gotten the wrong answer from a command that returned 14 commits and looked exhaustive.

**So the standing rule is kept and its evidence is replaced.** Superseding hand-off 2 (`:712`) in full, the corrected form is:

> **`git log -S<identifier>` is a search for changes in how often a name is written, not for changes in the value it names.** A key added to or removed from a `frozenset` literal moves no occurrence count, so `-S` sees such a commit only when something else in the same commit also moves the count — a docstring, a comment, another reference. Whether that happens is incidental to the question being asked: on `DEFERRED_META_KEYS` it happened in every transition and `-S` recovered the complete population; on `ALLOWED_META_KEYS` in the same file it did not, and `-S` recovers 9 of 13 definitions and 15 of 17 keys while returning 14 commits. **To establish what values a constant has ever held, replay the definition over every revision of the file** — `git log --follow` for the revision list, `git show <commit>:<path>` per revision, parse the assignment — and resolve each blob at **the path the file had at that commit** (L9). `-S` remains a sound way to *locate* the files that ever contained an identifier, because a file that ever held it took its count from zero at some commit.

### L9 re-derived

`git log --follow -- django_strawberry_framework/types/base.py` lists **77** revisions. Two of them, `77b8fe7f` and `084b4643`, predate the `types.py` → `types/base.py` split and do not resolve at the modern path: `git cat-file -e <c>:django_strawberry_framework/types/base.py` fails for both, and `git show` on the same pathspec exits `128` writing only to stderr. **A replay loop that reads stdout and skips empty results therefore drops those revisions without raising anything** — that is the mechanism behind the wrong figure, and it is the trap worth carrying.

Replaying all 77 with a fallback to `django_strawberry_framework/types.py`:

- `ALLOWED_META_KEYS` — **13** distinct definitions. Oldest is `084b4643` at the pre-rename path and holds **six** keys: `description`, `exclude`, `fields`, **`interfaces`**, `model`, `name`. The five-key set (`description` / `exclude` / `fields` / `model` / `name`) is the *second* definition, `f5d03652`, which is where `interfaces` was moved out. Newest is 17.
- Drop the fallback and the same replay yields **12** definitions and a five-key oldest. So "13 distinct definitions, oldest = five keys" is not a slip in one number; it is two numbers from two different populations in one sentence. Corrected: **13 definitions with the pre-rename revisions resolved, oldest six keys including `interfaces`.**
- This is the other side of `### The measurement sweep` row 2, which the same block verified correctly (`interfaces` in `ALLOWED` pre-`0.0.3`, in `DEFERRED` at `0.0.3`-`0.0.4`, in `ALLOWED` since). The row was right; the paragraph twelve lines below it was wrong about the same fact.

**M2's nine is unaffected, under either baseline** — checked because a corrected denominator is exactly where a downstream figure breaks silently. Against the true six-key oldest: 17 − 6 = 11 added, of which `filterset_class` and `orderset_class` were ever deferred → **9**. Against the spec section's own roster of five, which is the baseline the rationale actually names in the same paragraph ("The section listed five accepted keys … twelve keys were added"): 12 added, of which `interfaces`, `filterset_class` and `orderset_class` were ever deferred → **9**. No durable file is touched.

### Hand-off 1, restated exactly — supersedes pass 2's hand-off 1 (`:711`)

This is the specification for the `django_strawberry_framework/types/base.py::_format_unknown_fields_error` docstring that R3's Worker 2 writes. Every figure below was measured at HEAD by parsing the module's AST for the call expressions and their enclosing functions, then reading each `attr=` argument; nothing is read off `spec:56` or off the plan. **Worker 2 should write from the enumeration, not from the counts.**

**Five direct call sites, in three functions:**

| call site | enclosing function | `attr` label passed |
|---|---|---|
| `django_strawberry_framework/types/base.py:1270` | `::_validate_optimizer_hints` | `"optimizer_hints"` (`:1272`) |
| `:1280` | `::_validate_optimizer_hints` | `"optimizer_hints"` (`:1282`) |
| `:1324` | `::_selected_meta_targets` | `attr=attr` (`:1326`) — forwarded, not a literal |
| `:1612` | `::_select_fields` | `"fields"` (`:1614`) |
| `:1624` | `::_select_fields` | `"exclude"` (`:1626`) |

**Six distinct `attr` labels, covering seven `Meta` keys:** `exclude`, `fields`, `filesystem_path_fields`, `nullable_overrides/required_overrides` (one label, two keys), `optimizer_hints`, `relation_shapes`. This is member-for-member the list Worker 0 wrote into `### THE ONE SOURCE EDIT THIS CYCLE AUTHORIZES` when correcting L11, so the plan and this hand-off agree.

**Three of the six labels arrive indirectly**, through the single forwarding call at `:1324`, each supplied by its own validator: `nullable_overrides/required_overrides` from `::_validate_nullability_override_targets` (`:1396`), `filesystem_path_fields` from `::_validate_filesystem_path_targets` (`:1471`), `relation_shapes` from `::_validate_relation_shape_targets` (`:1536`). **Exactly one of the five direct call sites is inside `_selected_meta_targets`** — the retracted phrasing "five direct call sites, three of them via `_selected_meta_targets`" attached the three to the wrong noun.

The docstring's live defect is unchanged by any of this: it names `fields`, `exclude` and `optimizer_hints` as its complete caller set and omits the three indirect families. Nothing in `docs/SPECS/spec-005-django_type_contract-0_0_3.md` or its rationale is falsified by correcting it — re-confirmed this pass, neither file quotes or characterizes either authorized docstring, and `spec:56` is the sentence the corrected docstring should be made to agree with.

### Corrections to this artifact's pass-1 and pass-2 records

Recorded here rather than by editing the prior blocks, which stand as written. The first two supersede pass-2 text; the remaining five are pass-1 figures of the class pass 2 corrected, and complete the population that pass 2's own `### Corrections to this artifact's own pass-1 record` started.

- **`:638` and `:712` (pass 2), the `-S` method claim.** "Three of the four distinct definitions do not appear in its output" and "the command it cites would not have established it" are **false as measured** and are retracted; hand-off 2's standing-rule wording is superseded by the block quoted under `### M4 re-derived`. The recommendation to replay the definition over `git log --follow` stands, now with its real justification.
- **`:638` (pass 2), the `ALLOWED_META_KEYS` replay.** "13 distinct definitions, oldest `= {description, exclude, fields, model, name}`" is **internally inconsistent**: 13 requires resolving the two pre-rename revisions, and doing so makes the oldest **six** keys including `interfaces`. Corrected under `### L9 re-derived`. The `9 net-new` conclusion in the same sentence is unaffected and was re-verified against both baselines.
- **`:270` (pass 1), `### Spec changes made (Worker 1 only)` row `spec:73`:** "six of the twelve added keys arrived that way" is **nine**. This is the figure M2 corrected in the rationale; the row is the per-line change record the final gate walks, so the corrected number and the uncorrected one were sitting one table apart. Superseded.
- **`:121` (pass 1), drift row D16:** "`_format_unknown_fields_error` has five call sites reaching six keys" is **seven keys under six `attr` labels**. Superseded.
- **`:135` (pass 1), `### The read-only correctness audit, re-verified`:** "reached by five call sites covering six keys" followed by an enumeration of **seven**. The enumeration is right and the numeral is wrong: seven keys, six `attr` labels, five direct call sites. Superseded.
- **`:124` (pass 1), drift row D19** — *not reported by either review; found by sweeping the class rather than the reported instances.* "four owning specs added" is **three** (`spec-018`, `spec-010`, `spec-019`, in two bullets). Pass 2 superseded the identical figure in the `### Spec changes made` row at `:274` and did not carry the correction back to the drift row that fed it. Superseded.
- **`:117` (pass 1), drift row D12** — *likewise unreported.* "the third route into `ALLOWED_META_KEYS` added to the section, with both real test names" over-states what landed: `spec:75` names one (`::test_interfaces_is_shipped_not_deferred`), and the second name lives in the rationale, correctly. Pass 2 superseded the identical over-statement in the `### Spec changes made` row at `:271` and, again, not the drift row. Superseded; no spec edit is owed, since the spec is right to name one test in a paragraph about `Meta.interfaces`.

**The pattern in the last two is worth naming rather than just fixing:** pass 2 corrected each figure where it appeared in the table it was reading and left the drift row it had been copied *from*. A figure that appears twice in one artifact needs both copies marked, and the reliable way to find the second copy is to grep the whole file for the claim, not to correct the row in front of you.

### Files touched

- `docs/builder/bld-005-r2-spec_reconciliation.md` — the `Status:` line and this appended block. No prior block edited.
- `docs/SPECS/spec-005-django_type_contract-0_0_3.md` and `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md` — **not opened for writing.** Confirmed by byte count below: both are identical to their pass-2 state.

### Byte count

| | lines | bytes |
|---|---|---|
| spec at HEAD (pre-cycle) | 154 | 13,346 |
| spec after R2 pass 2 | 122 | 13,373 |
| **spec after R2 pass 3** | **122** | **13,373** |
| rationale after R2 pass 2 | 713 | 51,373 |
| **rationale after R2 pass 3** | **713** | **51,373** |

Both durable files are byte-identical to pass 2, and `git diff --stat` over the spec is unchanged at `45 insertions(+), 77 deletions(-)`. That is the mechanical evidence for "no durable file was edited", not a claim about intent.

### Validation run

Re-run in this pass on all three files even though only the artifact changed, so the close-of-item state is recorded rather than inherited.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-005-django_type_contract-0_0_3.md` → `OK: 7 terms - all have glossary entries and at least one spec link.` **exit 0**. Character-identical to the pre-flight baseline and to every prior quotation in this artifact.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-005-django_type_contract-0_0_3.md docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md docs/builder/bld-005-r2-spec_reconciliation.md` → **exit 0** on all three, this artifact included after the append.
- `git status --short` unchanged in shape: the five spec-004-cycle entries, the four staged-deleted `docs/builder/bld-003-*.md`, and this cycle's five (`M spec-005`, `?? rationale`, `?? bld-005-r1`, `?? bld-005-r2`, `?? build-005`). `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3` all clean. Nothing reverted (`AGENTS.md` rule 34).
- `git status --short -- django_strawberry_framework/ tests/ examples/` → **empty**. Both docstrings the widened authorization scopes remain R3's Worker 2's to write; this pass read them and wrote neither.
- **Not swept into a concurrent commit.** `git log --oneline -1` over the spec tops out at `ff65666d`, which predates the cycle; `git log` over the rationale, both `bld-005-*` artifacts and the plan is empty. `git status` alone was not used for this determination.
- No `pytest`, no `ruff` (no `.py` touched), no coverage-shaped flag.
- **Duplication and line-granularity checks not re-run, deliberately.** Both measure the two durable files against each other and against HEAD; both files are byte-identical to the state Worker 3 re-derived one pass ago (0 at n=8 under both named tokenizers; 65 removed non-empty lines, 45/45 accounted). Re-running a measurement over unchanged bytes would record a number, not verify one. Stated rather than silently skipped.

### The 7-anchor constraint

Unchanged and unchallenged: no durable file was edited, so all seven anchors remain at exactly 1 reference-style body use + 1 definition on the same seven carrier lines Worker 3 confirmed independently in both review passes — `djangotype` `spec:7`, `metafields` and `metaexclude` `spec:11`, `metaprimary` `spec:34`, `configurationerror` and `metamodel` `spec:52`, `metainterfaces` `spec:75`. `check_spec_glossary.py` passing at exit 0 above is the mechanical confirmation. The terms CSV was not opened. `docs/SPECS/spec-006-public_surface-0_0_3.md:108`'s by-title citation is untouched and `spec-006` is clean in `git status`.

### Hot-path budget / Floor verification / Failability proofs

Not applicable, unchanged from passes 1 and 2 and for the same reasons: the plan declares no hot path and floor-verification scope `none` build-wide, and this pass edits one Markdown artifact, introducing no boundary, guard, or rejection path. Nothing is owed.

### Notes for Worker 1 (spec reconciliation)

Hand-offs to R3 and the final gate.

1. **Read hand-off 1 from `### Hand-off 1, restated exactly` above, not from pass 2's `:711`.** The pass-2 wording is superseded. The restated version carries the call sites, their enclosing functions and each label's source as a table, so Worker 2 can write the docstring without re-deriving anything — and should write from the enumeration rather than from "five" and "six", since every defect this item found was a numeral standing in for a population.
2. **The plan and hand-off 1 agree, and this is the last pass that could have made them disagree.** Worker 0's L11 correction (`five direct call sites carrying six distinct attr labels`, with the six listed) was verified against source here, member for member. Worker 2 is dispatched against two documents that now say the same thing about the same helper.
3. **The corrected standing rule about `git log -S` is the block quoted under `### M4 re-derived`, and it is the only version that should leave this cycle.** Its evidence is a measurement on `ALLOWED_META_KEYS` in this repository, not the retracted observation about `DEFERRED_META_KEYS`. If it is carried anywhere durable, carry the measurement with it — the rule's whole claim is that the hazard is invisible when it bites, so a rule asserted without a demonstrated instance is the thing it warns against.
4. **The `--follow` rename trap (L9) is the more dangerous of the two and belongs beside it.** `git show <commit>:<new/path>` on a pre-rename revision exits `128` with output on stderr only, so a replay loop that reads stdout drops the oldest revisions and reports a clean number. It is what turned 13 definitions into a five-key oldest here. Resolve each blob at the path the file had at that commit.
5. **M5's remedy was marking, and the marking found two instances neither review reported.** Both were second copies of a figure whose first copy pass 2 had already corrected. For the final gate: `### Drift-row disposition` rows D12, D16, D19 and `### Spec changes made (Worker 1 only)` rows `spec:73`, `spec:75`, `spec:87-92` all carry superseded figures, every one marked in `### Corrections to this artifact's pass-1 and pass-2 records`. No unmarked figure of the corrected class remains in this artifact.
6. **Neither durable file needs a further pass, and the byte counts are the evidence.** Spec `122 / 13,373` and rationale `713 / 51,373`, identical to pass 2. Worker 3's instruction not to reopen them was verified rather than accepted: every figure the five findings turn on was re-derived, and each holds where it stands.
7. **No contract-level question arose and none was escalated.** All five findings are defects against measurement or against a record. The spec-004 competitive-positioning decision was not touched; M1 and L3 were not reopened.
8. **Baseline unchanged.** No growth, nothing reverted, no `git checkout`. The four staged-deleted `docs/builder/bld-003-*.md` entries still await the maintainer. Re-derive `HEAD` rather than quoting `ff03c137`.

### Review outcome

Not applicable — this is the Worker 1 apply-changes pass. `Status: planned` on return, which Worker 0 reads as "dispatch Worker 3" per Deviation 2. All five findings are closed; none is rejected and none is deferred. One recommended remedy was deliberately not taken (M4's softening to "a hazard that did not bite here"), because re-derivation showed the hazard does bite in this repository and the rule is better served by the measurement than by the retreat. Two further stale figures of the corrected class were found by sweeping for the class and are marked with the three reported.

---

## Review (Worker 3, pass 3)

Re-review of the second apply-changes pass. `HEAD` re-derived, not quoted: `ff03c1372365edcad488ff4671389d88ae145276` — unmoved. `git log --oneline -1 -- docs/SPECS/spec-005-django_type_contract-0_0_3.md` still tops out at `ff65666d`, which predates the cycle; `git log` over the rationale, both `bld-005-*` artifacts and the plan is empty, so nothing this cycle wrote has been swept into a concurrent commit. `git status` alone was not used for that determination. Baseline dirty is unchanged in shape and content: the five spec-004-cycle entries (`M docs/SPECS/spec-004-…`, `?? …spec-004-…-rationale.md`, `?? bld-004-r1`, `?? bld-004-r2`, `?? build-004`), the four deleted `docs/builder/bld-003-*.md`, and this cycle's five. Nothing reverted, no `git checkout`, no growth.

Read-only HEAD copies taken with `git show HEAD:… > <scratchpad outside the repo>`. No `git stash` / `checkout` / `restore` / `worktree`, no branch, no commit, no source or test edit, no `pytest`, no coverage-shaped flag.

Per the dispatch this pass does **not** reopen the spec or the rationale, whose content two prior passes settled. It verifies the non-modification claim, then reviews the four closures (M4, L9, L10, M5) and the escalation (L11).

**Non-modification verified mechanically, not accepted on prose.** Spec `122 lines / 13,373 bytes`, rationale `713 / 51,373` — byte-for-byte the pass-2 figures. `git diff --stat -- <spec>` is unchanged at `45 insertions(+), 77 deletions(-)`. The duplication and line-granularity measurements were therefore **not** re-run, deliberately and for the reason pass 3 gives: both compare bytes I re-derived one pass ago and which have not moved. Re-measuring unchanged bytes records a number rather than verifying one.

### High:

None.

### Medium:

#### M6 — L9's correction is right, but the sub-claim it rests on measures false, and that sub-claim is the demonstration under a standing lesson the cycle intends to carry out

`docs/builder/bld-005-r2-spec_reconciliation.md:989`, `:994` and `:1077` (hand-off 4)

```docs/builder/bld-005-r2-spec_reconciliation.md:994
- Drop the fallback and the same replay yields **12** definitions and a five-key oldest. So
  "13 distinct definitions, oldest = five keys" is not a slip in one number; it is two numbers from
  two different populations in one sentence.
```

Re-derived, one leg at a time. What holds:

- `git log --follow -- django_strawberry_framework/types/base.py` lists **77** revisions. **Holds.**
- `77b8fe7f` and `084b4643` are the two that do not resolve at the modern path. **Holds** — they are exactly the two my no-fallback replay could not read.
- `git show 084b4643:django_strawberry_framework/types/base.py` exits **128** with **0 bytes on stdout** and its message on stderr, so a stdout-reading loop drops the revision silently. **Holds.**
- Oldest `ALLOWED_META_KEYS` is `084b4643` at the pre-rename path and holds **six** keys — `description`, `exclude`, `fields`, **`interfaces`**, `model`, `name`. **Holds**, read raw out of `git show 084b4643:django_strawberry_framework/types.py`.
- 13 distinct definitions with the rename resolved. **Holds.**

What does not:

| replay | distinct value-sets | distinct literal text | oldest resolvable revision | oldest set |
|---|---|---|---|---|
| 77 revisions, pre-rename path resolved | **13** | 16 | `084b4643` @ `types.py` | **6 keys, incl. `interfaces`** |
| same 77, stdout-only (2 blobs unreadable) | **13** | 16 | `70c7bff2` @ `types/base.py` | **6 keys, incl. `interfaces`** |

Dropping the fallback yields **13, not 12**, and a **six-key**, not five-key, oldest. The reason is mechanical and checkable in one command: the first two post-rename revisions carry the same six-key set as the pre-rename ones — `git show 70c7bff2:django_strawberry_framework/types/base.py` and `git show 2893ccb8:…` both give `{model, fields, exclude, name, description, interfaces}` — so the two unreadable blobs contribute **no distinct definition of their own**. The five-key set (`f5d03652`, "Start specs for 0.0.3") is the *third* state under either replay, never the oldest.

So three sentences fall together: "12 definitions", "a five-key oldest", and the diagnosis "two numbers from two different populations in one sentence" — both of pass 2's numbers come from the same population, and the five-key oldest comes from neither. `:989`'s "that is the mechanism behind the wrong figure" and hand-off 4's "**It is what turned 13 definitions into a five-key oldest here**" are the same claim, and it is not established: the trap this pass demonstrates cannot produce that error. The real cause of pass 2's five-key oldest is not identified by the record, and "12" itself has the shape of an inference (13 − 1) rather than a measurement, which is the class this item has now charged five times.

Why this is Medium and not bookkeeping: hand-off 4 promotes the rename trap as "the more dangerous of the two [standing lessons]" and hand-off 3 instructs that if a lesson is carried anywhere durable the measurement is carried with it. This is the M4 situation exactly one pass later, with the polarity reversed — there the pass **refused** Worker 3's softening and replaced a false anecdote with a real measurement on `ALLOWED_META_KEYS`, and it was right to. The same standard applied here retires a false instance under a true rule.

Recommended change (no durable file is affected and none should be touched): keep the rule and the two legs that hold — the `128`/stderr-only behaviour and "resolve each blob at the path the file had at that commit" — retract "12 definitions", "a five-key oldest", the two-populations diagnosis and hand-off 4's causal clause, and replace them with the measurement above. The corrected instance is *stronger* than the retracted one, for the same reason M4's replacement was: here the stdout-only replay loses two revisions and **its summary numbers do not move at all** (13 and a six-key oldest either way), which is a sharper illustration of a silent failure than a number that visibly changes. If the cause of pass 2's five-key figure is wanted in the record, say it is unestablished rather than attributing it.

### Low:

#### L12 — a sixth figure of the corrected class survives unmarked, in the same table as the five, and the pass records the class as empty

`docs/builder/bld-005-r2-spec_reconciliation.md:267` — `### Spec changes made (Worker 1 only)`, row `spec:56`:

```docs/builder/bld-005-r2-spec_reconciliation.md:267
| spec:56 | New paragraph: the error shape is owned by `_format_unknown_fields_error` and inherited
by five further keys | the section claimed the contract for two keys; the package honours it for six
| D16 |
```

This is the sentence pair L4 charged and the pass corrected, in the rationale, to `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md:516`: "the section claimed the error shape as public contract for two keys; **the package honours that claim for seven**. The unit is keys: the raise sites carry six distinct `attr` labels rather than seven". The artifact's copy still reads "for two keys … honours it for six" — the mixed-unit form, in the per-line change table the final gate walks, one row above `:270`, which the same pass marked.

The five marked instances are each real and each verified here: `:270` ("six of the twelve added keys" → nine), `:121` (D16, "five call sites reaching six keys" → seven keys under six labels), `:135` (numeral six beside an enumeration of seven), `:124` (D19, "four owning specs" → three), `:117` (D12, "both real test names" → one). The sweep that found the last two by establishing the class rather than chasing the reported hits was the right method, and it is one row short of complete: hand-off 5 states "**No unmarked figure of the corrected class remains in this artifact**", which is what makes this worth a line rather than a shrug — a completeness claim is what stops the next reader looking.

Recommended change: a sixth bullet under `### Corrections to this artifact's pass-1 and pass-2 records` in the same form, and re-wording hand-off 5 to name six rows. Low because the row's own left-hand cell ("inherited by **five further keys**") lets a reader derive seven in place, and no durable file is affected.

### DRY findings

None to charge. Neither durable file was opened, so the spec-versus-rationale split is byte-identical to the state I re-derived at pass 2 (0 non-scaffold 8-word overlap under both named tokenizers); re-measuring unchanged bytes would not be a verification. No abstraction was created or extended this pass — the pass added one Markdown block to an artifact.

**Existence challenge:** raised and answered without a finding, and it is the same answer as pass 2. The one abstraction in play is the cumulative-artifact convention of superseding prior blocks rather than editing them, and it earns its existence for the reason the pass gives — prior blocks are the record of what a pass believed when it acted, and editing them destroys the only evidence of that. L12 is a cost of that convention, not an argument against it.

### The four closures, verified

**M4 — the sibling-constant experiment reproduces exactly, and it is now the sole support for the standing rule, so it was re-derived rather than compared.**

| claim (`:981`) | measured |
|---|---|
| `git log -S'ALLOWED_META_KEYS' -- …/types/base.py` returns 14 commits | **14** |
| replaying those blobs recovers 9 of the 13 distinct definitions | **9 of 13** |
| their union is 15 keys, not the 17 at HEAD | **15** |
| `cursor_field` and `filesystem_path_fields` appear in no blob `-S` returns | **confirmed** — they are exactly the two keys in `ALLOWED_META_KEYS` at HEAD absent from the `-S` union |
| the missed commits moved no occurrence count | **confirmed**: `dae186a1` 4→4, `8cac3495` 3→3, `7d892d6f` 3→3, `d418e649` 3→3, `51421e54` 4→4, `567cc6d0` 4→4 (each counted in the commit's blob and in its parent's) |

The rule therefore stands on a measurement in this repository, in the same file, on the sibling constant, and does not need the retracted `DEFERRED_META_KEYS` anecdote. The retraction itself also re-derives: `-S'DEFERRED_META_KEYS'` returns **11** commits whose blobs carry **all four** distinct value-sets and the exact six-key union — zero missing, as the pass says. So does the "why it fired" mechanism: the transitions moved the occurrence count (`f5d03652` 6→8; `e836d72e`, `1694bd2e`, `11d9fbe0` each 6→5), and `git show e836d72e -- …/types/base.py` does delete the docstring line `` "interfaces" remains in ``DEFERRED_META_KEYS``, so this step `` that moved it. **Accepted; the standing rule survives with real evidence under it.**

**L9 — the load-bearing half holds.** M2's nine survives under both baselines, re-derived from my own full replay rather than from the arithmetic in the artifact:

- ever-deferred union = `{aggregate_class, fields_class, filterset_class, interfaces, orderset_class, search_fields}`; `ALLOWED_META_KEYS` at HEAD = 17.
- against the true six-key oldest: 17 − 6 = **11** added, of which `filterset_class` and `orderset_class` were ever deferred → **9**.
- against the spec section's roster of five (the baseline the rationale names in the same paragraph): **12** added, of which `interfaces`, `filterset_class`, `orderset_class` were ever deferred → **9**.
- the nine are `connection`, `cursor_field`, `filesystem_path_fields`, `globalid_strategy`, `nullable_overrides`, `optimizer_hints`, `primary`, `relation_shapes`, `required_overrides` — none of which appears in any historical `DEFERRED_META_KEYS` definition across all 77 revisions.

The correction to the oldest set also holds. What does not is the sub-claim about what the un-resolved replay yields — M6.

**L10 — hand-off 1's restatement is right member for member, measured from the module AST at HEAD.** This is the figure that becomes shipped source, so nothing here is compared; everything is parsed.

| call site | enclosing function | `attr` |
|---|---|---|
| `django_strawberry_framework/types/base.py:1270` | `::_validate_optimizer_hints` | `"optimizer_hints"` (`:1272`) |
| `:1280` | `::_validate_optimizer_hints` | `"optimizer_hints"` (`:1282`) |
| `:1324` | `::_selected_meta_targets` | `attr=attr` (`:1326`), forwarded |
| `:1612` | `::_select_fields` | `"fields"` (`:1614`) |
| `:1624` | `::_select_fields` | `"exclude"` (`:1626`) |

**Five** direct call sites in **three** functions; **exactly one** inside `_selected_meta_targets`; **six** distinct `attr` labels (`exclude`, `fields`, `filesystem_path_fields`, `nullable_overrides/required_overrides`, `optimizer_hints`, `relation_shapes`) covering **seven** `Meta` keys; and **three of the six labels** arrive through the single forwarding site, supplied by `::_validate_nullability_override_targets` (call `:1393`, `attr` `:1396`), `::_validate_filesystem_path_targets` (`:1468` / `:1471`) and `::_validate_relation_shape_targets` (`:1533` / `:1536`). Every figure and every line number in `### Hand-off 1, restated exactly` matches. The instruction to write the docstring from the enumeration rather than from the counts is the right shape for the one edit this cycle authorizes into source. **Accepted.**

**L11 — the plan and the hand-off now agree, verified against both.** `docs/builder/build-005-django_type_contract-0_0_3.md` `### THE ONE SOURCE EDIT THIS CYCLE AUTHORIZES` now reads "**five direct call sites carrying six distinct `attr` labels**", marks the retracted "eight distinct `attr` values" in place with its cause, and lists the six labels. That list is member-for-member the six I measured. Worker 2 is dispatched against two documents that say the same thing. The plan was read only and is untouched in `git status`. **Accepted.**

**M5 — five marked, correctly; one survives.** See L12. The three the prior review named are marked, the two the pass found itself by establishing the class are real, and the marking form (supersede in the newest block, never edit a prior one) is right.

### Scope gates — confirmed

- `git status --short -- django_strawberry_framework/ tests/ examples/` → **empty**. `git diff --stat` over the same trees → empty.
- Both authorized docstrings' files are **byte-identical to HEAD**, proven by `git show HEAD:<path>` into the scratchpad and `diff`: `django_strawberry_framework/exceptions.py` identical, `django_strawberry_framework/types/base.py` identical. R3's Worker 2 still owns both edits; neither was pre-written. I read both while measuring L10 and made no edit — my source carve-out was not exercised at any point in this review.
- Baseline-dirty entries: the five spec-004-cycle files and the four deleted `docs/builder/bld-003-*.md` are present and unmodified; nothing reverted, no `git checkout` (`AGENTS.md` rule 34).
- `docs/SPECS/spec-005-…md` and its rationale not opened for writing this pass, proven by byte count and diffstat above.

### Format and link integrity

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-005-django_type_contract-0_0_3.md` →

  ```text
  OK: 7 terms - all have glossary entries and at least one spec link.
  ```

  exit **0**, character-identical to every prior quotation in this artifact and to the pre-flight baseline.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-005-django_type_contract-0_0_3.md docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md docs/builder/bld-005-r2-spec_reconciliation.md` → exit **0** on all three, this artifact included after my append.
- The seven glossary anchors are unchallenged this pass: no durable file was edited, and the checker passing is the mechanical confirmation.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty** (0 bytes). `__all__` and the re-export list are unchanged. No spec authorization needed.

### CHANGELOG sanity

Not applicable; item did not modify `CHANGELOG.md`. `git status --short -- CHANGELOG.md` is empty.

### Documentation / release sanity

The pass edited one per-cycle artifact and no durable doc, so most of the checklist has no subject; what applies was checked.

- No version string, shipped/planned status, or card ID moved anywhere: the spec, `pyproject.toml`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html` and `examples/fakeshop/db.sqlite3` are all clean in `git status`.
- No sibling spec written; `docs/SPECS/spec-006-public_surface-0_0_3.md` clean, so its by-title citation of `### Accepted vs deferred Meta keys` is intact by construction.
- No markdown link introduced this pass; the artifact's `<!-- LINK DEFINITIONS -->` block carries all 10 canonical group headers in order and is unchanged.
- No script-rendered doc regenerated.

### What looks solid

- **Declining the recommended softening of M4 was the right call, and the pass proved it rather than argued it.** The recommendation was to state the `-S` hazard as one that did not bite here; the pass went and found an instance where it does bite, in the same file, on the sibling constant, and put a measurement under the rule instead of a retreat. Every figure of that measurement re-derives — 14 commits, 9 of 13 definitions, 15 of 17 keys, and the two keys that vanish are named. That is the strongest single thing in this artifact.
- **Establishing the population instead of patching the reported instances** on M5, which is what found `:124` and `:117`. The stated pattern — "the reliable way to find the second copy is to grep the whole file for the claim, not to correct the row in front of you" — is the correct generalization, and L12 is a one-row shortfall in executing it, not a disagreement with it.
- **Hand-off 1 restated as an enumeration with call sites, enclosing functions and label sources**, so the docstring Worker 2 writes is transcribed rather than re-derived. Given that every defect this item found was a numeral standing in for a population, handing the population forward instead of the numeral is the fix applied to the process rather than to the sentence.
- **Refusing to reopen two correct documents.** The byte counts are offered as the evidence for "not opened", not a claim about intent, and they reproduce exactly. A pass whose findings are all about a record correctly confined itself to the record.
- **Verifying Worker 0's L11 correction against source rather than accepting the agreement.** Two documents agreeing is not two documents being right.

### Temp test verification

None created; `docs/builder/temp-tests/` stays empty. Every claim under review is a property of git history, of the module AST at HEAD, or of one Markdown artifact, and each was settled by direct measurement — a full 77-revision replay of both constants at both paths, the `-S` replay on both constants, occurrence counts across six commit/parent pairs, an AST walk of `types/base.py`, byte-identity diffs against HEAD, and the two checkers quoted above. A temp test could not have said anything those did not. No promotion to the permanent suite is owed.

### Static helper use

`scripts/review_inspect.py` **skipped, deliberately.** None of its four Worker-3 triggers fires: the pass adds no `.py` file, touches no file under `optimizer/` or `types/`, and adds zero lines of logic — the diff is one Markdown artifact. Its repeated-literal output has no subject here.

### Failability proofs

**None owed and none re-run.** The pass introduces no boundary, guard, gate, or rejection path; it appends to a Markdown artifact. `worker-3.md`'s mandatory re-run floor is satisfied by the empty set, which it permits when the diff introduces no boundary meeting it. Boundaries re-run: none. Boundaries accepted on the builder's record: none — the report correctly records that none exists.

### Hot-path budget / Floor verification

Not applicable, and correctly recorded as such: the plan declares no hot path and floor-verification scope `none` build-wide, and this pass changes no package source and reasons about no version-dependent behavior.

### Notes for Worker 1 (spec reconciliation)

1. **Routing.** This `revision-needed` returns to **Worker 1** per Deviation 2. **Neither durable file needs an edit and neither should be opened** — I verified the non-modification claim and re-derived every figure the two findings turn on. Both findings are in `docs/builder/bld-005-r2-spec_reconciliation.md`; the plan needs nothing further (L11 is closed and verified).
2. **M6's remedy is a replacement, not a retreat** — the same shape the pass itself chose for M4. The corrected instance is available above and measures: with the pre-rename path resolved, 13 distinct definitions and a six-key oldest; stdout-only, **also** 13 and **also** a six-key oldest, because `70c7bff2` and `2893ccb8` carry the same six-key set at the modern path. The trap is real and silent; what it does *not* do is move the summary numbers in this file, which is the better warning.
3. **Do not attribute pass 2's five-key oldest.** Two candidate mechanisms were tested and neither produces it. An unexplained figure recorded as unexplained is a smaller defect than a wrong cause recorded as established — that is the whole content of M4.
4. **L12 costs one bullet and one clause.** Add `:267` to `### Corrections to this artifact's pass-1 and pass-2 records` ("the package honours it for six" → seven keys under six `attr` labels, matching the rationale's corrected sentence at `…-rationale.md:516`), and re-word hand-off 5 from five rows to six. The corrected-class population as I now measure it is exactly six rows: `:117`, `:121`, `:124`, `:135`, `:267`, `:270`.
5. **One uncharged pass-1 figure, recorded rather than filed, because it cannot be settled from the record.** `### Eight duplications caught by measurement` (`:140`, `:142`) says "eight places" over a table of **nine** rows, one of which is annotated "(×2 shingles)". The first draft it counts no longer exists, so whether the heading or the table is wrong is not decidable from this artifact — and unlike the six corrected figures, no later pass has contradicted it. Flagged so a final-gate reader does not read it as a seventh instance of the corrected class, and so nobody "fixes" it by inventing a ninth place or deleting a row.
6. **No contract-level question arose and none was escalated.** M6 is a defect against measurement; L12 is an incomplete record. Neither turns on which contract the package should offer. The spec-004 competitive-positioning decision was not touched; M1, L3 and the two calls the reconciliation invited attack on were not reopened.
7. **The one source edit this cycle authorizes is fully specified and nothing blocks R3's dispatch.** Plan and hand-off 1 agree, both were verified against the AST, and both authorized docstrings are byte-identical to HEAD.
8. **Baseline unchanged.** No growth, nothing reverted, no `git checkout`. The four deleted `docs/builder/bld-003-*.md` entries still await the maintainer. Re-derive `HEAD` rather than quoting `ff03c137`.

### Review outcome

`revision-needed` — one Medium (M6) and one Low (L12), neither carrying a recorded rejection, both inside this artifact's own record of how it measured.

**The deliverables are done.** The spec and the rationale were not opened this pass, and I verified that mechanically rather than accepting it: `122 / 13,373` and `713 / 51,373`, `git diff --stat` unchanged at `45 insertions(+), 77 deletions(-)`, both checkers at exit 0, both authorized docstrings byte-identical to HEAD, source and test trees empty in `git status`. All four closures deliver what they claim where it matters — M4's standing rule now rests on a sibling-constant measurement that reproduces figure for figure, L9's six-key oldest and the nine both hold under either baseline, L10's hand-off is right member for member and is the input to the one authorized source edit, and five of six stale figures are marked. What remains open is one false sub-claim carrying a lesson intended to outlive the cycle, and one row the sweep missed under a hand-off that says the sweep is complete.

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
