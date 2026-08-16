# Build: R1b — Clause-by-clause mechanism sweep of the whole spec

Spec reference: `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` (lines 1-1096)
Status: final-accepted

## Plan (Worker 1)

Run 2026-08-16 by a fresh Worker 1 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-1.md`. **Combined plan + perform pass**, per the build
plan's `### Deviation 3` (Worker 1 is the only role that may mutate the spec, and this item's entire
deliverable is spec and rationale edits) and `### Maintainer decision 4`, which authorized the sweep and
split it out of R1.

**HEAD re-derived: `973d00b2`.** It had moved from the `066c068b` R1's final verification read, and from
the dispatch's hash before that. `git status --porcelain` is **124** entries; none of it intersects this
cycle's writable set and none of it was reverted. `git stash` / `checkout` / `restore` / `worktree` were
not used; the HEAD reference is `git show HEAD:<path>` into a scratch path outside the repository.

**Spec status-line re-verification (per-spawn duty).** Lines 1-5 re-read. The opener describes the
rationale companion, the four finalization sites, and the six scrubbed mechanisms. None of the four
corrections below falsifies any of it — no scrubbed mechanism returns, no finalization site changes, and
the rationale companion gains three entries rather than a new role. **No edit owed.**

### Scope

R1 verified the **112 lines this cycle added**. R1b covers the **984 pre-existing lines** — every line
of spec text no pass had opened at the mechanism level — plus two added-text sites (`:930`, `:1002`) the
maintainer routed here explicitly.

The defect class, restated: **a sentence asserting a mechanism, seam, cause, recourse, or capability the
code does not have.**

Out of scope, per the dispatch and re-confirmed as untouched below: the ~60 upstream `file:///…#LNN`
citations; the `## The 0.0.4 local package baseline` section as a deliberately historical snapshot (its
two "retired since" markers are still enumerated and opened, because they are claims about *today*);
prior-art descriptions of what upstream does; and forward design prescriptions for unshipped work.

### DRY analysis

**Helper inventory checked.** Not applicable in the code sense — this item writes no Python and plans
no helper. The inventory's purpose here is the documentary analogue, and it was run as the
single-ownership check `## Final verification job` step 4 prescribes: after the four corrections, `grep`
for the responsibility-to-seam map's bullet shape returns **four** bullets, all in `### Layer 4`
(`:647-650`); `### Phase 3` and `### Decision 3` now cite that section rather than restating a
lossy copy of it. That is the *same* consolidation R1's apply-changes pass 3 made when it deleted the
Borrow chapter's duplicate list, applied to the two remaining restatements.

- **Existing patterns reused.** The correction shape from R1: **cut the false clause, do not qualify
  it**, and let the section that owns the mechanism carry the scoped statement. Two of the four
  corrections are pure cuts; two are replacements, each earning it under R1's rule (`replace when the
  reason is checkable by the reader at their desk from the cited symbol`).
- **New helpers justified.** None. No new vocabulary, constant, or convention is introduced. The one
  new cross-reference (`### Decision 3` → `` `### Layer 4: Generated relation fields` ``) reuses the
  code-span heading-citation form the spec already uses at `:415` and `:930`.
- **Duplication risk avoided.** The obvious naive fix for `:930` / `:1002` is to *restate* Layer 4's
  per-seam scoping in both places. That would create the third and fourth copies of exactly the map
  whose duplication R1 spent three passes closing, and a duplicated map has no correct state — only a
  current half and a stale half. Both corrections therefore **shrink** to a pointer.

### Implementation steps

Performed in this same pass; line numbers are the current file's.

1. `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:610` — replace the three-member `Literal`
   with the alias name.
2. `…:394` — narrow the schema-audit benefit to the capability `check_schema` has.
3. `…:930` — cut `visibility composition` from Phase 3's generation list.
4. `…:1002` — cut it from Decision 3 and name the seams' real owner by pointer.
5. `docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md` — append one entry per
   correction (three entries; `:930` and `:1002` are one argument and share an entry), each naming the
   spec section by heading, what was cut or replaced, why, and the rejected alternative.
6. Re-run both gates, the link / anchor / rule-27 audit, the append-only proof, the byte ledger, the
   numbering check, and the five cross-spec anchors.

### Test additions / updates

None. This item runs no tests and changes no code. The read-only temp test under
`docs/builder/temp-tests/r1/` was **not** modified, moved, or deleted, and was not re-run — it belongs
to R1's escalation 8 and this pass has no claim resting on it.

### Implementation discretion items

None. Every correction's shape was decided here and is recorded with its reason in the rationale.

### Dispatched findings checklist

Derived by this pass rather than handed down: one box per false clause the enumeration found, ticked as
it was fixed.

- [x] `spec-009:610` — `relation_kind: Literal["forward_single", "many", "reverse_one_to_one"]  # mirrors utils.relations.RelationKind` names **three** of `utils/relations.py::RelationKind`'s **five** members, and asserts a mirror it does not have
- [x] `spec-009:394` — `[schema audit] can report exact unfinalized or unresolved fields`; `optimizer/extension.py::DjangoOptimizerExtension.check_schema` reports unresolved relation targets only, and structurally cannot observe an unfinalized field
- [x] `spec-009:930` (`### Phase 3`) — `Generate the annotation, resolver, and visibility composition for every exposed relation, at finalization, across every cardinality`; the finalizer generates no visibility composition at any cardinality
- [x] `spec-009:1002` (`### Decision 3`) — `Generate a relation field's annotation, resolver, visibility composition, and arguments at finalization`; same over-claim, plus `arguments`, which a forward single relation and a `"list"`-shaped relation also never receive

**Boxes added by the apply-changes pass** (appended, never rewriting a box above), one per false clause
Worker 3's review found plus the two Lows it recorded as examined. See
`## Build report (Worker 1, apply-changes pass)` for the evidence behind each.

- [x] **High** — rationale `` ### `### Phase 3 …` and `### Decision 3 …` `` entry: three false mechanism claims on a row-visibility boundary — a five-of-**eight** call-site list presented as exhaustive, `A **forward single** relation reaches none of them`, and the same absolute for a `"list"`-shaped many relation. `optimizer/walker.py::_build_child_queryset` composes visibility onto exactly those relations
- [x] **Medium** — `spec-009:417`: a third copy of the seam map naming 3 of the 8 invoking modules, a *different* incomplete triple than `### Layer 4`'s, two lines after `:415` declares the map stated once and not repeated
- [x] **Medium** — rationale `` ### `### Layer 2 …` `` entry: `the two that decide many-side classification through MANY_SIDE_RELATION_KINDS`, against a **three**-member frozenset whose third member `"many"` was already in the sketch
- [x] **Low 2, decided: fix** — `spec-009:930`'s surviving `across every cardinality`, the absolute the same rationale entry's own generalisable rule condemns
- [x] **Low 1, decided: no document edit** — the two non-reproducing evidence counts; both underlying claims re-verified true and the reproducing commands recorded in the new report, the closed enumeration table left unedited
- [x] **Consequential** — `spec-009:1002`'s new `whichever field owns the queryset`, which over-narrows: `optimizer/walker.py::_build_child_queryset` is one of the seams and is not a field

**Boxes added by apply-changes pass 2** (appended, never rewriting a box above), one per correction the
final verification dispatched. All three land in the rationale; none has a spec twin, which was checked
rather than assumed. Correction 3 is two clauses by the dispatch's own wording, so the three boxes map
to **four** clause edits; `## Build report (Worker 1, apply-changes pass 2)` carries the mapping and the
pasted command output behind each.

- [x] **Medium** — rationale `` ### `### Layer 2 …` `` entry: `This is the one place on this document where a replacement beat a cut`, a false definite description disproved 15 lines below by the same append's `narrowed … not cut` and 57 below by `### Decision 3 was replaced rather than cut`. **Deleted, not re-counted**
- [x] **Low 1, decided: fix** — rationale `` ### `### Phase 3 …` and `### Decision 3 …` `` rejected alternative: the harm clause named the configuration in which being unfiltered is harmless (target does **not** override `get_queryset`, so the default identity hook loses no rule). Polarity swapped to the harmful inverse the entry's own bullet 2 sets up
- [x] **Low 2, decided: fix** — two evidence spellings that do not reproduce: `plan_optimizations is imported by optimizer/extension.py and nothing else` (false repo-wide — three test modules and `scripts/bench_optimizer_walk.py` import it) and the `:768` grep parenthetical, whose command reaches **nine** paths, not the eight listed

**Box added by apply-changes pass 3** (appended, never rewriting a box above). One box, one clause edit,
in the rationale; the spec twin check was run with the shortest distinctive tokens and returned no twin,
so the spec is byte-unchanged. It is a newly-found false clause by the same criterion every box above
used — a present-tense, symbol-anchored mechanism claim in a permanent document that the named symbol's
own source refutes — so it earns a box rather than riding under a prior one.
`## Build report (Worker 1, apply-changes pass 3)` carries the pasted command output behind it.

- [x] **Medium** — rationale `` ### `### Phase 3 …` and `### Decision 3 …` `` entry: `at finalizer Phase 2` governed **both** named seams, and is false for the first. `resolved_relation_annotation` has exactly one package call site, inside **Phase 1**'s failure-atomic pending-relation walk. **Ordinal dropped, not restated** — restored to `at finalization`, the spelling `spec-009:930` already uses for the same pair

---

## Perform report (Worker 1, combined pass)

### Method, and why the denominator is reported

R1's, unchanged: **enumerate** every causal / mechanism / seam-attribution / recourse / capability
clause across the file; **open the symbol each names**; **cut what is false** or replace it with a
clause verified the same way; **report the denominator** so a reviewer audits coverage instead of
re-deriving it.

Two method corrections R1 paid for, both applied here:

- **An invariant comment validates the RULE, not the REASON.** Every causal clause was checked against
  the mechanism it names, never against the docstring motivating the rule it supports. The `:930` /
  `:1002` finding is exactly this: `### Layer 4`'s own visibility bullet is *correct*, and four review
  passes had confirmed it — but neither summary sentence had ever been opened at
  `apply_type_visibility_sync`'s call sites.
- **Wrapped phrases defeat multi-word greps.** Every population claim below was established with the
  shortest distinctive token and counted as *occurrences*, never with a phrase.

**Counts were produced by parsing the tables mechanically, not by eye** — R1's numbers were wrong twice
for exactly that reason. The parser counts a table row as a line starting `|` that is neither the header
nor the `|---|` rule, and buckets it on its `Verdict` cell.

### Denominator

Every figure below was **parsed off the tables**, not counted by eye, and the buckets sum to the row
total as a self-check.

**103 clause sites enumerated** across all 1,096 lines. Of those:

- **59 opened** at the symbol they name — the verdict is `true` or `FALSE`;
- **4 FALSE**, all four corrected in this pass (2 cuts, 2 replacements);
- **55 true**;
- **31 `judgement`** — an argument, a normative prescription, a goal, or a forward design
  prescription for unshipped work. None names a checkable symbol asserting present-tense behavior;
- **9 `note (upstream)`** — a description of what graphene-django, strawberry-graphql-django, or
  Graphene-Django does, where the named upstream module was located but its behavioral detail was not
  re-derived; a divergence here is a note, not a cut, per the dispatch. Four *other* upstream claims
  were cheap enough to open at the upstream symbol and are recorded `true` rather than `note`
  (`:280` `Dynamic`, `:387` `__strawberry_django_definition__`, `:422` `resolve_type`, `:479`
  `DjangoListConnection.total_count`);
- **4 `out of scope`** — the three upstream `file:///` citation blocks and the historical baseline
  snapshot, all excluded by the dispatch. The baseline's two "retired since" markers are **not**
  excluded: they are claims about the package today and are opened below.

`55 + 4 + 31 + 9 + 4 = 103` ✓.

**The pre-existing text is in markedly better shape than the added text was**, and the reason is
structural rather than lucky: 984 lines of a horizon document are overwhelmingly **prescriptive** — a
"should", a "take this", a "recommended adaptation" — and a prescription cannot be false *about a
mechanism*. The defect class needs a present-tense assertion to attach to, and pre-existing text offers
far fewer of them per line than a fix pass's connective tissue does. Three of this item's four findings
sit in the four places the pre-existing text does assert present tense: a code sketch's comment, a
`Benefits:` list, and two one-line summaries of another section's map.

### Enumeration table — spec (`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`)

| Site | Clause asserts | Symbol opened | Verdict |
|---|---|---|---|
| `:6` | purpose framing | — | judgement |
| `:8` | the narrow definition-order problem is documented in spec-008 | `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` (exists) | true |
| `:19-23` | cookbook schema citations | — | out of scope |
| `:25-36` | the Graphene reference exposes four model nodes with those ten members | `django-graphene-filters` cookbook | note (upstream) |
| `:41-63` | the target `class Meta` shape | R1's Group C (declaration untouched) | true |
| `:74-78` | the architectural goals the class names serve | — | judgement |
| `:83-95`, `:100-116` | the 0.0.4 baseline snapshot | — | out of scope (deliberately historical) |
| `:96` | `convert_relation` retired; relation annotations now resolve through `resolved_relation_annotation` | `types/converters.py::resolved_relation_annotation` (present, three-branch) | true |
| `:99` | `TypeRegistry.lazy_ref` retired; the pending-relation API superseded it | `registry.py` — `lazy_ref` **0** package-wide; `add_pending_relation` / `iter_pending_relations` / `discard_pending` present | true |
| `:123-144` | django-graphene-filters source references | — | out of scope |
| `:150-159` | `AdvancedDjangoObjectType` owns six `Meta` keys; this package's equivalent is `DjangoType.Meta` | `types/base.py::ALLOWED_META_KEYS` | true |
| `:161` | keeping Graphene names serves the migration path | — | judgement |
| `:164-175` | `AdvancedDjangoFilterConnectionField` binds eight things; the Strawberry equivalent is `DjangoConnectionField` | `connection.py::DjangoConnectionField` | true |
| `:178-187` | `LazyRelatedClassMixin` solves circular class graphs | upstream `mixins.py` | note (upstream) |
| `:189-194` | the lazy-ref pattern is reused for `RelatedFilter` / `RelatedOrder` / `RelatedAggregate` | `filters/base.py::RelatedFilter`, `orders/base.py::RelatedOrder` (present); `RelatedAggregate` absent and carded | true |
| `:196-206` | BFS factory architecture, adapted for Strawberry | — | judgement |
| `:209-219` | class-based generated type naming as a core invariant | — | judgement |
| `:221-232` | the Graphene package's layered permission model | upstream `permissions.py` | note (upstream) |
| `:234-247` | `AdvancedAggregateSet` semantics | upstream `aggregateset.py` | note (upstream) |
| `:249-255` | `AdvancedFieldSet` semantics | upstream `fieldset.py` | note (upstream) |
| `:259-277` | what to scrap / keep from django-graphene-filters | — | judgement |
| `:280` | Graphene-Django solves bidirectional relations with `Dynamic` relation fields | `graphene_django/converter.py` — `Dynamic(dynamic_type)` at three converter returns | true |
| `:282-293` | take / do-not-take from Graphene-Django | — | judgement |
| `:295` | the equivalent is a package-owned pending relation registry plus a Strawberry-native finalization pass | `registry.py::TypeRegistry.add_pending_relation`; `types/finalizer.py::finalize_django_types` | true |
| `:302-341` | strawberry-graphql-django source references | — | out of scope |
| `:344-352` | `_process_type`'s eight-step lifecycle | upstream `type.py::_process_type` | note (upstream) |
| `:355-362` | recommended lifecycle adaptation | — | judgement |
| `:365` | this gives the field metadata model without the decorator API | — | judgement |
| `:370-383` | the `DjangoTypeDefinition` sketch | R1's D10 (`fields_spec` / `exclude_spec`, subset declared) | true |
| `:387` | stored as `__django_strawberry_definition__`, mirroring upstream's `__strawberry_django_definition__` | `connection.py:178`/`:1386`/`:1582`/`:1690`/`:1771`; `strawberry_django/type.py:410` | true |
| `:391` | one canonical place for model/type metadata | — | judgement |
| `:392` | the optimizer can read from the definition rather than scattered class attrs | `optimizer/walker.py:317`, `optimizer/extension.py:1292`, `optimizer/nested_planner.py:896` | true |
| **`:394`** | **the schema audit can report exact *unfinalized* or unresolved fields** | **`optimizer/extension.py::DjangoOptimizerExtension.check_schema`; `docs/GLOSSARY.md` #"## Schema audit"** | **FALSE — NARROWED** |
| `:422` | `resolve_type` handles `strawberry.auto`, `Any`, and unresolved annotations via `resolve_model_field_type` | `strawberry_django/fields/base.py::StrawberryDjangoFieldBase.resolve_type` (`StrawberryAuto`, `Any`, `UNRESOLVED`) | true |
| `:426-429` | upstream's default relation fallback maps | R1-verified; upstream `fields/types.py` | true |
| `:431-439` | resolve relations to concrete registered types; five-step recommended behavior | — | judgement |
| `:444-450` | the Django edge cases those four upstream functions encode | upstream `fields/types.py` | note (upstream) |
| `:454-461` | keep this package's existing `SCALAR_MAP` as the initial supported set | `types/converters.py::SCALAR_MAP` (module-level `dict[type[models.Field], Any]`) | true |
| `:464-468` | `field` / `connection` as implementation patterns | upstream `fields/field.py` | note (upstream) |
| `:479` | `DjangoListConnection` has `total_count`, queryset awareness, optimized connection resolution | `strawberry_django/relay/list_connection.py::DjangoListConnection.total_count` | true |
| `:496-504` | **six shipped-optimizer capabilities**: root gating; `select_related` / `prefetch_related` / `only`; consumer-shaping preservation; `Prefetch` downgrade on a custom `get_queryset`; strictness warn/raise; plan caching | `optimizer/extension.py` #"gates on ``info.path.prev is None``"; `optimizer/plans.py` (`select_related` / `prefetch_related` / `only_fields`); `optimizer/plans.py::diff_plan_for_queryset`; `optimizer/walker.py::_target_has_custom_get_queryset` → `("prefetch", "custom_get_queryset")`; `optimizer/extension.py` `strictness not in ("off", "warn", "raise")` guard; `optimizer/extension.py::_build_cache_key` | true (all six) |
| `:509-511` | nested-prefetch lessons to borrow | — | judgement |
| `:518-524` | `django_resolver` / `django_getattr` centralize five patterns incl. async contexts | upstream `resolvers.py` (R1-verified) | true |
| `:531-545` | filter/order processing to borrow and not adopt | — | judgement |
| `:552-558` | what to scrap from Strawberry-Django, incl. `QuerySet._clone` monkey-patching | upstream `optimizer.py` | note (upstream) |
| `:560-566` | keep-as-references list | — | judgement |
| `:571-574` | the four-part hybrid | — | judgement |
| `:577-590` | Layer 1 collection responsibilities; do not call `strawberry.type(cls)` until finalization | `types/base.py` — **0** `strawberry.type(` calls | true |
| `:592-597` | the registry distinguishes unfinalized / finalized / pending / unresolved | `registry.py` — `_pending`, `_finalized`, `_definitions`; note that `is_finalized` is registry-global rather than per type | true |
| `:604-609`, `:611-612` | the `PendingRelation` sketch's other slots | R1's Group C | true |
| **`:610`** | **`relation_kind: Literal["forward_single", "many", "reverse_one_to_one"]` "mirrors `utils.relations.RelationKind`"** | **`utils/relations.py::RelationKind` — **five** members; `utils/relations.py::MANY_SIDE_RELATION_KINDS`** | **FALSE — REPLACED** |
| `:616-618` | during collection: scalars known, targets resolved or pending | `types/base.py::DjangoType.__init_subclass__` | true |
| `:622-627` | during finalization: many-side → `list[target_type]`, reverse one-to-one → `target_type \| None`, nullable forward → `target_type \| None` | `types/converters.py::resolved_relation_annotation`; `optimizer/field_meta.py::FieldMeta` #"Reverse OneToOne short-circuits to ``True``" | true |
| `:629` | preserves the Graphene benefit without Graphene internals | — | judgement |
| `:638` | finalization precedes schema conversion, so no post-schema patching is needed | `types/finalizer.py` — Phase 3 is `strawberry.type(...)` | true |
| `:639` | **a schema extension cannot be the trigger, because extensions run after the schema is already built** | `strawberry/extensions/base_extension.py` — six hooks (`on_operation`, `on_validate`, `on_parse`, `on_execute`, `resolve`, `get_results`), every one per-operation; no schema-build hook exists | true |
| `:640` | one entry point regardless of import layout | same as `:634` | true |
| `:659-674` | Layer 5's twelve-step pipeline and the non-finalization contract | R1-verified | true |
| `:676` | the Strawberry equivalent of `AdvancedDjangoFilterConnectionField` | `connection.py::DjangoConnectionField` | true |
| `:681-694` | the `FilterSet` public API sketch | R1's D11 | true |
| `:700-706` | filter implementation: metaclass collects `RelatedFilter`; lazy class refs; BFS factory; class-based names; `Q` conversion; permission hooks before applying; related queryset scope boundaries | `filters/sets.py::FilterSetMetaclass`; `filters/base.py::RelatedFilter` (three target shapes, `bind_filterset`); `filters/factories.py::FilterArgumentsFactory` (BFS + collision check); `filters/sets.py` `models.Q` builders; `filters/sets.py::_run_permission_checks` | true |
| `:708-714` | borrow / do-not-adopt for filters | — | judgement |
| `:717-723` | `OrderSet`, `RelatedOrder`, nested ordering, permission hooks | `orders/sets.py::OrderSet`; `orders/base.py::RelatedOrder` | true |
| `:725-729` | recursive `process_order`; the six-member `Ordering` vocabulary | R1-verified (`orders/inputs.py`) | true |
| `:733` | prefer list-of-order-objects semantics for client parity | — | judgement |
| `:736-766` | Layer 8 aggregate system | unshipped; `TODO-BETA-057-0.1.3` | judgement |
| `:769-771` | Layer 9 wraps the generated resolver | `spec-054-fieldset-0_1_1.md` (R1-verified) | true |
| `:773-781` | the five-step FieldSet resolver order | unshipped; `TODO-BETA-054-0.1.1` | judgement |
| `:784-792` | Layer 10 implements `get_queryset`, `apply_cascade_permissions`, opt-in sentinel redaction | `types/base.py::DjangoType.get_queryset`; `permissions.py::apply_cascade_permissions`; redaction carded `TODO-BETA-059-0.1.4` | true |
| `:793-797` | the sentinel-vs-cascade open design point | — | judgement |
| `:802-809` | Layer 11 keeps six current features, incl. FK-id elision and queryset reconciliation | `optimizer/_context.py::DST_OPTIMIZER_FK_ID_ELISIONS`; `optimizer/plans.py::diff_plan_for_queryset`; plus the `:496-504` symbols | true |
| `:811-818` | Strawberry-Django lessons to add | — | judgement |
| `:823-840` | the recommended ten-step finalization algorithm | — | judgement |
| `:844-846` | unresolved exposed relation fields are errors, not skipped | `types/finalizer.py::_format_unresolved_targets_error` | true |
| `:849-867` | why generic fallback is not the default | — | judgement |
| `:870` | error-only contract; `finalize_django_types()` raises with the unresolved-targets format | `types/finalizer.py::_format_unresolved_targets_error`; `spec-010` #"### Unresolved-target error format" | true |
| `:872` | relaxing error-only earns its own card | — | judgement |
| `:877-888` | the proposed module layout | `ls django_strawberry_framework/` — `types/definition.py`, `types/finalizer.py`, `types/relations.py`, `schema.py`, `relay.py`, `connection.py`, `filters/`, `orders/`, `permissions.py`, `management/commands/export_schema.py` all present; `aggregates/` and `fieldset/` carded | true |
| `:892-898` | existing modules to evolve: `types/base.py` collection-only; `types/converters.py` scalar + relation-annotation helpers | `types/base.py` (**0** `strawberry.type(`); `types/converters.py::SCALAR_MAP` + `::resolved_relation_annotation` | true |
| `:901` | the phases are a dependency order, not a schedule | — | judgement |
| `:904-917` | Phase 1 ships the foundation slice | R1-verified against `spec-010` | true |
| `:920-927` | Phase 2 moves `convert_relation` to pending creation | historical plan against the retired baseline symbol (`:96`) | judgement |
| **`:930`** | **Phase 3 generates "the annotation, resolver, and visibility composition for every exposed relation … across every cardinality"** | **every `utils/querysets.py::apply_type_visibility_sync` / `_async` call site (`connection.py`, `list_field.py`, `types/relay.py`, `permissions.py`, `filters/sets.py` — none in `types/finalizer.py` or `types/resolvers.py`); `types/finalizer.py::_synthesize_relation_connections`** | **FALSE — CUT** |
| `:932-938` | Phase 3 acceptance tests, incl. reverse one-to-one → `None` and metadata pointing back at the definition | `types/resolvers.py` #"``try/except DoesNotExist``"; `types/definition.py::DjangoTypeDefinition` | true |
| `:940-949` | Phase 4 adds `DjangoConnection`, `DjangoConnectionField`, `DjangoNodeField`, Relay node, `totalCount` | `connection.py::DjangoConnection`, `::DjangoConnectionField`; `relay.py::DjangoNodeField` | true |
| `:951-962` | Phase 5 filters and ordering, incl. the row-preserving to-many path | R1-verified (`:961`) | true |
| `:964-974` | Phase 6 aggregates | unshipped | judgement |
| `:976-983` | Phase 7 FieldSet and permissions | R1-verified (`:979`, `:981`) | true |
| `:985-992` | Phase 8 optimizer expansion | — | judgement |
| `:996` | Decision 1 — concrete relation target by default, never generic `DjangoModelType` | `types/converters.py::resolved_relation_annotation` (no placeholder branch) | true |
| `:999` | Decision 2 — the explicit consumer call is the only trigger | R1-verified (`:634`) | true |
| **`:1002`** | **Decision 3 — "Generate a relation field's annotation, resolver, visibility composition, and arguments at finalization"** | **as `:930`, plus `types/finalizer.py::_synthesize_relation_connections` (arguments arrive only with a synthesized relation connection, i.e. many-side + Relay-Node target + `"connection"` / `"both"` shape)** | **FALSE — REPLACED** |
| `:1005-1008` | Decisions 4 and 5 — the two reference packages | R1-verified (`:1008`) | true |
| `:1011` | Decision 6 — raise at finalization naming source model, field, and target model | `types/finalizer.py::_format_unresolved_targets_error` — `{source_model.__name__}.{field_name} -> {related_model.__name__}` | true |
| `:1015` | plain `strawberry.Schema` fully supported | R1-verified | true |
| `:1018` | `Meta.primary`: duplicate-primary and flipped-primary rejected **at registration**; ambiguity-by-omission caught **at finalization** | `registry.py::TypeRegistry.register` (two `ConfigurationError` raises); `types/finalizer.py::_audit_primary_ambiguity` (Phase 1) + `::_format_ambiguity_error`; `docs/SPECS/spec-018-meta_primary-0_0_6.md` | true |
| `:1021` | sentinel redaction stays optional | — | judgement |
| `:1024` | filters and orders shipped in `0.0.8`; their specs own the naming decisions | `docs/SPECS/spec-027-filters-0_0_8.md`, `spec-028-orders-0_0_8.md` (both exist) | true |
| `:1027-1039` | the eleven success criteria, three annotated `owed` | R1-verified (`:1034-1036`) | true |
| `:1041-1049` | the avoid-list and the end-state framing | — | judgement |

### Enumeration table — link and structural surface

| Site | Clause asserts | Symbol opened | Verdict |
|---|---|---|---|
| `:1051-1096` | the link-definition block: 25 defs, all resolving | scripted def/use audit — **25 / 25**, 0 missing, 0 orphan, 0 dead target | true |
| `### Layer 1`-`11`, `### Phase 1`-`8`, `### Decision 1`-`6` | numbering complete and un-renumbered | `grep -oE` over the current file — 11 / 8 / 6, in order, no gap | true |
| five cross-spec anchors | resolve in both directions | `spec-010:67` → #"### Layer 3: Finalization trigger", `spec-010:468` → #"### Decision 6: fail loudly" (`grep -c` on spec-009 → **1** each); `spec-009:99` / `:634` / `:870` → spec-010's #"### Must redo (not augment)" / #"## Strawberry finalization strategy" / #"### Unresolved-target error format" (`grep -c` → **1** each) | true |

### The four findings, in the order the file presents them

**1. `:394` — a `Benefits:` bullet claiming a capability the audit does not have.** The clause read
"can report exact **unfinalized** or unresolved fields". `check_schema` walks the `DjangoType`s
reachable from a **built** schema and returns one warning per exposed relation whose target model has no
registered `DjangoType`. "Unfinalized" is not a state it can observe — a type reachable from a built
schema has been through Phase 3 by construction — so the clause is not a missing feature but a category
error. **Narrowed rather than cut**, because the surviving half is the reason the definition object is
worth having, is verifiable from the linked glossary entry (which names the reported condition exactly),
and is the bullet's only use of `[glossary-schema-audit]`: cutting it would have dropped the spec's
glossary term count from 23 to 22 and orphaned a link definition.

**2. `:610` — a sketch comment asserting a mirror it is not.** `Literal["forward_single", "many",
"reverse_one_to_one"]  # mirrors utils.relations.RelationKind`, against a five-member alias. The two
dropped members are `"reverse_many_to_one"` and `"generic"` — the two that decide many-side
classification through `MANY_SIDE_RELATION_KINDS` — so a reader trusting the mirror concludes a
`GenericRelation` has no pending-relation kind at all. **Replaced with the alias name itself** rather
than re-spelled with all five: a re-spelling is true today and false on the next member, and an
enumeration copied out of a `Literal` is a copy no test compares. This is the same membership surface
R1's last finding turned on, and it is the second time this document has stated this set wrongly.

**3-4. `:930` and `:1002` — the visibility seam is not generated, at any cardinality.** One argument,
two sites. Both summarised `### Layer 4`'s four-seam map without its per-seam scoping. The finalizer
does generate the annotation (`types/converters.py::resolved_relation_annotation`, fed
`definition.field_map`) and the resolver (`types/resolvers.py::_attach_relation_resolvers`, Phase 2) for
every exposed relation at every cardinality. It generates **no** visibility composition for any of them:
every `apply_type_visibility_sync` / `_async` call site in the package sits in a field or subsystem that
owns a queryset — `connection.py`, `list_field.py`, `types/relay.py`, `permissions.py`,
`filters/sets.py` — and none sits in `types/finalizer.py` or `types/resolvers.py`. A **forward single**
relation reaches none of them; neither does a many-side relation under
`Meta.relation_shapes = {"<field>": "list"}`, because `types/finalizer.py::_synthesize_relation_connections`
attaches the visibility-composing pipeline only for a many-side relation whose target is
Relay-Node-shaped, under the `"connection"` / `"both"` shapes. `:1002`'s "arguments" fails on the same
boundary: the sidecar `filter:` / `order_by:` arguments arrive with the synthesized connection or not at
all.

`:930` was **cut** to the two seams the finalizer does generate — its `— Layer 4` pointer already
carried a reader to the scoped statement. `:1002` was **replaced**, because "generated field behavior
belongs to the finalizer" is the decision's whole title and a bare cut would have left two seams
unaccounted for exactly where a reader expects the full map; it now names the queryset-owning field as
their owner and points at `` `### Layer 4: Generated relation fields` ``, reusing the code-span heading
citation the spec already uses at `:415`.

**Why these two were reversed from R1's judgement, stated so the reversal is auditable rather than
silent.** R1 judged them non-findings on three grounds. Two of them hold and are why the remedies are
small: they restate an accepted map, and the scoped truth is one explicit pointer away. The third —
"neither names a symbol" — is what decided it here, in the other direction. An unscoped absolute over a
**row-level visibility** boundary reads as a security property, and "names no symbol" is not protection
when the sentence's subject is the finalizer and the entire document is about what the finalizer
generates. The direction of the error is fail-open: a reader who believes visibility composition is
generated for every cardinality concludes a forward FK is row-filtered when nothing filters it. This is
also the shape Worker 1's memory flags in one line — **an absolute over "every cardinality" or "every
path" in this package is false by construction, because Phase 2.5 re-shapes what Phase 2 attached** —
and `:930` says "across every cardinality" literally.

### Answering the split question (`BUILD.md` `### Slice splitting`) — required, and the answer is no

The remediation set is **four single-line edits in one document plus three append-only rationale
entries**: `git diff --numstat` moves from R1's `112 / 170` to `114 / 172` on the spec, i.e. **two
added and two deleted lines** beyond what the reviewer had already read, and `572 / 0` on the rationale.
That is a smaller diff than any prior pass on this cycle, and every hunk is independently checkable
against one named symbol.

The **boundary count is zero** — this item introduces no guard, cap, rejection path, or validation
branch, and writes no code — so the second trigger does not fire either. The three corrections are also
not separable in the way a split would need: `:930` and `:1002` are literally one argument told twice,
and splitting them would recreate the half-current/half-stale state that R1's single-ownership decision
exists to prevent.

**No split. Recommended.** The one thing that *would* have justified one — an unbounded remediation set
— did not materialise, and the reason is recorded above under the denominator: pre-existing prescriptive
text offers the defect class far less to attach to than a fix pass's connective tissue does.

### Spec changes made (Worker 1 only)

Four edits, all in `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`; two cuts and two
replacements. No renumbering, no heading text changed, no section added or removed.

Byte deltas were **measured per edit** rather than estimated, and their sum is checked against the
file's own before/after byte count.

1. **`:394`** — replaced `can report exact unfinalized or unresolved fields` with `can name the exact
   relation fields whose target model has no registered type`. Reason: `check_schema` cannot observe an
   unfinalized field; the replacement is `check_schema`'s own reported condition, verifiable from the
   glossary entry the bullet already links. **89 → 116 bytes, +27.**
2. **`:610`** — replaced `relation_kind: Literal["forward_single", "many", "reverse_one_to_one"]  #
   mirrors utils.relations.RelationKind` with `relation_kind: RelationKind  # the alias in
   utils.relations, five members`. Reason: the alias has five members and the comment asserted a mirror;
   naming the alias is drift-proof where an inline enumeration is not. **114 → 77 bytes, −37.**
3. **`:930`** — cut the visibility item from Phase 3's generation list:
   `the annotation, resolver, and visibility composition` → `the annotation and resolver`. Reason: the
   finalizer generates no visibility composition at any cardinality; the bullet's `— Layer 4` pointer
   already carries the scoped statement. **144 → 119 bytes, −25.**
4. **`:1002`** — cut `, visibility composition, and arguments` from Decision 3's generation list and
   added `; the visibility and argument seams belong to whichever field owns the queryset, per
   \`### Layer 4: Generated relation fields\``. Reason: same over-claim; replaced rather than cut so
   Decision 3 still accounts for all four seams, with the two it does not own attributed to the section
   that owns the map. **266 → 355 bytes, +89.**

`+27 − 37 − 25 + 89 = +54`, which closes exactly against the spec's **61,082 → 61,136** byte ledger.

No prior checklist box changed: R1's sixteen `- [x]` boxes are in R1's artifact and none of their
contracts is touched — D10's sketch correction, D15's Phase 3 restatement and the Decision-3 repurpose
all survive intact, and each of the four edits above narrows a claim rather than reversing one.

### Rationale changes (append-only, this cycle's constraint)

Three entries appended to `## Entries keyed to the spec`, immediately before `## Standing notes`, each
naming the spec section by heading:

1. `` ### `### Layer 2: Pending relation registry` — a sketch comment claiming a mirror it was not ``
2. ``` ### ``### Borrow `StrawberryDjangoDefinition` `` — a benefit the schema audit cannot deliver ```
3. `` ### `### Phase 3: Generated relation fields` and `### Decision 3: generated field behavior belongs to the finalizer` — the visibility seam is not generated for every cardinality ``

Each carries what was cut or replaced, why, a `may no longer claim` note where a decision lost a claim,
and the rejected alternative with the reason it lost. The pre-existing `## Standing notes` "three sites"
bullet is **still deliberately untouched** — correcting it would break append-only, and R1's own note
five lines above it already states the staleness.

