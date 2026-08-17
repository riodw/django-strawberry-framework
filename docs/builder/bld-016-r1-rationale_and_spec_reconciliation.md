# Build: Round 1 — rationale companion (reconstruction) + spec reconciliation

Spec reference: `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md`
Build plan: `docs/builder/build-016-fieldmeta_consolidation-0_0_6.md`
Status: final-accepted

**Procedural-closure shape** per `docs/builder/BUILD.md` `### Procedural-closure slices`: Worker 1 dispatched alone, no Worker 2 build and no Worker 3 review for this round. One combined Plan + Final-verification block. The spec clause that authorizes the closure is the build plan's `## Why this cycle exists` obligations 2 and 3 plus its `Ownership partition: none; sequential rounds` declaration — R1's whole deliverable is Markdown under Worker 1's exclusive spec custody (`docs/builder/worker-1.md` `## Spec custody`), so there is no source diff for a builder to write or a reviewer to read.

## Plan (Worker 1)

### Spec status-line re-verification

Performed at spawn, per `docs/builder/worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`. Lines 1-7 of the pre-reconciliation spec were read first. Two were falsified by the shipped build and both were edited in this pass:

- `Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact.` — the trailing clause is process justification, not build state.
- The whole preamble paragraph, whose closing instruction ("Before implementation work starts from this file, expand it into the full builder-format spec…") addresses a future implementation nineteen cards in the past.

Both are recorded under `### Spec changes made (Worker 1 only)`.

### Baseline and HEAD drift — measured, not restated

| Fact | Plan time | This pass | Note |
|---|---|---|---|
| `HEAD` | `d94db99262617bd21a36a7b60cc5dd2603d0b3b5` | `ded4b00c364c5938035d80dd6d38b1bef40a441c` | **Drift, and it is an amend, not new work.** |
| tree object | `7debb73f3b03e58ca197904756bed5d59753e549` | `7debb73f3b03e58ca197904756bed5d59753e549` | identical |
| parent | `d28fbc0a63613ed0ca0da4c784a670c499067b6a` | `d28fbc0a63613ed0ca0da4c784a670c499067b6a` | identical |
| subject | `refactor: single-site the duplicated class-label, bind, and fetch seams` | same | same |
| committer date | `2026-08-17 15:08:27 -0400` | `2026-08-17 15:25:18 -0400` | the only difference |
| `git status --short | wc -l` | 50 | 56 at pass end (53 at spawn) | see the count reconciliation below |

Commands: `git rev-parse HEAD`; `git log -1 --format='%H %T %ci %s'` on both; `git diff --stat d94db992 HEAD` -> empty; `git log -1 --format='%P'` on both.

`git merge-base --is-ancestor d94db992 HEAD` **fails** — `d94db992` is not an ancestor of `HEAD`, because a concurrent session amended it. This is the documented hazard in the standing memory note "Concurrent sessions rewrite main's history": a plan-time hash rots, and `git log A..B` listing a commit is not evidence of new work. **The trees are byte-identical, so every plan-time reading (V1-V11, F1-F13) remains valid against this tree without re-derivation from the older hash.** No plan-time claim is invalidated by the drift, and every claim restated in the spec was independently re-measured below regardless.

