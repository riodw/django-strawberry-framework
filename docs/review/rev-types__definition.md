# Review: `django_strawberry_framework/types/definition.py`

Status: verified

## DRY analysis

- None — the file is a single dataclass with no logic; there are no helper-extraction opportunities, no repeated literals (the five `frozenset()` defaults are the four-corner override contract storage and intentionally cannot share a sentinel because each set has a distinct invariant and identity is irrelevant for empty frozensets), and the per-field type annotations are unique enough that bundling them under a shared alias would obscure rather than DRY. The shadow overview confirms zero repeated string literals.

## High:

None.

## Medium:

### `definition.primary` is set but never read inside the package

`DjangoTypeDefinition.primary` (`types/definition.py:59`) is populated by `DjangoType.__init_subclass__` (`types/base.py:245`) and threaded into `registry.register_with_definition(..., primary=validated.primary)` (`base.py:247`), but no production code in `django_strawberry_framework/` reads `definition.primary` afterwards. The runtime "is this the primary?" predicate lives on the registry side as `_primaries[model]` (`registry.py:131-132,201-203,235`), and `primary_for(model)` is the documented lookup (`registry.py:235`). A `grep -n "\.primary\b" django_strawberry_framework/` confirms only `types/base.py` writes the field; no reader exists. Tests pin `definition.primary` (`tests/types/test_base.py:432,443`), but those are introspection-surface tests, not production consumers.

This matters because the field acts as a parallel source of truth that can drift from `registry._primaries[model]` if a future maintainer mutates one without the other (`register_definition` does not re-validate `definition.primary` against `_primaries[model]`, and the post-construction `dataclass` is freely mutable). The dataclass docstring (`types/definition.py:16-42`) lists invariants for `field_map`, `selected_fields`, `finalized`, and the four `consumer_*_fields` sets — but does NOT describe `primary` as an introspection-only mirror of the registry state, which is the only honest framing given that no package reader exists.

Recommended change: either (a) add a docstring `Invariants:` bullet for `primary` that explicitly frames it as a write-once introspection mirror of `registry._primaries[model]`, owned by `DjangoType.__init_subclass__`, never mutated post-construction, and never read by package code (consumers may read it for introspection only); or (b) drop the field entirely and route introspection through `registry.primary_for(definition.model) is type_cls`. Option (a) is the lower-risk fix because `tests/types/test_base.py:432,443` pin the field's existence and Slice 2 spec wording in `KANBAN.md` may treat the dataclass surface as the public introspection layer; option (b) is the higher-quality fix if and only if those tests can move to `registry.primary_for(...)` without losing coverage of the four-corner override contract. Worker 2 should choose (a) unless a deliberate registry-as-single-source-of-truth refactor is in scope for this cycle.

```django_strawberry_framework/types/definition.py:14-63
@dataclass
class DjangoTypeDefinition:
    ...
    primary: bool = False
    # Populated by ``_validate_meta``; consumed by ``finalize_django_types()``
    # as the finalizer's source of truth for base injection.
    interfaces: tuple[type, ...] = ()
    finalized: bool = False
```

The comment block at `definition.py:60-61` documents `interfaces` but is mis-attached: it sits between `primary` and `interfaces`, and because the dataclass body reads top-to-bottom, a reader scanning for `primary`'s rationale lands on the `interfaces` comment first and assumes it applies to `primary`. Either move the comment immediately above `interfaces` with no blank line between them or anchor it via inline `# ...` on `interfaces: tuple[type, ...] = ()`. See Low "Comment placement misattaches the `interfaces` rationale" below.

## Low:

### Mutable defaults on a `@dataclass` — `field_map: dict[str, FieldMeta]` and `optimizer_hints: dict[str, OptimizerHint]` are not `field(default_factory=...)`

