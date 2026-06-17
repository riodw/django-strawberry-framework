# Review: `django_strawberry_framework/testing/`

Status: verified

Folder pass over `django_strawberry_framework/testing/` covering the two verified sibling files (`_wrap.py`, `relay.py`) and the package `__init__.py`. Both file artifacts (`rev-testing___wrap.md`, `rev-testing__relay.md`) are `verified`; neither forwarded a folder-level concern. This pass adds the cross-file checks (duplicated helpers, naming/error drift, repeated literals, import direction, circular-import risk, comment consistency, and the `__init__.py` export surface) and the explicit disposition of the `__init__.py` +2 change.

## DRY analysis

- None — the folder is a two-file consumer-facing test-helper surface plus a thin re-export `__init__.py`, and every shared mechanism the two files need is already single-sourced *outside* this folder. `_wrap.py` reuses the one shared `_is_database_failure` predicate from `_django_patches.py:129` (the wrap/unwrap defense-in-depth contract); `relay.py` delegates payload computation to the canonical `types/relay.py::encode_typename`, imports the strategy set + the two gate-message constants from `types/base.py`, and re-exports `types/relay.py::decode_global_id` verbatim. The two siblings share **no** helper, constant, literal, or near-copy with each other — they address orthogonal concerns (DB-connection wrapping vs Relay GlobalID minting) and have a disjoint import set. There is nothing to fold at folder scope, and pulling a "shared testing util" out of two functions that touch different subsystems would be a false consolidation.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** Both files fan strictly outward to already-single-sourced cores: `_wrap.py:27` imports `_is_database_failure` from `_django_patches.py:129` (no local re-implementation of the `_DatabaseFailure is not None and isinstance(...)` test); `relay.py:40-45` imports `STRING_GLOBALID_STRATEGIES` + `_RELAY_NODE_GATE_LEAD` / `_RELAY_NODE_GATE_INHERIT_TAIL` from `types/base.py` and `encode_typename` / `decode_global_id` from `types/relay.py`. `relay.py::global_id_for` reads the finalize-stamped `effective_globalid_strategy` rather than the raw setting, so it is consistent-by-construction with live emission. No folder-internal duplication.
- **Duplication risk in the folder.** None across siblings. The only per-file repeated literal flagged by the static overviews is the 4× `"global_id_for:"` message prefix inside `relay.py` (distinct human-readable error subjects, not a dispatch key — intentional, covered in the per-file artifact). `_wrap.py` has zero repeated literals. No literal, constant, or helper is shared between the two files, so there is no cross-file repeated-literal DRY candidate.

### Other positives

