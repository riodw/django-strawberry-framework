# Review: `django_strawberry_framework/types/` (folder pass)

Status: verified

## DRY analysis

- None at folder scope — every cross-sibling candidate the dispatch raised resolves to "already single-sourced or deliberately distinct." Specifics:
  - **Meta-key vocabulary is single-sourced in `base.py`.** `DEFERRED_META_KEYS` (`base.py:63`), `ALLOWED_META_KEYS` (`base.py:67`), `RELATION_SHAPE_VALUES`/`DEFAULT_RELATION_SHAPE` (`base.py:98-99`), `STRING_GLOBALID_STRATEGIES`/`DEFAULT_GLOBALID_STRATEGY` (`base.py:122-123`). No sibling re-declares any of them — `relay.py` imports `DEFAULT_GLOBALID_STRATEGY`/`_validate_globalid_strategy` in-function (`relay.py:373-375`, cycle-dodge), `finalizer.py` imports `DEFAULT_RELATION_SHAPE` in-function (`finalizer.py:405`), and `definition.py`/`finalizer.py` consume `DEFERRED_META_KEYS` by import. No folder-level Meta-key literal duplication to fold.
  - **`relay.py`'s `MODEL_LABEL_STRATEGIES`/`TYPE_NAME_STRATEGIES` (`relay.py:402-403`) are NOT a duplicate of `base.py`'s `STRING_GLOBALID_STRATEGIES`.** They are payload-shape decode-acceptance memberships (a partition of the strategy space, not the strategy enum), centralized once and consumed cross-file by `filters/base.py`. The shared `"type+model"` literal across the two relay frozensets is the whole point of the partition, not a hoistable constant — see `rev-types__relay.md`.
  - **resolvers DRY twin stays file-local and deferred.** The `<name> in getattr(root, "__dict__", {})` loaded-signal probe appears at exactly N=2, both inside `resolvers.py` (`_fk_attname_is_deferred`, `_will_lazy_load_single`). Folder-wide grep confirms zero sibling adds a third site, so this does NOT promote to a folder-level act-now item — the divergent tails (`get_deferred_fields()` column-deferral cache vs `_state.fields_cache` relation-instance cache) answer two different questions over two different Django caches. Carry the per-file deferral verbatim: **"Defer until a third caller needs the bare `__dict__` loaded-signal; only then extract `def _attr_in_instance_dict(root, name) -> bool` for the first line of all callers."**

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The folder fans inward to one set of canonical surfaces, no parallel re-implementations: `_field_output_type_for`/`scalar_for_field` (`converters.py`) are the lone field-class MRO-walk lookups (the filter-input side delegates to `scalar_for_field`, not a second map; the file/image read-output map is consumed only by `convert_field_output` + `resolvers._attach_file_resolvers` + `inspect_django_type`); `origin_has_custom_id_resolver` (`definition.py`) is the deliberately-extracted anti-drift id-resolver predicate shared by the memoized hot path and the optimizer's definition-less fallback (`walker.py::origin_has_custom_id_resolver`); `graphql_type_name` (`definition.py:199-209`) is the single-source `self.name or self.origin.__name__` derivation reused by registry/relay/filters/types.relay; `finalizer.py` is the single owner-bind / sidecar-driver consolidation point (`_bind_set_owner_common`, `_bind_sidecar_sets` + frozen `_SidecarBindingSpec`); `relay.py` holds the single GlobalID validator (`_validate_globalid_strategy`, one rule two sources via `_resolve_globalid_strategy`), the single name→default table (`_RELAY_RESOLVER_DEFAULTS`), and now reads the model handle through the promoted `utils/querysets.py::model_for` (the prior in-module `_model_for` twin removed, commit `7a17ba75`). `FieldMeta` shape-construction in `resolvers.py` routes through the canonical `FieldMeta.from_django_field`/`_from_field_shape` so the resolver's relation-kind classification cannot drift from the walker's. Field-name resolution is single-channel folder-wide: `field_map[snake_case(name)]` (base.py ×2, finalizer.py ×2) uses the canonical `utils/strings.snake_case` against the canonical `field_map`.
- **New helpers considered.** No folder-level helper warranted. The only cross-sibling near-twin in scope is the resolvers `__dict__`-probe pair, evaluated and correctly deferred to N=3 (file-local, no sibling third site). The per-family `_format_*` error helpers in `finalizer.py`, the heterogeneous-body id-resolver chain in `definition.py`, and the twin MRO-walk lookups in `converters.py` were each rejected/deferred for folding inside their own files (distinct consumer vocabulary / detection strategies / divergent miss-semantics), and there is no cross-file variant of any to merge. `base.py`'s two-stage Meta-target validator pair and Relay-Node gate composer are file-local defer-with-trigger items (third target feature / fourth gated key), not folder-scope.
- **Duplication risk in the folder.** Cross-sibling repeated string literals, swept across all eight overviews (incl `__init__.py`), reduce to two genuinely-shared tokens and they are non-hoistable: (1) `"connection"` recurs in `base.py` (3x) and `finalizer.py` (3x), but it is membership content of the single named `RELATION_SHAPE_VALUES` frozenset (`base.py:98`) plus surface text inside finalizer docstrings/error messages and the `shape == "connection"` discriminant on the membership value — `finalizer.py` reads `DEFAULT_RELATION_SHAPE` by function-local import, never re-declaring the vocabulary; (2) `"__func__"` recurs in `definition.py` (2x) and `relay.py` (5x) but is the Python descriptor-unwrap protocol token read via `getattr(..., "__func__", default)` off heterogeneous descriptor objects, not a dispatch key. The strategy/shape string literals (`"model"`, `"type"`, `"type+model"`, `"list"`, `"both"`) are each membership content of a single named frozenset defined once and imported/consumed elsewhere. The `f"{model.__name__}.Meta..."` message prefixes recur across validators by design (distinct constraints, distinct remediation).

