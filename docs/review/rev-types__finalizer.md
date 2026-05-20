# Review: `django_strawberry_framework/types/finalizer.py`

Status: verified

## DRY analysis

- **Existing patterns reused.** `_format_unresolved_targets_error` (`types/finalizer.py:21-42`) and `_format_ambiguity_error` (`types/finalizer.py:45-63`) are the file's two consumer-surface error formatters; both docstrings cross-reference each other and the sibling formatter `_format_unknown_fields_error` at `types/base.py:394-402`. Three formatters now form a documented family covering every Meta-driven finalize-time consumer error string — the carry-forward predicted in `worker-memory/worker-1.md` is satisfied with no fourth formatter drift. `_audit_primary_ambiguity` (`types/finalizer.py:66-88`) is the sole consumer of the registry's `models_with_multiple_types()` helper (`registry.py:248-254`), `primary_for(model)` (`registry.py:232-239`), and `types_for(model)` (`registry.py:241-246`); each of those public iterators exists specifically for the audit per the registry docstring. `finalize_django_types` reuses `registry.is_finalized()` / `mark_finalized()` (`registry.py:344-350`) as the once-only gate, `registry.iter_pending_relations` / `discard_pending` (`registry.py:321-342`) as the identity-matched drain, `resolved_relation_annotation` (`types/converters.py:312-324`) for the rewritten annotation, and the four-step Phase 2.5 helpers in `types/relay.py` (`apply_interfaces:86-113`, `implements_relay_node:41-51`, `_check_composite_pk_for_relay_node:116-148`, `install_relay_node_resolvers:448-473`). `consumer_authored_fields` is the four-corner override frozenset stored on `DjangoTypeDefinition` (`types/definition.py:54`) and built by `_consumer_assigned_fields` + the annotation walks at `types/base.py:170-187`; this finalizer consumes it at the pending-relation short-circuit. Test pinning lives at `tests/test_registry.py:1044-1118` (audit ordering vs `is_finalized()` short-circuit), `tests/types/test_definition_order.py:60-322` (pending-relation resolution across import orders), and `tests/types/test_relay_*` for Phase 2.5.
- **New helpers a fix might justify.** A `_iter_unfinalized_definitions()` generator on the registry (or a private helper in this module) would consolidate the three identical `for type_cls, definition in registry.iter_definitions(): if definition.finalized: continue` loops at `types/finalizer.py:137-144,146-160,162-166`. The triple iteration is intentional — Phase 2 (resolver attach), Phase 2.5 (interface/Relay), and Phase 3 (`strawberry.type`) must run in that order across ALL types, not phase-by-phase per type, because Phase 2.5's `apply_interfaces` mutates `__bases__` and Phase 3's `strawberry.type` requires that mutation visible across the type's siblings before any decoration runs. So the helper is the loop body, not the phase ordering. Low-priority polish; the three call sites are short and the `if definition.finalized: continue` guard is short enough that DRYing it would lose the "skip already-decorated types on partial-failure rerun" intent at the seam most likely to be edited. The other live candidate is threading `definition.field_map[snake_case(pending.field_name)]` through to `resolved_relation_annotation` (`types/finalizer.py:130-133`) — `resolved_relation_annotation` accepts `field_meta` but the finalizer passes `None` so `FieldMeta.from_django_field(field)` re-runs per pending record. Pre-computed `FieldMeta` already lives on `DjangoTypeDefinition.field_map`; threading it would save a redundant FieldMeta build per pending relation.
- **Duplication risk in the current file.** The three `for type_cls, definition in registry.iter_definitions():` loops at lines 137, 146, and 162 each repeat the `if definition.finalized: continue` guard verbatim — a near-copy DRY signal, but justified by phase ordering (see above). The two error formatters (`_format_unresolved_targets_error`, `_format_ambiguity_error`) share the "per-line indented bullets joined by `\n`" shape but differ on the per-line template (offender vs source/target/related triple) and the actionable-guidance trailer; the docstrings explicitly call this out so the "look like duplicates but aren't" risk is documented. No repeated string literals flagged by the static helper. `registry.get(pending.related_model)` at line 119 vs `registry.primary_for(model)` at line 83 are NOT duplicates — `get()` honours the single-type-no-primary path while `primary_for()` is strict (see `registry.py:185-204,232-239`); the audit must use the strict form and resolution must use the lenient form.

