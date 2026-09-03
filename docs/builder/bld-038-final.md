# Build: final test-run gate — form_mutations / 0.0.12 (038)

Spec reference: `docs/SPECS/spec-038-form_mutations-0_0_12.md` (whole file, 2,408 lines). Build plan: `docs/builder/build-038-form_mutations-0_0_12.md`. Cycle artifacts: `bld-038-slice-0-rationale_extraction.md`, `bld-038-slice-1-code_conformance.md`, `bld-038-slice-2-spec_reconciliation.md`, `bld-038-integration.md`, `bld-038-review-1-citation_residue.md`.
Status: final-accepted

## Artifact shape: one Worker 1 pass

This is the `## Final test-run gate` of `docs/builder/BUILD.md`, run after Review round 1 reached
`final-accepted`. It is a single Worker 1 pass, so the template's `## Build report (Worker 2)` and
`## Review (Worker 3)` sections have no owner here and are not stubbed. What the gate owes is the
command list in its declared order with each result recorded honestly, the floor-verification
backstop, and the `### Deferred work catalog` — the next spec author's reading list, of which
Worker 1 is the only author.

**Every figure below was measured in this pass.** The two standing hazards `BUILD.md` names for
this gate both apply in force: a `--check` measures the **working tree**, and this tree is
heavily dirty (**180** paths) from a concurrent session, so a green `--check` here is not a
statement about `HEAD`. Where an instrument's input matters, the input is named beside the
output.

## Gate results

`docs/builder/BUILD.md` `## Final test-run gate`, in its declared order.

| # | Command | Result | Verdict |
| --- | --- | --- | --- |
| 1 | `uv run pytest --no-cov` | `7306 passed, 40 skipped in 77.45s`, exit **0** | **PASS** |
| 2a | `uv run python examples/fakeshop/manage.py check` | `System check identified no issues (0 silenced).` | **PASS** |
| 2b | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | `No changes detected` | **PASS** |
| 3a | `uv run ruff format --check .` | `438 files already formatted`, exit **0** | **PASS** |
| 3b | `uv run ruff check .` | `All checks passed!`, exit **0** | **PASS** |
| 3c | `git diff --check` | exit **2** — 4 trailing-whitespace lines in **one** file, `docs/feedback2.md` | **RED, not this cycle's** (see `### Escalations`) |
| 4 | Floor verification backstop | record present with resolved versions; re-read this pass; shared `.venv` unmutated | **PASS** |

### 1. `uv run pytest --no-cov` — full sweep

`7306 passed, 40 skipped in 77.45s`, exit **0**. No `--cov*` flag; `--no-cov` is required because
`pytest.ini`'s `addopts` auto-applies `--cov`, and it is the only coverage-shaped flag permitted.
**No line coverage was inspected or asserted** (`BUILD.md` `## Coverage is the maintainer's gate,
not a worker's tool`).

**The population did not silently shrink**, which is the failure mode a pass count alone cannot
see. Grepped the run's own output: `^FAILED` → **0**, `^ERROR` → **0**, `errors during
collection` → **0**. pytest's summary line carries an `N errors` term whenever collection failed
and this one does not. Against the re-review's `7296 passed, 40 skipped` the population **grew**
by 10 outcomes — the concurrent session's work, not this cycle's, which changed no executable
line in round 1 (the inverse AST-identity proof in
`docs/builder/bld-038-review-1-citation_residue.md` `## Final verification (Worker 1)` is the
mechanical statement of that, with two independently-chosen executable controls firing).

**The two blockers earlier passes escalated are gone at the working tree.** The four
`ActiveInputPermissionAttrs.__init__() got an unexpected keyword argument 'unset_sentinel'` rows
the Slice-1 passes recorded do not fail, and `tests/rest_framework/test_sets.py` — which the
integration pass recorded as **unparseable** in the working tree, blocking a valid whole-tree
sweep and both whole-tree `ruff` commands — now parses: `ruff check .` and `ruff format --check .`
both run clean over 438 files, and the sweep has 0 collection errors. Both were the concurrent
session's own uncommitted work, neither was ever worker-verifiable at `HEAD`, and both are now
moot rather than resolved by anyone here.

### 2. Django's own consistency checks

- `uv run python examples/fakeshop/manage.py check` → `System check identified no issues
  (0 silenced).`
- `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` → `No changes
  detected`. This is the model/admin/url-config drift `pytest` does not catch, and the cycle
  added two example-app `DjangoMutationField`s and one `ModelForm` without touching a model, so
  no migration was owed and none is missing.

### 3. The lint / format / diff gate — read-only, never `--fix`

- `uv run ruff format --check .` → `438 files already formatted`, exit **0**. (Emits the standing
  `COM812`-may-conflict warning, which is configuration, not a finding.)
