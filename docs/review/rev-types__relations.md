# Review: `django_strawberry_framework/types/relations.py`

Status: verified

## DRY analysis

- None — the module is 82 lines and hosts exactly two public dataclasses plus one private metaclass at the single canonical home for `PendingRelation` / `PendingRelationAnnotation` scaffolding; the shadow overview confirms 0 control-flow hotspots, 0 calls-of-interest, 0 Django/ORM markers, 0 repeated string literals. The producer (`types/base.py::_build_annotations`) and the consumer (`types/finalizer.py::finalize_django_types`) each import from this module, so the cross-folder consolidation point already exists — every alternative shape would re-introduce the dual-import / split-truth pattern this module was authored to eliminate (per the module docstring at `relations.py:1-16` framing).

## High:

None.

## Medium:

None.

## Low:

### `path:symbol` cross-file references in module + class docstrings drift from `AGENTS.md` rule-27 `path::QualifiedName` convention

The module docstring at `relations.py:7-13` and the class docstring at `relations.py:31-35` both cite `types/base.py:_build_annotations` and `types/finalizer.py:finalize_django_types` using a single-colon `path:symbol` separator, e.g.:

```django_strawberry_framework/types/relations.py:31-34
    Constructed by ``_build_annotations`` (``types/base.py:_build_annotations``)
    when a relation target type is not yet registered; resolved by
    ``finalize_django_types`` (``types/finalizer.py:finalize_django_types``)
    after every ``DjangoType`` has registered.
```

`AGENTS.md` rule 27 mandates `path::QualifiedName` (double-colon separator) for cross-file symbol references in source comments / docstrings, and explicitly says raw `path:NN` line-number citations are allowed only in per-cycle scratchpads. The single-colon `path:symbol` form is neither — it reads as a malformed line-number citation rather than a symbol-qualified path. The package's own sibling at `types/finalizer.py:196` already follows the canonical shape (`` ``types/base.py::_build_annotations`` ``). Same severity calibration as the citation-hygiene Lows recorded in earlier cycles (`spec-016` → `spec-020` drift in `list_field.py`, `spec-014` → `spec-018` drift in `optimizer/extension.py` + `optimizer/walker.py`) — citation-style hygiene, not logic. Recommended replacements:

- `relations.py:7-8` — `` ``_build_annotations`` (``types/base.py:_build_annotations``) `` → `` ``_build_annotations`` (``types/base.py::_build_annotations``) ``
- `relations.py:10-11` — `` ``finalize_django_types`` (``types/finalizer.py:finalize_django_types``) `` → `` ``finalize_django_types`` (``types/finalizer.py::finalize_django_types``) ``
- `relations.py:32` — `` ``_build_annotations`` (``types/base.py:_build_annotations``) `` → `` ``_build_annotations`` (``types/base.py::_build_annotations``) ``
- `relations.py:33-34` — `` ``finalize_django_types`` (``types/finalizer.py:finalize_django_types``) `` → `` ``finalize_django_types`` (``types/finalizer.py::finalize_django_types``) ``

### Module docstring cites spec-014 H1 but does not anchor the rev / decision sub-heading

The module docstring at `relations.py:3-5` cites:

```django_strawberry_framework/types/relations.py:3-5
This module owns the two scaffolding objects that close the import-order trap
addressed by spec-014 H1: ``PendingRelation`` (a frozen dataclass capturing a
relation field whose target ``DjangoType`` was not yet registered at collection
```

`spec-014` is the canonical home for the H1 closure (the registry-side identity contract); the citation correctly survives `docs/SPECS/NEXT.md` Step 8 archive sweeps because the H-number anchor is rev-relative, not path-relative (per the `rev-registry.md` carry-forward calibration: "when an inline rev-anchor citation cites sub-revision numbers / H-numbers, it's audit-trail not link rot"). Drift risk is still non-zero — `optimizer/extension.py` carried a `spec-014 Slice 1` citation that drifted to `spec-018 Slice 1` because the actual reasoning lived in a different spec, and this file's `_build_annotations` post-rename narrative ultimately landed under `spec-018` H2 / H3 per the `rev-optimizer__extension.md::Calibration` audit trail. Defer until a regression in the spec mapping fires or until the spec-NN sweep at the project pass; today the citation is correct against the spec on disk. (`docs/SPECS/spec-014-testing_shift-0_0_4.md` confirms the H1 anchor lives there — verified by the same calibration in earlier optimizer-folder cycles.)

