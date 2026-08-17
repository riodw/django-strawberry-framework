# Build: R2 — documentation completion and archive audit (spec-014)

Spec reference: `docs/SPECS/spec-014-testing_shift-0_0_4.md` (whole file, 39 lines at entry / 41 at exit)
Status: final-accepted

A **Worker-1-only item** on a residual-completion cycle: it writes Markdown only, touches no package
source and no test, and is dispatched with no Worker 2 and no Worker 3 pass
(`docs/builder/build-014-testing_shift-0_0_4.md` `## Dispatch record`). Per that dispatch this
artifact carries a **combined Plan + Final-verification block** rather than the four-pass shape.

The item's vantage is deliberate: this spawn did not write R1's reconciliation and carries no memory
of why any sentence in it is there. Every claim below was re-derived at `HEAD` by reading bodies, not
by confirming that names still exist.

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked.** Not applicable in the code sense — this item writes no Python and
proposes no helper. The documentary equivalent was performed, which is where this item's duplication
risk lives: `docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-rationale.md` was read for the shape of
an audit-pass append, and `docs/builder/bld-014-r1-rationale_and_spec_reconciliation.md` for what R1
already argued. Findings:

- **Existing patterns reused.** Two, both cited rather than re-argued: (a) spec-013's audit-pass
  entry shape — *claim as reconciled* / *what the test asserts at `HEAD`* / *why it is a correction
  not a defect* / *alternatives rejected* / *claim the spec may no longer make*; (b) its closing
  lesson about `path::QualifiedName` proving a symbol and not a sentence, restated here rather than
  re-derived because this cycle hit the same class of defect on the same commit (`1694bd2e`).
- **New shape justified.** One: `## Audit record — the adversarial re-derivation pass`, appended to
  the rationale below R1's entries. Its single responsibility is to hold what a second, memoryless
  reader found in R1's output. It is a new top-level section rather than edits inside R1's entries
  because the rationale is append-only during the cycle.
- **Duplication risk avoided.** The obvious near-copy is restating the whole V1-V10 table R1 already
  recorded. It does not arise: this pass re-derived a **different** claim set (the spec's own
  sentences, clause by clause) and records only the confirmations a future cycle would otherwise
  re-litigate, under `### What the audit confirmed unchanged`.

### Implementation steps

1. Re-derive the baseline; read every file dirty with concurrent work through
   `git show HEAD:<path>` into a scratch path outside the repo.
2. Re-derive each spec claim in turn against `HEAD`, reading test and source bodies rather than
   grepping names. Order: the seven models, the eight shapes, the two fences, the finalize seam, the
   one-extension-instance claim, the reload description clause by clause, the eight live-tier items,
   `CaptureQueriesContext`, `dst_optimizer_plan`, the Layer-3 ownership sentence, the two follow-ups,
   the package-level keep-list.
3. Audit F11-F14; disk-check every link definition in both files from that file's own directory,
   including the same-named-file-one-level-up masking trap.
4. Run the staged-anchor sweep the absent integration pass would have owned.
5. Verify R1's two forwarded items rather than accepting them.
6. Fix every claim that does not hold, present-tense, with no narration of the change; append a
   rationale entry per fix carrying the cause and the rejected alternatives.

Line numbers in this artifact are pin-at-write-time navigational hints.

### Test additions / updates

None. No test file is in this item's writable set and no test run is needed: the item lands Markdown
only. The mechanical gates that do apply are `scripts/check_spec_glossary.py` and the `source-layout`
markdown-scaffold check; both are recorded under `### Validation run`.

### Implementation discretion items

- Which spec section receives the recovered awkward-declaration-order constraint. Decided at write
  time: `## Settled decisions`, beside the finalization seam it exists to prove, rather than
  `## Shipped outcome`, which describes what the card contributed rather than what must stay true.
