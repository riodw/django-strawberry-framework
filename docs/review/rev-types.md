# Review: `django_strawberry_framework/types/` (folder pass)

Status: verified

## DRY analysis

- **Act-now — cross-folder `FieldMeta._from_field_shape(field, *, is_relation)` extraction.** `types/resolvers.py::_field_meta_for_resolver:188-218` (the `not hasattr(field, "is_relation")` test-double fallback branch) line-for-line duplicates `optimizer/field_meta.py::FieldMeta.from_django_field:139-164` — the cardinality-gated nullable rule (`is_m2m or is_o2m → False`; `reverse_one_to_one or getattr(field, "null", False)`) followed by the same 9-keyword-argument `FieldMeta(...)` constructor call (`name`, `is_relation`, `many_to_many`, `one_to_many`, `one_to_one`, `nullable`, `related_model`, `attname`, `target_field_name`, `target_field_attname`, `reverse_connector_attname`, `auto_created`). The only behavioural difference is that the resolver-side fallback hard-codes `is_relation=True` (the test-double fallback fires only when the field has no `is_relation` attribute and the caller is by definition asking about a relation field) while the canonical builder reads `bool(field.is_relation)`. Recommended consolidation: extract `FieldMeta._from_field_shape(field, *, is_relation: bool) -> FieldMeta` carrying the 11-line shared body to `optimizer/field_meta.py`; `FieldMeta.from_django_field` becomes a guard-and-delegate (`if not hasattr(field, "name") or not hasattr(field, "is_relation"): raise OptimizerError(...); return cls._from_field_shape(field, is_relation=bool(field.is_relation))`); `_field_meta_for_resolver`'s fallback collapses to `return FieldMeta._from_field_shape(field, is_relation=True)`. Per `rev-optimizer.md` folder-pass calibration ("when a cross-folder act-now DRY opportunity's second call site is in a different folder, the second-closing folder owns the extraction"), this is the second-closing folder and the right place to land it. Cite sites: `optimizer/field_meta.py::FieldMeta.from_django_field #"is_m2m = bool(getattr(field"` and `types/resolvers.py::_field_meta_for_resolver #"is_m2m = bool(getattr(field"`. Regression coverage: existing tests `tests/optimizer/test_field_meta.py` (canonical builder) plus `tests/types/test_resolvers.py:48-86`, `:446-481` (test-double fallback) pin both branches; no new test surface needed because the extraction preserves identical observable behaviour.

- **Defer-with-trigger — `_target_definition_for_model(model)` shared helper across `types/definition.py:172` and the `filters/sets.py::_owner_resolve_target` mirror.** `definition.py::related_target_for #"target_type = registry.primary_for(target_model)"` and `filters/sets.py::_owner_resolve_target` both walk the "primary, else single registered type, else None" resolution rule but the filter-side mirror reaches through `getattr(owner, "related_target_for", None)` rather than the registry directly — so the two sites are not yet near-twins. Quote-able trigger: "third caller of the `primary_for + get + get_definition` funnel lands (most plausibly an `aggregates` or `orders` subsystem at spec-028 Slice 3)". Same calibration as the per-file DRY bullet in `rev-types__definition.md`; folder pass restates it so the next DRY cycle picks up both sites in one sweep. Cite sites: `types/definition.py #"target_type = registry.primary_for(target_model) or registry.get(target_model)"` and `filters/sets.py::_owner_resolve_target`.

- **Defer-with-trigger — cross-file `getattr(field, "is_relation"/"related_model", default)` defensive-Protocol pattern at four sites under `types/`.** `types/base.py:920` (`getattr(field, "related_model", None) is None`), `types/definition.py:165` (`getattr(model_field, "is_relation", False)`), `types/definition.py:168` (`getattr(model_field, "related_model", None)`), and `types/resolvers.py:188-218` (eight `getattr` calls with the same defensive-Protocol shape). Today's four sites each consume the heterogeneous Django-`_meta` return shape (forward `Field` / reverse `ForeignObject` / `ManyToOneRel` / `ManyToManyRel` / GFK descriptor) and the per-call list of attributes differs by purpose. Trigger: "a fifth site adds the same `getattr(field, "is_relation"/"related_model")` defensive pair OR `optimizer/field_meta.py::_DjangoFieldLike` Protocol grows a `target_field` attribute that `types/` callers can rely on by static typing rather than `getattr`". Until then, each site documents its per-axis defensive shape in-line and the cross-file duplication is structural (Django ORM API), not consolidatable through a single helper.

## High:

None.

## Medium:

### M1 (consolidated forward): GLOSSARY drift on internal/public-API symbol coverage — bundled forward to `rev-django_strawberry_framework.md`

Per-file artifacts each ran their own GLOSSARY drift quick-check and landed in-cycle edits where the symbol was a primary public surface (`rev-types__base.md::M1` for `DjangoType` and `get_queryset`; `rev-types__relay.md::M1` for `SyncMisuseError` + `Relay Node integration`; `rev-types__resolvers.md::M1` for `Strictness mode`'s `OptimizerError` vs `RuntimeError`). Two GLOSSARY items remain forwarded from per-file siblings to project pass per the joint-cut deferral pattern (spec-027 Decision 10): (a) `finalize_django_types` Phase 2.5 enumeration deferred to per-`Meta.*sidecar*_class` entries pending `Meta.orderset_class` flip to `shipped (0.0.8)` (`rev-types__finalizer.md::Low #8`); (b) the internal-mechanics absences for `PendingRelation` / `PendingRelationAnnotation` (`rev-types__relations.md`), `DjangoTypeDefinition` / `related_target_for` / `graphql_type_name` / `_related_target_cache` (`rev-types__definition.md::Low #5`), and the `relay.py` internal helpers (`rev-types__relay.md::L6`) are correct convention per `optimizer/__init__.py:14-17` "internal implementation details" framing and need no in-cycle edit. Restated at folder scope so the project pass author lands (a) and confirms (b) in one sweep alongside the filter-subsystem joint-cut forwards from `rev-filters.md`. No folder-level GLOSSARY Medium — every public-surface drift already shipped its in-cycle fix; the deferrals are correct-by-convention.

## Low:

### L1: `types/base.py:896` carries the rotted `feedback.md § High "Direct relay.Node inheritance bypasses Relay finalization"` citation

`base.py:895-897` inline comment cites `feedback.md` for the "Direct relay.Node inheritance bypasses Relay finalization" H1 closure rationale:

```django_strawberry_framework/types/base.py:894:897
    # build would blow up with ``NodeIDAnnotationError`` (review feedback
    # ``feedback.md`` § High "Direct relay.Node inheritance bypasses Relay
    # finalization" and § "Extended Node interfaces").
```

Same drift class as the four `feedback.md § High` citations already swept out of `types/relay.py` in the `rev-types__relay.md::L2` fix pass (and the eight-site sweep flagged in `rev-types__finalizer.md` carry-forward). `docs/feedback.md` is now `# Review feedback - docs/spec-028-orders-0_0_8.md` — orders-card content, not relay-card. The reasoning the comment captures is correct against spec-015's Relay-Node H1 fix; only the pointer rotted. Recommended fix: replace `feedback.md § High "Direct relay.Node inheritance bypasses Relay finalization"` with a `spec-015-relay_interfaces-0_0_5.md #"Direct ``relay.Node`` inheritance"` substring anchor OR drop the cross-reference entirely (the surrounding prose at `:888-905` already documents the contract independently of the citation). Folder pass owns the bundle.

### L2: `types/base.py:936` `spec-014 H1` citation survives as a rev-anchor but inherits the optimizer-folder `spec-014 → spec-018` drift class

```django_strawberry_framework/types/base.py:935:936
            # whichever type was already registered at ``__init_subclass__``
            # time, which mis-bound when a secondary was registered before
            # the primary (the import-order trap closed by spec-014 H1).
```

Same rev-anchor calibration recorded in `rev-types__relations.md::Low #2` for the matching citation at `relations.py:4-5`: the H1 anchor is rev-relative not path-relative, so the citation survives `docs/SPECS/NEXT.md` Step 8 archive sweeps. Drift risk is still non-zero — the optimizer folder swept two `spec-014 → spec-018` rotations (`rev-optimizer__extension.md`, `rev-optimizer__walker.md`) because the cited prose actually lived in `spec-018-meta_primary-0_0_6.md`. For this site, the cited reasoning ("import-order trap") legitimately matches `spec-014` (the registry-side identity contract per `rev-types__relations.md` calibration). Defer until a regression in the spec mapping fires OR until the project-pass spec-NN sweep verifies all `types/`-side `spec-014 H1` cites against the actual spec contents.

### L3: `convert_relation` historical name drift in `docs/TREE.md:214` and `:264` (forwarded to project pass per per-file carry-forward)

Per `rev-types__converters.md::What looks solid > GLOSSARY drift quick-check`, `docs/TREE.md:214` and `:264` still cite the historical `convert_relation` name in the per-file comment column, while the source symbol is `resolved_relation_annotation` per `spec-018-meta_primary-0_0_6.md:139`'s explicit rename note. Forwarded to project pass (`worker-1.md` "must not ... update CHANGELOG.md" applies equally to TREE.md drift). Restated at folder scope so the project pass picks it up alongside the bundled `convert_relation` grep sweep `grep -n 'convert_relation' docs/TREE.md docs/GLOSSARY.md README.md docs/README.md docs/SPECS/*.md` recommended by the per-file carry-forward.

### L4: Folder-scope `path:symbol_name` vs canonical `path::QualifiedName` grep-sweep confirmation

Post `rev-types__relations.md::L1` fix (4 sites swept in `types/relations.py`), no remaining `path:symbol_name` (single-colon) cross-file citations exist under `types/`. Verified via `grep -n "\.py:[a-z_]" django_strawberry_framework/types/*.py` — zero matches. The canonical `path::QualifiedName` shape from `AGENTS.md` rule 27 is uniformly applied across the folder. Recorded as a no-edit positive-audit-trail Low so the project pass and the next DRY cycle can both confirm the sweep without re-running the grep.

### L5: GLOSSARY drift positive-audit-trail confirmation — folder-scope (no edit)

The seven per-file artifacts plus `__init__.py` collectively triggered GLOSSARY edits at `DjangoType` (in-cycle, `rev-types__base.md::M1`), `get_queryset` (bundled with the prior in-cycle), `SyncMisuseError` + `Relay Node integration` (in-cycle, `rev-types__relay.md::M1`), and `Strictness mode` (in-cycle, `rev-types__resolvers.md::M1`). The four entries that surface this folder's behaviour to consumers are now aligned with the shipped contract. Internal-mechanics symbols (`PendingRelation`, `PendingRelationAnnotation`, `_PendingRelationAnnotationMeta`, `DjangoTypeDefinition`, `related_target_for`, `graphql_type_name`, `_related_target_cache`, `apply_interfaces`, `install_relay_node_resolvers`, `_check_composite_pk_for_relay_node`, `install_is_type_of`, `implements_relay_node`, every `_resolve_*_default` / `_apply_*` / `_coerce_*` helper, `_RELAY_RESOLVER_DEFAULTS`, `_field_meta_for_resolver`, `_make_relation_resolver`) are correctly absent per the `optimizer/__init__.py:14-17` "internal implementation details" convention. The deferred `finalize_django_types` Phase 2.5 enumeration is recorded in M1 above and forwarded to project pass.

### L6: Folder `__init__.py` re-export surface aligned with `__all__`

`types/__init__.py:25-29` re-exports `DjangoType`, `SyncMisuseError`, and `finalize_django_types` with the matching `__all__` tuple at `:29`. All three are also exposed at the top-level package (`django_strawberry_framework.__init__.py::__all__`). Per the module docstring at `:1-23`, the folder layout is an internal implementation detail; the three re-exports are the consumer-facing surface. Shadow overview confirms 0 control-flow hotspots / 0 ORM markers / 0 calls of interest / 0 repeated literals / 0 TODO comments. No-edit positive-audit-trail Low so the next reviewer doesn't propose collapsing the re-exports or adding new ones speculatively (`START.md` "preemptively populate" anti-pattern).

### L7: Import direction is strict-DAG with one documented cycle-break

`types/` imports `..optimizer` (FieldMeta + hints + plans + logger + `_context`), `..exceptions` (typed errors), `..registry` (registry singleton + identity contract), `..utils` (strings + relations), and `..scalars` (BigInt) — all leaf-direction. Within `types/`: `base.py` imports `.converters`, `.definition`, `.relations`, `.relay`; `finalizer.py` imports `.converters`, `.relations`, `.relay`, `.resolvers`. The single documented cycle-break is `types/base.py::_validate_filterset_class:99`'s function-local `from ..filters.sets import FilterSet` (the `types → filters → types` cycle dodged via deferred import; documented at `base.py:86-94` and pinned by the `_validate_filterset_class` docstring's "Do NOT hoist to module top" tripwire). No other circular-import risk surface; verified via `grep -rn "^from .[a-z]\|^from ..[a-z]" django_strawberry_framework/types/*.py`. No-edit positive-audit-trail Low.

## What looks solid

### DRY recap

- **Existing patterns reused.** Single-source-of-truth helpers consolidate every cross-file contract in the folder: `graphql_type_name` property at `definition.py:108-119` (read by `filters/base.py:199`, `filters/base.py:204`, `filters/inputs.py:582`, `types/finalizer.py:282/333/339/366/416` — eight consumers, zero inline copies); `_format_unknown_fields_error` at `base.py:460-474` (single home for "unknown fields … Available: …" error shape across `Meta.fields` / `Meta.exclude` / `Meta.optimizer_hints`); `_interfaces_shape_error` + `_INTERFACES_SHAPE_ERROR_LEAD_IN` at `base.py:477-490` (two shape-rejection sites); `_is_relay_shaped(cls, interfaces)` at `base.py:179-190` (consumed at `:247` H1 collision guard and `:892` pk-annotation suppression); `_meta_optimizer_hints` at `base.py:442-457` (shape gate consumed by `_validate_meta:663`); `_format_*` formatter sibling-group at `finalizer.py:71-629` (nine canonical error formatters at module top so consumer error matching stays grep-stable across filter + order sidecars); `_model_for` at `relay.py:305-314` (four-site consolidation of `cls.__django_strawberry_definition__.model` reads); `_initial_queryset` at `relay.py:317-324` (single home for `model._default_manager.all()`); `_RELAY_RESOLVER_DEFAULTS` at `relay.py:493-498` (single source of truth for the four Relay resolver method names + framework defaults); `_apply_node_filter` at `relay.py:284-302` (color-agnostic, both sync and async consume it); `scalar_for_field` at `converters.py:119-139` (shared with `filters/inputs._scalar_from_model_field` so a column resolves to the same scalar on both sides of the converter / filter-input split); `resolved_relation_annotation` at `converters.py:329-341` (thin three-line `FieldMeta`-driven dispatch shared with the finalizer's deferred-resolution path); `_ValidatedMeta` NamedTuple at `base.py:571-590` (snapshot dataclass that prevents `__init_subclass__` from re-reading `getattr(meta, ...)` twice); five canonical error-message helpers `_format_*` consolidate the consumer-visible error surface at finalize time.
- **New helpers considered.** Two candidates evaluated and deferred at folder scope: (a) `_target_definition_for_model(model)` collapsing `definition.py::related_target_for #"target_type = registry.primary_for"` and `filters/sets.py::_owner_resolve_target` — deferred under the explicit "third caller" trigger; (b) shared defensive-Protocol typing or helper around the four-site `getattr(field, "is_relation"/"related_model", default)` pattern — deferred under the explicit "fifth site or Protocol grows the attribute" trigger. One candidate accepted as the act-now bullet: `FieldMeta._from_field_shape(field, *, is_relation)` cross-folder extraction.
- **Duplication risk in the current folder.** Three intentional sibling duplications kept verbatim per the load-bearing-distinction calibration: (1) `_bind_filterset_owner` / `_bind_orderset_owner` related-target-agreement walk at `finalizer.py:271-377` / `:480-551` — correct per `rev-types__finalizer.md` DRY analysis (third-sidecar trigger); (2) `_bind_filtersets` / `_bind_ordersets` four-subpass mirror at `finalizer.py:741-860` / `:632-738` — correct per the same calibration plus the documented `related.orderset` Layer-2 force-resolution asymmetry; (3) the four-set `consumer_authored_fields` union at `base.py:223-246` — correct per the two-source split (`cls.__dict__` for assignments vs `cls.__annotations__` for type hints). All three are recorded under per-file DRY recaps; folder pass does NOT re-file them per `worker-1.md` folder-pass DRY-recap convention.
- **Cross-file repeated-literal check.** Cross-file string-literal duplications (`"target_field"`, `"related_model"`, `"is_relation"`, `"name"`) are all consumed via `getattr(field, ATTR, default)` defensive-Protocol shape against Django's heterogeneous `_meta` return; the attribute names are Django ORM API surface, not consolidation candidates. Already subsumed by the act-now `FieldMeta._from_field_shape` extraction (the resolver-side fallback shares the exact attribute list with the canonical builder). No additional folder-level duplication finding warranted.

### Other positives

- **Module-responsibility boundaries are clean.** `base.py` owns the `DjangoType.__init_subclass__` pipeline and the eight `_validate_*` / `_normalize_*` / `_select_*` / `_build_*` helpers; `converters.py` owns scalar / choice-enum / relation-annotation conversion; `definition.py` owns the `DjangoTypeDefinition` dataclass + `related_target_for` + `graphql_type_name`; `finalizer.py` owns the once-only build gate (Phase 1 audit + Phase 2 resolution + Phase 2.5 sidecar binding + Phase 3 decoration); `relations.py` owns the pending-relation scaffolding (`PendingRelation` + `PendingRelationAnnotation`); `relay.py` owns the Relay-Node lifecycle (class-creation / annotation-synthesis / Phase 2.5 finalization split); `resolvers.py` owns the cardinality-aware relation-resolver factory + FK-id elision + strictness-N+1 surfacing. Each module's responsibility is named in its module docstring and the test trees (`tests/types/test_{base,converters,definition_*,definition_relations,relay_interfaces,relations,resolvers}.py`) split along the same axes.
- **Folder-scope test discipline.** Every documented behaviour is pinned by focused tests in the three trees per `AGENTS.md`: package-internal `tests/types/test_*.py` for invariants (identity contracts, validation rejection messages, sentinel ordering); example-app `examples/fakeshop/apps/*/tests/` for in-process schema behaviour (admin, services, management commands); example-app `examples/fakeshop/test_query/` for live `/graphql` HTTP query coverage. Worker memory's prior cycles enumerate 5+5+9+24+23+19+5+... dedicated tests per per-file artifact; the folder pass confirms the breadth.
- **Cycle-safe import discipline.** Two documented cycle breaks: `base.py:99` defers `from ..filters.sets import FilterSet` to function scope (cycle: `types → filters → types`); `definition.py:148-150` defers `from ..registry import registry, FieldDoesNotExist` to function scope (cycle: `definition → registry → definition`). Both are documented at-source with "Do NOT hoist to module top" tripwires AND the cycle path is named. `relay.py:27` and `relations.py:18` use `from __future__ import annotations` to demote annotation-only imports under `TYPE_CHECKING` per `AGENTS.md` rule 12. No other circular-import surface.
- **Test-double surfaces are documented as test-only.** `_make_relation_resolver(parent_type: type | None = None)` and `_field_meta_for_resolver(field, parent_type: type | None = None)` both accept the `None` default with the docstring contract "production calls always supply `parent_type=cls`". Per the `rev-types__resolvers.md::Low #2` fix pass, both docstrings now name the test-double-only nature of the `None` default and the silent-misuse failure mode at the production path. Same calibration applied uniformly across the folder.
- **Sentinel-before-early-return ordering at `types/base.py:201-208`.** The `_is_default_get_queryset` flip runs BEFORE the `meta is None` early-return so the abstract-shared-base pattern (an abstract base overriding `get_queryset` without declaring `Meta`) is correctly detected on concrete subclasses. Pinned by `tests/types/test_base.py::test_has_custom_get_queryset_inherits_through_abstract_base_without_meta:705-738` with bidirectional source ↔ test audit-trail comments.
- **Failure-atomic Phase 1 in `finalizer.py`.** `_audit_primary_ambiguity` raises before the `for pending in registry.iter_pending_relations()` walk starts at `:190`; the unresolved-target accumulator completes its sort before the resolved-annotation mutation loop runs at `:217-225`. Class-intact-on-raise contract pinned by `tests/types/test_definition_order.py::test_unresolved_target_raises_with_source_field_and_target:205` and `::test_finalize_ambiguity_error_fires_before_unresolved_target_error:910`.
- **Two-phase Relay lifecycle is well-documented and well-tested.** `relay.py:1-21` module docstring names exactly three lifecycle phases (class-creation, annotation-synthesis, Phase 2.5 finalization); the three discriminators (`cls.__dict__` membership / `relay.Node in interfaces` tuple-membership / `__func__` identity) answer different questions at different phases. Pinned by `tests/types/test_relay_interfaces.py`'s 1453-line suite covering every documented contract.
- **GLOSSARY drift quick-check at folder scope.** Of the seven per-file artifacts, four shipped in-cycle GLOSSARY edits at the four public-surface entries (`DjangoType`, `get_queryset`, `SyncMisuseError`+`Relay Node integration`, `Strictness mode`). The remaining internal-mechanics absences are correct convention per the cross-cycle calibration recorded across the optimizer + types subpackage cycles. The one remaining drift item (`finalize_django_types` Phase 2.5 enumeration) is correctly deferred to the per-`Meta.*sidecar*_class` entries pending the spec-028 joint-cut `shipped (0.0.8)` flip per spec-027 Decision 10's pattern.

### Summary

The seven-file `types/` subpackage is the package's primary type-system home (3,289 source lines under review: `base.py` 952, `converters.py` 342, `definition.py` 191, `finalizer.py` 860, `relations.py` 82, `relay.py` 528, `resolvers.py` 296, plus `__init__.py` 29). Every per-file artifact closed at `Status: verified` before this pass: zero High findings across the folder, six Mediums all landed in-cycle (two GLOSSARY drifts + one diagnostic-message clarification + one typed-marker GLOSSARY entry + one `RuntimeError → OptimizerError` GLOSSARY correction + Phase 2.5 GLOSSARY deferral), thirty-eight Lows split across citation hygiene (spec-NN drift sweeps already swept under `rev-types__relay.md::L1` + `rev-types__finalizer.md` + `rev-types__relations.md::L1`), forward-looking deferrals with explicit grep-able triggers, and positive-audit-trail confirmations. Folder pass surfaces one act-now cross-folder DRY opportunity (`FieldMeta._from_field_shape` extraction at `optimizer/field_meta.py` consumed by both the canonical `FieldMeta.from_django_field` builder and `types/resolvers.py::_field_meta_for_resolver`'s test-double fallback — the second-closing folder owns the landing per `rev-optimizer.md` calibration), two folder-scope defer-with-explicit-trigger DRY items, two new comment-pass Lows (the `base.py:896` rotted `feedback.md` cite + the `base.py:936` `spec-014 H1` rev-anchor confirmation), one TREE.md drift forward to project pass (`convert_relation` historical name), and three positive-audit-trail Lows (folder-scope `path::QualifiedName` sweep confirmation; folder `__init__.py` re-export surface aligned with `__all__`; strict-DAG import direction with one documented cycle-break). Cross-file repeated-literal check returns zero genuine duplications outside the act-now `_from_field_shape` extraction; cross-file naming/error-handling conventions are uniform across siblings (every `ConfigurationError` raise is typed-and-prefixed with the model name; every test-double surface names its test-only nature in the docstring; every cycle-break import carries a "Do NOT hoist to module top" tripwire). Standard three-spawn cycle (shape #4 collapse plausible at Worker 2 because the act-now DRY extraction is the only behaviour-touching item and the rest are comment-pass / forwards). `Status: under-review`.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/optimizer/field_meta.py` — added new classmethod `FieldMeta._from_field_shape(field, *, is_relation: bool) -> FieldMeta` carrying the 11-line cardinality-gated nullable rule + 12-keyword constructor body. Refactored `FieldMeta.from_django_field` to guard-and-delegate: keeps the `OptimizerError` typed-input-guard at the entry, then returns `cls._from_field_shape(field, is_relation=bool(field.is_relation))`. Added `Any` to the `typing` import for the helper's `field: Any` signature (test doubles like `SimpleNamespace` do not satisfy `_DjangoFieldLike`'s `is_relation` field; the helper accepts the broader shape because the canonical-builder path has already enforced the structural guard before delegating, and the resolver-side fallback fires precisely when the descriptor lacks `is_relation`).
- `django_strawberry_framework/types/resolvers.py` — collapsed `_field_meta_for_resolver`'s test-double fallback (formerly 30 lines reproducing the cardinality-gated nullable rule + 12-keyword constructor) to a single `FieldMeta._from_field_shape(field, is_relation=True)` delegation plus a 7-line comment naming the test-double scope and the `is_relation=True` rationale. Dropped the now-unused `relation_kind` import from `..utils.relations` (only the deleted fallback body used it; `is_many_side_relation_kind` is still imported and used at `_check_n1`).

### Tests added or updated

- None. Per artifact: "Regression coverage: existing tests `tests/optimizer/test_field_meta.py` (canonical builder) plus `tests/types/test_resolvers.py:48-86`, `:446-481` (test-double fallback) pin both branches; no new test surface needed because the extraction preserves identical observable behaviour." Verified by reading both test files:
  - `tests/optimizer/test_field_meta.py::test_from_django_field_*` (scalar / nullable-scalar / forward-FK / reverse-FK / reverse-M2M / forward-M2M / forward-O2O / reverse-O2O / rejects-non-django / rejects-partial-shape) pins the canonical-builder branch with `is_relation` read from `bool(field.is_relation)`.
  - `tests/types/test_resolvers.py::test_o1_make_relation_resolver_many_side` (lines 48-65) and `::test_o1_make_relation_resolver_forward_returns_attribute` (lines 67-86) drive `_make_relation_resolver(SimpleNamespace(...))` without `is_relation` on the fake field, exercising the test-double fallback branch with `is_relation=True`.
  - `tests/types/test_resolvers.py::test_o1_make_relation_resolver_reverse_one_to_one_returns_none_on_doesnotexist` (lines 446-481) drives the same fallback branch for a synthetic reverse-OneToOne shape.

### Validation run

- `uv run ruff format .` — pass (213 files unchanged)
- `uv run ruff check --fix .` — pass (All checks passed)
- Focused tests not executed per worker-2.md hard rules ("Never run pytest"). Semantic preservation verified by inspection: both delegating call sites construct identical `FieldMeta(...)` keyword arguments to the pre-extraction versions; `is_relation` is the only branch axis and is forwarded explicitly by each caller (`bool(field.is_relation)` from `from_django_field`; literal `True` from the resolver-side fallback). The nullable rule, target_field handling, and remaining 10 getattr-defaulted reads move verbatim.

### Notes for Worker 3

- Shadow file not used during the fix; both call sites are small enough to edit against `Read` output directly.
- Circular-import risk verified absent: `optimizer/field_meta.py` imports `..exceptions` + `..utils.relations` only (no `..types` import); the helper is a classmethod so the existing `from ..optimizer.field_meta import FieldMeta` line in `types/resolvers.py` already routes calls to it.
- `_from_field_shape` is named with a leading underscore so consumers continue to use `from_django_field` as the public entry point. The helper is documented as internal to the shared shape between the canonical builder and the resolver-side test-double fallback.
- `Any` was added to the `typing` import in `optimizer/field_meta.py` for the helper's `field: Any` annotation. The canonical `from_django_field` entry still types its `field` parameter as `_DjangoFieldLike` (Protocol enforces the `name`/`is_relation` attribute contract via the explicit `hasattr` guard); the helper deliberately widens to `Any` so the resolver-side fallback (which fires precisely when `is_relation` is missing from the structural shape) typechecks cleanly.
- The `_field_meta_for_resolver` docstring still describes the test-double fallback contract correctly post-delegation (its description of what the fallback advertises is the same shape the canonical builder would produce). The comment pass owns any docstring-polish there.
- Comment-pass Lows L1 (`base.py:896` rotted `feedback.md` cite), L2 (`base.py:936` `spec-014 H1` rev-anchor confirmation), forwards M1 + L3, and positive-audit-trail Lows L4-L7 remain for the comment pass.
- `uv.lock` not touched (no dependency change; `uv run` invocations were the existing format/check pair).
- Dirty paths shown in `git status` (KANBAN, `types/base.py`, `types/finalizer.py`, `types/relations.py`, `types/relay.py`, builder docs, kanban-app, test files, GLOSSARY) are concurrent maintainer work per AGENTS.md #33 — left untouched.

---

## Verification (Worker 3)

### Logic verification outcome

Act-now DRY extraction landed cleanly across both call sites — verification confirms bit-for-bit semantic preservation:

- `FieldMeta._from_field_shape` exists at `optimizer/field_meta.py::FieldMeta._from_field_shape` (lines 141-189) as a `@classmethod` with the keyword-only `is_relation: bool` parameter. The shared body carries the cardinality-gated nullable rule verbatim (`is_m2m or is_o2m → False`; otherwise `relation_kind(field) == "reverse_one_to_one" or bool(getattr(field, "null", False))`) and the 12-keyword `FieldMeta(...)` constructor call (`name`, `is_relation`, `many_to_many`, `one_to_many`, `one_to_one`, `nullable`, `related_model`, `attname`, `target_field_name`, `target_field_attname`, `reverse_connector_attname`, `auto_created`).
- `FieldMeta.from_django_field` (`field_meta.py:117-139`) preserves the `OptimizerError` typed-input-guard verbatim at the entry (`not hasattr(field, "name") or not hasattr(field, "is_relation")`) and now delegates via `return cls._from_field_shape(field, is_relation=bool(field.is_relation))`. The `OptimizerError` message and the two grep-anchor attribute names ("name" and "is_relation") are intact.
- `_field_meta_for_resolver` (`resolvers.py:174-198`) preserves the registry-first lookup (`parent_type → definition → field_map`), the registered-meta short-circuit, the `not hasattr(field, "is_relation")` test-double-fallback gate, and the canonical-builder fall-through. The fallback body collapses from 30 lines to one delegation: `FieldMeta._from_field_shape(field, is_relation=True)`. The `is_relation=True` hard-code matches the artifact's DRY-recap rationale ("the resolver-side fallback fires only when the field has no `is_relation` attribute and the caller is by definition asking about a relation field").
- `Any` import added to `optimizer/field_meta.py` for the helper's `field: Any` signature (correct widening — the helper's two callers each enforce their own structural guard before delegation). `relation_kind` import dropped from `resolvers.py` (only consumed by the deleted fallback body); `is_many_side_relation_kind` still imported and consumed at `_check_n1` per artifact-named scope.
- Focused tests pass:
  - `uv run pytest tests/optimizer/test_field_meta.py -x` → 16 passed (canonical-builder branch pinned across scalar / nullable-scalar / forward-FK / reverse-FK / reverse-M2M / forward-M2M / forward-O2O / reverse-O2O / rejects-non-django / rejects-partial-shape cases).
  - `uv run pytest tests/types/test_resolvers.py -x` → 26 passed. The two test-double fallback shapes named in the artifact (`test_o1_make_relation_resolver_many_side` at `test_resolvers.py:48-65`, `test_o1_make_relation_resolver_forward_returns_attribute` at `:67-86`, plus `test_o1_make_relation_resolver_reverse_one_to_one_returns_none_on_doesnotexist` at `:446-481`) all drive the delegated `_from_field_shape(field, is_relation=True)` path and pass.
- `uv run ruff format --check` + `uv run ruff check` on both touched files: clean.
- No semantic change. The delegated body is byte-identical to both pre-extraction bodies modulo the `is_relation` source (read vs literal `True`); every other axis (cardinality flags, target_field reads, related_model / attname / reverse_connector_attname / auto_created defaults) ports verbatim.

### DRY findings disposition

- Act-now `FieldMeta._from_field_shape` extraction: landed in-cycle per this verification block.
- Defer-with-trigger `_target_definition_for_model(model)` shared helper: deferred per the artifact's verbatim "third caller of the `primary_for + get + get_definition` funnel lands" trigger. No edit required.
- Defer-with-trigger cross-file `getattr(field, "is_relation"/"related_model", default)` defensive-Protocol pattern: deferred per the artifact's verbatim "fifth site adds the same `getattr` defensive pair OR `_DjangoFieldLike` Protocol grows a `target_field` attribute" trigger. No edit required — and partially subsumed by the act-now extraction since the resolver-side fallback now shares the exact attribute-list with the canonical builder.

### Temp test verification

- No temp test files created. The focused-test runs above cover both branches the extraction touches.

### Verification outcome

logic accepted; awaiting comment pass

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/types/base.py:887-895` — dropped the rotted `feedback.md § High "Direct relay.Node inheritance bypasses Relay finalization" and § "Extended Node interfaces"` parenthetical cross-reference from the `suppress_pk_annotation` comment block per artifact L1 recommendation (b). The surrounding prose at `:887-895` already documents the contract independently (the `id: int` + `id: GlobalID!` collision → `NodeIDAnnotationError` rationale is named in full one line above the deleted citation). Same drop pattern previously applied at `types/finalizer.py::finalize_django_types` and the four sites in `types/relay.py` per worker-2 memory `rev-types__finalizer.md` and `rev-types__relay.md::L2`.

### Per-finding dispositions

- L1: applied — dropped the rotted `feedback.md § High "Direct relay.Node inheritance bypasses Relay finalization"` cross-reference at `base.py:887-895` entirely per artifact recommendation (b). Verified rotted: `docs/feedback.md` is now `# Review feedback - docs/spec-028-orders-0_0_8.md` (orders-card content, no "Direct relay.Node" string). Surrounding prose self-names the `NodeIDAnnotationError` contract.
- L2: no edit — rev-anchor confirmed at `base.py:936`. The `spec-014 H1` citation legitimately matches the registry-side identity contract per the artifact's calibration (and per `rev-types__relations.md::Low #2`). `grep -in "import-order\|H1" docs/SPECS/spec-014-testing_shift-0_0_4.md` returns zero matches, so the citation is rev-anchor not path-anchor; the cited reasoning ("import-order trap closed by spec-014 H1") is preserved at the H1 anchor across `docs/SPECS/NEXT.md` Step 8 archive sweeps. Defer-with-trigger per artifact prose ("Defer until a regression in the spec mapping fires OR until the project-pass spec-NN sweep verifies all `types/`-side `spec-014 H1` cites against the actual spec contents").
- L3 (`docs/TREE.md:214` + `:264` `convert_relation` historical name): forwarded to project pass per artifact prose ("Forwarded to project pass... Restated at folder scope so the project pass picks it up alongside the bundled `convert_relation` grep sweep").
- L4 (folder-scope `path:symbol_name` vs `path::QualifiedName` grep-sweep): positive-audit-trail; no edit.
- L5 (folder-scope GLOSSARY drift positive-audit-trail): no edit.
- L6 (folder `__init__.py` re-export surface aligned with `__all__`): positive-audit-trail; no edit.
- L7 (strict-DAG import direction with one documented cycle-break): positive-audit-trail; no edit.
- M1 (consolidated forward GLOSSARY drift on `finalize_django_types` Phase 2.5 enumeration + internal-mechanics absences): forwarded to project pass per artifact prose ("Restated at folder scope so the project pass author lands (a) and confirms (b) in one sweep alongside the filter-subsystem joint-cut forwards from `rev-filters.md`").
- Docstring tightening on the new `FieldMeta._from_field_shape` helper and refactored callers (`from_django_field`, `_field_meta_for_resolver`): no additional edit beyond what the logic pass already shipped. `_from_field_shape`'s docstring (lines 143-163 of `optimizer/field_meta.py`) already names both call sites (`from_django_field` reads `bool(field.is_relation)`; resolver-side fallback hard-codes `True` because the field lacks `is_relation`), the cardinality-gated nullable rule, and the nine `getattr`-defaulted reads — sufficient for the next reader to follow the delegation without cross-file jumping. `from_django_field`'s docstring (lines 119-133) describes the typed-input guard and the load-bearing attribute pair without coupling the consumer-facing entry to the internal helper name. `_field_meta_for_resolver`'s inline comment (lines 189-196 of `types/resolvers.py`) explicitly names the delegation, the `is_relation=True` rationale, and that the observable `FieldMeta` matches the canonical builder.

### Validation run

- `uv run ruff format .` — pass (213 files unchanged; the deleted lines stayed within column 100)
- `uv run ruff check --fix .` — pass (All checks passed)

### Notes for Worker 3

- One-site, three-line drop at `base.py:887-895`; matches the precedent drops at `types/finalizer.py` (worker-2 memory `types/finalizer.py` entry, Low #3) and `types/relay.py` (worker-2 memory `types/relay.py` entry, L2 5-site sweep). Surrounding prose at `:887-895` carries the `NodeIDAnnotationError` rationale standalone — verified by reading the comment without the cited line.
- L2 deliberately left untouched per artifact's defer-with-trigger calibration; no docstring/comment edit at `base.py:936`. Same forwarding stance as `types/relations.py:4-5` recorded in worker-2 memory `types/relations.py` entry (Low #2).
- Forwards M1 + L3 remain queued for project pass; positive-audit-trail Lows L4-L7 require no comment-pass action.
- `uv.lock` not touched.
- No concurrent-maintainer dirty paths overlap with the comment-pass edit at `base.py:887-895`.

---

## Iteration log

### Verification (Worker 3, pass 3)

#### Terminal-verify outcome

Bare `fix-implemented` terminal-verify for the `types/` folder pass. All five gates pass:

1. **`git diff -- CHANGELOG.md` empty.** Confirmed empty — consistent with the `Not warranted` disposition.
2. **Changelog disposition cites both AGENTS.md rule 21 AND active-plan silence.** Verified at `## Changelog disposition > Reason` (`AGENTS.md` rule 21 quoted verbatim "Do not update CHANGELOG.md unless explicitly instructed" AND "the active review plan's silence on changelog authorization for this cycle").
3. **`Not warranted` framing honest.** `FieldMeta._from_field_shape` is leading-underscore private (`grep -n "_from_field_shape" django_strawberry_framework/optimizer/field_meta.py` confirms `def _from_field_shape` at `:142`); `FieldMeta.from_django_field` remains the public entry point with the `OptimizerError` typed-input guard intact at `:134-139`; `_field_meta_for_resolver` is already underscore-private. Semantics preserved bit-for-bit per the logic-pass verification block — `is_relation` is the only branch axis and is forwarded explicitly by each caller (`bool(field.is_relation)` from the canonical builder; literal `True` from the resolver-side fallback). The comment-pass drop of the rotted `feedback.md` cite at `base.py:887-895` is comment-only with no behaviour change (`grep -n "feedback.md" django_strawberry_framework/types/*.py` returns zero hits).
4. **Logic + comment passes accepted.** Pass-1 set `logic accepted; awaiting comment pass`; pass-2 set `comments accepted; awaiting changelog disposition`. Both iteration-log entries preserved verbatim above.
5. **Ruff plausible.** `uv run ruff format --check` on the three touched files (`optimizer/field_meta.py`, `types/resolvers.py`, `types/base.py`) → `3 files already formatted`. `uv run ruff check` on the same → `All checks passed!`.

`Not warranted` calibration siblings cited in the disposition (`filters/factories.py`, `optimizer/walker.py`, `optimizer/field_meta.py`, `types/relations.py`) are accurate per worker-3 memory: each is an internal-only docstring/private-helper change with the same "consumer-observable behaviour unchanged" framing.

#### Verification outcome

cycle accepted; verified

### Verification (Worker 3, pass 2)

#### Comment verification outcome

- L1 (rotted `feedback.md § High` citation at `base.py:896`): applied per artifact recommendation (b). `git diff -- django_strawberry_framework/types/base.py` shows a clean 3-line drop at the `suppress_pk_annotation` comment block; the post-fix line `895` ends with the standalone `# build would blow up with ``NodeIDAnnotationError``.` sentence. Surrounding prose at `:887-895` self-documents the `id: int` + `id: GlobalID!` collision rationale without the citation — verified by reading the comment block standalone. `grep -n "feedback.md" django_strawberry_framework/types/*.py` returns zero matches across the entire folder, consistent with the precedent sweeps in `rev-types__relay.md::L2` and `rev-types__finalizer.md`.
- L2 (`spec-014 H1` rev-anchor confirmation at `base.py:934`): confirmed no-edit per artifact's defer-with-trigger calibration. Citation survives at line 934 (`# the primary (the import-order trap closed by spec-014 H1).`); cited reasoning matches the registry-side identity contract per `rev-types__relations.md::Low #2` precedent. The artifact's deferral trigger ("regression in the spec mapping fires OR project-pass spec-NN sweep verifies all `types/`-side `spec-014 H1` cites") is preserved verbatim and grep-resolvable.
- L3 (`docs/TREE.md:214` + `:264` `convert_relation` historical name): forwarded to project pass per artifact prose; no in-cycle edit warranted.
- L4 (folder-scope `path:symbol_name` vs `path::QualifiedName` grep-sweep confirmation): positive-audit-trail; no edit.
- L5 (folder-scope GLOSSARY drift positive-audit-trail): no edit.
- L6 (folder `__init__.py` re-export surface aligned with `__all__`): positive-audit-trail; no edit.
- L7 (strict-DAG import direction with one documented cycle-break): positive-audit-trail; no edit.
- M1 (consolidated forward GLOSSARY drift on `finalize_django_types` Phase 2.5 enumeration + internal-mechanics absences): forwarded to project pass per artifact prose.
- Docstrings on the logic-pass extraction (`FieldMeta._from_field_shape`, `from_django_field`, `_field_meta_for_resolver`) verified during logic pass; the comment-pass correctly identified that no additional docstring polish was required because both call-site descriptions already name the delegation, the `is_relation` source axis, and the test-double-only nature of the resolver-side fallback. The comment scope is correctly bounded to the L1 single-site drop.

#### Validation

- `uv run ruff format --check django_strawberry_framework/types/base.py` → `1 file already formatted`.
- `uv run ruff check django_strawberry_framework/types/base.py` → `All checks passed!`.
- `git diff -- django_strawberry_framework/types/base.py` shape matches Worker 2's claimed scope: one hunk dropping the 3-line `feedback.md` citation at the `suppress_pk_annotation` comment block, plus the Medium-pass `_format_unknown_fields_error` refactor at `_validate_optimizer_hints` carried over from the per-file `rev-types__base.md::M2` cycle (sibling-cycle-attributable per worker-3 memory `optimizer/ (folder pass)` and `testing/ (folder pass)` precedent).
- `git diff -- CHANGELOG.md` empty (consistent with awaiting-changelog-disposition state).

#### Verification outcome

comments accepted; awaiting changelog disposition

---

## Changelog disposition

### State

`Not warranted`.

### Reason

Per `AGENTS.md` rule 21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active review plan's silence on changelog authorization for this cycle: the dispatch prompt does not authorize a `CHANGELOG.md` edit and the cycle's landed edits are internal-only.

The act-now DRY landing extracted `FieldMeta._from_field_shape` (private leading-underscore helper) and routed both `FieldMeta.from_django_field` and `_field_meta_for_resolver`'s test-double fallback through it. Semantics preserved bit-for-bit — both call sites construct identical `FieldMeta(...)` keyword arguments to their pre-extraction bodies; `is_relation` is the only branch axis and is forwarded explicitly by each caller (`bool(field.is_relation)` from the canonical builder; literal `True` from the resolver-side fallback). No public-API surface changed — `from_django_field` remains the public entry point with its `OptimizerError` typed-input guard intact, and `_field_meta_for_resolver` is already underscore-private. The comment pass dropped a rotted `feedback.md` citation at `types/base.py:887-895` (comment-only) with no behaviour change.

Calibration siblings for `Not warranted` on internal-only DRY delegations preserving semantics bit-for-bit: `filters/factories.py` (private helper parity fix), `optimizer/walker.py` (private-helper validator hoist preserving public contract), `optimizer/field_meta.py` (RelationKind TYPE_CHECKING relocation), `types/relations.py` (citation-hygiene-only). The cross-folder reach of the extraction does not promote the disposition because the helper is private and no consumer-facing symbol or message changed.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass (213 files unchanged)
- `uv run ruff check --fix .` — pass (All checks passed)
