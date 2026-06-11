# Package build plan: full_relay / 0.0.9 (032)

Spec source: `docs/spec-032-full_relay-0_0_9.md`
Target release: `0.0.9`
Date created: 2026-06-11
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Pre-flight: passed on 2026-06-11; baseline: clean at start; cleanup: prior-cycle `build-031-globalid_encoding-0_0_9.md` + seven `bld-*.md` artifacts deleted (tracked deletions now in the working tree as expected pre-flight churn), `worker-memory/`, `docs/shadow/`, `temp-tests/` cleared and re-seeded; `scripts/review_inspect.py` smoke-ran OK; `scripts/check_spec_glossary.py --spec docs/spec-032-full_relay-0_0_9.md` exited 0 (38 terms OK).
Baseline-dirty out-of-scope files: none (the eight `D docs/builder/*.md` entries are this build's own pre-flight cleanup; workers do not restore them).
Build-wide context flags:

- **Joint-cut version boundary (spec Decision 13):** this card never bumps `pyproject.toml`, `__version__`, `tests/base/test_init.py::test_version`, or `uv.lock` — the on-disk version stays `0.0.8`; the `0.0.9` bump is owned by the joint cut.
- **Pre-`033` optimizer posture (spec Decision 12):** every connection (root or synthesized) derives an empty optimizer plan until `WIP-ALPHA-033-0.0.9` lands; live tests assert behavior, not SQL shape; strictness mode does NOT flag nested-connection lazy loads.
- **CHANGELOG permission:** Slice 7 carries the explicit per-card `CHANGELOG.md` edit grant; no other slice touches it.
- **Generated docs are DB-backed:** Slice 7's `KANBAN.md` / `docs/GLOSSARY.md` edits go through the Django ORM + regenerate scripts, never hand-edits of the rendered markdown.

## Artifact list

- `docs/builder/bld-slice-1-validation_diagnostics.md`
- `docs/builder/bld-slice-2-root_node_fields.md`
- `docs/builder/bld-slice-3-relation_shapes.md`
- `docs/builder/bld-slice-4-cursor_conformance.md`
- `docs/builder/bld-slice-5-testing_relay.md`
- `docs/builder/bld-slice-6-library_activation.md`
- `docs/builder/bld-slice-7-doc_card_wrap.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: schema-validation diagnostics (Decision 8) -> `docs/builder/bld-slice-1-validation_diagnostics.md`
- [x] Slice 2: root `node(id:)` / `nodes(ids:)` — `DjangoNodeField` / `DjangoNodesField` (Decisions 3/4/5) -> `docs/builder/bld-slice-2-root_node_fields.md`
- [x] Slice 3: relation-as-Connection upgrade — `Meta.relation_shapes` + Phase-2.5 synthesis (Decisions 6/7) -> `docs/builder/bld-slice-3-relation_shapes.md`
- [x] Slice 4: cursor-contract conformance + permission integration (Decisions 9/5) -> `docs/builder/bld-slice-4-cursor_conformance.md`
- [x] Slice 5: public `testing/relay.py` helpers (Decision 10) -> `docs/builder/bld-slice-5-testing_relay.md`
- [x] Slice 6: fakeshop library activation (Decision 12) -> `docs/builder/bld-slice-6-library_activation.md`
- [x] Slice 7: doc updates + card-completion wrap (CHANGELOG grant; DB-backed KANBAN/GLOSSARY) -> `docs/builder/bld-slice-7-doc_card_wrap.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
