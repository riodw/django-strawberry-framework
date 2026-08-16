# Build: R3 — documentation completion and archive audit

Spec reference: `docs/SPECS/spec-010-foundation-0_0_4.md` (whole file; `## Cross-references` and the `<!-- LINK DEFINITIONS -->` block carry the edits)
Rationale companion: `docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md`
Build plan: `docs/builder/build-010-foundation-0_0_4.md` (`### R3 findings — the archive is not clean`, F17-F19)
Status: final-accepted

**Shape note.** This item was dispatched to Worker 1 alone — no Worker 2, no Worker 3 — because all three findings live inside the spec file, which `docs/builder/BUILD.md` `## Spec reconciliation` makes Worker 1's exclusively, and because the item lands no package source and no test. The planning pass, the work, and the final-verification pass therefore run in one spawn and are recorded in one artifact with both sets of sections present, the way `docs/builder/bld-003-final.md` records its own single-pass shape. `docs/builder/ARTIFACT.md`'s `## Build report (Worker 2)` and `## Review (Worker 3)` sections are not applicable; the work record lives under `## Work record (Worker 1)` below, and `## Final verification (Worker 1)` carries the verification that would otherwise be a separate spawn's. The build plan's `## Dispatch record` declares this shape in advance and names the one condition that would break it — a `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, or kanban-DB edit turning out to be owed, which is a Worker 0 re-partition rather than a Worker 1 edit. That condition was tested and did **not** fire; see `### Maintainer escalations`.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable, for the cycle's standing reason rather than a skip: `docs/builder/worker-1.md` `### Package-wide helper inventory before helper planning` gates *proposing helper-like logic*, and this pass proposes none. It also cannot be stale-by-neglect — `git diff -- django_strawberry_framework/ | wc -l` returns **0**, so no package source has moved for the whole cycle. No inventory was refreshed and none was needed.
- **Existing patterns reused.** The link-definition block, its `<!-- LINK DEFINITIONS -->` delimiter, and all ten canonical group headers already existed in the spec and every existing definition already resolved on disk, so this pass **extends a working block** rather than repairing one. Group selection follows `START.md` "Group = where the **target** lives, NOT the source", and `docs/SPECS/appx/` shares its parent's `<!-- docs/SPECS/ -->` group under the closed-list rule in the same section. The rationale companion's four definitions are the worked example of the two-level archive depth and were re-derived rather than assumed.
- **New helpers justified.** None; this pass writes Markdown only.
- **Duplication risk avoided.** One live risk, and it is the F18 class: "fix the link" and "fix the label" are two different repairs, and doing only the mechanical one leaves the file with a path and a display text that disagree — the exact defect, one line down. The plan therefore fixed the **label** for F18 (the path was already right by accident) and stated the intent judgement in the rationale, where a link checker's blind spot becomes a durable artifact. Second risk avoided: converting the third-party `strawberry_django/...:NNN` citations "while in here" would have turned a working, deliberately-pinned citation style into a broken one; they are declared out of scope by the spec's own `## What we take from strawberry-graphql-django` and defended in the rationale's `## Standing notes`.

### Implementation steps

1. Read the required standing docs, the active spec, the active rationale, the build plan's R3 section, and all three closed `bld-010-*` artifacts.
2. Re-derive the eight inline links and their on-disk resolution from `docs/SPECS/` rather than quoting the plan's measurement.
3. F18: settle intent from evidence (root README's own documentation map, its section list, and this spec's own doc obligations), then fix the label and the description.
4. F17 + F19: convert all eight to `[text][ref-id]`, correcting the three broken paths in the definitions, alphabetical within the group chosen by target location.
5. Key a rationale entry to each of F17 / F18 / F19, with F18 carrying the intent reasoning and both rejected alternatives.
6. Run the archive audit against `docs/SPECS/NEXT.md` Step 8's three link-rot classes for spec-010 specifically, plus the companion-split check.
7. Run the documentation-completion audit over the six consumer-facing surfaces, verifying rather than inheriting Worker 0's pre-dispatch reading, and specifically reconciling the glossary's shape list against the spec's four-shape enumeration and the four test rows.
8. Run the path-resolution sweep, the dangling-reference sweep, `check_spec_glossary.py`, the markdown scaffold check, and ruff.
9. Append a memory entry.

### Test additions / updates

None. This item lands no package source and no test. A focused `pytest` run was optional per the dispatch and was not run: the diff is two Markdown files, and nothing in it is reachable from the test tree. The verification this item owes is the path-resolution sweep, recorded in full under `### Path-resolution sweep` below.

### Implementation discretion items

