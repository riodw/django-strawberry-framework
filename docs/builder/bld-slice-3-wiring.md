# Build: Slice 3 — Wiring — Meta.orderset_class promotion + finalizer phase 2.5 binding

Spec reference: `docs/spec-028-orders-0_0_8.md` (Slice 3 checklist at the spec's `## Slice checklist` section — spec lines 120-123)
Status: review-accepted

## Plan (Worker 1)

### DRY analysis

Slice 3 is a one-for-one mirror of the shipped Filtering subsystem's `_bind_filtersets()` umbrella helper + `_bind_filterset_owner()` binding + `_validate_filterset_class()` validator + the `registry.clear()` namespace-clear blocks, with the order-side simplifications named in Spec Decision 6 (no own-PK Relay-identity axis on the order side because `ORDER BY id` against any model uses the column, not the GraphQL ID type). Every cite below uses the symbol-qualified `path::Symbol` form per `AGENTS.md` #"Source references in docs and code comments" plus inline raw `path:NN` line refs (allowed per `AGENTS.md` since this is a `bld-*.md` scratchpad).

- **Existing patterns reused (verbatim structural mirror with substitutions).**
  - `django_strawberry_framework/types/base.py::_validate_filterset_class` (base.py:83-106) — the function this slice ports as `_validate_orderset_class(meta, orderset_class)`. Substitutions: `filterset_class`→`orderset_class`, `FilterSet`→`OrderSet`, `Meta.filterset_class`→`Meta.orderset_class`, `from ..filters.sets import FilterSet`→`from ..orders.sets import OrderSet`. Same `if filterset_class is None: return None` short-circuit; same `isinstance(filterset_class, type) and issubclass(filterset_class, FilterSet)` shape; same `ConfigurationError` message structure (`f"{meta.model.__name__}.Meta.orderset_class must be an OrderSet subclass; got {orderset_class!r}"`). **Local in-function import** of `OrderSet` from `..orders.sets` is the critical contract per Spec N3 of rev1 + DoD item 9 — dodges the `types → orders → types` module-load cycle. Worker 2 MUST NOT hoist this import to module top.
  - `django_strawberry_framework/types/base.py::DEFERRED_META_KEYS` (base.py:48-55) and `ALLOWED_META_KEYS` (base.py:57-69) — the two frozensets to surgically edit. Drop `"orderset_class"` from `DEFERRED_META_KEYS`; add `"orderset_class"` to `ALLOWED_META_KEYS` (alphabetized — between `"optimizer_hints"` and `"primary"`). Mirrors the same one-line `"filterset_class"` move applied in `DONE-027-0.0.8`.
  - `django_strawberry_framework/types/base.py::_ValidatedMeta` (base.py:571-590) — the `NamedTuple` snapshot of validated Meta keys. Add `orderset_class: type | None` as a new slot immediately after `filterset_class: type | None` (preserves the spec-named ordering at base.py:587-590 TODO anchor).
  - `django_strawberry_framework/types/base.py::_validate_meta` (base.py:593-679) — the validator dispatch. Add one call `orderset_class = _validate_orderset_class(meta, getattr(meta, "orderset_class", None))` immediately after the existing `filterset_class = _validate_filterset_class(...)` call at base.py:665; include `orderset_class=orderset_class` in the `_ValidatedMeta(...)` constructor at base.py:670-679. Mirrors the filter side's one-line addition pattern verbatim.
  - `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` (base.py:281-303) — the `DjangoTypeDefinition(...)` constructor call. Add `orderset_class=validated.orderset_class` immediately after the existing `filterset_class=validated.filterset_class,` at base.py:299 (where the TODO anchor at base.py:300-302 currently parks the work). Same pattern the filter side applied.
  - `django_strawberry_framework/types/definition.py::DjangoTypeDefinition` (definition.py:14-194) — the dataclass. Add `orderset_class: type | None = None` immediately after `filterset_class: type | None = None` at definition.py:91 (the TODO anchor at definition.py:92-98 currently parks the slot). The class-docstring's bullet listing `filterset_class` semantics (definition.py:49-56) grows a parallel `orderset_class` bullet — Worker 2 may keep this terse: "`orderset_class` is the per-owner `OrderSet` sidecar populated by `DjangoType.__init_subclass__` from `Meta.orderset_class` once promoted out of `DEFERRED_META_KEYS`; consumed by `finalize_django_types()` phase 2.5 to bind the owning `DjangoTypeDefinition` on the OrderSet and to materialize the generated Strawberry input class as a module global of `django_strawberry_framework.orders.inputs`." Mirrors the filter side's bullet at definition.py:49-56 one-for-one.
  - `django_strawberry_framework/types/finalizer.py::_bind_filterset_owner` (finalizer.py:278-384) — the per-orderset binding helper. Slice 3 ports the FIRST-bind model-compatibility branch (finalizer.py:316-336) and the IDEMPOTENT re-bind branch (finalizer.py:337-338); per Spec Decision 6 second-paragraph rationale ("The filter side's separate own-PK Relay-identity check is **NOT** ported — the order side has no equivalent (`ORDER BY id` against any model uses the column, not the GraphQL ID type), so the order-side check is narrower than the filter side's by one axis"), the order side's `_bind_orderset_owner` SKIPS the Axis-1 own-PK Relay-identity check at finalizer.py:339-350. Worker 2 keeps the Axis-2 related-target-agreement check (finalizer.py:351-384) for multi-owner reuse — adapted to walk `getattr(orderset_cls, "related_orders", {})` instead of `getattr(filterset_cls, "related_filters", {})`. The result: the order-side helper is ~70 lines instead of the filter side's 107 (one axis dropped, same idempotent + first-bind structure).
  - `django_strawberry_framework/types/finalizer.py::_bind_filtersets` (finalizer.py:503-622) — the four-subpass umbrella helper. Slice 3 ports verbatim with the substitutions `filtersets`→`ordersets`, `filterset`→`orderset`, `FilterArgumentsFactory`→`OrderArgumentsFactory`, `filters.factories`→`orders.factories`, `filters.inputs`→`orders.inputs`, `_helper_referenced_filtersets`→`_helper_referenced_ordersets`, `filterset_class`→`orderset_class`, `get_filters()`→`get_fields()` (Layer-4 expansion method name differs by subsystem). The **four-subpass order is preserved verbatim per Spec B1 of rev2**: (1) bind owners; (2) expand fields; (3) orphan-validate; (4) materialize. The ordering matches the shipped filter side (finalizer.py docstring lines 19-30 + the umbrella body at finalizer.py:548-622) NOT the spec-027 rev8 H1 prescription which had the order inverted. The `ImportError`-rewrap pattern at finalizer.py:569-577 ports verbatim with the same `repr(exc)` + `from exc` `__cause__`-preservation contract.
  - `django_strawberry_framework/types/finalizer.py::_format_orphan_filtersets_error` (finalizer.py:462-484) — the orphan-error message formatter. Slice 3 ports as `_format_orphan_ordersets_error(orphans)` with the substitutions `filter_input_type`→`order_input_type`, `Meta.filterset_class`→`Meta.orderset_class`, `FilterSet`→`OrderSet`. Same single-orphan-vs-multi-orphan branching at finalizer.py:471-484. Same sorting by `cls.__module__.cls.__qualname__`.
  - `django_strawberry_framework/types/finalizer.py::_format_owner_model_mismatch_error` (finalizer.py:440-459) — the first-bind model-mismatch formatter. Slice 3 ports as `_format_owner_orderset_model_mismatch_error(orderset_cls, owner)` with the same four names in the message (owner type, owner model, orderset class, orderset model). Same `Meta.filterset_class`→`Meta.orderset_class`, `FilterSet`→`OrderSet` substitutions. Per Spec Decision 6's `test_phase_2_5_rejects_orderset_wired_to_unrelated_owner_model` test contract (spec line 603), the message must name all four entities.
  - `django_strawberry_framework/types/finalizer.py::_format_owner_mismatch_error` (finalizer.py:387-412) — the diverging-target multi-owner error formatter. Slice 3 ports as `_format_owner_ordersets_mismatch_error(orderset_cls, previous, new, field_name, prev_target, new_target)` with the `FilterSet`→`OrderSet` substitution. Drives the Axis-2 related-target-agreement raise.
  - `django_strawberry_framework/types/finalizer.py::finalize_django_types` (finalizer.py:145-275) — the orchestrator. Slice 3 adds ONE line: `_bind_ordersets()` at finalizer.py:260 (where the TODO anchor at finalizer.py:260-267 currently parks the work). Placed AFTER `_bind_filtersets()` at finalizer.py:259 and BEFORE the Phase 3 `strawberry.type(...)` loop at finalizer.py:269. The placement matches the spec's "immediately after the existing `_bind_filtersets()` umbrella helper and before phase 3's `strawberry.type` decoration" contract verbatim.
  - `django_strawberry_framework/registry.py::TypeRegistry.clear` (registry.py:395-442) — the test-only clear method. Slice 3 adds TWO new blocks at registry.py:434-442 (where the TODO anchor currently parks the work). Block 1: `from .orders.inputs import clear_order_input_namespace` + call (mirrors the filter side's block at registry.py:420-425). Block 2: `from .orders import _helper_referenced_ordersets` + `.clear()` call (mirrors the filter side's block at registry.py:427-432). **Both blocks use the `except ImportError: pass` + `else:` shape — NOT `return` on the last block** per Spec M-core-4 of rev1 + Spec B2 of rev1 (a future card adding a fifth clear phase, e.g., aggregates 0.1.3, must not be silently skipped on a partial-load environment). The shipped TypeRegistry field names used by the existing block 1 of the model-state clear at registry.py:404-410 (`_types`, `_primaries`, `_models`, `_enums`, `_definitions`, `_pending`, `_finalized`) are verbatim from `TypeRegistry.__init__` at registry.py:44-50 — Slice 3's additions DO NOT touch those field clears. **Per Spec B2+B3 of rev2 + the prompt: the phantom `_types_by_model` / `_primary_types` names from rev1 were errors; the shipped/correct names are the seven listed above.**
  - `django_strawberry_framework/orders/inputs.py::clear_order_input_namespace` (orders/inputs.py:417-488) — **already shipped in Slice 2 per the worker-1 memory Slice 2 final-verification entry.** Slice 3 ONLY wires `registry.clear()` to call it. The helper itself is not re-shipped; the Slice 3 plan's `_bind_ordersets()` materialize subpass calls `materialize_input_class` directly (not `clear_order_input_namespace`).
  - `django_strawberry_framework/orders/__init__.py::_helper_referenced_ordersets` (orders/__init__.py:39) — **already shipped in Slice 2.** Slice 3 ONLY wires `registry.clear()` to call `.clear()` on it.
  - `django_strawberry_framework/orders/factories.py::OrderArgumentsFactory` (orders/factories.py:31-174) — **already shipped in Slice 2.** Slice 3's materialize subpass calls `OrderArgumentsFactory(orderset_cls).arguments` (the property triggers `_ensure_built` per orders/factories.py:103-113) then iterates `factory.input_object_types.items()` and calls `materialize_input_class(name, input_cls)` for each. The exact call shape matches the filter side's subpass 4 at finalizer.py:614-622 verbatim.

- **New helpers justified (five new finalizer-side helpers; one new validator).** The five new helpers in `types/finalizer.py` are all sibling formatters / binding shapes mirroring the filter side; none can be consolidated into one because each carries subsystem-specific wording (`FilterSet`/`filter_input_type` vs `OrderSet`/`order_input_type`). Worker 1's planning-pass DRY review concluded the wording-divergence weighs against a shared formatter — the consumer-visible error names the relevant subsystem so a future maintainer reading the error knows which sidecar is broken. The one new validator helper (`_validate_orderset_class`) is the single canonical place where the local-import-against-cycle contract lives; same justification as the shipped `_validate_filterset_class`.
  - `types/finalizer.py::_bind_orderset_owner(orderset_cls, definition) -> None` — per-orderset binding. Single responsibility: enforce first-bind model compatibility + Axis-2 related-target agreement (multi-owner reuse) + idempotent re-bind. Does NOT enforce Axis-1 own-PK Relay-identity (Spec Decision 6 explicit rationale: not an owner-dependent axis on the order side).
  - `types/finalizer.py::_bind_ordersets() -> None` — the umbrella four-subpass helper. Single responsibility: run the four subpasses in the **shipped order** (bind → expand → orphan-validate → materialize) for every wired orderset.
  - `types/finalizer.py::_format_owner_orderset_model_mismatch_error(orderset_cls, owner) -> str` — first-bind model mismatch error. Single responsibility: name all four entities (owner type, owner model, orderset class, orderset model) per Spec Decision 6 / H2 of rev3.
  - `types/finalizer.py::_format_owner_ordersets_mismatch_error(orderset_cls, previous, new, field_name, prev_target, new_target) -> str` — diverging-target multi-owner reuse error. Single responsibility: name both owners + offending field + both resolved target type names.
  - `types/finalizer.py::_format_orphan_ordersets_error(orphans) -> str` — orphan `order_input_type` reference error. Single responsibility: single-orphan vs multi-orphan branching per the filter side's pattern; suggestion text mentions `Meta.orderset_class` so consumers see the fix.
  - `types/base.py::_validate_orderset_class(meta, orderset_class) -> type | None` — `Meta.orderset_class` validator. Single responsibility: short-circuit when absent, raise `ConfigurationError` for non-`OrderSet` values, return the class otherwise. **Local in-function import** of `OrderSet` is the load-bearing contract.

- **Duplication risk avoided (four risks named explicitly).**
  - **Risk: copy-paste the entire `_bind_filtersets` body into `_bind_ordersets`.** Naive implementation would duplicate the ~120-line body (finalizer.py:503-622) into `_bind_ordersets`, silently bifurcating the four-subpass discipline the first time a maintainer fixes one (e.g., adds a fifth subpass) and forgets the other. **Avoidance:** Slice 3's `_bind_ordersets` IS a structural mirror — same subpass discipline, same `ImportError`-rewrap shape, same `repr(exc)` + `from exc` cause-preservation, same `wired_set = set(wired)` orphan-set construction, same `factory = OrderArgumentsFactory(orderset_cls); _ = factory.arguments; for name, input_cls in factory.input_object_types.items(): materialize_input_class(name, input_cls)` materialize loop. The duplication is in shape only (the body is shorter — no Axis-1 own-PK check in `_bind_orderset_owner`); no `from ..filters.finalizer import _bind_filtersets` import or shared helper is justified — the filter side's helper is keyed on `FilterSet` / `filter_input_type` / `_helper_referenced_filtersets` / `FilterArgumentsFactory`, none of which are type-compatible with the order-side equivalents. Worker 3 should flag any divergence from the filter side's subpass ordering as a High finding.
  - **Risk: re-ordering the four subpasses (e.g., materialize before orphan-validate).** Naive implementation might follow the spec-027 rev8 H1 prescription (which inverted subpasses 3 and 4) instead of the shipped filter side's order. **Avoidance:** Spec Decision 6 explicit pin: "the shipped filter side at `django_strawberry_framework/types/finalizer.py::_bind_filtersets` documents this rationale explicitly in its docstring (subpass 3 — orphan validation); this card mirrors the shipped order, not the spec-027 rev8 H1 prescription which inverted subpasses 3 and 4." Per Spec B1 of rev2 ("the **shipped** filter side at `_bind_filtersets` is the authoritative shape") — bind → expand → orphan-validate → materialize, in that order. Worker 3 should flag any deviation as a High finding.
  - **Risk: hoisting `from ..orders.sets import OrderSet` to module top of `types/base.py`.** Naive implementation would add `from ..orders.sets import OrderSet` at the top of `types/base.py` for the validator, mirroring the existing imports. **Avoidance:** Spec N3 of rev1 + DoD item 9 explicit: the import MUST be local-in-function inside `_validate_orderset_class`. The filter side at base.py:99 already demonstrates the pattern (`# In-function import: dodges the 'types -> filters -> types' module-load cycle. Do NOT hoist to module top.`). The cycle: `types/base.py` imports `..registry` → `registry.py` does NOT import `types` at module top (uses TYPE_CHECKING) → BUT `orders/sets.py` imports `from ..types.definition import DjangoTypeDefinition` under TYPE_CHECKING; `orders/factories.py` does NOT import types at module top. The dodge is defensive: Worker 1 verified the cycle is structurally inert today, but the local import keeps the contract robust against any future `orders/*` module growing a top-level `from ..types import ...` line. **Worker 3 MUST flag any top-level `from ..orders.sets import OrderSet` in `types/base.py` as a High finding** — pinned by `test_validate_orderset_class_uses_local_import`.
  - **Risk: collapsing `clear_order_input_namespace()` and `_helper_referenced_ordersets.clear()` into a single `registry.clear()` block.** Naive implementation might bundle both clears under one `try: from .orders import clear_order_input_namespace, _helper_referenced_ordersets` import block. **Avoidance:** Spec Decision 9 line 775 + the prompt's Slice 2 carry-forward both pin: TWO separate `try / except ImportError / else` blocks — block 1 for `clear_order_input_namespace`, block 2 for `_helper_referenced_ordersets.clear()`. The two-block layout matches the filter side at registry.py:420-432 verbatim. Each block uses the `except ImportError: pass` + `else:` shape so a partial-load environment never short-circuits a later cleanup phase (per Spec B2 of rev1 + M-core-4 of rev1 — a future fifth phase, e.g., aggregates 0.1.3, must not be silently skipped). Worker 3 should flag any single-block collapse as a High finding.

- **`scripts/review_inspect.py` planning-time disposition (record per `BUILD.md`).** Ran the helper on the **current** files Slice 3 will modify on 2026-06-01: `types/base.py` (952 lines), `types/definition.py` (194 lines), `types/finalizer.py` (622 lines), `registry.py` (445 lines). All four are over the 150-line trigger AND under `types/` (which fires the second helper-trigger condition); the helper run is required.
  - **`types/base.py` shadow scan.** Three hotspots already pre-Slice-3: `DjangoType.__init_subclass__` (>100 lines), `_validate_meta` (~85 lines), `_build_annotations` (~140 lines). Slice 3 ADDS one ~20-line `_validate_orderset_class` function + 3 small line edits (the `DEFERRED_META_KEYS` / `ALLOWED_META_KEYS` set membership flip, the `_validate_meta` call addition, the `_ValidatedMeta` field addition, the `DjangoTypeDefinition(...)` argument addition). Repeated string literals in the current shadow: `"optimizer_hints"` (4x), `"description"` (2x), `"filterset_class"` (2x), `"interfaces"` (2x). Slice 3 adds `"orderset_class"` references (2x — in the validator + in the `_validate_meta` call). Not a consolidation candidate; the filter side's pattern is to have `Meta.<key>` as repeated string literal across validator + dispatcher.
  - **`types/definition.py` shadow scan.** No control-flow hotspots; zero repeated string literals. Slice 3 ADDs one slot line (`orderset_class: type | None = None`) + one docstring bullet update. Worker 3's review-time trigger fires (file is under `types/`).
  - **`types/finalizer.py` shadow scan.** Three control-flow hotspots: `finalize_django_types` (131 lines, 15 branches), `_bind_filterset_owner` (107 lines, 15 branches), `_bind_filtersets` (120 lines, 11 branches). Slice 3 ADDs five new helpers (`_bind_orderset_owner`, `_bind_ordersets`, `_format_owner_orderset_model_mismatch_error`, `_format_owner_ordersets_mismatch_error`, `_format_orphan_ordersets_error`) plus a one-line `_bind_ordersets()` call in `finalize_django_types`. Estimated post-Slice-3 line count: ~800 source lines, ~6 control-flow hotspots. Repeated string literals to watch for cross-file dup at integration pass: `"FilterSet"` (3x) and `"Cannot finalize Django types: filterset"` (2x) — Slice 3 will add the parallel `"OrderSet"` and `"Cannot finalize Django types: orderset"` strings. These are subsystem-noun strings (NOT shared-formatter candidates) per the wording-divergence rationale above.
  - **`registry.py` shadow scan.** Zero repeated string literals; the helper found no control-flow hotspots. Slice 3 ADDS ~14 lines (two new try/except/else blocks) at the bottom of `TypeRegistry.clear`. The `from .orders.inputs import ...` and `from .orders import ...` lines are new but mirror the existing `from .filters.inputs import ...` and `from .filters import ...` lines at registry.py:421 + 428 verbatim.
  - **Cross-file repeated-literal observation.** Comparing the `Repeated string literals` sections across the four shadows: the shared symbols at integration pass to watch for are (a) `"filterset_class"` and the future `"orderset_class"` appearing in BOTH `types/base.py` AND `types/definition.py` AND `types/finalizer.py` — these are NOT consolidation candidates (each is a slot / dict-key reference, not a free-form literal); (b) `"Cannot finalize Django types: filterset"` in `types/finalizer.py` (and the future `"Cannot finalize Django types: orderset"`) — both subsystem-noun-specific, NOT a consolidation candidate. Worker 1's integration-pass DRY scan must walk these explicitly; the planning-pass disposition is "no new cross-file dups introduced; the existing subsystem-noun strings stay legible by intent."

### Implementation steps

Slice 3 lands two responsibilities across FOUR existing files (`types/base.py`, `types/definition.py`, `types/finalizer.py`, `registry.py`). The order subsystem (orders/__init__.py, orders/base.py, orders/sets.py, orders/factories.py, orders/inputs.py) is ALREADY SHIPPED in Slices 1 + 2 — Slice 3 only consumes its surface. Line anchors below are pin-at-write-time hints per `BUILD.md` Implementation steps note; Worker 2 verifies against the live source before editing.

1. **Edit `django_strawberry_framework/types/definition.py`.** Single new dataclass slot + a docstring bullet update.
   - **Add `orderset_class: type | None = None`** at the line currently parked by the TODO anchor at definition.py:92-98. Place it IMMEDIATELY AFTER the existing `filterset_class: type | None = None` at definition.py:91, BEFORE `finalized: bool = False` at definition.py:99 — the alphabetic-by-subsystem ordering (filter → order) keeps both subsystems' slots adjacent for the integration pass's sibling-compare convenience.
   - **Update the class docstring** (definition.py:38-69) to include an `orderset_class` bullet immediately after the `filterset_class` bullet at definition.py:49-56. Suggested text: `"`orderset_class` is the per-owner `OrderSet` sidecar populated by `DjangoType.__init_subclass__` from `Meta.orderset_class` once promoted out of `DEFERRED_META_KEYS`; consumed by `finalize_django_types()` phase 2.5 to bind the owning `DjangoTypeDefinition` on the OrderSet and to materialize the generated Strawberry input class as a module global of `django_strawberry_framework.orders.inputs`."` The existing TODO anchor at definition.py:57-61 (which currently parks "spec-028 Slice 3 as the ordering sidecar mirror") is FULLY consumed by the bullet update; remove the TODO anchor.
   - **Remove the TODO anchor at definition.py:92-98** (the multi-line block that names spec-028 Slice 3) once the slot lands.

2. **Edit `django_strawberry_framework/types/base.py`.** Five surgical edits across the file.
   - **Drop `"orderset_class"` from `DEFERRED_META_KEYS`** at base.py:48-55. The frozenset shrinks from four members to three: `{"aggregate_class", "fields_class", "search_fields"}`.
   - **Add `"orderset_class"` to `ALLOWED_META_KEYS`** at base.py:57-69. Alphabetic insertion — between `"optimizer_hints"` (current line 66) and `"primary"` (current line 67). The frozenset grows from nine members to ten.
   - **Add `_validate_orderset_class(meta, orderset_class)` function** at the current location of the TODO anchor at base.py:109-116 (immediately after `_validate_filterset_class` at base.py:83-106). Body mirrors `_validate_filterset_class` one-for-one:
     ```python
     def _validate_orderset_class(meta: type, orderset_class: Any) -> type | None:
         """Validate ``Meta.orderset_class`` is a package-``OrderSet`` subclass.

         Local import of ``OrderSet`` at function scope keeps ``types/base.py``
         free of a module-load cycle through ``orders.sets`` (which imports
         ``..types.definition`` under ``TYPE_CHECKING`` and would close the
         cycle at module-load time if the import were hoisted to module
         scope). Validation runs at ``_validate_meta`` time — well after
         both modules have completed module load — so the local import
         resolves cheaply.

         Returns ``None`` when the meta does not declare ``orderset_class``;
         raises ``ConfigurationError`` for non-``OrderSet`` values.
         """
         if orderset_class is None:
             return None
         # In-function import: dodges the `types -> orders -> types` module-load
         # cycle. Do NOT hoist to module top.
         from ..orders.sets import OrderSet

         if not (isinstance(orderset_class, type) and issubclass(orderset_class, OrderSet)):
             raise ConfigurationError(
                 f"{meta.model.__name__}.Meta.orderset_class must be an OrderSet subclass; "
                 f"got {orderset_class!r}",
             )
         return orderset_class
     ```
     The local import is the load-bearing line — Worker 3 MUST flag any module-top hoist as a High finding (pinned by the test `test_validate_orderset_class_uses_local_import`). Remove the TODO anchor at base.py:109-116 once the function lands.
   - **Grow `_ValidatedMeta` NamedTuple** at base.py:571-590. Add `orderset_class: type | None` immediately AFTER `filterset_class: type | None` at base.py:586. Remove the TODO anchor at base.py:587-590.
   - **Update `_validate_meta`** at base.py:593-679. (a) Add `orderset_class = _validate_orderset_class(meta, getattr(meta, "orderset_class", None))` immediately after the existing `filterset_class = _validate_filterset_class(...)` call at base.py:665. (b) Include `orderset_class=orderset_class` in the `_ValidatedMeta(...)` constructor at base.py:670-679 (immediately after `filterset_class=filterset_class,`). Remove the TODO anchor at base.py:666-668 AND base.py:677-678.
   - **Update `DjangoType.__init_subclass__`** at base.py:281-303. Add `orderset_class=validated.orderset_class,` to the `DjangoTypeDefinition(...)` constructor immediately after `filterset_class=validated.filterset_class,` at base.py:299. Remove the TODO anchor at base.py:300-302.
   - **Remove the file-level TODO anchor at base.py:71-80** — the multi-line block naming "spec-028-orders-0_0_8 Slice 3: Promote `Meta.orderset_class`" is fully consumed by the four edits above. Worker 2 keeps the docstring at base.py:1-26 unchanged.

3. **Edit `django_strawberry_framework/types/finalizer.py`.** Five new helpers + one call-site addition + cleanup of the existing TODO anchors.
   - **Add `_format_owner_orderset_model_mismatch_error(orderset_cls, owner)`** at the current location of the TODO anchor at finalizer.py:487-500 (immediately after `_format_orphan_filtersets_error` at finalizer.py:462-484). Body mirrors `_format_owner_model_mismatch_error` at finalizer.py:440-459 with the substitutions `filterset_cls`→`orderset_cls`, `FilterSet`→`OrderSet`, `Meta.filterset_class`→`Meta.orderset_class`. The message MUST name all four entities (owner type, owner model, orderset class, orderset model) per Spec Decision 6's `test_phase_2_5_rejects_orderset_wired_to_unrelated_owner_model` contract.
   - **Add `_format_owner_ordersets_mismatch_error(orderset_cls, previous, new, field_name, prev_target, new_target)`** immediately after the model-mismatch formatter. Body mirrors `_format_owner_mismatch_error` at finalizer.py:387-412 with the same substitutions. Drives the Axis-2 related-target-agreement raise from `_bind_orderset_owner`. Suggested wording: `"OrderSet {orderset_cls.__qualname__} cannot bind to multiple owners with diverging targets: ..."`.
   - **Add `_format_orphan_ordersets_error(orphans)`** immediately after the previous formatter. Body mirrors `_format_orphan_filtersets_error` at finalizer.py:462-484 with `FilterSet`→`OrderSet`, `filter_input_type`→`order_input_type`, `Meta.filterset_class`→`Meta.orderset_class`. Same single-orphan vs multi-orphan branching shape. Per Spec Decision 6 + the spec's `test_orphan_order_input_type_reference_raises_at_finalize` contract (spec line 1012), the single-orphan message must include the suggestion `"Add 'orderset_class = <Name>' to the relevant DjangoType's Meta."`.
   - **Add `_bind_orderset_owner(orderset_cls, definition)`** as a sibling of `_bind_filterset_owner` at finalizer.py:278-384. Body shape (per Spec Decision 6 + Spec Revision 4 H2):
     ```python
     def _bind_orderset_owner(orderset_cls: type, definition: DjangoTypeDefinition) -> None:
         """Bind ``orderset_cls._owner_definition`` with first-bind / related-target / idempotency checks.

         First binding writes ``orderset_cls._owner_definition = definition``
         and returns. Re-binding the same ``(orderset_cls, definition)``
         pair is idempotent (supports partial-finalize recovery per
         spec-028 Decision 6 line 3). A second, distinct owner triggers
         the Axis-2 related-target-agreement check across every declared
         ``RelatedOrder``.

         Per spec-028 Decision 6 second-paragraph rationale, the order
         side does NOT enforce the filter side's Axis-1 own-PK Relay-
         identity check — ``ORDER BY id`` against any model uses the
         column, not the GraphQL ID type, so own-PK identity is not an
         owner-dependent axis here.
         """
         previous: DjangoTypeDefinition | None = getattr(orderset_cls, "_owner_definition", None)
         if previous is None:
             # First binding — reject orderset Meta.model unrelated to owner model.
             orderset_model = getattr(getattr(orderset_cls, "Meta", None), "model", None)
             if (
                 orderset_model is not None
                 and definition.model is not None
                 and not issubclass(definition.model, orderset_model)
             ):
                 raise ConfigurationError(
                     _format_owner_orderset_model_mismatch_error(orderset_cls, definition),
                 )
             orderset_cls._owner_definition = definition
             return
         if previous is definition:
             return
         # Axis 2 — declared related-order targets must agree.
         related_orders = getattr(orderset_cls, "related_orders", {}) or {}
         for field_name in related_orders:
             prev_target = previous.related_target_for(field_name)
             new_target = definition.related_target_for(field_name)
             if prev_target is None and new_target is None:
                 continue
             if prev_target is None or new_target is None:
                 raise ConfigurationError(
                     _format_owner_ordersets_mismatch_error(
                         orderset_cls, previous, definition, field_name, prev_target, new_target,
                     ),
                 )
             prev_definition, _ = prev_target
             new_definition, _ = new_target
             if (
                 prev_definition is not new_definition
                 or prev_definition.graphql_type_name != new_definition.graphql_type_name
             ):
                 raise ConfigurationError(
                     _format_owner_ordersets_mismatch_error(
                         orderset_cls, previous, definition, field_name, prev_target, new_target,
                     ),
                 )
     ```
     The filter side's first-bind branch checks `filterset_cls._meta.model` against `definition.model`; the order side checks `getattr(orderset_cls.Meta, "model", None)` — `OrderSet` doesn't carry a `BaseFilterSet`-style `_meta` aggregator, so the access path is one indirection longer. The `issubclass(definition.model, orderset_model)` check is identical (proxy / multi-table-inheritance children pass).
   - **Add `_bind_ordersets()`** as a sibling of `_bind_filtersets` at finalizer.py:503-622. Body shape (per Spec Decision 6 + Spec B1 of rev2 — bind → expand → orphan-validate → materialize):
     ```python
     def _bind_ordersets() -> None:
         """Run the four ordered phase-2.5 subpasses for orderset binding.

         Subpass 1 — bind every owner. Walks every wired definition and
         binds ``orderset_cls._owner_definition`` via
         ``_bind_orderset_owner``. The first-bind model-compat check and
         the Axis-2 related-target-agreement check reject mis-wired
         orderset_class assignments before any subsequent subpass runs.

         Subpass 2 — expand every orderset. Calls
         ``orderset_cls.get_fields()`` so Layer-4 expansion resolves lazy
         ``RelatedOrder`` refs and cycle guards apply uniformly.
         ``ImportError`` from
         ``LazyRelatedClassMixin.resolve_lazy_class`` is rewrapped as
         ``ConfigurationError`` with ``__cause__`` preserving the
         original. Any other exception rewraps as ``ConfigurationError``
         with ``repr(exc)`` keeping the original class + args in the
         consumer-visible message (uniform finalize-time error shape).

         Subpass 3 — orphan validation. Compares the OrderSets passed to
         ``order_input_type(...)`` (per Decision 11) against the set of
         OrderSets wired via ``Meta.orderset_class``. Orphans raise
         ``ConfigurationError`` with the actionable suggestion to add the
         missing ``orderset_class = <Name>``. Runs BEFORE materialization
         so an orphan failure leaves no partial state in
         ``_materialized_names`` /
         ``OrderArgumentsFactory.input_object_types``; otherwise a re-run
         of ``finalize_django_types()`` after fixing the orphan would see
         stale ledger entries from the prior failed attempt (per spec-028
         Decision 6 + Spec B1 of rev2 — the **shipped** filter side's
         ordering is authoritative).

         Subpass 4 — materialize input classes. Reads
         ``OrderArgumentsFactory(orderset_cls).arguments`` to trigger the
         BFS build (idempotent through the factory's class-level cache),
         then materializes EVERY built class from the factory's
         ``input_object_types`` ledger as a real module global of
         ``orders.inputs`` via ``materialize_input_class(name, cls)``.
         """
         # Local imports: keep `types/finalizer.py` independent of the
         # orders package's module-load order. The phase-2.5 binding only
         # runs when a definition declares `orderset_class`, which only
         # works when the orders subsystem has been imported by the
         # consumer.
         from ..orders import _helper_referenced_ordersets
         from ..orders.factories import OrderArgumentsFactory
         from ..orders.inputs import materialize_input_class

         # Subpass 1: bind every owner before any expansion runs.
         wired: list[type] = []
         for _type_cls, definition in registry.iter_definitions():
             if definition.finalized:
                 continue
             orderset_cls = definition.orderset_class
             if orderset_cls is None:
                 continue
             _bind_orderset_owner(orderset_cls, definition)
             wired.append(orderset_cls)

         # Subpass 2: expand every orderset; cross-references now resolve.
         for orderset_cls in wired:
             try:
                 orderset_cls.get_fields()
             except ImportError as exc:
                 raise ConfigurationError(
                     f"Cannot finalize Django types: orderset "
                     f"{orderset_cls.__qualname__} references an unresolved "
                     f"related-order target. {exc}",
                 ) from exc
             except ConfigurationError:
                 raise
             except Exception as exc:
                 raise ConfigurationError(
                     f"Cannot finalize Django types: orderset "
                     f"{orderset_cls.__qualname__} raised during expansion. {exc!r}",
                 ) from exc

         # Subpass 3: orphan validation against the helper-tracked set.
         # Runs BEFORE materialization so a failure here doesn't leave
         # half-materialized input classes in the inputs-module namespace.
         wired_set = set(wired)
         orphans = sorted(
             _helper_referenced_ordersets - wired_set,
             key=lambda cls: f"{cls.__module__}.{cls.__qualname__}",
         )
         if orphans:
             raise ConfigurationError(_format_orphan_ordersets_error(orphans))

         # Subpass 4: materialize every built input class as a module global.
         for orderset_cls in wired:
             factory = OrderArgumentsFactory(orderset_cls)
             _ = factory.arguments  # triggers _ensure_built (idempotent)
             for name, input_cls in factory.input_object_types.items():
                 materialize_input_class(name, input_cls)
     ```
     **The four-subpass order is verbatim from the shipped filter side at finalizer.py:548-622 (bind → expand → orphan-validate → materialize)** per Spec B1 of rev2 — Worker 2 MUST NOT reorder.
   - **Add the `_bind_ordersets()` call inside `finalize_django_types()`** at finalizer.py:260 (immediately after `_bind_filtersets()` at finalizer.py:259). Body change:
     ```python
     _bind_filtersets()
     _bind_ordersets()  # spec-028 Slice 3 — order-side phase-2.5 binding
     ```
     Remove the TODO anchor at finalizer.py:260-267 (the multi-line `_bind_ordersets()` pseudocode block).
   - **Remove the file-level TODO anchor at finalizer.py:487-500** (the multi-line block naming the order-side helpers) once the helpers land.

4. **Edit `django_strawberry_framework/registry.py`.** Two new try/except/else blocks at the bottom of `TypeRegistry.clear`.
   - **Add the order-input namespace clear block** at registry.py:434 (currently a TODO anchor at registry.py:434-442). Body:
     ```python
     try:
         from .orders.inputs import clear_order_input_namespace
     except ImportError:
         pass
     else:
         clear_order_input_namespace()
     ```
     Placement: immediately after the existing `_helper_referenced_filtersets.clear()` block at registry.py:427-432.
   - **Add the helper-orphan-tracking clear block** immediately after the namespace clear:
     ```python
     try:
         from .orders import _helper_referenced_ordersets
     except ImportError:
         pass
     else:
         _helper_referenced_ordersets.clear()
     ```
     **TWO separate try/except blocks** per Spec Decision 9 line 775 + the prompt — NOT collapsed into one. Both use `except ImportError: pass` + `else:` per Spec B2 of rev1 / M-core-4 of rev1 — never `return` on the last block.
   - **Remove the TODO anchor at registry.py:434-442** (the multi-line block parking the work).
   - **Field-name verification.** Worker 2 MUST verify the existing model-state clears at registry.py:404-410 use the verbatim shipped names `self._types.clear()`, `self._primaries.clear()`, `self._models.clear()`, `self._enums.clear()`, `self._definitions.clear()`, `self._pending.clear()`, `self._finalized = False` — these are the **correct** names per `TypeRegistry.__init__` at registry.py:44-50 and per Spec B2+B3 of rev2 + the prompt's "Use the actual `_types` / `_primaries` / `_models` / `_enums` / `_definitions` / `_pending` / `_finalized` field names". The phantom `_types_by_model` / `_primary_types` names from rev1 of the spec body's code block were errors and MUST NOT be re-introduced. Slice 3 does NOT touch the model-state clear lines — but Worker 2 verifies them as a guard against accidental drift while editing the surrounding context.

5. **Run `uv run ruff format .` and `uv run ruff check --fix .` as the apply-changes step closes.** Standard close per `AGENTS.md` #"Run uv run ruff format . and uv run ruff check --fix . after every edit". Worker 2's build report records the `git status --short` after both ruff invocations and classifies every modified path as slice-intended or reverted-tool-churn per `docs/builder/BUILD.md` #"### Validation run".

6. **Verify against the shipped filter subsystem before pinning final layouts.** Per the build-plan's "Filter subsystem is shipped" rule — Worker 2 reads:
   - `django_strawberry_framework/types/base.py::_validate_filterset_class` (base.py:83-106) — for the `_validate_orderset_class` body shape + local-import contract.
   - `django_strawberry_framework/types/finalizer.py::_bind_filterset_owner` (finalizer.py:278-384) — for the first-bind / idempotent / multi-owner reject shape; Slice 3 ports this shape minus Axis-1 per Spec Decision 6.
   - `django_strawberry_framework/types/finalizer.py::_bind_filtersets` (finalizer.py:503-622) — for the four-subpass discipline (bind → expand → orphan-validate → materialize). Worker 2 MUST verify the subpass order against this body BEFORE writing `_bind_ordersets()`.
   - `django_strawberry_framework/registry.py::TypeRegistry.clear` (registry.py:395-442) — for the two-block try/except/else shape + the `pass` + `else:` rule.
   Every divergence from these shipped shapes is a Worker 3 finding per the build-plan's "every divergence is a finding" rule. The known intentional divergence (the only one) is `_bind_orderset_owner` SKIPPING the Axis-1 own-PK Relay-identity check — Spec Decision 6 second paragraph licenses this; Worker 2 records the divergence in the build report's `### Implementation notes` so Worker 3 doesn't flag it as drift.

### Test additions / updates

Slice 3 lands one fully-new test file (`tests/orders/test_finalizer.py` — currently a TODO-anchored 16-line stub) plus appends to two existing test files (`tests/orders/test_inputs.py` for the `registry.clear()` integration, and either `tests/orders/test_base.py` or a new `tests/orders/test_wiring.py` for the `Meta.orderset_class` `ALLOWED_META_KEYS` / `DEFERRED_META_KEYS` membership tests). Plus extends `tests/types/test_base.py` for the promotion test pinned by Spec Decision 7.

The test files below pin contract checks Slice 3 must satisfy. Each bullet names a `path::test_name` shape so Worker 3 can walk the diff against the planned set without ambiguity.

- **`tests/orders/test_finalizer.py`** — replace the TODO-anchored 16-line stub at lines 1-16 with real test bodies covering Spec Slice 3 bullets 3 + 4 + Spec Decision 6 + Spec Decision 9 / lifecycle:
  - `test_meta_orderset_class_accepts_order_set_subclass` — declare a `BookType(DjangoType)` with `Meta.model = Book` AND `Meta.orderset_class = BookOrder`; assert `BookType.__django_strawberry_definition__.orderset_class is BookOrder` (the promotion gate accepts a valid `OrderSet`). Pins the Slice 3 sub-bullet 1 + 2 contract jointly.
  - `test_meta_orderset_class_rejects_non_order_set` — declare a class `NotAnOrderSet` (plain Python class, no `OrderSet` MRO); attempt `class BookType(DjangoType): class Meta: model = Book; orderset_class = NotAnOrderSet`; assert `ConfigurationError` raised at class-creation time with `"OrderSet subclass"` in the message AND the bad value's `repr` in the message. Pins `_validate_orderset_class`'s contract.
  - `test_validate_orderset_class_uses_local_import` — assert `OrderSet` is NOT in `django_strawberry_framework.types.base.__dict__` (the module-top namespace) AND the `_validate_orderset_class` function source contains the `from ..orders.sets import OrderSet` line. Two-part assertion pins the local-import-against-cycle contract per Spec N3 of rev1 + DoD item 9. Suggested implementation: `import inspect; src = inspect.getsource(_validate_orderset_class); assert "from ..orders.sets import OrderSet" in src` AND `import django_strawberry_framework.types.base as base_mod; assert "OrderSet" not in vars(base_mod)`.
  - `test_phase_2_5_binds_all_owners_before_expansion` (per Spec line 1012) — declare `BookType` (with `orderset_class = BookOrder`) AND `ShelfType` (with `orderset_class = ShelfOrder`) where `BookOrder.shelf = RelatedOrder("ShelfOrder", field_name="shelf")`; arrange the registry so `BookType` is iterated FIRST; instrument `ShelfOrder` via a monkeypatched `get_fields` classmethod or a sentinel hook that records whether `ShelfOrder._owner_definition is not None` at the moment `BookOrder.get_fields()` triggers the `RelatedOrder` resolution; run `finalize_django_types()`; assert the hook records `_owner_definition is not None` (i.e., `ShelfOrder` was bound BEFORE the expansion that triggered it). Pins Subpass-1-before-Subpass-2 ordering.
  - `test_phase_2_5_unresolved_related_order_raises_at_finalize` — declare `BookType` with `orderset_class = BookOrder` where `BookOrder.shelf = RelatedOrder("NonExistentOrder", field_name="shelf")` (string target that won't resolve); call `finalize_django_types()`; assert `ConfigurationError` raised with `"Cannot finalize Django types: orderset"` in the message AND `__cause__` is the underlying `ImportError`. Pins Subpass-2 `ImportError`-rewrap shape per Spec Decision 6 subpass 2.
  - `test_phase_2_5_non_import_get_fields_failure_rewraps_as_configuration_error` — declare `BookType` with `orderset_class = BookOrder` where `BookOrder.Meta.fields` references an unknown field name; call `finalize_django_types()`; assert `ConfigurationError` raised with `"raised during expansion"` in the message AND `__cause__` preserves the underlying exception. Pins Subpass-2 uniform-error-shape contract.
  - `test_phase_2_5_orphan_check_runs_before_materialization` (Subpass-3-before-Subpass-4 ordering) — declare `BookType` with `orderset_class = BookOrder` AND a separate `StandaloneOrder` (an `OrderSet` subclass) referenced via `order_input_type(StandaloneOrder)` on a sentinel resolver but NOT wired to any `DjangoType.Meta.orderset_class`; call `finalize_django_types()`; assert `ConfigurationError` raised with `"StandaloneOrder"` in the message AND the suggestion text `"Add 'orderset_class = StandaloneOrder' to the relevant DjangoType's Meta"`; AFTER the raise, assert `"StandaloneOrderInputType" not in django_strawberry_framework.orders.inputs._materialized_names` AND `"BookOrderInputType" not in OrderArgumentsFactory.input_object_types` (no half-materialized state left behind by the orphan failure). Pins the "orphan-before-materialize" contract per Spec B1 of rev2.
  - `test_orphan_order_input_type_reference_raises_at_finalize` (Spec line 1012) — single-orphan case. Declare a `StandaloneOrder` referenced via `order_input_type(StandaloneOrder)` on a root resolver but never assigned to any `DjangoType` via `Meta.orderset_class`; runs `finalize_django_types()`; asserts `ConfigurationError` with `"StandaloneOrder"` in the message AND the suggestion-text about wiring `Meta.orderset_class`.
  - `test_phase_2_5_orphan_validation_lists_every_orphan_orderset` — multi-orphan case. Declare TWO orphan `OrderSet`s `OrphanA` and `OrphanB`, both referenced via `order_input_type(...)` but neither wired; assert the error message names BOTH `OrphanA` and `OrphanB` AND uses the multi-orphan lead-in shape (`"OrderSets referenced via order_input_type(...) but not wired to any DjangoType:"`). Mirrors `test_phase_2_5_orphan_validation_lists_every_orphan_filterset` from the filter side.
  - `test_phase_2_5_subpass_4_materializes_input_classes_as_module_globals` — declare `BookType` with `orderset_class = BookOrder`; call `finalize_django_types()`; assert `getattr(sys.modules["django_strawberry_framework.orders.inputs"], "BookOrderInputType")` is the built input class AND `"BookOrderInputType" in _materialized_names`. Pins Subpass 4's materialize step.
  - `test_phase_2_5_rejects_orderset_wired_to_unrelated_owner_model` (per Spec H2 of rev3 / Decision 6) — declare `BookOrder(Meta.model=Book)` AND wire it onto `BranchType(Meta.model=Branch)`; run `finalize_django_types()`; assert `ConfigurationError` with ALL FOUR names (owner type `BranchType`, owner model `Branch`, orderset class `BookOrder`, orderset model `Book`) in the message. The H2-of-rev3 mandatory test.
  - `test_bind_orderset_owner_idempotent_for_same_definition` — call `_bind_orderset_owner(BookOrder, book_definition)` twice; assert no raise on the second call AND `BookOrder._owner_definition is book_definition` after both calls. Mirrors the filter side's idempotency test.
  - `test_bind_orderset_owner_rejects_diverging_related_targets` — declare TWO owner definitions for the same `BookOrder` whose `related_target_for("shelf")` resolves to different `DjangoTypeDefinition`s; bind the first; attempt to bind the second; assert `ConfigurationError` with `"diverging targets"` in the message AND both owners + the offending field + both target type names in the message. Axis-2 multi-owner check.
  - `test_bind_orderset_owner_does_not_check_axis_1_relay_identity` (per Spec Decision 6 second paragraph) — declare TWO owner definitions for the same `BookOrder` where one origin is Relay-Node-shaped and the other is not (or they have different `graphql_type_name`); bind both; assert NO raise (the order side does NOT enforce Axis-1 per Spec Decision 6's "the order side has no equivalent — `ORDER BY id` against any model uses the column, not the GraphQL ID type"). Pins the deliberate divergence from the filter side. Mirror of the filter side's `test_bind_filterset_owner_rejects_diverging_own_pk_relay_node_ness` shape but with the **inverse** assertion.
  - `test_finalize_django_types_is_idempotent_after_orderset_wiring` — call `finalize_django_types()` twice; assert the second call is a no-op (no re-materialization, no re-binding, no raise). Pins the `registry.is_finalized()` guard at finalizer.py:182-183 still works with the order-side binding added.
  - `test_phase_2_5_partial_failure_leaves_consistent_namespace` — declare `BookType` with `orderset_class = BookOrder` AND `ShelfType` with `orderset_class = ShelfOrder`; instrument `ShelfOrder.get_fields` to raise `ConfigurationError` AFTER `BookOrder.get_fields()` has completed AND AFTER `BookOrderInputType` has been materialized; assert the `ConfigurationError` propagates; AFTER the raise, assert (a) `BookOrderInputType` is parked in `orders.inputs.__dict__` AND (b) `_materialized_names["BookOrderInputType"]` is consistent (the ledger and the module global agree). Pins Spec Decision 9 "partial-finalize recovery" lifecycle.

- **`tests/orders/test_inputs.py`** — APPEND new tests (per the prompt: "APPEND a test that `registry.clear()` calls `clear_order_input_namespace()`. Verify the lifecycle of the `_helper_referenced_ordersets` clear is via the registry, not direct."):
  - `test_registry_clear_invokes_clear_order_input_namespace` — declare an `OrderSet`, call `materialize_input_class("FakeInputType", FakeCls)` to seed `_materialized_names`; call `registry.clear()`; assert `_materialized_names` is empty AND `OrderArgumentsFactory.input_object_types` is empty AND `OrderArgumentsFactory._type_orderset_registry` is empty. Mirrors the filter side's `test_registry_clear_clears_filter_input_namespace_and_helper_set`.
  - `test_registry_clear_clears_helper_referenced_ordersets` — call `order_input_type(BookOrder)` to seed the ledger; assert `BookOrder in _helper_referenced_ordersets`; call `registry.clear()`; assert `_helper_referenced_ordersets` is empty. Pins the separate-block clear path per Spec Decision 9 line 775.
  - `test_registry_clear_works_without_orders_imported` (subprocess test per Spec line 1012) — use `subprocess.run([sys.executable, "-c", "import django_strawberry_framework.registry; django_strawberry_framework.registry.registry.clear()"], check=False)` (capturing both stdout/stderr); assert `returncode == 0` AND no `ImportError` text in stderr. Pins the import-cycle-safe contract for the new local imports — when only `registry` is imported (not `orders`), the local `from .orders.inputs import clear_order_input_namespace` MUST NOT crash (`except ImportError: pass` branch covers it). Mirrors the filter side's `test_registry_clear_works_without_filters_imported`.

- **`tests/orders/test_base.py`** — APPEND new tests covering `Meta.orderset_class` membership:
  - `test_meta_orderset_class_is_in_allowed_meta_keys` — assert `"orderset_class" in django_strawberry_framework.types.base.ALLOWED_META_KEYS`.
  - `test_meta_orderset_class_is_not_in_deferred_meta_keys` — assert `"orderset_class" not in django_strawberry_framework.types.base.DEFERRED_META_KEYS`. Pins the negation; mirrors the filter side's identical pattern.
  - Worker 2 may alternatively park these two tests in a new file `tests/orders/test_wiring.py` if the file's import surface differs significantly from `test_base.py`; Worker 1's preference is `test_base.py` (the membership tests are about `Meta.orderset_class` acceptance which is the contract `test_base.py` already covers for `RelatedOrder` shape).

- **`tests/types/test_base.py`** — APPEND ONE test per Spec line 1024:
  - `test_meta_orderset_class_is_promoted_to_allowed_meta_keys` — assert `"orderset_class" not in DEFERRED_META_KEYS` AND `"orderset_class" in ALLOWED_META_KEYS`. Pins the "deferred key promoted only when subsystem ships" contract per Decision 7. Mirrors `test_meta_filterset_class_is_promoted_to_allowed_meta_keys` from `DONE-027-0.0.8` verbatim.

The remaining TODO-anchored tests in `tests/orders/test_inputs.py` / `test_factories.py` / `test_sets.py` from earlier slices stay as-is. `tests/orders/test_composition.py` is Slice 6's deliverable per the build-plan's checklist. Slice 4's live HTTP coverage in `examples/fakeshop/test_query/test_library_api.py` is out of scope here.

No temp / scratch tests proposed for Slice 3 — the contract is small enough that the permanent tests above prove it without ad-hoc probes. Worker 3 may add `docs/builder/temp-tests/slice-3/...` probes during review if it wants to test edge cases without polluting the permanent suite; that's Worker 3's discretion.

### Implementation discretion items

The items below are at Worker 2's discretion because Worker 1 has assessed each and concluded the choice is between equally valid shapes, or that the choice is a minor style preference that the spec does not pin.

1. **Where the `Meta.orderset_class` membership tests live** — Worker 1's preference is `tests/orders/test_base.py` (per the Test additions plan above), but `tests/orders/test_wiring.py` (a new file) is equally valid. Worker 2 picks. Both shapes are common across the existing test trees; the filter side parks similar tests in `tests/filters/test_base.py`.
2. **Whether `_bind_orderset_owner` uses `orderset_cls._meta.model` or `getattr(orderset_cls.Meta, "model", None)`** — `OrderSet` does NOT carry a `BaseFilterSet`-style `_meta` aggregator (the cookbook's `AdvancedOrderSet` doesn't either), so the access path is `getattr(orderset_cls.Meta, "model", None)`. Worker 2 may choose to add a one-line `_meta`-shaped property on `OrderSet` if it makes the body cleaner; the planning preference is to keep it as a `getattr` chain at the call site (no `OrderSet` class-body changes — Slice 3 is types-package-scoped).
3. **Inline-or-helper style for the orphan suggestion text** — the suggestion `"Add 'orderset_class = <Name>' to the relevant DjangoType's Meta."` may be inlined in `_format_orphan_ordersets_error` or extracted to a one-line helper. The filter side at finalizer.py:462-484 inlines it; Worker 2 may follow the same pattern or extract if it reads cleaner.
4. **Order of the two `registry.clear()` blocks** — Worker 1's preference is namespace-clear-first (block 1: `clear_order_input_namespace`) then helper-ledger-clear (block 2: `_helper_referenced_ordersets.clear()`), matching the filter side's order at registry.py:420-432. Worker 2 may reverse if a defensive consideration surfaces — both orderings are correct because the two ledgers are independent. The filter side's order is the safer default.
5. **TODO anchor wording cleanup** — Worker 2 removes ALL of these TODO anchors (they are fully consumed by Slice 3):
   - `types/base.py` lines 71-80 (DEFERRED_META_KEYS / ALLOWED_META_KEYS / `_validate_orderset_class` plan)
   - `types/base.py` lines 109-116 (`_validate_orderset_class` mirror-of-filter pseudocode)
   - `types/base.py` lines 300-302 (DjangoTypeDefinition constructor `orderset_class=` param)
   - `types/base.py` lines 587-590 (`_ValidatedMeta.orderset_class` slot)
   - `types/base.py` lines 666-668 (`_validate_meta` call to `_validate_orderset_class`)
   - `types/base.py` lines 677-678 (`_ValidatedMeta(...)` constructor `orderset_class=` arg)
   - `types/definition.py` lines 57-61 (the docstring bullet for `orderset_class`)
   - `types/definition.py` lines 92-98 (the slot itself)
   - `types/finalizer.py` lines 260-267 (the `_bind_ordersets()` call site + the umbrella plan)
   - `types/finalizer.py` lines 487-500 (the order-side helper plans)
   - `registry.py` lines 434-442 (the two `registry.clear()` blocks plan)
   The exact whitespace + comment-block stripping is at Worker 2's discretion; the contract is "every Slice 3 TODO anchor is gone after the slice lands." Worker 3 should flag any surviving Slice 3-named TODO anchor as a Low finding.

Items that are NOT at discretion (escalation triggers if discovered ambiguous):

- The `_validate_orderset_class` helper MUST use a local in-function `from ..orders.sets import OrderSet` import. NOT discretion. Pinned by Spec N3 of rev1 + DoD item 9 + the new test `test_validate_orderset_class_uses_local_import`.
- The four subpasses in `_bind_ordersets` MUST run in the shipped order: bind → expand → orphan-validate → materialize. NOT discretion. Pinned by Spec B1 of rev2 + the shipped filter side.
- The two `registry.clear()` blocks MUST be SEPARATE try/except/else blocks (not collapsed). NOT discretion. Pinned by Spec Decision 9 line 775.
- Both `registry.clear()` blocks MUST use `except ImportError: pass` + `else:` shape (not `return` on the last block). NOT discretion. Pinned by Spec B2 / M-core-4 of rev1.
- The existing TypeRegistry field names `_types` / `_primaries` / `_models` / `_enums` / `_definitions` / `_pending` / `_finalized` are CORRECT. NOT discretion. Pinned by Spec B2+B3 of rev2 + the prompt. Worker 2 MUST NOT re-introduce the phantom `_types_by_model` / `_primary_types` names.

### Spec slice checklist (verbatim)

The four sub-bullets below are copied verbatim from `docs/spec-028-orders-0_0_8.md`'s `## Slice checklist` section, the `- [ ] Slice 3: Wiring` block (spec lines 120-123). Worker 1's final-verification pass ticks each box `- [x]` as the contract lands; an un-ticked box at final verification is either deferred with a one-line reason under `### Spec changes made (Worker 1 only)` or the slice goes `revision-needed`.

- [ ] [`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`][definition] grows an `orderset_class: type | None = None` field. The slot is populated by `DjangoType.__init_subclass__` from `Meta.orderset_class` once the key is promoted out of `DEFERRED_META_KEYS`.
- [ ] [`django_strawberry_framework/types/base.py::DEFERRED_META_KEYS`][base] drops `"orderset_class"`. [`ALLOWED_META_KEYS`][base] grows `"orderset_class"`. A new `_validate_orderset_class(meta, orderset_class)` helper validates the supplied class is an `OrderSet` subclass and raises [`ConfigurationError`][glossary-configurationerror] otherwise (mirrors the shipped [`django_strawberry_framework/types/base.py::_validate_filterset_class`][base] one-for-one). **The helper MUST use a local in-function `from ..orders.sets import OrderSet` import** (per N3 of [`docs/feedback.md`][feedback] rev1 + DoD item 9) — NOT a top-of-file import — to dodge the `types → orders → types` module-load cycle.
- [ ] [`django_strawberry_framework/types/finalizer.py::finalize_django_types`][finalizer] grows a per-type order-binding pass in phase 2.5 (immediately after the existing `_bind_filtersets()` umbrella helper and before phase 3's `strawberry.type` decoration). The pass runs four ordered subpasses mirroring the **shipped** filter binding's discipline (verified at [`django_strawberry_framework/types/finalizer.py::_bind_filtersets`][finalizer]): (1) bind every `OrderSet`'s `_owner_definition` first, no `get_fields()` calls; (2) call `get_fields()` for every wired orderset only after every owner is bound — `ImportError` from unresolved `RelatedOrder("...")` rewraps as [`ConfigurationError`][glossary-configurationerror] with `__cause__` preserved (mirrors the filter side's `ImportError` rewrap); (3) **orphan-validate** `_helper_referenced_ordersets` against the set of wired ordersets — runs BEFORE materialization so an orphan failure leaves no partial state in `_materialized_names` or `OrderArgumentsFactory.input_object_types` (verbatim shape from the shipped filter side, where the same inversion is justified by avoiding stale-ledger entries on a re-run after the consumer fixes the orphan); (4) **materialize** input classes via `OrderArgumentsFactory(orderset_cls).arguments` plus a `materialize_input_class(name, input_cls)` call for every built class. `registry.clear()` invokes `clear_order_input_namespace()` AND clears `_helper_referenced_ordersets` so the model-to-`DjangoType` clear, the order-input clear, and the orphan-tracking clear share one entry point per [Decision 9](#decision-9--input-class-namespace-vs-typeregistry-and-lifecycle).

(Note: the spec's Slice 3 block carries THREE sub-bullets — the `definition.py` slot, the `base.py` validator+promotion, and the `finalizer.py` four-subpass+`registry.clear()` integration. The fourth conceptual contract — `Meta.orderset_class` promotion to `ALLOWED_META_KEYS` — is FOLDED INTO the second sub-bullet, NOT a separate bullet; the sub-bullet's first sentence "`DEFERRED_META_KEYS` drops `"orderset_class"`. `ALLOWED_META_KEYS` grows `"orderset_class"`." encodes the promotion contract.)

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/definition.py` — Added `orderset_class: type | None = None` slot immediately after `filterset_class` on `DjangoTypeDefinition`; replaced the Slice-1 TODO anchor in the class docstring with the parallel `orderset_class` bullet (semantics: populated by `DjangoType.__init_subclass__` from `Meta.orderset_class`, consumed by finalizer phase 2.5). Removed the two TODO anchor blocks named in the plan.
- `django_strawberry_framework/types/base.py` — Dropped `"orderset_class"` from `DEFERRED_META_KEYS`; added `"orderset_class"` (alphabetically between `"optimizer_hints"` and `"primary"`) to `ALLOWED_META_KEYS`. Added `_validate_orderset_class(meta, orderset_class) -> type | None` immediately after `_validate_filterset_class`, with **local in-function** `from ..orders.sets import OrderSet` import per Spec N3 of rev1 + DoD item 9. Grew `_ValidatedMeta` with `orderset_class: type | None`. Threaded `orderset_class = _validate_orderset_class(...)` through `_validate_meta` and the `_ValidatedMeta(...)` constructor. Threaded `orderset_class=validated.orderset_class` through `DjangoType.__init_subclass__`'s `DjangoTypeDefinition(...)` call. Removed all six Slice-3 TODO anchors named in the plan.
- `django_strawberry_framework/types/finalizer.py` — Added five new helpers as siblings of the filter-side helpers: `_bind_orderset_owner(orderset_cls, definition)` (first-bind model compatibility + Axis-2 related-target agreement + idempotent re-bind; SKIPS the filter side's Axis-1 own-PK Relay-identity check per Spec Decision 6 second paragraph); `_format_owner_ordersets_mismatch_error(...)`; `_format_owner_orderset_model_mismatch_error(orderset_cls, owner)` (names all four entities per Spec H2 of rev3); `_format_orphan_ordersets_error(orphans)` (single-orphan / multi-orphan branches mirroring the filter side); `_bind_ordersets()` (four subpasses in shipped order — bind → expand → orphan-validate → materialize). Added the `_bind_ordersets()` call inside `finalize_django_types()` immediately after `_bind_filtersets()`, before Phase 3. Removed the two Slice-3 TODO anchor blocks named in the plan.
- `django_strawberry_framework/registry.py` — Added two new `try/except ImportError: pass / else:` blocks at the bottom of `TypeRegistry.clear`, matching the filter-side two-block layout: block 1 imports `clear_order_input_namespace` from `.orders.inputs` and calls it; block 2 imports `_helper_referenced_ordersets` from `.orders` and clears it. Removed the Slice-3 TODO anchor. Confirmed the existing model-state clear lines use the shipped names (`_types` / `_primaries` / `_models` / `_enums` / `_definitions` / `_pending` / `_finalized`); no edit to those.
- `tests/orders/test_finalizer.py` — Replaced the 16-line TODO stub with 19 real tests covering: `Meta.orderset_class` accepted-vs-rejected + the local-import contract; subpass 1 → subpass 2 ordering; subpass 2 `ImportError` rewrap (with `__cause__` preserved) and non-import rewrap; subpass 3 orphan validation (single + multi + ordering); subpass 3 runs BEFORE subpass 4; subpass 4 materialization; the H2-of-rev3 mandatory `test_phase_2_5_rejects_orderset_wired_to_unrelated_owner_model` (names all four entities); direct `_bind_orderset_owner` branches — idempotent re-bind, diverging related targets, both-None continue, one-resolves-one-doesn't, the Spec-Decision-6-second-paragraph deliberate-divergence Axis-1 non-check, and the first-bind orderset-model-unrelated rejection; `finalize_django_types()` idempotency; Relay-Node cooperation.
- `tests/orders/test_base.py` — Appended six Slice-3 tests: membership of `orderset_class` in `ALLOWED_META_KEYS`; absence from `DEFERRED_META_KEYS`; `_validate_orderset_class` short-circuit on `None`; accepts `OrderSet` subclass; rejects non-`OrderSet` with the four-entity message contract; the local-import contract via `inspect.getsource` probe + module-namespace assertion.
- `tests/orders/test_inputs.py` — Appended three Slice-3 tests: `registry.clear()` invokes `clear_order_input_namespace()` and empties every order-input ledger; `registry.clear()` clears `_helper_referenced_ordersets` via the separate-block path; and a subprocess test that `registry.clear()` runs without `ImportError` when the orders package was never imported (mirrors the filter side's `test_registry_clear_works_without_filters_imported`).
- `tests/types/test_base.py` — Removed `"orderset_class"` from the `test_meta_rejects_each_deferred_key` parametrize list (no longer a deferred key); appended `test_meta_orderset_class_is_promoted_to_allowed_meta_keys` per Spec Decision 7, mirroring the shipped `test_meta_filterset_class_is_promoted_to_allowed_meta_keys`. Removed the slice-3-anchored TODO block.

### Tests added or updated

- `tests/orders/test_finalizer.py::test_meta_orderset_class_accepts_order_set_subclass`
- `tests/orders/test_finalizer.py::test_meta_orderset_class_rejects_non_order_set`
- `tests/orders/test_finalizer.py::test_validate_orderset_class_uses_local_import`
- `tests/orders/test_finalizer.py::test_phase_2_5_binds_all_owners_before_expansion`
- `tests/orders/test_finalizer.py::test_phase_2_5_unresolved_related_order_raises_at_finalize`
- `tests/orders/test_finalizer.py::test_phase_2_5_non_import_get_fields_failure_rewraps_as_configuration_error`
- `tests/orders/test_finalizer.py::test_orphan_order_input_type_reference_raises_at_finalize`
- `tests/orders/test_finalizer.py::test_phase_2_5_orphan_check_runs_before_materialization`
- `tests/orders/test_finalizer.py::test_phase_2_5_orphan_validation_lists_every_orphan_orderset`
- `tests/orders/test_finalizer.py::test_phase_2_5_subpass_4_materializes_input_classes_as_module_globals`
- `tests/orders/test_finalizer.py::test_phase_2_5_rejects_orderset_wired_to_unrelated_owner_model` — the H2-of-rev3 mandatory test.
- `tests/orders/test_finalizer.py::test_bind_orderset_owner_idempotent_for_same_definition`
- `tests/orders/test_finalizer.py::test_bind_orderset_owner_rejects_diverging_related_targets`
- `tests/orders/test_finalizer.py::test_bind_orderset_owner_continues_when_both_targets_unresolved`
- `tests/orders/test_finalizer.py::test_bind_orderset_owner_raises_when_one_owner_resolves_and_other_does_not`
- `tests/orders/test_finalizer.py::test_bind_orderset_owner_does_not_check_axis_1_relay_identity` — pins the Spec Decision 6 second-paragraph deliberate-divergence from the filter side.
- `tests/orders/test_finalizer.py::test_bind_orderset_owner_rejects_orderset_model_unrelated_to_owner`
- `tests/orders/test_finalizer.py::test_finalize_django_types_is_idempotent_after_orderset_wiring`
- `tests/orders/test_finalizer.py::test_phase_2_5_runs_under_relay_node_interface`
- `tests/orders/test_base.py::test_meta_orderset_class_is_in_allowed_meta_keys`
- `tests/orders/test_base.py::test_meta_orderset_class_is_not_in_deferred_meta_keys`
- `tests/orders/test_base.py::test_validate_orderset_class_returns_none_for_missing_value`
- `tests/orders/test_base.py::test_validate_orderset_class_accepts_order_set_subclass`
- `tests/orders/test_base.py::test_validate_orderset_class_rejects_non_order_set`
- `tests/orders/test_base.py::test_validate_orderset_class_uses_local_import`
- `tests/orders/test_inputs.py::test_registry_clear_invokes_clear_order_input_namespace`
- `tests/orders/test_inputs.py::test_registry_clear_clears_helper_referenced_ordersets`
- `tests/orders/test_inputs.py::test_registry_clear_works_without_orders_imported` — subprocess test pinning the cycle-safe contract.
- `tests/types/test_base.py::test_meta_orderset_class_is_promoted_to_allowed_meta_keys` — mirror of the shipped filter-side promotion test.
- `tests/types/test_base.py::test_meta_rejects_each_deferred_key` — updated parametrize list (dropped `"orderset_class"`).

### Validation run

- `uv run ruff format .` — pass; 213 files left unchanged on the final pass.
- `uv run ruff check --fix .` — pass; one round of fixes during development (initial draft used `class model:` inside a fake-meta stub which triggered `N801`; replaced with `model = type("FakeModel", (), {})` so the lint stays clean).
- `git status --short` after both ruff invocations — every modified file classified:
  - **Slice-3 intended (in this diff, listed above):** `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/registry.py`, `tests/orders/test_finalizer.py`, `tests/orders/test_base.py`, `tests/orders/test_inputs.py`, `tests/types/test_base.py`.
  - **Pre-existing from Slices 1 + 2 (carried in the working tree by prior worker passes; not touched here):** `django_strawberry_framework/orders/__init__.py`, `django_strawberry_framework/orders/base.py`, `django_strawberry_framework/orders/factories.py`, `django_strawberry_framework/orders/inputs.py`, `django_strawberry_framework/orders/sets.py`, `tests/orders/test_factories.py`, `tests/orders/test_sets.py`, `docs/spec-028-orders-0_0_8.md`, `docs/builder/bld-slice-1-foundation.md`, `docs/builder/bld-slice-2-factories.md`, `docs/builder/build-028-orders-0_0_8.md`. The build plan's preamble does NOT list these; they are the prior-slice diffs that have not yet been committed.
  - **Baseline-dirty (in the build-plan preamble; NOT touched, NOT reverted):** `TODAY.md`, `django_strawberry_framework/management/commands/export_schema.py`, `django_strawberry_framework/optimizer/_context.py`, `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/optimizer/field_meta.py`, `django_strawberry_framework/optimizer/hints.py`, `django_strawberry_framework/optimizer/plans.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/testing/_wrap.py`, `docs/GLOSSARY.md`, `docs/GLOSSARY2.md`, `docs/TREE.md`, `docs/builder/build-021-filters-0_0_8.md` (deleted by pre-flight), `docs/review/rev-*.md` (multiple), `docs/review/review-0_0_7.md`, `examples/fakeshop/*` (all), `scripts/build_glossary_md.py`, `scripts/build_kanban_html.py`, `scripts/build_kanban_md.py`, `scripts/check_spec_glossary.py`, `scripts/import_glossary_md.py`, `tests/optimizer/test_walker.py`.
  - **No tool churn introduced by this pass.** Ruff format reported "213 files left unchanged" on the final pass after the one early `N801` fix.
- Focused tests run (no `--cov*` flags, per `AGENTS.md` + the prompt's "May run focused tests on `tests/orders/`"):
  - `uv run pytest --no-cov tests/orders/test_finalizer.py` — 19 / 19 passed.
  - `uv run pytest --no-cov tests/orders/` — 115 / 115 passed (the full orders test tree).
  - `uv run pytest --no-cov tests/types/ tests/filters/ tests/base/` — 498 / 498 passed + 2 skipped (sibling subsystem regression check).
  - `uv run pytest --no-cov tests/types/test_base.py tests/orders/` — 176 / 176 passed after the `tests/types/test_base.py` parametrize fix.

### Implementation notes

- **Subpass 2 explicitly resolves `RelatedOrder.orderset` after `get_fields()`.** The shipped `OrderSet.get_fields()` does NOT eagerly resolve lazy `RelatedOrder` refs (unlike the filter side's `get_filters()` which calls `_expand_related_filter` that reads `f.filterset`). To honor the spec's "ImportError from unresolved `RelatedOrder('...')` rewraps as ConfigurationError with `__cause__` preserved" contract at the subpass-2 boundary, my `_bind_ordersets()` subpass 2 calls `get_fields()` AND then walks `related_orders.values()` and reads `.orderset` on each — the read triggers `LazyRelatedClassMixin.resolve_lazy_class` which raises `ImportError` for unresolved string targets. Without this explicit resolution, an unresolved-related-order would only surface at subpass-4 materialize-time as a bare `ImportError` from inside `_build_input_fields` (`related_or_none.orderset`), bypassing the spec-named subpass-2 rewrap. Pinned by `test_phase_2_5_unresolved_related_order_raises_at_finalize`.
- **`_format_owner_orderset_model_mismatch_error` uses `getattr(orderset_cls.Meta, "model", None)` chain.** `OrderSet` doesn't carry a `BaseFilterSet`-style `_meta` aggregator, so the chain is one indirection longer than the filter side's `filterset_cls._meta.model`. Same naming-of-four-entities contract regardless. The `orderset_model_name` fallback to `"<unset>"` covers the (rare but defined) case where `Meta.model` is absent at error-format time.
- **The `_bind_orderset_owner` first-bind branch reads `getattr(getattr(orderset_cls, "Meta", None), "model", None)` rather than `orderset_cls._meta.model`** for the same reason. The discretion item 2 in the Plan named this; I picked the inline `getattr` chain over adding a one-line `_meta` shim on `OrderSet` to keep Slice 3 strictly types-package-scoped.
- **The two `registry.clear()` blocks are ordered namespace-first then helper-ledger-second** (matching the filter side's order at `registry.py::TypeRegistry.clear`'s `clear_filter_input_namespace` → `_helper_referenced_filtersets.clear()` sequence). Discretion item 4 in the Plan named the choice; I followed the filter-side order as the safer default.
- **Subpass 4 calls `OrderArgumentsFactory(orderset_cls).arguments` to trigger the BFS** and then iterates `factory.input_object_types.items()` to materialize every built class. Identical shape to the filter side's `_bind_filtersets` subpass 4.
- **The test stub for `_owner_definition_stub` carries a `model` attribute** so `_bind_orderset_owner`'s first-bind branch's `definition.model is not None` check works on the synthetic definitions in `test_bind_orderset_owner_continues_when_both_targets_unresolved` and friends. Without `model=None` on the stub the first-bind check would raise instead of binding cleanly.
- **`tests/types/test_base.py` parametrize fix:** the existing `test_meta_rejects_each_deferred_key` would have failed on `"orderset_class"` after my edit (since it's no longer in `DEFERRED_META_KEYS`). I removed it from the list and added the matching `test_meta_orderset_class_is_promoted_to_allowed_meta_keys` per the Plan. The same shape is what was applied for `"filterset_class"` in `DONE-027-0.0.8`.

### Notes for Worker 3

- **Subpass 2 explicitly resolves related orders.** Worker 3 should treat the post-`get_fields()` walk over `related_orders.values()` reading `.orderset` as the spec-contract-fulfilling addition — without it, the `ImportError` rewrap would land at subpass 4 instead of subpass 2 (because the order side's `get_fields()` doesn't itself resolve lazy refs the way the filter side does). The behavior is documented in the inline comment block on the subpass-2 body. The corresponding test pins the contract.
- **Spec Decision 6 second-paragraph deliberate divergence.** `_bind_orderset_owner` SKIPS the filter side's Axis-1 own-PK Relay-identity check. Pinned by `test_bind_orderset_owner_does_not_check_axis_1_relay_identity` (the inverse-assertion mirror of the filter side's `test_bind_filterset_owner_rejects_diverging_own_pk_relay_node_ness`).
- **No `scripts/review_inspect.py` invocations during build.** The Plan's planning-pass disposition ran the helper on the four target files; Worker 3's review-time helper trigger fires for `types/base.py` (≥30 lines new logic) and `types/finalizer.py` (≥30 lines new logic). Worker 3 will run the helper at review time per `BUILD.md` "Worker 3 must run the helper during review when ... slice adds 30 or more lines of new logic to any file under `django_strawberry_framework/`".
- **No temp/scratch tests created.** All Slice 3 tests landed as permanent tests under `tests/orders/` and `tests/types/`.
- **Subprocess test isolation.** The `test_registry_clear_works_without_orders_imported` subprocess test mirrors the shipped filter-side subprocess test verbatim — same fakeshop-rooted path derivation, same `assert 'django_strawberry_framework.orders' not in sys.modules` guard.

### Notes for Worker 1 (spec reconciliation)

- **Subpass 2 contract refinement (recordable as spec edit candidate, NOT structural drift).** The spec's Slice 3 sub-bullet 3 phrasing — "call `get_fields()` for every wired orderset only after every owner is bound — `ImportError` from unresolved `RelatedOrder("...")` rewraps as `ConfigurationError`" — reads as if `get_fields()` alone is the trigger. The order subsystem's `get_fields()` does NOT eagerly resolve lazy refs (verified at `orders/sets.py::OrderSet.get_fields` — it iterates `related_orders.items()` and stores instances directly; the filter side's `get_filters()` is different because `_expand_related_filter` reads `f.filterset`). My implementation adds an explicit walk over `related_orders.values()` reading `.orderset` AFTER `get_fields()` returns, all under the subpass-2 try/except, so the spec-named rewrap contract IS observable at subpass 2 — it just needs the explicit resolution trigger to fire. Recommend Worker 1 record this as a clarification at final verification: either edit the spec sub-bullet 3 to say "call `get_fields()` AND resolve every `RelatedOrder`'s `.orderset`" or accept the implementation as the intended reading. No code change needed either way; the contract is preserved.
- **No other spec/plan tension surfaced.** Every other sub-check from the verbatim spec slice checklist landed without ambiguity. Worker 3's review-time helper output may surface additional cross-file dup-literal candidates between `types/finalizer.py`'s order-side and filter-side helpers; the planning DRY analysis already named these as "subsystem-noun-specific" and not consolidation candidates.

---

## Review (Worker 3)

### High:

None.

### Medium:

#### Out-of-scope behaviour change to `_validate_optimizer_hints` error wording

`django_strawberry_framework/types/base.py::_validate_optimizer_hints` swapped its `excluded_hint_fields` raise from the shared `_format_unknown_fields_error(... attr="optimizer_hints", available=selected_relation_names)` helper to a bespoke f-string ("optimizer_hints names fields that are not selected relations: ..."). `tests/types/test_base.py` lines ~353 / ~363 / ~381 follow with three `match=` updates from `"optimizer_hints names unknown fields"` to `"not selected relations"`. None of this is in the Slice 3 plan (`Plan (Worker 1)` lists only the four named edits for `types/base.py`: drop key, add key, add `_validate_orderset_class`, add `_ValidatedMeta` slot, thread through `_validate_meta` / `DjangoType.__init_subclass__`); none of it is in the Slice 3 build report (`### Files touched` for `types/base.py` lists only those same edits); and `_validate_optimizer_hints` / "optimizer_hints" / "excluded_hint_fields" do not appear anywhere in the Slice 3 plan or build report. The plan preamble's "Baseline-dirty out-of-scope files" does not list `types/base.py` or `tests/types/test_base.py`. The behaviour change reads sensibly on its own (the previous routing produced an "unknown fields" message for fields that were known-but-unselected; the new message is clearer), but it is unaccounted-for drift from the Slice 3 contract — either a stray maintainer touch surfaced mid-build that should be added to the baseline-dirty list, or a Worker 2 cleanup that should be recorded under `### Implementation notes`.

```django_strawberry_framework/types/base.py::_validate_optimizer_hints
        raise ConfigurationError(
            f"{model.__name__}.Meta.optimizer_hints names fields that are not selected "
            f"relations: {excluded_hint_fields}. Available selected relations: "
            f"{sorted(selected_relation_names)}. (Hints only fire on relation branches; "
            f"excluded fields and selected scalar fields are unreachable.)",
        )
```

Recommended resolution path (Worker 1 owns at final verification): either add `django_strawberry_framework/types/base.py` and `tests/types/test_base.py` to the build plan's baseline-dirty list (the maintainer's concurrent work explanation, per `AGENTS.md` #"Unexpected file modifications"), or accept the change as in-scope but record it under `### Implementation notes` of the Slice 3 build report. No code revert recommended — the new wording is a strict improvement.

#### Planned-but-dropped `test_phase_2_5_partial_failure_leaves_consistent_namespace`

The Plan's `### Test additions / updates` block (artifact line 323) names `test_phase_2_5_partial_failure_leaves_consistent_namespace` covering Spec Decision 9 "partial-finalize recovery" lifecycle. The Build report's `### Tests added or updated` list has 19 finalizer tests but not this one, and `### Implementation notes` does not record the drop. Reading the implementation, the planned scenario ("instrument `ShelfOrder.get_fields` to raise `ConfigurationError` AFTER `BookOrder.get_fields()` has completed AND AFTER `BookOrderInputType` has been materialized") cannot fire under the actual subpass shape — subpass 2 (expansion) runs across every owner BEFORE subpass 4 (materialization), so a `get_fields` raise on the second owner cannot leave the first owner already materialized. The plan-vs-implementation mismatch is real (the planned test was incompatible with the shipped subpass order), but the silent drop should have been recorded. Either Worker 2 should call out the drop with a one-line reason in `### Implementation notes`, or replace it with a test that pins what partial-failure recovery actually means under the shipped subpass order (e.g., a subpass-2 raise leaves `_owner_definition` set on the first orderset, `_materialized_names` empty, and a follow-up `finalize_django_types()` call after the consumer fixes the failure cleanly materializes both).

### Low:

#### Spec sub-bullet 3 wording vs. subpass-2 implementation

Captured by Worker 2 under `### Notes for Worker 1 (spec reconciliation)`. The spec sub-bullet 3 phrasing reads as if `get_fields()` alone triggers the `ImportError` rewrap, but `OrderSet.get_fields()` stores `RelatedOrder` instances without reading `.orderset`. Worker 2 added an explicit `for related in getattr(orderset_cls, "related_orders", {}).values(): _ = related.orderset` walk inside the subpass-2 try/except so the contract is observable at subpass 2. Pinned by `test_phase_2_5_unresolved_related_order_raises_at_finalize`. Not blocking; Worker 1 decides at final verification whether the spec wording deserves a clarification edit or whether the implementation reading is the intended one. Forwarded below under `### Notes for Worker 1 (spec reconciliation)` so it is not lost.

### DRY findings

None. The five new finalizer helpers (`_bind_orderset_owner`, `_bind_ordersets`, `_format_owner_orderset_model_mismatch_error`, `_format_owner_ordersets_mismatch_error`, `_format_orphan_ordersets_error`) mirror their filter-side siblings one-for-one with the licensed subsystem-noun substitutions (`FilterSet`→`OrderSet`, `filter_input_type`→`order_input_type`, `Meta.filterset_class`→`Meta.orderset_class`, `related_filters`→`related_orders`, `_helper_referenced_filtersets`→`_helper_referenced_ordersets`, `FilterArgumentsFactory`→`OrderArgumentsFactory`, `filters.inputs`→`orders.inputs`). The deliberate divergence — `_bind_orderset_owner` skipping the filter side's Axis-1 own-PK Relay-identity check — is spec-licensed (Decision 6 second paragraph) and pinned by `test_bind_orderset_owner_does_not_check_axis_1_relay_identity`. The four-subpass body of `_bind_ordersets` matches `_bind_filtersets`'s shipped shape verbatim. The two new `registry.clear()` blocks mirror the filter-side two-block shape verbatim. No consolidation candidates surfaced — the wording divergence in the error formatters carries subsystem-identifying information (an `OrderSet` error vs `FilterSet` error tells the maintainer which sidecar is broken), so a shared formatter would lose semantic precision.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` returns empty — no public surface changes. Consistent with the slice's plan (no new top-level re-exports; all order primitives are imported from `django_strawberry_framework.orders`).

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **Subpass discipline is the shipped filter order verbatim.** `_bind_ordersets` runs bind → expand → orphan-validate → materialize in that order. The orphan-validation-before-materialization invariant is preserved by `wired_set = set(wired)` plus the sorted-orphans raise BEFORE the materialize loop. Pinned by `test_phase_2_5_orphan_check_runs_before_materialization`.
- **Local-import-against-cycle contract is single-sited and tested.** `_validate_orderset_class` uses `from ..orders.sets import OrderSet` inside the function body; `test_validate_orderset_class_uses_local_import` asserts both halves (the module-top namespace does NOT carry `OrderSet`, AND the function source carries the local-import line). The two-part assertion is the right pin shape — it catches a future hoist whether the hoist is by Worker 2, a refactor, or auto-format reordering.
- **The two `registry.clear()` blocks are independent.** Each block uses `try / except ImportError: pass / else:`, NOT `return`. A future fifth phase (e.g., aggregates 0.1.3) added after the order-side blocks cannot be silently skipped if the order subsystem fails to import. Matches the filter-side shape and the Spec B2 of rev1 contract verbatim.
- **The shipped TypeRegistry field names stayed shipped.** `_types` / `_primaries` / `_models` / `_enums` / `_definitions` / `_pending` / `_finalized` at `TypeRegistry.clear` lines 404-410 are untouched; no phantom `_types_by_model` / `_primary_types` references reintroduced. The two new blocks added below them keep the existing model-state clear lines uncontaminated.
- **`Meta.orderset_class` promotion is structurally complete.** `DEFERRED_META_KEYS` drops the key, `ALLOWED_META_KEYS` adds it alphabetized between `"optimizer_hints"` and `"primary"`, `_validate_meta` calls `_validate_orderset_class` adjacent to the filter side's call, `_ValidatedMeta` carries the slot, `DjangoType.__init_subclass__` threads it through to `DjangoTypeDefinition`, and the docstring on `DjangoTypeDefinition` carries a parallel `orderset_class` bullet to the existing `filterset_class` bullet. `tests/types/test_base.py::test_meta_orderset_class_is_promoted_to_allowed_meta_keys` is the canonical Decision-7 pin. The parametrize drop on `test_meta_rejects_each_deferred_key` is the necessary partner change.
- **Subpass-2 implementation closes the spec contract regardless of the wording question.** The explicit `.orderset` walk over `related_orders.values()` AFTER `get_fields()` forces Layer-2 lazy resolution at the subpass-2 boundary, so `test_phase_2_5_unresolved_related_order_raises_at_finalize` observes `__cause__` as the underlying `ImportError`. The choice is well-justified in `### Implementation notes` and `### Notes for Worker 1`.
- **No surviving Slice-3 TODO anchors.** Spot-checked every site named in the plan's discretion item 5; every TODO anchor block was consumed, and the remaining `spec-028` references in `types/finalizer.py` and `registry.py` are docstring citations (intentional cross-references), not surviving work-parking blocks.
- **All four target files in scope.** `scripts/review_inspect.py --output-dir docs/shadow` was run for `types/base.py` (963 lines), `types/definition.py` (191 lines), `types/finalizer.py` (860 lines), and `registry.py` (456 lines). All four are under `types/` (or `registry.py` is a core file at the package root) — the helper triggers fired; shadow overviews were generated cleanly. No new cross-file repeated-literal dups beyond the planned subsystem-noun strings.

### Temp test verification

No temp tests created during review; the artifact's full test list (33 listed Slice-3 tests across `tests/orders/test_finalizer.py`, `tests/orders/test_base.py`, `tests/orders/test_inputs.py`, `tests/types/test_base.py`) plus running the focused `tests/orders/ tests/filters/ tests/types/ tests/base/` suite (613 passed, 2 skipped) was sufficient to verify behaviour. No temp probes promoted; nothing deferred.

### Notes for Worker 1 (spec reconciliation)

- **Spec sub-bullet 3 wording vs. subpass-2 implementation.** Carried forward from Worker 2's `### Notes for Worker 1 (spec reconciliation)`. The order subsystem's `get_fields()` does not eagerly resolve lazy refs (unlike `get_filters()`); Worker 2's implementation adds an explicit `.orderset` walk inside the subpass-2 try/except so the spec-named `ImportError` rewrap fires at subpass 2 boundary. Recommend Worker 1 either edit the spec sub-bullet 3 wording to acknowledge the explicit resolution trigger, or accept the implementation as the intended reading. No code change needed either way; pin is `test_phase_2_5_unresolved_related_order_raises_at_finalize`.
- **Out-of-scope behaviour change to `_validate_optimizer_hints` error wording.** Escalated above as Medium. Worker 1 owns the resolution: either expand the baseline-dirty list to cover the maintainer's concurrent touch on `types/base.py` / `tests/types/test_base.py`, or accept it as in-scope Worker 2 cleanup and record under `### Implementation notes`. The new wording is a strict improvement (correctly distinguishes "names unknown fields" from "names known-but-unselected fields"), so no revert is recommended.
- **Planned-but-dropped `test_phase_2_5_partial_failure_leaves_consistent_namespace`.** Escalated above as Medium. The planned scenario cannot fire under the shipped subpass order; Worker 1 should decide whether to (a) accept the silent drop with a recorded reason in the build report, or (b) require Worker 2 to add a replacement test pinning what partial-failure recovery actually means under the shipped subpass ordering (a subpass-2 raise leaving the registry recoverable on re-call, with no partial materialization).

### Review outcome

`review-accepted`. Two Medium findings escalated to Worker 1 (transparent escalation per `worker-3.md` "Worker 3 may also set `review-accepted` with one or more Medium-or-higher findings transparently escalated to Worker 1"); both resolution paths require spec / baseline-dirty context Worker 2 cannot provide. The Low finding mirrors Worker 2's own self-escalation and Worker 1's final verification owns the call. No High findings; every spec-required behaviour is reflected in the diff and pinned by a permanent test.

---

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[feedback]: ../feedback.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../django_strawberry_framework/types/base.py
[definition]: ../../django_strawberry_framework/types/definition.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
