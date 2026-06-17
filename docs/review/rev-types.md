# Review: `django_strawberry_framework/types/` (folder pass)

Status: verified

## DRY analysis

- None at folder scope — every cross-sibling candidate the dispatch raised resolves to "already single-sourced or deliberately distinct." Specifics:
  - **Meta-key vocabulary is single-sourced in `base.py`.** `DEFERRED_META_KEYS` (`base.py:63`), `ALLOWED_META_KEYS` (`base.py:67`), `RELATION_SHAPE_VALUES`/`DEFAULT_RELATION_SHAPE` (`base.py:98-99`), `STRING_GLOBALID_STRATEGIES`/`DEFAULT_GLOBALID_STRATEGY` (`base.py:122-123`). No sibling re-declares any of them — `relay.py` imports `DEFAULT_GLOBALID_STRATEGY`/`STRING_GLOBALID_STRATEGIES` in-function (`relay.py:385`, cycle-dodge), and `definition.py`/`finalizer.py` consume `DEFERRED_META_KEYS` by import. No folder-level Meta-key literal duplication to fold.
  - **`relay.py`'s `MODEL_LABEL_STRATEGIES`/`TYPE_NAME_STRATEGIES` (`relay.py:413-414`) are NOT a duplicate of `base.py`'s `STRING_GLOBALID_STRATEGIES`.** They are payload-shape decode-acceptance memberships (a partition of the strategy space, not the strategy enum), centralized once and consumed cross-file by `filters/base.py`. The shared `"type+model"` literal across the two relay frozensets is the whole point of the partition, not a hoistable constant — see `rev-types__relay.md`.
  - **resolvers DRY twin stays file-local and deferred.** The `<name> in getattr(root, "__dict__", {})` loaded-signal probe appears at exactly N=2, both inside `resolvers.py` (`resolvers.py:89` `_fk_attname_is_deferred`, `resolvers.py:136` `_will_lazy_load_single`). Folder-wide grep confirms zero sibling adds a third site, so this does NOT promote to a folder-level act-now item — the divergent tails (`get_deferred_fields()` column-deferral cache vs `_state.fields_cache` relation-instance cache) answer two different questions over two different Django caches. Carry the per-file deferral verbatim: **"Defer until a third caller needs the bare `__dict__` loaded-signal; only then extract `def _attr_in_instance_dict(root, name) -> bool` for the first line of both."**

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The folder fans inward to one set of canonical surfaces, no parallel re-implementations: `scalar_for_field` (`converters.py:119`) is the lone field-class→scalar lookup (the filter-input side delegates to it via local import, not a second map); `origin_has_custom_id_resolver` (`definition.py`) is the deliberately-extracted anti-drift id-resolver predicate shared by the memoized hot path and the optimizer's definition-less fallback; `finalizer.py` is the single owner-bind / sidecar-driver consolidation point (`_bind_set_owner_common`, `_bind_sidecar_sets` + frozen `_SidecarBindingSpec`); `relay.py` holds the single GlobalID validator (`_validate_globalid_strategy`, one rule two sources) and the single name→default table (`_RELAY_RESOLVER_DEFAULTS`). `FieldMeta` shape-construction in `resolvers.py` routes through the canonical `FieldMeta.from_django_field` so the resolver's relation-kind classification cannot drift from the walker's. Field-name resolution is single-channel folder-wide: `field_map[snake_case(name)]` (base.py ×2, finalizer.py ×2) uses the canonical `utils/strings.snake_case` against the canonical `field_map` — same lookup at every site, not duplicated logic.
- **New helpers considered.** No folder-level helper warranted. The only cross-sibling near-twin in scope is the resolvers `__dict__`-probe pair, evaluated and correctly deferred to N=3 (file-local, no sibling third site). The per-family `_format_*` error helpers in `finalizer.py` and the heterogeneous-body id-resolver chain in `definition.py` were each rejected for folding inside their own files (distinct consumer vocabulary / distinct detection strategies) and there is no cross-file variant of either to merge.
- **Duplication risk in the folder.** The strategy/shape string literals (`"model"`, `"type"`, `"type+model"`, `"list"`, `"connection"`, `"both"`) recur across `base.py` and `relay.py` but are each membership content of a single named frozenset defined once and imported/consumed elsewhere — not repeated dispatch keys. The `f"{model.__name__}.Meta..."` message prefixes recur across validators by design (distinct constraints, distinct remediation), per `rev-types__base.md`/`rev-types__converters.md`. Per-cycle-baseline cross-check: the spec-035 changes (`definition.py` inert `fields_class` slot, `resolvers.py` FK-elision guard + L3 threading) added no new cross-sibling literal or helper — they are self-contained within their owning files.

### Other positives

