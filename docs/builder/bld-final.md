# Build: Final test-run gate — optimizer_hardening / 0.0.10 (035)

Spec reference: `docs/spec-035-optimizer_hardening-0_0_10.md`
Build plan: `docs/builder/build-035-optimizer_hardening-0_0_10.md`
Status: final-accepted

Worker 1 final test-run gate — the build's last gate before maintainer handoff. The cross-slice
integration pass (`docs/builder/bld-integration.md`) is `final-accepted` with no consolidation
needed; all four in-spec slices are `final-accepted` (Slice 1 G1 procedural / shipped `d1dea2fd`,
Slice 2 G2 + Decision 5 — the only functional code this cycle, Slice 3 G3 deferred / no code,
Slice 4 doc + DB wrap). This pass runs the gate read-only; it edits no source/tests/spec/build-plan
and does not commit.

Working-tree baseline at gate time (`git status --short`, branch `main`, HEAD `3c2b0427`): exactly
the expected build surfaces dirty — `CHANGELOG.md`, `KANBAN.html`, `KANBAN.md`, `README.md`,
`django_strawberry_framework/optimizer/walker.py` (G2), `django_strawberry_framework/types/resolvers.py`
(Decision 5), `docs/GLOSSARY.md`, `docs/README.md`, `docs/spec-035-optimizer_hardening-0_0_10.md`
(Slice 2 Worker-1 test rerouting), `examples/fakeshop/db.sqlite3`, the three Slice-2 test files,
plus the six untracked `docs/builder/bld-*.md` / `build-035-*.md` artifacts. No version files
(`pyproject.toml`, `__init__.py`, `tests/base/test_init.py`, `uv.lock`) — consistent with the
joint-`0.0.10`-cut version boundary (Decision 9). No unexpected drift.

## Gate commands (run in order; each pass/fail recorded)

### 1. Full test sweep — `uv run pytest --no-cov`

**PASS — `1972 passed, 4 skipped in 92.32s`.**

- Full collection across all three test trees (`tests/`, `examples/fakeshop/apps/<app>/tests/`,
  `examples/fakeshop/test_query/`, plus the project-level `examples/fakeshop/tests/`). The explicit
  `--no-cov` opted out of `pytest.ini`'s auto-applied `--cov` (plain `pytest` is a coverage run here
  and is forbidden by "Coverage is the maintainer's gate, not a worker's tool"; no `--cov*` flag was
  used).
