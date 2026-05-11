# Review: `django_strawberry_framework/types/`

Folder-level pass. Scope covers `base.py`, `converters.py`, `definition.py`, `finalizer.py`, `relations.py`, `relay.py`, `resolvers.py`, and the subpackage `__init__.py`. Per-file artifacts under `docs/review/rev-types__*.md` were read first; this pass focuses on cross-file structure, repeated patterns, misplaced responsibilities, and the `__init__.py` re-export contract.

## High:

None.

## Medium:

### Recovery semantics for partial-failure are split across five files with no single owner

The "documented contract, not enforced" theme tracked across per-file artifacts now lands as a folder-wide structural issue. `registry.py` flagged `_finalized` as a documented-but-unenforced guard; `optimizer/plans.py` flagged `OptimizationPlan` mutation; `types/base.py` Medium #1 flagged the non-atomic `registry.register` + `register_definition` write pair; `types/definition.py` Medium #1 flagged the mutable `field_map` / `optimizer_hints` dicts; `types/finalizer.py` Medium #1 flagged Phase 2/3 non-atomicity where `definition.finalized = True` lands before `registry.mark_finalized()` and class-level annotation rewrites in Phase 1.5 happen before `registry.discard_pending` runs. Each per-file artifact recommended a local fix, but the correct resolution is a single recovery contract owned in one place. Two viable shapes: (a) `registry.clear()` is wired as the automatic recovery hook and `finalize_django_types` wraps Phases 1.5/2/3 in `try/except` that calls it and re-raises; (b) `DjangoTypeDefinition` becomes `frozen=True` with `MappingProxyType` dict slots and `definition.finalized` is collapsed into a registry-side state machine (`pending` → `attaching` → `finalized`) so the per-definition flag stops shadowing the registry-side flag. Either way the choice belongs in one artifact (this folder pass) and the per-file Mediums are sub-issues of it. Tests should pin: a Phase 3 raise on the Nth type leaves the registry in a state where `registry.clear()` + re-import produces a clean rebuild (today the leftover `definition.finalized=True` writes silently skip those types on the second pass).

```django_strawberry_framework/types/finalizer.py:60:88
    for pending, target_type in resolved:
        pending.source_type.__annotations__[pending.field_name] = resolved_relation_annotation(...)
        resolved_pending.append(pending)
    registry.discard_pending(resolved_pending)
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        _attach_relation_resolvers(...)
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        strawberry.type(type_cls, name=definition.name, description=definition.description)
        definition.finalized = True
    registry.mark_finalized()
```

### `_optimizer_field_map` / `_optimizer_hints` legacy mirrors are written here, read from `optimizer/`, and lack a single retirement anchor

`types/base.py:147-148` is the writer for the `_optimizer_field_map` / `_optimizer_hints` class-attribute mirrors that `optimizer/walker.py` and `optimizer/field_meta.py` read via `getattr` shape-guards. The optimizer-folder pass (worker memory 2026-05-10) flagged three differently-labelled mirror-retirement TODOs across the reader sites and asked the writer to carry the matching anchor. Today the writer in `types/base.py` has no TODO citing the retirement slice, so when the slice lands, a grep for the retirement spec will hit the reader sites but miss the writer. Either add a TODO at the writer naming the same retirement slice the optimizer-folder artifact identified, or — preferred — collapse the mirror entirely by reading `definition.field_map` / `definition.optimizer_hints` everywhere the optimizer currently reads `cls._optimizer_*`. The shape-guard asymmetry (`getattr(..., {}).get(...)` everywhere) exists precisely because the mirrors duplicate state that already lives on `DjangoTypeDefinition`; consolidating the read path eliminates an entire Medium class without a new abstraction.

```django_strawberry_framework/types/base.py:140:150
        registry.register(meta.model, cls)
        registry.register_definition(cls, definition)
        for pending_relation in pending:
            registry.add_pending_relation(pending_relation)

        cls._optimizer_field_map = field_map
        cls._optimizer_hints = optimizer_hints_dict
```

