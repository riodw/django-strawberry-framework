# Build: Review round 1 — spec-019 rationale extraction + spec-to-HEAD reconciliation

Spec reference: `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`
Rationale companion (created this round): `docs/SPECS/appx/spec-019-consumer_overrides_scalar-0_0_6-rationale.md`
Build plan: `docs/builder/build-019-consumer_overrides_scalar-0_0_6.md`
Status: final-accepted

**Combined pass.** This is a documentation-only residual closeout round with no builder involved, so Worker 1 ran planning, the work, and final verification on this one artifact. No code was written; no Worker 2 or Worker 3 pass exists, and the `## Build report` / `## Review` sections are therefore absent by design rather than skipped.

Declarations carried from the plan, unchanged:

- Ownership partition: `none; single sequential round`.
- Hot-path declaration: `none` (documentation-only cycle; no package source file is written).
- Floor-verification scope: `none` (no Django / Strawberry / channels seam is touched). No floor venv run is owed by this round or by the final gate.

---

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked.** Not applicable in the code sense — this round writes no `.py` file and proposes no helper, shared constant, validation branch, coercion utility, or test helper. The package-wide inventory step exists to prevent duplicated *code* shapes at plan time; a round whose entire diff is three `.md` files and one `.md` sentence has no shape to duplicate. Recorded explicitly rather than left silent.

The DRY question that *does* apply to this round is documentary: the rationale companion must not restate what the spec keeps, and neither file may restate a measurement the other owns.

- **Existing patterns reused.** The rationale file's structure follows the in-tree precedent set by `docs/SPECS/appx/spec-018-meta_primary-0_0_6-rationale.md` — `## Provenance of this record` (with the Moved / Kept-deliberately split and the byte table), `## What the card actually did, and what later cards did to it`, `## Entries keyed to the spec` with one heading per spec Decision, and a closing reconciliation table plus a "what this cycle deliberately did not fix" list. Reusing the shape means a reader who has read one rationale companion can navigate this one without re-learning it.
- **New shape justified.** One: a `### Nothing was skipped in the code` subsection stating the Task-1 verification per slice. It exists because this is a *residual* cycle, where "was anything skipped" is the load-bearing question rather than an assumption.
- **Duplication risk avoided.** Two, both real:
  1. **Byte counts in two places.** The rationale file's own byte table would be a mid-pass measurement of a file still being written. Prevented by having the rationale file point at this artifact for the authoritative figures and say why, so there is exactly one measured pair.
  2. **Contract text in both files.** Every candidate paragraph was classified Moved / Kept / Deleted before writing, and the `**Moved**` and `**Kept in the spec deliberately**` lists in the rationale file are the record of that classification. No sentence is in both files; falsified sentences are in neither.

### Implementation steps

1. Re-derive Task 1 independently — walk every `- [ ]` in the spec's `## Slice checklist` and `## Definition of done` against the working tree, per-name, not per-claim.
2. Run the focused suite once as evidence.
3. Read `django_strawberry_framework/types/base.py::_id_annotation_is_relay_node_id` and commit `2bcd7f96` and re-derive finding 1's mechanism change from source rather than from the plan's summary.
4. Create the rationale companion; perform the cut.
5. Rewrite the spec end to end as a clean current contract.
6. Correct the one live-doc falsehood in `CHANGELOG.md`; confirm `docs/GLOSSARY.md` needs no edit.
7. Verify: glossary checker, link-definition blocks (disk-exists every path), residue grep, byte counts, ruff, scaffold checker.

### Test additions / updates

None. This round writes no test. The focused suite named in the dispatch is run as evidence that the shipped contract still holds, not as a new pin.

### Implementation discretion items

None. Every choice this round faced was a contract question resolved from the spec, the code, or `KANBAN.md`'s renumber-sweep bullet.

### Dispatched findings checklist

One box per finding the plan's `## Verified findings carried into R1` dispatched, plus the three tasks.

