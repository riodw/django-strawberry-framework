# Rationale: spec-015 — Relay interfaces and Node foundation (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-015-relay_interfaces-0_0_5.md`][spec-015]. The spec is the contract
and states only what holds at `HEAD`; everything that explains **how it got there** lives here: the
two upstream packages the slice borrowed from and what it refused to borrow, the spike that licensed
the `__bases__` mutation, the eleven risks and their preferred-answer/fallback pairs, every claim the
spec once made and may no longer make, and the later cards that changed the shipped shape without
ever touching the spec.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. Unlike the four
residual cycles before it, **this one is a genuine MOVE**. Specs 011-013 were card-snapshot stubs
whose rationale had to be reconstructed from history, and spec-014 was a design record its own
implementing commit destroyed in place, so its rationale was a restoration. Spec-015 survived intact
at 626 lines with nine numbered Decisions, a borrowing posture, a spike, a helper sketch, eleven
risks, and a twelve-item definition of done. Text marked *Moved* below was **cut** out of the spec,
not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec section or Decision**, named by its own heading and linked to its anchor. A
  section with no entry here lost nothing and was not reconciled.
- Three of the spec's own top-level sections **no longer exist** — `## Pre-implementation spike
  outcome`, `## Borrowing posture`, and `## Risks and open questions`. Their entries say so and
  anchor the Decision the moved text bears on, per the [`worker-1.md`][worker-1] rule that an entry
  naming no decision cannot be looked up.
