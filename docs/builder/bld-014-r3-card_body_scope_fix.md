# Build: R3 — card-body `#### Scope` fix on `DONE-014-0.0.4`

Spec reference: `docs/SPECS/spec-014-testing_shift-0_0_4.md` (no spec clause; this item corrects board
data, not the spec). Build plan: [`build-014-testing_shift-0_0_4.md`][build-014] `## Mid-cycle
addition: R3`. Corrected mechanism and ready-to-apply recipe:
[`bld-014-r2-doc_completion_archive_audit.md`][bld-014-r2] `### F14`.
Status: final-accepted

Combined Plan + Final-verification block, per `docs/builder/BUILD.md` `### Procedural-closure
slices` and the plan's `## Dispatch record` (Worker 1 alone; this item writes no code).

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable in the package sense, and the substitute was run: this
  item writes no Python and touches nothing under `django_strawberry_framework/`. The inventory that
  *is* load-bearing here is the kanban **write-API** inventory — `examples/fakeshop/apps/kanban/services.py`
  was enumerated (`grep -n "^def "`, 40 module-level functions) looking for the shapes `remove`,
  `delete`, `item`. It carries `append_card_item`, `append_card_reference`, `add_dependency`,
  `remove_dependency`, `set_item_complete`, `verify_item`, `move_card_number`,
  `compact_card_numbers` — **no card-item removal function exists**. Recorded under
  `### Implementation notes` as the reason for the fallback the dispatch anticipated.
- **Existing patterns reused.** The maintainer's own fix at `6f8bf818` is the precedent: same defect,
  same board, two sibling cards (`DONE-011-0.0.4`, `DONE-013-0.0.4`), same disposition — delete the
  stray `kanban.CardItem` scope row, regenerate both exports, do not re-pack `order`. This item
  applies that precedent verbatim rather than inventing a third shape.
- **New helpers justified.** None. A one-row data correction does not justify adding a
  `remove_card_item` service function to `services.py`; `services.py` is outside this item's writable
  set in any case. The condition that would justify extracting one: a **third** independent caller
  needing card-item removal — at that point the deletion-plus-order semantics deserve a single site.
- **Duplication risk avoided.** The one real risk is a hand-edit of `KANBAN.md` duplicating the DB as
  a second source of truth. Prevented structurally: the edit is made through the ORM and both files
  are produced only by their generators.

### Implementation steps

