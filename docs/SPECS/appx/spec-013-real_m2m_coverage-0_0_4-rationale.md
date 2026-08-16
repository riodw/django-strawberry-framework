# Rationale: spec-013 — Real M2M coverage (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-013-real_m2m_coverage-0_0_4.md`][spec-013]. The spec is the contract
and states only what holds; everything that explains **how it got there** lives here: which five
fixture models and six relation edges the card retired, what its three commits actually did, where
the card's schema-shape test went and what replaced it, how the `library` app grew afterwards into
something far larger than the card's diff, and every claim the spec once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the work shipped, not before the build.** Card `DONE-013-0.0.4` shipped at
`0.0.4` across three commits on 2026-05-07, and the rule that gates a build on this move did not
exist then; this pass supplies it. Text marked *Moved* below was cut out of the spec, not copied: it
exists here and nowhere else.

## How to read this file

- **One entry per spec section**, named by the section's own heading and linked to its anchor. A
  section with no entry here lost nothing.
- **This spec has no numbered Decisions**, and it was never deliberated: it is a rendered snapshot of
  a Kanban card, created by the archive-and-renumber pass weeks after the work shipped. So the key is
  the heading, and two entries key to headings the reconciliation removed; each says so and anchors
  the section its subject bears on.
- **The stub shape, and the boilerplate preamble, are argued once and not retold here.**
  [`spec-007-…-rationale.md`][spec-007-rationale] `### The preamble — the stub's own justification,
  and an instruction that cannot be followed` weighs expand-it / delete-it / keep-and-reconcile
  against constraints verifiable at `HEAD`, and names this spec among the archived stubs carrying the
  identical paragraph. That argument applies here unchanged and is cross-referenced rather than
  repeated; this file records only what is specific to spec-013. The same disposition was applied by
  [`spec-011-…-rationale.md`][spec-011-rationale] and [`spec-012-…-rationale.md`][spec-012-rationale],
  the two preceding residual cycles.
- **The substance is therefore the change record.** [`BUILD.md`][build] requires each entry to carry
  the alternatives rejected, every change the claim has undergone with its cause, and any claim the
  section may no longer make. For this spec the deliverable is three findings plus the history the
  stub does not contain. The first is structural: **the stub's `## Scope` names nothing** — not a
  fixture, not a model, not a test — so no reader can check it against the tree without recovering
  three commits from history, which is exactly what this cycle had to do. The second is a relocation:
  **one of the card's own tests no longer exists where it was written**, having been replaced by a
  live HTTP twin. The third is dilution: **the `library` app the card created has since grown to more
  than double its original model count**, and a reader meeting today's `models.py` as "what card 013
  shipped" would credit this card with five later cards' substrate.
- **Every fact below was measured at this working tree, not restated.** Each commit, count, and
  quotation carries the command or blob it came from. Where a figure in this cycle's build plan
  disagreed with the measurement, the measurement is recorded and the disagreement is named.
- **The move and the reconciliation are one pass**, so this file carries both records: the entries
  keyed to the spec first, then `## Reconciliation record — what the spec now says, and why`.

## Provenance of this record

- **Moved** — cut from the spec by this pass, and now only here: the whole preamble paragraph
  beginning "This file is intentionally lightweight", and the whole `## Planning note` section
  (heading plus its one-word body). Both are quoted below inside the entries that dispose of them.
- **Added in exchange:** the paragraph's slot now carries the one-line pointer sentence naming what
  moved and where, plus its `[spec-013-rationale]` link definition under `<!-- docs/SPECS/ -->`.
- **Deleted outright rather than moved**, per [`worker-1.md`][worker-1] rule 2, because the current
  contract falsifies them: the `## Card snapshot` board-metadata bullets (the label list is wrong at
  `HEAD`), the `## Other` heading and its six bullets, and the past-tense framing of both `## Scope`
  bullets. Each deletion is recorded below as a claim the spec may no longer make; none is restored
  anywhere as live text.
- **No fenced code block was involved.** The spec carried zero before this pass and carries zero
  after.
- **The single glossary anchor changed carrier and survives.** `#relation-handling` was carried by
  `## Scope` bullet 2 as "[M2M traversal][glossary-relation-handling]"; the reconciled `## Scope`
  carries the identical link text on the sentence that states what the six edges are, where the
  cardinality catalogue is the subject. The ref-id `glossary-relation-handling` and its def are
  unchanged, the term string `M2M traversal` is preserved verbatim so the one-row
  `spec-013-…-terms.csv` still matches its `term` column, and
  `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md`
  exits 0 (`OK: 1 terms`) after the rewrite.

## What the card actually did — recovered, because the stub does not say