- [x] Task 1 — independent re-derivation that nothing was skipped in the code (all five slices).
- [x] Task 2 — the rationale MOVE, including the `015 → 019` renumber record and the "rev11 is not the last word" record.
- [x] Finding 1 — the `relay.NodeID` detection mechanism was rewritten (`2bcd7f96`); six spec surfaces rewritten to the landed mechanism, plus the live `CHANGELOG.md` half corrected and `docs/GLOSSARY.md` confirmed correct as written.
- [x] Finding 2 — `_is_relay_shaped` is a named module-scope helper, not an inline disjunction.
- [x] Finding 3 — both `consumer_annotated_*` comprehensions carry the `auto_annotated_fields` exclusion.
- [x] Finding 4 — `_consumer_assigned_fields` takes `cls`, not `cls.__dict__`.
- [x] Finding 5 — `consumer_authored_fields` is no longer `_build_annotations`'s exclusive consumer.
- [x] Finding 6 — Slice 5's self-referential KANBAN instruction, and its matching Definition-of-done item.
- [x] Finding 7 — Slice 5's stale archive bullet.
- [x] Finding 8 — the CHANGELOG target section moved from `[Unreleased]` to `## [0.0.6] - 2026-05-19`.
- [x] Finding 9 — the Prior-`0.0.6`-card note's pre-renumber filenames, converted to post-renumber card ids on the spec-018 precedent.
- [ ] Finding 10 — the `spec015_*` identifiers baked into landed tests. **Deliberately not fixed**; the landed spelling is recorded in the spec and the rename question is routed to the deferred-work catalog below. Deferral reason under `### Spec changes made (Worker 1 only)`.

---

## Final verification (Worker 1)

### Task 1 — per-item walk of the spec's `## Slice checklist` against the working tree

Re-derived independently of the build plan's pre-dispatch list. Method: for each of the 19 pinned test names, `grep -rln "def <name>" tests/ examples/` across the whole test tree — per name, so a miss cannot hide behind a matching sibling. For each source contract, read the current file.

**Slice 1 — Track annotation-only scalar overrides on `DjangoTypeDefinition`.** All contracts landed.

| Sub-check | Result |
|---|---|
| `consumer_annotated_scalar_fields` collected in `__init_subclass__` | **Landed.** `django_strawberry_framework/types/base.py`, the comprehension immediately after `consumer_annotated_relation_fields`, filtering `not field.is_relation`. Carries the later `auto_annotated_fields` exclusion (finding 3). |
| `consumer_annotated_scalar_fields` field on `DjangoTypeDefinition`, grouped-by-style order | **Landed.** `django_strawberry_framework/types/definition.py`, five `consumer_*_fields` lines in the order `authored, annotated_relation, annotated_scalar, assigned_relation, assigned_scalar` — the mandated grouping, with the cosmetic re-order applied. |
| Union into `consumer_authored_fields` | **Landed.** Four-way set-literal union at the site the spec names. |
| Plumbed through to the `DjangoTypeDefinition(` registration call | **Landed.** |
| `_NODEID_STRING_RE` at module scope | **Landed**, with the anchor-rationale comment above it. |
| `_has_node_id_marker` | **Landed**, body byte-equivalent to the spec's. |
| `_id_annotation_is_relay_node_id` | **Landed**, but by a **different mechanism** than the spec described — finding 1. Contract identical. |
| `_is_relay_shaped` | **Landed** as a named module-scope helper — finding 2; the spec described the predicate inline. |
| Relay `id` collision guard, both reject paths | **Landed.** Both error messages are byte-identical to the spec's (modulo the repo's ASCII-only `.py` rule turning the spec's em-dashes into hyphens). Guard control flow is flattened relative to the spec pseudocode — recorded as an eleventh divergence below. |
| 4 core override tests | **All 4 present**, `tests/types/test_definition_order.py`. |
| 4 converter-bypass tests | **All 4 present** — 3 in `test_definition_order.py`, `test_annotation_override_of_arrayfield_with_nested_array_is_allowed` in `tests/types/test_converters.py`, exactly the mandated placement split. |
| 11 Relay-collision tests | **All 11 present**, `tests/types/test_definition_order.py`. |

Test-name total: **19 of 19 found, 0 misses**, 18 in `test_definition_order.py` and 1 in `test_converters.py` — the "18 of 19" rule holds.

**Slice 2 — Retire the skipped test.** `grep -rn "test_consumer_annotation_overrides_synthesized" tests/ examples/ django_strawberry_framework/` returns nothing: the function, its skip decorator, and its reason text are gone from the whole tree. The conditional second sub-check (`CATEGORY_SCALAR_FIELDS` removal "only if it becomes unused") correctly did **not** fire — the constant is read at ~58 sites in `tests/types/test_base.py`.

