# Build: Final test-run gate — globalid_encoding / 0.0.9 (031)

Spec source: `docs/spec-031-globalid_encoding-0_0_9.md`
Build plan: `docs/builder/build-031-globalid_encoding-0_0_9.md`
Artifact: `docs/builder/bld-final.md`
Status: final-accepted

Gate run on 2026-06-10 from the repo root, after the integration pass reached
`final-accepted` (`bld-integration.md`). One build-caused `pytest` failure blocks
`final-accepted`: a stale type-anchored emitted-`GlobalID` assertion in a package
`tests/optimizer/` test that the Slice-2 default-flip invalidated and the Slice-4
example-suite sweep did not reach (it swept only `examples/fakeshop/test_query/`).
Gates 2-6 all pass. The owning slice and a precise fix contract are pinned under
`### Owning slice + fix contract` below.

---

## Gate command results

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **FAIL** — `1 failed, 1511 passed, 3 skipped` (78.78s) |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — "System check identified no issues (0 silenced)." (exit 0) |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — "No changes detected" (exit 0) |
| 4 | `uv run ruff format --check .` | **PASS** — "235 files already formatted" (exit 0; the standing `COM812`-vs-formatter warning is pre-existing config noise, not a failure) |
| 5 | `uv run ruff check .` | **PASS** — "All checks passed!" (exit 0) |
| 6 | `git diff --check` | **PASS** — clean, exit 0 (no whitespace errors / conflict markers; `docs/dry/dry-0_0_9.md` did NOT trip the check) |

`--no-cov` was passed to gate 1 to opt out of `pytest.ini`'s auto-applied `--cov`
(a plain `uv run pytest` would be a forbidden coverage run). No `--cov*` flag was
used in any command. The full sweep ran across all three test trees (`tests/`,
`examples/fakeshop/tests/`, `examples/fakeshop/test_query/`); `FAKESHOP_SHARDED=1`
tests do not run under the default invocation (expected).

---

## Gate 1 failure detail (the sole `pytest` failure)

```text
FAILED tests/optimizer/test_relay_id_projection.py::test_relay_id_with_custom_pk_attname_avoids_lazy_load

    node_id = relay.GlobalID.from_id(result.data["allItems"][0]["id"])
>   assert node_id.type_name == "CustomPKItemNode"
E   AssertionError: assert 'tests.custompkitem' == 'CustomPKItemNode'
E     - CustomPKItemNode
E     + tests.custompkitem

tests/optimizer/test_relay_id_projection.py:178: AssertionError
```

**This is a build-caused failure, not pre-existing and not out-of-scope.** Evidence:

- The failing assertion (`tests/optimizer/test_relay_id_projection.py:178`) decodes
  a `node { id }` emitted by a Relay-Node-shaped `DjangoType` (`CustomPKItemNode`,
  declared inline in the test with no `Meta.globalid_strategy`, so it takes the
  **package default** strategy) and asserts the **old type-anchored payload**
  `node_id.type_name == "CustomPKItemNode"`.
- The Slice-2 default-flip (spec Decision 9, build plan "Breaking default flip")
  re-roots the default emitted `GlobalID` type-name slot onto the Django model
  label (`model._meta.label_lower`). For this test's model
  (`app_label = "tests"`, model `CustomPKItem`) that is `tests.custompkitem` — the
  value the test now receives. The emitted payload is **correct**; the test's
  expectation is stale.
