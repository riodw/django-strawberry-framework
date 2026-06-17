# Review: `django_strawberry_framework/optimizer/walker.py`

Status: verified

## DRY analysis

- **FK-id-elision recompute twins (`_can_elide_fk_id` / `_target_pk_name`) duplicate the build-time logic in `field_meta.py`.** `walker.py::_can_elide_fk_id` (walker.py:854-889) and `walker.py::_target_pk_name` (walker.py:892-900) are `getattr(field, "<slot>", None)`-first shims whose *recompute fallback tails* (lines 865-889 and 897-900) re-derive `fk_id_elision_eligible` / `target_pk_name` from a raw descriptor, byte-equivalently to the producer logic in `field_meta.py::from_django_field` (the build-time stamper). This is the build-time-vs-walk-time FK-id-elision item `field_meta.py` already forwarded to the optimizer-folder pass; walker.py is the walk-time consumer side. Consolidation spans two files (a shared free function the stamper and the walker recompute tail both call), so it cannot land in a single-file cycle. **Defer with trigger:** "walker's raw-descriptor recompute fallback is removed" — i.e. once a registry-coverage gate guarantees every field reaching the walker is `FieldMeta`-stamped, the recompute tails delete and the dual path collapses. Forward to `docs/review/rev-optimizer.md` (folder pass) for the cross-file disposition.

- **The four G2 projection-writer call sites each re-pass `enable_only=enable_only` through six-plus shared arguments alongside the relation tuple.** `_plan_select_relation` / `_plan_prefetch_relation` / `_record_relation_access` / `_apply_hint`'s two re-dispatches all thread the same `(sel, django_field, target_type, plan, prefix, [full_path,] info, runtime_paths, resolver_identities, enable_only)` bundle (walker.py:449-472, 715-721, 738-762, 765-775). This is the same wide-argument-list candidate the prior cycles flagged on `_plan_select_relation` / `_plan_prefetch_relation`; spec-035 added one more positional-context member (`enable_only`) to every site. **Defer with trigger:** "the planner gains a further per-relation context member beyond `enable_only`" — at that point fold `(plan, prefix, info, runtime_paths, resolver_identities, enable_only)` into a frozen `RelationWalkContext` dataclass threaded once. Acting now is net-neutral (the bundle is still readable at four sites); the dataclass earns its keep on the next added member. Forward to `docs/review/rev-optimizer.md` since the same shape recurs across walker helpers.

## High:

None.

## Medium:

None.

## Low:

### `_connector_only_field` M2M branch reads `related_model._meta.pk.attname` raw (walker.py:947)

The M2M branch returns `parent_field.related_model._meta.pk.attname` with no `getattr` guard, unlike the reverse-FK / forward-single-valued branches above it (walker.py:935-946) which are fully `getattr`-defensive with a stamped-slot fallback. The asymmetry is **safe today**: the branch is reached only when `parent_field.many_to_many` is True (line 941 negates), which on any real Django M2M field guarantees a non-`None` `related_model` carrying `_meta.pk`. A partial test double that sets `many_to_many=True` without a real `related_model._meta` would `AttributeError` rather than returning `None` — but that matches the package's "fail loud on malformed double" posture for the connector column, and no stamped-slot equivalent exists for the M2M pk attname. Pre-existing (not a spec-035 change). **Defer with trigger:** "a stamped `m2m_connector_attname` (or equivalent) slot is added to `FieldMeta`" — at that point mirror the two branches above with a `getattr(..., None) or getattr(parent_field, "<slot>", None)` shape so all three connector branches share one defensive idiom. No source edit warranted now.

## What looks solid

### DRY recap

