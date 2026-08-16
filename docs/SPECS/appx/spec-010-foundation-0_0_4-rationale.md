# Rationale: spec-010 — 0.0.4 foundation slice (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-010-foundation-0_0_4.md`][spec-010]. The spec states the
implementation contract for the 0.0.4 foundation slice; everything that explains **how a claim in it
came to be corrected** lives here — the text cut out of the spec, the reason each cut was owed, and
the measurement that established it.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass, long after the
release rather than before the build. Card `DONE-010-0.0.4` shipped many minor versions ago and the
rule that gates a build on this move did not exist then. Text marked *Moved* below was cut out of the
spec, not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec section**, named by the section's own heading. A section with no entry in
  either block below lost nothing to either pass — that is not an omission.
- **The file has three blocks, and they answer different questions.**
  `## Entries keyed to the spec` records what was **cut out of** the spec: one retired section, and
  the citation convention that stopped being true.
  `## Reconciliation pass` records what the **surviving prose was turned into**: for every contract
  a later card or spec reshaped, what spec-010 used to claim, what is true now, which change caused
  it and why that change was right, and which alternative the change rejected.
  `## Coverage pass` records the one claim that was never true — a worked example the spec has
  carried since `0.0.4`, corrected when a test was finally written against it. Together they are the
  whole account.
- **The spec never narrates its own history** ([`BUILD.md`][build] `## Spec rationale extraction`),
  so every corrected claim was rewritten to state the contract that holds — no amendment block, no
  retraction, no "as of spec-NNN". A reader who has to reconstruct what is currently true by applying
  a chronology is reading a changelog. The chronology is here instead, and this file is the only
  place it exists.
- **Do not read this file as a description of the shipped machinery.** The `finalize_django_types()`
  phase order, the `PendingRelation` shape and the registry extensions are the spec's and the
  [glossary][glossary]'s.
- **In-repo citations are symbol-qualified**, per `AGENTS.md` rule 27. Third-party citations are
  not, and deliberately so — see the entry for `## What we take from strawberry-graphql-django`.

## Provenance of this record

Every claim below was re-derived against the working tree at the time of the pass, not carried from
an earlier report. Two measurements are quoted rather than restated, because both had been reported
wrong at least once before:

- The spec carried **42 raw `path:NN` occurrences on 30 lines**. Of those, **22 occurrences on 16
  lines** were in-repo citations that rule 27 forbids, and **20 occurrences on 14 lines** were pinned
  third-party prior art, which the rule does not reach.
- An earlier pass reported this split as 20-on-15 in-repo and 22-on-15 third-party. That is the two
  halves transposed and both line counts wrong. It is recorded here because the transposition is
  invisible in the total — 42 and 30 both reconcile either way — so only a re-derivation of the split
  itself catches it. The counts above come from
  `grep -Eo '[A-Za-z0-9_/.-]+[.](py|md|toml|cfg|yaml|yml):[0-9]+(-[0-9]+)?'` over the spec, partitioned
  on the `strawberry_django/` / `graphene/` / `graphene_django/` roots.

## Entries keyed to the spec

### `## Note on source line references` — removed whole

*Moved.* The spec carried this section:

> This spec includes line numbers for some current source files (e.g., `walker.py:64`,
> `base.py:147`). Those are accurate at the time of writing but the optimizer subsystem and
> `__init_subclass__` are still moving, so reviewers should treat in-repo line references as soft
> hints and verify against the symbol names (`_optimizer_field_map`, `_attach_relation_resolvers`,
> `plan_relation`, etc.). Exact line references are reliable for **external** prior-art snapshots
> (`strawberry_django/...`, `graphene_django/...`, `graphene/...`) because those repos are pinned.
> Before implementation begins, the assigned author should refresh the in-repo lines in this spec's
> "Migration of current code" section against `main` so the contributor's edit targets are not stale.

**Why it went.** The section is not merely stale, it is the thing that made the staleness permanent.
It institutionalized addressing moving in-repo source by line and then asked every future reader to
absorb the cost — treat the references as soft hints, verify the symbol yourself, and refresh them
before implementing. `AGENTS.md` rule 27 later settled the question in the opposite direction: an
in-repo citation names a symbol. Converting the 22 in-repo occurrences while leaving this section
standing would have produced a spec whose text told readers to expect line numbers it no longer
carried, so the conversion and the retirement are one change and could not be split.

**The instruction it carried was never dischargeable.** "Before implementation begins, the assigned
author should refresh the in-repo lines" was written for a slice that has since shipped; there is no
future author to address it to, and the refresh it asks for is exactly the work rule 27 makes
unnecessary. Its own examples had rotted to the point of proving the argument — of the four symbols
it named as the reliable fallback, `_optimizer_field_map` no longer occurs anywhere in the package,
and the walker reads the field map through
`django_strawberry_framework/optimizer/walker.py::_resolve_field_map` instead.

**What survived, and where.** One clause was load-bearing and was not discarded: that exact lines
*are* reliable for pinned third-party snapshots. That is the standing justification for the 20
surviving third-party citations, so it moved to the point of use, in the opening paragraph of
`## What we take from strawberry-graphql-django`. It is stated there as the convention it is — a line
is addressed only when the file it addresses cannot move — rather than as a caveat about this
document.

### `## What we take from strawberry-graphql-django` — scope of the surviving line references

The first draft of the replacement sentence scoped the convention to "this section and the
graphene-django section below". That was false on measurement: four third-party citations sit outside
both sections, in `### PendingRelation` and `### TypeRegistry extensions`. The correction generalizes
the rule to every third-party citation wherever it appears, which is what the convention actually is.

Recorded because the error is this pass's own instance of the defect class the cycle was chartered
against — a claim whose subject was assumed from where the text sat rather than measured against the
population. The catching mechanism was re-running the partitioned grep after the edit rather than
before it.

### `## Migration of current code (per the verification report)` — two cited symbols no longer exist

