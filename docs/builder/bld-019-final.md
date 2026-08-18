# Build: Final test-run gate — spec-019 (consumer override semantics, scalar fields)

Spec reference: [`docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md`][spec-019]
Rationale companion: [`docs/SPECS/appx/spec-019-consumer_overrides_scalar-0_0_6-rationale.md`][spec-019-rationale]
Build plan: [`docs/builder/build-019-consumer_overrides_scalar-0_0_6.md`][build-019]
Prior artifacts, both read in full as required context: [`docs/builder/bld-review-1-spec019_rationale.md`][bld-r1] (R1) and [`docs/builder/bld-019-integration.md`][bld-integration] (integration pass).
Status: final-accepted

**Cycle shape.** A residual closeout cycle: one documentation round, zero source changes. `HEAD` at this gate is `1b286483` — the same commit the integration pass recorded, so `HEAD` did not move again between the integration pass and this gate (it had moved once mid-cycle, `09003dc2` -> `1b286483`, when the concurrent spec-018 closeout landed).

**Supersession applied throughout this artifact.** Where R1's `### Notes for Worker 1` and the integration pass disagree, the integration pass governs: it re-derived R1's notes 3 and 4 and found note 4's claim **false** and note 3's population **understated**. The `### Deferred work catalog` below carries the integration pass's numbers and carries no dead item.

---

## Final verification (Worker 1)

### Spec status-line re-verification

Performed at the start of this spawn, per [`docs/builder/worker-1.md`][worker-1] `## Spec status-line re-verification (every Worker 1 spawn)`. The spec's header lines (title, target release, `Status:`, owner, predecessors, `Card line:`, `Deliberation:`, and the `015 -> 019` renumber note) were read against the state of the build at this gate:

- `Target release: 0.0.6.` — correct; the package is at `0.0.14` and this card shipped at `0.0.6`.
- `Status: shipped (0.0.6, 2026-05-19); archived. Card DONE-019-0.0.6.` — correct. Nothing in this cycle falsified it, and the file is where the line says it is (`docs/SPECS/`, not `docs/`).
- `Deliberation:` pointer at the rationale companion — the target exists on disk at the named path and its reference-style definition resolves.
- No predecessor doc named in the header was deleted by this build.

**No spec status-line edit was needed at this spawn.** The rationale companion's header was read on the same pass and is likewise accurate.

### Declarations carried from the plan

All three are deliberate decisions recorded in the plan's preamble, not silence:

- **Ownership partition: `none; single sequential round`.** R1 owned the spec, the rationale companion, and the one authorized `CHANGELOG.md` correction. No code round was ever opened, because R1's independent per-name walk and the integration pass's re-derivation both found no code gap. With one cohort there are no shared shapes to assign.
- **Hot-path declaration: `none`.** The cycle writes no package source file, so there is no operation to measure. No hot-path number is owed by any pass, this gate included.
- **Floor-verification scope: `none`.** No Django / Strawberry / channels integration seam is touched — the cycle's whole diff is three `.md`-and-`CHANGELOG` files. Per [`docs/builder/BUILD.md`][build] `### When it is required`, a cycle touching none of those seams declares `none` and skips it. **No floor venv was built by any pass, and none is owed by this gate**, which is the backstop for a declared scope rather than a second owner. Recorded here explicitly rather than left blank.

### Gate commands

Each run from the repository root at `HEAD` `1b286483`, in the order [`docs/builder/BUILD.md`][build] `## Final test-run gate` gives them. No `--cov*` flag was used anywhere in this pass; no `-x` / `--maxfail` was used, so no row is hidden. Every lint command was run read-only — never `--fix`.

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **pass** (exit 0) — `6161 passed, 40 skipped in 150.71s`. Full sweep across all three test trees (`tests/`, `examples/fakeshop/tests/`, `examples/fakeshop/test_query/`), 5 xdist workers. 0 failed, 0 errored, 0 collection errors. The 40 skips were enumerated with `-rs` rather than assumed, and are entirely the two standing environment-gated tiers: **37** `requires the Postgres tier (FAKESHOP_PG_DSN)` in `tests/test_lateral_pg_parity.py` and `tests/test_predicate_pg_explain.py`, and **3** `requires FAKESHOP_SHARDED=1` in `tests/test_permissions.py`, `examples/fakeshop/test_query/test_multi_db.py`, and `examples/fakeshop/apps/library/tests/test_generic_connection_sharded.py`. Both tiers skip under the default invocation by design ([`AGENTS.md`][agents]). The `-rs` run is a second full sweep and reported the same `6161 passed, 40 skipped`. |
| 2 | `uv run python examples/fakeshop/manage.py check` | **pass** (exit 0) — `System check identified no issues (0 silenced).` |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **pass** (exit 0) — `No changes detected`. |
| 4 | `uv run ruff format --check .` | **pass** (exit 0) — `424 files already formatted`. (The `COM812` formatter-conflict warning is a standing configuration notice, not a failure; `AGENTS.md` records that `COM812` is deliberately enabled.) |
| 5 | `uv run ruff check .` | **pass** (exit 0) — `All checks passed!` |
| 6 | `git diff --check` | **pass** (exit 0) — no output; no whitespace error and no conflict marker anywhere in the tree. |

