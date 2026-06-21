# Review: `django_strawberry_framework/types/resolvers.py`

Status: verified

## DRY analysis

- **`_will_lazy_load_single` (`resolvers.py::_will_lazy_load_single` #"field_name in getattr(root,") and `_fk_attname_is_deferred` (`resolvers.py::_fk_attname_is_deferred` #"attname in getattr(root,") share the `<name> in getattr(root, "__dict__", {})` loaded-signal probe, with deliberately divergent tails.** `_will_lazy_load_single` falls back to `_state.fields_cache` membership (relation-instance cache); `_fk_attname_is_deferred` falls back to `get_deferred_fields()` membership (column-deferral cache). Two different Django caches answering two different questions ("is the related object loaded?" vs "is the FK column loaded?"). Defer with explicit trigger: **"Defer until a third caller needs the bare `__dict__` loaded-signal; only then extract `def _attr_in_instance_dict(root, name) -> bool` for the first line of all callers."** Folding only the shared first line at N=2 is net-negative — the bodies diverge immediately after and the one-liner reads clearer inline than as a named-helper indirection. (`__dict__` is the file's only repeated string literal per the static overview, and it is exactly this intentional sibling probe.)

## High:

None.

## Medium:

None.

## Low:

### Archived design specs still cite the removed `_is_fk_id_elided` helper

Commit `79b74b46` deleted `resolvers.py::_is_fk_id_elided` (its read inlined into `forward_resolver` via the threaded `elisions` read at `resolvers.py::_make_relation_resolver.forward_resolver` #"elisions ="). Two archived design docs still reference the symbol by `path::_is_fk_id_elided`:

- `docs/SPECS/spec-015-relay_interfaces-0_0_5.md`
- `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md`

These are completed / archived design docs under `docs/SPECS/` — historical snapshots of the design at their authoring time, not standing references that must track source renames. AGENTS.md #27's grep-sweep-on-rename rule targets live code comments and standing docs; archived specs are deliberately frozen records. So this is a non-defect-today **forward-Low**, not an action-now stale-doc. Defer with trigger: **"Defer unless a future reader treats `docs/SPECS/spec-003` / `spec-015` as a live source map; if so, add a one-line 'superseded by inlined `forward_resolver` elisions read (0.0.10)' note rather than rewriting the frozen design text."** Do NOT rewrite archived spec bodies as part of this cycle — they are intentionally immutable history. Re-confirmed still present this cycle (`grep -rln _is_fk_id_elided` hits only these two archived specs plus review scratchpads).

## What looks solid

### DRY recap

- **Existing patterns reused.** The module single-sites its derivations through shared helpers rather than re-spelling them: the optimizer's canonical sentinels (`DST_OPTIMIZER_FK_ID_ELISIONS` / `DST_OPTIMIZER_PLANNED` / `DST_OPTIMIZER_STRICTNESS` + `get_context_value` from `optimizer/_context.py`) and the canonical key builders (`resolver_key`, `runtime_path_from_info` from `optimizer/plans.py`); the N+1 logger is aliased (not re-created) from `optimizer.logger`; `FieldMeta` shape construction goes through the canonical `FieldMeta.from_django_field` / `_from_field_shape` (`resolvers.py::_field_meta_for_resolver`) so relation-kind classification cannot drift from the walker's; cardinality dispatch reuses `is_many_side_relation_kind` + `instance_accessor` from `utils/relations`; file-column routing reuses `_field_output_type_for` from `types/converters.py` — the one MRO-walk home for `FIELD_OUTPUT_TYPE_MAP`, shared by `convert_field_output` + `inspect_django_type` + `_attach_file_resolvers`. `_name_resolver` centralises the `resolve_<field>` rename across all four generated resolvers. The L3 feedback refactor (`planned` / `precomputed_key` / `_PLAN_UNREAD` threading) is itself a DRY win — it collapses a duplicated `info.path` walk between the elision and N+1 checks into one per row.
- **New helpers considered.** `_fk_attname_is_deferred` was extracted from `_build_fk_id_stub` as a named single-source loaded-signal for the FK *column* — correct extraction, mirrors `_will_lazy_load_single` for the relation *instance*. The shared `__dict__` first-line fold was evaluated and deferred-with-trigger at N=2 (see DRY analysis). No candidate reaches act-now.
- **Duplication risk in the current file.** Two near-twin pairs are intentional sibling design, not copies: (1) the two `__dict__`-probe loaded-checks over two distinct Django caches (column-deferral vs relation-instance); (2) `_attach_file_resolvers` is the deliberate structural twin of `_attach_relation_resolvers` (same Phase-2 iterate-skip-attach shape) but with an intentionally divergent skip set — relation pass uses `consumer_assigned_relation_fields` (assigned overrides only), file pass uses the broader `consumer_authored_fields` union so an annotation-only `attachment: str` opt-out is also honored (spec-037 Decision 3, confirmed at `finalizer.py::finalize_django_types` #"_attach_file_resolvers"). The three cardinality resolver closures share the `_check_n1(...)` preamble but have genuinely distinct bodies; folding would re-couple divergent logic.

### Other positives

- **Optimizer hand-off is correct (the data-correctness crux).** `_check_n1` reads `DST_OPTIMIZER_PLANNED` and returns immediately when the plan sentinel is absent (no optimizer in play). The walker invariant — every key in `fk_id_elisions` is also in `planned` (`_record_relation_access` records the planned key before the elision append) — is exactly why `force_unplanned` must exist: an elided-but-deferred FK key would otherwise short-circuit `_check_n1` on the planned membership and stay silent. The guard chain `_fk_attname_is_deferred` → `_build_fk_id_stub` returns `_FK_ELISION_UNSAFE` → `forward_resolver` sets `elision_unsafe=True` → `_check_n1(force_unplanned=True)` bypasses the planned short-circuit and re-probes the lazy-load. No wrong / stale / leaked-data path found.
- **`_prefetched_objects_cache` / `fields_cache` reads are right.** `many_resolver` reads `_prefetched_objects_cache[accessor_name]`, returns `_result_cache` when present else the cached manager, and falls through to `list(getattr(root, accessor_name).all())` on any miss — same rows, same order, skipping the QuerySet clone + list copy on the hot path (feedback H1). Keyed on `accessor_name` (not `field_name`), matching what Django stores under for reverse relations without `related_name`. The many-side cache check (`_will_lazy_load_many`) reads ONLY `_prefetched_objects_cache` and deliberately does NOT apply the single-valued `__dict__` short-circuit — the inline comment correctly notes that doing so would silently exempt the many-side strictness path.
- **Empty-file parent-null guard is right.** `_make_file_resolver` returns `value if value else None`, and the falsy-`FieldFile`→`None` contract is the documented cross-module invariant that lets `converters._safe_file_attr` assume "always truthy here" (`converters.py::_safe_file_attr` #"always truthy here"). The resolver carries NO `try/except` — storage-shaped failures (`ValueError` / `OSError` / `NotImplementedError`, and the deliberately-propagated `SuspiciousFileOperation`) surface later in per-subfield resolution, by design.
- **FK-id-elision deferred-column safety.** `_build_fk_id_stub` returns `_FK_ELISION_UNSAFE` BEFORE the `getattr(root, attname)` read when the column is deferred (a consumer `.only(...)` surviving B8 consumer-wins diffing) — the deferred column is never read, avoiding a silent per-row lazy load. `_fk_attname_is_deferred` confirms deferral only on a real Django instance via `get_deferred_fields()`, preserving the module-wide "test-double = loaded" contract. `router.db_for_read` hydrates `state.db` with the parent row as routing hint, correct multi-DB behavior.
- **Sync/async manager handling.** The generated resolvers are plain sync callables; `manager.all()` is prefetch-aware so the cached list is returned without a DB hit when prefetched, and Strawberry handles the async transport. This module never awaits, never seeds a visibility queryset, and contains no get_queryset / permission / async code (grep = zero) — so it is structurally incapable of a sync-context coroutine misuse or permission bypass.
- **No import-time side effects; privacy / export hygiene.** Module top level is imports + three module-constant sentinels (`_EMPTY_ELISIONS`, `_PLAN_UNREAD`, `_FK_ELISION_UNSAFE`) + defs — no ORM query, schema build, or registry mutation at import. The docstring's "resolvers.py imports nothing from base.py" invariant holds (confirmed in the import list). Every symbol is `_`-prefixed; `types/__init__.py` `__all__` is `("DjangoType", "SyncMisuseError", "finalize_django_types")` — none of these resolvers leak.

### Summary

`resolvers.py` is unchanged across this cycle's baseline (`git diff 0581cdde -- target` and `git diff HEAD -- target` both empty; `git log 0581cdde..HEAD -- target` returns nothing). The spawn-noted 0.0.11 file-resolver surface (`_make_file_resolver`, `_attach_file_resolvers`) plus the prior spec-035 Decision 5 hardening are fully cumulative-in-HEAD (last touch `ee1afb58`, predating the baseline). Reviewing the current source on its own merits: the optimizer hand-off (plan-sentinel read, `_prefetched_objects_cache` / `fields_cache` probes, `force_unplanned` defeating the planned short-circuit for a deferred-FK fallback), the empty-file parent-null guard pairing with `converters._safe_file_attr`, and the asymmetric file-vs-relation skip-set attachment are all correct and verified against their cross-module counterparts. No High, no Medium; one forward-looking Low (archived-spec citation of a removed helper) carries an explicit trigger and needs no edit. This is a genuine no-source-edit cycle (shape #5) — Worker 2 sections filled inline below.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, "289 files left unchanged".
- `uv run ruff check --fix .` — pass, "All checks passed!".

### Notes for Worker 3
- Genuine shape #5: `git diff 0581cdde9ed487b8504f4e1057f49120222983c9 -- django_strawberry_framework/types/resolvers.py`, `git diff HEAD -- …resolvers.py`, and `git log 0581cdde..HEAD -- …resolvers.py` are ALL empty. The 0.0.11 file-resolver work + spec-035 Decision 5 hardening are cumulative-in-HEAD (last touch `ee1afb58`).
- Single Low is forward-looking with a verbatim trigger (archived-spec `_is_fk_id_elided` citations under `docs/SPECS/`); no action this cycle. Re-confirmed via `grep -rln _is_fk_id_elided` (hits only the two archived specs + review scratchpads; zero in `django_strawberry_framework/`).
- No GLOSSARY-only fix in scope. All resolver symbols are private (`_`-prefixed, none in `types/__init__.py` `__all__`). The relevant GLOSSARY entries are contract-level for the PUBLIC `DjangoFileType` / `DjangoImageType` / `Meta.required_overrides` / `Upload` symbols (GLOSSARY lines 334 / 894 / 892 / 1361) and were re-verified accurate against `_make_file_resolver`'s falsy-`FieldFile`→`None` contract and `_attach_file_resolvers`' `consumer_authored_fields` opt-out.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits — the module's docstrings and inline comments (logger-alias rationale, `__dict__`-probe divergence, `force_unplanned` / `_FK_ELISION_UNSAFE` spec-035 Decision-5 notes, the file-vs-relation skip-set asymmetry) accurately describe the current code and the verified cross-module contracts.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. **Not warranted** — no source change this cycle (zero tracked-file edits). AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_11.md`, silent on changelog edits) both apply.

---

## Verification (Worker 3)

### Logic verification outcome
Genuine shape #5 (no-source-edit) confirmed and accepted. Zero-edit proof clean on all axes: `git diff 0581cdde9ed487b8504f4e1057f49120222983c9 -- django_strawberry_framework/types/resolvers.py`, `git diff HEAD -- …resolvers.py`, and `git log 0581cdde..HEAD -- …resolvers.py` are ALL empty; the owned-paths `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) is empty, so there is no sibling-cycle attribution to record. The dirty working tree (`docs/dry/`, `docs/feedback2.md`, the `docs/review/rev-*.md` family, `docs/spec-038-…`) is all docs scratch, none of it an owned source path. Each Worker 2 section opens with the `Filled by Worker 1 per no-source-edit cycle pattern.` gate line.

High `None.` / Medium `None.` independently confirmed genuine by reading current source against the three named cross-module counterparts:

- **Optimizer hand-off (`force_unplanned`).** Confirmed the walker invariant at source: `_record_relation_access` appends `resolver_identities` to `plan.planned_resolver_keys` UNCONDITIONALLY (`walker.py::_record_relation_access` #"append_unique_many(plan.planned_resolver_keys") and runs at `_plan_select_relation` #"_record_relation_access(" BEFORE the elision branch appends the same identities to `plan.fk_id_elisions` (`walker.py` #"append_unique_many(plan.fk_id_elisions"). So every elided key is also a planned key — exactly why `forward_resolver` must set `force_unplanned=True` (`resolvers.py::_make_relation_resolver.forward_resolver` #"force_unplanned=elision_unsafe") to defeat the `key in planned and not force_unplanned` short-circuit (`resolvers.py::_check_n1` #"key in planned and not force_unplanned") when the deferred-FK fallback fires, keeping the access strictness-visible rather than silently lazy-loading a planned relation.
- **`_prefetched_objects_cache` keyed on `accessor_name`.** `many_resolver` reads `prefetched.get(accessor_name)` and returns `_result_cache` when present else the cached manager, falling through to `list(getattr(root, accessor_name).all())` on a miss — keyed on `accessor_name` (`instance_accessor(field)`), not `field_name`, matching Django's reverse-relation storage without `related_name`. `_will_lazy_load_many` reads ONLY `_prefetched_objects_cache` and deliberately omits the single-valued `__dict__` short-circuit (the inline comment and `_will_lazy_load_single`'s divergent `fields_cache` tail confirm the two probes answer two different questions over two different caches).
- **Empty-file parent-null guard.** `_make_file_resolver` returns `value if value else None` (`resolvers.py::_make_file_resolver.file_resolver` #"return value if value else None"); independently confirmed the matching invariant in `converters._safe_file_attr` (`converters.py::_safe_file_attr` #"always truthy here -- an empty") whose docstring states "an empty file resolves the whole object to ``None`` before any subfield runs." The narrow catch `(ValueError, OSError, NotImplementedError)` correctly excludes `SuspiciousFileOperation` (a `SuspiciousOperation`, not in the tuple) so the path-traversal signal propagates. The parent resolver carries no `try/except`, by design.
- **File-resolver attachment skip-set asymmetry.** Confirmed at the finalizer call sites: relation pass uses `skip_field_names=definition.consumer_assigned_relation_fields` (`finalizer.py::finalize_django_types` #"skip_field_names=definition.consumer_assigned_relation_fields"); the file pass uses the BROADER `skip_field_names=definition.consumer_authored_fields` (`finalizer.py` #"skip_field_names=definition.consumer_authored_fields"), so an annotation-only `attachment: str` opt-out is also honored (spec-037 Decision 3).

The single Low is genuinely forward-looking: `grep -rln _is_fk_id_elided` over `*.py`/`*.md` hits ONLY the two archived design docs (`docs/SPECS/spec-015-relay_interfaces-0_0_5.md`, `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md`) plus review scratchpads (and a worktree mirror) — ZERO occurrences in `django_strawberry_framework/`. AGENTS.md #27's grep-sweep-on-rename targets live code/standing docs; archived specs under `docs/SPECS/` are frozen history, so this is a non-defect-today forward-Low with a verbatim trigger, no edit this cycle.

### DRY findings disposition
DRY-None accepted. The `<name> in getattr(root, "__dict__", {})` first-line probe shared by `_will_lazy_load_single` (relation-instance cache via `_state.fields_cache`) and `_fk_attname_is_deferred` (FK-column-deferral cache via `get_deferred_fields()`) is a deliberate sibling probe over two distinct Django caches; the bodies diverge immediately, so folding only the shared line at N=2 is net-negative. Deferred with the explicit N=3 trigger. `_attach_file_resolvers` vs `_attach_relation_resolvers` is intentional structural-twin design with the verified divergent skip set (above). No act-now DRY candidate.

### Temp test verification
None needed — no source edit, no new behavior to pin; all claims verified by reading live source and grep against cross-module counterparts.

### Changelog verification
`Not warranted` accepted. `git diff -- CHANGELOG.md` is empty. Disposition cites BOTH AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence (`docs/review/review-0_0_11.md`). Internal-only framing matches the diff scope (zero tracked edits; all resolver symbols private — `types/__init__.__all__` is `("DjangoType", "SyncMisuseError", "finalize_django_types")`, none of these resolvers leak).

### GLOSSARY (#4-vs-#5 gate)
Genuine #5, no missed #4. All resolver symbols are `_`-prefixed private and absent from `types/__init__.__all__`; `grep` for `_make_file_resolver` / `_attach_file_resolvers` / `_check_n1` / `_build_fk_id_stub` / `force_unplanned` / `_will_lazy_load` in `docs/GLOSSARY.md` returns nothing → absence is correct, not drift. No GLOSSARY-only fix in scope.

### Comment/docstring verification
Accepted. No comment/docstring edits this cycle; the existing docstrings (logger-alias rationale, `__dict__`-probe divergence, `force_unplanned`/`_FK_ELISION_UNSAFE` spec-035 Decision-5 notes, file-vs-relation skip-set asymmetry) accurately describe the current code and the verified cross-module contracts.

### Validation
`uv run ruff format --check django_strawberry_framework/types/resolvers.py` → "1 file already formatted"; `uv run ruff check …resolvers.py` → "All checks passed!".

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `types/resolvers.py` checklist box in `docs/review/review-0_0_11.md`.

---

## Iteration log

- Worker 1 (shape #5): reviewed current source; both baseline and HEAD diffs empty; no High/Medium; one forward-looking Low carried with trigger; ruff both clean; `Status: fix-implemented`.
- Worker 3 (verification): zero-edit proof clean on all axes; optimizer hand-off / `_prefetched_objects_cache` accessor keying / empty-file parent-null guard / file-vs-relation skip-set asymmetry independently confirmed at source against walker.py + converters.py + finalizer.py; Low confirmed forward-looking (grep of `_is_fk_id_elided` = zero in package source); genuine #5 (private symbols, no GLOSSARY drift); changelog `Not warranted` both-cited; ruff clean. `cycle accepted; verified`.