### Other positives

- **Internal structure stayed coherent through the 0.0.11 file/image surface and the `model_for` promotion.** The two relevant maintainer changes are both fully cumulative-in-HEAD and self-contained within their owning files: the spec-037 file/image read-output surface lives in `converters.py` (`FIELD_OUTPUT_TYPE_MAP`, `DjangoFileType`/`DjangoImageType`, `_safe_file_attr`) + the resolver attachment in `resolvers.py` (`_make_file_resolver`/`_attach_file_resolvers`), and the `model_for` promotion (commit `7a17ba75`) only swapped `relay.py`'s read sites onto `utils/querysets.py::model_for` (verbatim `__django_strawberry_definition__.model` return — semantics-identical, `grep -rn _model_for` returns zero). `git log fefd80db..HEAD -- django_strawberry_framework/types/` is empty — the folder is byte-identical to both the per-cycle baseline and HEAD. No responsibility leaked between siblings.
- **Responsibility boundaries are clean.** `base.py` orchestrates Meta validation + annotation synthesis; `converters.py` owns all field-shape introspection and the file/image vs scalar output routing (so base carries no file/image branch); `definition.py` is the pure metadata record + id-resolver predicates; `finalizer.py` is the call-time pipeline (zero import-time side effects); `relations.py` is pure data scaffolding; `relay.py` is the GlobalID + resolver-injection machinery; `resolvers.py` is resolve-time access (imports nothing from `base.py` — invariant grep-confirmed). No misplaced helper, no overlapping ownership.
- **Import direction is one-way and acyclic (verified at source).** Intra-folder top-level imports form a DAG: `__init__` → {base, finalizer, relay}; `base` → {converters, definition, relations, relay}; `finalizer` → {converters, relations, relay, resolvers}; `resolvers` → {converters}; `converters`/`definition`/`relations`/`relay` have no top-level intra-folder import (leaves). The `base ↔ relay` cross-reference is one-way at module top (`base→relay` only; `relay→base` is the function-local `_resolve_globalid_strategy` import at `relay.py:373`); the `definition ↔ registry` cross-ref is a function-local cycle-dodge (`definition.py:235`); each carries a documented "do not hoist" rationale. No `optimizer/ → types/` top-level back-edge — the sole `optimizer→types` edge is the sanctioned in-function leaf read `walker.py::origin_has_custom_id_resolver` (`from ..types.definition import origin_has_custom_id_resolver`, `walker.py:900`), documented in `types/__init__.py`. No circular-import risk introduced at folder scope.
- **`types/__init__.py` exports are exactly the public surface.** `__all__ = ("DjangoType", "SyncMisuseError", "finalize_django_types")` (`types/__init__.py:35`) — the three documented public exports, each re-exported from its owning sibling (`base` `DjangoType`, `relay`→via `utils.querysets` `SyncMisuseError`, `finalizer` `finalize_django_types`). All three are also exposed at the package root; this `__init__.py` is the dotted-path-convenience surface. Internal helpers (`convert_scalar`, `convert_choices_to_enum`, `_attach_relation_resolvers`, etc.) are intentionally NOT surfaced here, only reachable by dotted submodule path. The docstring documents the dependency-direction contract and the dotted-path-convenience rationale. No premature future surface, no over-export.
- **Comment/error-handling consistency across siblings.** Every sibling routes config errors through `ConfigurationError` with model/Meta-qualified messages; every cycle-dodge import carries a "Do NOT hoist" comment naming the exact cycle; the static overviews report zero stale TODOs across the folder. No naming or error-handling drift between siblings.

