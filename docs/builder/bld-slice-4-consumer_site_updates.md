# Build: Slice 4 — Consumer-site updates (relation conversion + optimizer)

Spec reference: `docs/spec-014-meta_primary-0_0_6.md` (lines 136-168; slice summary at lines 675-679; Decisions 6/7/8/9 at lines 521-605)
Status: final-accepted

## Plan (Worker 1)

This is the largest slice in the build. Three high-severity fixes (H1, H2, H3) plus stale-test rewrites for two test files plus seven new tests. Steps are bucketed by fix so review can walk each contract independently. Line numbers are pin-at-write-time hints; Worker 2 must verify against the live source before editing because Slices 1-3 have already shifted some files.

### DRY analysis

**Existing patterns reused.**

- **Registry helper trio (`get` / `primary_for` / `types_for` / `models_with_multiple_types`)** — Slice 1 already centralized the multi-type lookup surface (`registry.py:137-206`). Slice 4's nested-relation paths (`types/converters.py:343`, `types/finalizer.py:117`, `optimizer/walker.py:205`) continue to call `registry.get(...)` — that returns the primary post-finalize, no code change. The audit at `optimizer/extension.py:626-665` continues to call `registry.iter_types()` (the Slice 1 once-per-registered-type iterator). Per Decision 8 L3 (`spec:563`), `definition.primary` is **store-only**; no Slice 4 code path may read it for routing.
- **`consumer_authored_fields` short-circuit (`types/base.py:617` for the relation branch, `:647` for the scalar branch)** — Already filters annotation overrides and assigned `strawberry.field` resolvers out of the synthesis loop. H1's always-defer change targets the eager-bind branch *below* that short-circuit; the short-circuit itself stays unchanged. This is exactly the contract revision 3 H1 (`spec:20-22`) pinned: "auto-synthesized" replaces "every".
- **`PendingRelation` + `PendingRelationAnnotation`** — `types/base.py:638-639` already records `PendingRelation` and sets the annotation to `PendingRelationAnnotation` for the unregistered-target case. H1 just removes the eager-bind alternate branch so every auto-synthesized relation lands on this path.
- **`_resolve_field_map(model)` (`optimizer/walker.py:74-95`)** — Already the single Django-private `_meta.get_fields()` access site for the walker. H2 extends its signature with `source_type: type | None = None`; both callers stay in this helper, no duplication.
- **`registry.get_definition` + `registry.model_for_type`** — Both already work for any registered type (primary or secondary). The wrapper `_resolve_model_from_return_type` at `extension.py:371-411` is the one helper that changes shape. The underlying registry methods are untouched.
- **Plan cache key constructor `_build_cache_key` (`extension.py:668-725`)** — Already the single insertion site for the four-element cache tuple. H2 adds the fifth `origin` slot here; no inlined tuple-builder duplication risk because every cache hit/miss flows through `_get_or_build_plan:585`.
- **Schema-audit warning sink (`extension.py:646-664`)** — H3 changes the collection structure from a plain `list[str]` to a deduped accumulator, but the loop body, the SKIP-hint guard (`:659`), the field-map walk (`:655-658`), and the registry-target check (`:661`) all stay intact. Only the accumulator step changes.

**New helpers justified.**

- **`OriginAndModel` named tuple OR `(origin, model)` plain tuple** in `optimizer/extension.py` (per Decision 9 + rev6 M2 at `spec:42`). Single responsibility: carry both halves of the resolver-return-type resolution so the caller `_optimize` can feed `origin` into `_get_or_build_plan` and `target_model` into the cache key + walker. **Shape decision (pinned during planning, NOT discretionary):** use `NamedTuple` because `extension.py` already imports `NamedTuple` from `typing` for `CacheInfo` (`:32`, `:274-279`). Reusing the existing import pattern keeps the helper-pair convention `CacheInfo` / `OriginAndModel` aligned and avoids reaching into `collections.namedtuple` or `dataclasses` for a one-shot. Field names `origin` and `model` match Decision 9's prose ("origin Strawberry type alongside the model"). The named tuple is module-private (`_OriginAndModel`) — no `__all__` change required.
- No new module is required. The shape lives next to `_resolve_model_from_return_type` (`extension.py:371`), the only caller.

**Duplication risk avoided.**

