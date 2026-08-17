# Rationale: spec-014 — IRL API test shift (recovered design record, rejected alternatives, change record)

Deliberative companion to [`spec-014-testing_shift-0_0_4.md`][spec-014]. The spec is the contract and
states only what holds now; everything that explains **how it got there** lives here — the design
record the spec was authored as, the alternatives that record weighed, what its four commits actually
did, the four later contracts that reshaped the shipped surface it describes, and every claim the
spec may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the work shipped, not before the build.** Card `DONE-014-0.0.4` shipped at
`0.0.4` across commits on 2026-05-07, and the rule that gates a build on this move did not exist
then; this pass supplies it.

**This file is a restoration, not a reconstruction — and that makes spec-014 the exception in its
series.** [`spec-011`][spec-011-rationale], [`spec-012`][spec-012-rationale], and
[`spec-013`][spec-013-rationale] were card-snapshot stubs: they had never been deliberated, so their
rationale companions had to be assembled out of git history and measurement. Spec-014 *was*
deliberated. It was authored at `73004d74` as a genuine 61-line pre-implementation design record
carrying a current-state survey, goals, non-goals, a proposed app, test-placement rules, a candidate
migration catalogue, a keep-package-level list, a migration strategy, validation expectations, and an
open-decisions section. **Its own implementing commit deleted all of it in place.** Recovering that
deliberative layer is this cycle's largest single deliverable, and it is `## The recovered design
record` below.

## How to read this file

- **One entry per spec section**, named by the section's own heading and linked to its anchor. A
  section with no entry here lost nothing.
- **The recovered design record comes first, before the per-section entries.** It is not keyed to one
  spec section because it is not a fragment of one: it is the whole document the spec used to be, and
  every current section descends from some part of it. Each recovered section says which current
  section it bears on.
- **This spec has no numbered Decisions.** So the key is the heading, and one entry keys to a heading
  the reconciliation renamed; it says so and names both spellings.
- **Every fact below was measured at this working tree, not restated.** Each commit, count, and
  quotation carries the command or blob it came from. Where a figure in this cycle's
  [build plan][build-014] disagreed with the measurement, the measurement is recorded and the
  disagreement is named.
- **The move and the reconciliation are one pass**, so this file carries both records: the recovered
  record and the entries keyed to the spec first, then
  `## Reconciliation record — what the spec now says, and why`.

### Why the recovered catalogue is fenced rather than quoted inline

[`AGENTS.md`][agents] rule 27 forbids raw `path:NN` source references in code comments, specs, and
standing docs, allowing them only in per-cycle scratchpads. The recovered
`## High-value migrations to HTTP tests` section is **37 such references** across 8 bullets
(`git show 73004d74:docs/spec-testing_shift.md | awk '/^## High-value/,/^## Tests that should/' |
grep -o "tests/[a-z_/]*\.py:[0-9]*" | wc -l` -> `37`), and this rationale file is a tracked standing
doc, not a scratchpad.

Three dispositions were weighed.

- **Translate each `path:NN` into the symbol-qualified form.** Rejected, and this is the important
  rejection: the line numbers name lines in `tests/` files as they stood on 2026-05-07, and those
  files have been rewritten many times since. A translation would have to guess which of today's
  symbols each historical line belonged to, and a wrong guess would read as a measured fact. Worse,
  the *point* of preserving the catalogue is that it records what the author was looking at, which a
  translation destroys.
- **Drop the catalogue and summarize it.** Rejected: it is the single most deliberative artifact the
  destroyed record contained — the author's own priority ordering over the migration — and a summary
  of a priority ordering is not a priority ordering.
- **Reproduce it verbatim inside a fenced code block, with the recovery command beside it.**
  Adopted. A fenced block renders verbatim as example content and is explicitly not a live link or
  reference ([`START.md`][start] `## Markdown link convention`), so what sits inside it is
  **quotation of a historical document, not a reference this document is making**. Rule 27 governs
  refs a doc asserts; it does not turn a quoted primary source into an assertion. The block is
  labelled as a quotation of a specific blob so no reader mistakes the numbers for current.

The same fencing is applied to the two other recovered sections that name a source path with a line
number. Recovered sections carrying no `path:NN` are quoted as blockquotes.

## Provenance of this record

- **Recovered, not moved.** The ten deliberative sections below were not cut out of the spec by this
  pass. They were deleted from it by `67b07f79` on 2026-05-07, and had existed nowhere since. They
  are restored here from `git show 73004d74:docs/spec-testing_shift.md`. This is the difference
  between this file and its three siblings, and it is why `## The recovered design record` is the
  bulk of it.
- **Moved by this pass** — cut from the spec and now only here: the `## Status` sentence "The
  original spec remains here as the design record, but this document now describes the shipped state
  and the remaining follow-up surface." It is quoted below inside the entry that disposes of it.
- **Added in exchange:** the `## Status` slot now carries a present-tense shipped statement plus the
  one-line pointer sentence naming what moved and where, with its `[spec-014-rationale]` link
  definition under `<!-- docs/SPECS/ -->`.
- **Deleted outright rather than moved**, per [`worker-1.md`][worker-1] rule 2, because the current
  contract falsifies them: the `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])`
  construction claim, the `DJANGO_SETTINGS_MODULE = config.settings` claim, the two-app enumeration
  read as exhaustive, the per-test full-reload description of the autouse fixture, and the "remain
  non-goals for this slice and should land under their own specs" framing of seven Layer-3 features
  of which five have shipped. Each deletion is recorded below as a claim the spec may no longer make;
  none is restored anywhere as live text.
- **The seven glossary anchors all survive their carriers.** `choice enum`, `DjangoConnectionField`,
  `DjangoOptimizerExtension`, `DjangoType`, `finalize_django_types`, `OptimizerHint`, and
  `Strictness mode` are each preserved verbatim as the `term` column of
  [`spec-014-testing_shift-0_0_4-terms.csv`][spec-014-terms] requires, on rewritten sentences.
  `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-014-testing_shift-0_0_4.md`
  exits 0 (`OK: 7 terms`) after the rewrite, as it did before.
- **No fenced code block existed in the spec** before this pass, and none exists after. The fenced
  blocks are in this file only.

## What the card actually did — four commits, and the one that destroyed the record

All 2026-05-07. Three name the spec in their message; the fourth is a sibling card's and is included
because it is the one that overwrote the spec.

| Commit | Time | What it did |
|---|---|---|
| `73004d74` "Refactor tests a bit;" | 12:22 | **Authored `docs/spec-testing_shift.md`** — the 61-line design record recovered below — and created the `library` example app plus the first `test_library_api.py`. Shared with card `DONE-013-0.0.4`. |
| `1057ddc2` "Complete spec-testing_shift.md;" | 13:08 | **This card's own scope.** Deleted `tests/fixtures/` — the unmanaged `tests_cardinality` app — dropped `tests.fixtures.apps.TestsCardinalityConfig` from the example project's `INSTALLED_APPS`, and re-pointed the package tests at the real `library` models. Shared with card `DONE-013-0.0.4`. |
| `67b07f79` | 13:50 | Card `DONE-013-0.0.4`'s coverage expansion — **and the commit that overwrote the spec**, replacing the design record with a shipped-state summary and adding the `## Status` line claiming the record survived. |
| `a7ca9cc2` "Finish spec-testing_shift.md" | 17:58 | **The layout shift.** Moved the flat example project into `examples/fakeshop/config/` + `examples/fakeshop/apps/`, re-pointed `pytest.ini`'s `DJANGO_SETTINGS_MODULE` from `settings` to `config.settings`, and updated `AGENTS.md` / `docs/TREE.md` / `test_query/README.md`. It also **re-edited the spec** (+10/-8), re-pathing the summary `67b07f79` had just written and adding the two `## Remaining follow-ups` bullets. |

*The fourth row's spec edit is not in this cycle's [build plan][build-014].* The plan's commit table
records `a7ca9cc2` as the layout shift only. `git show a7ca9cc2 -- docs/spec-testing_shift.md`
returns a real diff: the shipped-state summary `67b07f79` wrote described the **flat** layout
(`examples/fakeshop/library/`, `DJANGO_SETTINGS_MODULE = settings`) and was already stale four hours
later. So the spec's current body is not one commit's work but two, and the strictness-mode and
`Prefetch(...)` follow-up bullets that `## Remaining follow-ups` still carries were authored at
`a7ca9cc2`, not at the overwrite. Both matter to the entries below, so the row is corrected here
rather than left to the plan.

### Nothing was skipped in the code — re-derived, not accepted

[`BUILD.md`][build] `## Claims are proven mechanically, never accepted on prose` requires the plan's
verification pass to be re-derived rather than inherited. All ten rows reproduce. Three figures
beside them do not, and are corrected.

