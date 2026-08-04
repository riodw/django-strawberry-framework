# Build plan: spec-048 secure output and error defaults

Spec source: [`docs/spec-048-secure_output_defaults-0_0_17.md`][spec-048]
Target release version: `0.0.17`
Date created: 2026-08-03
Card: `TODO-ALPHA-048-0.0.17` - Secure output and error defaults: drop file path, fail-closed debug, prod error policy

## Pre-flight outcome and working-tree baseline

The tree was **dirty on purpose** at pre-flight. Card `047` (spec-047 resource policy, `0.0.16`) had been built in this same worktree and was awaiting the maintainer's commit; its output is the baseline this build sits on, not churn. Baseline-dirty files this build neither reverted nor tidied:

- `django_strawberry_framework/resource_policy.py`, `extensions/resource_policy.py`, `utils/context.py` (new in `047`)
- `django_strawberry_framework/connection.py`, `conf.py`, `list_field.py`, `optimizer/_context.py`, `optimizer/predicates.py`, `types/finalizer.py`, `utils/connections.py`, `utils/querysets.py` (`047` edits)
- `examples/fakeshop/apps/library/schema.py`, `examples/fakeshop/apps/products/schema.py`, `tests/test_resource_policy.py`, `examples/fakeshop/test_query/test_resource_policy_api.py`
- the `docs/SPECS/` archive moves already staged for the prior cycle, and `examples/fakeshop/apps/kanban/constants.py`
- `docs/feedback.md`, `docs/row-preserving-predicates-part1-plan.md`, `docs/dry/dry-file-mutations__resolvers.md`, `multi-root-schedule-graph-reproduction.md` (unrelated concurrent work)

### Tracked binary / generated files that are concurrent-writable

`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md`. A concurrent maintainer session flipped card `047` to Done in the DB during this cycle; the re-render picked that up alongside this build's own rows. That is the concurrent writer's work carried forward, not this build's, and it was **not** reverted.

## Build-wide context flags

- **Version-bump owner:** this card. Card `048` is the only non-Done card at `0.0.17` (`049` targets `0.0.18`, `050` targets `0.0.19`), so Slice 5 owns the `pyproject.toml` / `__version__` / `tests/base/test_init.py` / `uv.lock` bump. See spec-048 Decision 12.
- **Intentional alpha breaking change:** `path` leaves the default file/image output. Migration note is a Slice 5 deliverable in `docs/README.md`.
- **`CHANGELOG.md`:** not touched. [`AGENTS.md`][agents] reserves it and this card does not claim the permission.
- **Card `050`** plans to extract `DjangoDebugExtension` into a standalone package. Slice 2's changes are confined to `extensions/debug.py` plus its two test files and introduce no new dependency on package-internal symbols beyond the already-imported package logger, so the extraction's verbatim-move plan is unaffected.

## Standing rules in force

- **One slice at a time,** except where the ownership partition below licenses concurrency.
- **DRY first.** Every plan and every implementation answers "is this the maximally DRY shape that stays readable?" before anything else. Three consolidations this build owes: one `path` field definition serving both opt-in output types, one truncation primitive serving both debug row families, and one policy-resolution idiom shared with `resource_policy.py`.

## Ownership partition

Slices 1-3 ran sequentially (each consumes the surface the previous one lands). Slice 4's test work ran as **three concurrent cohorts under a declared partition**, and Slice 5's glossary work as a fourth:

| Cohort | Files owned |
|---|---|
| T1 debug tests | `tests/extensions/test_debug.py`, `examples/fakeshop/test_query/test_debug_extension_api.py` |
| T2 error-policy tests | `tests/auth/test_mutations.py`, `tests/forms/test_resolvers.py`, `tests/mutations/test_write_transaction.py`, `tests/mutations/test_permissions.py`, `examples/fakeshop/test_query/test_kanban_api.py`, `examples/fakeshop/test_query/test_products_api.py`, `examples/fakeshop/test_query/test_library_api.py`, `examples/fakeshop/test_query/test_resource_policy_api.py`, `examples/fakeshop/test_query/test_error_policy_api.py`, `tests/test_error_policy.py` |
| T3 file-path tests + surface pins | `tests/types/test_resolvers.py`, `tests/types/test_converters.py`, `tests/types/test_base.py`, `tests/base/test_init.py`, `examples/fakeshop/test_query/test_uploads_api.py`, `examples/fakeshop/apps/scalars/schema.py`, `examples/fakeshop/test_query/test_multi_db.py` |
| G glossary fold-in | the `apps.glossary` DB tables and the regenerated `docs/GLOSSARY.md` |

No file appears in two cohorts. `examples/fakeshop/db.sqlite3` is written by cohort G (glossary tables) and by the Slice 5 card flip (kanban tables); those are disjoint table sets and were sequenced anyway.

## Hot-path declaration

- **Slice 1** (`convert_field_output`): **not** hot-path. The opt-in swap is one dict lookup at *type-creation* time, not per request, per resolver, or per row.
- **Slice 2** (debug extension): **not** hot-path in the sense that matters. The extension is opt-in and development-only; the new gate makes the non-debug path strictly *cheaper* (no bracket, no snapshot), and the caps run once per operation over already-materialized rows.
- **Slice 3** (error policy): **per-operation, but only on the error path.** The teardown reads one attribute and one setting per operation; the classification and mask run only over `result.errors`, which is empty on every successful operation. The one measurable addition to a *failing* operation is a `uuid4()` and a log record per masked error.
- **Slice 5:** none.

## Floor-verification scope

- **Slice 1:** Strawberry type-construction seam. Focused scope: `tests/types/test_converters.py`, `tests/types/test_base.py`, `tests/types/test_resolvers.py`.
- **Slice 2:** Django database-connection and Strawberry extension-lifecycle seam. Focused scope: `tests/extensions/test_debug.py`.
- **Slice 3:** Strawberry extension-lifecycle and graphql-core error seam. Focused scope: `tests/test_error_policy.py`, `examples/fakeshop/test_query/test_error_policy_api.py`.
- **Slices 4-5:** none beyond what the owning slice already declares.

## Artifacts

- `docs/builder/build-048-secure_output_defaults-0_0_17.md` (this file)
- `docs/builder/bld-048-final.md` - the final gate

## Slice checklist

- [x] **Slice 1** - `types/converters.py` + `types/base.py`: `path` leaves the default output; the `Meta.filesystem_path_fields` per-column opt-in and its four type-creation rejections. Spec Slice 1.
- [x] **Slice 2** - `extensions/debug.py`: the `settings.DEBUG` fail-closed gate, the `allow_unsafe_production` acknowledgement, and the deterministic payload caps. Spec Slice 2.
- [x] **Slice 3** - `error_policy.py` + `conf.py` + `extensions/error_policy.py` + `schema.py`: the production error policy, its structural classification, and the prepended extension. Spec Slice 3.
- [x] **Slice 4** - tests across all three trees, run as the three concurrent cohorts above. Spec Slice 4.
- [x] **Slice 5** - docs fold-in (`docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `README.md`, `TODAY.md`, `KANBAN.md`) and the `0.0.17` version bump. Spec Slice 5.
- [x] **Final test-run gate** - `docs/builder/bld-048-final.md`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md

<!-- docs/ -->
[spec-048]: ../SPECS/spec-048-secure_output_defaults-0_0_17.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