None reserved. The item has no downstream worker, so nothing is delegable.

### Dispatched findings checklist

R3 is a review-round-shaped item against a spec with no live `## Slice checklist`, so per `docs/builder/worker-1.md` planning step 8 the boxes below are the dispatched findings plus the item's named obligations. Worker 1 both performs and ticks; each box cites the evidence in this artifact that discharges it.

- [x] **F17** — `../GOAL.md`, `../TODAY.md`, `TREE.md` corrected to `../../GOAL.md`, `../../TODAY.md`, `../TREE.md`; all three proved to exist on disk (`### Path-resolution sweep`).
- [x] **F18** — the masked `../README.md` settled by a stated intent judgement, not a mechanical fix; reasoning and both rejected alternatives keyed into the rationale.
- [x] **F19** — all eight inline cross-file links converted to reference-style, definitions alphabetical within the group chosen by target location; count measured before and after with the command quoted.
- [x] Third-party `strawberry_django/…:NNN` / `graphene_django/…` / `graphene/…` citations, in-page anchors, and fenced-code content left inline.
- [x] Documentation completion audited across root `README.md`, `docs/README.md`, `docs/GLOSSARY.md` (three anchors), `TODAY.md`, `docs/TREE.md`, and `KANBAN.md`'s `DONE-010-0.0.4` row — verified, not inherited.
- [x] The glossary's supported forward-reference / manual relation shapes list reconciled against the spec's four-shape enumeration **and** against the four landed test rows.
- [x] F14's residue confirmed fixed and consistent; no surviving `docs/FEATURES.md` reference in the spec.
- [x] Step 8 Class 1 (references **TO** spec-010) walked, including `SpecDoc.path` as rendered into `KANBAN.md`; read-only, no edit.
- [x] Step 8 Class 2 (references **FROM** spec-010) — F17/F18/F19; closed above.
- [x] Step 8 Class 3 (between specs that both moved) — the four spec-008 / spec-009 references confirmed to resolve.
- [x] Companion split confirmed: spec at `docs/SPECS/`, `-terms.csv` and `-rationale.md` at `docs/SPECS/appx/`, and the rationale's four definitions re-derived at the two-level depth.
- [x] `docs/SPECS/spec-009-…md` and `spec-008-…md` opened **read-only** and only to confirm an anchor resolves; neither citation repointed.
- [x] `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-010-foundation-0_0_4.md` re-run after the edits, exits 0.
- [x] `scripts/check_trailing_commas.py --check` re-run over both files, exits 0; ten group headers intact and in order.
- [x] `uv run ruff format .` and `uv run ruff check --fix .` run; both no-ops, as a Markdown-only pass should be.
- [x] No `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, or `db.sqlite3` edit made; the escalation condition tested and recorded.
- [x] `docs/SPECS/appx/spec-010-foundation-0_0_4-terms.csv` untouched; the edits name no new glossary anchor and remove none.
- [x] Every count command-produced, with the command quoted beside it, counted as occurrences.
- [x] No commit, no branch, no `git stash` / `checkout` / `restore` / `worktree`; no package source or test file written; no baseline-dirty path touched.

---

## Work record (Worker 1)

### Files touched

- `docs/SPECS/spec-010-foundation-0_0_4.md` — eight inline cross-file links converted to reference-style; three broken paths corrected; the F18 entry's label and description corrected; six new link definitions added across two groups.
- `docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md` — new `## Archive pass — the links the move left behind` section with one entry per finding.
- `docs/builder/bld-010-r3-doc_completion_archive.md` — this file.
- `docs/builder/worker-memory/worker-1.md` — one appended entry.

Nothing else. `git diff --stat` over the two spec-family files reports `800 insertions(+), 125 deletions(-)`, which **includes R1's uncommitted edits** to the same two files — R1 is closed and its diff is still in the working tree, so a stat over these paths cannot isolate this pass. The enumeration above is the authoritative statement of what R3 changed.

### The eight links, before and after

Measured before the edits:

```shell
$ grep -o '](' docs/SPECS/spec-010-foundation-0_0_4.md | wc -l
       8
```

Every one of the eight was a cross-file link (the `grep -v '](#'` filter removed nothing), matching the plan's F19 measurement exactly: 1 each of `../GOAL.md`, `../README.md`, `../TODAY.md`, `TREE.md`, and 2 each of `](spec-008-…)` and `](spec-009-…)`.

