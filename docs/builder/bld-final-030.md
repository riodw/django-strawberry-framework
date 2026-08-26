# Build: Final test-run gate (`030` residual reconciliation cycle)

Spec reference: `docs/SPECS/spec-030-connection_field-0_0_9.md` (whole file; header lines 1-11 re-read on entry)
Rationale companion: `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md`
Terms companion: `docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv` (read-only this pass; the integration pass finished it)
Build plan: `docs/builder/build-030-connection_field-0_0_9.md`, checklist item "Final test-run gate"
Status: final-accepted

**Every gate command passed.** Nothing failed, so no attribution, no baseline exception, and no escalation is owed on the gate's own results — and that outcome is recorded as a measurement, not as a silence: each command's exit code and output summary is below. Two things about the tree that a green gate could otherwise hide are stated up front, because both are real and neither is this cycle's:

1. **A floor-verification trigger file went dirty MID-PASS.** `django_strawberry_framework/types/base.py` was clean when this pass began and is `M` now. It belongs to the concurrent session, it touches no `030`-audited symbol, and it is attributed with evidence under `### Floor-verification resolution`.
2. **The full sweep is green over a tree that carries 27 dirty `.py` files this cycle did not write.** A green sweep here therefore proves the suite passes against HEAD-plus-concurrent-work, which is what the gate asks for; it is not, and is not reported as, a clean-HEAD result.

- **Hot-path declaration: none.** Stated explicitly. This pass writes exactly two files (`docs/builder/bld-final-030.md` and the gitignored `docs/builder/worker-memory/worker-1.md`) and no `.py` file, so no code runs differently and no number can move. The plan's conditional clause (a change inside `connection.py::_pipeline_sync` / `::_pipeline_async` / `::_resolve_from_window` / `::_finalize_queryset`, or `optimizer/extension.py::apply_connection_optimization`) is not triggered.
- **Boundary count: 0.** No guard, cap, rejection path, or validation branch is added, so no failability proof is owed and the `### Slice splitting` question does not arise.
- **No `--cov*` flag** was used in any invocation this pass, in any form. `--no-cov` only, per `BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`. Line coverage was neither inspected nor asserted.
- **No `ruff` fix mode.** `ruff format --check` and `ruff check` only, both read-only. Running either in write mode would rewrite the concurrent session's 27 dirty `.py` files.
- **No `git stash`, `git checkout`, `git restore`, `git worktree`, branch, switch, or commit** was run or attempted, in any form.
- **Environment.** `uv run` worked for every command this pass; the concurrent dynamic-version migration that broke it during the rationale pass has settled, and the `.venv/bin/python` fallback the plan's baseline authorizes was not needed. Recorded because the plan told every later pass to expect the failure.

## Working-tree baseline re-read (`git status --short`, re-derived at pass start and again mid-pass)

**Re-derived, not inherited from the plan or from the task brief.** `git status --short` reports **102** entries. Dirty-and-out-of-scope, never edited and never reverted (`AGENTS.md` rule 34):

- **27 dirty `.py` files**, all the concurrent session's — 7 package (`django_strawberry_framework/__init__.py`, `_request_body.py`, `exceptions.py`, `middleware/request_body.py`, `mutations/inputs.py`, `scalars.py`, **`types/base.py`**), 1 script (`scripts/bug_hunt.py`), and 19 test files (`tests/base/test_init.py`, `tests/filters/test_base.py`, `test_factories.py`, `test_inputs.py`, `tests/forms/test_converter.py`, `test_inputs.py`, `test_sets.py`, `tests/mutations/test_fields.py`, `test_inputs.py`, `tests/test_bug_hunt.py`, `test_exceptions.py`, `test_resource_policy.py`, `test_scalars.py`, `test_schema.py`, `test_sets_mixins.py`, `test_strawberry_patches.py`, `test_views.py`, `tests/types/test_relay_interfaces.py`, plus untracked `tests/mutations/test_operations.py`).
- `AGENTS.md`, `pyproject.toml`, `uv.lock` (M), and the untracked `docs/review/**` (~44), `docs/dry/**` (8), `docs/bug_hunt/**` (1) churn.

**The concurrent footprint GREW between the integration pass and this one, and the growth is the load-bearing part.** The integration pass measured **23** dirty `.py` files; there are now **27**. The four new ones are `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/types/base.py`, `tests/mutations/test_fields.py`, and `tests/types/test_relay_interfaces.py`. **`types/base.py` is one of the four files the plan's floor-verification conditional names**, and `tests/types/test_relay_interfaces.py` sits in the `types/` tree — so the growth lands precisely where this cycle's own declaration is keyed. That is why the resolution below is proved rather than asserted.

**This cycle's own footprint is 11 paths and did NOT grow.** Re-derived rather than trusted:

```shell
$ git status --short -- docs/SPECS/ docs/builder/
 M docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv
 M docs/SPECS/spec-030-connection_field-0_0_9.md
?? docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
?? docs/builder/bld-integration-030.md
?? docs/builder/bld-rationale-030.md
?? docs/builder/bld-slice-1-030-connection_base.md
?? docs/builder/bld-slice-2-030-connection_field.md
?? docs/builder/bld-slice-3-030-optimizer_cooperation.md
?? docs/builder/bld-slice-4-030-live_http_export.md
?? docs/builder/bld-slice-5-030-doc_wrap_audit.md
?? docs/builder/build-030-connection_field-0_0_9.md

$ git status --short -- docs/SPECS/ docs/builder/ | grep -c '\.py$'
0
```

