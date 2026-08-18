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
- `docs/builder/bld-018-final.md` — final gate. **Deleted at closeout; its content is folded into `## Closeout record` below.**

**Closeout disposition, 2026-08-18.** All three `bld-*` artifacts were deleted at closeout by the
maintainer's instruction. The two per-round artifacts were deleted before the cycle was committed and
**appear in no commit**; `bld-018-final.md` was committed at `b5b2af81` and is recoverable from there.
**This plan is the cycle's sole surviving file**, and `## Closeout record` below carries everything the
three artifacts held that a later reader needs. The names above are kept because they record which passes ran and in what order — **they name
passes, not readable files, and the checklist boxes below inherit that reading.** Everything a later
reader needs from any of the three is folded into `## Closeout record` below. The spec-017 closeout produced this same condition and left its pointers
dangling, which cost commit `09003dc2` to repair — hence the explicit note rather than a silent
deletion.

## Checklist

- [x] R1: Rationale extraction + spec-to-HEAD reconciliation -> `docs/builder/bld-review-1-spec018_rationale.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> recorded under `## Closeout record` below (artifact deleted at closeout).

## Closeout record

Folded in from `docs/builder/bld-018-final.md` when that artifact was deleted at closeout. `HEAD` at
gate time: `de2601e9`. `Status: final-accepted` for every round and for the gate.

### What a green gate does and does not prove here

**This round wrote zero lines of code** — its writable set was markdown only, so a red suite could not
have been its doing and a green suite proves nothing about its diff. The gate was run because the
process requires it and because an unattributed failure must never be waved through, not because it
can validate a documentation change.

**The tree was not this round's alone.** At gate time `git status --short` showed **94 entries**, of
which **15 under `django_strawberry_framework/`** (14 `.py` modules plus the `debug_toolbar.html`
template) and **12 under `tests/`** — all 27 a concurrent session's work, not read as work product, not
edited, not reverted (`AGENTS.md` rule 34). Attribution rule applied to every command: a failure is
this round's only if the failing path is in this round's writable set. None was.

### Gate results

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `6151 passed, 40 skipped in 59.98s`, exit 0 |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — `no issues (0 silenced)`, exit 0 |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit 0 |
| 4 | `uv run ruff format --check .` | **PASS** — `424 files already formatted`, exit 0 |
| 5 | `uv run ruff check .` | **PASS** — `All checks passed!`, exit 0 |
| 6 | `git diff --check` | **PASS** — no output, exit 0 |

**No `--cov*` flag was passed to any command** and plain `uv run pytest` — a coverage run in this
repository — was never invoked. No `git stash`, `checkout`, `restore`, or `worktree` at any point.
Neither `ruff` invocation used `--fix`. The plan's recorded dirty-baseline exception went **unused**,
because nothing failed. The suite was fully interpretable: no collection error, no half-saved
concurrent edit, no unattributable row.

Two checks outside the gate's list were re-run rather than cited from an earlier pass:
`check_spec_glossary.py --spec docs/SPECS/spec-018-meta_primary-0_0_6.md` -> `OK: 15 terms`, exit 0 (it
is the one script a rationale move can break, and it broke mid-pass twice in the spec-017 sibling and
once here); `check_trailing_commas.py --check` -> exit 0 on this cycle's written paths.

**Floor verification scope: `none`**, correctly — no Django, Strawberry, or channels seam is touched
because no source is. No floor venv was built and the shared `.venv` was never mutated.

### The proof the extraction was a move, not a copy

The cross-round integration pass returned **no integration findings** and required no consolidation
dispatch. Its measurements are the evidence for this cycle's central claim:

| Measure | Result |
|---|---|
| Long sentences (>=90 chars) in the spec | 371 |
| Long sentences (>=90 chars) in the companion | 203 |
| **Byte-identical sentences shared by both** | **0** |
| **Near-duplicate runs of >=110 chars (`difflib` longest-match over all 75,313 pairs)** | **0** |

