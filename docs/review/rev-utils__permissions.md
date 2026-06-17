# Review: `django_strawberry_framework/utils/permissions.py`

Status: verified

## DRY analysis

- None — this module IS the consolidation point (the 0.0.9 DRY pass, `docs/feedback.md` Major 3, plus the 79b74b46 feedback-H3 single-pass fusion). The whole point of the file is that FilterSet and OrderSet independently grew the same active-input permission contract and a divergence is an authorization-bug class, so the neutral mechanics are single-sited here. The single-pass classifier `active_permission_targets` (lines 161-208) is itself the source; `active_related_branches` (211-253) and `active_permission_field_paths` (256-300) are deliberately kept as thin wrappers over it precisely so the LEAF/RELATED classification rule stays single-sited — re-merging the wrappers into the partition (or vice versa) would re-introduce the duplication this commit removed. `verbatim_path` (149-158) is the shared identity `fallback_path` consumed by both the in-file `active_related_branches` (line 249) and the order side `OrderSet._active_permission_targets` (`orders/sets.py:362`); it is module-level (not a per-call lambda) specifically to avoid allocating a fresh closure each order-side walk — already the maximally-DRY shape. `_check_method_name` (46-54) single-sites the `check_<field>_permission` name transform behind an `lru_cache`. `iter_input_items` is re-exported (line 67) from `utils/input_values.py` only to preserve the legacy import path — not a re-implementation.

## High:

None.

## Medium:

None.

## Low:

### `active_related_branches` discards the LEAF half it computes, so `fallback_path=verbatim_path` is dead inside that call

`active_related_branches` (lines 211-253) delegates to `active_permission_targets` with `field_specs={}`, `logic_keys=frozenset()`, `fallback_path=verbatim_path`, then returns only `branches`. Because every field with no field-spec entry classifies as LEAF and the LEAF list is discarded (`_leaf_paths` unused), `verbatim_path` is never actually invoked through this path — it is passed only to satisfy the now-required `fallback_path` keyword. This is correct and intentional (the wrapper exists to keep the single-pass classification single-sited per feedback H3), not a defect: the cost is one always-discarded `leaf_paths` list per `active_related_branches` call. Correct as-is — the partition genuinely runs in one walk and the discarded list is `O(active-leaf-fields)`, negligible at the per-input-level scale this runs at. Defer: revisit only if a profiler shows the discarded-LEAF allocation is hot, or if a future caller needs the RELATED half *without* paying for LEAF classification — at that point split `iter_active_fields` consumption by an early-skip on `kind`. Note that `verbatim_path`'s real execution is via the order side (`orders/sets.py:362`, covered by `tests/orders/test_sets.py::test_orderset_active_permission_field_paths_falls_back_to_python_attr_when_no_field_spec_entry`), so the symbol is not untested dead code.

### `verbatim_path` has no dedicated unit test, only transitive coverage

`verbatim_path` (149-158) is exercised transitively — through the order side's `_active_permission_targets` fallback (`tests/orders/test_sets.py:513`) and passed (but discarded) through `active_related_branches`. There is no direct `tests/utils/test_permissions.py` assertion that `verbatim_path("a__b") == "a__b"`. The function is a one-line identity so the transitive coverage is sufficient for correctness, but a one-line direct test would pin the public-`__all__` contract (the symbol is now public surface) independent of the order side. Defer: add a direct assertion when `verbatim_path` next gains any non-identity behaviour, or if the order-side fallback test is ever removed/retargeted. Correct as-is under the 100% gate (the line is covered).

## What looks solid

### DRY recap

- **Existing patterns reused.** Consumes the shared `iter_active_fields` classifier + `SetInputTraversal` config + `is_inactive_value` + `iter_input_items` + `LEAF`/`RELATED` markers, all single-sited in `utils/input_values.py` (lines 35-42 import block). The same outward-fan, no-family-import shape as the other `utils/` consolidation siblings (`connections.py`, `inputs.py`, `input_values.py`) — duck-typed `cls` only, so both families import without a cycle (module docstring lines 21-23). `active_related_branches:243-252` and `active_permission_field_paths:290-299` correctly reuse the single `active_permission_targets` partition rather than re-spelling the `iter_active_fields` loop.
- **New helpers considered.** No new helper warranted. Considered folding `active_related_branches` / `active_permission_field_paths` back inline at their two `_active_permission_targets` call sites (`filters/sets.py:1289`, `orders/sets.py:339`) — rejected: they preserve the public `_active_permission_field_paths` shape (the `[0]` LEAF slice) the families documented, and folding would re-duplicate the LEAF-extraction across both families. Considered collapsing `active_permission_targets`'s two-list partition into a single tagged list — rejected: the two callers want exactly one half each, and `run_active_input_permission_checks` consumes both halves at line 333, so the `(leaf_paths, branches)` tuple is the natural shape.
- **Duplication risk in the current file.** The eight-keyword signatures of `active_permission_targets` / `active_permission_field_paths` (lines 161-171, 256-266) are near-identical, but that is the unavoidable pass-through of the same configuration superset — `active_permission_field_paths` forwards all eight to `active_permission_targets` verbatim. This is intentional thin-wrapper shape, not copy-paste logic. `_check_method_name` and `extract_branch_value`'s `is_inactive_value` use are distinct concerns, not a repeat.

