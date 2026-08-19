# Package build plan: multi_db / 0.0.7 (023)

Spec source: `docs/SPECS/spec-023-multi_db-0_0_7.md` (already archived; the active-spec path `docs/spec-023-multi_db-0_0_7.md` no longer exists)
Target release: `0.0.7` (shipped; tag `0.0.7` at commit `72f6cd9`)
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Ownership partition: none; sequential slices. Worker 1 is the sole writing role in this cycle.
Hot-path declaration: none. No production code is planned; nothing runs per request, per resolver, or per row.
Floor-verification scope: none. No slice touches a Django / Strawberry / channels integration seam; the cycle writes Markdown only.
Pre-flight: passed on 2026-08-18 with two recorded deviations (below); baseline: DIRTY with a concurrent session's work.

## Cycle shape — residual reconciliation, not a fresh build

`DONE-023-0.0.7` shipped inside the `0.0.7` joint cut. Worker 0 verified every Definition-of-done item against HEAD before writing this plan (evidence in `## Pre-dispatch verification` below): **nothing was skipped in the code.** All six package-internal tests, both live `/graphql/` tests, and every Slice 3 doc edit landed under the spec-pinned names.

What did NOT land is the spec's `-rationale.md` sibling, and the spec has since drifted from HEAD because later cards changed surfaces it makes factual claims about. So this cycle has exactly two units of work, both Markdown, both Worker 1's:

1. The rationale MOVE that `docs/builder/BUILD.md` `## Spec rationale extraction` requires (pre-flight step 7, deferred into Slice 1 because the extraction IS this cycle's work rather than its precondition).
2. Spec reconciliation: rewrite every drifted claim so the spec states the CURRENT contract directly, with no chronology. Every change is recorded in the rationale file, never in the spec.

Per the maintainer's dispatch instruction, Workers 2 and 3 are dispatched only if a slice turns out to need a **code** change. Nothing found so far does.

## Pre-flight outcome and deviations

- Step 1 (baseline): DIRTY. Another session is mid-cycle on `spec-021` / `spec-022` (its `worker-memory/worker-1.md` was written 2026-08-18 19:37, during this pre-flight). Baseline-dirty out-of-scope files are listed below.
- Step 2 (`scripts/review_inspect.py`): smoke run on `django_strawberry_framework/types/resolvers.py` exited 0.
- Step 3 (artifact reset): **DEVIATION — old `bld-*.md` / `build-*.md` were NOT deleted.** `bld-003-final.md`, `bld-final.md`, `bld-final-022.md`, `bld-integration.md`, `bld-integration-022.md`, four `bld-review-*.md`, `build-021-apps-0_0_7.md`, and `build-022-export_schema-0_0_7.md` are the concurrent session's live record. Deleting them is the one irreversible pre-flight mistake and `AGENTS.md` rule 34 forbids reverting concurrent work. This cycle therefore uses `-023`-suffixed artifact paths, verified absent.
- Step 4 (`.gitignore`): `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/` all listed.
- Step 5 (scratch cleared): **DEVIATION — scratch was NOT cleared**, same reason as step 3. `worker-memory/worker-1.md` is the concurrent cycle's live notebook. This cycle's Worker 1 writes `docs/builder/worker-memory/worker-1-023.md` instead, which Worker 0 created empty.
- Step 6 (`check_spec_glossary`): `OK: 18 terms - all have glossary entries and at least one spec link.` (exit 0).
- Step 7 (rationale extraction): NOT yet done — it is Slice 1 of this cycle.

### Baseline-dirty out-of-scope files (never edit, never revert)

`KANBAN.html`, `KANBAN.md`, `docs/GLOSSARY.md`, `docs/SPECS/spec-021-apps-0_0_7.md`, `docs/SPECS/spec-022-export_schema-0_0_7.md`, `docs/builder/build-020-list_field-0_0_7.md` (deleted by the other session), `docs/feedback.md`, `examples/fakeshop/db.sqlite3`, `tests/test_apps.py`, every untracked `docs/SPECS/appx/spec-021-*-rationale.md` / `spec-022-*-rationale.md`, `docs/builder/DONE/`, and every artifact listed under step 3.

**Concurrent-writable tracked binary / generated files:** `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`. This cycle plans NO edit to any of them, so any churn observed in them is the other session's and must be left alone.

## Pre-dispatch verification (Worker 0, against HEAD)

Every Definition-of-done item read against source before dispatch. Findings are handed to Worker 1 as verified inputs, not as hypotheses.

### Delivered in full — no code gap

| DoD | Verified at | Result |
| --- | --- | --- |
| 2 — five resolver-level tests | `tests/types/test_resolvers.py` | all five present under the spec-pinned names (`test_fk_id_elision_stub_sets_state_db_via_router_db_for_read`, `..._router_call_passes_parent_row_as_instance`, `..._router_call_passes_none_instance_when_parent_lacks_state`, `..._returns_none_for_null_fk_and_does_not_call_router`, `test_strictness_check_is_connection_agnostic_under_non_default_alias`) |
| 2 — one optimizer-plan test | `tests/optimizer/test_multi_db.py` | present; exactly one `def test_` (`test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias`), no `parametrize` |
| 3 — two live tests + module skip | `examples/fakeshop/test_query/test_multi_db.py` | both spec-pinned tests present; module-level `pytest.skip(..., allow_module_level=True)` gate, holder-pattern URLConf, `_build_test_schema` fixture, `_seed_book_chain` all present as pinned |
| 4 — fakeshop schemas unmodified | `apps/library/schema.py`, `apps/products/schema.py` | no `.using(` routing decoration |
| 5 — additive `DATABASES` | `examples/fakeshop/config/settings.py` | `FAKESHOP_SHARDED == "1"` ADDS `shard_b`; `db_shard_b.sqlite3` committed |
| 6 / 7 / 8 — no production change, `__all__` unchanged | `django_strawberry_framework/` | the card's own commit added no package source |
| 10 — GLOSSARY flip | `docs/GLOSSARY.md` index row + `## Multi-database cooperation` | `shipped (0.0.7)` with the four narrowed-axis bullets verbatim |
| 11 — `docs/README.md` forward-pointer | `### Sharded mode (multi-DB)` | additive-layout prose + the four-axis pointer to the GLOSSARY anchor |
| 13 — KANBAN Done card | `KANBAN.md` | `DONE-023-0.0.7 - Multi-database cooperation contract`, spec link resolves |
| 14 — CHANGELOG | `CHANGELOG.md` `[0.0.7]` `### Added` | the pinned bullet is present; no second `[0.0.7]` heading |

The four contract axes still hold at HEAD:

- **Axis 1** — `django_strawberry_framework/types/resolvers.py::_build_fk_id_stub` #"state.db = router.db_for_read" still runs `state.db = router.db_for_read(field_meta.related_model, instance=instance)` with `instance = root if hasattr(root, "_state") else None`.
- **Axis 2** — `django_strawberry_framework/optimizer/plans.py::OptimizationPlan.apply` applies only `only()` / `select_related()` / `prefetch_related()`, all `_db`-preserving.
- **Axis 3 (plan-construction time)** — `django_strawberry_framework/optimizer/walker.py::_build_child_queryset` still starts from `field.related_model._default_manager.all()`.
- **Axis 4** — `_state.db` appears exactly once in `types/resolvers.py` (the axis-1 line); `_check_n1` does not read it.

### Drifted spec claims Worker 1 must reconcile (verified, with the cause)

Each is a claim the spec makes that is FALSE or incomplete at HEAD. None is a code defect; each is later work the spec never absorbed.

- **D1 — the single-hit grep is dead.** `## Current state` bullet 1 and `### Decision 2 — No production code change` both assert `router.db_for_read` at `_build_fk_id_stub` is "the package's only explicit `router.db_for_read` call", citing a grep "returning that single hit". At HEAD `db_for_read` / `db_for_write` are also called at `utils/permissions.py #"aliases = {router.db_for_read(model)"`, `utils/write_transaction.py::...` #"return router.db_for_write(model)", and `utils/write_transaction.py #"instance_alias = router.db_for_write(model, instance=instance)"`; `.using(` appears across `permissions.py`, `relay.py`, `filters/sets.py`, `types/resolvers.py`, `optimizer/predicates.py`, `optimizer/single_parent_fetch.py`, `mutations/resolvers.py`, `utils/querysets.py`, `utils/write_transaction.py`, `rest_framework/resolvers.py`. Cause: the `0.0.11`-`0.0.14` write family and the visibility-boundary hardening. The claim was true when written and is a per-card scope statement, so the fix is to scope it to the card's own moment rather than to delete the contract it justifies.
- **D2 — axis 3's "generated child querysets do NOT inherit the root alias" is now time-qualified.** Still true at plan-construction (`_build_child_queryset`), but the later nested-connection machinery threads the parent alias at FETCH time: `optimizer/single_parent_fetch.py #"child_qs = spec.pristine_child_queryset.using(queryset.db)"`, the alias-late note at `optimizer/nested_planner.py #"correct alias-late predicate at fetch time"`, and `filters/sets.py #"child_manager.using(parent_db).all()"`. The spec states the boundary flatly in `### Decision 3` axis 3, `## Edge cases and constraints`, `## Risks and open questions`, and `## Out of scope`.
- **D3 — `plan_optimizations` signature.** The `## Edge cases and constraints` bullet pins `plan_optimizations(selected_fields, model, info=None, *, source_type=None)`. HEAD carries an additional keyword-only `runtime_prefixes` (`optimizer/walker.py::plan_optimizations`).
- **D4 — `RelationKind` membership.** The `## Test plan` test-(e) entry quotes `RelationKind` as the four-member literal and `MANY_SIDE_RELATION_KINDS` as `{"many", "reverse_many_to_one"}`. HEAD adds `"generic"` to both (`utils/relations.py #"RelationKind: TypeAlias"`, `#"MANY_SIDE_RELATION_KINDS"`). The spec's conclusion (`"forward_single"` is the right kind, `"many_to_one"` is not a member) survives; the quoted membership does not.
- **D5 — `_build_fk_id_stub` gained an earlier exit.** The `## Edge cases and constraints` null-FK bullet says the router call "only runs when `related_id is not None`". HEAD adds a prior `_FK_ELISION_UNSAFE` return when `field_meta.attname` is deferred (`types/resolvers.py::_build_fk_id_stub`), so there are now two pre-router exits, and the rejected alternative in `### Decision 2` calling the body "six lines" is stale.
- **D6 — resolver-level alias preservation is undocumented.** `types/resolvers.py::_visible_related_object` #"source = source.using(alias)" re-pins a relation visibility re-check onto the related row's own `_state.db`. That is cooperation behavior inside the contract's subject matter that postdates the spec and appears nowhere in it.
- **D7 — the live test file is no longer two tests.** `examples/fakeshop/test_query/test_multi_db.py` now holds ten tests (debug-extension alias capture, row-preserving predicates on `shard_b`, and the `0.0.14` model- and serializer-flavor write-alias pinning suites). `### Decision 6`'s pinned import header (rev5 X4: "only `DjangoOptimizerExtension` is imported from the package") and DoD item 3's exhaustive reading are both stale.
- **D8 — `test_library_api.py` is not the only `test_query/` file.** `### Decision 7`'s justification rests on that being true; there are 22 modules in the tree now, and `examples/fakeshop/test_query/conftest.py` exists, which is the exact conftest-extraction the Decision deferred.
- **D9 — counts in `## Current state`.** "`tests/optimizer/` ships seven test modules today" — 17 now. `pyproject.toml` / `__version__` / `tests/base/test_init.py` pinned at `0.0.6` — all `0.0.14` now.
- **D10 — `### Decision 9` calls `DONE-025-0.0.7` "still in flight".** The whole `0.0.7` cut shipped 2026-05-27 with seven cards (`KANBAN.md` #"0.0.7` shipped 2026-05-27"), tag `0.0.7` at `72f6cd9`.
- **D11 — the archive already happened.** `### Decision 1`'s lifecycle note and `## Goals` item 1 / DoD item 1 still speak of the spec as active at `docs/spec-023-multi_db-0_0_7.md`. It lives at `docs/SPECS/spec-023-multi_db-0_0_7.md` and its terms CSV at `docs/SPECS/appx/`; the link-definition block is already re-relativized, so only the prose lags.
- **D12 — one surviving letter drift of the rev5 X1 class.** `## Risks and open questions` #"the test in Slice 1 (g) sets `root._state.db`" still cites (g); the strictness test is (e) in the post-relocation numbering, which rev5 X1 fixed in `### Decision 3` and X2 / X3 fixed in two other bullets.
- **D13 — the spec narrates its own history.** Lines 8-51 are a five-revision changelog, the `Status:` line advertises it as "preserved for archaeology", and rev-annotations (`rev2 H2`, `rev3 R4`, `rev5-post X7`, …) are threaded through nearly every section. `docs/builder/BUILD.md` `## Spec rationale extraction` is explicit that this layer MOVES and that the spec must read as a clean current contract.

Worker 1 owns whether each of D1-D13 is a spec edit, a rationale entry, or both. The one rule Worker 0 fixes: **no explanation of any change may appear in the spec.** Corrected text states the contract as though it had always been right; the what/why/when goes in `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md`.

## Artifact list

- `docs/builder/bld-slice-1-023-rationale_extraction.md` — DELETED at closeout
- `docs/builder/bld-slice-2-023-spec_reconciliation.md` — DELETED at closeout
- `docs/builder/bld-integration-023.md` — DELETED at closeout
- `docs/builder/bld-final-023.md` — DELETED at closeout

All four are per-cycle scratchpads and were deleted after the work committed at `f466863a`; they are recoverable from that commit (`git show f466863a:<path>`). Every load-bearing measurement they carried is folded into `## Final gate record` below, so no statement in this plan depends on reading them. Citations to them elsewhere in this file are records of what the cycle produced, not live pointers.

## Checklist

- [x] Slice 1: Rationale extraction — MOVE the deliberative layer out of `docs/SPECS/spec-023-multi_db-0_0_7.md` into `docs/SPECS/appx/spec-023-multi_db-0_0_7-rationale.md` -> `docs/builder/bld-slice-1-023-rationale_extraction.md`
- [x] Slice 2: Spec reconciliation — rewrite D1-D13 so the spec states the current contract, recording each change in the rationale -> `docs/builder/bld-slice-2-023-spec_reconciliation.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration-023.md`
- [x] Final gate -> `docs/builder/bld-final-023.md`

## Final gate record

Folded out of `docs/builder/bld-final-023.md` before that artifact was deleted. These are the four things it carried that exist nowhere else; the rest of it duplicated this plan, was already carded, or described a tree state that has since moved.

### Gate commands, as run

| # | Command | Result |
|---|---|---|
| 1 | `uv run ruff format --check .` | PASS — `424 files already formatted`, exit 0 |
| 2 | `uv run ruff check .` | PASS — `All checks passed!`, exit 0 |
| 3 | `git diff --check` | PASS — no output, exit 0, across this cycle's files and the concurrent session's |
| 4 | `uv run python scripts/check_trailing_commas.py --check` | FAIL repo-wide on ONE violation, attributed below; PASS scoped |
| 5 | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-023-multi_db-0_0_7.md` | PASS — `OK: 18 terms - all have glossary entries and at least one spec link.`, exit 0 |

Command 4 scoped twice, and both are the runs that actually cover this cycle: over every tracked candidate (`$(git ls-files '*.md' '*.py' '*.csv')`, **859 files**) -> exit **0**; over the cycle's own diff -> exit **0**. Ruff is Python-only and this diff is Markdown and CSV, so command 4 is the only lint that reads the diff at all.

The single repo-wide violation is a **git-ignored non-repository file** — an agent's local auto-memory topic file under `.claude/`, untracked, matched by `.gitignore:170`, with an mtime four days before this cycle. The checker's directory walk does not consult `.gitignore`. Attributed, not fixed. This is a known false red already carded on `TODO-ALPHA-052-0.1.0`, which owns teaching the walker to skip ignored paths or declaring the script scoped-run-only.

### Commands deliberately NOT run, and the authority

Decided answers, not omissions. `uv run pytest --no-cov`, `examples/fakeshop/manage.py check`, and `makemigrations --check --dry-run` were all skipped: `AGENTS.md` #"No pytest after edits" governs, `docs/builder/worker-1.md` `## Required reading` says an instruction conflicting with `AGENTS.md` or `START.md` loses, and `START.md` names all three in one breath. **`docs/builder/BUILD.md`'s gate is the conflicting instruction and it loses.** Independently of precedence, the diff contains zero Python, so no test's behaviour is reachable from it and a green sweep would have been evidence about the concurrent session's tree rather than this build. No `--cov*` flag was passed by any pass in the cycle.

### The rationale MOVE, proved mechanically

The cycle's central act is Slice 1's claim that the deliberative layer was **moved**, not copied and not summarized, and `docs/builder/worker-1.md` requires the claim be proved rather than accepted. Measured at the integration pass over the spec / rationale pair: exact long-sentence overlap **0**, and the longest shared word-shingle run **33 words**, each one read and accounted for as a link-definition tail, a quoted out-of-scope enumeration, or a short mechanism restatement the rationale needs verbatim. Text that landed in the rationale left the spec. Slice 1's mechanism is consistent with the measurement — its cut script captured each excised block to JSON and deleted it in the same run, so no block was retyped and none could survive in both files.

### Postcondition measurements on the spec / rationale pair

Re-verified at the gate rather than accepted from the integration pass:

- Anchors and references, both files: in-page unresolved **none**, used-not-defined **none**, defined-not-used **none**; **0** missing definition paths; **0** broken cross-file `#fragment`.
- Duplicate link-definition targets: **0** in both files (7 in the rationale before the integration pass fixed them).
- `#"substring"` citations: spec **47**, **0** broken. Rationale **22**, **1** broken — the dead `KANBAN.md` locator homed on `TODO-ALPHA-052-0.1.0` above.
- `grep -oE 'rev[0-9]'`: **0** in the spec, **0** in the terms CSV (202 in the spec before Slice 1).
- `four axes` **6** occurrences; `five axes` / `fifth axis` **0**. The framing the shipped GLOSSARY and CHANGELOG share survived the reconciliation.
- `grep -oE '\([a-g]\)'` in the spec: **40** occurrences, `(g)` **0**, all resolving to the six-test a-f layout.
- Staged anchors naming this build (`TODO(spec-023`, `TODO-(ALPHA|BETA|STABLE)-023`): **0 lines** repo-wide, before any exclusion.

### Closeout

Not performed, by maintainer instruction: no edit to `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, or any `docs/builder/worker-*.md` role file; no retrospective; no KANBAN or CHANGELOG movement.

## Deferred-work homing

The final gate catalogued three deferrals, restated in full below; a fourth was measured after that gate closed `final-accepted` and is recorded here rather than back-dated into it. Each of the four was **re-derived against the working tree at homing time**, not carried from the pass that raised it — the spec-020 cycle's homing found two wrong claims in its own catalog, so a catalog is a claim and re-derivation is the precondition for moving one.

The homing itself is a kanban-DB edit plus a `scripts/build_kanban_md.py` / `scripts/build_kanban_html.py` regenerate, which is outside this cycle's spec-and-`.py` scope and outside the concurrent-writer freeze on `examples/fakeshop/db.sqlite3`. This section is the record the homing pass works from; no card body was edited by this cycle.

1. **The shipped `docs/GLOSSARY.md` axis-3 sentence lacks the plan-time qualifier -> `TODO-ALPHA-051-0.0.15`, Slice 5 glossary flip.** Re-derived at homing: `grep -c 'at plan-construction time' docs/GLOSSARY.md` -> **0**, against `CHANGELOG.md` #"at plan-construction time" and seven statements of the plan/fetch boundary in the reconciled spec. The entry's axis-3 line reads `docs/GLOSSARY.md` #"generated `Prefetch` child querysets do NOT inherit the root alias" — true of plan time, which is what the entry describes, and the only one of the three shipped surfaces a reader can misread as a fetch-time promise. **Why that card:** its Slice 5 already owns one `GlossaryTerm.body` ORM edit and one `scripts/build_glossary_md.py` run, and three spec-020 glossary halves are homed there for exactly that reason. Never hand-edit the rendered file.
2. **`_visible_related_object`'s resolver-level alias re-pin is absent from the same GLOSSARY entry -> `TODO-ALPHA-051-0.0.15`, the same Slice 5 flip.** Re-derived at homing: `grep -c '_visible_related_object' docs/GLOSSARY.md` -> **0**. Discoverability, not correctness — the behavior is contract in the spec and shipped in `django_strawberry_framework/types/resolvers.py::_visible_related_object`. **Constraint the homing pass inherits:** it lands as a refinement of axis 3 and **not** as a fifth axis; `four axes` occurs 6 times in the spec and `five axes` / `fifth axis` 0, and the framing is load-bearing in the shipped GLOSSARY entry and in `CHANGELOG.md` too, so a card that adds a fifth puts three shipped surfaces out of step. **Take items 1 and 2 together or neither:** they are one ORM edit on one row, and landing 2 alone leaves the entry naming the re-pin while still lacking the plan-time qualifier the re-pin is an instance of.
3. **A dead `KANBAN.md` locator inside the rationale's moved Decision 9 justification -> `TODO-ALPHA-052-0.1.0`, repo-wide sweep / spec-rationale consistency checker.** Re-derived at homing: the cited substring `owns the version bump` has **0** occurrences in the working tree's `KANBAN.md` and **0** at HEAD, so it was already dead when Slice 1 moved the block. **Why that card:** it is the *generated-target class* that card's spec-022 bullet already scopes — a `#"substring"` citation whose target is a script-rendered document, killed by a regenerate with no edit to the citing file and therefore invisible to the citing spec's own review. Worth more as a regression case for that checker than as a repair: the substance survives the dead locator, since the joint-cut policy is stated normatively in the spec's own `### Decision 9`. If repaired, re-point at `docs/SPECS/spec-020-list_field-0_0_7.md` Decision 10, which the same sentence already names as the policy's true source. The citation sits in moved-verbatim deliberation, which `docs/builder/worker-1.md` rule 4 protects from rewriting.
4. **NOT IN THE FINAL GATE'S CATALOG — `GlossarySpecMention.notes` for this spec is stale until the writing form of `import_spec_terms` runs.** Slice 2 rewrote the `notes` cell of 7 rows in `docs/SPECS/appx/spec-023-multi_db-0_0_7-terms.csv`, and `examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py::Command._sync_spec_mentions` is what writes that column into the DB. **Re-derived at homing, and the consequence is measured rather than assumed:** the CSV diff is 14 changed lines over 7 rows and the term and anchor columns are byte-identical across it, so no anchor moved; `::Command._assert_plan_matches_db` compares only ordered `term__anchor` lists for `GlossarySpecMention` and for `card.glossary_links`, never `notes`, so the read-only `--check` form stays green; and `scripts/build_glossary_md.py` selects `notes` in its `allGlossarySpecMentions` query but consumes only `specPath`, so no rendered surface drifts — `grep -c 'The entry this card flips from' docs/GLOSSARY.md` -> **0**. Invisible to every gate the board runs, which is why it is recorded rather than left to be re-found. **Work:** one writing-form `import_spec_terms` run at a window when no concurrent session is writing `examples/fakeshop/db.sqlite3`. Not carded — a sync command, not an edit; if it is preferred batched, `TODO-ALPHA-052-0.1.0` already carries the `_sync_spec_mentions` orphan-row bullet against the same command and the same file.

Two items in that catalog are **decided, not deferred**, and are homed nowhere: `## Implementation plan`'s line-delta estimate table, and the unticked `- [ ]` boxes in the shipped spec.
