# Package build plan: full_relay / 0.0.9 (032)

Spec source: `docs/SPECS/spec-032-full_relay-0_0_9.md` (already archived; the card shipped as `DONE-032-0.0.9`)
Target release: `0.0.9` (shipped)
Cycle type: **residual reconciliation cycle** — the code is built and shipped. What is owed is the missing `-rationale.md` companion plus a spec/code reconciliation that makes the spec describe what actually exists today.
Build rule: one slice at a time. Plan first, edit second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

Ownership partition: `none; sequential slices.` Every slice writes the same spec file, so no two can run concurrently.
Hot-path declaration: `none.` No slice changes executable bytes.
Floor-verification scope: `none.` No slice touches a Django / Strawberry / channels integration seam.

Pre-flight: passed on 2026-08-26.

- **Baseline** (`git status --short`): the maintainer has staged deletions of the eleven prior-cycle `docs/builder/bld-031-*.md` artifacts and carries one untracked `0_0_14.md` at the repo root. Both are concurrent maintainer work, out of scope per `AGENTS.md` rule 34 — **never edited, never reverted** by any worker.
- **Baseline-dirty out-of-scope files:** `docs/builder/bld-031-*.md` (11 staged deletions), `0_0_14.md` (untracked).
- **Artifact reset deviation (recorded, not silently taken):** `docs/builder/build-031-globalid_encoding-0_0_9.md`, `docs/builder/bld-031-final.md`, and `docs/builder/bld-003-final.md` remain on disk. `worker-0.md` pre-flight step 3 would delete them; the maintainer is actively mid-deletion of that same cohort, so deleting tracked files under a concurrent writer is refused here and the step is discharged by its other half instead — **every path this cycle creates was verified not to exist.** Completed plans are archived by the maintainer under `docs/builder/DONE/`.
- `scripts/review_inspect.py` smoke invocation: **passed** (`django_strawberry_framework/relay.py --output-dir docs/shadow --stdout`).
- **Baseline exception, recorded LATE (2026-08-27) rather than at pre-flight — `scripts/build_tree_md.py --check` fails at HEAD.** Pre-flight did not run it, so the exception `BUILD.md` `## Final test-run gate` requires was not on record when the gate hit it. It is recorded now, on measurement rather than convenience, and the lateness is the finding: **pre-flight should run every gate command it expects the final gate to run, or a pre-existing failure arrives at the end of the cycle looking like the cycle caused it.**
  - Evidence, obtained read-only (rendered into a scratch copy outside the repo; no stash/checkout/worktree): the entire render delta against `git show HEAD:docs/TREE.md` is **three added rows** — `tests/test_consumers.py` (twice, current + target tree) and `examples/fakeshop/test_query/test_connection_pagination_api.py`. Those modules landed in maintainer commits `0e5044da` / `3c105cf9` (2026-08-26), one day *after* `docs/TREE.md`'s last render (`91989b60`), and `git status` reports `docs/TREE.md` clean — so the staleness is committed at HEAD.
  - None of the three files is in this cycle's diff. The render consumed this cycle's three edited test-module docstrings and produced **zero** changed comment lines, because all three edits sit on lines 4-5 rather than the docstring's first summary line, which is the only line the renderer reads. Worker 0 predicted this before the gate ran; the gate measured it, which is what settles it.
  - **Not fixed here.** `docs/TREE.md` is on this cycle's do-not-touch list, and `START.md` separately warns against regenerating a rendered doc while another session's feature work is mid-flight. The fix is one `build_tree_md.py` run committed alongside the `0.0.14` work. Escalated to the maintainer.
- `.gitignore` lists all three untracked scratch paths (`docs/builder/worker-memory/`, `docs/shadow/`, `docs/builder/temp-tests/`).
- Scratch: `docs/builder/temp-tests/` empty; `docs/shadow/` carries only regenerable overviews (overwritten per run); the four `docs/builder/worker-memory/worker-N.md` files exist and are seeded by this cycle's first spawn.
- Spec-doc consistency check: run by Slice 0 as a pre- and post-condition of the rationale move.
- **Spec rationale extraction: OWED — it is Slice 0 of this cycle.** No reconciliation slice dispatches until it is done and verified.

