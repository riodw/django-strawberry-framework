# Spec: Public Surface & Documentation Discipline

## Problem statement

The package's public surface — what's re-exported from `django_strawberry_framework/__init__.py`, what `docs/README.md` describes as "shipped", what tests pin as the consumer contract — must stay aligned with the actual implementation. The original alpha review called this out while the optimizer was still incomplete. As of 0.0.3, the Layer 2 optimizer is effective end-to-end, so this spec records the promotion discipline and the current exported surface.

The fix is not more documentation. It is stricter documentation discipline. This spec defines the rules that govern what gets promoted to the public surface and how the surface is described. With those rules in place, README updates, optimizer-visibility decisions, and any future "is X shipped?" judgment call all reduce to applying the rules.

## Current state

0.0.3 public surface (per `django_strawberry_framework/__init__.py`):

- `DjangoType` — Layer 2 type system, shipped.
- `DjangoOptimizerExtension` — Layer 2 optimizer, shipped end-to-end through O1-O6 and B1-B8.
- `OptimizerHint` — typed optimizer-hint wrapper, shipped as part of B4.
- `auto` — re-exported from `strawberry`.
- `__version__`.

Current README structure (`docs/README.md`):

- Goal, vs comparisons, full target architecture (subsystems, folder layout, tests-mirror), design-doc list, status.

The remaining mismatch risk is Layer 3: the README's target layout includes subpackages that do not exist on disk yet (`filters/`, `orders/`, `aggregates/`, `management/`, plus single-file modules `apps.py`, `fieldset.py`, `permissions.py`, `connection.py`). Those names stay planned until their implementations, tests, and docs land.

## Goal

A public surface and documentation contract that:

- Says exactly what works today, with no aspirational language masquerading as current-state.
- Makes it impossible to accidentally import a feature that isn't effective end-to-end.
- Has a single named status vocabulary so contributors and consumers read the same words the same way.
- Reduces every future "is X shipped?" decision to applying the rules in this spec.

## Non-goals

This spec does not redesign the package layout — that lives in `docs/README.md` "Package architecture" and the per-subsystem spec docs. It defines the rules that govern when each piece of the layout becomes consumer-visible.

## Topics

### Top-level re-export rule

`django_strawberry_framework/__init__.py` re-exports a name iff **all four** are true:

1. The implementation is shipped — the symbol exists in the package and the code path it represents is effective end-to-end. Not stubbed. Not behind a known-broken hook.
2. The behavior is tested — at least one test pins the consumer-visible contract; not "covered as a side effect of an integration test".
3. The contract is documented — the symbol appears in `docs/README.md` "Current surface" with a status marker of `shipped`.
4. The naming is stable enough to honor for the rest of the alpha — renaming requires a deprecation cycle.

Names that fail any of these stay reachable via their dotted submodule path (`from django_strawberry_framework.<subpackage> import <Name>`) so power users and tests can still get them, but they are not in the top-level namespace.

#### Decision for 0.0.3

`DjangoOptimizerExtension` remains top-level-exported because the optimizer is now effective end-to-end. O1-O6 and B1-B8 are implemented and covered, including the O3 root-gated resolve hook, nested prefetch chains, projection, custom `get_queryset` downgrade to `Prefetch`, optimizer hints, plan introspection, schema audit, field metadata caching, and queryset diffing.

```
from django_strawberry_framework import DjangoOptimizerExtension, OptimizerHint
```

The subpackage paths also remain supported:

```
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.optimizer.hints import OptimizerHint
```

The `__all__` for 0.0.3 is therefore:

```
__all__ = (
    "DjangoOptimizerExtension",
    "DjangoType",
    "OptimizerHint",
    "__version__",
    "auto",
)
```

### When a subsystem is top-level vs subpackage-only

Subpackages exist for code organization (`types/`, `optimizer/`, future `filters/`, `orders/`, etc.) regardless of whether they're top-level-exported. The promotion path for a consumer-facing class:

- A subsystem starts as a subpackage with an `__init__.py` that re-exports its consumer-facing names internally. Consumers reach it via `from django_strawberry_framework.<subpackage> import <Name>`.
- When the subsystem meets all four top-level re-export rules above, its primary consumer-facing names are added to `django_strawberry_framework/__init__.py`'s `__all__`.
- The subpackage `__init__.py` keeps its own re-exports too, so both import paths continue working.