| # | Claim | Result | How it was re-derived |
|---|---|---|---|
| V1 | the test-only fixture app is gone | holds | `tests/fixtures` absent on disk; `grep -rn "TestsCardinalityConfig\|tests\.fixtures\|tests_cardinality"` over `*.py` / `*.ini` / `*.toml` / `*.md` returns **no live hit** — every hit is documentary |
| V2 | the `config/` + `apps/` layout exists | holds | `ls examples/fakeshop/config/` -> `schema.py`, `settings.py`, `test_settings.py`, `urls.py`, `wsgi.py`, `__init__.py`; `ls examples/fakeshop/apps/` -> six app packages |
| V3 | the seven models and their relation shapes are present | holds | `grep -n "^class " examples/fakeshop/apps/library/models.py` — all seven present among **11** classes; the eight shapes read off the field declarations (`Shelf.branch` FK / `Branch.shelves`, `Book.shelf` FK / `Shelf.books`, `Book.genres` M2M / `Genre.books`, `MembershipCard.patron` O2O / `Patron.card`, `Book.CirculationStatus` choices, `Book.subtitle` `null=True`) |
| V4 | the live acceptance suite exists at the named path | holds | `examples/fakeshop/test_query/test_library_api.py`, **192** test functions at `HEAD` |
| V5 | the eight live tests the card shipped survive by name | holds | `grep -c "def <name>("` -> 1 for each of the eight, against `git show HEAD:examples/fakeshop/test_query/test_library_api.py` (the working-tree copy is dirty with a concurrent session's edits) |
| V6 | both optimizer hints are still declared on an example type | holds | `examples/fakeshop/apps/library/schema.py` #"optimizer_hints = {\"book\": OptimizerHint.prefetch_related(), \"patron\": OptimizerHint.SKIP}" |
| V7 | the autouse reload fixture still exists under its name | holds, reshaped | `examples/fakeshop/test_query/conftest.py::_reload_project_schema_for_acceptance_tests` — the name survives, the scope and body do not; see the `## Live HTTP coverage` entry |
| V8 | the package-level tests said to remain are still there | holds | `tests/test_registry.py` 78 tests, `tests/optimizer/test_walker.py` 168, 34 `cache_key` references in `tests/optimizer/test_extension.py`, `tests/types/test_definition_order.py` 46 tests, `tests/utils/` 12 modules |
| V9 | "The original spec remains here as the design record" | **FALSE** | `67b07f79` deleted ten of the eleven `##` sections in the same commit that added the sentence. `git show 73004d74:… \| grep -c ''` -> **61** lines; the same at `67b07f79` -> **27** |
| V10 | `ctx.dst_optimizer_plan` still exists | holds | `tests/test_connection.py` #"plan = getattr(ctx, \"dst_optimizer_plan\", None)"; `tests/test_list_field.py` |

**Three figures beside the rows do not reproduce, and one clarifies.**

- The plan's V3 row says "the seven models and **nine** relation shapes the spec names". The spec
  names **eight**: forward FK, reverse FK, forward OneToOne, reverse OneToOne, forward M2M,
  reverse M2M, a choice field, and a nullable scalar field. There is no ninth. The finding is
  unaffected — all eight are present — but the number is wrong and would propagate.
- The plan calls the destroyed catalogue a "**ten-bullet** candidate catalogue". It is **8** bullets
  (`awk '/^## High-value/,/^## Tests that should/' | grep -c "^[A-Z]"` -> 8) carrying 37 candidate
  refs. Again the finding is unaffected.
- The plan's V1 row says the grep returns "9 hits, all documentary". It now returns roughly twice
  that. **The population is moving**, not the finding: the extra hits are two concurrent residual
  cycles' rationale files and artifacts written since the plan. This is why the row above states the
  live-hit count rather than the total.
- The plan's V9 evidence reads "-61/+27 lines". Read as line counts that is exactly right (61 before,
  27 after). Read as a `git diff --stat`, it is not: the stat is `25 insertions(+), 59 deletions(-)`.
  The row above states the line counts explicitly so the two cannot be confused.

**No code defect was found.** Everything spec-014 promised is present at `HEAD`. The whole of this
cycle's work is documentary.

## The recovered design record

Recovered in full from `git show 73004d74:docs/spec-testing_shift.md`. Ten sections, deleted in place
by `67b07f79`. Each is reproduced verbatim under its original heading, with a note on what it bears
on and — where the deliberation was later answered, contradicted, or overtaken — what actually
happened.

### `## Current state` — the survey the shift was argued from

Bears on [Problem statement][spec-014-problem].

> `docs/README.md` defines the shipped public surface as `DjangoType`, `finalize_django_types()`,
> definition-order-independent relation finalization, generated relation resolvers, and
> `DjangoOptimizerExtension`.
>
> `examples/fakeshop/test_query/README.md` reserves `examples/fakeshop/test_query/` for live GraphQL
> API tests that hit `/graphql/` through Django’s request stack, usually with
> `django.test.Client.post(...)`.
>
> The current fakeshop schema is still a placeholder in
> `examples/fakeshop/fakeshop/products/schema.py`, so the existing tests cannot simply be moved into
> `examples/fakeshop/test_query/` without first adding a real schema that uses the shipped surface.
>
> The current OneToOne and M2M tests depend on `tests.fixtures.apps.TestsCardinalityConfig` being
> registered from `examples/fakeshop/fakeshop/settings.py`, which works but mixes test fixture models
> into the example project. A real example app with its own models and schema would remove that
> pressure.

*What this establishes.* The shift was not a style preference. Two concrete blockers are named: the
example schema was a placeholder, so there was nothing to move tests *onto*; and the cardinality
fixtures reached the example project through its own settings, so package-test substrate and example
project were already entangled. The second is what card `DONE-014-0.0.4` was actually chartered to
fix, and the deleted survey is the only place that entanglement is stated as the reason.

*Note the path.* `examples/fakeshop/fakeshop/products/schema.py` — the project was doubly nested at
authoring time. The flattening and then the `config/` + `apps/` restructure both happened inside this
same card's day.

### `## Goals` — five, all met

Bears on [Problem statement][spec-014-problem].

> Move consumer-visible GraphQL behavior to IRL HTTP tests where possible.
>
> Use real Django models, real database tables, real schema import/finalization, the real Strawberry
> view, and real JSON responses.
>
> Keep fast package-level tests for narrow internals, invalid configuration, registry lifecycle,
> finalizer failure-atomicity, cache-key construction, and utility helpers.
>
> Reduce reliance on test-only model fixtures being loaded through the example project’s settings.
>
> Make the example project a durable proving ground for the currently shipped API, not only for
> future Layer 3 features.

*The fifth goal is the one that aged into a standing rule.* "A durable proving ground for the
currently shipped API" is now [`AGENTS.md`][agents]'s test-placement rule and its live-first
corollary — any line reachable via a real GraphQL query against fakeshop must be covered in
`examples/fakeshop/test_query/`. The 192 test functions in `test_library_api.py` at `HEAD`, against 8
at this card's own commit, are that goal compounding.

### `## Non-goals` — four, and one of them is why `## Remaining follow-ups` reads as it does

Bears on [Remaining follow-ups][spec-014-follow-ups].

> Do not remove all package tests. The unit/integration split should become sharper, not disappear.
>
> Do not force intentionally broken app states through `/graphql/` just to test internal failure
> paths.
>
> Do not activate unshipped Layer 3 API such as `DjangoConnectionField`, filters, orders, aggregates,
> fieldsets, permissions, or Relay nodes as part of this shift.
>
> Do not require full production readiness for the example project; the target is realistic framework
> acceptance coverage.

*This is the origin of the sentence the reconciliation had to fix.* The third non-goal is a scope
fence written when all seven features were unshipped, and the shipped-state summary carried it
forward as "remain non-goals for this slice and should land under their own specs" — which reads at
`HEAD` as a claim that they are still unshipped. Five have shipped. See the
`## Remaining follow-ups` entry.

*The second non-goal is a live constraint, not history.* It is why registry-failure, finalizer-
atomicity, and invalid-`Meta` coverage is package-level by contract rather than by convenience, and
the current spec's `## Package-level tests that intentionally remain` is its surviving statement.

### `## Proposed example app` — the design the `library` app was built to

Bears on [Shipped outcome][spec-014-shipped-outcome].