- **Reading `definition.primary` for routing.** Decision 8 L3 (`spec:563`) explicitly forbids any code path from reading `definition.primary` to make ambiguity-routing decisions. Worker 2 reviewing the diff must reject any "while I'm here" code that introduces such a read. The plumb stays write-only (already done in Slice 2) and the routing surface stays at `registry.get` / `registry.primary_for` / `registry.types_for`.
- **Threading `source_type` into `_selected_scalar_names`.** Rev6 M1 (`spec:41`) audit pinned: `_selected_scalar_names` (`walker.py:481-504`) is nested-only — called from `_plan_select_relation:275` with `django_field.related_model` (never the resolver's root return type). Threading `source_type` here would invite call-site confusion and break the "nested → primary" contract for FK-id elision. The TODO comment at `walker.py:488-495` already pins the decision; the plan honors it.
- **Nested plan caching.** Rev6 L1 (`spec:43`, `spec:601`) audit pinned: `DjangoOptimizerExtension._plan_cache` is root-only — only insertion site is `_get_or_build_plan:585`. Worker 2 must NOT introduce a nested extension-cache path or thread `None` origins through walker recursion. The walker's nested `_walk_selections` calls (`walker.py:281, 348`) and `_build_prefetch_child_queryset` (`walker.py:336`) stay uncached at the extension level; the walker leaves `source_type=None` for nested calls and routes through `registry.get(model)` (the primary).
- **Repeated `(model, type_cls)` iteration patterns.** Worker 2 must not introduce a separate "primary-only" iterator on the registry — Decision 4's "Note on `iter_types()`" (`spec:477`) explicitly forbids it because skipping secondaries would silently miss relation fields. Dedupe at the warning-collection layer per H3.
- **Repeated cache-key tuple literal.** The five-element tuple is constructed exactly once at `_build_cache_key`'s `return` statement. The cache type annotation on `self._plan_cache` (`extension.py:452-455`) is extended to the new five-slot shape in the same edit so the declared key type stays in sync with the constructor.
- **Repeated regression-test setup boilerplate.** Multi-type Slice 4 tests all share the same shape: `ItemType(Meta.primary=True)` + `AdminItemType` on `Item`, plus a fixture isolating the registry. Each test redeclares the type pair inline (existing tests/types/test_base.py and tests/optimizer/test_*.py conventions). Do NOT introduce a shared module-level helper for "build a multi-type Item pair" — the test-by-test inline declarations are how every existing relation/optimizer test in the package is written (e.g., `tests/types/test_definition_order.py:177-218`), and a shared factory would obscure which `Meta.fields` selection a given regression cares about. Mirror the existing autouse `_isolate_registry` fixture in each touched file (already present in `tests/optimizer/test_walker.py:51-56` and `tests/optimizer/test_extension.py:51-56`; `tests/types/test_converters.py` has its own pattern — confirm before editing).

### Implementation steps

The slice breaks into five buckets: **H1** (auto-synthesized always-defer in `types/base.py`), **H2** (optimizer root-planning origin threading in `optimizer/walker.py` + `extension.py`), **H3** (schema-audit dedupe in `extension.py`), **stale-test rewrites** (two test files), and **new tests** (three test files). Each bucket is contract-isolated; Worker 2 should land them in this order so Worker 3's review can walk each fix independently.

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — Slices 1-3 have shifted file shapes (e.g., `tests/types/test_base.py` grew from ~640 to 771 lines; `tests/optimizer/test_extension.py` shifted moderately). Spec line numbers cited inline (`spec:NNN`) are stable.

#### Bucket H1 — Always-defer auto-synthesized relation binding (`types/base.py`)

Spec: `spec:137`, `spec:521-525` (Decision 6 row 1), `spec:736-738` (Edge cases entry).

1. **`types/base.py:615-645` `_build_annotations` relation branch.** Replace the eager-bind-or-defer dispatch with always-defer for auto-synthesized fields.
   - The `if field.name in consumer_authored_fields: continue` short-circuit at **`types/base.py:617`** STAYS unchanged. (Spec H1 contract: consumer-authored fields are unaffected — `spec:137`, `spec:524-525`.)
   - The `if getattr(field, "related_model", None) is None: raise ...` GenericFK guard at **`types/base.py:620-626`** STAYS unchanged.
   - Remove the maintainer's TODO anchor at **`types/base.py:627-635`** and its pseudo-code lines as part of this edit.
   - **Replace the if/else at lines 636-645** (the `target_type = registry.get(field.related_model); if target_type is None: pending.append(...); else: annotations[...] = resolved_relation_annotation(...)` block) with the unconditional pending-record path:
     - `pending.append(_record_pending_relation(cls, source_model, field, field_meta))`
     - `annotations[field.name] = PendingRelationAnnotation`
   - The `resolved_relation_annotation` import at **`types/base.py:40`** may become unused once the eager branch is gone. Worker 2 verifies via `ruff check --fix` and removes the import if F401 fires. Do NOT remove `PendingRelationAnnotation` or `PendingRelation` imports — they remain load-bearing.
   - The scalar branch at **`types/base.py:646-661`** STAYS unchanged (the spec's `:631` short-circuit reference is the per-iteration scalar guard at `types/base.py:647`, also untouched).
2. **Spot-check** `types/finalizer.py:117` (`target_type = registry.get(pending.related_model)`) — no change. Slice 3's audit ran first, so `registry.get(...)` now returns the primary (or the single registered type), and the existing `if target_type is None: raise "unresolved target"` (`finalizer.py:118-127`) covers the truly-unregistered case. Spec line 138 says "no code change required" — verify by reading the surrounding lines without editing.
3. **Spot-check** `types/converters.py:312-350` (`convert_relation`) — no change. `convert_relation` is a standalone helper called by the direct-converter test (`tests/types/test_base.py:720`); its `registry.get(target_model)` call already routes through Slice 1's multi-type semantics. Spec line 139 says "no change". Verify and move on.

**Net post-Slice-4 H1 behavior** (per `spec:736-738`):
- Single-type usage: identical post-finalize result. The only observable difference is that `cls.__annotations__[field.name]` is `PendingRelationAnnotation` between `__init_subclass__` and `finalize_django_types()` instead of resolved-immediately when the target happened to be declared first. Acceptable: finalization is the documented synchronization point.
- Multi-type usage: secondary-before-source-before-primary import order now resolves correctly (the import-order trap is closed).
- Consumer-authored fields: unchanged — `consumer_authored_fields` short-circuit still fires before any pending-record logic runs.

#### Bucket H2 — Optimizer origin-type propagation (`optimizer/walker.py`, `optimizer/extension.py`)

Spec: `spec:140-144`, `spec:148-152`, `spec:528-531` (Decision 6 rows 4-7), `spec:565-605` (Decision 9 in full), `spec:723-725` (Risks / `__build_cache_key` plumbing).

**H2a — Walker signature change.**

1. **`optimizer/walker.py:74-95` `_resolve_field_map(model)`.** Add a keyword-only `source_type: type | None = None` parameter.
   - New behavior: `type_cls = source_type if source_type is not None else registry.get(model)`. The rest of the function body is unchanged.
   - Remove the TODO anchor at lines 83-89 as part of this edit.
   - Verify the type-cls-dependent `_resolve_optimizer_hints` lookup (called from `_walk_selections:208`) reads the *new* `type_cls` correctly — it should, because `_walk_selections` receives the return value from `_resolve_field_map` and threads `type_cls` directly into the hints lookup.
2. **`optimizer/walker.py:126-252` `_walk_selections` signature change.** Add a keyword-only `source_type: type | None = None` parameter on `_walk_selections`. Pass it through to the root `_resolve_field_map(model, source_type=source_type)` at **`walker.py:139`**.
   - Recursive nested calls at **`walker.py:281-288`** (inside `_plan_select_relation`) and **`walker.py:348-355`** (inside `_build_prefetch_child_queryset`) MUST omit `source_type=` (or pass `source_type=None`). The nested target's `registry.get(model)` lookup must still return the primary for nested relation steps. Spec contract: `spec:140-142`, `spec:529` (Decision 6 row 5: "nested target_type lookup unchanged").
   - Remove the TODO anchor at lines 135-138 as part of this edit.
3. **`optimizer/walker.py:28-49` `plan_optimizations`.** Add a keyword-only `source_type: type | None = None` parameter. Thread it into the root `_walk_selections(..., source_type=source_type)` call at **`walker.py:38`**.
   - Remove the TODO anchor at lines 35-37 as part of this edit.
4. **`optimizer/walker.py:481-504` `_selected_scalar_names`.** No signature change (rev6 M1 pinned at `spec:41`, `spec:141`). The existing `_resolve_field_map(model)` call at **`walker.py:496`** stays nested-only (no `source_type` kwarg), which routes through `registry.get(model)` → primary. This is the correct behavior for nested FK-id elision.
   - **Keep** the maintainer's TODO comment block at **`walker.py:488-495`** as a permanent code comment (drop the `TODO(spec-...)` prefix and reword as a non-TODO note documenting the rev6 M1 audit decision). Reasoning: the comment encodes a non-obvious "do NOT thread source_type here" invariant; once the TODO is resolved, the rationale is still load-bearing for future readers. Worker 2 may pick the exact comment wording at discretion (see [Implementation discretion items](#implementation-discretion-items)).

**H2b — Extension origin-and-model helper.**

5. **`optimizer/extension.py:371-411` `_resolve_model_from_return_type(info)`.** Rewrite the return shape per rev6 M2 (`spec:42`, `spec:144`).
   - Add a module-private `class _OriginAndModel(NamedTuple): origin: type; model: type[models.Model]` just above the function (`extension.py:~370`). Reuse the existing `from typing import NamedTuple` import at `extension.py:32`.
   - Change the function return annotation from `type[models.Model] | None` to `_OriginAndModel | None`.
   - Change the final return from `return registry.model_for_type(origin)` to:
     - `model = registry.model_for_type(origin)`
     - `if model is None: return None`
     - `if origin is None: return None` (defensive — the `getattr` at `:395` could theoretically return `None` even when `type_name` resolved)
     - `return _OriginAndModel(origin=origin, model=model)`
   - **Failure contract (rev6 M2 pin):** return `None` whenever **either** origin or model is unresolvable. The existing early returns at lines 387-394 (non-object leaf, missing schema, missing schema type) keep their `return None` behavior — they were already covered.
   - Remove the TODO anchor at lines 396-410 as part of this edit.

6. **`optimizer/extension.py:509-563` `_optimize`.** Adapt the caller to the new helper shape.
   - Change `target_model = _resolve_model_from_return_type(info)` (`:531`) to:
     - `resolved = _resolve_model_from_return_type(info)`
     - `if resolved is None: ...` (the existing pass-through at `:533-538` stays — the `logger.debug` block and the `return result`).
     - `origin, target_model = resolved.origin, resolved.model`
   - Pass `origin` into the plan-cache helper at **`extension.py:550`**: `plan = self._get_or_build_plan(_root_child_selections(selections), target_model, info, origin)`.
   - Remove the TODO anchor at lines 525-530 as part of this edit.

**H2c — Plan cache key + signature plumbing.**

7. **`optimizer/extension.py:565-603` `_get_or_build_plan`.** Add an `origin: type | None` positional parameter (or keyword-only — Worker 2 picks; see discretion items).
   - Pass `origin` to `_build_cache_key(info, target_model, origin)` at **`extension.py:585`**.
   - Pass `origin` to `plan_optimizations(selections, target_model, info=info, source_type=origin)` at **`extension.py:590`**.
   - Remove the TODO anchor at lines 572-584 as part of this edit.
   - **Cache scope (rev6 L1 pin):** This helper is the **sole** insertion site for `_plan_cache`. The `origin` parameter always receives the concrete root origin in production (because the only caller is `_optimize`, which has just unpacked `resolved.origin`). Direct/test-only callers of `_build_cache_key` may pass `origin=None`. Do NOT introduce a nested extension-cache path.

8. **`optimizer/extension.py:667-725` `_build_cache_key`.** Add an `origin: type | None` parameter and append it as the fifth tuple slot.
   - Update the return type annotation to `tuple[str, frozenset[tuple[str, Any]], type, tuple[str, ...], type | None]`.
   - Change the return statement at **`extension.py:725`** to `(doc_key, relevant_vars, target_model, runtime_path_from_info(info), origin)`.
   - Remove the TODO anchor at lines 723-724 as part of this edit; remove the older TODO anchor at lines 692-694 too.

9. **`optimizer/extension.py:452-455` `self._plan_cache` type annotation.** Extend the declared key type to the new five-element tuple shape:
   - From: `dict[tuple[str, frozenset[tuple[str, Any]], type, tuple[str, ...]], Any]`
   - To: `dict[tuple[str, frozenset[tuple[str, Any]], type, tuple[str, ...], type | None], Any]`
   - This is in the `__init__` body. Do not extract a type alias — Decision 9's prose pins the shape inline and the alias would split the documentation surface.

**Net post-Slice-4 H2 behavior** (per `spec:567-605`):
- Root resolver returning `AdminItemType` plans against `AdminItemType.field_map` and `AdminItemType.optimizer_hints` (not the primary's). Plan-cache entries for primary-return and secondary-return resolvers on the same model are distinct.
- Nested relation steps continue to route through `registry.get(related_model)` → primary. Unchanged from today.
- Direct/test-only callers of `_build_cache_key` may pass `origin=None` and receive a valid four-and-a-half-shape key. The slot's `None` value is reserved for those callers.

#### Bucket H3 — Schema-audit dedupe (`optimizer/extension.py`)

Spec: `spec:150`, `spec:533` (Decision 6 last row), `spec:737` (Risks `iter_types` semantic change entry).

10. **`optimizer/extension.py:625-665` `check_schema`.** Switch warning collection from `list[str]` to a `(source_model, field_name)`-keyed accumulator.
    - Current shape (`extension.py:646-664`): `warnings: list[str] = []`, append `f"{_model.__name__}.{field_name} has no registered target DjangoType"` per offending field. Under Slice 1's `iter_types()` semantic change (one yield per registered type per `spec:737`), a model with `{ItemType(primary), AdminItemType}` both exposing the same unregistered-target `category` relation would produce two identical warnings.
    - **New shape:** Replace `warnings: list[str] = []` with two collections — `seen: set[tuple[type[models.Model], str]] = set()` and `warnings: list[str] = []`. Inside the relation-field loop body, when the unregistered-target condition is true (`:661`), add a `key = (_model, field_name)` check: `if key in seen: continue; seen.add(key); warnings.append(...)`. The append at `:662-664` is preserved verbatim; only the dedupe guard is new.
    - **Document the rationale.** Add a one-line comment above the dedupe guard: `# Dedupe (source_model, field_name) so multi-type models do not double-warn` (or equivalent — Worker 2 picks the exact phrasing). The comment should make clear this is a multi-type artifact, not generic defensive coding (per spec: "Document the dedupe rationale in a one-line comment so future readers understand it is a multi-type artifact, not a generic defensiveness").
    - Remove the TODO anchor at lines 640-645 as part of this edit.
    - **Do NOT switch to a `primary_or_single_per_model` iterator** — that helper does not exist (Decision 4 dropped it at `spec:477`) and switching would silently skip secondary-only relation fields (the entire reason rev2 H3 exists).
    - The SKIP-hint guard at **`extension.py:659`** stays in place: SKIP-hinted fields are still excluded from both `seen` and `warnings`.

**Net post-Slice-4 H3 behavior** (per `spec:533`):
- Reachable secondary types whose relation fields the primary does not expose are still audited.
- Identical-string duplicate warnings from overlapping field maps are collapsed to a single warning per `(source_model, field_name)`.

#### Bucket M2-stale — Stale-test rewrites

Spec stale-test surfaces (M2 references at `spec:22, :36`, `:42`, line-targeted at `spec:145-148, :153`).

The spec's pre-Slice-2 line numbers for `tests/types/test_base.py:509, :526, :549, :598` are STALE (the file grew from ~640 lines to 771 lines across Slices 1-3 — Slice 2 added six `Meta.primary` tests). Worker 1 confirmed the **real** sites during planning by reading the current file: the four pre-finalize eager relation-annotation assertions live at **`tests/types/test_base.py:648`**, **`:669-671`**, **`:691-694`**, and **`:748-751`**. See [Notes for Worker 1 (spec reconciliation)](#notes-for-worker-1-spec-reconciliation-1) for the spec-line-correction proposal.

The four `tests/optimizer/test_extension.py:469, :499, :508, :517` line numbers are accurate against the current tree.

**M2a — `tests/types/test_base.py` rewrites (four sites).** Per `spec:153`, pick the smallest-touch option per test.

11. **`tests/types/test_base.py:634-648` `test_relation_fk_to_target_djangotype`.** The pre-finalize assertion `assert ItemType.__annotations__["category"] is CategoryType` (line 648) currently expects the eager-bound `CategoryType` annotation. Under H1 always-defer, this is `PendingRelationAnnotation` pre-finalize.
    - **Action:** Option (a) — add `finalize_django_types()` before the assertion. Smallest-touch: insert one line and update the assertion to read post-finalize. This preserves the test's intent (an FK relation maps to its target type) while accommodating the new defer-then-resolve flow. Imports: `finalize_django_types` is already importable from `django_strawberry_framework` (Worker 2 confirms the import line near the file's top).
12. **`tests/types/test_base.py:651-671` `test_relation_reverse_fk_returns_list`.** The pre-finalize `a = CategoryType.__annotations__; assert a["items"] == list[ItemType]; assert a["properties"] == list[PropertyType]` at lines 669-671 expects eager-bound `list[...]` annotations.
    - **Action:** Option (a) — add `finalize_django_types()` before the `a = ...` line. Re-read `CategoryType.__annotations__` after finalize and assert against the resolved annotations.
13. **`tests/types/test_base.py:674-694` `test_relation_meta_default_when_neither_fields_nor_exclude_set`.** Same pattern at lines 691-694 (`a = CategoryType.__annotations__; ...`).
    - **Action:** Option (a) — add `finalize_django_types()` before the `a = ...` line. Smallest-touch.
14. **`tests/types/test_base.py:723-751` `test_relation_full_chain_when_all_targets_registered`.** Four pre-finalize annotation assertions at lines 748-751.
    - **Action:** Option (a) — add `finalize_django_types()` before the four asserts. Smallest-touch.

**Why option (a) across all four** (rather than option (b) "assert PendingRelationAnnotation pre-finalize" or option (c) "delete; covered by new tests"): each of these tests pins the **target type** of the relation conversion, which is the load-bearing post-finalize contract these tests have always exercised. Asserting pre-finalize `PendingRelationAnnotation` would lose the target-type pin entirely. Deletion would leave a gap because the new auto-deferred regression tests in `tests/types/test_converters.py` target multi-type scenarios; the single-type "FK → target type" coverage in `test_base.py` is still load-bearing and not redundant with the new tests. Option (a) preserves the original test contract by adding the synchronization point the spec's H1 contract introduces.

**Pre-existing pending-state test stays unchanged.** The existing `tests/types/test_base.py:697-714 test_relation_unregistered_target_raises` already asserts `ItemType.__annotations__["category"] is PendingRelationAnnotation` (line 705) pre-finalize for an unregistered target. That assertion remains correct under H1 (the unregistered-target case has always been deferred) and does NOT need a rewrite.

**M2b — `tests/optimizer/test_extension.py` rewrites (four sites; split by case).** Per `spec:145-148`.

15. **`tests/optimizer/test_extension.py:469 test_resolve_model_from_return_type_unwraps_nested_wrappers`** — the **success case**. Rewrite to assert the new helper return shape.
    - The current line 496 `assert _resolve_model_from_return_type(info) is Category` becomes:
      - `result = _resolve_model_from_return_type(info)`
      - `assert result is not None`
      - `assert result.model is Category`
      - `assert result.origin is CategoryType` (the test's locally-declared `class CategoryType(DjangoType)` is in scope at this point)
    - This pins both legs of the new pair contract: `model` is preserved (regression check), `origin` is now exposed (new contract).
16. **`tests/optimizer/test_extension.py:499 test_resolve_model_returns_none_for_non_object_leaf`** — the **failure case** (non-object leaf). Currently asserts `_resolve_model_from_return_type(info) is None`. **Keep as-is** per rev6 M2 (`spec:147`). The helper returns `None` outright when the leaf type has no name — the failure contract returns `None`, not `(origin, None)`.
17. **`tests/optimizer/test_extension.py:508 test_resolve_model_returns_none_when_no_strawberry_schema`** — the **failure case** (missing strawberry schema). Currently asserts `... is None`. **Keep as-is** per rev6 M2.
18. **`tests/optimizer/test_extension.py:517 test_resolve_model_returns_none_when_type_not_in_schema`** — the **failure case** (missing schema type). Currently asserts `... is None`. **Keep as-is** per rev6 M2.

**Risk callout for Worker 3.** Tests 16-18 are listed in the spec checklist under "Rewrite stale tests" (`spec:145, :147`), which a quick read could plausibly interpret as "rewrite to the pair shape." The pin is explicit at `spec:147`: those three tests KEEP asserting `None`. Worker 3 should verify the diff leaves their assertion shape unchanged.

#### Bucket new-tests — Six relation-conversion regressions + seven optimizer regressions

Spec: `spec:154-168`. Test placement per `spec:539-547` (Decision 7) + `spec:32, :36` (rev4 L5 / rev5 M2 — existing hosts are the default; only create `tests/types/test_relations.py` if the host outgrows comfortable size). All new tests use the per-file autouse `_isolate_registry` fixture (`tests/optimizer/test_extension.py:51-56`, `tests/optimizer/test_walker.py` has its own equivalent; `tests/types/test_converters.py` — confirm at write time).

**Test host pin (per spec lines 154 and 161):**
- Six relation-conversion tests → **`tests/types/test_converters.py`** (current file size 1455 lines; spec at `spec:32` explicitly authorizes this host and says "no `tests/types/test_relations.py` exists today" — only create a new file if `test_converters.py` would outgrow a comfortable size; six tests ~150 lines do NOT push that line). **Decision pinned by Worker 1: stay in `test_converters.py`; do NOT create `tests/types/test_relations.py`.**
- Seven optimizer tests → **`tests/optimizer/test_walker.py`** and **`tests/optimizer/test_extension.py`**, split by what the test exercises. **Per-test host pin documented below.**

**N1 — Relation conversion tests (`tests/types/test_converters.py`).** Per `spec:154-160`.

19. **`test_consumer_authored_relation_annotation_override_survives_always_defer`** (H1 regression). Decisive shape per `spec:155`:
    - Declare `AdminItemType(DjangoType)` on `Item` *without* `Meta.primary` (no `primary=True` → not the primary).
    - Declare `ItemType(DjangoType)` on `Item` with `Meta.primary=True`.
    - Declare `CategoryType(DjangoType)` with consumer-authored annotation `items: list["AdminItemType"]` (annotation-only override).
    - Call `finalize_django_types()`.
    - Assert `CategoryType.__annotations__["items"]` resolves to `list[AdminItemType]` (NOT `list[ItemType]` — the consumer override wins over the primary).
    - Mirrors `tests/types/test_definition_order.py:174-198` (the existing annotation-only override test).
20. **`test_consumer_assigned_strawberry_field_relation_survives_always_defer`** (H1 regression). Per `spec:156`:
    - Same multi-type `Item` setup. `CategoryType` uses `@strawberry.field def items(self) -> list[AdminItemType]: return []` (assigned, not annotated).
    - Assert the assigned `StrawberryField` is preserved through `__init_subclass__` and `finalize_django_types()` — `CategoryType.__django_strawberry_definition__.consumer_assigned_relation_fields == frozenset({"items"})` AND no `PendingRelationAnnotation` replaces it.
    - Mirrors `tests/types/test_definition_order.py:201-227` (the existing assigned-resolver override test).
21. **`test_relation_resolves_to_primary_type_when_target_model_has_multiple`** (H1 functional). Per `spec:157`:
    - Declare `ItemType(Meta.primary=True)` and `AdminItemType` on `Item`. Declare `CategoryType` with `items` reverse relation.
    - Finalize. Build a minimal Strawberry schema referencing `CategoryType`. Introspect the schema and assert the `items` field's GraphQL type is `ItemType` (not `AdminItemType`).
    - This is the headline H1 contract test.
22. **`test_relation_resolves_to_primary_when_secondary_registered_before_source_before_primary`** (H1 regression — pins the import-order trap closure). Per `spec:158`:
    - Declaration order matters and is load-bearing:
      1. Declare `AdminItemType` on `Item` *without* `Meta.primary`.
      2. Declare `CategoryType` referencing the `items` reverse relation (the SOURCE).
      3. Declare `ItemType(Meta.primary=True)` on `Item`.
    - Call `finalize_django_types()`. Build a schema. Introspect.
    - Assert `CategoryType.items` resolves to `ItemType` (the primary), NOT `AdminItemType`.
    - **Without H1's always-defer** (pre-Slice-4 behavior): the eager-bind path at `_build_annotations` would freeze `items` to `AdminItemType` at step 2 because `registry.get(Item)` would have returned `AdminItemType` (the single registered type at that moment). The test would fail. This is the exact import-order trap rev2 H1 (`spec:13`) identifies and rev4 H1 (`spec:31`) refines.
23. **`test_relation_resolves_when_target_model_has_one_type_no_primary`** (backward compatibility). Per `spec:159`:
    - Single-type setup: `ItemType` on `Item` *without* `Meta.primary`. `CategoryType` references `items`.
    - Finalize. Assert `CategoryType.__annotations__["items"] == list[ItemType]` post-finalize.
    - Pins that the always-defer change does not break the single-type-no-primary path.
24. **`test_relation_target_with_multiple_no_primary_surfaces_audit_error_at_finalize`** (H1 + Slice 3 audit composition). Per `spec:160`:
    - Declare `CategoryType` with `items` relation to `Item`, plus two `Item` types (`ItemType` and `AdminItemType`) *neither* primary.
    - Assert `finalize_django_types()` raises `ConfigurationError` with message containing the audit's `"Declare Meta.primary = True"` substring.
    - Confirms the audit fires before the unresolved-target error. Slice 3 already pins this at `tests/types/test_definition_order.py:391` for the audit-only case; this test extends it with a relation source in the mix.

**N2 — Optimizer regression tests (`tests/optimizer/test_walker.py` and `tests/optimizer/test_extension.py`).** Per `spec:161-168`.

25. **`test_optimizer_walker_plans_root_from_resolver_return_type_when_secondary`** (H2 regression — root-from-return-type). Per `spec:162`. **Host: `tests/optimizer/test_walker.py`** (walker unit-level test; uses synthetic selection nodes; matches existing walker-test style at e.g. `tests/optimizer/test_walker.py:111-145`).
    - Setup: `ItemType(Meta.primary=True)` on `Item` with `optimizer_hints = {"category": OptimizerHint.SKIP}`; `AdminItemType` on `Item` with `optimizer_hints = {"category": OptimizerHint.prefetch_related()}` (a hint absent from `ItemType`).
    - Call `plan_optimizations([_sel("category")], Item, source_type=AdminItemType)`.
    - Assert the resulting `plan.prefetch_related` reflects `AdminItemType`'s hint (force_prefetch behavior), NOT `ItemType`'s SKIP behavior.
    - Note: Worker 2 must register both types' definitions via the `_register_type_definition` helper at `test_walker.py:83-103` (or extend it to accept `optimizer_hints=`). The helper already takes `optimizer_hints=None` per `:84`; pass differing hints for each type.
26. **`test_scalar_only_secondary_resolver_uses_secondary_field_map`** (rev6 M1 regression — root-from-return-type for scalar-only selection). Per `spec:163`. **Host: `tests/optimizer/test_walker.py`** (walker unit-level; pure-function assertion on `.only_fields`).
    - Setup: register two definitions — `ItemType(Meta.primary=True)` with `field_map` selecting fewer scalars (e.g., `("id", "name")`) and `AdminItemType` with `field_map` selecting more scalars (e.g., `("id", "name", "description")`). Worker 2 uses `_register_type_definition` with a custom `field_map=` kwarg to make the secondary's field map differ from the primary's.
    - Call `plan_optimizations([_sel("description")], Item, source_type=AdminItemType)`.
    - Assert `plan.only_fields == ("description",)`. Without H2 root-threading, `_resolve_field_map(Item)` would route through `registry.get(Item)` → `ItemType`, whose field map omits `description`, and the walker would treat `description` as unknown (the `django_field is None` branch at `walker.py:144`), dropping the only-field projection.
    - Rev6 M1 pin: this test exercises **only** the root `_walk_selections` / `_resolve_field_map(..., source_type=AdminItemType)` path. It does NOT touch `_selected_scalar_names` (that helper is nested-only and stays on the primary).
27. **`test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model`** (H2 regression — plan-cache key separation). Per `spec:164`. **Host: `tests/optimizer/test_extension.py`** (cache-key test; lives near the existing cache-differentiation tests at `test_extension.py:740-880`).
    - Setup: `ItemType(Meta.primary=True)` and `AdminItemType` on `Item`. Build a Strawberry schema with two root fields — `all_items: list[ItemType]` and `all_admin_items: list[AdminItemType]`. Finalize.
    - Execute queries against both root fields and `assert ext.cache_info().size == 2` (two distinct cache entries).
    - Without the cache-key change, both fields would key on the same `(doc_key, vars, Item, response_path)` tuple and produce a `size == 1` collision — wrong plan reused across origin types.
    - This test is paired with the existing `test_cache_differentiates_same_model_root_fields` at `test_extension.py:819` (same model, different response paths — different keys today). This new test extends the contract by holding response paths constant and varying the origin only via a per-field return-type annotation.
28. **`test_optimizer_walker_uses_primary_for_nested_relation_target`** (H2 functional — nested unchanged). Per `spec:165`. **Host: `tests/optimizer/test_walker.py`** (walker unit-level test).
    - Setup: register `ItemType(Meta.primary=True)` and `AdminItemType` on `Item`; register `CategoryType` on `Category`.
    - Call `plan_optimizations([_sel("items", selections=[_sel("name")])], Category)` (NO `source_type` — simulating nested or untyped-root call).
    - Walker's nested `_walk_selections` recursion plans `items` against `ItemType.field_map` (the primary). Assert `plan.prefetch_related == (Prefetch("items", queryset=...),)` and the child plan's only_fields reflect `ItemType`'s scalar set.
    - Pins the nested contract — primary still wins for nested traversal even when both types are registered.
29. **`test_schema_audit_warns_on_relation_field_exposed_only_on_secondary_type`** (H3 regression — secondary-only fields still audited). Per `spec:166`. **Host: `tests/optimizer/test_extension.py`** (schema-audit test; sits next to existing `test_check_schema_warns_unregistered_target` at `test_extension.py:1771`).
    - Setup: `ItemType(Meta.primary=True)` on `Item` with `Meta.fields = ("id", "name")` (no relation fields). `AdminItemType` on `Item` with `Meta.fields = ("id", "name", "category")` (exposes `category` relation). Register `Item` types but never register `Category` (the target). Build a schema referencing `AdminItemType`. Finalize.
    - Assert `DjangoOptimizerExtension.check_schema(schema)` produces a warning containing `"Item.category"` AND `"no registered target"`.
    - Without H3 (if Worker 2 mistakenly switched to a "primary only" iterator), the audit would skip `AdminItemType` and silently miss this warning.
30. **`test_schema_audit_dedupes_when_same_relation_field_visited_via_multiple_types`** (H3 regression — dedupe contract). Per `spec:167`. **Host: `tests/optimizer/test_extension.py`**.
    - Setup: `ItemType(Meta.primary=True)` and `AdminItemType` both on `Item`, both selecting `category` (a relation whose target `Category` has no registered `DjangoType`). Build a schema referencing both. Finalize.
    - Assert `check_schema(schema)` produces exactly **one** warning matching `"Item.category"` (not two). Use `sum(1 for w in warnings if "Item.category" in w) == 1`.
    - Without H3 dedupe, the `iter_types()` semantic change (Slice 1) plus the unchanged audit loop would produce two identical warnings.
31. **`test_model_for_type_reverse_lookup_works_for_secondary_type`** (functional — secondary planability). Per `spec:168`. **Host: `tests/optimizer/test_extension.py`** (registry-reverse-lookup test; can also live in `tests/test_registry.py` — Worker 1 picks).
    - **Test host pin: `tests/optimizer/test_extension.py`** because the spec's prose at `spec:168` frames the test as "Secondary types remain discoverable for the optimizer when a resolver returns an `AdminItemType` directly" — the *optimizer* surface, not the bare registry. Mirrors existing optimizer-side reverse-lookup tests (`test_resolve_model_from_return_type_unwraps_nested_wrappers` at `test_extension.py:469`).
    - Setup: `ItemType(Meta.primary=True)` and `AdminItemType` on `Item`. Build a schema where the root field returns `list[AdminItemType]`. Finalize.
    - Assert `registry.model_for_type(AdminItemType) is Item`. Optionally also unwrap the schema's return-type and call `_resolve_model_from_return_type` on a synthesized `info` — assert the returned `_OriginAndModel.origin is AdminItemType` and `.model is Item`.
    - Pins that the `model_for_type` reverse-lookup contract is unchanged and discoverable for secondaries.

### Test additions / updates

**Stale test rewrites (eight tests, two files).**

- `tests/types/test_base.py:634, :651, :674, :723` — H1 stale rewrites; spec says lines 509, 526, 549, 598 but real positions are line-shifted by Slices 1-3 (`test_base.py` grew from ~640 to 771 lines). Smallest-touch option (a) for all four: insert `finalize_django_types()` before the pre-finalize annotation read.
- `tests/optimizer/test_extension.py:469` — H2 success-case rewrite; assert `_OriginAndModel(origin=..., model=Category)` shape.
- `tests/optimizer/test_extension.py:499, :508, :517` — H2 failure cases; KEEP asserting `None` (rev6 M2 pin).

**New tests (13 tests, three files).**

- `tests/types/test_converters.py` — six relation-conversion tests (#19-24).
- `tests/optimizer/test_walker.py` — three walker tests (#25, 26, 28).
- `tests/optimizer/test_extension.py` — four extension tests (#27, 29, 30, 31).

**Assertion shape — pin per test.**

- Pre-finalize state (where intentionally checked): `__annotations__[field_name] is PendingRelationAnnotation`.
- Post-finalize state (where the contract lands): `__annotations__[field_name] == list[TargetType]` / `is TargetType` / `is TargetType | None` per cardinality.
- Schema-reflective assertions: `schema._schema.type_map[...]` or introspection on `__strawberry_definition__.fields` for the relation field's target type.
- Walker-state assertions: tuple-shape on `plan.select_related`, `plan.prefetch_related`, `plan.only_fields`, `plan.fk_id_elisions`.
- Cache-state assertions: `ext.cache_info().size`, `ext.cache_info().hits`, `ext.cache_info().misses`.

**Temp test opportunities for Worker 3.**

- A temp test under `docs/builder/temp-tests/slice-4-consumer-site-updates/` could verify that the new `_OriginAndModel` named tuple is module-private (no `__all__` export). Worker 3 may write it if review needs evidence, but the helper's named-tuple shape doesn't have a public-surface risk profile that justifies a permanent test.
- A temp test verifying that `_resolve_field_map(model, source_type=None)` is structurally indistinguishable from the pre-change call site (no silent behavior drift on the nested path) could be useful — Worker 3 picks.

### Implementation discretion items

Each item is a stylistic preference between equally-valid shapes that Worker 1 has assessed and explicitly delegates. Architectural decisions stay with the plan.

- **Named tuple vs plain tuple for `_resolve_model_from_return_type`'s return shape.** The plan pins `NamedTuple` because `extension.py` already imports `NamedTuple` for `CacheInfo`. Worker 2 may use a plain `tuple[type, type[models.Model]]` instead if the named-tuple boilerplate feels heavier than the readability gain — both shapes satisfy the rev6 M2 contract. **Default: `NamedTuple` named `_OriginAndModel`.** If switching to plain tuple, the unpack site at `_optimize` (`origin, target_model = resolved`) is mechanically identical; the docstring around the helper should still describe both legs.
- **`_get_or_build_plan(origin)` parameter positioning.** Positional vs keyword-only. The plan's example uses positional. If Worker 2 prefers `*, origin: type | None`, that's fine — there's one call site (`_optimize:550`) and no public callers.
- **Comment wording for the `_selected_scalar_names` rev6 M1 invariant.** The plan keeps the existing TODO comment block at `walker.py:488-495` as a permanent code comment (re-worded to drop the `TODO(spec-...)` prefix). Worker 2 picks the exact phrasing; the load-bearing content is "do NOT thread source_type here; nested-only by design" plus the call-graph rationale.
- **H3 dedupe accumulator shape.** Plan default: parallel `seen: set[tuple[type, str]]` + `warnings: list[str]` with a guard. Alternative: `warnings: dict[tuple[type, str], str]` + `return list(warnings.values())` at the end. Both are correct; the parallel-set shape is the smaller diff. Worker 2 picks.
- **Comment wording on the dedupe rationale.** "Dedupe (source_model, field_name) so multi-type models do not double-warn" is a starting point; Worker 2 picks the exact phrasing as long as the comment encodes "multi-type artifact, not generic defensiveness."
- **Where the `_OriginAndModel` class lives within `extension.py`.** Plan default: immediately above `_resolve_model_from_return_type` (so reading the helper top-down explains the return shape). Worker 2 may place it next to `CacheInfo` (`extension.py:274-279`) for the "small NamedTuple cluster" convention, if that reads better. Both are file-local module symbols.

---

## Notes for Worker 1 (spec reconciliation)

Surface during planning — Worker 1 reads at final verification and decides on a spec edit.

- **Spec line numbers for `tests/types/test_base.py` stale tests are stale.** Spec lines 145 and 153 cite `tests/types/test_base.py:509, :526, :549, :598` for the pre-finalize relation-annotation assertions, but the real positions in the current tree are `:648, :669-671, :691-694, :748-751`. The file grew across Slices 1-3 (Slice 2 added six `Meta.primary` tests; current size 771 lines). The pin-at-write-time line-number convention in BUILD.md covers this, but the spec is deliberately line-reference-heavy and the four cited sites are functionally critical to Worker 2's read-and-edit pass. Recommend Worker 1 either: (a) update the spec to the four real positions during this slice's final verification, or (b) add a one-line note next to spec line 153 stating "pin-at-write-time line numbers; verify against current tree before editing."
- **Spec line 138 references `types/finalizer.py:69`** for the pending-relation resolution path. The actual position in the current tree is `:117` (after Slice 3 added `audit_primary_ambiguity` at `:64-92` and shifted `_resolve_pending` downward). Pin-at-write-time covers this too; same recommendation as the test-file note above.
- **Spec line 140 references `optimizer/walker.py:80`** for the root `_resolve_field_map` call. The actual position is `:74-95` (the function signature), with the body invocation `_walk_selections(..., source_type)` at `:38` in `plan_optimizations`. Pin-at-write-time covers this; spec wording itself is correct.
- **Spec line 144 references `optimizer/extension.py:396`** for `_resolve_model_from_return_type`. Actual position is `:371-411`. Pin-at-write-time covers this.
- **No structural drift expected from this slice.** All H1/H2/H3 contracts are pinned by rev6 M1/M2 + L1/L2, and all stale-test rewrites have explicit per-site instructions. Worker 2 should be able to land the slice without escalation; if structural drift surfaces (e.g., the `_OriginAndModel` shape needs to be public for an unexpected reason), Worker 2 follows BUILD.md's "Plan-vs-implementation drift" → `Status: revision-needed` escalation path.

If any of the line-number drifts above turn out to materially confuse Worker 2 during the implementation pass, Worker 1 may make a small spec edit during final verification per the standing precedent established in Slices 1-3 (Slice 2's spec edit at `spec:319-321` set the precedent: when source-line-pins drift, the spec is updated to match the source). The carry-forward note in `worker-1.md` records this as a recurring pattern.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/base.py` — H1 always-defer. Replaced the eager-bind-or-defer branch in `_build_annotations` with unconditional pending-record + `PendingRelationAnnotation`. Removed the resolved-immediately path, removed the slice-4 TODO anchor pseudo-code block, and rewrote the function docstring to describe the new contract. The `consumer_authored_fields` short-circuit at the relation branch (line 617) and the scalar branch (line 647) stay verbatim. Dropped the now-unused `resolved_relation_annotation` import (ruff would have flagged it; removed proactively).
- `django_strawberry_framework/optimizer/walker.py` — H2a. Added keyword-only `source_type: type | None = None` to `plan_optimizations`, `_walk_selections`, and `_resolve_field_map`. Threaded `source_type` from `plan_optimizations` -> root `_walk_selections` -> root `_resolve_field_map`. Recursive nested `_walk_selections` calls inside `_plan_select_relation` and `_build_prefetch_child_queryset` intentionally omit `source_type=` (defaulting to `None`) so nested targets keep routing through `registry.get(model)` -> primary. Reworded the `_selected_scalar_names` TODO block at lines 488-495 into a permanent code comment that documents the rev6 M1 audit invariant ("do NOT thread source_type here; nested-only by design"). Removed the slice-4 TODO anchor pseudo-code blocks from all three signatures.
- `django_strawberry_framework/optimizer/extension.py` — H2b + H2c + H3. Added `_OriginAndModel` `NamedTuple` (`origin: type`, `model: type[models.Model]`) immediately above `_resolve_model_from_return_type`; reuses the existing `NamedTuple` import. Rewrote `_resolve_model_from_return_type` to return `_OriginAndModel | None` with the rev6 M2 failure contract (returns `None` when either origin or model is unresolvable; returns the pair only when both resolve). Updated `_optimize` to unpack `resolved.origin, resolved.model` and pass `origin` into `_get_or_build_plan`. Extended `_get_or_build_plan` signature with a positional `origin: type | None` parameter and threaded it into `_build_cache_key(info, target_model, origin)` and `plan_optimizations(..., source_type=origin)`. Extended `_build_cache_key` signature with `origin: type | None = None` and appended it as the fifth tuple slot. Extended the `self._plan_cache` type annotation to the five-element key tuple. H3: replaced the `warnings: list[str] = []` accumulator in `check_schema` with a parallel `seen: set[tuple[type, str]] = set()` + `warnings: list[str] = []` shape, guarded the append with `key in seen` / `seen.add(key)`. Added a one-line dedupe-rationale comment ("Dedupe (source_model, field_name) so multi-type models do not double-warn ... a multi-type artifact, not generic defensiveness").

### Tests added or updated

**Stale-test rewrites (in scope).**

- `tests/types/test_base.py::test_relation_fk_to_target_djangotype` — added `finalize_django_types()` before the post-finalize annotation assertion (per-site option (a) from the plan).
- `tests/types/test_base.py::test_relation_reverse_fk_returns_list` — same option (a).
- `tests/types/test_base.py::test_relation_meta_default_when_neither_fields_nor_exclude_set` — same option (a).
- `tests/types/test_base.py::test_relation_full_chain_when_all_targets_registered` — same option (a).
- `tests/optimizer/test_extension.py::test_resolve_model_from_return_type_unwraps_nested_wrappers` — rewrote to assert the new pair shape: `result is not None`, `result.model is Category`, `result.origin is CategoryType`.
- `tests/optimizer/test_extension.py::test_resolve_model_returns_none_for_non_object_leaf` — unchanged (still asserts `None` per rev6 M2 failure-case pin).
- `tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_no_strawberry_schema` — unchanged.
- `tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_type_not_in_schema` — unchanged.

**Stale-test rewrites (small drift; out-of-plan but mechanically obvious).**

- `tests/types/test_definition_order.py::test_reverse_fk_resolves_when_parent_declared_before_child` — flipped the pre-finalize assertion from `CategoryType.__annotations__["items"] == list[ItemType]` to assert `PendingRelationAnnotation`, since H1 always-defer now applies to this case too. Post-finalize assertion unchanged.
- `tests/types/test_definition_order.py::test_reverse_fk_resolves_when_child_declared_before_parent` — same flip on the symmetric pre-finalize assertion.

**Boilerplate updates.**

- `tests/optimizer/test_extension.py::test_cache_eviction_removes_old_entries` — extended the pre-seeded `_plan_cache` keys from 4-tuple to 5-tuple shape (`origin` slot = `None`) to match the new cache-key type annotation. The eviction-removed assertion was updated to the same 5-tuple shape.
- `tests/optimizer/test_extension.py::test_optimize_returns_original_queryset_for_empty_plan` — widened the monkeypatched `plan_optimizations` lambda signature to accept the new `*, source_type=None` keyword (otherwise the lambda would `TypeError` when `_get_or_build_plan` calls it through to the patched stub).

**New tests (13 total).**

- `tests/types/test_converters.py` — six new tests at the end of the file:
  - `test_consumer_authored_relation_annotation_override_survives_always_defer` (H1 regression for annotation overrides).
  - `test_consumer_assigned_strawberry_field_relation_survives_always_defer` (H1 regression for assigned-resolver overrides).
  - `test_relation_resolves_to_primary_type_when_target_model_has_multiple` (headline H1 schema-level contract).
  - `test_relation_resolves_to_primary_when_secondary_registered_before_source_before_primary` (H1 import-order trap closure).
  - `test_relation_resolves_when_target_model_has_one_type_no_primary` (single-type backward-compat).
  - `test_relation_target_with_multiple_no_primary_surfaces_audit_error_at_finalize` (H1 + Slice 3 audit composition).
- `tests/optimizer/test_walker.py` — three new tests at the end of the file:
  - `test_optimizer_walker_plans_root_from_resolver_return_type_when_secondary` (H2 root origin-type propagation through hints).
  - `test_scalar_only_secondary_resolver_uses_secondary_field_map` (rev6 M1 root-from-return-type for scalar-only selection).
  - `test_optimizer_walker_uses_primary_for_nested_relation_target` (H2 nested-unchanged contract).
- `tests/optimizer/test_extension.py` — four new tests at the end of the file:
  - `test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model` (H2 plan-cache origin separation).
  - `test_schema_audit_warns_on_relation_field_exposed_only_on_secondary_type` (H3 secondary-only field still audited).
  - `test_schema_audit_dedupes_when_same_relation_field_visited_via_multiple_types` (H3 dedupe contract).
  - `test_model_for_type_reverse_lookup_works_for_secondary_type` (functional — secondary discoverable; exercises the full `_resolve_model_from_return_type` pair return).

### Validation run

- `uv run ruff format .` — pass (1 file reformatted; 99 unchanged).
- `uv run ruff check --fix django_strawberry_framework/ tests/` — pass (`All checks passed!`). The two pre-existing `scripts/check_spec_glossary.py` errors flagged by `ruff check .` are Slice 1 drift, out of scope.
- `uv run pytest tests/ --no-cov -q` — 610 passed, 3 skipped.
- `uv run pytest examples/ --no-cov -q` — 72 passed (no regression on example HTTP / in-process tests).
- Focused run for the touched test files (`tests/types/test_base.py tests/types/test_converters.py tests/optimizer/test_walker.py tests/optimizer/test_extension.py tests/types/test_definition_order.py --no-cov -q`) — 307 passed, 3 skipped.

### Implementation notes

- **`_OriginAndModel` shape chosen.** Picked the `NamedTuple` shape per the plan default. The class lives **immediately above** `_resolve_model_from_return_type` (not next to `CacheInfo`) so reading the helper top-down explains the return shape; this is one of two equally valid placements the plan delegated to discretion.
- **`_get_or_build_plan(origin)` parameter positioning.** Made it a positional fourth parameter (after `selections`, `target_model`, `info`). There's exactly one call site (`_optimize` line 554) and no public callers; positional reads naturally as "build a plan for these selections of this model, with this resolver info, originating from this Strawberry type."
- **H3 dedupe accumulator shape.** Picked the parallel `seen: set[tuple[type, str]]` + `warnings: list[str]` shape (smaller diff than a `dict[(type,str), str]` alternative, as the plan noted).
- **Comment wording on the dedupe rationale.** Encoded the multi-type-artifact framing per the spec: "Dedupe (source_model, field_name) so multi-type models do not double-warn ... a multi-type artifact, not generic defensiveness ... every reachable type is still audited (we cannot skip secondaries, since a secondary may expose a relation the primary hides)."
- **`_selected_scalar_names` comment.** Reworded the TODO block at `walker.py:488-495` into a permanent code comment ending "(spec-014 rev6 M1 audit invariant.)" so future readers see why `source_type` is intentionally absent at this site.
- **Removed import.** Dropped `resolved_relation_annotation` from `types/base.py:40` since the always-defer change leaves no caller. The helper itself stays defined in `types/converters.py` because the finalizer still calls it.

### Notes for Worker 3

- No shadow file was used during implementation; the planning artifact already cited every line number Worker 2 needed to navigate, and the actual diffs are constrained to specific local regions (H1 = lines 615-645 of base.py; H2 = three signature edits in walker.py + four edits in extension.py; H3 = one loop edit in extension.py). Pin-at-write-time line drift was minimal — every plan-cited site lined up within +/- 5 lines.
- The two `tests/types/test_definition_order.py` stale rewrites (parent-before-child and child-before-parent) are not in the plan's stale-test list. They became stale for the same reason as the four `tests/types/test_base.py:634/:651/:674/:723` sites: H1 always-defer makes every auto-synthesized relation `PendingRelationAnnotation` pre-finalize, regardless of whether the target was already registered. The fix is the same minimal-touch option (a) shape — flip the pre-finalize assertion. Recording here so Worker 3 reviews the edit as a parallel stale-test rewrite, not unrelated test churn.
- `_OriginAndModel` is intentionally module-private (no leading-capital `_`). No `__all__` export change.
- `_plan_cache` type annotation expanded from 4-tuple to 5-tuple per Decision 9; no extracted type alias (the plan pinned the inline shape).
- Cache-eviction test at `tests/optimizer/test_extension.py:925-944` was updated to use 5-tuple keys so its pre-seeded fixtures match the new annotation. This is mechanical, not a contract change.
- The lambda-signature widening at `tests/optimizer/test_extension.py:675` is the same kind of mechanical update — the patched stub needs to swallow the new keyword the production code now passes.

### Notes for Worker 1 (spec reconciliation)

- **Out-of-plan stale-test rewrites in `tests/types/test_definition_order.py`.** Two existing tests (lines 33-52 and 55-74 in the current tree) asserted pre-finalize eager-bind behavior — `assert CategoryType.__annotations__["items"] == list[ItemType]` and `assert ItemType.__annotations__["category"] is CategoryType` BEFORE `finalize_django_types()` was called. Under H1 always-defer these assertions now fail because the pre-finalize state is `PendingRelationAnnotation`. The plan listed the four `tests/types/test_base.py` sites but did not call out these two definition-order sites. I treated this as small-drift (mechanically obvious correction within the slice contract) and applied option (a)-equivalent rewrites: flipped the pre-finalize assertions to `PendingRelationAnnotation` checks; post-finalize assertions stayed identical. Recommend Worker 1 either: (a) accept the in-place rewrite as part of this slice, or (b) update the spec's stale-test catalog (`spec:153`) to include these two sites in the next revision.
- **Spec line numbers in `### Notes for Worker 1` were accurate within +/- ~5 lines.** No spec edits triggered by drift during the implementation pass. The spec's pin-at-write-time disclaimers held up.
- **`test_optimize_returns_original_queryset_for_empty_plan` lambda signature.** The monkeypatched lambda at `tests/optimizer/test_extension.py:675` had to grow `*, source_type=None` to match the new `plan_optimizations` signature. This is a mechanical test-only fix (no contract surface change) and falls under small-drift. Recording for completeness.
- **`test_cache_eviction_removes_old_entries` cache-key shape.** Same category — the test pre-seeds `_plan_cache` with fake keys; those keys grew from 4-tuple to 5-tuple to match the production annotation. No contract drift.
- **No structural drift.** Every architectural decision the plan called out (NamedTuple vs plain tuple, parameter positioning, comment shapes) was a discretion item that landed at the plan's default.

---

## Review (Worker 3)

Static helper invoked on the three Worker-2-touched optimizer/types files. Shadow files written under `docs/builder/shadow/`:

- `django_strawberry_framework__types__base.overview.md` — repeated literals `optimizer_hints` (4x), `description` (2x), `interfaces` (2x). No Slice 4 literals surfaced; the new H1 relation-branch logic adds no string literals.
- `django_strawberry_framework__optimizer__walker.overview.md` — `_resolve_field_map` (`walker.py:83-109`) and `_walk_selections` (`walker.py:140-273`) now carry the `source_type` parameter; `_selected_scalar_names` (`walker.py:502-525`) intentionally omits it (rev6 M1 audit invariant captured as permanent code comment at lines 509-516). Three `_walk_selections` call sites: line 46 (root, threads `source_type=source_type`), line 302 (`_plan_select_relation` nested, omits source_type), line 369 (`_build_prefetch_child_queryset` nested, omits source_type). Repeated literals untouched by Slice 4.
- `django_strawberry_framework__optimizer__extension.overview.md` — new `_OriginAndModel` NamedTuple at `extension.py:371-386`, `_resolve_model_from_return_type` at `:389-420` returns `_OriginAndModel | None`, `_optimize` unpacks the pair at `:542`, `_get_or_build_plan` carries `origin` to `_build_cache_key` at `:590` and to `plan_optimizations(..., source_type=origin)` at `:595`, `_build_cache_key` returns the five-element tuple at `:732-735`, `_plan_cache` annotation extended at `:461-464`. H3 dedupe via parallel `seen: set[tuple[type[models.Model], str]]` at `:653` + guard at `:670-673`. No new repeated string literals.

### High:

None.

### Medium:

None.

### Low:

#### L1 — Cache-key test does not strictly pin "origin slot is what distinguishes the keys"

`tests/optimizer/test_extension.py::test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model` asserts `ext.cache_info().size == 2` after running two queries against two root fields (`allItems` and `allAdminItems`). Two cache entries DO land, but the existing `response_path` slot in the key (`("allItems",)` vs `("allAdminItems",)`) is sufficient to distinguish them on its own — the new `origin` slot is not strictly load-bearing in this test. A stricter pin would force `response_path` and `doc_key` to agree (e.g. aliasing both root fields to the same response key, or executing the same selection through two separate `DjangoOptimizerExtension` instances on schemas that only differ by root-field return type) so the only differentiator is `origin`.

This is mitigated by the broader test suite: `test_optimizer_walker_plans_root_from_resolver_return_type_when_secondary` and `test_scalar_only_secondary_resolver_uses_secondary_field_map` directly verify the `source_type=origin` threading reaches the walker, and `test_resolve_model_from_return_type_unwraps_nested_wrappers` pins the `_OriginAndModel.origin` capture at the resolver helper. So the H2 contract is verifiable across the cluster, but the cache test by itself does not isolate the origin slot.

Recommendation: Worker 1 may weigh during final verification whether to land a stricter pin (likely a new test that holds response_path constant) or accept the cluster-level coverage. Either is defensible; Slice 4 acceptance does not block on it.

```tests/optimizer/test_extension.py:2900
@pytest.mark.django_db
def test_plan_cache_keys_distinguish_primary_and_secondary_returns_for_same_model():
    ...
    schema.execute_sync("{ allItems { name } }")
    schema.execute_sync("{ allAdminItems { name } }")
    assert ext.cache_info().misses == 2
    assert ext.cache_info().size == 2
```

#### L2 — H3 dedupe comment is multi-line, plan said "one-line"

The plan and the spec at line 150 both ask for a "one-line comment" to document the dedupe rationale. Worker 2 wrote a seven-line block at `extension.py:645-652`. Content is correct and clear; the multi-type-artifact framing is preserved per the spec contract. The seven-line form is a minor stylistic departure from the plan's wording — Worker 2's implementation-discretion notes flagged comment wording as a discretion item, and the multi-line form is arguably more readable here because the rationale references the spec contract and the iter_types semantic change explicitly. No correctness impact; flagging as Low only because spec wording specified "one-line."

```django_strawberry_framework/optimizer/extension.py:645:652
        # Dedupe (source_model, field_name) so multi-type models do not
        # double-warn: registry.iter_types() yields one entry per registered
        # type after spec-014 Slice 1, so a model with multiple types whose
        # field maps overlap on the same unregistered-target relation would
        # otherwise produce one identical warning per registered type. The
        # dedupe is a multi-type artifact, not generic defensiveness — every
        # reachable type is still audited (we cannot skip secondaries, since
        # a secondary may expose a relation the primary hides).
```

### DRY findings

None new. The DRY discipline this slice carried in the plan held up under implementation:

- `_resolve_field_map` remains the single `_meta.get_fields()` access site; the `source_type` parameter extended the helper in place rather than spawning a sibling.
- `_OriginAndModel` is one module-private NamedTuple with one call site (`_resolve_model_from_return_type`'s return) and one unpack site (`_optimize`'s consumer at `:542`); no parallel pair-builder duplication.
- The cache-key five-tuple is constructed exactly once at `_build_cache_key`'s `return` (`:732-735`); the `self._plan_cache` annotation at `:461-464` was updated in the same edit, so the declared key type stays in sync with the constructor.
- The H3 dedupe accumulator (`seen: set[tuple[type[models.Model], str]]` + `warnings: list[str]`) is one local pair inside one function (`check_schema`). No global accumulator, no helper extraction; the alternative `dict[(type, str), str]` shape was correctly rejected by the plan.
- `definition.primary` is still NOT read anywhere in `django_strawberry_framework/` — the Decision 8 L3 contract holds across Slice 4 (grep confirms; the only mentions of `.primary` are in tests, the `DjangoTypeDefinition` dataclass itself, and the spec).
- The H1 always-defer change collapsed the eager-bind / pending-record branches into one path. The unused `resolved_relation_annotation` import was dropped from `types/base.py:40` — the helper still lives in `types/converters.py` for the finalizer's call site, so the import elision is the correct localization.
- The new test cluster (six relation-conversion tests + seven optimizer tests) all redeclare type pairs inline; no shared factory was introduced. Matches the plan's deliberate "do NOT introduce a shared module-level helper for build a multi-type Item pair" decision and mirrors the existing `tests/types/test_definition_order.py:177-218` convention.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returns empty — `__all__` and the re-export list are unchanged. The new `_OriginAndModel` NamedTuple is module-private (`_`-prefixed) and lives only in `optimizer/extension.py`. No new public exports authorized by the spec for Slice 4 (the Definition of done at `spec:756-773` does not list any). Pass.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The single spec edit in the working tree (`docs/spec-014-meta_primary-0_0_6.md:318-326`, expanding the TODO-anchor placement comment) predates Slice 4 — it was made by Worker 1 during Slice 2's final-verification per the worker-3 memory note on Slice 2's Low finding. Slice 4 Worker 2 did NOT edit the spec; the diff against the prior committed spec shows only the Slice-2-era edit.

### What looks solid

- **rev6 M1 audit invariant pinned in three places.** The TODO comment at `walker.py:488-495` was correctly converted to a permanent code comment (`walker.py:509-516`) ending with "(spec-014 rev6 M1 audit invariant.)". The contract is encoded in code, in a regression test (`test_scalar_only_secondary_resolver_uses_secondary_field_map`), and in the plan — three independent pins for a non-obvious "do NOT thread `source_type` here" invariant.
- **rev6 M2 failure contract pinned exactly.** `_resolve_model_from_return_type` returns `None` whenever ANY leg fails: non-object leaf (`:406-407`), missing strawberry schema (`:408-410`), missing schema type (`:411-413`), missing origin (`:414-416`), missing model (`:417-419`). The pair is returned only when both legs resolve (`:420`). The success case `:469` asserts the pair shape; failure cases `:502`, `:511`, `:520` continue to assert `None`. The risk callout in the plan ("Tests 16-18 are listed in the spec checklist under Rewrite stale tests... the pin is explicit at spec:147") held.
- **rev6 L1 cache scope held.** `_get_or_build_plan` is the sole insertion site for `_plan_cache` (`extension.py:590-606`). Nested walker recursion at `walker.py:302, :369` does not call `_build_cache_key` and leaves `source_type=None`. The walker's `_selected_scalar_names` is untouched. No nested extension-cache path was introduced.
- **H1 consumer-authored short-circuit preserved.** `types/base.py:621` short-circuit (relation branch) and `types/base.py:644` short-circuit (scalar branch) are both unchanged. The always-defer logic only runs AFTER the short-circuit, so consumer overrides survive verbatim. The two regression tests `test_consumer_authored_relation_annotation_override_survives_always_defer` and `test_consumer_assigned_strawberry_field_relation_survives_always_defer` directly pin both flavors of consumer override.
- **H1 import-order trap closure pinned.** The `test_relation_resolves_to_primary_when_secondary_registered_before_source_before_primary` test orchestrates the exact declaration order rev2 H1 identified (secondary → source → primary) and asserts the post-finalize relation resolves to the primary. Schema-level introspection follows.
- **H2 origin threading verified end-to-end.** The `source_type` parameter flows from `optimizer/extension.py:_optimize` → `_get_or_build_plan(origin)` → `plan_optimizations(..., source_type=origin)` → `_walk_selections(..., source_type=source_type)` → `_resolve_field_map(model, source_type=source_type)`. Three walker tests (`test_optimizer_walker_plans_root_from_resolver_return_type_when_secondary`, `test_scalar_only_secondary_resolver_uses_secondary_field_map`, `test_optimizer_walker_uses_primary_for_nested_relation_target`) pin each leg of the propagation.
- **H3 dedupe with full reachable-type iteration.** `check_schema` continues to call `registry.iter_types()` (no switch to a `primary_or_single_per_model()` helper). The `seen: set[tuple[type, str]]` accumulator dedupes warnings without dropping the audit of secondary-only relation fields. Both H3 regression tests pass.
- **Out-of-plan small drift on `tests/types/test_definition_order.py` is mechanically obvious.** Worker 2 flipped two pre-finalize `assert ... == list[ItemType]` / `assert ... is CategoryType` assertions to `assert ... .__name__ == "PendingRelationAnnotation"` (same shape as the existing in-test pattern). Post-finalize assertions stayed identical. The drift is intrinsic to H1 always-defer (every auto-synthesized relation is now `PendingRelationAnnotation` pre-finalize, regardless of whether the target was already registered) and Worker 2 correctly flagged it for Worker 1.
- **`test_cache_eviction_removes_old_entries` and `test_optimize_returns_original_queryset_for_empty_plan` adjustments.** The 5-tuple cache key shape change forced two mechanical test updates (pre-seeded fixture keys grew from 4-tuple to 5-tuple; the monkeypatched `plan_optimizations` lambda grew `*, source_type=None`). Both are minimal test-only fixes; no contract surface drift.
- **Validation discipline.** Worker 2 ran `uv run ruff format .` and `uv run ruff check --fix django_strawberry_framework/ tests/`; both pass. No `pytest --cov*` flags were used.
- **Plan-cite line accuracy.** The plan's pin-at-write-time line numbers landed within +/- 5 lines of the real positions Worker 2 edited. The four spec-cited `tests/types/test_base.py:509, :526, :549, :598` shifts (real positions `:648, :669-671, :691-694, :748-751`) were called out in the plan's `Notes for Worker 1`.

### Temp test verification

- Worker 3 attempted a temp test under `docs/builder/temp-tests/slice-4-consumer_site_updates/test_h3_dedupe_secondary_only.py` to extend the H3 dedupe check to three reachable types and the "every type SKIPs" suppression case. The test setup ran into a Strawberry `UnresolvedFieldTypeError` on `CategoryType.items` because the `_isolate_registry` fixture cleared the registry between the type declarations and the schema build (a fixture-pattern issue, not a Slice 4 contract issue). The temp test was deleted; the in-tree `test_schema_audit_dedupes_when_same_relation_field_visited_via_multiple_types` already pins the two-type dedupe case and the SKIP-hint guard is verified by existing tests around the H3 surface. **Disposition:** deleted. No follow-up needed.
- Worker 2 noted possible temp test opportunities in the plan (lines 280-282); both are observability-style checks (the named tuple is module-private; nested `source_type=None` is structurally identical to the pre-change call site). The in-tree tests already cover the contract-level pins; no temp test was load-bearing.

### Notes for Worker 1 (spec reconciliation)

- **Spec line-number drift catalog from Worker 2's build report is accurate.** Lines 145-148, 153, 138, 140, 144 in the spec carry pin-at-write-time line numbers that no longer match the post-Slices-1-3 tree (`tests/types/test_base.py` grew from 640 to ~771 lines; `types/finalizer.py:69` is now `:117`; `optimizer/walker.py:80` is now `:74-95`; `optimizer/extension.py:396` is now `:371-411`). Worker 1 may either: (a) update the spec to the post-Slice-4 positions during final verification, or (b) add a one-line "verify against current tree before editing" note next to each cited site. Either is fine; spec is line-reference-heavy by design and a maintainer reading the spec in isolation could mis-navigate.
- **L1 cache-key test weakness.** The H2 cache-key test relies on `response_path` distinguishing the two queries; the new `origin` slot is not strictly load-bearing in this test (see Low L1 above). Worker 1 may add a complementary test (or accept the cluster-level coverage) during integration pass review.
- **Out-of-plan stale-test rewrites in `tests/types/test_definition_order.py:33-55, :58-79`.** Mechanical pre-finalize assertion flips per H1 always-defer. Worker 2 surfaced this explicitly; the rewrites are within the slice's contract envelope and do not require a spec edit. Worker 1 may opt to extend the spec's stale-test catalog (`spec:153`) to include these two sites for completeness in a future revision.
- **No structural drift.** All architectural decisions held to the plan; the discretion items (NamedTuple shape, parameter positioning, comment wording, dedupe accumulator shape) landed at the plan's defaults. No `revision-needed` escalation triggered during the build pass.

### Review outcome

`review-accepted` — every spec-required behavior is reflected in the diff, every Worker-2-touched file passes ruff/format, every High/Medium severity finding is `None`, and the two Low findings carry recorded reasons (test weakness mitigated by sibling coverage; comment length is a discretion item). Tests 610 pass + 3 skip in `tests/`; 72 pass in `examples/`. Setting `Status: review-accepted`.

---

## Final verification (Worker 1)

- **DRY check across Slice 4 + Slices 1-3.** No new duplication introduced. Specific cross-slice surfaces walked:
  - `source_type=` keyword is threaded through one root call chain (`extension._optimize` -> `_get_or_build_plan` -> `plan_optimizations` -> `_walk_selections` -> `_resolve_field_map`); every nested call site (`walker.py:_plan_select_relation`, `walker.py:_build_prefetch_child_queryset`, `walker.py:_selected_scalar_names`) intentionally omits it. The pre-existing `PendingRelation.source_type` dataclass attribute (`types/relations.py`, populated at `types/base.py:670`) is a name-only collision with the walker parameter; semantically distinct (the relation source's DjangoType vs. the resolver's return type), so not a DRY hazard. No consolidation needed.
  - `_OriginAndModel` NamedTuple (`optimizer/extension.py:371-386`) sits beside the pre-existing `CacheInfo` NamedTuple (`optimizer/extension.py:274-279`); both reuse the single `from typing import NamedTuple` import (`extension.py:32`). The two-NamedTuple cluster pattern is intentional and DRY (one shared import, two module-local helpers). No duplication.
  - The five-element plan-cache key tuple is constructed exactly once at `_build_cache_key`'s `return` (`extension.py:736`); the `self._plan_cache` annotation (`extension.py:461-464`) was extended in the same edit. The constructor and the declared key type stay synchronized; no parallel tuple-builder duplication risk.
  - The H3 audit dedupe set (`seen: set[tuple[type[models.Model], str]]` at `extension.py:653`) lives in `check_schema` only — no global accumulator, no helper extraction, no parallel-set pattern in any other slice surface. Iteration still uses Slice 1's `registry.iter_types()` (one yield per registered type); the dedupe sits at the warning-collection layer per Decision 6 row 7.
  - `definition.primary` is store-only across all four slices (Decision 8 L3) — `grep "\.primary" django_strawberry_framework/` confirms the only consumer-side reads are in the `DjangoTypeDefinition` dataclass itself, the registry's `register_with_definition` wrapper (which forwards the keyword), and `types/base.py:128` where Slice 2 populates the field. No optimizer / audit / converter code reads it for routing. Decision 8 L3 contract holds.
  - Slice 1's `iter_types()` semantic change (one yield per registered type) and Slice 4's `seen` dedupe in `check_schema` are the matched pair — Slice 1 broadened the iteration; Slice 4 deduped at the consumer per `spec:737`. Confirmed coherent.
- **Existing tests still pass.**
  - `uv run pytest tests/ --no-cov -q` -> 610 passed, 3 skipped (the 3 skips are pre-existing — relay-noqa / generic-FK / conditional-import surfaces unrelated to Slice 4).
  - `uv run pytest examples/ --no-cov -q` -> 72 passed (full example tree, includes `examples/fakeshop/tests/` and `examples/fakeshop/test_query/`).
  - No coverage flags used. Pass.
- **Spec reconciliation.** One spec edit applied this slice — see `### Spec changes made (Worker 1 only)` below. The two Worker-3 Low findings (L1 cache-key test weakness, L2 multi-line dedupe comment) are non-blocking and accepted as-is:
  - **L1 (cache-key test):** the H2 cache-key test relies on `response_path` (`("allItems",)` vs `("allAdminItems",)`) to distinguish the two cache entries; the new `origin` slot is not the unique differentiator in that single test. However, cluster-level coverage compensates: `test_optimizer_walker_plans_root_from_resolver_return_type_when_secondary` and `test_scalar_only_secondary_resolver_uses_secondary_field_map` directly verify the `source_type=origin` threading reaches the walker, and `test_resolve_model_from_return_type_unwraps_nested_wrappers` pins the `_OriginAndModel.origin` capture. The H2 contract is verifiable across the test cluster; an additional stricter-pin test (holding `response_path` constant) is deferred to the integration pass for consideration. Acceptable as-is.
  - **L2 (H3 dedupe comment is seven lines, not one):** the spec at line 150 said "one-line comment"; Worker 2 wrote a seven-line block at `extension.py:645-652`. The content is correct, the multi-type-artifact framing is preserved per spec, and the rationale references both the spec contract and the `iter_types()` semantic change. The expansion is a code-comment clarity matter, not a correctness issue. Accepted as-is per Worker 2's discretion (comment wording was an explicit discretion item in the plan).
- **Final status:** `final-accepted`.

### Summary

Slice 4 shipped the H1/H2/H3 trifecta — the three high-severity contracts that constitute the consumer-site updates layer of spec-014:

- **H1 always-defer (`types/base.py`).** Replaced the eager-bind-or-defer dispatch in `_build_annotations`'s relation branch with unconditional pending-record + `PendingRelationAnnotation`. The `consumer_authored_fields` short-circuit (relations branch + scalars branch) is preserved verbatim, so consumer annotation overrides and assigned `strawberry.field` resolvers still skip synthesis entirely. The change closes the import-order trap where a secondary registered before the source would freeze a relation against the secondary even when the primary later registered.
- **H2 origin-type propagation (`optimizer/walker.py` + `optimizer/extension.py`).** Added `source_type` keyword threading through `plan_optimizations -> _walk_selections -> _resolve_field_map`; introduced the `_OriginAndModel` NamedTuple as `_resolve_model_from_return_type`'s new return shape (pair-or-`None` failure contract per rev6 M2); extended `_get_or_build_plan` and `_build_cache_key` with an `origin` parameter; extended the plan-cache key from four to five elements with `origin: type | None` as the fifth slot; extended `self._plan_cache`'s type annotation in lockstep. Nested walker paths (`_plan_select_relation`, `_build_prefetch_child_queryset`, `_selected_scalar_names`) stay on the primary by design.
- **H3 audit dedupe (`optimizer/extension.py`).** Replaced the plain-list `warnings` accumulator in `check_schema` with a parallel `seen: set[tuple[type, str]]` + `warnings: list[str]` pair plus a guard. Continues to iterate every reachable registered type via `registry.iter_types()` so secondary-only relation fields are still audited; dedupes at the `(source_model, field_name)` layer so multi-type models do not double-warn.

Test deliverables: four stale-test rewrites in `tests/types/test_base.py` (option (a) per-site: insert `finalize_django_types()` before pre-finalize annotation reads), two out-of-plan small-drift rewrites in `tests/types/test_definition_order.py` (mechanical pre-finalize flips per H1 always-defer; now spec-authorized at line 153), six new relation-conversion regressions in `tests/types/test_converters.py`, three new walker regressions in `tests/optimizer/test_walker.py`, four new extension regressions in `tests/optimizer/test_extension.py`, plus two mechanical 5-tuple-shape boilerplate updates in `tests/optimizer/test_extension.py` for the cache-key fixture and the monkeypatched `plan_optimizations` lambda.

Definition 8 L3 contract holds across the slice — `definition.primary` is store-only; all routing flows through `registry.get`, `registry.primary_for`, and the threaded `origin` parameter. Slice 4 is the largest commit in the build (1,560 insertions across 14 files); review and verification completed in one Worker-2 pass and one Worker-3 pass with no `revision-needed` escalation.

### Spec changes made (Worker 1 only)

- **`docs/spec-014-meta_primary-0_0_6.md:153`** (the M2 stale-test checklist for `tests/types/test_base.py`). Slice 4 final verification. Updated the four pre-finalize-line references from the pre-Slice-2 positions (`:509`, `:526`, `:549`, `:598`) to the post-Slice-3 positions (`:648`, `:669-671`, `:691-694`, `:748-751`); the file grew from ~640 to ~771 lines across Slices 1-3. Added a sentence authorizing the two parallel rewrites in `tests/types/test_definition_order.py:33-55` and `:58-79` that Worker 2 performed as out-of-plan small drift (mechanical pre-finalize-assertion flips per H1 always-defer; same root cause as the `test_base.py` sites). Smallest reconciling edit; precedent matches Slice 2's spec edit at `:319-321` ("when source-line-pins drift, update the spec to match the source"). The rev3 M2 historical narrative at spec line 22 still cites the original pre-Slice-2 positions — left unchanged because the revision-history block is the accurate record of the spec's authoring state and the actionable surface is the slice checklist at line 153.