- **Internal structure stayed coherent through spec-035.** The three post-baseline commits (`cf9202f5` `fields_class` slot, `8866fcea` spec-035 Decision 5, `79b74b46` permission-target consolidation / `_is_fk_id_elided` inline) are all in HEAD and touch only `definition.py` + `resolvers.py`; `git diff --stat HEAD -- django_strawberry_framework/types/` is empty (folder byte-identical to HEAD). The `fields_class` slot is inert (rejected via `DEFERRED_META_KEYS`, no populator) and the FK-elision guard's correctness was independently re-traced against the walker invariant in `rev-types__resolvers.md`. No responsibility leaked between siblings as a result.
- **Responsibility boundaries are clean.** `base.py` orchestrates Meta validation + annotation synthesis; `converters.py` owns all field-shape introspection (so base stays focused); `definition.py` is the pure metadata record + id-resolver predicates; `finalizer.py` is the call-time pipeline (zero import-time side effects); `relations.py` is pure data scaffolding; `relay.py` is the GlobalID + resolver-injection machinery; `resolvers.py` is resolve-time access (imports nothing from `base.py` — invariant grep-confirmed). No misplaced helper, no overlapping ownership.
- **Import direction is one-way and acyclic.** Intra-folder top-level imports form a DAG: `__init__` → {base, finalizer, relay}; `base` → {converters, definition, relations, relay}; `finalizer` → {converters, relations, relay, resolvers}. The `base ↔ relay` and `definition ↔ registry` cross-references are function-local cycle-dodges documented at each site. No `optimizer/ → types/` top-level back-edge (only the sanctioned in-function `walker.py` leaf read documented in `types/__init__.py`). No circular-import risk introduced at folder scope.
- **`types/__init__.py` exports are exactly the public surface.** `__all__ = ("DjangoType", "SyncMisuseError", "finalize_django_types")` (`types/__init__.py:35`) — the three documented public exports, each re-exported from its owning sibling (`base`/`relay`/`finalizer`). Internal helpers (`convert_scalar`, `convert_choices_to_enum`, `_attach_relation_resolvers`, etc.) are intentionally NOT surfaced here, only reachable by dotted submodule path. The docstring documents the dependency-direction contract and the dotted-path-convenience rationale. No premature future surface, no over-export.
- **Comment/error-handling consistency across siblings.** Every sibling routes config errors through `ConfigurationError` with model/Meta-qualified messages; every cycle-dodge import carries a "Do NOT hoist" comment naming the exact cycle; the static overviews report zero stale TODOs across the folder. No naming or error-handling drift between siblings.

### Summary

`django_strawberry_framework/types/` is a coherent, single-responsibility-per-module subsystem with all seven sibling per-file artifacts `verified`. The folder is byte-identical to HEAD (`git diff --stat HEAD -- types/` empty); the spec-035 changes (`definition.py` inert `fields_class` slot, `resolvers.py` FK-elision guard + L3 threading) are already in HEAD and self-contained within their owning files — no responsibility leaked, no new cross-sibling literal or helper. The dispatch's three cross-file concerns all resolve cleanly: (1) the resolvers `__dict__`-probe DRY twin is N=2 file-local with divergent tails over two distinct Django caches — stays deferred-with-trigger to N=3, not a folder act-now; (2) the spec-035 structure stayed coherent; (3) Meta-vocabulary constants are single-sourced in `base.py` with no sibling re-declaration, and `relay.py`'s strategy frozensets are a distinct payload-shape partition, not a duplicate. `__init__.py` exports exactly the three public symbols (`DjangoType`, `SyncMisuseError`, `finalize_django_types`); import direction is one-way and acyclic. No High, Medium, or Low folder-level findings. No-findings folder pass with zero source edits — shape #3 → #5.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; `270 files left unchanged`.
- `uv run ruff check .` — pass; `All checks passed!`.