> Add a dedicated example app for shipped-surface testing. It can live inside the fakeshop project as
> a small app whose purpose is to exercise framework behavior through real models and a real schema
> without polluting the product-catalog example.
>
> The app should include models for these relationship shapes:
>
> A FK and reverse FK pair equivalent to `Category` and `Item`.
>
> A multi-hop FK graph equivalent to `Category`, `Item`, `Property`, and `Entry`.
>
> A OneToOne pair equivalent to `User` and `Profile`.
>
> An M2M graph equivalent to `Author`, `Book`, and `Tag`.
>
> A choice field and nullable field if the scalar/enum schema-shape tests are moved into IRL
> coverage.
>
> The schema should use only shipped APIs: `DjangoType`, `finalize_django_types()`,
> `DjangoOptimizerExtension`, normal Strawberry root fields, and root resolvers returning Django
> QuerySets. Type declarations should intentionally exercise awkward definition orders in at least
> one module so the schema proves finalization behavior at app import time.

*The mapping actually built.* `Branch`/`Shelf` is the FK pair; `Branch → Shelf → Book → Loan →
Patron` is the multi-hop graph (five hops, deeper than the four proposed); `Patron`/`MembershipCard`
is the OneToOne pair; `Book`/`Genre` is the M2M graph, collapsed from the proposed three models to
two because `Author` had no distinct cardinality to prove; `Book.circulation_status` and
`Book.subtitle` are the conditional choice and nullable fields, and the condition was met.

*The naming instruction was followed and is worth preserving.* "a small app whose purpose is to
exercise framework behavior ... without polluting the product-catalog example" is why the app is
`library` and not an extension of `products`, and it is the rule later cards kept: `scalars`,
`kanban`, `glossary`, and `accounts` are each a separate app for a separate framework surface rather
than more models bolted onto `products`.

*The last sentence is a live constraint the spec never carried.* "Type declarations should
intentionally exercise awkward definition orders in at least one module" is an instruction about how
the example schema must be written, not deliberation about whether to write it. It is the reason
`apps/library/schema.py` declares types out of dependency order, and a later editor tidying that
module into dependency order would silently retire the coverage. It is recorded here because it was
destroyed rather than because it is deliberation.

### `## Test placement rules` — three tiers, now four

Bears on [Package-level tests that intentionally remain][spec-014-package-level].

> Tests under `examples/fakeshop/test_query/` should hit `/graphql/` through
> `django.test.Client.post(...)` and assert HTTP status, GraphQL response JSON, and query counts
> where relevant.
>
> Tests under `examples/fakeshop/tests/` should continue to cover in-process schema execution,
> services, models, admin, commands, URLs, and project wiring that does not need HTTP.
>
> Tests under `tests/` should remain the home for package internals, direct helper tests, invalid
> Meta behavior, registry lifecycle, finalizer atomicity, optimizer cache-key construction, and tests
> that need monkeypatching or synthetic failure states.

*This is the direct ancestor of [`AGENTS.md`][agents] rule 7*, which is now the canonical statement
and carries **four** tiers rather than three: the per-app tier
`examples/fakeshop/apps/<app>/tests/` was split out of `examples/fakeshop/tests/` later, so each app
carries its own coverage and deleting an app loses only its tests. The rule also narrowed the
`examples/fakeshop/tests/` tier to project/config-level tests owned by no single app.

*Why the spec does not restate these rules.* They are standing-doc content, and a spec restating a
standing doc is a second source that drifts. The current spec states only the placement decisions
this card made; `AGENTS.md` owns the general rule.

### `## High-value migrations to HTTP tests` — the priority ordering, quoted verbatim

Bears on [Live HTTP coverage][spec-014-live-http] and [Remaining follow-ups][spec-014-follow-ups].

Quoted from the blob `73004d74:docs/spec-testing_shift.md`, fenced for the reason given in
`### Why the recovered catalogue is fenced rather than quoted inline`. **The line numbers are the
2026-05-07 state of files that have been rewritten many times since; they are historical evidence,
not navigational references.** Recover the source with:

```shell
git show 73004d74:docs/spec-testing_shift.md
```

```text
## High-value migrations to HTTP tests
Definition-order and relation traversal should move first. Candidate source tests include `tests/types/test_definition_order_schema.py:22`, `tests/types/test_definition_order.py:33`, `tests/types/test_definition_order.py:55`, and `tests/types/test_definition_order.py:122`. The HTTP replacement should query nested FK and reverse-FK paths and prove the schema works after real app import/finalization.
OneToOne and M2M should move out of the test fixture app. Candidate source tests include `tests/types/test_definition_order.py:77`, `tests/types/test_definition_order.py:96`, `tests/types/test_definition_order_schema.py:51`, and `tests/optimizer/test_definition_order.py:39`. The HTTP replacement should query both sides of OneToOne and M2M relationships using real tables.
Relation resolver correctness should become API behavior. Candidate source tests include `tests/types/test_resolvers.py:58`, `tests/types/test_resolvers.py:97`, and, if a no-optimizer endpoint or schema variant is useful, `tests/types/test_resolvers.py:398`.
Optimizer query-count behavior is the highest-value HTTP migration after relation traversal. Candidate source tests include `tests/optimizer/test_extension.py:51`, `tests/optimizer/test_extension.py:82`, `tests/optimizer/test_extension.py:118`, `tests/optimizer/test_extension.py:160`, `tests/optimizer/test_extension.py:201`, `tests/optimizer/test_extension.py:247`, `tests/optimizer/test_extension.py:328`, `tests/optimizer/test_extension.py:1275`, `tests/optimizer/test_extension.py:1309`, `tests/optimizer/test_extension.py:1381`, `tests/optimizer/test_extension.py:2018`, and `tests/optimizer/test_extension.py:2054`.
Consumer-shaped queryset behavior should be proven through HTTP once the example schema has root fields that intentionally return pre-shaped querysets. Candidate source tests include `tests/optimizer/test_extension.py:2277`, `tests/optimizer/test_extension.py:2319`, and `tests/optimizer/test_extension.py:2354`.
Optimizer hints can become HTTP tests if the example schema contains a type or root field configured with `OptimizerHint.SKIP` and `OptimizerHint.prefetch_related()`. Candidate source tests include `tests/optimizer/test_extension.py:1678` and `tests/optimizer/test_extension.py:1715`.
Manual relation override behavior should be proven by response data rather than Strawberry-internal resolver inspection. Candidate source tests include `tests/types/test_definition_order.py:174`, `tests/types/test_definition_order.py:201`, `tests/types/test_definition_order.py:230`, and `tests/optimizer/test_definition_order.py:146`.
Choice enum and scalar schema shape can move later if the new app includes appropriate fields. Candidate source tests include `tests/types/test_converters.py:105`, `tests/types/test_converters.py:233`, `tests/types/test_base.py:224`, `tests/types/test_base.py:305`, and `tests/types/test_base.py:317`.
```

*What the ordering bought, and what it cost.* Every one of the eight bullets has a matching live test
in the card's own eight-test shipment, in the declared order: definition-order traversal
(`test_library_branch_shelf_book_loan_graph_over_http`), OneToOne and M2M
(`…patron_card_and_genre_reverse_paths_over_http`), relation resolvers and the manual override
(`…relation_override_shapes_http_response_data`), optimizer query counts
(`…optimizer_selects_book_shelf_in_http_query`, `…reverse_fk_and_m2m_prefetch_sql_shape_over_http`),
consumer-shaped querysets (`…consumer_prefetched_queryset_cooperates_with_optimizer_over_http`),
optimizer hints (`…optimizer_hints_are_observable_over_http`), and choice enum plus nullable scalar
(`…choice_enum_and_nullable_subtitle_are_deliberate_http_contracts`). The catalogue was executed, not
merely written — which is precisely why deleting it left no trace anyone would notice.

*The cost is that the eight-way mapping was only re-derivable from history.* The shipped-state
summary lists the same coverage as an undifferentiated sentence, so nothing in the spec said which
package tests each live test was discharging, or that the migration had a declared priority at all.

### `## Tests that should stay package-level` — the keep-list, and the reason for each

Bears on [Package-level tests that intentionally remain][spec-014-package-level].

> Registry tests in `tests/test_registry.py` should stay under `tests/` because they directly
> validate registry state, idempotency, clear behavior, phase-1 failure atomicity, phase-3 partial
> mutation, and retry behavior.
>
> Configuration and error tests should stay under `tests/`, including missing/unknown Meta keys,
> invalid optimizer hints, unsupported fields, unresolved relation target errors, class-attribute
> shadowing, enum sanitization collisions, grouped choices, and nullable conversion edge cases.
>
> Optimizer internals should stay under `tests/`, including cache-key construction, directive
> variable collection, operation-name separation, eviction, `_resolve_model_from_return_type`,
> `_stash_on_context`, `_optimizer_active`, `plan_relation`, `FieldMeta.from_django_field`, and
> walker unit tests.
>
> Utility tests under `tests/utils/` should stay as unit tests.

