# Review: `django_strawberry_framework/` (project-level pass + top-level `__init__.py`)

Status: verified

Project-level synthesis pass over the whole package, covering the public-API export
surface in the top-level `django_strawberry_framework/__init__.py` (the only top-level
file not individually reviewed) and triaging every package-wide DRY concern forwarded
by the per-file and folder passes. Per-cycle baseline `cd4a90e26dbcf19231acfea0bd39d400a24f1796`;
`git diff cd4a90e26dbcf19231acfea0bd39d400a24f1796 -- django_strawberry_framework/` is
empty (whole package unchanged since baseline), `git diff HEAD -- django_strawberry_framework/__init__.py`
is empty, and `git log cd4a90e..HEAD -- <3 patch modules + apps.py>` returns nothing.
Genuine no-source-edit cycle (shape #5): zero edits to any tracked file, no High, no
behaviour-changing Medium, every Low/DRY item forward-looking or forwarded. The
maintainer just closed a dedicated DRY consolidation cycle (`docs/dry/dry-0_0_11.md`),
so the current factoring is largely intentional; each forwarded item below is triaged
honestly as act-now vs defer-with-trigger / intentional-sibling-design against that
freshly-DRY'd state.

## DRY analysis

This is the package-wide collection point. Each bullet is one forwarded cross-folder /
cross-module candidate, with a verbatim trigger so a future DRY cycle can re-triage when
the trigger fires. None is act-now: the maintainer's `0.0.11` DRY cycle already reached
the consolidatable cores (shared `_PERMISSION_ASYNC_RECOURSE`, the `model_for` promotion,
`verbatim_path` promotion, routing both async-guards through `reject_async_in_sync_context`);
what remains here is either genuinely sibling-divergent orchestration or a single concrete
site with no twin yet.

- **Defer-with-trigger — shared `apply()` scaffold across the three patch modules + the `apps.py` dispatch site.** Forwarded from `rev-_cross_web_patches.md`, `rev-_strawberry_patches.md`, `rev-_django_patches.md`, and `rev-apps.md`. `_cross_web_patches.py::apply`, `_strawberry_patches.py::apply`, and `_django_patches.py::apply` each repeat a four-step skeleton: the `if not upstream_patches_enabled(): return` toggle gate, the once-per-process `_missing_symbol_logged` `logger.info(...)` notice, the `if _patch_is_installed(): return` re-entrancy short-circuit, and the import-time `ImportError`-capture that nulls the patched symbol. `apps.py::DjangoStrawberryFrameworkConfig.ready` (`django_strawberry_framework/apps.py:42-44`) is the dispatch site that imports all three and calls them in sequence. Consolidation shape: a shared `_apply_patch(*, is_installed, install, missing_symbol_present, missing_msg, _state)` helper, or a small `PatchModule` dataclass holding the captured upstream original plus `install` / `is_installed` / `missing_symbol_present` callables, that the three modules import and the `ready()` dispatch iterates. **Do NOT act now:** verified at source that only the skeleton is shared — the install bodies differ structurally (`DjangoHTTPRequestAdapter.body = property(_patched_body)` vs `BaseView.parse_json = _patched_parse_json` vs the `SimpleTestCase` upstream-mirroring attribute loop), the guard arity differs (`_cross_web`/`_django` guard one symbol, `_strawberry` guards two: `BaseView is None or HTTPException is None`), and each carries a distinct missing-symbol message naming its own upstream surface. A shared helper would couple three unrelated install protocols for marginal line savings; the maintainer's DRY cycle deliberately left it (its reach was the permission/decode/model-handle helpers). **Trigger (verbatim): "a fourth patch module lands, OR the three modules are confirmed to stay structurally parallel after a `PatchModule`-callable refactor preserves each install/guard body"** — at that point extract the scaffold and drive `ready()` off the descriptor list.

- **Defer-with-trigger — cross-family `inputs.py` mirror (`filters/inputs.py` ↔ `orders/inputs.py`).** Forwarded from `rev-filters__inputs.md`, `rev-filters.md`, `rev-orders__inputs.md`, `rev-orders.md`. The two families run parallel `materialize_input_class` / `clear_*_input_namespace` / `_build_input_fields` / `normalize_input_value` / `_field_specs`-(`FieldSpec`) ledger scaffolds, but the mechanics already bottom out single-sited in `utils/inputs.py` + `utils/input_values.py` (the 0.0.9 DRY pass); each module's wrapper only pins family constants (`module_path`, `family_label="FilterSet"` vs `"OrderSet"`, ledger, factory + set class names). Already bottomed to `utils/inputs.py`. **Note: `mutations/inputs.py` is now a partial third consumer** — it imports `build_strawberry_input_class` + `materialize_generated_input_class` but bypasses the BFS `GeneratedInputArgumentsFactory` and the `clear_*` ledger (inline Strawberry types, no namespace ledger), so the `clear_*` call-site count is still 2 (filters + orders) and the family-descriptor `ClearSpec` is not yet a 3-way table. **Do NOT act now:** two full families only; a per-family descriptor object buys no readability over the current single-sited mechanics. **Trigger (verbatim): "a third generated-input family lands (e.g. the aggregates `AggregateSet` set), making the family-constant variation a 3-way table"** — then fold the `materialize_*` / `clear_*` wrappers through a single `(module_path, family_label, ledger, factory_module, factory_class_name, collision_registry_attr, set_module, set_class_name)` family descriptor.

- **Defer-with-trigger — filter/order apply-pipeline scaffold (`filters/sets.py::FilterSet` ↔ `orders/sets.py::OrderSet`).** Forwarded from `rev-filters__sets.md`, `rev-filters.md`, `rev-orders__sets.md`, `rev-orders.md`. The `apply_sync` / `apply_async` / `apply` + `_apply_common_prelude` / `_apply_common_finalize` dispatch shell is shared structurally across the two `*Set` classes; the shared steps (permission core, request resolution, input traversal, sync-misuse routing) already route through single-sited `utils/permissions.py` / `utils/input_values.py` / `utils/querysets.py` cores, leaving only the prelude/finalize/dispatch shell and the permission-check `sync_to_async` wrap divergence. `docs/GLOSSARY.md:971` pins the filter/order apply-pair parity as intentional sibling design. **Do NOT act now:** the coroutine-color hazard is real (the sync path must raise `SyncMisuseError` synchronously; the async path must `await` first) and only two families exist. **Trigger (verbatim): "a third `*Set.apply_*` family (e.g. `AggregateSet`) landing — then fold the prelude/finalize/dispatch scaffold through a shared mixin."**

- **Defer-with-trigger — Layer-6 dynamic-cache primitives (`filters/factories.py` only; orders side deferred TODO).** Forwarded from `rev-filters__factories.md`, `rev-filters.md`, `rev-orders__factories.md`, `rev-orders.md`. `filters/factories.py::_make_hashable` and the `(model, fields_key, extra)` key body of `::_make_cache_key` are the only concrete implementation of the model-keyed dynamic-class cache shape. `orders/factories.py` reserves `_dynamic_orderset_cache` / `get_orderset_class` as a TODO-anchored deferred non-goal (`orders/factories.py` `#"TODO(spec-028-orders-0_0_8 Decision 12"`, lines ~85-103) with NO implementation, so **no twin exists** and a single concrete site is not duplication. The eventual consolidation site (`utils/inputs.py::make_set_meta_cache_key`) and the future twin both live outside `filters/`. **Do NOT act now.** **Trigger (verbatim): "when a card revives the orders Layer-6 surface (i.e. `orders/factories.py` gains a real `get_orderset_class` + `_dynamic_orderset_cache` implementation)"** — then hoist `_make_hashable` + the cache-key body to the shared site and parameterize per family.

- **Defer-with-trigger — shared mutation `OPERATIONS` verb vocabulary across `mutations/` (sets/resolvers/permissions/fields).** Forwarded from `rev-mutations__sets.md` and `rev-mutations.md`. The verb literals `"create"` / `"update"` / `"delete"` are spelled inline in four of the five `mutations/` modules: `sets.py::_VALID_OPERATIONS` (`frozenset`, the membership single-source for `Meta.operation` validation), `resolvers.py` (equality dispatch `meta.operation == "create"`/`"update"` + single-verb positional `_authorize_or_raise(..., "create"/"update"/"delete", ...)` args), `permissions.py::_OPERATION_PERMISSION_ACTION` (dict KEYS), and `fields.py::_synthesized_mutation_signature` (membership tests `operation in ("update","delete")` / `("create","update")`). The only true single-source candidate is the bare verb **vocabulary** (a canonical `OPERATIONS = ("create","update","delete")` tuple). **Keep the verb→Django-codename map (`_OPERATION_PERMISSION_ACTION` values) and the verb→input-kind map (`_OPERATION_INPUT_KIND`) as distinct axes — they must NOT be folded into the vocabulary.** Forwarded to project level (not folder) because a canonical verb tuple is plausibly a package-level constant (a future read-side `aggregates`/bulk-write family would share it). **Do NOT act now:** `resolvers.py`'s equality-against-single-literal dispatch and single-verb authorize args cannot consume a membership set (a forced fit, confirmed in `rev-mutations__sets.md`), so a vocabulary tuple buys clarity, not call-site reduction, until a real iterator/membership consumer beyond `sets.py` exists. The maintainer's DRY cycle did not touch this (it shared the recourse string and routed the guard, not the verb vocabulary). **Trigger (verbatim): "Promote a shared `OPERATIONS` verb tuple when a second module needs to iterate or membership-test the verb set (beyond `sets._VALID_OPERATIONS`), OR when a fourth mutation operation lands; then single-source the vocabulary and rebuild `_VALID_OPERATIONS` / the dict keys / the per-op branches from it."**

- **Defer-with-trigger — permission-wrapper-layer mixin (`filters/sets.py::FilterSet` ↔ `orders/sets.py::OrderSet` six delegate methods).** Forwarded from `rev-orders__sets.md`, `rev-orders.md`, `rev-filters__sets.md`. The six `OrderSet` permission delegates (`_request_from_info`, `_extract_branch_value`, `_active_permission_field_paths`, `_active_permission_targets`, `_invoke_permission_method`, `_run_permission_checks`) are byte-symmetric one-line delegates into `utils/permissions.py`, mirroring `FilterSet`'s same-named methods; the only per-family residue is the family-label string (`"OrderSet"` vs `"FilterSet"`), the `related_attr`/`target_attr` tokens (`"related_orders"`/`"orderset"` vs `"related_filters"`/`"filterset"`), and `logic_keys` (`frozenset()` vs the filter operator bag). The mechanics already bottom out single-sited in `utils/permissions.py` (0.0.9 DRY Major-3); only the thin family-config delegate layer is duplicated. **Do NOT act now:** a shared `PermissionDelegateMixin` parameterized by a small config object spans two folders and must preserve each family's public method names (the documented consumer-facing surface), so it is project-wide triage, not a folder-level fold; only two families exist. **Trigger (verbatim): "a third `*Set` family with the same permission-delegate layer lands (e.g. `AggregateSet`); then hoist the six delegates into a shared mixin parameterized by `(family_label, related_attr, target_attr, logic_keys)`, preserving each family's public method names."**

- **Defer-with-trigger — `utils/` public-surface `__all__` re-export asymmetry (submodule-direct imports bypass it).** Forwarded from `rev-utils.md` (folder mirror of `rev-utils__relations.md`'s `instance_accessor` Low and `rev-utils__typing.md`'s `is_async_callable` Low). `utils/__init__.py::__all__` (7 symbols: `RelationKind`, `is_many_side_relation_kind`, `pascal_case`, `relation_kind`, `snake_case`, `unwrap_graphql_type`, `unwrap_return_type`) is sorted, leaks nothing private, and matches the package docstring — but **every production consumer imports submodule-direct** (`from ..utils.relations import …` / `.strings` / `.typing`); the package-root path is exercised only by a single test (`tests/utils/test_typing.py:9`). `instance_accessor` and `is_async_callable` are consumed submodule-direct and are *omitted* from `__all__`, so they are not anomalies but the dominant convention. `unwrap_return_type` (in `__all__`) is no longer orphaned (caller `mutations/sets.py::_is_relay_id_annotation`, commit `ee1afb58`) — but that caller, too, imports submodule-direct. **Do NOT act now:** the asymmetry is harmless and internally consistent. **Trigger (verbatim): "a production consumer begins importing these helpers via the `utils` package root; then reconcile in one direction — either promote `instance_accessor` / `is_async_callable` into `__all__` (so the root path is complete), or drop the unused re-exports (so the submodule path is the sole public surface)."**

## High:

None.

## Medium:

None.

## Low:

None.

The top-level `__init__.py` is correct on every project-pass axis (covered in `### Other positives`): export surface, `__all__` completeness/sort, `__version__` == pyproject `0.0.11`, logger single-source declaration, and import-order/circular-import safety. No source-level finding. All seven forwarded DRY items are defer-with-trigger or intentional-sibling-design; none warrants an act-now edit against the freshly-DRY'd codebase.

## What looks solid

### DRY recap

- **Existing patterns reused.** The package is a mature single-source graph after the `0.0.11` DRY cycle: `utils/` is the bottom-of-graph consolidation layer (`utils/querysets.py::model_for`, `reject_async_in_sync_context`, `utils/permissions.py::verbatim_path` + the active-input permission core, `utils/inputs.py` generated-input substrate, `utils/input_values.py` set-input traversal, `utils/strings.py` case conversion, `utils/relations.py` relation-shape classifier) and every upper subsystem imports from it rather than re-spelling. The top-level `__init__.py` itself reuses the canonical-logger single-source pattern (`logger = logging.getLogger("django_strawberry_framework")` declared once at `__init__.py:13`, re-exported by subpackages via `from .. import logger`).
- **New helpers considered.** The shared patch-`apply()` scaffold (`PatchModule` dataclass / `_apply_patch` helper) was evaluated and **rejected for now** — only the orchestration skeleton is shared; the install bodies and guard arities diverge per upstream surface (verified at source), so a shared helper would couple unrelated install protocols. The `apps.py::ready()` dispatch-table refactor (`for fn in (apply_django, …): fn()`) was rejected — it would trade explicit, greppable, order-visible calls for marginal savings and obscure the deliberate ordering. The six cross-family / cross-module candidates (inputs mirror, apply-pipeline scaffold, Layer-6 cache, OPERATIONS vocabulary, permission-wrapper mixin, `utils` `__all__` asymmetry) were all evaluated and deferred with explicit triggers — none has a third consumer / twin yet, and folding two-member families would re-introduce per-family parameter objects for no readability gain.
- **Duplication risk across the package.** The four-step patch-`apply()` skeleton (toggle gate / once-only notice / re-entrancy short-circuit / import-time `ImportError` capture) is the one genuine cross-module near-copy; it is intentional sibling design at three distinct upstream-patch lifecycle sites and is captured as the first forwarded DRY item. The filters↔orders byte-symmetric twins (inputs wrappers, apply pipeline, permission delegates) are deliberate family-parallel design pinned by `docs/GLOSSARY.md:971` and the `RelatedSetTargetMixin` docstring; the mutation verb literals are distinct dispatch axes that must not be over-folded. All other repeated literals across the package are family-token / Django-protocol-attr reads off heterogeneous objects, dispositioned per-file as non-hoistable.

### Other positives

- **`__init__.py` export surface is complete and ordered.** `__all__` (`__init__.py:38-62`) is alphabetically sorted, includes `__version__`, and every named symbol resolves to a real import: `BigInt` / `Upload` / `strawberry_config` (scalars), the four `mutations` symbols (`DjangoModelPermission`, `DjangoMutation`, `DjangoMutationField`, `FieldError`), `DjangoConnection`/`DjangoConnectionField` (connection), `DjangoListField`, `DjangoNodeField`/`DjangoNodesField` (relay), `DjangoOptimizerExtension` (optimizer), `OptimizerHint` (optimizer.hints), `DjangoType`/`SyncMisuseError`/`finalize_django_types` (types), `DjangoFileType`/`DjangoImageType` (types.converters), `aapply_cascade_permissions`/`apply_cascade_permissions` (permissions), and `auto` (re-exported from strawberry). No private symbol leaks; no `__all__` entry lacks a backing import.
- **`auto` re-export is a deliberate part of the DRF-shaped public surface** — the comment at `__init__.py:3-4` documents that consumers write `from django_strawberry_framework import auto` without importing strawberry directly. `DjangoFileType`/`DjangoImageType` are surfaced from the `types.converters` submodule into the root namespace so the file/image scalar-output types are first-class public symbols (consistent with the 0.0.11 media-upload feature work).
- **`__version__ == "0.0.11"` matches `pyproject.toml [project].version`** (verified `grep -E '^version' pyproject.toml` → `version = "0.0.11"`) per AGENTS.md #31 (bump both together). The active plan header also confirms the in-sync state.
- **Logger declared as a single source of truth.** The literal `"django_strawberry_framework"` lives in exactly one place (`__init__.py:13`); the comment at `:7-12` documents that subpackages re-export it via `from .. import logger` (verified consumers: `optimizer/walker.py`, `optimizer/extension.py`, `optimizer/__init__.py`) and that the logger name is consumer-facing (Django `LOGGING` config key) and therefore public even though it is not in `__all__`.
- **Import-order / circular-import safety is correct and intentional.** The `logging` import and `logger` declaration precede all subpackage imports (`:5`, `:13`), so subpackages re-exporting `logger` at import time see a defined object — the inline `# noqa: E402  # logger must exist before subpackage imports` at `:15` documents exactly this ordering constraint. All subsequent `from .<subpackage> import …` lines carry `# noqa: E402` because they intentionally follow the logger declaration. No subpackage imports back from the package root at module-import time (the only back-references are the `from .. import logger` re-exports, which resolve against the already-defined attribute), so the package-root import is acyclic.
- **Whole-package stability.** `git diff cd4a90e..` and `git diff HEAD --` are both empty for the entire package; every per-file and folder artifact in the plan is `verified`; the dirty working tree is `docs/review/*` scratchpads + `docs/feedback2.md` only (out-of-scope concurrent work per AGENTS.md #34).

### Summary

The project-level pass confirms a settled, maximally-DRY-within-readability package. The top-level `__init__.py` is correct on every axis: a sorted/complete `__all__`, a `__version__` matching `pyproject.toml` at `0.0.11`, a single-sourced canonical logger declared before subpackage imports (the `# noqa: E402` ordering is load-bearing and documented), and an acyclic package-root import graph. All seven forwarded package-wide DRY items are collected here and triaged honestly against the maintainer's just-completed `0.0.11` DRY cycle: every one is defer-with-trigger or intentional-sibling-design, none is act-now. The shared patch-`apply()` scaffold is the strongest candidate but is genuine sibling divergence (distinct install bodies, guard arities, and notices per upstream surface), and a shared helper would couple three unrelated install protocols; the filters↔orders twins (inputs mirror, apply pipeline, permission-wrapper mixin) are deliberate family-parallel design awaiting a third `*Set` family; the Layer-6 cache has no twin (orders side is a TODO non-goal); the mutation OPERATIONS vocabulary is plausibly a future package constant but its dispatch axes must stay distinct; and the `utils` `__all__` asymmetry is a harmless, consistent submodule-direct convention. No High, no Medium, no Low. Genuine no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, `289 files left unchanged`.
- `uv run ruff check --fix .` — pass, `All checks passed!`.

### Notes for Worker 3
- Project-level pass, shape #5 (no-source-edit). `git diff cd4a90e26dbcf19231acfea0bd39d400a24f1796 -- django_strawberry_framework/` is empty (whole package unchanged since baseline); `git diff HEAD -- django_strawberry_framework/__init__.py` is empty; `git log cd4a90e..HEAD -- <3 patch modules + apps.py>` returns nothing. Prior artifact at this path was `Status: verified` (previous cycle) — overwritten cleanly, old Worker 3 banner dropped.
- All severities `None.`. The `__init__.py` is correct on every project-pass axis: `__all__` sorted/complete (`__init__.py:38-62`), `__version__ == "0.0.11"` matches `pyproject.toml` (verified), logger single-sourced and declared before subpackage imports with documented `# noqa: E402` ordering, acyclic package-root import graph.
- Seven forwarded DRY items triaged in `## DRY analysis`, every one defer-with-trigger / intentional-sibling-design, none act-now (see per-item dispositions and verbatim triggers). The patch-`apply()` scaffold divergence was confirmed at source (distinct install bodies / guard arities / notices). The maintainer's `0.0.11` DRY cycle deliberately did not collapse any of the seven.
- No GLOSSARY-only fix in scope: the `__init__.py` exposes no new symbol needing a GLOSSARY entry beyond what the per-file passes already verified; the logger is consumer-facing but its name is documented inline, not a GLOSSARY contract symbol. No project-pass GLOSSARY drift surfaced (the one prior `apps.py` GLOSSARY Medium at `docs/GLOSSARY.md:308` was already resolved in HEAD by its owning cycle).
- No Lows to disposition.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits. The `__init__.py` comments were audited: the `auto` re-export rationale (`:3-4`), the canonical-logger block (`:7-12`), and the `# noqa: E402` ordering note (`:15`) are all accurate and load-bearing — none stale, none restating obvious code. No edit warranted.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

**Not warranted.** No source, test, or doc edit was made this cycle (shape #5). Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active review plan (`docs/review/review-0_0_11.md`), which does not authorize a `CHANGELOG.md` edit for the project pass, no changelog entry is owed. No `CHANGELOG.md` edit.

---

## Verification (Worker 3)

### Logic verification outcome
No High / Medium / Low findings exist (all `None.`), so there is no per-finding logic to accept or reject. The project-pass axes on the top-level `__init__.py` were independently re-verified against live source:

- **Zero-edit proof (shape #5).** `git diff --stat cd4a90e2 -- django_strawberry_framework/` empty; `git diff --stat HEAD -- django_strawberry_framework/__init__.py` empty; owned-paths stat (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) empty vs baseline. HEAD is `82666eac`; baseline `cd4a90e2` is a WIP stash atop it. Working tree dirt is `docs/review/*` scratchpads + `docs/feedback2.md` only — concurrent docs-review work (AGENTS.md #34), no tracked source/test/GLOSSARY/CHANGELOG file dirty. "Files touched: None" holds.
- **`__all__` sorted/complete/no private leak.** AST parse: 23 entries, `vals == sorted(vals)` True, zero `_`-prefixed entries other than `__version__`. Pinned by `tests/base/test_init.py::test_public_api_surface_is_pinned` (exact-tuple assertion) + `test_file_upload_exports_resolve_to_their_source_definitions` (identity pins for the three spec-037 re-exports).
- **`__version__ == "0.0.11"` matches `pyproject.toml`.** `grep -E '^version' pyproject.toml` → `0.0.11`; `__init__.py:36` → `0.0.11`. Pinned by `test_version`. AGENTS.md #31 satisfied.
- **Logger single-source + load-bearing `# noqa: E402` ordering.** Exactly one `getLogger("django_strawberry_framework")` (`__init__.py:13`), declared before all `from .<subpackage>` imports; only `optimizer/__init__.py` re-exports it via `from .. import logger` (attribute read against the already-defined object, not a module cycle) → package-root import acyclic. Pinned by `test_logger_name_is_django_strawberry_framework` + `test_optimizer_subpackage_reexports_top_level_logger` (`is` identity).
- Ruff check on `__init__.py`: `All checks passed!`.

### DRY findings disposition
All seven forwarded items confirmed correctly DEFERRED (defer-with-trigger / intentional-sibling-design), none a missed act-now consolidation. Load-bearing spot-checks:

- **Patch `apply()` scaffold (3 modules).** Divergence verified at source: guard arity differs (`_strawberry_patches.py:259` guards two symbols `BaseView is None or HTTPException is None`; `_cross_web` / `_django` guard one each); install bodies structurally distinct (`DjangoHTTPRequestAdapter.body = property(_patched_body)` vs `BaseView.parse_json = _patched_parse_json` vs the `_django` `for alias in connections` / `for name,_ in cls._disallowed_connection_methods` setattr loop mirroring upstream `SimpleTestCase`); distinct missing-symbol messages. A shared helper would couple three unrelated install protocols — deferral correct.
- **verb→codename vs verb→input-kind maps stay distinct.** `_OPERATION_PERMISSION_ACTION` = `{create:add, update:change, delete:delete}` (Django codenames); `_OPERATION_INPUT_KIND` = `{create:CREATE, update:PARTIAL}` (input kinds). Different value spaces — must not be folded into a bare verb tuple. Confirmed.
- **`clear_*` call-site count still 2.** The shared BFS-ledger core `utils/inputs.py::clear_generated_input_namespace` has exactly two delegating callers: `filters/inputs.py:876` and `orders/inputs.py:383`. `mutations/inputs.py::clear_mutation_input_namespace` owns its own module-level ledger and explicitly does NOT delegate to the shared core (documented `mutations/inputs.py:28,141`), so it is not a third consumer. Family-descriptor `ClearSpec` is not yet a 3-way table — deferral correct.
- **`utils` `__all__` asymmetry.** `utils/__init__.py::__all__` is the 7 sorted symbols claimed; `is_async_callable` / `instance_accessor` correctly omitted (submodule-direct consumed). `unwrap_return_type` confirmed no longer orphaned — real consumer `mutations/sets.py:830` `_is_relay_id_annotation` (imported submodule-direct at `:53`), which also corroborates the dominant submodule-direct convention. Harmless/consistent — deferral correct.

The maintainer's just-closed `0.0.11` DRY cycle bounded its reach to the permission/decode/model-handle cores; none of the seven is a genuine readability/correctness win being wrongly punted.

### Temp test verification
None used — no behavioral suspicion to prove; existing `tests/base/test_init.py` pins every project-pass axis.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the project-level pass checkbox in `docs/review/review-0_0_11.md`.
