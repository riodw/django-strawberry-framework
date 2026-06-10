# Package build plan: globalid_encoding / 0.0.9 (031)

Spec source: `docs/spec-031-globalid_encoding-0_0_9.md`
Target release: `0.0.9`
Date created: 2026-06-09
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

Pre-flight: passed on 2026-06-09; baseline: clean (`git status --short` empty before cleanup); cleanup: prior-cycle spec-030 artifacts removed (`build-030-connection_field-0_0_9.md` + seven `bld-*.md`), `docs/builder/worker-memory/` re-seeded with four empty files, `docs/shadow/` and `docs/builder/temp-tests/` cleared. Pre-flight checks: (1) working tree clean; (2) `scripts/review_inspect.py django_strawberry_framework/types/relay.py --output-dir docs/shadow --stdout` ran; (3) old build artifacts deleted and all new plan/bld paths verified absent; (4) `.gitignore` lists `docs/builder/worker-memory/`, `docs/shadow/`, `docs/builder/temp-tests/`; (5) scratch dirs cleared; (6) `scripts/check_spec_glossary.py --spec docs/spec-031-globalid_encoding-0_0_9.md` → `OK: 29 terms`.

## Baseline-dirty out-of-scope files

None. The working tree was clean at pre-flight. The only working-tree changes are this cleanup's tracked-file deletions of the prior spec-030 build artifacts (eight files), which the maintainer commits alongside this build cycle. Workers do not touch unrelated files.

## Build-wide context flags

- **Version-bump owner: the joint `0.0.9` cut, NOT this card** (spec Decision 12). This card's slices land within the `0.0.9` line and never bump the version. Leave `pyproject.toml`, `django_strawberry_framework/__init__.py::__version__`, `tests/base/test_init.py::test_version`, and `uv.lock` UNCHANGED. On-disk version stays `0.0.8`. No CHANGELOG release-heading promotion — Slice 5 edits live under `[Unreleased]` only.
- **Breaking default flip (spec Decision 9).** Slice 2 flips the package-default `GlobalID` payload from the (DONE-015) type-anchored form to the Django model label (`products.item:<pk>`). This is a breaking wire-format change, acceptable pre-`1.0.0`, opt-out via the `type` strategy. Slice 4's live-test churn (every emitted-AND-filter-input `GlobalID` assertion moves to the model-label form) is the expected blast radius, not unrelated drift.
- **`GlobalID` filter validation co-lands with the flip (spec Decision 13).** `filters/base.py::_decode_and_validate_global_id` is made strategy-aware in Slice 2 (not a later slice) so emitted model-label IDs round-trip through the filter layer. The earlier "filtering unchanged" framing is corrected by the spec's Revision 5.
- **CHANGELOG-edit permission is granted ONLY in Slice 5** (spec Doc updates / DoD item 7). `AGENTS.md` withholds CHANGELOG edits by default; the Slice 5 Worker 2 dispatch prompt must name the `CHANGELOG.md` `### Changed` + `### Added` `[Unreleased]` edits explicitly. No other slice touches `CHANGELOG.md`.
- **Net-new GLOSSARY symbols.** `Meta.globalid_strategy` and `RELAY_GLOBALID_STRATEGY` have NO glossary heading at spec-authoring time and are intentionally absent from `spec-031-globalid_encoding-0_0_9-terms.csv`. Slice 5 creates their glossary entries (DB-backed regenerate per Worker 0 "Closing out a kanban card"); the card-close terms-CSV/`import_spec_terms` reconciliation happens at maintainer/closeout time, not mid-build.
- **No new module.** Encode/decode land in the existing `django_strawberry_framework/types/relay.py`; the only registry addition is `definition_for_graphql_name` in `registry.py` (spec Decision 11). Tests mirror source: `tests/types/test_relay_interfaces.py`, `tests/types/test_base.py`, `tests/filters/test_base.py`, `tests/test_registry.py`, plus live `examples/fakeshop/test_query/`.
- **Sequential dependency.** Slices 1→2→3→4 each build on the prior (1 stores the strategy + precedence; 2 reads it to encode + records `effective_globalid_strategy`; 3 reads the recorded field to decode; 4 proves it live). Slice 5 (docs + wrap) lands last. No slice may start before the prior slice reaches `final-accepted`.
- **Coverage is the maintainer's / CI's gate.** Workers never run pytest with `--cov*`. Worker-local validation is `uv run ruff format .` + `uv run ruff check --fix .`. The final gate runs `uv run pytest --no-cov` once.

## One-slice-at-a-time rule

Build only one slice at a time. Do not start the next slice until the current slice's plan/build/review/verification/spec-reconciliation cycle is complete (Worker 1 sets the artifact `Status: final-accepted` and Worker 0 marks the box). After all five slices are built, run the cross-slice integration pass, then the final test-run gate.

## DRY-first rule

Every plan, implementation, and review pass answers one question first: is this the maximally DRY shape that stays readable? Duplicated logic, parallel data flows, near-copies between modules, and repeated string/key/tuple literals are build-time defects. Worker 1 plans for DRY; Worker 3 enforces it; Worker 1 re-checks DRY across slices at integration. Specific watch points for this build: the shared `_validate_globalid_strategy` rule must serve BOTH the `Meta` and `RELAY_GLOBALID_STRATEGY` paths (one validator, two call sites with source-specific error text); the strategy→payload-shape mapping (`model`/`type`/`type+model`/`callable`/`custom`) recurs in the encoder, the decode Step-2 enforcement, and the strategy-aware filter — it must be one named source of truth, not three parallel literal sets.

## Artifact list

- `docs/builder/bld-slice-1-globalid_strategy_key.md`
- `docs/builder/bld-slice-2-encode_seam.md`
- `docs/builder/bld-slice-3-decode_seam.md`
- `docs/builder/bld-slice-4-live_http.md`
- `docs/builder/bld-slice-5-doc_card_wrap.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: `Meta.globalid_strategy` net-new key (validated + stored on the definition) + `RELAY_GLOBALID_STRATEGY` settings read + the precedence resolver (spec `## Slice checklist` lines 84-88; Decisions 5/6/7) -> `docs/builder/bld-slice-1-globalid_strategy_key.md`
- [x] Slice 2: the encode seam — strategy-parameterized `resolve_typename` injection + the four encoders + the default flip to `model` + strategy-aware `GlobalID` filter validation (spec `## Slice checklist` lines 89-95; Decisions 3/4/9/10/13) -> `docs/builder/bld-slice-2-encode_seam.md`
- [x] Slice 3: the decode seam — `decode_global_id` resolve-then-enforce dispatch + `registry.definition_for_graphql_name` + encoder/decoder symmetry + transitional `type+model` (spec `## Slice checklist` lines 96-100; Decision 8) -> `docs/builder/bld-slice-3-decode_seam.md`
- [x] Slice 4: live HTTP coverage on a Relay-Node-shaped fakeshop type (emitted model-label ID, the headline filter round-trip, the deterministic `type`-opt-out) (spec `## Slice checklist` lines 101-104) -> `docs/builder/bld-slice-4-live_http.md`
- [x] Slice 5: doc updates + card-completion wrap (GLOSSARY net-new entries, docs/README, docs/TREE, TODAY, README, the per-card CHANGELOG permission grant, KANBAN move) (spec `## Slice checklist` lines 105-113; Decisions 9/12) -> `docs/builder/bld-slice-5-doc_card_wrap.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