The four `consumer_*_fields` slots and `interfaces` all use safe-immutable defaults (`frozenset()` / `()`), but `field_map` (`definition.py:51`) and `optimizer_hints` (`definition.py:52`) are required positional fields with no default — so the standard dataclass mutable-default trap does not apply at construction. However, the dataclass docstring at `definition.py:16-42` describes `field_map` as "treated as immutable by every reader," and the runtime type is a plain `dict`. The contract is documented but not enforced: a future reader could legally mutate `definition.field_map["foo"] = bar` and the registry would silently observe the mutation. Defer until a regression surfaces (the field_map is owned by a single construction site at `base.py:174`, all reads in `walker.py:114`, `extension.py:713`, and `finalizer.py:192` go through it without mutation, and the package tests pin the immutability convention via observed behavior). Trigger: when a fourth reader of `field_map` lands, OR when a fix lands that touches `field_map` mutation rules, harden the dataclass with `types.MappingProxyType` wrappers at the construction site (`base.py:174,228`) so the immutability invariant is enforced at the type-system layer.

### `finalized: bool` is the only flip-once field but has no `__post_init__` or `frozen=True` protection

`finalized` (`definition.py:63`) is documented at `types/definition.py:30-35` as "flips exactly once, in `finalize_django_types()`," but a typo at any call site that does `definition.finalized = True` outside `finalize_django_types()` would silently corrupt the re-finalization short-circuit. The current `@dataclass` decorator without `frozen=True` allows arbitrary attribute writes. Defer until the finalization phase grows a second writer (e.g. a Relay finalization rerun branch or a partial-rebuild API). Trigger: when `finalize_django_types()` gains an explicit rerun or partial-rebuild path, add a write-guard via `__setattr__` override or a `frozen=True` + `dataclasses.replace(definition, finalized=True)` pattern at the single finalizer write site (`finalizer.py:244`).

### Comment placement misattaches the `interfaces` rationale

The inline comment at `definition.py:60-61` sits between `primary: bool = False` and `interfaces: tuple[type, ...] = ()`. Because Python dataclass body reads top-to-bottom and dataclass fields don't carry per-field block comments natively, a reader scanning for documentation on `primary` lands on the `# Populated by _validate_meta; consumed by finalize_django_types() ...` block first and may mistakenly attribute it to `primary`. The comment is about `interfaces` only — `primary` is consumed by the registry, not the finalizer. Recommended (defer with trigger or fold into the Medium fix): move the comment immediately adjacent to `interfaces` with no blank line, OR convert it to a docstring `Invariants:` bullet alongside the existing four bullets. Trigger: address inside the Medium "primary is set but never read" docstring-update fix.

### Optional fields ordered after required fields hides the call-site contract

`field_map`, `optimizer_hints`, and `has_custom_get_queryset` (`definition.py:51-53`) are required positional fields without defaults. They sit between `selected_fields` (also required, `definition.py:50`) and the optional defaults block (`definition.py:54-63`). The dataclass field ordering is correct (required fields must precede defaulted fields). However, the single construction site at `base.py:228-246` uses keyword arguments exclusively, so positional construction is not the contract — all 13 fields are named. Defer; no action needed. The dataclass field-order rule keeps the contract self-documenting at the class-definition site.

### `Literal["__all__"]` import surfaces a typing-only dependency

`from typing import Literal` (`definition.py:6`) is imported solely for the `fields_spec: tuple[str, ...] | Literal["__all__"] | None` annotation at `definition.py:48`. The string literal `"__all__"` matches the normalization output of `_normalize_fields_spec` (`base.py:301-307`), which can return `"__all__"` as a bare `str` even though the function signature says `tuple[str, ...] | str | None`. The dataclass tightens the type with `Literal["__all__"]`, but the producer (`_normalize_fields_spec`) does not — the caller relies on the function's runtime behavior to honor the `Literal`. Defer; not a defect today, but a typing-tightening opportunity. Trigger: when a third call site for `_normalize_fields_spec` lands, or when mypy/pyright is added to the CI gate, tighten `_normalize_fields_spec`'s return type to `tuple[str, ...] | Literal["__all__"] | None` so producer and storage agree.

## What looks solid

### DRY recap