Tracked binary / generated files that a concurrent writer can rewrite mid-cycle: `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`. **This cycle writes none of them** (see Scope below), so any churn in them is a concurrent writer's and is left alone.

## Scope of this cycle (maintainer-set)

- **In scope:** `docs/SPECS/spec-032-full_relay-0_0_9.md`, the net-new `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md`, sibling spec files whose citations the rationale move breaks, and `.py` source under `django_strawberry_framework/` / `tests/` / `examples/` **only if the code is found to have skipped or dropped a spec contract**.
- **Out of scope:** every closeout / agentflow edit (`KANBAN.md`, `docs/GLOSSARY.md`, `CHANGELOG.md`, `TODAY.md`, `README.md`, `GOAL.md`, `docs/TREE.md`, `docs/README.md`, the kanban DB). Do not touch them.
- **Every file this cycle creates carries `032` in its name.**

## Worker-0 pre-dispatch verification (code vs. spec)

Performed before any dispatch, per `BUILD.md` `### Worker 0 verifies every finding against source before dispatching`. **Verdict: the code did not skip, drop, or forget any spec-032 contract.** Every functional deliverable and every spec-named test exists at HEAD:

- Slice 1 — `types/base.py::_validate_interfaces` carries the six named-helper rejections (`_RELAY_NON_INTERFACE_HELPERS`, identity-matched, raising before the non-class branch so `relay.NodeID` is named); the two re-affirmation pins exist in `tests/types/test_base.py`.
- Slice 2 — `django_strawberry_framework/relay.py` ships both factories with `strawberry.ID` arguments, `_decode_or_graphql_error` (narrow scope), pk pre-coercion, typed-match check, per-type batching, `_interleave`, and the `_node_fields_declared` ledger; `types/finalizer.py` raises the exact `"node lookup configured but no Node types registered."` message; both symbols are in `__init__.py.__all__`.
- Slice 3 — `ALLOWED_META_KEYS` contains `"relation_shapes"`, `_validate_relation_shapes` + the stage-2 target validation exist, `DjangoTypeDefinition` carries the slot, and `types/finalizer.py::_synthesize_relation_connections` performs the Phase-2.5 synthesis with the two-surface collision guard.
- Slice 4 — `connection.py::_connection_type_for` is always-concrete; `tests/test_connection.py::test_relay_max_results_cap` and the live conformance matrix in `examples/fakeshop/test_query/test_library_api.py` exist.
- Slice 5 — `django_strawberry_framework/testing/relay.py` ships `global_id_for` / `decode_global_id` with the cause-discriminated remediations.
- Slice 6 — the library `Query` carries `node` / `nodes` / typed `genre`; `BookType` is Relay-Node-shaped with the `circulation_status="repair"` `get_queryset`; every named live test exists.

**So no Worker-2 dispatch is authorized on a skipped-code finding.** What the verification *did* find is a spec that no longer describes the code, in two distinct buckets:

**Bucket A — surface this card's own build shipped and the spec never described.** Traced to the spec-032-era commits (`3e247237`, `1f16d963`):

- A1 `relay.py::_stamp_node_type` / `types/relay.py::_NODE_TYPE_HINT_ATTR` — the decode-resolved type is stamped on a shallow copy and honored by `install_is_type_of` before the isinstance fallback. Decision 4 currently claims plain `is_type_of` injection suffices; for a model with two registered Relay types it does not.
- A2 `relay.py::_check_nodes_result` — a net-new `ConfigurationError` boundary requiring a consumer `resolve_nodes` override to return a list 1:1 with the `node_ids` it received. Unmentioned in the spec.
- A3 `relay.py` `reject_async_in_sync_context` + `_SYNC_RESOLVER_RECOURSE` — the root fields reject an awaitable returned in a sync context themselves; the spec says only that `SyncMisuseError` is inherited from the defaults unchanged.
- A4 `relay.py::_coerce_pk_or_none` coerces against the concrete field behind `resolved_type.resolve_id_attr()` via `utils/querysets.py::coerce_field_value_or_none`, not `model._meta.pk.to_python` unconditionally — the `relay.NodeID` id-slot generalization the spec's Decision 5 / Edge cases / DoD 3 do not state.

