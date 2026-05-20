# Review: `django_strawberry_framework/optimizer/field_meta.py`

Status: verified

<!-- Worker 3 accepted the combined comment + changelog pass; cycle closed. -->

## DRY analysis

- Replace the hard-coded `{"many", "reverse_many_to_one"}` membership set at `optimizer/field_meta.py:116` with a call to the existing `is_many_side_relation_kind` helper at `utils/relations.py:68-70` (which already wraps the canonical `MANY_SIDE_RELATION_KINDS` frozenset at `utils/relations.py:14-19`). Single literal site today.

## High:

None.

## Medium:

### `is_many_side` duplicates the canonical many-side set literal

`FieldMeta.is_many_side` at `optimizer/field_meta.py:114-116` checks membership against an inline `{"many", "reverse_many_to_one"}` set. The package already exports a canonical frozenset `MANY_SIDE_RELATION_KINDS` and a helper `is_many_side_relation_kind(kind)` in `utils/relations.py:14-19,68-70`, and the optimizer walker uses that helper at `optimizer/walker.py:74`. The inline literal here is the third copy of the same membership rule and is the duplication risk: if a fifth relation kind ever joins the many-side set (e.g., a future reverse-M2M variant gets a distinct label), this site must be updated separately from the canonical frozenset, and `RelationKind` is a closed `Literal` so the typing layer will not catch the drift. This is a redundant implementation that should be consolidated.

Recommendation: call `is_many_side_relation_kind(self.relation_kind)` from `utils.relations` (already imported transitively — the module already imports from `utils.relations`). The change is one line in `is_many_side` and one extra symbol on the existing import. The test surface in `tests/optimizer/test_field_meta.py` already pins both branches indirectly via `nullable` short-circuits on reverse FK / reverse M2M; an explicit `is_many_side` test would be a Low add for the fix.

```django_strawberry_framework/optimizer/field_meta.py:113:116
    @property
    def is_many_side(self) -> bool:
        """Return whether this relation resolves as a GraphQL list."""
        return self.relation_kind in {"many", "reverse_many_to_one"}
```

## Low:

### `@runtime_checkable` on `_DjangoFieldLike` is unused

`_DjangoFieldLike` at `optimizer/field_meta.py:32-46` is decorated `@runtime_checkable`, but the protocol is only used as a static type annotation on `from_django_field`'s `field` parameter (`optimizer/field_meta.py:119`). No `isinstance(field, _DjangoFieldLike)` check exists anywhere in the package (grep over `django_strawberry_framework/` and `tests/` confirms zero call sites). The `@runtime_checkable` decorator adds runtime metaclass machinery and import cost for no benefit; static-type-only protocols should drop the decorator. The explicit `hasattr(field, "name") or not hasattr(field, "is_relation")` guard at `optimizer/field_meta.py:135` already provides the runtime contract enforcement the Protocol would have, with a typed `OptimizerError` message; the decorator is dead weight.

Recommendation: drop the `@runtime_checkable` decorator and the corresponding `runtime_checkable` import on line 23. Keep the `Protocol` annotation — it still serves the static-typing contract and the docstring's structural-contract narrative.

```django_strawberry_framework/optimizer/field_meta.py:32:46
@runtime_checkable
class _DjangoFieldLike(Protocol):
    """Structural contract for the inputs ``from_django_field`` accepts.
    ...
    """
    name: str
    is_relation: bool
```

### `relation_kind` property recomputes from booleans rather than calling the canonical classifier

`FieldMeta.relation_kind` at `optimizer/field_meta.py:100-111` reimplements the four-branch dispatch from `utils.relations.relation_kind` (`utils/relations.py:39-65`) using the stored boolean flags. The shapes are intentionally parallel, but the duplication means a future change to the classifier's branch order or new kind would need two synchronized edits. Today the gap is structurally contained because `from_django_field` calls `utils.relations.relation_kind(field)` at line 161 to populate the short-circuit — so the canonical classifier is still consulted at build time — but the property's dispatch could just as well delegate to the same classifier passing `self` (since `FieldMeta` already exposes `many_to_many` / `one_to_many` / `one_to_one` / `auto_created`, satisfying `_RelationFieldLike` at `utils/relations.py:23-36`).

Recommendation: have the property call `relation_kind(self)` from `utils.relations`. The property keeps its docstring and surface; the body collapses to a one-line delegation. Defer if the folder pass identifies a reason to keep them parallel.

