# Review: `django_strawberry_framework/types/definition.py`

## High:

None.

## Medium:

### Mutable container fields lack frozen/post-init guarantees

`field_map` and `optimizer_hints` are typed `dict[str, ...]`, and `selected_fields` is `tuple[Any, ...]`. The dataclass is not `frozen=True` and the dict fields are not wrapped or copied. Once a `DjangoTypeDefinition` is handed to the optimizer/finalizer it is treated as the canonical, immutable shape — but nothing prevents a downstream caller from mutating `field_map[...]` or reassigning `interfaces`. This is the same "documented contract, not enforced" pattern flagged in `registry.py`, `optimizer/plans.py`, and `types/base.py`: the symptom is silent state corruption that surfaces on the next schema build or plan-cache hit. Either freeze the dataclass (and store `MappingProxyType` views for the dicts), or document explicitly that the producer (`types/base.py`/finalizer) is the only writer and add an assertion in the consumer paths.

```django_strawberry_framework/types/definition.py:14:41
@dataclass
class DjangoTypeDefinition:
    ...
    field_map: dict[str, FieldMeta]
    optimizer_hints: dict[str, OptimizerHint]
    ...
    interfaces: tuple[type, ...] = ()
    finalized: bool = field(default=False)
```

## Low:

### `finalized: bool` carries lifecycle state on a "metadata object" dataclass

The module docstring calls this a "canonical metadata object", but `finalized: bool` (and the implicit producer/consumer split it encodes) makes the dataclass a small state machine. There is no method on the class itself that flips `finalized`; the producer in `types/base.py`/`types/finalizer.py` mutates the flag externally. Same calibration as `registry._finalized` — fine while there is one writer, fragile the moment a second slice needs to read it. Worth a folder-pass note to confirm exactly one site flips it.

```django_strawberry_framework/types/definition.py:41:41
finalized: bool = field(default=False)
```

### `Any | None` escape hatches on four `*_class` slots

`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class` are all `Any | None`. These will be tightened when the respective specs land (`docs/FEATURES.md` lists them as deferred), but the typing here is loose enough that a consumer misassignment (e.g., assigning an *instance* instead of a *class*) would not be caught even by a future static check. Mark them with a TODO anchor naming the slice that will tighten the type, matching the convention `base.py` already uses for the relay-interfaces anchor below.

```django_strawberry_framework/types/definition.py:32:35
filterset_class: Any | None = None
orderset_class: Any | None = None
aggregate_class: Any | None = None
fields_class: Any | None = None
```

### TODO anchor is single-site but adjacent slot has no anchor

The relay-interfaces TODO at lines 37-40 anchors `interfaces`, but the four `*_class` slots above and `search_fields` carry no slice anchor despite being equally deferred surface. AGENTS.md asks for TODO anchors at the source site for staged-but-unimplemented slices; consider adding short anchors (or a single grouped anchor) so the retirement search at slice-ship time finds every related slot.

```django_strawberry_framework/types/definition.py:32:36
filterset_class: Any | None = None
orderset_class: Any | None = None
aggregate_class: Any | None = None
fields_class: Any | None = None
search_fields: tuple[str, ...] = ()
```

### `field(default=False)` on `finalized` is verbose

`finalized: bool = False` is equivalent and matches the style used on the `frozenset()` and `()` defaults above. No behavior change; one less import-surface dependency on `field` for readers.

```django_strawberry_framework/types/definition.py:41:41
finalized: bool = field(default=False)
```

## What looks solid

- Static helper `scripts/review_inspect.py` was run; overview at `docs/review/shadow/django_strawberry_framework__types__definition.overview.md`.
- Import graph is tight: stdlib + django + two local imports from `optimizer/`, both type-only at runtime usage. No circular-import risk visible.
- Default values use immutable sentinels (`frozenset()`, `()`) — no shared-mutable-default footgun.
- Single class, no methods, no control-flow hotspots; the file is exactly the "canonical metadata object" the docstring promises.
- TODO anchor at lines 37-40 names the active spec (`docs/spec-relay_interfaces.md`) and the slice (0.0.5), per AGENTS.md.

---

### Summary:

`definition.py` is a thin dataclass holding the canonical metadata for a `DjangoType`. The only meaningful concern is the same "documented contract, not enforced" theme already established across `registry.py`, `optimizer/plans.py`, and `types/base.py`: the mutable `dict` fields are treated as immutable post-handoff but nothing prevents mutation — fold the resolution into the types/ folder-pass stance on whether to freeze definitions or wrap their mutable fields. Remaining items are Low: loose `Any | None` typing on deferred-spec slots without TODO anchors, the redundant `field(default=False)` form on `finalized`, and a folder-pass follow-up to confirm `finalized` has exactly one writer site.

## Verification

PASS. Worker 2 diff addresses both actionable Lows: `field(default=False)` collapsed to `finalized: bool = False` (and `field` import dropped), and a grouped TODO anchor was added above the four `*_class` slots naming the deferred specs in `docs/FEATURES.md`. The Medium (frozen/MappingProxyType) and the two remaining Lows (`finalized` lifecycle single-writer check, `search_fields` anchor) are explicitly routed by the artifact body to the types/ folder pass, so retain-without-change is contract-sanctioned. A new slot `consumer_assigned_scalar_fields: frozenset[str] = frozenset()` was added to support the types/base.py cycle's scalar-override path; that cross-file addition is sanctioned by the prior cycle's accepted Medium and uses an immutable-sentinel default consistent with siblings. `uv run pytest tests/types -q --no-cov` → 84 passed, 1 skipped.