### `_validate_meta` / `_validate_optimizer_hints_against_selected_fields` / `_format_unresolved_targets_error` all own slices of consumer-visible `Meta.*` error messaging

`types/base.py` owns the `_format_unknown_fields_error` helper and three call sites for `Meta.fields` / `Meta.exclude` / `Meta.optimizer_hints` typo guards. `types/finalizer.py:14-28` owns `_format_unresolved_targets_error`, which names `Meta.exclude` / `Meta.fields` in its string. If consumer-surface `Meta` keys are renamed or supplemented (e.g., a future `Meta.optional_fields`), the rename has to be hunted across two files with different formatting conventions. Per `rev-types__base.md` Medium #3 the hint validation itself was already consolidated into one `_validate_optimizer_hints` helper — extending the same approach to "consumer-surface error strings live in one module" (or one `_errors.py`) would close the loop. Low-cost variant: add a one-line comment in `finalizer._format_unresolved_targets_error` pointing readers to `base._format_unknown_fields_error` as the sibling convention so the next rename touches both.

```django_strawberry_framework/types/finalizer.py:14:28
def _format_unresolved_targets_error(unresolved: list[PendingRelation]) -> str:
    ...
    return (
        ...
        "Declare a DjangoType for each unresolved target model, or exclude these "
        "relation fields via Meta.exclude / Meta.fields."
    )
```

### `attname` / relation-shape derivation is duplicated between `base.py`/`converters.py` and `resolvers.py`

`types/resolvers.py:167-173` re-derives forward-FK `attname` via `getattr(field, "attname", None)` and re-runs `relation_kind(field)` to dispatch the resolver branch. `types/base.py` already consumes `FieldMeta` for the same shape derivation, and `optimizer/field_meta.py` is documented as the single source of truth (worker memory 2026-05-10 field_meta entry). The resolver builder takes `field` from `model._meta.get_field(name)` directly and bypasses the `FieldMeta` already cached on `definition.field_map`. Wiring the resolver builder to consume `FieldMeta` rather than the raw Django field would eliminate the `getattr` shape-guard asymmetry flagged in `rev-types__resolvers.md` Low #2 and the parallel one in `rev-types__converters.md` Medium #3 (`resolved_relation_annotation`'s `getattr(field, "null", False)`). Folder-pass DRY candidate; deferral acceptable only if a comment names which side is the SSoT.

```django_strawberry_framework/types/resolvers.py:163:175
def _make_relation_resolver(field: models.Field, parent_type: type) -> Callable[..., Any]:
    field_name = field.name
    kind = relation_kind(field)
    ...
    attname = getattr(field, "attname", None)
```

## Low:

### `or {}` / `or ()` / `or []` / `set()` defensive-coerce posture is now seen in 7+ files

Carry-forward from per-file artifacts: `conf.py`, `optimizer/extension.py`, `optimizer/_context.py`, `optimizer/plans.py`, `optimizer/walker.py`, `types/base.py:255` (`_meta_optimizer_hints`), `types/converters.py:172` (`list(field.choices or [])`), and `types/resolvers.py:47-53` (now-fixed `_EMPTY_FROZENSET`). The package needs a single stance — strict (raise on misconfigured non-dict-non-None) or lenient (current). This is a project-pass decision but recording it folder-side because the types folder is where it bites consumers (`Meta.optimizer_hints = None` silently becomes `{}`). No source change here; deferred to `rev-django_strawberry_framework.md`.

```django_strawberry_framework/types/base.py:255:255
    return getattr(meta, "optimizer_hints", None) or {}
```

### Relay-interfaces TODO anchors total 14 occurrences across 6 files

Counts: `base.py` 5, `relay.py` 5, `finalizer.py` 1, `definition.py` 1, `resolvers.py` 1, `__init__.py` 1. All cite `docs/spec-relay_interfaces.md` with the same `TODO(0.0.5 relay interfaces; see <spec>)` prefix — consistent shape, which is what AGENTS.md asks for. Worth pinning a single checklist for the slice author so all 14 land in the same commit. Per the artifact for `types/relay.py`, the five named helpers (`install_is_type_of`, `apply_interfaces`, `implements_relay_node` / `install_relay_node_resolvers`, `_resolve_id_attr_default` / `_resolve_id_default`, sync/async `_resolve_node_default` / `_resolve_nodes_default`) must actually land in `relay.py` rather than be split into `base.py` / `finalizer.py`; the `__init__.py` TODO ("keep `types.relay` internal") is the contract enforcing that.

