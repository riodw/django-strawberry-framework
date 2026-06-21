# Review: `django_strawberry_framework/optimizer/walker.py`

Status: verified

## DRY analysis

- **`_target_pk_name` recompute twin shared with `field_meta.py`.** `walker.py::_target_pk_name` (walker.py:873-881) is a `getattr(field, "target_pk_name", None)`-first shim whose recompute fallback reads `related_model._meta.pk.name` — byte-equivalent to `field_meta.py::_target_pk_name` (field_meta.py:232-246), which does the same off a model. Note the input-contract divergence: the walker's takes a **field/FieldMeta** and dereferences `.related_model`, while `field_meta.py`'s takes a **model** directly — consolidation needs a shared free function spanning both files. (The sibling `_can_elide_fk_id` predicate twin that the prior cycle flagged here is now RESOLVED — commit `3b4f90c0` routed the walker's raw-field fallback through `FieldMeta._from_field_shape`, so the eligibility *predicate* is single-sourced; only the `_target_pk_name` model-pk lookup still hand-recomputes.) **Defer with trigger:** "walker's raw-descriptor recompute fallback is removed" — i.e. once a registry-coverage gate guarantees every field reaching the walker is `FieldMeta`-stamped, the `_target_pk_name` recompute tail deletes and the dual path collapses. Forward to `docs/review/rev-optimizer.md` (folder pass) for the cross-file disposition.

- **The wide relation-context argument bundle threaded through four projection-writer call sites.** `_plan_select_relation` / `_plan_prefetch_relation` / `_record_relation_access` / `_apply_hint`'s two re-dispatches all thread the same `(plan, prefix, info, runtime_paths, resolver_identities, enable_only)` bundle alongside the relation tuple (walker.py:449-473, 716-722, 739-763, 765-776). The same wide-argument-list candidate prior cycles flagged on `_plan_select_relation` / `_plan_prefetch_relation`. **Defer with trigger:** "the planner gains a further per-relation context member beyond `enable_only`" — at that point fold `(plan, prefix, info, runtime_paths, resolver_identities, enable_only)` into a frozen `RelationWalkContext` dataclass threaded once. Acting now is net-neutral (the bundle is still readable at four sites); the dataclass earns its keep on the next added member. Forward to `docs/review/rev-optimizer.md` since the same shape recurs across walker helpers.

## High:

None.

## Medium:

None.

## Low:

### `_connector_only_field` M2M branch reads `related_model._meta.pk.attname` raw (walker.py:928)

The M2M branch returns `parent_field.related_model._meta.pk.attname` with no `getattr` guard, unlike the reverse-FK / forward-single-valued branches above it (walker.py:916-927) which are fully `getattr`-defensive with a stamped-slot fallback. The asymmetry is **safe today**: the branch is reached only when `parent_field.many_to_many` is True (line 922 negates and returns first), which on any real Django M2M field guarantees a non-`None` `related_model` carrying `_meta.pk`. A partial test double that sets `many_to_many=True` without a real `related_model._meta` would `AttributeError` rather than returning `None` — but that matches the package's "fail loud on malformed double" posture for the connector column, and no stamped-slot equivalent exists for the M2M pk attname. Pre-existing (not a `3b4f90c0` change). **Defer with trigger:** "a stamped `m2m_connector_attname` (or equivalent) slot is added to `FieldMeta`" — at that point mirror the two branches above with a `getattr(..., None) or getattr(parent_field, "<slot>", None)` shape so all three connector branches share one defensive idiom. No source edit warranted now.

## What looks solid

### DRY recap

- **Existing patterns reused.** The walker routes every shared selection-traversal primitive through the `optimizer/selections.py` underscore aliases bound at module top (walker.py:55-62), the 0.0.9 DRY consolidation (`docs/feedback.md` Major 2) — the walker and the `extension.py` AST seam share ONE fragment / directive / response-key / `edges { node }`-unwrap implementation. Plan-time prefetch visibility reuses `utils/querysets.py::apply_type_visibility_sync` (walker.py:244) so plan-time and resolve-time visibility cannot drift. Window bounds reuse `utils/connections.py::derive_connection_window_bounds` via the thin `_connection_window_slice` adapter (walker.py:1284) so plan-time and resolve-time windows share one rule. The `_dst_<field>_connection` `to_attr` literal is single-sourced in `_relation_connection_to_attr` (walker.py:1161-1170). `_resolver_identities_for` (walker.py:248-284) is correctly shared by the list-relation walk and the connection planner with the field-name-vs-accessor vocabulary split documented. **This cycle's `3b4f90c0` change is itself a DRY win:** `_can_elide_fk_id`'s raw-field fallback now delegates to `FieldMeta._from_field_shape(field, is_relation=True).fk_id_elision_eligible` (walker.py:870) instead of hand-copying the 7-clause predicate, so the walker and `FieldMeta` share ONE elision decider — the same delegation `types/resolvers.py::_field_meta_for_resolver` already uses.
- **New helpers considered.** Considered hoisting the spec-035 G2 gate into a plan-level flag on `OptimizationPlan` rather than a threaded `enable_only` parameter; rejected because Decision 4 pins build-time threading through all four projection writers (one writer, `_project_scalar_only_window`, applies `.only(...)` without ever touching `plan.only_fields`, so a plan-attribute or post-hoc-clear sweep cannot reach it). The parameter threading is the correct shape, not a DRY smell. The `_can_elide_fk_id` predicate consolidation that prior cycles considered for this file is now done in production (`3b4f90c0`); only the `_target_pk_name` model-pk lookup recompute remains (deferred above, cross-file).
- **Duplication risk in the current file.** The repeated `enable_only=enable_only` forwarding across the dispatch tree (walker.py:449-473, 745-763) is intentional single-decision propagation, not duplication — the gate is derived ONCE in `plan_optimizations` (walker.py:109) and threaded so root, child, and window plans share one operation decision. The shadow's repeated literals (`arguments` 5x, `prefetch` 3x, `related_model` 2x, `_optimizer_runtime_prefixes` 2x, `selections` 2x) are reflective-access attribute names / dict keys read at structurally distinct sites, not a string-keyed-dispatch DRY signal.

### Other positives

- **Maintainer FK-id-elision→`FieldMeta` change (commit `3b4f90c0`) preserves semantics — verified clause-by-clause.** `_can_elide_fk_id` keeps the stamped fast-path (`getattr(field, "fk_id_elision_eligible", None)` returned directly for a registered `FieldMeta`, walker.py:867-869) and only the raw-field fallback changed (walker.py:870). Comparing the pre-`3b4f90c0` hand-copied predicate against `FieldMeta._from_field_shape` (field_meta.py:216-225), the conjunct set is identical: `attname is not None`, `related_model is not None`, `target_pk_name is not None`, `target_field_name == target_pk_name`, `not many_to_many`, `not one_to_many`, `not auto_created`, `not has_composite_pk(related_model)`. The composite-PK exclusion (previously a separate `pragma: no cover` guard) is now an inline conjunct evaluated only after `related_model is not None` short-circuits — same fail-closed result, no `None` deref. `target_pk_name` derivation is equivalent (`field_meta.py::_target_pk_name(related_model)` reads `related_model._meta.pk.name` defensively, matching the old `_target_pk_name(field)` reading `field.related_model._meta.pk.name`). The old `getattr(field, "target_field_name", None)` fallback branch was dead on the raw-field path the fallback now serves (a raw forward Django `ForeignKey` always exposes `target_field`, so `getattr(target_field, "name", None)` resolves; only synthetic `FieldMeta`-shaped inputs — which carry the stamped slot and never reach the fallback — would have used it), so dropping it is behavior-preserving. The `related_model is None` case short-circuits to `False` on both old and new paths (the only test reaching the fallback, per the commit message).
- **The dispatch-named "model_for promotion" does NOT touch walker.** `grep model_for django_strawberry_framework/optimizer/walker.py` is empty; the walker's visibility seam uses `utils/querysets.py::apply_type_visibility_sync` (`_build_child_queryset`, walker.py:244), not `model_for`. The `model_for` promotion (commit `7a17ba75`) landed in `connection.py` / `relay.py` / `mutations/resolvers.py`, out of scope for this file.
- **The spec-035 G2 gate is implemented exactly to Decision 4's four-writer contract.** All four `only_fields` / `.only(...)` writers consult the gate: `_walk_selections` (Relay custom-pk append walker.py:398, scalar-leaf append walker.py:417), `_record_relation_access` (FK connector append walker.py:612 — the writer that makes `only_fields` non-empty *independently* of scalar leaves, the leak the naive "block scalar appends" mechanism misses), `_ensure_connector_only_fields` (early return walker.py:1022, correctly BEFORE the empty-`only_fields` guard at walker.py:1024), and `_project_scalar_only_window` (early return walker.py:993 — the direct `.only(...)` that never lands in `only_fields`). The gate is derived once and threaded; `select_related` / `prefetch_related` / `fk_id_elisions` are untouched under non-`QUERY`.
- **FK-id elision stays correctly enabled under non-`QUERY` (Decision 5, walker half).** The elision branch in `_plan_select_relation` (walker.py:509-516) is independent of `enable_only`, so a mutation `{ relation { id } }` still records `fk_id_elisions` while the connector append is suppressed (full-row load guarantees the FK column is present). The consumer-`.only()`-defers-the-FK hazard is handled at resolve time in `types/resolvers.py` (loaded-check + loud sentinel fallback, out of scope) — the walker side is correct to keep the elision recorded.
- **Cacheable-flag writes are correct (plans.py / extension.py forward verified).** `plan.cacheable = False` is written at: custom-`get_queryset` prefetch downgrade (walker.py:568-569, set BEFORE the bare-lookup `related_model is None` early return), consumer-supplied Prefetch hint (walker.py:728, AFTER `rebased_prefetch` validation so a `ConfigurationError` leaves no phantom flip), and child-plan propagation (walker.py:647-648, 1416-1417). The `_plan_connection_relation` DISTINCT-guard early return (walker.py:1411-1412) does NOT flip parent cacheable — correct, because the request-scoped queryset was built only into the throwaway `sub_plan`/`child_queryset` and discarded on fallback; the parent absorbs child metadata only on the success path (walker.py:1415). `extension.py` inserts into the plan cache only `if plan.cacheable`, so no cross-request leak.
- **Downgrade-to-Prefetch-on-custom-`get_queryset` is the upstream-cribbed rule, applied consistently.** `plan_relation` (walker.py:136-145) downgrades to prefetch whenever `_target_has_custom_get_queryset`, and `_apply_hint`'s `force_select` path (walker.py:739-750) honors the same downgrade even against an explicit consumer `select_related()` hint — correct precedence (Django cannot `select_related` across a custom-`get_queryset` visibility boundary).
- **Connection-fallback shapes correctly partitioned between "fully unplanned" and "record-resolver-keys".** `_plan_connection_relation` leaves the field FULLY unplanned (no `planned_resolver_keys`) for sidecar / divergent-alias / hint-SKIP / DISTINCT / unwindowable-partition shapes so Slice-4 strictness sees the real per-parent access, but RECORDS resolver keys for the malformed-pagination `window is None` path (walker.py:1372) so strictness does not preempt the field's own cursor-validation error — the error-locality distinction (spec-033 Decision 5/8) is precisely implemented and documented.
- **Reflective-access audit clean.** Every `getattr` carries a default or is guarded by an upstream branch (e.g. the `type_cls.__name__` reads in `_apply_hint`/`force_select` are reachable only when `_resolve_optimizer_hints` returned non-empty, requiring `type_cls is not None` — documented at walker.py:690-696). The raw `_meta` accesses are each gated by an upstream presence check or a real-Django-field branch condition.
- **Both spec-035 TODO anchors validly scoped.** `TODO(spec-035 Slice 3)` at walker.py:323 and walker.py:840 name the G3 fragment-classifier deferral against the live `docs/spec-035-optimizer_hardening-0_0_10.md`. Per AGENTS.md #26 no `NotImplementedError` pairing is warranted — the default inline-all path is complete for every reachable shape; the classifier is purely additive future hardening that must NOT fail loudly. `docs/feedback.md` (the docstring cross-ref) also exists on disk.

### Summary

`walker.py` is the optimizer's core selection-tree → `OptimizationPlan` walker and is in excellent shape. The only this-cycle change (commit `3b4f90c0`) routes `_can_elide_fk_id`'s raw-field fallback through the canonical `FieldMeta._from_field_shape` predicate; a clause-by-clause comparison against the pre-commit hand-copied body confirms identical eligibility semantics (including the composite-PK fail-closed exclusion, the `related_model is None` short-circuit, and the dropped-`target_field_name`-fallback being dead on the raw-field path it serves). The dispatch-named "model_for promotion" does not touch this file. Both `git diff <baseline>` and `git diff HEAD` are empty (cumulative-in-HEAD); no public-contract symbol drifted in GLOSSARY (the walker has no `__all__` and no GLOSSARY entry — absence correct); no High/Medium; one pre-existing Low (M2M connector raw `_meta` access, deferred with trigger) and two cross-file DRY items (the `_target_pk_name` recompute twin with `field_meta.py`, and the wide relation-context argument bundle) forwarded to the folder pass. Set `Status: fix-implemented` per the no-source-edit (shape #5) cycle pattern: no High, no behavior-changing Medium, all Lows forward-looking/deferred, empty cycle diff.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, no changes (`289 files left unchanged`).
- `uv run ruff check --fix .` — pass (`All checks passed!`; only the pre-existing COM812-vs-formatter config notice).

### Notes for Worker 3
- Both `git diff b1beed32cb3e78e5ca6825d15a3a56042c3d5216 -- django_strawberry_framework/optimizer/walker.py` and `git diff HEAD -- django_strawberry_framework/optimizer/walker.py` are empty; commit `3b4f90c0` (the FK-id-elision→`FieldMeta` change, +11/-32) is cumulative-in-HEAD. Reviewed against current HEAD source (`33466db5`).
- Maintainer's FK-id-elision→`FieldMeta` change verified semantics-preserving by clause-by-clause comparison of the pre-`3b4f90c0` `_can_elide_fk_id` body against `FieldMeta._from_field_shape(...).fk_id_elision_eligible` (see `### Other positives`). The dispatch-named "model_for promotion" does not touch this file (`grep model_for` empty).
- No High / no behavior-changing Medium. Two DRY items deferred-with-trigger, forwarded to `rev-optimizer.md` (folder pass): the `_target_pk_name` recompute twin shared with `field_meta.py` (the sibling `_can_elide_fk_id` predicate twin is now RESOLVED by `3b4f90c0`), and the wide relation-context argument bundle. One Low (M2M connector raw `_meta` at walker.py:928) deferred-with-trigger; pre-existing, not a `3b4f90c0` change.
- No GLOSSARY-only fix in scope. GLOSSARY has no entry for any walker symbol (no `__all__`; `plan_optimizations`/`plan_relation` are internal optimizer symbols — absence correct). No public-symbol drift.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits. The docstrings accurately describe behavior, including the updated `_can_elide_fk_id` docstring (which now documents the `FieldMeta._from_field_shape` delegation and the shared single-predicate rationale, walker.py:856-866) and the `_resolve_field_map` DUAL CONTRACT note that the elision fallback depends on. The spec-035 writer docstrings each name Decision 4 and state which projection they gate. Both `TODO(spec-035 Slice 3)` anchors (walker.py:323, walker.py:840) are valid per AGENTS.md #26; the cross-referenced `docs/spec-035-optimizer_hardening-0_0_10.md` and `docs/feedback.md` both exist on disk.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source edit this cycle (zero tracked-file changes). Per AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_11.md`) which carries no changelog directive for review cycles. Commit `3b4f90c0` itself ships under its own maintainer prompt, out of scope for this review.

---

## Verification (Worker 3)

### Logic verification outcome

Shape-#5 no-source-edit cycle verifying maintainer commit `3b4f90c0` (cumulative-in-HEAD). Empty diff is necessary but not sufficient for a maintainer-committed change, so the FK-id-elision→`FieldMeta` logic was independently confirmed correct, not merely untouched.

- **Zero-edit proof.** `git diff b1beed32cb3e78e5ca6825d15a3a56042c3d5216 -- django_strawberry_framework/optimizer/walker.py` empty AND `git diff HEAD -- …walker.py` empty AND owned-paths `git diff --stat b1beed32… -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty. HEAD `33466db5`. No sibling-cycle attribution needed (clean stat).
- **`model_for` absent.** `grep -n model_for django_strawberry_framework/optimizer/walker.py` exit 1 (zero hits). The walker's visibility seam is `apply_type_visibility_sync`, not `model_for`. The dispatch-named promotion does not touch this file — confirmed.
- **FK-id-elision→`FieldMeta` semantics-equivalent (verified clause-by-clause against live source).** Stamped fast-path unchanged (walker.py `_can_elide_fk_id` #"stamped = getattr(field, \"fk_id_elision_eligible\", None)" → returned directly). Fallback is a single delegation `FieldMeta._from_field_shape(field, is_relation=True).fk_id_elision_eligible` — the SAME delegation `types/resolvers.py::_field_meta_for_resolver` uses (`grep _from_field_shape` → resolvers.py:292, field_meta.py:165/168, walker.py:870). The 8-conjunct predicate at `field_meta.py::FieldMeta._from_field_shape` #"fk_id_elision_eligible=(" (lines 216-225) matches the artifact's pre-commit clause list exactly: `attname is not None`, `related_model is not None`, `target_pk_name is not None`, `target_field_name == target_pk_name`, `not is_m2m`, `not is_o2m`, `not auto_created`, `not has_composite_pk(related_model)`. Composite-PK exclusion is an inline conjunct evaluated only after `related_model is not None` short-circuits → **no None-deref** (`has_composite_pk` unreachable when `related_model is None`). `target_pk_name` derivation equivalent (`field_meta.py::_target_pk_name(model)` reads `_meta.pk.name` defensively).
- **Positive + negative test-pinned THROUGH the raw-field fallback.** The elision tests use unregistered models (inline `models.Model` subclasses / `SimpleNamespace`), so `_resolve_field_map` yields raw Django fields and `_can_elide_fk_id` hits the FALLBACK, not the stamped path:
  - Positive: `tests/optimizer/test_walker.py::test_plan_elides_forward_fk_when_target_pk_is_not_named_id` (non-`id` PK still elides → `("target@target",)`).
  - Negative: `test_plan_does_not_elide_fk_to_non_pk_to_field` (`to_field="code"` → `target_field_name != target_pk_name` conjunct → `fk_id_elisions == ()`).
  - Commit-cited fallback short-circuit: `test_plan_select_relation_with_missing_related_model_is_not_elided` (`SimpleNamespace(related_model=None, attname="relation_id")` → `related_model is None` conjunct → `fk_id_elisions == ()`, no deref).
  - Ran `uv run pytest tests/optimizer/test_walker.py -k "elid or missing_related_model or non_pk_to_field"` → **11 passed** (subset coverage-fail is expected, not a test failure).
- **G2 `enable_only` gate.** Derived once via `walker.py::_enable_only_for_operation` #"return operation is None or operation is OperationType.QUERY" (QUERY-only) and threaded through all four projection writers; the `fk_id_elisions` append in `_plan_select_relation` is correctly INDEPENDENT of `enable_only` (Decision 5 walker half) — confirmed at the elision branch (`append_unique_many(plan.fk_id_elisions, …)` gated only by `_can_elide_fk_id` / custom-get_queryset / custom-id-resolver / id-only-selection, not the gate).
- **get_queryset→Prefetch downgrade** present in `plan_relation` #"return (\"prefetch\", \"custom_get_queryset\")" — confirmed.
- **Low (M2M connector raw `_meta`, walker.py `_connector_only_field` #"return parent_field.related_model._meta.pk.attname") genuinely deferred-with-trigger.** Verbatim trigger "a stamped `m2m_connector_attname` (or equivalent) slot is added to `FieldMeta`". Pre-existing, reached only when `many_to_many` is True (the `not parent_field.many_to_many` branch returns first). No GLOSSARY-only fix.

### DRY findings disposition

Two cross-file items correctly forwarded to `docs/review/rev-optimizer.md` (folder pass): (1) the `_target_pk_name` recompute twin with `field_meta.py` (input-contract divergence: walker takes field/FieldMeta and dereferences `.related_model`; field_meta takes a model) — defer-with-trigger "walker's raw-descriptor recompute fallback is removed"; (2) the wide relation-context argument bundle threaded through four projection writers — defer-with-trigger "the planner gains a further per-relation context member beyond `enable_only`". The sibling `_can_elide_fk_id` predicate twin is now RESOLVED by `3b4f90c0` (single-sourced through `_from_field_shape`). Both defers have a real divergence and a falsifiable trigger; acting now is net-neutral. Accepted as forwarded.

### Temp test verification

None — no temp tests created. Verification used the existing permanent suite (`tests/optimizer/test_walker.py`) which pins the fallback positive+negative decisively.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `optimizer/walker.py` checklist box in `docs/review/review-0_0_11.md`. Genuine shape #5: zero tracked edits, maintainer's `3b4f90c0` FK-id-elision→`FieldMeta` change independently confirmed semantics-preserving (clause-by-clause + positive/negative fallback tests), no High/Medium, one pre-existing Low deferred-with-trigger, two DRY items forwarded, GLOSSARY accurate (no walker-symbol entry — absence correct), changelog Not-warranted with both citations.