The stub names no commit. The card's diff was recovered by content search, and it is **three commits,
all 2026-05-07**, none of which carries the card id or the spec name in its message. Every stat below
is from `git show --stat --format='' <commit>`; every timestamp from
`git log --date=format:'%Y-%m-%d %H:%M'`.

| Commit | Time | What it did for this card |
|---|---|---|
| `73004d74` "Refactor tests a bit;" | 12:22 | Created the `library` example app at `examples/fakeshop/library/` — `models.py` (136 lines, 7 managed models), `migrations/0001_initial.py` (197 lines), `schema.py` (98), `apps.py`, `__init__.py` — registered it in the fakeshop settings and project schema, and added the first `examples/fakeshop/test_query/test_library_api.py` (227 lines). |
| `1057ddc2` "Complete spec-testing_shift.md;" | 13:08 | **The substitution itself.** Deleted `tests/fixtures/` — the unmanaged `tests_cardinality` app (`__init__.py`, `apps.py`, `cardinality_models.py`, `models.py`) — dropped it from `examples/fakeshop/settings.py`, and re-pointed both `test_definition_order.py` files plus `tests/types/test_definition_order_schema.py` at the real `library` models. |
| `67b07f79` "feat: Implement library app for real API testing in fakeshop project" | 13:50 | Expanded `test_library_api.py` to eight live tests (+239 lines), added two non-live library schema tests to `examples/fakeshop/tests/test_schema.py`, and updated `AGENTS.md` / `docs/TREE.md` / `test_query/README.md` for the new tier. Its own message states the card's scope verbatim: "Removed the test-only cardinality fixture app and integrated its functionality into the new library app." |

**The retired fixture set, named.** `git show 1057ddc2~1:tests/fixtures/cardinality_models.py` is 67
lines holding five `managed = False` models under `app_label = "tests_cardinality"`: `User`,
`Profile` (`OneToOneField` to `User`, `related_name="profile"`), `Author`, `Tag`, and `Book`
(`ForeignKey` to `Author` `related_name="books"`, `ManyToManyField` to `Tag` `related_name="books"`).
Its module docstring was "Unmanaged Django models covering relation cardinalities missing from
fakeshop." — which is the sentence the card set out to make false, by making the cardinalities
present in fakeshop.

The replacement is one-to-one on **cardinality**, never on name, and each right-hand edge was read
off `git show 73004d74:examples/fakeshop/library/models.py`:

| Retired fixture edge | Cardinality | Real `library` replacement |
|---|---|---|
| `Profile.user` | forward `OneToOneField` | `MembershipCard.patron` |
| `User.profile` | reverse `OneToOneField` | `Patron.card` |
| `Book.author` | forward `ForeignKey` | `Book.shelf` |
| `Author.books` | reverse `ForeignKey` | `Shelf.books` |
| `Book.tags` | forward `ManyToManyField` | `Book.genres` |
| `Tag.books` | reverse `ManyToManyField` | `Genre.books` |

**Why real managed models rather than better fixtures.** The retired app was `managed = False` under
a synthetic `app_label`, so it had no table, could not be seeded, and could not be reached from a
GraphQL request: it could only ever prove annotation shape, never resolution. That ceiling is what
made the substitution worth a card rather than a cleanup — the same six edges, once carried by
migrated tables in a real app, become reachable from the live `/graphql/` endpoint, which is where
[`AGENTS.md`][agents] rule 10 requires the coverage to be. The stub's `## Scope` records the
substitution and not one word of this, which is why a reader could not tell the card apart from a
rename.

### Nothing was skipped in the code

Re-derived at this working tree rather than accepted from this cycle's build plan
([`BUILD.md`][build] `## Claims are proven mechanically, never accepted on prose`). `HEAD` is
`973d00b2`. Three of the files below are dirty with a concurrent session's uncommitted work
(`examples/fakeshop/test_query/test_library_api.py`, `tests/types/test_definition_order.py`, and
`docs/GLOSSARY.md`), so each was read read-only via `git show HEAD:<path>` into a scratch path
outside the repository — never from the working tree, and never via `git stash` or `git checkout`.

- **V1 — the real managed app exists and is wired in.** `examples/fakeshop/apps/library/models.py`
  exists with its own `migrations/` package; `examples/fakeshop/config/settings.py`
  #"apps.library.apps.LibraryConfig" registers it.
- **V2 — the fixture app is gone.** `git ls-tree -r HEAD --name-only | grep -c "tests/fixtures/"`
  returns **0**. `grep -rn "tests_cardinality\|cardinality_models"` over the tree (excluding `.git`,
  `.venv`, and the binary `db.sqlite3`) returns **five** hits, all documentary: two in
  [`spec-011-…-rationale.md`][spec-011-rationale] and three in this cycle's own build plan. No source
  file, no test, and no standing doc names it. *(This cycle's build plan claims "zero hits outside
  `docs/builder/DONE/`"; the measured population is the five above and the plan's characterization is
  the one to distrust — the finding it supports, that no live surface references the fixture app, is
  unaffected.)*