The conversion to symbol-qualified form left two citations naming symbols the package has since
retired: `types/converters.py::convert_relation` and `registry.py::TypeRegistry.lazy_ref`. Both were
kept, and neither was silently repointed at a live symbol.

**Why keeping them is correct.** This section is a migration record: it describes what the 0.0.4
slice changed, starting from the pre-slice state. `convert_relation` is named as the function the
slice rewrote and `TypeRegistry.lazy_ref` as the placeholder it deleted — the spec's own text says
**Deleted** — so both names are load-bearing history. Repointing them at
`types/converters.py::resolved_relation_annotation` would make the record describe a migration that
never happened. This is the same boundary the board has already ruled twice, most recently on the
`convert_relation` sweep item carried by `TODO-ALPHA-051-0.0.15`: a present-tense survival in a
shipped spec is correct as history and is not in a sweep.

**The residual risk, stated rather than fixed.** A symbol-qualified citation to a retired symbol
still reads as a live pointer to a reader who does not notice the section it sits in. The
countermeasure available today is the section framing; the durable one is the source-symbol-citation
checker scoped by `TODO-ALPHA-052-0.1.0`, whose own specification already names this exact case —
distinguishing a live spec's claim from a shipped spec's history — as the thing it must get right.

### `## Strawberry finalization strategy` and `### Unresolved-target error format` — two inbound citations repointed

Both cited [`spec-009-rich_schema_architecture-0_0_4.md`][spec-009] by raw line range. One was
merely a rule-27 violation; the other was also aimed wrong.

- `(670-687)` addressed the auto-trigger direction. The subject was right and the form was not; it
  now reads `#"### Layer 3: Finalization trigger"`.
- `(1076-1077)` was cited as the **source of the requirement** that the unresolved-target error name
  the source model, source field and target model. Those lines carry
  `### Should multiple DjangoTypes per model be allowed?` — a different question entirely. The
  requirement sits seven lines earlier, at `### Decision 6: fail loudly`, which is what the citation
  now names.

**Why the second one is the more interesting failure.** It resolved. A reader following it landed in
the right document, in the right neighbourhood, on prose about the same subsystem — and not on the
claim. That is the separating test this cycle put into words: a pointer that lands on a section about
the right subject is not thereby a pointer to the claim, and the only pointer that survives a later
edit of its destination is one the destination names. A heading anchor satisfies both tests; a line
range satisfies neither, because it silently re-aims every time the target file grows a paragraph.

## Standing notes

- **The third-party citations are not debt.** Twenty raw `path:NN` occurrences survive in this spec
  by design. Rule 27 governs in-repo source, whose line numbers move under the repository's own
  commits; a pinned upstream snapshot cannot move, and a line is the most precise address available
  for it. A future sweep that "finishes the job" by converting these would replace exact addresses
  with vaguer ones.
- **The spec's decisions were not touched.** This pass corrected two citations, converted the in-repo
  citation form, and retired one section. No contract, error string, phase order or invariant in
  spec-010 was changed, and nothing in the package was edited on its account. The pass that follows is
  where the contracts themselves were reconciled.

## Reconciliation pass — what the spec now says, and why

The pass above moved the deliberative layer out and deliberately left every contract standing. This
section is the second pass's record. Spec-010 shipped at `0.0.4` and the foundation it laid is the
layer every later card built on, so fifteen of its statements had been overtaken by work that
extended them. Each was rewritten to state the contract that holds at `HEAD`, directly; each entry
below carries what the spec used to claim, what is true now, the spec or card that caused the change
and why that change was right, and the alternative the change rejected.

**One judgement call governs the whole section, and it was the hard part.** Spec-010 owns the
foundation layer — the definition object, pending relations, the finalization lifecycle, the
consumer-override contract for relation fields, and the registry extensions. It does not own filters,
orders, relay, connections, mutations, GlobalID encoding, or file/image output mapping. Every one of
the fifteen findings sits on surface that a later spec extended, and reconciling against `HEAD` pulls
hard toward absorbing that surface, because all of it is visible in the code spec-010 designed. Each
was resolved the same way, and the discipline is one the spec had already found for itself: its
`### Finalization phase` calls the three-phase lifecycle "a skeleton later slices insert into rather
than a closed list" and pushes the inserted phases' contents to the specs that shipped them.
**Extended to every other section, that means: where a slot or a phase exists but belongs to another
document, name the seam and point at the owner; never transplant the paragraph.** A contract told
twice goes stale in one of the tellings, and spec-010 is the wrong of the two to keep current.

### `### Collection phase: DjangoType.__init_subclass__` — step 8's eager-bind arm (F1)

*Claim the spec no longer makes.* That collection resolves a relation immediately when
`registry.get(field.related_model)` already answers, and defers only an unknown target.

*What is true now.* Every auto-synthesized relation defers unconditionally. The target's registration
state at class-creation time is not consulted at all
(`django_strawberry_framework/types/base.py::_build_annotations #"Always defer auto-synthesized relation annotations"`).

*What caused it, and why it was right.* `spec-018-meta_primary-0_0_6.md`. Once a model may carry more
than one `DjangoType`, an eager bind freezes the annotation against whichever type happened to be
registered when this class body executed — which need not be the type the relation should resolve to
once every module has been imported. That is import-order-dependent schema shape, and refusing it is
spec-010's own second invariant. The eager arm was not merely made redundant by the primary layer; it
was the mechanism by which the primary layer could have been silently defeated.

*Alternative rejected — defer only when the target model already has two or more registered types.*
It reads as the minimal fix and it does not work: the second registration arrives **after** the first
bind, so at the moment of the eager bind the ambiguity is not yet observable. A rule that can only see
the registry's current state cannot decide anything that depends on its final state. Deferring
everything means one resolution rule runs once, over a settled registry, for every relation.

