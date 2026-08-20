# Package build plan: scalar_conversion_fakeshop / 0.0.7 (026)

Spec source: `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` (already archived; the active-spec path `docs/spec-026-scalar_conversion_fakeshop-0_0_7.md` does not exist)
Target release: `0.0.7` (shipped 2026-05-27; tag `0.0.7`)
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Ownership partition: none; sequential slices. Slices 1 and 3 are Worker 1's alone; Slice 2 is the only slice with a Worker 2 / Worker 3 cycle.
Hot-path declaration: none. No production code changes. Slice 2 edits comment and docstring text only; nothing runs per request, per resolver, or per row.
Floor-verification scope: none. No slice touches a Django / Strawberry / channels integration seam.
Pre-flight: passed on 2026-08-18 with two recorded deviations (below); baseline: DIRTY with two concurrent sessions' work.

## Cycle shape — residual reconciliation of a STUB spec, not a fresh build

`DONE-026-0.0.7` shipped inside the `0.0.7` joint cut across two commits. Worker 0 verified every claim the spec makes against HEAD and against the ship commits before writing this plan (evidence in `## Pre-dispatch verification`): **nothing was skipped in the code.**

Two things did not land:

1. `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` is a **3,593-byte stub** — the only surviving stub in the `015`+ builder-format era. It carries a `## Card snapshot`, a one-word `## Planning note`, and a `## Other` bullet list lifted from the ship commit message. It has no `## Slice checklist`, no `## Architectural decisions`, no `## Test plan`, and no `## Definition of done`, so there is nothing for a reader to audit the shipped code against. Its own body still instructs a reader to "expand it into the full builder-format spec … before implementation work starts from this file" — implementation finished fifteen months of cards ago.
2. The spec's `-rationale.md` sibling was never created.

On top of that the stub's surviving claims have drifted: several were true at the ship commit and are false at HEAD, and one central justification was **already false when it was written**. Details and measurements are in `## Pre-dispatch verification`.

Per the maintainer's dispatch instruction, Workers 2 and 3 are dispatched only where a slice needs a **code** change. Exactly one slice does (Slice 2): three `.py` sites assert an invariant about the example tree that no longer holds.

## Pre-flight outcome and deviations

- Step 1 (baseline): DIRTY. Two other sessions are mid-cycle on `spec-024` and `spec-025` (`worker-memory/worker-*-024.md` and `-025.md` seeded 2026-08-18 20:45 and 23:47). Baseline-dirty out-of-scope files are listed below.
- Step 2 (`scripts/review_inspect.py`): smoke run on `examples/fakeshop/apps/scalars/models.py --output-dir docs/shadow --stdout` exited 0.
- Step 3 (artifact reset): **DEVIATION — old `bld-*.md` / `build-*.md` were NOT deleted.** `bld-003-final.md`, `bld-slice-1a-024-planned_vs_head.md`, `bld-slice-1b-024-divergence_and_floor.md`, `bld-slice-3-024-rename_rot_sweep.md`, `build-024-django_trac_37064_hardening-0_0_7.md`, and `build-025-scalar_map_helper-0_0_7.md` are two concurrent sessions' live record. Deleting them is the one irreversible pre-flight mistake and `AGENTS.md` rule 34 forbids reverting concurrent work. This cycle therefore uses `-026`-suffixed artifact paths; all four were verified absent.
- Step 4 (`.gitignore`): `docs/shadow/` (line 174), `docs/builder/worker-memory/` (line 188), `docs/builder/temp-tests/` (line 192) all listed.
- Step 5 (scratch cleared): **DEVIATION — scratch was NOT cleared**, same reason as step 3. `worker-memory/worker-2-024.md` (7,973 bytes) and `worker-3-024.md` (9,614 bytes) are the `024` cycle's live notebooks. This cycle's workers use `docs/builder/worker-memory/worker-<N>-026.md`, which Worker 0 created empty.
- Step 6 (`check_spec_glossary`): `OK: 3 terms - all have glossary entries and at least one spec link.` (exit 0).
- Step 7 (rationale extraction): NOT yet done — it is Slice 1 of this cycle.

### Baseline-dirty out-of-scope files (never edit, never revert)

