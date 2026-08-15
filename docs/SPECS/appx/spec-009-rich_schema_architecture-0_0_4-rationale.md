# Rationale: spec-009 — rich schema architecture (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-009-rich_schema_architecture-0_0_4.md`][spec-009]. The spec states
the long-term layered architecture the package is built toward; everything that explains **how a
claim in it came to be falsified and corrected** lives here — the text cut out of the spec, the
evidence that falsified it, and the alternative each correction rejected.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass, long after the
release rather than before the build. Card `DONE-009-0.0.4` shipped many minor versions ago and the
rule that gates a build on this move did not exist then. Text marked *Moved* below was cut out of the
spec, not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec section**, named by the section's own heading. A section with no entry here
  lost nothing to this pass — that is not an omission.
- **This spec is a design horizon, not a contract.** It describes eleven layers, most of which have
  since shipped under their own specs. It is deliberately not the owner of any shipped behavior, so
  a reader looking for what the package *does* wants [`docs/GLOSSARY.md`][glossary] and the
  per-feature specs, never this one.
- **The corrections here are unusually load-bearing for a horizon document.** One of them —
  `### Layer 3: Finalization trigger` — described a mechanism that was rejected before the
  foundation slice shipped, and described it as preferred. Two further sections repeated it. A
  reader designing against the spec would have designed against a mechanism that has never existed.
- **In-repo citations are symbol-qualified**, per `AGENTS.md` rule 27. The spec carried twelve raw
  `path:NN` citations, one per line, all of them in-repo; every one was converted.

## Provenance of this record

Every claim below was re-derived against the working tree at the time of the pass. The central
one — that nothing in the package auto-triggers finalization — was established by grepping the whole
package for calls to `finalize_django_types()` and confirming that the only occurrences are prose in
docstrings, with no call site outside the consumer's own code. It was *not* carried from the
spec-008 cycle's report, though that cycle reached the same conclusion independently.

## Entries keyed to the spec

### `### Layer 3: Finalization trigger` — the rejected mechanism, stated as preferred

*Moved.* The spec carried this:

> Preferred triggers:
>
> 1. `DjangoConnectionField(Type)` calls `finalize_django_types()` before it returns a field.
> 2. `DjangoNodeField(Type)` calls `finalize_django_types()` before it returns a field.
> 3. `DjangoSchema(...)` calls `finalize_django_types()` before constructing `strawberry.Schema`.
> 4. `finalize_django_types()` remains public for advanced users.
>
> Why this combination:
>
> - cookbook-style schemas define node types first and root fields after, so `DjangoConnectionField`
>   can finalize naturally
> - direct manual schemas can use `DjangoSchema`
> - advanced users can call the finalizer explicitly in tests or unusual import layouts

**What actually shipped.** Only item 4. `DjangoConnectionField`, `DjangoNodeField` and `DjangoSchema`
all exist and none of them calls the finalizer; the explicit consumer call is the sole trigger, and
`spec-010-foundation-0_0_4.md` #"## Strawberry finalization strategy" states so in terms — "no
shipped helper auto-triggers finalization". Items 1-3 were rejected before the foundation slice
landed.

**Why the combination lost.** Two reasons, and the first is fatal on its own.

1. *It reintroduces the coupling the architecture exists to remove.* If constructing a connection
   field finalizes, then whether a given `DjangoType` is included depends on whether its module was
   imported before that construction — which is import-order coupling wearing a different hat. The
   package's whole premise is that schema shape must never depend on declaration or import order.
   A trigger that fires on the first construction of any of three unrelated objects makes the
   finalization boundary implicit and position-dependent, which is precisely the failure mode
   [definition-order independence][glossary-definition-order-independence] is named after.
2. *It puts a process-global mutation behind three constructors.* `finalize_django_types()` mutates a
   process-global registry and mutates class objects, and the registry is deliberately lockless.
   Spec-010 pins the finalizer to a single-threaded setup window for that reason. Three separate
   auto-trigger sites multiply the number of places that window can be violated, and none of the
   three constructors is in a position to enforce it.

**What was kept.** The fourth bullet of "Why this combination" — that finalization must happen before
Strawberry schema conversion, so no post-schema patching is needed — is a genuine requirement rather
than an argument for the rejected mechanism, and it survives in the rewritten section alongside the
reason a schema extension cannot be the trigger.

**The constraint the rejection leaves behind** is stated in the spec rather than here, because it
binds future work: any helper that ever auto-triggers finalization must also enforce the
single-threaded setup window, by being constrained to schema-construction time or by acquiring a real
lock.

### `### Decision 2: explicit package finalizer` — the same falsification, in one clause

*Moved.* The decision read:

> Add `finalize_django_types()` and call it from package-owned schema/field helpers.

The first half shipped; the second half is the rejected auto-trigger in six words. It is recorded
separately from the Layer 3 entry because of how it was found: the Layer 3 correction was made first,
and this clause survived it, three hundred lines away in a section a reader would reasonably treat as
the authoritative summary. A correction applied at the site where a claim is *argued* does not reach
the site where it is *asserted*, and the numbered-decision list is exactly where a hurried reader
looks.