*Alternative rejected — keep the eager arm behind a "single registered type" fast path for
performance.* Collection runs once per class at import; there is no hot path here to buy back, and the
branch's whole cost is a dictionary lookup the finalizer performs anyway.

### `## What does not ship in this slice`, `### TypeRegistry extensions`, `### Stays deferred` — the duplicate-model claim (F2)

*Claims the spec no longer makes.* That `Meta.primary` is unshipped. That "the current
registry hard-fails on duplicate models, and that stays". That `_types` is
`dict[type[models.Model], type]`.

*What is true now.* `_types` is `dict[type[models.Model], list[type]]` beside a `_primaries` map;
`register` takes `primary=` and returns whether it added state; `primary_for`, `types_for` and
`models_with_multiple_types` exist; and `registry.get()` returns the declared primary, or the single
registered type, or `None` when several are registered with no primary
(`django_strawberry_framework/registry.py::TypeRegistry.get`).

*What caused it, and why it was right.* `spec-018-meta_primary-0_0_6.md`. A hard failure on the second
registration is the correct default only while there is no way to express which of two types a
relation means; once `Meta.primary` exists the failure is the wrong shape, because the legitimate case
— an admin-facing type and a public type over one model — was unrepresentable rather than merely
unvalidated. What survived is the strictness, relocated: ambiguity is refused at finalization by an
audit that names the offending model, rather than at import by a registration that names only the
second arrival.

*Alternative rejected — restate spec-018's selection rule here.* The strongest pull in the pass,
because the registry pseudocode is spec-010's and the reader is right there. It loses because the
resolution order, the ambiguity audit's message, and the `primary=` collision rules are one contract
with one owner, and a second copy in the foundation spec would go stale on spec-018's next edit while
looking authoritative. What spec-010 keeps is the shape that makes multiple registrations
*representable* — that genuinely is the foundation's, since the many-valued map is what let spec-018
land without reshaping this layer — plus one clause naming who owns the rule.

*Alternative rejected — delete the "What does not ship" bullet outright.* Tempting once the claim is
false, and wrong: the bullet's job is to draw the slice's boundary, and the boundary is still real.
It was rewritten to draw it where it now sits — the registry's shape inside, the selection rule
outside — rather than removed.

### `### Collection phase` step 13 and `### Should redo now` — the two optimizer mirrors (F3)

*Claims the spec no longer makes.* That `cls._optimizer_field_map` and `cls._optimizer_hints` are
mirrored onto the class "for one minor version". That the walker reads them through
`getattr(type_cls, "_optimizer_field_map", None)`. That the mirrors are "removed in the next minor".

*What is true now.* Neither name exists anywhere in the package —
`grep -ro '_optimizer_field_map' django_strawberry_framework/ | wc -l` returns **0**. The walker
resolves both through the registered definition, per planning entry
(`django_strawberry_framework/optimizer/walker.py::_resolve_field_map`, `::_resolve_optimizer_hints`),
and the schema audit reads `registry.get_definition(type_cls).field_map` directly
(`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.check_schema`).

*What caused it, and why it was right.* `de35a622` (`refactor(types,optimizer): consolidate metadata
onto DjangoTypeDefinition`, shipped at `0.0.5`) — the removal spec-010 promised, performed on
schedule. It was right for a reason beyond tidiness: resolving the map **per planning entry** rather
than reading it off the root class is what lets a nested branch plan against the metadata of the type
it is descending into. A class-attribute mirror is inherently a per-class read, so keeping it would
have kept a shape that quietly answers the wrong question at depth.

*Alternative rejected — leave the promise in place because it is "history".* It is not history; it is
a forward-looking commitment, and a reader cannot tell from the spec that it has already been
discharged. The rule that a spec never narrates its own history cuts both ways: it may not say "these
were removed in `0.0.5`" either. It says what the store is, and nothing about what it once was.

### `### Should redo now` — the mirror that survived (F4)

*Claim the spec no longer makes.* That `cls._is_default_get_queryset` is the third legacy mirror,
"mirrored from the definition for one minor version" and removed with the other two.

*What is true now.* It survives, and it is load-bearing. `DjangoType` declares it
`_is_default_get_queryset: ClassVar[bool] = True`, and `__init_subclass__` stamps it **before** the
`meta is None` early-return
(`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls._is_default_get_queryset = not has_custom_get_queryset"`).
`has_custom_get_queryset()` prefers `__django_strawberry_definition__.has_custom_get_queryset` and
falls back to the negated sentinel.

*What caused it, and why it was right.* No later spec: **the requirement spec-010 itself states**. The
spec requires that an abstract intermediate base which overrides `get_queryset` without declaring
`Meta` still propagate the signal to its concrete subclasses. Trace that against the collection order
and the promise becomes impossible to keep: such a base returns at the `meta is None` branch, before a
`DjangoTypeDefinition` is built, before `register_with_definition`, before
`cls.__django_strawberry_definition__` is set. A definition-only carrier structurally cannot hold the
flag for the one class that most needs to carry it. Its two siblings are read only for **registered**
types, which by construction have a definition — which is exactly why they could be absorbed and this
one could not. The asymmetry is not an oversight or an unfinished migration; it is the shape of the
requirement.

*Alternative rejected — synthesize a definition for `Meta`-less abstract bases so the flag has
somewhere to live.* It removes the mirror at the cost of the opt-out: the whole point of the
`meta is None` branch is that an intermediate base is not a registered type, and manufacturing a
definition for one puts a non-type into `iter_definitions()`, which every finalizer phase loops over.
A one-line class attribute is a far smaller price than a second class of entry in the registry.

*Alternative rejected — walk the MRO at read time instead, and drop the stamp.*
`_detect_custom_get_queryset` already walks the MRO, so the read could too. It loses on the call
profile: `has_custom_get_queryset()` is consulted by the optimizer per relation traversal per plan,
where the current shape is a constant-time attribute read and the alternative is an MRO walk. Turning
an import-time computation into a planning-time one to delete an attribute is the wrong trade.

