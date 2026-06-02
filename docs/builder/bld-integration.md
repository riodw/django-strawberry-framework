# Build: Cross-slice integration pass

Spec reference: `docs/spec-028-orders-0_0_8.md` (whole spec — the integration pass covers Slices 1-6 in aggregate; no single spec line range)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

The integration-pass DRY scan walks the seven inputs required by `docs/builder/BUILD.md` "Cross-slice integration pass":

1. Every prior `docs/builder/bld-slice-*.md` artifact read in slice order. All six artifacts are at `Status: final-accepted`; every per-slice `What looks solid` / `DRY findings` / `Notes for Worker 1` block was walked.
2. `scripts/review_inspect.py --all --output-dir docs/shadow` re-ran at the start of this pass (43 package `.py` files refreshed). Per-file `Repeated string literals` sections cross-walked.
3. `Imports` sections cross-walked to confirm one-way dependency direction.
4. Naming-symmetry scan walked every order-side / filter-side / type-side pair Slices 1-3 introduced.
5. The five deferred items Worker 0 surfaced (collision-message wording, `_isolate_registry` duplication, DONE-027 "carried by sibling" closure, `_field_type_suffix` dead surface, Slice 3 `_validate_optimizer_hints` parked follow-up) all addressed below.

### Cross-file repeated-literals walk

Cross-walked `## Repeated string literals` sections for every shadow overview under `docs/shadow/django_strawberry_framework__{orders,filters,sets_mixins,types,registry}__*.overview.md`.

Per-file findings (verbatim from the shadow overviews):

- `orders/factories.py`: None.
- `orders/inputs.py`: 3x `description`, 2x `__annotations__`.
- `orders/sets.py`: 5x `related_orders`, 2x `_expanded_fields`.
- `orders/__init__.py`: None.
- `orders/base.py`: None.
- `filters/factories.py`: None.
- `filters/inputs.py`: 3x `contains`, 3x `description`, 2x `istartswith`, 2x `week_day`, 2x `field_name`, 2x `__annotations__`.
- `filters/sets.py`: 5x `related_filters`, 3x `__dataclass_fields__`, 3x `FilterSet`, 3x logical-branch-depth error fragments, 2x `_expanded_filters`, 2x `is_relation`, 2x `_permission`.
- `types/finalizer.py`: 4x `<unresolved>`, 3x `FilterSet`, 2x `_owner_definition`, 2x `cannot bind to multiple owners with diverging targets:`, 2x `related_orders`, 2x `OrderSet`, 2x `Cannot finalize Django types: orderset`, 2x `Cannot finalize Django types: filterset`, plus the binding-error fragment family (`resolves`, `resolves it to`, `(relay_node=`, `, type_name=`, `), but its own Meta.model is`, `, or attach it to a`, `' to the relevant DjangoType's Meta.`).

**Cross-file occurrences** (literal appears in two or more shadow files):

| Literal | Files | Subsystem-noun status | DRY action |
|---|---|---|---|
| `description` | `orders/inputs.py`, `filters/inputs.py` | Python attribute on Strawberry input fields — not a duplicate executable string, both subsystems emit `description=...` per `dataclasses.field` kwarg | None |
| `__annotations__` | `orders/inputs.py`, `filters/inputs.py` | Python dunder, reflective access at `_build_class_type` time | None |
| `related_orders` | `orders/sets.py`, `types/finalizer.py` | Load-bearing class-attribute identifier referenced from the metaclass (sets) and the binding pass (finalizer) — same-subsystem cross-file reference | None |
| `related_filters` | `filters/sets.py`, `types/finalizer.py` | Symmetric to `related_orders` on the filter side | None |
| `OrderSet` | `orders/*` (within docstrings), `types/finalizer.py` | Class-name token used in subsystem-noun-specific error messages and class-attribute checks; carries identifying information for the consumer | None |
| `FilterSet` | `filters/*`, `types/finalizer.py` | Symmetric to `OrderSet` on the filter side | None |
| `Cannot finalize Django types: orderset` / `Cannot finalize Django types: filterset` | `types/finalizer.py` (both, side-by-side) | Subsystem-noun-specific error prefixes — the noun is load-bearing for the consumer (tells them WHICH Meta key to fix); a shared formatter would lose the per-subsystem nounce | None |