### Gates, proofs and ledger — all run this pass

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0, 23 terms** —
  unchanged, which is the point of narrowing `:394` rather than cutting it.
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0** for both.
- **Link / anchor / rule-27 audit** (fenced blocks stripped, definition lines excluded from the use
  scan, target existence checked on disk): spec **25 defs / 25 uses, 0 missing, 0 orphan, 0 dead
  target**; rationale **11 / 11, 0 / 0 / 0**. **0** `](#…)` in-page anchors in either file, so none can
  dangle. **0** in-repo raw `path:NN` in either document (`grep -nE
  '[A-Za-z0-9_/.-]+\.(py|md):[0-9]+'` with `file:///` excluded → no match).
- **No renumbering.** `### Layer 1`-`### Layer 11` (11, in order, no gap); `### Phase 1`-`### Phase 8`
  (8, no gap); `### Decision 1`-`### Decision 6` (6, no gap). The two vacated slots R1 repurposed still
  carry positive contracts.
- **Cross-spec anchors: five, both directions, re-derived 2026-08-16 at the moment of dependence** —
  `spec-010` is under a concurrent cycle and may retitle a heading between passes. All ten `grep -c`
  readings are **1**. Nothing was repaired; nothing needed to be.
- **Ledger.** Spec **61,082 → 61,136 bytes**, **1,096 → 1,096 lines** (four single-line replacements).
  `git diff --numstat` against HEAD: spec **114 / 172**, rationale **572 / 0**. HEAD's own copies
  (`git show HEAD:<path>` into an out-of-repo scratch path) measure **54,232 / 1,154** and
  **12,273 / 208**. Both identities close: `1,154 − 172 + 114 = 1,096` and `208 + 572 = 780`.
  Rationale **51,082 → 56,461 bytes**, **710 → 780 lines**.
- **Append-only re-proved on the rationale.** `git diff -- <rationale> | grep -c '^-'` → **1**, and
  printing it shows the `--- a/…` header — no HEAD line deleted **or modified**. `git diff -U0` hunks
  are `@@ -166,0 +167,570 @@`, `@@ -185,0 +756 @@`, `@@ -186,0 +758 @@`; `570 + 1 + 1 = 572` closes
  against `--numstat`. `head -166` of the working file `cmp`s **exit 0** against `head -166` of HEAD's
  copy (HEAD's file is 208 lines, so the prefix is a real prefix). The two single-line hunks are R1's
  alphabetical link-definition insertions, unchanged by this pass.
- **Provenance: nothing was swept into a concurrent commit.** `git log --stat` over both document paths
  → the newest commit touching either is still **`f3c94642`**, unchanged although HEAD moved to
  `973d00b2` this pass. `git show HEAD:` re-measures the HEAD figures above — the second, independent
  proof. Both files are ` M`; this artifact is `??`. Verified with `git log --stat` plus `git show
  HEAD:`, never `git status` alone.
- **No source, tests, or third file touched.** The diff is two `.md` files plus this artifact. No
  `pytest` was run in this pass at all, with or without `--cov*` flags. The temp test under
  `docs/builder/temp-tests/r1/` was not modified, moved, or deleted.

### Notes for Worker 3 (audit)

- **The reversal at `:930` / `:1002` is the one judgement call worth re-deriving from scratch.** R1's
  final verification examined both and judged them non-findings; this pass reverses that on the
  fail-open direction of a visibility claim. The evidence is one `grep` — every
  `apply_type_visibility_sync` / `_async` call site in the package — plus
  `types/finalizer.py::_synthesize_relation_connections`'s eligibility gate. If the reversal is wrong,
  the remedy is a revert of two edits, not a re-plan.
- **The `:394` narrowing is the only edit whose replacement text makes a new positive claim.** It
  should be checked against `check_schema`'s body and the `## Schema audit` glossary entry, which state
  the same condition in the same words.
- **`:610` deliberately does not enumerate.** If a reviewer prefers the five members spelled out, the
  rejected alternative and its reason are in the rationale entry; that is a preference, not a defect.
- The denominator's bucket counts were produced by parsing the tables, not by reading them. The parser
  rule is stated under `### Denominator` and re-derives in one command.

### Notes for Worker 1 (spec reconciliation)

- **R1's escalations 1-5 and 8-10 are unchanged and none was repaired here** — all sit outside this
  cycle's writable set. Escalation 8 (no permanent-suite row pins `async def get_queryset` →
  `SyncMisuseError` for a *default* `DjangoConnectionField` under `await schema.execute`) is still the
  only one whose evidence inaction destroys, and the ready-made body under `docs/builder/temp-tests/r1/`
  still clears with the cycle. **Still recommended for carding.**
- **Escalations 6 and 7 are now discharged**: 6 was `:610` and 7 was `:930` / `:1002`; all three sites
  are corrected above. R1b consumed both inputs rather than rediscovering them, which is what handing
  them forward was for.
- **One observation, reported rather than repaired.** `:592-597` says the registry "should distinguish
  registered but unfinalized types" from finalized ones. `registry.py` carries a **registry-global**
  `is_finalized` flag, not a per-type one; per-type state lives on
  `types/definition.py::DjangoTypeDefinition.finalized`. The prescription is satisfied across the two
  objects, so it is not a false clause — but a future pass tightening that sentence should say which
  object holds which half.

### Status

`planned`. Four false clauses found and fixed, the denominator reported from parsed tables, and the
split question answered in writing (no split). Worker 0 reads `planned` on this artifact as "dispatch
Worker 3", per the build plan's `### Deviation 3`.

---

## Review (Worker 3)

Run 2026-08-16 by a fresh Worker 3 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-3.md`. **HEAD re-derived: `973d00b2`** (unchanged from the
perform pass's reading). `git status --porcelain` is **125** entries; nothing outside this cycle's
writable set was edited, reverted, or `git checkout`ed, and the HEAD reference throughout is
`git show HEAD:<path>` into an out-of-repo scratch path. No `pytest` was run, with or without `--cov*`.

`### Failability proofs` and `### Hot-path budget` are **not applicable**: this is a documentation pass.
It writes no code, introduces no guard, cap, gate, or rejection path — so there is no boundary meeting
the mandatory re-run floor, and the empty re-run set is legal on that ground — and the plan declared no
hot path.

**Verdict up front.** The four edits are individually correct and the denominator is sound: I re-parsed
the tables and reproduced **103 / 59 / 4 / 55 / 31 / 9 / 4** exactly, and each of the four corrected
spec lines now says something true at the symbol it names. The reversal at `:930` / `:1002` is right in
its *conclusion* — the finalizer generates no visibility composition — and **wrong in the mechanism it
gives for that conclusion**, in text that has been appended to the permanent rationale. That is the High
finding. Two further sites of the sweep's own defect class survive: one in the rationale, one at a spec
line the enumeration never opened.

### High:

#### The rationale's visibility argument states three false mechanism claims on a row-visibility boundary

`docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md:706-715` (entry
`### \`### Phase 3: Generated relation fields\` and \`### Decision 3: ...\``), and the same three claims
in this artifact at `:290-299` and `:311-318`.

The conclusion is correct and I verified it independently: `grep -c apply_type_visibility` returns **0**
in both `types/finalizer.py` and `types/resolvers.py`, and `types/resolvers.py::_make_relation_resolver`
generates three shapes (`many_resolver`, `reverse_one_to_one_resolver`, `forward_resolver`) that all
return the row-bound accessor with no visibility call. The cut at `:930` and the replacement at `:1002`
are therefore sound and I am not asking for them to be reverted.

The **argument** is not sound. Three claims, in order:

1. *"every `utils/querysets.py::apply_type_visibility_sync` call site in the package sits in a field or
   subsystem that owns a queryset — `connection.py`, `list_field.py`, `types/relay.py`,
   `permissions.py`, `filters/sets.py`"* — the em-dash list is presented as the enumeration of *every*
   call site and it is **five of eight**. Real invocation sites (docstring mentions excluded):

   ```
   grep -rn 'apply_type_visibility_\(sync\|async\)(' django_strawberry_framework/ | grep -v '``'
     2 connection.py   2 filters/sets.py   2 list_field.py   1 mutations/resolvers.py
     1 optimizer/walker.py   1 permissions.py   4 types/relay.py   5 utils/querysets.py
   ```

   The omission that matters is `optimizer/walker.py::_build_child_queryset` — which the **spec's own
   `### Layer 4` visibility bullet names explicitly** (`spec-009:649`: "It runs on the connection
   pipeline, on `list_field.py::DjangoListField`, and on the optimizer's prefetch child
   (`optimizer/walker.py::_build_child_queryset`)"). The rationale entry defending Layer 4's map
   contradicts Layer 4's map.

2. *"A **forward single** relation reaches none of them"* — **false.**
   `optimizer/walker.py::plan_relation` tests `_target_has_custom_get_queryset(target_type)` **before**
   the many-side test and returns `("prefetch", "custom_get_queryset")` for *any* relation, forward FK
   included. `_plan_prefetch_relation` sets `plan.cacheable = False` and does **not** return early
   (the only early return is `django_field.related_model is None`), so it reaches
   `_build_prefetch_child_queryset` → `_build_child_queryset(..., has_custom_qs=True)` →
   `apply_type_visibility_sync(target_type, queryset, info, allow_sliced=True)`. A forward FK whose
   target type overrides `get_queryset` is row-filtered, inside the generated `Prefetch`.

3. *"neither does a many-side relation under `Meta.relation_shapes = {"<field>": "list"}`"* — **false
   for the same reason**, and more directly: `"list"` is the shape that stays on the prefetch path, and
   `many_resolver` reads `_prefetched_objects_cache[accessor_name]`, i.e. exactly the rows the
   visibility-composed child queryset produced.

The gate on all three is `target_type.has_custom_get_queryset()` — which is the only configuration in
which "visibility composition" denotes anything at all, so the exception is not a corner case, it is the
whole case.

**Why this is High rather than a wording nit.** It is a claim about a **row-level visibility /
data-isolation** boundary (`worker-3.md` `### Fail-open shape hunting` severity floor), it now lives in
a permanent document rather than a cycle scratchpad, and it is internally contradicted twice over: by
`spec-009:649` and by this artifact's own enumeration row `:496-504`, which verifies
`optimizer/walker.py::_target_has_custom_get_queryset` → `("prefetch", "custom_get_queryset")` as a
shipped capability and grades it `true`. The direction is the inverse of the one the entry set out to
close — it tells a reader a forward FK is *not* row-filtered when it is — but it is the same defect
class this item exists to remove, written by the fix pass, which is the pattern this cycle has paid for
eight times.

**Recommended change.** In the rationale entry, replace the exhaustive-reading enumeration and the two
"reaches none of them" absolutes with the claim that is actually load-bearing and actually true: *the
generated resolver never composes visibility itself; row-level visibility reaches a relation only
through a queryset-owning seam — the synthesized connection pipeline, the cascade-permission helpers, or
`optimizer/walker.py::_build_child_queryset`'s prefetch child when the target type overrides
`get_queryset`* — and drop the "concludes a forward FK is row-filtered when nothing filters it" clause
from the rejected-alternative paragraph, which asserts the same falsehood as a harm. Cite
`spec-009:649` rather than re-spelling the site list, which is the same
single-ownership rule the `### DRY analysis` applied to `:930` / `:1002` and did not apply to itself.
The rationale is append-only for this cycle, so this is an amendment appended in the same entry's
manner, not an edit of the shipped paragraph — Worker 1 owns which.

### Medium:

#### The rationale repeats the cycle's set-algebra defect on `MANY_SIDE_RELATION_KINDS`

`docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md:673-675`, and this artifact at
`:279-281`: *"the two members it dropped (`"reverse_many_to_one"` and `"generic"`) are **the two** that
decide many-side classification through `utils/relations.py::MANY_SIDE_RELATION_KINDS`."*

```
django_strawberry_framework/utils/relations.py:28
MANY_SIDE_RELATION_KINDS: frozenset[RelationKind] = frozenset(
    {"many", "reverse_many_to_one", "generic"},
)
```

The frozenset has **three** members, and the third — `"many"` — was already present in the sketch the
finding is about. "The two that decide many-side classification" is a false definite description of a
three-member constant. Everything else in the entry is exact (five members correctly enumerated, the
`GenericRelation` harm statement correct), and the remedy chosen is the right one.

This is the **third** time this cycle has stated a relation on this same three-member frozenset with a
member missing: R1 pass 7's finding was a fix-pass sentence that dropped `"generic"` from it, and this
is a fix-pass sentence dropping `"many"` from it. Recommended change: `"reverse_many_to_one"` and
`"generic"` are **two of the three** members of `MANY_SIDE_RELATION_KINDS`, and the sketch's own
`"many"` is the third — which is a stronger version of the same argument, because it says the sketch
enumerated one many-side kind and dropped the other two.

#### `spec-009:417` is an unenumerated third instance of the very restatement `:930` / `:1002` were cut for

```
docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:417
... the `utils/querysets.py::apply_type_visibility_sync` / `apply_type_visibility_async` pair — with
`utils/querysets.py::SyncMisuseError` closing the sync path against an `async def get_queryset` — is
applied by whichever field owns the queryset: `connection.py`, `list_field.py`, `types/relay.py`.
```

Three modules of eight, and a *different* incomplete triple than `### Layer 4` gives four sections
later (`:649` names `connection`, `list_field`, and `optimizer/walker.py`; `:417` names `connection`,
`list_field`, and `types/relay.py`). Neither list is complete and the two disagree with each other
inside one document — the exact half-current/half-stale state the `### DRY analysis` says the
pointer-shrink at `:930` / `:1002` exists to prevent. `:1002`'s new text borrows this line's phrasing
("whichever field owns the queryset"), so the phrase is now load-bearing at two sites while the seam it
names is owned by three subsystems that are not fields.

**How it was missed, which is the auditable part.** I re-derived the enumeration's line coverage
programmatically: the 103 rows' `:NNN` / `:NNN-NNN` sites cover **785 of 1,096 lines**, leaving 95 gaps
totalling 311 lines. Almost all of those are headings, blank lines and fenced-code interiors, and I
scanned every non-blank uncovered line for present-tense package assertions — `:417` is the one that
matters, and it sits inside the largest content gap (`395-421`, 18 non-blank lines). The artifact cites
`:415` twice, so the section was read; line `:417` was never opened.

Scope is genuinely arguable and I am not asserting it: `### Scope` declares R1b's territory as the 984
pre-existing lines plus two routed added-text sites, and `:417` is added text (absent from
`git show HEAD:`), so it is R1's. Against that, `### Maintainer decision 4` says "all 1,096 spec lines",
and the case for the `:930` / `:1002` reversal is precisely that R1's added-text sweep did not catch
this shape. Worker 1 owns the call: fix here, or record the narrowing and card it. What is not
available is leaving it unrecorded, because R1 is `final-accepted` and nothing else in this cycle
re-reads that section.

### Low:

#### Two evidence counts in the enumeration table do not reproduce with the stated command

- Rows `:577-590` and `:892-898`: "`types/base.py` — **0** `strawberry.type(` calls".
  `grep -c "strawberry.type(" django_strawberry_framework/types/base.py` returns **1** —
  `types/base.py:1732`, inside a comment ("Phase 3 ``strawberry.type(...)`` decoration with both the
  synthesized..."). Zero *calls* is correct; the stated count is not.
- Row `:99`: "`registry.py` — `lazy_ref` **0** package-wide". `grep -rn lazy_ref` returns **10** hits,
  all of `mutations/fields.py::_lazy_ref` and its `auth/` callers — a different symbol. `TypeRegistry`
  has no `lazy_ref` and the claim is correct; only a word-boundary or `.lazy_ref` spelling reproduces
  the stated **0**.

Both underlying claims are true and I verified them. The finding is against the count as *evidence*: a
reviewer re-running the printed command gets a different number, which is the property the
report-the-denominator method exists to provide. Recommended change: state the command that produces
the number, or state the count of *calls* rather than occurrences.

#### `:930`'s surviving "across every cardinality" is the absolute R1b's own new rule condemns

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:930` now reads *"Generate the annotation and
resolver for every exposed relation, at finalization, across every cardinality — Layer 4."* The
rationale entry that produced this cut states, as its generalisable lesson, *"an absolute over 'every
cardinality' or 'every path' in this package is false by construction, because Phase 2.5 re-shapes what
Phase 2 attached"* — and then leaves "across every cardinality" standing on the surviving half of the
same sentence.

It is defensible as a Phase-2 statement and I am not calling it false: `_attach_relation_resolvers` does
run for every selected relation. But under the **default** `"connection"` shape,
`types/finalizer.py::_synthesize_relation_connections` then removes both the generated list annotation
and the Phase-2 list resolver ("so the SDL never carries the list form"), so for the commonest many-side
case neither generated seam survives finalization. Recommended change: none required; if Worker 1 wants
the sentence to be true of the *finalized* type rather than of Phase 2, "at Phase 2, before Phase 2.5
re-shapes the many-side default" is the scoping that costs four words. Recorded so a later pass does not
re-open it as new.

### DRY findings

- **The consolidation is the right one and it was applied unevenly.** Shrinking `:930` and `:1002` to
  pointers rather than restating Layer 4's map is correct, and the `### DRY analysis`'s reasoning ("a
  duplicated map has no correct state — only a current half and a stale half") is exactly right. The
  same pass then wrote a *fourth* copy of that map into the rationale (High finding 1) and left a
  *third* copy in the spec at `:417` (Medium finding 2). Post-pass the map exists at `:417`, `:649`,
  `:1002` (as a pointer) and rationale `:708`, and three of the four spellings disagree. One canonical
  telling — `### Layer 4` — plus pointers is the shape; the site list belongs nowhere else.
- **No new vocabulary, constant, convention, or indirection is introduced**, so the existence challenge
  does not arise on this item. `### DRY analysis`'s "helper inventory not applicable in the code sense"
  is the honest reading, not an evasion.
- Enumeration-table row `:496-504` grades six optimizer capabilities `true` in one row; I re-opened
  `_target_has_custom_get_queryset` and `plans.py::diff_plan_for_queryset` and both hold. The row is
  dense but not padded.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**. `__all__` and the re-export list are
unchanged. This item touches no Python file at all: the working-tree diff for its writable set is two
`.md` files plus this artifact.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applies — the item's entire deliverable is documentation. All gates re-run rather than trusted; byte and
`shasum` measured **before and after** each gate run, since `--check` scripts touch mtimes.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0, 23 terms.** The
  count is unchanged, which is the whole point of narrowing `:394` rather than cutting it: the bullet is
  the only user of `[glossary-schema-audit]`, and I confirmed that independently (one use, one def).
- `uv run python scripts/check_trailing_commas.py --check` on both files → **exit 0**. `shasum -a 256`
  identical before and after both gate runs; `wc -c -l` unchanged.
- **Link audit, code spans NOT stripped** (stripping is what manufactures the orphan false positive):
  spec **25 defs / 25 uses**, rationale **11 / 11**; 0 missing, 0 orphan, 0 dead target on disk.
- **0** `](#` in-page anchors in either file, so none can dangle. **0** in-repo raw `path:NN` in either
  document (`grep -nE '[A-Za-z0-9_/.-]+\.(py|md):[0-9]+'` less `file:///`).
- **No renumbering.** `### Layer 1`-`11`, `### Phase 1`-`8`, `### Decision 1`-`6`: each appears exactly
  once, in file order, no gap and no duplicate.
- **Five cross-spec anchors, both directions, re-derived at this moment** (spec-010 is under a
  concurrent cycle): `spec-010:67` → `### Layer 3: Finalization trigger`, `spec-010:468` →
  `### Decision 6: fail loudly`, and `spec-009:99` / `:634` / `:870` → spec-010's
  `### Must redo (not augment)` / `## Strawberry finalization strategy` /
  `### Unresolved-target error format`. All ten `grep -c` readings are **1**. Nothing repaired, nothing
  needing repair.
- **Ledger, re-measured independently.** Spec **61,136 bytes / 1,096 lines**; rationale **56,461 /
  780**. `git show HEAD:` copies **54,232 / 1,154** and **12,273 / 208**. `--numstat` **114 / 172** and
  **572 / 0**. Both identities close: `1,154 − 172 + 114 = 1,096`, `208 + 572 = 780`.
- **Per-edit byte deltas verified against the files, not accepted from the report.** Current lines
  measure 116 / 77 / 119 / 355 bytes at `:394` / `:610` / `:930` / `:1002`; HEAD's corresponding lines
  measure 89 (`head:393`) and 114 (`head:651`) for the two pre-existing sites. `+27 − 37 − 25 + 89 =
  +54`, and `61,082 + 54 = 61,136`. The spec's `114 / 172` (vs R1's `112 / 170`) is consistent with
  exactly two of the four edits landing on lines R1 had already added.
- **Append-only proved the strong way.** `git diff -- <rationale> | grep -c '^-'` → **1**, and it is the
  `--- a/…` header, so no HEAD line was deleted **or modified**. `-U0` hunks
  `@@ -166,0 +167,570 @@`, `@@ -185,0 +756 @@`, `@@ -186,0 +758 @@` sum `570 + 1 + 1 = 572` against
  `--numstat`. `head -166` of the working file `cmp`s **exit 0** against `head -166` of HEAD's copy
  (HEAD is 208 lines, so the prefix is real).
- **Provenance.** `git log --stat` over both document paths: newest commit touching either is still
  `f3c94642`, with HEAD at `973d00b2`. Nothing was swept into a concurrent commit. Verified with
  `git log --stat` plus `git show HEAD:`, never `git status` alone.
- **`### Dispatched findings checklist` audited box by box.** Four boxes, four edits, one-to-one: `:610`
  → edit 2, `:394` → edit 1, `:930` → edit 3, `:1002` → edit 4. No box without an edit, no edit without
  a box, and each box's quoted defect text matches HEAD's line character-for-character where it quotes
  one.
- **Scope boundaries respected.** `## The 0.0.4 local package baseline` (`:83-95`, `:100-116`) is
  byte-unchanged; neither "retired since" marker was modernised and both are still enumerated as claims
  about today (rows `:96`, `:99`). No `file:///` citation was touched. No forward design prescription
  was cut as though it were a mechanism claim — the four edits are the only content changes in the file,
  and all four are inside present-tense assertions.

### What looks solid

- **The denominator reproduces exactly.** Parsing the tables myself (a row is a `|`-leading line that is
  neither header nor rule; bucket on the last cell) gives **103** rows: 54 `true` + 1 `true (all six)` =
  **55**; **4** FALSE (1 NARROWED, 1 CUT, 2 REPLACED); **31** `judgement`; **9** `note (upstream)`;
  3 `out of scope` + 1 `out of scope (deliberately historical)` = **4**. `55 + 4 + 31 + 9 + 4 = 103`,
  opened `= 59`. Every figure in `### Denominator` is right, and this is the first pass on this cycle
  whose stated counts survived a mechanical recount unchanged.
- **The two unopenable buckets hold up under scrutiny.** I read all 31 `judgement` sites and all 9
  `note (upstream)` sites. The `judgement` rows are goals (`:74-78`), normative rules (`:872`,
  `:800`), prescriptions (`:355-362`, `:823-840`), open design points (`:793-797`, `:1021`) and
  unshipped-work designs (`:736-766`, `:773-781`, `:964-974`) — none asserts present-tense package
  behavior. The 9 upstream notes are all prior-art descriptions the dispatch puts out of scope; the
  four upstream claims cheap enough to open (`:280`, `:387`, `:422`, `:479`) were promoted to `true`
  rather than parked, which is the correct direction. The only quibble is `:196-206`, whose opening
  sentence describes upstream BFS factories and would read better as `note (upstream)` — both buckets
  are out of scope for cutting, so nothing turns on it.
- **`:394` is the strongest of the four edits.** `check_schema` (`optimizer/extension.py:1265-1312`)
  walks `_collect_schema_reachable_types(schema)` and emits exactly one warning shape —
  `"{type_cls.__name__} ({model.__name__}.{field_name}) has no registered target DjangoType"`. The
  replacement text is that condition in the glossary's own words (`docs/GLOSSARY.md` `## Schema audit`),
  nothing true was lost, and "unfinalized" is genuinely unobservable from a built schema. The narrowing
  preserves the sole `[glossary-schema-audit]` use, which is what keeps the term count at 23.
- **`:610` is correct and the reasoning is the right shape.** `utils/relations.py:21-26` is a five-member
  `TypeAlias`; the sketch named three and claimed a mirror. Naming the alias instead of re-spelling it
  is the drift-proof choice, and the rejected alternative is recorded rather than assumed.
- **The reversal's conclusion is right and its remedies are minimal.** Both corrected sentences say
  something true, `:1002` keeps Decision 3 accounting for all four seams instead of leaving two
  unattributed, and neither edit touches a heading, a number or an anchor.
- **The split answer is correct.** Four single-line edits, zero new boundaries, and `:930` / `:1002`
  are one argument told twice — splitting them would recreate the half-current/half-stale state the
  item is trying to remove. Answered in writing before it could become a default.
- **Four findings in 984 lines is a plausible yield, not a thin one.** I sampled `true` rows chosen for
  being least likely to have been read carefully — `:150-159` (`ALLOWED_META_KEYS`), `:189-194`
  (`RelatedAggregate` absent: 0 hits package-wide), `:295` / `:99` (pending-relation API present:
  `add_pending_relation` / `iter_pending_relations` / `discard_pending` at `registry.py:508/513/526`),
  `:592-597`, `:802-809` (`DST_OPTIMIZER_FK_ID_ELISIONS`), `:844-846` / `:870`
  (`ConfigurationError(_format_unresolved_targets_error(...))` at `finalizer.py:771`, formatting
  `{source_model}.{field_name} -> {related_model}`), `:877-888` (module layout, `types/relations.py`
  present, `aggregates/` and `fieldset/` correctly marked carded), `:996` and `:1018`. Every one held.
- **The `:592-597` observation was reported rather than repaired**, correctly: the registry-global
  `is_finalized` plus per-type `DjangoTypeDefinition.finalized` do satisfy the prescription across two
  objects, so it is not a false clause. Both symbols confirmed present.

### Temp test verification

No temp tests were written for this review. Every claim under audit is a statement about static source,
so the verification instrument is reading plus `grep`, not execution; running the suite would have
proved nothing about a documentation edit.

`docs/builder/temp-tests/r1/test_async_execution_default_connection.py` (R1's escalation-8 body) was
**not** modified, moved, re-run, or deleted — `ls -la` shows it unchanged at its 20:42 mtime, older than
this cycle's later passes. `docs/builder/temp-tests/r1b/` was never created; nothing needed it.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: High finding 1 needs your call on how an append-only file gets an amendment.** The
  rationale is append-only for this cycle and the defective sentences are inside an entry this pass
  appended. Resolution paths: (a) append a corrective paragraph to the same entry naming the three
  claims and giving the true mechanism — cheapest, keeps append-only literally intact, leaves a wrong
  sentence readable above the correction; (b) treat the entry as this cycle's own output rather than
  inherited text and rewrite the three claims in place, since append-only exists to protect *pre-cycle*
  content and R1's own ledger already distinguishes the two; (c) leave the argument and card it. I
  recommend (b) and consider (c) unsafe: a false mechanism claim about a row-visibility boundary,
  contradicting the spec section it defends, is not something to ship on the argument that the
  conclusion it supports is right.
- **Escalated: Medium finding 2 (`spec-009:417`) is a scope question only you can settle.** `### Scope`
  narrowed R1b to the 984 pre-existing lines; `### Maintainer decision 4` says "all 1,096 spec lines".
  The site is R1's added text and R1 is `final-accepted`. Either fix it here — it is a one-line
  pointer-shrink identical in shape to the `:1002` remedy already made — or record the narrowing
  explicitly and card it. Do not let it fall between the two items.
- **The line-coverage figure is worth carrying into R2 and R4 as an instrument.** The tables cover
  785 of 1,096 lines in 103 rows; the residue is 95 gaps / 311 lines, overwhelmingly headings, blanks
  and fence interiors, but `395-421` is 18 non-blank lines and is where `:417` hid. A sweep that
  reports its denominator should also report its **line coverage**, because the bucket counts cannot
  see a site that was never enumerated — which is precisely how `:930` / `:1002` survived R1.
- **R1's escalations 1-5 and 8-10 remain open and none was touched here**; escalation 8's evidence is
  still the only one that inaction destroys, and the ready-made body still clears with the cycle. The
  `### Notes for Worker 1` account of escalations 6 and 7 being discharged by `:610` and `:930` /
  `:1002` is accurate — I checked all three sites.
- Low finding 2 (`:930`'s surviving "across every cardinality") is recorded as **examined and not
  raised as a defect** so a later pass does not re-open it as new.

### Review outcome

`revision-needed`. One High and two Medium findings, none of them in the four spec edits themselves —
the edits stand, the denominator stands, the gates all pass, and the split answer is right. What does
not stand is the argument that was appended to the permanent rationale to justify the reversal: it
enumerates five of eight visibility call sites as though exhaustive, omits the one site the spec's own
`### Layer 4` bullet names, and twice asserts that a relation reaches no visibility seam when the
optimizer's prefetch downgrade composes visibility onto exactly those relations. Fix the argument, not
the conclusion.

---

## Build report (Worker 1, apply-changes pass)

Run 2026-08-16 by a fresh Worker 1 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-1.md`. **HEAD re-derived: `973d00b2`** (unchanged from the
review pass's reading; `git rev-parse --short HEAD` run at the start of this pass, not inherited from the
dispatch). This is the apply-changes pass, which is Worker 1's on this item per the build plan's
`### Deviation 3` corollary. No `pytest` was run, with or without `--cov*`. `git stash` / `checkout` /
`restore` / `worktree` were not used; every HEAD reference is `git show HEAD:<path>` into a scratch path
outside the repository. Nothing outside this cycle's writable set was edited or reverted, and nothing
under `docs/builder/temp-tests/` was touched.

**Spec status-line re-verification (per-spawn duty).** Lines 1-5 re-read. The opener describes the
rationale companion, the four finalization sites, and the six scrubbed mechanisms. None of the six
corrections below falsifies any of it. **No edit owed.**

### Method this pass: name the symbol, open it, quote what was found

Three of this item's corrections have themselves been false (R1's `:385`, R1's `:418`, and the reversal's
argument), always the same way: the writer verified the *rule* and asserted a *mechanism* around it from
memory. So every clause written this pass names a symbol, that symbol was opened, and the finding is
quoted below. Where a complete enumeration was needed it was **produced mechanically and the command's
output pasted**, never typed from memory — three of the four findings this pass closes are miscounted
enumerations.

#### Enumeration 1 — every module that invokes the visibility pair

```
$ grep -rn 'apply_type_visibility_\(sync\|async\)(' django_strawberry_framework/ \
    | awk -F: '{print $1}' | sort | uniq -c
   2 django_strawberry_framework/connection.py
   2 django_strawberry_framework/filters/sets.py
   2 django_strawberry_framework/list_field.py
   1 django_strawberry_framework/mutations/resolvers.py
   1 django_strawberry_framework/optimizer/walker.py
   1 django_strawberry_framework/permissions.py
   4 django_strawberry_framework/types/relay.py
   5 django_strawberry_framework/utils/querysets.py
```

**Eight modules.** The rationale's list named five, and the omitted `optimizer/walker.py` is the one the
spec's own `### Layer 4` visibility bullet names explicitly. (`utils/querysets.py`'s five are the two
`def` lines plus three internal delegations; the other seven are external invocations.)

```
$ grep -c apply_type_visibility django_strawberry_framework/types/finalizer.py \
    django_strawberry_framework/types/resolvers.py
django_strawberry_framework/types/finalizer.py:0
django_strawberry_framework/types/resolvers.py:0
```

The **conclusion** the four spec edits rest on is therefore intact and none of them was weakened: the
finalizer composes no visibility.

#### Enumeration 2 — the frozenset, quoted

```
django_strawberry_framework/utils/relations.py
RelationKind: TypeAlias = Literal[
    "many",
    "reverse_many_to_one",
    "reverse_one_to_one",
    "forward_single",
    "generic",
]

MANY_SIDE_RELATION_KINDS: frozenset[RelationKind] = frozenset(
    {"many", "reverse_many_to_one", "generic"},
)
```

**Three** members, not two. The third, `"many"`, was already present in the sketch the finding is about.
This is the third time this cycle has stated a relation on this constant with a member missing (R1 pass 7
dropped `"generic"`; R1b dropped `"many"`), which is why the remedy is a **quotation** rather than a
restatement.

#### Mechanism — a forward FK to a custom-`get_queryset` target IS row-filtered

Worker 3's High is **confirmed**, re-derived here rather than accepted. Opened, in call order:

```
django_strawberry_framework/optimizer/walker.py::plan_relation
    if _target_has_custom_get_queryset(target_type):
        ...
        return ("prefetch", "custom_get_queryset")
    if is_many_side_relation_kind(relation_kind(field)):
        return ("prefetch", "default")
    return ("select", "default")
```

The custom-`get_queryset` test runs **before** the many-side test, so it fires for any relation shape,
forward FK included. `_walk_selections` dispatches on that verdict
(`prefer_prefetch=relation_plan_kind == "prefetch"`), and `_plan_prefetch_relation`'s only early return
is `if django_field.related_model is None:` — so the downgrade reaches:

```
django_strawberry_framework/optimizer/walker.py::_build_child_queryset
    queryset = field.related_model._default_manager.all()
    if has_custom_qs:
        ...
        queryset = apply_type_visibility_sync(target_type, queryset, info, allow_sliced=True)
    return queryset
```

Two conditions gate it, and naming them is what makes the corrected claim checkable rather than another
absolute: **(a)** the target type overrides `get_queryset`
(`types/base.py::DjangoType.has_custom_get_queryset`, a constant-time read of the
`__init_subclass__`-set flag), and **(b)** the optimizer extension is installed —
`walker.plan_optimizations` is imported by `optimizer/extension.py` and by nothing else, so a plain
`strawberry.Schema` without `DjangoOptimizerExtension` never runs the walk. That second condition is the
one the corrected rejected-alternative paragraph now states as the real harm.

The `"list"`-shape claim fails for the same reason plus a more direct one:
`types/finalizer.py::_synthesize_relation_connections`'s docstring records `"list"` as *"synthesize
nothing"*, which leaves the relation on the prefetch path whose child queryset `_build_child_queryset`
just composed.

### Closing the enumeration gap: `395-421`, opened and graded

Worker 3's Medium 2 is right that the miss was a **region**, not a line: the prior tables' sites cover
`739` of the spec's 1,096 lines in their 100 spec rows (plus 46 more from the link table's
`:1051-1096`, giving the reviewer's `785`), and `395-421` was 18 non-blank lines never opened although
the report cites `:415` twice. Every non-blank line in that region is now a row.

| Site | Clause asserts | Symbol opened | Verdict |
|---|---|---|---|
| `:396-397` | definition-order independence intersects postponed annotations; neither is solved by walking the annotation namespace twice | — | judgement |
| `:399`, `:403` | the `Required behavior:` preamble, and "keep provenance one system" | — | judgement |
| `:401` | provenance is recorded at collection time, and the override validators plus `_build_annotations` read **one** union rather than re-deriving it | `types/base.py::DjangoType.__init_subclass__` #"consumer_authored_fields = frozenset("; `types/definition.py::DjangoTypeDefinition` (five provenance frozensets); `types/base.py::_build_annotations` — the one union is threaded to all five readers | true |
| `:402` | postponed annotations are resolved by deferring `strawberry.type` to finalization | `types/base.py` — **0** `strawberry.type(` invocations; `types/finalizer.py` Phase 3 performs it | true |
| `:405-406`, `:408-413` | borrow the six behaviors upstream's field classes encode, not the class | upstream `fields/base.py` / `fields/field.py` | note (upstream) |
| `:415` | upstream binds all six to one field class; `### Layer 4` "states that seam map once; it is **not repeated here**" | `### Layer 4` (four bullets, `:647-650`) and `:417` two lines below | true — **restored by this pass's `:417` fix**; the second clause was falsified by the line directly beneath it |
| **`:417`** | **the visibility pair "is applied by whichever field owns the queryset: `connection.py`, `list_field.py`, `types/relay.py`"** | **Enumeration 1 above — 3 of 8 modules, and a different incomplete triple than `### Layer 4`'s** | **FALSE — REPLACED** |
| `:419` | one object still answers every question: every seam reads `DjangoTypeDefinition` rather than a private copy | annotation — `types/finalizer.py` #"resolved_relation_annotation(" is fed `field_meta` off the definition; resolution — `types/resolvers.py` #"definition.field_map.get(field.name)"; visibility — `utils/querysets.py` #"type_cls.__django_strawberry_definition__.model"; arguments — `connection.py` #"definition = target_type.__django_strawberry_definition__" | true (all four) |

**Every other gap of 5+ non-blank lines opened too, because the same argument applies to them.** After
`395-421` the residual map still held five such runs. They are opened here rather than left for a later
pass to rediscover, and the second table below closes the two that carry unenumerated present-tense
assertions:

| Site | Clause asserts | Symbol opened | Verdict |
|---|---|---|---|
| `:68` | node lookup is nullable by contract: dispatch is `required=False` unconditionally, so hidden / missing / uncoercible-pk all resolve to `null` | `relay.py` #"Resolution is **nullable by contract**" — the module docstring states it, and `resolve_node` / `resolve_nodes` dispatch `required=False` at all four sites | true |
| `:70` | three `Meta` keys are deferred and refused at class creation; `ALLOWED_META_KEYS` is the declarable enumeration | `types/base.py::DEFERRED_META_KEYS` = `frozenset({"aggregate_class", "fields_class", "search_fields"})`; `::ALLOWED_META_KEYS` — 17 keys, including the five the sentence names | true |
| `:644-654` | `### Layer 4` itself — the four-seam map every other site now points at | annotation / resolution / visibility / arguments each opened above; `:652`'s "every seam above reads it" is `:419`'s claim and holds; `:654`'s "Phase 2 is the only window" holds against `types/finalizer.py` (Phase 2 attaches, Phase 3 runs `strawberry.type`) | true (all four bullets) |
| `:9-18` | the document's own scope bullets, then `## Target outcome`'s opening | — | judgement |
| `:469-475` | the package exposes `DjangoListField` / `DjangoConnectionField` / `DjangoNodeField`, each a **factory returning a Strawberry field** so no consumer-facing class carries a stacked decorator | `list_field.py::DjangoListField`, `connection.py::DjangoConnectionField`, `relay.py::DjangoNodeField` — all three are module-level `def`s carrying the `# noqa: N802 # PascalCase for graphene-django parity` marker | true |
| `:481-483` | `totalCount` is opt-in per type; every node type resolves through a generated concrete `<TypeName>Connection`; the generic base owns the `first` + `last` guard | `connection.py::_connection_type_for` #"always a generated concrete ``<TypeName>Connection``"; `connection.py::_guard_first_and_last`; the opt-in read from `definition.connection`, never re-parsed from `Meta` | true |
| `:485-490` | the `DjangoConnection(relay.ListConnection[NodeType])` sketch, and that a bare generic **alias** loses the `resolve_connection` override at Strawberry's generic specialization | `connection.py` #"a generic ALIAS handed to the schema loses the ``resolve_connection``"; the concrete class is built at #"f\"{definition.graphql_type_name}Connection\"" | true |
| `:492` | `aggregates` on the connection is still owed and lands through the same generated-subclass mechanism; `TODO-BETA-057-0.1.3` owns it | no `aggregates` member on either connection class; `aggregates/` absent from the package, consistent with the `:736-766` row | true |

**That `### Layer 4` was itself unenumerated is the sharper form of Worker 3's point.** Three sites were
corrected this cycle by pointing at a section no row had ever opened. It holds — but the enumeration had
no way of knowing that, which is the argument for reporting line coverage alongside the bucket counts.

### Revised denominator

| | Prior (perform pass) | This pass | Revised |
|---|---|---|---|
| rows enumerated | 103 | +16 | **119** |
| opened (`true` or `FALSE`) | 59 | +12 | **71** |
| **FALSE** | 4 | +1 (`:417`) | **5** |
| `true` | 55 | +11 | **66** |
| `judgement` | 31 | +3 | **34** |
| `note (upstream)` | 9 | +1 | **10** |
| `out of scope` | 4 | 0 | **4** |

`66 + 5 + 34 + 10 + 4 = 119` ✓, and `opened = 66 + 5 = 71` ✓.

**Line coverage, the instrument Worker 3 asked for.** Prior: **785 / 1,096** (739 from the 100 spec rows,
46 from the link table's `:1051-1096`). Revised: **842 / 1,096**, i.e. **+57 lines** across the sixteen
new rows. Residual: 108 gaps / 254 lines, and **no residual gap now holds five or more non-blank lines**
— the largest holds four. Every figure here was produced by parsing column 1 of every table row for
`:NNN` / `:NNN-NNN`, expanding ranges and unioning; none was counted by eye, which is the discipline both
of this cycle's wrong count sets came from skipping. Re-derivation note: **117** of the 119 rows carry a
`:NNN` site in column 1; the remaining two are the structural table's `### Layer 1`-`11` numbering row and
its five-cross-spec-anchor row, which name headings rather than lines and are `true`. A parser filtering
on "column 1 contains `:NNN`" therefore reports 117 rows / 64 `true`, and both figures reconcile by
adding those two.

### The findings, and what each remedy was

**High — the reversal's argument.** Confirmed and **rewritten in place**, not appended as a correction
beneath a wrong sentence. Worker 3 offered three resolution paths and recommended (b); (b) is what the
dispatch also directs, and it is right: append-only exists to protect **pre-cycle** content, and every
line touched here sits inside an entry this cycle appended (all beyond HEAD's line 166 — see the
append-only proof below). Leaving a false mechanism claim about a row-visibility boundary readable above
its own correction is the outcome the rule was never meant to buy.

What the entry now says, in place of the exhaustive-reading enumeration and the two absolutes: the
finalizer generates annotation and resolver **at finalizer Phase 2** and composes no visibility
(`grep -c` → 0 in both modules, quoted); row-level visibility reaches a relation only through a
queryset-owning seam; **which** seam depends on the relation's shape and on **two named conditions the
finalizer does not control** — the connection-synthesis eligibility gate for the many-side case, and
custom-`get_queryset` **plus** an installed optimizer extension for the prefetch-child case that catches
a forward single relation. `### Layer 4` is cited for the seam list rather than a fourth copy being
written — the single-ownership rule the `### DRY analysis` applied to `:930` / `:1002` and, as Worker 3
observed, did not apply to itself.

The rejected-alternative paragraph's harm clause ("concludes a forward FK is row-filtered when nothing
filters it") asserted the same falsehood as a harm and is **replaced** by the true one: a reader who
believes the finalizer composes visibility for every cardinality stops asking which seam does, and so
never learns that a schema without `DjangoOptimizerExtension`, over a target that does not override
`get_queryset`, is unfiltered on a path the sentence claimed was covered.

**Medium — `spec-009:417`.** Fixed here rather than carded. The dispatch settles the scope question
Worker 3 escalated (`### Maintainer decision 4` reads "all 1,096 spec lines"), and the site is not
merely a third copy: it stands **two lines below** `:415`'s "it is not repeated here", so leaving it
would leave the spec contradicting itself on the page. Remedy is the identical pointer-shrink applied at
`:1002`. Its rationale entry is a **new** entry keyed to
`` ### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField` `` — its own heading rather than a
paragraph folded into the Phase 3 entry, because `BUILD.md` `## Spec rationale extraction` requires an
entry to name the decision it belongs to or it cannot be looked up.

**Medium — the third strike on `MANY_SIDE_RELATION_KINDS`.** Fixed by **quoting the constant** (see
Enumeration 2) rather than restating its membership a fourth time, and by taking Worker 3's stronger
framing: the sketch enumerated **one** many-side kind and dropped the other two.

**Low 1 — the two non-reproducing counts.** Both underlying claims re-verified true and neither document
carries the count, so no document edit is owed; the prior enumeration table is a closed section and was
not edited. The reproducing commands, for the record:
`grep -c 'strawberry\.type(' django_strawberry_framework/types/base.py` → **1**, a comment mention; zero
*invocations* is the true claim and `grep -n` distinguishes them. `grep -rn '\blazy_ref\b'` → 10 hits,
all `mutations/fields.py::_lazy_ref` and its `auth/` callers; `TypeRegistry` has no `lazy_ref`, which is
the true claim, and `grep -rn '\.lazy_ref'` → **0** is the spelling that reproduces it.

**Low 2 — `:930`'s surviving "across every cardinality".** Worker 3 recorded it as examined and required
nothing. **Decided: fix.** The rationale entry that produced the cut states, as its generalisable lesson,
that an absolute over "every cardinality" is false by construction here — and leaving the counterexample
standing in the very sentence that entry produced is the internal contradiction this whole item exists to
remove. The replacement takes `### Layer 4`'s own words ("in the cardinality-correct spelling",
`:647`) rather than introducing `Phase 2.5`, a term this spec never defines and which would collide with
the spec's own `### Phase 1`-`8` migration numbering. The coverage claim the absolute was carrying is not
lost: `### Phase 2` (`:926`) enumerates all five relation shapes and Phase 3's own acceptance list pins
the many-side and reverse-one-to-one outcomes.

**Consequential — `spec-009:1002`.** Its new text said the seams "belong to whichever **field** owns the
queryset", borrowing `:417`'s phrasing. `optimizer/walker.py::_build_child_queryset` is one of the three
seams `### Layer 4` names and is not a field, so the noun over-narrowed. Changed to "the queryset-owning
**components** `### Layer 4: Generated relation fields` names". This narrows nothing in the decision and
was not one of Worker 3's boxes; it is recorded because it is the same defect class, found by re-reading
the fix pass's own new prose.

### Spec changes made (Worker 1 only)

Three edits, all in `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`. No renumbering, no heading
text changed, no section added or removed, and **none of the four prior edits was weakened** — `:394`
and `:610` are byte-unchanged, `:930` and `:1002` were narrowed further, never reverted.

Byte deltas measured per edit against the exact pre-edit line, not estimated.

1. **`:417`** — replaced `is applied by whichever field owns the queryset: \`connection.py\`,
   \`list_field.py\`, \`types/relay.py\`.` with `runs at the queryset-owning seams
   \`### Layer 4: Generated relation fields\` names, never inside the generated resolver.` Reason: three
   of eight invoking modules, a different incomplete triple than `### Layer 4`'s, two lines below `:415`'s
   claim that the map is not repeated here. **472 → 490 bytes, +18.**
2. **`:930`** — `for every exposed relation, at finalization, across every cardinality` →
   `for every exposed relation at finalization, in the cardinality-correct spelling`. Reason: the
   surviving absolute the entry's own rule condemns; the replacement is `### Layer 4`'s own wording.
   **120 → 130 bytes, +10.**
3. **`:1002`** — `belong to whichever field owns the queryset, per
   \`### Layer 4: Generated relation fields\`.` → `belong instead to the queryset-owning components
   \`### Layer 4: Generated relation fields\` names.` Reason: the visibility seam includes
   `optimizer/walker.py::_build_child_queryset`, which is not a field. **356 → 362 bytes, +6.**

`+18 + 10 + 6 = +34`, which closes exactly against the spec's **61,136 → 61,170** byte ledger.

**Prior checklist boxes.** R1's sixteen and R1b's original four are untouched and none of their contracts
is reversed. `:930` and `:1002` were narrowed further in the same direction their boxes recorded.

### Rationale changes

In-place corrections inside entries **this cycle appended**, plus one new entry:

1. `` ### `### Layer 2: Pending relation registry` `` — the `MANY_SIDE_RELATION_KINDS` clause replaced by
   the quoted three-member frozenset and the "two of those three / the sketch's own `"many"` is the
   third" framing.
2. `` ### `### Phase 3 …` and `### Decision 3 …` `` — the three false mechanism claims replaced by the
   `grep -c` evidence plus a two-bullet, condition-naming account of which seam composes visibility for
   which relation shape; the Phase-2 scoping added to the "every cardinality" sentence in the same entry;
   the cut/replaced paragraph updated for the `components`-not-`fields` correction; the
   rejected-alternative harm clause replaced.
3. **New entry** `` ### `### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField` ` `` — the
   `:417` correction, with its own rejected alternative (*complete the list to all eight modules*), lost
   because a copied enumeration rots and because most of the eight are not relation read seams at all.

The pre-existing `## Standing notes` "three sites" bullet is **still deliberately untouched**.

### Gates, proofs and ledger — all re-run this pass

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0, 23 terms.**
- `uv run python scripts/check_trailing_commas.py --check` on both documents → **exit 0**.
- **Link / anchor / rule-27 audit** (code spans NOT stripped, target existence checked on disk): spec
  **25 defs / 25 uses**, rationale **11 / 11**; 0 missing, 0 orphan, 0 dead target. **0** `](#…)` in-page
  anchors in either file, so none can dangle. **0** in-repo raw `path:NN` in either document
  (`grep -nE '[A-Za-z0-9_/.-]+\.(py|md):[0-9]+'` less `file:///` → no match). The new rationale entry
  adds no link definition and needs none.
- **No renumbering.** `### Layer 1`-`11` (11, in order, no gap); `### Phase 1`-`8` (8, no gap);
  `### Decision 1`-`6` (6, no gap), parsed with `^### (Layer|Phase|Decision) N` and compared against the
  expected sequence.
- **Cross-spec anchors: five, both directions, re-derived at the moment of dependence** — `spec-010`
  remains under a concurrent cycle. `spec-009` carries `### Layer 3: Finalization trigger` and
  `### Decision 6: fail loudly` (`grep -c` → 1 each, cited from `spec-010:67` and `:468`); `spec-010`
  carries `### Must redo (not augment)`, `## Strawberry finalization strategy`, and
  `### Unresolved-target error format` (`grep -c` → 1 each). Nothing repaired; nothing needed repair.
- **Ledger.** Spec **61,136 → 61,170 bytes**, **1,096 → 1,096 lines** (three single-line replacements).
  Rationale **56,461 → 60,443 bytes**, **780 → 829 lines**. `git diff --numstat` against HEAD: spec
  **114 / 172**, rationale **621 / 0**. HEAD's own copies (`git show HEAD:` into an out-of-repo scratch
  path) measure **54,232 / 1,154** and **12,273 / 208**. Both identities close:
  `1,154 − 172 + 114 = 1,096` and `208 + 621 = 829`.