Plus `docs/builder/bld-final-030.md` (this file, new) and the gitignored `docs/builder/worker-memory/worker-1.md`. **Every version-controlled path this cycle touches is `.md` or `.csv`.** `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md`, `CHANGELOG.md`, `TODAY.md`, `README.md`, and `scripts/**` are all clean and all fenced out; none was edited or attempted.

---

## Plan (Worker 1)

### Spec status-line re-verification

Read on entry: spec lines 1-11 (title, the shipped-in line, `Status:`, Owner, Predecessors, the rationale-companion pointer). All still describe the cycle's current state:

- `Status: **SHIPPED (0.0.9)**` and the five-slice summary are accurate, including Slice 3's corrected summary and Slice 5's `## [0.0.9]` release-heading clause.
- The Predecessors paragraph's closing sentence — "this card ships and documents the first three, and the fourth's status belongs to `DONE-033-0.0.9`" — is the Slice-3-reconciled form, not the pre-cycle "leaves the fourth planned" form.
- Line 11's rationale-companion pointer resolves: `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md` exists on disk at 100,796 B.

**No status-line edit was needed and none was made.**

### CODE GAP list

**Empty.** All five slices, the rationale pass, and the integration pass each closed with an empty CODE GAP list, and the gate found nothing that changes that: the full sweep is green, both Django consistency checks are clean, and the lint/format/diff gate is clean. Nothing is dispatched to Worker 2, nothing owes a failability proof, and `Status: final-accepted` follows directly.

### Implementation steps / test additions / discretion items

None, three times over, each for the same reason: this pass writes no `.py` file, adds no executable surface, and makes no judgement call the artifacts left open. The gate ran the commands `BUILD.md` `## Final test-run gate` names, in the order it names them, and recorded them.

---

## Final verification (Worker 1)

### Gate command results

Every command was run from the repository root in the shared `.venv` via `uv run`. Exit codes were captured per command, not inferred from output text.

| # | Command | Verdict | Output summary |
|---|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** (exit 0) | `6570 passed, 42 skipped in 135.19s (0:02:15)`; a confirming re-run with `-rs` 20 min later: `6571 passed, 42 skipped`, exit 0 |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** (exit 0) | `System check identified no issues (0 silenced).` |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** (exit 0) | `No changes detected` |
| 4a | `uv run ruff format --check .` | **PASS** (exit 0) | `429 files already formatted` |
| 4b | `uv run ruff check .` | **PASS** (exit 0) | `All checks passed!` |
| 4c | `git diff --check` | **PASS** (exit 0) | no output |
| 5 | Floor verification | **resolves to `none`** | proved inversely below; no floor venv built |

**Command 1 — the full sweep, run to completion and its output read in full.** Not a truncated or interrupted run: the process exited 0 and its final line is the summary quoted above. 6,570 rows across all three test trees per `AGENTS.md` (package `tests/`, per-app `examples/fakeshop/apps/<app>/tests/`, live `examples/fakeshop/test_query/`) plus `examples/fakeshop/tests/`. **No `--cov*` flag in any form.**

**The 42 skips are environment gates, not silent failures — and the census corrected my first assumption, which is why it was run.** I expected the sharded-mode gate (`AGENTS.md` line 30, sharded tests behind `FAKESHOP_SHARDED`) and sampled two rows that fit it. A full `-rs` census over the whole sweep says the sharded gate accounts for **3 of 42**; the dominant gate is the **Postgres tier**:

| Rows | Gate | Sites |
|---|---|---|
| 37 | `requires the Postgres tier (FAKESHOP_PG_DSN)` | `tests/test_lateral_pg_parity.py` (35 across module-level + 6 function sites), `tests/test_predicate_pg_explain.py` (2) |
| 2 | `could not import 'django.contrib.postgres.fields': No module named 'psycopg2'` | `tests/types/test_converters.py:1300`, `:1541` |
| 2 | `requires FAKESHOP_SHARDED=1 (the sharded DATABASES layout)` | `examples/fakeshop/test_query/test_multi_db.py:39`, `examples/fakeshop/apps/library/tests/test_generic_connection_sharded.py:29` |
| 1 | `multi-DB alias pin needs the FAKESHOP_SHARDED 'shard_b' alias` | `tests/test_permissions.py:823` |

All four are declared environment gates under the default invocation and none is `030`-adjacent. **Recording the correction rather than the tidy version of it**: two sampled rows that both fit a hypothesis read exactly like a measured population, and here they were 2 of 42.

**A second thing the census exposed: the row count moved between two runs of the identical command.** The gate run reported `6570 passed`; the `-rs` census run ~20 minutes later reported `6571 passed`, same 42 skips, both exit 0. Nothing in this cycle changed — it writes no `.py` file — so the extra row is the concurrent session's, consistent with `tests/types/test_relay_interfaces.py` and the two `tests/mutations/` files going dirty during this pass (see the baseline re-read). **Both runs are green, and the pass/fail verdict is what the gate turns on, not the count.** It is worth stating plainly because it is `BUILD.md`'s own "a bare count rots" hazard observed live: a row total measured against a tree a concurrent session is writing is a reading at an instant, not a property of the suite, and a later pass that treats `6570` as a fixed expectation would be comparing against a number that was already stale when written.

The known order-dependent `DuplicatedTypeName` / `LazyType KeyError` class (`BUILD.md` `### Example-project schema changes must sync every schema-module list`) **did not fire**. It could not have been this cycle's in any case — no app and no schema module was added, and no schema-module list was touched — but a green full parallel run is the only instrument that can say it did not fire at all, and it is the run that was performed.

**Command 4a's stderr carries one advisory, and it is not a failure.** `warning: The following rule may cause conflicts when used with the formatter: COM812` is a pre-existing `pyproject.toml` lint-configuration advisory about a rule `AGENTS.md` line 17 deliberately keeps enabled (`scripts/check_trailing_commas.py`, not ruff, owns single-line explosion). The command exited 0. It is named here so a future reader does not mistake it for a regression this cycle introduced — the warning predates the cycle and this cycle touched neither `pyproject.toml` nor any `.py` file.