### Notes for Worker 3
- No-findings folder pass (shape #3 → #5). All seven sibling per-file artifacts are `verified`; `types/` is byte-identical to HEAD (`git diff --stat HEAD -- django_strawberry_framework/types/` empty). Zero edits to any tracked file.
- Dispatch forward items, all dispositioned at folder scope with no action:
  - resolvers DRY twin (`_will_lazy_load_single` / `_fk_attname_is_deferred`): N=2, both in `resolvers.py`, no sibling third site — stays deferred-with-trigger ("until a third caller needs the bare `__dict__` loaded-signal"). NOT promoted to folder act-now.
  - spec-035 `definition.py`/`resolvers.py` changes: confirmed self-contained, folder structure coherent.
  - Meta-vocabulary constants: single-sourced in `base.py`; no sibling re-declares; `relay.py` strategy frozensets are a distinct payload-shape partition, not a duplicate.
- `__init__.py` exports verified: `__all__` = the three public symbols only; one-way acyclic import direction; no optimizer→types top-level back-edge.
- No GLOSSARY-only fix in scope — sibling artifacts already verified GLOSSARY consistency per symbol; no folder-level prose drift.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No source edits, so no comment/docstring changes. The `types/__init__.py` module docstring (dependency-direction contract, dotted-path-convenience rationale, internal-helpers-not-exposed note) is accurate against the source and the sibling artifacts; no stale comment or over-promising docstring at folder scope.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source/test change occurred (read-only folder pass over a folder byte-identical to HEAD). Cited authority: AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_10.md` is silent on changelog edits for this item.

---

## Verification (Worker 3)

### Logic verification outcome
No-findings folder pass (shape #5). Zero High/Medium/Low at folder scope — nothing to address or reject. All four load-bearing folder claims independently re-derived from live source (not the artifact's prose):

- **(a) `__all__` is exactly the 3 public exports.** `types/__init__.py:35` `__all__ = ("DjangoType", "SyncMisuseError", "finalize_django_types")`, each re-exported from its owning sibling (`base.py:31`, `finalizer.py:32`, `relay.py:33`). No over-export; internal helpers stay dotted-path-only.
- **(b) Intra-folder import graph is acyclic; no `optimizer↔types` top-level cycle.** Top-level intra-folder DAG read from each sibling's import block: `__init__`→{base,finalizer,relay}; `base`→{converters,definition,relations,relay}; `finalizer`→{converters,relations,relay,resolvers}; `converters`/`definition`/`relations`/`relay`/`resolvers` have NO top-level intra-folder import. `resolvers.py` imports nothing from `base.py` (invariant holds). The `base↔relay` cross-ref is one-way at top level (`base→relay` only); `relay→base` is function-local (`relay.py:384`, inside the fn at :377, documented). `definition↔registry` cycle-dodge is function-local (`definition.py:235`, documented at :230-231). Package-wide grep: **NO top-level `optimizer→types` back-edge** — the sole `optimizer→types` edge is function-local `walker.py:919 → ..types.definition` (the sanctioned leaf read); `selections.py:101` is `strawberry.types.nodes`, not the package's `types/`.
- **(c) resolvers DRY is genuinely N=2-confined and correctly deferred.** Package-wide grep of the `<name> in getattr(root, "__dict__", {})` loaded-signal probe returns exactly 2 hits, both in `resolvers.py` (`:89` `_fk_attname_is_deferred`, `:136` `_will_lazy_load_single`); each helper defined once; zero sibling third site. Deferral-to-N=3 sound: the divergent tails read two distinct Django caches (column-deferral via `get_deferred_fields()` vs relation-instance via `_state.fields_cache`), so folding now conflates two questions. Not a dodged folder act-now.
- **(d) Meta-vocabulary literals genuinely single-sourced in `base.py`.** All six constants defined exactly once, all in `base.py` (`DEFERRED_META_KEYS:63`, `ALLOWED_META_KEYS:67`, `RELATION_SHAPE_VALUES:98`, `DEFAULT_RELATION_SHAPE:99`, `STRING_GLOBALID_STRATEGIES:122`, `DEFAULT_GLOBALID_STRATEGY:123`). No sibling re-declares any. `relay.py` imports `DEFAULT_GLOBALID_STRATEGY`/`_validate_globalid_strategy` in-function (`:384`). `relay.py`'s `MODEL_LABEL_STRATEGIES`/`TYPE_NAME_STRATEGIES` (`:413-414`) are distinctly-named payload-shape decode-acceptance partitions, not a re-declaration of the strategy enum — the shared `"type+model"` literal is membership content, not a hoistable dispatch key.

### DRY findings disposition
DRY = None at folder scope, accepted. The single cross-sibling near-twin (resolvers `__dict__`-probe pair) is N=2 file-local with divergent cache tails — carried forward verbatim with the in-source N=3 trigger, not promoted. `relay.py` strategy frozensets confirmed a distinct partition (cross-checked by name + literal), not a duplicate. No folder-level helper warranted.

### Temp test verification
- None used. All four claims are statically grep-/read-decidable; no behavior question required a temp test. No source edit introduced a test, so no pytest run warranted.
- Disposition: n/a.

### Shape #5 (no-source-edit) checklist
- `git diff HEAD -- django_strawberry_framework/types/` empty; `--stat` empty; `git diff -- CHANGELOG.md` empty (last folder touch `8866fcea`, in HEAD). Per-item zero-edit proof holds.
- Each Worker 2 section opens `Filled by Worker 1 per no-source-edit cycle pattern.` (Fix report :48, Comment/docstring :73, Changelog :79).
- Zero Lows → no verbatim-trigger requirement; no GLOSSARY-only fix in scope.
- Changelog `Not warranted` cites BOTH AGENTS.md #21 AND active-plan (`review-0_0_10.md`) silence; framing honest (read-only pass, no public-API surface changed).
- `uv run ruff format --check django_strawberry_framework/types/` — 8 files already formatted; `uv run ruff check` — All checks passed.
- All seven sibling per-file artifacts confirmed `Status: verified` with `[x]` boxes (review-0_0_10.md:112-118).

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `types/` folder-pass checklist box (review-0_0_10.md:119).

---

## Iteration log

(none)
