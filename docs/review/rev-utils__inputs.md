# Review: `django_strawberry_framework/utils/inputs.py`

Status: verified

## DRY analysis

- None — this module IS the cross-family DRY resolution, not a candidate for further consolidation. It single-sites the generated-input substrate (`GeneratedInputFieldSpec`, `graphql_camel_name`, `build_strawberry_input_class`, `materialize_generated_input_class`, `build_lazy_input_annotation`, `iter_set_subclasses`, `_safe_import`, `clear_generated_input_namespace`, `GeneratedInputArgumentsFactory`) that `filters/` and `orders/` re-export under spec aliases and that `mutations/inputs.py` now also consumes directly. `FilterArgumentsFactory` / `OrderArgumentsFactory` subclass `GeneratedInputArgumentsFactory` and supply only the family hook ClassVars + fresh caches; folding the two `_build_input_triples` hooks (filter appends the `and_`/`or_`/`not_` operator bag, order does not — Spec Decision 8) would re-merge the one genuinely divergent seam, net-negative. The only repeated string literals (`description` 3x in `build_strawberry_input_class`; `. Rename one` / `so its class-derived input type name is unique.` 2x across the two collision messages in `materialize_generated_input_class #"is materialized by two distinct"` and `GeneratedInputArgumentsFactory._ensure_built #"is claimed"`) are distinct collision-message bodies for two distinct collision surfaces (name-vs-class materialization clash vs name-vs-set BFS-registry clash) keyed off different objects with family-specific wording (`family_label` vs `_factory_label`/`_family_label`/`_rename_noun`). Not hoistable.

## High:

None.

## Medium:

None.

## Low:

### `clear_generated_input_namespace` eight-kwarg surface vs the (now three) call sites (defer)

The clear helper takes seven keyword-only string identifiers (`materialized_names`, `field_specs`, `factory_module`, `factory_class_name`, `collision_registry_attr`, `set_module`, `set_class_name`). The two set-family call sites (`filters/inputs.py #"clear_generated_input_namespace("` at :876, `orders/inputs.py #"clear_generated_input_namespace("` at :383) pass the same shape with only the family-specific strings differing. `mutations/inputs.py` does NOT call this helper (it owns no per-set ledger — `mutations/inputs.py` lines 26-28, 141). Correct as-is: the parameters are heterogeneous string identifiers, not a repeated literal bundle, and a frozen `ClearSpec` dataclass would only relocate the spelling. Defer until a *third clear call site* repeating the exact eight-kwarg shape lands; collapse the three through a shared `ClearSpec` then. (Note: the new mutations consumer is NOT that trigger — it deliberately bypasses the clear lifecycle.)

### `_build_input_triples` `NotImplementedError` is a loud-at-call-site abstract hook (no-action)

The base declares `_build_input_triples` as `raise NotImplementedError  # family hook` (`utils/inputs.py:417`) rather than `@abc.abstractmethod`. Because `GeneratedInputArgumentsFactory` is never instantiated directly and `__init_subclass__` already rejects grand-subclasses, an instantiable subclass that forgets to override would raise `NotImplementedError` loudly at first `arguments` read with a clear traceback. No silent/late failure path exists, so this is message-quality only and not worth an `abc` conversion that would add a metaclass interaction with the existing `__init_subclass__`. No action; recorded for audit.

## What looks solid

### DRY recap

- **Existing patterns reused.** Cycle-safe best-effort import via `_safe_import` (`utils/inputs.py #"def _safe_import"`) reused by both lookups inside `clear_generated_input_namespace`; the live-subclass walk `iter_set_subclasses` is the single BFS-over-`__subclasses__` used by the clear lifecycle and re-exported as `_iter_filterset_subclasses` / `_iter_orderset_subclasses`. Binding-state attr names are read from `sets_mixins.py::SetLifecycleAttrs.binding_attrs` (`sets_mixins.py:296`) rather than re-spelled, so owner/cache/guard slot names live in one place per family (`docs/feedback.md` Major 3). `ConfigurationError` (`exceptions.py`) is the single collision exception type across both the materialization ledger and the BFS registry.
- **New helpers considered.** A `ClearSpec` dataclass to collapse the eight-kwarg clear surface — rejected/deferred (see Low; only two clear call sites, trigger = third). An `abc.abstractmethod` for `_build_input_triples` — rejected (see Low; loud-at-call-site, `__init_subclass__` already gates instantiable-subclass shape).
- **Duplication risk in the current file.** The two collision-error message bodies share the tail `". Rename one"` + `"so its class-derived input type name is unique."` (the 2x repeated literals the static overview flags). These are two DIFFERENT failure modes — duplicate module-global materialization under one name vs two distinct sets claiming one BFS type name — phrased as distinct human-readable diagnostics with distinct family-label interpolation, not a dispatch key. Sharing the tail would couple two independently-evolvable messages; intentional sibling design, correct to leave. The `filters`/`orders` factory subclasses are likewise intentional sibling parameterizations (hook ClassVars + the `_build_input_triples` family hook).

### Other positives