```django_strawberry_framework/types/__init__.py:19:20
# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# keep ``types.relay`` internal; do not re-export Relay helper functions.
```

### Three near-identical `for type_cls, definition in registry.iter_definitions()` loops in `finalizer.py` will become four once Phase 2.5 lands

Already flagged in `rev-types__finalizer.md` Low #1; surfacing at folder pass because the consolidation interacts with the Medium #1 recovery-contract decision above. If Phase 2/3 wrap in `try/except` for atomicity, the same wrap can host a single loop body that does resolver-attach + (future) interface-install + `strawberry.type(...)` per non-finalized definition. Defer until the relay slice lands.

```django_strawberry_framework/types/finalizer.py:68:88
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        _attach_relation_resolvers(...)
    # TODO(0.0.5 relay interfaces; ...)
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        strawberry.type(type_cls, name=definition.name, ...)
        definition.finalized = True
```

### `_record_pending_relation`'s reverse-O2O nullable rule belongs next to `relation_kind`

`types/base.py:459-468` inlines `nullable=kind == "reverse_one_to_one" or bool(getattr(field, "null", False))`. Per `rev-types__base.md` Low #5 this string-typed kind constant comparison belongs in `utils/relations.py` next to `relation_kind` so the two co-locate. The utils folder pass is the right place to land this; flagged here so the types folder pass artifact tracks the migration target.

```django_strawberry_framework/types/base.py:466:466
        nullable=kind == "reverse_one_to_one" or bool(getattr(field, "null", False)),
```

### `__init__.py` re-export contract is correct and tight; one note on the deferred surface

Confirmed via helper run on the subpackage `__init__.py`: only two re-exports (`DjangoType`, `finalize_django_types`), `__all__` matches, internal helpers (`convert_scalar`, `convert_relation`, `convert_choices_to_enum`, `_make_relation_resolver`, `_attach_relation_resolvers`, `PendingRelationAnnotation`, `PendingRelation`, `DjangoTypeDefinition`, `FieldMeta`, `OptimizerHint`) are reachable only via dotted-submodule paths. The docstring's dependency-direction promise ("optimizer subpackage must not import back from `types/`") is honoured — no `optimizer/` file imports from `types/` (verified by grep of all `optimizer/*.py` imports during the optimizer folder pass). Only finding: the `__init__.py` re-exports are minimal and reflect the alpha-posture deferral correctly, but `__all__` should grow with the relay slice (or the `__init__.py` TODO should be removed in the same change). Worth pinning to the relay TODO checklist.

```django_strawberry_framework/types/__init__.py:16:22
from .base import DjangoType
from .finalizer import finalize_django_types

# TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
# keep ``types.relay`` internal; do not re-export Relay helper functions.

__all__ = ("DjangoType", "finalize_django_types")
```

## What looks solid