`CHANGELOG.md`, `KANBAN.html`, `KANBAN.md`, `django_strawberry_framework/_strawberry_patches.py`, `django_strawberry_framework/optimizer/hints.py`, `docs/GLOSSARY.md`, `docs/SPECS/appx/spec-021-apps-0_0_7-terms.csv`, `docs/SPECS/spec-021-apps-0_0_7.md`, `docs/SPECS/spec-022-export_schema-0_0_7.md`, `docs/feedback.md`, `examples/fakeshop/db.sqlite3`, `tests/optimizer/test_hints.py`, `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md`, every file under `docs/builder/DONE/`, and every artifact listed under pre-flight step 3.

**Concurrent-writable tracked binary / generated files:** `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`. This cycle plans NO edit to any of them, so any churn observed in them is another session's and must be left alone.

### Scope fence set by the maintainer

This cycle touches **spec files and `.py` files only**. No closeout-agentflow edits: no `docs/builder/BUILD.md`, `ARTIFACT.md`, or `worker-*.md` role-file changes; no KANBAN / GLOSSARY / CHANGELOG movement; no `-terms.csv` edit (its three anchors resolve and `check_spec_glossary` is green); no closeout retrospective.

## Pre-dispatch verification (Worker 0, against HEAD and the ship commits)

The card shipped across two commits, both dated 2026-05-27 and both attributed in their message to the pre-renumber id `DONE-048-0.0.7` (`card-renumber-2026-07-30` moved it to `026`):

- `2701eb88` — *Add apps.scalars with paired-model converter coverage substrate* (10 files, +753/-1).
- `cae2d5a3` — *Add Patron.lifetime_fines_cents BigInt to the library example* (4 files, +58/-1).

### Delivered in full — no code gap

Every promise in the stub's `## Other` list read against source. Findings are handed to Worker 1 as verified inputs, not hypotheses.

| Spec claim | Verified at | Result |
| --- | --- | --- |
| new `apps.scalars` example app | `examples/fakeshop/apps/scalars/` | present; `apps.py::ScalarsConfig`, `models.py`, `schema.py`, `migrations/0001_initial.py`, `tests/` all shipped in `2701eb88` |
| `ScalarSpecimen` — every scalar field non-null | `apps/scalars/models.py::ScalarSpecimen` | `flag` / `score` / `price` / `occurred_on` / `occurred_at` / `occurred_time` / `payload` / `external_id` / `signed_big` / `unsigned_big`, none nullable; `label` unique |
| intra-model self-FK `parent`, `related_name="children"` | `apps/scalars/models.py::ScalarSpecimen` #"related_name=\"children\"" | present, `null=True`, `on_delete=CASCADE` |
| `NullableScalarSpecimen` — every scalar field `null=True, blank=True` | `apps/scalars/models.py::NullableScalarSpecimen` | all eleven columns nullable, mirroring `ScalarSpecimen` column-for-column |
| cross-model FK `partner` -> `ScalarSpecimen`, `SET_NULL`, `related_name="nullable_partners"` | `apps/scalars/models.py::NullableScalarSpecimen` #"related_name=\"nullable_partners\"" | present exactly as specified |
| both exposed via `ScalarSpecimenType` / `NullableScalarSpecimenType` | `apps/scalars/schema.py` | both present; `Meta.fields` selects every converted column plus the relations |
| two root resolvers composed into the project `Query` | `apps/scalars/schema.py::Query.all_scalar_specimens` / `::Query.all_nullable_scalar_specimens`; `examples/fakeshop/config/schema.py` #"from apps.scalars.schema import Query as ScalarsQuery" | both present and composed |
| `ScalarsConfig` in `INSTALLED_APPS` | `examples/fakeshop/config/settings.py` #"apps.scalars.apps.ScalarsConfig" | present |
| real-domain `BigIntegerField` on `Patron` | `apps/library/models.py::Patron` #"lifetime_fines_cents" | present, `default=0`, selected in `apps/library/schema.py::PatronType` and pinned live at `test_query/test_library_api.py` #"lifetime_fines_cents=large_value" (`2**53 + 12345`) |
| the eight named live HTTP tests | `test_query/test_scalars_api.py` | all eight present at ship and at HEAD — plus a ninth the spec omits (below) |

The `0003_patron_lifetime_fines_cents` migration `cae2d5a3` added no longer exists as a file: `a7eb8f73` / `af8ec0e4` squashed the library and scalars migrations into one initial each. The column is present in `apps/library/migrations/0001_initial.py`, so this is a squash, not a loss.

### Drifted or defective spec claims Worker 1 must reconcile (verified, with the cause)

