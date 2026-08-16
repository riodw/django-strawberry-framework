# Build: R2 — Documentation completion and archive audit (013 / real_m2m_coverage / 0.0.4)

Spec reference: `docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md` (whole file; 77 lines, 5,533 bytes at
R2 entry, 5,739 after)
Status: final-accepted

This is a **review-round-shaped** item of a residual-completion cycle, dispatched to Worker 1 alone
(`docs/builder/build-013-real_m2m_coverage-0_0_4.md` `## Dispatch record`). It writes no code, so
`docs/builder/BUILD.md` `### Isolation is non-waivable` does not bind it and this pass performs both
the work and its own final verification.

Writable set as dispatched, and nothing else was touched:

- `docs/builder/bld-013-r2-doc_completion_archive_audit.md` (this file, created)
- `docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md` (one defect-driven correction, below)
- `docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-rationale.md` (appended only)
- `docs/builder/worker-memory/spec-013-worker-1.md`

This pass made **no database write and ran no generator**, per the plan's F12 disposition:
`examples/fakeshop/db.sqlite3` and `docs/GLOSSARY.md` are dirty with a concurrent session's
uncommitted work, and neither was opened for writing or reading.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately skipped, for the reason R1 recorded:
  the package-wide AST inventory exists to prevent duplicated *code* shapes before a builder writes
  them. This item's writable set is three Markdown files, it plans no helper, constant, validation
  branch, or test helper, and no pass of this cycle touches `django_strawberry_framework/`.
- **Existing patterns reused.** The audit shape is the one the two closed residual cycles' R2 items
  used (`docs/builder/build-011-stale_placeholder_cleanup-0_0_4.md` `### R3, added after R2` records
  what its R2 reported rather than built, and the same DB-backed disposition). The link-scaffold and
  ref-id checks are the mechanical form `START.md` `## Markdown link convention` defines; they were
  run as one script over both files rather than eyeballed.
- **New helpers justified.** None. No executable artifact of any kind; the audit script was run
  inline through `uv run python -` and written nowhere.
- **Duplication risk avoided.** One. Re-arguing in the rationale a disposition R1 already argued
  (the `[backlog]` cluster, the KANBAN staleness) — avoided by appending only what **this** audit
  found and pointing at R1's entries for the rest.

### Implementation steps

1. Re-derive every factual claim in the reconciled `## Scope` at `HEAD` (`973d00b2`), reading each
   dirty file via `git show HEAD:<path>` into a scratch path outside the repository.
2. Confirm the out-of-scope fence: each disclaimed model/field exists at `HEAD` and post-dates the
   card's last commit.
3. Read the spec for narrated history; read the rationale for anchor resolution against the
   **rewritten** headings.
4. Run the archive audit mechanically: link-definition resolution from each file's own directory,
   the ten canonical group headers, group-of-target correctness, alphabetical order, inline-link
   sweep, ref-id defined/unused sets, `check_spec_glossary`, `check_trailing_commas`, terms-CSV shape.
5. Verify F11 independently and check the four surfaces it does not name.
6. Sweep inbound `spec-013` references and staged anchors.
7. Fix every defect the audit proves; defer with evidence anything outside the writable set.

Line numbers are pin-at-write-time navigational hints.

### Test additions / updates

None, and none is possible: this item's writable set contains no test file. One focused `--no-cov`
run was considered to confirm a cited test passes and was **not** needed — the falsified claim was
established by reading the assertion at `HEAD` and at the commit that changed it, which is stronger
evidence than a green run (a green run proves the test passes, not that the spec describes it).
No `pytest` invocation was made by this pass and no `--cov*` flag was used anywhere.

### Implementation discretion items

None. The one spec edit is argued in the rationale with its rejected alternatives.

### Dispatched findings checklist

One box per finding as `docs/builder/build-013-real_m2m_coverage-0_0_4.md` `### R2 findings` states
it. F12 is quoted as stated but was **recorded, not dispatched** by the plan; it is carried here
un-ticked with its deferral reason and reversal recipe so the audit is complete.

- [x] **F9** — "The spec is already at `docs/SPECS/` and every link definition resolves at that depth
  (`../../KANBAN.md`, `../GLOSSARY.md#relation-handling`), and the file is already reference-style
  with all ten canonical group headers. The archive move itself is therefore **done**; what R2 owes
  is the audit and the new companion's own link hygiene." Audit performed mechanically over **both**
  files at their differing depths; every one of the 9 spec defs and 19 rationale defs resolves to an
  existing file, and each sits in the group of its **target's** location. Details in
  `### B — Archive audit`.