No cross-file literal surfaced that is consolidable without losing subsystem-identifying information. All cross-file occurrences are either Python-attribute tokens (universally safe to repeat), load-bearing class-attribute identifiers consumed by metaclass + finalizer-binding-pass pairs, or subsystem-noun-specific error prefixes whose noun is the actionable signal for the consumer.

### Cross-file imports walk

Confirmed one-way dependency direction (from the per-file shadow overviews and `grep -rn "from .*filters\|import.*filters" django_strawberry_framework/orders/`; symmetric grep for `filters/` → `orders/`):

- `django_strawberry_framework/orders/*.py` — imports from `..sets_mixins` (`LazyRelatedClassMixin`, `ClassBasedTypeNameMixin`), `..exceptions` (`ConfigurationError`), `..registry` (none directly — Slice 3 wires through finalizer), `..conf`, `django.*`, `strawberry.*`, stdlib. **Zero imports from `filters/`.** The only `filters` mention in `orders/` is the docstring breadcrumb in `orders/base.py` ("importing through `filters.base` would load the entire filter subsystem just to build orders" — historical rationale for the H1-rev3 neutralization). Confirmed clean.
- `django_strawberry_framework/filters/*.py` — imports from `..sets_mixins`, `..exceptions`, `..registry`, `..conf`, `django.*`, `strawberry.*`, stdlib. **Zero imports from `orders/`.** Confirmed clean.
- `django_strawberry_framework/types/*.py` — imports from BOTH `..filters.*` and `..orders.*`, but ALL such imports are **local in-function** to dodge the `types → orders → types` and `types → filters → types` module-load cycles:
  - `types/base.py::_validate_filterset_class` at line 88: `from ..filters.sets import FilterSet` (local).
  - `types/base.py::_validate_orderset_class` at line 116: `from ..orders.sets import OrderSet` (local).
  - `types/finalizer.py::_bind_ordersets` at lines 673-675: `from ..orders import _helper_referenced_ordersets`, `from ..orders.factories import OrderArgumentsFactory`, `from ..orders.inputs import materialize_input_class` (all local).
  - `types/finalizer.py::_bind_filtersets` at lines 780-782: symmetric trio for `filters/` (all local).
- `django_strawberry_framework/registry.py::TypeRegistry.clear` at lines 421, 428, 442, 449: four local-import-with-`pass`-on-ImportError blocks (two for the filter side, two for the order side) per Spec Decision 9 line 775. Symmetric across subsystems.

The sibling-package boundary (`orders/` ⊥ `filters/`) is intact. The integration point lives at `types/` and `registry.py`, both via local in-function imports.

### Naming-symmetry walk

Every order-side symbol that mirrors a filter-side symbol is uniformly named:

| Order side | Filter side | Convention |
|---|---|---|
| `OrderSet` / `OrderSetMetaclass` / `RelatedOrder` | `FilterSet` / `FilterSetMetaclass` / `RelatedFilter` | `<Noun>Set` |
| `OrderArgumentsFactory` | `FilterArgumentsFactory` | `<Noun>ArgumentsFactory` |
| `OrderArgumentsFactory.input_object_types` | `FilterArgumentsFactory.input_object_types` | shared attribute name |
| `OrderArgumentsFactory._type_orderset_registry` | `FilterArgumentsFactory._type_filterset_registry` | `_type_<lowercase>_registry` |
| `order_input_type(OrderSet)` | `filter_input_type(FilterSet)` | `<noun>_input_type(<NounSet>)` |
| `_helper_referenced_ordersets` | `_helper_referenced_filtersets` | `_helper_referenced_<lowercase>s` |
| `clear_order_input_namespace()` | `clear_filter_input_namespace()` | `clear_<noun>_input_namespace` |
| `materialize_input_class(name, input_cls)` (orders) | `materialize_input_class(name, cls)` (filters) | shared name; per-subsystem module-scope namespace |
| `_materialized_names: dict[str, type]` | `_materialized_names: dict[str, type]` | shared attribute name; per-subsystem module-scope namespace |
| `INPUTS_MODULE_PATH = "django_strawberry_framework.orders.inputs"` | `INPUTS_MODULE_PATH = "django_strawberry_framework.filters.inputs"` | shared attribute name; per-subsystem value |
| `_input_type_name_for(orderset_class)` | `_input_type_name_for(filterset_class)` | shared name |
| `Meta.orderset_class` | `Meta.filterset_class` | `Meta.<noun>set_class` |
| `_validate_orderset_class` | `_validate_filterset_class` | `_validate_<noun>set_class` |
| `_bind_ordersets()` / `_bind_orderset_owner()` | `_bind_filtersets()` / `_bind_filterset_owner()` | `_bind_<noun>sets` / `_bind_<noun>set_owner` |
| `_format_owner_orderset_model_mismatch_error` / `_format_owner_ordersets_mismatch_error` / `_format_orphan_ordersets_error` | symmetric `_format_*` triplet on the filter side | per-subsystem error formatters |
| `OrderSet.apply_sync` / `OrderSet.apply_async` | `FilterSet.apply_sync` / `FilterSet.apply_async` / `FilterSet.apply` (dispatcher) | order side has NO `apply` dispatcher per Spec DoD 4(c) — spec-licensed asymmetry |
| `OrderSet.check_permissions` (instance) + `OrderSet._run_permission_checks` (classmethod) | `FilterSet.check_permissions` (instance) + `FilterSet._run_permission_checks` (classmethod) | dual surface mirrored verbatim |
| `Meta.orderset_class` slot on `DjangoTypeDefinition` | `Meta.filterset_class` slot on `DjangoTypeDefinition` | symmetric optional `type | None` |

