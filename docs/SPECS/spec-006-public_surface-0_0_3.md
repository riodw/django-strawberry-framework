# Spec: Public Surface & Documentation Discipline

Deliberation and this spec's change record live in its companion [rationale file][spec-006-rationale]: where the alignment problem came from, the three-section README shape this spec declined, and the release-gating judgement an `Open questions` section once recorded.

## Problem statement

The package's public surface — what's re-exported from `django_strawberry_framework/__init__.py`, what the documentation describes as shipped, what tests pin as the consumer contract — must stay aligned with the actual implementation. This spec records the promotion discipline that keeps the three aligned and the vocabulary the documentation states status in.

The fix is not more documentation. It is stricter documentation discipline. This spec defines the rules that govern what gets promoted to the public surface and how the surface is described. With those rules in place, README updates, optimizer-visibility decisions, and any future "is X shipped?" judgment call all reduce to applying the rules.

## Where the public surface is defined

This spec carries the rules, not the roster. Three surfaces carry the roster, and a name is public only when all three agree about it:

- `django_strawberry_framework/__init__.py` — `__all__` is the surface itself, and adding a name to it is what promotion means.
- `tests/base/test_init.py::test_public_api_surface_is_pinned` — pins that tuple verbatim, so no name enters or leaves the surface as a side effect of another change. This is the executable source of the roster.
- `docs/GLOSSARY.md` `## Public exports` — the documented surface, grouped by import path. One group lists the names re-exported from the package root, one bullet each; the other groups list what a subpackage or submodule exposes under its own dotted path. Every bullet reaches a per-feature entry carrying the marker the name is documented under — by a link on the name, or by one inside its gloss when that entry serves several names or documents the behavior the name wraps — so a bullet is what documents a name and the group it sits in is what states which import surface the name is on.

`__all__` is not the whole consumer surface. A `Meta` key such as [`Meta.primary`][glossary-metaprimary] is consumer-visible without being an exported name, and the documentation rules below govern it identically.

Two categories sit outside `__all__` by design, and neither is a gap in it: a family whose subpackage or leaf-module import path is itself the opt-in boundary (`### When a subsystem is top-level vs subpackage-only`), and a name behind a soft dependency, which stays resolvable by attribute access on the package while staying out of `__all__` so `from django_strawberry_framework import *` never imports the optional distribution (`spec-039-serializer_mutations-0_0_13.md`).

## Goal

A public surface and documentation contract that:

- Says exactly what works today, with no aspirational language masquerading as current-state.
- Makes it impossible to accidentally import a feature that isn't effective end-to-end.
- Has a single named status vocabulary so contributors and consumers read the same words the same way.
- Reduces every future "is X shipped?" decision to applying the rules in this spec.

## Non-goals

This spec does not redesign the package layout — that lives in `docs/TREE.md`, which keeps the on-disk and target module layouts side by side, and in the per-subsystem spec docs. It defines the rules that govern when each piece of the layout becomes consumer-visible.

## Topics

### Top-level re-export rule

`django_strawberry_framework/__init__.py` re-exports a name only when **all four** are true:

1. The implementation is shipped — the symbol exists in the package and the code path it represents is effective end-to-end. Not stubbed. Not behind a known-broken hook.
2. The behavior is tested — at least one test pins the consumer-visible contract; not "covered as a side effect of an integration test".
3. The contract is documented — the symbol carries a bullet in the root re-export group of `docs/GLOSSARY.md` `## Public exports`, linking a per-feature entry whose status marker reads `shipped`. A bullet in one of that section's per-subpackage groups documents the symbol but does not satisfy this condition: it records the import path as the surface, which is the opposite placement.
4. The naming is stable enough to honor for the rest of the alpha — renaming requires a deprecation cycle.

**The four conditions are requirements, never entitlements.** A family may satisfy every one of them and still stay out of the root namespace, when the owning spec makes its import path the opt-in boundary; `### When a subsystem is top-level vs subpackage-only` states when that applies. So the four conditions decide whether a name *may* be promoted, and the boundary rule decides whether it *is*.

