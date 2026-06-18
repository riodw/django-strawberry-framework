# Build: Cross-slice integration pass — mutations / 0.0.11 (036)

Spec reference: `docs/spec-036-mutations-0_0_11.md` (Status **COMPLETE**, card `DONE-036-0.0.11`; all five slices `final-accepted`)
Build plan: `docs/builder/build-036-mutations-0_0_11.md`
Status: final-accepted

This is the Worker-1 cross-slice integration pass per `BUILD.md` "Cross-slice integration pass". Every spec slice (1–5) reached `final-accepted`; this pass scans the assembled build for cross-slice duplication, import-direction / boundary drift, export-surface drift, and comment-story coherence, then sets a single `Status:`. It is read-only on source/tests/docs (any code-change opportunity is recorded as an actionable item and flagged for a Worker 2 consolidation + Worker 3 review, not fixed here).

## Spec status-line re-verification (this spawn)

Spec line 5 reads `Status: **COMPLETE** (card DONE-036-0.0.11; all five slices shipped — build complete)`. Accurate for the current state (all five slices `final-accepted`, integration + final gate remaining). No header edit needed this spawn.

## Artifacts read (in slice order, full)

- `docs/builder/bld-slice-1-input_generation.md` — `final-accepted`. Generation substrate `mutations/inputs.py` (+ `mutations/__init__.py`), public `FieldError` export.
- `docs/builder/bld-slice-2-mutation_base.md` — `final-accepted` (1 pass-1 High, resolved pass 2). `mutations/sets.py` + `mutations/permissions.py`, finalizer phase-2.5 bind, `registry.clear()` co-clear, `DjangoMutation` + `DjangoModelPermission` exports.
- `docs/builder/bld-slice-3-resolvers.md` — `final-accepted` (Medium M3-1 / Low L3-1 resolved pass 2; FV-1 raised then withdrawn — a test-DB row-isolation artifact, NOT an optimizer ContextVar leak; production byte-unchanged). `mutations/resolvers.py` + `mutations/fields.py`, the `optimizer/extension.py` `selection_extractor` seam, `DjangoMutationField` export.
- `docs/builder/bld-slice-4-products_live.md` — `final-accepted` (1 deferred Low). Products live write surface + the `spec-035` G2 handoff discharged at the behavioral tier.
- `docs/builder/bld-slice-5-docs_wrap.md` — `final-accepted` (1 cosmetic Low; 2 pre-existing kanban-test fails surfaced as out-of-scope). Doc/DB-backed-doc wrap + card → `DONE-036-0.0.11`.

## Static inspection helper — confirmed run on every review-worthy module

Re-ran `scripts/review_inspect.py … --output-dir docs/shadow` this pass on the five `mutations/` modules and `optimizer/extension.py` for fresh cross-slice overviews:

- `docs/shadow/django_strawberry_framework__mutations__inputs.overview.md`
- `docs/shadow/django_strawberry_framework__mutations__sets.overview.md`
- `docs/shadow/django_strawberry_framework__mutations__permissions.overview.md`
- `docs/shadow/django_strawberry_framework__mutations__resolvers.overview.md`
- `docs/shadow/django_strawberry_framework__mutations__fields.overview.md`
- `docs/shadow/django_strawberry_framework__optimizer__extension.overview.md`

Per-slice helper coverage (from the slice artifacts) is complete: Worker 3 ran it on `inputs.py` (Slice 1), `sets.py` + `permissions.py` + `types/finalizer.py` (Slice 2), `resolvers.py` + `fields.py` (Slice 3), and `test_products_api.py` (`--outline-only`, Slice 4). `mutations/permissions.py` is a near-pure-class module (one `has_permission` body + one action-map constant) but was inspected anyway (Slice 2). Slice 5 is doc/DB-only — no review-worthy `.py` logic, skip recorded in its artifact. No review-worthy Python file in the build went un-inspected.

## Cross-slice DRY scan

### Repeated string literals compared across the six overviews

