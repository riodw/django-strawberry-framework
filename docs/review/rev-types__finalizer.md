# Review: `django_strawberry_framework/types/finalizer.py`

Status: verified

## DRY analysis

- **Defer with trigger.** Collapse the filter-side `_bind_filterset_owner` (`types/finalizer.py:271-377`) and order-side `_bind_orderset_owner` (`types/finalizer.py:480-551`) related-target-agreement walk into a shared `_check_related_targets_agree(field_name_iterable, previous, new, on_mismatch)` helper IFF a third sidecar-binding subsystem lands (e.g., aggregates or search). Today the two sites differ only in (a) which getattr probes the helper-tracked map (`related_filters` vs `related_orders`) and (b) which mismatch formatter to call (`_format_owner_mismatch_error` vs `_format_owner_ordersets_mismatch_error`). Both walks are otherwise identical: `prev_target = previous.related_target_for(field_name)` / `new_target = definition.related_target_for(field_name)` / both-None continue / one-None raise / `prev_definition is not new_definition or graphql_type_name diverges` raise. Trigger fires when the third sidecar lands; until then, the two-call-site footprint is below the "load-bearing distinction" threshold per the `rev-filters__sets.md::apply_sync` / `apply_async` calibration.
- **Defer with trigger.** Collapse the filter-side `_bind_filtersets` (`types/finalizer.py:741-860`) and order-side `_bind_ordersets` (`types/finalizer.py:632-738`) four-subpass orchestration into a shared `_bind_sidecars(sidecar_kind, *, definition_attr, helper_referenced, factory_cls, materializer)` helper IFF a third sidecar-binding subsystem lands. The subpass shape is identical: subpass 1 (bind every owner via per-sidecar `_bind_*_owner`), subpass 2 (expand via `cls.get_*()` with ImportError → ConfigurationError wrap + generic Exception → ConfigurationError wrap), subpass 3 (orphan validation against `_helper_referenced_*` set sorted by qualified module path), subpass 4 (materialize via factory `.arguments` touch + ledger walk). The order side adds a `related.orderset` Layer-2 force-resolution loop in subpass 2 (`types/finalizer.py:702-703`); the filter side relies on `get_filters` driving Layer-2 internally. That divergence is the third concrete difference (alongside the two helper-referenced sets and the two factory classes) and is the load-bearing reason to defer rather than act now — collapsing today would obscure the Layer-2 force-resolution asymmetry. Same calibration as the `_bind_*_owner` deferral above.
- **Defer with trigger.** Hoist the "exact-target-equality + qualified-name divergence" inner check (`types/finalizer.py:362-377` filter side, `:536-551` order side) into a `_targets_diverge(prev_target, new_target) -> bool` predicate IFF a third call site lands (e.g., from a future RelatedAggregate binding path). The two sites are literal duplicates after the both-None / one-None preamble: `prev_definition, _ = prev_target` / `new_definition, _ = new_target` / `if prev_definition is not new_definition or prev_definition.graphql_type_name != new_definition.graphql_type_name: raise ConfigurationError(...)`. Today's two-site footprint is below the carry-forward threshold from `rev-filters__sets.md`'s mirrored-pair calibration.
- **Defer with trigger.** Extract the two `Cannot finalize Django types: <kind> <qualname> raised during expansion. <repr(exc)>` wrap blocks (`types/finalizer.py:710-716` orderset side, `:818-830` filterset side) into a shared `_wrap_expansion_failure(sidecar_cls, sidecar_kind, exc)` helper IFF a third sidecar lands. The two blocks share the exact `repr(exc)` keeps-class+args framing, the `from exc` traceback preservation, and the H-core-1 audit-trail rationale. Trigger fires when the third sidecar's subpass 2 needs the same wrap shape.

## High:

None.

## Medium:

None at file scope. See the two Low forwards below — both rotate through `rev-types.md` folder pass and `rev-django_strawberry_framework.md` project pass per the calibration recorded in `rev-filters.md` (folder-scope citation-drift escalation) and the joint-cut GLOSSARY deferral pattern from spec-027 Decision 10. Per-file citation drift at this scope stays Low; the folder pass owns the escalation call once the per-file Lows across `types/` are tallied.

## Low:

### `spec-021` citation drift across 8 sites (forward to folder pass)

Eight inline citations in this file reference `spec-021` for filterset / orderset rationale that actually lives in `docs/SPECS/spec-027-filters-0_0_8.md` (filtering subsystem) and `docs/spec-028-orders-0_0_8.md` (ordering subsystem). `spec-021` is the apps-/AppConfig-spec at `docs/SPECS/spec-021-apps-0_0_7.md` (zero filterset/orderset content; verified by `grep -c "filterset\|FilterSet\|filter_input_type" docs/SPECS/spec-021-apps-0_0_7.md` → 0). The drift is the same class the filters folder pass already escalated to Medium across 43 sites in `filters/{__init__,base,factories,inputs,sets}.py` (`rev-filters.md::M1`); this file adds 8 more sites in `types/` that the filters folder pass would have missed.

Affected sites in `types/finalizer.py`:

