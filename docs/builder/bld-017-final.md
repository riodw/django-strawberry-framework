# Build: Final test-run gate (spec-017)

Spec reference: `docs/SPECS/spec-017-deferred_scalars-0_0_6.md`
Rationale companion: `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-rationale.md`
Build plan: `docs/builder/build-017-deferred_scalars-0_0_6.md`
Closed round artifacts: `docs/builder/bld-017-r1-rationale_and_spec_reconciliation.md` (`final-accepted`), `docs/builder/bld-017-r3-doc_completion_audit.md` (`final-accepted`) — **both DELETED at closeout on maintainer instruction (2026-08-17), after their cycle was committed at `172a1ab1` / `64828956`.** Every later reference to either file in this artifact is provenance, kept so a reader can see which round established a finding; none of it is a live pointer. The one piece of their content anything outside this cycle depended on — R3's exact current/replacement text for the four MF-1 rows, cited by `TODO-ALPHA-052-0.1.0`'s MF-1 bullet — was folded into `### MF-1` below before the deletion. Both files remain recoverable from git history.
Shape: **final test-run gate** (`docs/builder/BUILD.md` `## Final test-run gate`), with the cross-slice integration pass's two live obligations folded in per the build plan's `## Artifact list`.
Status: final-accepted

`HEAD` at the time of this pass: `acaa6b833d836aa02487eb14a57eb1c98e93354e` (unchanged from R1's and R3's passes).

**What this cycle changed:** six Markdown files, no source and no tests. Listed under `## Files this cycle wrote` below.

---

## Gate results

Every command was run from the repository root in the shared `.venv` via `uv run`. No `--cov*`-shaped flag was passed in any invocation; `--no-cov` is the only coverage-shaped flag used, and it is required because `pytest.ini`'s `addopts` auto-applies `--cov` (`docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). No line-coverage figure was inspected or asserted anywhere in this pass.

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `6145 passed, 40 skipped in 84.14s`, exit 0 |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).`, exit 0 |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit 0 |
| 4a | `uv run ruff format --check .` | **PASS** — `423 files already formatted`, exit 0 |
| 4b | `uv run ruff check .` | **PASS** — `All checks passed!`, exit 0 |
| 4c | `git diff --check` | **PASS** — no output, exit 0 |

Notes on the readings, so a later reader does not have to re-derive them:

- **Command 1 is the full sweep across all three test trees** (`AGENTS.md` line 7: package `tests/`, per-app `examples/fakeshop/apps/<app>/tests/`, live `examples/fakeshop/test_query/`). It ran under the repo's default parallel xdist configuration, which is the configuration `docs/builder/BUILD.md` `### Example-project schema changes must sync every schema-module list` requires as the backstop for order-dependent registry pollution. Zero failures, zero errors, zero collection errors.
- **Command 4a emits one pre-existing warning**, `The following rule may cause conflicts when used with the formatter: COM812`. It is ruff's standing advisory about this repo's deliberate `COM812` selection (`AGENTS.md` line 17 makes the trailing-comma layout a gate), not a failure: the command exited 0 and reformatted nothing.
- **Command 4a was observed to exit 1 exactly once, transiently, and the reading recorded above is the reproduced one.** On one intermediate invocation it exited 1 while still printing `423 files already formatted` — i.e. it reported nothing unformatted. It was immediately re-run three consecutive times, each `exit=0` with the same `423 files already formatted`. The tree carries a concurrent session actively writing Python files (`## Attribution` below), so a scan racing a mid-write file is the available explanation; no file was named as unformatted on any run, and this pass reformatted nothing. Recorded rather than quietly dropped, because a one-off non-zero exit on a gate command is exactly the shape of signal that should not be smoothed away — but it is not reproducible and names no file, so it does not block `final-accepted`.
- **No gate command failed**, so no re-loop through an owning round was triggered.

### Commands deliberately NOT run