- **Append-only re-proved.** `git diff -- <rationale> | grep -c '^-'` → **1**, and printing it shows the
  `--- a/…` header — no HEAD line deleted **or modified**. `git diff -U0` hunks are
  `@@ -166,0 +167,619 @@`, `@@ -185,0 +805 @@`, `@@ -186,0 +807 @@`; `619 + 1 + 1 = 621` closes against
  `--numstat`. `head -166` of the working file `cmp`s **exit 0** against `head -166` of HEAD's copy
  (HEAD's file is 208 lines, so the prefix is real). Every line this pass rewrote sits at 667 or beyond,
  i.e. inside text R1b appended at hunk `+167`.
- **Provenance: nothing was swept into a concurrent commit.** `git log --stat` over both document paths →
  the newest commit touching either is still **`f3c94642`**, with HEAD at `973d00b2`. Verified with
  `git log --stat` plus `git show HEAD:` re-measurement, never `git status` alone.
- **No source, tests, or third file touched.** The diff is two `.md` files plus this artifact. No
  `pytest` was run. `docs/builder/temp-tests/r1/` was not modified, moved, or deleted.

### Notes for Worker 3 (audit)

- **The High's remedy is a rewrite in place, not an appended correction.** If that reading of append-only
  is wrong, the alternative is (a) from your own list and the text is ready to be relocated rather than
  re-derived. The append-only proof above is unchanged in kind: one `-` line, `head -166` `cmp` 0.
- **`:930` and `:1002` were touched a second time.** Neither reverses its first correction; both narrow
  further. The `+34` byte ledger closes per-edit, so a re-measurement will reproduce it exactly.
- **The eight new enumeration rows outside `395-421`** (`:9-18`, `:68`, `:70`, `:469-475`, `:481-483`,
  `:485-490`, `:492`, `:644-654`) are additions beyond the dispatched Medium — they close every remaining
  gap of 5+ non-blank lines. All are graded `true` or `judgement` and change no document text; if you
  disagree with opening them, nothing depends on them but the coverage figure.
- **The revised coverage figure is the one claim here most worth re-deriving**, because it is a count and
  this cycle's counts have been wrong twice. The parser rule: collect every `:NNN` / `:NNN-NNN` from
  column 1 of every table row, expand ranges, union.

### Notes for Worker 1 (spec reconciliation)

- **R1's escalations 1-5 and 8-10 remain open and none was touched here.** Escalation 8 (no permanent-suite
  row pins `async def get_queryset` → `SyncMisuseError` for a *default* `DjangoConnectionField` under
  `await schema.execute`) is still the only one whose evidence inaction destroys; the ready-made body under
  `docs/builder/temp-tests/r1/` still clears with the cycle. **Still recommended for carding.**
- **Carry into R4 as an instrument:** a sweep that reports its denominator should also report its **line
  coverage**, because bucket counts cannot see a site that was never enumerated. `### Layer 4` — the
  section three corrections this cycle point at — had itself never been a row until this pass.
- **`:592-597`'s registry-global `is_finalized` vs per-type `DjangoTypeDefinition.finalized`** remains
  reported-not-repaired, unchanged from the perform pass. Still not a false clause.

### Status

`planned`. One High, two Mediums, and both Lows closed; the four prior spec edits stand unweakened; the
enumeration gap that hid `:417` is opened and the denominator revised to 119 rows / 842 lines covered,
with no residual gap holding five or more non-blank lines.
Worker 0 reads `planned` on this artifact as "dispatch Worker 3", per the build plan's `### Deviation 3`.

---

## Review (Worker 3, pass 2)

Run 2026-08-16 by a fresh Worker 3 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-3.md`. **HEAD re-derived: `973d00b2`** (unchanged from the
apply-changes pass's reading; `git rev-parse HEAD` run at the start of this pass, not inherited).
`git status --porcelain` is **134** entries; nothing outside this cycle's writable set was edited,
reverted, or `git checkout`ed. `git stash` / `checkout` / `restore` / `worktree` were not used; every
HEAD reference is `git show HEAD:<path>` into an out-of-repo scratch path. No `pytest` was run, with or
without `--cov*` flags. Nothing under `docs/builder/temp-tests/` was touched.

`### Failability proofs` and `### Hot-path budget` are **not applicable**: this is a documentation pass.
It writes no code and introduces no guard, cap, gate, or rejection path, so no boundary meets the
mandatory re-run floor and the empty re-run set is legal on that ground; the plan declares no hot path.

**Verdict up front.** The High is closed correctly and I re-derived its whole chain at the symbols rather
than sampling it — every mechanism claim in the rewritten entry holds, including the two gating
conditions, which are stated in the *narrowing* direction ("only when X **and** Y") rather than as the
absolutes that produced the finding. Both Mediums are closed, the two Lows are disposed of, the
`:417` contradiction was real and its remedy is accurate, the frozenset quotation is character-exact,
the four original spec edits stand unweakened, and the widened enumeration reproduces **exactly** under
my own mechanical parse — 119 rows, 66/5/34/10/4, opened 71, 842/1,096 lines, 108 gaps / 254 lines,
largest residual gap 4 non-blank. Three Lows below, all recorded as examined with no build pass required.

### High:

None.

The dispatched High is closed. I re-derived the chain independently, in call order, and every link holds:

- `optimizer/walker.py:178-187` — `plan_relation` tests `_target_has_custom_get_queryset(target_type)`
  and returns `("prefetch", "custom_get_queryset")` **before** the `is_many_side_relation_kind(...)`
  test, so the downgrade fires for any relation shape, forward FK included.
- `optimizer/walker.py:793` — `_plan_prefetch_relation`'s only early return is
  `if django_field.related_model is None:`; every other path reaches
  `_build_prefetch_child_queryset` (`:809`), which calls `_build_child_queryset(...,
  has_custom_qs=has_custom_get_queryset)` (`:871-877`).
- `optimizer/walker.py:374-383` — the `if has_custom_qs:` branch is
  `queryset = apply_type_visibility_sync(target_type, queryset, info, allow_sliced=True)`, quoted in the
  entry character-for-character including `allow_sliced=True`.
