# Rationale: spec-008 — definition-order independence (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-008-definition_order_independence-0_0_4.md`][spec-008]. The spec
states the problem and the constraints any solution had to hold; everything that explains **how the
decision was reached and how it fared** lives here: the upstream source tours that supplied the
evidence, the alternatives each choice rejected and why each lost, and every claim the spec once
made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the release, not before the build.** Card `DONE-008-0.0.4` shipped ten minor
versions ago and the rule that gates a build on this move did not exist then; this pass supplies it.
Text marked *Moved* below was cut out of the spec, not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec section**, named by the section's own heading and linked to its anchor. A
  section with no entry here lost nothing to this pass — that is not an omission.
- **Who reads it.** Worker 3 reads it during review; Worker 1 owns it; Worker 2 never reads it. A
  reader looking for what the package *does* wants
  [`docs/GLOSSARY.md`][glossary] and [`spec-010-foundation-0_0_4.md`][spec-010], not this file.
- **This spec has no numbered Decisions**, so the key is the heading. Five entries key to headings
  that no longer exist in the spec at all — `### Finalization trigger choices` and the four
  `### … questions` sections, which this pass removed whole. Each anchors the surviving section
  nearest to where it stood and says so.
- **This spec is unusual in the series: it declined, in its own text, to decide anything.** It says
  "This section is not a final implementation plan", titles its conclusion
  `## Current strongest direction, not a final plan`, and frames every mechanism as a question to
  settle. Its deliverable was a *decision*, and the decision was taken and implemented elsewhere, by
  [`spec-010-foundation-0_0_4.md`][spec-010]. So the majority of the document is deliberation by
  construction, and the rationale is where most of it belongs.
- **Do not read this file as a description of the shipped machinery.** The `finalize_django_types()`
  contract, its phase order, the `PendingRelation` shape, and the registry extensions are
  [`spec-010`][spec-010]'s and the [glossary][glossary]'s. What is recorded here is only what
  **spec-008 predicted and weighed**, and how each prediction fared.
- **Upstream citations are symbol-qualified**, per `AGENTS.md` rule 27. The spec carried
  thirty-one raw `path:NN` citations into two third-party checkouts outside this repository — 25 of
  them the only citation on their line, and six more riding as bare backticked continuation integers
  on three of those lines, which is why a line-counting grep sees only 25; a
  `-rationale.md` is not on rule 27's scratchpad list, so moving them did not launder them and every
  one was converted here. Two checkout roots are used below and are named once:
  **[G]** = `~/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/`, and
  **[S]** = `~/projects/strawberry-django-main/`.

## Provenance of this record

- **Moved** — cut from the spec by this pass, and now only here: both prior-art sections' "Source
  snapshot inspected" and "Key source references" lists, their worked examples, and their `### Pros`
  / `### Cons` lists; the `## Design options for this package` "not a final implementation plan"
  paragraph and the whole of `### Decision criteria`; the Pros / Cons lists of all four
  `### Option N` sections; and the whole of `### Finalization trigger choices`,
  `### Registry questions`, `### User annotation questions`, `### Generic fallback questions`, and
  `### Rich-schema dependency questions`.
- **Condensed rather than moved — the one place this pass wrote new spec prose.** Under the
  maintainer decision recorded on this cycle, condensed prior art **stays** in the spec: the two
  upstream approaches, and what this package borrowed from and avoided in each. Emptying the spec of
  prior art would have falsified [`spec-010`][spec-010]'s own inbound description of it
  (`#"discusses the relation-resolution problem space and prior art at length"`) in the same change
  that was supposed to make the cluster consistent. So each prior-art section's opening was rewritten
  to state the mechanism and its failure mode directly, and both `### Relevance to this package`
  subsections — the borrow / avoid lists, which are conclusions rather than evidence — were left
  untouched.
- **Deliberately left in the spec by this pass, and the list is exhaustive.**
  `## Current strongest direction, not a final plan`'s opening two paragraphs and its "target
  behavior" list, `### Hard invariants`, `### Proposed shape to evaluate`, `## Acceptance criteria`,
  `### Failure criteria`, `## Fakeshop implication`, `## Cookbook implication`, and
  `## Decision context to preserve`. Each is either the statement of *which* option won (removing it
  would leave the spec with no outcome at all), a constraint list that reads as contract rather than
  as argument, or a section the reconciliation item demotes to a pointer at the document that now
  owns it — a disposition this pass has no authority to pre-empt.
- **Nothing was deleted outright by this pass.** `worker-1.md` rule 2 deletes rather than moves
  prose the current decisions have falsified. Nothing in spec-008 is falsified by spec-008: the
  document is internally consistent, and it was falsified by the package, which is a different
  question and the reconciliation item's. Where a moved block is recorded against HEAD below, that is
  because the block's whole content is a prediction and its fate is the only thing worth recording
  about it.
- **All three of the spec's fenced code blocks were disposed of, none deleted.** Two moved here with
  their sections — the Graphene class-order example and the Strawberry explicit-annotation example;
  the one one-line fence (the `registry.get_type_for_model(model)` call) was folded into the
  condensed prose as an inline code span. The spec now carries none and this file carries two. The
  unit matters: `grep -c '^```'` counts fence **delimiter** lines, of which the spec had six, and a
  block is two of them.
- **All ten glossary anchors survive.** Four sat inside text this pass moved
  (`Meta.fields` in Option 4's Pros, `finalize_django_types` in the finalization-trigger list, and
  `Meta.primary` and `schema audit` in two of the question sections). Each was re-sited into
  surviving prose in the same edit that removed its carrier, by changing an existing sentence's link
  form rather than by adding narration or leaving a hollow section behind to host a link.

## Entries keyed to the spec

### `## Prior art: Graphene-Django` — the source tour, the worked example, and the Pros / Cons weighing

Spec: [Prior art: Graphene-Django][spec-008-graphene].

*Moved — the source snapshot inspected.* Five files under **[G]**: `graphene_django/types.py`,
`graphene_django/converter.py`, `graphene_django/registry.py`, `graphene/types/dynamic.py`, and
`graphene/types/schema.py`.

*Moved — the key source references, converted to symbol-qualified form.* The spec cited each of
these by raw line number; the line numbers were still accurate when this pass re-read the checkout,
which is luck rather than a property of the citation form.

- `graphene_django/types.py::DjangoObjectType.__init_subclass_with_meta__ #"construct_fields(model, registry, fields, exclude, convert_choices_to_enum)"`
  builds the Django fields.
- `graphene_django/types.py::DjangoObjectType.__init_subclass_with_meta__ #"registry.register(cls)"`
  registers the `DjangoObjectType` **after** field construction — the ordering that makes deferral
  necessary.
- `graphene_django/registry.py::Registry.register` registers a type by model.
- `graphene_django/registry.py::Registry.get_type_for_model` returns the type for a model.
- The three relation converters are
  `graphene_django/converter.py::convert_onetoone_field_to_djangomodel` (reverse `OneToOneRel`),
  `graphene_django/converter.py::convert_field_to_list_or_connection` (`ManyToManyField`,
  `ManyToManyRel`, `ManyToOneRel`), and
  `graphene_django/converter.py::convert_field_to_djangomodel` (`OneToOneField`, `ForeignKey`).
- Each of those three ends `#"return Dynamic(dynamic_type)"` — the placeholder return that is the
  whole mechanism.
- `graphene/types/dynamic.py::Dynamic` defines the placeholder;
  `graphene/types/dynamic.py::Dynamic.get_type` resolves it.
- `graphene/types/schema.py::TypeMap.create_fields_for_type #"if isinstance(field, Dynamic)"`
  resolves `Dynamic` fields while building the schema and **skips the field** when the dynamic
  function returns nothing.

