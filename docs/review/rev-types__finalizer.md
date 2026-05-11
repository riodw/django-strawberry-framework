# Review: `django_strawberry_framework/types/finalizer.py`

## High:

None.

## Medium:

### Phase 2/3 are not failure-atomic despite docstring promising "Phase 1 is failure-atomic"

The module docstring on `finalize_django_types` acknowledges that Phase 2 resolver attachment and Phase 3 `strawberry.type(...)` mutate classes in place and that recovery requires `registry.clear()` and fresh class recreation. The contract is documented but not enforced: if `strawberry.type()` raises on the fifth of ten types, the first four are already mutated *and* marked `definition.finalized = True`, but `registry.mark_finalized()` has not yet been called. On retry, `is_finalized()` returns `False`, the loop re-enters, the first four are skipped via `if definition.finalized: continue`, and the fifth is retried — yet `__annotations__` for *every* pending source class has already been rewritten (Phase 1.5) and resolvers re-attached. A subsequent retry that succeeds will land in a half-decorated state where consumer code cannot tell whether finalization completed cleanly. Same calibration as the "documented contract, not enforced" theme tracked across `registry.py`, `optimizer/plans.py`, and `types/base.py`: raise here means silent state corruption. Recommend either (a) wrapping Phase 2+3 in try/except that calls `registry.clear()` and re-raises with a clear "registry left in unrecoverable state; re-import the package" message, or (b) explicitly documenting the per-type `definition.finalized` flag as the recovery anchor and asserting it on entry.

```django_strawberry_framework/types/finalizer.py:31:88
def finalize_django_types() -> None:
    ...
    Phase 1 is failure-atomic: unresolved-target detection completes before
    mutating any class object. Phase 2 resolver attachment and Phase 3
    ``strawberry.type(...)`` calls mutate classes in place; a Strawberry-side
    failure there requires ``registry.clear()`` and fresh class recreation.
    ...
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        strawberry.type(type_cls, name=definition.name, description=definition.description)
        definition.finalized = True

    registry.mark_finalized()
```

### Phase 1.5 annotation mutation precedes the unresolved-targets gate's failure-atomic promise on retries