**Slice 3 — `_consumer_assigned_fields` docstring.** Landed. The docstring enumerates all four corners by name (`relation × annotation`, `relation × assigned`, `scalar × annotation`, `scalar × assigned`), names the `__init_subclass__` collection sites, names the four sets on `DjangoTypeDefinition`, and names the single `consumer_authored_fields` short-circuit read by `_build_annotations`'s two branches. Every element the sub-check requires is present.

**Slice 4 — version-bump quintet.** All five checkboxes are no-ops as predicted, and long past. `pyproject.toml` reads `version = "0.0.14"`; `django_strawberry_framework/__init__.py` reads `__version__ = "0.0.14"`; `tests/base/test_init.py`, `docs/GLOSSARY.md`'s current-version line, and `uv.lock` carry no `0.0.5` string. The Prior-`0.0.6`-card note itself was factually wrong (finding 9) and is corrected.

**Slice 5 — docs, KANBAN, CHANGELOG, archive.** All landed; read end to end rather than grepped.

| Sub-check | Result |
|---|---|
| Root `README.md` version line | No-op, at the current release. |
| `docs/README.md` shipped-capability line | **Landed** — the scalar-override bullet names both override styles, the `convert_scalar` bypass, and the `relay.Node` `id` collision. |
| GLOSSARY `Scalar field override semantics` → `shipped (0.0.6)` | **Landed**, with the converter-bypass paragraph (all three named behavior changes), the Relay-collision paragraph (both sub-restrictions), and the metadata-limitation paragraph. |
| GLOSSARY `Scalar field conversion` names the override recourse | **Landed** — the "Subclass MRO walk" paragraph names `Meta.exclude` *and* a consumer annotation override as the two recourses. |
| GLOSSARY `Definition-order independence` closing sentence removed | **Landed** — `grep "Manual scalar-field override semantics"` returns nothing. |
| GLOSSARY `DjangoType` alpha-constraints list | No scalar-override entry present; nothing to drop, as the spec anticipated. |
| GLOSSARY index badge | **Landed** — `shipped (0.0.6)`. |
| `docs/TREE.md` | No change needed, as specified. |
| `TODAY.md` | **Landed**, including the "not currently demonstrated in fakeshop" qualifier. |
| `KANBAN.md` `DONE-019-0.0.6` | **Landed** in the Done section with the verbatim body. Its Relay paragraph still describes the retired mechanism — deferred, see the catalog. |
| `CHANGELOG.md` five entries | **All five present** under `## [0.0.6] - 2026-05-19` (finding 8). One of them carried a false mechanism claim — corrected this round (finding 1's live half). |
| Archive | **Landed** — spec at `docs/SPECS/`, terms CSV at `docs/SPECS/appx/`, link block re-relativized. |

Also verified: the rev10 L2 temporary `[tool.ruff.lint.per-file-ignores]` ERA001 entry was removed. `pyproject.toml`'s per-file-ignores carry `ERA001` only for `tests/**/*.py` and `examples/**/*.py` — no package path.

### Task 1 — per-item walk of the spec's `## Definition of done`

| Item | Result |
|---|---|
| Every Slice 1 / 2 / 3 checkbox checked | **Satisfied** per the walk above. |
| Skipped test deleted; no "Deferred scalar-field override behavior" skip block remains | **Satisfied.** |
| All 19 Slice 1 tests pass, at the mandated placements | **Satisfied.** Focused run below; placement split confirmed. |
| `uv run pytest` passes with 100% package coverage | **Not run by this round** — `BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool` forbids `--cov*` flags in any worker pass. Coverage is the maintainer's gate; the focused suite was run with `--no-cov`. |
| `uv run ruff check .` | **Passes.** |
| `uv run ruff format --check .` | **Passes.** |
| `git diff --check` | **Passes.** |
| GLOSSARY `Scalar field override semantics` reads `shipped (0.0.6)` | **Satisfied.** |
| GLOSSARY `Scalar field conversion` names the override recourse | **Satisfied.** |
| GLOSSARY body names the metadata-route limitation | **Satisfied** — a dedicated paragraph names the resolver-backed sibling field and warns off the metadata-only form. |
| KANBAN shows the card in Done, no in-flight entry | **Satisfied.** The item's own wording was self-contradictory (finding 6) and is rewritten. |
| CHANGELOG carries the five entries | **Satisfied**, under the post-cut heading (finding 8). |
| Slice 4 quintet verified by `grep`, not blind edits | **Satisfied** — grepped, all no-ops. |
| No new public symbol / `Meta.*` key; `__all__` unchanged | **Satisfied** — the four helpers and the definition field are all private (`_`-prefixed or dataclass-internal); no `Meta` key was added. |

**No code gap found.** Every spec contract has an implementation. No code round needs to be opened.

### Focused test run

```
uv run pytest tests/types/test_definition_order.py tests/types/test_converters.py tests/types/test_base.py --no-cov
```

`286 passed in 6.47s` (8 xdist workers, Python 3.14.2, Django 6.1). No `--cov*` flag. Recorded as "it runs", per `## Final verification job` step 5.

### DRY check across this round and prior accepted rounds

No prior round exists in this cycle. Against the concurrent spec-018 residual cycle's output: the rationale companion reuses that file's section shape deliberately (see `### DRY analysis`) and duplicates none of its content — the two describe different cards. No repeated literal, no near-copy helper.

### Verification owed before `final-accepted`

| Check | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md` | **exit 0** — `OK: 15 terms`. Same count as before the move; every term still links to a real anchor. |
| Spec `<!-- LINK DEFINITIONS -->` block | 22 definitions, 21 distinct uses, **0 undefined refs, 0 unused defs**, all ten canonical group headers present in order. Every def path disk-exists-checked from `docs/SPECS/`. |
| Rationale `<!-- LINK DEFINITIONS -->` block | 12 definitions, 12 uses, **0 undefined, 0 unused**, all ten headers present in order. Every def path disk-exists-checked from `docs/SPECS/appx/`; the one initially-missing target (`../../builder/bld-review-1-spec019_rationale.md`) is this file, which now exists. |
| `uv run python scripts/check_trailing_commas.py --check` on both `.md` files | **exit 0** — the `source-layout` hook's markdown-scaffold rule is satisfied by both. |
| `uv run ruff format --check .` | **Passes** — no drift. This round edited no `.py`. |
| `uv run ruff check .` | **Passes** — no drift. No baseline exception needed. |
| Residue grep | **0.** See below. |
| Byte counts | See below. |

**Residue grep.** Pattern set as dispatched, run over the whole spec:

```
grep -n "rev[0-9]\|Rev[0-9]\|Revision [0-9]\|Worker 1 picks\|Worker 1 may\|option (a)\|post-rev\|H1:\|M1:\|L1:" docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md
```

**Zero matches. No deliberate survivors.** Every one of the 182 `rev<N> <H|M|L><n>` attributions is gone, the eleven-revision history block is gone, and all 24 "Worker 1 picks / may" hedges are gone. Pre-move counts, measured before any edit: `rev[0-9]` 287 occurrences, `Rev[0-9]` 24, `Revision [0-9]` 12, `rev<N> <H|M|L><n>` 182, "Worker 1 picks"/"Worker 1 may" 24. Every figure was measured at the time of writing it, not carried from the dispatch.

**Byte counts**, `wc -c`, both measured after both files were finished:

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md` | 181,073 | 104,017 | **-77,056** |
| `docs/SPECS/appx/spec-019-consumer_overrides_scalar-0_0_6-rationale.md` | 0 (did not exist) | 47,488 | +47,488 |
| **Pair total** | 181,073 | 151,505 | **-29,568** |

The pair shrank, which is the proof the move was a move and not a copy: a copy would have left the pair total at or above 181,073. The 29,568-byte net reduction is the falsified and superseded prose that was **deleted rather than moved** — chiefly the retired `typing.get_type_hints` fail-soft apparatus (described at length in six spec sections), the seven successive line-delta estimates, and the per-revision restatements of contracts that later revisions replaced. `BUILD.md`'s corpus ratchet is not what this measures: that ratchet binds `docs/builder/BUILD.md`, `ARTIFACT.md`, and the four `worker-*.md` role files, none of which this round may edit or did edit.

### Spec changes made (Worker 1 only)

Every edit, with the spec section, the finding that triggered it, and a one-line reason. The spec was rewritten end to end for the rationale move, so "the whole file" is the diff; the entries below are the substantive contract changes inside it.

**The rationale move itself (Task 2)** — `## Revision history` block (eleven revisions), and 182 inline revision attributions across `## Slice checklist`, `## Architectural decisions`, `## Edge cases and constraints`, `## Test strategy`, `## Definition of done`, and the verbatim KANBAN and CHANGELOG bodies. Reason: `BUILD.md` `## Spec rationale extraction` — the spec never narrates its own history. All cut to `docs/SPECS/appx/spec-019-consumer_overrides_scalar-0_0_6-rationale.md`, keyed to the spec heading each belongs to.

| # | Spec section | Finding | Change and reason |
|---|---|---|---|
| 1 | Header `Status:` line | Task 2 | `draft (revision 11, post-build maintainer-feedback pass)` → `shipped (0.0.6, 2026-05-19); archived. Card DONE-019-0.0.6`. A shipped card's spec is not a draft, and the named revision has been superseded. |
| 2 | Header, new `Deliberation:` line + renumber note | Task 2 | Added the one-line pointer to the rationale companion (required: "every decision keeps a pointer") and the `015 → 019` renumber record with commit `a357c68c`, so a reader chasing `git log` for "spec-019" is not left guessing. |
| 3 | `## Goals` bullet 5 | 1 | `typing.get_type_hints(cls, include_extras=True)` + "token-shaped regex fail-soft" + "resolved-object fallback for the sibling-annotation-unresolved case" → the landed direct `cls.__annotations__["id"]` read dispatching on the value's shape. |
| 4 | `### Decision 7`, detection prose and code block | 1 | The `try` / `except (NameError, AttributeError)` structure, the `hints` mapping, both named "fail-soft sub-cases", and the whole fail-soft vocabulary replaced with the landed two-arm `isinstance(raw, str)` dispatch and its two docstring-stated consequences (no other annotation is consulted; behavior is identical on every supported Python). |
| 5 | `## Slice checklist`, Slice 1 module-scope-helpers checkbox | 1 | Same substitution, plus the helper's described structure corrected. |
| 6 | `## Slice checklist`, Slice 1 annotation-reject sub-bullet | 1 | The two-sub-case fail-soft description replaced with the shape-dispatch description; the "guard suppression only, Strawberry still resolves" contract retained because it is still true. |
| 7 | `## Edge cases and constraints`, `relay.Node` bullet | 1 | Same substitution; "mixed (directly-resolved `id` alongside other unresolved annotations)" reworded to state the stronger landed property — detection reads only `cls.__annotations__["id"]`, so no other annotation can influence the verdict. |
| 8 | `## Test strategy`, coverage paragraph | 1 | The four fail-soft-path enumerations replaced with the four arms actually in the code (string accept / string reject / resolved accept / resolved reject), each named against the tests that hit it. |
| 9 | `## Slice checklist`, Slice 5 verbatim KANBAN body | 1 | The Relay paragraph's `typing.get_type_hints` + two-fail-soft-sub-case narrative rewritten to the landed mechanism. |
| 10 | `## Slice checklist`, Slice 5 verbatim CHANGELOG `Added` entry | 1 | Same, matched word-for-word to the corrected live `CHANGELOG.md` sentence so the two copies cannot drift apart again. |
| 11 | `### Decision 7` + Slice 1 helpers checkbox | 2 | The inline `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)` disjunction replaced by `_is_relay_shaped(cls, interfaces)`, added as a fourth module-scope-helper sub-check with its single-source-of-truth docstring. |
| 12 | `### Decision 1` post-Slice-1 sample + Slice 1 collection checkbox | 3 | Both comprehensions gained the `and field.name not in auto_annotated_fields` clause, with a sentence saying it arrived with the later `auto`-typed-annotations card and does not change this card's contract. |
| 13 | `## Current state` code block and `### Decision 6` prose | 4 | `_consumer_assigned_fields(cls.__dict__, fields)` → `_consumer_assigned_fields(cls, fields)`; Decision 6's prose now says the function takes the class and walks `cls.__dict__` internally. |
| 14 | `### Decision 2` | 5 | "the only short-circuit input to `_build_annotations`" → the union is read by `_build_annotations` **and** by `_validate_nullability_override_targets`, `_validate_filesystem_path_targets`, `_validate_relation_shape_targets`. The rejected four-parameter alternative moved to the rationale; the vindication stayed. |
| 15 | `## Slice checklist`, Slice 5 KANBAN bullet | 6 | "move `DONE-019-0.0.6` → `DONE-019-0.0.6`" → "the card lands in the Done section as `DONE-019-0.0.6`, and no in-flight entry for it remains." |
| 16 | `## Definition of done`, KANBAN item | 6 | The matching self-contradiction ("shows `DONE-019-0.0.6`; `DONE-019-0.0.6` is no longer present") rewritten to the same landed end state. |
| 17 | `## Slice checklist`, Slice 5 archive bullet | 7 | "stays at its working location; archival is the maintainer's call" → the archived reality, naming the paths and the `NEXT.md` Step 8 sweep that performed the move, and keeping the DoD's non-gating on it. |
| 18 | `## Slice checklist` Slice 5 CHANGELOG bullet + `## Definition of done` CHANGELOG item | 8 | Both now state that the entries land under `[Unreleased]` pre-cut and sit under `## [0.0.6] - 2026-05-19` at `HEAD`. |
| 19 | `## Slice checklist`, Slice 4 Prior-`0.0.6`-card note | 9 | "three cards (`spec-013-deferred_scalars`, `spec-014-meta_primary`, this card)" → "four cards: `DONE-016-0.0.6`, `DONE-017-0.0.6`, `DONE-018-0.0.6`, and this card (`DONE-019-0.0.6`)". Post-renumber **card ids**, not filenames, on the spec-018 precedent `KANBAN.md`'s `[spec-011]` sweep bullet records. |
| 20 | `### Decision 7` guard code block | new (11th divergence) | The pseudocode's outer `if has_id_annotation or has_id_assignment:` wrapper and its `if _id_annotation_is_relay_node_id(cls): pass  # Accept.` / `else: raise` shape replaced with `HEAD`'s flattened form (`if has_id_annotation and not _id_annotation_is_relay_node_id(cls):`). Semantically identical; the spec should not point a reader at a control flow the code does not have. |
| 21 | `### Decision 7a` heading | Task 2 | `Decision 7a — Converter validation bypass (H2 fix)` → `Decision 7a — Converter validation bypass`. The `(H2 fix)` suffix is a revision attribution in a heading; the six in-page anchors that referenced it were updated in the same pass and all resolve. |
| 22 | `## Implementation plan` table | Task 2 | The `Approx. line delta` column dropped (seven successive pre-build estimates for shipped work, none describing the landed diff), along with the "Total expected delta" paragraph. Files / Tests / Notes columns kept. |
| 23 | `## Test strategy`, two Relay test descriptions | 10 | `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` and `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted` rewritten to the landed mechanism, with an explicit note that each **name** is the landed spelling and predates the current mechanism. |
| 24 | `## Slice checklist`, Slice 1 unresolved-string test recipe | 10 | Recast from a prescriptive recipe into "the landed recipe, recorded as the shipped spelling, not as a choice to re-make", naming `stub_name = f"spec015_unresolved_relay_stub_{uuid.uuid4().hex}"` as the landed identifier and stating it is deliberately not renamed. |
| 25 | Whole file | Task 2 | Every "Worker 1 picks during planning" / "Worker 1 may override" hedge (24 occurrences) removed: each named a choice a later revision or the build itself already made, and a spec that still poses a settled question invites re-litigation. Where the alternative retained real value it is stated as an equivalent discharge (e.g. parametrizing the direct-inheritance reject test) rather than as an open decision. |

**Deferral reasons for un-ticked boxes.** Exactly one box in `### Dispatched findings checklist` is `- [ ]`:

- **Finding 10** — target: the deferred-work catalog below, for a future maintainer follow-up. Reason: the `spec015_*` identifiers are test-local synthetic strings with no cross-file consumer; renaming them is a code edit with no correctness payoff and a real collision risk against the concurrent session's dirty copy of `tests/types/test_definition_order.py`. The plan explicitly directs "do not rename".

### Notes for Worker 1 (spec reconciliation)

Carried for the integration pass and the final gate. The first two are the plan's findings 9 and 10; the rest are divergences this round's own verification surfaced that the plan's ten did not name.

1. **Finding 9's sweep-population effect (reportable, per the dispatch).** `KANBAN.md`'s `[spec-011]` renumber-sweep bullet (in `TODO-ALPHA-052-0.1.0`'s section) names `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md` as still carrying the pre-renumber filename `spec-013-deferred_scalars` and a second, `spec-014-meta_primary`, in the same sentence. **Both are retired by this round**, exactly as the spec-018 residual cycle retired its own occurrence. Re-derivable: `grep -c "spec-013" docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md` reported **1** before this round and reports **0** after. The sweep card should re-derive its population rather than carry an older reading forward; spec-019 is no longer in it. The bullet's own text already warns against re-adding spec-018 from an older reading — the same caution now applies to spec-019.
2. **Finding 10 — the `spec015_*` identifiers, deferred.** `tests/types/test_definition_order.py` uses `app_label = "test_spec015_unsupported"`, `"test_spec015_grouped_choices"`, `"test_spec015_co_resident"`, and `stub_name = f"spec015_unresolved_relay_stub_{uuid.uuid4().hex}"`. Landed spelling recorded in the spec; not renamed.
3. **New: two landed test names describe a retired mechanism.** `test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` and `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted` are named for fail-soft sub-cases 1 and 2, which no longer exist as a mechanism. Both still pin real, current contracts. Additionally, the second test carries an inline comment reading "the fail-soft annotation walk accepts the directly-resolved NodeID-marked id even when another annotation on the same class fails to resolve" — the *behavior* is right, the *vocabulary* is retired, and under the landed mechanism the independence is structural rather than a recovery. A future card opening that file could retitle both and reword the comment; this round writes no code.
4. **New: `KANBAN.md`'s live `DONE-019-0.0.6` body still describes the retired mechanism.** The spec's verbatim copy was corrected this round; the live card body was not. It is DB-backed — `scripts/build_kanban_md.py` renders `KANBAN.md` from the fakeshop kanban app's DB — so the fix is a DB edit plus a regenerate, out of a documentation cycle's scope, and hazardous while a concurrent session holds `examples/fakeshop/db.sqlite3` open (`START.md` "Concurrent sessions"). The two copies now disagree, and the spec's is the correct one.
5. **New: the guard's control flow diverged from the pseudocode** (artifact row 20). Recorded here as well as fixed, because it is an eleventh item the plan's list did not carry: the plan verified the guard's *contract* but not its *shape*, and a spec pseudocode block that a builder copies mechanically is exactly the surface where shape matters.
6. **Confirmed, not an edit: `docs/GLOSSARY.md` needs no correction.** The `Scalar field override semantics` entry was read end to end for finding 1's defect class. It states the contract — `id: relay.NodeID[...]` accepted in direct, PEP 563 / stringified, and mixed forms — and **names no detection mechanism anywhere**, so nothing in it was falsified by `2bcd7f96`. Correct as written; deliberately untouched.
7. **Not this round's to fix: the `[015-…]` CHANGELOG tracking label.** Left alone per the plan, because it belongs to the `[spec-011]`/`[spec-013]` renumber cluster `KANBAN.md` tracks and half-fixing a cluster leaves it divergently rather than uniformly wrong. Its link definition resolves correctly, so the label alone is the artifact.

### Summary

This round delivered the rationale extraction that pre-flight step 7 never ran for card 019, reconciled the spec to `HEAD`, corrected one false claim about shipped code in a shipped doc, and independently confirmed that nothing was skipped in the code.

- **Rationale MOVE.** `docs/SPECS/appx/spec-019-consumer_overrides_scalar-0_0_6-rationale.md` created (47,488 bytes); the spec fell from 181,073 to 104,017 bytes and carries **zero** surviving revision attributions, down from 182. The pair total fell by 29,568 bytes — the falsified prose that was deleted rather than moved.
- **Reconciliation.** All ten plan findings worked, nine fixed in the spec and one (the `spec015_*` identifiers) deliberately recorded-not-renamed. An eleventh divergence — the guard's flattened control flow — was surfaced by this round's own reading and fixed.
- **One live-doc correction.** `CHANGELOG.md`'s `## [0.0.6]` Relay-guard `Added` entry asserted a `typing.get_type_hints` fail-soft mechanism that commit `2bcd7f96` retired two days after the release. One sentence replaced; nothing else in the file touched. `docs/GLOSSARY.md` was read for the same defect and confirmed correct as written.
- **No code gap.** All 19 Slice-1 test names exist under their own names at their mandated placements; Slice 2's deletion happened; Slice 3's docstring is live; Slice 4 is long past; Slice 5's docs half holds end to end. `286 passed` on the focused suite. **No code round is needed.**

Final status: **`final-accepted`**.
