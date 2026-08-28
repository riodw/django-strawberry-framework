# Build: final test-run gate — `034` residual-reconciliation cycle

Spec reference: `docs/SPECS/spec-034-permissions-0_0_10.md` (whole file; not edited by this pass)
Rationale companion: `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` (not edited by this pass)
Build plan: `docs/builder/build-034-permissions-0_0_10.md`
Inputs: `bld-034-slice-0-rationale_extraction.md`, `bld-034-review-1a-cascade_module.md`, `bld-034-review-1b-composition_pins.md`, `bld-034-review-1c-fakeshop_and_surface.md`, `bld-034-review-2-spec_reconciliation.md`, `bld-034-review-3-code_repair.md`, `bld-034-integration.md`, `bld-034-review-4-rationale_correction.md` (all eight read in full, in cycle order)
Status: final-accepted

**Pass shape.** The gate lands no source and no test. Per `docs/builder/BUILD.md` `### Procedural-closure slices` it carries one combined `## Plan (Worker 1)` + `## Final verification (Worker 1)` block; `## Build report (Worker 2)` and `## Review (Worker 3)` are marked not-applicable with that reason.

---

## Plan (Worker 1) + Final verification (Worker 1)

### Spec status-line re-verification (this spawn)

Performed at the top of this spawn and recorded in `docs/builder/bld-034-review-4-rationale_correction.md` `### Spec status-line re-verification (this spawn)`: the spec's title, identity paragraph, `Status:`, `Owner:`, `Predecessors:` and companion-pointer paragraph were read end to end and **none is falsified by anything this cycle did**. No header edit is owed and none was made. Re-confirmed here after R4's edits, since R4 wrote into the file the spec points at: the pointer paragraph still describes the companion accurately.

### The gate, in the order `docs/builder/BUILD.md` `## Final test-run gate` gives

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS — `6913 passed, 42 skipped in 62.03s`**, exit 0 |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS — `System check identified no issues (0 silenced).`**, exit 0 |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS — `No changes detected`**, exit 0 |
| 4 | `uv run ruff format --check .` | **PASS — `434 files already formatted`**, exit 0 |
| 5 | `uv run ruff check .` | **PASS — `All checks passed!`**, exit 0 |
| 6 | `git diff --check` | **PASS — no output**, exit 0 |
| 7 | Floor verification (confirmation, not re-ownership) | **CONFIRMED** — see `### Floor-verification confirmation` |

Real output, quoted as produced:

```shell
$ uv run pytest --no-cov -q
........................................................................ [ 99%]
.........................................                                [100%]
================= 6913 passed, 42 skipped in 62.03s (0:01:02) ==================
# exit 0

$ uv run python examples/fakeshop/manage.py check
System check identified no issues (0 silenced).
# exit 0

$ uv run python examples/fakeshop/manage.py makemigrations --check --dry-run
No changes detected
# exit 0

$ uv run ruff format --check .
warning: The following rule may cause conflicts when used with the formatter: `COM812`. ...
434 files already formatted
# exit 0

$ uv run ruff check .
All checks passed!
# exit 0

$ git diff --check
# no output, exit 0
```

**Zero failures, so no attribution work was owed and none is invented.** The plan's preamble records a pre-flight baseline exception — the tree was **not** clean at pre-flight and is dirty with a concurrent maintainer session's kanban-tooling work (`BACKLOG.md`, `KANBAN.md`, `KANBAN.html`, `README.md`, `examples/fakeshop/db.sqlite3`, `scripts/_kanban_lib.py`, `scripts/build_kanban_html.py`, `scripts/build_kanban_md.py`, `tests/test_build_kanban_html.py`, plus untracked `0_0_14.md` and `docs/DIVERGENCE.md`). That exception **was not needed**: rows 4-6 pass over the whole tree, the concurrent files included. Recorded so a later reader knows the exception was available and went unused rather than assuming it was relied on.

`--no-cov` is the only coverage-shaped flag used anywhere in this pass, and it is required because `pytest.ini`'s `addopts` auto-applies `--cov` (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). **No line coverage was inspected or asserted.**