- **Existing patterns reused.** The walker routes every shared selection-traversal primitive through the `optimizer/selections.py` underscore aliases bound at module top (walker.py:54-61), the 0.0.9 DRY consolidation (`docs/feedback.md` Major 2) — the walker and the `extension.py` AST seam share ONE fragment / directive / response-key / `edges { node }`-unwrap implementation. Plan-time prefetch visibility reuses the shared `utils/querysets.py::apply_type_visibility_sync` (walker.py:243) so plan-time and resolve-time visibility cannot drift. The window bounds reuse `utils/connections.py::derive_connection_window_bounds` via the thin `_connection_window_slice` adapter (walker.py:1303) so plan-time and resolve-time windows share one rule. The `_dst_<field>_connection` `to_attr` literal is single-sourced in `_relation_connection_to_attr` (walker.py:1180-1189). `_resolver_identities_for` (walker.py:247-283) is correctly shared by the list-relation walk and the connection planner with the field-name-vs-accessor vocabulary split documented.
- **New helpers considered.** Considered hoisting the spec-035 G2 gate into a plan-level flag on `OptimizationPlan` rather than a threaded `enable_only` parameter; rejected because the spec's Decision 4 explicitly pins build-time threading through all four projection writers (one writer, `_project_scalar_only_window`, applies `.only(...)` without ever touching `plan.only_fields`, so a plan-attribute or post-hoc-clear sweep cannot reach it). The parameter threading is the correct shape, not a DRY smell. Considered folding `_can_elide_fk_id`'s recompute tail into a shared helper now; rejected for this single-file cycle (cross-file with `field_meta.py`, deferred above).
- **Duplication risk in the current file.** The repeated `enable_only=enable_only` forwarding across the dispatch tree (walker.py:449-472, 745-762) is intentional single-decision propagation, not duplication — the gate is derived ONCE in `plan_optimizations` (walker.py:108) and threaded so root, child, and window plans share one operation decision. The shadow's "2x `operation` / 2x `target_field` / 2x `_optimizer_runtime_prefixes`" repeated literals are reflective-access attribute names at structurally distinct sites (e.g. `target_field` is the descriptor probe in `_can_elide_fk_id` vs the connector probe in `_connector_only_field`), not a string-keyed-dispatch DRY signal.

### Other positives

