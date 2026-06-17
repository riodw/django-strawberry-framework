# Review: `django_strawberry_framework/utils/inputs.py`

Status: verified

## DRY analysis

- None — this module IS the DRY chokepoint (the 0.0.9 DRY pass / `docs/feedback.md` Major 1 + Major 3). It single-sites the BFS input-type generation, the per-class collision check, the idempotent cache, the subclass-rejection guard, the materialization ledger, the namespace-clear lifecycle, the lazy forward-ref builder, the camelCase head-lower helper, and the live-subclass walk. `filters/factories.py::FilterArgumentsFactory` and `orders/factories.py::OrderArgumentsFactory` already subclass `GeneratedInputArgumentsFactory` directly and supply only the seven family hook attrs + two fresh caches; `filters/inputs.py` and `orders/inputs.py` re-export the free functions verbatim under their spec aliases (`FieldSpec` / `build_input_class` / `_camel_case` / `_iter_*set_subclasses`). Folding the two `_build_input_triples` family hooks (one appends the `and_`/`or_`/`not_` operator bag, one does not — Spec Decision 8) would re-merge the one genuinely divergent seam; net-negative. Re-consolidating a consolidation point is the canonical net-negative move this release.

## High:

None.

## Medium:

None.

## Low:

### `clear_generated_input_namespace` keyword-arg surface vs the two call sites (defer)

The clear helper takes eight keyword-only parameters (`materialized_names`, `field_specs`, `factory_module`, `factory_class_name`, `collision_registry_attr`, `set_module`, `set_class_name`). Both call sites (`filters/inputs.py #"clear_generated_input_namespace("` and `orders/inputs.py #"clear_generated_input_namespace("`) pass the same shape with only the family-specific module/class/attr strings differing. This is correct as-is — the parameters are heterogeneous string identifiers, not a repeated literal bundle, and a frozen `ClearSpec` dataclass would only relocate the spelling without removing it. Defer until a third set family lands (a third call site repeating the exact eight-kwarg shape); collapse the three through a shared `ClearSpec` then.

### `_build_input_triples` `NotImplementedError` is a silent-at-rest abstract hook (no-action)

The base declares `_build_input_triples` as `raise NotImplementedError  # family hook` rather than `@abc.abstractmethod`. Because `GeneratedInputArgumentsFactory` is never instantiated directly (only the two concrete subclasses are) and `__init_subclass__` already rejects grand-subclasses, an instantiable subclass that forgets to override the hook would raise `NotImplementedError` loudly at first `arguments` read, at the call site, with a clear traceback. No silent/late failure path exists, so this is message-quality only and not worth an `abc` conversion that would add an import and a metaclass interaction with the existing `__init_subclass__`. No action; recorded for audit.

## What looks solid

### DRY recap

- **Existing patterns reused.** Cycle-safe best-effort import via `_safe_import` (`utils/inputs.py #"def _safe_import"`) reused by both lookups inside `clear_generated_input_namespace`; the live-subclass walk `iter_set_subclasses` (`utils/inputs.py #"def iter_set_subclasses"`) is the single BFS-over-`__subclasses__` used by the clear lifecycle and re-exported as `_iter_filterset_subclasses` / `_iter_orderset_subclasses`. The binding-state attr names are read from `sets_mixins.py::SetLifecycleAttrs.binding_attrs` (`sets_mixins.py:296`) rather than re-spelled, so owner/cache/guard slot names live in one place per family (`docs/feedback.md` Major 3). `ConfigurationError` (`exceptions.py`) is the single collision exception type across both the materialization ledger and the BFS registry.
- **New helpers considered.** A `ClearSpec` dataclass to collapse the eight-kwarg clear surface — rejected/deferred (see Low; only two call sites, trigger = third family). An `abc.abstractmethod` for `_build_input_triples` — rejected (see Low; loud-at-call-site, `__init_subclass__` already gates instantiable-subclass shape).
- **Duplication risk in the current file.** The two collision-error message bodies (`materialize_generated_input_class #"is materialized by two distinct"` and `_ensure_built #"is claimed"`) share the tail `". Rename one"` + `"so its class-derived input type name is unique."` (the 2x repeated literals the static overview flags). These are two DIFFERENT failure modes — duplicate module-global materialization under one name vs two distinct sets claiming one BFS type name — phrased as distinct human-readable diagnostics, not a dispatch key. Sharing the tail string would couple two independently-evolvable error messages; intentional sibling design, correct to leave.