Each is a claim the stub makes that is false, incomplete, or unauditable. None is a code defect except D2/D3's mirrored `.py` comments, which Slice 2 owns.

- **D1 — the spec has no auditable contract at all.** It is 3,593 bytes with four headings (`## Card snapshot`, `## Planning note`, `## Other`, plus the title). `grep -c '^## Architectural decisions'` -> **0**; there is no `## Slice checklist`, `## Test plan`, `## Doc updates`, or `## Definition of done`. Every other spec from `015` forward carries all of them (measured across `docs/SPECS/`: `026` is the only file after `014` with zero `## Architectural decisions`). The stub's own preamble — "This file is intentionally lightweight… Before implementation work starts from this file, expand it into the full builder-format spec" — describes a precondition that the two ship commits made moot in May 2026.
- **D2 — "the only `SET_NULL` ondelete in the example tree" is false at HEAD.** True at `2701eb88`: `git grep 'SET_NULL' 2701eb88 -- 'examples/fakeshop/apps/*/models.py'` returned exactly one non-comment hit, `NullableScalarSpecimen.partner`. At HEAD `on_delete=models.SET_NULL` occurs **four** times across `examples/fakeshop/apps/*/models.py` — `apps/kanban/models.py` twice, `apps/scalars/models.py::ScalarSpecimen` #"related_name=\"tagged_specimens\"" once, and `partner` once. Cause: the kanban docs-as-data app (which did not exist at ship — `git ls-tree 2701eb88 examples/fakeshop/apps/` lists only `library`, `products`, `scalars`) and the O6 `Prefetch`-downgrade substrate `ScalarSpecimenTag`. **The same claim is mirrored in three `.py` sites** and is Slice 2's work.
- **D3 — "the only cross-model FK in the scalars app" is false at HEAD.** `ScalarSpecimen.tag` is a forward FK from `ScalarSpecimen` to `ScalarSpecimenTag`, a second cross-model FK inside the app, added with the O6 downgrade substrate. `partner` is still the only cross-model FK *out of* `NullableScalarSpecimen`.
- **D4 — the "upstream code paths no other example app reaches" justification was already false when written.** The stub names five such paths. Measured at the ship commit itself: `apps/library` carried **8** models, **7** sibling `DjangoType` classes in one module, and a **7**-`CreateModel` initial migration. So "Django's two-`CreateModel` initial migration path", "the registry / `finalize_django_types()` resolving sibling `DjangoType` classes in one app", "Strawberry type registration across sibling types in one schema build", and "the optimizer planning across two managed models in one query" were all reached by `apps/library` at the moment `apps/scalars` landed. Only `SET_NULL` ondelete behavior was genuinely unique at ship, and D2 retired that too. What IS distinctive about the pairing — and remains so — is the per-column **nullable / non-null converter-branch mirror**: no other example app carries an all-nullable twin of an all-required model, so no other app exercises both branches of one `SCALAR_MAP` row in one round-trip. Worker 1 rewrites the justification to the claim the code actually supports.
- **D5 — the test list is one short, and was at ship.** The stub enumerates eight live tests. `2701eb88:examples/fakeshop/test_query/test_scalars_api.py` shipped **nine** `def test_` functions; the omitted one is `test_scalar_specimen_introspects_json_scalar_in_both_shapes` (JSON scalar introspection in both shapes), which the ship commit message does list. The commit message itself says "(8 tests)" above nine bullets, so the miscount predates the spec.
- **D6 — the deliberate `ArrayField` / `HStoreField` exclusion is absent from the spec.** Both are PostgreSQL-only and the fakeshop runs on SQLite, so their converter rows stay covered in `tests/`. This is a real scope decision, stated in the ship commit message and in `apps/scalars/models.py`'s module docstring, and it belongs in the spec's non-goals rather than only in source prose.
- **D7 — the spec describes the ship moment, and the app has grown five ways since.** At HEAD `apps/scalars` also carries `ScalarSpecimenTag` (O6 downgrade), `Base36Field` + `OverrideSpecimen` (spec-029 consumer overrides), `MediaSpecimen` (spec-037 file/image), `filters.py`, `orders.py`, `forms.py`, seven `DjangoType` classes, two mutations, and **29** tests in `test_query/test_scalars_api.py` against the nine that shipped. `migrations/0001_initial.py` now carries **5** `CreateModel` operations plus an `AddField`, against **2** at ship. The spec must state the card's own contract without implying it is the app's current inventory.
- **D8 — `ScalarSpecimenType.Meta.fields` is no longer the card's selection.** `tag` was added by the O6 card. The card-026 selection (`id`, `label`, the ten scalars, `parent`, `children`, `nullable_partners`) is intact underneath it.
- **D9 — the `Status:` line is a placeholder.** It reads "shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact", which describes the file's provenance rather than the card's state.
- **D10 — `## Planning note` is the single word `shipped`.**