- **Every fact below was measured at this working tree, not restated.** The tree is dirty with two
  concurrent sessions' work, so every source and test reading was taken read-only via
  `git show HEAD:<path>` into a scratch path outside the repository
  (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`). `HEAD` is
  `4c9e4e0dd66f64b6eb3e29dcf481a9bfb4ec6eae`.
- **Grep found the candidates; reading the bodies cleared them.** Two claims in this cycle's own
  build plan survived a symbol grep and failed a reading — recorded under
  this file's Decision 7 entry and its `## Test plan` entry.
- **The move and the reconciliation are one pass**, so this file carries both records: the entries
  keyed to the spec first, then `## Reconciliation record — what the spec now says, and why`.

## Provenance of this record

**Moved** — cut from the spec by this pass, and now only here:

- the whole `## Pre-implementation spike outcome` section, heading, prose, and fenced example;
- the whole `## Borrowing posture` section — both `###` sub-sections with all eight per-borrow
  "Justification:" paragraphs, and the seven-bullet "Explicitly do not borrow in `0.0.5`" list;
- the whole `## Risks and open questions` section, all eleven bullets with their preferred-answer /
  fallback pairs;
- the per-Decision "Justification:" paragraphs that argue a rejected alternative rather than
  constrain an implementation — named individually in the entries below.

**Kept in the spec deliberately, against the pull of this move.** [`worker-1.md`][worker-1]'s
carve-out for implementation-relevant rationale is load-bearing here and three sentences exercised
it. The `__func__`-identity discriminator's reason ("a `cls.__dict__` check would never see the
inherited `relay.Node` default and would skip injection forever") stays in Decision 3, because a
builder who never reads it writes the `__dict__` check. The `"pk"` → concrete-attname coercion's
reason stays in the same Decision, because without it the `__dict__` cache always misses and
Decision 7's no-lazy-load invariant silently fails. The suppression-versus-base-injection timing
split stays in Decision 5, because it is why the two halves run in different lifecycle phases. Each
is a "why" that changes **how** the thing is built, not deliberation about whether to build it.

**Deleted outright rather than moved**, per [`worker-1.md`][worker-1] rule 2, because the current
contract falsifies them: the `Status:` line's three-deleted-drafts clause and its `READY-004`
pointer; the Slice-5 `Cleanup` box instructing deletion of a file that does not exist; the
`## Internal helper surface` signature sketch (all four resolver signatures wrong); the
`## Current state` claim that the finalizer has no interface awareness; Decision 9's `is_awaitable`
/ `asgiref` detection sentence and its `sync_to_async` / `acount` promise; the three
`README.md #"For the current capability snapshot"` citations for a promise that paragraph does not
make; the `id: relay.NodeID[str] = strawberry.field(...)` spelling, which is now refused; and
Decision 1's claim that a `types/base.py` block comment names the interface-application seam. Each deletion is recorded below as a claim the spec may no longer make; none is restored
anywhere as live text.

**Two fenced code blocks left the spec.** The spike's five-line `__bases__` example (quoted below)
and the helper-surface signature sketch (quoted below). The spec keeps six fenced blocks — the four
consumer examples in `## User-facing API`, Decision 3's injection loop, and the restated
`## Internal helper surface` signature list, which is a **new** fence written in place of the
deleted sketch. Seven fences before, six after.

**Glossary anchors: eighteen of nineteen were untouched; one changed carrier and survives.**
`#apply_cascade_permissions` was carried only by the `## Risks and open questions` bullet on
sentinel/cascade behavior, which this pass moved here. The reconciled `## Non-goals` bullet on
cascade permissions now carries the identical `[apply_cascade_permissions][glossary-…]` link text,
so the term string still matches its `spec-015-…-terms.csv` row, and
`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-015-relay_interfaces-0_0_5.md`
exits 0 after the rewrite. No other moved paragraph carried a glossary link.

**Spec size:** 73,479 bytes before this pass and 66,594 after, both measured with `wc -c`; 626 lines
before and 595 after. The per-section accounting was recorded in this cycle's R1 artifact, which was
retired at closeout; it is readable at
`git show 01b011ea:docs/builder/bld-015-r1-rationale_and_spec_reconciliation.md`.

## What the card actually did — recovered from history

Every commit below was confirmed with `git log -1 --format='%ad %s' --date=short <sha>`.

| Commit | Date | What it did for this card |
|---|---|---|
| `b756e515` | 2026-05-08 | "0.0.5 plan spec-relay_interfaces start" — authored `docs/spec-relay_interfaces.md`. |
| `cc2f0981`, `904fcfa0`, `3982978d`, `9c677b95`, `32dea521` | 2026-05-08..12 | Spec authoring: slice checklist, a content-versioned `Node` draft later dropped, kanban tracking, `0.0.5` prep. |
| `e6907fa8` | 2026-05-13 | **The card's implementation.** `types/relay.py` (+305), Phase 2.5 in `types/finalizer.py`, `_build_annotations` suppression, the four `resolve_*` defaults, and every test the Test plan names — the three later relocated included. |
| `e836d72e` | 2026-05-13 | Slice 5: `ALLOWED_META_KEYS` promotion, docs, version bump. |
| `a7c8f8ff` / `df13b644` / `40c1855f` / `3ed0bb84` | 2026-05..06 | Spec relocation to `docs/SPECS/`, numbering to `spec-011-relay_interfaces-0_0_5.md`, `path:NN` → symbol-qualified conversion. |
| `81e4704d` | 2026-06-01 | "docs: archive prior specs to `docs/SPECS/` and renumber per Step 8 pass" — renumbered `spec-011-relay_interfaces` → **`spec-015-relay_interfaces`**. The in-source citations were not swept. |

Three later commits changed what spec-015 owns without touching the spec:

| Commit | Date | What it changed |
|---|---|---|
| `4f4db722` | 2026-06-02 | "tests: relocate optimizer behavioral coverage from package tests to live /graphql/ HTTP" — retired `test_relay_target_relation_planning_unchanged`. |
| `be9130e3` | 2026-06-13 | "Migrate package tests to the live /graphql/ fakeshop suite" — retired the two `test_definition_order_schema.py` schema-construction extensions in favour of live twins. |
| `6912ca92` | 2026-06-13 | "DRY pass (docs/feedback.md round)" — replaced the resolvers' hand-rolled `_default_manager.all()` + `cls.get_queryset(...)` with the shared `initial_queryset` / `apply_type_visibility_*` boundary. |

### Nothing was skipped in the code

The first of the maintainer's three obligations is that everything spec-015 promised is present at
`HEAD`, and that anything promised and never delivered is a defect. Fifteen claims were checked
against `HEAD`; **every one holds, and no code defect was found.** The two that needed more than a
grep:

- **Thirty of the thirty-three named tests exist under their own names**, each confirmed by
  `grep -c "def <name>("` returning 1 in [`tests/types/test_relay_interfaces.py`][test-relay-interfaces]
  or [`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection]. The other three were
  **built and later relocated, never skipped** — proven by diff, not inferred: `git show e6907fa8`
  adds `+def test_relay_target_relation_planning_unchanged`,
  `+def test_relay_declared_type_emits_node_interface_and_global_id`, and
  `+def test_mixed_relay_and_non_relay_types_introspect_cleanly`; `git show 4f4db722` removes the
  first and `git show be9130e3` removes the other two, each in a commit whose message states the
  live-first relocation as its purpose.
- **The two live twins assert what their names claim.** Reading them rather than grepping them:
  [`test_library_api.py`][test-library-api]`::test_relay_genre_type_emits_node_interface_and_global_id_live`
  asserts `"Node" in interface_names` and that `id` introspects as `NON_NULL(ID)`; `::…_no_interface_bleed_live`
  asserts `Node` is on `GenreType`, absent from `ShelfType`, and that `ShelfType.id` is **not** `ID`.
  Both docstrings name themselves "the live twin of" the retired package test.

## Entries keyed to the spec

### The `Status:` line — a merge record for three files that no longer exist

Spec: the header block.

*Deleted, not moved.* "This document is the merged, canonical result of three superseded drafts
(`-1.md`, `-2.md`, and `-3.md`), all of which have been deleted; this file is the single source of
truth for the `READY-004` slice."

*Why deleted rather than moved.* Two of its three facts are process provenance the spec is not
entitled to assert — which drafts were merged, and that they were deleted — and the third names a
board id that no longer exists. `ls docs/spec-relay_interfaces*` matches nothing, so the merge is
unverifiable from the tree in either direction. The durable fact, that this file is the single
source of truth for the card, survives in the reconciled line.

*Claims the spec no longer makes.* That three superseded drafts were merged into it; that any draft
was deleted; that the slice is `READY-004`.

*The contradiction that made this a finding.* The same spec's Slice-5 `Cleanup` box read
"Delete `docs/spec-relay_interfaces-3.md` (drafts `-1.md` and `-2.md` were already removed in an
earlier cleanup)" — an unticked instruction to delete a file the `Status:` line four hundred lines
above already declared deleted. Both cannot be current. The box is deleted with the clause.

### `## Current state` — a section that narrated its own correction

Spec: [Current state][spec-015-current-state].

*Nothing moved; three bullets were rewritten and one parenthetical was deleted.*

*Deleted, not moved.* "keeps `interfaces` in `DEFERRED_META_KEYS` (historically — by `0.0.5` the key
is already in `ALLOWED_META_KEYS` per the historical comment block in the same file)."

*This is the shape [`BUILD.md`][build] forbids by name, and it is instructive that it arose from a
correction rather than from neglect.* A prior reader noticed the first clause was false and patched
a parenthetical **over** it instead of replacing it, leaving one sentence that asserts a thing and
then denies it. The reader cannot tell which half is current without going to the source. At `HEAD`
`ALLOWED_META_KEYS` contains `"interfaces"` and `DEFERRED_META_KEYS` is exactly
`{"aggregate_class", "fields_class", "search_fields"}` — read from
[`types/base.py`][types-base] — so the reconciled bullet states that and nothing about how it got
there.

*Two further bullets were false at `HEAD` and are rewritten.* The finalizer bullet said the three
loops run "with no interface awareness today"; Phase 2.5 has existed since `e6907fa8` and at `HEAD`
runs `apply_interfaces` → `_check_composite_pk_for_relay_node` → `install_relay_node_resolvers` →
`install_globalid_typename_resolver` before the `strawberry.type(...)` loop. The optimizer bullet
said "the four Relay resolvers can opt into optimizer cooperation the same way root resolvers do
today"; they never did, and the same spec's Decision 3 says the consultation is deferred — see
this file's Decision 9 entry for the half of that contradiction that shipped
as false.

*Claims the spec no longer makes.* That `interfaces` is a deferred Meta key; that the finalizer has
no interface awareness; that the Relay resolvers consult the optimizer extension.

### `## Pre-implementation spike outcome` — the empirical licence for Decision 1

Bears on [Decision 1][spec-015-decision-1]; the section this entry keys to no longer exists.

*Moved verbatim, the whole section.* "A minimal local spike against the installed Strawberry version
showed that mutating bases before `strawberry.type(...)` works:

```python
class Item(Base):
    name: str


Item.__bases__ = (Base, relay.Node)
strawberry.type(Item)
```

The resulting type is a subclass of `relay.Node`, and Strawberry records the `Node` interface on the
object definition. This is the empirical anchor for Decision 1's `cls.__bases__` mutation step and
supports the existing design comment in `django_strawberry_framework/types/base.py
#"DEFERRED_META_KEYS: frozenset[str]"`. Real `DjangoType` classes carry synthesized annotations,
pending relations, generated resolvers, optimizer metadata, inherited `get_queryset`, and
consumer-authored relation overrides, so Decision 5 still pins the order of operations explicitly and
the test plan covers the full surface."

*Why it moved rather than stayed.* It is the evidence that made Decision 1 safe to write, not a
constraint on how Decision 1 is implemented: the mechanism it validates is stated normatively in
Decision 1 itself, and the ordering it defers to is stated normatively in Decision 5. A builder who
never reads the spike still writes the same code. It is exactly the "derivation narrative" the move
is for — and it is the single most useful thing in this file for a reviewer asking *why is mutating
`__bases__` acceptable at all*, which is why it is preserved rather than deleted.

*Its own claim has held.* The spike's prediction survived contact: at `HEAD`
[`types/relay.py::apply_interfaces`][types-relay] performs precisely
`type_cls.__bases__ = (*type_cls.__bases__, *additions)`, and the only elaboration the shipped code
adds is the `TypeError` → `ConfigurationError` wrap the risks section asked for.

### `## Borrowing posture` — nine justified borrows and seven refusals

Bears on [Decision 3][spec-015-decision-3] and [Decision 6][spec-015-decision-6]; the section this
entry keys to no longer exists.

*Moved, the whole section.* Both `###` sub-sections and the do-not-borrow list. Reproduced here in
substance, with each borrow's own justification preserved:

**From `strawberry-django` — borrowed heavily** (local source path
`/Users/riordenweber/projects/strawberry-django-main/strawberry_django`, referenced from
[`docs/TREE.md`][tree]):

- **Resolver injection pattern** — `strawberry_django/type.py::_process_type
  #"Default querying methods for relay"`. The `if issubclass(cls, relay.Node):` loop iterates the
  four names and replaces the attribute only if
  `existing_resolver is None or existing_resolver.__func__ is getattr(relay.Node, attr).__func__`.
  *Justification:* this slice does not invent a new override-detection scheme; it reuses one already
  hardened against Strawberry version churn.
- **`resolve_id` shape** — `strawberry_django/relay/utils.py::resolve_model_id`. Read
  `root.__dict__[id_attr]` first, fall back to `getattr`, coerce to `str`. *Justification:* matches
  the `_will_lazy_load_single` / `_will_lazy_load_many` philosophy in `types/resolvers.py` and the
  rest of the optimizer-cooperation story.
- **`resolve_id_attr` shape** — `strawberry_django/relay/utils.py::resolve_model_id_attr`. One
  try/except around Strawberry's own scan with a `"pk"` fallback. *Justification:* zero extra
  surface, exact alignment with Strawberry's documented `NodeID` mechanism, and it lets a consumer
  write `id: relay.NodeID[str]` without the framework adding a `Meta` key.
- **`resolve_node` / `resolve_nodes` queryset shape** — `strawberry_django/relay/utils.py::resolve_model_nodes`
  and `::resolve_model_node`. *Justification:* every step has a direct counterpart already shipped
  (`cls.get_queryset(...)` for their `run_type_get_queryset`, our `DjangoOptimizerExtension` for
  theirs); the borrow is structural, not implementation-level.
- **`MAP_AUTO_ID_AS_GLOBAL_ID` behavior** — borrowed as *behavior*, tied to the per-type
  `Meta.interfaces` declaration instead of a global setting. *Justification:* a global setting fights
  the loud-rejection-of-unshipped-behavior posture documented in [`docs/GLOSSARY.md`][glossary];
  per-type opt-in keeps the contract local to the class declaration.
- **`is_type_of` virtual subclass** — `strawberry_django/type.py::_process_type #"is_type_of"`.
  *Justification:* our root and relation resolvers return Django model instances, not
  Strawberry-typed wrappers, and Strawberry's interface dispatch uses `is_type_of` to identify the
  concrete type; strawberry-django chose this borrow for the same reason and we have no
  architectural daylight from them on the point.

**From `django-graphene-filters` / `graphene-django` — borrowed only the user-facing shape and the
validation philosophy:**

- **`class Meta: interfaces = (Node,)`** — from the cookbook recipes schema. *Justification:*
  [`GOAL.md`][goal] already commits to this shape, and the cookbook is what makes it concrete for
  the graphene-django users this package wants to migrate.
- **"Warn loud when Relay-shaped behavior is configured without `Node`"** — `django_graphene_filters/object_type.py
  #"sentinel"`. *Justification for NOT shipping the warning in `0.0.5`:* no consumer code path in
  `0.0.5` required Relay (no connection field, no FK redaction), so the warning would have warned
  about behavior that did not yet exist.

**Explicitly refused in `0.0.5`, and why each lost:** graphene-django's `__init_subclass_with_meta__`
plumbing and `_meta` options bag; its redacted-sentinel system and cascade FK resolution; its
connection-field auto-upgrade in `convert_django_field`; strawberry-django's full `_process_type`
post-pass that mutates `type_def.fields` (our finalizer already handles relation finalization through
`_attach_relation_resolvers`, so a second field-rewriting pass buys nothing); strawberry-django's
`StrawberryDjangoField` custom field class (a much larger architectural commitment, tracked
separately); decorator-style `@strawberry_django.type(Model)` (the entire reason this package
exists); and **wrapping the model primary key directly in `relay.NodeID[py_type]` inside
`convert_scalar`** — an early draft's proposal, rejected because Strawberry's `Node` interface
already provides `id: GlobalID!` and resolves the underlying attribute via `resolve_id_attr()`, so
suppressing the synthesized scalar `id` and letting the interface-supplied field win is the simpler
borrow.

*Why the whole section moved.* Eight "Justification:" paragraphs and a seven-item refusal list are the
definition of a deliberative layer: they argue *which* implementation to choose, and every choice
they reached is stated normatively in the Decisions that survive. The two that a builder must not
lose — the `__func__` discriminator's reason and the `__dict__`-cache-first ordering — are already
restated in Decision 3 and Decision 7 respectively, so nothing implementation-relevant left the spec
with them.

*The one refusal that later reversed itself, recorded so nobody re-litigates it as a defect.* The
`is_type_of` borrow shipped exactly as described, and then grew: at `HEAD`
[`types/relay.py::install_is_type_of`][types-relay] consults a `_dsf_node_type_hint` stamp set by the
root refetch fields **before** the isinstance fallback, because a model with two registered Relay
types made every candidate's `is_type_of` answer `True` for the same bare instance. That is
`DONE-032-0.0.9`'s work, not this card's, and it does not falsify anything spec-015 says.

### Decision 1: where interfaces are applied

Spec: [Decision 1][spec-015-decision-1].

*Moved: the three-bullet "Justification:" block.* "The only alternative — forcing consumers to write
`class ItemType(DjangoType, relay.Node):` — contradicts the `class Meta`-driven posture in `GOAL.md`
and the public-surface promise in `README.md`." Plus: `cls.__bases__` mutation is the same mechanism
graphene-django uses internally, well-trodden Python with one real constraint; and running the step
between Phase 2 and Phase 3 means relation-resolver attachment runs against the still-pre-decoration
class, which is what the existing Phase 2 already requires.

*The rejected alternative, stated once so it is not re-opened.* Requiring explicit
`class Foo(DjangoType, relay.Node)` inheritance was weighed and lost on posture grounds — and note
that the shipped code **accepts it anyway** as a second entry path: `implements_relay_node(type_cls)`
gates the Relay work off the resolved MRO, so a consumer who writes the base directly gets the same
composite-pk gate and the same four defaults. What was rejected was making it the *only* path.

*Claim the spec no longer makes.* That `README.md #"For the current capability snapshot"` carries a
public-surface promise — see this file's entry on the `README.md` citations.

### Decision 2: id field handling

Spec: [Decision 2][spec-015-decision-2].

*Nothing moved; the section was rewritten twice over, on two independent axes.*

**Axis 1 — the trigger is wider than "`relay.Node` is among `Meta.interfaces`".** At `HEAD` the
predicate is [`types/base.py::_is_relay_shaped`][types-base]:
`any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)`. So suppression
also fires for direct inheritance (`class Foo(DjangoType, relay.Node)`) and for any
`@strawberry.interface` that itself subclasses `relay.Node` — the canonical way to extend
Relay-Node behavior, as the shipped comment says. The narrower tuple-membership reading was never
what shipped in full generality, and [`CHANGELOG.md`][changelog]'s `0.0.5` entry already said so
("including consumer subclasses of `relay.Node`"); only the spec lagged.

**Axis 2 — what is dropped is the primary key's field NAME, not the literal `"id"`.** At `HEAD`
`_build_annotations` computes `pk_name = source_model._meta.pk.name` and skips the field whose
`field.name` matches it. The shipped comment explains why the *name* and not the *attname*: for a
relation primary key (`OneToOneField(primary_key=True)`) they differ — `name="user"` versus
`attname="user_id"` — and the loop compares against `field.name`. A spec that says "drop the `id`
key" describes a model with an auto pk and silently mis-describes every renamed or relation pk.

**The escape hatch the spec did not mention.** Decision 2 said the composite-pk case raises,
unconditionally. At `HEAD` [`types/relay.py::_check_composite_pk_for_relay_node`][types-relay]
**honors the remediation its own error message proposes**: it asks
`relay.Node.resolve_id_attr.__func__(type_cls)` directly, and a type carrying an explicit
`id: relay.NodeID[...]` annotation passes; only a `NodeIDAnnotationError` — no annotation at all —
raises. Two shipped rows pin both halves:
[`test_relay_interfaces.py`][test-relay-interfaces]`::test_relay_node_with_composite_pk_raises` and
`::test_composite_pk_with_explicit_node_id_annotation_is_accepted`.

*Why the gate asks Strawberry directly rather than calling `type_cls.resolve_id_attr()`, kept in the
spec as implementation-relevant.* A relay-shaped child of a relay-shaped parent inherits the parent's
**installed framework default**, which swallows `NodeIDAnnotationError` into the `"pk"` fallback — so
the obvious spelling lets a composite-pk child slip the gate. `::test_relay_chain_composite_pk_child_still_gated`
pins it.

*Claims the spec no longer makes.* That suppression is keyed to `relay.Node` being a member of the
`Meta.interfaces` tuple; that the suppressed annotation key is the literal `"id"`; that a composite
primary key combined with `relay.Node` raises unconditionally.

### Decision 3: Relay resolver injection

Spec: [Decision 3][spec-015-decision-3]. This Decision drew four of the twelve findings and is the
largest reconciliation in the pass.

*Moved: two "Justification:" paragraphs.* That the four defaults are direct ports of
strawberry-django's `relay/utils.py` shapes (the ports themselves stay, cited at the implementation
site), and that strawberry-django is not imported at runtime because a runtime dependency on it
would re-introduce the decorator-first plumbing the package exists to avoid.