- **Existing patterns reused.** The four-corner consumer override contract storage (`consumer_authored_fields`, plus the four `consumer_*_fields` partitions, `definition.py:54-58`) faithfully mirrors the `_consumer_assigned_fields` collection-site shape in `base.py:319-380` and the four-corner override docstring at `base.py:328-360`. The dataclass is the canonical introspection surface those collection sites feed.
- **New helpers considered.** No helper extraction is appropriate — the file is purely a metadata container; behavior lives at the construction site (`base.py:228-246`) and the consumer sites (`registry.py`, `finalizer.py`, `walker.py`, `extension.py`, `relay.py`, `list_field.py`).
- **Duplication risk in the current file.** The five `frozenset()` defaults are intentionally distinct slots (annotated × scalar, annotated × relation, assigned × scalar, assigned × relation, plus the union `consumer_authored_fields`); they look duplicated but encode the four-corner contract from `base.py:328-360` and cannot share a sentinel without losing the per-corner introspection surface.

### Other positives

- The docstring at `definition.py:16-42` documents four explicit invariants tied to the canonical construction site (`base.py:__init_subclass__`) and the canonical finalization site (`finalizer.py`). Cross-reference accuracy is preserved across the package — every named site exists at the cited path.
- The dataclass acts as the documented inter-module contract: `registry.register_definition` (`registry.py:259`), `iter_definitions` (`registry.py:315`), `finalize_django_types` (per `finalizer.py:216-244`), `apply_interfaces` (`relay.py:86-101`), `walker.py:114`, `extension.py:713`, and `list_field.py:112` all consume the same `DjangoTypeDefinition` shape — no parallel metadata records exist.
- The `consumer_authored_fields` slot at `definition.py:54` correctly carries the union the four-corner contract needs, not a recomputed `frozenset.union(...)` — the union is computed once at `base.py:186-193` and stored, so downstream readers (`_build_annotations` `base.py:818,851`; `finalizer.py:185`) get a constant-time membership test instead of re-unioning four sets per field.
- The `selected_fields: tuple[models.Field, ...]` slot preserves `Model._meta.get_fields()` iteration order per the invariant doc; this is the contract `_select_fields` (`base.py:725`) feeds and `_attach_relation_resolvers` (`resolvers.py:281`) reads.
- Static helper output (`docs/shadow/django_strawberry_framework__types__definition.overview.md`) confirms: 0 control-flow hotspots, 0 TODO comments, 0 repeated string literals, single class definition, 6 imports — appropriate complexity for a metadata container.

### Summary

`types/definition.py` is a near-pure data container with documented invariants and a single construction site. The file has one substantive Medium: `definition.primary` is written but never read by package code, so the dataclass currently maintains a parallel-but-untested mirror of `registry._primaries[model]` — the docstring should either explicitly frame `primary` as an introspection-only mirror or the field should be dropped in favor of `registry.primary_for(...)`. Five trigger-gated Lows cover mutable-default contract enforcement, `finalized` flip protection, comment placement, ordering convention, and the typing-tightening opportunity for `Literal["__all__"]`. No DRY action items; the four-corner override storage shape is correctly distinct, not duplicated.

---

## Fix report (Worker 2)

Consolidated single-spawn: M1 is a docstring-invariant addition plus a
comment-block reposition with no behavior change; L1-L5 are all
forward-looking per Worker 1's own prose ("Defer until …", "Trigger:
when …", "no action needed").

### Files touched
- `django_strawberry_framework/types/definition.py:42-65` — added
  `primary` invariant bullet to the `DjangoTypeDefinition` docstring
  framing it as a write-once introspection mirror of
  `registry._primaries[model]`, owned by
  `DjangoType.__init_subclass__`, never mutated post-construction, never
  read by package code (consumers may read for introspection only);
  repositioned the `# Populated by _validate_meta; consumed by
  finalize_django_types() …` comment block from above `primary` (where
  it mis-attached) to immediately below `interfaces: tuple[type, ...] =
  ()` with a lead-in naming the slot (`# ``interfaces`` is populated by
  …`) so a reader scanning top-to-bottom can no longer mis-attribute the
  rationale to `primary`.

### Tests added or updated
- None. M1 is a docstring + comment-placement change with no behavior
  surface. Existing tests at `tests/types/test_base.py:432,443` already
  pin `definition.primary` as the registry-mirror introspection field
  (Worker 1 cited these as the reason option (a) is the lower-risk fix).