## High:

None.

## Medium:

### Phase 2.5 `apply_interfaces` runs AFTER Phase 2 `_attach_relation_resolvers`, so resolver-driven introspection inside an interface override is invisible to Phase 2

`finalize_django_types` attaches the framework relation resolvers at `types/finalizer.py:137-144` (Phase 2) BEFORE injecting the interface bases at `types/finalizer.py:146-160` (Phase 2.5). The docstring at `types/finalizer.py:99-104` explicitly orders Phase 2.5 "between Phase 2 and Phase 3" and justifies the ordering: `strawberry.type(...)` at Phase 3 needs to see the mutated bases. The trade-off is that Phase 2's `_attach_relation_resolvers` calls `setattr(cls, field.name, strawberry.field(resolver=resolver))` (`types/resolvers.py:261`) on the class BEFORE any interface base contributes its own attribute layout to the MRO. The framework resolvers are pure callables that read `parent_type=cls` and look up `registry.get_definition(parent_type)` at runtime, so the MRO at attach time does not affect runtime behavior — but if a Strawberry interface ever exposes a class-level `resolve_<field>` default that consumers would expect to win over the framework auto-resolver, the current ordering would let the framework `setattr` win because the interface's `__bases__` injection hasn't happened yet. Today no Strawberry interface (including `relay.Node`) exposes a same-named `resolve_<field>` default for an auto-mapped Django relation column, so this is a latent ordering risk, not a live bug. Recommended change: add an inline comment at `types/finalizer.py:137-144` explicitly documenting "Phase 2 runs BEFORE Phase 2.5; interface base injection cannot supersede framework resolvers attached here. If a future Strawberry interface exposes a same-named `resolve_<field>` default, swap the loop ordering and re-pin the test surface." Pinning test would assert that a consumer interface with a `resolve_items` classmethod still wins over the framework's auto-generated resolver — currently no such test exists.

```django_strawberry_framework/types/finalizer.py:137-160
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        _attach_relation_resolvers(
            type_cls,
            definition.selected_fields,
            skip_field_names=definition.consumer_assigned_relation_fields,
        )

    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        # ``apply_interfaces`` is the only step that depends on a non-empty
        # ``Meta.interfaces`` tuple. The Relay-node gate and resolver injection
        ...
        if definition.interfaces:
            apply_interfaces(type_cls, definition)
        if implements_relay_node(type_cls):
            _check_composite_pk_for_relay_node(type_cls)
            install_relay_node_resolvers(type_cls)
```

### `resolved_relation_annotation` rebuilds `FieldMeta` per pending relation when the pre-computed `FieldMeta` already lives on `definition.field_map`

`types/finalizer.py:130-133` calls `resolved_relation_annotation(pending.django_field, target_type)` without passing `field_meta=`. `resolved_relation_annotation` (`types/converters.py:312-324`) then falls back to `FieldMeta.from_django_field(field)` (line 319) for every pending relation. The pre-computed `FieldMeta` already exists on `DjangoTypeDefinition.field_map[snake_case(pending.field_name)]` — `types/base.py:168` constructs `field_map` exactly once per `DjangoType` subclass and the finalizer can reach it via `registry.get_definition(pending.source_type).field_map.get(snake_case(pending.field_name))`. Cost is small (one `FieldMeta` per pending relation), but the redundancy is what worker-memory's calibration calls "the asymmetric outlier" — `resolved_relation_annotation`'s `field_meta=None` keyword exists exactly for this thread-through, and the only production call site does not use it. Recommended change: at `types/finalizer.py:114` capture `source_definition = registry.get_definition(pending.source_type)` once per pending record (already needed at line 115 for the consumer-authored check), then pass `field_meta=source_definition.field_map[snake_case(pending.field_name)]` at the `resolved_relation_annotation` call. Adds one lookup (already there for consumer_authored) and removes one `FieldMeta` build per pending relation. Test pin: extend `tests/types/test_definition_order.py` to assert `FieldMeta.from_django_field` is NOT called during `finalize_django_types()` when `field_map` is populated (e.g. via `monkeypatch.setattr` counting calls). Low risk; behavior identical.