### `## Open questions` — two answers falsified, one settled by shipping

Three of the five questions had been overtaken by shipped work.

- *Should plain `strawberry.Schema` remain fully supported?* The old answer — "yes for simple
  schemas, but rich schemas should use `DjangoSchema` or package-owned fields that finalize before
  schema construction" — is the Layer 3 falsification a third time, and it carried a real cost: it
  told consumers that plain `strawberry.Schema` was a second-class path. It is not. Because the
  trigger lives in neither the schema nor the field objects, every schema shape works identically
  once the consumer has called the finalizer, and choosing `DjangoSchema` is a richness decision with
  no bearing on finalization.
- *Should multiple `DjangoType`s per model be allowed?* Settled by [`Meta.primary`][glossary-metaprimary]
  in `0.0.6`. The rewritten answer states the shipped shape — many types per model, exactly one
  primary, ambiguity refused rather than guessed — and points at
  [`spec-018-meta_primary-0_0_6.md`][spec-018] for the contract. The three refusal sites were
  verified in `registry.py` and `types/finalizer.py` rather than taken from the card.
- *Should filters/orders/aggregates copy Graphene names exactly?* Settled for filters and orders,
  which shipped in `0.0.8` under [`spec-027`][spec-027] and [`spec-028`][spec-028] following exactly
  the rule this section stated. Left open for aggregates, which have not shipped. Splitting the
  answer was deliberate: collapsing it to "settled" would have claimed a record for a subsystem that
  does not exist yet.

The two remaining questions — generic fallback, and whether sentinel redaction is required — were
re-checked and left alone. Both answers still hold.

### `## Current local package baseline` → `## The 0.0.4 local package baseline`

The section is a snapshot of the package as it stood when the spec was authored, and it was headed
and worded as though it described the package now. Every line number in it had rotted, and two of the
thirteen functions it listed as "Important current functions" no longer exist.

The correction anchors the section to the moment it describes rather than rewriting it to the present.
That is the right direction for a design horizon: the layers below were designed against *that*
baseline, so replacing it with today's inventory would break the argument the rest of the document
makes. The rejected alternative was deleting the section outright, which would have left the layer
designs with no stated starting point.

Two entries carry an explicit **retired since** marker rather than being repointed:
`types/converters.py::convert_relation`, whose work is now done by
`types/converters.py::resolved_relation_annotation`, and `registry.py::TypeRegistry.lazy_ref`, the
`NotImplementedError` placeholder the 0.0.4 slice deleted. Marking beats deleting because both names
appear in the layer arguments further down; marking beats repointing because neither replacement is
what the baseline argument was about.

### `### Status: deferred design idea, no card yet` → `### The unresolved-relation contract is error-only`

Two problems, one edit. The heading was status-shaped, which the board has been retiring from specs
since the spec-002 residual cycle — a spec states its contract, and a status line inside it is a
second place for the truth to live. And the status it stated, "no card yet", is a claim about the
board that no spec can keep true.

The substance was re-measured and kept: `Meta.unresolved_relations` is still uncarded, and the
error-only contract still holds. Only the framing changed, from a status report about a deferred idea
to a statement of the contract that is actually in force, with the wording delegated to
[`spec-010`][spec-010].

### `## Migration path from current package` → `## Migration path from the 0.0.4 baseline`

Eight numbered phases, several of them long since shipped, presented as a forward plan. The
correction adds one sentence establishing what the list is — a dependency order drawn from the
baseline above, not a schedule — and stating that the spec does not track which phases have shipped.

This follows the disposition the spec-003 residual cycle set and recorded in its own companion: a
spec states its contract and never narrates its own shipping status. The rejected alternative was
annotating each phase with its shipped version, which would have made the section a second, unowned
copy of the board and guaranteed it would drift.

## Standing notes

- **The Layer 3 falsification had three sites, not one.** It was argued in `### Layer 3`, asserted in
  `### Decision 2`, and assumed in an `## Open questions` answer. Any future correction to a claim in
  this spec should assume the same shape: a horizon document states its positions more than once, in
  a layer section, a decision line and an open-question answer, and fixing only the argued site
  leaves the assertion standing where readers are most likely to trust it.
- **This spec owns no shipped behavior.** Every correction above moved it further from describing the
  package and closer to describing the design intent. That is the correct direction for it. If a
  future reader finds this document and the code disagreeing, the code and the owning spec win, and
  the fix is here rather than there.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../../GLOSSARY.md
[glossary-definition-order-independence]: ../../GLOSSARY.md#definition-order-independence
[glossary-metaprimary]: ../../GLOSSARY.md#metaprimary

<!-- docs/SPECS/ -->
[spec-009]: ../spec-009-rich_schema_architecture-0_0_4.md
[spec-010]: ../spec-010-foundation-0_0_4.md
[spec-018]: ../spec-018-meta_primary-0_0_6.md
[spec-027]: ../spec-027-filters-0_0_8.md
[spec-028]: ../spec-028-orders-0_0_8.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
