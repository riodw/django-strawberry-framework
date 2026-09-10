# Rationale companion: spec-039 (DRF serializer mutations — `SerializerMutation`)

Companion to [`docs/SPECS/spec-039-serializer_mutations-0_0_13.md`][spec-039]. It
carries that spec's **deliberative layer** and nothing else: the ten-revision authoring
history that produced the contract, every Decision's justification, every alternative a
Decision rejected and why it lost, the two one-sentence chronology fragments two Decision
bodies were carrying inline, the risk / open-question deliberation that settled the
card's design questions, and the preamble's account of where the improvement set
came from. The spec carries the contract; this file carries how the contract was arrived
at. Neither duplicates the other — the text here **left** the spec.

Read this when checking a finished implementation against the reasoning that produced it,
or before re-opening a settled question. Worker 2 never reads it
([`docs/builder/BUILD.md`][build-md] `### Who reads it, and when`).

**How later passes append to this file.** Each Decision below carries a
`### Changes this Decision underwent` section. A reconciliation pass that finds the spec
stale against `HEAD` — a guard that shipped differently, a helper that never landed where
the Decision said it would, a default a later card inverted — appends a `**Post-ship:**`
bullet there, naming the shipped behavior and the card or commit that changed it. A
Decision a reconciliation checked and found still true earns a bullet too, saying so — a
measured no-change and an unexamined one read identically otherwise. Findings belonging to
no single Decision go under [Non-Decision deliberation](#non-decision-deliberation).
Nothing needs restructuring to take an addition, and the corrections themselves always
land in the spec, stated directly and without chronology.

## Provenance of this record

Created by Slice 0 of the `039` residual-reconciliation cycle, whose plan is
[`docs/builder/build-039-serializer_mutations-0_0_13.md`][build-039] and whose record of
the move itself is the per-cycle artifact
[`docs/builder/bld-039-slice-0-rationale_extraction.md`][bld-039-slice-0]. `spec-039`
shipped in `0.0.13` with a [`-terms.csv`][spec-039-terms] companion and no `-rationale.md`
sibling; this file closes that gap. Nothing in it is new reasoning: every passage below
was cut from the spec in the same pass that created this file, except the framing
paragraphs, the `### Changes this Decision underwent` summaries, and the
[Non-Decision deliberation](#non-decision-deliberation) entries, which are this pass's own
and say so. The `034` / `035` / `036` / `037` / `038` companions are the five
immediately-preceding executions of the same move and this file matches their shape —
[`spec-038`][spec-038]'s most closely, since `spec-039` is its structural twin.

The spec was verified byte-identical to `HEAD` before the first edit
(`git show HEAD:docs/SPECS/spec-039-serializer_mutations-0_0_13.md` into a scratch path
outside the repo, diffed clean against the working copy) at **343,592 bytes, 4,354
lines**. It stood at **296,665 bytes, 3,725 lines** when the move
finished: **53,853 bytes cut** by six routes, **6,926 bytes** of pointers, link
definitions and two hold-backs added back, for a net **46,927 bytes** removed.

- **The whole `Revision history (kept inline so the spec is self-contained):` block** —
  its preamble line, the blank line under it, ten `Revision N` entries and the trailing
  blank: 310 lines, **26,041 bytes**. The ten entries are reproduced under
  [Revision history](#revision-history) below; the 61-byte preamble line was **deleted,
  not moved** — its claim that the history is kept inline is exactly what this move made
  untrue.
- **14 `Justification:` blocks**, one under every Decision, **7,649 bytes**. Reproduced
  under each Decision's heading; the 14 labels became `###` headings here — 1 stood on
  its own line (Decision 1) and 13 were inline prefixes stripped from the paragraph they
  introduced (Decisions 2-14), which is why those sections open lower-case.
- **14 `Alternatives considered (and rejected):` blocks**, one under every Decision,
  carrying **31** rejected alternatives, **9,766 bytes**. All 14 labels stood on their own
  line and all 14 became `###` headings here. **The pairing is 1:1** — as in the `038`
  execution, and unlike `037`, where two Decisions each carried one half of the pair and
  both files needed an explicit `None.` — so no Decision below has a missing section.
- **Two one-sentence chronology fragments carried inline in Decision bodies** —
  [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)'s
  "This reverses the earlier draft's `stays in __all__` choice …" (**171 bytes**) and
  [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)'s
  "(An earlier draft lumped `uv.lock` with the version files …)" (**130 bytes**). Each is
  reproduced verbatim under its Decision's `### Changes this Decision underwent`. Both
  sentences state only how the Decision reached its current form; the contract each one
  trails is asserted by the paragraph it sat in, which stayed.
- **The body of `## Risks and open questions`** — its two-line preamble plus **9** items,
  118 lines, **9,525 bytes**. Eight of the nine are written as preferred-answer /
  fallback pairs and the ninth is a card-citation tension recorded rather than silently
  reconciled; both shapes are a build-time deliberation instrument rather than a contract,
  so the body moved and the spec keeps the heading and a pointer here. **One record inside
  it was held back rather than moved** — see below.
- **The improvement section's preamble** — 7 lines, **571 bytes**. It narrates where the
  improvement set came from (a review pass proposed sixteen improvements plus one
  follow-on) and closes "This section records the design of each." The **seventeen
  improvement subsections themselves did not move**: each states a shipped contract, which
  is the spec's job. The replacement preamble states the same scope without the
  chronology.

**The census used the shortest distinctive token, not the label phrase.**
`grep -oin 'ustification'` over the pre-move spec finds **14** occurrences and
`grep -oin 'lternatives'` finds **14** — every one of them a block label, so neither count
is a vocabulary sample of a larger population. The two label lists interleave strictly
(each `Justification:` is immediately followed by its `Alternatives considered (and
rejected):`, and each pair sits under exactly one of the 14 `### Decision N` headings),
which is what establishes the 1:1 pairing rather than an inference from the equal counts.
The 31 rejected alternatives are the top-level `- **` bullets inside the 14 blocks:
2 / 2 / 2 / 3 / 2 / 3 / 3 / 3 / 1 / 2 / 1 / 3 / 3 / 1 for Decisions 1-14. The 9 Risks
items and the 10 Revision entries are the top-level `- **` bullets of their own sections,
counted the same way. The improvement subsection count is **17**, measured from the
section's own `###` heading list — each subsection present exactly once — not from the
preamble's own "16 + 1" arithmetic.

**Every in-page anchor inside the moved text resolves, and five were deliberately
re-pointed.** The moved text carries **73 anchor occurrences across 19 distinct anchors**.
Fourteen are the `#decision-N--…` slugs and one is `#risks-and-open-questions`; this file
carries headings with exactly those slugs — the fourteen Decision headings are reproduced
character-for-character from the spec, so their GitHub slugs are identical — so those
**68** occurrences needed no re-pointing. The remaining **5**, all inside the revision
history, name spec sections this companion does not carry
(`#test-plan`, `#borrowing-posture`, `#implementation-plan`, and `#cross-flavor-reuse-and-dry-obligations`
twice). Left inline they would have dangled, so each is now a reference-style link into
the spec and resolves in one hop.

**One record was held back in the spec, and it is not a glossary hold-back.** The DRF
floor bullet in `## Risks and open questions` ended in a **`Recorded floor (Slice 0,
verified): djangorestframework>=3.17.0`** statement — a measured, normative record, and
the spec's only statement of the pinned floor, which the Slice 0 checklist calls one of
"three places that must agree". Moving it would have taken a contract out of the contract,
so it was appended to the surviving normative sentence it explains, in
[Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)'s
soft-dep-coverage item, and the **five** spec references that reached for it through the
Risks heading — two Slice 0 checklist sub-checks, the `## User-facing API` partial-update
paragraph, [Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation)'s
live-coverage list, and the `## Test plan` partial-update row — were re-pointed at Decision
12. The record itself is **not** reproduced under
[Risks and open questions](#risks-and-open-questions) below: a hold-back that also appears
here would be a copy, and the move admits none. The deliberation that surrounded the
record — why the CI matrix under `-W error` is the binding constraint rather than
serializer-API availability, and what happens if no compatible release exists — moved here
with the rest of the item.

**One clause was held back for the glossary gate.**
`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-039-serializer_mutations-0_0_13.md`
requires every term in [`spec-039-serializer_mutations-0_0_13-terms.csv`][spec-039-terms]
to keep at least one link in the spec, and two of its 38 terms —
[`FilterSet`][glossary-filterset] and [`OrderSet`][glossary-orderset] — had their **only**
spec link inside prose this move cuts: the sibling-surface parenthetical in
[Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions)'s
justification, which said the serializer flavor "is uniform with them (and with
`DjangoType` / `FilterSet` / `OrderSet`)". Pruning their now-unused link definitions would
have failed the gate, and editing the CSV is not the fix. The Decision body already
asserts the mutation is "declared exactly like every other consumer surface in the
package"; the enumeration now names which surfaces those are, at that sentence, and the
justification below keeps the claim without it. **This is the same two terms the `038`
execution held back**, in the same parenthetical of the same Decision — the coupling is
structural, not a coincidence of wording.

Because of that hold-back, **no link definition was pruned from the spec**: a post-move
sweep found **0 dangling `][label]` uses, 0 unused definitions and 0 dangling in-page
anchors** in both files.

**Reconciliation against `HEAD` is a separate pass, and it has not run yet.** This move
checked nothing against the tree; it graded prose against the spec's own text only. The
cycle's four audit slices grade every contract row against `HEAD` and its Slice 2 rewrites
every stale contract statement, appending the `**Post-ship:**` bullets under each Decision
below and the entries under
[Non-Decision deliberation](#non-decision-deliberation). Until that has run, the absence
of a `**Post-ship:**` bullet under a Decision means **unexamined**, not **unchanged**.

**Three shapes a move cannot discharge were found and deliberately left in the spec.**
They are spec rewrites, which the reconciliation slice owns; each is recorded under
[Non-Decision deliberation](#non-decision-deliberation) with what makes it a rewrite
rather than a cut.

## Revision history

Ten revisions produced the contract: an initial draft from the card body, eight review
passes, and a final-verification reconciliation. Each Decision's
`### Changes this Decision underwent` section below reads from these entries. The block is
the spec's own, verbatim, except that five in-page anchors naming spec sections this
companion does not carry are now reference-style links into the spec. The one **post-ship**
change the spec records — the 2026-07-15 security-hardening revision — was never folded
into this history and still sits inline in the spec as an amendment blockquote; see
[Non-Decision deliberation](#non-decision-deliberation).

- **Revision 1** — initial draft authored from the [`TODO-ALPHA-039-0.0.13`][kanban]
  card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-06-26). Pinned: the
  canonical structured filename
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)); the card-scope
  boundary that ships the serializer flavor and reuses the frozen `036` contracts +
  the `038`-generalized factory, parking auth for the sibling `0.0.13` card
  ([Decision 2](#decision-2--card-scope-boundary-the-serializer-flavor-ships-auth-stays-out-the-frozen-036-contracts-and-the-038-factory-are-reused-unchanged));
  the **`class Meta`-not-`MutationOptions`** surface
  ([Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions));
  the `rest_framework/` subpackage layout
  ([Decision 4](#decision-4--module-and-test-locations-rest_framework-subpackage-mirroring-forms));
  the one-base public surface reusing the `038`-generalized factory
  ([Decision 5](#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused));
  the base-class strategy — `SerializerMutation` rides the
  [`DjangoMutation`][glossary-djangomutation] base via the [`_resolve_model`][spec-036]
  seam, `ModelSerializer`-driven
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven));
  the serializer-derived input mapping with a fail-loud converter
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
  the `serializer.errors` → [`FieldError`][glossary-fielderror-envelope] pipeline with
  DRF-native `partial=True` update
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload));
  the optimizer composition reusing the `036` re-fetch path
  ([Decision 9](#decision-9--optimizer-composition-the-modelserializer-payload-re-fetch-rides-the-spec-036-g2-path));
  the operation set (`create` / `update`, no serializer `delete`)
  ([Decision 10](#decision-10--operations-create--update-no-serializer-delete));
  permission reuse
  ([Decision 11](#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelserializer));
  the **soft `djangorestframework` dependency + the 100%-coverage strategy** (DRF out
  of runtime deps, added to the dev group, the absent path covered by simulated
  absence)
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy));
  the products live serializer surface
  ([Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation));
  and **the joint `0.0.13` cut owning the version bump**
  ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)). Four
  card-body tensions are carried into
  [Risks and open questions](#risks-and-open-questions) rather than silently
  reconciled (the card's `Meta.model_operations` vs the package's per-operation
  `Meta.operation`; the card's `Meta.lookup_field` vs the package's `id:`-decode
  locate; the card's "dual-purposed for inputs **and outputs**" converter vs the
  `036`-frozen uniform `node` / `result` slot; and a model-less plain `Serializer`
  flavor), each with a preferred reading.
- **Revision 2** — applied a code-review pass (all findings verified against the
  package source first). Foundational (shape-setting)
  fixes: (1) the resolver pipeline is reordered to **locate → authorize → decode** so
  write authorization runs **before** any relation decode — the package security
  invariant the `038` form pipeline pins
  ([`forms/resolvers.py`][forms-resolvers] #"Authorize runs BEFORE the relation decode"),
  closing a relation-visibility-probe-by-id regression
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload));
  (2) schema-time field discovery goes through an overridable
  `get_serializer_for_schema()` hook (not a bare no-arg `serializer_class()`), with
  request-dependent schema shape rejected loudly
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
  (3) renamed serializer fields (`source`) are designed — supported `source` scope, a
  GraphQL-name-from-field-name rule, backing-column resolution via `source`, and the
  declared name preserved in the now-`(serializer_field_name, source, kind)` reverse map
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
  (4) a **dedicated recursive `serializer.errors` flattener** with a dotted path
  convention (`items.0.name`, `NON_FIELD_ERRORS_KEY` → `"__all__"` at every level)
  replaces the implicit reuse of the one-level `036` mapper
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)).
  Plus: the serializer-input ledger clears in the
  [`finalize_django_types`][glossary-finalize_django_types] **pre-bind reset block**
  (not only `TypeRegistry.clear()`) for retry-idempotence
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven));
  the soft-DRF root export is pinned to a root `__getattr__` + a shared `require_drf()`
  with the exact behavior of all four import forms and a cache-eviction rule for the
  absent-path test
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy));
  `uv.lock` is reconciled as **updated** (the DRF dev-group add) while the package
  version stays `0.0.12`
  ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)); and the
  smaller gaps — `optional_fields = "__all__"` rejected as a bare string,
  `permission_classes` kept explicitly in the serializer allowed-key set, and the
  runtime serializer `context` resolved via the shared `request_from_info` helper
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)
  / [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)).