Worker 1 owns whether each of D1-D10 is a spec edit, a rationale entry, or both. The one rule Worker 0 fixes: **no explanation of any change may appear in the spec.** Corrected text states the contract as though it had always been right; the what / why / when goes in `docs/SPECS/appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md`.

### Code work verified as needed (Slice 2 only)

Three `.py` sites assert D2's retired invariant. All three are prose inside source files; none changes behavior.

- `examples/fakeshop/apps/scalars/models.py::NullableScalarSpecimen` #"place in the example tree that exercises" — docstring: "the only place in the example tree that exercises `SET_NULL` ondelete planning under the optimizer".
- `examples/fakeshop/apps/scalars/models.py` #"row instead of cascading" — inline comment on `partner`: "the only `SET_NULL` ondelete in the example tree".
- `examples/fakeshop/test_query/test_scalars_api.py::test_scalars_set_null_ondelete_detaches_partner_in_http_query` #"Pins the only" — docstring: "Pins the only `SET_NULL` ondelete in the example tree".

`AGENTS.md` #"Source refs in docs and code comments" and the standing no-process-provenance rule both apply: the replacement states the invariant that is true now, and names no card, commit, or history.

## Artifact list

- `docs/builder/bld-slice-1-026-rationale_extraction.md` — DELETED at closeout
- `docs/builder/bld-slice-2-026-stale_invariant_comments.md` — DELETED at closeout
- `docs/builder/bld-slice-3-026-spec_reconstruction.md` — DELETED at closeout
- `docs/builder/bld-integration-026.md` — DELETED at closeout
- `docs/builder/bld-final-026.md` — DELETED at closeout

All five are per-cycle scratchpads and were deleted after the work committed at `7722c4b3`; each is recoverable from that commit (`git show 7722c4b3:<path>`). Every load-bearing measurement they carried is folded into `## Final gate record` below, so no statement in this plan depends on reading them. Citations to them elsewhere in this file are records of what the cycle produced, not live pointers.

Two things were checked before deleting them, because a deleted file is recoverable but not greppable. No durable file cited any of the five: the only cross-file references were this plan's own artifact list and checklist, plus the concurrent `027` cycle's scratchpads naming them in its baseline-dirty list — those are that cycle's record of the tree it ran against, not pointers into this one, and were deliberately left alone. And the one body of slice-artifact reasoning worth keeping was already durable: Slice 2's four measured-and-rejected replacement framings live in `docs/SPECS/appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md` `## D2 and D3`, which states the rule that replaced them.

## Checklist

- [x] Slice 1: Rationale extraction — create `docs/SPECS/appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md` and MOVE the stub's deliberative layer into it -> `docs/builder/bld-slice-1-026-rationale_extraction.md`
- [x] Slice 2: Code correction — retire the three stale "only `SET_NULL` in the example tree" claims in `apps/scalars/models.py` and `test_query/test_scalars_api.py` -> `docs/builder/bld-slice-2-026-stale_invariant_comments.md`
- [x] Slice 3: Spec reconstruction — expand the stub into full builder format stating the current contract, resolving D1-D10, every change recorded in the rationale -> `docs/builder/bld-slice-3-026-spec_reconstruction.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-integration-026.md`
- [x] Final gate -> `docs/builder/bld-final-026.md`

## Final gate record

Folded out of `docs/builder/bld-final-026.md` and `docs/builder/bld-integration-026.md` before those artifacts were deleted. This is what they carried that exists nowhere else; the rest of them duplicated this plan, restated the spec or rationale, or measured facts the tree still answers on demand.

### Gate commands, as run