- Whether to name the specific type pairs in that sentence or state the rule abstractly. Decided:
  name them, because an abstract "declares types out of dependency order" is not checkable and the
  point of the constraint is that a future editor can verify what must not be tidied.

### Dispatched findings checklist

The plan's F11-F14 plus the two obligations the dispatch added.

- [x] **F11** The spec is at `docs/SPECS/` with a reference-style link block carrying all ten
  canonical group headers in order, and `check_spec_glossary` is green. Audit the archive plus the
  new companion's own link hygiene, disk-checking from each file's own directory.
- [x] **F12** All seven glossary anchors resolve and every one is `shipped`; `KANBAN.md`'s
  `DONE-014-0.0.4` card renders them.
- [x] **F13** The durable docs are complete for this card's work; confirm no durable-doc edit is
  owed, and route rather than edit if one is.
- [x] **F14** Record the duplicate `#### Scope` bullet with a ready-to-apply recipe; make no
  database write and run no generator.
- [x] **Adversarial re-derivation** of every claim the reconciled spec makes, reading bodies rather
  than checking names.
- [x] **Staged-anchor sweep** the absent integration pass would have owned.
- [x] **R1's two forwarded items** verified rather than accepted.

---

## Final verification (Worker 1)

### Baseline re-derived

`HEAD` at this pass is `6f8bf818e9b1bc45059017c17fc346a3daca0b8f`, **not** the `676f10d2` R1 recorded
and not the `973d00b2` the build plan recorded. Three concurrent-session commits landed between R1
and this pass — `7ef9f030` (spec-013 reconciliation), `58bff76a` (spec-013 cycle record), and
`6f8bf818` (KANBAN re-home of spec-013's deferred work). **The third is evidence for this pass** and
changed a finding; see `### F14`.

`git status --porcelain docs/SPECS/ docs/builder/` at entry showed the spec-009 pair and two
`bld-013-*` deletions as concurrent sessions' work, untouched throughout.
`docs/SPECS/spec-014-testing_shift-0_0_4.md` carried only R1's uncommitted edit, so this pass's
further edit to it remains unambiguously attributable.

Files this item needed to read that are baseline-dirty with concurrent work:
`examples/fakeshop/test_query/test_library_api.py`, `examples/fakeshop/apps/library/schema.py`, and
`docs/GLOSSARY.md` — each read through `git show HEAD:<path>` into a scratch path outside the repo.
`examples/fakeshop/config/schema.py`, `examples/fakeshop/test_query/conftest.py`,
`examples/fakeshop/schema_reload.py`, and `examples/fakeshop/apps/library/models.py` were clean at
`HEAD` and read directly. **`examples/fakeshop/db.sqlite3`, `KANBAN.md`, and `KANBAN.html` are all
clean at this baseline** — a material change from the plan's, recorded under `### F14`. Nothing dirty
was edited, reverted, staged, stashed, or `git checkout`ed; no generator ran; no database write was
made (the one database access was a read-only `mode=ro&immutable=1` open, to make the F14 recipe
accurate rather than guessed).

### What did not hold — three claims, and how each was fixed

**1. `## Live HTTP coverage` claimed the forward FK is served as `select_related`.** This is the
defect class the dispatch predicted, and it reproduced exactly.
`test_library_optimizer_selects_book_shelf_in_http_query` survives by name, and its body asserts
`len(captured) == 2` with `library_book` in the first query and `library_shelf` in the second,
because `ShelfType.get_queryset` (declared in `examples/fakeshop/apps/library/schema.py`) forces the
optimizer to downgrade the join to a visibility-scoped `Prefetch`. The same commit `1694bd2e`
inverted the sibling assertion spec-013 cited. **Fixed**: the coverage sentence now states the
planned decision, the downgrade, its cause, and the observable two-query shape — present tense, no
chronology — following the shape spec-013's reconciliation established.

**2. A live constraint lived only in the rationale.** R1 recovered "Type declarations should
intentionally exercise awkward definition orders in at least one module" and correctly judged it a
live constraint rather than deliberation — then recorded it only in the rationale companion. A
constraint on how a module must be written is normative and belongs in the contract; the rationale is
the one file a future editor tidying `apps/library/schema.py` will not open. Verified at `HEAD`: the
module declares `LoanType` ahead of `BookType` and `PatronType`, `ShelfType` ahead of `BranchType`,
and `MembershipCardType` ahead of `PatronType`. **Fixed**: `## Settled decisions` now carries the
order as a contract on the module, naming the consequence — the coverage retires with no test
failing. R1's other recovered live constraint, the `CaptureQueriesContext` broad-SQL-shape rule, was
**already** carried as contract in that same section and needed no change.

**3. `## Remaining follow-ups` said every fenced Layer-3 feature is "owned by their own spec".** Six
of seven are: filters `spec-027`, orders `spec-028`, `DjangoConnectionField` `spec-030`, Relay nodes
`spec-032`, permissions `spec-034`, fieldsets `spec-054`. **Aggregates has no spec** — it is carded
as `TODO-BETA-057-0.1.3`. A routing sentence that routes a reader to a document that does not exist
is the same defect class as the `## Status` sentence R1 removed. **Fixed** with one clause: owned by
its own spec, or by its own card where no spec is authored yet.

Each fix has a rationale entry under `## Audit record — the adversarial re-derivation pass` carrying
the cause, the alternatives rejected with the reason each lost, and the claim the spec may no longer
make.

### What held — re-derived, not accepted

Read as bodies against the sentences describing them. The durable record is the rationale's
`### What the audit confirmed unchanged`; the summary:

- **The seven models are exactly the card-era set.** `git show
  73004d74:examples/fakeshop/library/models.py` holds **7** classes and they are the seven the spec
  names. All seven survive at `HEAD` among 11.
- **All eight relation/field shapes are real edges or columns on those seven** — forward FK, reverse
  FK, forward OneToOne (`MembershipCard.patron`), reverse OneToOne (`Patron.card`), forward M2M
  (`Book.genres`), reverse M2M (`Genre.books`), choice field (`Book.circulation_status`), nullable
  scalar (`Book.subtitle`). The dispatch's "eight" is right and the plan's "nine" was wrong, as R1
  found.
- **Both out-of-scope fences are accurate.** `apps/products` and `apps/library` were both created by
  this card's own `a7ca9cc2`; the other four app packages are `2701eb88`, `d346a45e`, `f9ebb9fa`,
  `5bd246aa`. The four extra model classes and two extra fields are all later cards'.
- **`finalize_django_types()` is called exactly once, in the right place** — after all six app schema
  imports and above the `DjangoSchema(...)` construction in `examples/fakeshop/config/schema.py`.
- **"Exactly one `DjangoOptimizerExtension` instance" is true as stated and is not falsified by the
  factory form.** `extensions=[lambda: _optimizer]` returns the same module-level singleton on every
  call; the singleton exists precisely so the instance-bound plan cache survives per-request
  extension construction. A bare class entry would be the shape that falsifies the claim.
- **Every clause of the `schema_reload.py` / `conftest.py` description holds** — registry clear,
  documented dependency-safe order (glossary before kanban), all six contributing app schema
  modules, `config.schema` + `config.urls` reload, `clear_url_caches()`, module-scoped autouse
  fixture with a one-call body, function-scoped shell-reload guard, `id()`-based registration
  fingerprint over seven registry maps plus the six module objects, and full rebuild on teardown when
  a test mutated them.
- **Seven of the eight live-tier coverage items hold** (the eighth is fix 1 above): nested
  `Branch → Shelf → Book → Loan → Patron`; nullable reverse OneToOne; reverse M2M; reverse FK + M2M
  prefetch at three queries with `library_book_genres` pinned; choice-enum wire value plus
  `BookTypeCirculationStatusEnum` introspection and the nullable scalar; consumer-shaped queryset
  cooperation; both `OptimizerHint` forms; and the relation override observed through response data.
- **`CaptureQueriesContext(connection)` is genuinely the practice** — imported from
  `django.test.utils`, used across eight live-tier modules, with every SQL assertion a substring or
  `JOIN`-presence check rather than a full SQL string.
- **`ctx.dst_optimizer_plan` is not surfaced through HTTP JSON** — zero hits under
  `examples/fakeshop/test_query/`.
- **Both `## Remaining follow-ups` bullets hold.** Strictness has two incidental comment mentions and
  no live assertion; `DjangoDebugExtension` exists at
  `django_strawberry_framework/extensions/debug.py`, so the enabling-surface clause is right. No
  live-tier file constructs a `Prefetch` — the two hits are docstrings in `test_scalars_api.py`.
- **The package-level keep-list and the coupling claims hold** — `tests/` still carries registry
  lifecycle, finalizer atomicity, invalid `Meta`, enum sanitization, unresolved targets, optimizer
  cache-key construction, walker, and helpers; the layered relation-override claim and the
  `apps.products.models` / `apps.library.models` coupling are both accurate.
- **The retired fixture app has zero live hits** —
  `grep -rn "TestsCardinalityConfig\|tests\.fixtures\|tests_cardinality"` over `*.py` / `*.ini` /
  `*.toml` returns nothing; `tests/fixtures/` is absent. `pytest.ini` reads
  `DJANGO_SETTINGS_MODULE = config.test_settings` and `pythonpath = examples/fakeshop`, with
  `examples/fakeshop/apps` deliberately not added.

### F11 — archive and link hygiene

The archive move is done and correct. `docs/SPECS/spec-014-testing_shift-0_0_4.md` carries the
`<!-- LINK DEFINITIONS -->` delimiter and all ten canonical group headers in order, as does the new
companion at `docs/SPECS/appx/`.

Link definitions were **disk-checked from each file's own directory**, by existence test per path,
never by reading:

- From `docs/SPECS/`: `../GLOSSARY.md` (the seven glossary defs) and
  `appx/spec-014-testing_shift-0_0_4-rationale.md`. Both resolve.
- From `docs/SPECS/appx/`: all 13 pre-existing defs plus the one this pass added — `../../../` to
  the repository root (`AGENTS.md`, `CHANGELOG.md`, `KANBAN.md`, `START.md`), `../../` to `docs/`
  (`GLOSSARY.md`, and the new `TREE.md`), `../` to `docs/SPECS/`, bare filenames to siblings under
  `appx/`, and `../../builder/` to the builder docs. All 14 resolve.

**Masking trap checked explicitly**, not assumed: neither `docs/SPECS/GLOSSARY.md` nor
`docs/SPECS/appx/GLOSSARY.md` exists, and neither `docs/SPECS/TREE.md` nor `docs/SPECS/appx/TREE.md`
exists, so no `../../` path is silently satisfied one level up.

Reference-integrity check on both files: every `][ref-id]` use has a definition and every definition
has a use — zero undefined, zero unused, in both.

In-page anchors: the rationale's anchors into the spec (`#status`, `#problem-statement`,
`#shipped-outcome`, `#live-http-coverage`,
`#package-level-tests-that-intentionally-remain`, `#settled-decisions`, `#remaining-follow-ups`) all
resolve against the spec's headings. This pass added no heading and renamed none.

