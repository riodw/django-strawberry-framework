# Review: `django_strawberry_framework/utils/permissions.py`

Status: fix-implemented

## DRY analysis

- None — this module IS the resolution of the FilterSet/OrderSet active-input permission duplication (the 0.0.9 DRY pass, `docs/feedback.md` Major 3; the feedback-H3 single-pass fusion). FilterSet and OrderSet independently grew the same active-input permission contract and a divergence is an authorization-bug class, so the neutral mechanics are single-sited here. The single-pass classifier `active_permission_targets` (`utils/permissions.py:164-211`) is the sole source; `active_related_branches` (`:214-256`) and `active_permission_field_paths` (`:259-303`) are deliberately thin wrappers returning one half each so the LEAF/RELATED classification rule stays single-sited — re-merging the wrappers (or vice versa) would re-introduce the cross-family duplication this removed. `verbatim_path` (`:152-161`) is the shared identity `fallback_path` consumed by the in-file `active_related_branches` (`:252`) and the order side `OrderSet._active_permission_targets` (`orders/sets.py:362`); module-level (not a per-call lambda) to avoid allocating a fresh closure each order-side walk — already maximally DRY. `_check_method_name` (`:46-54`) single-sites the `check_<field>_permission` name transform behind an `lru_cache`. `iter_input_items` is re-exported (`:67`) from `utils/input_values.py` only to preserve the legacy import path — not a re-implementation.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** Consumes the shared `iter_active_fields` classifier + `SetInputTraversal` config + `is_inactive_value` + `iter_input_items` + `LEAF`/`RELATED` markers, all single-sited in `utils/input_values.py` (import block `utils/permissions.py:35-42`). Same outward-fan, no-family-import shape as the other `utils/` consolidation siblings (`connections.py`, `inputs.py`, `input_values.py`) — duck-typed `cls` only, so both families import without a cycle (module docstring `:21-23`). `active_related_branches` (`:246-255`) and `active_permission_field_paths` (`:293-302`) reuse the single `active_permission_targets` partition rather than re-spelling the `iter_active_fields` loop.
- **New helpers considered.** No new helper warranted. Folding `active_related_branches` / `active_permission_field_paths` back inline at their two `_active_permission_targets` call sites (`filters/sets.py:1312`, `orders/sets.py:356`) — rejected: they preserve the public `_active_permission_field_paths` `[0]` LEAF-slice shape both families documented, and folding would re-duplicate LEAF-extraction across both families. Collapsing the two-list partition into a single tagged list — rejected: each caller wants exactly one half, and `run_active_input_permission_checks` consumes both halves (`:336`), so the `(leaf_paths, branches)` tuple is the natural shape.
- **Duplication risk in the current file.** The eight-keyword signatures of `active_permission_targets` / `active_permission_field_paths` (`:164-174`, `:259-269`) are near-identical, but that is the unavoidable pass-through of the same configuration superset — `active_permission_field_paths` forwards all eight verbatim. Intentional thin-wrapper shape, not copy-paste logic. Zero repeated string literals (static overview confirms).

### Other positives

- **Single-pass partition is exhaustive and disjoint.** Verified against `iter_active_fields` (`utils/input_values.py`): the `LOGIC` > `RELATED` > `LEAF` ladder assigns exactly one kind per active field, with the inactive-value skip (`is_inactive_value`) applied to both the whole input and each field before classification. `active_permission_targets` keeps only `LEAF` (gate paths) and `RELATED` (branches) and drops `LOGIC` (owned by the filter-side logical recursion) — matches the docstring (`:184-188`). RELATED classification keys only off `related_attr` membership, independent of `field_specs`/`logic_keys`, so the empty-config `active_related_branches` call provably yields the same branch tuples it always did (docstring `:238-244` confirmed against the classifier).
- **Family-neutral contract holds at source.** Operates only on a duck-typed `cls` and imports neither family package; both `filters/sets.py` and `orders/sets.py` import it without a cycle. Filter side passes `unset_sentinel=UNSET` + a real lookup→form-key remap; order side passes `unset_sentinel=None` + `verbatim_path` + `handle_top_level_list=True` (`orders/sets.py:356-364`). `request_from_info` raises `ConfigurationError` naming the **family-neutral** `family_label` (`FilterSet`/`OrderSet`/`DjangoMutation`) with no `.apply` suffix — correct, since the mutation `check_permission` seam (`mutations/permissions.py:94`) has no `.apply` method (feedback CR-5).
- **Active-input-only scope verified.** `extract_branch_value` collapses `None` and the family `unset_sentinel` to "branch not supplied"; `iter_active_fields` skips inactive values inside the classifier; `active_related_branches` scopes a branch active purely on key presence so an empty branch does not exercise child gates. No gate fires for an unsupplied field — the active-input-only guarantee.
- **Reflective access is all safe-by-construction.** Every `getattr` uses a default — `getattr(info,"context",None)`, `getattr(context,"request",None)`, `getattr(input_value,field_name,None)`, `getattr(bare_instance,method_name,None)` — except `getattr(related_obj,target_attr)` (`:341`), which is reached only after the RELATED classification guarantees `related_obj` is the declared sidecar instance. `callable(method)` gates the invoke; `hasattr(child_set,"_run_permission_checks")` (`:342`) gates the child recursion. Zero Django/ORM markers (shadow overview confirms) — actual queryset visibility lives in `utils/querysets.py`, not here.
- **Per-class dedup is the documented parent-vs-child double dispatch.** `run_active_input_permission_checks` (`:306-348`) keys `fired.setdefault(cls, set())` per class; the child set recurses into its OWN class entry (`:345`) and the parent per-branch gate fires against the parent's set (`:348`), so both fire exactly once. Gates key on the SOURCE field (`field.spec.django_source_path`), so a consumer cannot bypass a gate by populating a different lookup of the same field. `_check_method_name` is `lru_cache(maxsize=2048)` over the bounded declared-path set (request-independent), keeping only the bound-instance probe per-request (feedback L5).

