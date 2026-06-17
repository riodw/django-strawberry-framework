# Review: `django_strawberry_framework/types/definition.py`

Status: verified

## DRY analysis

- None — this module IS the single source for `DjangoTypeDefinition` metadata and its id-resolver predicate family. `origin_has_custom_id_resolver` (`definition.py::origin_has_custom_id_resolver`) is already the deliberately-extracted shared helper that both the memoized hot path (`DjangoTypeDefinition.has_custom_id_resolver_for`) and the optimizer's definition-less fallback call, so the two cannot drift (docstring at `definition.py:300-305` states this contract explicitly). The four-helper id-resolver chain (`origin_has_custom_id_resolver` -> `_class_has_custom_id_resolver` / `_resolves_id_off_pk` -> `_is_framework_relay_id_resolver`) is heterogeneous-body decomposition (MRO scan vs NodeID-annotation check vs framework-default identity test), not near-copies; folding any pair would merge distinct detection shapes behind one signature. The two repeated literals the static overview flags (`"resolve_id"` x2, `"__func__"` x2) are a name-string the guard tests against plus a dunder attribute read — neither is a dispatch key worth hoisting at N=2.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `origin_has_custom_id_resolver` (`definition.py::origin_has_custom_id_resolver`) is the canonical shared id-resolver predicate consumed by both `DjangoTypeDefinition.has_custom_id_resolver_for` (`definition.py:294`) and the optimizer's definition-less fallback — extracted precisely so they cannot diverge. `graphql_type_name` (`definition.py::DjangoTypeDefinition.graphql_type_name`) centralizes the `self.name or self.origin.__name__` derivation that would otherwise be three inline copies in `finalizer.py` / `filters/base.py` / `filters/inputs.py` (its docstring names them). Field-name normalization for `relation_connections` lookups reuses the SAME `snake_case(sel.name)` the `field_map` lookup uses (docstring `definition.py:99-100`), so walker resolution stays single-channel.
- **New helpers considered.** Folding the four id-resolver helpers into one — rejected; bodies are distinct detection strategies (MRO class-attr scan, NodeID-off-pk check, framework-default identity). Hoisting `"resolve_id"` / `"__func__"` to module constants — rejected at N=2; not dispatch keys.
- **Duplication risk in the current file.** The two memoization caches (`_related_target_cache`, `_custom_id_resolver_cache`) follow the same `dict default_factory, repr=False, membership-not-get` shape but key different value spaces (full `(target_definition, model_field) | None` tuples vs `bool`) and gate on different stability signals (`registry.is_finalized()` vs always-stable MRO/annotation inputs) — intentional sibling design, correctly NOT a shared abstraction. Both correctly use membership checks so a cached `None`/`False` is a valid answer (documented `definition.py:184-185`, `194-195`).

### Other positives

