# Review: `django_strawberry_framework/mutations/resolvers.py`

Status: verified

## DRY analysis

- None — every cross-module primitive this module needs is already routed through its canonical single-source helper, and the in-file factoring is already at its DRY floor. The model lookup is `utils/querysets.py::model_for` (3 sites: `_locate_instance`, `_run_pipeline_sync`, `_coerce_lookup_id`); the visibility-queryset seed is `apply_type_visibility_sync(initial_queryset(...))` (shared with every read surface); the GlobalID decode + model-check + pk-coercion is the shared `relay.py::decode_model_global_id` DRY-2 primitive (`_decode_relation_id_set`, `_coerce_lookup_id`); the sync-context coroutine guard is `utils/querysets.py::reject_async_in_sync_context` with the shared `mutations/permissions.py::_PERMISSION_ASYNC_RECOURSE` string (`_authorize_or_raise`); the FK-vs-M2M relation index is single-sited in `_relation_field_index` and reused by both `_decode_relations` and `_provided_attr_names`; the relation decode itself is single-sourced through `_decode_relation_id_set`, which the FK wrapper (`_decode_single_relation_id`) and M2M wrapper (`_decode_relation_id_list`) both delegate to; the `ValidationError → FieldError` mapping is single-sourced in `_validation_error_to_field_errors` (shared by the `full_clean` path and the `IntegrityError`-race fallback); the create/update write-finalization tail is single-sourced in `_validate_save_assign_refetch_payload` (DRY-3); and the payload construction is single-sourced in `_build_payload`. No remaining duplicated logic, parallel data flow, or near-copy to extract.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The this-cycle DRY edit (commit `7a17ba75`) swapped the three inline `type_cls.__django_strawberry_definition__.model` reads for `utils/querysets.py::model_for` at `resolvers.py::_locate_instance #"model = model_for(target_type)"`, `resolvers.py::_run_pipeline_sync #"model = model_for(primary_type)"`, and `resolvers.py::_coerce_lookup_id #"target_model = model_for(target_type)"` — the model lookup is now single-sited package-wide. Beyond that the module reuses: `apply_type_visibility_sync` + `initial_queryset` for every visibility-scoped read (`_locate_instance`, `_relation_visibility_error`); the shared `decode_model_global_id` GlobalID primitive (`_decode_relation_id_set`, `_coerce_lookup_id`); `reject_async_in_sync_context` + `_PERMISSION_ASYNC_RECOURSE` for the authorize seam (`_authorize_or_raise`); `is_forward_many_to_many` for the M2M predicate (`_relation_field_index`); and `mutation_payload_child_selections` + `apply_connection_optimization` for the optimizer-planned re-fetch (`_refetch_optimized`).
- **New helpers considered.** None justified — the file is already decomposed into single-responsibility helpers (decode, locate, authorize, validate, save, refetch, payload), each with one call shape. The create/update tail is already collapsed into `_validate_save_assign_refetch_payload` (DRY-3) and the FK/M2M decoders already collapse into `_decode_relation_id_set` (DRY-2); no further extraction would reduce duplication without obscuring the create/update/delete prelude differences the module deliberately keeps explicit.
- **Duplication risk in the current file.** The `_relation_error` text is reused for wrong-type, uncoercible, hidden, and missing relation ids — this is intentional (the no-existence-leak contract requires hidden and missing to be indistinguishable). The `"many_to_many"` literal appears twice (`_relation_field_index`, `_decode_relation_id_set`) as a `getattr` field-attribute probe — a Django field-API attribute name, not a shared domain constant, so inlining it at each probe is correct (folding it behind a constant would imply a single-source contract that does not exist).

### Other positives