**Command 4c's scope, stated rather than assumed.** `git diff --check` scans the **tracked, modified** working tree for whitespace errors and conflict markers; it does not read untracked files. Nine of this cycle's eleven paths are untracked (`??`), so they are outside what that command can see. Their equivalent gate was run and is recorded under `### Cycle deliverable consistency checks` — `scripts/check_trailing_commas.py --check`, which is the project's own whitespace / layout / link-scaffold gate and which reads a path regardless of git status. Staging the untracked files to widen `git diff --check` was rejected deliberately: `git add -N` mutates the index that a concurrent session is committing from.

**The coverage of that substitute gate is bounded, and the bound is measured rather than assumed.** It covers the three `docs/SPECS/` files (all three exit 0, silently). It does **not** cover the eight `bld-*-030` / `build-030` artifacts or this file: `scripts/check_trailing_commas.py --check docs/builder/bld-final-030.md` reports `excluded from the source-layout rules -- not checked`, because `docs/builder/bld-*.md` is a per-cycle scratchpad that `START.md` `## Temp artifact conventions` exempts from stylistic cleanup by design. So the nine builder artifacts sit outside both instruments — `git diff --check` cannot see them (untracked) and the layout gate declines them (exempt). That is the intended arrangement, not a hole this pass should plug, but a gate report that implied full coverage of all eleven paths would be overstating what ran.

### Attribution: nothing failed, so nothing needs attributing away

Recorded as a positive statement because the reverse — a failure quietly excused — is the finding this section exists to prevent.

- **No `pytest` failure, error, or collection error.** So no `## Claims are proven mechanically, never accepted on prose` obligation was incurred: there is no "pre-existing at HEAD" claim to record, no failing node id list, no traceback, and no escalation. Had one fired, this pass could not have reproduced it at clean HEAD — the tree carries 27 concurrent-owned dirty `.py` files and `git stash` / `git checkout` / `git worktree` are banned — and the discharge would have been to record the node ids, the traceback, the read-only `git show HEAD:<path>` content, and whether the failing test or its code sits in this cycle's footprint, then escalate. Nothing triggered it.
- **No `ruff format --check` or `ruff check` complaint against any file, this cycle's or the concurrent session's.** All 429 files are formatted and all lint checks pass, so there is no "this belongs to the concurrent session" call to make. `ruff` has no `.md` / `.csv` scope, so this cycle's own eleven paths were never in its purview — which is why "expect none" was the right prediction and is now a measurement.
- **No `git diff --check` whitespace error or conflict marker anywhere in the tracked tree**, including in the 27 concurrent-owned dirty `.py` files.
- **No pre-flight baseline exception was invoked**, because none was needed. The plan's preamble records the baseline as dirty and `BUILD.md` permits an exception to keep a baseline failure from blocking `final-accepted`; no gate command failed, so the mechanism is unused. Stated explicitly rather than left unmentioned: an unused exception mechanism and a quietly-applied one read identically in a report that omits the sentence.

### Floor-verification resolution: `none`, proved inversely

The plan's floor-verification scope is **conditional**, not unconditional: it fires for "any slice that lands a `.py` change under `connection.py`, `types/base.py`, `types/definition.py`, or `optimizer/extension.py`", and "a spec-only slice declares `none`". So the resolution turns on a fact about this cycle's footprint, and that fact is measured rather than asserted:

```shell
$ git status --short -- docs/SPECS/ docs/builder/ | grep -c '\.py$'
0
```

**No `.py` file is in this cycle's footprint at all** — the eleven paths are two `.md`, one `.csv`, and eight `.md` builder artifacts. Every slice artifact and the integration artifact independently declared `none` on the same inverse proof. **Resolution: `none`. No floor venv was built, none is owed, `/tmp/dsf-floor` was not created, and the shared `.venv` was not mutated, installed into, or downgraded.**

**The complication, named because it would otherwise be invisible: `django_strawberry_framework/types/base.py` — a named trigger file — is dirty, and it went dirty DURING this pass.** It was absent from `git status` when this pass started and present a few minutes later. It is the concurrent session's, and the attribution is proved from three directions rather than argued:

```shell
$ git diff --stat HEAD -- django_strawberry_framework/types/base.py
 django_strawberry_framework/types/base.py | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)

$ git diff HEAD -- django_strawberry_framework/types/base.py | grep -E '^@@'
@@ -51,6 +51,7 @@ from strawberry.relay.types import NodeIDPrivate
@@ -406,7 +407,7 @@ def _validate_globalid_strategy(

$ git diff HEAD -- django_strawberry_framework/types/base.py \
    | grep -E '^[+-]' | grep -icE '_validate_connection|ALLOWED_META_KEYS|_is_relay_shaped|cursor_field|connection'
0
```

1. **It is not this cycle's edit.** This cycle's footprint contains zero `.py` files, and no pass in it has write access to `django_strawberry_framework/**`. The plan fences package `.py` files out for every dirty-but-untouched file (`AGENTS.md` rule 34), and this pass's writable list is four paths, none of them a `.py` file.
2. **It does not touch a `030` surface.** Two insertions and one deletion, in two hunks: an import addition near line 51 and a one-line change inside `_validate_globalid_strategy`, which is a `DONE-031-0.0.9` GlobalID surface. **Zero** added-or-removed lines mention `_validate_connection`, `ALLOWED_META_KEYS`, `_is_relay_shaped`, `cursor_field`, or `connection` in any casing — so Slice 1's audit of `_validate_connection`'s four rejection paths, the `"connection"` membership in `ALLOWED_META_KEYS`, and the shared `_is_relay_shaped` predicate are all unaffected, and the four `raise ConfigurationError` sites the integration pass's I2 counted against `types/base.py::_validate_connection` still stand.
3. **The conditional was never armed.** It fires on a slice **landing** a change, not on a file **being** dirty. No slice landed one. The resolution is `none` on the plan's own terms, and would be `none` even if the concurrent change were larger.