1. Re-derive the baseline. Confirm `examples/fakeshop/db.sqlite3`, `KANBAN.md`, and `KANBAN.html` are
   clean at the current `HEAD` (the plan's figures are stale by construction — `## Baseline-dirty
   out-of-scope files` says so itself).
2. **Baseline regenerate before any DB edit.** Run `scripts/build_kanban_md.py` and
   `scripts/build_kanban_html.py`; require `git diff KANBAN.md KANBAN.html` to be empty. A non-empty
   diff means a concurrent session's rows are unlanded -> stop, revert nothing, `revision-needed`.
3. Read the card's rows through the ORM (`Card.objects.get(number=14)` plus its `CardItem` set) and
   confirm R2's mechanism claim — a stray `scope` `CardItem`, not a rendered `description` column —
   before deleting anything.
4. Delete the identified row through the Django ORM, located **by text**, not by primary key.
5. Regenerate both exports; require the `KANBAN.md` diff to be exactly the one removed bullet.
6. Regenerate a second time and hash both files; require byte-identity with the first run.
7. `manage.py check` and `manage.py import_spec_terms --check`.
8. Confirm the rendered card still carries its three substantive scope bullets, its seven glossary
   terms, and its spec link.

Line numbers are pin-at-write-time navigational hints.

### Test additions / updates

None, and none is possible: this item's writable set contains no test file, and the dispatch forbids
a `pytest` run. The mechanical equivalents are steps 2, 5, 6, 7 above — a clean-baseline regenerate,
an exact-diff assertion, a two-consecutive-regenerate byte-stability proof, and the two management
commands.

### Implementation discretion items

- Whether to re-pack the surviving `order` values to `0-2` after the delete. Assessed: they already
  are `0`, `1`, `2` (the stray held `3`), so no re-pack is needed or possible. The renderer orders by
  `order` and does not require contiguity from `0` in any case; `6f8bf818` did not re-pack either.

### Dispatched findings checklist

- [x] **F14** The rendered `DONE-014-0.0.4` card body carries a **duplicate `#### Scope` row** —
  bullet 4 ("remove the `tests.fixtures.apps` fixture app + unmanaged cardinality fixtures; switch
  package tests to real `library` models.") restating bullets 1-3. Removed at the source (the
  `kanban.CardItem` row) and both exports regenerated.

---

## Final verification (Worker 1)

### What the database actually held

`HEAD` at this pass: `6f8bf818e9b1bc45059017c17fc346a3daca0b8f` — the maintainer's own sibling fix,
so the precedent commit is this pass's baseline. `git status --porcelain` -> **184 paths** at the end
of the pass, **181** at the start; the three added are exactly this item's outputs (below). Of the
181 baseline paths, `docs/GLOSSARY.md` is dirty with a concurrent session's work and was never opened
— `scripts/build_glossary_md.py` was not run.

`Card.objects.get(number=14)` is `pk=36`. **The model has no `description` field at all** — reading
`getattr(card, "description", ...)` returns the sentinel — which independently confirms R2's
correction of the build plan's mechanism: the fourth bullet could not have been a rendered
`description` column, because no such column exists. Its ten `CardItem` rows at entry:

| pk | section | order | text (truncated) |
|---|---|---|---|
| 642-646 | `files_touched` | 0-4 | the five paths the card names |
| 639 | `scope` | 0 | `Removed `tests.fixtures.apps.TestsCardinalityConfig` from the example project.` |
| 640 | `scope` | 1 | `Removed the old unmanaged cardinality fixture files under `tests/fixtures/`.` |
| 641 | `scope` | 2 | `Package tests that need OneToOne / M2M / cardinality coverage now use real models from …` |
| **638** | **`scope`** | **3** | **`remove the `tests.fixtures.apps` fixture app + unmanaged cardinality fixtures; switch package tests to real `library` models.`** |
| 637 | `why_it_matters` | 0 | `test hygiene.` |

**`pk=638` is the stray**, and two independent signals identify it as the redundant row rather than
one of the three substantive ones:

1. **Content.** It is a single lowercase sentence restating all three of `639`-`641` — one clause per
   bullet, in the same order — where each of those three states one distinct fact in sentence case.
   The three carry information it does not; it carries none they do not.
2. **Provenance.** Its primary key (`638`) is **lower** than all three (`639`-`641`) while its
   `order` (`3`) is **higher**, so it was created first and appended last. That is the signature of a
   card-import step that seeded one summary row and then wrote the authored bullets after it — the
   same shape the maintainer's `6f8bf818` message describes ("a third CardItem restating the two
   above it, which the renderer emitted because it builds sections from card items alone").

### What was deleted, and through which API

**Direct ORM `.delete()`, not a service function** — because no sanctioned write API covers this
operation. `examples/fakeshop/apps/kanban/services.py` exposes `append_card_item` but **no**
card-item removal counterpart (full enumeration in `### DRY analysis`); `services.py` is outside this
item's writable set, so adding one was not an option and would have been unjustified for a one-row
correction in any case. The dispatch anticipated exactly this fallback.

```python
# examples/fakeshop $ uv run python manage.py shell -c ...
from apps.kanban.models import CardItem

stray = CardItem.objects.get(
    card__number=14,
    section__key="scope",
    text__startswith="remove the `tests.fixtures.apps` fixture app",
)
stray.delete()
```

Located by text and by the three-way `card`/`section`/`text` conjunction, never by primary key.
Result: `(2, {'kanban.UUIDModel': 1, 'kanban.CardItem': 1})`.

**The `2` is the point of using the ORM.** The row's `UUIDModel` side-row
(`8f168388-d41c-4f0a-aaa5-6dba95073ab8`, read before the delete) cascaded away with it, because
`UUIDModel.carditem` is a `OneToOneField(..., on_delete=models.CASCADE)`. A raw `DELETE FROM` would
have left that row orphaned, breaking the one-hot `kanban_uuidmodel_exactly_one_link` check
constraint's invariant and the `uuid { id }` selection both generators' in-process `/graphql/` query
makes. The `2` is the mechanical evidence that the side-row was handled.

The three surviving rows re-read after the delete: `639`/`0`, `640`/`1`, `641`/`2`. No re-pack was
needed (see `### Implementation discretion items`).

### Verification, in the dispatched order

1. **Baseline regenerate BEFORE any DB edit — clean.** Both generators run at `6f8bf818` with no DB
   write first: `Wrote 69 cards (excluded 1 backlog cards) and 15 board docs` /
   `Wrote 70 cards, 15 board docs, and 11 lookup arrays`. `git status --porcelain KANBAN.md
   KANBAN.html examples/fakeshop/db.sqlite3` -> **empty**, and `git diff --stat` on both files ->
   **empty**. No pre-existing DB-vs-file drift, so every byte of the diff below is this item's. The
   `revision-needed` branch this step guards did not trigger.
2. **ORM edit** — above.
3. **Regenerate both** — done.
4. **The `KANBAN.md` diff is exactly the one removed bullet.** `git diff --stat` ->
   `KANBAN.md | 1 -`, `KANBAN.html | 2 +-`; `git diff --numstat KANBAN.md` -> `0 1`. The whole
   markdown diff:

   ```text
   @@ -4477,7 +4477,6 @@
    - Removed `tests.fixtures.apps.TestsCardinalityConfig` from the example project.
    - Removed the old unmanaged cardinality fixture files under `tests/fixtures/`.
    - Package tests that need OneToOne / M2M / cardinality coverage now use real models from `examples/fakeshop/apps/library/`.
   -- remove the `tests.fixtures.apps` fixture app + unmanaged cardinality fixtures; switch package tests to real `library` models.
   ```

   `KANBAN.html`'s `1 1` numstat is its single-line data block, and the removed substring is the
   identical sentence — confirmed by grepping the html diff for it. Nothing else moved.
5. **Two-consecutive-regenerate byte-stability — proved by hash.** Both generators run a second time;
   `shasum -a 256` before and after is identical on both files:

   | file | sha256 (run 1) | sha256 (run 2) |
   |---|---|---|
   | `KANBAN.md` | `7b94e9dd92f9c428da32e0ff317aff24fab81bd5a764b0d536c773a23acd1aa0` | same |
   | `KANBAN.html` | `6c9a86bb414013ecc96f1c1a56c1bf277106e8047dee1e6435b66971c9fcad2f` | same |

   The `git diff --numstat` after run 2 is unchanged (`0 1` / `1 1`), i.e. the second render is a
   fixed point, not a further edit.
6. **`uv run python examples/fakeshop/manage.py check`** -> `System check identified no issues (0
   silenced).` **Pass.**
7. **`uv run python examples/fakeshop/manage.py import_spec_terms --check`** -> `OK: 49 done cards
   have glossary links.` **Pass, all done cards.** No earlier-card failure arose, so the
   pre-archive-path exception the dispatch allows for was not needed.
8. **The rendered card is intact.** `KANBAN.md:4455` onward: the `DONE-014-0.0.4` heading and its
   `KANBAN.html` anchor, `Priority: Low` / `Status: Done` / `Relative size: S` / four labels, the
   spec link `[spec-014-testing_shift-0_0_4.md](docs/SPECS/spec-014-testing_shift-0_0_4.md)`, the
   `#### Glossary terms` table with **seven** rows (Choice enum generation, `DjangoConnectionField`,
   `DjangoOptimizerExtension`, `DjangoType`, `finalize_django_types`, `OptimizerHint`, Strictness
   mode — each `shipped`), `#### Scope` with **three** bullets, `#### Files likely touched` with its
   five paths, and `#### Why it matters`. The card also still appears once in the Done index table at
   `KANBAN.md:133`. Only the fourth scope bullet is gone.

### Validation run

- No `ruff` invocation: this pass touched no Python file.
- `scripts/build_glossary_md.py` **was not run**, and `docs/GLOSSARY.md` was not opened for writing —
  it is dirty with a concurrent session's uncommitted rows (`START.md` `## Concurrent sessions`).
- No `pytest` run; no `--cov*` flag in any command this pass issued.
- No `git checkout`, `git stash`, `git restore`, `git worktree`, branch creation, or commit.
- **Floor verification: not applicable.** The plan declares floor-verification scope `none`; this item
  touches no executable code and no upstream integration seam.
- **Hot-path budget: not applicable.** The plan declares no hot path; this item deletes one database
  row and re-renders two documents.
- **Failability proofs: none; this pass introduced no new boundary.** It introduced no code. The
  substitute assurance is step 5's byte-stability proof, which is the property a test would pin.
- `git status --porcelain` at the end shows exactly three changed paths this item owns —
  `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3` — plus this artifact (new) and the
  gitignored `docs/builder/worker-memory/spec-014-worker-1.md`. Baseline count `181` -> `184`;
  nothing in the concurrent sessions' 181 paths moved.

### Spec slice checklist audit

`### Dispatched findings checklist` carries one box, **F14**, and it is `- [x]`: the contract landed
in the diff above. No box is left un-ticked, so no deferral reason is owed.

### DRY check across this item, R1, and R2

No duplication introduced. This artifact does not restate R1's `V1-V10` table or R2's `F11-F14`
findings; it records the single mechanical operation R2's `### F14` specified, and cites that section
rather than re-deriving the recipe. The one shape borrowed — the maintainer's `6f8bf818` disposition
— is cited as precedent, not re-argued.

### Summary

`DONE-014-0.0.4` was the last card on the board carrying the duplicate `#### Scope` bullet. The
source was a stray `kanban.CardItem` row (`pk=638`, section `scope`, `order=3`) whose text restated
the three authored bullets above it; the model has no `description` field, so the build plan's
original mechanism account could not have been right and R2's correction holds. The row was deleted
through the Django ORM — cascading its `UUIDModel` side-row, which is why the ORM and not raw SQL —
and both board exports were regenerated. The baseline regenerate before the edit was clean, the
resulting `KANBAN.md` diff is exactly the one removed line, a second regenerate is byte-identical,
`manage.py check` passes, and `import_spec_terms --check` reports OK for all 49 done cards. The card
still renders its three substantive scope bullets, its seven glossary terms, and its spec link.

`Status: final-accepted`. The changed files are handed to the maintainer for review; no commit was
made.

### Spec changes made (Worker 1 only)

**None.** The spec's status/header lines were re-verified at the start of this spawn per
`docs/builder/worker-1.md` `## Spec status-line re-verification` and still describe the build's
current state — R1 and R2 reconciled them, and this item changed no contract the spec states. The
defect fixed here lives in board data, not in the spec, and `docs/SPECS/spec-014-testing_shift-0_0_4.md`
is untouched by this pass.

### Deferred

**Nothing.** F14 was the cycle's only deferred item, and it is discharged here. The final gate's
`### Deferred work catalog` should record this item as closed rather than carrying F14's recipe
forward.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[bld-014-r2]: bld-014-r2-doc_completion_archive_audit.md
[build-014]: build-014-testing_shift-0_0_4.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