**Note on 4 and 5.** Both ran across the whole tree, so they cover the concurrent sessions' ~100 dirty paths as well as this cycle's four. Both are clean, so no lint or format drift exists to attribute to anyone, and no pre-flight baseline exception is needed.

### Floor verification confirmation

`No floor-verification scope declared.` The plan declares `none` and gives the reason (no Django / Strawberry / channels seam is touched). No pass owed a floor run, none ran one, and this gate owes none. Nothing here is an unrun floor claim.

### Paths this cycle changed

The complete list, for the maintainer's commit. Confirmed against `git status --short` at this gate:

| Path | State | What it is |
|---|---|---|
| `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md` | ` M` | R1's rationale move and 25-entry reconciliation. 104,017 bytes, matching both prior artifacts' recorded figure. Untouched by the integration pass and by this gate. |
| `docs/SPECS/appx/spec-019-consumer_overrides_scalar-0_0_6-rationale.md` | `??` | The new rationale companion R1 created (47,488 bytes) plus the integration pass's three custodial corrections. 48,834 bytes at this gate. Tracked-and-committed by contract ([`docs/builder/worker-1.md`][worker-1] `### Performing the rationale move`, rule 5), not scratch. |
| `CHANGELOG.md` | ` M` | R1's one authorized correction. `git diff HEAD --stat` reports `1 insertion(+), 1 deletion(-)` — exactly the one sentence retiring the `typing.get_type_hints` fail-soft description in the `## [0.0.6]` `Added` Relay-guard entry. |
| `docs/builder/build-019-consumer_overrides_scalar-0_0_6.md` | `??` | Worker 0's build plan for this cycle. |
| `docs/builder/bld-review-1-spec019_rationale.md` | `??` | R1's round artifact. |
| `docs/builder/bld-019-integration.md` | `??` | The integration pass artifact. |
| `docs/builder/bld-019-final.md` | `??` | This artifact. |

**Not this cycle's output.** `git status --short` reports **108 paths** when the gate commands ran and **109** once this artifact was written. Everything above accounts for seven of them; the remaining ~102 belong to the maintainer's concurrent sessions and are reported, never edited and never reverted ([`AGENTS.md`][agents] rule 34). Two classes deserve naming so a commit does not sweep them in:

- **`docs/builder/DONE/` and the artifact churn around it.** A concurrent session created `docs/builder/DONE/` and is moving closed build plans into it (` D` on `docs/builder/build-017-deferred_scalars-0_0_6.md` with an untracked counterpart under `DONE/`; `docs/builder/bld-017-final.md` deleted outright with no counterpart; `docs/builder/bld-018-final.md` staged for deletion in the index). **None of this is spec-019's output** and none of it is this cycle's to complete, undo, or imitate.
- **The dirty package-source and test files**, `tests/types/test_definition_order.py` among them. This cycle reads that file and writes no code at all.

Stage this cycle's seven paths explicitly (`git add <path>`), never `git add -A` ([`START.md`][start] "Concurrent sessions").

### Failure attribution

**No gate command failed, so no attribution was owed.** Recorded because the judgement was prepared rather than skipped: this cycle's diff is four content files, none of them `.py`, no model, no migration, and no schema module, so a `pytest` / `manage.py check` / `makemigrations` failure could not have been caused by it. Had one appeared, the discharge would have been to record the failing node ids and the evidence that the failing test and the code under it are absent from this cycle's diff, then escalate to the maintainer — never to edit a test, edit source, revert, `git stash`, `git checkout`, `git restore`, or open a `git worktree`, all of which race or destroy the concurrent sessions' uncommitted work. A pre-existing-at-`HEAD` failure claim is not worker-verifiable on a legitimately dirty tree ([`docs/builder/BUILD.md`][build] `## Claims are proven mechanically, never accepted on prose`), so this gate would have said what it measured and what it could not.

### Dispatched-findings audit

R1's `### Dispatched findings checklist` carries twelve boxes: eleven `- [x]` and one `- [ ]`.