- **No floor venv was built** — see `## Floor verification` below.
- **No `pytest` with any `--cov*` flag**, in this or any other form.
- **No write-mode lint** — `ruff format .` / `ruff check --fix .` were not run. The gate is read-only by contract, and a write-mode repo-wide run on this tree would have rewritten a concurrent session's ten dirty package files.
- **No `git stash` / `git checkout` / `git restore` / `git worktree`** was run at any point in this pass. Every HEAD comparison below used `git show HEAD:<path>` into a scratch path outside the repository, then `diff` (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`).

## Floor verification

**Declared scope: `none`.** The build plan's preamble declares `Floor-verification scope: **none.**` on the grounds that no round touches a Django / Strawberry / channels integration seam; R1 and R3 restated `none` in their own artifacts, and both are correct — this cycle changed six Markdown files and no line of Python. **Nothing was owed and nothing was skipped.**

The floor, quoted from `docs/builder/BUILD.md` `## Floor verification` rather than from memory, is **Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0**. No floor venv was created, per the plan's declaration and the gate's dispatch.

For completeness, and because `docs/builder/BUILD.md` `## Floor verification` forbids stating the shared environment's versions from memory or from a document, the shared `.venv` was **read** rather than recalled:

```shell
uv pip list | grep -Ei '^(django|strawberry-graphql|channels) '
# channels                    4.3.2
# django                      6.1
# strawberry-graphql          0.323.2
python3 -V   # Python 3.14.2
```

That reading is recorded only to make explicit that **command 1's green sweep is a top-of-range result, not a floor result**. It licenses no floor claim, and this cycle owes none.

## Folded-in cross-slice integration obligations

The build plan states that no `bld-integration.md` is produced for this cycle (R1 and R3 landed Markdown only, so there is no cross-round DRY surface) and folds two live obligations from `docs/builder/BUILD.md` `## Cross-slice integration pass` into this gate. Both are discharged here.

### Step 1 — every closed artifact read in full

Read end to end during this pass, not skimmed and not sampled:

- `docs/builder/build-017-deferred_scalars-0_0_6.md` (87 lines) — preamble, pre-flight record with both recorded deviations, baseline-dirty list, Worker-0 pre-dispatch verification (8 findings), artifact list, checklist.
- `docs/builder/bld-017-r1-rationale_and_spec_reconciliation.md` (201 lines) — including the (a)/(b)/(c) disposition tables, the per-test F3 table, the F2 branch verification, both pre-dispatch-finding corrections, and the 30-row `### Spec changes made (Worker 1 only)` table.
- `docs/builder/bld-017-r3-doc_completion_audit.md` (295 lines) — including all eleven doc-surface dispositions, both maintainer follow-ups with their exact current/replacement text, and the archive audit.
- `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` (685 lines) and `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-rationale.md` (313 lines), both in full.

Steps 2, 3, 4 and 5 of that section have no live subject here: no Python file was touched, so no shadow overview was produced by this cycle and there is no **Repeated string literals** or **Imports** section to compare across artifacts; step 5's walk of `What looks solid` / `DRY findings` is subsumed by the `### Deferred work catalog` below, which walks both artifacts' `Notes for Worker 1` sections item by item.

### Step 6 — staged-anchor sweep, re-derived

```shell
grep -rEn 'TODO\(spec-017|TODO-(ALPHA|BETA|STABLE)-017' . | grep -v '^\./\.git/'
```

Three hits, **all three inside this cycle's own build-cycle artifacts, and all three quoting the sweep pattern itself rather than staging work**:

- `docs/builder/build-017-deferred_scalars-0_0_6.md:54` — Worker 0's pre-dispatch record of this same sweep.
- `docs/builder/build-017-deferred_scalars-0_0_6.md:76` — the sentence folding this obligation into this gate.
- `docs/builder/bld-017-r1-rationale_and_spec_reconciliation.md:68` — R1's record of the same sweep.

**Zero anchors in shipped source, tests, or comments. Zero anchors anywhere outside `docs/builder/`.** Nothing is owed.

One refinement to Worker 0's pre-dispatch claim, since this gate re-derives rather than restates: Worker 0 recorded "zero hits outside `KANBAN.md`", but re-running the sweep with `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` excluded returns the **same three hits** — i.e. there are now **zero** board-file hits too. That is expected rather than surprising: card 17 is `DONE-017-0.0.6`, and `docs/builder/BUILD.md` line 11 pins that a Done card drops its `TODO-<MILESTONE>-` prefix, so the pattern cannot match a shipped card's live id. The exclusion clause is correct as a rule and simply has no subject on this card.

## Attribution: every non-green signal classified before a verdict

The working tree is legitimately dirty with a concurrent session's in-flight work (`AGENTS.md` rule 34; the build plan's `## Baseline-dirty out-of-scope files`). **Nothing on that list was edited or reverted by this pass**, and no `git` command capable of discarding another session's work was run. Every signal below was classified before any verdict was recorded.