The two spec-family gates re-run in this spawn under R4 are recorded in that round's artifact and are not re-run here: `check_spec_glossary.py` `OK: 42 terms` exit 0, `check_citations.py` `OK: 857 citations resolve` exit 0, `check_trailing_commas.py --check` exit 0, and 96/96 + 51/51 ref-def parity with 0 unresolved anchors in both files.

### Floor-verification confirmation

The plan declares one floor-verification scope: `examples/fakeshop/test_query/test_products_api.py -k cascade`, owned by **R3's builder pass**. R1, R2, R4 and this gate declare `none` — they land no framework seam. **This gate is the backstop confirming it happened, not a second owner.**

`bld-034-review-3-code_repair.md` `### Floor verification` (the pass-2 record, re-run rather than inherited) carries every field `BUILD.md` `## Floor verification` requires:

- **Scratch venv, outside the repo:** `/tmp/dsf-floor-034`; every install it ever received carried an explicit `--python /tmp/dsf-floor-034/bin/python`.
- **Resolved versions, as read by `uv pip list --python /tmp/dsf-floor-034/bin/python`:** `django 5.2.16`, `strawberry-graphql 0.316.0`, `django-strawberry-framework 0.0.14` (editable), `channels 4.3.2`, `pytest 9.1.1`, `pytest-django 4.14.0`; interpreter `Python 3.10.19`.
- **Focused scope as run:** `/tmp/dsf-floor-034/bin/python -m pytest examples/fakeshop/test_query/test_products_api.py -k cascade --no-cov`
- **Result:** `13 passed`, exit 0, with all four `[allCategories]` / `[allItems]` / `[allProperties]` / `[allEntries]` node ids of both staff tests among the PASSED lines.
- **Shared `.venv` untouched**, verified by R3 after the run.

**The record is complete, so no re-run was owed.** It was corroborated read-only anyway, because a floor claim is exactly the shape `BUILD.md` `## Claims are proven mechanically, never accepted on prose` says to re-derive — and because the versions are the one half of the record that can rot after the fact:

```shell
$ /tmp/dsf-floor-034/bin/python -V
Python 3.10.19
$ uv pip list --python /tmp/dsf-floor-034/bin/python
channels                    4.3.2
django                      5.2.16
django-strawberry-framework 0.0.14   /Users/riordenweber/projects/django-strawberry-framework
pytest                      9.1.1
pytest-django               4.14.0
strawberry-graphql          0.316.0
```

The venv still exists and resolves **exactly** as R3 recorded, at the versions `BUILD.md` `## Floor verification` states canonically. **No install ran in this pass and the shared `.venv` was never written to.**

### Round-status chain, confirmed at the artifacts rather than at the plan

Every artifact's own `Status:` line was read on disk. `bld-034-slice-0-rationale_extraction.md`, `-review-1a-`, `-review-1b-`, `-review-1c-`, `-review-2-`, `-review-3-`, `-integration.md` and `-review-4-` all read `final-accepted`. **No round is left `built`, `review-accepted` or `revision-needed`.** The plan's two open boxes are R4 and this gate; both are now `final-accepted` and their checkboxes are Worker 0's to mark.

### The one decision routed to Worker 0 by the integration pass is closed

`bld-034-integration.md` `### What Worker 0 must decide` offered **(a)** route finding I1 to this catalog as an inherited divergence, or **(b)** dispatch one Worker-1 micro-pass to fix it. **Option (b) was taken:** `bld-034-review-4-rationale_correction.md`, `final-accepted`. I1 is therefore **discharged, not deferred**, and appears in the catalog below only as a closed item — a reader arriving from the integration artifact, which files it as open, needs to be told so in the file that supersedes it.

---

### Deferred work catalog