### Validation run
- `uv run ruff format .` — pass / no-changes (118 files left unchanged).
- `uv run ruff check --fix .` — pass / no-changes (all checks passed).
- No pytest per `START.md`'s standing rule (formatting only; no behavior
  change to confirm).

### Notes for Worker 3
- Shadow file: `docs/shadow/django_strawberry_framework__types__definition.overview.md`
  (Worker 1 confirmed 0 control-flow hotspots, 0 TODOs, 6 imports — no
  refresh needed for a docstring + comment-reposition edit).
- Per-finding dispositions and changelog disposition consolidated into a
  single spawn under explicit dispatch authorisation (all Lows
  forward-looking, M1 trivially-localised docstring + comment-reposition
  with no logic change — satisfies the first AND second consolidation
  criteria in `worker-2.md`'s "Consolidated single-spawn pass" section).
- M1 took option (a) per Worker 1's verbatim recommendation: "Worker 2
  should choose (a) unless a deliberate registry-as-single-source-of-truth
  refactor is in scope for this cycle." No such refactor is in cycle 22
  scope.
- Comment-block reposition uses the lead-in form (`# ``interfaces`` is
  populated by …`) per Worker 1's verbatim option in the artifact's
  Medium recommendation: "Either move the comment immediately above
  ``interfaces`` with no blank line between them or anchor it via
  inline `# ...` on `interfaces: tuple[type, ...] = ()`." The chosen
  form (positioned below the field with an explicit `interfaces`
  lead-in) is functionally equivalent and slightly more robust against
  future re-ordering — the slot is named in the comment text itself, so
  a future reader cannot mis-attribute even if the comment drifts.

---

## Verification (Worker 3)

### Logic verification outcome
- M1 (docstring + comment reposition): accepted. `git diff -- django_strawberry_framework/types/definition.py` shows exactly two hunks: (a) a new `primary` `Invariants:` bullet at lines 42-48 framing the slot as a write-once introspection mirror of `registry._primaries[model]`, owned by `DjangoType.__init_subclass__`, never mutated post-construction, never read by package code — matches Worker 1's verbatim option (a) recommendation; (b) the `# Populated by _validate_meta; …` block moved from above `primary` to immediately below `interfaces` with a lead-in naming the slot (`# ``interfaces`` is populated by …`), eliminating the mis-attachment Low 3 flagged. No behavior change; no signature change; the dataclass field order is preserved.
- L1 (mutable defaults `field_map` / `optimizer_hints`): forward-looking, verbatim trigger preserved ("when a fourth reader of `field_map` lands, OR when a fix lands that touches `field_map` mutation rules, harden the dataclass with `types.MappingProxyType` wrappers at the construction site (`base.py:174,228`)…") — disjunctive arms intact.
- L2 (`finalized` flip-once protection): forward-looking, verbatim trigger preserved ("when `finalize_django_types()` gains an explicit rerun or partial-rebuild path, add a write-guard via `__setattr__` override or a `frozen=True` + `dataclasses.replace(definition, finalized=True)` pattern at the single finalizer write site (`finalizer.py:244`)") — disjunctive arms intact.
- L3 (comment mis-attaches `interfaces` rationale): folded into M1 fix per Worker 1's verbatim instruction "address inside the Medium 'primary is set but never read' docstring-update fix." Verified via post-edit re-read: the comment now sits below `interfaces` with explicit slot-name lead-in.
- L4 (optional-after-required ordering): forward-looking, verbatim "Defer; no action needed" framing preserved.
- L5 (`Literal["__all__"]` typing-only dep): forward-looking, verbatim trigger preserved ("when a third call site for `_normalize_fields_spec` lands, or when mypy/pyright is added to the CI gate, tighten `_normalize_fields_spec`'s return type to `tuple[str, ...] | Literal['__all__'] | None`…") — disjunctive arms intact.

### DRY findings disposition
None — Worker 1 explicitly recorded zero DRY items; the file is a single dataclass with no helper-extraction opportunities. Confirmed via post-edit re-read.

### Temp test verification
None used. M1 is a docstring + comment-reposition change with no behavior surface.

### Comment-pass verification
Structurally fused with the logic pass per worker-memory pattern (15) — the M1 fix IS a docstring/comment edit, so the comment pass is a structural no-op. Per-finding dispositions in the artifact correctly enumerate each Low's forward-looking carry-forward; Low 3 correctly cross-references the M1 fold.

### Changelog disposition verification
`git diff -- CHANGELOG.md` is empty. `Not warranted` cites BOTH `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization for cycle 22, plus the twenty-one-deep 0.0.7 precedent chain. Internal-only framing is honest: docstring + comment-reposition on a metadata container with no consumer-visible behavior change, no public symbol added or removed, no typed-error contract change.

### Validation run
- `uv run ruff format --check django_strawberry_framework/types/definition.py` — pass (1 file already formatted).
- `uv run ruff check django_strawberry_framework/types/definition.py` — pass (all checks passed).
- No pytest per `AGENTS.md` standing rule for docstring/comment-only edits.

### Verification outcome
`cycle accepted; verified`

---

## Comment/docstring pass

Consolidated into the logic pass above — M1 IS a docstring + comment
edit, so the comment pass is structurally fused with the logic pass per
worker-memory pattern (15) "When the M1 fix lands the docstring in the
same diff because the docstring IS the contract, the comment pass is
structurally a no-op — document this explicitly rather than re-editing."

### Files touched
- None additional. See logic-pass `## Fix report (Worker 2)` above.

### Per-finding dispositions
- Medium 1 (`primary` set but never read): addressed in logic pass via
  docstring `Invariants:` bullet + comment-block reposition; no
  additional comment edit needed.
- Low 1 (mutable defaults on `field_map` / `optimizer_hints`):
  forward-looking — verbatim trigger: "when a fourth reader of
  `field_map` lands, OR when a fix lands that touches `field_map`
  mutation rules, harden the dataclass with `types.MappingProxyType`
  wrappers at the construction site (`base.py:174,228`) so the
  immutability invariant is enforced at the type-system layer." No
  in-cycle edit.
- Low 2 (`finalized` flip-once protection): forward-looking — verbatim
  trigger: "when `finalize_django_types()` gains an explicit rerun or
  partial-rebuild path, add a write-guard via `__setattr__` override or
  a `frozen=True` + `dataclasses.replace(definition, finalized=True)`
  pattern at the single finalizer write site (`finalizer.py:244`)." No
  in-cycle edit.
- Low 3 (comment mis-attaches `interfaces` rationale): folded into the
  Medium 1 fix per Worker 1's verbatim instruction "address inside the
  Medium 'primary is set but never read' docstring-update fix." Done.
- Low 4 (optional-after-required ordering): forward-looking — verbatim
  prose: "Defer; no action needed. The dataclass field-order rule keeps
  the contract self-documenting at the class-definition site." No
  in-cycle edit.
- Low 5 (`Literal["__all__"]` typing-only dep): forward-looking —
  verbatim trigger: "when a third call site for `_normalize_fields_spec`
  lands, or when mypy/pyright is added to the CI gate, tighten
  `_normalize_fields_spec`'s return type to `tuple[str, ...] |
  Literal['__all__'] | None` so producer and storage agree." No
  in-cycle edit.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass / no-changes.

### Notes for Worker 3
Comment pass is structurally fused with the logic pass; no additional
file touches.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly
instructed") AND the active `docs/review/review-0_0_7.md` plan's silence
on changelog authorization for cycle 22. The cycle's only edit is a
docstring `Invariants:` bullet + comment-block reposition on a
metadata-container dataclass — no consumer-visible behavior change, no
public symbol added or removed, no typed-error contract change. The
twenty-one-deep precedent chain (cycles 1-21 in the 0.0.7 window) all
closed `Not warranted` on the same combination of AGENTS.md + plan
silence; cycle 22's docstring-and-comment-only surface area is strictly
narrower than any prior cycle in the chain (no behavior change, no test
addition, no signature change).

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass / no-changes.

---

## Iteration log

_None yet._