- The **4 skipped** tests are the `FAKESHOP_SHARDED`-gated sharded-only tests, which are out of the
  default invocation by design (`AGENTS.md` — "Sharded-specific tests live behind `FAKESHOP_SHARDED`
  and do not run under the default pytest invocation"). Expected, not a failure.
- Line coverage was NOT inspected or asserted (per the gate's narrow contract — `fail_under = 100`
  is CI's / the maintainer's gate).

### 2. Django consistency — `uv run python examples/fakeshop/manage.py check`

**PASS — `System check identified no issues (0 silenced).` (exit 0).** No model/admin/url-config
drift.

### 3. Django consistency — `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`

**PASS — `No changes detected` (exit 0).** Confirms model state is migration-consistent. Slice 4
edited the kanban/glossary DB **rows** via the ORM (`GlossaryTerm.body`, `Card.status`, `SpecDoc.url`,
`CardItem`, `CardGlossaryTerm` / `GlossarySpecMention`), **not** the schema, so no migration is needed
— `--check --dry-run` reports none missing, exactly as the build plan's Slice-4 note predicted.

### 4. Lint / format / diff gate (read-only — no `--fix`)

- **`uv run ruff format --check .` — PASS** (`267 files already formatted`, exit 0). The
  `COM812 may cause conflicts with the formatter` line is the repo's **standing config note**
  (recorded across the slice build reports), not a formatting failure — the command exited 0.
- **`uv run ruff check .` — PASS** (`All checks passed!`, exit 0).
- **`git diff --check` — PASS** (exit 0, no output). No whitespace errors or conflict markers
  anywhere in the working tree.

## Gate verdict

All seven gate commands pass. No failure to route back through an owning slice. No pre-flight
baseline exception was needed (none was recorded in the build plan; the baseline was clean). The
build delivered its spec contract — G1 (shipped `d1dea2fd`) + G2 + Decision 5 + the doc/card wrap —
with G3 deferred by design. **Status set to `final-accepted`.**

### Deferred work catalog

Walked every per-slice and integration artifact's spec-reconciliation notes, `What looks solid`,
`DRY findings`, and `Notes for Worker 1` sections, cross-checked against the spec. The build did
defer work; one bullet per deferral, with the source artifact section, the licensing spec line (where
applicable), and a one-line description. This catalog is the next spec author's (and the
abstract-return optimizer entry card's) reading list.

- **G3 entirely deferred — the whole fragment type-condition narrowing, carry-forward requirements
  R1–R3.** Source: `bld-slice-3-g3_fragment_narrowing.md` (Plan + Final-verification, the deferral
  contract) and `bld-integration.md` Pre-step 5 ("the deferred G3 design is the largest
  carry-forward"). Licensed by spec Slice-3 checklist line 56 (`**[deferred]**`), Decision 6 (lines
  223-258, "Status: DEFERRED — carry-forward requirements, no runtime code in spec-035"), Decision 7
  (lines 260-272), Revision 3 (line 15), Out-of-scope (line 416), and DoD items 6-8 (lines 443-449,
  `*(deferred)*`). Description: G3's registry-only fragment type-condition narrowing ships no runtime
  code in spec-035 because it has no reachable production trigger today (an abstract interface/union
  root never enters the walker — `registry.model_for_type` returns `None` for the abstract origin, so
  `extension.py::_optimize` passes the queryset through before the walker / any classifier runs). The
  full design moves to the **abstract-return optimizer entry card** (the `BACKLOG.md`
  `polymorphic_interface_connections` work, or a dedicated card), which must satisfy:
  - **(R1)** Build the abstract-return production-entry contract FIRST (target-model resolution,
    origin / plan-cache identity for an abstract origin, registry-only possible-concrete-type
    enumeration, strictness for an abstract walk) — the precondition that makes the narrowing
    reachable at all (spec Decision 6 R1, lines 256).
  - **(R2)** Thread the classifier through BOTH walker inliner consumers — `walker.py::_walk_selections`
    AND `walker.py::_selected_scalar_names` (the FK-id-elision-safety analyzer) — or prove the second
    only ever sees concretely-typed relation child selections (spec Decision 6 R2, line 257). The two
    `# TODO(spec-035 Slice 3)` source anchors in `walker.py` plus the `selections.py` inliner anchor
    stage this.
  - **(R3)** Define a non-Relay registry name-resolution primitive (scan `registry.iter_definitions()`
    by `graphql_type_name`; the existing `definition_for_graphql_name` is Relay-Node-only) with
    explicit fail-closed ambiguity behavior, and source interface GraphQL names from Strawberry
    definition metadata, not Python `__name__` (spec Decision 6 R3, line 258).
  - The deferred G3 test plan (spec lines 364-381) travels with it, including the P3a note that the
    live `GenreType` matching-type test is no-regression / coverage only, not a behavioral proof.

- **G2 live-test handoff — the first `0.0.11` mutation card must add a live `examples/fakeshop/test_query/`
  test.** Source: `bld-slice-2-g2_only_operation_gating.md` "Three-test-tree sweep note" (the live
  handoff recorded as carry-forward, not triggered this card). Licensed by spec Slice-2 test plan
  "Live-test handoff (mandatory for the first mutation card)" (line 362) and Out-of-scope "The
  `0.0.11` mutations cohort … G2 live-test handoff" (line 422). Description: G2's coverage is
  package-internal only because the fakeshop schema exposes no mutation surface today, so the behavior
  is not yet reachable over `/graphql/`. The first card that adds a fakeshop mutation returning a
  queryset (the `0.0.11` cohort) MUST add or migrate a live `examples/fakeshop/test_query/`
  acceptance test (reload-fixture pattern, `CaptureQueriesContext` SQL-shape assertion) proving the
  mutation queryset response keeps `select_related` / `prefetch_related` while carrying NO deferred
  loading.

- **`force_unplanned` "planned-but-genuinely-lazy" pattern note — a recurring hazard for future
  elision/optimization seams.** Source: `bld-slice-2-g2_only_operation_gating.md` "Notes for Worker 1
  (spec reconciliation)" (resolved in-cycle) and `bld-integration.md` Pre-step 5 ("planned-but-lazy
  pattern … recurs in the `0.0.11` mutation cohort"). Not a per-card deferral that licenses a spec
  line — it is a forward-looking design caveat surfaced for the maintainer / next author. Description:
  any future "strictness-visible fallback" on an elision or optimization seam must first check whether
  the relation is recorded `planned` (by `_record_relation_access`, unconditionally), because
  `_check_n1`'s `if key in planned` short-circuit silences strictness unless the keyword-only
  `force_unplanned` bypass is threaded (added by Slice 2 on the unsafe-elision fallback). This will
  recur when the `0.0.11` mutation cohort adds more queryset-returning resolvers.

- **Accepted cross-card `planning_state` "Needs spec" rendering — a repo-wide done-card cleanup
  follow-up.** Source: `bld-slice-4-doc_wrap.md` "Notes for Worker 1 / Final verification" (accepted
  cross-card pre-existing condition) and `bld-integration.md` Pre-step 5. No spec line licenses it
  (it is out of Slice-4 scope and not introduced by this build). Description: the rendered
  `DONE-035-0.0.10` card header reads `- Status: Needs spec` because `planning_state` was deliberately
  left untouched (out of slice scope). This matches existing done-card precedent (repo-wide: `Shipped`
  ×28, `Planned` ×4, `Needs spec` ×2, `In progress` ×1 — the joint-cut sibling `DONE-034-0.0.10`
  itself renders `- Status: In progress`). If the maintainer wants done cards to render a terminal
  `planning_state`, that is a separate cross-card cleanup spanning many DONE cards — flagged for a
  maintainer / next-spec follow-up, NOT a defect of this build.

- **Pre-existing DONE-034 `import_spec_terms` mention-drift — repaired as a side effect of Slice 4's
  write pass (surfaced to the maintainer).** Source: `bld-slice-4-doc_wrap.md` "DB-verification
  findings" + "Implementation notes" ("`import_spec_terms` side effect — DONE-034 drift repair").
  Description: at HEAD `3c2b0427`, `import_spec_terms --check` was FAILING on **card 34** (not card
  35): DONE-034's `SpecDoc.url` resolved to the archive path `docs/SPECS/spec-034-permissions-0_0_10.md`
  but its `GlossarySpecMention` rows were stored under the old `docs/spec-034-permissions-0_0_10.md`
  path, so `--check` found zero mentions at the archive path. Slice 4's standard WRITE-mode
  `import_spec_terms` re-created card 34's mentions under the archive `spec_path` (it keys every done
  card on `plan.spec_path`), so post-Slice-4 `--check` reports `OK: 35 done cards have glossary links.`
  The stale `docs/`-path mention rows for card 34 are now orphaned but harmless (`--check` only queries
  the archive path). This was a pre-existing data drift independent of card 35, repaired incidentally;
  surfaced here so the maintainer is aware the Slice-4 commit's `db.sqlite3` diff includes a card-34
  mention-row reconciliation (GLOSSARY spec-mention total rose 851→916; feeds the cross-reference
  tables only, zero term-body drift, byte-clean re-regenerate confirmed).

## Spec changes made (Worker 1 only)

None. The final test-run gate made no spec edit. The spec status line (line 5: "G1 shipped
(commit `d1dea2fd`); G2 + the doc wrap remain; G3 deferred") still accurately describes the completed
build (G1/G2 shipped, G3 deferred, doc wrap complete via Slice 4) and makes no stale "already-shipped
work remains unshipped" claim. The spec file correctly stays at its working location
`docs/spec-035-optimizer_hardening-0_0_10.md` (AGENTS.md #26 / BUILD.md "Spec stays at its working
location"); only the `SpecDoc.url` DB field points forward at the `docs/SPECS/` archive home.

## Outcome

Gate passes on all seven commands. **Status: `final-accepted`.** The gate closes the build cycle;
Worker 0 may mark the final checklist box `- [x]` and hand off to the maintainer for review and
commit.