### Other positives

- **BFS correctness.** `_ensure_built` uses a FIFO `pending.pop(0)` queue with an enqueue-time `target not in seen` gate plus a pop-time `if set_cls in seen: continue` guard, so `A -> B -> A` cycles terminate and each set builds exactly once. Cycle handling, double-enqueue dedupe, and the deterministic breadth-first order are all pinned (`tests/filters/test_factories.py::test_filter_arguments_factory_bfs_handles_cycle`, `::test_filter_arguments_factory_dedupes_target_enqueued_twice`; `tests/orders/test_factories.py::test_factory_handles_cycles_via_seen_set`, `::test_factory_dedupes_double_enqueued_target_via_seen_check`).
- **Collision detection is identity-based and idempotent.** Both the ledger collision (`existing is not None` after `existing is cls` short-circuits the self-rematerialize) and the BFS collision (`existing_owner is not None and existing_owner is not set_cls`) key on object identity, so a re-walk of an already-registered root never false-positives. Both raise paths name both qualified class names + the family label. Covered on both families (`tests/filters/test_factories.py::test_filter_arguments_factory_collision_raises_on_distinct_class_with_same_name`, `tests/orders/test_factories.py::test_factory_raises_on_two_distinct_ordersets_sharing_classname`, `tests/utils/test_inputs.py::test_materialize_generated_input_class_names_family_in_collision`).
- **Cache-key correctness + mutability.** The class-derived `type_name_for()` is the single cache key, computed once in `__init__` (`self.input_type_name`) and again per-visit in `_build_class_type` via the same call on the same class object — they agree by construction. `input_object_types` and the named collision registry are mutable class-level dicts, and `__init_subclass__` rejects grand-subclassing precisely because a deeper subclass would inherit (not isolate) those mutable dicts; the base declares them annotation-only so a family that forgets to redefine fails loud. Subclass rejection pinned on both families (`tests/filters/test_factories.py::test_filter_arguments_factory_rejects_subclassing`, `tests/orders/test_factories.py::test_factory_subclass_rejected_at_class_creation_time`); cross-instance cache sharing pinned (`::test_factory_input_object_types_shared_across_factory_instances`).
- **Lazy related-class resolution.** `build_lazy_input_annotation` passes the type name as a runtime-computed string into `Annotated[input_type_name_for(set_class), strawberry.lazy(module_path)]` (NOT interpolated into a module-level literal), preserving the ForwardRef wrapping that `LazyType.resolve_type` resolves through `module.__dict__` after `finalize_django_types()` materializes the class. The `isinstance(set_class, type) and issubclass(...)` guard raises `TypeError` with family wording at the resolver-declaration site rather than schema-build time.
- **Namespace-clear lifecycle.** `clear_generated_input_namespace` only `delattr`s a binding attr `if attr in subclass.__dict__`, so a subclass that never bound tolerates the clear and an inherited base default (`_owner_definition = None`) is restored rather than masked. Materialized class objects are deliberately left parked in `__dict__` (the materialization helper overwrites in place on the next finalize; `delattr` would break a consumer's held `strawberry.lazy(...)` LazyType) — the docstring states this explicitly. `_safe_import` makes each subsystem lookup independently best-effort so a partial-load build still clears whatever is reachable. The two lookups + the `None`-in-`sys.modules` ImportError path are pinned (`tests/utils/test_inputs.py::test_safe_import_returns_none_for_unimportable_module`).
- **Two-family parameterization seams.** Every family-specific value is a class attr on the concrete factory (`_collision_registry_attr`, `_factory_label`, `_family_label`, `_rename_noun`, `_related_attr`, `_related_target_attr`) or a re-exported alias on the family `inputs` module; the base contains zero filter/order branching. The shared substrate is exercised end-to-end through real GraphQL builds on both families plus a direct cross-family parity test (`tests/utils/test_inputs.py::test_filter_and_order_families_share_one_substrate`).
- **No Django/ORM surface.** Static overview reports zero ORM markers. All `getattr`/`setattr` are duck-typed module-global / related-attr / class-attr access (the `Related*(None, ...)` placeholder skip at `_ensure_built` is guarded `target is not None`); no `_meta`, queryset, or model-instance access. No first-party family import means no import cycle (the module's stated contract, mirrored from `utils/connections.py`).

### Summary

`utils/inputs.py` is the deliberately-single-sited substrate for the filter/order generated-input subsystems and reviews as a clean consolidation point: the BFS walk, identity-based collision detection (ledger + registry), idempotent class cache, grand-subclass rejection, lazy forward-ref builder, and namespace-clear lifecycle are each implemented exactly once and parameterized by class-attr hooks rather than family branching. No High/Medium findings. Two forward-looking Lows (defer the eight-kwarg clear surface to a third family; `NotImplementedError` hook is loud-at-call-site, no action). The file is unchanged since baseline `14910230` (empty `git log 14910230..HEAD` + empty `git diff HEAD`) and ruff-clean, so this is a no-source-edit cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format --check django_strawberry_framework/utils/inputs.py` — `1 file already formatted` (COM812-formatter-conflict warning only, pre-existing config note).
- `uv run ruff check django_strawberry_framework/utils/inputs.py` — `All checks passed!`

### Notes for Worker 3
No shadow regeneration (trusted plan-time `--all` sweep at `docs/shadow/django_strawberry_framework__utils__inputs.overview.md`). Both Lows are forward-looking/no-action: (1) `ClearSpec` dataclass deferred until a third set family adds the third eight-kwarg call site; (2) `_build_input_triples` `NotImplementedError` is intentional — loud at the `arguments` call site, and `__init_subclass__` already gates instantiable-subclass shape, so no `abc` conversion. No GLOSSARY-only fix in scope (no GLOSSARY mention of any symbol in this file). No false-premise rejections.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source/test/GLOSSARY/CHANGELOG edit was made (per AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" and the active plan `docs/review/review-0_0_10.md`, which is silent on changelog entries for this item).

---

## Verification (Worker 3)

Shape #5 (no-source-edit) terminal-verify.

**Shadow-file dictum applied.** The shadow (`docs/shadow/django_strawberry_framework__utils__inputs.overview.md`) strips comments and string literals; its line numbers are not canonical. Used only to confirm control-flow shape; all line references below are original-source.

### Logic verification outcome

Re-derived every load-bearing correctness claim from LIVE source (not the artifact's prose):

- **BFS input-type generation.** `_ensure_built` (368-394): FIFO `pending.pop(0)` with pop-time `if set_cls in seen: continue` (372-373) + enqueue-time `target not in seen` gate (393). `A->B->A` terminates (A is in `seen` before it is re-reachable); each set builds exactly once via the `if target_name not in self.input_object_types` guard (387). `Related*(None, ...)` placeholder skipped by `target is not None` (393). Pinned: `tests/filters/test_factories.py::test_filter_arguments_factory_bfs_handles_cycle`, `::test_filter_arguments_factory_dedupes_target_enqueued_twice`; `tests/orders/test_factories.py::test_factory_handles_cycles_via_seen_set`, `::test_factory_dedupes_double_enqueued_target_via_seen_check` (all grep-confirmed present).
- **Identity-based collision detection.** Ledger path (`materialize_generated_input_class`): `existing is cls` self-rematerialize short-circuit (128) precedes `existing is not None` raise (130). BFS path: `existing_owner is not None and existing_owner is not set_cls` (378). Both key on object identity, so a re-walk of an already-registered root never false-positives; both raise paths name both qualified class names + family label. Pinned: `tests/filters/test_factories.py::test_filter_arguments_factory_collision_raises_on_distinct_class_with_same_name`, `tests/orders/test_factories.py::test_factory_raises_on_two_distinct_ordersets_sharing_classname`, `tests/utils/test_inputs.py::test_materialize_generated_input_class_names_family_in_collision` (grep-confirmed).
- **Stable class-derived names + cache-key correctness.** `set_class.type_name_for()` is the single key: computed in `__init__` as `self.input_type_name` (343), per-visit as `target_name` (376) and in `_build_class_type` as `type_name` (398) — same call on the same class object, agree by construction. `arguments` serves `self.input_object_types[self.input_type_name]` (357). Idempotent (subsequent reads hit the cache).
- **No cross-request mutable-state leak.** `input_object_types` + the named collision registry are class-level dicts declared annotation-only on the base (316; no default), redefined fresh per family. `__init_subclass__` (330-338) rejects any grand-subclass (`GeneratedInputArgumentsFactory not in cls.__bases__`) precisely because inherited dicts would cross-contaminate. Pinned: `::test_filter_arguments_factory_rejects_subclassing`, `::test_factory_subclass_rejected_at_class_creation_time`, `::test_factory_input_object_types_shared_across_factory_instances` (grep-confirmed).
- **Lazy related-class resolution.** `build_lazy_input_annotation` passes a runtime-computed string into `Annotated[input_type_name_for(set_class), strawberry.lazy(module_path)]` (174) — NOT a module-level literal — so the ForwardRef wrapping that `LazyType.resolve_type` resolves via `module.__dict__` holds. Misuse guard `isinstance(set_class, type) and issubclass(...)` raises `TypeError` at the resolver-declaration site (171-172).
- **Namespace-clear lifecycle.** `delattr` only `if attr in subclass.__dict__` (273) so an inherited base default is restored, not masked; materialized class objects deliberately left parked (docstring 240-245); `_safe_import` makes each subsystem lookup independently best-effort. Pinned: `::test_safe_import_returns_none_for_unimportable_module`.

### DRY findings disposition

DRY None is sound — genuine consolidation point, re-consolidating would be net-negative. Verified by grep: exactly 2 clear call sites (`filters/inputs.py:875`, `orders/inputs.py:383`) and exactly 2 direct factory subclasses (`FilterArgumentsFactory`, `OrderArgumentsFactory`); `binding_attrs` single-sourced at `sets_mixins.py::SetLifecycleAttrs.binding_attrs` (sets_mixins.py:296). Both Lows forward-looking:
- **L1 (ClearSpec)** gated on a *third* set family adding a third 8-kwarg call site — only 2 sites exist by grep, so genuinely deferred; the params are heterogeneous string identifiers, not a repeated literal bundle. No source-site TODO owed (gated on a future family, not a staged framework slice).
- **L2 (`NotImplementedError` hook)** verbatim trigger present at `utils/inputs.py:417` (`raise NotImplementedError  # family hook`). No-action: loud at the `arguments` call site, and `__init_subclass__` already gates instantiable-subclass shape, so an `abc` conversion buys message-quality only.
Neither Low is a GLOSSARY-only fix (no GLOSSARY mention of any symbol in this file).

### Temp test verification

None — no behavior suspicion required isolation; all claims statically decidable from source + grep-confirmed existing tests.

### Verification outcome

`cycle accepted; verified`.

Zero-edit proof (per-item): `git diff HEAD -- django_strawberry_framework/utils/inputs.py` empty; `git log 14910230..HEAD -- <target>` empty; last-touch `edab6806` (2026-06-13) predates HEAD `58ca2def` (prompt baseline `14910230` stale — content verified by source-read + grep, not SHA). Worker 2 sections each open `Filled by Worker 1 per no-source-edit cycle pattern.` Changelog `Not warranted` cites BOTH AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND active-plan silence; `git diff HEAD -- CHANGELOG.md` empty; internal-only framing honest (no public-API surface changed). Ruff format-check (`1 file already formatted`, COM812-config warning only) + `ruff check` (`All checks passed!`) pass.
