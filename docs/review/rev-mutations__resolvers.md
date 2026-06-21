# Review: `django_strawberry_framework/mutations/resolvers.py`

Status: verified

## DRY analysis

- Defer-with-trigger — the visibility-vs-existence relation-pk gate pair. `_relation_visibility_error` (resolvers.py:454-498) and `_relation_existence_error` (resolvers.py:529-570) are deliberate, non-mergeable siblings today: the GlobalID path runs `apply_type_visibility_sync(initial_queryset(...))` against the related type and pre-coerces pks inside `decode_model_global_id`, while the raw-pk path runs `_default_manager.filter(pk__in=...)` and coerces locally via `_coerce_relation_pk_or_none` (resolvers.py:501-526). Both end in the SAME `{str(pk)} <= <queried-set>` subset test producing the SAME `_relation_error`. The shared tail is one statement (the subset comparison), so collapsing now would force a queryset-source + coercion-source parameterization that hides the visibility-vs-existence distinction — net negative. **Trigger: a third relation-membership gate lands (e.g. a reverse-relation or GenericForeignKey writer), OR the subset/error tail grows past the single comparison line.** Then fold the queried-pk-set producer into a parameter and single-source the `{str(pk)} <= existing` + `_relation_error` tail. Do NOT re-flag as act-now — two distinct contracts (one consults `get_queryset`, one consults the default manager) sharing a one-line tail is correct sibling design.

## High:

None.

## Medium:

None.

## Low:

### Repeated `"many_to_many"` getattr probe literal (forward-looking)