- The eleven ticked boxes were audited against the cycle's diff by the integration pass, which re-derived R1's carry-forward notes and confirmed finding 9's population effect, the guard control-flow fix, the `docs/GLOSSARY.md` confirmation, and the landed `CHANGELOG.md` correction. This gate independently re-confirmed the `CHANGELOG.md` diff is exactly one bullet and the two spec/rationale byte counts are unchanged from the recorded figures. No box needs un-ticking, and no landed contract was left un-ticked.
- The one `- [ ]` box, **finding 10** (the `spec015_*` identifiers), carries its one-line deferral reason under R1's `### Spec changes made (Worker 1 only)` and is homed in the `### Deferred work catalog` below. It is a recorded deferral, not a silent gap.

Re-derived at this gate, so the catalog's population is measured rather than copied: `grep -rn 'spec015' tests/ examples/ django_strawberry_framework/` returns **four** occurrences, all in `tests/types/test_definition_order.py` — three `app_label`s and one stub-module prefix — and none anywhere else in the tree.

### Deferred work catalog

Every item either prior artifact explicitly deferred to a future slice, future spec, or maintainer follow-up. The integration pass's numbers are used throughout; R1's superseded notes 3 and 4 are handled as the supersession requires — note 3's population corrected here, note 4 **absent, because the item does not exist**.

1. **The `spec015_*` synthetic identifiers baked into landed test code.** Source: R1's `### Dispatched findings checklist` (finding 10, the one `- [ ]` box) and `### Notes for Worker 1` item 2; carried forward by the integration pass's `### Notes for Worker 1` item 1. Licensed by the plan's finding 10 ("do not rename") and by the spec's `## Test strategy` and Slice 1 unresolved-string-test entries, which record the spelling as the landed one rather than as a recipe to re-make. Four occurrences, all in `tests/types/test_definition_order.py` and all test-local synthetic strings with no cross-file consumer: `app_label = "test_spec015_unsupported"`, `app_label = "test_spec015_grouped_choices"`, `app_label = "test_spec015_co_resident"`, and `stub_name = f"spec015_unresolved_relay_stub_{uuid.uuid4().hex}"`. Target: maintainer follow-up, or any future card that opens that file for another reason — renaming has no correctness payoff and a real collision risk against the concurrent session's dirty copy.

2. **The retired fail-soft vocabulary in `tests/types/test_definition_order.py` — four occurrences across three tests.** Source: the integration pass's `### Notes for Worker 1` item 2 and its finding 2, **superseding R1's `### Notes for Worker 1` item 3**, which counted three occurrences across two tests. No spec clause licenses this one; it is a vocabulary residue of commit `2bcd7f96`, which retired the `typing.get_type_hints` fail-soft mechanism two days after the `0.0.6` release. The four are: two test **names** derived from the retired "fail-soft sub-case 1 / 2" vocabulary (`::test_consumer_id_unresolved_nodeid_shaped_string_on_relay_node_type_passes_guard_only` and `::test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted`); one inline **comment** in the second of those, #`"the fail-soft annotation walk accepts the"`; and one **docstring** on a third test R1 did not enumerate, `::test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises` #`"raises via the fail-soft regex reject"`. All three tests pin current, correct contracts — only the vocabulary is retired. Target: the same future card that opens the file. **A rename pass carrying R1's old count of three will stop one occurrence short**, which is exactly why the corrected count is stated here.

3. **`KANBAN.md`'s `[spec-011]` renumber-sweep bullet needs its population re-derived; spec-019 has left it.** Source: R1's `### Notes for Worker 1` item 1 (the plan's finding 9's reportable sweep-population effect), re-derived and carried by the integration pass's `### Notes for Worker 1` item 4. The bullet, under `TODO-ALPHA-052-0.1.0`, names this spec as still carrying the pre-renumber filenames `spec-013-deferred_scalars` and `spec-014-meta_primary`; R1 retired both on the spec-018 precedent, and `grep -c 'spec-013'` on the spec now returns **0**. DB-backed, so the fix is a kanban DB edit plus a `scripts/build_kanban_md.py` regenerate — genuinely deferred, and out of a documentation cycle's scope. Target: card `TODO-ALPHA-052-0.1.0`, whose owner should re-derive the population rather than carry an older reading forward.

4. **`CHANGELOG.md`'s `[015-consumer_override_semantics_scalar_fields-0.0.6]` tracking label.** Source: R1's `### Notes for Worker 1` item 7, carried by the integration pass's item 5. A pre-renumber label in prose for a card that is `DONE-019-0.0.6`; its reference-style link definition resolves correctly, so the label alone is the artifact. Deliberately left alone because it belongs to the `[spec-011]` / `[spec-013]` renumber cluster `KANBAN.md` tracks, and half-fixing a cluster leaves it divergently rather than uniformly wrong. Target: the same sweep card, `TODO-ALPHA-052-0.1.0`.