### `PendingRelation.field_name` semantics enclosed in `relations.py:40-42` are pinned by `tests/types/test_relations.py` only at the identity / equality / set-membership layer

The class docstring at `relations.py:40-42` documents:

```django_strawberry_framework/types/relations.py:40-42
    ``field_name`` is the raw Django ``field.name`` as stored on the model; the
    snake-cased form used as a ``field_map`` key is rebuilt at the consumer via
    ``snake_case(pending.field_name)``. ``nullable`` and ``relation_kind`` are
```

The contract is correct against `types/finalizer.py:209` (`field_meta = definition.field_map[snake_case(pending.field_name)]`), but the only tests for `PendingRelation` (`tests/types/test_relations.py:1-69`) pin only the `__hash__` / `__eq__` / set-membership identity surfaces with a non-hashable `_NonHashableField()` stand-in — none of them verify the producer-stores-raw / consumer-rebuilds-via-`snake_case` contract directly. The indirect coverage exists at `tests/types/test_definition_order.py` (every "PendingRelation registered with raw `field.name` then snake_cased at finalize" path), but the file-local test module would benefit from one regression pin that fails loud if `_build_annotations` ever lowercases `field.name` before stuffing it into `PendingRelation` (which would silently double-snake at the finalizer). Defer until either (a) a regression surfaces consumer-side or (b) a third producer of `PendingRelation` lands (today the only producer is `types/base.py:937-947` via `_build_annotations`); the contract is single-sourced and the consumer-side `snake_case` rebuild is documented in the docstring.

### `_PendingRelationAnnotationMeta` lacks an explicit `# noqa: D101` justification for the inline `__repr__` comment block at `relations.py:62-66`

The metaclass at `relations.py:59-72` carries a one-line class docstring at `:60` (`"""Metaclass that gives the sentinel a useful schema-construction error repr."""`) plus a five-line inline `# ...` audit-trail comment at `:62-66` explaining the rewrite contract. The audit-trail comment is correct and grep-stable, but its content (a full sentence-form claim about what `finalize_django_types()` rewrites, naming `resolved_relation_annotation` and `source_type.__annotations__`) duplicates the same explanation already given in the module docstring at `:7-13` AND in the `PendingRelationAnnotation` docstring at `:76-82`. Three physically separate prose-of-truth sites for the same rewrite rule is a brittleness signal — same calibration as the `optimizer/field_meta.py:62-76` vs `:140-152` prose-duplication Low recorded earlier. Defer until a fourth prose site for the rewrite rule lands (or until a fact in the comment block drifts vs the module docstring), at which point fold to one canonical home and `See docstring above` at the other sites. Today the three sites agreed at authoring; the drift risk is forward-looking.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is the canonical home for `PendingRelation` / `PendingRelationAnnotation`, with single-import boundaries at every consumer (`registry.py:30,49,323,328,341`, `types/base.py:45,938-948`, `types/finalizer.py:58,71,187,188,189`). The `__hash__ = object.__hash__` override at `relations.py:56` is the single-source-of-truth for the identity contract that `TypeRegistry.discard_pending` reads at `registry.py:341-352` (verified via `id(record)` set comprehension on the kwargs).
- **New helpers considered.** A shared `_pending_record_repr(record)` formatter was considered for use across `types/finalizer.py::_format_unresolved_targets_error` (`:71`) and the existing identity-stable repr on `PendingRelation` — rejected because `_format_unresolved_targets_error` produces a user-facing `ConfigurationError` message with a different shape from a debug repr, and the dataclass-default `__repr__` is sufficient for in-test inspection (`tests/types/test_relations.py:34-67` reads `hash(pending)` and `pending in {pending}` rather than the repr). A shared `_relation_kind_to_str(kind)` helper was considered for the docstring framing — rejected because `RelationKind` is already a `TypeAlias = Literal[...]` at `utils/relations.py:7-12` and string conversion is implicit.
- **Duplication risk in the current file.** Three docstring sites (`relations.py:7-13`, `:31-34`, `:76-82`) plus one inline comment block (`:62-66`) restate the producer / consumer / rewrite contract — flagged as a forward-looking Low; the agreement is current. The `__hash__ = object.__hash__` override at `:56` has a single inline justification comment (`# identity-based hash; django_field may be unhashable`) — single-sourced, no duplication risk.