```django_strawberry_framework/types/finalizer.py:111-135
    unresolved: list[PendingRelation] = []
    resolved: list[tuple[PendingRelation, type]] = []
    consumer_authored: list[PendingRelation] = []
    for pending in registry.iter_pending_relations():
        definition = registry.get_definition(pending.source_type)
        if definition is not None and pending.field_name in definition.consumer_authored_fields:
            consumer_authored.append(pending)
            continue
        target_type = registry.get(pending.related_model)
        ...
    resolved_pending = [*consumer_authored]
    for pending, target_type in resolved:
        pending.source_type.__annotations__[pending.field_name] = resolved_relation_annotation(
            pending.django_field,
            target_type,
        )
        resolved_pending.append(pending)
    registry.discard_pending(resolved_pending)
```

### Partial-failure rerun has no documented contract for half-decorated classes; the `definition.finalized` per-entry guard is the only safety net

The docstring at `types/finalizer.py:91-105` claims Phase 1 is failure-atomic and warns that "a Strawberry-side failure [in Phase 2/3] requires `registry.clear()` and fresh class recreation." But the implementation is more forgiving than that prose: at lines 138, 147, and 163 the per-entry `if definition.finalized: continue` guard means a rerun would skip already-decorated types and attempt the rest. `registry.is_finalized()` is NOT set at the top until line 168, so a Phase 3 failure mid-iteration leaves the registry not-finalized; the next `finalize_django_types()` call would re-run Phase 1 (now potentially with the previously-unresolved targets resolved), re-run the audit, drain pending again (no-op — already drained), and re-loop Phase 2/2.5/3 skipping the already-finalized entries via the per-entry guard. That is a useful partial-recovery path that the docstring does NOT describe — and it's at odds with the "must registry.clear() and recreate" guidance. Worse, Phase 2's `_attach_relation_resolvers` and Phase 2.5's `apply_interfaces` are NOT idempotent on a class whose `definition.finalized` is False but whose attributes/bases were already mutated by a partial-failure prior pass (a Phase 3 failure would have run Phase 2 + 2.5 first). A rerun would re-attach resolvers (`setattr` overwriting the previous Strawberry-decorated field, generally fine) and re-mutate `__bases__` (`apply_interfaces` already filters via `if iface not in type_cls.__mro__`, so safe). So the implementation IS rerun-safe at fine granularity, but the docstring's "must clear()" instruction would push consumers to wipe state they don't have to. Recommended change: rewrite the docstring contract — either tighten the implementation to roll back Phase 2/2.5 mutations on a Phase 3 raise (heavy; not justified by current consumer surface), OR loosen the docstring to "if `strawberry.type` raises mid-iteration, the call is partially-applied; calling `finalize_django_types()` again is safe and resumes from the failing entry. `registry.clear()` is the recommended path only if the consumer cannot fix the offending type." Pair with a test in `tests/types/test_definition_order.py` that monkey-patches `strawberry.type` to raise on the third type and asserts a second `finalize_django_types()` completes the remaining entries.

```django_strawberry_framework/types/finalizer.py:91-105
def finalize_django_types() -> None:
    """Resolve pending relations, attach resolvers, and finalize collected types.

    Phase 1 is failure-atomic: unresolved-target detection completes before
    mutating any class object. Phase 2 resolver attachment and Phase 3
    ``strawberry.type(...)`` calls mutate classes in place; a Strawberry-side
    failure there requires ``registry.clear()`` and fresh class recreation.
    ...
    """
```

## Low:

### `mark_finalized()` runs after Phase 3 only on success; the docstring does not state where in the lifecycle finalization is recorded

`registry.mark_finalized()` (`types/finalizer.py:168`) is the last statement; a Phase 2/2.5/3 raise skips it, leaving the registry in the partial-success state described in the Medium finding above. The docstring at `types/finalizer.py:91-105` documents Phase 1 atomicity but never says "the registry is marked finalized only after every type's Phase 3 call returns." Consumers reading the docstring might assume `is_finalized()` flips on entry (it does not — that's the `if registry.is_finalized(): return` at line 106 reading the prior call's flag), or on Phase 1 success, or any time before line 168. Recommended change: add one sentence to the docstring — "The registry's finalized flag flips only after every collected type has been decorated via `strawberry.type`; a Phase 2/2.5/3 raise leaves the flag False and supports the partial-recovery rerun described above." Combines with the Medium docstring rewrite.

```django_strawberry_framework/types/finalizer.py:162-168
    for type_cls, definition in registry.iter_definitions():
        if definition.finalized:
            continue
        strawberry.type(type_cls, name=definition.name, description=definition.description)
        definition.finalized = True

    registry.mark_finalized()
```