**It is not reverted, not edited, and not "tidied."** It stays exactly as the concurrent session left it.

### Archival state and companion pairing — confirmed on disk

The cycle's stated end state was the spec at `docs/SPECS/` with **both** companions at `docs/SPECS/appx/`, matching every prior archived spec. Confirmed by reading the disk, not by assuming the move happened:

```shell
$ ls -la docs/SPECS/spec-030-connection_field-0_0_9.md \
         docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv \
         docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
-rw-r--r--  100796  docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
-rw-r--r--    8378  docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv
-rw-r--r--  138692  docs/SPECS/spec-030-connection_field-0_0_9.md

$ ls docs/spec-030*
zsh: no matches found: docs/spec-030*     # no stray copy at the old working location

$ ls docs/SPECS/*-rationale.md docs/SPECS/*-terms.csv
zsh: no matches found                      # no companion stranded beside the spec instead of under appx/
```

Three properties, each measured: the spec is at `docs/SPECS/`; both companions are at `docs/SPECS/appx/`; and there is no residual copy at either the pre-archival working location or the wrong archived directory. The `<!-- docs/SPECS/ -->` link-definition group header covers `docs/SPECS/appx/` as its subdirectory, per `START.md`'s closed ten-header list — no eleventh header was earned or attempted anywhere in this cycle.

**The pairing claim was checked against the whole archive, not only against `030`.** A per-spec existence walk over all 56 files in `docs/SPECS/` shows **`spec-001` through `spec-030` each carry both companions, with no gap** — so `030` is now contiguous with the 001-029 run the plan's premise named, which is the exact end state the cycle set out to reach. The walk also surfaced a broader gap that is **not** this cycle's and is carried to the catalog as item 13.

### Cycle deliverable consistency checks

The two deliverables are the reconciled spec and the new rationale companion. Both were read this pass and both validate.

**1. `check_spec_glossary` holds at the required count.**

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-030-connection_field-0_0_9.md
OK: 50 terms - all have glossary entries and at least one spec link.
EXIT=0
```

Matches the pre-flight reading (`OK: 50 terms`) and every slice's postcondition. The count is unchanged across the whole cycle, which is the invariant the terms-CSV amendment's bounds were written to protect.

**2. `check_trailing_commas --check` over the three files this cycle wrote under `docs/SPECS/`.**

```shell
$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-030-connection_field-0_0_9.md \
    docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md \
    docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv
EXIT=0
```

Silent and exit 0 — the markdown link scaffold, the ten canonical group headers, and the layout rules all hold on both `.md` files, and the `.csv` passes. This is also the untracked-file gate that `git diff --check` structurally cannot provide (see command 4c above).

**3. `import_spec_terms --check`, run and recorded verbatim.**

```shell
$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
EXIT=0
```

Green, and identical to the integration pass's reading — the known baseline failure on an earlier done card is not present at this HEAD. **The importer was never run without `--check`** in this pass or any pass of this cycle.

**4. `examples/fakeshop/db.sqlite3` is unmodified by this cycle.**

```shell
$ git status --short -- examples/fakeshop/db.sqlite3
(no output)
```

Clean — not dirtied by this cycle and not dirtied by the concurrent session either. Nothing was reverted, and nothing would have been: `BUILD.md` `### Tracked binary / generated files` and `AGENTS.md` rule 34 both forbid it.

**5. The terms CSV's readability postcondition, re-derived rather than inherited.** The integration pass's I11 found `csv.DictReader` silently truncating 8 of 50 `notes` cells at the first unquoted comma and rewrote the file through `csv.writer`. Re-measured this pass with the same parser both readers use:

```
data rows=50   rows with restkey (truncated notes)=0
header: term,anchor,notes
anchors unique (one row per anchor): True
```

**0 of 50** truncate, the row count is 50 data rows as before, and the one-row-per-anchor shape holds. The CSV was read only; this pass did not write it.

**6. Both deliverables read end to end.** The spec (724 lines / 138,692 B) and the companion (502 lines / 100,796 B). The spec reads as a single current contract with no chronology, no amendment block, and no "as of `033`" hedge; the companion carries the chronology, with each moved passage's retraction stated as a `**Post-ship:**` bullet under the owning Decision. **No defect was exposed in either, so neither was edited — which is the expected outcome of a gate, and is recorded as a result rather than as an absence.**

### Deferred work catalog

The next spec author's reading list, and this cycle's most valuable output. Walked from **all seven** completed artifacts — `bld-rationale-030.md` `### Notes for Worker 1 (spec reconciliation)`; each slice artifact's `### Handed forward to …`, `### CODE GAP list`, and `### Spec changes made … deferral reasons` sections; `bld-slice-5-030-doc_wrap_audit.md` `### Maintainer findings`; and `bld-integration-030.md` `### Carried items 1-9` and `### Deferred work catalog for the final gate`.

**Every item below was re-measured this pass.** Two of the re-measurements changed an item materially (items 6 and 13), which is the point of re-deriving rather than copying forward. Nothing here is fixable inside this cycle's scope fence.