- **`__init__.py` export surface is correct and minimal.** `__all__ = ["safe_wrap_connection_method"]` (`testing/__init__.py:43`) exports exactly the one symbol that exists today, imported from `._wrap` at `:41`. The Relay helpers (`global_id_for` / `decode_global_id`) are deliberately **not** re-exported from the package root — they live at the `django_strawberry_framework.testing.relay` submodule path (per the card DoD and to keep `import django_strawberry_framework.testing` light, paying the `types`-package import cost only in suites that import the submodule). This is documented in the `__init__.py` docstring (`:16-26`) and matches GLOSSARY (`docs/GLOSSARY.md:43-46`).
- **The `__init__.py` +2 change is a doc-only future-version bump, not a premature export.** `git diff 14910230..HEAD -- testing/__init__.py` is a single hunk: the "Future exports" docstring line `0.0.12` → `0.0.14` (`testing/__init__.py:28-29`). No symbol was added to `__all__`; no unshipped `TestClient` / `AsyncTestClient` / `GraphQLTestCase` was imported or exported. The change is the *opposite* of the AGENTS.md/START.md "don't preemptively populate future-feature surfaces" hazard — it is a prose-only correction that makes the docstring **consistent** with `docs/GLOSSARY.md`, which marks `TestClient` (`:135,1311-1313`), `AsyncTestClient` (`:135`/`#testclient`), and `GraphQLTestCase` (`:87,600-606`) all as "planned for `0.0.14`". The forward-looking surfaces remain documented-only and unexported. No finding.
- **Import direction is a clean one-way fan-out; zero circular-import risk.** No package module imports `django_strawberry_framework.testing` (grep for `import ...\.testing` outside `testing/` returns nothing — the only consumer is consumer test suites). `_wrap.py` imports stdlib + `django.db.backends...BaseDatabaseWrapper` + `_django_patches`; `relay.py` imports `strawberry.relay` + `..exceptions` + `..types.base` + `..types.relay`. Both edges point outward to the package core; there is no `testing → testing` cross-edge between the two siblings and no back-edge from the core into `testing`. (Note: the `from django_strawberry_framework.testing import safe_wrap_connection_method` at `_wrap.py:89` is inside the function docstring's example block, not a real import.)
- **Naming and error-handling are consistent with the package idiom.** `relay.py` raises the branded `ConfigurationError` for all five mis-use gates; `_wrap.py` raises a targeted `TypeError` for a non-callable `wrapper` and otherwise degrades gracefully (returns `False`/install). The two files use distinct error vocabularies because they guard distinct contracts — no drift, no inconsistent shaping for the same failure class.
- **Both siblings are unchanged since baseline.** `git log 14910230..HEAD -- testing/` shows only commit `143c045f`, which touched `testing/__init__.py` (the doc bump above); `_wrap.py` and `relay.py` have empty diffs vs baseline and vs HEAD. `git diff HEAD -- testing/` is empty. Both per-file artifacts are `verified`.

### Summary

`django_strawberry_framework/testing/` is a clean, well-bounded two-file consumer test-helper surface. The two siblings (`_wrap.py`, `relay.py`) share no code with each other and each delegates to already-single-sourced machinery (`_django_patches._is_database_failure`; `types/relay.encode_typename` + `types/base` strategy constants), so folder-level DRY is correctly None. The `__init__.py` export surface is correct and minimal — `__all__` exports only the shipped `safe_wrap_connection_method`, and the Relay helpers stay at the submodule path by design. The +2 `__init__.py` change is a doc-only `0.0.12` → `0.0.14` future-version bump that brings the docstring into agreement with `docs/GLOSSARY.md`; it exports nothing premature and is the right kind of change (documented-only forward surface, no early `__all__` population). Import direction is a one-way fan-out with no circular-import risk and no back-edge into `testing`. No High / Medium / Low at folder scope. No-source-edit folder pass (shape #3 → #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, 270 files left unchanged (pre-existing COM812-vs-formatter advisory notice only).
- `uv run ruff check .` — pass, "All checks passed!".

### Notes for Worker 3
- Shadow overviews used: `docs/shadow/django_strawberry_framework__testing____init__.overview.md` (1 import, 0 symbols, 0 markers, 0 repeated literals — confirms `__init__.py` is a pure re-export), plus the two sibling overviews (`__testing___wrap`, `__testing__relay`). Shadow line numbers not canonical; artifact cites original source.
- Folder-pass cross-checks performed: (a) sibling repeated-literal compare — no literal shared between `_wrap.py` and `relay.py`; only per-file `relay.py` 4× `"global_id_for:"` (already dispositioned in `rev-testing__relay.md`). (b) import-direction — one-way outward fan, no `testing → testing` cross-edge, no core → `testing` back-edge (grep clean). (c) `__init__.py` export surface — `__all__` exports only the shipped `safe_wrap_connection_method`; Relay helpers correctly submodule-path-only.
- The `__init__.py` +2 change (`git diff 14910230..HEAD`) is a doc-only `0.0.12`→`0.0.14` future-version bump in the "Future exports" section; **exports nothing premature**, and is now consistent with `docs/GLOSSARY.md` (TestClient/AsyncTestClient/GraphQLTestCase all "planned for `0.0.14`"). No source-logic change anywhere in the folder.
- No GLOSSARY-only fix in scope — `docs/GLOSSARY.md:43-46` (testing subpackage symbol list) accurately describes the current export surface and the submodule-path discipline; the future-version table rows match the bumped docstring.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits warranted. The `__init__.py` module docstring (`testing/__init__.py:1-39`) accurately describes the current export (`safe_wrap_connection_method`), the deliberately-not-re-exported Relay helpers and the import-weight rationale, and the future `0.0.14` surfaces — and the +2 change already corrected the only stale element (the future-version anchor) to match GLOSSARY. The two sibling files' comments/docstrings were each accepted in their own verified cycles. No stale comments, no obsolete TODOs (all three shadow overviews report zero TODO anchors).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. This folder pass makes no source change (empty `git diff HEAD -- testing/`), so there is nothing to record; and per AGENTS.md #21 / START.md, `CHANGELOG.md` is not touched unless explicitly instructed, and the active plan (`docs/review/review-0_0_10.md`) records no changelog requirement for review cycles.

---

## Verification (Worker 3)

No-source-edit folder pass (shape #5). Baseline HEAD `58ca2def`; the prompt-cited `14910230` is the doc-bump predecessor. All claims independently confirmed.

### Logic verification outcome
High / Medium / Low all None at folder scope — nothing to address; verified there is no missed defect (no premature export):
- **Zero this-cycle edits.** `git diff HEAD -- django_strawberry_framework/testing/` empty. `git log 14910230..HEAD -- testing/` = only `143c045f` (the doc bump), not this cycle.
- **Export surface minimal & correct (no premature export).** Read `testing/__init__.py` directly: `__all__ = ["safe_wrap_connection_method"]` (line 43) — exactly the one shipped symbol, imported from `._wrap` (line 41). No `TestClient` / `AsyncTestClient` / `GraphQLTestCase` import or export anywhere in the module; `global_id_for` / `decode_global_id` correctly NOT re-exported (submodule-path-only per DoD).
- **Future-export mention is docstring-only.** `git diff 14910230..HEAD -- testing/__init__.py` is a single hunk: the "Future exports … planned for" anchor `0.0.12`→`0.0.14` (line 28-29). No `__all__` change, no unshipped import. GLOSSARY confirms `TestClient` (`:135`,`:1311-1313`), `AsyncTestClient` (`:135`/`:1315`), `GraphQLTestCase` (`:87`,`:600-606`) all "planned for `0.0.14`" — the docstring is now consistent, not premature. This is the *opposite* of the don't-preemptively-populate hazard.
- **One-way acyclic imports.** `grep -rn "import.*\.testing"` over `django_strawberry_framework/` (excluding `testing/`) = NO BACK-EDGE. `_wrap.py` imports stdlib + `django.db.backends…BaseDatabaseWrapper` + `_django_patches._is_database_failure`; `relay.py` imports `strawberry.relay` + `..exceptions` + `..types.base` + `..types.relay`. Both fan strictly outward; no `testing→testing` cross-edge.

### DRY findings disposition
Folder DRY None confirmed sound. The two siblings are orthogonal (DB-connection wrapping vs Relay GlobalID minting), share no helper/constant/literal, and each delegates to already-single-sourced cores: `_wrap.py` reuses `_django_patches._is_database_failure`; `relay.py` imports `STRING_GLOBALID_STRATEGIES` + the two gate-message constants from `types/base.py` and delegates payload to `types/relay.encode_typename`. The only per-file repeated literal (4× `"global_id_for:"`) is dispositioned in the per-file artifact. Pulling a "shared testing util" out of two disjoint-subsystem functions would be false consolidation. No carry-forward.

### Temp test verification
None. No source change; both siblings verified in their own cycles. No temp test warranted.

### Shape #5 / preamble / changelog checks
- Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` — confirmed.
- No High/Med/Low to forward; no GLOSSARY-only fix (the GLOSSARY rows match the bumped docstring and the current export surface).
- Changelog **Not warranted**: `git diff HEAD -- CHANGELOG.md` empty; both citations present (AGENTS.md #21 + active-plan silence). Internal-only framing honest — the +2 is a doc bump exporting nothing public.
- `uv run ruff format --check django_strawberry_framework/testing/` = 3 files already formatted; `uv run ruff check` = All checks passed.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `testing/` folder-pass checklist box in `docs/review/review-0_0_10.md`.

---

## Iteration log

(none)