- [x] **F10** — "The card's single glossary anchor resolves and carries the right shipped version:
  `#relation-handling` -> `docs/GLOSSARY.md` `## Relation handling`, **Status:** shipped (`0.0.1`+).
  `KANBAN.md`'s `DONE-013-0.0.4` card renders it." Confirmed at `HEAD` (the glossary was read via
  `git show HEAD:docs/GLOSSARY.md` because the working copy is dirty), and the terms CSV is one row
  per anchor.
- [x] **F11** — "The durable docs the card's work belongs in are already complete and correct:
  `docs/TREE.md` carries the `apps.library/` app-role paragraph naming 'many-to-many joins' and lists
  `examples/fakeshop/apps/library/tests/test_schema.py`; `AGENTS.md` rule 7 carries the four-tier
  test-placement rule this card's commit introduced. **No durable-doc edit is owed.**" Verified
  independently rather than accepted, plus the four surfaces F11 does not name. Details in
  `### C — Documentation completion`.
- [ ] **F12** — "The rendered `DONE-013-0.0.4` card body carries a **duplicate `#### Scope` row**:
  bullet 3 ('replace test-only M2M / cardinality fixtures with real `library` models; add package +
  HTTP coverage.') restates bullets 1 and 2. It is the card's `description` column rendered into the
  scope section — the identical defect card `DONE-011-0.0.4` carried." **Deferred, by the plan's own
  disposition.** The defect is real and was re-confirmed at `KANBAN.md` line 4519; the fix is an ORM
  edit plus a regenerate, and `examples/fakeshop/db.sqlite3` is dirty with a concurrent session's
  uncommitted work, so a regenerate would publish rows that have not landed (`START.md`
  `## Concurrent sessions`). Reversal recipe and one mechanism correction in
  `### Deferred work list`.

---

## Build report (Worker 1, acting for this item)

### Files touched

- `docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md` — one bullet corrected, 5,533 -> 5,739 bytes,
  77 lines unchanged (`wc -c -l`). See `### Spec changes made (Worker 1 only)`.
- `docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-rationale.md` — **appended only**, 37,372 ->
  41,636 bytes / 532 -> 595 lines. One new `## Audit record` section carrying the defect, its cause,
  the rejected alternatives, the claim the spec may no longer make, and one inbound-staleness note.
  No existing line was edited (`worker-1.md` `### Performing the rationale move` rule 4).
- `docs/builder/bld-013-r2-doc_completion_archive_audit.md` — this artifact.
- `docs/builder/worker-memory/spec-013-worker-1.md` — memory entry appended.

Nothing else. `git status --porcelain` after the pass shows **130** paths; the delta against R1's
recorded 129 is this artifact. Every baseline-dirty path was left exactly as found — none was
edited, reverted, staged, stashed, `git checkout`ed, or `git restore`d. The three `HEAD` blobs this
pass needed from dirty files (`tests/types/test_definition_order.py`,
`examples/fakeshop/test_query/test_library_api.py`, `docs/GLOSSARY.md`) were read via
`git show HEAD:<path>` into a scratch path **outside** the repository.

### A — Audit of R1's output, as an adversary

`HEAD` = `973d00b2c4cae3d3474dcd819b1c9a012d18bfe1`. Every row below is a re-derivation, not a read
of R1's artifact.

**A1. Every factual claim in `## Scope`, walked.**

| Claim | Verdict | How it was checked |
|---|---|---|
| the retired `tests_cardinality` app is genuinely absent | holds | `git ls-tree -r HEAD --name-only \| grep -c "^tests/fixtures/"` -> 0; `tests/fixtures` absent on disk; `grep -rn "tests_cardinality\|cardinality_models"` (excluding `.git`, `.venv`, `__pycache__`, `*.sqlite3`) -> 11 hits, **every one documentary** (this spec + its rationale + this cycle's plan and artifacts + `spec-011-…-rationale.md`). No source file and no test names it. |
| the five retired models `User`, `Profile`, `Author`, `Tag`, `Book` and their six edges | holds | `git show 1057ddc2~1:tests/fixtures/cardinality_models.py` — five `class` declarations, all `managed = False` under `app_label = "tests_cardinality"`; `Profile.user` O2O, `Book.author` FK `related_name="books"`, `Book.tags` M2M `related_name="books"` |
| six cardinality rows name real fields on real models | **all six hold** | `git show HEAD:examples/fakeshop/apps/library/models.py`: `MembershipCard.patron = OneToOneField(Patron, related_name="card")` gives rows 1 and 2; `Book.shelf = ForeignKey(Shelf, related_name="books")` gives rows 3 and 4; `Book.genres = ManyToManyField(Genre, related_name="books")` gives rows 5 and 6 |
| eleven test functions exist at `HEAD` with those exact names | **all eleven hold** | `grep -c "def <name>("` per symbol against the `HEAD` blob of each of the four files -> **1** for every one of the eleven. The two package files and `test_library_api.py` were read at `HEAD`, not the working tree |
| `library_book_genres` really is in **both** attributed tests | holds | `awk` over the `HEAD` blob attributing each occurrence to its enclosing `def`: `test_library_reverse_fk_and_m2m_prefetch_sql_shape_over_http` (`assert "library_book_genres" in sql`) and `test_library_consumer_prefetched_queryset_cooperates_with_optimizer_over_http` (`assert "library_book_genres" in prefetch_sql`). Four further occurrences live in later cards' tests and are correctly not claimed |
| `[GenreType!]!` matches what the live introspection test asserts | holds | `test_book_genres_m2m_renders_as_list_shape_live` unwraps `NON_NULL -> LIST -> NON_NULL -> OBJECT` and asserts `name == "GenreType"`, from `_introspect_type("BookType")` — the served schema, not a locally constructed one |
| package-tier annotation claims | hold | `test_many_to_many_forward_and_reverse_relations_resolve` asserts `BookType.__annotations__["shelf"] is ShelfType`, `["genres"] == list[GenreType]`, `GenreType…["books"] == list[BookType]`, `ShelfType…["books"] == list[BookType]`; `test_one_to_one_forward_and_reverse_relations_resolve` asserts `MembershipCardType…["patron"] is PatronType` and `PatronType…["card"] == (MembershipCardType \| None)` |
| optimizer-planning claims | hold | `test_plan_relation_decisions_match_cardinality_after_finalization` asserts `("prefetch","default")` for `Book.genres` and `Genre.books`, and `("select","default")` for `MembershipCard.patron` and `Patron.card` |
| per-app schema claims | hold | `test_project_schema_includes_library_types` asserts `{"title","shelf","genres"} <=` `BookType`'s introspected field names through `project_schema.execute_sync` |
| traversal / reverse-path HTTP claims | hold | `test_library_patron_card_and_genre_reverse_paths_over_http` pins reverse O2O (`card`, including the `None` case for a card-less patron) and reverse M2M (`allLibraryGenres { books }`) in the response body |
| forward FK "planned as `select_related` in a served query" | **DOES NOT HOLD** | see `### DEFECT-1` below |

**DEFECT-1 — the one claim that failed, and it is exactly the class this cycle exists for.**
The spec's HTTP-tier bullet said `::test_library_optimizer_selects_book_shelf_in_http_query` shows
"the forward FK is planned as `select_related` in a served query". At the card's own commit that was
literally what the test asserted (`git show 67b07f79:…/test_library_api.py`: `len(captured) == 1`
plus `"JOIN" in sql`). At `HEAD` the same test asserts `len(captured) == 2`, with `library_book` in
the first query and `library_shelf` in the second, under the comment that `ShelfType.get_queryset`
implements the nested-visibility contract so the optimizer "correctly downgrades
`select_related("shelf")` to Prefetch". The flip landed at `1694bd2e` "Finish
build-021-filters-0_0_8" (2026-05-28) — `git show 1694bd2e~1:<path>` carries `== 1`,
`git show 1694bd2e:<path>` carries `== 2`.

The claim also **contradicted `docs/GLOSSARY.md`**, which documents the downgrade twice
(`#"the optimizer downgrades a JOIN to a ``Prefetch`` when a target type defines one"` and the
`get_queryset` downgrade bullet in the optimizer entry) — so the spec, the tree, and the glossary
disagreed three ways. Fixed in the spec, recorded in the rationale with its rejected alternatives.

**Why a name-existence sweep could not have found it, recorded for the next cycle.** All eleven
`path::QualifiedName` citations resolve; the falsified one names a test that still exists under its
original name with its assertion inverted. `path::QualifiedName` fails loudly on rename — it is
silent on an assertion flip. Only reading each cited body against the sentence describing it closes
that gap, and that is the check R2 owes that no grep discharges.

**A2. The out-of-scope fence is accurate.** Every disclaimed item exists on the model at `HEAD` and
arrived after the card's last commit (`67b07f79`, 2026-05-07 13:50):

| Fence item | On the model at `HEAD` | Arrived |
|---|---|---|
| generic relation | `TaggedItem` + `Branch.tags = GenericRelation(...)` | `d592ac3a`, 2026-05-08 12:07 |
| its proxy-model variant | `ProxyBranch(Branch)` with `proxy = True` + `proxy_tags` | `41008e4c`, 2026-07-17 21:11 |
| `Shelf.alt_branches` | `ManyToManyField` to `Branch` | `d1fb4cf2`, 2026-06-24 23:57 |
| the `BigIntegerField` | `Patron.lifetime_fines_cents` | `cae2d5a3`, 2026-05-27 17:27 |
| the keyset models | `Periodical`, `Issue` | `51421e54`, 2026-07-10 21:10 |

Cross-checked from the other direction: `git show 73004d74:examples/fakeshop/library/models.py`
carries **7** `^class` declarations and none of the five fence items; the `HEAD` blob carries **11**.
R1's correction of the plan's "12" reproduces exactly.

**A3. No claim in the spec narrates history.** `grep -nEi "as of|amendment|previously|no longer|used
to|originally|formerly|review round|[0-9a-f]{8}"` over the spec returns exactly **one** line — line
7, the pointer sentence naming what moved to the rationale, which `worker-1.md`
`### Performing the rationale move` rule 1 **requires**. No amendment block, no retraction
paragraph, no chronology, no commit hash. The corrected bullet was written in the present tense for
the same reason. The spec reads as a clean current contract.

**A4. The rationale is a usable review instrument.** Every entry opens by naming the spec section it
belongs to, by heading and by reference-style anchor link. R1 rewrote the spec's headings, so each
anchor was re-resolved against the **current** headings rather than assumed: the spec's `##` headings
at `HEAD`+R1 are exactly `## Card snapshot` and `## Scope`, and the rationale's only two
spec-targeting anchors are `#card-snapshot` and `#scope`. Both resolve. The two entries keyed to
removed headings (`## Planning note`, `## Other`) say so in their first line and anchor the surviving
section their subject bears on — which is the shape that keeps them lookup-able. Every entry carries
rejected alternatives with the reason each lost, the change record, and an explicit "claim the spec
may no longer make". The new `## Audit record` section was written to the same shape.

**A5. No contradictions.** The two files agree with each other (the six-edge table, the eleven
citations, the model counts, and the fence are stated once each and cross-referenced, never
restated divergently). Against `docs/TREE.md`: the `apps.library/` role paragraph names the same
relation surface. Against `AGENTS.md` rule 7: the spec's three-tier split of its citations
(`tests/`, `examples/fakeshop/test_query/`, `examples/fakeshop/apps/<app>/tests/`) is that rule's
partition, and every cited path sits in the tier rule 7 assigns it. Against rule 10: the card's
live-first coverage is where rule 10 requires it, and the one relocation is rule 10 being applied.
Against `docs/GLOSSARY.md` `## Relation handling`: the six sub-anchors (forward/reverse FK, O2O, M2M)
are the same six cardinalities, and the glossary's planning statements (`select_related` for forward
FK/O2O, `prefetch_related` for reverse FK and both M2M halves) match the spec's optimizer-tier claims
exactly — after DEFECT-1 was fixed, which is the sentence that had disagreed.

### B — Archive audit

Run as one script over both files rather than by eye; every path was resolved from **its own**
directory and disk-checked.

- **Link-definition resolution.** All **9** spec definitions and all **19** rationale definitions
  resolve to a file that exists. The differing depth is correct in both directions: the spec's
  `../../KANBAN.md` and the rationale's `../../../KANBAN.md` both resolve to the repository-root
  `KANBAN.md`; the spec's `../GLOSSARY.md` and the rationale's `../../GLOSSARY.md` both resolve to
  `docs/GLOSSARY.md`. **The masking trap was checked by resolving, not by reading**: each definition
  was `resolve()`d and its repository-relative path printed, so a same-named file one level up could
  not have passed as the intended target. Every printed target is the intended file.
- **Delimiter and group headers.** Both files carry exactly one `<!-- LINK DEFINITIONS -->` line and
  all ten canonical group headers in the exact `START.md` order, present even when empty.
- **Group = the target's location.** Every definition was re-derived to its expected group from the
  resolved path and compared with the group it sits under: **zero mismatches** in either file. The
  `docs/SPECS/appx/` definitions correctly sit under `<!-- docs/SPECS/ -->` (the ten headers are a
  closed list; a subdirectory shares its parent's group).
- **Alphabetical within each group.** Holds in both files.
- **No inline `](path)` cross-file link.** Zero in either file, code spans and fenced blocks stripped
  before matching. URLs and in-page anchors: none present, so none was miscounted as a defect.
- **Ref-ids.** Zero undefined uses in either file. Unused definitions: the rationale has **none**;
  the spec has exactly one, `[backlog]` — **recorded, not partial-fixed**, per R1's disposition and
  `worker-0.md` `## Closing out a kanban card`. It is one file of the 71-definition / 23-file cluster
  `TODO-ALPHA-052-0.1.0` owns, and `KANBAN.md` line 340 names `spec-013` in the eight-spec `[backlog]`
  list. Re-verified as still-correct, so the board claim needs no change from this cycle.
- **`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md`**
  -> `OK: 1 terms - all have glossary entries and at least one spec link.` (exit 0), re-run **after**
  the spec edit.
- **Terms CSV shape.** `docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-terms.csv` holds a header
  plus exactly **one** data row (`M2M traversal,relation-handling,…`) — one row per anchor, the shape
  `import_spec_terms` requires, which `check_spec_glossary` alone does not prove. Audited, not
  edited.
- **`uv run python scripts/check_trailing_commas.py --check <spec> <rationale>`** -> exit 0, re-run
  after both edits, in `--check` mode only so neither file was auto-rewritten. Also run clean over
  this cycle's plan and R1 artifact.

### C — Documentation completion

**F11 verified independently, not accepted.**

- `docs/TREE.md` line 911ff carries the `apps.library/` app-role paragraph, and it names
  "many-to-many joins" among the relations the app proves. Line 601 lists
  `library/tests/test_schema.py` with its own role comment; lines 596-601 list the whole per-app
  library test tree. `docs/TREE.md` is **clean** in the working tree, so this is `HEAD` content.
- `AGENTS.md` rule 7 carries the four-tier test-placement rule (`tests/` package tier,
  `examples/fakeshop/apps/<app>/tests/` per-app tier, `examples/fakeshop/test_query/` live tier,
  `examples/fakeshop/tests/` project tier, plus the `tests/base/` two-file reservation). That this
  card's commit introduced it is confirmed by `git show 67b07f79 -- AGENTS.md`, which rewrites the
  test-placement paragraph to name `test_library_api.py` as the live acceptance suite and adds the
  "library acceptance tests use inline `Model.objects.create(...)`" rule now standing as rule 9.
  `AGENTS.md` is clean in the working tree.

**The four surfaces F11 does not name, checked here.** None owes an edit:

- `TODAY.md` — its line 5 scope note **forbids** enumerating the non-`products` apps ("Do **not**
  broaden this file to enumerate the other apps"), and its lines 374-381 already reference `library`
  as the app carrying the O2O / M2M surface products cannot reach. Nothing owed; adding anything
  would violate the file's own stated scope.
- `docs/README.md` — line 101 lists "relation conversion (forward / reverse FK, forward / reverse
  OneToOne, forward / reverse M2M)" as shipped package capability, which is this card's six edges.
  Nothing owed.
- `CHANGELOG.md` `## [0.0.4]` — its `### Added` block already carries both halves of this card:
  "Relation finalization support for FK, reverse FK, OneToOne, reverse OneToOne, and M2M fields" and
  "A restructured `examples/fakeshop` project with a real API-testing app, migrations, schema
  examples, and query tests". `AGENTS.md` rule 21 forbids CHANGELOG updates unless instructed, and
  none was. Nothing owed.
- `examples/fakeshop/test_query/README.md` — line 11 describes `test_library_api.py` as the first
  live API suite covering "FK and reverse-FK traversal, OneToOne nullability, M2M traversal, …
  optimizer SQL shape". Nothing owed.

**No durable-doc edit is owed by this card, and none was made.** Had one been owed on
`docs/TREE.md` it would still have been a report rather than an edit: that file is script-rendered
by `scripts/build_tree_md.py` from module docstrings plus the kanban DB, so a hand edit is reverted
by the next render and a regenerate is barred by this cycle's no-generator rule.

### D — Inbound-reference sweep

`grep -rln "spec-013"` across the tree (excluding `.git`, `.venv`, `__pycache__`, `*.sqlite3`)
returns 14 files. Excluding this cycle's own four (`spec-013` + its rationale + the plan + the R1
artifact) and `KANBAN.html` (the Vue shell's data block, regenerated from the same DB as
`KANBAN.md`), the inbound set is:

| Site | Verdict |
|---|---|
| `KANBAN.md:134`, `KANBAN.md:4501` | correct — the card's `SpecDoc` link, path unchanged by R1 |
| `KANBAN.md:340` | correct — the eight-spec unused-`[backlog]` catalogue; `spec-013` still belongs on it (re-measured: the definition is still there, deliberately) |
| `KANBAN.md:341` | **stale, deferred** — "Four archived stubs still carry the boilerplate … preamble: `spec-013`, `spec-016`, `spec-024`, `spec-026`". Re-measured by `grep -c 'expand it into the full builder-format spec'` per file: `spec-016` 1, `spec-024` 1, `spec-026` 1, `spec-013` **0**. The correct figure is **three**. R1 routed it; it stays deferred |
| `docs/SPECS/appx/spec-011-…-rationale.md:28` | **stale, deferred** — says five still carry it (`spec-012`, `spec-013`, `spec-016`, `spec-024`, `spec-026`); measured **three**. It was already stale by one before this cycle (the spec-012 cycle). Prior cycle's committed file, outside the writable set |
| `docs/SPECS/appx/spec-011-…-rationale.md:256` | correct — the eight-spec `[backlog]` list |
| `docs/SPECS/appx/spec-012-…-rationale.md:348` | correct — same `[backlog]` list |
| `docs/builder/DONE/build-001-django_types-0_0_1.md:151` | correct — "M2M coverage shipped \| spec-013"; the reconciliation strengthens it |
| `docs/builder/DONE/build-012-…md:76` | correct — the `[backlog]` eight-spec list |
| `docs/builder/DONE/build-007-…md:254` | **stale, deferred, and new to this sweep** — a smallest-specs ranking naming "spec-013 (1,669 bytes)". R1's reconciliation made the file 5,533 bytes and this pass 5,739. See `### Deferred work list` |
| `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` (3 body uses + 1 def) | **false positive, confirmed** — the ref-id `[spec-013]` is defined as `spec-017-deferred_scalars-0_0_6.md`; every body use reads "`docs/SPECS/spec-017-deferred_scalars-0_0_6.md`" in its link text. Names spec-017, not card 13 |
| `docs/SPECS/spec-018-meta_primary-0_0_6.md:175`, `docs/SPECS/spec-019-…md:133` | **false positives, confirmed** — both name a pre-renumber "`spec-013-deferred_scalars`" in a `0.0.6` sibling-card note. Neither names this card |

**Nothing else's claim about this spec was broken by R1's rewrite.** The only rewrite-caused
inbound staleness is the `build-007` byte figure, and the two preamble-count sites R1 already
routed. All three are cross-surface or prior-cycle-owned and are catalogued rather than partial-fixed.

### E — Staged-anchor sweep

`grep -rEn 'TODO\(spec-013|TODO-(ALPHA|BETA|STABLE)-013' .` excluding `.git`, `.venv`,
`__pycache__`, `*.sqlite3`, `KANBAN.md`, `KANBAN.html`, and `BACKLOG.md` returns **exactly one**
hit: `docs/builder/bld-013-r1-rationale_and_spec_reconciliation.md:279`, R1's own quotation of the
command inside a per-cycle scratchpad. **No staged anchor exists in shipped source, tests, or any
standing doc.** Nothing to remove, and no finding.

### Failability proofs

None; this pass introduced no new boundary. Its writable set is three Markdown files and it added no
guard, gate, or rejection path.

### Hot-path budget

Not applicable; plan declares no hot path (`docs/builder/build-013-real_m2m_coverage-0_0_4.md`
preamble: "Hot-path declaration: none").

### Floor verification

Not applicable; plan declares floor-verification scope none — no item of this cycle touches
executable code.

### Implementation notes

- **The corrected bullet states the plan, the downgrade, its cause, and the observable shape** rather
  than just deleting the falsified half. The forward FK *is* still planned as `select_related`; what
  a later contract changed is what the planner may execute once the target type declares
  `get_queryset`. Stating only "two queries" would have lost the planning fact the package tier
  independently pins, and stating only the plan is what was wrong.
- **The `library_book_genres` occurrence count was attributed, not counted.** `grep -c` on the file
  returns 6; three of those live in later cards' tests. Attributing each occurrence to its enclosing
  `def` with `awk` is what proves the spec's *two*-test claim, where a count would only have been
  consistent with it.
- **The spec edit is the only one the audit could prove.** Several sentences could have been written
  more tightly; none was false, and `worker-1.md` `## Spec custody` licenses an edit only where the
  build proves the spec inaccurate.

### Notes for Worker 3

No Worker 3 pass is dispatched for this item (`## Dispatch record`: "Worker 1 only"). The
verification a reviewer would run is above, with the command or blob for each row.

### Notes for Worker 1 (spec reconciliation)

Everything this pass owes the final gate is in `### Deferred work list`. Two items carry forward from
R1 unchanged (the preamble-count staleness and the `[backlog]` cluster) and two are new (the
`build-007` byte figure, and F12's mechanism correction).

---

## Final verification (Worker 1)

- **Dispatched findings checklist:** F9, F10, F11 `- [x]`, each confirmed against the audit
  performed in this pass rather than against R1's record. F12 `- [ ]` with its deferral reason and
  reversal recipe. No box is ticked without matching audit evidence.
- **Every planned step implemented.** Steps 1-7 all ran; none was rejected.
- **DRY check against prior accepted work:** the rationale append cites R1's entries rather than
  re-arguing them, and the artifact does not restate the spec's content. No new duplication.
- **Claims proven mechanically** (`docs/builder/BUILD.md` `## Claims are proven mechanically, never
  accepted on prose`): every count in this artifact is either a listed set the reader can re-derive
  (the eleven symbols, the five fence items, the inbound sites) or was measured as it was written.
  The one relocation-shaped claim — that the `select_related` assertion flipped at `1694bd2e` — was
  proven by blob comparison at the commit and its parent, both quoted.
- **Existing tests:** none run, and none owed — this item's writable set contains no test and no
  source. No `--cov*` flag was used anywhere in this pass.
- **Staged-anchor sweep:** performed, `### E` above. Zero anchors in shipped surfaces.
- **No fail-open shape landed.** Not applicable to a Markdown-only diff, confirmed by reading it.
- **Final status:** `final-accepted`. The audit is complete and every defect is either fixed
  (DEFECT-1) or deferred with its evidence and reason.

### Summary

Audited R1's reconciled spec and its new rationale companion as an adversary and audited the archive.
Of the reconciled `## Scope`'s claims, everything checkable by grep held: the retired
`tests_cardinality` app is genuinely gone from every live surface, all six cardinality rows name real
fields on real `library` models, **all eleven** cited test functions exist at `HEAD` under those exact
names, the `library_book_genres` SQL pin really is in both attributed tests, the `[GenreType!]!` claim
matches the live introspection assertion, and every out-of-scope fence item is on the model at `HEAD`
and post-dates the card. **One claim was false**: the forward FK is no longer served as a
`select_related` join — `1694bd2e` flipped that test to assert the optimizer's `get_queryset`
downgrade to a visibility-scoped `Prefetch`, which is what `docs/GLOSSARY.md` documents and the spec
contradicted. Corrected in the spec and recorded in the rationale with its rejected alternatives.
The archive audit is clean: 28 link definitions across the two files all resolve at their differing
depths to the intended target, all ten group headers present and ordered in both, groups keyed to the
target's location, zero inline cross-file links, zero undefined ref-ids, `check_spec_glossary` and
`check_trailing_commas` green, and the terms CSV one row per anchor. No durable-doc obligation is
open: F11's two surfaces verified independently and the four it does not name checked as well. The
staged-anchor sweep is empty; the inbound sweep confirms R1's three false positives and adds one new
byte-count staleness.

### Spec changes made (Worker 1 only)

| Spec lines | Change | Reason |
|---|---|---|
| 1-5 | header block re-verified, left unchanged | `worker-1.md` `## Spec status-line re-verification`: title, target release `0.0.4`, `Status: shipped`, owner all still accurate at `HEAD`; no predecessor reference to update. R1 verified the same block; this is the independent re-verification the per-spawn rule requires |
| 41 | HTTP-tier bullet for `::test_library_optimizer_selects_book_shelf_in_http_query` rewritten: "the forward FK is planned as `select_related` in a served query" -> "…planned as `select_related` in a served query and, because `ShelfType` declares a `get_queryset` visibility hook, that plan is downgraded to a visibility-scoped `Prefetch`: two queries, the first over `library_book` and the second over `library_shelf`." | **DEFECT-1.** The old claim is falsified at `HEAD` (the test asserts `len(captured) == 2` and a Prefetch downgrade, flipped at `1694bd2e`) and contradicted `docs/GLOSSARY.md`, which documents the downgrade. Stated as the current contract with no chronology, per `docs/builder/BUILD.md` `## Spec rationale extraction` |
| (rationale, appended) | new `## Audit record` section: the DEFECT-1 entry keyed to `## Scope` with its rejected alternatives and the claim the spec may no longer make, plus the `build-007` inbound-staleness note | `worker-1.md` rule 4 — the rationale is append-only during the build, and records what this audit found. No existing line was edited |
| 51 | `[backlog]` kept, again | **F8 / F12-adjacent deferral, unchanged.** Still the only unused definition; still one file of the 71-definition cluster `TODO-ALPHA-052-0.1.0` owns. Partial-fixing leaves the surface divergently rather than uniformly wrong |

### Deferred work list

One bullet per item, naming the source, the evidence, and why it was not fixed here. All five are
outside this item's writable set or barred by the cycle's no-database-write rule.

- **F12 — the `DONE-013-0.0.4` card body's duplicate `#### Scope` row.** *Source:* the plan's
  `### R2 findings` F12. *Evidence:* `KANBAN.md` line 4519 under `### [DONE-013-0.0.4 …]`
  `#### Scope`, bullet 3 ("replace test-only M2M / cardinality fixtures with real `library` models;
  add package + HTTP coverage.") restating bullets 1 and 2 — re-confirmed by reading the rendered
  card. *Why not fixed:* `KANBAN.md` / `KANBAN.html` render from `examples/fakeshop/db.sqlite3`,
  which is **dirty with a concurrent session's uncommitted work**; a regenerate would publish rows
  that have not landed (`START.md` `## Concurrent sessions`), and a hand-edit of a generated file is
  reverted by the next render. The card-011 cycle dispatched its equivalent item only after
  verifying the DB was clean at `HEAD`; that precondition fails here.
  **Reversal recipe (one step, once the DB is clean at `HEAD`):** through the Django ORM against
  `examples/fakeshop/db.sqlite3`, delete the third `#### Scope` bullet of card 13 — identified by its
  text rather than by an assumed index, since `CardItem.order` is not re-derivable without opening
  the DB this cycle may not touch:
  `CardItem.objects.get(card__number=13, section__key="scope", text__startswith="replace test-only M2M").delete()`
  (`CardItem.card` -> `Card.number` `PositiveIntegerField`; `CardItem.section` -> `Section.key`
  `SlugField`, both read from `examples/fakeshop/apps/kanban/models.py` at `HEAD`). Then regenerate
  `KANBAN.md` and `KANBAN.html`. Nothing else changes; the spec and rationale already carry the
  non-duplicated form.
  **Mechanism correction to F12, measured:** the plan says the duplicate "is the card's
  `description` column rendered into the scope section". It is not.
  `scripts/build_kanban_md.py::render_card` builds every `#### <section>` block from `card["items"]`
  grouped by section, and the renderer's only use of a `description` key is the relative-size legend
  (`grep -n "description" scripts/build_kanban_md.py` -> two hits, both in the size legend). The
  duplicate is a third `CardItem` row on the `scope` section whose text happens to equal the card's
  description — an importer artifact, not a render path. The fix target is a row, not a column, which
  is why the recipe above names one.
- **`KANBAN.md:341` — the archived-stub preamble count is now stale.** *Source:* R1's
  `### Inbound spec-013 references`, re-measured here. *Evidence:* the line says four
  (`spec-013`, `spec-016`, `spec-024`, `spec-026`); `grep -c 'expand it into the full builder-format
  spec'` returns 1 for each of `spec-016` / `spec-024` / `spec-026` and **0** for `spec-013`. The
  correct figure is **three**. *Why not fixed:* DB-backed, same blocker as F12 — an ORM edit plus a
  regenerate.
- **`docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-rationale.md:28` — the same count, in a
  prior cycle's committed rationale.** *Evidence:* it says five still carry it (`spec-012`,
  `spec-013`, `spec-016`, `spec-024`, `spec-026`); measured **three**. It was already stale by one
  before this cycle, from the spec-012 residual cycle. *Why not fixed:* a prior cycle's committed
  rationale is outside this cycle's writable set (`AGENTS.md` rule 22's spirit and the dispatch's
  explicit do-not-touch list), and fixing one of the two co-stale sites while the DB-backed one stays
  wrong is the partial fix `worker-0.md` `## Closing out a kanban card` forbids.
- **`docs/builder/DONE/build-007-onboarding_docs_spec_consolidation-0_0_4.md:254` — a smallest-specs
  byte ranking naming "spec-013 (1,669 bytes)".** *Source:* this pass's inbound sweep; new, not in
  R1's record. *Evidence:* the spec is 5,739 bytes after this pass, so the ranking's figure and
  ordering are both stale. *Why not fixed:* it is a closed cycle's committed record of a measurement
  taken at its own date, not a live claim restated anywhere; the spec-012 residual cycle left the
  equivalent spec-012 figure standing for exactly this reason, and prior cycles' `build-*.md` files
  are in this dispatch's do-not-touch list. Recorded in the rationale's `## Audit record` as well.
- **F8 — the unused `[backlog]` link definition.** *Source:* the plan's `### R1 findings` F8, carried
  forward unchanged. *Evidence:* `grep -c '\[backlog\]'` over the spec -> 1, the definition itself;
  re-confirmed by this pass's ref-id audit as the file's only unused definition. *Why not fixed:*
  one file of a 71-definition / 23-file cross-surface cluster owned by `TODO-ALPHA-052-0.1.0`, which
  `KANBAN.md` line 340 already catalogues by name. A spec-only correction diverging from
  un-editable copies is worse than uniformly wrong.

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
