# Build: Final gate — spec-041 Channels ASGI router reconciliation cycle

Spec reference: `docs/SPECS/spec-041-channels_router-0_0_14.md` (whole file; 1832 lines)
Status: final-accepted

Cycle type: **post-ship reconciliation round**, per
`docs/builder/build-041-channels_router-0_0_14.md`. One slice
(`docs/builder/bld-041-slice-1-rationale_and_spec_reconciliation.md`, `Status: final-accepted`),
no integration pass owed — a single-slice cycle has no cross-slice surface — and the one
integration duty that still applies with one slice, the staged-anchor sweep, is folded in below.

---

## Gate scope, and why it deviates

`docs/builder/BUILD.md` `## Final test-run gate` prescribes a `pytest` run. This cycle does not
run one, and the build plan's `## Final gate scope` records the reason rather than leaving the
omission bare. Restated here so this file stands alone:

1. **No `.py` file changed in this cycle.** `git diff -- django_strawberry_framework/ tests/`
   contains nothing this cycle authored; the cycle wrote two markdown files and edited a third.
   A green suite would therefore be evidence about somebody else's code, not this build's.
2. **The tree is dirty with a concurrent cycle's in-flight source edits.** `spec-050` is mid-build
   on this checkout, with modified files under `django_strawberry_framework/`, `tests/` and
   `examples/`. A failing row could not be attributed to this build at all, and attributing it
   anyway is how a cycle inherits another cycle's regression.
3. `AGENTS.md` #"No pytest after edits" independently forbids a run absent a maintainer request.

The gate therefore runs every read-only check that **can** see this cycle's output, and records
each instrument's actual input beside its result. Two of the checks below are structurally blind
to the files this cycle wrote; that is stated at each, because a green checker is evidence only
for what it reads, and two gates agreeing is not corroboration when neither can see the other's
failure.

## Gate results

All run from the repository root in this pass.

| Instrument | Input it actually reads | Result |
| --- | --- | --- |
| `uv run ruff format --check .` | every `.py` file in the tree, this cycle's and the concurrent cycle's alike | **445 files already formatted**, exit 0 |
| `uv run ruff check .` | same | **All checks passed!**, exit 0 |
| `git diff --check` | whitespace errors in the unstaged diff, whole tree | clean, exit 0 |
| `uv run python scripts/check_citations.py --check` | first-party `.py` files and `KANBAN.md` **only** | **OK: 981 citations resolve (814 in 442 .py files, 167 in KANBAN.md)**, exit 0 |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-041-channels_router-0_0_14.md` | the spec plus `docs/SPECS/appx/spec-041-channels_router-0_0_14-terms.csv` (31 lines = 30 rows + header, clean in `git status`) | **OK: 30 terms - all have glossary entries and at least one spec link.**, exit 0 |
| `uvx pre-commit run --files <the four cycle paths>` | the four paths named below, explicitly | all hooks Passed, exit 0 |

### What each green does and does not establish

- **`ruff format --check` / `ruff check`.** Both carry a standing advisory that `COM812` may
  conflict with the formatter. It is pre-existing configuration in `pyproject.toml`, not this
  cycle's: this cycle touched no `.py` file and no lint configuration. Recorded, not fixed. Worker
  0 read the same two numbers at dispatch time (`445 files already formatted`,
  `All checks passed!`); this is an independent re-run, not a quotation of that reading.
- **`check_citations.py`.** Reads `.py` files and `KANBAN.md` and is **blind to both markdown
  files this cycle wrote**. Its green means this cycle broke no existing `path::Symbol` citation
  elsewhere in the tree. It is not evidence that the pair's own citations resolve; that evidence
  is the 46-occurrence AST resolution recorded in the slice artifact and re-run at final
  verification.
- **`check_spec_glossary.py`.** Compares term and anchor only. The `notes` prose beside each row
  drifts ungated, so its green says nothing about the glossary vocabulary the reconciliation
  rewrote. The `-terms.csv` was not writable this cycle and was not touched.
- **`pre-commit`.** Green on the first run. The `source-layout` hook auto-fixes by default and a
  rewrite fails the run, so a first-run green is the evidence that it rewrote nothing — the
  link-definition scaffold in both new files was authored correctly. Explicit paths always: the
  hook's default is a repo-wide auto-fix that would rewrite the concurrent session's untracked
  files.

Command, in full:

```shell
uvx pre-commit run --files docs/SPECS/spec-041-channels_router-0_0_14.md \
  docs/SPECS/appx/spec-041-channels_router-0_0_14-rationale.md \
  docs/builder/bld-041-slice-1-rationale_and_spec_reconciliation.md \
  docs/builder/build-041-channels_router-0_0_14.md