### Other positives

- **Single-pass partition is exhaustive and disjoint.** Verified against `iter_active_fields` (`utils/input_values.py:173-182`): the `LOGIC` > `RELATED` > `LEAF` if/elif/else ladder assigns exactly one kind per active field, with the inactive-value skip (`is_inactive_value`) applied to both the whole input and each field before classification. `active_permission_targets` keeps only `LEAF` (gate paths) and `RELATED` (branches) and drops `LOGIC` (owned by the filter-side logical recursion) — the partition matches the docstring claim (lines 184-188) exactly. RELATED classification keys only off `related_attr` membership, independent of `field_specs`/`logic_keys`, so the empty-config `active_related_branches` call provably yields the same branch tuples it always did (docstring 238-241 confirmed against the classifier).
- **Reflective access is all safe-by-construction.** Every `getattr` uses a default: `getattr(info, "context", None)`, `getattr(context, "request", None)`, `getattr(input_value, field_name, None)`, `getattr(bare_instance, method_name, None)`, `getattr(related_obj, target_attr)` (the one without a default, line 338, is only reached after the RELATED classification guarantees `related_obj` is the declared sidecar instance). `callable(method)` gates the invoke; `hasattr(child_set, "_run_permission_checks")` gates the child recursion. No raw `_meta` reads, no `setattr`, no `__dict__` poking. Zero Django/ORM markers (confirmed by the shadow overview) — this is a pure traversal/dispatch module; the actual queryset visibility (`apply_type_visibility_sync`/`_async`) lives in `utils/querysets.py`, not here.
- **Per-class dedup is the documented parent-vs-child double dispatch.** `run_active_input_permission_checks` (303-345) keys `fired.setdefault(cls, set())` per class; the child set recurses into its OWN class entry (line 342) and the parent per-branch gate fires against the parent's set (line 345), so both fire exactly once — pinned by `tests/utils/test_permissions.py::test_run_active_input_permission_checks_double_dispatch_and_dedup` (asserts `parent.name`==1 despite a repeated path, `parent.child`==1, `child._run`==1).
- **Data-isolation contract is sound.** Gates key on the SOURCE field (one fire per declared field across all its lookups, via `field.spec.django_source_path`), so a consumer cannot bypass a gate by populating a different lookup of the same field. The active-input-only contract (inactive branches skipped end-to-end) means an empty branch does not exercise the child's gates — correct, an unsupplied branch carries no data to authorize. `request_from_info` raises `ConfigurationError` (not a silent None) when no request resolves, so a mis-wired consumer fails loud rather than running gates against `None`.
- **`verbatim_path` promotion is coherent in this file.** Public name (line 149, no leading underscore), in `__all__` (line 70), docstring (150-157) accurately describes both call sites (the discard caller + the order side) and the closure-allocation rationale; the internal caller `active_related_branches:249` uses the public name; no orphan `_verbatim_path` reference survives in source or tests (grep-confirmed). Already verified in the orders/sets.py cycle; confirmed consistent here per dispatch instruction.
- **Test discipline.** `tests/utils/test_permissions.py` covers `request_from_info` (all four shapes incl. both ConfigurationError raises), `extract_branch_value` (sentinel collapse + None), `invoke_permission_method` (fire/dedup/absent), `run_active_input_permission_checks` (double-dispatch), `active_related_branches` (empty-no-collection), and `active_permission_field_paths` (logic+related exclusion + fallback). `active_permission_targets` is exercised through both thin wrappers and the run-checks stub. No GLOSSARY mention of any symbol (grep empty) — no GLOSSARY drift to fix.

### Summary

