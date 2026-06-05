# Build: Cross-slice integration pass — spec-029 consumer_dx_cleanup (0.0.9)

Spec reference: `docs/spec-029-consumer_dx_cleanup-0_0_9.md`
Status: final-accepted

> Run note: performed **inline by Worker 0** at the maintainer's direction ("no more dispatching"), after the build was committed (`2d1f296`) — not via a Worker 1 subagent. The review reads the committed source + the three accepted slice artifacts + freshly-regenerated `docs/shadow/` overviews.

## Pre-write requirements (BUILD.md "Cross-slice integration pass")

1. **Read every prior `bld-slice-*.md` artifact in slice order.** Done — `bld-slice-1-extensions_singleton_factory.md`, `bld-slice-2-inspect_django_type.md`, `bld-slice-3-nullability_overrides.md` (all `final-accepted`), and `bld-slice-4-card_completion_wrap.md` (the card-completion wrap; closed via the DB-backed close-out, see `Status` note in that artifact). Slice 4 shipped no package code, so it carries no DRY surface.
2. **Static helper run / skip recorded for every code-bearing `.py`.** Re-ran `scripts/review_inspect.py --output-dir docs/shadow` on the build's four code files: `types/base.py`, `types/converters.py`, `management/commands/inspect_django_type.py`, `optimizer/extension.py` (docstring-only). All four overviews refreshed for this pass.
3. **Repeated-string-literal comparison across the overviews.** Compared (results below) — no literal appears across two or more of the new surfaces.
4. **Imports comparison / dependency direction.** Compared (results below) — one-way `management → types` / `management → optimizer-registry` direction confirmed; no sibling reaches across a documented boundary.
5. **Walked each accepted slice's `What looks solid` + `DRY findings`.** No deferred follow-up was left for this pass to land; each slice resolved its own DRY questions.

## Integration checks

### Duplicated helpers across slices

None. The three slices introduce non-overlapping helpers, each with a single responsibility:
- Slice 1 — per-construction-site `lambda: <instance>` factories (no helper; deliberately not extracted per Decision 3, so per-site cache/strictness lifetime stays explicit).
- Slice 2 — `inspect_django_type.py` command-local helpers (`_yes_no`, `_scalar_row`, `_relation_row`); reuses `export_schema.py`'s `import_module_symbol` loader *shape* (intentional parity, not a copy to consolidate).
- Slice 3 — `convert_scalar(force_nullable=...)` tri-state + `_validate_nullability_override_targets` in `base.py`, reusing the existing `_normalize_sequence_spec` (the `Meta.exclude` guard) and `_format_unknown_fields_error` rather than re-implementing them.

### Cross-slice contract: Slice 2 reader ↔ Slice 3 writer (the one real seam)

Slice 2's `inspect_django_type` reads the resolved annotation from `origin.__annotations__[field.name]` and Django-side metadata from `definition.field_map[snake_case(field.name)]`; Slice 3 *writes* the nullability override into that same `origin.__annotations__` via the `convert_scalar` `force_nullable` seam at construction time. Verified they agree and do not duplicate:
- **Key derivation matches writer/reader.** Command uses `field_map[snake_case(field.name)]` and `origin.__annotations__[field.name]`; `base.py::_build_annotations` writes with the identical `field_map[snake_case(field.name)]` keying and the raw `field.name` annotation key. No drift.
- **Single source for the resolved annotation.** The command reads `origin.__annotations__` (not a `convert_scalar` re-run), so a Slice-3 override is reflected automatically — confirmed by the cross-slice test `test_inspect_reads_resolved_annotation_not_field_null` (landed in the Slice-3 cycle): the command reports `title → String` (post-`nullable_overrides`) and `subtitle → String!` (post-`required_overrides`). The two slices share the contract; neither re-derives the other's nullability.
- **Relay-suppressed-pk handling is single-sourced.** Both the command's suppressed-pk special-case and Slice 3's Relay-pk override rejection key off `relay_shaped` + `model._meta.pk.name` — the same identity `_build_annotations` uses. No parallel Relay detection.

### Inconsistent naming / error handling between slices

Consistent. Construction-time configuration failures raise `ConfigurationError` (Slice 3's five override-rejection paths, matching the existing `Meta`-validation posture); command-time failures raise `CommandError` (Slice 2's five modes, matching `export_schema.py`). The split is correct — `ConfigurationError` is the type-creation contract, `CommandError` is the management-command contract; no slice crosses them.

### Repeated ORM / queryset patterns

None centralizable. Slice 3's acceptance resolver (`Book.objects.exclude(subtitle__isnull=True).order_by("id")`, in the example project) is the only new queryset and is example-app, not package, code. Slice 2 reads `definition.selected_fields` / `field_map` (no new ORM). Slice 1 touched no ORM.

### Misplaced responsibilities between modules

None. Slice 2 (`management/commands/`) is a strict *reader* of the `types/` introspection surface — a one-way `management → types`/registry dependency, the correct direction. Slice 3 stays entirely inside `types/` (base + converters) at construction time, with no finalizer change. Slice 1 touched only schema-construction call sites + docs.

### Missing or too-broad exports

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty** across the whole build — `__all__` / re-export list unchanged. The new command is Django-discovered, not a package export; the override keys are `Meta` surface, not exports. No export drift.

### Repeated string literals / dict keys / tuple shapes across slices

Compared the **Repeated string literals** section of all four shadow overviews:
- `base.py`: `optimizer_hints` 4×, and `description` / `filterset_class` / `interfaces` / `nullable_overrides` / `orderset_class` / `required_overrides` 2× each. The two net-new keys' 2× count (in `ALLOWED_META_KEYS` + their `getattr` read) matches the established `filterset_class` / `orderset_class` pattern — not a new third-literal defect.
- `converters.py`: none.
- `inspect_django_type.py`: `__name__` 2× — an attribute access, not an extractable constant.
- `optimizer/extension.py`: `_strawberry_schema` 2× — pre-existing, untouched by this build's docstring-only change.
- **No literal appears across two or more of the new surfaces.** The command's converter-row labels are command-local; the Meta-key names are base-local; nothing to centralize.

### Comments / docs coherence across the new code

Coherent and one story. The singleton-factory rationale reads identically across `docs/README.md`, `docs/GLOSSARY.md` (`DjangoOptimizerExtension` / `finalize_django_types` / `strawberry_config` / `BigInt` entries), `GOAL.md`, and `TODAY.md`. The new `Schema introspection management command` GLOSSARY entry and the `Meta.nullable_overrides` / `Meta.required_overrides` entries cross-reference each other and the existing `scalar-field-conversion` / `scalar-field-override-semantics` entries with resolving anchors. `docs/GLOSSARY.md` regenerates from the kanban/glossary DB with a clean diff (the DB was reconciled to match the committed, hand-edited content), so the doc layer is internally consistent.

## DRY / consolidation findings

**None. No consolidation loop needed.** The build is clean across slices; no Worker 2 consolidation + Worker 3 review pass is required.

## Summary

The three functional slices compose cleanly: distinct, single-responsibility helpers; one well-defined Slice-2↔Slice-3 seam (`origin.__annotations__`) that both sides agree on without duplication; consistent `ConfigurationError` (construction) vs `CommandError` (command) error contracts; one-way `management → types` dependency; no public-surface drift; no cross-slice repeated literals; coherent doc story (and the generated `docs/GLOSSARY.md` round-trips from the DB). Integration `final-accepted`.