Naming is uniform across the two subsystems. The only spec-licensed asymmetries are:

- `OrderSet.apply` dispatcher omitted (Spec DoD 4(c) — order side has no sync-misuse `RuntimeError` rewrap path).
- `_bind_orderset_owner` SKIPS the filter side's Axis-1 own-PK Relay-identity check (Spec Decision 6 second paragraph — ordering does NOT consult Relay shape; an `ORDER BY id` uses the Django PK column, not the GraphQL `GlobalID`).
- Order side has no operator-bag / form-validation surface (Spec Decision 8 line 686).

Each asymmetry is pinned by a permanent test in `tests/orders/` and is spec-licensed.

### Deferred-item resolution (the five items Worker 0 named)

1. **`materialize_input_class` collision-message wording divergence (Slice 1 deferral).** Compared the two messages side-by-side via `grep -n -A4 "raise ConfigurationError" django_strawberry_framework/orders/inputs.py django_strawberry_framework/filters/inputs.py`:

   - Order side (`orders/inputs.py:384-388`): `f"{name!r} is materialized by two distinct OrderSet input classes: {existing.__module__}.{existing.__qualname__} vs {input_cls.__module__}.{input_cls.__qualname__}. Rename one orderset so its class-derived input type name is unique."`
   - Filter side (`filters/inputs.py:871-875`): `f"{name!r} is materialized by two distinct FilterSet input classes: {existing.__module__}.{existing.__qualname__} vs {cls.__module__}.{cls.__qualname__}. Rename one filterset so its class-derived input type name is unique."`

   The two messages are structurally identical and differ only in two subsystem-noun substitutions (`OrderSet`/`orderset` ↔ `FilterSet`/`filterset`). Consolidating to a shared formatter that strips the subsystem noun would force the consumer to do extra work to identify which `Meta.<X>set_class` declaration is conflicting — the noun is actionable, not redundant. **Resolution: accept both messages as-is.** The wording divergence is intentional subsystem identification, not DRY drift. No consolidation needed.

2. **`_isolate_registry` duplication between `tests/orders/test_finalizer.py:51-65` and `tests/orders/test_composition.py:88-124` (Slice 6 deferral).** The two fixtures are NOT literal duplicates:

   - `test_finalizer.py::_isolate_registry` clears six caches on the **order side only** (`registry`, `_field_specs`, `_helper_referenced_ordersets`, `_materialized_names`, `OrderArgumentsFactory.input_object_types`, `OrderArgumentsFactory._type_orderset_registry`).
   - `test_composition.py::_isolate_registry` clears twelve caches on **BOTH subsystems** (the six order-side caches above PLUS the six filter-side equivalents).

   The composition test's extended-scope reset is load-bearing for Slice 6's cross-card contract; the finalizer test's narrow-scope reset is appropriate for the order-side-only tests in that file. Consolidating to a single `tests/orders/conftest.py` fixture would force one of two patterns: (a) the wider 12-cache reset applies to every `tests/orders/` test (paying filter-side reset cost on every order-only test, plus introducing a dependency on `filters/` that the finalizer test currently does not need); or (b) a parametrized fixture with a `clear_filter_side: bool = False` toggle (thread a parameter through every test file's fixture chain to express what is currently a one-line clear-list extension at the composition test's local scope). Neither pattern improves clarity over the per-file fixture. **Resolution: accept the two fixtures as separately scoped to their use sites.** The "duplication" is two same-shaped-but-different-scoped resets; keeping them local to their files is the right altitude. Worker 3's Slice 6 `### DRY findings` already endorsed this disposition.

