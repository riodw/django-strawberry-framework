# Package build plan: permissions / 0.0.10 (034)

Spec source: `docs/spec-034-permissions-0_0_10.md`
Target release: `0.0.10`
Date created: 2026-06-15
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

Pre-flight: passed on 2026-06-15 with a recorded baseline-dirty exception (see "Baseline-dirty out-of-scope files"); cleanup: removed the completed prior-cycle `build-033-connection_optimizer-0_0_9.md` (all boxes `[x]`, committed and recoverable), no `bld-*.md` artifacts existed, `docs/builder/worker-memory/` + `docs/builder/temp-tests/` + `docs/shadow/` confirmed empty (shadow re-cleared after the `review_inspect.py` smoke run). Checks: `review_inspect.py` runs (smoke on `registry.py`, exit 0); `.gitignore` lists all three scratch paths (`docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/`); `check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md` → `OK: 43 terms`, exit 0.

## Baseline-dirty out-of-scope files

The working tree was **not** clean at pre-flight. `git status --short` showed 50+ deletions, all under per-cycle scratchpad trees that no permissions slice touches:

- `docs/dry/dry-0_0_9.md` (deleted)
- `docs/review/rev-*.md` and `docs/review/rev-final.md` (~52 files deleted)

These are review-/DRY-cycle scratchpad files from a prior cycle. Per `AGENTS.md` ("Unexpected file modifications … are presumptively the maintainer's or another dev's in-progress work … ignore them as out-of-scope … never auto-revert without explicit maintainer authorization") and `START.md` ("Don't restore deleted files because you assume they belong"), these are recorded as the build baseline and treated as **out of scope**: no worker edits them, no worker reverts them. They are committed source of truth, so the maintainer can restore with `git checkout HEAD -- docs/review/ docs/dry/` if the deletions were unintended — flagged for the maintainer, not actioned by the build. No permissions slice writes anywhere under `docs/review/` or `docs/dry/`.

### Concurrent-sweep update (observed during Slice 1 planning, 2026-06-15)

During Worker 1's read-only Slice-1 planning pass the working tree changed again, presumptively from concurrent maintainer/tooling activity (verified, not caused by any worker):