The helper's **Repeated string literals** section reports literals repeated *within a single file*. Comparing the per-file sections across all six overviews, **no literal flagged in one file's section also appears in another file's section** — i.e. there is no cross-slice repeated-literal candidate. The per-file repeats are:

- `mutations/inputs.py`: `DjangoMutation for` (3×, the `ConfigurationError` message lead-in — Slice-1 Low, recorded no-change; coupling three independent messages by a shared prefix was correctly rejected), `many_to_many` (3×, the Django-field attribute string — see the forward-M2M idiom below).
- `mutations/sets.py`: `DjangoMutation` (8×, docstring/error-message family label), `input_class` / `partial_input_class` (4× each), `operation` (3×), `permission_classes` (3×) — all `Meta`-key names used in the validation matrix within the one file; these are the keys of `_ALLOWED_MUTATION_META_KEYS`, used once per validation branch, not a cross-file literal.
- `mutations/permissions.py`, `mutations/resolvers.py`, `mutations/fields.py`: **None.**
- `optimizer/extension.py`: `_strawberry_schema` (2×, unrelated to mutations — pre-existing).

### The five named single-source targets (source-verified, all single-sourced)

The task names five literals/shapes that must be single-sourced across `inputs.py` / `sets.py` / `resolvers.py` / `fields.py`. Traced each in source:

1. **Operation-set `{"create","update","delete"}`** — single-sourced as `sets.py::_VALID_OPERATIONS` (the canonical valid-set; `sets.py:81`). The remaining bare `"create"`/`"update"`/`"delete"` occurrences are **semantically distinct uses, not re-enumerations of the valid set**:
   - `permissions.py::_OPERATION_PERMISSION_ACTION` (`permissions.py:37`) — the canonical operation→Django-perm-action map (these literals ARE the map keys).
   - `resolvers.py` — `_run_pipeline_sync` operation dispatch (`:510`/`:512`) + the three `_authorize_or_raise(…, "create"/"update"/"delete", …)` audit labels (`:536`/`:577`/`:627`).
   - `fields.py` — signature-shape branches `operation in ("update","delete")` (`:159`) / `("create","update")` (`:165`).
   The operation→input-kind map (`_OPERATION_INPUT_KIND`, `sets.py:88`, built from the Slice-1 `CREATE`/`PARTIAL` constants) IS shared — `fields.py:62` imports it from `sets.py`. The Slice-2/3 "shared-operations-enum if a third enumeration appears" watch was satisfied: Slice 3 added a per-operation **method table** (`_run_create`/`_run_update`/`_run_delete` keyed on `meta.operation`), not a fourth enumeration of the set. **Verdict: a single shared `Operation` enum across these four distinct concerns would be over-abstraction (Worker 3's standing assessment) — no consolidation warranted.**
2. **Model-perm-action map** — single-sourced as `permissions.py::_OPERATION_PERMISSION_ACTION` (`permissions.py:37-41`), read once at `:84`. One site. Clean.
3. **`"__all__"` sentinel** — single-sourced as `inputs.py::NON_FIELD_ERROR_KEY = NON_FIELD_ERRORS` (`inputs.py:67`), imported by `resolvers.py:70` and used at `resolvers.py:388`/`:392`/`:409`. No bare `"__all__"` string in executable code (only docstrings/comments). Clean (AR-M3).
4. **`<field>_id` suffix** — the generator owns the python-attr construction `f"{field.name}_id"` in `inputs.py::relation_input_annotation` (`inputs.py:281`). `resolvers.py::_relation_field_index` reconstructs the same `f"{field.name}_id"` (`resolvers.py:171`) as the **inverse** wire-attr→field map, derived from the live `_meta` field object (NOT a hardcoded mapping). Slice 2's `_validate_input_class` derives the expected attr set by *calling* `relation_input_annotation` (`sets.py:211`), so the validator cannot drift from the generator. Slice 3's M3-1/L3-1 fix specifically replaced a string-suffix heuristic with this index-driven derivation. **Verdict: a justified mirror over one field-attname convention (Django's own `<fk>_id`), already adjudicated DRY-clean by Slice-3 W3+W1 — no consolidation warranted.**
5. **`node`/`result` payload slot names** — single-sourced as `inputs.py::payload_object_slot` (`inputs.py:433-440`, the only function emitting the bare `"node"`/`"result"` strings). Called by `sets.py:579` (bind) and `resolvers.py:458`/`:506` (payload build). No bare slot literal anywhere else in executable code. Clean (AR-H5).

### The standing forward-M2M idiom watch (recorded across Slices 1–3)

`getattr(field, "many_to_many", False)` appears at **9 sites package-wide**: 5 inside `mutations/` (`inputs.py:184`/`:277`/`:420`, `resolvers.py:167`) and 4 pre-existing outside it (`permissions.py:110`, `filters/sets.py:614`, `optimizer/field_meta.py:188`, `utils/relations.py:69`, `orders/inputs.py:168`). This was flagged by Slice 1 and carried forward by Slices 2/3 as a possible integration-pass idea. **Integration-pass verdict: NOT a consolidation item.** (a) It is a **pre-existing package-wide idiom** (4 of the 9 sites predate this build); a `mutations/`-local helper would *diverge* from the established convention. (b) A genuine fix would be a repo-wide predicate touching `optimizer/`, `filters/`, `orders/`, `utils/`, `permissions/` — out of scope for a mutations-card integration pass, and the kind of cross-subsystem refactor that belongs in its own card. (c) The idiom is a one-line attribute read with no logic to drift. Recording it for the next spec author's reading list (see Deferred follow-ups), not flagging a Worker 2 pass.

### Duplicated helpers / repeated ORM-or-queryset patterns / misplaced responsibilities

- **No duplicated helper across slices.** The generation substrate is single-sited in `inputs.py` and reused by `sets.py` (bind) and `resolvers.py` (decode/payload). The materialize/dedupe/collision mechanics delegate to the shared `utils/inputs.py` substrate (verified: zero re-copies of the ledger / collision check / camel-name across the slices). `clear_mutation_input_namespace` deliberately does NOT call the set-family `clear_generated_input_namespace` (justified divergence — mutations have no factory / set-base `_lifecycle`).
- **Sync/async pipeline single-sourced.** `resolvers.py::resolve_mutation_async` wraps the *same* `_run_pipeline_sync` body in one `sync_to_async(thread_sensitive=True)` (AR-M4); `resolve_mutation_sync` is a thin `UNSET`-normalizing alias. No parallel async pipeline.
- **ORM/queryset patterns centralized.** The update/delete visibility locate reuses `utils/querysets.py::{apply_type_visibility_sync, initial_queryset}` (the `_resolve_node_default` shape — the package's one sync-`get_queryset`/`SyncMisuseError` site). The post-write re-fetch reuses `optimizer/extension.py::apply_connection_optimization` (the connection field's own seam) so the G2 gate, optimizer discovery, and no-optimizer short-circuit all come for free. The resolver never calls `get_queryset` directly and adds no second optimizer-plan path.
- **`optimizer/extension.py` `selection_extractor` seam.** The one mutations-driven change to a non-`mutations/` module: a `mutation_payload_child_selections(slot)` extractor + a `selection_extractor` kwarg on `apply_connection_optimization` defaulting to `_connection_node_child_selections` (the prior hardcoded value — read-side byte-identical, verified). The two extractors share four navigation primitives but differ in depth (one payload slot vs `edges{node}`); a common "navigate N levels" helper for two call sites would be over-abstraction (Slice-3 W3+W1 verdict). No `on_execute` / ContextVar / `.set` / `.reset` change (the withdrawn FV-1 hypothesis — verified zero such hunks in the diff). Responsibilities are correctly placed: the navigator lives with the optimizer it serves.
- **Write-auth single-sited.** `DjangoModelPermission.has_permission` resolves the request via `utils/permissions.py::request_from_info` (the read-side resolver); the resolver maps a `check_permission` `False` → `GraphQLError` and never re-walks `permission_classes`. No second user-resolution walk.

### Inconsistent naming / error handling between slices

Consistent. Every fail-loud raises `ConfigurationError` (class-creation / finalize-time) or surfaces a `FieldError` envelope entry (validation) or a top-level `GraphQLError` (write-auth denial / malformed GlobalID) — the same three-tier discipline the spec pins, applied uniformly across the slices. The `<Name>Payload` uniform `node`/`result` slot is the single shape across create/update/delete. No divergent error vocabulary or validation shape between slices.

## Import-direction / boundary verdict — CLEAN (one-way)

The `mutations/` subpackage depends on `types/` / `optimizer/` / `utils/` / `registry`, never vice-versa. Confirmed from the overviews' **Imports** sections and a reverse-dependency grep:

- **Forward deps (from the overviews):** `mutations/` imports `..exceptions`, `..registry`, `..types.converters`, `..types.relay`, `..utils.inputs`, `..utils.permissions`, `..utils.querysets`, `..optimizer.extension` — all the documented dependencies, all forward. No sibling imports from outside the documented boundary; no `mutations/` module imports another subsystem package's internals beyond these named seams.
- **The only references to `mutations/` from outside the subpackage are non-static, by design:**
  1. `__init__.py:19` — the package-root public re-export (the four symbols). Expected.
  2. `types/finalizer.py:694` — a **cycle-safe function-local** `from ..mutations.sets import bind_mutations` *inside* `finalize_django_types()` (not a module-top import), mirroring the filter/order binders' local-import idiom. Does not create a static load-order dependency.
  3. `registry.py:526`/`:531` — **string-literal** module paths inside `_clear_if_importable(...)` co-clear blocks (lazy, by-name, `ImportError`-skipped). Not real imports.

No reverse static dependency exists: `types/`, `optimizer/`, `registry` do not import `mutations/` at module load. The boundary the spec mandates (Decision 4 / Decision 12) holds.

## Export-surface verdict — CLEAN (exactly four net-new symbols; DEFERRED/ALLOWED byte-unchanged)

- `git diff HEAD -- django_strawberry_framework/__init__.py` adds **exactly** the four net-new symbols to the import block and `__all__`: `DjangoModelPermission`, `DjangoMutation`, `DjangoMutationField`, `FieldError` (alphabetical slots), and removes the resolved `TODO(spec-036 Slice 1-3)` staged-export block. Nothing else added; no symbol over-exported. Spec-authorized by Decision 5 + Decision 15.
- `__version__ = "0.0.10"` — **byte-unchanged** (Decision 13 joint-`0.0.11`-cut boundary; the version bump is owned by the joint cut, not this card). `pyproject.toml` / `uv.lock` absent from the diff.
- `tests/base/test_init.py` pins the four symbols in the expected `__all__`; `test_version` untouched.
- `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` (`types/base.py:63`/`:67`) — `git diff HEAD -- types/base.py` is **empty (byte-unchanged)**. The mutation `Meta` namespace uses its own `_ALLOWED_MUTATION_META_KEYS` (`sets.py:67`), disjoint from the `DjangoType` sets (Decision 12 isolation verified). The only `mutations/` references to the base sets are docstring mentions confirming the byte-unchanged contract.

## Comment-story coherence — CLEAN

The comments tell one coherent story across the new code. Cross-references are consistent and accurate: the `<field>_id` / `node`·`result` / `"__all__"`-sentinel / GlobalID-vs-raw-pk contracts are each documented at their single source (`inputs.py`) and referenced (not re-explained) at the consumer sites (`sets.py`, `resolvers.py`, `fields.py`). The `transaction.atomic()` + single-`sync_to_async(thread_sensitive=True)` boundary (AR-M4), the by-pk re-fetch-without-visibility (Medium-1), and the test-DB-isolation `transaction=True` rationale for async-write tests are each documented once at their site. No stale or contradictory comment across the slices; the Decision/AR tags used in comments match the spec.

## Cross-slice integration findings

No code-change consolidation item rises to a DRY *defect* (a duplication that entrenches parallel logic). The two recorded DRY observations are deliberately NOT routed to a Worker 2 pass:

1. **Forward-M2M idiom (`getattr(field, "many_to_many", False)`, 9 package-wide sites).** Pre-existing package-wide convention; a `mutations/`-local extraction would diverge from it, and a repo-wide predicate is a cross-subsystem refactor out of this card's scope. Carry to the next spec author's reading list (Deferred follow-ups), not a consolidation pass.
2. **`test_products_api.py` envelope-assert (`result["errors"][0]["field"] == <key>`, 3 sites — `:323`/`:357`/`:515`).** The Slice-4 deferred Low. Test-only convenience in the example tree (not package source), three two-line asserts with distinct field keys and slightly divergent surrounding context. At-threshold for a `_assert_field_error` helper but assessed by Worker 3 as acceptable consumer-test code. A minor maintainability nicety, not a DRY defect that warrants a Worker 2 + Worker 3 loop. Recorded; left to a future slice if more envelope asserts accrue.

Neither observation requires a code change to accept the build cross-slice-clean.

## Deferred follow-ups walked (from every accepted slice's `What looks solid` / `DRY findings` / `Notes for Worker 1`)

For the `bld-final.md` deferred-work catalog (the next spec author's reading list):

- **Forward-M2M predicate** (Slices 1–3 watch) — a package-wide "is forward M2M" helper could single-source the 9-site `getattr(field, "many_to_many", False)` idiom; a cross-subsystem cleanup, not this card.
- **Ambiguous relation-target primary raw-pk fallback** (Slices 1–2 note) — `inputs.py::relation_input_annotation` silently falls back to the raw-pk scalar when a *related* model is in the ambiguous "multiple types, no declared primary" state (Decision 11's no-primary raise is scoped to the mutation's OWN model). A possible future hardening (raise at bind for an ambiguous relation target), not a defect.
- **`_assert_field_error` envelope helper** (Slice 4 Low) — optional test-helper consolidation if more example-test envelope asserts accrue.
- **Card-DoD `docs/spec-mutations.md` filename conflict** (Slice 5) — card-36 DoD CardItem 0 reads "Add `docs/spec-mutations.md`" while the spec lives at `docs/spec-036-mutations-0_0_11.md`; recorded-not-reconciled per spec Risks line 555. Maintainer follow-up, not owed within this build.
- **Pre-existing kanban-test failure** (Slice 5; OUT OF SCOPE for this pass per the task framing) — `apps/kanban/tests/test_commands.py::test_import_card_predicted_files_command_marks_directories` and `test_services.py::test_create_card_from_spec_creates_planned_rows_for_future_paths` fail identically at committed HEAD because the maintainer's `constants.py` allowlist (commit `a1713981`) now lists `django_strawberry_framework/mutations/` + `tests/mutations/test_inputs.py` as tracked, while the two tests hardcode them as planned (`is_current=False`). Byte-identical-to-HEAD, not in this build's authored diff. It WILL trip the `bld-final.md` full `pytest` sweep — the final gate must surface it to the maintainer, NOT re-loop a slice. Fix: repoint the two tests' planned-path constants at a path genuinely absent from `constants.py`.

## Final status

`final-accepted`. The build is cross-slice clean: every named literal/shape (operation-set, perm-action map, `"__all__"` sentinel, `<field>_id` suffix, `node`/`result` slots) is single-sourced; the helper's repeated-literal sections surface no cross-file candidate; the import direction is one-way (`mutations/` → `types/`/`optimizer/`/`utils/`/`registry`, never reverse, the only outside references being the public re-export, a cycle-safe function-local finalizer import, and string-keyed `registry.clear()` co-clears); the export surface carries exactly the four net-new public symbols with `__version__` and `DEFERRED_META_KEYS`/`ALLOWED_META_KEYS` byte-unchanged; and the comments tell one coherent story. The two DRY observations (the pre-existing forward-M2M idiom; the at-threshold example-test envelope-assert) are recorded for the deferred-work catalog and do not warrant a Worker 2 consolidation pass. No spec edit was required this pass. Proceed to the final test-run gate (`bld-final.md`).