3. **DONE-027-0.0.8 filter spec's "Slice-6 carried by sibling" deferral (Slice 6 spec contract).** Spec line 138-139 explicitly states "The Slice-6 conditional clause from the Filtering spec's `## Slice checklist` — 'carried by sibling' — is satisfied here by this card carrying the composition test instead." Slice 6 of spec-028 ships `tests/orders/test_composition.py` with two test functions that pin the cross-card composition contract end-to-end. **Resolution: closed.** No further action required.

4. **`OrderSet._field_type_suffix` flagged as dead surface (Slice 1 deferral).** `grep` confirms every `type_name_for` call site in `orders/` passes no `field_path=` argument:

   - `orders/inputs.py::_input_type_name_for` line 136: `return orderset_class.type_name_for()` (no `field_path=`).
   - `orders/factories.py` lines 100, 141, 169: all call `_input_type_name_for(...)` which delegates without `field_path=`.

   The `_field_type_suffix = "InputType"` default lives on `sets_mixins.ClassBasedTypeNameMixin` (line 59), which is the neutral shared mixin. Removing the slot would break the filter side's per-field-bag class naming (filter side overrides to `"FilterInputType"` and consumes it at `type_name_for(field_path=...)` call sites in `filters/inputs.py`). For the order side, the slot is inherited-but-unconsumed surface — a natural mixin-inheritance pattern where one subsystem uses a hook the sibling subsystem doesn't. **Resolution: document as future-extension surface, not dead code.** A future card that adds per-field-bag classes to the order side (analogous to the filter side's `LookupArgsFilterInputType` per-field bags) would consume the slot naturally; until then, the slot stays on the mixin with the order side as an inheriting non-consumer. Recorded under `### Deferred work catalog` so a future reader does not interpret the unused slot as a bug.

5. **Slice 3 `_validate_optimizer_hints` wording follow-up (Slice 3 final-verification pass-2 deferral).** Worker 2 pass-1 swapped the shared `_format_unknown_fields_error` call to a bespoke f-string ("optimizer_hints names fields that are not selected relations: ...") which is a strict wording improvement (distinguishes "names unknown fields" from "names known-but-unselected fields"). Worker 1 pass-1 ruled this out of scope and required pass-2 to revert; the improved wording is parked as a maintainer follow-up per Slice 3 final-verification disposition. **Resolution: confirmed parked.** Recorded under `### Deferred work catalog` for the next spec author's reading list.

### Implementation steps

None. The integration pass surfaced zero DRY-driven consolidation work. The slice-deferred items are all dispositioned without code changes:

- Five subsystem-noun-specific wordings stay as-is (load-bearing per-subsystem identification).
- Two test fixtures stay locally scoped to their files (different reset scope per use site).
- One mixin slot stays inherited-but-unconsumed on the order side (future-extension surface).
- One Slice-3 wording improvement stays parked (Worker 1 pass-1 already ruled it out of scope).
- One sibling-Slice-6 closure stays closed.

### Test additions / updates

None. The existing 615-test focused sweep (615 passed when slice-6 final verification ran; 665 passed including library acceptance + live HTTP under this integration pass) already pins every cross-slice contract:

- `tests/orders/test_composition.py::test_filter_and_order_compose_through_finalizer_and_apply_pipelines` — cross-subsystem materialization + apply-pipeline composition.
- `tests/orders/test_composition.py::test_filter_and_order_share_lazy_related_class_mixin_via_neutral_module` — neutral-mixin sharing pin (catches a future sibling-copy refactor).
- `tests/orders/test_base.py::test_related_order_imports_lazy_mixin_from_sets_mixins_not_filters_base` — H1-of-rev3 import-discipline pin (catches a future regression back to `filters.base`).
- `tests/orders/test_finalizer.py::test_bind_orderset_owner_does_not_check_axis_1_relay_identity` — spec-licensed asymmetry pin.
- `tests/orders/test_finalizer.py::test_phase_2_5_orphan_check_runs_before_materialization` — subpass ordering pin (orphan before materialize, the load-bearing invariant).
- `tests/types/test_base.py::test_meta_orderset_class_is_promoted_to_allowed_meta_keys` — Decision-7 promotion-gate pin.
- `examples/fakeshop/test_query/test_library_api.py::test_library_books_filter_and_order_compose` — live HTTP cross-card composition pin.

### Implementation discretion items

None. The integration pass produced no code changes; nothing was at Worker 2's discretion.

### Spec slice checklist (verbatim)

Not applicable. The integration pass is not a spec-checklist slice; it is the cross-slice DRY scan that runs after every spec slice is `final-accepted`. The build plan tracks it as `### Cross-slice integration pass -> docs/builder/bld-integration.md` (build-plan line 87), not as a numbered spec slice.

---

## Final verification (Worker 1)

- **DRY check across all slices:** clean. The seven cross-slice DRY scan inputs (every prior `bld-slice-*.md` artifact, every per-file shadow overview's `Repeated string literals` section, every per-file `Imports` section, the order-vs-filter naming-symmetry table, every per-slice `What looks solid` and `DRY findings` section, the five Worker-0-named deferred items, the Worker 3 review pass-2 findings) all walked. Zero consolidation candidates surfaced that would improve clarity without losing subsystem-identifying information or use-site-appropriate scope.

- **Existing tests still pass:** `uv run pytest tests/orders/ tests/filters/ tests/types/ tests/base/ examples/fakeshop/apps/library/tests/ examples/fakeshop/test_query/test_library_api.py --no-cov` → **665 passed, 2 skipped, 1 warning in 9.94s**. No `--cov*` flags used. The single warning is the pre-existing `tests/types/test_generic_foreign_key.py::test_generic_relation_executes_with_optimizer_extension` Strawberry-extensions DeprecationWarning, unrelated to spec-028.

- **Spec reconciliation:** none required. The five deferred items all close without spec body edits:
  - Items 1, 2 are use-site dispositions, not spec contracts.
  - Item 3 is closed by Slice 6's shipped contract; spec line 138-139 already records the closure.
  - Item 4 is an interpretation note about the inherited-from-mixin slot; the spec already pins (per Decision 8 line 686) that the order side has no operator-bag / per-field-bag classes, which implies the slot is future-extension surface for the order side.
  - Item 5 is a Worker-1-pass-1-already-disposed parking; no spec edit needed.

- **Cross-slice naming-symmetry consistency:** confirmed via the naming-symmetry table above. Every Order-side symbol uniformly mirrors its Filter-side sibling under the spec-licensed asymmetries (no `apply` dispatcher; no Axis-1 own-PK Relay-identity check on `_bind_orderset_owner`; no operator-bag surface).

- **Cross-slice dependency direction:** confirmed via the cross-file imports walk. `orders/` ⊥ `filters/` (sibling-package isolation); both compose through `types/` and `registry.py` via local in-function imports for cycle avoidance.

- **Public surface:** `git diff -- django_strawberry_framework/__init__.py` returns empty across the whole spec-028 build (verified by the per-slice `### Public-surface check` sections in Slices 1-6, all reporting "empty" or "no change"). The spec contracted no top-level `__all__` growth; the build delivered no top-level `__all__` growth. The growth that DID land — `orders/__init__.py::__all__` expanding from `("Ordering", "OrderSet", "OrderSetMetaclass", "RelatedOrder")` to include `"order_input_type"` per Slice 2 — is subsystem-boundary growth licensed by Spec Decision 11 + Decision 2, NOT package-root growth.

- **CHANGELOG:** only Slice 5 touched `CHANGELOG.md` (per the build plan's "CHANGELOG-edit permission" preamble). Slice 5's `### Added` and `### Changed` bullets shipped under preserved `[Unreleased]` with no version-heading promotion per Decision 10 / Revision 5. Verified clean against `git diff` and the per-slice CHANGELOG sanity blocks.

- **No version bump:** `pyproject.toml`, `django_strawberry_framework/__init__.py::__version__`, and `tests/base/test_init.py::test_version` all unchanged across the whole spec-028 build (the build plan's "No version bump in this card" rule + Revision 5 maintainer-commanded boundary). Confirmed by `git diff -- pyproject.toml django_strawberry_framework/__init__.py tests/base/test_init.py` returning empty.

- **Baseline-dirty discipline:** the 25+ baseline-dirty out-of-scope paths listed in the build plan preamble (`TODAY.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, optimizer files, kanban app files, etc.) all stayed out-of-scope per their carve-outs; the three Slice-5 carve-outs (`docs/GLOSSARY.md`, `docs/TREE.md`, `TODAY.md`) were layered additively in Slice 5 only.

- **Final status:** `final-accepted`.

### Summary

The cross-slice integration pass for spec-028-orders-0_0_8 ran clean. Zero consolidation work surfaced. Every cross-file repeated literal is either a Python attribute/dunder token (universally safe), a load-bearing class-attribute identifier consumed symmetrically by the metaclass and the finalizer binding pass, or a subsystem-noun-specific error prefix carrying actionable per-subsystem identification. Every order-side symbol uniformly mirrors its filter-side sibling under spec-licensed asymmetries. The sibling-package boundary `orders/` ⊥ `filters/` is intact; both subsystems compose through `types/` and `registry.py` via local in-function imports for cycle avoidance. The five Worker-0-named deferred items all close without code changes or spec body edits. 665 focused tests pass. The build is staged to spawn the final test-run gate.

### Spec changes made (Worker 1 only)

None. The integration pass surfaced no spec gaps requiring reconciliation. The two Slice-3 spec edits (line 123 sub-bullet 3 subpass-2 wording + Decision 6 subpass 2 paragraph) and the seven Slice-4 spec edits (status header roll-forward + line 127 M7 combined-test + lines 1031/1034/1038 staff-context / city-substitution narration + line 1041 `name` → `city` + lines 1044-1045 combined bullet + Decision 13 line 942 + Implementation-plan row line 966) remain in place from their respective Worker-1 final-verification passes. The Slice-5 and Slice-6 status-header roll-forwards remain in place. No new spec edits in this pass.

### Deferred work catalog

Per `docs/builder/BUILD.md` "Cross-slice integration pass": every item that surfaced across the build that's deferred to a future card / spec / maintainer follow-up. One bullet per deferral with the source artifact section and a one-line description.

- **`_validate_optimizer_hints` wording improvement** (source: `docs/builder/bld-slice-3-wiring.md` `### Spec changes made (Worker 1 only)` pass-1 + `### Build report (Worker 2, pass 2)` revert). The pass-1 wording swap from the shared `_format_unknown_fields_error` helper to a bespoke f-string ("optimizer_hints names fields that are not selected relations: ...") was reverted in pass-2 as out-of-scope. The improved wording IS a strict improvement (correctly distinguishes "names unknown fields" from "names known-but-unselected-as-a-relation fields") and is parked for a maintainer follow-up commit OR a future error-message-clarity spec card. License source: AGENTS.md "Don't add features, refactor, or introduce abstractions beyond what the task requires" + the build plan's per-slice scoping discipline.

- **`OrderSet._field_type_suffix` is inherited-but-unconsumed on the order side** (source: `docs/builder/bld-slice-1-foundation.md` `### Notes for Worker 1 (spec reconciliation)` final bullet). The `_field_type_suffix = "InputType"` default on `django_strawberry_framework/sets_mixins.py::ClassBasedTypeNameMixin` is consumed only by `type_name_for(field_path=...)` call sites; no `orders/` call site passes a non-`None` `field_path` because the order side has no per-field-bag classes (Spec Decision 8 line 686 — "no operator-bag, no form validation"). The slot stays inherited as future-extension surface; a future card that ships per-field per-OrderSet bag classes (e.g., for a hypothetical `RangeOrder` analogous to `RangeFilter`) would consume it naturally. License source: Spec Decision 8 line 686.

- **`OrderSet.apply` sync-misuse dispatcher is intentionally absent** (source: spec-028 DoD item 4(c) + `docs/builder/bld-slice-2-factories.md` `### DRY findings` bullet 4). The filter side ships `FilterSet.apply(...)` to rewrap `RuntimeError` from sync-misuse against async-only `get_queryset` re-derivation; the order side has no `get_queryset` re-derivation step so the dispatcher has no work to do. Future cards that introduce an analogous re-derivation step on the order side would need to revisit. License source: Spec DoD item 4(c) + Decision 8 line 676.

- **Order-side `_is_expanding_fields` reentry-branch coverage** (source: `docs/builder/bld-slice-1-foundation.md` `### Notes for Worker 1 (spec reconciliation)` first bullet + `docs/builder/bld-slice-2-factories.md` `### What looks solid` bullet 10). The reentry-branch test in `OrderSet._expand_meta_fields` was structurally unreachable in Slice 1; Slice 2's removal of the explicit branch test (per the Plan's "Restructure recommendation") left the `_is_expanding_fields` slot in place for defensive purposes. If Slice 6's composition test or a future card produces a recursive `get_fields()` call path, the slot is already in place to re-introduce a guard test without speculative reintroduction now. License source: AGENTS.md "never propose pragma no cover as a workaround for an interpreter-divergent or abstraction-level bug" (the slot stays; the test is added only when the call path exists).

- **H4-rev3 position-side-channel leak deferral** (source: `docs/spec-028-orders-0_0_8.md` Revision 2 H4 + Decision 8 step 4 + Slice 5 GLOSSARY entry bodies). Ordering by a hidden related column changes the position of visible parent rows based on data the user cannot read, so a determined consumer can infer the relative ordering of hidden rows by diff'ing two queries. The leak is intentionally accepted for `0.0.8` (low bandwidth, no value disclosure — only causal explanation of visible ordering); the closing-this design is deferred to a sibling `0.0.9` ordering-permissions card (independent of connection-field design per N-new-1 of Revision 3). License source: Spec Revision 2 H4 + Revision 3 N-new-1.

- **Connection-aware optimizer planning + Layer 6 dynamic-factory cache + DISTINCT ON design** (source: `docs/spec-028-orders-0_0_8.md` Decision 12 + Out-of-scope enumeration at Revision 1). The dynamic-factory cache for connection fields without an explicit `*_class` declaration, the connection-aware optimizer planning that would inspect `queryset.query.order_by` to extend `plan.only_fields`, and the `Meta.distinct` shape choice (tuple-of-names vs class-reference) are all deferred to `0.0.9` alongside the connection-field cohort. License source: Spec Decision 12.

- **`AggregateSet` / `Meta.search_fields` / `FieldSet` / `apply_cascade_permissions`** (source: `docs/spec-028-orders-0_0_8.md` Key glossary references + Out-of-scope enumeration at Revision 1). Sibling Layer-3 sidecars deferred to later cohorts (`0.1.3` aggregates; `0.1.2` search; `0.1.1` fieldsets; `0.0.10` permission cascade). The lazy-resolution architecture this card pins composes with each without retrofit. License source: Spec Revision 1 Out-of-scope block.

- **DONE-027-0.0.8 Slice-6 "carried by sibling" — CLOSED** (source: `docs/spec-028-orders-0_0_8.md` line 138-139 + `docs/builder/bld-slice-6-composition_smoke.md` Final verification). Closed by spec-028 Slice 6 shipping `tests/orders/test_composition.py` with two test functions pinning the cross-card composition contract end-to-end. Recorded here for the next spec author's reading list so the carry-forward chain is traceable; this is the cycle-closing entry, not a new deferral.

- **Worker-3 Slice-6 optional consolidation candidate (`_clear_both_subsystems()` helper)** (source: `docs/builder/bld-slice-6-composition_smoke.md` `### DRY findings` bullet 1). The autouse `_isolate_registry` fixture in `tests/orders/test_composition.py` literally duplicates its 12-line clear sequence in setup and teardown. The same pattern lives in `tests/orders/test_finalizer.py::_isolate_registry` (6-line order-only) and `tests/filters/test_factories.py` (filter-side per-test clears). A future test-infrastructure card could factor a shared `_clear_both_subsystems()` helper at the `tests/orders/` level or a `tests/_shared/` location. Not surfaced as a Slice-6 finding because the duplicated literal IS the shape Slice 6's Plan endorsed; recorded for future test-fixture-hygiene work.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
