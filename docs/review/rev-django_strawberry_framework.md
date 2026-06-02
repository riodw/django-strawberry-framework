# Review: `django_strawberry_framework/` (project pass)

Status: verified

Project-level pass. Covers the top-level `django_strawberry_framework/__init__.py` and consolidates every forward from per-file and folder-pass artifacts under `docs/review/rev-*.md`.

Sibling artifacts read (Worker 1's contract per `docs/review/worker-1.md` "Folder and project passes"):

- Top-level files: `rev-_django_patches.md`, `rev-apps.md`, `rev-conf.md`, `rev-exceptions.md`, `rev-list_field.md`, `rev-registry.md`, `rev-scalars.md`, `rev-sets_mixins.md` (all `Status: verified`).
- Folder passes: `rev-filters.md`, `rev-management__commands.md`, `rev-management.md`, `rev-optimizer.md`, `rev-testing.md`, `rev-types.md`, `rev-utils.md` (all `Status: verified`).
- Per-file leaves under those folders all `Status: verified`.

Shadow overview for the top-level `__init__.py` regenerated at project-pass time (the plan-time `--all` sweep skipped it): `docs/shadow/django_strawberry_framework____init__.overview.md` (7 imports, 0 symbols, 0 control-flow hotspots, 0 calls of interest, 0 repeated literals, 0 TODOs).

## DRY analysis

- **Defer-with-trigger — cross-folder `_camel_case` extraction landing in `utils/strings.py::camel_case(name)` during the next REVIEW cycle that closes `orders/`.** Two byte-identical helpers exist today at `filters/inputs.py:783-789` and `orders/inputs.py:164-170` (the latter is concurrent spec-028 Slice 3 maintainer work landed post-baseline at `b8fbd74` / `f3a0777`, NOT in the 0.0.7 plan checklist). `utils/strings.py`'s module docstring at `:13-15` already commits to the canonical-home pattern ("Kept minimal on purpose. If a third style ever shows up we'll add it here rather than re-deriving inline at the call site"). Per the second-closing-folder calibration (`rev-utils.md::Carry forward`, `rev-utils__strings.md::DRY analysis`, `rev-filters.md::DRY analysis`), the cycle that closes `orders/` second owns the landing. The project pass does NOT land this — the consolidation belongs to the 0.0.8 cycle's `orders/` folder pass.

- **Defer-with-trigger — `lazy_input_annotation(name, module_path)` helper in `utils/typing.py` collapsing the `Annotated[<name>, strawberry.lazy(<module_path>)]` ForwardRef-wrap shape.** Three sites today inside `filters/` only (`__init__.py:87`, `inputs.py:640`, `inputs.py:725`) — per `rev-filters.md::DRY analysis` bullet 3 the consolidation defers until a second sibling subsystem (orders/aggregates) reaches for the same Strawberry `LazyType.resolve_type` ForwardRef-wrap. With `orders/` landing as concurrent work, that trigger will likely fire in the 0.0.8 cycle; the project pass restates the deferral so it shows up in the next DRY cycle's grep. Helper would lift the six-line load-bearing `LazyType.resolve_type`-requires-Annotated comment at `filters/__init__.py:79-86` alongside the function body.

- **Defer-with-trigger — package-wide submodule `__all__` convention pass.** Today's state per `grep -n '^__all__' django_strawberry_framework/**/*.py`: submodule-level `__all__` is the exception, not the rule — only `optimizer/extension.py:68`, `exceptions.py:8`, `list_field.py:22`, and `sets_mixins.py:127` carry one. Every submodule under `filters/`, every submodule under `types/`, every other submodule under `optimizer/`, every submodule under `testing/`, and every submodule under `utils/` lacks one. Per the `rev-utils.md::L1` calibration ("acting on `utils/*.py` would create a single-folder anomaly"), do NOT land per-folder submodule `__all__` adoption piecemeal. Defer until either (a) a major-version-bump release boundary triggers a package-wide cleanup pass authoring submodule `__all__` uniformly, OR (b) any submodule grows a fourth public symbol where the internal-helper / public-symbol split inside the submodule becomes load-bearing. The project pass records this as the canonical, package-wide deferral that supersedes every per-folder phrasing.

- **Defer-with-trigger — package-wide backtick-convention pass across docstrings (single-backtick vs RST-style double-backtick).** Per `rev-filters.md::Low #8` forwarded from per-file siblings, the four `filters/` siblings and `__init__.py` carry divergent conventions (RST-style double-backticks in helpers ported from the cookbook; single-backticks in package-original consumer-facing docstrings; mixed in `inputs.py` and `sets.py`). Same drift class appears across `types/` per `rev-types.md`'s comment hygiene audit and in `_django_patches.py`'s RST `.. code-block::` blocks. Two acceptable shapes: (a) standardize package-wide on single-backticks (matches the consumer-facing exterior surface and `__init__.py` posture); (b) standardize RST-style double-backticks for docstrings AND single-backticks for inline `#` comments (matches cookbook ports and Sphinx autodoc friendliness). Defer until either (i) a Sphinx autodoc pass lands as a real card, OR (ii) a consumer-facing docs site ships. Today the inconsistency is internal and the per-symbol GLOSSARY entries paper over the surface mismatch. Project pass records the cross-folder grep for the next DRY/REVIEW cycle.

- **None within `__init__.py` itself.** The top-level `django_strawberry_framework/__init__.py` is 39 source lines with seven imports, one module-level `logger`, one `__version__`, and one `__all__`. There is no executable code beyond `logging.getLogger("django_strawberry_framework")`, no symbol definitions other than the logger, no repeated literals (shadow overview confirms `repeated string literals: 0`), and no DRY surface to consolidate against — every cross-cutting consolidation lives one or two folders deeper.

## High:

None.

## Medium:

### M1 — Active plan + version mismatch: `pyproject.toml` and `django_strawberry_framework/__init__.py::__version__` are both `0.0.8`, but the active review plan is `docs/review/review-0_0_7.md` (versions are NOT in sync)

The plan header at `docs/review/review-0_0_7.md:4` claims "Versions confirmed in sync: `pyproject.toml` and `django_strawberry_framework/__init__.py` both at `0.0.7`." This is no longer true:

```pyproject.toml:4
version = "0.0.8"
```

```django_strawberry_framework/__init__.py:26
__version__ = "0.0.8"
```

The `0.0.8` version landed via the spec-027 filter-subsystem joint-cut version-bump per `CHANGELOG.md:18-26` (`## [Unreleased] / ### Added / Filtering subsystem.`). The two version pins are themselves in sync — the drift is between the plan-named release (`0.0.7`) and the package's current version (`0.0.8`).

Per `docs/review/REVIEW.md` "Versioned review plan" — "Worker 0 reads `pyproject.toml` and `django_strawberry_framework/__init__.py`; versions must match. … If versions differ, record the mismatch in the plan before any review starts." The versions DO match each other; what differs is the plan's named release. The plan was authored at `0.0.7` and the cycle ran across the version bump to `0.0.8`. Per `worker-0.md` closeout job and `REVIEW.md`'s plan-naming rule, the right resolution is for Worker 0 to record the version-bump-mid-cycle event in the active plan (or open a fresh `review-0_0_8.md` plan) before the final-test-run-gate runs.

**Why Medium.** This is a workflow-hygiene defect, not a source defect: the current cycle's review work is correct against the `0.0.8` source surface (the spec-027 filter-subsystem joint-cut landed mid-cycle and every `filters/` per-file artifact already accounts for it via the `RelatedFilter` GLOSSARY `shipped (0.0.8)` calibration per `rev-filters__base.md::Low #6`). But the rev-final.md gate and the closeout job both reference `review-0_0_7.md` by name, so the next reviewer following the audit trail lands at a plan claiming a version that no longer matches the source. Recommended resolution at project-pass scope: surface the mismatch in `rev-django_strawberry_framework.md` (here) so Worker 0's closeout pass picks it up; the plan-file edit itself is Worker 0's responsibility per `REVIEW.md` "Worker 0 owns the plan." No source/test/GLOSSARY/CHANGELOG edit warranted at project-pass time.

### M2 — CHANGELOG.md test/ → testing/ rename rot at two sites — bundled cross-folder rename sweep

Per `rev-testing___wrap.md::Low #2` (forwarded to project pass), `CHANGELOG.md` carries two surfaces citing the old `django_strawberry_framework.test` path post-rename to `django_strawberry_framework.testing`:

```CHANGELOG.md:33
- `safe_wrap_connection_method` — cooperative wrap-time helper for consumers (or third-party libraries)
  replacing a method on a Django `connections[alias]` between `setUpClass` and `tearDownClass`. … Public
  export from [`django_strawberry_framework.test`][test-init]. …
```

```CHANGELOG.md:207
[test-init]: django_strawberry_framework/test/__init__.py
```

`grep -n "django_strawberry_framework.test\b" CHANGELOG.md docs/GLOSSARY.md docs/TREE.md README.md docs/README.md` confirms the drift is confined to these two `CHANGELOG.md` sites (no other surface still cites the old `test/` path). The actual subpackage on disk is `django_strawberry_framework/testing/` per `ls django_strawberry_framework/`; the rename landed in `0.0.7` per `rev-testing___wrap.md` and the working test directory is `testing/_wrap.py` / `testing/__init__.py`.

**Recommended fix.** Two-site sweep at Worker 2's project-pass spawn:

1. Replace `Public export from [`django_strawberry_framework.test`][test-init]` at `CHANGELOG.md:33` with `Public export from [`django_strawberry_framework.testing`][test-init]` (preserves the `[test-init]` ref-id so callers of the link don't break).
2. Replace `[test-init]: django_strawberry_framework/test/__init__.py` at `CHANGELOG.md:207` with `[test-init]: django_strawberry_framework/testing/__init__.py`.

Post-fix grep `grep -n "django_strawberry_framework.test\b" CHANGELOG.md` should return zero hits.

**Why Medium, not Low.** This is a shipped CHANGELOG entry naming a public consumer-import path that no longer exists on disk. A consumer reading `CHANGELOG.md:33` and copy-pasting `from django_strawberry_framework.test import safe_wrap_connection_method` will hit `ModuleNotFoundError`. Per `AGENTS.md` rule 21 ("Do not update CHANGELOG.md unless explicitly instructed") the edit needs explicit project-pass authorization — this artifact's recommendation IS that explicit authorization, scoped narrowly to the two-site rename sweep. The fix is mechanical and bounded; no other CHANGELOG hunk in scope.

### M3 — TREE.md `convert_relation` historical name drift at three sites

Per `rev-types__converters.md::What looks solid > GLOSSARY drift quick-check` and `rev-types.md::L3` (forwarded to project pass), `docs/TREE.md` cites the historical `convert_relation` symbol name at three sites in the per-file comment column:

```docs/TREE.md:214
│   ├── converters.py        # convert_scalar, convert_choices_to_enum, convert_relation
```

```docs/TREE.md:264
│   ├── converters.py        # convert_scalar, convert_choices_to_enum, convert_relation
```

```docs/TREE.md:357
│   ├── test_converters.py   # ← convert_scalar / convert_relation / convert_choices_to_enum
```

The source symbol was renamed to `resolved_relation_annotation` per `docs/SPECS/spec-018-meta_primary-0_0_6.md:139` ("the relation-annotation builder; was historically referenced as `convert_relation`"). Confirmed by reading `django_strawberry_framework/types/converters.py::resolved_relation_annotation`.

**Recommended fix.** Three-site sweep at Worker 2's project-pass spawn — replace every `convert_relation` token in `docs/TREE.md` with `resolved_relation_annotation` (preserve every surrounding character; the per-file comment column has fixed alignment, so the longer string may push the column — confirm the file still renders cleanly post-fix or accept the alignment shift since `docs/TREE.md` is a documentation tree, not source code).

**Why Medium.** Same calibration as M2 — `docs/TREE.md` is a top-level package map shipped to consumers via the rendered `docs/` site. A consumer or maintainer following the per-file comment column lands at a symbol that no longer exists on disk; `grep -rn "convert_relation" django_strawberry_framework/` returns zero hits in source. The rev-anchor `docs/SPECS/spec-018-meta_primary-0_0_6.md:139` documents the rename explicitly as a public-API change. The fix is mechanical and bounded.

### M4 — GLOSSARY filter-subsystem joint-cohort first-cohort coverage — 21 symbols absent

Forwarded by every `rev-filters__*.md` artifact, `rev-filters.md::Low #4`, and `rev-sets_mixins.md::Low #5`. Per the spec-027 Decision 10 joint-cut deferral pattern, the filter-subsystem first-cohort GLOSSARY entries are best authored together at version-bump time when the second cohort (orders) lands. With `0.0.8` shipping the filter subsystem AND the orders subsystem landing as concurrent maintainer work for the next cycle, the project pass evaluates the cohort.

**Current GLOSSARY coverage today** (per `grep -n "^## " docs/GLOSSARY.md`):

- `FilterSet` (`:433`), `filter_input_type` (`:445`), `Meta.filterset_class` (`:620`), `RelatedFilter` (`:870`) — four entries, all current at `shipped (0.0.8)`.

**Filter-subsystem public surface absent from GLOSSARY** (per `django_strawberry_framework/filters/__init__.py:90-107` `__all__`):

- Parity-floor primitives: `TypedFilter`, `ArrayFilter`, `ArrayFilterMethod`, `RangeFilter`, `RangeField`, `ListFilter`, `ListFilterMethod` (7 symbols).
- GlobalID pair: `GlobalIDFilter`, `GlobalIDMultipleChoiceFilter` (2 symbols).
- Validators: `validate_range` (1 symbol — the public name a consumer reaches for to validate the two-element list contract per `rev-filters.md::What looks solid`).
- Metaclass: `FilterSetMetaclass` (1 symbol — exported per `__all__` for `isinstance` checks).
- Filter base re-export: `Filter` (1 symbol — verbatim re-export of `django_filters.Filter` per `rev-filters.md::Low #5`'s defer-with-trigger).
- Shared mixins (from `sets_mixins.py`, re-exported by `filters/__init__.py:30, 98`): `LazyRelatedClassMixin`, `ClassBasedTypeNameMixin`, `type_name_for`, `resolve_lazy_class` (4 symbols per `rev-sets_mixins.md::Low #5`).

Total filter-cohort GLOSSARY absences: **16 public symbols**.

**Filter-subsystem internal-but-cross-module-cited symbols also absent** (per the per-file artifacts' enumerations):

- `INPUTS_MODULE_PATH`, `_input_type_name_for`, `convert_filter_to_input_annotation`, `normalize_input_value`, `LOOKUP_NAME_MAP` (per `rev-filters__inputs.md::Low #5`).
- `FilterArgumentsFactory`, `get_filterset_class`, `_dynamic_filterset_cache`, `_make_cache_key` (per `rev-filters__factories.md::Low #6`).
- `HIDE_FLAT_FILTERS` settings key (per `rev-filters__inputs.md::Low #5`).

Per the `Internal-mechanics GLOSSARY absence is correct convention` calibration recorded across the optimizer + types subpackage cycles AND per `optimizer/__init__.py:14-17` framing ("internal implementation details consumed by … not consumer-facing API"), the internal mechanics absences are **correct convention** and should NOT be filed as gaps. The cohort that warrants GLOSSARY entry is the 16-symbol public surface above.

**Recommended fix.** Author 16 GLOSSARY entries together as one Worker 2 spawn, paired with the orders-cohort entries when that subsystem reviews. Per the project-pass scope rule, the project pass does NOT itself author the entries — it confirms the cohort boundary and forwards to the joint-cut authoring step. The forward gate is:

- Trigger A: `Meta.orderset_class` flips to `shipped (0.0.8)` (currently `planned for 0.0.8` per `docs/GLOSSARY.md` per `rev-types__finalizer.md::Low #9`); when the orders cohort enters GLOSSARY, the filter cohort lands together.
- Trigger B: a consumer-facing release-notes pass or a Sphinx autodoc pass authors the cohort as part of release prep.

**Why Medium, not Low.** Single per-file Low is the right scope; folder-pass bundling (`rev-filters.md::Low #4`) escalates to project-pass scope; the 16-symbol public-surface cohort meets the architecture-documentation hygiene rubric for Medium (a consumer reading `from django_strawberry_framework.filters import TypedFilter, GlobalIDFilter, LazyRelatedClassMixin` and grep-ing GLOSSARY finds nothing). The 0.0.8 release ships these symbols as `__all__` exports; the entries are warranted before the version-bump promotion.

**Recommended verbatim entry-text drafts** are NOT preserved in this artifact at full length per `worker-1.md` ("preserve the verbatim replacement text in the artifact — Worker 2 lifts it directly") — that calibration applies to single-symbol drift fixes where the existing entry needs verbatim replacement, not to a 16-entry first-cohort authoring pass. The right shape here is: Worker 2 reads `docs/SPECS/spec-027-filters-0_0_8.md` for each symbol's contract surface, drafts entries matching the existing GLOSSARY house style (`## SymbolName` heading, `**Status:** shipped (0.0.8).` line, body, `**See also:**` cross-refs, alphabetical placement, Index + Browse-by-category bullets), and offers the draft to the maintainer for review before commit. The joint-cut authoring is the maintainer-collaboration scope, not a mechanical drift fix.

## Low:

### L1 — `spec-025-scalar_map_helper-0_0_7.md` stale `TODO-ALPHA-029-0.0.11` references for the Upload scalar — actual card is `TODO-ALPHA-035-0.0.11`

Per `rev-scalars.md::Low #1`'s explicit project-pass forward, `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` cites `TODO-ALPHA-029-0.0.11` for the Upload scalar at multiple sites (`:69`, `:91`, `:100`, `:234`, `:611` per the spec content). The actual Upload scalar card is `TODO-ALPHA-035-0.0.11` per `KANBAN.md:657` (`### [TODO-ALPHA-035-0.0.11 — Upload scalar and file / image field mapping]`) and `docs/GLOSSARY.md:1014` ("next: [`Upload`](#upload-scalar) in `0.0.11`"); `TODO-ALPHA-029-0.0.11` is the `DjangoType` consumer-DX cleanup pass per `KANBAN.md:252`.

The `scalars.py` module docstring itself was already fixed in `rev-scalars.md`'s own cycle (the source-side `TODO-ALPHA-028` → `TODO-ALPHA-035-0.0.11` rotation); only the `docs/SPECS/` archived spec retains the stale reference.

**Recommended fix.** `sed -i '' 's/TODO-ALPHA-029-0.0.11/TODO-ALPHA-035-0.0.11/g' docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` then re-verify by `grep -n "TODO-ALPHA-029" docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` returns zero. The `TODO-ALPHA-029-0.0.11` token is exclusively the Upload-scalar reference in this spec; no other meaning to preserve. Citation-hygiene Low per the `worker-memory/worker-1.md` calibration "Severity calibration for citation hygiene. Stale TODO-ALPHA-NN anchors … are Low (citation hygiene) … when the prose the citation supports is correct against the actual cited content — only the pointer rotted."

### L2 — GLOSSARY drift on `OptimizerError` and `DjangoStrawberryFrameworkError` — public `__all__` exports without GLOSSARY entries

Per `rev-exceptions.md::Low #2` (forwarded to project pass), `django_strawberry_framework/exceptions.py::__all__` exports three classes (`DjangoStrawberryFrameworkError`, `ConfigurationError`, `OptimizerError`); only `ConfigurationError` has a GLOSSARY entry (`docs/GLOSSARY.md:196-209`). The base class `DjangoStrawberryFrameworkError` is the explicit single-`except` entry point per the base-class docstring, and `OptimizerError` is the typed marker for `types/resolvers.py::_check_n1` and `optimizer/field_meta.py::FieldMeta.from_django_field`'s descriptor guard.

`rev-types__resolvers.md::Low #3` records the in-cycle interaction: the `Strictness mode` GLOSSARY entry's `RuntimeError → OptimizerError` fix preserves `[OptimizerError](#optimizererror)` anchor reference text that will only resolve once the `OptimizerError` GLOSSARY entry lands.

**Recommended fix.** Author two GLOSSARY entries paired with the M4 filter-cohort authoring pass:

- `## OptimizerError` (Status: `shipped (0.0.4)` since the exception type ships from the initial alpha; raise contexts: strictness-mode N+1 detection at `types/resolvers.py::_check_n1`, descriptor-shape guard at `optimizer/field_meta.py::FieldMeta.from_django_field`).
- `## DjangoStrawberryFrameworkError` (Status: `shipped (0.0.1)`; the single-`except` entry-point for consumers who want to catch the package's typed errors without enumerating each subclass).

Defer until the M4 joint-cut authoring pass — same Worker 2 spawn authors both. Trigger per the per-file artifact ("a third exception subclass landing under `exceptions.py`, OR the project-pass artifact deciding to enforce uniform `__all__` ↔ GLOSSARY coverage"): the project pass declines to land per-file ahead of the M4 cohort, so the trigger is satisfied at the M4 spawn boundary.

### L3 — GLOSSARY drift on `DST_OPTIMIZER_*` context-key string literals (5 keys) and `FieldMeta` typed wrapper

Per `rev-optimizer___context.md::Low #2`, `rev-optimizer__field_meta.md::Low #2`, and `rev-optimizer.md::Low #2 / #3` (forwarded to project pass), the optimizer subpackage's cross-module-cited context-key literals (`dst_optimizer_planned`, `dst_optimizer_lookup_paths`, `dst_optimizer_strictness`, plus the two already named in `FK-id elision` / `Strictness mode` GLOSSARY entries) AND the `FieldMeta` typed wrapper (cross-module public-import surface at `types/base.py:39`, `types/definition.py:10`, `types/converters.py:49`, `types/resolvers.py:43`, `types/finalizer.py:54`) lack GLOSSARY entries.

Per the joint-cut deferral pattern (`rev-optimizer___context.md` framing), these are "internal-but-cross-module-visible optimizer symbols best authored together at the project layer alongside their first cohort of consumer documentation." The first cohort already exists today — `DjangoOptimizerExtension`, `OptimizerHint`, `Plan cache`, `FK-id elision`, `only() projection`, `Schema audit`, `Strictness mode`, `Queryset diffing` all have current entries with drift fixes already shipped in their per-file cycles.

**Trigger for action.** Per the consolidated calibration "Internal-mechanics GLOSSARY absence is correct convention" applied uniformly across the optimizer + types subpackage cycles: the 5 `DST_OPTIMIZER_*` literals and `FieldMeta` are the internal mechanics surfaces that the consumer contract surfaces through documented umbrella entries. They are CORRECTLY absent today. Forward to project pass is a "positive audit-trail confirmation" per `rev-optimizer.md::Low #4` framing, NOT a recommendation to add entries.

**Project-pass decision.** Confirm correct-by-convention; do NOT add entries. Defer until either (a) `_context.py` loses its underscore prefix and the read helper becomes public consumer API (today `_context` is a `_`-prefixed internal module per `optimizer/__init__.py:14-17`), OR (b) a sixth `dst_optimizer_*` key lands (today there are five, well below the GLOSSARY-cohort threshold), OR (c) `FieldMeta` consumers grow outside the package boundary (today every consumer is internal). No in-cycle GLOSSARY edit warranted; the calibration is the audit trail.

### L4 — GLOSSARY drift on `conf.settings` / `DJANGO_STRAWBERRY_FRAMEWORK` settings-dict surface

Per `rev-conf.md::Low #2` and the project-pass forward, `docs/GLOSSARY.md` has no entry for the `conf` module, the `settings` singleton, `_normalize_user_settings`, or `DJANGO_STRAWBERRY_FRAMEWORK` as a settings-key surface. The `ConfigurationError` entry at `docs/GLOSSARY.md:196-209` reads as illustrative not exhaustive.

Per `AGENTS.md` rule 20 ("Add settings keys only when the feature that needs them lands; do not preemptively populate") and per the per-file deferral, the consumer-visible settings-dict contract is unstable today — there are zero shipped settings keys at `0.0.8`. The `HIDE_FLAT_FILTERS` key per `rev-filters__inputs.md::Low #5` is the closest candidate but it's not yet documented as consumer-facing.

**Project-pass decision.** Defer per `rev-conf.md` framing. Trigger: the first real consumer-facing settings key lands (most likely under spec-027 / spec-028 follow-ups when `HIDE_FLAT_FILTERS` graduates to documented API or a new key surfaces). At that point, author `## DJANGO_STRAWBERRY_FRAMEWORK settings dict` and `## conf.settings` together as one cohort. The forward is purely audit-trail at project-pass scope; no in-cycle edit.

### L5 — Process-global ledger cross-cycle-clear contract for `_helper_referenced_filtersets` / `_field_specs` / `_materialized_names` / `_dynamic_filterset_cache` is documented at each site but not pinned by a direct cross-substrate regression test

Per `rev-filters.md::Low #3 / Low #6` (forwarded to project pass), the filter-subsystem ships four process-global ledgers with intentionally divergent clear contracts (per `rev-filters__factories.md::What looks solid` and `rev-filters__inputs.md::What looks solid`):

- `_helper_referenced_filtersets` (`filters/__init__.py:48`) — cleared by `registry.clear()` via cycle-safe local import.
- `_field_specs` and `_materialized_names` (`filters/inputs.py:133-150`) — cleared by `clear_filter_input_namespace` (driven by `registry.clear()`).
- `_dynamic_filterset_cache` (`filters/factories.py:40-46`) — NO clear hook by `M-filters-3` review decision (test-isolation nicety only).

The autouse `_isolate_registry` fixture in `tests/filters/test_inputs.py` (per `rev-filters__inputs.md::What looks solid`) clears the ledgers directly per-test — but does NOT exercise the cross-substrate contract where `registry.clear()` itself reaches into `filters/__init__.py` via cycle-safe local import to drop `_helper_referenced_filtersets`.

**Why Low and not Medium.** The cross-substrate clear IS documented at each site (audit-trail comments at `filters/__init__.py:42-47`, `filters/inputs.py:133-140`, `filters/inputs.py:144-150`, `filters/factories.py:40-46`) AND is indirectly pinned by the autouse fixture's explicit clear of both `_field_specs` and `_helper_referenced_filtersets`. A latent regression risk exists if a future refactor removes the local import inside `registry.clear()` without affecting the autouse fixture; the existing test suite would not catch the regression.

**Recommended fix.** Defer with explicit trigger: "when a consumer-facing reload story lands (e.g. Django dev-server autoreloader rebuild without `registry.clear()`) OR when a fifth process-global ledger lands under the filter / order / aggregate subsystem family." Today the four-ledger divergence is correctly scoped and documented; a coordinated clear-hook story (single umbrella `clear_filter_subsystem_state()`) was evaluated and rejected at `rev-filters.md::What looks solid` because the per-cache lifecycle policies diverge intentionally. A single regression test pinning "after `registry.clear()`, `_helper_referenced_filtersets` and `_field_specs` are both empty" would close the gap cheaply but is not warranted today given the autouse fixture coverage.

### L6 — `_helper_referenced_filtersets` monotonic growth contract is recorded for visibility — no edit warranted

Per `rev-filters.md::Low #6` (forwarded to project pass), `_helper_referenced_filtersets` grows monotonically over a process lifetime; bounded by the count of distinct `FilterSet` subclasses (small and stable). The behavior matches `_field_specs`'s same `_isolate_registry`-only clear pattern. In production this is fine; in long-running consumer reload scenarios (Django autoreloader rebuilding models without calling `registry.clear()`), the ledger retains stale class identities until process exit.

**Project-pass decision.** No edit warranted today; the joint-cut deferral pattern of spec-027 Decision 10 is correctly scoped. The audit trail is the comment at `filters/__init__.py:42-47`; the trigger from L5 above is the same trigger that would re-open this Low. Recorded for project-pass visibility per the per-file artifact's explicit routing.

### L7 — Package-wide `spec-014 H1` rev-anchor citations under `types/` survive cleanly — defer-with-trigger for the project-pass spec-NN sweep

Per `rev-types__relations.md::Low #2` and `rev-types.md::L2`, two sites cite `spec-014 H1` as a rev-anchor (the registry-side identity contract closing the import-order trap):

- `django_strawberry_framework/types/base.py:936` (`# the primary (the import-order trap closed by spec-014 H1).`).
- `django_strawberry_framework/types/relations.py:4-5` (per `rev-types__relations.md::Low #2`).

The cited reasoning legitimately matches `spec-014` content (the import-order trap H1 closure); the anchor is rev-relative not path-relative, so it survives `docs/SPECS/NEXT.md` Step 8 archive sweeps. Drift risk is still non-zero — the optimizer folder swept two `spec-014 → spec-018` rotations (`rev-optimizer__extension.md`, `rev-optimizer__walker.md`) because the cited prose actually lived in `spec-018-meta_primary-0_0_6.md`.

**Project-pass decision.** Defer per the per-file artifact's calibration. Trigger: "a regression in the spec mapping fires OR the project-pass spec-NN sweep verifies all `types/`-side `spec-014 H1` cites against the actual spec contents." At project-pass scope: a full spec-NN sweep across `django_strawberry_framework/**/*.py` is beyond the project-pass charter and would inflate the cycle. The two sites are recorded here so the next REVIEW cycle (likely the `0.0.8` cycle) can run the sweep against the version-bump baseline.

### L8 — Top-level `__init__.py` `# noqa: E402` discipline is correct; one paper-trail observation

`django_strawberry_framework/__init__.py:8-24` carries six `# noqa: E402` markers on the imports below the `logger = logging.getLogger("django_strawberry_framework")` assignment. The marker is load-bearing per the inline comment at `:18` ("logger must exist before subpackage imports"). The pattern is correct: `logger` is established before `from strawberry import auto` and the five `from . …` imports so that subpackages can do `from .. import logger` without triggering circular-import-at-import-time issues.

The shadow overview confirms the file shape: 7 imports / 0 symbols / 0 control-flow hotspots / 0 calls of interest / 0 repeated literals / 0 TODOs. The `__all__` tuple at `:28-39` exports 10 symbols alphabetically: `BigInt`, `DjangoListField`, `DjangoOptimizerExtension`, `DjangoType`, `OptimizerHint`, `SyncMisuseError`, `__version__`, `auto`, `finalize_django_types`, `strawberry_config`. Each export has a GLOSSARY entry per `docs/GLOSSARY.md`:

- `BigInt` — `docs/GLOSSARY.md:176`.
- `DjangoListField` — `docs/GLOSSARY.md:313`.
- `DjangoOptimizerExtension` — `docs/GLOSSARY.md:345`.
- `DjangoType` — `docs/GLOSSARY.md:375`.
- `OptimizerHint` — `docs/GLOSSARY.md` (per the per-file artifact `rev-optimizer__hints.md`).
- `SyncMisuseError` — `docs/GLOSSARY.md` (per the per-file artifact `rev-types__relay.md::M1`).
- `finalize_django_types` — `docs/GLOSSARY.md:474`.
- `strawberry_config` — `docs/GLOSSARY.md:1059`.
- `auto` — re-export of `strawberry.auto`; not listed in GLOSSARY but documented inline at `__init__.py:6-7` (correct per consumer-import-path framing — the entry would be for Strawberry's `auto`, not ours).
- `__version__` — module-version string; not a consumer concept that warrants GLOSSARY entry.

**Project-pass observation.** The `logger` symbol IS consumer-facing per the comment at `:13-15` ("Consumer-facing: the name is the key clients use in Django's `LOGGING` config dict, so it is part of the public surface even though it is not in `__all__`"). The string `"django_strawberry_framework"` lives in exactly one source location AND is consumed by subpackages via `from .. import logger` per `optimizer/__init__.py`. `docs/GLOSSARY.md` does NOT have a dedicated `## logger` entry; the name `"django_strawberry_framework"` as the Django `LOGGING`-config key surfaces in CHANGELOG entries and the consumer-facing README only indirectly.

**No edit warranted.** The current factoring is correct: `logger` is excluded from `__all__` deliberately (per the `:13-15` comment — "it is part of the public surface even though it is not in `__all__`"), and a `## logger` GLOSSARY entry would compete with `## django_strawberry_framework Django LOGGING dict key` framing. Defer until a consumer-facing logging-configuration documentation pass lands; the trigger is "the first time a consumer cuts a ticket asking how to configure log levels for the package" OR "a Sphinx autodoc pass that needs the `logger` symbol named."

### L9 — Plan archive note: `orders/` subpackage exists on disk but is NOT in the active `0.0.7` plan checklist

`ls django_strawberry_framework/` shows an `orders/` subpackage at the top level (alongside `filters/`, `management/`, `optimizer/`, `testing/`, `types/`, `utils/`). The `0.0.7` review plan at `docs/review/review-0_0_7.md:50-99` does NOT list any `rev-orders__*.md` artifacts; per worker-memory `worker-1.md`'s "Concurrent maintainer work attribution" calibration, the `orders/` subpackage is concurrent spec-028 Slice 3 maintainer work landed post-baseline (commits `b8fbd74` / `f3a0777`).

Shadow overviews for `orders/` siblings DO exist under `docs/shadow/` (regenerated by the plan-time `--all` sweep): `django_strawberry_framework__orders____init__.overview.md`, `__orders__base.overview.md`, `__orders__factories.overview.md`, `__orders__inputs.overview.md`, `__orders__sets.overview.md`. The subpackage is out-of-scope for the 0.0.7 review cycle but in-scope for whatever cycle opens next (likely `review-0_0_8.md`).

**Project-pass observation.** Recorded so Worker 0's closeout pass and the next-cycle planning step have the audit trail. The cross-folder `_camel_case` extraction (DRY analysis bullet 1) is the most concrete carry-forward for the 0.0.8 cycle to pick up.

## What looks solid

### DRY recap

- **Existing patterns reused at package scope.** The package's single source of truth for cross-cutting contracts is consistently single-sited: `_django_patches.py::_is_database_failure` (single home, consumed by `testing/_wrap.py:27`); `optimizer/_context.py:34-38`'s five `DST_OPTIMIZER_*` constants (single home, consumed by `optimizer/extension.py:48-52` and `types/resolvers.py:36-38`); `optimizer/hints.py::hint_is_skip` (single home, consumed by `optimizer/walker.py:433` and `optimizer/extension.py:721`); `optimizer/__init__.py:26`'s `logger` re-export of the package-level `logging.getLogger("django_strawberry_framework")` (`__init__.py:16` — single source of truth, consumed by `optimizer/extension.py:46` and `optimizer/walker.py:16`); `utils/relations.py::RelationKind` closed-`Literal` + `MANY_SIDE_RELATION_KINDS` + `is_many_side_relation_kind` triple (single home, consumed across `optimizer/walker.py:14`, `optimizer/field_meta.py:26,31`, `types/relations.py:24`, `types/resolvers.py:50`); `utils/strings.py::snake_case` + `pascal_case` (single home, consumed across `optimizer/walker.py:15`, `types/base.py:42`, `types/finalizer.py:56`, `types/converters.py:52`, `sets_mixins.py:34`); `utils/typing.py::unwrap_graphql_type` (single home, consumed at `optimizer/extension.py:45`); `filters/inputs.py::INPUTS_MODULE_PATH` (single source of truth, five consumers); `filters/inputs.py::_LOGIC_KEYS` + `LOOKUP_NAME_MAP` (single source of truth, imported by `filters/sets.py`); `sets_mixins.py::ClassBasedTypeNameMixin` + `LazyRelatedClassMixin` (canonical home for cross-subsystem shared mixins, consumed by `filters/base.py:37` and `filters/sets.py:31` today, will be consumed by `orders/` in the next cycle); `types/definition.py::graphql_type_name` (single home, eight consumers); `types/relay.py::_RELAY_RESOLVER_DEFAULTS` (single home for four Relay resolver method names). Every cross-folder consolidation that the per-file/folder artifacts called out has been either landed in-cycle (the act-now `FieldMeta._from_field_shape` extraction at `rev-types.md`) or deferred-with-explicit-trigger (the `_camel_case` cross-folder extraction at `rev-utils.md`; the `lazy_input_annotation` cross-subsystem helper at `rev-filters.md`).

- **New helpers considered at package scope.** A single `clear_filter_subsystem_state()` umbrella collapsing `_helper_referenced_filtersets` + `_field_specs` + `_materialized_names` + `_dynamic_filterset_cache` was evaluated at `rev-filters.md::What looks solid` and rejected because the per-cache clear-vs-no-clear policies diverge intentionally per `M-filters-3` review decision. A folder-level `management/_common.py` (cross-management-command shared helpers) was evaluated at `rev-management.md` and rejected because the single concrete management command today is a single consumer below the package's DRY threshold. A folder-level `_walk_selection_tree(on_node, on_fragment_def)` higher-order helper consolidating the three `optimizer/extension.py` walkers was evaluated at `rev-optimizer.md` and deferred until a third walker lands. A package-wide `path::QualifiedName` citation convention enforcement script was evaluated implicitly by the per-file `path:symbol_name → path::QualifiedName` sweeps and confirmed clean at folder scope per `rev-types.md::L4` (zero remaining single-colon citations under `types/`); no enforcement script warranted today because the convention is uniformly applied.

- **Duplication risk at package scope.** Three categories of intentional duplication, all documented as load-bearing sibling design and recorded across the per-file / folder artifacts: (1) Mirrored sync/async pairs (`apply_sync`/`apply_async`, `_apply_get_queryset_sync`/`_apply_get_queryset_async`, `_derive_related_visibility_querysets_sync`/`_derive_related_visibility_querysets_async`, `_resolve_node_default`/`_resolve_nodes_default`, `_bind_filterset_owner`/`_bind_orderset_owner`, `_bind_filtersets`/`_bind_ordersets`, `_resolve_array_field`/`_resolve_hstore_field`) — kept as load-bearing distinctions for static call-site routing; consolidation gates on a third call site landing per the consolidated calibration in `worker-memory/worker-1.md`. (2) Mirrored filter/order sidecar binding pipeline in `types/finalizer.py` (the `_bind_filtersets`/`_bind_ordersets` four-subpass mirror at `:741-860` / `:632-738`) — correct per the load-bearing-distinction calibration plus the documented `related.orderset` Layer-2 force-resolution asymmetry. (3) Cross-file `getattr(field, "<flag>"/"<related>", default)` defensive-Protocol pattern across four sites under `types/` — correct because Django's `_meta` API returns heterogeneous shapes (forward `Field` / reverse `ForeignObject` / `ManyToOneRel` / `ManyToManyRel` / GFK descriptor) and consolidation through a helper would obscure the per-call defensive shape; partial subsumption by the act-now `FieldMeta._from_field_shape` extraction landed in `rev-types.md`.

### Other positives

- **Top-level `__init__.py` is a thin, correctly-scoped public-surface curator.** 39 source lines. Imports the framework's `logger` first (before any subpackage import) so subpackages can re-export it without circular-import-at-import-time risk. Imports `strawberry.auto` as the consumer-facing re-export so consumers can write `from django_strawberry_framework import auto` without importing strawberry directly. Imports the four cross-folder public symbols (`DjangoListField`, `DjangoOptimizerExtension`, `OptimizerHint`, `BigInt` + `strawberry_config`, `DjangoType` + `SyncMisuseError` + `finalize_django_types`) per a clean alphabetized `__all__` tuple. Version pin at `:26` (`__version__ = "0.0.8"`) matches `pyproject.toml:4`. No executable code beyond the `logger` assignment; no class definitions; no Django ORM markers (the two flagged by the shadow are pure import-line tokens, not ORM operations).

- **Public-API discipline across the package.** Every consumer-facing symbol exported through the top-level `__all__` traces back to a single canonical home: `BigInt` → `scalars.py`; `DjangoListField` → `list_field.py`; `DjangoOptimizerExtension` → `optimizer/__init__.py` → `optimizer/extension.py`; `DjangoType` / `SyncMisuseError` / `finalize_django_types` → `types/__init__.py` → `{base,relay,finalizer}.py`; `OptimizerHint` → `optimizer/hints.py`; `strawberry_config` → `scalars.py`; `auto` → strawberry re-export. The package-wide `from django_strawberry_framework import X` import path is the canonical consumer surface; the deeper paths (`from django_strawberry_framework.types import DjangoType`) work too but the top-level re-export is the recommended consumer entry. Each public symbol has a corresponding GLOSSARY entry; the absences flagged in M4 / L2 are first-cohort joint-cut deferrals, not coverage gaps in shipped public API.

- **Module-responsibility boundaries are clean at package scope.** `_django_patches.py` owns the Django Trac #37064 hardening unwrap-time half + `_is_database_failure` predicate. `apps.py` owns the `DjangoStrawberryFrameworkConfig` AppConfig + `ready()` hook that auto-applies `_django_patches.apply()`. `conf.py` owns the `DJANGO_STRAWBERRY_FRAMEWORK` settings dict reader (today an empty surface; no shipped keys). `exceptions.py` owns the three-class typed-error hierarchy. `list_field.py` owns `DjangoListField`. `registry.py` owns the model-keyed registry + identity contracts. `scalars.py` owns `BigInt` + `strawberry_config`. `sets_mixins.py` owns the cross-subsystem shared mixins (`ClassBasedTypeNameMixin`, `LazyRelatedClassMixin`). `filters/` owns the filter subsystem (six-layer pipeline + BFS factory + dynamic-cache + input namespace). `management/` owns Django management entry points (today: `export_schema`). `optimizer/` owns the cardinality-aware optimizer (extension + walker + plans + hints + field-meta + context). `testing/` owns the wrap-time half of Trac #37064 defense-in-depth. `types/` owns the type system (base + converters + definition + finalizer + relations + relay + resolvers). `utils/` owns the leaf-utility helpers (relations / strings / typing). Each subpackage's `__init__.py` documents its responsibility and curates the re-export surface.

- **Settings and configuration boundaries are tight.** `AGENTS.md` rule 20 ("Add settings keys only when the feature that needs them lands; do not preemptively populate") is honored package-wide: zero shipped consumer-facing settings keys at `0.0.8`. The `DJANGO_STRAWBERRY_FRAMEWORK` settings-dict surface is described per `AGENTS.md` rule 19 ("reads `DJANGO_STRAWBERRY_FRAMEWORK` from the consumer's settings dict; missing keys raise `AttributeError`"). The internal `HIDE_FLAT_FILTERS` key per `rev-filters__inputs.md::Low #5` is the only candidate; it is not yet documented as consumer-facing API. The `conf.settings` singleton's read-only nature and the `_normalize_user_settings` validator's load-time `ConfigurationError` raise are the documented configuration boundary; project pass confirms no leakage.

- **Optimizer/type/registry responsibility boundaries are well-factored.** The cross-folder act-now `FieldMeta._from_field_shape` extraction landed cleanly in `rev-types.md`'s cycle: `optimizer/field_meta.py` owns the shared shape builder (`_from_field_shape`); `optimizer/field_meta.py::FieldMeta.from_django_field` is the public typed-input entry; `types/resolvers.py::_field_meta_for_resolver`'s test-double fallback delegates to the shared shape with `is_relation=True`. The optimizer / types / registry split is one-way: `optimizer/` is the leaf consumed by `types/` and `filters/`; `types/` is consumed by `filters/`; `registry/` is consumed by all three; `utils/` is the strictest leaf (zero first-party imports). No circular import risk at module-load time anywhere in the package — the documented cycle-breaks (`types/base.py:99` `from ..filters.sets import FilterSet`; `types/definition.py:148-150` `from ..registry import registry, FieldDoesNotExist`) use function-local imports with "Do NOT hoist to module top" tripwires.

- **Test placement discipline matches AGENTS.md rule 9.** Per the per-file artifact carry-forwards: every subpackage carries its own `tests/<subpackage>/test_*.py` package-internal coverage (e.g. `tests/optimizer/test_walker.py`, `tests/types/test_base.py`, `tests/filters/test_inputs.py`, `tests/utils/test_strings.py`); every example-app behavior carries `examples/fakeshop/apps/<app>/tests/` per-app coverage; every live-HTTP GraphQL contract carries `examples/fakeshop/test_query/test_*.py` coverage. No test-tree drift surfaced across any per-file artifact. The `tests/base/` pair (`test_init.py`, `test_conf.py`) is correctly limited per AGENTS.md rule 6 ("both may grow, no new files added").

- **CHANGELOG.md is current at `0.0.8`'s shipped surface.** `CHANGELOG.md:18-26` (`## [Unreleased] / ### Added / Filtering subsystem`) and `CHANGELOG.md:28-66` (`## [0.0.7] - 2026-05-27`) carry the documented contracts; the only drift is the M2 sweep at `:33` + `:207` for the test/ → testing/ rename. The KANBAN link defs (`[card-*]: KANBAN.md#…`) and GLOSSARY link defs (`[glossary-*]: docs/GLOSSARY.md#…`) all resolve per spot-check.

- **GLOSSARY drift quick-check at project scope.** Of the 60+ public symbols / category headings in the package's `__all__` exports + subpackage `__all__` exports + cross-module-cited public surfaces, the in-cycle drift fixes already shipped at per-file scope cover: `DjangoType` (`rev-types__base.md::M1`), `get_queryset` (bundled), `SyncMisuseError` + `Relay Node integration` (`rev-types__relay.md::M1`), `Strictness mode` `RuntimeError → OptimizerError` (`rev-types__resolvers.md::M1`), `Schema export management command` (`rev-management__commands__export_schema.md::Medium`), `ConfigurationError` (`rev-optimizer__hints.md::Medium`, construction-time conflict rejection language). The remaining cohort-level work is M4 (16-symbol filter cohort + L2 exception siblings), correctly deferred to the joint-cut authoring pass per spec-027 Decision 10's pattern.

- **Citation hygiene at project scope.** The major spec-NN drift sweeps (`spec-014 → spec-018` across `optimizer/`, `spec-011 → spec-015` across `relay.py` + tests, `spec-016 → spec-020` for `list_field`, `spec-020 → spec-025` for `scalars`, `spec-021 → spec-027` across `filters/` 43 sites + `types/finalizer.py` 8 sites) all closed at per-file or folder-pass cycles. Project-pass forwards are limited to: M3 (`convert_relation` historical name in `docs/TREE.md` 3 sites), L1 (`TODO-ALPHA-029-0.0.11` Upload-scalar drift in `docs/SPECS/spec-025`), L7 (defer-with-trigger for the cross-package `spec-014 H1` rev-anchor sweep). `path::QualifiedName` convention is uniformly applied across `types/`, `optimizer/`, `utils/` per the per-file / folder-pass audits (`rev-types.md::L4`); no single-colon `path:symbol_name` regressions package-wide.

- **Ruff gates clean at project scope.** Per the per-file / folder-pass artifacts' validation runs: `uv run ruff format --check django_strawberry_framework/` consistently reports "all files already formatted" across every subfolder; `uv run ruff check django_strawberry_framework/` consistently reports "All checks passed!" (the one repo-wide `COM812`-vs-formatter warning is pre-existing global config noise, not a project-pass scope concern). The trailing-comma-layout enforcement per `scripts/check_trailing_commas.py` runs in pre-commit per AGENTS.md rule 17; no comma-layout regressions surfaced across any per-file artifact.

- **Cross-folder DRY landings discipline established.** The cross-folder `FieldMeta._from_field_shape` extraction landed cleanly in `rev-types.md`'s cycle — `optimizer/field_meta.py` got the new helper, `types/resolvers.py` collapsed to a one-line delegation, no test surface change required (existing tests pin both branches). The pattern is the canonical template for future cross-folder consolidations: source-only edit, two-file diff, behaviour preserved by existing test coverage, second-closing folder owns the landing. The `_camel_case` extraction queued for the 0.0.8 `orders/` folder pass will follow the same template.

- **Three-spawn cycle integrity holds across the package.** Every per-file artifact closed at `Status: verified` before this project pass spawned. No `revision-needed` loops, no false-premise rejections leaking across cycles, no Worker 2 self-approval (the Worker 2 / Worker 3 split is non-waivable per `REVIEW.md` "Subagent dispatch"). The standard three-spawn shape ran for the substantive Mediums (the `_isolate_registry` ledger contract; the spec-021 → spec-027 mass-rewrite; the `_normalize_range_value` partial-range drop); the consolidated single-spawn shape (shape #4) handled the GLOSSARY-bearing Mediums; the no-source-edit shape (shape #5) handled the folder-pass scopes that produced zero in-cycle edits. The discipline is consistent and the cycle artifacts are the audit trail.

### Summary

The package-level pass closes the 0.0.7 review cycle's project scope cleanly: one Medium for a workflow-hygiene defect (active-plan / source-version mismatch at `0.0.7` plan vs `0.0.8` source), three Mediums for cross-package drift sweeps (CHANGELOG test/ → testing/ rename rot at 2 sites; TREE.md `convert_relation` historical-name drift at 3 sites; GLOSSARY filter-subsystem first-cohort 16-symbol joint-cut deferral), and nine Lows split across forwarded drift fixes, joint-cut GLOSSARY deferrals (`OptimizerError` / `DjangoStrawberryFrameworkError`; `DST_OPTIMIZER_*` literals + `FieldMeta`; `conf.settings`), and positive-audit-trail confirmations (top-level `__init__.py` shape, package-wide `path::QualifiedName` convention compliance, cross-substrate clear contract documentation discipline). Five DRY items at package scope, all defer-with-explicit-trigger: cross-folder `_camel_case` extraction (gated on the 0.0.8 cycle's `orders/` folder pass), `lazy_input_annotation` helper (gated on a second sibling subsystem reaching for the same Strawberry `LazyType.resolve_type` ForwardRef-wrap), package-wide submodule `__all__` convention pass (gated on a major-version-bump or a fourth-public-symbol-per-submodule trigger), package-wide backtick-convention pass (gated on a Sphinx autodoc pass or consumer-facing docs site landing), and one "None — single source of truth" bullet for `__init__.py` itself. The act-now DRY landings already shipped at per-file / folder-pass scope (the cross-folder `FieldMeta._from_field_shape` extraction at `rev-types.md` is the canonical template). Top-level `__init__.py` review confirms a 39-line public-surface curator with correct `# noqa: E402` discipline, correctly-curated 10-symbol `__all__`, and load-bearing `logger` declaration ahead of subpackage imports. Shape #5 is **DISQUALIFIED** — M2 (CHANGELOG sweep), M3 (TREE.md sweep), and L1 (spec-025 stale-anchor sweep) all require real source edits at Worker 2 spawn time; M4 (filter-cohort GLOSSARY authoring) is deferred to a joint-cut authoring pass per the spec-027 Decision 10 pattern but is in-cycle Medium scope. M1 (plan-version mismatch) is Worker 0's closeout responsibility, not a Worker 2 source edit. Standard three-spawn cycle applies.

---

## Fix report (Worker 2)

Consolidated single-spawn pass per dispatch — M2 (CHANGELOG `test` → `testing` rename) + M3 (TREE.md `convert_relation` → `resolved_relation_annotation` rename) + L1 (spec-025 `TODO-ALPHA-029-0.0.11` → `TODO-ALPHA-035-0.0.11` rename). M1 routed to Worker 0 closeout per dispatch (NO action this pass). M4 deferred per artifact (NO action). L2-L9 forwarded/deferred/no-edit per artifact.

### Files touched

- `CHANGELOG.md:33` — `Public export from [\`django_strawberry_framework.test\`][test-init]` → `Public export from [\`django_strawberry_framework.testing\`][test-init]` (preserves the `[test-init]` ref-id; consumer-facing public-import-path documentation now matches the on-disk subpackage at `django_strawberry_framework/testing/`).
- `CHANGELOG.md:207` — `[test-init]: django_strawberry_framework/test/__init__.py` → `[test-init]: django_strawberry_framework/testing/__init__.py` (link-def now resolves to the actual on-disk file). Post-edit `grep -n "django_strawberry_framework\.test\b\|test/__init__\.py" CHANGELOG.md` returns zero hits.
- `docs/TREE.md:214` — `converters.py        # convert_scalar, convert_choices_to_enum, convert_relation` → `converters.py        # convert_scalar, convert_choices_to_enum, resolved_relation_annotation` (current-on-disk-layout per-file comment now names the actual symbol per `django_strawberry_framework/types/converters.py::resolved_relation_annotation` and the rename audit-trail at `docs/SPECS/spec-018-meta_primary-0_0_6.md:139`).
- `docs/TREE.md:264` — same swap in the target-package-layout per-file comment (`convert_relation` → `resolved_relation_annotation`).
- `docs/TREE.md:357` — `test_converters.py   # ← convert_scalar / convert_relation / convert_choices_to_enum` → `test_converters.py   # ← convert_scalar / resolved_relation_annotation / convert_choices_to_enum` (current-on-disk test-tree per-file comment). Post-edit `grep -n "convert_relation" docs/TREE.md` returns zero hits. Comment-column alignment shifts slightly (longer string) but `docs/TREE.md` is a documentation tree, not source — alignment shift accepted per artifact M3 recommendation.
- `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` — six-site `TODO-ALPHA-029-0.0.11` → `TODO-ALPHA-035-0.0.11` swap via `sed -i '' 's/TODO-ALPHA-029-0\.0\.11/TODO-ALPHA-035-0.0.11/g'` (artifact L1 named five sites at `:69`, `:91`, `:100`, `:234`, `:611`; sed found six — the sixth at `:620` is the spec's `## Non-goals` paragraph naming the Upload card; same drift class, same rotation). Post-edit `grep -c "TODO-ALPHA-029" docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` returns `0`; `grep -c "TODO-ALPHA-035-0.0.11"` returns `6`.

### Tests added or updated

- None. All three edits are pure documentation surfaces (CHANGELOG entry prose + link def; reference-tree per-file comments; archived-spec citation hygiene). No source-code symbol changes, no behavior changes, no test surface to add or pin. The M3 rename target `resolved_relation_annotation` is already pinned by existing tests under `tests/types/test_converters.py` (per the existing test-converters surface enumerated in `docs/TREE.md:357` itself).

### Validation run

- `uv run ruff format .` — pass (213 files left unchanged; pre-existing `COM812`-vs-formatter warning is global-config noise, not in cycle scope).
- `uv run ruff check --fix .` — pass (All checks passed!).
- `git status --short uv.lock` — clean (uv.lock unchanged; no `uv run` dependency-change call surface in this cycle).

### Notes for Worker 3

- **M1 explicitly out of scope.** Dispatch prompt routes M1 (workflow-hygiene `0.0.7` plan vs `0.0.8` source-version mismatch) to Worker 0 closeout — NO action this pass; preserved here for Worker 3's audit trail and Worker 0 handoff.
- **M2 authorization.** The artifact body explicitly authorizes the M2 `CHANGELOG.md` edit per the AGENTS.md rule 21 "unless explicitly instructed" gate (artifact M2 prose: "this artifact's recommendation IS that explicit authorization, scoped narrowly to the two-site rename sweep"). Recorded in Changelog disposition below as `Warranted and edited`.
- **M3 grep verification.** Post-edit `grep -n "convert_relation" docs/TREE.md` returns zero hits; source-symbol `resolved_relation_annotation` confirmed present at `django_strawberry_framework/types/converters.py` (per existing-context source enumeration in the artifact and AGENTS.md test-placement context).
- **L1 grep verification.** Post-edit `grep -n "TODO-ALPHA-029" docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` returns zero; six-site rename confirmed (artifact named five — actual sweep found six because `:620` Non-goals paragraph also carried the stale token; same Upload-scalar drift class so same rotation applies).
- **M4 deferred per artifact.** GLOSSARY filter-cohort first-cohort 16-symbol joint-cut authoring pass deferred per artifact's own spec-027 Decision 10 framing (joint cut with orders cohort when `Meta.orderset_class` flips to `shipped (0.0.8)`); NO action this pass.
- **L2-L9 disposition per artifact.** All Lows either explicitly deferred-with-trigger, forwarded to joint-cut pass (L2 paired with M4), or positive-audit-trail confirmations (L3 / L6 / L7 / L8). L9 plan-archive note routes to Worker 0 closeout via M1 handoff. NO in-cycle edits.
- **No shadow file used.** All three edits were on documentation surfaces; the shadow overview for top-level `__init__.py` (`docs/shadow/django_strawberry_framework____init__.overview.md`) noted in the artifact was not consulted for the edits because no source-file fix was in cycle scope.
- **No false-premise rejections.** Every edit applied as the artifact specified; the L1 sixth-site discovery is a count-correction, not a premise rejection — the rename target and rotation are correct as artifact-specified.

---

## Verification (Worker 3)

### Logic verification outcome

Consolidated single-spawn terminal-verify. Every artifact finding accounted for against the diff at `git diff -- CHANGELOG.md docs/TREE.md docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`:

- M1: NO action — explicitly routed to Worker 0 closeout per dispatch (plan-vs-source version mismatch). Audit trail preserved in artifact; verified Worker 2 did not touch the plan file.
- M2 (CHANGELOG `test` → `testing` two-site rename): applied. `CHANGELOG.md:33` body and `:207` link def both swapped; ref-id `[test-init]` preserved. Post-edit `grep -n "django_strawberry_framework\.test\b\|test/__init__\.py" CHANGELOG.md` returns zero hits.
- M3 (TREE.md `convert_relation` → `resolved_relation_annotation` three-site rename): applied at `docs/TREE.md:214`, `:264`, `:357`. Post-edit `grep -n "convert_relation" docs/TREE.md` returns zero hits; source symbol `resolved_relation_annotation` confirmed at `django_strawberry_framework/types/converters.py:350`.
- M4 (GLOSSARY filter-cohort 16-symbol authoring): deferred per artifact's own spec-027 Decision 10 joint-cut framing. No in-cycle edit; pre-authorized by artifact prose.
- L1 (spec-025 `TODO-ALPHA-029-0.0.11` → `TODO-ALPHA-035-0.0.11`): applied. Artifact named 5 sites; Worker 2 widened to 6 (sixth at `:620` in `## Out of scope` Upload-promotion bullet). Verified the sixth site IS legitimately Upload-scalar drift (same Upload-card reference, same rotation applies) — widening is correct, not drift. Post-edit `grep -c "TODO-ALPHA-029" docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` returns 0; `grep -c "TODO-ALPHA-035-0.0.11"` returns 6.
- L2 (`OptimizerError` / `DjangoStrawberryFrameworkError` GLOSSARY): deferred — forwarded to M4 joint-cut pass per artifact.
- L3 (`DST_OPTIMIZER_*` literals + `FieldMeta` GLOSSARY): NO action — positive-audit-trail confirmation per artifact's "correct-by-convention" calibration.
- L4 (`conf.settings` / `DJANGO_STRAWBERRY_FRAMEWORK` GLOSSARY): deferred per artifact — first real consumer-facing settings key is the trigger.
- L5 (cross-substrate clear contract regression test): deferred per artifact — fifth process-global ledger or consumer-facing reload story is the trigger.
- L6 (`_helper_referenced_filtersets` monotonic growth): NO action — recorded for visibility; same trigger as L5.
- L7 (package-wide `spec-014 H1` rev-anchor sweep): deferred per artifact — next REVIEW cycle's spec-NN sweep is the trigger.
- L8 (top-level `__init__.py` `# noqa: E402` + `logger` exclusion): NO edit warranted; positive-audit-trail confirmation.
- L9 (orders/ subpackage not in 0.0.7 plan): NO action — routed to Worker 0 closeout via M1 handoff.

L1 widening from 5→6 sites is the only count discrepancy and is legitimate (matches the artifact's own M3 / `types/finalizer.py` precedent recorded in worker-3 memory: artifact heading counts may understate when sibling Lows overlap or when prose enumeration misses one occurrence; the load-bearing check is the post-fix grep, which is clean).

### DRY findings disposition

All five DRY items are defer-with-explicit-trigger per artifact (`_camel_case` cross-folder extraction gated on 0.0.8 `orders/` folder pass; `lazy_input_annotation` cross-subsystem helper; package-wide submodule `__all__` convention pass; package-wide backtick-convention pass; "None" for `__init__.py` itself). No DRY action in scope for this project-pass cycle; the act-now `FieldMeta._from_field_shape` extraction already landed in the `types/` folder-pass cycle (per worker-3 memory `## types/ (folder pass)`).

### Temp test verification

None used. All three edits are pure documentation surfaces (CHANGELOG prose + link def; TREE.md per-file comments; archived-spec citation hygiene); no behavior change to pin.

### Changelog disposition verification

`Warranted and edited`. `git diff -- CHANGELOG.md` matches the artifact's M2 two-site rename verbatim (body at `:33` swaps `django_strawberry_framework.test` → `django_strawberry_framework.testing` preserving `[test-init]` ref-id; link def at `:207` swaps target path). Authorization is cited explicitly in the artifact body's M2 prose ("this artifact's recommendation IS that explicit authorization, scoped narrowly to the two-site rename sweep") per AGENTS.md rule 21 ("Do not update CHANGELOG.md unless explicitly instructed"). The disposition section also re-cites the dispatch prompt's confirmation. No other CHANGELOG hunk; the M3 and L1 edits target `docs/TREE.md` and `docs/SPECS/spec-025-…` which do not warrant CHANGELOG entries (pure citation-hygiene with no shipped-symbol behavior change).

### Validation

- `uv run ruff format --check .` — pass (213 files already formatted; pre-existing COM812 global-config warning is not in scope).
- `uv run ruff check .` — pass (All checks passed!).

### Verification outcome

`cycle accepted; verified`.

---

## Comment/docstring pass

Consolidated into this single-spawn pass per dispatch. All three in-cycle edits ARE documentation/comment edits (CHANGELOG prose + link-def; TREE.md per-file comments; archived-spec citation hygiene) — there are no source-code docstrings or comments to update separately. The logic + comment surfaces collapse into the single set of edits enumerated above.

### Files touched

(Same set as Fix report above — pure documentation surfaces; no source-file docstrings touched.)

### Per-finding dispositions

- M1: NO action — routed to Worker 0 closeout per dispatch.
- M2: Applied (CHANGELOG.md:33 + :207 `test` → `testing` rename, two sites). Authorized by artifact body.
- M3: Applied (docs/TREE.md:214 + :264 + :357 `convert_relation` → `resolved_relation_annotation` rename, three sites).
- M4: Deferred per artifact (joint-cut authoring pass with orders cohort).
- L1: Applied (six-site `TODO-ALPHA-029-0.0.11` → `TODO-ALPHA-035-0.0.11` rename in `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`; one more site than artifact named — sixth site at `:620` Non-goals paragraph carries the same Upload-scalar drift, same rotation applies).
- L2: Deferred — forwarded to M4 joint-cut authoring pass.
- L3: NO action — positive-audit-trail confirmation per artifact ("correct-by-convention; do NOT add entries").
- L4: Deferred — first real consumer-facing settings key landing is the trigger.
- L5: Deferred — fifth process-global ledger or consumer-facing reload story is the trigger.
- L6: NO action — recorded for visibility; same trigger as L5.
- L7: Deferred — project-pass spec-NN sweep at next REVIEW cycle is the trigger.
- L8: NO edit warranted — `# noqa: E402` discipline correct, `logger` exclusion-from-`__all__` deliberate per inline comment.
- L9: NO action — routed to Worker 0 closeout via M1 handoff.

### Validation run

- `uv run ruff format .` — pass (213 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).

### Notes for Worker 3

Same as Fix report above. Consolidated single-spawn means logic + comment dispositions land together; no separate comment-pass artifact section to verify.

---

## Changelog disposition

### State

`Warranted and edited`.

### Reason

The artifact M2 prose explicitly authorizes the `CHANGELOG.md` test/ → testing/ rename sweep as the cycle's explicit `CHANGELOG.md` edit permission, scoped narrowly to the two-site rename ("Per `AGENTS.md` rule 21 ('Do not update CHANGELOG.md unless explicitly instructed') the edit needs explicit project-pass authorization — this artifact's recommendation IS that explicit authorization, scoped narrowly to the two-site rename sweep"). The dispatch prompt confirms this authorization ("The project-pass artifact body explicitly authorizes this CHANGELOG edit per dispatch"). No other CHANGELOG hunk in scope; the M3 edits target `docs/TREE.md` and the L1 edits target `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` — neither requires a CHANGELOG entry because both are pure documentation citation-hygiene fixes (no consumer-visible behavior change, no public-API change, no shipped-symbol rename).

### What was done

Two-site rename inside `CHANGELOG.md`:

1. `CHANGELOG.md:33` — `Public export from [\`django_strawberry_framework.test\`][test-init]` → `Public export from [\`django_strawberry_framework.testing\`][test-init]`. Preserves the `[test-init]` ref-id; the consumer-visible public-import-path text now matches the actual on-disk subpackage at `django_strawberry_framework/testing/`. Consumers who copy-paste the import path from this CHANGELOG bullet against `0.0.7` will now write `from django_strawberry_framework.testing import safe_wrap_connection_method` (which works) instead of `from django_strawberry_framework.test import safe_wrap_connection_method` (which raises `ModuleNotFoundError`).
2. `CHANGELOG.md:207` — `[test-init]: django_strawberry_framework/test/__init__.py` → `[test-init]: django_strawberry_framework/testing/__init__.py`. Link def now resolves to the actual on-disk file; reference-style markdown link from `:33` resolves correctly post-rename. Per AGENTS.md rule 28, the link def lives under the existing `<!-- django_strawberry_framework/ -->` group header (no group-header move needed because the target path stays in the same subpackage root).

Post-edit `grep -n "django_strawberry_framework\.test\b\|test/__init__\.py" CHANGELOG.md` returns zero hits.

### Validation run

- `uv run ruff format .` — pass (213 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!).

---

## Iteration log

(Append-only.)