**1. MF-1 — `docs/GLOSSARY.md`: the three `030` entries never state that `totalCount` selection-gating is directive-resolved.** *(DB-backed regenerate.)*
Source: `bld-slice-5-030-doc_wrap_audit.md` `### Maintainer findings`, Population C; carried by `bld-slice-4-030-live_http_export.md` `### Handed forward to Slice 5`. Licensing spec text: the Slice-5 `## Doc updates` glossary obligation, which asks for status flips and says nothing about the directive property. Re-derived: a section-scoped sweep of `docs/GLOSSARY.md` for `@skip` / `@include` / `directive` / `should_include` inside the `DjangoConnectionField`, `DjangoConnection`, and `Meta.connection` entries returns **0 occurrences in all three**, while the same vocabulary occurs **4** times in the spec. A consumer reading only the glossary cannot tell whether a `@skip`-ed `totalCount` still costs a query; the gate is `optimizer/selections.py::should_include` and is live-pinned by `examples/fakeshop/test_query/test_library_api.py::test_genre_connection_total_count_skip_include_no_count`.

**2. MF-2 — `docs/GLOSSARY.md`: `Meta.cursor_field` is shipped, finalization-validated public surface with no glossary heading, while other entries' bodies reference it.** *(DB-backed regenerate.)*
Source: `bld-slice-5-030-doc_wrap_audit.md` `### Maintainer findings`, Population D; first raised in `bld-slice-1-030-connection_base.md` `### Handed forward to Slices 2-5`. Licensing spec text: none — the spec correctly needs no change, because `Meta.cursor_field` is never rendered as a glossary link and is absent from the terms CSV, so `check_spec_glossary` is satisfied and Decision 9's citation of `django_strawberry_framework/keyset.py` is the right choice while no anchor exists. Re-derived: `grep -c '^## Meta.cursor_field' docs/GLOSSARY.md` = **0**, while the key is referenced in two entry bodies (`docs/GLOSSARY.md:391` under `Connection-aware optimizer planning`, `:547` under `DjangoConnection`) as though a reader could look it up. Every other `Meta` key has a heading.

**3. MF-3 — `CHANGELOG.md`: zero entries for keyset cursors or `Meta.cursor_field`.** *(Text edit.)*
Source: `bld-slice-5-030-doc_wrap_audit.md` `### Maintainer findings`; carried unchanged by Slices 1-4. Licensing spec text: none; the feature is not `030`'s, which is likely how it fell between two cards' changelog obligations. Re-derived: `grep -ci keyset CHANGELOG.md` = **0**, `grep -c cursor_field CHANGELOG.md` = **0**. The keyset codec, its `Meta.cursor_field` opt-in, and the AES-SIV soft dependency all shipped on the `0.0.14` line as public surface, against a file whose own header promises "All notable changes … will be documented in this file".

**4. MF-4 — the already-sliced-`QuerySet` `GraphQLError` is undocumented in both `CHANGELOG.md` and `docs/GLOSSARY.md`.** *(Text edit for `CHANGELOG.md`; DB-backed regenerate for the glossary.)*
Source: `bld-slice-2-030-connection_field.md` `### Handed forward to Slices 3-5` (new from that pass), then `bld-slice-5-030-doc_wrap_audit.md` `### Maintainer findings`, Population E. Licensing spec text: none — the guard is now contracted in the spec at six sites, but neither standing doc was ever in a card's obligation for it. Re-derived: `grep -ciE 'pre-sliced|already-sliced|already sliced|pre sliced'` returns **0** in `CHANGELOG.md` and **0** in `docs/GLOSSARY.md`. `connection.py::_guard_source_not_pre_sliced` converts a raw boundary `TypeError` into a clear `GraphQLError` when a consumer `resolver=` returns `Category.objects.all()[:5]` — a consumer-visible error contract on a shipped field, in neither file. Slice 2 established the guard reached the package through a commit naming no card and no spec, which is why no card's doc obligation covered it.

**5. MF-5 — the terms-CSV `notes` column asserts statuses no instrument reads.** *(Content half RESOLVED by the integration pass; the GATE half is an open maintainer proposal.)*
Source: `bld-slice-5-030-doc_wrap_audit.md` `### Maintainer findings` and `### Handed forward to the integration pass`; resolved for `spec-030` by `bld-integration-030.md` I10 / I11. **The gate question stands:** `scripts/check_spec_glossary.py` validates only the `term,anchor` pair against real glossary headings and never reads `notes`, so that column can assert arbitrary statuses indefinitely with no instrument objecting. The proposal is one decision: either `notes` is contract text and needs a gate, or it is scratch and must stop asserting statuses. **Two measurements now support it, and the second is evidence the gap has already bitten**: `030`'s column drifted to **12** stale cells with nothing objecting, and `csv.DictReader` — the parser **both** readers use (`check_spec_glossary.py::load_terms` and the fakeshop `import_spec_terms` command) — was **silently truncating 8 of 50 `notes` cells** at the first unquoted comma, including the very cell whose dropped tail held the `WIP-032` mention the finding flagged. So part of the column never reached the DB at all. **Fence note: `scripts/**` was outside this cycle's fence** and is on this pass's do-not-touch list; no edit to it was made or attempted. Post-fix on disk: 0 of 50 truncate (re-derived above). Consequence for the maintainer: the reconciled cells change a file, not the database — they reach the glossary DB only when the importer next runs without `--check`.