- **The spec-035-window change (`cf9202f5`, +6 lines) is correct and well-grounded.** The dispatch framed it as "spec-035 optimizer-hardening", but the actual single commit in `14910230..HEAD` adds the `fields_class` forward-reserved sidecar slot (5 docstring lines `definition.py:64-68` + the field `definition.py:161`). It is a genuinely inert slot: `fields_class` sits in `DEFERRED_META_KEYS` (`types/base.py:64`), so `Meta.fields_class` is rejected at validation (`types/base.py:1070`), the slot has no populator, and it stays `None` until `TODO-BETA-046-0.1.1`. spec-034 Decision (line 220) confirms the same — "no populator this card... Reserving the slot is the only `definition.py` change." This is the structural mirror of the shipped `filterset_class` / `orderset_class` slots, NOT a premature future surface (no `__all__` change, no import of an unshipped symbol) — the opposite of the AGENTS.md "don't preempt future-feature settings" hazard.
- **GLOSSARY consistent, no drift.** `Meta.fields_class` is "planned for `0.1.1`" at `docs/GLOSSARY.md:95` and `:686-692`, exactly matching the slot's `None`-until-`0.1.1` docstring and the `DEFERRED_META_KEYS` membership. The `TODO-BETA-046-0.1.1` anchor matches `docs/TREE.md:274`.
- **`related_target_for` cache safety is correctly gated.** Caching only when `registry.is_finalized()` (`definition.py:247`) avoids locking in a transient pre-finalize `None` while the registry can still gain `DjangoType`s — the documented hazard at `definition.py:241-246`. All four registry methods it relies on exist (`registry.is_finalized` `:427`, `registry.get` `:221`, `registry.get_definition` `:346`, `registry.primary_for` `:268`).
- **In-function imports correctly break the `definition -> registry -> definition` load cycle** (`definition.py:230-235`), with a "Do NOT hoist" comment naming the exact cycle. The strawberry-relay imports in `_resolves_id_off_pk` / `_is_framework_relay_id_resolver` are likewise deferred, keeping module-load side-effect-free.
- **Reflective access is all justified.** Every `getattr` carries a safe default (`is_relation` False, `related_model` None, `__mro__` (), `__dict__` {}, `__func__` falling back to the value itself); `FieldDoesNotExist` is caught and mapped to `None`; `NodeIDAnnotationError` is caught and treated as "no NodeID -> resolves to pk -> safe". The `isinstance(origin, type) and issubclass(origin, relay.Node)` guard short-circuits before `issubclass` can throw on a non-class.
- **`_meta.get_field` is the only ORM marker** and is wrapped in the documented try/except; no queryset construction, no request-state, no `select_related`/`prefetch_related` here — this is a pure metadata record plus two read-only memoized lookups.

### Summary

Pure metadata dataclass (`DjangoTypeDefinition`) plus its id-resolver predicate family; no schema build, no ORM query construction, no request-scope state. The only post-baseline change (`cf9202f5`) adds the inert `fields_class` forward-reservation slot — verified inert via `DEFERRED_META_KEYS` rejection and the spec-034 / GLOSSARY / TREE cross-references, and it correctly mirrors the shipped sibling slots without preempting any public surface. The this-cycle diff against HEAD is empty. DRY factoring is already at its single-source shape (the `origin_has_custom_id_resolver` extraction is the canonical anti-drift move). No High / Medium / Low findings.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 270 files left unchanged.
- `uv run ruff check --fix .` — pass; All checks passed.