*Kept, deliberately.* The `__func__`-identity paragraph and the `"pk"` → `attname` coercion
paragraph. Both are named in `## Provenance of this record` above and both change how the code is
written.

**The `super(cls, cls).resolve_id_attr()` sketch is deleted, not moved — it is a trap.** Decision 3
sketched `_resolve_id_attr_default(cls)` as
`try: return super(cls, cls).resolve_id_attr() except NodeIDAnnotationError: return "pk"`, a faithful
port of upstream. At `HEAD` the shipped docstring rejects that exact spelling by name: with `cls`
bound at runtime, a relay-shaped `DjangoType` subclassing another relay-shaped `DjangoType` inherits
the parent's installed copy of the default, and the MRO walk from the child lands back on that copy
re-bound to the child — **infinite recursion**. The shipped default instead reads a Phase-2.5 stamp
(`_dsf_relay_id_attr`, written by `_stamp_relay_id_attr`) from the class's own `__dict__`, falling
back to a direct `relay.Node.resolve_id_attr.__func__(cls)` call for unstamped callers. Leaving the
sketch in the spec would have been a standing invitation to reintroduce the recursion, which is
precisely rule 2's case for deletion over relocation.

*The stamp bought a second thing worth recording.* Upstream caches only on success, so the common
no-`NodeID` `"pk"` fallback re-ran the full MRO `eval_type` annotation scan on **every**
`resolve_id` call — once per row of every result set. The stamp turns that into one dict read. It
also seeds `_id_attr = None` into the class's own `__dict__` to blind Strawberry's
*inherited*-cache read, which otherwise let whichever class in a chain resolved first decide the
child's id attribute.