*What the spec may no longer assert.* That every legacy class attribute from the pre-definition era
has been retired, or that this one is scheduled for retirement.

### `## What does not ship`, `### Manual annotation contract for relation fields`, `### DjangoTypeDefinition`, `### Stays deferred` — the override contract (F5)

*Claims the spec no longer makes.* That manual override on scalar fields is "not pinned in this
slice" and remains an "implementation detail with the same warning as today". That the definition
carries three `consumer_*` sets.

*What is true now.* The contract is a four-corner matrix — relation x scalar, by annotation x by
assignment — with a fifth `auto` corner beside it. The definition carries all four split sets plus
their union (`consumer_annotated_relation_fields`, `consumer_annotated_scalar_fields`,
`consumer_assigned_relation_fields`, `consumer_assigned_scalar_fields`, `consumer_authored_fields`),
and `_build_annotations` short-circuits on the union at both its relation and its scalar branch. The
four corners are enumerated once, on
`django_strawberry_framework/types/base.py::_consumer_assigned_fields`.

*What caused it, and why it was right.* `spec-019-consumer_overrides_scalar-0_0_6.md` promoted the
scalar half from documented caveat to pinned contract; the `auto` declare-but-infer marker arrived
later at `0.0.9` (commit `95393168`, "Support auto-typed field annotations in DjangoType") and is
catalogued in the [glossary][glossary]. Both were right for the same reason: the relation half had a
contract and the scalar half had a warning, so the identical consumer gesture — shadowing a selected
column's name — behaved as a supported override on one branch and as an undocumented accident on the
other. The `auto` corner closes the remaining gap, where a consumer wants the field *declared* for
readability but still model-inferred, and had no way to ask for that without accidentally overriding
it.

*Alternative rejected — describe the scalar corners here, since spec-010 stores their sets.* Storing
a set and owning its semantics are different things, and this is the distinction the whole
reconciliation turns on. Spec-010 asserts exactly one thing about the scalar branch: that it feeds the
same union, so the short-circuit is one mechanism rather than two. What a scalar override is permitted
to do to the package's scalar conversion — bypassing `convert_scalar`'s validations, skipping choice-
enum registration — is spec-019's, stated once there.

### `### Manual annotation contract for relation fields` — the detection rule (F6)

*Claim the spec no longer makes.* That a class-dict value counts as a consumer override when it "is
not a Django manager/descriptor".

*What is true now.* The value must be a `StrawberryField`. Any other shadow of a selected Django field
name raises `ConfigurationError` at class creation, naming the field and both supported override forms
(`django_strawberry_framework/types/base.py::_consumer_assigned_fields #"shadows a Django"`).

*What caused it, and why it was right.* `spec-019-consumer_overrides_scalar-0_0_6.md`, which needed the
rule to hold for scalar columns too and found the exclusionary form indefensible there. The original
rule is a **negative** test — anything that is not Django's own class machinery is treated as a
deliberate override — so a typo, a stray default, a leftover constant, or a mistakenly assigned plain
function all silently suppress synthesis for that field. The failure then surfaces at schema build, in
Strawberry's vocabulary, no longer naming the field that caused it. The positive test inverts that: the
two supported gestures are recognized, and everything else fails immediately with the name of the
offending attribute. This is the "guard the answer, not one spelling of the incoherent input" shape —
the old rule enumerated what a non-override looks like, which is an open set.

*Alternative rejected — widen the accepted set to `StrawberryField` plus anything callable.* It would
have kept a bare `def items(self): ...` working as an override. It loses because an undecorated method
is exactly the near-miss the error message needs to catch: the consumer meant `@strawberry.field`, and
accepting it silently produces a field Strawberry will not resolve.

### `### DjangoTypeDefinition` and `### Stays deferred` — the reserved slots (F7)

*Claims the spec no longer makes.* That the dataclass carries six forward-reserved slots
(`filterset_class`, `orderset_class`, `aggregate_class`, `fields_class`, `search_fields`,
`interfaces`), all unused. That `DEFERRED_META_KEYS` rejects all six `Meta` keys.

*What is true now.* `DEFERRED_META_KEYS` is exactly `{aggregate_class, fields_class, search_fields}`.
Of the original six, only `fields_class` is still both a slot and a rejected key. `aggregate_class` and
`search_fields` are rejected keys with **no** slot at all. `interfaces`, `filterset_class` and
`orderset_class` are live, and the dataclass has additionally taken on `primary`, `connection`,
`cursor_field`, `relation_shapes`, `relation_connections`, `globalid_strategy`,
`effective_globalid_strategy`, and two memoization caches.

*What caused it, and why it was right.* Seven specs in sequence — `spec-015-relay_interfaces-0_0_5.md`
(`interfaces`), `spec-018-meta_primary-0_0_6.md` (`primary`), `spec-027-filters-0_0_8.md` and
`spec-028-orders-0_0_8.md` (the two sidecar classes), `spec-030-connection_field-0_0_9.md`
(`connection`), `spec-031-globalid_encoding-0_0_9.md` (the two GlobalID slots),
`spec-032-full_relay-0_0_9.md` (the two relation-shape slots), plus the `stable_cursor_field` keyset
opt-in. The interesting part is not that they landed; it is that two of the six pre-declared slots were
**deleted** on the way. Declaring a slot before its subsystem exists guesses the shape it will hold,
and `aggregate_class` / `search_fields` are the cases where the guess had no evidence behind it: their
subsystems are still unbuilt, so a `tuple[str, ...] = ()` sitting on the dataclass asserted a shape
nobody had designed. Every slot that *did* land came with its own spec and its own validated type.