*The spec's surviving one-sentence version is a lossy compression of this.* "Registry lifecycle,
finalizer atomicity, invalid Meta configuration, enum sanitization failures, unresolved targets,
optimizer cache-key construction, low-level walker behavior, and helper utilities" preserves the
categories and drops the **reason** attached to the first — that these tests validate state
transitions directly, which no wire response can observe. The reason is the load-bearing part: it is
the test that decides whether a *new* internal belongs package-level, and the compressed list cannot
answer that for anything not already on it.

*It is also the boundary the live-first corollary is measured against.* [`AGENTS.md`][agents]
requires live coverage for any line reachable from a real query; this list is the enumeration of what
is not so reachable, and the standing maintainer feedback to retire a package-only stand-in once a
live tier reaches the same line applies only outside it.

### `## Migration strategy` — additive first, retire second

Bears on [Shipped outcome][spec-014-shipped-outcome].

Fenced rather than blockquoted because it names a source path with an extension that reads as a
reference; the file it names no longer exists.

```text
## Migration strategy
Start by adding the real example app and schema without deleting existing package tests. The first HTTP tests should be additive and should cover a narrow end-to-end path: seed data, POST to `/graphql/`, nested relation response, and query count.
Once an HTTP test proves the same public behavior more realistically, downgrade the corresponding package test to a smaller internal assertion or remove the duplicate if it no longer adds unique value.
Move OneToOne and M2M off `tests.fixtures.cardinality_models.py` only after the new example app has real migrations and HTTP coverage for both relationship shapes.
Keep package tests that assert exact annotation objects or registry internals until an equivalent internal contract is intentionally no longer needed.
```

*This is the sequencing the four commits actually followed*, and it is the answer to the obvious
alternative — delete the fixture app first, then build the replacement. That alternative was rejected
here in advance, in the third sentence: the fixture app comes out only *after* the real app has
migrations and live coverage for both cardinalities. `73004d74` added the app and the first live
suite; `1057ddc2`, forty-six minutes later, removed the fixtures. The order was not incidental.

*The second sentence is the origin of a recurring maintainer instruction.* "Downgrade the
corresponding package test ... or remove the duplicate if it no longer adds unique value" is the
live-first retirement rule, still applied whenever a package-only stand-in is superseded by a live
test.

### `## Validation expectations` — the modest one

Bears on [Live HTTP coverage][spec-014-live-http].

> The new HTTP test layer should run with `pytest` and Django’s test database, using
> `django.test.Client` against `/graphql/`.
>
> Focused validation for each migration should include the new `examples/fakeshop/test_query/` tests
> plus the package tests most likely to be affected by schema/finalization changes.
>
> Release validation should continue to run the full suite when explicitly requested.

*Nothing here was contradicted; it was outgrown.* The second sentence's "package tests most likely to
be affected by schema/finalization changes" is a hand-picked focused scope, and the repo has since
learned that this class of staleness is structurally invisible below a full parallel run — an omitted
schema module strands types across a `registry.clear()` and fails order-dependently. [`BUILD.md`][build]
`### Example-project schema changes must sync every schema-module list` is the current rule and
requires the full sweep, not a focused selection. The recovered sentence is preserved because it
records that the hand-picked-scope approach was tried and found insufficient, which is why the
current rule is written as an absolute.

### `## Risks and open decisions` — four, all four now closed

Bears on [Settled decisions][spec-014-settled].

> The new app needs a name and placement. A small app under the fakeshop project is simplest, but the
> name should make clear that it is a framework acceptance app rather than the product-catalog
> example.
>
> The schema needs to call `finalize_django_types()` exactly once after importing all example
> `DjangoType`s. This may require tightening registry isolation in tests so package tests and example
> schema imports do not fight over global state.
>
> HTTP query-count assertions may include request-stack overhead if authentication, middleware, or
> GraphQL view behavior changes. The tests should count only database queries and avoid brittle
> assumptions about non-ORM work.
>
> Plan-introspection assertions through `ctx.dst_optimizer_plan` do not naturally survive HTTP JSON
> responses. Those should usually remain package-level unless a deliberate debug field or test-only
> extension is introduced, which is not recommended for the first migration.

**This section is the single most valuable recovery in the file**, because the spec's
`## Settled decisions` states all four resolutions and none of the risks they resolve. A settled
decision with its risk deleted reads as an arbitrary preference.

- **Risk 1 → the app name.** The resolution "`apps.library` under the example project's `apps/`
  package" is the answer to "the name should make clear that it is a framework acceptance app rather
  than the product-catalog example". Without the risk, the name looks like taste.
- **Risk 2 → the finalization seam, and it predicted the fixture that exists today.** "This may
  require tightening registry isolation in tests so package tests and example schema imports do not
  fight over global state" is precisely the collision `_reload_project_schema_for_acceptance_tests`
  exists to prevent, and the spec's surviving "the fixture is load-bearing" sentence is the
  conclusion with the premise removed. The risk was correct and understated: the fixture has since
  grown from a per-test full reload into a module-scoped rebuild over six app schema modules plus a
  function-scoped identity-fingerprint guard.
- **Risk 3 → the `CaptureQueriesContext` decision.** "Count only database queries and avoid brittle
  assumptions about non-ORM work" is the reason the settled decision says *broad SQL shape rather
  than fragile full SQL strings*. It is also a live constraint on anyone adding an assertion to the
  suite, and it was deleted.
- **Risk 4 → the plan-introspection deferral, whose premise has since changed.** The recovered text
  says plan introspection stays package-level "unless a deliberate debug field or test-only extension
  is introduced, **which is not recommended for the first migration**". A test-only extension was
  later introduced — `DjangoDebugExtension`, shipped `0.0.14` — so the disqualifying condition no
  longer holds. See the `## Remaining follow-ups` entry.

## Entries keyed to the spec

### `## Status` — a sentence that was false on the day it was written

Spec: [Status][spec-014-status].

*Moved.* The spec carried:

> Implemented for the 0.0.4 testing-shift slice. The original spec remains here as the design record,
> but this document now describes the shipped state and the remaining follow-up surface.

The claim is false, and its falsity is not drift. `67b07f79` is the commit that added the sentence
**and** the commit that deleted the ten sections the sentence says survived, in one diff: 61 lines
in, 27 lines out. A reader trusting it would conclude the design record was available and stop
looking.

*The cost is measurable.* This spec's rationale companion did not exist until this cycle, and the
reason it did not is this sentence — it told every subsequent reader, including three prior residual
cycles that swept these archived specs, that the deliberation was already in the file. The absent
companion in `## Provenance of this record` is a direct consequence.

*The alternatives rejected.*

- **Correct the sentence in place** — "the original spec was replaced by this summary; see git
  history". Rejected: that is a spec narrating its own history, which [`BUILD.md`][build]
  `## Spec rationale extraction` forbids outright, and it leaves the record still only in git.
- **Restore the ten sections to the spec.** Rejected: the spec is a contract, and eight of the ten
  sections are deliberation, candidate catalogues, and strategy — exactly the layer the extraction
  rule moves out. Restoring them would rebuild the very shape the rule exists to prevent, and would
  re-introduce 37 `path:NN` refs into a standing doc.
- **Recover the record into the rationale companion and leave `## Status` as a present-tense
  shipped statement with a pointer.** Adopted. The record is preserved where deliberation belongs,
  the spec keeps its one-line pointer as [`worker-1.md`][worker-1] rule 1 requires, and no reader is
  told a false thing about where to look.

*Claim the spec may no longer make.* That it contains, or preserves, the original design record.

### `## Problem statement` — past-tense narration of a live contract

Spec: [Problem statement][spec-014-problem].

*Nothing moved.* The section said "The desired shift **was** to keep low-level package tests for
internals while moving public GraphQL behavior into live example-project API tests", which reads as a
record of a past intention rather than a statement of the current rule. It is the current rule — it
is [`AGENTS.md`][agents] rule 7 and its live-first corollary — so it is stated in the present.

The rewrite also folds in the concrete reason the recovered `## Current state` gave and the summary
dropped: an unmanaged fixture model has no table, so its relation edges could only ever be asserted
as annotation shape and never resolved through a query. That is implementation-relevant rationale by
[`worker-1.md`][worker-1]'s carve-out — it is why the shift was necessary rather than merely
tidier — so it belongs in the spec, not here.

*The alternative rejected.* **Move the whole problem statement here and leave the spec starting at
`## Shipped outcome`.** Rejected: a contract with no statement of the problem it solves cannot be
checked for scope, and `## Non-goals`-style fencing has nothing to attach to.

### `## Implemented outcome` → `## Shipped outcome` — four claims, three of them falsified

Spec: [Shipped outcome][spec-014-shipped-outcome].