- The test file is **not** part of this build's diff (`git diff --stat --
  tests/optimizer/test_relay_id_projection.py` is empty; last touched by the
  unrelated `spec-029` commit `2d1f2963`), so the build never updated it. It is a
  GlobalID-shaped failure, which the gate guidance flags as "almost certainly this
  build's responsibility."
- Reproduced deterministically in isolation: `uv run pytest --no-cov
  "tests/optimizer/test_relay_id_projection.py::test_relay_id_with_custom_pk_attname_avoids_lazy_load"`
  → `1 failed in 0.84s`.

**Scope confirmation (no second stale assertion in the package `tests/` tree).** A
repo-wide grep for stale type-anchored emitted-`GlobalID` assertions
(`grep -rn '\.type_name' tests/optimizer/ tests/types/ | grep '== "' | grep -v
'label_lower|products.|library.|kanban.|tests.'`) returns **only**
`tests/optimizer/test_relay_id_projection.py:178`. The one other near-match
(`tests/types/test_relay_interfaces.py:1446`,
`_definition_of(CategoryNode).graphql_type_name == "CategoryNode"`) is a
`graphql_type_name` *property* read, NOT a `GlobalID` wire-payload assertion, and is
correct. So `:178` is the single stale site.

### Owning slice + fix contract

**Owning slice: Slice 2 (the encode seam — `bld-slice-2-encode_seam.md`).** The
default-flip to `model` is the Slice-2 contract (spec line 93 / Decision 9; build
plan checklist line 47). The stale assertion is the direct blast radius of that
flip. It is NOT Slice-4 scope: Slice 4 was explicitly bounded to
`examples/fakeshop/test_query/` (spec Slice-4 box; `bld-slice-4-live_http.md` Plan
"This slice touches ONLY `examples/fakeshop/test_query/` test files"), and its
inventory grep swept only that tree (`bld-slice-4-live_http.md` step D, "Grep-sweep
the whole `test_query/` tree"). The package `tests/optimizer/` assertion lives
outside that boundary and so was never in Slice 4's contract. The assertion churn
belongs to the slice that flipped the emitted-payload default — Slice 2.

**Fix contract (route through the Slice-2 loop: Worker 1 plans the one-line fix →
Worker 0 dispatches Worker 2 → Worker 0 dispatches Worker 3 → Worker 1 re-runs this
gate):**

- File: `tests/optimizer/test_relay_id_projection.py`, function
  `test_relay_id_with_custom_pk_attname_avoids_lazy_load`, line ~178.
- Change the stale expectation `assert node_id.type_name == "CustomPKItemNode"` to
  the model-label form the default `model` strategy now emits. Mirror the Slice-4
  data-driven posture (`bld-slice-4-live_http.md`, derive from the ORM, not a
  hardcoded literal): `assert node_id.type_name == CustomPKItem._meta.label_lower`
  (which is `"tests.custompkitem"`). The `node_id.node_id == "abc-123"` assertion
  (line 179) and the optimizer `only_fields` projection assertions (the actual
  subject of this test — custom-pk attname projection) are UNCHANGED; only the
  emitted-`GlobalID` type-name expectation moves.
- Update the adjacent comment if it names the type-anchored payload as the wire
  form (the test's headline subject is the custom-pk *attname* projection, which the
  flip does not change — keep that framing; only the GlobalID round-trip line moves).
- After the fix: this slice's Worker 2 reruns `uv run ruff format .` +
  `uv run ruff check --fix .`; Worker 1 re-runs the full gate
  (`uv run pytest --no-cov` + gates 2-6) and confirms `1512 passed, 3 skipped` (the
  now-green test) with gates 2-6 still passing, then sets `bld-final.md` to
  `final-accepted`.

This is the ONLY build-caused failure; gates 2-6 already pass, so the re-run is
expected to flip directly to `final-accepted` once the one assertion is corrected.

---

## Out-of-scope / concurrent activity (recorded, NOT blocking)

- **`docs/dry/dry-0_0_9.md`** is dirty in the working tree (concurrent DRY cycle,
  per the build plan's build-wide context and `AGENTS.md` #33). It did NOT trip
  `git diff --check` (gate 6 clean), and it is not a file this build touched. Left
  untouched, out of scope.
- **Maintainer "archive 030" state.** The Slice-5 artifact recorded a transient
  pre-existing `import_spec_terms --check` mismatch from the concurrent spec-030
  archive; the Slice-5 bare `import_spec_terms` run incidentally reconciled it (now
  `OK`). Not a gate command here and not this build's responsibility; recorded for
  the maintainer's awareness only.
- The 3 skipped `pytest` tests are the standard default-invocation skips (no
  build-introduced skip); the 2 warnings are the pre-existing
  `Overriding setting DATABASES` `UserWarning`s in
  `examples/fakeshop/apps/products/tests/test_commands.py` (sharded-DB override),
  unrelated to this build.

---

### Deferred work catalog

The next spec author's reading list. Walked every per-slice and integration
artifact's `### Notes for Worker 1 (spec reconciliation)`, `### What looks solid`,
and `### Spec changes made (Worker 1 only)` sections, plus the integration pass's
`### Deferred work catalog (integration-relevant)`. Every item below is licensed by
the spec (cited) and tracked elsewhere — none is in-card spec-031 work left undone.