### CS-1 — `scripts/build_tree_md.py --check` exits 1. **Concurrent session's; NOT this cycle's.**

R3 recorded and diagnosed this. Per the gate's dispatch it was **re-verified rather than restated**, read-only, and the diagnosis holds exactly.

```shell
uv run python scripts/build_tree_md.py --check
# /Users/.../docs/TREE.md is not up to date; run scripts/build_tree_md.py.   (exit 1)

# Read-only diagnosis: copy the rendered doc OUTSIDE the repo, render into the COPY, diff.
cp docs/TREE.md "$SCRATCH/TREE.copy.md"
uv run python scripts/build_tree_md.py --md "$SCRATCH/TREE.copy.md"    # exit 0
diff docs/TREE.md "$SCRATCH/TREE.copy.md"                              # exit 1
```

The entire drift is **two lines, which are one entry rendered into each of the two layouts**:

```
292c292,417c417
<     ├── converters.py             # Fail-loud converter-dispatch skeleton shared by the form + serializer converters.
---
>     ├── converters.py             # Fail-loud converter-dispatch skeleton shared by write-field and filter-input converters.
```

`git status --short -- docs/TREE.md` is empty afterwards: `docs/TREE.md` was never written by this pass, only copied.

**Attribution, proven rather than asserted.** The drifting text is `django_strawberry_framework/utils/converters.py`'s module docstring, which is on the build plan's baseline-dirty list. Comparing the worktree file against pristine `HEAD`, read-only:

```shell
git show HEAD:django_strawberry_framework/utils/converters.py > "$SCRATCH/converters.HEAD.py"
diff "$SCRATCH/converters.HEAD.py" django_strawberry_framework/utils/converters.py
# 1c1
# < """Fail-loud converter-dispatch skeleton shared by the form + serializer converters.
# ---
# > """Fail-loud converter-dispatch skeleton shared by write-field and filter-input converters.
#   (plus a three-line body change naming filters/inputs.py as a third caller)
```

**This yields a stronger result than "not ours".** The on-disk `docs/TREE.md` carries *`HEAD`'s* docstring text verbatim, so **`docs/TREE.md` is up to date with respect to `HEAD` and is stale only with respect to the concurrent session's uncommitted edit.** The `--check` failure is therefore not a pre-existing defect at `HEAD` either; it is the expected, transient consequence of a docstring edit whose regenerate has not landed yet. Whoever commits `django_strawberry_framework/utils/converters.py` owns the `scripts/build_tree_md.py` run in that same commit (`START.md` "Rendered docs — fix the source, not the file"). **Escalated to the maintainer here; not fixed, not reverted, and not this cycle's.**

### CS-2 — the baseline-dirty list has shrunk since the build plan was written. **No action; recorded so a later reader is not confused.**

`git status --short` at this pass no longer shows the spec-016 residual cycle's entries that the build plan enumerated (`docs/builder/bld-015-final.md`, `bld-016-*.md`, `build-016-*.md`, `docs/builder/DONE/build-016-fieldmeta_consolidation-0_0_6.md`), while `HEAD` is unchanged at `acaa6b83`. A concurrent session resolved its own artifact churn without a commit landing. Two files the plan listed are still dirty and were previously absent from the session-start snapshot (`django_strawberry_framework/testing/relay.py`, `tests/testing/test_relay.py`) — both are on the plan's list. **Consequence for this gate: none.** The list is a do-not-touch list; an entry leaving it removes an obligation rather than creating one, and nothing on it was touched either way.

### No other non-green signal