**Not in this catalog, and deliberately named so it is not re-opened.** R1's `### Notes for Worker 1` item 4 deferred a kanban DB edit plus regenerate for `KANBAN.md`'s live `DONE-019-0.0.6` body, on the claim that it still describes the retired mechanism. **That claim is false and the item is not live work.** The integration pass re-derived it at four levels and this gate re-derived the first two independently: `get_type_hints` and `fail-soft` occur **0x** in `KANBAN.md`, **0x** in `KANBAN.html`, and **0 rows** across every text column of `examples/fakeshop/db.sqlite3`; the card's Relay item is a single line naming no detection mechanism, because the kanban DB stores only the first line of each drop-in bullet. No DB edit and no regenerate is owed by this card — which matters beyond one sentence, since a DB-edit-plus-regenerate is the most hazardous class of task in this repo while a concurrent session holds the DB open.

**No fifth item.** The integration pass's `### Notes for Worker 1` item 6 records that there is **no code gap and none opened** — all 19 Slice-1 tests present under their own names at their mandated placements, Slice 2's deletion done, Slice 3's docstring live, Slice 4 long past, Slice 5's docs half holding end to end. That is a confirmation, not a deferral, so it is not carried as catalog work.

### DRY check across this cycle

No new duplication. The cycle introduced no constant, helper, module, or shared literal in any language — no `.py` file was written. The one duplication risk the cycle could carry, the same measurement or contract sentence appearing in both the spec and its rationale companion, was checked directly by the integration pass's `### Pair coherence` and is absent; the rationale's byte table deliberately points at the round artifact rather than restating a count of a file still being written, and that pointer is intact.

### Spec changes made (Worker 1 only)

**None at this gate.** The active spec `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md` and its rationale companion `docs/SPECS/appx/spec-019-consumer_overrides_scalar-0_0_6-rationale.md` were read at this spawn for the status-line re-verification above and for the catalog's re-derivations, and **neither was edited**. The gate surfaced no defect in either that required a custodial correction: all six gate commands passed, the byte counts match the recorded figures exactly (104,017 and 48,834), and every catalog claim re-derived at this gate agreed with the integration pass.

The full record of this cycle's spec edits lives in R1's `### Spec changes made (Worker 1 only)` (25 numbered entries plus the rationale move itself) and the integration pass's (three custodial corrections to the rationale companion). Neither prior artifact was appended to by this gate.

### Summary

The gate ran all six commands and **all six passed**, so the build closes.

- **Full sweep green.** `uv run pytest --no-cov`: `6161 passed, 40 skipped`, zero failures and zero collection errors, run without `-x` or `--maxfail` so no row is hidden and without any `--cov*` flag. The 40 skips were enumerated, not assumed: 37 Postgres-tier and 3 `FAKESHOP_SHARDED`, both standing environment gates. Django's `check` and `makemigrations --check --dry-run` are clean, and the read-only `ruff format --check .` / `ruff check .` / `git diff --check` triple is clean across the whole tree — including the concurrent sessions' ~100 dirty paths, so there is no lint or format drift to attribute to anyone.
- **No failure attribution was owed**, and none was invented. The judgement was prepared against this cycle's diff (four content files, no `.py`, no model, no migration, no schema module) and recorded under `### Failure attribution` so the reasoning is durable even though it did not have to fire.
- **All three plan declarations are deliberate, and all three are stated rather than left blank**: ownership partition `none; single sequential round`, hot path `none`, floor-verification scope `none`. No floor venv was owed, none was built, and this gate closes on no unrun floor claim.
- **Four deferred items, none of them dead.** The `spec015_*` identifiers (4 occurrences, re-derived at this gate), the retired fail-soft vocabulary (4 occurrences across 3 tests — the integration pass's corrected count, superseding R1's 3-across-2), the `[spec-011]` renumber-sweep bullet's population, and the `[015-…]` CHANGELOG tracking label. R1's fifth deferred item — a kanban DB edit plus regenerate — is **excluded and named as excluded**, because the integration pass measured the claim behind it as false at four levels and this gate re-derived two of them.
- **Seven paths are this cycle's**, listed in full for the maintainer's commit. `docs/builder/DONE/` and the concurrent cycle's artifact churn are **not** this cycle's output and must not be swept into it; stage explicitly, never `git add -A`.
- **Nothing was committed.** Only the maintainer commits, and this gate is their first touch point.

Final status: **`final-accepted`**.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

[spec-019-rationale]: ../SPECS/appx/spec-019-consumer_overrides_scalar-0_0_6-rationale.md
[spec-019]: ../SPECS/spec-019-consumer_overrides_scalar-0_0_6.md

<!-- docs/builder/ -->

[bld-integration]: bld-019-integration.md
[bld-r1]: bld-review-1-spec019_rationale.md
[build-019]: build-019-consumer_overrides_scalar-0_0_6.md
[build]: BUILD.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