- **V3 — every retired cardinality is carried by a real model.** The mapping table above, each
  right-hand edge re-read at `HEAD` from `examples/fakeshop/apps/library/models.py`.
- **V4 — package-level traversal coverage exists.**
  [`tests/types/test_definition_order.py`][test-types-definition-order]
  `::test_many_to_many_forward_and_reverse_relations_resolve` asserts
  `BookType.__annotations__["genres"] == list[GenreType]`,
  `GenreType.__annotations__["books"] == list[BookType]`,
  `ShelfType.__annotations__["books"] == list[BookType]`, and — in the same test —
  `BookType.__annotations__["shelf"] is ShelfType`, so the forward-FK half of the mapping is pinned
  there too. `::test_one_to_one_forward_and_reverse_relations_resolve` carries the O2O pair:
  `MembershipCardType.__annotations__["patron"] is PatronType` and
  `PatronType.__annotations__["card"] == (MembershipCardType | None)`.
- **V5 — package-level optimizer-planning coverage exists.**
  [`tests/optimizer/test_definition_order.py`][test-optimizer-definition-order]
  `::test_plan_relation_decisions_match_cardinality_after_finalization` asserts
  `plan_relation(Book.genres, GenreType) == ("prefetch", "default")` and the reverse `Genre.books`
  likewise, alongside `("select", "default")` for both halves of the O2O pair.
- **V6 — the eight live tests the card shipped all exist at `HEAD` by name.** Measured by diffing the
  `^def test_` list of `git show 67b07f79:examples/fakeshop/test_query/test_library_api.py` against
  the same list from `git show HEAD:<same path>`: `test_library_branch_shelf_book_loan_graph_over_http`,
  `…patron_card_and_genre_reverse_paths_over_http`, `…optimizer_selects_book_shelf_in_http_query`,
  `…reverse_fk_and_m2m_prefetch_sql_shape_over_http`,
  `…choice_enum_and_nullable_subtitle_are_deliberate_http_contracts`,
  `…consumer_prefetched_queryset_cooperates_with_optimizer_over_http`,
  `…optimizer_hints_are_observable_over_http`, `…relation_override_shapes_http_response_data`.
- **V7 — the M2M prefetch is pinned at the SQL level, not merely at the wire.** The literal
  `library_book_genres` — the join table's own name — occurs **6** times in the file at `HEAD`
  (`grep -c`), three of them inside card-013 tests: the reverse-FK/M2M prefetch-shape test, the
  consumer-prefetched-queryset test, and a filter test. A fallback to per-row N+1 queries could not
  produce that string, so the assertion pins the mechanism and not just the response body.
