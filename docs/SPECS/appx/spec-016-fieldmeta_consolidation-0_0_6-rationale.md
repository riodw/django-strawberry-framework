# Rationale: spec-016 — FieldMeta single-source-of-truth consolidation and mirror retirement (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-016-fieldmeta_consolidation-0_0_6.md`][spec-016]. The spec is the
contract and states only what holds at `HEAD`; everything that explains **how it got there** lives
here: which two commits the card shipped, where its deliberation was actually written down and why
that place was never the spec, why three of the seven reader sites it named were already stale on the
day the card shipped, what the two bounded exceptions to the single-source rule buy and cost, why the
free relation classifiers are deliberately still called on raw Django descriptors, and every claim
the spec once made and may no longer make.

## Provenance of this record — a reconstruction, not a move

**This file was reconstructed from history. It is NOT the product of a
[`BUILD.md`][build] `## Spec rationale extraction` move, because spec-016 had no deliberative layer
to cut.** The distinction matters and is stated first so no later reader mistakes recovered material
for relocated material. The spec was a 4,558-byte card snapshot: `## Card snapshot`, a one-word
`## Planning note`, `## Scope`, `## Why it matters`, and an eleven-bullet `## Other` dumping ground.
It carried no numbered Decision, no slice checklist, no test plan, and no rejected alternative. There
was nothing to move out of it that a reader would recognize as deliberation.

The deliberation for this card **does** exist — it was simply written somewhere else, and this file
is the first document to key it to the spec. Recovered from four sources, each cited at the entry
that uses it:

1. **`BETTER.md` item 35** at `de35a622^` — the pre-implementation proposal, with the scoring, the
   two-part decomposition, the seven named sites, and the "why it matters" argument the spec's
   summary bullets were condensed from. `BETTER.md` was renamed to `BACKLOG.md` at `40c1855f`
   (2026-05-20), five days after the card shipped.
2. **The eight retired `TODO(spec-fieldmeta-*)` source anchors** at `de35a622^` — the in-source
   staging record, including the compatibility reasoning that justified keeping the mirrors for part
   of the `0.0.x` line before retiring them.
3. **The two shipping commits**, `de35a622` and `2bd7cb84`, read by `git show`.
4. **The later commits that reshaped the shipped sites** — `f83bb71b`, `36da25b4`, `991d5120` —
   which is why three of the spec's seven site names could no longer be found at `HEAD`.

**What this pass genuinely MOVED out of the spec** (cut, not copied; it exists here and nowhere
else):

- the whole preamble paragraph beginning "This file is intentionally lightweight";
- the whole `## Planning note` section, heading plus its one-word body;
- the deliberative bullets of `## Other` — the `BETTER.md`-graduation precedent bullet and the
  drift-surface argument bullet.

**Added to the spec in exchange:** a one-line pointer sentence in the preamble's slot naming what
lives here, plus its `[spec-016-rationale]` link definition under `<!-- docs/SPECS/ -->`.

**Deleted outright rather than moved**, per [`worker-1.md`][worker-1] rule 2, because the current
contract falsifies them: the `## Other` heading and its remaining nine bullets, the seven colon-form
source references, the three stale site names, the `~7 sites` tilde, and the sentence "Existing tests
pass without modification". Each is recorded below as a claim the spec may no longer make; none is
restored anywhere as live text.

**No fenced code block was involved.** The spec carried zero before this pass and carries zero after.

**Byte counts, measured:** spec 4,558 bytes before this pass, 8,953 after. The spec grew, and that is
the intended direction here: the stub omitted contract — the current reader sites, the two bounded
exceptions, the change population — and a contract a reader cannot check against the tree is the
defect this cycle was opened to fix. The [`BUILD.md`][build] corpus ratchet binds the workflow
corpus, not a spec.

## How to read this file

- **One entry per spec section**, named by that section's own heading and linked to its anchor. A
  section with no entry here lost nothing.
- **This spec has no numbered Decisions**, so the key is the heading. Two entries key to headings the
  reconciliation removed; each says so and anchors the section its subject now bears on.
- **The stub shape and its boilerplate preamble are argued once, elsewhere, and not retold here.**
  [`spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md`][spec-007-rationale]
  `### The preamble — the stub's own justification, and an instruction that cannot be followed`
  weighs expand-it / delete-it / keep-and-reconcile against constraints verifiable at `HEAD`, and
  names spec-016 among the seven archived stubs carrying the identical paragraph, at its measured
  4,558 bytes. That argument applies here unchanged and is cross-referenced rather than repeated;
  [`spec-011`][spec-011-rationale], [`spec-012`][spec-012-rationale], and
  [`spec-013`][spec-013-rationale] applied the same disposition in the three preceding residual
  cycles, and this file follows them.