Names that fail any of these stay reachable via their dotted submodule path (`from django_strawberry_framework.<subpackage> import <Name>`) so power users and tests can still get them, but they are not in the top-level namespace. For a family whose import path is the boundary, that same dotted path is the contract rather than a consolation for having failed a condition — the two cases are reached from opposite directions and are told apart by the owning spec, never by the import form.

#### Decision for 0.0.3

[`DjangoOptimizerExtension`][glossary-djangooptimizerextension] and the typed per-relation override wrapper [`OptimizerHint`][glossary-optimizerhint] are top-level-exported because the optimizer is effective end-to-end rather than stubbed or gated behind a known-broken hook: the root-gated resolve hook, nested prefetch chains, column projection, the custom-`get_queryset` downgrade to `Prefetch`, hints, plan introspection, [schema audit][glossary-schema-audit], field metadata caching, and [queryset diffing][glossary-queryset-diffing] are implemented and covered. `spec-002-optimizer-0_0_2.md` is where that record is kept slice by slice; this spec applies the rule to it.

```
from django_strawberry_framework import DjangoOptimizerExtension, OptimizerHint
```

The subpackage paths also remain supported:

```
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.optimizer.hints import OptimizerHint
```

Promotion is performed by adding the name to `__all__`, whose membership is pinned where `## Where the public surface is defined` says it is; this spec does not carry a copy of the tuple.

### When a subsystem is top-level vs subpackage-only

Subpackages exist for code organization (`types/`, `optimizer/`, `filters/`, `orders/`, and so on) regardless of whether they're top-level-exported. The promotion path for a consumer-facing class:

- A subsystem starts as a subpackage with an `__init__.py` that re-exports its consumer-facing names internally. Consumers reach it via `from django_strawberry_framework.<subpackage> import <Name>`.
- When the subsystem meets all four top-level re-export rules above, its primary consumer-facing names are added to `django_strawberry_framework/__init__.py`'s `__all__`.
- The subpackage `__init__.py` keeps its own re-exports too, so both import paths continue working.

**A subsystem may keep the subpackage path as its only path, and the choice belongs to the spec that ships it.** When importing a subsystem has a consequence a consumer must opt into — pulling in an optional distribution, importing `django.contrib.auth` machinery, or enabling a surface that must never be on by default in production — the import path *is* the opt-in, and promoting the name would take that choice away by making the import implicit. Such a subsystem states the decision and its reason in its own spec, keeps its names out of `__all__`, and documents them in `docs/GLOSSARY.md` under the import path that is the boundary — as one of `## Public exports`' per-subpackage groups, or with the dotted path stated in the family's own entry — never in that section's root re-export group. This is a deliberate placement, not a failed promotion, and nothing in this spec overrides it.

Internal helpers — factories, walkers, individual `Filter` / `Order` / aggregate primitives, converters — never get top-level re-exports. They stay reachable via their submodule path (`from django_strawberry_framework.filters.factories import ...`) for power users and tests; they are not in `__all__`.

### How status is published

**No consumer-visible entry without a marker.** A capability a consumer can read about must carry a status marker wherever it is described, and the marker must be readable without inferring it from tense, section placement, or the surrounding prose.

Two documents publish the markers, and both are generated from a database, never hand-maintained, so a marker cannot drift from the record behind it:

- `docs/GLOSSARY.md` — one entry per public symbol, `Meta` key, configuration argument, and named behavior, each carrying its own status marker stamped with the release the marker is true of. This is the per-feature locus, and the one the re-export rule's documentation condition reads.
- `docs/TREE.md` — the module layouts, kept as two trees: what is on disk, and the target shape with each not-yet-existing entry naming the card that will ship it. Naming the card satisfies this rule: it resolves to a target release, which a bare marker does not.

**Prose elsewhere in the documentation — the onboarding README, the capability snapshot — may not publish a marker of its own; it points at the per-feature locus, which is how a capability described there stays marked.** Any status word such prose does use comes from the legend `### Status-marker vocabulary` delegates to, and is read at the scope it is written at: a release-scoped summary over a group of capabilities says where the group stands and is not a per-feature marker for anything inside it. Such prose stays subject to `### Alpha signaling rules`: its language may not claim more than the marker it points at.

The rejected three-section README shape, and why sectioning lost to per-entry markers, are in the [rationale file][spec-006-rationale].

### Status-marker vocabulary