### Other positives

- **Module shape.** 82 lines, two public symbols (`PendingRelation`, `PendingRelationAnnotation`), one private metaclass (`_PendingRelationAnnotationMeta`); shadow overview confirms 0 control-flow hotspots, 0 Django/ORM repeat markers, 0 calls-of-interest, 0 TODO comments, 0 repeated string literals. The module's purpose is single-responsibility (definition-order-independence scaffolding) and the file does that and only that.
- **Frozen dataclass + identity-hash contract.** The `@dataclass(frozen=True)` decorator at `:27` synthesizes value-based `__eq__` (so the test at `tests/test_registry.py:580-581` builds two distinct records from the same kwargs and the equality assertion holds), and the explicit `__hash__ = object.__hash__` at `:56` restores identity-based `__hash__` so `discard_pending`'s `{id(record) for record in resolved}` set comprehension at `registry.py:351` is the canonical removal predicate. The full pin lives at `tests/types/test_relations.py:34-67` (three tests covering hash-identity / equality / set-membership) plus `tests/test_registry.py:564-590` (`test_discard_pending_uses_identity_match_with_real_pending_relation`).
- **Sentinel repr metaclass.** The `_PendingRelationAnnotationMeta.__repr__` at `:68-72` returns `"<unfinalized DjangoType relation; call finalize_django_types() before constructing strawberry.Schema>"` — pinned by `tests/types/test_base.py:841` (`assert "finalize_django_types()" in repr(PendingRelationAnnotation)`). The metaclass is the right shape: it shapes the Strawberry-side `TypeError` consumer message that fires only when the rewrite was skipped (the unhappy path), without affecting the happy-path (where `finalize_django_types()` rewrites `source_type.__annotations__` before `strawberry.type` ever sees the class).
- **Snapshot fields documented as informational.** `nullable` and `relation_kind` at `:53-54` are documented at `:42-45` as "snapshot fields kept for self-contained record introspection; the production consumer reads the live `FieldMeta` from `DjangoTypeDefinition.field_map` instead" — the docstring correctly disowns the snapshot fields from the production read-path, which prevents a future regression where `PendingRelation`'s snapshot drifts from the live `FieldMeta` and a reader keys against the wrong source. Verified against `types/finalizer.py:209` which reads `definition.field_map[snake_case(pending.field_name)]` rather than `pending.nullable` / `pending.relation_kind`.
- **Imports.** Four imports — `from __future__ import annotations` (annotation forward-ref), `from dataclasses import dataclass`, `from django.db import models`, `from ..utils.relations import RelationKind`. No first-party imports of sibling `types/` modules — the file is at the bottom of the `types/` import DAG and consumed by `types/base.py:45` + `types/finalizer.py:58` + `registry.py:30` (TYPE_CHECKING). No circular-import risk.
- **GLOSSARY drift quick-check confirmation.** `PendingRelationAnnotation`, `PendingRelation`, `_PendingRelationAnnotationMeta` are all absent from `docs/GLOSSARY.md` — correct per the internal-mechanics convention recorded in earlier cycles (`optimizer/__init__.py:14-17` "internal implementation details" calibration applied uniformly across the optimizer + types subpackages). Consumer-visible behavior surfaces through `Definition-order independence` (`docs/GLOSSARY.md:231-257`) and `Relation handling` (`docs/GLOSSARY.md:888-926`); both entries are aligned with the module's role (definition-order-independence scaffolding for relation finalization). No in-cycle GLOSSARY edit warranted; the absence is intentional convention, not drift. Per dispatch, the GLOSSARY drift check on `PendingRelationAnnotation` and `Relation handling` is closed.
- **Test placement discipline.** The hash-contract pin lives at `tests/types/test_relations.py` (package-internal tree, system-under-test is the dataclass identity contract per `AGENTS.md` line 6) — the right tree because the identity contract is a Python-language property of `PendingRelation`, not an end-to-end GraphQL behavior reachable through a `/graphql` query. The complementary `tests/test_registry.py::test_discard_pending_uses_identity_match_with_real_pending_relation` at `tests/test_registry.py:564-590` exercises the same identity contract through the `discard_pending` consumer. No real-usage-rule miss.