Internal helpers — factories, walkers, individual `Filter` / `Order` / aggregate primitives, converters — never get top-level re-exports. They stay reachable via their submodule path (`from django_strawberry_framework.filters.factories import ...`) for power users and tests; they are not in `__all__`.

### `docs/README.md` structure

Two sections, with explicit status markers inside each:

- `## Current surface` — what works today. Every entry carries a status marker (`shipped` / `partial` / `experimental`). No entry without a marker.
- `## Planned surface` — what's coming. Every entry carries a status marker (`planned` / `in flight` / `deferred`). No aspirational language without a marker.

There is no third section. The reviewer suggested `Current` / `Planned` / `Not implemented yet`, but the third section duplicates the second once the markers are in place. The sharper fix is the markers themselves, not more sectioning.

The "Folder layout" tree currently in the README becomes two trees, one per section: a `Current` tree showing what's actually on disk, with each entry's status marker, and a `Planned` tree showing the target shape, with each not-yet-existing entry's status marker. `docs/TREE.md` already keeps both shapes side-by-side; the README's job is to point at TREE.md for detail and surface only the high-level marker breakdown.

### Status-marker vocabulary

Every consumer-visible feature mention in `docs/README.md`, `docs/TREE.md`, and any spec doc uses one of these markers. No synonyms, no improvisation.

- `shipped` — Effective end-to-end, tested, documented, contract stable for the alpha. Top-level-exportable.
- `partial` — Some code paths effective, others not; the description must spell out which is which. Not top-level-exportable.
- `experimental` — Reachable via dotted path, may break without notice. Not top-level-exportable.
- `planned` — Has a spec doc or is named in this or another spec. No code yet. Not importable.
- `in flight` — Has a spec doc and partial implementation; landing across multiple slices. Not top-level-exportable.
- `deferred` — Reserved for a future spec; no work in flight; no Meta key accepted today (or accepted-and-rejected per `spec-django_type_contract.md` "Accepted vs deferred Meta keys"). Not importable.
- `aspirational` — Mentioned in design conversations as a possibility but not yet committed to. Not promoted to README.

### Alpha signaling rules

The language describing a feature must match its marker:

- `shipped` features use present tense without hedging: "DjangoType generates...", "convert_choices_to_enum produces...".
- `partial` features must qualify which paths work: "DjangoOptimizerExtension's per-resolver dispatch is shipped; the `on_executing_start` hook required for end-to-end effectiveness is in flight."
- `experimental`, `planned`, `in flight`, `deferred`, `aspirational` features use future tense or hedged language: "FilterSet will provide...", "permissions.py is reserved for...".

Rule of thumb: if a Django developer reading the section would assume they can use the feature today, the marker must support that assumption. If reading the marker would tell them "no, not yet", the language must agree.

### When to amend this spec

Every future subsystem spec (filters, orders, aggregates, permissions, connection field, relay interfaces, `Meta.primary`, consumer overrides) should:

- Pick a starting marker for its subsystem in the README.
- Specify the migration path through the markers as the work lands (`planned` -> `in flight` -> `partial` -> `shipped`).
- List the test surface that pins its `shipped` contract.
- Reference this spec for the rules.

If a future change introduces a marker that isn't in this spec — for example, a deprecation marker — the marker is added here in the same change. The vocabulary is single-sourced.

## Coordination with other specs

- `spec-django_types.md` and `spec-optimizer.md` define the implementations. This spec defines the rules that govern when those implementations show up in the public surface.
- `spec-django_type_contract.md` defines the contract boundary for `DjangoType` itself. This spec extends that to the package level.
- The optimizer-visibility decision specifically is amended into `spec-optimizer.md` "Visibility status" so the optimizer spec carries the local context for its own re-export trajectory; this spec carries the rule that produced the decision.
- Future subsystem specs plug into this spec by following the migration path described above.

## Open questions

None blocking 0.0.3.

## References

- `docs/alpha-review-feedback.md` — recommendations #1 (silent acceptance), #2 (README aspirational), #7 (docs gap), #8 (alpha guarantees).
- `docs/spec-django_type_contract.md` — companion spec for the DjangoType-side contract.
- `docs/spec-optimizer.md` — carries the local visibility-status amendment that this spec governs.
- `docs/README.md` — the surface this spec governs.
- `django_strawberry_framework/__init__.py` — the canonical top-level surface.
