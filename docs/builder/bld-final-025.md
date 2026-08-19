# Build: Final test-run gate — spec-025 (scalar_map_helper / 0.0.7)

Spec reference: `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` (whole file) + `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md`
Status: final-accepted

**This gate was reopened after it first closed.** Everything from `## Plan (Worker 1)` through `### Summary` below is the original pass, which ran against a **thirteen**-divergence record. Worker 0 then re-derived the deferred-work catalog and found a fourteenth divergence (D14) that the whole cycle had missed, a Slice 3 was dispatched, and this artifact's `### Deferred work catalog` was revised. Read `## Reopening: Slice 3 and the fourteenth divergence` before treating any count in the original pass as current — that section states which of them still hold and which are scoped to a pass that ended at thirteen.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not re-run for this pass and correctly so: `git status --short` shows no diff under `django_strawberry_framework/` attributable to this cycle (the two dirty package files, `_strawberry_patches.py` and `optimizer/hints.py`, are the concurrent cycles' and are in the plan's baseline-dirty list), so the inventory Slice 1 refreshed over the whole package is still current. Shapes it searched — `scalar`, `config`, `parse`, `serialize`, `label`, `safe` — are the same shapes this gate touches, and this gate proposes no helper: it runs read-only commands and, where a defect surfaced, edits Markdown.
- **Existing patterns reused.** The gate's own instruments were rebuilt rather than inherited from the slices' prose: an anchor sweep, a reference-id / link-target sweep, and a `#"..."` substring sweep, each stripping fenced blocks **and** inline code spans, and each handling a fence nested inside a blockquote (`> ```python`) — the shape both slices' pinned GLOSSARY bodies use. A first cut of the anchor instrument replaced code spans with `re.S` and silently collapsed newlines, so its line numbers were wrong while its count was right; the reported line numbers below come from the line-preserving version.
- **New helpers justified.** None. No `.py` file is touched by this cycle or by this pass.
- **Duplication risk avoided.** The one duplication risk in a two-file Markdown cycle is a fact stated in both the spec and the rationale drifting apart. That is exactly what this pass found (three sites, below), and the fix in each case removed the drift rather than restating the fact in a third place.

### Implementation steps

1. Run the five gate items in `docs/builder/BUILD.md` `## Final test-run gate` order and record each verbatim.
2. Record the plan's floor-verification declaration and that no floor run was owed. Build no floor venv.
3. Re-derive every population in both slice artifacts that this gate's catalog or verdict depends on; never carry a figure forward.
4. Perform the cross-slice coherence scan the cycle deliberately has no `bld-integration.md` for: does the rationale contradict the spec, or itself, anywhere Slice 2's own pass should have caught?
5. Write the `### Deferred work catalog`, re-measuring every item before writing it down.

### Test additions / updates

None. No `.py` file, no test. The full sweep in gate item 1 is the only test invocation this pass makes and it is a whole-tree run, not a focused scope.

### Implementation discretion items

- **Whether the three coherence defects found in the rationale warrant `revision-needed` or an in-pass fix.** Decided: in-pass fix. All three are in `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md`, which is Worker 1's own file in a cycle where Worker 1 is the sole writing role; there is no builder to route a re-loop to, and `revision-needed` on a Markdown slice whose custodian is the pass performing the audit would be ceremony. Each is recorded under `### Spec changes made (Worker 1 only)`.

### Spec slice checklist (verbatim)

This is the final gate, not a spec slice and not a review round, so there is neither a `## Slice checklist` sub-bullet set to copy nor a findings cohort. The obligations this pass is audited against are the five gate items in `docs/builder/BUILD.md` `## Final test-run gate` plus the `### Deferred work catalog`, tracked here:

- [x] `uv run pytest --no-cov` — full sweep, all three test trees.
- [x] `uv run python examples/fakeshop/manage.py check`.
- [x] `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`.
- [x] `uv run ruff format --check .`, `uv run ruff check .`, `git diff --check` — all read-only, no `--fix`.
- [x] Floor verification: the plan declares scope `none`; declaration recorded, no floor run owed, no floor venv built.
- [x] `### Deferred work catalog` written, every population re-derived.
- [x] Cross-slice coherence confirmed in place of the absent `bld-integration.md`.

---

## Build report (Worker 2)

Not applicable. Worker 2 was never dispatched in this cycle — no code change was needed (`docs/builder/build-025-scalar_map_helper-0_0_7.md` `## Cycle shape`), and this pass is Worker 1's. The record of what this pass ran and wrote is `## Final verification (Worker 1)` below.

---

## Review (Worker 3)

Not applicable for the same reason: there is no builder diff. Every check a review pass would own on the two Markdown files was performed independently in this section against source, not against the slices' prose.

---

## Final verification (Worker 1)

Read-only HEAD comparisons used `git show HEAD:<path>` into a scratch path **outside** the repository. No `git stash`, `checkout`, `restore`, or `worktree` at any point — three concurrent cycles (`spec-024`, `spec-026`, plus the maintainer) are live on this tree. `HEAD` is `ddf8bbafd928d634b6aeb546864e60bce8fec752`.

### 1. The gate, verbatim

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `================= 6179 passed, 40 skipped in 101.83s (0:01:41) =================`, exit **0**. No failures, no errors, no collection errors. No `--cov*` flag was used, here or anywhere in this pass. |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).` exit **0**. |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit **0**. |
| 4a | `uv run ruff format --check .` | **PASS** — `424 files already formatted`, exit **0**. One pre-existing configuration warning, not a failure: `warning: The following rule may cause conflicts when used with the formatter: COM812.` |
| 4b | `uv run ruff check .` | **PASS** — `All checks passed!` exit **0**. |
| 4c | `git diff --check` | **PASS** — no output, exit **0**. Whole tree, so it covers the concurrent cycles' tracked edits too. |

**No failure occurred, so the attribution machinery this gate carries was not needed.** Recorded because its absence is the finding: with zero `.py` files touched by either slice, a pytest / `manage.py` / ruff failure would by construction not have been this cycle's, and none appeared to have to prove that. `git diff --check` cannot see the untracked rationale file; the whitespace check for it was run directly (`0` lines matching `\t` or trailing space, file ends in exactly one newline) because `git diff --check --no-index /dev/null <file>` exits 1 on a non-empty diff regardless of whitespace and is the wrong instrument for an untracked file.

### 2. Floor verification

**`No floor-verification scope declared` in the substantive sense — the plan declares scope `none`, and no floor run was owed.** Recorded verbatim from `docs/builder/build-025-scalar_map_helper-0_0_7.md` preamble:

> Floor-verification scope: none. No slice touches a Django / Strawberry / channels integration seam; the cycle writes Markdown only.

Confirmed against the diff rather than accepted on the declaration: `git status --short` attributes exactly two paths to this cycle, both Markdown (`docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`, `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md`). No request/response handling, no view or ASGI plumbing, no body parsing, no session/auth surface, no queryset or expression compilation, no schema or type construction against Strawberry internals, no consumer or middleware wiring is in the diff, because no executable line is. **No floor venv was built**, and the shared `.venv` was not mutated, installed into, or downgraded.

The one version-dependent *claim* the spec makes — that Strawberry's `cls is None and name is not None` overload returns a `ScalarDefinition` without emitting `DeprecationWarning` — is a citation, re-verified by Worker 0 at the installed version and restated by Slice 2 against the **declared floor** (`strawberry-graphql>=0.316.0`) rather than a resolved version. That restatement is what makes it a claim a floor run would not change: the spec now names the constraint as the guarantee and names the venv reading as confirming the top of the range only. `pyproject.toml` declares `strawberry-graphql>=0.316.0`, `Django>=5.2.16`, `requires-python >=3.10,<4.0`, verified by reading the file this pass.

### 3. Gates on the two files this cycle wrote

| Gate | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` | `OK: 17 terms - all have glossary entries and at least one spec link.` exit **0** — the count the spec's own Definition-of-done item 9a pins, unchanged from pre-flight, and re-run **after** this pass's own edits. Re-derived independently: the terms CSV carries **17** data rows. |
| `uv run python scripts/check_trailing_commas.py --check` on the spec and the rationale | exit **0**, before and after this pass's edits |
| in-page anchors, spec | **81** total, **9** unresolved — all nine verified below |
| in-page anchors, rationale | **54** total, **0** unresolved |
| reference ids, both files | `used-not-defined: []`, `defined-not-used: []` |
| link-definition targets (file exists + `#fragment` resolves against the target's real computed slugs), both files | **0** failures |
| inline cross-file links (the convention forbids them), both files | **0** |
| `#"..."` substring citations, spec | **18** distinct, **18** resolve, **0** dead |
| `#"..."` substring citations, rationale | **6** distinct, **5** resolved, **1** dead — found by this pass and fixed (defect 3 below) |

Byte counts as this pass leaves them: spec **114,760** (135,777 at `HEAD`), rationale **92,034** (92,007 as Slice 2 left it; +27 from this pass's three edits).

### 4. The 9 remaining unresolved spec anchors — characterization verified, not accepted

The task was to verify the "all inside quoted `docs/GLOSSARY.md` entry bodies where they do resolve" claim for **all nine** rather than accept it. Done, per anchor, with the target-side resolution checked against `docs/GLOSSARY.md`'s own computed heading slugs:

| Spec line | Anchor | Resolves in `docs/GLOSSARY.md` | Site |
|---|---|---|---|
| 48 | `#strawberry_config` | yes | Slice 4 checklist bullet, inside the paragraph it pins verbatim for the `BigInt scalar` entry |
| 456 | `#bigint-scalar` | yes | blockquoted `## strawberry_config` entry body |
| 490 | `#bigint-scalar` | yes | that body's `**See also:**` row |
| 490 | `#upload-scalar` | yes | same row |
| 490 | `#specialized-scalar-conversions` | yes | same row |
| 493 | `#strawberry_config` | yes | blockquoted `BigInt scalar` entry append |
| 493 | `#djangooptimizerextension` | yes | same append |
| 493 | `#djangotype` | yes | same append |
| 493 | `#specialized-scalar-conversions` | yes | same append |

All nine resolve in `docs/GLOSSARY.md`, and all nine sit in text the spec pins verbatim for that file — eight inside blockquoted entry bodies, and the ninth (line 48) inside the Slice 4 bullet that quotes the same paragraph. **Recorded as deliberately not fixed**: rewriting them as reference links into the spec would make the pinned bodies differ character-for-character from the file they pin, which is the defect the pin exists to prevent. Independently confirmed that the pin is currently exact — the spec's blockquoted `## strawberry_config` body diffs **IDENTICAL** against the live `docs/GLOSSARY.md` entry, so the anchors are not the only thing riding on leaving them alone.

**One sub-population in Slice 2's artifact is wrong, and the total is right.** `docs/builder/bld-slice-2-025-spec_reconciliation.md` §3 enumerates them as `#bigint-scalar` x2, `#upload-scalar` x2, `#specialized-scalar-conversions` x2, `#strawberry_config` x2, `#djangotype` x1, `#djangooptimizerextension` x1 — which sums to **10** against a stated total of 9. The measured breakdown is `#upload-scalar` **x1**. The artifact closes with the cycle so nothing durable carries the error; the durable record (rationale §`## Verification performed by the spec reconciliation (Slice 2)`) lists the anchor names without counts and is correct as written.

### 5. Cross-slice coherence — the judgement holds for DRY, and did NOT hold for claim coherence

The plan's `## Checklist` note says: with one writing role and two Markdown slices there is no cross-slice DRY surface to scan, so no `bld-integration.md` is produced, and Slice 2's own pass covers rationale/spec coherence. **The DRY half of that judgement is correct and I confirm it**: there is no duplicated helper, no repeated literal, no shared constant, no module boundary, and no shadow overview to compare, because no `.py` file is in the diff. The `## Cross-slice integration pass` steps 3 and 4 (repeated string literals, import direction across shadow overviews) have no subject.

**The coherence half did not hold.** Three defects survived Slice 2's own pass, all in the rationale, all findable only by reading the two files against each other, and all fixed in this pass:

1. **Slice 2's blanket `python3.10` -> `python3.14` sweep hit a sentence *describing* the `python3.10` citations, producing a self-contradiction.** The provenance section's `**Re-relativization.**` bullet read: "The move left the moved text's `.venv/lib/python3.14/...` citations exactly as written even though they were already dead at `HEAD`; the reconciliation slice re-pointed them at `python3.14`". Left as `python3.14` and then re-pointed at `python3.14` cannot both be true. This is the class of defect a mechanical sweep creates and only a read can see: the sweep was right about every live citation and wrong about the one sentence that names the old spelling on purpose. Slice 2's own artifact anticipated the shape — it recorded "2 descriptive mentions remain" — and its instrument counted the two it knew about while this sentence had already been swept.
2. **A present-tense byte count of a file the next slice went on to grow.** The rationale's Slice 1 verification section read "This file is 76,619 bytes". It is 92,034. The section was retitled `## Verification performed by the rationale move (Slice 1)` by Slice 2 precisely so its statements read as historical, and every other statement in it does; this one is phrased as a present-tense fact and was false the moment Slice 2 appended to the file. Same trap as spec-017's mid-pass byte count, one step removed: not a count of a file the pass is still writing, but a count left in the present tense for a later pass to falsify.
3. **A dead `#"..."` substring citation into `KANBAN.md`, pre-existing at `HEAD` and moved verbatim into the rationale.** Decision 8's second justification bullet cited `` `KANBAN.md #"The last \`0.0.7\` card to ship owns the version bump"` ``. `grep -c 'owns the version bump' KANBAN.md` reports **0** — in the worktree and at `HEAD` (`git show HEAD:KANBAN.md` into a scratch path outside the repo, then grep). Slice 2 audited every `#"..."` anchor in the **spec** and found 3 dead across 8 uses; it did not run the same instrument on the **rationale**, which had inherited one by the move. **Pre-existence verified read-only**: the identical citation is at line 390 of `git show HEAD:docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`, so it is not introduced by this cycle — the cycle merely relocated it into a durable record and then swept only one of the two files it lives in.

So: no `bld-integration.md` was owed, and one would not have caught these either — its check list is DRY-shaped. What caught them is the instrument symmetry rule this gate applied: **run every sweep on both files, not on the file the slice was editing.** That is the durable lesson, and it is the one the missing-integration-pass question was really asking.

### 6. Every claim I assert was measured or read against source

No figure below was inherited from a slice artifact, the build plan, or my own memory file without re-derivation.

| Claim | Instrument | Result |
|---|---|---|
| full sweep outcome | `uv run pytest --no-cov`, summary line quoted verbatim | 6179 passed, 40 skipped, exit 0 |
| spec bytes at `HEAD` / now | `wc -c` on `git show HEAD:` copy and the worktree | **135,777** -> **114,760** |
| rationale bytes | `wc -c` | **92,007** as Slice 2 left it -> **92,034** after this pass |
| terms CSV data rows | `tail -n +2 \| grep -c .` | **17** — matches `check_spec_glossary`'s `17 terms` |
| `TODO-ALPHA-028-0.0.11` in the terms CSV | `grep -o \| wc -l` | **2** (the `DjangoFileType` and `DjangoImageType` rows) |
| `spec-013` / `spec-011` in the spec | `grep -o \| wc -l` each | **0** and **0** — the label rot is repaired, as the plan states |
| `python3.10` in the spec at `HEAD` | `grep -o \| wc -l` on the `git show HEAD:` copy | **19** across 16 lines |
| `python3.10` on lines Slice 1 moved | per-line match of each HEAD line's distinctive prefix against the rationale | **5** (HEAD L10 x1, L235 x2, L302 x2) |
| the spec-side `python3.10` population Slice 2 faced | 19 minus the 5 moved | **14** — Slice 2's figure is **confirmed** |
| `python3.10` now | `grep -o \| wc -l` | spec **0**; rationale **4**, all descriptive (D12's heading, D12's resolution paragraph, Slice 1's verification record, Slice 2's chronology-sweep line) |
| Slice 2's "2 descriptive mentions remain" | the four sites above | **4**. Two of the four are sentences Slice 2 wrote *after* it took the measurement, so the "2" was true when measured and false when the pass ended — not a defect in the durable record, whose own figure (14) is right |
| the rationale's moved-text `python3.10` count Slice 2 states as 6 | not worker-verifiable | The rationale is untracked at `HEAD`, so its intermediate state cannot be reconstructed read-only. From the derivable ends it is 4 or 5, not 6: 5 occurrences arrived with the move and Slice 1's own final-verification removed one by converting an inline `](.../python3.10/...config.py)` target to `][config]`. Recorded, not asserted, and **escalated** — only the maintainer can reconstruct an intermediate untracked state |
| the 9 `Rationale companion` pointer lines' stated bullet counts | per-block count in the rationale against each pointer's prose | **all 9 accurate**; alternatives per block `[2, 7, 3, 3, 3, 2, 3, 3, 2]` = **28**, matching the provenance table |
| justification bullets at `HEAD` | per-block count over `git show HEAD:` | `[3, 8, 3, 4, 4, 3, 5, 4, 4]` = **38**; the rationale carries **37**, one retained in the spec. Both the artifact and the rationale table now read 38 (37 moved, 1 retained) — the correction Slice 2 made to the durable record is **confirmed** |
| the spec's pinned `## strawberry_config` GLOSSARY body vs the live entry | strip `> ` prefixes, `difflib` against the live entry | **IDENTICAL**, character for character |
| the live `DONE-025-0.0.7` KANBAN card body | read `KANBAN.md` at the card | generated shape only — Priority / Status / Relative size / Labels / Spec / a 17-row glossary-terms table / 2 package files / Verified in upstream / a one-line `#### Note`. The long past-tense paragraph the spec pins in `## Doc updates` appears **nowhere** in `KANBAN.md` |
| the quoted `CHANGELOG.md` `### Added` body vs the landed bullet | read both | the landed bullet (line 174) carries a trailing `Tracked as [...][card-...] in [\`KANBAN.md\`][kanban].` clause the spec's quote omits — confirmed |
| `CHANGELOG.md` `## [0.0.7]` pre-renumber card labels | `grep -oE '\[[0-9]{3}-[a-z0-9_]+-0\.0\.7\]' \| sort \| uniq -c`, worktree **and** `git show HEAD:` copy | **the item is already discharged in the worktree.** At `HEAD`: 14 occurrences across 7 pre-renumber labels (`016`/`017`/`018` x5/`019`/`046` x2/`047` x3/`048`). In the worktree: **0** pre-renumber labels, all 7 now post-renumber (`020`/`021`/`022` x5/`023`/`024` x2/`025` x3/`026`) — a concurrent session repaired it (`CHANGELOG.md` is baseline-dirty, 20 insertions / 20 deletions). Slice 2 recorded it as open with the `047` label at 3 occurrences; that was true at `HEAD` and is **false now** |

**A catalog is a claim, and re-deriving it moved one item out of the catalog entirely.** The `CHANGELOG.md` label row above is the concrete cost of copying a figure forward: had this gate carried Slice 2's note as written, the artifact would have handed the maintainer a 14-occurrence sweep that no longer exists.

### 7. Spec status-line re-verification

`worker-1.md` `## Spec status-line re-verification` discharged by reading spec lines 1-6 against the build's state. All four factual claims hold after Slice 2: the `Target release:` line names the joint `0.0.7` cut and the `## [0.0.7] - 2026-05-27` heading (verified — that heading is `CHANGELOG.md` line 166); `Status:` says shipped and points at the rationale companion (verified, the file exists at the cited path and the `[spec-025-rationale]` definition resolves); `Predecessors:` cites `spec-017`, two GLOSSARY entries, the `[0.0.6]` `### Notes` line, and the card — the first three resolve, and the fourth is a *historical* reference to a line this card removed (`grep -c 'Migration to a' CHANGELOG.md` reports **0**), which is correct for a `Predecessors:` line naming what the card paid down. **No status-line edit is owed.**

### 8. Scope compliance

`git status --short` attributes exactly four paths to this cycle: `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` (M), `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md` (??), this artifact, and `docs/builder/worker-memory/worker-1-025.md`. No `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `CHANGELOG.md` / `docs/TREE.md` / `docs/README.md` / `GOAL.md` / `TODAY.md` / `README.md` edit, no `examples/fakeshop/db.sqlite3` write, no `-terms.csv` edit, no `docs/builder/DONE/` move, no spec relocation. Every baseline-dirty out-of-scope file the plan lists is still dirty and **none was reverted**. Both concurrent cycles' artifacts are untouched — `bld-slice-1a/1b/2/3-024`, `bld-integration-024`, `bld-final-024`, `build-024`, `bld-slice-1/2/3-026`, `build-026`, `bld-003-final`, `docs/builder/DONE/` — as are `docs/SPECS/spec-024-*`, `spec-026-*` and their rationale companions, which appeared on the tree after this plan's pre-flight. `docs/builder/build-025-scalar_map_helper-0_0_7.md` was read and not written; its final checkbox is Worker 0's. `docs/builder/bld-slice-1-025-*.md` and `bld-slice-2-025-*.md` were read and not written. No other worker's memory file was read or written. No `-024` memory file was opened. No commit, no branch.

### 9. Verdict

`final-accepted`. Every gate command passed. No slice owns a failing behavior, because nothing failed. Three coherence defects in this cycle's own Markdown were found and fixed in this pass rather than routed to a re-loop, for the reason recorded under `### Implementation discretion items`; one of the three was pre-existing at `HEAD` and verified so read-only.

## Reopening: Slice 3 and the fourteenth divergence

Added after this gate first returned `final-accepted`. Worker 0 re-derived the deferred-work catalog below, found a **fourteenth** post-ship divergence in the spec that Slices 1 and 2 and this gate all missed, and dispatched Slice 3 (`docs/builder/bld-slice-3-025-decision_9_census.md`, `Status: final-accepted`). Nothing in the original pass's gate results changed — no `.py` file was touched then or now — but the record it audited grew, so this section states what moved.

**Why this gate did not catch it.** The pass above ran every sweep on both files and derived its own instrument for anchors, references and substrings. None of those instruments can see a **true-when-written census sentence**: `the project's sole schema-construction site` resolves, cites nothing, matches no chronology token, and is grammatical. The only instrument that finds it is asking, of each present-tense claim about the tree, whether the tree still looks like that — which is what the D1-D13 derivation did and what this gate accepted as complete rather than re-running.

### The finding

`examples/fakeshop/strategy_schemas.py::build_strategy_schema` is a second **non-test** schema-construction site in fakeshop, added post-ship by `8fe01840` (2026-07-07). Re-derived here rather than transcribed:

| Claim | Command | Result |
|---|---|---|
| the file's adding commit | `git log --diff-filter=A -- examples/fakeshop/strategy_schemas.py` | one commit, `8fe01840`, 2026-07-07 |
| the ship commit precedes it | `git merge-base --is-ancestor b1a6d01f 8fe01840` | exit **0** — so the census was true when written |
| baseline schema sites | `git grep -nE '(strawberry\.Schema\|DjangoSchema)\(' b1a6d01f^ -- examples/fakeshop` | **two** code sites: `config/schema.py:26` and `test_query/test_multi_db.py:142` |
| non-test sites at `HEAD` | package-wide grep, `.venv` excluded, every hit opened | **two**: `config/schema.py` and `strategy_schemas.py`. All four `django_strawberry_framework/` hits are docstring examples; `config/schema.py`'s second hit is a comment |

**No code gap, and this is the load-bearing half.** Every fakeshop schema that resolves `BigInt` carries the registration; `strategy_schemas.py` passes `config=strawberry_config()` although no card asked it to, six weeks after the ship commit, which is evidence *for* Decision 9 rather than against it. The two fakeshop modules that build schemas with no registration at all — `test_query/test_products_visibility_api.py` (seven builds) and `test_query/test_transport_api.py` (one of two) — resolve no `BigIntegerField` / `PositiveBigIntegerField`: the first builds over `apps.products` types and `apps/products/models.py` contains no `Big`, the second over a pure-Strawberry query with no Django model. That is Decision 5's rule holding exactly as written.

### What Slice 3 changed

Four spec sentences, none by refreshing the count — a replacement census ("the two sites") would rot the same way "one" did:

- `### Decision 9` ¶1: "the project's **sole schema-construction site**" -> "**the schema the project serves at `/graphql/`**", plus one sentence saying the contract names that site rather than a count, and handing the general question to `### Decision 5`'s rule.
- `### Decision 9` ¶2 closing clause: "schema construction happens once, in `config/schema.py`" -> "an app `schema.py` contributes a `Query` root and leaves construction to whatever composes it."
- `## Risks` live-tier bullet: "**the one** fakeshop schema-construction call" -> "the construction call for the schema fakeshop serves at `/graphql/`". Its content survives whole.
- `## Current state`'s `config/schema.py` bullet: -> "the schema the project serves at `/graphql/` — its sole **non-test** schema-construction site". A fourth surface, initially fenced off by the dispatch as not-a-defect and unfenced when Slice 3's own counter-evidence (the baseline grep above) showed the claim false of the baseline surface too. The framing sentence scopes that section in **time**, and tier is the axis the claim was wrong on.

In the rationale: a `### D14` entry on the established shape, three `## Decision 9` subsection updates (`### Changes this Decision underwent`, `### Claims this Decision may no longer make`, and the `Contract that stays:` line, which did **not** survive verbatim), a `## Verification performed by the Decision 9 census repair (Slice 3)` section, and the `[spec-025-current-state]` / `[strategy-schemas]` definitions. The spec cites `strategy_schemas.py` nowhere: naming a second site in a contract document re-creates what D10 established the rule against.

### Which counts in the original pass above are now scoped, and which are wrong

Slice 3 adjudicated each site rather than bumping the token, and this artifact needs the same treatment. **Nothing in the original pass is falsified**, because every count in it is scoped to a pass that genuinely ended at thirteen:

- §3's `in-page anchors, spec` **81 / 9 unresolved** and `rationale` **54 / 0** are pre-Slice-3 measurements. Re-measured now: spec **82 / 9 unresolved** (the 9 unchanged — the same quoted-`docs/GLOSSARY.md` set, none introduced or moved), rationale **65 / 0**.
- §3's byte counts (spec 114,760; rationale 92,034) were true when written. Now: spec **115,181**, rationale **102,132**.
- §4's per-anchor table of the 9 unresolved spec anchors still holds; Slice 3 added no in-page anchor to any quoted GLOSSARY body.
- §5's "three defects survived Slice 2" is a count of *coherence defects this gate found*, not of divergences, and is untouched.
- The rationale's own `## Post-ship divergence record` heading moved from `(D1-D13)` to `(D1-D14)` and its opener from "Thirteen places" to "Fourteen places", with the slug moved at both use sites. Its `## Provenance of this record` and `## Verification performed by the spec reconciliation (Slice 2)` **keep thirteen**, each gaining one scoping clause: both are statements about what Slice 2 acted on, and Slice 2 did not act on D14. The spec's own five occurrences of "thirteen" were left alone — they count the thirteen factory tests, a different population.

### Gates, re-run after Slice 3's edits

| Gate | Command | Result |
|---|---|---|
| glossary | `python3 scripts/check_spec_glossary.py --spec docs/SPECS/spec-025-scalar_map_helper-0_0_7.md --terms docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv` | `OK: 17 terms - all have glossary entries and at least one spec link.` exit **0** — the count Definition-of-done item 9a pins, unchanged |
| source layout | `python3 scripts/check_trailing_commas.py --check` on the spec and the rationale | exit **0**, no output |
| whitespace | `git diff --check` on the spec | exit **0**, no output. Trailing-whitespace / tab scan: **0** lines in either file |
| anchors / refs, both files | own sweep, code spans and fenced blocks stripped | spec 82 anchors / 9 unresolved (all pre-existing); rationale 65 / **0**. `used-not-defined: []` and `defined-not-used: []` both files; **0** bad definition targets; **0** inline cross-file links; 1 delimiter and 10 canonical headers each |
| substring citations | `grep -F` in the **cited** file | Slice 3 added one, `examples/fakeshop/config/schema.py #"schema = DjangoSchema("`, which resolves. It replaced a `line 77` reference that would have violated `AGENTS.md` rule 27 in a tracked standing doc |
| `pytest` | not run | Slice 3 changes **no executable line**. Stated rather than skipped silently. No `--cov*` flag in any pass |
| `ruff` | not run | no `.py` file touched |

The original pass's five gate items were **not** re-run, and are not owed: they gate executable behaviour, and the reopening added no executable line. `git status --short` still attributes no `.py` file to this cycle.

### Deferred work catalog

The next spec author's reading list. **Revised at the reopening**: every homing target below was verified against `KANBAN.md` before being written, and two of Worker 0's proposed attributions were wrong and are corrected in place. Every population was re-derived; where a figure differs from the artifact or message that supplied it, the difference is stated. **Everything here is outside this cycle's scope fence** (spec files and `.py` source only) except where noted.

**Card ids verified on the board before use** — `grep -nE '^#+ .*(ALPHA-05[012])' KANBAN.md`: `TODO-ALPHA-050-0.0.15 - Extract DjangoDebugExtension into the standalone django-strawberry-debug package` (L157), `TODO-ALPHA-051-0.0.15 - Boundary hardening and system-wide DRY squeeze` (L211), `TODO-ALPHA-052-0.1.0 - Beta release (cleanup, verification, alpha -> beta)` (L315). All three exist with those titles.

**Two corrections to the homing proposal, both about card ownership.** `KANBAN.md` lines 353 and 364 were proposed as `TODO-ALPHA-051-0.0.15`'s in the original catalog and are **card 052's**: the heading at L315 is `TODO-ALPHA-052-0.1.0` and `awk`-scanning L315-L400 for `^#+ \[` returns no further heading, so both lines sit inside card 052's section. The original catalog's "board-side residue for whoever owns `TODO-ALPHA-051-0.0.15`" on the CHANGELOG item is therefore wrong; it is 052's own bullet, which makes both items self-corrections on that card rather than cross-card hand-offs.

**Maintainer decisions — both home on `TODO-ALPHA-052-0.1.0`, flagged as contract calls**

Homing verified: card 052's board-DB spec-path-rot bullet (`KANBAN.md` L359) already carries the twin question in its own words — "Whether a Done card's DoD should stay a historical record or become navigable is a maintainer contract call" — so both items below land beside an open question of the same kind rather than opening a new one.

- **Should a spec pin a verbatim body for a DB-generated file at all?** (`bld-slice-2-025-spec_reconciliation.md` `### Notes for Worker 1`.) The spec's `## Doc updates` pins a long past-tense Done body for `KANBAN.md`, and Definition-of-done item 15 requires `KANBAN.md` to carry it. `KANBAN.md` is rendered from the fakeshop kanban DB, and the live `DONE-025-0.0.7` card carries a generated body instead — verified this pass by reading the card: Priority / Status / Relative size / Labels / Spec, a 17-row glossary-terms table, two package files, a `#### Verified in upstream` line, and a one-line `#### Note`. Not fixable from the spec side: the fix is either a DB edit plus a regenerate (`KANBAN.md` is fenced, and DB-backed per `AGENTS.md`) or the general decision that a spec should not pin a verbatim body for a generated file, which applies corpus-wide rather than to `025`. Rejected alternatives the slices recorded: Slice 2 narrowed DoD 15 to pin the **body** rather than the card **number** (as far as the spec side can go) and explicitly declined to delete the pinned body, since deleting it would drop the only record of what the card claimed to have written. No slice recorded an alternative of hand-editing `KANBAN.md`, which the scope fence and `AGENTS.md` both forbid.
- **`KANBAN.md`'s live version-bump policy contradicts the one this spec's Decision 8 rests on.** New this pass. Decision 8's moved justification cited `KANBAN.md #"The last \`0.0.7\` card to ship owns the version bump"`; that substring exists nowhere in `KANBAN.md`, at `HEAD` or now. The nearest live statement is `KANBAN.md` line 64 — "The version bump from `0.0.8` is owned by the joint `0.0.9` cut, **not any single card**, per Decision 11 of `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`" — which is the opposite ownership rule. This pass dropped the dead substring anchor and kept the citation (defect 3, §5); reconciling *which* policy is current is a maintainer contract call spanning `spec-025`, `spec-029` and the board, not a link repair a rationale companion may make.

**Fenced-file doc residue (this cycle's scope fence closed these; the catalog is their only route to the maintainer)**

The five terms-CSV rows in the next two entries are **one edit** and home together on `TODO-ALPHA-052-0.1.0`. Reason to record: the fix is a CSV edit plus an `import_spec_terms` re-run, the same ORM-edit-plus-regenerate instrument as that card's board-DB spec-path-rot bullet (`KANBAN.md` L359) and its `CardItem` 723 bullet (L363), which names that instrument explicitly — "DB-backed, so the fix is an ORM edit plus regenerate - the same instrument as this card's board-DB spec-path-rot bullet".

**Checker gap worth adding to the same card, all three legs verified rather than asserted.** The CSV's `notes` column is a value no gate compares and nothing renders:

- **Written** by `import_spec_terms` into `GlossarySpecMention.notes` — `examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py` reads `row.get("notes")` and passes it in the `update_or_create` defaults of `_sync_spec_mentions`; `GlossarySpecMention.notes` is a `TextField(blank=True, default="")` in `examples/fakeshop/apps/glossary/models.py`.
- **Not read** by `check_spec_glossary` — `grep -n 'notes' scripts/check_spec_glossary.py` returns exactly **two** hits, a docstring line and an `--help` string. `load_terms` is typed `-> list[tuple[str, str]]` and appends `(term, anchor)` only.
- **Fetched but never rendered** by `scripts/build_glossary_md.py` — its GraphQL query selects `notes` inside `allGlossarySpecMentions`, but the only reads out of that payload are `specPath` (a set comprehension) and `len()` for a progress line. `grep -n '"notes"' scripts/build_glossary_md.py` returns nothing.

So a stale `notes` row cannot fail a gate and cannot appear in a rendered doc, which is why all five rows below rotted silently. That is the durable half of this item; the five row fixes are the cheap half.

- **`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv`: the `DjangoFileType` and `DjangoImageType` rows cite `TODO-ALPHA-028-0.0.11`, which shipped as `DONE-037-0.0.11`.** (`bld-slice-1-025-rationale_authoring.md` and `bld-slice-2-025-spec_reconciliation.md` `### Notes for Worker 1`; the build plan's `### Verified NOT defects`.) Re-derived: **2** occurrences, one per row. The live `DONE-025-0.0.7` KANBAN card's own glossary table already records both terms as `shipped (0.0.11)`, so the CSV is the last surface carrying the TODO id. The CSV is not a spec file, and Slice 2's reason for not touching it stands: editing one surface of a multi-surface cluster leaves it divergently rather than uniformly wrong.
- **Three further stale rows in the same CSV, not recorded by either slice.** New this pass, and they belong with the item above because they land in the same file and the same edit. (a) The `Upload scalar` row reads "Next package-defined scalar (planned for `0.0.11`); reuses this card's helper unchanged" — `Upload` shipped, and D3 established that it is *not* package-defined and needs no `_PACKAGE_SCALAR_MAP` entry, so the row states the mechanism D3 retired. (b) The `DjangoOptimizerExtension` row cites the consumer pattern as `extensions=[DjangoOptimizerExtension()]`, the instance shape D9 replaced with `extensions=[lambda: _optimizer]` throughout the spec. (c) The `Strictness mode` row reads "the new GLOSSARY entry `strawberry_config` **ought to be ordered** between ..." — future tense for something Slice 4 did in `0.0.7`.
- **A KANBAN bullet still describes six `[spec-013]` occurrences in this spec -> `TODO-ALPHA-052-0.1.0`, as a self-correction.** (Both slices' `### Notes for Worker 1`; the build plan's `### Verified NOT defects`.) **Card attribution corrected at the reopening:** the original catalog and both slice artifacts named `TODO-ALPHA-051-0.0.15`; the bullet is at `KANBAN.md` **line 353, inside card 052's section** (heading at L315, no further `^#+ \[` heading through L400), so it is that card's own bullet and the fix is a self-correction, not a hand-off. Re-derived: `grep -o 'spec-013' | wc -l` and `grep -o 'spec-011' | wc -l` both report **0** in `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`. The label rot is repaired here; the L353 description of it is what is stale. Two clauses of that bullet decay with it: its claim that this spec "carries **six occurrences - five uses plus the definition line all five depend on**", and its instruction that the `[spec-013]` half "lands whole on this sweep, with no half for `TODO-ALPHA-051-0.0.15`" — which no longer has an `025` component to land. Note the bullet's own warning against carrying the smaller figure (five) forward: neither figure has a referent now.
- **The spec's quoted `CHANGELOG.md` `### Added` body omits a trailing clause the landed bullet carries.** (`bld-slice-2-025-spec_reconciliation.md` `### Notes for Worker 1`.) Verified: `CHANGELOG.md` line 174 ends `... See [\`strawberry_config\`][glossary-strawberry-config]. Tracked as [025-warning_free_scalar_registration_via_strawberryconfigscalar_map-0.0.7][card-...] in [\`KANBAN.md\`][kanban].`; the spec's quote stops at the `See ...` sentence. The clause is appended by the kanban tooling rather than authored, so quoting the authored text is defensible — recorded so the next reader does not rediscover it as a defect. `CHANGELOG.md` is fenced.
- **`docs/README.md`'s `DjangoSchema(...)` error-policy snippets omit `config=`.** (Build plan `### Verified NOT defects`.) Confirmed as **not** a `spec-025` migration gap: they are spec-048 illustrations scoped to `error_policy=`. `docs/README.md` carries `strawberry_config` in 9 places. Left as a recorded non-defect so a future sweep does not re-raise it; docs are fenced regardless.

**Already discharged — do NOT carry forward**

- **`CHANGELOG.md`'s `## [0.0.7]` pre-renumber card labels.** (`bld-slice-2-025-spec_reconciliation.md` `### Notes for Worker 1`, which recorded the `047-...` label at 3 occurrences as open; and `KANBAN.md` line 364, which measures the whole population at 14 across 7 labels.) **Fixed in the working tree by a concurrent session.** At `HEAD` the section carries 14 pre-renumber labels; in the worktree it carries **0** — re-confirmed at the reopening, `grep -oE '\[0(1[6-9]\|4[6-8])-[a-z0-9_]+-0\.0\.7\]' CHANGELOG.md` returns nothing — all seven now post-renumber. **The residual is the board's own measurement, and its card attribution is corrected at the reopening:** `KANBAN.md` line 364 is inside card **052**'s section, not card 051's as this catalog first said, so its now-stale figure of 14 is a self-correction for `TODO-ALPHA-052-0.1.0` and should ride the same edit as the L353 `[spec-013]` bullet above — same card, same file, same class of stale measurement. Not open work for a spec author either way.

**Package docstring schema examples split on `config=strawberry_config()` -> `TODO-ALPHA-051-0.0.15`, as a maintainer doc-style call**

New at the reopening, Worker 0's finding, and the only catalog item touching `.py` files. Re-derived rather than accepted — "4 examples, 1 compliant" is a claim, and it reproduces. The package's multi-line `strawberry.Schema(...)` **construction examples** in docstrings number exactly four, and one carries the registration:

| Site | `config=strawberry_config()` |
|---|---|
| `django_strawberry_framework/extensions/debug.py` (module docstring) | **yes** |
| `django_strawberry_framework/extensions/resource_policy.py::DjangoResourcePolicyExtension` (class docstring) | no |
| `django_strawberry_framework/optimizer/extension.py` (module docstring) | no |
| `django_strawberry_framework/optimizer/extension.py` (method docstring, the singleton-in-a-factory example) | no |

Population boundary, since the greppable token over-collects: a package-wide grep for `(strawberry\.Schema|DjangoSchema)\(` returns 25 hits, of which 21 are inline prose mentions in the `` ``strawberry.Schema(...)`` `` form, a `class DjangoSchema(strawberry.Schema):` definition, or an error-message string. Only the four above open a multi-line constructor block. Adjacent but not in the population: `django_strawberry_framework/scalars.py`'s `strawberry_config` docstring, which names the pattern inline (`pass it as ``strawberry.Schema(query=..., config=...``) without building an example.

**The precedent-setting file is the one that goes away.** `TODO-ALPHA-050-0.0.15` Slice 2 (`KANBAN.md` L172) opens "delete `extensions/debug.py` + `tests/extensions/test_debug.py`" — verified — so the only compliant example will not exist after that card ships, leaving the population at **three** non-compliant sites and no in-package precedent.

**Homed, not fixed, and deliberately so:** whether a topic-scoped illustration (an optimizer example, a resource-policy example) should carry an unrelated `config=` line is a doc-style decision for the maintainer, not a defect a spec cycle may settle. It is also outside this cycle's fence, which owes no `.py` edit.

**One correction to the homing rationale.** Card 051's convention is verified verbatim and repeatedly — "Fold into whichever WP batch legitimately opens `<file>`" appears at `KANBAN.md` L248, L250, L252, L255, L258 and L260 — but its batches do **not** currently name two of the three target files: card 051's section mentions `extensions/resource_policy.py` **once** and `optimizer/extension.py` **zero** times. So the "batches already open the file" half of the rationale is not established by the board text for the optimizer sites; 051 remains the right home on its convention and its boundary-hardening scope, and the batch coverage is something that card's own planning must establish. Worker 0's "already carries three same-class docstring-precision items" also does not reproduce: by the narrow reading — a docstring whose prose misdescribes the code it documents — card 051 carries at least **five** (L233 `_package_view_instance`, L235 `send_revalidated_operation_frame`, L237 `MAX_REQUEST_BODY_BYTES`, L246 `ConfigurationError`, L247 `_format_unknown_fields_error`), plus a sixth docstring surface at L253 that is stale spec *paths* rather than imprecision. The class is real and well-populated; the count of three is not.

**Two corrections to the homing message's own populations, recorded because a wrong population is what gets inherited**

- **The fakeshop schema-building module count is nine, not six.** Seven `test_query/` modules (`test_debug_extension_api`, `test_error_policy_api`, `test_multi_db`, `test_optimizer_auto_api`, `test_products_visibility_api`, `test_resource_policy_api`, `test_transport_api`) plus two under `apps/library/tests/` (`test_generic_connection`, `test_generic_connection_sharded`), plus `strategy_schemas.py`.
- **Two of them build schemas with no `config=strawberry_config` at all, and that is not a gap.** `test_query/test_products_visibility_api.py` (seven builds, zero) and `test_query/test_transport_api.py` (two builds, one). Neither resolves `BigInt` — the first over `apps.products` types with no `Big` anywhere in `apps/products/models.py`, the second over a pure-Strawberry query with no Django model — so Decision 5's rule does not reach them: the registration is owed by a `BigInt`-resolving schema, not by every schema. A future sweep for "sites missing the registration" must not re-raise these two.
- **Instrument trap behind both figures.** `config=strawberry_config()` **with the empty parens** under-reports: it misses `test_query/test_optimizer_auto_api.py`'s `config=strawberry_config(extra_scalar_map={BombValue: bomb_scalar})`. Count on `config=strawberry_config`. The mirror trap produced the six-module figure — `grep -c strawberry_config` counts the import line as a build. Two instruments, two wrong populations, same root: the token is not the population.

**Not worker-verifiable — escalated to the maintainer**

- **The rationale's moved-text `python3.10` population, stated as 6 by Slice 2.** The rationale is untracked at `HEAD`, so no read-only reference exists for its intermediate state and the figure can be neither confirmed nor refuted without the tree at an intermediate point. Derivable bounds put it at 4 or 5. The claim is recorded with its evidence (§6) and escalated; nothing depends on it — the spec-side figure of 14 is confirmed, and both files now report `python3.10` at 0 live occurrences.

**Artifact-local, closes with the cycle (recorded, no action)**

- `bld-slice-2-025-spec_reconciliation.md` §3's per-anchor breakdown of the 9 unresolved anchors sums to 10 (`#upload-scalar` is x1, not x2); its total of 9 is right, and the durable record carries no counts. Same artifact's "2 descriptive `python3.10` mentions remain" is 4, both extras being sentences the pass wrote after measuring.

### Summary

The gate passes on all five items: the full sweep is `6179 passed, 40 skipped` at exit 0, Django's `check` and `makemigrations --check --dry-run` are clean, `ruff format --check` / `ruff check` / `git diff --check` are clean, and the plan's floor-verification scope of `none` is confirmed against a diff that contains no executable line, so no floor run was owed and no floor venv was built. Nothing failed, so nothing needed attribution.

The cycle's substantive residue is not in the code and not in the gate: it is that **the absent integration pass was correctly absent for DRY and insufficient for claim coherence.** Three defects survived Slice 2 into the durable rationale — a mechanical `python3.10` -> `python3.14` sweep that swept the one sentence naming the old spelling on purpose and left it self-contradictory; a present-tense byte count that a later slice falsified by appending to the same file; and a dead `KANBAN.md` substring citation, pre-existing at `HEAD`, that survived because the substring audit ran on the spec and not on the file the spec's own text had been moved into. All three are fixed here. The pattern behind all three is one rule: **run every sweep on both files, not on the file the slice happens to be editing.**

Re-deriving the deferred-work catalog rather than transcribing it changed it: one item (the `CHANGELOG.md` pre-renumber labels, 14 occurrences at `HEAD`) is already discharged in the working tree by a concurrent session and is recorded as closed rather than handed on, and three further stale rows in the terms CSV were found that neither slice recorded. One count in each slice artifact was wrong and neither is load-bearing; one Slice 2 figure is not worker-verifiable at all and is escalated rather than asserted.

### Spec changes made (Worker 1 only)

All three edits are to `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md`. None changes a contract, so no `revision-needed` is triggered and no builder re-pass is owed. `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` was **not** edited by this pass.

| Site | Change | Reason | Triggered by |
|---|---|---|---|
| `## Provenance of this record`, the `**Re-relativization.**` bullet | `` `.venv/lib/python3.14/...` citations exactly as written `` -> `` `.venv/lib/python3.10/...` `` | Slice 2's blanket `python3.10` -> `python3.14` sweep hit a sentence *describing* the old spelling, leaving the bullet saying the move left them as `python3.14` and the reconciliation then re-pointed them at `python3.14`. The sentence's whole job is to name what the move did not change | this gate's cross-slice coherence read (§5 defect 1) |
| `## Verification performed by the rationale move (Slice 1)`, the byte-count bullet | "This file is 76,619 bytes" -> "This file was 76,619 bytes as the move left it" | present tense for a measurement Slice 2 falsified by appending to the same file; the file is 92,034 bytes. Every other statement in that section already reads as historical | this gate's read (§5 defect 2) |
| `## Decision 8`, second justification bullet | the citation `` [`KANBAN.md #"The last \`0.0.7\` card to ship owns the version bump"`][kanban] `` -> `` the last-card-owns-the-bump policy [`KANBAN.md`][kanban] carried for the `0.0.7` cut `` | the substring exists nowhere in `KANBAN.md`, verified in the worktree **and** at `HEAD` read-only. Same repair Slice 2 applied to the spec's three dead substring anchors — drop the substring, keep the file citation — applied to the file Slice 2's audit did not sweep. The claim itself stands on the sentence; which bump policy is current is escalated as a maintainer decision above | this gate's substring audit (§5 defect 3) |

All gates were re-run after these edits: `check_spec_glossary` `OK: 17 terms` exit 0; `check_trailing_commas --check` exit 0 on both files; the rationale's anchors 54/0 unresolved, `used-not-defined: []`, `defined-not-used: []`, 0 bad definition targets, 0 inline cross-file links, and **6 -> 5 distinct `#"..."` citations with 5 of 5 resolving**.

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
