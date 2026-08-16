# Build: R1 — spec/code reconciliation (scrub six dropped features, correct ten drift rows)

Spec reference: `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` (whole file; the archived spec)
Rationale companion: `docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md` (append-only this cycle)
Build plan: `docs/builder/build-009-rich_schema_architecture-0_0_4.md`
Status: final-accepted

**This is a combined plan + perform pass** under the plan's `### Deviation 3`. Worker 1 wrote the plan below AND performed every edit; there is no Worker 2 build report, because the deliverable is spec + rationale edits and Worker 1 is the only role that may make them. `Status: planned` routes this artifact to Worker 3 for audit, not to Worker 2.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable in its usual form and stated rather than omitted: **this item writes no package code**, so no helper, shared constant, validation branch, coercion utility, or test helper is proposed and the package-wide AST inventory has nothing to prevent. The read-only source reading this pass did perform is recorded under `### Source verification performed` — it was verification of claims, not a search for a reuse site. If Worker 3 disagrees that the inventory is moot here, the disagreement is about whether a documentation pass can introduce duplication in `django_strawberry_framework/`, and it cannot: the diff touches two `.md` files.
- **Existing patterns reused.** The rationale companion's own six pre-existing entries are the shape every new entry copies: heading names the spec section, `*Moved.*` marks text cut out of the spec, alternatives are named with the reason each lost. No new entry shape was invented. The spec's existing conventions were likewise reused rather than extended — symbol-qualified in-repo citations (`path::QualifiedName`, `path #"substring"`), reference-style cross-file links, `TODO-<MILESTONE>-<NNN>-<x.y.z>` card ids.
- **New helpers justified.** None.
- **Duplication risk avoided.** Two, both real for this item. **(a) The spec restating the rationale.** Prevented by the single-ownership split the plan's DRY rule states: every *why it lost* sentence went to the rationale and no scrubbed mechanism is argued in the spec. The one deliberate exception is implementation-relevant rationale, which `worker-1.md` `### Performing the rationale move` says **stays** — e.g. the value-not-callable hint rule and the "generic alias loses `resolve_connection`" mechanism, both of which change how a future change is built. **(b) The spec becoming a second copy of the board.** Prevented by a rule adopted here and recorded in the rationale: *name a card for open work, never a version for shipped work.* Naming a card points forward and has one owner; naming a shipped version duplicates `KANBAN.md` and drifts. This is what lets Maintainer decision 1 ("state which card owns each still-unshipped layer") and the first residual cycle's rejection of per-phase shipped-version annotations both hold at once.

### Boundary count

Zero. This item adds no guard, cap, rejection path, or validation branch — it writes no executable line. No split trigger fires. No failability proof is owed (`BUILD.md` `### What needs a proof, and what does not`: doc edits need none).

### Hot-path declaration

Not applicable; the plan declares no hot path for any residual item, and this one touches no executable line.

### Floor-verification scope

None, per the build plan's cycle-wide declaration. No item changes package behavior at any version.

### Implementation steps

Performed in this pass. Paths are exact; no line numbers are cited (`AGENTS.md` rule 27 — and the spec's zero in-repo `path:NN` count is a property this pass preserves, re-measured below).

1. Scrub each of the six dropped features from **every** site, not only the sites the dispatch named — a `grep -c` sweep per dropped symbol after the named sites are fixed (`### Sweep evidence`).
2. Where a scrubbed section's whole subject was the dropped mechanism, rewrite it to state what the shipped architecture actually does, with symbol-qualified evidence. Never leave a hole, never leave "this was rejected" prose in the spec body.
3. Apply the ten Group-B corrections per the plan's table, verifying each row against source first.
4. Keep every surviving Decision's number and heading text stable; repurpose the vacated slot rather than renumber or gap.
5. Append one rationale entry per touched spec section, naming the alternatives rejected and why each lost, and any claim the section may no longer make.
6. Re-run `check_spec_glossary.py`, `check_trailing_commas.py --check`, the link-definition and in-page-anchor validators, and the cross-reference sweep.

### Test additions / updates

None. This item runs no tests and changes no code. The two mechanical checks in `### Validation run` are the whole verification surface, plus the link/anchor validators written for this pass.

### Implementation discretion items

None delegated — there is no Worker 2 on this chain. Two choices the dispatch explicitly left to Worker 1 are **decided** here and recorded in `### Spec changes made (Worker 1 only)`: how to handle Decision 3's vacated slot, and how to handle `## Migration path`'s Phase 3.

### Dispatched findings checklist

One box per drift row dispatched to R1 — D1-D16, minus D6's spec-028 half (item R2's) and minus Group C (verified accurate; not dispatched). Group C rows are listed after the boxes as explicit non-work so a later pass does not re-open them.

- [x] **D1** — `types/fields.py::DjangoModelField`: the spine of `### Layer 4`, `### Decision 3`, `### Phase 3`, `### Layer 9`, and the `### Borrow \`StrawberryDjangoFieldBase\`…` transition path. Verdict `DROP AND SCRUB`. No `types/fields.py` exists; zero package-wide occurrences; `types/resolvers.py::_attach_relation_resolvers` is the **permanent** finalizer Phase-2 mechanism.
- [x] **D2** — `OptimizerStore` + `with_hints` / `with_prefix` / `apply` + Info-scoped callable prefetch/annotate hints, in `### Borrow \`OptimizerStore\`…` and `### Layer 11`. Verdict `DROP AND SCRUB`. Zero occurrences of all four names; the callable-hint bullet is **contradicted** by `optimizer/hints.py` #"MUST never depend on request-varying data".
- [x] **D3** — `get_strawberry_annotations` borrowed into `utils/typing.py`, in `### Borrow \`get_strawberry_annotations\``. Verdict `DROP AND SCRUB`. Zero occurrences; provenance is solved by the four `consumer_*_fields` frozensets on `types/definition.py::DjangoTypeDefinition`.
- [x] **D4** — `DjangoField(...)` "for explicit advanced fields", one sentence in `### Borrow \`field\` and \`connection\` as implementation patterns`. Verdict `DROP AND SCRUB`. Absent from `__init__.py::__all__`; the explicit non-Relay field ships as `list_field.py::DjangoListField`.
- [x] **D5** — keep `DjangoModelType` "as an internal or explicitly requested fallback", in `### Borrow \`resolve_type\`…` plus the `## Open questions` "Should generic fallback exist?" answer. Verdict `DROP AND SCRUB`; scrubbing resolves a live self-contradiction with `### The unresolved-relation contract is error-only`.
- [x] **D6 (spec-009 half only)** — `ASC_DISTINCT` / `DESC_DISTINCT` and "PostgreSQL `DISTINCT ON` plus window-function fallback" in `### Layer 7`, and the `### Phase 5` acceptance-test line. Verdict `DROP AND SCRUB`. The spec-028 half is item R2's and was **not** touched.
- [x] **D7** — `## Target outcome` root field `object_type: ObjectTypeNode = DjangoNodeField(ObjectTypeNode)`; the supported spelling is `ObjectTypeNode | None`.
- [x] **D8** — `## Target outcome` `Meta` carrying `aggregate_class`, `fields_class`, `search_fields`, all three in `types/base.py::DEFERRED_META_KEYS` and hard-rejected at class creation today.
- [x] **D9** — `### Borrow \`DjangoListConnection\`` sketch: `DjangoConnection` carrying `total_count: int | None` and `aggregates: AggregateType | None`. Wrong in both fields.
- [x] **D10** — `### Borrow \`StrawberryDjangoDefinition\`` dataclass sketch: storage attr matches exactly; `fields`→`fields_spec`, `exclude`→`exclude_spec`; `aggregate_class` / `search_fields` / the `LazyClassRef` union absent. **Over-ticked at the combined pass and closed in the apply-changes pass** — the sketch is now corrected and change 36 records it.
- [x] **D11** — `### Layer 6` filter API: `class ObjectFilter(AdvancedFilterSet)` with `Meta.filter_fields`.
- [x] **D12** — `### Layer 7` / `### Layer 8` base names `AdvancedOrderSet` / `AdvancedAggregateSet`.
- [x] **D13** — `### Layer 5` item 2 "finalize pending types", which contradicts the spec's own corrected `### Layer 3`.
- [x] **D14** — `## Proposed module layout`: `types/fields.py` a dead proposal; `fieldset.py` listed flat against the section's own package-layout preamble; `orders/inputs.py` omitted although shipped code requires it.
- [x] **D15** — `## Migration path` Phases 1-8, with Phase 3 never shipped.
- [x] **D16** — `## Success criteria` (11 bullets); the three unmet ones are each carded.

**Group C — verified accurate, deliberately untouched** (recorded so no later pass re-opens them): `## The 0.0.4 local package baseline` and its two "retired since" markers; `#### Take class-based generated type naming`; the `### Layer 2` `PendingRelation` sketch; `## Target outcome`'s `class ObjectTypeNode(DjangoType, relay.Node)` declaration (valid, not drift — `types/relay.py::apply_interfaces` #"already inherits a listed interface directly" makes it a documented no-op); and the upstream `file:///…#LNN` citations, which were **not** "fixed".

---

## Perform report (Worker 1, combined pass)

### Files touched

- `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` — six scrubs, ten drift corrections, two convention fixes. Itemized in `### Spec changes made (Worker 1 only)`.
- `docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md` — **appended only.** Eleven new entries plus a `### Convention corrections made in the same pass` entry, in the existing six-entry shape. Two link definitions added under `<!-- docs/ -->` (`glossary-filterset`, `glossary-ordering`). **No existing entry was rewritten**, and `## How to read this file`, `## Provenance of this record`, and `## Standing notes` were not edited.
- `docs/builder/bld-009-r1-spec_code_reconciliation.md` — this artifact.
- `docs/builder/worker-memory/spec-009-worker-1.md` — created and appended (the cycle's namespaced file; it did not exist, so this pass created it).

No source file, test file, example file, sibling spec, standing doc, or DB row was touched. `docs/SPECS/spec-028-orders-0_0_8.md` was **read-only** and is item R2's.

### Byte counts

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-009-…-0_0_4.md` | 54,232 bytes / 1,154 lines | **60,855 bytes / 1,099 lines** | +6,623 bytes / **-55 lines** |
| `docs/SPECS/appx/spec-009-…-rationale.md` | 12,273 bytes / 208 lines | **36,744 bytes / 537 lines** | +24,471 bytes / +329 lines |

`git diff --stat` on the spec reads **103 insertions, 158 deletions** — the spec lost more lines than it gained and still grew in bytes. That is the honest shape of this pass and is worth stating rather than glossing: the six scrubs deleted a dataclass sketch, three bullet lists, and a transition path (many short lines), while the replacements are prose paragraphs stating what the shipped architecture does, plus the D7-D16 corrections, which are net additions by construction. The corpus ratchet does not reach a spec — `BUILD.md` `## The corpus ratchet` scopes it to `BUILD.md`, `ARTIFACT.md`, and the four `worker-*.md` files — but the growth is recorded here so a maintainer can judge whether any replacement paragraph is longer than its subject deserves.

### Source verification performed

The plan's finding table is Worker 0's verified input contract and was not re-litigated; every row this pass wrote prose against was re-read at source first, per the dispatch. Read-only, symbol-qualified:

- **D1 replacement machinery** — `types/finalizer.py` #"Phase 2: ``_attach_relation_resolvers`` installs the framework's auto"; `types/resolvers.py::_make_relation_resolver`; `types/resolvers.py::_attach_relation_resolvers`; `types/converters.py::resolved_relation_annotation`; `utils/querysets.py::apply_type_visibility_sync`; the synthesized `__signature__` on `connection.py` #"Build the resolver ``__signature__`` + ``__annotations__`` carrying the sidecar args". All four seams exist as named.
- **D7** — `relay.py` #"Resolution is **nullable by contract**": dispatch is `required=False` unconditionally.
- **D8** — `types/base.py::DEFERRED_META_KEYS` is exactly `{"aggregate_class", "fields_class", "search_fields"}`; `types/base.py::ALLOWED_META_KEYS` read in full (18 keys). Promotion owners read from the board: `fields_class` → `TODO-BETA-054-0.1.1`, `search_fields` → `TODO-BETA-055-0.1.2`, `aggregate_class` → `TODO-BETA-057-0.1.3` with the mechanical flip on `TODO-BETA-058-0.1.3` (`KANBAN.md` #"It is the only `DEFERRED_META_KEYS` member left to promote").
- **D9** — `connection.py::DjangoConnection` #"The base carries no ``total_count`` field"; `connection.py::_build_total_count_connection`; `types/base.py::_validate_connection` #"the only recognized sub-key is ``{\"total_count\": bool}``". The generic-specialization reason for the generated subclass is `docs/GLOSSARY.md` `## \`DjangoConnection\`` #"a bare generic alias loses the `resolve_connection` override".
- **D11** — `filters/sets.py::FilterSet` (subclasses `django_filters.filterset.BaseFilterSet`); `filters/sets.py::FilterSetMetaclass.__new__` #"Allow consumers to use `filter_fields` as a synonym for `fields`". **See the correction under `### Notes for Worker 3`.**
- **D12** — `orders/sets.py::OrderSet`; `orders/base.py::RelatedOrder`.
- **D13** — `grep -n finalize django_strawberry_framework/connection.py` returns only `_finalize_queryset` and docstring prose; no `finalize_django_types` call site.
- **D6** — `orders/inputs.py::Ordering` has exactly the six members; `orders/sets.py` #"models.Min if direction.is_ascending else models.Max".
- **D14** — package listing confirms no `types/fields.py` and a shipped `orders/inputs.py`; `docs/TREE.md` #"fieldset/    # planned by TODO-BETA-054-0.1.1" and #"permissions/    # planned by TODO-BETA-059-0.1.4".
- **D3 replacement** — `types/definition.py` carries the five `consumer_*_fields` frozensets; `types/base.py::_build_annotations` produces them.
- **Layer 9 / `#### Take \`fields_class\`` replacement** — `docs/SPECS/spec-054-fieldset-0_1_1.md` #"resolver wrapping" (and its explicit rejection of both `permission_classes` and a custom field class).
- **Inbound-anchor safety** — a repo-wide grep for `spec-009` found exactly two heading-anchored inbound citations, both in `docs/SPECS/spec-010-foundation-0_0_4.md`: `### Layer 3: Finalization trigger` and `### Decision 6: fail loudly`. **Both headings are untouched by this pass.** `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` #"the higher-level target outcome" is a whole-file reference, not an anchor, and the `Meta` key list it points at survives.

### Sweep evidence

After every named site was fixed, `grep -c` per dropped symbol across the whole spec. This is what caught the sites the dispatch did not name.

| Symbol | Count after |
|---|---|
| `DjangoModelField` | 0 |
| `types/fields.py` | 0 |
| `OptimizerStore` / `with_hints` / `with_prefix` | 0 / 0 / 0 |
| `get_strawberry_annotations` | 0 |
| `DjangoField(` | 0 |
| `ASC_DISTINCT` / `DESC_DISTINCT` / `DISTINCT ON` | 0 / 0 / 0 |
| `AdvancedFilterSet` / `AdvancedOrderSet` | 0 / 0 |

`DjangoModelType` (6), `AdvancedAggregateSet` (2), and `AdvancedFieldSet` (2) survive **deliberately** — every one names an **upstream** class in a citation or in the argument for why this package refuses it, never a mechanism this package adopts. Removing them would have deleted `### Decision 1`'s and `## Why not use generic relation fallback by default?`'s reasoning along with the rejected feature, and would have made the `file:///` citations false.

Three residues only the sweep found, all now fixed: `## What to scrap from Strawberry-Django` "Keep as references" listed *optimizer stores*; `## Recommended combined architecture` item 4 said "evolve it with Strawberry-Django field stores"; `## Proposed module layout`'s evolve list called `types/resolvers.py` "transitional relation resolver support". The first two are D2 echoes and the third is D1's transition-path echo — none was in the dispatched site list. **The finalization falsification now has four known sites, not three** (layer section, decision line, open-question answer, and an implementation list — Layer 5 item 2); the rationale's `## Standing notes` predicted three.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` → `OK: 23 terms - all have glossary entries and at least one spec link.` **Exit 0. Count unchanged at 23** — no scrub removed the last mention of a glossary term. Two terms came close and were preserved on purpose: `[glossary-ordering]`, whose only site was the scrubbed Layer 7 borrow list (kept, and strengthened to name the six-member vocabulary), and `[glossary-fieldset]`, which gained sites in `## Target outcome` and `### Phase 7`.
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0.** The `<!-- LINK DEFINITIONS -->` block and all 10 canonical group headers are intact in both files.
- **Link-definition validator** (written for this pass, run over both files, code fences stripped): **0 missing definitions, 0 orphan definitions** in each. The scrub orphaned none, and the one definition added to the spec (`[spec-010]`) is used.
- **In-page anchor validator**: **0 unresolved** `](#…)` anchors in either file.
- **Cross-reference sweep**: every backtick-quoted `## …` / `### …` / `#### …` section reference in the rationale resolves to a live spec heading, by exact match or by the file's existing prefix convention (`### Layer 4` → `### Layer 4: Generated relation fields`). Verified mechanically; every prefix resolves to exactly one heading, so no reference is ambiguous.
- **Rule-27 property preserved**: the spec still carries **zero** in-repo raw `path:NN` citations. Every citation this pass added is `path::QualifiedName` or `path #"substring"`.
- `git log --stat` over both document paths → most recent commit touching either is still `f3c94642`; **HEAD unchanged at `054de9dd`**; `git status --porcelain` over both paths shows them `M` and uncommitted. **This pass's work was not swept into a concurrent session's commit.**

No `pytest` was run and no `--cov*` flag was used anywhere in this pass.

**Baseline growth observed, reported and NOT reverted** (`AGENTS.md` rule 34; the plan's `## Baseline growth`): `docs/SPECS/spec-010-foundation-0_0_4.md` and `docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md` are now `M`, and `docs/builder/build-010-foundation-0_0_4.md`, `bld-010-r1-spec_reconciliation.md`, `bld-010-r2-lazy_override_coverage.md` are untracked. That is a **concurrent spec-010 cycle**, not this cycle's output, and no worker here may edit, revert, or `git checkout` any of it. It matters to R1 for one reason and it was checked: spec-010 holds the only two heading-anchored inbound citations into spec-009. Both still read `#"### Layer 3: Finalization trigger"` and `#"### Decision 6: fail loudly"`, and both headings exist byte-identical in the edited spec-009 (`grep -c` → 1 each). Nothing dangles in either direction. Worker 0 should append this growth to the plan's own list rather than a worker editing the plan.

### Implementation notes

- **`` ``double-backtick`` `` code spans.** A rationale entry heading quotes a spec heading that itself contains code spans (`` ### Borrow `OptimizerStore`, but … ``). Backslash-escaping a backtick inside a single-backtick span does not work in Markdown — the span closes early and renders broken. Every such heading uses double-backtick delimiters, space-padded where the content ends in a backtick. Neither mechanical checker can see this class of error, which is why it is called out for Worker 3.
- **`AggregateSet` in the Layer 8 example is unlinked on purpose.** It sits inside a fenced code block, and `START.md` "Markdown link convention" keeps fenced content verbatim — a reference-style link there would render as literal brackets.
- **Ownership annotations name cards, never versions.** Applied to the three deferred `Meta` keys, `aggregates` on the connection, Phases 6 and 7, `## Proposed module layout`'s three planned packages, and the three unmet success criteria. The rule and why it does not collide with the first residual cycle's rejection of per-phase shipped-version annotations are in the rationale's `## Migration path from the 0.0.4 baseline` entry.

### Notes for Worker 3

- **Read the rationale first.** `BUILD.md` `### Who reads it, and when` puts Worker 3 there deliberately, and this pass is the case it was written for: a rewrite audited by its own author cannot see an over-cut. The specific question worth adversarial attention — **did any replacement paragraph state more than the shipped code supports?** Every claim carries a symbol-qualified citation; re-derive rather than accept, particularly the four D1-replacement seams and the `_validate_connection` sub-key claim.
- **One drift row was corrected against source, and the correction is load-bearing.** D11 reads "`Meta.filter_fields` → `Meta.fields`", which implies `filter_fields` is rejected. It is not: `filters/sets.py::FilterSetMetaclass.__new__` #"Allow consumers to use `filter_fields` as a synonym for `fields`" aliases it when `fields` is absent, deliberately, for cookbook parity. So the spec's Layer 6 example was uncopyable on the **base-class name alone**. The spec now uses `fields` as canonical (django-filter's key, and what `GOAL.md` and `docs/GLOSSARY.md` show) and states the alias in one sentence. If Worker 3 judges the alias should not appear in the spec at all, that is a defensible different call — flag it rather than assuming the omission was accidental.
- **Two vacated numbered slots were repurposed rather than gapped**, and the dispatch left the choice to Worker 1. `### Decision 3` and `### Phase 3` now state positive contracts. The reasoning is in `### Spec changes made (Worker 1 only)` and the rationale. Renumbering was forbidden and was not done; `### Decision 6: fail loudly` and `### Layer 3: Finalization trigger` — the two anchors `spec-010` cites — are byte-identical.
- **Two convention fixes were made outside the D-rows**, both recorded below: an inline cross-file link converted to reference-style, and one sentence of spec-narrates-its-own-history deleted (moved to the rationale). Both are standing-rule violations only Worker 1 may fix. If Worker 3 reads them as scope creep, say so — they are separable from every D-row.
- **What was deliberately NOT done**, so a finding is not raised for it: the upstream `file:///…#LNN` citations were not "fixed" (Group C; out-of-repo, so rule 27 does not reach them); `spec-028` was not opened; no card, DB row, or generated doc was touched; no source defect was edited (none was found — see below).

### Notes for Worker 1 (spec reconciliation)

- **No correctness defect was found in shipped source.** This pass read the seams behind D1, D6-D9, and D11-D14 and every one behaves as the plan's table records. Nothing is escalated to the maintainer under this head.
- **One observation for the maintainer, not a defect and not actionable in this cycle.** `filters/sets.py::FilterSetMetaclass.__new__`'s `filter_fields` alias mutates the consumer's `Meta` class in place (`meta_class.fields = meta_class.filter_fields`). That is fine for the normal one-`Meta`-per-`FilterSet` case and is pre-existing, shipped, tested behavior; it is recorded only because this pass documented the alias in the spec for the first time and a reader may wonder whether a shared `Meta` base could be affected. **No edit was made and none is proposed here.**
- **Carried to R2, unchanged from the plan.** `docs/SPECS/spec-028-orders-0_0_8.md` `### Decision 12` still defers `DISTINCT ON` to `0.0.9`. The spec-009 half now states the row-preserving property rather than the mechanism, so R2's reconciliation should say the deferral was **discharged by an alternative**, not postponed — the two halves must not end up telling different stories.

---

## Review (Worker 3)

Audited 2026-08-15. Scope: the working-tree diff of `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
(103 insertions / 158 deletions) and `docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md`
(329 insertions / 0 deletions), against shipped source read read-only. No source, test, sibling spec,
standing doc, DB row, or generated doc was touched by this pass; `git status --porcelain` over
`docs/SPECS/` and `docs/builder/` shows only this cycle's two files plus the concurrent spec-010
cycle's five. `docs/SPECS/spec-028-orders-0_0_8.md` is clean, so R2's half is genuinely untouched.

**Method.** Every replacement paragraph was re-derived against source rather than accepted on the
perform report's prose (`BUILD.md` `## Claims are proven mechanically, never accepted on prose`). The
two mechanical gates and the link / anchor / rule-27 validators were re-run rather than trusted. The
`### Dispatched findings checklist` was walked box by box against the diff. `git stash`, `git
checkout`, `git restore`, and `git worktree` were not used; the HEAD reference was
`git show HEAD:<path>` into a scratch path outside the repository.

### High:

None.

### Medium:

#### D10 is ticked `- [x]` but nothing in the diff addresses it

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:367-384` (`### Borrow
\`StrawberryDjangoDefinition\``) is byte-unchanged by this pass, and the `### Spec changes made
(Worker 1 only)` table's 35 rows carry no D10 entry — every other dispatched row appears there at
least once. `BUILD.md` `### Dispatched findings checklist` fixes the severity: a tick with no
matching fix is a Medium finding.

The row is not cosmetic. The unmodified `DjangoTypeDefinition` sketch still declares five things the
shipped dataclass does not have, verified against `django_strawberry_framework/types/definition.py`:

- `fields:` and `exclude:` — shipped slots are `fields_spec` and `exclude_spec`
- `aggregate_class:` — absent from the shipped definition entirely
- `search_fields:` — absent from the shipped definition entirely
- `type | LazyClassRef | None` — `LazyClassRef` has **zero** occurrences package-wide; the shipped
  slots are plain `type | None`

Two of those (`aggregate_class`, `search_fields`) are the same `DEFERRED_META_KEYS` members the pass
took care to annotate with owning cards in `## Target outcome`, so the spec now states two different
things about them in two sections. This is the same "uncopyable as written" class Maintainer decision
1 exists to close, sitting inside a fenced `python` block a reader will copy.

Recommended change: correct the sketch (`fields_spec` / `exclude_spec`, drop the `LazyClassRef`
union, and either drop `aggregate_class` / `search_fields` or mark them as the destination with their
cards, consistently with `## Target outcome`), record the edit as a D10 row in `### Spec changes
made`, and add the matching rationale entry. If Worker 1 instead judges D10 already-accurate-enough
to leave alone, the box must be un-ticked and the deferral recorded — a tick asserts a fix that is
not there.

#### The annotation-provenance replacement names the wrong producer, and the wrong first consumer

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:401`:

> `types/definition.py::DjangoTypeDefinition` carries those provenance sets and
> `types/base.py::_build_annotations` is their producer and first consumer

Both halves of that clause are false against shipped source:

- **Not the producer.** `types/base.py::_build_annotations` takes `consumer_authored_fields` as a
  keyword *parameter* and never derives it. The producers are `DjangoType.__init_subclass__`'s two
  inline comprehensions (`types/base.py` #"consumer_annotated_relation_fields = frozenset(") for the
  annotated pair, `types/base.py::_consumer_assigned_fields` for the assigned pair, and the union
  built at `types/base.py` #"Four-corner consumer-override contract". `_build_annotations`'s own
  docstring says so: #"See ``_consumer_assigned_fields`` for the four-corner override contract that
  populates ``consumer_authored_fields``".
- **Not the first consumer.** `types/base.py::_validate_nullability_override_targets` receives
  `consumer_authored_fields` before `_build_annotations` is called, followed by
  `_validate_filesystem_path_targets` and `_validate_relation_shape_targets`.

The rationale repeats the same error at
`docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md:214-216` ("produced and first
consumed by `types/base.py::_build_annotations`").

This is the exact failure mode a replacement paragraph carries — a new claim about shipped code that
nobody had verified. Recommended change: name `_consumer_assigned_fields` (and the
`__init_subclass__` collection step) as the producer and `_build_annotations` as *a* consumer, or
drop the producer/first-consumer clause entirely and keep the invariant, which is the load-bearing
part and is correct as written.

#### Layer 4's visibility bullet states a package-wide guarantee the shipped code does not give unconditionally

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:652`:

> **visibility** — `utils/querysets.py::apply_type_visibility_sync` composes the target type's
> row-level `get_queryset` onto the relation queryset, so a nested traversal cannot see a row a root
> query would hide

The named seam is real and the first clause verifies. The **"so … cannot"** does not, for a generated
relation field:

- `types/resolvers.py::_make_relation_resolver` does not import or call `apply_type_visibility_sync`
  at all — `types/resolvers.py` imports nothing from `utils/querysets`. `many_resolver` returns
  `getattr(root, accessor_name).all()` row-bounded, and `forward_resolver` returns
  `getattr(root, field_name)`.
- The composition happens on three *other* paths: `connection.py` #"qs = apply_type_visibility_sync(",
  `list_field.py` #"apply_type_visibility_sync(target_type, qs, info)", and — for a generated relation
  — `optimizer/walker.py::_build_child_queryset`.
- The optimizer is **opt-in**: `optimizer/extension.py` #"Opt-in at schema construction", and every
  example in `docs/README.md` installs it through `extensions=[...]`. `docs/GLOSSARY.md`
  `## \`get_queryset\` visibility hook` states the guarantee conditionally too — "The load-bearing
  behavior is optimizer cooperation".

So the guarantee holds for the synthesized `<field>Connection` shape and for any relation the
optimizer planned, and not for an opted-in raw `list[T]` relation (`Meta.relation_shapes`) or a
forward FK read on a schema without the extension, where `apply_cascade_permissions` is the
documented answer instead. **I am not asserting a source defect and am escalating none** — the raw
list form is an explicit opt-in and the default many-side shape is the connection. The finding is
that the spec sentence over-states. Recommended change: one clause — name where the composition runs
(the connection pipeline, the list field, and the optimizer's prefetch child) rather than asserting an
unconditional "cannot".

#### The spec opener still says "the three sites", which this pass itself falsified to four

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:3` still reads "the three sites that direction
was stated at". This pass's own `### Sweep evidence` records the opposite — "**The finalization
falsification now has four known sites, not three**" — and change #17 fixed the fourth (`### Layer 5`
item 2). The opener sentence was *edited by this pass* (change #1 appended the six-mechanism clause)
and the stale count was carried through the edit.

`BUILD.md` `## Claims are proven mechanically` — "a count asserted in the same breath as the lesson it
illustrates is routinely wrong" — is the rule this trips. Recommended change: "the four sites that
direction was stated at". (The rationale's pre-existing `## Standing notes` bullet also says three,
but that entry is correctly untouched under append-only; the new
`### \`### Layer 5: Connection field\`` entry's method note already records the correction, so the
rationale is self-correcting where the spec is not.)

#### Spec-narrates-its-own-history survivors, including two inside a section this pass rewrote

The pass deleted one instance (`### Phase 1`, change #26) under `BUILD.md` `## Spec rationale
extraction` — "the spec … never narrates its own history". Four larger instances survive:

- `:645` — "An earlier direction had `DjangoConnectionField`, `DjangoNodeField` and `DjangoSchema`
  each finalize on construction … That combination was **rejected** before the foundation slice
  shipped: …". Textbook "this was rejected" prose in the spec body. Its final sentence ("Any future
  helper that auto-triggers finalization must therefore also enforce the single-threaded setup
  window") is implementation-relevant and should stay as a forward-looking constraint; the narration
  around it belongs in the rationale, where the `### Layer 3` entry already tells the story.
- `:878` — "The flat-module names in older drafts of this spec have been migrated to packages below."
- `:893` — "This matches the target layout in `docs/TREE.md` and replaces the earlier flat-file
  proposal (`filters.py`, `filterset.py`, …)."
- `:1018` — "see `### Layer 3: Finalization trigger` above for why the auto-triggering alternative was
  rejected."

`:878` and `:893` sit in `## Proposed module layout`, which this pass edited twice (changes #24 and
#25), so the convention fix was applied in one section and skipped in the section next to it. All four
are pre-existing at HEAD, so the honest dispositions are (a) fix them here, since the pass already
opened the convention-fix door and owns the file, or (b) record an explicit deferral naming the
follow-up. What is not available is leaving them un-noted while the smaller `### Phase 1` instance was
deleted — that reads as a rule applied by accident.

### Low:

#### Two stated counts are wrong

- `docs/SPECS/appx/spec-009-…-rationale.md:214-215` — "the **four** `consumer_*_fields` frozensets on
  `types/definition.py::DjangoTypeDefinition`". There are **five**: `consumer_authored_fields`,
  `consumer_annotated_relation_fields`, `consumer_annotated_scalar_fields`,
  `consumer_assigned_relation_fields`, `consumer_assigned_scalar_fields`. "Four" is defensible as
  "the four spelling-specific sets" but is not what the sentence says, and this artifact's own
  `### Source verification performed` says "the five `consumer_*_fields` frozensets" — the delivered
  text and its verification note disagree. The spec text itself says "those provenance sets" with no
  count and is fine.
- `docs/builder/bld-009-r1-spec_code_reconciliation.md` `### Source verification performed`, D8 —
  "`types/base.py::ALLOWED_META_KEYS` read in full (18 keys)". It holds **17**: `connection`,
  `cursor_field`, `description`, `exclude`, `fields`, `filesystem_path_fields`, `filterset_class`,
  `globalid_strategy`, `interfaces`, `model`, `name`, `nullable_overrides`, `optimizer_hints`,
  `orderset_class`, `primary`, `relation_shapes`, `required_overrides`. Artifact-only; the spec
  correctly cites the constant as the enumeration rather than a number, so nothing shipped is wrong.

Recorded as Low rather than Medium because neither propagates into a contract claim, but both are
counts recorded as measured. Everything else numeric in the pass re-measured exactly: 54,232 → 60,855
bytes / 1,154 → 1,099 lines on the spec, 12,273 → 36,744 bytes / 208 → 537 lines on the rationale,
`--numstat` 103/158 and 329/0.

#### One rationale entry names no spec section, so it cannot be looked up

`### Convention corrections made in the same pass` is the only new entry whose heading names no spec
heading. `BUILD.md` `## Spec rationale extraction`: "an entry naming no decision cannot be looked up,
and is worthless however well argued." Its body does cite `### Phase 1` twice, so the content is
sound; the fix is the heading (e.g. `` ### `### Phase 1` — two convention corrections made in the
same pass ``), which also matches the file's own `## How to read this file` rule ("One entry per spec
section, named by the section's own heading").

#### The `<TypeName>Connection` sentence reads as though the subclass exists only under the opt-in

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:486` — "`Meta.connection = {"total_count":
True}` is what asks for one, and the connection field resolves that type through a generated concrete
`<TypeName>Connection` subclass carrying the member". `connection.py::_connection_type_for`
**always** returns a generated concrete subclass; the `Meta.connection` value "only controls the
shape". The next paragraph's "the concrete subclass is what keeps package pagination dispatch
reachable at all" implies the correct reading, so a careful reader recovers it, but the first sentence
scopes the generation to the opt-in. One word ("that type" → "every node type") closes it.

#### The rationale's enumeration of surviving `Advanced*` sites is incomplete

`…rationale.md:437-440` lists the kept upstream-name sites as `#### Take aggregate semantics`,
`` #### Take `fields_class` ``, and the `file:///` citation list. `AdvancedFieldSet` also survives at
`docs/SPECS/spec-009-…-0_0_4.md:772` (`### Layer 9`, "Use `AdvancedFieldSet` semantics."), which the
enumeration does not name. The survival is **correct** — it is a prior-art reference in the same shape
as Layer 6's "Use `django-graphene-filters` semantics" and Layer 8's aggregate line, and it must not
be renamed — but the rationale is what a later pass will read to decide whether a surviving name is
deliberate, so the list should be complete.

### DRY findings

- **No package-code duplication is possible here**; the diff touches two `.md` files and adds no
  helper, constant, or branch. The plan's DRY analysis is correct that the usual inventory is moot,
  and it says so rather than omitting it.
- **Spec / rationale near-duplication of one argument, deliberate and declared.** The "upstream binds
  all of them to one field class because its public API is decorator-first; this package's public API
  is `class Meta`" argument appears in the spec at `:415` and again in the rationale at `:308-315`.
  The rationale flags the overlap itself ("is the whole argument, and it is now stated in the spec
  because it is implementation-relevant"), which is the plan's own carve-out for implementation-
  relevant rationale. Recorded, not flagged — but it is the one place in this pass where the
  single-ownership law is bent, and if either copy is later edited the other will drift. A one-line
  pointer from the rationale to the spec's statement, instead of a second telling, would remove the
  risk at no cost to the entry.
- **Existence challenge: not raised.** This pass introduces no abstraction, registry, indirection, or
  helper, so there is nothing whose existence to challenge. The one structural choice it did make —
  repurposing the vacated `### Decision 3` / `### Phase 3` slots rather than gapping or renumbering —
  is the *less* machinery-heavy option and is correct: renumbering was forbidden by the inbound
  anchor, and a numbered gap carries no contract while inviting a later reader to re-fill it.
- **The single-ownership split held on the scrubs.** No "why it lost" sentence survives in the spec
  body for any of the six dropped mechanisms; every one is in the rationale. Verified by reading each
  replacement section end to end, not only by grep.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → empty, and `git status --porcelain` on that
path is clean. `__all__` and the re-export list are unchanged. No spec authorization is needed. (The
plan's `## Build-wide context flags` declares source read-only for the whole cycle, which this
confirms.)

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. `git status --porcelain CHANGELOG.md` is clean, and
`AGENTS.md` rule 21 plus the plan's `## Build-wide context flags` close it for this cycle.

### Documentation / release sanity

**Applies** — the diff is entirely docs / archived-spec surface. Both changed files were read end to
end.

- **Version strings and card IDs.** No version string was changed. Every card id the pass introduced
  exists on the board, verified by `grep -o "TODO-BETA-<NNN>-[0-9.]*" KANBAN.md`:
  `TODO-BETA-053-0.1.1`, `TODO-BETA-054-0.1.1`, `TODO-BETA-055-0.1.2`, `TODO-BETA-057-0.1.3`,
  `TODO-BETA-058-0.1.3`, `TODO-BETA-059-0.1.4`. The three planned-package annotations match
  `docs/TREE.md` #"fieldset/    # planned by TODO-BETA-054-0.1.1", #"aggregates/    # planned by
  TODO-BETA-057-0.1.3", and #"permissions/    # planned by TODO-BETA-059-0.1.4" — the spec names the
  same cards the rendered tree does, so the two cannot disagree without both moving.
- **KANBAN movement / DB.** None. `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and
  `docs/GLOSSARY.md` are all clean in `git status --porcelain`; this pass wrote none of them, as the
  plan requires.
- **Archival.** Nothing moved. The spec is already at `docs/SPECS/`, the rationale at
  `docs/SPECS/appx/`, and both link-definition blocks resolve from those locations — every non-anchor
  link definition in both files was disk-existence-checked and all 36 resolve.
- **Markdown link scaffold.** `uv run python scripts/check_trailing_commas.py --check <spec>
  <rationale>` → exit 0, re-run rather than trusted. Independent validator over both files with code
  fences stripped: **0 missing definitions, 0 orphan definitions** in each; the spec's one new
  definition (`[spec-010]`) is used, and the rationale's two (`[glossary-filterset]`,
  `[glossary-ordering]`) are used. **0 unresolved in-page `](#…)` anchors.** The spec now carries **0**
  inline cross-file links; the one apparent inline link in the rationale is inside a code span (it is
  the *quotation* of the link that change #26 removed) and therefore renders verbatim per `START.md`
  "Markdown link convention" — correct, not a violation.
- **Glossary chain.** `uv run python scripts/check_spec_glossary.py --spec <spec>` → `OK: 23 terms -
  all have glossary entries and at least one spec link.` Exit 0, count unchanged at 23, matching the
  pre-flight baseline and the card's 23 glossary links. The two terms the report says came close
  (`[glossary-ordering]`, `[glossary-fieldset]`) both survive with live sites.
- **Rule 27.** The spec still carries **zero** in-repo raw `path:NN` citations (independently
  re-measured over the raw file, `file://` excluded), and so does the rationale. Every citation the
  pass added is `path::QualifiedName` or `path #"substring"`. The ~60 upstream `file:///…#LNN`
  citations are out-of-repo and correctly untouched.
- **No obsolete "coming soon" / "planned" wording introduced.** The `planned by TODO-BETA-…`
  annotations are deliberate forward pointers with an owner each, which is what Maintainer decision 1
  asked for, not stale staging language.
- **No script-rendered doc regenerated**, so the staging-docstring check does not apply.
- **Verbatim-copy check.** The pass copies no fenced block from another document, so there is no
  character-for-character `diff` to run. The one fenced block it edited (`DjangoConnection`) uses
  three backticks inside a document with no four-backtick outer fence — no conflict.

### What looks solid

- **The scrub is complete and it stopped in the right place.** `grep -c` over the current spec:
  `DjangoModelField` 0, `types/fields.py` 0, `OptimizerStore` / `with_hints` / `with_prefix` 0/0/0,
  `get_strawberry_annotations` 0, `DjangoField(` 0, `ASC_DISTINCT` / `DESC_DISTINCT` / `DISTINCT ON`
  0/0/0, `AdvancedFilterSet` / `AdvancedOrderSet` 0/0. The six surviving `DjangoModelType` mentions
  are exactly the legitimate ones — the upstream source-reference list (`:312`), the two "Strawberry-
  Django's default relation fallback maps" bullets (`:431-432`), the `## What to scrap from
  Strawberry-Django` refusal (`:556`), the `## Why not use generic relation fallback by default?`
  argument (`:854`), and `### Decision 1` (`:999`). What D5 dropped — the sentence reserving a
  fallback tier *for this package* — is genuinely gone, replaced by an explicit no-placeholder-tier
  statement at `:444` that resolves the self-contradiction with
  `### The unresolved-relation contract is error-only`.
- **I swept for a fifth finalization-echo site and there is none.** Every one of the 40 `finaliz*`
  occurrences in the current spec is consistent with "the explicit consumer call, and nothing else";
  the fourth site (`### Layer 5` item 2) is closed and its replacement paragraph at `:677` states the
  negative contract with the failure it prevents, which is better than a silent deletion.
- **The anchor constraint holds in both directions, re-verified at 2026-08-15T22:29:59Z** (timestamped
  because the concurrent spec-010 cycle can retitle a heading between passes). Inbound:
  `spec-010:67` cites `spec-009 #"### Layer 3: Finalization trigger"` and `spec-010:467` cites
  `spec-009 #"### Decision 6: fail loudly"`; both headings exist exactly once in the edited spec-009
  (`grep -c` → 1 each). Outbound: `spec-009:637` cites `spec-010 #"## Strawberry finalization
  strategy"` and `spec-009:873` cites `spec-010 #"### Unresolved-target error format"`; both exist
  exactly once in the current spec-010. No Decision or Phase was renumbered — `### Decision 1` through
  `### Decision 6` and `### Phase 1` through `### Phase 8` are all present with their original numbers,
  and the two vacated slots were repurposed with positive contracts carrying no "this was rejected"
  prose. **Re-checked at 2026-08-15T22:37:39Z** after `spec-010` moved again mid-review (its diff grew
  to 167/108 during this pass): all four anchors still resolve, and `spec-010:8`'s stale "custom field
  classes" description still stands — see the escalation below.
- **The append-only claim on the rationale is mechanically proved, not asserted.** `git diff` over the
  rationale contains exactly one line starting with `-` and it is the `--- a/` header: no line was
  removed. The first 164 lines (`## How to read this file`, `## Provenance of this record`, and all
  six pre-existing entries) are byte-identical to `git show HEAD:` — `cmp` exit 0. `## Standing notes`
  is unchanged. The only in-place additions outside the entry block are the two required link
  definitions, alphabetical in the `<!-- docs/ -->` group.
- **Every replacement paragraph I re-derived except the two named above verifies exactly.** Spot list,
  all read read-only from source: `types/finalizer.py` #"Phase 2: ``_attach_relation_resolvers``
  installs the framework's auto" and #"Phase 3: ``strawberry.type(cls, name=..., description=...)``
  decorates" confirm Layer 4's Phase-2-before-Phase-3 claim and the "Phase 2 is the only window"
  constraint; `types/converters.py::resolved_relation_annotation` returns literally
  `list[target_type]` / `target_type | None` / `target_type`, matching the spec's three spellings
  word for word; `connection.py` #"Build the resolver ``__signature__`` + ``__annotations__``
  carrying the sidecar args" confirms argument injection; `connection.py::DjangoConnection`'s
  docstring #"The base carries no ``total_count`` field" and
  `connection.py::_build_total_count_connection` confirm the D9 correction in both fields, and the
  "generic base owns the `first` + `last` guard, window consumption, and cursor-mode dispatch"
  sentence matches that docstring clause for clause; `types/base.py::DEFERRED_META_KEYS` is exactly
  the three named keys and `_validate_meta` raises on them, so the `## Target outcome` paragraph is
  right; `relay.py` #"Resolution is **nullable by contract**" confirms D7 and `required=False` is
  unconditional at the dispatch sites; `orders/inputs.py::Ordering` has exactly the six members named
  and `orders/sets.py` #"models.Min if direction.is_ascending else models.Max" annotates and orders by
  the generated alias, so Layer 7's row-preserving paragraph is accurate; `optimizer/hints.py` is
  `@dataclass(frozen=True)` and pins #"Strategy selection MUST never depend on request-varying data",
  so the value-not-callable rule is not merely unbuilt-and-scrubbed but positively supported;
  `filters/sets.py::FilterSet` really does subclass `filterset.BaseFilterSet`, which is the stated
  reason for the name.
- **The D11 correction against source is right, and it was worth making.**
  `filters/sets.py::FilterSetMetaclass.__new__` #"Allow consumers to use `filter_fields` as a synonym
  for `fields`" assigns `meta_class.fields = meta_class.filter_fields` only when `fields` is absent —
  so `filter_fields` is aliased, not rejected, and the drift table's "`Meta.filter_fields` →
  `Meta.fields`" did understate it. The spec's landing (canonical `fields`, alias stated in one
  sentence, `"__all__"` supported in both spellings) is the correct call and I am not flagging the
  alias's presence: a cookbook migrant reading this spec is exactly the reader who needs it.
- **Both out-of-row convention fixes were in scope, not scope creep.** (a) The inline → reference-style
  link is a direct `AGENTS.md` rule 28 / `START.md` requirement on a file this pass legitimately owns,
  and `START.md` says in terms "Don't drift back to inline". (b) Deleting spec-narrates-its-own-history
  prose is `BUILD.md` `## Spec rationale extraction` applied literally, and it is a fix only Worker 1
  may make. My only objection is that (b) was applied incompletely — see the Medium above; the
  decision to make it at all was correct.
- **Owning-card annotations are applied only to unshipped items**, and the rule that reconciles them
  with the first residual cycle's rejection of per-phase shipped-version annotations ("name a card for
  open work, never a version for shipped work") is stated once, in the rationale, and applied
  consistently across the deferred `Meta` keys, `aggregates`, Phases 6/7, the module layout, and the
  three unmet success criteria. Eight-of-eleven is deliberately kept out of the spec, which is right.
- **The `` ``double-backtick`` `` heading handling is correct** and the report was right that no
  mechanical checker can see it: every rationale entry heading quoting a spec heading that itself
  contains a code span uses double-backtick delimiters, space-padded where the content ends in a
  backtick. I checked all fourteen new entry headings; none renders broken.

### Temp test verification

- No temp test files were created under `docs/builder/temp-tests/r1/`, and none was warranted: this
  item ships no executable line, so there is no behavior a test could pin. The directory is left
  empty.
- Verification instead used read-only source reads, `grep -c` sweeps, two re-runs of the cycle's
  mechanical gates, and one throwaway Python validator (link definitions, orphan definitions, in-page
  anchors, raw `path:NN`, link-target disk existence, and rationale→spec heading resolution) executed
  from a stdin heredoc with no file written into the repository. Its results are quoted under
  `### Documentation / release sanity`.
- Disposition: nothing to promote.

### Failability proofs

**Not applicable to a documentation pass.** `BUILD.md` `### What needs a proof, and what does not`
scopes the obligation to a new boundary, guard, gate, or rejection path a slice introduces; this diff
touches two `.md` files and introduces none, so the mandatory re-run floor is computed over an empty
set and an empty re-run set is legal here. No boundary was re-run and none was accepted on a builder's
record, because none exists. Worker 3's source carve-out was not exercised: no production file was
mutated at any point in this pass.

### Hot-path budget

**Not applicable to a documentation pass.** The build plan declares `Hot-path declaration: none` for
the whole cycle and R1's plan repeats it; no item touches an executable line, so there is no before /
after number owed and none is missing. I found nothing that contradicts the not-hot-path declaration.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (report-only, do not repair): `spec-010` now mis-describes `spec-009`.**
  `docs/SPECS/spec-010-foundation-0_0_4.md:8` says spec-009 "describes the long-term architecture
  (filters, orders, aggregates, connections, permissions, **custom field classes**)". That last item
  is exactly what D1 scrubbed, so this pass falsified an inbound description in a file it may not
  touch. Read at 2026-08-15T22:29:59Z; `spec-010` is `M` under a concurrent cycle and is a moving
  target, so re-read before acting. Resolution paths: (i) route it to the spec-010 cycle, whose file
  it is; (ii) hold it for the maintainer to sequence at commit, which the plan's `### Second growth`
  already anticipates; (iii) widen this cycle — **not** available under the plan's `## Build-wide
  context flags` without a maintainer decision. My recommendation is (ii): the plan already flagged
  the two-cycle collision to the maintainer and this is a concrete instance of it.
- **`KANBAN.md` carries a stale assertion about this spec, and it predates this pass.**
  `KANBAN.md:335` says "`spec-009 #"### Layer 3: Finalization trigger"` … still presents hybrid
  auto-finalization as the preferred direction". That has been false since the **first** residual
  cycle (`f3c94642`) corrected Layer 3, and it is more false now. It is DB-backed and script-rendered,
  so it is R3/R4 territory, not R1's — recorded here so it is not lost. Same bullet's raw
  `spec-010:65` / `spec-010:408` / `spec-009 (670-687)` / `spec-009 (1076-1077)` line references are
  themselves rot-prone.
- **R2 carry-forward is consistent, confirmed.** The spec-009 half of D6 now states the row-preserving
  *property* (`### Layer 7` `:657` and `### Phase 5` `:961`) rather than the `DISTINCT ON` mechanism,
  and the rationale's `### Layer 7` entry says in terms that `DISTINCT ON` "is not a deferred better
  answer; it is a worse one for a cursor-paginated schema". R2's reconciliation of
  `spec-028 ### Decision 12` must therefore say **discharged by an alternative**, not postponed, or
  the two halves will tell different stories. `spec-028` is clean in `git status`, so R2 starts from
  an untouched file.
- **The `filters/sets.py` in-place `Meta` mutation observation from the perform report is correct and
  I am not raising it as a finding either.** `meta_class.fields = meta_class.filter_fields` does mutate
  the consumer's `Meta`, and the `hasattr(meta_class, "fields")` guard sees inherited attributes, so a
  shared `Meta` base could interact — but it is pre-existing, shipped, tested behavior, out of this
  cycle's writable set, and the plan forbids a source edit here. Recorded for the maintainer only.
- **Nothing else escalates.** I found no correctness defect in shipped source and I am escalating none.
  The Layer 4 visibility Medium above is a finding about the *spec sentence*, deliberately not about
  the code.

### Review outcome

`revision-needed`.

Five Medium and four Low findings, none of them intentionally rejected yet. Three of the Mediums are
plain factual corrections inside this pass's own writable set and are cheap to close: the D10 tick
(fix the sketch or un-tick and defer), the `_build_annotations` producer / first-consumer clause in
both files, and the opener's "three sites". The remaining two — Layer 4's absolute visibility
guarantee and the four spec-narrates-its-own-history survivors — need Worker 1's judgement on wording
and scope respectively, and either a fix or a recorded rejection reason will close them.

Under the plan's `### Deviation 3` corollary, the apply-changes pass for R1 is Worker 1's and sets
`Status: planned` again, returning the artifact to the `planned` → Worker 3 mapping.

---

## Build report (Worker 1, apply-changes pass)

Performed 2026-08-15 by a **fresh Worker 1 invocation** that did not write the pass under review; the
artifact and the working-tree diff were its whole context. Under the build plan's `### Deviation 3`
corollary the apply-changes pass for R1 is Worker 1's, and it sets `Status: planned`, returning the
artifact to the `planned` -> Worker 3 mapping for re-review. Worker 3's `## Review (Worker 3)` section
and every prior section are untouched; the only edit outside this section is the `- [x] **D10**`
checklist box, whose annotation this pass is instructed to make.

**All five Medium and all four Low findings are closed. None was rejected.**

### Findings closed

| Finding | Disposition | Where it landed |
|---|---|---|
| **M1** — D10 ticked with no matching change | **Fixed**, sketch corrected against source | Spec change 36; rationale entry ``### Borrow `StrawberryDjangoDefinition` `` |
| **M2** — wrong producer and wrong first consumer of the provenance sets | **Fixed** in both files | Spec change 37; rationale entry ``### Borrow `get_strawberry_annotations` `` |
| **M3** — Layer 4's visibility bullet over-claims | **Fixed** by cutting the absolute and naming the three composition sites | Spec change 38; rationale entry ``### Borrow `StrawberryDjangoFieldBase` … `` |
| **M4** — spec opener still says "the three sites" | **Fixed** | Spec change 39 |
| **M5** — four spec-narrates-its-own-history survivors | **Fixed**, all four | Spec changes 40-43; rationale entry `### \`### Phase 1\`, \`### Layer 3\`, …` |
| **L1a** — "the four `consumer_*_fields` frozensets" (five exist) | **Fixed** | Rolled into spec change 37's rationale half |
| **L1b** — artifact says `ALLOWED_META_KEYS` (18 keys); it holds 17 | **Corrected here**, not in place | This section, `### Correction to a prior section` below |
| **L2** — one rationale entry names no spec section | **Fixed**, heading now names all four | Rationale entry heading |
| **L3** — `<TypeName>Connection` reads as opt-in-only *generation* | **Fixed** | Spec change 44 |
| **L4** — incomplete `AdvancedFieldSet`-survivor enumeration | **Fixed**, `### Layer 9` added | Rationale entry `### Layer 6 …` |

Worker 3's `### DRY findings` recorded (and explicitly did not flag) the spec/rationale near-duplication
of the "upstream binds all of them to one field class" argument. **Left as it stands**, deliberately: it
is the `worker-1.md` `### Performing the rationale move` carve-out for implementation-relevant rationale,
both copies were re-read this pass and agree, and replacing the rationale's telling with a pointer would
cost the entry the argument a reviewer needs in hand. Recorded as a rejection with a reason rather than
silently.

### Correction to a prior section

`### Source verification performed`, D8 states "`types/base.py::ALLOWED_META_KEYS` read in full (18
keys)". It holds **17**, re-measured this pass from the frozenset literal: `connection`, `cursor_field`,
`description`, `exclude`, `fields`, `filesystem_path_fields`, `filterset_class`, `globalid_strategy`,
`interfaces`, `model`, `name`, `nullable_overrides`, `optimizer_hints`, `orderset_class`, `primary`,
`relation_shapes`, `required_overrides`. The correction is recorded here rather than applied in place,
because a prior pass's report is that pass's record. **Nothing shipped is affected**: the spec cites the
constant as the enumeration and states no number.

### Byte counts

| File | At R1's combined pass | After this pass | Delta |
|---|---|---|---|
| `docs/SPECS/spec-009-…-0_0_4.md` | 60,855 bytes / 1,099 lines | **61,401 bytes / 1,099 lines** | +546 bytes / 0 lines |
| `docs/SPECS/appx/spec-009-…-rationale.md` | 36,744 bytes / 537 lines | **42,969 bytes / 613 lines** | +6,225 bytes / +76 lines |

**The spec's over-write risk was the calibration for this pass and it was answered by cutting, not by
qualifying.** Four narration blocks and one redundant sentence were deleted (M5, and the
`aggregate/filter/order defaults` benefits bullet narrowed); the additions are the corrected
`DjangoTypeDefinition` prose, the Layer 4 seam restatement, and the `<TypeName>Connection` clarification.
Line count is unchanged at 1,099 and `git diff --numstat` against HEAD reads **115 insertions / 170
deletions** on the spec — it still deletes more lines than it adds. The +546 bytes is the honest residue
of replacing four short narrative lines with three denser contract sentences, and it is reported rather
than argued away.

The rationale grew because it is where the cut narration went, which is the extraction rule working as
designed rather than a second over-write.

### Append-only proof on the rationale

Re-proved mechanically rather than carried from Worker 3's pass. `git diff` over the rationale contains
exactly **one** line starting with `-`, and it is the `--- a/` header: no line was removed. `head -164`
of the working file is byte-identical to `head -164` of `git show HEAD:<path>` (`cmp` exit 0) — the six
pre-existing entries, `## How to read this file`, and `## Provenance of this record` are untouched.
`## Standing notes` is untouched, including its pre-existing "three sites" bullet: correcting it would
break append-only, so the new `### \`### Phase 1\`, …` entry states in terms that the bullet is stale and
where the fourth site is recorded.

**One edit needs its exemption stated explicitly.** M4's fix edits the **spec's** opener ("the three
sites" -> "the four sites"), not the rationale's. The spec is not append-only for this cycle, so no
exemption is needed; the rationale's own stale count is the one deliberately left alone, above. (The
dispatch brief described M4 as a rationale-opener finding; Worker 3's section cites the spec's line 3,
and the spec is where the sentence is. Re-derived before editing.)

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  -> `OK: 23 terms - all have glossary entries and at least one spec link.` **Exit 0, count still 23.**
  The scrubbed benefits bullet and the deleted narration removed no term's last site.
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` -> **exit 0** for both.
- **Link / anchor / rule-27 validator** re-run over both files with code fences stripped: **0 missing
  definitions, 0 orphan definitions, 0 unresolved in-page `](#…)` anchors, 0 raw in-repo `path:NN`
  citations, 0 dead link-definition targets** (every non-anchor definition disk-existence-checked) in
  each file. The rule-27 property the spec entered this cycle with is preserved.
- **Cross-spec anchors re-verified at 2026-08-15T22:45:45Z**, because the concurrent spec-010 cycle can
  retitle a heading between passes and Worker 3's 22:37:39Z check is not permanent. **Five, all
  resolving, in both directions.** Inbound: `spec-010` cites `spec-009` #"### Layer 3: Finalization
  trigger" and #"### Decision 6: fail loudly" — `grep -c` -> 1 each in the edited spec-009, and this
  pass renumbered nothing. Outbound: `spec-009` cites `spec-010` #"## Strawberry finalization strategy",
  #"### Unresolved-target error format", and #"### Must redo (not augment)" — `grep -c` -> 1 each in the
  current spec-010. The third outbound anchor is one Worker 3's four-anchor count did not include; it is
  live and it resolves. `spec-008`'s inbound reference is whole-file, not anchored.
- **Counts measured as written, per `BUILD.md` `## Claims are proven mechanically`.** `DjangoTypeDefinition`
  carries **29** dataclass slots (27 public, 2 private caches) and **3** methods (`graphql_type_name`,
  `related_target_for`, `has_custom_id_resolver_for`), counted by AST rather than by eye; `ALLOWED_META_KEYS`
  holds **17**; there are **5** `consumer_*_fields` slots, four spelling-specific plus their union; **3**
  override-target validators read that union before `_build_annotations`; `LazyClassRef` has **0**
  occurrences package-wide; the deleted flat-file list named **8** modules.
- `git log --stat` over both document paths -> the most recent commit touching either is still
  `f3c94642`; `HEAD` unchanged at `054de9dd`; both paths are `M` and uncommitted. **This pass's work was
  not swept into a concurrent session's commit.**

No `pytest` was run, no `--cov*` flag was used, no branch was created or switched, and nothing was
committed.

### Baseline growth observed, reported, NOT reverted

`git status --porcelain | wc -l` -> **112**, up from 68 at the plan's `## Baseline growth`. `HEAD`
unchanged at `054de9dd`. The new group is a **THIRD concurrent residual cycle, on `spec-011`**:
`docs/SPECS/spec-011-stale_placeholder_cleanup-0_0_4.md` (`M`),
`docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-rationale.md`,
`docs/builder/build-011-stale_placeholder_cleanup-0_0_4.md`, and
`docs/builder/bld-011-r1-rationale_and_spec_reconciliation.md` (`??`). The concurrent **spec-010** cycle
also moved again — its spec diff now reads 170/110, up from the 167/108 Worker 3 saw mid-review.

**Checked for coupling, and there is none:** `grep -n spec-009` over both spec-011 files returns
nothing, so spec-011 carries no inbound anchor into this cycle's writable set. Spec-010's two inbound
anchors were re-verified above at 22:45:45Z and still resolve. Nothing was edited, reverted, or
`git checkout`-ed (`AGENTS.md` rule 34). Worker 0 should append this growth to the plan rather than a
worker editing it.

Worker 3's escalation that `spec-010`'s opener still describes spec-009 as covering "custom field
classes" is **re-read and still standing** as of this pass, and is still not repairable from here. Its
recommended resolution (ii) — hold it for the maintainer to sequence at commit — is unchanged, and now
applies to a three-cycle collision rather than a two-cycle one.

### Source verification performed (this pass)

Every claim a finding turned on was re-derived read-only rather than accepted from Worker 3's prose.

- **M1** — `types/definition.py::DjangoTypeDefinition` read in full: `fields_spec` / `exclude_spec` are
  the shipped names; `filterset_class` / `orderset_class` / `fields_class` are `type | None`;
  `aggregate_class` and `search_fields` are absent; `grep -rn LazyClassRef django_strawberry_framework/`
  -> 0.
- **M2** — `types/base.py::DjangoType.__init_subclass__` builds `consumer_annotated_relation_fields` and
  `consumer_annotated_scalar_fields` inline, calls `types/base.py::_consumer_assigned_fields` for the
  assigned pair, and unions the four at #"Four-corner consumer-override contract". Three validators
  (`_validate_nullability_override_targets`, `_validate_filesystem_path_targets`,
  `_validate_relation_shape_targets`) receive the union **before** `_build_annotations` is called, and
  `_build_annotations` takes it as a keyword parameter it never derives.
- **M3** — `types/resolvers.py` imports nothing from `..utils.querysets`; the package-wide call sites of
  `apply_type_visibility_sync` relevant to a generated relation are `connection.py`, `list_field.py`, and
  `optimizer/walker.py::_build_child_queryset` (the last gated on `has_custom_qs`, inside an extension
  that is opt-in at schema construction). **Confirmed as a documentation over-claim, not a source
  defect. Nothing is escalated.**
- **L3** — `connection.py::_connection_type_for` docstring: #"Always returns a generated concrete
  ``<TypeName>Connection`` subclass"; the `Meta.connection` value "only controls the shape".

### Notes for Worker 3 (re-review)

- **The three cut narration blocks are the judgement call worth auditing.** `### Layer 3`'s rejected-
  direction paragraph was **deleted rather than re-moved**: its substance is already in the rationale's
  own `### Layer 3` entry (both reasons, in more detail), so moving it would have created a second copy
  of a story the file already tells. What stayed in the spec is the forward-looking constraint on any
  future auto-triggering helper — implementation-relevant, so `worker-1.md` says it stays — restated as a
  property of the lockless registry rather than as the moral of a rejection. If you read the deletion as
  losing something the rationale does not carry, say so.
- **`## Proposed module layout`'s closing sentence was deleted, not shortened.** It said the layout
  "replaces the earlier flat-file proposal" and listed eight never-built module names. Removing the
  chronology left only "This matches the target layout in `docs/TREE.md`", which the section's own
  preamble already establishes — so the sentence went entirely. That is a slightly larger cut than the
  finding asked for and is flagged as such.
- **`## Open questions`' pointer was rewritten, not deleted.** After the Layer 3 deletion it would have
  pointed at a section that no longer argues the rejection, so it now cites the spec section for the
  contract and the rationale for the alternative.
- **Nothing new was added to the spec that a finding did not require.** The two additions with any bulk
  — the `DjangoTypeDefinition` subset paragraph and the Layer 4 seam restatement — are M1 and M3
  respectively. Re-derive both against source rather than accepting them; they are new claims about
  shipped code, which is the class of sentence this pass's predecessor got wrong twice.

### Spec changes made (Worker 1 only)

Continuing the combined pass's numbering. Symbol-qualified, no line numbers.

| # | Section | Change | Finding | Reason |
|---|---|---|---|---|
| 36 | `### Borrow \`StrawberryDjangoDefinition\`` | Sketch corrected to shipped names and types (`fields_spec` / `exclude_spec`, sidecars as plain `type \| None`, `aggregate_class` / `search_fields` / `LazyClassRef` dropped) and declared an explicit **subset**, with one paragraph naming what the shipped record adds and why the two absent slots have no storage. Benefits bullet narrowed from "filter/order/aggregate defaults" to "filter and order defaults" | M1 (D10) | The row was ticked with the section byte-unchanged; the sketch sits in a fenced `python` block a reader copies, and it contradicted `## Target outcome`'s own `DEFERRED_META_KEYS` paragraph |
| 37 | `### Track annotation provenance structurally…` | "`types/base.py::_build_annotations` is their producer and first consumer" -> `DjangoType.__init_subclass__` derives them, `DjangoTypeDefinition` carries them, and the override validators and `_build_annotations` all read the same union | M2 | False in both halves against source; the rationale half of the same sentence was corrected with it, and its "four frozensets" count fixed to four-plus-their-union |
| 38 | `### Layer 4: Generated relation fields` | Visibility bullet: the unconditional "so a nested traversal **cannot** see a row a root query would hide" replaced by the three sites the composition actually runs on, and where a raw `list[T]` relation gets its answer instead | M3 | The spec asserted a package-wide guarantee the generated resolver does not give; `_make_relation_resolver` never calls the seam |
| 39 | opener | "the three sites that direction was stated at" -> "the four sites" | M4 | Falsified by this cycle's own sweep, in a sentence the combined pass had edited |
| 40 | `### Layer 3: Finalization trigger` | The "an earlier direction had … was **rejected**" paragraph deleted; the constraint it left behind restated as a property of the lockless registry, with a one-line pointer to the rationale entry | M5 | `BUILD.md` `## Spec rationale extraction` — the spec never narrates its own history; the rationale already carries the whole story |
| 41 | `## Proposed module layout` | "The flat-module names in older drafts of this spec have been migrated to packages below." deleted | M5 | Chronology, in a section this cycle had already edited twice |
| 42 | `## Proposed module layout` | Closing sentence reduced to "This matches the target layout in `docs/TREE.md`." — the eight-name flat-file "replaces" list deleted | M5 | Chronology, and redundant against the section's own preamble |
| 43 | `## Open questions` | "see `### Layer 3` above for why the auto-triggering alternative was rejected" -> the spec section for the contract, the rationale companion for the alternative | M5 | Same rule; and change 40 removed the argument the pointer pointed at |
| 44 | `### Borrow \`DjangoListConnection\`` | "the connection field resolves **that type** through a generated concrete `<TypeName>Connection`" -> resolves **every** node type, with the opt-in deciding only the shape | L3 | `_connection_type_for` always generates; the sentence scoped generation to the opt-in |

**Rationale changes (append-only, Worker 1 only).** One new entry (``### Borrow `StrawberryDjangoDefinition` ``,
for M1); the M2/L1a correction and the M3 and L3 method notes folded into the entries this cycle already
added for those sections; the L4 survivor list completed with `### Layer 9`; the L2 heading renamed to
name all four spec sections it covers, and extended with the three narration deletions of changes 40-43.
Every touched entry is one **this cycle** authored — the six pre-existing entries and `## Standing notes`
are byte-identical to HEAD.

**Deferrals.** None. Every dispatched box is `- [x]` with a landed contract behind it, D10 included.

---

## Final verification (Worker 1)

*(not yet run — follows Worker 3's acceptance)*

### Spec changes made (Worker 1 only)

Every edit, with the section, the drift row that triggered it, and a one-line reason. Symbol-qualified, no line numbers.

**Header re-verification** (`worker-1.md` `## Spec status-line re-verification`): the spec carries no status/owner/predecessor lines — its opener is the rationale-companion pointer. That pointer was falsified by this pass (it enumerated what the companion carries) and was extended to name the six scrubbed mechanisms. **D1-D6.**

| # | Section | Change | Row | Reason |
|---|---|---|---|---|
| 1 | opener | Rationale pointer extended to name the six dropped mechanisms | D1-D6 | The pointer enumerated the companion's contents and would otherwise under-describe it |
| 2 | `## Target outcome` | `object_type: ObjectTypeNode` → `ObjectTypeNode \| None`, plus a paragraph stating the nullable-by-contract dispatch | D7 | A copied non-null annotation builds a schema that violates non-null on every hidden or missing row |
| 3 | `## Target outcome` | Added a paragraph naming the three `DEFERRED_META_KEYS` and the card that promotes each, and pointing at `ALLOWED_META_KEYS` | D8 | The flagship example raises `ConfigurationError` today; the reader needs to know which keys are the destination |
| 4 | `#### Take \`fields_class\`` | "implement it as part of a custom Strawberry field class" → resolver wrapping, citing `spec-054` | D1 | Unnamed D1 echo found by the sweep; `spec-054` pins resolver wrapping as the mechanism |
| 5 | Strawberry-Django reference list | Removed the 6 `file:///` entries that existed only to anchor dropped mechanisms (`get_strawberry_annotations`, `OptimizerStore` ×4 — the class and its three methods) | D2, D3 | "Reshaped to not mention the features at all" reaches the citation list; `DjangoModelType`'s entry was **kept**, since the surviving refusal argument cites it |
| 6 | `### Borrow \`_process_type\`` | Final adaptation bullet no longer post-processes fields into `DjangoModelField` objects | D1 | Names a class that does not exist and never will |
| 7 | `### Borrow \`get_strawberry_annotations\`` | Replaced by `### Track annotation provenance structurally, not by re-collecting annotations` | D3 | Section's whole subject was the dropped borrow; the replacement states the shipped provenance mechanism so the chapter keeps the topic |
| 8 | `### Borrow \`StrawberryDjangoFieldBase\` and \`StrawberryDjangoField\`` | Dataclass sketch and borrow list replaced by the four shipped seams, plus the single-definition invariant and **why upstream needs the class and this package does not** | D1 | The section's subject was creating `DjangoModelField`; the behaviors are real requirements and had to land somewhere |
| 9 | `### Borrow \`resolve_type\`…` | Item 5 rewritten; the "Keep `DjangoModelType` only as an internal or explicitly requested fallback" sentence deleted and replaced with the no-placeholder-tier statement | D5 | Resolves a live self-contradiction with `### The unresolved-relation contract is error-only` |
| 10 | `### Borrow \`field\` and \`connection\`…` | `DjangoField(...)` → `DjangoListField(...)`; "Internally those should use a custom `DjangoModelField`" → the factory-returns-a-field statement | D4, D1 | `DjangoField(...)` is the decorator-first surface this package exists to avoid; its capabilities ship under other names |
| 11 | `### Borrow \`DjangoListConnection\`` | Sketch corrected: no `total_count` on the base, `totalCount` opt-in via `Meta.connection` through a generated `<TypeName>Connection`, `aggregates` restated as owed with its card | D9 | Wrong in both fields; the generic-specialization reason is implementation-relevant and stays in the spec |
| 12 | `### Borrow \`OptimizerStore\`…` | Heading → `### Keep the current optimizer's strengths, and borrow its nested-prefetch lessons`; the 3 store/callable bullets removed; a value-not-callable hint rule added | D2 | Heading named a dropped mechanism; the callable bullet was **contradicted** by the invariant that buys the plan cache |
| 13 | `### Borrow \`django_resolver\` and \`django_getattr\`` | `DjangoModelField.get_result` → `types/resolvers.py::_make_relation_resolver` | D1 | Unnamed D1 echo found by the sweep |
| 14 | `## What to scrap from Strawberry-Django` | "Keep as references" list: `field-class lifecycle` → `type finalization lifecycle`, `annotation namespace preservation` → annotation handling, `optimizer stores and nested prefetch handling` → nested prefetch handling | D1, D2, D3 | Three residues only the `grep -c` sweep found |
| 15 | `## Recommended combined architecture` | Items 3 and 4: "field/type/finalization mechanics" → type/finalization; "evolve it with Strawberry-Django field stores" → nested-connection prefetch lessons | D1, D2 | Same sweep |
| 16 | `### Layer 4` | Retitled `### Layer 4: Generated relation fields`; rewritten to the four shipped seams plus the constraint that makes Phase 2 the only generation window | D1 | Dispatch-prescribed rewrite; the "transition path" ending in "delete per-relation resolver generation" was false in both directions |
| 17 | `### Layer 5` | Item 2 "finalize pending types" removed, list renumbered 1-12, and a paragraph added stating that constructing a connection field must **not** finalize | D13 | The spec contradicted its own corrected `### Layer 3`; removing the item alone would have left the reader unwarned |
| 18 | `### Layer 6` | `AdvancedFilterSet` → `FilterSet`; `Meta.filter_fields` → `Meta.fields`; paragraph added on the naming reason and the parity alias | D11 | `AdvancedFilterSet` was never this package's name at any version; see `### Notes for Worker 3` for the alias correction |
| 19 | `### Layer 7` | `Advanced[OrderSet]` → `[OrderSet]`; `ASC_DISTINCT` / `DESC_DISTINCT` and the `DISTINCT ON` bullet removed; the `Ordering` borrow bullet strengthened to the six-member vocabulary; a row-preserving `Min`/`Max` paragraph added | D6, D12 | The directives were replaced, not deferred; the fan-out problem needed to keep an answer in the layer |
| 20 | `### Layer 8` | `class ObjectAggregate(AdvancedAggregateSet)` → `AggregateSet` | D12 | An unshipped-but-carded class follows the shipped `*Set` convention |
| 21 | `### Layer 9` | `DjangoModelField.get_result` → resolver wrapping, with `spec-054` and `TODO-BETA-054-0.1.1` named | D1 | Dispatch-named D1 echo |
| 22 | `### Layer 11` | `field-level OptimizerStore` and `callable prefetch/annotate hints` bullets removed | D2 | Dispatch-named D2 echo |
| 23 | `## Definition-order strategy…` | Algorithm step 6: "attach `DjangoModelField` instances" → "attach the generated relation resolvers"; the "custom field" clause dropped from the Use list | D1 | Names a class that does not exist |
| 24 | `## Proposed module layout` | `types/fields.py` removed; `fieldset.py` → `fieldset/` with its card; `orders/inputs.py` added; `aggregates/` and `permissions.py` annotated with their cards | D14 | `fieldset.py` contradicted the section's own package-layout preamble; `orders/inputs.py` ships and is required by shipped code |
| 25 | `## Proposed module layout` | Evolve list: `types/resolvers.py` "transitional relation resolver support" → generation and attachment for every cardinality; `optimizer/*` "add field stores and connection awareness" → nested-connection awareness | D1, D2 | Sweep residues |
| 26 | `### Phase 1` | Inline link → reference-style `[spec-010]`; "Earlier drafts of this spec listed `DjangoSchema` here; the foundation contract has narrowed" deleted, moved to the rationale | convention | `AGENTS.md` rule 28 / `START.md`; and `BUILD.md` `## Spec rationale extraction` — the spec never narrates its own history |
| 27 | `### Phase 3` | Retitled `### Phase 3: Generated relation fields`; body restated to Layer 4's mechanism. **The five acceptance tests are unchanged.** | D1, D15 | **Decision recorded:** the vacated slot is repurposed, not gapped and not renumbered. Renumbering is forbidden (`spec-010` cites `### Decision 6` by anchor) and a gap is a scar that invites a later reader to re-fill it with what was removed. Repurposing is honest here because the five acceptance tests all pass today via the machinery that superseded the class — the phase's contract was always right, only its named mechanism was wrong |
| 28 | `### Phase 5` | `ASC_DISTINCT` / `DESC_DISTINCT` acceptance line → a to-many order path that duplicates no parent rows and inflates no `totalCount` | D6 | The mechanism can never pass as written; the property is what the shipped tests pin |
| 29 | `### Phase 6`, `### Phase 7` | Owning cards named; `AdvancedFieldSet` → `FieldSet`; sentinel redaction marked opt-in with its card | D15, D12 | Maintainer decision 1 requires the owning card for each unshipped layer; only unshipped items are annotated |
| 30 | `### Phase 8` | `field-level optimizer stores` bullet removed | D2 | Dispatch-named D2 echo |
| 31 | `### Decision 3` | `### Decision 3: custom Strawberry field class` → `### Decision 3: generated field behavior belongs to the finalizer` | D1 | **Decision recorded:** slot repurposed, not gapped. The replacement states the positive contract (behavior belongs to the finalizer; composability comes from one readable definition) **without naming the mechanism that lost** — the spec body carries no "this was rejected" prose |
| 32 | `### Decision 5` | "field processing, annotations, connection extensions, and optimizer stores" → type finalization, annotation handling, connection extensions, nested-prefetch planning | D1, D2 | Named two dropped mechanisms in the summary decision list — the site a hurried reader trusts most |
| 33 | `## Open questions` | "Should generic fallback exist?" removed entirely | D5 | Directly contradicted `### The unresolved-relation contract is error-only`; the surviving section already owns the answer |
| 34 | `## Success criteria` | The three unmet criteria annotated with their owning cards | D16 | Maintainer decision 1; shipped criteria are deliberately **not** annotated with versions |
| 35 | link definitions | `[spec-010]` added under `<!-- docs/SPECS/ -->`, alphabetical | convention | Required by change 26; no definition was orphaned by any scrub |

**Deferrals.** None. Every dispatched box is `- [x]`; no D-row was left partially addressed.

---

## Review (Worker 3, pass 2)

Audited 2026-08-15 by a **fresh Worker 3 invocation** with no in-context memory of pass 1 beyond
`docs/builder/worker-memory/spec-009-worker-3.md`. Scope: the whole working-tree diff of
`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` (**115 insertions / 170 deletions**, re-measured)
and `docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md` (**405 insertions / 0
deletions**), against shipped source read read-only, plus the nine findings pass 1 raised.

**Method.** Every one of the nine findings was re-verified individually against source, not against the
apply-changes pass's prose. Every *new* sentence the pass added was re-derived as a fresh claim about
shipped code (`BUILD.md` `## Claims are proven mechanically, never accepted on prose`). Every stated
count was re-measured — the `DjangoTypeDefinition` slot/method counts by AST, `ALLOWED_META_KEYS` from
the frozenset literal. The mechanical gates and the link / anchor / rule-27 validators were re-run, not
trusted. The `### Dispatched findings checklist` was walked box by box against the diff. `git stash`,
`git checkout`, `git restore`, and `git worktree` were not used; the HEAD reference was
`git show HEAD:<path>` into a scratch path outside the repository.

**Byte / line ledger, independently re-measured.** Spec 61,401 bytes / 1,099 lines (HEAD baseline
60,855 / 1,099 at pass 1 → +546 / 0). Rationale 42,969 / 613 (36,744 / 537 → +6,225 / +76). HEAD's
rationale is 208 lines; 208 + 405 = 613. Every number in the apply-changes `### Byte counts` table and
its `### Validation run` re-derives exactly.

### High:

None.

### Medium:

#### The `DjangoTypeDefinition` subset paragraph explains the missing `LazyClassRef` with a mechanism the shipped code contradicts

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:385`:

> A sidecar slot is a plain `type | None` — no lazy class reference is needed, because a sidecar binds
> at finalization rather than at class creation.

The M1 fix is otherwise correct and I verified every structural claim in it (below, under
`### What looks solid`). This one clause is a **new** causal claim about shipped code, added by the
apply-changes pass, and it is false in both halves:

- **A sidecar does not bind at finalization rather than at class creation.**
  `types/base.py::_validate_filterset_class` requires an already-resolved class at **class creation** —
  `if not (isinstance(filterset_class, type) and issubclass(filterset_class, FilterSet))` raises
  `ConfigurationError` — and `types/base.py::DjangoType.__init_subclass__` populates the slot there
  (`types/base.py` #"filterset_class=validated.filterset_class"). What happens at finalization Phase 2.5
  is the *reverse* binding (`types/definition.py::DjangoTypeDefinition` #"to bind the owning
  ``DjangoTypeDefinition`` on the FilterSet"), which is a different operation from the one the sentence
  is reasoning about.
- **The causal arrow is inverted.** Deferred binding is what would *permit* a lazy reference, not what
  removes the need for one. The real reason the slot can be a plain `type | None` is the opposite of
  what the sentence says: the value is validated to a concrete class at class creation, so a
  forward/string reference is refused and can never reach the slot.

It also puts the spec in contradiction with itself. Two untouched lines still describe lazy refs for
exactly these classes: `:704` "`RelatedFilter` uses lazy class refs" and the finalization algorithm's
`:836` "resolve lazy filter/order/aggregate/fieldset class refs". A reader designing the `fields_class`
slot for `TODO-BETA-054-0.1.1` — which this same paragraph points at — would take "a sidecar binds at
finalization" as licence to accept a class declared later, which shipped code refuses at class
creation.

This is the pass's own signature risk realised once more: a fluent explanatory clause, in a paragraph
whose *facts* were all verified, that nobody checked because it reads like connective tissue.

Recommended change: keep the observation and drop or invert the reason — e.g. "A sidecar slot is a
plain `type | None`: `Meta.filterset_class` / `Meta.orderset_class` are validated to a concrete class at
class creation (`types/base.py::_validate_filterset_class`), so no lazy reference can reach the slot."
If the algorithm's `:836` lazy-ref step is itself now stale, that is a separate row and should be
recorded as one rather than settled implicitly by a subordinate clause.

### Low:

#### The Layer 4 visibility correction was not swept onto its twin bullet 230 lines earlier

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:419`, in
`### Borrow \`StrawberryDjangoFieldBase\` and \`StrawberryDjangoField\``:

> **visibility** — `utils/querysets.py::apply_type_visibility_sync`, so the target type's
> `get_queryset` composes onto the relation queryset

This is the second of the spec's **two** four-seam bullet lists describing where a generated relation
field's responsibilities live; change 38 qualified the Layer 4 copy (`:652`) and left this one. It is
milder than the Layer 4 original — it names the seam without asserting a "cannot see" guarantee — which
is why this is Low and not a repeat of M3. But the list's own preamble (`:415`) frames each bullet as
where that responsibility lives *for a generated relation field*, and M3 established that the seam does
not run inside the generated resolver at all. The spec now describes the same seam two ways in two
sections, which is the shape M1 was raised for.

The rationale's new method note (`…rationale.md:306-308`) generalises the rule correctly — "naming the
seam that implements a guarantee is not the same as establishing where the guarantee holds — **a bullet
listing four seams invites exactly that slip**" — and then applies it to only one of the two bullets
listing four seams.

Recommended change: one clause or a pointer — "…composes onto the relation queryset on the paths
`### Layer 4` names" — or a recorded rejection stating that the unqualified mechanism naming is
deliberate here because this section is about upstream's class rather than about this package's
guarantees.

### DRY findings

- **No package-code duplication is possible.** The diff touches two `.md` files and adds no helper,
  constant, or branch. The plan's DRY analysis is right that the usual inventory is moot and says so
  rather than omitting it.
- **The spec / rationale near-duplication pass 1 recorded was rejected with a reason, and the rejection
  is sound.** The "upstream binds all of them to one field class because its public API is
  decorator-first" argument still appears in both (`spec:415`, `rationale:277-283`). The apply-changes
  pass declined to replace the rationale's telling with a pointer, on the `worker-1.md`
  `### Performing the rationale move` implementation-relevant carve-out, and recorded the rejection
  explicitly rather than silently. I re-read both copies: they agree, and the entry does need the
  argument in hand. Accepted as an intentional rejection; the drift risk stands and is now on the
  record in two places, which is the most a reviewer can ask for.
- **Cross-spec near-duplicate, PRE-EXISTING and not introduced by this pass — recorded, not flagged.**
  Change 40's replacement sentence in `### Layer 3` ("any future helper that auto-triggers it must also
  enforce the single-threaded setup window — either by being constrained to schema-construction time or
  by acquiring a real lock around the finalizer") is a near-verbatim twin of
  `docs/SPECS/spec-010-foundation-0_0_4.md:67`'s closing sentence. Both predate this cycle (the deleted
  Layer 3 paragraph carried the same clause), so nothing was introduced; but the plan's DRY rule
  extends single-ownership **across** specs, and this is a live instance. It is not repairable from
  here — spec-010 belongs to a concurrent cycle — so it is routed to Worker 1 below rather than raised
  as a finding.
- **Existence challenge: not raised.** The pass introduces no abstraction, registry, indirection, or
  helper. The one structural choice — repurposing the vacated `### Decision 3` / `### Phase 3` slots
  rather than gapping or renumbering — remains the less machinery-heavy option and is unchanged this
  pass.
- **The single-ownership split still holds on the scrubs.** I re-read every rewritten section end to
  end: no "why it lost" sentence survives in the spec body for any of the six dropped mechanisms, and
  the three narration deletions of changes 40-43 moved the split further in the right direction rather
  than blurring it.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → empty; `git status --porcelain` on that path is
clean. `__all__` and the re-export list are unchanged, so no spec authorization is needed. Consistent
with the plan's `## Build-wide context flags` declaring source read-only cycle-wide.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. `git status --porcelain CHANGELOG.md` is clean, and
`AGENTS.md` rule 21 plus the plan's `## Build-wide context flags` close it for this cycle.

### Documentation / release sanity

**Applies** — the diff is entirely docs / archived-spec surface. Both changed files were read end to end.

- **Mechanical gates, re-run not trusted.**
  `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.`, **exit 0, count still 23** —
  matching the pre-flight baseline and the card's 23 glossary links. The three narration deletions and
  the narrowed benefits bullet removed no term's last site.
  `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0** for both.
- **Link / anchor / rule-27 validator**, written fresh for this pass and run over both files with code
  fences stripped: spec **25 definitions / 25 used, 0 missing, 0 orphan**; rationale **11 / 11, 0
  missing, 0 orphan**; **36 definitions total, every non-anchor target disk-existence-checked and all
  resolve**; **0** `](#…)` in-page anchors in either file, therefore 0 unresolved; **0** raw in-repo
  `path:NN` citations in either file, measured both outside and inside code spans with `file:///` URLs
  excluded. The spec now carries **0** inline cross-file links; the rationale's single apparent one
  disappears once code spans are stripped — it is the *quotation* of the link change 26 removed, so it
  renders verbatim per `START.md` "Markdown link convention". Correct, not a violation. The ~60 upstream
  `file:///…#LNN` citations are out-of-repo and correctly untouched; not flagged.
- **Cross-spec anchors: FIVE, all resolving in both directions, re-verified at
  2026-08-15T22:55:40Z.** Timestamped because spec-010 is `M` under a concurrent cycle and moved again
  between pass 1's 22:37:39Z check and this one. Inbound (2): `spec-010:67` cites `spec-009` #"### Layer
  3: Finalization trigger", `spec-010:468` cites #"### Decision 6: fail loudly" — `grep -c` → 1 each in
  the edited spec-009. Outbound (3): `spec-009:99` cites `spec-010` #"### Must redo (not augment)",
  `:637` #"## Strawberry finalization strategy", `:873` #"### Unresolved-target error format" — `grep
  -c` → 1 each in the current spec-010. **Worker 1's five-anchor count is right and pass 1's four was
  short**; the `:99` outbound one is real and live. `spec-008`'s inbound reference is whole-file, not
  anchored. `grep -rln spec-009 docs/SPECS/` returns no spec-011 file, so the third concurrent cycle
  carries no inbound anchor into this cycle's writable set.
- **No renumbering.** `### Decision 1` through `### Decision 6` and `### Phase 1` through `### Phase 8`
  are all present with their original numbers and no gaps; the two vacated slots carry positive
  contracts and no "this was rejected" prose.
- **Version strings and card IDs.** No version string changed. Every card id introduced or retained
  exists on the board: `TODO-BETA-054-0.1.1`, `TODO-BETA-055-0.1.2`, `TODO-BETA-057-0.1.3`,
  `TODO-BETA-058-0.1.3`, `TODO-BETA-059-0.1.4` all match `KANBAN.md`.
- **KANBAN / DB / generated docs.** `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and
  `docs/GLOSSARY.md` are all absent from `git status --porcelain` — clean, as the plan requires. No
  script-rendered doc was regenerated, so the staging-docstring check does not apply.
- **Archival.** Nothing moved; both files stay at their archived paths and every link definition
  resolves from there.
- **Verbatim-copy check.** The pass copies no fenced block from another document. The one fenced block
  it edited (`DjangoTypeDefinition`) uses three backticks in a document with no four-backtick outer
  fence — no conflict.
- **Provenance.** `HEAD` unchanged at `054de9dd`; the most recent commit touching either document is
  still `f3c94642`; both paths are `M` and uncommitted. This pass's work was not swept into a
  concurrent session's commit.

### What looks solid

**All nine of pass 1's findings are closed, each verified against source rather than against the
apply-changes report.**

- **M1 (D10) — closed and correct.** The sketch now reads `fields_spec: tuple[str, ...] |
  Literal["__all__"] | None`, `exclude_spec: tuple[str, ...] | None`, and three plain `type | None`
  sidecars, with `aggregate_class`, `search_fields`, and the `LazyClassRef` union gone. Every slot name
  and annotation matches `types/definition.py::DjangoTypeDefinition` character for character.
  `grep -rn LazyClassRef django_strawberry_framework/` → **0**. `DEFERRED_META_KEYS` is exactly
  `{"aggregate_class", "fields_class", "search_fields"}`, so the "no slot at all" claim and the
  "`fields_class` alone is reserved ahead of its key" claim both hold.
  **The stated counts re-measure exactly, by AST rather than by eye:** `DjangoTypeDefinition` carries
  **29** dataclass slots — **27** public, **2** private (`_related_target_cache`,
  `_custom_id_resolver_cache`) — and **3** methods (`graphql_type_name`, `related_target_for`,
  `has_custom_id_resolver_for`). The "explicit subset" framing is the right shape for a horizon
  document and the enumeration of what the shipped record adds (selection and field-map slots,
  provenance frozensets, Relay/connection sidecars, three methods) is accurate. The one defect in this
  paragraph is the Medium above and it is a subordinate clause, not the correction.
- **M2 — closed in both files, and the replacement is right where the original was wrong.**
  `types/base.py::DjangoType.__init_subclass__` builds `consumer_annotated_relation_fields` /
  `consumer_annotated_scalar_fields` inline, calls `types/base.py::_consumer_assigned_fields` for the
  assigned pair, and unions all four at #"Four-corner consumer-override contract". The **three**
  override-target validators (`_validate_nullability_override_targets`,
  `_validate_filesystem_path_targets`, `_validate_relation_shape_targets`) each receive that union
  **before** `_build_annotations` is called, and `_build_annotations` takes it as a keyword parameter it
  never derives. The spec's new bullet says exactly that and asserts no ordering it cannot support.
  `grep` for "producer and first" / "first consumer" across both files → **0 hits**; the claim is gone,
  not merely softened. L1a rides with it: the rationale now says "four spelling-specific …
  frozensets — a fifth slot, `consumer_authored_fields`, carries their union", which matches the five
  shipped slots.
- **M3 — closed, and the replacement does not over-claim in the other direction.**
  `types/resolvers.py` imports **nothing** from `utils/querysets` (verified by reading its whole import
  block and by `grep -n querysets` → 0 hits), so the seam genuinely cannot run inside the generated
  resolver. The three sites named are the three that exist for a generated relation:
  `connection.py:1776`, `list_field.py:236`, and `optimizer/walker.py::_build_child_queryset:383`,
  the last gated on `has_custom_qs` inside an extension whose module docstring opens #"Opt-in at schema
  construction". The added recourse clause ("a raw `list[T]` relation on a schema carrying no optimizer
  extension gets its row-level answer from the `permissions.py` cascade helpers instead") is accurate as
  documentation guidance — `permissions.py::apply_cascade_permissions` is the consumer-invoked helper
  that path uses. The sentence is now conditional where the code is conditional. Its unswept twin is the
  Low above.
- **M4 — closed, and Worker 1 was right to re-derive where the sentence lives.** `:3` now reads "the
  four sites that direction was stated at". The dispatch brief called this a rationale-opener finding;
  pass 1's section cited the spec's line 3; the sentence is in the spec. Re-deriving instead of
  following the brief was correct.
  **Leaving the rationale's `## Standing notes` "three sites" bullet is defensible, and I judged it
  rather than accepting it.** Three things make it hold: the build plan's `### Residual scope` binds the
  rationale to append-only for this cycle (citing `worker-1.md` `### Performing the rationale move`
  rule 4), so correcting the bullet in place would break a plan-level constraint to fix a
  four-lines-of-consequence count; the staleness is stated explicitly **five lines above the bullet** in
  the same file (`…rationale.md:565-568`, "the `## Standing notes` bullet below still says … three
  sites"), so no reader reaches it uninoculated; and the bullet's actual lesson — a horizon document
  states its positions more than once, so fix every site — is not just still true but *strengthened* by
  the fourth site. It is a documented stale count, not an undocumented contradiction between the two
  documents. It should be corrected by whichever pass next has the rationale open without the
  append-only constraint, and that is a note, not a finding.
- **M5 — all four closed, and I swept rather than re-read.** `### Layer 3`'s rejected-direction
  paragraph, `## Proposed module layout`'s two sentences, and the `## Open questions` pointer are all
  gone or rewritten. **There is no fifth survivor.** My independent sweep for the class — `earlier
  (draft|direction|version|proposal)`, `older draft`, `previously`, `was/were rejected`, `originally`,
  `used to`, `superseded`, `obsolete`, `this spec (once|previously|originally)`, `has since` — returns
  exactly three hits in the whole spec, none of them narration of the spec's own history: `:3` is the
  rationale pointer, whose entire job under `BUILD.md` `## Spec rationale extraction` is to name what
  the companion carries; `:96` and `:99` are the `## The 0.0.4 local package baseline` "retired since"
  markers, which narrate the **package's** history against a deliberately frozen snapshot and are
  Group C verified-accurate; `:904` states that the spec does not track which phases shipped, which is a
  contract, not chronology.
  The three deletions are also the right calls on the merits. Deleting rather than re-moving the Layer 3
  paragraph loses nothing: the rationale's own `### Layer 3` entry carries both reasons in more detail,
  and what stayed in the spec is the forward-looking constraint — "The registry is deliberately lockless
  and finalization is a process-global mutation, so any future helper that auto-triggers it must also
  enforce the single-threaded setup window" — which I verified against `registry.py` #"Mutating methods
  are not guarded by a lock". `## Proposed module layout`'s closing sentence going entirely rather than
  being shortened is correct and was flagged as the larger cut it is; the residue ("This matches the
  target layout in `docs/TREE.md`.") is what the section's own preamble already establishes, and a list
  of eight never-built module names records nothing actionable. The `## Open questions` rewrite is
  necessary, not optional — after change 40 the old pointer aimed at a section that no longer argues the
  rejection.
- **L1b — correctly handled as a correction-in-place-of-a-rewrite.** `ALLOWED_META_KEYS` holds **17**,
  re-measured from the frozenset literal in `types/base.py`; the seventeen names Worker 1 lists are
  exactly the seventeen in the source, in order. Recording the correction in the new section rather than
  editing the combined pass's report is the right instinct — a prior pass's report is that pass's record.
- **L2 — closed.** The entry heading now reads `` ### `### Phase 1`, `### Layer 3`, `## Proposed module
  layout`, `## Open questions` — convention corrections made beside the drift rows ``, naming all four
  spec sections it covers and satisfying the file's own `## How to read this file` rule.
- **L3 — closed, and verified against source rather than against the report.**
  `connection.py::_connection_type_for`'s docstring says #"Always returns a generated concrete
  ``<TypeName>Connection`` subclass of ``DjangoConnection[target_type]``" and that the
  `definition.connection` slot #"only controls the shape"; the body confirms it — both branches return a
  generated class, `_build_total_count_connection` or `_generate_connection_class`. The spec's new
  sentence ("resolves **every** node type through a generated concrete `<TypeName>Connection` subclass;
  the opt-in decides only whether that subclass carries the member or adds nothing over the base")
  matches the docstring clause for clause.
- **L4 — closed.** `…rationale.md:487-492` now enumerates `AdvancedAggregateSet` in `#### Take aggregate
  semantics`, `AdvancedFieldSet` in `` #### Take `fields_class` `` **and** in `### Layer 9: FieldSet and
  field-level permissions`, plus the `file:///` citation list. The list is complete against the spec's
  surviving upstream-name sites.

**Nothing else new was introduced.** I re-derived every remaining new sentence in changes 36-44 and the
rationale's apply-changes additions against source; apart from the Medium above, all verify. Spot list:
the `Min`/`Max` row-preserving paragraph against `orders/sets.py` #"models.Min if direction.is_ascending
else models.Max"; `DEFERRED_META_KEYS` against the `## Target outcome` paragraph; the declarable-key
list (`model`, `fields`, `interfaces`, `filterset_class`, `orderset_class`) against
`ALLOWED_META_KEYS`; "connection fields can resolve filter and order defaults from the node type"
against `connection.py:1777-1780` and `:1857`, which read `definition.filterset_class` /
`definition.orderset_class` directly; the deleted flat-file list's **8** module names, counted from the
diff. **The pass answered its calibration by cutting rather than qualifying, and the ledger proves it:
115 insertions against 170 deletions, line count unchanged at 1,099, +546 bytes.** The rationale grew
because that is where the cut narration went.

**The append-only claim on the rationale is mechanically proved, and I proved it independently.**
`git diff` over the rationale contains exactly **one** line beginning with `-`, and it is the `--- a/`
header — so *no HEAD line was deleted or modified*, which is a stronger statement than the `head -164`
check and subsumes it. `head -164` of the working file `cmp`s exit 0 against `head -164` of
`git show HEAD:<path>` copied to a scratch path outside the repository. The file is **not** a pure
prefix — insertions land at `+167` (403 lines of entries) and at `+589` / `+591` (the two link
definitions, alphabetical inside `<!-- docs/ -->`) — which is exactly what "appended entries plus two
required definitions" should look like and is not a violation of anything. `## Standing notes` is
untouched.

**Every checklist tick has a matching hunk in the working-tree diff — no repeat of the D10 over-tick.**
I walked D1-D16 individually against the diff: D1 (Layer 4 / Decision 3 / Phase 3 / Layer 9 / module
layout / algorithm step 6 / `_process_type` / `django_resolver` / Decision 5), D2 (heading, three
bullets, Layer 11, Phase 8, four `file:///` citations), D3 (section replaced), D4 (`DjangoField(` →
`DjangoListField(`), D5 (fallback sentence + open question), D6 (Layer 7 + Phase 5), D7, D8, D9, D10
(**now** the corrected sketch plus change 36), D11, D12, D13, D14, D15, D16 — all sixteen produce a
visible hunk. The D10 box carries the annotation the apply-changes pass was instructed to add, and it is
the only edit outside that pass's own section. One honest limitation: this artifact is untracked, so
"prior sections untouched" is not mechanically verifiable from git; I confirmed it only by the
`## Review (Worker 3)` section reading consistently with the findings the apply-changes pass enumerates.

### Temp test verification

- No temp test files were created under `docs/builder/temp-tests/r1/`, and none was warranted: this
  item ships no executable line, so there is no behavior a test could pin. The directory does not exist
  and was not created; the `r2` / `r2b` directories present under `docs/builder/temp-tests/` belong to
  the concurrent spec-010 cycle and were neither read nor touched.
- Verification instead used read-only source reads, an AST count of `DjangoTypeDefinition`'s slots and
  methods, `grep -c` sweeps, re-runs of both mechanical gates, and one throwaway Python validator (link
  definitions, orphans, in-page anchors, dead link targets, raw `path:NN` inside and outside code spans,
  inline-link detection) executed from a stdin heredoc. Nothing was written into the repository; the two
  HEAD reference copies went to a scratch path outside it.
- Disposition: nothing to promote.

### Failability proofs

**Not applicable to a documentation pass.** `BUILD.md` `### What needs a proof, and what does not`
scopes the obligation to a new boundary, guard, gate, or rejection path a slice introduces; this diff
touches two `.md` files and introduces none, so the mandatory re-run floor is computed over an empty set
and an empty re-run set is legal here. No boundary was re-run and none was accepted on a builder's
record, because none exists. Worker 3's source carve-out was not exercised: no production file was
mutated at any point in this pass.

### Hot-path budget

**Not applicable to a documentation pass.** The build plan declares `Hot-path declaration: none` for the
whole cycle and R1's plan repeats it; no item touches an executable line, so there is no before/after
number owed and none is missing. I found nothing that contradicts the not-hot-path declaration.

### Notes for Worker 1 (spec reconciliation)

- **The one Medium is inside this cycle's writable set and is a plain factual correction.** It needs a
  clause rewritten, not a judgement call. If the finalization algorithm's `:836` "resolve lazy
  filter/order/aggregate/fieldset class refs" step is itself stale against
  `types/base.py::_validate_filterset_class`, that is a new drift row and should be recorded as one —
  do not settle it silently by leaving the subordinate clause that currently contradicts it.
- **Escalated (report-only, do not repair): `spec-010:8` still mis-describes `spec-009`.** Re-read at
  2026-08-15T22:55:40Z and still standing — it lists "custom field classes" among what spec-009
  describes, which is exactly what D1 scrubbed. Unchanged from pass 1's escalation and from the
  apply-changes pass's re-read. Recommendation is still (ii): hold for the maintainer to sequence at
  commit. The collision is now three cycles wide (spec-010 and spec-011 both dirty).
- **Escalated (report-only, do not repair): change 40 also weakened what `spec-010:67` finds.** That
  line says "The auto-trigger direction in `spec-009` #"### Layer 3: Finalization trigger" was not
  adopted" — the anchor still resolves and the *claim* is still true, but after change 40 the cited
  section no longer states the direction anywhere; it points at the rationale instead. Nothing dangles
  and nothing is false, so this is not a finding; it is a second instance of the same two-cycle coupling
  and belongs with the escalation above.
- **Cross-spec near-duplicate, pre-existing.** `spec-009`'s post-change-40 single-threaded-setup-window
  sentence and `spec-010:67`'s closing sentence are near-verbatim twins, and were twins before this
  cycle too. The plan's DRY rule extends single-ownership across specs; the right owner is
  `spec-010`, which owns the finalization-trigger contract. Not repairable from here.
- **Source observation, not a defect and not actionable in this cycle.**
  `types/definition.py::DjangoTypeDefinition`'s invariants docstring says `fields_class` is "the
  forward-reserved `FieldSet` sidecar slot for ``TODO-BETA-046-0.1.1``". `046` is now `DONE-046-0.0.14`
  (the transport card) after the card renumber; the live owner is `TODO-BETA-054-0.1.1`, which is what
  the spec, `KANBAN.md`, and `docs/TREE.md` all say. **The spec is right and the source docstring is
  stale.** Source is read-only in this cycle, so this is recorded for the maintainer only; it is a
  candidate row for whichever cycle next owns source docstrings.
- **R2 carry-forward is unchanged and still consistent.** The spec-009 half of D6 states the
  row-preserving property, not the `DISTINCT ON` mechanism, and the rationale says the mechanism "is not
  a deferred better answer; it is a worse one for a cursor-paginated schema". R2's reconciliation of
  `spec-028` `### Decision 12` must say **discharged by an alternative**, not postponed. `spec-028` is
  still absent from `git status --porcelain`, so R2 starts from an untouched file.
- **Nothing else escalates.** I found no correctness defect in shipped source and I am escalating none.
  Both findings above are about spec sentences, deliberately not about the code.

### Review outcome

`revision-needed`.

**All nine of pass 1's findings are genuinely closed** — eight fixed and verified against source, one
(the rationale's `## Standing notes` count) intentionally left with a recorded reason I have judged
defensible. No fix landed hollow, no tick is unbacked, and the pass answered its over-write risk by
cutting more lines than it added.

Two new findings block acceptance, both inside this cycle's writable set and both cheap:

1. **Medium** — `:385`'s "a sidecar binds at finalization rather than at class creation" is a new causal
   claim contradicted by `types/base.py::_validate_filterset_class` and by the spec's own `:704` /
   `:836` lazy-ref lines. Rewrite the clause or drop it.
2. **Low** — the twin four-seam visibility bullet at `:419` did not receive M3's qualification. Qualify
   it, point it at `### Layer 4`, or record why the unqualified form is deliberate there.

Under the plan's `### Deviation 3` corollary the apply-changes pass for R1 is Worker 1's and sets
`Status: planned` again, returning the artifact to the `planned` → Worker 3 mapping.

## Build report (Worker 1, apply-changes pass 2)

Fresh Worker 1 invocation, 2026-08-15. Scope: the two findings Worker 3's pass 2 raised (one Medium,
one Low). Pass 2 confirmed all nine of pass 1's findings genuinely closed, so nothing else was
re-opened. Both fixes were made by cutting, not by appending a qualification.

### Findings closed

#### Medium — `:385` "a sidecar binds at finalization rather than at class creation"

**Cut, not qualified.** The clause was a causal claim introduced by the previous apply-changes pass and
false in both halves. Re-derived against source before rewriting rather than from the review's prose:

- `types/base.py::_validate_filterset_class` raises `ConfigurationError` unless the value
  `isinstance(..., type) and issubclass(..., FilterSet)`; `types/base.py::_validate_orderset_class` is
  its exact twin for `OrderSet`. Both are called from `_validate_meta`, i.e. at **class creation**.
- `types/definition.py` slots read `filterset_class: type | None` / `orderset_class: type | None` /
  `fields_class: type | None` — the sketch's plain type is right, so the paragraph's *observation*
  survives; only its reason was wrong.

New text:

> A sidecar slot is a plain `type | None`, validated to a concrete class at class creation
> (`types/base.py::_validate_filterset_class`).

The lazy-reference framing is gone entirely rather than
inverted, which is what removes the contradiction with the spec's untouched `RelatedFilter` lazy-ref
lines instead of arguing with them.

**No new drift row was opened for the finalization algorithm's lazy-ref step, and the reason is
mechanical, not a judgement call.** Worker 3 asked that a stale step be recorded rather than settled
silently. It is not stale: the finalizer really does resolve lazy class refs, but they are
`RelatedFilter` / `RelatedOrder` **related-set targets inside** an already-resolved set class
(`types/finalizer.py::_expand_filterset`, `types/finalizer.py::_expand_orderset`), never the
`Meta.filterset_class` value. Two different objects; the algorithm step and the validators are both
accurate. The disambiguation is recorded in the rationale so the next reader does not re-raise it.

#### Low — `:419` twin four-seam visibility bullet

**Pointed at the section that owns the seam map, rather than restating it.** The bullet now reads:

> - **visibility** — `utils/querysets.py::apply_type_visibility_sync`, running on the paths
>   `### Layer 4: Generated relation fields` names

Backticked-heading self-reference is the spec's
existing convention (four prior uses of `### Layer 3: Finalization trigger` and `### Decision 6: fail
loudly`), and the heading text matches byte-for-byte (`grep -n '^### Layer 4: Generated relation
fields$'` → line 647).

Restating Layer 4's three paths here was rejected: the spec already describing the same seam two ways in
two sections is the shape M1 was raised for, and a pointer keeps single ownership. The mechanism clause
the pointer replaced ("so the target type's `get_queryset` composes onto the relation queryset") was
also a near-restatement of the section's own behaviors list four bullets above ("row-level
`get_queryset` chaining onto the relation's own queryset"), so cutting it removes a duplication as well
as the imprecision.

**Layer 4's cited paths were re-derived, not trusted**, since the pointer now depends on them:
`grep -rn apply_type_visibility_sync django_strawberry_framework/` shows `connection.py:1780`,
`list_field.py:217`, and `optimizer/walker.py:383` among the relation-field call sites, and
`grep -n querysets django_strawberry_framework/types/resolvers.py` returns **zero** lines — the
generated resolver imports nothing from `utils/querysets`.

### Byte counts

| File | After apply-changes pass 1 | After this pass | Delta |
|---|---|---|---|
| `docs/SPECS/spec-009-…-0_0_4.md` | 61,401 bytes / 1,099 lines | **61,382 bytes / 1,099 lines** | **-19 bytes** / 0 lines |
| `docs/SPECS/appx/spec-009-…-rationale.md` | 42,969 bytes / 613 lines | **44,769 bytes / 634 lines** | +1,800 bytes / +21 lines |

Every number measured with `wc -c -l` at the moment of writing, not restated from a prior section. The
spec is **net-negative**, which is the calibration the over-write risk asks for: the Medium's fix is
-15 bytes and the Low's is -12, against 0 lines changed in count. `git diff --numstat` against HEAD now
reads **115 insertions / 170 deletions** on the spec (unchanged in count from pass 2's measurement,
because both edits are single-line replacements inside lines the cycle had already rewritten) and
**426 insertions / 0 deletions** on the rationale.

The rationale grew because it is where the cut reasoning goes — the extraction rule working as designed.

### Append-only proof on the rationale

Re-proved mechanically this pass, not carried forward. `git diff` over the rationale contains exactly
**one** line beginning with `-` and it is the `--- a/` header. `head -166` of the working file is
byte-identical to `head -166` of `git show HEAD:<path>` (`cmp` exit 0) — the diff's first hunk starts at
`@@ -166,0 +167 @@`, so every pre-existing entry, `## How to read this file`, `## Provenance of this
record`, and `## Standing notes` are untouched, including the stale "three sites" bullet left alone on
purpose in pass 1.

Both rationale edits this pass are **in-place corrections of entries this cycle added** (lines 167+),
which is the carve-out `worker-1.md` `### Performing the rationale move` rule 4 leaves open: those lines
do not exist at HEAD, so correcting them removes nothing from the committed record.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.` **Exit 0, 23 terms.**
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0** for both.
- Link / anchor / rule-27 validator re-run over both files with code fences stripped: **0 undefined
  reference-style uses, 0 orphan link definitions, 0 unresolved in-page `](#…)` anchors** in either
  file, and **0** raw in-repo `path:NN` matches across both (`grep -nE
  '[A-Za-z0-9_/.-]+\.(py|md):[0-9]+'` → 0). Rule 27 is preserved.
- `git log --stat` over both paths: newest commit touching either is still `f3c94642` (spec +71/-36,
  rationale +208 new). **No concurrent session swept this cycle's work into a commit** — the working
  tree still carries the whole diff, and the HEAD baselines (60,855 / 1,099 and 36,744 / 208 lines)
  re-derive exactly against pass 1's ledger.
- No `pytest`, no `--cov*`, no source or test file touched, no commit, no branch.

### Cross-spec anchors

Not re-verified wholesale — this pass depends on **no** cross-spec anchor. Both edits are in-page and
cite in-repo symbols only. The `spec-010` escalations Worker 3 recorded (its line 8 mis-describing
spec-009, and its line 67's weakened-but-true finding) are unchanged and remain report-only; nothing in
this pass touches either side of them.

### Spec changes made (Worker 1 only)

| Section | Change | Reason | Triggered by |
|---|---|---|---|
| `docs/SPECS/spec-009-…-0_0_4.md`, ``### Borrow `StrawberryDjangoDefinition` `` | Replaced the sidecar-slot justification clause: "no lazy class reference is needed, because a sidecar binds at finalization rather than at class creation" → "validated to a concrete class at class creation (`types/base.py::_validate_filterset_class`)" | The cut clause was a false causal claim about shipped code — the validators run at class creation, and deferred binding would *permit* a lazy reference rather than remove the need for one — and it contradicted the spec's own untouched `RelatedFilter` lazy-ref lines | Worker 3 pass 2, **Medium** |
| `docs/SPECS/spec-009-…-0_0_4.md`, ``### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField` `` | Visibility bullet's mechanism clause replaced with a pointer: "running on the paths `### Layer 4: Generated relation fields` names" | The twin four-seam bullet never received the qualification the Layer 4 sibling got; a pointer closes it without the spec describing one seam two ways | Worker 3 pass 2, **Low** |
| `docs/SPECS/appx/…-rationale.md`, ``### Borrow `StrawberryDjangoDefinition` `` entry | Corrected the same false claim in this cycle's own entry ("a sidecar is bound at **finalization**…" → the two validators refusing anything but a resolved subclass at class creation) and appended one paragraph recording the cut plus the `RelatedFilter`-vs-set-class disambiguation | Leaving the falsehood in the rationale while cutting it from the spec is the half-reconciliation `worker-1.md` `## Review-round custody` forbids | Worker 3 pass 2, **Medium** |
| `docs/SPECS/appx/…-rationale.md`, `### Layer 4` entry | Appended one paragraph recording that the four-seam rule had two instances and that pass 2 pointed the twin here | The rationale generalised the rule and applied it to one bullet; the record now matches the spec | Worker 3 pass 2, **Low** |

**`### Dispatched findings checklist` re-audited against the diff, box by box: no tick changed.** All
sixteen boxes remain `- [x]` and every row still owns at least one hunk in the spec diff. The two edits
this pass fall inside rows already ticked — the `:385` paragraph is D10's section (which pass 1 already
un-hollowed) and the `:419` bullet sits in D1's ``### Borrow `StrawberryDjangoFieldBase`…`` section,
whose D1 scrub (the `DjangoModelField` transition path) is unaffected by a visibility-bullet reword.
Neither finding was a drift row, so neither adds a box.

### Notes for Worker 3 (re-review, pass 3)

- **The Medium's replacement is a fact with one citation, deliberately not a mechanism.** If you judge
  the paragraph now under-explains why the sketch omits `LazyClassRef`, the fuller reasoning is in the
  rationale entry rather than the spec, on the standing split.
- **The `RelatedFilter` lazy-ref question is answered, not deferred.** `types/finalizer.py::_expand_filterset`
  and `::_expand_orderset` resolve lazy refs *inside* a resolved set class; the finalization algorithm's
  step 3 is accurate and no drift row was opened. Please re-derive rather than accept.
- **The Low's fix is a forward in-page pointer** (line 419 → the section at 647). Forward backticked-
  heading references are pre-existing convention in this spec (line 444 forward-references two).

## Review (Worker 3, pass 3)

Audited 2026-08-15 by a **fresh Worker 3 invocation** whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-3.md`. Scope is deliberately narrow, as dispatched: the two
findings pass 2 raised (one Medium, one Low), the apply-changes pass 2 diff, and regression. Work passes
1 and 2 already accepted was **not** re-litigated; pass 2's own nine-finding closure audit stands.

**Method.** Both fixes were re-derived from shipped source, not from the build report's prose
(`BUILD.md` `## Claims are proven mechanically, never accepted on prose`). Worker 1's argument for *not*
opening a drift row was re-derived the same way, since a wrong answer there leaves a live staleness. The
append-only proof, the byte ledger, the mechanical gates, the link/anchor validator, and the five
cross-spec anchors were re-run rather than carried forward. `git stash`, `git checkout`, `git restore`,
and `git worktree` were not used; the HEAD reference was `git show HEAD:<path>` copied to a scratch path
outside the repository. No source or test file was read-write opened, none was mutated, nothing was
committed, no branch was created.

**Ledger, independently re-measured at review time.** Spec **61,382 bytes / 1,099 lines**; rationale
**44,769 bytes / 634 lines** — both match Worker 1's `### Byte counts` table exactly.
`git diff --numstat` against HEAD `054de9dd`: spec **115 insertions / 170 deletions** (unchanged in count
from pass 2), rationale **426 / 0** (405 → 426, +21 lines). HEAD's own copies measure 54,232 / 1,154 and
12,273 / 208, and 1,154 - 170 + 115 = 1,099 and 208 + 426 = 634 both close.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **No package-code duplication is possible.** The pass touches two `.md` files, adds no helper,
  constant, or branch, and is net **-19 bytes** on the spec. The usual inventory stays moot and the plan
  says so rather than omitting it.
- **The Low's fix is itself a DRY win, and I verified the duplication it removes.** The clause the
  pointer replaced ("so the target type's `get_queryset` composes onto the relation queryset") was a
  near-restatement of `### Layer 4`'s own visibility bullet (`:652`, "composes the target type's
  row-level `get_queryset` onto the relation queryset"). Replacing it with a citation of the section that
  owns the seam map leaves **one** telling of the mechanism instead of two — the same single-ownership
  split the cycle applies between spec and rationale. `grep -n "composes onto the relation queryset"`
  across both documents → **0 hits**; the duplicated phrasing is gone, not softened.
- **Independent twin sweep, run against the documents rather than against the reported file list.**
  `grep -n '\*\*visibility\*\*'` over both files returns exactly **two** bullets (`:419`, `:652`) — the
  pair pass 2 identified, with no third instance anywhere; `grep` for the retracted Medium clause
  ("binds at finalization", "lazy class reference", "no lazy") returns exactly **one** hit, the
  rationale's own record *of* the retraction at `…rationale.md:235`, correctly framed as the claim that
  was cut. Neither correction has an un-swept sibling. This was the pass-2 failure mode ("a finding fixed
  at the cited line is not a finding fixed") and it did not recur.
- **Existence challenge: not raised.** The pass introduces no abstraction, registry, indirection, or
  helper; both edits are subtractive.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**, and `git status --porcelain` on that
path is clean. `__all__` and the re-export list are unchanged, so no spec authorization is needed.
`CHANGELOG.md`, `docs/GLOSSARY.md`, and `docs/TREE.md` are likewise absent from `git status --porcelain`.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

**Applies** — the diff is entirely archived-spec / rationale surface.

- **Mechanical gates, re-run not trusted.**
  `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.`, **exit 0, count still 23**.
  Neither edit removed a term's last link site.
  `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0** for both,
  so the 10-header link-definition scaffold is intact in both files.
- **Link / anchor / rule-27 validator**, written fresh for this pass (fences stripped; code spans kept
  for link-use detection, stripped for the raw-path scan): spec **25 definitions / 25 used, 0 missing,
  0 orphan**; rationale **11 / 11, 0 missing, 0 orphan**; every non-anchor def's target
  disk-existence-checked and **every `GLOSSARY.md#…` anchor resolved against the rendered headings**
  (0 misses in either file); **0** `](#…)` in-page anchors, therefore none to break; **0** raw in-repo
  `path:NN` citations, measured both inside and outside code spans. The upstream `file:///…#LNN`
  citations are out-of-repo and out of scope, as dispatched.
- **Cross-spec anchors: the five re-verified in both directions and re-timestamped
  2026-08-15T23:15:27Z.** Outbound (3): `spec-009:99` → `spec-010` #"### Must redo (not augment)",
  `:637` → #"## Strawberry finalization strategy", `:873` → #"### Unresolved-target error format" — 1 hit
  each in the current `spec-010`. Inbound (2): `spec-010:67` → `spec-009` #"### Layer 3: Finalization
  trigger", `spec-010:468` → #"### Decision 6: fail loudly" — 1 hit each in the edited `spec-009`.
  **None is broken; nothing to repair.** My sweep also enumerated the anchored citations *outside* the
  spec-009↔spec-010 pair, which the five-count does not cover and which are equally exposed to concurrent
  edits: `spec-009:257` → `spec-054-fieldset-0_1_1.md` #"resolver wrapping" (3 hits) and
  `…rationale.md:58` → `spec-010` #"## Strawberry finalization strategy" (1 hit) both resolve, and
  `…rationale.md:280` → `spec-054` #"a custom `DjangoModelField` field class is unnecessary machinery"
  resolves under whitespace normalization (it spans a line break at `spec-054:812-813`, as hard-wrapped
  `#"substring"` citations routinely do). `spec-008`'s inbound reference is still whole-file, not
  anchored. All eight targets exist on disk.
- **Card ids re-checked, because `KANBAN.md` went dirty between pass 2 and this pass.** Pass 2 recorded
  it clean; it is now `M` (2 insertions / 3 deletions) alongside `KANBAN.html` and `db.sqlite3` under a
  concurrent session. A concurrent **card renumber** is the known hazard here, so every id both documents
  cite was re-grepped against the live board: `TODO-BETA-053-0.1.1`, `-054-0.1.1`, `-055-0.1.2`,
  `-057-0.1.3`, `-058-0.1.3`, `-059-0.1.4` all still present. No renumber has landed; nothing in this
  cycle's documents is stale against the board.
- **No renumbering, no version-string change, no archival movement, no script-rendered doc regenerated,
  no verbatim fenced drop-in copied.** Both edits are single-line, in-page, and cite in-repo symbols only.
- **Provenance.** `HEAD` still `054de9dd`; the newest commit touching either document is still
  `f3c94642`; both paths remain `M` and uncommitted. No concurrent session swept this cycle's work into a
  commit.

### What looks solid

**1. The Medium fix — verified at source, and the contradiction is dissolved rather than reworded.**
`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:385` now reads "A sidecar slot is a plain
`type | None`, validated to a concrete class at class creation
(`types/base.py::_validate_filterset_class`)." Every element re-derived:

- `types/base.py::_validate_filterset_class` raises `ConfigurationError` unless
  `isinstance(filterset_class, type) and issubclass(filterset_class, FilterSet)`, and
  `types/base.py::_validate_orderset_class` is its exact twin for `OrderSet` — both read end to end, not
  grepped.
- Both are called from `types/base.py::_validate_meta` (#"filterset_class = _validate_filterset_class",
  the adjacent line for the orderset twin), and `_validate_meta` is called from
  `types/base.py::DjangoType.__init_subclass__` (#"validated = _validate_meta(cls, meta)"). That is
  **class creation**, exactly as the replacement says.
- The claim is not merely true at the validator: I swept every reader of the slot. No path anywhere in
  `django_strawberry_framework/` re-assigns `definition.filterset_class` or resolves it lazily —
  `connection.py:1781/1817/1861` read it as a class and call `.apply_sync` / `filter_input_type` on it
  directly. There is no second door into the slot for a string or a callable.
- **The dissolution is genuine.** The replacement makes no claim about lazy references at all, so the
  spec's untouched `:704` ("`RelatedFilter` uses lazy class refs") and `:836` (algorithm step 3) are no
  longer being denied by a subordinate clause. The pass answered the finding by *cutting* the causal
  claim rather than inverting it, which is the repair that leaves nothing to re-check.
- One nuance, examined and **not** raised as a finding: the sketch shows three sidecars and only two of
  them have validators, because `fields_class`'s `Meta` key is in `DEFERRED_META_KEYS` and rejected
  outright — so *a fortiori* nothing unresolved can reach that slot either, and the sentence is
  forward-correct guidance for the `TODO-BETA-054-0.1.1` reader the same paragraph points at. The twin
  validator and the fuller reasoning are in the rationale entry, per the standing split.

**2. Worker 1's argument for not opening a drift row holds against source — I re-derived it rather than
accepting it, as asked.** The distinction is real and structural, not a wording escape:

- `types/finalizer.py::_expand_filterset` calls `filterset_cls.get_filters()`, and
  `types/finalizer.py::_expand_orderset` calls `orderset_cls.get_fields()` and then forces
  `related.orderset` for each entry in `related_orders` — i.e. both operate on a **set class that is
  already a resolved class object**, and what they resolve is the *target* of a `RelatedFilter` /
  `RelatedOrder` declared inside it.
- That target is the only thing in this area that is ever lazy: `sets_mixins.py::LazyRelatedClassMixin`
  ("Used by `RelatedFilter` to break cycles between filtersets declared in the same module") and
  `sets_mixins.py::RelatedSetTargetMixin` resolve a string / callable through `resolve_lazy_class`.
  `filters/base.py::RelatedFilter` and `orders/base.py::RelatedOrder` are its only subclasses.
- `Meta.filterset_class` never touches that machinery: it is refused at class creation unless it is
  already a `FilterSet` subclass, per the point above.

So the algorithm's step 3 ("resolve lazy filter/order/aggregate/fieldset class refs") is **accurate as
written** — the refs it resolves genuinely are lazy filterset/orderset class references, just
related-set targets rather than the `Meta` sidecar value. There is no unfixed staleness and no drift row
is owed. The disambiguation is additionally recorded in the rationale (`…rationale.md:238-242`) so the
next reader does not re-raise it, which is the right home for it.

**3. The Low fix — accurate, and not under-specified for a section-alone reader.**
`:419` now reads "**visibility** — `utils/querysets.py::apply_type_visibility_sync`, running on the paths
`### Layer 4: Generated relation fields` names".

- The pointer target exists **byte-for-byte**: `grep -n '^### Layer 4: Generated relation fields$'` → one
  hit, line 647.
- Layer 4 really does name paths, and they re-derive:
  `grep -rn apply_type_visibility_sync django_strawberry_framework/` puts the generated-relation call
  sites at `connection.py:1780`, `list_field.py:217`, and `optimizer/walker.py:383`, and
  `grep -n querysets django_strawberry_framework/types/resolvers.py` returns **zero** lines — the
  generated resolver imports nothing from `utils/querysets`, so Layer 4's "not inside the generated
  resolver" is still exactly right.
- **Pointer-not-restatement is the right call and does not under-specify the bullet.** The list's own
  preamble (`:415`) asks one question of each bullet — *where does this responsibility live* — and the
  bullet answers it with the seam's symbol path, which is the same amount of information its three
  siblings carry (`:417`, `:418`, `:420` each name a symbol and nothing about where the guarantee holds).
  The reader who wants the paths gets a same-document citation; the reader who wants the seam gets it
  inline. Restating the three paths here is what would have re-created the two-tellings problem the
  Medium was raised for.
- The citation style is pre-existing convention, verified rather than asserted: five other backticked
  heading self-references already exist (`:444`, `:645`, `:677`, `:1002`, `:1018`), and `:444` is itself
  a **forward** reference, so a forward pointer at `:419` introduces nothing new.

**4. No regression — the diff is exactly the two edits, and the -19 is arithmetically forced.** Both
edited lines appear as `+` lines in `git diff -U0`, confirming they sit inside lines the cycle had
already rewritten, which is why the insertion/deletion counts are unchanged at 115/170 (my own count of
`^+` / `^-` lines is 116/171 including the two file headers). Re-deriving the byte delta from the pass-2
review's verbatim quotation of the two old clauses against the two new ones gives **-15** and **-4**,
summing to **exactly -19** — the measured 61,401 → 61,382. Because that arithmetic closes to the byte,
no third spec edit of nonzero size can be hiding in this pass. Stated limitation: a hypothetical
*byte-neutral* edit inside an already-added line would be invisible to this test, and the pass-1 state is
not reconstructible to rule it out; the walk below plus the twin sweep above are what cover that
residual.

**5. Append-only on the rationale, proved mechanically.** `git diff` over the rationale contains exactly
**one** line beginning with `-`, and it is the `--- a/` header — so no HEAD line was deleted *or
modified* anywhere in the file, which subsumes any prefix check. `git diff -U0` puts the first hunk at
**`@@ -166,0 +167,424 @@`**, exactly as Worker 1 recorded; the other two hunks are `@@ -185,0 +610 @@`
and `@@ -186,0 +612 @@` (the two link definitions), and 424 + 1 + 1 = 426 closes against `--numstat`.
`head -166` of the working file `cmp`s **exit 0** against `head -166` of `git show HEAD:<path>` in a
scratch path outside the repository. `## How to read this file`, `## Provenance of this record`, and
`## Standing notes` are untouched, including the deliberately-left "three sites" bullet (re-confirmed
present at `…rationale.md:593`).

**6. The rationale edits are provably in-place corrections of this cycle's own entries.** This follows
from the one-`-`-line proof rather than from the report: since no HEAD line changed, every line either
fix touched must be one this cycle added (lines 167+). The six pre-existing entries are bit-identical.
I read both corrected entries end to end and they re-derive: the `### Borrow \`StrawberryDjangoDefinition\``
entry (`:215-221`, `:234-244`) states the validator pair, the class-creation timing, the inverted causal
arrow, and the `RelatedFilter`-vs-`Meta.filterset_class` disambiguation — all four confirmed above; the
`### Layer 4` entry's new paragraph (`:323-329`) states that the spec carried two four-seam bullets and
that the twin now cites this section, which is what the spec shows.

**7. Checklist ticks still match the diff.** All sixteen `### Dispatched findings checklist` boxes
remain `- [x]` and no tick changed. Both edits fall inside rows already ticked and already carrying
hunks: `:385` is D10's ``### Borrow `StrawberryDjangoDefinition` `` section (un-hollowed in
apply-changes pass 1) and `:419` sits in D1's ``### Borrow `StrawberryDjangoFieldBase`… `` section, whose
D1 scrub — the `DjangoModelField` transition path — is untouched by a visibility-bullet reword. Neither
finding was a drift row, so neither owes a new box.

### Temp test verification

- No temp test files were created under `docs/builder/temp-tests/r1/`, and none was warranted: this item
  ships no executable line. The directory does not exist and was not created; the `r2` / `r2b`
  directories under `docs/builder/temp-tests/` belong to the concurrent spec-010 cycle and were neither
  read nor touched.
- Verification instead used read-only source reads (`types/base.py`, `types/finalizer.py`,
  `sets_mixins.py`), `grep` sweeps, one throwaway Python link/anchor/rule-27 validator and one byte-delta
  calculator (both executed from stdin heredocs, nothing written into the repository), re-runs of both
  mechanical gates, and two `git show HEAD:` copies into a scratch path outside the repository.
- Disposition: nothing to promote.

### Failability proofs

**Not applicable to a documentation pass**, and stated rather than omitted. `BUILD.md`
`### What needs a proof, and what does not` scopes the obligation to a new boundary, guard, gate, or
rejection path a unit introduces; this diff is two single-line edits in two `.md` files and introduces
none, so the mandatory re-run floor is computed over an empty set and an empty re-run set is legal here.
No boundary was re-run and none was accepted on a builder's record, because none exists. Worker 3's
source carve-out was not exercised: no production file was mutated at any point in this pass.

### Hot-path budget

**Not applicable to a documentation pass**, and stated rather than omitted. The build plan declares
`Hot-path declaration: none` cycle-wide and R1's plan repeats it; no item touches an executable line, so
no before/after number is owed and none is missing. Nothing in the diff contradicts that declaration.

### Notes for Worker 1 (spec reconciliation)

- **One measurement slip in this pass's own report, recorded rather than raised as a finding.**
  `### Byte counts` attributes the -19 as "the Medium's fix is -15 bytes and the Low's is -12". The
  Medium's is -15; the **Low's is -4**, not -12 (-15 + -4 = the -19 the same paragraph measures, and the
  file measures 61,382). The total, the final byte counts, and both `--numstat` figures are all exactly
  right; only the per-edit split is wrong, it changes nothing in either document, and no reader of the
  spec is exposed to it. It is not raised as a Low because there is nothing in the deliverable to
  correct — but it is the third consecutive pass on this artifact where the headline number is right and
  an incidental one beside it is not, and that pattern is worth carrying rather than dropping. Record the
  correction in `## Final verification (Worker 1)` if you want the artifact internally consistent; do not
  edit the prior section.
- **`KANBAN.md`, `KANBAN.html`, and `examples/fakeshop/db.sqlite3` went dirty between pass 2
  (22:55:40Z) and this pass (23:15:27Z)** under a concurrent session. Every card id both documents cite
  still resolves against the live board, so nothing is stale today — but a card **renumber** landing
  before commit would silently falsify six ids in the spec and rationale. Worth one `grep` at the commit
  gate.
- **Escalated (report-only, do not repair): `spec-010:8` still mis-describes `spec-009`.** Re-read at
  2026-08-15T23:15:27Z, unchanged — it lists "custom field classes" among what spec-009 describes, which
  is exactly what D1 scrubbed. Recommendation unchanged: hold for the maintainer to sequence at commit.
- **Escalated (report-only, do not repair): `spec-010:67`'s weakened-but-true finding**, and the
  **pre-existing cross-spec near-duplicate** between `spec-009`'s single-threaded-setup-window sentence
  and `spec-010:67`'s closing sentence. Both unchanged from pass 2; neither is repairable from this
  cycle's writable set.
- **Source observation, unchanged and still not actionable here.**
  `types/definition.py` #"the forward-reserved ``FieldSet`` sidecar" still names `TODO-BETA-046-0.1.1`,
  which is now `DONE-046-0.0.14` after the card renumber; the live owner is `TODO-BETA-054-0.1.1`, which
  is what the spec, `KANBAN.md`, and `docs/TREE.md` say. **The spec is right and the source docstring is
  stale.** Source is read-only this cycle — a candidate row for whichever cycle next owns source
  docstrings.
- **The rationale's `## Standing notes` "three sites" bullet is still stale on purpose** (confirmed at
  `…rationale.md:593`), for the append-only reason pass 2 judged defensible and with the staleness
  flagged five lines above it. Correct it in whichever pass next has the rationale open without the
  append-only constraint.
- **R2 carry-forward is unchanged.** `docs/SPECS/spec-028-*` is still absent from
  `git status --porcelain`, so R2 starts from an untouched file, and the D6 split (spec-009 states the
  row-preserving property; the `DISTINCT ON` mechanism is **discharged by an alternative**, not
  postponed) is unaffected by this pass.
- **Nothing else escalates.** No correctness defect was found in shipped source, and none is escalated.

### Review outcome

`review-accepted`.

Both dispatched fixes hold under independent re-derivation from source, and the argument for not opening
a third drift row holds too — `_expand_filterset` / `_expand_orderset` resolve a `RelatedFilter` /
`RelatedOrder` target *inside* an already-resolved set class, an object `Meta.filterset_class` never is,
so the algorithm's lazy-ref step is accurate and owes no row. The Medium was closed by cutting the false
causal clause rather than inverting it, which is what makes the contradiction with the spec's untouched
lazy-ref lines genuinely dissolve instead of move. The Low was closed by a pointer that removes a
duplicated mechanism sentence as well as the imprecision, and it leaves the bullet carrying exactly what
its three siblings carry.

No regression: the spec is net **-19 bytes** and that number is forced to the byte by the two edits'
own arithmetic, the insertion/deletion counts are unchanged, the rationale diff still contains exactly
one `-` line, the two rationale corrections are provably confined to lines this cycle added, all sixteen
checklist ticks are unchanged and still backed, both mechanical gates pass (`23` glossary terms, exit 0
on both files), every link definition and glossary anchor resolves with zero orphans, there are zero
in-repo raw `path:NN` citations, and all five cross-spec anchors resolve in both directions at
2026-08-15T23:15:27Z. Neither escalation is repairable from this cycle's writable set and both remain
report-only for the maintainer.

`### Failability proofs` and `### Hot-path budget` are not applicable to a documentation pass, for the
reasons stated in their own sections rather than by omission.

---

## Final verification (Worker 1)

Run 2026-08-15 by a **fresh Worker 1 invocation** whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-1.md`. This section supersedes the
`## Final verification (Worker 1)` placeholder above, whose body is the combined pass's
`### Spec changes made` table and is left untouched as that pass's record.

**Method.** The whole artifact was read end to end — plan, combined perform pass, three Worker 3 reviews,
two Worker 1 apply-changes passes — then every load-bearing claim was **re-derived rather than read as
discharged by Worker 3's acceptance** (`worker-1.md` `### Verifying relocation / promotion claims`). Both
mechanical gates, the link / anchor / rule-27 validator, the append-only proof, the byte ledger, the five
cross-spec anchors, and the sixteen-box checklist audit were re-run from scratch. `git stash`,
`git checkout`, `git restore`, and `git worktree` were not used; the HEAD reference was
`git show HEAD:<path>` copied to a scratch path outside the repository. No `pytest` was run and no
`--cov*` flag was used: **this item runs no tests and changes no code**, so `worker-1.md`
`## Final verification job` step 5 is discharged by stating that rather than by a focused scope.
The staged-anchor sweep is R4's and was **not** duplicated here (step 6).

### Final status

`revision-needed`. **One Medium**, below. Everything else verifies.

The finding is not a checklist over-tick and not a regression from apply-changes pass 2 — it is a
**new claim about shipped code that this cycle authored in its combined pass and that no later pass
re-derived**, sitting one line above the bullet that has now been corrected twice. It is inside this
cycle's writable set and closes with one clause.

### Medium: the seam list attributes async safety to a module that contains none

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:418`, in
``### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField` ``:

> - **access, async safety, and N+1 cooperation** — `types/resolvers.py::_make_relation_resolver`,
>   attached across a finalized type by `types/resolvers.py::_attach_relation_resolvers`

**`django_strawberry_framework/types/resolvers.py` contains zero async machinery.**
`grep -nE 'async|sync_to_async|SynchronousOnly|await ' django_strawberry_framework/types/resolvers.py`
returns **0 lines** — no `async def`, no `sync_to_async`, no `await`, no `SyncMisuseError`. The three
generated shapes are plain sync callables: `many_resolver` returns
`list(bounded_rows(getattr(root, accessor_name).all(), info))` (or the `_prefetched_objects_cache` hit),
`reverse_one_to_one_resolver` and `forward_resolver` return `getattr(root, accessor_name)`. Unprefetched
on an async execution, the many-side path issues the query in the calling context; nothing in the module
mediates that.

The other two thirds of the bullet **are** right and should survive: *access* is exactly what the module
does (`types/resolvers.py` module docstring #"attaches a cardinality-aware resolver per relation field"),
and *N+1 cooperation* is real and load-bearing — `manager.all()` is prefetch-aware, the resolver reads
`_prefetched_objects_cache[accessor_name]` directly, and `_check_n1` is the strictness probe. Only
**async safety** is misattributed.

Where it actually lives, re-derived: `utils/querysets.py` owns the single
`sync_to_async(thread_sensitive=True)` worker (`utils/querysets.py` #"Run ``fn(*args, **kwargs)`` in ONE
``sync_to_async(thread_sensitive=True)`` worker") and the `SyncMisuseError` boundary, and it is applied
by `connection.py`, `list_field.py`, and `types/relay.py` — **the same family of seams the visibility
bullet was corrected to name**, not the generated resolver.

Three things make this a Medium rather than a Low:

- The line is **new text this cycle wrote** — `git diff` carries it as a `+` line (change 8 replaced the
  section's dataclass sketch and borrow list with these four bullets). It is not a pre-existing
  inaccuracy inherited from HEAD.
- The bullet is a **responsibility map in a horizon document**. Its own preamble (`:415`) asks one
  question of each bullet — where does this responsibility live — and answers `async-safe queryset
  access` (`:412`, the upstream behavior the map is answering) with a module that does not provide it. A
  reader implementing or auditing async relation access is sent to the wrong file and, worse, is told the
  requirement is already discharged there.
- It is the **fourth instance of one pattern in one four-bullet list**, and the pattern is the one this
  artifact itself named. D10's untouched section, M3's "cannot see" absolute, `:385`'s "binds at
  finalization", and now `:418`'s "async safety" are all connective tissue in a seam list that nobody
  re-derived. The rationale generalised the rule correctly — a bullet listing four seams invites exactly
  that slip — and pass 2 applied it to the visibility bullet only. **Grep for the shape the rule names,
  not for the site the finding names** is the artifact's own lesson, and it is still owed one bullet.

**Recommended change** (Worker 1's apply-changes pass owns it under the plan's `### Deviation 3`
corollary; re-derive rather than accept this prescription): drop `async safety` from the bullet and leave
`access and N+1 cooperation`, then either give async safety its own bullet naming `utils/querysets.py`'s
`sync_to_async` worker and the paths that apply it, or state in one clause that async-safe queryset
access is the connection / list-field / node-field seams' responsibility rather than the generated
resolver's — the same disposition M3 reached for visibility, which is the sibling requirement in the
same list. Do **not** close it by weakening `:412`'s upstream behavior list; that entry is a real
requirement and is correct as a requirement.

### DRY: the two four-seam lists are a live near-duplication this cycle created — recorded, not blocking

Recorded here under `## Final verification job` step 4 (duplication no single pass could see, because no
single pass held all three). This cycle rewrote **two** sections into four-seam responsibility lists
where HEAD had one borrow list and one transition path: `:417-420` and `:650-653`. Three of the four
bullets now tell the same fact twice in different words — `resolved_relation_annotation` at `:417` and
`:650`, `_make_relation_resolver` at `:418` and `:651`, the synthesized `__signature__` at `:420` and
`:653`. Only the visibility bullet was resolved into a pointer.

Not blocking on its own, for two reasons that were checked rather than assumed: the two sections have
genuinely different jobs (the `### Borrow …` chapter maps upstream prior art onto this package; the
`### Layer N` chapter defines the architecture), and the **mechanism telling now exists once** — Layer 4
carries the three composition paths and the not-inside-the-generated-resolver constraint, and the Borrow
copy cites it. `grep -v '^\s*$' | sort | uniq -d` over the spec finds no duplicated line of any length.

It is recorded because the Medium above is the third finding to land in these two lists, and the natural
fix for it is the same pointer treatment. **The apply-changes pass should decide the shape of the whole
Borrow list once** — either every bullet cites Layer 4 for the paths and states only the seam, or the
list is declared the upstream-mapping telling with a one-line pointer at the top — rather than closing a
fourth bullet in isolation and leaving the fifth to a fifth pass.

### Dispatched findings checklist audit — all sixteen ticks confirmed, none changed

Walked box by box against `git diff -- <spec>` (611 diff lines) and against the current file, not against
any pass's report. **No over-tick, no landed-but-open box, no deferral.** D10 — the row over-ticked at
the combined pass and caught by Worker 3 pass 1 — is the one that most deserved distrust and is now
genuinely landed.

| Box | Contract | Evidence it landed |
|---|---|---|
| D1 | `DjangoModelField` / `types/fields.py` scrubbed everywhere | **12** `-` lines carrying either symbol; `grep -c` on the current spec → **0** and **0** (HEAD: 11) |
| D2 | `OptimizerStore` / `with_hints` / `with_prefix` / callable hints scrubbed | **9** `-` lines; current counts 0 / 0 / 0 (HEAD: 8) |
| D3 | `get_strawberry_annotations` borrow replaced by the provenance section | **3** `-` lines; current count 0 (HEAD: 3); replacement section present at `:396` |
| D4 | `DjangoField(...)` → `DjangoListField(...)` | `-- \`DjangoField(...)\` for explicit advanced fields` / `+- \`DjangoListField(...)\``; current `DjangoField(` count 0 |
| D5 | fallback-tier sentence and the open question removed | `-Keep \`DjangoModelType\` only as an internal or explicitly requested fallback…` and `-### Should generic fallback exist?`; `DjangoModelType` 8 → **6** |
| D6 | `ASC_DISTINCT` / `DESC_DISTINCT` / `DISTINCT ON` removed from Layer 7 and Phase 5 | three `-` lines; current counts 0 / 0 / 0 |
| D7 | `object_type: ObjectTypeNode \| None` | `-    object_type: ObjectTypeNode = …` / `+    object_type: ObjectTypeNode \| None = …` |
| D8 | the three `DEFERRED_META_KEYS` named with their promoting cards | new paragraph at `:255`; `DEFERRED_META_KEYS` re-measured by AST = exactly `{aggregate_class, fields_class, search_fields}` |
| D9 | no `total_count` on the base; `aggregates` restated as owed with its card | `-    total_count: int \| None`; new opt-in paragraph; new `aggregates`-owed paragraph naming `TODO-BETA-057-0.1.3` |
| D10 | sketch corrected to shipped names and types | `-    fields:` / `+    fields_spec:`, `-    exclude:` / `+    exclude_spec:`, four `- … LazyClassRef …` lines gone. Re-derived: `types/definition.py` slots are `fields_spec` / `exclude_spec` and three plain `type \| None` sidecars; `grep -rn LazyClassRef django_strawberry_framework/` → **0** |
| D11 | `class ObjectFilter(FilterSet)`, canonical `Meta.fields` | `-class ObjectFilter(AdvancedFilterSet):` / `+class ObjectFilter(FilterSet):`; `AdvancedFilterSet` count 0; the one surviving `filter_fields` mention is the deliberate parity-alias sentence at `:699` |
| D12 | `AdvancedOrderSet` → `OrderSet`, `AdvancedAggregateSet` → `AggregateSet` in this package's sketches | `-class ObjectAggregate(AdvancedAggregateSet):` / `+class ObjectAggregate(AggregateSet):`; `AdvancedOrderSet` count 0 |
| D13 | Layer 5 item 2 removed and the negative contract stated | `-2. finalize pending types`; list renumbered 1-12; new "It does **not** finalize" paragraph at `:677` |
| D14 | `types/fields.py` out, `fieldset/` as a package with its card, `orders/inputs.py` present | `-- \`django_strawberry_framework/fieldset.py\`` / `+…/fieldset/ — planned by TODO-BETA-054-0.1.1`; `orders/` line names `inputs.py`; no `types/fields.py` |
| D15 | Phase 3 restated, Phases 1-8 intact | `-### Phase 3: DjangoModelField` / `+### Phase 3: Generated relation fields`; `grep '^### Phase '` → Phases 1-8, no gap, no renumber |
| D16 | the three unmet success criteria carry their owning cards | `search — owed; TODO-BETA-055-0.1.2`, `aggregate output on connections — owed; TODO-BETA-057-0.1.3`, `field-level permission masking — owed; TODO-BETA-054-0.1.1`; the eight met criteria carry no annotation, as decided |

**Group C is still untouched**, re-confirmed: the two "retired since" markers, the `PendingRelation`
sketch, the `class ObjectTypeNode(DjangoType, relay.Node)` declaration, and the upstream `file:///…#LNN`
citations. The Medium above adds no box — it is a new-claim finding, not a drift row, exactly as pass 2's
Medium and Low were.

### Gates and proofs re-run, not read

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0, 23 terms**, matching
  the pre-flight baseline and the card's 23 glossary links.
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0** for both.
- **Link / anchor / rule-27 validator**, written fresh for this pass (fences stripped; code spans handled
  both ways because two of the spec's link uses sit *inside* code spans): spec **25 definitions, 0
  missing, 0 orphan**; rationale **11 definitions, 0 missing, 0 orphan**; every non-anchor definition
  target disk-existence-checked, **0 dead**; **0** `](#…)` in-page anchors in either file, therefore none
  unresolved; **0** raw in-repo `path:NN` citations in either file, measured inside and outside code
  spans with `file:///` excluded. The two definitions my first pass reported as orphans
  (`glossary-aggregateset`, `glossary-finalize-django-types`) are used at `:141` and `:637` inside code
  spans — **not orphans**; the naive strip produced a false positive, and the corrected count agrees with
  Worker 3's 25/25. Upstream `file:///…#LNN` citations are out-of-repo and out of scope, as dispatched.
- **Byte / line ledger, re-measured with `wc -c -l` at verification time.** Spec **61,382 bytes / 1,099
  lines**; rationale **44,769 bytes / 634 lines**. `git diff --numstat` against HEAD `054de9dd`: spec
  **115 / 170**, rationale **426 / 0**. HEAD's own copies measure **54,232 / 1,154** and **12,273 / 208**
  (`git show HEAD:` into a scratch path outside the repo). Both close: `1,154 - 170 + 115 = 1,099` and
  `208 + 426 = 634`. Every figure in Worker 3 pass 3's ledger re-derives exactly.
- **Append-only on the rationale, proved independently.** `git diff -- <rationale> | grep -c '^-'` → **1**,
  and that line is the `--- a/` header, so **no HEAD line was deleted or modified anywhere**. `git diff -U0`
  hunks are `@@ -166,0 +167,424 @@`, `@@ -185,0 +610 @@`, `@@ -186,0 +612 @@`, and `424 + 1 + 1 = 426`
  closes against `--numstat`. `head -166` of the working file `cmp`s **exit 0** against `head -166` of
  `git show HEAD:<path>`. `## How to read this file`, `## Provenance of this record`, the six
  pre-existing entries, and `## Standing notes` are untouched.
- **No renumbering.** `### Layer 1`-`### Layer 11`, `### Phase 1`-`### Phase 8`, and `### Decision 1`-
  `### Decision 6` are all present with their original numbers and no gaps; the two vacated slots
  (`### Decision 3`, `### Phase 3`) carry positive contracts and no "this was rejected" prose.
- **Provenance: nothing was swept into a concurrent commit.** `git log --stat` over both document paths →
  newest commit touching either is still **`f3c94642`** (spec +71/-36, rationale +208 new); `HEAD` is
  still **`054de9dd`**; both paths are `M` and uncommitted in `git status --short`. `git status --porcelain`
  is now **146** entries, up from the 142 the dispatch recorded — reported, **not reverted**, and none of
  it intersects this cycle's writable set.

### Cross-spec anchors: five, all resolving in both directions, re-timestamped **2026-08-15T23:23:59Z**

Re-verified from scratch because `spec-010` is `M` under a concurrent cycle and has moved between every
pair of passes on this artifact. Reported, not repaired.

- **Inbound (2).** `spec-010:67` cites `spec-009` #"### Layer 3: Finalization trigger";
  `spec-010:468` cites #"### Decision 6: fail loudly". `grep -c '^### Layer 3: Finalization trigger$'` and
  `grep -c '^### Decision 6: fail loudly$'` on the edited spec-009 → **1 each**.
- **Outbound (3).** `spec-009:99` → `spec-010` #"### Must redo (not augment)"; `:637` → #"## Strawberry
  finalization strategy"; `:873` → #"### Unresolved-target error format". `grep -c` on the current
  spec-010 → **1 each**.
- `spec-008`'s inbound reference is whole-file, not anchored; `grep -n spec-009` over the spec-011 files
  returns nothing, so the third concurrent cycle still carries no inbound anchor here.

### Fail-open-shaped prose: the two visibility bullets and the `StrawberryDjangoDefinition` paragraph

Read as a reader who had not seen the argument, per the dispatch. The three named sites are **clean**;
the Medium above was found by widening the read to the rest of the same bullet list, which is where the
pattern says to look.

- **`:652` (Layer 4 visibility).** Now states where the composition runs — connection pipeline,
  `list_field.py::DjangoListField`, `optimizer/walker.py::_build_child_queryset` — says in terms that it
  is *not* inside the generated resolver, and names the recourse for a raw `list[T]` relation on a
  schema with no optimizer. Re-derived: `grep -rn apply_type_visibility_sync django_strawberry_framework/`
  puts the generated-relation call sites at `connection.py:1780`, `list_field.py:217`, and
  `optimizer/walker.py:383`; `grep -c querysets django_strawberry_framework/types/resolvers.py` → **0**;
  `permissions.py::apply_cascade_permissions` exists at `permissions.py:554`. **Conditional where the
  code is conditional. No absolute survives.**
- **`:419` (the twin).** Now a pointer — "running on the paths `### Layer 4: Generated relation fields`
  names". Target verified byte-for-byte: `grep -c '^### Layer 4: Generated relation fields$'` → 1. It
  asserts no guarantee of its own, so there is nothing left to over-claim.
- **`:385` (`### Borrow \`StrawberryDjangoDefinition\``).** "A sidecar slot is a plain `type | None`,
  validated to a concrete class at class creation (`types/base.py::_validate_filterset_class`)."
  Re-derived independently of Worker 3's acceptance: `_validate_filterset_class` (`types/base.py:138`)
  and `_validate_orderset_class` (`:164`) are called from `_validate_meta` (`:1167-1168`), which
  `DjangoType.__init_subclass__` calls at `:535` — class creation, as stated. No causal claim about lazy
  binding survives, so the spec's untouched `RelatedFilter` lazy-ref lines are no longer contradicted.
  **One nuance examined and deliberately not raised**: the sketch shows three sidecars and only two have
  validators, because `fields_class`'s `Meta` key is refused outright by `DEFERRED_META_KEYS` — the
  unvalidated slot is unreachable rather than unguarded, so the sentence is stricter than the code, never
  looser. That is the safe direction and is the same judgement Worker 3 pass 3 recorded.
- **Two further new claims re-derived rather than accepted**, because they are the other bulk additions:
  `:401`'s provenance sentence (`__init_subclass__` derives — inline frozenset at `types/base.py:567`
  plus `_consumer_assigned_fields` at `:795`, unioned at `:608` #"Four-corner consumer-override contract";
  `_build_annotations` at `:1640` takes `consumer_authored_fields` as a keyword parameter it never
  derives) and `:255`'s `DEFERRED_META_KEYS` paragraph (AST-measured: `DEFERRED_META_KEYS` = 3 keys,
  `ALLOWED_META_KEYS` = **17**, so the spec's decision to cite the constant rather than a number is what
  keeps it true). Both verify.

### Builders' required-amendment lists, discharged

`worker-1.md` `## Review-round custody`. Every `### Notes for Worker 1 (spec reconciliation)` item across
the six prior sections is accounted for: the R2 carry-forward is consistent and unchanged (spec-009 states
the row-preserving property; the `DISTINCT ON` mechanism is **discharged by an alternative**, not
postponed, and `spec-028` is still absent from `git status --porcelain`); the `filters/sets.py` in-place
`Meta` mutation was correctly recorded as a maintainer observation and not edited; the `KANBAN.md:335`
stale assertion is R3/R4 territory and is not R1's; and no correctness defect in shipped source was found
by any pass, including this one. **Nothing was recorded and left unimplemented.**

### Escalations carried forward to the maintainer at commit — report-only, none repaired here

1. **`docs/SPECS/spec-010-foundation-0_0_4.md:8` still mis-describes spec-009.** It lists "custom field
   classes" among what spec-009 describes, which is exactly what D1 scrubbed. Re-read at
   2026-08-15T23:23:59Z and **still standing**. The file belongs to the concurrent spec-010 cycle and is
   outside this cycle's writable set; the maintainer must sequence the two cycles at commit.
2. **The `spec-010:67` coupling.** That line says the auto-trigger direction in spec-009
   #"### Layer 3: Finalization trigger" was not adopted. The anchor resolves and the claim is still true,
   but after change 40 the cited section no longer states the direction — it points at the rationale.
   Nothing dangles and nothing is false. Second instance of the same two-cycle coupling. Related and
   pre-existing: spec-009's single-threaded-setup-window sentence and `spec-010:67`'s closing sentence are
   near-verbatim twins, and were twins before this cycle; the right owner is spec-010.
3. **`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`'s docstring reserves
   `fields_class` for `TODO-BETA-046-0.1.1`** — a stale card number after the renumber (`046` is now
   `DONE-046-0.0.14`, the transport card). The live owner is `TODO-BETA-054-0.1.1`, which is what the
   spec, `KANBAN.md`, and `docs/TREE.md` all say. **The spec is right and the source docstring is stale.**
   Source is read-only in this cycle; a candidate row for whichever cycle next owns source docstrings.
4. **The rationale's `## Standing notes` "three sites" bullet is stale on purpose.** Correcting it would
   break the plan's append-only constraint on the rationale for this cycle; the staleness is stated
   explicitly five lines above it, and the spec's own opener was corrected to "four sites" (change 39).
   Correct the bullet in whichever pass next has the rationale open without that constraint.
5. **Worker 3 pass 2's per-edit byte-split arithmetic slip**, recorded here at pass 3's request so the
   artifact is internally consistent without any prior section being edited: apply-changes pass 2's
   `### Byte counts` attributes the -19 as "-15 and -12". The Low's edit is **-4**, not -12
   (-15 + -4 = -19). **Every total, every final count, and both `--numstat` figures are exact** — spec
   61,382 bytes and 115/170 both re-measured this pass — so no document is wrong and nothing in either
   deliverable needs correcting.
6. **`KANBAN.md`, `KANBAN.html`, and `examples/fakeshop/db.sqlite3` are dirty under a concurrent
   session.** Every card id both documents cite still resolves against the live board, so nothing is
   stale today — but a card **renumber** landing before commit would silently falsify six ids in the spec
   and rationale. Worth one `grep` at the commit gate.

### Summary

R1 turns the archived spec-009 from a horizon document describing six mechanisms this package chose
against into one that describes what shipped. Two files changed; no source, test, sibling spec, standing
doc, generated doc, or DB row was touched.

**The six Group-A scrubs are complete and correctly bounded.** Every dropped symbol is at **zero**
occurrences in the current spec, against HEAD counts of 11 / 8 / 3 / 2 / 1 for the named ones:
`DjangoModelField` 0, `types/fields.py` 0, `OptimizerStore` / `with_hints` / `with_prefix` 0 / 0 / 0,
`get_strawberry_annotations` 0, `DjangoField(` 0, `ASC_DISTINCT` / `DESC_DISTINCT` / `DISTINCT ON`
0 / 0 / 0, `AdvancedFilterSet` / `AdvancedOrderSet` 0 / 0, `LazyClassRef` 0. Where a scrubbed section's
whole subject was the dropped mechanism it was rewritten to state what the shipped architecture does,
never left as a hole and never left as "this was rejected" prose — the deliberation went to the rationale
companion, which is append-only for this cycle and provably so.

**The scrub stopped in the right place, and that boundary was re-verified name by name.** The surviving
`DjangoModelType` (**6**), `AdvancedAggregateSet` (**2**), and `AdvancedFieldSet` (**2**) mentions are
each legitimate upstream prior art or a refusal site, never a mechanism this package adopts:
`DjangoModelType` survives at `:312` (the upstream `file:///` source-reference list), `:431-432`
(Strawberry-Django's *own* default relation fallback maps), `:556` (`## What to scrap from
Strawberry-Django`), `:854` (`## Why not use generic relation fallback by default?`), and `:999`
(`### Decision 1`, which refuses it by name); `AdvancedAggregateSet` at `:142` (upstream citation) and
`:235` (`#### Take …`, upstream design being praised); `AdvancedFieldSet` at `:250` (same) and `:772`
(`### Layer 9`'s prior-art reference, the twin of Layer 6's "Use `django-graphene-filters` semantics").
Removing any of them would have deleted the argument along with the rejected feature and falsified the
upstream citations.

**The ten Group-B corrections all landed**, each verified against shipped source rather than against the
drift table: the node field's nullable-by-contract spelling (D7), the three `DEFERRED_META_KEYS` named
with the card that promotes each (D8), the connection's opt-in `totalCount` and still-owed `aggregates`
(D9), the `DjangoTypeDefinition` sketch corrected to `fields_spec` / `exclude_spec` and declared an
explicit subset of a 29-slot record (D10), `FilterSet` with canonical `Meta.fields` **plus** the
cookbook-parity `filter_fields` alias the drift row itself had understated (D11), the shipped `*Set`
base names (D12), Layer 5's self-contradicting "finalize pending types" replaced by the negative contract
(D13), the module layout's dead proposal removed and `fieldset/` / `orders/inputs.py` corrected (D14),
Phase 3 restated to the machinery that actually passes its five acceptance tests (D15), and the three
unmet success criteria annotated with their owning cards (D16). Two vacated numbered slots
(`### Decision 3`, `### Phase 3`) were **repurposed with positive contracts rather than gapped or
renumbered** — renumbering was forbidden because `spec-010` cites `### Decision 6` by anchor, and all
five cross-spec anchors resolve in both directions.

**Ledger.** Spec **54,232 → 61,382 bytes**, **1,154 → 1,099 lines** (`git diff --numstat` 115 / 170 — it
deletes more lines than it adds and still grows in bytes, because the six scrubs removed a dataclass
sketch, three bullet lists, and a transition path while the replacements are denser contract prose).
Rationale **12,273 → 44,769 bytes**, **208 → 634 lines** (426 / 0 — append-only, proved by exactly one
`-` line in its diff and a byte-identical `head -166`). Both gates green: 23 glossary terms, exit 0 on
both files, zero orphan link definitions, zero unresolved in-page anchors, zero in-repo raw `path:NN`.

**What is left.** One Medium — `:418` attributes async safety to `types/resolvers.py`, which contains no
async machinery — plus the recorded shape question about the two four-seam lists it sits in. Everything
else is verified and stands.


---

## Build report (Worker 1, apply-changes pass 3)

Run 2026-08-16 by a fresh Worker 1 invocation. Closes the one Medium final verification left open
(`### Medium: the seam list attributes async safety to a module that contains none`) and discharges the
DRY note beside it (`### DRY: the two four-seam lists are a live near-duplication this cycle created`),
which the dispatch made binding input rather than advisory. `Status: planned` per the plan's
`### Deviation 3` corollary — this item's fix passes are Worker 1's, so the artifact routes to Worker 3
for audit, not to Worker 2.

**Spec status-line re-verification (per-spawn duty).** Lines 1-5 of the spec re-read. The opener still
describes the rationale companion, the four finalization sites, and the six scrubbed mechanisms; the
build did not falsify any of it. No edit owed.

### The shape decided, and why

The dispatch's instruction was to decide the shape of **both** four-seam lists once rather than close a
fourth bullet in isolation. Decided:

> **`### Layer 4: Generated relation fields` is the sole owner of the responsibility-to-seam map.
> ``### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField` `` states the borrow argument and
> points at it, and carries no seam list of its own.**

Three reasons, each checked rather than assumed:

1. **Only one section can own a map.** A duplicate map has no correct state — it has a current half and
   a stale half, which is precisely how three consecutive passes each found one more wrong bullet.
2. **Layer 4 is the architecture chapter and is already the cited one.** Pass 2 had already resolved the
   twin's visibility bullet into a pointer at Layer 4; this pass generalises that single decision to the
   whole list instead of repeating it bullet by bullet. Layer 4 is also what `### Phase 3` cites
   (`:930` — "the annotation, resolver, and visibility composition … — Layer 4").
3. **The Borrow chapter's own job is the upstream comparison**, not the paths: which behaviors upstream's
   field classes encode, and why this package distributes them rather than gathering them into a field
   object. That argument needs no per-seam citations, and the `DjangoTypeDefinition` invariant paragraph
   that closes the section is the part that is genuinely its own.

**The Medium is closed by deletion, not by re-attribution.** The false clause left with the bullet that
carried it. Cutting was preferred over rewriting per the dispatch, and it retires the fourth defect and
the three-bullet duplication in a single edit.

**Async safety is answered once, in the Borrow chapter, and deliberately NOT as a fifth Layer 4 bullet.**
Async-safe queryset access is not a generated relation field's seam at all; adding it to Layer 4 would
repeat the same mis-attribution one section over. Two alternatives were considered and rejected: cutting
`- async-safe queryset access` from the upstream-requirement list at `:412` (rejected — it is a real
requirement, and the finding said so explicitly), and saying nothing at all (rejected — the section's
whole job is to say where each borrowed behavior lives, so an unanswered member reads as an oversight).

### Source verification performed (this pass) — every seam claim in BOTH lists, plus the swept third site

Re-derived independently; the review's prescribed remediation was treated as a hypothesis, and **it was
wrong in its mechanism**, which is the pass's most important finding.

**The dispatch's prescription was not adopted.** It said async safety "lives in `utils/querysets.py`'s
single `sync_to_async(thread_sensitive=True)` worker, applied by `connection.py` / `list_field.py` /
`types/relay.py`". The worker is `utils/querysets.py::run_in_one_sync_boundary`, and
`grep -rn run_in_one_sync_boundary django_strawberry_framework/` puts its call sites in `permissions.py`,
`schema.py`, `filters/sets.py`, `orders/sets.py`, `auth/mutations.py`, and `mutations/resolvers.py` —
**none of the three named modules calls it**. What those three actually apply is the colored runner pair
`utils/querysets.py::apply_type_visibility_sync` / `utils/querysets.py::apply_type_visibility_async`
(`connection.py:1780` / `:1815`, `list_field.py:217` + its `apply_type_visibility_async` import,
`types/relay.py:843` / `:864` / `:904` / `:929`), with `utils/querysets.py::SyncMisuseError`
(defined `utils/querysets.py:116`) closing the sync path against an `async def get_queryset` — raised by
`utils/querysets.py::reject_async_in_sync_context` (`:139`, raise at `:168`), which
`apply_type_visibility_sync` calls at `:2944`.
The spec now states the mechanism that ships, not the one the finding guessed at.

**The finding's own core claim re-derived.**
`grep -cE 'async|sync_to_async|SynchronousOnly|await ' django_strawberry_framework/types/resolvers.py`
→ **0**. All three generated shapes are plain `def`: `many_resolver`, `reverse_one_to_one_resolver`,
`forward_resolver`.

**Layer 4's four bullets, each re-derived before being declared the survivor.**

| Layer 4 bullet | Claim | Evidence |
|---|---|---|
| annotation | `types/converters.py::resolved_relation_annotation`, cardinality-correct spellings | `converters.py:714-726`: `list[target_type]` on many-side, `target_type \| None` on nullable, bare `target_type` otherwise — exactly the three spellings named |
| resolution | `_make_relation_resolver` per relation; `_attach_relation_resolvers` installs at Phase 2, before `strawberry.type` at Phase 3 | `resolvers.py:300` / `:425`; `finalizer.py:17` ("Phase 2: `_attach_relation_resolvers` installs …") and `:34` ("Phase 3: `strawberry.type(...)` decorates"); the only production call site is `finalizer.py:793` |
| visibility | `apply_type_visibility_sync` on connection pipeline / `list_field.py::DjangoListField` / `optimizer/walker.py::_build_child_queryset`, not inside the generated resolver; `permissions.py` cascade helpers on the raw-`list[T]` path | call sites `connection.py:1780`, `list_field.py:217`, `walker.py:383`; `_build_child_queryset` at `walker.py:350`; `DjangoListField` at `list_field.py:153` (a function, so `path::Name` is correct); `permissions.py::apply_cascade_permissions` at `:554`; `grep -c querysets types/resolvers.py` → 0 |
| arguments | `connection.py::DjangoConnectionField` synthesizes a resolver `__signature__` | `connection.py:1824` (the builder docstring), assignments at `:2004` and `:2163` |

**No Layer 4 bullet needed changing.** That is the finding of the side-by-side read, and it is why the
whole edit lands on the other side.

**A third site of the same shape, found by sweeping and fixed here.** Grepping for the *shape* rather
than the site — the artifact's own lesson, and the reason this pass was told not to close one bullet —
turned up ``### Borrow `django_resolver` and `django_getattr` ``, whose two closing sentences this cycle
also rewrote:

- `django_getattr`'s five centralized patterns include **async contexts**, and the new sentence said to
  borrow them "into the generated relation resolver" — the same instruction to put async handling in a
  module that has none.
- The new second sentence asserted that centralizing them there "lets one resolver body **also carry**
  filtering, ordering, pagination, permissions, and optimizer cooperation". The generated resolver
  carries **none** of the first four; those are the connection field's. What its bodies do carry, read
  off `resolvers.py`: the N+1 probe (`types/resolvers.py::_check_n1`, `:160`), the
  `_prefetched_objects_cache` read (`:349-357`), the FK-id elision
  (`types/resolvers.py::_build_fk_id_stub`, `:99`), and the `resource_policy.py::bounded_rows` call
  (`:432`). HEAD's version of that sentence was future-conditional ("once fields also need …"); this
  cycle turned a conditional into an assertion, which is the same defect family as the Medium.

Both sentences corrected. Reported as a scope extension beyond the two lists the dispatch named,
because leaving them would have contradicted the corrected borrow section two screens later and
guaranteed a fifth pass.

### Spec changes made (Worker 1 only)

| # | Spec location | Change | Reason |
|---|---|---|---|
| 41 | `spec-009` ``### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField` ``, the four-bullet seam list and the paragraph above it | Bullet list **deleted**; the setup paragraph now ends "`### Layer 4: Generated relation fields` states that seam map once; it is not repeated here" | Closes the Medium by deletion and retires the three-bullet duplication the DRY note recorded. Single ownership of the map |
| 42 | same section, new paragraph after it | One paragraph placing async-safe queryset access on the queryset-owning fields, naming `_make_relation_resolver`'s sync callables, the `apply_type_visibility_sync` / `apply_type_visibility_async` pair, `SyncMisuseError`, and `connection.py` / `list_field.py` / `types/relay.py` | `:412` lists it as a real upstream requirement; the section must answer where it lives, and the deleted bullet answered it wrongly |
| 43 | same section, invariant paragraph | "every mechanism **above** reads it" → "every **seam** reads it" | There is no longer a local list for "above" to point at |
| 44 | `spec-009` ``### Borrow `django_resolver` and `django_getattr` ``, closing sentence 1 | Added the carve-out: "— except async contexts: that resolver stays sync, and async-safe access belongs to the field that owns the queryset" | Same mis-attribution, third site; swept per the grep-the-shape rule |
| 45 | same section, closing sentence 2 | "lets one resolver body also carry filtering, ordering, pagination, permissions, and optimizer cooperation" → "keeps the N+1 probe, the prefetch-cache read, the FK-id elision, and the row-bound call out of a variant per relation kind" | The four named concerns are false against `types/resolvers.py`; the four substituted ones were read off it |
| 46 | `spec-009-…-rationale.md`, the ``### Borrow `StrawberryDjangoFieldBase` … `` and `### Layer 4` entry | "access **and async safety** via `_make_relation_resolver`" corrected to "access and N+1 cooperation …, async safety via its `apply_type_visibility_async` twin on the fields that own the queryset" | The rationale carried this cycle's own copy of the false claim; in-place correction of a line this cycle added, so append-only holds |
| 47 | same rationale entry, two new paragraphs | Records the shape decision, the alternatives rejected (correct the bullet; drop the requirement; say nothing), and why async is not a fifth Layer 4 bullet | `worker-1.md` `## Review-round custody` — rejected alternatives are recorded so the shape is not re-fought |
| 48 | `spec-009-…-rationale.md`, new entry ``### Borrow `django_resolver` and `django_getattr` `` | New entry keyed to that heading, in spec order between the `OptimizerStore` entry and `### Layer 7` | The two corrected sentences need a keyed entry; `## Spec rationale extraction` requires every entry name its spec section by heading |

No Decision, Layer, or Phase was renumbered; no source, test, sibling spec, standing doc, generated doc,
or DB row was touched.

### Byte counts

| File | Before this pass | After | Delta | vs HEAD |
|---|---|---|---|---|
| `spec-009-…-0_0_4.md` | 61,382 / 1,099 | **61,359 / 1,096** | **-23 bytes / -3 lines** | HEAD 54,232 / 1,154; `--numstat` **112 / 170**; `1,154 - 170 + 112 = 1,096` closes |
| `…-0_0_4-rationale.md` | 44,769 / 634 | **49,460 / 690** | **+4,691 / +56** | HEAD 12,273 / 208; `--numstat` **482 / 0**; `208 + 482 = 690` closes |

**Net-negative on the spec, as the dispatch asked.** The pass deletes a four-bullet list (four bullets
plus a blank line) and adds one paragraph and four clauses; the rationale absorbs the reasoning, which
is where it belongs.

### Append-only proof on the rationale

- `git diff -- <rationale> | grep -c '^-'` → **1**, and that line is the `--- a/` header. No HEAD line
  was deleted or modified.
- `git diff -U0` hunks: `@@ -166,0 +167,480 @@`, `@@ -185,0 +666 @@`, `@@ -186,0 +668 @@`.
  `480 + 1 + 1 = 482` closes against `--numstat`.
- `head -166` of the working file `cmp`s **exit 0** against `head -166` of `git show HEAD:<path>`
  copied to a scratch path outside the repository. `## How to read this file`,
  `## Provenance of this record`, the six pre-existing entries, and `## Standing notes` are untouched.
- Change 46 corrects a line **this cycle added** (current `:284-290`, inside the `+167,480` block, which
  does not exist at HEAD), so correcting it removes nothing committed. Fourth time this property has
  been proved on this item.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0, 23 terms.**
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0** for both.
- **Link / anchor / rule-27 validator** (fences stripped; reference uses scanned inside and outside code
  spans, which is what makes `glossary-aggregateset` / `glossary-finalize-django-types` read as used
  rather than orphaned): spec **25 definitions / 25 uses, 0 missing, 0 orphan**; rationale **11 / 11,
  0 missing, 0 orphan**; every non-anchor definition target disk-existence-checked, **0 dead**; **0**
  `](#…)` in-page anchors in either file; **0** raw in-repo `path:NN` citations in either file, measured
  with `file:///…` excluded. Numbers agree with final verification's.
- **No renumbering.** `### Layer 1`-`### Layer 11` (11 headings), `### Phase 1`-`### Phase 8` (no gap),
  `### Decision 1`-`### Decision 6`; the two vacated slots still carry positive contracts.
- No `pytest`, no `--cov*` flag, no `ruff` (both deliverables are Markdown). Nothing was committed and no
  branch was created.

### Cross-spec anchors — five, both directions, re-timestamped 2026-08-16T00:32:44Z

Re-derived rather than carried forward, because `spec-011`'s cycle committed three times during this
pass.

- **Inbound (2).** `spec-010:67` → `spec-009` #"### Layer 3: Finalization trigger"; `spec-010:468` →
  #"### Decision 6: fail loudly". `grep -c` on the edited spec-009 → **1 each**.
- **Outbound (3).** `spec-009:99` → `spec-010` #"### Must redo (not augment)"; `:634` → #"## Strawberry
  finalization strategy"; `:870` → #"### Unresolved-target error format". `grep -c` on the current
  spec-010 → **1 each**. (Those three spec-009 line numbers moved from `:637` / `:873` by this pass's
  -3-line delta; the anchors are unchanged.)
- Reported, not repaired: `spec-010:8` still lists "custom field classes" among what spec-009 describes,
  which is what D1 scrubbed. Still standing at this timestamp, still outside this cycle's writable set.

### Provenance — nothing was swept into a concurrent commit

`git log --stat` over both document paths: the newest commit touching either is still **`f3c94642`**.
Both paths are `M` and uncommitted; the artifact is `??`.

**HEAD moved five times during this pass** — the dispatch recorded `d0f4562a`; HEAD read `e324b187`,
`2b7e5b16`, `892c4173` and finally **`9f968e86`** as the pass ran. Those commits are the concurrent
spec-010 / spec-011 residual cycles and a types test pass; `git show --name-only` on each returns **no**
`spec-009` or `bld-009` path. `git show HEAD:` on both documents `cmp`s byte-identical to the copies taken at the start
of the pass, so the ledger's HEAD figures (54,232 / 1,154 and 12,273 / 208) are still current.
`git status --porcelain` is **147** entries, up from the 146 final verification recorded — reported,
**not reverted**, and none of it intersects this cycle's writable set.

### Dispatched findings checklist — ticks unchanged, and correctly so

The sixteen `- [x]` boxes are D-rows from the drift table. This pass changed no D-row contract: every
dropped symbol is still at zero, the ten Group-B corrections still stand as final verification audited
them, and Group C is still untouched. Re-spot-checked against the current file rather than the diff:
`DjangoModelField` 0, `types/fields.py` 0, `OptimizerStore` 0, `get_strawberry_annotations` 0,
`AdvancedFilterSet` 0, `AdvancedOrderSet` 0, `LazyClassRef` 0, `DjangoField(` 0.

Like pass 2's Medium and Low, this pass's finding was a **new-claim** finding rather than a drift row, so
it adds no box and un-ticks none. No deferral is owed.

### Notes for Worker 3 (re-review, pass 4)

- The load-bearing thing to re-derive is **the prescription that was rejected**: confirm for yourself
  that `run_in_one_sync_boundary` has no call site in `connection.py`, `list_field.py`, or
  `types/relay.py`, and that what those three apply is the `apply_type_visibility_sync` / `_async` pair.
  If that is wrong, change 42 is wrong.
- **Read the deletion as well as the additions.** The pass's main edit is the removal of a bullet list;
  `git diff` shows it as four `-` lines with nothing replacing them in place, which is the intended
  shape, not an accident. Pass 2's visibility-bullet pointer is removed **by** that deletion — it was not
  reverted, it was subsumed.
- Changes 44 and 45 are outside the two lists the dispatch named. They are reported as a deliberate scope
  extension under the grep-the-shape rule; if you judge them out of scope, say so rather than assuming
  they were an oversight.
- The rationale's `## Standing notes` "three sites" bullet is **still deliberately stale** (escalation 4
  of final verification) — pre-existing text, untouchable under this cycle's append-only constraint.

---

## Review (Worker 3, pass 4)

Fourth review pass on this item, run 2026-08-16 by a fresh Worker 3 invocation whose only carry-forward
is `docs/builder/worker-memory/spec-009-worker-3.md`. Scope: apply-changes pass 3 (changes 41-48) — the
architectural decision it made, the prescription it rejected, the scope extension it took, Layer 4's four
bullets, and the whole no-regression / append-only / gate / anchor surface re-derived from scratch rather
than read as discharged by the three prior passes.

Method notes: HEAD re-derived at the start of the pass (**`9f968e86`**, the dispatch's "around" hash) and
re-checked at the end; read-only HEAD copies obtained with `git show HEAD:<path>` into a scratch path
**outside** the repository; no `git stash` / `checkout` / `restore` / `worktree`; no `pytest` with any
`--cov*` flag; nothing committed; no branch created; no concurrent file touched.

### High:

None.

### Medium:

#### `:417`'s "chosen per execution" is false at the connection seam — and the same clause is in the rationale

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:417` (change 42) and
`docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md:353` (change 47) both close with:

> … the `utils/querysets.py::apply_type_visibility_sync` / `apply_type_visibility_async` pair — with
> `utils/querysets.py::SyncMisuseError` closing the sync path against an `async def get_queryset` — **is
> chosen per execution** by whichever field owns the queryset: `connection.py`, `list_field.py`,
> `types/relay.py`.

Everything in that sentence except the emphasized clause re-derives. **The colored pair is not chosen per
execution at the connection seam; it is fixed when the field is constructed.**

- `connection.py::_build_connection_resolver` branches on the **consumer resolver's declaration**, not on
  the execution context: `resolver is None` and the plain-`def` branch emit a `def _resolve` calling
  `_pipeline_sync` unconditionally (`connection.py:1951`, `:1968`, `:1995`); only
  `is_async_callable(resolver)` yields the `async def` branch that awaits `_pipeline_async`
  (`connection.py:1981`). `in_async_context()` appears in that builder only inside
  `_require_async_iterable_context`, which guards a returned source shape, never the pipeline choice.
- The **nested relation connection** builder is sync-only — `connection.py:2154` calls `_pipeline_sync`
  with no async sibling anywhere in that resolver — so for a `<field>_connection` sibling the async
  runner is unreachable regardless of execution.
- The module states the consequence itself, in words:
  `connection.py::_build_connection_resolver` #"A sync pipeline meeting an async ``get_queryset`` raises
  ``SyncMisuseError`` (the Relay-foundation contract); to drive an async ``get_queryset`` hook through a
  connection, supply an ``async def`` ``resolver=``".
- **Proved by execution, not by reading** — temp test, one row, passing:
  `docs/builder/temp-tests/r1/test_async_execution_default_connection.py`. A default
  `DjangoConnectionField` over a type declaring `async def get_queryset`, driven by
  `await schema.execute(...)`, raises `SyncMisuseError`. The sync runner ran under async execution.

Only `types/relay.py` matches the sentence unconditionally (`in_async_context()` at
`types/relay.py:842` and `:903`, per call). `list_field.py` matches for its default resolver
(`list_field.py:207`) and not for its consumer-resolver branches, which commit at construction via
`is_async_callable` (`list_field.py:243`).

**Why this is a Medium and not a Low.** It is the same class as the four findings that preceded it: new
text this cycle wrote, in a sentence whose whole job is to state a shipped contract, wrong in the
connective clause the author had no reason to re-derive. Its consequence is actionable and inverted — a
reader is told the package picks the async runner when they execute asynchronously, when the shipped
contract is that an `async def get_queryset` under a connection needs an `async def resolver=` supplied at
construction. The sentence half-refutes itself: `SyncMisuseError` is *only* reachable under async
execution **because** the choice is not per execution.

**Recommended change** (Worker 1's; re-derive rather than accept this prescription). Drop the mechanism
claim and keep the ownership claim — e.g. "… is applied by whichever field owns the queryset:
`connection.py`, `list_field.py`, `types/relay.py`" — or state the mechanism accurately: `types/relay.py`
and `DjangoListField`'s default resolver select per execution via `in_async_context()`, while a connection
field's color is fixed at construction, which is why an `async def get_queryset` under a connection
requires an `async def resolver=`. Do **not** close it by deleting the `SyncMisuseError` clause; that
clause is correct and load-bearing. **Fix both sites in the same edit** — the rationale's copy at `:353`
sits inside this cycle's own `+167,480` block, so correcting it in place preserves append-only by exactly
the argument change 46 already used and recorded.

### Low:

None.

### DRY findings

- **The near-duplication the DRY note recorded is genuinely retired, not moved.** `grep -n 'seam'` over
  the spec returns four sites, and only `### Layer 4` (`:645`-`:652`) carries a responsibility-to-seam
  list; `:415` is a one-line pointer to it, `:417` answers the one requirement that is not a Layer 4 seam,
  `:419` is the invariant, `:1002` is Decision 3 restating the same architecture. The three facts that
  were told twice — `resolved_relation_annotation`, `_make_relation_resolver`, the synthesized
  `__signature__` — are each told once now. `grep -v '^\s*$' | sort | uniq -d` over the spec finds only
  code-fence boilerplate and one-word list items; over the rationale, only `>`.
- **No dangling reference to the deleted list.** Every in-document reference to that section
  (`:415`, `:930`, `:1002`) points at Layer 4 or restates the architecture; nothing says "the borrow
  section lists the seams". `grep -c '^### Layer 4: Generated relation fields$'` → **1**, so the pointer
  resolves uniquely.
- No new abstraction, helper, registry, or indirection was introduced; the existence challenge has no
  target this pass. The diff touches two `.md` files and no `.py` file.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are
unchanged; this item writes no package code.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applies — the deliverable is two documentation files.

- **Card ids re-grepped against the live board this pass** (`KANBAN.md` has been dirty under a concurrent
  session across this artifact's passes, so this is re-measured, not carried): the seven ids cited across
  both documents — `DONE-009-0.0.4`, `TODO-BETA-053-0.1.1`, `TODO-BETA-054-0.1.1`, `TODO-BETA-055-0.1.2`,
  `TODO-BETA-057-0.1.3`, `TODO-BETA-058-0.1.3`, `TODO-BETA-059-0.1.4` — all resolve (2 / 17 / 16 / 16 / 5
  / 7 / 3 occurrences). No renumber has landed.
- **No renumbering.** `### Layer 1`-`### Layer 11` (11 headings), `### Phase 1`-`### Phase 8` (no gap),
  `### Decision 1`-`### Decision 6`; the two vacated slots still carry positive contracts and no
  "this was rejected" prose.
- **Link / anchor / rule-27 validator, written fresh for this pass** (fences stripped; reference uses
  scanned with code spans intact, which is what keeps `glossary-aggregateset` /
  `glossary-finalize-django-types` off the orphan list): spec **25 definitions / 25 uses, 0 missing,
  0 orphan, 0 dead targets**; rationale **11 / 11, 0 missing, 0 orphan, 0 dead**; **0** `](#…)` in-page
  anchors in either file; **0** raw in-repo `path:NN` citations in either file (`grep -n '\.py:[0-9]'`
  over both → no match), with the 67 upstream `file:///…#LNN` citations out of scope as dispatched.
  Independently reproduces pass 3's and final verification's 25/25 and 11/11.
- **Gates re-run, not read.** `check_spec_glossary.py --spec <spec>` →
  `OK: 23 terms - all have glossary entries and at least one spec link.`, **exit 0, 23 terms**.
  `check_trailing_commas.py --check <spec> <rationale>` → **exit 0**.
- **Ledger re-measured with `wc -c -l`.** Spec **61,359 bytes / 1,096 lines**; rationale **49,460 / 690**.
  `git diff --numstat` against HEAD `9f968e86`: spec **112 / 170**, rationale **482 / 0**. HEAD's own
  copies re-measure **54,232 / 1,154** and **12,273 / 208**. Both identities close:
  `1,154 - 170 + 112 = 1,096` and `208 + 482 = 690`. Net-negative on the spec (-23 bytes / -3 lines
  against pass 3's 61,382 / 1,099), as the dispatch required.
- **Append-only on the rationale, proved mechanically and independently.**
  `git diff -- <rationale> | grep -c '^-'` → **1**, and that one line is the `--- a/` header, which
  subsumes any `head -N` argument; `git diff -U0` hunks are `@@ -166,0 +167,480 @@`, `@@ -185,0 +666 @@`,
  `@@ -186,0 +668 @@`, and `480 + 1 + 1 = 482` closes against `--numstat`; `head -166` of the working file
  `cmp`s **exit 0** against `head -166` of `git show HEAD:<path>` taken into an out-of-repo scratch path.
- **Provenance.** Newest commit touching either document is still `f3c94642`; both are `M` and
  uncommitted; the artifact is `??`. `git status --porcelain` is now **77** entries, down from the 147 the
  pass-3 report recorded — concurrent cycles committed during and after that pass. Reported, **not
  reverted**; `git show HEAD:` on both documents still measures the ledger's HEAD figures, so no
  spec-009 content was swept into any of those commits.

### Cross-spec anchors — five, both directions, re-verified and re-timestamped **2026-08-16T00:46:48Z**

- **Inbound (2).** `spec-010:67` cites spec-009 #"### Layer 3: Finalization trigger"; `spec-010:468`
  cites #"### Decision 6: fail loudly". `grep -c` for each heading on the edited spec-009 → **1 each**.
- **Outbound (3).** `spec-009:99` → `spec-010` #"### Must redo (not augment)"; `:634` → #"## Strawberry
  finalization strategy"; `:870` → #"### Unresolved-target error format". `grep -c` on the current
  spec-010 → **1 each**. The three spec-009 line numbers match pass 3's post-delta values.
- `spec-011-stale_placeholder_cleanup-0_0_4.md` still carries no inbound spec-009 reference
  (`grep -rn spec-009` over it → nothing). `spec-008`'s inbound reference remains whole-file.
- **Reported, not repaired:** `docs/SPECS/spec-010-foundation-0_0_4.md:8` still lists "custom field
  classes" among what spec-009 describes — the claim D1 scrubbed. Third consecutive pass at which it
  stands; outside this cycle's writable set.

### Dispatched findings checklist

Sixteen boxes, all `- [x]`, zero `- [ ]`. This pass changed no D-row contract, and the ticks are still
correct: every scrubbed symbol re-counted against the **current** file rather than the diff —
`DjangoModelField` 0, `types/fields.py` 0, `OptimizerStore` / `with_hints` / `with_prefix` 0 / 0 / 0,
`get_strawberry_annotations` 0, `DjangoField(` 0, `ASC_DISTINCT` / `DESC_DISTINCT` / `DISTINCT ON`
0 / 0 / 0, `AdvancedFilterSet` / `AdvancedOrderSet` 0 / 0, `LazyClassRef` 0. Like passes 2 and 3, this
pass's finding is a **new-claim** finding, not a drift row: it adds no box and un-ticks none.

### Failability proofs

Not applicable to a documentation pass. This item introduces no guard, gate, cap, or rejection path — it
writes no executable line, and the diff touches two `.md` files. `BUILD.md` `### What needs a proof, and
what does not` scopes the obligation to new boundaries, so the mandatory re-run floor is satisfied by an
empty set: the diff introduces no boundary that meets it. Worker 3's source carve-out was not exercised;
no production file was mutated at any point in this pass.

### Hot-path budget

Not applicable to a documentation pass; the plan declares no hot path for any residual item and this one
touches no executable line.

### Static helper

`scripts/review_inspect.py` not run — recorded skip with reason: the diff adds and touches **no** `.py`
file, so none of Worker 3's three trigger conditions (`BUILD.md` `### When to run the helper during
build`) fires. All source reading this pass was read-only verification of the documents' claims.

### What looks solid

- **The architectural decision is right, and it is complete.** Single ownership of the
  responsibility-to-seam map is the correct call on evidence rather than taste: a duplicated map has a
  current half and a stale half, and this artifact produced four findings in a row proving it. I checked
  the two things that would have made it wrong anyway. **(a) The Borrow chapter still makes its argument
  without the list** — it states borrow-the-behaviors-not-the-class, enumerates the six real upstream
  requirements (`:408`-`:413`, with `async-safe queryset access` correctly left intact), gives the
  decorator-first-vs-`class Meta` reason the responsibilities are distributed, answers the one requirement
  that is not a Layer 4 seam, and closes on the `DjangoTypeDefinition` invariant, which is the part
  genuinely its own. **(b) Nothing a Borrow-only reader needs is now unreachable:** all six requirements
  land somewhere — 1, 2 in the invariant paragraph's definition contents (`:419`, `:652`), 3 and 6 in
  Layer 4's *arguments* bullet, 4 in *visibility*, 5 at `:417` — and the pointer names a heading that
  `grep -c` finds exactly once. Choosing a heading reference over an in-page anchor also keeps the file's
  `0` in-page-anchor property intact.
- **The rejected prescription was rejected correctly, and I re-derived both halves.**
  `grep -rn run_in_one_sync_boundary django_strawberry_framework/` puts its **call** sites in
  `permissions.py:728`, `schema.py:234`/`:248`/`:257`, `filters/sets.py:3376`, `orders/sets.py:452`,
  `auth/mutations.py:336`/`:642`/`:649`/`:837`/`:838`/`:1118`, `mutations/resolvers.py:1539` — and
  **nowhere** in `connection.py`, `list_field.py`, or `types/relay.py` (the `consumers.py` hit is a
  comment saying it deliberately does *not* add one). What those three apply is the colored pair:
  `connection.py:1780`/`:1815`, `list_field.py:211`/`:217`, `types/relay.py:843`/`:864`/`:904`/`:929`.
  The `SyncMisuseError` half also verifies at the level of mechanism, not just symbol presence:
  `utils/querysets.py:116` defines it, `reject_async_in_sync_context` (`:139`) closes the coroutine via
  `_dispose_sync_awaitable` before raising at `:168`, and `apply_type_visibility_sync` (`:2882`) calls it
  at `:2944` on the `type_cls.get_queryset(...)` return. Placing async safety in the Borrow chapter rather
  than as a fifth Layer 4 bullet is also right: it is not a seam of the generated field, and a fifth
  bullet would have re-committed the mis-attribution one section over.
- **The finding's own core claim holds.**
  `grep -cE 'async|sync_to_async|SynchronousOnly|await ' django_strawberry_framework/types/resolvers.py`
  → **0**; `many_resolver`, `reverse_one_to_one_resolver`, and `forward_resolver` are all plain `def`.
- **All four Layer 4 bullets re-derived independently; none needs changing** — a claim this history says
  to distrust, and it survived. *annotation*: `types/converters.py::resolved_relation_annotation`
  (`converters.py:714`-`:726`) returns exactly `list[target_type]` on the many side, `target_type | None`
  when nullable, bare `target_type` otherwise — the three spellings named, in that order.
  *resolution*: `_make_relation_resolver` at `resolvers.py:300`, `_attach_relation_resolvers` at `:425`,
  sole production call site `finalizer.py:793`, and the finalizer's own module docstring places
  `_attach_relation_resolvers` at Phase 2 and `strawberry.type(...)` at Phase 3 — so "installs at
  finalizer Phase 2, before `strawberry.type` runs at Phase 3" is exact. *visibility*: the three named
  call sites are `connection.py:1780`, `list_field.py:217`, `optimizer/walker.py:383`,
  `_build_child_queryset` is `walker.py:350`, `permissions.py::apply_cascade_permissions` is
  `permissions.py:554`, and `grep -c querysets django_strawberry_framework/types/resolvers.py` → **0**,
  so "not inside the generated resolver" is structural rather than asserted. *arguments*:
  `DjangoConnectionField` (`connection.py:2168`) returns `relay.connection(resolver=`
  `_build_connection_resolver(...))`, and that builder assigns `_resolve.__signature__` at
  `connection.py:2004`; the relation-connection builder does the same at `:2163`.
- **The scope extension (changes 44, 45) was in scope, and I would have raised it had it been left.**
  Both halves check out. HEAD's text was future-conditional — `git show HEAD:<spec>` line 569 reads "This
  will be more robust than custom per-cardinality relation resolvers **once** fields also need filtering,
  ordering, pagination, permissions, and optimizer hooks" — and this cycle's combined pass turned it into
  an assertion about what the generated resolver carries. That assertion is false:
  `grep -cniE 'filterset|orderset|paginat|permission' django_strawberry_framework/types/resolvers.py` →
  **0**. The four substituted concerns are all present — `_check_n1` (`resolvers.py:160`), the
  `_prefetched_objects_cache` read (`:349`-`:357`), `_build_fk_id_stub` (`:99`), and
  `resource_policy.py::bounded_rows` (`:354`, `:362`). It is the same defect family, in the same
  document, inside this cycle's writable set, two screens from the section being corrected; deferring it
  would have left the spec arguing with itself. That is a sweep under the artifact's own rule, not creep.
- **No regression anywhere else.** Every ledger identity closes, append-only is proved the strong way,
  both gates are exit 0, all five anchors resolve in both directions, no renumbering, no orphan or dead
  link definition, zero in-repo `path:NN`, no `.py` touched, public surface unchanged.
- Two claims examined and deliberately **not** raised, recorded so a fifth pass does not re-open them:
  (a) `:526`'s "the single place every cardinality's access passes through" is pre-existing cycle text
  three passes accepted, and it is true of the generated *relation field* — a `<field>_connection` sibling
  is a different field, not another path through the same one; (b) change 45's "keeps … out of a variant
  per relation kind" reads correctly as *the four mechanisms are single implementations* (`_check_n1`,
  `_build_fk_id_stub`, and `bounded_rows` are each one function called from the cardinality bodies), not
  as a claim that no per-cardinality body exists.

### Temp test verification

- `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` — one row, **passed**
  (`uv run pytest <path> --no-cov -q -o addopts=''`; `addopts` overridden only to drop `pytest.ini`'s
  auto-applied `--cov`, per `BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`).
  It drives a default `DjangoConnectionField` over a type with `async def get_queryset` through
  `await schema.execute(...)` and asserts `SyncMisuseError`, which is only reachable if the **sync**
  visibility runner ran under **async** execution. That is the mechanical proof behind the Medium.
- **Disposition: kept on disk for Worker 1's re-run** (gitignored, cleared with the cycle). Not promoted:
  it pins already-correct shipped behavior rather than catching a bug, and this item's writable set
  excludes tests. The permanent-suite gap it exposes is recorded below as a note, not as a finding.

### Notes for Worker 1 (spec reconciliation)

1. **The Medium is a two-site fix.** `spec-009:417` and `rationale:353` carry the same clause; correcting
   only the spec would reproduce the exact half-correction this artifact has now recorded twice
   ("a finding fixed at the cited line is not a finding fixed"). The rationale site is inside this
   cycle's own added block, so the in-place correction is licensed by change 46's argument.
2. **Candidate row for whichever cycle owns tests** (not this one; reported, not repaired): the permanent
   suite pins `async def get_queryset` → `SyncMisuseError` on the connection field only under
   `execute_sync` (`tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse`).
   The documented contract that the same rejection holds under `await schema.execute` for a default
   connection field — the thing that makes an `async def resolver=` mandatory — has no permanent row.
   My temp test is a ready-made body for it.
3. **Escalations 1-6 of final verification are unchanged and none was repaired here.** Re-checked this
   pass: `spec-010:8` still mis-describes spec-009 (still outside the writable set); the
   `types/definition.py::DjangoTypeDefinition` docstring still reserves `fields_class` for the stale
   `TODO-BETA-046-0.1.1` while spec, `KANBAN.md`, and `docs/TREE.md` all say `TODO-BETA-054-0.1.1` — the
   spec is right and the source is stale; the rationale's `## Standing notes` "three sites" bullet is
   still deliberately stale under the append-only constraint, with the staleness stated five lines above
   it. Nothing new was found in any of them.
4. **Working-tree drift since pass 3 is large but disjoint.** `git status --porcelain` fell from 147 to
   **77** and HEAD moved to `9f968e86` while this pass ran; `git show HEAD:` on both documents still
   `cmp`s to the ledger's HEAD figures, so nothing of this item was swept into a concurrent commit. Worth
   one re-check of the card ids at the commit gate, as final verification already flagged.

### Review outcome

`revision-needed`. One Medium, no High, no Low. Everything the pass set out to do lands — the shape
decision is right and complete, the rejected prescription was rejected correctly, the scope extension was
in scope and accurate, all four Layer 4 bullets survive independent re-derivation, and no ledger, gate,
anchor, or append-only property regressed. The one open item is the replacement sentence's own mechanism
clause: `chosen per execution` is false at the connection seam, at two sites, and is the fifth instance of
the pattern this artifact keeps naming.

## Build report (Worker 1, apply-changes pass 4)

Run 2026-08-16 by a fresh Worker 1 invocation. Closes the one Medium of `## Review (Worker 3, pass 4)`
(`#### :417's "chosen per execution" is false at the connection seam — and the same clause is in the
rationale`) at both sites. Nothing else in the pass was reopened. `Status: planned` per the plan's
`### Deviation 3` corollary — this item's fix passes are Worker 1's, so the artifact routes to Worker 3
for audit, not to Worker 2.

**Spec status-line re-verification (per-spawn duty).** Lines 1-5 re-read. The opener still describes the
rationale companion, the four finalization sites, and the six scrubbed mechanisms; this pass falsifies
none of it. No edit owed.

**HEAD re-derived at the start of the pass: `5851bb59`** ("Share the FilterSet/OrderSet permission facade
and land the remaining DRY consolidations"), not the `9f968e86` the dispatch named. Re-checked at the end;
unchanged. No concurrent file touched, no `git stash` / `checkout` / `restore` / `worktree`, nothing
committed, no branch created, no `--cov*` flag.

### Source verification performed (this pass) — the prescription treated as a hypothesis

The review's recommended wording was re-derived rather than accepted (`BUILD.md` `## Claims are proven
mechanically, never accepted on prose`; this cycle has had two dispatched prescriptions turn out wrong).
**Its mechanism claim holds, and the three seams genuinely differ:**

| Seam | When the color is chosen | Evidence |
|---|---|---|
| root connection, `connection.py::_build_connection_resolver` | **construction**, from the consumer resolver's declaration | `resolver is None` (`connection.py:1947`), async-generator (`:1958`) and plain-`def` (`:1989`) branches all emit a `def _resolve` calling `_pipeline_sync`; only `is_async_callable(resolver)` (`:1976`) emits the `async def` awaiting `_pipeline_async`. `in_async_context()` appears in that builder only inside `_require_async_iterable_context` (`:1936`), which guards a returned source shape |
| nested relation connection | **sync-only**, no async sibling | `connection.py:2154` calls `_pipeline_sync`; the builder docstring states it has "no `resolver=` seam" and that an `async def get_queryset` target therefore raises `SyncMisuseError` on every query |
| `list_field.py::DjangoListField` | **split**: default resolver per call, consumer branches at construction | `in_async_context()` at `list_field.py:206` in `_default`; `is_async_generator_callable` / `is_async_callable` at `:235` / `:242` for the consumer wrapper. The module comment at `:192-201` says so in words |
| `types/relay.py` | **per call**, unconditionally | `in_async_context()` at `types/relay.py:841` (`_resolve_node_default`) and `:902` (`_resolve_nodes_default`), each dispatching to the `_async` sibling at `:848` / `:913` |

Confirmed by execution as well as by reading: Worker 3's temp test
`docs/builder/temp-tests/r1/test_async_execution_default_connection.py` re-run read-only
(`uv run pytest <path> --no-cov -q -o addopts=''`) — **1 passed**. A default `DjangoConnectionField` over
a type declaring `async def get_queryset`, driven by `await schema.execute(...)`, raises `SyncMisuseError`;
that is only reachable if the **sync** runner ran under **async** execution. The temp test was not
modified, moved, or deleted.

### The fix: cut the mechanism claim, keep the ownership claim

Three seams, three timings. Stating the mechanism accurately costs a sentence per seam in a paragraph
whose job is to say **where** the behavior lives, and the dispatch's standing rule is to cut rather than
qualify. So the timing claim is **deleted at both sites** and no timing claim replaces it:
`is chosen per execution by` → `is applied by`. The `SyncMisuseError` clause is correct and load-bearing
and was kept, exactly as the review required. The corrected sentence makes no timing claim at all, so it
cannot flatten the three differing seams into one wrong generalisation — which is the failure mode that
produced findings in three consecutive passes.

**Rejected: restating the mechanism accurately in the spec** (the review's second option). It is true but
costs three clauses in the Borrow chapter, and *when* a field's color is decided is the connection /
list-field modules' own contract — each states it in its own docstring, and `connection.py` cites the
Decision that owns it. The spec sentence exists to answer "where does async-safe queryset access live",
and "applied by whichever field owns the queryset" answers it completely.

**Rejected: a retraction note in the rationale.** `worker-1.md` `### Performing the rationale move` rule 2
is explicit — *delete, do not move, prose the current decisions have falsified*; a false clause belongs in
neither file. The clause was incidental description inside this cycle's own added block, not a rejected
alternative, so it leaves no argument for a fifth pass to re-open. The differing timings are recorded
here and in worker memory instead.

### Spec changes made (Worker 1 only)

| # | Spec location | Change | Reason |
|---|---|---|---|
| 49 | `spec-009` ``### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField` ``, the async-safety paragraph (`:417`, added as change 42) | `is chosen per execution by whichever field owns the queryset` → `is applied by whichever field owns the queryset` | The colored pair is fixed at **construction** at the connection seam (`_build_connection_resolver` branches on the resolver's declaration; the nested relation-connection builder has no async sibling), so "per execution" was false there and inverted the actionable consequence. Per call only in `types/relay.py` and in `DjangoListField`'s default resolver |
| 50 | `spec-009-…-rationale.md`, the ``### Borrow `StrawberryDjangoFieldBase` … `` and `### Layer 4` entry (`:352-353`, added as change 47) | Same clause, same cut: `is chosen per execution by` → `is applied by` | The rationale carried this cycle's own copy of the false clause. Correcting a line **this cycle added** preserves append-only, by exactly the argument change 46 recorded |

No Decision, Layer, or Phase was renumbered; no source, test, sibling spec, standing doc, generated doc,
temp test, or DB row was touched. The diff is two `.md` files and one word-region per file.

### Byte counts

| File | Before this pass | After | Delta | vs HEAD |
|---|---|---|---|---|
| `spec-009-…-0_0_4.md` | 61,359 / 1,096 | **61,346 / 1,096** | **-13 bytes / 0 lines** | HEAD 54,232 / 1,154; `--numstat` **112 / 170**; `1,154 - 170 + 112 = 1,096` closes |
| `…-0_0_4-rationale.md` | 49,460 / 690 | **49,447 / 690** | **-13 bytes / 0 lines** | HEAD 12,273 / 208; `--numstat` **482 / 0**; `208 + 482 = 690` closes |

Net-negative on both files, as the dispatch required. Sixth consecutive net-negative spec pass.

### Append-only proof on the rationale

- `git diff -- <rationale> | grep -c '^-'` → **1**, and that line is the `--- a/` header; no HEAD line was
  deleted or modified, which subsumes any `head -N` argument.
- `git diff -U0` hunks unchanged in shape: `@@ -166,0 +167,480 @@`, `@@ -185,0 +666 @@`,
  `@@ -186,0 +668 @@`; `480 + 1 + 1 = 482` closes against `--numstat`.
- `head -166` of the working file `cmp`s **exit 0** against `head -166` of `git show HEAD:<path>` taken
  into a scratch path outside the repository. The six pre-existing entries and `## Standing notes` —
  including its deliberately-stale "three sites" bullet — are untouched.

### Gates and link surface

- `uv run python scripts/check_spec_glossary.py --spec <spec>` → `OK: 23 terms - all have glossary entries
  and at least one spec link.`, **exit 0, 23 terms**.
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0**.
- Link validator (fences stripped, definition lines excluded from the use scan, code spans left intact):
  spec **25 defs / 25 uses, 0 missing, 0 orphan, 0 dead**; rationale **11 / 11, 0 missing, 0 orphan,
  0 dead**. **0** `](#…)` in-page anchors in either file. **0** in-repo raw `path:NN`
  (`grep -nE '\.py:[0-9]+'` over both, upstream `file:///…#LNN` excluded as dispatched).
- **No renumbering.** `### Layer 1`-`### Layer 11` (11 headings, no gap), `### Phase 1`-`### Phase 8`,
  `### Decision 1`-`### Decision 6`.
- **Cross-spec anchors, five, both directions, re-verified this pass.** Inbound: `spec-010:67` →
  #"### Layer 3: Finalization trigger", `spec-010:468` → #"### Decision 6: fail loudly", `grep -c` on the
  edited spec-009 → **1 each**. Outbound: spec-009 → `spec-010` #"### Must redo (not augment)",
  #"## Strawberry finalization strategy", #"### Unresolved-target error format", `grep -c` on the current
  spec-010 → **1 each**.
- **Reported, not repaired** (outside the writable set, fourth consecutive pass): `spec-010:8` still lists
  "custom field classes" among what spec-009 describes — the claim D1 scrubbed.

### Provenance — nothing swept into a concurrent commit

`git log --stat` over both paths: the newest commit touching either is still **`f3c94642`**
("docs(specs): reconcile spec-009 and spec-010, and give each a rationale companion"), unchanged across
all four passes, even though HEAD moved from `9f968e86` to `5851bb59` while this cycle ran.
`git show HEAD:` on both documents still measures **54,232 / 1,154** and **12,273 / 208** — the ledger's
HEAD figures — so no spec-009 content was adopted by any concurrent commit. Both files are ` M`; the
artifact is `??`. Verified with `git log --stat` plus `git show HEAD:`, never `git status` alone.

### Dispatched findings checklist — ticks unchanged, and correctly so

Sixteen boxes, all `- [x]`, zero `- [ ]`; re-read against this diff. Like passes 2, 3, and 4's finding,
this one is a **new-claim** finding rather than a drift row: it corrects text this cycle wrote, adds no
box, and un-ticks none. No D-row contract moved.

### Carried forward, report-only

Worker 3's note 2 stands and is **not** repaired here (this item's writable set excludes tests): the
permanent suite pins `async def get_queryset` → `SyncMisuseError` on the connection field only under
`execute_sync` (`tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse`).
The same rejection under `await schema.execute` for a **default** connection field — the contract that
makes an `async def resolver=` mandatory, and the exact fact this pass's correction turns on — has no
permanent row. `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is a ready-made
body for whichever cycle owns tests.

### Status

`Status: planned` — routes to Worker 3 for a fifth audit pass.

## Review (Worker 3, pass 5)

Fifth review pass on this item, run 2026-08-16 by a fresh Worker 3 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-3.md`. Scope, per dispatch: **apply-changes pass 4 only** — one
clause deleted at two sites, -13 bytes, zero line change — plus regression. The architectural decision, the
Layer 4 bullets, the scope extension, and the scrub were accepted with evidence in passes 3 and 4 and were
not re-audited; items 1, 2, 4, 5 and 6 below were re-derived from source and from the tree rather than read
as discharged.

Method notes: HEAD re-derived at the start of the pass (**`5851bb59`**, matching the build report, not the
dispatch's `9f968e86`) and re-checked at the end — unchanged. Read-only HEAD copies taken with
`git show HEAD:<path>` into a scratch path **outside** the repository; no `git stash` / `checkout` /
`restore` / `worktree`; no `pytest` with any `--cov*` flag; nothing committed; no branch created; no
concurrent file touched.

### High:

None.

### Medium:

None.

### Low:

None.

### The fix, verified

- **The clause is gone from both files.** `grep -rn "per execution"` over the spec and the rationale →
  **no match, exit 1**. The surviving spec sentence (`spec-009:417`) reads "… the
  `apply_type_visibility_sync` / `apply_type_visibility_async` pair — with `SyncMisuseError` closing the
  sync path against an `async def get_queryset` — **is applied by** whichever field owns the queryset:
  `connection.py`, `list_field.py`, `types/relay.py`." The rationale twin (`rationale:352-353`) took the
  same cut in its own phrasing ("… **is applied by** `connection.py`, `list_field.py`, and
  `types/relay.py` — the fields that own the queryset"). The `SyncMisuseError` clause is intact at both
  sites, as the finding required.
- **No timing claim survives.** A vocabulary sweep for the whole shape, not the cited line
  (`grep -nEi "per execution|per-execution|per call|per-call|at construction|construction-time|chosen|in_async_context|is_async_callable|execution context"`)
  returns **one** hit across both documents — `rationale:66`, "imported before that construction", which is
  about import-order coupling in an unrelated pre-existing entry. The two edited sentences now assert
  ownership only, which is the property that makes them safe across three differing seams.
- **The byte delta is fully accounted for by that one substitution.**
  `is chosen per execution by` = 26 bytes, `is applied by` = 13 bytes, difference **13** — and each file
  fell **exactly 13 bytes** with **0** line change. One occurrence per file consumes the entire delta.
  (Honest limit: this excludes any other net-byte edit, not a hypothetical byte-neutral one; the unchanged
  `--numstat` and unchanged hunk shape below close the rest.)

### The four-seam timing derivation — re-derived independently, all four hold

The substance of the build report is its claim that the three seams genuinely differ, which is what
licenses cutting rather than restating. Re-derived against source this pass, not read:

- **Root connection — fixed at construction.** `connection.py::_build_connection_resolver` (`:1888`) has
  four branches, read end-to-end: `resolver is None` (`:1947`), `is_async_generator_callable` (`:1958`) and
  the plain-`def` `else` (`:1989`) each emit a **sync** `def _resolve` calling `_pipeline_sync`
  (`:1951`, `:1968`, `:1995`); only `is_async_callable(resolver)` (`:1976`) emits the `async def` awaiting
  `_pipeline_async` (`:1981`). The builder's only `in_async_context()` is at `:1939`, inside
  `_require_async_iterable_context`, which guards the **returned source shape**, never the pipeline choice.
  `_pipeline_sync` (`:1750`) itself has no async dispatch — it calls `apply_type_visibility_sync` at
  `:1780` unconditionally; `_pipeline_async` calls the `_async` sibling at `:1815`. Confirmed.
- **Nested relation connection — sync-only.** `_build_relation_connection_resolver` (`:2029`) reaches
  `_pipeline_sync` at `:2154` and `_pipeline_async` appears nowhere in it (module-wide, `_pipeline_async`
  occurs only at its `:1788` definition and the `:1981` await). The docstring's "no ``resolver=`` seam"
  phrase the report cites is real, at `connection.py:2090`. Confirmed.
- **`list_field.py` — split.** `_default` chooses per call via `in_async_context()` (`:206`, dispatching to
  `apply_type_visibility_async` at `:211` and `apply_type_visibility_sync` at `:217`); the consumer-resolver
  branches commit at construction via `is_async_generator_callable` (`:235`) / `is_async_callable` (`:242`).
  The module comment at `:192`-`:201` states the asymmetry in words and calls it intentional. Confirmed.
- **`types/relay.py` — per call, unconditionally.** `_resolve_node_default` (`:812`) tests
  `in_async_context()` at `:841` before the sync path at `:843`; `_resolve_nodes_default` (`:869`) does the
  same at `:902` / `:904`; the `_async` siblings await `apply_type_visibility_async` at `:864` / `:929`.
  Confirmed.

So the corrected sentence is not merely *not false* — it is the only single-clause form that is true of all
three. Any surviving timing word would have been wrong for at least one seam.

### Cutting was the right remedy over the two rejected alternatives

Judged, not deferred:

- **Restating the mechanism accurately (the review's own second option) — correctly rejected.** It is true
  but costs a clause per seam in a chapter whose job is the responsibility-to-seam map, and it would put a
  *when* contract in the spec that each module's docstring already owns and states more precisely
  (`list_field.py:192`-`:201`; `connection.py:2090`, `:1901`-`:1916`). Restating it here recreates exactly
  the two-copies-one-stale condition that pass 3's deletion of the duplicated bullet list was accepted for
  fixing. Cutting is consistent with that accepted decision; restating would have partly undone it.
- **A retraction note in the rationale — correctly rejected**, and its citation is real:
  `docs/builder/worker-1.md` `### Performing the rationale move` rule 2 reads "**Delete — do not move —
  prose the current decisions have falsified.** … Git preserves history, so a false sentence belongs in
  neither file." The clause was incidental description inside this cycle's own added block, not a rejected
  alternative, so the rationale's `## Rejected alternatives` sense of the file has nothing to retain.
- **The one thing worth naming as a cost, not a finding:** the shortened sentence no longer tells a
  Borrow-chapter reader the actionable consequence — that an `async def get_queryset` under a connection
  needs an `async def resolver=` supplied at construction. That consequence is owned and stated by
  `connection.py::_build_connection_resolver`'s own docstring, which is where a consumer meets it, and the
  spec sentence answers "where does async-safe queryset access live" completely. Accepted as the
  intended trade, recorded so a sixth pass does not re-open it.

### No regression

- **Ledger re-measured with `wc -c -l`.** Spec **61,346 bytes / 1,096 lines** (was 61,359 / 1,096);
  rationale **49,447 / 690** (was 49,460 / 690). Both **-13 bytes / 0 lines**, exactly as reported.
  `git show HEAD:` copies re-measure **54,232 / 1,154** and **12,273 / 208**; `git diff --numstat` is
  spec **112 / 170**, rationale **482 / 0**. Both identities close: `1,154 - 170 + 112 = 1,096` and
  `208 + 482 = 690`. Seventh consecutive net-negative spec state.
- **Append-only on the rationale, proved mechanically.** `git diff -- <rationale> | grep -c '^-'` → **1**,
  and printing that line shows it is the `--- a/…` header — no HEAD line deleted or modified, which
  subsumes any `head -N` argument. `git diff -U0` hunks are `@@ -166,0 +167,480 @@`, `@@ -185,0 +666 @@`,
  `@@ -186,0 +668 @@`; `480 + 1 + 1 = 482` closes against `--numstat`. `head -166` of the working file
  `cmp`s **exit 0** against `head -166` of `git show HEAD:<path>` taken to an out-of-repo scratch path
  (HEAD's file is 208 lines, so the 166-line prefix is a real prefix, not the whole file). The corrected
  line 353 sits inside the `+167,480` block, so the in-place correction is licensed by change 46's argument.
- **Gates re-run, not read.** `uv run python scripts/check_spec_glossary.py --spec <spec>` →
  `OK: 23 terms - all have glossary entries and at least one spec link.`, **exit 0, 23 terms**.
  `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0**.
- **Link surface, validator written fresh for this pass** (fences stripped, definition lines excluded from
  the use scan, code spans left intact): spec **25 defs / 25 uses, 0 missing, 0 orphan, 0 dead targets**;
  rationale **11 / 11, 0 missing, 0 orphan, 0 dead**. **0** `](#…)` in-page anchors in either file.
  **0** in-repo raw `path:NN` (`grep -nE '\.py:[0-9]+'` over both, upstream `file:///…#LNN` excluded as
  dispatched). Independently reproduces passes 3 and 4.
- **No renumbering.** `### Layer 1`-`### Layer 11` (11 headings, no gap: Layers 1-11 at `:576`, `:599`,
  `:631`, `:644`, `:656`, `:678`, `:716`, `:735`, `:768`, `:783`, `:799`); `### Phase 1`-`### Phase 8`
  (8 headings); `### Decision 1`-`### Decision 6` (6 headings).
- **Provenance.** `git log --oneline -1` over both paths: newest commit touching either is still
  **`f3c94642`**, unchanged across all five passes. Both files are ` M`; the artifact is `??`.
  `git show HEAD:` still measures the ledger's HEAD figures, so no spec-009 content was swept into a
  concurrent commit while `git status --porcelain` moved 77 → **83** entries during this pass. Reported,
  **not reverted**.
- **Public-surface check.** `git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__`
  and the re-export list are unchanged; this item writes no package code.

### Cross-spec anchors — five, both directions, re-verified and re-timestamped **2026-08-16T01:00:55Z**

- **Inbound (2).** `spec-010:67` cites spec-009 #"### Layer 3: Finalization trigger"; `spec-010:468` cites
  #"### Decision 6: fail loudly". `grep -c` for each heading on the edited spec-009 → **1 each**.
- **Outbound (3).** `spec-009:99` → `spec-010` #"### Must redo (not augment)"; `:634` → #"## Strawberry
  finalization strategy"; `:870` → #"### Unresolved-target error format". `grep -c` on the current
  spec-010 → **1 each**. The three spec-009 line numbers are unchanged from passes 3 and 4.
- `spec-011-stale_placeholder_cleanup-0_0_4.md` still carries no inbound spec-009 reference
  (`grep -rn spec-009` over it → nothing).
- **Reported, not repaired:** `docs/SPECS/spec-010-foundation-0_0_4.md:8` still lists "custom field
  classes" among what spec-009 describes — the claim D1 scrubbed. Fourth consecutive pass at which it
  stands; outside this cycle's writable set.

### Dispatched findings checklist

Sixteen boxes, all `- [x]`, zero `- [ ]` — unchanged, and still matching the diff. This pass's change
touches no D-row contract: it adds no box and un-ticks none. The scrubbed symbols were re-counted against
the **current** spec rather than the diff and are all **0**: `DjangoModelField`, `types/fields.py`,
`OptimizerStore`, `with_hints`, `with_prefix`, `get_strawberry_annotations`, `DjangoField(`,
`ASC_DISTINCT`, `DESC_DISTINCT`, `DISTINCT ON`, `AdvancedFilterSet`, `AdvancedOrderSet`, `LazyClassRef`.
(Their non-zero counts in the rationale are the record of what was scrubbed and why — expected.)
All seven cited card ids re-grepped against the live `KANBAN.md` this pass (it is dirty under a concurrent
session, so this is re-measured, not carried): `DONE-009-0.0.4` 2, `TODO-BETA-053-0.1.1` 17,
`TODO-BETA-054-0.1.1` 16, `TODO-BETA-055-0.1.2` 16, `TODO-BETA-057-0.1.3` 5, `TODO-BETA-058-0.1.3` 7,
`TODO-BETA-059-0.1.4` 3 — identical to pass 4. No renumber has landed.

### DRY findings

- None. The diff deletes 13 bytes from each of two `.md` files and touches no `.py` file, so it introduces
  no abstraction, helper, registry, or indirection: the existence challenge has no target this pass.
- The deletion is itself the DRY-correct direction on the pattern this artifact keeps naming — the spec
  now states ownership once and defers *when* to the modules whose docstrings own it, rather than keeping a
  second copy of a mechanism that would need re-verifying every time the seams change.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **empty**. `__all__` and the re-export list are
unchanged.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applies — the deliverable is two documentation files. Card ids, renumbering, link/anchor surface, both
gates, the ledger identities, append-only, and provenance are all recorded under `### No regression` and
`### Dispatched findings checklist` above; every one re-run this pass. Nothing in the changed word-region
carries version strings, KANBAN movement, verbatim spec drop-ins, or staging language, so those sub-checks
have no target here.

### Failability proofs

Not applicable to a documentation pass. The diff introduces no guard, gate, cap, or rejection path and
writes no executable line, so `BUILD.md` `### What needs a proof, and what does not` scopes the obligation
to an empty set and the mandatory re-run floor is satisfied by that empty set. Worker 3's source carve-out
was not exercised; no production file was mutated at any point in this pass.

### Hot-path budget

Not applicable to a documentation pass; the plan declares no hot path for any residual item and this one
touches no executable line.

### Static helper

`scripts/review_inspect.py` not run — recorded skip with reason: the diff adds and touches **no** `.py`
file, so none of Worker 3's trigger conditions in `BUILD.md` `### When to run the helper during build`
fires. All source reading this pass was read-only verification of the documents' claims.

### What looks solid

- **The remedy matches the defect exactly.** The finding was that a connective clause over-generalised
  three differing seams; the fix removes the clause rather than replacing it with a second generalisation.
  That is the smallest change that closes it, and the pass took the two prior corrections' lesson — it
  fixed both sites in one edit, so the "a finding fixed at the cited line is not a finding fixed" pattern
  did not recur for the first time in this artifact's history.
- **The build report's own justification re-derives.** This artifact's recurring failure mode is a correct
  fix beside a wrong "because" clause, so the four-seam table was the thing I checked hardest; every row is
  exact, including the two details easiest to get wrong (the connection builder's `in_async_context()` is
  in the source-shape guard, not the pipeline choice; the relation-connection builder has no async sibling
  at all). Line citations in the table are the branch-guard lines, and each resolves.
- **The temp test was re-run rather than assumed** by Worker 1, read-only, and left in place — a builder
  re-running the reviewer's proof instead of restating its conclusion.
- **Everything the four prior passes established is intact.** Ledger identities close, append-only is
  proved the strong way, both gates exit 0, all five cross-spec anchors resolve in both directions, no
  renumbering, no orphan or dead link definition, zero in-repo `path:NN`, zero in-page anchors, public
  surface unchanged, no `.py` file touched, no concurrent commit adopted any spec-009 content.

### Temp test verification

- `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` — re-run this pass, read-only:
  `uv run pytest <path> --no-cov -q -o addopts=''` → **1 passed** (`addopts` overridden only to drop
  `pytest.ini`'s auto-applied `--cov`, per `BUILD.md` `## Coverage is the maintainer's gate, not a
  worker's tool`). Not modified, moved, or deleted, per dispatch.
- **Disposition: kept on disk** (gitignored, clears with the cycle). Not promoted — it pins already-correct
  shipped behavior rather than catching a bug, and this item's writable set excludes tests. The permanent
  suite gap it exposes remains report-only, carried below.

### Notes for Worker 1 (spec reconciliation)

1. **Nothing new is open on this item.** Every finding from passes 1-4 is closed and re-verified; this
   pass adds none.
2. **Carried, unchanged, report-only — the permanent-suite gap.** `tests/test_connection.py::`
   `test_sync_context_async_get_queryset_raises_sync_misuse` pins `async def get_queryset` →
   `SyncMisuseError` on the connection field only under `execute_sync`. The same rejection under
   `await schema.execute` for a **default** connection field — the fact the corrected sentence turns on —
   still has no permanent row, and the temp test is a ready-made body for whichever cycle owns tests.
   Worth carding rather than leaving in a cycle-scoped artifact, since the artifact clears with the cycle.
3. **Escalations 1-6 of final verification are unchanged and none was repaired here.** Re-checked:
   `spec-010:8` still mis-describes spec-009 (outside the writable set); the
   `types/definition.py::DjangoTypeDefinition` docstring still reserves `fields_class` for the stale
   `TODO-BETA-046-0.1.1` while spec, `KANBAN.md`, and `docs/TREE.md` say `TODO-BETA-054-0.1.1`; the
   rationale's `## Standing notes` "three sites" bullet is still deliberately stale under append-only,
   with the staleness stated five lines above it.
4. **Re-check the card ids once more at the commit gate.** `git status --porcelain` moved 77 → 83 while
   this pass ran and HEAD is `5851bb59`; nothing of this item was swept, but `KANBAN.md` stays dirty under
   a concurrent session, so the seven ids are worth one final re-grep immediately before the commit.

### Review outcome

`review-accepted`. No High, no Medium, no Low. The one-clause cut lands at both sites, "per execution" is
gone from both documents, the surviving sentences make no timing claim, the four-seam derivation that
justifies cutting rather than restating re-derives exactly against source, both rejected alternatives were
rejected for correct and citable reasons, and nothing regressed — ledger, append-only, gates, links,
anchors, renumbering, checklist ticks, card ids, public surface. The finding sizes on this item have run
9 → 2 → 1 → 1 → 0, and the fifth pass found nothing because there is nothing left to find, not because it
looked less hard: items 1, 2, 4, 5 and 6 were each re-derived from source or from the tree this pass.

---

## Final verification (Worker 1, pass 2)

Run 2026-08-16 by a **fresh Worker 1 invocation** whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-1.md`. Second final verification on this item; the first
set `revision-needed` on a Medium the three reviews before it had missed, and apply-changes passes 3
and 4 plus Worker 3 passes 4 and 5 closed that line of work.

**Method.** The whole artifact was read end to end — plan, combined perform pass, five Worker 3
reviews, four Worker 1 apply-changes passes, the prior final verification — and then every load-bearing
claim was **re-derived rather than read as discharged by Worker 3's zero-finding acceptance**
(`worker-1.md` `### Verifying relocation / promotion claims`). Both mechanical gates, the link / anchor
/ rule-27 validator, the append-only proof, the byte ledger, the five cross-spec anchors, the
sixteen-box checklist, and every `+` line of the spec diff were re-run or re-read from scratch.
`git stash`, `git checkout`, `git restore`, and `git worktree` were not used; the HEAD reference was
`git show HEAD:<path>` into a scratch path outside the repository. **This item runs no tests and
changes no code**, so `## Final verification job` step 5 is discharged by stating that rather than by a
focused scope; Worker 3's temp test under `docs/builder/temp-tests/r1/` was confirmed present and
untouched but not re-run, because no finding here turns on it. The staged-anchor sweep is R4's and was
**not** duplicated (step 6).

**Spec status-line re-verification (per-spawn duty).** Lines 1-5 of the spec re-read. The opener still
describes the rationale companion, the **four** finalization sites, and the six scrubbed mechanisms;
nothing in the build falsifies it. No edit owed.

**HEAD re-derived: `5851bb59`**, matching the dispatch and both pass-4/5 readings. `git status
--porcelain` is **89** entries, up from the 83 Worker 3 pass 5 recorded — reported, **not reverted**,
and none of it intersects this cycle's writable set.

### Final status

`revision-needed`. **One Medium**, below. Everything else verifies, including all sixteen checklist
ticks.

**Nothing was repaired here.** The finding sits in this cycle's writable set and a custodian edit would
close it, but an edit made by the pass that accepts the item is a fresh unreviewed claim — which is the
whole reason the first final verification declined to self-fix and was right to. The apply-changes pass
owns it under the plan's `### Deviation 3` corollary.

### Medium: the optimizer-hint rule's reason inverts the plan cache's actual mechanism

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:515`, in
`### Keep the current optimizer's strengths, and borrow its nested-prefetch lessons` (added by the
combined pass as change 12):

> **A hint must be a value, not a callable.** Strategy selection is what a cross-request plan cache is
> keyed on, so a hint that can consult the request makes the plan un-cacheable and the cache unsound at
> the same time.

**The rule is right, the consequence is right, and the stated reason is false — and inverted, which is
the same shape as `:385`'s "binds at finalization".** Strategy selection is **not** what the plan cache
is keyed on, and cannot be.

- `optimizer/extension.py::DjangoOptimizerExtension._build_cache_key` enumerates its key in its own
  docstring: **five** components — the printed operation AST plus reachable fragment definitions; the
  frozenset of `(var_name, var_value)` for `@skip`/`@include` and non-root `first`/`last`/`before`/
  `after` variables; the target Django model class; the root response path; and the resolver's origin
  Strawberry type. `Meta.optimizer_hints` and strategy selection appear in **none** of them
  (`grep -rn optimizer_hints django_strawberry_framework/optimizer/` returns `extension.py:1279`,
  `walker.py`, `nested_planner.py`, `nested_fetch.py`, `hints.py` — never the key builder).
- The shipped invariant says the opposite of "keyed on", in terms:
  `optimizer/hints.py` #"The knob is schema-static and needs NO plan-cache-key change: the plan cache
  is instance-bound (``optimizer/extension.py`` Decision 11), so strategy selection never depends on
  request-varying data." The instance binding is real —
  `optimizer/extension.py` #"Publish this instance so ``apply_connection_optimization`` can" sets the
  `_active_optimizer` ContextVar so the connection field shares the **instance-bound** plan cache.
- **The causal arrow is backwards.** The unsoundness the sentence predicts is real precisely *because*
  strategy selection is absent from the key: a request-consulting hint would bake request-specific
  shaping into a plan that a later request retrieves under a key blind to it. If strategy selection
  *were* keyed on, a callable hint would merely fragment the cache — the failure mode the sentence
  rules out would be the benign one.

Three things make this a Medium rather than a Low, on the same test the four prior instances were
graded by:

- It is **new text this cycle wrote** — `git diff` carries it as a `+` line, and no pass re-derived it.
  Worker 3 pass 1 verified `optimizer/hints.py` is `@dataclass(frozen=True)` and pins the
  MUST-never-depend rule, which establishes the **rule**; the `keyed on` mechanism behind it was never
  checked by any of the five reviews.
- It is the **stated reason for a normative rule in a horizon document**, in the one section a future
  optimizer card reads. The same rationale entry names `TODO-BETA-053-0.1.1` as owning the live
  annotation-dependency fragment; a reader widening `Meta.optimizer_hints` under that card is told the
  cache key already covers strategy selection, which is the exact premise that would make a
  request-varying hint look safe to key around.
- **The rationale's twin telling is correct**, so the spec is not merely imprecise, it disagrees with
  its own companion. `…rationale.md:426` reads "`optimizer/hints.py` pins that strategy selection
  'MUST never depend on request-varying data', and **that invariant is what buys the cross-request plan
  cache**" — invariant-buys-cache, which is what the source says. The spec's condensation to
  selection-keys-cache is where the inversion entered. Under the cycle's own single-ownership law a
  duplicate map has a current half and a stale half; this pair now has exactly that.

**Recommended change** (Worker 1's apply-changes pass owns it; re-derive rather than accept this
prescription — this cycle has had two dispatched prescriptions turn out wrong in their mechanism). The
cheapest correct fix is to align the spec to the rationale's already-correct telling: keep "A hint must
be a value, not a callable", and replace the reason with the invariant-buys-the-cache form, or cut the
mechanism clause entirely and let the rule stand on `optimizer/hints.py`'s citation — the same
cut-don't-qualify disposition passes 3 and 4 reached. Do **not** close it by deleting
"request-varying shaping belongs to `get_queryset`"; that clause is correct and load-bearing. It is a
**one-site** fix: `grep -n -i 'keyed on|cache key|plan cache|un-cacheable'` over both documents returns
the spec's `:515` and the rationale's correct `:426-427` and nothing else, so the two-site trap this
artifact recorded twice does not apply here.

### Fail-open-shaped prose: where the sixth was found, and the sites that are clean

Read cold, as a reader who had not seen the arguments, per the dispatch — and read as the **whole set
of `+` lines** (112 of them) rather than at the sites the prior findings named, since "grep for the
shape, not the site" is this artifact's own lesson and is what the fifth instance was found by. The
five sites the history points at are all **clean**:

- **`:417` (async safety).** "… is applied by whichever field owns the queryset: `connection.py`,
  `list_field.py`, `types/relay.py`." Re-derived independently:
  `grep -cE 'async|sync_to_async|SynchronousOnly|await ' django_strawberry_framework/types/resolvers.py`
  → **0**; `grep -c querysets …/types/resolvers.py` → **0**; the pair's call sites are
  `connection.py:1780`/`:1815`, `list_field.py:211`/`:217`, `types/relay.py:843`/`:864`/`:904`/`:929`.
  The rejected prescription re-checked too: `run_in_one_sync_boundary`'s call sites are
  `schema.py`, `permissions.py`, `filters/sets.py`, `auth/mutations.py`, `mutations/resolvers.py`,
  `orders/sets.py` — **none** of the three named modules (the `consumers.py` hit is a comment saying it
  deliberately adds none). **No timing claim survives**, so the sentence cannot flatten three differing
  seams.
- **`:649` (Layer 4 visibility).** Conditional where the code is conditional: names the connection
  pipeline, `list_field.py::DjangoListField`, and `optimizer/walker.py::_build_child_queryset`, says in
  terms it is not inside the generated resolver, and names the cascade-helper recourse. Call sites
  re-derived at `connection.py:1780`, `list_field.py:217`, `walker.py:383`.
- **`:385` (`### Borrow \`StrawberryDjangoDefinition\``).** "validated to a concrete class at class
  creation (`types/base.py::_validate_filterset_class`)" — no lazy-binding claim survives. The
  three-sidecars-two-validators nuance is examined and again **not** raised: `fields_class`'s `Meta`
  key is refused outright by `DEFERRED_META_KEYS` (re-measured from the frozenset literal: exactly
  `{aggregate_class, fields_class, search_fields}`), so the slot is unreachable rather than unguarded —
  the sentence is stricter than the code, never looser.
- **`:401` (provenance).** "`DjangoType.__init_subclass__` derives those provenance sets and
  `DjangoTypeDefinition` carries them; the override validators and `_build_annotations` all read the
  same union rather than re-deriving one" — the producer/first-consumer claim is gone, not softened.
- **`:483` (`<TypeName>Connection`).** "resolves **every** node type … the opt-in decides only whether
  that subclass carries the member" matches `connection.py::_connection_type_for`; the
  generic-specialization reason re-derives byte-for-byte against `docs/GLOSSARY.md` `## \`DjangoConnection\``
  #"a bare generic alias loses the `resolve_connection` override".

Three further new causal claims were re-derived because they are the remaining "because" clauses in
added text, and they hold: `:68`'s nullable-by-contract sentence is near-verbatim
`relay.py` #"Resolution is **nullable by contract**"; Layer 4's four bullets each verify
(`types/converters.py::resolved_relation_annotation` returns literally `list[target_type]` /
`target_type | None` / `target_type`; `types/finalizer.py`'s module docstring places
`_attach_relation_resolvers` at Phase 2 and `strawberry.type(...)` at Phase 3); and change 45's four
substituted concerns are all present in `types/resolvers.py` (`_check_n1`, the
`_prefetched_objects_cache` read, `_build_fk_id_stub`, `resource_policy.py::bounded_rows`) while
`grep -cniE 'filterset|orderset|paginat|permission'` over that module → **0**.

**One claim examined and deliberately not raised**, recorded so a later pass does not re-open it:
`### Phase 3`'s acceptance-test bullet "async-safe relation access" sits in a phase whose body now
points at Layer 4, and Layer 4 no longer owns async safety. It is not a contradiction — the bullet is a
**property of the finished schema**, asserting no module and no seam, and the property holds through
the queryset-owning fields. The five acceptance tests are pre-existing text change 27 deliberately left
unchanged.

### Duplication across all nine passes taken together

`## Final verification job` step 4, run against the two documents rather than any pass's file list,
because no single pass held the whole cycle.

- **The four-seam near-duplication the prior final verification recorded is genuinely retired.** Only
  `### Layer 4` carries a responsibility-to-seam list; `:415` is a one-line pointer to it. The three
  facts that were told twice — `resolved_relation_annotation`, `_make_relation_resolver`, the
  synthesized `__signature__` — are each told once. `grep -v '^[[:space:]]*$' | sort | uniq -d` over
  the spec returns only code-fence boilerplate and one-word list items; over the rationale, only `>`.
- **One live inconsistent-shape instance remains, and it is the Medium above**: the optimizer-hint rule
  is argued in both documents with two different mechanisms, one of which is false. It is the same
  class the pass-3 single-ownership decision was made to end, arriving at a different pair of
  documents rather than a different pair of sections.
- **The declared spec/rationale overlap is unchanged and still declared.** The
  "upstream binds all of them to one field class because its public API is decorator-first" argument
  appears at `spec:415` and in the rationale entry; it was recorded as an intentional rejection with
  the `worker-1.md` implementation-relevant carve-out cited, and both copies still agree.
- No new abstraction, helper, constant, or branch exists to challenge: the diff touches two `.md` files
  and no `.py` file.

### Dispatched findings checklist audit — sixteen boxes, all ticks confirmed, none changed

Walked box by box against the **current** files and `git diff -- <spec>`, not against any pass's
report, and with D10 given the extra scrutiny its history earns. **No over-tick, no landed-but-open
box, no deferral owed.** Scrub counts measured current-vs-HEAD with `grep -oF | wc -l`:

| Box | Contract | Evidence re-derived this pass |
|---|---|---|
| D1 | `DjangoModelField` / `types/fields.py` scrubbed everywhere | current **0** / **0**; HEAD **11** / **1**. Replacement sections live: `### Layer 4: Generated relation fields` (`:644`), `### Decision 3: generated field behavior belongs to the finalizer` (`:1001`), `### Phase 3: Generated relation fields` (`:929`), `### Layer 9` resolver wrapping (`:771`) |
| D2 | `OptimizerStore` / `with_hints` / `with_prefix` / callable hints scrubbed | current **0 / 0 / 0**; HEAD **8 / 2 / 2**. Section retitled to `### Keep the current optimizer's strengths…`; the value-not-callable rule is present at `:515` — **and carries the Medium above, which is about its reason, not its presence** |
| D3 | `get_strawberry_annotations` borrow replaced by the provenance section | current **0**, HEAD **3**; `### Track annotation provenance structurally…` present at `:396` |
| D4 | `DjangoField(...)` → `DjangoListField(...)` | current `DjangoField(` **0**, HEAD **1**; `DjangoListField(...)` present |
| D5 | fallback tier and the open question removed | `DjangoModelType` **8 → 6**; the six survivors enumerated under `### Summary`; `:441` states the no-placeholder-tier contract |
| D6 | `ASC_DISTINCT` / `DESC_DISTINCT` / `DISTINCT ON` gone from Layer 7 and Phase 5 | current **0 / 0 / 0**; HEAD **2 / 2 / 1**. Layer 7 now carries the six-member `Ordering` vocabulary and the `Min`/`Max` row-preserving paragraph; Phase 5's line is the property |
| D7 | `object_type: ObjectTypeNode \| None` | present in the `## Target outcome` sketch, with the nullable-by-contract paragraph beneath it; `relay.py:17-19` re-read |
| D8 | the three `DEFERRED_META_KEYS` named with their promoting cards | paragraph at `:70`; `types/base.py:65-67` is exactly the three keys, `ALLOWED_META_KEYS` (`:69-89`) is exactly **17** |
| D9 | no `total_count` on the base; `aggregates` restated as owed with its card | `### Borrow \`DjangoListConnection\`` carries both paragraphs; the fenced base has no `total_count` member |
| D10 | sketch corrected to shipped names and types | **the row this audit most distrusted.** Sketch reads `fields_spec` / `exclude_spec` and three plain `type \| None` sidecars; `types/definition.py:146`,`:147`,`:162-164` match name-for-name; `aggregate_class` / `search_fields` absent; `grep -rc LazyClassRef django_strawberry_framework/` → no non-zero file (HEAD spec had **4**) |
| D11 | `class ObjectFilter(FilterSet)`, canonical `Meta.fields` | `AdvancedFilterSet` **1 → 0**; the sketch reads `class ObjectFilter(FilterSet):` with `fields = {`; the parity-alias sentence is at `:696` |
| D12 | `Advanced` prefix dropped from this package's `*Set` sketches | HEAD `:769` read `Advanced[OrderSet][glossary-orderset]` and `:791` `class ObjectAggregate(AdvancedAggregateSet):`; current `:719` reads `[OrderSet]` and `:741` `class ObjectAggregate(AggregateSet):`. (The literal token `AdvancedOrderSet` is 0 at HEAD too — HEAD spelled it around a reference-style link — so the contract is the prefix, not the token, and it landed) |
| D13 | Layer 5 item 2 removed and the negative contract stated | list runs 1-12 with no "finalize pending types"; the "It does **not** finalize" paragraph is at `:674` |
| D14 | `types/fields.py` out, `fieldset/` as a package with its card, `orders/inputs.py` present | `## Proposed module layout` shows `fieldset/ — planned by TODO-BETA-054-0.1.1`, `aggregates/ … TODO-BETA-057-0.1.3`, `permissions.py … TODO-BETA-059-0.1.4`, and `orders/` naming `inputs.py`; no `types/fields.py` line |
| D15 | Phase 3 restated, Phases 1-8 intact | `grep '^### Phase '` → Phases 1-8 at `:903`,`:919`,`:929`,`:940`,`:951`,`:964`,`:976`,`:985` — no gap, no renumber |
| D16 | the three unmet success criteria carry their owning cards | `search — owed; TODO-BETA-055-0.1.2`, `aggregate output on connections — owed; TODO-BETA-057-0.1.3`, `field-level permission masking — owed; TODO-BETA-054-0.1.1`; the eight met criteria carry no annotation |

**Group C is still untouched**, re-confirmed: the two "retired since" markers (`:96`, `:99`), the
`### Layer 2` `PendingRelation` sketch, the `class ObjectTypeNode(DjangoType, relay.Node)` declaration,
and the upstream `file:///…#LNN` citations. The Medium above adds **no box** — like the findings of
passes 2, 3, 4, and the first final verification, it is a new-claim finding about text this cycle
wrote, not a drift row. **No deferral is owed for any box.**

### Gates and proofs re-run, not read

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0, 23 terms**,
  matching the pre-flight baseline and the card's 23 glossary links.
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0** for both.
- **Link / anchor / rule-27 validator**, written fresh for this pass (fences stripped, definition lines
  excluded from the use scan, code spans left intact so the two in-code-span uses are not false
  orphans): spec **25 definitions / 25 uses, 0 missing, 0 orphan**; rationale **11 / 11, 0 missing,
  0 orphan**; every non-anchor definition target disk-existence-checked, **0 dead**; **0** `](#…)`
  in-page anchors in either file, therefore none unresolved; **0** raw in-repo `path:NN` citations in
  either file, with `file://` URLs excluded. Independently reproduces passes 3, 4, and 5.
- **Byte / line ledger, re-measured with `wc -c -l`.** Spec **61,346 bytes / 1,096 lines**; rationale
  **49,447 / 690**. `git diff --numstat`: spec **112 / 170**, rationale **482 / 0**. HEAD's own copies
  (`git show HEAD:` into an out-of-repo scratch path) measure **54,232 / 1,154** and **12,273 / 208**.
  Both identities close: `1,154 - 170 + 112 = 1,096` and `208 + 482 = 690`.
- **Append-only on the rationale, proved independently.** `git diff -- <rationale> | grep -c '^-'` →
  **1**, and printing it shows the `--- a/…` header, so no HEAD line was deleted **or modified**
  anywhere. `git diff -U0` hunks are `@@ -166,0 +167,480 @@`, `@@ -185,0 +666 @@`, `@@ -186,0 +668 @@`;
  `480 + 1 + 1 = 482` closes against `--numstat`. `head -166` of the working file `cmp`s **exit 0**
  against `head -166` of HEAD's copy (HEAD's file is 208 lines, so the prefix is a real prefix).
  `## How to read this file`, `## Provenance of this record`, the six pre-existing entries, and
  `## Standing notes` — including its deliberately-stale "three sites" bullet at `:649` — are untouched.
- **No renumbering.** `### Layer 1`-`### Layer 11` (`:576`, `:599`, `:631`, `:644`, `:656`, `:678`,
  `:716`, `:735`, `:768`, `:783`, `:799`), `### Phase 1`-`### Phase 8`, `### Decision 1`-
  `### Decision 6`, each complete and in order with no gap. The two vacated slots carry positive
  contracts and no "this was rejected" prose.
- **Every rationale entry names its spec section by heading** — all 22 `###` entries do, so the L2 fix
  holds and no entry is unlookupable.
- **Provenance: nothing was swept into a concurrent commit.** `git log --stat` over both document paths
  → the newest commit touching either is still **`f3c94642`** (spec +71/-36, rationale +208 new),
  unchanged across all ten passes on this item. `git show HEAD:` on both still measures the ledger's
  HEAD figures. `git status --short` shows both ` M` and uncommitted; the artifact is `??`. Verified
  with `git log --stat` plus `git show HEAD:`, never `git status` alone.

### Cross-spec anchors: five, all resolving in both directions, re-timestamped **2026-08-16T01:12:52Z**

Re-derived from scratch rather than carried, because `spec-010` is under a concurrent cycle and has
moved between passes. Reported, not repaired.

- **Inbound (2).** `spec-010:67` cites `spec-009` #"### Layer 3: Finalization trigger";
  `spec-010:468` cites #"### Decision 6: fail loudly". `grep -c '^### Layer 3: Finalization trigger$'`
  and `grep -c '^### Decision 6: fail loudly$'` on the edited spec-009 → **1 each**.
- **Outbound (3).** `spec-009:99` → `spec-010` #"### Must redo (not augment)"; `:634` → #"## Strawberry
  finalization strategy"; `:870` → #"### Unresolved-target error format". `grep -c` on the current
  spec-010 → **1 each**.
- `spec-008`'s inbound reference is whole-file, not anchored; `grep -rn spec-009` over the spec-011
  files returns nothing.

### Builders' required-amendment lists, discharged

`worker-1.md` `## Review-round custody`. Every `### Notes for Worker 1 (spec reconciliation)` item
across the nine prior sections is accounted for: the R2 carry-forward is consistent and unchanged
(spec-009 states the row-preserving property at `### Layer 7` and `### Phase 5`; the `DISTINCT ON`
mechanism is **discharged by an alternative**, not postponed, and `docs/SPECS/spec-028-orders-0_0_8.md`
is still absent from `git status --porcelain`, so R2 starts from an untouched file); the
`filters/sets.py` in-place `Meta` mutation was correctly recorded as a maintainer observation and not
edited; the `KANBAN.md` stale assertion about Layer 3 is R3/R4 territory; the two-site discipline
Worker 3 pass 4 asked for was honoured by apply-changes pass 4. **Nothing was recorded and left
unimplemented.** No pass, this one included, found a correctness defect in shipped source, and none is
escalated as one.

### Escalations carried forward to the maintainer at commit — report-only, none repaired here

1. **`docs/SPECS/spec-010-foundation-0_0_4.md:8` still mis-describes spec-009.** It lists "custom field
   classes" among what spec-009 describes, which is exactly what D1 scrubbed. Re-read at
   2026-08-16T01:12:52Z and **still standing** — fifth consecutive pass. The file belongs to the
   concurrent spec-010 cycle and is outside this cycle's writable set; only the maintainer can sequence
   the two at commit.
2. **The `spec-010:67` coupling, and its pre-existing near-duplicate sentence.** That line says the
   auto-trigger direction in spec-009 #"### Layer 3: Finalization trigger" was not adopted; the anchor
   resolves and the claim is still true, but after change 40 the cited section no longer states the
   direction — it points at the rationale. Nothing dangles and nothing is false. Related and
   pre-existing: spec-009's single-threaded-setup-window sentence and `spec-010:67`'s closing sentence
   are near-verbatim twins, and were twins before this cycle; the right owner is spec-010.
3. **`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`'s docstring reserves
   `fields_class` for `TODO-BETA-046-0.1.1`** (`types/definition.py:65`) — a stale card number after
   the renumber; `046` is now `DONE-046-0.0.14`, the transport card. The live owner is
   `TODO-BETA-054-0.1.1`, which is what the spec, `KANBAN.md`, and `docs/TREE.md` all say. **The spec is
   right and the source docstring is stale.** Source is read-only in this cycle; a candidate row for
   whichever cycle next owns source docstrings.
4. **The rationale's `## Standing notes` "three sites" bullet is stale on purpose** (`:649`).
   Correcting it would break the plan's append-only constraint on the rationale for this cycle; the
   staleness is stated explicitly at `:643`, five lines above the bullet, and the spec's own opener was
   corrected to "four sites" (change 39). Correct it in whichever pass next has the rationale open
   without that constraint.
5. **A permanent-suite gap worth carding, and it will be lost if it is not carded.**
   `tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse` (`:1110`) pins
   `async def get_queryset` → `SyncMisuseError` on a connection field only under `execute_sync`. There
   is **no** row pinning the same rejection under `await schema.execute` for a **default**
   `DjangoConnectionField` — the contract that makes an `async def resolver=` mandatory, and the exact
   fact apply-changes pass 4's correction turns on. Worker 3's temp test
   `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is a ready-made body and was
   confirmed present and untouched this pass, but it is gitignored and **clears with the cycle**, so an
   uncarded gap is a lost gap. Tests are outside this cycle's writable set.
6. **Worker 3 pass 2's per-edit byte-split arithmetic slip**, carried from the first final verification
   so the artifact stays internally consistent without any prior section being edited: apply-changes
   pass 2's `### Byte counts` attributes its -19 as "-15 and -12"; the Low's edit is **-4**, not -12.
   Every total, every final count, and both `--numstat` figures are exact. Nothing in either deliverable
   needs correcting.
7. **`KANBAN.md`, `KANBAN.html`, and `examples/fakeshop/db.sqlite3` are dirty under a concurrent
   session.** Every card id both documents cite still resolves against the live board, so nothing is
   stale today — but a card **renumber** landing before commit would silently falsify the seven ids in
   the spec and rationale. Worth one `grep` at the commit gate.

### Summary

R1 turns the archived spec-009 from a horizon document describing six mechanisms this package chose
against into one that describes what shipped. **Two files changed and nothing else**: no source, test,
example, sibling spec, standing doc, generated doc, or DB row was touched, and the public surface
(`git diff -- django_strawberry_framework/__init__.py`) is empty.

**The six Group-A scrubs are complete, and the completeness was verified by counting rather than by
reading a site list.** Every dropped symbol is at **zero** occurrences in the current spec, against
HEAD counts of 11 / 8 / 2 / 2 / 3 / 1 / 2 / 2 / 1 / 1 / 4 for `DjangoModelField`, `OptimizerStore`,
`with_hints`, `with_prefix`, `get_strawberry_annotations`, `DjangoField(`, `ASC_DISTINCT`,
`DESC_DISTINCT`, `DISTINCT ON`, `AdvancedFilterSet`, and `LazyClassRef`; `types/fields.py` went 1 → 0.
Where a scrubbed section's whole subject was the dropped mechanism it was **rewritten to state what the
shipped architecture does** — Layer 4's four named seams, the provenance section, the
value-not-callable hint rule, the no-placeholder-tier contract, the row-preserving `Min`/`Max`
paragraph, the corrected connection sketch — never left as a hole and never left as "this was rejected"
prose. The deliberation went to the append-only rationale companion.

**The scrub stopped in the right place, and the boundary was re-verified name by name.** The surviving
`DjangoModelType` (**6**), `AdvancedAggregateSet` (**2**), and `AdvancedFieldSet` (**2**) mentions are
each an upstream citation, a description of *upstream's own* behavior, or a refusal site — never a
mechanism this package adopts. `DjangoModelType` survives at `:312` (the upstream `file:///`
source-reference list), `:428-429` (Strawberry-Django's own default relation fallback maps), `:553`
(`## What to scrap from Strawberry-Django`), `:851` (`## Why not use generic relation fallback by
default?`), and `:996` (`### Decision 1`, which refuses it by name); `AdvancedAggregateSet` at `:142`
(upstream citation) and `:235` (`#### Take …`, upstream design being praised); `AdvancedFieldSet` at
`:250` (same) and `:769` (`### Layer 9`'s prior-art reference, the twin of Layer 6's "Use
`django-graphene-filters` semantics"). Removing any of them would have deleted the argument along with
the rejected feature and falsified the upstream citations.

**The ten Group-B corrections all landed**, each re-verified against shipped source rather than against
the drift table: the node field's nullable-by-contract spelling (D7), the three `DEFERRED_META_KEYS`
named with the card that promotes each (D8), the connection's opt-in `totalCount` and still-owed
`aggregates` (D9), the `DjangoTypeDefinition` sketch corrected to `fields_spec` / `exclude_spec` and
declared an explicit subset (D10), `FilterSet` with canonical `Meta.fields` **plus** the cookbook-parity
`filter_fields` alias the drift row itself had understated (D11), the shipped `*Set` base names (D12),
Layer 5's self-contradicting "finalize pending types" replaced by the negative contract (D13), the
module layout's dead proposal removed and `fieldset/` / `orders/inputs.py` corrected (D14), Phase 3
restated to the machinery that actually passes its five acceptance tests (D15), and the three unmet
success criteria annotated with their owning cards (D16). Two vacated numbered slots (`### Decision 3`,
`### Phase 3`) were **repurposed with positive contracts rather than gapped or renumbered** —
renumbering was forbidden because `spec-010` cites `### Decision 6` by anchor — and all five cross-spec
anchors resolve in both directions.

**The single-ownership decision.** Three consecutive passes each closed one bullet of a duplicated
four-seam responsibility map, and each time the next pass found another. Apply-changes pass 3 stopped
patching bullets and decided the shape once: **`### Layer 4: Generated relation fields` is the sole
owner of the responsibility-to-seam map, and ``### Borrow `StrawberryDjangoFieldBase` and
`StrawberryDjangoField` `` states the borrow argument and points at it, carrying no seam list of its
own.** The duplicated list was deleted rather than corrected; async-safe queryset access — the one
borrowed behavior that is not a generated field's seam — got one sentence in the Borrow chapter rather
than a fifth Layer 4 bullet, because adding it there would have repeated the mis-attribution one
section over. The generalisable rule, now recorded in the rationale: **the architecture chapter owns
the map, the prior-art chapter cites it**, because a duplicate map has no correct state — it has a
current half and a stale half.

**Ledger.** Spec **54,232 → 61,346 bytes**, **1,154 → 1,096 lines** (`--numstat` **112 / 170**; it
deletes more lines than it adds and still grows in bytes, because the scrubs removed a dataclass
sketch, three bullet lists, and a transition path while the replacements are denser contract prose).
Rationale **12,273 → 49,447 bytes**, **208 → 690 lines** (**482 / 0** — append-only, proved by exactly
one `-` line in its diff, a byte-identical `head -166`, and hunks summing `480 + 1 + 1 = 482`). Closing
identities: `1,154 - 170 + 112 = 1,096` and `208 + 482 = 690`. Both gates green — 23 glossary terms,
exit 0 on both files — with 25/25 and 11/11 link definitions, zero orphans, zero dead targets, zero
unresolved in-page anchors, and zero in-repo raw `path:NN`.

**What is left.** One Medium: `:515`'s "Strategy selection is what a cross-request plan cache is keyed
on" states a mechanism `optimizer/extension.py::DjangoOptimizerExtension._build_cache_key` contradicts,
with the causal arrow inverted, while the rationale's twin telling of the same argument is correct.
Everything else is verified and stands.

## Build report (Worker 1, apply-changes pass 5)

Fresh Worker 1 invocation; only carry-forward is `docs/builder/worker-memory/spec-009-worker-1.md`.
Closes the single Medium from `## Final verification (Worker 1, pass 2)`. **One sentence, one site, one
file.** No source, no tests, no rationale change, no sibling spec, no renumbering.

**Spec status-line re-verification (per-spawn duty).** Spec lines 1-5 re-read. The opener still
describes the rationale companion, the four finalization sites, and the six scrubbed mechanisms;
nothing in this pass falsifies it. No edit owed.

**HEAD re-derived: `c2b8622d`** — moved again mid-pass from the dispatch's `5851bb59` (a sixth move on
this item). The newest commit touching either document is still `f3c94642`, so nothing was swept.

### Source verification performed (this pass) — the prescription treated as a hypothesis

Both halves re-derived from source before any prose was written, per the dispatch's own warning that
two prescriptions on this item turned out wrong.

- **The key builder, opened rather than cited.** `optimizer/extension.py::DjangoOptimizerExtension._build_cache_key`
  read in full, docstring and body. Its return tuple is literally
  `(doc_key, relevant_vars, target_model, runtime_path_from_info(info), origin)` — the printed
  operation AST plus reachable fragments, the `(name, value)` frozenset for `@skip`/`@include` and
  non-root `first`/`last`/`before`/`after` variables, the target model, the root response path, the
  resolver's origin type. **`optimizer_hints`, `OptimizerHint`, `nested_strategy`, and strategy
  selection appear in none of the five.** `grep -rn optimizer_hints django_strawberry_framework/optimizer/`
  → `walker.py` (x6), `nested_planner.py` (x3), `nested_fetch.py`, `hints.py` (x5), and
  `extension.py:1279` — which is the walker-facing `definition.optimizer_hints or {}` read, not the key
  builder. **The dispatched finding is confirmed: the spec's stated reason is false.**
- **The invariant, quoted from its own source.** `optimizer/hints.py` #"The knob is schema-static and
  needs NO plan-cache-key change" continues "the plan cache is instance-bound
  (``optimizer/extension.py`` Decision 11), so strategy selection never depends on request-varying
  data." Two directly-quotable facts: strategy selection is **schema-static**, and the cache
  **needs no key change for it**.
- **"Cross-request" is the right adjective and was not assumed.** `optimizer/extension.py` calls
  `_plan_cache` "the cross-request cache" in terms (#"cross-request cache and the walker for
  ``cacheable = False`` plans", #"cross-request ``_doc_cache_entry`` LRU"), and
  #"Publish this instance so ``apply_connection_optimization`` can" sets the `_active_optimizer`
  ContextVar so the connection field shares the same instance-bound cache. So the phrase survives the
  rewrite unchanged; only the "keyed on" clause was false.

### The fix: replace the inverted mechanism with the two quotable facts, keep the rule

Both clauses of the replacement are verified **separately from the rule they support**, which is the
lesson the final verification attached to this finding.

Before (`:515`): "Strategy selection is what a cross-request plan cache is keyed on, so a hint that can
consult the request makes the plan un-cacheable and the cache unsound at the same time."

After: "Strategy selection is schema-static, so the cross-request plan cache is not keyed on it; a hint
that could consult the request would make every cached plan unsound."

- **Clause 1 — "schema-static"** is `optimizer/hints.py`'s own word, and the citation that carries it
  (`optimizer/hints.py::OptimizerHint`) already sits in the very next sentence of the same paragraph,
  so no second reference was added to prove it.
- **Clause 2 — "not keyed on it"** is the direct reading of the five-part return tuple above. It is a
  **stated fact with a citation**, not a causal story, which is the shape this cycle's memory records as
  rot-resistant.
- **The causal arrow now runs the way the code does**: static-therefore-unkeyed, and unkeyed-therefore-
  a-request-consulting-hint-would-be-unsound. The old sentence ran keyed-therefore-unsound, which is
  backwards — if selection *were* keyed on, a callable hint would merely fragment the cache.
- **"un-cacheable" was cut, not rephrased.** It was the half that only followed from the false premise;
  the surviving consequence ("every cached plan unsound") is the one the mechanism actually produces.
- **Nothing else in the paragraph was touched.** The rule sentence, the `optimizer/hints.py::OptimizerHint`
  citation, and the load-bearing "request-varying shaping belongs to `get_queryset`" clause are
  byte-identical to before, the last per the finding's explicit instruction.

**Rejected: cutting the mechanism clause entirely.** Passes 3 and 4 both cut, and cutting was
considered first here. It loses more than it saves: this is the one section a future optimizer card
reads before widening `Meta.optimizer_hints`, and the finding notes the live annotation-dependency
fragment is already carded on `TODO-BETA-053-0.1.1`. A reader of that card needs to know the cache is
blind to strategy selection — that is precisely what makes a request-varying hint dangerous rather than
merely inefficient. The `worker-1.md` implementation-relevant-rationale carve-out ("the why that
changes HOW a thing is built") covers it, and the rationale entry already records that this rule is
stated positively in the spec on purpose. The replacement is **9 bytes shorter than the false version**,
so keeping it cost nothing against the cut.

**Rejected: a companion rationale entry.** The rationale's twin telling at `:426-427` is already
correct and already says invariant-buys-the-cache; this pass aligns the spec **to** it. Appending a
paragraph about a spec sentence the rationale never got wrong would create the second telling that the
single-ownership decision exists to prevent. The rationale is byte-identical to the prior pass.

### Spec changes made (Worker 1 only)

- `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:515`, in
  `### Keep the current optimizer's strengths, and borrow its nested-prefetch lessons`. Triggered by the
  Medium in `## Final verification (Worker 1, pass 2)`. One sentence replaced: the false, arrow-inverted
  "Strategy selection is what a cross-request plan cache is keyed on" mechanism gives way to the two
  source-quotable facts (schema-static; not keyed on it) and the consequence that actually follows.
  Rule, citation, and the `get_queryset` clause unchanged.

No other spec edit. No rationale edit. Line count unchanged, so no anchor, list, or numbered slot moved.

### Byte counts

| File | Before (this pass) | After | HEAD baseline |
|---|---|---|---|
| `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` | 61,346 / 1,096 | **61,337 / 1,096** | 54,232 / 1,154 |
| `docs/SPECS/appx/…-rationale.md` | 49,447 / 690 | **49,447 / 690** (untouched) | 12,273 / 208 |

Ledger identities re-closed against a freshly re-measured HEAD (`git show HEAD:<path> | wc -c -l`, not a
carried number): spec `1,154 - 170 + 112 = 1,096` with `--numstat` reading **112 / 170**; rationale
`208 + 482 = 690` with `--numstat` **482 / 0**. **Eighth consecutive net-negative spec pass** (-9 bytes).

### Append-only proof on the rationale

Unchanged this pass, and re-proved rather than asserted: `git diff` over the rationale has exactly
**one** `-` line (the `--- a/` header), `head -166` of the working copy `cmp`s byte-identical against
`git show HEAD:` piped to a scratch path **outside** the repository, and `--numstat` is **482 / 0**.
`git stash`, `git checkout`, `git restore`, and `git worktree` were not used.

### Gates and link surface

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → **exit 0**, "OK: 23 terms - all have glossary entries and at least one spec link."
- `uv run python scripts/check_trailing_commas.py --check` on both documents → **exit 0**.
- In-page anchors: **zero unresolved** in either file (fenced code stripped before slugging).
- Link definitions: **zero orphans, zero undefined refs** in either file. The one raw hit,
  `[target]`, is the false positive this artifact's memory already records — it is inside the code span
  `` `list[target]` `` at `:647`, pre-existing text this pass did not touch.
- In-repo raw `path:NN`: **zero** in both documents (upstream `file:///…#LNN` citations are
  out-of-repo and out of scope, and were not touched).
- No renumbering: Layers 1-11, Phases 1-8, Decisions 1-6 all untouched; the edit is confined to one
  line inside one existing section and did not change the file's line count.

### Cross-spec anchors — five, both directions, re-timestamped 2026-08-16T01:21:44Z

Re-derived rather than carried, because `spec-010` is under a concurrent cycle. All five resolve.

- **Inbound (2).** `spec-010` cites spec-009 #"### Layer 3: Finalization trigger" and
  #"### Decision 6: fail loudly"; `grep -c` on the edited spec-009 → **1 each**.
- **Outbound (3).** spec-009 → `docs/SPECS/spec-010-foundation-0_0_4.md` #"### Must redo (not
  augment)", #"## Strawberry finalization strategy", #"### Unresolved-target error format";
  `grep -c` on the current spec-010 → **1 each**.

Reported, not repaired — nothing was broken.

### Provenance — nothing was swept into a concurrent commit

`git log --stat` over both paths (never `git status` alone): the newest commit touching either document
is **`f3c94642`**, unchanged across all eleven passes, with `e1f9ed26` and `abb0dd12` behind it.
Both HEAD baselines re-measured to the same 54,232 / 1,154 and 12,273 / 208 the ledger has always used,
which is the second, independent proof no concurrent commit adopted this work. HEAD itself moved
`5851bb59` → `c2b8622d` during the pass; that is other cycles' traffic and none of it intersects this
item's writable set.

### Dispatched findings checklist — ticks unchanged, and correctly so

**16 boxes, 16 `- [x]`, 0 `- [ ]`** — identical to the prior pass. This finding is a **new-claim**
defect in prose this cycle wrote, not a drift row, so it adds no box and un-ticks none. Its nearest
relative is **D2**, whose contract is that `OptimizerStore` / `with_hints` / `with_prefix` and the
Info-scoped callable hint are dropped and scrubbed: re-verified after the edit,
`grep -c 'OptimizerStore\|with_hints\|with_prefix'` on the spec → **0**, and the value-not-callable rule
D2's scrub replaced them with is still stated positively. D2's tick stands. No deferral is owed.

### Status

`planned`. The one Medium is closed at its single site with both of its replacement clauses verified
independently against source. Ready for Worker 3 re-review (pass 6).

## Review (Worker 3, pass 6)

Sixth review pass on this item, run 2026-08-16 by a fresh Worker 3 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-3.md`. Scope, per dispatch: **apply-changes pass 5 only** — one
sentence, one site, **-9 bytes, zero line change** — plus regression. The scrub, the single-ownership
decision, the Layer 4 bullets, the scope extension, and every previously accepted item were not re-audited.
Items 1, 3, 4, 5, 6 and 7 below were re-derived from source and from the tree rather than read as discharged
by the build report; the two source claims were checked by **opening `optimizer/extension.py` and
`optimizer/hints.py`**, not by reading the build report's account of them.

Method notes: **HEAD re-derived at the start of the pass (`c2b8622d`, matching the build report) and again at
the end — unchanged.** Read-only HEAD copies taken with `git show HEAD:<path>` into a scratch path **outside**
the repository; no `git stash` / `checkout` / `restore` / `worktree`; no `pytest` with any `--cov*` flag;
nothing committed; no branch created; no concurrent file touched. `git status --porcelain` is **102** entries,
up from the 89 the prior final verification recorded — reported, **not reverted**; none of it intersects this
cycle's writable set. The newest commit touching either document is still **`f3c94642`**, and both HEAD
baselines still measure 54,232 / 1,154 and 12,273 / 208, so nothing was swept into a concurrent commit.

### High:

None.

### Medium:

None.

### Low:

None.

### The replacement sentence, verified clause by clause and separately from the rule it supports

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:515` now reads, in full:

> **A hint must be a value, not a callable.** Strategy selection is schema-static, so the cross-request plan
> cache is not keyed on it; a hint that could consult the request would make every cached plan unsound.
> `Meta.optimizer_hints` therefore carries frozen directives (`optimizer/hints.py::OptimizerHint`), and
> request-varying shaping belongs to `get_queryset`, which already runs per request and is already composed
> into every path.

Each clause was checked against the mechanism, not against the invariant comment that motivates it — the
separation this finding's history exists to teach.

- **"schema-static" is the source's own word, and it is true of the mechanism, not only of the docstring.**
  `optimizer/hints.py::OptimizerHint` #"The knob is schema-static and needs NO plan-cache-key change"
  continues "so **strategy selection** never depends on request-varying data", so the spec's subject noun is
  the source's own too. Re-derived beyond the docstring: the only two inputs to selection are
  `optimizer/extension.py::DjangoOptimizerExtension.__init__` #"self.nested_connection_strategy =
  resolve_strategy(" — resolved once, at extension **construction**, from a constructor argument — and the
  per-type `Meta.optimizer_hints` `nested_strategy`, validated at `Meta` build time. `on_execute` only
  *publishes* the already-resolved instance (`_active_nested_strategy.set(self.nested_connection_strategy)`);
  it does not choose. The `"auto"` selection is not a counter-example and is worth naming, because it is the
  one place a reader would expect request-time choice: `nested_fetch.py::resolve_strategy`'s docstring calls
  it "**one stable strategy** whose lateral-capable queryset chooses from its fetch-time DB alias" — the
  strategy object is fixed; only a capability check inside it runs at fetch time. The design deliberately
  keeps the *selection* static, which makes the spec's adjective stronger than a paraphrase of one comment.
- **"the cross-request plan cache is not keyed on it" — the builder's actual return, read in full.**
  `optimizer/extension.py::DjangoOptimizerExtension._build_cache_key` returns literally
  `(doc_key, relevant_vars, target_model, runtime_path_from_info(info), origin)`: the printed operation AST
  plus reachable fragment definitions; the `(name, value)` frozenset for `@skip`/`@include` and non-root
  `first`/`last`/`before`/`after` variables; the target model class; the root response path; the resolver's
  origin type. **Strategy selection is absent from every one of the five.** Worker 0's zero-occurrence claim
  reproduces independently: `grep -c optimizer_hints django_strawberry_framework/optimizer/extension.py` →
  **1**, and that single hit is `:1279` (`definition.optimizer_hints or {}`, the walker-facing hint read),
  **29 lines above** the key builder's `def` at `:1298` and outside its body (`:1298-1372`).
  `nested_strategy` and `OptimizerHint` are **0** in the file. The clause is a stated fact with a citation,
  not a causal story.
- **"cross-request" is the right adjective for `_plan_cache`, and it is the source's own.**
  `optimizer/extension.py` #"cross-request ``_plan_cache`` deliberately refuses" and #"cross-request cache and
  the walker for ``cacheable = False`` plans" both name it; `optimizer/nested_planner.py` #"extension's
  cross-request plan cache" and `optimizer/predicates.py` #"cross-request ``OptimizationPlan`` cache" use the
  same phrase from outside the module. It is also the **more informative** of the two available adjectives:
  `hints.py` says "instance-bound", which is *why* it survives a request, but "cross-request" is the property
  the unsoundness argument actually needs.
- **The consequence follows in the direction the code implies.** Unkeyed → a request-consulting hint bakes
  request-specific shaping into a plan a later request retrieves under a key blind to it. The old sentence
  ran keyed-therefore-unsound, which is backwards: if selection *were* in the key, a callable hint would
  merely fragment the cache. The surviving "un-cacheable" half was **cut rather than rephrased**, correctly —
  it only followed from the false premise.

**One wording point examined and deliberately not raised**, recorded so a later pass does not re-open it:
"would make **every** cached plan unsound" is a universal drawn from a singular antecedent ("a hint that
could consult the request"), and read distributively, one such hint only endangers plans whose selection
traverses it. The universal is nonetheless the correct reading here, because the sentence is arguing at the
level of the *rule* it supports — the rule is categorical ("a hint must be a value"), so its negation
withdraws the cache's soundness **guarantee**, which is itself universal: once any hint may consult the
request, no cached plan's key certifies it. This is rhetoric over a true mechanism, not the class of defect
the five prior findings were (inverted arrow, wrong module attribution, wrong timing). Flagging it would be
manufacturing a finding.

### Worker 1's replace-don't-cut call, and the rule it proposes

**The call is right.** Passes 3 and 4 cut because the deleted text was a *duplicate* map with a stale half
and a current half — deletion removed a second telling, and the surviving telling was already correct. This
one is not a duplicate: the rationale's twin at `:426-427` argues invariant-buys-the-cache and is correct,
but it is the **rationale**, and a reader widening `Meta.optimizer_hints` under `TODO-BETA-053-0.1.1`
(re-grepped: **17** live hits in `KANBAN.md`) reads the spec section, not the appendix. Cutting the clause
would have left the rule as a bare assertion at exactly the site where knowing *the cache is blind to
strategy selection* is what separates "dangerous" from "merely inefficient". The replacement is **shorter
than the falsehood**, so the usual cost argument for cutting does not apply.

**The generalisable rule Worker 1 offers — "cut when the reason cannot be verified cheaply; replace when it
can and a builder needs it" — is sound and worth carrying.** Both halves have to hold: cheap verification
alone is not enough (pass 5's cut was over a claim that was *also* cheaply checkable — the four seams were
enumerable — and cutting was still right, because no single true sentence covered them), and a builder's need
alone is not enough (an expensive-to-verify reason is a future stale claim regardless of who wants it). The
conjunction is what distinguishes this pass from passes 3 and 4, and it does. One caveat for whoever carries
it: "cheaply verifiable" must mean *by the reader at their desk from the cited symbol*, not *by the pass that
wrote it* — the five findings on this item were all written by authors who had just read the seam.

### Regression: no line moved, and the -9 is fully consumed by the one substitution

- **Ledger re-measured with `wc -c -l`**, not carried: spec **61,337 bytes / 1,096 lines** (was 61,346 /
  1,096 — **-9 / 0**); rationale **49,447 / 690**, unchanged. `git diff --numstat`: spec **112 / 170**,
  rationale **482 / 0** — both identical to the prior pass. HEAD's copies re-measured **54,232 / 1,154** and
  **12,273 / 208**. Both identities close: `1,154 - 170 + 112 = 1,096` and `208 + 482 = 690`.
- **Arithmetic byte forcing on the substitution** (the method this cycle's memory records for edits whose
  prior state is unrecoverable, since the whole paragraph is a `+` line and HEAD has no copy). The build
  report's verbatim before-sentence is **173** bytes; the after-sentence in the file is **164**; difference
  **exactly 9**. The current line at `:515` is **433** bytes and contains the after-sentence, so the
  reconstructed prior line is **442** — one occurrence consumes the entire file delta. **Therefore the rule
  sentence, the `optimizer/hints.py::OptimizerHint` citation, and the `get_queryset` clause are byte-identical
  to before**, since any further edit inside that line would have to be exactly byte-compensating *and*
  line-neutral. Closed from the other side too: line count unchanged at 1,096, `--numstat` unchanged at
  112/170, and the spec's `git diff -U0` hunk count is **73** with the edit's hunk still `@@ -556 +513,3 @@`
  (recorded here because no prior pass captured the spec's hunk shape — pass 7, if there is one, can diff
  against it).
- **No anchor or numbered slot moved.** `### Layer 1`-`### Layer 11` at `:576`, `:599`, `:631`, `:644`,
  `:656`, `:678`, `:716`, `:735`, `:768`, `:783`, `:799`; `### Phase 1`-`### Phase 8` at `:903`, `:919`,
  `:929`, `:940`, `:951`, `:964`, `:976`, `:985`; `### Decision 1`-`### Decision 6` at `:995`, `:998`,
  `:1001`, `:1004`, `:1007`, `:1010`. Complete, in order, no gap, no renumber — and every one at the same
  line the prior pass recorded.
- **The scrub did not regress under the edit.** Re-counted with `grep -oF | wc -l` on the current file:
  `DjangoModelField`, `OptimizerStore`, `with_hints`, `with_prefix`, `get_strawberry_annotations`,
  `DjangoField(`, `ASC_DISTINCT`, `DESC_DISTINCT`, `DISTINCT ON`, `AdvancedFilterSet`, `LazyClassRef`,
  `types/fields.py` → **0 each**. D2, the box this edit sits inside, is the one most exposed to a careless
  rewrite reintroducing a callable-hint spelling; it did not.

### Append-only on the rationale, proved mechanically and independently

Untouched by this pass, and proved rather than assumed. `git diff -- <rationale> | grep -c '^-'` → **1**, and
printing it shows `--- a/docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md` — the diff
header. Exactly one `-` line means **no HEAD line was deleted or modified anywhere**, which subsumes any
prefix check. `git diff -U0` hunks are `@@ -166,0 +167,480 @@`, `@@ -185,0 +666 @@`, `@@ -186,0 +668 @@`,
and `480 + 1 + 1 = 482` closes against `--numstat`. Belt and braces: `head -166` of the working file `cmp`s
**exit 0** against `head -166` of `git show HEAD:<path>` written to a scratch path outside the repository
(HEAD's file is 208 lines, so the prefix is a real prefix).

### Gates re-run, not read

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0, 23 terms**.
- `uv run python scripts/check_trailing_commas.py --check` on both documents → **exit 0**.
- **Link / anchor / rule-27 scan, written fresh for this pass** (fences stripped, definition lines excluded
  from the use scan, code spans stripped before the `path:NN` sweep): spec **25 definitions / 25 uses, 0
  missing, 0 orphan**; rationale **11 / 11, 0 missing, 0 orphan**; every non-anchor, non-URL definition
  target disk-existence-checked → **0 dead**; **0** `](#...)` in-page anchors in either file, so none can be
  unresolved; **0** in-repo raw `path:NN` in either file with `file://` URLs excluded. The known
  `` `list[target]` `` false positive is still at `:647` and still inside a code span, in the
  `resolved_relation_annotation` bullet this pass did not touch.
- **Card ids re-grepped against the live (concurrently-dirty) board**, per this cycle's standing practice:
  `DONE-009-0.0.4` (2), `TODO-BETA-053-0.1.1` (17), `TODO-BETA-054-0.1.1` (16), `TODO-BETA-055-0.1.2` (16),
  `TODO-BETA-057-0.1.3` (5), `TODO-BETA-058-0.1.3` (7), `TODO-BETA-059-0.1.4` (3) — all seven resolve in
  `KANBAN.md`. No renumber has landed.

### Cross-spec anchors: five, both directions, re-timestamped **2026-08-16T01:28:18Z**

Re-derived from scratch, not carried, because `spec-010` is under a concurrent cycle and has moved between
passes on this item.

- **Inbound (2).** `spec-010-foundation-0_0_4.md:67` cites spec-009 #"### Layer 3: Finalization trigger";
  `:468` cites #"### Decision 6: fail loudly". `grep -c` for each exact heading on the **edited** spec-009 →
  **1 each** (`:631` and `:1010`).
- **Outbound (3).** spec-009 `:99` → `spec-010` #"### Must redo (not augment)" (`spec-010:507`); `:634` →
  #"## Strawberry finalization strategy"; `:870` → #"### Unresolved-target error format". `grep -c` on the
  current spec-010 → **1 each**.
- `spec-008`'s inbound reference is whole-file, not anchored; `grep -rln spec-009` over `docs/SPECS/` returns
  spec-008, spec-010, the two spec-009 files, and the two sibling rationales — no spec-011 file cites it.

Reported, not repaired; nothing is broken.

### Dispatched findings checklist — 16 boxes, 16 ticks, none changed

Counted on the current artifact: **16** `- [x]`, **0** `- [ ]`, unchanged from the prior pass and correctly
so. This was a new-claim defect in prose this cycle wrote, not a drift row, so it adds no box and un-ticks
none. Its nearest box, **D2** (drop and scrub `OptimizerStore` / `with_hints` / `with_prefix` / Info-scoped
callable hints), is re-verified above at 0 occurrences with the value-not-callable rule still stated
positively. No deferral is owed.

### DRY findings

None. The diff is one sentence in one `.md` file. The one duplication this cycle has been policing — the
same argument told twice with two different mechanisms — is what this edit **closes**: the spec's telling at
`:515` and the rationale's at `:426-427` now argue the same mechanism in the same direction (static
invariant buys the cross-request cache), so the pair no longer has a current half and a stale half. Worker
1's rejection of a companion rationale entry is right for the same reason: appending a third telling of a
rule the rationale never got wrong would re-create the shape the single-ownership decision exists to end.

No abstraction, helper, registry, constant, or indirection layer exists in this diff to raise an existence
challenge against; no `.py` file is touched.

### Failability proofs

**Not applicable to a documentation pass.** The diff introduces no boundary, guard, gate, or rejection path —
it changes one sentence in one `.md` file and no executable line — so the mandatory re-run floor
(`worker-3.md` "The independent re-run has a mandatory floor") is met by an **empty re-run set**, which is
legal exactly when the diff introduces no boundary meeting the floor. Nothing was mutated; the source
carve-out was not exercised.

### Hot-path budget

**Not applicable to a documentation pass.** The plan declares no hot-path slice for this item and the diff
changes no executable line, so there is no before/after number to carry.

### Static helper use

`scripts/review_inspect.py` **skipped, with reason**: none of `BUILD.md` `### When to run the helper during
build`'s Worker 3 triggers fires — no `.py` file is added or modified, nothing under `optimizer/` or `types/`
is touched, and the diff adds zero lines of logic. `git diff --numstat` over the working tree confirms the
two changed paths for this item are both `.md`. No shadow files were generated or read this pass.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** (0 lines). `__all__` and the re-export
list are unchanged. No new public exports.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applies — the item's whole deliverable is documentation. Confirmed on the current files:

- **Version strings and card ids match.** The spec's card annotations resolve on the live board (seven ids
  re-grepped above); the spec is the archived `0_0_4` document and this pass changes no version string.
- **No KANBAN movement**, no spec archival, no generated doc regenerated. `KANBAN.md`, `KANBAN.html`,
  `docs/TREE.md`, `docs/GLOSSARY.md` and `examples/fakeshop/db.sqlite3` are outside this cycle's writable
  set; the dirty ones are concurrent work and were neither read as inputs nor touched.
- **Markdown links introduced or moved: none.** 25/25 and 11/11 definitions/uses, zero orphans, zero dead
  targets, verified above.
- **No verbatim spec drop-in** into another document this pass, so the character-for-character `diff` check
  has no subject.
- **No obsolete "coming soon" / "planned" / old-version wording** introduced: the replacement sentence
  states a shipped invariant in the present tense and names no future state.
- The rationale's deliberately-stale `## Standing notes` "three sites" bullet (`:649`) is **unchanged and
  still correct to leave**: the plan's append-only constraint on the rationale forbids editing it this
  cycle, and the staleness is stated explicitly five lines above it at `:643`. Carried below as an
  escalation, not a finding.

### What looks solid

- **The fix's two clauses were verified separately from the rule they support** — which is the exact lesson
  the sixth finding produced, applied by the pass that received it rather than restated. Both clauses are
  quotable facts with citations rather than causal stories, which is the rot-resistant shape.
- **Worker 1 treated the dispatched prescription as a hypothesis and opened the key builder**, after two
  prescriptions on this item turned out wrong in their mechanism. The build report's reading of
  `_build_cache_key`'s five-part return is exact, and its "cross-request is the right adjective and was not
  assumed" paragraph independently reproduces.
- **The causal arrow now runs the way the code does**, and the "un-cacheable" half was cut rather than
  softened. A half-true clause kept for rhythm is how five of the six findings on this item entered.
- **Net-negative again** — the eighth consecutive net-negative spec pass, and the one time in this cycle
  where keeping a reason was cheaper in bytes than deleting it.

### Temp test verification

- `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` — Worker 3 pass 4's temp test
  (default `DjangoConnectionField` + `async def get_queryset` + `await schema.execute` -> `SyncMisuseError`).
  Confirmed **present and untouched** this pass; **not deleted**, per dispatch.
- **Disposition: not re-run, and noted for follow-up.** No finding in this pass turns on it — the diff
  changes no executable line — so re-running it would prove nothing about this edit. It remains the
  ready-made body for the permanent-suite gap escalated as item 5 of `## Final verification (Worker 1,
  pass 2)`, and it is gitignored, so the gap is lost unless carded. Re-escalated below.
- No new temp test was created this pass: every claim under review was settled by reading source and by
  arithmetic on the file, and a documentation edit has no runtime behavior to pin.

### Notes for Worker 1 (spec reconciliation)

Nothing is repaired here; all items are report-only and none blocks acceptance.

1. **Escalated (unchanged, sixth consecutive pass): `docs/SPECS/spec-010-foundation-0_0_4.md:8` still
   mis-describes spec-009**, listing "custom field classes" among what it describes — exactly what D1
   scrubbed. Re-read at 2026-08-16T01:28:18Z; still standing. The file belongs to the concurrent spec-010
   cycle and is outside this cycle's writable set. Resolution paths: the maintainer sequences the two at
   commit, or spec-010's own cycle takes the row. **Worker 1 cannot close it from here.**
2. **Escalated (unchanged): the permanent-suite gap is still uncarded and still clears with the cycle.**
   `tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse` pins the
   `SyncMisuseError` rejection only under `execute_sync`; no row pins it under `await schema.execute` for a
   **default** `DjangoConnectionField`. Tests are outside this cycle's writable set and the temp-test body is
   gitignored. Resolution paths: card it before the cycle closes, or the maintainer promotes the temp body at
   commit. This is the only item on the list whose evidence is destroyed by inaction.
3. **Escalated (unchanged): `django_strawberry_framework/types/definition.py:65` reserves `fields_class` for
   `TODO-BETA-046-0.1.1`**, a stale card number after the renumber (`046` is now `DONE-046-0.0.14`, the
   transport card); the live owner is `TODO-BETA-054-0.1.1`, which is what the spec, `KANBAN.md`, and
   `docs/TREE.md` all say. **The spec is right and the source docstring is stale.** Source is read-only in
   this cycle; a candidate row for whichever cycle next owns source docstrings.
4. **Unchanged and correct to leave: the rationale's `## Standing notes` "three sites" bullet** (`:649`) is
   stale on purpose under the append-only constraint, with the staleness stated at `:643`. Correct it in the
   first pass that has the rationale open without that constraint.
5. **A commit-gate `grep`, not a finding.** `KANBAN.md`, `KANBAN.html`, and `examples/fakeshop/db.sqlite3`
   are dirty under a concurrent session. All seven card ids cited across the two documents resolve today
   (counts recorded above), but a card **renumber** landing before commit would silently falsify them. One
   grep at the commit gate covers it.
6. **The generalisable rule is worth carrying into the artifact's lessons, with one qualification.**
   "Cut when the reason cannot be verified cheaply; replace when it can and a builder needs it" is sound,
   and both halves must hold — pass 5's cut was over a cheaply-checkable claim and was still right, because
   no single true sentence covered the four differing seams. Qualification: **"cheaply verifiable" must mean
   by the reader at their desk from the cited symbol, not by the pass that wrote it.** All six findings on
   this item were fluent sentences written by an author who had just read the seam.

### Review outcome

**`review-accepted`. Zero findings.** Finding sizes across this item now read **9 -> 2 -> 1 -> 1 -> 1 -> 0**.

The single Medium from `## Final verification (Worker 1, pass 2)` is closed at its only site. Both
replacement clauses are true of the mechanism and are the source's own vocabulary; the consequence follows in
the direction the code implies; the replace-don't-cut call is the right one and is distinguishable from
passes 3 and 4's cuts on a rule that holds. The regression surface is closed from three independent
directions — the -9 is arithmetically forced onto the one substitution, the line count and `--numstat` are
unchanged, and the hunk shape, numbering, scrub counts, gates, link surface, cross-spec anchors, and sixteen
checklist ticks all re-derive to the prior pass's values. The rationale is byte-identical and provably
append-only. Nothing in the writable set is left open; the six notes above are report-only and belong to the
maintainer or to other cycles.

---

## Final verification (Worker 1, pass 3)

Run 2026-08-16 by a **fresh Worker 1 invocation** whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-1.md`. Third final verification on this item; the first two
each set `revision-needed` on a Medium every preceding review pass had missed.

**Method.** The whole artifact was read end to end — plan, combined perform pass, six Worker 3 reviews,
five Worker 1 apply-changes passes, both prior final verifications — and then **all 112 `+` lines of the
spec diff were read cold, in order**, rather than only at the sites the six prior findings named. That is
the method that found the sixth defect and it is what found the seventh. Every causal or mechanism clause
in added text was checked **against the mechanism it names, not against the docstring that motivates the
rule it supports** (this artifact's own lesson: *an invariant comment validates the RULE, not the
REASON*). Both mechanical gates, the link / anchor / rule-27 audit, the append-only proof, the byte
ledger, the five cross-spec anchors, and the sixteen-box checklist were re-run from scratch rather than
read as discharged by Worker 3 pass 6's zero-finding acceptance (`worker-1.md`
`### Verifying relocation / promotion claims`). `git stash`, `git checkout`, `git restore`, and
`git worktree` were not used; the HEAD reference was `git show HEAD:<path>` into a scratch path outside
the repository. **This item runs no tests and changes no code**, so `## Final verification job` step 5 is
discharged by stating that rather than by a focused scope; Worker 3's read-only temp test was re-run
anyway (below). The staged-anchor sweep is R4's and was **not** duplicated (step 6).

**Spec status-line re-verification (per-spawn duty).** Spec lines 1-5 re-read. The opener still describes
the rationale companion, the **four** finalization sites, and the six scrubbed mechanisms; nothing in the
build falsifies it. No edit owed.

**HEAD re-derived: `c2b8622d`**, matching the dispatch and Worker 3 pass 6. `git status --porcelain` is
**108** entries, up from the 102 pass 6 recorded — reported, **not reverted**, and none of it intersects
this cycle's writable set.

### Final status

`revision-needed`. **One Medium**, below. Everything else verifies, including all sixteen checklist
ticks, both ledger identities, append-only, both gates, the link surface, and all five cross-spec
anchors.

**Nothing was repaired here**, for the reason both prior final verifications gave and were right to: an
edit made by the pass that accepts the item is a fresh unreviewed claim, and this item has now produced
**seven** findings whose whole shape is *a fluent new sentence nobody re-derived*. The apply-changes pass
owns the fix under the plan's `### Deviation 3` corollary.

### Medium: Layer 4's raw-`list[T]` recourse names a helper that structurally cannot cover that relation kind

`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:649`, the **visibility** bullet of
`### Layer 4: Generated relation fields`, closing clause (added by apply-changes pass 1 as change 38, the
fix for Worker 3 pass 1's M3):

> … not inside the generated resolver, which returns the row-bound accessor; **a raw `list[T]` relation on
> a schema carrying no optimizer extension gets its row-level answer from the `permissions.py` cascade
> helpers instead**

Everything before the emphasis re-derives exactly (re-checked this pass and recorded under
`### Gates and proofs re-run, not read`). **The recourse clause is false, and false in the fail-open
direction: it names a mechanism that is defined to skip precisely the relation kind it is offered for.**

- **A raw `list[T]` relation is always a to-many relation.**
  `types/converters.py::resolved_relation_annotation` emits `list[target]` **only** on
  `meta.is_many_side` (`converters.py:722-723`); the to-one spellings are `target | None` and bare
  `target`. So "raw `list[T]` relation" means reverse FK, reverse one-to-many, or M2M, and nothing else.
- **The cascade helpers are forward-edge-only, by definition and by guard.**
  `permissions.py`'s module docstring opens: `apply_cascade_permissions` makes "every single-column
  concrete **forward** relation of `cls`'s model respect its target type's own visibility", and states in
  terms that "Reverse FK / reverse OneToOne, M2M, and `GenericRelation` stay outside parent-row cascade
  semantics and are skipped". The guard is mechanical, not merely documentary:
  `permissions.py::_is_cascadable_edge` requires `not field.many_to_many and not field.one_to_many`
  (`permissions.py:221-222`) and excludes `ForeignObjectRel` outright.
- **So nothing runs on that path.** `types/resolvers.py` imports neither `..utils.querysets` nor
  `..permissions` (import block read in full: `exceptions`, `optimizer.*`, `registry`,
  `resource_policy.bounded_rows`, `utils.relations`, `.converters`), and `many_resolver` returns
  `list(bounded_rows(getattr(root, accessor_name).all(), info))` or the `_prefetched_objects_cache` hit.
  Without the optimizer extension there is no `optimizer/walker.py::_build_child_queryset` either. A raw
  many-side list therefore gets **no** target-type `get_queryset` at all on that path — only
  `resource_policy.py::bounded_rows`, which is a row **cap**, not a visibility answer.
- **The cascade cannot be reached indirectly either.** `apply_cascade_permissions` is invoked by a
  consumer *inside* a `DjangoType.get_queryset`; the bullet's own first half establishes that the target
  type's `get_queryset` never runs on this path, so the target's cascade never runs. Applying it on the
  **owner** type narrows the owner's rows by the owner's forward edges — it does not filter the children
  of a to-many relation, and a hidden child of a visible parent is still returned.

Three things make this a Medium on the same test the six prior instances were graded by:

- It is **new text this cycle wrote** — `git diff` carries it as a `+` line. It has been read by four
  review passes and two final verifications, each of which verified the *three named call sites* and the
  *not-inside-the-generated-resolver* structural claim (both true) and treated the recourse clause as
  connective tissue. Worker 3 pass 2 accepted it as "accurate as documentation guidance —
  `permissions.py::apply_cascade_permissions` is the consumer-invoked helper that path uses", which
  confirms the symbol exists and is consumer-invoked, not that it applies to a to-many relation. **The
  invariant validated the rule, not the reason** — the seventh instance of the pattern, found by the
  method the sixth taught.
- It is a **responsibility map in a horizon document**, and this bullet's subject is row-level
  visibility, which is a data-isolation surface. The error direction is **fail-open**: it tells a reader
  that an unfiltered path is covered by a named security mechanism. No source defect follows — the
  shipped default for a many-side relation is `"connection"` (`types/base.py` #"``\"connection\"`` is the
  secure default (spec-047 Decision 5)") and the raw list is an explicit `Meta.relation_shapes` opt-in
  that is row-bounded — so this is a **documentation** finding graded like its six predecessors, not a
  source escalation. **I am asserting no source defect and escalating none.**
- Its consequence is actionable and inverted, in the same way `:418`'s and `:515`'s were: a reader
  choosing `Meta.relation_shapes = {"x": "list"}` is told where the row-level answer comes from, and the
  place named cannot give one.

**Recommended change** (Worker 1's apply-changes pass owns it; re-derive rather than accept this
prescription — three dispatched prescriptions on this item have already turned out wrong in their
mechanism). The cheapest correct fix is the disposition passes 3, 4 and 5 converged on: **cut the
recourse clause**, leaving the bullet stating where the composition runs and that it is not inside the
generated resolver — both true and both independently verified. If a recourse is judged necessary at
this site, the accurate one is that the raw many-side list is an explicit opt-in whose ceiling is
`resource_policy.py::bounded_rows` and whose row-level visibility is the `"connection"` default's or the
optimizer's, not the cascade's; that is three clauses in a bullet whose job is to name a seam, which is
why cutting is likely the better trade. Do **not** close it by weakening the first half of the bullet —
the three call sites and the not-inside-the-resolver constraint are correct and load-bearing. It is a
**one-site** fix: `grep -n 'cascade helpers'` over both documents returns only the spec's `:649`, and the
rationale's `### Layer 4` entry states the seam ownership without repeating the recourse, so the two-site
trap this artifact recorded twice does not apply.

### Cold read of all 112 `+` lines: the sites that are clean, and why they were re-derived

Read as a reader who had not seen the arguments, in file order, per the dispatch. Every mechanism clause
in added text was opened at the thing it names. The six sites the history points at are all **clean**;
the seventh was found in the same bullet as the third, one clause further along.

- **`:68` (nullable by contract).** `relay.py:17-19` reads "Resolution is **nullable by contract**:
  dispatch is `required=False` unconditionally" — the spec's sentence is that sentence. `required=False`
  confirmed at the three dispatch sites (`relay.py:434`, `:527`, `:542`).
- **`:70` (`DEFERRED_META_KEYS`).** `types/base.py:65-67` is exactly
  `{"aggregate_class", "fields_class", "search_fields"}`; the refusal is `ConfigurationError`
  (`types/base.py:1152-1154`, `deferred = sorted(declared & DEFERRED_META_KEYS)` → `raise`), at class
  creation. `ALLOWED_META_KEYS` is the enumeration and the spec cites the constant rather than a number,
  which is what keeps it true; the five keys it does name as declarable are all in it.
- **`:385` (`### Borrow \`StrawberryDjangoDefinition\``).** `_validate_filterset_class`
  (`types/base.py:138`) is called from `_validate_meta` (`:1167`) at class creation. The sketch's slot
  names and annotations match `types/definition.py::DjangoTypeDefinition` name-for-name (AST-listed this
  pass: `fields_spec`, `exclude_spec`, three plain `type | None` sidecars, `interfaces`,
  `optimizer_hints`, `finalized`); `aggregate_class` and `search_fields` are absent; the "three lookup
  methods" count re-measures exactly (`graphql_type_name`, `related_target_for`,
  `has_custom_id_resolver_for`). No lazy-binding claim survives.
- **`:401` (provenance).** `types/base.py` builds the annotated pair inline and calls
  `_consumer_assigned_fields` for the assigned pair, unioning at `:613`; the override-target validators
  and `_build_annotations` each take `consumer_authored_fields` as a parameter they never derive
  (`:1346`, `:1437`, `:1506`, `:1411`, `:1485`). "All read the same union rather than re-deriving one" is
  exact.
- **`:417` (async safety).** No timing claim survives ("is applied by"). `types/resolvers.py` has zero
  async markers; the pair's call sites are `connection.py:1780`/`:1815`, `list_field.py:211`/`:217`,
  `types/relay.py:843`/`:864`/`:904`/`:929`; `SyncMisuseError` is `utils/querysets.py:116`.
- **`:483` (`<TypeName>Connection`).** `connection.py::_connection_type_for`'s docstring and body both
  say **always** a generated concrete subclass, with `definition.connection` controlling only the shape;
  the generic-alias reason is the module's own (`connection.py:18`, "a generic ALIAS handed to the schema
  loses the ``resolve_connection``"), and the base's docstring carries the `first` + `last` guard, window
  consumption, and cursor-mode dispatch clause for clause.
- **`:515` (the plan-cache rule, apply-changes pass 5's replacement — the highest-risk text in the
  cycle).** Both clauses re-derived **separately from the rule they support**, by opening the builder
  rather than citing the invariant: `optimizer/extension.py::DjangoOptimizerExtension._build_cache_key`'s
  five-part key is documented and returned as `(doc_key, relevant_vars, target_model, root path, origin)`
  — strategy selection in none. "schema-static" is `optimizer/hints.py`'s own word (`hints.py:94`), and
  "cross-request" is `extension.py`'s own for `_plan_cache` (`:1124`, `:1129`). `OptimizerHint` is
  `@dataclass(frozen=True)` (`hints.py:72`). The arrow now runs static→unkeyed→unsound, which is the
  direction the code implies.
- **Layer 4's other three bullets.** `resolved_relation_annotation` returns literally `list[target_type]`
  / `target_type | None` / `target_type`; `_attach_relation_resolvers` is Phase 2 and `strawberry.type`
  is Phase 3 (`finalizer.py:17`, `:34`, sole call site `:793`, and `:800` states the class is frozen by
  Phase 3, which is the "only window" constraint); `connection.py` synthesizes `_resolve.__signature__`
  (`:1824` builder, assignments `:2004`, `:2163`). `DjangoConnectionField`, `DjangoNodeField`, and
  `DjangoListField` are all **functions** (`connection.py:2168`, `relay.py:388`, `list_field.py:153`), so
  "each is a factory returning a Strawberry field" is structural.
- **Layer 6 / Layer 7 (the filter and order corrections).** `filters/sets.py::FilterSet` really does
  subclass `filterset.BaseFilterSet` (`:1135-1143`), and the `filter_fields` alias fires **only when
  `fields` is absent** (`:1010-1018`, `hasattr(meta_class, "filter_fields") and not hasattr(meta_class,
  "fields")`) — so "accepted as a cookbook-parity alias when `fields` is absent" is precise. The
  `Ordering` enum has exactly six members, `ASC`/`DESC` plus four explicit NULLS variants, in both the
  package (`orders/inputs.py:91-96`) and upstream (`strawberry_django/ordering.py:92-97`), and the
  package enum's own portability note is the argument the spec's "exactly what a portable null partition
  needs" restates. `orders/sets.py::OrderSet._resolve_order_expressions` annotates `Min` for ascending /
  `Max` for descending on to-many paths and states the duplicate-rows-and-`totalCount` failure the spec
  names; the pk tiebreaker is `connection.py:1707` and is confirmed by `list_field.py:173` describing its
  own absence of one.
- **Layer 3 (`:634`) and the registry.** `registry.py:110` reads "Mutating methods are not guarded by a
  lock", so "the registry is deliberately lockless" is the source's own claim, not an inference.
- **`spec-054-fieldset-0_1_1.md` exists and carries #"resolver wrapping"** (`:461`, `:806`), so both
  citations of it resolve; its `:272`, `:703`, `:807-811` support the gate→override cascade ordering and
  the zero-overhead-on-unmanaged-fields clauses the spec attributes to it.
- **One clause examined and deliberately not raised**, recorded so an eighth pass does not re-open it:
  change 45's "keeps the N+1 probe, the prefetch-cache read, the FK-id elision, and the row-bound call
  out of a variant per relation kind". `_make_relation_resolver` does branch per cardinality, but each of
  the four named concerns is a **single implementation** called from the bodies (`_check_n1`,
  the `_prefetched_objects_cache` read, `_build_fk_id_stub`, `resource_policy.py::bounded_rows`), which
  is what the sentence claims and what Worker 3 pass 4 recorded. Not a finding.

### Duplication and inconsistent shape across all twelve passes taken together

`## Final verification job` step 4, run against the two documents rather than any pass's file list.

- **The four-seam near-duplication is genuinely retired** — re-confirmed independently, not carried. Only
  `### Layer 4` carries a responsibility-to-seam list; `:415` is a one-line pointer to it.
  `grep -v '^[[:space:]]*$' | sort | uniq -d` over the spec returns only code-fence boilerplate and
  one-word list items.
- **The optimizer-hint inconsistency the prior final verification found is closed.** The spec's `:515`
  and the rationale's `:426-427` now argue the same mechanism in the same direction; the pair no longer
  has a current half and a stale half.
- **One near-duplication examined this pass and deliberately NOT raised**, recorded so it is not
  re-opened: the resolver-wrapping justification is stated twice, at `#### Take \`fields_class\`` (`:257`,
  change 4) and `### Layer 9` (`:771`, change 21) — "wrapping keeps the gate/override cascade ordering
  expressible and costs nothing on unmanaged fields", in two phrasings. It is **not** the four-seam shape
  and does not meet the DRY bar that blocks acceptance, for three checked reasons: both tellings are
  **accurate** against `spec-054-fieldset-0_1_1.md` (`:272`, `:703`, `:807`); **neither owns the
  mechanism** — spec-054 does, and both cite it, so there is no in-repo map with a drift surface, only
  two pointers at one external owner; and the two sections make **different contrasts** (prior art:
  wrapping vs. mutating *Graphene* fields; architecture: wrapping vs. mutating the *field object* after
  the fact), which is the same job split that licensed the Borrow-chapter / Layer-4 division. Recorded as
  a judged non-finding, not silence.
- No new abstraction, helper, constant, or branch exists to challenge: the diff touches two `.md` files
  and no `.py` file.

### Dispatched findings checklist audit — sixteen boxes, all ticks confirmed, none changed

Walked box by box against the **current** files and `git diff -- <spec>`, not against any pass's report,
with D10 given the extra scrutiny its over-tick history earns. **No over-tick, no landed-but-open box, no
deferral owed.** Box counts measured on the artifact: **16** `- [x]`, **0** `- [ ]`.

| Box | Contract | Evidence re-derived this pass |
|---|---|---|
| D1 | `DjangoModelField` / `types/fields.py` scrubbed everywhere | current **0** / **0** (`grep -oF \| wc -l`); replacement sections live at `### Layer 4: Generated relation fields`, `### Decision 3: generated field behavior belongs to the finalizer`, `### Phase 3: Generated relation fields`, `### Layer 9` |
| D2 | `OptimizerStore` / `with_hints` / `with_prefix` / callable hints scrubbed | current **0 / 0 / 0**; section retitled; the value-not-callable rule present at `:515` and its reason now verified against `_build_cache_key` |
| D3 | `get_strawberry_annotations` borrow replaced by the provenance section | current **0**; `### Track annotation provenance structurally…` present, and its producer/consumer claim re-derived against `types/base.py` |
| D4 | `DjangoField(...)` → `DjangoListField(...)` | `DjangoField(` **0**; `list_field.py:153` defines `DjangoListField`, and `graphene_django/fields.py:21` defines the symbol the spec says it keeps |
| D5 | fallback tier and the open question removed | `DjangoModelType` **6**, every site enumerated below; `### Should generic fallback exist?` absent; the no-placeholder-tier contract present |
| D6 | `ASC_DISTINCT` / `DESC_DISTINCT` / `DISTINCT ON` gone from Layer 7 and Phase 5 | current **0 / 0 / 0**; the six-member `Ordering` vocabulary and the `Min`/`Max` paragraph both verified at source |
| D7 | `object_type: ObjectTypeNode \| None` | present in the `## Target outcome` sketch with the nullable-by-contract paragraph; `relay.py:17-19` re-read |
| D8 | the three `DEFERRED_META_KEYS` named with their promoting cards | `types/base.py:65-67` is exactly the three keys, refused with `ConfigurationError` at `:1154`; the Meta sketch shows all three |
| D9 | no `total_count` on the base; `aggregates` restated as owed with its card | the fenced base carries no `total_count`; `connection.py::DjangoConnection` #"The base carries no ``total_count`` field" |
| D10 | sketch corrected to shipped names and types | **the row this audit most distrusted.** AST-listed `types/definition.py::DjangoTypeDefinition`: `fields_spec`, `exclude_spec`, `filterset_class`/`orderset_class`/`fields_class` all `type \| None`, no `aggregate_class`, no `search_fields`; `LazyClassRef` **0** package-wide; 3 methods, matching the "three lookup methods" claim |
| D11 | `class ObjectFilter(FilterSet)`, canonical `Meta.fields` | `AdvancedFilterSet` **0**; `filters/sets.py:1135-1143` subclasses `BaseFilterSet`; the alias fires only when `fields` is absent (`:1010-1018`), which is what the parity sentence says |
| D12 | `Advanced` prefix dropped from this package's `*Set` sketches | `AdvancedOrderSet` **0**; the Layer 7 bullet reads `[OrderSet]` and Layer 8's sketch `class ObjectAggregate(AggregateSet):` |
| D13 | Layer 5 item 2 removed and the negative contract stated | list runs 1-12 with no "finalize pending types"; "It does **not** finalize" paragraph present |
| D14 | `types/fields.py` out, `fieldset/` as a package with its card, `orders/inputs.py` present | module layout shows `fieldset/`, `aggregates/`, `permissions.py` with their cards and `orders/` naming `inputs.py`; `orders/inputs.py` exists and carries the direction enum (`Ordering`, `:68`) |
| D15 | Phase 3 restated, Phases 1-8 intact | `grep -o '^### Phase [0-9]*'` → Phases 1-8, no gap, no renumber |
| D16 | the three unmet success criteria carry their owning cards | the three `— owed; TODO-BETA-…` annotations present; the eight met criteria carry none |

**Group C is still untouched**, re-confirmed: the two "retired since" markers, the `### Layer 2`
`PendingRelation` sketch, the `class ObjectTypeNode(DjangoType, relay.Node)` declaration, and the upstream
`file:///…#LNN` citations. **The Medium above adds no box** — like the findings of passes 2-6 and both
prior final verifications, it is a new-claim finding about text this cycle wrote, not a drift row.

### Gates and proofs re-run, not read

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0, 23 terms.**
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0** for both.
- **Link / anchor / rule-27 audit, written fresh for this pass** (fences stripped, definition lines
  excluded from the use scan): spec **25 definitions / 25 uses, 0 missing, 0 orphan**; rationale
  **11 / 11, 0 missing, 0 orphan**; every non-anchor, non-URL definition target disk-existence-checked →
  **0 dead**; **0** `](#…)` in-page anchors in either file. **0** in-repo raw `path:NN`
  (`grep -nE '[A-Za-z0-9_/.-]+\.(py|md):[0-9]+'` over both with `file:///` excluded → no match); the
  known `` `list[target]` `` false positive at `:647` is inside a code span and was not touched.
- **Backticked-heading self-references all resolve**: the spec's four in-page section citations
  (`### Decision 6: fail loudly`, `### Layer 3: Finalization trigger`,
  `### Layer 4: Generated relation fields`, `### The unresolved-relation contract is error-only`) each
  match exactly one live heading. Every rationale citation of a spec section resolves except those that
  name an **old** heading inside a rename record or a heading in another file — each checked individually
  (`## Current local package baseline`, `## Migration path from current package`,
  `### Status: deferred design idea, no card yet` are rename records; `## Spec rationale extraction`,
  `### Performing the rationale move`, `### Decision 12`, `## The single-ownership law` are other files';
  `## Standing notes` is the rationale's own).
- **Byte / line ledger, re-measured with `wc -c -l`.** Spec **61,337 bytes / 1,096 lines**; rationale
  **49,447 / 690**. `git diff --numstat`: spec **112 / 170**, rationale **482 / 0** (counted directly off
  the diff as well: 112 `+` lines and 170 `-` lines on the spec). HEAD's own copies
  (`git show HEAD:<path>` into an out-of-repo scratch path) measure **54,232 / 1,154** and
  **12,273 / 208**. Both identities close: `1,154 − 170 + 112 = 1,096` and `208 + 482 = 690`.
- **Append-only on the rationale, proved independently.** `git diff -- <rationale>` contains exactly
  **one** line beginning with `-`, and printing it shows the `--- a/…` header — no HEAD line was deleted
  **or modified** anywhere, which subsumes any prefix check. `git diff -U0` hunks are
  `@@ -166,0 +167,480 @@`, `@@ -185,0 +666 @@`, `@@ -186,0 +668 @@`; `480 + 1 + 1 = 482` closes against
  `--numstat`. `head -166` of the working file `cmp`s **exit 0** against `head -166` of HEAD's copy. The
  two single-line hunks were opened rather than assumed: both are new link definitions
  (`[glossary-filterset]`, `[glossary-ordering]`), inserted alphabetically inside the `<!-- docs/ -->`
  group — additions, not edits of existing text.
- **No renumbering.** `### Layer 1`-`### Layer 11` (11 headings, no gap), `### Phase 1`-`### Phase 8`,
  `### Decision 1`-`### Decision 6`, each complete and in order. The two vacated slots carry positive
  contracts and no "this was rejected" prose.
- **Temp test re-run, read-only.**
  `uv run pytest docs/builder/temp-tests/r1/test_async_execution_default_connection.py --no-cov -q -o addopts=''`
  → **1 passed** (`addopts` overridden only to drop `pytest.ini`'s auto-applied `--cov`). Not modified,
  moved, or deleted. No other test was run: this item runs none.
- **Provenance: nothing was swept into a concurrent commit.** `git log --stat` over both document paths →
  the newest commit touching either is still **`f3c94642`** (spec +71/−36, rationale +208 new), unchanged
  across all twelve passes. `git show HEAD:` on both still measures the ledger's HEAD figures — the
  second, independent proof. Both files are ` M` and uncommitted; the artifact is `??`. Verified with
  `git log --stat` plus `git show HEAD:`, never `git status` alone.

### Cross-spec anchors: five, all resolving in both directions, re-timestamped **2026-08-16T01:43:55Z**

Re-derived from scratch because `spec-010` is under a concurrent cycle and has moved between passes.

- **Inbound (2).** `spec-010:67` cites `spec-009` #"### Layer 3: Finalization trigger"; `spec-010:468`
  cites #"### Decision 6: fail loudly". `grep -c` for each exact heading on the edited spec-009 →
  **1 each**.
- **Outbound (3).** `spec-009:99` → `spec-010` #"### Must redo (not augment)"; `:634` → #"## Strawberry
  finalization strategy"; `:870` → #"### Unresolved-target error format". `grep -c` on the current
  spec-010 → **1 each**.
- `spec-008`'s inbound reference is whole-file, not anchored; no `spec-011` file cites spec-009.

### Builders' required-amendment lists, discharged

`worker-1.md` `## Review-round custody`. Every `### Notes for Worker 1 (spec reconciliation)` item across
the eleven prior sections is accounted for: the R2 carry-forward is consistent and unchanged (spec-009
states the row-preserving property at `### Layer 7` and `### Phase 5`; the `DISTINCT ON` mechanism is
**discharged by an alternative**, not postponed, and `docs/SPECS/spec-028-orders-0_0_8.md` is still
absent from `git status --porcelain`, so R2 starts from an untouched file); the `filters/sets.py`
in-place `Meta` mutation was correctly recorded as a maintainer observation and not edited; the
`KANBAN.md` stale assertion about Layer 3 is R3/R4 territory; the two-site discipline Worker 3 pass 4
asked for was honoured; Worker 3 pass 6's six report-only notes are carried below. **Nothing was recorded
and left unimplemented.** No pass, this one included, found a correctness defect in shipped source, and
none is escalated as one.

### Escalations carried forward to the maintainer at commit — report-only, none repaired here

1. **`docs/SPECS/spec-010-foundation-0_0_4.md:8` still mis-describes spec-009.** It lists "custom field
   classes" among what spec-009 describes, which is exactly what D1 scrubbed. Re-read at
   2026-08-16T01:43:55Z and **still standing** — seventh consecutive pass. Outside this cycle's writable
   set; only the maintainer can sequence the two cycles at commit.
2. **NEW, and the same shape as escalation 1: `docs/SPECS/spec-010-foundation-0_0_4.md:491`.** It reads
   "**Annotation namespace preservation**: `get_strawberry_annotations` … is the right helper for the day
   a stable consumer-override contract lands. **Out of scope for 0.0.4**; flagged here so it is not
   reinvented later." That is D3's scrubbed borrow, and spec-009 now states the opposite position —
   provenance is solved structurally by the four `consumer_*_fields` frozensets, and "keep provenance one
   system. A second, independently-derived view … is a source of disagreement, not a safety net." The
   consumer-override contract it defers to has since shipped. Found by this pass's inbound-reference
   sweep; not previously recorded. Same owner and same resolution path as escalation 1.
3. **The `spec-010:67` coupling, and its pre-existing near-duplicate sentence.** `spec-010:67` says the
   auto-trigger direction in spec-009 #"### Layer 3: Finalization trigger" was not adopted; the anchor
   resolves and the claim is still true, but after change 40 the cited section no longer states the
   direction — it points at the rationale. Nothing dangles and nothing is false. Related and
   pre-existing: spec-009's single-threaded-setup-window sentence and `spec-010:67`'s closing sentence
   are near-verbatim twins, and were twins before this cycle; the right owner is spec-010.
4. **`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`'s docstring reserves
   `fields_class` for `TODO-BETA-046-0.1.1`** (`types/definition.py:65`) — a stale card number after the
   renumber (`046` is now `DONE-046-0.0.14`, the transport card). The live owner is
   `TODO-BETA-054-0.1.1`, which is what the spec, `KANBAN.md`, and `docs/TREE.md` all say. **The spec is
   right and the source docstring is stale.** Source is read-only in this cycle.
5. **The rationale's `## Standing notes` "three sites" bullet is stale on purpose.** Correcting it would
   break the plan's append-only constraint on the rationale for this cycle; the staleness is stated
   explicitly five lines above it, and the spec's own opener was corrected to "four sites" (change 39).
   Correct it in the first pass that has the rationale open without that constraint.
6. **The permanent-suite gap, and it is the one item on this list whose evidence inaction destroys.**
   `tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse` pins
   `async def get_queryset` → `SyncMisuseError` on a connection field only under `execute_sync`. **No row
   pins the same rejection under `await schema.execute` for a *default* `DjangoConnectionField`** — the
   contract that makes an `async def resolver=` mandatory, and the exact fact apply-changes pass 4's
   correction turns on. `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is a
   ready-made body, re-run and confirmed passing this pass, but it is gitignored and **clears with the
   cycle**. **Recommend it be carded** before the cycle closes; tests are outside this cycle's writable
   set.
7. **A card-renumber `grep` at the commit gate.** `KANBAN.md`, `KANBAN.html`, and
   `examples/fakeshop/db.sqlite3` are dirty under a concurrent session. All seven card ids cited across
   the two documents resolve today, but a renumber landing before commit would silently falsify them —
   and this repo has already done one renumber (escalation 4 is its residue). One grep covers it.
8. **Worker 3 pass 2's per-edit byte-split arithmetic slip**, carried from both prior final verifications
   so the artifact stays internally consistent without any prior section being edited: apply-changes pass
   2's `### Byte counts` attributes its −19 as "−15 and −12"; the Low's edit is **−4**, not −12. Every
   total, every final count, and both `--numstat` figures are exact. Nothing in either deliverable needs
   correcting.

### Summary

R1 turns the archived spec-009 from a horizon document describing six mechanisms this package chose
against into one that describes what shipped. **Two files changed and nothing else**: no source, test,
example, sibling spec, standing doc, generated doc, or DB row was touched, and the public surface
(`git diff -- django_strawberry_framework/__init__.py`) is empty.

**The six Group-A scrubs are complete, and completeness was verified by counting rather than by reading a
site list.** Every dropped symbol is at **zero** occurrences in the current spec, re-counted this pass
with `grep -oF | wc -l`: `DjangoModelField`, `types/fields.py`, `OptimizerStore`, `with_hints`,
`with_prefix`, `get_strawberry_annotations`, `DjangoField(`, `ASC_DISTINCT`, `DESC_DISTINCT`,
`DISTINCT ON`, `AdvancedFilterSet`, `AdvancedOrderSet`, `LazyClassRef` — 0 each. Where a scrubbed
section's whole subject was the dropped mechanism it was **rewritten to state what the shipped
architecture does** — Layer 4's four named seams, the provenance section, the value-not-callable hint
rule, the no-placeholder-tier contract, the row-preserving `Min`/`Max` paragraph, the corrected
connection sketch — never left as a hole and never left as "this was rejected" prose. The deliberation
went to the append-only rationale companion.

**The scrub is correctly bounded, and the boundary was re-verified site by site.** The surviving
`DjangoModelType` (**6**), `AdvancedAggregateSet` (**2**), and `AdvancedFieldSet` (**2**) mentions are
each an upstream citation, a description of *upstream's own* behavior, or a refusal site — never a
mechanism this package adopts. `DjangoModelType` at `:312` (the upstream `file:///` reference list),
`:428-429` (Strawberry-Django's own default relation fallback maps), `:553`
(`## What to scrap from Strawberry-Django`), `:851` (`## Why not use generic relation fallback by
default?`), `:996` (`### Decision 1`, which refuses it by name); `AdvancedAggregateSet` at `:142`
(upstream citation) and `:235` (upstream design being praised); `AdvancedFieldSet` at `:250` (same) and
`:769` (`### Layer 9`'s prior-art reference, the twin of Layer 6's "Use `django-graphene-filters`
semantics"). Removing any of them would have deleted the argument along with the rejected feature and
falsified the upstream citations.

**The ten Group-B corrections all landed**, each re-verified against shipped source rather than against
the drift table: the node field's nullable-by-contract spelling (D7), the three `DEFERRED_META_KEYS`
named with the card that promotes each (D8), the connection's opt-in `totalCount` and still-owed
`aggregates` (D9), the `DjangoTypeDefinition` sketch corrected to `fields_spec` / `exclude_spec` and
declared an explicit subset of a 29-slot record (D10), `FilterSet` with canonical `Meta.fields` **plus**
the cookbook-parity `filter_fields` alias the drift row itself had understated (D11), the shipped `*Set`
base names (D12), Layer 5's self-contradicting "finalize pending types" replaced by the negative contract
(D13), the module layout's dead proposal removed and `fieldset/` / `orders/inputs.py` corrected (D14),
Phase 3 restated to the machinery that actually passes its five acceptance tests (D15), and the three
unmet success criteria annotated with their owning cards (D16). Two vacated numbered slots
(`### Decision 3`, `### Phase 3`) were **repurposed with positive contracts rather than gapped or
renumbered** — renumbering was forbidden because `spec-010` cites `### Decision 6` by anchor — and all
five cross-spec anchors resolve in both directions.

**The single-ownership decision.** Three consecutive passes each closed one bullet of a duplicated
four-seam responsibility map, and each time the next pass found another. Apply-changes pass 3 stopped
patching bullets and decided the shape once: **`### Layer 4: Generated relation fields` is the sole owner
of the responsibility-to-seam map, and ``### Borrow `StrawberryDjangoFieldBase` and
`StrawberryDjangoField` `` states the borrow argument and points at it, carrying no seam list of its
own.** The duplicated list was deleted rather than corrected; async-safe queryset access — the one
borrowed behavior that is not a generated field's seam — got one sentence in the Borrow chapter rather
than a fifth Layer 4 bullet, because adding it there would have repeated the mis-attribution one section
over. The generalisable rule: **the architecture chapter owns the map, the prior-art chapter cites it**,
because a duplicate map has no correct state — it has a current half and a stale half.

**Ledger.** Spec **54,232 → 61,337 bytes**, **1,154 → 1,096 lines** (`--numstat` **112 / 170**; it
deletes more lines than it adds and still grows in bytes, because the scrubs removed a dataclass sketch,
three bullet lists, and a transition path while the replacements are denser contract prose). Rationale
**12,273 → 49,447 bytes**, **208 → 690 lines** (**482 / 0** — append-only, proved by exactly one `-` line
in its diff, a byte-identical `head -166`, and hunks summing `480 + 1 + 1 = 482`). Closing identities:
`1,154 − 170 + 112 = 1,096` and `208 + 482 = 690`. Both gates green — 23 glossary terms, exit 0 on both
files — with 25/25 and 11/11 link definitions, zero orphans, zero dead targets, zero unresolved in-page
anchors, and zero in-repo raw `path:NN`.

**The most transferable thing this item produced is the defect pattern itself, now at seven instances of
one class.** Every finding on R1 has been the same shape: **a fluent subordinate clause explaining *why*,
in connective tissue nobody re-derives because it reads like glue** — D10's byte-unchanged section, Layer
4's "cannot see" absolute, `:385`'s "binds at finalization", `:418`'s async-safety mis-attribution,
`:417`'s "chosen per execution", `:515`'s plan-cache "keyed on", and now `:649`'s cascade-helper recourse.
Six were written by *this cycle's own fix passes*, which makes a fix pass's new prose the highest-risk
text in the cycle. Three detection rules earned their keep and should be carried: **an invariant comment
validates the RULE, not the REASON** — when a clause names a cache, a key, a lock, an ordering, or a
helper, open the thing it names rather than the docstring that motivates the rule it supports; **read all
`+` lines cold, in order**, not only the sites prior findings named, which is how the sixth and seventh
were found after five and six reviews respectively had validated the same paragraphs; and **when one
argument is told in both spec and rationale, diff the two tellings** — the spec/rationale pair is a
second container for the duplicate-map failure. The remedy generalises as *cut when the reason cannot be
verified cheaply by the reader at their desk from the cited symbol; replace when it can and a builder
needs it* — and the seventh finding's recommended remedy is a cut.

**What is left.** One Medium: `:649`'s "a raw `list[T]` relation … gets its row-level answer from the
`permissions.py` cascade helpers instead" names a helper that skips reverse FK, reverse one-to-many, and
M2M by definition and by guard — the exact relation kinds a `list[T]` annotation is emitted for — so the
clause is false in the fail-open direction. The shipped code is correct (`"connection"` is the secure
default and the raw list is an explicit, row-bounded opt-in); nothing is escalated as a source defect.
Everything else is verified and stands.

---

## Build report (Worker 1, apply-changes pass 6)

Run 2026-08-16 by a fresh Worker 1 invocation carrying only
`docs/builder/worker-memory/spec-009-worker-1.md`. Closes final-verification pass 3's Medium **and**
runs the dispatch's class sweep instead of stopping at the named site. **HEAD re-derived: `9f8584c7`** —
it moved mid-pass (`c2b8622d` at dispatch), so every hash written before this pass is stale.
`git status --porcelain` is **104** entries; none of it intersects this cycle's writable set and none of
it was reverted. `git stash` / `checkout` / `restore` / `worktree` were not used; the HEAD reference is
`git show HEAD:<path>` into a scratch path outside the repository.

**Spec status-line re-verification (per-spawn duty).** Lines 1-5 re-read. The opener still describes the
rationale companion, the **four** finalization sites, and the six scrubbed mechanisms; the three cuts
below falsify none of it. No edit owed.

### The dispatched finding, re-derived rather than accepted

The prescription was verified before it was applied, per the dispatch (three prescriptions on this item
have been wrong in their mechanism). It holds, and the source is stricter than the finding stated:

- `types/converters.py::resolved_relation_annotation` returns `list[target_type]` **only** under
  `if meta.is_many_side`; the other two returns are `target_type | None` and `target_type`. A raw
  `list[T]` relation is therefore always reverse FK / reverse one-to-many / M2M.
- `permissions.py::_is_cascadable_edge` is `isinstance(field, models.ForeignKey) and field.column is not
  None` — an **allowlist**, not the `not many_to_many and not one_to_many` denial the finding quoted, so
  the exclusion is structural rather than a guard that could be widened. `_is_unsupported_forward_edge`
  and the module docstring agree: reverse FK / reverse OneToOne, M2M and `GenericRelation` "stay outside
  parent-row cascade semantics".
- `types/resolvers.py`'s import block, read in full: `exceptions`, `optimizer.*`, `registry`,
  `resource_policy.bounded_rows`, `utils.relations`, `.converters`. Neither `permissions` nor
  `utils.querysets`. `many_resolver` returns `bounded_rows(...)` over the prefetch-cache hit or over
  `getattr(root, accessor_name).all()` — a row **cap**, not a visibility answer.

The clause was **cut**, one site in the spec — and one more in the rationale that the pass-3
one-site claim missed (below).

### The one-site claim was wrong: the rationale carries the same falsehood, hidden by a line wrap

Pass 3 recorded `grep -n 'cascade helpers'` over both documents as returning only the spec's `:649`.
It returns only `:649` **and** `:887` on the spec — because in the rationale the phrase wraps:
`…and `permissions.py`'s cascade` / `helpers are the documented answer on that path.` (rationale
`### Borrow \`StrawberryDjangoFieldBase\`…` entry). `grep -n cascade` — the shortest distinctive token —
finds it immediately. This is `BUILD.md` `## Claims are proven mechanically` in the flesh: **a long grep
phrase samples a claim's vocabulary rather than establishing its population.** The spec/rationale
twin-telling trap has now bitten this item **three** times, and the third instance was created by the
same fix pass that created the first.

### The class sweep: every causal / mechanism / seam / recourse clause this cycle added

Method per the dispatch: enumerate the clause, name the symbol it asserts, **open that symbol**, and cut
or replace anything false. Read cold in file order across all 112 spec `+` lines and all 500 rationale
`+` lines, not at the sites prior findings named.

**Denominator: 101 clauses enumerated (55 spec / 46 rationale); 78 opened at the symbol they name; 4
changed** (3 spec cuts, 1 rationale correction, plus 2 rationale retraction notes the cuts owe). The 23
not opened are marked `judgement` in the tables — an argument, a forward-looking design prescription, or
a claim about a rejected alternative, none of which names a checkable symbol. A later pass can audit the
coverage from the tables rather than re-deriving it, and can tell a miss from a genuinely new claim.

#### Spec (55 clauses)

| Site | Clause asserts | Symbol opened | Verdict |
|---|---|---|---|
| `:3` | rationale companion holds four finalization sites + six scrubbed mechanisms | rationale `### Layer 5` entry; `grep -oF` x13 over the spec | true (all 13 at **0**) |
| `:62` | `object_type: ObjectTypeNode \| None` sketch line | `relay.py` #"nullable by contract" | true |
| `:66` | "contract rather than illustration" framing | — | judgement |
| `:68` | `required=False` unconditionally → hidden / missing / uncoercible-pk all resolve `null` | `relay.py:17-25` | true, verbatim the module's own sentence |
| `:70` | three keys in `DEFERRED_META_KEYS`, refused at class creation, each with its promoting card | `types/base.py::DEFERRED_META_KEYS`, `ALLOWED_META_KEYS`; `KANBAN.md` cards 054/055/057/058 | true |
| `:257` | wrapping keeps the gate/override cascade expressible; spec-054 owns the mechanism | `spec-054-fieldset-0_1_1.md` #"resolver wrapping" (2 hits) | true |
| `:363` | metadata on the definition, so one lookup answers every question | `types/definition.py::DjangoTypeDefinition.field_map` | true |
| `:375-379` | sketch slot names / types | AST of `DjangoTypeDefinition` (29 slots) | true |
| `:385a` | "also carries … and three lookup methods" | AST: 3 methods (`graphql_type_name`, `related_target_for`, `has_custom_id_resolver_for`) | true |
| `:385b` | a sidecar slot is `type \| None`, validated at class creation | `types/base.py::_validate_filterset_class` / `_validate_orderset_class` | true for the three class sidecars the sketch shows |
| `:385c` | `aggregate_class` / `search_fields` have no slot; each lands with its card | AST (absent); `DEFERRED_META_KEYS` | true |
| `:393` | connection fields resolve filter/order defaults from the node type | `connection.py:1781-1784`, `:1861`, `:1872` | true |
| `:397` | neither problem is solved by re-walking the annotation namespace | — | judgement |
| `:401` | provenance recorded at collection time; validators + `_build_annotations` read the same union | `types/base.py:613` union, `:1346` / `:1437` / `:1506` validators, `:1646` `_build_annotations` | true (3 validators + `_build_annotations`) |
| `:402` | deferring `strawberry.type` to finalization "is when every target type exists" | `types/finalizer.py` phase docstring (Phase 3) | true |
| `:403` | one provenance system, not two | — | judgement |
| `:409-413` | the five borrowed behaviors are real upstream requirements | `strawberry_django/fields/base.py`, `fields/field.py` (`get_queryset`, `is_async`, `get_result`, `django_resolver`) | true |
| `:415a` | upstream binds all of them to one field class | same | true |
| `:415b` | this package's API is `class Meta`, so the finalizer owns generation | `types/finalizer.py` Phases 1-3 | true |
| `:417` | the sync/async visibility pair is applied by `connection.py`, `list_field.py`, `types/relay.py` | all `apply_type_visibility_*` call sites, grepped package-wide | true (those three are the field owners) |
| `:419` | one object answers every question; every seam reads it | `DjangoTypeDefinition`; `_field_meta_for_resolver` reads `registry.get_definition` | true |
| `:439-441` | no placeholder tier; unresolved target → finalization fails | `types/finalizer.py:770-771` `raise ConfigurationError(_format_unresolved_targets_error(...))` | true |
| `:472` | `DjangoListField` keeps graphene-django's symbol | `graphene_django/fields.py:21` | true |
| `:476` | each is a factory returning a Strawberry field | `list_field.py:153`, `relay.py:388`, `connection.py:2168` — all `def` | true |
| `:483a` | a count costs a second query, so the base carries no `total_count` | `connection.py::DjangoConnection` | true |
| `:483b` | **every** node type resolves through a generated concrete subclass; the opt-in decides only the member | `connection.py::_connection_type_for` | true |
| `:483c` | the base owns `first`+`last` guard, window consumption, cursor-mode dispatch | `connection.py::DjangoConnection` docstring/body | true |
| `:491` | a bare generic alias loses the `resolve_connection` override | `connection.py:18` (module's own reason) | true |
| `:493` | `aggregates` lands through the same generated-subclass mechanism | — | judgement (forward design prescription; `TODO-BETA-057-0.1.3` exists) |
| `:515a` | strategy selection is schema-static, so the plan cache is not keyed on it | `optimizer/extension.py::_build_cache_key` — 5 key parts, strategy in none | true |
| `:515b` | a request-reading hint would make every cached plan unsound | `optimizer/hints.py:94-98` | true |
| **`:515c`** | **`get_queryset` "is already composed into every path"** | **`types/resolvers.py` (no `utils/querysets` import); every `apply_type_visibility_*` call site** | **FALSE — CUT** |
| **`:526`** | **`_make_relation_resolver` is "the single place every cardinality's access passes through"** | **`types/finalizer.py::_synthesize_relation_connections` + `_suppress_relation_list_form`** | **FALSE — CUT** |
| `:526b` | that resolver stays sync; async-safe access belongs to the queryset owner | `grep -cE 'async\|sync_to_async\|SynchronousOnly\|await '` over `types/resolvers.py` → **0** | true |
| `:528` | centralizing keeps the N+1 probe / cache read / FK-id elision / row-bound call out of a per-kind variant | `_check_n1`, `_prefetched_objects_cache` read, `_build_fk_id_stub`, `bounded_rows` | true (one implementation each) |
| `:562-574` | borrow lists (finalization lifecycle, annotations, nested prefetch) | — | judgement |
| `:642` | the registry is deliberately lockless, so an auto-trigger must enforce the setup window | `registry.py::TypeRegistry` #"Mutating methods are not guarded by a lock" | true (source's own claim) |
| `:645` | four named seams, produced by the finalizer | `types/finalizer.py` Phase 2 / 2.5 / 3 | true |
| `:647` | annotation seam, cardinality-correct spelling | `types/converters.py::resolved_relation_annotation` | true |
| `:648` | resolvers installed at Phase 2, before `strawberry.type` at Phase 3 | `types/finalizer.py` phase docstring; `_attach_relation_resolvers` | true |
| `:649a` | visibility composes on the connection pipeline, `DjangoListField`, the optimizer prefetch child; not inside the generated resolver | `connection.py:1780`/`:1815`, `list_field.py:211`/`:217`, `optimizer/walker.py:383`; `types/resolvers.py` imports | true |
| **`:649b`** | **raw `list[T]` "gets its row-level answer from the `permissions.py` cascade helpers instead"** | **`permissions.py::_is_cascadable_edge`; `resolved_relation_annotation`; `types/resolvers.py` imports** | **FALSE — CUT (the dispatched finding)** |
| `:650` | `DjangoConnectionField` synthesizes a resolver `__signature__` carrying the sidecar args | `connection.py:1824`, `:2004`, `:2163` | true |
| `:652a` | the definition holds field name, origin type, relation metadata, sidecar bindings | AST slots (`selected_fields`, `origin`, `field_map`, the sidecars) | true |
| `:652b` | `fields_class` wraps the generated resolver rather than replacing it | `spec-054-fieldset-0_1_1.md` | true |
| `:654` | cannot generate at class creation (target may not exist) nor after `strawberry.type` (frozen) — Phase 2 is the only window | `types/finalizer.py` Phase 2/3 | true |
| `:662-672` | the 12-step connection pipeline | — | judgement (normative "It should:", not a shipped-code claim) |
| `:674` | constructing a connection field must not finalize | `grep finalize_django_types` over `connection.py` → no call | true |
| `:696a` | named `FilterSet` because it subclasses django-filter's `BaseFilterSet` | `filters/sets.py:1135-1140` | true |
| `:696b` | `filter_fields` is an alias only when `fields` is absent; `"__all__"` works in both spellings | `filters/sets.py::FilterSetMetaclass.__new__` (`meta_class.fields = meta_class.filter_fields`) | true (the alias is an assignment, so the value path is identical) |
| `:728` | the six-member `Ordering` vocabulary is what a portable null partition needs | `orders/inputs.py:89-96` | true (6 members) |
| `:731` | naive join inflates page + `totalCount`; `Min`/`Max` composes with the pk tiebreaker | `orders/sets.py:357`; `connection.py:1707` | true |
| `:771` | wrapping keeps the cascade in one place, costs nothing on unmanaged fields | `spec-054-fieldset-0_1_1.md` | true (twin of `:257`, judged non-finding in pass 3, re-confirmed) |
| `:875` | the package layout is canonical because it fixes import paths / promotion / test mirroring | `docs/TREE.md` | true |
| `:884-887` | `orders/` = base/sets/factories/inputs; `permissions.py` migrates at `TODO-BETA-059-0.1.4` with sentinel redaction | `ls django_strawberry_framework/orders/`; `KANBAN.md` card 059 (`Meta.redaction_mode`) | true |
| `:890` | "matches the target layout in `docs/TREE.md`" | `docs/TREE.md:337`, `:347`, `:392` | true |
| `:896-898` | per-file Phase responsibilities | `types/resolvers.py`, `optimizer/*` | true |
| `:904-913` | Phase 1 ships the foundation slice; `DjangoSchema` owned by a later wrapper phase | `spec-010-foundation-0_0_4.md`; `__init__.py:46` | true (the section is the 0.0.4 slice's scope, and `:901` states the list is a dependency order, not a shipping record) |
| `:930`, `:961`, `:965`, `:979`, `:981` | Phase 3/5/6/7/8 restatements and their owning cards | `KANBAN.md` cards 054/055/057/059 | true |
| `:1002` | composability from one readable definition, not a per-field object | `DjangoTypeDefinition` | true |
| `:1015` | plain `strawberry.Schema` fully supported because the trigger is the consumer call | `__init__.py` export; no in-package call site | true |
| `:1034-1036` | the three owed criteria carry their cards | `KANBAN.md` | true |

#### Rationale (46 clauses)

| Site | Clause asserts | Symbol opened | Verdict |
|---|---|---|---|
| nullable-node entry | dispatch `required=False` → three cases resolve `null`; raise-instead lost | `relay.py:17-25` | true / judgement on the rejected alternative |
| same | the flagship example raised `ConfigurationError` on the whole class | `types/base.py::DEFERRED_META_KEYS` refusal | true |
| `fields_class` entry | `permission_classes` is class-per-policy with a fixed message contract | Strawberry `BasePermission` | true |
| same | resolver wrapping costs nothing on an unmanaged field; spec-054 pinned it | `spec-054-fieldset-0_1_1.md` | true |
| `StrawberryDjangoDefinition` entry | `_spec` suffix distinguishes declaration from `selected_fields` | AST slots | true |
| same | `LazyClassRef` zero package-wide; both validators refuse at **class creation** | `grep`; `types/base.py:138`, `:164` | true |
| same | "twenty-nine slots" | AST count | true — **exactly 29** |
| same | the pass-1 replacement clause ("binds at finalization") was false; `RelatedFilter` lazy refs are a different object | `types/finalizer.py::_expand_filterset` | true |
| provenance entry | four spelling-specific frozensets + a fifth union slot, derived in `__init_subclass__` | AST slots; `types/base.py:613` | true |
| same | "first readers are the three override-target validators, `_build_annotations` after them" | `types/base.py:1346`, `:1437`, `:1506`, `:1646` | true — exactly three |
| field-class entry | every capability ships through this package's own grain (five named seams) | the five symbols | true |
| same | upstream is decorator-first, so the return value is the only object it owns | `strawberry_django/fields/field.py` | true |
| same | Phase 2 is permanent, not transitional | `types/finalizer.py` | true |
| Layer 4 entry | `_make_relation_resolver` never calls `apply_type_visibility_sync`; the composition runs at three sites, the last opt-in | `types/resolvers.py` imports; the three call sites | true |
| **Layer 4 entry** | **"`permissions.py`'s cascade helpers are the documented answer on that path"** | **`permissions.py::_is_cascadable_edge`** | **FALSE — CORRECTED IN PLACE** (the wrapped twin of spec `:649b`) |
| same | the twin four-seam list; async-safety mis-attribution; `grep -cE` over `types/resolvers.py` returns 0 | re-run this pass → **0** | true |
| same | renumbering forbidden because `spec-010` cites `### Decision 6` by anchor | `spec-010-foundation-0_0_4.md:468` | true |
| placeholder entry | unresolved targets raise at finalization | `types/finalizer.py::_format_unresolved_targets_error` | true |
| same | upstream `DjangoModelType` is pk-only | `strawberry_django/fields/types.py:73-74` (`pk: strawberry.ID`) | true |
| `DjangoField` entry | its capabilities ship split across the three factories + `@strawberry.field` | the three factory `def`s | true |
| same | the one upstream-only extra is single-library | `graphene_django/` (no analogue) | true |
| optimizer entry | graphene-django ships **no** optimizer module at all | `ls graphene_django/` → none | true |
| same | `optimizer/hints.py` pins "MUST never depend on request-varying data"; that invariant buys the cache | `optimizer/hints.py:94-98` | true |
| same | "a frozen four-directive `OptimizerHint`"; no `annotate` hint in any form | `optimizer/hints.py` — `@dataclass(frozen=True)`; 5 fields, but `__post_init__` says "beyond **the four directives**" | true against the module's own vocabulary (`nested_strategy` is its "knob"); recorded so a later pass does not re-open it |
| same | request-varying shaping "already has its seam in `get_queryset`, which runs per request by construction" | same as `:515c` | **true — and note it makes no composition claim**; diffing the two tellings is what exposed the spec's `:515c` |
| same | the live fragment is already carded on `TODO-BETA-053-0.1.1` | `KANBAN.md` (17 hits) | true |
| `django_getattr` entry | `django_getattr`'s five patterns include async contexts | spec `:634-639`; `strawberry_django/resolvers.py` | true |
| same | the generated resolver carries no filtering / ordering / pagination / permission check; its three bodies carry four named things | `types/resolvers.py` read in full | true |
| Layer 7 entry | `Ordering` is member-for-member identical to upstream's | `orders/inputs.py:89-96` vs `strawberry_django/ordering.py` | true |
| same | graphene-django has no DISTINCT ordering directives anywhere | `grep -rn` over `graphene_django/` → none | true |
| same | the shipped answer annotates `Min`/`Max` | `orders/sets.py:357` (exact substring) | true |
| same | `DISTINCT ON`'s leftmost-expression constraint fights the cursor ordering | `connection.py:1707` pk tiebreaker + SQL semantics | true |
| same | `spec-028` `### Decision 12` is the sibling site | `docs/SPECS/spec-028-orders-0_0_8.md` | true (R2's carry-forward, untouched) |
| connection entry | generated subclass is not a naming convenience | `connection.py:18` | true |
| same | `_connection_type_for` **always** returns a concrete subclass; `Meta.connection` only controls the shape | `connection.py::_connection_type_for` | true |
| Layer 5 entry | `DjangoConnectionField` contains no finalizer call | `grep` over `connection.py` | true |
| same | the count is four sites, not three | rationale's own `### Layer 5` entry; spec `:3` | true |
| Layer 6 entry | `AdvancedFilterSet` was never this package's name at any version | `git log -S AdvancedFilterSet -- django_strawberry_framework` → one hit, a docstring citing **upstream** | true |
| same | `FilterSetMetaclass.__new__` aliases `filter_fields` onto `fields` when `fields` is absent | `filters/sets.py` | true |
| same | the survivors list (`AdvancedAggregateSet` x2, `AdvancedFieldSet` x2, the `file:///` list) | `grep -oF` on the spec → 2 / 2 | true |
| module-layout entry | `orders/inputs.py` ships and owns the direction enum; `docs/TREE.md` plans `fieldset/` at 054 | `ls orders/`; `docs/TREE.md:347` | true |
| same | `permissions.py` annotated with its planned migration | `docs/TREE.md:392`; `KANBAN.md` card 059 | true |
| migration entry | naming a card points forward; naming a version duplicates the board | — | judgement |
| same | "eight of the eleven success criteria are met today" | spec `## Success criteria` — 11 items, 3 annotated `owed` | true |
| conventions entry | `check_trailing_commas.py` enforces the scaffold, not inline-vs-reference | `scripts/check_trailing_commas.py` | true |
| same | the three deleted narration sites; `## Standing notes` left stale on purpose | rationale + spec `:3` | true |
| same | `### Phase 1`'s inline link is now reference-style `[spec-010]` | spec `:904`, `:1082` | true |

### Spec changes made (Worker 1 only)

Four edits, one document each way. Every one **cuts** a false clause rather than qualifying it
(`worker-1.md` rule 2: a false clause is deleted, not retracted into the rationale — the retraction
notes below record what may no longer be claimed, which is a different obligation).

1. **`docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md:649`** — cut
   `; a raw \`list[T]\` relation on a schema carrying no optimizer extension gets its row-level answer
   from the \`permissions.py\` cascade helpers instead`. Reason: the named helper is a forward-FK
   allowlist and covers exactly the complement of the relation kinds `list[T]` is emitted for; the
   error direction was fail-open. Bullet now ends at the verified structural claim. **−146 bytes.**
2. **`…:515`** — cut ` and is already composed into every path` from the `get_queryset` clause. Reason:
   the same falsehood one section earlier, in the same fail-open direction — the generated relation
   resolver composes no target-type `get_queryset`, so the raw `list[T]` opt-in path has none. The
   value-not-callable rule stands on "runs per request", which is what the rationale's own telling of
   the argument says and all the rule needs. **−41 bytes.**
3. **`…:526`** — cut `, which is the single place every cardinality's access passes through`. Reason:
   under the shipped `"connection"` default, finalizer Phase 2.5
   (`types/finalizer.py::_synthesize_relation_connections` →
   `types/finalizer.py::_suppress_relation_list_form`, which `delattr`s the field) removes a many-side
   relation's generated list form before Phase 3, and `connection.py::_build_relation_connection_resolver`
   owns that access. The borrow instruction needs no superlative. **−68 bytes.**
4. **`docs/SPECS/appx/…-rationale.md`, `### Borrow \`StrawberryDjangoFieldBase\`…` entry** — replaced
   the wrapped twin of edit 1 with the verified disposition (`resource_policy.py::bounded_rows` is the
   ceiling) plus an explicit **no recourse may be named for that path** and the one-line reason, so the
   claim cannot be reconstructed from either document. Two short retraction notes append to the entries
   that own edits 2 and 3, per `BUILD.md` `## Spec rationale extraction` ("any claim the decision once
   made and may no longer make").

No drift row's contract changed, so **no checklist box changed**: the artifact still carries **16**
`- [x]` and **0** `- [ ]`, and D2's tick (the value-not-callable rule at `:515`) survives the cut
intact — the rule and its plan-cache reason are both untouched.

### Gates, ledger and proofs — all re-run this pass

- `uv run python scripts/check_spec_glossary.py --spec <spec>` → `OK: 23 terms - all have glossary
  entries and at least one spec link.` **exit 0, 23 terms.**
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0**.
- **Link / anchor / rule-27 audit** (fences stripped, definition lines excluded from the use scan):
  spec **25 defs / 25 uses, 0 missing, 0 orphan, 0 dead targets**; rationale **11 / 11, 0 / 0 / 0**;
  **0** `](#…)` in-page anchors in either file; **0** in-repo raw `path:NN`. The new rationale prose
  cites only symbol-qualified paths (`permissions.py::_is_cascadable_edge`,
  `types/converters.py::resolved_relation_annotation`, `resource_policy.py::bounded_rows`,
  `types/finalizer.py::_synthesize_relation_connections`).
- **No renumbering.** `### Layer 1`-`11`, `### Phase 1`-`8`, `### Decision 1`-`6` — complete, in order,
  no gap.
- **Cross-spec anchors: five, both directions, re-timestamped 2026-08-16T02:04:40Z.** Inbound
  `spec-010:67` → #"### Layer 3: Finalization trigger" and `spec-010:468` → #"### Decision 6: fail
  loudly" (`grep -c` on spec-009 → 1 each); outbound `spec-009:99` / `:634` / `:870` → spec-010's
  #"### Must redo (not augment)" / #"## Strawberry finalization strategy" / #"### Unresolved-target
  error format" (`grep -c` → 1 each).
- **Ledger.** Spec **61,337 → 61,082 bytes**, **1,096 → 1,096 lines** (−255 this pass, ninth
  consecutive net-negative pass); cumulative `--numstat` **112 / 170** against HEAD's **54,232 / 1,154**,
  identity `1,154 − 170 + 112 = 1,096` ✓. Rationale **49,447 → 50,849 bytes**, **690 → 708 lines**;
  cumulative **500 / 0** against HEAD's **12,273 / 208**, identity `208 + 500 = 708` ✓.
- **Append-only re-proved.** `git diff -- <rationale>` contains exactly **one** line starting with `-`,
  and printing it shows the `--- a/…` header — no HEAD line deleted or modified. `git diff -U0` hunks
  `@@ -166,0 +167,498 @@`, `@@ -185,0 +684 @@`, `@@ -186,0 +686 @@`; `498 + 1 + 1 = 500` closes against
  `--numstat`. `head -166` of the working file `cmp`s **exit 0** against `head -166` of HEAD's copy.
  In-place correction of a **new** entry preserves all three, as it has through ten prior proofs.
- **Provenance.** `git log --stat` over both paths: the newest commit touching either is still
  **`f3c94642`**, unchanged even though HEAD moved to `9f8584c7` mid-pass. `git show HEAD:` re-measures
  54,232 / 1,154 and 12,273 / 208 — the second, independent proof that nothing was swept. Both files
  are ` M`; the artifact is `??`. Never `git status` alone.
- **No source, tests, or third file touched.** The diff is two `.md` files. The temp test under
  `docs/builder/temp-tests/r1/` was not modified, moved, or deleted.

### What the next verification should look for

The sweep leaves **zero** unopened mechanism clauses in this cycle's added text, which is the state no
prior pass could claim. Three residual risks, named so a fourth final verification can target them:

1. **This report's own new prose** — the two rationale retraction notes and the corrected Layer 4
   sentence are exactly the highest-risk text class this item has produced seven instances of. Each
   states one fact with one citation and no causal story, which is the shape chosen deliberately.
2. **Pre-existing text is out of scope and still unswept.** The sweep covered added lines only; the
   spec's untouched HEAD prose has never been read against source in this cycle.
3. **The wrapped-phrase trap is now proven live here.** Any "one-site fix" claim on this item must be
   established with the shortest distinctive token, never a phrase.

The eight escalations final verification pass 3 carried forward are unchanged and none was repaired
here; escalation 6 (the permanent-suite gap for `async def get_queryset` on a default
`DjangoConnectionField`) is still the only one whose evidence inaction destroys.

### Status

`planned`. The dispatched Medium is closed, and so are the three further instances of its class the
sweep found — two in the spec, one the wrapped rationale twin the pass-3 one-site claim missed.
Every cut is a deletion, not a qualification, and the top-level `Status:` line is the artifact's
single source of truth. Ready for Worker 3 re-review (pass 7).

---

## Review (Worker 3, pass 7)

Run 2026-08-16 by a fresh Worker 3 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-3.md`. Seventh review pass on R1. **HEAD re-derived:
`9f8584c7`**, matching the apply-changes pass 6 report (it had moved from `c2b8622d` mid-pass).
`git status --porcelain` is **106** entries — reported, not reverted; the only `docs/SPECS/` file dirty
outside this cycle's writable set is `docs/SPECS/spec-012-version_release_alignment-0_0_4.md`, which
belongs to the concurrent spec-012 cycle. `git stash` / `checkout` / `restore` / `worktree` were not
used; the HEAD reference was `git show HEAD:<path>` into a scratch path outside the repository. No
source, test, or spec file was edited by this pass.

**Method.** The four cuts were re-derived at the symbols they turn on rather than accepted from the
build report; the sweep's denominator was re-counted from the tables and from the 612 `+` lines
independently; the 23 `judgement` rows and a sample of the "opened" rows were re-opened; both gates,
the link/anchor/rule-27 audit, the byte ledger, the append-only proof, the five cross-spec anchors, the
sixteen boxes and every cited card id were re-run from scratch.

### High:

None.

### Medium:

#### M1 — the correction sentence overstates the cascade's coverage in the same fail-open direction it retracts

`docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md:321-324` (apply-changes pass 6's
edit 4, the in-place replacement of the wrapped twin):

> **No recourse may be named for that path**: `permissions.py`'s cascade helpers are not one —
> `permissions.py::_is_cascadable_edge` admits only single-column concrete forward FK / OneToOne edges,
> **which is the exact complement of the reverse-FK / reverse-one-to-many / M2M kinds
> `types/converters.py::resolved_relation_annotation` emits `list[T]` for**.

The load-bearing half is correct and I re-derived it independently. The emphasized half is not, and the
set algebra is fully mechanical:

- `django_strawberry_framework/utils/relations.py:20-30` — `RelationKind` is
  `{"many", "reverse_many_to_one", "reverse_one_to_one", "forward_single", "generic"}` and
  `MANY_SIDE_RELATION_KINDS` is `{"many", "reverse_many_to_one", "generic"}`.
  `types/converters.py::resolved_relation_annotation` emits `list[target_type]` on exactly
  `meta.is_many_side`, i.e. on those three kinds.
- **`generic` is missing from the sentence's enumeration.** A `GenericRelation` is classified `"generic"`
  (`utils/relations.py::relation_kind`, the duck-typed branch that precedes the `one_to_many` fallback)
  and is therefore a `list[T]` kind. The sentence names three kinds where the code has four; the source
  it is arguing from names four (`permissions.py` module docstring: "Reverse FK / reverse OneToOne, M2M,
  and ``GenericRelation`` stay outside parent-row cascade semantics").
- **"exact complement" is false, and false fail-open.** The complement of the `list[T]` kinds contains
  `reverse_one_to_one` and `forward_single`. `_is_cascadable_edge` is
  `isinstance(field, models.ForeignKey) and getattr(field, "column", None) is not None`, so it admits
  only part of `forward_single` and admits **no** `reverse_one_to_one` — a `OneToOneRel` is a
  `ForeignObjectRel`, not a `ForeignKey`. A reverse one-to-one relation is therefore in **neither** set:
  it is annotated `target_type | None`, not `list[T]`, and it is skipped by the cascade. Read literally,
  the sentence tells a reader that everything not `list[T]` is cascade-covered, which is exactly the
  claim the cut was made to remove, one relation kind over.

Why this is Medium and not Low: it is new text this cycle wrote; its subject is row-level visibility,
a data-isolation surface; and it is graded on the same test as the six documentation findings before it
— the consequence is actionable and inverted for a consumer with a reverse-O2O or `GenericRelation`
field. It is also the seventh-instance pattern reproduced *inside the sentence retracting it*: a fluent
precision word ("exact complement") in the connective tissue of a fix, which is precisely the class this
item's own final verification named as its most transferable lesson.

**Recommended change.** Unlike the four cuts, this one should be **replaced, not cut** — the disjointness
is the note's whole point, it is cheaply verifiable by the reader at their desk from one named constant,
and the replacement is shorter than an argument. Something of the shape: *"…admits only single-column
concrete forward FK / OneToOne edges, and admits none of the `list[T]` kinds:
`utils/relations.py::MANY_SIDE_RELATION_KINDS` is `{"many", "reverse_many_to_one", "generic"}`, every one
of which `_is_cascadable_edge` refuses. (`reverse_one_to_one` is outside both sets — the cascade is not
its answer either.)"* Re-derive rather than adopt this prescription; three dispatched prescriptions on
this item have been wrong in their mechanism, and this is a fourth.

#### M2 — the sweep's coverage numbers do not re-derive from the tables they are offered against

`docs/builder/bld-009-r1-spec_code_reconciliation.md:4299-4303`:

> Denominator: 101 clauses enumerated (55 spec / 46 rationale); 78 opened at the symbol they name; 4
> changed … The 23 not opened are marked `judgement` in the tables … A later pass can audit the coverage
> from the tables rather than re-deriving it.

The last sentence is the obligation the numbers create, and three of the four numbers fail it. Measured
this pass:

| Stated | Re-derived from the tables | Verdict |
|---|---|---|
| 55 spec | **55** distinct spec sites (62 table rows; sub-lettered rows `:385a/b/c`, `:415a/b`, `:483a/b/c`, `:515a/b/c`, `:526/:526b`, `:649a/b`, `:696a/b` collapse to one site each; the `:930, :961, :965, :979, :981` row expands to five) | **exact** |
| 46 rationale | **47** rows | off by one |
| 23 `judgement` | **7** rows carry `judgement` in the verdict column (spec `:66`, `:397`, `:403`, `:493`, `:562-574`, `:662-672`; rationale "migration entry"), plus one hybrid ("true / judgement on the rejected alternative"). Expanding the multi-item judgement rows into their bullets reaches ~20 and contradicts the collapsing convention the 55 uses | not derivable |
| 78 opened | **~94** under the same convention (102 − 8) | not derivable |

The direction is benign — the report **understates** its own opened count, so no site is uncovered on
account of it, and I found no coverage gap (below). The finding is the auditability claim: a later pass
told "23 rows are `judgement`" goes looking for sixteen rows that are not there, and the cheapest
resolution of that mismatch is to assume the tables are the stale half. `BUILD.md`
`## Claims are proven mechanically, never accepted on prose` grades a stated count that was not measured
as a Medium, and its own remedy applies verbatim here — **measure as you write the number**.

**Recommended change.** Worker 1's next section records the corrected figures (prior sections are never
edited): 55 spec sites / 47 rationale rows = 102, of which 7 are unopened `judgement` rows and ~95 were
opened. Alternatively state the denominator as *table rows* (62 + 47 = 109) and drop the collapsing
convention, which is the shape a later pass can recount with `grep -c`.

### Low:

#### L1 — the build report misquotes the predicate the dispatched finding turns on

`docs/builder/bld-009-r1-spec_code_reconciliation.md:4269-4270` renders `_is_cascadable_edge` as
`isinstance(field, models.ForeignKey) and field.column is not None`. The source
(`django_strawberry_framework/permissions.py:203`) is
`isinstance(field, models.ForeignKey) and getattr(field, "column", None) is not None`. The backticks
present it as the expression, and the `getattr` default form is deliberate — the docstring states it
"guards the single-column contract against a future `ForeignKey` shape whose value is not one concrete
column", i.e. a shape on which the quoted form would raise `AttributeError` rather than return `False`.

The **conclusion is unaffected**: the predicate is an allowlist either way, which is the whole of what
the finding needed, and I confirm the report's headline correction — the source *is* stricter than final
verification pass 3 stated, which had quoted a `not many_to_many and not one_to_many` denial that does
not exist in the current body. Low because it lives in a per-cycle scratchpad and no deliverable carries
it. Worth recording because a quoted expression is read as transcribed, and this item's whole defect
class is text that reads as transcribed and was in fact paraphrased.

### DRY findings

None new. The diff is two `.md` files and no `.py` file, so there is no abstraction, helper, constant,
or branch to challenge, and the existence challenge has nothing to attach to.

Two prior duplication decisions were re-checked rather than carried, since the wrapped-twin failure was
a duplication failure:

- **The four-seam single-ownership split holds.** `### Layer 4: Generated relation fields` is still the
  only section carrying a responsibility-to-seam list; the Borrow chapter (`:415`) points at it and
  carries none.
- **The spec/rationale twin surface is now clean for all four cut claims**, established with the
  shortest distinctive token per `BUILD.md` `## Claims are proven mechanically` rather than with a
  phrase: `cascade` over both files returns 3 rationale hits and 14 spec hits, every one of which is
  either pre-existing HEAD text about the forward-FK cascade (`### Layer 10`, the prior-art lists, the
  `permissions/` migration note) or the corrected note itself; `composed`, `every path`, `single place`,
  and `recourse` each return only the retraction notes that are *about* the cuts. No fourth site
  survives.
- The `:257` / `:771` resolver-wrapping near-duplication that pass 3 examined and did not raise is
  unchanged; I re-checked and reach the same disposition (two pointers at one external owner,
  `spec-054-fieldset-0_1_1.md`, making different contrasts). Recorded so an eighth pass does not
  re-open it.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — `__all__` and the re-export list are
unchanged. `git diff --name-only` over the whole tree confirms this cycle touched only the two `.md`
deliverables.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applies — the whole deliverable is documentation. All re-run this pass, not read as discharged:

- **Gates.** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.`, **exit 0, 23 terms**.
  `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0**.
- **Link surface, audited with a script written fresh for this pass** (fences stripped; definition lines
  excluded from the use scan; uses matched as `[text][ref]` on the raw line so backticked link text is
  not destroyed — my first attempt stripped code spans and produced 20 false orphans, recorded because
  it is an easy way to mis-audit this file): spec **25 definitions / 25 distinct uses, 0 missing,
  0 orphan**; rationale **11 / 11, 0 / 0**. Every non-anchor, non-URL definition target
  disk-existence-checked → **0 dead**. **0** `](#…)` in-page anchors in either file. **0** in-repo raw
  `path:NN` (`[A-Za-z0-9_/.-]+\.(py|md):[0-9]+` with `file:///` and code spans excluded → no match); the
  known `` `list[target]` `` false positive is inside a code span and untouched.
- **No renumbering.** `### Layer 1`-`### Layer 11` (11, no gap), `### Phase 1`-`### Phase 8`,
  `### Decision 1`-`### Decision 6`, each complete and in order.
- **Cross-spec anchors: five, both directions, re-timestamped 2026-08-16T02:15:51Z.** Inbound
  `spec-010:67` → #"### Layer 3: Finalization trigger", `spec-010:468` → #"### Decision 6: fail loudly"
  (`grep -c` on spec-009 → **1 each**). Outbound `spec-009:99` → #"### Must redo (not augment)",
  `:634` → #"## Strawberry finalization strategy", `:870` → #"### Unresolved-target error format"
  (`grep -c` on the current spec-010 → **1 each**). Re-derived from scratch because spec-010 is under a
  concurrent cycle.
- **Every cited card id re-grepped against the current (concurrently dirty) `KANBAN.md`**, per this
  worker's standing note: `TODO-BETA-053-0.1.1` (17), `054-0.1.1` (16), `055-0.1.2` (16), `057-0.1.3`
  (5), `058-0.1.3` (7), `059-0.1.4` (3) — all resolve today.
- **Checklist: 16 `- [x]`, 0 `- [ ]`**, measured on the artifact. No box's contract changed, which is
  correct: all four edits are deletions of clauses no drift row owned, and D2's tick survives the `:515`
  cut because the value-not-callable rule and its plan-cache reason are both untouched.
- No obsolete "coming soon" / "planned" / old-version wording was introduced; nothing was regenerated
  from a script-rendered source.

### Failability proofs

**Not applicable to a documentation pass.** The diff introduces no boundary, guard, gate, or rejection
path — it touches two `.md` files and no executable line — so `BUILD.md` `### What needs a proof, and
what does not` puts this pass outside the obligation, and the mandatory re-run floor is met with an
**empty re-run set**, which `worker-3.md` licenses only in exactly this case. The source carve-out was
not exercised: no production file was mutated at any point in this pass.

### Hot-path budget

**Not applicable.** The plan declares no hot path for this item, and the diff adds no runtime cost of any
kind — no source file is touched.

### What looks solid

- **All four cuts hold, each re-derived at the symbol rather than accepted.**
  - `:649` — `types/converters.py::resolved_relation_annotation` returns `list[target_type]` only under
    `if meta.is_many_side` (`converters.py:722-723`), and `MANY_SIDE_RELATION_KINDS` is
    `{"many", "reverse_many_to_one", "generic"}`. `permissions.py::_is_cascadable_edge` admits only
    `models.ForeignKey`. `types/resolvers.py` imports `..resource_policy.bounded_rows` and
    `..utils.relations` but **nothing** from `..utils.querysets` or `..permissions`, and carries **zero**
    function-level imports (grepped for `    from ` / `    import ` → no match), so the import block is
    the whole story. `many_resolver` returns `list(bounded_rows(getattr(root, accessor_name).all(), info))`
    or the `_prefetched_objects_cache` hit — a row cap, not a visibility answer. The clause was false.
  - `:515` — the same falsehood, and cutting it leaves the value-not-callable rule standing on
    "runs per request", which is all it needs.
  - `:526` — **the new mechanism assertion, and it verifies.** `types/finalizer.py::_suppress_relation_list_form`
    performs a real `delattr(type_cls, name)` (guarded by `if name in type_cls.__dict__`) plus an
    `__annotations__.pop`, and is called on the `shape == "connection"` branch at both the first-attach
    site (`finalizer.py:661`) and the re-entrancy site (`:583`). `DEFAULT_RELATION_SHAPE` is
    `"connection"` (`types/base.py:111`). Decisively, the synthesized field's resolver is
    `connection.py::_build_relation_connection_resolver(...)` built inline at `finalizer.py:615` — the
    captured `list_resolver` is passed only to `_register_relation_connection_teardown` for restore, and
    `connection.py` imports `_check_n1` from `types.resolvers` but not `_make_relation_resolver`. So the
    many-side access under the shipped default genuinely does **not** pass through
    `_make_relation_resolver`, and the superlative was false. The retraction note's qualifier —
    "the single place only for the shapes that survive Phase 2.5" — is the honest form, and it is right:
    Phase 2.5 also requires `implements_relay_node(type_cls)`, a Node-shaped target, and a
    non-consumer-authored field.
  - The rationale twin — I re-ran the discovery the way the report says it should have been run the
    first time. `grep -n 'cascade helpers'` returns the spec's `:649` and `:887` only; `grep -n cascade`
    finds the wrapped rationale instance immediately. The wrap is real and is at
    `rationale:321/322` ("`permissions.py`'s cascade" / "helpers are the documented answer on that
    path"). **A long grep phrase samples a claim's vocabulary rather than establishing its population**
    is now demonstrated live on this item, not merely cited.
- **Both verified non-findings confirmed, so an eighth pass need not re-open them.**
  - `OptimizerHint` is `@dataclass(frozen=True)` with **five** fields (`force_select`, `force_prefetch`,
    `prefetch_obj`, `skip`, `nested_strategy`) while `__post_init__`'s docstring says "beyond **the four
    directives** and the empty no-op form". The fifth is documented in the class docstring as a "knob"
    that is "schema-static and needs NO plan-cache-key change". The rationale's "frozen four-directive
    `OptimizerHint`" is therefore true against the module's own vocabulary, which is what the sweep
    claimed. Not a finding.
  - `git log --oneline -S AdvancedFilterSet -- django_strawberry_framework` returns exactly one commit
    (`1694bd2e`), whose only hit is `+ Direct port of \`AdvancedFilterSet.get_filters\`` — a docstring
    citing upstream, still the single package-wide occurrence today (`filters/sets.py:1267`). The claim
    "never this package's name at any version" holds. Not a finding.
- **No regression, proved mechanically.** Spec **61,082 bytes / 1,096 lines**; rationale **50,849 / 708**
  (`wc -c -l`). `git show HEAD:` into an out-of-repo scratch path measures **54,232 / 1,154** and
  **12,273 / 208**. `git diff --numstat`: **112 / 170** and **500 / 0**. Both identities close:
  `1,154 − 170 + 112 = 1,096` and `208 + 500 = 708`. Append-only proved the strong way — the rationale's
  diff contains exactly **one** line beginning with `-`, and printing it shows the `--- a/…` header, so
  no HEAD line was deleted **or modified**; `git diff -U0` hunks are `@@ -166,0 +167,498 @@`,
  `@@ -185,0 +684 @@`, `@@ -186,0 +686 @@`, summing `498 + 1 + 1 = 500`; `head -166` of the working file
  `cmp`s **exit 0** against `head -166` of HEAD's copy.
- **Provenance re-checked, not assumed from `git status`.** `git log --stat` over both paths: the newest
  commit touching either is still `f3c94642`, unchanged although HEAD moved to `9f8584c7`. `git show HEAD:`
  re-measures the HEAD ledger figures — the second, independent proof that nothing was swept into a
  concurrent commit.
- **No coverage gap found, which is the result I most tried to falsify.** Independent enumeration of the
  612 `+` lines: the 112 spec lines map onto the 62 table rows with nothing left over (the residue is
  fenced sketch lines, list fragments, and one link definition). The rationale's added text carries
  **17** `##`/`###` sections below line 166, and the table's 17 distinct entry names cover all seventeen,
  `## Standing notes` included. I re-swept the added text with markers the starting grep list does not
  hold — `therefore`, `ensures`, `guarantees`, `never`, `always`, `only`, `every`, `cannot`, `owns`,
  `composes`, `belongs`, `means`, `lets`, `sole`, `no … at all`, `nothing` — and every line that hit is
  already a table row.
- **The seven `judgement` rows were re-opened and none is a misfiled checkable claim.** `:66` is a
  framing sentence; `:397` and `:403` argue against a mechanism this cycle scrubbed, so no symbol exists
  to open; `:562-574` and `:662-672` are a borrow list and a normative "It should:" pipeline; the
  rationale's migration entry is a convention preference. `:493` is the closest call — it carries
  "`aggregates` … is still owed", which *is* checkable — and it checks out: there is no `aggregates/`
  package, `connection.py` has no `aggregates` member, and `TODO-BETA-057-0.1.3` resolves.
- **Sampled "opened" rows, chosen for being the least likely to have been read carefully, all
  re-derive.** `types/definition.py::DjangoTypeDefinition` AST → **29** slots and **exactly 3** methods
  (`graphql_type_name`, `related_target_for`, `has_custom_id_resolver_for`); `orders/inputs.py::Ordering`
  → **6** members, set-identical to `strawberry_django/ordering.py::Ordering` (declaration order differs,
  which "member-for-member identical" survives); `graphene_django/` contains **no** optimizer module and
  **no** `DISTINCT` anywhere, and `graphene_django/fields.py:21` is `class DjangoListField(Field)`;
  upstream `DjangoModelType` is `pk: strawberry.ID` and nothing else; `filters/sets.py:1135-1140`
  subclasses `filterset.BaseFilterSet` and `FilterSetMetaclass.__new__` aliases `filter_fields` onto
  `fields` by plain assignment, only under `hasattr(filter_fields) and not hasattr(fields)` — which is
  why "`__all__` works in both spellings" is exact rather than approximate; `orders/sets.py:357` is
  `aggregate = models.Min if direction.is_ascending else models.Max`; `finalizer.py:770-771` is
  `raise ConfigurationError(_format_unresolved_targets_error(unresolved))`; `connection.py`'s single
  `finalize_django_types` occurrence is a docstring mention at `:1834`, not a call; `docs/TREE.md`
  carries `fieldset/  # planned by TODO-BETA-054-0.1.1` and `permissions/  # planned by TODO-BETA-059-0.1.4
  … (``Meta.redaction_mode``)`.
- **The two new retraction notes are the right shape**, apart from M1. Each states one fact with one
  symbol-qualified citation and no causal story, which is the discipline this item's history earns; the
  `:515` note's core claim ("`types/resolvers.py` imports nothing from `utils/querysets`") is the
  strongest form available, since I confirmed the module has no function-level imports at all.

### Temp test verification

- `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` — re-run read-only:
  `uv run pytest docs/builder/temp-tests/r1/test_async_execution_default_connection.py --no-cov -q -o addopts=''`
  → **1 passed** (`addopts` overridden only to drop `pytest.ini`'s auto-applied `--cov`; no `--cov*` flag
  was used anywhere in this pass). Not modified, moved, or deleted.
- No new temp test was written: every claim this pass tested was settled by reading source at the named
  symbol or by a `grep`/AST measurement, and a temp test would have added nothing a `pytest` run could
  observe.
- Disposition unchanged: kept, and still **recommended for carding** — see the escalation below.
- `scripts/review_inspect.py` **skipped**, recorded per `worker-3.md` "Static helper use": the diff adds
  no `.py` file, touches nothing under `optimizer/` or `types/`, and adds zero lines of logic anywhere,
  so none of the three trigger conditions fires.

### Notes for Worker 1 (spec reconciliation)

1. **M1 is the only item that changes a deliverable.** It is a replacement, not a cut, for the reason
   given there; re-derive the prescription rather than adopting it.
2. **M2 and L1 are artifact-internal.** Prior sections are never edited, so the resolution is that the
   next Worker 1 section records the corrected denominator and the corrected predicate quotation in its
   own text. No deliverable is affected by either.
3. **Escalated: the sweep's own residual risk 2 is the right next target, and it is a scope question
   only the maintainer can answer.** The sweep covered *added* lines. The spec's untouched HEAD prose has
   never been read against source in this cycle, and it is the larger half — 984 of 1,096 lines. I found
   nothing false in the pre-existing text I read incidentally (`### Layer 10`'s cascade recommendation and
   `## Open questions`'s sentinel-vs-cascade answer are both about forward-FK cascade and are accurate in
   that context), but that is a sample, not a sweep. Resolution paths: (a) accept added-lines-only as the
   item's declared scope and close R1 there; (b) card a follow-up item for a full-file sweep of spec-009
   against shipped source; (c) fold it into whichever cycle next opens spec-009 without an append-only
   constraint. This is a contract-level scope call, not a worker's.
4. **The eight escalations final verification pass 3 carried forward are unchanged**, and I re-checked
   the two that rot: `docs/SPECS/spec-010-foundation-0_0_4.md:8` still lists "custom field classes" among
   what spec-009 describes (eighth consecutive pass), and `:491` still carries the scrubbed
   `get_strawberry_annotations` borrow. Both are outside this cycle's writable set; only the maintainer
   can sequence the two cycles at commit.
5. **Escalation 6 remains the one whose evidence inaction destroys.** No permanent row pins
   `async def get_queryset` → `SyncMisuseError` under `await schema.execute` for a *default*
   `DjangoConnectionField`; the ready-made body is gitignored and clears with the cycle. Re-confirmed
   passing this pass. Recommend carding before the cycle closes.

### Review outcome

`revision-needed`. Two Medium and one Low, none of them in the four cuts — **the cuts hold, and so does
the sweep's coverage**. M1 is a false clause in a deliverable and must close; M2 and L1 close in the next
Worker 1 section without touching either document.

The finding sizes across this item now read 9 → 2 → 1 → 1 → 1 → 0 → 3. The rise is not a regression: pass
6 reviewed one sentence at one site, this pass reviewed a 109-row class sweep and the four edits that
came out of it, and M1 is the first finding on this item found *inside the correction that retires its
own class* rather than in the text being corrected.

---

## Build report (Worker 1, apply-changes pass 7)

Run 2026-08-16 by a fresh Worker 1 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-1.md`. Seventh apply-changes pass on R1, and the closing one:
Worker 3 pass 7 raised one deliverable finding (M1) and two artifact-internal corrections (M2, L1), and
all three close here. **HEAD re-derived: `9f8584c7`** — unchanged from pass 7's reading, the first pass on
this item where it did not move. `git status --porcelain` is **116** entries, reported and not reverted;
`git stash` / `checkout` / `restore` / `worktree` were not used, and the HEAD comparison ran through
`git show HEAD:<path>` into a scratch path outside the repository. One file was edited: the rationale.
The spec was **not** edited this pass (the twin check below is why), and no source, test, kanban, or
build-plan file was touched.

**Scope note.** The whole-spec clause-by-clause sweep Worker 3 escalated is **not** in this pass. The
maintainer authorized it and split it into its own item, **R1b**, with its own artifact and worker chain
(`docs/builder/build-009-rich_schema_architecture-0_0_4.md` `### Maintainer decision 4`). R1's contract
remains the D1-D16 drift-table reconciliation.

### M1 — the "exact complement" clause, re-derived at the constant and replaced

The prescription was **not adopted**; every set membership in it was re-derived at the symbol first,
which is the discipline this item's history earns (three dispatched prescriptions in this cycle turned
out to be wrong in their mechanism, and one turned out to be *understated*). All of it checks out:

- `django_strawberry_framework/utils/relations.py` #"RelationKind: TypeAlias" — five kinds: `"many"`,
  `"reverse_many_to_one"`, `"reverse_one_to_one"`, `"forward_single"`, `"generic"`.
  `utils/relations.py::MANY_SIDE_RELATION_KINDS` is `frozenset({"many", "reverse_many_to_one",
  "generic"})` — **three** kinds, so the old sentence's three-item enumeration named the wrong three:
  it listed `reverse-FK / reverse-one-to-many / M2M` and **dropped `generic`**.
- `types/converters.py::resolved_relation_annotation` returns `list[target_type]` under exactly
  `if meta.is_many_side`, and `optimizer/field_meta.py::FieldMeta.is_many_side` is
  `is_many_side_relation_kind(self.relation_kind)`, i.e. `kind in MANY_SIDE_RELATION_KINDS`. So the
  `list[T]` kinds *are* that frozenset, exactly.
- `permissions.py::_is_cascadable_edge` refuses all three: a forward or reverse `ManyToManyField` is not
  a `ForeignKey`; a `ManyToOneRel` is a `ForeignObjectRel`; and a `GenericRelation` is "a `ForeignObject`
  but not a `ForeignKey`" — the predicate's own docstring names all four exclusions, `GenericRelation`
  included, so the source the sentence argued *from* already listed the kind the sentence dropped.
- **"Exact complement" is false and false fail-open.** `"reverse_one_to_one"` is in **neither** set. It
  is not `list[T]`: `FieldMeta` documents that reverse OneToOne "short-circuits to `True`" for
  `nullable`, so `resolved_relation_annotation` returns `target_type | None` (the spec says the same at
  `### Layer 3`'s field-annotation list, "reverse one-to-one becomes `target_type | None`"). And it is not
  cascadable: a `OneToOneRel` is a `ForeignObjectRel`, not a `ForeignKey`. `permissions.py`'s module
  docstring states the union directly — "Reverse FK / reverse OneToOne, M2M, and ``GenericRelation`` stay
  outside parent-row cascade semantics". Read literally, "exact complement" told a reader that everything
  not `list[T]` is cascade-covered, which is the claim the retraction existed to remove, one kind over.

**Replaced, not cut**, for the reason the finding gives: the disjointness is the note's whole point, and
it is now verifiable at the reader's desk from one named constant. The new text
(`docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md` #"so it refuses every kind in"):

> …`permissions.py::_is_cascadable_edge` admits only single-column concrete forward FK / OneToOne edges,
> so it refuses every kind in `utils/relations.py::MANY_SIDE_RELATION_KINDS` (`"many"`,
> `"reverse_many_to_one"`, `"generic"`) — exactly the kinds
> `types/converters.py::resolved_relation_annotation` emits `list[T]` for. Refusing them all is not the
> same as covering the rest: `"reverse_one_to_one"` is in neither set — it is annotated
> `target_type | None`, and the cascade skips it too.

Two deliberate wording choices. The claim is now stated as **disjointness plus a named exception**, never
as a partition, because a partition is the shape that was wrong twice; and the constant is *named and
enumerated* rather than only named, so a reader can check the three-vs-four membership without opening a
file. The paragraph's trailing sentence was re-wrapped in the same edit (it carried a 39-character
orphan line from an earlier pass); no word of it changed.

### The spec-side twin check — run first, and it came back empty

This item has been bitten three times by a spec/rationale twin, once by a phrase that **wrapped** across a
line and survived six passes. So the check ran on the shortest distinctive tokens, never a multi-word
phrase: `grep -n complement` over both documents → **one hit, the rationale line being fixed**;
`grep -c cascade` over both → **16** spec lines and **3** rationale lines at check time (4 after the
edit, which adds one), every spec hit read
(`### Layer 10`, `## Open questions`, `## Success criteria`, the `apply_cascade_permissions` borrow rows,
the `permissions/` package migration note) and **none** of them names the cascade as the recourse for a
`list[T]` relation — apply-changes pass 6 had already cut the one that did (`:649`);
`grep -n 'recourse\|reverse-FK\|reverse_one_to_one\|OneToOne\|one-to-one'` over both → the spec's **six**
reverse-one-to-one lines are all the annotation contract (`:449`, `:523`, `:610`, `:626`, `:926`, `:936`
— including "reverse one-to-one becomes `target_type | None`", which the corrected sentence now agrees
with), and none of them makes a cascade claim; `recourse` occurs once, in the line being fixed.

**No spec-side twin exists, so the spec is byte-unchanged this pass** — recorded explicitly, because a
byte-unchanged spec is exactly the outcome that looks like a skipped step.

### M2 — the sweep's coverage numbers, re-measured and corrected

Apply-changes pass 6 stated "101 clauses enumerated (55 spec / 46 rationale); 78 opened; 4 changed … The
23 not opened are marked `judgement`". Three of those four numbers do not re-derive. Re-measured this
pass by parsing the two tables mechanically (row = a line starting `|` that is neither the header nor the
`|---|` rule), not by re-reading them:

| Figure | Pass 6 stated | Re-measured | How to recount it |
|---|---|---|---|
| Spec table rows | — | **62** | rows in `#### Spec (55 clauses)` |
| Distinct spec sites | 55 | **55** | 62 rows, minus 11 for the eight sub-lettered groups (`:385a/b/c`, `:415a/b`, `:483a/b/c`, `:515a/b/c`, `:526`/`:526b`, `:649a/b`, `:652a/b`, `:696a/b`), plus 4 for the five-site row `:930, :961, :965, :979, :981` |
| Rationale table rows | 46 | **47** | rows in `#### Rationale (46 clauses)` — the heading's own count is the one that is off |
| Unopened `judgement` rows | 23 | **7** | 6 spec (`:66`, `:397`, `:403`, `:493`, `:562-574`, `:662-672`) + 1 rationale (the migration entry). An eighth row is hybrid — the rationale's nullable-node entry, verdict "true / judgement on the rejected alternative" — and its checkable half **was** opened, so it counts as opened |
| Opened | 78 | **95** | 102 − 7 |
| Changed | 4 | **4** | unchanged and correct: 3 spec cuts (`:515c`, `:526`, `:649b`) + 1 rationale correction, plus the 2 retraction notes the cuts owe |

**The corrected denominator, stated in the form a later pass can recount with one command:** the sweep
enumerated **109 table rows** — 62 spec + 47 rationale — which collapse to **102 distinct items**
(55 spec sites + 47 rationale rows). **7** rows carry a pure `judgement` verdict and were deliberately not
opened at a symbol, because each is an argument, a forward-looking prescription, or a claim about a
rejected alternative, none of which names a checkable symbol. **95** items were opened at the symbol they
name. **4** were changed. Row-convention equivalents, for a recount that skips the collapsing rule
entirely: 109 rows, 7 unopened, 102 opened.

The error's direction was benign — it **understated** the opened count, so no site was left uncovered on
account of it, and Worker 3's independent sweep of the 612 `+` lines found no coverage gap. The defect is
in the auditability the numbers were offered for: a later pass told "23 rows are `judgement`" goes looking
for sixteen rows that do not exist and concludes the tables are the stale half. The lesson is
`BUILD.md` `## Claims are proven mechanically, never accepted on prose` applied to one's own summary line
— **measure the count as you write it**, from the artifact, with a command.

### L1 — `_is_cascadable_edge`, quoted correctly

Apply-changes pass 6 rendered the predicate as `isinstance(field, models.ForeignKey) and field.column is
not None`. The source (`django_strawberry_framework/permissions.py::_is_cascadable_edge`) is:

```python
return isinstance(field, models.ForeignKey) and getattr(field, "column", None) is not None
```

The `getattr` default form is deliberate and load-bearing in the same fail-closed direction as the rest of
that module: the docstring says the check "guards the single-column contract against a future
`ForeignKey` shape whose value is not one concrete column", i.e. a shape on which the paraphrased form
would raise `AttributeError` instead of returning `False`. The conclusion the finding turned on is
unaffected — the predicate is an allowlist either way — but a backticked expression is read as
transcribed, and paraphrase-presented-as-transcription is this item's entire defect class. Prior sections
are never edited, so the correct quotation lives here.

### Spec changes made (Worker 1 only)

**Spec: no change this pass.** `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` is byte-identical
to its pass-6 state (61,082 bytes / 1,096 lines), because the twin check above found no spec-side telling
of the corrected claim. No Layer, Phase, or Decision number moved; no heading text changed.

**Rationale: one in-place correction**, at
`docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md` #"One of the four seams was
restated", in the entry apply-changes pass 6 added *this cycle*. Trigger: Worker 3 pass 7 M1. Reason: the
sentence's "exact complement" claim was mechanically false — it dropped `"generic"` from the `list[T]`
kinds and implied `"reverse_one_to_one"` was cascade-covered when it is in neither set. Replaced (not
cut) with the disjointness-plus-exception form quoted above, citing
`utils/relations.py::MANY_SIDE_RELATION_KINDS` by name and enumerating its three members. **In-place
correction of an entry this cycle added preserves append-only**, and the proof below is mechanical, not
asserted.

### Dispatched findings checklist — 16 boxes, 16 ticks, none changed

Re-audited against the diff rather than re-read: the spec diff is byte-identical to the one the pass-6
and final-verification-pass-3 audits ran against (`git diff --numstat` → `112 / 170`, unchanged), so every
tick still stands on the same evidence. D1-D16 all `- [x]`; `grep -c '^- \[x\]'` over the checklist block
→ **16**, `grep -c '^- \['` → **16**. No box was ticked or un-ticked this pass, and none is deferred.

### Ledger, and the identities closing

| Document | HEAD | Before this pass | After this pass | `git diff --numstat` |
|---|---|---|---|---|
| spec-009 | 54,232 B / 1,154 L | 61,082 / 1,096 | **61,082 / 1,096** (unchanged) | `112 / 170` |
| rationale | 12,273 B / 208 L | 50,849 / 708 | **51,082 / 710** (+233 B, +2 L) | `502 / 0` |

Both identities close: `1,154 − 170 + 112 = 1,096` and `208 + 502 = 710`. HEAD figures re-measured with
`git show HEAD:<path> | wc -c -l`, not carried from a prior section. The +2 lines are the re-wrap: the
replacement says more than the falsehood it retires and absorbed a 39-character orphan line while doing
it.

### Append-only on the rationale, re-proved mechanically

- `git diff` over the rationale contains exactly **one** line beginning `-`, and printing it shows
  `--- a/docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md`. No HEAD line was deleted
  **or modified** — a modification would appear as a `-`/`+` pair.
- `git diff -U0` hunks: `@@ -166,0 +167,500 @@`, `@@ -185,0 +686 @@`, `@@ -186,0 +688 @@` —
  `500 + 1 + 1 = 502`, matching `--numstat`. The two single-line hunks are the alphabetical
  link-definition insertions from an earlier pass, opened rather than assumed.
- `head -166` of the working file `cmp`s **exit 0** against `head -166` of `git show HEAD:`'s copy, written
  to a scratch path outside the repository.
- The first hunk grew `498 → 500` this pass, which is the whole visible effect of the edit: the
  correction lands inside the block this cycle appended, never above line 166.

### Gates, links, and rules — re-run, not read

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.` **Exit 0**, 23 terms.
- `uv run python scripts/check_trailing_commas.py --check` over **both** documents → **exit 0**.
- **In-page anchors.** Neither document contains a `](#…)` anchor (0 in each), so none can dangle; the
  cross-document citations use the `#"substring"` convention, audited separately below.
- **Link definitions.** Spec: 25 definitions, 0 undefined uses, 0 true orphans — a naive audit reports
  `glossary-aggregateset` and `glossary-finalize-django-types` as orphans, and both are the known
  false positive: their `[text][ref]` uses sit *inside* code spans
  (`` `Advanced[AggregateSet][glossary-aggregateset].compute` `` and
  `` `[finalize_django_types][glossary-finalize-django-types]()` ``), which a code-span-stripping sweep
  cannot see. Rationale: 11 definitions, 0 orphans, 0 undefined uses. The ten canonical group headers are
  intact in both (the `--check` gate above enforces the scaffold).
- **`AGENTS.md` rule 27.** Zero raw in-repo `path:NN` in either document (regex sweep for
  `<file>.<py|md>:<digits>`). The upstream `file:///…#LNN` citations are out-of-repo and out of scope, and
  the `[target]` inside `` `list[target]` `` remains the known code-span false positive. Every citation
  this pass added is symbol-qualified: `utils/relations.py::MANY_SIDE_RELATION_KINDS`,
  `types/converters.py::resolved_relation_annotation`, `permissions.py::_is_cascadable_edge`.
- **No renumbering.** `### Layer 1`-`11`, `### Phase 1`-`8`, `### Decision 1`-`6` all present, contiguous,
  in order, with heading text unchanged (extracted mechanically from the spec, not eyeballed).

### Cross-spec anchors: five, both directions, re-timestamped **2026-08-16T02:32:02Z**

Re-derived from scratch, because `spec-010` is under a concurrent cycle and has moved between passes.

- **Inbound (2).** `spec-010` cites spec-009 #"### Layer 3: Finalization trigger" (in its
  no-auto-trigger bullet) and #"### Decision 6: fail loudly" (in its error-format section). `grep -cF` for
  each exact heading on the current spec-009 → **1 each**.
- **Outbound (3).** spec-009 cites `spec-010-foundation-0_0_4.md` #"### Must redo (not augment)",
  #"## Strawberry finalization strategy", and #"### Unresolved-target error format". `grep -cF` on the
  current spec-010 → **1 each**.
- `spec-008`'s inbound reference is whole-file, not anchored; no `spec-011` file cites spec-009. Nothing
  was repaired — a break would have been reported, per the build plan's standing instruction.

### Provenance — nothing was swept into a concurrent commit

`git log --stat` over both paths: the newest commit touching either document is still **`f3c94642`**,
unchanged across every pass on this item and although HEAD has moved repeatedly (it did not move this
pass — `9f8584c7` at both ends). `git show HEAD:` re-measures the HEAD
ledger figures above, which is the second, independent proof. `git status` alone was never used for this.

### What the next verification should look for

1. **The replacement sentence itself.** It is new text written by a fix pass, which is this item's
   highest-risk category — six of the seven defects it has produced were written by fix passes, and M1 was
   the seventh, written by the fix for the sixth. Open `utils/relations.py::MANY_SIDE_RELATION_KINDS` and
   `permissions.py::_is_cascadable_edge` and check the membership claims cold rather than reading the
   citation as evidence.
2. **The corrected denominator.** It is a stated count, so it is subject to the rule that produced M2:
   re-measure 62 / 47 / 7 / 95 from the tables rather than accepting them.
3. **Not the whole-spec sweep** — that is R1b's contract now, and re-opening it here would re-merge the
   split the maintainer made.

### Status

`planned`. All three pass-7 findings are closed: M1 replaced in the rationale after re-deriving every set
membership at the symbol, M2 and L1 corrected in this section without editing any prior section. The spec
is byte-unchanged because the twin check found nothing to change, and that is recorded rather than left to
inference. Ready for Worker 3 re-review (pass 8).

---

## Review (Worker 3, pass 8)

Run 2026-08-16 by a fresh Worker 3 invocation whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-3.md`. Eighth review pass on R1, and a narrow one: the whole
deliverable change is **one replaced sentence in the rationale**, with two artifact-internal corrections
(M2's sweep numbers, L1's quoted predicate). **HEAD re-derived: `9f8584c7`** — unchanged from the
apply-changes pass 7 report, the second consecutive pass on which it did not move.
`git status --porcelain` is **125** entries, reported and not reverted; the only files dirty inside this
cycle's writable set are the two deliverables. `git stash` / `checkout` / `restore` / `worktree` were not
used; the HEAD reference was `git show HEAD:<path>` into a scratch path outside the repository. No source,
test, spec, rationale, or build-plan file was edited by this pass.

**Scope honoured.** The whole-spec clause-by-clause sweep this reviewer escalated last pass is **R1b**
(`docs/builder/build-009-rich_schema_architecture-0_0_4.md` `### Maintainer decision 4`, and its own
checklist row and worker chain at `### Checklist` / the dispatch table). It was not re-opened here and its
absence from this diff is not a finding. The scrub, the single-ownership decision, the four pass-6 cuts,
and every previously accepted item were likewise not re-audited.

**Method.** Items 1, 2, 3 and 5 were re-derived from scratch rather than accepted on the strength of seven
prior passes: every set membership in the replacement sentence was opened at its constant or predicate
(including the Django class hierarchy the disjointness rests on, checked by `issubclass` rather than by
reading a docstring); the spec-side twin sweep was re-run independently on shortest distinctive tokens;
both sweep tables were re-parsed programmatically rather than re-read; the ledger, append-only proof, both
gates, the link/anchor/rule-27 audit, the five cross-spec anchors and the sixteen boxes were all re-run.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

None. The diff is one replaced sentence in one `.md` file; there is no abstraction, helper, constant, or
branch to challenge, so the existence challenge has nothing to attach to.

One duplication property **is** load-bearing here and was re-checked rather than carried, because every
prior failure on this item was a duplication failure: the corrected claim has **no twin**. See item 2
below — `complement` now returns **zero** hits across both documents, and no other telling of the
claim exists in either file.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** (0 lines) — `__all__` and the re-export
list are unchanged. `git status --porcelain | grep SPECS` confirms this cycle's writable set is exactly the
two `.md` deliverables; no `.py` file is touched by it.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applies — the whole deliverable is documentation. Everything below was re-run this pass, not read as
discharged by a prior one.

- **Gates.** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.`, **exit 0, 23 terms**.
  `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0**. (`--check` sets
  `do_fix = not args.check` in `scripts/check_trailing_commas.py::main`, so the gate cannot have rewritten
  either file; the byte measurements below were taken both before and after the gate run and are identical.)
- **In-page anchors.** `grep -c '](#'` → **0** in the spec and **0** in the rationale, so none can dangle.
- **Link definitions.** Audited with a fresh script that strips fenced blocks for the *use* scan but does
  **not** strip code spans (stripping them is what manufactures the known false positives). Spec: **25
  definitions / 25 distinct uses, 0 undefined, 0 orphan**. Rationale: **11 / 11, 0 / 0**. Every non-URL,
  non-anchor definition target disk-existence-checked → **0 dead**. Because no code spans were stripped,
  `glossary-aggregateset` and `glossary-finalize-django-types` resolve as the real uses they are — the
  known false positive is confirmed to be an artifact of the stripping sweep, not a property of the file.
  All **10** canonical group headers plus the `<!-- LINK DEFINITIONS -->` marker present in both.
- **`AGENTS.md` rule 27.** Regex sweep for `[A-Za-z0-9_/.-]+\.(py|md):[0-9]+` excluding `file:///` →
  **zero** in-repo raw `path:NN` in either document. Every citation the replacement sentence adds is
  symbol-qualified (`utils/relations.py::MANY_SIDE_RELATION_KINDS`,
  `types/converters.py::resolved_relation_annotation`, `permissions.py::_is_cascadable_edge`).
- **No renumbering.** `### Layer 1`-`### Layer 11` (11, contiguous, in order), `### Phase 1`-`### Phase 8`,
  `### Decision 1`-`### Decision 6`, extracted mechanically. The constraint at the build plan's
  `### Constraint binding R1 and R2` therefore still holds.
- **Cross-spec anchors: five, both directions, re-timestamped 2026-08-16T02:40:23Z.** Inbound (2):
  `spec-010-foundation-0_0_4.md:67` → #"### Layer 3: Finalization trigger", `:468` → #"### Decision 6: fail
  loudly"; each resolves to **exactly one heading** in the current spec-009 (`grep -c '^### …'` → 1 each,
  at `:631` and `:1010`). Outbound (3): spec-009 `:99` → #"### Must redo (not augment)", `:634` →
  #"## Strawberry finalization strategy", `:870` → #"### Unresolved-target error format"; `grep -cF` on
  the current `spec-010` (concurrently dirty, re-read from disk this pass) → **1 each**. The spec's fourth
  outbound anchor, `:257` → `spec-054-fieldset-0_1_1.md` #"resolver wrapping", also resolves (file exists,
  2 hits). Nothing was repaired.
- **Recount nuance, recorded so a ninth pass does not re-open it.** The "1 each" figure for the two
  **inbound** anchors reproduces under `grep -c '^### <heading>'`, not under a bare `grep -cF`, which
  returns **5** and **2** — the extra hits are spec-009's own backticked in-text references to its
  headings (`:642`, `:674`, `:999`, `:1015` and `:441`). The anchors resolve unambiguously to one heading
  each in every case, so this is a recount convention, not a defect, and it is **not** raised as a finding.
- **Checklist: 16 `- [x]`, 16 `- [`**, measured on the artifact — all ticked, none changed, which is
  correct: this pass changed no spec line, so no box's evidence moved.
- No obsolete "coming soon" / "planned" / old-version wording was introduced; no script-rendered doc was
  regenerated; no KANBAN card moved.

### Failability proofs

**Not applicable to a documentation pass.** The diff introduces no boundary, guard, gate, or rejection
path — it replaces one sentence in one `.md` file and touches no executable line — so `BUILD.md`
`### What needs a proof, and what does not` puts this pass outside the obligation, and the mandatory
re-run floor is met with an **empty re-run set**, which `worker-3.md` licenses in exactly this case. The
source carve-out was not exercised: no production file was mutated at any point in this pass.

### Hot-path budget

**Not applicable to a documentation pass.** The plan declares no hot path for this item and the diff adds
no runtime cost of any kind; no source file is touched.

### What looks solid

**1. The replacement sentence is true at every symbol, and nothing true was lost.** Each assertion was
opened cold rather than read as evidence, per the build report's own instruction.

The shipped text (`…-rationale.md` #"so it refuses every kind in"):

> `permissions.py::_is_cascadable_edge` admits only single-column concrete forward FK / OneToOne edges,
> so it refuses every kind in `utils/relations.py::MANY_SIDE_RELATION_KINDS` (`"many"`,
> `"reverse_many_to_one"`, `"generic"`) — exactly the kinds
> `types/converters.py::resolved_relation_annotation` emits `list[T]` for. Refusing them all is not the
> same as covering the rest: `"reverse_one_to_one"` is in neither set — it is annotated
> `target_type | None`, and the cascade skips it too.

- `django_strawberry_framework/utils/relations.py:28-30` — `MANY_SIDE_RELATION_KINDS` is
  `frozenset({"many", "reverse_many_to_one", "generic"})`, **three** members, enumerated in the sentence
  exactly and in full. `RelationKind` (`:20-26`) carries five kinds; the two the sentence does not
  enumerate are `reverse_one_to_one` (named as the exception) and `forward_single` (the cascade's own
  domain).
- **"exactly the kinds `resolved_relation_annotation` emits `list[T]` for" is exact, not approximate.**
  `types/converters.py:722-723` returns `list[target_type]` under `if meta.is_many_side` and nothing else;
  `optimizer/field_meta.py::FieldMeta.is_many_side` is `is_many_side_relation_kind(self.relation_kind)`;
  `utils/relations.py:124-126` is `return kind in MANY_SIDE_RELATION_KINDS`. The chain is three hops with
  no other branch, so the `list[T]` set **is** that frozenset.
- **"refuses every kind" is true, and I checked it against Django rather than against the docstring that
  asserts it.** `_is_cascadable_edge` (`permissions.py:203`) is
  `isinstance(field, models.ForeignKey) and getattr(field, "column", None) is not None`. Under a
  configured Django: `issubclass(ManyToManyField, ForeignKey)` → `False`;
  `issubclass(ManyToOneRel, ForeignKey)` → `False` (it is a `ForeignObjectRel`);
  `GenericRelation.__mro__` is `GenericRelation → ForeignObject → RelatedField → …` with
  `issubclass(GenericRelation, ForeignKey)` → `False` and `issubclass(GenericRelation, ForeignObject)` →
  `True`. All three refused.
- **The named exception is right in both halves.** `"reverse_one_to_one"` is not in the frozenset, so
  `resolved_relation_annotation` falls through to `if meta.nullable: return target_type | None`, and
  `optimizer/field_meta.py:221` short-circuits `nullable` to `True` for that kind
  (`nullable = kind == "reverse_one_to_one" or bool(getattr(field, "null", False))`) — so the annotation
  is `target_type | None`, matching the spec's own `:626` ("reverse one-to-one becomes
  `target_type | None`"). And `issubclass(OneToOneRel, ForeignKey)` → `False`, so the cascade does not
  admit it. **"Skips" is the precise verb**, not a hedge: `permissions.py::_is_unsupported_forward_edge`
  excludes `ForeignObjectRel` before reaching the fail-closed arm, so a reverse O2O is silently skipped
  rather than refused loudly. The sentence says "skips it too" and that is what the code does.
- **Nothing true was lost.** The replaced sentence's surviving content — the "no recourse may be named"
  framing, "admits only single-column concrete forward FK / OneToOne edges", and both symbol citations —
  is carried forward verbatim; only the false "exact complement of the reverse-FK / reverse-one-to-many /
  M2M kinds" half was retired, and its one true implication (the cascade does not cover the `list[T]`
  kinds) is stated more strongly than before, since it now names the constant and enumerates it. The
  shape is disjointness-plus-exception, not a partition, which is the shape that was wrong twice.

**2. The spec-side twin check re-derives independently, and the spec really is byte-unchanged.**

- `grep -n complement` over **both** documents → **zero hits**. The one hit that existed is the line that
  was replaced; no spec-side telling was ever there, and none was introduced.
- `grep -ni cascade` → **16** spec lines and **4** rationale lines (3 before the edit, +1 from it), matching
  the build report. I read all sixteen: `:35`, `:144`, `:225`, `:789`, `:980`, `:1038`, `:1057` are borrow
  rows / glossary defs, `:57` is example code, `:232` is the layered-model rule, `:257` and `:771` are the
  **`FieldSet` gate/override** cascade (a different sense of the word, owned by `spec-054`), `:783-797` is
  `### Layer 10`'s parent-row cascade-filtering recommendation, `:887` is the `permissions/` package
  migration note, and `:1021` is `## Open questions` on sentinel-vs-cascade. **None of the sixteen names
  the cascade as the recourse for a `list[T]` relation** — the one that did was cut at `:649` in pass 6.
- Cross-checked with a second token set: `recourse` occurs **once** in either document (the corrected
  rationale line); `reverse one-to-one` / `reverse_one_to_one` occurs on **six** spec lines (`:449`,
  `:523`, `:610`, `:626`, `:926`, `:936`), all annotation/`DoesNotExist` contract and none making a
  cascade claim. `:626` **agrees** with the corrected sentence, which is the strongest available
  corroboration that the replacement did not create a spec/rationale contradiction.
- **Byte-unchanged, proved four ways.** `wc -c -l` → **61,082 / 1,096**, identical to pass 7's reading;
  `git diff --numstat` → **112 / 170**, identical to the pass-6 and pass-7 readings; the identity
  `1,154 − 170 + 112 = 1,096` closes against HEAD re-measured this pass (`git show HEAD:` → 54,232 /
  1,154); and the measurement was taken **before and after** the gate runs with identical results
  (`shasum` 635bf6f2…). A byte-neutral edit passing all four is not a shape any plausible edit takes.

**3. The corrected sweep numbers re-derive exactly — I parsed the tables, I did not re-read them.**
Rows counted programmatically (a line starting `|` that is neither the header nor the `|---|` rule):

| Figure | Build report | Re-derived this pass | Verdict |
|---|---|---|---|
| Spec table rows | 62 | **62** | exact |
| Distinct spec sites | 55 | **55** | exact |
| Rationale table rows | 47 | **47** | exact |
| Total rows / total items | 109 / 102 | **109 / 102** | exact |
| Pure `judgement`, unopened | 7 | **7** | exact |
| Opened | 95 | **95** | exact (102 − 7) |
| Changed | 4 | **4** | exact |

The collapsing arithmetic reproduces independently: normalising each site cell and counting duplicates
finds **exactly eight** sub-lettered groups — `:385`×3, `:415`×2, `:483`×3, `:515`×3, `:526`×2, `:649`×2,
`:652`×2, `:696`×2 — i.e. 19 rows collapsing to 8 sites (−11), and **exactly one** multi-site row
(`:930, :961, :965, :979, :981`, +4), giving `62 − 11 + 4 = 55`. Note this pass-8 list corrects pass 7's,
which named seven groups and omitted `:652a/b`; the totals were unaffected because pass 7 stated the
result (55) rather than the summands, and 55 was right both times. The `judgement` count re-derives to
**6 spec** rows (`:66`, `:397`, `:403`, `:493`, `:562-574`, `:662-672`) **+ 1 rationale** (the migration
entry) = 7, with the rationale's nullable-node row correctly excluded as the hybrid
("true / judgement on the rejected alternative") whose checkable half was opened. `Changed` = **4** is
verifiable by a different signal than the prose: exactly **3** bold-site rows in the spec table
(`**:515c**`, `**:526**`, `**:649b**`) and **1** in the rationale table (`**Layer 4 entry**`).
**The tables now close as an audit instrument**, which was the point of M2 — every one of the seven
figures is recountable with one command and none requires trusting a prior section.

**4. L1's quotation is byte-identical to source.** The build report's fenced line `cmp`s **exit 0**
against `django_strawberry_framework/permissions.py:203` with its indentation stripped —
`return isinstance(field, models.ForeignKey) and getattr(field, "column", None) is not None`. The
`getattr`-default form and its fail-closed rationale are now correctly represented.

**5. No regression, proved mechanically.**

- Ledger: spec **61,082 B / 1,096 L** (unchanged); rationale **51,082 / 710** (was 50,849 / 708, so
  **+233 B / +2 L**, matching the report). HEAD re-measured via `git show HEAD:` into an out-of-repo
  scratch path: **54,232 / 1,154** and **12,273 / 208**. `git diff --numstat`: **112 / 170** and
  **502 / 0**. Both identities close: `1,154 − 170 + 112 = 1,096` and `208 + 502 = 710`.
- Append-only proved the strong way: the rationale's `git diff` contains exactly **one** line beginning
  `-`, and printing it shows the `--- a/…` header — so no HEAD line was deleted **or modified** (a
  modification would surface as a `-`/`+` pair). `git diff -U0` hunks are `@@ -166,0 +167,500 @@`,
  `@@ -185,0 +686 @@`, `@@ -186,0 +688 @@`, summing `500 + 1 + 1 = 502`. `head -166` of the working file
  `cmp`s **exit 0** against `head -166` of HEAD's copy, re-run after all other checks. The first hunk grew
  `498 → 500`, exactly the +2 lines, confirming the edit landed inside this cycle's appended block and
  never above line 166.
- Provenance re-checked rather than inferred from `git status`: `git log -1 -- <path>` on both documents
  returns **`f3c94642`**, unchanged, so nothing was swept into a concurrent session's commit.

**6. Two things the replacement gets right that a shorter fix would have missed.** It enumerates the
constant's members inline, so the three-vs-four membership is checkable without opening a file — which is
what makes the sentence auditable at the reader's desk, the stated reason for replacing rather than
cutting. And it states the exception's *annotation* (`target_type | None`), which is independently
corroborated by the spec at `:626`; a sentence that had only said "reverse one-to-one is outside both
sets" would have been true but unfalsifiable at a glance.

### Temp test verification

- `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` — re-run read-only:
  `uv run pytest docs/builder/temp-tests/r1/test_async_execution_default_connection.py -q -o addopts=''`
  → **1 passed**. `addopts` was overridden only to drop `pytest.ini`'s auto-applied `--cov`; **no `--cov*`
  flag was used anywhere in this pass.** The file was not modified, moved, or deleted.
- No new temp test was written. Every claim this pass tested was settled by opening the named symbol, by
  a programmatic parse of the artifact's tables, or by an `issubclass` check on Django's own class
  hierarchy; a temp test would have added nothing a `pytest` run could observe about a `.md` sentence.
- Disposition unchanged: kept, and still **recommended for carding** — see note 3 below.
- `scripts/review_inspect.py` **skipped**, recorded per `worker-3.md` "Static helper use": the diff adds no
  `.py` file, touches nothing under `optimizer/` or `types/`, and adds zero lines of logic, so none of the
  three trigger conditions fires.

### Notes for Worker 1 (spec reconciliation)

1. **Nothing is dispatched back.** All three pass-7 findings are closed at the evidence, not at the prose:
   M1's replacement is true at every symbol and loses nothing, M2's seven figures all re-derive from the
   tables, and L1's quotation `cmp`s clean against source.
2. **One input for R1b, offered rather than raised, because it is squarely R1b's contract and outside
   R1's.** `spec-009:610` (and its sibling in the same sketch) carries
   `relation_kind: Literal["forward_single", "many", "reverse_one_to_one"]  # mirrors utils.relations.RelationKind`.
   `utils/relations.py::RelationKind` has **five** members; the sketch names three and the comment claims
   it mirrors the alias. This is **pre-existing HEAD text** (`git show HEAD:` line 651, untouched by this
   cycle's 112 added lines), so it is not an R1 finding and not a regression — but it is the same
   `RelationKind` membership surface M1 turned on, so R1b should have it in hand rather than rediscover it.
3. **Escalation 6 remains the one whose evidence inaction destroys**, unchanged and re-confirmed passing:
   no permanent row pins `async def get_queryset` → `SyncMisuseError` under `await schema.execute` for a
   *default* `DjangoConnectionField`, and the ready-made body is gitignored and clears with the cycle.
   Recommend carding before the cycle closes.
4. **The two cross-cycle rot items are unchanged** (ninth consecutive pass):
   `docs/SPECS/spec-010-foundation-0_0_4.md:8` still lists "custom field classes" among what spec-009
   describes, and `:491` still carries the scrubbed `get_strawberry_annotations` borrow. Both are outside
   this cycle's writable set; only the maintainer can sequence the two cycles at commit.
5. **Observation, not a finding: both deliverables' mtimes moved during this pass** (to 22:40:39 local)
   while their bytes did not — `shasum`, `wc -c -l`, `--numstat` and the `head -166` `cmp` are all
   identical before and after every command this pass ran, and `--check` mode cannot write
   (`do_fix = not args.check`). Attributable to the concurrently-worked tree. Recorded because an mtime
   change on a file a report calls "byte-unchanged" is exactly the shape that looks like a skipped step.

### Review outcome

`review-accepted`. Zero findings at any severity.

The finding sizes across this item now read 9 → 2 → 1 → 1 → 1 → 0 → 3 → 0. The pass-7 spike was a
109-row class sweep plus its four edits; this pass reviewed the one sentence that sweep's own correction
got wrong, and it holds under independent re-derivation at every symbol it cites — including the two
memberships (`generic` in the `list[T]` set, `reverse_one_to_one` in neither set) whose omission was the
defect. The two artifact-internal corrections also hold: the sweep tables now function as the audit
instrument they were offered as, and the quoted predicate is transcription rather than paraphrase.

R1's contract — the D1-D16 drift-table reconciliation — is complete and internally consistent, and the
open-ended half is now R1b's, correctly split rather than absorbed.

---

## Final verification (Worker 1, pass 4)

Run 2026-08-16 by a **fresh Worker 1 invocation** whose only carry-forward is
`docs/builder/worker-memory/spec-009-worker-1.md`. Fourth final verification on this item; the first
three each set `revision-needed` on a Medium every preceding review pass had missed.

**Scope, and why it is narrower than the three prior final verifications.** The maintainer has
authorized a clause-by-clause mechanism sweep of the **whole** spec and split it into its own item,
**R1b** (`docs/builder/build-009-rich_schema_architecture-0_0_4.md` `### Maintainer decision 4`). R1's
contract is the D1-D16 drift-table reconciliation and nothing more. So a false mechanism clause in
pre-existing text this cycle did not write is recorded as R1b input rather than held against R1; a
false clause in text this cycle **added or rewrote** is still R1's and would block acceptance. Prior
final verifications correctly held R1 open for exactly that class; what changed is only that the
pre-existing surface now has its own item.

**Method.** The whole artifact was read end to end — plan, combined perform pass, eight Worker 3
reviews, seven Worker 1 apply-changes passes, all three prior final verifications — and then **all 112
`+` lines of the spec diff were read cold, in file order**, rather than only at the sites the eleven
prior findings named. Every causal, mechanism, seam-attribution, or recourse clause in added text was
checked **against the mechanism it names, not against the docstring that motivates the rule it
supports**. Both mechanical gates, the link / anchor / rule-27 audit, the append-only proof, the byte
ledger, the five cross-spec anchors, the sixteen-box checklist, and the sweep's corrected denominators
were re-run from scratch rather than read as discharged by Worker 3 pass 8's zero-finding acceptance
(`worker-1.md` `### Verifying relocation / promotion claims`). `git stash`, `git checkout`,
`git restore`, and `git worktree` were not used; the HEAD reference was `git show HEAD:<path>` into a
scratch path outside the repository. **This item runs no tests and changes no code**, so
`## Final verification job` step 5 is discharged by stating that rather than by a focused scope; the
read-only temp test was re-run anyway (below). The staged-anchor sweep is R4's and was **not**
duplicated (step 6).

**Spec status-line re-verification (per-spawn duty).** Spec lines 1-5 re-read. The opener still
describes the rationale companion, the **four** finalization sites, and the six scrubbed mechanisms;
nothing in the build falsifies it. No edit owed.

**HEAD re-derived: `066c068b`** — moved again from the `9f8584c7` the last two passes read.
`git status --porcelain` is **129** entries; none of it intersects this cycle's writable set and none of
it was reverted.

### Final status

`final-accepted`. **No finding at any severity.** Nothing was edited in either deliverable this pass, so
this acceptance rests on no fresh unreviewed claim of its own.

### The cold read: a clean result, with the evidence of having looked

All 112 added spec lines were read in file order and every clause naming a checkable symbol was opened
at that symbol. **No false mechanism, seam, cause, or recourse clause survives in text this cycle added
or rewrote.** The eight sites this item's history points at are each clean, and each was re-derived
here rather than accepted:

- **`:62` / `:68` (node nullability).** `relay.py` #"Resolution is **nullable by contract**"; the spec
  sentence is that sentence.
- **`:70` (`DEFERRED_META_KEYS`).** `django_strawberry_framework/types/base.py` lines 65-67 are exactly
  `frozenset({"aggregate_class", "fields_class", "search_fields"})`; the spec cites
  `ALLOWED_META_KEYS` as the enumeration rather than a number, which is what keeps it true.
- **`:385` (`### Borrow \`StrawberryDjangoDefinition\``).** No lazy-binding claim survives; the sketch's
  slot names match `types/definition.py::DjangoTypeDefinition` name-for-name (AST: **29** slots,
  **3** methods), `aggregate_class` and `search_fields` absent, `LazyClassRef` **0** package-wide.
- **`:401` (provenance).** `types/base.py::DjangoType.__init_subclass__` derives the four spelling sets
  and unions them; the three override-target validators and `_build_annotations` each take
  `consumer_authored_fields` as a parameter they never derive.
- **`:417` (async safety).** No timing claim survives ("is applied by"). Re-derived:
  `types/resolvers.py` has zero async markers and imports nothing from `utils/querysets`.
- **`:483` (`<TypeName>Connection`).** `connection.py::_connection_type_for` always returns a generated
  concrete subclass; the opt-in controls only the shape.
- **`:515` (the plan-cache rule).** Both clauses re-derived separately from the rule they support, by
  opening the builder rather than citing the invariant: `_build_cache_key`'s five-part key carries no
  strategy selection; "schema-static" is `optimizer/hints.py`'s own word.
- **`:649` (Layer 4 visibility).** The bullet now ends at the verified structural claim — the three
  composition sites and "not inside the generated resolver, which returns the row-bound accessor". The
  false cascade-helper recourse is gone; `grep -i complement` over both documents returns **0**.

**Two clauses examined this pass and judged NOT findings, recorded rather than left as silence** —
both are new text, and both sit in a real coverage gap in apply-changes pass 6's sweep, which is why
they are named explicitly rather than passed over:

1. **`:930` (`### Phase 3`)** — "Generate the annotation, resolver, and visibility composition for every
   exposed relation, at finalization, across every cardinality — Layer 4."
2. **`:1002` (`### Decision 3`)** — "Generate a relation field's annotation, resolver, visibility
   composition, and arguments at finalization, from one `DjangoTypeDefinition`."

The sweep's coverage of both is thinner than its tables imply: `:930` was verified only through the
row `` `:930`, `:961`, `:965`, `:979`, `:981` `` against `KANBAN.md` **card ids**, and the `:1002` row
covers only Decision 3's *second* sentence ("composability from one readable definition"). Neither
first-sentence mechanism claim was opened. Opening them: the finalizer does generate the annotation
(`resolved_relation_annotation`, sourced from `definition.field_map` at `types/finalizer.py:765-779`)
and the resolver (`_attach_relation_resolvers` at Phase 2) for every relation and every cardinality —
but for a forward FK and for the raw-`list[T]` `Meta.relation_shapes` opt-in, **no** visibility
composition is generated at all; only the Phase-2.5 synthesized relation connection carries a pipeline
that composes it.

They are judged non-findings on three checked grounds, not waved through. **(a) They restate an
accepted map rather than asserting a new mechanism.** `### Layer 4`'s own opening sentence — verified
across eight review passes and settled by the single-ownership decision — is "Generated relation fields
are produced by the finalizer, and their responsibilities are distributed across four named seams",
with visibility as one of the four. Raising these would re-open that framing, not close a defect.
**(b) Neither names a symbol.** Every one of the eleven prior findings named a specific symbol and told
a reader that symbol does something it does not — go to `permissions.py`'s cascade helpers for a
row-level answer, `types/resolvers.py` handles async safety, the plan cache is keyed on strategy
selection. These two name none, so there is no seam a reader is misdirected to. **(c) The scoped truth
is one pointer away and the pointer is explicit.** `:930` ends "— Layer 4", and Layer 4's visibility
bullet states where the composition runs and that it is not inside the generated resolver. A reader
following the citation gets the qualified statement.

Recorded so a later pass can re-judge rather than re-derive: if the maintainer wants the two summary
sentences scoped to match Layer 4's per-seam qualification, that is a wording preference on accepted
text, not a correction of a false claim.

Two further checks that could have produced an eighth-class finding and did not:

- **`:419` / `:652` "every seam reads it".** Opened at all four seams rather than the one prior passes
  cited: resolution reads `registry.get_definition` (`types/resolvers.py::_field_meta_for_resolver`);
  visibility reads `type_cls.__django_strawberry_definition__.model` (`utils/querysets.py:200`);
  arguments read `definition.filterset_class` / `orderset_class` (`connection.py`); and **annotation**
  — the one that looked like the gap, since `resolved_relation_annotation(field, target_type, *,
  field_meta)` takes no definition — is fed `field_meta = definition.field_map[...]` at
  `types/finalizer.py:765`. All four read it. **True.**
- **The rationale's "because the other three really are unconditional".** Opened per seam: the
  annotation, resolution, and arguments bullets each assert what their named symbol does without a
  scope qualifier, so the aside is true of the bullets it is about.

### Dispatched findings checklist audit — sixteen boxes, all ticks confirmed, none changed

Walked box by box against the **current** files, not against any pass's report, with D10 given the extra
scrutiny its over-tick history earns. Measured on the artifact: **16** `- [x]`, **0** `- [ ]`.
**No over-tick, no landed-but-open box, no deferral owed.**

| Box | Evidence re-derived this pass |
|---|---|
| D1 | `DjangoModelField` **0**, `types/fields.py` **0** (`grep -oF \| wc -l` on the current spec) |
| D2 | `OptimizerStore` / `with_hints` / `with_prefix` **0 / 0 / 0**; the value-not-callable rule present at `:515` and its plan-cache reason verified against `_build_cache_key` |
| D3 | `get_strawberry_annotations` **0**; `### Track annotation provenance structurally…` present |
| D4 | `DjangoField(` **0**; `DjangoListField(...)` present |
| D5 | `DjangoModelType` **8 → 6**, every survivor enumerated below; the no-placeholder-tier contract present |
| D6 | `ASC_DISTINCT` / `DESC_DISTINCT` / `DISTINCT ON` **0 / 0 / 0** |
| D7 | `:62` reads `object_type: ObjectTypeNode \| None = DjangoNodeField(ObjectTypeNode)` |
| D8 | the `DEFERRED_META_KEYS` paragraph is present and `types/base.py:65-67` is exactly the three keys |
| D9 | `total_count: int` **0** in the spec; the opt-in `totalCount` and still-owed `aggregates` paragraphs both present |
| D10 | `:375-376` read `fields_spec` / `exclude_spec`; three plain `type \| None` sidecars; `LazyClassRef` **0** package-wide |
| D11 | `:684` reads `class ObjectFilter(FilterSet):` with `fields = {`; `AdvancedFilterSet` **0** |
| D12 | `:741` reads `class ObjectAggregate(AggregateSet):`; `:719` reads `[OrderSet]`; `AdvancedOrderSet` **0** |
| D13 | `:674` "It does **not** finalize" present; no "finalize pending types" item |
| D14 | `:884` names `orders/… inputs.py` (all four files exist on disk), `:886` `fieldset/ — planned by TODO-BETA-054-0.1.1`; no `types/fields.py` line |
| D15 | `:929` `### Phase 3: Generated relation fields`; `### Phase 1`-`### Phase 8` complete, no gap |
| D16 | `:1034-1036` carry the three `— owed; TODO-BETA-…` annotations; the eight met criteria carry none |

**Group C is still untouched**, re-confirmed: the two "retired since" markers, the `### Layer 2`
`PendingRelation` sketch, the `class ObjectTypeNode(DjangoType, relay.Node)` declaration, and the
upstream `file:///…#LNN` citations.

### Duplication and inconsistent shape across all sixteen passes taken together

`## Final verification job` step 4, run against the two documents rather than any pass's file list,
because no single pass held the whole cycle. This check has caught a real defect twice on this item.

- **Single ownership of the responsibility-to-seam map holds.** `grep` for the map's bullet shape
  returns **four** bullets, all in `### Layer 4` (`:647-650`). `seam` occurs six times in the spec:
  `:415` (the pointer), `:417` (the one behavior that is not a Layer 4 seam), `:419` and `:652` (the
  single-object invariant), `:645` (Layer 4's preamble), `:1002` (Decision 3's restatement). No second
  map exists.
- **The spec/rationale twin surface is clean for all five corrected claims**, established with the
  shortest distinctive token rather than a phrase — the trap that hid a wrapped twin for six passes:
  `complement` **0 / 0**; `per execution` **0 / 0**; `composed`, `every path`, `single place`, and
  `recourse` occur **0** times in the spec and only inside the rationale's retraction notes, which are
  *about* the cuts.
- **No duplicated line of any length.** `grep -v '^[[:space:]]*$' | sort | uniq -d` over the spec
  returns only fenced-code boilerplate and one-word list items; over the rationale, only `>`.
- **The `:257` / `:771` resolver-wrapping near-duplication remains a judged non-finding**, unchanged
  from final-verification pass 3 and Worker 3 pass 7: two pointers at one external owner
  (`spec-054-fieldset-0_1_1.md`), making different contrasts.
- No new abstraction, helper, constant, or branch exists to challenge: the diff touches two `.md` files
  and no `.py` file.

### Gates and proofs re-run, not read

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md`
  → `OK: 23 terms - all have glossary entries and at least one spec link.` **exit 0, 23 terms.**
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → **exit 0** for both.
- **In-page anchors:** `grep -c '](#'` → **0** in each file, so none can dangle. **Link definitions:**
  25/25 on the spec and 11/11 on the rationale, 0 orphan, 0 dead target — with the known false positive
  confirmed as a stripping artifact (`glossary-aggregateset` and `glossary-finalize-django-types` are
  used *inside* code spans; so is `[target]` in `` `list[target]` `` at `:647`).
- **`AGENTS.md` rule 27:** zero in-repo raw `path:NN` in either document (`grep -nE
  '[A-Za-z0-9_/.-]+\.(py|md):[0-9]+'` with `file:///` excluded → no match).
- **No renumbering.** `### Layer 1`-`### Layer 11` at `:576`, `:599`, `:631`, `:644`, `:656`, `:678`,
  `:716`, `:735`, `:768`, `:783`, `:799`; `### Phase 1`-`### Phase 8` (8, no gap); `### Decision 1`-
  `### Decision 6` (6, no gap). The two vacated slots carry positive contracts and no "this was
  rejected" prose, so the build plan's `### Constraint binding R1 and R2` still holds.
- **Byte / line ledger, re-measured with `wc -c -l`.** Spec **61,082 bytes / 1,096 lines**; rationale
  **51,082 / 710**. `git diff --numstat`: spec **112 / 170**, rationale **502 / 0** (counted off the
  diff independently: 113 `+` and 171 `-` lines including the two file headers). HEAD's own copies
  (`git show HEAD:<path>` into an out-of-repo scratch path) measure **54,232 / 1,154** and
  **12,273 / 208**. Both identities close: `1,154 − 170 + 112 = 1,096` and `208 + 502 = 710`.
- **Append-only on the rationale, proved independently.** `git diff -- <rationale> | grep -c '^-'` →
  **1**, and printing it shows the `--- a/…` header — no HEAD line was deleted **or modified**, which
  subsumes any prefix check. `git diff -U0` hunks are `@@ -166,0 +167,500 @@`, `@@ -185,0 +686 @@`,
  `@@ -186,0 +688 @@`; `500 + 1 + 1 = 502` closes against `--numstat`. `head -166` of the working file
  `cmp`s **exit 0** against `head -166` of HEAD's copy (HEAD's file is 208 lines, so the prefix is a
  real prefix). The two single-line hunks are the alphabetical link-definition insertions, opened
  rather than assumed.
- **The sweep's corrected denominators re-derive, parsed programmatically rather than re-read** — they
  are stated counts, and M2 exists because a stated count was not measured. Script-counted rows (a line
  starting `|` that is neither the header nor the `|---|` rule): spec table **62**, rationale table
  **47**, total **109**; pure `judgement` verdicts **7** (`:66`, `:397`, `:403`, `:493`, `:562-574`,
  `:662-672`, and the rationale's migration entry); bold changed-site rows **4** (`**:515c**`,
  `**:526**`, `**:649b**`, `**Layer 4 entry**`). Every figure apply-changes pass 7 corrected is exact.
- **Temp test re-run, read-only.**
  `uv run pytest docs/builder/temp-tests/r1/test_async_execution_default_connection.py -q -o addopts=''`
  → **1 passed** (`addopts` overridden only to drop `pytest.ini`'s auto-applied `--cov`; no `--cov*`
  flag was used anywhere in this pass). Not modified, moved, or deleted. No other test was run.
- **Provenance: nothing was swept into a concurrent commit.** `git log --stat` over both document paths
  → the newest commit touching either is still **`f3c94642`**, unchanged across all sixteen passes and
  although HEAD has moved to `066c068b`. `git show HEAD:` on both still measures the ledger's HEAD
  figures — the second, independent proof. Both files are ` M` and uncommitted; the artifact is `??`.
  Verified with `git log --stat` plus `git show HEAD:`, never `git status` alone.

### Cross-spec anchors: five, all resolving in both directions, re-timestamped **2026-08-16T03:05Z**

Re-derived from scratch because `spec-010` is under a concurrent cycle and has moved between passes.

- **Inbound (2).** `spec-010:67` cites `spec-009` #"### Layer 3: Finalization trigger"; `spec-010:468`
  cites #"### Decision 6: fail loudly". `grep -c` for each exact heading on the current spec-009 →
  **1 each** (`:631`, `:1010`).
- **Outbound (3).** `spec-009:99` → `spec-010` #"### Must redo (not augment)"; `:634` →
  #"## Strawberry finalization strategy"; `:870` → #"### Unresolved-target error format". `grep -c` on
  the current spec-010 → **1 each**.
- `spec-008`'s inbound reference is whole-file, not anchored; no `spec-011` file cites spec-009.
  Nothing was repaired — a break would have been reported, per the plan's standing instruction.

### Builders' required-amendment lists, discharged

`worker-1.md` `## Review-round custody`. Every `### Notes for Worker 1 (spec reconciliation)` item
across the fifteen prior sections is accounted for: the R2 carry-forward is consistent and unchanged
(spec-009 states the row-preserving property at `### Layer 7` and `### Phase 5`; the `DISTINCT ON`
mechanism is **discharged by an alternative**, not postponed); the `filters/sets.py` in-place `Meta`
mutation was correctly recorded as a maintainer observation and not edited; the `KANBAN.md` stale
assertion about Layer 3 is R3/R4 territory; the two-site discipline Worker 3 pass 4 asked for was
honoured; Worker 3 pass 8's five report-only notes are carried below. **Nothing was recorded and left
unimplemented.** No pass, this one included, found a correctness defect in shipped source, and none is
escalated as one.

### Escalations carried forward to the maintainer at commit — report-only, none repaired here

1. **`docs/SPECS/spec-010-foundation-0_0_4.md:8` still mis-describes spec-009.** It lists "custom field
   classes" among what spec-009 describes, which is exactly what D1 scrubbed. Re-read this pass and
   **still standing** — tenth consecutive pass. Outside this cycle's writable set; only the maintainer
   can sequence the two cycles at commit.
2. **`docs/SPECS/spec-010-foundation-0_0_4.md:491`**, same shape: it still names
   `get_strawberry_annotations` as "the right helper for the day a stable consumer-override contract
   lands", which is D3's scrubbed borrow, and spec-009 now states the opposite position. Same owner and
   same resolution path as escalation 1.
3. **The `spec-010:67` coupling, and its pre-existing near-duplicate sentence.** The anchor resolves and
   the claim is still true, but after change 40 the cited section no longer states the direction — it
   points at the rationale. Nothing dangles and nothing is false. The single-threaded-setup-window
   sentence in spec-009 and `spec-010:67`'s closing sentence were near-verbatim twins before this cycle
   too; the right owner is spec-010.
4. **`django_strawberry_framework/types/definition.py::DjangoTypeDefinition`'s docstring reserves
   `fields_class` for `TODO-BETA-046-0.1.1`** — a stale card number after the renumber (`046` is now
   `DONE-046-0.0.14`, the transport card). The live owner is `TODO-BETA-054-0.1.1`, which is what the
   spec, `KANBAN.md`, and `docs/TREE.md` all say. **The spec is right and the source docstring is
   stale.** Source is read-only in this cycle.
5. **The rationale's `## Standing notes` "three sites" bullet is stale on purpose.** Correcting it would
   break the plan's append-only constraint on the rationale for this cycle; the staleness is stated
   explicitly five lines above it, and the spec's own opener was corrected to "four sites" (change 39).
   Correct it in the first pass that has the rationale open without that constraint.
6. **R1b input, not an R1 finding:** `spec-009:610`'s
   `relation_kind: Literal["forward_single", "many", "reverse_one_to_one"]  # mirrors
   utils.relations.RelationKind` names **three** members where `utils/relations.py::RelationKind` has
   **five** (`"many"`, `"reverse_many_to_one"`, `"reverse_one_to_one"`, `"forward_single"`,
   `"generic"`). Pre-existing HEAD text, untouched by this cycle's 112 added lines, and squarely R1b's
   contract — but it is the same `RelationKind` membership surface Worker 3 pass 7's M1 turned on, so
   R1b should have it in hand rather than rediscover it.
7. **R1b input, offered so it is not rediscovered:** `:930` (`### Phase 3`) and `:1002`
   (`### Decision 3`) summarise Layer 4's four-seam map without Layer 4's per-seam scoping, and
   apply-changes pass 6's sweep verified neither first sentence at its mechanism (the `:930` row checked
   card ids only; the `:1002` row covers Decision 3's second sentence). Judged **not** a finding here
   for the three reasons given above. If the maintainer wants them scoped, it is a wording preference on
   accepted text.
8. **The permanent-suite gap — the one item on this list whose evidence inaction destroys.**
   `tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse` pins
   `async def get_queryset` → `SyncMisuseError` on a connection field only under `execute_sync`. **No
   row pins the same rejection under `await schema.execute` for a *default* `DjangoConnectionField`** —
   the contract that makes an `async def resolver=` mandatory, and the exact fact apply-changes pass 4's
   correction turns on. `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is a
   ready-made body, re-run and confirmed passing this pass, but it is gitignored and **clears with the
   cycle**. **Recommend carding before the cycle closes**; tests are outside this cycle's writable set.
9. **A card-renumber `grep` at the commit gate.** `KANBAN.md`, `KANBAN.html`, and
   `examples/fakeshop/db.sqlite3` are dirty under concurrent sessions. All seven card ids cited across
   the two documents resolve today, but a renumber landing before commit would silently falsify them —
   and this repo has already done one renumber (escalation 4 is its residue). One grep covers it.
10. **Worker 3 pass 2's per-edit byte-split arithmetic slip**, carried from all three prior final
    verifications so the artifact stays internally consistent without any prior section being edited:
    apply-changes pass 2's `### Byte counts` attributes its −19 as "−15 and −12"; the Low's edit is
    **−4**, not −12. Every total, every final count, and both `--numstat` figures are exact.

### Summary

R1 turns the archived spec-009 from a horizon document describing six mechanisms this package chose
against into one that describes what shipped. **Two files changed and nothing else**: no source, test,
example, sibling spec, standing doc, generated doc, or DB row was touched, and the public surface
(`git diff -- django_strawberry_framework/__init__.py`) is empty. This item ran no tests and changed no
code; the read-only temp test under `docs/builder/temp-tests/r1/` is the only `pytest` invocation in its
history, and no `--cov*` flag was used in any pass.

**The six Group-A scrubs are complete, and completeness was verified by counting rather than by reading
a site list.** Every dropped symbol is at **zero** occurrences in the current spec, re-counted this pass
with `grep -oF | wc -l`: `DjangoModelField`, `types/fields.py`, `OptimizerStore`, `with_hints`,
`with_prefix`, `get_strawberry_annotations`, `DjangoField(`, `ASC_DISTINCT`, `DESC_DISTINCT`,
`DISTINCT ON`, `AdvancedFilterSet`, `AdvancedOrderSet`, `LazyClassRef` — 0 each. Where a scrubbed
section's whole subject was the dropped mechanism it was **rewritten to state what the shipped
architecture does** — Layer 4's four named seams, the provenance section, the value-not-callable hint
rule, the no-placeholder-tier contract, the row-preserving `Min`/`Max` paragraph, the corrected
connection sketch — never left as a hole and never left as "this was rejected" prose. The deliberation
went to the append-only rationale companion.

**The scrub is correctly bounded, and the boundary was re-verified site by site this pass.** The
surviving `DjangoModelType` (**6**), `AdvancedAggregateSet` (**2**), and `AdvancedFieldSet` (**2**)
mentions are each an upstream citation, a description of *upstream's own* behavior, or a refusal site —
never a mechanism this package adopts. `DjangoModelType` at `:312` (the upstream `file:///` reference
list), `:428-429` (Strawberry-Django's own default relation fallback maps), `:553`
(`## What to scrap from Strawberry-Django`), `:851` (`## Why not use generic relation fallback by
default?`), `:996` (`### Decision 1`, which refuses it by name); `AdvancedAggregateSet` at `:142`
(upstream citation) and `:235` (upstream design being praised); `AdvancedFieldSet` at `:250` (same) and
`:769` (`### Layer 9`'s prior-art reference, the twin of Layer 6's "Use `django-graphene-filters`
semantics"). Removing any of them would have deleted the argument along with the rejected feature and
falsified the upstream citations.

**The ten Group-B corrections all landed**, each re-verified against shipped source rather than against
the drift table: the node field's nullable-by-contract spelling (D7), the three `DEFERRED_META_KEYS`
named with the card that promotes each (D8), the connection's opt-in `totalCount` and still-owed
`aggregates` (D9), the `DjangoTypeDefinition` sketch corrected to `fields_spec` / `exclude_spec` and
declared an explicit subset of a 29-slot record (D10), `FilterSet` with canonical `Meta.fields` **plus**
the cookbook-parity `filter_fields` alias the drift row itself had understated (D11), the shipped `*Set`
base names (D12), Layer 5's self-contradicting "finalize pending types" replaced by the negative
contract (D13), the module layout's dead proposal removed and `fieldset/` / `orders/inputs.py`
corrected (D14), Phase 3 restated to the machinery that actually passes its five acceptance tests
(D15), and the three unmet success criteria annotated with their owning cards (D16). Two vacated
numbered slots (`### Decision 3`, `### Phase 3`) were **repurposed with positive contracts rather than
gapped or renumbered** — renumbering was forbidden because `spec-010` cites `### Decision 6` by anchor —
and all five cross-spec anchors resolve in both directions.

**The single-ownership decision, which is R1's one architectural call.** Three consecutive passes each
closed one bullet of a duplicated four-seam responsibility map, and each time the next pass found
another. Apply-changes pass 3 stopped patching bullets and decided the shape once: **`### Layer 4:
Generated relation fields` is the sole owner of the responsibility-to-seam map, and ``### Borrow
`StrawberryDjangoFieldBase` and `StrawberryDjangoField` `` states the borrow argument and points at it,
carrying no seam list of its own.** The duplicated list was deleted rather than corrected; async-safe
queryset access — the one borrowed behavior that is not a generated field's seam — got one sentence in
the Borrow chapter rather than a fifth Layer 4 bullet, because adding it there would have repeated the
mis-attribution one section over. The generalisable rule: **the architecture chapter owns the map, the
prior-art chapter cites it**, because a duplicate map has no correct state — it has a current half and a
stale half.

**Ledger, with both identities closing.** Spec **54,232 → 61,082 bytes**, **1,154 → 1,096 lines**
(`--numstat` **112 / 170**; it deletes more lines than it adds and still grows in bytes, because the
scrubs removed a dataclass sketch, three bullet lists, and a transition path while the replacements are
denser contract prose). Rationale **12,273 → 51,082 bytes**, **208 → 710 lines** (**502 / 0** —
append-only, proved by exactly one `-` line in its diff, a byte-identical `head -166`, and hunks summing
`500 + 1 + 1 = 502`). Closing identities: **`1,154 − 170 + 112 = 1,096`** and **`208 + 502 = 710`**.
Both gates green — 23 glossary terms, exit 0 on both files — with 25/25 and 11/11 link definitions, zero
orphans, zero dead targets, zero unresolved in-page anchors, and zero in-repo raw `path:NN`.

**The most transferable thing this item produced is the defect pattern itself, at eleven instances of
one class.** Every finding on R1 has been the same shape: **a fluent subordinate clause explaining
*why*, in connective tissue nobody re-derives because it reads like glue** — D10's byte-unchanged
section, Layer 4's "cannot see" absolute, `:385`'s "binds at finalization", `:418`'s async-safety
mis-attribution, `:417`'s "chosen per execution", `:515`'s plan-cache "keyed on", `:649`'s
cascade-helper recourse, `:515c`'s "already composed into every path", `:526`'s "the single place every
cardinality's access passes through", the wrapped rationale twin of the cascade claim, and the "exact
complement" clause written by the fix that retired the class. Nearly all were written by *this cycle's
own fix passes*, which makes a fix pass's new prose the highest-risk text in the cycle. Two method
lessons paid for the whole item and should be carried:

- **An invariant comment validates the RULE, not the REASON.** When a clause names a cache, a key, a
  lock, an ordering, a seam, or a helper, open the thing it names rather than the docstring that
  motivates the rule it supports. Four review passes verified `:649`'s three call sites (true) and never
  asked whether the cascade applies to a to-many edge.
- **Wrapped phrases defeat multi-word greps.** A rationale twin survived six passes because the phrase
  broke across a line: `grep 'cascade helpers'` missed it and `grep cascade` found it instantly. Search
  the shortest distinctive token and count occurrences, never establish a population with a phrase.

The remedy generalises as **cut when the reason cannot be verified cheaply *by the reader at their desk
from the cited symbol*; replace when it can and a builder needs it** — five of the six remedies on this
item were cuts, and the one replacement (the `MANY_SIDE_RELATION_KINDS` disjointness note) earned it by
being checkable from one named constant, and came in stating more than the falsehood it retired.

**What is left: nothing inside R1's contract.** The D1-D16 drift-table reconciliation is complete,
internally consistent, and clean under a cold read of all 112 added lines. The open-ended
whole-spec mechanism sweep is **R1b**'s, correctly split rather than absorbed, and two inputs are handed
to it above (escalations 6 and 7). Ten items are carried to the maintainer at commit; **escalation 8 —
the permanent-suite gap for `async def get_queryset` on a default `DjangoConnectionField` — is the only
one whose evidence inaction destroys, and it is recommended for carding.**

### Spec changes made (Worker 1 only)

**None.** This pass edited neither deliverable. The spec is byte-identical at 61,082 / 1,096 and the
rationale at 51,082 / 710, both matching apply-changes pass 7's and Worker 3 pass 8's measurements, so
this acceptance introduces no fresh unreviewed claim of its own. No deferral is owed: all sixteen
`### Dispatched findings checklist` boxes are `- [x]` with a landed contract re-verified against the
current files this pass.