Both files were stripped of fenced code and table rows before splitting, so quoted pseudocode in the
companion's historical records does not inflate the comparison. Two zeros over 75,313 pairs is the
`Moved` / `Kept deliberately` / `Deleted outright` / `Reconciled in place` disposition set holding in
fact rather than in assertion.

Four further confirmations: **32** `path::Symbol` refs in the spec and **17** in the companion all
resolve against a parsed AST; the **5** surviving `#"substring"` citations each resolve inside the named
symbol's own source range, extracted via `ast` rather than by searching the file; the moved round-label
vocabulary (`H[1-3]` / `M[1-2]` / `L[1-5]` / `rev[1-6]` / `revision`) returns **0** hits under a
word-boundary sweep; and **9** pointer links carry each spec site whose deliberation moved. Overlap
against `docs/GLOSSARY.md` and `CHANGELOG.md` peaks at 45 characters and every hit is an identifier or
the mandated link scaffold — no contract sentence and no error message is duplicated.

The one place the pair could have told two stories was the `plan_optimizations` call site, where the
spec carried a precise checklist box against a vague routing-table row. Worker 3 caught it as RR-1 and
both sites now spell the chain identically (`_get_or_build_plan`, reached from `._optimize` via
`.apply_to`).

### Maintainer hand-offs

**No deferred work of this round's own.** Every dispatched finding, Worker 3's seven findings, RR-1,
and the final-verification pass's own Decision 1 finding landed inside the round. D-R3-1, escalated
non-blocking, was closed by deletion rather than parked. Three items lie outside the writable set by
the dispatch:

1. **The live `KANBAN.md` `DONE-018-0.0.6` card body names the public `audit_primary_ambiguity()`** —
   private as `_audit_primary_ambiguity` since commit `13d8dac5`, 2026-05-18. **Now homed on
   `TODO-ALPHA-052-0.1.0`**, which carries the row id, the fix instrument (a DB edit plus regenerate,
   since `KANBAN.md` renders from `examples/fakeshop/db.sqlite3`), and the two findings below. Nothing
   further is owed here. **One row, not two:** this item originally also charged the body with quoting
   the retired duplicate-primary message `"<new> is already declared primary as <existing>"`. That was
   read off the verbatim card-body copy in the companion, which does carry it, and attributed to the
   board, which never did — the substring `declared primary` returns zero `CardItem` and zero
   `CardReference` rows board-wide. The withdrawal is recorded because the card bullet cites this
   hand-off and tells its author not to hunt for a second edit. Two facts surfaced in the same
   measurement and travelled to that bullet: the one real staleness is `CardItem` 723 (`note`, order
   6), and **10 of that card's 15 `note` items end mid-sentence** (rows 720, 721, 722, 723, 725, 726,
   727, 728, 732, 733) from an import-time truncation predating every residual cycle, so row 723 is
   both stale and clipped. Same defect class the round's own reports hit three times — a description
   outliving the source it was derived from — reaching the hand-off list itself.
2. **Two `check_trailing_commas` layout violations exist repo-wide and belong to no cycle**, so they
   are recorded here rather than carded: `examples/fakeshop/test_query/test_products_visibility_api.py`
   (untracked, a concurrent session's live-tier test, `should collapse (< threshold, over-exploded)`)
   and an agent memory file under `.claude/` missing the link-def scaffold, outside the package
   entirely. Both block a pre-commit run over their own paths until their owners fix them. Neither was
   fixed and neither was reverted.
3. **No standing-doc edit is owed for this card.** `docs/GLOSSARY.md`, `CHANGELOG.md`,
   `docs/README.md`, and `TODAY.md` were each read against `HEAD` and each reflects shipped state — the
   glossary marks `Meta.primary` `shipped (0.0.6)` and quotes the landed error message, and
   `CHANGELOG.md` documents both the message reword and the `register` / `get` semantics. Recorded so
   the next author does not re-derive it.

### The honest reading of the green

This round wrote no code, **so the suite can neither convict nor acquit it.** What the gate genuinely
establishes is that the tree the round was closed against is coherent, and that nothing the round did
broke a build it never touched.