| # | Command | Result |
|---|---|---|
| 1 | `uv run ruff format --check .` | PASS — `424 files already formatted`, exit 0 |
| 2 | `uv run ruff check .` | PASS — `All checks passed!`, exit 0 |
| 3 | `git diff --check` | PASS — no output, exit 0, across this cycle's files and both concurrent sessions' |
| 4 | `uv run python scripts/check_trailing_commas.py --check` (repo-wide) | PASS — exit 0, no output |
| 5 | same, over every tracked candidate (`git ls-files '*.md' '*.py' '*.csv'`, 855 paths) | PASS — exit 0 |
| 6 | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` | PASS — `OK: 3 terms`, exit 0 |
| 7 | `uv run python scripts/check_citations.py` | PASS — 742 citations resolve, 77 of them in `KANBAN.md`, exit 0 |

The `.gitignore`-blind `check_trailing_commas` failure the dispatch anticipated did **not** occur, so nothing needed attributing to a concurrent session and nothing was fixed or reverted in any baseline-dirty file. Commands 1-3 cover the whole tree, so they covered the concurrent sessions' dirty `.py` files too, and were green there as well.

### Commands deliberately NOT run, and the authority

Decided answers, not omissions. `uv run pytest --no-cov`, `examples/fakeshop/manage.py check`, and `makemigrations --check --dry-run` were all skipped. `AGENTS.md` #"No pytest after edits" governs, `START.md` names `manage.py check` in the same breath, and `docs/builder/worker-1.md` says an instruction conflicting with `AGENTS.md` or `START.md` loses — so `docs/builder/BUILD.md`'s gate is the conflicting instruction and it loses. No `--cov`, `--cov-report`, or `--cov-config` flag was passed by any pass in the cycle.

Independently of precedence, a run would not have been evidence about this cycle: see the AST proof below, and note the tree was dirty with two other sessions' uncommitted work, so a green sweep would have recorded their state as this cycle's.

### Zero executable lines changed, proved mechanically

The claim the cycle's hot-path, floor, and no-test-run declarations all rest on. For each of the two edited `.py` files, HEAD was obtained read-only (`git show HEAD:<path>` into a scratch path outside the repo — no `git stash`, `checkout`, `restore`, or `worktree` anywhere in the cycle), both versions were parsed with `ast`, **every module, class, and function docstring was stripped**, and the two `ast.dump` strings compared:

```text
models.head.py vs examples/fakeshop/apps/scalars/models.py        : IDENTICAL
tests.head.py  vs examples/fakeshop/test_query/test_scalars_api.py: IDENTICAL
```

Comments are absent from the AST by construction, so an identical dump means no statement, expression, field declaration, argument, decorator, or import differs from HEAD. Three consequences, each load-bearing: model field declarations are executable AST, so migration state cannot have drifted and `makemigrations --check` cannot answer differently; no Django / Strawberry / channels surface is touched, which settles the floor question; and both files parse, which disproves the one thing a prose-only `.py` diff can actually break — a docstring that no longer terminates.

The diff itself: 18 added / 17 removed over 4 hunks (`models.py` 8/6, `test_scalars_api.py` 10/11).

### Floor verification

Scope `none`, confirmed against the landed diff rather than accepted from the plan. No floor venv was built and building one for a prose diff would have been wrong. The AST proof above is stronger than a seam-by-seam grep: not one executable construct differs from HEAD, so there is no seam to exercise, and no planned floor run went unrun. `docs/builder/BUILD.md` `## Floor verification` remains the single canonical statement of the floor versions; this plan deliberately restates no floor number.

### Deferred work: all three items HOMED, not carried

The gate's `### Deferred work catalog` listed three items, every locator re-derived unscoped. All three were **homed onto `TODO-ALPHA-052-0.1.0` on 2026-08-19** and committed at `7722c4b3`, so the catalog itself is discharged rather than inherited:

- The `DONE-026-0.0.7` card body's two false census clauses (`CardItem` 762 and 763) -> card 052 `CardItem` 1380, clauses (i) and (ii).
- `CHANGELOG.md`'s repetition of the retired exclusivity shape -> card 052 `CardItem` 1381, clause (iii).
- `CHANGELOG.md`'s two undercounts (three retired tests where six, eight live tests where nine) -> card 052 `CardItem` 1381, clauses (i) and (ii).

The board half was homed rather than repaired in place, matching how card 052 already carries the `DONE-017-0.0.6` and `DONE-018-0.0.6` stale-card-body findings. `KANBAN.md` and `KANBAN.html` are rendered from `examples/fakeshop/db.sqlite3`, so whoever closes them edits the DB and regenerates; `CHANGELOG.md` is closed to a build cycle by `AGENTS.md` rule 21 and card 052 owns the promotion.