**The signatures are as-built divergence, not later churn.** The spec pinned
`_resolve_id_default(cls, root, info)`, `_resolve_node_default(cls, info, node_id, required=False)`,
and `_resolve_nodes_default(cls, info, node_ids=None, required=False)`. `e6907fa8` shipped
`(cls, root, *, info)`, `(cls, node_id, *, info, required=False)`, and
`(cls, *, info, node_ids=None, required=False)`. The shipped docstring records the cause: Strawberry's
Relay machinery calls `cls.resolve_node(node_id, info=info, required=...)`, so a positional `info`
slot produced `TypeError: got multiple values for argument 'info'`.
`::test_resolve_node_accepts_strawberry_positional_call_shape` pins the corrected shape and names the
failure it replaced. The spec was never updated, so for fifteen months it pinned signatures no
shipped resolver had.

**The queryset body sketch predates the sealed-visibility boundary.** Decision 3's body was
`_default_manager.all()` → `cls.get_queryset(qs, info)` → `.filter(...)`. At `HEAD` both halves route
through the shared boundary — [`utils/querysets.py`][utils-querysets]'s `initial_queryset(cls)` and
`apply_type_visibility_sync` / `apply_type_visibility_async` — landed by `6912ca92`'s DRY pass and
then hardened by the spec-045 sealed-execution-queryset work, which treats a `get_queryset` return as
untrusted query state rather than a trusted executable object. The Relay resolvers are consumers of
that boundary, not owners of it, so the spec now names the seam and points at its contract instead of
re-sketching a body that would drift again.

*Claims the spec no longer makes.* That `_resolve_id_attr_default` delegates through
`super(cls, cls)`; that any of the four defaults has the signature it originally listed; that the
node resolvers assemble their queryset from `_default_manager.all()` and a direct `cls.get_queryset`
call.

### Decision 4: validation

Spec: [Decision 4][spec-015-decision-4].

*Moved: two "Justification:" paragraphs.* That writing the interface check as
`hasattr(entry, "__strawberry_definition__") and entry.__strawberry_definition__.is_interface` is
robust against future Strawberry changes to `relay.Node` and forces every accepted entry to be a real
Strawberry interface; and that duplicates are rejected rather than tolerated because the
`__bases__` injection step no-ops idempotently anyway, so tolerating them would only let typos hide.

*Nothing here was falsified — the validator grew.* All seven original rules are present at `HEAD` in
[`types/base.py::_validate_interfaces`][types-base], and `DONE-032-0.0.9` added an eighth: a named
rejection for six `strawberry.relay` non-interface helpers (`GlobalID`, `NodeID`, `Connection`,
`ListConnection`, `Edge`, `PageInfo`), matched **by identity** before the generic non-class branch,
because `relay.NodeID` is a `typing.Annotated` alias that would otherwise die in the generic
rejection without ever being named. The spec now records the eighth rule; the reason for the identity
match and the ordering stays in the source, where the ordering constraint lives.

### Decision 5: lifecycle and idempotency

Spec: [Decision 5][spec-015-decision-5].

*Moved: the no-new-state "Justification:".* That any new tracking state would be redundant with
`cls.__bases__` and would have to be re-validated for clear/redefine cycles, increasing the surface
the slice has to test.

*Kept, deliberately: the suppression-timing split.* Why `id` suppression happens at collection time
while base injection waits for finalization — annotation synthesis is where `cls.__annotations__` is
written, and Phase 1 relation finalization still mutates it, so a partially-finalized class must not
also be a partially-interface-injected one. That is an ordering constraint on the implementation and
stays.