| Site | Before | After | Finding |
|---|---|---|---|
| `## Purpose` bullet 1 | `](spec-008-definition_order_independence-0_0_4.md)` | `[spec-008]` | F19 |
| `## Purpose` bullet 2 | `](spec-009-rich_schema_architecture-0_0_4.md)` | `[spec-009]` | F19 |
| `## Cross-references` 1 | `](spec-008-definition_order_independence-0_0_4.md)` | `[spec-008]` | F19 |
| `## Cross-references` 2 | `](spec-009-rich_schema_architecture-0_0_4.md)` | `[spec-009]` | F19 |
| `## Cross-references` 3 | `` [`README.md`](../README.md) `` | `` [`docs/README.md`][docs-readme] `` + corrected description | **F18** + F19 |
| `## Cross-references` 4 | `](../GOAL.md)` — broken | `[goal]` -> `../../GOAL.md` | F17 + F19 |
| `## Cross-references` 5 | `](../TODAY.md)` — broken | `[today]` -> `../../TODAY.md` | F17 + F19 |
| `## Cross-references` 6 | `](TREE.md)` — broken | `[tree]` -> `../TREE.md` | F17 + F19 |

Measured after:

```shell
$ grep -n '](' docs/SPECS/spec-010-foundation-0_0_4.md | grep -v '](#'
$ echo $?
1
```

Zero remaining inline cross-file links. Six definitions were added — four under `<!-- Root -->` (`contributing`, `goal`, `readme`, `today`), two under `<!-- docs/ -->` (`docs-readme`, `tree`) — plus two under `<!-- docs/SPECS/ -->` (`spec-008`, `spec-009`), each alphabetical within its group and grouped by where the target lives. `[contributing]` and `[readme]` are new uses introduced by F18's corrected description, not conversions.

### F18 — the intent judgement

The finding is that `../README.md` **resolves** from `docs/SPECS/`, to `docs/README.md`, while its display text said `README.md` and its label said "Operational entry point, install/test/build". A link checker follows the path, finds a file, and reports the link healthy; only intent settles it.

Verified mechanically first:

```shell
$ cd docs/SPECS && ls ../README.md ../../README.md
../README.md      ../../README.md
```

Both exist — that is precisely why the rot is masked rather than visible.

**Decision: the reference intends `docs/README.md`.** Three independent readings agree.

1. **The root README's own documentation map.** `README.md` `## Project documentation` labels `docs/README.md` "install, quick start, walkthrough, status" and `CONTRIBUTING.md` "dev setup, format, test, build, publish". Between them they are the spec label's "install/test/build" — and neither of them is the root README itself.
2. **The root README's section list.** `## Why this package exists`, `## Why it's fast`, `## Is this for you?`, `## Status`, `## Get started → docs/README.md`, `## Project documentation`. It is positioning, and it explicitly delegates getting started. A file that delegates getting started is not the operational entry point. `START.md` `## What this repo is` says the same thing in one word: "`README.md` = positioning".
3. **This spec's own contract.** `## Strawberry finalization strategy` locates the earliest-safe-call-point boundary, the single-threaded lifecycle window, the module-discovery note, and the correct/wrong-order snippet pair in `docs/README.md` — three separate sentences, all naming that file, all placed there by R1's F14 fix.

Because the path was already right by accident, **the label was the error and the label is what moved.** The entry now names `docs/README.md` and its description states what that file actually carries. Restating "test/build" against a file with no build section would have re-created the same defect class one line down, so the description also names `CONTRIBUTING.md` for the contributor workflow and the root `README.md` for the public-API list and landing snippet that `## Phased implementation order` step 10 assigns it — which keeps both files reachable without inventing extra cross-reference rows, and removes the "but a cited file vanished from the list" objection that would otherwise re-open the question.

Both rejected alternatives (repoint to the root README; repoint to `CONTRIBUTING.md`) are recorded in the rationale with the one-line reason each lost.

### Path-resolution sweep

`START.md`: "the convention makes link rot visible, not impossible" — so every rewritten path is disk-checked before the move is called done. The sweep covers **both** files' complete definition blocks, not just the changed lines.