- **Every fact below was measured at this working tree, not restated.** Each commit, count, and
  quotation carries the command or blob it came from. Where a figure in this cycle's build plan
  disagreed with the measurement, the measurement is recorded and the disagreement is named — three
  such disagreements are recorded, in `## What the card actually did`, `### ## Scope — the reader-site
  list`, and `### ## Change population`.
- **Where a change was made by a commit whose message states no reasoning, the entry names the commit
  and stops.** Where this pass supplies reasoning of its own it is labelled as this pass's argument
  against constraints verifiable at `HEAD`, never as a recovered discussion.
- **The move and the reconciliation are one pass**, so this file carries both records: the entries
  keyed to the spec first, then `## Reconciliation record`.

## What the card actually did — recovered, because the stub understates it

**Two commits, not one.** The spec's `## Other` named a single commit, `de35a62`. Measured:

- **`de35a622`** "refactor(types,optimizer): consolidate metadata onto DjangoTypeDefinition"
  (2026-05-15 22:26), 16 files, +403/-178 — the whole implementation. Six package source files, six
  test files, four per-cycle review documents under `docs/`.
- **`2bd7cb84`** "Refactor README.md and TODAY.md for clarity and structure" (2026-05-16 00:49) — the
  documentation and board half: it added the `CHANGELOG.md` entry, added the board card as
  `DONE-ALPHA-012-0.0.6`, and **deleted `BETTER.md` item 35**, which is the graduation the spec
  described. Its message names none of that.

*Disagreement named.* This cycle's build plan, `## Worker-0 verification pass`, states that
`de35a622` "is the card's whole implementation" and lists `CHANGELOG.md` among the files the spec's
list omits. Both readings are half right: `de35a622` is the whole *implementation*, and
`CHANGELOG.md` is not in its diff at all — `git show --name-only de35a622` returns 16 paths and none
of them is `CHANGELOG.md`. The CHANGELOG entry is `2bd7cb84`'s. The spec now names both commits.

**What the implementation retired, measured at `de35a622^`:**