*Alternative rejected — enumerate all twenty-odd live slots in the spec.* One edit away, and it reads
as thoroughness. It loses for the reason the spec-003 reconciliation recorded for the same shape: an
inventory of a dataclass is a symbol map, it is a second copy of seven other specs' contracts, and it
goes stale on every one of their next edits. The spec now carries the **partition** instead — which
slots are the foundation's, which are later, and a table naming each one's owner — which is the thing
a foundation document is uniquely placed to state and the thing no other document states at all.

### `### TypeRegistry extensions` and `### Collection phase` step 10 — two calls became one (F8)

*Claim the spec no longer makes.* That collection calls `registry.register(...)` and then
`registry.register_definition(...)`.

*What is true now.* One atomic call,
`django_strawberry_framework/registry.py::TypeRegistry.register_with_definition`, which snapshots the
pre-call state and, if `register_definition` raises, rolls back only what its own call added.

*What caused it, and why it was right.* `194f0992` (`fix(types): harden type collection and registry
guarantees`), a `0.0.4`-line hardening commit, later refined by
`spec-018-meta_primary-0_0_6.md`'s snapshot-restore correction. The two-call sequence has a window in
which a type is registered and reachable by relation resolution with no definition behind it; every
consumer of `iter_definitions()` and `get_definition()` then has to tolerate a half-registered type, or
fail somewhere far from the cause. Making the pair atomic moves the failure to the call that caused it.

*Alternative rejected — unconditional rollback of all three maps.* The obvious rollback, and it
corrupts state: since `register` is idempotent for an already-stored type, a failed
re-register-with-a-different-definition would tear down a **pre-existing**, valid registration that
this call never created. The snapshot-and-conditional-restore is what makes "either fully succeeds or
leaves the registry untouched" true in both the fresh and the idempotent case.

### `### TypeRegistry extensions` and `## Idempotency and lifecycle contract` — the second guard and the fuller reset (F9)

*Claims the spec no longer makes.* That the post-finalization guard lives only in
`__init_subclass__`. That `clear()` resets exactly `_types`, `_models`, `_enums`, `_definitions`,
`_pending` and `_finalized`.

*What is true now.* `django_strawberry_framework/registry.py::TypeRegistry._check_mutable` refuses
every mutator once the registry is finalized, with `clear()` as the single deliberate exception so
test teardown can reset a finalized registry. `clear()` additionally runs registered per-type and
per-subsystem teardowns before dropping the maps, and resets `_primaries`, `_type_teardowns` and the
GlobalID setting snapshot.

*What caused it, and why it was right.* `194f0992` for the guard; `c3767495` (`fix(types): harden
finalization lifecycle`, `0.0.13`) for the teardown pass; `spec-018-meta_primary-0_0_6.md` and
`spec-031-globalid_encoding-0_0_9.md` for the two extra maps. The guard is not redundant with
`__init_subclass__`'s: that one sees only consumers who arrive by class creation, and any other route
into the registry — a late import triggered from a request handler, a subsystem writing directly —
would otherwise corrupt a finalized snapshot with no error at all. The teardown pass exists because
`clear()`'s original contract ("registry state only; class mutation is not rolled back") turned every
framework-installed class artifact into cross-test residue; the fix is deliberately *opt-in*, so each
subsystem announces its own teardown rather than the registry guessing.

