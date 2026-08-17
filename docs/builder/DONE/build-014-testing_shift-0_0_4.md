# Package build plan: testing_shift / 0.0.4 (014) — residual-completion cycle

Spec source: `docs/SPECS/spec-014-testing_shift-0_0_4.md` (already archived; card `DONE-014-0.0.4`)
Rationale companion: `docs/SPECS/appx/spec-014-testing_shift-0_0_4-rationale.md` — **does not exist**; creating it is this cycle's first obligation.
Terms companion: `docs/SPECS/appx/spec-014-testing_shift-0_0_4-terms.csv` (exists, 7 rows, one row per anchor, `check_spec_glossary` green — `OK: 7 terms`).
Target release: `0.0.4` (shipped; this cycle bumps no version and lands no feature).
Build rule: one item at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every item must justify shared/duplicated patterns before merging.
Ownership partition: none; sequential items. R1 and R2 both write the spec file, so they could not run concurrently even if the rest were disjoint.
Hot-path declaration: none. Both items write Markdown only; no package source and no test is in any item's writable set.
Floor-verification scope: **none.** No item touches a Django / Strawberry / channels integration seam — no item touches executable code at all.
Pre-flight: passed on 2026-08-16 with two recorded deviations (steps 3 and 5, below); baseline: **dirty with concurrent sessions' work — 174 paths, none of them this cycle's**; cleanup: **nothing deleted or cleared** (deviation, below); memory files namespaced per cycle.

## Why this cycle exists

Card `DONE-014-0.0.4` shipped at `0.0.4`, so the code is not in question as *new* work. Three obligations, in the maintainer's framing:

1. **Nothing was skipped in the code.** Everything spec-014 promised must be present at `HEAD`, and anything promised and never delivered is a defect this cycle fixes.
2. **Later work that changed the shipped shape is legitimate — but the spec must say so.** Where a later card corrected, superseded, or completed something spec-014 owns, the spec is rewritten to state the **current** contract directly. It never narrates the change (`docs/builder/BUILD.md` `## Spec rationale extraction`).
3. **The explanation goes in the rationale, not the spec.** What changed, why, which commit caused it, and what the spec may no longer claim — all of it lands in the rationale companion, keyed to the spec section it belongs to.

Spec-014 is **not** a card-snapshot stub, unlike specs 011-013. It is a genuine pre-implementation design record — 61 lines of problem statement, goals, non-goals, a proposed app, test-placement rules, a ten-bullet migration catalogue, and a risks-and-open-decisions section — that was **overwritten in place** by its own implementing commit and replaced with a shipped-state summary. That single fact reshapes all three obligations, and it is this cycle's central finding (V9 / F1 below).

## Worker-0 verification pass (performed before any dispatch)

`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`. Every finding below was read against `HEAD` (`973d00b2`) before this plan was written; each cites its symbol-qualified path (`AGENTS.md` rule 27) or its commit. A finding is dispatched only if it holds.

### What the card actually did — recovered from history

Three commits, all 2026-05-07, two of which name the spec in their message:

| Commit | Time | What it did for this card |
|---|---|---|
| `73004d74` "Refactor tests a bit;" | 12:22 | Authored `docs/spec-testing_shift.md` (the original 61-line design record) and created the `library` example app + the first `test_library_api.py`. Shared with card 013. |
| `1057ddc2` "Complete spec-testing_shift.md;" | 13:08 | **The card's own scope.** Deleted `tests/fixtures/` — the unmanaged `tests_cardinality` app — and dropped `tests.fixtures.apps.TestsCardinalityConfig` from the example project's `INSTALLED_APPS`; re-pointed the package tests at the real `library` models. Shared with card 013. |
| `a7ca9cc2` "Finish spec-testing_shift.md" | 17:58 | **The layout shift.** Moved the flat example project into `examples/fakeshop/config/` (settings, schema, urls, wsgi) + `examples/fakeshop/apps/` (`apps.products`, `apps.library`), re-pointed `pytest.ini`'s `DJANGO_SETTINGS_MODULE` from `settings` to `config.settings`, and updated `AGENTS.md` / `docs/TREE.md` / `test_query/README.md`. |