### `consumer_authored` short-circuit at line 116-118 is silent: the pending record is moved to `resolved_pending` without any annotation rewrite, with no logging or audit hook

When a consumer authors their own annotation on a relation field (`items: list["AdminItemType"]`), the collection pipeline at `types/base.py:170-187` records the name in `consumer_annotated_relation_fields` (which feeds `consumer_authored_fields`) AND `types/base.py:790-791` skips the `PendingRelation` append entirely. So a `PendingRelation` shouldn't reach the finalizer for a consumer-annotated relation in the first place. The line 116-118 short-circuit is therefore a defense-in-depth branch — but the comment `consumer_authored.append(pending)` is silent about that. If `_build_annotations` is ever changed to NOT skip pending append for consumer-annotated relations (e.g. for the future spec that wires lazy/forward-reference interface lookup), this branch becomes load-bearing for not double-mutating `__annotations__`. Recommended change: add a one-sentence comment at line 116 calling out that the branch is currently defense-in-depth (no production reachable path), and naming `types/base.py:790-791` as the primary skip. Low risk; documentation only.

```django_strawberry_framework/types/finalizer.py:114-118
    for pending in registry.iter_pending_relations():
        definition = registry.get_definition(pending.source_type)
        if definition is not None and pending.field_name in definition.consumer_authored_fields:
            consumer_authored.append(pending)
            continue
```

### `definition is not None` guard on line 116 is dead given the documented `register_with_definition` contract

`registry.get_definition(pending.source_type)` returns `None` only when `register_definition` was never called for `pending.source_type`. Pending relations are added via `registry.add_pending_relation(...)` at `types/base.py:243` AFTER `registry.register_with_definition` at `types/base.py:241` — the same `__init_subclass__` call. So `registry.get_definition(pending.source_type)` is guaranteed non-None for any pending record that reaches the finalizer. The `if definition is not None and ...` guard at line 116 is dead under the documented production call graph. Recommended change: either drop the `None` check (with a brief `# definition is always set; see types/base.py register_with_definition ordering` comment), or keep it as defense-in-depth with that same comment. Either way the implicit contract should be made explicit.

```django_strawberry_framework/types/finalizer.py:114-118
    for pending in registry.iter_pending_relations():
        definition = registry.get_definition(pending.source_type)
        if definition is not None and pending.field_name in definition.consumer_authored_fields:
            consumer_authored.append(pending)
            continue
```

### `resolved` / `consumer_authored` / `unresolved` lists are allocated even when `iter_pending_relations()` is empty

The three lists at lines 111-113 are eagerly allocated even for the common case where no relations are pending (single-type-per-model with all targets resolved at collection time). Pure allocation cost (three empty lists per call), so this is a Low cosmetic. The `if unresolved:` guard at line 125 already short-circuits when nothing was unresolved, and the `for pending, target_type in resolved:` loop at line 129 short-circuits when nothing was resolved. The `discard_pending(resolved_pending)` call at line 135 always runs; `discard_pending` is a no-op when its iterable is empty so this is fine. Recommended change: none required. Listed here only because the three-list allocation pattern reads as more bookkeeping than the function needs; a future maintainer might be tempted to consolidate into a `pending_classifier` dataclass with three frozensets. Defer.

```django_strawberry_framework/types/finalizer.py:111-113
    unresolved: list[PendingRelation] = []
    resolved: list[tuple[PendingRelation, type]] = []
    consumer_authored: list[PendingRelation] = []
```

### Module docstring at line 1 is one line; the file's lifecycle contract (Phase 1/2/2.5/3 ordering, single-call once-only, partial-failure recovery) deserves a module-level summary mirroring `types/relay.py`'s introduction

`types/relay.py:1-21` opens with a multi-paragraph module docstring that names every helper and the lifecycle phase it runs in. `types/finalizer.py:1` is a single line. The module owns the once-only build gate and is the primary public consumer surface (re-exported at `django_strawberry_framework/__init__.py:23`), so a richer module docstring would match the relay sibling's discipline. Recommended change: expand the module docstring to a short paragraph naming the four phases, the once-only gate, and the failure-recovery posture. Comment-pass work; defer until logic findings are accepted.