- `uv run ruff check .` → `All checks passed!`, exit **0**.
- `git diff --check` → exit **2**. Exactly **8** output lines naming **4** trailing-whitespace
  errors, all in **`docs/feedback2.md`**, a tracked maintainer review-input document (`START.md`
  `## docs/`: "maintainer review inputs for in-flight work"). **Conflict markers anywhere in the
  tree: 0.** Attributed rather than assumed: the file is ` M` from a concurrent session (its last
  commit is `f4b74e66`, unrelated to this cycle), it is on no `038` worker's writable list, and a
  token sweep of its 23,681 added bytes finds **0** of this cycle's 11 identifiers with a live
  control. Scoped to this cycle's own writable surface — the spec, the companion, the eight
  round-1 files, the five Slice-1 files — `git diff --check` exits **0** with no output. Not
  reverted, not touched (`AGENTS.md` rule 34, and the plan's `## Scope fence`). See
  `### Escalations`.

**A `--check` measures the working tree**, so what this row actually says is that the working
tree carries no whitespace error this cycle authored, and that one baseline-dirty file will fail
CI's whitespace gate for whoever commits it.

### 4. Floor verification — the backstop, not a second owner

`docs/builder/BUILD.md` `## Floor verification` makes the gate the **backstop that confirms it
happened**. The plan declares scope `none` build-wide; **Slice 1 re-declared it in-scope for
GAP-2 and GAP-3** (Django's upload / body-parsing and `validate_unique` seams) with the owning
pass named as the Worker 2 build pass for that slice. So the question here is whether the record
exists with its resolved versions, and whether the shared `.venv` survived.

**The record exists and names its owner.** `docs/builder/bld-038-slice-1-code_conformance.md`:
the plan's `### Floor verification` re-declares the scope and names the owner; the Worker 2 build
report's `### Floor verification` records the venv path, the resolved versions as read, and both
focused scopes' results; both Worker 3 passes verified it (`### Floor verification — it happened,
and the shared `.venv` was not mutated`; `### Floor verification — the shared `.venv` was not
mutated`); and that slice's Worker 1 final verification **re-executed** both scopes rather than
reading the record. Recorded results: `tests/forms/test_resolvers.py -k "file or upload or
preserve or integrity"` → **11 passed, 57 deselected**;
`examples/fakeshop/test_query/test_products_api.py -k "with_file or integrity"` → **3 passed, 131
deselected**, and **4 passed** for the union selection including `default_category`. No planned
floor verification is unrun, so the venv is not rebuilt here.

**Both environments read this pass, never stated from memory** (`BUILD.md` bans that explicitly):

| Environment | Read with | Versions |
| --- | --- | --- |
| floor venv `/tmp/dsf-floor` (outside the working tree, still present) | `uv pip list --python /tmp/dsf-floor/bin/python`; `/tmp/dsf-floor/bin/python -c "import sys; …"` | `django 5.2.16`, `strawberry-graphql 0.316.0`, `django-filter 26.1`, `pillow 12.3.0`, Python **3.10.19** |
| shared `.venv` | `uv pip list`; `uv run python -c "import sys; …"` | `django 6.1`, `strawberry-graphql 0.324.0`, `django-filter 26.1`, `channels 4.3.2`, `djangorestframework 3.18.0`, `pillow 12.3.0`, Python **3.14.2** |

The floor reading is exactly the floor `docs/builder/BUILD.md` `## Floor verification` states —
Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0** — and the shared `.venv`
carries the newest supported set, **not** the floor, which is the mechanical statement that
**the shared `.venv` was not mutated**. No `uv pip install` was issued by this pass at all.

**Round 1 declared floor scope `none` and that declaration is correct on measured ground:** its
diff contains 0 executable lines, so it touches no Django / Strawberry / channels seam on any
version.

### The generator `--check` runs (CI's `lint` job) — green, and what they measured

`START.md` "Pre-commit and CI gates" puts a `--check` on every generator in CI's `lint` job, and
this cycle's fence bars editing their outputs. All four run read-only here; **no generator was
run in write mode against a repository path.**

| Generator | `--check` result |
| --- | --- |
| `scripts/build_kanban_md.py --check` | exit **0**, `KANBAN.md is up to date.` |
| `scripts/build_kanban_html.py --check` | exit **0**, `KANBAN.html is up to date.` |
| `scripts/build_glossary_md.py --check` | exit **0**, `docs/GLOSSARY.md is up to date.` |
| `scripts/build_tree_md.py --check` | exit **0**, `docs/TREE.md is up to date.` |

**What that green does and does not say, stated because the whole hazard is reading it wrongly.**
All four measure the **working tree**, and all four of their outputs plus their inputs plus the
renderers themselves are baseline-dirty: ` M KANBAN.md`, ` M KANBAN.html`, ` M docs/GLOSSARY.md`,
` M docs/TREE.md`, ` M examples/fakeshop/db.sqlite3`, and ` M` on `scripts/build_kanban_md.py`,
`build_kanban_html.py`, `build_glossary_md.py`, `build_tree_md.py` and `scripts/_kanban_lib.py`.
So the green says the concurrent session's dirty outputs are self-consistent with their dirty
inputs under their dirty renderers. **No claim is made that `HEAD` is green.**

I tried to make one read-only and record why it cannot be made: rendering `HEAD`'s
`examples/fakeshop/db.sqlite3` (copied to scratch outside the repo, `DJANGO_STRAWBERRY_KANBAN_DB`
pointed at it) produced a `KANBAN.md` differing from `git show HEAD:KANBAN.md` by a whole
`## Snapshot` section — but the renderer executing that comparison is the **working tree's**, and
`scripts/build_kanban_md.py` carries 24,109 added bytes of a concurrent session's work. That is
an instrument mismatch, not evidence of drift: it renders `HEAD` data with a newer renderer.
Establishing `HEAD` consistency needs `HEAD`'s renderer as well and belongs to whoever commits.

**None of it is this cycle's.** Token sweep over each surface's own working diff for 11
cycle-`038` identifiers (`bld-038`, `createDefaultCategoryItemViaForm`,
`UpdateItemWithFileViaForm`, `DefaultCategoryItemModelForm`, `the decode reverse map`,
`the file-routing contract`, `the plain-base edge case`, `kwarg-requiring-form case`, …):
**0 hits in every one**, with live controls on the same bytes (`KANBAN.md` +102,396 bytes carries
`Decision` ×20 and `form` ×33; `KANBAN.html` +2,421,689 bytes carries `spec-011` ×23;
`docs/README.md` +50,539 bytes carries `form` ×23), so the instrument was reading the real diffs.
`examples/fakeshop/db.sqlite3` is the one surface a token sweep cannot speak to — git reports no
textual diff for a binary blob — and its attribution rests on the fence plus the fact that no
`038` artifact records a DB edit, which is weaker evidence and is stated as such.

### The two other CI `lint` checkers, for completeness

Neither is in the gate's declared command list; both are in CI's `lint` job, so a red one blocks
whoever commits.

- `uv run python scripts/check_citations.py --check` → `OK: 938 citations resolve (785 in 435
  .py files, 153 in KANBAN.md).` **Green here is not evidence about round 1's defect**: by its
  own docstring the gate resolves `path::Symbol` references only and structurally cannot see an
  ordinal citation. It is cited for its population line and as a regression check on the
  `::Symbol` citations sitting beside this cycle's edits.
- `uv run python scripts/check_trailing_commas.py --check` (repo-wide, read-only) → **7 layout
  violations**, exit non-zero. Attributed: **5** in two **untracked** `docs/spec-037-*` files a
  concurrent session is drafting (`docs/spec-037-uploads-0_0_11.md` ×3,
  `docs/spec-037-upload_file_image_mapping-0_0_11-2.md` ×2), and **2** in baseline-dirty
  `tests/utils/test_input_values.py:493` / `tests/utils/test_permissions.py:431`. **0** in any
  file this cycle wrote; run against this cycle's own paths it exits **0**. Not fixed — its
  default mode is a repo-wide auto-fix that would rewrite another session's untracked files.

### Staged-anchor backstop

`grep -rn 'TODO(spec-038'` over `.py` and `.md`, `.venv` excluded → **13** hits, and **0** of them
is a staged anchor in shipped source or tests. Every one is prose *about* the discipline: 4 in
`docs/dry/dry-0_0_12.md` (a closed cycle's scratch doc), 1 in the spec's own sentence describing
the anchor convention (`#"a source-site `TODO(spec-038 Slice N)`"`), and 8 in this cycle's own
`docs/builder/` artifacts recording the sweep. Positive control on the same instrument:
`TODO(spec-050` returns **22** live anchors in `.py`, so the zero is a reading and not an empty
grep.

## Cross-artifact walk: how the deferred-work catalog was harvested

> **Every artifact this walk enumerates was retired when the cycle closed** and is recoverable in full from the cycle's commit: `git show cce37373:<path>`. Each was read from disk at the time this pass ran; the paths are commit-resolvable, not disk-resolvable.

`START.md` "Past mistakes": harvesting items from a doc is an **enumerate-and-tick over the
source's own numbering**, not a section sweep — a sweep looks complete and leaves items unhomed.
So every source list below was enumerated by its own numbering and every item ticked to a
destination. Each source's `### Notes for Worker 1`, `### What looks solid`, `### DRY findings`
and spec-reconciliation sections were read in full.

| Source and its own numbering | Items | Where each went |
| --- | --- | --- |
| `bld-038-slice-0` `### Notes for Worker 1` items **1-9** | 9 | **0 deferred.** All nine were consolidated into Slice 1's routed list (items 1 and 8 absorbed into its 22 and 24, item 9 became non-edit note N2, items 2-7 survived as its 27-32) and discharged by Slice 2 |
| `bld-038-slice-1` the four proven gaps **GAP-1 … GAP-4** | 4 | **0 deferred.** All four built and landed; `def get_form(` went 0 → 2 in the 300-file population, the GAP-2/GAP-3 rows carry failability proofs, and GAP-3's contract-level question was settled at dispatch |
| `bld-038-slice-1` `### Notes for Worker 1` items **1-35** + non-edit notes **N1-N3** | 38 | **0 deferred.** Slice 2 applied 33, decided 5 walk rows as non-edits, deferred 0 |
| `bld-038-slice-1` `### Ruling 2` | 1 | → **catalog item 1** (`TODAY.md`), carried verbatim |
| `bld-038-slice-2` `### Deferred work catalog input` items **1-5** | 5 | → catalog items **1-5** |
| `bld-038-integration` `### Deferred work catalog` items **1-8** | 8 | items 1-5 are Slice 2's re-derived; **6** is discharged by round 1 (recorded as such); **7-8** → catalog items **6-7** |
| `bld-038-integration` `### Escalations` | 2 | → `### Escalations` below; both now moot at the working tree |
| `bld-038-review-1` plan `### Deferred work catalog input` items **1-6** | 6 | → catalog items **8-12** (its 1 and 2 are one `spec-030` fix and merge) |
| `bld-038-review-1` apply-changes `### Deferred work catalog input` items **7-13** | 7 | → catalog items **13-18**, with item 13's two halves both **cleared** (item 18) |
| `bld-038-review-1` re-review `### Notes for Worker 1` items **1-6** | 6 | 1-2 ruled in that artifact's `## Final verification (Worker 1)`; 3-5 confirmed there; 6 folds into catalog item **12** |

**18 catalog items, 3 recorded-and-closed non-items, 4 escalations.** Every item names an owner in
**prose**, because this cycle's fence bars `KANBAN.md` and the kanban DB — the normal home — and
`START.md` is explicit that an item routed forward without a named owner dies.

## `### Deferred work catalog`

> **Provenance paths in this catalog are commit-resolvable.** Every `bld-038-*.md` source cited below other than this report was retired when the cycle closed; recover any of them with `git show cce37373:<path>`. Every item's figures were re-derived in this pass, so no item depends on reading the artifact it names.

Every item carries its source artifact section, the spec line that licenses the deferral if any,
a one-line description, and a **named owner in prose**. Each was **re-derived in this pass**, not
accepted from its source's self-report (`START.md`: "Round's self-reported deferral = claim").

**1. `TODAY.md` under-enumerates the products form-mutation surface — six named, eight shipped.**
Carried **verbatim** from `docs/builder/bld-038-slice-1-code_conformance.md` `### Ruling 2`, as
Slice 2 and the integration pass both preserved it.

> - **`TODAY.md` under-enumerates the products form-mutation surface — six named, eight shipped.**
>   Owner: **the maintainer** (no worker may edit it; the build plan's `## Scope fence` puts
>   `TODAY.md` out of scope for this whole cycle and the kanban DB with it, so this bullet is the
>   homing mechanism). Source: `docs/builder/bld-038-slice-1-code_conformance.md` `### Medium:`
>   ("The staleness sweep's population excluded the repo-root standing docs"), escalated again in
>   both review passes' `### Notes for Worker 1 (spec reconciliation)` item 1. Cause: this slice
>   added `updateItemWithFileViaForm` and `createDefaultCategoryItemViaForm` to
>   `examples/fakeshop/apps/products/schema.py::Mutation` under the GAP-2 / GAP-3 escalations —
>   surface the fence did not anticipate. Three homes, each resolving exactly once, each listing
>   six of the eight: `TODAY.md` #"- **Form-based mutation write surface**",
>   `TODAY.md` #"as of `0.0.12` the form-backed mutations",
>   `TODAY.md` #"**Form-backed mutations (`0.0.12`).**". The full set is
>   `createItemViaForm`, `updateItemViaForm`, `createItemWithFileViaForm`,
>   `updateItemWithFileViaForm`, `createDefaultCategoryItemViaForm`, `createStampedItemViaForm`,
>   `submitContact`, `submitPing` — re-derived twice (8 classes, 8 `DjangoMutationField` rows), so
>   no recount is owed. Recommended action: widen the fence by this one file and re-pin the three
>   sentences; measured at three sentences in one file, no generator, no gate. `TODAY.md` is
>   byte-identical to `HEAD` (42,568 bytes, `cmp` clean) — nothing was pre-emptively touched.
>   No licensing spec clause: this is cycle-caused drift, not a spec deferral.

Re-derived at the gate: `TODAY.md` is still byte-identical to `HEAD` (**42,568** bytes both
sides), the six older wire names occur 3-4× each, `updateItemWithFileViaForm` and
`createDefaultCategoryItemViaForm` occur **0** times, and all three quoted homes resolve **exactly
once** each. The count is still 8 (8 form-mutation classes in `products/schema.py`).

**2. The five working-tree-only hunks this cycle deliberately adopted nowhere.** Source:
`bld-038-slice-2` catalog input item 2, re-derived by `bld-038-integration` item 2. Licensing
clause: none in the spec — it is the build plan's `## Contract-level escalations` ruling that an
uncommitted guard is **not** a shipped contract, so the spec is reconciled against `HEAD` and a
working-tree-only guard is catalogued rather than written in. Owner: **the concurrent session that
authored them**, whose own cycle commits them; no `038` worker action is owed, and per
`AGENTS.md` rule 34 no worker edits or reverts them.

- `django_strawberry_framework/forms/inputs.py` — the `str.isidentifier` / `keyword.iskeyword`
  field-name guard (`keyword.iskeyword`: **0** at `HEAD`, **1** now; `isidentifier`: 0 → 1); the
  guarded `dict(form_class.base_fields)` read; two out-of-vocabulary `operation_kind` raises in
  `build_form_input_class` / `build_form_inputs` (`operation_kind`: 14 at `HEAD`, **24** now).
- `django_strawberry_framework/forms/sets.py` — the typed `BaseException` wrap around the
  `get_form_fields` hook invocation in `_mutation_form_fields` (`_safe_text`: 0 → **2**).
- `django_strawberry_framework/forms/resolvers.py` — the multi-relation container check lifted to
  `django_strawberry_framework/utils/write_values.py::materialize_relation_id_container`
  (0 → **2**).

They are also recorded in the rationale companion's `## Non-Decision deliberation`, so a reader
of the spec's silence does not conclude they do not exist.

**3. Two `forms/inputs.py` guards the spec is deliberately silent about.** Source:
`bld-038-slice-2` catalog input item 3; `bld-038-integration` item 3. Licensing clause: none —
Slice 1 graded both as landed contracts (its D-14 / D-15) and Slice 2 judged both too narrow to
promote into a numbered Decision, recording them in the companion under Decision 7 rather than
dropping them. Owner: **the next spec author**, to decide whether either earns a Decision. No
worker action owed this cycle.

- `django_strawberry_framework/forms/inputs.py::_guard_input_attr_collisions` — two form fields
  colliding on a generated input attr or on the camelCased GraphQL name.
- `django_strawberry_framework/forms/inputs.py::_model_less_relation_annotation`'s reject for a
  plain-`Form` relation field whose `queryset` is `None` at class definition.

Re-derived: both present at `HEAD` (**2** occurrences each) and unchanged in the working tree, so
neither is the concurrent session's.

**4. `docs/SPECS/NEXT.md` is modified in the working tree and no `038` pass touched it.** Source:
`bld-038-slice-2` catalog input item 4; `bld-038-integration` item 4. Owner: **the concurrent
session that authored the diff**. Reported rather than reverted (`AGENTS.md` rule 34); it is on no
worker's writable list. Re-derived at the gate: still ` M`, **+15 / −6** lines, 44,577 → 45,205
bytes. The diff rewrites **Step 3's `KANBAN.md` reading instructions** — it now enumerates
`## Card ID format`, `## Relative size`, `## Progress to 1.0.0` and `## Card index` as the parts
to read, drops the `## WIP / DONE spec map` from the markdown surface (moving it to
`KANBAN.html`), and repoints `scripts/build_kanban_md.py::spec_paths_for_card` to `::spec_link`.
It tracks the same session's `scripts/build_kanban_md.py` rewrite, which is why the generator
`--check` story above and this item are one piece of work. **Consequence worth naming:** the next
spec author runs a `NEXT.md` whose Step 3 is uncommitted, and its `::spec_link` citation is
unresolvable at `HEAD`.

**5. The four full-sweep failures earlier passes escalated — now moot, and recorded rather than
dropped.** Source: `bld-038-slice-2` catalog input item 5; `bld-038-integration` item 5. They were
the concurrent session's uncommitted `sets_mixins.py` edit
(`ActiveInputPermissionAttrs.__init__() got an unexpected keyword argument 'unset_sentinel'`),
never worker-verifiable at `HEAD`, and explicitly not deferred work. This gate's sweep is
`7306 passed, 40 skipped, 0 failed, 0 collection errors`, so nothing remains to escalate. Owner:
**nobody** — recorded so a reader of the earlier artifacts does not chase a live failure that no
longer exists. **Not a deferral.**

**6. `docs/SPECS/spec-036-mutations-0_0_11.md` and its companion still name three shipped cards by
their pre-ship `TODO-ALPHA-` ids.** Source: `bld-038-integration` `### Deferred work catalog`
item 7. Licensing clause: none — a parallel site in a sibling archived spec, outside this cycle's
writable surface. Owner: **the next spec author**, or whoever next reconciles `spec-036`.
Re-derived: `docs/SPECS/spec-036-mutations-0_0_11.md` carries `TODO-ALPHA-038` ×1 and
`TODO-ALPHA-039` ×1; `docs/SPECS/appx/spec-036-mutations-0_0_11-rationale.md` carries
`TODO-ALPHA-037` ×1, `TODO-ALPHA-038` ×1, `TODO-ALPHA-039` ×1. All three are `DONE-` cards now.
Same class Slice 2 retired inside `spec-038` (its walk items 15-17).

**7. `examples/fakeshop/apps/products/schema.py::Mutation`'s docstring names seven of the eight
form mutations, omitting `submitPing`.** Source: `bld-038-integration` `### Deferred work
catalog` item 8. Licensing clause: none — pre-existing (five of six at `HEAD`) and carried forward
by this cycle's widening of the same paragraph. Owner: **Worker 0**, to fold into a builder pass
whose partition already opens the file, or **the maintainer**. Re-derived: the file defines **8**
form-mutation classes; of the eight camelCase wire names, seven occur once in the docstring and
`submitPing` occurs **0** times. One file, one clause. The adjacent `test_products_api.py` section
comment names all eight and states the count it must keep, so the two surfaces disagree. No
generator reads the paragraph — only the module docstring's **first** line feeds `docs/TREE.md`,
and that line is byte-identical to `HEAD`.

### The stranded-ordinal class (items 8-18)

Round 1 fixed `spec-038`'s stranded ordinal citations and proved its own retirement at **0** under
three independent instruments. Items 8-18 are the **same defect class in other cycles'
vocabularies**, deliberately not fixed here: fixing another spec's citations inside this round
would be exactly the half-fix the round exists to correct, and most of the sites sit outside its
ownership partition. No clause of `spec-038` licenses deferring another spec's citation defect,
and `BUILD.md` requires the licensing line only "**if any**".

**The population's history is itself the finding.** Five instruments have now been pointed at this
class and each had its own blind spot; the graded population moved **11 → 41 → 16 → 38 → 37 →
36**. Which instrument missed what is recorded per item, because the standing lesson is that a
census glob can have more than one blind spot and there is no reason to expect the last one found
to be the last one there is:

- Worker 0's `\bP[123]\b` could not see a suffixed label (`P4`, `P1.6`, `P2-3`, `P1-B`).
- The round plan's `\bP[0-9]+(?:[.\-][0-9A-Za-z]+)?\b` fixed that and still cannot see a non-`P`
  vocabulary (`Md1`, `L3-1`, `D1`) **nor** a letter-suffixed one — `P3a` / `P3b` fail its trailing
  `\b` outright, so the census that certified `spec-030`'s `P1-B` was structurally incapable of
  catching `P3a` in the same vocabulary.
- The first review's `spec-<NNN> <ordinal>` resolver reached the `Md<n>` family but compared
  literal strings, so an **en-dash** range read as unresolved (`spec-044 D4-D5`), and it did not
  reach `M1a` / `H4` / `SR-3` or the `Decision N`-into-a-spec-with-no-Decisions cases.
- The apply-changes resolver fixed those and requires the spec stem and the ordinal on **one
  line**, so every bare ordinal whose spec is named elsewhere in the file — precisely items 9-11
  below — is invisible to it. It and the P-label census are complementary; neither alone is the
  population.
- **All four over-report**, because a literal-string resolver cannot see a **numbered-list**
  resolution (`spec-028 DoD 4(c)`, `spec-043 scenario 4`) or an **abbreviated** one
  (`spec-048 D1` → `### Decision 1`). Two catalogued rows fell to this at final verification;
  see item 18.

**Corrected population, measured at final verification** (per `(spec, token)` pair, occurrences on
any line naming that spec, over the **437** tracked `.py` files): **36 occurrences over 20 files
in 5 spec vocabularies**, of which **5** (`spec-030 P1-B`) were already homed on the board, so
**31 are new**. Not the 38 / 22 / 7 and 33 the apply-changes pass published, and not the
re-review's 37 / 21 / 6 and 32 either. Control rows on the same instrument: `spec-038` `P1` / `P2`
/ `P3` → **0** each, so the round's own fix is confirmed by an instrument that never scoped it.
Per vocabulary: `spec-039` **20**, `spec-030` **7**, `spec-036` **4**, `spec-011` **4**,
`spec-016` **1**.

**8. `spec-030`'s `P1-B` label is stranded at five sites, two of them in shipped package
source.** Source: `bld-038-review-1` plan `### Deferred work catalog input` items 1-2 (one fix,
merged here). `docs/SPECS/spec-030-connection_field-0_0_9.md` carries **0** `P1-B` occurrences;
its rationale companion carries **5**. Owner: **the maintainer**, to route onto a `spec-030`
follow-up card — the cycle fence bars `KANBAN.md` and the kanban DB, so no board home can be
created from inside it. Sites, re-derived — `django_strawberry_framework/orders/sets.py` at
`#"(``spec-030-connection_field-0_0_9`` P1-B). Scalar columns"` and at
`#"multiplied (``spec-030-connection_field-0_0_9`` P1-B); ``None``"` (**2**), plus
`examples/fakeshop/test_query/test_library_api.py` (**3**). Items 8 and 14 must move **together**
so `spec-030`'s retirement can be proved at 0 rather than half-fixed.

**9. `spec-033`'s `P2-3` is stranded at two sites in shipped package source.** Source:
`bld-038-review-1` plan item 3. `spec-033` carries **0** P-label occurrences. Owner: **the
maintainer**, a `spec-033` follow-up card. Sites, both in
`django_strawberry_framework/optimizer/nested_planner.py` — at
`#"covering the general page (the P2-3 false-coverage defect);"` and at
`#"naming a duplicated column (the P2-3 defect)."` **Invisible to the one-line resolver** — the
module cites `spec-033` eleven times but not on either site's own line.

**10. `spec-032`'s `the P1 bug` / `the P2 bug` are stranded.** Source: `bld-038-review-1` plan
item 4. `spec-032`'s spec carries **0** P-label occurrences (its rationale companion carries 47).
Owner: **the maintainer**, a `spec-032` follow-up card. Sites:
`tests/test_relay_node_field.py` (**2**). Same one-line-resolver blind spot as item 9.

**11. Three P-labels naming no spec at all, undecodable without their author.** Source:
`bld-038-review-1` plan item 5. Owner: **the maintainer** — resolving these needs the authoring
cycle, which no worker can recover read-only. Sites:
`tests/test_lateral_pg_parity.py #"P2-4: two callers of ONE extension"`,
`examples/fakeshop/apps/library/tests/test_generic_connection_sharded.py #"Pins the P1 fix:"`,
`examples/fakeshop/test_query/test_library_api.py #"the P0 served it 1"`. Neither of the first two
files contains a single `spec-NNN` reference.

**12. CONTRACT-LEVEL ESCALATION — `AGENTS.md` rule 27's ordinal half has no gate, and that is why
this round existed.** Source: `bld-038-review-1` plan item 6, corroborated by its re-review item
6. Owner: **the maintainer** — this is a policy call, not a worker's
(`BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch`).

`scripts/check_citations.py` resolves `path::Symbol` references only, says so in its own
docstring, and puts `docs/` deliberately out of scope. **Nothing in the repository can see a
`spec-NNN … <ordinal>` citation**, so the class recurs silently on every spec sweep — the
`START.md` "Rule w/o gate rots" shape, whose stated remedy is the missing gate rather than the
sites. Measured corroboration for both ungated halves of rule 27: the `#"substring"` half carries
**1,434** citations over the 709 readable of 711 tracked paths, of which ~128 already do not
resolve, overwhelmingly in `docs/builder/DONE/` plans and archived specs; the ordinal half is the
**36** of items 8-18.

**A gate needs a policy call before it can be written**, which is exactly why it is the
maintainer's: which ordinal vocabularies stay legitimate, whether `Decision N` / `DoD N` /
`TODO(spec-NNN slice N)` stay permitted (the readings in this cycle say they should), and whether
`docs/` enters scope. **And this cycle has now proven two things such a gate must have, or it will
publish false positives of its own:** an **en-dash-tolerant** range comparison (the
`spec-044 D4-D5` and `spec-044 Test plan 1-7` cases) and a **numbered-list / abbreviation**
resolution step rather than a literal string search (the `spec-028 DoD 4(c)`, `spec-043 scenario
4` and `spec-048 D1` cases). Both are corrections this cycle derived by reading; a gate skipping
either would reproduce exactly the errors graded here. Concrete shape if wanted: extend
`check_citations.py` to flag a `spec-<NNN>` followed within one line by an ordinal token not on an
allowlist, resolved against that spec's live text, with those two provisions. Deliberately **not
attempted** in this cycle — a new gate is scope the brief does not carry, and 32 fixed sites under
an ungated rule is still strictly better than 32 false citations.

**13. `spec-039`'s `Md<n>` label vocabulary is stranded at 14 shipped sites.** Source:
`bld-038-review-1` apply-changes item 7. Owner: **the maintainer**, onto a `spec-039` follow-up
card; `spec-039`'s own residual cycle has not run, so its vocabulary sweep is the natural home.
Sites, re-derived per token: `Md1` ×3 (`forms/inputs.py`, `rest_framework/inputs.py`,
`utils/inputs.py`), `Md2` ×3 (`mutations/resolvers.py`, `rest_framework/resolvers.py`,
`utils/querysets.py`), `Md3` ×2 (`rest_framework/resolvers.py`, `utils/querysets.py`), `Md4` ×2
(`utils/querysets.py`, both), `Md5` ×1 (`rest_framework/inputs.py`), `Md7` ×3 (`forms/sets.py`,
`mutations/sets.py::construction_kwargs`, `rest_framework/sets.py`). `spec-039` carries **0**
`Md<n>` occurrences and **has no rationale companion**, and bare `Md` is 0 there too, so no
expansion resolves — these were **never** labels in that spec and are false independently of this
cycle. **The round plan's out-of-scope table certified spec-039's citations as resolving; that
certification is true of the `P<N>.<M>` labels its census measured** (`spec-039` carries `P2.2` and
`P1.6` live) **and false of this vocabulary.** The narrowing is recorded in
`bld-038-review-1-citation_residue.md` `## Final verification (Worker 1)` rather than by editing
the plan section, which `docs/builder/ARTIFACT.md` forbids.

**14. `spec-039` carries three further stranded ordinal vocabularies nobody has swept.** Source:
`bld-038-review-1` apply-changes item 8. Owner: **the maintainer**, the **same** `spec-039`
follow-up card as item 13 — they must move together so spec-039's retirement can be proved at 0.
Sites: `M1a` ×4 (`forms/resolvers.py`, `mutations/resolvers.py` ×2,
`rest_framework/resolvers.py`), `H4` ×1
(`rest_framework/resolvers.py #"for a serializer-only relation - spec-039 H4"`), `SR-3` ×1
(`tests/rest_framework/test_converter.py`). All **0** in spec-039. `H4` and `SR-3` read as
review-severity labels, which `START.md` "Style Rio cares about" bars from standing prose
outright, so the fix is content restatement rather than a spelling repair.

**15. Two more `spec-030` sites in a letter-suffixed spelling every prior instrument was blind
to.** Source: `bld-038-review-1` apply-changes item 9. Owner: **the maintainer**, folded into item
8's `spec-030` card so all seven sites retire in one pass. Sites:
`tests/test_connection.py #"(``spec-030-connection_field-0_0_9`` P3a)"` and
`tests/test_registry.py #"cycle-safe local import (``spec-030-connection_field-0_0_9`` P3b)"`.
`spec-030` carries **0** `P3a` / `P3b`; its rationale companion carries **4** and **3** — the
identical shape as item 8's `P1-B` 0 / 5.

**16. `spec-036`'s `L3-1` / `M3-1` / `FV-1` are stranded, and two of the three are banned severity
labels.** Source: `bld-038-review-1` apply-changes item 10. Owner: **the maintainer**, a
`spec-036` follow-up card. Sites:
`django_strawberry_framework/mutations/inputs.py #"never indexed as a decode-able FK (spec-036 L3-1)"`,
`django_strawberry_framework/utils/relations.py::is_forward_concrete_relation #"(spec-036 L3-1)"`,
`django_strawberry_framework/mutations/sets.py #"FK-to-field-name reversal, spec-036 M3-1"`,
`tests/mutations/test_resolvers.py #"(spec-036 FV-1)"`. Re-derived: `L3-1`, `M3-1`, `FV-1` and the
bare `L3` / `M3` / `FV` are **0** in both spec-036 and its companion; its live label vocabulary is
`AR-H4` / `AR-M1` / `AR-M3` / `Major-2` / `Medium-1`. `L<n>` / `M<n>` are Low / Medium
review-round labels with a round index, exactly what `START.md` bars from standing prose.
**spec-036's residual cycle has already run and left these**, which is the argument for item 12's
gate rather than a sixth manual sweep.

**17. Four `spec-011` citations are a renumber artifact, already homed on a live board card.**
Source: `bld-038-review-1` apply-changes item 11, **with its prior-art clause corrected** by the
re-review's `Low` and by final verification. Owner: **the maintainer**, and the item is **already
scheduled** — this entry's value is the re-measurement, not a re-homing. Sites:
`django_strawberry_framework/types/base.py #"``_validate_interfaces`` (spec-011 Decision 4)."`,
`types/base.py` ×2 `#"(spec-011 Decision 7"` (the connector-column docstring and its matching
inline comment), and
`django_strawberry_framework/types/resolvers.py #"# FK-id elision (spec-011 Decision 7)"`.
`docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` is a 3,440-byte stub carrying the string
`Decision` **0** times; the true target is `docs/SPECS/spec-015-relay_interfaces-0_0_5.md`, whose
`### Decision 4` and `### Decision 7` are what the sites mean.

**The prior-art clause the apply-changes pass wrote is wrong and is corrected here.** F14 is not
orphaned in a `DONE/` plan. The live-code half is on the board today: card heading
`KANBAN.md:300`, `### [TODO-ALPHA-053-0.0.15 - Boundary hardening and system-wide DRY squeeze]`,
bullet at `:341` opening `#"The `[spec-011]` renumber artifact reaches six live-code sites"`, with
the per-file counts (`types/base.py` five, `types/resolvers.py` one, plus `tests/types/test_base.py`
and `tests/filters/test_sets.py`) and a **re-derivation trap** stated in its own words. Two
corrections to carry with it, both measured read-only at the gate:

- **The trap's mechanism reproduces; its numbers are dated.** `git grep -oh '\[spec-011\]' | wc -l`
  returns **42** today, of which **41** are the literal token and **1** is git's
  `Binary file examples/fakeshop/db.sqlite3 matches` line. The +1 inflation is exactly as the
  board describes; the board's `9 vs 8` is its 2026-08-17 reading of a documentation-tree
  population that has since grown to 41. **Carry the mechanism and the per-file counts, never the
  tree-wide total.** Note also that the bracketed spelling `[spec-011]` occurs **0** times in
  tracked `.py` — that command measures the documentation tree, and the source/test population is
  a different measurement.
- **The second card is `056`, not `057`.** The documentation half's bullet renders at
  `KANBAN.md:582` under `### [TODO-ALPHA-056-0.0.17 - Alpha documentation-debt discharge]` and does
  say `#"The six package-source and test occurrences are carried by `TODO-ALPHA-053-0.0.15`"` —
  while the `:341` bullet says the documentation half is owned by `TODO-ALPHA-057-0.1.0`. One of
  the two board bullets is stale about the other's card id. Read-only observation; `KANBAN.md` is
  fenced and untouched.

**The 4-vs-8 discrepancy is subject, not drift, and item 11 was right to publish both.**
Enumerated: **8** `spec-011` occurrences in the 437 tracked `.py` files (`types/base.py` ×5,
`types/resolvers.py` ×1, `tests/filters/test_sets.py` ×1, `tests/types/test_base.py` ×1 — file for
file what F14 and the board bullet record), of which exactly **4** carry an ordinal and **4** do
not: two `spec-011 #"substring"` citations, one bare `(spec-011)`, one `spec-011-era` prose
mention. Live control: `spec-015` returns **30**. F14 counts every mention of a renumbered spec;
this catalog counts the ones whose ordinal resolves against nothing. Neither count is wrong.

**18. `spec-016 Decision 4` is stranded — and two rows this catalog previously carried are NOT
defects and are struck.** Source: `bld-038-review-1` apply-changes items 12-13, its re-review's
`Medium`, and final verification.

- **Live: `spec-016 Decision 4`.**
  `examples/fakeshop/test_query/test_library_api.py #"Pins the end-to-end contract (spec-016 Decision 4,"`.
  `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` carries **0** `### Decision N` headings
  and the string `Decision` **0** times, so the ordinal names nothing findable. Owner: **the
  maintainer**, a `spec-016` follow-up card — or, if the correct target turns out to be another
  spec, the same renumber-artifact treatment item 17 needs. Note the same file also carries the
  item-8 `P1-B` sites and item-11's `P0`, so a single pass over it could retire three catalog
  rows.
- **STRUCK — `spec-043 scenario 4` resolves.**
  `examples/fakeshop/test_query/test_products_api.py::test_create_item_login_bracket_via_test_client #"spec-043 scenario 4: ``TestClient.login()`` scopes write auth to the bracket."`
  `docs/SPECS/spec-043-test_client-0_0_14.md` `## Test plan` numbers its scenarios `1.`…`5.` and
  item 4 is `#"4. **`login()` scoping.** `seed_data(1)`, a write-auth-gated products"`, which the
  citing docstring restates almost clause for clause. Anchor present, section present, item
  present: `START.md` "grade by ANCHOR presence, never distance" clears it, the same way this
  catalog's own grading pass cleared `spec-028 DoD 4(c)` and `spec-044 Test plan 1-7`.
- **STRUCK — `spec-048 D1` resolves.**
  `examples/fakeshop/test_query/test_uploads_api.py #"publishes ``path`` in the live schema (spec-048 D1)."`
  The literal token `D1` is indeed **0** in spec-048 — and `D<N>` is a **measured repo-wide
  shorthand for `Decision <N>`**, not this site's invention: **26** `spec-<NNN> … D<N>` citations
  exist in tracked `.py` and in **20** of them the named spec carries a matching `### Decision <N>`
  heading (`spec-040` ×12, `spec-041` ×3, `spec-044` ×2, `spec-053` ×2, `spec-048` ×1). spec-048
  ships `### Decision 1 — `path` leaves the safe default for two composed opt-in types`, whose
  first listed property is `**The field is gone from the SDL, not merely null.**` over
  `DjangoFileType` / `DjangoImageType` — precisely what the citing docstring asserts.

Both struck rows are **kept here as cleared convention cases** rather than deleted, alongside
`spec-028 DoD 4(c)`, `spec-044 D4-D5`, `spec-044 Test plan 1-7` and the four
`spec-099-example-0_0_9` fixture-data hits that earlier passes cleared by reading. The lesson —
that a literal-string resolver over-reports in **both** directions — is the one thing item 12's
gate has to be built knowing, and a silently-dropped row does not carry it. The rule was then run
against **every** remaining row: none of items 8-11 or 13-17 has a resolution path, verified token
by token against the named spec **and** its rationale companion.

## Escalations for Worker 0

**1. `git diff --check` is red on one baseline-dirty file, and it will be red in CI.**
`docs/feedback2.md` carries 4 trailing-whitespace lines. It is a tracked maintainer review-input
document, dirty from a concurrent session, on no `038` worker's writable list, and a token sweep
of its added bytes finds none of this cycle's identifiers. Scoped to this cycle's writable
surface the command exits 0. **Not fixed and not reverted** — `AGENTS.md` rule 34 and the plan's
fence both bar it, and per `BUILD.md` `## Claims are proven mechanically` a working-tree state
this cycle does not own is the maintainer's to resolve. It does not block `final-accepted`: the
failure is outside this cycle's diff and pre-existing.

**2. `scripts/check_trailing_commas.py --check` is red on 7 layout violations, none this
cycle's.** 5 in two untracked `docs/spec-037-*` drafts, 2 in baseline-dirty
`tests/utils/test_input_values.py` / `tests/utils/test_permissions.py`. Not fixed: the script's
default mode is a repo-wide auto-fix that would rewrite another session's untracked files.

**3. The four generator `--check` runs are green against the WORKING TREE, and no `HEAD` claim is
available read-only.** Their outputs, their DB input and the four renderer scripts are all dirty
from the concurrent session, so a `HEAD` render uses the wrong renderer (demonstrated above: it
drops `HEAD`'s whole `## Snapshot` section). Whoever commits must re-check these against a tree
where the renderers and the DB land together, or CI's `lint` job will find the mismatch. Nothing
here is this cycle's: 0 cycle tokens in every one of those diffs, with live controls.

**4. Two blockers earlier passes escalated are moot at the working tree, not resolved by anyone.**
`tests/rest_framework/test_sets.py` parses again and the four `unset_sentinel` failures no longer
fail — both the concurrent session's own doing. Recorded so the escalation chain closes rather
than dangling.

## Cycle checklist state

The build plan's `## Checklist` carries two unticked boxes at the time of writing:

- `- [ ] Review round 1: citation residue …` — its artifact reached
  **`Status: final-accepted`** at this spawn's Pass A.
- `- [ ] Final test-run gate …` — this artifact.

Both are **Worker 0's** to flip (`docs/builder/BUILD.md` `## Required plan structure`; Worker 1
does not mark build-plan checkboxes). Slices 0, 1, 2 and the integration pass are already
`- [x]`, and every one of the six artifacts is `final-accepted`.

## Failability proofs

`None; this pass introduced no new boundary.` Worker 1 wrote no source, no test, and — beyond the
one-word custodial spec repair recorded in Review round 1's `### Spec changes made (Worker 1
only)` — no byte outside this artifact and its own memory file. The `### Deferred work catalog`
adds no guard, cap, rejection path, or validation branch. The gate's own obligation is to confirm
that every boundary the cycle **did** add carries a proof, and that confirmation is discharged:
Slice 1's five proofs are recorded in
`docs/builder/bld-038-slice-1-code_conformance.md` with the manifest at
`docs/builder/temp-tests/slice-1/proofs.json`, all five anchors verified matching exactly once in
the live tree, no `ACTIVE-MUTATION.json` / `RESTORE-FAILED.json` anywhere, and round 1's inverse
AST-identity proof re-run at final verification with four controls (two firing on executable
mutations in two different files, one confirming docstring blindness, one confirming the
uniqueness abort). No mutation residue survives: swept for both of my own control suffixes →
**0** hits.

## Hot-path budget

`Not applicable; plan declares no hot path.` The plan's build-wide `none` holds, and its ground
holds: this cycle changed **0** executable lines in `django_strawberry_framework/`. Round 1's diff
is 65 comment / docstring lines and its docstring-stripped AST digest is identical across all
eight files. The two costs Slice 1 recorded remain the only ones and neither is package cost nor
per-request: the two new example-app `DjangoMutationField`s cost one construction each **at
schema build**, and `CreateDefaultCategoryItemViaForm.get_form_kwargs` issues one
`Category.objects.order_by("pk").first()` read per call **of that one example-app mutation**,
inside the pipeline's read phase.

## Floor verification

Recorded in full under `### 4. Floor verification — the backstop, not a second owner` above:
scope re-declared by Slice 1 for GAP-2 / GAP-3, owned and run by that slice's Worker 2 build
pass, verified by two reviewers, re-executed by that slice's Worker 1 final verification, and
confirmed present here with both environments read this pass (`/tmp/dsf-floor`: Django 5.2.16 /
strawberry-graphql 0.316.0 / Python 3.10.19; shared `.venv`: Django 6.1 /
strawberry-graphql 0.324.0 / Python 3.14.2 — **unmutated**). No floor venv was built by this pass
and no `uv pip install` was issued.

## Spec changes made (Worker 1 only)

**None this pass.** The one custodial repair of this spawn — `(the kwarg-requiring-form fix)` →
`(the kwarg-requiring-form case)` at `docs/SPECS/spec-038-form_mutations-0_0_12.md` line 1349 — is
recorded in `docs/builder/bld-038-review-1-citation_residue.md` `### Spec changes made (Worker 1
only)`, where the pass that made it belongs. The gate wrote no spec byte.

**Spec status-line re-verification** (`docs/builder/worker-1.md`, every spawn): the spec's opening
lines still describe the build's state — `#"Shipped in `0.0.12` (card [`DONE-038-0.0.12`][kanban])."`
— and the companion's opening paragraph still describes what it carries. 177,322 bytes / 2,408
lines and 82,360 bytes / 1,245 lines respectively. `uv run python scripts/check_spec_glossary.py
--spec docs/SPECS/spec-038-form_mutations-0_0_12.md` → `OK: 31 terms - all have glossary entries
and at least one spec link.`
`docs/SPECS/appx/spec-038-form_mutations-0_0_12-terms.csv` untouched by every pass of this cycle.

## git status

**180** dirty paths at the end of this pass, up from the plan's 116 baseline; the concurrent
session has kept writing throughout. This cycle's own surface, and nothing else, is:

```
 M django_strawberry_framework/forms/converter.py
 M django_strawberry_framework/forms/inputs.py
 M django_strawberry_framework/forms/resolvers.py
 M django_strawberry_framework/forms/sets.py
 M django_strawberry_framework/mutations/sets.py
 M docs/SPECS/spec-038-form_mutations-0_0_12.md
 M examples/fakeshop/apps/products/forms.py
 M examples/fakeshop/apps/products/schema.py
 M examples/fakeshop/test_query/test_products_api.py
 M tests/forms/test_inputs.py
 M tests/forms/test_resolvers.py
 M tests/forms/test_sets.py
?? docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md
?? docs/builder/bld-038-*.md          (six artifacts)
?? docs/builder/build-038-form_mutations-0_0_12.md
```

Five of those `M` files are mixed with a concurrent session's hunks (`forms/inputs.py`,
`forms/sets.py`, `forms/resolvers.py`, `tests/forms/test_resolvers.py`,
`tests/forms/test_sets.py`), which is why every claim in this cycle about a baseline-dirty file
was stated against `git show HEAD:<path>` into a scratch path **outside** the repo, or against a
pre-edit pristine copy where `HEAD` was not a usable reference. **No `git stash` / `checkout` /
`restore` / `worktree` was run by any pass of this cycle**, and nothing outside the declared
writable surface was edited or reverted. Only the maintainer commits.

## Summary

The `spec-038` residual-reconciliation cycle is closed. It discharged the two obligations that
were never closed at ship time: the spec's missing rationale companion now exists
(`docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md`, 82,360 bytes, the whole
deliberative layer moved out verbatim), and the shipped spec has been graded against `HEAD` and
rewritten to describe the code that actually ships. Along the way the cycle found what the charter
existed to find: **four proven code gaps**, of which two — the `get_form` construction-hook arm
and the omitted-file-preserve contract — were `or` disjuncts that a 100%-covered, fully green
subsystem had carried for three releases and that neither reading the diff nor a coverage run
could have surfaced. All four were built, with failability proofs, and one carried a
contract-level question settled at dispatch by building the test the Definition of done had always
named. Slice 2 then rewrote 33 stale contract statements across the spec's five redundant homes,
the integration pass cross-checked 26 contract classes and repaired 2 divergences, and Review
round 1 retired the 32 stranded ordinal citations Slice 2's own label sweep had falsified in
shipped source — 0 executable lines changed, proved by an inverse AST-identity digest with firing
controls.

Every gate command passes but one, and that one is a concurrent session's trailing whitespace in a
file no worker here may touch. The catalog hands the next spec author **18 items**, every one with
a named owner in prose because the fence bars the board, and hands the maintainer **one
contract-level escalation**: the rule this whole round enforced has no gate, and writing one needs
a policy call plus the two instrument provisions this cycle paid to learn.

## Final status

`final-accepted`.

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