- **No-existence-leak discipline holds through the delegations.** `_locate_instance` and `_relation_visibility_error` both route through `apply_type_visibility_sync(initial_queryset(...))`, so a row hidden by the target type's `get_queryset` is the SAME `FieldError` as a genuinely-missing row — verified the `model_for` promotion did not bypass the visibility queryset (the helper returns `type_cls.__django_strawberry_definition__.model` verbatim and is consumed only for the model handle / `DoesNotExist` catch / decode model-check, never as a query seed in place of the visibility queryset).
- **Authorization is fail-closed and async-safe.** `_authorize_or_raise` runs `check_permission` through `reject_async_in_sync_context` BEFORE the `if not allowed` branch, so an `async def check_permission` override is `close()`d and raised as `SyncMisuseError` rather than treated as a truthy "allow" (the bypass the comment at `resolvers.py::_authorize_or_raise` documents). The shared `_PERMISSION_ASYNC_RECOURSE` constant is imported from `permissions.py`, not re-spelled.
- **Transaction atomicity + async wrapping preserved.** `_run_pipeline_sync` wraps authorize → snapshot in one `transaction.atomic()`; `resolve_mutation_async` wraps that exact body in a single `sync_to_async(thread_sensitive=True)` call, so the write, its M2M `.set(...)`, and the snapshot never interleave ORM work with `await`s. The `model_for` delegation sits inside the atomic body and changes nothing about the boundary.
- **GlobalID decode preserved on both the top-level `id:` and relation ids.** `_coerce_lookup_id` and `_decode_relation_id_set` both run the wire value through `decode_model_global_id` against the target/related model: a wrong-model id is a `FieldError` (never a cross-model pk lookup), an uncoercible `node_id` is "not found" (never a raw Django `ValueError`). The `model_for(target_type)` swap feeds the helper the same model handle the inline read produced.
- **M2M `.set` post-save + raw-pk existence guard intact.** `_assign_m2m` runs after `save()` inside the transaction; the raw-pk M2M path is existence-checked (`_relation_existence_error`) with `_coerce_relation_pk_or_none` dropping out-of-range pks before `pk__in`, so a nonexistent pk rolls the whole write back rather than writing a dangling through-row.

### Summary

Drift re-review of the create/update/delete write core after the maintainer's DRY cycle. The this-cycle change to this file is exactly the `model_for` promotion (commit `7a17ba75`): three inline `type_cls.__django_strawberry_definition__.model` reads now call the canonical `utils/querysets.py::model_for` helper, which returns that attribute verbatim — a pure, semantics-identical single-site delegation. The other delegations the prompt flagged (`reject_async_in_sync_context`, the shared `decode_model_global_id` primitive, the `_PERMISSION_ASYNC_RECOURSE` string) were already in HEAD from the cycle-27 verify and were re-confirmed: none introduce a permission bypass, none regress the no-existence-leak contract, transaction atomicity and the single-`sync_to_async` async wrapping are unchanged, and M2M `.set` post-save with its raw-pk existence guard is intact. `git diff <baseline>` and `git diff HEAD` are both empty for this file (the +13/-23 is cumulative-in-HEAD), no High/Medium/Low surfaced, and the GLOSSARY `#djangomutation` entry is accurate (no drift). Genuine no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (289 files left unchanged; COM812-vs-formatter warning is informational only).
- `uv run ruff check --fix .` — pass (All checks passed!).