```shell
$ uv run python - <<'PY'
import re, pathlib
for src in ["docs/SPECS/spec-010-foundation-0_0_4.md", "docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md"]:
    p = pathlib.Path(src)
    print(f"--- {src}")
    for line in p.read_text().splitlines():
        m = re.match(r"^\[([^\]]+)\]:\s+(\S+)$", line)
        if not m:
            continue
        ref, target = m.groups()
        path = target.split("#")[0]
        if path.startswith(("http://", "https://")):
            print(f"  URL  [{ref}] {target}")
            continue
        resolved = (p.parent / path).resolve()
        print(f"  {'OK  ' if resolved.exists() else 'MISS'} [{ref}] -> {target}")
PY
--- docs/SPECS/spec-010-foundation-0_0_4.md
  OK   [contributing] -> ../../CONTRIBUTING.md
  OK   [goal] -> ../../GOAL.md
  OK   [readme] -> ../../README.md
  OK   [today] -> ../../TODAY.md
  OK   [docs-readme] -> ../README.md
  OK   [glossary-choice-enum-generation] -> ../GLOSSARY.md#choice-enum-generation
  OK   [glossary-configurationerror] -> ../GLOSSARY.md#configurationerror
  OK   [glossary-definition-order-independence] -> ../GLOSSARY.md#definition-order-independence
  OK   [glossary-djangoconnectionfield] -> ../GLOSSARY.md#djangoconnectionfield
  OK   [glossary-djangonodefield] -> ../GLOSSARY.md#djangonodefield
  OK   [glossary-djangooptimizerextension] -> ../GLOSSARY.md#djangooptimizerextension
  OK   [glossary-djangotype] -> ../GLOSSARY.md#djangotype
  OK   [glossary-finalize-django-types] -> ../GLOSSARY.md#finalize_django_types
  OK   [glossary-metafields] -> ../GLOSSARY.md#metafields
  OK   [glossary-metaprimary] -> ../GLOSSARY.md#metaprimary
  OK   [glossary-optimizerhint] -> ../GLOSSARY.md#optimizerhint
  OK   [glossary-schema-audit] -> ../GLOSSARY.md#schema-audit
  OK   [tree] -> ../TREE.md
  OK   [spec-008] -> spec-008-definition_order_independence-0_0_4.md
  OK   [spec-009] -> spec-009-rich_schema_architecture-0_0_4.md
  OK   [spec-010-rationale] -> appx/spec-010-foundation-0_0_4-rationale.md
--- docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md
  OK   [glossary] -> ../../GLOSSARY.md
  OK   [spec-009] -> ../spec-009-rich_schema_architecture-0_0_4.md
  OK   [spec-010] -> ../spec-010-foundation-0_0_4.md
  OK   [build] -> ../../builder/BUILD.md
```

**25 definitions, 25 `OK`, 0 `MISS`.** F17 and F18 are closed by this output: the three formerly-broken targets are `[goal]`, `[today]`, `[tree]`, and they resolve.

The reciprocal sweep — every `[ref-id]` *use* in the body has a definition, and every definition is used — also runs clean on both files (`dangling uses: []`, `unused defs: []`), which is what proves the conversion left no half-converted link behind.

### Archive audit — `docs/SPECS/NEXT.md` Step 8, all three classes

**Class 1 — references TO the moved spec.** Every path-shaped reference to `spec-010-foundation-0_0_4.md` outside this cycle's own artifacts, and its resolution from its own source directory:

```shell
$ grep -rn "spec-010-foundation-0_0_4" . --include="*.md" | grep -E "\]:|\]\(" | grep -v "docs/builder/b"
```

| Source | Target as written | Resolves |
|---|---|---|
| `KANBAN.md:137` (`## WIP / DONE spec map` row) | `docs/SPECS/spec-010-foundation-0_0_4.md` | OK |
| `KANBAN.md:4605` (card body `Spec:` line) | `docs/SPECS/spec-010-foundation-0_0_4.md` | OK |
| `docs/SPECS/spec-008-…md:222-227` (6 defs, 5 of them anchored) | `spec-010-foundation-0_0_4.md` | OK |
| `docs/SPECS/spec-009-…md:1085` | `spec-010-foundation-0_0_4.md` | OK |
| `docs/SPECS/spec-036-…md:665`, `spec-038-…md:2507` | `spec-010-foundation-0_0_4.md` | OK |
| `docs/SPECS/appx/spec-005-…-rationale.md:692`, `spec-008-…-rationale.md:1022`, `spec-009-…-rationale.md:616`, `spec-010-…-rationale.md:685` | `../spec-010-foundation-0_0_4.md` | OK |

Both `KANBAN.md` sites render from the one `SpecDoc` for card 010 (`apps/kanban/models.py::SpecDoc.path`, read by `scripts/build_kanban_md.py::spec_paths_for_card`), so the two rows above are one stored value and it is already correct. Worker 0's pre-dispatch reading confirmed; **no edit, and none owed.**

Spec-008's five *anchored* inbound definitions were checked against this spec's current heading list, because R1 renamed one heading in this cycle and a heading rename is the one edit class that silently breaks an inbound anchor:

| Inbound anchor | Heading it targets | Present |
|---|---|---|
| `#test-fixtures-and-acceptance-criteria` | `## Test fixtures and acceptance criteria` | yes |
| `#unresolved-target-error-format` | `### Unresolved-target error format` | yes |
| `#finalization-phase-finalize_django_types` | ``### Finalization phase: `finalize_django_types()` `` | yes |
| `#invariants-this-slice-must-protect` | `## Invariants this slice must protect` | yes |
| `#strawberry-finalization-strategy` | `## Strawberry finalization strategy` | yes |

All five resolve. R1's rename (`### Manual annotation contract for relation fields`, which lost a `(0.0.4)` suffix) is targeted by nothing, as R1 recorded and this pass re-confirms.

**Class 2 — references FROM the moved spec.** This is F17/F18/F19, the class Step 8 says gets missed, and it is closed above and proved by `### Path-resolution sweep`.

**Class 3 — between specs that both moved.** Spec-010 holds four references to its two siblings under `docs/SPECS/` (two to spec-008, two to spec-009), all four now `[spec-008]` / `[spec-009]` resolving to bare sibling filenames. The sweep shows both `OK`. This is Step 8's "same surface, different meaning" case: the definition text a former sibling-under-`docs/` carried is textually identical to the one a sibling-under-`docs/SPECS/` needs, so it can only be verified, never inferred — which is what the sweep does.

Separately, the spec carries three `#"…"` symbol-style citations into its siblings (`AGENTS.md` rule 27, not Markdown links, correctly not converted). All three targets confirmed present, read-only:

| Citation | Target |
|---|---|
| `spec-009-…md #"### Layer 3: Finalization trigger"` | `docs/SPECS/spec-009-…md:634` |
| `spec-009-…md #"### Decision 6: fail loudly"` | `docs/SPECS/spec-009-…md:1013` |
| `spec-008-…md #"### The shape that shipped"` | present, 1 occurrence |

**No divergence from the concurrent spec-009 session was observed**, so there is nothing to record under that head and nothing was repointed. Both files were opened read-only and only to confirm resolution.

**Companion split.** Re-derived rather than inherited:

```shell
$ cd docs/SPECS && ls -d spec-010-foundation-0_0_4.md appx/spec-010-foundation-0_0_4-terms.csv appx/spec-010-foundation-0_0_4-rationale.md
```

All three present, split correctly — spec at `docs/SPECS/`, both companions at `docs/SPECS/appx/`. The rationale archived **two** levels deeper than it started, and its four definitions reflect it: `../../GLOSSARY.md`, `../../builder/BUILD.md`, `../spec-009-…md`, `../spec-010-…md`. All four `OK` in the sweep. Its two `docs/SPECS/`-group definitions sit under `<!-- docs/SPECS/ -->` rather than an invented eleventh header, per `START.md`'s closed-list rule.

### Documentation completion audit

Verified, not inherited. Worker 0's pre-dispatch reading holds in every particular.

| Surface | Checked | Result |
|---|---|---|
| root `README.md` | landing snippet imports and calls `finalize_django_types()`; `## Project documentation` map lists all eight standing docs | current |
| `docs/README.md` | `## Installation`, `## Quick start` (imports `finalize_django_types`), `## Schema setup boundary` carrying the **Recommended** and **Wrong order** snippets as a pair, the single-threaded window, and the most-common-failure-mode note | current |
| `docs/GLOSSARY.md#definition-order-independence` | status `shipped (0.0.4)`; 4 supported relation cycles; 6 supported forward-reference / manual relation shapes; the fail-loud error contract; the deferred-cardinality-validation note | current — see reconciliation below |
| `docs/GLOSSARY.md#finalize_django_types` | status `shipped (0.0.4)`; call-window sentence matches the spec's boundary word for word in substance; worked snippet present | current |
| `docs/GLOSSARY.md#djangotype` | status `shipped (0.0.5)` — the entry describes the class as it stands after spec-015, not as 0.0.4 shipped it, which is the glossary's documented job | current |
| `TODAY.md` | quick-start block imports and calls `finalize_django_types()`; the two-rules paragraph states the after-imports / before-`Schema(...)` boundary | current |
| `docs/TREE.md` | `types/finalizer.py` and `registry.py` both carry docstring-derived one-liners naming the finalization gate and the pending-relation registry | current |
| `KANBAN.md` `DONE-010-0.0.4` | six shipped bullets; the manual-override bullet states the annotation-only / assigned split correctly | current as history — see `### Maintainer escalations` |

**The specific reconciliation this item was told to run.** R2 and R2b made the glossary's "supported forward-reference / manual relation shapes" list fully test-backed for the first time, so the list, the spec's four-shape enumeration, and the landed rows must now agree. They do:

| Glossary bullet | Spec's `Tests cover all four shapes` | Landed row |
|---|---|---|
| generated relation annotations for targets declared before or after the source | (the cyclic acceptance tests, not an override shape) | the cyclic rows |
| same-module string annotations `items: list["ItemType"]` | — | `::test_same_module_string_forward_reference_annotation_survives_finalization` |
| stringified annotations from `from __future__ import annotations` | — | the `branch_module` / `shelf_module` fixtures |
| cross-module `Annotated[…, strawberry.lazy("module.path")]` | shape 2 — `list[Annotated["ItemType", strawberry.lazy(…)]]` | `::test_cross_module_lazy_relation_override_types_the_field_as_the_referenced_class` (+ its `primary=True` discriminator sibling `::…_wins_over_the_registered_primary_type`) |
| annotation-only relation overrides, which keep the generated resolver | shape 1 — `items: list["ItemType"]` | `::test_annotation_only_relation_override_keeps_generated_resolver` |
| `strawberry.field(resolver=…)` **and** `@strawberry.field` relation overrides, which keep the consumer resolver | shapes 3 and 4 | `::test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver` (R2b) and `::test_assigned_relation_field_override_keeps_consumer_resolver` |

Four spec shapes, four rows, one-to-one; the glossary's sixth bullet covers spec shapes 3 and 4 in one line and is now backed by both rows rather than one. The glossary's fourth bullet elides the annotated type inside the marker — R2's final pass already ruled that unspecific rather than wrong, and this pass concurs: the placement rule that R2 added is normative and belongs in the contract document, and the glossary is DB-generated. **No glossary edit is owed.**

**F14's residue.** R1's fix is complete and consistent. `grep -c "FEATURES.md" docs/SPECS/spec-010-foundation-0_0_4.md` returns **0**. `## Phased implementation order` step 10 now names `README.md` for the public-API list and landing snippet and `docs/README.md` for the quick-start plus the schema-setup boundary with the correct/wrong-order pair — which matches both files on disk exactly. No residue survives, and this pass's F18 fix is the same judgement applied one section further down, in `## Cross-references`, where R1's F14 sweep did not reach because the entry there was a link rather than a prose location claim.

**Staged-anchor sweep.** `grep -rn "TODO(spec-010" . --include="*.py" --include="*.md"` returns exactly one hit, in `docs/builder/bld-010-r2b-assigned_override_coverage.md`, and it is prose *about* the sweep rather than an anchor. Zero staged anchors in source. (The tree-wide sweep is `bld-010-final.md`'s obligation; recorded here because this item is the cycle's doc-wrap.)

### Validation run

| Command | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-010-foundation-0_0_4.md` | `OK: 12 terms - all have glossary entries and at least one spec link.` exit 0 |
| `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-010-foundation-0_0_4.md docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md` | exit 0 — ten group headers present, in order |
| `uv run ruff format .` | `419 files left unchanged` |
| `uv run ruff check --fix .` | `All checks passed!` |
| `git status --porcelain \| wc -l` | 143 (was 141 at spawn; the delta is the concurrent session's, plus this artifact) |

Both ruff runs are no-ops, as a Markdown-only pass should be. The terms CSV was not touched and did not need to be: the edits add no glossary anchor and remove none, which is why `check_spec_glossary.py` still reports the same 12 terms as the pre-flight run did.

### Implementation notes

- **`[docs-readme]` rather than `[readme]` for `docs/README.md`.** The spec now references both READMEs, so the ref-ids must be distinguishable at the point of use. `[readme]` is kept for the root file to match every other standing doc in the repo (`START.md`, `docs/README.md`, `CONTRIBUTING.md` all use `[readme]` for the root README), and the qualified id goes to the file that needs qualifying.
- **Group placement of `[docs-readme]` and `[tree]`.** Both targets live under `docs/`, so both sit under `<!-- docs/ -->` even though the source file lives under `docs/SPECS/` — `START.md`'s "group by where the **target** lives" rule. `[docs-readme]` sorts before the `glossary-*` block and `[tree]` after it.
- **The F18 description names three files in one bullet.** Deliberate, and the alternative was three bullets. One bullet keeps `## Cross-references` a list of *destinations for a reader with a question* rather than a file index, and it makes the disambiguation legible at the point where the ambiguity existed.

### Notes for Worker 1 (spec reconciliation)

Two items for the final gate. Neither is a source defect, and neither blocks this item.