```django_strawberry_framework/types/finalizer.py:1
"""Finalization lifecycle for collected ``DjangoType`` classes."""
```

## What looks solid

- Static helper ran cleanly: 168 lines, 4 symbols, one control-flow hotspot (`finalize_django_types` at 78 lines / 15 branch nodes — Medium-tier "branchy" attention applied above, but the branches map directly to the four documented phases and the per-phase `if definition.finalized: continue` guard is the only structural duplicate).
- The `_audit_primary_ambiguity` audit ordering — runs AFTER the `registry.is_finalized()` short-circuit (line 106) and BEFORE pending-relation resolution (line 111) — is explicitly test-pinned by `tests/test_registry.py:1097-1118` (`test_audit_runs_only_when_not_finalized`), which asserts a second `finalize_django_types()` call hits the `is_finalized()` guard without re-running the audit. The docstring at lines 77-79 names the pinning spec line; the carry-forward from `types/converters.py` (Worker 1 memory) about the `_audit_primary_ambiguity` location is satisfied.
- Failure-atomicity at Phase 1: the `if unresolved: raise ConfigurationError(...)` at line 125 fires BEFORE any `__annotations__` rewrite (lines 130-133) or `registry.discard_pending` (line 135), so a finalize() that detects unresolved targets leaves every class object un-mutated and the pending list intact. Consumers can declare the missing types and re-call `finalize_django_types()`.
- The sentinel discipline pattern flagged in `worker-memory/worker-1.md` (hints.py SKIP, _context.py _MISSING, plans.py finalize tuple-swap) appears here as the `definition.finalized` per-entry boolean acting as a per-class rerun gate. Worker 0 / sibling artifacts have called out the dataclass surface concern (`rev-types__definition.md` Medium about `finalized: bool = False` being the only mutable flag on a frozen-otherwise dataclass) but inside this module, the flag is consumed correctly: it gates each of the three phase loops at lines 137-138, 146-147, 162-163 and flips exactly once per entry at line 166.
- The three sibling error formatters are now documented as a family — `_format_unresolved_targets_error` (`types/finalizer.py:21-29`), `_format_ambiguity_error` (`types/finalizer.py:45-55`), and `_format_unknown_fields_error` (`types/base.py:394-402`) — each docstring naming the others. The "look like duplicates but aren't" risk worker-memory flagged is closed with documentation.
- `apply_interfaces` (called at line 157) and `install_relay_node_resolvers` (called at line 160) are MRO-aware: `apply_interfaces` filters via `iface not in type_cls.__mro__` (`types/relay.py:101`) so direct `class Foo(DjangoType, relay.Node)` consumers don't double-inject; `install_relay_node_resolvers` uses the `__func__` identity test (`types/relay.py:472`) so a consumer override on `resolve_id` is preserved. Both contracts are pinned in `types/relay.py`'s test surface.
- `implements_relay_node(type_cls)` at line 158 is correctly checked AFTER `apply_interfaces` has potentially mutated `__bases__`, so a type that gains `relay.Node` only through `Meta.interfaces = (relay.Node,)` (no direct subclass) is correctly detected and routed through the composite-pk gate and resolver injection. This was the H1 fix referenced in `types/base.py`'s relay shape predicate.

### Summary