*Moved — the worked example, in full.* The spec showed that this class order works under
Graphene-Django:

```python
class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = ("id", "items")


class ItemType(DjangoObjectType):
    class Meta:
        model = Item
        fields = ("id", "category")
```

with the note that "`CategoryType.items` is initially a dynamic placeholder. When the Graphene schema
builds, the placeholder resolves `Item` through the registry." Its two load-bearing facts — either
declaration order works, and a never-registered target becomes a silently skipped field — survive in
the condensed section, which is why the example itself is evidence rather than contract.

*Moved — the `### Pros` list, verbatim.* "Supports bidirectional rich model graphs without requiring
declaration order. / Keeps automatic relation typing: relation fields become the concrete related
Graphene type when available. / Avoids needing a generic fallback object for normal relation fields.
/ Works naturally with Graphene's own schema-building lifecycle."

*Moved — the `### Cons` list, verbatim.* "Missing target types can become skipped fields rather than
immediate class-definition errors. / Errors move later, from class creation to schema build or
introspection. / The dynamic placeholder is Graphene-specific; Strawberry does not expose the same
exact field lifecycle. / The registry must tolerate incomplete graphs during class creation."

*Con 3 was priced as a blocker and turned out not to be one.* It is true as stated — Strawberry
exposes no equivalent of Graphene's field-mounting lifecycle — and the package built a
Strawberry-native equivalent anyway: `types/relations.py::PendingRelationAnnotation`, a sentinel
class whose metaclass `__repr__` names itself as unfinalized and which the finalizer rewrites in
place. The "parts to avoid" list was right to rule out porting `graphene.Dynamic`; what it could not
know is that the *pattern* ported cleanly without the substrate. Cons 2 and 4 were accepted
deliberately and shipped: errors do move later, and the registry does tolerate incomplete graphs
until finalization. Con 1 is the one the package refused outright — see the hard invariant against
silent field skipping.

*Claims the section no longer makes.* That any Graphene or `graphene_django` line number is a
resolvable citation; that the Pros / Cons balance is an open weighing rather than a settled one.

### `## Prior art: Strawberry-Django` — the source tour, both mode examples, and the Pros / Cons weighing

Spec: [Prior art: Strawberry-Django][spec-008-strawberry].

*Moved — the source snapshot inspected.* Five files under **[S]**: `strawberry_django/type.py`,
`strawberry_django/fields/base.py`, `strawberry_django/fields/types.py`,
`strawberry_django/utils/typing.py`, and `tests/types.py`.

*Moved — the key source references, converted to symbol-qualified form.* All seven `type.py`
citations sit inside one function, which the raw line numbers concealed:

- `strawberry_django/type.py::_process_type #"cls_annotations[f.name] = strawberry.auto"` injects
  `strawberry.auto` for model fields.
- `strawberry_django/type.py::_process_type #"strawberry.type(cls, **kwargs)"` performs the
  Strawberry decoration.
- `strawberry_django/type.py::_process_type #"for f in type_def.fields:"` post-processes the
  Strawberry fields.
- `strawberry_django/type.py::_process_type #"if f.name in auto_fields:"` detects fields that came
  from `auto`.
- `strawberry_django/type.py::_process_type #"f.type_annotation = type_annotation"` updates the
  Django field annotation and description.
- `strawberry_django/type.py::_process_type #"f.origin_django_type = django_type"` records the origin
  Django type on each field.
- `strawberry_django/type.py::_process_type #"cls.__strawberry_django_definition__ = django_type"`
  stores the definition.
- `strawberry_django/fields/base.py::StrawberryDjangoFieldBase.resolve_type` resolves `auto` field
  types.
- `strawberry_django/fields/types.py #"field_type_map: dict["` defines the Django model-field type
  map; inside it, `#"related.ForeignKey: DjangoModelType"` maps `ForeignKey` to the generic type and
  `#"reverse_related.ManyToOneRel: list[DjangoModelType]"` maps reverse FK to a list of it.
- `strawberry_django/utils/typing.py::get_strawberry_annotations` preserves the declaring module's
  namespace through `StrawberryAnnotation` — the three cited lines are its `def` line, its
  `namespace = sys.modules[c.__module__].__dict__` read, and its
  `StrawberryAnnotation(v, namespace=namespace)` construction.
- `tests/types.py #"from __future__ import annotations"` enables postponed annotations;
  `tests/types.py::Fruit #"color: Color | None"` references `Color` before it is declared;
  `tests/types.py::Color #"fruits: list[Fruit]"` references `Fruit` from the reverse side; and
  `tests/types.py::User` / `::Group` / `::Tag` show a second cyclic graph built the same way.

*Moved — the explicit-annotation-mode example, in full.*

```python
from __future__ import annotations

@strawberry_django.type(models.Fruit)
class Fruit:
    color: Color | None


@strawberry_django.type(models.Color)
class Color:
    fruits: list[Fruit]
```

*Moved — the `auto`-mode fallback table.* "`ForeignKey` -> `DjangoModelType` / reverse FK ->
`list[DjangoModelType]` / relation fields under relay settings -> `relay.Node` or lists of
`relay.Node`." The condensed section keeps all three mappings in prose, because the shape of the
fallback is exactly what this package rejected as a default and the rejection is unreadable without
it.

*Moved — the `### Pros` list, verbatim.* "Fits Strawberry's annotation-driven design. / Explicit
relation annotations support rich cyclic graphs through postponed annotations. / `auto` remains safe
without requiring every related type to be known. / Missing concrete target types do not block type
creation when using `auto`."

*Moved — the `### Cons` list, verbatim.* "Fully automatic relation fields do not become the concrete
related type by default. / Users must explicitly annotate rich relations. / DRF-style
`fields="__all__"` does not produce the same rich relation graph that this package aims to produce. /
Generic `DjangoModelType` is less useful for nested querying."

*The Cons are the whole reason this package exists, and they held.* No generic relation fallback ever
shipped here: `DjangoModelType` has zero occurrences in the package through `0.0.14`, and automatic
`Meta.fields = "__all__"` relations resolve to the concrete related `DjangoType`. The Pros were also
right, and were taken: the package borrowed the annotation-namespace handling and the
post-`strawberry.type` field rewrite wholesale, which is what the surviving
`### Relevance to this package` list says.

*Claims the section no longer makes.* That any `strawberry_django` line number is a resolvable
citation; that the choice between the two upstream relation modes is open.

### `## Design options for this package` and `### Decision criteria` — the yardstick, and the disclaimer that made the spec a design record

Spec: [Design options for this package][spec-008-options].

*Moved — the disclaimer, verbatim.* "This section is not a final implementation plan. It exists to
preserve enough context to make the best decision before implementation."

That sentence is small and it decided how this whole document is read. It is the clearest statement
of the thing that distinguishes spec-008 from every sibling: it is a design record whose deliverable
was a decision, not a contract, and the contract was written elsewhere. The ownership boundary this
cycle settled — spec-008 owns the problem and the analysis, [`spec-010`][spec-010] owns every shipped
contract, `spec-001` owns what subclass creation collects — rests directly on it. Recorded here
rather than deleted for that reason.

*Moved — the thirteen decision criteria, verbatim.* "supports cookbook-style rich schemas / supports
fakeshop-style bidirectional model graphs / preserves concrete related `DjangoType`s by default /
keeps `Meta.fields = "__all__"` useful / fails loudly before serving an incomplete schema / avoids
Graphene runtime dependencies / avoids generic relation placeholders as the default schema shape /
works with Strawberry's type lifecycle instead of fighting it / preserves explicit Strawberry
annotations as an override path / keeps the optimizer able to inspect concrete relation metadata /
creates a foundation for related filters, orders, aggregates, fieldsets, permissions, and connections
/ minimizes boilerplate for users / avoids fragile post-schema mutation when a cleaner pre-schema
lifecycle is possible."