- **The spec-035 G2 gate is implemented exactly to Decision 4's four-writer contract.** All four `only_fields` / `.only(...)` writers consult the gate: `_walk_selections` (Relay custom-pk append walker.py:397, scalar-leaf append walker.py:416), `_record_relation_access` (FK connector append walker.py:611 — the writer that makes `only_fields` non-empty *independently* of scalar leaves, which the spec calls out as the leak the naive "block scalar appends" mechanism misses), `_ensure_connector_only_fields` (early return walker.py:1041, correctly BEFORE the empty-`only_fields` guard), and `_project_scalar_only_window` (early return walker.py:1012 — the direct `.only(...)` that never lands in `only_fields`). Nothing relies on the empty-set no-op. The gate is derived once and threaded; `select_related` / `prefetch_related` / `fk_id_elisions` are untouched under non-`QUERY`, matching the spec's "column-deferral hazard only" rationale.
- **FK-id elision stays correctly enabled under non-`QUERY` (Decision 5, walker half).** The elision branch in `_plan_select_relation` (walker.py:508-514) is independent of `enable_only`, so a mutation `{ relation { id } }` still records `fk_id_elisions` while the connector append is suppressed (full-row load guarantees the FK column is present). The consumer-`.only()`-defers-the-FK hazard is correctly handled at resolve time in `types/resolvers.py::_build_fk_id_stub` (the loaded-check + `_FK_ELISION_UNSAFE` loud fallback, verified present out-of-scope) — the walker side is correct to keep the elision recorded. Pinned by `test_mutation_id_only_relation_still_records_elision`.
- **Cacheable-flag writes are correct (plans.py forward verified).** `plan.cacheable = False` is written at three sites: custom-`get_queryset` prefetch downgrade (walker.py:567-568, set BEFORE the bare-lookup `related_model is None` early return so the downgrade reason persists), consumer-supplied Prefetch hint (walker.py:727, with the documented request/user-scoped-closure rationale), and child-plan propagation (walker.py:646-647, 1435-1436). Verified the contract closes: `extension.py::_plan_for` inserts into `_plan_cache` only `if plan.cacheable` (extension.py:922), so a non-cacheable plan is never cached — no cross-request data leak. The `_plan_connection_relation` DISTINCT-guard early return (walker.py:1430-1431) does NOT flip parent cacheable, which is **correct**: the custom-`get_queryset` queryset was built only into the throwaway `sub_plan`/`child_queryset` and discarded on fallback, so no request-scoped queryset is baked into the parent plan; per-parent resolution re-runs `get_queryset` fresh each request. The throwaway `sub_plan` isolation (walker.py:1414, merged to parent only on the success path at walker.py:1434) is the mechanism that makes every connection-fallback early return leak-free for resolver keys, fk-id elisions, AND cacheable.
- **Downgrade-to-Prefetch-on-custom-`get_queryset` is the upstream-cribbed rule and applied consistently.** `plan_relation` (walker.py:135-144) downgrades to prefetch whenever `_target_has_custom_get_queryset`, and `_apply_hint`'s `force_select` path (walker.py:738-749) honors the same downgrade even against an explicit consumer `select_related()` hint — the correct precedence (Django cannot `select_related` across a custom-`get_queryset` boundary without losing the visibility hook).
- **Connection-fallback shapes are correctly partitioned between "fully unplanned" and "record-resolver-keys".** `_plan_connection_relation` leaves the field FULLY unplanned (no `planned_resolver_keys`) for sidecar / divergent-alias / hint-SKIP / DISTINCT / unwindowable-partition shapes so Slice-4 strictness sees the real per-parent access (walker.py:1345-1351, 1380, 1402, 1431), but RECORDS resolver keys for the malformed-pagination `window is None` path (walker.py:1391) so strictness does not preempt the field's own cursor-validation error — the error-locality distinction (spec-033 Decision 5/8) is precisely implemented and documented.
- **Reflective-access audit (85 calls-of-interest) clean.** Every `getattr` carries a default or is guarded by an upstream branch (e.g. the `type_cls.__name__` reads in `_apply_hint`/`force_select` are reachable only when `_resolve_optimizer_hints` returned non-empty, which requires `type_cls is not None` — documented at walker.py:689-695). The raw `_meta` accesses (walker.py:189, 383, 900, 947, 975, 1016, 1484) are each gated by an upstream presence check or a real-Django-field branch condition; the composite-PK `pragma: no cover` (walker.py:876) is justified (fail-closed guard, no test fixture defines composite PKs).
- **Both spec-035 TODO anchors are validly scoped.** `TODO(spec-035 Slice 3)` at walker.py:322 and walker.py:839 name the G3 fragment-classifier deferral; the spec confirms G3 ships no runtime code and is carried forward to the abstract-return optimizer entry card (no reachable production trigger today, since `registry.model_for_type` returns `None` for abstract origins and `_optimize` passes the queryset through before the walker runs). Per AGENTS.md #26, no `NotImplementedError` pairing is warranted — the default inline-all path is complete and correct for every reachable shape; the classifier is purely additive future hardening that must NOT fail loudly. The anchors correctly name the active doc + slice.
- **G2 test discipline is exhaustive.** `tests/optimizer/test_walker.py` pins all three `_enable_only_for_operation` arms plus the defensive `None`/partial-double arms (`test_enable_only_defaults_enabled_without_info`, walker.py:3460), mutation drops `only` but keeps `select`/`prefetch` (3341), to-one no-`only` (3362), to-many prefetch no deferred loading (3379), scalar-only window no-`only` (3396), subscription gated (3445), and elision-still-recorded-under-mutation (3497). `test_extension.py` adds the cache-coexistence pin (`test_query_and_mutation_plans_coexist_distinct_keys`, 1180) and the real-execution end-to-end (`test_mutation_real_execution_suppresses_only_keeps_select_related`, 1213).