**6. MF-6 — stale `docs/spec-…` paths inside kanban card bodies. RE-DERIVED AND MATERIALLY WIDER than the finding as recorded: it is 8 cards, not 1.** *(DB-backed regenerate — ORM row edits plus `scripts/build_kanban_md.py` / `scripts/build_kanban_html.py`; note `KANBAN.html`'s Vue shell is hand-edited and only its data block regenerates.)*
Source: `bld-slice-5-030-doc_wrap_audit.md` `### Maintainer findings`, Population G, framed there as "half-archived residue inside one card"; carried by `bld-integration-030.md` catalog item 6. Licensing text: `AGENTS.md` rule 26, which says the archival step "rewrites every cross-reference in one sweep".
For `DONE-030-0.0.9` the recorded finding re-derives exactly: `KANBAN.md:3479` (a DoD checkbox, `Add docs/spec-030-connection_field-0_0_9.md.`) and `:3514` (the description bullet), against a correct `Spec:` field and a correct board index row — 2 stale against 2 correct inside one card, which is why a whole-file count could never have distinguished "archived" from "half-archived".
**The task asked whether other cards share it. They do.** A path-existence walk over every `docs/spec-…` token in `KANBAN.md` classifies each against the disk:
- **8 archived specs are rotted, at 11 occurrences**: `spec-028-orders-0_0_8` (2), `spec-029-consumer_dx_cleanup-0_0_9` (2), `spec-030-connection_field-0_0_9` (2), `spec-032-full_relay-0_0_9` (2), and `spec-033-connection_optimizer-0_0_9`, `spec-034-permissions-0_0_10`, `spec-035-optimizer_hardening-0_0_10`, `spec-045-visibility_boundary-0_0_14` (1 each). Every one of these files exists at `docs/SPECS/<basename>` and **not** at the cited path.
- **6 further tokens are NOT rot and must not be swept**, which is exactly why a blind `docs/spec-` → `docs/SPECS/spec-` substitution would be the wrong fix: `docs/spec-056-pg_full_text_search-0_1_2.md`, `docs/spec-057-aggregates-0_1_3.md` (2), and `docs/spec-059-node_sentinel-0_1_4.md` name specs that **do not exist yet** — `AGENTS.md` rule 26 puts an in-flight spec at `docs/`, so those paths are correct-in-advance; and `docs/spec-aggregates.md`, `docs/spec-pg_full_text_search.md`, `docs/spec-search_fields.md` are pre-canonical unnumbered names a card body cites historically, the same shape as Decision 1's deliberate `docs/spec-connection.md` contrast.
The board carries **154** correct `docs/SPECS/` occurrences against those 11 rotted ones, so the sweep mostly landed — and the residue is one class of miss (paths inside card **bodies**, as opposed to `Spec:` fields and index rows) repeated across 8 cards rather than a one-card accident. **The fix is one DB pass over 11 rows, and it needs the three-way classification above, not a global replace.**

**7. MF-7 — the keyset-cursor feature has no owning spec.** *(New spec, or a `BACKLOG.md` / card decision.)*
Source: `bld-integration-030.md` `### Carried items 1-9` item 6, found by that pass's guard sweep over `connection.py`. Licensing spec text: none — Decision 9 states that `connection.py` owns the dispatch seam and `keyset.py` owns the codec, which correctly attributes the four raise sites away from `030` but leaves them owned by nothing. Re-derived: no `docs/SPECS/` or `docs/` spec file has `keyset` or `cursor` in its name; `Meta.cursor_field` is *mentioned* by **8** archived specs (`spec-010`, `spec-015`, `spec-030`, `spec-032`, `spec-033`, `spec-049`, `spec-053`, `spec-055`) and is the *subject* of none. The surface is real: `cursor_field` is in `ALLOWED_META_KEYS`, two-stage validated (`types/base.py::_validate_cursor_field` at class creation plus `validate_cursor_field_columns` at finalization), 31 occurrences in `keyset.py`, and **four `GraphQLError` raise sites inside `connection.py`** (`_keyset_order_state` ×3, `_resolve_keyset_connection` ×1). It shipped as `BACKLOG.md` item 39 sub-feature 3, commit `51421e54`. **Combined with items 2 and 3 this is one feature missing all three of its documentation homes — spec, glossary entry, changelog entry — which is why it is one maintainer decision rather than three.**

**8. The card-less-provenance finding, carried in the framing the integration pass finally reached — not the alarm the slices opened it with.** *(Framing to carry; no repair owed.)*
Source: opened in `bld-slice-2-030-connection_field.md` `### Handed forward to the integration pass`, extended by Slices 3, 4, and 5, then bounded and reframed in `bld-integration-030.md` `### Carried items 1-9` item 5. The bounded sweep — `git log --oneline --reverse -S<symbol>` over `connection.py` and `optimizer/extension.py` for ten symbols — found **11 distinct commits naming no card and no spec**, and asking Slice 5's two questions of each returned **nothing further uncontracted**: every `_guard_*` and `_require_async_iterable_context` is now contracted, and the two guard-touching commits spot-checked (`6912ca92`, `0e864b7e`) are pure call-site consolidation. **So card-less commits are this repo's ordinary mode, not an anomaly**, and "the commit named no card" is not the risk. The risk has a sharper form: **`6912ca92`, a card-less DRY pass four days after the card shipped, is what created the single-call-site invariant that Slice 1's entire `_guard_first_and_last` reachability audit rests on.** A card-less commit's hazard is less that it adds uncontracted surface (measured: it did not) than that it can silently author or destroy the invariant a later audit will lean on. Slice 5 adds the one direction the sweep could not cover: **a card-less commit's DOC debt is invisible to every instrument this cycle used** — items 3 and 4 are exactly that consequence, a feature belonging to no card's doc obligation getting no changelog entry and no glossary heading with no gate noticing. Any future `git log -S` provenance sweep should therefore ask, per hit, whether the surface it finds is *documented*, not only whether it is contracted.

**9. An instrument bug the integration pass found in its own checker, and any future link-audit script must handle it.** *(Method note; no repair owed in this repo's source.)*
Source: `bld-integration-030.md` `### Populations swept…` instrument notes and postcondition proof 3. **`START.md` contains the literal `<!-- LINK DEFINITIONS -->` twice** — once at `START.md:65` in the prose documenting the convention, once as the actual delimiter — so a body/definitions split at the *first* occurrence dumps **40 lines of live prose** into the definitions block, where its real `][build]` use is never counted. The checker reported `unused defs: ['build']` on a file that is not broken, and the hit was explainable ("documentation artifact") in a way that read exactly like a real finding. Two further notes from the same validation: DOTALL fence-stripping mispairs on an odd fence count and must be replaced by line-based tracking; and the delimiter count must be checked before trusting any split. `spec-030` and its companion each contain the delimiter exactly once, so their results stood — but a future link-audit script over the whole of `docs/SPECS/` will meet this. **And it will meet it in THIS file**: measured after writing, `grep -c 'LINK DEFINITIONS' docs/builder/bld-final-030.md` = **2**, because documenting the literal is what creates the second occurrence. The population is therefore "any file that documents the convention", not "`START.md`" — which is a wider population than the finding as it was recorded, and the reason it is worth stating as a rule (count the delimiter, then split on the last) rather than as an anecdote about one file.

**10. The unrecorded `0.0.9` review round of this spec.** *(Provenance gap; record it, do not invent its contents.)*
Source: `bld-rationale-030.md` `### Notes for Worker 1 (spec reconciliation)` note 5; carried through Slices 1-4 and into `bld-integration-030.md` catalog item 10. The revision history the rationale move preserved verbatim lists **three revisions and one finding round**, yet **four finding labels** are cited from live code and tests — `P1-B`, `P3a`, `P3b`, and an `Open Question: direct relay.Node` — three of which occurred **zero** times in the pre-move spec. Two shipped `030` contracts arrived through rounds the history does not record: the directive-resolved `totalCount` selection gate came through `9e864f59` "Finish REVIEW of 0.0.9", and `e2b5b10b` is titled "spec-030 review round". All four labels and both contracts are now homed in the companion and stated in the spec, so this is a **provenance** gap, not a code or contract gap. **The round's contents were never recorded and must not be reconstructed.** The general warning is what a future pass needs: this spec's revision history is not the complete record of what reshaped it.

**11. `test_anonymous_inline_fragment_under_connection_field_resolves` is correctly absent from `spec-030` and must stay absent.** *(Boundary to preserve; no repair owed.)*
Source: `bld-slice-4-030-live_http_export.md` `### Handed forward to Slice 5 and the integration pass`; honored and verified by `bld-integration-030.md` `### Carried items 1-9` item 8. The test lives in `examples/fakeshop/test_query/test_library_api.py` (commit `9e864f59`) inside `030`'s own live block, but its subject is an **optimizer selection-walker** High, not a `030` contract. Verified as a postcondition rather than merely intended: `grep -c 'test_anonymous_inline_fragment' docs/SPECS/spec-030-connection_field-0_0_9.md` = **0**. Named so a later sweep of that live block does not adopt it into `030`'s Test plan on proximity.

**12. The archived-spec inline-link-TEXT rot is not `spec-030`-specific, and a resolution check structurally cannot find it.** *(One sweep in its own pass; outside this cycle's fence.)*
Source: `bld-slice-5-030-doc_wrap_audit.md` `### Handed forward to the integration pass` (its method note) and `### Maintainer findings` Population A; acted on for `spec-030` in `bld-integration-030.md` postcondition proof 4, carried as catalog item 9. Population A is the first population in this cycle where **the reference-style definitions were correct and the visible link text was wrong** — `spec-030` said `docs/spec-030-connection_field-0_0_9.md` in prose at 7 occurrences over 5 lines while every `[ref-id]: …` definition resolved. **Any sweep that checks link resolution — including the anchor checker every slice of this cycle used — reports a clean file in exactly that case.** The instrument that works reconstructs the visible path and classifies it by prefix. `spec-030`'s sites are closed (0 post-edit, re-derived by the integration pass), but **the same archival sweep produced every archived spec**, so the same latent population exists across `docs/SPECS/`. Note the overlap with item 6: that is the same defect class on the kanban side, and the same three-way classification (rot / correct-in-advance / historical name) will be needed.

**13. NEW this pass — the rationale-companion coverage gap across the archive: 21 of 56 archived specs have no `-rationale.md`, and 2 have no `-terms.csv`.** *(Maintainer decision on whether the companion is retrospective policy or forward-only.)*
Source: derived from the archival-pairing confirmation above, extending the premise the build plan's `## Cycle purpose` opens with ("Every archived spec from `001` through `029` has one … `spec-030` has only its `-terms.csv`"). That premise is now satisfied, and the per-spec walk that confirmed it shows the run is **contiguous from `001` to `030` and then stops**: `spec-031` through `spec-043`, `spec-049` through `spec-055`, and `spec-063` carry no rationale companion — **21 specs** — while `spec-044` through `spec-048` do. Two specs carry no terms CSV either (`spec-053-graph_substrate-0_1_1`, `spec-063-structural_templates-0_1_6`), both unshipped. **This cycle exists because `030` was the one gap inside the 001-029 run; closing it makes `031` the new leading edge of a much larger one.** Whether that matters is a maintainer call — the companion is a `BUILD.md` pre-flight step for *new* builds, and nothing says an already-shipped spec owes one retroactively — but it is now a 21-spec question rather than a 1-spec one, and this cycle is the reason anybody can see it. Named here rather than acted on: creating 21 rationale companions is not a residual reconciliation cycle.

**14. Decision 13's no-version-bump rule survives only because four spec sites cite a SYMBOL rather than a file.** *(Method note to preserve; a future "simplify the citation" edit would falsify all four.)*
Source: `bld-slice-5-030-doc_wrap_audit.md` `### Summary`, stated there as "the finding worth carrying". Across `030`'s four commits `pyproject.toml` and `uv.lock` are untouched and `__version__` is byte-identical `"0.0.8"`, so Decision 13 holds — but the doc-wrap commit `8cac3495` **does** touch `tests/base/test_init.py`, for Decision 14's `__all__` pin. The rule reads as true only because all four spec sites name `tests/base/test_init.py::test_version` rather than the bare file. A later editor shortening those citations to the filename — the kind of tidy-up that looks harmless — would make four spec sentences false at once, and no gate in this repo would see it.

### Summary

Every command in `BUILD.md` `## Final test-run gate` passed, in the order that section gives them: the full `uv run pytest --no-cov` sweep (**6570 passed, 42 skipped**, exit 0, all three test trees, no `--cov*` flag, output read in full; a confirming `-rs` re-run 20 minutes later gave `6571 passed, 42 skipped`, exit 0 — one row the concurrent session added mid-pass, which is `BUILD.md`'s "a bare count rots" hazard observed live), `manage.py check` (no issues), `makemigrations --check --dry-run` (no changes), and the read-only lint/format/diff gate (`429 files already formatted`, `All checks passed!`, `git diff --check` silent). **The skip census corrected my own first assumption and is recorded that way**: I expected the `FAKESHOP_SHARDED` gate and sampled two rows that fit it, where the real breakdown is 37 Postgres-tier, 2 missing-`psycopg2`, 2 sharded, 1 multi-DB alias — two conforming samples read exactly like a measured population. **Nothing failed, so no attribution, no baseline exception, and no maintainer escalation is owed on the gate's results** — and both facts a green gate could hide are stated instead of omitted: the sweep is green over a tree carrying **27** concurrent-owned dirty `.py` files, and `django_strawberry_framework/types/base.py` — a named floor-verification trigger file — **went dirty mid-pass** from that same session, touching **zero** `030`-audited symbols across two hunks (an import and a `_validate_globalid_strategy` line, a `031` surface).

**Floor verification resolves to `none`, proved inversely rather than asserted**: the plan's scope is conditional on a slice landing a `.py` change under `connection.py` / `types/base.py` / `types/definition.py` / `optimizer/extension.py`, and this cycle's footprint contains **0** `.py` files across all eleven paths. No floor venv was built and the shared `.venv` was not mutated. The archival end state is confirmed on disk — spec at `docs/SPECS/`, **both** companions at `docs/SPECS/appx/`, no stray copy at either the pre-archival location or beside the spec — and the per-spec walk that confirmed it shows `001` through `030` now paired contiguously, which is precisely what the cycle set out to achieve. `check_spec_glossary` holds at `OK: 50 terms`, `check_trailing_commas --check` passes on all three `docs/SPECS/` files this cycle wrote (and is the untracked-file gate `git diff --check` cannot be), `import_spec_terms --check` is green at `OK: 49 done cards have glossary links.` with the importer never run without `--check`, and `examples/fakeshop/db.sqlite3` is unmodified.

**The `### Deferred work catalog` carries 14 items, every one re-measured rather than inherited, and two of the re-measurements changed the item.** MF-6 is not "half-archived residue inside one card": a path-existence walk over `KANBAN.md` finds **8 archived specs rotted at 11 occurrences across 8 cards**, against 154 correct `docs/SPECS/` occurrences — and six further `docs/spec-…` tokens that must **not** be swept, three naming specs that do not exist yet (correct-in-advance under `AGENTS.md` rule 26) and three pre-canonical historical names. So the fix is 11 targeted DB rows with a three-way classification, never a global replace. And item 13 is new: closing `030`'s missing companion makes `031` the leading edge of a **21-spec** rationale-companion gap that nobody could see while `030` was the one hole in the `001`-`029` run. The catalog's remaining shape is what the cycle's slices earned — four inverse-audit documentation gaps (the directive-resolved gate, `Meta.cursor_field`, keyset cursors, the pre-sliced-queryset error, three of which are one feature missing all three of its doc homes), one gate gap with two supporting measurements including a parser that was silently dropping 8 of 50 cells, one un-owned feature, and five method notes a future pass will need: the card-less-provenance reframing with its doc-debt corollary, the `START.md` double-delimiter instrument bug, the unrecorded review round, the link-TEXT-versus-resolution blind spot across the whole archive, and the symbol-not-file citation that alone keeps Decision 13 true.

**CODE GAP list: empty**, for the seventh consecutive pass of this cycle. The gate exposed no defect in either deliverable, so neither the spec nor the rationale companion was edited this pass — the expected outcome, recorded as a result. Hot-path: **none**. Boundary count: **0**. Floor verification: **none**. All three stated explicitly.

**Status: `final-accepted`.** The build cycle is closed and hands to the maintainer, who reviews the whole cycle and commits the eleven paths plus this artifact at their discretion. Worker 0 may mark the plan's final checkbox.

### Spec changes made (Worker 1 only)

**None.** The gate exposed no defect in `docs/SPECS/spec-030-connection_field-0_0_9.md` or `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md`, so neither was edited. The spec's header/status lines were re-read on entry per `worker-1.md` `## Spec status-line re-verification` and still describe the cycle's current state, so no status-line repair was owed either.

The final gate has no `### Spec slice checklist (verbatim)` — it implements no spec slice. Its equivalent obligation is the five numbered gate commands plus the four closing checks, and all nine are discharged above with their measured outcome. Nothing is deferred without a stated reason and nothing is silently dropped.

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