### F12 — glossary anchors

All seven `term`-column strings from
`docs/SPECS/appx/spec-014-testing_shift-0_0_4-terms.csv` survive verbatim in the spec body after
this pass's edits (`grep -c` per term: `choice enum` 1, `DjangoConnectionField` 1,
`DjangoOptimizerExtension` 1, `DjangoType` 2, `finalize_django_types` 3, `OptimizerHint` 1,
`Strictness mode` 1). All seven anchors resolve to `##` headings in `docs/GLOSSARY.md` at `HEAD`
(`Choice enum generation`, `DjangoConnectionField`, `DjangoOptimizerExtension`, `DjangoType`,
`finalize_django_types`, `OptimizerHint`, `Strictness mode`). `KANBAN.md`'s `DONE-014-0.0.4` card
renders all seven in its `#### Glossary terms` table and every row reads `shipped` with a version.
**No edit owed.**

### F13 — durable docs

**No durable-doc edit is owed, and nothing needs routing.** Confirmed by reading, not accepted:

- `AGENTS.md` rule 7 carries **four** test tiers — `tests/`,
  `examples/fakeshop/apps/<app>/tests/`, `examples/fakeshop/test_query/`, and
  `examples/fakeshop/tests/` — where the card era had three. The fourth arrived later, so the rule is
  ahead of this card rather than behind it.