- **`callable` / `custom` decode path → `WIP-ALPHA-032-0.0.9` (Full Relay story).**
  Source: `bld-slice-3-decode_seam.md` (Plan DRY analysis + `decode_global_id`
  Step-2; review `### DRY findings`). Spec licence: Decision 4 / Decision 8 (spec
  line 98/408 — `callable` / `custom` effective strategies are **encode-only** in
  `0.0.9`; they have no `decode_global_id` branch, falling out of the predicate
  math). A consumer-owned paired decoder is deferred to card 032.
- **First consumer of `decode_global_id` / `registry.definition_for_graphql_name`
  → `WIP-ALPHA-032-0.0.9`.** Source: `bld-slice-3-decode_seam.md` Plan
  ("the forward-looking piece root `node(id:)` / `nodes(ids:)` … will consume … No
  shipped `0.0.9` path calls it yet") + `### Public-surface check`. Spec licence:
  Decision 8 / Decision 11 (spec line 57/68/418 — both helpers are internal
  forward-looking surfaces with no shipped `0.0.9` caller; root `node(id:)` /
  `nodes(ids:)` in card 032 is their first consumer; the latent breaking-default
  flip is undecodable until 032 ships, per the CHANGELOG `[Unreleased]` note).
- **Connection-aware optimizer planning → `WIP-ALPHA-033-0.0.9`.** Source:
  `bld-integration.md` `### Deferred work catalog (integration-relevant)`. Spec
  licence: Key glossary references / Dependency surfaces (spec line 69 — orthogonal
  to this card; `DjangoConnectionField`'s `edges { node { id } }` picks up the
  model-label payload through the same `resolve_typename` seam with no
  `connection.py` change).
- **`type+model` is a strategy bridge, NOT a rename-history alias map → `BACKLOG.md`
  item 39.** Source: `bld-integration.md` deferral list; `bld-slice-5-doc_card_wrap.md`
  (CHANGELOG / TODAY `type+model`-first sequence + rename-ordering caveat). Spec
  licence: Decision 9 (spec Revision 5 P2 + lines 446-454 — `type+model` decodes an
  old type-anchored ID only while its old GraphQL type name still resolves; a full
  rename-history alias map is post-`1.0.0`, documented in CHANGELOG `[Unreleased]`
  + `TODAY.md` by Slice 5).
- **Joint `0.0.9` version cut (NOT this card) → maintainer.** Source:
  `bld-integration.md` deferral list; `bld-slice-5-doc_card_wrap.md`
  (version-files-untouched verification). Spec licence: Decision 12 (spec lines 3 /
  113 — `pyproject.toml`, `__version__`, `tests/base/test_init.py::test_version`,
  `uv.lock` stay at `0.0.8`; no `## [0.0.9]` CHANGELOG heading promotion; the bump is
  owned by the joint cut across cards 029/030/031/032/033). On-disk version is
  correctly still `0.0.8` (verified: CHANGELOG bullets are under `[Unreleased]`
  only, version files absent from the working-tree diff).

Aside from these five tracked-elsewhere items, the build delivered the spec
end-to-end: all five slices reached `final-accepted` and the cross-slice integration
pass is `final-accepted`. The two Worker-1 spec edits made during the build are
recorded in their own slice artifacts (NOT deferrals): the Slice-4 line-102
`TODAY.md`-ownership reconciliation (`bld-slice-4-live_http.md`) and the Slice-5
`check_spec_glossary` spec-body-link addition for the two net-new GLOSSARY anchors
that brought the check to `OK: 31 terms` (`bld-slice-5-doc_card_wrap.md`). No
in-card spec-031 functional work is deferred — the only outstanding item is the
build-caused gate failure above (the stale `tests/optimizer/` assertion), which is
this build's own correction, routed to the Slice-2 loop, not a deferral.

---

## Spec changes made (Worker 1 only)

None. No spec gap, conflict, or inaccuracy surfaced during this gate pass. Per-spawn
spec status-line re-verification (spec lines 1-9): the `Status: planned — not
started` line + the unticked `## Slice checklist` are the intentional contract record
(spec line 5: "The Slice checklist below stays unticked as the contract record
(build progress is tracked in the build plan, not here)") — not a build tracker; no
header edit required. No predecessor reference broke. The two earlier Worker-1 spec
edits (Slice-4 line-102, Slice-5 link defs) were already made and recorded in their
own slice artifacts; nothing further is needed here.

---

## Outcome

`Status: revision-needed`. One build-caused `pytest` failure
(`tests/optimizer/test_relay_id_projection.py::test_relay_id_with_custom_pk_attname_avoids_lazy_load`,
a stale type-anchored emitted-`GlobalID` assertion invalidated by the Slice-2
default-flip) blocks `final-accepted`. Worker 0 re-dispatches the **Slice 2** loop
(Worker 2 applies the one-line model-label assertion fix per `### Owning slice + fix
contract`, then Worker 3 reviews), after which Worker 1 re-runs this final test-run
gate. Gates 2-6 already pass and there is no other build-caused failure, so the
re-run is expected to flip to `final-accepted` once the single assertion is
corrected. The build plan's final-box (`build-031-…md` line 52) stays `- [ ]` until
that re-run passes (Worker 0 owns the box; this gate does not tick it).

---

## Gate-fix: build report (Worker 2)

Applied the pinned one-line fix from `### Owning slice + fix contract`. This
resolves the **sole** gate failure
(`tests/optimizer/test_relay_id_projection.py::test_relay_id_with_custom_pk_attname_avoids_lazy_load`).
The failure is **Slice-2-owned** (the model-label default flip, spec Decision 9 /
`bld-slice-2-encode_seam.md`): the Slice-2 contract itself was correct — only this
sibling optimizer test's stale type-anchored assertion needed updating to match the
shipped model-label payload. No source, spec, build-plan, or other test changed.

### Files touched

- `tests/optimizer/test_relay_id_projection.py` — in
  `test_relay_id_with_custom_pk_attname_avoids_lazy_load`, changed the stale
  type-anchored assertion `node_id.type_name == "CustomPKItemNode"` to the
  data-driven `node_id.type_name == CustomPKItem._meta.label_lower` (resolves to
  `"tests.custompkitem"` for the test's inline `app_label = "tests"` /
  `CustomPKItem` model — derived from the ORM, NOT a hardcoded literal, mirroring
  the Slice-4 data-driven posture). Refreshed the adjacent comment to name the
  model-label slot under the default `model` strategy and explain the ORM-derived
  expectation. The `CustomPKItem` model is the inline class already declared in the
  test body and in scope at the assertion. ALL other assertions unchanged:
  `node_id.node_id == "abc-123"`, the `only_fields` custom-pk-attname projection
  (`"uuid" in plan.only_fields`, `"id" not in plan.only_fields`), the lazy-load /
  single-query assertions, and `result.data`.

### Tests updated

- `tests/optimizer/test_relay_id_projection.py::test_relay_id_with_custom_pk_attname_avoids_lazy_load`
  — the one stale GlobalID type-name assertion, now data-driven.

### Validation run

- `uv run ruff format .` — pass ("235 files left unchanged"; the standing
  `COM812`-vs-formatter warning is the pre-existing config noise noted in gate 4,
  not a failure).
- `uv run ruff check --fix .` — pass ("All checks passed!").
- `git status --short` classification: `M tests/optimizer/test_relay_id_projection.py`
  is this pass's **only slice-intended change**. All other `M` source/test/docs
  entries (`filters/`, `types/`, `registry.py`, `tests/types/`, `tests/filters/`,
  `examples/`, `CHANGELOG.md`, `KANBAN.*`, `docs/GLOSSARY.md`, `docs/TREE.md`,
  `docs/README.md`, `README.md`, `TODAY.md`, `db.sqlite3`, the spec + its terms CSV)
  are the **cumulative accepted Slice 1-5 + integration diff plus the Worker-1 spec
  edits** — EXPECTED, not reverted. `docs/dry/dry-0_0_9.md` is the **concurrent DRY
  cycle** (AGENTS.md #33) — EXPECTED, untouched. The `??` `bld-*.md` / `build-*.md`
  entries are this build's artifacts — EXPECTED. No unrelated tool churn from this
  pass.
- Focused confirm (explicit `--no-cov`, no `--cov*`):
  `uv run pytest tests/optimizer/test_relay_id_projection.py --no-cov` →
  **4 passed in 1.54s**. The previously-failing
  `test_relay_id_with_custom_pk_attname_avoids_lazy_load` now PASSES; the other 3
  tests in the file stay green. (Did not run the full repo suite — Worker 1's gate
  re-run owns that.)

### Implementation notes

- Used `CustomPKItem._meta.label_lower` (not a hardcoded `"tests.custompkitem"`) so
  the assertion tracks the model rather than a literal, robust to an `app_label` /
  model-name change. `label_lower` is the same Django-canonical accessor the
  Slice-2 `model` encoder emits (`definition.model._meta.label_lower`), so the
  test reads the wire payload against its own source of truth.

### Notes for Worker 3

Not applicable to this gate-fix pass (the fix routes Slice-2's loop: Worker 0 will
dispatch Worker 3 for review next). Single-line test-assertion change; no source,
no control-flow, no new logic.

### Notes for Worker 1

This is the only build-caused gate failure and it is now green. The Slice-2 contract
(model-label default flip) was correct as shipped — this was purely a stale sibling
optimizer-test assertion outside Slice 4's `examples/fakeshop/test_query/` boundary.
The top-level `Status:` line is left at `revision-needed` (Worker 1 owns the gate
re-run and the flip to `final-accepted`); the already-`final-accepted` slice
artifacts' status lines were not touched. Gates 2-6 already passed, so the full-gate
re-run is expected to confirm `1512 passed, 3 skipped` and flip directly to
`final-accepted`.

---

## Gate-fix: review (Worker 3)

Reviewed the gate-fix's single-file diff: `git diff -- tests/optimizer/test_relay_id_projection.py`.
The change lands in `test_relay_id_with_custom_pk_attname_avoids_lazy_load` (the
custom-pk-attname optimizer projection regression). The stale type-anchored
assertion `node_id.type_name == "CustomPKItemNode"` is replaced with the
data-driven `node_id.type_name == CustomPKItem._meta.label_lower`, and the adjacent
comment is refreshed to name the model-label slot under the default `model`
strategy. Everything else in the working tree is already-accepted Slice 1-5 +
integration work + the two Worker-1 spec edits + the concurrent
`docs/dry/dry-0_0_9.md` + maintainer "archive 030" state — out of this gate-fix's
scope (filtered via the `### Gate 1 failure detail` fix contract and `### Files
touched`).

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

None. The fix removes a hardcoded literal rather than adding one: it derives the
expected wire-payload type-name slot from the model's own
`CustomPKItem._meta.label_lower` — the same Django-canonical accessor the Slice-2
`model` encoder emits (`definition.model._meta.label_lower`). The test now reads the
emitted payload against its single source of truth, mirroring the Slice-4
data-driven posture (`bld-slice-4-live_http.md`, ORM-derived not hardcoded). No
parallel literal introduced; robust to an `app_label` / model-name change.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — `__all__` and the
re-export list are unchanged. The gate-fix touches one test file only; no public
export added, removed, or reordered. Consistent with the build's "no new public
exports" Definition of Done.

### CHANGELOG sanity

Not applicable; gate-fix did not modify `CHANGELOG.md` (diff scoped to one test file).

### Documentation / release sanity

Not applicable; gate-fix did not modify docs/release/KANBAN/archive surfaces (diff
scoped to `tests/optimizer/test_relay_id_projection.py`).

### What looks solid

- **Correct shipped behavior.** Under the default `model` strategy (Decision 9
  default flip), the emitted `GlobalID` type-name slot is the Django model label
  `app_label.modelname`. For the test's inline `CustomPKItem` (`app_label = "tests"`,
  model `CustomPKItem`, declared at `tests/optimizer/test_relay_id_projection.py:127`
  with `app_label = "tests"` at :132), `_meta.label_lower` is `"tests.custompkitem"`
  — exactly the value the gate-1 failure showed the test now receives. The old
  `"CustomPKItemNode"` was the stale type-anchored payload. The new expectation is
  correct.
- **Data-driven, not hardcoded.** The assertion references
  `CustomPKItem._meta.label_lower`, not the string `"tests.custompkitem"`. `CustomPKItem`
  is the inline model already in scope at the assertion (defined at :127, used at
  :182 inside the same `try` block). Robust to app_label / model-name drift.
- **No optimizer-coverage weakening.** The test's headline subject — the custom-pk
  attname projection — is untouched: `assert "uuid" in plan.only_fields` (:171) and
  `assert "id" not in plan.only_fields` (:172) remain, as does the single-query
  lazy-load gate `with django_assert_num_queries(1):` (:162) and `result.data` (:173).
  The other GlobalID round-trip assertion `node_id.node_id == "abc-123"` (:183) is
  unchanged. Only the type-name slot expectation moved. `numstat` is `6 2` — the 2
  deletions are the old comment line + old assertion; the 6 insertions are the
  expanded comment (4 lines) + the new assertion + comment continuation. No
  assertion removed.
- **No collateral.** No source change, no other test changed, no public-surface
  change; the diff is confined to the one function in the one file the fix contract
  named.

### Temp test verification

No temp tests created. The fix is a single data-driven test-assertion update with
no new control flow or logic; the focused run below is sufficient proof. Static
inspection helper (`scripts/review_inspect.py`) not run and not required — the diff
adds no source logic and touches no `.py` file under `django_strawberry_framework/`
(test-file-only, comment + one assertion).

### Notes for Worker 1 (spec reconciliation)

None. No spec ambiguity, no follow-up slice candidate. The Slice-2 contract
(model-label default flip, Decision 9) was correct as shipped; this was purely the
stale sibling optimizer-test assertion outside Slice 4's
`examples/fakeshop/test_query/` boundary, now corrected. The top-level `Status:`
line is left untouched (`revision-needed`) — Worker 1 owns the full-gate re-run and
the flip to `final-accepted`.

### Focused-test result

`uv run pytest tests/optimizer/test_relay_id_projection.py --no-cov` (explicit
`--no-cov`; no `--cov*` flag; did not run the full repo suite) → **4 passed in
1.51s**. The previously-failing
`test_relay_id_with_custom_pk_attname_avoids_lazy_load` now PASSES; the other 3
tests in the file stay green. Matches the contract's expected count (4 passed).

### Review outcome

`review-accepted`. The fix correctly updates the stale type-anchored assertion to the
shipped model-label payload (`CustomPKItem._meta.label_lower` = `"tests.custompkitem"`,
Decision 9 default flip), the assertion is data-driven (ORM-derived, not a hardcoded
literal), and it does not weaken the test's optimizer coverage (the `only_fields`
custom-pk-attname projection, the single-query lazy-load gate, and the other GlobalID
round-trip assertion are all unchanged). No High/Medium/Low findings, no DRY findings,
no public-surface change. Per the gate-fix contract, this review does NOT change the
top-level `Status:` line — Worker 1 owns the gate re-run and the final flip to
`final-accepted`.

---

## Final test-run gate — re-run (Worker 1)

Re-run on 2026-06-10 from the repo root, after the gate-fix loop closed
(Worker 2's `## Gate-fix: build report` applied the one-line data-driven assertion
fix; Worker 3's `## Gate-fix: review` set `review-accepted`). All 6 gate commands
re-run from a clean baseline; the sole prior failure is resolved.

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `1512 passed, 3 skipped` (2 warnings, 72.35s) |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — "System check identified no issues (0 silenced)." (exit 0) |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — "No changes detected" (exit 0) |
| 4 | `uv run ruff format --check .` | **PASS** — "235 files already formatted" (exit 0; the standing `COM812`-vs-formatter warning is pre-existing config noise, not a failure) |
| 5 | `uv run ruff check .` | **PASS** — "All checks passed!" (exit 0) |
| 6 | `git diff --check` | **PASS** — clean, exit 0 (no whitespace errors / conflict markers; `docs/dry/dry-0_0_9.md` did NOT trip the check) |

`--no-cov` was passed to gate 1 to opt out of `pytest.ini`'s auto-applied `--cov`
(a plain `uv run pytest` would be a forbidden coverage run). No `--cov*` flag was
used in any command. The full sweep ran across all three test trees (`tests/`,
`examples/fakeshop/tests/`, `examples/fakeshop/test_query/`); `FAKESHOP_SHARDED=1`
tests do not run under the default invocation (expected). The 3 skips are the
standard default-invocation skips and the 2 warnings are the pre-existing
`Overriding setting DATABASES` `UserWarning`s in
`examples/fakeshop/apps/products/tests/test_commands.py` — both unchanged from the
first gate run and unrelated to this build.

### Gate-fix confirmation (the sole prior failure is resolved)

The first gate run was `1 failed, 1511 passed, 3 skipped` — the one failure being
`tests/optimizer/test_relay_id_projection.py::test_relay_id_with_custom_pk_attname_avoids_lazy_load`
(a stale type-anchored emitted-`GlobalID` assertion invalidated by the Slice-2
default-flip to `model`). The Slice-2 gate-fix loop corrected that one assertion to
the data-driven `node_id.type_name == CustomPKItem._meta.label_lower`
(`"tests.custompkitem"`). This re-run confirms:

- The previously-failing test now PASSES (no longer in the failure list; the full
  suite is green).
- The count moved exactly as predicted: `1 failed / 1511 passed / 3 skipped` →
  `1512 passed / 3 skipped` (the one fixed test, ZERO failures).
- No NEW build-caused failure surfaced. The gate-fix was a single test-file
  assertion change with no source / control-flow impact, so no regression was
  possible — and the full sweep confirms it.
- Gates 2-6 still pass (unchanged from the first run; the gate-fix touched no
  source, docs, migrations, formatting, or whitespace).

`git diff --check` (gate 6) produced no output (exit 0): it flagged neither the
concurrent out-of-scope `docs/dry/dry-0_0_9.md` nor any file this build touched.
Confirmed clean.

### Deferred work catalog — confirmed present and complete

The `### Deferred work catalog` subsection above (under the first gate-run sections)
is present, unchanged, and complete. It carries the five tracked-elsewhere items,
each spec-licensed and routed to its owner:

1. `callable` / `custom` decode path → `WIP-ALPHA-032-0.0.9` (Decision 4 / 8;
   encode-only in `0.0.9`).
2. First consumer of `decode_global_id` / `registry.definition_for_graphql_name`
   → `WIP-ALPHA-032-0.0.9` (Decision 8 / 11; root `node(id:)` / `nodes(ids:)`).
3. Connection-aware optimizer planning → `WIP-ALPHA-033-0.0.9` (orthogonal to this
   card; same `resolve_typename` seam, no `connection.py` change).
4. `type+model` is a strategy bridge, NOT a rename-history alias map → `BACKLOG.md`
   item 39 (Decision 9; full alias map is post-`1.0.0`).
5. Joint `0.0.9` version cut (NOT this card) → maintainer (Decision 12; version
   files stay at `0.0.8`, no `## [0.0.9]` CHANGELOG heading).

Aside from these five, the build delivered the spec end-to-end (all five slices +
the cross-slice integration pass reached `final-accepted`). No in-card spec-031
functional work is deferred. The single build-caused gate failure that blocked the
first run was this build's own correction (routed through the Slice-2 loop) and is
now resolved — not a deferral.

---

## Outcome (re-run)

`Status: final-accepted`. All 6 gate commands pass on re-run: `pytest --no-cov` is
fully green at `1512 passed, 3 skipped` (the sole prior failure — the stale
`tests/optimizer/test_relay_id_projection.py` type-anchored assertion — is resolved
by the Slice-2 gate-fix, with ZERO failures and no new build-caused failure), and
gates 2-6 (`manage.py check`, `makemigrations --check --dry-run`,
`ruff format --check .`, `ruff check .`, `git diff --check`) all pass. The Deferred
work catalog is present and complete (five tracked-elsewhere items). This closes the
final test-run gate. Worker 0 now marks the build plan's final box
(`build-031-…md` line 52) `- [x]` and hands off to the maintainer. Worker 1 does NOT
tick that box (Worker 0 owns it) and does NOT commit.