### Notes for Worker 3
- No GLOSSARY-only fix in scope; `docs/GLOSSARY.md` `#djangomutation` prose is accurate against current source (Meta-driven create/update/delete base) — no drift to edit.
- No Low findings to disposition (all severities `None.`).
- The this-cycle source change is the `model_for` promotion (commit `7a17ba75`, +13/-23 cumulative-in-HEAD); both `git diff 5ef9f2500707b57182d8fa305269678519db804f -- <target>` and `git diff HEAD -- <target>` are empty. The DRY delegations (`model_for`, `reject_async_in_sync_context`, `decode_model_global_id`, `_PERMISSION_ASYNC_RECOURSE`) were verified semantics-preserving: no permission/existence-leak bypass, transaction atomicity and single-`sync_to_async` async wrapping intact, M2M `.set` post-save guarded.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits — the module docstrings and the `_authorize_or_raise` / `_locate_instance` / `_coerce_lookup_id` comments remain accurate after the `model_for` delegation (the helper docstring at `utils/querysets.py::model_for` documents the centralization the resolver now relies on). No stale spec/feedback references, no obsolete TODOs (0 TODO anchors).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source/test edit this cycle (AGENTS.md: "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_11.md` records no changelog action for this RE-OPENED item). The `model_for` promotion is an internal DRY single-siting with no consumer-visible behavior change.

---

## Verification (Worker 3)

### Logic verification outcome
DRIFT RE-VERIFY of the create/update/delete write core after the maintainer's DRY cycle. No High/Medium/Low surfaced (all `None.`) — nothing to address or reject; verification is the independent semantics-preservation audit the dispatch requires.

Target stability confirmed: `git diff HEAD -- django_strawberry_framework/mutations/resolvers.py` empty AND `git diff 5ef9f2500707b57182d8fa305269678519db804f -- <target>` empty; target absent from the owned-paths stat (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` stat empty — no sibling-cycle dirt to attribute). Zero edits this cycle, no further drift.

The five maintainer DRY delegations independently confirmed semantics-preserving against live HEAD source (`d63d77f8`), each NO-regression:
1. **`model_for` promotion is pure single-site delegation.** `utils/querysets.py:105` returns `type_cls.__django_strawberry_definition__.model` verbatim. Consumed at exactly three resolver sites — `_locate_instance:575` (model handle for the `DoesNotExist` catch at :584), `_run_pipeline_sync:811` (handle passed to branches for `model(**attrs)` construction), `_coerce_lookup_id:1094` (model-check arg to `decode_model_global_id`). NEVER used as the visibility-queryset seed: every visibility read independently builds `apply_type_visibility_sync(initial_queryset(...))` (`_locate_instance:576`, `_relation_visibility_error:480`) — so the no-existence-leak contract is untouched (hidden == missing, same `_relation_error` / `_not_found_error`).
2. **Authorize seam fail-closed via `reject_async_in_sync_context`.** querysets.py:86-90 does `iscoroutine → value.close() → raise SyncMisuseError` BEFORE returning. `_authorize_or_raise:1022` passes `mutation_cls().check_permission(...)` as the first (positional) arg, so the raise fires before `if not allowed:1029` — a truthy orphaned coroutine from an `async def check_permission` override can never reach the allow branch (no authz bypass). Shared `_PERMISSION_ASYNC_RECOURSE` imported from permissions.py, not re-spelled.
3. **`decode_model_global_id` type-checks both ids.** Top-level `id:` via `_coerce_lookup_id:1095` against `model_for(target_type)`; relation ids via `_decode_relation_id_set:366` against `relation_field.related_model`. The helper (relay.py:202-225) is non-raising (`try/except Exception → DECODE_FAILED`), and a model mismatch is `WRONG_MODEL` (relay.py:220) BEFORE any pk use — so a wrong-model id is a `FieldError` (never a cross-model lookup) and an uncoercible `node_id` is `UNCOERCIBLE_PK` (never a raw Django `ValueError`).
4. **`transaction.atomic()` + single `sync_to_async`.** `_run_pipeline_sync:815` wraps the create/update/delete branch dispatch in one `transaction.atomic()`; `resolve_mutation_async:1165` wraps that exact same `_run_pipeline_sync` body in one `sync_to_async(_run_pipeline_sync, thread_sensitive=True)` — the write, M2M `.set`, and snapshot never interleave ORM work with `await`s. The `model_for` delegation sits inside the atomic body and changes no boundary.
5. **M2M `.set` post-save with raw-pk existence guard.** `_assign_m2m:870` runs after `_save_or_field_errors:867`, inside the atomic body; raw-pk M2M is existence-checked via `_relation_existence_error` (reached at `_decode_relation_id_set:375-378`) with `_coerce_relation_pk_or_none` dropping out-of-range pks before `pk__in` (no backend `OverflowError`), so a nonexistent pk rolls the whole write back rather than writing a dangling through-row.

GLOSSARY `#djangomutation` (`docs/GLOSSARY.md:388`) accurate against live source: "decode → authorize → `full_clean()` → write → optimizer-re-fetch → payload, sync and async, with the write inside one `transaction.atomic()` (async via a single `sync_to_async(thread_sensitive=True)`)"; the async-hook `SyncMisuseError`-not-allow note (`docs/GLOSSARY.md:380`) matches the fail-closed authorize seam. No drift; no GLOSSARY-only fix in scope (correct for a #5).

### DRY findings disposition
DRY analysis is `None` — every cross-module primitive routes through its canonical single-source helper (`model_for`, `decode_model_global_id`, `reject_async_in_sync_context` + shared `_PERMISSION_ASYNC_RECOURSE`, `apply_type_visibility_sync`/`initial_queryset`), and in-file factoring is at its DRY floor (`_decode_relation_id_set` DRY-2, `_validate_save_assign_refetch_payload` DRY-3, `_build_payload`, `_relation_field_index`). The `model_for` promotion is the only this-cycle source change and is cumulative-in-HEAD (commit `7a17ba75`); nothing carried forward.

### Temp test verification
- None used. No source edit this cycle and the whole correctness battery is already permanently test-pinned (no-existence-leak at the three seams, refetch-without-visibility, delete-snapshot-pk, raw-pk M2M overflow, async-parity no-leak); the audit was static against live source plus the helper contracts, which suffices for a no-edit drift re-verify.
- Disposition: n/a.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the (re-opened) `mutations/resolvers.py` checkbox at `docs/review/review-0_0_11.md:110`.