- `docs/TREE.md` renders `examples/fakeshop/config/` as the orchestration package, the `apps/` tree,
  and all four test trees, with the placement rule and the live-first coverage priority restated in
  prose above them.

Both are outside this cycle's writable set in any case (`docs/TREE.md` is script-rendered), and
neither needed a change, so no routing arose.

### F14 — the duplicate `#### Scope` bullet: recorded, not fixed, and its stated blocker has cleared

**The defect holds.** The rendered `DONE-014-0.0.4` card carries four `#### Scope` bullets, the
fourth being a lowercase one-line restatement of the first three:
`- remove the `tests.fixtures.apps` fixture app + unmanaged cardinality fixtures; switch package
tests to real `library` models.` (`KANBAN.md` line 4480 at `HEAD`).

**Two things the plan said about it are no longer true at this baseline, and the catalog must not
repeat them.**

1. **`DONE-011-0.0.4` and `DONE-013-0.0.4` no longer carry the defect.** The maintainer removed both
   at `6f8bf818` (2026-08-16), whose message reads "Drop the duplicate Scope row DONE-013 has carried
   since 2026-05-30: a third CardItem restating the two above it, which the renderer emitted because
   it builds sections from card items alone." Both cards now render exactly two scope bullets.
   **`DONE-014-0.0.4` is the last card carrying it.**
