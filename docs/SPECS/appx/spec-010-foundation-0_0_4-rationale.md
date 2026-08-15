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

- **One entry per spec section**, named by the section's own heading. A section with no entry here
  lost nothing to this pass — that is not an omission.
- **This is a change record, not a full rationale extraction.** Spec-010 was authored as an
  implementation contract and states its decisions directly, so it carried little deliberation to
  cut. What it did carry, and what this file holds, is one retired section plus the record of a
  citation convention that stopped being true.
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
  spec-010 was changed, and nothing in the package was edited on its account.

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