Homing also falsified card 052's own stub-preamble bullet (`CardItem` 1347), which was corrected in the same edit: the population it stated as three, and instructed later sweeps to measure as three, was already **one** before this cycle and is now **zero**.

### Decided rather than deferred

The highest-value thing the deleted artifacts carried, and the reason this section exists: eight questions the cycle examined and closed. None has a future owner, and each is one a later pass would otherwise re-open as new.

1. **`examples/fakeshop/apps/scalars/models.py` #"covered transitively by every other example app" is TRUE at HEAD.** Escalated by Worker 3 as a fifth census the Slice 2 plan's sweep missed, then closed with no fix and re-verified independently twice. Worker 3 had measured model *ownership* (`apps/accounts` is an installed example app with no `models.py`) against a sentence whose subject is converter-row *coverage* — and `transitively` is the sentence's own word for exactly that gap. **Not to be re-opened.**
2. **Slice 3's `### Spec slice checklist audit` contradicts its own body twice.** It records the census sweep as 21 hits where its body says 35, and the history-narration grep as 0 where its body says 1. Measured independently at both the integration pass and the gate: **35** and **1** — the body is right in both, the table wrong in both. Left as written, because an accepted artifact is the record of work already done; the corrected figures are here.
3. **The rationale's append-only rule took exactly one recorded exception.** The integration pass replaced `D1`'s own false `docs/SPECS/` census in place rather than appending a correction — narrowest possible scope, flagged rather than discovered. Upheld: the rule protects an entry's argument, no argument changed, and shipping a false census inside the file whose subject is false censuses is the one outcome the rule cannot license.
4. **The rationale quotes Decision headings with an ASCII hyphen where the spec uses an em dash.** Cosmetic; every anchor resolves. Not edited, for the append-only reason.
5. **The spec-vs-`.py` prose overlap stays as it is (19 shared 7-grams), and Slice 3's stated prevention is recorded as not having held.** Its DRY analysis said the spec must not carry a second copy of the causal sentence; the landed diff does. Decided no edit: `docs/builder/worker-1.md`'s carve-out keeps the "why" that changes how a thing is built in the spec, while the `.py` comment states the same invariant at the code. The load-bearing property was measured — **no shared run carries a number**, so the copies cannot drift into disagreeing the way `SET_NULL`-is-4-not-1 did.
6. **The one substantive spec-vs-rationale overlap has a named owner: the spec.** `## Non-goals` item 1's `tests/` coverage boundary is normative, and the rationale's `D6` copy sits inside the argument for it.
7. **Decision 5's "package coverage stays at 100%" is recorded, not graded.** Every `--cov*` flag is forbidden to every worker pass, so no pass can measure it; it restates the standing `fail_under = 100` CI gate rather than asserting a new measurement. The maintainer's gate owns it.
8. **Floor verification: nothing to run.** See `### Floor verification` above.

### Methodology notes worth keeping

- **A home-grown slugger indicts the file before it indicts itself, in a new character each time.** The gate's own link checker reported six broken fragments and nine unresolved anchors; all were its `re.sub(r"\s+", "-")` collapsing whitespace runs where GitHub replaces each whitespace character individually, so a heading with an em dash (which GitHub strips, leaving two spaces) slugged to one hyphen. One character in the instrument, fifteen false findings. A known trap in its underscore form; this was the same class in a different character.
- **A corpus total that includes the cycle's own artifacts is not stable across passes.** Deferred item 1's file count read 6 at Slice 3 and 7 at the gate, because every pass that writes about a retired claim adds a site. Both readings were correct at their moment and neither is a defect. State live sites and per-file occurrence counts; never a corpus total.
- **Count occurrences, not matching lines.** `grep -o … | wc -l` throughout; `grep -c` counts lines and is a different population.
- The cycle had **four inherited claims overturned by the pass that checked them**, including two in this plan's own `## Pre-dispatch verification`. Re-derive; never carry a number forward on trust.

### Closeout

Not performed, by maintainer instruction: no edit to `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, or any `docs/builder/worker-*.md` role file; no retrospective; no `docs/GLOSSARY.md`, `docs/TREE.md`, or `CHANGELOG.md` movement; no `-terms.csv` edit; no card wrap beyond the deferred-work homing recorded above.