Commands 1 through 4c produced no failure, no error, and no warning other than ruff's standing `COM812` advisory noted above. There is no failing test row to attribute, so no `## Claims are proven mechanically, never accepted on prose` "pre-existing at HEAD" escalation is owed for the suite.

## Files this cycle wrote

Confirmed against `git status --short` at the close of this pass. Exactly six paths, all Markdown:

| Path | State | Written by |
|---|---|---|
| `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` | modified (`M`) | R1 |
| `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-rationale.md` | new (`??`) | R1 |
| `docs/builder/build-017-deferred_scalars-0_0_6.md` | new (`??`) | Worker 0 |
| `docs/builder/bld-017-r1-rationale_and_spec_reconciliation.md` | new (`??`) | R1 |
| `docs/builder/bld-017-r3-doc_completion_audit.md` | new (`??`) | R3 |
| `docs/builder/bld-017-final.md` | new (this file) | this gate |

Plus the gitignored `docs/builder/worker-memory/spec-017-worker-1.md`.

**No package source file, no test file, and no generated doc appears in that list.** `examples/fakeshop/db.sqlite3` was opened **read-only** by this pass (`file:…?mode=ro` URI) to re-derive the MF-1 row identities below; it was never written, and `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` were never regenerated.

Byte counts re-measured with `wc -c` at this working tree, because two artifacts disagree by two bytes and a stated count is a claim like any other:

| File | Bytes now | R1 recorded | R3 recorded |
|---|---|---|---|
| `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` | 62,677 | 62,677 | 62,677 |
| `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-rationale.md` | **41,325** | 41,323 | 41,325 |
| `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-terms.csv` | 1,754 | — | 1,754 |

R3's figure is the correct one. R1's 41,323 was measured mid-pass against a self-referential figure it was still iterating (its own `## Provenance of this record` table quotes its own size), and the file grew two bytes before the pass closed. **`41,325` is the number a later reader should use**; the companion's own table still states `41,323` and is stale by two bytes. Recorded rather than corrected — the file is out of this gate's writable set, the discrepancy is cosmetic, and correcting a self-referential byte count re-opens the same fixed-point iteration.

## Verification carried over and re-derived

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-017-deferred_scalars-0_0_6.md` → **exit 0**, `OK: 16 terms - all have glossary entries and at least one spec link.` Re-run at this pass, not carried on R1's or R3's word.
- The spec's status/header lines were re-read at the start of this spawn (`docs/builder/worker-1.md` `## Spec status-line re-verification`): `Target release: 0.0.6.` / `Status: shipped in 0.0.6.` / `Owner: package maintainer.` / `Predecessors: …` / `Card line: …` plus R1's rationale pointer. **No status line is falsified by this gate; no edit made.** One *body* line is falsified — see MF-3.

---

## Deferred work catalog

The next spec author's reading list (`docs/builder/BUILD.md` `## Final test-run gate`). Every item explicitly deferred by either closed round is below, one bullet each. **Each item's population is enumerated inline — rows, files, and counts — rather than pointed at by artifact name**, because per-cycle `bld-*.md` artifacts are deleted at the next build's pre-flight while cards keep citing them, so a bullet reading "see the R3 artifact" becomes unreadable.

Every count below was re-derived at this pass by grepping the **shortest distinctive token** and counting **occurrences**, not matching lines.

### MF-3 — `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` still carries one falsified `BigAutoField` sentence. **NEW at this gate; not recorded by either round.**

**Source:** found by this gate's folded-in `## Cross-slice integration pass` step 1 (reading both closed artifacts and both spec files in full). It is the one item in this catalog that is a **defect in this cycle's own deliverable** rather than work deliberately deferred.

**The surviving text**, `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` #"No current-day consumer recourse", the third bullet of Decision 1's target-Django-fields list:

```text
- `BigAutoField` → `int` (preserved). No current-day consumer recourse for the `2**31` boundary — wait for [Scalar field override semantics][glossary-scalar-field-override-semantics].
```

**Why it is false at `HEAD`:** the recourse shipped in the *same release*. `DONE-019-0.0.6` landed consumer annotation overrides, and `docs/GLOSSARY.md`'s `Scalar field override semantics` entry reads `shipped (0.0.6)`. There is nothing to wait for.