The vocabulary is single-sourced, and this spec is not the source. `docs/GLOSSARY.md` `## Status legend` carries every marker with its meaning, and it renders from the glossary database, so the legend and the markers stamped on individual entries cannot disagree. Every consumer-visible feature mention — in `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/README.md`, `TODAY.md`, or any spec doc — uses a marker from that legend. No synonyms, no improvisation.

Two properties of the legend are load-bearing for the rules in this spec, so a change to either is a change to this spec's gate:

- **A marker names a release, not only a state.** `shipped` is stamped with the version it shipped in and an unshipped marker with the version it is committed to. The re-export rule's condition 3 reads that stamp, not the bare word.
- **A marker is attached to the feature's own entry, never to a document or a section.** A section boundary is not a marker and does not substitute for one.

A `Meta` key held back for a later spec is published as `deferred`. Which keys those are, and what accepting or rejecting one means, is the contract of `spec-005-django_type_contract-0_0_3.md` "Accepted vs deferred Meta keys" and not this spec's.

### Alpha signaling rules

The language describing a feature must match its marker:

- A `shipped` entry uses present tense without hedging: "[`DjangoType`][glossary-djangotype] generates...", "[`FilterSet`][glossary-filterset] accepts...", "`convert_choices_to_enum` produces...".
- An entry whose marker says the feature is not available yet uses future or hedged language — "will provide...", "is reserved for..." — and names the release or card it is tracked against, so the reader can tell a commitment from a possibility.
- An entry marked `alpha constraint` — available, but narrower than the eventual API — states both halves: what works today and what it does not reach yet. One tense alone is what makes a partial surface read as a whole one.

Rule of thumb: if a Django developer reading the section would assume they can use the feature today, the marker must support that assumption. If reading the marker would tell them "no, not yet", the language must agree.

### What a subsystem spec owes these rules

A subsystem spec satisfies these rules **inside its own change**, against artifacts that hold their shape, and it does not amend this document to do so:

- Publish the subsystem's entry with a status marker, in the same change that ships the behavior the marker claims. That is the documentation condition, and it is where the migration from an unshipped marker to `shipped` actually happens.
- Land the test that pins the consumer-visible contract, and — for a promoted name — the change to the pinned export tuple. A promotion no test records is not a promotion.
- State whether its consumer-facing names are promoted, or whether its own import path is the opt-in boundary, and give the reason. That decision is the owning spec's to make and this spec's to license; leaving it unstated is what makes an export look accidental.
- Add a marker the legend does not carry to the legend and the record it renders from — never to this spec, which would make a second source of the vocabulary.

**Each obligation is discharged against the code, the tests, or the generated docs, because those can be checked. Do not add an obligation to come back and edit this spec: nothing can check it.**

## Coordination with other specs

- `spec-001-django_types-0_0_1.md` and `spec-002-optimizer-0_0_2.md` define the implementations. This spec defines the rules that govern when those implementations show up in the public surface.
- `spec-005-django_type_contract-0_0_3.md` defines the contract boundary for `DjangoType` itself. This spec extends that to the package level.
- Every decision about which names a subsystem makes public is recorded once, in the spec that ships the subsystem. This spec owns the rule and the exported roster's location; it does not hold a second copy of any subsystem's placement decision, and no subsystem spec restates the roster.
- Future subsystem specs plug into this spec by discharging `### What a subsystem spec owes these rules` in their own change.

## References

- `docs/SPECS/spec-005-django_type_contract-0_0_3.md` — companion spec for the DjangoType-side contract.
- `docs/SPECS/spec-002-optimizer-0_0_2.md` — the optimizer subsystem whose public entry point `#### Decision for 0.0.3` applies the re-export rule to.
- `docs/GLOSSARY.md` — the documented surface and the status vocabulary both rules above read.
- `docs/README.md` and `TODAY.md` — the consumer-facing prose `### Alpha signaling rules` governs.
- `django_strawberry_framework/__init__.py` — the canonical top-level surface.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-queryset-diffing]: ../GLOSSARY.md#queryset-diffing
[glossary-schema-audit]: ../GLOSSARY.md#schema-audit

<!-- docs/SPECS/ -->
[spec-006-rationale]: appx/spec-006-public_surface-0_0_3-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