### Summary

`walker.py` is the optimizer's core selection-tree walker and was hardened by spec-035's G2 gate (+172 lines threading an operation-wide `enable_only` projection flag through every `only_fields` / `.only(...)` writer). The change is implemented exactly to Decision 4's four-writer contract — including the two writers (`_record_relation_access`'s independent FK-connector append and `_project_scalar_only_window`'s direct `.only(...)`) that the spec explicitly identifies as the leaks a naive scalar-only gate would miss — and the FK-id-elision-stays-enabled Decision 5 walker half is correct (the safety guard correctly lives at resolve time in `types/resolvers.py`). The `cacheable` flag forward verified clean: every downgrade write is correct, the DISTINCT-fallback non-flip is correct (throwaway sub-plan isolation means nothing request-scoped reaches the parent), and `extension.py` only caches `if plan.cacheable`, so no cross-request leak. G2 test coverage is exhaustive across all gate arms. No High or Medium findings; one pre-existing Low (M2M connector raw `_meta` access, deferred with trigger) and two cross-file DRY items (the FK-id-elision recompute twin with `field_meta.py`, and the wide relation-context argument bundle) forwarded to the folder pass. Set `Status: fix-implemented` per the no-source-edit cycle pattern (shape #5): no High, no behavior-changing Medium, both Lows forward-looking/deferred, empty cycle diff.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 270 files unchanged.
- `uv run ruff check --fix .` — all checks passed (only the pre-existing COM812-vs-formatter config notice).

### Notes for Worker 3
- This-cycle diff (`git diff HEAD -- django_strawberry_framework/optimizer/walker.py`) is empty; spec-035's G2 change (commit `8866fcea`, +172 lines) was already merged before this cycle. Reviewed against current HEAD source.
- No High / no behavior-changing Medium. Two DRY items deferred-with-trigger and forwarded to `rev-optimizer.md` (folder pass): the FK-id-elision recompute twin shared with `field_meta.py`, and the wide relation-context argument bundle. One Low (M2M connector raw `_meta` at walker.py:947) deferred-with-trigger; pre-existing, not spec-035.
- No GLOSSARY-only fix in scope. GLOSSARY grep for walker symbols: only line 924 (`OptimizerHint` walker dispatch prose) is accurate; no walker public-symbol drift.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

The spec-035 docstrings on every gated writer accurately describe the G2 contract (each names Decision 4 and states which projection it gates and why the gate is needed there). The TODO anchors are valid per AGENTS.md #26. No stale comments, no docstrings promising unimplemented behavior. No comment/docstring edits warranted.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source edit this cycle (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_10.md` is silent on changelog edits for review cycles). The spec-035 G2 feature itself ships its CHANGELOG entry under its own Slice 4 maintainer prompt, out of scope for this review.

---

## Verification (Worker 3)

### Logic verification outcome