### Summary

`django_strawberry_framework/types/relations.py` is a single-purpose 82-line scaffolding module hosting `PendingRelation` (frozen dataclass with explicit `object.__hash__` override for identity-based registry tracking) and `PendingRelationAnnotation` (sentinel annotation carrying a custom metaclass repr for friendly schema-construction error messages when `finalize_django_types()` was skipped). Zero High / zero Medium; four Lows are all forward-looking or comment-pass: (a) four cross-file references in module + class docstrings use single-colon `path:symbol` instead of `AGENTS.md` rule-27 `path::QualifiedName` (canonical shape already followed at `types/finalizer.py:196`); (b) module docstring's `spec-014 H1` citation correctly survives Step 8 archive sweeps as a rev-anchor but inherits the same drift-risk class as the optimizer-folder `spec-014 → spec-018` rotations; (c) `PendingRelation.field_name` snake_case-rebuild contract documented but not pinned in `tests/types/test_relations.py` — defer until second producer lands; (d) the producer-consumer-rewrite contract is duplicated across three docstring sites + one inline comment block — defer until a fourth restating site lands or until any of the three drifts. The shadow overview confirms zero control-flow hotspots / zero ORM markers / zero calls-of-interest / zero repeated literals. The GLOSSARY drift quick-check on `PendingRelationAnnotation` and `Relation handling` closes with no in-cycle edit warranted — internal-mechanics convention per the cross-cycle calibration. Standard three-spawn cycle; `Status: under-review`.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/types/relations.py` — Low #1 citation hygiene per AGENTS.md rule 27: rewrote four cross-file `path:symbol` references to `path::QualifiedName` form. Two sites in the module docstring (`types/base.py:_build_annotations` → `types/base.py::_build_annotations`; `types/finalizer.py:finalize_django_types` → `types/finalizer.py::finalize_django_types`) and the matching pair in the `PendingRelation` class docstring. Brings the file in line with the canonical shape already in use at `types/finalizer.py::_format_unresolved_targets_error #"types/base.py::_build_annotations"`.

### Tests added or updated

- None. Citation-hygiene comment-only change; no behavior surface to pin. Consistent with prior citation-hygiene Lows (`list_field.py` spec-016→spec-020, `optimizer/extension.py` spec-014→spec-018, `types/finalizer.py` 9× spec rotations) which all shipped without test surface.

### Validation run

- `uv run ruff format .` — pass (212 files unchanged)
- `uv run ruff check --fix .` — pass (All checks passed!)

### Notes for Worker 3

- Lows #2-4 deferred-with-trigger per dispatch and artifact prose:
  - Low #2 (`spec-014 H1` citation): correct against spec on disk; defer until a regression in the spec mapping fires or the next project-pass spec-NN sweep.
  - Low #3 (`field_name` snake_case rebuild contract not pinned in `tests/types/test_relations.py`): defer until (a) a regression surfaces consumer-side or (b) a third producer of `PendingRelation` lands; today the single producer is `types/base.py::_build_annotations`.
  - Low #4 (producer/consumer/rewrite prose duplicated across 3 docstring sites + 1 inline comment block): defer until a fourth restating site lands or any of the three drifts; today the three sites agree at authoring.
- No shadow file used during implementation; the edits are localized to 4 docstring lines.
- Concurrent maintainer activity per AGENTS.md #33: working tree carries unrelated modifications to `types/base.py`, `types/finalizer.py`, `docs/builder/bld-slice-3-wiring.md`, `docs/builder/build-028-orders-0_0_8.md`, `docs/review/review-0_0_7.md`, `tests/types/test_base.py`, plus untracked `docs/review/rev-types__finalizer.md`. Left untouched.
- `uv.lock` unchanged.