2. **The concurrency blocker has cleared.** `examples/fakeshop/db.sqlite3`, `KANBAN.md`, and
   `KANBAN.html` are **all clean** at this pass's baseline. The plan's reason for deferring — a dirty
   database whose regenerate would publish unlanded rows — does not hold any more. This item still
   makes no database write and runs no generator, because the dispatch forbids both outright; but the
   deferral now rests on the dispatch, not on concurrency, and the catalog should say so rather than
   carry a stale justification forward.

**The "third consecutive cycle" framing is therefore superseded.** It was accurate as a description
of how the disposition was reached three times; it is misleading as a description of the board, since
two of the three cards have since been fixed and the fix is demonstrated.

**Ready-to-apply recipe**, derived from the board schema and confirmed against a read-only open of
the database rather than guessed:

The duplicate is a fourth `kanban.CardItem` row on the `scope` section of the card, not a rendered
column — the renderer builds each section purely from its card items, which is why a stray row
appears as a bullet. On the board at this baseline it is the row whose `order` is `3` and whose text
is the lowercase restatement; the three authored bullets are `order` `0`-`2`. Locate it by text, not
by primary key, since keys shift.

```python
# examples/fakeshop, e.g. uv run python manage.py shell
from apps.kanban.models import CardItem

stray = CardItem.objects.get(
    card__number=14,
    section__key="scope",
    text__startswith="remove the `tests.fixtures.apps` fixture app",
)
stray.delete()
# Re-pack the remaining orders only if the renderer needs contiguity; at 6f8bf818
# the maintainer's equivalent fix did not need to.
```