Data-isolation-critical module reviewed at high rigor against current source (HEAD's 79b74b46 single-pass fusion + the working-tree `verbatim_path` promotion, the latter already-accepted from a prior cycle). The module is the deliberately-single-sited shared permission-traversal core for FilterSet/OrderSet; both `_active_permission_targets` callers (`filters/sets.py:1305`, `orders/sets.py:356`) confirmed to delegate here with family-specific config. The LEAF/RELATED partition is exhaustive, disjoint, and source-field-keyed; reflective access is uniformly defaulted-or-guarded; the parent-vs-child double dispatch fires each gate exactly once; zero Django/ORM surface. No High or Medium findings. Two forward Lows, both correct-as-is and trigger-gated (discarded-LEAF allocation in `active_related_branches`; no dedicated `verbatim_path` unit test). No logic finding needs a Worker 2 fix and the cycle produces zero edits to any tracked file, so this is a no-source-edit cycle (shape #5): Worker 2 sections filled inline below, both ruff commands run clean, top-level status set to bare `fix-implemented` for direct Worker 3 verification.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 270 files left unchanged (no edits).
- `uv run ruff check --fix .` — pass; All checks passed (no edits).

### Notes for Worker 3
No shadow regeneration (the plan-time `--all` sweep overview was current and used). No false-premise rejections. Two forward Lows, both correct-as-is and trigger-gated:
- **Low 1 (discarded-LEAF in `active_related_branches`)** — forward-looking, no action now; revisit on a profiler hot-path or a RELATED-only-without-LEAF caller.
- **Low 2 (no dedicated `verbatim_path` unit test)** — forward-looking, no action now; line is covered transitively under the 100% gate (`tests/orders/test_sets.py:513`), add a direct assertion when the symbol gains non-identity behaviour.

No GLOSSARY-only fix in scope (grep of `docs/GLOSSARY.md` for every symbol in this file returned empty). The dispatch's mention of `apply_type_visibility_sync`/`_async` is context (why this subsystem matters); those functions live in `utils/querysets.py` and are out of scope for this artifact.

---

## Verification (Worker 3)

Terminal-verify of the data-isolation-critical shared permission-traversal core, at maximum rigor. Every invariant below re-derived independently from LIVE source (`utils/permissions.py`, `utils/input_values.py::iter_active_fields`, `orders/sets.py::_active_permission_targets`) — the artifact was used as a checklist, never as the source of truth.

### Logic verification outcome

**Shape #5 zero-edit proof (this item).** `git diff HEAD -- django_strawberry_framework/utils/permissions.py` is the 14-line `verbatim_path` promotion ONLY (`_verbatim_path`→`verbatim_path`, `+"verbatim_path"` in `__all__`, internal caller at :249 repointed) — the prior-cycle change already accepted in the orders/sets.py cycle and confirmed coherent here per dispatch, NOT a new edit. `git log -1 -- <target>` = `79b74b46` (single-pass fusion). No NEW edits this cycle. CHANGELOG.md + GLOSSARY.md diffs both empty.

**Invariant 1 — partition exhaustive + disjoint, reproduces the prior two walks (the bypass-critical one).** Re-derived `active_permission_targets` (`:199-208`) against `iter_active_fields` (`input_values.py:163-182`): the `LOGIC` > `RELATED` > `LEAF` if/elif/else ladder (`:177-182`) assigns exactly one `kind` per active field; the inactive-value skip (`is_inactive_value`) fires on the whole input (`:163`) and per field (`:174`) before classification. `active_permission_targets` keeps `LEAF` (gate paths) + `RELATED` (branches) and drops `LOGIC` — matching the docstring (`:172-188`). RELATED keys ONLY off `related_attr` membership (`:179`), independent of `field_specs`/`logic_keys`, so the empty-config `active_related_branches` call provably yields the same branch tuples as the full-config partition. Proven by temp test (below): hand-derived LEAF/RELATED/LOGIC walk == fused partition == both wrappers; `seen == active_keys` (exhaustive) and no field classified twice (disjoint). A misclassification that would DROP a gate is excluded — `and_`/`branch_a`/`inactive` provably NOT in the LEAF half.

**Invariant 2 — no lookup-swap bypass.** LEAF paths key on `field.spec.django_source_path` (the lookup-free source field, `:202-203`), falling back to `fallback_path(python_attr)` only when no spec entry (`:204`). So `check_<field>_permission` fires once per SOURCE field regardless of which lookups a consumer populates — a consumer cannot substitute an ungated lookup of the same field for the gated one. Confirmed: temp test asserts a spec'd field keys on `source_one__lookup` (lookup stripped), spec-less falls back verbatim. Artifact "Data-isolation contract is sound" claim verified against source.

**Invariant 3 — undefaulted `getattr(related_obj, target_attr)` (`:338`) genuinely guarded.** It is inside the related-branch loop (`:337`), so `related_obj` is always `field.related_obj` from a RELATED record — i.e. `related[python_attr]` (`input_values.py:180`), the declared `RelatedFilter`/`RelatedOrder` sidecar instance, never a leaf value or `None`-from-classification. Temp test confirms: a RELATED `related_obj` carrying the slot resolves the child; a non-sidecar `object()` raises `AttributeError` (the guard IS the RELATED classification, not a getattr default). No wrong-instance, no silent-None.

**Invariant 4 — `verbatim_path` coherence.** Public (`:149`, no leading underscore), in `__all__` (`:70`), docstring (`:150-157`) accurately describes both call sites (the `active_related_branches` discard caller + the order side) and the closure-allocation rationale. Internal caller `:249` uses the public name; symbol-precise grep across `django_strawberry_framework/` + `tests/` returns exactly 5 hits (perm `__all__`/def/:249 use, orders import :47/use :362) — ZERO orphan `_verbatim_path`. Coherent.

All High (None) / Medium (None) / Low (2) dispositions verified. No finding requires a Worker 2 fix.

### DRY findings disposition

DRY=None accepted — this module IS the consolidation point (feedback H3 single-pass fusion). Verified by grep: `iter_active_fields`/`is_inactive_value`/`iter_input_items`/`SetInputTraversal`/`LEAF`/`RELATED` all single-sourced in `utils/input_values.py` (import block `:35-42`); `active_permission_targets` is the sole classifier and `active_related_branches`/`active_permission_field_paths` are thin wrappers returning one half each (`:243-253`, `:290-300`). Re-merging the wrappers into the partition (or vice versa) would re-introduce the cross-family duplication this commit removed. `_check_method_name` single-sites the name transform behind `lru_cache`. Sound.

### Temp test verification

- Temp test file: `docs/review/temp-tests/utils/test_permissions_partition.py` (gitignored).
- 5 tests, all pass (`uv run pytest ... --no-cov` → 5 passed): partition reproduces the two pre-consolidation walks + exhaustive + disjoint; `active_related_branches` empty-config == full-config RELATED half; `verbatim_path` identity; undefaulted `:338` getattr reached only after RELATED classification (sidecar resolves, non-sidecar raises AttributeError).
- Disposition: DELETED at cycle closeout by Worker 0; not promoted — every behavior is already pinned in the permanent suite (`tests/utils/test_permissions.py` 8 tests pass: double-dispatch dedup, logic+related exclusion, fallback; `tests/orders/test_sets.py::test_orderset_active_permission_field_paths_falls_back_to_python_attr_when_no_field_spec_entry` :513 covers `verbatim_path` execution under the 100% gate). The temp tests are verification corroboration, not the sole proof of any shipped behavior — no Medium-for-promotion finding.

### Forward-looking Lows

Both Lows correct-as-is and trigger-gated, no source-site TODO owed (each gates on a FUTURE change — a profiler hot-path / `verbatim_path` gaining non-identity behavior — not a staged framework slice, so AGENTS.md #26 NotImplementedError/TODO is correctly not triggered): L1 (discarded-LEAF allocation in `active_related_branches`, `O(active-leaf-fields)`, negligible); L2 (no dedicated `verbatim_path` unit test — line covered transitively under the 100% gate via the order-side fallback test). GLOSSARY grep for every symbol returned empty (the `verbatim` hit at GLOSSARY.md:492 is unrelated prose about django-graphene-filters lazy resolution, not a symbol mention) — no GLOSSARY drift, no GLOSSARY-only fix.

### Changelog disposition

`Not warranted` — verified: `git diff -- CHANGELOG.md` empty; disposition cites BOTH AGENTS.md #21 AND the active plan `review-0_0_10.md`'s silence. Internal-only framing is honest — zero new source edits this cycle (the `verbatim_path` promotion is a prior closed cycle; `__all__` membership is internal hygiene, not a new public-API surface this cycle). Accepted.

### Comment/docstring pass

No-source-edit cycle — no comment/docstring changes to review. The docstrings on the reviewed (already-merged) surface were verified accurate against final behavior during the logic pass above (partition docstring `:172-188`, `verbatim_path` `:150-157`, run-checks double-dispatch `:312-325`).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `utils/permissions.py` checklist box in `docs/review/review-0_0_10.md`.

---

## Comment/docstring pass

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source edit this cycle (internal-only review of already-merged + already-accepted changes). AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `review-0_0_10.md` is silent on any changelog entry for this item.

---

## Iteration log