1. **`KANBAN.md`'s `DONE-010-0.0.4` reserved-slot list is correct as history but reads as present tense.** The card body says `DjangoTypeDefinition` carries "forward-reserved slots (`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`, `interfaces`) ready for Layer 3 to populate". R1's F7 established that at `HEAD` only `fields_class` is reserved-and-unused, and that `aggregate_class` / `search_fields` are **rejected** `Meta` keys with no slot at all. The card is nonetheless accurate as a record of what 0.0.4 shipped — `git log -S "aggregate_class" -- django_strawberry_framework/types/definition.py` shows both names introduced at `27d62919` (the foundation slice) and removed at `f83bb71b`, i.e. after 0.0.4. This is the same class R1 ruled on for the Phase-0 spike record: a present-tense survival that is correct as history. **No edit made and, on this reading, none owed** — which is why it is not an escalation. Recorded because the reading is a judgement and `KANBAN.md` is DB-backed, so if the maintainer draws the boundary elsewhere the fix is a kanban-DB edit plus a re-render, never a hand-edit of the rendered file.
2. **`KANBAN.md` lines 335-336 carry two carded, still-open observations about this spec** — that its two inbound citations into spec-009 resolve to something other than the claim they are cited for, and that it holds the board's largest single rule-27 debt (42 raw `path:NN` occurrences on 30 lines, measured 2026-08-14). Both are *semantic* claims about citation content and source-reference style, not link rot, and both are owned by a board card rather than by this cycle. This pass verified only that the three `#"…"` citation targets **exist**; it did not and could not adjudicate whether each supports the claim it is cited for, which is the carded work. Flagged so the final gate does not read this item's clean Class-3 result as closing them.

### Maintainer escalations

**None.** The dispatch's one stop-and-record condition — a `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, or kanban-DB edit turning out to be genuinely owed — was tested against all four surfaces and **did not fire**:

- `docs/GLOSSARY.md#definition-order-independence` — reconciled against the spec's four shapes and the four landed rows; agrees. The elided `Annotated[…]` bullet is unspecific rather than wrong, as R2 already ruled. No edit owed.
- `docs/GLOSSARY.md#finalize_django_types`, `#djangotype` — both current. No edit owed.
- `KANBAN.md` `DONE-010-0.0.4` — correct as a historical record, evidenced by `git log -S` above. No edit owed; the judgement is recorded as note 1 rather than escalated, because escalating a non-defect would cost a Worker 2 re-partition for nothing.
- `KANBAN.md` / `KANBAN.html` `SpecDoc.path` for card 010 — already `docs/SPECS/spec-010-foundation-0_0_4.md` on both rendered surfaces. No edit owed.

So this item completes whole, and `Status: final-accepted` covers all of it rather than a part.

---

## Final verification (Worker 1)

- **Spec status-line re-verification (every Worker 1 spawn).** Lines 1-3 read as the title, the glossary-linked subject, and the rationale-companion pointer. R1 rewrote the pointer's contents list in this cycle to include the reconciliation record; R2 and R2b added no new class of content to the rationale (their entries are keyed decisions of the same shape), and this pass's `## Archive pass` section is likewise covered by the pointer's existing "this spec's change record" clause. **No status-line edit was owed and none was made.**
- **Dispatched findings checklist.** Every box above is `- [x]` and each cites its evidence in this artifact. No box is deferred, so no deferral reason is owed under `### Spec changes made (Worker 1 only)`.
- **DRY check across this item and the three prior accepted items.** No new duplication. This item introduces no helper, constant, literal, or test shape; its only repeated construct is the link-definition block, which is a `START.md`-mandated scaffold rather than a duplication. The one near-miss the plan flagged — a second cross-reference row for the root README, duplicating what `## Phased implementation order` step 10 already says — was avoided by naming the file inside the existing bullet instead.
- **Prior artifacts read in full.** `bld-010-r1-spec_reconciliation.md`, `bld-010-r2-lazy_override_coverage.md`, `bld-010-r2b-assigned_override_coverage.md`, all read-only and complete, per `docs/builder/BUILD.md` `## Cross-slice integration pass`'s no-"as-needed" rule. R1's `### Notes for Worker 1` item 2 was the load-bearing one: it defines the correct-as-history boundary this pass applied twice, to the Phase-0 spike record (left alone) and to the KANBAN card body (left alone).
- **Failability and fail-open checks.** Not applicable and the obligation does not attach: `docs/builder/BUILD.md` `### What needs a proof` attaches it to **new boundaries**, and this item's diff is two Markdown files with zero package source and zero test. Stated rather than omitted, because R2b's final pass established that checking whether the obligation attaches is what makes the answer honest.
- **Relocation / promotion claims.** One, and it is the item's central claim: that F17's three broken targets now resolve. Proved by running the sweep in this artifact rather than by reading it off a prior pass — 25 definitions, 25 `OK`, 0 `MISS`, command and full output quoted.
- **Existing tests.** None run; the item lands no code, and the dispatch made a focused run optional. Nothing in the diff is reachable from the test tree.
- **Floor verification.** `No floor-verification scope declared.` — the build plan declares `none` for R3.
- **Hot path.** `Not applicable; plan declares no hot path.` R3 writes Markdown only.
- **Spec reconciliation.** Complete; see below.
- **Final status:** `final-accepted`.

