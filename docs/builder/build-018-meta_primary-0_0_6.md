# Package build plan: meta_primary / 0.0.6 (018)

Spec source: `docs/SPECS/spec-018-meta_primary-0_0_6.md` (already archived; NOT at `docs/`)
Rationale companion (to create): `docs/SPECS/appx/spec-018-meta_primary-0_0_6-rationale.md`
Terms companion (exists): `docs/SPECS/appx/spec-018-meta_primary-0_0_6-terms.csv`
Target release: `0.0.6` (shipped 2026-05-19; package is now at `0.0.14`)
Cycle type: **residual closeout cycle**, not a fresh six-slice build. Every spec slice shipped in
commit `8cec18a3` ("Finish docs/spec-014-meta_primary-0_0_6.md" — the card was renumbered 014 -> 018
by the 2026-07-30 board renumber). This cycle delivers the rationale extraction that pre-flight step 7
never ran for this card, reconciles the spec to `HEAD`, and confirms nothing was skipped in the code.
Build rule: one round at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every round must justify shared/duplicated patterns before merging.

Ownership partition: `none; single sequential round` (R1 owns the spec + the rationale file and
nothing else; a code round is only opened if R1's verification surfaces a real code gap).
Hot-path declaration: `none` (documentation-only cycle; no source file is written).
Floor-verification scope: `none` (no Django / Strawberry / channels seam is touched).

Pre-flight: run 2026-08-17 against `HEAD de2601e9`.

- **Step 1 baseline: NOT clean, and deliberately not resolved.** 62 paths are dirty/untracked from
  the maintainer's concurrent sessions (`START.md` "Concurrent sessions"). Per `AGENTS.md` rule 34
  they are out of scope: never edited, never reverted by this cycle. The maintainer directed this
  cycle to ignore concurrent work.
- **Step 2 `scripts/review_inspect.py`:** smoke invocation against `django_strawberry_framework/registry.py`
  with `--output-dir docs/shadow --stdout` succeeded.
- **Step 3 artifact reset: PARTIAL, deliberately.** No `build-018-*` / `bld-*` path for THIS cycle
  existed. The prior cycle's `docs/builder/build-017-deferred_scalars-0_0_6.md` and
  `docs/builder/bld-017-final.md` are **dirty in the working tree** (a concurrent session is writing
  them), so deleting them would clobber live work; they are left in place under rule 34. The spec's
  `-terms.csv` sibling is tracked and durable and was never a deletion candidate.
- **Step 4 `.gitignore`:** lists `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/`.
- **Step 5 scratch cleared: PARTIAL, deliberately.** `docs/builder/worker-memory/` was cleared and
  re-seeded with four empty files (it held a stale three-file set from the prior cycle).
  `docs/builder/temp-tests/` (`r1`, `r1c`, `r2`, `r4`) and `docs/shadow/` were **left intact** —
  both are gitignored and unrecoverable once deleted, and the concurrent session's artifacts above
  indicate a cycle may still be reading them.
- **Step 6 spec-doc consistency:** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-018-meta_primary-0_0_6.md`
  exits 0 (`OK: 15 terms`). It must still exit 0 after the rationale move.
- **Step 7 spec rationale extraction: NOT DONE — this cycle's headline deliverable.** Dispatched as
  R1 rather than as a gate before it, because the extraction IS the work rather than a precondition
  for it.

Baseline-dirty out-of-scope files (never edit, never revert): every path listed by `git status --short`
at cycle start, notably `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`,
`docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-rationale.md`, `docs/builder/bld-017-final.md`,
`docs/builder/build-017-deferred_scalars-0_0_6.md`, `docs/dry/dry-folder-types.md`,
`docs/review/review-0_0_14.md`, every untracked `docs/review/rev-*.md`, and the eleven dirty package
source / test files.

Tracked binary / generated files a concurrent writer can rewrite mid-cycle: `examples/fakeshop/db.sqlite3`,
`KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`. This cycle writes none of them; churn on any of them
is a concurrent writer's, not this cycle's output.

Build-wide context flags:

- **The spec is already archived.** It sits at `docs/SPECS/spec-018-meta_primary-0_0_6.md` with its
  terms CSV at `docs/SPECS/appx/`; a later spec author's `docs/SPECS/NEXT.md` Step 8 sweep moved it.
  So "archive the spec" is **already satisfied**; what is missing is the `-rationale.md` sibling in
  `docs/SPECS/appx/`. Nothing in this cycle moves the spec again.
- **The card is closed.** `KANBAN.md` carries `DONE-018-0.0.6` linked to the archived spec path, and
  `CHANGELOG.md`'s `## [0.0.6] - 2026-05-19` section carries the card's `Added` / `Changed` entries.
  No DB edit and no KANBAN / GLOSSARY regenerate is in scope.
- **The card shipped as `014`.** Every commit message, build artifact, and in-tree comment from the
  original build says `spec-014-meta_primary-0_0_6.md`. The 2026-07-30 board renumber moved it to
  `018`. Both numbers name one card; the rationale file records the mapping so a future reader
  chasing `git log` is not left guessing.

## Verified findings carried into R1 (Worker 0's pre-dispatch source verification)

Every item below was checked against source at `HEAD de2601e9` before dispatch, per
`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`.

**Result on the load-bearing question: NOTHING WAS SKIPPED IN THE CODE.** All six slices shipped.
Every one of the 19 Slice-1, 7 Slice-2, 6 Slice-3, and 17 Slice-4 test names the spec's
`## Slice checklist` pins exists in the tree under its own name (`grep -rl "def <name>" tests examples`,
run per name, zero misses). Every `## Definition of done` bullet holds. The docs half of Slice 6
holds: `docs/GLOSSARY.md` carries `Meta.primary` at `shipped (0.0.6)` with the multi-type bullet on
`DjangoType`, the index badge is flipped, `docs/README.md` and `TODAY.md` both mention the key, and
`CHANGELOG.md` carries the entries. The version quintet is long past `0.0.6`.

What the spec says and `HEAD` does not, i.e. the reconciliation list — all documentation-only:

1. **Duplicate-primary message.** Spec: `"<new> is already declared primary as <existing>"`
   (8 occurrences). `HEAD` (`django_strawberry_framework/registry.py::TypeRegistry.register`):
   `f"Cannot register {type_cls.__name__} as primary for {model.__name__}; {existing_primary.__name__} is already the primary type"`.
   Changed by commit `21212a19` ("End Bug Hunt", 2026-05-20) to carry the model name;
   `CHANGELOG.md` documents the reword. `docs/GLOSSARY.md` already quotes the corrected string, so
   the spec is the last carrier of the retired one.
2. **Audit function is private.** Spec names `audit_primary_ambiguity()` (11 occurrences);
   `HEAD` has `django_strawberry_framework/types/finalizer.py::_audit_primary_ambiguity`, renamed by
   commit `13d8dac5` ("Apply feedback", 2026-05-18) the same day the build landed.
3. **Audit signature.** Spec's Decision 5 pseudocode has the audit call
   `registry.models_with_multiple_types()` itself. `HEAD` takes
   `multi_type_models: tuple[type[models.Model], ...]` — `finalize_django_types` materializes that
   one-shot generator ONCE and feeds both this audit and spec-031's Phase-2.5
   `_audit_model_label_routing`. Landed in commit `7d892d6f` (spec-031, `0.0.9`).
4. **`register_with_definition` rollback body.** Spec's Decision 3a pseudocode still carries the
   `if type_cls in types:` guard `13d8dac5` removed, and predates the extraction of the removal into
   the shared `TypeRegistry._detach_type_from_model` helper (commit `1fb42b04`), which the later
   public `TypeRegistry.unregister` shares. The rollback CONTRACT (snapshot `_primaries`, roll back
   only what this call appended) is unchanged and correct.
5. **`resolved_relation_annotation` never called `registry.get`.** Spec's Decision 6 table and its
   Slice 4 bullet both claim `types/converters.py::resolved_relation_annotation` reads
   `target_type = registry.get(...)` and is "unchanged". At `HEAD` the helper takes `target_type` as
   a parameter and performs no registry lookup — and it already did at spec-authoring time
   (introduced that way in commit `27d62919`, `0.0.4`, two releases earlier). This claim was **false
   when written**, not broken later.
6. **Broken `#"substring"` citation.** The spec cites
   `optimizer/walker.py::_walk_selections #"registry.get(django_field.related_model)"` for the nested
   relation lookup. That exact string is absent from `walker.py` at `HEAD`: the nested lookup moved
   into `optimizer/walker.py::_resolve_relation_target`, which prefers
   `definition.related_target_for(...)` and falls back to `registry.get(related_model)` (commit
   `36da25b4`). The nested-resolves-to-primary CONTRACT still holds —
   `DjangoTypeDefinition.related_target_for` itself routes through `registry.get(target_model)` —
   only the citation rotted.
7. **`_resolve_model_from_return_type` shape.** The spec deliberately left the return shape to
   Worker 1 ("named tuple or a plain tuple"). What landed is the `_OriginAndModel` NamedTuple with
   `origin` / `model` fields, in the original build commit. The spec should name the landed shape.
8. **Registry surface grew after the card.** `TypeRegistry.unregister` and
   `TypeRegistry.register_type_teardown` (commits `b70c0360` / `1fb42b04`, both in the `0.0.6`
   window and both `CHANGELOG`-documented) are not this card's surface but share this card's
   `_primaries` / `_types` invariants.
9. **Slice 6's self-referential KANBAN instruction.** The verbatim body says to move
   `DONE-018-0.0.6` -> `DONE-018-0.0.6`; the renumber rewrote both halves of a
   `WIP-...-014` -> `DONE-014` instruction into the same string. Same defect class the spec-017 cycle
   found and recorded.
10. **`docs/FEATURES.md` no longer exists.** The original build edited it; a later docs consolidation
    deleted it. The spec's `## Doc updates` does not name it, so this is a rationale note only.

None of the ten is a code defect. **No code round is opened unless R1's own verification finds one.**

## Artifact list

- `docs/builder/bld-review-1-spec018_rationale.md` — R1: rationale extraction + spec reconciliation. **Deleted at closeout.**
- `docs/builder/bld-integration.md` — cross-round integration pass. **Deleted at closeout.**
- `docs/builder/bld-018-final.md` — final gate. Survives.

**Closeout disposition, 2026-08-18.** The two per-round artifacts were deleted at closeout by the
maintainer's instruction, **before the cycle was committed — so they appear in no commit and cannot be
recovered from git history**; this plan and `docs/builder/bld-018-final.md` are the surviving record. The names above are kept because they record which passes ran and in what order — **they name
passes, not readable files, and the checklist boxes below inherit that reading.** Everything a later
reader needs from either artifact is folded into `docs/builder/bld-018-final.md`: the integration pass's
measured results under its `## Integration pass results, folded in`, and R1's findings in its
`## Deferred work catalog`. The spec-017 closeout produced this same condition and left its pointers
dangling, which cost commit `09003dc2` to repair — hence the explicit note rather than a silent
deletion.

## Checklist

- [x] R1: Rationale extraction + spec-to-HEAD reconciliation -> `docs/builder/bld-review-1-spec018_rationale.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-018-final.md`