---

## Verification (Worker 3)

### Logic verification outcome

Terminal-verify on a consolidated single-spawn (shape #4) cycle. Worker 2 applied Low #1 verbatim per the artifact's four recommended replacements — four `path:Name` → `path::QualifiedName` swaps confirmed via `git diff -- django_strawberry_framework/types/relations.py`: two in the module docstring (`types/base.py:_build_annotations` → `types/base.py::_build_annotations` at `:7-8`; `types/finalizer.py:finalize_django_types` → `types/finalizer.py::finalize_django_types` at `:10-11`) and the matching pair in the `PendingRelation` class docstring at `:31-34`. Post-fix `grep -n "path:" relations.py` returns zero hits on the single-colon `path:symbol` form. Canonical shape at `types/finalizer.py:196` (`# Defense-in-depth: ``types/base.py::_build_annotations`` already skips the`) grep-confirmed in-repo. Lows #2-4 deferred-with-trigger per the artifact's own verbatim prose, pre-authorized by dispatch.

### DRY findings disposition

`None — …` DRY bullet at `relations.py:7` framing the 82-line module as the single canonical home for `PendingRelation` / `PendingRelationAnnotation` scaffolding with cross-folder consolidation already in place (producer at `types/base.py::_build_annotations`, consumer at `types/finalizer.py::finalize_django_types`). No in-cycle DRY action; deferral premise (single producer + single consumer) holds.

### Temp test verification

None used; the cycle is a citation-hygiene comment-only edit with no behavior surface to pin.

### Verification outcome

cycle accepted; verified

Concurrent maintainer activity per AGENTS.md #33 acknowledged in Worker 2's Notes-for-Worker-3 and confirmed via `git status` (modifications to `types/base.py`, `types/finalizer.py`, `docs/builder/bld-slice-3-wiring.md`, `docs/builder/build-028-orders-0_0_8.md`, `docs/review/review-0_0_7.md`, `tests/types/test_base.py`, plus untracked `docs/review/rev-types__finalizer.md`) — all left untouched, none overlap the four-line relations.py docstring edit. Changelog disposition `Not warranted` cites both AGENTS.md rule 21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization for this cycle; `git diff -- CHANGELOG.md` is empty as required. Ruff spot-verify on relations.py: `uv run ruff format --check` (1 file already formatted) + `uv run ruff check` (All checks passed!).

---

## Comment/docstring pass

(Consolidated single-spawn — Low #1 is the comment/docstring edit itself; Lows #2-4 are defer-with-trigger.)

### Files touched

- `django_strawberry_framework/types/relations.py` — see Fix report above. Four `path:symbol` → `path::QualifiedName` rewrites in module and class docstrings.

### Per-finding dispositions

- Low #1: applied verbatim per artifact's four recommended replacements; reads as canonical AGENTS.md rule 27 shape.
- Low #2: deferred-with-trigger (rev-anchor `spec-014 H1` citation is correct today; revisit if/when the optimizer-folder-style spec-NN sweep fires for `types/` or a regression surfaces).
- Low #3: deferred-with-trigger (defer until second `PendingRelation` producer lands or consumer-side regression appears).
- Low #4: deferred-with-trigger (defer until a fourth restating site lands or any of the three drifts; today the three docstring sites + inline-comment-block agree).

### Validation run

- `uv run ruff format .` — pass
- `uv run ruff check --fix .` — pass

### Notes for Worker 3

Lows #2-4 deferral triggers preserved verbatim from artifact prose; no in-cycle edit warranted on any of them.

---

## Changelog disposition

### State

Not warranted.

### Reason

Per AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization for this cycle. The in-cycle edit is citation-style hygiene on four docstring lines — no consumer-visible behavior change, no public-symbol surface change, no typed-error contract change. Calibration siblings (`list_field.py`, `optimizer/extension.py`, `optimizer/walker.py`, `types/finalizer.py` citation-rotation cycles) all closed `Not warranted` on the same shape.

### What was done

No `CHANGELOG.md` edit.

### Validation run

- `uv run ruff format .` — pass
- `uv run ruff check --fix .` — pass

---

## Iteration log