```

```
kanban tracked path constants...................................Passed
source layout (py trailing commas + ascii-only; md link-def
  scaffold; json/graphql brace explosion).......................Passed
ruff format.....................................(no files to check) Skipped
ruff check......................................(no files to check) Skipped
kanban anchors collision-free...................................Passed
citations resolve (AGENTS.md rule 27 path::Symbol refs).........Passed
```

The two `ruff` hooks skip because the cycle touched no `.py` file — which is the same fact the
gate-scope deviation rests on, reported by a second instrument.

## Staged-anchor sweep

The one cross-slice-integration duty that still applies to a single-slice cycle. Re-derived here
rather than adopted:

```shell
grep -rEn 'TODO\(spec-041|TODO-(ALPHA|BETA|STABLE)-041' --include='*.py' --include='*.md' .
```

- Population over `.py` and `.md`, excluding `.venv/`: **6**.
- Population in `.py` files: **0**. No source file carries a staged anchor for this build's spec
  or card, so nothing this cycle shipped left an anchor behind and nothing names a still-open
  slice.
- All six hits are prose *describing* an anchor, not a live anchor: the spec's `## Slice checklist`
  row requiring one for any staged seam, two in this cycle's companion (the round-vocabulary entry
  and the card-annotation record), one in `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`,
  and **two in this cycle's own slice artifact** — the two sentences that report this sweep.
- Worker 0 measured **4** at dispatch time. The difference is not drift: the two artifact
  sentences did not exist when Worker 0 ran it. A census run over a corpus it is itself being
  written into reports a different number every time it is written down, which is why the split is
  stated here rather than a single total.

## Floor verification confirmation

The build plan declares floor-verification scope **`none`**, and the declaration is deliberate
rather than an omission: no slice in this cycle touches a Django / Strawberry / channels
integration seam, because no slice touches executable code. No floor run was owed, none was run,
and no floor claim in this cycle rests on an unrun gate.

The floor itself, read from `docs/builder/BUILD.md` `## Floor verification` and never from memory:
Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**. The shared `.venv` is
not the floor; `uv pip list` in this cycle read `channels 4.3.2`, `daphne 4.2.2`, `django 6.1`,
`strawberry-graphql 0.324.0`. That reading is load-bearing for two of the cycle's findings and is
cited wherever it is used. No install into, downgrade of, or other mutation of the shared `.venv`
happened in any pass.

## Hot-path budget

The build plan declares hot-path scope **`none`**. Deliberate for the same reason: the cycle adds
no serialization point, no lock, no extra pass over a result set and no per-item work, because it
adds no executable code at all.

## Working-tree disposition

`git status --short` at the close of this gate lists this cycle's four paths and no others of its
own:

- `docs/SPECS/spec-041-channels_router-0_0_14.md` — modified.
- `docs/SPECS/appx/spec-041-channels_router-0_0_14-rationale.md` — new, untracked.
- `docs/builder/bld-041-slice-1-rationale_and_spec_reconciliation.md` — new, untracked.
- `docs/builder/build-041-channels_router-0_0_14.md` — new, untracked (Worker 0's).

Plus `docs/builder/bld-041-final.md`, this file, and the untracked scratch
`docs/builder/worker-memory/worker-1-041.md`.

Every other dirty path belongs to the concurrent `spec-050` session. None was edited, staged,
reverted or stashed at any point in this cycle. No `git stash`, `git checkout --`, `git restore`
or `git worktree` was run; HEAD was read with `git show HEAD:<path>` into a scratch path outside
the repository. Nothing is committed — only the maintainer commits.

## Deferred work catalog

Everything this cycle found in a surface it could not write. Each carries a named owner, so
nothing is routed forward unhomed.

1. **The dependency decision: does the Channels floor move, or does the
   `Framework :: Django :: 6.1` classifier get qualified?** Source:
   `docs/builder/bld-041-slice-1-rationale_and_spec_reconciliation.md`
   `### Escalated to the maintainer (not acted on)`. Owner: **the maintainer**, as a contract-level
   call on the package's public install hint. Both facts verified at source in this cycle:
   `pyproject.toml` advertises `Framework :: Django :: 5.2`, `6.0` **and `6.1`**, while the
   installed `channels 4.3.2`'s own metadata classifiers stop at `Framework :: Django :: 6.0`. The
   spec now states only what is verifiably true and makes no whole-range promise. Rejected
   alternatives, each with the reason it lost:
   - *Bump `CHANNELS_FLOOR` and the `channels[daphne]` row to a 6.1-classifying release* — a `.py`
     plus packaging-metadata change no worker in this cycle may make, needing its own suite run and
     a `uv.lock` regeneration, and no such Channels release is installed here to bump to.
   - *Qualify or drop the `6.1` classifier* — it is a claim about the package's own tested surface;
     CI exercises 6.1, and withdrawing it to make one soft dependency's range statement true would
     understate support for every consumer who never installs `channels`.
   - *Keep the whole-range wording and footnote the gap* — the wording is falsifiable and now
     false; a footnote leaves the reader two statements and no way to tell which is current.
   - *Say nothing about 6.1* — the spec's stated justification for the floor **is** the advertised
     range, so silence reads as oversight rather than decision.
2. **Three parallel sites that ride that same answer, all outside this cycle's writable set.**
   Source: the slice artifact's `## Review (Worker 3, pass 2)`
   `### Notes for Worker 1 (spec reconciliation)`, re-derived in this pass — the phrase
   `whole advertised Django range` returns **3** occurrences repo-wide outside this cycle's own
   artifacts (`docs/GLOSSARY.md` 1, `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` 2). Owner:
   **the maintainer**, in one pass with item 1; fixing `spec-041` alone is the partial claim fix
   that leaves the dominant residual defect.

   **Corrected and DISCHARGED 2026-09-11 by this cycle's slice 2**
   (`docs/builder/bld-041-slice-2-deferral_homing.md`). Two errors in the paragraph above and in
   the bullets below, both of the same shape — a **phrase** count reported as a **claim** count:
   - The phrase count and the claim population are different numbers, and only the phrase count
     was measured. `spec-042` carried **4** sites asserting the range, not 2: the two the phrase
     reaches, plus one in its `Definition of done` reading *covering the advertised Django range
     through 6.0* and one in its Decision 5 body reading *the package's advertised Django 6.0
     range* — neither containing the word *whole*, and both quoted here in their pre-correction
     spelling, which no longer exists in the file. The repo-wide claim population was therefore
     **5**, not 4 — and the `pyproject.toml` comment was counted into the 4 while containing the
     phrase nowhere, so the figure was wrong in both directions at once.
   - The `pyproject.toml` bullet states the comment "belongs to the `django-debug-toolbar>=7.0.0`
     row **above** it". The direction is inverted: the comment block precedes and describes the
     row **below** it. The bullet's substantive point — that the comment and the `spec-042` sites
     are one question rather than two — is unaffected and now sits on the board.
   All 5 sites are corrected in the working tree, uncommitted: `docs/GLOSSARY.md`'s entry via a
   `GlossaryTerm` body edit plus a `scripts/build_glossary_md.py` render, and `spec-042`'s 4 in
   place. The `pyproject.toml` comment is the one site still owed, and it rides item 1's
   decision.
   - `docs/GLOSSARY.md`'s `DjangoGraphQLProtocolRouter` entry body, at the clause
     `#"one floor covering the package's whole advertised Django range through 6.0"` — **1**
     occurrence. Consumer-facing, and **rendered from the fakeshop glossary DB**, so the fix is an
     ORM edit plus `scripts/build_glossary_md.py`, never a hand-edit: a hand-edit is reverted by
     the next render and goes red in CI's generator `--check`.
   - `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` — **2** occurrences, the same sentence shape for
     the `django-debug-toolbar>=7.0.0` floor: one in its `## Slice checklist` dependency-gate row
     and one in its `### Error shapes` section. A different card's spec.
   - `pyproject.toml`'s comment ending
     `#"Framework :: Django :: 6.0 classifier the package itself advertises."` — it sits three
     lines below the `channels[daphne]>=4.3.2` row but belongs to the `django-debug-toolbar>=7.0.0`
     row above it, which is why it and the `spec-042` pair are one question, not two.
3. **The board-owned card-id renumber for `spec-041`.** **Re-measured and homed 2026-09-11 by
   slice 2**: the row's `spec-041` figures hold, and the two populations are now enumerated on
   the alpha documentation-debt card with per-file counts and a decided-non-edit grading — the
   `062` census row amended, the `068` family given a row of its own, which it had never had.
   The original text follows unchanged. Source: the slice artifact's
   `### Counts re-measured in this pass` and the companion's Doc-updates-and-Slice-2-wrap change
   record. Owner: **the `KANBAN.md` card-id census**, which requires one pass over all 34
   spec-surface sites rather than a per-spec share. Re-measured this cycle: the pair carries
   `TODO-BETA-062-0.1.5` ×3 (spec 2, companion 1) and `TODO-BETA-068-0.1.8` ×4 (spec 3,
   companion 1); **5 of those 7 are renumberable sites** (the companion's one of each quotes the id
   inside a sentence declaring it stale, the class the census already excludes from its own
   sweepable total). The census currently records `spec-041 3` for the `062` population, taken when
   `spec-041` was one file; the total still sums, but only 2 of the 3 are renumberable. The
   `068` → `071` family is the same 2026-08-29 board-insert renumber and is **not yet enumerated**
   in that census at all — surfacing it is this cycle's contribution.
4. **The `-terms.csv` `notes` column is ungated.** Source: this file's
   `### What each green does and does not establish`. Owner: the existing `KANBAN.md` item that
   already owns the "decide whether the `notes` column of a spec's `-terms.csv` is contract text"
   ruling; recorded here only because this cycle rewrote vocabulary the gate cannot see and should
   not be read as having verified it.

No other deferral exists. No finding from either review round was rejected, none was left
un-homed, and no code defect was found for Worker 0 to re-partition.

**Disposition at 2026-09-11, after slice 2.** Items 1 and 2 now sit on the boundary-hardening /
DRY-squeeze card, which already owns the `[dependency-groups]` and extras surface and is the only
`To Do` card that opens those rows; the beta release card excludes version floors by name. Items 3
and 4 sit on the alpha documentation-debt card, item 3 with the corrected census above. Item 1 is
the only one of the four that is still a *decision* rather than scheduled work.

## Final status

`final-accepted`.

- Slice 1: `final-accepted` (`docs/builder/bld-041-slice-1-rationale_and_spec_reconciliation.md`).
- Every gate in `## Gate results` passed, with its input stated.
- Staged-anchor sweep: 0 in `.py`, 6 prose mentions, split explained.
- Floor-verification scope `none` and hot-path scope `none`, both declared deliberately and
  neither resting on an unrun claim.
- Four deferred items catalogued, each with a named owner.

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