The heading was renamed. "Implemented outcome" pairs with the false `## Status` framing (this is what
the implementation produced, as of then); "Shipped outcome" states what is true. No inbound link or
in-page anchor pointed at the old heading — `grep -rn "spec-014-testing_shift"` across the tree
returns only whole-file references from [`KANBAN.md`][kanban] and this cycle's own artifacts — so the
rename breaks nothing.

**Claim 1 — the schema construction.** The spec said the project schema "then constructs
`strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])`". At `HEAD`
(`examples/fakeshop/config/schema.py` #"schema = DjangoSchema(") it constructs:

```python
schema = DjangoSchema(
    query=Query,
    mutation=Mutation,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
```

Four separate later contracts, each with its own cause commit, none of them spec-014's:

| Element | Cause | The contract it carries |
|---|---|---|
| `DjangoSchema` instead of `strawberry.Schema` | `1b06c39e` (2026-07-15) | generated mutations' write transactions must span GraphQL response completion; the write pipeline refuses to run under a plain `Schema` |
| `mutation=Mutation` | `00618519` (2026-06-17) | the example project's write surface |
| `config=strawberry_config()` | `b1a6d01f` (2026-05-27), reworked `23cb569a` / `46ffc64f` (2026-06-05) | the package's schema-config factory |
| `extensions=[lambda: _optimizer]` | `23cb569a` (2026-06-05) | a module-level singleton wrapped in a factory, so the instance-bound optimizer plan cache survives per-request extension construction and `Schema.__init__` emits no instance-deprecation warning |

*The alternative rejected.* **Restate the current constructor call verbatim in the spec.** Rejected
for the reason the drift itself demonstrates: a spec that transcribes a line owned by four other
specs is a second source of truth for all four, and it will be wrong again at the next change to any
of them — this exact sentence has now been wrong twice. The reconciled spec instead states the
invariant spec-014 actually owns (finalize exactly once, after all example `DjangoType`s are
imported, before the schema object is constructed; exactly one `DjangoOptimizerExtension` instance
serves the schema) and explicitly assigns the rest of the call to its owners. That claim is stable
under all four later contracts and remains checkable.

**Claim 2 — `pytest.ini`.** The spec said `DJANGO_SETTINGS_MODULE = config.settings`. At `HEAD` it is
`config.test_settings`, since `a9fa8c34` (2026-07-10, "test+ci: speed up and harden the fakeshop test
tier"), which introduced `examples/fakeshop/config/test_settings.py` as a pytest-only layer over the
shipped settings. `git log -S"config.test_settings" -- pytest.ini` returns that commit alone. The
`pythonpath = examples/fakeshop` half of the claim is unchanged and survives verbatim, including its
deliberate negative — that `examples/fakeshop/apps` is *not* added directly, which is what makes
`apps.library` the import path rather than `library`.

**Claim 3 — two domain apps.** The spec named `apps.products` and `apps.library`. `ls
examples/fakeshop/apps/` returns six packages. Each addition traced with
`git log --diff-filter=A`:

| App | Landed at | What it exists for |
|---|---|---|
| `scalars` | `2701eb88` (2026-05-27) | paired-model converter coverage substrate |
| `kanban` | `d346a45e` (2026-05-29) | dogfoods `DjangoType` + filters on the board data |
| `glossary` | `f9ebb9fa` (2026-06-01) | the glossary subsystem the rendered `docs/GLOSSARY.md` is built from |
| `accounts` | `5bd246aa` (2026-07-02) | the session-auth surface; it carries no `models.py` at all, using `django.contrib.auth`'s |

*The alternative rejected.* **Update the spec to enumerate all six.** Rejected: five of the six are
not this card's, so enumerating them would credit spec-014 with four later cards' substrate — the
same over-crediting [`spec-013`][spec-013-rationale]'s reconciliation had to fence off in
`apps/library/models.py`. The spec now states that it establishes `apps.products` and `apps.library`
there and fences the rest as later cards'. That claim stays true no matter how many apps are added.

**Claim 4 — the seven models.** This claim is *true* and stays, but it was unfenced. The spec named
`Branch`, `Shelf`, `Genre`, `Book`, `Patron`, `MembershipCard`, `Loan` as though they were the
module's content. `grep -c "^class "` returns **7** at `73004d74` and **11** at `HEAD`. The four
additions, each traced with `git log -S<symbol> --follow -- examples/fakeshop/apps/library/models.py`:

| Later addition | Landed at | What it exists for |
|---|---|---|
| `TaggedItem` (+ `Branch.tags` `GenericRelation`) | `d592ac3a` (2026-05-08) | unsupported-relation error handling in annotation building |
| `Periodical`, `Issue` | `51421e54` (2026-07-10) | keyset value-encoded cursors (`Meta.cursor_field`) |
| `ProxyBranch` (+ `proxy_tags`) | `41008e4c` (2026-07-17) | proxy-model content-type resolution under non-default `for_concrete_model` |

Field-level growth inside the seven named models is later cards' too —
`Patron.lifetime_fines_cents` (the `BigIntegerField → BigInt` converter) and `Shelf.alt_branches` (a
second M2M edge, for raw-pk relation input on the write side). The reconciled spec therefore claims
"seven of its models" and fences every other class **and field** in the module as outside scope. The
field clause is deliberate: a class-only fence would leave a reader crediting this card with
`alt_branches`, which is the second M2M edge in a module whose one in-scope M2M is `Book.genres`.

*Claims the spec may no longer make.* That the served schema is a plain `strawberry.Schema` with a
bare extension instance; that `DJANGO_SETTINGS_MODULE` is `config.settings`; that `apps/` holds two
app packages; that `apps/library/models.py`'s current content, its generic relations, its proxy
model, its second M2M, its `BigInt` field, or its keyset substrate are this card's.

### `## Live HTTP coverage` — the fixture kept its name and lost its shape

Spec: [Live HTTP coverage][spec-014-live-http].

The spec described the autouse fixture as one that "clears the registry, reloads `apps.library.schema`,
reloads `config.schema`, reloads `config.urls`, and clears URL caches". Every verb is still performed
somewhere; none of it is performed the way the sentence says, and the sentence's implicit contract —
a per-test full reload of one app's schema — is the part that is wrong.

At `HEAD`, reworked at `a9fa8c34` (2026-07-10):

- The reload logic is **single-sited** in `examples/fakeshop/schema_reload.py`, not in the fixture.
  `reload_all_project_schemas()` clears the registry, then re-imports or reloads
  `_PROJECT_APP_SCHEMA_MODULES` — **all six** app schemas, in a dependency-safe order — then calls
  `reload_project_schema_shell()`, which reloads `config.schema` and `config.urls` and clears
  Django's URL caches.
- `_reload_project_schema_for_acceptance_tests` is **module-scoped**, not function-scoped, and its
  body is one call. It runs the full rebuild once per module per worker.
- A separate **function-scoped** autouse guard,
  `_isolate_project_schema_for_acceptance_test`, does the per-test work: it fingerprints app
  registrations by `id()` over `registry._pending` and the six schema modules, rebuilds only the
  schema and URLconf shell, asserts the shell reload did not mutate registrations, and on teardown
  re-runs the full rebuild if the test did mutate them.

*Why it changed.* Two pressures the original could not have anticipated. The six-app enumeration is
[`BUILD.md`][build] `### Example-project schema changes must sync every schema-module list` in
practice — reloading only `apps.library.schema` leaves the other five stranded-registered across a
`registry.clear()` and produces order-dependent `DuplicatedTypeName` / `LazyType KeyError` at the
aggregate schema build, a failure class invisible below the full parallel run. The scope split is
cost: `a9fa8c34` is a test-tier speed-up commit, and a full six-module reload per test was the
expense it removed.

*The alternative rejected.* **Describe the fixture generically — "an autouse fixture rebuilds project
schema state" — and name no mechanism.** Rejected: the mechanism is the contract here. The
single-siting is what stops a seventh app being added to one list and not another, and the
identity-fingerprint guard is what makes the cheap per-test path safe. A generic sentence would let a
future editor collapse the pair back into one per-test full reload, or into one per-module reload
with no guard, and read the spec as permitting it.

*Claim the spec may no longer make.* That the autouse fixture performs a per-test registry clear and
reloads one app's schema module; that the reload logic lives in the fixture rather than in
`schema_reload.py`; that only `apps.library.schema` is reloaded.

### `## Resolved risks and decisions` → `## Settled decisions` — a rename, and a restored premise

Spec: [Settled decisions][spec-014-settled].

The four resolutions are all still true and all four stay verbatim. Two changes:

- **The heading was renamed.** "Resolved risks and decisions" implies a chronology — there were
  risks, then they were resolved — and the risks it refers to were deleted from the document, so the
  heading pointed at nothing. "Settled decisions" states what the section is. No inbound reference
  pointed at the old anchor.
- **The risks the four decisions answer are recovered above**, in the recovered-record entry for the
  original `## Risks and open decisions` section. That is the whole content of this entry: the spec keeps the
  conclusions, this file keeps the premises, and the recovered section is the only place the pairing
  is legible.

*Claim the spec may no longer make.* None. All four resolutions hold at `HEAD`.

### `## Remaining follow-ups` — one claim falsified, one premise changed, one still correct

Spec: [Remaining follow-ups][spec-014-follow-ups].

**The Layer-3 sentence was falsified.** The spec said filters, orders, aggregates, fieldsets,
permissions, Relay nodes, and `DjangoConnectionField` "remain non-goals for this slice and should
land under their own specs". Five of the seven have landed:

| Feature | Shipped | Where |
|---|---|---|
| filters (`FilterSet`, `RelatedFilter`, the filter primitives) | `0.0.8` | [`CHANGELOG.md`][changelog] `## [0.0.8]` |
| orders (`OrderSet`, `RelatedOrder`, `Ordering`) | `0.0.8` | same |
| Relay nodes (`DjangoNodeField` / `DjangoNodesField`) | `0.0.9` | `## [0.0.9]` |
| `DjangoConnectionField` | `0.0.9` | same |
| permissions | `0.0.8` and `0.0.10` | the `check_<field>_permission` filter/order gates at `0.0.8`; `apply_cascade_permissions` / `aapply_cascade_permissions` cascade visibility at `0.0.10` |

Aggregates and fieldsets are still ahead, carded on the beta line: `FieldSet` at
`TODO-BETA-054-0.1.1` and the aggregation subsystem at `TODO-BETA-057-0.1.3` in
[`KANBAN.md`][kanban].

*Note the permissions row is not a single version.* The spec's flat list treats "permissions" as one
feature; it shipped in two independent pieces two releases apart. The reconciled spec does not
attempt to version any of them — versions belong to those specs and to `CHANGELOG.md`, and repeating
them here is how this sentence got stale in the first place.

*The alternative rejected.* **Update the sentence to say which shipped when.** Rejected on the
extraction rule: a spec listing five other features' release versions is narrating a history that is
not its own and will drift with every one of them. The reconciled sentence states only what is
durably true — these features are outside this spec's scope, each owned by its own spec, alpha line
for five and `0.1.x` beta line for two — and the version table lives here.

**The strictness-mode bullet's premise changed; its disposition did not.** The spec's condition for
moving [strictness-mode][glossary-strictness-mode] coverage to the live tier was "only if a debug
header, test-only extension, or other consumer-visible response surface exposes the planned-key
state". `DjangoDebugExtension` shipped at `0.0.14` (`django_strawberry_framework/extensions/debug.py`)
and is exactly such a surface: a `SchemaExtension` writing captured SQL and resolver exceptions into
the response's `extensions.debug` map. The recovered `## Risks and open decisions` shows the original
deliberation went further than the spec's summary — it said a test-only extension was "not
recommended for the first migration", a disqualification that has since expired.

The **disposition** is unchanged and was verified, not assumed: strictness has no live-tier
assertion. `grep -rni "strictness" examples/fakeshop/test_query/` returns two hits, both incidental
comments inside `test_library_api.py`, neither an assertion. So the reconciled bullet states the
current contract — coverage is package-level, the enabling surface exists, the migration is available
to a future slice rather than blocked — and the premise change is recorded here.

*The alternative rejected.* **Delete the condition now that it is met.** Rejected: the condition is
the specification of what a valid live strictness test would have to do (observe planned-key state
through a consumer-visible response surface, not by reaching into internals). Deleting it would leave
a future slice free to satisfy the follow-up with an internals-inspecting live test, which is the one
shape the original deliberation ruled out.

**The `Prefetch(...)` deferral still holds, and was verified so it would not be "fixed".**
`grep -rn "Prefetch(" examples/fakeshop/test_query/` returns two hits, both inside docstrings in
`test_scalars_api.py` describing what the optimizer plans internally. No live-tier file constructs a
`Prefetch` object, and the two consumer-cooperation live tests use plain `prefetch_related(...)`. The
bullet is restated in the present tense with the verification made explicit — "no live-tier test
constructs one" — so the next reader can re-derive it in one grep instead of re-reasoning it.

*Claims the spec may no longer make.* That filters, orders, permissions, Relay nodes, or
`DjangoConnectionField` are unshipped or awaiting their own specs; that no consumer-visible surface
exposes planned-key state.

## Reconciliation record — what the spec now says, and why

### The strategy, and what it rejected

The spec is a **contract for the test-placement shift**, and every rewrite below was made to satisfy
one test: *can a reader check this sentence against `HEAD` today, and will it still be checkable
after the next unrelated card touches the same file?* Two shapes were rejected wholesale.

- **Transcribing current implementation detail.** Rejected wherever the detail is owned by a later
  spec — the schema constructor call, the app list, the model list, the Layer-3 versions. Each was
  the source of a drifted claim, and each would drift again. The spec states the invariant it owns
  and fences the rest.
- **Any narration of the change.** No amendment block, no "as of", no "previously", no chronology.
  [`BUILD.md`][build] `## Spec rationale extraction`: a reader must never have to apply a history to
  the spec to learn what is currently true. The one place this bit hardest is
  `## Remaining follow-ups`, where the honest-looking fix ("these have since shipped") is exactly the
  forbidden shape; the accepted fix drops the temporal frame entirely.

### Section by section

| Section | Change |
|---|---|
| `## Status` | the false design-record claim replaced by a present-tense shipped statement plus the one-line rationale pointer |
| `## Problem statement` | past-tense narration rewritten present-tense; the unmanaged-fixture reason recovered from `## Current state` folded in as implementation-relevant rationale |
| `## Implemented outcome` → `## Shipped outcome` | renamed; model list fenced to "seven of its models" with classes **and fields** outside it excluded; app list fenced to the two this spec establishes; `DJANGO_SETTINGS_MODULE` corrected to `config.test_settings` with its pytest-only-layer role stated; the constructor transcription replaced by the finalize-once + one-extension-instance invariant plus an explicit assignment of the rest to later specs |
| `## Live HTTP coverage` | the fixture paragraph rewritten to the `schema_reload.py` single-siting, the six-module dependency-safe rebuild, the module-scoped autouse fixture, and the function-scoped identity-fingerprint guard; the coverage sentence re-framed as "the coverage this spec ships" so the suite's later growth is not claimed |
| `## Package-level tests that intentionally remain` | unchanged in substance; "now use" de-tensed to "use" |
| `## Resolved risks and decisions` → `## Settled decisions` | renamed; all four resolutions verbatim |
| `## Remaining follow-ups` | strictness bullet restated with its condition intact and the enabling surface named; `Prefetch(...)` bullet restated present-tense with its verification made explicit; the Layer-3 sentence rewritten as a scope fence with no temporal frame |

### The link scaffold

The spec's ten canonical group headers and its seven `<!-- docs/ -->` glossary definitions are
unchanged. One definition was added, `[spec-014-rationale]` under `<!-- docs/SPECS/ -->`, resolving
to `appx/spec-014-testing_shift-0_0_4-rationale.md` from the spec's own directory —
verified to exist on disk. This file's own definitions resolve from `docs/SPECS/appx/`: `../../../`
to the repository root, `../../` to `docs/`, `../` to `docs/SPECS/`, and a bare filename to a sibling
under `appx/`. Each was disk-checked from this directory rather than assumed, because a same-named
file one level up silently masks a depth error.

### What this cycle deliberately did not fix

- **The rendered `DONE-014-0.0.4` card body carries a duplicate `#### Scope` bullet** — a fourth
  bullet restating its first three, the identical defect `DONE-011-0.0.4` and `DONE-013-0.0.4` carry.
  [`KANBAN.md`][kanban] is generated from `examples/fakeshop/db.sqlite3`, so the fix is an ORM edit
  plus a regenerate, never a hand-edit; the database is dirty at this cycle's baseline with a
  concurrent session's uncommitted work, and regenerating would publish rows that have not landed.
  **Superseded outright by the two passes below.** The blocker cleared mid-cycle, the sibling cards
  were fixed at `6f8bf818`, and the defect itself was then fixed here — see
  `### The board defect, re-derived` and `## Closing record — the board defect is fixed`. The
  mechanism stated in this bullet's original form (a rendered `description` column) was also wrong:
  the board's `Card` model has no `description` field at all.
- **`docs/builder/DONE/build-008-definition_order_independence-0_0_4.md` cites this spec for an
  object it does not own** — almost certainly rot from the card renumber. It is a closed cycle's
  archived artifact, outside this cycle's writable set, and recorded rather than fixed.
  **Re-derived and closed by the audit pass below; see
  `### The build-008 citation is a record of a fixed defect, not live rot`.**

## Audit record — the adversarial re-derivation pass

Appended by the documentation-completion and archive-audit pass, which re-derived every claim in the
reconciled spec at `HEAD` from an adversarial vantage: it did not write the reconciliation and had no
memory of why any sentence was there. The seven models and their eight relation/field shapes, both
out-of-scope fences, the finalize-once seam, the one-`DjangoOptimizerExtension`-instance claim, every
clause of the `schema_reload.py` / `conftest.py` description, seven of the eight live-tier coverage
items, the `CaptureQueriesContext` practice, the `ctx.dst_optimizer_plan` deferral, and both
`## Remaining follow-ups` bullets held exactly as written. Three claims did not, and one item R1
forwarded turned out to be already closed.

### `## Live HTTP coverage` — the forward-FK claim was falsified by a later visibility contract

Spec: [Live HTTP coverage][spec-014-live-http].

*The claim as reconciled.* The coverage sentence listed "forward FK `select_related`" among the
shapes the card's live tier proves — which is what
`test_library_optimizer_selects_book_shelf_in_http_query` asserted when the card shipped: a single
joined query.

*What the test asserts at `HEAD`.* `len(captured) == 2`, `library_book` in the first query and
`library_shelf` in the second, under a comment stating that `ShelfType.get_queryset` implements the
nested-visibility contract so the optimizer "correctly downgrades `select_related("shelf")` to
Prefetch so the visibility hook applies before the join surfaces hidden rows." The assertion flipped
at `1694bd2e` (2026-05-28), the same commit that flipped the sibling claim in
[`spec-013`][spec-013-rationale]; `ShelfType.get_queryset` is declared in
`examples/fakeshop/apps/library/schema.py`.

*Why this is a correction and not a code defect.* The downgrade is the package's documented rule — a
relation whose target type declares a custom `get_queryset` cannot be served by a join, because the
join would surface rows the hook excludes. The forward FK is still *planned* as `select_related`;
what changed is what the planner is allowed to execute. The card's edge is intact and still pinned
over HTTP.

*The alternatives rejected.*

- **Drop the shape from the list and let the package tier carry the forward FK.** Rejected: the
  card's contract is that this edge is proven over the wire, and [`AGENTS.md`][agents] rule 10 wants
  it there. Deleting a claim to avoid restating it hides the edge rather than fixing the sentence.
- **Say only "forward FK traversal".** Rejected: a claim vague enough never to be falsified is also
  one no reader can check, which is the failure mode this whole cycle exists to close.
- **Record the flip as history.** Rejected — [`BUILD.md`][build] `## Spec rationale extraction`
  forbids chronology in the contract. The flip is here; the spec states the observable shape.

*Claim the spec may no longer make.* That `Book.shelf` is served as a `select_related` join over
HTTP. It is planned as one and executed as a visibility-scoped `Prefetch`.

*The lesson, restated because this is the second consecutive cycle to hit it.* Naming a test by
`path::QualifiedName` proves the symbol survives, never that the sentence describing it survives. A
test that keeps its name while its assertion is inverted is invisible to a name-existence sweep.
Every other claim in this spec was checkable by grep; this one was reachable only by reading the
body against the sentence.

### `## Settled decisions` — a live constraint that lived only in this file

Spec: [Settled decisions][spec-014-settled].

*The gap.* The recovered `## Proposed example app` section closes with an instruction — "Type
declarations should intentionally exercise awkward definition orders in at least one module so the
schema proves finalization behavior at app import time" — and R1 correctly identified it as a live
constraint rather than deliberation, but recorded it **only here**. A constraint on how a module must
be written is normative, so by [`worker-1.md`][worker-1]'s carve-out it belongs in the contract; a
rationale companion is the one place a future editor will not look before tidying an import-ordered
module. That is a reconciliation gap, and it is closed: the spec now states the non-dependency
declaration order of `examples/fakeshop/apps/library/schema.py` as a contract on the module.

*Verified at `HEAD`, not inherited.* The module declares `LoanType` (which annotates `Book` and
`Patron`) ahead of both `BookType` and `PatronType`, `ShelfType` ahead of `BranchType`, and
`MembershipCardType` ahead of `PatronType`. Two of those classes carry the original docstrings saying
so ("Shelf declared before Branch to exercise FK finalization", "Card declared before Patron to
exercise OneToOne finalization"), which is corroboration rather than the contract.

*The alternative rejected.* **Leave it in the rationale and rely on the two class docstrings.**
Rejected: a docstring on `ShelfType` cannot stop an editor reordering the module, because the editor
who reorders is exactly the one who reads the order as an accident to be tidied. The constraint has
to be stated where the contract is, naming the consequence — the coverage retires silently, with no
test failing.

*Claim the spec may no longer make.* None; this is an addition, not a retraction. The
`CaptureQueriesContext` broad-SQL-shape rule, R1's other recovered live constraint, was already
carried as contract in this same section and needed no change.

### `## Remaining follow-ups` — "each owned by their own spec" overstated one of seven

Spec: [Remaining follow-ups][spec-014-follow-ups].

*The claim as reconciled.* Layer-3 features "are each owned by their own spec". Six of the seven are:
filters `spec-027`, orders `spec-028`, `DjangoConnectionField` `spec-030`, Relay nodes `spec-032`,
permissions `spec-034`, fieldsets `spec-054`. **Aggregates has no spec authored** — `ls
docs/SPECS/ | grep -i aggregat` returns nothing; it is carded as `TODO-BETA-057-0.1.3` in
[`KANBAN.md`][kanban] and referenced there as an amendment obligation on the graph-substrate card.

*Why it was worth an edit.* The sentence's job is to route a reader who asks "who owns this?" to the
owner. For aggregates it routes them to a document that does not exist, which is the same defect
class as the `## Status` sentence R1 removed — a pointer at nothing. The fix is one clause: each
feature is owned by its own spec, or by its own card where no spec is authored yet.

*The alternative rejected.* **Name the card ids in the spec.** Rejected on the same ground the
Layer-3 version table was rejected: a card id is another spec's identifier, it moves under the board
renumber, and repeating it here creates a second source that drifts. The routing statement stays
generic; the card id lives in this file.

*Claim the spec may no longer make.* That every Layer-3 feature it fences off already has a spec of
its own.

### The build-008 citation is a record of a fixed defect, not live rot

R1 forwarded `docs/builder/DONE/build-008-definition_order_independence-0_0_4.md` as citing spec-014
for an object it does not own, to be routed to the deferred-work catalog. Re-derived: **nothing is
owed, and nothing should be routed.**

The artifact does not itself misattribute. Its `#### Maintainer decision 4` *records* that two source
comments — in `types/relations.py` and `types/base.py::_build_annotations` — wrongly cited spec-014
for the `PendingRelation` scaffolding and the import-order trap, correctly reassigns them to
`spec-010` and `spec-018`, and dispatches item R2b to fix them. That item is ticked `- [x]` in the
artifact's checklist, and the fix landed: `git grep -n "spec-014" HEAD -- django_strawberry_framework/`
returns **nothing**, while `types/relations.py` now cites `spec-010` and `spec-018` and
`types/base.py` cites `spec-018`. The artifact is a closed cycle's accurate record of a defect that
no longer exists. Deferring it would have carried a phantom into the catalog.

*The lesson.* A forwarded item is a claim like any other. "An archived artifact cites spec-014" is a
grep result; "for an object it does not own" is the sentence, and reading the surrounding section
showed the artifact was the thing that fixed it.

### The board defect, re-derived — the deferral's stated reason is stale

The duplicate `#### Scope` bullet on the rendered `DONE-014-0.0.4` card was real when this audit ran:
the card rendered four scope bullets, the fourth a lowercase one-line restatement of the first three.
(It was fixed later in the same cycle — `## Closing record — the board defect is fixed`.) Two things
said about it above no longer hold, and are corrected here so the next cycle does not carry them
forward.

- **The sibling cards no longer carry it.** The maintainer removed the equivalent row from
  `DONE-011-0.0.4` and `DONE-013-0.0.4` at `6f8bf818` (2026-08-16), whose message names the mechanism
  exactly: "a third `CardItem` restating the two above it, which the renderer emitted because it
  builds sections from card items alone." Both now render two scope bullets. `DONE-014-0.0.4` is the
  **last** card carrying the defect, and `6f8bf818` is the worked precedent for fixing it.
- **The dirty-database blocker has cleared.** `examples/fakeshop/db.sqlite3`, [`KANBAN.md`][kanban],
  and `KANBAN.html` are all clean at the audit pass's baseline. The deferral stands only because this
  cycle's dispatch forbids any database write and any generator run outright.

The defect is a stray `kanban.CardItem` row on the card's `scope` section — not a rendered column, as
the cycle's build plan supposed. The renderer builds each section purely from its card items, so a
stray row appears as a bullet; the fix is to delete that one row through the ORM, locating it by
text rather than by primary key, and regenerate both board exports.

### What the audit confirmed unchanged

Recorded so the next cycle re-derives rather than re-argues these.

- **The seven models are exactly the card-era set.** `git show
  73004d74:examples/fakeshop/library/models.py | grep -c "^class "` -> **7**, and they are `Branch`,
  `Shelf`, `Genre`, `Book`, `Patron`, `MembershipCard`, `Loan`. All seven survive at `HEAD` among 11
  classes.
- **All eight relation/field shapes are real edges or columns on those seven.** Forward FK
  `Shelf.branch` / `Book.shelf` / `Loan.book` / `Loan.patron`; reverse FK `Branch.shelves` /
  `Shelf.books` / `Book.loans` / `Patron.loans`; forward OneToOne `MembershipCard.patron`; reverse
  OneToOne `Patron.card`; forward M2M `Book.genres`; reverse M2M `Genre.books`; choice field
  `Book.circulation_status`; nullable scalar `Book.subtitle`.
- **Both fences are accurate.** `apps/products` and `apps/library` were both created by this card's
  own `a7ca9cc2` (`git log --diff-filter=A` on each package's `__init__.py`); the other four apps are
  `2701eb88`, `d346a45e`, `f9ebb9fa`, `5bd246aa`. The four extra model classes and the two extra
  fields are all later, as the tables above record.
- **`finalize_django_types()` is called once, in the right place.** In
  `examples/fakeshop/config/schema.py` it sits after all six app schema imports and above the
  `DjangoSchema(...)` construction. **The one-instance claim is not falsified by the factory form**:
  `extensions=[lambda: _optimizer]` returns the same module-level singleton on every call, which is
  precisely why the singleton exists — a bare `DjangoOptimizerExtension` class entry would construct
  a fresh instance per request and lose the instance-bound plan cache.
- **Every clause of the reload description holds** —
  `schema_reload.py::reload_all_project_schemas` does `registry.clear()`, then `_reload_or_import`
  over the six `_PROJECT_APP_SCHEMA_MODULES` in a documented dependency-safe order (glossary before
  kanban), then `reload_project_schema_shell()` reloading `config.schema` and `config.urls` and
  calling `clear_url_caches()`. `conftest.py::_reload_project_schema_for_acceptance_tests` is
  `scope="module", autouse=True` with a one-call body;
  `_isolate_project_schema_for_acceptance_test` is the function-scoped guard, fingerprinting through
  `_registry_registration_identity()` — seven `id()`-keyed tuples over the registry maps plus the six
  module objects — asserting the shell reload did not mutate registrations and re-running the full
  rebuild on teardown if the test did.
- **The other seven live-tier coverage items were read as bodies.** Nested
  `Branch → Shelf → Book → Loan → Patron` traversal; nullable reverse OneToOne (a second patron
  resolves `card: None`); reverse M2M `Genre.books`; reverse FK + M2M prefetch at three queries with
  `library_book_genres` pinned; choice-enum wire value plus `BookTypeCirculationStatusEnum`
  introspection and the nullable `subtitle` scalar; consumer-shaped queryset cooperation (`JOIN` in
  the root query, genres prefetched); `OptimizerHint.prefetch_related()` and `OptimizerHint.SKIP`
  each with their own query-count shape; and the relation override observed purely through response
  data and a query count.
- **`CaptureQueriesContext(connection)` is genuinely the practice.** Imported from
  `django.test.utils` with `connection` from `django.db`, used across eight live-tier modules, and
  every SQL assertion in the card's tests is a substring or `JOIN`-presence check rather than a full
  SQL string.
- **`ctx.dst_optimizer_plan` is still package-level.** `grep -rn "dst_optimizer_plan"
  examples/fakeshop/test_query/` returns nothing.
- **Both follow-ups still hold.** `grep -rni "strictness" examples/fakeshop/test_query/` returns two
  incidental comments in `test_library_api.py` and no assertion; `grep -rn "Prefetch("` returns two
  docstring mentions in `test_scalars_api.py` and no constructed `Prefetch`.
- **The retired fixture app has zero live hits.** `grep -rn
  "TestsCardinalityConfig\|tests\.fixtures\|tests_cardinality"` over `*.py` / `*.ini` / `*.toml`
  returns nothing at all; `tests/fixtures/` is absent.
- **The durable docs owe nothing.** [`AGENTS.md`][agents] rule 7 carries four test tiers;
  [`docs/TREE.md`][tree] renders `examples/fakeshop/config/` and all four test trees with the
  placement rule restated in prose. Both are script-rendered or standing docs outside this cycle's
  writable set, and neither needed an edit.

## Closing record — the board defect is fixed

The duplicate `#### Scope` bullet that the two entries above deferred was fixed in this cycle, after
the audit pass established that its stated blocker had cleared. `DONE-014-0.0.4` was the last card on
the board carrying it, so the pattern is now fully retired.

- **The source was a stray `kanban.CardItem` row** on the card's `scope` section — `order` `3`, a
  lowercase sentence restating the three authored bullets at `order` `0`-`2`. Two independent signals
  identified it: content (it carries no fact the other three do not) and provenance (its primary key
  is *lower* than all three while its `order` is *higher*, i.e. created first and appended last — the
  signature of an import step seeding a summary row).
- **The build plan's mechanism account was not merely stale but impossible.** It supposed the bullet
  was the card's `description` column rendered a second time; the `Card` model has no `description`
  field, which `getattr(card, "description", <sentinel>)` returning the sentinel disproves in one
  line. Confirm a mechanism against the model, never against the rendered output that motivated the
  claim.
- **The delete went through the Django ORM, not raw SQL, and the delete result is the evidence.**
  `.delete()` returned `(2, {'kanban.UUIDModel': 1, 'kanban.CardItem': 1})`: the row's `UUIDModel`
  side-row cascaded away with it, because `UUIDModel.carditem` is a `OneToOneField(...,
  on_delete=models.CASCADE)`. A raw `DELETE FROM` would have orphaned that side-row, breaking both
  the one-hot link check constraint and the `uuid { id }` selection each generator's in-process
  `/graphql/` query makes. `examples/fakeshop/apps/kanban/services.py` has `append_card_item` but no
  removal counterpart, so a direct ORM `.delete()` is the sanctioned fallback; adding a service
  function for one row is not justified until a third independent caller needs one.
- **Verification a `git diff` cannot give.** Both board exports were regenerated *before* the edit
  and the diff required to be empty, which is what makes the resulting one-line diff attributable;
  then regenerated twice after it, with `sha256` identity between the two runs proving the render is
  a fixed point rather than a further edit. `manage.py check` and `manage.py import_spec_terms
  --check` both pass, and the card still renders its three substantive scope bullets, its seven
  glossary terms, and its spec link.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[changelog]: ../../../CHANGELOG.md
[kanban]: ../../../KANBAN.md
[start]: ../../../START.md

<!-- docs/ -->
[glossary-strictness-mode]: ../../GLOSSARY.md#strictness-mode
[tree]: ../../TREE.md

<!-- docs/SPECS/ -->
[spec-011-rationale]: spec-011-stale_placeholder_cleanup-0_0_4-rationale.md
[spec-012-rationale]: spec-012-version_release_alignment-0_0_4-rationale.md
[spec-013-rationale]: spec-013-real_m2m_coverage-0_0_4-rationale.md
[spec-014]: ../spec-014-testing_shift-0_0_4.md
[spec-014-follow-ups]: ../spec-014-testing_shift-0_0_4.md#remaining-follow-ups
[spec-014-live-http]: ../spec-014-testing_shift-0_0_4.md#live-http-coverage
[spec-014-package-level]: ../spec-014-testing_shift-0_0_4.md#package-level-tests-that-intentionally-remain
[spec-014-problem]: ../spec-014-testing_shift-0_0_4.md#problem-statement
[spec-014-settled]: ../spec-014-testing_shift-0_0_4.md#settled-decisions
[spec-014-shipped-outcome]: ../spec-014-testing_shift-0_0_4.md#shipped-outcome
[spec-014-status]: ../spec-014-testing_shift-0_0_4.md#status
[spec-014-terms]: spec-014-testing_shift-0_0_4-terms.csv

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md
[build-014]: ../../builder/build-014-testing_shift-0_0_4.md
[worker-1]: ../../builder/worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