```django_strawberry_framework/optimizer/field_meta.py:100:111
    @property
    def relation_kind(self) -> RelationKind:
        """Return this relation's GraphQL/runtime cardinality classifier."""
        if self.many_to_many:
            return "many"
        if self.one_to_many:
            if self.auto_created:
                return "reverse_many_to_one"
            return "many"
        if self.one_to_one and self.auto_created:
            return "reverse_one_to_one"
        return "forward_single"
```

## What looks solid

### DRY recap

- **Existing patterns reused.** The module imports and reuses `RelationKind` / `relation_kind` from `django_strawberry_framework/utils/relations.py:7-12,39-65`. The `from_django_field` classmethod delegates the reverse-OneToOne short-circuit to `utils.relations.relation_kind(field)` at `optimizer/field_meta.py:161`, which is the canonical classifier. `OptimizerError` at `optimizer/field_meta.py:25` is the shared exception from `exceptions.py` already audited in `docs/review/rev-exceptions.md`. The dataclass is consumed canonically as `DjangoTypeDefinition.field_map: dict[str, FieldMeta]` at `types/definition.py:25` and is the single source of truth for relation shape — every read site routes through it (`types/base.py:162,807`, `types/converters.py:301-349`, `types/resolvers.py:163-182,210-212`, `optimizer/walker.py:107`, `optimizer/extension.py:677-679`).
- **Duplication risk in the current file.** The string literals `"reverse_many_to_one"` and `"reverse_one_to_one"` each appear twice (`optimizer/field_meta.py:107,116` for the former; `optimizer/field_meta.py:110,161` for the latter). The first pair is the in-file duplication caught by the helper's repeated-literal report; the second appears once locally and once in the `from_django_field` short-circuit, so the cross-call duplication is contained. The `relation_kind` property at `optimizer/field_meta.py:101-111` mirrors the classifier logic in `utils/relations.relation_kind` at `utils/relations.py:39-65` — same four-branch dispatch, same return values. Both are intentional (one reads stored booleans on the dataclass, one reads attributes off a Django descriptor) and the second is the source the first imports, so the parallel is the contract, not drift; flagged as a Low cross-file observation for the optimizer folder pass.

### Other positives

- `@dataclass(frozen=True, slots=True)` at `optimizer/field_meta.py:49` is the right shape: immutable per-field snapshot, slot-backed for cache efficiency, hashable for downstream dict/set use. Tests pin immutability at `tests/optimizer/test_field_meta.py:182-186`.
- The cardinality gate at `optimizer/field_meta.py:158-161` correctly forces `nullable=False` for many-side cardinalities BEFORE consulting `field.null`. The block comment at lines 145-157 explains why (Django's `ForeignObjectRel` proxies the forward FK's `null` flag, so a reverse-FK descriptor for a nullable forward FK would otherwise read `True`). The test surface at `tests/optimizer/test_field_meta.py:65-109` pins both the reverse-FK and reverse-M2M shapes against drift toward the descriptor's class-level default.
- The explicit `OptimizerError` guard at `optimizer/field_meta.py:135-139` converts a late `AttributeError` deep inside `__init_subclass__` into a typed call-site failure naming the bad input. Tests pin both the missing-everything case and the partial-shape case (`tests/optimizer/test_field_meta.py:157-179`).
- The two-line `target_field` extraction at `optimizer/field_meta.py:142` is a deliberate single-read for two consumers (`target_field_name` and `target_field_attname`); the comment on lines 140-141 captures the rationale and prevents a future maintainer from inlining the second `getattr(field, "target_field", None)` call.
- The `from_django_field` factory uses a uniform `getattr(field, attr, default)` shape across all eight optional attribute reads (`optimizer/field_meta.py:142,143,144,161,167,169,170,171,172,173,174`), so the four documented descriptor shapes (forward field, reverse FK, M2M, O2O) all build cleanly without per-shape branching. This is the structural payoff of the `FieldMeta` abstraction.
- `is_relation` is normalized through `bool(field.is_relation)` at `optimizer/field_meta.py:164` so a truthy non-bool from a custom descriptor never leaks into the cached map's contract. Same defense via `bool(...)` on `many_to_many` / `one_to_many` / `one_to_one` / `auto_created` (`optimizer/field_meta.py:143,144,167,174`).
- Polymorphic shape across walker / converters / resolvers: walker.py reads `field_map.values()` whose entries can be either `FieldMeta` (registered type) or raw Django fields (unregistered fallback), and every read site uses defensive `getattr(field, attr, default)` (`optimizer/walker.py:194,539-542,587-595`) so both shapes satisfy the consumer contract. `FieldMeta`'s attribute names (`attname`, `related_model`, `is_relation`, `many_to_many`, `one_to_many`, `one_to_one`, `auto_created`) are deliberately the same names Django uses on its field descriptors so the polymorphism does not need a translation layer.
- Static helper ran cleanly: one hotspot (`from_django_field`, 57 lines / 5 branches) which is justified by the eight `getattr`-driven kwargs the factory has to assemble; the function is straight-line construction, not branchy logic. Two-marker ORM table is entirely docstring mentions, not live `_meta` / `get_fields()` calls — the module imports nothing from `django.db.models._meta` directly. No TODOs.

