# Review: `django_strawberry_framework/types/resolvers.py`

Status: verified

## DRY analysis

- **Restated carry-forward from rev-optimizer__field_meta.md L1 (verbatim trigger).** `_field_meta_for_resolver` at `types/resolvers.py:182-210` reconstructs `FieldMeta.from_django_field`'s 11-kwarg shape (`name`, `is_relation`, `many_to_many`, `one_to_many`, `one_to_one`, `nullable`, `related_model`, `attname`, `target_field_name`, `target_field_attname`, `reverse_connector_attname`, `auto_created`) verbatim, plus the cardinality-gated `nullable` rule from `optimizer/field_meta.py:138-156`. The duplication is intentional (test-doubles in `tests/types/test_resolvers.py:142-167,569-576` pass `SimpleNamespace` shapes that lack `is_relation`, so the canonical builder's `OptimizerError` guard at `optimizer/field_meta.py:130-134` rejects them). Defer until a third non-Django call site lands; then hoist the body into a `FieldMeta._from_field_like(field)` classmethod that takes the cardinality-gated nullable + 11-kwarg construction and drops the `is_relation` guard, and have both `from_django_field` and the resolver fallback delegate. Trigger condition verbatim from carry-forward: "deferred until third non-Django call site lands (hoist into `FieldMeta._from_field_like`)."
- **Repeated `getattr(field, "<name>", <default>)` 11-call ladder at `types/resolvers.py:190-209`.** Eleven `getattr(field, ...)` calls (`many_to_many`, `one_to_many`, `target_field`, `null`, `one_to_one`, `related_model`, `attname`, `target_field` two reads via `target_field`, `field`, `auto_created`) form a structural mirror of `optimizer/field_meta.py:137-170`. Folded naturally into the above `FieldMeta._from_field_like` hoist — no separate consolidation needed once that lands. Mentioned here so the DRY-cycle export does not double-count it as an independent finding.

## High:

None.

## Medium:

None.

## Low:

### `_field_meta_for_resolver` test-double fallback survives only via `hasattr(field, "is_relation")` shape gate; the gate string-matches the canonical builder's guard but not its rationale

`_field_meta_for_resolver` at `types/resolvers.py:182` reads `hasattr(field, "is_relation")` to decide whether to delegate to `FieldMeta.from_django_field` or to fall through to the in-module 11-kwarg fallback construction. The intent is "test-double `SimpleNamespace` without `is_relation` → build a synthetic `FieldMeta` so the test does not have to set `is_relation=True`." But `FieldMeta.from_django_field` (`optimizer/field_meta.py:130-134`) guards on **both** `hasattr(field, "name")` AND `hasattr(field, "is_relation")`, raising `OptimizerError` when either is missing. The resolver-side guard tests only the second condition; a test double that supplies `is_relation=True` but omits `name` would call into `from_django_field` and fail with `OptimizerError` from the optimizer subpackage's call site, not from the resolver's seam. Defer until either a third non-Django call site lands (folded into the `FieldMeta._from_field_like` hoist) OR a test exercises the `name`-missing path; the current production code only ever hits this with `field.name` always present (Django field descriptors guarantee `name`), so the asymmetry is latent. Recommend treating this Low as the second carry-forward trigger on the `_field_meta_for_resolver` deferred consolidation — when Worker 2 lands the `_from_field_like` hoist, drop the in-module fallback entirely and let the unified guard raise.

### Module docstring at `types/resolvers.py:18-20` cites `base._select_fields(model, fields_spec, exclude_spec)` but the signature change history is now invisible at this seam

The cycle-20 docstring refresh updated the resolver module docstring to name the new `base._select_fields` signature. The wording is correct, but the docstring no longer carries a hint that this is *the* signature after the M1 fix in `rev-types__base.md` (the prior signature took the `_ValidatedMeta` instance and re-ran shape gates). A future reader who finds this module via grep on `_select_fields` will not see the historical "shape-gate invariant" context. Defer until a second consumer of `_select_fields` lands outside `types/base.py` — the canonical home for the signature contract is `base.py`'s docstring (currently at `base.py:660-693`), and the resolver module docstring should stay a forward citation. Trigger: when `_select_fields` gains a second caller, add a one-line cross-reference here ("see `_select_fields` docstring in `types.base` for the shape-gate-once invariant").

