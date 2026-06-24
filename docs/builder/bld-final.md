# Build: Final test-run gate — form_mutations / 0.0.12 (038)

Spec reference: `docs/SPECS/spec-038-form_mutations-0_0_12.md`
Build plan: `docs/builder/build-038-form_mutations-0_0_12.md`
Status: final-accepted

Worker 1 final test-run gate. All six slices (1, 2, 3, 4, 5a, 5b) and the
cross-slice integration pass (`bld-integration.md`, including the I1 normalizer
consolidation + the I2 `Item.attachment` package-`tests/`-tree fixture sweep) are
`final-accepted`. This gate is the comprehensive backstop before maintainer handoff:
it runs the full `pytest` sweep across all three test trees plus the Django
consistency checks and the lint/format/diff gate, and assembles the deferred-work
catalog. It does NOT inspect line coverage (the maintainer's / CI's gate).

Ran from the repo root on 2026-06-23. Working-tree baseline matches the expected
build-038 state: all six slices' source/test edits + I1 (`utils/inputs.py`,
`mutations/sets.py`, `forms/inputs.py`) + I2 (`tests/mutations/test_sets.py`,
`tests/mutations/test_inputs.py`, `tests/filters/test_sets.py`); the net-new
`django_strawberry_framework/forms/`, `tests/forms/`, `examples/.../products/forms.py`,
and the source-only `examples/fakeshop/apps/products/migrations/0002_item_attachment.py`
are present. The carve-out files (`examples/fakeshop/db.sqlite3`, `KANBAN.md`,
`KANBAN.html`, `docs/GLOSSARY.md`, `docs/feedback.md`) are dirty as expected from the
concurrent-writer + Slice-5b regenerate state per the build-plan flags — NOT touched
by this gate. `manage.py migrate` was NOT run (the `0002` migration is intentionally
source-only / un-applied to the committed `db.sqlite3`).

---

## Gate command results

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `2366 passed, 4 skipped, 4 xfailed in 127.20s` (exit 0) |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).` |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected` (exit 0) |
| 4 | `uv run ruff format --check .` | **PASS** — `277 files already formatted` (exit 0) |
| 5 | `uv run ruff check .` | **PASS** — `All checks passed!` (exit 0) |
| 6 | `git diff --check` | **PASS** — no whitespace errors / conflict markers (exit 0) |

### Gate 1 — `uv run pytest --no-cov` (full sweep, all three test trees)

PASS. **2366 passed, 4 skipped, 4 xfailed, 0 failed** in 127.20s (exit 0). The
explicit `--no-cov` opted out of `pytest.ini`'s auto-applied `--cov` (no coverage
inspected — the maintainer's gate). All three `AGENTS.md` test trees ran in the one
invocation, confirmed by represented node ids in the run:

- Package `tests/` — e.g. `tests/utils/test_typing.py`, `tests/utils/test_strings.py`
  (and the full `tests/mutations/`, `tests/forms/`, `tests/filters/` set).
- Per-app non-live `examples/fakeshop/apps/*/tests/` — e.g.
  `apps/products/tests/test_services.py`, `apps/products/tests/test_schema.py`,
  `apps/products/tests/test_commands.py`, `apps/library/tests/test_schema.py`; plus the
  project-level `examples/fakeshop/tests/` (`test_export_schema.py`,
  `test_inspect_django_type.py`).
- Live tier `examples/fakeshop/test_query/` — e.g. `test_kanban_api.py`,
  `test_library_api.py`, `test_uploads_api.py`, `test_products_api.py`.

`FAKESHOP_SHARDED` was NOT set (those tests are out of the default invocation per
`AGENTS.md`). The two most-likely failure sources the gate prompt flagged did **not**
materialize: (a) no additional Slice-4 `Item.attachment`-column staleness surfaced in
the example/live trees — the I2 sweep had only swept the package `tests/` tree, but
Slice 4 authored its own `examples/.../test_products_api.py` against the new column, so
no example/live test hardcoded `Item`'s old columns; (b) no generated-doc-freshness
test (regenerate-and-diff of `KANBAN.md` / `docs/GLOSSARY.md`) went red against the
concurrent-writer mixed DB state.

### Gate 2 — `uv run python examples/fakeshop/manage.py check`

