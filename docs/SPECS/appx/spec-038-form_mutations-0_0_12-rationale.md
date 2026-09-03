# Rationale companion: spec-038 (Form-based mutations — `DjangoFormMutation` / `DjangoModelFormMutation`)

Companion to [`docs/SPECS/spec-038-form_mutations-0_0_12.md`][spec-038]. It
carries that spec's **deliberative layer** and nothing else: the authoring
revision history that produced the contract, every Decision's justification,
every alternative a Decision rejected and why it lost, the rejected plain-form
cleaned-data echo [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)
was carrying inline, and the risk / open-question deliberation that settled the
card's design questions. The spec carries the contract; this file carries how the
contract was arrived at. Neither duplicates the other — the text here **left** the
spec.

Read this when checking a finished implementation against the reasoning that
produced it, or before re-opening a settled question. Worker 2 never reads it
([`docs/builder/BUILD.md`][build-md] `### Who reads it, and when`).

**How later passes append to this file.** Each Decision below carries a
`### Changes this Decision underwent` section. A reconciliation pass that finds
the spec stale against `HEAD` — a guard that shipped differently, a helper that
never landed where the Decision said it would, a default a later card inverted —
appends a `**Post-ship:**` bullet there, naming the shipped behavior and the card
or commit that changed it. A Decision a reconciliation checked and found still
true earns a bullet too, saying so — a measured no-change and an unexamined one
read identically otherwise. Findings belonging to no single Decision go under
[Non-Decision deliberation](#non-decision-deliberation). Nothing needs
restructuring to take an addition, and the corrections themselves always land in
the spec, stated directly and without chronology.

## Provenance of this record

Created by Slice 0 of the `038` residual-reconciliation cycle, whose plan is
[`docs/builder/build-038-form_mutations-0_0_12.md`][build-038] and whose record of
the move itself is the per-cycle artifact
`docs/builder/bld-038-slice-0-rationale_extraction.md`,
retired when that cycle closed and recoverable at
`git show cce37373:docs/builder/bld-038-slice-0-rationale_extraction.md`.
`spec-038` shipped in `0.0.12` with a [`-terms.csv`][spec-038-terms] companion and
no `-rationale.md` sibling; this file closes that gap. Nothing in it is new
reasoning: every passage below was cut from the spec in the same pass that created
this file, except the framing paragraphs, the `### Changes this Decision underwent`
summaries, and the [Non-Decision deliberation](#non-decision-deliberation) entries,
which are this pass's own and say so. The `034` / `035` / `036` / `037` companions
are the four immediately-preceding executions of the same move and this file
matches their shape.

The spec was verified byte-identical to `HEAD` before the first edit
(`git show HEAD:docs/SPECS/spec-038-form_mutations-0_0_12.md` into a scratch path
outside the repo, diffed clean against the working copy) at **185,851 bytes, 2,555
lines**. It stood at **164,240 bytes, 2,227 lines** when the move finished (Slice 2's
reconciliation has since edited it): **26,640 bytes cut**
by four routes, **5,029 bytes** of pointers, link definitions and two held-back
fragments added back, for a net **21,611 bytes** removed.

- **The whole `Revision history (kept inline so the spec is self-contained):`
  block** — its preamble, the blank line under it, and one `Revision 1` entry,
  41 lines, **2,948 bytes**. The entry is reproduced under
  [Revision history](#revision-history) below, byte-for-byte, **2,885 bytes** of
  it; the 62-byte preamble line was **deleted, not moved** — its claim that the
  history is kept inline is exactly what this move made untrue — and so was the
  1-byte blank line between them.
- **14 `Justification:` blocks**, one under every Decision, carrying 2
  justification bullets (Decision 1) and 13 paragraphs, **5,574 bytes**.
  Reproduced under each Decision's heading; the 14 labels became `###` headings
  here — 1 stood on its own line (Decision 1) and 13 were inline prefixes
  stripped from the paragraph they introduced (Decisions 2-14), which is why
  those sections open lower-case.
- **14 `Alternatives considered (and rejected):` blocks**, one under every
  Decision, carrying **25** rejected alternatives, **6,993 bytes**. All 14 labels
  stood on their own line and all 14 became `###` headings here. **The pairing is
  1:1** — unlike the `037` execution of this move, where two Decisions each
  carried one half of the pair and both files needed an explicit `None.` — so no
  Decision below has a missing section. The 14 blank lines separating each
  justification from its alternatives label account for the remaining 14 bytes of
  the 12,581-byte combined region.
- **[Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)'s
  `Rejected (recorded, not silently dropped): **cleaned-data echo**` paragraph** —
  14 lines, **1,093 bytes** (1,094 with its trailing blank). A rejected
  alternative recorded in the Decision body rather than in its own block; it is
  reproduced verbatim as the third entry under that Decision's
  `### Alternatives considered (and rejected)`.
- **The body of `## Risks and open questions`** — its preamble plus **14** items,
  **10,017 bytes**. Nine of the fourteen already carried a `RESOLVED` marker, and
  the other five are written as preferred-answer / fallback pairs; both shapes are
  a build-time deliberation instrument rather than a contract, so the body moved
  and the spec keeps the heading and a pointer here.

**The census used the shortest distinctive token, not the label phrase.**
`grep -oin 'ustification'` over the pre-move spec finds **14** occurrences and
`grep -oin 'lternatives'` finds **14** — every one of them a block label, so the
words appear nowhere else in the spec and neither count is a vocabulary sample of
a larger population. The two label lists interleave strictly (each
`Justification:` is immediately followed by its `Alternatives considered (and
rejected):`, and each pair sits under exactly one of the 14 `### Decision N`
headings), which is what establishes the 1:1 pairing rather than an assumption
from the equal counts. The 25 rejected alternatives are the top-level `- **`
bullets inside the 14 blocks: 2 / 2 / 2 / 2 / 3 / 2 / 2 / 2 / 1 / 1 / 1 / 1 / 2 /
2 for Decisions 1-14. The 14 Risks items are the top-level `- **` bullets between
the section's preamble and the next `##` heading; `grep -c RESOLVED` over that
range returns **9**.

**Every in-page anchor inside the moved text resolves locally here.** The moved
text carries **36 anchor occurrences across 15 distinct anchors**: all fourteen
`#decision-N--…` slugs and `#risks-and-open-questions`. This file carries headings
with exactly those slugs — the fourteen Decision headings are reproduced
character-for-character from the spec, so their GitHub slugs are identical — so
**zero** anchors inside moved text needed re-pointing.

**Four surviving `[Risks](#risks-and-open-questions)` uses in the spec were
re-pointed here, deliberately.** They sit in `## Non-goals`, the
`### Reference-package parity checkpoint` table,
[Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)'s
`Meta.return_field_name` paragraph, and
[Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form)'s
plain-form paragraph. Every one promises the reader *deliberation* — a card-body
tension recorded, a preferred resolution "settled with its fallback" — and that
deliberation is here, so leaving them would have made a reader who followed one
land on a spec heading containing only a pointer back to this file. They now read
`[Risks and open questions][rationale-risks]` and resolve in one hop. The spec
keeps its `## Risks and open questions` heading and its pointer paragraph, and has
no inbound in-page anchors on it any more.

**Two fragments were held back in the spec, and the glossary gate is why.**
`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-038-form_mutations-0_0_12.md`
requires every term in [`spec-038-form_mutations-0_0_12-terms.csv`][spec-038-terms]
to keep at least one link in the spec, and three of its 31 terms —
[`FilterSet`][glossary-filterset], [`OrderSet`][glossary-orderset] and
[`finalize_django_types`][glossary-finalize_django_types] — had their **only**
spec link inside prose this move cuts. Pruning their now-unused link definitions
would have failed the gate, and editing the CSV is not the fix. So the two
clauses carrying those three links were held back into the surviving normative
sentence each of them explains, and the moved text below reads without them:

- **[Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions)'s
  sibling-surface parenthetical.** Its justification said the form flavor "is
  uniform with it (and with `DjangoType` / `FilterSet` / `OrderSet`)". The
  Decision body already asserts the mutation is "declared exactly like every
  other consumer surface in the package"; the parenthetical now names which
  surfaces those are, at that sentence. The justification below keeps the claim
  without the enumeration.
- **[Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)'s
  single-finalize-call clause.** Its justification said the plain-form bind "still
  hangs off the single `finalize_django_types()` call (no second public finalize
  entry point)". That is implementation-relevant under
  [`docs/builder/BUILD.md`][build-md] `## Spec rationale extraction`'s carve-out —
  a builder who never reads it adds the second entry point the Decision's own
  rejected alternative names — and the Decision body already ends the bind
  paragraph with "not a new public finalize entry point the consumer must call",
  so the clause was appended there as its own sentence. The justification below
  keeps the cost argument without it.

Because of those two hold-backs, **no link definition was pruned from the spec**:
the move orphaned exactly three, all three were re-linked in the body, and a
post-move sweep found **0 dangling `][label]` uses and 0 unused definitions** in
both files.

**Reconciliation against `HEAD` is a separate pass, and it has run.** This move
checked nothing against the tree; the cycle's Slice 2 graded the whole corpus and
rewrote every stale contract statement, recording what changed and why as the
`**Post-ship:**` bullets under each Decision below, plus the entries under
[Non-Decision deliberation](#non-decision-deliberation). Its record is
the per-cycle artifact `docs/builder/bld-038-slice-2-spec_reconciliation.md`,
retired when that cycle closed and recoverable at
`git show cce37373:docs/builder/bld-038-slice-2-spec_reconciliation.md`.

**The one shape a move could not discharge is discharged.**
[Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
opened with an `Ordering correction — authorize runs BEFORE the relation decode
(post-ship security fix).` paragraph, stated that "the step numbers below reflect
the original draft sequence", and then left its seven numbered steps in the
superseded order. Moving the narration alone would have left the spec asserting the
wrong pipeline order with no correction at all — strictly worse than the chronology —
so it stayed until a pass could renumber the steps and sweep every step citation.
Slice 2 did both; the Decision now states the shipped order directly and this
Decision's first `**Post-ship:**` bullet carries the supersession.

## Revision history

One revision produced the contract: `spec-038` was authored in a single drafting
pass and never went through a numbered review revision, which is why every
Decision's `### Changes this Decision underwent` section below reads from that one
revision. The block below is the spec's own, verbatim. The one post-ship change
the spec did record — the
[Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)
authorize-before-decode ordering correction — was never folded into this history and
sat inline in the spec until Slice 2's reconciliation moved it to that Decision's
`**Post-ship:**` bullets.

- **Revision 1** — initial draft authored from the [`TODO-ALPHA-038-0.0.12`][kanban]
  card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-06-20). Pinned: the
  canonical structured filename
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the card-scope
  boundary that ships the two form flavors and reuses the frozen `036` contracts,
  parking serializer / auth for `0.0.13`
  ([Decision 2](#decision-2--card-scope-boundary-the-two-form-flavors-ship-serializer--auth-stay-out-the-frozen-036-contracts-are-reused-unchanged));
  the **`class Meta`-not-`MutationOptions`** surface
  ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions));
  the `forms/` subpackage layout
  ([Decision 4](#decision-4--module-and-test-locations-forms-subpackage-mirroring-mutations));
  the two-base public surface
  ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root));
  the base-class strategy — `DjangoModelFormMutation` rides the
  [`DjangoMutation`][glossary-djangomutation] base via the
  [`_resolve_model`][spec-036] seam, the plain `DjangoFormMutation` is the
  model-less sibling
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling));
  the form-derived input mapping
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth));
  the `form.errors` → [`FieldError`][glossary-fielderror-envelope] pipeline
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload));
  the optimizer composition reusing the `036` re-fetch path
  ([Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path));
  the operation set (`create` / `update`, no form `delete`)
  ([Decision 10](#decision-10--operations-create--update-for-the-modelform-no-form-delete));
  permission reuse
  ([Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form));
  the products live form surface
  ([Decision 12](#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation));
  the finalizer-bind reuse
  ([Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change));
  and **this card owning the `0.0.12` version bump**
  ([Decision 14](#decision-14--this-card-owns-the-0012-version-bump)). Two
  card-body tensions are carried into
  [Risks and open questions](#risks-and-open-questions) rather than silently
  reconciled (the card's `Meta.return_field_name` key vs the `036`-frozen uniform
  `node` / `result` slot, and the spec-filename vs the card's `docs/spec-form_mutations.md`),
  each with a preferred reading.

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-038-d1].

### Justification (moved from the spec)

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in
  [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN (`038`) and target patch
  (`0_0_12`) into the filename.
- The topic slug is `form_mutations` — short, snake-case, and naming the subsystem
  (the stem of the card DoD's suggested `docs/spec-form_mutations.md`).

### Alternatives considered (and rejected)

- **The card's own `docs/spec-form_mutations.md`.** Rejected: predates the
  structured-filename convention; [`spec-036`][spec-036] Decision 1 (and the cards
  before it) set the precedent of preferring the structured name and recording the
  card's older one (carried in [Risks](#risks-and-open-questions)).
- **Topic slug `forms` / `modelform`.** Rejected: `forms` collides conceptually
  with the Django `forms` module name, and `modelform` undersells the plain-`Form`
  half the card also ships.

### Changes this Decision underwent

- **Revision 1** pinned the canonical structured filename and the
  `form_mutations` topic slug over the card's own pre-convention
  `docs/spec-form_mutations.md` name.
- **Post-ship:** graded against `HEAD` and unchanged. The spec is at
  `docs/SPECS/spec-038-form_mutations-0_0_12.md` with the `form_mutations` slug, and
  the `-terms.csv` / `-rationale.md` companions sit under `docs/SPECS/appx/`.

## Decision 2 — Card-scope boundary: the two form flavors ship; serializer / auth stay out; the frozen `036` contracts are reused unchanged

Spec: [Decision 2 — Card-scope boundary: the two form flavors ship; serializer / auth stay out; the frozen `036` contracts are reused unchanged][spec-038-d2].

### Justification (moved from the spec)

the card is sized **L** and the serializer / auth flavors are
separately carded with their own `0.0.13` targets — pulling either forward would
bloat the slice exactly as [`START.md`][start]'s scope-creep rule warns. The
foundation already exists; this card's job is the form-specific generation + pipeline
on top of it.

### Alternatives considered (and rejected)

- **Ship the serializer flavor too** (it is "close"). Rejected:
  [`SerializerMutation`][glossary-serializermutation] is its own `0.0.13` card with
  a soft DRF dependency and a serializer-field converter; the form flavor's
  Django-core `Form` dependency is unconditional and a distinct slice.
- **Extend the `036` `FieldError` with form metadata.** Rejected: the card mandates
  the envelope is **reused unchanged**; forking it would break the one-contract
  promise the `0.0.13` cards also depend on.

### Changes this Decision underwent

- **Revision 1** pinned the card-scope boundary that ships the two form
  flavors and reuses the frozen `036` contracts, parking the serializer and auth
  flavors for `0.0.13`.
- **Post-ship:** the `036` contracts are still reused unchanged by *this* card, but
  the spec's `frozen` / `byte-identical` vocabulary for the
  [`FieldError`][glossary-fielderror-envelope] envelope became false and was replaced
  with **additive**. `mutations/inputs.py::FieldError` now states in its own docstring
  that the type is additive rather than frozen, and it has gained two optional
  members, `codes` (structured error codes) and `path` (the dotted `field` split into
  segments), both defaulting to `[]`. What the Decision may still claim — and does —
  is that `038` adds no member to it. The vocabulary occurred in the H1 title,
  `## Key glossary references`, `## Problem statement`, `## Goals`, the
  `### Reference-package parity checkpoint` row, `## Non-goals` and this Decision's
  own body; every one now reads "shared" / "defined" / "unchanged". **Decision 2's
  heading was deliberately NOT rewritten** even though it contains the word "frozen":
  two in-page anchors and the companion's own `[spec-038-d2]` definition resolve
  through it. `CHANGELOG.md`'s dated `[0.0.11]` / `[0.0.12]` entries also say
  "frozen"; those are observations of their own date in a maintainer-owned file and
  were deliberately left alone.
- **Post-ship:** the two sibling flavors this Decision parks for `0.0.13` have both
  shipped — [`SerializerMutation`][glossary-serializermutation] as
  `django_strawberry_framework/rest_framework/` and auth mutations as
  `django_strawberry_framework/auth/mutations.py`. The Decision's card-scope boundary
  is unaffected (this card still ships neither), so only the `TODO-ALPHA-039` /
  `TODO-ALPHA-040` card citations were replaced by the shipped module homes, in this
  Decision, `## Non-goals` and `## Out of scope`.

## Decision 3 — `class Meta` surface, not graphene's `MutationOptions`

Spec: [Decision 3 — `class Meta` surface, not graphene's `MutationOptions`][spec-038-d3].

### Justification (moved from the spec)

this is the package's defining surface contract, stated verbatim in
[`START.md`][start] ("Meta classes everywhere on consumer surfaces"). The
[`spec-036`][spec-036] [`DjangoMutation`][glossary-djangomutation] base already
established the nested-`Meta` mutation shape; the form flavor is uniform with it.
The *capabilities* of graphene-django's form mutations are borrowed at the outcome
level; the `MutationOptions` mechanism is not.

### Alternatives considered (and rejected)

- **graphene's `__init_subclass_with_meta__` keyword options.** Rejected: it is the
  metaclass-options surface the nested `class Meta` replaces; it also fragments the
  declaration shape away from [`DjangoMutation`][glossary-djangomutation].
- **A `@django_form_mutation(form_class=...)` decorator.** Rejected: a decorator on
  a consumer class is exactly the shape [`START.md`][start] forbids.

### Changes this Decision underwent

- **Revision 1** pinned the **`class Meta`-not-`MutationOptions`** surface.
- **Post-ship:** graded against `HEAD` and unchanged. Both bases are declared
  through a nested `class Meta`; no `MutationOptions` / `__init_subclass_with_meta__`
  surface exists anywhere in the package.

## Decision 4 — Module and test locations: `forms/` subpackage mirroring `mutations/`

Spec: [Decision 4 — Module and test locations: `forms/` subpackage mirroring `mutations/`][spec-038-d4].

### Justification (moved from the spec)

the card predicts `django_strawberry_framework/forms/` and
[`tests/forms/`][test-forms]; the [`mutations/`][mutations-sets] subpackage
([`spec-036`][spec-036] Decision 4) is the proven shape for a `class Meta`-driven
write subsystem. A separate `forms/` subpackage keeps the form-specific generation +
pipeline cleanly distinct from the model-driven `mutations/` while sharing its
public contracts.

### Alternatives considered (and rejected)

- **Fold the form bases into [`mutations/`][mutations-sets].** Rejected: the card
  predicts a `forms/` subpackage, the form-field converter is a distinct concern
  from the model-column generator, and the upcoming serializer flavor gets its own
  `rest_framework/` subpackage too — one subpackage per flavor keeps each
  extension point separable.
- **A flat `forms.py` module.** Rejected: the surface is a converter + a metaclass +
  a resolver pipeline + input generation — a subpackage matches it, and the card
  predicts `forms/`.

### Changes this Decision underwent

- **Revision 1** pinned the `forms/` subpackage layout mirroring `mutations/`.
- **Post-ship:** graded against `HEAD` and unchanged. `forms/` ships exactly
  `converter.py` / `inputs.py` / `sets.py` / `resolvers.py` plus `__init__.py`, and
  [`tests/forms/`][test-forms] mirrors all four.

## Decision 5 — Public surface: `DjangoFormMutation` / `DjangoModelFormMutation` exported from the root

Spec: [Decision 5 — Public surface: `DjangoFormMutation` / `DjangoModelFormMutation` exported from the root][spec-038-d5].

### Justification (moved from the spec)

keeping the public surface at two symbols (the two bases) — reusing
the field factory + error type via seams rather than a parallel factory — honors the
"one exposure idiom, one error contract" posture the package and the card both want,
and the seams are exactly what the `0.0.13` serializer flavor needs next (so the
generalization is the DRY investment, not throwaway). The audience for both bases is
every schema with a form-backed write, so the root export matches
[`DjangoMutation`][glossary-djangomutation]'s placement.

### Alternatives considered (and rejected)

- **A net-new `DjangoFormMutationField`.** Rejected as the default (a second exposure
  idiom for the same job once the seams exist); retained only as the
  [Risks](#risks-and-open-questions) fallback if generalizing the shipped factory's
  dispatch / input-ref proves invasive.
- **Claiming the factory is reused "unchanged."** Rejected as factually wrong: the
  shipped factory's resolver dispatch and `data:`-ref derivation are hardwired to the
  model path (verified in [`mutations/fields.py`][mutations-fields]), so the form
  flavor demands the three seam generalizations above — a real `fields.py` change, not
  a no-op reuse.
- **Exposing only from `django_strawberry_framework.forms`.** Rejected: the bases are
  used in schema modules alongside root-exported types, exactly as
  [`DjangoMutation`][glossary-djangomutation] is root-exported.

### Changes this Decision underwent

- **Revision 1** pinned the two-base public surface, and the three
  field-factory axes the card must generalize into overridable seams.
- **Post-ship:** **axis 1's parenthetical was wrong on its own date, and the spec
  lost.** It offered "a duck-typed `_mutation_meta` + `_payload_type_name` check" as
  the generalized target check, but `_payload_type_name` is a **bind** output while
  [`DjangoMutationField`][glossary-djangomutationfield] is constructed at import, when
  `@strawberry.type class Mutation` evaluates — before the bind runs — so a check
  requiring it could never pass. `mutations/fields.py::_validate_mutation_target` says
  so explicitly at `HEAD`. The axis now states the shipped protocol
  (`mutations/fields.py::_has_mutation_protocol`): a `_mutation_meta` attribute,
  callable `resolve_sync` / `resolve_async` / `input_type_name`, and a non-`None`
  `input_module_path`, with concreteness a separate own-snapshot-plus-current-ledger
  check. Axes 2 and 3 graded conformant and keep their derivation prose; only the
  lead-in's future tense ("this card must generalize") was made present.

## Decision 6 — Base-class strategy: `DjangoModelFormMutation` rides the `DjangoMutation` base; the plain form is the model-less sibling

Spec: [Decision 6 — Base-class strategy: `DjangoModelFormMutation` rides the `DjangoMutation` base; the plain form is the model-less sibling][spec-038-d6].

### Justification (moved from the spec)

subclassing [`DjangoMutation`][glossary-djangomutation] for the
`ModelForm` flavor reuses the maximum shipped machinery for zero new
model-pipeline code, and the [`_resolve_model`][spec-036] seam was built for it. The
plain-form model-less case is genuinely different (no model row to return), so a
sibling base is the honest shape rather than bending the model-required base.

### Alternatives considered (and rejected)

- **Make the plain `Form` also subclass [`DjangoMutation`][glossary-djangomutation]
  by relaxing the model requirement (the unified architecture).** Rejected: even
  with the `_validate_meta` seam making the model-requirement overridable, a
  model-less plain form would force model-less branches into *every* model-centric
  step of [`bind_mutations`][mutations-sets] (`_resolve_primary_type(meta.model)`,
  `build_payload_type(object_type=primary_type, …)`) and the payload-slot derivation,
  rippling the no-model case through the model-driven path the model + ModelForm
  flavors share. A contained sibling base with its own small registry + bind keeps
  the model-driven `_bind_mutation` free of model-less conditionals. (The cost — a
  parallel registry + `bind_form_mutations()` + a `finalizer.py` wiring line — is
  named explicitly in [Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change),
  not hand-waved.)
- **Honor `Meta.return_field_name`.** Rejected: it forks the payload object-field
  name across flavors, the exact collision the `036` uniform slot was frozen to
  prevent.

A third rejected alternative, recorded in the Decision body rather than in the
block above and moved from there verbatim:

Rejected (recorded, not silently dropped): **cleaned-data echo** — graphene-django's
plain `DjangoFormMutation` echoes `form.cleaned_data` as output fields (its
`fields_for_form` is dual-purposed for input *and* output). Rejected for `0.0.12`
because (a) `cleaned_data` is heterogeneous and includes values with no clean GraphQL
output mapping (a `forms.FileField`'s cleaned value is an `UploadedFile`; a
`ModelChoiceField`'s is a model instance), so a faithful echo would need a second
output-type generator and ad-hoc per-type rules; (b) the plain form is a
parity-completeness flavor where a predictable success flag is sufficient — a consumer
that needs to return data uses a model-backed `DjangoModelFormMutation` (which returns
the `node` / `result` object); and (c) `ok` + `errors` is trivially well-typed for a
model-less payload and keeps the cross-flavor `errors` envelope identical. The
asymmetry still mirrors graphene-django's split (its `DjangoModelFormMutation` is
model-backed; its `DjangoFormMutation` is not) — only the model-less *output* shape
differs, deliberately.

### Changes this Decision underwent

- **Revision 1** pinned the base-class strategy — `DjangoModelFormMutation`
  rides the [`DjangoMutation`][glossary-djangomutation] base via the
  [`_resolve_model`][spec-036] seam, the plain `DjangoFormMutation` is the
  model-less sibling with the pinned `ok` + `errors` payload.
- **Post-ship:** the plain form still has its **own** metaclass over its own
  disjoint ledger — the contract is intact — but the *mechanism* is now a shared
  factory: `DjangoFormMutationMetaclass = make_meta_validating_metaclass(register_form_mutation, …)`
  from [`mutations/sets.py`][mutations-sets], landed by the write-stack DRY
  consolidation (`5165314b`, 2026-07-01), which also gave both flavors' `resolve_sync`
  / `resolve_async` a shared `resolver_seams(...)` factory and reduced
  `bind_form_mutations()` to one `bind_write_declarations(...)` call. It shipped in
  `731fecd8` as a hand-written `class …(type)`.
- **Post-ship:** the Decision's one-builder-one-ledger payload contract holds, but the
  `## Implementation plan` spelling of it (`build_payload_type(object_type=None)`) was
  never the shipped signature: `object_type` is keyword-**required** with no default,
  and `forms/sets.py::bind_form_mutations` selects the model-less shape by passing a
  `resolve_object_type` that returns `None`. The plan cell now carries the real
  signature.
- **Post-ship:** the form allowed-key set is **two** sets, not one, and both this
  Decision's body and the `## Slice checklist` under-described it — including on their
  own date, since both sets already existed at `731fecd8`.
  `_ALLOWED_MODELFORM_META_KEYS` is `MODEL_BACKED_WRITE_META_KEYS | {form_class}` and
  `_ALLOWED_PLAIN_FORM_META_KEYS` is `COMMON_WRITE_META_KEYS | {form_class}`, so the
  plain flavor additionally drops `operation` (correctly, per Decision 10) **and**
  `select_for_update`, the post-`038` row-locking key a model-less mutation has
  nothing to lock with.
- **Post-ship:** the plain-form payload paragraph's "fully-pinned resolution of the
  prior preferred/fallback uncertainty" framing was a chronology hedge whose referent
  (the `## Risks and open questions` body) left the spec when this companion was
  created. The shape is unchanged; the framing is gone.

## Decision 7 — Form-field → Strawberry input mapping: the form is the input source of truth

Spec: [Decision 7 — Form-field → Strawberry input mapping: the form is the input source of truth][spec-038-d7].

### Justification (moved from the spec)

the form — not the model — is the validation and field contract a
form-mutation consumer chose; a plain `Form` can declare fields with no model column
(a `confirm_email`, a `captcha`), which the model-column `036` generator cannot
express. Deriving from `form_class.base_fields` (the stable class-level field set) is
the only correct source, and it is exactly what graphene-django's `fields_for_form`
does. Reusing the read-side converters where types overlap keeps the wire contract
symmetric without duplicating the scalar table.

### Alternatives considered (and rejected)

- **Derive the input from the model's editable columns (reuse the `036`
  generator).** Rejected: it drops form-only fields and ignores form-level
  `required` overrides — wrong for a plain `Form`, and divergent from the consumer's
  declared form contract for a `ModelForm`.
- **A parallel form-field scalar table independent of the read converters.**
  Rejected: it would let a `choices` form field resolve to a different enum than the
  read side, breaking the symmetric wire contract; reuse the shipped registry.

### Changes this Decision underwent

- **Revision 1** pinned the form-derived input mapping — the fail-loud
  converter dispatch, the `input_attr → (form_field_name, kind)` reverse map, the
  visibility-on-every-branch relation decoder, and the shape-identity / naming /
  collision discipline.
- **Post-ship:** `_SCALAR_FORM_FIELDS` gained a **`forms.JSONField` →
  `strawberry.scalars.JSON`** row in `efb7bda5` (2026-07-15, "map JSON fields to
  JSON"). It has to be an explicit row: `JSONField` subclasses `CharField`, so without
  its own entry the MRO walk resolves to the parent and types a JSON payload as
  `String`, rejecting the object / array literals the form field accepts. The row is
  now in the Decision's converter list, the `## Slice checklist` Slice-1 enumeration
  and `## Definition of done` item 2 — the twelfth row of a table the spec had
  enumerated as eleven.
- **Post-ship:** `NullBooleanField` requiredness became a **three**-case rule in
  `5737ddda` (2026-07-15, "keep null booleans optional on every path"), single-sited
  in `forms/converter.py::form_field_required` and shared by the annotation path and
  `forms/inputs.py`'s build site so the column-backed and column-less paths cannot
  drift: an exact `NullBooleanField` is forced optional, a subclass keeps its declared
  requiredness, and a non-null-column-backed field keeps `required=True`. The spec's
  one-line `bool | None` mapping was true of the common case and silent on the other
  two.
- **Post-ship:** the reverse-map record type is single-sited on
  `utils/inputs.py::InputFieldSpec`, landed by the serializer card
  (`60dbf469`, spec-039, 2026-06-27) when a second write flavor needed the same
  record. `forms/converter.py` now owns only the four `kind` constants and re-exports
  them from `utils/inputs.py`. The spec described an `(input_attr, graphql_name) →
  (form_field_name, kind)` tuple local to `forms/inputs.py`; the shipped record adds
  `related_model` (recorded at build time) and the serializer-only `source` /
  `nested_specs` axes, and names the form field through the neutral `target_name`.
  The record's **ownership** statement had five homes, not the two the reconciliation
  reached: the Decision body and the `## Slice checklist` Slice-1 sub-check were
  corrected, while the `## Implementation plan` Slice-1 cell, `## Definition of done`
  item 2 and the `## Test plan` `test_converter.py` row went on attributing the record
  to `forms/converter.py` — two of them under a `forms/converter.py` subject, so they
  contradicted the corrected Decision rather than merely lagging it. All three now
  name the shared `utils/inputs.py::InputFieldSpec` and place the per-field record at
  the `forms/inputs.py` build site; the `test_converter.py` row keeps its tier (the
  clauses are pinned in `tests/forms/test_inputs.py`, which is correct placement
  rather than a gap) and only its record spelling changed.
- **Post-ship:** the relation decode is no longer a form-local decoder over `036`
  primitives. `utils/write_values.py::decode_visible_relation` (`e9c13f55` /
  `8bac47be`) is now the single spine every write flavor rides and the owner of the
  cross-flavor invariant that a writer never attaches a row it cannot see; the form
  flavor supplies only the `empty_values` skip and the `to_field_name` projection,
  with `decode_field_handlers` / `decode_provided_fields` owning the `UNSET` strip and
  the `kind` dispatch. `036`'s `_decode_relation_id_set` — which the spec named three
  times as the helper NOT reused, because it skipped the visibility hook on the raw-pk
  branch — no longer exists as a symbol; the gap it left is closed inside the shared
  spine, for both branches. **The visibility-on-every-branch security contract
  survived the rewrite verbatim**; only the mechanism sentence changed.
- **Post-ship:** the input-shape cache key is a **4-tuple**. `a2418106` (2026-08-16,
  "materialize one-shot form field declarations before reuse") added
  `forms/sets.py::_form_input_hook_identity(mutation_cls)` as a fourth component —
  `None` unless the mutation overrides `get_form_fields`, otherwise the mutation class
  — so two mutations over one form with different field-discovery overrides cannot
  dedupe to one input. The conceptual identity is unchanged; the spec's 3-tuple simply
  omitted a discriminator. Fixed in this Decision, `## Definition of done` item 2 and
  the Slice-1 / Slice-2 checklist clauses.
- **Post-ship:** there are **two** narrowing guards, not one, keyed on the same
  `get_form_kwargs` / `get_form` waiver. `cf3293cf` (2026-06-26) added
  `forms/inputs.py::guard_partial_required_column_less_fields`, which rejects an
  `update` narrowing that drops a required **column-less** field — the reconstruction
  can only supply model-backed fields, so dropping a declarative extra finalizes a
  form whose bound validation fails on every request. The Decision's "`update` is
  exempt" clause was therefore false and is replaced; scoping the partial guard to
  column-less fields is load-bearing, since reusing the create guard would wrongly
  reject the model-backed fields the partial path legitimately drops.
- **Post-ship, not written into the spec:** two further `forms/inputs.py` guards
  landed that the spec is silent about and that the reconciliation judged too narrow
  to promote into a Decision — `_guard_input_attr_collisions` (two form fields whose
  generated input attrs or GraphQL names collide, e.g. a `ModelChoiceField` `category`
  emitting `category_id` beside a literal `category_id` field) and
  `_model_less_relation_annotation`'s reject for a plain-`Form` relation field whose
  `queryset` is `None` in the uninstantiated `base_fields` schema-time discovery reads.
  Both are recorded here so a later reader does not mistake the spec's silence for
  their absence.
- **Post-ship:** the field-discovery paragraph's "This replaces the earlier
  'instantiate `form_class()` no-arg' plan" chronology was rewritten to state the
  prohibition directly. The rule is unchanged.

## Decision 8 — Resolver pipeline: instantiate → `is_valid()` → `form.errors` → `save()` → optimizer re-fetch → payload

Spec: [Decision 8 — Resolver pipeline: instantiate → `is_valid()` → `form.errors` → `save()` → optimizer re-fetch → payload][spec-038-d8].

### Justification (moved from the spec)

`form.is_valid()` / `form.save()` is the Django-native form contract
graphene-django uses; routing `form.errors` into the frozen envelope (rather than
raising) is the one-contract promise; reusing the `036` locate / authorize /
transaction / re-fetch steps means the form flavor inherits every composition `036`
already proved.

### Alternatives considered (and rejected)

- **Run the model's `full_clean()` in addition to `form.is_valid()`.** Rejected:
  double validation, and a plain `Form` has no model to clean; the form's validation
  is authoritative.
- **A separate per-flavor transaction / async shape.** Rejected: the one-`atomic()`
  / one-`sync_to_async` boundary `036` set is the proven foundation; reuse it.

### Changes this Decision underwent

- **Revision 1** pinned the `form.errors` →
  [`FieldError`][glossary-fielderror-envelope] pipeline and the partial-update
  reconstruction.
- **Post-ship: the pipeline order changed, and the spec was left narrating the
  change instead of stating it.** The shipped order is **locate → authorize → decode →
  construct/validate → write → re-fetch → return**, and it is a security boundary: the
  decode issues visibility-scoped `get_queryset` queries, so decoding before the
  write-auth check let an unauthorized caller probe related-object visibility by id,
  and a top-level `GraphQLError` denial versus an in-band relation
  [`FieldError`][glossary-fielderror-envelope] is an observable distinction. The
  correction landed with the serializer card (`60dbf469`, spec-039, 2026-06-27), which
  lifted the whole sequence into
  `mutations/resolvers.py::run_write_pipeline_sync` #"authorize BEFORE decode" so the
  ordering is owned in one place for every flavor. Until this reconciliation the spec
  carried an `Ordering correction — authorize runs BEFORE the relation decode
  (post-ship security fix).` paragraph plus the sentence "the step numbers below
  reflect the original draft sequence", and **left its seven numbered steps in the
  superseded order** — a reader had to apply a chronology to recover the contract,
  which `docs/builder/BUILD.md` `## Spec rationale extraction` forbids. Slice 2
  renumbered the steps (old 2 → 1 locate, old 3 → 2 authorize, old 1 → 3 decode; steps
  4-7 keep their numbers), deleted the narration, and swept the step citations. **The
  Decision heading was deliberately NOT rewritten**: its arrow sequence says nothing
  about decode-versus-authorize, and 28 in-page `](#decision-8…` links in the spec plus
  this companion's own `[spec-038-d8]` definition resolve through it.
  One residue of that renumber outlived it: the preamble's citation of the shared
  runner read "whose own docstring states it as **step 3**". True of
  `run_write_pipeline_sync`'s own six-item docstring list, in which authorize is third
  — and false in the only enumeration a reader of this Decision has, where step 3 is
  the decode, immediately below. Two enumerations, one bare ordinal, in adjacent
  sentences. The citation is now by content (`#"authorize BEFORE decode"`) with no
  ordinal, which is what `START.md` means by citing a contract by content and never by
  ordinal; the nine surviving `step N` citations inside the spec all resolve against
  this Decision's own renumbered list.
- **Post-ship:** the "Helper reuse" paragraph's helper-location list was stale in
  three places **and wrong on its own date in a fourth.** At `HEAD` the promoted
  helpers live in three modules: `locate_instance`, `coerce_lookup_id`,
  `authorize_or_raise`, `refetch_optimized`, `build_payload`, `not_found_error` and
  `save_or_field_errors` in [`mutations/resolvers.py`][mutations-resolvers];
  `validation_error_to_field_errors` in `utils/errors.py`; `raw_choice_value` in
  `utils/write_values.py`. The fourth is `payload_object_slot`, which the paragraph
  listed among the helpers this card promoted: it was **already public** in
  `mutations/inputs.py` at `731fecd8^`, before `038` began, so that clause was false
  when written — and the spec's own `## Current state` bullet said so, making two spec
  homes contradict each other. `## Current state` was the right one; the promotion list
  lost the name.
- **Post-ship:** the paragraph also carried an **unresolved build instruction** —
  "the lighter edit is dropping the leading underscore … the cleaner edit is lifting
  them to a neutral `mutations/_pipeline.py` … Slice 3 picks one and names it" — which
  has no place in a shipped contract. Slice 3 picked underscore-drop-in-place; no
  `mutations/_pipeline.py` exists. The spec now states where the helpers live and the
  two-options deliberation is retired.
- **Post-ship:** the form pipeline is no longer a per-flavor body calling helpers by
  name. `forms/resolvers.py` imports `make_resolver_entries` and
  `run_write_pipeline_sync` from [`mutations/resolvers.py`][mutations-resolvers] and
  `pipeline_write_phase` from `utils/write_transaction.py`, supplying only the
  form-specific decode and write steps: the seven-step sequence is a **shared runner
  the form flavor parameterizes**. The observable contract the steps describe is
  unchanged; the implementation prose was not.
- **Post-ship:** the one-`transaction.atomic()` sentence is no longer the whole
  boundary story. The runner also pins the transaction to one write alias
  (`open_write_pipeline` / `pipeline_alias_guard` / `check_instance_write_alias`,
  the `0.0.14` mutation-atomicity work), captures an immutable
  `authorized_pk` / `target_state` snapshot right after the locate so a later step
  cannot retarget the write, and calls `check_deadline(info)` **before** the
  transaction opens (the `spec-047` cooperative deadline). A form mutation inherits
  every one, so the Decision and the Slice-3 checklist now say so.
- **Post-ship:** step 4's update reconstruction has **three** shapes, not one
  `model_to_dict` formula, because an omitted field must bind in the same shape a
  provided one decodes to: `model_to_dict` for scalars and a `to_field_name`-less
  FK / one-to-one, `_to_form_key_value` per member for a real forward M2M, and
  `_to_form_key_value` for a `ModelChoiceField` **with** `to_field_name`. It also reads
  the form's **full** declared field set (`get_form_fields`), not the narrowed input.
  The one-shape formula had **four** normative homes — Decision 8 step 4, the Slice-3
  checklist, the `## Edge cases` update-preservation bullet and
  `## Definition of done` item 4 — and all four were corrected.
- **Post-ship (spec addition, not a correction):** step 4's file clause is correct and
  survived the renumber verbatim, with one clause appended: the reconstruction
  contributes **no key at all** for a file field, because `model_to_dict` yields the
  stored relative path, which is not a re-bindable `data=` value for a field fed from
  `files=`. The addition is earned rather than decorative — no wire-level row of any
  design can detect the exclusion's removal, since a file widget's
  `value_from_datadict` reads `files` only and a stray `data=` key is inert, so the
  exclusion is a data-hygiene boundary whose only observable is the reconstructed
  payload. A reader taking the previous sentence as the whole story believed a live
  test covered it, and for three patch releases none did.
- **Post-ship (spec addition):** the `get_form_kwargs` step's queryset clause read as
  though the hook mutates `field.queryset` itself, which it cannot. It now says the
  hook returns **constructor kwargs**, so the hook is the channel and the form applies
  the narrowing in its own `__init__` — and carries an appended clause recording that
  such an injection is only *observably* working if a test asserts the **written row**,
  because the wire envelope of a failed write is identical whether the injection ran
  or not (a missing non-nullable FK raises `IntegrityError` too and maps to the same
  `"__all__"` envelope). Measured twice by two workers on this cycle.
- **Post-ship:** the required-extra bullet's "both failure modes the review names"
  citation named an authority neither the spec nor this companion carries, and was
  reduced to "both failure modes" — the bullet already enumerates them.

## Decision 9 — Optimizer composition: the `ModelForm` payload re-fetch rides the `spec-036` G2 path

Spec: [Decision 9 — Optimizer composition: the `ModelForm` payload re-fetch rides the `spec-036` G2 path][spec-038-d9].

### Justification (moved from the spec)

reusing the `036` re-fetch is the whole point of subclassing
[`DjangoMutation`][glossary-djangomutation] — the G2 composition and the
by-pk-without-visibility contract come for free, with no new optimizer code and no
new live-test handoff (the `036` Slice 4 G2 test already discharged the
[`spec-035`][spec-035] obligation).

### Alternatives considered (and rejected)

- **Return `form.save()`'s instance without re-fetching.** Rejected: a freshly
  saved instance has no related rows loaded, so any relation in the response
  selection N+1s — exactly the failure the `036` re-fetch prevents.

### Changes this Decision underwent

- **Revision 1** pinned the optimizer composition reusing the `036` re-fetch
  path.
- **Post-ship:** graded against `HEAD` and unchanged in contract. Two spellings were
  corrected: the helper is `refetch_optimized`, not `_refetch_optimized`, and the
  by-pk-without-visibility-filter exception was labelled "the `036` Medium-1
  exception" — a review-finding identifier undecodable from any spec — now stated as
  "the `036` re-fetch exception" with its reason (the actor just wrote the row) intact.

## Decision 10 — Operations: `create` / `update` for the `ModelForm`, no form `delete`

Spec: [Decision 10 — Operations: `create` / `update` for the `ModelForm`, no form `delete`][spec-038-d10].

### Justification (moved from the spec)

matching the upstream operation set keeps the parity surface honest;
a form `delete` would be a new contract with no graphene-django precedent and a
redundant overlap with the shipped model-driven `delete`.

### Alternatives considered (and rejected)

- **Add a form `delete`.** Rejected: no upstream precedent, and the model-driven
  `delete` is the existing path; adding it would invent surface the card does not
  ask for.

### Changes this Decision underwent

- **Revision 1** pinned the operation set (`create` / `update`, no form
  `delete`) and the plain base's outright rejection of `Meta.operation`.
- **Post-ship:** graded against `HEAD` and unchanged. The operation split is exactly
  as pinned. The closing sentence framed it as "the single resolution of the prior
  contradiction (one shared checklist rule that read as if the plain base also took
  `create` / `update`)" — a chronology whose referent the reader cannot find — and now
  states the split directly.

## Decision 11 — Write authorization: reuse the `036` seam (`DjangoModelPermission` for the `ModelForm`, explicit classes for the plain form)

Spec: [Decision 11 — Write authorization: reuse the `036` seam (`DjangoModelPermission` for the `ModelForm`, explicit classes for the plain form)][spec-038-d11].

### Justification (moved from the spec)

reusing the `036` write-auth seam is the card's explicit
reuse-the-foundation posture; the `ModelForm` flavor gets it for free, and the
plain-form case keeps the safe-by-default stance `036` established rather than
silently shipping an unauthenticated write surface.

### Alternatives considered (and rejected)

- **A new form-specific permission class.** Rejected: the `036` seam already covers
  the `ModelForm` flavor, and a plain form's authorization is a consumer choice, not
  a model-permission one.

### Changes this Decision underwent

- **Revision 1** pinned permission reuse —
  [`DjangoModelPermission`][glossary-djangomodelpermission] for the `ModelForm`
  flavor, an explicit `Meta.permission_classes` for the plain form.
- **Post-ship:** the plain-form permission posture is settled, so the "**Preferred
  resolution:**" framing and its "settled with its fallback in Risks" pointer are
  gone: an unset `Meta.permission_classes` resolves to `(DenyAll,)`
  (`forms/sets.py::DjangoFormMutation._validate_meta`), and a public plain-form write
  is the explicit `Meta.permission_classes = []` opt-in. The `## Edge cases`
  plain-form-authorization bullet said an unset key **fails configuration**, which is
  false and was the losing side of a two-home disagreement with this Decision.
- **Post-ship:** the plain base additionally **rejects** a
  [`DjangoModelPermission`][glossary-djangomodelpermission] subclass in
  `Meta.permission_classes` at class creation — that class resolves its codename from
  `mutation._resolve_model(mutation.Meta)`, which a model-less mutation never
  supplies, and the generic permission-class validation accepts it, so without the
  targeted reject the misconfiguration finalized cleanly and surfaced only as a raw
  `AttributeError` at request time. The Decision settled the *default* and said
  nothing about an explicitly-set model-permission class; it now covers both.

## Decision 12 — Live coverage: products grows a `ModelForm` and a plain `Form` mutation

Spec: [Decision 12 — Live coverage: products grows a `ModelForm` and a plain `Form` mutation][spec-038-d12].

### Justification (moved from the spec)

the [`AGENTS.md`][agents] live-HTTP-priority rule makes the products
write surface the right home for form-mutation acceptance coverage; products already
has the `Item` constraint and the `Mutation` wiring `036` added, so the form surface
is a small additive extension, not a new app.

### Alternatives considered (and rejected)

- **Synthetic-model-only coverage (no live surface).** Rejected: form mutations are
  live-reachable the moment products exposes them, and the
  [`AGENTS.md`][agents] rule prioritizes the live `/graphql/` test where a realistic
  request reaches the path.

### Changes this Decision underwent

- **Revision 1** pinned the products live form surface.
- **Post-ship:** the live form surface is wider than products. The Decision's
  narrowing to `test_products_api.py` was faithful when written, and products is still
  the card's own home, but as a standing description of the live surface it was
  incomplete: `examples/fakeshop/apps/library/` exposes `CreateShelfViaForm`,
  `UpdateBookViaForm`, `CreateBranchWithShelf` and `CreateBranchPair` (earning the
  non-Relay raw-pk decode, the `to_field_name` conversion, the request-scoped-queryset
  idiom and the plain-form `perform_mutate` rollback), and
  `examples/fakeshop/apps/scalars/` exposes `CreateMediaSpecimenImageViaForm`.
  Products itself carries **eight** form mutations, not the six a mid-cycle reading
  would have found: this cycle's own Slice 1 added `updateItemWithFileViaForm` and
  `createDefaultCategoryItemViaForm` to close two proven test gaps. The figure was
  re-derived twice — eight classes, eight `DjangoMutationField` rows.

## Decision 13 — Finalization seam: reuse the mutation phase-2.5 bind, no `DEFERRED_META_KEYS` change

Spec: [Decision 13 — Finalization seam: reuse the mutation phase-2.5 bind, no `DEFERRED_META_KEYS` change][spec-038-d13].

### Justification (moved from the spec)

the `ModelForm` flavor reuses the one finalization gate via the
`build_input` seam (the materialize-before-`Schema` discipline
[`spec-027`][spec-027] / [`spec-028`][spec-028] / `036` all share); the plain form's
own registry + `bind_form_mutations()` is the contained cost of keeping the
model-driven `_bind_mutation` free of model-less branches
([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)).
Leaving `DEFERRED_META_KEYS` untouched honors the cross-subsystem invariant.

### Alternatives considered (and rejected)

- **A separate public `finalize_django_forms()` entry point.** Rejected: a second
  gate the consumer must remember to call; `bind_form_mutations()` hangs off the
  existing `finalize_django_types()` phase-2.5 window instead.
- **Claiming the `036` bind materializes the form input "unchanged."** Rejected as
  false: `_materialize_input_for` builds a model-column input from `meta.model`
  (verified in [`mutations/sets.py`][mutations-sets]); the form flavor must swap the
  generator via the `build_input` seam.

### Changes this Decision underwent

- **Revision 1** pinned the finalizer-bind reuse, the three `registry.clear()`
  co-clear rows, and the shared `make_declaration_registry` mechanics over two
  disjoint ledgers.
- **Post-ship:** the three form clears still exist and are all reached, but
  `registry.py` names **none** of them. `60dbf469` (spec-039, 2026-06-27) inverted the
  wiring: each owning module announces its own clear via
  `register_subsystem_clear(...)` under a stable owner key —
  `forms.input_namespace` (registered `before_bind=True`), `forms.declarations` and
  `forms.shape_cache` — and `registry.clear()` drains `iter_subsystem_clears()`. That
  keeps `registry.py` free of per-subsystem imports and makes a reload replace an
  owner's callback rather than duplicate it. The contract ("`registry.clear()` clears
  three form rows") is unchanged; the Decision's "co-clears" mechanism and the
  `## Implementation plan` Slice-2 cell naming `registry.py` as the file that gains
  the rows were both false and are corrected.
- **Post-ship:** the shared-mechanics / disjoint-ledgers call now has a **third**
  consumer the spec could not have named — `auth/mutations.py` instantiates
  `make_declaration_registry` alongside `mutations/sets.py` and `forms/sets.py`. That
  is live evidence for the Decision rather than a correction to it, and
  `## Out of scope` now says so where it names the auth flavor.

## Decision 14 — This card owns the `0.0.12` version bump

Spec: [Decision 14 — This card owns the `0.0.12` version bump][spec-038-d14].

### Justification (moved from the spec)

`038` closes the `0.0.12` feature set (it is the only card in it), so
it owns the cut. The bump moves only after the bases, tests, and docs are complete
(Slice 5), never in Slice 1.

### Alternatives considered (and rejected)

- **Defer the bump to a separate release-alignment card.** Rejected: no such
  `0.0.12` card exists; a deferral would orphan the bump.
- **Bump in Slice 1.** Rejected: the version should move only after the feature and
  docs are complete.

### Changes this Decision underwent

- **Revision 1** pinned **this card owning the `0.0.12` version bump**.
- **Post-ship:** the `0.0.12` cut happened and its figures are **not** stale — the
  package is now `0.0.15`, three patch releases on, and nothing about the release this
  card closed was "updated". What changed is the *mechanism*: the Decision aligned a
  version **quintet**, and at `HEAD` there are three surfaces, not five.
  `AGENTS.md` #"The release is single-sourced" made `__version__` the only literal:
  `pyproject.toml` carries no `version` key at all (`[tool.hatch.version]` derives its
  packaging metadata from `__init__.py`) and `uv.lock` records the package as
  `source = { editable = "." }` with no version key, so the Decision's trailing
  "`uv.lock` if it carries the package version" conditional now resolves to "it does
  not". Corrected in this Decision, `## Definition of done` item 8 and the Slice-5
  checklist.

## Risks and open questions

The spec's whole `## Risks and open questions` body. Nine of its fourteen items
already carried a `RESOLVED` marker recording that a Decision had answered the
question outright; the other five pair a preferred answer for the `0.0.12` cut
with a fallback if implementation proved the preferred answer wrong. Both shapes
are a build-time deliberation instrument, not a contract, so the body moved and
the spec keeps the heading and a pointer here. Nothing was held back: every rule
any item states is also stated by the Decision that answered it or by the spec's
`## Edge cases and constraints`, so no item carries a sentence the implementation
depends on. Two of the fourteen are card-citation tensions the cut chose to record
rather than silently reconcile.

Each item names a preferred answer for the `0.0.12` cut and a fallback if
implementation reveals it is wrong.

- **The plain-`Form` payload shape (model-less) — RESOLVED, no longer open.**
  Pinned in [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)
  as the fixed two-field shape `ok: Boolean!` + `errors: [FieldError!]!` with the
  `perform_mutate(self, form, info) -> None` hook (default `form.save()`-if-present
  else no-op). Cleaned-data echo (graphene parity) was considered and rejected for
  `0.0.12` (heterogeneous `cleaned_data` has no clean GraphQL output mapping; the
  plain form is a parity-completeness flavor; a data-returning consumer uses a
  `DjangoModelFormMutation`). There is no remaining preferred/fallback ambiguity — an
  implementer cannot ship a divergent plain-form shape.
- **`ModelForm` partial-update semantics — RESOLVED.** Pinned in
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload):
  `update` reconstructs the full bound payload from the located instance overlaid with
  the provided fields (`data = {**model_to_dict(instance, non-file fields),
  **provided_data}`, `files = provided_files`), so a bound `ModelForm` validates the
  whole set while omitted fields are preserved — the `036` `PartialInput` contract,
  not graphene-django's full update. The alternative (graphene-style full update,
  dropping `PartialInput` and requiring all form-required fields) was rejected for
  cross-flavor consistency with the model-driven `DjangoMutation.update`. Fallback if
  the reconstruction proves leaky for an exotic form (custom non-model fields with
  required-on-partial semantics): narrow to graphene-style full update for that form
  via an opt-in, never silently — but the package default is partial.
- **Form-input shape identity + collision — RESOLVED.** Pinned in
  [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)
  as the `036`-parallel identity `(form_class, operation kind, frozenset(effective
  field names))` with canonical / shape-derived names, dedupe, and a finalize-time
  [`ConfigurationError`][glossary-configurationerror] for two distinct shapes on one
  generated name (same form / different narrowings, and different forms / same
  `__name__`). No remaining ambiguity — an implementer cannot silently reuse the wrong
  input class or hit a late Strawberry name clash.
- **Relation-id visibility in the form decode — RESOLVED (a restored `036`
  invariant).** Pinned in
  [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)
  / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload):
  the `relation_single` / `relation_multi` decode type- and visibility-checks the id
  through the related primary `DjangoType.get_queryset` **before** the form, so the
  form's non-request-scoped default queryset is not the only guard — a hidden target
  is the same field-keyed `FieldError` as the model-mutation path. (Earlier revisions
  delegated this to `ModelChoiceField.to_python`, which dropped the invariant; fixed.)
- **Form `Meta` / base validation hardening — RESOLVED.** Pinned: a
  `ModelForm` on the plain `DjangoFormMutation` base is rejected at class creation
  ([Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)),
  a required non-model extra field stays required on `update`
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)),
  and `Meta.fields` / `Meta.exclude` are normalized + fail-loud against `form_class.base_fields`
  (bare string / duplicate / unknown name / empty set →
  [`ConfigurationError`][glossary-configurationerror],
  [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)),
  mirroring the `036` model-mutation validators.
- **Raw-pk relation visibility — RESOLVED (security).** The `036`
  `_decode_relation_id_set` passes a raw pk through with **no** visibility hook (only
  the Relay-`GlobalID` branch is scoped), so it is **not** reused unchanged; a
  dedicated form relation decoder
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)
  / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload))
  resolves every branch (Relay + raw pk, single + multi) through the related primary
  `get_queryset` before the form, closing the non-Relay hole.
- **Write-time `IntegrityError` — RESOLVED.** The form write reuses the `036`
  `_save_or_field_errors` mapper, so a post-validation concurrent-race / residual
  constraint at `form.save()` (or the plain-form save) returns the `FieldError`
  envelope, not a top-level error
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
- **Form-construction hooks — RESOLVED.** Schema-time discovery reads
  `form_class.base_fields` (no instantiation; overridable `get_form_fields()`), and
  runtime construction goes through `get_form_kwargs(info, *, data, files,
  instance=None)` / `get_form(...)` (the graphene-django parity seam) so a
  kwarg-requiring or queryset-scoping migrated form works
  ([Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)
  / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)).
- **`to_field_name`, plain-form `operation`, create-narrowing, converter dispatch,
  file-clear — RESOLVED.** `to_field_name` honored in the relation decoder
  (#6); plain `DjangoFormMutation` rejects any `Meta.operation` and uses the `"form"`
  shape sentinel (#4); a `create` narrowing dropping a required field raises (#7,
  waived under a `get_form_kwargs` override); the converter's fallthrough raises with
  no base-`forms.Field` catch-all (#5); file **clearing** is explicitly out of scope
  for `0.0.12` (upload + preserve only, #8).
- **Generalizing the field factory (dispatch + ref + target check).** Preferred
  answer ([Decision 5](#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root)):
  generalize [`DjangoMutationField`][glossary-djangomutationfield] along all three
  hardwired-to-model axes — the target check (accept the mutation/form family), the
  `_resolve` dispatch (call `mutation_cls.resolve_sync` / `resolve_async` so a form
  flavor routes to [`forms/resolvers.py`][forms-resolvers]), and the `data:` lazy-ref
  derivation (consult `mutation_cls.input_type_name` + `input_module_path`) — each
  defaulting to today's model behavior, so one factory exposes every flavor with no
  model-flavor regression. Fallback: a thin net-new `DjangoFormMutationField` (its own
  dispatch + ref) for the form flavors only, if generalizing the shipped factory's
  dispatch proves invasive — but the seam approach is preferred because the `0.0.13`
  [`SerializerMutation`][glossary-serializermutation] flavor needs the same three
  generalizations.
- **Plain-form write-authorization default.** Preferred answer
  ([Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form)):
  the plain form keeps the safe-by-default posture — an unset `permission_classes`
  denies (no model-permission default exists without a model), so a public plain-form
  write is an explicit `Meta.permission_classes = []` opt-in. Fallback: ship a
  permissive `AllowAny`-style built-in the plain form defaults to, if deny-by-default
  proves too strict for the common "public contact form" case — never weaken the
  `ModelForm` default.
- **Card conflict — `Meta.return_field_name`.** The card lists
  `Meta.return_field_name` as part of the DRF-style surface, but [`spec-036`][spec-036]
  Decision 7 (AR-H5) **froze** the uniform `node` / `result` payload slot to keep one
  cross-flavor client contract. Preferred reading: honor the frozen `036` slot and
  do **not** adopt `Meta.return_field_name` (the card's own dependency, the
  [`FieldError` envelope][glossary-fielderror-envelope] reuse, implies the frozen
  payload shape). Recorded per the [`docs/SPECS/NEXT.md`][next] "prefer the card,
  surface the conflict" rule; the fallback is to support `return_field_name` as an
  optional override aliasing the uniform slot if a consumer needs the graphene-django
  field name verbatim for migration.
- **Card-citation note — the spec filename vs the card's `docs/spec-form_mutations.md`.**
  The card DoD names `docs/spec-form_mutations.md`; the structured convention
  authors at `docs/SPECS/spec-038-form_mutations-0_0_12.md`
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)). Recorded, not
  silently reconciled, per the [`docs/SPECS/NEXT.md`][next] boundary rule.
- **`form.save(commit=False)` vs `form.save()` for relation timing.** Preferred
  answer ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload)):
  the `ModelForm` flavor calls `form.save()` (commit=True) directly — for a `ModelForm`
  with M2M fields this already runs `save_m2m()` **internally**, so a single
  `form.save()` inside the one `transaction.atomic()` is correct and complete (no
  separate M2M step). Fallback: switch to `commit=False` + explicit `instance.save()`
  + `form.save_m2m()` (still inside the transaction) only if a consumer needs the saved
  instance *before* its M2M rows are written (e.g. a `clean()` that inspects the pk) —
  a contained resolver change, not a contract change.

## Non-Decision deliberation

Findings and provenance that belong to no single Decision.

- **The `Justification:` / `Alternatives considered (and rejected):` pairing is
  1:1 across all fourteen Decisions, and that is a measured result rather than an
  inference from two equal counts.** The `037` execution of this move found a
  Decision with a justification and no alternatives and another with the reverse,
  and had to carry an explicit `None.` in both files so a later reader could not
  mistake a genuine absence for a chunk the move dropped. `spec-038` needed
  neither: the two label lists interleave strictly and each pair sits under
  exactly one Decision heading.
- **The fourteen `Decision N` anchors survived the move untouched.** `spec-036`'s
  execution had to repair a broken slug with 16 uses and re-point five uses across
  four anchors naming spec sections its companion lacked; `spec-037` carried
  neither defect. Nor does `spec-038`: all 36 anchor occurrences in the moved text
  resolve locally here, because the fourteen Decision headings are reproduced
  character-for-character.
- **The glossary gate, not the carve-out, decided what stayed.** The
  implementation-relevance carve-out
  ([`docs/builder/BUILD.md`][build-md] `## Spec rationale extraction`) would have
  held back
  [Decision 13](#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change)'s
  single-finalize-call clause on its own merits. It would **not** have held back
  [Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions)'s
  sibling-surface parenthetical, which is ordinary deliberation; that one stayed
  because it carries the spec's only links to two of the terms
  `check_spec_glossary.py` gates. Worth naming because the coupling is invisible
  from either document: a spec's `-terms.csv` silently pins which prose the
  rationale move may not take, and the failure surfaces as a gate exit 1 rather
  than as a reading error.
- **Every moved block was checked against the carve-out, and the normative
  statement each one explains survives in the spec.** The two rejected
  alternatives most at risk of taking a contract with them were
  [Decision 9](#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path)'s
  ("return `form.save()`'s instance without re-fetching" — rejected because a
  freshly saved instance N+1s on any relation in the selection) and
  [Decision 7](#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth)'s
  ("a parallel form-field scalar table" — rejected because a `choices` field would
  resolve to a different enum than the read side). Both Decision bodies state the
  requirement normatively without the rejection: Decision 9's body pins the
  by-pk re-fetch through the `036` optimizer path, and Decision 7's body carries
  the whole over-DRY-into-drift paragraph. Neither move can produce the defect its
  rejection warns about.
- **Post-ship: the spec's own emphasis labels were undecodable, and the sweep split
  two ways.** `spec-038` keyed its emphasis to `P1` / `P2` / `P3` priority tiers and to
  bare `#4`-`#8` review-finding numbers — **62 occurrences** at the point Slice 2
  swept them — with no legend anywhere in the spec or this companion. Those are
  orphaned review residue under `START.md` "Style Rio cares about" and were removed,
  the sentence's own contract wording carrying the emphasis instead; not one of them
  added a clause. The five `AR-H1` / `AR-H4` / `AR-H5` / `AR-M6` / `Medium-1`
  identifiers were graded separately, and **verified against their spec before being
  touched**: all five resolve inside [`spec-036`][spec-036] (7 / 14 / 6 / 12 / 3
  occurrences there), so they were decodable — but they are review-finding labels
  rather than spec-decision pointers, so each was replaced by the contract it
  labelled (`AR-H4` → "the `036` id-type-check contract", `AR-H1` / `AR-M6` → "the
  `036` second-different-class-under-one-name raise", `Medium-1` → "the `036`
  re-fetch exception", `AR-H5` → the surviving `spec-036 Decision 7` pointer). No WHY
  was lost in either group.
- **Post-ship: the promotion renamed nine helpers, and the spec kept using the old
  spellings outside the paragraph that announced it.** Six underscore-prefixed names
  the spec used in normative sentences no longer exist at `HEAD` at all
  (`_locate_instance`, `_coerce_lookup_id`, `_authorize_or_raise`,
  `_refetch_optimized`, `_validation_error_to_field_errors`, `_raw_choice_value`), as
  did `_decode_relation_id_set` and `_coerce_relation_pk_or_none`. Slice 2 corrected
  the ones that assert what the shipped pipeline **calls** and deliberately left the
  ones inside `## Current state`, whose vintage framing dates them, and the ones
  naming the `036` starting point a Decision explicitly frames as such
  (`_validate_mutation_meta`, `_materialize_input_for`, `_bind_mutation`,
  `_normalize_field_sequence`, `_shape_build_cache` all still exist). This class was
  in no routed list: the paragraph announcing the promotion was, but its parallel
  spellings elsewhere were not — the residual-defect shape `START.md` describes as
  "one spelling fixed, parallel site still live".
- **Post-ship: `## Current state` was graded clause by clause and owes no edit.** All
  five bullets are dated **observations** of the pre-build repo, which stand under
  `docs/builder/BUILD.md` `### `## Current state`: observations stand, predictions do
  not`, even the two the shipped card falsified. The one clause needing a real check
  was the parenthetical quoting [`docs/TREE.md`][tree] as reserving `forms/` and
  `tests/forms/` "planned by `TODO-ALPHA-038-0.0.12`" — a **quotation of a generated
  body**, so Slice 2 diffed it against both renders rather than reasoning about it:
  the phrase occurs **twice** in `docs/TREE.md` at `731fecd8^` (exactly the two rows
  the bullet describes) and **zero** times in the current render, where those rows now
  read "Form-mutations subsystem …". So the quotation was true on its own date and is
  a dated observation, not a false claim; the observation framing carries it. The
  borderline "there is no joint cut to defer the version bump to" clause is an
  inference rather than a reading, but the inference held.
- **Post-ship: the concurrent session's uncommitted hardening of `forms/` was NOT
  written into the spec.** Five guards exist only in the working tree at the time of
  this reconciliation — a `str.isidentifier` / `keyword.iskeyword` field-name guard, a
  guarded `base_fields` read, two out-of-vocabulary `operation_kind` raises, a typed
  wrap around the `get_form_fields` hook invocation, and the multi-relation container
  check lifted to `utils/write_values.py::materialize_relation_id_container`. An
  uncommitted guard is not a shipped contract and may be revised or dropped before its
  own cycle commits, so all five were routed to the cycle's deferred-work catalog
  instead. Recorded here so a later reader does not read the spec's silence as their
  absence.
- **Post-ship: the terms-CSV coupling bound this pass too, and the deletions were
  checked against it before being made.** Slice 0 discovered that
  [`spec-038-form_mutations-0_0_12-terms.csv`][spec-038-terms] silently pins which
  prose may be removed, because `check_spec_glossary.py` requires every term to keep
  at least one **link** in the spec. Slice 2 removed considerably more prose than the
  move did — a whole narration paragraph, a two-options deliberation, 62 emphasis
  labels — and no term lost its last link: the gate reports `OK: 31 terms` before and
  after. One link definition did fall orphaned (`utils-querysets`, whose only two uses
  were inside the retired `mutations/_pipeline.py` deliberation) and was pruned; it is
  a source-path label, not a CSV-pinned glossary anchor, so pruning it is safe. Seven
  new definitions were added for modules the shipped contract now names
  (`auth-mutations`, `mutations-operations`, `rest-framework-package`,
  `testing-package`, `utils-errors`, `utils-write-transaction`, `utils-write-values`).
- **Routed to the maintainer, out of this slice's reach.** The cycle is fenced to
  spec files and package `.py` source, so no closeout-agentflow doc was touched.
  [`docs/GLOSSARY.md`][glossary]'s
  [`DjangoFormMutation`][glossary-djangoformmutation] entry is the published home
  of the plain-form sibling contract
  [Decision 6](#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling)
  pins, and the spec's `## Key glossary references` described that entry's
  correction as Slice 5 work it "must" do — future tense about a shipped card's own
  closeout. Slice 2 graded it: the rendered [`docs/GLOSSARY.md`][glossary] carries both
  entries as `shipped (0.0.12)`, both in Public exports and the Mutations browse row,
  with the `DjangoFormMutation` body already rewritten to the model-less-sibling
  shape, so the promise is discharged and only the tense was wrong. The spec now
  states the entries' shipped contract instead of promising to correct them.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[kanban]: ../../../KANBAN.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary]: ../../GLOSSARY.md
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[glossary-djangoformmutation]: ../../GLOSSARY.md#djangoformmutation
[glossary-djangomodelpermission]: ../../GLOSSARY.md#djangomodelpermission
[glossary-djangomutation]: ../../GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: ../../GLOSSARY.md#djangomutationfield
[glossary-fielderror-envelope]: ../../GLOSSARY.md#fielderror-envelope
[glossary-filterset]: ../../GLOSSARY.md#filterset
[glossary-finalize_django_types]: ../../GLOSSARY.md#finalize_django_types
[glossary-orderset]: ../../GLOSSARY.md#orderset
[glossary-serializermutation]: ../../GLOSSARY.md#serializermutation
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-027]: ../spec-027-filters-0_0_8.md
[spec-028]: ../spec-028-orders-0_0_8.md
[spec-035]: ../spec-035-optimizer_hardening-0_0_10.md
[spec-036]: ../spec-036-mutations-0_0_11.md
[spec-038-d10]: ../spec-038-form_mutations-0_0_12.md#decision-10--operations-create--update-for-the-modelform-no-form-delete
[spec-038-d11]: ../spec-038-form_mutations-0_0_12.md#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelform-explicit-classes-for-the-plain-form
[spec-038-d12]: ../spec-038-form_mutations-0_0_12.md#decision-12--live-coverage-products-grows-a-modelform-and-a-plain-form-mutation
[spec-038-d13]: ../spec-038-form_mutations-0_0_12.md#decision-13--finalization-seam-reuse-the-mutation-phase-25-bind-no-deferred_meta_keys-change
[spec-038-d14]: ../spec-038-form_mutations-0_0_12.md#decision-14--this-card-owns-the-0012-version-bump
[spec-038-d1]: ../spec-038-form_mutations-0_0_12.md#decision-1--spec-filename-and-canonical-naming
[spec-038-d2]: ../spec-038-form_mutations-0_0_12.md#decision-2--card-scope-boundary-the-two-form-flavors-ship-serializer--auth-stay-out-the-frozen-036-contracts-are-reused-unchanged
[spec-038-d3]: ../spec-038-form_mutations-0_0_12.md#decision-3--class-meta-surface-not-graphenes-mutationoptions
[spec-038-d4]: ../spec-038-form_mutations-0_0_12.md#decision-4--module-and-test-locations-forms-subpackage-mirroring-mutations
[spec-038-d5]: ../spec-038-form_mutations-0_0_12.md#decision-5--public-surface-djangoformmutation--djangomodelformmutation-exported-from-the-root
[spec-038-d6]: ../spec-038-form_mutations-0_0_12.md#decision-6--base-class-strategy-djangomodelformmutation-rides-the-djangomutation-base-the-plain-form-is-the-model-less-sibling
[spec-038-d7]: ../spec-038-form_mutations-0_0_12.md#decision-7--form-field--strawberry-input-mapping-the-form-is-the-input-source-of-truth
[spec-038-d8]: ../spec-038-form_mutations-0_0_12.md#decision-8--resolver-pipeline-instantiate--is_valid--formerrors--save--optimizer-re-fetch--payload
[spec-038-d9]: ../spec-038-form_mutations-0_0_12.md#decision-9--optimizer-composition-the-modelform-payload-re-fetch-rides-the-spec-036-g2-path
[spec-038-terms]: spec-038-form_mutations-0_0_12-terms.csv
[spec-038]: ../spec-038-form_mutations-0_0_12.md

<!-- docs/builder/ -->
[build-038]: ../../builder/build-038-form_mutations-0_0_12.md
[build-md]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->
[forms-resolvers]: ../../../django_strawberry_framework/forms/resolvers.py
[mutations-fields]: ../../../django_strawberry_framework/mutations/fields.py
[mutations-resolvers]: ../../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../../django_strawberry_framework/mutations/sets.py

<!-- tests/ -->
[test-forms]: ../../../tests/forms/

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