- The helper `scripts/review_inspect.py` was run on every file in the folder including the `__init__.py`; overviews exist under `docs/review/shadow/` and informed the cross-file checks below.
- Import direction is one-way and clean across the subpackage: `relations.py` and `definition.py` are leaves (only depend on `..utils.relations`, `..optimizer.*`); `converters.py` depends on `..registry`, `..utils.*`, `.relations`; `resolvers.py` depends on `..optimizer.*` and `..utils.relations`; `base.py` depends on `..optimizer.*`, `..registry`, `..utils.*`, `.converters`, `.definition`, `.relations`; `finalizer.py` depends on `..registry`, `.converters`, `.relations`, `.resolvers`. No `types/` file imports from another `types/` file in a back-edge direction; no `types/` file imports from a future-slice stub (`relay.py` has no current importers, consistent with its stub status). The folder's `__init__.py` docstring claim about dependency direction is enforceable today.
- `PendingRelation` hashability contract is now documented from three sides: `registry.py:discard_pending` (the `set(resolved)` consumer), `relations.py` (the frozen-dataclass producer with the `__post_init__` hash probe), and `base.py:_record_pending_relation` (the construction site). The three-way pin is the right shape for a load-bearing invariant.
- Consumer-surface error string conventions are mostly centralised: `_format_unknown_fields_error` covers three call sites for `Meta.fields` / `Meta.exclude` / `Meta.optimizer_hints` typo guards (post-fix); `_format_unresolved_targets_error` covers the relation-resolution failure. The split is annotated in the artifact above; the shape is otherwise consistent.
- Comment story across the folder is coherent: the "Phase N" numbering used in `finalizer.py` docstrings matches the per-method `# B<N>:` markers being phased out elsewhere; the relay-interfaces TODO anchors all cite the same active spec; the `_consumer_assigned_*_fields` naming is mirrored consistently between `base.py` (collector) and `definition.py` (storage).
- No circular-import risk introduced by the per-file fixes already landed in the cycle (atomic registry pair, scalar-override handling, `_check_n1` cardinality split, `_EMPTY_FROZENSET` sentinel). Folder-pass import sweep matches the optimizer-folder-pass result: one-way dependencies, no back-edges.

---

## Verification

PASS — no-source-change folder cycle. Zero High. All four Mediums are consolidation issues whose artifact bodies explicitly route the resolution to (a) the project-level pass (`rev-django_strawberry_framework.md`) for ratification of the package-wide recovery contract, the `or {}` defensive-coerce stance, the `FieldMeta`-as-SSoT decision, and the runtime_path_*/resolver_key placement question; or (b) future slices already anchored in optimizer-folder-pass routing (mirror retirement for `_optimizer_field_map` / `_optimizer_hints`; relay-interfaces slice for the 14 TODO anchors and the finalizer triple-loop consolidation; utils folder pass for the reverse-O2O nullable rule). The summary text and the folder-pass body both name those forward destinations. Per Worker 3 memory calibration on no-source-change cycles (2026-05-11 optimizer folder pass; 2026-05-11 types/finalizer.py), a folder-pass cycle that bundles "retire legacy mirrors" + "non-atomic mutation" + "consumer-surface error string split" + "shape-SSoT" findings legitimately defers to a coordinated downstream slice when (a) zero High, (b) every Medium body explicitly names the project pass or the future slice as its right home, (c) findings are calibration of future-breakage rather than current bugs — all three conditions hold here. `uv run pytest tests/types tests/test_registry.py -q --no-cov` → 119 passed, 1 skipped.

### Summary:

Four Mediums, six Lows. The Mediums are all consolidation issues rather than new defects: (1) the package-wide "documented contract, not enforced" recovery-semantics question now spans registry + plans + base + definition + finalizer and needs a single owner — folder pass is the right place to take the decision but the project pass owns ratifying it; (2) the `_optimizer_*` legacy-mirror writer in `base.py` lacks the retirement TODO anchor that the optimizer-folder reader sites cite, and the right resolution is to drop the mirror entirely by having the optimizer read `DjangoTypeDefinition` directly; (3) consumer-surface `Meta.*` error strings split across `base.py` and `finalizer.py` need a sibling-comment or a shared `_errors.py`; (4) resolvers re-derive relation shape via `getattr` while the optimizer consumes `FieldMeta`, and the SSoT question raised by `optimizer/field_meta.py`'s carry-forward calibration now has a cross-folder caller. Lows are package-wide carry-forwards (`or {}` posture, relay-TODO inventory, triple-loop in finalizer, reverse-O2O nullable rule's home, `__init__.py` deferred-surface note). Project-pass forwards: ratify the recovery contract, ratify the `or {}` stance, confirm `FieldMeta` is the single shape SSoT across optimizer/types/resolvers, and confirm the `runtime_path_*` / `resolver_key` placement question (already raised by optimizer folder pass; resolvers.py is the cross-folder caller that reinforces it).