`types/finalizer.py` is the once-only build gate for the package's `DjangoType` registry and is correctly atomic at Phase 1 — unresolved-target detection and the primary-ambiguity audit complete before any class-object mutation, so a finalize() that detects a config error leaves classes intact for re-call. Three Mediums cluster around the post-Phase-1 behavior: (M1) Phase 2 resolver-attach runs before Phase 2.5 interface injection, a latent ordering risk if a future Strawberry interface ever exposes a same-named `resolve_<field>` default the framework would shadow; (M2) `resolved_relation_annotation` is called without the pre-computed `FieldMeta` already living on `definition.field_map`, so `FieldMeta.from_django_field` runs redundantly per pending relation; (M3) the docstring's "registry.clear() and fresh class recreation" partial-failure guidance is stricter than the implementation, which actually supports a fine-grained rerun via the `definition.finalized` per-entry gate. Five Lows are documentation polish — `mark_finalized()` lifecycle wording, defense-in-depth comments on the `consumer_authored` and `definition is not None` branches, the three eagerly-allocated lists, and a one-line module docstring that should grow. The audit ordering is well-pinned, the failure-atomic Phase 1 is well-pinned, and the three sibling error formatters now form a documented family.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/types/finalizer.py` — M2 logic refactor: thread the pre-computed `FieldMeta` from `definition.field_map` through to `resolved_relation_annotation` via the new `field_meta=` kwarg, removing the per-pending-relation `FieldMeta.from_django_field` rebuild. The classify loop now captures `field_meta = definition.field_map[snake_case(pending.field_name)]` alongside `(pending, target_type)`, and the resolved loop unpacks the triple and forwards `field_meta=` into the converter. L3 partial: kept the `if definition is not None` guard at line 116 and added an inline comment naming the producer ordering (`register_with_definition` then `add_pending_relation` in the same `__init_subclass__` call). Added two imports: `..optimizer.field_meta.FieldMeta` (for the resolved-tuple type annotation) and `..utils.strings.snake_case` (for the `field_map` key lookup, matching the construction site at `types/base.py:168`).

### Tests added or updated

- None. M2 is a behavior-preserving refactor (identical `FieldMeta` produced, just sourced from `field_map` instead of rebuilt from the field); L3 is a comment-only annotation of an existing defense-in-depth guard. Per the artifact's M2 recommended-test note ("extend `tests/types/test_definition_order.py` to assert `FieldMeta.from_django_field` is NOT called during `finalize_django_types()` when `field_map` is populated"), the prompt explicitly skips the optimization-counting test as nice-to-have but not required for a refactor with no observable behavior change.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).
- `uv run pytest tests/types/ -x` — pass (239 passed, 2 skipped; coverage gate fails as expected for a focused-tests run, not the full sweep). Note: the prompt's `tests/test_django_types.py` path does not exist on disk; ran `tests/types/` only.

### Notes for Worker 3

- M1, M3, L1, L2, L5 are intentionally deferred to the comment pass per the prompt's "Deferred items" section (M1 inline-comment polish, M3 docstring rewrite, L1/L2/L5 documentation polish).
- L4 is explicitly "no required change" per the artifact text ("Recommended change: none required.") and was not touched.
- L3 chose the "keep guard + add comment" option per the prompt's explicit instruction ("Choose the simpler path: keep the guard, add the comment"). The producer-ordering reference points at `types/base.py:241-243` (`register_with_definition` then `add_pending_relation` in the same `__init_subclass__` call).
- No optimization-counting test added for M2 per the prompt's skip-with-rationale directive. Rationale: identical `FieldMeta` produced before/after; behavior change is purely "where the FieldMeta came from" — counts are an implementation-detail assertion, not a contract.
- No shadow file was used during the fix.

---

## Verification (Worker 3)

### Logic verification outcome

- **M2 accepted.** Diff threads pre-computed `FieldMeta` from `definition.field_map[snake_case(pending.field_name)]` through to `resolved_relation_annotation` via the `field_meta=` kwarg. Confirmed: (a) the `snake_case` lookup matches the `field_map` construction site at `types/base.py:168` (`{snake_case(f.name): FieldMeta.from_django_field(f) for f in fields}`); (b) `resolved_relation_annotation`'s signature at `types/converters.py:312-319` accepts the `field_meta=` kwarg and uses `field_meta or FieldMeta.from_django_field(field)`, so an equivalent `FieldMeta` is now sourced from `field_map` instead of rebuilt per pending relation; (c) the `resolved` tuple shape widened from 2-tuple to 3-tuple consistently between producer and consumer loops; (d) the two new imports (`FieldMeta` from `..optimizer.field_meta`; `snake_case` from `..utils.strings`) match the canonical sources used elsewhere in the package; (e) no other observable behavior changed.
- **L3 accepted.** Brief comment landed at lines 117-120 near the `definition is not None` guard naming the producer ordering (`register_with_definition` then `add_pending_relation` in the same `__init_subclass__` call, citing `types/base.py`) and explicitly framing the guard as kept-as-defense-in-depth. Matches the artifact's "keep guard + add comment" option exactly.
- **M1, M3, L1, L2, L5 deferred to comment pass** per the artifact's Fix-report notes — all are documentation/comment polish that the comment pass owns. Accepted as deferred.
- **L4 deferred** — artifact text reads "Recommended change: none required."; intentional no-op.

### DRY findings disposition

- The "asymmetric outlier" DRY callout from `## DRY analysis` (`resolved_relation_annotation` rebuilding `FieldMeta` when `definition.field_map` already holds it) is now closed by the M2 fix: the production call site forwards the pre-computed `FieldMeta` via `field_meta=`, exercising the keyword the converter exposes for exactly this thread-through.
- Other DRY items (the three eagerly-allocated lists at lines 111-113; the three `if definition.finalized: continue` guards across phase loops) remain deferred per the artifact's "justified by phase ordering" prose — no in-cycle action required.