**Bucket B — post-ship contract changes later cards made to surface this spec owns.** Traced to `567cc6d0` (the `0.0.14` security card) and the spec-033 / spec-047 cohort:

- B1 `types/base.py::DEFAULT_RELATION_SHAPE = "connection"` (spec-047 Decision 5). The spec states `"both"` as the default in Goal 2, the Slice-3 checklist, the User-facing API sample, Decision 6 (three bullets + justification + a rejected alternative), Decision 7, Edge cases, Risks, and DoD item 6.
- B2 `resource_policy.py::ResourcePolicy.max_node_ids = 200`, enforced by `extensions/resource_policy.py` on the `ids` argument. This **falsifies** the spec's Edge case "`nodes(ids:)` is uncapped" and the matching Risks item, whose stated fallback in fact landed.
- B3 `relay.py` calls `check_deadline(info)` in both resolvers (spec-047 cooperative deadline).
- B4 `Meta.cursor_field` keyset cursors **shipped** (`ALLOWED_META_KEYS`), so every spec sentence deferring them to `BACKLOG.md` item 39 as unshipped needs re-reading.
- B5 The Phase-2.5 synthesis gained re-entrancy handling and the spec-033 walker slot (`_SYNTHESIZED_RELATION_CONNECTION_MARKER`, `_record_relation_connection`, teardown registration).
- B6 `relay.py`'s module scope broadened past the root fields: `decode_model_global_id` / `DecodeResult` / `GlobalIDDecode` / `_resolve_real_pk` now serve the write flavors. Decision 11 describes the module as the root-field home only.
- B7 Fakeshop consequences of B1: `GenreType`/`BookType` carry explicit `relation_shapes = {...: "both"}` raw-list opt-ins, `IssueType` carries `{"issues": "connection"}`, and `LoanType` gained a default-OFF `FAKESHOP_TEST_LOAN_CONNECTION` Relay opt-in.
- B8 Test renames the spec's Test plan still spells by the old names: `test_default_both_synthesizes_connection_sibling` became three tests, and `test_relation_shapes_on_consumer_authored_relation_raises` became two.

**Foreign-citation hazard (pre-recorded, standing lesson).** One sibling spec cites text this cycle's rationale move relocates: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` #"Revision 6 P2 established that nothing implements strictness for connections" points into spec-032's inline revision history. No `spec-032-full_relay-0_0_9.md#<anchor>` link exists anywhere in the tree (checked), so the citation census is exactly this one site plus the plain-`Decision N` references, which survive the move.

## Artifact list

The cycle ran seven artifacts, all `final-accepted`; each is summarized in the
`## Checklist` below. They were deleted after the cycle's commit (`7d2c15dc`) and are
recoverable from it; anything in them that a later pass must not re-open was folded into
this file first, under `## Settled, do not re-open`.

- `docs/builder/bld-032-slice-0-rationale_extraction.md` (deleted)
- `docs/builder/bld-032-slice-1-root_field_surface.md` (deleted)
- `docs/builder/bld-032-slice-2-relation_shapes.md` (deleted)
- `docs/builder/bld-032-slice-3-cross_spec_residue.md` (deleted)
- `docs/builder/bld-032-review-1-spec_diff.md` (deleted)
- `docs/builder/bld-032-integration.md` (deleted)
- `docs/builder/bld-032-final.md` (deleted)

## Settled, do not re-open

Two review-round findings were rejected with reasons rather than routed. Both look like
ordinary defects to a reader who has not seen the reasoning, and acting on either would
damage something load-bearing, so they are recorded here rather than left to be
rediscovered.

- **The six `### Justification (moved from the spec)` bodies in
  `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` open with a lowercase fragment.
  Leave them.** They open mid-sentence because the move was byte-verbatim, and
  byte-verbatim is the property that makes the move auditable: a future reader can diff any
  moved body against the spec's own git history and confirm nothing was reworded.
  `worker-1.md` `### Performing the rationale move` additionally makes the companion
  append-only during a build. Capitalising six openers buys nothing and destroys that, and
  it costs the same later as now — which is exactly why leaving the finding open would
  invite a future pass to "fix" it.
