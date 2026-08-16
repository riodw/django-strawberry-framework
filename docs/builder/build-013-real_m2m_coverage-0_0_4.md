# Package build plan: real_m2m_coverage / 0.0.4 (013) — residual-completion cycle

Spec source: `docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md` (already archived; card `DONE-013-0.0.4`)
Rationale companion: `docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-rationale.md` — **does not exist**; creating it is this cycle's first obligation.
Terms companion: `docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-terms.csv` (exists, 1 row, one row per anchor, `check_spec_glossary` green — `OK: 1 terms`).
Target release: `0.0.4` (shipped; this cycle bumps no version and lands no feature).
Build rule: one item at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every item must justify shared/duplicated patterns before merging.
Ownership partition: none; sequential items. R1 and R2 both write the spec file, so they could not run concurrently even if the rest were disjoint.
Hot-path declaration: none. Both items write Markdown only; no package source and no test is in any item's writable set.
Floor-verification scope: **none.** No item touches a Django / Strawberry / channels integration seam — no item touches executable code at all.
Pre-flight: passed on 2026-08-15 with two recorded deviations (steps 3 and 5, below); baseline: **dirty with concurrent sessions' work — 124 paths, none of them this cycle's**; cleanup: **nothing deleted or cleared** (deviation, below); memory files namespaced per cycle.

## Why this cycle exists

Card `DONE-013-0.0.4` shipped at `0.0.4`, so the code is not in question as *new* work. Three obligations, in the maintainer's framing:

1. **Nothing was skipped in the code.** Everything spec-013 promised must be present at `HEAD`, and anything promised and never delivered is a defect this cycle fixes.
2. **Later work that changed the shipped shape is legitimate — but the spec must say so.** Where a later card corrected, superseded, or completed something spec-013 owns, the spec is rewritten to state the **current** contract directly. It never narrates the change (`docs/builder/BUILD.md` `## Spec rationale extraction`).
3. **The explanation goes in the rationale, not the spec.** What changed, why, which commit caused it, and what the spec may no longer claim — all of it lands in the rationale companion, keyed to the spec section it belongs to.

Spec-013 is a **card-snapshot stub**: 1,669 bytes, no Decisions, no slice checklist, no rationale companion at all. So obligation 3 here is a creation, not a completion, and obligation 2 is mostly a matter of dispositioning claims that a raw Kanban render dumped into the file.

## Worker-0 verification pass (performed before any dispatch)

`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`. Every finding below was read against `HEAD` (`973d00b2`) before this plan was written; each cites its symbol-qualified path (`AGENTS.md` rule 27) or its commit. A finding is dispatched only if it holds.

### What the card actually did — recovered from history, because the stub does not say

The stub names no commit, so the card's diff was recovered by content search. The work is **three commits, all 2026-05-07**, and none of them carries the card id or the spec name in its message:

| Commit | What it did for this card |
|---|---|
| `73004d74` "Refactor tests a bit;" | Created the `library` example app — `models.py` (136 lines, 7 managed models), `migrations/0001_initial.py`, `schema.py`, `apps.py` — registered it in fakeshop `INSTALLED_APPS` and the project schema, and added the first `examples/fakeshop/test_query/test_library_api.py` (227 lines). |
| `1057ddc2` "Complete spec-testing_shift.md;" | **The substitution itself.** Deleted `tests/fixtures/` — the unmanaged `tests_cardinality` app (`__init__.py`, `apps.py`, `cardinality_models.py`, `models.py`) — dropped it from fakeshop settings, and re-pointed both `test_definition_order.py` files plus `tests/types/test_definition_order_schema.py` at the real `library` models. |
| `67b07f79` "feat: Implement library app for real API testing in fakeshop project" | Expanded `test_library_api.py` to eight live tests, added two non-live library schema tests, and updated `AGENTS.md` / `docs/TREE.md` / `test_query/README.md` for the new tier. Its own message states the card's scope verbatim: "Removed the test-only cardinality fixture app and integrated its functionality into the new library app." |

**The retired fixture set, named.** `tests/fixtures/cardinality_models.py` at `1057ddc2~1` held five `managed = False` models under `app_label = "tests_cardinality"`: `User`, `Profile` (forward `OneToOneField`), `Author`, `Tag`, and `Book` (`ForeignKey` to `Author`, `ManyToManyField` to `Tag`). The replacement mapping is one-to-one on cardinality, not on name:

| Retired fixture edge | Real `library` replacement |
|---|---|
| `Profile.user` (forward OneToOne) | `MembershipCard.patron` |
| `User.profile` (reverse OneToOne) | `Patron.card` |
| `Book.author` (forward FK) | `Book.shelf` |
| `Author.books` (reverse FK) | `Shelf.books` |
| `Book.tags` (forward M2M) | `Book.genres` |
| `Tag.books` (reverse M2M) | `Genre.books` |

### V1-V8: nothing was skipped in the code — verified, not assumed

| # | Claim to verify | At `HEAD` | Evidence |
|---|---|---|---|
| V1 | the real managed `library` app exists and is wired into the example project | exists | `examples/fakeshop/apps/library/models.py` (7 models at creation, 12 today), `config/settings.py` #"apps.library.apps.LibraryConfig", and the app's own migration package |
| V2 | the test-only fixture app is gone tree-wide | gone | `tests/fixtures/` does not exist; `grep -rn "tests_cardinality\|cardinality_models"` returns **zero** hits outside `docs/builder/DONE/` |
| V3 | every cardinality the fixtures covered is covered by real models | all six | the mapping table above; each row read off `examples/fakeshop/apps/library/models.py` at `HEAD` |
| V4 | package-level M2M traversal coverage exists | exists | `tests/types/test_definition_order.py::test_many_to_many_forward_and_reverse_relations_resolve` asserts `BookType.genres == list[GenreType]`, `GenreType.books == list[BookType]`, `ShelfType.books == list[BookType]` — read at **`HEAD`**, not the working tree (the file is dirty with a concurrent session's one-line edit) |
| V5 | package-level optimizer-planning coverage exists | exists | `tests/optimizer/test_definition_order.py::test_plan_relation_decisions_match_cardinality_after_finalization` asserts `plan_relation(Book.genres, GenreType) == ("prefetch", "default")` and the reverse `Genre.books` likewise, alongside the O2O `("select", "default")` pair |
| V6 | the HTTP-level coverage the card shipped survives | all 8 survive by name | `test_library_branch_shelf_book_loan_graph_over_http`, `…patron_card_and_genre_reverse_paths_over_http`, `…optimizer_selects_book_shelf_in_http_query`, `…reverse_fk_and_m2m_prefetch_sql_shape_over_http`, `…choice_enum_and_nullable_subtitle_are_deliberate_http_contracts`, `…consumer_prefetched_queryset_cooperates_with_optimizer_over_http`, `…optimizer_hints_are_observable_over_http`, `…relation_override_shapes_http_response_data` — each `grep -c "def <name>("` -> 1 |
| V7 | the M2M **prefetch** is pinned at the SQL level over HTTP, not merely at the wire | pinned | `test_library_api.py` #"library_book_genres" in the reverse-FK/M2M prefetch-shape test and again in the consumer-prefetched-queryset test — the join table name, so a fallback to an N+1 could not produce it |
| V8 | the card's two non-live schema tests survive | survive, relocated | `examples/fakeshop/apps/library/tests/test_schema.py::test_project_schema_includes_library_types` (asserts `{"title", "shelf", "genres"}` on `BookType`) and `::test_library_djangotype_declaration_order_stays_awkward`, moved from the then-flat `examples/fakeshop/tests/test_schema.py` by the later per-app test-tree split |

**One card-013 test no longer exists, and its removal is licensed, not a drop.** `tests/types/test_definition_order_schema.py::test_m2m_schema_shape_builds_with_real_library_models` (added by `1057ddc2`, asserting `str(genres_field.type) == "[GenreType!]!"` through `schema._schema.type_map`) was removed at `be9130e3` "Migrate package tests to the live `/graphql/` fakeshop suite". Its live twin is `examples/fakeshop/test_query/test_library_api.py::test_book_genres_m2m_renders_as_list_shape_live`, whose docstring names the retired test explicitly and asserts the same `[GenreType!]!` shape through **real introspection over HTTP** rather than the private `type_map`. That is the same-or-stronger contract the migration commit's own rule requires, and it is `AGENTS.md` rule 10 applied. **This is exactly the class of later change obligation 2 covers: the spec must state the current contract, and the rationale must record the move.**

**No code defect was found. No source or test file is in any item's writable set, so no Worker 2 pass is dispatched** — which is the disposition the maintainer's dispatch instruction anticipated.

### R1 findings — the spec's own text

Each is a stub-shaped defect or a claim later work falsified. None is a code defect.

| # | Finding | Evidence |
|---|---|---|
| F1 | No rationale companion exists. `docs/builder/BUILD.md` `## Spec rationale extraction` makes it the first substantive action of a build; specs 001-012 all have one. | `ls docs/SPECS/appx/spec-013-*` returns only the terms CSV |
| F2 | The preamble paragraph ("This file is intentionally lightweight… Before implementation work starts from this file, expand it into the full builder-format spec") is deliberation about the file, and its instruction is **counterfactual** at `HEAD`: implementation shipped ten minor versions ago and no expansion preceded it. | spec-013 line 7 |
| F3 | `## Planning note` carries the single word `shipped` — a raw Kanban `planning_note` column render, not contract. | spec-013 lines 18-20 |
| F4 | `## Other` is an undifferentiated dump of six heterogeneous Kanban rows — a "why it matters" note, a restated scope bullet, and four `#### Files likely touched` paths — under a heading that names none of them. | spec-013 lines 27-34 |
| F5 | `## Card snapshot` restates board fields (labels, priority, relative size) that belong to the Kanban database and are rendered into `KANBAN.md`. Spec-007's reconciled shape draws this line explicitly, and specs 011 and 012 already follow it. | spec-013 lines 9-16 vs. `docs/SPECS/spec-012-version_release_alignment-0_0_4.md` `## Card snapshot` |
| F6 | `## Scope` names **nothing**: not the fixtures it retired, not the models that replaced them, not one test. The spec cannot be checked against the tree without recovering three commits from history — which is what this cycle had to do. The retired set is finite (five models, six edges) and nameable, and so is the replacement. | the two tables above |
| F7 | `## Other`'s four file paths are a board **prediction** field (`#### Files likely touched`), not a record of the card's diff, and one is wrong for the card's own era: `examples/fakeshop/apps/library/models.py` did not exist at that path when the card shipped — the app lived at `examples/fakeshop/library/` until the later per-app `apps/` namespace split. The list also omits every file the card actually deleted. | `73004d74` / `1057ddc2` stats; the path is correct at `HEAD` and wrong for `0.0.4` |
| F8 | The `[backlog]` link definition is unused (one occurrence in the file — the definition itself). | `grep -c "\[backlog\]"` -> 1 |

**F8 is recorded, not dispatched.** Multiple archived stubs carry the same unused definition; `worker-0.md` `## Closing out a kanban card` forbids partial-fixing a pattern that spans surfaces, and `TODO-ALPHA-052-0.1.0` already carries the cluster. It goes to the deferred-work catalog.

### R2 findings — documentation completion and archive audit

| # | Finding | Evidence |
|---|---|---|
| F9 | The spec is already at `docs/SPECS/` and every link definition resolves at that depth (`../../KANBAN.md`, `../GLOSSARY.md#relation-handling`), and the file is already reference-style with all ten canonical group headers. The archive move itself is therefore **done**; what R2 owes is the audit and the new companion's own link hygiene. | path check; `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md` -> `OK: 1 terms` |
| F10 | The card's single glossary anchor resolves and carries the right shipped version: `#relation-handling` -> `docs/GLOSSARY.md` `## Relation handling`, **Status:** shipped (`0.0.1`+). `KANBAN.md`'s `DONE-013-0.0.4` card renders it. | `docs/GLOSSARY.md` #"## Relation handling"; `KANBAN.md` `### [DONE-013-0.0.4 …]` |
| F11 | The durable docs the card's work belongs in are already complete and correct: `docs/TREE.md` carries the `apps.library/` app-role paragraph naming "many-to-many joins" and lists `examples/fakeshop/apps/library/tests/test_schema.py`; `AGENTS.md` rule 7 carries the four-tier test-placement rule this card's commit introduced. **No durable-doc edit is owed.** | read at `HEAD` |
| F12 | The rendered `DONE-013-0.0.4` card body carries a **duplicate `#### Scope` row**: bullet 3 ("replace test-only M2M / cardinality fixtures with real `library` models; add package + HTTP coverage.") restates bullets 1 and 2. It is the card's `description` column rendered into the scope section — the identical defect card `DONE-011-0.0.4` carried. | `KANBAN.md` #"replace test-only M2M / cardinality fixtures" (line 4519), under `### [DONE-013-0.0.4 …]` `#### Scope` |

**F12 is recorded, not dispatched — and the reason is concurrency, not disposition.** `KANBAN.md` / `KANBAN.html` are generated from `examples/fakeshop/db.sqlite3`, so the fix is an ORM edit plus a regenerate (never a hand-edit). **`examples/fakeshop/db.sqlite3` and `docs/GLOSSARY.md` are both dirty at plan time with a concurrent session's uncommitted work.** The card-011 cycle dispatched its equivalent item only after verifying the DB was clean at `HEAD`; that precondition fails here, and a regenerate would publish a concurrent session's unlanded rows (`START.md` `## Concurrent sessions`). F12 therefore goes to the deferred-work catalog with its reversal recipe, and **this cycle makes no database write and runs no generator.**

## Baseline-dirty out-of-scope files

`HEAD` at plan time: `973d00b2c4cae3d3474dcd819b1c9a012d18bfe1`. `git status --porcelain | wc -l` -> **124**, and **not one of them is this cycle's**. Every path belongs to a concurrent maintainer session (`START.md` `## Concurrent sessions`, `AGENTS.md` rule 34). **No worker edits, reverts, stages, or `git checkout`s any of them.** In particular:

- `examples/fakeshop/db.sqlite3`, `docs/GLOSSARY.md` — dirty; see F12. No worker of this cycle opens either for writing, and no worker runs `scripts/build_kanban_md.py`, `build_kanban_html.py`, or `build_glossary_md.py`.
- `docs/SPECS/spec-009-…md` and its `appx/` rationale companion are modified right now by a concurrent residual-completion cycle. Read only as shape precedent, never as authority.
- `tests/types/test_definition_order.py` is dirty with a one-line concurrent edit. V4's evidence was therefore re-derived from `git show HEAD:<path>` rather than the working tree, per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`. Any pass needing it does the same.
- ~40 modified package sources, ~25 modified tests, and the `docs/review/` + `docs/bug_hunt/` scratchpads of an in-flight cycle. `AGENTS.md` rule 22 forbids touching `docs/review/` regardless.

**The list is moving.** Any pass that needs the baseline re-derives it rather than quoting this section.

## Pre-flight deviations, recorded

Two steps of `worker-0.md` `## Pre-flight procedure` did not run as written; both deviations protect concurrent sessions.

- **Step 3 (artifact reset).** **Nothing was deleted.** `docs/builder/bld-003-final.md`, `bld-009-r1-*.md`, `build-009-…md`, and `build-011-…md` are the committed records of closed cycles and one concurrent session's live plan. Deleting a prior cycle's record is the one irreversible pre-flight mistake that step names. What the step protects — that this cycle overwrites no existing path — was verified directly: every path in `## Artifact list` was confirmed absent, as was the rationale companion.
- **Step 5 (scratch directories cleared).** **Nothing was cleared.** `docs/builder/worker-memory/` holds seven files a concurrent session wrote, and `docs/shadow/` is that session's review substrate. Clearing either would destroy live work. This cycle instead uses **namespaced** memory files — `docs/builder/worker-memory/spec-013-worker-0.md` and `…/spec-013-worker-1.md` — following the precedent that session set. No worker of this cycle reads or writes any other file in that directory.

Steps 1, 2, 4, 6 ran: the baseline is enumerated above and included per the maintainer's knowing dispatch onto this tree; `scripts/review_inspect.py` smoke-invoked OK; `.gitignore` carries all three scratch paths; `check_spec_glossary --spec docs/SPECS/spec-013-…md` exits 0. Step 7 (rationale extraction) is item R1.

## Artifact list

- `docs/builder/bld-013-r1-rationale_and_spec_reconciliation.md`
- `docs/builder/bld-013-r2-doc_completion_archive_audit.md`
- `docs/builder/bld-013-final.md`

**No `bld-integration.md`.** `docs/builder/BUILD.md` `## Cross-slice integration pass` scans landed source for cross-slice duplication; this cycle lands no source at all, so there is no cross-slice DRY surface. Both of the pass's live obligations are folded into the final gate: the staged-anchor sweep, and the read of every closed artifact. Same disposition, and the same reason, as the spec-011 and spec-012 cycles.

## Checklist

- [x] R1: create the rationale companion and reconcile the spec against `HEAD` (F1-F8)
- [x] R2: documentation completion and archive audit (F9-F12)
- [x] Final test-run gate

Every item closed `final-accepted`.

## Cycle outcome, recorded

**The cycle's whole diff is five Markdown files** — the reconciled spec, its new rationale companion, and this plan plus three artifacts. No package source, no test, no database write, no generator run.

**One real spec-vs-code drift was found and fixed**, which is the outcome the maintainer's framing was aimed at. The spec's HTTP-tier bullet claimed `examples/fakeshop/test_query/test_library_api.py::test_library_optimizer_selects_book_shelf_in_http_query` shows the forward FK planned as `select_related` in a served query. True at the card's own commit (`67b07f79`: one query, `JOIN` in the SQL); **false at `HEAD`**, where `ShelfType` declares a `get_queryset` visibility hook and the optimizer downgrades the join to a visibility-scoped `Prefetch` — two queries. The flip landed at `1694bd2e` (2026-05-28) and `docs/GLOSSARY.md` documents the downgrade twice, so spec, tree, and glossary disagreed three ways. R2 rewrote the bullet present-tense and appended the cause, the rejected alternatives, and the retired claim to the rationale.

**The lesson, carried forward:** `path::QualifiedName` proves a symbol survives, not that the sentence describing it survives. All eleven test symbols the reconciled spec cites exist at `HEAD`; the falsified claim named a test that kept its name while its assertion was inverted — invisible to any grep, and reachable only by reading the test body against the sentence.

**The gate ran clean apart from one row it does not own.** `uv run pytest --no-cov` -> `1 failed, 5831 passed, 40 skipped`; the failure is `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol`, which reproduces in isolation, whose test file and production module are both byte-identical to `HEAD`, and which no item of this cycle could have touched. Recorded, diagnosed, and escalated rather than fixed or masked (`AGENTS.md` rule 34) — the same disposition, on the same file, the spec-011 cycle reached. Everything else passed: `manage.py check` and `makemigrations --check --dry-run` clean, `ruff format --check` / `ruff check` / `git diff --check` green tree-wide, `check_trailing_commas --check` and `check_spec_glossary` green on this cycle's files, floor-verification scope `none` as declared, and the staged-anchor sweep found zero surviving `TODO(spec-013` / `TODO-*-013` anchors in shipped source, tests, or standing docs.

**Six deferred items are catalogued in `bld-013-final.md`**, F12 among them with a ready-to-apply ORM recipe. F12 is the one piece of work this cycle identified and could not perform: `examples/fakeshop/db.sqlite3` is dirty with a concurrent session's uncommitted rows, so a regenerate would publish work that has not landed.

## Corrections to this plan, recorded

Figures in `## Worker-0 verification pass` that did not reproduce when R1 measured them, corrected here rather than left standing (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` — a stated count reads as measured and propagates silently):

- **`library/models.py` model count.** V1 said "7 models at creation, 12 today"; R1 measured **11** model classes at `HEAD`. The creation figure holds.
- **The `library/` -> `apps/library/` move.** The plan's F7 called the `apps/` namespace split "later"; R1 dated it to `a7ca9cc2`, **2026-05-07 17:58** — four hours after the card's last commit and the day *before* the `0.0.4` cut. F7's finding is unaffected (the path was still wrong for the card's own era, which is what a "likely touched" prediction field records), but the split was contemporaneous, not distinctly later.
- **V2's grep population.** "Zero hits outside `docs/builder/DONE/`" is really 5 documentary hits across archived cycle records. No source file or test references the retired app; the finding stands.

## Dispatch record

| Item | Passes dispatched | Why |
|---|---|---|
| R1 | Worker 1 only | The maintainer's standing instruction for this cycle: an item that changes only the spec and its rationale is Worker 1's alone, and both files are Worker 1-owned by `docs/builder/BUILD.md` `## Spec reconciliation` in any case. |
| R2 | Worker 1 only | Its findings are inside the spec and its companions. The one durable-doc-shaped finding (F12) is DB-backed and blocked on a dirty `db.sqlite3`, so it is catalogued rather than built. |
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