### Notes for Worker 3
- No-source-edit cycle (shape #5). This-cycle diff `git diff HEAD -- django_strawberry_framework/types/definition.py` is empty; the spec-window change `cf9202f5` (`fields_class` slot, +6 lines) is already in HEAD and was reviewed against current source.
- Change-context note: the dispatch labeled this "spec-035 optimizer-hardening", but the only commit in `14910230..HEAD` for this file is the `fields_class` forward-reservation slot — verified inert (no populator; `DEFERRED_META_KEYS` rejection at `types/base.py:64`/`:1070`; spec-034 Decision line 220).
- No GLOSSARY-only fix in scope — `docs/GLOSSARY.md:95`/`:686-692` already states `Meta.fields_class` "planned for `0.1.1`", consistent with the slot.
- All severities `None.` — no per-finding dispositions to carry.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

The class docstring invariant block (`definition.py:64-68`) and the field comment region were both reviewed; they accurately describe the inert slot and cross-reference `DEFERRED_META_KEYS` and `TODO-BETA-046-0.1.1`. No stale comments, no docstrings promising unimplemented behavior, no obsolete TODOs (static overview reports 0 TODO comments). No comment edits warranted.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source/test edits this cycle (AGENTS.md #21 "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_10.md` is silent on changelog edits for this item).

---

## Verification (Worker 3)

Shadow caveat applied: the shadow strips `#` comments and replaces string-literal tokens with `...`, so its line numbers are non-canonical; original `definition.py` line numbers and this artifact's references are treated as canonical. The shadow was used only to corroborate control flow / symbol inventory.

### Logic verification outcome
No-source-edit cycle (shape #5). All severities `None.` — no per-finding dispositions to verify. The substantive verification is the `fields_class` inert verdict and the soundness of the existing `DjangoTypeDefinition` construction:

- **`fields_class` slot is genuinely INERT — verified independently, NOT a premature-surface defect.**
  - IS in `DEFERRED_META_KEYS`: `types/base.py:64` `frozenset({"aggregate_class", "fields_class", "search_fields"})`.
  - `Meta.fields_class` IS rejected at validation: `_validate_meta` computes `deferred = sorted(declared & DEFERRED_META_KEYS)` (`base.py:1070`) and raises `ConfigurationError("Meta keys not supported yet: [...]. The feature that owns them has not shipped.")` (`:1071-1074`); `fields_class` is also absent from `ALLOWED_META_KEYS` (`:67-85`).
  - No populator: whole-package `grep -rn "fields_class"` returns ONLY the docstring (`definition.py:64,66`), the slot itself (`:161`), the `DEFERRED_META_KEYS` membership (`base.py:64`), and the deferred-surface error message (`exceptions.py:26`). Zero assignment site — no `__init_subclass__` populator, no `definition.fields_class =` anywhere. Slot stays `None` until `TODO-BETA-046-0.1.1`.
  - Structural mirror, not preemption: `fields_class: type | None = None` (`:161`) sits directly under shipped `filterset_class`/`orderset_class` (`:159-160`), same shape; no `__all__` change, no import of an unshipped symbol. This is the inverse of the AGENTS.md #20 "don't preemptively populate future-feature surfaces" hazard (a reserved-but-rejected slot, not an active surface). GLOSSARY ("planned for 0.1.1") is consistent.
- **`+6` change matches exactly**: `git diff 14910230..HEAD` for this file shows 5 docstring lines (`:64-68`) + the one field (`:161`) added by `cf9202f5` — and nothing else. (The dispatch's "spec-035" label is cosmetic drift; the single commit is the `fields_class` reservation.)
- **Rest of the definition is sound.** `related_target_for` caches only post-`registry.is_finalized()` (`:247-249,274-275`) avoiding a locked-in transient `None`; membership-not-`get` semantics for both caches (`:248,291`) keep `None`/`False` valid cached answers. In-function imports (`:233-235`) break the `definition→registry→definition` load cycle (Do-NOT-hoist comment). Reflective access all carries safe defaults; `FieldDoesNotExist`/`NodeIDAnnotationError` caught and mapped to None/safe; `isinstance(origin, type) and issubclass(...)` short-circuits before `issubclass` can throw (`:330`). DRY at single-source shape: `origin_has_custom_id_resolver` is the lone shared id-resolver predicate (one `def`), the four-helper chain is heterogeneous-body decomposition, the two N=2 repeated literals are not dispatch keys.

### DRY findings disposition
Artifact `## DRY analysis` = None, with reasoned rejection of the two candidate folds (four id-resolver helpers; `"resolve_id"`/`"__func__"` literals). Independently confirmed: `grep "def origin_has_custom_id_resolver"` = exactly one def; folding the helpers would merge distinct detection shapes (MRO scan / NodeID-off-pk / framework-default identity). No carry-forward.

### Temp test verification
None — no behavioral suspicion required a temp test; inert verdict and DRY claims are grep-decidable from source.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `types/definition.py` checklist box in `docs/review/review-0_0_10.md`.

Shape #5 terminal checklist: (a) `git diff HEAD -- django_strawberry_framework/types/definition.py` empty + this-cycle owned-path diff clean; (b) each Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.`; (c) all severities `None.`, no Low requiring trigger phrasing, no GLOSSARY-only fix; (d) changelog `Not warranted` cites BOTH AGENTS.md #21 AND active-plan silence, and `git diff -- CHANGELOG.md` empty; (e) ruff format `--check` = "1 file already formatted", ruff check = "All checks passed!".
