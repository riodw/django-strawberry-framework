# Build: Cross-slice integration pass

Spec reference: `docs/spec-relay_interfaces.md`
Status: final-accepted

## Plan (Worker 1)

The integration pass examined the five final-accepted slice artifacts (`bld-slice-1-validation_and_storage.md` through `bld-slice-5-promotion_docs_version.md`) plus the post-promotion source tree as it stands after Slice 5 closed. The scan focused on:

1. Re-confirming the four-discriminator architecture across Slices 1/2/3/4 has not been collapsed by Slice 5's promotion + bypass-deletion refactor.
2. Cross-file repeated string literals (`"id"`, `"pk"`, the four resolver names, `"interfaces"`, `Meta.<key>` lead-ins, error message prefixes).
3. Import-direction one-way dependency: `types/relay.py` does not import from `types/base.py`; `types/finalizer.py` imports orchestration helpers; `types/definition.py` is bottom-most.
4. Canonical doc phrasings landed verbatim across `docs/FEATURES.md`, `docs/README.md`, `TODAY.md`, `KANBAN.md`, `CHANGELOG.md`.
5. Deferred follow-ups recorded in each slice's `What looks solid` / `DRY findings` / `Notes for Worker 1` sections that should land in this pass.
6. `__init__.py` `__all__` matches the six pinned names (Definition of done item 11).
7. `pytest-asyncio` integration (Slice 4 carry-forward): only the intentional five Relay async tests exist; no accidental `async def` elsewhere.

## Integration findings (Worker 1)

None.

### High:

None.

### Medium:

None.

### Low:

None.

### Cross-slice DRY observations

Repeated string literals reported by `scripts/review_inspect.py` against the post-Slice-5 source (fresh shadow run at integration-pass time):