### Summary

`FieldMeta` is structurally clean and well-tested: dataclass shape is right (frozen / slots), the cardinality gate for `nullable` is correct and pinned, the factory's reflective-access pattern is uniform across shapes, and the `OptimizerError` guard converts a late attribute error into a typed call-site failure. Two flags raised: `is_many_side` duplicates the canonical `MANY_SIDE_RELATION_KINDS` set membership rule that already lives in `utils/relations.py` (Medium, easy consolidation to the existing helper), and `@runtime_checkable` on `_DjangoFieldLike` is unused dead weight (Low). The `relation_kind` property's parallel dispatch with `utils.relations.relation_kind` is structurally redundant but contained today (Low, defer-or-fix at folder pass discretion).

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/optimizer/field_meta.py`:
  - Imports (lines 22-29): dropped `runtime_checkable` from the `typing` import; expanded the `utils.relations` import to a parenthesized triple bringing in `is_many_side_relation_kind` alongside the existing `RelationKind` / `relation_kind`.
  - `_DjangoFieldLike` decorator (was line 32): dropped `@runtime_checkable`. The class remains a `Protocol` for static typing; no `isinstance(..., _DjangoFieldLike)` site exists anywhere in the package or tests, so removing the runtime metaclass machinery is behavior-neutral. (L1)
  - `FieldMeta.relation_kind` property (was lines 100-111): collapsed the four-branch dispatch to `return relation_kind(self)`. `FieldMeta` exposes `many_to_many` / `one_to_many` / `one_to_one` / `auto_created` as `bool` dataclass fields, structurally matching `_RelationFieldLike` at `utils/relations.py:23-36`; the property's `getattr(field, attr, False)` defaults inside `utils.relations.relation_kind` are harmless when the attributes are always present. (L2)
  - `FieldMeta.is_many_side` property (was lines 113-116): collapsed the inline `{"many", "reverse_many_to_one"}` set membership to `return is_many_side_relation_kind(self.relation_kind)`, routing through the canonical helper at `utils/relations.py:68-70` which wraps the canonical `MANY_SIDE_RELATION_KINDS` frozenset. (M1)

### Tests added or updated

- `tests/optimizer/test_field_meta.py::test_is_many_side_pins_every_relation_kind` — pins `is_many_side` directly for each `RelationKind` value (forward M2M / reverse FK both `True`; reverse O2O / forward single both `False`). Each case asserts `relation_kind` first to anchor which branch the membership read is exercising. The four cases are constructed via direct `FieldMeta(...)` kwargs rather than going through `from_django_field`, so the membership rule is pinned without depending on Django descriptor shapes. Replaces the previous indirect coverage which only pinned both branches via `nullable` short-circuits on reverse-FK / reverse-M2M from `from_django_field`.

### Validation run

- `uv run ruff format .` — pass (100 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).
- Focused tests: not run per worker prompt (Worker 3 will run focused tests during verification).

### Notes for Worker 3

- Naming-collision check on L2: the property is named `relation_kind` and the module-level import is also named `relation_kind`. Inside the property body, Python resolves `relation_kind(self)` to the module-level imported function (LEGB: local → enclosing → module → builtin; class scope is NOT part of method-body name resolution). Verified by reading both files — no rename of the import was needed, and ruff reports no shadowing diagnostic. If a future maintainer ever needs to call `self.relation_kind` from inside the property body, that would already be infinite recursion regardless of the import naming, so the collision is structural and benign here.
- Structural check on `_RelationFieldLike`: confirmed `FieldMeta` matches the protocol. `_RelationFieldLike` at `utils/relations.py:23-36` requires `many_to_many` / `one_to_many` / `one_to_one` / `auto_created` as `bool`; `FieldMeta` declares all four as `bool` dataclass fields (`optimizer/field_meta.py:89-92,98`). The classifier reads them through `getattr(..., False)` so even if a future shape were to drop one, the defaults still apply.
- Shadow file: not used for this pass; line citations are against the original source as updated.
- Comment pass: not yet performed. Property docstrings ("Return this relation's GraphQL/runtime cardinality classifier." and "Return whether this relation resolves as a GraphQL list.") are still accurate for the delegating bodies; the comment pass can confirm or polish during the next Worker 2 spawn.

---

## Verification (Worker 3)

### Logic verification outcome

- High: None — accepted.
- M1 (`is_many_side` delegation + new test `test_is_many_side_pins_every_relation_kind`): accepted. The body collapses to `is_many_side_relation_kind(self.relation_kind)` at `optimizer/field_meta.py:111`, routing through the canonical helper at `utils/relations.py:68-70`. The new test pins all four `RelationKind` branches via direct `FieldMeta(...)` construction (forward M2M / reverse FK both `True`; reverse O2O / forward single both `False`), each preceded by a `relation_kind` anchor so the membership read is unambiguous.
- L1 (drop `@runtime_checkable` + import): accepted. Both the decorator on `_DjangoFieldLike` and the `runtime_checkable` import are gone; `Protocol` is still imported and the static-typing contract on `from_django_field`'s `field` parameter is unchanged. No `isinstance(..., _DjangoFieldLike)` call site exists anywhere in the package — confirmed dead-weight removal is behaviour-neutral.
- L2 (`relation_kind` property delegation): accepted. The four-branch body collapses to `return relation_kind(self)` at `optimizer/field_meta.py:106`. Structural protocol confirmed: `_RelationFieldLike` at `utils/relations.py:23-36` requires `many_to_many` / `one_to_many` / `one_to_one` / `auto_created` as `bool`, and `FieldMeta` declares all four as `bool` dataclass fields at `optimizer/field_meta.py:92-95,101`. Naming-collision check: the module-level `relation_kind` import resolves cleanly inside the property body (method bodies use LEGB; class scope is not part of method-body name resolution), and `uv run pytest tests/optimizer/test_field_meta.py -x` runs 16 passing tests including the existing branch coverage (`test_from_django_field_reverse_fk`, `test_from_django_field_many_to_many`, `test_from_django_field_reverse_one_to_one_is_nullable`, `test_from_django_field_one_to_one`) that exercise every `relation_kind` arm via the cardinality-gated `nullable` short-circuit at `optimizer/field_meta.py:156`.

### DRY findings disposition

All three duplications consolidated against `utils/relations.py` canonical helpers. The hard-coded `{"many", "reverse_many_to_one"}` literal at the former `optimizer/field_meta.py:116` is gone — `is_many_side_relation_kind` now wraps the canonical `MANY_SIDE_RELATION_KINDS` frozenset at `utils/relations.py:14-19,68-70` as the single source of truth. The parallel four-branch dispatch in the `relation_kind` property is gone — the property now delegates to `utils.relations.relation_kind(self)` so any future branch order or new `RelationKind` value lands in exactly one place. The two-shape parallel between `FieldMeta` reading stored booleans and `utils.relations.relation_kind` reading attributes off a Django descriptor is preserved as the intentional contract (both read the same four flag names; `getattr(..., False)` defaults keep the classifier defensive). Accepted.

### Temp test verification

None used. The existing tests plus the newly-added `test_is_many_side_pins_every_relation_kind` cover every `RelationKind` branch and the `is_many_side` membership read directly via `FieldMeta(...)` construction; no temp test under `docs/review/temp-tests/` was needed.

### Verification outcome

`logic accepted; awaiting comment pass`

Validation re-runs: `uv run ruff check django_strawberry_framework/optimizer/field_meta.py` — pass. `uv run pytest tests/optimizer/test_field_meta.py -x` — 16/16 passed (the focused-run coverage gate fail is expected when only one test file is run and is not a finding).

Scope check: `git diff -- django_strawberry_framework/ tests/ --stat` shows changes in `conf.py`, `optimizer/_context.py`, `optimizer/extension.py`, `optimizer/field_meta.py`, `registry.py`, `tests/optimizer/test_extension.py`, and `tests/optimizer/test_field_meta.py`. The non-`field_meta` files are pre-existing uncommitted modifications from prior review cycles (matching this run's earlier checklist items for `conf.py`, `_context.py`, `extension.py`, `registry.py`); Worker 2's current pass is confined to `optimizer/field_meta.py` and `tests/optimizer/test_field_meta.py` per the artifact scope.

Top-level `Status:` remains `fix-implemented` (Worker 2-owned); not advanced to `verified` per the interim-sub-pass rule. Comment pass still to come.

---

## Comment/docstring pass

No docstring updates needed. The post-edit `relation_kind` and `is_many_side` properties still match their existing docstrings (semantics unchanged; the bodies only delegate to the canonical helpers in `utils/relations.py`). The `_DjangoFieldLike` class docstring still accurately describes the static structural contract after dropping `@runtime_checkable` — it never referenced runtime-checkability, only the structural attributes (`name`, `is_relation`) and the defensive `getattr` reads for the rest. Module docstring, `FieldMeta` class docstring (Attributes block), and `from_django_field` docstring all still describe the final approved behavior verbatim.

Validation: `uv run ruff format .` — pass (100 files left unchanged). `uv run ruff check --fix .` — pass (all checks passed). No source edits.

---

## Changelog disposition

- Warranted? Not warranted.
- Reason: this cycle's edits are internal DRY consolidations against the canonical helpers in `utils/relations.py` — `is_many_side` now calls `is_many_side_relation_kind`, `relation_kind` now delegates to `utils.relations.relation_kind(self)`, and `@runtime_checkable` was dropped from a Protocol that never had a runtime `isinstance` call site. No public API change. No observable behaviour change: the delegated helpers return identical outputs to the inline forms (`MANY_SIDE_RELATION_KINDS` wraps the same `{"many", "reverse_many_to_one"}` set; the four-branch dispatch in `utils.relations.relation_kind` matches the property's prior dispatch by construction). Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed.") and the active plan (no changelog authorization for this cycle item), no `CHANGELOG.md` edit is made.
- What was done: no `CHANGELOG.md` edit.
- Validation: `uv run ruff format .` — pass; `uv run ruff check --fix .` — pass.

---

## Iteration log

## Verification (Worker 3, pass 2)

- **Comment verification outcome:** No docstring updates needed — accepted. `git diff -- django_strawberry_framework/optimizer/field_meta.py` shows only the logic-pass deltas (drop `runtime_checkable` import + decorator, expand `utils.relations` import to include `is_many_side_relation_kind`, collapse the `relation_kind` property body to `relation_kind(self)`, collapse the `is_many_side` property body to `is_many_side_relation_kind(self.relation_kind)`); no further edits in this pass. Both property docstrings ("Return this relation's GraphQL/runtime cardinality classifier." and "Return whether this relation resolves as a GraphQL list.") still accurately describe semantics after the DRY-consolidation — the delegated helpers in `utils/relations.py` return identical outputs to the prior inline bodies, so the existing docstrings are not stale. The `_DjangoFieldLike` class docstring never referenced runtime-checkability and remains accurate. Module docstring, `FieldMeta` Attributes block, and `from_django_field` docstring all still describe the final approved behavior verbatim.
- **Changelog verification outcome:** Not warranted — accepted. `git diff -- CHANGELOG.md` is empty; `CHANGELOG.md` untouched. The disposition's rationale cites all four required facts: (1) internal DRY consolidations against canonical helpers in `utils/relations.py`, (2) no public API change, (3) no observable behavior change (`MANY_SIDE_RELATION_KINDS` wraps the same `{"many", "reverse_many_to_one"}` set; `utils.relations.relation_kind` four-branch dispatch matches the property's prior dispatch by construction), (4) `AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed." plus the active plan's lack of changelog authorization for this cycle item. Validation: both `uv run ruff format .` and `uv run ruff check --fix .` recorded as pass in the disposition; spot-re-ran `uv run ruff check django_strawberry_framework/optimizer/field_meta.py` — pass.
- **Verification outcome:** `cycle accepted; verified`.