### Temp test verification

- None. M2 is a behavior-preserving refactor (identical `FieldMeta` produced from `field_map` versus rebuilt via `FieldMeta.from_django_field(field)`); L3 is a comment-only annotation. No temp tests written.

### Validation

- `uv run pytest tests/types/ -x` — 239 passed, 2 skipped (coverage gate fails as expected for a focused-tests run; this is the standard behavior for non-full sweeps). `tests/test_django_types.py` does not exist on disk (path was in the prompt; Worker 2 also noted this); `tests/types/` is the correct in-package test path.

### Verification outcome

`logic accepted; awaiting comment pass`

---

## Comment/docstring pass

### Files touched

- `django_strawberry_framework/types/finalizer.py` — five comment/docstring edits:
  - **L5 — module docstring expanded.** Replaced the single-line module docstring at line 1 with a multi-paragraph summary modeled on `types/relay.py:1-21`. Names the four phases (Phase 1 failure-atomic relation classification + `_audit_primary_ambiguity`; Phase 2 `_attach_relation_resolvers`; Phase 2.5 `apply_interfaces` + relay-node injection; Phase 3 `strawberry.type(...)`), the once-only entry-guard via `registry.is_finalized()`, the failure-recovery posture (failure-atomic Phase 1, mid-iteration Phase 2/2.5/3 raise leaves the registry not-finalized and supports partial recovery on rerun), and that `registry.clear()` remains the recommended escape hatch only when the offending type cannot be fixed in place. Lines ≤110.
  - **M3 — partial-failure contract rewritten.** Rewrote the `finalize_django_types` docstring (originally at lines 91-105) to match the implementation's per-entry `if definition.finalized: continue` rerun safety. New body documents: (a) Phase 1 atomicity covers both `_audit_primary_ambiguity` and the unresolved-target detection; (b) Phase 2/2.5/3 ordering and the rationale (decorator sees mutated bases); (c) partial-failure recovery — if `strawberry.type` (or any earlier Phase 2/2.5 step) raises mid-iteration, calling `finalize_django_types()` again is safe and resumes from the failing entry via the per-entry `definition.finalized` guard, and `apply_interfaces` re-mutating `__bases__` is a no-op via its `iface not in type_cls.__mro__` filter; (d) `registry.clear()` is recommended only when the consumer cannot fix the offending type in place. Acknowledges Phase 1 failure-atomicity and the once-only entry-guard.
  - **L1 — `mark_finalized()` lifecycle sentence.** Folded into the rewritten function docstring as a dedicated "Lifecycle of the finalized flag" paragraph: states explicitly that `registry.mark_finalized()` runs as the last statement and only on Phase 3 success, so `is_finalized()` flips ONLY after every collected type has been decorated.
  - **M1 — Phase 2/2.5 ordering inline comment.** Added a six-line comment immediately above the Phase 2 loop documenting that Phase 2 runs BEFORE Phase 2.5, that interface base injection cannot supersede framework resolvers attached here, and that no Strawberry interface currently exposes a same-named `resolve_<field>` default for an auto-mapped Django relation. Closes with the trigger condition for a future swap (Strawberry interface introduces such a default → swap loop ordering and pin consumer-interface-wins behavior in tests).
  - **L2 — `consumer_authored` defense-in-depth comment.** Added a six-line comment immediately above the `if definition is not None and pending.field_name in definition.consumer_authored_fields:` check naming `types/base.py:790-791` as the primary skip that already prevents the pending append, and explaining the branch is kept so a future change to `_build_annotations` (e.g. a lazy/forward-reference path that does append a pending record) cannot double-mutate `__annotations__` here. Distinct from the existing line-117-120 comment that names the producer ordering for the `is not None` guard.

Skipped per prompt: the M3 partial-recovery rerun test in `tests/types/test_definition_order.py` was deferred — Worker 1 framed it as a defensive-recovery test rather than a behavior-pinning need, and the prompt explicitly defers it to a future cycle.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).