- Two `ClassVar` declarations, `types/base.py:73-74`, and the two mirror writes at
  `types/base.py:144-145`. (`BETTER.md` item 35 named the writer as `types/base.py:137` — already
  drifted by seven lines when the proposal was written, which is the standing argument for
  [`AGENTS.md`][agents] rule 27's symbol-qualified form over line numbers.)
- Four mirror reads: `optimizer/walker.py:86` (`getattr(type_cls, "_optimizer_field_map", None)`),
  `optimizer/extension.py:356` (`hasattr(origin, "_optimizer_field_map")`),
  `optimizer/extension.py:619`, and the hints read the walker performed alongside the field-map read.
- **Eight** `# TODO(spec-fieldmeta-*)` comment anchors — measured as
  `git grep -o "# TODO(spec-fieldmeta" de35a622^ -- 'django_strawberry_framework/*.py' | wc -l` = 8,
  at `extension.py:351,615`, `walker.py:81,187`, `base.py:140,657`, `converters.py:229`,
  `resolvers.py:181`. Counting every occurrence of the bare token `spec-fieldmeta` in package `.py`
  files gives **13**: the eight anchors plus five prose cross-references inside the
  `optimizer/field_meta.py` module docstring, which the same commit rewrote. Both counts are stated
  because the spec's "All `TODO(spec-fieldmeta-*)` source anchors removed" is true of both and the
  numbers differ.

**What the implementation added:** the `FieldMeta.relation_kind` and `FieldMeta.is_many_side`
properties the consolidated readers consume, and `optimizer/walker.py::_resolve_optimizer_hints`.

## Entries keyed to the spec

### The preamble — boilerplate whose instruction is counterfactual

Bears on [Card snapshot][spec-016-card-snapshot], the section the paragraph introduced.

*Moved verbatim, the whole paragraph.* "This file is intentionally lightweight. It preserves the card
scope from the Kanban database so the card has a durable `SpecDoc` FK target and a stable repository
file. Before implementation work starts from this file, expand it into the full builder-format spec
described by `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`."

*Claim the spec no longer makes.* That implementation work may start from this file, and that the
file should be expanded into a full builder-format spec. Both are impossible here for the same reason
they are impossible in the six sibling stubs: the card's work shipped on 2026-05-15/16 and this file
was created on **2026-06-01** by `81e4704d` "docs: archive prior specs to docs/SPECS/ and renumber
per Step 8 pass" — sixteen days later, as a back-fill. There was never any implementation work to
start from it, and the expansion was never performed in this file or in any sibling.

*Why the first two sentences moved rather than stayed.* They explain why the file exists, which is
process justification and not a contract. They were also a duplicate: the `Status:` line already
carried "canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact", so the
identity survived one level up. The reconciliation then simplified that `Status:` line to `shipped`,
because the stub-identity clause is itself now the rationale's business and the line's job is to say
what state the work is in.

*The alternatives, and why keep-and-reconcile won.* Not re-argued — see
[`spec-007-…-rationale.md`][spec-007-rationale], which weighs expanding the stub (rejected: an
expansion after the fact could only be a reconstruction wearing the shape readers trust as a
pre-implementation contract), deleting the file (rejected, and mechanically refused — the fakeshop
kanban app will not keep a `done` card without a linked `SpecDoc`), and keeping the snapshot and
reconciling it when it drifts (what happened). Spec-016 is named in that entry's own list of seven.

### `## Planning note` — a retained field's discarded value

Bears on [Card snapshot][spec-016-card-snapshot].

*Moved verbatim, heading and body.* "## Planning note" / "shipped".

*Why it went.* It is not a sentence, it is not a planning note, and it duplicates the `Status:` line
one screen above it. It is a rendered board field whose value happened to be the word "shipped" —
the snapshot renderer emitted the heading because the field existed, not because it said anything. A
section whose entire content is a word already stated elsewhere is the cheapest kind of drift: there
is no way to tell whether it is current.

*Rejected alternative.* Reword it into a real planning note. Rejected: there is no planning to
record. No commit message, spec, or standing doc records any planning for this card beyond
`BETTER.md` item 35, which is recovered in full above and belongs here rather than under a heading
in the contract.

### `## Card snapshot` — the board fields are the database's

Bears on [Card snapshot][spec-016-card-snapshot].

*Claim the spec no longer makes, as live text.* The six board-metadata bullets — `Status: done / Done`,
`Milestone: alpha / Alpha (pre-0.1.0)`, `Priority: Medium`, `Relative size: M`, and the five-label
list `cleanup`, `field-meta`, `metadata`, `optimizer`, `types`.

*Why they went, and why this is a deletion rather than a move.* They are a **rendered copy of DB
rows**. [`BUILD.md`][build] `### Generated docs are DB-backed` makes `examples/fakeshop/db.sqlite3`
the source of truth for card metadata and `KANBAN.md` / `KANBAN.html` its renderings; a third
hand-maintained copy inside a spec has no mechanism keeping it true and no reader who should trust
it over the board. The identity bullets a reader needs to find the card — number, status, milestone —
are retained, in the one-line form [`spec-013`][spec-013-rationale] settled on. The spec now says
explicitly that it does not restate the rest.

*Not a falsification claim.* Unlike spec-013's label list, spec-016's five labels were **still
correct** at `HEAD` when this pass ran. They were removed for the structural reason above, not
because they had drifted. Recording that distinction is the point: the next reader should not infer
from the deletion that the board had changed.

### `## Scope` — the reader-site list was written before the implementation and never re-pointed

Bears on [Single source of truth][spec-016-ssot] and [Mirror retirement][spec-016-mirror].

*Claims the spec no longer makes.* All seven source references in their original form, and three of
the seven site names outright:

| The spec said | At `HEAD` | Cause |
|---|---|---|
| `types/base.py:_record_pending_relation` | **no such symbol** — `git grep "def _record_pending_relation"` at `HEAD` returns nothing; the canonical read is `types/base.py::_build_annotations` #"field_meta = field_map[snake_case(field.name)]" | `f83bb71b` "Run REVIEW.md;" (2026-05-20) deleted the helper and inlined its body into the annotation loop |
| `types/converters.py:resolved_relation_annotation` | true, but the **canonical read moved upstream** — `resolved_relation_annotation` now takes a keyword-only `field_meta` and the read is `types/finalizer.py::finalize_django_types` | `f83bb71b`, the same commit: it removed the second, eager-bind call path in `types/base.py` and made the surviving finalizer call pass the canonical value explicitly |
| `optimizer/walker.py:_walk_selections` (hints read) | the read is `optimizer/walker.py::_resolve_optimizer_hints`, called by `_walk_selections` and injected into `optimizer/nested_planner.py` | **stale on the day it shipped**: `de35a622` itself created the helper at `walker.py:88`. `36da25b4` (2026-06-11) changed its parameter from `type_cls` to `definition`; `991d5120` "fix(optimizer): isolate nested planning" (2026-07-13) injected it into the nested planner |

*The third row is the load-bearing one, and it is a correction to this cycle's plan.* The build
plan's V5/F3 describe the hints read as "extracted into its own helper" later. Measured, it was not:
`git grep -n "_resolve_optimizer_hints" de35a622 -- django_strawberry_framework/optimizer/walker.py`
returns the definition at line 88 and the call at line 194 **in the shipping commit**. The site name
`_walk_selections (hints read)` was copied verbatim out of `BETTER.md` item 35 — a proposal written
against the pre-implementation code — and no pass ever re-pointed it at what the commit actually
built. That is a different and more instructive failure than post-hoc drift: **the spec never
described its own implementation, only the proposal for it.** The other two rows are genuine later
drift.

*Why the colon form went.* [`AGENTS.md`][agents] rule 27 requires `path::QualifiedName`,
`path::QualifiedName #"unique substring"`, or `path #"unique substring"`, and licenses raw
`path:NN` / `path:name` only in per-cycle scratchpads that close with their cycle. An archived spec
is a standing doc. Seven references used the colon form; all seven are now symbol-qualified, and the
two `types/` reads and two `optimizer/` reads that needed line-level precision carry the
`#"substring"` form.

*One further correction the sweep produced.* The spec named
`optimizer/extension.py:check_schema`. Measured, `check_schema` is a `@staticmethod` on
`optimizer/extension.py::DjangoOptimizerExtension`, so the qualified name is
`optimizer/extension.py::DjangoOptimizerExtension.check_schema`. `BETTER.md` item 35, the
`CHANGELOG.md` entry, and this cycle's build plan all use the bare form; the spec now does not.

*Rejected alternative.* Keep the historical site names and add a note that they have moved.
Rejected: [`BUILD.md`][build] `## Spec rationale extraction` forbids the spec narrating its own
history, and a contract listing symbols that do not exist cannot be checked against the tree at all
— which is the concrete cost this cycle paid, since verifying "nothing was skipped" required
recovering three commits before a single claim could be tested.

### `## Scope` — "single source of truth" stated without its two bounded exceptions

Bears on [Bounded exceptions to the single-source rule][spec-016-exceptions].

*What the spec omitted.* Two documented, deliberate departures from the single-source rule:

- **The walker's dual contract.** `optimizer/walker.py::_resolve_field_map`
  #"DUAL CONTRACT (read before consuming the returned map)" returns `FieldMeta` values for a
  registered model and raw Django field objects from a `model._meta.get_fields()` walk for an
  unregistered one.
- **The test-double fallbacks.** `types/resolvers.py::_field_meta_for_resolver` falls back to
  `FieldMeta._from_field_shape(field, is_relation=True)` or `FieldMeta.from_django_field(field)`, and
  `types/converters.py::resolved_relation_annotation` re-derives when `field_meta is None`.

*Why the omission mattered enough to fix.* Both are reachable by grep and neither was mentioned, so
a reader auditing the code against the spec finds a second metadata shape and a re-derivation path
inside the very functions the spec cites as consolidated, with nothing to tell them whether they are
drift the audit should report or design the audit should pass. That is the failure mode this cycle
exists to close: an unstated exception makes an audit unresolvable, not merely incomplete.

*What each exception buys, and what it costs — this pass's reading of the sites, labelled as such.*
The walker's fallback buys the optimizer the ability to plan for a model with no registered
`DjangoType` at all, which is what keeps a partially-annotated schema working. It costs a typing
invariant: the map is `FieldMeta | Any`, so a reader must know which attributes are safe to reach for
before consuming a value. The site names its own exit condition —
`optimizer/walker.py::_resolve_field_map` #"registry-coverage gate lands" — so the exception is
explicitly provisional, and the spec states it as a current contract without inheriting that
promise. The
test-double fallbacks buy direct unit coverage of the cardinality branches without constructing a
registered type; they cost a re-derivation path that only stays honest because
`FieldMeta._from_field_shape` is the canonical builder's own shape helper, so the fallback produces
the value the canonical path would have produced on the same descriptor.

*Rejected alternative.* Close the exceptions instead of documenting them — make the walker's
fallback build `FieldMeta` objects, and delete the resolver fallbacks. Rejected for this cycle, on
two grounds. The walker's own docstring defers its closure to a named future gate, so closing it here
would pre-empt a scoped decision with a drive-by change; and both changes are production-code work on
a shipped card whose brief is that nothing was skipped, in a cycle whose one authorized source edit
is a docstring cross-reference. Recorded so the next round does not read the documentation as an
endorsement of the shapes being permanent.

### `### Bounded exceptions` — the dual contract was stated on a false premise, in both files

Bears on [Bounded exceptions to the single-source rule][spec-016-exceptions]. Added by this cycle's
second round, which corrected the source half; the spec half landed in the third.

*Claims neither the spec nor the source may make any longer.* Two, and they were the same claim
written twice:

- The spec said the two shapes "coexist safely **only because** every downstream read is
  `getattr(..., default)`".
- `optimizer/walker.py::_resolve_field_map`'s docstring said "Both shapes are read via
  `getattr(..., default)` downstream -- that defensive access is the **ONLY** reason the two coexist
  safely", and pointed the reader at a twin site said to carry "the same divergence (and the same
  `getattr`-defensive fallback)".

*Why they are false, measured.* Ten plain, non-`getattr` attribute reads of a value taken out of that
map exist in the walker — `related_model` six times, `is_relation` twice, `name` twice — so defensive
access is demonstrably not how every read happens, and therefore cannot be the only reason the shapes
coexist. The twin claim is false for a different reason:
`types/resolvers.py::_field_meta_for_resolver` is annotated `-> FieldMeta` and every one of its three
exits yields a `FieldMeta`, so it has no dual return shape at all and its consumers read attributes
with no defaults anywhere. What the two sites actually share is one **policy** — prefer the canonical
definition-backed metadata, fall back when it is unreachable — and neither the return shape nor the
read discipline.

*What both files say instead.* The invariant a consumer must obey, stated as a rule: `name` and
`is_relation` are guaranteed on both shapes by
`optimizer/field_meta.py::_DjangoFieldLike` #"``name`` and ``is_relation``; the remaining attributes"
and are read directly; any other attribute is read directly only where both shapes carry it; a `FieldMeta`-only
attribute is never read off the map without a `getattr(..., default)`. That rule, not a blanket
`getattr` discipline, is what makes the two shapes safe to coexist. The cross-reference now names the
asymmetry rather than asserting symmetry.

*Rejected alternative — publish a closed safe-list of the directly-readable attributes.* The obvious
repair was to name the three attributes actually read directly (`name`, `is_relation`,
`related_model`) and be done. Rejected, because `related_model` is 6 of the 10 direct reads and is
**not** guaranteed on the raw shape: `optimizer/field_meta.py::_DjangoFieldLike` deliberately
promises only `name` and `is_relation`, and the walker itself hedges that very attribute with
`getattr(django_field, "related_model", None)` a few lines below the docstring. A list naming it
would be contradicted by the module's own code, which is the same class of defect being fixed — a
confidently-stated absolute that the surrounding source falsifies. Stating the rule and naming only
the two guaranteed attributes covers all six `related_model` reads without asserting a guarantee that
does not exist.

*Rejected alternative — leave both texts as coarse-but-directionally-right prose.* Rejected. The
paragraph is labelled `DUAL CONTRACT (read before consuming the returned map)`, which is an
instruction to obey it; a false invariant is at its most expensive in the one place a reader is told
to rely on it. The decisive argument was narrower still: the corrected cross-reference sentence
*leans* on the false premise for its meaning, so leaving the premise standing would have extended the
imprecision rather than merely inheriting it.

*A citation deliberately left stale, recorded so it is not read as an oversight.*
`docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md` cites the deleted clause
#"ONLY reason the two coexist safely" and was **not** edited. It is a closed cycle's record of what
the source said at that cycle, and rewriting a historical quotation to track a later reword falsifies
the record it exists to preserve. A maintainer who prefers to re-point it should use
`optimizer/walker.py::_resolve_field_map` #"lets the two shapes coexist" — the greppable single-line
form, which is not the longer phrase, because the replacement's own line wrapping splits
`lets the two shapes coexist safely` across two lines.

### `## Why it matters` — the tilde, and the classifier-versus-FieldMeta confusion

Bears on [Out of scope][spec-016-out-of-scope] and [Why it matters][spec-016-why].

*Claim the spec no longer makes.* "~7 sites of duplicated relation-shape logic", and its companion
framing that the duplication was "re-deriving relation shape via `relation_kind(field)` + raw
`getattr(field, ...)`".

*Why the tilde had to go, and why the framing was actively misleading.* The number was never
approximate — it is exactly the seven sites `BETTER.md` item 35 enumerated, three SSoT plus four
mirror, and the spec listed all seven two sections above the tilde. A tilde in front of a figure the
same document enumerates reads as an estimate of an unmeasured population and invites the next
reader to re-measure it.

The framing is worse. Naming `relation_kind(field)` as the duplication makes the shared classifier
look like the thing this card retired, and at `HEAD` that classifier is still called on raw Django
descriptors at several sites **by design**. Measured with
`git grep -n "relation_kind(\|is_many_side_relation_kind(" HEAD -- django_strawberry_framework`:
`connection.py::_keyset_order_state`, `filters/sets.py::_relay_filter_class_for_field`,
`optimizer/join_taxonomy.py::classify_relation_join`, `optimizer/walker.py::plan_relation`,
`optimizer/walker.py::_apply_hint`, `utils/relations.py::classify_path`, and
`utils/relations.py::_lenient_traverses_to_many` — plus
`optimizer/field_meta.py::FieldMeta.relation_kind`,
`optimizer/field_meta.py::FieldMeta.is_many_side`, and
`optimizer/field_meta.py::FieldMeta._from_field_shape`, which are the two `FieldMeta` properties
delegating **to** the classifier and the canonical builder's shape helper. A reader who greps the classifier, finds seven raw-field
call sites, and reads the spec's framing concludes the consolidation was undone. It was not: those
sites classify descriptors they obtained outside any definition, which was never in scope.

*What the spec says instead.* The rule is now stated on the axis that actually distinguishes the two:
**where relation shape is needed for a field belonging to a registered `DjangoType`, read the
`FieldMeta` the definition already holds.** `## Out of scope` names the classifier calls explicitly
as correct and states that `FieldMeta.relation_kind` / `FieldMeta.is_many_side` delegate to
`utils/relations.py` rather than duplicating it.

*A change with a cause, recorded.* Those two properties did not always delegate. `de35a622` shipped
both as inlined branch ladders inside `FieldMeta`; a later DRY pass collapsed them onto the shared
classifier, so `FieldMeta.relation_kind` is now `return relation_kind(self)` and
`FieldMeta.is_many_side` is `return is_many_side_relation_kind(self.relation_kind)`. Same answers,
one implementation — and it is why the spec can now say the classifier is the single implementation
of the classification without contradicting the single-source claim about `FieldMeta`.

### `## Scope` and `## Other` — the file list was incomplete and the test claim was false

Bears on [Change population][spec-016-population].

*Claims the spec no longer makes.*

- The five-file list `types/base.py`, `types/converters.py`, `types/resolvers.py`,
  `optimizer/walker.py`, `optimizer/extension.py` as the change population. It omits
  **`optimizer/field_meta.py`** — where the `FieldMeta.relation_kind` / `is_many_side` properties the
  whole consolidation consumes were added, and where the retired anchor prose lived — and omits all
  **six test files** `de35a622` modified.
- **"Existing tests pass without modification."** Its own commit falsifies it:
  `git show --stat de35a622` records `tests/optimizer/test_walker.py` at +120/-… and
  `tests/types/test_resolvers.py` at +72, with four further test files changed. The sentence is
  false, not stale — it was untrue when written.

*Why it is worth recording rather than just fixing.* The false sentence is the specific hazard a
"pure internal refactor" claim carries. The refactor was invisible to consumers and highly visible
to tests, because the tests assert against the internal seams it moved. A future card reading
"existing tests pass without modification" as the precedent for a similar consolidation would budget
for none of that work.

*Rejected alternative.* Replace the sentence with "tests were updated". Rejected as still
uncheckable: the spec now names the six files and states why they changed, so the claim can be
re-derived from the commit.

### `## Other` — eleven bullets of five kinds under a heading that names none of them

Bears on [Change population][spec-016-population], [Why it matters][spec-016-why], and
[Compatibility][spec-016-compat].

*The heading and all eleven bullets are gone.* `## Other` was a rendered dumping ground for board
item-rows the snapshot generator had no home for. Sorted by kind, it held: two compatibility
statements, one commit reference, six file paths, the `BETTER.md`-graduation history, and two
argument bullets. Each is now either live contract in the section that owns it, or an entry in this
file, or deleted as falsified. Nothing is in two places.

*Moved here verbatim — the graduation precedent.* "Originally tracked as `BACKLOG.md` item 35
(\"`FieldMeta` single-source-of-truth consolidation and mirror retirement\"). Promoted to a DONE card
and removed from `BACKLOG.md` when the work shipped — per `BACKLOG.md`'s \"graduate into a
`KANBAN.md` card when scheduled\" workflow. This is the first `BACKLOG.md` item to graduate; the
precedent for shipped items: strike-through with SHIPPED status is fine while the item awaits a
release; once a release is imminent, move the item to a `KANBAN.md` `DONE` card and delete it from
`BACKLOG.md` so the strategic-differentiation file doesn't keep pointing at completed architecture
debt."

*Why it belongs here.* It is a process precedent about how the backlog file is maintained — a
statement about the repository's workflow, not about the shipped code. It is also the only surviving
record of that precedent, so deleting it would lose it.

*Two measured corrections to it, recorded rather than silently applied.* The file was named
**`BETTER.md`** at the time, not `BACKLOG.md`: `git cat-file -e de35a622^:BACKLOG.md` fails — the
path did not exist — while `de35a622^:BETTER.md` carries item 35 at lines 588-609. The rename to
`BACKLOG.md` happened at `40c1855f` "housekeeping: rename files" (2026-05-20), four days after the
graduation. And the removal was `2bd7cb84`'s, in the same commit that added the CHANGELOG entry and
the board card. The claim "the first `BACKLOG.md` item to graduate" is the card's own and **this pass
did not verify it**; it is recorded as the card's assertion, not as a measurement.

*Moved here verbatim — the drift-surface argument.* "The consolidation eliminates ~7 sites of
duplicated relation-shape logic and removes legacy class-attribute residue that previously survived
`registry.clear()`. Single source of truth for field metadata reduces drift surface whenever Django
adds a new relation flag or changes a descriptor attribute." Its substance is now stated as contract
in `## Why it matters` on the corrected axis, without the tilde and without the classifier framing;
the sentence itself is kept here as the record of the form the argument originally took.

*The `BETTER.md` argument the card never carried, recovered.* Item 35 gave the reason this card was
sequenced before the features that would consume it, and no version of the spec ever said it: "a
prerequisite for any future item that adds new relation kinds or new `FieldMeta` fields — would
amplify the drift surface if shipped without consolidating first." It also recorded why the two
halves shipped as one card — "Combined into one item because they share the same underlying intent
(one canonical metadata path through `DjangoTypeDefinition`)" — which is the rejected alternative of
splitting SSoT consolidation and mirror retirement into two cards, and the reason the split lost.
`## Why it matters` now carries the prerequisite argument as contract.

*The compatibility-window reasoning, recovered from the retired anchors.* The mirrors were not an
oversight; they were a deliberate compatibility hold. The anchor at `walker.py:81` read
"once the one-minor compatibility …", and the `field_meta.py` docstring at `de35a622^:22` stated the
mirror "remains for the 0.0.x line while the …". So the retirement's real decision was that the hold
had expired — the alternative being to carry the mirrors further into `0.0.x`, rejected because a
second store with no consistency enforcement is a correctness hazard rather than a compatibility
service, and because nothing supported ever read those private names. `## Why it matters` now states
the hazard; the window's existence is recorded only here.

### The `[backlog]` link definition — recorded, not fixed

Bears on the spec's link-definition block.

`[backlog]: ../../BACKLOG.md` sits under `<!-- Root -->` and no inline `[…][backlog]` use remains,
since the `## Other` bullet that mentioned `BACKLOG.md` mentioned it in backticks rather than as a
link and has moved here. The definition is **retained**, matching what
[`spec-013`][spec-013-rationale] settled for the identical residue in its own block: the path
resolves on disk, an unused definition breaks no render, and removing it in one sibling stub while
six others keep theirs trades a harmless wart for a divergence. Recorded here so a later sweep knows
it was seen and left, not missed.

## Reconciliation record — what the spec now says, and why

### The strategy, and the alternatives it rejected

The reconciliation had to make the spec checkable against `HEAD` without letting it narrate its own
history. Three approaches were weighed:

- **Point-fix the seven references and leave the structure.** Rejected. It fixes F2 and F3 and leaves
  the spec unable to answer the two questions a reader actually arrives with — what is canonical, and
  what are the exceptions — because the stub's `## Scope` was a list of sites with no rule stated
  above them.
- **Expand into a full builder-format spec.** Rejected, for the reason
  [`spec-007-…-rationale.md`][spec-007-rationale] gives at length and this file does not repeat: a
  post-hoc expansion presents inferred slices and decisions in the shape readers trust as a
  pre-implementation contract.
- **Restate `## Scope` as a rule plus its current sites, plus a named exceptions section and a named
  out-of-scope section.** Chosen. The card's real contract is one rule with two bounded carve-outs
  and one commonly-confused neighbour, and every reconciliation finding lands inside that shape:
  the site names become the rule's readers, the undocumented exceptions become a section, and the
  classifier confusion becomes `## Out of scope`.

### What changed, section by section

- **Preamble.** `Status:` simplified to `shipped`; the stub-justification paragraph replaced by the
  one-line pointer to this file.
- **`## Planning note`.** Removed.
- **`## Card snapshot`.** Six rendered board-metadata bullets collapsed to one identity line plus an
  explicit statement that the board owns the rest.
- **`## Scope`.** Restructured into four named subsections. `### Single source of truth` states the
  rule and lists all seven current reader sites, symbol-qualified.
  `### Bounded exceptions to the single-source rule` states the walker's dual contract and the
  test-double fallbacks as design. `### Mirror retirement` states the mirrors' absence as an
  invariant with the `registry.clear()` reason attached, and the anchors' absence.
  `### Out of scope` draws the `FieldMeta`-read versus raw-descriptor-classification line.
- **`## Why it matters`.** Rewritten to three reasons: drift surface, the two-store correctness
  hazard, and the prerequisite argument recovered from `BETTER.md` item 35. No tilde, no classifier
  framing.
- **`## Change population`** (new). Both commits, six source files, six test files, the standing docs,
  and the explicit correction that existing tests did not pass unmodified.
- **`## Compatibility`** (new heading over relocated `## Other` content). The two compatibility
  statements, plus the note that the retired attributes were private and undocumented.
- **`## Other`.** Removed.

### Verification of the move and the reconciliation

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md`
  -> `OK: 2 terms - all have glossary entries and at least one spec link.` Both linked anchors
  survive the rewrite: `[DjangoType][glossary-djangotype]` in `### Single source of truth` and
  `[relation shape][glossary-relation-handling]` in the same paragraph. The terms CSV needed no row:
  the reconciled body links exactly the two anchors it already carries.
- The spec has **no in-page anchors** and no cross-reference into moved text, so nothing dangles. The
  anchors this file links into the spec were checked against the reconciled headings.
- No surviving reference anywhere points into text this pass moved without naming this file.

### What this cycle deliberately did not fix

Recorded so a later sweep knows each was seen:

- ~~**`optimizer/walker.py::_resolve_field_map`'s dual-contract cross-reference points at
  `optimizer/resolvers.py`, a module that has never existed.**~~ **FIXED** by this cycle's second
  round, together with the false premise in the same paragraph; the reference reads
  `types/resolvers.py::_field_meta_for_resolver`, the one spelling the package's two already-correct
  sites use. This entry is kept rather than deleted because it records what the round was dispatched
  to do; the deliberation is under
  [`### Bounded exceptions` — the dual contract was stated on a false premise, in both files](#bounded-exceptions--the-dual-contract-was-stated-on-a-false-premise-in-both-files).
- **`tests/test_registry.py` carries a comment naming `_record_pending_relation`**, a symbol deleted
  at `f83bb71b`. Measured: `git grep -n "_record_pending_relation" HEAD` returns four paths —
  this spec (now fixed), `docs/SPECS/spec-010-foundation-0_0_4.md` (twice, where it is a historical
  reference in another card's spec),
  `tests/test_registry.py::test_finalize_discards_consumer_authored_pending_relation_without_rewriting_annotation`
  #"``FieldMeta.from_django_field`` and ``_record_pending_relation``", and the fakeshop DB. Tests are
  outside every round's writable set in this cycle.
- **`CHANGELOG.md` #"Consolidated field metadata onto" names this card by its pre-renumber id**,
  `012-fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement-0.0.6`, which
  `2bd7cb84` wrote as `DONE-ALPHA-012-0.0.6` before the board renumber made it 016. The same entry
  also carries the three stale site names and the bare `extension.check_schema`.
  [`AGENTS.md`][agents] rule 21 forbids `CHANGELOG.md` edits unless told, so no round in this cycle
  touches it.
- **The card's `CardItem` bodies in the fakeshop DB are a verbatim copy of the pre-reconciliation
  spec text**, colon-form references and the retired symbol name included. The archive-audit round
  ruled the restatement **not owed**: a card body is the board's record of what the card *said*, the
  spec is the contract, and the two are different artifacts serving different readers. Re-writing 26
  rows to match a spec they historically preceded would replace a faithful record with a
  retro-fitted one, churn a `db.sqlite3` two concurrent sessions share, and force a regenerate of
  three DB-backed docs — for no reader whose question the spec does not already answer. The condition
  that would change the answer is named: if a card body ever became the **only** statement of a
  contract, or if the board began rendering card bodies as current source references, restating them
  would become owed.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-007-rationale]: spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
[spec-011-rationale]: spec-011-stale_placeholder_cleanup-0_0_4-rationale.md
[spec-012-rationale]: spec-012-version_release_alignment-0_0_4-rationale.md
[spec-013-rationale]: spec-013-real_m2m_coverage-0_0_4-rationale.md
[spec-016]: ../spec-016-fieldmeta_consolidation-0_0_6.md
[spec-016-card-snapshot]: ../spec-016-fieldmeta_consolidation-0_0_6.md#card-snapshot
[spec-016-compat]: ../spec-016-fieldmeta_consolidation-0_0_6.md#compatibility
[spec-016-exceptions]: ../spec-016-fieldmeta_consolidation-0_0_6.md#bounded-exceptions-to-the-single-source-rule
[spec-016-mirror]: ../spec-016-fieldmeta_consolidation-0_0_6.md#mirror-retirement
[spec-016-out-of-scope]: ../spec-016-fieldmeta_consolidation-0_0_6.md#out-of-scope
[spec-016-population]: ../spec-016-fieldmeta_consolidation-0_0_6.md#change-population
[spec-016-ssot]: ../spec-016-fieldmeta_consolidation-0_0_6.md#single-source-of-truth
[spec-016-why]: ../spec-016-fieldmeta_consolidation-0_0_6.md#why-it-matters

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