### Summary

R3 closed the spec-010 archive. All eight of the spec's inline cross-file links are now reference-style with definitions in the existing bottom block; the three targets that resolved to nothing from `docs/SPECS/` resolve; and the fourth — the one that resolved to the *wrong* existing file and that no checker could ever have flagged — was settled by an evidence-backed intent judgement and corrected at the label rather than the path. Twenty-five link definitions across the spec and its rationale were disk-checked, with zero misses. All three of `docs/SPECS/NEXT.md` Step 8's link-rot classes were walked for spec-010: Class 1 is clean and needed no edit (the kanban `SpecDoc.path` is already correct on both rendered surfaces, and all five of spec-008's inbound anchors survive R1's heading rename), Class 2 was the finding set, and Class 3's four sibling references all resolve. The companion split is right and the rationale's two-level depth was re-derived. The documentation-completion audit verified all six consumer-facing surfaces independently of Worker 0's reading and found them current, including the specific reconciliation this item was told to run: the glossary's six shape bullets, the spec's four-shape enumeration, and the four landed test rows now agree one-to-one, which they did not before R2 and R2b. No `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, or kanban-DB edit was owed, so the dispatch's stop-and-escalate condition did not fire and the item completes whole.

### Spec changes made (Worker 1 only)

Each edit is keyed to its finding, cites the spec section by its own heading (the durable address; `AGENTS.md` rule 27 permits raw `path:NN` only inside a per-cycle artifact like this one), and carries a one-line reason.

| # | Spec section | Edit | Reason |
|---|---|---|---|
| F19 | `## Purpose` (2 bullets) | `](spec-008-…)` / `](spec-009-…)` become `[spec-008]` / `[spec-009]` | `AGENTS.md` rule 28: cross-file links are reference-style so the next relocation touches definitions, not prose |
| F19 | `## Cross-references` (bullets 1-2) | same conversion for the two sibling references | same |
| **F18** | `## Cross-references` (bullet 3) | `` [`README.md`](../README.md) `` becomes `` [`docs/README.md`][docs-readme] ``, and the description is corrected to what that file carries, naming `CONTRIBUTING.md` for the contributor workflow and the root `README.md` for the public-API list and landing snippet | The path resolved to `docs/README.md` while the label named the root README; the operational entry point is `docs/README.md`, so the label was the error. Reasoning and both rejected alternatives keyed into the rationale |
| F17 + F19 | `## Cross-references` (bullets 4-6) | `](../GOAL.md)`, `](../TODAY.md)`, `](TREE.md)` become `[goal]`, `[today]`, `[tree]`, with definitions `../../GOAL.md`, `../../TODAY.md`, `../TREE.md` | All three resolved to nothing from the archived depth — Step 8's "failure mode that gets missed", because the move's visible diff is a rename |
| F17-F19 | `<!-- LINK DEFINITIONS -->` | 8 definitions added: `contributing`, `goal`, `readme`, `today` under `<!-- Root -->`; `docs-readme`, `tree` under `<!-- docs/ -->`; `spec-008`, `spec-009` under `<!-- docs/SPECS/ -->` | Alphabetical within the group chosen by where the target lives; all disk-checked |

**Rationale entries keyed to these changes** (`docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md`, new `## Archive pass — the links the move left behind`): one per finding, with F18 carrying the intent judgement, its three lines of evidence, and both rejected alternatives (repoint to the root README; repoint to `CONTRIBUTING.md`), and F19 carrying what was deliberately left inline and why converting the third-party pinned citations would have broken a working convention.

**Not changed, deliberately:** the third-party citations into pinned upstream snapshots; in-page `](#…)` anchors; anything inside a fenced code block; the three `#"…"` symbol-style sibling citations (verified to resolve, not repointed, per the concurrent-session constraint); `docs/SPECS/appx/spec-010-foundation-0_0_4-terms.csv`; and every generated surface.

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