PASS. `System check identified no issues (0 silenced).` No model/admin/url drift.

### Gate 3 — `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`

PASS. `No changes detected` (exit 0). The Slice-4 `Item.attachment` migration
`0002_item_attachment.py` already exists, so model state is migration-consistent and
no un-generated migration is outstanding. `migrate` was NOT run (the `0002` migration
is intentionally source-only / un-applied to the committed `db.sqlite3`).

### Gate 4 — `uv run ruff format --check .`

PASS. `277 files already formatted` (exit 0). Read-only; no `--fix` passed. (The
`COM812 may cause conflicts with the formatter` line is the standing repo config
warning, not a format failure — the `--check` exit code is 0.)

### Gate 5 — `uv run ruff check .`

PASS. `All checks passed!` (exit 0). Read-only lint; no `--fix`.

### Gate 6 — `git diff --check`

PASS. No whitespace errors or conflict markers anywhere in the working tree (exit 0).

---

### Deferred work catalog

Per BUILD.md, this catalog walks every per-slice + integration artifact's
spec-reconciliation / `What looks solid` / `Notes for Worker 1` sections and surfaces
every explicitly-deferred item. It is the next spec author's / maintainer's reading
list. Nothing was deferred beyond the items below.

**Doc-debt / source follow-ups (out of spec-038 contract):**

- **(a) `docs/TREE.md` stale `mutations/` "planned by TODO-ALPHA-036-0.0.11" line.**
  Source: Slice 5a + 5b `Notes for Worker 1`; `bld-integration.md` "Deferred
  follow-ups". `docs/TREE.md` still renders `mutations/` as
  `# planned by TODO-ALPHA-036-0.0.11` despite `mutations/` shipping in `0.0.11`
  (`DONE-036`). This is **spec-036 doc debt, OUT of spec-038's contract** — Worker 1
  edits only the active spec, never source `TREE.md` here. No licensing spec line (it
  is pre-existing debt from a prior build). Maintainer / next-author follow-up.

- **(b) DONE-038 card-body free-text `Status: In progress` cosmetic.** Source: Slice 5b
  `### Final verification` (item 4b); `bld-integration.md` "Deferred follow-ups". The
  rendered DONE-038 card body shows `Status: In progress` (vs sibling DONE-037's
  `Status: Shipped`). It was already `In progress` at HEAD (pre-existing free-text,
  independent of the workflow `status.key=done`, which is correct); outside Slice-5b's
  named scope. Not a defect — cosmetic. A one-line DB-backed `CardItem.text` →
  `"Shipped"` + re-render (matching DONE-037) if the maintainer wants the DONE-card
  convention nicety.

- **(c) Slice-1 Low: `_model_less_relation_annotation` `queryset=None` → raw
  `AttributeError`.** Source: Slice 1 `Notes for Worker 1` / Open-Low;
  `bld-integration.md` Step-5 walk + "Deferred follow-ups". A plain-`Form`
  `ModelChoiceField` declared with no `queryset` raises a raw `AttributeError` instead
  of a `ConfigurationError`. Out-of-spec input shape, reviewed-and-accepted as a Low at
  Slice 1 (spec does not require the graceful raise for this shape). Robustness nicety
  for a future slice / card; not a cross-slice duplication, so not part of the I1 loop.

- **(d) Spec `docs/`-vs-`docs/SPECS/` self-reference residual.** Source: build-plan
  "Build-wide context flags" (spec path discrepancy); `bld-integration.md` "Deferred
  follow-ups". The live spec is `docs/SPECS/spec-038-form_mutations-0_0_12.md`, but the
  spec prose self-references `docs/spec-038-...` (in `docs/`, not `docs/SPECS/`) in
  Decision 1 / Definition-of-done item 1 / the DoD spec-glossary command path. Cosmetic
  spec-internal inconsistency; not a blocker (all plans/builds/reviews used the
  `docs/SPECS/` path). Worker 1 may reconcile in a future spec-touching pass or leave to
  the next-author `docs/SPECS/NEXT.md` Step-8 archive sweep.

**Future-card test pin (carry-forward DRY):**