- **Revision 3** — applied a second code-review pass (again verified against the package
  source first; the form `guard_create_required_fields` /
  `_cached_build_form_input` per-declaration precedent and the
  `save_or_field_errors` return-discard were confirmed in code). Foundational
  (shape-setting) fixes: (1) serializer input identity is now a **`SerializerInputShape`
  descriptor** (the emitted field specs + normalized `optional_fields`), not the
  name-only `(class, op, names)` key — two same-named shapes that differ in requiredness
  or in `get_serializer_for_schema()`-returned field specs get distinct deterministic
  names or a `ConfigurationError`, never silent cache reuse
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
  (2) a **create-required narrowing guard** (`guard_create_required_serializer_fields`,
  the form `guard_create_required_fields` analog) fails at bind, per declaration, before
  the descriptor cache lookup, when `Meta.fields` / `Meta.exclude` drops a writeable
  required-no-default field; `Meta.injected_fields` is the only explicit subtraction
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
  Plus: an **id-like-suffix rule** so a relation field already named `*_id` / `*_pk` is
  not double-suffixed (`category` → `categoryId`, `category_id` → `categoryId`,
  `category_pk` → `categoryPk`)
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
  a **value-preserving save** — the resolver captures `serializer.save()`'s returned
  object in the `save_or_field_errors` closure (called once) and re-fetches by its pk,
  rather than re-deriving from a return the wrapper discards
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload));
  and the root `__getattr__` is pinned to **not memoize** `SerializerMutation`, with the
  absent-DRF test also evicting the root attribute
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
- **Revision 4** — applied a third code-review pass (test-placement, verified against
  [`examples/fakeshop/test_query/README.md`][test-query-readme] #"Coverage rule.",
  [`docs/TREE.md`][tree] #"Coverage priority.", the existing
  [`test_uploads_api.py`][test-uploads-api] live-multipart precedent, and the
  [`Item.attachment`][products-models] `FileField`). **Foundational restructuring:** the
  five-slice plan collapses to **four** — the serializer resolver pipeline and the
  products live serializer surface now land in **one** slice (Slice 3), so every
  consumer-reachable resolver line is earned by a real `/graphql/` request *at the commit
  it appears* (a separate live slice would leave reachable lines package-covered at the
  resolver commit, the inverse of the live-first rule)
  ([Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation)).
  [`test_products_api.py`][test-products-api] becomes the **primary** harness for every
  reachable branch (happy paths, envelopes, reverse-map, partial-update, visibility,
  write-auth, authorize-before-decode, **the multipart `Upload` write**, **the
  request-context `validate()` path**, and the G2 query shape — the last two are shipped
  `0.0.13` runtime branches, so they move from package tests to live), and
  [`tests/rest_framework/test_resolvers.py`][test-rest-framework] is narrowed to the
  residue a live query cannot drive (recursive-flattener shapes, raw-pk/non-Relay +
  many-relation decode, call-once save, `IntegrityError`, sync/async + `SyncMisuseError`,
  hermetic kwargs seams). The [Test plan][spec-039-test-plan] now states the **explicit
  package-test boundary** so the new `tests/rest_framework/` tree cannot accrete
  resolver-acceptance coverage. The old Slice 5 (docs + soft-dep + card wrap) is now
  Slice 4 throughout.