Assembled by walking **every** per-round and integration artifact's `### Notes for Worker 1 (spec reconciliation)`, `### DRY findings`, `### What looks solid`, `### Review outcome` and `### Deferred work catalog` sections on disk. R2's twelve items were **read out of `bld-034-review-2-spec_reconciliation.md` `### Deferred work catalog`** and the integration pass's four out of `bld-034-integration.md` `### Deferred work catalog — this pass's contribution`, neither restated from a summary. De-duplicated **by item, not by artifact**: each bullet names every artifact section that carries it, so an item two artifacts describe at different line numbers is one bullet and not two, and an item only an earlier artifact carries is not dropped.

**Every population claim below was re-derived in this pass, and three of the inherited descriptions did not survive re-derivation** — recorded in group E. A catalog is a claim.

#### A. Card-id rot — one coupled class, a maintainer decision, not a deferral of convenience

The three surfaces below are **one problem**, and the reason they are stated together is that fixing any one alone makes the set worse. The board's own per-site grading rules four `spec-034` sites **"leave verbatim" precisely because the source still reads the old id**. Renumber the source without the spec and those four rulings become wrong; renumber the spec without the source and the board's stated justification evaporates. The maintainer can act on all three at once; no worker can act on any of them, because the board file that homes the disposition is outside this cycle's maintainer-set scope.

- **A1 — `examples/fakeshop/apps/products/schema.py` carries 18 rotted card-id occurrences beside one that is correct.** Re-derived this pass: `TODO-BETA-046-0.1.1` ×7, `TODO-BETA-047-0.1.2` ×5, `TODO-BETA-049-0.1.3` ×6, and `TODO-BETA-062-0.1.5` ×1 — **the last must not be swept**; card 062 is still To Do under exactly that id. Live referents for the other three: `TODO-BETA-055-0.1.1` / `TODO-BETA-056-0.1.2` / `TODO-BETA-058-0.1.3`. Carried by: `bld-034-review-1c-fakeshop_and_surface.md` census G-iii + finding M2 (which found it, "NEW, unowned"), `bld-034-review-2-…` catalog, `bld-034-review-3-code_repair.md` `### Notes for Worker 1` (confirming the file is byte-identical to `HEAD` after every transient proof), `bld-034-integration.md` pre-condition 6. Licensed by: the build plan's `## R1 outcome` maintainer escalation. **A blanket sweep is the wrong fix** — an undifferentiated `TODO-` rewrite over this file destroys the one correct id.
- **A2 — `spec-034` itself carries 10 card-id occurrences in 4 spellings, deliberately frozen by the same escalation.** Re-derived this pass: `TODO-ALPHA-034-0.0.10` ×6, `TODO-BETA-046-0.1.1` ×2, `TODO-ALPHA-035-0.0.10` ×1, `TODO-ALPHA-033-0.0.10` ×1 — **byte-identical across R2, R3, R4 and this gate**, which is what the escalation required. Carried by: `bld-034-slice-0-…` `### Notes for Worker 1` (three populations, unverified), `bld-034-review-1a-…` out-of-territory note, `bld-034-review-1c-…` census G-i (which grades them per site: two quote `docs/TREE.md`'s superseded predicted-path row and stay verbatim, one is a card-wrap instruction true only in its own tense and needs de-tensing, three are live-claim sites), `bld-034-review-2-…` catalog, `bld-034-integration.md` pre-condition 6. **The per-site grading is the ruling to apply, and applying it needs A1 to move in the same pass.**
- **A3 — the rationale companion's 15 card-id occurrences in 6 spellings are all decided-non-edit history, and that class is now closed by measurement rather than by assumption.** Re-derived this pass, unchanged by R4: `TODO-ALPHA-027` ×2, `TODO-ALPHA-027-0.0.10` ×2, `TODO-ALPHA-033-0.0.10` ×2, `TODO-ALPHA-034-0.0.10` ×5, `TODO-ALPHA-035-0.0.10` ×1, `TODO-BETA-046-0.1.1` ×3. Every one sits inside a `- **Revision N**` history bullet, a `### Changes this Decision underwent` entry, or the Risks body's own record of a stale-id finding — true as history at the date each records. The `TODO-ALPHA-027-0.0.10` pair is the sharpest and is *deliberately* preserved: it records an incoming review that **claimed** the fakeshop hooks carried that marker and the verification that found they already read `034`. Carried by: `bld-034-integration.md` pre-condition 6 ("one population no pass enumerated"); partially by `bld-034-review-1c-…` census G-ii, which enumerated **three of the fifteen**, and by R2, whose post-round measurement was explicitly spec-only. **Nothing to fix.** Listed because an unmeasured population reads exactly like an empty one.

#### B. Board citations — one this cycle caused, one whose board-side half no longer reads as recorded

- **B1 — three `KANBAN.md` citations into `spec-034` dangle, and Slice 0's rationale move is what broke them.** Said plainly rather than filed as inherited: **this cycle caused it.** The board item cites `#"but the live kanban card is"`, `#"Stale card-id reference in \`TODAY.md\`"` and `#"so \`<NNN>\` is"` against the spec; all three sentences moved into `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` in Slice 0. Re-derived this pass, each substring counted in both files: **spec 0 / companion 1, all three.** The repair is a path swap in the board item, not a reword — the sentences themselves are intact and unedited. Carried by: `bld-034-review-1c-…` (which found the first), `bld-034-review-2-…` catalog before/after sweep (which found the other two), `bld-034-integration.md` catalog. **No gate can see this class** — `scripts/check_citations.py` resolves `path::Symbol` in `.py` files and `KANBAN.md` only, so a `path #"substring"` citation into a `docs/` file is invisible to it, which is exactly why it needs a human. `KANBAN.md` is outside this cycle's maintainer-set scope, so no worker may fix it.
- **B2 — the `scalar-only` item: the surviving spec occurrence is real and already homed; the board claim R2 quoted is not findable at `HEAD`.** R2's catalog records `KANBAN.md`'s claim that `spec-034` "no longer carries `scalar-only` anywhere and is DISCHARGED" as **false**. Re-derived in two halves. **The spec half holds exactly:** `grep -c 'scalar-only' docs/SPECS/spec-034-permissions-0_0_10.md` returns **1**, in the `## Edge cases` non-nullable-forward-FK bullet, and it is character-for-character the substring `docs/builder/DONE/build-029-consumer_dx_cleanup-0_0_9.md`:324 cites — `docs/SPECS/spec-034-permissions-0_0_10.md #"is scalar-only (spec-029 Decision 10)"` — whose row records that the conclusion still holds but the cited Decision was renamed (`Scalar-only scope` → `Non-relation scope`) and **homes the item on `TODO-ALPHA-052`.** So the surviving occurrence has an owner. **The board half does not reproduce:** at `HEAD` no `KANBAN.md` line makes that claim — `DISCHARGED` occurs 4 times and `no longer carries` 4 times, none of them about `spec-034` and `scalar-only`. `KANBAN.md` is baseline-dirty and being actively rewritten by the concurrent session, so either it has since been removed or R2 read a region that has since been rewritten; **which of the two is not determinable from inside this cycle**, and the board is a file no worker here may read as settled or write to. **Maintainer action: confirm against the board once the concurrent kanban work lands.** Carried by: `bld-034-review-2-…` catalog, `bld-034-integration.md` catalog.

#### C. Source-side items the cohorts escalated rather than dispatched

- **C1 — a catalogued fail-open shape with no live exploit path.** `django_strawberry_framework/permissions.py::_is_unsupported_forward_edge #"getattr(field, \"is_relation\", False)"` is a `getattr`-default on the walk's fail-closed-vs-skip decision — `BUILD.md` `### Fail-open shapes`' catalogued form, filed Medium by `bld-034-review-1a-…` finding M1. Unreachable at `HEAD`: the only caller is `::_edge_plan`, whose sole input is `model._meta.get_fields()`, every member of which defines `is_relation` as a class attribute — and the two predicates beside it on the same line use plain attribute access, so the one `getattr` is inconsistent with its own line. Resolution paths R1a recorded: **(a)** read `field.is_relation` directly so an unanswerable shape raises rather than being silently classified a non-relation; **(b)** leave it and record the closed-population argument in the docstring so a later reader does not "fix" it into a real fallback. Carried by: `bld-034-review-1a-…` M1 + `### Notes for Worker 1`, `bld-034-review-2-…` catalog.
- **C2 — `permissions.py::_cascadable_edges` / `::_cascadable_edge_names` are dead production code, so the fix is a deletion and not an extraction.** Raised as an existence challenge (`bld-034-review-1a-…` DRY D1), decided by nobody. Reader counts re-derived independently twice — by `bld-034-integration.md` `### Consolidation candidates` and again here: `_cascadable_edges` has **one** reader (`_cascadable_edge_names`) and `_cascadable_edge_names` has **zero production readers** (one import + three call sites, all in `tests/test_permissions.py`). Every production path — `_validate_fields`, the preflight, `_walk` — calls `_edge_plan(model)` directly. R1a's paths: **(a)** delete `_cascadable_edges` and inline `_edge_plan(model).cascadable`; **(b)** delete both and let the three test sites read the plan directly, as `tests/test_permissions.py` already does elsewhere; **(c)** keep both as documented test seams. **Low value; should gate nothing.** Note for whoever takes it: R4's Decision 5 `**Post-ship:**` bullet now records *why* the pair is vestigial — `c68aecab` moved every production reader onto `_edge_plan`.
- **C3 — the `view_<model>` branch is dead in all four fakeshop hooks, and collapsing it is a contract decision.** Each hook's `elif user and user.has_perm("products.view_<model>")` branch is the same expression as the fall-through it precedes, so it cannot change the result, and it costs a permission-table read per request per type (`bld-034-review-1c-…` finding M1, escalated as contract-level). It is **spec-conformant** — Slice 4 box 1 and Decision 6's consumer-recipe divergence both demand it. Paths: **(a)** keep and record in the spec *why* the redundant branch exists; **(b)** collapse each hook and add a spec sentence saying the grant is deliberately not a branch; **(c)** give the branch different behaviour, which reverses Decision 6's recorded divergence and is the maintainer's call alone. **R3 deliberately preserved the ordering constraint R1c named:** the staff rows are now on disk, and T2 asserts the `view_<model>` actor explicitly for all four models, so a collapse would now be performed against a suite that can detect a mistake in it. Carried by: `bld-034-review-1c-…` M1 + `### Notes for Worker 1`, `bld-034-review-2-…` catalog, `bld-034-review-3-…` `### Notes for Worker 1`.

#### D. Coverage and doc obligations outside this cycle's reach

- **D1 — the prefetch-child alias behaviour is described in a standing doc and asserted by nothing.** `bld-034-review-1b-…` finding L2: `tests/optimizer/test_multi_db.py` has zero `cascad` occurrences and no `FAKESHOP_SHARDED`-gated file exercises the cascade inside a prefetch child. **Not a SKIPPED contract** — the spec claims no pin for that bullet — but a future `FAKESHOP_SHARDED`-gated row asserting the prefetch child's `.db` would close it. Carried by: `bld-034-review-1b-…` L2 + `### Notes for Worker 1`, `bld-034-review-2-…` catalog.
- **D2 — `examples/fakeshop/apps/products/services.py::seed_cascade_split` has no per-app test.** Every other public helper in the module is covered. Example apps sit outside the `fail_under` gate, so this is a test-surface asymmetry, not a coverage gap. Carried by: `bld-034-review-1c-…` finding L1, `bld-034-review-2-…` catalog.
- **D3 — a one-clause docstring imprecision in `utils/querysets.py::_seal_or_defect`.** It says "The cascade (`require_model_rows=False`) keeps its own slice rejection in `permissions.py::_validated_target_subquery`" — true for the **hook return**; the **root** slice rejection lives in `permissions.py::_validate_root_queryset`. Corroborated independently by `bld-034-integration.md` `### Cross-cohort seam` 2, which reached the same split from the other direction. In a source file no cohort had territory over. Carried by: `bld-034-review-1a-…` out-of-territory note, `bld-034-review-2-…` catalog.
- **D4 — `docs/README.md`'s "Coming next `0.0.10`" line is not re-derivable at `HEAD`**, and was graded SUPERSEDED by four later cuts rather than as a `034` gap. Recorded so a later reader does not re-open it as a missed doc obligation of this card. Carried by: `bld-034-review-1c-…` census E7, `bld-034-review-2-…` catalog.
- **D5 — the `KANBAN.md` M2M / reverse-relation cascade follow-up surfacing cannot be established or performed here.** The spec's `## Doc updates` Slice 5 obligates surfacing the missing follow-up card to the maintainer; R1c could not establish whether it happened, and board edits are outside the cycle's maintainer-set scope. The spec's `## Non-goals` and `## Out of scope` both still say no follow-up card exists. Carried by: `bld-034-review-1c-…` census E15, `bld-034-review-2-…` catalog. Related deliberation, for whoever picks it up: the rationale companion's `## Risks and open questions` **M2M / reverse-relation cascade has no follow-up card** item states the two-question card body (hide the parent vs. narrow the list) the maintainer would need.

#### E. Corrections to the cycle's own record — recorded, not open work

`docs/builder/ARTIFACT.md` forbids editing a prior artifact entry and the build plan is Worker 0's file, so none of these could be fixed at its source. They are carried here because this is the file a later reader ends at.

- **E1 — `**Post-ship:**` bullet count: "14 under 11 Decisions plus 6" is wrong; it is 19 under 10 Decisions plus 6 = 25.** Stated in `bld-034-review-2-…` `### Summary` and copied into the build plan's `## R2 outcome`. Re-derived by `bld-034-integration.md` `### Spec ⇄ rationale coherence` by enumerating every indent-0 `- **Post-ship…` bullet and attributing each to its enclosing section: Decisions 1, 3, 6, 11 one each; 7, 8, 9, 12 two each; 10 three; 5 four; plus 6 under `## Non-Decision deliberation`. Decisions 2, 4 and 13 carry none. **The `11` is right in its digits and wrong in its subject** — it counts *sections carrying bullets* (10 Decisions + the non-Decision section), not Decisions. **R4 adds two bullets**, so the figure at `HEAD` is now **20 under 10 Decisions plus 7 = 27**. The file was always correct; only the number describing it was wrong.
- **E2 — `bld-034-review-1b-…` census rows S2-4 and S2-5 cite `permissions.py::_cascade_edges`, a symbol that does not exist.** The live symbol is `permissions.py::_walk`, which R1a cites correctly throughout. The cited *substring* is real and lives in `_walk`, so the evidence stands and the CONFORMS grades are sound; only the symbol name is wrong. **Contained** — `grep -rn '_cascade_edges' --include='*.md' .` returns exactly those two lines and nothing in either spec-family file. Found by `bld-034-integration.md` `### Finding I2`; two cohorts naming one function differently is a cross-cohort seam only a cross-cohort read reaches.
- **E3 — the `_edge_plan` memo's attribution: the integration pass named `c68aecab`; the memo actually first shipped at `bc1a6aaf`, a month earlier.** Re-derived by R4 rather than inherited (`bld-034-review-4-rationale_correction.md` `### The finding re-derived at source`): `git log -S'_edge_plan'` returns `c68aecab` alone, but `git log -S'lru_cache'` over the same file returns `bc1a6aaf` (2026-06-15), which put `@lru_cache(maxsize=1024)` on a new `_cascadable_edges` and rewrote `_walk` to iterate it; `c68aecab` (2026-07-16) widened that memo into `_edge_plan`. `bc1a6aaf` is an ancestor of `c68aecab`. The correction matters beyond tidiness: `bc1a6aaf` landed **the same day as the card's final review revision**, so the deliberation's "deferred" fallback was already false when the spec closed, not four releases later. **The shipped record carries the corrected attribution** — only the integration artifact's prose carries the older one.
- **E4 — three prose-only Lows R3 recorded rather than fixed.** From `bld-034-review-3-code_repair.md` `### Notes for Worker 1`: **L1** the pass-1 build report's stated reason for dropping a shipped trailing assertion is wrong (the correct reason is "not generalizable to the parametrized `model`"; the drop itself is right); **L2** the plan's prediction that repeated literals would fall was falsified at `+1` per root field, because `pytest.param("x", …, id="x")` writes the name twice — it changes nothing about the constant's justification; **L3** the pass-2 report's stated obstacle to annotating the helper's parameter does not hold (`from django.db.models import Model` binds `Model`; there is no collision), though the choice it defends is right on the per-file-`ANN`-ignore ground. All three are sustained corrections, not re-openable defects.
- **E5 — Slice 0's link-definition-ordering note is half wrong, re-derived here.** `bld-034-slice-0-…` `### Notes for Worker 1` flags two out-of-alphabetical-order definitions in the spec, "flagged only so a later pass does not attribute it to the move". Measured: **one is real** — under `<!-- django_strawberry_framework/ -->`, `[definition]` sits after `[types-base]` instead of after `[connection]`. **The other is not** — under `<!-- docs/ -->`, `[glossary]` correctly precedes `[glossary-aggregateset]`, which is alphabetical order; that group is sorted throughout. Both predate the move (Slice 0 confirmed against the pre-move copy) and `scripts/check_trailing_commas.py --check` accepts the file, since its scaffold fixer slots definitions per category without re-sorting within one. **Cosmetic; nobody's blocker.** Listed because it is an item **only the cycle's earliest artifact carries** and re-deriving it is what showed half of it was never true — the `033` cycle recorded both halves of exactly this lesson.

#### F. A standing observation for whichever card next touches the products models

- **F1 — the staff rows' page expectation is coupled to the connection's default `ORDER BY`, and that coupling now has exactly one home.** `examples/fakeshop/test_query/test_products_api.py::_cascade_page_gids` derives its expectation from `order_by("pk")` capped at `_RELAY_MAX_RESULTS`, which is sound today by contract: `optimizer/plans.py::deterministic_order` resolves to `("id",)` with no `Meta.ordering` on any products model and no keyset target. **If a later card gives any of the four products models a `Meta.ordering`, all eight staff rows go red for an ordering reason rather than a permission one.** After R3's consolidation that coupling lives in one expression and one docstring, so the future fix is a one-site edit. Carried by: `bld-034-review-3-…` `### Notes for Worker 1`, and by no other artifact — this is the second item in the catalog that only one artifact carries.

#### Closed by this cycle, listed so a reader arriving from an earlier artifact is not misled

- **Integration finding I1 — the shipped-not-deferred per-model edge memo — is DISCHARGED, not deferred.** `bld-034-integration.md` files it as an open decision for Worker 0 and `docs/builder/build-034-permissions-0_0_10.md` lists R4 as unbuilt; both predate `bld-034-review-4-rationale_correction.md`, which took option (b) and is `final-accepted`. All three sites now state what shipped: the Risks item's cost premise and its fallback are corrected in place naming `permissions.py::_edge_plan`, Decision 5's rejected alternative 4 keeps its text and gains a `**Post-ship:**` bullet recording the adoption and which premise of the rejection gave way, and a fourth bullet under `## Non-Decision deliberation` records the Risks correction. **The spec was not touched and is still narration-free** — `Post-ship` / `post-ship` / `Revision ` / `as of review` / `later changed` / `amendment` all measure **0** occurrences in it after R4.

**The catalog holds 19 bullets**, of which 12 are R2's re-confirmed items, 4 come from the integration pass, 2 are carried by exactly one artifact each and would have been lost by assembling from the most recent artifact alone (E5 from Slice 0, F1 from R3), and 1 is new to this gate (E3). Seven bullets (A1, A2, B1, B2, C1, C2, C3) are maintainer decisions; five (D1-D5) are future-slice or future-card work; five (E1-E5) are recorded corrections that close with this cycle; one (A3) is closed by measurement; one (F1) is a forward-looking coupling note.

### Final status

`final-accepted`. Every gate command passes with zero failures, so nothing routes back through an owning round's loop. The floor verification the plan scoped was run by its declared owner and its record carries every required field, corroborated read-only here. All eight prior artifacts read `final-accepted`. The catalog is assembled from every artifact rather than the newest, and the three claims it inherited that did not survive re-derivation are corrected in place rather than propagated.

### Spec changes made (Worker 1 only)

**None by this pass.** The gate edits no spec-family file. R4's four edits to `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` are recorded under `docs/builder/bld-034-review-4-rationale_correction.md` `### Spec changes made (Worker 1 only)`; `docs/SPECS/spec-034-permissions-0_0_10.md` was not written to by R4, by the integration pass, or by this gate — its last write is R3's final verification.

---

## Build report (Worker 2)

Not applicable. `docs/builder/BUILD.md` `### Procedural-closure slices`: the final gate lands no source and no tests. There is no `### Files touched` beyond this artifact, no `### Failability proofs` (no boundary introduced), no `### Hot-path budget` (the plan declares none for every pass after R1 and no executable byte changes here), and no `### Floor verification` **owned** by this pass — R3's builder pass owns the cycle's single floor run and this gate is its declared backstop. The gate's own `ruff` invocations are the read-only `--check` forms in the table above; **no `--fix` and no write-mode formatting ran.**

---

## Review (Worker 3)

Not applicable, same reason. `docs/builder/BUILD.md` `### Isolation is non-waivable` binds the builder/reviewer pair over a **source diff**; there is none. What stands in place of a second reader is that every command above is quoted with its real output and is re-runnable, and that every inherited claim in the catalog was re-derived rather than carried — which is how B2's board half, E3's attribution and E5's half-false note were caught.

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