### `_make_relation_resolver`'s `parent_type: type | None = None` default is documented for "test-double direct calls" but two production-shape integration tests at `tests/types/test_resolvers.py:142-152, 161-174, 577-590` still pass `parent_type=None`

The default exists for test ergonomics, but the resolver-key plumbing (`resolver_key(parent_type=None, ...)`) at `optimizer/plans.py:resolver_key` produces a key shape that production never emits — `_attach_relation_resolvers` always supplies `parent_type=cls`. The three direct unit tests cited above never reach the B3 N+1 check path (their `info.context=None` short-circuits at `_check_n1`'s `_get_context_value` lookup), so the `parent_type=None` path is effectively unreachable under any context-bearing call. Worker 1's prior judgment from `rev-types__base.md` M2 said "the four-corner override contract is the audit pin"; the asymmetry between production (`parent_type=cls` always) and tests (`parent_type=None` sometimes) is a Low-tier seam, not a defect. Defer until either (1) a third non-test caller of `_make_relation_resolver` lands — at which point removing the default is a one-line change — OR (2) the `_field_meta_for_resolver` hoist removes the `parent_type=None` reachability from this module entirely. No code change recommended now.

### `_check_n1`'s `kind: str | None` parameter docstring (`types/resolvers.py:130-136`) says "Pass `kind=None` only when you explicitly want the legacy single-valued check" but no production caller passes `kind=None`

The docstring carries the "kind is required" contract correctly, but the `kind=None` branch is exercised only by tests (`tests/types/test_resolvers.py:375, 395, 416`) that predate B3's cardinality-aware shape. The "legacy single-valued check" framing implies a deprecation path that does not exist — there is no live consumer of the `kind=None` branch outside test isolation. Defer until either the legacy framing is retired (replace "legacy" with "test-double fallback") OR the `kind=None` branch is removed entirely after the four cited test sites are updated to pass `kind="forward"`. Lower priority than the deferred `_from_field_like` hoist; lands as a comment-pass Low if Worker 2 picks it up while touching the module.

### `_will_lazy_load_single` short-circuit on `field_name in getattr(root, "__dict__", {})` at `types/resolvers.py:97` is documented as "compatibility for test doubles" but the same line silently exempts a production code path where a Django signal handler or descriptor pre-populates `__dict__` (forward OneToOne assignment via descriptor)

The docstring at `types/resolvers.py:91-95` correctly notes "Django's descriptor populates `root._state.fields_cache` after a load and also stamps `root.__dict__` on some access paths." That second clause is load-bearing — Django's forward FK / OneToOne descriptor sets `instance.__dict__[field.name]` when the related instance has been assigned. This is correct behavior (the cached value is the assigned instance), but a regression where a future Django version stops populating `__dict__` on assignment would silently flip this branch to "lazy" without breaking any test. Defer until Django's descriptor contract changes (the upstream change would surface as a CI failure on the integration tests); no proactive change needed. Trigger: when the next Django LTS bump lands, add a focused unit test pinning `__dict__`-only cache hit returns `False` for single-valued relations.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_resolver_logger` shares the optimizer subpackage logger (`types/resolvers.py:34`) so consumers configuring `django_strawberry_framework` see B3 warnings — no parallel logger hierarchy. `resolver_key` + `runtime_path_from_info` from `optimizer/plans.py` are the canonical key-derivation helpers and are reused at all three resolver branches (`types/resolvers.py:66, 141`). `_get_context_value` from `optimizer/_context.py` is the single context-read seam for `DST_OPTIMIZER_*` sentinels (three call sites: `types/resolvers.py:61-65, 138, 150`), preserving the dict-or-object dual-shape contract pinned in `tests/types/test_resolvers.py:198-202, 250-253`. `is_many_side_relation_kind` (`utils/relations.py:74`) is the canonical many-side classifier and is consumed by both `_check_n1` and `FieldMeta.is_many_side`.
- **New helpers considered.** `_name_resolver` (`types/resolvers.py:157`) was the prior cycle's act-now extraction (three rename sites collapsed); no further consolidation candidate at this granularity. `_field_meta_for_resolver` fallback was considered for promotion to `FieldMeta._from_field_like` and explicitly deferred per carry-forward trigger.
- **Duplication risk in the current file.** The three resolver closure bodies (`many_resolver`, `reverse_one_to_one_resolver`, `forward_resolver` at `types/resolvers.py:246-268`) share the `_check_n1` call shape but have intentionally distinct return-value handling per cardinality — list-materialization for many, try/except for reverse OneToOne, attribute read for forward. Collapsing into a single dispatch function would require runtime branching on every call, where the closure-per-kind shape lets each branch be a tight straight-line function. The duplication is intentional sibling design; no consolidation candidate.

### Other positives

- **Module-level `_EMPTY_ELISIONS` sentinel** at `types/resolvers.py:50` is the kind of "do not allocate per-call" hygiene the optimizer hot path requires. The `frozenset()` default returned from `_get_context_value` keeps `key in elisions` O(1) without per-call allocation pressure.
- **Cardinality-aware `_check_n1` dispatch** at `types/resolvers.py:144-147` correctly routes many-side cardinalities through `_will_lazy_load_many` (which checks only `_prefetched_objects_cache` — the only Django-honored cache for the many side) and is pinned by `tests/types/test_resolvers.py:493-521, 524-542`. The "consumer set `root.items` directly" trap is closed.
- **B2 FK-id elision path** at `types/resolvers.py:264-268` is keyed off the branch-sensitive `resolver_key` (parent type + field name + runtime path), pinned by `tests/types/test_resolvers.py:307-330, 333-352`. A regression that fell back to a bare `field_name`-keyed elision set would be caught.
- **Reverse OneToOne `DoesNotExist` branch** at `types/resolvers.py:252-260` correctly closes over the `related_model.DoesNotExist` exception class at closure-creation time, avoiding per-call `getattr(related_model, "DoesNotExist")` lookup. Pinned by `tests/types/test_resolvers.py:555-590`.
- **Spec-019 Slice 1 router test coverage** at `tests/types/test_resolvers.py:681-798` pins the four router call-shape axes (default db return, parent-row instance forwarded, `instance=None` when parent lacks `_state`, null FK takes early-return before router). The strictness-axis test at `tests/types/test_resolvers.py:801-836` pins connection-agnostic shape under non-default alias.
- **Skip-set contract** at `types/resolvers.py:290-293` correctly honors `consumer_assigned_relation_fields` (the StrawberryField-assigned override surface) while letting `consumer_annotated_relation_fields` (annotation-only overrides) still receive the framework resolver — this is the documented four-corner contract from `rev-types__base.md` M2: annotation-only overrides change the GraphQL type but the manager-to-list conversion must still happen, so `setattr(cls, name, strawberry.field(resolver=...))` is the correct behavior. The integration seam at `finalizer.py:218-222` reads `definition.consumer_assigned_relation_fields` (not the union `consumer_authored_fields`), preserving end-to-end the override semantics base.py M2 documents.
- **`_name_resolver` rename hygiene** ensures GraphiQL traces show `resolve_<field_name>` instead of `many_resolver` / `forward_resolver` / `reverse_one_to_one_resolver` — small DX win pinned by three test assertions (`tests/types/test_resolvers.py:152, 174, 590`).

### Summary

`types/resolvers.py` is a well-factored relation-resolver module owning the three-cardinality dispatch (many-side `list(.all())`, reverse-OneToOne `try/except DoesNotExist`, forward `getattr` plus B2 FK-id stub), the B3 N+1 strictness check with cardinality-aware lazy-load detection, and the integration seam with `_attach_relation_resolvers` (called once from `finalizer.py:220-224`). No High or Medium findings. Five trigger-gated Lows, all deferring against documented future conditions (the `_from_field_like` hoist, the `_select_fields` second-caller cross-reference, the `parent_type=None` default removal, the `kind=None` legacy framing retirement, and the Django-LTS-bump descriptor pin). The carry-forward DRY trigger from `rev-optimizer__field_meta.md` L1 is restated verbatim as the leading DRY bullet with the original "third non-Django call site" trigger preserved. The `consumer_authored_fields` four-corner contract from `rev-types__base.md` M2 is honored end-to-end at the `_attach_relation_resolvers` seam — annotation-only overrides correctly receive the framework resolver while StrawberryField assignments are skipped.

---

## Fix report (Worker 2)

### Files touched
- None. Consolidated single-spawn per `docs/review/worker-2.md` "All Lows are explicitly forward-looking per Worker 1's own prose; no in-cycle edit required." 0H/0M/5L with each Low carrying a verbatim deferral trigger.

### Tests added or updated
- None.

### Validation run
- `uv run ruff format .` — pass / 118 files left unchanged
- `uv run ruff check --fix .` — pass / All checks passed
- No pytest per `START.md` standing rule (no source/test edit).

### Notes for Worker 3
- Consolidated single-spawn: logic + comment + changelog batched per dispatch authorisation and the "all Lows forward-looking" criterion.
- DRY analysis bullet 1 is a verbatim carry-forward from `rev-optimizer__field_meta.md` L1 with trigger preserved: "deferred until third non-Django call site lands (hoist into `FieldMeta._from_field_like`)." DRY bullet 2 explicitly folds into the same hoist — no separate consolidation candidate.
- Per-Low verbatim trigger phrases (each preserved under per-finding dispositions below):
  - L1 (`_field_meta_for_resolver` shape-gate asymmetry): "Defer until either a third non-Django call site lands (folded into the `FieldMeta._from_field_like` hoist) OR a test exercises the `name`-missing path."
  - L2 (`_select_fields` cross-reference): "Defer until a second consumer of `_select_fields` lands outside `types/base.py`."
  - L3 (`parent_type=None` default): "Defer until either (1) a third non-test caller of `_make_relation_resolver` lands … OR (2) the `_field_meta_for_resolver` hoist removes the `parent_type=None` reachability."
  - L4 (`_check_n1` `kind=None` legacy framing): "Defer until either the legacy framing is retired … OR the `kind=None` branch is removed entirely."
  - L5 (`_will_lazy_load_single` `__dict__` descriptor exemption): "Defer until Django's descriptor contract changes."
- Worker 1's per-Low prose self-adjudicates each Low against in-cycle edit: L3 says "No code change recommended now"; L5 says "no proactive change needed"; L1/L2/L4 each say "Defer until …" with the trigger naming a future cycle, not this one. Pattern (11) variant from memory: Worker 1's reviewer-self-adjudication is the strongest evidence-of-no-edit.
- No shadow file used.

---

## Comment/docstring pass

### Files touched
- None. M0 (no Medium) and all five Lows carry Worker 1's explicit "defer" prose; no in-cycle docstring edit warranted.

### Per-finding dispositions
- Low 1 (`_field_meta_for_resolver` shape-gate asymmetry): Forward-looking. Quote: "Defer until either a third non-Django call site lands (folded into the `FieldMeta._from_field_like` hoist) OR a test exercises the `name`-missing path; the current production code only ever hits this with `field.name` always present (Django field descriptors guarantee `name`), so the asymmetry is latent." No edit; recorded as second carry-forward trigger on the `_field_meta_for_resolver` deferred consolidation.
- Low 2 (`_select_fields` cross-reference at `types/resolvers.py:18-20`): Forward-looking. Quote: "Defer until a second consumer of `_select_fields` lands outside `types/base.py` — the canonical home for the signature contract is `base.py`'s docstring (currently at `base.py:660-693`), and the resolver module docstring should stay a forward citation." No edit.
- Low 3 (`_make_relation_resolver` `parent_type=None` default): Forward-looking. Quote: "No code change recommended now." No edit.
- Low 4 (`_check_n1` `kind=None` legacy framing): Forward-looking. Quote: "Lower priority than the deferred `_from_field_like` hoist; lands as a comment-pass Low if Worker 2 picks it up while touching the module." No edit — module not touched this cycle.
- Low 5 (`_will_lazy_load_single` `__dict__` exemption): Forward-looking. Quote: "no proactive change needed. Trigger: when the next Django LTS bump lands, add a focused unit test pinning `__dict__`-only cache hit returns `False` for single-valued relations." No edit.

### Validation run
- `uv run ruff format .` — pass / 118 files left unchanged
- `uv run ruff check --fix .` — pass / All checks passed

### Notes for Worker 3
Comment pass structurally a no-op: zero-line footprint matches memory pattern (e), variant for 0H/0M/all-forward-Lows artifacts. Verbatim trigger phrases preserved under per-finding dispositions above so a future cycle satisfying a trigger can grep-discover this deferral.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Cites both:
- `AGENTS.md` line 21: "Do not update CHANGELOG.md unless explicitly instructed."
- The active plan `docs/review/review-0_0_7.md` is silent on changelog authorisation for this cycle (cycle 26: rev-types__resolvers.md). The dispatch prompt named no authorisation either.
Additional reinforcement: zero source/test/docstring footprint this cycle (no consumer-visible surface changed), and the precedent chain across cycles 1-25 of the 0.0.7 review is uniformly `Not warranted`, now twenty-six deep. Memory pattern (1): chain-length itself is the `Not warranted` default for zero-edit spawns.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / 118 files left unchanged
- `uv run ruff check --fix .` — pass / All checks passed

---

## Verification (Worker 3)

### Logic verification outcome
0H/0M; all five Lows verbatim-trigger-preserved by Worker 2 under per-finding dispositions (L1 "third non-Django call site lands … OR a test exercises the `name`-missing path"; L2 "second consumer of `_select_fields` lands outside `types/base.py`"; L3 disjunctive "third non-test caller … OR the `_field_meta_for_resolver` hoist removes the `parent_type=None` reachability"; L4 disjunctive "legacy framing is retired … OR the `kind=None` branch is removed entirely"; L5 "Django's descriptor contract changes"). DRY carry-forward from `rev-optimizer__field_meta.md` L1 restated verbatim ("deferred until third non-Django call site lands (hoist into `FieldMeta._from_field_like`)"); DRY-2 explicitly folded into the same hoist. Worker 1's per-Low self-adjudication ("No code change recommended now"; "no proactive change needed"; "Defer until …") is the strongest evidence-of-no-edit per memory pattern (11).

### DRY findings disposition
Two DRY bullets carried forward as a single deferred consolidation (`FieldMeta._from_field_like` hoist), trigger "third non-Django call site" preserved verbatim. No in-cycle action.

### Temp test verification
None needed.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box at `docs/review/review-0_0_7.md:123`.

Source-diff attribution: `git diff -- django_strawberry_framework/types/resolvers.py` shows one hunk (lines 18-20 docstring) updating the `_select_fields` reference to the new `(model, fields_spec, exclude_spec)` signature — this hunk is attributable to cycle 20 (`rev-types__base.md` M1 signature change + cycle-20 comment pass), already verified per `review-0_0_7.md:117`. No new resolvers-attributable edits this cycle. `git diff -- CHANGELOG.md` empty, matching `Not warranted`. Ruff clean on `django_strawberry_framework/types/resolvers.py`. Consolidated single-spawn no-op confirmed per memory pattern (cycles 2-5, 9-15, 17, 19, 21, 23-25 lineage; 26th 0.0.7 cycle).