1. **The `docs/review/` + `docs/dry/` deletions above reverted** — those files are present again (someone ran the `git checkout HEAD -- …` restore, or a sweep's git op touched them). Either way: still out of scope, still not a worker's concern.
2. **An em-dash→hyphen comment-normalization sweep** rewrote `—`/`–` to `-` inside **comments and docstrings only** (verified: no code semantics changed, the products cascade hooks are byte-identical apart from one comment's dash) across: `examples/fakeshop/apps/products/schema.py`, `examples/fakeshop/test_query/test_products_api.py`, `tests/base/test_init.py`, `tests/optimizer/test_extension.py`, `tests/test_connection.py`, `tests/test_list_field.py`, `tests/test_relay_node_field.py`.
3. **Concurrent kanban-DB regeneration** — `examples/fakeshop/db.sqlite3` (binary) + the generated `KANBAN.md` / `KANBAN.html` are modified together (a DB edit + `scripts/build_kanban_*` re-render).

**Standing instruction to every worker for this build:** these three are **out-of-scope concurrent work** — do NOT revert them, do NOT "clean them up." They overlap several slice-target files (the em-dash swaps sit in comments at lines no slice edits). Consequences:
- **Worker 2:** your post-ruff `git status --short` classification reverts only drift **your own** ruff invocation caused. The pre-existing em-dash comment swaps and the `db.sqlite3`/`KANBAN.*` changes predate your pass — leave them. Only edit the exact lines your slice requires.
- **Worker 3:** when reviewing a slice diff, treat comment-only em-dash swaps in a touched file as pre-existing concurrent churn, not Worker 2's change; scope findings to the slice's real edits.
- **Slice 5 (Worker 1 planning + Worker 2 build):** the card-move/glossary work edits `examples/fakeshop/db.sqlite3` and re-renders `KANBAN.md`/`KANBAN.html` itself. Plan and build Slice 5 against the **then-current** DB state (re-inspect at that point); the concurrent kanban regeneration may have moved the baseline. Flag any unexpected DB divergence to the maintainer rather than guessing.

This is flagged to the maintainer in Worker 0's handoff. No worker action beyond "do not revert."

### ⛔ STANDING GUARD — never discard working-tree changes (added after a Slice-2 incident)

**All build work is UNCOMMITTED** (the maintainer commits only at the end of the build). Therefore any command that discards working-tree modifications destroys accepted, **unrecoverable** work:

- **NEVER run** `git checkout -- <path>`, `git restore <path>`, `git stash`, `git reset --hard`, or any equivalent that reverts a tracked file to HEAD. HEAD is the pre-build state (e.g. `permissions.py` is a `NotImplementedError` stub at HEAD); reverting to it deletes the slice's implementation.
- **To undo your OWN ruff drift** (the only legitimate revert): re-edit the specific drifted lines back by hand with Edit, or note the drift — do NOT `git checkout` the file.
- **Temp-test cleanup:** delete ONLY files you created under `docs/builder/temp-tests/<slice>/` (use `rm`, target exact paths); never `git checkout` a source/test file as "cleanup."

*Incident (recovered):* during Slice-2 review a `git checkout -- django_strawberry_framework/permissions.py` discarded the accepted, uncommitted Slice-1 cascade implementation, reverting it to the HEAD stub. Worker 0 reconstructed the exact accepted bytes from the agent transcript Read result (`docs/builder/.../subagents/agent-ab981300a30c48b7b.jsonl`), restored the file (py_compile OK, `ruff format` 0-change ⇒ byte-canonical, `ruff check` clean), and re-ran the Slice-2 review to confirm green. No implementation logic was hand-authored; the restore is exact accepted content.

## Build-wide context flags

- **Version boundary (joint `0.0.10` cut owns the bump — spec [Decision 13]):** NO slice edits `pyproject.toml`, `__version__`, `tests/base/test_init.py::test_version`, or `uv.lock`; NO `CHANGELOG.md` release heading is promoted. On-disk version stays `0.0.9`; `0.0.10`-tagged surfaces ship under `[Unreleased]`. The `0.0.10` patch line is shared with `TODO-ALPHA-035-0.0.10`; the bump is the maintainer's joint-cut release act (and lands only after the still-pending `0.0.9` cut). **Exception that DOES land in this card:** the `__all__` exports pin in `tests/base/test_init.py` grows by two members in Slice 1 (`apply_cascade_permissions`, `aapply_cascade_permissions`) — exports are card-owned surface; the version constant in the same file is cut-owned and untouched.
- **CHANGELOG-edit permission is Slice-5-only (spec "Doc updates"):** `AGENTS.md` withholds `CHANGELOG.md` edits without explicit instruction. Slice 5's doc-update step is the explicit per-card grant — only the Slice 5 dispatch may touch `CHANGELOG.md`, and only under `[Unreleased]` (no version-heading promotion). Slices 1–4 must NOT edit `CHANGELOG.md`.
- **Slice 5 is DB-backed generated-doc work (spec line ~482; `BUILD.md` "Generated docs are DB-backed"; `worker-0.md` "Closing out a kanban card"):** `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` are rendered from `examples/fakeshop/db.sqlite3` via `scripts/build_*_md.py`. The card-move and glossary-flip mean **edit the DB via the Django ORM, then regenerate** — never hand-edit the rendered markdown. This card ships **no net-new glossary symbol** (the `aapply_cascade_permissions` twin documents inside the existing `apply_cascade_permissions` entry), so no new terms-CSV anchor is added; the existing `apply_cascade_permissions` glossary body is flipped `planned → shipped (0.0.10)` and re-statused entries are reconciled in the DB.
- **One new source module + tests (spec [Decision 3]):** the only new package file is `django_strawberry_framework/permissions.py` (Slice 1), exported from `__init__.py`. Its test twin is the new `tests/test_permissions.py`. Slices 2–3 add NO source change — they extend existing test files. Slice 4 uncomments existing products-schema hooks and extends `test_products_api.py`.
- **Staged seams (spec line ~381):** Slice 1 ships the whole runtime surface, so no cross-slice seams are expected. If review splits a slice, any staged-but-not-implemented seam uses an `AGENTS.md`-style `TODO(spec-034 Slice N)` anchor (paired with `NotImplementedError` where a call path must fail loudly), removed in the change that ships that slice.
- **Coverage is the maintainer's gate:** no worker runs `pytest` with `--cov*` flags. Worker-local validation is `uv run ruff format .` + `uv run ruff check --fix .`. The final gate runs `uv run pytest --no-cov` once.
- **Multi-DB test harness gate (spec [Decision 8] / Slice 1 Test plan):** `test_multi_db_subquery_pinned_to_caller_alias` needs a second DB alias that only exists under `FAKESHOP_SHARDED`; build it on the established `tests/optimizer/test_multi_db.py` in-test alias/router pattern rather than reinventing one. Sharded-specific coverage does not run under a bare `uv run pytest`.

## One-slice-at-a-time rule (short copy)

Build only one slice at a time. Do not start the next slice until the current slice's plan → build → review → final-verification → spec-reconciliation cycle is complete and Worker 1 has set the artifact `final-accepted`. After all five spec slices are accepted, run the cross-slice integration pass, then the final test-run gate. No maintainer pause between slices on the happy path; escalate genuine blockers immediately.

## DRY-first rule (short copy)

Before any code: is this the maximally DRY shape that stays readable? Duplicated logic, parallel data flows, near-copies between modules, and repeated string/key/tuple literals are build-time defects. Worker 1 plans for DRY; Worker 3 enforces it before accepting; Worker 1 re-checks DRY across slices at the integration pass. (Spec-specific DRY pressure points: the sync-misuse coroutine-probe reuses the `utils/querysets.py::apply_type_visibility_sync` shape rather than re-implementing it — [Decision 10]; the async variant wraps the *single* sync walk via `sync_to_async` so there is no sync/async fork to drift — [Decision 10]; the cascade is invoked through the shipped `get_queryset` seam at every pipeline so no second application point is introduced — [Decision 12]; `fields=` validation is one set-comparison helper, not per-call-site logic.)

## Artifact list

- `docs/builder/bld-slice-1-cascade_foundation.md`
- `docs/builder/bld-slice-2-optimizer_cooperation.md`
- `docs/builder/bld-slice-3-composition_pins.md`
- `docs/builder/bld-slice-4-products_activation.md`
- `docs/builder/bld-slice-5-doc_wrap.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] Slice 1: cascade foundation — `django_strawberry_framework/permissions.py` + package-root export (spec lines 56-63; Decision 4 / Decision 5 / Decision 8 / Decision 9 / Decision 10) -> `docs/builder/bld-slice-1-cascade_foundation.md`
- [x] Slice 2: optimizer cooperation + N+1 audit — no source change; Prefetch-downgrade / cacheable=False / zero-extra-queries / strictness-silence / FK-id-elision pins (spec lines 64-66; Decision 7 / Decision 12) -> `docs/builder/bld-slice-2-optimizer_cooperation.md`
- [x] Slice 3: composition pins — gates, connections, nodes, lists; no new code in filters/orders/connection/relay/list_field (spec lines 67-69; Decision 11 / Decision 12) -> `docs/builder/bld-slice-3-composition_pins.md`
- [x] Slice 4: fakeshop products activation + live HTTP — uncomment four cascade hooks, live coverage via `create_users(1)` across `Entry → Item → Category`, audit `is_private` seeders + re-pin affected assertions (spec lines 70-74) -> `docs/builder/bld-slice-4-products_activation.md`
- [x] Slice 5: doc updates + card-completion wrap — GLOSSARY flip + re-status, `docs/README.md` / `docs/TREE.md` / `TODAY.md` / `README.md`, `CHANGELOG.md` `[Unreleased]` (explicit permission grant), KANBAN card → Done via the kanban DB + re-render; no version-file edits (spec lines 75-76; Doc updates; Decision 13) -> `docs/builder/bld-slice-5-doc_wrap.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`