*The criteria are the reason the four-option comparison is legible at all, and they were not
neutral.* Six of the thirteen are prohibitions on the two upstream approaches: three worded as such
("avoids Graphene runtime dependencies", "avoids generic relation placeholders as the default schema
shape", "avoids fragile post-schema mutation when a cleaner pre-schema lifecycle is possible") and
three the same prohibition stated positively ("preserves concrete related `DjangoType`s by default",
"keeps the optimizer able to inspect concrete relation metadata", "fails loudly before serving an
incomplete schema"). That is why Options 1 through 3 could not win on any reading. That is not a
defect in the list; it is the list doing its job, since the prohibitions come from `GOAL.md` rather
than from this spec's own preference. But a reader who sees only the four options and not the
criteria will read the choice as looser than it was.

*The criteria are also the closest thing this spec has to a durable contribution that outlived it.*
Every one of the thirteen still holds at HEAD, and the two that are absence-shaped and therefore
easiest to erode without noticing — zero Graphene imports, zero generic-fallback types — were
verified directly rather than assumed during this cycle's read-only audit.

*Claims the section no longer makes.* That a design decision remains to be made; that context is
being preserved *before* implementation.

### `### Option 1` through `### Option 4` — the four candidate designs, and why three lost

Spec: [Option 1][spec-008-option1] · [Option 2][spec-008-option2] · [Option 3][spec-008-option3] ·
[Option 4][spec-008-option4]. Each section's descriptive sentence stays in the spec; the Pros and
Cons moved.

**Option 1 — keep eager resolution.** *Moved, Pros:* "Small implementation. / Fail-loud at class
creation. / No schema-finalization complexity. / Current optimizer can assume relation targets are
concrete." *Moved, Cons:* "Bidirectional schemas remain awkward. / `fields="__all__"` cannot
represent normal Django graphs. / Fakeshop cannot expose both `Category.items` and `Item.category` on
the primary types." **Why it lost:** the third con is the spec's whole problem statement restated, so
Option 1 is the null option and loses by definition. Its Pros were nonetheless all preserved by the
winner — the implementation is fail-loud, and the optimizer still sees concrete targets, just after
finalization instead of at class creation.

**Option 2 — Strawberry-Django-style explicit relation annotations.** *Moved, Pros:* "Aligns with
Strawberry's native forward-reference system. / Avoids building a custom lazy relation registry. /
Lets advanced users resolve cycles with `from __future__ import annotations`." *Moved, Cons:* "Moves
away from the package's DRF-first goal. / `Meta.fields = "__all__"` still needs a fallback for
relation fields. / Requires a stable consumer-override contract, which is currently not promised."
**Why it lost:** the first con is disqualifying against `GOAL.md`, and the second says the option does
not actually solve the problem — it relocates it to the `"__all__"` path, which is the path the
package cares most about. **What survived of it:** all three Pros, as an escape hatch rather than as
the default. Every mechanism Option 2 named ships today — same-module string annotations,
`from __future__ import annotations` stringified forms, cross-module
`Annotated[..., strawberry.lazy(...)]`, and annotation-only overrides that keep the generated
resolver. The third con was also discharged: the consumer-override contract that was "currently not
promised" became one, at `0.0.6`, by [`spec-019`][spec-019].

**Option 3 — generic relation fallback.** *Moved, Pros:* "Breaks definition-order cycles. / Keeps
type creation from failing. / Easy to explain as an alpha fallback." *Moved, Cons:* "Relation fields
become less useful. / Nested querying is limited. / The generated schema can silently degrade from
rich relation type to generic placeholder. / It is not the best long-term fit for DRF-shaped
automatic schema generation." **Why it lost:** the third con names a silent degradation, and every
version of silent degradation is refused by the hard-invariant list. It lost so completely that the
spec's own `### Generic fallback questions` section then asked whether it should exist even as an
emergency hatch, and the answer was no — see that entry below.

**Option 4 — Graphene-style deferred relation resolution.** *Moved, Pros:* "Best fit for automatic
rich relation generation. / Preserves DRF-shaped `Meta.fields` behavior. / Supports bidirectional
model graphs. / Keeps the current 'relations become concrete related `DjangoType`s' promise." *Moved,
Cons:* "Requires a package-level pending-relation registry. / Errors move from type creation to a
later finalization point. / Strawberry type definitions may need to be patched or delayed carefully.
/ The optimizer and relation resolver attachment must handle pending targets until finalization."
**Why it won, and how it fared:** it shipped whole at `0.0.4`, and all four of its Cons were paid
exactly as priced rather than discovered later — the pending-relation registry is
`types/relations.py::PendingRelation` plus `registry.py::TypeRegistry.add_pending_relation` /
`iter_pending_relations` / `discard_pending`; the errors did move to finalization; the type
definitions are rewritten in place by the finalizer; and pending targets are carried by
`types/relations.py::PendingRelationAnnotation` until they resolve. An option whose stated costs are
all still visible in the shipped code, under the names it gave them, is the strongest evidence
available that the comparison was made honestly rather than reverse-engineered from a preferred
answer.

*This entry is the only place in the repository where the three rejected designs are recorded at
all.* [`spec-010`][spec-010] closes out one rejected finalization option through its own spike and
otherwise documents only what shipped; nothing else names Options 1 through 3.

*Claims the sections no longer make.* That the comparison is live; that Option 4 is a candidate
rather than the shipped design; that `Meta.fields = "__all__"` behavior is a promise still to be
kept.

### `### Finalization trigger choices` — the section removed, and the one prediction this spec got wrong

Spec: none — the heading was removed. The pointer that replaced it, covering the four candidate
triggers and all four sets of questions, is one sentence in
[The finalization trigger][spec-008-trigger].

Bears on [The finalization trigger][spec-008-trigger], the section that now states the settled
answer, and on [The shape that shipped][spec-008-proposed] and [The decision][spec-008-decision], the
surviving sections either side of where it stood. **This is the most consequential entry in the file:
it is the spec's own stated leading direction being rejected by the implementation.**

*Moved verbatim, the whole section.* "The main unresolved technical question is the Strawberry
finalization point.

Possible approaches:

1. Delay `strawberry.type(cls, ...)` until relation targets are resolved.
2. Finalize immediately with placeholders, then patch `__strawberry_definition__.fields`.
3. Require schema construction through a package helper that finalizes pending relations before
   creating `strawberry.Schema`.
4. Use a hybrid: collect early, finalize through package-owned fields or schema helpers, and keep an
   explicit `finalize_django_types()` escape hatch for tests and advanced import layouts.

The tradeoffs:

- Option 1 may be cleanest if class registration can be separated from Strawberry finalization
  without losing current ergonomics.
- Option 2 preserves normal `strawberry.Schema(...)` usage but couples the package to Strawberry
  internals and risks fragile post-finalization mutation.
- Option 3 is explicit and safe, but adds a new top-level API and may surprise users who expect plain
  `strawberry.Schema`.
- Option 4 probably fits the broader goal best, but it needs careful API design so simple schemas
  remain simple and rich schemas finalize predictably.

The newer rich-schema architecture spec leans toward a hybrid finalization story:

- `DjangoConnectionField(Type)` finalizes before building a rich field.
- `DjangoNodeField(Type)` finalizes before building a node field.
- `DjangoSchema(...)` finalizes before constructing `strawberry.Schema`.
- `finalize_django_types()` remains public for explicit control.

This spec should continue to treat that as the leading direction, not an already proven
implementation."

*The leading direction was rejected. Approach 3 shipped, unmixed.* Nothing in the package
auto-finalizes. `finalize_django_types` has no call site anywhere in
`django_strawberry_framework/` outside its own definition, its re-exports, and docstrings;
`connection.py` and `relay.py` contain none (`connection.py::_finalize_queryset` is queryset
pagination, an unrelated name collision); and `schema.py::DjangoSchema` contains none. The explicit
consumer call is the **sole** trigger, and it is documented as such in
`docs/README.md #"Schema setup boundary"`, in the glossary's `` ## `finalize_django_types` `` entry,
and in `GOAL.md`'s own worked example, which calls it by hand before constructing the schema.

*The retraction, stated plainly: `finalize_django_types()` is not an escape hatch.* Approach 4 cast
it as a hatch "for tests and advanced import layouts" beside a set of preferred implicit triggers.
There are no implicit triggers. It is the contract, the ordinary path, and the only path — and the
inversion matters because a reader who takes the spec's framing will look for the implicit trigger
they are supposed to be using, conclude they have configured something wrong, and never find it. The
same inversion propagated one document further out, into
[`spec-009-rich_schema_architecture-0_0_4.md`][spec-009]'s Layer 3, which describes the same
never-shipped auto-finalization as "preferred triggers"; that is a sibling defect, escalated to the
maintainer rather than fixed here.

*Why approach 3 won over the hybrid, reconstructed from what shipped rather than asserted.* The
hybrid's own stated cost was that "it needs careful API design so simple schemas remain simple and
rich schemas finalize predictably", and predictability is exactly what it cannot give: if three
different constructors may each be the one that finalizes, the finalization point becomes a function
of which field a consumer happened to declare first, which is import-order dependence re-entering
through the trigger after being driven out of the relation graph. Approach 3's stated cost — "adds a
new top-level API and may surprise users who expect plain `strawberry.Schema`" — was paid once, in
one documented line of consumer setup, and bought a single named point where the whole graph is known
to be complete. The hard invariant against import order changing the public schema shape is the
criterion that decided it.

*A later change made the spec's speculative naming worse rather than obsolete.* Approach 4 named
`DjangoSchema(...)` as the finalizing schema constructor. `DjangoSchema` **shipped** — at `0.0.14`,
in `django_strawberry_framework/schema.py`, for an entirely unrelated contract: it installs
`DjangoMutationExecutionContext` so a generated mutation's `transaction.atomic()` spans response
completion, and resolves the production `ErrorPolicy` at construction. It does not finalize anything.
A speculative name that never landed is a dead reference a reader abandons; a speculative name that
was later taken by a different feature is a live one that confirms a false belief.

*Claims the section no longer makes.* That the finalization point is unresolved; that any of
approaches 1, 2, or 4 is live; that `DjangoConnectionField`, `DjangoNodeField`, or `DjangoSchema`
finalizes anything; that `finalize_django_types()` is an escape hatch, a convenience, or anything
other than the required call; that the hybrid story is this spec's leading direction.

### `### Registry questions` — the section removed; every question settled, and the guesses were right

Spec: none — the heading was removed. The pointer that replaced it, covering the four candidate
triggers and all four sets of questions, is one sentence in
[The finalization trigger][spec-008-trigger].

Bears on [Proposed shape to evaluate][spec-008-proposed]. The `Meta.primary` glossary anchor this
section carried was re-sited into `## Acceptance criteria`'s finalized-primary-metadata bullet in the
same edit.

*Moved verbatim, the framing.* "The registry will need to answer more than 'which type owns this
model?'"

*Moved verbatim, the questions.* "Can there be multiple `DjangoType`s per model before `Meta.primary`
exists? / If multiple types exist, which one should automatic relations choose? / Should automatic
relation resolution require exactly one primary type? / How should abstract/interface types
participate? / How should generated input/output types for filters, orders, and aggregates share the
registry? / How should tests reset registry state without leaking temporary classes?"

*Moved verbatim, the "Likely direction".* "keep one primary output type per model for automatic
relation resolution / allow non-primary model-backed types later / make ambiguous automatic relation
targets a configuration error / store pending relation records separately from finalized type
records."

*Every guess was right, and the change the decision underwent is that a later card made them true.*
`Meta.primary` shipped at `0.0.6`, by [`spec-018-meta_primary-0_0_6.md`][spec-018], which is the
authoritative catalog and is not restated here. Ambiguity **is** a configuration error, raised by
`types/finalizer.py::_audit_primary_ambiguity` and formatted by `::_format_ambiguity_error`. Pending
records **are** stored separately from finalized type records, on the same registry object. Registry
reset **is** `TypeRegistry.clear()`, extended by `registry.py::register_subsystem_clear` so
subsystems tear their own generated artifacts down rather than leaking them across lifecycles.

*The one question that turned out to be a different question.* "Can there be multiple `DjangoType`s
per model **before** `Meta.primary` exists?" assumes the constraint would be lifted by the same
mechanism that resolved ambiguity. It was — but the interesting correction is where the ambiguity
raise fires. [`spec-018`][spec-018] moved it from registration to finalization, because registration
cannot know whether a later sibling will claim primary, and a registration-time raise would therefore
have made the outcome depend on import order: the exact property this spec's hard invariants forbid.
The question's own framing is what corrected its answer.

*Claims the section no longer makes.* That any of the six questions is open; that `Meta.primary` is
future work; that one `DjangoType` per model is the rule; that the primary-selection direction is a
likely one rather than the shipped one.

### `### User annotation questions` — the section removed; three answers shipped, one is still deferred and says so

Spec: none — the heading was removed. The pointer that replaced it, covering the four candidate
triggers and all four sets of questions, is one sentence in
[The finalization trigger][spec-008-trigger].

Bears on [Proposed shape to evaluate][spec-008-proposed].

*Moved verbatim, the framing.* "Explicit annotations should remain useful."

*Moved verbatim, the questions.* "If a user manually annotates a relation field, should that override
automatic conversion? / Should the package validate that manual annotations match the Django relation
cardinality? / Can a manual annotation intentionally point to a non-primary type for a model? / How
should forward references and `from __future__ import annotations` interact with generated
annotations?"

*Moved verbatim, the "Likely direction".* "preserve manual annotations as an escape hatch / validate
them when enough metadata is available / let manual annotations opt into non-primary target types /
keep automatic `Meta.fields = "__all__"` relations concrete by default."

*Three of the four shipped as predicted.* The supported forward-reference and manual-relation shapes
are enumerated in the [glossary][glossary] under `## Definition-order independence` and are that
entry's to own — same-module string annotations, `from __future__ import annotations` stringified
forms, cross-module `Annotated[..., strawberry.lazy(...)]`, annotation-only overrides that keep the
generated resolver, and `strawberry.field(resolver=...)` overrides that keep the consumer resolver.
Automatic `"__all__"` relations are concrete by default. The consumer-override half of the contract
was extended to scalar fields at `0.0.6` by [`spec-019`][spec-019].

*The second guess is the one that did not ship, and the package says so out loud.* "validate them
when enough metadata is available" was the hedge, and the shipped answer is: not yet. The glossary
records it in one sentence — "Validation that a manual relation annotation matches the Django
relation cardinality is deferred" — which is the correct place for it, because it is a published
consumer-visible limitation rather than a design argument. Recorded here so a reader of this spec's
prediction does not count it as vindicated along with its three neighbours: it is the only one of
this spec's nineteen settled questions whose answer is still "deferred", and it is deferred
explicitly rather than by omission.

*Claims the section no longer makes.* That the override semantics are open; that manual annotations
are an escape hatch whose contract is unpromised; that cardinality validation is a likely direction
rather than a published deferral.

### `### Generic fallback questions` — the section removed; answered by omission, exactly as predicted

Spec: none — the heading was removed. The pointer that replaced it, covering the four candidate
triggers and all four sets of questions, is one sentence in
[The finalization trigger][spec-008-trigger].

Bears on [Acceptance criteria][spec-008-acceptance]. The `schema audit` glossary anchor this section
carried was re-sited onto `## Acceptance criteria`'s existing unresolved-versus-skipped bullet, which
already named the behavior in plain words.

*Moved verbatim, the framing.* "Generic fallback is useful as an emergency escape hatch but conflicts
with the goal if it becomes the default."

*Moved verbatim, the questions.* "Should generic fallback exist at all in 1.0? / If it exists, should
it be per-field, per-type, or global? / Should it be allowed only for intentionally skipped relation
targets? / How would it appear in schema audit output?"

*Moved verbatim, the "Likely direction".* "do not implement generic fallback first / default
unresolved exposed relations to `ConfigurationError` / consider explicit fallback later only if real
projects need it."

*The prediction was followed to the letter, and the last clause is still open in the only way that
costs nothing.* No generic relation fallback exists anywhere in the package through `0.0.14`;
`DjangoModelType` has zero occurrences. Unresolved exposed relations raise, and the error names the
source model, the source field, and the target
(`types/finalizer.py::_format_unresolved_targets_error`). "Consider explicit fallback later only if
real projects need it" has not been triggered by any project in ten minor versions, which is the
evidence the deferral was correct rather than merely convenient.

*The fourth question was answered by a subsystem that already existed.* "How would it appear in
schema audit output?" presumed a fallback to report. Schema audit instead reports relation targets
without a registered `DjangoType` as warnings and ignores hidden and `OptimizerHint.SKIP` fields —
which is precisely the "distinguishes unresolved targets from intentionally skipped fields" behavior
`## Acceptance criteria` asks for, delivered by [`spec-004`][spec-004] at `0.0.3`, one release before
this decision landed. A question about a mechanism that was never built was answered by a mechanism
that already worked.

*Claims the section no longer makes.* That generic fallback is under consideration for `1.0`; that
its granularity, its permitted scope, or its audit representation is an open question.

### `### Rich-schema dependency questions` — the section removed; the answer was "per subsystem, as each ships"

Spec: none — the heading was removed. The pointer that replaced it, covering the four candidate
triggers and all four sets of questions, is one sentence in
[The finalization trigger][spec-008-trigger].

Bears on [Features that depend on this decision][spec-008-features].

*Moved verbatim, the framing.* "Definition-order independence should be designed with later systems
in mind."

*Moved verbatim, the questions.* "Should filters/orders/aggregates resolve related class graphs
during the same finalization pass? / Should `DjangoTypeDefinition` store `filterset_class`,
`orderset_class`, `aggregate_class`, `fields_class`, and `search_fields` from the start? / Should
connection fields trigger finalization of only reachable types or the whole registry? / Should
aggregate output types be generated before or after relation finalization? / Should cascade
permission traversal use the same relation graph as the optimizer?"

*Moved verbatim, the "Likely direction".* "collect all rich `Meta` keys early / finalization should
produce one shared graph of model/type/relation metadata / filters/orders/aggregates can have their
own factories, but they should consume the same finalized graph / optimizer and permissions should
not maintain separate relation maps that can drift from type generation."

*The architectural half was right; the "collect all rich `Meta` keys early" half was not, and the
split is visible in `types/definition.py` today.* Of the five keys named, `filterset_class` and
`orderset_class` carry real slots and are bound at finalization (`0.0.8`,
[`spec-027`][spec-027] / [`spec-028`][spec-028]); `fields_class` carries a slot that is declared and
**reserved**, holding `None` while `Meta.fields_class` sits in `types/base.py::DEFERRED_META_KEYS`;
and `aggregate_class` and `search_fields` have no slot at all. So one landed reserved, two landed
bound, and two do not exist. Each arrived with the card that shipped its feature rather than being
reserved up front, which is the package's general rule for `Meta` keys and the opposite of what this
bullet predicted.

*Why the miss is worth recording rather than filing as a small error.* Reserving five slots in a
shared metadata object for features three releases away is the shape that produces dead fields nobody
dares remove, and the package's own convention — a key's feature ships in the same card that
introduces the key, never reserved-but-nonfunctional — is written into a comment beside
`ALLOWED_META_KEYS`. The prediction was reaching for a real goal (one shared finalized graph, no
subsystem maintaining its own relation map) and picked a mechanism that would have worked against it.
That goal was met without the mechanism: filtersets and ordersets bind inside the finalization pass
against the same definition objects the optimizer and the cascade traversal read.

*Claims the section no longer makes.* That any of the five questions is open; that
`DjangoTypeDefinition` should carry all five sidecar slots from the start; that aggregate output
types or fieldsets are pending design questions for this spec rather than unshipped Beta cards.

## Entries added by the spec-reconciliation pass

The entries above record what the rationale-extraction pass moved out of the spec. The entries below
record what the reconciliation pass **changed** in the spec: the claims the repository had falsified,
the sections the cluster's single-ownership boundary moved to another document, and the one section
retired as a third telling. Each names the spec heading it belongs to.

Two rules shaped every one of them and are stated once here rather than repeated per entry. **The
spec never narrates its own history**, so no entry below has a counterpart amendment note in the spec
— the spec states the corrected contract directly and this file carries the correction. And **a
concrete claim restated in two documents is a defect, not redundancy**, so where a claim moved, the
duplicate was retired rather than kept in sync.

### `## Problem` and `## Package behavior before this decision` — the tense, and one symbol that no longer exists

Spec: [Problem][spec-008-problem].

*Claims the sections no longer make.* That `DjangoType` **currently** resolves relation targets
eagerly; that a function named `convert_relation` exists; that the eager pipeline is the package's
present behavior.

The heading `## Current package behavior` and the sentences under it described the pre-`0.0.4` state
in the present tense, which stopped being true the moment the decision shipped. The reconciliation
states the same facts as the constraint the design faced — the pipeline is named as the one this
design had to replace — rather than re-titling them "formerly", which would have been the chronology
the spec is not allowed to carry.

*The dead symbol is worth recording separately.* `convert_relation` has **zero** occurrences in
`django_strawberry_framework/`; relation annotations resolve through
`types/converters.py::resolved_relation_annotation`. A named symbol is the strongest kind of claim a
spec makes, because a reader can grep for it, and the grep returning nothing reads as the reader's
mistake before the spec's. The reconciliation describes the step functionally instead of naming a
current symbol, because the symbol that replaced it belongs to the pipeline
[`spec-001`][spec-001] and [`spec-010`][spec-010] own, not to this record.

`KANBAN.md`'s board item on present-tense survivals in shipped specs rules spec-008 out of *its*
sweep as "correct as history". That is not a contradiction: it declines to fix the survivals in
passing, and this cycle is the authorized place.

### `### Features that depend on this decision` — the prediction that came true and was never updated

Spec: [Features that depend on this decision][spec-008-features].

*Claims the section no longer makes.* That the eight dependent systems are future work; that any of
them "needs" the foundation in a tense that implies it has not been built on it yet.

Six of the eight shipped on this foundation exactly as the section predicted —
`DjangoConnectionField` and `DjangoNodeField` at `0.0.9`, related filters and orders at `0.0.8`,
cascade permissions at `0.0.10`, and relation-kind dispatch throughout the optimizer. Related
aggregates and fieldsets remain Beta cards. This is the spec's strongest vindication and its
most-falsified tense at the same time, which is why the reconciliation keeps the eight-item list
intact — the list is the argument for why the decision mattered — and states the shipped / Beta split
in one closing sentence rather than annotating each bullet.

The section is also the sole carrier of two glossary anchors, so it could not have been demoted even
had the ownership boundary asked for it; it is spec-008's own material and the boundary does not.

### `## The decision` (was `## Current strongest direction, not a final plan`) — the reversal

Spec: [The decision][spec-008-decision] and [The finalization trigger][spec-008-trigger].

*Claims the section no longer makes.* That Option 4 is the "strongest direction" rather than the
decision; that this is not a finalized implementation plan; that the type-finalization mechanics
still need implementation research and tests; that any of the six target-behavior bullets is a
"should" awaiting proof.

**The finalization trigger is where the spec was wrong rather than merely stale, and it is the reason
this pass exists.** The entry on `### Finalization trigger choices` above carries the full record: the
hybrid direction the spec named as leading — implicit finalization inside `DjangoConnectionField`,
`DjangoNodeField`, and `DjangoSchema`, with `finalize_django_types()` as an "escape hatch for tests
and advanced import layouts" — was rejected outright, and approach 3 shipped unmixed. The
reconciliation states the settled answer in the spec as a plain contract and leaves the reversal
here.

*Two consequences deliberately carried into the spec's wording.* First, the spec no longer calls the
explicit call an escape hatch anywhere in the finalization sense; it is "the ordinary path and the
only path". The inversion is the whole harm — a reader who takes the old framing hunts for the
implicit trigger they believe they should be using. Second, the spec does not enumerate
`DjangoConnectionField` / `DjangoNodeField` / `DjangoSchema` as non-finalizing. That negative claim is
a property of the pass, so it belongs to [`spec-010`][spec-010] under the ownership boundary, and
this pass wrote it there (`#"Auto-trigger via"`). Enumerating it in both would have been the exact
duplication this cycle exists to remove.

*The `escape hatch` phrase was not swept globally, and that was deliberate.* Two surviving uses are
correct as written — explicit user annotations as an override path, in
`## Prior art: Strawberry-Django` `### Relevance to this package` and in the decision's
target-behavior list. Only the finalization-trigger sense is the inversion.

*The `DjangoSchema` naming hazard is unchanged and is recorded in the trigger entry above.* The spec's
speculative name was later taken by a real, unrelated feature at `0.0.14`, which is worse than a name
that never landed. Removing the speculative claim is the only fix available to a spec; the sibling
half of it is spec-010's Edit 3.

### `### Hard invariants` — demoted to a pointer, and why that is not a loss

Spec: [Hard invariants][spec-008-invariants].

*Claims the section no longer makes.* None — every one of the eight invariants holds at HEAD,
verified in this cycle's read-only audit, including the two that are absence-shaped and therefore
easiest to erode without noticing (zero Graphene imports, zero generic-fallback types).

The demotion is an **ownership** decision, not a correctness one, and the distinction matters because
the section's accuracy is what makes it tempting to keep. [`spec-010`][spec-010]'s
"Invariants this slice must protect" carries the same eight constraints with enforcement teeth —
"Any change that violates one of them is a rejected change" — and with acceptance tests behind each.
Two accurate copies of a constraint list are one stale copy waiting to happen, and the copy that
would go stale is the one with no tests behind it.

*Moved — the eight invariants, as this record stated them.* "no Graphene runtime dependency / no
silent Graphene-style field skipping / no generic relation fallback by default / no serving a schema
with unresolved exposed model relations / no requirement for manual relation annotations on the
normal `Meta.fields = "__all__"` path / no optimizer regression where finalized relations become
opaque / no hidden schema-shape degradation based only on import order / clear reset/isolation story
for tests that create temporary `DjangoType` classes."

*Moved — `### Failure criteria`, the same list stated as rejection conditions.* "import order changes
the public schema shape / missing related types are silently skipped / automatic
`fields = "__all__"` relation fields degrade to generic placeholders by default / relation metadata
is finalized in one subsystem but not visible to another / optimizer planning loses relation target
information / generated filter/order/aggregate types need to recreate a separate relation graph /
schema construction can succeed while exposed relation targets are unresolved." Its heading was
retired rather than demoted: seven of its seven entries are the negation of an invariant above, so it
was a duplicate inside the spec before it was a duplicate across the cluster.

*The one invariant that decided the trigger question.* "No hidden schema-shape degradation based only
on import order" is what rules out the hybrid: three constructors each able to finalize makes the
finalization point a function of which field a consumer declared first, which is import-order
dependence re-entering through the trigger after being driven out of the relation graph.

### `### The shape that shipped` (was `### Proposed shape to evaluate`) — demoted to a pointer

Spec: [The shape that shipped][spec-008-proposed].

*Claims the section no longer makes.* That the shape is proposed, or is to be evaluated; that
Strawberry finalization should be avoided "unless tests prove placeholder patching is safer" (the
tests were run — [`spec-010`][spec-010]'s Spike B closed placeholder patching out as rejected).

*Moved — the collection-phase steps, verbatim.* "1. Validate `Meta`. / 2. Select Django fields. /
3. Create or update a type-definition object for the class. / 4. Register the model/type pair early
enough for later classes to discover it. / 5. For scalar fields, record enough metadata to build
annotations. / 6. For relation fields: if the related model is already registered, record the
concrete target type; otherwise create a pending relation record with source type, source model,
field name, related model, relation kind, and nullability/cardinality metadata. / 7. Preserve
user-authored annotations before generating package annotations. / 8. Avoid finalizing with
Strawberry until the relation strategy is known, unless tests prove placeholder patching is safer."

*Moved — the pre-schema-construction steps, verbatim.* "1. Resolve all pending relations against the
registry. / 2. Resolve lazy type metadata needed by the rich-schema systems. / 3. For each resolved
relation, compute the concrete annotation: many-side -> `list[target_type]`; reverse OneToOne ->
`target_type | None`; forward nullable -> `target_type | None`; forward non-null -> `target_type`. /
4. Merge generated annotations with user-authored annotations. / 5. Attach or rebuild generated
Strawberry fields. / 6. Attach Django relation metadata for the optimizer and future field classes. /
7. If any exposed relation target is still missing, raise `ConfigurationError` with the source model,
source field, and related model named."

*Step 7 is quoted above as this record's proposal, not restated here as a contract.* The requirement
it asked for — that the raise name the source model, the source field, and the target model — survives
in the spec as a design constraint any implementation must satisfy, and the canonical wording, the
message format, and the substring assertions that pin it are [`spec-010`][spec-010]'s. Both documents
state that split. This entry is the deliberative record of what was asked for; it is not a third home
for the contract, and nothing below should be read as one.

*Every step landed, and the two halves landed in two different documents' custody.* The collection
half is [`spec-001`][spec-001]'s and the finalization half is [`spec-010`][spec-010]'s, which is the
boundary this cycle settled. The spec keeps one sentence saying the shape shipped whole, because
"the proposal was adopted unchanged" is this record's own outcome and nobody else's to state.

*One step's wire shape is version-scoped and no longer belongs to any of the three.* Step 3's
"many-side -> `list[target_type]`" was the shape at `0.0.4`; `Meta.relation_shapes` made it declarable
per field at `0.0.9` and the default moved to `"connection"` at `0.0.14`. Restating it in the spec
would have pinned a shape two releases stale, which is why the demotion sentence names the outcome
and not the mapping.

### `## Acceptance criteria` and `### Failure criteria` — demoted to a pointer, and the one criterion the implementation refused

Spec: [Acceptance criteria][spec-008-acceptance].

*Claims the section no longer makes.* That the criteria are a checklist awaiting satisfaction; that
"root `DjangoConnectionField` can finalize reachable model types before schema construction" is
something the package must do.

**Twelve of the thirteen narrow-and-broad criteria are met.** Bidirectional `CategoryType.items` /
`ItemType.category` in either declaration order; all six relation shapes; `Meta.fields = "__all__"`
over a bidirectional graph; a `ConfigurationError` naming source model, source field, and target
model; optimizer plans over concrete targets; schema audit distinguishing unresolved targets from
intentionally skipped fields; manual annotation override; no silent generic fallback; `DjangoNodeField`
on finalized primary metadata. That inventory is [`spec-010`][spec-010]'s, checkable and tested,
which is why the spec now points at it rather than carrying a second copy that no test reads.

*The thirteenth is the criterion the implementation deliberately made unmeetable, and it is the same
reversal as the trigger.* "Root `DjangoConnectionField` can finalize reachable model types before
schema construction" names a mechanism that was rejected. The dependency the bullet was protecting is
satisfied a different way: the field is constructed against already-finalized metadata because the
consumer called the finalizer first. Left in place it reads as an unmet requirement — a reader
auditing the package against this list would score it as a gap — when it is a superseded one. That is
the difference this entry exists to record, and it is why the criterion is retired from the spec
rather than re-worded there.

### `## Fakeshop implication` — demoted; two of its eight rows are falsified

Spec: [Fakeshop implication][spec-008-fakeshop].

*Claims the section no longer makes.* That `Category.properties` and `Property.entries` resolve to
`list[PropertyType]` and `list[EntryType]`; that the fakeshop graph "cannot be represented as one rich
primary type per model without omitting some relation fields".

*Moved — the eight rows, verbatim.* "`Category.items` should resolve to `list[ItemType]`. /
`Category.properties` should resolve to `list[PropertyType]`. / `Item.category` should resolve to
`CategoryType`. / `Property.category` should resolve to `CategoryType`. / `Item.entries` should
resolve to `list[EntryType]`. / `Property.entries` should resolve to `list[EntryType]`. /
`Entry.item` should resolve to `ItemType`. / `Entry.property` should resolve to `PropertyType`."

*Six of the eight still hold; two do not, and which two is not the obvious split.* The four forward-FK
rows hold untouched — `relation_shapes` never reached them. Of the four many-side rows,
`Category.items` and `Item.entries` hold because `products/schema.py` carries an explicit
`relation_shapes = {"…": "both"}` opt-in for each. `Category.properties` and `Property.entries` do
**not**: `CategoryType` opts `items` in and deliberately leaves `properties` on the `0.0.14` default,
and `PropertyType` carries no `relation_shapes` key at all, so both are reachable only through their
`…Connection` siblings and have no list form in the SDL. The fixture was built that way on purpose —
one type covering both shapes live.

*The closing sentence is falsified in the best possible way.* Every one of the eight relations is
exposed on one rich primary type per model today. The type declares an explicit field tuple rather
than `fields = "__all__"`, which is a fixture choice and not a limitation of the decision.

*Why the section is demoted rather than corrected in place.* Correcting it would have meant the spec
carrying a per-field wire-shape table — the exact artifact [`spec-032`][spec-032] owns, at the exact
granularity that moved twice in two releases. The spec keeps the fixture's *role* (this record chose
it, and it proves the point) and points elsewhere for its shape.

### `## Cookbook implication` — demoted to a pointer at spec-009

Spec: [Cookbook implication][spec-008-cookbook].

*Claims the section no longer makes.* That the nine-member node surface is uniformly aspirational.

Six of the nine shipped: `fields = "__all__"` at `0.0.4`, `interfaces = (relay.Node,)` at `0.0.5`,
`filterset_class` and `orderset_class` at `0.0.8`, type-level `get_queryset` from `0.0.1`, and
cascade permissions at `0.0.10`. Three are unshipped Beta work — `fields_class`, `search_fields`, and
`aggregate_class`. Read as written, the section describes a target none of which had landed; two
thirds of it is now fact.

The demotion is an ownership call: the cookbook fixture is
[`spec-009`][spec-009]'s target-outcome material, and it is the one that must be re-scored as the
three Beta cards ship. A second copy here would need the same re-scoring and would not get it.

### `## Decision context to preserve` — retired

Spec: none — the heading was retired, so there is no anchor to name. Its content is distributed across
[Prior art: Graphene-Django][spec-008-graphene], [Prior art: Strawberry-Django][spec-008-strawberry],
[Why this matters for the goal][spec-008-goal], and [The decision][spec-008-decision].

*Claims the section no longer makes.* All six of them, as claims. Nothing in it was wrong.

The section's six bullets restate the borrow / avoid conclusions of both
`### Relevance to this package` subsections, plus the `GOAL.md` product target already stated in
`## Why this matters for the goal`, plus the decision itself now stated in `## The decision`. After
the rationale-extraction pass condensed both prior-art sections into their conclusions, this became
the **third** telling of the same conclusions inside one file.

Every bullet is a conclusion rather than deliberation, so the ordinary move test does not reach it;
the cycle's DRY rule does. It is recorded here in full so nothing is lost: "Graphene-Django gives the
right product insight: defer relation lookup until the registry has enough information. /
Graphene-Django gives the wrong implementation substrate: do not port `Dynamic` or silent field
skipping. / Strawberry-Django gives the right implementation lessons: annotation handling, custom
fields, field post-processing, and async-safe resolvers. / Strawberry-Django gives the wrong default
relation shape for this package's goal: generic relation placeholders should not be the normal
automatic output. / `django-graphene-filters` gives the product target: concrete rich nodes with
sidecar filters, orders, aggregates, fieldsets, permissions, and connection fields. / The package
should combine those lessons into a Strawberry-native, fail-loud, concrete-relation finalization
model."

The heading's own framing — "Before implementation, keep these conclusions visible" — is what dates
it. Implementation is ten minor versions behind us.

### The two `### Relevance to this package` subsections — retensed, not moved

Spec: [Prior art: Graphene-Django][spec-008-graphene] · [Prior art: Strawberry-Django][spec-008-strawberry]
(each subsection's own heading is a duplicate `### Relevance to this package`, so the parent section's
anchor is the addressable one).

*Claims the sections no longer make.* That the borrow and avoid lists are instructions to a future
implementer ("the parts to borrow", "the package should treat Graphene-Django as evidence").

Nothing in either list changed. Each is now stated as what the package borrows and avoids, because
every item on both lists was acted on: there are zero Graphene imports and zero generic-fallback
types, the namespace-aware annotation handling and field post-processing shipped, and decorator-first
declaration never became the primary API. A prescription that was followed and is still written as a
prescription reads as unfinished work.

*One anchor moved into this prose.* The `Meta.fields` glossary anchor was re-sited onto the
Strawberry subsection's closing sentence, which already named `Meta.fields = "__all__"` in HEAD's own
words — a link-form change on surviving prose, not a new sentence written to host a link. Its
previous carrier was an `## Acceptance criteria` bullet this pass demoted.

### Anchor custody across this pass

Spec: no single decision — this entry is keyed to the reconciliation pass rather than to a spec
heading, and the four re-sited anchors' new hosts are named in its own bullets below.

All ten glossary anchors survive; `check_spec_glossary.py` reports `OK: 10 terms`. Four sat on prose
this pass removed and each was re-sited **in the same edit that removed its carrier**, never by
editing the terms CSV and never by leaving a hollow section to host a link:

- `Meta.fields` -> the `## Prior art: Strawberry-Django` `### Relevance to this package` closing
  sentence, which already named the key.
- `finalize_django_types` -> `### The finalization trigger`'s opening sentence. Its previous host was
  the rationale-pointer line the extraction pass created, whose neutrality was load-bearing while the
  trigger question still read as open. It no longer is: the answer is stated, so the anchor sits on
  the answer.
- `Meta.primary` -> `### The finalization trigger`'s sentence pointing at [`spec-018`][spec-018],
  where naming the key is the point of the pointer.
- `schema audit` -> the `## Acceptance criteria` pointer sentence, which names what the inventory
  covers.

### The five sibling-spec edits this pass landed, and the one it did not

Spec: no single decision — this entry is keyed to the reconciliation pass rather than to a spec
heading; every edit it records lands in a sibling spec, not in spec-008.

Under the single-ownership law an inbound reference that contradicts the boundary must be fixed in
the same change that draws it, or the cluster is inconsistent in the commit that was meant to make it
consistent. Five edits were authorized and all five landed.

- **`spec-001` #"owns that pass"** named this spec as the owner of the finalization pass. It is not:
  this record declines, in its own text, to own any contract, and [`spec-010`][spec-010] pins the
  phases, the idempotency, and the call point. Repointed to spec-010.
- **`spec-010` #"helpers wrap it in later releases"** predicted wrapper helpers that never shipped.
  Restated as the contract that holds: no shipped helper wraps the entry point.
- **`spec-010` #"Auto-trigger via"** described `DjangoSchema(...)` and `DjangoConnectionField(Type)`
  auto-triggering as a later-phase wrapper. This is D3's falsification reaching the sibling that
  inherited the prediction. Restated as the negative fact, with the never-adopted direction named as
  recorded rather than recommended. The sentence's second half — the single-threaded-window
  obligation on any *future* such helper — is kept: it is a live constraint on work not yet done, not
  a claim about shipped code.
- **`spec-010`'s two raw line-range citations into this spec** (`(400-414)` and `(397-505)`) resolved
  to sections this pass rewrote or removed. A line-range citation cannot dangle loudly the way a
  broken link can — it silently resolves to different prose — so both were converted to
  heading-anchored references in the same change.
- **`spec-010`'s rerun-recovery contract** asserted the opposite of the code it owns. See the next
  entry.

**Not edited: [`spec-009`][spec-009]'s Layer 3.** It describes the same never-shipped
auto-finalization as "preferred triggers" — the same inversion, one document further out. It is
deferred to its own cycle by maintainer decision: spec-009 is a large architecture spec, and a
drive-by edit to one section leaves the rest unreconciled while creating the impression that the file
has been checked. Deferring it does **not** license this spec to keep pointing at it as live
guidance, which is why `## The decision` states the direction was not adopted.

### `spec-010`'s rerun-recovery contract — a spec asserting the opposite of its own code

Spec: none in spec-008 — the contract belongs to [`spec-010`][spec-010], and this entry is keyed to
the reconciliation pass that corrected it.

Not a spec-008 entry, recorded here because this pass made the edit and the explanation has to live
somewhere keyed to the change.

Spec-010 stated that re-calling `finalize_django_types()` after a Phase 2/3 failure on the same
classes is **unsupported** and that recovery **requires** `registry.clear()` plus fresh classes.
`types/finalizer.py`'s module docstring states the opposite: a raise inside Phase 2, 2.5, or 3 leaves
the registry's finalized flag False and "supports a fine-grained partial recovery on rerun", via the
per-entry `if definition.finalized: continue` guards at the head of each phase loop, with
`registry.clear()` demoted to "the recommended escape hatch only when the offending type cannot be
fixed in place". Shipped tests pin the relaxed behavior directly — one re-finalizes **without**
`registry.clear()` after fixing the cause and asserts the rerun is clean.

Some later change relaxed the contract and no spec recorded it. Under the ownership boundary the
relaxed behavior is a property of the pass spec-010 owns, so spec-010 is the only correct home for
it; leaving it would have meant a shipped spec contradicting its own code for however long a
spec-010 cycle takes, which is a stronger defect than any this cycle set out to fix.

*The boundary this pass held.* It did not re-derive the recovery semantics. It states what the
finalizer's docstring and the `definition.finalized` guards actually do, read at HEAD, and nothing
more.

*Related, and in the same edit: the phase count.* Spec-010 documents three phases; the shipped pass
runs four — Phase 2.5 was inserted between resolver attachment and `strawberry.type` decoration — and
Phase 1 additionally runs a primary-ambiguity audit. Spec-010's prose now **acknowledges** both
insertion points without **claiming** them: Phase 2.5's contents belong to the specs that shipped
them (interfaces, relation-as-Connection synthesis, filterset and orderset binding, GlobalID wiring)
and the ambiguity audit to [`spec-018`][spec-018]. Acknowledging an insertion point is what keeps a
phase-order contract honest; enumerating its contents would have made spec-010 the owner of five
other specs' work.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../../GLOSSARY.md

<!-- docs/SPECS/ -->
[spec-001]: ../spec-001-django_types-0_0_1.md
[spec-004]: ../spec-004-optimizer_beyond-0_0_3.md
[spec-008]: ../spec-008-definition_order_independence-0_0_4.md
[spec-008-acceptance]: ../spec-008-definition_order_independence-0_0_4.md#acceptance-criteria
[spec-008-cookbook]: ../spec-008-definition_order_independence-0_0_4.md#cookbook-implication
[spec-008-decision]: ../spec-008-definition_order_independence-0_0_4.md#the-decision
[spec-008-fakeshop]: ../spec-008-definition_order_independence-0_0_4.md#fakeshop-implication
[spec-008-features]: ../spec-008-definition_order_independence-0_0_4.md#features-that-depend-on-this-decision
[spec-008-goal]: ../spec-008-definition_order_independence-0_0_4.md#why-this-matters-for-the-goal
[spec-008-graphene]: ../spec-008-definition_order_independence-0_0_4.md#prior-art-graphene-django
[spec-008-invariants]: ../spec-008-definition_order_independence-0_0_4.md#hard-invariants
[spec-008-option1]: ../spec-008-definition_order_independence-0_0_4.md#option-1-keep-eager-resolution
[spec-008-option2]: ../spec-008-definition_order_independence-0_0_4.md#option-2-strawberry-django-style-explicit-relation-annotations
[spec-008-option3]: ../spec-008-definition_order_independence-0_0_4.md#option-3-generic-relation-fallback
[spec-008-option4]: ../spec-008-definition_order_independence-0_0_4.md#option-4-graphene-style-deferred-relation-resolution
[spec-008-options]: ../spec-008-definition_order_independence-0_0_4.md#design-options-for-this-package
[spec-008-problem]: ../spec-008-definition_order_independence-0_0_4.md#problem
[spec-008-proposed]: ../spec-008-definition_order_independence-0_0_4.md#the-shape-that-shipped
[spec-008-strawberry]: ../spec-008-definition_order_independence-0_0_4.md#prior-art-strawberry-django
[spec-008-trigger]: ../spec-008-definition_order_independence-0_0_4.md#the-finalization-trigger
[spec-009]: ../spec-009-rich_schema_architecture-0_0_4.md
[spec-010]: ../spec-010-foundation-0_0_4.md
[spec-018]: ../spec-018-meta_primary-0_0_6.md
[spec-019]: ../spec-019-consumer_overrides_scalar-0_0_6.md
[spec-027]: ../spec-027-filters-0_0_8.md
[spec-028]: ../spec-028-orders-0_0_8.md
[spec-032]: ../spec-032-full_relay-0_0_9.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