*The phase order held exactly, and then acquired two more steps.* At `HEAD`
[`types/finalizer.py::finalize_django_types`][types-finalizer] runs, inside the Phase-2.5 loop,
`apply_interfaces` → `_check_composite_pk_for_relay_node` → `install_relay_node_resolvers` →
`install_globalid_typename_resolver` (spec-031's), plus a `Meta.cursor_field` validation, all before
the `strawberry.type(...)` loop. The two additions are later cards' and are named in the reconciled
Decision so a reader is not surprised by them; the spec-015 ordering is unchanged.

*The idempotency contract survives verbatim.* [`tests/test_registry.py`][test-registry]`::test_registry_clear_allows_fresh_relay_declared_type_to_finalize`
asserts `relay.Node in FreshCategoryNode.__mro__` after `clear()` plus redefinition. The
[`docs/GLOSSARY.md`][glossary] sentence the Decision quotes has since been reworded upstream of the
spec; the reconciled quotation matches the glossary's current wording rather than the 2026-05 one.

### Decision 6: compatibility with the override contract

Spec: [Decision 6][spec-015-decision-6].

*Moved: three "Justification:" paragraphs.* That the `__func__` precedence rule matches
strawberry-django's semantics so migration does not surprise consumers; that the validation rule from
Decision 4 makes the empty/absent case a true no-op including for id suppression; and that
unconditional `is_type_of` injection costs one method per class while removing a class of subtle
interface-dispatch bugs that would otherwise surface only once `Meta.interfaces` is added later.

*Everything normative here shipped and still holds.* `install_is_type_of` is invoked from
`DjangoType.__init_subclass__` for every subclass, discriminated on `cls.__dict__` membership so a
consumer-declared `is_type_of` survives; `::test_is_type_of_injected_for_all_djangotypes` pins both
halves.

### Decision 7: optimizer and projection invariants

Spec: [Decision 7][spec-015-decision-7].

*Moved: the FK-id-elision and connector-column "Justification:" clauses* — that `GlobalID` handling
lives entirely in the Relay resolvers so the walker continues to see the Django primary-key column it
always saw, and that the field map is the optimizer's source of truth because suppression happens
later in the data flow.

*Kept, deliberately: the no-avoidable-lazy-loads reasoning.* The `__dict__`-cache-then-`getattr`
order and its dependence on the optimizer keeping the pk in `only()` is the reason the resolver is
written the way it is, and a builder who loses it writes the `getattr` first.

**The fifth invariant is where grep cleared a claim that reading falsified.** Decision 7 promised
that `select_related` / `prefetch_related` planning for relations whose target is a Relay-declared
`DjangoType` "continues to work unchanged", and this cycle's build plan recorded, as verified
evidence, that the live products suite "pins forward-FK `select_related`". It does not. At `HEAD`
[`test_products_api.py`][test-products-api]`::test_products_optimizer_selects_nested_forward_fk_depth_2_over_http`
keeps its name and asserts the opposite of what the name suggests: its docstring reads "Before
spec-034 this query planned a single `select_related("item__category")` JOIN. With the cascade hooks
active, `ItemType` and `CategoryType` both define a custom `get_queryset`, so the optimizer downgrades
each forward FK in the `item -> category` chain to a windowed `Prefetch`", and the row now pins a
deterministic three-query Prefetch chain with **no** inter-products JOIN. This is the exact failure
mode two prior residual cycles hit — a test that kept its name while its assertion was inverted — and
it is recorded here rather than quietly corrected because the build plan is a committed record.

*What actually holds, and is what the reconciled Decision now says.* The Relay declaration does not
perturb relation planning: the optimizer reads target metadata from `DjangoTypeDefinition`, not from
`__strawberry_definition__`, so suppressing the synthesized scalar `id` is invisible to it. Planning
for a Relay-declared target is decided by the same rules as any other target — the shipped
`get_queryset` → `Prefetch` downgrade included, which is why the forward chain is a Prefetch chain
today. Both shapes are pinned live across the four Relay-declared products types
([`apps/products/schema.py`][products-schema] carries four `interfaces = (relay.Node,)` declarations):
the forward chain by the test above and the reverse-FK prefetch chain by
`::test_products_optimizer_prefetches_nested_reverse_fk_depth_2_over_http`.

*The one thing no longer pinned by any row, recorded not fixed.* The retired
`test_relay_target_relation_planning_unchanged` was an **A/B** row — a Relay-declared `CategoryNode`
as the FK target of a non-Relay `ItemType` root, asserting `"category" in plan.select_related`
(recovered with `git show 4f4db722^:tests/optimizer/test_relay_id_projection.py`). Its live
replacements assert planning **across** Relay targets but not planning **unchanged relative to a
non-Relay target**, because every products type now carries a `get_queryset` and therefore takes the
downgrade path. Nothing regressed and nothing was skipped — the coverage was deliberately relocated
under the repository's live-first policy — but the comparative assertion is gone, and this cycle
catalogs that as deferred work rather than writing a test it is not authorized to write.

### Decision 8: registry implications and one-type-per-model

Spec: [Decision 8][spec-015-decision-8].

*Moved: three "Justification:" clauses.* That `_resolve_node_default` resolves its model
unambiguously without `Meta.primary`; that deferring the multiple-types-per-model node-ownership
question keeps `0.0.5` tight; and the pointer to the future slice that must decide it.

*The deferral it names has since landed, and the answer it deferred was given.* `Meta.primary`
shipped at `0.0.6` ([`docs/GLOSSARY.md`][glossary] `## Meta.primary`, "shipped (`0.0.6`)"), and the
question "which of several types per model owns Relay node lookup" was answered by `0.0.9`'s GlobalID
work: a model-label payload resolves through `registry.get(model)`, which returns the primary. The
reconciled Decision states the `0.0.5` contract and names the successor contract rather than pointing
at a board id that no longer exists.

### Decision 9: async resolver support

Spec: [Decision 9][spec-015-decision-9].

*Deleted, not moved: the detection mechanism and two API promises.* "detect the resolver context
(Strawberry's `info` carries an `is_awaitable` signal; `asgiref.sync.iscoroutinefunction` is the
fallback), and route through Django's native async queryset API (`aget`, `afirst`, `aiter`, `acount`)
when async, falling back to `sync_to_async(qs.first)` / `sync_to_async(qs.get)` for operations that do
not yet have native async equivalents." And the closing risk note: "If a needed async ORM API is
missing in the supported Django range, fall back to `sync_to_async` wrapping the equivalent sync
call."

*Why deleted.* Every mechanism named is absent at `HEAD`. Detection is
`strawberry.utils.inspect.in_async_context()`; materialization is Django's native `aget` / `afirst`
and an `async for` comprehension; `acount` is never called and `sync_to_async` appears nowhere in
[`types/relay.py`][types-relay] (`grep` for `sync_to_async|acount|aiter` in the `HEAD` blob returns
nothing). A fallback that was never needed and an API list that does not match the code are not
history worth preserving as prose; they are three ways for the next reader to be wrong.

**The false half of the spec's own self-contradiction.** Decision 9 asserted that "the optimizer's
existing async resolver support carries through unchanged because the new resolvers call
`ext.optimize(qs, info=info)` with the same signature the existing root-gated optimizer uses" — while
Decision 3, in the same document, said the optimizer-extension consultation is deferred to a
follow-up slice. Decision 3 is the one that shipped: `grep -n "optimize"` over the `HEAD` blob of
`types/relay.py` matches only the word "optimizer" inside a docstring. The reconciled Decision 9
states what carries the async contract instead, and [`docs/GLOSSARY.md`][glossary]'s Relay entry has
said the same thing for some time ("Optimizer-extension cooperation on the per-node `resolve_node`
resolver is deferred to a follow-up slice").

**A contract shipped that the spec never mentioned.** A sync resolver context meeting an async
`get_queryset` raises `SyncMisuseError` — a typed marker multiple-inheriting `ConfigurationError`
and `RuntimeError` — rather than failing with `AttributeError: 'coroutine' object has no attribute
'filter'`. It lives in [`utils/querysets.py`][utils-querysets] (re-exported from `types/relay.py` for
compatibility), is raised by the shared visibility boundary for every sync surface rather than only
the Relay ones, and is pinned by a row in [`test_relay_interfaces.py`][test-relay-interfaces]
asserting the class relationship rather than a message substring. It belongs in Decision 9 because it
is the answer to "what happens at the sync/async seam this Decision opened", and the reconciled
Decision states it.

*Claims the spec no longer makes.* That async detection reads an `is_awaitable` signal off `info` or
falls back to `asgiref.sync.iscoroutinefunction`; that the resolvers call `aiter` or `acount`; that
any path wraps a sync call in `sync_to_async`; that the resolvers call `ext.optimize(...)`.

### `## Internal helper surface` — a sketch every shipped signature contradicts

Spec: [Internal helper surface][spec-015-internal-helper-surface].

*Deleted, not moved: the whole fenced signature sketch.* It declared
`_resolve_id_attr_default(cls) -> str`, `_resolve_id_default(cls, root, info) -> str`,
`_resolve_node_default(cls, info, node_id, required=False)`, and
`_resolve_nodes_default(cls, info, node_ids=None, required=False)`, plus `apply_interfaces`,
`implements_relay_node`, `install_relay_node_resolvers`, and `install_is_type_of` with one-line
docstrings.

*Why deleted and replaced rather than moved.* Four of the eight signatures are wrong in a way that
matters — the keyword-only `info` is the whole content of the `TypeError` fix recorded under
Decision 3 — and the other four are right. Moving a mixed block here would hide four correct
anchors in an appendix while leaving the spec with no helper surface at all; deleting the wrong four
and restating the shipped eight gives the spec a section that is checkable against
[`types/relay.py`][types-relay] in one pass. The section's own hedge ("The signatures below are
implementation anchors and may evolve during review") is what let the divergence sit unfixed, and it
goes with the sketch.

*The stale lower bound.* The section closed by pinning Strawberry's expectations to "the pinned
`strawberry-graphql>=0.262.0` lower bound", and `## Risks and open questions` repeated the figure. At
`HEAD` [`pyproject.toml`][pyproject] reads `strawberry-graphql>=0.316.0`, with an in-file comment
explaining the floor as spec-044 Decision 6's per-operation extension-isolation requirement — a
reason unrelated to Relay. The Django floor is `Django>=5.2.16`. Both figures are restated once, in
the reconciled section, rather than twice.

*Claims the spec no longer makes.* That any of the four `_resolve_*_default` helpers takes `info`
positionally; that the Strawberry lower bound is `0.262.0`.

### `## Risks and open questions` — eleven preferred answers, all now settled

Bears on [Decision 1][spec-015-decision-1], [Decision 2][spec-015-decision-2],
[Decision 3][spec-015-decision-3], [Decision 6][spec-015-decision-6], and
[Decision 9][spec-015-decision-9]; the section this entry keys to no longer exists.

*Moved, all eleven bullets.* The section's preamble promised that each names "a preferred answer for
`0.0.5` and a fallback if implementation reveals the preferred answer is wrong"; six spell the
preferred answer out and five state theirs as a justification. Recorded here with the outcome,
because a risk register whose every entry has resolved is the clearest possible statement that the
design held:

| Risk | Preferred answer | What happened |
|---|---|---|
| Strawberry version compatibility | do not bump the lower bound; `>=0.262.0` already exposed the full Relay surface | held for this card; the floor later moved to `0.316.0` for an unrelated reason (spec-044 extension isolation) |
| `cls.__bases__` mutation constraints | attempt the assignment, surface `TypeError` as a `ConfigurationError` naming the offending interface; fallbacks were a replacement class with rewritten registry entries, or narrowing to explicit inheritance | preferred answer shipped verbatim in `apply_interfaces`; neither fallback was needed |
| Should non-Relay interfaces ship in `0.0.5`? | yes — generic base application with Strawberry validation in scope, Relay defaults only for Relay; fallback was `relay.Node`-only with a focused error | preferred answer shipped; pinned by `::test_non_relay_interface_works` and live by `library`'s `interfaces = (relay.Node, Named)` |
| Should Relay ID mapping be configurable globally? | no — per-type activation on `relay.Node`; fallback was a future setting | held through `0.0.5`; `0.0.9` added `Meta.globalid_strategy` and `RELAY_GLOBALID_STRATEGY`, which configure the *payload*, not whether the mapping activates |
| Should `resolve_node` use the optimizer? | apply `cls.get_queryset(...)`; consult the optimizer "only if straightforward" | it was not straightforward and was not done; still deferred at `HEAD` |
| Base-class injection vs Strawberry decoration cache | injection must run before `strawberry.type(...)` on every pass and `registry.clear()` must keep releasing `_definitions` | held; reduces to the `0.0.4` clear-and-redefine contract, pinned by the registry idempotency row |
| `relay.Node` `is_type_of` interaction | inject for every `DjangoType`; not borrowing risks "Cannot determine type for object of model X" | shipped; later extended with the multi-type hint stamp by `DONE-032-0.0.9` |
| `relay.NodeID` annotation discovery | `super(cls, cls).resolve_id_attr()` with a `"pk"` fallback; a parallel `Meta.id_attr` key would fragment the surface | the *conclusion* held — no `Meta.id_attr` key exists — but the mechanism did not: see Decision 3's recursion trap |
| Composite primary keys | reject at finalization with a clear `ConfigurationError`; fallback was a deterministic encode/decode contract | rejection shipped, with the `NodeID` escape hatch the message proposes actually honored |
| Connection-field stability | keep the four defaults small so a connection slice can wrap or replace them without churn | held: `DjangoConnectionField` and `DjangoNodeField` shipped at `0.0.9` and dispatch **into** these defaults rather than replacing them |
| Sentinel/cascade behavior | do not adopt graphene-django's `get_node` sentinel routing; let the permissions slice decide | `apply_cascade_permissions` shipped at `0.0.10` and integrates through `get_queryset`, not through `resolve_node` — the question this bullet posed, answered |

*Why the whole section moved rather than being trimmed to its live entries.* Not one bullet is still
open. A "risks and open questions" section in which every risk resolved is, by construction, a change
record — and a reader who meets it in the spec has to check eleven resolutions against the tree
before knowing which sentences are contracts. Zero are.

### `## Test plan` — three relocations and one false assertion claim

Spec: [Test plan][spec-015-test-plan].

*Nothing moved; four bullets were rewritten.* Three name tests that no longer live where the spec
says, and one describes an assertion the shipped test does not make.

**The three relocations** are recorded under `### Nothing was skipped in the code` above, proven by
the adding and removing diffs. The reconciled Test plan names the live twins by path and node id, so
a reader can find the coverage instead of concluding it was dropped.

**The false assertion claim.** The spec said `test_resolve_id_attr_falls_back_to_pk` proves the
default "returns the model's concrete pk attname (e.g. `"id"` after Django resolves `"pk"`)". The
shipped row asserts `CategoryNode.resolve_id_attr() == "pk"` and, directly,
`_resolve_id_attr_default(CategoryNode) == "pk"`. The literal string `"pk"` is what the default
returns; the coercion to the concrete attname happens one layer later, inside `_resolve_id_default`,
which is where the spec's own Decision 3 puts it. The spec's `## User-facing API` says
`BookType.resolve_id_attr()` returns `"pk"` — so the document disagreed with itself on this too, and
the Test-plan half was the wrong half.

*One more `## User-facing API` bullet was false in the same family.* It promised
`BookType.resolve_id(root, info)` returns `str(root.__dict__["pk"])`. Django never stores the pk under
the literal key `"pk"`; the shipped resolver coerces `"pk"` to `root.__class__._meta.pk.attname`
first, which is exactly what Decision 3's port note says it must do, and keying on the **root's**
class rather than the definition's model is deliberate so proxy-model rows are not mis-keyed.

### `## Out of scope` and the KANBAN ids — sixteen board references, none of them resolvable

Spec: [Out of scope][spec-015-out-of-scope], plus `## Problem statement`, `## Non-goals`,
`## Doc updates`, and Decision 8.

*Nothing moved; every board reference was replaced by a statement of the current contract.* The spec
cited `READY-004`, `READY-002`, `READY-003`, `READY-005`, `NEXT-005`, `NEXT-006`, `NEXT-001`,
`NEXT-002`, `BACKLOG-005`, `BACKLOG-007`, `BACKLOG-009`, `BACKLOG-011`, `BACKLOG-012`, `BLOCKED-002`,
`IN-PROGRESS-001`, and `DONE-011`. All predate the board's renumbering, and each now names a
different card or nothing.

*Why the ids were not simply renumbered.* [`worker-0.md`][worker-0] #"Verify card/glossary references against the DB"
forbids the partial fix, and the reason is visible in this very list: eight of the
sixteen name deferrals that have since **shipped**, so a correct renumber would point at a `DONE`
card while the surrounding sentence still says "planned for a later slice". Renumbering buys a
correct pointer to a wrong claim. Stating the current contract fixes both, and needs no board id at
all — every status below was read from [`docs/GLOSSARY.md`][glossary], the durable catalog, not from
the moving board:

| What the spec deferred | Status at `HEAD` |
|---|---|
| `DjangoConnectionField`, `DjangoNodeField` | shipped `0.0.9` |
| Connection-aware optimizer planning | shipped `0.0.9` |
| `Meta.primary` / multiple types per model | shipped `0.0.6` |
| Cascade permissions (`apply_cascade_permissions`) | shipped `0.0.10` |
| Filters / orders (`FilterSet`, `OrderSet`) | shipped `0.0.8` |
| Consumer override semantics for scalar fields | shipped `0.0.6` |
| Deferred scalar conversions (`BigIntegerField`, `JSONField`, …) | shipped `0.0.6` |
| Stable choice-enum naming (`Meta.choice_enum_names`) | planned `0.1.4` |
| `FieldSet` | planned `0.1.1` |
| Aggregates (`AggregateSet`, `Meta.aggregate_class`) | planned `0.1.3` |
| Migration / adoption guides | planned `0.1.8` |
| Composite-primary-key Relay node encoding | still out of scope; no successor contract |

*The one that reads as a defect and is not.* `## Doc updates` instructed moving `READY-004` to a new
`DONE-NNN` card and advancing the recommended hybrid sequence. That work landed — the card is
`DONE-015-0.0.5` — and the instruction is now a description of a completed action, so the reconciled
bullets state the shipped card rather than the movement.

### The `relay.NodeID` spelling — a later card made the documented form an error

Spec: [User-facing API][spec-015-user-facing-api] and [Test plan][spec-015-test-plan].

*Deleted, not moved: `id: relay.NodeID[str] = strawberry.field(...)`.* The spec offered that spelling
twice as the way to point Relay at a non-pk column without overriding a classmethod.

*Why it is now an error rather than merely dated.* At `HEAD`
[`types/base.py::DjangoType.__init_subclass__`][types-base] carries a Relay id-collision guard added
at `0.0.6`: on a Relay-shaped type an **assigned** `id = strawberry.field(...)` raises
`ConfigurationError` outright, and an `id` **annotation** must be `relay.NodeID[...]`. The error text
names the three supported recourses — `@classmethod resolve_id`, an `id: relay.NodeID[<pk_type>]`
annotation, or a resolver-backed sibling field. A reader following the spec's spelling would have hit
a `ConfigurationError` on the class they were writing.

*The mechanism the spec described was also the wrong shape, independently of `0.0.6`.* The shipped row
`::test_node_id_annotation_overrides_default_id_attr` annotates the **target column**
(`name: relay.NodeID[str]`), not `id`, and its docstring records a trap the spec never mentions: the
subscripted `relay.NodeID[str]` form is required, because the bare `Annotated[str, relay.NodeID]`
spelling does not register — Strawberry expects `NodeIDPrivate` instances in the metadata, which only
land via subscription. The reconciled prose carries both facts.

*Claim the spec no longer makes.* That a consumer may declare
`id: relay.NodeID[str] = strawberry.field(...)` on a Relay-shaped `DjangoType`.

### Decision 1's block-comment citation — a comment that no longer exists

Spec: [Decision 1][spec-015-decision-1].

*Deleted, not moved.* "The deferred-key comment at `django_strawberry_framework/types/base.py
#"DEFERRED_META_KEYS: frozenset[str]"` already names this seam."

*Why deleted.* The comment it cites was the design note quoted in the moved spike entry — "the
relay-interface application pass (`cls.__bases__` injection before `strawberry.type`) has not landed
yet" — and it was removed when the pass landed, correctly: `grep -c "relay-interface application
pass"` over the `HEAD` blob of `types/base.py` returns **0**. The sentence pointed a reader at a
comment that would tell them the feature is unbuilt, and then at nothing. The `#"…"` substring in the
citation still resolves, which is why it survived: the anchor is the constant's declaration line, not
the comment the sentence was about.

### The `README.md` citations — the substring survived, the sentence did not

Spec: [Current state][spec-015-current-state], [Decision 1][spec-015-decision-1], and
[Definition of done][spec-015-definition-of-done] item 11.

*Deleted, not moved: three citations of a promise their target does not carry.* The spec cited
`README.md #"For the current capability snapshot"` three times, as the source of "It is stable
through `0.1.0`" (of `get_queryset`), "the public-surface promise" (Decision 1), and "today's names
remain stable through `0.1.0`" (DoD 11).

*This is the pass's cleanest illustration of why grep does not clear a claim.* The substring is
present at `HEAD`: [`README.md`][readme] carries a paragraph beginning "For the current capability
snapshot". That paragraph is a three-sentence pointer to `TODAY.md`, `docs/GLOSSARY.md`, and
`KANBAN.md`. It contains no stability promise, no `0.1.0` horizon for the public surface, and no
mention of `get_queryset`. A symbol-qualified reference validated by grep therefore passed for
fifteen months while the sentence it was cited for lived somewhere else — README's alpha-status
paragraph says "The public names are stable", full stop, with no version horizon.

*What the reconciled spec says instead.* The public-surface claim is re-anchored to the sentence that
actually makes it, and the `0.1.0` horizon — which no current document asserts — is dropped rather
than re-attributed. The `get_queryset` stability claim keeps only what is verifiable: the hook is
shipped, documented in [`docs/README.md`][docs-readme], and every framework-owned invocation now runs
through the sealed visibility boundary.

*Claim the spec no longer makes.* That any current document promises the public surface, or
`get_queryset`, is stable through `0.1.0`.

## Reconciliation record — what the spec now says, and why

### The strategy, and what it rejected

Three dispositions were available for a shipped spec whose text later work falsified.

- **Leave it and describe the drift here.** Rejected: the maintainer's second obligation is explicit
  that the spec must state the current contract, and a reader who opens the spec first — which is
  what a spec is for — would still be told that `_resolve_id_attr_default` calls
  `super(cls, cls).resolve_id_attr()`, which at `HEAD` is an infinite recursion.
- **Annotate each falsified claim in place with what superseded it.** Rejected by
  [`BUILD.md`][build] `## Spec rationale extraction` in as many words: no amendment block, no
  retraction paragraph, no "as of review round N". A contract that carries its own chronology forces
  the reader to reconstruct the present by applying a diff, which is the failure `## Current state`
  already demonstrated at one-sentence scale.
- **Rewrite each falsified claim to state what holds, and record every change here.** Chosen. The
  spec reads as though it had been right from the start; this file carries what changed, when, why,
  and which commit caused it.

### The reconciliation, section by section

- **`Status:` line** — states that this is the primary spec for the shipped `0.0.5` Relay foundation
  and names the card, `DONE-015-0.0.5`. The merge record and the `READY-004` id are gone.
- **`## Slice checklist`** — Slice 3's sub-bullet now says the pk field's name is dropped for a
  Relay-shaped type rather than "the `id` key … when `relay.Node` is among `Meta.interfaces`";
  Slice 4's four resolver sub-bullets carry the shipped signatures; the Slice-5 `Cleanup` box is
  removed. Boxes stay unticked: the `Status:` line is the source of truth for a shipped card, and
  ticking a historical checklist would assert a per-item verification this pass did not perform.
- **`## Current state`** — the deferred-key bullet, the finalizer bullet, and the optimizer bullet
  state `HEAD`. The `get_queryset` bullet drops the unsupported stability horizon and names the
  sealed boundary. The glossary quotation matches the glossary's current wording.
- **`## User-facing API`** — the `resolve_id_attr` / `resolve_id` bullets state the `"pk"` return and
  the attname coercion; the `resolve_node` / `resolve_nodes` bullets drop the optimizer-consultation
  claim; the `get_queryset` cooperation subsection names the shared visibility boundary the calls
  route through.
- **Decisions 2, 3, 5, 8, 9 and the `## Internal helper surface`** — rewritten as recorded in the
  entries above. Decisions 1, 4, 6, 7 keep their normative content and lose only justification
  paragraphs, except Decision 7's fifth invariant, which is restated so it no longer promises a
  `select_related` shape the tree does not produce.
- **`## Implementation plan`** — commit 3's "drop the `id` key" becomes the pk-name suppression;
  commit 5's promotion-rule justification loses its board id. The five-commit framing stays: it is
  how the work was actually sequenced and `e6907fa8` / `e836d72e` are the commits it names.
- **`## Test plan`, `## Non-goals`, `## Out of scope`, `## Doc updates`, `## Definition of done`** —
  reconciled per the entries above.
- **What did not change.** `## Problem statement`'s framing, `## Goals`, `## Edge cases and
  constraints`, Decision 3's injection loop, and all three `## User-facing API` code examples are
  accurate at `HEAD` and were left alone. The three examples were re-read against the shipped
  validator and finalizer rather than assumed.

### The link scaffold

The spec's link-definition block is unchanged: all nineteen `[glossary-*]` defs survive, because the
one whose only body use left the spec (`#apply_cascade_permissions`) was re-homed onto the
`## Non-goals` cascade bullet in the same edit. This file's own block carries the ten canonical group
headers in order, with paths resolved from `docs/SPECS/appx/` and disk-checked.

### What this cycle deliberately did not fix

- **The `[spec-011]` citation cluster.** `81e4704d` renamed the file without sweeping its citations,
  so eight sites — five in `types/base.py`, one in `types/resolvers.py`, one in
  `tests/types/test_base.py`, one in `tests/filters/test_sets.py` — cite `spec-011`, which is now a
  different document. It is verified (three distinct quoted substrings each resolve once in spec-015
  and zero times in spec-011), already homed on a live [`KANBAN.md`][kanban] card with the correct population and an
  explicit "do not widen this into a documentation sweep" boundary, and every one of those files is
  dirty with a concurrent session's in-flight work. Recorded, not stolen.
- **The A/B relation-planning row.** Recorded under
  this file's Decision 7 entry: no current row asserts that
  planning across a Relay-declared target matches planning across a non-Relay one. Writing it is a
  test change, and this cycle writes no code.
- **A stale cross-reference inside a shipped test docstring.**
  [`tests/types/test_relay_interfaces.py`][test-relay-interfaces]`::test_relay_node_strips_django_id_annotation`
  closes with "End-to-end coverage of the same suppression path lives in
  `tests/types/test_definition_order_schema.py`" — the file whose two Relay extensions `be9130e3`
  retired in favour of the live twins. The docstring is accurate about there being end-to-end
  coverage and wrong about where. Fixing it edits a test file, which this cycle's writable set
  excludes.
- **The `public-exports` terms-CSV gap.** The spec links nineteen glossary anchors and the companion
  CSV carries eighteen; `public-exports` is linked from the Slice checklist but has no CSV row, so the
  `DONE-015-0.0.5` card renders eighteen glossary terms. That is the archive audit's item, not this
  one's.

## Addendum: substring-anchor stability, and four counts re-measured

Appended by the archive-audit pass, which re-derived the reconciliation above against `HEAD`
independently. Everything the reconciliation asserts about the shipped code held on re-reading; what
did not hold is recorded here rather than by rewriting the entries, so the record of what was
believed and when survives.

### Four `#"unique substring"` anchors the reconciliation retired, and seven citations that quote them

Bears on [Decision 1][spec-015-decision-1], [Decision 2][spec-015-decision-2], and
[Decision 6][spec-015-decision-6].

`AGENTS.md` rule 27 lets shipped source cite a spec by `spec-NNN #"unique substring"`, and eleven
such substrings of this spec are quoted from `django_strawberry_framework/types/relay.py` and
`tests/types/test_relay_interfaces.py`. Rewriting a cited sentence retires its anchor exactly the way
renaming a symbol retires a `::QualifiedName`, and the reconciliation rewrote four of them:

| Substring | Cited from | Disposition |
|---|---|---|
| `is removed from synthesized scalar annotations` | `tests/types/test_relay_interfaces.py::test_relay_node_strips_django_id_annotation` | restored in Decision 2 (the rewrite had inserted one word, "the") |
| `Composite primary keys (Django 5.2+) are explicitly out of scope` | `types/relay.py::_check_composite_pk_for_relay_node`, `tests/types/test_relay_interfaces.py::test_relay_node_with_composite_pk_raises` | restored in Decision 2 ("explicitly" had been dropped) |
| `injection (Decision-1 borrow) is added unconditionally` | `types/relay.py::install_is_type_of`, `tests/types/test_relay_interfaces.py::test_is_type_of_injected_for_all_djangotypes` | restored in Decision 6 (the parenthetical had been dropped as borrowing-posture residue) |
| ``surface any `TypeError` `` … `` as a `ConfigurationError` `` | `tests/types/test_relay_interfaces.py::test_apply_interfaces_wraps_typeerror_as_configuration_error` | **not** restored to the spec — the sentence belongs to the moved risk register, and putting deliberation back would undo the move. The verbatim risk bullet below carries the sentence and is the anchor's one occurrence in this companion, so the citation resolves there; this row elides the middle of the anchor so the catalogue is not a second occurrence. `types/relay.py::apply_interfaces` cites Decision 1 `#"never as a raw layout error"` instead, which resolves in the spec. |

Restoring three wordings costs the spec nothing: each sentence is otherwise unchanged and each
remains true at `HEAD`. The general lesson is the cheap one — **a spec sentence that shipped source
quotes is an interface, and rewording it is a breaking change to that interface.** Sweep every anchor
before and after any reconciliation pass, and sweep it on **flattened** text. A citation whose
opening `#` + quote sits on one line and whose closing quote sits on the next is the same anchor with
a newline inside it, and every line-scoped matcher — `git grep` included — reports it as absent, so
the sites most in need of repair are the ones a per-line sweep cannot see. Flatten first, then match:

```shell
git ls-files '*.py' '*.md' | while read -r f; do
  tr '\n' ' ' <"$f" | grep -oE 'spec-[0-9]{3}[^"]{0,120}#"[^"]+"' | sed "s|^|$f: |"
done
```

The companion sweep finds the split anchors themselves: an occurrence of `#` immediately followed by
a double quote, with no further double quote later on the same line, is a citation broken across a
line break. It resolves in no target, and no gate reports it —
[`scripts/check_citations.py`][check-citations] matches `path::Symbol` within a single line and holds
`docs/` out of scope by design.

*The verbatim risk bullet, so the fourth citation resolves.* From the moved
`## Risks and open questions`:

"**`cls.__bases__` mutation constraints.** Python permits assigning to `cls.__bases__` only when the
resulting MRO and instance layout are compatible. In practice this is fine for `DjangoType` +
Strawberry interfaces because all interfaces are zero-attribute classes. Preferred answer: attempt
the assignment and surface any `TypeError` as a `ConfigurationError` that names the offending
interface. Fallback: if base mutation is unsafe for some real `DjangoType` shape, the implementation
creates a replacement class with the desired bases and updates `registry._types` / `_definitions` to
point at it, or narrows the slice to require explicit `class Foo(DjangoType, relay.Node):` and
reserves `Meta.interfaces` for a later slice. The Meta-driven path is preferred; the fallbacks exist
so the slice can ship even if a corner case turns up."

The remaining seven substrings, plus the three that shipped source still cites under the pre-renumber
`spec-011` name, each resolve exactly once in the reconciled spec.

### A dead symbol reference the reconciliation carried forward

Bears on [Decision 7][spec-015-decision-7]. Its FK-id-elision invariant cited
`django_strawberry_framework/types/resolvers.py::_is_fk_id_elided`, a symbol that does not exist at
`HEAD` and did not exist when the reconciliation ran — it was inherited unexamined from the
pre-reconciliation text, in the one Decision the pass otherwise rewrote. The resolver-side executor
is `::_build_fk_id_stub` (the walker reads the stamped `FieldMeta.fk_id_elision_eligible` slot), and the citation now names it.

### Decision 3's injection-loop fence did not match the shipped guard

Bears on [Decision 3][spec-015-decision-3]. The reconciliation recorded the fence as accurate at
`HEAD` and left it alone. It was not: `types/relay.py::install_relay_node_resolvers` guards with
`existing is None or (existing_func is not None and existing_func is node_func)`, where the fence
compared two `getattr(..., "__func__", None)` results directly — so a consumer attribute with no
`__func__` would have matched a `None` default and been overwritten. The fence now carries the
shipped guard, and the sentence below it attributes the identity test to strawberry-django and the
added clause to this package.

### Four counts, re-measured

Numbers the reconciliation stated that did not reproduce, corrected in place above where they appear
in this file and listed here so the correction is visible:

- **626, not 627, lines** in the spec before the pass (`wc -l` and `awk 'END{print NR}'` agree; the
  file ends with a newline, so there is no off-by-one to recover). Byte counts were exact:
  73,479 → 66,594.
- **Six fenced blocks survive, not four**, and the spec **gains one** rather than none — the
  restated `## Internal helper surface` list is itself a new fence. Seven before, six after.
- **Nineteen `[glossary-*]` defs, twenty-one uses** — `glossary-configurationerror` (Slice 4
  checklist and Decision 1) and `glossary-metaprimary` (`## Non-goals` and Decision 8) are each used
  twice, so "each used exactly once" is wrong. The load-bearing half holds: every def is used at
  least once and none is orphaned.
- **`## Borrowing posture` measures 6,230 bytes**, not 6,210, taking the section as its heading line
  through the line before the next `## `. `## Risks and open questions` reproduced exactly at 5,568.

Two descriptive looseness items. The first is recorded and not corrected: the eleven risk bullets are
summarized in a three-column table above rather than reproduced verbatim, so "*Moved, all eleven
bullets*" is true of the substance and not of the wording — the verbatim `cls.__bases__` bullet is
now above, and the other ten are paraphrase.

The second **has since been corrected in the spec**. `## Test plan`'s two projection bullets
illustrated the query as `{ allItems { id } }` / `{ allItems { id otherScalar } }` where the shipped
rows in `tests/optimizer/test_relay_id_projection.py` send `{ allCategories { id } }` and
`{ allCategories { id name } }` — wrong on both the root field and the second selection. The
invariant each bullet describes was always the one its named row asserts, which is why this was
graded as looseness rather than a false claim, and the bullets now name the queries the rows send.
Two details are worth keeping, because both are what let the error survive four passes over this
section: `allItems` **does** occur in that module, in a third row
(`::test_relay_id_with_custom_pk_attname_avoids_lazy_load`), so a grep for it returns a plausible
hit; and `otherScalar` occurs nowhere in the repository at all, which is the tell a reader should
have caught first. An illustrative query inside a `## Test plan` bullet is still a claim about
shipped code, and it is checkable by reading the row it names.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[changelog]: ../../../CHANGELOG.md
[goal]: ../../../GOAL.md
[kanban]: ../../../KANBAN.md
[pyproject]: ../../../pyproject.toml
[readme]: ../../../README.md

<!-- docs/ -->
[docs-readme]: ../../README.md
[glossary]: ../../GLOSSARY.md
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[spec-015]: ../spec-015-relay_interfaces-0_0_5.md
[spec-015-current-state]: ../spec-015-relay_interfaces-0_0_5.md#current-state
[spec-015-decision-1]: ../spec-015-relay_interfaces-0_0_5.md#decision-1-where-interfaces-are-applied
[spec-015-decision-2]: ../spec-015-relay_interfaces-0_0_5.md#decision-2-id-field-handling
[spec-015-decision-3]: ../spec-015-relay_interfaces-0_0_5.md#decision-3-relay-resolver-injection
[spec-015-decision-4]: ../spec-015-relay_interfaces-0_0_5.md#decision-4-validation
[spec-015-decision-5]: ../spec-015-relay_interfaces-0_0_5.md#decision-5-lifecycle-and-idempotency
[spec-015-decision-6]: ../spec-015-relay_interfaces-0_0_5.md#decision-6-compatibility-with-the-override-contract
[spec-015-decision-7]: ../spec-015-relay_interfaces-0_0_5.md#decision-7-optimizer-and-projection-invariants
[spec-015-decision-8]: ../spec-015-relay_interfaces-0_0_5.md#decision-8-registry-implications-and-one-type-per-model
[spec-015-decision-9]: ../spec-015-relay_interfaces-0_0_5.md#decision-9-async-resolver-support
[spec-015-definition-of-done]: ../spec-015-relay_interfaces-0_0_5.md#definition-of-done
[spec-015-internal-helper-surface]: ../spec-015-relay_interfaces-0_0_5.md#internal-helper-surface
[spec-015-out-of-scope]: ../spec-015-relay_interfaces-0_0_5.md#out-of-scope-owned-elsewhere
[spec-015-test-plan]: ../spec-015-relay_interfaces-0_0_5.md#test-plan
[spec-015-user-facing-api]: ../spec-015-relay_interfaces-0_0_5.md#user-facing-api

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-0]: ../../builder/worker-0.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->
[types-base]: ../../../django_strawberry_framework/types/base.py
[types-finalizer]: ../../../django_strawberry_framework/types/finalizer.py
[types-relay]: ../../../django_strawberry_framework/types/relay.py
[utils-querysets]: ../../../django_strawberry_framework/utils/querysets.py

<!-- tests/ -->
[test-registry]: ../../../tests/test_registry.py
[test-relay-id-projection]: ../../../tests/optimizer/test_relay_id_projection.py
[test-relay-interfaces]: ../../../tests/types/test_relay_interfaces.py

<!-- examples/ -->
[products-schema]: ../../../examples/fakeshop/apps/products/schema.py
[test-library-api]: ../../../examples/fakeshop/test_query/test_library_api.py
[test-products-api]: ../../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->
[check-citations]: ../../../scripts/check_citations.py

<!-- .venv/ -->

<!-- External -->