### Notes for Worker 3

- All five comment-pass edits land in `django_strawberry_framework/types/finalizer.py` only. No source-logic changes; no test changes.
- The module docstring deliberately mirrors the `types/relay.py:1-21` shape (lifecycle-phase enumeration + cross-references to the relevant helpers) per Worker 1's L5 recommendation.
- The rewritten `finalize_django_types` docstring preserves the `registry.clear()` recommendation as the escape-hatch path, just loosened from "required" to "recommended only when the consumer cannot fix the offending type in place." Safety contract is intact.
- M1's inline ordering comment includes the explicit trigger condition (a future Strawberry interface introducing a same-named `resolve_<field>` default) so the next maintainer reading the loop knows exactly when to revisit.
- L2's defense-in-depth comment cites the precise upstream skip site (`types/base.py:790-791`) so the contract between `_build_annotations` and the finalizer stays grep-stable.
- No shadow file was used.

---

## Changelog disposition

- **Warranted?** Not warranted.
- **Reason:** the cycle is an internal refactor plus documentation polish. M2 (the only logic change) threads pre-computed `FieldMeta` from `definition.field_map` through to `resolved_relation_annotation` — performance-neutral / behavior-preserving (identical `FieldMeta` produced, just sourced from `field_map` instead of rebuilt per pending relation). L3 is a defense-in-depth comment annotating an existing guard. M1, M3, L1, L2, L5 are all docstring or comment polish describing already-shipped behavior. No public API change, no observable behavior change, no consumer-visible wire format, error message, or contract shift.
- **What was done:** no `CHANGELOG.md` edit. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active review plan's silence on authorizing changelog edits for this cycle, the disposition is recorded here and no edit is made.
- **Validation:** `uv run ruff format .` — pass; `uv run ruff check --fix .` — pass.

---

## Verification (Worker 3, pass 2)

- **Comment outcome:** M1 + M3 + L1 + L2 + L5 accepted; L4 deferred per artifact.
  - L5 module docstring expansion verified: opens with a multi-paragraph summary naming all four phases (Phase 1 failure-atomic relation classification with `_audit_primary_ambiguity`, Phase 2 `_attach_relation_resolvers`, Phase 2.5 `apply_interfaces` + Relay-node injection, Phase 3 `strawberry.type(...)`), the once-only entry-guard via `registry.is_finalized()` (line 108 cited), and the failure-recovery posture (per-entry `if definition.finalized: continue` guards skip already-decorated types on rerun; `registry.clear()` only when offending type cannot be fixed in place).
  - M3 rewritten function docstring verified: no longer claims `registry.clear()` is the only path on partial failure; explicitly documents partial-failure recovery via the per-entry `definition.finalized` guard and that `apply_interfaces` re-mutating `__bases__` is a no-op because of its `iface not in type_cls.__mro__` filter. `registry.clear()` is now framed as the recommended path "only when the consumer cannot fix the offending type in place" — exactly the loosened wording the artifact's Medium recommended.
  - L1 `mark_finalized()` lifecycle sentence verified: present as a dedicated "Lifecycle of the finalized flag" paragraph at the end of the function docstring, stating `registry.mark_finalized()` runs as the last statement of this function and only on Phase 3 success, so `is_finalized()` flips ONLY after every collected type has been decorated.
  - M1 Phase 2/2.5 ordering inline comment verified: six-line comment immediately above the Phase 2 loop (lines 208-214) documents the ordering, the no-current-conflict status, the latent-risk framing, and the swap-loop-and-pin-test trigger condition.
  - L2 consumer_authored defense-in-depth comment verified: six-line comment (lines 179-184) cites `types/base.py:790-791` as the primary skip site that prevents the pending append, and explains the branch is kept so a future `_build_annotations` change cannot double-mutate `__annotations__` here. Distinct from the existing L3 comment at lines 174-177 which names producer ordering for the `is not None` guard.
- **Changelog outcome:** not warranted accepted. `git diff -- CHANGELOG.md` is empty. Rationale cites both `AGENTS.md`'s "do not update CHANGELOG.md unless explicitly instructed" rule and the active plan's lack of authorization. Both ruff commands recorded (`uv run ruff format .` pass; `uv run ruff check --fix .` pass).
- **Verification outcome:** `cycle accepted; verified`.