*Alternative rejected — have `clear()` also strip `__strawberry_definition__` and the attached
resolvers from finalized classes.* It would make `clear()` a true reset. It loses because those
artifacts are not identity-safe to remove — Strawberry and the consumer may both hold references, and
a partially un-decorated class is a worse state than a decorated one. The contract instead stays
honest about its limit ("resets registry state for fresh type classes; does not roll back class
mutation") and tests are told to declare fresh classes, which they do naturally.

### `### Finalization phase` — the resolution call's third argument (F10)

*Claim the spec no longer makes.* That the phase-1 rewrite calls
`resolved_relation_annotation(p.django_field, target_type)`.

*What is true now.* It passes `field_meta=` as a keyword-only third argument, read from the owning
definition's `field_map[snake_case(p.field_name)]`
(`django_strawberry_framework/types/converters.py::resolved_relation_annotation`).

*What caused it, and why it was right.* `spec-016-fieldmeta_consolidation-0_0_6.md`, which names this
function among its targets. Without the argument the helper re-derives cardinality and nullability
from the Django field on the spot, which is a second computation of something collection already
computed and stored. Two derivations of one fact are two chances to disagree, and the disagreement
would be invisible: the annotation the finalizer writes would say `list[T]` while the `FieldMeta` the
optimizer plans against says otherwise. Threading the precomputed projection makes the schema and the
plan provably agree because they read the same object.

*Alternative rejected — make `field_meta` required rather than defaulted.* Stronger on paper, and it
breaks the helper's other callers, which hold a Django field and no definition. The default preserves
the standalone path while letting the finalizer — the one caller that *has* the projection — pass it.

### `### Finalization phase` and `### Collection phase` — two steps the lifecycle omitted (F11)

*Claims the spec no longer makes.* That phase 2 attaches relation resolvers and nothing else. That
collection ends at stashing the definition.

*What is true now.* Phase 2 attaches relation resolvers **and** file/image resolvers, the latter over
the broader `consumer_authored_fields` skip set rather than the relation pass's
`consumer_assigned_relation_fields`
(`django_strawberry_framework/types/finalizer.py::finalize_django_types #"_attach_file_resolvers"`).
Collection ends with `install_is_type_of(cls)`.

*What caused it, and why it was right.* `spec-037-upload_file_image_mapping-0_0_11.md` for the file
pass, `spec-015-relay_interfaces-0_0_5.md` for `is_type_of`. Both belong exactly where they landed and
nowhere else: phase 2 is the **only** window in which a resolver may attach — after phase 1 has settled
every annotation, before the final phase's `strawberry.type(...)` freezes the class — so a second
resolver-installing subsystem has one correct home rather than a choice. The two different skip sets
are the detail worth stating, because they look like a typo and are not: an annotation-only file
override must still suppress the generated file resolver, while an annotation-only relation override
must still receive its generated relation resolver.

*Alternative rejected — describe what the file/image resolvers do.* Spec-037's, in one clause. Spec-010
states only that the window exists, that it is singular, and that both passes share it.

### `### Finalization phase` and `## Idempotency and lifecycle contract` — the scope of failure-atomicity (F12)

*Claim the spec no longer makes.* That a phase-1 failure means nothing whatever has happened yet.

*What is true now.* Phase 1 mutates no **class object**, which is the claim that matters and the claim
the contract rests on. One registry write precedes it: the per-build `RELAY_GLOBALID_STRATEGY`
snapshot, a pure read that may raise and that on success records
`registry._globalid_setting_snapshot`
(`django_strawberry_framework/types/finalizer.py::finalize_django_types #"_validated_globalid_setting"`).

*What caused it, and why it was right.* `spec-031-globalid_encoding-0_0_9.md`. Reading and validating
the setting once per build, before the loop that consumes it, is right for two reasons: an explicitly
invalid value must raise even in a schema with zero Relay types, and a retry after a partial finalize
must reuse the original snapshot rather than silently producing a mixed-strategy schema where some
types were stamped under the old value. Both require the read to happen before any type is touched.

*Alternative rejected — leave the atomicity sentence unqualified, since a settings snapshot is
"not really state".* It is state, it is observable, and `registry.clear()` resets it precisely because
it is. The precision costs one clause and buys the reader the ability to trust the sentence literally;
an approximately-true invariant is the kind a later change quietly invalidates without anyone noticing
which half was load-bearing.

### `### End-to-end schema and HTTP tests` — a path that no longer exists (F13)

*Claims the spec no longer makes.* That end-to-end schema tests live at
`examples/fakeshop/tests/test_schema.py`. That `tests/types/test_definition_order_schema.py` proves
in-process schema execution.

*What is true now.* The schema-composition tests are at
`examples/fakeshop/apps/library/tests/test_schema.py`, beside the app whose coverage they are;
`tests/types/test_definition_order_schema.py` holds one test, pinning the pending-relation sentinel's
repr.

*What caused it, and why it was right.* `31642c9c` (`tests: relocate example app tests into per-app
folders`, `0.0.7`), codifying what is now `AGENTS.md` rule 7. Per-app placement means deleting an app
loses only that app's tests and nothing else's — the property a shared `examples/fakeshop/tests/`
directory cannot have. That directory still exists, for project-level tests owned by no single app,
which is why the path looks plausible and the file is absent.

*Alternative rejected — leave the section naming the old paths, on the ground that a spec's test plan
is history.* A test plan differs from a migration record in exactly the way that matters here: a
reader consults it to find the tests, and a path that resolves to nothing is not history, it is a
broken pointer. The migration section's retired **symbol** names are correct as history because their
sentences are about what the slice changed; a test-location list is about where something is.

### `## Strawberry finalization strategy` and `## Phased implementation order` — the documentation targets (F14)

*Claims the spec no longer makes.* That `docs/FEATURES.md` holds the capability catalog entry. That
the root `README.md` carries the wrong-order example and the import-boundary note.

*What is true now.* `docs/FEATURES.md` does not exist — `40c1855f` renamed it to `docs/GLOSSARY.md`.
The root `README.md` carries the landing snippet; `docs/README.md` carries the schema-setup boundary
section with the correct and wrong-order snippets as a pair, the single-threaded window, and the
import-boundary note.

*What caused it, and why it was right.* The rename plus the onboarding-doc restructure that split a
landing page from a documentation entry point. The split is the right shape for the specific content
this spec placed: a wrong-order example is a *failure-mode* explanation, and a landing README's job is
to make the correct shape look small. Putting the failure mode on the front page makes the surface
look more delicate than it is.

*Alternative rejected — also retarget the Phase-0 spike record's `README.md` references.* Left alone
deliberately. Those sentences state what a spike concluded and where its conclusion was recorded at the
time; they are the same class as the retired-symbol citations the earlier pass ruled on above — a
present-tense survival in a shipped spec that is correct as history. Only the two sentences stating a
**current** documentation location were retargeted. The boundary is flagged for the maintainer in
`docs/builder/bld-010-r1-spec_reconciliation.md` rather than settled unilaterally.

### `### Finalization phase` — the consumer-authored arm in phase 1 (F15)

*Claim the spec no longer makes.* That the phase-1 loop's consumer-authored branch is a live
classification arm that pending records actually reach.

*What is true now.* It is defense-in-depth and unreachable under the documented call graph:
`_build_annotations` never appends a pending record for a consumer-authored name, so no such record can
arrive. The source says so in place
(`django_strawberry_framework/types/finalizer.py::finalize_django_types #"Defense-in-depth"`).

*What caused it, and why it was right.* F1's change, transitively: once collection defers
unconditionally *and* short-circuits consumer-authored names before the deferral, the two conditions
that would put such a record in the pending list cannot both hold. Keeping the arm is right because the
invariant it protects lives in a **different function** — a future collection path that does record
pending for an overridden name (a lazy or cross-module forward-reference route is the obvious
candidate) would otherwise overwrite the consumer's annotation with a generated one, silently, with no
guard between the two functions.

*Alternative rejected — delete the arm as dead code.* The strongest DRY-shaped argument available, and
it loses on the asymmetry of the two failure modes: keeping an unreachable three-line branch costs a
reader one paragraph, while deleting it converts a future collection-side change from a no-op into a
silent consumer-override clobber. What the spec owed was not the deletion but the honesty — presenting
an unreachable arm as live classification is what made the code look like it was doing work it was not.

### What this pass deliberately did not change

- **The unresolved-target error format and its two inbound citations.** `spec-009`'s
  `### Layer 3: Finalization trigger` and `### Decision 6: fail loudly` both still resolve, verified
  read-only at the moment of editing. A concurrent session was reconciling `spec-009` during this pass,
  so repointing either citation was refused on principle: a citation repointed at a file another
  session is actively rewriting produces two half-corrections instead of one whole one.
- **`spec-008`'s two citations**, for the same reason and by the same check.
- **The `## What ships` list of six.** Every one of the six is present at `HEAD`, verified
  individually. The list describes what this slice delivered, and later additions to the same phases
  are named in the phase descriptions rather than promoted into the deliverable list — that is the
  absorption line, applied to the one section where crossing it would have been least visible.
- **The seven invariants.** All seven still hold, and none was reworded.
- **The third-party line citations.** The standing note above governs; nothing in this pass touched
  them.
- **`docs/SPECS/appx/spec-010-foundation-0_0_4-terms.csv`.** The twelve glossary anchors the spec body
  names are unchanged by every edit above, and `check_spec_glossary.py` exits 0 on the reconciled spec.
  The CSV is DB-backed through `import_spec_terms` on a `DONE` card, so leaving it untouched was a
  requirement rather than a convenience.

## Coverage pass — the claim that was never true

### `### Manual annotation contract for relation fields` — the lazy override's worked example (F16)

*Claim the spec no longer makes.* That a cross-module lazy relation override is spelled
`items: Annotated[list["ItemType"], strawberry.lazy("...")]`, with the marker wrapping the collection.
The same example stood in the `Tests cover all four shapes` list as `Annotated[..., strawberry.lazy("...")]`,
whose elision hid the placement rather than stating it.

*What is true now.* The marker must annotate the **target type**, inside the collection parameter:
`list[Annotated["ItemType", strawberry.lazy("module.path")]]` for a to-many relation, and
`Annotated["ItemType", strawberry.lazy("module.path")] | None` for a nullable FK. The spec now says so
normatively, and both worked examples carry the inner spelling.

*Why the outer spelling cannot work.* Strawberry converts a lazy reference into a `LazyType` only when
the type it annotates is itself a `ForwardRef` — `arg.resolve_forward_ref(args[0]) if isinstance(args[0],
ForwardRef) else args[0]`, in `strawberry/utils/typing.py::eval_type`. With the marker on the outside,
`args[0]` is `list["ItemType"]`, a generic alias rather than a `ForwardRef`, so the marker is discarded
and the inner string degrades to an ordinary forward reference evaluated against the declaring module's
namespace. Two measurements, run against the shipped package: the outer spelling raises
`strawberry.exceptions.unresolved_field_type.UnresolvedFieldTypeError: Could not resolve the type of
'items'` at `strawberry.Schema(...)` construction when the target is not importable at module scope,
and it builds a correct schema when the same target name **is** bound in that namespace. So the outer
spelling is not a syntax error but something worse — an inert marker that appears to work in every case
where the escape hatch is unnecessary and fails in the only case it exists for.

*What caused it, and why the correction is owed.* Nothing later reshaped this contract; the example was
wrong when it was written and has stood since `0.0.4`, in a document whose own `### Spike C` outcome
already named `list[Annotated["Target", strawberry.lazy("module.path")]]` the correct shape. The spec
contradicted itself, and the half a consumer would copy was the wrong half. It survived because the
`Tests cover all four shapes` claim was false for this shape: no test anywhere exercised a lazy
relation override, so nothing in the suite could disagree with the prose. Writing that test
(`tests/types/test_definition_order.py::test_cross_module_lazy_relation_override_types_the_field_as_the_referenced_class`)
is what surfaced it — the general lesson being that a worked example in a spec is an untested claim
until some row executes it.

*Alternative rejected — document the outer spelling as a rejection path with its error.* It would put
the failure in front of a reader who had already copied the wrong line, and it loses on two counts: the
package rejects nothing here (the error is Strawberry's, raised from an ordinary unresolvable forward
reference, and pinning an upstream message buys a suite failure on the next Strawberry release for no
contract gain), and a contract section documents what a consumer must write, not an inventory of what
they must not. The one thing the outer spelling deserves is the sentence explaining why placement is
load-bearing, which is now normative text in the spec rather than a rejection note here.

### `### Manual annotation contract for relation fields` — the fourth shape's missing row (F20)

*Claim the spec could not make.* `Tests cover all four shapes` was false for a second listed shape as
well as the lazy one: the `= strawberry.field(resolver=...)` **assignment** on a relation field had no
row anywhere, leaving three of four covered once F16's lazy row landed.

*What is true now.* Each of the four listed shapes has exactly one pinning row, and the four names map
one-to-one onto the four bullets: annotation-only ->
`::test_annotation_only_relation_override_keeps_generated_resolver`; the inner-spelled lazy override ->
`::test_cross_module_lazy_relation_override_types_the_field_as_the_referenced_class` (with
`::…_wins_over_the_registered_primary_type` as its discriminator, not a second shape); the
`strawberry.field(resolver=...)` assignment ->
`::test_assigned_relation_field_resolver_kwarg_override_keeps_consumer_resolver`; the `@strawberry.field`
decorator -> `::test_assigned_relation_field_override_keeps_consumer_resolver`. **No spec text changed:
the sentence needed a landed row, not a rewrite.**

*Why the assignment form is a genuine fourth case rather than a spelling of the decorator form.* The
spec spells it as an *annotated* assignment, so the field name lands in **both**
`consumer_annotated_relation_fields` and `consumer_assigned_relation_fields`. That double membership is
the only relation-field configuration in which the narrow skip set handed to `_attach_relation_resolvers`
is populated **and** the name is inside the broader `consumer_authored_fields` union handed to
`_attach_file_resolvers` — the two-different-skip-sets shape F11 records as deliberate. Nothing in the
suite exercised that state before.

*Alternative rejected — make the row discriminate Strawberry's annotation-over-resolver-return-type
precedence.* The row's class annotation and its resolver's return annotation both name `list[ItemType]`,
so the schema is identical under either precedence and the row cannot tell which one Strawberry applied.
Discriminating it would require the two to name **different** types, which is exactly the cardinality /
type validation this spec defers ("trust the user's annotation; do not silently overwrite"). Pinning an
upstream precedence rule the package does not contract for buys a suite failure on a future Strawberry
release for no contract gain. Consequence to carry: the floor run performed for this row is **not**
evidence about that precedence, and must not later be cited as such.

*Not changed — [`docs/GLOSSARY.md`][glossary] `#definition-order-independence`.* Its bullet reads
"cross-module `Annotated[..., strawberry.lazy("module.path")]` annotations", which names the marker with
the annotated type elided. That is unspecific, not wrong, and the glossary is generated from
`examples/fakeshop/db.sqlite3` — a change there is a DB edit plus a regenerate, not a spec edit. The
placement rule belongs in the contract document, and it is now there.

## Archive pass — the links the move left behind

This spec was moved from `docs/` to `docs/SPECS/` by an earlier `docs/SPECS/NEXT.md` Step 8 sweep that
did not re-relativize the link targets inside the moved file's body. Step 8 names that class as "the
failure mode that gets missed", and the reason is structural rather than careless: the visible diff of an
archive move is a rename, so a reviewer reading the diff sees nothing wrong, while every relative target
inside the unchanged body is now wrong by one directory level. Three of the four surviving inline links
broke outright; the fourth did something worse.

### `## Cross-references` — three targets that resolve to nothing (F17)

*What was wrong.* `../GOAL.md`, `../TODAY.md`, and `TREE.md`, correct from `docs/`, resolve to nothing
from `docs/SPECS/`. Corrected to `../../GOAL.md`, `../../TODAY.md`, and `../TREE.md`, and carried as
reference-style definitions so the next relocation costs four definition lines rather than a body sweep.

### `## Cross-references` — the README the label and the path disagreed about (F18)

*What was wrong, and why no checker could see it.* The entry read
`` [`README.md`](../README.md) `` under the label "Operational entry point, install/test/build". From
`docs/SPECS/` that path **resolves** — to `docs/README.md`, not the root `README.md` its display text
names. A same-named file one level up masks depth rot completely: a link checker follows the path, finds
a file, and reports the link healthy. Only intent settles it, so the reasoning is the durable artifact
here and the fix is the cheap part.

*The judgement, and the evidence for it.* The reference intends **`docs/README.md`**. Three
independent readings agree. (a) The root `README.md`'s own documentation map labels `docs/README.md`
"install, quick start, walkthrough, status" and `CONTRIBUTING.md` "dev setup, format, test, build,
publish" — between them they are the label's "install/test/build", and neither of them is the root
README. (b) The root README is positioning: its sections are *Why this package exists*, *Why it's fast*,
*Is this for you?*, *Status*, and a `Get started ->` arrow pointing at `docs/README.md`. A file that
delegates getting started is not the operational entry point. (c) This spec's own contract already
locates its operational content there: the earliest-safe-call-point boundary, the single-threaded
lifecycle window, the module-discovery note, and the correct/wrong-order snippet pair are all stated
against `docs/README.md` (see `## Strawberry finalization strategy`), which is where F14 put them.

*What changed.* The path was already right by accident, so the **label** was the error and the label is
what moved: the entry now names `docs/README.md`, and its description was corrected to what that file
actually carries. Restating "test/build" against a file with no build section would have re-created the
same class of defect one line down.

*Alternative rejected — repoint to the root `README.md` and keep the label.* This spec does have a
doc obligation on the root README (`## Phased implementation order` step 10 assigns it the public-API
list and the landing snippet), so the alternative is not absurd. It loses because the label's head noun
is "operational entry point" and the root README explicitly is not one. The obligation is preserved
without inventing a second cross-reference row: the corrected entry names `CONTRIBUTING.md` and the root
`README.md` in its own sentence, so neither file is orphaned and a future reader cannot re-open the
question by observing that a cited file went missing from the list.

*Alternative rejected — repoint to `CONTRIBUTING.md`.* Literally the best match for "install/test/build"
taken as three words, and wrong: the display text names a README, and the entry's job is to hand a reader
the one place to start operating the package. `CONTRIBUTING.md` is now reachable from the same entry
anyway.

### The whole file — inline links became reference-style (F19)

*What changed.* Eight inline `](path)` cross-file links (two each to spec-008 and spec-009, one each to
the root README, `GOAL.md`, `TODAY.md`, and `docs/TREE.md`) became `[text][ref-id]` uses backed by
definitions in the existing bottom block, grouped by where the **target** lives rather than where this
spec lives. `AGENTS.md` rule 28 and `START.md` "Markdown link convention" are the rule; this archive
pass is the demonstration of the reason. The convention does not make link rot impossible — it makes it
**visible and cheap**, by collecting every relative path in one auditable block instead of scattering
them through 600 lines of prose where a move cannot see them.

*Deliberately left inline.* The third-party citations into pinned upstream snapshots
(`strawberry_django/...:NNN`, `graphene_django/...`, `graphene/...`) keep their line numbers and their
form; `## What we take from strawberry-graphql-django` states that convention and `## Standing notes`
above defends it as not-debt. In-page anchors (`](#...)`) and anything inside a fenced code block stay
inline per `START.md`. Finishing the job on those would have converted a working citation style into a
broken one.

*Not changed — the two spec-009 citations by heading anchor.* A concurrent session is reconciling
spec-009 while this pass runs. Converting this spec's *inline links* to that file is safe because it
does not change what they point at; repointing a citation at a file someone else is actively rewriting
produces two half-corrections instead of one fix. Both anchors were confirmed to resolve at the moment
of the edit and left otherwise untouched.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../../GLOSSARY.md

<!-- docs/SPECS/ -->
[spec-009]: ../spec-009-rich_schema_architecture-0_0_4.md
[spec-010]: ../spec-010-foundation-0_0_4.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