- **Substrate contract held across a NEW third consumer this release.** The substrate now serves three families, not two: `mutations/inputs.py` (new in 0.0.11) imports `build_strawberry_input_class` + `graphql_camel_name` + `materialize_generated_input_class` (`mutations/inputs.py:52-54`) and deliberately bypasses the BFS factory and `build_lazy_input_annotation`/`clear_generated_input_namespace` (mutation inputs use inline strawberry types, no per-set ledger), exactly as `mutations/inputs.py` lines 26-28 state. Cross-module wiring re-grepped at source: filters (`filters/inputs.py:37-61`, `filters/factories.py:35,67`, `filters/__init__.py:19,75`), orders (`orders/inputs.py:33-52`, `orders/factories.py:26,33`, `orders/__init__.py:27,76`), mutations (`mutations/inputs.py:52-54`, `mutations/resolvers.py:88,154`). No drift between the docstring's "mechanics-only, domain semantics stay at call sites" claim and reality.
- **BFS correctness.** `_ensure_built` uses a FIFO `pending.pop(0)` queue with a pop-time `if set_cls in seen: continue` guard plus an enqueue-time `target not in seen` gate, so `A -> B -> A` cycles terminate and each set builds exactly once. Pinned: `tests/filters/test_factories.py::test_filter_arguments_factory_bfs_handles_cycle`, `::test_filter_arguments_factory_dedupes_target_enqueued_twice`; `tests/orders/test_factories.py::test_factory_handles_cycles_via_seen_set`, `::test_factory_dedupes_double_enqueued_target_via_seen_check`.
- **Identity-based, idempotent collision detection.** Ledger path: `existing is cls` self-rematerialize short-circuit precedes `existing is not None` raise; BFS path: `existing_owner is not None and existing_owner is not set_cls`. Both key on object identity (a re-walk of an already-registered root never false-positives) and name both qualified class names + family label. Pinned on both families plus `tests/utils/test_inputs.py::test_materialize_generated_input_class_names_family_in_collision`.
- **No cross-instance mutable-state leak.** `input_object_types` + the named collision registry are class-level dicts declared annotation-only on the base (no default), redefined fresh per family; `__init_subclass__` rejects grand-subclasses precisely because inherited dicts would cross-contaminate. Pinned: `::test_filter_arguments_factory_rejects_subclassing`, `::test_factory_subclass_rejected_at_class_creation_time`, `::test_factory_input_object_types_shared_across_factory_instances`.
- **Lazy related-class resolution.** `build_lazy_input_annotation` passes a runtime-computed string into `Annotated[input_type_name_for(set_class), strawberry.lazy(module_path)]` (NOT a module-level literal), preserving the ForwardRef wrapping `LazyType.resolve_type` resolves via `module.__dict__` after `finalize_django_types()`; the `isinstance`/`issubclass` guard raises `TypeError` with family wording at the resolver-declaration site.
- **Namespace-clear + import-cycle hygiene.** `delattr` only `if attr in subclass.__dict__` (inherited base default restored, not masked); materialized classes deliberately left parked in `__dict__` (`setattr` overwrites on next finalize; `delattr` would break a held `strawberry.lazy(...)` LazyType — docstring states this). `_safe_import` makes each subsystem lookup independently best-effort. No first-party family import means no cycle (the module's stated contract, mirrored from `utils/connections.py`). Zero Django/ORM markers (static overview) — all `getattr`/`setattr` are duck-typed module-global / related-attr / class-attr access.

### Summary

`utils/inputs.py` is the single-source neutral substrate for the generated-input machinery shared by the filter, order, and (new in 0.0.11) mutation families. Both `git diff 07e139b6 -- utils/inputs.py` and `git diff HEAD -- utils/inputs.py` are empty and `git log baseline..HEAD` for the file returns nothing, so there is no tracked edit this cycle — the module is settled. All cross-module wiring re-verified at source; the docstring's mechanics-only/domain-at-call-sites split holds, including for the new mutations consumer that deliberately uses only the inline-type-safe subset of helpers (and correctly omits the clear lifecycle). No `__all__`, all symbols private/dotted-path-addressed, so no GLOSSARY symbol entries are warranted (absence correct). No High/Medium findings; two forward-looking/no-action Lows; DRY is a single `None —` because the module is itself the resolution. Genuine no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (`289 files left unchanged`; COM812-formatter-conflict config warning only, pre-existing).
- `uv run ruff check --fix .` — pass (`All checks passed!`).

### Notes for Worker 3
- No GLOSSARY-only fix in scope: the module exports no `__all__`; every symbol is private/dotted-path-addressed and carries no GLOSSARY symbol entry (absence correct). The only GLOSSARY `inputs`-adjacent prose (`strawberry_config` kwarg forwarding, GLOSSARY:1292/1297) belongs to a different module and is unaffected.
- Both Lows forward-looking / no-action: (L1) `ClearSpec` deferred until a *third* eight-kwarg clear call site — grep confirms exactly two (`filters/inputs.py:876`, `orders/inputs.py:383`); the new mutations consumer is NOT a clear call site. (L2) `_build_input_triples` `NotImplementedError` (`utils/inputs.py:417`) is intentional — loud at the `arguments` call site, `__init_subclass__` already gates instantiable-subclass shape. No source-site TODO owed (gated on a future family, not a staged framework slice).
- Cross-module wiring re-grepped at source (filters/orders/mutations consumers) — intact and matching the module docstring; no drift. No false-premise rejections.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits — the module docstring's mechanics-only/domain-at-call-sites split, the `make_dataclass` rationale (`build_strawberry_input_class`), the parked-class `delattr` rationale (`clear_generated_input_namespace`), and the `__subclasses__()` test-isolation note (`iter_set_subclasses`) all read accurate against the implementation and against the new third (mutations) consumer.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source/test/GLOSSARY/CHANGELOG edit was made this cycle (`AGENTS.md` #"Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_11.md` is silent on changelog entries for this item).

---

## Verification (Worker 3)

### Logic verification outcome
Genuine no-source-edit (shape #5). Zero-edit proof clean on all axes: `git diff 07e139b6 -- utils/inputs.py` empty, `git diff HEAD -- utils/inputs.py` empty, `git log 07e139b6..HEAD -- utils/inputs.py` empty, owned-paths stat (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) empty, `git diff -- CHANGELOG.md` empty — so no sibling-cycle attribution needed and the "Files touched: None" claim holds. All three Worker 2 sections open with "Filled by Worker 1 per no-source-edit cycle pattern."

High/Medium both `None.` — independently confirmed genuine: the substrate is the cross-family DRY resolution itself, not a fix candidate. Spot-checked the contract: `build_strawberry_input_class` (type()+annotations preserves the strawberry.field name= metadata that make_dataclass would strip); `materialize_generated_input_class` (`existing is cls` idempotent short-circuit precedes `existing is not None` raise, ConfigurationError names both qualnames + family_label); `build_lazy_input_annotation` (runtime-string into `Annotated[..., strawberry.lazy()]`, isinstance/issubclass TypeError guard); `clear_generated_input_namespace` (delattr only `if attr in subclass.__dict__`, materialized classes left parked); the BFS factory base (`__init_subclass__` rejects grand-subclasses; `_ensure_built` FIFO pop(0) with pop-time seen-guard + enqueue-time not-in-seen gate → cycles terminate; identity-based collision check).

New mutations consumer correctly bypasses BFS factory / lazy annotation / per-set ledger: `grep` of `mutations/inputs.py` imports exactly three helpers (`build_strawberry_input_class`, `graphql_camel_name`, `materialize_generated_input_class` at :52-54) and does NOT import/call `build_lazy_input_annotation`, `clear_generated_input_namespace`, or subclass `GeneratedInputArgumentsFactory`. The docstring at :26-28 and :141-145 states the rationale verbatim (mutation inputs derive from one model's editable columns, not a related-set BFS; no `_lifecycle` binding state; `clear_mutation_input_namespace` reuses the *pattern*, not the helper). No GLOSSARY drift — no `__all__`, all symbols private/dotted-path-addressed, zero GLOSSARY symbol entries (absence correct → genuine #5, not a missed #4).

`clear_generated_input_namespace` count is still 2: `grep -rn "clear_generated_input_namespace("` returns the def (`utils/inputs.py:215`) + exactly two call sites (`filters/inputs.py:876`, `orders/inputs.py:383`). The mutations consumer is NOT a third call site, so the `ClearSpec` defer trigger has not fired.

Both Lows genuinely forward-looking:
- **L1 (`ClearSpec` 8-kwarg surface defer):** trigger is a *third* clear call site repeating the eight-kwarg shape — confirmed exactly two exist; mutations deliberately bypasses the clear lifecycle (`clear_mutation_input_namespace` owns its module-level ledger and does not delegate). No-action, deferred with verbatim trigger.
- **L2 (`_build_input_triples` `NotImplementedError`):** present at `utils/inputs.py:417` (`raise NotImplementedError  # family hook`). Loud-at-call-site abstract hook; `__init_subclass__` already gates instantiable-subclass shape; an `abc` conversion would add a metaclass interaction with the existing `__init_subclass__`. No-action, recorded for audit.

### DRY findings disposition
DRY-None is genuine — this module IS the cross-family DRY resolution. The two repeated collision-message tails (". Rename one" / "so its class-derived input type name is unique.") are two DIFFERENT failure modes (name-vs-class materialization clash vs name-vs-set BFS-registry clash) with family-specific interpolation — sharing the tail would couple two independently-evolvable diagnostics. The filter/order factory subclasses are intentional sibling parameterizations (hook ClassVars + the `_build_input_triples` family hook, divergent per Spec Decision 8). Both candidate helpers (`ClearSpec`, `abc.abstractmethod`) correctly rejected/deferred. Nothing forwarded.

### Temp test verification
None — no behavior suspicion to prove; this is a no-source-edit re-review of a settled substrate. No temp tests created.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.

Changelog "Not warranted" cites BOTH required sources (AGENTS.md + active-plan silence) and the internal-only framing matches the (empty) diff scope. Ruff format-check (`1 file already formatted`) + `ruff check` (`All checks passed!`) pass.