- **`## Current state`'s "as of this writing" in
  `docs/SPECS/spec-032-full_relay-0_0_9.md` is section scoping, not a stale timestamp.
  Leave it.** It declares the date the section describes rather than the date the file was
  edited, and three of this cycle's case-(c) gradings rest on that declaration: Slice 1's
  five struck-through foundation items, Slice 2's `GenreType` description, and Slice 3's
  products sentence. The spec's line 3 disclosure and this one are designed redundancy, not
  rot.

## Dispatch shape

Every reconciliation slice edits the spec and nothing else, so **Worker 2 is not dispatched** (maintainer instruction: dispatch a builder only when the code needs to change; a spec-only change is Worker 1's alone). Isolation is preserved instead by one Worker 3 pass over the whole spec diff before the integration pass — `BUILD.md` `### Cohorting, naming, and closure` requires it, and the residual cycle's dominant defect is a *false description* of a finding, which only an agent with no memory of writing the sentence can catch.

## Checklist

- [x] Slice 0: spec rationale extraction (pre-flight step 7) -> `docs/builder/bld-032-slice-0-rationale_extraction.md`
  - Closed `final-accepted`. Spec 188,525 -> 145,056 bytes; companion `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` created at 75,855 bytes. `check_spec_glossary.py` exits 0 both before and after (`OK: 40 terms`), 0 residual `Justification:` / `Alternatives considered` labels and 0 `Revision N` markers survive in the spec, and the anchor/link sweep is clean on both files.
  - **Census correction that widens Slice 3:** the pre-dispatch census grammar was `spec-032 Decision N`; the actual population is `spec-032` plus any chronology word. Two `.py` comment sites cite the moved revision history — `tests/test_relay_node_field.py` #"(spec-032 Revision 7 P1)" and #"Discriminating (spec-032 Revision 7 P2)". `.py` files are in this cycle's maintainer-set scope, so **Slice 3 owns them** alongside the `spec-033` site; no maintainer widening is needed and nothing is deferred.
- [x] Slice 1: root-field surface reconciliation (A1-A4, B2, B3, B6) -> `docs/builder/bld-032-slice-1-root_field_surface.md`
  - Closed `final-accepted`. All seven findings re-verified at HEAD; **no code defect** — every one is spec staleness, so no builder was owed. 26 prose sites across 12 spec sections; spec 145,056 -> 157,923 bytes, companion 75,855 -> 85,123.
  - **Correction to this plan's own bucketing:** A3 (`reject_async_in_sync_context` / `_SYNC_RESOLVER_RECOURSE`) is Bucket **B**, not A — `git log -S` returns exactly one commit, `dc00f4a6` (2026-08-16), post-ship. Re-verified independently by Worker 0. The pre-dispatch verification read the surrounding module's era rather than the symbol's own history.
  - Found beyond the dispatched list: **DoD item 1 is false at HEAD in both halves** (both glossary entries ship and both terms are in the CSV) — taken here rather than split, since the sentence names one Slice-1 and one Slice-2 symbol and a half-fix is the defect this cycle exists to avoid; **Slice 2 needs no action on it**. Routed onward: the pre-archive `docs/spec-032-...` path spelling at five prose sites -> **Slice 3**; the same falsified "deliberately uncapped" claim in `docs/GLOSSARY.md`'s `## DjangoNodesField` entry -> **final gate's `### Deferred work catalog`** (DB-generated and on this cycle's do-not-touch list).
- [x] Slice 2: relation-as-Connection reconciliation (B1, B5, B7, B8) -> `docs/builder/bld-032-slice-2-relation_shapes.md`
  - Closed `final-accepted`. All four findings re-verified at HEAD; **no code defect**. 20 prose sites + 2 link defs; spec 157,923 -> 165,828 bytes, companion 85,123 -> 97,055 (the companion outgrowing the spec is the signature of a reversal rather than an addition).
  - **The `"both"`-default sweep, measured:** 16 literal `"both"` occurrences pre-pass, of which 10 asserted the old default; four more sites carried the claim with **no matching token** (a test name spelling it `_both_`, a `sibling`/`opt-out` sentence in `## Problem statement`, an Edge-case title, and the `Status:` line's "siblings" framing). Population 14, all rewritten. Post-pass the literal count is *higher* (22) with zero default assertions — saying "opt-in" where you said "default" adds occurrences, so a count alone would have read as a regression.
  - **Correction to this plan's own finding text:** the `{"issues": "connection"}` key is on `PeriodicalType`, not `IssueType` (which carries no `relation_shapes` at all).
  - Routed to Slice 3 with replacement text: three `.py` docstring/comment sites still spelling the `implicit "both" default`, and `BookType.Meta`'s comment naming a nonexistent `ItemType.properties` (the field is `CategoryType.properties`).
  - Tree note: the maintainer committed the eleven `bld-031-*` deletions mid-cycle (`b2392014`). Nothing of this cycle's was swept; nothing was reverted.
- [x] Slice 3: cross-spec residue + foreign-citation repair (B4, spec-033 citation, the `.py` comment sites, the pre-archive path spellings) -> `docs/builder/bld-032-slice-3-cross_spec_residue.md`
  - Closed `final-accepted`. **No code defect.** Spec 165,828 -> 170,612; companion 97,055 -> 108,497; `spec-033` +230 bytes (one citation repair + one link def, nothing else); 7 `.py` files comment/docstring-only.
  - **Citation census as an anchor measurement, 369 occurrences / 54 files:** 102 contract citations (`Decision N` / `Goal N` / `Edge cases` / `DoD` / `Slice N`), which survive the move by construction; **12 chronology citations, which do not** (live population outside this cycle's own scratchpads: 4 occurrences at 3 sites, all repaired); 13 pre-archive `docs/spec-032-…` path spellings; 242 bare identity mentions. The durable number is the classification, not the total: a rationale move puts ~1% of a spec's inbound references at risk.
  - The classifier was blind to the plural `Decisions 6/7` on its first run and had mis-filed a live `types/finalizer.py` citation — the same shape as Slice 0's missed `Revision N PN`, one pass later. Fixed and re-measured.
  - **Independently re-verified by Worker 0:** all 7 `.py` files are comment/docstring-only — AST normalized with docstrings blanked and positions flattened is byte-identical to `git show HEAD:<path>` for every one, with the checker proved failable by an executable-change control and a renamed-arg control (and passing line-shift / comment-only / docstring-only negatives). Worker 2's own proof needed three attempts and its first two passed their own controls, so this is a second instrument, not a re-run of the first.
  - Two sites were graded case (c) — true, forward-looking, since resolved — and deliberately **left standing** rather than flipped into a false claim that the package lacks keyset cursors (Goal 4 and Decision 9's stale-`after` bullet).
- [x] Review round 1: Worker 3 over the whole spec diff -> `docs/builder/bld-032-review-1-spec_diff.md`
  - Worker 3 returned `review-accepted` with **zero High findings** — every sampled contract sentence is true at HEAD — and two Mediums escalated to Worker 1.
  - **M-1** (`docs/GLOSSARY.md` `## Meta.relation_shapes` still says `"both"` is the implicit default) is a genuine routing gap this plan's own dispatch created: Slice 1 found the sibling defect **in the same file** and routed it, and Slice 2 then ran the cycle's largest `"both"`-default census over the spec and `.py` only, never re-sweeping the file Slice 1 had just implicated. The lesson is the routing, not the sentence — **a file implicated by one slice's finding belongs in the next slice's census scope.** The file is DB-generated and on this cycle's do-not-touch list, so the fix is a second deferred-catalog entry with corrected text, beside the one already routed.
  - **M-2** (`recorded at final verification` chronology surviving the extraction) is a spec edit Worker 1 owns: Slice 0 routed three sites, the measured population is **six** — four in `## Doc updates` plus one each in `## Slice checklist` and `## Test plan`.
  - Worker 3 re-derived all three of Slice 3's deferred routings and confirmed each genuinely out of scope. It also caught its own near-miss: Slice 2's `"both"` 16 -> 22 count reads as a mixed-instrument comparison and is not, which would have been a false Medium.
- [x] Cross-slice integration pass -> `docs/builder/bld-032-integration.md`
  - Closed `final-accepted`. No cross-slice contradiction: the `relation_shapes` default reads one consistent way across all ten of its homes, the `nodes` cap seam between Slice 1 and Slice 3 states one contract, and 13/13 Decisions are keyed in both directions with no normative sentence stranded in the companion. Staged-anchor sweep: zero `TODO(spec-032` anchors in shipped source; proved a measurement rather than a broken instrument by finding live `TODO(spec-033/035/036` anchors with the same grep.
  - Closed both of Worker 3's declared blind spots rather than routing them: the companion's eight revision entries are byte-faithful to HEAD (27/31 lines identical, the 4 differences all mandatory in-page -> cross-file anchor conversions), and every sibling spec was swept (14 files, 68 occurrences, zero chronology and zero pre-archive paths).
  - **New finding: `KANBAN.md` carries the same pre-archive path rot and no census had the repo root in scope** — 17 stale `docs/spec-<NNN>` prose paths, 13 naming archived specs that resolve to missing files, two of them this card's own. **A census is bounded by its roots as well as its grammar, and roots look like configuration rather than a claim.** Routed with a named owner.
  - Recorded rather than hidden: the census walk initially included `docs/builder/worker-memory/`, so the script counted a `spec-032` token in two forbidden files. Counts only, no content read — but the forbidden-read rule is about the file, not the method, so the walk was re-scoped and the crossing written into the artifact.
- [x] Final test-run gate -> `docs/builder/bld-032-final.md`
  - Closed `final-accepted` under the baseline exception recorded in this preamble. `uv run pytest --no-cov`: **6870 passed, 42 skipped, zero failures, zero errors.** `manage.py check`, `makemigrations --check --dry-run`, `ruff format --check`, `ruff check`, `git diff --check`, `check_spec_glossary` (032 and 033), `check_citations` (`OK: 815 citations resolve`) and `check_trailing_commas --check` all pass. Floor scope `none`, so no venv was built and `.venv` was never mutated. `pre-commit` is unavailable in this environment (`Failed to spawn`) and every hook is write-mode; discharged by five read-only proxies rather than forced.
  - Gate 10 (`build_tree_md.py --check`) fails on committed-at-HEAD staleness that predates this cycle — see the baseline exception above. The failure record and its attribution stay in the artifact unsoftened, and the owed `build_tree_md.py` run is catalog entry 6 with a named owner: the exception licenses `final-accepted`, it does not discharge the run.
  - Zero executable bytes re-proved a **third** time here by an AST-normalized comparison against HEAD, shown failable on three executable mutations and silent on three cosmetic controls.
  - `### Deferred work catalog`: seven items in six entries, every one with a named owner and, where a prior pass supplied it, replacement text.

## Post-cycle closure

The cycle closed with a deferred-work catalog of seven items in six entries. All were
discharged in a follow-on sweep on 2026-08-27, so the two statements above that name open
obligations — gate 10's owed `build_tree_md.py` run, and the catalog itself — are history
rather than current state. The gate records are left unsoftened on purpose; this note is
the correction, not an edit to them.

- `docs/GLOSSARY.md`'s two falsified claims (`DjangoNodesField` "deliberately uncapped";
  `Meta.relation_shapes` defaulting to `"both"`) corrected in the glossary DB and re-rendered.
- `spec-033`'s five dead `### Decision 9` anchors re-pointed at the doubled-hyphen form.
- The stale pre-archive `docs/spec-<NNN>` paths closed in both homes: three remaining `.py`
  docstrings, and thirteen kanban card-body paths rewritten in the DB and re-rendered. The
  six deliberate `.py` non-edits and the four in-flight kanban paths were left alone, and the
  reasons are carded on `TODO-ALPHA-051` so a later sweep cannot undo them.
- `tests/test_relay_connection.py`'s seven degenerate `"both"` parametrize arms renamed
  `"default"`, which is what they actually exercise; the genuine eighth `[both]` id was not
  touched.
- `TODAY.md`'s relation-as-Connection paragraph now leads with the current default.
- `docs/TREE.md` regenerated; `build_tree_md.py --check` passes.
- `CardItem` pk 1409 deleted — the spec-032 remediation-tail defect it described is fixed.

Committed as `7d2c15dc`.