Then regenerate both board exports (`scripts/build_kanban_md.py`, `scripts/build_kanban_html.py`) and
confirm byte-stability on a second run, exactly as `6f8bf818` did. **Do not hand-edit `KANBAN.md` or
`KANBAN.html`** — the next render reverts it.

### Staged-anchor sweep

`grep -rEn 'TODO\(spec-014|TODO-(ALPHA|BETA|STABLE)-014' .` excluding `.git`, `.venv`, `KANBAN.md`,
`KANBAN.html`, and `BACKLOG.md` returns **zero hits** (exit 1). No staged anchor for this spec
survives anywhere in the tree. This is the obligation the absent `bld-integration.md` would have
carried; it is discharged here and needs no repeat at the final gate.

### R1's two forwarded items — verified, not accepted

**1. The `build-008` citation is already closed; nothing should be routed.** R1 recorded that
`docs/builder/DONE/build-008-definition_order_independence-0_0_4.md` cites spec-014 for an object it
does not own, and forwarded it to the deferred-work catalog. Read in context, the artifact does not
misattribute: its `#### Maintainer decision 4` *records* that two **source comments** wrongly cited
spec-014, reassigns them to `spec-010` and `spec-018`, and dispatches item R2b to fix them. That box
is ticked and the fix landed — `git grep -n "spec-014" HEAD -- django_strawberry_framework/` returns
nothing, while `types/relations.py` now cites `spec-010` and `spec-018` and
`types/base.py` cites `spec-018`. The artifact is a closed cycle's accurate record of a defect that
no longer exists. **Deferring it would have carried a phantom into the catalog.** Recorded in the
rationale so the next cycle does not re-forward it.

**2. One of R1's three recovered constraints was left out of the contract.** The
`CaptureQueriesContext` broad-SQL-shape rule was already in `## Settled decisions` and needed
nothing. The awkward-declaration-order constraint was **not** in the spec at all — a reconciliation
gap, now closed (fix 2 above).

### DRY check across this item and R1

No duplication introduced. The audit section does not restate R1's V1-V10 table; it records a
disjoint claim set. The one shape borrowed from spec-013's rationale — the falsified-live-claim entry
form — is cited as a reuse in `### DRY analysis` rather than re-argued, and the `path::QualifiedName`
lesson is restated deliberately because this is the second consecutive cycle to hit it, which is
itself the finding.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-014-testing_shift-0_0_4.md`
  -> `OK: 7 terms - all have glossary entries and at least one spec link.` **Pass**, unchanged from
  entry, with all seven CSV `term` strings confirmed verbatim in the body by per-term `grep -c`.
- `uv run python scripts/check_trailing_commas.py --check` on both files -> **pass**, no output. Both
  carry the delimiter and all ten canonical group headers in order.
- Link definitions disk-checked per path from each file's own directory (14 from `docs/SPECS/appx/`,
  2 from `docs/SPECS/`), plus the four explicit masking checks. All resolve.
- Reference integrity on both files: zero undefined refs, zero unused definitions.
- In-page anchors from the rationale into the spec: all resolve.
- No `pytest` run and no coverage-shaped flag in any pass. No test is in this item's writable set,
  and no claim required a focused run — every one was decidable by reading the test body.
- **Floor verification: not applicable.** The plan declares floor-verification scope `none`; this
  item touches no executable code.
- **Hot-path budget: not applicable.** The plan declares no hot path; this item writes Markdown only.
- **Failability proofs: none; this pass introduced no new boundary.** It introduced no code.
- `git status --porcelain` after the pass shows exactly three paths this item owns as changed or new
  — `docs/SPECS/spec-014-testing_shift-0_0_4.md`,
  `docs/SPECS/appx/spec-014-testing_shift-0_0_4-rationale.md`, and this artifact — plus the
  gitignored `docs/builder/worker-memory/spec-014-worker-1.md`. Nothing else moved by this pass; the
  concurrent sessions' `spec-009` pair and `bld-013-*` deletions are exactly as found.

### Deferred

- **F14 — the duplicate `#### Scope` bullet on the rendered `DONE-014-0.0.4` card.** Deferred
  **because this item's dispatch forbids any database write and any generator run**, not because of
  concurrency: the plan's stated blocker has cleared (`examples/fakeshop/db.sqlite3`, `KANBAN.md`,
  and `KANBAN.html` are all clean at this baseline). `DONE-014-0.0.4` is now the **last** card
  carrying the defect — the maintainer fixed `DONE-011-0.0.4` and `DONE-013-0.0.4` at `6f8bf818`,
  which is also the worked precedent for the fix. The ready-to-apply recipe is in `### F14` above and
  belongs in the final gate's `### Deferred work catalog` **with the corrected justification**.