**Population, established mechanically.** The claim lived at three sites in the pre-reconciliation spec. R1 fixed two and missed the third:

```shell
grep -n 'current-day' docs/SPECS/spec-017-deferred_scalars-0_0_6.md    # 1 occurrence: line 310
grep -n 'wait for'    docs/SPECS/spec-017-deferred_scalars-0_0_6.md    # 1 occurrence: line 310 (same sentence)
```

- `## Risks and open questions`, the `BigAutoField` bullet — **fixed** (deleted; recorded at rationale companion #"BigAutoField` deferred with \"no current-day recourse\"").
- `## Edge cases and constraints`, the `BigAutoField` bullet — **fixed** (now reads "handled by the consumer annotation override (`DONE-019-0.0.6`)").
- **Decision 1's target-fields list — NOT fixed. The one live occurrence.**

**Two consequential knock-ons in the rationale companion**, which must be corrected in the same edit or the companion becomes self-falsifying:

- `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-rationale.md` #"none is restored anywhere as live text" — that sentence's list includes the `BigAutoField` "no current-day recourse" claim, and the claim **is** live text at spec line 310.
- Same file, #"the spec's Risks bullet was not, which is why it is deleted rather than moved" — implies the spec no longer makes the claim; it does.

**Exact replacement text for the spec bullet** (matching the wording `## Edge cases and constraints` already uses, so the two agree):

```text
- `BigAutoField` → `int` (preserved). A PK past the `2**31` boundary is handled by the consumer annotation override shipped by the sibling card `DONE-019-0.0.6` ([Scalar field override semantics][glossary-scalar-field-override-semantics]), not by this card.
```

The reference-style link `[glossary-scalar-field-override-semantics]` is already defined in the spec's bottom block, so the scaffold needs no change and `check_spec_glossary.py` stays green (the term keeps a carrier).

**Why this gate did not execute the fix.** The gate's dispatch authorizes a spec or rationale edit *only if a gate command exposes a defect in them*. No gate command did — commands 1 through 4c are all green, and this was found by reading. Stretching "a grep I ran while enumerating this catalog" into "a gate command" would be exactly the kind of after-the-fact reframing this process exists to prevent, so the finding is **escalated with the exact replacement text supplied and left unexecuted**. **Target: maintainer** — either apply the three-site edit directly at commit, or re-dispatch a one-pass R1 spec-custodian correction. Both are one edit's worth of work; neither needs rediscovery.

**Why it did not block `final-accepted`.** It is a documentation residue in an archived spec for a card that shipped at `0.0.6`; it falsifies no code contract, no test, and no standing doc, and every mechanical gate is green. It is recorded first in this catalog because it is the item most likely to be lost.

### MF-1 — the `DONE-017-0.0.6` KANBAN card still claims the deprecation is "suppressed at the definition site"

**Source:** `docs/builder/bld-017-r3-doc_completion_audit.md` `## Obligation 2` and its `### Notes for Worker 1 (spec reconciliation)`. **Licensed by** the build plan's `**No round in this cycle is authorized to write the DB or regenerate those three docs**` — `examples/fakeshop/db.sqlite3` is concurrent-writable and a hand-edit of the rendered `KANBAN.md` is silently reverted by the next regenerate (`docs/builder/BUILD.md` `### Generated docs are DB-backed`).

**What is false:** the card says the Strawberry class-direct-to-`scalar()` `DeprecationWarning` is "suppressed at the definition site" behind a "tight `warnings.catch_warnings()` filter". No suppression exists at `HEAD` — `django_strawberry_framework/scalars.py` defines `BigInt` as a bare `NewType`, binds behavior through `_BIGINT_SCALAR_DEFINITION` built from Strawberry's no-warning `name=`-only `strawberry.scalar(...)` overload, and registers it through `_PACKAGE_SCALAR_MAP` behind the public `strawberry_config()` factory. `DONE-025-0.0.7` removed the suppression (`docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` Decision 6, "Remove the `warnings.catch_warnings()` suppression block").

**Population, re-derived at this pass, twice — rendered and DB-side:**

```shell
# rendered: the DONE-017-0.0.6 card body spans KANBAN.md lines 4235-4302
awk '/^### \[DONE-017-0\.0\.6/{f=1} f&&/^### \[/&&!/DONE-017-0\.0\.6/{f=0} f' KANBAN.md \
  | grep -o 'suppress[a-z]*' | sort | uniq -c
#    3 suppressed
#    1 suppression        -> 4 occurrences
```

DB side, opened read-only (`sqlite3.connect("file:examples/fakeshop/db.sqlite3?mode=ro", uri=True)`) so the concurrent writer is never blocked:

- `kanban_card` `id=39`, `number=17`, `title="Deferred scalar conversions"`.
- `kanban_carditem` **`id=703`** (note section), **`id=713`** (test-plan section), **`id=715`** (note section) — the three rows whose `text` contains `suppress`.
- `kanban_cardreference` **`id=62`** (`source_card_id=39` → `target_card_id=47`, and card 47 is confirmed `number=25`, `title="Warning-free scalar registration via `StrawberryConfig.scalar_map`"`, i.e. `DONE-025-0.0.7`), field `raw_text`.
- **Rows `715` and `62` are byte-identical** — verified by direct string comparison at this pass, not assumed. **They must be amended together** or the rendered card contradicts itself. The `{{card_ref:1}}` placeholder inside them is FK-backed and must be kept verbatim.

Four rows, four occurrences, one each. **Target: maintainer**, on a tree where no concurrent session is live on the DB.

The exact current and replacement text for all four rows follows. **It was folded in here from R3's `## Obligation 2` when R1 and R3 were deleted at closeout** (see the note under the header above) — it is the one piece of either artifact that anything outside this cycle depends on, since `TODO-ALPHA-052-0.1.0`'s MF-1 bullet cites it.

**1. `kanban.CardItem` `id=703`** (section `note`, order `1`). Current:

```text
Public `BigInt` scalar (`django_strawberry_framework/scalars.py`, `NewType`-based) with the Strawberry class-direct-to-`scalar()` `DeprecationWarning` suppressed at the definition site so consumers see no warning at import time.
```

Replacement:

```text
Public `BigInt` scalar (`django_strawberry_framework/scalars.py`, `NewType`-based). At `0.0.6` the Strawberry class-direct-to-`scalar()` `DeprecationWarning` was suppressed at the definition site so consumers saw no warning at import time; that suppression no longer exists — see the registration note below.
```

**2. `kanban.CardItem` `id=713`** (section `test_plan`, order `0`). Current:

```text
100% coverage via `tests/test_scalars.py` (new flat file) and `tests/types/test_converters.py` (extended). Includes a `test_package_import_does_not_emit_strawberry_deprecation_warning` guard so future regressions to the suppression are explicit.
```

Replacement:

```text
100% coverage via `tests/test_scalars.py` (new flat file) and `tests/types/test_converters.py` (extended). Includes a `test_package_import_does_not_emit_strawberry_deprecation_warning` guard so future regressions to the warning-free import surface are explicit.
```

The test survives under that name; only what it guards changed.

**3. `kanban.CardItem` `id=715`** (section `note`, order `12`) **and 4. `kanban.CardReference` `id=62`** (`source_card_id=39`, `target_card_id=47`), field `raw_text`. Current text of **both** (the `{{card_ref:1}}` placeholder is FK-backed — keep it verbatim):

```text
The internal Strawberry deprecation about passing a class (or `NewType`) to `strawberry.scalar(...)` is suppressed at the definition site (tight `warnings.catch_warnings()` filter). The package import surface is therefore clean. Migration to a `StrawberryConfig.scalar_map`-based design is roadmapped as `{{card_ref:1}}` — that path is a real public-API change (consumers using `BigInt` directly will merge a package-provided `StrawberryConfig` into their `strawberry.Schema(...)`), not an internal-only refactor.
```

Replacement for **both**:

```text
The internal Strawberry deprecation about passing a class (or `NewType`) to `strawberry.scalar(...)` was suppressed at the definition site at `0.0.6` (tight `warnings.catch_warnings()` filter), keeping the package import surface clean. `{{card_ref:1}}` replaced that suppression: `BigInt` is now a bare `NewType` bound to a `ScalarDefinition` built from Strawberry's no-warning `strawberry.scalar(name=...)` overload and registered through the package scalar map that the public `strawberry_config()` factory merges into a consumer's `strawberry.Schema(...)` — the real public-API change this note anticipated, not an internal-only refactor.
```

Edit through the Django ORM against `examples/fakeshop/db.sqlite3` (never raw SQL — `post_save` writes the side rows the render needs), then regenerate both rendered surfaces:

```shell
uv run python scripts/build_kanban_md.py
uv run python scripts/build_kanban_html.py
```

Verify by re-running the occurrence count: `awk` over the `DONE-017-0.0.6` card range piped through `grep -o 'suppress[a-z]*'` must report **3 occurrences**, all past-tense inside the amended sentences, and zero occurrences of `is suppressed at the definition site`. `KANBAN.html`'s hand-edited Vue shell is untouched by the regenerate; only its data block moves.

### MF-2 — `CHANGELOG.md`'s `[0.0.6]` entry labels this card with its pre-renumber number

**Source:** `docs/builder/bld-017-r3-doc_completion_audit.md` `### `CHANGELOG.md` — **(b)**` and `## Obligation 2`. **Licensed by** `AGENTS.md` rule 21 (no `CHANGELOG.md` edit without being told — the spec's Slice 6 grant covered writing the `0.0.6` entry at ship time, not re-editing it now) **and** by the whole-cluster rule below.

**Population:** exactly **one occurrence**, `CHANGELOG.md:210`, in the `[0.0.6]` `Added` `BigInt` bullet: `Tracked as [013-deferred_scalar_conversions-0.0.6][card-deferred-scalar-conversions]`. The card is `DONE-017-0.0.6`; `013` is a pre-board-renumber name (today `spec-013` is the archived real-M2M stub). **Label-only** — the link definition `[card-deferred-scalar-conversions]: KANBAN.md#deferred_scalar_conversions` resolves correctly.

**Target:** fold into the carded renumber sweep named in the next item, **not** fixed alone. A partial fix leaves the cluster divergently rather than uniformly wrong.

### The `[spec-013]` ref-id cluster in `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`

**Source:** the build plan's `**Known-wrong across multiple surfaces, deliberately NOT partial-fixed here**`, re-recorded by R1 (`### Notes for Worker 1`, "Deferred-work catalog input for the final gate") and by R3 (`### Explicitly changed nothing`). **Licensed by** `KANBAN.md:349`, which already cards the whole documentation-only cluster onto `TODO-ALPHA-051-0.0.15` / `TODO-ALPHA-052-0.1.0` and states why it must land whole, and by `worker-0.md` "Verify card/glossary references against the DB", which forbids correcting one surface of a multi-surface wrong reference.

**Population, re-derived at this pass — and the count needs one refinement both rounds' phrasing leaves ambiguous:**

```shell
grep -o '\[spec-013\]' docs/SPECS/spec-025-scalar_map_helper-0_0_7.md | wc -l   # 6
```

**Six occurrences: five uses plus one definition.** Both rounds say "five occurrences" / "five links", which is right about the *uses* and one short of the total. Enumerated so the sweep cannot miss the definition:

- `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md:6` — one use, in the `Predecessors:` line.
- `:64` — **two** uses in one line (Decision 1 and Decision 6 both cited).
- `:319` — one use.
- `:335` — one use.
- `:706` — the **definition**, `[spec-013]: spec-017-deferred_scalars-0_0_6.md`. It resolves correctly; only the label is a pre-renumber artifact. **Renaming the five uses without this line breaks all five.**

Sibling surfaces of the same cluster, already recorded by R3's `### Pre-archive / mis-citation sweep` and re-listed here so the sweep is self-contained: `KANBAN.md:349`, `docs/SPECS/spec-018-meta_primary-0_0_6.md`, `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`, `docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-rationale.md`, plus MF-2's `CHANGELOG.md:210`. **Target: `TODO-ALPHA-051-0.0.15` / `TODO-ALPHA-052-0.1.0`.**

### `docs/TREE.md` regenerate, owed by whoever commits the concurrent session's `utils/converters.py`

**Source:** `docs/builder/bld-017-r3-doc_completion_audit.md` `## Gates` and its `### Notes for Worker 1`. Re-verified at this gate as **CS-1** above, with the added result that `docs/TREE.md` is **not** stale with respect to `HEAD` — it matches `HEAD`'s docstring exactly, and only the uncommitted worktree edit diverges. **Not a spec-017 item at all**; catalogued so a later reader does not attribute the `--check` failure to this cycle. **Target: whoever commits `django_strawberry_framework/utils/converters.py`**, in that same commit.

### Explicitly NOT deferred

- **No code work.** R1's audit resolved every `## Slice checklist` sub-check, `## Goals` bullet, `## User-facing API` row, `## Test plan` category (1-19), and `## Definition of done` item to either **(a)** present at `HEAD` or **(b)** deliberately superseded by later work, with **zero (c) "never shipped"** dispositions and no defect found. No contingent R2 round was opened, and none is owed.
- **No archive move.** The spec sits at `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` and both companions at `docs/SPECS/appx/`; R3's placement audit confirmed it. Do not "re-archive".
- **No `docs/GLOSSARY.md`, `docs/README.md`, root `README.md`, or `TODAY.md` work.** All four were audited to **(a)** correct and current on every point this card's contract reaches — including the two GLOSSARY entries R1 flagged as *suspected* carriers of suppression wording, which turned out to have been corrected already.

---

## Summary

The final test-run gate for the spec-017 residual-completion cycle. **All six gate commands pass**: the full sweep across all three test trees (`6145 passed, 40 skipped`), both Django consistency checks, and all three read-only lint/format/diff commands. **Floor verification was declared `none` and correctly owed nothing** — the cycle changed six Markdown files and no line of Python — so no floor venv was built; the shared `.venv`'s versions were read rather than recalled solely to make explicit that the green sweep is a top-of-range and not a floor result.

Both folded-in integration obligations are discharged: every closed artifact and both spec files were read in full, and the staged-anchor sweep re-derives to **zero anchors in shipped source, tests, or comments** (the only three hits are this cycle's own artifacts quoting the sweep pattern, and there are now zero board-file hits because a Done card's id cannot carry a `TODO-` prefix).

Every non-green signal was classified before a verdict. **One exists**: `scripts/build_tree_md.py --check` exits 1. R3's diagnosis was re-verified read-only rather than restated — copy the rendered doc outside the repo, render into the copy, diff — and holds exactly: two lines, one `utils/converters.py` docstring entry rendered into both layouts, from a concurrent session's baseline-dirty file. Comparing that file against pristine `HEAD` yields a stronger result than "not ours": **`docs/TREE.md` matches `HEAD` exactly and is stale only against an uncommitted edit**, so this is not a pre-existing defect at `HEAD` either. Escalated to the maintainer; not fixed, not reverted. No test failed, so no failing-row escalation is owed.

The `### Deferred work catalog` carries five items with every population enumerated inline — rows, files, and counts — so each survives the deletion of the artifacts that recorded it. **One is new at this gate and is the item worth the maintainer's attention: MF-3.** Decision 1's target-fields list still says `BigAutoField` has "no current-day consumer recourse — wait for Scalar field override semantics", false since the sibling card `DONE-019-0.0.6` shipped that recourse in the same release. R1 identified this exact false claim and corrected two of its three sites, leaving the third live — and the rationale companion consequently asserts twice that the claim survives nowhere as live text, which the surviving sentence falsifies. Exact replacement text is supplied; the fix was **not executed** because no gate command exposed it and this gate's writable set conditions a spec edit on exactly that.

Two counts recorded by earlier passes were re-derived and refined rather than repeated: the `[spec-013]` cluster is **six occurrences — five uses plus the definition line that all five depend on**, where both rounds' "five" describes only the uses; and the rationale companion measures **41,325** bytes, not R1's mid-pass 41,323.

Final status: **`final-accepted`**.