- **V8 — the card's two non-live schema tests exist, relocated.**
  [`examples/fakeshop/apps/library/tests/test_schema.py`][test-library-schema]
  `::test_project_schema_includes_library_types` (asserting `{"title", "shelf", "genres"}` is a
  subset of `BookType`'s field names) and `::test_library_djangotype_declaration_order_stays_awkward`.
  Both were written into the then-flat `examples/fakeshop/tests/test_schema.py` by `67b07f79` and
  moved by `31642c9c` "tests: relocate example app tests into per-app folders" (2026-05-29), the
  commit that created the per-app test tier [`AGENTS.md`][agents] rule 7 now codifies.

**No code defect was found, so this cycle dispatched no builder pass.** Nothing spec-013 promised is
absent at `HEAD`. The two live findings are both about the record: the spec did not name what it
delivered, and one delivered test now lives somewhere else — the entries below.

## Entries keyed to the spec

### The preamble — boilerplate whose instruction is counterfactual

Bears on [Card snapshot][spec-013-card-snapshot], the section the paragraph introduced.

*Moved verbatim, the whole paragraph.* "This file is intentionally lightweight. It preserves the card
scope from the Kanban database so the card has a durable `SpecDoc` FK target and a stable repository
file. Before implementation work starts from this file, expand it into the full builder-format spec
described by `docs/SPECS/NEXT.md` and `docs/builder/BUILD.md`."

*Claim the spec no longer makes.* That implementation work may start from this file, and that the
file should first be expanded into a full builder-format spec. The card's three commits landed on
2026-05-07 and this file was created by a later archive-and-renumber pass, so there was never any
implementation work for it to precede.

*Why the first two sentences moved rather than stayed.* They explain why the file exists, which is
process justification and not a contract about anything — and the spec's `Status:` line already says
the same thing one level up, in the line whose job it is. The three-way choice behind the stub shape
is [`spec-007-…-rationale.md`][spec-007-rationale]'s, cross-referenced above and not re-argued.

### `## Planning note` — a retained field's discarded value

Bears on [Card snapshot][spec-013-card-snapshot]; the section this entry keys to no longer exists.

*Moved verbatim, the whole section.* The heading `## Planning note` and its entire body, the single
word "shipped".

*Why it was removed rather than restated.* It renders one Kanban column, and the value it rendered is
a **status**, which the spec's `Status:` line already carries in the line whose job that is —
"Status: shipped". A section whose body duplicates a header line one screen above it is not a
contract; it is a render artifact. The planning-state dimension's own retirement is recorded in
[`spec-007-…-rationale.md`][spec-007-rationale]'s entry for the same section and is not repeated
here.

*Claim the spec no longer makes.* That the card carries a planning note.

### `## Card snapshot` — the board fields are the database's, and they had already drifted

Spec: [Card snapshot][spec-013-card-snapshot].

*Nothing moved; the board-metadata bullets were deleted.* The section claimed "Labels: `example-app`,
`m2m`, `tests`". The card carries **four** at `HEAD` — `example-app`, `internal`, `m2m`, `tests`
(read from [`KANBAN.md`][kanban] under `### [DONE-013-0.0.4 …]`). The extra label is `internal`, the
same dimension rebuild that falsified spec-012's two-label list; the divergence is therefore not
specific to this card but a property of hand-copying database rows into a file nothing re-renders.

*The drift is the argument, not an incidental defect.* A hand-copied render of database rows is wrong
the moment the board is edited, and nothing in the repository can detect it: [`KANBAN.md`][kanban]
regenerates from `examples/fakeshop/db.sqlite3`, the spec does not. So patching the label list to
read four labels lost — it buys correctness until the next board edit and owes the same patch again.
Deleting the section outright also lost: the card's identity is the one board fact a spec is entitled
to state, since this spec exists to be that card's `SpecDoc` target, and entries in this file resolve
to its anchor. The surviving two-bullet shape is [`spec-012-…-rationale.md`][spec-012-rationale]'s
and spec-011's, adopted unchanged.

*Claims the spec no longer makes.* That card 13 carries exactly the three labels `example-app`,
`m2m`, and `tests`; that it is Medium priority or relative size S. The latter two remain true in the
database and neither is the spec's to assert.

### `## Scope` — two summary bullets that name nothing

Spec: [Scope][spec-013-scope].

*Nothing moved; both bullets were rewritten.* The claims were "Replaced test-only M2M/cardinality
fixtures with real managed models in the `library` example app." and "Added package-level and
HTTP-level coverage for [M2M traversal][glossary-relation-handling] and optimizer planning."

*This is the cycle's central reconciliation, and the fault is that neither sentence is checkable.*
Both are true. Neither can be confirmed or refuted against the tree by anyone who does not already
know the answer: "test-only M2M/cardinality fixtures" names no file, no app label, and no model;
"real managed models" names none of the seven the card created; "package-level and HTTP-level
coverage" names not one test. The retired set is small and finite — five models, six edges, one
deleted directory — and so is the replacement, so the vagueness buys nothing. The practical cost is
measurable: establishing what this card did took three commit recoveries and a content search,
because the spec that exists to record it records only its own genre.

*The alternatives the rewrite rejected.*

- **Add the file list from `## Other` to `## Scope` and stop there.** Rejected: those four paths are
  a board *prediction* field, not the card's diff — see the `## Other` entry below — so promoting
  them would harden a wrong claim into the contract section.
- **Name the models but not the tests.** Rejected: the card's deliverable *is* coverage. A scope that
  names the substitution and not the assertions leaves the reader unable to check the half that
  matters, and it is the half a later refactor can silently remove — as one later commit in fact did,
  legitimately, to one of these tests.
- **Reconstruct a full builder-format spec** with slices, a test plan, and a definition of done.
  Rejected for the reason [`spec-007-…-rationale.md`][spec-007-rationale] gives: the work shipped
  before the file existed, so any such expansion is a reconstruction presented in the shape readers
  trust as a pre-implementation contract. A stub cannot mislead about a deliberation it does not
  claim to have had.
- **State the coverage as a count** ("eight live tests, two package tests"). Rejected: a count rots
  silently and cannot be grepped. `path::QualifiedName` per [`AGENTS.md`][agents] rule 27 fails loudly
  when a name changes, which is the property that makes a spec checkable.

*What replaced it.* `## Scope` now names the retired app by path and `app_label`, its five models, the
six edges as a cardinality mapping table, and every test that pins the contract at `HEAD` by
`path::QualifiedName` — split into the package tier and the live HTTP tier, because the card's own
scope statement drew that line and [`AGENTS.md`][agents] rule 7 has since codified it.

*Claims the spec no longer makes.* That its scope is describable without naming the fixtures, the
models, or the tests; and that the card's coverage lives entirely where it was first written — see
the next entry.

### `## Scope` — one of the card's own tests was removed, and the removal is a strengthening

Spec: [Scope][spec-013-scope].

*Nothing moved; this entry records the one later change that altered the shipped shape.* It is
obligation 2's case for this card, and it is invisible from the stub.

*What happened.* `1057ddc2` re-pointed `tests/types/test_definition_order_schema.py` at the real
`library` models, and in doing so gave it
`::test_m2m_schema_shape_builds_with_real_library_models` — a test that declared `BookType` /
`GenreType`, built a `strawberry.Schema`, and asserted
`str(schema._schema.type_map["BookType"].fields["genres"].type) == "[GenreType!]!"`. That test does
not exist at `HEAD`. It was removed by `be9130e3` "Migrate package tests to the live /graphql/
fakeshop suite" (2026-06-13), which cut
[`tests/types/test_definition_order_schema.py`][test-types-definition-order-schema] from four test
functions to one (`git show be9130e3~1:<path>` vs `git show be9130e3:<path>`, both greped for
`^def test_`).

*Why this is not a drop.* The same commit added
[`examples/fakeshop/test_query/test_library_api.py`][test-library-api]
`::test_book_genres_m2m_renders_as_list_shape_live`, whose docstring names the retired test outright
("The live twin of ``test_m2m_schema_shape_builds_with_real_library_models``") and asserts the same
`[GenreType!]!` shape by unwrapping `NON_NULL -> LIST -> NON_NULL -> OBJECT GenreType` from **real
introspection over HTTP** rather than from the private `schema._schema.type_map`. The commit states
its own governing rule in its body: a package test moves to the live suite "only when the same
behavior is reachable through the real `/graphql/` endpoint AND the live replacement applies the
same-or-stronger contract … line coverage alone is not treated as sufficient." Both conditions hold
here — the wire shape is reachable by introspection, and reading it from the served schema is
strictly stronger than reading it from a private attribute of a locally-constructed one. This is
[`AGENTS.md`][agents] rule 10 applied, and [`START.md`][start]'s standing "live-first" preference.

*Why the spec records the current location and not the move.* [`BUILD.md`][build] `## Spec rationale
extraction` is explicit that the spec states the current contract and never narrates how it got
there. So the reconciled `## Scope` lists the live twin among the HTTP-tier coverage, by its
`path::QualifiedName`, with no mention of what it replaced; the replacement is recorded here, once.

*The alternatives rejected.*

- **Treat the removal as coverage loss and re-flag it as a defect.** Rejected on the evidence: the
  contract survives, in a stronger form, under a rule the removing commit states and this repository
  applies generally. Re-litigating it would be this cycle overturning a settled migration.
- **List the retired test in the spec as historical context.** Rejected: chronology in a spec is
  precisely what the extraction rule forbids, and a reader checking the spec against `HEAD` would be
  sent looking for a symbol that does not exist.
- **Say nothing anywhere.** Rejected: this is the one fact that makes the stub's implicit claim false
  — that a reader can find all of card 013's coverage where card 013 wrote it. An unrecorded
  relocation is how a later reviewer concludes a test was dropped.

*Claim the spec may not make.* That the card's coverage lives entirely in the files its own commits
touched. Two of its deliverables have moved since: this test to the live tier at `be9130e3`, and the
two non-live schema tests to the per-app tier at `31642c9c`.

### `## Scope` — the `library` app is no longer this card's diff, and the spec must not claim it

Spec: [Scope][spec-013-scope].

*Nothing moved; this entry bounds the reconciled section rather than correcting anything the stub
said.* The stub's vagueness has a second cost beyond uncheckability: because it says only "real
managed models in the `library` example app", a reader at `HEAD` naturally reads today's
`models.py` as the card's deliverable. That reading over-credits this card by a wide margin, and the
margin is measurable — `git show 73004d74:examples/fakeshop/library/models.py | grep -c "^class "`
returns **7**; the same count at `HEAD` returns **11**. *(This cycle's build plan says 12; the
measured figure is 11 and the plan's number is the one to distrust.)*

Every addition belongs to a later card, and each was traced with
`git log -S<symbol> --follow -- examples/fakeshop/apps/library/models.py`:

| Later addition | Landed at | What it exists for |
|---|---|---|
| `TaggedItem` + `Branch.tags` (`GenericRelation`) | `d592ac3a` (2026-05-08) | unsupported-relation error handling in annotation building |
| `Patron.lifetime_fines_cents` (`BigIntegerField`) | `cae2d5a3` (2026-05-27) | the `BigIntegerField -> BigInt` scalar converter |
| `Shelf.alt_branches` (`ManyToManyField` to `Branch`) | `d1fb4cf2` (2026-06-24) | raw-pk relation input on the **write** side — a second M2M edge, not this card's |
| `Periodical`, `Issue` | `51421e54` (2026-07-10) | keyset value-encoded cursors (`Meta.cursor_field`) |
| `ProxyBranch` + `proxy_tags` | `41008e4c` (2026-07-17) | proxy-model content-type resolution for generic connections |

**The app itself also moved.** `examples/fakeshop/library/` became `examples/fakeshop/apps/library/`
at `a7ca9cc2` "Finish spec-testing_shift.md" (2026-05-07 17:58) — the project-wide `apps/` + `config/`
restructure, four hours after the card's last commit and the day *before* the `0.0.4` release cut. So
the path is correct at `HEAD` and correct at the release, and wrong only for the three commits that
are the card's actual diff.

*Why the spec names `Book.genres` explicitly rather than "the M2M edge".* Because there are two M2M
edges on `Shelf`/`Book` at `HEAD` and only one of them is this card's. Naming the edge is what keeps
the scope checkable in a file that other cards keep extending — and it is why the reconciled
`## Scope` closes with an explicit sentence putting the later growth outside this card, in the shape
[`spec-011`][spec-011-rationale]'s reconciled scope used to fence off scalar-override semantics.

*The alternative rejected.* **Say nothing and let `## Scope` name only the six edges.** Rejected as
insufficient: silence about the app's growth is exactly the condition that produced the misreading,
since the six edges are a subset of a file that now carries eleven models. One bounding sentence
costs a line and closes the question.

*Claim the spec may not make.* That the `library` app's current model set, its generic relations, its
proxy model, its second M2M, its `BigInt` field, or its keyset substrate are card 013's scope.

### `## Other` — six rows of three kinds under a heading that names none of them

Bears on [Scope][spec-013-scope]; the heading this entry keys to no longer exists.

*Nothing moved; the heading and its six bullets were deleted.* The section rendered one
`#### Why it matters` row ("test hygiene."), the card's `description` column ("replace test-only M2M /
cardinality fixtures with real `library` models; add package + HTTP coverage."), and four
`#### Files likely touched` paths, flattened into one undifferentiated list under a heading that
names none of the three kinds. The counts were re-read from the rendered card body in
[`KANBAN.md`][kanban] and match the stub's six.

*Disposition, bullet by bullet, rather than a bulk drop.*

- "test hygiene." — no successor. It is a board-level triage note about the card's value, and a spec
  that tells a reader its own subject is hygiene says nothing `## Scope` does not.
- "replace test-only M2M / cardinality fixtures with real `library` models; add package + HTTP
  coverage." — a restatement of `## Scope` bullets 1 and 2 in the imperative, and the same duplicate
  row `DONE-011-0.0.4` carried. Dropped with them. (This is F12's board-side defect seen from the
  spec side; the board fix is deferred, below.)
- The four paths — **not carried forward as a file list.** As rendered they read as a record of what
  the card changed, and two of the four are wrong as such. `examples/fakeshop/apps/library/models.py`
  is the path at `HEAD` and at the release, but the card's own commits wrote
  `examples/fakeshop/library/models.py`; and the list omits every file the card *deleted* — the four
  under `tests/fixtures/` that are the substitution itself. What survives into the reconciled
  `## Scope` is not the list but the coverage it gestured at, stated by `path::QualifiedName`.

*Claims the spec no longer makes.* That `Other` is a section of card 13; that the card's diff touched
exactly those four files; that "test hygiene" is a contract.

### The `[backlog]` link definition — recorded, not fixed

Spec: the link-definitions block, `<!-- Root -->` group.

`[backlog]: ../../BACKLOG.md` is defined and never used: `grep -c '\[backlog\]'` over the spec returns
1, the definition itself. It is **deliberately left in place**, exactly as the spec-011 and spec-012
cycles left theirs. The board already owns the pattern: [`KANBAN.md`][kanban] catalogues 71 unused
link definitions across 23 files, naming an unused `[backlog]` definition in eight archived specs and
listing `spec-013` among them, to be retired in one sweep by the checker card. Fixing one file of a
cross-surface pattern leaves the surface *divergently* wrong rather than uniformly wrong, which is the
disposition [`worker-0.md`][worker-0] `## Closing out a kanban card` prescribes, so it goes to this
cycle's deferred-work catalog instead.

## Reconciliation record — what the spec now says, and why

The spec went from **1,669 bytes / 59 lines** to **5,533 bytes / 77 lines**: it more than tripled in
prose while losing two of its four sections, because every surviving sentence had to name something a
reader can `grep`. The before-figure is the committed file at `973d00b2`; the after-figure is this
pass's working tree on top of it. Both were read with `wc -c -l`.

That is the largest of the three residual-cycle specs by a wide margin — spec-011 landed at 3,440
bytes and spec-012 at 2,814 — and the reason is that this card's contract is an enumeration, six
edges plus the eleven test functions that pin them, where theirs were a policy and a set of five version
surfaces.

### The strategy, and what it rejected

The strategy: a coverage-substitution card's contract **is** the set of relation edges it moved from
fixtures onto real models, plus the tests that pin each one at `HEAD`. So the spec must name the
retired set, name the replacement set, and name the assertions — nothing else it could say is
checkable. Two alternatives lost.

- **Leave `## Scope` as two summary bullets and put the enumeration only here.** Rejected: it keeps
  the spec uncheckable against the tree, which is the defect this pass exists to close. A reader
  confirming a coverage card needs the coverage in the contract, not in the deliberation file — the
  rationale answers *why*, and the spec must answer *what*.
- **Enumerate the six edges but describe coverage as "package and HTTP tests in
  `test_definition_order.py` and `test_library_api.py`".** Rejected: naming the files without the
  test functions is a half-measure that survives a deletion. The test-function names are the thing a
  later refactor moves, and naming them is what made the `be9130e3` relocation visible to this cycle
  at all.

### `## Scope` — two unnamed summaries became a named substitution plus a named coverage map

Spec: [Scope][spec-013-scope]. The section now carries: the retired app by path and `app_label` with
its five models; the six-edge cardinality mapping table; the package-tier tests by
`path::QualifiedName` with what each asserts; the live-tier tests by `path::QualifiedName`, including
the SQL join-table pin and the introspection shape test; the two per-app schema tests; and a closing
sentence fencing the `library` app's later growth outside this card's scope. No `path:NN` line numbers
appear anywhere — they rot on the next edit of files this spec does not own — and the two module-level
references use [`AGENTS.md`][agents] rule 27's `path #"unique substring"` form.

*Why the bounding sentence is in the contract rather than only here.* A reader checking this spec
opens `examples/fakeshop/apps/library/models.py` and finds eleven models where the spec names six
edges across six. Without the sentence, the honest reading is that the spec is stale. With it, the
spec is precisely and verifiably true — and it is the sentence a future reader deletes only if the
card's scope actually widens.

### The link scaffold

The block keeps all ten canonical group headers in order. It gained `[spec-013-rationale]` under
`<!-- docs/SPECS/ -->`, `[test-types-definition-order]` and `[test-optimizer-definition-order]` under
`<!-- tests/ -->`, and `[library-models]`, `[test-library-api]`, and `[test-library-schema]` under
`<!-- examples/ -->`; it keeps `[kanban]`, `[glossary-relation-handling]`, and the unused `[backlog]`
for the reason the entry above gives. Every path was disk-checked from `docs/SPECS/`, and the
archived-depth trap was re-checked in both directions: `../../tests/…` and `../../examples/…` reach
the real trees and `../GLOSSARY.md` reaches [`docs/GLOSSARY.md`][glossary], with no same-named file
one level up to mask a bad depth. This file's own defs sit one level deeper again (`../../../`,
`../../`), disk-checked the same way.

### What this cycle deliberately did not fix

Three surfaces carry claims this rewrite falsifies or that a partial fix would worsen. Each is
recorded here and routed to the cycle's deferred-work catalog rather than half-fixed.

- **[`KANBAN.md`][kanban] still lists `spec-013` among four archived stubs "still carrying the
  boilerplate … preamble"**, and [`spec-011-…-rationale.md`][spec-011-rationale] carries the same
  list. Both become stale the moment this pass lands. Neither is fixable here: `KANBAN.md` is
  generated from `examples/fakeshop/db.sqlite3`, which is **dirty with a concurrent session's
  uncommitted work**, so a regenerate would publish rows that have not landed
  ([`START.md`][start] `## Concurrent sessions`); and a prior cycle's committed rationale file is
  outside this cycle's writable set. The next sweep should measure **three**, not four.
- **The card body's duplicate `#### Scope` row** — the `description` column rendered a third time
  under the same heading, the identical defect `DONE-011-0.0.4` carried. Same blocker: it is an ORM
  edit plus a regenerate, never a hand-edit of the rendered file.
- **The `[spec-013]` ref-id in `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`** resolves to
  `spec-017-deferred_scalars-0_0_6.md`, and `spec-018` / `spec-019` reference a
  "`spec-013-deferred_scalars`" that pre-dates the board renumber. None of these names this card, and
  none is broken by this rewrite — they are recorded so a future `grep -rn "spec-013"` does not read
  them as inbound references to card 13.

## Audit record — what the archive audit found after the reconciliation

Appended by the documentation-completion and archive-audit pass, which re-derived every claim in the
reconciled spec at `HEAD` (`973d00b2`) from an adversarial vantage: it did not write the
reconciliation and had no memory of why any sentence was there. Ten of the eleven cited test
functions, the six-edge mapping, the retired fixture set, the SQL join-table pin, the `[GenreType!]!`
introspection claim, and every out-of-scope fence held exactly as written. One claim did not.

### `## Scope` — the forward-FK HTTP claim was falsified by a later visibility contract

Spec: [Scope][spec-013-scope], the HTTP-tier bullet naming
`::test_library_optimizer_selects_book_shelf_in_http_query`.

*The claim as reconciled.* "the forward FK is planned as `select_related` in a served query" — which
is what the test asserted when the card shipped: `git show 67b07f79:…/test_library_api.py` pins
`len(captured) == 1` plus `"JOIN" in sql`, a single joined query.

*What the test asserts at `HEAD`.* `len(captured) == 2`, with `library_book` in the first query and
`library_shelf` in the second, under the comment that `ShelfType.get_queryset` implements the
nested-visibility contract so the optimizer "correctly downgrades `select_related("shelf")` to
Prefetch so the visibility hook applies before the join surfaces hidden rows." The assertion flipped
at `1694bd2e` "Finish build-021-filters-0_0_8" (2026-05-28) — `git show 1694bd2e~1:<path>` carries
`== 1`, `git show 1694bd2e:<path>` carries `== 2`.

*Why this is a correction and not a defect in the code.* The downgrade is the package's documented
rule — a relation whose target type carries a custom `get_queryset` cannot be served by a join,
because the join would surface rows the visibility hook excludes. The forward FK is still *planned*
as `select_related`; what changed is what the planner is allowed to execute once the target type
declares visibility. The card's edge is intact and still pinned over HTTP.

*What replaced it.* The bullet now states the planned decision, the downgrade, its cause, and the
observable two-query shape — all in the present tense, with no reference to what the assertion used
to say.

*The alternatives rejected.*

- **Drop the bullet and let the package-tier `plan_relation` assertions carry the forward FK.**
  Rejected: the card's own contract is coverage at both tiers, and the HTTP tier is where
  [`AGENTS.md`][agents] rule 10 wants it. Deleting a live citation to avoid restating it hides the
  edge rather than fixing the claim.
- **Say only "the forward FK is exercised in a served query".** Rejected for the same reason the
  reconciliation rejected a bare count: a claim vague enough never to be falsified is also one no
  reader can check, and the vagueness of the original stub is the defect this cycle exists to close.
- **Record the flip in the spec as history.** Rejected — [`BUILD.md`][build] `## Spec rationale
  extraction` forbids chronology in the contract. The flip is here; the spec states only what holds.

*Claim the spec no longer makes.* That `Book.shelf` is served as a `select_related` join over HTTP.
It is planned as one and executed as a visibility-scoped `Prefetch`.

*The lesson, for the next residual cycle.* Naming a test by `path::QualifiedName` proves the symbol
survives; it does not prove the sentence describing it survives. A test that keeps its name while
its assertion is inverted is invisible to a name-existence sweep, and only reading the body against
the sentence finds it. Every other claim in this spec was checkable by grep; this one was not.

### Inbound references — one further staleness, recorded not fixed

The reconciliation grew the spec from 1,669 to 5,533 bytes, which falsifies the byte figure in
`docs/builder/DONE/build-007-onboarding_docs_spec_consolidation-0_0_4.md`'s smallest-specs ranking
("spec-013 (1,669 bytes)"). It is a closed cycle's committed record of a measurement taken at its own
date, and the spec-012 residual cycle left the equivalent figure for spec-012 standing for the same
reason; it is not restated as a live claim anywhere. Recorded here and in the cycle's deferred-work
catalog rather than edited.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[kanban]: ../../../KANBAN.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary]: ../../GLOSSARY.md
[glossary-relation-handling]: ../../GLOSSARY.md#relation-handling

<!-- docs/SPECS/ -->
[spec-007-rationale]: spec-007-onboarding_docs_spec_consolidation-0_0_4-rationale.md
[spec-011-rationale]: spec-011-stale_placeholder_cleanup-0_0_4-rationale.md
[spec-012-rationale]: spec-012-version_release_alignment-0_0_4-rationale.md
[spec-013]: ../spec-013-real_m2m_coverage-0_0_4.md
[spec-013-card-snapshot]: ../spec-013-real_m2m_coverage-0_0_4.md#card-snapshot
[spec-013-scope]: ../spec-013-real_m2m_coverage-0_0_4.md#scope

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[worker-0]: ../../builder/worker-0.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->
[test-optimizer-definition-order]: ../../../tests/optimizer/test_definition_order.py
[test-types-definition-order]: ../../../tests/types/test_definition_order.py
[test-types-definition-order-schema]: ../../../tests/types/test_definition_order_schema.py

<!-- examples/ -->
[test-library-api]: ../../../examples/fakeshop/test_query/test_library_api.py
[test-library-schema]: ../../../examples/fakeshop/apps/library/tests/test_schema.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