```
types/finalizer.py:25  reject orphan ``filter_input_type`` references) per spec-021 Decision 6
types/finalizer.py:276 pair is idempotent (supports partial-finalize recovery per spec-021
types/finalizer.py:296 type names) per spec-021 line 574.
types/finalizer.py:394 offending field, and both resolved target type names per spec-021
types/finalizer.py:404 "owners (per spec-021 H2 of rev8)."
types/finalizer.py:429 "separate FilterSet subclasses for the diverging owners (per spec-021 H2 of rev8)."
types/finalizer.py:461 orphan branch uses the spec-pinned actionable message from spec-021
types/finalizer.py:760 ``ConfigurationError`` per spec-021 line 673 with the actionable
types/finalizer.py:800 # be resolved. Re-wrap as ``ConfigurationError`` per spec-021 lines
```

Why Low at this scope: per-file Lows that file at Low severity rotate through folder-pass bundling per the `rev-filters.md` escalation precedent — the per-file scope did not justify Medium for any single citation, and the cross-folder pattern is best owned at the folder/project boundary so the maintainer fixes filters + types + any future cross-folder cites in one sed sweep.

Why this matters: the user-error messages embedded at `types/finalizer.py:404` (`"owners (per spec-021 H2 of rev8)."`) and `:429` (`"separate FilterSet subclasses for the diverging owners (per spec-021 H2 of rev8)."`) are consumer-visible in the runtime `ConfigurationError` body. A consumer who pastes the error string into a search engine and lands on the actual spec-021 (apps spec) finds zero filterset content. The fix sentence should cite spec-027 (or the working-name anchor the maintainer prefers).

Recommended fix: sed-sweep this file's `spec-021` → `spec-027` (filtering rationale) AND simultaneously sweep the 43 sites in `filters/` so the consumer-visible error messages and source-comment rationale share one citation. Forward to `rev-types.md` folder pass for bundled handling alongside the carry-forward this artifact records for the types folder.

### `spec-014` citation drift at `_format_ambiguity_error` docstring (`types/finalizer.py:102-103`)

The docstring on `_format_ambiguity_error` cites `spec-014` for the test pins, but the cited substrings actually live in `spec-018-meta_primary-0_0_6.md` (verified: `docs/SPECS/spec-018-meta_primary-0_0_6.md:127` contains `"with the fix sentence"` and `:133` contains `"test_finalize_ambiguity_error_message_contains_actionable_fix"`; `spec-014-testing_shift-0_0_4.md` contains zero matches for either substring). spec-014 is `testing_shift-0_0_4` (testing migration); the ambiguity-audit contract lives in spec-018 (`Meta.primary` design). Same single-digit drift class as the `spec-014 → spec-018` confusion already filed at `rev-optimizer__extension.md` and twice at `rev-optimizer__walker.md`:

```
types/finalizer.py:102-103
    audit's tests pin against (spec-014 #"with the fix sentence",
    spec-014 #"test_finalize_ambiguity_error_message_contains_actionable_fix").
```

Recommended fix: `spec-014` → `spec-018` at both sites. Same path-substring shape (`spec-018 #"..."`) since the anchors are still substring-resolvable in the actual spec.

### Rotted `feedback.md` citation at `types/finalizer.py:251`

The comment block at `:246-252` cites `feedback.md § High "Direct relay.Node inheritance bypasses Relay finalization"`:

```
types/finalizer.py:250-252
# directly without ``Meta.interfaces`` (review feedback
# ``feedback.md`` § High "Direct relay.Node inheritance bypasses Relay
# finalization").
```