- **(e) `tests/utils/` direct pin for `normalize_field_name_sequence` before the
  0.0.13 serializer card.** Source: `bld-integration.md` I1 recommended fix + Worker-2
  `Notes for Worker 3` + Worker-3 `Notes for Worker 1`. The I1-lifted shared helper
  `utils/inputs.py::normalize_field_name_sequence(value, *, label, flavor)` is currently
  pinned only indirectly (through the two delegations exercised by
  `tests/mutations/test_sets.py` + `tests/forms/test_inputs.py`). A direct
  `tests/utils/test_inputs.py` case over both `flavor` strings + the bare-string +
  duplicate raises is the cleaner pin before the `0.0.13` `SerializerMutation` card
  (`TODO-ALPHA-039-0.0.13`) adds a third reader. Flagged at-discretion / non-blocking;
  not added, to avoid over-scoping the consolidation.

**Retrospective lesson (not a deferral, recorded for the catalog):**

- **(f) I2 lesson — a model-column add must sweep all three test-tree fixtures.**
  Source: `bld-integration.md` I2 consolidation pass + Worker-1 integration re-run
  memory. The Slice-4 `Item.attachment` `FileField` add went uncaught in the package
  `tests/` tree until the integration consolidation loop, because that tree was last
  fully run before Slice 4 and several fixtures hardcoded `Item`'s old editable-column
  set. Lesson for future builds: a model-column add must grep-sweep all three test
  trees (package `tests/`, per-app `examples/fakeshop/apps/*/tests/`, live
  `examples/fakeshop/test_query/`) for hardcoded column assumptions in the same change,
  not rely on the final gate to surface them. (The fix landed in this build — I2 — so
  this is a workflow note, not outstanding work.)

**Concurrency-coordination items for the maintainer (reconcile at commit; NOT build
defects):**

- **(g1) Mixed `examples/fakeshop/db.sqlite3` / `KANBAN.md` / `KANBAN.html` /
  `docs/GLOSSARY.md` diff.** Source: build-plan "Build-wide context flags" (Slice-5 DB
  writes apply on top of concurrent work, maintainer-authorized 2026-06-23) + Slice 5b
  `### Final verification`. A concurrent writer intermittently rewrites
  `db.sqlite3` with semantic kanban data; per maintainer direction, Slice 5b's DB-backed
  card move + GLOSSARY promotion were applied on top of that concurrent state WITHOUT
  reverting it. Consequence: the regenerated `KANBAN.*` / `docs/GLOSSARY.md` reflect
  BOTH the concurrent edits AND the 038 card move. The `git diff db.sqlite3 clean`
  verification was correctly NOT applicable (the DB legitimately diverged); Slice 5b
  proved its writes via the two-consecutive-regenerate byte-stability check instead.
  **The maintainer reconciles this mixed diff at commit** — it is a coordination point,
  not a build defect. (This gate left all four files untouched.)

- **(g2) Un-applied `products.0002` migration on the committed `db.sqlite3`.** Source:
  build-plan flags + Slice 4 artifact + this gate's prompt. The Slice-4
  `0002_item_attachment.py` migration is intentionally **source-only / un-applied** to
  the committed `db.sqlite3` (the live tests run on pytest-django's ephemeral DB, which
  applies all migrations fresh, so they exercise the new column without the committed DB
  needing it). `makemigrations --check` reports "No changes" (model state matches the
  migration graph); `migrate` was NOT run. Maintainer note: the column is in the
  migration source and exercised by the test suite, but the committed `db.sqlite3` does
  not carry the applied migration — intentional and per-plan.

---

## Outcome

**All six gate commands PASS. Status: `final-accepted`.**

The full `pytest` sweep (2366 passed / 0 failed across all three test trees), the two
Django consistency checks, and the three lint/format/diff gates all pass. No re-loop is
needed — no owning slice to route back. The build delivers the spec end-to-end; the
deferred-work catalog above captures the (out-of-038-contract) doc debt, the
future-card test-pin opportunity, the I2 retrospective lesson, and the
concurrency-coordination items the maintainer reconciles at commit.

The build is **READY for maintainer handoff.** Worker 0 may mark the final checklist
box `- [x]`. The maintainer reviews the whole build, then commits the source/test
changes + every `bld-*.md` artifact + the completed plan + the spec edits, reconciling
the mixed `db.sqlite3` / `KANBAN.*` / `docs/GLOSSARY.md` diff (item g1) and noting the
un-applied `products.0002` migration (item g2) at commit time.