### Summary

`django_strawberry_framework/types/` is a coherent, single-responsibility-per-module subsystem with all seven sibling per-file artifacts `verified` this cycle (each itself a genuine shape #5). The folder is byte-identical to both the per-cycle baseline (`fefd80db622593d367aa387723cb8fcfb2c8b2e3`) and HEAD: `git diff` against both is empty and `git log baseline..HEAD -- types/` returns nothing. The two relevant maintainer changes — the spec-037 file/image read-output surface (`converters.py` + `resolvers.py`) and the `model_for` promotion (`relay.py`, commit `7a17ba75`, semantics-identical verbatim return, `_model_for` twin removed) — are fully cumulative-in-HEAD and self-contained within their owning files; no responsibility leaked, no new cross-sibling literal or helper. The dispatch's cross-file concerns all resolve cleanly: (1) the file/relation resolver structural-twin in `resolvers.py` is intentional sibling design with a verified-divergent skip set (`consumer_assigned_relation_fields` for relations vs the broader `consumer_authored_fields` for files, spec-037 Decision 3) — not a folder-level fold; (2) the `__dict__`-probe extraction trigger is N=2 file-local with divergent cache tails — stays deferred-with-trigger to N=3, not a folder act-now; (3) Meta-vocabulary constants are single-sourced in `base.py` with no sibling re-declaration, and `relay.py`'s strategy frozensets are a distinct payload-shape partition. The two genuinely cross-sibling repeated literals (`"connection"`, `"__func__"`) are non-hoistable membership/protocol tokens. `__init__.py` exports exactly the three public symbols; import direction is one-way and acyclic with the only `optimizer→types` edge being the sanctioned in-function leaf read. No High, Medium, or Low folder-level findings. No-findings folder pass with zero source edits — shape #3 → #5.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; `289 files left unchanged`.
- `uv run ruff check --fix .` — pass; `All checks passed!`.

### Notes for Worker 3
- No-findings folder pass (shape #3 → #5). All seven sibling per-file artifacts are `verified` this cycle; `types/` is byte-identical to both the per-cycle baseline (`fefd80db622593d367aa387723cb8fcfb2c8b2e3`) and HEAD — `git diff --stat <baseline> -- types/`, `git diff --stat HEAD -- types/`, `git log <baseline>..HEAD -- types/`, and the owned-paths `--stat` vs baseline (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) are ALL empty. Zero edits to any tracked file.
- Dispatch forward items, all dispositioned at folder scope with no action:
  - file/relation resolver structural-twin (`_attach_file_resolvers` vs `_attach_relation_resolvers`, `resolvers.py`): intentional structural twin with a verified-divergent skip set (relation = `consumer_assigned_relation_fields`, file = broader `consumer_authored_fields`, spec-037 Decision 3, confirmed at `finalizer.py` call sites). NOT a folder-level fold.
  - `__dict__`-probe extraction trigger (`_will_lazy_load_single` / `_fk_attname_is_deferred`): N=2, both in `resolvers.py`, no sibling third site — stays deferred-with-trigger ("until a third caller needs the bare `__dict__` loaded-signal"). NOT promoted to folder act-now.
  - Meta-vocabulary constants: single-sourced in `base.py`; no sibling re-declares; `relay.py` strategy frozensets are a distinct payload-shape partition, not a duplicate.
  - file/image surface (`converters.py`/`resolvers.py`) + `model_for` promotion (`relay.py`): confirmed cumulative-in-HEAD and self-contained, folder structure coherent.
- `__init__.py` exports verified: `__all__` = the three public symbols only (`DjangoType`/`SyncMisuseError`/`finalize_django_types`); one-way acyclic import direction; no optimizer→types top-level back-edge (sole edge is the sanctioned in-function `walker.py:900` leaf read).
- No GLOSSARY-only fix in scope — sibling artifacts already verified GLOSSARY consistency per symbol (`#djangotype`, `#djangofiletype`/`#djangoimagetype`/`#upload-scalar`, `#metarequired_overrides`, `finalize_django_types`, `Meta.relation_shapes`/`globalid_strategy`/`RELAY_GLOBALID_STRATEGY`, Relay-Node prose); no folder-level prose drift.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No source edits, so no comment/docstring changes. The `types/__init__.py` module docstring (dependency-direction contract, the one sanctioned in-function `optimizer/walker.py` leaf read, dotted-path-convenience rationale, internal-helpers-not-exposed note) is accurate against the source and the sibling artifacts; no stale comment or over-promising docstring at folder scope.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source/test change occurred (read-only folder pass over a folder byte-identical to HEAD and to the per-cycle baseline). Cited authority: AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md` is silent on changelog edits for this item.

---

## Verification (Worker 3)

Shape #5 no-source-edit folder pass. Incoming `Status: fix-implemented` (bare) -> terminal-verify.

### Zero-edit proof
Clean on all axes: `git diff --stat fefd80db.. -- types/` empty, `git diff --stat HEAD -- types/` empty, `git log fefd80db..HEAD -- types/` empty, owned-paths stat (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) vs baseline empty. `types/` is byte-identical to both the per-cycle baseline and HEAD. No dirty hunk touches any `types/` path, so no sibling-cycle attribution required. All three Worker 2 sections open `Filled by Worker 1 per no-source-edit cycle pattern.`

### Logic verification outcome
No High/Medium/Low findings to address. The folder reasoning is sound, independently re-verified against live source (content-not-identifier per AGENTS.md #27):
- **Import DAG one-way / acyclic.** Module-top intra-folder edges confirmed: `__init__`->{base,finalizer,relay} (`__init__.py:31-33`); `base`->{converters,definition,relations,relay} (`base.py:58-61`); `finalizer`->{converters,relations,relay,resolvers} (`finalizer.py:67-78`); `resolvers`->{converters} (`resolvers.py:51`); converters/definition/relations/relay carry zero module-top intra-folder edge (leaves). `base->relay` is module-top only; `relay->base` is the function-local `_resolve_globalid_strategy` import (`relay.py:373`); `definition->registry` is the function-local cycle-dodge (`definition.py:235`). No module-top `optimizer->types` back-edge in any of the seven files (parent imports go only to exceptions/optimizer/registry/scalars/utils); the sole `optimizer->types` edge is the in-function leaf read `from ..types.definition import origin_has_custom_id_resolver` (`walker.py:900`), documented in `types/__init__.py`.
- **`__all__`** = exactly `("DjangoType", "SyncMisuseError", "finalize_django_types")` (`__init__.py:35`), each re-exported from its owning sibling (base / relay-via-querysets / finalizer); internal helpers not surfaced.
- **resolver twin NOT folded** — `_attach_relation_resolvers` (`resolvers.py:411`) / `_attach_file_resolvers` (`resolvers.py:461`) both file-local, divergent skip sets (spec-037 D3); correctly file-level.
- **`__dict__`-probe trigger kept file-level** — exactly N=2 (`_fk_attname_is_deferred` `resolvers.py:76`, `_will_lazy_load_single` `resolvers.py:126`), both in resolvers.py; the finalizer/base/relay `__dict__` reads are unrelated class-dict membership checks, not the relation loaded-signal probe. No sibling third site. Deferred-with-trigger to N=3 correctly.
- **`_model_for` twin removed, `model_for` promotion correct** — `grep -rn _model_for types/` exit 1 (no orphan); `grep -n model_for relay.py` = import + exactly 3 sites (`relay.py:111,173,762`), matching the prior relay-drift verification in worker-3 memory (none a visibility-qs seed).
- No folder-internal duplication missed; the two cross-sibling repeated literals (`"connection"`, `"__func__"`) are non-hoistable membership/protocol tokens; nothing wrongly forwarded/withheld from the project pass.

### DRY findings disposition
DRY-None at folder scope, confirmed sound. Forwarded items (none folder-level act-now): resolver `__dict__`-probe stays file-local deferred-with-trigger to N=3; Meta-vocabulary constants single-sourced in `base.py` with no sibling re-declaration; relay strategy frozensets are a distinct payload-shape partition, not a `STRING_GLOBALID_STRATEGIES` duplicate.

### Temp test verification
None — no-source-edit folder pass, no behavior under suspicion. No temp tests created.

### Changelog disposition
`git diff -- CHANGELOG.md` empty. "Not warranted" cites BOTH AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization for this item. Internal-only framing matches the diff scope (zero source/test change). Accepted.

### Validation
Ruff format-check (`uv run ruff format --check types/` -> 8 files already formatted) and `uv run ruff check types/` -> All checks passed. GLOSSARY prose accuracy was verified per-symbol by the seven sibling `verified` artifacts; no folder-level GLOSSARY-only fix in scope (a GLOSSARY-only fix would be disqualifying for #5; none present).

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the types/ folder-pass checklist box in `docs/review/review-0_0_11.md`.

---

## Iteration log

(none)