Per the worker memory carry-forward (`list_field.py` Low #4), `docs/feedback.md` is now spec-028-orders content; verified by `grep -in "Direct relay.Node" docs/feedback.md` → zero matches. The reasoning the comment captures is correct against the actual spec-015 Relay-node H1 fix; only the pointer rotted. Same Low citation-hygiene severity as the `list_field.py` `docs/feedback.md` Low.

Recommended fix: replace `feedback.md § High "..."` with either (a) the actual spec-015/spec-016 anchor where the Direct-relay.Node-inheritance H1 reasoning was authored, or (b) drop the cross-reference entirely if the surrounding docstring prose at `:246-249` already names the contract clearly enough on its own — it does. Acceptable per `AGENTS.md` rule 27.

### Rotted line-number citations across 4 sites (forward-looking)

Four inline comments cite spec-NN line numbers that will drift if the spec body shifts (same rot class as the `CHANGELOG-NN` drift in `rev-management__commands__export_schema.md`):

```
types/finalizer.py:277  Decision 6 lines 683-685
types/finalizer.py:296  per spec-021 line 574
types/finalizer.py:760  per spec-021 line 673
types/finalizer.py:800  per spec-021 lines 416 + 1030
```

Today `spec-027.md:574` and `:673` still resolve to the cited content (verified via `awk` on the spec); `:416` and `:1030` resolve to unrelated content. The four sites are rotted-on-spec-edit. Defer until either (a) the spec-021 → spec-027 sweep lands (folds these into one pass), or (b) a fifth line-number citation accumulates. Acceptable replacement per `AGENTS.md` rule 27: `spec-027-filters-0_0_8.md::Decision 6 #"unique substring"` substring anchors that survive line edits.

### `_audit_primary_ambiguity` `O(N)` sort on a typically-small list (defer-with-trigger)

`_audit_primary_ambiguity` sorts the offender list (`types/finalizer.py:141`) keyed on `entry[0].__name__`. For typical builds with one or two ambiguous models the sort is trivially cheap; for a maliciously-sized offender list (>1k ambiguous models) the sort is unnecessary if the caller wants the registration-order shape. Today's behavior (deterministic name-sort) is what the docstring promises and what `test_finalize_ambiguity_error_message_contains_actionable_fix` pins. Defer until a second offenders-list consumer surfaces and asks for registration-order shape — surface tightening, not correctness.

### `_bind_orderset_owner` Meta-defensive getattr vs filter-side `._meta.model` asymmetry (defer-with-trigger)

The order side resolves the orderset's model via `getattr(getattr(orderset_cls, "Meta", None), "model", None)` (`types/finalizer.py:505`, mirrored at `:595`) — a two-level defensive walk that returns `None` for a missing `Meta` or a missing `model` attribute. The filter side resolves the equivalent via `filterset_cls._meta.model` (`types/finalizer.py:319`, mirrored at `:447`) — a direct attribute access that assumes `_meta` is always populated. The asymmetry is intentional load-bearing per the worker memory carry-forward calibration: the filterset is a `django_filters.filterset.BaseFilterSet` subclass which always carries `_meta` (django-filter populates it via `BaseFilterSet.__init_subclass__`); the orderset is the package's own `OrderSet` whose `Meta` attribute surface is consumer-supplied. Both are correct shapes today.

Defer collapsing into a shared `_sidecar_model_for(sidecar_cls, sidecar_kind)` helper until either (a) `OrderSet` grows a `_meta` analogue (then the two paths share a stable attribute), or (b) a third sidecar lands with yet another model-attribute convention. Until then, the documented asymmetry is the right shape — same calibration as `rev-filters__sets.md`'s "load-bearing distinction, don't fold through a shared dispatcher" framing.

### `_owner_definition` model-mismatch check skips when `definition.model` is `None` (defer-with-trigger)

`_bind_filterset_owner`'s first-bind branch at `types/finalizer.py:320-324` short-circuits when `definition.model is None` (the `not issubclass(definition.model, filterset_model)` arm is only reached when both models are non-None). For a concrete `DjangoType` `definition.model` is always populated per `types/base.py::__init_subclass__`, but the abstract-shared-base path (sentinel-only definition with `model = None`) could pass through. Today no caller in the wired set ships an abstract shared base as a `filterset_class` owner; the guard is correct against the documented call graph but the docstring at `:310-318` frames the check as authoritative without flagging the `None`-skip.

Defer until either (a) the abstract-shared-base path grows an `_owner_definition`-bearing surface (forces the check to widen), or (b) a regression test asserts the `None`-skip is the intended shape. Same surface-tightening severity as the `definition.py::_related_target_cache` Any-widening Low recorded earlier.

### `_bind_*_owner`'s identity-then-equality check pattern across two sites (DRY note, forward to folder pass)

Both `_bind_filterset_owner` (`types/finalizer.py:330-331`) and `_bind_orderset_owner` (`:516-517`) use the same `if previous is definition: return` idempotency short-circuit immediately after the first-bind path. The pattern is shared at exactly two sites; defer collapsing under the same trigger as the act-now DRY bullets above (third sidecar lands). Same Low severity as the citation-hygiene Lows.

### GLOSSARY drift quick-check forward to project pass

`finalize_django_types` (`docs/GLOSSARY.md:474-494`) entry is current at the 0.0.4-shipped contract level — Phase 1 / Phase 2 / Phase 3 framing, the `relax registry.clear()` recommendation, and the `finalize_django_types()` second-call no-op are all aligned with `:182-183` source behavior. The 0.0.7 cycle's Phase 2.5 additions (`_bind_filtersets()` / `_bind_ordersets()` four-subpass orchestration + the H2-rev8 multi-owner check + the H-core-3 first-bind model-compat check) are NOT documented in the GLOSSARY entry — they surface in the `Meta.filterset_class` entry at `:620-633` ("routes through `finalize_django_types` phase 2.5 — which binds the owner ..., validates owner compatibility, calls `filterset_cls.get_filters()` ..."), which IS aligned with the implementation.

Worker 1 calibration: the `finalize_django_types` GLOSSARY entry deliberately defers the Phase 2.5 enumeration to the `Meta.filterset_class` / `Meta.orderset_class` entries (joint-cut deferral pattern per spec-027 Decision 10 — `Meta.orderset_class` is `planned for 0.0.8`). When the orderset entry flips to `shipped (0.0.8)`, the `finalize_django_types` entry should grow a Phase 2.5 bullet enumerating the sidecar four-subpass shape uniformly. Forward to `rev-django_strawberry_framework.md` project pass alongside the filter-subsystem GLOSSARY forwards already enumerated by `rev-sets_mixins.md`, `rev-filters__base.md`, and `rev-filters.md` — same joint-cut deferral pattern.

No in-cycle GLOSSARY edit warranted; no shape #4 routing needed.

## What looks solid

### DRY recap

- **Existing patterns reused.** Five canonical helpers consolidate error-message authoring at the top of the module so consumer error matching stays grep-stable: `_format_unresolved_targets_error` (`types/finalizer.py:71-92`), `_format_ambiguity_error` (`:95-114`), `_format_owner_mismatch_error` (`:380-405`), `_format_owner_pk_mismatch_error` (`:408-430`), `_format_owner_model_mismatch_error` (`:433-452`), `_format_orphan_filtersets_error` (`:455-477`), `_format_owner_ordersets_mismatch_error` (`:554-577`), `_format_owner_orderset_model_mismatch_error` (`:580-605`), `_format_orphan_ordersets_error` (`:608-629`). Sibling-grouping convention preserved across the filter/order pair so a maintainer adding a third sidecar inherits the layout shape. The `_audit_primary_ambiguity` walk delegates to the canonical `registry.models_with_multiple_types()` / `registry.primary_for(...)` / `registry.types_for(...)` registry surface (per the registry's documented Slice 1 audit-helper trio at `registry.py::TypeRegistry`), no inline shape-rebuild.
- **New helpers considered.** Four candidates evaluated: (a) shared `_bind_sidecar_owner` collapsing `_bind_filterset_owner` + `_bind_orderset_owner` — deferred per the load-bearing-distinction calibration recorded in DRY analysis; (b) shared `_check_related_targets_agree` walk extraction — deferred under the same trigger; (c) shared `_wrap_expansion_failure` for the two `repr(exc)` wrap blocks — deferred under the third-sidecar trigger; (d) shared `_sidecar_model_for(cls, kind)` for the filter-side `_meta.model` vs order-side `getattr(getattr(...))` asymmetry — deferred per the worker memory calibration that the two model-attribute conventions are intentional sibling design.
- **Duplication risk in the current file.** Three intentional sibling duplications: (1) `_bind_filterset_owner` / `_bind_orderset_owner` mirror at the related-target-agreement walk (`:344-377` / `:518-551`) — correct per the load-bearing sync-vs-async-style calibration; (2) `_bind_filtersets` / `_bind_ordersets` four-subpass mirror (`:632-738` / `:741-860`) — correct per the same calibration plus the documented `related.orderset` Layer-2 force-resolution asymmetry at the order side that the filter side does NOT need; (3) the eight `_format_*` siblings at the top of the module — correct per the documented "consumer error matching stays grep-stable" docstring promise.

### Other positives

- **Failure-atomic Phase 1 is documented and pinned.** The module docstring (`types/finalizer.py:8-16`) and the `finalize_django_types` function docstring (`:147-152`) both explicitly frame Phase 1 as failure-atomic: the primary-ambiguity audit and the unresolved-target check complete before any class object is mutated. The implementation honors this — `_audit_primary_ambiguity` (`:117-142`) raises before the `for pending in registry.iter_pending_relations()` walk starts (`:190`), the unresolved-target accumulator (`:187`, raise at `:214-215`) completes its sort before the resolved-annotation mutation loop runs (`:217-225`). The class-intact-on-raise contract is pinned by `tests/types/test_definition_order.py::test_unresolved_target_raises_with_source_field_and_target` (line 205) and `tests/types/test_definition_order.py::test_finalize_ambiguity_error_fires_before_unresolved_target_error` (line 910).
- **Partial-failure recovery is documented + pinned.** The function docstring (`:163-172`) names every recovery mechanism: the per-entry `if definition.finalized: continue` guards (`:235`, `:244`, `:263`) skip already-decorated types; `apply_interfaces` re-mutating `__bases__` is a no-op because it filters via `iface not in type_cls.__mro__`; `registry.mark_finalized()` runs only as the last statement of the function so a Phase 2/2.5/3 raise leaves the flag False. Same partial-finalize recovery is pinned at `tests/test_registry.py:387-440` plus the Phase 2.5 subpass-ordering tests at `tests/filters/test_finalizer.py:367-468`.
- **TYPE_CHECKING import discipline.** The `DjangoTypeDefinition` import is deferred under `TYPE_CHECKING` (`:67-68`) with `# pragma: no cover - type-checking-only import.` per the `AGENTS.md` rule 12 calibration (pragma justified for branches genuinely unreachable under the test runner). Verified by the worker memory carry-forward from `rev-optimizer__field_meta.md` re `from __future__ import annotations` enabling TYPE_CHECKING demotion — same pattern correctly applied here.
- **Local imports for cross-package cycles.** Both `_bind_ordersets` (`:670-677`) and `_bind_filtersets` (`:777-784`) defer their sidecar-package imports to function scope to keep `types/finalizer.py` independent of orders / filters module-load order. The deferred-import block is documented with its own comment block (`:670-674` / `:777-781`) framing the consumer-import-driven activation contract. Same pattern as the `_django_patches.py` `apps.py::AppConfig.ready` deferred import calibration recorded by `rev-apps.md`.
- **Test coverage discipline across three trees.** Direct test pins identified for every documented-contract surface: `tests/types/test_definition_order.py` (24 tests in this file alone cover Phase 1 contracts + audit ordering + filter-binding-across-module-boundary pins); `tests/test_registry.py:1067+` (audit success + audit-vs-unresolved ordering); `tests/filters/test_finalizer.py` (23 tests for Phase 2.5 filter subpasses); `tests/orders/test_finalizer.py` (19 tests for Phase 2.5 order subpasses).
- **Decision-7 first-bind model-compat check is finalize-time visible per H-core-3.** The `_bind_filterset_owner` first-bind branch at `:319-327` and `_bind_orderset_owner` first-bind branch at `:505-513` both reject mis-wired `Meta.filterset_class` / `Meta.orderset_class` at finalize time with a typed `ConfigurationError` — replacing the opaque query-time `FieldError` the mismatch would otherwise raise far from its cause. Both code paths share the documented `not issubclass(definition.model, sidecar_model)` shape (filter and order); the asymmetry in how `sidecar_model` is resolved (filter `._meta.model` vs order `getattr(getattr(...))`) is the load-bearing sidecar-class-API distinction noted under Lows.
- **`spec-021 H2 of rev8` consumer error wording is grep-stable.** Both filter-side `_format_owner_mismatch_error` (`:404`) and `_format_owner_pk_mismatch_error` (`:429`) end with the literal `(per spec-021 H2 of rev8).` suffix; the order-side `_format_owner_ordersets_mismatch_error` (`:576`) ends with `(per spec-028 Decision 6).`. The grep-stable footer is the documented test-pin shape — `tests/filters/test_finalizer.py:225` asserts `"diverging targets"` in msg, `:367` asserts the orphan suggestion text. Any rename of either spec-NN would force a paired test + source + GLOSSARY update; the citation-drift Lows above cover the source side of that contract.

### Summary

`types/finalizer.py` is the once-only build-gate for the package's `DjangoType` registry — 860 lines, 15 symbols, zero High / zero Medium at file scope. Phase 1's failure-atomic contract is correctly documented, implemented, and test-pinned; Phase 2.5's four-subpass binding pipeline is consistently shaped across the filter / order sidecar pair with three intentional sibling duplications kept verbatim per the load-bearing-distinction calibration. Eight `_format_*` formatter siblings live at the top of the module so consumer error matching stays grep-stable. The only material defect class is citation drift: 8 `spec-021` cites that should be `spec-027` (forward to folder pass per the `rev-filters.md` escalation precedent across 43 already-filed sites), 2 `spec-014` cites that should be `spec-018` (same single-digit drift class as the `rev-optimizer__extension.md` / `rev-optimizer__walker.md` Lows), 1 `feedback.md` cite pointing at archived content, and 4 line-number citations rot-prone to spec edits. The `finalize_django_types` GLOSSARY entry is current at the 0.0.4-shipped contract level with Phase 2.5 enumeration correctly deferred to the per-`Meta.*sidecar*_class` entries pending the spec-028 joint-cut `shipped (0.0.8)` flip. Standard three-spawn cycle — `Status: under-review` — with the Lows routing through the comment-pass step and the forwards lifting into `rev-types.md` and `rev-django_strawberry_framework.md` as enumerated.

---

## Fix report (Worker 2)

Consolidated single-spawn (shape #4) — all nine in-cycle Lows are citation hygiene / comment fixes with zero behaviour change. Five forward-looking defer-with-trigger Lows untouched per artifact's own prose. Logic + comment + changelog disposition collapsed into this single spawn.

### Files touched
- `django_strawberry_framework/types/finalizer.py::finalize_django_types` (module docstring `#"reject orphan ``filter_input_type`` references) per spec-027 Decision 6"`) — `spec-021` → `spec-027` swap (Phase 2.5 narrative cites the filtering subsystem, not the apps spec).
- `django_strawberry_framework/types/finalizer.py::_format_ambiguity_error` — `spec-014` → `spec-018` swap at both substring anchors in the docstring (`#"with the fix sentence"` and `#"test_finalize_ambiguity_error_message_contains_actionable_fix"` both verified to live in `docs/SPECS/spec-018-meta_primary-0_0_6.md:127` / `:133`; zero matches in `spec-014-testing_shift-0_0_4.md`).
- `django_strawberry_framework/types/finalizer.py::finalize_django_types` (the `apply_interfaces` gate inline comment in the Phase-2.5 loop) — dropped the `feedback.md § High "Direct relay.Node inheritance bypasses Relay finalization"` cross-reference entirely per artifact recommendation (b): the surrounding prose ("they also catch consumers who wrote ``class Foo(DjangoType, relay.Node)`` directly without ``Meta.interfaces``") names the contract clearly on its own; `grep -in "Direct relay.Node" docs/feedback.md` → zero matches, citation rotted.
- `django_strawberry_framework/types/finalizer.py::_bind_filterset_owner` (docstring `#"pair is idempotent (supports partial-finalize recovery"`) — `spec-021 Decision 6 lines 683-685` → `spec-027 Decision 6 #"Partial-finalize lifecycle"` (substring anchor verified unique in spec-027 via `grep -c`).
- `django_strawberry_framework/types/finalizer.py::_bind_filterset_owner` (docstring `#"Any divergence raises ``ConfigurationError`` naming both owners"`) — `spec-021 line 574` → `spec-027 #"owning `FilterSet`'s target `DjangoType`"` (substring anchor verified unique in spec-027 via `grep -c`).
- `django_strawberry_framework/types/finalizer.py::_format_owner_mismatch_error` (docstring `#"Names both owners' qualified names"`) — same `spec-021 line 574` → `spec-027 #"owning `FilterSet`'s target `DjangoType`"` swap; this is the docstring referent for the consumer-visible error string `#"per spec-027 H2 of rev8"` below.
- `django_strawberry_framework/types/finalizer.py::_format_owner_mismatch_error` (consumer-visible error message body `#"Declare separate FilterSet subclasses for the diverging owners"`) — `(per spec-021 H2 of rev8).` → `(per spec-027 H2 of rev8).` (this is one of two consumer-visible error-message sites that ship `spec-NN H2 of rev8` literally in the runtime `ConfigurationError` body; matches the spec-027 escalation precedent recorded across 43 `filters/` sites in `rev-filters.md::M1`).
- `django_strawberry_framework/types/finalizer.py::_format_owner_pk_mismatch_error` (consumer-visible error message body `#"separate FilterSet subclasses for the diverging owners"`) — same `spec-021 H2 of rev8` → `spec-027 H2 of rev8` swap; the second consumer-visible error-message site.
- `django_strawberry_framework/types/finalizer.py::_format_orphan_filtersets_error` (docstring `#"orphan branch uses the spec-pinned actionable message"`) — `spec-021 line 673` → `spec-027 #"Bind the owner."` (substring anchor verified unique in spec-027 via `grep -c`).
- `django_strawberry_framework/types/finalizer.py::_bind_filtersets` (docstring `#"Subpass 3 — orphan validation."`) — `spec-021 line 673` → `spec-027 #"Bind the owner."` (same anchor as above, second cite of the same spec passage).
- `django_strawberry_framework/types/finalizer.py::_bind_filtersets` (inline comment in Subpass 2 `#"LazyRelatedClassMixin.resolve_lazy_class"`) — `spec-021 lines 416 + 1030` → `spec-027 #"lazy-related-filter targets unresolved at finalize raise"` (the artifact's line 416 / line 1030 numbers were noted as resolving to unrelated content; the substring anchor names the actual contract — `ImportError` from unresolved lazy refs rewraps as `ConfigurationError` at finalize time; verified unique in spec-027 via `grep -c`).

Five defer-with-trigger Lows untouched per artifact's own prose (Lows 5-9 in the artifact: `_audit_primary_ambiguity` O(N) sort, `_bind_orderset_owner` Meta-defensive getattr asymmetry, `_owner_definition` model-mismatch None-skip, `_bind_*_owner` identity-then-equality DRY pattern, GLOSSARY drift forward to project pass). All triggers are explicit in the artifact's `Low:` body; no source change in scope this cycle.

### Tests added or updated
None — citation-hygiene / comment-fix consolidated pass with zero behaviour change. Existing test pins continue to assert against the consumer-visible error-string substrings (`"diverging targets"`, `"H2 of rev8"`, `"Bind the owner"` actionable suggestion text); the swap from `spec-021 H2 of rev8` to `spec-027 H2 of rev8` at the two consumer-visible error sites is a one-character substring change. The artifact's `## What looks solid` section names `tests/filters/test_finalizer.py:225` (`"diverging targets"` assertion) and `:367` (orphan suggestion text); neither asserts against the `spec-NN` prefix, so no test surface needs to flex.

### Validation run
- `uv run ruff format .` — pass (212 files unchanged)
- `uv run ruff check --fix .` — pass (All checks passed!)
- `git status --short uv.lock` — clean (no uv.lock churn)
- `grep -n "spec-021\|spec-014\|feedback.md" django_strawberry_framework/types/finalizer.py` — zero hits (sweep complete)

### Notes for Worker 3
- Shape #4 consolidated-single-spawn (artifact `Low:` section is 9 in-cycle Lows + 5 explicit defer-with-trigger). Status set to bare `fix-implemented` per the consolidated-spawn end-state.
- All four rotted line-number cites replaced with `#"unique substring"` anchors per AGENTS.md rule 27 (the rule's exact shape: `path::QualifiedName #"unique substring"` or `path #"unique substring"`); each substring's uniqueness verified in `docs/SPECS/spec-027-filters-0_0_8.md` via `grep -c` before commit.
- The artifact noted that spec-021 lines 416 / 1030 resolve to unrelated content TODAY; the substring anchor "lazy-related-filter targets unresolved at finalize raise" names the actual rewrap contract the comment captures (line 1038 in spec-027, inside the Slice-3 test plan). That is the right rationale anchor for the ImportError → ConfigurationError rewrap convention.
- The `feedback.md § High` cite drop (artifact recommendation b) was chosen over relinking to a spec-015 / spec-016 anchor because the contract the comment captures is already self-named in the surrounding prose; relinking would have added another rot-prone pointer without earning its keep.
- spec-021 → spec-027 swap is the same drift class the filters folder pass already escalated to Medium across 43 sites in `filters/{__init__,base,factories,inputs,sets}.py` per `rev-filters.md::M1`; this cycle catches up the 8 more sites in `types/finalizer.py` that the filters folder pass would have missed by scope.
- Two of the spec-021 sites are consumer-visible runtime `ConfigurationError` message bodies (the `"(per spec-021 H2 of rev8)."` suffixes at `_format_owner_mismatch_error` / `_format_owner_pk_mismatch_error`). Those are now `"(per spec-027 H2 of rev8)."` — a consumer who pastes the error into a search engine will land on spec-027-filters-0_0_8.md instead of the apps spec.
- No shadow file used during fix implementation.
- No false-premise rejections.
- uv.lock unchanged across the cycle (no `uv run` dependency surface invoked).

---

## Comment/docstring pass

Consolidated into the single Worker 2 spawn — see `## Fix report (Worker 2)` above. The entire cycle was a comment / docstring / inline-comment pass; there is no separate logic vs. comment partition this cycle.

### Per-finding dispositions

- Low #1 (`spec-021` citation drift across 8 sites): fixed (eight swaps applied verbatim per `## Files touched` enumeration above).
- Low #2 (`spec-014` citation drift at `_format_ambiguity_error` docstring): fixed (two swaps to `spec-018` at the substring anchors).
- Low #3 (Rotted `feedback.md` citation at `finalize_django_types` Phase-2.5 loop): fixed via artifact recommendation (b) — cross-reference dropped; surrounding prose names the contract.
- Low #4 (Rotted line-number citations across 4 sites): fixed in this cycle (folded into the spec-021 → spec-027 sweep per the artifact's own deferral trigger condition); all four replaced with substring anchors per AGENTS.md rule 27.
- Low #5 (`_audit_primary_ambiguity` O(N) sort): deferred-with-trigger per artifact — surface tightening only; no in-cycle edit.
- Low #6 (`_bind_orderset_owner` Meta-defensive getattr asymmetry): deferred-with-trigger per artifact — load-bearing intentional sibling design; no in-cycle edit.
- Low #7 (`_owner_definition` model-mismatch None-skip): deferred-with-trigger per artifact — surface tightening only; no in-cycle edit.
- Low #8 (`_bind_*_owner` identity-then-equality DRY pattern): deferred-with-trigger per artifact's DRY analysis — collapse only when third sidecar lands; no in-cycle edit.
- Low #9 (GLOSSARY drift forward to project pass): no in-cycle edit per artifact — joint-cut deferral pattern per spec-027 Decision 10, forwarded to `rev-django_strawberry_framework.md` project pass alongside the four other filter-subsystem GLOSSARY forwards.

### Validation run
- `uv run ruff format .` — pass
- `uv run ruff check --fix .` — pass

### Notes for Worker 3
Pure docstring / comment / inline-comment edits; no logic surface changed. Sibling comment-pass calibrations for the consolidated shape from the memory digest above: `exceptions.py`, `list_field.py`, `testing/_wrap.py`, `types/converters.py`, `types/definition.py`, `optimizer/_context.py`, `optimizer/extension.py`, `optimizer/hints.py`, `optimizer/plans.py`, `filters/` folder pass.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Cites BOTH halves per `worker-2.md::Changelog dicta — three-state disposition` "Not warranted" rule:

1. `AGENTS.md` rule 21: "Do not update CHANGELOG.md unless explicitly instructed."
2. The active plan does not name `CHANGELOG.md` for this cycle, and the dispatch prompt explicitly named "Not warranted" as the calibration: "Changelog `Not warranted` (citation hygiene, no behavior change) citing AGENTS.md + active plan silence."

Cycle's edits are entirely citation hygiene and comment fixes — no logic change, no behaviour change, no consumer-facing typed-error contract change. The two consumer-visible error-message sites change `spec-021 H2 of rev8` → `spec-027 H2 of rev8` (a one-character `1` → `7` substring difference); the error class (`ConfigurationError`), the trigger condition, the field list in the message, and the actionable-suggestion text are all bit-for-bit identical. No consumer who matches on `ConfigurationError` or on `"diverging targets"` / `"separate FilterSet subclasses"` substrings is affected.

Sibling calibrations for `Not warranted` on the same citation-hygiene shape from the memory digest: `filters/` folder pass (`spec-021`→`spec-027` citation hygiene + Slice-tense rotations across 43 sites/5 files; no logic change — same pattern as this cycle but at folder scope), `optimizer/extension.py` (`spec-014`→`spec-018` at one site + GLOSSARY lift), `optimizer/walker.py` (`spec-014`→`spec-018` rotation). All ruled `Not warranted` under the same AGENTS.md #21 + active-plan-silence pair.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass
- `uv run ruff check --fix .` — pass

---

## Verification (Worker 3)

### Logic verification outcome
Consolidated single-spawn (shape #4) cycle: all in-cycle Lows discharged or deferred-with-trigger per the artifact's own prose; zero behaviour change.

- **Low #1 (spec-021 → spec-027 across 8/9 enumerated sites).** Diff covers every enumerated line: module docstring `:25`, `_bind_filterset_owner` docstring `:271-275` and `:291-294`, `_format_owner_mismatch_error` docstring `:387-392` and consumer-visible body `:399-402` (`(per spec-027 H2 of rev8).`), `_format_owner_pk_mismatch_error` consumer-visible body `:425-427` (`(per spec-027 H2 of rev8).`), `_format_orphan_filtersets_error` docstring `:455-460`, `_bind_filtersets` docstring `:753-758` and Subpass-2 comment `:794-803`. `grep -n "spec-021" django_strawberry_framework/types/finalizer.py` → zero hits; `grep -c "spec-027" ...` → 9 (matches the 9 enumerated lines; the artifact's `8 sites` heading versus 9-line enumeration is a counting glyph, not a missed swap).
- **Low #2 (spec-014 → spec-018 at 2 sites).** Both substring anchors at `_format_ambiguity_error` docstring `:102-103` swapped to `spec-018 #"with the fix sentence"` and `spec-018 #"test_finalize_ambiguity_error_message_contains_actionable_fix"`. `grep -c` confirms both anchors are unique in `docs/SPECS/spec-018-meta_primary-0_0_6.md` (1 each).
- **Low #3 (feedback.md cross-reference at `:250-252`).** Dropped per artifact recommendation (b); surrounding prose at `:246-250` ("they also catch consumers who wrote `class Foo(DjangoType, relay.Node)` directly without `Meta.interfaces`") self-names the contract. `grep -n "feedback.md" django_strawberry_framework/types/finalizer.py` → zero hits.
- **Low #4 (rotted line-number cites at 4 sites).** All four replaced with AGENTS rule 27 substring anchors: `spec-027 Decision 6 #"Partial-finalize lifecycle"`, `spec-027 #"owning \`FilterSet\`'s target \`DjangoType\`"`, `spec-027 #"Bind the owner."`, `spec-027 #"lazy-related-filter targets unresolved at finalize raise"`. All four substrings confirmed unique in `docs/SPECS/spec-027-filters-0_0_8.md` via `grep -c` → 1 each. The "lines 416 + 1030" replacement names the actual rewrap contract (ImportError → ConfigurationError) rather than the stale line range that resolved to unrelated content today.
- **Lows #5-#9 (deferred-with-trigger / forwarded).** Untouched per the artifact's own prose for each (O(N) sort surface tightening, `_bind_orderset_owner` Meta-defensive getattr load-bearing asymmetry, `_owner_definition` None-skip surface tightening, `_bind_*_owner` identity-then-equality DRY pattern under third-sidecar trigger, GLOSSARY drift forwarded to `rev-django_strawberry_framework.md` project pass under joint-cut deferral pattern).

DRY analysis disposition: all four DRY bullets in the artifact are defer-with-explicit-trigger (third sidecar lands); zero in-cycle DRY action. Verified the deferral premises hold against the current source (two filter/order mirror pairs, identical wrap-block shape, identical `_targets_diverge` predicate shape).

### DRY findings disposition
All four DRY bullets deferred-with-trigger per the artifact's own prose; no in-cycle helper extraction. The "third sidecar lands" trigger is the load-bearing distinction keeping the filter/order mirror pair legible today — same calibration as `rev-filters__sets.md::apply_sync` / `apply_async`.

### Temp test verification
- Temp test files used: none.
- Disposition: not applicable (citation-hygiene / comment-only cycle, no behaviour change).

### Verification outcome
cycle accepted; verified

- `git diff -- CHANGELOG.md` is empty (matches `Not warranted` claim).
- Changelog disposition cites BOTH AGENTS.md rule 21 AND dispatch-prompt / active-plan silence — both halves present per the three-state rule.
- `uv run ruff format --check django_strawberry_framework/types/finalizer.py` → "1 file already formatted"; `uv run ruff check django_strawberry_framework/types/finalizer.py` → "All checks passed!".
- Two consumer-visible error-message sites swap `spec-021 H2 of rev8` → `spec-027 H2 of rev8` (one-character `1`→`7`); the precedent chain (`rev-filters.md` 43-site folder-pass swap including consumer-visible error bodies ruled `Not warranted`, `rev-optimizer__extension.md` and `rev-optimizer__walker.md` `spec-014`→`spec-018` rotations ruled `Not warranted`) holds — the citation footer is not a test-pinned substring, so the `Not warranted` framing is honest.
- Five forward-looking Lows and four DRY deferrals are gated on the third-sidecar trigger; the deferral audit trail in the artifact is grep-resolvable for the future-cycle author.

---

## Iteration log

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