- `django_strawberry_framework/types/base.py`: `4x optimizer_hints`, `2x description`, `2x interfaces`. All three are intentional intra-file repeats (the `optimizer_hints` literal appears in `ALLOWED_META_KEYS`, `_validate_meta`'s docstring, `_validate_optimizer_hints`'s implementation, and a test-reachable error message; `interfaces` appears in `ALLOWED_META_KEYS` at line 61 and `getattr(meta, "interfaces", None)` at line 302 — the validator's single read site; `description` appears in `ALLOWED_META_KEYS` and `DjangoTypeDefinition` construction). None are cross-file duplicates.
- `django_strawberry_framework/types/relay.py`: `2x __func__`. Both occurrences are inside `install_relay_node_resolvers` (`existing_func = getattr(existing, "__func__", None)` at line 327 and `node_func = getattr(node_default, "__func__", None)` at line 328) — Slice 4's pass-2 review acknowledged this as borderline and intentionally left inline so the `__func__` identity discriminator stays visible at its only call site. Not a finding.
- `django_strawberry_framework/types/finalizer.py`: no repeated literals.
- `django_strawberry_framework/types/resolvers.py`: `2x reverse_one_to_one`. Pre-existing; not introduced by the Relay build. Out of scope for this integration pass.
- `django_strawberry_framework/types/definition.py`: no repeated literals.

Cross-file literal scan (production source only, via `grep -rn`):

- `"interfaces"` appears at `base.py:61` (in `ALLOWED_META_KEYS`) and `base.py:302` (in `_validate_interfaces`'s `getattr(meta, "interfaces", None)` lookup). Same file, same intentional shape — one defines the allowed-keys set membership, the other looks up the consumer's `Meta` attribute by the same name. No cross-file duplication.
- `"pk"` appears only in `types/relay.py` (at lines 145, 161, plus docstring mentions at 135, 139, 152, 153). All are inside the two `_resolve_id_attr_default` / `_resolve_id_default` helpers and represent Django's conventional "primary-key field name fallback" idiom (the upstream `strawberry_django/relay/utils.py:285-348` borrow site uses the same literal). Not a cross-file repeat.
- `"is_type_of"` appears once at `relay.py:75` (the consumer-preservation discriminator in `install_is_type_of`). Single site; no need for a constant.
- The four resolver method names (`"resolve_id"`, `"resolve_id_attr"`, `"resolve_node"`, `"resolve_nodes"`) appear exactly once each in production source, all four inside the `_RELAY_RESOLVER_DEFAULTS` tuple at `relay.py:297-302`. Slice 4 pass-2 consolidated these into a single source of truth; the shadow's repeated-literal counts dropped from `2x` per name in pass 1 to `1x` in pass 2 and remain `1x` after Slice 5.
- `Meta.<key>` lead-in prefix (`f"{meta.model.__name__}.Meta.interfaces ..."`) appears across the six `raise ConfigurationError(...)` sites inside `_validate_interfaces` (`base.py:300-360`). Slice 1 pass-2 consolidated the long shape-rejection lead-in into `_INTERFACES_SHAPE_ERROR_LEAD_IN` + `_interfaces_shape_error(...)` (`base.py:271-283`). The remaining entry-level "must contain interface classes" / "may not contain DjangoType" / "not a Strawberry interface" / "duplicate entries" messages reuse the prefix verbatim by intent (Decision 4 line 319), and Slice 4's composite-pk error at `relay.py:130-135` continues the same `<Model>.Meta.interfaces`-rooted error scaffolding when relevant (the composite-pk error addresses the model, not `Meta.interfaces`, so its lead-in is `f"{model.__name__}: relay.Node is not supported on models with a composite primary key. ..."` — a deliberate distinction since the error is about the model's pk shape rather than a Meta-value problem).

**Four-discriminator confirmation** (carried forward from every prior slice's memory):

1. Slice 1's `_validate_interfaces` at `django_strawberry_framework/types/base.py:277` — Strawberry-interface validation at class-creation time inside the `Meta`-shape validator. Intact, returns the normalized tuple to `_validate_meta`.
2. Slice 2's `__dict__` membership at `django_strawberry_framework/types/relay.py:75` (`if "is_type_of" in type_cls.__dict__: return`) — preserves consumer-declared `is_type_of` from `install_is_type_of`. Intact; unchanged by Slice 5.
3. Slice 3's tuple-membership at `django_strawberry_framework/types/base.py:557` (`suppress_pk_annotation = relay.Node in interfaces`) — suppresses the synthesized `id` annotation at collection time inside `_build_annotations`. Intact; unchanged by Slice 5.
4. Slice 4's MRO-issubclass check at `django_strawberry_framework/types/relay.py:50` (`return issubclass(type_cls, relay.Node)` inside `implements_relay_node`) plus the `__func__` identity test at `django_strawberry_framework/types/relay.py:327-328` (`existing_func = getattr(existing, "__func__", None); node_func = getattr(node_default, "__func__", None)`) inside `install_relay_node_resolvers` — gates the composite-pk check + injects the four `resolve_*` defaults at finalization time. Intact; unchanged by Slice 5.

No discriminator was collapsed into a generic helper. Each answers a structurally different question at its own lifecycle phase. The carry-forward from Slices 2/3/4's memory (each warning the next slice against unifying discriminators) was honored end-to-end.

### Helper-script confirmation

Re-ran `scripts/review_inspect.py --output-dir docs/build/shadow` on every production source file the build touched, regenerating the shadow overviews at integration-pass time so the "Repeated string literals" / "Imports" sections reflect the post-Slice-5 state:

- `django_strawberry_framework/types/base.py` — re-run (overview pre-Slice-5 was from Slice 1's planning pass; needed refresh after Slice 5's promotion + comment-block removal). Fresh overview confirms `4x optimizer_hints`, `2x description`, `2x interfaces` — all intra-file intentional.
- `django_strawberry_framework/types/relay.py` — re-run. Confirms `2x __func__` only; the four resolver names are each `1x` (Slice 4 pass-2 consolidation held through Slice 5).
- `django_strawberry_framework/types/finalizer.py` — re-run. No repeated literals.
- `django_strawberry_framework/types/resolvers.py` — re-run. `2x reverse_one_to_one` is pre-existing, not introduced by the Relay build.
- `django_strawberry_framework/types/definition.py` — re-run (was missing entirely from `docs/build/shadow/` because Slice 1's storage change was small and the helper was not run on it during slice planning; Slice 1's plan ran the helper on `base.py` only). Fresh overview confirms no repeated literals and one-way dependency (imports `FieldMeta`, `OptimizerHint` from `..optimizer`; no upward imports). Skip recorded for Slice 1: the original skip was acceptable because the change was a single-line comment update on the `interfaces` slot at line 42, but the integration pass needs the overview for cross-file scanning, so the helper was run here.

Skip recorded for `django_strawberry_framework/__init__.py`: per BUILD.md "no review-worthy logic" allowance, the Slice 5 edit was one `__version__` line bump plus removal of a satisfied TODO anchor comment (no logic, no new imports, no exports). `__all__` and the import block are unchanged from `0.0.4`. The static-inspection helper is skipped for this file.

### Canonical-phrasing confirmation

Each canonical phrasing from Slice 5's DRY analysis was verified verbatim across the named docs:

- **Subsystem name** — "Relay Node integration":
  - `docs/FEATURES.md:66` — `### Relay Node integration` (subsection header).
  - `docs/README.md:44` — `### Relay Node` (gating header; the spelling difference is intentional per Slice 5's plan note "two spellings are intentional, the second is the full subsystem name and the first is the gating header").
  - `docs/README.md:65` — `See [FEATURES.md's Relay Node integration subsection]...` cross-reference uses the full subsystem name.
  - `KANBAN.md:328` — `### DONE-011 — 0.0.5 Relay interfaces and Node foundation` (the long-form card title from Slice 5's plan).
- **Resolver list literal in canonical order** — `resolve_id_attr`, `resolve_id`, `resolve_node`, `resolve_nodes`:
  - `docs/FEATURES.md:86` — verbatim.
  - `CHANGELOG.md:13` — verbatim.
  - `KANBAN.md:337` — verbatim.
  - All three match `_RELAY_RESOLVER_DEFAULTS` order at `types/relay.py:298-301`.
- **Composite-pk constraint phrasing** — "Models whose primary key is a Django 5.2+ `CompositePrimaryKey` raise `ConfigurationError` at finalization; declare an explicit `id: relay.NodeID[...]` annotation or remove `relay.Node` from `Meta.interfaces` to remediate.":
  - `docs/FEATURES.md:90` — verbatim.
  - `CHANGELOG.md:16` — verbatim.
  - `KANBAN.md:340` — verbatim.
- **`is_type_of` scope phrasing** — "`is_type_of` injection is unconditional for every `DjangoType` (Relay-declared or not); consumer-declared `is_type_of` is preserved.":
  - `docs/FEATURES.md:89` — verbatim.
  - `CHANGELOG.md:15` — verbatim.
  - `KANBAN.md:339` — verbatim.
- **Promotion-line phrasing** — "`Meta.interfaces` promoted from `DEFERRED_META_KEYS` to `ALLOWED_META_KEYS`.":
  - `CHANGELOG.md:20` — verbatim, in `### Changed`.
  - Single site (other docs describe shipped state; only the changelog tracks the literal promotion).
- **TODAY.md** updates per Slice 5's plan:
  - `TODAY.md:14` — the library-app callout sentence ("`GenreType` declares `interfaces = (relay.Node,)` and its live `/graphql/` HTTP test ... exercises the end-to-end Relay GlobalID round trip") landed correctly. `Meta.interfaces` and `Relay node and connection integration` removed from the "not directly usable yet" list per spec lines 524-525.
- **`__init__.py` `__all__` pin** — Definition of done item 11. Confirmed: `__all__` at `django_strawberry_framework/__init__.py:26-33` contains exactly six names (`DjangoOptimizerExtension`, `DjangoType`, `OptimizerHint`, `__version__`, `auto`, `finalize_django_types`). `tests/base/test_init.py::test_public_api_surface_is_pinned` pins the same six-name set; the test is unchanged by Slice 5.

No prose drift across the five docs.

### Notes for Worker 0 / closeout

- Status flipped directly to `final-accepted`; no consolidation cycle needed. Worker 0 can mark the integration-pass checkbox in `docs/build/build-relay_interfaces-0_0_5.md` and dispatch Worker 1 for `bld-final.md` next (the final test-run gate).
- The four-discriminator architecture is intact and the bypass-deletion refactor (Slice 5) did not collapse, hoist, or generalize any of them. Carry forward to `bld-final.md`'s focus: the full `uv run pytest` sweep is the cycle's only remaining gate; coverage line-by-line inspection is out of scope per BUILD.md "Final test-run gate."
- Note for `bld-final.md`: Slice 4 added `pytest-asyncio>=1.0.0` to `[dependency-groups] dev` and `asyncio_mode = auto` to `pytest.ini`. Only the five intentional Slice-4 async tests under `tests/types/test_relay_interfaces.py` (lines 586, 598, 610, 625, 639) use `async def`; no accidental sync test was annotated `async` and no other test tree is affected. The full sweep should run cleanly.
- Note for `bld-final.md`: Slice 5 deleted `tests/_relay_bypass.py` and `docs/spec-relay_interfaces-3.md`. Cross-tree `grep` for `_relay_bypass` and `stage_relay_definition` returns zero matches; `docs/spec-relay_interfaces-3.md` is absent from disk. No orphan imports.
- Carry-forward to closeout retrospective: the four-discriminator architecture is the load-bearing DRY invariant of this build. Future builds touching `__init_subclass__` / `__bases__` / Strawberry-default-resolver injection should preserve the same structural-split posture — collapsing override discriminators into a generic helper is a DRY false positive that upstream `strawberry-django` itself avoids.

## Final verification (Worker 1)

- Cross-slice DRY clean: **Y**.
- Helper coverage confirmed: **Y** (every production source file the build touched has a fresh shadow overview under `docs/build/shadow/`; one helper skip recorded for `__init__.py` per BUILD.md "no review-worthy logic" allowance).
- Canonical phrasings consistent: **Y** (five canonical strings landed verbatim across the five docs per Slice 5's DRY analysis).

### Summary

The cross-slice integration pass for the `relay_interfaces` / `0.0.5` build finds the post-promotion source tree clean. Every prior slice's accepted artifact has been re-read in slice order; the four-discriminator architecture across Slices 1/2/3/4 (Slice 1's `_validate_interfaces`, Slice 2's `__dict__` membership for `is_type_of`, Slice 3's `relay.Node in interfaces` tuple-membership for `id` suppression, Slice 4's `issubclass(cls, relay.Node)` MRO + `__func__` identity for the four `resolve_*` defaults) survived Slice 5's promotion + bypass-deletion refactor unchanged — no discriminator was collapsed into a generic helper. `_RELAY_RESOLVER_DEFAULTS` remains the sole iteration site for the four method names in production source (each name `1x`, confirmed by fresh shadow overview). The validated `interfaces` tuple flows one-way from `_validate_meta` (`base.py:393`) through `__init_subclass__` capture into both `DjangoTypeDefinition(interfaces=...)` storage (Slice 1) and `_build_annotations(interfaces=...)` consumption (Slice 3); Phase 2.5 in `finalize_django_types()` reads from `definition.interfaces` (Slice 4). No re-read of `Meta` outside the single `_validate_interfaces` site. The cross-file repeated-literal scan returns no cross-file duplicates: `"interfaces"` lives in two intentional intra-file sites in `base.py`; `"pk"` is the Django-conventional fallback string and lives only in `types/relay.py`; `"is_type_of"` appears once; the four resolver names appear exactly once each. Cross-doc canonical phrasings (subsystem name, resolver list order, composite-pk constraint, `is_type_of` scope, promotion line) landed verbatim across `docs/FEATURES.md`, `docs/README.md`, `TODAY.md`, `KANBAN.md`, `CHANGELOG.md`. `__init__.py` `__all__` is unchanged at the six pinned names (Definition of done item 11). No consolidation cycle is needed.

### Spec changes made (Worker 1 only)

No spec edits. Slice 4's prior spec edits (Decision 3 lines 313-315 clarifying the `"pk"` coercion and the optimizer-extension deferral) and Slice 5's prior spec edit (the spec status line at line 3, trimming the now-stale "remains to be deleted" qualifier) are the canonical spec changes for this build; the integration pass surfaces no further reconciliation needs.

### Final status

`final-accepted`