**Count reconciliation, measured at pass end.** 56 total = **4 this cycle's** + **52 baseline-dirty**. The cycle's four: `?? docs/builder/build-016-fieldmeta_consolidation-0_0_6.md` (Worker 0's plan, already present at spawn), and this pass's three — `M docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md`, `?? docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md`, `?? docs/builder/bld-016-r1-rationale_and_spec_reconciliation.md`. (The memory file is gitignored and does not appear.)

**The baseline is 52, not the plan's 50 — a discrepancy worth naming rather than rounding away.** Bucketed, the 52 are exactly the populations the plan's `## Baseline-dirty out-of-scope files` enumerates: 9 modified package source files, 10 modified test files, `M docs/review/review-0_0_14.md`, **28** untracked `docs/review/rev-*.md`, 2 deleted `docs/builder/build-*.md`, 2 untracked `docs/builder/DONE/build-*.md`. The plan's own enumeration therefore already summed above 50, and the `rev-*.md` bucket is the one it wrote as "~29" — a concurrent review cycle is actively emitting those files, so its population moves. Non-cycle dirty paths were **already 52 at this pass's spawn**, before any edit of mine. Every one of the 52 falls inside a bucket the plan declared out of scope, and none is this cycle's.

**All 52 baseline-dirty paths are untouched** — not edited, not reverted, not staged, no `git checkout`. `git stash`, `git checkout`, `git restore`, and `git worktree` were used nowhere in this pass; every source reading was taken read-only via `git show HEAD:<path>` into a scratch path outside the repository (`…/scratchpad/head/`) or via `git grep … HEAD`.

`optimizer/extension.py` — one of the five files the spec named and dirty with a concurrent session's work — was read **only** through `git show HEAD:` (V6/V7 below). The file was never opened in the working tree.

### DRY analysis

**Helper inventory checked.** Not applicable as a package-wide AST inventory: this round adds no helper, constant, validation branch, coercion utility, or test helper, and writes no `.py` file. `docs/builder/worker-1.md` `### Package-wide helper inventory before helper planning` gates *helper planning*, and there is none. In its place the round performed the equivalent read-only sweep for its actual medium — the sibling residual-cycle rationale companions — to avoid re-authoring an argument that already exists:

- **Existing patterns reused.** The entry-per-spec-section shape, the `## Provenance of this record` ledger, and the `## Reconciliation record` tail were taken from `docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-rationale.md` (headings at :1-:47, :174, :415). The reconciled spec's shape — one-line pointer sentence in the preamble slot, collapsed one-line `## Card snapshot`, `## Scope` as prose contract — was taken from `docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md`. The stub-shape argument (expand / delete / keep-and-reconcile, with the kanban-signals refusal that makes deletion mechanically impossible) is **cited, not retold**: it lives at `docs/SPECS/appx/spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md:80`, and that entry already names spec-016 among its seven identical-preamble siblings, at its measured 4,558 bytes.
- **New shared shape justified.** None. Nothing in this round is reusable by another round.
- **Duplication risk avoided.** The live risk was re-arguing the stub-shape question in a fourth sibling file (spec-007, 011, 012, 013 already carry or cite it), which would give the repository four divergent versions of one settled argument. Prevented by cross-reference. The second risk was stating the same fact as live contract in the spec *and* as a moved passage in the rationale; prevented by the `## Provenance of this record` ledger, which classifies every passage as moved, added, or deleted, and by keeping nothing in two places.

### Boundary count

Zero. This round writes Markdown and CSV only, adds no guard, cap, rejection path, or validation branch, and therefore owes no failability proof (`docs/builder/BUILD.md` `### What needs a proof, and what does not`). No split trigger fires.

### Hot-path declaration

None, per the build plan's `Hot-path declaration: **none.**` No executable statement changed.

### Floor-verification scope

None, per the build plan's `Floor-verification scope: **none.**` This round touches no Django / Strawberry / channels integration seam. Floor facts for the record, quoted from `docs/builder/BUILD.md` `## Floor verification`: Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**; the shared `.venv` is not the floor.

### Implementation steps

1. Re-derive `HEAD` and the baseline; record drift. Done above.
2. Re-measure every V1-V11 claim this pass intends to restate as contract, read-only. Done in `### Independent verification of every restated fact`.
3. Recover the deliberative layer from history (`BETTER.md` item 35, the eight retired anchors, the two shipping commits, the three later reshaping commits). Done.
4. Write the rationale companion at `docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md`, keyed to spec sections by heading and anchor, opening with a provenance section that states this is a **reconstruction** and not a move.
5. Reconcile the spec to state the current contract directly.
6. Verify: `check_spec_glossary.py` exit 0, scaffold check exit 0, every link def disk-exists, every anchor resolves against a real heading, every `#"substring"` unique.
7. Append the memory entry.

### Dispatched findings checklist

One box per R1 finding dispatched to this round by the build plan's `### R1 findings — the spec's own text`. F8 belongs to R2 and F9-F13 to R3; neither appears here.

- [x] **F1** — "No rationale companion exists, and there is no deliberative layer in the spec to move." R1 reconstructs the deliberation and says in the companion's provenance section that this is a reconstruction, not a move. Landed: `docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md` `## Provenance of this record — a reconstruction, not a move`, whose first sentence states it in bold, plus the four cited recovery sources.
- [x] **F2** — "Every source reference in the spec uses the forbidden `path:symbol` colon form — seven of them." Landed: all seven replaced with `path::QualifiedName` / `path::QualifiedName #"unique substring"`; measured 0 remaining colon-form references (see `### Independent verification`, F2 row).
- [x] **F3** — "Three of the seven named reader sites no longer exist under those names." Landed: the spec now names `types/base.py::_build_annotations`, `types/finalizer.py::finalize_django_types` (feeding `types/converters.py::resolved_relation_annotation`), and `optimizer/walker.py::_resolve_optimizer_hints`; the renames and their causes are in the rationale's `### ## Scope — the reader-site list was written before the implementation and never re-pointed` table. **The finding is confirmed but one of its three causes is corrected** — see the correction row below.
- [x] **F4** — "The spec's 'single source of truth' claim is stated without the two bounded exceptions the shipped code documents." Landed: `### Bounded exceptions to the single-source rule`, naming the walker's dual contract and the test-double fallbacks as design, with the `getattr(..., default)` invariant and the "no production call site reaches either" statement.
- [x] **F5** — "The spec's file list is incomplete against its own commit… The spec claims 'Existing tests pass without modification', which its own commit falsifies." Landed: `## Change population` names both commits, the six source files including `optimizer/field_meta.py`, the six test files, and states explicitly that existing tests did **not** pass unmodified.
- [x] **F6** — "The `~7 sites of duplicated relation-shape logic` claim needs the current population, not a tilde." Landed: `## Why it matters` drops the tilde and the classifier framing; `### Out of scope` draws the `FieldMeta`-read versus raw-descriptor-classification line and states that `FieldMeta.relation_kind` / `is_many_side` delegate to `utils/relations.py`.
- [x] **F7** — "The `Status:` line and `## Planning note` still address a *future* implementation." Landed: `Status:` is now `shipped.`; the preamble paragraph and the whole `## Planning note` section are removed and moved to the rationale.

### Implementation discretion items

- Whether to keep the now-unused `[backlog]` link definition in the spec's `<!-- Root -->` group. **Decided, not delegated:** keep, matching what `spec-013`'s cycle settled for the identical residue. The path resolves on disk, an unused definition breaks no render, and removing it in one sibling stub while six keep theirs trades a harmless wart for a divergence. Recorded in the rationale's `### The `[backlog]` link definition — recorded, not fixed`.
- Whether `## Change population` belongs in a contract at all. **Decided:** yes. The maintainer's reconciliation agenda names it explicitly, and it is the record of the card's own diff — the same thing `spec-013` carries when it names its test files.

---

## Final verification (Worker 1)

### Independent verification of every restated fact

Every row was measured at this tree in this pass. Nothing here is carried over from the plan on trust; where the measurement disagrees with the plan, the disagreement is named.

| # | Claim now stated as contract | Measurement |
|---|---|---|
| V1 | canonical read is `types/base.py::_build_annotations` #"field_meta = field_map[snake_case(field.name)]", feeding `PendingRelation(relation_kind=…, nullable=…)` | `git show HEAD:` copy, `base.py:1830` inside `_build_annotations` (`def` at `:1714`, `PendingRelation(` at `:1849`). `git grep "def _record_pending_relation" HEAD` -> **no match**. |
| V2 | `types/converters.py::resolved_relation_annotation` takes keyword-only `field_meta` and reads only `meta.is_many_side` / `meta.nullable`; the canonical read is `types/finalizer.py::finalize_django_types` | `converters.py:804-816`; `finalizer.py:856` read and `:873` call with `field_meta=field_meta`, both inside `finalize_django_types` (`def` at `:749`, the only module-level `def` in `700-920`). Production callers: `git grep resolved_relation_annotation HEAD` -> the only call site in `django_strawberry_framework/` outside `converters.py` itself is `finalizer.py:873`. |
| V3 | `types/resolvers.py::_field_meta_for_resolver` does `registry.get_definition(parent_type)` -> `definition.field_map.get(field.name)`; `::_make_relation_resolver` consumes `relation_kind` / `is_many_side` / `related_model` / `attname` | `resolvers.py:273-297` and `:300-388` (`field_meta = _field_meta_for_resolver(...)` at `:336`, then `.relation_kind`, `.is_many_side`, `.related_model`, `.attname`). |
| V4 | `optimizer/walker.py::_resolve_field_map` reads `registry.get_definition(...)`, with a `model._meta.get_fields()` fallback | `walker.py:283-323`. |
| V5 | the hints read is `optimizer/walker.py::_resolve_optimizer_hints`, called by `::_walk_selections` and injected into `optimizer/nested_planner.py` | `walker.py:343-347` def; call at `:461` inside `_walk_selections` (`def` at `:426`); injection `resolve_optimizer_hints=_resolve_optimizer_hints` at `walker.py:1464`; consumed at `nested_planner.py:1155` (`param` at `:1100`). |
| V6 | `optimizer/extension.py::_collect_schema_reachable_types` gates on a registered definition | `extension.py:670` def, `:706` `registry.get_definition(origin) is not None`. Read via `git show HEAD:` only — the working-tree file is a concurrent session's. |
| V7 | the audit read is `optimizer/extension.py::DjangoOptimizerExtension.check_schema` | `extension.py:1264` `@staticmethod`, `:1265` `def check_schema`, inside `class DjangoOptimizerExtension` (`:799`); `:1292` `registry.get_definition(type_cls)`, `:1295` `field_map`, `:1296` `optimizer_hints`. **Correction to the plan and the spec:** the qualified name carries the class. |
| V8 | no class-attribute mirror exists as declaration or read | `git grep -c "_optimizer_field_map" HEAD -- django_strawberry_framework tests examples scripts` -> **no matching path** (the only hit repo-wide is `examples/fakeshop/db.sqlite3`, 6 occurrences — card body text, not code). At `de35a622^` the same grep found `types/base.py:73,74` (ClassVars), `:144,145` (writes), `walker.py:86`, `extension.py:356,619` (reads). |
| V9 | no `TODO(spec-fieldmeta-*)` anchor remains | `git grep -c "spec-fieldmeta" HEAD -- django_strawberry_framework tests examples scripts` -> **no matching path** (DB only). |
| V10 | `FieldMeta.relation_kind` / `is_many_side` delegate to `utils/relations.py` | `field_meta.py:153-155` `return relation_kind(self)`; `:157-160` `return is_many_side_relation_kind(self.relation_kind)`; both imported from `..utils.relations` at `:26-31`. |
| V11 | no second field-metadata store | covered by V8 plus V4/V5's single producer. |
| F2 | zero colon-form source references remain in the spec | every source reference in the reconciled spec is `path::QualifiedName`, `path::QualifiedName #"…"`, or `path #"…"`; the five `#"substring"` forms were each confirmed to match **exactly once** in their named file at `HEAD` (`grep -cF` = 1 for all five). |
| F5 | the change population | `git show --name-only --format='' de35a622` -> 16 paths, listed in the rationale; `git show --stat de35a622` -> `tests/optimizer/test_walker.py` +120, `tests/types/test_resolvers.py` +72, six test files total. `git grep -c "# TODO(spec-fieldmeta" de35a622^ -- 'django_strawberry_framework/*.py'` counted as occurrences -> **8**; the bare token `spec-fieldmeta` -> **13** (8 anchors + 5 docstring cross-references). |
| F6 | the classifier population | `git grep -n "relation_kind(\|is_many_side_relation_kind(" HEAD -- django_strawberry_framework` -> raw-descriptor call sites at `connection.py:818`, `filters/sets.py:2031`, `optimizer/join_taxonomy.py:301`, `optimizer/walker.py:185,1026`, `utils/relations.py:305,438`, plus `optimizer/field_meta.py:155,160,231` (the two delegating properties and the canonical builder). The spec states the rule on the axis that separates these from the retired duplication rather than counting them. |
| — | public surface | `git show --name-only de35a622 \| grep -c "__init__.py"` -> **0**. |
| — | coverage gate | `pyproject.toml:209` `fail_under = 100`. The spec states the gate rather than asserting a measured coverage number, since coverage flags are forbidden to workers. |

**Three corrections to the build plan, each measured:**

1. **The card shipped two commits, not one.** `de35a622` (2026-05-15 22:26, 16 files, +403/-178) is the whole implementation. `2bd7cb84` "Refactor README.md and TODAY.md for clarity and structure" (2026-05-16 00:49) added the `CHANGELOG.md` entry, added the board card as `DONE-ALPHA-012-0.0.6`, and deleted `BETTER.md` item 35. The plan's `### What the card actually did` calls `de35a622` the card's whole implementation *and* lists `CHANGELOG.md` among the omitted files; `CHANGELOG.md` is not in that commit's 16 paths at all. This also explains F12: `2bd7cb84` is where the pre-renumber `012-` id in `CHANGELOG.md:221` came from.
2. **`_resolve_optimizer_hints` was created by `de35a622` itself, not extracted later.** `git grep -n "_resolve_optimizer_hints" de35a622 -- django_strawberry_framework/optimizer/walker.py` -> def at `:88`, call at `:194`, in the shipping commit. The plan's V5/F3 read it as a later extraction. The truth is sharper: the spec's site name `_walk_selections (hints read)` was copied verbatim from `BETTER.md` item 35 — a pre-implementation proposal — and no pass ever re-pointed it at what shipped. `36da25b4` (2026-06-11) later changed the parameter from `type_cls` to `definition`; `991d5120` (2026-07-13) injected it into the nested planner.
3. **The `_record_pending_relation` deletion and the `resolved_relation_annotation` upstream move are one commit**, `f83bb71b` "Run REVIEW.md;" (2026-05-20) — five days after the card shipped. It deleted the helper, removed the second eager-bind call path in `types/base.py`, and made the surviving finalizer call pass the canonical `field_meta` explicitly. The plan attributes V1's rename to spec-018; the surviving comment at `types/base.py` #"the import-order trap closed by spec-018" credits spec-018 for the eager-bind removal, so the two readings are consistent — the commit is `f83bb71b` and the spec that motivated it is 018. Both are now recorded, with the commit as the primary citation.

### Spec changes made (Worker 1 only)

Spec path: `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md`. Byte count **4,558 -> 9,162**. Every change is a rewrite to the current contract; nowhere does the spec narrate its own history.

| # | Cited pre-reconciliation spec text | Change | Reason | Finding |
|---|---|---|---|---|
| 1 | `Status: shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact.` | -> `Status: shipped.` | The trailing clause is process justification about the file, not a statement of build state; it is a duplicate of the moved preamble and now lives in the rationale. | F7 |
| 2 | `This file is intentionally lightweight. … expand it into the full builder-format spec described by docs/SPECS/NEXT.md and docs/builder/BUILD.md.` | **Moved** to the rationale; replaced by the one-line pointer sentence naming what lives there, plus the `[spec-016-rationale]` definition under `<!-- docs/SPECS/ -->`. | The instruction is counterfactual — the work shipped 2026-05-15/16 and this file was created 2026-06-01 by `81e4704d`, so there was never implementation to start from it. | F1, F7 |
| 3 | `## Planning note` / `shipped` | **Moved** (heading and body) to the rationale; section removed. | Not a sentence, not a planning note, and a duplicate of the `Status:` line. | F7 |
| 4 | The six `## Card snapshot` board-metadata bullets (status, milestone, priority, relative size, five labels). | Collapsed to one identity line plus an explicit statement that the board owns the rest. | Rendered copies of DB rows with nothing keeping them true (`docs/builder/BUILD.md` `### Generated docs are DB-backed`). The labels were still **correct** at `HEAD`; the removal is structural, and the rationale says so. | F1 |
| 5 | All seven colon-form references, e.g. `django_strawberry_framework/types/base.py:_record_pending_relation`, `optimizer/extension.py:check_schema`. | Replaced with `path::QualifiedName` and `path::QualifiedName #"unique substring"`; `check_schema` gains its class (`DjangoOptimizerExtension.check_schema`). | `AGENTS.md` rule 27; an archived spec is a standing doc, not a per-cycle scratchpad. | F2 |
| 6 | `_record_pending_relation`; `types/converters.py:resolved_relation_annotation` as the canonical read; `optimizer/walker.py:_walk_selections` (hints read). | Repointed to `types/base.py::_build_annotations`, `types/finalizer.py::finalize_django_types` (passing into `resolved_relation_annotation`), and `optimizer/walker.py::_resolve_optimizer_hints` with its `nested_planner.py` injection. | Three of seven sites were uncheckable against `HEAD` — one of them stale on the day the card shipped. Causes are in the rationale, not the spec. | F3 |
| 7 | `## Scope` as a flat two-bullet list of sites. | Restructured into `### Single source of truth` (the rule, then its seven readers), `### Bounded exceptions to the single-source rule` (new), `### Mirror retirement`, `### Out of scope` (new). | The stub listed sites with no rule above them, so a reader could not tell what the contract was; and the two documented exceptions were reachable by grep but unstated, making an audit unresolvable rather than merely incomplete. | F4, F6 |
| 8 | `Three reader sites now read FieldMeta…` / `DjangoType.__init_subclass__ no longer writes…` | Restated in present-tense invariant form ("`FieldMeta` … **is** the canonical store"; "writes no legacy class-attribute mirror"), with the `registry.clear()` reason attached to the mirror invariant. | `docs/builder/BUILD.md` `## Spec rationale extraction` — the spec reads as a clean current contract; "now" and "no longer" are chronology. | F3 |
| 9 | `~7 sites of duplicated relation-shape logic` and the framing `re-deriving relation shape via relation_kind(field) + raw getattr(field, ...)`. | Rewritten. `## Why it matters` gives three reasons with no tilde; `### Out of scope` states that calling the shared classifiers on a raw descriptor was never in scope and names the delegation. | The number was exact, not approximate, and the framing made the shared classifier look like the retired duplication — a reader who greps it finds seven live raw-field call sites and concludes the consolidation was undone. | F6 |
| 10 | The five-file list, and `Existing tests pass without modification.` | Replaced by `## Change population`: both commits, six source files (adding `optimizer/field_meta.py`), six test files, standing docs, and the explicit statement that existing tests did **not** pass unmodified. | The file list omitted the module where the consumed `FieldMeta` properties were added; the test sentence was false when written, not merely stale. | F5 |
| 11 | `## Other` (heading + eleven bullets). | Removed. Each bullet is now live contract in the owning section, an entry in the rationale, or deleted as falsified — never two of those. | A rendered dumping ground of five different kinds of content under a heading naming none of them. | F1, F5, F6 |
| 12 | (new) `## Compatibility` | Added, carrying the two compatibility statements plus the note that the retired attributes were private and undocumented. | `## Other`'s compatibility content needed a heading that names it. | F1 |
| 13 | `[backlog]: ../../BACKLOG.md` | **Kept**, now unused. | Matches `spec-013`'s settled disposition for the identical residue; recorded in the rationale rather than silently trimmed. | — |

**No deferral rows.** Every box in `### Dispatched findings checklist` is `- [x]` with its landing site named, so no `- [ ]` needs a deferral reason.

### Rationale companion

Created at `docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md`, **36,128 bytes**, tracked (untracked-on-disk now; the maintainer's commit stages it alongside the spec, per `docs/builder/worker-1.md` rule 5).

- **Keyed to the spec.** Nine entries, each opening with the spec section it belongs to by heading and a reference-style link to that section's anchor. Two entries key to headings the reconciliation removed (`## Planning note`, `## Other`) and each says so and anchors the section its subject now bears on. No entry names no section.
- **Reconstruction, stated as such.** `## Provenance of this record — a reconstruction, not a move` is the first section, states in bold that this is not a `## Spec rationale extraction` move because the spec had no deliberative layer to cut, and names the four recovery sources. It then separates what genuinely **moved** (the preamble paragraph, the whole `## Planning note`, and the two deliberative `## Other` bullets), what was **added in exchange**, and what was **deleted outright** under `worker-1.md` rule 2.
- **Rejected alternatives recorded**, one per entry where a choice existed: rewording the planning note; keeping the historical site names with a "has moved" note; closing the two bounded exceptions instead of documenting them; replacing the false test sentence with "tests were updated"; and, for the pass as a whole, point-fixing the references versus expanding the stub versus restating the scope as a rule.
- **Claims the spec may no longer make** are enumerated per entry, including the three stale site names, the tilde, the classifier framing, the five-file list, the false test sentence, and the expansion instruction.
- **The stub-shape argument is cited, not retold** (`spec-007-…-rationale.md:80`), which is where the expand / delete / keep-and-reconcile weighing and the kanban-signals deletion refusal already live.

### Terms CSV

`docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-terms.csv` — **not edited**. The reconciled body links exactly the two anchors the CSV already carries (`djangotype`, `relation-handling`), one row per anchor, so no row was owed. Both links survive the rewrite inside `### Single source of truth`.

### Verification runs

| Check | Command | Result |
|---|---|---|
| Glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` | `OK: 2 terms - all have glossary entries and at least one spec link.` exit **0** |
| Markdown scaffold | `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md` | exit **0** |
| Link defs, spec (5) | disk-exists loop over every `^[ref]: path` | 5/5 resolve |
| Link defs, rationale (16) | same loop | 16/16 resolve |
| Anchors | every `#…` target compared against the reconciled spec's nine `##`/`###` headings | 9/9 resolve; the spec itself has no in-page anchors, so nothing dangles |
| Depth rot | `../../../AGENTS.md` from `docs/SPECS/appx/` = repo root; the spec's glossary defs stay `../GLOSSARY.md` (from `docs/SPECS/`), **not** `../../` | checked explicitly; no same-named file one level up masks either path |
| `#"substring"` uniqueness | `grep -cF` per reference in the named file's `HEAD` copy | 1 for all five |
| Working tree | `git status --short` | 56 paths; exactly 4 are this cycle's; all 52 baseline-dirty paths untouched (count reconciled above against the plan's 50) |

No `pytest` was run — this pass changes no executable code (`docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`; the round's brief forbids it outright). No formatter was run: Markdown and CSV only, and the scaffold check above is the applicable gate.

### Out-of-scope residue found while verifying — for the final gate's deferred catalog

Neither is this round's to fix, and neither is a defect in shipped behavior:

- **`tests/test_registry.py:504`** carries a comment naming `_record_pending_relation`, deleted at `f83bb71b`. `git grep -n "_record_pending_relation" HEAD` returns four paths: the spec (now fixed), `docs/SPECS/spec-010-foundation-0_0_4.md` (two lines, where it is a legitimate historical reference in another card's spec), this test comment, and the fakeshop DB. Tests are outside every round's writable set this cycle.
- **`CHANGELOG.md:221`** carries the pre-renumber card id **and** the three stale site names **and** the bare `extension.check_schema`. `AGENTS.md` rule 21 forbids the edit; this is F12's population, wider than F12 recorded it.

### Summary

Reconstructed spec-016's deliberative layer into a new 36KB rationale companion keyed to the spec by heading and anchor, stating in its own provenance section that it is a reconstruction rather than a `## Spec rationale extraction` move, and moved out of the spec the three passages that genuinely were deliberation. Reconciled the spec from a 4,558-byte card snapshot into a 9,162-byte current contract: all seven source references symbol-qualified, the three stale reader sites repointed at `HEAD` (one of which was stale on the day the card shipped, having been copied from a pre-implementation proposal), the two bounded exceptions to the single-source rule stated as design, the classifier-versus-`FieldMeta` line drawn in a new `### Out of scope`, the complete two-commit change population recorded with the false "existing tests pass without modification" claim corrected, and the counterfactual preamble and one-word `## Planning note` gone. Every V1-V11 claim was independently re-measured read-only at this tree; three plan-level facts were corrected in the process. No source file, test, generated doc, or baseline-dirty path was touched. F8 remains open and belongs to R2.

### Final status

`final-accepted`.