`Phase 1` collects `unresolved`, `resolved`, and `consumer_authored` lists before raising. That part is genuinely atomic on first call. However, `pending.source_type.__annotations__[pending.field_name] = resolved_relation_annotation(...)` in the resolved loop mutates classes *before* `registry.discard_pending(resolved_pending)` runs, and there is no guard that an exception inside `resolved_relation_annotation` (which goes through `converters.py`'s reflective dispatch) leaves the partially-mutated annotation map in place while pending records remain undischarged. The docstring labels this as part of Phase 2 implicitly, but readers tracing "Phase 1 is failure-atomic" naturally read the annotation rewrite as Phase 1 because it precedes resolver attachment. Recommend either renumbering ("Phase 1: gate; Phase 1.5: annotations; Phase 2: resolvers; Phase 3: strawberry.type") in the docstring to match what already exists in the TODO comment at line 76 (which already says "Phase 2.5"), or moving the annotation write into the same loop as `_attach_relation_resolvers` to consolidate "mutating phase" boundaries.

```django_strawberry_framework/types/finalizer.py:56:66
    if unresolved:
        raise ConfigurationError(_format_unresolved_targets_error(unresolved))

    resolved_pending = [*consumer_authored]
    for pending, target_type in resolved:
        pending.source_type.__annotations__[pending.field_name] = resolved_relation_annotation(
            pending.django_field,
            target_type,
        )
        resolved_pending.append(pending)
    registry.discard_pending(resolved_pending)
```

## Low:

### Three near-identical `for type_cls, definition in registry.iter_definitions()` loops, two with the same `if definition.finalized: continue` skip

Phase 2 (lines 68-75) and Phase 3 (lines 82-86) walk `iter_definitions()` separately, both using the same `finalized` skip. The TODO at line 76 reserves a slot for a Phase 2.5 doing the same walk a third time. Once the relay-interfaces slice ships, that is three identical loops. Recommend collapsing into a single walk that performs resolver attach, (future) interface install, and `strawberry.type(...)` for each non-finalized definition; the loop body grows but the cross-cutting "what does Phase 2.5 add" question becomes one anchor instead of a TODO comment block. Defer until the relay slice lands to avoid speculative refactor.

```django_strawberry_framework/types/finalizer.py:68:86
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        _attach_relation_resolvers(...)
    # TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md): ...

    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        strawberry.type(type_cls, name=definition.name, description=definition.description)
        definition.finalized = True
```

### `_format_unresolved_targets_error` helper lives in this module but its message refers to "Meta.exclude / Meta.fields" consumer surface owned by `types/base.py`

The helper is colocated with its single caller, which is fine, but the error string names consumer-facing `Meta` knobs whose validation lives in `types/base.py:_validate_meta`. If `Meta.exclude`/`Meta.fields` are renamed or supplemented (e.g., `Meta.optional_fields`), this string drifts silently. Folder-pass candidate: confirm there's a single canonical site for consumer-surface error strings, or accept that error strings naming `Meta.*` are an exception worth annotating.

```django_strawberry_framework/types/finalizer.py:22:28
    return (
        "Cannot finalize Django types: the following relation targets are unresolved.\n"
        f"{body}\n\n"
        "Declare a DjangoType for each unresolved target model, or exclude these "
        "relation fields via Meta.exclude / Meta.fields."
    )
```

### TODO anchor for the relay-interfaces Phase 2.5 spans 5 comment lines without `noqa: ERA001`

AGENTS.md exempts "Pseudo:" sections inside spec TODO comments from ERA001 but recommends inline `noqa ERA001` suppression when needed. The block at lines 76-80 reads as imperative comment, not pseudo-code, so it is likely fine under ERA001 — but worth a folder-pass cross-check against the other 5 relay-interfaces TODO anchors flagged in `types/base.py` (worker-memory entry 2026-05-11) to confirm they all use the same comment shape and the linter is not silently allowlisting one form over another.

```django_strawberry_framework/types/finalizer.py:76:80
    # TODO(0.0.5 relay interfaces; see docs/spec-relay_interfaces.md):
    # insert Phase 2.5 here: apply ``definition.interfaces`` to
    # ``type_cls.__bases__``, surface incompatible interfaces as
    # ConfigurationError, reject composite-pk Relay nodes, and install Relay
    # ``resolve_*`` defaults before Strawberry decorates the class.
```

### Idempotency check via `registry.is_finalized()` and per-definition `if definition.finalized: continue` is doubly defensive

`registry.is_finalized()` short-circuits at the top of the function. The per-definition `finalized` check inside Phase 2/3 only fires if a caller bypassed `is_finalized` (impossible through documented surface) or if a prior call raised between the `definition.finalized = True` write and `registry.mark_finalized()`. The double guard exists because of the failure-atomicity gap flagged in Medium #1 above; if Medium #1 is resolved by wrapping Phase 2+3 in a try/except + `registry.clear()`, the per-definition flag becomes redundant. Track resolution together.

```django_strawberry_framework/types/finalizer.py:39:86
    if registry.is_finalized():
        return
    ...
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
```

## What looks solid

- Static helper run was mandatory (file is under `types/`); ran cleanly — control-flow hotspot of 58 lines / 11 branches in `finalize_django_types` is real but is the documented phase orchestrator, so per-branch named coverage is the right Medium framing rather than a complexity Low.
- Phase 1 collection genuinely is failure-atomic: `unresolved`, `resolved`, and `consumer_authored` are local lists, and the raise at line 57 fires before any class mutation. Splitting consumer-authored from auto-resolved is the right shape for the resolver-attach skip set.
- `registry.discard_pending` is identity-matched per `registry.py:185-196`, so the `resolved_pending = [*consumer_authored]` + appended `resolved` records is correct against `iter_pending_relations`' identity contract — no hashability assumption is introduced here.
- `_attach_relation_resolvers` is invoked with `skip_field_names=definition.consumer_assigned_relation_fields`, preserving the "consumer-assigned StrawberryField wins" contract from `types/base.py`.
- `definition.finalized` is the single per-definition writer site (confirmed by the only `= True` assignment in the codebase being on line 86) — matches the carry-forward question from `types/definition.py` worker-memory.

---

### Summary:

Two Mediums: documented-but-unenforced failure-atomicity for Phase 2/3 (consistent with the package-wide "documented contract, not enforced" theme tracked across registry/plans/base) and a related phase-numbering/ordering clarity issue around the annotation rewrite. Lows are mostly DRY / cosmetic and several should defer to the relay-interfaces slice rather than be fixed pre-emptively. No Highs. The file is a 58-line orchestrator that does its job cleanly; the open question is recovery semantics on partial failure, which is a registry/definition concern as much as a finalizer concern — flag for the types/ folder pass to take a package-wide stance with `types/base.py` Medium #1 (non-atomic register pair) and `types/definition.py` Medium #1 (mutable definition contract).

## Verification

PASS — no-source-change cycle. Zero Highs. Both Mediums (Phase 2/3 atomicity; Phase 1.5 annotation-mutation phase numbering) explicitly routed in artifact body to the types/ folder pass to take a package-wide stance alongside `types/base.py` Medium #1 (non-atomic register pair) and `types/definition.py` Medium #1 (mutable definition contract). All Lows carry "Defer until relay slice", "Folder-pass candidate", "worth a folder-pass cross-check", or "Track resolution together" framing — contract-sanctioned deferrals consistent with the no-source-change pattern previously accepted for `optimizer/plans.py` and the `optimizer/` folder pass. `git diff -- django_strawberry_framework/types/finalizer.py` is empty. `uv run pytest tests/types -q --no-cov` → 84 passed, 1 skipped.