- `grep -rn "plan_optimizations" django_strawberry_framework/` — one `import` line,
  `optimizer/extension.py:95`, consumed at `:1184`. `django_strawberry_framework/schema.py` contains
  **0** `DjangoOptimizerExtension` references, so `DjangoSchema` does not auto-install it: condition (b)
  is materially load-bearing, not decorative, and is consistent with `spec-009:1015` ("plain
  `strawberry.Schema` fully supported").
- `types/base.py:712-725` — the default `get_queryset` is an identity hook, so condition (a) is what
  makes "visibility composition" denote anything at all.
- `grep -c apply_type_visibility` on `types/finalizer.py` and `types/resolvers.py` → **0** and **0**, as
  quoted; `types/resolvers.py:341/369/378` are the three named shapes (`many_resolver`,
  `reverse_one_to_one_resolver`, `forward_resolver`) and none composes visibility.
- `types/finalizer.py:475-565` — `_synthesize_relation_connections` gates on `implements_relay_node`,
  many-side, non-consumer-authored, Relay-Node target, and shape; `"list"` synthesizes nothing.
  `types/base.py:111` — `DEFAULT_RELATION_SHAPE = "connection"`, so the entry's "(default)" is right.
  The entry states these as **necessary** conditions ("only for … under …"), which stays true even
  though it does not spell the source-side Node requirement — the safe direction, and the opposite of
  the absolutes it replaced.
- `connection.py:1780` / `:1815` — the connection pipeline does compose visibility, so the many-side
  bullet's premise holds.
- `### Layer 4` is cited rather than re-spelled; no fourth copy of the seam map was written.

The rewrite is in place inside text this cycle appended (every touched line is beyond HEAD's 166), and
the append-only proof below still holds the strong way, so resolution path (b) was legitimately
available.

### Medium:

None.

- **`spec-009:417`.** The contradiction was real: `:415` and `:417` are both absent from
  `git show HEAD:` (R1's added text), `:415` ends "states that seam map once; it is not repeated here",
  and `:417` is the next non-blank line. The remedy — "runs at the queryset-owning seams
  `### Layer 4: Generated relation fields` names, never inside the generated resolver" — is accurate,
  is the same pointer-shrink shape as `:1002`'s, and its rationale entry is keyed to the real spec
  heading (`### Borrow \`StrawberryDjangoFieldBase\` and \`StrawberryDjangoField\``, `spec-009:405`) in
  the double-backtick form the file already uses at its `:452` / `:514` / `:689` entries.
- **`MANY_SIDE_RELATION_KINDS`.** Verified character for character against
  `django_strawberry_framework/utils/relations.py:19-30`: `RelationKind` is the five-member `Literal`
  quoted, and `MANY_SIDE_RELATION_KINDS: frozenset[RelationKind] = frozenset({"many",
  "reverse_many_to_one", "generic"},)` matches the artifact's Enumeration 2 and the rationale's inline
  `frozenset({"many", "reverse_many_to_one", "generic"})` exactly. The "two of those three / the
  sketch's own `"many"` is the third" framing is correct set algebra and is the stronger argument.

### Low:

#### The rejected-alternative harm clause names the configuration in which being unfiltered is harmless

`docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md:757-761`: *"… leaving a schema
built without `DjangoOptimizerExtension`, whose relation target **does not** override `get_queryset`,
unfiltered on a path the sentence claimed was covered."*

The sentence is **true as written** — such a schema is unfiltered, and the old sentence did claim that
path was covered — which is why this is a Low and not a repeat of the closed High. But it is vacuous:
`types/base.py:712-725` makes the default `get_queryset` an identity hook, so a target that does not
override it has no row-visibility rule to lose. The configuration in which the reader's false belief
actually costs something is the **inverse** on condition (a): target **does** override `get_queryset`,
optimizer extension **absent** — then `forward_resolver` returns the row-bound accessor, the prefetch
downgrade never runs, and a consumer-authored visibility rule silently does not reach the relation.
That is the harm the entry's own bullet 2 sets up.

Recommended change: swap the polarity — *"a schema built without `DjangoOptimizerExtension` over a
target that **does** override `get_queryset`"*. **Not required, and no build pass is owed for it:** the
two gating conditions are stated correctly and in full two paragraphs above, so the entry does not
misdescribe the mechanism; only its illustration picks the harmless corner. Recorded as examined so a
later pass does not re-open it as new.

#### Two evidence spellings in the permanent rationale do not reproduce exactly

Both underlying claims are true and I verified them; the finding is against the *evidence*, which is the
property the report-the-denominator method exists to provide.

- `…-rationale.md:765-771` — the parenthetical gives
  `grep -rn 'apply_type_visibility_\(sync\|async\)(' django_strawberry_framework/` as reaching eight
  named modules. Run as spelled it reaches **nine**: it also matches
  `forms/resolvers.py:32`, a docstring mention. "Three of the **eight modules that invoke**" is correct
  — `forms/resolvers.py` never calls the pair — so the defect is that the command reaches a superset of
  the list beside it. One word fixes it (`… reaches, invocations only, …`) or drop the parenthetical and
  keep the claim.
- `…-rationale.md:735-736` — *"`plan_optimizations` is imported by `optimizer/extension.py` and nothing
  else."* True of the package source and that is the load-bearing scope, but three test modules import
  it (`tests/optimizer/test_walker.py:45`, `test_multi_db.py:42`, `test_definition_order.py:9`), and
  `optimizer/walker.py:122` and `optimizer/nested_fetch.py:38` both name "direct / test callers" in
  their own comments. "imported by no package module but `optimizer/extension.py`" is the exact form.

Recommended change as stated; **not required** — neither claim is false and neither is the entry's
load-bearing sentence. Recorded as examined.

#### Two commands in this artifact do not produce the output printed beside them

Artifact-only (a `bld-*` scratchpad that closes with the cycle), so **no document edit is owed** and I
am not asking for one; recorded because both are the very defect class the pass was closing.

- `### Enumeration 1` (`:858-869`) prints the unfiltered command but the **filtered** output. As
  spelled it returns nine paths, `mutations/resolvers.py` **3** and `utils/querysets.py` **7**; the
  printed table is what `… | grep -v '``'` returns. The conclusion ("eight modules", invocations) is
  right, and I reproduced both spellings.
- `### The findings, and what each remedy was`, Low 1 (`:1053-1055`) records
  *"`grep -rn '\blazy_ref\b'` → 10 hits"*. That command returns **0** — `_` is a word character, so
  `\b` is exactly what excludes `_lazy_ref`. The 10 hits come from the plain `grep -rn 'lazy_ref'`
  (4 `auth/mutations.py`, 2 `auth/queries.py`, 4 `mutations/fields.py`). The companion
  `grep -rn '\.lazy_ref'` → **0** is correct as recorded, and `registry.py` has **0** `lazy_ref`, so the
  underlying claim stands.

### DRY findings

- **The single-ownership rule is now applied to itself, which is what the last pass asked for.** Post-fix
  the seam map has exactly one telling — `### Layer 4` (`:644-654`) — and three pointers at it
  (`:417`, `:930`'s `— Layer 4`, `:1002`), with the rationale entries citing the heading instead of
  writing a fourth copy. The count that mattered went 4 spellings / 3 disagreeing → 1 spelling.
  `grep -rn "whichever field owns"` over `docs/SPECS/` now returns exactly one hit, and it is the
  rationale **quoting the text it retired**.
- **The two remedies chose quotation over restatement, correctly.** `MANY_SIDE_RELATION_KINDS` is now
  pasted rather than paraphrased, and `:610` names the alias rather than re-spelling it. Both are the
  drift-proof shape for a membership claim, and both close the "same constant, third strike" pattern by
  removing the paraphrase rather than fixing it.
- **No new vocabulary, constant, convention, or indirection is introduced**, so the existence challenge
  does not arise on this item either. The eight extra enumeration rows beyond the dispatched Medium add
  coverage, not machinery, and change no document text.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — 0 lines of diff. `__all__` and the
re-export list are unchanged. This item touches no Python file at all; its working-tree footprint is two
`.md` files (` M`) plus this artifact (`??`).

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applies — the item's entire deliverable is documentation. Every gate re-run rather than trusted, with
`shasum -a 256` and `wc -c -l` taken **before and after** each run, since `--check` scripts touch mtimes.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0, 23 terms.**
- `uv run python scripts/check_trailing_commas.py --check` on both documents → **exit 0**.
  `shasum -a 256` identical before and after both runs on both files; `wc -c -l` unchanged.
- **Link / anchor / rule-27 audit** (fenced blocks stripped, **code spans NOT stripped** — stripping
  them is what manufactures the orphan false positive; definition lines excluded from the use scan;
  targets existence-checked on disk): spec **25 defs / 25 uses**, rationale **11 / 11**; **0** missing,
  **0** orphan, **0** dead target. **0** `](#` in-page anchors in either file, so none can dangle.
  **0** in-repo raw `path:NN` in either document (`[A-Za-z0-9_/.-]+\.(py|md):[0-9]+` less `file:///`).
- **No renumbering.** `^### (Layer|Phase|Decision) N` parsed and compared against the expected sequence:
  `Layer 1`-`11`, `Phase 1`-`8`, `Decision 1`-`6` — 25 headings, in file order, no gap, no duplicate.
- **Five cross-spec anchors, both directions, re-derived at this moment** (`spec-010` is under a
  concurrent cycle, so the reading is fresh, not carried): `spec-010-foundation-0_0_4.md:67` →
  `### Layer 3: Finalization trigger` and `:468` → `### Decision 6: fail loudly`, both `grep -c` **1**
  in spec-009; `spec-009:99` / `:634` / `:870` → spec-010's `### Must redo (not augment)` /
  `## Strawberry finalization strategy` / `### Unresolved-target error format`, all `grep -c` **1**.
  Nothing repaired; nothing needed repair.
- **Ledger, re-measured independently.** Spec **61,170 bytes / 1,096 lines**; rationale **60,443 / 829**.
  `git show HEAD:` copies **54,232 / 1,154** and **12,273 / 208**. `git diff --numstat` **114 / 172** and
  **621 / 0**. Both identities close: `1,154 − 172 + 114 = 1,096` and `208 + 621 = 829`.
- **Per-edit byte deltas verified against the file.** `:417` / `:930` / `:1002` measure **490 / 130 /
  362** bytes (`awk NR==n | wc -c`), matching the report; `+18 + 10 + 6 = +34` and `61,136 + 34 =
  61,170`, which is what the file measures. Convention note for a later re-measurement, not a defect:
  the perform pass's `:394` **116** and `:610` **77** exclude the trailing newline (they measure 117 and
  78 with it) while this pass's three figures include it — the deltas are unaffected either way.
- **The four original spec edits stand unweakened.** `:394` and `:610` carry the perform pass's
  replacement text character-for-character (`- [schema audit][glossary-schema-audit] can name the exact
  relation fields whose target model has no registered type`; `relation_kind: RelationKind  # the alias
  in utils.relations, five members`). `:930` still lacks `visibility composition` and `:1002` still
  lacks `, visibility composition, and arguments`; both were narrowed further in the same direction,
  never reverted, and the byte sum closing at +34 leaves no room for an unreported fourth edit.
- **Append-only proved the strong way.** `git diff -- <rationale> | grep -c '^-'` → **1**, and printing
  it shows the `--- a/…` header, so no HEAD line was deleted **or modified**. `-U0` hunks
  `@@ -166,0 +167,619 @@`, `@@ -185,0 +805 @@`, `@@ -186,0 +807 @@` sum `619 + 1 + 1 = 621` against
  `--numstat`. `head -166` of the working file `cmp`s **exit 0** against `head -166` of HEAD's copy
  (HEAD is 208 lines, so the prefix is real). Every rewritten line sits well beyond 166, so the
  in-place correction is inside this cycle's own appended text. `## Standing notes`' "three sites"
  bullet is HEAD content and the one-`-`-line proof shows it unmodified.
- **Provenance.** `git log --stat` over both document paths → the newest commit touching either is still
  **`f3c94642`**, with HEAD at `973d00b2`. Nothing was swept into a concurrent commit. Verified with
  `git log --stat` plus a `git show HEAD:` re-measurement, never `git status` alone.
- **`### Dispatched findings checklist` audited box by box.** Six boxes added by the apply-changes pass,
  each with a matching edit and no edit without a box: High → the rewritten Phase 3 / Decision 3
  rationale entry; Medium `:417` → spec edit 1 **plus** the new rationale entry; Medium
  `MANY_SIDE_RELATION_KINDS` → the Layer 2 entry's quoted frozenset; Low 2 → spec edit 2; Low 1 →
  explicitly no edit, disposition recorded; Consequential `:1002` → spec edit 3. Three spec edits, three
  rationale changes, six boxes, one-to-one. R1's sixteen and R1b's original four are untouched.

### What looks solid

- **The revised denominator reproduces exactly, mechanically.** I parsed every table row myself (a row
  is a `|`-leading line that is neither header nor rule; bucket on the last cell, `*` stripped) and got
  **119** enumeration rows — 66 `true`, 5 `FALSE`, 34 `judgement`, 10 `note (upstream)`, 4
  `out of scope`; `66 + 5 + 34 + 10 + 4 = 119`, opened `= 71`. The eight rows of the `### Revised
  denominator` summary table are correctly excluded. The re-derivation note also holds: **117** of the
  119 rows carry a `:NNN` in column 1, the two exceptions being the numbering row and the cross-spec
  anchor row.
- **The line-coverage instrument reproduces too, and it is the right instrument.** Expanding every
  `:NNN` / `:NNN-NNN` from column 1 and unioning gives **842 of 1,096** lines, **108** gaps totalling
  **254** lines, and the largest residual gap holds **4** non-blank lines (`630-637` and `598-603`) —
  every figure in `### Revised denominator` reproduces to the unit. Prior `785` also reconciles as
  `739 + 46`.
- **The coverage map was audited, not just its arithmetic** — that was the last pass's whole point. I
  dumped every uncovered non-blank line and read all of them. The residue is headings, section openers,
  fence delimiters, and prescriptions (`Take …`, `Borrow …`, `Keep that.`). Eleven uncovered lines do
  carry present-tense package assertions — `:385`, `:393`, `:441`, `:476`, `:491`, `:493`, `:515`,
  `:526`, `:642`, `:696`, `:890` — and I opened the six most falsifiable at the symbol. **All held:**
  `types/definition.py:164` carries the `fields_class` slot while `aggregate_class` / `search_fields`
  have none (`:385`), `types/base.py:138::_validate_filterset_class` exists (`:385`),
  `connection.py::_pipeline_sync` reads `definition.filterset_class` / `orderset_class` off the node
  type (`:393`), `optimizer/hints.py:73::OptimizerHint` is frozen and
  `extension.py:1315::_build_cache_key` keys on AST + directive/pagination variables + model + origin
  with no hint component (`:515`), `registry.py` has **0** `threading` / `Lock` references (`:642`),
  and `filters/sets.py:1135-1143` subclasses `filterset.BaseFilterSet` with the `filter_fields` alias
  at `:1010-1018` (`:696`). No fifth false clause is hiding in the residue I could reach.
- **The `Phase 2.5` call is right.** Introducing it into `### Phase 3` would collide with the spec's own
  `### Phase 1`-`8` **migration** numbering, which is a different axis from `types/finalizer.py`'s
  internal Phase 1 / 2 / 2.5 / 3 — and the spec's `### Phase 3` heading is itself a migration phase, not
  the finalizer's. `### Layer 4`'s own words ("in the cardinality-correct spelling", `:647`) are the
  cheaper and already-owned scoping, and the coverage the absolute carried survives at `:926`, which
  enumerates all five relation shapes. The rationale keeps `Phase 2.5` in its generalisable rule, where
  it matches `types/finalizer.py`'s docstring vocabulary ("a raise inside Phase 2, 2.5, or 3").
- **The `components`-not-`fields` self-catch is correct and worth the line it cost.**
  `optimizer/walker.py::_build_child_queryset` is named by `### Layer 4`'s visibility bullet (`:649`)
  and is a module-level function, not a field; `:1002` now reads "the queryset-owning components
  `### Layer 4: Generated relation fields` names". The same noun was removed from `:417`, so the
  over-narrow phrasing survives nowhere in the spec.
- **This is the first pass on this cycle whose stated counts survived a mechanical recount unchanged in
  both directions** — buckets and line coverage, prior and revised figures alike.

### Temp test verification

No temp tests were written for this review, and `docs/builder/temp-tests/r1b/` was never created. Every
claim under audit is a statement about static source or about document bytes, so the instruments are
reading, `grep`, and a table parser; executing the suite would prove nothing about a documentation edit.

`docs/builder/temp-tests/r1/test_async_execution_default_connection.py` (R1's escalation-8 body) was
**not** modified, moved, re-run, or deleted — `ls -la` shows it unchanged at its 20:42 mtime, older than
this cycle's later passes.

### Notes for Worker 1 (spec reconciliation)

- **All three Lows above are dispositioned by me as examined-and-not-required.** None needs a Worker 2
  pass. If you want the two rationale tightenings (harm-clause polarity, and the two evidence
  spellings) they are one clause each and both sit inside text this cycle appended, so the same
  in-place reading of append-only that carried the High covers them. If you take none of them, nothing
  false ships.
- **The `≥5 non-blank` gap criterion is not equivalent to "no unenumerated present-tense claim", and
  the residue should be carried into R2/R4 with that caveat.** Eleven uncovered lines still carry
  present-tense assertions (listed under `### What looks solid`); I opened six and all held, but they
  survive as single lines *between* covered rows, which a gap-size threshold cannot see. The instrument
  to carry forward is line coverage **plus** a scan of the uncovered non-blank lines themselves, which
  is cheap once the coverage set exists.
- **Examined and not raised, so a later pass does not re-open it:** `### Layer 4`'s visibility bullet
  (`:649`) enumerates three appliers where eight modules invoke the pair. It is correct as scoped —
  Layer 4 is about generated *relation* fields, and `types/relay.py` (node defaults), `permissions.py`
  (cascade), `filters/sets.py` (related-filter scope) and `mutations/resolvers.py` (write path) are not
  relation-read seams — and row `:644-654` grades it `true`. It is now the single telling every other
  site points at, so if a future call site is added, that bullet is the one line to update.
- **R1's escalations 1-5 and 8-10 remain open and none was touched here.** Escalation 8 (no
  permanent-suite row pins `async def get_queryset` → `SyncMisuseError` for a *default*
  `DjangoConnectionField` under `await schema.execute`) is still the only one whose evidence inaction
  destroys; the ready-made body under `docs/builder/temp-tests/r1/` clears with the cycle. **Still
  recommended for carding.**
- **`:592-597`'s registry-global `is_finalized` vs per-type `DjangoTypeDefinition.finalized`** remains
  reported-not-repaired across all three passes, and is still not a false clause.

### Review outcome

`review-accepted`. The High is closed by a rewrite whose every mechanism claim I re-derived at the
symbols — the two gating conditions are real, correctly ordered, and stated as necessary conditions
rather than absolutes, which is the shape whose absence caused the finding. Both Mediums are closed:
`:417`'s contradiction was genuine and its remedy is the same pointer-shrink as `:1002`'s, and the
frozenset is now quoted character-exactly rather than paraphrased a fourth time. The four original spec
edits stand unweakened, the widened enumeration and its line-coverage figure reproduce exactly under an
independent mechanical parse, the coverage *map* was audited line by line rather than only its
arithmetic, and every gate, identity, anchor and append-only proof re-runs clean. The three Lows are
recorded with their dispositions and require no further build pass.

---

## Final verification (Worker 1)

Run 2026-08-16 by a fresh Worker 1 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-1.md`. **HEAD re-derived: `973d00b2`** (`git rev-parse
--short HEAD` at the start of this pass, not inherited from the dispatch; unchanged from Worker 3's
pass-2 reading). `git status --porcelain` is **134** entries; nothing outside this cycle's writable set
was edited, reverted, or `git checkout`ed. `git stash` / `checkout` / `restore` / `worktree` were not
used; every HEAD reference is `git show HEAD:<path>` into an out-of-repo scratch path. Nothing under
`docs/builder/temp-tests/` was touched.

**This item runs no tests and changes no code.** No `pytest` was invoked in this pass, with or without
`--cov*` flags; the working-tree footprint of the item is two `.md` documents plus this artifact, and
`git diff -- django_strawberry_framework/` is empty. `## Final verification job` step 5's focused run is
therefore vacuous and is recorded as such rather than skipped silently. Step 6's staged-anchor sweep
belongs to **R4** (`## Artifact list`: "the staged-anchor sweep into R4") and was deliberately not
duplicated here.

**Spec status-line re-verification (per-spawn duty).** Lines 1-5 re-read. The opener describes the
rationale companion, the four finalization sites, and the six scrubbed mechanisms. Nothing R1b landed
falsifies any of it. **No edit owed.**

**Nothing was edited by this pass.** Every finding below is recorded, not repaired: three prior final
verifications on this cycle found their own defect and set `revision-needed` rather than fixing and
self-accepting, and that is what surfaced three of the cycle's fifteen findings. A custodian edit made
here would be a fresh unreviewed claim in a permanent document, which is exactly the failure this item
is closing.

### Method — changed lines read cold, in file order, at their symbols

The only method that has produced a clean result on this cycle. The five changed spec lines and the
whole of R1b's appended rationale region (`:667-784`, the complete set — R1's region is `:167-666` and
closed under R1's `final-accepted`) were read in file order, with every clause naming a checkable symbol
opened at that symbol. Prior findings' sites were **not** the search space.

### Verification obligations — each proof re-run here, not read off the report

| Obligation | Result |
|---|---|
| Ledger — spec | `wc -c -l` → **61,170 / 1,096** ✓ |
| Ledger — rationale | `wc -c -l` → **60,443 / 829** ✓ |
| HEAD copies | `git show HEAD:` → **54,232 / 1,154** and **12,273 / 208** ✓ |
| `--numstat` | spec **114 / 172**; rationale **621 / 0** ✓ |
| Identity 1 | `1,154 − 172 + 114 = 1,096` ✓ |
| Identity 2 | `208 + 621 = 829` ✓ |
| Append-only, `-` lines | `git diff -- <rationale> \| grep -c '^-'` → **1**, and printing it gives `--- a/docs/SPECS/appx/…` ✓ |
| Append-only, hunks | `-U0` → `@@ -166,0 +167,619 @@`, `@@ -185,0 +805 @@`, `@@ -186,0 +807 @@`; `619 + 1 + 1 = 621` ✓ |
| Append-only, prefix | `head -166` working `cmp` `head -166` HEAD → **exit 0** ✓ |
| Glossary gate | `check_spec_glossary.py --spec …spec-009…` → `OK: 23 terms …` **exit 0** ✓ |
| Comma gate | `check_trailing_commas.py --check` on both → **exit 0** ✓ |
| Numbering | `^### (Layer\|Phase\|Decision) N` → **11 / 8 / 6**, in file order, no gap, no duplicate ✓ |
| In-page anchors | `grep -c '](#'` → **0 / 0**, so none can dangle ✓ |
| Link defs | spec **25 / 25**, rationale **11 / 11**; 0 missing, 0 orphan; 0 dead once the `#fragment` is stripped before the disk check (the known false positive is code-span stripping — a second one is fragment-keeping, recorded here so the next pass does not re-raise it) ✓ |
| Raw `path:NN` | `grep -nE '[A-Za-z0-9_/.-]+\.(py\|md):[0-9]+'` less `file:///` → **no match** in either document ✓ |
| Cross-spec anchors | five, both directions, re-derived at the moment of dependence: `spec-010:67` and `:468` cite spec-009's `### Layer 3: Finalization trigger` / `### Decision 6: fail loudly` (`grep -c` **1** each, and both cited lines read in full); `spec-009:99` / `:634` / `:870` cite spec-010's `### Must redo (not augment)` / `## Strawberry finalization strategy` / `### Unresolved-target error format` (`grep -c` **1** each) ✓ |
| Provenance | `git log --stat` over both paths → newest commit touching either is still **`f3c94642`**, HEAD at `973d00b2`. Nothing swept into a concurrent commit. `git status` alone was not used ✓ |
| Per-edit bytes | measured with `awk NR==n \| wc -c`: `:394` **117**, `:417` **490**, `:610` **78**, `:930` **130**, `:1002` **362**; HEAD's `:393` **90** and `:651` **115**. `+27 − 37 − 25 + 89 = +54` and `+18 + 10 + 6 = +34`; `61,082 + 54 + 34 = 61,170`, which is what the file measures ✓ |

**Enumeration re-derived by parsing the tables, not by reading them.** A row is a `|`-leading line
outside a fence that is neither header nor rule; bucket on the last cell; the eight rows of the
`### Revised denominator` summary table excluded. Result: **119** rows — **66** `true`, **5** `FALSE`,
**34** `judgement`, **10** `note (upstream)`, **4** `out of scope`; `66 + 5 + 34 + 10 + 4 = 119`,
opened **71**. Line coverage by expanding every `:NNN` / `:NNN-NNN` in column 1 and unioning: **842 of
1,096**, **108** gaps / **254** lines, largest residual gap **4** non-blank (`598-603`). **117** of the
119 rows carry a `:NNN`; the two exceptions are the numbering row and the cross-spec-anchor row. Every
figure reproduces to the unit.

### Planned steps — all six landed

`### Implementation steps` 1-4 are the four spec edits (verified at the lines above); step 5 is the
three appended rationale entries (`:667`, `:689`, `:703`); step 6 is the gate/proof/ledger block, re-run
independently here. The apply-changes pass added three further spec edits and one further rationale
entry, all dispatched by Worker 3's findings. **No step was rejected**, so no deferral reason is owed
under `## Final verification job` step 3's last clause.

### `### Dispatched findings checklist` audit — ten boxes, ten edits, one-to-one

Self-derived on this item, so the audit is against the diff rather than a spec checklist. Each box was
checked by opening the current line and, where the box quotes HEAD's text, by `awk`-ing the
corresponding HEAD line out of the out-of-repo copy.

- `:610` → spec now reads `relation_kind: RelationKind  # the alias in utils.relations, five members`; HEAD's `:651` is the quoted `Literal[...]` line character-for-character.
- `:394` → spec now reads `- [schema audit][glossary-schema-audit] can name the exact relation fields whose target model has no registered type`; HEAD's `:393` is the quoted `report exact unfinalized or unresolved fields` line.
- `:930` → `visibility composition` absent; the box's contract holds.
- `:1002` → `, visibility composition, and arguments` absent; the box's contract holds.
- High (rationale visibility argument) → rewritten at `:703-761`; the five-of-eight list, both "reaches none of them" absolutes, and the harm clause are gone.
- Medium `:417` → spec edit **plus** the new rationale entry at `:763`.
- Medium `MANY_SIDE_RELATION_KINDS` → rationale `:674-677` now quotes `frozenset({"many", "reverse_many_to_one", "generic"})` and carries the "two of those three / the sketch's own `"many"` is the third" framing.
- Low 2 → `:930` now reads `in the cardinality-correct spelling`.
- Low 1 → no document edit, disposition recorded in the build report.
- Consequential `:1002` → `queryset-owning components`, not `field`.

**No edit lacks a box.** The document changes are exactly seven spec-line replacements and four
rationale entries; each maps to a box above. **No box lacks an edit**, and none is over-ticked. R1's
sixteen boxes are in R1's artifact and none of their contracts is reversed — `:930` and `:1002` were
narrowed further in the same direction, never reverted.

### Cold read of the five changed spec lines, at their symbols

- **`:394`** — `check_schema` (`optimizer/extension.py::DjangoOptimizerExtension.check_schema`) walks `_collect_schema_reachable_types`, iterates each exposed relation whose `meta.related_model` has no `registry.get(...)`, and appends `f"{type_cls.__name__} ({_model.__name__}.{field_name}) has no registered target DjangoType"`. The replacement text is that condition. **True.**
- **`:417`** — `types/resolvers.py` carries **0** `async def` / `await` and **0** `apply_type_visibility`; `utils/querysets.py::SyncMisuseError` is raised by `reject_async_in_sync_context` when a hook returns an awaitable in a sync context. "Runs at the queryset-owning seams `### Layer 4` names, never inside the generated resolver" holds, and the second half is the load-bearing clause. **True.**
- **`:610`** — `utils/relations.py` defines `RelationKind: TypeAlias = Literal["many", "reverse_many_to_one", "reverse_one_to_one", "forward_single", "generic"]`. Five members, in `utils.relations`. **True.**
- **`:930`** — `types/converters.py::resolved_relation_annotation` returns `list[target_type]` / `target_type | None` / `target_type` on the three branches, i.e. Layer 4's "cardinality-correct spelling"; `types/resolvers.py::_attach_relation_resolvers` installs one generated resolver per relation in `selected_fields`. **True.** Examined and not raised: `_attach_relation_resolvers` skips `skip_field_names` (consumer-assigned relation fields), so "every exposed relation" is not literally exhaustive — but the carve-out exists so a consumer override is not clobbered, the section's subject is *generated* relation fields, and `### Layer 4`'s own resolution bullet is scoped the same way and is graded `true` by three passes. Recorded so a later pass does not re-open it as new.
- **`:1002`** — same two symbols, plus `types/finalizer.py::_synthesize_relation_connections` for the argument seam. "Queryset-owning components `### Layer 4` names" is apt for both the visibility appliers (`:649` names the connection pipeline, `list_field.py::DjangoListField`, `optimizer/walker.py::_build_child_queryset`) and the argument owner (`:650` names `connection.py::DjangoConnectionField`). **True.**

### The reversal's mechanism chain, re-derived independently rather than accepted

Run at the symbols, in call order, without reading Worker 3's line numbers first:

- `optimizer/walker.py::plan_relation` — `if _target_has_custom_get_queryset(target_type): … return ("prefetch", "custom_get_queryset")` sits **above** `if is_many_side_relation_kind(relation_kind(field)):`, so the downgrade fires for any relation shape, forward FK included.
- `optimizer/walker.py::_build_child_queryset` — `queryset = field.related_model._default_manager.all()`, then `if has_custom_qs:` → `queryset = apply_type_visibility_sync(target_type, queryset, info, allow_sliced=True)`, quoted in the entry character-for-character.
- `types/base.py::DjangoType.get_queryset` is a documented identity hook, so condition (a) is what makes "visibility composition" denote anything.
- `django_strawberry_framework/schema.py` contains **0** `DjangoOptimizerExtension` references, so condition (b) is materially load-bearing.

Both conditions are stated in the rewritten entry as **necessary** ("only when … and …"), which is the
shape whose absence caused the finding. **The High is genuinely closed.**

### Weighing the three Lows Worker 3 recorded rather than raised

**Low 1 — the rejected-alternative harm clause (`rationale:757-761`). Decided: FIX.** Worker 3 called it
"the nearest thing to a fifth false correction" and dispositioned it not-required; I disagree on the
disposition, not on the analysis. The clause is literally true and materially vacuous: `types/base.py`'s
default `get_queryset` is an identity hook, so a target that does not override it has no visibility rule
to lose, and the entry's own bullet 2 sets up the harmful inverse (override present, optimizer absent).
What makes it more than a wording preference is *where* it sits — a rejected alternative's recorded harm
is the load-bearing half of the entry (`BUILD.md` `## Spec rationale extraction`: the recorded reason is
what stops the next round re-fighting the question). A harm a reader can defeat in one line is a reason
that will not hold. Worker 3 supplied the exact swap; it is one clause, inside this cycle's own appended
text, so the same in-place reading of append-only that carried the High covers it.

**Low 2 — two evidence spellings in the permanent rationale. Decided: FIX, and the second is the one
that matters.** Both underlying claims re-verified true here.

- `rationale:768` — run as spelled, `grep -rn 'apply_type_visibility_\(sync\|async\)(' django_strawberry_framework/` reaches **nine** paths, adding `forms/resolvers.py:32`, a docstring mention. Reproduced. One word fixes it.
- `rationale:735` — *"`plan_optimizations` is imported by `optimizer/extension.py` and nothing else."* Package source: exactly one importer, `optimizer/extension.py:95`. Repo-wide: `tests/optimizer/test_multi_db.py`, `test_definition_order.py`, and `test_walker.py` import it too, and `optimizer/nested_fetch.py` names "direct `plan_optimizations` callers (tests)" in its own comment. **The sentence as written is an absolute enumeration that is literally false against the repo** — the exact shape this cycle has now been burned by four times — and it is the sentence establishing condition (b). Worker 3's exact form, "imported by no package module but `optimizer/extension.py`", costs three words and makes it true.

**Low 3 — artifact-only bookkeeping. Decided: NO EDIT, accepted as recorded.** `bld-*.md` closes with
the cycle (`START.md` "Temp artifact conventions"). Both are real: `### Enumeration 1` prints the
unfiltered command with the filtered output (reproduced — as spelled it returns nine paths,
`mutations/resolvers.py` **3** and `utils/querysets.py` **7**), and `grep -rn '\blazy_ref\b'` returns
**0** because `_` is a word character (reproduced). Two more of the same class, found here and likewise
requiring no edit: the perform report's `### DRY analysis` says "Two of the four corrections are pure
cuts; two are replacements" while its own `### The four findings` records one cut (`:930`) and three
replacements (`:394` narrowed, `:610`, `:1002`); and the apply pass's "the over-narrow phrasing survives
nowhere in the spec" is inexact — `:526` still reads "async-safe access belongs to the **field** that
owns the queryset" (a different spelling than the `whichever field owns` grep searched). `:526` itself
is **not** false: it is scoped to async access on a relation read, where the queryset owner is the
connection or list field. Recorded so a later pass does not re-open either as new.

### The gap-size threshold, and the caveat Worker 3 asked to be acted on or accepted

**Decided: accept the `>= 5 non-blank` criterion, with the residue discharged rather than assumed.**
Worker 3 is right that a gap-size threshold is not equivalent to "no unenumerated present-tense claim",
and right that it opened only six of the eleven single-line survivors. I opened **the remaining six**
(`:441`, `:476`, `:491`, `:493`, `:526`, `:890`) at their symbols:

- `:441` "no placeholder tier … a relation either resolves to a concrete registered `DjangoType` or finalization fails" — `types/finalizer.py::_format_unresolved_targets_error`; both in-file headings it cites (`### The unresolved-relation contract is error-only` at `:869`, `### Decision 6: fail loudly` at `:1010`) resolve. **True.**
- `:476` "each is a **factory returning a Strawberry field**" — the three module-level `def`s at `list_field.py::DjangoListField`, `connection.py::DjangoConnectionField`, `relay.py::DjangoNodeField`. **True.**
- `:491` "a bare generic alias loses the `resolve_connection` override at Strawberry's generic specialization" — `connection.py` #"a generic ALIAS handed to the schema loses the ``resolve_connection``". **True.**
- `:493` "`aggregates` … unbuilt; `TODO-BETA-057-0.1.3` owns it, and it lands through the same generated-subclass mechanism `totalCount` uses" — no `aggregates` member on either connection class; `aggregates/` absent and carded in `docs/TREE.md`. **True.**
- `:526` "that resolver stays sync, and async-safe access belongs to the field that owns the queryset" — `types/resolvers.py` has 0 async markers; `apply_type_visibility_async`'s external callers are `connection.py`, `list_field.py`, `types/relay.py`, `filters/sets.py`. **True as scoped** (see Low 3).
- `:890` "this matches the target layout in `docs/TREE.md`" — every module the list names appears in `docs/TREE.md`'s target layout with the same card annotations (`aggregates/` → `TODO-BETA-057-0.1.3`, `fieldset/` → `TODO-BETA-054-0.1.1`, `permissions/` → `TODO-BETA-059-0.1.4`). The spec's list is a proposal-scoped subset, not an equality claim. **True.**

**All six held.** With Worker 3's six, the entire eleven-line residue is now opened and no sixth false
clause hides in it. That is what licenses accepting the threshold: the criterion is accepted **because
the residue it cannot see was enumerated and discharged**, not because the criterion is sound on its own.
Carry into R2 / R4 as `line coverage + a scan of the uncovered non-blank lines`, exactly as Worker 3
framed it.

### Cross-pass consistency, and against R1's closed diff

- **The single-ownership consolidation now holds, and I re-derived it rather than reading it.** `grep -n "apply_type_visibility" ` over the spec returns exactly **two** hits: `:417` (a pointer) and `:649` (`### Layer 4`'s bullet, the one telling). `:930` carries `— Layer 4` and `:1002` names the heading. No fourth copy. The pre-fix state was three spellings that disagreed.
- **R1's closed text already carried the correct three-applier list** (`rationale:316-318`: the connection pipeline, `list_field.py::DjangoListField`, and `optimizer/walker.py::_build_child_queryset`, "the last of which is opt-in at schema construction"). R1b's perform pass then wrote a five-module list omitting exactly the site R1 had got right, 450 lines above it in the same file. That is the sharpest available statement of why a fix pass's own new prose is the highest-risk text in a cycle: the correct enumeration was already in the document being appended to.
- **No new vocabulary, constant, or convention** is introduced by R1b, so the existence challenge does not arise. The one new cross-reference form reuses `:415`'s code-span heading citation.
- **Two rationale entries are keyed to `### Borrow \`StrawberryDjangoFieldBase\` and \`StrawberryDjangoField\``** (`:270` from R1, `:763` from R1b). That is correct under `BUILD.md` `## Spec rationale extraction` — each names the decision it belongs to and records a different change — and is not a duplication finding.

### The finding this pass adds — Medium, and it is the fifth false correction-pass clause

**`rationale:682` — "This is the one place on this document where a replacement beat a cut" is a false
definite description, contradicted twice inside the same append.**

The clause closes the `### \`### Layer 2: Pending relation registry\`` entry, justifying why `:610` was
replaced rather than cut. Counterexamples, all in the same file, two of them written by the same pass in
the same operation:

- `rationale:697` — *"The clause was **narrowed to the capability the symbol has**, not cut"* (the `:394` entry). **Fifteen lines below the claim.**
- `rationale:739` — *"`### Decision 3` was **replaced** rather than cut"* (the Phase 3 / Decision 3 entry). Fifty-seven lines below.
- `rationale:638` — R1's own *"replaced with the contract stated directly"*.

Both readings of "this document" fail. Read as the spec, replacements beat cuts at `:394`, `:417`,
`:930` and `:1002`. Read as this record, `:697` and `:739` say so in as many words. The artifact's own
`### DRY analysis` states "two are replacements" for the same four corrections, so the claim was false
against its author's own adjacent prose at the moment of writing.

**Why Medium and not Low.** It is not a mechanism claim about shipped code, which is why it is not
High — no reader concludes anything wrong about the package from it. It is Medium on the same ground
`spec-009:417` was: a permanent document contradicting itself on the page, in the sentence that teaches
the cut-versus-replace rule this whole cycle turns on. It is also a **stated count** in the sense
`BUILD.md` `## Claims are proven mechanically` means — a definite description that reads as measured,
propagates as measured, and is invisible to re-reading — and it is the same false-definite-description
shape as the `MANY_SIDE_RELATION_KINDS` "the two that decide many-side classification", which this cycle
graded Medium and fixed.

**Recommended remedy: delete the clause.** The entry's reason for replacing rather than cutting is
already complete without it ("the sketch needs a type for the slot, and `RelationKind` is checkable from
the cited symbol at the reader's desk"), and the sentence adds only a population claim the document
disproves. This is R1's own rule applied to R1b's prose: **cut when the reason cannot be verified
cheaply by the reader at their desk.** Do not replace it with a corrected count — a count of remedies
rots on the next remedy, which is the identical argument that retired the `RelationKind` re-spelling
eleven lines above it.

### DRY check across this item and prior accepted items

No new duplication. The item's whole shape is de-duplication: three restatements of `### Layer 4`'s seam
map collapsed to pointers, one membership claim collapsed to a quoted constant, one to an alias name.
The three remedies this pass asks for are all **deletions or one-clause narrowings**, none of which adds
a shape. No DRY opportunity remains open.

### Escalations carried forward — report-only, unrepaired, and unchanged in substance

1. **`spec-010:8` and `:491`** describe surfaces this cycle scrubbed, and the `spec-010:67` coupling has a near-duplicate sentence. Owned by the concurrent spec-010 cycle; only the maintainer can sequence the two cycles at commit. Both spec-010 files re-read read-only this pass; nothing was edited, reverted, or `git checkout`ed.
2. **`types/definition.py::DjangoTypeDefinition`'s docstring** reserves `fields_class` for the pre-renumber `TODO-BETA-046-0.1.1`. Source is read-only in this cycle.
3. **The rationale's `## Standing notes` "three sites" bullet** is deliberately stale under append-only and flagged in-file five lines above it; the one-`-`-line proof shows it unmodified.
4. **`spec-009:592-597`'s registry-state sentence** is satisfied across two objects — registry-global `is_finalized` versus per-type `DjangoTypeDefinition.finalized`. Not false; a future pass tightening it should say which object holds which half. Reported-not-repaired across all four passes.
5. **The one whose evidence inaction destroys.** No permanent test row pins `async def get_queryset` → `SyncMisuseError` for a *default* `DjangoConnectionField` under `await schema.execute`. The ready-made body at `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is gitignored and clears with the cycle. **Recommend carding before the cycle closes.** Not modified, moved, re-run, or deleted by this pass.

### Summary

**What R1b shipped.** A clause-by-clause mechanism sweep of all 1,096 lines of
`spec-009-rich_schema_architecture-0_0_4.md` — the 984 pre-existing lines no prior pass had opened at
the mechanism level, plus the two added-text sites the maintainer routed here — under
`### Maintainer decision 4`. The defect class: *a sentence asserting a mechanism, seam, cause, recourse,
or capability the code does not have.*

**The yield, and why its ratio is structural.** **Four** false clauses in 984 pre-existing lines,
against **eleven** in the 112 lines this cycle added. That ratio is not luck. A horizon document's
pre-existing text is overwhelmingly **prescriptive** — "should", "take this", "recommended adaptation",
"borrow the behaviors not the class" — and **a prescription cannot be false about a mechanism**: the
defect class needs a present-tense assertion to attach to, and prescriptive text offers far fewer per
line than a fix pass's connective tissue does. All four pre-existing findings sit in the only four
places pre-existing text does assert present tense: a code sketch's comment (`:610`), a `Benefits:` list
(`:394`), and two one-line restatements of another section's map (`:930`, `:1002`). The fifth, `:417`,
is a section-closing paragraph of the same kind. **The operational lesson for any future sweep: go
straight to code-sketch comments, `Benefits:` / `Implementation:` lists, and one-line restatements of
another section — and skip the "should" prose.**

**The five corrections that landed**, all single-line, no renumbering, no heading text changed, no
section added or removed:

1. **`:610`** — `Literal["forward_single", "many", "reverse_one_to_one"]  # mirrors utils.relations.RelationKind` (three of five members, asserting a mirror it did not have) → `relation_kind: RelationKind  # the alias in utils.relations, five members`. Replaced with the alias, not re-spelled: a copied enumeration is true today and false on the next member.
2. **`:394`** — "can report exact **unfinalized** or unresolved fields" → "can name the exact relation fields whose target model has no registered type". `check_schema` cannot observe an unfinalized field from a built schema; narrowed rather than cut because the bullet is the sole `[glossary-schema-audit]` use and cutting it would have dropped the term count 23 → 22.
3. **`:930`** (`### Phase 3`) — visibility composition cut from the generation list, and the surviving "across every cardinality" absolute replaced by `### Layer 4`'s own "in the cardinality-correct spelling".
4. **`:1002`** (`### Decision 3`) — visibility and arguments cut from the generation list and attributed to "the queryset-owning **components** `### Layer 4` names", so the decision still accounts for all four seams without writing a third copy of the map.
5. **`:417`** — a third copy of the seam map naming three of eight invoking modules, a *different* incomplete triple than `### Layer 4`'s, standing **two lines below** `:415`'s own "it is not repeated here" — the spec contradicting itself on the page. Replaced by the same pointer-shrink.

**Post-fix the seam map has exactly one telling** — `### Layer 4` (`:644-654`) — with `:417`, `:930` and
`:1002` pointing at it. Four rationale entries record the reasoning, each keyed to the spec heading it
belongs to, each with its rejected alternative and the reason it lost.

**Final enumeration denominator and coverage map.** **119** clause sites enumerated across all 1,096
lines: **66** `true`, **5** `FALSE` (all corrected), **34** `judgement`, **10** `note (upstream)`, **4**
`out of scope`; **71** opened at the symbol they name. Line coverage **842 / 1,096**, residue **108**
gaps / **254** lines, **no residual gap holding five or more non-blank lines** (largest is four). The
eleven single-line present-tense survivors *between* covered rows were all opened — six by Worker 3, six
by this pass (`:441`, `:476`, `:491`, `:493`, `:526`, `:890`, one overlapping) — and **all held**. Every
figure reproduces under an independent mechanical parse.

**Ledger, with closing identities.** Spec **61,170 bytes / 1,096 lines** (HEAD: 54,232 / 1,154);
rationale **60,443 / 829** (HEAD: 12,273 / 208). `git diff --numstat`: spec **114 / 172**, rationale
**621 / 0**. Both identities close: `1,154 − 172 + 114 = 1,096` and `208 + 621 = 829`. Per-edit byte
deltas `+27 − 37 − 25 + 89` and `+18 + 10 + 6` sum to the file's `61,082 → 61,170`. Append-only holds
the strong way: one `-` line and it is the `--- a/` header, so no HEAD line was deleted or modified;
`head -166` `cmp`s clean against HEAD's copy. Gates: glossary **23 terms, exit 0**; trailing commas
**exit 0** on both; **25/25** and **11/11** link definitions with 0 missing / 0 orphan / 0 dead; **0**
in-page anchors; **0** in-repo raw `path:NN`; Layers **11** / Phases **8** / Decisions **6** intact and
un-renumbered; five cross-spec anchors **1** each in both directions. `git log --stat` over both paths:
newest commit touching either is still **`f3c94642`** with HEAD at `973d00b2` — nothing was swept into a
concurrent commit.

**What blocks acceptance.** One Medium in the permanent rationale (`:682`, above) plus two Low-severity
clauses I have decided to fix rather than accept (the vacuous rejected-alternative harm, and
`plan_optimizations` "imported by … and nothing else"). None touches a spec edit, the conclusion of the
reversal, the denominator, the coverage map, or any gate. **Fix the three clauses; nothing else on this
item is open.**

### Spec changes made (Worker 1 only)

**None.** This pass edited neither the spec nor the rationale. Every finding above is recorded for the
apply-changes pass rather than repaired here, so no fresh unreviewed claim enters a permanent document
at the moment of acceptance.

No `### Dispatched findings checklist` box is left `- [ ]`, so no deferral reason is owed under
`## Final verification job` step 3.

### Final status

`revision-needed`. One Medium and two decided Lows, all in text this cycle appended to the permanent
rationale, all remediable by deletion or a one-clause narrowing:

1. **Medium** — `rationale:682` "the one place on this document where a replacement beat a cut": **delete the clause**, do not re-count.
2. **Low 1, decided fix** — `rationale:757-761`: swap the harm clause's polarity to the target that **does** override `get_queryset`.
3. **Low 2, decided fix** — `rationale:735` → "imported by no package module but `optimizer/extension.py`"; `rationale:768` → mark the parenthetical grep as invocations-only, or drop it and keep the claim.

The apply-changes pass for this item is Worker 1's per the build plan's `### Deviation 3` corollary, and
sets `planned` again, which Worker 0 reads as "dispatch Worker 3".

---

## Build report (Worker 1, apply-changes pass 2)

Run 2026-08-16 by a fresh Worker 1 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-1.md`. **HEAD re-derived: `973d00b2`** (`git rev-parse
--short HEAD` at the start of this pass, not inherited from the dispatch; unchanged from the final
verification's reading). `git stash` / `checkout` / `restore` / `worktree` were not used; the one HEAD
reference is `git show HEAD:<path>` into an out-of-repo scratch path. No file outside this cycle's
writable set was edited, reverted, or `git checkout`ed; nothing under `docs/builder/temp-tests/` was
touched. No `pytest` ran, with or without `--cov*` flags, and `git diff -- django_strawberry_framework/`
is empty — this pass reads source and writes only documents.

**Spec status-line re-verification (per-spawn duty).** Lines 1-5 re-read. The opener describes the
rationale companion, the four finalization sites, and the six scrubbed mechanisms. All three
corrections land in the rationale's own R1b region; none touches a finalization site, a scrubbed
mechanism, or the companion's role. **No edit owed.**

### Scope: three corrections, four clause edits, zero spec edits

The final verification dispatched exactly three items and nothing else. All three sit in entries this
cycle appended to the rationale, so they are corrected **in place** under the reading of append-only
this cycle has now used twenty-one times: append-only protects **pre-cycle** text, and appending a
correction beneath a false clause is the outcome the rule was never meant to buy.

**The spec is byte-unchanged.** The writable set allowed a spec edit "only if a twin of any corrected
clause exists there — check, do not assume". Checked mechanically, and the check had to survive the
line-wrap trap this cycle has been bitten by: `grep -c 'beat a cut'` returns **0 even in the rationale
that contains the phrase**, because it wraps as `beat a\ncut`. So each clause was swept by its shortest
distinctive token instead.

```
$ S=docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md
$ for t in 'beat a cut' 'replacement' 'one place' 'plan_optimizations' \
           'nothing else' 'unfiltered' 'apply_type_visibility' 'eight'; do
      printf '%-22s : ' "$t"; grep -c -- "$t" "$S"; done
beat a cut             : 0
replacement            : 0
one place              : 1
plan_optimizations     : 0
nothing else           : 1
unfiltered             : 0
apply_type_visibility  : 2
eight                  : 0
```

Both non-zero hits opened and graded **not a twin**: `:771` "expressible in one place" is the
`FieldSet` wrapping argument, and `:634` "the trigger is the explicit consumer call, and nothing else"
is Layer 3's finalization contract. The spec's two `apply_type_visibility` sites are `:417` (the
pointer this cycle installed) and `:649` (`### Layer 4`'s canonical telling) — the *target* of the
corrected clause, not a copy of it. `plan_optimizations` and `unfiltered` do not occur in the spec at
all. **No spec twin exists, so no spec edit was made**, and `wc` confirms the file is byte-identical.

### Correction 1 (Medium) — `rationale:682`, the false definite description: DELETED

Before (three lines):

```
from the authority and cannot drift. This is the one place on this document where a replacement beat a
cut: the sketch needs a type for the slot, and `RelationKind` is checkable from the cited symbol at the
reader's desk.
```

After (two lines):

```
from the authority and cannot drift. A replacement beat a cut here because the sketch needs a type for
the slot, and `RelationKind` is checkable from the cited symbol at the reader's desk.
```

**Deleted, not re-counted**, exactly as dispatched. The clause that survives is the entry's actual
reason for replacing rather than cutting, and it is verifiable at the reader's desk from the cited
symbol; the clause that went is a population claim over the document, which is the shape that rots on
the next remedy. This is the same argument that retired the `RelationKind` re-spelling eleven lines
above it, now applied to the sentence that taught it.

Not touched, and recorded so a later pass does not read the omission as an oversight: `rationale:533`
"this is the one place in this pass where a spec claim was kept rather than corrected" is a **different**
predicate over a **different** population (R1's pass, claims *kept*), sits in R1's `final-accepted`
region, and was not dispatched. It is flagged for Worker 3 below rather than repaired here — grading it
would mean re-deriving R1's whole 103-row table, which is not this pass's scope.

### Correction 2 (Low, promoted to fix) — the harm clause's polarity: INVERTED

The entry's bullet 2 states the two conditions as **necessary**: visibility composition reaches a
relation through `optimizer/walker.py::_build_child_queryset` "only when the target type overrides
`get_queryset` **and** the optimizer extension is installed". The rejected alternative's harm clause
then named the configuration where the *first* condition fails — in which nothing is lost, because
`types/base.py::DjangoType.get_queryset` is a documented identity hook. The harmful configuration is
the inverse: the consumer **wrote** a visibility rule and the schema is built without the extension
that would apply it.

Before / after, the changed clause only:

```
- gate it — leaving a schema built without `DjangoOptimizerExtension`, whose relation target does not
- override `get_queryset`, unfiltered on a path the sentence claimed was covered.
+ gate it — leaving a forward single relation whose target **does** override `get_queryset`, read through
+ a schema built without `DjangoOptimizerExtension`, unfiltered on a path the sentence claimed was
+ covered.
```

**Why `forward single` and not `any relation`** — the scope was narrowed deliberately rather than
carried over, because a many-side relation under the default shape is composed by the synthesized
connection pipeline whatever the optimizer does (the entry's own bullet 1), so an unscoped harm claim
would have been the same over-reach in the opposite direction. The forward single is the shape with no
second seam, and it is checkable at the symbol:

```
$ grep -c 'apply_type_visibility' django_strawberry_framework/types/resolvers.py
0
$ sed -n '378,420p' django_strawberry_framework/types/resolvers.py   # forward_resolver, both exits
        if not elisions and planned is None:
            return getattr(root, field_name)
        ...
        return getattr(root, field_name)
```

Both exits of `types/resolvers.py::_make_relation_resolver`'s `forward_resolver` return the row-bound
accessor. No new mechanism sentence was added for this: the entry already states 45 lines above that
each emitted shape "returns the row-bound accessor with no visibility call in it", and restating it
inside the same entry is the duplication shape this cycle exists to remove.

### Correction 3 (Low, promoted to fix) — two evidence spellings, both re-derived here

**3a — `rationale:733`, `plan_optimizations`.** The claim "imported by `optimizer/extension.py` **and
nothing else**" is false repo-wide. Importers enumerated mechanically, not typed:

```
$ grep -rn 'import .*plan_optimizations' --include='*.py' . | grep -v '^./\.venv'
tests/optimizer/test_multi_db.py:42:from django_strawberry_framework.optimizer.walker import plan_optimizations
tests/optimizer/test_definition_order.py:9:from django_strawberry_framework.optimizer.walker import plan_optimizations, plan_relation
scripts/bench_optimizer_walk.py:180:    from django_strawberry_framework.optimizer.walker import plan_optimizations
scripts/bench_optimizer_walk.py:199:    from django_strawberry_framework.optimizer.walker import plan_optimizations
django_strawberry_framework/optimizer/extension.py:95:from .walker import plan_optimizations, plan_relation

$ grep -rn 'import .*plan_optimizations' --include='*.py' django_strawberry_framework/
django_strawberry_framework/optimizer/extension.py:95:from .walker import plan_optimizations, plan_relation
```

Four importers outside the package — and the count the final verification recorded ("three test
modules") is itself one short, because `tests/optimizer/test_walker.py` imports it inside a
parenthesized multi-line `from … import (…)` that a single-line `^from` anchor cannot see. That is the
grep-shape trap again, found by re-running rather than by trusting the number, which is why the fix
must not carry a count at all.

Applied — the second grep is the whole warrant:

```
- under `DjangoOptimizerExtension`: `plan_optimizations` is imported by `optimizer/extension.py` and
- nothing else.
+ under `DjangoOptimizerExtension`: `plan_optimizations` is imported by no package module but
+ `optimizer/extension.py`.
```

The sentence establishes condition (b) of the entry's central argument, so it had to stay a claim
rather than be cut; "no package module but" is true, is scoped to the population the argument needs,
and costs three words.

**3b — `rationale:768`, the grep parenthetical.** The command as spelled reaches **nine** paths, not
the eight listed:

```
$ grep -rn 'apply_type_visibility_\(sync\|async\)(' django_strawberry_framework/ | cut -d: -f1 | sort -u
django_strawberry_framework/connection.py
django_strawberry_framework/filters/sets.py
django_strawberry_framework/forms/resolvers.py      <-- the ninth: a docstring mention, no invocation
django_strawberry_framework/list_field.py
django_strawberry_framework/mutations/resolvers.py
django_strawberry_framework/optimizer/walker.py
django_strawberry_framework/permissions.py
django_strawberry_framework/types/relay.py
django_strawberry_framework/utils/querysets.py
```

The underlying claim — **eight** modules with executable invocations — is true, and was re-derived
mechanically by tokenizing each module and keeping only matches on lines carrying non-comment,
non-string tokens:

```
$ uv run python - <<'PY'   # tokenize.COMMENT / tokenize.STRING lines dropped
django_strawberry_framework/connection.py [1780, 1815]
django_strawberry_framework/filters/sets.py [2470, 2505]
django_strawberry_framework/list_field.py [211, 217]
django_strawberry_framework/mutations/resolvers.py [885]
django_strawberry_framework/optimizer/walker.py [383]
django_strawberry_framework/permissions.py [702]
django_strawberry_framework/types/relay.py [843, 864, 904, 929]
django_strawberry_framework/utils/querysets.py [2893, 2993, 3169, 3276, 3295]
distinct executable-invocation modules: 8
```

That set is exactly the eight the parenthetical already lists, so the enumeration was correct and only
its attribution to a command was not. Remedy per the dispatch's "drop it and keep the claim", and per
the standing preference for deleting a fragile clause over restating it — **the command spelling is
what was deleted; the eight module names, which a reader can open one by one, stay**:

```
- invoke `apply_type_visibility_sync` / `_async`
- (`grep -rn 'apply_type_visibility_\(sync\|async\)(' django_strawberry_framework/` reaches
- `connection.py`, `filters/sets.py`, `list_field.py`, `mutations/resolvers.py`, `optimizer/walker.py`,
- `permissions.py`, `types/relay.py`, `utils/querysets.py`), and a **different** incomplete triple than
+ invoke `apply_type_visibility_sync` / `_async` (`connection.py`, `filters/sets.py`, `list_field.py`,
+ `mutations/resolvers.py`, `optimizer/walker.py`, `permissions.py`, `types/relay.py`,
+ `utils/querysets.py`), and a **different** incomplete triple than
```

No count was corrected into the document by this pass. Correction 1 removed a count, 3a removed one,
and 3b removed the command that mis-supported one.

### Gates, proofs and ledger — all re-run this pass, none read off a prior report

| Obligation | Result |
|---|---|
| Ledger — spec, before / after | **61,170 / 1,096** → **61,170 / 1,096**, byte-identical as expected ✓ |
| Ledger — rationale, before / after | **60,443 / 829** → **60,356 / 828** ✓ |
| Per-edit deltas sum to the ledger | `-33` (c1) `+5` (c3a) `+30` (c2) `-89` (c3b) = **-87** bytes; `-1 +0 +1 -1` = **-1** line. `60,443 - 87 = 60,356` ✓ and `829 - 1 = 828` ✓ |
| HEAD copies | `git show HEAD:` → spec **54,232 / 1,154**, rationale **12,273 / 208** ✓ |
| `--numstat` | spec **114 / 172** (unchanged); rationale **620 / 0** ✓ |
| Identity 1 (spec) | `1,154 - 172 + 114 = 1,096` ✓ |
| Identity 2 (rationale) | `208 + 620 = 828` ✓ |
| Append-only, `-` lines | `git diff -- <rationale> \| grep -c '^-'` → **1**, and printing it gives `--- a/docs/SPECS/appx/…` — no HEAD line deleted or modified ✓ |
| Append-only, hunks | `-U0` → `@@ -166,0 +167,618 @@`, `@@ -185,0 +804 @@`, `@@ -186,0 +806 @@`; `618 + 1 + 1 = 620` = the numstat addition ✓ |
| Append-only, prefix | `head -166` working `cmp` `head -166` HEAD copy → **exit 0** ✓ |
| Glossary gate | `check_spec_glossary.py --spec …spec-009…` → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0** ✓ |
| Comma gate | `check_trailing_commas.py --check` on **both** documents → **exit 0** ✓ |
| Numbering | `^### (Layer\|Phase\|Decision) N` → **11 / 8 / 6**, printed in file order, no gap, no duplicate, none renumbered ✓ |
| In-page anchors | `grep -c '](#'` → **0 / 0**, so none can dangle ✓ |
| Link defs | spec **25 defs / 25 uses**, rationale **11 / 11**; 0 missing, 0 orphan, 0 dead. Uses harvested from the raw body as well as the fence-stripped one (a ref-style use can sit inside a code span) and the `#fragment` stripped before each disk check — both known false-positive shapes ✓ |
| Raw `path:NN` | `grep -nE '[A-Za-z0-9_/.-]+\.(py\|md):[0-9]+'` less `file:///` → **no match** in either document. The `optimizer/extension.py:95` and `forms/resolvers.py` evidence lives in this artifact, which `START.md` exempts, never in the permanent files ✓ |
| Cross-spec anchors | five, both directions, `grep -c` **1** each: spec-010 `:67` / `:468` → spec-009 `### Layer 3: Finalization trigger` / `### Decision 6: fail loudly`; spec-009 `:99` / `:634` / `:870` → spec-010 `### Must redo (not augment)` / `## Strawberry finalization strategy` / `### Unresolved-target error format`. Nothing to repair ✓ |
| Provenance | `git log --stat` over both paths → newest commit touching either is still **`f3c94642`**, HEAD at `973d00b2`. Nothing was swept into a concurrent commit. `git status` alone was not used as the test ✓ |

**Failability proofs.** None; this pass introduced no boundary, guard, gate, or rejection path. It edits
two Markdown documents.

**Hot-path budget.** Not applicable; the plan declares no hot path and this pass writes no code.

**Floor verification.** Not applicable; the plan declares floor-verification scope `none` for this item.

### `### Dispatched findings checklist` — three boxes added, four clause edits, mapping stated

The checklist still maps one-to-one after the append. Correction 3 is two clauses by the dispatch's own
wording ("Both are one clause each"), so its single box covers two edits; every other box is one edit:

- Medium box → `rationale:682` deletion.
- Low 1 box → `rationale:759-761` polarity swap.
- Low 2 box → `rationale:732-733` and `rationale:767-769`.

**No box lacks an edit and no edit lacks a box.** No box on this item is left `- [ ]`, so no deferral
reason is owed under `## Final verification job` step 3. Boxes above this pass's block were appended to,
never rewritten; the artifact's prior sections are untouched.

**Explicitly not fixed, per the dispatch**: the artifact-only bookkeeping the final verification accepted
(the filtered output printed under an unfiltered command in `### Enumeration 1`; the
`grep -rn '\blazy_ref\b'` attribution returning 0 because `_` is a word character; the perform report's
"two are replacements"; and the apply pass's "survives nowhere in the spec" against `:526`'s different
spelling). `bld-*.md` is per-cycle scratch that closes with the cycle, not a permanent document.

### Notes for Worker 3

- **The three edits are the whole diff.** `git diff` over the two permanent documents shows one file
  changed (`…-rationale.md`), four clause sites, net `-87` bytes / `-1` line. The spec is byte-identical
  to its state at the final verification, which the ledger row proves rather than asserts.
- **Re-derive both greps rather than reading the pasted output**; that is the instruction this pass was
  given and it found a fourth importer the final verification's own count had missed. The two commands
  are quoted verbatim above and take a second each.
- **The one judgement call worth a second opinion** is correction 2's narrowing to `forward single`.
  The dispatch said "state the harmful configuration"; I scoped it to the relation shape that has no
  second visibility seam, because the unscoped inverse would over-claim for a default-shaped many-side
  relation, which the connection pipeline composes with or without the optimizer.
- **Flagged, not repaired:** `rationale:533` "this is the one place in this pass where a spec claim was
  kept rather than corrected" is the same *grammatical* shape as the Medium just deleted. It was not
  dispatched, sits in R1's `final-accepted` region, and its predicate and population both differ. If
  Worker 3 judges it in scope, it is a re-derivation of R1's table, not a one-line check.

### Notes for Worker 1 (spec reconciliation)

No spec reconciliation is owed: the spec is byte-unchanged and the twin sweep above is the evidence,
not an assumption. The five escalations the final verification carried forward are **unchanged in
substance and unrepaired by this pass** — `spec-010:8` / `:491` / `:67` (the concurrent cycle's, and
only the maintainer can sequence the two at commit); `types/definition.py::DjangoTypeDefinition`'s
`fields_class` docstring reserving a pre-renumber card (source is read-only in this cycle); the
rationale's `## Standing notes` "three sites" bullet, deliberately stale under append-only and flagged
five lines above it (the one-`-`-line proof shows it unmodified again this pass); `spec-009:592-597`'s
registry-global `is_finalized` versus per-type `DjangoTypeDefinition.finalized`, reported-not-repaired
across five passes now. **And the one whose evidence inaction destroys:** no permanent test row pins
`async def get_queryset` → `SyncMisuseError` for a *default* `DjangoConnectionField` under
`await schema.execute`; the ready-made body at
`docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is gitignored and clears with
the cycle. **Card it before the cycle closes.** Not modified, moved, re-run, or deleted by this pass.

### Status

`planned`. The three dispatched corrections are closed as four clause edits in the permanent rationale,
each one a deletion or a one-clause narrowing; the spec is byte-unchanged and its lack of a twin was
checked rather than assumed; every gate, identity, and append-only proof re-runs clean. Worker 0 reads
`planned` on this item as "dispatch Worker 3".

---

## Review (Worker 3, pass 3)

Run 2026-08-16 by a fresh Worker 3 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-3.md`. **HEAD re-derived: `973d00b2`** (`git rev-parse HEAD`
at the start of this pass, not inherited from the dispatch). `git status --porcelain` is **140** entries.
`git stash` / `checkout` / `restore` / `worktree` were not used; the only HEAD reference is
`git show HEAD:<path>` into an out-of-repo scratch path. No file outside this pass's writable set was
edited, reverted, or `git checkout`ed; nothing under `docs/builder/temp-tests/` was touched, and the
gitignored `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is still on disk.
No `pytest` ran, with or without `--cov*` flags.

**Scope taken.** The four clause edits of `## Build report (Worker 1, apply-changes pass 2)` and nothing
else. The four original spec edits, the High's rewrite, and the enumeration's coverage map were audited
by two prior review passes and the final verification and were not re-opened. Every number below was
re-derived from the tree, not read off a prior report.

### High:

None.

### Medium:

None.

### Low:

Four, all **artifact-only** and all dispositioned **examined, not required**: none touches the spec, the
rationale, or any other permanent document, and none holds the item. They are recorded because three of
them are the cycle's own recurring class — a supporting clause whose command or count does not reproduce
as spelled — and the fourth is a supporting clause that undersells its own warrant.

#### Low 1 — `bld-009-r1b:1958-1962`: the `plan_optimizations` shortfall is attributed to the wrong module, and "three test modules" was not short

The apply pass writes: *"Four importers outside the package — and the count the final verification
recorded ('three test modules') is itself one short, because `tests/optimizer/test_walker.py` imports it
inside a parenthesized multi-line `from … import (…)` that a single-line `^from` anchor cannot see."*
Re-derived by AST rather than by grep, which is the only shape immune to both the multi-line and the
in-function import:

```
$ uv run python -  # ast.ImportFrom over every *.py outside .venv, name == 'plan_optimizations'
django_strawberry_framework/optimizer/extension.py 95
scripts/bench_optimizer_walk.py 180
scripts/bench_optimizer_walk.py 199
tests/optimizer/test_definition_order.py 9
tests/optimizer/test_multi_db.py 42
tests/optimizer/test_walker.py 30
package modules: 1   test modules: 3   other: 1   distinct non-package modules: 4
```

There are exactly **three** test modules, and the final verification (`:1646`) had already named all
three including `test_walker.py`. The importer its list actually missed is `scripts/bench_optimizer_walk.py`,
whose two imports are **indented inside function bodies** — a different grep-shape trap, and one the
apply pass's own pasted output at `:1950-1951` displays. So "four importers outside the package" is
correct and "'three test modules' is one short" is not; the diagnosis names the wrong module and the
wrong trap.

**Why it does not hold the item.** The remedy carries **no count at all** — `rationale:732-733` now reads
*"`plan_optimizations` is imported by no package module but `optimizer/extension.py`"*, and the AST run
above proves that population is exactly one module, `optimizer/extension.py:95`. Everything else in the
package that names the symbol is its own definition (`optimizer/walker.py:128`) or a docstring/comment
(`optimizer/__init__.py:14`, `optimizer/plans.py:135,259`, `optimizer/nested_fetch.py:38,291`). The
`### Dispatched findings checklist` box at `:114` also states it correctly ("three test modules and
`scripts/bench_optimizer_walk.py`"). Only the build report's narrative sentence is wrong, and `bld-*.md`
closes with the cycle (`START.md` "Temp artifact conventions"), which is the disposition the final
verification's Low 3 already set for this class.

#### Low 2 — `bld-009-r1b:1525` and `:1828`: "`git diff -- django_strawberry_framework/` is empty" does not reproduce

```
$ git diff --numstat -- django_strawberry_framework/ | wc -l
45
```

Forty-five package modules are modified in the working tree. They are the four concurrent cycles' and
the package-source session's work — out of scope under `AGENTS.md` L34, and untouched here — so the
**conclusion** the sentence supports ("this pass writes only documents") is right, but the command it
offers as proof answers the wrong question: it measures the whole tree, not the pass's footprint. The
claim that does reproduce is the one the ledger already carries — the item's entire working-tree
footprint is `…-rationale.md` at `-87` bytes / `-1` line, with the spec byte-unchanged. Same class as
Low 1, same disposition; recorded so a later pass does not re-raise it as new, and so R2/R4 spell this
proof as a footprint rather than a whole-tree diff.

#### Low 3 — `bld-009-r1b:1845-1847`: the wrap-trap claim was true before the edit and is false after it

*"`grep -c 'beat a cut'` returns **0** even in the rationale that contains the phrase, because it wraps
as `beat a\ncut`."* Post-edit the rationale returns **1**: correction 1 re-flowed the sentence, and
`:682` now carries `A replacement beat a cut here because the sketch needs a type for` on one line. The
claim was true of the pre-edit text — the recorded "Before" block at `:1876-1877` shows `beat a` ending
one line and `cut:` beginning the next — so this is a tense artifact of measuring before editing and
narrating after, not a false measurement. It is recorded only because the *method* it justifies is the
one that matters, and that method reproduces exactly (see `### What looks solid`).

#### Low 4 — `bld-009-r1b:1936-1937`: `forward_resolver` has three exits, not two, and the third makes the harm clause stronger

*"Both exits of `types/resolvers.py::_make_relation_resolver`'s `forward_resolver` return the row-bound
accessor."* There are three `return` statements: `types/resolvers.py:392` (`return getattr(root, field_name)`,
the no-sentinel fast path), `:404` (`return stub`, the FK-id elision stub from `_build_fk_id_stub`), and
`:420` (`return getattr(root, field_name)`). Two return the row-bound accessor; the third returns a stub.

The correction is not affected, and the omission understates its own warrant. Both sentinels the stub
path is gated on are stashed by the optimizer extension and by nothing else:

```
$ grep -rn 'DST_OPTIMIZER_FK_ID_ELISIONS|DST_OPTIMIZER_PLANNED' django_strawberry_framework/ \
    | grep -v types/resolvers.py
optimizer/_context.py:30,31   (definitions)
optimizer/extension.py:1226   self._stash_union(info.context, DST_OPTIMIZER_FK_ID_ELISIONS, fk_id_elisions)
optimizer/extension.py:1234   self._stash_union(info.context, DST_OPTIMIZER_PLANNED, planned_resolver_keys)
```

In the configuration the harm clause names — a schema built **without** `DjangoOptimizerExtension` —
`elisions` is empty and `planned` is `None`, so `:392` is the only reachable exit. The stub exit cannot
occur there at all. Artifact-only, no remedy required.

### The three corrections, verified

**Correction 1 — `rationale:682`, deleted not re-counted. Confirmed.**

```
docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md:682
from the authority and cannot drift. A replacement beat a cut here because the sketch needs a type for
the slot, and `RelationKind` is checkable from the cited symbol at the reader's desk.
```

The false definite description is gone and no corrected count replaced it. The surviving clause is the
entry's actual reason for replacing rather than cutting, and it is checkable at the reader's desk from
the cited symbol, which is the entry's own stated standard. **No replacement-count survives anywhere**:
`grep -n 'replacement'` over the rationale returns six lines (`:141`, `:234`, `:372`, `:477`, `:551`,
`:682`), every one of them a description of a single named remedy, none a population claim; `grep -n
'one place'` returns exactly one line, `:533`, graded below; `:777`'s "the one telling" is a claim about
the spec's seam map, and the spec's two `apply_type_visibility` sites (`:417` pointer, `:649` telling)
confirm it.

**Correction 2 — the harm clause's polarity, and the `forward single` scoping. Confirmed, and the
scoping is right.**

```
docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md:757-761
… leaving a forward single relation whose target **does** override `get_queryset`, read through
a schema built without `DjangoOptimizerExtension`, unfiltered on a path the sentence claimed was
covered.
```

Each conjunct re-derived at the symbol, in call order:

- `django_strawberry_framework/types/base.py:712-718` — `get_queryset` is the *"Default identity hook"*
  in as many words, so a target that does **not** override it has no rule to lose. The pre-edit clause
  was the vacuous half; the polarity swap is correct.
- `grep -c 'apply_type_visibility' django_strawberry_framework/types/resolvers.py` → **0**. The
  generated resolver composes no visibility on any cardinality.
- `grep -c 'DjangoOptimizerExtension' django_strawberry_framework/schema.py` → **0**. Nothing
  auto-installs the extension, so "built without" is a reachable configuration and condition (b) is
  materially load-bearing.
- **The scoping to forward single is right, and the unscoped inverse would have over-claimed.**
  `connection.py:1780` / `:1815` and `list_field.py:211` / `:217` call `apply_type_visibility_sync` /
  `_async` unconditionally — no optimizer sentinel, no extension check — so a default-shaped many-side
  relation is composed by the connection pipeline or the list field whether or not the optimizer is
  installed. Worker 1's stated reason for narrowing reproduces at the symbols.
- The narrowing is also in the **safe direction**: `reverse_one_to_one` is a second single-cardinality
  shape whose resolver (`types/resolvers.py:372`) is likewise unfiltered, so the clause understates the
  harm surface rather than overstating it. A harm claim that is narrower than the truth cannot be the
  over-reach this class of finding is about.

**Correction 3 — the two evidence spellings. Both re-derived.**

- `rationale:732-733` — *"imported by no package module but `optimizer/extension.py`"*. The AST run under
  Low 1 gives exactly one package importer, `optimizer/extension.py:95`. **True**, and count-free.
- `rationale:767-769` — the `grep` **command** is deleted and the eight module names are kept, exactly as
  dispatched. The enumeration is correct: tokenizing each package module and dropping
  `tokenize.COMMENT` / `tokenize.STRING` lines reproduces **8** distinct executable-invocation modules —
  `connection.py [1780, 1815]`, `filters/sets.py [2470, 2505]`, `list_field.py [211, 217]`,
  `mutations/resolvers.py [885]`, `optimizer/walker.py [383]`, `permissions.py [702]`,
  `types/relay.py [843, 864, 904, 929]`, `utils/querysets.py [2893, 2993, 3169, 3276, 3295]` — which is
  the listed set character-for-character. The raw command as previously spelled still reaches **nine**
  paths, the ninth being `forms/resolvers.py` (a docstring mention). Deleting the command and keeping
  the names is the right remedy: the names are the claim, and each one opens.

### The spec twin check, re-derived independently

Run as spelled against `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`; output reproduces the
apply pass's block line for line:

```
beat a cut : 0    replacement : 0        one place   : 1    plan_optimizations : 0
nothing else : 1  unfiltered : 0         apply_type_visibility : 2    eight : 0
```

Both non-zero hits opened and graded independently, without reading the apply pass's grades first:

- `spec:771` — *"Wrapping keeps the cascade below expressible in one place and costs nothing on a field
  no `FieldSet` manages"*. The `AdvancedFieldSet` resolver-wrapping argument, owned by
  `spec-054-fieldset-0_1_1.md`. Different subject, different predicate. **Not a twin.**
- `spec:634` — *"**The trigger is the explicit consumer call, and nothing else.**"* Layer 3's
  finalization contract, whose wording `spec-010-foundation-0_0_4.md` owns. **Not a twin.**
- The two `apply_type_visibility` sites are `:417` (the pointer this cycle installed) and `:649`
  (`### Layer 4`'s canonical telling) — the corrected clause's *target*, not a copy of it. **Not twins.**

`plan_optimizations`, `unfiltered`, `eight` and `replacement` do not occur in the spec at all. **No spec
twin exists**, and the spec measures byte-unchanged by two independent instruments (below). The wrap
trap the sweep was built around is real for the pre-edit text; see Low 3 for the one narration artifact.

### `rationale:533` — graded, and it is a note, not a finding

*"**`aggregates` does not exist yet**, and this is the one place in this pass where a spec claim was kept
rather than corrected"*.

**Grade: true statement that rhymes with the deleted Medium. No edit owed, and it should not be
re-opened.** Three grounds, in decreasing weight:

1. **Nothing in the document disproves it, which is the whole of what made `:682` a finding.** `:682`
   was contradicted *on the page* — `:697` "narrowed … not cut" fifteen lines below, `:739` "`### Decision 3`
   was **replaced** rather than cut" fifty-seven below, in as many words. I swept the same file for the
   `:533` predicate (`grep -n 'kept\|was left\|left standing\|not corrected\|deliberately'`) and every
   hit inside R1's `:167-666` region is explicitly a *different* category by the sentence that records
   it: `:399`'s kept `DjangoModelType` mentions and `:584`'s kept upstream class names are **prior-art
   citations that were never false** ("renaming them would have made the citations false"), not claims
   found wrong and retained; `:620`'s eight-of-eleven is a number kept **out** of the spec, the opposite
   operation. `:77`'s "What was kept" sits at line 77, inside HEAD's pre-cycle text, so it is not "this
   pass". No counterexample exists to find.
2. **Different predicate over a different population.** `:682` quantified over *remedy shapes* across
   every correction in the document — the largest population the record has, and one two adjacent
   entries enumerate. `:533` quantifies over one pass's *kept-because-owed* judgements, a predicate that
   requires the claim to be untrue of today's code **and** deliberately retained as an owed target
   outcome. `aggregates` is the only site meeting both halves; `AdvancedFieldSet` at `spec:769` is the
   nearest neighbour and the record at `:584` classifies it, on its own separate ground, as a citation.
3. **It sits in R1's `final-accepted` region.** Re-opening closed text needs evidence of falsity, not of
   grammatical resemblance, and there is none. Grading it exhaustively would mean re-deriving R1's
   103-row table, which is disproportionate against a claim no adjacent text contradicts.

Flagging it rather than repairing it was the right call by the apply pass. Recorded here so a later pass
does not re-open it as new.

### No regression, append-only, gates — every figure re-derived

| Obligation | Re-derived result |
|---|---|
| Ledger — spec | `wc -c -l` → **61,170 / 1,096**, identical to the final verification's reading ✓ |
| Ledger — rationale | `wc -c -l` → **60,356 / 828** ✓ |
| HEAD copies | `git show HEAD:` → spec **54,232 / 1,154**, rationale **12,273 / 208** ✓ |
| `--numstat` | spec **114 / 172** (unchanged from the final verification — the second independent instrument confirming the spec is byte-unchanged, not merely same-sized); rationale **620 / 0** ✓ |
| Identity 1 | `1,154 − 172 + 114 = 1,096` ✓ |
| Identity 2 | `208 + 620 = 828` ✓ |
| Per-edit deltas | reconstructed from the recorded before/after blocks and measured in Python: c1 **−33 / −1**, c3a **+5 / 0**, c2 **+30 / +1**, c3b **−89 / −1**; sum **−87 / −1**; `60,443 − 87 = 60,356` ✓ and `829 − 1 = 828` ✓ — every per-edit figure reproduces to the byte |
| Append-only, `−` lines | `git diff -- <rationale> \| grep -c '^-'` → **1**, and printing it gives `--- a/docs/SPECS/appx/…`. No HEAD line was deleted or modified, which subsumes any prefix check ✓ |
| Append-only, hunks | `-U0` → `@@ -166,0 +167,618 @@`, `@@ -185,0 +804 @@`, `@@ -186,0 +806 @@`; `618 + 1 + 1 = 620` = the numstat addition ✓ |
| Append-only, prefix | `head -166` working `cmp` `head -166` HEAD copy → **exit 0** ✓ |
| Glossary gate | `check_spec_glossary.py --spec …spec-009…` → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0** ✓ |
| Comma gate | `check_trailing_commas.py --check` on **both** documents → **exit 0** ✓ |
| Numbering | `^### (Layer\|Phase\|Decision) N` → **11 / 8 / 6**, printed in file order: Layers 1-11 at `:576…:799`, Phases 1-8 at `:903…:985`, Decisions 1-6 at `:995…:1010`. No gap, no duplicate, none renumbered ✓ |
| In-page anchors | `grep -c '](#'` → **0 / 0**, so none can dangle ✓ |
| Link defs | independent parser (single `<!-- LINK DEFINITIONS -->` delimiter, uses harvested from the raw body so a ref-style use inside a code span still counts, `#fragment` stripped before the disk check): spec **25 defs / 25 uses**, rationale **11 / 11**; **0** missing, **0** orphan, **0** dead ✓ |
| Raw `path:NN` | `grep -nE '[A-Za-z0-9_/.-]+\.(py\|md):[0-9]+'` less `file:///` → **no match** in either permanent document ✓ |
| Cross-spec anchors | five, both directions, each re-read at the moment of dependence. `spec-010:67` cites `### Layer 3: Finalization trigger`; `spec-010:468` cites `### Decision 6: fail loudly`; `spec-009:99` cites `### Must redo (not augment)`; `:634` cites `## Strawberry finalization strategy`; `:870` cites `### Unresolved-target error format`. Heading-anchored `grep -cE '^#'` returns **1** for each of the five targets, so every anchor exists and is unique ✓ |
| Provenance | `git log --stat` over both paths → newest commit touching either is still **`f3c94642`**, HEAD at `973d00b2`. Nothing swept into a concurrent commit; `git status` alone was not used as the test ✓ |

**Failability proofs.** Not applicable to a documentation pass: the four edits introduce no boundary,
guard, gate, or rejection path, so the mandatory re-run floor is computed over an empty set and an empty
re-run set is legal here by `docs/builder/worker-3.md` `### Reading is necessary, not sufficient`.

**Hot-path budget.** Not applicable to a documentation pass: the plan declares no hot path and this item
writes no code, so no before/after number is owed.

**Test staleness.** Swept independently rather than against the item's file list, per the role file: the
item changes no symbol name, no public identifier, and no behavior, so no test tree can have gone stale.
`git diff --numstat -- tests/ examples/` carries only the concurrent cycles' work, none of it reachable
from this item's four clause edits.

### `### Dispatched findings checklist` — three boxes, four edits, mapping holds

Thirteen boxes now: four self-derived (`:90-93`), six from the apply-changes pass (`:99-104`), three from
apply-changes pass 2 (`:112-114`). The pass-2 block is appended under its own demarcating paragraph at
`:106-110`, which states the three-boxes-to-four-edits mapping and its reason (correction 3 is two
clauses by the dispatch's own wording). Mapping walked one by one:

- Medium box (`:112`) → `rationale:682` deletion. Verified at the line; the box says "**Deleted, not
  re-counted**" and the line carries no count.
- Low 1 box (`:113`) → `rationale:757-761` polarity swap. Verified at the line, and the box's own
  statement of what was wrong ("the default identity hook loses no rule") matches `types/base.py:718`.
- Low 2 box (`:114`) → `rationale:732-733` **and** `rationale:767-769`. Both verified at the lines.

**No box lacks an edit and no edit lacks a box; every box is `- [x]`, so no deferral reason is owed.**
No prior box was rewritten: the pass-2 additions are strictly below `:105`, the ten earlier boxes read
consistently with the final verification's own "ten boxes, ten edits, one-to-one" audit at `:1587-1607`,
and none of their contracts is reversed or narrowed. Worth recording: the Low 2 box at `:114` states the
importer population **correctly** ("three test modules and `scripts/bench_optimizer_walk.py`") where the
build report's prose at `:1958-1962` does not — Low 1 above is confined to the narrative.

### DRY findings

**None.** All four edits are subtractions or one-clause narrowings and introduce no shape: correction 1
removes a population claim, 3a removes an absolute, 3b removes a command spelling and keeps the
enumeration a reader can open, and correction 2 replaces one clause with another of near-equal length
(+30 bytes) rather than adding a new mechanism sentence. Correction 2 is the one place a duplication
could have entered — restating "returns the row-bound accessor with no visibility call in it" inside the
rejected alternative — and the apply pass explicitly declined to, pointing at the entry's own statement
45 lines above. That is the right call and the same de-duplication the whole item performs.

**Existence challenge:** does not arise. No new abstraction, registry, indirection, vocabulary term, or
convention is introduced; the net effect of the item is `-87` bytes.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are
unchanged. No public export was added, removed, or renamed by this item, which writes no code at all.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md. Confirmed mechanically:
`git diff --numstat -- CHANGELOG.md` returns no rows.

### Documentation / release sanity

Applies — the item's whole footprint is one documentation file.

- **Version strings and card IDs.** No version string is touched; `pyproject.toml` and
  `django_strawberry_framework/__init__.py` are not in the item's diff. The card annotations the edited
  region names (`TODO-BETA-057-0.1.3`) are untouched by these four edits.
- **KANBAN.** No card movement; `git status --porcelain KANBAN.md` is empty.
- **Standing docs.** `docs/TREE.md`, `KANBAN.md`, `CHANGELOG.md`, `pyproject.toml`, `TODAY.md` and
  `BACKLOG.md` are all clean. `docs/GLOSSARY.md` **is** modified in the working tree — that is a
  concurrent cycle's render (the glossary is DB-generated), not this item's, and the glossary gate still
  passes at **23 terms** against the spec, so no term this item's region depends on has been dropped.
- **Links.** The item introduces no new cross-file link and no in-page anchor. All 11 rationale link
  definitions and all 25 spec definitions resolve on disk, with 0 orphans — re-derived above.
- **Archival.** The spec and its rationale are already at their archived homes (`docs/SPECS/` and
  `docs/SPECS/appx/`); the item neither moves nor re-relativizes anything.
- **Verbatim copies.** None; no fenced block was dropped in from the spec, so the four-backtick outer
  fence rule does not arise. The one fenced construct removed (3b's `grep` command) was deleted, not
  relocated.
- **Stale staging language.** No "coming soon" / "planned" / old-version wording is introduced. The
  rationale is not a script-rendered doc, so the docstring-staging check does not apply.

### What looks solid

- **Every stated number reproduces to the unit** — the ledger, both closing identities, the numstat, the
  hunk arithmetic, the four per-edit byte and line deltas, and all seven gates. Reconstructing the
  per-edit deltas from the recorded before/after blocks and measuring them independently gave
  `−33 / +5 / +30 / −89 = −87` and `−1` line, landing on the file's measured `60,356 / 828` exactly.
  That is the second consecutive pass whose figures survive a mechanical recount unchanged.
- **The append-only proof is still the strong form.** Exactly one `-` line and it is the `--- a/` header,
  which subsumes any prefix comparison; the `head -166` `cmp` is a redundant confirmation rather than
  the proof.
- **The remedy shapes are right, and they are the ones this cycle's history argues for.** Three of four
  edits delete a claim rather than restate it; the fourth narrows one clause. Nothing written to a
  permanent document this pass asserts a number, which structurally forecloses the failure mode that
  produced five false corrections on this cycle. Correction 3b in particular keeps the eight module
  names — which a reader opens one by one — and deletes only the command that mis-supported them, which
  is the right half to cut.
- **The scoping judgement Worker 1 asked for a second opinion on is correct**, and correct for the reason
  given: `connection.py:1780`/`:1815` and `list_field.py:211`/`:217` compose visibility with no optimizer
  sentinel in sight, so an unscoped harm claim really would have over-reached on the many side. The
  narrowing also errs safe, understating the harm surface by omitting `reverse_one_to_one`.
- **The spec twin sweep was run rather than assumed**, its output reproduces line for line, and both
  non-zero hits were opened and graded — correctly — rather than dismissed on the count.
- **The deferred item was flagged, not silently repaired.** Repairing `rationale:533` inside R1's closed
  region on a rhyme would have been a fresh unreviewed claim in a permanent document, which is the exact
  failure this item closes.

### Temp test verification

- **No temp tests were created or run this pass.** The item changes no code and no behavior, so there is
  no behavior for a temp test to prove; verification was reading plus mechanical re-derivation at the
  symbols (AST import walk, `tokenize`-filtered invocation scan, byte-delta reconstruction).
- `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is **present and untouched**.
  Nothing under `docs/builder/temp-tests/` was created, modified, moved, re-run, or deleted. Its
  disposition is unchanged and it remains the subject of escalation 5 below.

### Notes for Worker 1 (spec reconciliation)

- **No spec reconciliation is owed.** The spec is byte-unchanged, confirmed by two independent
  instruments (`wc -c -l` **61,170 / 1,096** and `git diff --numstat` **114 / 172**, both identical to
  the final verification's readings), and its lack of a twin was re-derived here rather than accepted.
- **The five escalations carry forward unchanged in substance and unrepaired**, exactly as the apply
  pass records them: (1) `spec-010:8` / `:67` / `:491`, owned by the concurrent spec-010 cycle and
  sequenceable only by the maintainer at commit; (2) `types/definition.py::DjangoTypeDefinition`'s
  `fields_class` docstring reserving a pre-renumber card, source being read-only in this cycle;
  (3) the rationale's `## Standing notes` "three sites" bullet, deliberately stale under append-only and
  flagged in-file five lines above it, shown unmodified again by the one-`-`-line proof; (4)
  `spec-009:592-597`'s registry-global `is_finalized` versus per-type `DjangoTypeDefinition.finalized`,
  reported-not-repaired across six passes now.
- **Escalated: the one whose evidence inaction destroys.** No permanent test row pins
  `async def get_queryset` → `SyncMisuseError` for a *default* `DjangoConnectionField` under
  `await schema.execute`. The ready-made body at
  `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is gitignored and clears with
  the cycle. **Card it before the cycle closes**; the resolution paths are (a) promote it to
  `tests/` or `examples/fakeshop/test_query/` in a follow-up card, or (b) record an explicit decision
  that the boundary stays unpinned. This is the fourth pass to say so and the only escalation whose cost
  rises with delay.
- **Report-only, no action asked:** the four Lows above are all confined to `bld-*.md`, which closes with
  the cycle. If R2 or R4 wants one behaviour change out of them, it is Low 2's: spell "this pass wrote no
  source" as the item's **footprint** (the two-document diff and its byte delta), not as
  `git diff -- django_strawberry_framework/`, which cannot be empty on a tree carrying five concurrent
  sessions.

### Review outcome

`review-accepted`.

All three dispatched corrections are closed by four clause edits in the permanent rationale, and every
one of them is a subtraction or a one-clause narrowing — the shape least able to introduce a sixth false
correction, which is what the proportionality of this pass turned on. The Medium's false definite
description is **deleted, not re-counted**, and no replacement-count survives anywhere in the file. The
harm clause now names the harmful configuration, and its deliberate scoping to forward single relations
re-derives at the symbols in both directions: the generated resolver composes no visibility, nothing
auto-installs the optimizer extension, and the connection and list-field seams compose the many side
with or without it. Both evidence spellings re-derive — one package importer of `plan_optimizations` by
AST, eight executable-invocation modules by tokenizer, matching the retained enumeration
character-for-character. The spec is byte-unchanged by two instruments and carries no twin, checked as
spelled. Every gate, identity, per-edit delta, and append-only proof reproduces to the unit; the
checklist's thirteen boxes map one-to-one onto fourteen edits with the mapping stated and no prior box
rewritten. `rationale:533` is graded a note: it rhymes grammatically with the deleted Medium but no text
in the document contradicts it, its predicate and population both differ, and it sits in a closed region.

The four Lows are artifact-only, dispositioned examined-not-required, and none touches the spec, the
rationale, or any other permanent document. Nothing on this item is open.

---

## Final verification (Worker 1, pass 2)

Run 2026-08-16 by a fresh Worker 1 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-1.md`. **HEAD re-derived: `973d00b2`** (`git rev-parse HEAD`
at the start of this pass, not inherited from the dispatch; unchanged from Worker 3's pass-3 reading).
`git status --porcelain` is **141** entries; nothing outside this cycle's writable set was edited,
reverted, or `git checkout`ed. `git stash` / `checkout` / `restore` / `worktree` were not used; every
HEAD reference is `git show HEAD:<path>` into an out-of-repo scratch path. Nothing under
`docs/builder/temp-tests/` was touched, and
`docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is still on disk at its
unchanged 20:42 mtime.

**This item runs no tests and changes no code.** No `pytest` was invoked in this pass, with or without
`--cov*` flags, so `## Final verification job` step 5's focused run is vacuous and is recorded as such
rather than skipped silently. Step 6's staged-anchor sweep belongs to **R4** (`## Artifact list`: "the
staged-anchor sweep into R4") and was deliberately not duplicated here.

**The item's footprint, stated as a footprint** — Worker 3's pass-3 Low 2 is right that
`git diff -- django_strawberry_framework/` is not the proof and does not reproduce (**45** package
modules are dirty from the concurrent sessions). Re-measured the way that does reproduce: the item's
entire working-tree footprint is `git diff --numstat` **114 / 172** on the spec and **620 / 0** on the
rationale, plus this artifact (`??`). No source file, test file, or third document is in it.

**Spec status-line re-verification (per-spawn duty).** Lines 1-5 re-read. The opener describes the
rationale companion, the four finalization sites, and the six scrubbed mechanisms. Nothing R1b landed
falsifies any of it. **No edit owed.**

**Nothing was edited by this pass.** Every finding and note below is recorded, not repaired. Four prior
final verifications on this cycle each edited nothing and each either produced the clean result or found
the defect; a custodian edit made here would be a fresh unreviewed claim in a permanent document, which
is the failure this item exists to close.

### Method — the whole R1b diff read cold, in file order, at its symbols

Not the prior findings' sites, and not only pass 2's four clause edits. The five changed spec lines and
the **whole** R1b rationale region (`:667-784`; R1's region is `:167-666` and closed under R1's
`final-accepted`, HEAD's pre-cycle text is `:1-166` and `:785-828`) were read in file order, with every
clause naming a checkable symbol opened at that symbol. That is what produced the one finding, which
sits in text pass 2 did not touch and which two review passes and one final verification read without
opening the phase vocabulary it names.

### Verification obligations — each proof re-run here, not read off a prior report

| Obligation | Result |
|---|---|
| Ledger — spec | `wc -c -l` → **61,170 / 1,096** ✓ |
| Ledger — rationale | `wc -c -l` → **60,356 / 828** ✓ |
| HEAD copies | `git show HEAD:` into an out-of-repo path → **54,232 / 1,154** and **12,273 / 208** ✓ |
| `--numstat` | spec **114 / 172**; rationale **620 / 0** ✓ |
| Identity 1 | `1,154 − 172 + 114 = 1,096` ✓ |
| Identity 2 | `208 + 620 = 828` ✓ |
| Cross-item byte chain | R1 closed at **61,082 / 1,096** (`bld-009-r1:5273`); `61,082 + 54 + 34 = 61,170`, which is what the file measures ✓ |
| Append-only, `-` lines | `git diff -- <rationale> \| grep -c '^-'` → **1**, and printing it gives `--- a/docs/SPECS/appx/…` — no HEAD line deleted **or modified** ✓ |
| Append-only, hunks | `-U0` → `@@ -166,0 +167,618 @@`, `@@ -185,0 +804 @@`, `@@ -186,0 +806 @@`; `618 + 1 + 1 = 620` = the numstat addition ✓ |
| Append-only, prefix | `head -166` working `cmp` `head -166` HEAD copy → **exit 0** ✓ |
| Glossary gate | `check_spec_glossary.py --spec …spec-009…` → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0** ✓ |
| Comma gate | `check_trailing_commas.py --check` on **both** documents → **exit 0**; `shasum -a 256` and `wc -c -l` identical before and after both gate runs ✓ |
| Numbering | `^### (Layer\|Phase\|Decision) N` → **11 / 8 / 6**, printed in file order (`Layer 1`-`11` at `:576…:799`, `Phase 1`-`8` at `:903…:985`, `Decision 1`-`6` at `:995…:1010`); no gap, no duplicate, none renumbered ✓ |
| In-page anchors | `grep -c '](#'` → **0 / 0**, so none can dangle ✓ |
| Link defs | independent parser (single `<!-- LINK DEFINITIONS -->` delimiter; uses harvested from the raw body so a ref-style use inside a code span still counts; `#fragment` stripped before the disk check): spec **25 defs / 25 uses**, rationale **11 / 11**; **0** missing, **0** orphan, **0** dead ✓ |
| Raw `path:NN` | `grep -nE '[A-Za-z0-9_/.-]+\.(py\|md):[0-9]+'` less `file:///` → **no match** in either permanent document ✓ |
| Cross-spec anchors | five, both directions, re-derived at the moment of dependence (`spec-010` is under a concurrent cycle). Citing lines read in full: `spec-010:67` → `### Layer 3: Finalization trigger`, `spec-010:468` → `### Decision 6: fail loudly`; `spec-009:99` / `:634` / `:870` → spec-010's `### Must redo (not augment)` / `## Strawberry finalization strategy` / `### Unresolved-target error format`. **Heading-anchored** `grep -cE '^<heading>$'` returns **1** for all five, so every anchor exists and is unique ✓ |
| Provenance | `git log --stat` over both paths → the newest commit touching either is still **`f3c94642`**, HEAD at `973d00b2`; the two commits behind it are `e1f9ed26` and `abb0dd12`. Nothing was swept into a concurrent commit. `git status` alone was not used as the test ✓ |
| Per-edit bytes | `awk NR==n \| wc -c`: `:394` **117**, `:417` **490**, `:610` **78**, `:930` **130**, `:1002` **362**; HEAD's `:393` **90** and `:651` **115**, so `+27` and `−37` reproduce against HEAD directly ✓ |
| Structural confirmation of the spec's edit set | the spec's `--numstat` moved `112 / 170` (R1) → `114 / 172` (R1b) and has not moved since. Exactly **two** HEAD lines were modified across all of R1b (`:394`, `:610`); the other five edits (`:417`, `:930` ×2, `:1002` ×2) all landed on R1-added lines, which cannot move the counts. That is an independent check on "seven edits and no eighth" ✓ |

**Enumeration re-derived by parsing the tables, not by reading them.** A row is a `|`-leading line
outside a fence whose header row begins `| Site |`; bucket on the last cell with `*` stripped; the
`### Revised denominator` summary table is excluded by that header rule. Result: **119** rows — **66**
`true`, **5** `FALSE`, **34** `judgement`, **10** `note (upstream)`, **4** `out of scope`;
`66 + 5 + 34 + 10 + 4 = 119`, opened **71**. Line coverage by expanding every `:NNN` / `:NNN-NNN` in
column 1 and unioning: **842 of 1,096**, **108** gaps / **254** lines; the largest residual gaps hold
**4** non-blank lines (`630-637` and `598-603`). **117** of the 119 rows carry a `:NNN` in column 1, the
two exceptions being the numbering row and the cross-spec-anchor row. Every figure reproduces to the
unit — the third consecutive pass whose counts survive a mechanical recount unchanged.

### Planned steps — all landed, none rejected

`### Implementation steps` 1-4 are the four spec edits, verified at the lines; step 5 is the three
appended rationale entries (`:667`, `:688`, `:702`); step 6 is the gate / proof / ledger block, re-run
independently above. The apply-changes pass added three further spec edits and one further rationale
entry, and apply-changes pass 2 added four clause edits — every one of them dispatched by a recorded
finding. **No step was rejected**, so no deferral reason is owed under `## Final verification job`
step 3's last clause.

### `### Dispatched findings checklist` audit — thirteen boxes, fourteen edits, mapping stated

Self-derived on this item, so the audit runs against the diff rather than a spec checklist. The three
boxes appended by pass 2 sit under their own demarcating paragraph (`:106-110`) which states the
three-boxes-to-four-edits mapping and its reason — correction 3 is two clauses by the dispatch's own
wording. Each box opened at the current line:

- `:610` → `relation_kind: RelationKind  # the alias in utils.relations, five members`; HEAD's `:651` is the quoted `Literal[...]` line character-for-character.
- `:394` → `- [schema audit][glossary-schema-audit] can name the exact relation fields whose target model has no registered type`; HEAD's `:393` is the quoted `report exact unfinalized or unresolved fields` line.
- `:930` → `visibility composition` absent, and `in the cardinality-correct spelling` present (the Low 2 box).
- `:1002` → `, visibility composition, and arguments` absent, and `queryset-owning components` present (the Consequential box).
- High (rationale visibility argument) → rewritten at `:702-761`: the five-of-eight list, both "reaches none of them" absolutes and the old harm clause are all gone.
- Medium `:417` → spec edit **plus** the new rationale entry at `:763`.
- Medium `MANY_SIDE_RELATION_KINDS` → `:674-677` quotes `frozenset({"many", "reverse_many_to_one", "generic"})` and carries the "two of those three / the sketch's own `"many"` is the third" framing.
- Low 1 (apply pass) → explicitly no document edit; disposition recorded in the build report.
- Medium (pass 2) → `:682` deletion; the line carries no population claim and no replacement count.
- Low 1 (pass 2) → `:757-761` polarity swap.
- Low 2 (pass 2) → `:732-733` **and** `:767-769`.

**No box lacks an edit and no edit lacks a box.** The permanent document changes are exactly seven
spec-line replacements and four rationale entries plus four in-place clause corrections; each maps to a
box. Every box is `- [x]`, so no deferral reason is owed. No prior box was rewritten — the pass-2
additions are strictly below `:105` — and none of R1's sixteen contracts is reversed: `:930` and
`:1002` were narrowed further in the same direction, never reverted.

### Cold read of the four clause edits of pass 2, at their symbols

- **Correction 1, `rationale:682`.** Now `A replacement beat a cut here because the sketch needs a type for the slot, and `RelationKind` is checkable from the cited symbol at the reader's desk.` The false definite description is deleted and no corrected count replaced it. Swept the whole file: `grep -n 'replacement'` returns six lines (`:141`, `:234`, `:372`, `:477`, `:551`, `:682`), every one a description of a single named remedy; `grep -n 'one place'` returns exactly one, `:533`, graded below. **True and count-free.**
- **Correction 2, `rationale:757-761`.** `types/base.py::DjangoType.get_queryset` is a documented identity hook, so the pre-edit polarity named the harmless corner; the inverse is the harmful one. The scoping to **forward single** re-derives in both directions: `types/resolvers.py` carries **0** `apply_type_visibility` and **0** async markers, `schema.py` carries **0** `DjangoOptimizerExtension`, and `connection.py:1780`/`:1815` plus `list_field.py:211`/`:217` invoke the pair with no optimizer sentinel — so a default-shaped many-side relation really is composed with or without the walker and an unscoped inverse would have over-reached. The narrowing also errs safe by omitting `reverse_one_to_one`. **True.**
- **Correction 3a, `rationale:732-733`.** `imported by no package module but `optimizer/extension.py``. Re-derived by AST over every `*.py` outside `.venv` (`ast.ImportFrom`, name `plan_optimizations`): package importers = **1**, `optimizer/extension.py:95`. **True, and count-free.**
- **Correction 3b, `rationale:765-769`.** The command spelling is deleted and the eight module names kept. Re-derived by tokenizing each package module and dropping `tokenize.COMMENT` / `tokenize.STRING` lines: executable invocations of `apply_type_visibility_sync` / `_async` live in exactly `connection.py`, `filters/sets.py`, `list_field.py`, `mutations/resolvers.py`, `optimizer/walker.py`, `permissions.py`, `types/relay.py`, `utils/querysets.py` — **8**, the listed set character-for-character. `forms/resolvers.py:32` is a docstring mention, opened and confirmed. The entry's characterisations of the three non-relation-read seams also hold at the lines (`permissions.py:702` is inside the cascade edge walk, `filters/sets.py:2470` inside `_iter_visibility_steps`, `mutations/resolvers.py:885` inside the write path's `pin_write_queryset`). **True.**

### Cold read of the five changed spec lines, at their symbols

- **`:394`** — `check_schema` (`optimizer/extension.py:1265-1312`) walks `_collect_schema_reachable_types(schema)` and appends exactly one warning shape, `f"{type_cls.__name__} ({_model.__name__}.{field_name}) has no registered target DjangoType"`. The replacement text is that condition. **True.**
- **`:417`** — `types/resolvers.py` carries **0** `apply_type_visibility` and **0** async markers; `utils/querysets.py::SyncMisuseError` exists and is raised on the sync path. "Runs at the queryset-owning seams `### Layer 4` names, never inside the generated resolver" holds, and `:415`'s "it is not repeated here" is restored — `:417` is the next non-blank line after it and now points rather than repeats. **True.**
- **`:610`** — `utils/relations.py` defines `RelationKind: TypeAlias = Literal["many", "reverse_many_to_one", "reverse_one_to_one", "forward_single", "generic"]`. **True.**
- **`:930`** — `types/converters.py::resolved_relation_annotation` returns `list[target_type]` / `target_type | None` / `target_type`, which is Layer 4's "cardinality-correct spelling"; `types/resolvers.py::_attach_relation_resolvers` installs one generated resolver per relation in `selected_fields`. **True.** Examined and not raised (unchanged from the prior pass): `_attach_relation_resolvers` skips `skip_field_names`, so "every exposed relation" is not literally exhaustive — the carve-out exists so a consumer override is not clobbered, the subject is *generated* relation fields, and Layer 4's own resolution bullet is scoped the same way.
- **`:1002`** — same two symbols plus `types/finalizer.py::_synthesize_relation_connections` for the argument seam. "Queryset-owning components" is apt for both the visibility appliers and the argument owner, and `optimizer/walker.py::_build_child_queryset` is a module-level `def` (`walker.py:350`), i.e. genuinely not a field. **True.**

### Worker 3's four Lows — grading confirmed, and each checked for a twin in the permanent rationale

That check is what decides whether "artifact-only" is the right grading, so it was run per Low rather
than asserted for the set. **None of the four has a twin in the spec or the rationale**, and all four
reproduce as Worker 3 recorded them.

1. **The `plan_optimizations` diagnosis (`:1958-1962`).** Confirmed wrong in the direction Worker 3 states, and the AST run is the instrument: the importers are `optimizer/extension.py:95` (package), `tests/optimizer/{test_walker.py:30, test_multi_db.py:42, test_definition_order.py:9}` (**three** test modules, exactly what the final verification named at `:1646`), and `scripts/bench_optimizer_walk.py:180,199`, whose two imports are **indented inside function bodies** — the importer the final verification's list actually missed, and a fifth grep-shape trap on this cycle. Separately confirmed that the *grep* the apply pass pasted cannot see `test_walker.py:30`, because its name sits inside a parenthesized multi-line `from … import (…)` — so both traps are real and the report attached the wrong one to the wrong module. **No twin:** the applied clause carries no count at all, and the population it does claim (one package importer) is exactly true.
2. **"`git diff -- django_strawberry_framework/` is empty" (`:1525`, `:1828`).** Reproduced as false — **45** package modules are dirty from the concurrent sessions. The conclusion it supports is right; the command measures the tree rather than the pass. **No twin:** `grep -n 'git diff'` over the rationale returns **0**, and the spec carries no such claim. This pass states the item's footprint instead, above.
3. **The wrap-trap claim (`:1845-1847`).** `grep -c 'beat a cut'` now returns **1**, at `:682` — because correction 1 re-flowed the line. The recorded "Before" block at `:1876-1877` shows `beat a` ending one line and `cut:` beginning the next, so the claim was true of the pre-edit text and is a tense artifact of measuring before editing and narrating after. **No twin:** the narration exists only in this artifact.
4. **`forward_resolver` has three exits (`:1936-1937`).** Confirmed at `types/resolvers.py`: `return getattr(root, field_name)` on the no-sentinel fast path, `return stub` on the FK-id elision path, and `return getattr(root, field_name)` after `_check_n1`. Both sentinels the stub path reads (`DST_OPTIMIZER_FK_ID_ELISIONS`, `DST_OPTIMIZER_PLANNED`) are stashed by `optimizer/extension.py` and by nothing else, so in the configuration the harm clause names — a schema built **without** `DjangoOptimizerExtension` — the stub exit is unreachable and the omission understates its own warrant, exactly as Worker 3 says. **Near-twin examined and graded a note, not a finding:** `rationale:711-713` says each of the three emitted shapes "returns the row-bound accessor with no visibility call in it". It states no exit count; its load-bearing predicate ("no visibility call") is exactly true and `grep -c`-verified at 0; and "returns the row-bound accessor" is `### Layer 4`'s own vocabulary at `spec-009:649`, accepted text graded `true` by three passes. The same shorthand is equally loose for `many_resolver`, which returns `bounded_rows(...)` of those rows — so tightening it would be a rewrite of an accepted phrase rather than the correction of a false clause. Recorded so a later pass does not re-open it as new.

### `rationale:533` — Worker 3's "note, not a finding" grading confirmed

Re-derived rather than accepted. `:533` reads *"this is the one place in this pass where a spec claim
was kept rather than corrected"*, and it survives all three tests the deleted `:682` failed. **(a) No
counterexample exists on the page**: sweeping the file for the predicate (`kept`, `was left`, `left
standing`, `not corrected`, `deliberately`, `retained`, `survives`) returns, inside R1's `:167-666`
region, only `:399` and `:584` — prior-art citations that were never false, classified as such by the
sentences that record them — and `:620`, a number deliberately kept **out** of the spec, the opposite
operation. `:77` and `:151` are HEAD's pre-cycle text (`:1-166`), so they are not "this pass" at all,
and `:151`'s "re-measured and kept" substance is a claim that *holds*, not one found wrong and retained.
`:682`, by contrast, was contradicted in as many words at `:697` and `:739`. **(b) Different predicate
over a different population** — remedy shapes across every correction in the document, versus one pass's
kept-because-owed judgements. **(c) It sits in R1's `final-accepted` region**, and re-opening closed text
needs evidence of falsity rather than of grammatical resemblance. Flagging rather than repairing it was
the right call.

### The finding this pass adds — Medium, in text pass 2 did not touch

**`rationale:705-708` attributes the annotation seam to the wrong finalizer phase.** The sentence
opening the rewritten Phase 3 / Decision 3 entry reads:

> The finalizer generates the annotation (`types/converters.py::resolved_relation_annotation`) and the
> resolver (`types/resolvers.py::_attach_relation_resolvers`) for every exposed relation, in the
> cardinality-correct spelling, **at finalizer Phase 2**.

The trailing adverbial governs both named seams, and it is false for the first of them.
`resolved_relation_annotation` has exactly **one** call site in the package —
`types/finalizer.py:775` — and it sits inside **Phase 1**'s failure-atomic pending-relation walk, after
the `unresolved` raise and before `registry.discard_pending(...)`. `types/finalizer.py`'s own module
docstring says so in as many words: *"Phase 1 (failure-atomic): walk `registry.iter_pending_relations()`
and classify each pending record as `unresolved` …, `consumer_authored` …, or `resolved` (target
registered; **rewrite the synthesized annotation via `resolved_relation_annotation`**)"*, with
`_attach_relation_resolvers` assigned to Phase 2 by the next bullet. The source itself marks the
boundary: the `# Phase 2 runs BEFORE Phase 2.5` comment introduces the resolver loop, which follows the
annotation rewrite.

**Why it is a defect and not a scope judgement.** Every other clause this pass graded a note is true
under its stated scope; this one is false under every reading, because the phase it names is not the
phase the code runs in. It is also the checkable kind: a phase number attached to a named symbol whose
owning module states the phase vocabulary in its docstring. And the entry treats those numbers as
precise — its own generalisable rule at `:752-754` is *"Phase 2.5 re-shapes what Phase 2 attached"*, and
Worker 3's pass 2 spent a paragraph distinguishing the finalizer's internal `Phase 1 / 2 / 2.5 / 3` axis
from the spec's `### Phase 1`-`8` migration numbering. A reader who takes the sentence at face value
also mislocates the failure-atomic boundary, since Phase 1 is the phase that raises *before* any class
object is mutated.

**Why Medium.** It is not a claim about a security or data-isolation boundary and no reader concludes
anything unsafe from it, so it is not High — the entry's conclusion (the finalizer composes no
visibility) is untouched, as are all four spec edits. It is Medium on the ground `spec-009:417` and
`rationale:682` were: a false, symbol-anchored mechanism claim in a **permanent** document, of the exact
class this item exists to remove, written by a fix pass. It is the **sixth** correction-pass clause on
this cycle to be false, after `:385`, `:418`, the reversal's argument, `:1002`'s "whichever field", and
`:682`'s "the one place".

**How it survived.** It was written by the apply-changes pass (artifact `:1031`, "generates annotation
and resolver **at finalizer Phase 2**"), and two review passes plus the prior final verification
re-derived the entry's *other* mechanism claims — `plan_relation`'s test order, `_plan_prefetch_relation`'s
early return, `_build_child_queryset`'s branch, `_synthesize_relation_connections`'s gate,
`DEFAULT_RELATION_SHAPE`, `schema.py`'s zero extension references — without opening the phase vocabulary
the same sentence asserts. Reading the region cold and in file order, rather than at the previously
named sites, is what found it: the detection rule to carry forward is that **a phase, stage, or ordinal
attached to a named symbol is a claim, and the module docstring that owns the phase vocabulary is the
authority to open.**

**Recommended remedy — scope the phase to the resolver, or cut it.** The cheapest true form moves the
number into the seam it belongs to: *"generates the annotation (`resolved_relation_annotation`, in
Phase 1's pending-relation walk) and installs the resolver (`_attach_relation_resolvers`) at Phase 2"*.
If the apply pass prefers this cycle's standing preference for subtraction, *"at finalization"* alone
carries everything the entry's argument needs and asserts no ordinal — the phase number is load-bearing
only for the later `Phase 2.5 re-shapes what Phase 2 attached` rule, which is about the **resolver** and
survives either way. **Do not write a new phase claim for the annotation unless it is re-derived**; the
verified fact is `types/finalizer.py`'s Phase 1 bullet naming `resolved_relation_annotation`, and the
single call site at `types/finalizer.py:775`.

### Two further notes, recorded rather than raised

- **`rationale:359-360`, in R1's closed region, is the nearest surviving relative of the `:417` shape.** It says the colored runner pair "is applied by `connection.py`, `list_field.py`, and `types/relay.py` — the fields that own the queryset". Measured: the **async** twin's external appliers are those three **plus** `filters/sets.py:2505` — four, not three. Graded a **note, not a finding**, on the standard this pass applied to `:533` and Worker 3 applied to `### Layer 4`'s `:649` bullet: the appositive scopes the population to queryset-owning *fields*, and `filters/sets.py` is a `FilterSet` (the related-filter scope boundary), not a field — so it is complete as scoped, it sits in a `final-accepted` region, and re-opening closed text needs falsity rather than resemblance. Worth carrying into R4 as the one enumeration of this shape still standing in a permanent document.
- **"Five cross-spec anchors, `grep -c` → 1 each" is loose in its spelling** in the perform and apply passes. A plain `grep -c` for the two spec-009 targets returns **5** (`### Layer 3: Finalization trigger`, four of them in-body pointers at `:642`, `:674`, `:999`, `:1015`) and **2** (`### Decision 6: fail loudly`, one an in-body pointer at `:441`). Heading-anchored — `grep -cE '^<heading>$'` — all five return **1**, which is the load-bearing property (the anchor exists and is unique), and Worker 3's pass 3 spelled it that way. Artifact-only, no edit owed; recorded so a later pass re-running the check does not read the discrepancy as drift.

### Cross-pass and cross-item consistency

- **The single-ownership consolidation holds and was re-derived.** `grep -n apply_type_visibility` over the spec returns exactly **two** hits: `:417` (a pointer) and `:649` (`### Layer 4`'s bullet, the one telling). `:930` carries `— Layer 4` and `:1002` names the heading. No fourth copy; the pre-fix state was three spellings that disagreed.
- **Against R1's closed diff, the two items are consistent in shape and in fact.** R1's `:306-310` correctly assigns Phase 2 to `_attach_relation_resolvers` alone; R1's `:312-329` already carried the correct three-applier visibility list (`connection` pipeline, `list_field.py::DjangoListField`, `optimizer/walker.py::_build_child_queryset`) that R1b's perform pass then contradicted 450 lines below and the apply pass restored. The spec's `### Layer 4` — R1-authored, since HEAD's `### Layer 4` was `Strawberry-native field class` — never attributes the annotation to a phase, so the finding above is R1b's own prose and not an inherited claim.
- **Two rationale entries keyed to `` ### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField` `` ** (`:270` from R1, `:763` from R1b) are correct under `BUILD.md` `## Spec rationale extraction`: each names the decision it belongs to and records a different change. Not a duplication finding.
- **No new vocabulary, constant, convention, or indirection** is introduced by R1b, so the existence challenge does not arise.

### DRY check across this item and prior accepted items

No new duplication. The item's whole shape is de-duplication: three restatements of `### Layer 4`'s seam
map collapsed to pointers, one membership claim collapsed to a quoted constant, one to an alias name,
and pass 2's four edits are three subtractions and a one-clause narrowing. The remedy this pass asks for
is a scoping or a cut, which adds no shape. **No DRY opportunity remains open.**

### Escalations carried forward — report-only, unrepaired, unchanged in substance

1. **`spec-010:8` and `:491`, and the `spec-010:67` coupling** with its near-duplicate sentence — all describe surfaces this cycle scrubbed. Owned by the concurrent spec-010 cycle; only the maintainer can sequence the two at commit. Both spec-010 files were read read-only this pass; nothing was edited, reverted, or `git checkout`ed.
2. **`types/definition.py::DjangoTypeDefinition`'s docstring** reserves `fields_class` for the pre-renumber `TODO-BETA-046-0.1.1`. Source is read-only in this cycle.
3. **The rationale's `## Standing notes` "three sites" bullet** is deliberately stale under append-only and flagged in-file five lines above it; the one-`-`-line proof shows it unmodified again this pass.
4. **`spec-009:592-597`'s registry-state sentence** is satisfied across two objects — registry-global `is_finalized` versus per-type `DjangoTypeDefinition.finalized`. Not false; a future pass tightening it should say which object holds which half. Reported-not-repaired across seven passes now.
5. **The one whose evidence inaction destroys.** No permanent test row pins `async def get_queryset` → `SyncMisuseError` for a *default* `DjangoConnectionField` under `await schema.execute`. The ready-made body at `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is gitignored and clears with the cycle. **This needs carding before the cycle closes** — it is the fifth pass to say so and the only escalation whose cost rises with delay. Not modified, moved, re-run, or deleted by this pass.

### Summary

**What R1b shipped.** A clause-by-clause mechanism sweep of all 1,096 lines of
`spec-009-rich_schema_architecture-0_0_4.md` — the 984 pre-existing lines no prior pass had opened at
the mechanism level, plus the two added-text sites the maintainer routed here — under
`### Maintainer decision 4`. The defect class: *a sentence asserting a mechanism, seam, cause, recourse,
or capability the code does not have.*

**The yield, and why the ratio is structural.** **Four** false clauses in 984 pre-existing lines against
**eleven** in the 112 lines this cycle added. That is not luck. A horizon document's pre-existing text is
overwhelmingly **prescriptive** — "should", "take this", "recommended adaptation", "borrow the behaviors
not the class" — and **a prescription cannot be false about a mechanism**: the defect class needs a
present-tense assertion to attach to, and prescriptive text offers far fewer per line than a fix pass's
connective tissue does. All four pre-existing findings sit in the only places such text does assert
present tense — a code-sketch comment (`:610`), a `Benefits:` list (`:394`), and two one-line
restatements of another section's map (`:930`, `:1002`); the fifth, `:417`, is a section-closing
paragraph of the same kind. **The operational lesson for any future sweep: go straight to code-sketch
comments, `Benefits:` / `Implementation:` lists, one-line restatements of another section, and
section-closing paragraphs — and skip the "should" prose.**

**The five corrections that landed**, all single-line, no renumbering, no heading text changed, no
section added or removed:

1. **`:610`** — `Literal["forward_single", "many", "reverse_one_to_one"]  # mirrors utils.relations.RelationKind` (three of five members, asserting a mirror it did not have) → `relation_kind: RelationKind  # the alias in utils.relations, five members`. Replaced with the alias rather than re-spelled: a copied enumeration is true today and false on the next member.
2. **`:394`** — "can report exact **unfinalized** or unresolved fields" → "can name the exact relation fields whose target model has no registered type", which is `check_schema`'s own reported condition. Narrowed rather than cut because the bullet is the sole `[glossary-schema-audit]` use and cutting it would have dropped the term count 23 → 22.
3. **`:930`** (`### Phase 3`) — visibility composition cut from the generation list, and the surviving "across every cardinality" absolute replaced by `### Layer 4`'s own "in the cardinality-correct spelling".
4. **`:1002`** (`### Decision 3`) — visibility and arguments cut from the generation list and attributed to "the queryset-owning **components** `### Layer 4` names", so the decision still accounts for all four seams without writing a third copy of the map.
5. **`:417`** — a third copy of the seam map naming three of eight invoking modules, a *different* incomplete triple than `### Layer 4`'s, standing **two lines below** `:415`'s own "it is not repeated here" — the spec contradicting itself on the page. Replaced by the same pointer-shrink.

**The reversal is the substantive one.** R1's final verification had judged `:930` / `:1002`
non-findings; R1b reversed that on the fail-open direction of a **row-visibility** claim, and the
reversal's conclusion — the finalizer composes no visibility at any cardinality — was re-derived
independently here at `plan_relation` → `_plan_prefetch_relation` → `_build_child_queryset`, plus
`grep -c apply_type_visibility` returning **0** in both `types/finalizer.py` and `types/resolvers.py`
and **0** `DjangoOptimizerExtension` references in `schema.py`. The reversal's *argument* was itself
false when first written and was rewritten in place; the rewrite's two gating conditions are stated as
necessary rather than absolute, which is the shape whose absence caused the finding.

**Post-fix the seam map has exactly one telling** — `### Layer 4` (`:644-654`) — with `:417`, `:930` and
`:1002` pointing at it. Four rationale entries record the reasoning, each keyed to the spec heading it
belongs to, each with its rejected alternative and the reason it lost.

**Final enumeration denominator and coverage map.** **119** clause sites across all 1,096 lines: **66**
`true`, **5** `FALSE` (all corrected), **34** `judgement`, **10** `note (upstream)`, **4** `out of
scope`; **71** opened at the symbol they name. Line coverage **842 / 1,096**; residue **108** gaps /
**254** lines with **no residual gap holding five or more non-blank lines** (largest is four). The
gap-size criterion was accepted **because the residue it cannot see was discharged, not because the
criterion is sound**: eleven single-line present-tense survivors sit *between* covered rows and all
eleven were opened — six by Worker 3, six by the prior final verification, one overlapping — and all
held. Carry the instrument forward as **line coverage plus a scan of the uncovered non-blank lines**.

**Ledger, with closing identities.** Spec **61,170 bytes / 1,096 lines** (HEAD: 54,232 / 1,154);
rationale **60,356 / 828** (HEAD: 12,273 / 208). `git diff --numstat`: spec **114 / 172**, rationale
**620 / 0**. Both identities close: `1,154 − 172 + 114 = 1,096` and `208 + 620 = 828`. The cross-item
chain closes too: R1 ended at **61,082 / 1,096**, and `61,082 + 54 + 34 = 61,170`. Append-only holds the
strong way — one `-` line and it is the `--- a/` header, so no HEAD line was deleted or modified; hunks
`618 + 1 + 1 = 620`; `head -166` `cmp`s exit 0 against HEAD's copy. Gates: glossary **23 terms, exit
0**; trailing commas **exit 0** on both; **25/25** and **11/11** link definitions with 0 missing / 0
orphan / 0 dead; **0** in-page anchors; **0** in-repo raw `path:NN`; Layers **11** / Phases **8** /
Decisions **6** intact and un-renumbered; five cross-spec anchors unique in both directions.
`git log --stat` over both paths: the newest commit touching either is still **`f3c94642`** with HEAD at
`973d00b2` — nothing was swept into a concurrent commit.

**Needs carding before the cycle closes** (escalation 5, the only one whose evidence inaction destroys):
**no permanent test row pins `async def get_queryset` → `SyncMisuseError` for a *default*
`DjangoConnectionField` under `await schema.execute`.** The ready-made body at
`docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is gitignored and clears with
the cycle, so the evidence is destroyed by inaction rather than by a decision. Card it, or record an
explicit decision that the boundary stays unpinned.

**What blocks acceptance.** One Medium in the permanent rationale — `:705-708`'s "at finalizer Phase 2"
covering a seam that runs at Phase 1. It touches no spec edit, not the reversal's conclusion, not the
denominator, not the coverage map, and no gate. **Fix that one clause; nothing else on this item is
open.**

### Spec changes made (Worker 1 only)

**None.** This pass edited neither the spec nor the rationale. The finding above is recorded for the
apply-changes pass rather than repaired here, so no fresh unreviewed claim enters a permanent document
at the moment of acceptance — the discipline that has produced every clean result on this cycle.

No `### Dispatched findings checklist` box is left `- [ ]`, so no deferral reason is owed under
`## Final verification job` step 3.

### Final status

`revision-needed`. One Medium, in text this cycle appended to the permanent rationale, remediable by
scoping one clause or deleting an ordinal:

1. **Medium** — `rationale:705-708`: "at finalizer Phase 2" governs both `resolved_relation_annotation` and `_attach_relation_resolvers`; the annotation rewrite runs at **Phase 1** (`types/finalizer.py:775`, inside the failure-atomic pending-relation walk the module docstring's Phase 1 bullet names it in). Scope the phase to the resolver, or drop the ordinal and say "at finalization".

The apply-changes pass for this item is Worker 1's per the build plan's `### Deviation 3` corollary, and
sets `planned` again, which Worker 0 reads as "dispatch Worker 3".

---

## Build report (Worker 1, apply-changes pass 3)

Run 2026-08-16 by a fresh Worker 1 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-1.md`. **HEAD re-derived twice: `973d00b2` at the start of
this pass** (`git rev-parse HEAD`, not inherited from the dispatch; unchanged from the pass-2 final
verification's reading) **and `fd0c7327` at the end** — a concurrent package-source session committed
`Share FilterSet and OrderSet dynamic Meta hashing and class factories` mid-pass, touching six
`filters/` / `orders/` / `utils/` source and test files and neither of this cycle's documents. Every
figure in the ledger table below was **re-measured against the new HEAD** afterwards: `--numstat`,
both HEAD copies, and the newest-commit provenance are all unchanged, so no identity moved.
`git status --porcelain` is **174** entries — up from **141** last pass, all of
it the concurrent sessions. Nothing outside this cycle's writable set was edited, reverted, or
`git checkout`ed; `git stash` / `checkout` / `restore` / `worktree` were not used, and every HEAD
reference is `git show HEAD:<path>` into an out-of-repo scratch path. Nothing under
`docs/builder/temp-tests/` was touched —
`docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is still on disk at its
unchanged 20:42 mtime and its unchanged 1,565 bytes.

**This item runs no tests and changes no code.** No `pytest` was invoked, with or without `--cov*`
flags. The staged-anchor sweep belongs to **R4** and was not duplicated here.

**Spec status-line re-verification (per-spawn duty).** Lines 1-5 re-read at the start of this pass. The
opener describes the rationale companion, the four finalization sites, and the six scrubbed mechanisms.
This pass changes one temporal adverbial inside one rationale entry: it introduces no mechanism, retires
none, and touches no finalization site. **No edit owed.**

### Scope: one correction, one clause edit, zero spec edits

The dispatch carried the single Medium the pass-2 final verification raised. It was **verified at the
source before being rewritten**, per the standing instruction not to take a finding's reading on trust —
this is the sixth correction-pass clause on this cycle to be false, and a fix pass's own new prose is
the highest-risk text in the cycle.

### The finding, re-derived rather than accepted

**Claim under test:** `rationale:705-708` said the finalizer generates the annotation
(`types/converters.py::resolved_relation_annotation`) and the resolver
(`types/resolvers.py::_attach_relation_resolvers`) for every exposed relation "at finalizer Phase 2".
The adverbial governs both seams.

**1 — the annotation seam has exactly one call site, and it is not in Phase 2.** Enumerated
mechanically by AST over the package rather than by grep, because a `grep` for the name also matches the
`import`, the definition, and four docstring mentions:

```shell
$ uv run python - <<'PY'
import ast, pathlib
hits=[]
for p in sorted(pathlib.Path("django_strawberry_framework").rglob("*.py")):
    for n in ast.walk(ast.parse(p.read_text())):
        if isinstance(n, ast.Call):
            f=n.func
            name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if name == "resolved_relation_annotation":
                hits.append((p.as_posix(), n.lineno))
print("package call sites of resolved_relation_annotation:", len(hits), hits)
PY
package call sites of resolved_relation_annotation: 1 [('django_strawberry_framework/types/finalizer.py', 887)]
```

**Re-derived at HEAD as well as in the working tree**, because a concurrent package-source session has
`types/finalizer.py` dirty and the line has moved. `git show HEAD:django_strawberry_framework/types/finalizer.py`
puts the same call at **775** — the line the dispatch named — and the working tree puts it at **887**.
Same call, same enclosing block, both readings agree on the phase:

```shell
$ grep -n "resolved_relation_annotation\|# Phase 2 runs BEFORE\|discard_pending" <HEAD copy of types/finalizer.py>
12:  rewrite the synthesized annotation via ``resolved_relation_annotation``).
68:from .converters import resolved_relation_annotation
775:        pending.source_type.__annotations__[pending.field_name] = resolved_relation_annotation(
781:    registry.discard_pending(resolved_pending)
783:    # Phase 2 runs BEFORE Phase 2.5; interface base injection cannot
```

The call sits **above** `registry.discard_pending(resolved_pending)` and **above** the
`# Phase 2 runs BEFORE Phase 2.5` comment that introduces the `_attach_relation_resolvers` loop. Read
in the working tree at `:881-899`, it is inside the `for pending, target_type, field_meta in resolved:`
loop that runs immediately after `if unresolved: raise ConfigurationError(...)` — that is Phase 1's
failure-atomic walk, by construction: the raise is what makes it atomic, and it precedes the rewrite.

**2 — the module that owns the phase vocabulary assigns it to Phase 1 in as many words.**
`types/finalizer.py`'s module docstring, identical at HEAD and in the working tree:

```
- Phase 1 (failure-atomic): walk ``registry.iter_pending_relations()`` and
  classify each pending record as ``unresolved`` ..., ``consumer_authored``
  ..., or ``resolved`` (target registered; rewrite the synthesized annotation
  via ``resolved_relation_annotation``).
  ...
- Phase 2: ``_attach_relation_resolvers`` installs the framework's auto
  relation resolvers across every not-yet-finalized type.
```

**Verdict: the finding is correct.** The adverbial is true of `_attach_relation_resolvers` and false of
`resolved_relation_annotation`, which runs one phase earlier. Not a scope judgement — the phase named is
not the phase the code runs in, under every reading.

### The remedy: the ordinal is dropped, and the replacement is the spec's own spelling

Applied at `rationale:708`, a one-line in-place correction:

- **Before:** `cardinality-correct spelling, at finalizer Phase 2. It generates **no** visibility composition for any`
- **After:** `cardinality-correct spelling, at finalization. It generates **no** visibility composition for any`

Three reasons this is the right form, in the order they decided it:

1. **It asserts strictly less.** Both Phase 1 and Phase 2 are inside `finalize_django_types()`, so
   "at finalization" is true of both seams under any grouping, and it is checkable from the cited
   symbols at the reader's desk. Text that asserts no ordinal cannot be the seventh false correction —
   the cheapest possible answer to the cycle's own worst pattern.
2. **It is not new prose: it is the spelling the corrected spec line already carries.** The rationale
   sentence is a restatement of `spec-009:930`, which this cycle rewrote to
   `Generate the annotation and resolver for every exposed relation at finalization, in the cardinality-correct spelling — Layer 4.`
   The entry had swapped that document's own `at finalization` for an ordinal; the fix restores it, so
   the entry and the line it explains now agree word for word on the temporal scope.
3. **The entry's argument never needed the number.** The ordinal is load-bearing only for the entry's
   generalisable rule at `:752-754` — "Phase 2.5 re-shapes what Phase 2 attached" — which is about the
   **resolver** and survives untouched. Verified independently: Phase 2 is `_attach_relation_resolvers`
   and Phase 2.5 is `_synthesize_relation_connections`, which `finalizer.py` `#"Remove the generated
   list form before Phase 3 freezes the"` shows deleting the generated list form.

**The alternative was considered and rejected.** Scoping the ordinal to each seam — "in Phase 1's
pending-relation walk … at Phase 2" — is true and was verified above, but it writes **two** new phase
claims into a permanent document to buy precision the paragraph does not spend, and an ordinal is
exactly the kind of incidental precision that rots. Cutting the adverbial entirely was also rejected:
`at finalization` costs two words and keeps the sentence parallel with `:930` and with the entry's own
closing `at finalization or anywhere else` at `:744`.

### The spec twin check, run per token and by shortest distinctive token

The wrap trap, the different-spelling trap, and the `\b`-vs-underscore trap have each bitten this cycle,
so every sweep below is a single short token, and every hit was opened and graded rather than counted.

```shell
$ grep -n -- "at finalizer"     <spec> <rationale>
rationale:708  (the clause under repair; now gone)
spec:648       - **resolution** - ... `_attach_relation_resolvers` installs them at finalizer Phase 2, before `strawberry.type` runs at Phase 3

$ grep -n -- "cardinality-correct" <spec> <rationale>
spec:647, spec:930, rationale:708, rationale:736

$ grep -n -- "generates the annotation" <spec> <rationale>
rationale:705

$ grep -n -- "only window"       <spec> <rationale>
rationale:310, spec:654

$ grep -n -- "Phase"             <rationale>
275, 289, 307, 310, 374, 479, 482, 484, 487, 507, 560, 563, 610, 624, 629, 635, 643, 694, 702, 708, 735, 753, 774
```

Graded:

- **`spec:648` — not a twin, and true.** `### Layer 4`'s **resolution** bullet attributes Phase 2 to
  `_attach_relation_resolvers` alone; the **annotation** bullet at `:647` names no phase at all. The
  spec never makes the attribution the rationale made, exactly as the dispatch reported — verified,
  not assumed. **No spec edit owed, and the spec is byte-identical this pass.**
- **`spec:654` — a note, not a twin.** "Phase 2 is the only window" is scoped to resolver generation by
  its own preceding sentence (the target may not exist at class creation; the type is frozen after
  `strawberry.type`) and pinned to that scope by `rationale:307-310`, which calls
  `_attach_relation_resolvers` "the permanent finalizer Phase-2 mechanism". It is not false under that
  reading, it sits in R1's `final-accepted` region, and re-opening closed text needs falsity rather
  than grammatical resemblance — the standard this cycle applied to `:533` and to `rationale:359-360`.
  Recorded so a later pass does not re-open it as new.
- **`rationale:310`, `rationale:479-482` — true, checked at the source.** `:310`'s subject is
  per-relation resolver generation (Phase 2 ✓); `:482`'s is
  `types/finalizer.py::_synthesize_relation_connections` at Phase 2.5, which the module docstring's
  Phase 2.5 bullet names ✓.
- **`spec:930`, `spec:1002`, `rationale:744` — already ordinal-free** (`at finalization`), which is
  what made that the replacement rather than an invention.

**No other ordinal attached to a named symbol survives in either document.** The remaining `Phase`
hits are heading names, migration-phase references (`### Phase 1`-`8`, a different axis), or the
Phase 2.5 rule verified above.

### Gates, proofs and ledger — all re-run this pass, none read off a prior report

| Check | Result |
|---|---|
| Ledger — spec | `wc -c -l` **61,170 / 1,096** before **and** after; `shasum -a 256` identical before and after (`ae7deb30…`) — **byte-unchanged, checked not assumed** ✓ |
| Ledger — rationale | `wc -c -l` **60,356 / 828** → **60,351 / 828**; **−5 bytes, 0 lines** ✓ |
| Per-edit delta reproduces | `at finalizer Phase 2` (20 chars) → `at finalization` (15) = **−5**, and `60,356 − 5 = 60,351` is what the file measures ✓ |
| Line 708 width | `awk NR==708 \| wc -c` **103 → 98**; under the 100-char wrap, so no reflow and the hunk is one line ✓ |
| `--numstat` | spec **114 / 172** (unmoved since R1b's first pass); rationale **620 / 0** (unmoved — the correction lands on an R1b-added line, so it cannot move the counts) ✓ |
| Identity 1 | `1,154 − 172 + 114 = 1,096` ✓ |
| Identity 2 | `208 + 620 = 828` ✓ |
| Cross-item byte chain | R1 closed at **61,082 / 1,096**; `61,082 + 54 + 34 = 61,170` = the spec's measurement, unchanged because this pass edited no spec line ✓ |
| Append-only, `-` lines | `git diff -- <rationale> \| grep -c '^-'` → **1**, printed and it is `--- a/docs/SPECS/appx/…` — no HEAD line deleted **or modified** ✓ |
| Append-only, hunks | `-U0` → `@@ -166,0 +167,618 @@`, `@@ -185,0 +804 @@`, `@@ -186,0 +806 @@`; `618 + 1 + 1 = 620` = the numstat addition ✓ |
| Append-only, prefix | `head -166` working `cmp` `head -166` HEAD copy → **exit 0** ✓ |
| Glossary gate | `check_spec_glossary.py --spec …spec-009…` → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0** ✓ |
| Comma gate | `check_trailing_commas.py --check` on **both** documents → **exit 0**; `shasum -a 256` and `wc -c -l` identical before and after the gate run, so the auto-fixer wrote nothing ✓ |
| Numbering | `^### (Layer\|Phase\|Decision) N` → **11 / 8 / 6**, printed in file order (`Layer 1`-`11` at `:576…:799`, `Phase 1`-`8` at `:903…:985`, `Decision 1`-`6` at `:995…:1010`) — identical to the prior pass's positions; no gap, no duplicate, **none renumbered** ✓ |
| In-page anchors | `grep -c '](#'` → **0 / 0**, so none can dangle ✓ |
| Link defs | independent parser (single `<!-- LINK DEFINITIONS -->` delimiter; uses harvested from the raw body so a ref-style use inside a code span still counts; `#fragment` stripped before the disk check): spec **25 / 25**, rationale **11 / 11**; **0** missing, **0** orphan, **0** dead ✓ |
| Raw `path:NN` | `grep -nE '[A-Za-z0-9_/.-]+\.(py\|md):[0-9]+'` less `file:///` → **no match** in either permanent document (exit 1) ✓ |
| Cross-spec anchors | five, both directions, re-derived at the moment of dependence. Citing lines read in full: `spec-010:67`, `spec-010:468`; `spec-009:99` / `:634` / `:870`. **Heading-anchored** `grep -cE '^<heading>$'` returns **1** for all five targets (`### Must redo (not augment)`, `## Strawberry finalization strategy`, `### Unresolved-target error format`, `### Layer 3: Finalization trigger`, `### Decision 6: fail loudly`) — every anchor exists and is unique. **Nothing repaired**; `spec-010` is a concurrent cycle's file and was read read-only ✓ |
| Provenance | `git log --stat` over **both** paths → the newest commit touching either is still **`f3c94642`**, HEAD at `973d00b2`. Nothing was swept into a concurrent commit. `git status` alone was not used as the test ✓ |

### `### Dispatched findings checklist` — one box added, one clause edit, mapping stated

The box appended by this pass sits under its own demarcating paragraph (`:116-121`), strictly below the
pass-2 additions, and rewrites no prior box. **One box, one edit, one-to-one** — this pass made exactly
one change to a permanent document. Every box on the checklist is `- [x]`, so no deferral reason is owed
under `## Final verification job` step 3, and none of R1's sixteen contracts or R1b's fourteen prior
edits is reversed: `:708`'s correction moves in the same direction as every prior one on this item
(remove an unverifiable precision, point at the scoped statement) rather than restoring anything.

### Notes for Worker 3

- **The one thing to re-derive first**, because it is the sixth false correction-pass clause on this
  cycle and this pass's own prose is now the highest-risk text on it: the AST call-site enumeration
  above, at HEAD **and** in the working tree. `types/finalizer.py` is dirty from a concurrent session,
  so a line number alone will not reproduce — the dispatch's `:775` is HEAD's, the working tree's is
  `:887`, and both sit above `registry.discard_pending` and above `# Phase 2 runs BEFORE Phase 2.5`.
- **The replacement asserts nothing beyond `spec-009:930`'s own wording**, which is deliberate. If it
  reads as under-specified, the tightening is a scope decision for the maintainer, not a correction:
  two new phase claims for a paragraph whose argument needs neither is what the standing preference for
  subtraction is against.
- **`spec:654` is graded a note above and is not repaired.** Grading it a finding means re-opening R1's
  `final-accepted` region, which needs falsity rather than resemblance; its scoped reading is pinned by
  `rationale:307-310`.
- **The spec is byte-identical this pass** — `shasum -a 256` before and after, in the table above, not
  inferred from "I did not edit it".

### Notes for Worker 1 (spec reconciliation)

No spec reconciliation owed. The correction removes an ordinal from a rationale entry; the spec's own
statements of the same pair (`:647`, `:648`, `:930`, `:1002`) were each opened and are each true as
written, and `### Layer 4`'s per-seam scoping is what the entry now defers to on both counts.

Carried forward unchanged, report-only, none repaired by this pass:

1. **`spec-010:8` / `:491` and the `spec-010:67` coupling** — the concurrent cycle's; only the
   maintainer can sequence the two at commit.
2. **`types/definition.py::DjangoTypeDefinition`'s docstring** reserves `fields_class` for the
   pre-renumber `TODO-BETA-046-0.1.1`. Source is read-only in this cycle.
3. **The rationale's `## Standing notes` "three sites" bullet** is deliberately stale under append-only
   and flagged in-file five lines above it; the one-`-`-line proof shows it unmodified again.
4. **`spec-009:592-597`'s registry-state sentence** is satisfied across two objects — registry-global
   `is_finalized` versus per-type `DjangoTypeDefinition.finalized`. Not false; a tightening pass should
   say which object holds which half.
5. **`rationale:359-360`** and **`rationale:533`**, both in R1's closed region, both graded notes by
   prior passes and unchanged here.
6. **The one whose evidence inaction destroys.** No permanent test row pins `async def get_queryset` →
   `SyncMisuseError` for a *default* `DjangoConnectionField` under `await schema.execute`. The
   ready-made body at `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is
   gitignored and clears with the cycle. **Card it before the cycle closes** — sixth pass to say so.

### Status

`planned`

---

## Review (Worker 3, pass 4)

Run 2026-08-16 by a fresh Worker 3 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-3.md`. **HEAD re-derived at the start of this pass:
`676f10d2`** (`git rev-parse HEAD`, not inherited from the dispatch) — moved again from the `fd0c7327`
the apply pass closed on, and from the `973d00b2` it opened on — **and re-derived again at the end of
this pass: `6f8bf818`**, the concurrent spec-013 residual cycle having landed two KANBAN/builder commits
mid-review. Both `--numstat` pairs and the newest-commit provenance were **re-measured against the new
HEAD** afterwards and are unchanged (`620 / 0`, `114 / 172`, newest commit still `f3c94642`), so no
identity below moved. `git status --porcelain` is **174**
entries, unchanged in count from the apply pass and all of it the four concurrent cycles, the REVIEW
cycle, the DRY cycle and the package-source session. Every figure below was measured at `676f10d2`;
none was read off a prior report. Nothing outside this pass's writable set was edited, reverted, or
`git checkout`ed; `git stash` / `checkout` / `restore` / `worktree` were not used, and every HEAD
reference is `git show HEAD:<path>` into an out-of-repo scratch path. Nothing under
`docs/builder/temp-tests/` was touched — `docs/builder/temp-tests/r1/test_async_execution_default_connection.py`
is on disk at its unchanged **1,565** bytes and unchanged **20:42** mtime.

**Scope of this pass, and why it is narrow.** The whole change is one temporal adverbial inside one
rationale entry: `at finalizer Phase 2` → `at finalization`, −5 bytes, 0 lines, spec byte-unchanged.
Three prior review passes and two final verifications have audited the spec edits, the High's rewrite
and the enumeration; none of that was re-opened. What *was* re-derived from source, because it is what
this pass's acceptance rests on: the finding's correctness, the remedy's provenance, the twin sweep, and
every gate.

**No `pytest` was invoked**, with or without `--cov*` flags. This item runs no tests and changes no code.

### High:

None.

### Medium:

None.

### Low:

None.

### The finding was correct — re-derived at HEAD and in the working tree, by symbol not by line

The apply pass's `### Notes for Worker 3` asks for exactly this first, and it reproduces.

- **One call site, enumerated by AST over the whole package, at both trees.** Working tree:
  `1 [('django_strawberry_framework/types/finalizer.py', 887)]`. HEAD, swept by walking
  `git ls-tree -r --name-only HEAD` and parsing each `git show HEAD:<path>` rather than the checkout:
  `1 [('django_strawberry_framework/types/finalizer.py', 775)]`. The line-number hazard the dispatch
  flagged is real and is exactly as described — a concurrent session has `types/finalizer.py` dirty and
  the call has moved 112 lines. Both readings are the same call.
- **The call is in Phase 1, positionally.** In the HEAD copy the call at `775` sits inside the
  `for pending, target_type, field_meta in resolved:` loop that opens immediately after
  `if unresolved: raise ConfigurationError(...)` at `770-771`; `registry.discard_pending(resolved_pending)`
  follows at `781`, and the `# Phase 2 runs BEFORE Phase 2.5` comment at `783` introduces the
  `_attach_relation_resolvers(` loop at `793`. The raise preceding the rewrite is what makes the walk
  failure-atomic, so the enclosing block is Phase 1 by construction and not only by label.
- **The module that owns the phase vocabulary says so.** `types/finalizer.py`'s module docstring,
  identical at HEAD and in the working tree, assigns *"rewrite the synthesized annotation via
  ``resolved_relation_annotation``"* to the `Phase 1 (failure-atomic)` bullet and
  ``_attach_relation_resolvers`` to the `Phase 2` bullet.

**Verdict: the adverbial was false of the first of the two seams it governed.** Not a scope judgement.

### The remedy asserts nothing new — the replacement is the document's own wording

- **`spec-009:930` reads** `Generate the annotation and resolver for every exposed relation at
  finalization, in the cardinality-correct spelling — Layer 4.` — read at the line, not from the report.
- **`rationale:708` now reads** `cardinality-correct spelling, at finalization. It generates **no**
  visibility composition for any`. Entry and spec line agree word for word on the temporal scope, and
  the entry's own closing `at finalization or anywhere else` at `:744` is the third instance of the same
  spelling in the same entry. Nothing was invented.
- **`at finalization` is true of both seams, checked rather than assumed.** `finalize_django_types()`
  opens at `finalizer.py:664` in the HEAD copy; the Phase 1 annotation rewrite (`775`) and the Phase 2
  resolver install (`793`) are both inside it. The claim is verifiable from the two cited symbols at a
  reader's desk, which is the property the entry needed and the ordinal was not buying.
- **Nothing downstream lost an antecedent.** The entry's generalisable rule at `:752-754` — *"Phase 2.5
  re-shapes what Phase 2 attached"* — names both ordinals in its own sentence and is about the resolver
  and the connection synthesis, neither of which the edit touched. Re-verified at the source anyway:
  Phase 2 is `_attach_relation_resolvers`, Phase 2.5 is `_synthesize_relation_connections`
  (`finalizer.py:475`, called at `869`), whose `#"Remove the generated list form before Phase 3 freezes
  the"` is the re-shaping the rule asserts. Read end-to-end at `:702-760`, the entry is coherent after
  the edit and its neighbouring claims are unaffected.
- **The paragraph's one adjacent number still reproduces**, and it is worth saying because it is a
  measurement over a currently-dirty file: `grep -c apply_type_visibility` on `types/finalizer.py` and
  `types/resolvers.py` returns **0 / 0** in the working tree **and** 0 / 0 at HEAD. The concurrent
  session's edits to `finalizer.py` have not invalidated the sentence the edited clause introduces.

### The rejected alternative — the call is right

Worker 1 rejected per-seam scoping (*"in Phase 1's pending-relation walk … at Phase 2"*) in favour of
the subtraction. Concur, on three grounds, the first of which is decisive:

1. **It is the only remedy shape that cannot become the seventh false correction.** Six correction-pass
   clauses on this cycle have been false, and the class is precisely *a fluent subordinate clause
   asserting a mechanism*. The per-seam form writes **two** new ordinal claims into a permanent
   document to replace one; the subtraction writes zero. A remedy that asserts no number is
   unfalsifiable in the good sense, and this reviewer's own carried-forward rule from R1b pass 3 is
   *"cut when the reason cannot be verified cheaply from the cited symbol; replace when it can"* — here
   it can be, from `spec-009:930`, so a replacement was available and was used.
2. **The paragraph never spends the precision.** The ordinals do no work in the entry's argument, whose
   conclusion is that the finalizer composes no visibility. An ordinal attached to an implementation
   detail of a private helper is the kind of incidental precision that rots on the next refactor —
   and the 775→887 drift **inside this very cycle**, from an unrelated concurrent commit, is the
   demonstration.
3. **Rejecting the full cut was also right.** `at finalization` costs two words and keeps the sentence
   parallel with `:930` and `:744`; deleting it would have made the entry the only one of the three
   statements of this pair carrying no temporal scope at all.

### The twin sweep, re-derived independently

Run fresh over both documents, one short token at a time per the wrap / spelling / `\b` traps, and every
hit opened rather than counted:

| Token | Hits (spec / rationale) | Grade |
|---|---|---|
| `at finalizer` | `spec:648` / none | The clause under repair is gone from the rationale. `:648` is `### Layer 4`'s **resolution** bullet and attributes Phase 2 to `_attach_relation_resolvers` alone — true, and not the attribution the rationale made |
| `cardinality-correct` | `spec:647`, `spec:930` / `rationale:708`, `:736` | `:647` is the **annotation** bullet and names **no** phase — confirmed by reading the line, which is the load-bearing half of the dispatch's claim. `:736` quotes Layer 4's phrase as the replacement it made |
| `generates the annotation` | none / `rationale:705` | The repaired sentence's own opening; no twin |
| `only window` | `spec:654` / `rationale:310` | Graded below |
| `at finalization` | `spec:654`, `:870`, `:927`, `:930`, `:1002`, `:1011`, `:1018` / `rationale:77`, `:235`, `:390`, `:708`, `:744` | The replacement's spelling is the documents' established one, in both files and in both R1's and R1b's text |
| `Phase` | 10 spec hits / 23 rationale lines (`275 … 774`) | Heading names, the `### Phase 1`-`8` migration axis, and the Phase 2 / 2.5 claims verified above |

**Repo-wide, not document-wide.** `grep -rn "at finalizer" --include=*.md --include=*.py`, excluding
per-cycle scratchpads, returns no other attribution of the annotation seam to a phase: the only
spec-009 hit is `:648`, and the remaining hits (`KANBAN.md:499`, `spec-027`, `spec-028`,
`filters/sets.py:2614`, `docs/dry/`) are `phase 2.5` sidecar-binding claims about a different subject in
other cycles' documents. **No orphaned twin survives the retirement.**

### `spec:654` — the "note, not a finding" grading is confirmed, and on a ground the prior passes did not state

`spec:654` reads `… Phase 2 is the only window, which is why it is a permanent mechanism rather than a
transitional one.` Read at whole-layer scope it would be false, because `### Layer 4`'s **annotation**
bullet sits seven lines above and that seam runs in Phase 1. The prior grading nevertheless holds, and
the strongest reason is on the page rather than in the companion:

- **The trailing relative clause is the disambiguator.** `it is a permanent mechanism rather than a
  transitional one` fixes the subject, because only one mechanism was ever accused of being
  transitional. `rationale:306-310` names it: *"The claim `### Layer 4` may no longer make: that
  `_attach_relation_resolvers` is transitional."* The sentence is about resolver installation, and of
  resolver installation `Phase 2 is the only window` is exactly true.
- The two supporting grounds the apply pass gave also hold: the preceding sentence's two-sided argument
  is the resolver's, and the line sits in R1's `final-accepted` region, where re-opening needs falsity
  rather than grammatical resemblance. My own carried-forward rule — *grade a rhyme by asking what
  disproves it* — asks for an on-page counterexample, and the relative clause is an on-page
  *confirmation* instead.

Recorded, not raised: a cold reader arriving at `:654` without `rationale:306-310` can over-read the
ordinal across the layer. That is a tightening a maintainer may want and is noted for Worker 1 below; it
is not this item's defect, the line is byte-unchanged this pass, and holding a one-clause subtraction on
it would be manufacturing the finding the dispatch warns against.

### No regression, append-only, gates — every figure re-derived at `676f10d2`

| Check | Result |
|---|---|
| Ledger — spec | `wc -c -l` **61,170 / 1,096** ✓; `shasum -a 256` `ae7deb30f66e35c5a98757e9c580fb1b17d67131b7cac4ded55585d33457b057` — matches the apply pass's recorded prefix, so the spec is byte-unchanged by an independent measurement ✓ |
| Ledger — rationale | `wc -c -l` **60,351 / 828** ✓ |
| Per-edit delta | `at finalizer Phase 2` = **20** chars, `at finalization` = **15**; **−5**, and `60,356 − 5 = 60,351` ✓ |
| Line 708 width | `awk NR==708 \| wc -c` → **98**, under the 100-char wrap, so no reflow and the hunk stays one line ✓ |
| `--numstat` | spec **114 / 172**, rationale **620 / 0** — both unmoved, as they must be for an edit landing on an R1b-added line ✓ |
| Identity 1 | HEAD spec is **1,154** lines (`git show HEAD:<spec> \| wc -l`); `1,154 − 172 + 114 = 1,096` ✓ |
| Identity 2 | HEAD rationale is **208** lines; `208 + 620 = 828` ✓ |
| Cross-item byte chain | `61,082 + 54 + 34 = 61,170` = the spec's measurement ✓ (arithmetic over R1's recorded close; the R1 baseline is not re-derivable from `676f10d2`, and the terminal figure is measured) |
| Append-only, `-` lines | `git diff -- <rationale> \| grep -c '^-'` → **1**, printed, and it is `--- a/docs/SPECS/appx/…` — no HEAD line deleted **or modified** ✓ |
| Append-only, hunks | `-U0` → `@@ -166,0 +167,618 @@`, `@@ -185,0 +804 @@`, `@@ -186,0 +806 @@`; `618 + 1 + 1 = 620` = the numstat addition ✓ |
| Append-only, prefix | `head -166` working `cmp` `head -166` HEAD copy → **exit 0**, both **10,772** bytes ✓ |
| Glossary gate | `check_spec_glossary.py --spec …spec-009…` → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0** ✓ |
| Comma gate | `check_trailing_commas.py --check` on **both** documents → **exit 0**; `shasum -a 256` + `wc -c -l` captured before and after the gate run and `cmp`-identical, so the auto-fixer wrote nothing ✓ |
| Numbering | `^### (Layer\|Phase\|Decision) [0-9]+` → **11 / 8 / 6**, printed in file order (`Layer 1`-`11` at `576…799`, `Phase 1`-`8` at `903…985`, `Decision 1`-`6` at `995…1010`) — no gap, no duplicate, **none renumbered** ✓ |
| In-page anchors | `grep -c '](#'` → **0 / 0**; none can dangle ✓ |
| Link defs | independent parser (single `<!-- LINK DEFINITIONS -->` delimiter; uses harvested from the raw body so a ref-style use inside a code span still counts; `#fragment` stripped before the disk check): spec **25 uses / 25 defs**, rationale **11 / 11**; **0** missing, **0** orphan, **0** dead ✓ |
| Raw `path:NN` | `grep -nE '[A-Za-z0-9_/.-]+\.(py\|md):[0-9]+'` less `file:///` → **no match** in either permanent document (exit 1) ✓ |
| Cross-spec anchors | five, both directions. Citing lines read in full: `spec-009:99`, `:634`, `:870`; `spec-010:67`, `:468`. **Heading-anchored** `grep -cE '^<heading>'` returns **1** for all five targets (`### Must redo (not augment)`, `## Strawberry finalization strategy`, `### Unresolved-target error format`, `### Layer 3: Finalization trigger`, `### Decision 6: fail loudly`) ✓. Both `spec-010` files read read-only; nothing edited ✓ |
| Provenance | `git log --stat` over **both** paths → newest commit touching either is still **`f3c94642`**, with HEAD three commits further on at `676f10d2`. Nothing was swept into a concurrent commit; `git status` alone was not used as the test ✓ |

### `### Dispatched findings checklist` — one box added, one clause edit, mapping holds

- **14 boxes, 0 unticked** (`grep -c '^- \[x\]'` → 14, `'^- \[ \]'` → 0), against 4 (perform) + 6 (apply
  1) + 3 (apply 2) + 1 (apply 3). The prior final verification's "thirteen boxes, fourteen edits"
  becomes **fourteen boxes, fifteen edits**, the extra edit still being apply-pass-2's correction 3,
  which the dispatch worded as two clauses.
- **The new box sits under its own demarcating paragraph** at `:116-121`, strictly below the pass-2
  block, and its text states the finding, the symbol, the phase, and the remedy shape
  (*"Ordinal dropped, not restated"*). **One box, one clause edit, one-to-one.**
- **No prior box was rewritten.** The artifact is untracked, so this is asserted from content rather
  than from `git diff`: all thirteen prior box texts match the descriptions the pass-2 final
  verification enumerated, and the three demarcating paragraphs are intact and in pass order.
- The box's direction is consistent with all fourteen prior edits — remove an unverifiable precision,
  defer to the scoped statement — and reverses none of R1's sixteen contracts.

### DRY findings

None. The item's whole shape is de-duplication, and this pass's edit is a pure subtraction that adds no
shape: an ordinal is retired and replaced by a spelling already carried at three other sites in the two
documents (`spec-009:930`, `rationale:744`, and now `:708`), which is convergence, not duplication.
**The existence challenge does not arise** — R1b introduces no vocabulary, constant, convention,
registry or indirection layer, and this pass introduces no prose that could host one.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — `__all__` and the re-export list are
unchanged. Stated as the file's own footprint rather than as a whole-tree claim, per this reviewer's
carried-forward note: on this repo, with 174 dirty entries across six concurrent sessions, a whole-tree
`git diff` can never be empty and is not evidence about this item.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applies — the item's entire footprint is one documentation file.

- **Footprint, named:** `docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md`, −5 bytes,
  0 lines, one clause on `:708`. `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` is byte-
  identical by `shasum`. No other permanent document was touched by this pass.
- **No version string, shipped/planned status, or card ID** is introduced, moved, or invalidated: the
  edit changes a temporal adverbial inside an existing entry and touches no KANBAN surface, no release
  metadata, and no archival.
- **Links:** no link was introduced or moved; the parser above shows 0 missing / 0 orphan / 0 dead in
  both documents, and both in-page-anchor counts remain 0.
- **No verbatim spec drop-in** is created by this pass, so the `diff`-against-source obligation does not
  arise — but the inverse was checked and is the point of the remedy: the corrected clause now agrees
  word for word with `spec-009:930`'s `at finalization`.
- **No staging language** (`planned`, `Slice N`, `TODO(`) enters either document, and neither is
  script-rendered, so no regenerate is owed.
- **Spec status line** (`:1-5`) re-read: it describes the rationale companion, the four finalization
  sites and the six scrubbed mechanisms. This pass introduces no mechanism and retires none. **No edit
  owed** — confirming the apply pass's own reading.

### What looks solid

- **The remedy is the shape least able to introduce a seventh false clause**, and it was chosen for that
  reason explicitly. A substitution of the document's own existing wording asserts strictly less than
  what it replaces, and the apply pass verified the finding at the source before rewriting rather than
  taking the dispatch's reading on trust — which is exactly the discipline six false corrections earned.
- **The AST enumeration at *both* trees** is the right instrument and the right defence. A `grep` would
  have counted the import, the definition and four docstring mentions; a line number alone would not
  have reproduced, because a concurrent session moved the call 112 lines mid-cycle. Naming both readings
  and showing they share an enclosing block is what makes the claim survivable.
- **The alternative was rejected with the cost stated**, not silently. Recording *why the more precise
  form was worse* is what keeps the next pass from "fixing" `at finalization` back into an ordinal.
- **The `shasum`-before-and-after on the byte-unchanged file.** "I did not edit it" is not a measurement
  on a tree six sessions are writing; the hash is, and it matches independently here.
- **`spec:654` and `rationale:359-360` were flagged and left**, with the reason recorded. Not re-opening
  `final-accepted` text on a rhyme is the correct instinct, and both notes are carried where a later
  pass will find them instead of re-discovering them as new.

### Temp test verification

- **No temp test was written or run this pass.** The item changes no code and asserts no runtime
  behavior; every claim under review is verifiable by AST enumeration and by reading the two documents,
  which is where the evidence for it lives.
- `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` was **not** modified, moved,
  run or deleted: **1,565** bytes at its unchanged **20:42** mtime. It remains the escalation whose cost
  rises with delay (below).
- **Failability proofs and hot-path budget: not applicable.** This is a documentation pass — the diff
  introduces no boundary, guard, gate or rejection path, and no code path at all, so the mandatory
  re-run floor is computed over an empty set and the empty re-run set is legal on `worker-3.md`'s own
  terms. Worker 1's plan declared no hot path for this item and none could exist.

### Notes for Worker 1 (spec reconciliation)

No spec reconciliation owed; the spec is byte-unchanged and its four statements of this pair (`:647`,
`:648`, `:930`, `:1002`) were each opened here and are each true as written.

One note this pass adds, **recorded and not raised**:

- **`spec-009:654`'s `Phase 2 is the only window` is true only under its resolver scope**, and that
  scope is carried by the trailing `which is why **it** is a permanent mechanism` plus
  `rationale:306-310` rather than by anything nearer than seven lines. A cold reader who reaches `:654`
  from `### Layer 4`'s **annotation** bullet at `:647` can over-read the ordinal across the layer — the
  same over-read the repaired rationale clause made. It is in R1's `final-accepted` region, byte-
  unchanged, and graded a note by two prior passes and by this one. If a maintainer wants it tightened,
  the cheapest true form is naming the subject once (`Phase 2 is the only window for the resolver`),
  which asserts no new ordinal; it is a scope decision, not a correction, and should not be taken by a
  fix pass on its own authority.

Carried forward unchanged, report-only, none repaired by this pass:

1. **`spec-010:8` / `:491` and the `spec-010:67` coupling** — the concurrent cycle's; only the
   maintainer can sequence the two at commit. Both `spec-010` files were read read-only this pass.
2. **`types/definition.py::DjangoTypeDefinition`'s docstring** reserves `fields_class` for the
   pre-renumber `TODO-BETA-046-0.1.1`. Source is read-only in this cycle.
3. **The rationale's `## Standing notes` "three sites" bullet** is deliberately stale under append-only
   and flagged in-file five lines above it; the one-`-`-line proof shows it unmodified again this pass.
4. **`spec-009:592-597`'s registry-state sentence** is satisfied across two objects — registry-global
   `is_finalized` versus per-type `DjangoTypeDefinition.finalized`. Not false; a tightening pass should
   say which object holds which half.
5. **`rationale:359-360`** and **`rationale:533`**, both in R1's closed region, both graded notes by
   prior passes and unchanged here.
6. **Escalated: the one whose evidence inaction destroys.** No permanent test row pins
   `async def get_queryset` → `SyncMisuseError` for a *default* `DjangoConnectionField` under
   `await schema.execute`. The ready-made body at
   `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is gitignored and clears with
   the cycle. **Card it before the cycle closes** — this is the seventh pass to say so, and the only
   escalation whose cost rises with delay. Resolution paths: (a) card it now against the correct
   `AGENTS.md` test tree and let the body seed the card, or (b) accept the loss deliberately and record
   that the gap is known and unpinned.

### Review outcome

`review-accepted`.

The finding was correct and was re-derived here from source at both trees rather than accepted; the
remedy is a substitution of the document's own existing wording, which asserts strictly less than what
it replaces and is verifiable from the two symbols the sentence already cites; the alternative was
rejected for the right reason and the reason is recorded; the twin sweep reproduces at document and repo
scope with no orphaned twin; the checklist maps one box to one edit with no prior box rewritten; and
every gate, identity, append-only proof and ledger figure re-measured at `676f10d2` matches to the unit,
with the spec byte-identical by hash. No High, Medium or Low finding; no DRY finding; no unresolved
item. This is the first pass on this item where the change asserts no number, no ordinal and no set
relation — the three shapes that produced all six false corrections on this cycle.

### Status

`review-accepted`

---

## Final verification (Worker 1, pass 3)

Run 2026-08-16 by a fresh Worker 1 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-1.md`. **HEAD re-derived: `6f8bf818`** (`git rev-parse
--short HEAD` at the start of this pass, not inherited from the dispatch) — moved again from the
`676f10d2` Worker 3's pass 4 measured at. `git status --porcelain` is **170** entries, all of it the
four concurrent cycles, the REVIEW cycle, the DRY cycle and the package-source session. `git stash` /
`checkout` / `restore` / `worktree` were not used; every HEAD reference is `git show HEAD:<path>` into
an out-of-repo scratch path. Nothing outside this cycle's writable set was edited, reverted, or
`git checkout`ed. Nothing under `docs/builder/temp-tests/` was touched —
`docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is on disk at its unchanged
**1,565** bytes and **20:42** mtime.

**This item runs no tests and changes no code.** No `pytest` was invoked in this pass, with or without
`--cov*` flags, so `## Final verification job` step 5's focused run is vacuous and is recorded as such
rather than skipped silently. Step 6's staged-anchor sweep belongs to **R4** (`## Artifact list`: "the
staged-anchor sweep into R4") and was deliberately not duplicated here. The footprint is stated as a
footprint, per Worker 3's pass-3 Low 2: the item's entire working-tree footprint is `git diff --numstat`
**114 / 172** on the spec and **620 / 0** on the rationale, plus this artifact (`??`). **64** package
modules are dirty from the concurrent sessions and none of them is this item's.

**Spec status-line re-verification (per-spawn duty).** Lines 1-5 re-read. The opener describes the
rationale companion, the four finalization sites, and the six scrubbed mechanisms. Nothing R1b landed
falsifies any of it, and pass 3's single edit retires an ordinal rather than a mechanism. **No edit
owed.**

**Nothing was edited by this pass.** The one item below is recorded, not repaired. Every clean result on
this cycle has come from a verification pass that edited nothing; a custodian edit made here would be a
fresh unreviewed claim at the moment of acceptance, which is the failure this item exists to close.

### Method — the whole R1b diff read cold, in file order, at its symbols

Not pass 3's single clause, and not the prior findings' sites. The **five** changed spec lines and the
**whole** R1b rationale region (`:667-784`; R1's region is `:167-666` and closed under R1's
`final-accepted`, HEAD's pre-cycle text is `:1-166` and `:785-828`) were read in file order, with every
clause naming a checkable symbol opened at that symbol, and every absolute, ordinal, count and set
relation in the region extracted mechanically and graded one by one.

### Verification obligations — every proof re-run here, none read off a prior report

| Obligation | Result |
|---|---|
| Ledger — spec | `wc -c -l` → **61,170 / 1,096** ✓ |
| Ledger — rationale | `wc -c -l` → **60,351 / 828** ✓ |
| HEAD copies | `git show HEAD:` into an out-of-repo path → **54,232 / 1,154** and **12,273 / 208** ✓ |
| `--numstat` | spec **114 / 172**; rationale **620 / 0** ✓ |
| Identity 1 | `1,154 − 172 + 114 = 1,096` ✓ |
| Identity 2 | `208 + 620 = 828` ✓ |
| Cross-item byte chain | R1 closed at **61,082 / 1,096** (read at `bld-009-r1-spec_code_reconciliation.md:4758`); `61,082 + 54 + 34 = 61,170`, which is what the file measures ✓ |
| Append-only, `-` lines | `git diff -- <rationale> \| grep -c '^-'` → **1**, printed, and it is `--- a/docs/SPECS/appx/…` — no HEAD line deleted **or modified** ✓ |
| Append-only, hunks | `-U0` → `@@ -166,0 +167,618 @@`, `@@ -185,0 +804 @@`, `@@ -186,0 +806 @@`; `618 + 1 + 1 = 620` = the numstat addition ✓ |
| Append-only, prefix | `head -166` working `cmp` `head -166` HEAD copy → **exit 0**, both **10,772** bytes ✓ |
| Glossary gate | `check_spec_glossary.py --spec …spec-009…` → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0** ✓ |
| Comma gate | `check_trailing_commas.py --check` on **both** documents → **exit 0**; `shasum -a 256` on both captured before and after and `diff`-identical, so the auto-fixer wrote nothing ✓ |
| Spec byte-unchanged since pass 3 | `shasum -a 256` → `ae7deb30f66e35c5a98757e9c580fb1b17d67131b7cac4ded55585d33457b057`, matching Worker 3's pass-4 reading — an independent instrument, not "I did not edit it" ✓ |
| Numbering | `^### (Layer\|Phase\|Decision) [0-9]+` printed in file order: `Layer 1`-`11` at `576…799`, `Phase 1`-`8` at `903…985`, `Decision 1`-`6` at `995…1010`. **11 / 8 / 6**, no gap, no duplicate, **none renumbered** ✓ |
| In-page anchors | `grep -c '](#'` → **0 / 0**, so none can dangle ✓ |
| Link defs | independent parser (single `<!-- LINK DEFINITIONS -->` delimiter; uses harvested from the raw body so a ref-style use inside a code span still counts; `#fragment` stripped before the disk check): spec **25 defs / 25 uses**, rationale **11 / 11**; **0** missing, **0** orphan, **0** dead ✓ |
| Raw `path:NN` | `grep -nE '[A-Za-z0-9_/.-]+\.(py\|md):[0-9]+'` less `file:///` → **no match** in either permanent document ✓ |
| Cross-spec anchors | five, both directions, re-derived at the moment of dependence and every citing line read in full. `spec-010:67` cites `### Layer 3: Finalization trigger`, `spec-010:468` cites `### Decision 6: fail loudly`; `spec-009:99` / `:634` / `:870` cite spec-010's `### Must redo (not augment)` / `## Strawberry finalization strategy` / `### Unresolved-target error format`. **Heading-anchored** `grep -cE '^<heading>$'` returns **1** for all five, so each anchor exists and is unique. Both `spec-010` files read read-only ✓ |
| Provenance | `git log --stat` over **both** paths → the newest commit touching either is still **`f3c94642`**, with HEAD five commits further on at `6f8bf818`; the three behind it are `e1f9ed26`, `abb0dd12`, `81e4704d`. Nothing was swept into a concurrent commit. `git status` alone was not used as the test ✓ |
| Per-edit bytes | `awk NR==n \| wc -c`: `:394` **117**, `:417` **490**, `:610` **78**, `:930` **130**, `:1002` **362**; HEAD's `:393` **90** and `:651` **115**, so `+27` and `−37` reproduce against HEAD directly. `rationale:708` measures **98**, under the wrap ✓ |
| Structural bound on the spec's edit set | `--numstat` moved `112 / 170` (R1) → `114 / 172` (R1b) and has not moved since. Exactly **two** HEAD lines were ever modified by R1b; every other spec edit landed on an R1-added line, which cannot move the counts. An independent check on "seven edits and no eighth" ✓ |

**Enumeration and line coverage re-derived by parsing the tables, not by reading them.** A row is a
`|`-leading line outside a fence under a `| Site |` header; bucket on the last cell with `*` stripped,
which excludes the `### Revised denominator` summary table by its header. Result: **119** rows — **66**
`true`, **5** `FALSE`, **34** `judgement`, **10** `note (upstream)`, **4** `out of scope`;
`66 + 5 + 34 + 10 + 4 = 119`, opened **71**. Line coverage by expanding every `:NNN` / `:NNN-NNN` in
column 1 and unioning: **842 of 1,096**, **108** gaps / **254** lines, **no residual gap holding five or
more non-blank lines** — the largest holds **4** (`598-603`). **117** of the 119 rows carry a `:NNN`.
Every figure reproduces to the unit; this is the fourth consecutive pass whose counts survive a
mechanical recount unchanged.

### Planned steps — all landed, none rejected

`### Implementation steps` 1-4 are the four spec edits, verified at the lines; step 5 is the three
appended rationale entries (`:667`, `:688`, `:702`); step 6 is the gate / proof / ledger block, re-run
independently above. The apply-changes pass added three further spec edits and one further rationale
entry, pass 2 four clause edits, and pass 3 one — every one dispatched by a recorded finding. **No step
was rejected**, so no deferral reason is owed under `## Final verification job` step 3's last clause.

### `### Dispatched findings checklist` audit — fourteen boxes, fifteen edits, one-to-one

`grep -c '^- \[x\]'` → **14**, `'^- \[ \]'` → **0**. Self-derived on this item, so the audit runs
against the documents rather than a spec checklist. Each box opened at its current line, and where a box
quotes HEAD's text the corresponding HEAD line was `awk`'d out of the out-of-repo copy:

- `:610` → `relation_kind: RelationKind  # the alias in utils.relations, five members`; HEAD's `:651` is the quoted `Literal["forward_single", "many", "reverse_one_to_one"]  # mirrors utils.relations.RelationKind` line character-for-character.
- `:394` → `- [schema audit][glossary-schema-audit] can name the exact relation fields whose target model has no registered type`; HEAD's `:393` is the quoted `- [schema audit][glossary-schema-audit] can report exact unfinalized or unresolved fields` line character-for-character.
- `:930` → `grep -c 'visibility composition'` on the line → **0**; `in the cardinality-correct spelling` present (the Low 2 box).
- `:1002` → `, visibility composition, and arguments` **0** repo-wide in the spec; `queryset-owning components` present (the Consequential box).
- High (rationale visibility argument) → rewritten at `:702-761`: `grep -c 'reaches none of them'` → **0**, the five-of-eight list is gone, and the harm clause is the inverted one.
- Medium `:417` → spec edit **plus** the new rationale entry at `:763`, keyed to the real spec heading `### Borrow \`StrawberryDjangoFieldBase\` and \`StrawberryDjangoField\`` (`spec:405`).
- Medium `MANY_SIDE_RELATION_KINDS` → `:674-677` quotes `frozenset({"many", "reverse_many_to_one", "generic"})` and carries the "two of those three / the sketch's own `"many"` is the third" framing.
- Low 1 (apply pass) → explicitly no document edit; disposition recorded.
- Medium (pass 2) → `:682`; `grep -n 'one place'` over the rationale returns exactly **one** line, `:533`, graded below, so no replacement-count survives in the deleted clause's own entry.
- Low 1 (pass 2) → `:757-761` polarity swap, verified at the line.
- Low 2 (pass 2) → `:732` reads `imported by no package module but`, and `grep -c "grep -rn 'apply_type_visibility"` over the rationale → **0**, the command deleted and the eight names kept.
- Medium (pass 3) → `:708` reads `cardinality-correct spelling, at finalization.`

**No box lacks an edit and no edit lacks a box.** The permanent-document changes are exactly seven
spec-line replacements across five lines, four appended rationale entries, and five in-place clause
corrections inside this cycle's own appended text; each maps to a box, and correction 3 of pass 2 is the
one box covering two clause edits, stated as such in its own demarcating paragraph. Every box is `- [x]`,
so no deferral reason is owed. No prior box was rewritten — the three demarcating paragraphs are intact
and in pass order — and none of R1's sixteen contracts is reversed: `:930` and `:1002` were narrowed
further in the same direction, never restored.

### Cold read of the five changed spec lines, at their symbols

- **`:394`** — `optimizer/extension.py::DjangoOptimizerExtension.check_schema` (read whole, by AST) walks `_collect_schema_reachable_types(schema)`, skips non-relations and `OptimizerHint.SKIP`, and appends one warning per exposed relation whose `meta.related_model` has no `registry.get(...)`. Its own docstring states the same condition. The replacement text is that condition. **True.**
- **`:417`** — `types/resolvers.py` carries **0** `async def` / `await ` and **0** `apply_type_visibility`; `utils/querysets.py::SyncMisuseError` is a real class (`ConfigurationError, RuntimeError`) raised on the sync path. "Runs at the queryset-owning seams `### Layer 4` names, never inside the generated resolver" holds, and `:415`'s "it is not repeated here" is restored: `:417` is the next non-blank line and now points rather than repeats. **True.**
- **`:610`** — `utils/relations.py` defines `RelationKind: TypeAlias = Literal["many", "reverse_many_to_one", "reverse_one_to_one", "forward_single", "generic"]`, read at the source. Five members, in `utils.relations`. **True.**
- **`:930`** — `types/converters.py::resolved_relation_annotation` returns `list[target_type]` on `is_many_side`, `target_type | None` on `nullable`, else `target_type` — Layer 4's "cardinality-correct spelling", read at the body; `types/resolvers.py::_attach_relation_resolvers` installs one generated resolver per selected relation. **True.** Examined and not raised, unchanged from two prior passes: `_attach_relation_resolvers` skips `skip_field_names`, so "every exposed relation" is not literally exhaustive — the carve-out exists so a consumer override is not clobbered, and Layer 4's own resolution bullet is scoped the same way.
- **`:1002`** — same two symbols plus `types/finalizer.py::_synthesize_relation_connections` for the argument seam. `optimizer/walker.py::_build_child_queryset` is a module-level `def` (AST, `walker.py`), i.e. genuinely not a field, so "queryset-owning **components**" is the apt noun for both the visibility appliers and the argument owner. **True.**

### Cold read of R1b's whole rationale region (`:667-784`), at its symbols

Every mechanism claim re-derived from source in this pass, none accepted from a prior report:

- **`:671-678`** — `RelationKind` has five members and `MANY_SIDE_RELATION_KINDS` is `frozenset({"many", "reverse_many_to_one", "generic"})`, both read at `utils/relations.py`; the quotation is character-exact. The set algebra holds: the sketch's dropped `{"reverse_many_to_one", "generic"}` are two of that three and its own `"many"` is the third. `utils/relations.py::relation_kind` returns `"generic"` for a `GenericRelation`, so the harm statement holds. **True.**
- **`:691-694`** — `check_schema`'s walk and single warning shape, above. **True.**
- **`:699-700`** — *"the finalizer's own `ConfigurationError` is the only thing that speaks to unresolved targets before a schema exists"*. Swept every `unresolved` occurrence in the package: the only pre-schema unresolved-**relation-target** reporter is `types/finalizer.py::_format_unresolved_targets_error`, raised as `ConfigurationError`; the other hits are a different sense of the word (lazy string hops, deferred filters, a `FieldSet` expansion `ImportError` — itself also a finalizer `ConfigurationError`). **True as scoped.**
- **`:705-713`** — the repaired clause. AST call-site enumeration over the package returns **exactly one** call site of `resolved_relation_annotation`, `types/finalizer.py:887` in the working tree, and its enclosing function is `finalize_django_types` (`763-1088`); `_attach_relation_resolvers` is called at `:911`, also inside it. **`at finalization` is true of both seams**, which is what the remedy needed. `grep -c apply_type_visibility` on `types/finalizer.py` and `types/resolvers.py` → **0 / 0**; the three emitted shapes `many_resolver` / `reverse_one_to_one_resolver` / `forward_resolver` all exist at `types/resolvers.py`. **True.** ("Returns the row-bound accessor" stays the accepted `### Layer 4` shorthand, graded a note by pass 2 and unchanged.)
- **`:720-733`** — the two gating conditions, re-derived in call order without reading the prior passes' line numbers: `optimizer/walker.py::plan_relation` tests `_target_has_custom_get_queryset(target_type)` **above** `is_many_side_relation_kind(...)` and returns `("prefetch", "custom_get_queryset")`; `_plan_prefetch_relation`'s only early return is `if django_field.related_model is None:`; `_build_child_queryset`'s `if has_custom_qs:` branch is `apply_type_visibility_sync(target_type, queryset, info, allow_sliced=True)`, quoted character-for-character including `allow_sliced=True`. `_synthesize_relation_connections`'s docstring gates on Relay-Node-shaped source and target, many-side, and shape, with `"list"` = *"synthesize nothing"*. `plan_optimizations` importers by AST over every `*.py` outside `.venv`: package = **1**, `optimizer/extension.py:95`. **All true, and the conditions are stated as necessary rather than absolute.**
- **`:752-754`** — *"the generalisable rule this document has now produced twice"* is a count, so it was checked: the first production is `rationale:477-482` (R1's, on *"the single place every cardinality's access passes through"*), the second is this one. **Twice is exact.** Phase 2.5 = `_synthesize_relation_connections`, whose docstring removes the generated list annotation and the Phase-2 list resolver before Phase 3 — the re-shaping the rule asserts. **True.**
- **`:757-761`** — the inverted harm clause. `types/base.py::DjangoType.get_queryset` is a documented identity hook; `forward_resolver`'s reachable exit without the extension is the row-bound accessor; `schema.py` carries **0** `DjangoOptimizerExtension` references. The narrowing to **forward single** errs safe. **True.**
- **`:766-783`** — the `:417` entry. Tokenizing every package module and dropping `tokenize.COMMENT` / `tokenize.STRING` lines gives **exactly eight** distinct executable-invocation modules — `connection.py`, `filters/sets.py`, `list_field.py`, `mutations/resolvers.py`, `optimizer/walker.py`, `permissions.py`, `types/relay.py`, `utils/querysets.py` — the listed set character-for-character. "Two lines below" reproduces (`:415`, blank `:416`, `:417`). The three characterisations of the non-relation-read seams each hold at the call site: `permissions.py` inside the cascade edge-state block, `filters/sets.py` inside `_iter_visibility_steps`, `mutations/resolvers.py` inside `pin_write_queryset`. **True.**
- **Single ownership re-derived, not read.** `grep -n apply_type_visibility` over the spec returns exactly **two** hits: `:417` (a pointer) and `:649` (`### Layer 4`'s bullet, the one telling). `:930` carries `— Layer 4` and `:1002` names the heading. No fourth copy.
- **`:776`'s "three halves that disagreed"** — graded a **note**. "This document" has a loose antecedent (the sentence sits in the rationale but its subject is the spec's map), and the count is exact under the reading Worker 3 recorded independently at pass 2 — four spellings of which three disagreed with `### Layer 4`. Not false under every reading, which is the bar; recorded so a later pass does not re-open it as new.

### `spec-009:654` — Worker 3's "note, not a finding" grading is CONFIRMED, on a corrected ground

The dispatch asks for confirmation or reversal. **Confirmed** — the grading holds and the line stays
unrepaired — but the ground Worker 3 stated is the weaker half and should not be carried forward as
recorded.

- **The stated ground does not survive measurement.** Worker 3's pass 4 grades it a note because "its own trailing clause fixes the subject on-page — only `_attach_relation_resolvers` was ever accused of being transitional". Measured: `grep -n 'transitional\|transition'` over the whole spec returns **exactly one** line, `:654` itself. The word has **no antecedent on the spec page at all**; the accusation it answers lives only in `rationale:306-310`. The disambiguator is in the companion, not on the page.
- **The grading is nevertheless right, on two grounds that do survive.** (a) `rationale:306-310` pins the subject explicitly and in the identical wording — *"The claim `### Layer 4` may no longer make: that `_attach_relation_resolvers` is transitional … so Phase 2 is the only window"* — so the sentence has a documented intended reading under which it is exactly true. (b) That is the difference from `rationale:708`, which this cycle graded a Medium and fixed: `:708` **named `resolved_relation_annotation` in the same sentence**, so it was false under every reading. `:654` names no symbol and is true under its pinned one. Re-opening R1's `final-accepted` region needs falsity, not looseness — the standard already applied to `:533` and `rationale:359-360`.
- **What is genuinely true and worth the maintainer's attention.** Read at whole-layer scope the ordinal is wrong three ways, not one: the annotation seam runs at Phase 1 (`:647` names no phase), the connection synthesis at Phase 2.5, and the argument seam is `connection.py::DjangoConnectionField`'s, not the finalizer's at all. Worker 3's proposed cheapest true form — `Phase 2 is the only window for the resolver` — asserts no new ordinal and costs three words. **It is a scope decision for the maintainer, not a correction a fix pass takes on its own authority**, and it is not this item's defect: the line is byte-unchanged this cycle.

### The one item this pass adds — Low, artifact-only, and corrected in this section rather than propagated

**The `### Summary` blocks attribute two of R1b's five findings to pre-existing text that HEAD does not
contain.** Every prior summary on this item states the yield as *"four false clauses in 984 pre-existing
lines"*, naming `:610`, `:394`, `:930` and `:1002` as the four. Measured against HEAD:

- `git show HEAD:<spec>` contains **0** occurrences of `visibility composition` and **0** of `apply_type_visibility`. HEAD's `### Layer 4` is titled `Strawberry-native field class`, its `### Phase 3` is `DjangoModelField`, and its `### Decision 3` is `custom Strawberry field class`. All three sections are R1's rewrite, so `:930`, `:1002` **and** `:417` are text this cycle added.
- HEAD carries `:393`'s schema-audit bullet and `:651`'s `Literal[...]` line verbatim. Those are the **two, and only two**, HEAD lines R1b ever modified — which the `--numstat` bound (`112 / 170` → `114 / 172`) independently confirms.

So the true split of R1b's five `FALSE` rows is **two in the 984 pre-existing lines** (`:394`, `:610`)
and **three in the cycle's own added text** (`:417`, `:930`, `:1002`).

**Disposition: Low, artifact-only, no document edit owed, and it does not hold the item.** The twin
check was run per item rather than asserted for the set: `pre-existing`, `984`, `prescriptive`,
`prescription`, `added text` and `added-text` return **0** in the spec; the rationale's two hits are
`:663` (the `## Standing notes` bullet, correctly called pre-existing — it is HEAD's `:167+`) and `:747`
(*"judged non-findings during the **added-text** sweep"*), which classifies `:930` / `:1002` **correctly**.
The permanent record is right; the artifact's `### Scope` at `:26-28` is right ("plus two added-text
sites the maintainer routed here explicitly"); only the summary prose slipped, and `bld-*.md` closes
with the cycle (`START.md` "Temp artifact conventions"). That is the disposition four prior
artifact-only Lows on this item already carry.

**The structural conclusion is strengthened, not weakened, which is why this is a correction and not a
retraction.** Two findings in 984 pre-existing lines against three more in the 114 the cycle touched — on
top of R1's own findings, all of which were in that same added text by construction, R1's scope having
been the 112 added lines — makes the density gap *wider* than the reported ratio, not narrower. R1's own
count is not re-derived here and is not asserted as measured by me.

### DRY check across this item and prior accepted items

No new duplication. The item's whole shape is de-duplication: three restatements of `### Layer 4`'s seam
map collapsed to pointers, one membership claim collapsed to a quoted constant, one to an alias name,
and the five in-place corrections are four subtractions and one one-clause narrowing. Re-derived rather
than read: the spec's seam map now has exactly one telling and three pointers. **No DRY opportunity
remains open**, and the existence challenge does not arise — R1b introduces no vocabulary, constant,
convention, registry or indirection.

### Escalations carried forward — report-only, unrepaired

1. **`spec-010:8` and `:491`, and the `spec-010:67` coupling** — surfaces this cycle scrubbed, owned by the concurrent spec-010 cycle; only the maintainer can sequence the two at commit. Both `spec-010` files read read-only this pass; nothing edited, reverted, or `git checkout`ed.
2. **`types/definition.py::DjangoTypeDefinition`'s docstring** reserves `fields_class` for the pre-renumber `TODO-BETA-046-0.1.1`. Source is read-only in this cycle.
3. **The rationale's `## Standing notes` "three sites" bullet** is deliberately stale under append-only and flagged in-file five lines above it; the one-`-`-line proof shows it unmodified again this pass.
4. **`spec-009:592-597`'s registry-state sentence**, satisfied across two objects (registry-global `is_finalized` versus per-type `DjangoTypeDefinition.finalized`); **`rationale:533`**; **`rationale:359-360`**; and **`spec-009:654`** (above) — all graded notes, none false, all in `final-accepted` regions.
5. **The async `SyncMisuseError` coverage gap is NO LONGER an open escalation.** The maintainer decided it (`### Maintainer decision 5`, read at the build plan): the ready-made body at `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is promoted to a permanent test **in this cycle**, as item **R1c** — the cycle's only code-writing item, carrying a failability proof and its own floor run. It is scheduled work, not an unowned risk, and the seven-pass "needs carding" flag stops here.

### Summary

**What R1b shipped.** A clause-by-clause mechanism sweep of all 1,096 lines of
`spec-009-rich_schema_architecture-0_0_4.md` — the 984 lines identical to HEAD that no pass had opened at
the mechanism level, plus the two added-text sites the maintainer routed here — under
`### Maintainer decision 4`. The defect class: *a sentence asserting a mechanism, seam, cause, recourse,
or capability the code does not have.*

**The yield, and why the ratio is structural.** The sweep found **five** false clauses. Measured against
HEAD rather than assumed: **two** of them (`:610`, `:394`) sit in the 984 pre-existing lines, and three
(`:417`, `:930`, `:1002`) sit in text this cycle had added — R1 rewrote `### Layer 4`, `### Phase 3` and
`### Decision 3` wholesale, and HEAD contains no occurrence of `visibility composition` or
`apply_type_visibility` at all. Set beside R1's own findings, every one of which was in the 112 lines it
added, the density gap between pre-existing and fix-pass text is **wider** than this item's earlier
summaries reported. **The reason is structural rather than lucky.** A horizon document's pre-existing
text is overwhelmingly **prescriptive** — "should", "take this", "recommended adaptation", "borrow the
behaviors not the class" — and **a prescription cannot be false about a mechanism**: the defect class
needs a present-tense assertion to attach to, and prescriptive text offers far fewer of them per line
than a fix pass's connective tissue does. Both pre-existing findings sit in the only places such text
does assert present tense — a code-sketch comment (`:610`) and a `Benefits:` list (`:394`) — and the
three in added text are one-line restatements of another section's map (`:930`, `:1002`) and a
section-closing paragraph (`:417`). **The operational lesson for any future sweep: go straight to
code-sketch comments, `Benefits:` / `Implementation:` lists, one-line restatements of another section,
and section-closing paragraphs — and skip the "should" prose.**

**The five corrections that landed**, all single-line, no renumbering, no heading text changed, no
section added or removed:

1. **`:610`** — `Literal["forward_single", "many", "reverse_one_to_one"]  # mirrors utils.relations.RelationKind` (three of five members, asserting a mirror it did not have) → `relation_kind: RelationKind  # the alias in utils.relations, five members`. Replaced with the alias rather than re-spelled: a copied enumeration is true today and false on the next member.
2. **`:394`** — "can report exact **unfinalized** or unresolved fields" → "can name the exact relation fields whose target model has no registered type", which is `check_schema`'s own reported condition. Narrowed rather than cut because the bullet is the sole `[glossary-schema-audit]` use and cutting it would have dropped the term count 23 → 22.
3. **`:930`** (`### Phase 3`) — visibility composition cut from the generation list, and the surviving "across every cardinality" absolute replaced by `### Layer 4`'s own "in the cardinality-correct spelling".
4. **`:1002`** (`### Decision 3`) — visibility and arguments cut from the generation list and attributed to "the queryset-owning **components** `### Layer 4` names", so the decision still accounts for all four seams without writing a third copy of the map.
5. **`:417`** — a third copy of the seam map naming three of eight invoking modules, a *different* incomplete triple than `### Layer 4`'s, standing **two lines below** `:415`'s own "it is not repeated here" — the spec contradicting itself on the page. Replaced by the same pointer-shrink.

**The reversal is the substantive one.** R1's final verification had judged `:930` / `:1002`
non-findings; R1b reversed that on the fail-open direction of a **row-visibility** claim, and the
reversal's conclusion — the finalizer composes no visibility at any cardinality — was re-derived
independently again in this pass at `plan_relation` → `_plan_prefetch_relation` → `_build_child_queryset`,
with `grep -c apply_type_visibility` returning **0** in both `types/finalizer.py` and
`types/resolvers.py`, **0** `DjangoOptimizerExtension` references in `schema.py`, and one package
importer of `plan_optimizations` by AST. The reversal's *argument* was itself false when first written
and was rewritten in place; its two gating conditions are now stated as necessary rather than absolute.

**Post-fix the seam map has exactly one telling** — `### Layer 4` (`:644-654`) — with `:417`, `:930` and
`:1002` pointing at it, re-derived here as exactly two `apply_type_visibility` occurrences in the spec.
Four rationale entries record the reasoning, each keyed to the spec heading it belongs to (both `### Borrow`
entries verified against the real headings at `spec:367` and `spec:405`), each with its rejected
alternative and the reason it lost.

**Final enumeration denominator and coverage map.** **119** clause sites across all 1,096 lines: **66**
`true`, **5** `FALSE` (all corrected), **34** `judgement`, **10** `note (upstream)`, **4** `out of
scope`; **71** opened at the symbol they name. Line coverage **842 / 1,096**; residue **108** gaps /
**254** lines with **no residual gap holding five or more non-blank lines** (largest is four). **The
gap-size criterion was accepted because the residue it cannot see was discharged, not because the
criterion is sound**: eleven single-line present-tense survivors sit *between* covered rows and all
eleven were opened — six by Worker 3, six by the pass-2 final verification, one overlapping — and all
held. Carry the instrument forward as **line coverage plus a scan of the uncovered non-blank lines**.

**Ledger, with closing identities.** Spec **61,170 bytes / 1,096 lines** (HEAD: 54,232 / 1,154);
rationale **60,351 / 828** (HEAD: 12,273 / 208). `git diff --numstat`: spec **114 / 172**, rationale
**620 / 0**. Both identities close: `1,154 − 172 + 114 = 1,096` and `208 + 620 = 828`. The cross-item
chain closes: R1 ended at **61,082 / 1,096**, and `61,082 + 54 + 34 = 61,170`, which is what the file
measures. Append-only holds the strong way — one `-` line and it is the `--- a/` header, so no HEAD line
was deleted or modified; hunks `618 + 1 + 1 = 620`; `head -166` `cmp`s exit 0 against HEAD's copy at
10,772 bytes. Gates: glossary **23 terms, exit 0**; trailing commas **exit 0** on both with `shasum`
unchanged across the runs; **25/25** and **11/11** link definitions with 0 missing / 0 orphan / 0 dead;
**0** in-page anchors; **0** in-repo raw `path:NN`; Layers **11** / Phases **8** / Decisions **6** intact
and un-renumbered; five cross-spec anchors unique in both directions. `git log --stat` over both paths:
the newest commit touching either is still **`f3c94642`** with HEAD at `6f8bf818` — nothing was swept
into a concurrent commit.

**For the maintainer at commit time.** The item is two `.md` files. R1b's own contribution is `+88`
bytes on the spec across seven single-line replacements on five lines, and the rationale's
`:667-784` region — measured **118 lines / 9,269 bytes** — of four appended entries carrying five
in-place clause corrections. The two files' whole working-tree delta against HEAD, R1's work included,
is `+6,938` bytes on the spec and `+48,078` on the rationale. No source, no test, no third document, no
KANBAN or glossary surface. The one clause a future reader should not re-open is `spec-009:654`, graded
a note three times and carrying a maintainer-only tightening (`Phase 2 is the only window for the
resolver`) if the ordinal's layer-wide reading is judged worth four words.

### Spec changes made (Worker 1 only)

**None.** This pass edited neither the spec nor the rationale. The one item it adds is artifact-only,
carries no twin in either permanent document (checked per item, not asserted for the set), and is
corrected in this section rather than propagated — so no fresh unreviewed claim enters a permanent
document at the moment of acceptance.

No `### Dispatched findings checklist` box is left `- [ ]`, so no deferral reason is owed under
`## Final verification job` step 3.

### Final status

`final-accepted`.

Every planned step landed and none was rejected. The fourteen self-derived checklist boxes map
one-to-one onto fifteen edits with no box un-ticked, no box over-ticked, and no edit lacking a box. The
whole R1b diff — five changed spec lines and the entire `:667-784` rationale region — was read cold, in
file order, at its symbols, with every absolute, ordinal, count and set relation in the region extracted
mechanically and graded; every mechanism claim holds, and the one clause pass 3 changed asserts strictly
less than what it replaced. Every gate, identity, per-edit byte, append-only proof, anchor, enumeration
bucket and coverage figure re-runs clean and reproduces to the unit. `spec-009:654`'s note grading is
confirmed on a corrected ground. The single item this pass adds is a summary attribution confined to this
artifact, which closes with the cycle; it is corrected above rather than carried forward, and the
structural conclusion it qualifies is strengthened by the correction. **Nothing on this item is open.**