`getattr(field, "many_to_many", False)` appears twice — `_relation_field_index` (resolvers.py:309) and `_decode_relation_id_set` (resolvers.py:384). Both are the same intent ("is this field an M2M?"), and `utils/relations.py::is_forward_many_to_many` already owns the *forward*-M2M predicate this module imports (resolvers.py:91). The plain `many_to_many` probe is broader (any M2M, incl. reverse) and the two sites read different field objects in different control flow, so a shared `_is_m2m(field)` one-liner would add a named indirection without removing logic. Defer until a third bare `many_to_many` probe appears in this module OR `is_forward_many_to_many` grows a non-forward companion; then route all M2M-shape probes through `utils/relations`. Forward-looking only — not actionable this cycle.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module routes every shared concern to a canonical primitive rather than re-implementing: GlobalID decode + model-check + pk-coercion through `relay.py::decode_model_global_id` / `GlobalIDDecode` (resolvers.py:88, used at the relation-set decode resolvers.py:375 and the lookup-id decode resolvers.py:1104 — the spec-036 DRY-2 single source); sync visibility + `SyncMisuseError` discipline through `utils/querysets.py::apply_type_visibility_sync` + `initial_queryset` (resolvers.py:90, at `_relation_visibility_error` resolvers.py:489 and `_locate_instance` resolvers.py:585); optimizer re-fetch through `optimizer/extension.py::apply_connection_optimization` + the slot-aware `mutation_payload_child_selections` (resolvers.py:83, at `_refetch_optimized` resolvers.py:775-779); forward-M2M predicate through `utils/relations.py::is_forward_many_to_many` (resolvers.py:310); payload slot through `mutations/inputs.py::payload_object_slot` (resolvers.py:773, 821); the `"__all__"` non-field sentinel through `mutations/inputs.py::NON_FIELD_ERROR_KEY` (single-sourced from Django's `NON_FIELD_ERRORS`, consumed at resolvers.py:696, 723).
- **New helpers considered.** The create/update write-finalization tail is ALREADY extracted — `_validate_save_assign_refetch_payload` (resolvers.py:841-882) single-sources `full_clean -> save -> M2M -> re-fetch -> payload` for both branches (spec-036 DRY-3), so `_run_create`/`_run_update` differ only in their prelude. The `FieldError`-builder family (`_relation_error`, `_relation_null_error`, `_not_found_error`, `_invalid_lookup_id_error`, `_integrity_error_field_errors`) is intentionally one named builder per distinct message/contract — folding them into a parameterized factory would obscure which surface each message belongs to and reduce no logic. No new helper warranted.
- **Duplication risk in the current file.** The two relation-pk gates (`_relation_visibility_error` / `_relation_existence_error`) and their two coercion paths (`decode_model_global_id` pre-coercion vs `_coerce_relation_pk_or_none`) are near-mirrors but encode two genuinely different contracts (visibility `get_queryset` vs default-manager existence; resolve-type id-field coercion vs `_meta.pk` coercion) — tracked as the single defer-with-trigger DRY bullet. The `"many_to_many"` getattr literal x2 is the forward-looking Low. Neither is act-now.

### Other positives

- **No existence leak, verified end-to-end.** Hidden and missing collapse to one indistinguishable `FieldError` on every path: update/delete locate (`_locate_instance` returns `None` on `DoesNotExist`, mapped to `_not_found_error` at resolvers.py:944/997), relation visibility (`_relation_visibility_error` returns the uniform `_relation_error`), and lookup-id decode (`UNCOERCIBLE_PK` -> `_not_found_error`, `WRONG_MODEL`/`DECODE_FAILED` -> `_invalid_lookup_id_error` decided pre-DB-read at resolvers.py:1105-1108). The top-level `id:` is decoded + type-checked against the target model BEFORE the lookup (`_coerce_lookup_id`), so a wrong-model id is never coerced to a bare pk that hits the same-pk row of the right model (feedback #1).
- **Atomicity + async parity is single-bodied.** `_run_pipeline_sync` wraps authorize->snapshot in one `transaction.atomic()` (resolvers.py:824); `resolve_mutation_async` does NOT re-implement the pipeline — it runs the SAME `_run_pipeline_sync` under one `sync_to_async(thread_sensitive=True)` (resolvers.py:1174), so the write, M2M `.set(...)`, and snapshot never interleave ORM work with awaits (AR-M4). M2M assignment is correctly post-`save()` (`_assign_m2m` called after `_save_or_field_errors` at resolvers.py:879).
- **Async-hook bypass closed loud, not silent-allow.** Both an `async def get_queryset` (via `apply_type_visibility_sync`) and an `async def check_permission` (`_authorize_or_raise` resolvers.py:1032-1037: `inspect.iscoroutine` -> `.close()` -> `SyncMisuseError`) are rejected rather than treated as a truthy "allow". The async-`has_permission` case is correctly delegated one level down to `check_permission` itself. This is the load-bearing authorization-bypass guard and is implemented at the right seam.
- **Decode-time defensive rejections that close real save-time leaks.** `_explicit_null_error` (NOT-NULL on a `blank=True, null=False` column that `clean_fields` skips), `_unencodable_text_error` (lone UTF-16 surrogate that escapes as a raw `UnicodeEncodeError`), `_make_aware_if_naive` (naive datetime under `USE_TZ` that a `-W error` config escalates), and `_coerce_relation_pk_or_none` (out-of-range raw M2M pk that crashes the backend with `OverflowError`) each reject at decode as a field-keyed `FieldError` before any DB-bound work — every one is documented against a specific feedback finding and maps to the in-band envelope rather than leaking a top-level exception.
- **`exclude` carve-out is constraint-aware (AR-H2).** `_unprovided_exclude` + `_unique_constraint_groups` keep validating any unprovided field co-participating in a `UniqueConstraint`/`unique_together`/`unique` group with a provided field, and `_provided_attr_names` reverses `<field>_id` -> field-name through the relation index (NOT a blind suffix strip), so a scalar column literally named `<x>_id` is never mis-excluded (spec-036 M3-1). The `_is_forward_concrete_relation` guard (`column is not None and related_model is not None`) keeps a `GenericForeignKey` out of the FK index.
- **Delete snapshot/identity contract.** `_run_delete` materializes the optimizer-planned snapshot fully (`force_load=True`) BEFORE deletion, and deletes via the *located instance* not the snapshot — so Django's `Model.delete()` nulling `instance.pk` leaves the snapshot's `pk`/`id` intact for the delete payload's cache-eviction contract (feedback P1).
- **Test discipline.** `tests/mutations/test_resolvers.py` exists alongside the live products write surface in `examples/fakeshop/test_query/test_mutation_atomicity.py`, exercising the pipeline through real GraphQL per AGENTS.md's prefer-real-usage rule; the sole first-party callers are `mutations/fields.py:212-213` (async/sync dispatch).

### Summary

`resolvers.py` is the create/update/delete write core and it is correctness-rigorous: a single sync pipeline body wrapped once for async, one `transaction.atomic()` boundary, no-existence-leak collapse on every locate/relation/lookup path, async-hook bypass rejected loud at the right seam, post-write optimizer-planned re-fetch by pk without the visibility filter, and a battery of decode-time rejections that each close a specific save-time exception leak into the field-keyed `FieldError` envelope. DRY is essentially resolved — the write-finalization tail is already single-sourced (DRY-3), GlobalID decode/visibility/optimizer all route to canonical primitives, and the only consolidation candidate (the visibility-vs-existence relation-pk gate pair) is a correct two-contract sibling deferred with a third-gate trigger. `git diff` is empty against both the cycle baseline (`4ceeb5f9`) and HEAD — the file landed via spec-036/037 build commits, with the latest touch (`aa625fef`) already in HEAD — and the GLOSSARY's mutation surface (`DjangoMutation`, `DjangoMutationField`, `FieldError` envelope, `DjangoModelPermission`, input-type generation) is current with the implementation. Genuine no-source-edit cycle (shape #5): zero findings requiring a behavior change, one defer-with-trigger DRY bullet, one forward-looking Low.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, 289 files left unchanged.
- `uv run ruff check --fix .` — pass, all checks passed.

### Notes for Worker 3
- `git diff 4ceeb5f9e2f69f9080bcb47c60d2f44c27e471bc -- django_strawberry_framework/mutations/resolvers.py` is empty; `git diff HEAD -- …` is empty. The "NEW file / full first-review" framing is satisfied by a full first-review read, but the file already landed in HEAD via spec-036/037 build commits (latest touch `aa625fef`, in HEAD) — so there is no pending edit and the cycle is a genuine shape #5.
- DRY bullet (relation-pk gate pair `_relation_visibility_error` / `_relation_existence_error`) is defer-with-trigger; do not action this cycle.
- Low (`"many_to_many"` getattr literal x2 at resolvers.py:309, 384) is forward-looking; no edit.
- No GLOSSARY-only fix in scope: ran the grep-GLOSSARY drift check across all public mutation symbols (`DjangoMutation` :384-390, `DjangoMutationField` :392-398, `FieldError` envelope :495-501, `DjangoModelPermission` :380-382, input-type generation :637-644) — all accurate vs implementation, no stale prose.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits. The module's docstrings are exhaustive and accurate (each helper cites its spec-036 decision / feedback finding and the contract it enforces); no stale comment, no docstring promising behavior the implementation lacks, no obsolete TODO (overview reports 0 TODO comments). The six `# noqa: A002` markers on the `id` shadowing are correct and necessary (the `id:` argument name is part of the Relay-spec field signature).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source, test, GLOSSARY, or CHANGELOG edit was made this cycle (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_11.md` is silent on any changelog action for this item). Internal review-only pass over an already-shipped file.

---

## Verification (Worker 3)

### Logic verification outcome

Genuine shape #5 (no-source-edit), verified with write-core rigor. All High / Medium `None.` confirmed genuine, not lazy — every load-bearing correctness claim maps to a named passing test in `tests/mutations/test_resolvers.py` (45/45 pass):

- **No-existence-leak collapse on every path.** Hidden and missing collapse to one `FieldError`, verified at each seam: update/delete locate (`_locate_instance` returns `None` on `DoesNotExist` → `_not_found_error`, pinned by `test_hidden_row_update_is_not_found_no_existence_leak`); relation visibility (`_relation_visibility_error` → uniform `_relation_error`, `test_globalid_relation_override_flows_through_visibility_contract` + `test_m2m_hidden_related_id_is_field_error`); lookup-id decode (`_coerce_lookup_id` decides `WRONG_MODEL`/`DECODE_FAILED` → `_invalid_lookup_id_error` and `UNCOERCIBLE_PK` → `_not_found_error` pre-DB-read at resolvers.py:1105-1108, `test_wrong_type_globalid_yields_field_error_no_cross_model_lookup` + `test_update_uncoercible_pk_in_wellformed_id_is_not_found_no_crash`). The `GlobalIDDecode` enum has exactly the four statuses the docstrings cite (relay.py:182-185).
- **`full_clean()` → `FieldError` envelope faithful.** `_validation_error_to_field_errors` keys `error_dict` per-field, maps Django's `NON_FIELD_ERRORS` to the `NON_FIELD_ERROR_KEY` `"__all__"` sentinel (single-sourced from `mutations/inputs.py`), pinned by `test_unique_constraint_caught_by_validate_constraints_keys_all_sentinel`.
- **Atomicity.** One `transaction.atomic()` wraps authorize→snapshot (resolvers.py:824); M2M `.set(...)` runs post-`save()` inside the block (`_assign_m2m` after `_save_or_field_errors` at resolvers.py:879).
- **Delete uses the located instance.** `_run_delete` materializes the snapshot (`force_load=True`) BEFORE deletion and calls `instance.delete()` on the located row, not the snapshot — so the snapshot keeps its `pk`/`id` (`test_delete_snapshot_materializes_relation_before_delete`, `test_delete_happy_path_returns_snapshot_and_removes_row`).
- **FK `_id` assignment + GlobalID decode.** `_decode_relations` routes forward FK/O2O `<field>_id` through `_decode_single_relation_id` → shared `_decode_relation_id_set` → `decode_model_global_id` (type-check against `related_model`); raw-pk M2M existence-checked via `_relation_existence_error` + `_coerce_relation_pk_or_none` (the raw-pk mirror of relay.py's `_coerce_pk_or_none`), pinned by `test_create_raw_pk_m2m_nonexistent_id_is_field_error_no_dangling_row` + `test_raw_pk_m2m_existence_check_coerces_out_of_range_pk_no_overflow`.
- **Post-write re-fetch optimizer-planned, NO `.only()` under mutation op.** `_refetch_optimized` re-fetches by pk WITHOUT the visibility filter through `apply_connection_optimization`; the G2 gate (walker.py:66-71, 413-414) confirms `MUTATION` leaves `plan.only_fields` untouched, so no `.only(...)` is applied (`test_refetch_skips_visibility_filter_after_authorized_write`).
- **Sync/async parity.** `resolve_mutation_async` wraps the SAME `_run_pipeline_sync` under one `sync_to_async(thread_sensitive=True)` (resolvers.py:1174); no re-implementation (`test_async_pipeline_create_happy_path`, `test_async_mutation_does_not_leak_into_later_read_optimizer_execution`).
- **Async-hook bypass rejected loud at both seams.** `get_queryset` async → `SyncMisuseError` via `apply_type_visibility_sync` (`test_sync_misuse_async_get_queryset_from_sync_path`); `check_permission` async → `_authorize_or_raise` closes the coroutine + raises `SyncMisuseError` (resolvers.py:1032-1037), and the `has_permission`-entry async case is rejected one level down in `sets.py::check_permission` (sets.py:557-563, `iscoroutine` → `.close()` → raise). No truthy-coroutine silent-allow path.

### DRY findings disposition

The single defer-with-trigger DRY bullet (the `_relation_visibility_error` / `_relation_existence_error` gate pair) is correctly carried forward: the two gates encode two genuinely different contracts (visibility `get_queryset` via `apply_type_visibility_sync` vs default-manager existence) sharing only a one-line subset-test tail, with a verbatim third-gate trigger. Collapsing now would force a queryset-source + coercion-source parameterization that hides the visibility-vs-existence distinction — correct sibling design, not act-now.

### Temp test verification

None — no temp tests created. Relied on the existing permanent suite (`tests/mutations/test_resolvers.py`, 45 tests) plus the live write surface (`examples/fakeshop/test_query/test_mutation_atomicity.py`).

### Verification outcome

`cycle accepted; verified`.

Zero-edit proof holds two ways: `git diff 4ceeb5f9 -- mutations/resolvers.py` empty AND `git diff HEAD -- …` empty; the owned-paths `--stat` (django_strawberry_framework/ tests/ GLOSSARY CHANGELOG) is empty for the cycle baseline; CHANGELOG clean. The only dirty source paths (`optimizer/walker.py`, `utils/relations.py`) are the AGENTS.md #33 concurrent-maintainer work the dispatch explicitly scoped out, and they do not touch the target. All three Worker 1/2 sections open with `Filled by Worker 1 per no-source-edit cycle pattern.`. The forward-looking Low (`"many_to_many"` getattr probe x2 at resolvers.py:309, 384) carries its defer rationale and is not actionable. GLOSSARY mutation prose (`DjangoModelPermission` :376-382, `DjangoMutation` :384, `DjangoMutationField`, `FieldError` envelope :39, Input-type generation) reads accurate vs live source — the sole dirty GLOSSARY hunk is at line 305 (relation-cardinality = #33), not in mutation prose — so this is a genuine #5, not a missed #4. Changelog "Not warranted" cites both AGENTS.md and the active plan's silence. `Status: verified`.