### Summary

`utils/permissions.py` is the deliberately single-sited active-input permission-traversal core shared by the FilterSet and OrderSet families (and, for `request_from_info`, the mutation seam). It is unchanged this cycle: both `git diff be1d5b23540b2ea2b2e991585b93a9bcf744aa7e -- target` and `git diff HEAD -- target` are empty, and `git log baseline..HEAD -- target` returns nothing — the `verbatim_path` promotion the spawn flagged landed earlier (commit 8d6ca99b "Finish REVIEW") and is cumulative-in-HEAD, with the last touch to the file at `bd998093`. The family-neutral contract, active-input-only scope, and `verbatim_path` identity-fallback helper all verify at source; the LEAF/RELATED partition is exhaustive, disjoint, and source-field-keyed; reflective access is uniformly defaulted-or-guarded; the parent-vs-child double dispatch fires each gate exactly once. No symbol is public-contract (none appear in `docs/GLOSSARY.md`; the package-root `from .permissions import` resolves to the distinct *top-level* `permissions.py`, not this `utils/` module) so GLOSSARY absence is correct. No High / Medium / Low findings. Genuine shape #5 (no-source-edit cycle).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — `289 files left unchanged` (COM812-formatter-conflict warning only; pre-existing/benign, no edits).
- `uv run ruff check --fix .` — `All checks passed!`

### Notes for Worker 3
- No-source-edit cycle: both `git diff be1d5b23540b2ea2b2e991585b93a9bcf744aa7e -- django_strawberry_framework/utils/permissions.py` and `git diff HEAD -- …` are empty; `git log baseline..HEAD -- target` returns nothing. The `verbatim_path` promotion (public + in `__all__`, used as `fallback_path` by `active_related_branches` at `:252` and `orders/sets.py:362`) is cumulative-in-HEAD (commit 8d6ca99b; last file touch `bd998093`), not a pending edit.
- All severities `None.` — nothing forward-looking to carry forward.
- No GLOSSARY-only fix in scope: grep of `docs/GLOSSARY.md` for every backticked symbol from this file (`verbatim_path`, `run_active_input_permission_checks`, `active_permission_targets`, `active_related_branches`, `active_permission_field_paths`, `invoke_permission_method`, `request_from_info`, `extract_branch_value`, `iter_input_items`, `_check_method_name`) returns zero hits — all are private `utils/` helpers (not re-exported from the package root; the root `from .permissions import` is the distinct top-level module), so absence is correct, not drift.
- Orphan check: `verbatim_path` has real first-party consumers (`utils/permissions.py:252`, `orders/sets.py:362`); `git log -S 'def verbatim_path'` shows it was introduced by the REVIEW-cycle promotion (8d6ca99b) and `grep _verbatim_path` returns zero — twin fully removed, no orphan.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits. The module docstring (`:1-24`), the `# ONE active-input traversal …` block (`:332-335`), and the `# Child set …` / `# Per-branch gate …` comments (`:343-347`) accurately describe the single-pass partition and the parent-vs-child double dispatch; verified against the code. The `iter_input_items` re-export comment (`:57-60`) correctly states the symbol is single-sited in `utils/input_values.py` — confirmed by grep (sole `def iter_input_items` is `utils/input_values.py:53`).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — zero edits to any tracked file this cycle. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md` (silent on changelog edits for review cycles), no changelog entry is warranted.

---

## Verification (Worker 3)