- **Revision 5** — applied a fourth code-review pass (every claim verified against the
  package source first: the finalizer's **direct, unconditional** mutation / form clears
  ([`types/finalizer.py`][types-finalizer] #"clear_mutation_input_namespace"),
  `TypeRegistry.clear()`'s `_clear_if_importable` asymmetry, the
  [`django.yml`][django-workflow] CI matrix × [`pytest.ini`][pytest-ini]
  `filterwarnings = error`, `fail_under = 100`, and DRF's lazy `.fields` were all
  confirmed). **Foundational (shape-setting) fixes:** (1) the pre-bind
  `clear_serializer_input_namespace()` is pinned **import-guarded** (`try/except
  ImportError` / `_clear_if_importable`) — `rest_framework/inputs.py` is behind the DRF
  soft-import guard while the mutation / form clears are direct unconditional imports, and
  [`finalize_django_types`][glossary-finalize_django_types] runs on **every** DRF-absent
  schema build, so a literal mirror would `ImportError` and break schema construction for
  every DRF-absent consumer
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven),
  Slice 2 checklist); (2) the **DRF version floor** open question becomes a concrete
  **pre-Slice-1 check gated by the CI matrix under `-W error`** — the dev-group DRF must
  import / run warning-free on (Python 3.14, Django 6.0 / `latest`); DRF's Django support
  lags Django releases, so a compatible release must be confirmed before pinning and a
  targeted DRF-origin `ignore::` line budgeted — the binding constraint, not
  `NON_FIELD_ERRORS_KEY` availability
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)
  / [Risks](#risks-and-open-questions)). Plus: a **save-time `ValidationError`** (from a
  custom `create()` / `update()` / model `full_clean()`) is routed through the recursive
  flattener into the envelope — split by exception type from `IntegrityError`, never a
  top-level `GraphQLError`
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)
  step 6); the `get_serializer_for_schema()` loud-rejection guard wraps **`.fields`
  materialization**, not `serializer_class()` (DRF builds `.fields` lazily, so a
  context-requiring serializer fails at `.fields` access, not construction)
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
  the carried `is_input` parameter is pinned **accepted-and-ignored with no `if not
  is_input:` branch**, so it adds no uncovered line under `fail_under = 100`
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth));
  the partial-update unique-together fire is flagged a **DRF behavior** (DRF backfills the
  unchanged member from `serializer.instance`) tied to the verified floor; the mutation's
  `Meta.fields` (input surface) vs the serializer's own `Meta.fields` (validation) are
  clarified as **distinct namespaces** and `Meta.optional_fields` noted a no-op on
  `update`; `ListField` is scoped to **scalar children** (a relation / nested-serializer
  child raises); the `rest_framework/` name-collision test cost is named at
  [Decision 4](#decision-4--module-and-test-locations-rest_framework-subpackage-mirroring-forms);
  and the stale "Slice 5" CHANGELOG reference is corrected to Slice 4.
- **Revision 6** — applied a [`GOAL.md`][goal] + working-reference cross-reference pass
  (every claim verified first: [`GOAL.md`][goal]'s crit-6 serializer example really does
  show the `DjangoMutation` base with **no** `operation`, while the model sibling and
  prose carry an explicit `operation = "create"`; and the shipped `DjangoMutation`
  **requires** an explicit `operation` — a missing key is a `ConfigurationError`,
  [`spec-036`][spec-036] — so defaulting it for the serializer flavor would make it the
  only write flavor that infers the op). **Foundational (surface-reconciliation) fixes:**
  the spec's public surface (`SerializerMutation` base + mandatory `operation`) and
  GOAL.md's crit-6 example diverged, and nothing in Slice 4 reconciled them — now (1)
  [Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)
  weighs the GOAL-literal "`DjangoMutation` detects `serializer_class`" alternative and
  justifies the `SerializerMutation` base on **by-name `graphene-django` migration
  parity** (crit 7); (2)
  [Decision 10](#decision-10--operations-create--update-no-serializer-delete) pins
  `operation` mandatory (uniform with the family that already requires it) and frames the
  real crit-7 friction (the migrant adds an `operation` key + splits one auto-dispatching
  mutation into two); (3) the **Slice-4 GOAL.md edit now explicitly corrects the crit-6
  example** to the `SerializerMutation` base + `operation = "create"`, asserting the
  read-only-`id`-dropped `CategorySerializerInput { name: String! }` shape; and (4) the
  [Risks](#risks-and-open-questions) `model_operations`-alias fallback is elevated to the
  named near-term crit-7 affordance. Plus: a note that the `django-graphene-filters`
  cookbook is **query/filter-only**, so reference parity for this card is graphene-django's
  `rest_framework`, not the cookbook ([Borrowing posture][spec-039-borrowing-posture]); the
  `get_serializer_kwargs` parity row reflagged **name-borrowed, not signature-compatible**
  (a graphene override can't carry over verbatim); the serializer flavor framed as the
  deliberate **crit-7 exception that keeps its source package** (`djangorestframework` is
  the reused validation engine, not a runtime to shed); and the fail-loud converter's
  relation/file mapping pinned as **mandated by [`GOAL.md`][goal]'s "don't silently weaken
  rich relations" non-goal**, not stylistic
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
- **Revision 7** — applied a DRY / cross-flavor reuse pass (every reuse claim verified
  against the source first — the relation-decode fork, `_VALID_FORM_OPERATIONS`, the
  shape-cache "twin of" comment, the sync-pipeline orchestration copies, the two
  hand-maintained ledger-clear lists, the `build_input` seam cluster, the field-spec /
  namespace / typo-guard duplications, and the absence of any `register_subsystem_clear`
  seam were all confirmed; corrections folded in: the form bases normalize via
  `forms/sets.py::_resolve_effective_form_field_names` not `_normalize_field_sequence`, no
  `field_error(...)` ctor exists yet, `_form_kwargs_overridden` is the helper to
  generalize). Added a **[Cross-flavor reuse and DRY obligations][spec-039-dry]**
  section: the confirmed reuses locked as import obligations, **seven third-copy-fork
  promotions** to single-site now (**P1.1** relation-decode core → `_visible_related_object`
  in `utils/querysets.py`; **P1.2** `NON_DELETE_WRITE_OPERATIONS`; **P1.3** shape-build cache
  plumbing; **P1.4** fail-loud converter dispatch skeleton → `utils/converters.py`; **P1.5**
  the sync write-pipeline orchestration — a **security** ordering, the highest-value
  promotion; **P1.6** a `register_subsystem_clear` seam collapsing the two hand-edited clear
  lists; **P1.7** the `build_input` build/stash/name cluster), **seven single-siting items**
  (**P2.1**–**P2.7**: unified field-spec, the one-ledger namespace trio, `_pascalize_token`,
  the leaf-error sentinel/ctor, the `_validate_meta` sub-validators, `_hook_overridden`, the
  `reject_unknown_meta_keys` typo-guard), the **P3** pin-as-import list + a deliberately
  NOT-applicable list, and a per-`rest_framework/`-module **import manifest** (the DoD-checkable
  DRY contract). Each promotion is pinned into its Decision
  ([4](#decision-4--module-and-test-locations-rest_framework-subpackage-mirroring-forms) /
  [6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven) /
  [7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth) /
  [8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload) /
  [10](#decision-10--operations-create--update-no-serializer-delete)) and its Slice DoD
  line, and the [Implementation plan][spec-039-implementation-plan] (the per-slice file lists +
  the "no regression" item) is reconciled to show the promotions touch `mutations/` /
  `utils/` / `forms/` / `types/finalizer.py` / `registry.py` **net-near-zero**
  (extract-and-re-point), behavior-preservingly (the `036` / `038` suites stay green).
- **Revision 8** — applied a deep-architecture review (11 findings, each verified against
  the source + the new `TODO(spec-039 Slice N)` anchors before editing). **Contract-precision
  fixes:** **(F1)** `SerializerMutation` is **removed from `__all__`** while DRF is soft — a
  star import consults `__all__` and would trip the `__getattr__` DRF guard, breaking
  `from … import *` for DRF-absent consumers (verified: the root has eager `__all__` + no
  lazy precedent); it stays a **named** lazy export, with a star-import soft-dep test added
  ([Decision 5](#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused) /
  [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
  **(F2)** save-time `ValidationError` is **split by class** — DRF's `.detail` → the
  recursive flattener, Django's `error_dict` / `messages` → the flat `036`
  `validation_error_to_field_errors` (verified: the `036` mapper reads Django's shape, not
  `.detail`), two separate tests
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)).
  **(F3)** the generated relation input carries **one** strategy-dependent annotation
  (Relay → `GlobalID`, else raw-pk scalar; verified via products'
  malformed-`GlobalID`-is-top-level-coercion test); "accepts both" is the shared decode
  *helper*'s contract, package-tested by direct call (Decisions 7/8). **(F4)** serializer-only
  relation fields are **supported via `field.queryset.model`** (else rejected) — the
  previously-undefined write-only-`PrimaryKeyRelatedField` case (Decision 7). **(F5)** the
  error flattener keys `FieldError.field` to the **GraphQL input name** via the reverse map
  (serializer name only when no input field exists), with a live renamed-field test
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)).
  **(F6)** `run_write_pipeline_sync` is **scoped to model-backed create/update only** (delete +
  plain form excluded) with a precise `decode_step` / `write_step` callback contract and a
  byte-equivalence requirement on the existing model/form suites
  (the [sync write-pipeline skeleton][spec-039-dry] promotion). **(F7)** `get_serializer_kwargs`
  precedence pinned — framework-owned `partial=True` (`ConfigurationError` on `partial=False`),
  merged request `context`. **(F8)** Slice 4 splits **implemented-on-main** docs from
  **release** ("shipped (0.0.13)" / README "Shipped today" / changelog) docs, the latter
  deferred to the joint cut ([Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).
  **(F9)** the live request-context proof is an explicit `validate()`, not a `HiddenField`
  (subtle under `partial=True`). **(F10)** `register_subsystem_clear` uses static
  `(module_path, attr)` rows (no DRF import at registration), with the import-time invariant
  stated. **(F11)** the DRF dev-dependency wiring + floor probe moves to a **pre-Slice-1
  gate (Slice 0)**, since Slice 1–3 tests import DRF. Plus the config assessment: serializer
  relation decode consumes the recorded `effective_globalid_strategy`, never
  `conf.settings` / `_resolve_globalid_strategy` on the query path.
- **Revision 9** — applied an architecture-pass review (3 H + 5 M findings + missing edge
  cases, each verified against the source before editing). **(H1)** normalized the Slice 0 /
  Slice 4 wording across the Status block, Goals item 8, and Decision 14 (the soft-dep wiring
  + `uv.lock` regen are owned by the **Slice 0 gate**, Slice 4 is docs + card-wrap only) —
  the stale "Four slices" / "soft-dep wiring in Slice 4" prose contradicted the gate.
  **(H2)** rewrote the **Write-time `ValidationError`** edge case (and the DoD Slice 3 item)
  to **split by exception class** to match Decision 8 step 6 — it previously sent a Django
  `ValidationError` (no `.detail`) down the DRF `.detail` flattener. **(H3)** made
  `context["request"]` **strictly framework-owned** — the framework sets it unconditionally
  from `request_from_info(...)`, an override supplying a *different* `request` is a
  `ConfigurationError` (actor cannot drift from the permission seam); the prior "escape
  hatch" wording is removed
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)
  step 4). **(M1)** the Slice 3 + DoD relation-id summaries now state the **one
  strategy-dependent generated shape** (shared decoder accepts both only for package-only
  branches) and include the **serializer-only `field.queryset.model`** target source.
  **(M2)** added a **Nullability and defaults** paragraph to Decision 7 (`allow_null` →
  annotation nullability; `required` + DRF `default` → omission; omitted-vs-explicit-`None`
  preserved; `allow_blank` not encoded) with tests. **(M3)** a serializer relation target
  with **no registered primary `DjangoType`** is a class-creation `ConfigurationError`, not
  a default-manager fallback — stricter than the promoted `_visible_related_object` helper,
  whose form behavior stays byte-unchanged (Decision 7). **(M4)** `register_subsystem_clear`
  is now a **mandatory Slice 2 requirement** (static `(module_path, attr)` string rows
  resolved via `_clear_if_importable`), not a budget-dependent fallback — the two-hand-edit
  option is removed. **(M5)** the current-state prose now names the cross-module DRY blast
  radius (`utils/` / `mutations/` / `forms/` / `registry.py` / `types/finalizer.py`).
  **Missing edge cases:** the request-actor-cannot-be-swapped case (H3), two serializer
  fields colliding on one generated GraphQL input name (the serializer analog of
  `forms/inputs.py::_guard_input_attr_collisions`), and two **writable** fields sharing one
  `source` (rejected as a double-write) were pinned. Plus a **Slice 0 floor acceptance
  artifact** (probe script / explicit `uv` commands; the floor recorded in `pyproject.toml`
  + the `require_drf()` hint + Risks) and a **Slice 3 grep-guard** that the serializer
  resolver reads neither `conf.settings` nor `_resolve_globalid_strategy` on the query path.
- **Revision 10** — Slice 4 final-verification reconciliation (Worker 1, build-039). All
  five slices (Slice 0 + Slices 1-4) are final-accepted and on main; the implemented-on-main
  docs (TREE / TODAY / GOAL crit-6 / the GLOSSARY body marked **"implemented on main,
  releasing in 0.0.13"** with the `status` FK kept `planned`) and the card wrap
  ([`DONE-039-0.0.13`][kanban] → Done, all 7 DoD items ticked) landed in Slice 4 (F8 /
  [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)). No version bump,
  no `CHANGELOG.md` / `README.md` Status / `docs/README.md` edit (joint-cut deferrals, F8 —
  confirmed absent from the build diff).

## Decision 1 — Spec filename and canonical naming

Spec: [Decision 1 — Spec filename and canonical naming][spec-039-d1].

### Justification (moved from the spec)

- The structured `spec-<NNN>-<topic>-<0_0_X>.md` convention pinned in
  [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card's NNN (`039`) and target patch
  (`0_0_13`) into the filename.
- The topic slug is `serializer_mutations` — short, snake-case, and naming the
  subsystem (the stem of the card DoD's suggested `docs/spec-serializer_mutations.md`).

### Alternatives considered (and rejected)

- **The card's own `docs/spec-serializer_mutations.md`.** Rejected: predates the
  structured-filename convention; [`spec-036`][spec-036] / [`spec-038`][spec-038]
  Decision 1 set the precedent of preferring the structured name and recording the
  card's older one (carried in [Risks](#risks-and-open-questions)).
- **Topic slug `serializers` / `drf` / `rest_framework`.** Rejected: `serializers`
  collides conceptually with the DRF `serializers` module name; `drf` / `rest_framework`
  name the dependency, not the subsystem capability (the mutation flavor).

### Changes this Decision underwent

- **Revision 1** pinned the canonical structured filename and the `serializer_mutations`
  topic slug over the card's own pre-convention `docs/spec-serializer_mutations.md`
  name.
- No later revision reopened it.
- **Post-ship (`039` residual reconciliation, 2026-09-05).** The Decision described the
  spec as living at the `docs/` top level and asserted that Step 8's archive sweep would
  leave it there. A later card's Step 8 sweep archived it, exactly as
  [`AGENTS.md`][agents] rule 26 prescribes — the "leaves it there" clause was only ever
  true while `039` was the single active spec. The Decision now states the stem
  convention and the archived location (`docs/SPECS/`, companions in `docs/SPECS/appx/`)
  directly. `## Definition of done` item 1 carried the same two path literals in a
  runnable command, so the command was unrunnable as written; it now names the archived
  paths and records the measured `OK: 38 terms`.

## Decision 2 — Card-scope boundary: the serializer flavor ships; auth stays out; the frozen `036` contracts and the `038` factory are reused unchanged

Spec: [Decision 2 — Card-scope boundary: the serializer flavor ships; auth stays out; the frozen `036` contracts and the `038` factory are reused unchanged][spec-039-d2].

### Justification (moved from the spec)

the card is sized **L** and auth is separately carded with its own
`0.0.13` target — pulling it forward would bloat the slice exactly as
[`START.md`][start]'s scope-creep rule warns. The foundation and the form-flavor
precedent already exist; this card's job is the serializer-specific generation +
pipeline on top of them. This is the third and last of the three flavors
[`spec-036`][spec-036] Decision 2 named as the envelope's reusers (`038` form, `039`
serializer, `040` auth).

### Alternatives considered (and rejected)

- **Ship auth mutations too** (they also reuse the envelope). Rejected: auth is its
  own `0.0.13` card with a distinct surface (`login` / `logout` / `register` +
  `current_user`, composing with `django.contrib.auth`), not a serializer-flavor
  concern.
- **Extend the `036` `FieldError` with serializer metadata.** Rejected: the card
  mandates the envelope is **reused unchanged**; forking it would break the
  one-contract promise.

### Changes this Decision underwent

- **Revision 1** pinned the card-scope boundary that ships the serializer flavor and
  reuses the frozen `036` contracts plus the `038`-generalized factory, parking auth for
  the sibling `0.0.13` card.
- No later revision reopened it.
- **Post-ship (`039` residual reconciliation, 2026-09-05).** The Decision, `## Non-goals`
  bullet 2, and `## Goals` item 3 all promised that the card added **no** field to
  `FieldError` and did not re-open [`mutations/inputs.py`][mutations-inputs] — while the
  improvement section's `ErrorDetail.code` and structured-`path` items, in the same
  document, add `codes` and `path` to exactly that type. `mutations/inputs.py::FieldError`
  carries both at `HEAD`, and `KANBAN.md` records the envelope as ADDITIVE rather than
  frozen. All three sites now state the additive contract: a member may be added, none
  removed or retyped, and the addition lands once in the shared envelope so all three write
  flavors gain it together. The "frozen" framing was `036`'s promise about *forking*, not
  about *extending*, and reading it as the latter is what let the contradiction sit in one
  document.

## Decision 3 — `class Meta` surface, not graphene's `MutationOptions`

Spec: [Decision 3 — `class Meta` surface, not graphene's `MutationOptions`][spec-039-d3].

### Justification (moved from the spec)

this is the package's defining surface contract, stated verbatim in
[`START.md`][start] ("Meta classes everywhere on consumer surfaces"). The
[`spec-036`][spec-036] [`DjangoMutation`][glossary-djangomutation] base and the
[`spec-038`][spec-038] form bases already established the nested-`Meta` mutation shape;
the serializer flavor is uniform with them. The
*capabilities* of graphene-django's `SerializerMutation` are borrowed at the outcome
level; the `MutationOptions` / `ClientIDMutation` mechanism is not. [`GOAL.md`][goal]'s
DRF-migration diff spells the surface as
`class CreateCategoryFromSerializer(DjangoMutation): class Meta: serializer_class = …`;
the card ships the **`SerializerMutation` base** instead (for the by-name
`graphene-django` migration carry-over weighed in
[Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)),
and Slice 4 updates that GOAL.md example to the shipped base so the two stop disagreeing
in print.

### Alternatives considered (and rejected)

- **graphene's `__init_subclass_with_meta__` keyword options.** Rejected: it is the
  metaclass-options surface the nested `class Meta` replaces; it also fragments the
  declaration shape away from [`DjangoMutation`][glossary-djangomutation].
- **A `@serializer_mutation(serializer_class=…)` decorator.** Rejected: a decorator on
  a consumer class is exactly the shape [`START.md`][start] forbids.

### Changes this Decision underwent

- **Revision 1** pinned the **`class Meta`-not-`MutationOptions`** surface.
- **Revision 6** reconciled the surface against [`GOAL.md`][goal]'s crit-6 example,
  which spells the declaration on the `DjangoMutation` base: the Decision records that
  Slice 4 corrects the GOAL example to the shipped `SerializerMutation` base rather than
  the spec bending to it.
- **Post-ship (`039` residual reconciliation, 2026-09-05).** Checked against `HEAD` and
  still true as written. The `class Meta` surface, its key set, and the rejection of
  graphene's `MutationOptions` / `__init_subclass_with_meta__` / `ClientIDMutation` lineage
  all hold; the `Meta` key set has since grown (Decision 6), which is a widening of the
  namespace this Decision defined, not a change to the surface it chose.

## Decision 4 — Module and test locations: `rest_framework/` subpackage mirroring `forms/`

Spec: [Decision 4 — Module and test locations: `rest_framework/` subpackage mirroring `forms/`][spec-039-d4].

### Justification (moved from the spec)

the card predicts `django_strawberry_framework/rest_framework/` and
[`tests/rest_framework/`][test-rest-framework]; the [`forms/`][forms-sets] subpackage
([`spec-038`][spec-038] Decision 4) is the proven shape for a flavor reusing the
mutation base — and `rest_framework/` is its near-exact structural twin (a converter +
an input generator + a metaclass-or-subclass + a resolver pipeline). A separate
subpackage keeps the serializer-specific generation + pipeline cleanly distinct and
behind one DRF soft-import boundary
([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
The directory name `rest_framework/` matches the card prediction and graphene-django's
own `rest_framework/` subpackage. **One cost is worth naming:** because
`django_strawberry_framework.rest_framework` shares its leaf name with DRF's own
top-level `rest_framework` package, the absent-DRF test must evict **both** `rest_framework*`
**and** `django_strawberry_framework.rest_framework*` from `sys.modules` (the two-namespace
eviction dance in
[Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).
That test-complexity is a **direct consequence of the name**, accepted here for the card +
graphene-django parity — a future reader seeing the double eviction should know it traces
to this naming choice, not to an accident of the guard.

### Alternatives considered (and rejected)

- **Fold the serializer base into [`mutations/`][mutations-sets] or
  [`forms/`][forms-sets].** Rejected: the card predicts a `rest_framework/` subpackage,
  the serializer-field converter is a distinct concern, and the DRF soft-import
  boundary wants its own module wall — one subpackage per flavor keeps each extension
  point separable (the `036` / `038` precedent).
- **A flat `rest_framework.py` module.** Rejected: the surface is a converter + an
  input generator + a base + a resolver pipeline — a subpackage matches it, and the
  card predicts `rest_framework/`.
- **Name it `serializers/` instead of `rest_framework/`.** Rejected: the card predicts
  `rest_framework/`, it matches graphene-django's layout, and it names the dependency
  boundary the soft-import guard wraps.

### Changes this Decision underwent

- **Revision 1** pinned the `rest_framework/` subpackage layout mirroring `forms/`.
- **Revision 5** added the **name-collision cost** paragraph —
  `django_strawberry_framework.rest_framework` shares its leaf name with DRF's own
  top-level `rest_framework`, so the absent-DRF test must evict both namespaces from
  `sys.modules`. That cost is a consequence of the naming choice, named so a later
  reader does not read the double eviction as an accident of the guard. The paragraph is
  normative and stayed in the spec.
- **Revision 7** pinned the DRY promotions' homes into the `**Shared-helper homes**`
  paragraph, which is an import obligation rather than deliberation and also stayed in
  the spec.
- **Post-ship (`039` residual reconciliation, 2026-09-05).** Two of the "Shared-helper
  homes" paragraph's promotion targets named addresses the code did not use. The
  relation-decode core landed as the **public** `utils/querysets.py::visible_related_object`
  (with a batched `::visible_related_objects` the spec never named), not a private
  `_visible_related_object`; and the non-delete ops constant plus its single-sited reject
  message landed in a net-new `mutations/operations.py`, not in `mutations/sets.py` or the
  hypothesised `mutations/bind_helpers.py`, which does not exist. The module list also
  omitted two shipped modules, `rest_framework/__init__.py` (the `require_drf()` guard) and
  `rest_framework/hook_context.py` (the frozen hook surface). All four are corrected in
  place. The lesson worth keeping: a promotion target written before the promotion is a
  **prediction**, and eight further spec sites cited the predicted private name — a
  vocabulary `scripts/check_citations.py` cannot see, because it reads `.py` and `KANBAN.md`
  only.

## Decision 5 — Public surface: `SerializerMutation` exported from the root, the `038`-generalized factory reused

Spec: [Decision 5 — Public surface: `SerializerMutation` exported from the root, the `038`-generalized factory reused][spec-039-d5].

### Justification (moved from the spec)

keeping the public surface at one symbol (the base) — reusing the field
factory + error type rather than a parallel factory — honors the one-shared-contract
promise and lets the `038` generalization pay off exactly as designed. The base + the
seam set are the irreducible new surface.

### Alternatives considered (and rejected)

- **A net-new `DjangoSerializerMutationField` factory.** Rejected: the `038`-generalized
  [`DjangoMutationField`][glossary-djangomutationfield] already exposes any
  mutation-family member; a parallel factory would duplicate the dispatch + ref logic
  for no gain (it was the explicit `038` fallback, not needed because the generalization
  shipped).
- **Exporting from a `django_strawberry_framework.rest_framework` namespace only.**
  Rejected: the symbol is used inside schema modules alongside root-exported
  [`DjangoMutation`][glossary-djangomutation] / [`DjangoModelFormMutation`][glossary-djangomodelformmutation],
  so it belongs at the root next to its sibling flavor bases (the `036` / `038`
  precedent) — guarded so the root import survives DRF's absence
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)).

### Changes this Decision underwent

- **Revision 1** pinned the one-symbol public surface reusing the `038`-generalized
  factory — the three model-hardwired axes are **verified**, not re-generalized, which
  is the dividend the `038` forward-intent bought.
- **Revision 8 (F1)** removed `SerializerMutation` from `__all__` while DRF is soft: a
  star import consults `__all__` and binds every listed name through `__getattr__`, so a
  DRF-guarded lazy name would make `from django_strawberry_framework import *` raise for
  a DRF-absent consumer who never writes a serializer mutation. It stays a **named**
  lazy export, with a star-import soft-dep test.
- **Post-ship (`039` residual reconciliation, 2026-09-05).** The Decision opened "One
  net-new public symbol", and the Slice-2 checklist and `## Definition of done` item 8
  repeated it. `__init__.py::_DRF_SOFT_EXPORTS` carries **seven** lazy names, and six of
  them are specified elsewhere in this same spec — `register_serializer_field_converter` and
  `SerializerFieldConversion`, `describe_serializer_input`, `NestedSerializerConfig`, and
  `SerializerHookContext` / `UploadMetadata` (the hook contract). Nothing was
  under-specified; Decision 5 was simply never reconciled to the sections that grew the
  surface. The *contract* it states — lazy through the root `__getattr__`, guarded by
  `require_drf()`, deliberately out of `__all__` — held for all seven throughout and
  survives the edit verbatim; only the count changed. Rejected while reconciling: scoping
  Decision 5 to `SerializerMutation` and pointing at the improvement items for the rest. It
  loses the one property a public-surface Decision exists to give a reader — a single place
  that answers "what does this card export?".

## Decision 6 — Base-class strategy: `SerializerMutation` rides the `DjangoMutation` base, `ModelSerializer`-driven

Spec: [Decision 6 — Base-class strategy: `SerializerMutation` rides the `DjangoMutation` base, `ModelSerializer`-driven][spec-039-d6].

### Justification (moved from the spec)

this is the exact shape [`DjangoModelFormMutation`][glossary-djangomodelformmutation]
proved in `038`, and the [`_resolve_model`][spec-036] seam was frozen in `036`
"for the `0.0.13` serializer flavor (`Meta.serializer_class.Meta.model`)". Riding the
base maximizes reuse (permission, locate, re-fetch, payload, bind all come free) and
keeps the serializer flavor uniform with the form flavor. A **dedicated
[`SerializerMutation`][glossary-serializermutation] base** (rather than teaching
[`DjangoMutation`][glossary-djangomutation] itself to detect `serializer_class` — the
shape [`GOAL.md`][goal]'s crit-6 example literally shows) also buys the strongest
**crit-7 migration ergonomics**: a `graphene-django` serializer-mutation consumer
already writes `class FooMutation(SerializerMutation): ...`, so exporting a
`SerializerMutation` base lets that declaration carry over **by name** — only the import
line changes ([`GOAL.md`][goal] crit 7), strictly better than GOAL's literal
`DjangoMutation` shape. GOAL.md's crit-6 example currently depicts the `DjangoMutation`
base; Slice 4 reconciles it to this shipped base so the north star stops advertising a
declaration that will not dispatch.

### Alternatives considered (and rejected)

- **`DjangoMutation` itself detects `Meta.serializer_class`** (no dedicated
  `SerializerMutation` base — the literal shape [`GOAL.md`][goal]'s crit-6 example shows,
  `class CreateCategoryFromSerializer(DjangoMutation): class Meta: serializer_class = …`).
  Rejected: it forfeits the by-name `graphene-django` migration carry-over above (a
  migrant's `class FooMutation(SerializerMutation)` would have to be rewritten to
  `(DjangoMutation)`), and folds serializer-specific `Meta` validation / `build_input`
  branching into the model-driven base's hot path instead of isolating it in a subclass.
  The base is reused **by subclassing**, not by overloading one class with both flavors.
  Slice 4 updates GOAL.md's example to the `SerializerMutation` base.
- **A standalone `SerializerMutation` not subclassing `DjangoMutation`** (its own
  metaclass + registry + bind, the model-less [`DjangoFormMutation`][glossary-djangoformmutation]
  shape). Rejected for the `ModelSerializer`-driven contract: it would re-implement the
  permission / locate / re-fetch / payload the base already provides; the model-less
  sibling shape is reserved for the deferred plain-`Serializer` flavor.
- **Supporting both `ModelSerializer` and plain `Serializer` in `0.0.13`** (graphene's
  single `SerializerMutation` handles both via `model_class=None`). Rejected: it
  doubles the surface (two payload shapes, two bind paths) for a rare case; the
  `ModelSerializer` flavor is the headline and the `038` form card already
  established the two-flavor split lands across cards, not within one.

### Changes this Decision underwent

- **Revision 1** pinned the base-class strategy — `SerializerMutation` rides the
  [`DjangoMutation`][glossary-djangomutation] base via the [`_resolve_model`][spec-036]
  seam, `ModelSerializer`-driven.
- **Revision 2** moved the serializer-input ledger clear into the
  [`finalize_django_types`][glossary-finalize_django_types] pre-bind reset block, not
  only `TypeRegistry.clear()`, for retry-idempotence.
- **Revision 5** pinned that clear **import-guarded**: `rest_framework/inputs.py` sits
  behind the DRF soft-import guard while the mutation / form clears are direct
  unconditional imports, and the finalizer runs on **every** DRF-absent schema build, so
  a literal mirror would `ImportError` and break schema construction for every
  DRF-absent consumer.
- **Revision 6** weighed the GOAL-literal "`DjangoMutation` detects `serializer_class`"
  alternative and justified the dedicated base on by-name `graphene-django` migration
  parity (crit 7). That alternative is the first entry under `### Alternatives
  considered (and rejected)` above.
- **Revision 7** pinned the cross-flavor reuse obligations onto this base's
  `_validate_meta` / `build_input` overrides so they could not become a third
  byte-parallel copy of the form cluster.
- **Revision 9 (M4)** made `register_subsystem_clear` a **mandatory** Slice 2
  requirement rather than a budget-dependent fallback, removing the two-hand-edit
  option.
- **Post-ship (`039` residual reconciliation, 2026-09-05).** Three corrections.
  **(a) The `register_subsystem_clear` row shape inverted.** The spec specified static
  `(module_path, attr)` STRING rows resolved lazily by `_clear_if_importable`, in four
  places (the Slice-2 sub-block, this Decision's cross-flavor paragraph,
  `## Definition of done` item 3, and the subsystem-clear-registration-seam table cell).
  Commit `48f9f65d`
  (2026-07-11, "Refactor subsystem clear registration and handling") replaced them with a
  zero-argument callable plus a keyword `owner`, and now **rejects** a string
  (`TypeError`, pinned by `tests/test_registry.py::test_register_subsystem_clear_rejects_string_references`).
  The reason it changed is the reason the callable form is better: a string row lets a
  rename fail *silently*, leaving state uncleared, where importing the owner to register
  makes the same rename fail loudly at import. The soft-dependency property the spec
  attributed to lazy string resolution is preserved by a different mechanism — only an
  imported owner can register, so a DRF-absent build registers nothing — which is why the
  outcome the four sites promised still holds while the mechanism they named does not.
  **(b) The allowed-key set grew.** `_ALLOWED_SERIALIZER_META_KEYS` is
  `MODEL_BACKED_WRITE_META_KEYS` (which itself gained `select_for_update`) plus
  `serializer_class` / `optional_fields` / `injected_fields` / `nested_fields`.
  **(c) The "only genuinely-new `_validate_meta` logic" sentence understated the shipped
  validator by six checks** and appeared twice, near-identically, in this Decision and the
  Slice-2 `**DRY / reuse**` sub-bullet. Both now enumerate the shipped set. The pattern is
  worth naming: a sentence of the form "the only new X is Y" is falsified by every later
  card that adds an X, and nothing in the process re-reads it.

## Decision 7 — Serializer-field → Strawberry input mapping: the serializer is the input source of truth

Spec: [Decision 7 — Serializer-field → Strawberry input mapping: the serializer is the input source of truth][spec-039-d7].

### Justification (moved from the spec)

deriving the input from the serializer's fields is the card's headline
parity item and the only way a serializer's declared / renamed / extra fields reach the
write surface; reusing the read-side converters keeps the symmetric wire contract; the
fail-loud converter matches the package's own [`forms/converter.py`][forms-converter]
posture; the shape-identity + materialize-before-`Schema` discipline is the proven
set-family lifecycle.

### Alternatives considered (and rejected)

- **Reuse the `036` model-column generator** (derive the input from `Meta.model`, not
  the serializer). Rejected: a serializer may declare fields a model lacks, rename
  fields, mark columns read-only, or narrow — the input must be the serializer's
  contract, exactly the `038` form-derived precedent.
- **graphene's `singledispatch` + `Field → String` catch-all.** Rejected: the
  catch-all shadows the raise so an unmapped field silently becomes `String`; the
  fail-loud MRO walk is the package's settled discipline.
- **Build a serializer-derived output type** (`is_input=False`). Rejected: the frozen
  uniform `node` / `result` slot is the one cross-flavor output contract; a
  serializer-derived output would fork it.

### Changes this Decision underwent

- **Revision 1** pinned the serializer-derived input mapping with a fail-loud converter
  dispatch.
- **Revision 2** routed schema-time field discovery through an overridable
  `get_serializer_for_schema()` hook rather than a bare no-arg `serializer_class()`,
  rejecting a request-dependent schema shape loudly; designed renamed serializer fields
  (`source`), the GraphQL-name-from-field-name rule, and the reverse map that preserves
  the declared name; and rejected `Meta.optional_fields = "__all__"` as a bare string.
- **Revision 3** replaced the name-only `(class, op, names)` identity with the
  **`SerializerInputShape` descriptor**, added the create-required narrowing guard, and
  added the id-like-suffix rule so a relation field already named `*_id` / `*_pk` is not
  double-suffixed.
- **Revision 5** moved the loud-rejection guard onto **`.fields` materialization**
  rather than `serializer_class()` construction (DRF builds `.fields` lazily, so a
  context-requiring serializer fails at attribute access, not construction); pinned the
  carried `is_input` parameter **accepted-and-ignored with no branch** so it adds no
  uncovered line under `fail_under = 100`; scoped `ListField` to scalar children; and
  separated the mutation's `Meta.fields` (input surface) from the serializer's own
  (validation).
- **Revision 6** pinned the fail-loud relation / file mapping as **mandated by
  [`GOAL.md`][goal]'s "don't silently weaken rich relations" non-goal**, not a stylistic
  preference.
- **Revision 7** single-sited the converter dispatch skeleton and the per-field record
  so the serializer flavor imports them rather than forking a third copy.
- **Revision 8 (F3 / F4)** pinned **one** strategy-dependent generated relation
  annotation (Relay → `GlobalID`, else raw-pk scalar) — "accepts both" is the shared
  decode helper's contract, not the emitted shape — and supported serializer-only
  relation fields through `field.queryset.model`, the previously-undefined
  write-only-`PrimaryKeyRelatedField` case.
- **Revision 9 (M1 / M2 / M3)** stated the one generated relation shape in the Slice-3
  and definition-of-done summaries, added the **Nullability and defaults** paragraph,
  and made a relation target with no registered primary
  [`DjangoType`][glossary-djangotype] a class-creation
  [`ConfigurationError`][glossary-configurationerror] rather than a default-manager
  fallback.
- **Post-ship (`039` residual reconciliation, 2026-09-05).** Six corrections, of which the
  first is the one a reader would have acted on and been wrong.
  **(a) Nullability.** The Decision said annotation nullability follows `field.allow_null`
  alone and is "independent of requiredness". At `HEAD` the annotation is nullable when the
  field is `allow_null=True` **or** optional, with a `strawberry.UNSET` default. The shipped
  rule is the correct one and the spec sentence could not be made true without contradicting
  the bullet two lines below it, which forbids fabricating a GraphQL default: a GraphQL
  input field that is neither nullable nor defaulted **is required**, so an omittable
  non-null field would be un-satisfiable. Implementing the old sentence would have emitted
  exactly that.
  **(b) Converter dispatch.** The precheck table is longer and stricter than "matched first
  by `isinstance`": the nested-serializer reject runs first, and the single-relation
  precheck matches the broad `serializers.RelatedField` and then rejects any
  non-`PrimaryKeyRelatedField`. That rejection is a real, tested contract the spec stated
  nowhere, and a DRF migrant would reasonably have expected a `SlugRelatedField` to work.
  **(c) Relation cardinality.** `_reject_relation_cardinality_mismatch` and the re-derivation
  of `kind` from the serializer field's cardinality were unspecified. The invariant they
  serve — the generated input must describe the same shape the runtime serializer validates
  — is now stated.
  **(d) The reverse map** is nine axes and six kinds (`utils/inputs.py::InputFieldSpec`),
  not the `input_attr → (serializer_field_name, source, kind)` triple with four kinds the
  Decision and the Slice-1 checklist both described. `nested_specs` is what lets the
  resolver's reverse map recurse at every depth.
  **(e) Descriptor identity** omitted `descriptions` (an independent axis) and
  mis-stated the annotation axis, which is the **post-widening** repr — the axis that makes
  an `allow_null` pair diverge instead of collapsing onto one shape. The spec was describing
  a weaker identity than shipped, and both omissions are pinned by their own tests.
  **(f) Canonical naming.** The canonical `<Serializer>Input` is granted only when the
  shape's identity equals the identity default no-arg discovery produces
  (`_default_full_shape_identity`), not whenever a shape looks full; the spec's looser
  definition licensed a collision at materialize for a hook-returned "full" shape.
  Also folded in here from the deleted post-ship hardening blockquote: the writable-`source`
  uniqueness rule spans the whole write surface (inputs **and** `Meta.injected_fields`),
  because DRF resolves a collision last-write-wins and an injected value could otherwise
  silently replace the client's.

## Decision 8 — Resolver pipeline: instantiate → `is_valid()` → `serializer.errors` → `save()` → optimizer re-fetch → payload

Spec: [Decision 8 — Resolver pipeline: instantiate → `is_valid()` → `serializer.errors` → `save()` → optimizer re-fetch → payload][spec-039-d8].

### Justification (moved from the spec)

`serializer.is_valid()` / `serializer.save()` is the DRF-native
validation + write entry; routing `serializer.errors` into the envelope (rather than
raising) is the graphene-django / cross-flavor contract; the relation-visibility decode
is the package security invariant the `036` / `038` mutations enforce; the single
`atomic()` / single `sync_to_async` boundary is the settled async-safety contract.

### Alternatives considered (and rejected)

- **Skip `is_valid()` and rely on the model's `full_clean()`.** Rejected: it loses the
  serializer's `validate_<field>` / `validate()` logic — the whole point of the
  flavor.
- **Reconstruct the full payload for `update` (the `038` shape).** Rejected: DRF's
  `partial=True` is the native partial-update mechanism and is cleaner than a
  `model_to_dict` overlay; reconstruction is a form-flavor necessity, not a serializer
  one.
- **Pass relation ids straight to the serializer without the visibility decode.**
  Rejected: a `PrimaryKeyRelatedField`'s default queryset is `Model.objects.all()`
  (not request-scoped), so a hidden target would be writable — the package's
  relation-visibility invariant (the `036` / `038` contract) requires the decode-time
  `get_queryset` check.

### Changes this Decision underwent

- **Revision 1** pinned the `serializer.errors` →
  [`FieldError`][glossary-fielderror-envelope] pipeline with the DRF-native
  `partial=True` update.
- **Revision 2** reordered the pipeline to **locate → authorize → decode** so write
  authorization runs before any relation decode, closing a
  relation-visibility-probe-by-id regression against the invariant the `038` form
  pipeline already pinned; replaced the implicit reuse of the one-level `036` mapper
  with a dedicated recursive `serializer.errors` flattener (dotted `items.0.name`,
  `NON_FIELD_ERRORS_KEY` → `"__all__"` at every level); and resolved the runtime
  serializer `context` through the shared `request_from_info` helper.
- **Revision 3** made the save **value-preserving**: the resolver captures
  `serializer.save()`'s returned object inside the `save_or_field_errors` closure
  (called once) and re-fetches by its pk, rather than re-deriving from a return the
  wrapper discards.
- **Revision 5** routed a save-time `ValidationError` — from a custom `create()` /
  `update()` or the model's `full_clean()` — through the flattener into the envelope
  instead of a top-level `GraphQLError`.
- **Revision 8 (F2 / F5 / F7)** split the save-time `ValidationError` by class (DRF's
  `.detail` → the recursive flattener, Django's `error_dict` / `messages` → the flat
  `036` mapper), keyed `FieldError.field` to the **GraphQL input name** through the
  reverse map, and pinned `get_serializer_kwargs` precedence with framework-owned
  `partial=True` and merged request `context`.
- **Revision 9 (H2 / H3)** rewrote the write-time `ValidationError` edge case to split
  by exception class so a Django `ValidationError` no longer went down the DRF `.detail`
  path, and made `context["request"]` **strictly framework-owned** — an override
  supplying a different `request` is a
  [`ConfigurationError`][glossary-configurationerror], and the prior "escape hatch"
  wording was removed so the actor cannot drift from the permission seam.
- **Post-ship (`039` residual reconciliation, 2026-09-05) — the hardening fold.** The spec
  carried a 178-line `> Post-ship hardening revision (2026-07-15)` blockquote at its head
  and a bracketed `**[superseded by …]**` clause inside the Slice-3 checklist. Both are
  gone; **none of their content is.** The blockquote was chronology in framing and the sole
  statement of live contract in substance, so deleting it would have removed the only
  description of the hook surface, the alias guard, the phase separation, the drift
  snapshot, the relation-intent ledger and the post-save attestation, while leaving
  Decisions 7, 8 and 12 asserting the superseded shape. Each bullet was therefore folded
  into the step that owns it, restated in the present tense as the rule: the alias guard,
  the authorization phase's database-enforced read-only barrier, and the pinned-connection
  phase separation into the Decision's preamble; the post-locate `authorized_pk` /
  `target_state` snapshot into step 1; the constructor-only hook contract, the frozen
  `SerializerHookContext` / `UploadMetadata` view, the reserved-key omission-sentinel +
  identity checks, the `_hook_mapping` boundary, the agreement guards, the runtime
  writable-`source` walk and the relation-queryset scoping into step 4; the relation-intent
  ledger, the validator queryset pinning and the flattener's iterative / cycle-rejecting /
  budget-capped shape into step 5; and the drift check, the M2M snapshot, the write witness,
  the relation attestation and `_checked_saved_result` into step 6.

  **What the hardening changed, and why.** A security audit of the shipped pipeline found
  that leaving hooks in ownership of `data` and `instance` preserved an authorization
  bypass: a hook holding the live located instance could mutate the row that had just been
  authorized, and DRF's `update()` saves the whole instance. The break was intentional and
  pre-`1.0`, with no compatibility shim. Three design choices inside it are worth recording
  because each had a plausible weaker alternative that was rejected:
  - **Reserved returns are checked by omission sentinel + object identity, never deep
    equality.** A deep `!=` recurses on deep valid payloads, and a `pop(..., None)` default
    conflates an explicit `None` with omission. So a returned `data` must be omitted or the
    exact frozen object, and **any** returned `instance` key is refused outright.
  - **The alias guard performs no read/write classification.** A lexical keyword test is
    bypassable — leading SQL comments, PostgreSQL `EXPLAIN ANALYZE UPDATE`, write-capable
    functions invoked through `SELECT` — so the guard rejects every statement on a
    non-pinned connection before it executes, and the authorization phase's exception is
    made safe by a **database-enforced** read-only transaction rather than by inspecting
    SQL. Post-hoc detection was rejected: it cannot roll back a write that already escaped.
  - **The freeze fails closed on an opaque leaf.** Aliasing a possibly-mutable value a hook
    could reach back through was the alternative, and it reopens the same class of bypass
    the revision exists to close.
- **Post-ship (`039` residual reconciliation, 2026-09-05) — four further corrections.**
  **(a) `run_write_pipeline_sync` is not scoped to model-backed create/update.** The
  Decision's DRY paragraph, the sync-write-pipeline-skeleton table cell, and the Slice-3
  DRY bullet all said so,
  citing **F6**, and all three were false at `HEAD`: the skeleton's own docstring calls it
  "the shared write orchestration every mutation flavor rides", and delete, the model-less
  plain form, and the auth flavor all ride it through a `tail_step` seam and a
  no-primary-type `{ ok: true }` tail. F6 argued that folding delete and the model-less form
  in would make the skeleton a leaky generic framework; a callback seam per variation turned
  out to keep it small while single-siting the security ordering for **every** flavor rather
  than three of them, which is strictly more of what the promotion was for. F6 lost on
  that.
  **(b) The serializer does not call `save_or_field_errors`.** Four spec homes said the write
  was wrapped by that `036` mapper. The serializer reaches the identical envelope through
  the shared `utils/errors.py::integrity_error_field_errors` leaf — the same leaf
  `save_or_field_errors` itself calls — and that deviation is what makes the savepoint
  containment possible, since the wrapper's shape assumes a caller that already holds the
  instance.
  **(c) Error re-keying happens at every depth, not only the root segment.** The spec said
  nested sub-paths keep DRF's structure; `_rekey_segment` over the recursive child maps
  built from `InputFieldSpec.nested_specs` re-keys the whole path. An understatement rather
  than a falsehood, but one that would have taught a reader to accept `shelves.0.alt_branches`
  as correct.
  **(d) Two shipped mechanisms had no home anywhere in the spec** —
  `_assert_runtime_write_source_ownership` (the runtime half of the writable-`source` rule,
  which exists precisely because schema discovery cannot see a context-dependent
  `get_fields()`) and `_pin_validator_querysets` (DRF *shares* validator objects across
  serializer instances, so pinning them per instance closes a concurrency hazard the
  relation-field scoping does not touch). Both now sit in the steps they run in. Two whole
  modules were likewise unnamed: `utils/write_values.py` (the shared decode substrate, zero
  spec mentions) and `utils/errors.py` (the shared leaf-error substrate, zero spec mentions).
  Both are now named in the Decision's preamble and in the import manifest. A shipped
  mechanism the spec never states is a contract with no home, and the only instrument that
  finds one is a cross-check of the code against the spec's five homes.

## Decision 9 — Optimizer composition: the `ModelSerializer` payload re-fetch rides the `spec-036` G2 path

Spec: [Decision 9 — Optimizer composition: the `ModelSerializer` payload re-fetch rides the `spec-036` G2 path][spec-039-d9].

### Justification (moved from the spec)

the re-fetch path is shipped and the G2 gate exists for exactly this;
reusing it gives the serializer flavor optimizer-composed returns for free, identical
to the form flavor.

### Alternatives considered (and rejected)

- **Return `serializer.data` / `serializer.instance` without re-fetching.** Rejected:
  `serializer.instance` after `save()` has no response-selection relations loaded, so a
  relation in the response selection N+1s; the re-fetch is what makes the response
  planable, and `serializer.data` is the serializer's representation, not the
  `DjangoType` the frozen slot returns.

### Changes this Decision underwent

- **Revision 1** pinned the optimizer composition reusing the `036` re-fetch path.
- No later revision reopened it.
- **Post-ship (`039` residual reconciliation, 2026-09-05).** Checked against `HEAD` and
  still true as written: the payload re-fetch rides the `036` `refetch_optimized` path and
  the G2 gate keeps `select_related` / `prefetch_related` while suppressing `.only(...)`.
  What changed is only where the contract is **pinned** — its behavioral half live and its
  plan-object half package-internal, since the optimizer's stash is introspection state no
  `/graphql/` response carries — and the spec now names both tests instead of implying one
  tier holds the whole row.

## Decision 10 — Operations: `create` / `update`, no serializer `delete`

Spec: [Decision 10 — Operations: `create` / `update`, no serializer `delete`][spec-039-d10].

### Justification (moved from the spec)

`create` / `update` are the operations a serializer expresses; `delete`
has no serializer step; one-mutation-per-operation is the package's settled shape (the
`036` / `038` precedent).

### Alternatives considered (and rejected)

- **Adopt graphene's `model_operations` runtime dispatch.** Rejected: it fragments the
  declaration shape away from [`DjangoMutation`][glossary-djangomutation] /
  [`DjangoModelFormMutation`][glossary-djangomodelformmutation] (one mutation per
  operation), and the single-string `Meta.operation` is the more `class Meta`-idiomatic
  selector.
- **Add a serializer `delete`.** Rejected: DRF serializers have no delete pipeline;
  the model-driven `DjangoMutation` `delete` already covers it.

### Changes this Decision underwent

- **Revision 1** pinned the operation set (`create` / `update`, no serializer `delete`).
- **Revision 6** pinned `Meta.operation` **mandatory** — the shipped model-driven base
  already requires an explicit `operation`, so defaulting it for the serializer flavor
  alone would make it the only write flavor that infers the op — and framed the real
  crit-7 friction it leaves a `graphene-django` migrant: one auto-dispatching
  `model_operations = ["create", "update"]` mutation must become two, each carrying a
  key their old code never had.
- **Revision 7** promoted the `{create, update}` set to a single
  `NON_DELETE_WRITE_OPERATIONS` constant both the form and serializer `_validate_meta`
  overrides import, so the rule and the "no serializer/form delete" message single-site.
- **Post-ship (`039` residual reconciliation, 2026-09-05).** The non-delete operation
  set's promotion landed in
  a net-new `mutations/operations.py`, not in `mutations/sets.py`: the constant
  `NON_DELETE_WRITE_OPERATIONS`, the `NON_DELETE_OPERATION_INPUT_KIND` map, and the
  single-sited `non_delete_operation_error` message live there and reach both flavors
  through `mutations/sets.py::require_non_delete_operation`. That module did not exist when
  the spec was written. The DRY intent — one set, one message, no
  `_VALID_SERIALIZER_OPERATIONS` — is intact; only the address moved. The Decision and the
  non-delete-operation-set table cell both named the old one, and the form flavor's private
  `_VALID_FORM_OPERATIONS`, cited as the byte-identical precedent, no longer exists.

## Decision 11 — Write authorization: reuse the `036` seam (`DjangoModelPermission` for the `ModelSerializer`)

Spec: [Decision 11 — Write authorization: reuse the `036` seam (`DjangoModelPermission` for the `ModelSerializer`)][spec-039-d11].

### Justification (moved from the spec)

the seam was frozen in `036` and proven reusable in `038`; the
`ModelSerializer`'s model resolves the default perm for free through the
`_resolve_model` override, so the serializer flavor is safe-by-default with no new
permission machinery.

### Alternatives considered (and rejected)

- **Use DRF's own `permission_classes` / `DEFAULT_PERMISSION_CLASSES`.** Rejected: the
  package's write-auth is a first-class, `class Meta`-driven contract shared across
  flavors; threading DRF's request-level permissions through a GraphQL mutation would
  fork the contract and couple write-auth to DRF's view machinery (which is absent — a
  serializer is used here without a DRF view).

### Changes this Decision underwent

- **Revision 1** pinned permission reuse —
  [`DjangoModelPermission`][glossary-djangomodelpermission] resolves for free through
  the `_resolve_model` override, so the flavor is safe-by-default with no new permission
  machinery.
- **Revision 2** kept `permission_classes` explicitly in the serializer allowed-key set.
- **Post-ship (`039` residual reconciliation, 2026-09-05).** Checked against `HEAD` and
  still true as written. The `036` write-auth seam is inherited unchanged and
  `check_permission` remains the escape hatch. The hardening revision wrapped the
  permission call in a phase-scoped authorization exception to the pipeline alias guard
  (Decision 8), which constrains *where* the permission backend may read, not *what* this
  Decision authorizes.

## Decision 12 — Soft `djangorestframework` dependency and the 100%-coverage strategy

Spec: [Decision 12 — Soft `djangorestframework` dependency and the 100%-coverage strategy][spec-039-d12].

### Justification (moved from the spec)

this is the established pattern for a soft dependency under a 100%-coverage
gate — out of runtime deps, in the dev group, the absent path simulated. It mirrors
[`spec-037`][spec-037]'s `pillow` handling exactly, and graphene-django's own optional
`rest_framework` dependency.

### Alternatives considered (and rejected)

- **Add DRF to `[project].dependencies`.** Rejected: it forces every consumer to
  install DRF even if they never write a serializer mutation, exactly the soft-dep the
  card mandates against ("package import must succeed without DRF installed").
- **`# pragma: no cover` the whole `rest_framework/` subpackage.** Rejected: it would
  ship untested write-side code; the dev-group dependency lets the suite cover it for
  real, which is the point of the 100% gate.
- **Skip the absent-path test.** Rejected: the guard's raise is a reachable line under
  the 100% gate; simulated absence covers it.

### Changes this Decision underwent

- **Revision 1** pinned the **soft `djangorestframework` dependency + the 100%-coverage
  strategy**: DRF out of runtime deps, added to the dev group, the absent path covered
  by simulated absence.
- **Revision 2** pinned the soft-DRF root export to a root `__getattr__` plus a shared
  `require_drf()`, with the exact behavior of all four import forms and a cache-eviction
  rule for the absent-path test.
- **Revision 3** pinned the root `__getattr__` to **not memoize** `SerializerMutation`,
  with the absent-DRF test also evicting the root attribute — otherwise an earlier
  import in the same process leaves the symbol bound and masks the missing-dependency
  path.
- **Revision 5** turned the DRF version floor from an open question into a concrete
  pre-Slice-1 check **gated by the CI matrix under `-W error`**, naming DRF's
  Django-support lag rather than `NON_FIELD_ERRORS_KEY` availability as the binding
  constraint.
- **Revision 8 (F1 / F11)** kept `SerializerMutation` out of `__all__` while DRF is
  soft, and moved the DRF dev-dependency wiring plus the floor probe into a
  **pre-Slice-1 gate (Slice 0)**, since Slices 1-3 import DRF in tests.
- **Revision 9** added the Slice 0 floor **acceptance artifact** — a probe script or a
  documented sequence of explicit `uv` commands — and the three-places-must-agree rule
  for the recorded floor.
- The floor's **value** is a contract rather than deliberation, so the recorded-floor
  statement was held back into this Decision's body when the
  [Risks and open questions](#risks-and-open-questions) body moved here — it is the one
  measured record the move refused to take. See
  [Provenance of this record](#provenance-of-this-record).

Carried inline in the `__all__` paragraph and moved from there verbatim:

This reverses the earlier draft's "stays in `__all__`"
choice, which assumed a `0.0.14` `channels` / `debug_toolbar` hard-dep posture that does
not hold while DRF is soft.
- **Post-ship (`039` residual reconciliation, 2026-09-05).** Item 3 prescribed
  **monkeypatching `builtins.__import__`** to simulate DRF's absence, and the
  `## Test plan`'s DRF-absent bullet repeated it. That patch does not work here, and its
  failure mode is the dangerous one: the guards call `importlib.import_module`, which
  consults `sys.modules` directly and never calls `__import__`, so the patch leaves the
  guard unreached and the test passes **without exercising anything**. `START.md`
  ("Soft-dep absence") bans it outright for that reason. The shipped harness uses the
  importlib-native `sys.modules[name] = None` sentinel through the shared
  `tests/_soft_dependency.py::simulated_absence`, and runs the root-import half in a fresh
  subprocess, which is strictly stronger than an in-process re-import: it can catch a
  newly-introduced eager import at the package root, which a warm process cannot. Left as
  written, this row would have taught the next author to write a test that cannot fail —
  the reason it is corrected rather than merely annotated. Everything else in item 3 (the
  three raising entry points, the two-cache eviction, the root-attribute deletion, the
  non-memoization requirement) was accurate and is unchanged.

## Decision 13 — Live coverage: products grows a `ModelSerializer` mutation

Spec: [Decision 13 — Live coverage: products grows a `ModelSerializer` mutation][spec-039-d13].

### Justification (moved from the spec)

the card DoD mandates "live HTTP coverage … exercising a
`ModelSerializer` mutation", and the test-query README makes live the **first** home for
any reachable line — so the resolver and its live surface are one deliverable, not two
slices. Products is the established write-surface example (the `036` / `038` precedent),
already carries the `unique_item_per_category` constraint, the seeded fixtures, and the
[`Item.attachment`][products-models] `FileField` the `Upload` path needs. DRF being a
dev-group dependency
([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy))
keeps it present in the test context.

### Alternatives considered (and rejected)

- **Keep the resolver and the products live surface as separate commits** (the prior
  draft split them across two slices). Rejected: it violates the
  [`test_query/README.md`][test-query-readme] #"Coverage rule." — at the resolver
  commit, the resolver's reachable lines would be earned by `tests/rest_framework/`
  package tests, then duplicated by live tests in the next slice. Merging them into
  Slice 3 is the reviewer-pinned fix; the resolver's reachable behavior is earned live,
  once.
- **A dedicated `test_serializer_api.py` against a fresh app.** Rejected: products
  already carries the `unique_item_per_category` constraint and the seeded fixtures;
  extending `test_products_api.py` matches the `036` / `038` precedent (a dedicated
  file remains an acceptable alternative if the products suite grows unwieldy).
- **Reuse the `library` app.** Rejected: products is the canonical write-surface
  example and already hosts the model-driven and form mutations.

### Changes this Decision underwent

- **Revision 1** pinned the products live serializer surface.
- **Revision 4** collapsed the five-slice plan to **four**, landing the serializer
  resolver pipeline and the products live surface in **one** slice so every
  consumer-reachable resolver line is earned by a real `/graphql/` request at the commit
  it appears; [`test_products_api.py`][test-products-api] became the primary harness and
  [`tests/rest_framework/test_resolvers.py`][test-rest-framework] was narrowed to the
  residue a live query cannot drive.
- **Revision 8 (F9)** made the live request-context proof an explicit `validate()`
  rather than a `HiddenField`, which is subtle under `partial=True`.
- **Post-ship (`039` residual reconciliation, 2026-09-05).** Checked against `HEAD` and
  still true as written: products carries `serializers.py` with an `ItemSerializer` and its
  live surface in [`test_products_api.py`][test-products-api]. One clarification landed in
  the `## Test plan` rather than here — "live" is the one aggregate `/graphql/` schema, not
  one file, and the fixtures those improvement items need (a non-Relay target, a raw-pk M2M, a
  nested write, a schema-hook serializer) live in the library app, so those rows and both
  golden-SDL snapshots sit in `test_query/test_library_api.py`. Same tier, same transport,
  different app; the spec was silent rather than wrong.

## Decision 14 — Version bumps are owned by the joint `0.0.13` cut

Spec: [Decision 14 — Version bumps are owned by the joint `0.0.13` cut][spec-039-d14].

### Justification (moved from the spec)

per [`docs/SPECS/NEXT.md`][next] Step 3 / Step 6, when multiple cards
target one patch version the bump belongs to the joint cut, not any individual card's
spec. `039` and `040` both target `0.0.13`.

### Alternatives considered (and rejected)

- **Bump to `0.0.13` in this card's Slice 4.** Rejected: `040` also ships into
  `0.0.13`; a per-card bump races the joint cut and would have to be reconciled when
  the sibling lands.

### Changes this Decision underwent

- **Revision 1** pinned **the joint `0.0.13` cut owning the version bump**.
- **Revision 2** reconciled `uv.lock` as **updated** — the DRF dev-group add changes its
  dependency graph — while the package's own version entry stays `0.0.12`.
- **Revision 8 (F8)** split Slice 4's **implemented-on-main** docs from the **release**
  docs, deferring the latter to the joint cut.
- **Revision 9 (H1)** normalized the Slice 0 / Slice 4 wording across the Status block,
  Goals item 8 and this Decision: the soft-dep wiring and `uv.lock` regen belong to the
  **Slice 0 gate**, and Slice 4 is docs + card-wrap only.
- **Revision 10** recorded the Slice 4 final-verification reconciliation — all five
  slices final-accepted, no version bump and no `CHANGELOG.md` / `README.md` Status /
  [`docs/README.md`][docs-readme] edit, each confirmed absent from the build diff.

Carried inline in the `uv.lock` paragraph and moved from there verbatim:

(An earlier draft lumped
`uv.lock` with the version files, which contradicted the dev-group add; this reconciliation
resolves it.)
- **Post-ship (`039` residual reconciliation, 2026-09-05).** Two present-tense claims about
  this card's version discipline had become claims about today's tree, which reads
  `0.0.15`: `## Goals` item 8's "these stay `0.0.12` until the joint cut" and
  `## Out of scope`'s "The `0.0.13` version bump". Both **held as predictions** — the card
  bumped nothing and the joint cut performed the bump in `fa704722` — so both are re-tensed
  to card-scoped statements rather than rewritten or deleted. `docs/builder/BUILD.md`
  `### '## Current state': observations stand, predictions do not` is the rule; the wrinkle
  it does not cover is a prediction that **held** but whose present tense now points at the
  wrong subject.

## Risks and open questions

The spec's whole `## Risks and open questions` body. Eight of its nine items pair a
preferred answer for the `0.0.13` cut with a fallback if implementation proved the
preferred answer wrong; the ninth is a card-citation tension the cut chose to record
rather than silently reconcile. Both shapes are a build-time deliberation instrument, not
a contract, so the body moved and the spec keeps the heading and a pointer here. **One
record did not move**: the DRF floor item's `Recorded floor (Slice 0, verified): …`
statement is a measured normative record with no other home in the spec, so it was held
back into
[Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)
and is reproduced below only as part of the item it sat in. Every other rule any item
states is also stated by the Decision that answered it or by the spec's
`## Edge cases and constraints`.

Each item names a preferred answer for the `0.0.13` cut and a fallback if
implementation reveals it is wrong.

- **The `## In progress` KANBAN column is empty as this spec is authored.** The
  [`docs/SPECS/NEXT.md`][next] flow targets "the next-up Work-In-Progress card", but no
  card is in the `wip` status (the column renders empty; `git`-verified against the
  `apps.kanban` DB). Preferred reading: `039` is the **lowest-NNN card in the active
  To-Do / Alpha column** and the natural next-up spec target (the latest `DONE` card is
  `038-0.0.12`; `039` is the next NNN). The card's status was **not** moved to `wip`
  (the [`docs/SPECS/NEXT.md`][next] boundary forbids non-spec DB edits). Fallback: if
  the maintainer intended a different next card, re-author against it — but `039` is the
  unambiguous lowest-NNN active card.
- **Model-less plain `Serializer` flavor — deferred (preferred), not RESOLVED.**
  Preferred answer ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven)):
  `0.0.13` ships the `ModelSerializer`-driven contract only (a resolvable model, the
  uniform `node` / `result` slot); a plain model-less `serializers.Serializer` is out of
  scope (it has no object slot and `DjangoMutation`'s base requires a resolvable model).
  Fallback: add a model-less sibling later in the [`DjangoFormMutation`][glossary-djangoformmutation]
  shape (its own metaclass + `{ ok, errors }` payload + `bind_serializer_mutations()`),
  if a consumer needs a serializer-validated non-model write — never weaken the
  `ModelSerializer` contract.
- **Card key `Meta.model_operations` vs the package's `Meta.operation` — the real
  crit-7 friction point.** The card lists `Meta.model_operations` (graphene's
  runtime-dispatched list); the package uses per-operation `Meta.operation`
  ([Decision 10](#decision-10--operations-create--update-no-serializer-delete)).
  Preferred reading: honor `Meta.operation` (uniform with
  [`DjangoMutation`][glossary-djangomutation] / [`DjangoModelFormMutation`][glossary-djangomodelformmutation]
  — both of which already **require** an explicit `operation`, so the serializer flavor
  cannot quietly default it without becoming the odd one out). This is where the
  `graphene-django` serializer-mutation migrant feels crit-7 most: their one
  auto-dispatching `model_operations = ["create", "update"]` mutation must become **two**
  package mutations, each with an `operation` key their old code never had — a
  declaration-shape change, not "only the import line changes." The base-class swap
  ([Decision 6](#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven))
  carries over by name; this key does not. The **near-term affordance** (preferred over
  leaving the migrant to hand-split) is to accept `Meta.model_operations` as an alias
  that **expands to the per-operation mutations** under the hood — a contained
  metaclass-time desugaring that keeps the package's one-mutation-per-op internals while
  letting the graphene key migrate verbatim; sequence it right after `0.0.13` if the
  migration friction proves real. Recorded per the [`docs/SPECS/NEXT.md`][next] "prefer
  the card, surface the conflict" rule.
- **Card key `Meta.lookup_field` vs the `id:`-decode locate.** The card lists
  `Meta.lookup_field` (graphene's non-pk update locate via `get_object_or_404`); the
  package locates an `update` row by decoding the `id:` `GlobalID` server-side and
  running it through the target `get_queryset`
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)).
  Preferred reading: keep the `id:`-decode locate (the package's no-existence-leak
  contract, uniform with `036` / `038`); the fallback is a future `Meta.lookup_field`
  for a non-pk locate (a contained resolver change). Recorded, not silently reconciled.
- **Card phrase "dual-purposed for inputs and outputs" vs the frozen `node` / `result`
  slot.** The card DoD names the converter "dual-purposed for inputs and outputs
  (mirroring graphene's `is_input=True` flag)"; the `036`-frozen uniform `node` /
  `result` slot is the package's one cross-flavor output contract
  ([Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)).
  Preferred reading: the converter is **input-directed**; the mutation output is the
  primary [`DjangoType`][glossary-djangotype] in the frozen slot, not a
  serializer-derived output type (the same way `038` superseded `Meta.return_field_name`).
  The `is_input` parameter is carried for graphene parity / forward use but is
  **accepted-and-ignored — no `if not is_input:` branch**, so it adds no uncovered line
  under `fail_under = 100`. Fallback: if a consumer needs a serializer-shaped output, that
  is a separate (post-`1.0.0`) surface, not this card.
- **DRF version floor — a concrete pre-Slice-1 check, gated by the CI matrix under
  `-W error`.** This is the biggest practical risk and the **binding** constraint is
  *not* serializer-API availability — it is that the dev-group DRF must **import and run
  warning-free across the entire CI matrix**. [`pyproject.toml`][pyproject] declares
  `requires-python = ">=3.10,<4.0"` with Django 5.2 / 6.0 classifiers, the
  [`django.yml`][django-workflow] matrix runs **Django 5.2.0 → 5.2.\* → 6.0.\* →
  `latest` on Python 3.10 → 3.14**, and [`pytest.ini`][pytest-ini] sets
  `filterwarnings = error`. So **any** `DeprecationWarning` / `RemovedInDjango*Warning`
  DRF emits under Django 6.0 / `latest` or Python 3.14 becomes a hard
  collection / test failure — exactly the failure mode the `forms.URLField()`
  `assume_scheme` deprecation just produced (a third-party-adjacent deprecation turned
  fatal by `-W error`). DRF's Django-version support also **lags** Django releases, so a
  DRF release that officially supports Django 6.0 / Python 3.14 may not yet exist; if it
  does not, the Django-6.0 / `latest` matrix nodes fail at `uv sync` / import time.
  Preferred answer
  ([Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)):
  **this is a pre-Slice-1 dependency gate (Slice 0), not a Slice 4 surprise (F11)** —
  because Slice 1–3 tests import DRF, the dev-dep add + `uv.lock` regen + any `ignore::`
  line and the verified floor must all land in the gate *before* converter code. In that
  gate, verify a `djangorestframework` release exists that imports and runs **warning-free
  on (Python 3.14, Django 6.0 / `latest`)** as well as the floor (`Python>=3.10`,
  `Django>=5.2`); record the **exact** floor pinned in the dev group (and matched in the
  guard's install hint), plus **any DRF-origin `ignore::` line** that release still needs —
  [`pytest.ini`][pytest-ini]'s own comment already sanctions a targeted `ignore::` for
  "warnings originating in third-party packages we cannot fix" (never a blanket ignore).
  Secondary (API-availability) constraint: bump the floor if a needed serializer API (e.g.
  `api_settings.NON_FIELD_ERRORS_KEY`) is only present in a later release. The probe runs
  against the actually-installed DRF in the gate; the matrix-warning check is the one that
  gates the floor, and if no compatible release exists the card blocks at the gate rather
  than mid-Slice-1.
  The **recorded floor** this gate produced is a measured normative record rather than
  deliberation, so it was held back into
  [Decision 12](#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy)
  and lives in the spec, not here.
- **`serializer.save()` create-vs-update + M2M.** Preferred answer
  ([Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)):
  `serializer.save()` runs `create()` (no instance) / `update()` (with instance)
  internally and assigns M2M within that call, all inside the one
  `transaction.atomic()` — no separate M2M step (the DRF idiom). Fallback: an explicit
  `perform_save` hook only if a consumer serializer needs the saved instance before its
  M2M rows — a contained resolver change, not a contract change.
- **`rest_framework` in the example's `INSTALLED_APPS`.** Preferred answer
  ([Decision 13](#decision-13--live-coverage-products-grows-a-modelserializer-mutation)):
  add `"rest_framework"` to the fakeshop `INSTALLED_APPS` only if a flat
  `ModelSerializer` needs the app registry (most do not — DRF serializers validate /
  save without the app installed). Fallback: add it unconditionally if a serializer
  feature (browsable-API-only machinery) is reached; settled during implementation.
- **Card-citation note — the spec filename vs the card's
  `docs/spec-serializer_mutations.md`.** The card DoD names
  `docs/spec-serializer_mutations.md`; the structured convention authors at
  `docs/spec-039-serializer_mutations-0_0_13.md`
  ([Decision 1](#decision-1--spec-filename-and-canonical-naming)). Recorded, not
  silently reconciled, per the [`docs/SPECS/NEXT.md`][next] boundary rule.

## Improvements over graphene-django's DRF integration

The preamble the spec's improvement section used to carry, **quoted verbatim below**. Only
the preamble moved: the seventeen improvement subsections each state a shipped contract and
stayed in the spec. What the preamble adds beyond the spec's replacement text is provenance
— that the set came from a review pass rather than the original draft, that sixteen items
were proposed together and a seventeenth followed on, and that the section is a design
record. The count is seventeen either way; the spec now says so without narrating how it
got there. The quotation is reproduced as it stood, round vocabulary and ordinals included,
because a record of deleted text that has been edited is no longer a record of it.

> A review pass (rev6) proposed 16 improvements that make the serializer
> lane stricter, safer, and more diagnosable than graphene-django's DRF integration, plus one
> follow-on (#17 — opt-in nested serializer inputs). They are all in-scope for `0.0.13` (not
> backlog). Each keeps the existing wins (fail-loud unmapped fields, visibility-checked
> relations, authorize-before-decode, framework-owned `context["request"]` / `partial`, recursive
> error flattening, transaction boundary, descriptor-based input identity, DRF-soft-dep root).
> This section records the design of each.

### Post-ship changes to individual improvement items (`039` residual reconciliation, 2026-09-05)

- **Row locking — the lock inverted from opt-in-`False` to opt-out-`True`, and widened to
  all three model-backed flavors.** The item shipped as written and a later concurrency
  hardening (the `0.0.14` line; `mutations/sets.py::validate_select_for_update` and
  `mutations/resolvers.py::locate_instance` both carry the attribution in source) changed
  the default and moved the key into the shared `MODEL_BACKED_WRITE_META_KEYS`. Locked
  writes are the safe posture, so an opt-*out* is the shape that fails safe when a consumer
  says nothing — which is the whole argument, and it is why the title lost the word
  "Optional". Rejected: keeping a per-flavor default. It would have made the same `Meta` key
  mean different things on three bases, and one shared validator exists precisely so the
  key's contract cannot drift.
- **The save-time kwargs hook — the signature changed, its canonical example became a
  rejection, and a second guard arrived.** Shipped signature is
  `get_serializer_save_kwargs(self, info, *, data, hook_context)`, not
  `(info, data, instance=None)`: the hardening revision withheld the live instance from
  every hook. `_assert_save_kwargs_not_model_fields` now refuses **any** save kwarg naming a
  model field, which rejects the item's own `owner=request.user` example — model-field
  injection goes exclusively through the audited `Meta.injected_fields` channel, so the
  two items are now one policy rather than two overlapping seams. The live fixture stamps a
  non-model `stamp` kwarg the serializer's `create()` consumes; `topic` is the *negative*
  fixture (the model-field rejection), so the spec's live-test claim named the wrong one.
- **The explicit injection contract — `_assert_injected_field_agreement` never existed.**
  The item named a symbol with zero occurrences package-wide. Runtime acceptance of an
  injected field rides the ONE unified `_write_surface_specs` walk through
  `_assert_schema_runtime_agreement`, which is better than a parallel guard would have been:
  an injected field and an input field get the same checks by construction rather than by
  two bodies staying in step. The `get_serializer_injected_data` signature also gained
  `hook_context` with the hardening.
- **The schema/runtime agreement guard — two drift arms were unstated, and the
  missing-`Meta` case was a fail-open.** The guard also holds requiredness drift and
  annotation-`repr` drift, which the item did not mention. More importantly the meta arm
  read `getattr(mutation_cls, "_mutation_meta", None)` and *returned* on `None`, silently
  skipping both arms — a guard reporting agreement it never checked. `_mutation_meta` cannot
  legitimately be absent there (the base class defaults the attribute, the metaclass rejects
  an abstract base, and the same module dereferences it unguarded strictly earlier), so the
  shipped fix raises for both incoherent spellings and the item now states the snapshot
  requirement as a contract.
- **Visibility-scoped relation validation — the extracted type-check helper is public and
  shared.** The item named `_type_check_relation_id`; it lives at
  `utils/write_values.py::type_check_relation_id`, in the shared decode substrate all three
  flavors call.
- **Opt-in nested serializer inputs — an empty declaration is carved out.** The item read as
  unconditional ("`Meta.nested_fields` **REQUIRES** … override"); a `Meta.nested_fields =
  {}` opts nothing in, passes no nested data, and demands no override.

## Non-Decision deliberation

Findings and provenance that belong to no single Decision. Every entry below is this
pass's own, and every one is an observation about the **spec's own text**: this move
checked nothing against `HEAD`.

- **The `Justification:` / `Alternatives considered (and rejected):` pairing is 1:1 across
  all fourteen Decisions, and that is a measured result rather than an inference from two
  equal counts.** The `037` execution of this move found a Decision with a justification
  and no alternatives and another with the reverse, and had to carry an explicit `None.`
  in both files so a later reader could not mistake a genuine absence for a chunk the move
  dropped. `spec-039` needed neither: the two label lists interleave strictly and each
  pair sits under exactly one Decision heading.
- **The glossary gate, not the carve-out, decided what stayed — and it caught the same two
  terms it caught on `038`.** The implementation-relevance carve-out
  ([`docs/builder/BUILD.md`][build-md] `## Spec rationale extraction`) would not have held
  back
  [Decision 3](#decision-3--class-meta-surface-not-graphenes-mutationoptions)'s
  sibling-surface parenthetical, which is ordinary deliberation; it stayed because it
  carries the spec's only links to [`FilterSet`][glossary-filterset] and
  [`OrderSet`][glossary-orderset]. Worth naming twice because the coupling is invisible
  from either document: a spec's `-terms.csv` silently pins which prose the rationale move
  may not take, and the failure surfaces as a gate exit 1 rather than as a reading error.
  The two set-family terms sit in a spec about mutations for one reason only — they are
  the prior set-family precedent the CSV's own `notes` column cites — so any future
  serializer-shaped card will hit this same pair again.
- **The `Recorded floor` hold-back is a different failure mode from the glossary one, and
  no gate would have caught it.** `check_spec_glossary.py` compares terms and anchors; it
  cannot tell that a section body carries the spec's only statement of a pinned dependency
  version. Had the whole Risks body moved, the spec would have kept a Slice 0 checklist
  demanding "three places that must agree" while carrying none of them, and both the
  `## User-facing API` and `## Test plan` partial-update assertions would have cited a
  floor the spec no longer stated. The rule that caught it is the carve-out's own
  tie-break: when it is unclear whether a sentence is deliberation or instruction, it
  stays.
- **Every moved block was checked against the carve-out, and the normative statement each
  one explains survives in the spec.** The rejected alternatives most at risk of taking a
  contract with them were
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)'s
  third ("pass relation ids straight to the serializer without the visibility decode" —
  rejected because a `PrimaryKeyRelatedField`'s default queryset is not request-scoped) and
  [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)'s
  second (graphene's `Field → String` catch-all — rejected because it shadows the raise).
  Both Decision bodies state the requirement normatively without the rejection: Decision 8
  pins the decode-time `get_queryset` check on every relation branch, and Decision 7 pins
  the raising fallthrough. Neither move can produce the defect its rejection warns about.
- **Slice 2 obligation — the post-ship hardening blockquote is an amendment block, and it
  could not be moved.** The spec opens with a 178-line
  `> **Post-ship hardening revision (2026-07-15, on `main` after `0.0.13`).**` blockquote
  that says a security audit "superseded parts of this spec's hook contract" and that
  "where this spec and the code disagree, the code and [`docs/README.md`][docs-readme]
  govern". Its framing is pure chronology and belongs here; its **bullets are the current
  contract** of the hook surface, the alias guard, the phase separation, the drift
  snapshot, the relation-intent ledger and the post-save attestation, and nothing else in
  the spec states them. Moving the framing alone would leave the spec asserting a
  superseded hook contract in
  [Decision 7](#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth)
  and
  [Decision 8](#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload)
  with no correction at all — strictly worse than the chronology, exactly as the `038`
  execution found for its own ordering correction. So it stays until a pass can fold each
  bullet into the Decision it supersedes and delete the blockquote. That is a spec rewrite,
  and the reconciliation slice owns it.
- **Slice 2 obligation — the `[superseded by the 2026-07-15 hardening revision — …]`
  bracket inside the Slice 3 checklist.** The `## Slice checklist` construct step spells
  the pipeline as `serializer_class(**get_serializer_kwargs(...))` and then appends a
  bracketed note saying that shape "no longer describes the construct step". A checklist
  box is the one place a stale figure is a false completion claim
  ([`docs/builder/BUILD.md`][build-md]
  ``### `## Current state`: observations stand, predictions do not``), so the fix is to
  state the shipped construct step directly and retire the bracket — a rewrite, not a cut.
- **The process labels are gone from the spec, and the count that justified the work was
  three different numbers.** `spec-039` keyed its emphasis to `P1.x` / `P2.x` / `P3`
  DRY-promotion tiers and to bare `F<N>` / `M<N>` / `H<N>` review-finding identifiers, which
  [`AGENTS.md`][agents] bans from standing prose. The strip was held back until the audit
  passes finished, because those passes navigate the spec by the labels, and until it could
  land in one pass with its `.py` citer sweep — stripping a label vocabulary is a rename
  that strands every citer, and no gate in this repo can see it. Three published figures
  disagreed about the size of the population and all three were instruments rather than
  measurements: a right-word-bounded glob said 165, a left-bounded one said 175 and later
  186, and the difference is that a left-bounded glob counts the `M2` inside `M2M`. The
  measured population was **177** occurrences over 37 distinct tokens, plus one `Medium-7`
  severity label no `P|F|M|H|D`-shaped glob can see. Foreign-spec labels stayed: `G2`
  (12 occurrences, [`spec-035`][spec-035]'s goal vocabulary), `AR-H5` and `036 Medium-1`
  (both [`spec-036`][spec-036]'s). The labels that moved into this file with the revision
  history stay here, where they are a dated record of what a review round found rather than
  standing prose.
- **Three `###` headings carried a tier label, and nothing linked to them.** The strip
  renamed `Promotions to single-site now (P1 — third-copy forks)`,
  `Single-siting that prevents drift (P2)` and
  `Small reuses to pin; deliberately not applicable (P3)`, changing each one's GitHub anchor
  slug. A repo-wide sweep for the three old slugs found **zero** inbound references, in the
  spec, in this file, and in every other tracked `.md` — so the rename stranded nothing.
  The promotion table's key column moved from tier ordinals to content names for the same
  reason [`START.md`][start] gives for citing a contract by content: a heading rewrite
  strands every ordinal, and a content name survives one.
- **The round vocabulary is retired, and the ordinals were the citer population.**
  Seventeen `###` headings named themselves after the review pass that proposed them, and
  the section heading `Round-6 improvements (better-than-graphene-django)` was round
  provenance too — the attribution [`START.md`][start] "Style Rio cares about" forbids in
  standing prose. All eighteen were renamed: the section to
  `Improvements over graphene-django's DRF integration`, taken from the section's own
  opening sentence, and each subsection to the content title it already carried after the
  prefix. The subsection order was already thematic rather than numeric and was kept; the
  preamble now names the ordering so a reader can navigate it without the numbers.
  Pre-retirement population: **62** occurrences in the spec and **19** in this file. (The
  **18** an earlier pass published was a count of *lines*; one line here carries two
  occurrences, which is exactly why [`START.md`][start] says to count occurrences and not
  lines.) **The anchors stranded nothing** — a repo-wide sweep found zero inbound
  references to any of the seventeen subsection slugs, and the section slug was cited only
  by the spec's own link definition, re-pointed in the same pass. What the rename really
  stranded was every **ordinal**: each `rev6 #N` and each bare `#N` in prose, in both files.
  All of them are now content names, per [`START.md`][start]'s rule that a contract is cited
  by content because a heading rewrite strands an ordinal.
- **The improvement count is seventeen, and the preamble's own arithmetic is what made that
  worth measuring.** The preamble says "16 improvements … plus one follow-on (#17)", which
  reads as seventeen and is; the section's heading list carried `#1` through `#17`, each
  exactly once, in a deliberately non-numeric order that the retirement kept. The
  replacement preamble states the measured count rather than the arithmetic.

### Post-ship findings that belong to no single Decision (`039` residual reconciliation, 2026-09-05)

Unlike the entries above this heading, these were measured against `HEAD`.

- **The head opener and `## Goals` item 3 both said "byte-identical", and the envelope is
  additive.** Same falsification as Decision 2's; recorded here because the opener is not a
  Decision and a reader forms their model of the card from it first. The full population was
  seven sites, not two: besides the opener and the goal, the document title, Decision 5's
  "returns the frozen envelope" sentence, the graphene-parity `serializer.errors` row, the
  rejected-second-envelope bullet, and the flattener section's two "frozen envelope"
  mentions all asserted the unextended contract. All seven now state the additive one, and
  the `## Key glossary references` bullet names the extension rather than only the freeze.
  Two "`spec-036` **froze** X" sentences stay: they describe what the predecessor card did,
  and Decision 2 carries the carve-out for what this one added. Decision 2's own heading
  keeps the word `frozen` because rewriting it would strand every `#decision-2--…` anchor in
  both files.
- **`## Current state` survives verbatim, and that is a decision rather than an omission.**
  Eleven of its clauses are dated observations the section header licenses — "no
  `rest_framework/` module exists", "the version line reads `0.0.12`", "products has no
  `serializers.py` yet" — all falsified *by the build*, which is what a `## Current state`
  is for. Its predictions were graded separately and every one held. The two present-tense
  claims that needed re-tensing were in `## Goals` and `## Out of scope`, where nothing
  dates them.
- **The `### Import manifest` moved from per-symbol to per-module granularity.** Audits
  found all four of its rows measurably stale at once — symbols that had moved, symbols
  never imported, symbols belonging to a sibling module — and re-deriving them by hand would
  have produced a manifest stale again at the next legitimate DRY-driven move *inside* a
  permitted module. Three resolutions were on the table: re-derive per-symbol from a
  measured population; narrow to module granularity; or retire the manifest and keep only
  the "do not re-implement" prose. Module granularity was chosen because it is the level at
  which the contract is actually stable, and because the per-symbol obligation that genuinely
  needs a ratchet already has an executable one
  (`tests/rest_framework/test_dry_import_ratchet.py`). Retiring the manifest entirely was
  rejected: the DoD cites it, and prose with no enumerated population is not checkable.
- **The Slice-1 DRY bullet's DoD check was a grep that was never written.** It was the
  cycle's only DROPPED row. Identity beats a grep on both sides: a grep is satisfied by a
  same-named local carrying a copied body, and it breaks on a legitimate import-style
  change. The spec now states the mechanism, the population, and one ceiling — the four
  input-kind constants are interned `str`, so their rows catch a deletion and a value drift
  but not a same-valued re-spelling. Stating the ceiling matters more than closing it: a
  guard whose limits are unwritten reads as covering more than it does.
- **Four P-table cells cited symbols that no longer exist** (`_VALID_FORM_OPERATIONS`, the
  model flavor's id-set decoder and its four error helpers, the form flavor's own
  model-backed sync pipeline, `FormInputFieldSpec`). Each sat in a "Duplicated today"
  column describing the fork a promotion resolved, so the promotion itself is what deleted
  them. They are now described by content rather than by dead name — a fork that no longer
  exists cannot be cited by symbol, and `scripts/check_citations.py` reads `.py` and
  `KANBAN.md` only, so nothing would ever have flagged them.
- **The three obligations the rationale move logged for the reconciliation slice, and where
  each stands.** That earlier entry is left as written — this file is append-only during a
  build — so its present tense ("it stays until a pass can fold each bullet…") is now the
  record of a state, not a claim about today. The **hardening blockquote** is folded and
  deleted (Decision 8 above records the fold, bullet by bullet, and what the hardening
  changed). The **`[superseded by …]` bracket** in the Slice-3 checklist is gone: the
  construct step now states the shipped contract directly, so there is nothing left for a
  marker to point at. The **process-label vocabulary** is deliberately still there.
- **The `.py` citer population was wider than the census that dispatched it.** The
  dispatched figure was 21 label-carrying comment lines across eight files, derived from a
  `P|F|M|H|D`-shaped glob. The sweep found the same tokens plus `Md1`-`Md7`, `SR-3`, `D8`,
  and the bare severity words `High` and `Medium` used as review labels — vocabulary the
  dispatching glob was not written to see — across **fifteen** files, the example project
  and the package tests included. A positive-vocabulary census misses whatever it was not
  written to see; the correction is two independent instruments and a stated pattern beside
  every published figure.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[django-workflow]: ../../../.github/workflows/django.yml
[goal]: ../../../GOAL.md
[kanban]: ../../../KANBAN.md
[pyproject]: ../../../pyproject.toml
[pytest-ini]: ../../../pytest.ini
[start]: ../../../START.md

<!-- docs/ -->
[docs-readme]: ../../README.md
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror
[glossary-djangoformmutation]: ../../GLOSSARY.md#djangoformmutation
[glossary-djangomodelformmutation]: ../../GLOSSARY.md#djangomodelformmutation
[glossary-djangomodelpermission]: ../../GLOSSARY.md#djangomodelpermission
[glossary-djangomutation]: ../../GLOSSARY.md#djangomutation
[glossary-djangomutationfield]: ../../GLOSSARY.md#djangomutationfield
[glossary-djangotype]: ../../GLOSSARY.md#djangotype
[glossary-fielderror-envelope]: ../../GLOSSARY.md#fielderror-envelope
[glossary-filterset]: ../../GLOSSARY.md#filterset
[glossary-finalize_django_types]: ../../GLOSSARY.md#finalize_django_types
[glossary-orderset]: ../../GLOSSARY.md#orderset
[glossary-serializermutation]: ../../GLOSSARY.md#serializermutation
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-035]: ../spec-035-optimizer_hardening-0_0_10.md
[spec-036]: ../spec-036-mutations-0_0_11.md
[spec-037]: ../spec-037-upload_file_image_mapping-0_0_11.md
[spec-038]: ../spec-038-form_mutations-0_0_12.md
[spec-039-borrowing-posture]: ../spec-039-serializer_mutations-0_0_13.md#borrowing-posture
[spec-039-d10]: ../spec-039-serializer_mutations-0_0_13.md#decision-10--operations-create--update-no-serializer-delete
[spec-039-d11]: ../spec-039-serializer_mutations-0_0_13.md#decision-11--write-authorization-reuse-the-036-seam-djangomodelpermission-for-the-modelserializer
[spec-039-d12]: ../spec-039-serializer_mutations-0_0_13.md#decision-12--soft-djangorestframework-dependency-and-the-100-coverage-strategy
[spec-039-d13]: ../spec-039-serializer_mutations-0_0_13.md#decision-13--live-coverage-products-grows-a-modelserializer-mutation
[spec-039-d14]: ../spec-039-serializer_mutations-0_0_13.md#decision-14--version-bumps-are-owned-by-the-joint-0013-cut
[spec-039-d1]: ../spec-039-serializer_mutations-0_0_13.md#decision-1--spec-filename-and-canonical-naming
[spec-039-d2]: ../spec-039-serializer_mutations-0_0_13.md#decision-2--card-scope-boundary-the-serializer-flavor-ships-auth-stays-out-the-frozen-036-contracts-and-the-038-factory-are-reused-unchanged
[spec-039-d3]: ../spec-039-serializer_mutations-0_0_13.md#decision-3--class-meta-surface-not-graphenes-mutationoptions
[spec-039-d4]: ../spec-039-serializer_mutations-0_0_13.md#decision-4--module-and-test-locations-rest_framework-subpackage-mirroring-forms
[spec-039-d5]: ../spec-039-serializer_mutations-0_0_13.md#decision-5--public-surface-serializermutation-exported-from-the-root-the-038-generalized-factory-reused
[spec-039-d6]: ../spec-039-serializer_mutations-0_0_13.md#decision-6--base-class-strategy-serializermutation-rides-the-djangomutation-base-modelserializer-driven
[spec-039-d7]: ../spec-039-serializer_mutations-0_0_13.md#decision-7--serializer-field--strawberry-input-mapping-the-serializer-is-the-input-source-of-truth
[spec-039-d8]: ../spec-039-serializer_mutations-0_0_13.md#decision-8--resolver-pipeline-instantiate--is_valid--serializererrors--save--optimizer-re-fetch--payload
[spec-039-d9]: ../spec-039-serializer_mutations-0_0_13.md#decision-9--optimizer-composition-the-modelserializer-payload-re-fetch-rides-the-spec-036-g2-path
[spec-039-dry]: ../spec-039-serializer_mutations-0_0_13.md#cross-flavor-reuse-and-dry-obligations
[spec-039-implementation-plan]: ../spec-039-serializer_mutations-0_0_13.md#implementation-plan
[spec-039-terms]: spec-039-serializer_mutations-0_0_13-terms.csv
[spec-039-test-plan]: ../spec-039-serializer_mutations-0_0_13.md#test-plan
[spec-039]: ../spec-039-serializer_mutations-0_0_13.md

<!-- docs/builder/ -->
[bld-039-slice-0]: ../../builder/bld-039-slice-0-rationale_extraction.md
[build-039]: ../../builder/build-039-serializer_mutations-0_0_13.md
[build-md]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->
[forms-converter]: ../../../django_strawberry_framework/forms/converter.py
[forms-resolvers]: ../../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../../django_strawberry_framework/forms/sets.py
[mutations-inputs]: ../../../django_strawberry_framework/mutations/inputs.py
[mutations-sets]: ../../../django_strawberry_framework/mutations/sets.py
[types-finalizer]: ../../../django_strawberry_framework/types/finalizer.py

<!-- tests/ -->
[test-rest-framework]: ../../../tests/rest_framework/

<!-- examples/ -->
[products-models]: ../../../examples/fakeshop/apps/products/models.py
[test-products-api]: ../../../examples/fakeshop/test_query/test_products_api.py
[test-query-readme]: ../../../examples/fakeshop/test_query/README.md
[test-uploads-api]: ../../../examples/fakeshop/test_query/test_uploads_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