No-source-edit cycle (shape #5). `git diff HEAD -- django_strawberry_framework/optimizer/walker.py` empty; `git diff HEAD -- CHANGELOG.md` empty. HEAD `58ca2def`; change context for walker.py since `14910230` is spec-035 (`8866fcea`, +161/-11) plus the TODO-anchor commit (`4241d37d`), both pre-cycle and already merged. Reviewed against current HEAD source.

Independently re-derived every high-risk invariant from source (did not trust the artifact):

1. **G2 `enable_only` four-writer gate — all four writers gated, confirmed by direct read.** Enumerated every `only_fields`/`.only(` write site (`grep`): exactly four families, each consults the gate.
   - Writer 1 — scalar-leaf append (`_walk_selections`): Relay custom-pk append gated at `walker.py:397` (`if db_field is not None and enable_only`), scalar-leaf append gated at `walker.py:416` (`if enable_only`). Both `continue` unconditionally so the field stays accounted-for.
   - Writer 2 — FK-connector append (`_record_relation_access`, `walker.py:611`): `if enable_only and attname is not None`. The subtle one — it makes `only_fields` non-empty independently of scalar leaves. Gated. Line 613 `planned_resolver_keys` append is correctly UNCONDITIONAL (strictness sees the relation regardless of operation).
   - Writer 3 — prefetch-connector (`_ensure_connector_only_fields`, `walker.py:1041`): `if not enable_only: return` placed BEFORE the empty-`only_fields` guard at `:1043` — correct, because the empty-set no-op is insufficient (writers 2 and 4 populate independently of the scalar path).
   - Writer 4 — direct `.only(...)` scalar-only window (`_project_scalar_only_window`, `walker.py:1012`): `if not enable_only: return child_queryset` BEFORE the `.only(*fields)` at `:1022`. The second subtle one — never touches `plan.only_fields`. Gated.
   The gate is derived ONCE (`_enable_only_for_operation`, `walker.py:64`; called at `:108`) and threaded through every recursion (`_walk_selections`, `_plan_select_relation`/`_plan_prefetch_relation`, `_build_prefetch_child_queryset`, both `_apply_hint` re-dispatches at `:748`/`:761`/`:774`, `_plan_connection_relation` at `:1425`/`:1453`). Gate-OFF path preserves correct behavior: full columns (no premature `.only()`), JOIN/Prefetch intact. Re-derived via a gitignored temp test (below).

2. **`cacheable` flag — no cross-request leak.** All five write sites read: custom-`get_queryset` prefetch downgrade (`walker.py:568`, on the active plan), child-plan propagation (`:646-647`), consumer-Prefetch hint (`:727`, set AFTER `rebased_prefetch` validation at `:709` so a `ConfigurationError` leaves no phantom flip), connection sub-plan isolation (`:1416` on `sub_plan`, merged to parent only on the success path at `:1435-1436`). DISTINCT-fallback non-flip (`:1430-1431`) confirmed correct: the `return` precedes the `:1434-1436` merge, and the request-scoped queryset was built only into the throwaway `sub_plan`/`child_queryset`, discarded on fallback — nothing request-scoped reaches the parent. Contract closes cross-file: `extension.py:922-923` is the SOLE `_plan_cache` insertion site, gated `if plan.cacheable`; the only serve path (`:899-912`) reads from that cache, which therefore never holds a non-cacheable plan.

3. **Downgrade-to-Prefetch on custom `get_queryset`.** `plan_relation` (`walker.py:135-141`) returns `("prefetch", "custom_get_queryset")` whenever `_target_has_custom_get_queryset` (null-guarded, `:147-148`); `_apply_hint`'s `force_select` honors the same downgrade (`:738-749`) even against an explicit consumer `select_related()`. Correct precedence (Django cannot `select_related` across a custom-`get_queryset` visibility boundary).

4. **FK-id elision at walk time stays recorded independent of the gate (Decision 5).** Elision branch in `_plan_select_relation` (`walker.py:508-515`) is independent of `enable_only` — `append_unique_many(plan.fk_id_elisions, ...)` fires under MUTATION/SUBSCRIPTION while the connector append is suppressed. Resolve-time guard genuinely in `types/resolvers.py`: `_FK_ELISION_UNSAFE` sentinel (`:72`), `_build_fk_id_stub` returns it when the FK attname is deferred (`:97-112`), resolver checks `if stub is not _FK_ELISION_UNSAFE` before use (`:386-387`), spec-035 Decision 5 named at `:381`. Confirmed cross-file.

5. **Low + DRY forwards genuine.** M2M Low (`walker.py:947` raw `related_model._meta.pk.attname`, no getattr guard unlike the two branches above at `:935-946`): confirmed pre-existing — introduced by `7863d5d8` (connection optimizer refactor), NOT spec-035 (`8866fcea` touched only `_ensure_connector_only_fields`'s signature in this area, not line 947). Trigger ("a stamped `m2m_connector_attname` slot is added to `FieldMeta`") is falsifiable: `field_meta.py` has `target_field_attname`/`reverse_connector_attname` slots (feeding the two defensive branches) but NO m2m pk-attname slot — so the M2M branch genuinely has no stamped fallback to mirror today. No-action confirmed. Branch is reachable only when `many_to_many` is True (`:941` negates+returns first), where a real Django M2M guarantees `related_model._meta.pk`.

### DRY findings disposition

Both forwards confirmed genuinely cross-file (cannot land in this single-file cycle):
- **FK-id-elision recompute twins** (`_can_elide_fk_id`/`_target_pk_name` recompute tails at `walker.py:865-889`/`:897-900`) are byte-equivalent to the build-time producer in `field_meta.py::from_django_field`/`_build` (`:139`,`:186`,`:208-215`). Both walker helpers are `getattr(field, "<slot>", None)`-first shims (`:862`,`:894`). Note the input-contract divergence: `field_meta.py::_target_pk_name` (`:227`) takes a **model**, walker's (`:892`) takes a **field/FieldMeta** — consolidation needs a shared free function spanning both files. Matches the field_meta.py-side forward I verified last cycle. Forwarded to `rev-optimizer.md`.
- **Wide relation-context argument bundle** (`(plan, prefix, info, runtime_paths, resolver_identities, enable_only)` recurring across four call sites): `RelationWalkContext` dataclass does not yet exist (grep empty); the same shape recurs across `_plan_select_relation`/`_plan_prefetch_relation` (flagged by prior cycles), so a folder-pass `RelationWalkContext` is the right home. Act-now is net-neutral; deferral reasoning sound. Forwarded to `rev-optimizer.md`.

Both disposed by citation inside this artifact + the open `[ ]` folder-pass box at `review-0_0_10.md:100`.

### Temp test verification

- Temp test used: `docs/review/temp-tests/optimizer/test_w3_g2_gate_rederive.py` (gitignored). Independent re-derivation of the four-writer gate from real fakeshop models (`Item`/`Category`) + the real applied queryset's `deferred_loading`: writer-1 scalar leaf, writer-2 FK connector (gate-off → `(frozenset(), True)` + JOIN intact), writer-3 prefetch connector (Prefetch survives, child no mask), Decision-5 elision-recorded-under-MUTATION/SUBSCRIPTION, and the `_enable_only_for_operation` truth table. **5 passed.**
- Disposition: **deleted** after verification — behavior is fully covered by the permanent G2 suite (no new behavior bug or gap found; nothing to promote).
- Also ran the permanent named G2 suite (`tests/optimizer/test_walker.py` + `test_extension.py`, `-k "mutation or subscription or enable_only or scalar_only_window or elision or coexist or suppresses or query_identical"`, `--no-cov`): **18 passed.**

### Shape #5 checks

- Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` (`## Fix report` line 52, `## Comment/docstring pass` line 73, `## Changelog disposition` line 81). "Files touched: None" holds (`git diff HEAD -- walker.py` empty).
- Changelog **Not warranted**, both citations present (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" + active plan `review-0_0_10.md` silence). `git diff HEAD -- CHANGELOG.md` empty. Internal-only framing honest (spec-035's own CHANGELOG entry ships under its Slice 4, out of scope).
- No GLOSSARY-only fix. Both Lows forward-looking/deferred with verbatim triggers; no GLOSSARY-only Low.
- `uv run ruff format --check` → already formatted; `uv run ruff check` → all checks passed (only the pre-existing COM812-vs-formatter notice).
- Working-tree dirty paths (per `git status`) are sibling-cycle/docs work; none touch `walker.py`. Comment/docstring pass: spec-035 writer docstrings each name Decision 4 and state which projection they gate; both `TODO(spec-035 Slice 3)` anchors (`:322`,`:839`) valid per AGENTS.md #26 (G3 ships no runtime code, default inline-all path complete) — no edits warranted.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `optimizer/walker.py` checklist box at `review-0_0_10.md:99`.

---

## Iteration log

(none)