- **Nothing else is deferred.** R1's `build-008` item is closed rather than deferred (above), and no
  durable-doc edit is owed.

### Summary

Every claim the reconciled spec-014 makes was re-derived at `HEAD` by a spawn with no memory of
writing it, reading test and source bodies rather than confirming names. Three did not hold. The
`## Live HTTP coverage` forward-FK claim was falsified by `ShelfType`'s later `get_queryset`
visibility hook, which downgrades the join to a visibility-scoped `Prefetch` — the same commit and
the same defect class that the sibling spec-013 cycle found, caught here only by reading the test
body. A live constraint recovered by R1 — the deliberately non-dependency `DjangoType` declaration
order in `apps/library/schema.py`, whose tidying would silently retire finalization coverage — lived
only in the rationale and is now stated as contract. And the Layer-3 routing sentence claimed every
fenced feature has its own spec when aggregates has only a card. All three are fixed present-tense in
the spec, each with a rationale entry carrying the cause, the alternatives rejected, and the claim
the spec may no longer make. Everything else held: the seven models, the eight shapes, both fences,
the finalize seam, the one-extension-instance claim, every clause of the reload description, the
other seven live-tier items, `CaptureQueriesContext`, the `dst_optimizer_plan` deferral, the
package-level keep-list, and both follow-ups. The archive and link hygiene are clean, all seven
glossary anchors resolve as `shipped`, no durable-doc edit is owed, and the staged-anchor sweep is
empty. One item R1 forwarded turned out already fixed and is closed rather than deferred; F14 remains
deferred, but its stated blocker has cleared and its justification is corrected.

Final status: `final-accepted`.

### Spec changes made (Worker 1 only)

| Section | Change | Reason |
|---|---|---|
| `## Live HTTP coverage` | "forward FK `select_related`" replaced by the planned-`select_related` / executed-as-visibility-scoped-`Prefetch` statement naming `Book.shelf`, `ShelfType`'s `get_queryset`, and the two-query shape | the claim was falsified at `1694bd2e`; a test that keeps its name while its assertion inverts is invisible to a name sweep |
| `## Settled decisions` | added the non-dependency `DjangoType` declaration order of `examples/fakeshop/apps/library/schema.py` as a contract on the module, naming the three orderings and the silent-coverage-loss consequence | a live constraint R1 recovered but recorded only in the rationale; normative text belongs in the contract |
| `## Remaining follow-ups` | "each owned by their own spec" -> "each owned by its own spec or, where none is authored yet, by its own card" | aggregates has no spec, only `TODO-BETA-057-0.1.3`; a routing sentence must not route at a document that does not exist |

Rationale appended (never rewritten): `## Audit record — the adversarial re-derivation pass`, with
one entry per fix plus `### The build-008 citation is a record of a fixed defect, not live rot` and
`### What the audit confirmed unchanged`. One forward-pointer clause was added to each of R1's two
`### What this cycle deliberately did not fix` bullets so a reader stopping there is not left with a
superseded fact; R1's reasoning is untouched.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