`67b07f79` (13:50, between the second and third) is card 013's coverage expansion, and it is also the commit that **overwrote the spec** — see V9.

### V1-V10: nothing was skipped in the code — verified, not assumed

| # | Claim to verify | At `HEAD` | Evidence |
|---|---|---|---|
| V1 | the test-only fixture app is gone from the example project | gone | `tests/fixtures/` does not exist; `grep -rn "TestsCardinalityConfig\|tests\.fixtures\|tests_cardinality"` over source, tests, and settings returns **zero** live hits — all 9 hits are documentary (`KANBAN.md` x3, this spec, prior cycles' rationale/plan files) |
| V2 | the `config/` + `apps/` layout the spec describes exists | exists | `examples/fakeshop/config/` holds `settings.py`, `test_settings.py`, `schema.py`, `urls.py`, `wsgi.py`; `examples/fakeshop/apps/` holds six app packages |
| V3 | the `library` app carries the seven models and nine relation shapes the spec names | all present | `examples/fakeshop/apps/library/models.py` — `Branch`, `Shelf`, `Genre`, `Book`, `Patron`, `MembershipCard`, `Loan` all present among 11 classes |
| V4 | the live `/graphql/` acceptance suite exists at the named path | exists | `examples/fakeshop/test_query/test_library_api.py`, 192 test functions at `HEAD` (8 at the card's own commit) |
| V5 | the eight live tests the card shipped survive by name | all 8 survive | each `grep -c "def <name>("` -> 1: `test_library_branch_shelf_book_loan_graph_over_http`, `…patron_card_and_genre_reverse_paths_over_http`, `…optimizer_selects_book_shelf_in_http_query`, `…reverse_fk_and_m2m_prefetch_sql_shape_over_http`, `…choice_enum_and_nullable_subtitle_are_deliberate_http_contracts`, `…consumer_prefetched_queryset_cooperates_with_optimizer_over_http`, `…optimizer_hints_are_observable_over_http`, `…relation_override_shapes_http_response_data` |
| V6 | both optimizer hints the spec's HTTP-coverage sentence names are still declared on an example type | both declared | `examples/fakeshop/apps/library/schema.py` #"optimizer_hints = {\"book\": OptimizerHint.prefetch_related(), \"patron\": OptimizerHint.SKIP}" on `LoanType.Meta` |
| V7 | the autouse reload fixture still exists under the name the spec gives it | exists, reshaped | `examples/fakeshop/test_query/conftest.py::_reload_project_schema_for_acceptance_tests` — the **name** survives; its scope and body do not (D5) |
| V8 | the package-level tests the spec says intentionally remain are still there | all remain | `tests/test_registry.py` (78 tests), `tests/optimizer/test_walker.py` (168), `tests/optimizer/test_extension.py` (34 `cache_key` references), the relation-override tests in `tests/types/test_definition_order.py`, and the `tests/utils/` tree |
| V9 | "The original spec remains here as the design record" | **FALSE** | `67b07f79` deleted all ten deliberative sections of `docs/spec-testing_shift.md` in the same commit that added the `## Status` line making the claim. `git diff 73004d74 67b07f79 -- docs/spec-testing_shift.md` is -61/+27 lines. The design record is recoverable only from `git show 73004d74:docs/spec-testing_shift.md` |
| V10 | `ctx.dst_optimizer_plan`, the attribute the spec's resolved-decisions section names, still exists | exists | `tests/test_connection.py` #"ctx.dst_optimizer_plan", `tests/test_list_field.py` #"plan = ctx.dst_optimizer_plan" |

**No code defect was found. No source or test file is in any item's writable set, so no Worker 2 pass is dispatched** — which is the disposition the maintainer's dispatch instruction anticipated.

### R1 findings — the spec's own text

Each is a claim later work falsified, or a deliberative layer that never got a home. None is a code defect.

| # | Finding | Evidence |
|---|---|---|
| F1 | No rationale companion exists, **and this spec is the one in the series that had a real deliberative layer to lose.** Specs 011-013 were card-snapshot stubs whose rationale files had to be constructed from history; spec-014's deliberation was written, then destroyed in place by its own implementing commit. Recovering it is this cycle's largest single deliverable. | `ls docs/SPECS/appx/spec-014-*` returns only the terms CSV; V9 |
| F2 | `## Status` claims "The original spec remains here as the design record". It does not: the commit that wrote that sentence is the commit that deleted the record. | V9 |
| F3 | `## Implemented outcome` claims `pytest.ini` sets `DJANGO_SETTINGS_MODULE = config.settings`. At `HEAD` it is `config.test_settings`, a pytest-only layer over the shipped settings, since `a9fa8c34` (2026-07-10). | `pytest.ini` #"DJANGO_SETTINGS_MODULE = config.test_settings"; `examples/fakeshop/config/test_settings.py` |
| F4 | `## Implemented outcome` claims the project schema "constructs `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])`". At `HEAD` it constructs `DjangoSchema(query=Query, mutation=Mutation, config=strawberry_config(), extensions=[lambda: _optimizer])` — four separate later contracts (mutation atomicity, the schema-config factory, the singleton-in-a-factory plan-cache preservation, the write surface). | `examples/fakeshop/config/schema.py` #"schema = DjangoSchema(" |
| F5 | `## Implemented outcome` names two domain apps (`apps.products`, `apps.library`). At `HEAD` there are six: `accounts`, `glossary`, `kanban`, `library`, `products`, `scalars`. | `ls examples/fakeshop/apps/` |
| F6 | `## Implemented outcome` names the `library` app's seven models as though they are its content. At `HEAD` the module holds **11** classes; the four additions belong to later cards. The spec needs the same out-of-scope fence spec-013's reconciliation adopted. | `examples/fakeshop/apps/library/models.py` |
| F7 | `## Live HTTP coverage`'s description of the autouse fixture — "clears the registry, reloads `apps.library.schema`, reloads `config.schema`, reloads `config.urls`, and clears URL caches" — describes a per-test full reload that no longer exists. At `HEAD` the fixture is **module-scoped**, delegates to the single-sited `schema_reload` module, reloads **all six** app schemas in a dependency-safe order, and is paired with a function-scoped guard that does only a shell reload plus a registration fingerprint check. | `examples/fakeshop/test_query/conftest.py`; `examples/fakeshop/schema_reload.py`; the rework landed at `a9fa8c34` |
| F8 | `## Remaining follow-ups` says Layer-3 features "remain non-goals for this slice and should land under their own specs", listing filters, orders, aggregates, fieldsets, permissions, Relay nodes, and `DjangoConnectionField`. Five of the seven have since shipped under their own specs (filters/orders `0.0.8`, Relay nodes + `DjangoConnectionField` `0.0.9`, permissions `0.0.10`); only aggregates and fieldsets are still ahead, on the `0.1.x` beta line. | `docs/README.md` shipped list; `KANBAN.md` |
| F9 | `## Remaining follow-ups` gives a condition for moving strictness-mode coverage to HTTP — "only if a debug header, test-only extension, or other consumer-visible response surface exposes the planned-key state". That surface **now exists** (`DjangoDebugExtension`, `0.0.14`), so the sentence's premise has changed even though its disposition has not. | `django_strawberry_framework/extensions/debug.py`; strictness still has no live-tier coverage — 2 incidental comment mentions in `test_library_api.py`, no assertion |
| F10 | The `## Remaining follow-ups` deferral of custom `Prefetch(...)` objects with shaped querysets **still holds** — recorded so the reconciliation does not "fix" a claim that is correct. No live-tier file constructs a `Prefetch`; the two consumer-cooperation live tests use plain `prefetch_related(...)`. | `grep -rn "Prefetch(" examples/fakeshop/test_query/` returns only docstring mentions |

### R2 findings — documentation completion and archive audit

| # | Finding | Evidence |
|---|---|---|
| F11 | The spec is already at `docs/SPECS/` with a reference-style link block and all ten canonical group headers, and `check_spec_glossary` is green. The archive move is therefore **done**; what R2 owes is the audit and the new companion's own link hygiene. | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-014-testing_shift-0_0_4.md` -> `OK: 7 terms` |
| F12 | All seven glossary anchors resolve and every one is `shipped`. The card renders them in `KANBAN.md`. | `KANBAN.md` `### [DONE-014-0.0.4 …]` `#### Glossary terms` |
| F13 | The durable docs are already complete for this card's work: `AGENTS.md` rule 7 carries the test-placement rule (now four tiers, not the card-era three), and `docs/TREE.md` renders the `config/` + `apps/` layout and all four test trees. **No durable-doc edit is owed.** | read at `HEAD` |
| F14 | The rendered `DONE-014-0.0.4` card body carries a **duplicate `#### Scope` row** — bullet 4 ("remove the `tests.fixtures.apps` fixture app + unmanaged cardinality fixtures; switch package tests to real `library` models.") is the card's `description` column restating bullets 1-3. The identical defect cards `DONE-011-0.0.4` and `DONE-013-0.0.4` carry. | `KANBAN.md` line 4480 |

**F14 is recorded, not dispatched — and the reason is concurrency, not disposition.** `KANBAN.md` / `KANBAN.html` are generated from `examples/fakeshop/db.sqlite3`, so the fix is an ORM edit plus a regenerate (never a hand-edit). `examples/fakeshop/db.sqlite3` is dirty at plan time with concurrent sessions' uncommitted work, so a regenerate would publish rows that have not landed (`START.md` `## Concurrent sessions`). F14 goes to the deferred-work catalog with its recipe, and **this cycle makes no database write and runs no generator.** This is the third cycle in a row to reach that disposition on the same board defect; the catalog should say so.

## Baseline-dirty out-of-scope files

`HEAD` at plan time: `973d00b2c4cae3d3474dcd819b1c9a012d18bfe1`. `git status --porcelain | wc -l` -> **174**, and **not one of them is this cycle's**. Every path belongs to a concurrent maintainer session (`START.md` `## Concurrent sessions`, `AGENTS.md` rule 34). **No worker edits, reverts, stages, or `git checkout`s any of them.** In particular:

- `examples/fakeshop/db.sqlite3`, `docs/GLOSSARY.md` — dirty; see F14. No worker of this cycle opens either for writing, and no worker runs `scripts/build_kanban_md.py`, `build_kanban_html.py`, or `build_glossary_md.py`.
- `docs/SPECS/spec-009-…md` + its `appx/` rationale, and `docs/SPECS/spec-013-…md` + its new `appx/` rationale, are two concurrent residual cycles' in-flight output. Read `spec-013`'s pair as shape precedent — it is this cycle's direct sibling — but never as authority, and never edit either.
- `examples/fakeshop/test_query/test_library_api.py` and several `tests/` files are dirty with concurrent edits. Every V-row above that reads them was derived from `git show HEAD:<path>` into a scratch path outside the repo, per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`. Any pass needing them does the same.
- `docs/review/`, `docs/bug_hunt/`, and `docs/dry/` scratchpads of in-flight cycles. `AGENTS.md` rule 22 forbids touching `docs/review/` regardless.

**`docs/SPECS/spec-014-testing_shift-0_0_4.md` itself is CLEAN at `HEAD`** — it is not in the dirty list, so this cycle's edits to it are unambiguously attributable.

**The list is moving.** Any pass that needs the baseline re-derives it rather than quoting this section.

## Pre-flight deviations, recorded

Two steps of `worker-0.md` `## Pre-flight procedure` did not run as written; both deviations protect concurrent sessions, and both follow the precedent the spec-013 cycle set on this same tree.

- **Step 3 (artifact reset).** **Nothing was deleted.** `docs/builder/bld-003-final.md`, the `bld-009-*` / `build-009-*` pair, the `bld-013-*` / `build-013-*` set, and `build-011-*` are the committed or in-flight records of closed and running cycles. Deleting a prior cycle's record is the one irreversible pre-flight mistake that step names. What the step protects — that this cycle overwrites no existing path — was verified directly: all five paths in `## Artifact list` plus the rationale companion were confirmed absent.
- **Step 5 (scratch directories cleared).** **Nothing was cleared.** `docs/builder/worker-memory/` holds nine files two concurrent sessions wrote, and `docs/shadow/` is live review substrate. Clearing either would destroy running work. This cycle uses **namespaced** memory files — `docs/builder/worker-memory/spec-014-worker-0.md` and `…/spec-014-worker-1.md` — following the precedent the spec-009 and spec-013 sessions set. No worker of this cycle reads or writes any other file in that directory.

Steps 1, 2, 4, 6 ran: the baseline is enumerated above and included per the maintainer's knowing dispatch onto this tree; `scripts/review_inspect.py` smoke-invoked OK; `.gitignore` carries all three scratch paths; `check_spec_glossary --spec docs/SPECS/spec-014-…md` exits 0. Step 7 (rationale extraction) is item R1.

## Artifact list

- `docs/builder/bld-014-r1-rationale_and_spec_reconciliation.md`
- `docs/builder/bld-014-r2-doc_completion_archive_audit.md`
- `docs/builder/bld-014-r3-card_body_scope_fix.md` (added mid-cycle; see below)
- `docs/builder/bld-014-final.md`

**No `bld-integration.md`.** `docs/builder/BUILD.md` `## Cross-slice integration pass` scans landed source for cross-slice duplication; this cycle lands no source at all, so there is no cross-slice DRY surface. Both of the pass's live obligations are folded into the final gate: the staged-anchor sweep, and the read of every closed artifact. Same disposition, and the same reason, as the spec-011, spec-012, and spec-013 cycles.

## Checklist

- [x] R1: create the rationale companion and reconcile the spec against `HEAD` (F1-F10)
- [x] R2: documentation completion and archive audit (F11-F14)
- [x] R3: card-body `#### Scope` fix (F14, unblocked mid-cycle) -> `docs/builder/bld-014-r3-card_body_scope_fix.md`
- [x] Final test-run gate

Every item closed `final-accepted`.

## Cycle outcome, recorded

**The cycle's diff is ten paths**: the reconciled spec, its new rationale companion, this plan plus four artifacts, and — from R3 alone — `KANBAN.md`, `KANBAN.html`, and `examples/fakeshop/db.sqlite3`. **No package source and no test file was written.**

**Nothing was skipped in the code.** V1-V10 all reproduced when R1 re-derived them independently. Everything spec-014 promised is present at `HEAD`: the fixture app is gone with zero live references, the `config/` + `apps/` layout stands, all seven card-era `library` models survive, all eight card-era live tests survive by name, both optimizer hints are still declared, and every package-level test the spec says intentionally remains is still there.

**The finding that made this spec different from its three siblings.** Specs 011-013 were card-snapshot stubs whose rationale files had to be *reconstructed* from history. Spec-014 was a genuine 61-line pre-implementation design record — and its own implementing commit `67b07f79` **deleted all ten deliberative sections in place**, in the same diff that added a `## Status` line claiming "The original spec remains here as the design record". R1 recovered the whole record from `git show 73004d74:docs/spec-testing_shift.md` into the rationale companion. That companion is 59,517 bytes against a 8,011-byte spec — the only file in the series where the rationale is a restoration rather than a reconstruction.

**Four spec-vs-reality drifts were fixed, and the adversarial pass caught the one grep could not.** R1 closed F2-F10 (the false `## Status` claim, `config.settings` → `config.test_settings` at `a9fa8c34`, the `strawberry.Schema` → `DjangoSchema` constructor, two → six apps, seven → eleven `library` classes, the reworked reload fixture, and the Layer-3 follow-ups). R2 — a fresh spawn with no memory of writing any of it — then found three more, the first being **the same defect class the spec-013 cycle found on the same clause**: `## Live HTTP coverage` claimed the forward FK is served as `select_related`, but `test_library_optimizer_selects_book_shelf_in_http_query` survives by name while asserting `len(captured) == 2` — `ShelfType.get_queryset` forces a visibility-scoped `Prefetch`, flipped at `1694bd2e`. R2 also promoted a **live constraint** that R1 had filed only in the rationale (`apps/library/schema.py`'s deliberately awkward `DjangoType` declaration order is load-bearing finalization coverage; tidying it would silently retire that coverage), and narrowed an "each owned by their own spec" clause that was true for six of seven features.

**The lesson, carried forward, and now twice-confirmed:** `path::QualifiedName` proves a symbol survives, not that the sentence describing it survives. Two consecutive residual cycles have found their one real drift in a test that kept its name while its assertion was inverted — invisible to every grep, reachable only by reading the body against the sentence. **The adversarial re-derivation pass is what earns its keep; it is not a formality.**

**F14 was deferred at plan time and closed mid-cycle instead.** Its precondition — a dirty `examples/fakeshop/db.sqlite3` — cleared while the cycle ran, and the maintainer landed the identical fix on `DONE-013-0.0.4` at `6f8bf818`. R3 deleted the stray `kanban.CardItem` through the Django ORM (the cascade also took its `UUIDModel` side-row, which a raw SQL delete would have orphaned and thereby broken both generators' `uuid { id }` selection) and regenerated. Verified by a clean baseline regenerate *before* the edit, a resulting diff of exactly one bullet, and byte-identical hashes across two consecutive regenerates. **`DONE-014-0.0.4` was the last card carrying that defect, so the pattern is now fully retired board-wide.** R2 additionally corrected this plan's account of its mechanism: it was a stray scope row, not a rendered `description` column — the `Card` model has no `description` field at all.

**The gate ran clean apart from two rows it does not own.** `uv run pytest --no-cov` → `2 failed, 5964 passed, 40 skipped`. Both failures are in `tests/filters/test_sets.py` against `django_strawberry_framework/filters/sets.py`, a pair dirty with a concurrent session's uncommitted work; one of the two tests **does not exist at `HEAD`** at all. Recorded, diagnosed, and escalated rather than fixed or masked (`AGENTS.md` rule 34). The kanban suites pass 196/196, so R3's database write broke nothing, and the spec-013 cycle's unattributable `test_dedupe_serializer_input_shape_is_sole_cache_protocol` failure now passes. Everything else was green: `manage.py check`, `makemigrations --check --dry-run`, `ruff format --check`, `ruff check`, `git diff --check`, `check_spec_glossary` (`OK: 7 terms`), floor-verification scope `none` as declared, and a staged-anchor sweep finding zero surviving `TODO(spec-014` / `TODO-*-014` anchors.

**Nothing is deferred.** The catalog in `bld-014-final.md` records F14 as discharged and R1's `build-008` citation as a verified phantom (its misattributions were fixed by that cycle's own R2b item; `git grep spec-014 HEAD -- django_strawberry_framework/` is empty). The unused-`[backlog]` pattern that the three prior cycles each carried forward does not apply here — neither spec-014 nor its rationale carries such a definition.

## Corrections to this plan, recorded

Figures in `## Worker-0 verification pass` that did not reproduce when the items measured them, corrected here rather than left standing (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`):

- **"nine relation shapes"** (V3) — the spec names **eight**. There is no ninth.
- **"a ten-bullet candidate catalogue"** (`## Why this cycle exists`) — the recovered `## High-value migrations to HTTP tests` holds **eight** bullets carrying 37 `path:NN` refs.
- **V1's "zero live hits / 9 documentary"** — the documentary population is moving (two concurrent cycles' artifacts have roughly doubled it). The finding is unaffected: the *live* hit count is zero, which is what V1 asserts.
- **The commit table omits that `a7ca9cc2` also edited the spec** (+10/-8). `67b07f79`'s shipped-state summary described the *flat* layout and was stale within four hours; F9's and F10's two follow-up bullets were authored at `a7ca9cc2`, not at the overwrite.
- **V9's "-61/+27"** is exact as line counts (61 → 27); as a `--stat` it is `+25/-59`. Both recorded so neither is "corrected" into the other.
- **F14's mechanism** — a stray `kanban.CardItem` scope row, not the `description` column rendered twice (above).

**`HEAD` moved twice during the cycle**, `973d00b2` → `676f10d2` → `6f8bf818`, and the dirty-path count drifted 174 → 186. No moved file was evidence for any verification row; every affected read was re-derived at the current `HEAD` by the item that needed it.

## Mid-cycle addition: R3, and why F14 stopped being deferred

`docs/builder/worker-0.md` `### Mid-flight instructions are mirrored into the artifact` — recorded here because no artifact section would otherwise capture a Worker-0 decision to add an item.

F14 was catalogued rather than dispatched on one precondition: `examples/fakeshop/db.sqlite3` was dirty with concurrent sessions' uncommitted rows, so a regenerate would publish work that had not landed. **R2 found that precondition had cleared mid-cycle, and its finding was re-verified before this item was added:**

- `git status --porcelain examples/fakeshop/db.sqlite3 KANBAN.md KANBAN.html` returns **empty** — all three clean at `6f8bf818`.
- The maintainer landed `6f8bf818` "docs(kanban): re-home the spec-013 residual cycle's deferred work" during this cycle, which **fixed the identical defect on `DONE-013-0.0.4`** (`grep -n "replace test-only M2M / cardinality fixtures" KANBAN.md` now returns nothing) and had already fixed `DONE-011-0.0.4`.
- `DONE-014-0.0.4` is therefore the **last card carrying it** (`KANBAN.md` line 4480).

So the plan's "third consecutive cycle to reach that disposition" framing is superseded, and R2 additionally corrected the plan's account of the **mechanism**: the duplicate is a stray `kanban.CardItem` scope row, not the `description` column rendered a second time. The recipe R3 executes is R2's corrected one, not this plan's original.

`docs/GLOSSARY.md` remains dirty with concurrent work, so **R3 runs the two kanban generators only** — `scripts/build_kanban_md.py` and `scripts/build_kanban_html.py` — and never `scripts/build_glossary_md.py`. This item makes the cycle's only database write.

**Dispatched to Worker 1 alone**, consistent with R1 and R2 and with the maintainer's standing instruction for this cycle. `docs/builder/BUILD.md` `### Isolation is non-waivable` binds a pass that writes code; R3 writes none — it is a one-row data correction whose whole effect is mechanically verifiable by a two-consecutive-regenerate byte-stability proof plus a one-bullet `git diff`.

## Dispatch record

| Item | Passes dispatched | Why |
|---|---|---|
| R1 | Worker 1 only | The maintainer's standing instruction for this cycle: an item that changes only the spec and its rationale is Worker 1's alone, and both files are Worker 1-owned by `docs/builder/BUILD.md` `## Spec reconciliation` in any case. |
| R2 | Worker 1 only | Its findings are inside the spec and its companions. The one durable-doc-shaped finding (F14) is DB-backed and blocked on a dirty `db.sqlite3`, so it is catalogued rather than built. |
| Final | Worker 1 only | `worker-1.md` `## Final test-run gate` gives the whole gate to Worker 1. |
| (none) | Worker 2 / Worker 3 | The verification pass found no code defect and no code item to build. `### Isolation is non-waivable` binds a pass that writes code; this cycle writes none. |

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
