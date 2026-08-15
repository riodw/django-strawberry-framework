# Package build plan: debug_extension / 0.0.14 (044)

Spec source: `docs/SPECS/spec-044-debug_extension-0_0_14.md` (**archived by item R3 of this cycle**; it was at `docs/spec-044-debug_extension-0_0_14.md` when this plan was written, and every earlier reference to that path in this file is correct as of the pass that wrote it)
Target release: `0.0.14` (**already shipped** — `pyproject.toml` `[project].version = "0.0.14"`, `django_strawberry_framework/__init__.py::__version__ = "0.0.14"`, `CHANGELOG.md` `## [0.0.14] - 2026-07-20`, card `DONE-044-0.0.14`)
Date created: 2026-07-31
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging. Duplicated logic, parallel data flows, near-copies, and repeated literals are build-time defects — including in the doc/spec surfaces this cycle touches (a fact told twice in two files goes stale in one of them).
Ownership partition: none; sequential residual items.
Hot-path declaration: none. No residual item changes package source, so no item runs per request, per resolver, per row, per connection, or per outbound message.
Floor-verification scope: none. No residual item touches a Django / Strawberry / channels integration seam — the cycle edits the spec, its rationale sibling, cross-references, and DB-rendered docs only.
Pre-flight: passed on 2026-07-31 with **three** recorded deviations (below); baseline: one out-of-scope deletion at pre-flight, which grew to **ten** concurrent-session entries by item R2 (see the baseline-dirty list, which carries the final-gate exception this growth requires); cleanup: **deliberately not performed** — see Deviation 1.

## This is a residual-completion cycle, not a fresh build

The spec's three slices were built, reviewed, and **released** before this cycle opened. What remains is the deliverable set the shipped cycle never produced. The maintainer scoped it in three sequential items: the missing `-rationale.md`, the unfinished documentation, then the spec archive.

### Already-shipped spec slices — verified delivered at HEAD (no build cycle dispatched)

Not checkboxes: Worker 0 may only tick a box after a Worker 1 final verification, and these slices predate this plan. They are evidence, pre-verified by Worker 0 at pre-flight so no worker re-derives them, and item **R2** carries their formal `## Definition of done` audit.

| Spec slice | Delivered at HEAD — evidence |
|---|---|
| Slice 1 — `extensions/` subpackage + `extensions/debug.py` + split live/mechanics tests | `django_strawberry_framework/extensions/__init__.py`, `django_strawberry_framework/extensions/debug.py`, `tests/extensions/__init__.py`, `tests/extensions/test_debug.py`, `examples/fakeshop/test_query/test_debug_extension_api.py` all present |
| Slice 2 — implemented-contract docs (card WIP, no version bump) | `docs/GLOSSARY.md` carries the `DjangoDebugExtension` + Response-extensions debug middleware entries; `docs/TREE.md` carries real `extensions/` and `tests/extensions/` rows; `examples/fakeshop/config/schema.py` docstring names the shipped `DjangoDebugExtension` and fakeshop's opt-out; `GOAL.md` success criterion 7 carries the engine-configuration scoping clarification |
| Slice 3 — the joint `0.0.14` cut + final card wrap | version quintet reads `0.0.14` (`pyproject.toml`, `__init__.py`, `tests/base/test_init.py::test_version`); `docs/GLOSSARY.md` line 179 reads `shipped (0.0.14)`; `CHANGELOG.md` `## [0.0.14] - 2026-07-20`; card `DONE-044-0.0.14` with a `SpecDoc` and 42 `CardGlossaryTerm` rows |

### Residual scope (this cycle's actual work)

- **R1 — spec rationale extraction.** `docs/spec-044-debug_extension-0_0_14-rationale.md` does not exist. `docs/builder/BUILD.md` `## Spec rationale extraction` makes the move the first substantive action of a build and pre-flight step 7 gates dispatch on it; the shipped cycle skipped it. Worker 1 is the only role that may perform it.
- **R2 — finish the documentation.** The spec's `Status:` line (line 74) is already accurate, but its **opener is stale**: line 3 still reads ``Planned for `0.0.14` (card [`WIP-ALPHA-044-0.0.14`][kanban])`` for a card that is Done and a version that shipped. The archived `0.0.14` siblings show the shipped form (`spec-042` / `spec-043` line 3: ``Built for `0.0.14` (card [`DONE-0NN-0.0.14`][kanban])``). Item R2 realigns the opener and audits every `## Doc updates` obligation and `## Definition of done` row against HEAD, fixing any drift found.
- **R3 — archive the spec.** Move `docs/spec-044-debug_extension-0_0_14.md`, its `-terms.csv`, and the R1 `-rationale.md` to `docs/SPECS/`, with the full three-direction cross-reference sweep, the `SpecDoc.path` repoint in the kanban DB, and the `KANBAN.md` / `KANBAN.html` regenerate.

## Pre-flight outcome (7 steps, `docs/builder/worker-0.md` `## Pre-flight procedure`)

1. **Working-tree baseline is explicit.** `git status --short` → one entry, `D to-many-search-optimizer-reproduction.md`. Concurrent-session work per `AGENTS.md` rule 34. See the baseline-dirty list below.
2. **`scripts/review_inspect.py` runs.** `uv run python scripts/review_inspect.py django_strawberry_framework/extensions/debug.py --output-dir docs/shadow --stdout` emitted its overview (11 imports, 19 symbols). Working.
3. **Build artifacts are reset — DEVIATION 1, see below.** Verified instead that every path this plan creates is absent: no `docs/builder/build-044*`, no `docs/builder/bld-044*`, no `docs/spec-044-*-rationale.md`.
4. **`.gitignore` lists the untracked scratch paths.** `docs/shadow/` (line 174), `docs/builder/worker-memory/` (188), `docs/builder/temp-tests/` (192). Present.
5. **Scratch directories are cleared — DEVIATION 1, see below.** Deliberately not cleared.
6. **Spec-doc consistency check.** `uv run python scripts/check_spec_glossary.py --spec docs/spec-044-debug_extension-0_0_14.md` → `OK: 42 terms - all have glossary entries and at least one spec link.` Exit 0.
7. **Spec rationale is extracted.** **Not done — it is item R1 of this cycle.** Ordinarily this gates dispatch. Here it cannot, because R1 *is* the dispatch: the slices whose spawns the gate protects from a 205KB spec were built and released before this plan existed, so there is no builder left to protect. R1 is dispatched first regardless, so every later spawn in this cycle reads the smaller spec exactly as the rule intends.

### Deviation 1 — the prior cycle's artifacts, memory, shadow, and temp-tests are PRESERVED

Pre-flight steps 3 and 5 delete old `build-*.md` / `bld-*.md` and clear `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/`. Not performed, deliberately:

- The 25 artifacts under `docs/builder/` belong to the **spec-046 transport-security cycle**, are **committed** (`git log -1 -- docs/builder/bld-final.md` → `ff65666d`), and `docs/builder/bld-final.md` names a maintainer-owned `BUILD.md` closeout item — so that cycle's **closeout retrospective has not run**.
- `docs/builder/worker-memory/` (430 lines across four files) and `docs/builder/temp-tests/` (10 cycle directories) are **gitignored**, so deleting them is unrecoverable, and `worker-0.md` `## Closeout job` steps 2 and 5 read exactly those files. Clearing them would destroy the input to a retrospective the maintainer has not yet run.
- The reasoning is `BUILD.md`'s own, under `### Cohorting, naming, and closure` ("Pre-flight for a round"): when the input to a cycle is already-built work, the prior artifacts are the record of that work and must survive. Every residual item here operates on already-built, already-released work.
- **Collision is avoided by naming, not by deletion.** Every artifact this plan creates is `bld-044-`-prefixed, and none of those paths exists.
- Consequence for dispatch: each worker's memory file opens with spec-046 entries. Dispatch prompts say so and require this cycle's entries to be appended under a `## spec-044 residual cycle` heading, so the two cycles stay distinguishable at the next closeout.

### Deviation 2 — artifact filenames carry the `044` card number

`## Build artifact naming` gives `bld-slice-<N>-<slug>.md`; the surviving spec-046 set already occupies `bld-slice-1..5-*`, `bld-integration.md`, and `bld-final.md`. This cycle uses `bld-044-<item>-<slug>.md` and `bld-044-final.md` — still `docs/builder/bld-`-prefixed, and unambiguous about which cycle each artifact records. The items are also not spec slices (the spec's slices shipped), so an `N` mirroring a slice number would misdescribe them.

### Deviation 3 — the `built` state is skipped where the deliverable is Worker-1-exclusive

`docs/builder/ARTIFACT.md` `## Status field ownership` gives `built` to Worker 2, and `worker-0.md` `## Per-slice dispatch` maps `planned` → Worker 2. Item **R1** has no Worker 2 role that could set it: `BUILD.md` `## Spec rationale extraction` makes Worker 1 the only role that performs the move, and states outright that **Worker 2 never reads the rationale file** — "that is the point of the move." Dispatching a builder at it would hand the file to the one worker the mechanism exists to keep away from it.

So for R1 only, the chain is **Worker 1 (plan + perform, `planned`) → Worker 3 (audit, `review-accepted` | `revision-needed`) → Worker 1 (final verification, `final-accepted`)**, and Worker 0 reads `planned` on the R1 artifact as "dispatch Worker 3", not Worker 2. This is declared here, before dispatch, so no pass improvises the mapping.

The Worker 3 audit is **not** skippable alongside the Worker 2 build. `BUILD.md` names Worker 3 as a reader of the rationale file during review, and names the move as "the one place this move can itself cause a defect" — moving implementation-relevant rationale out of the spec is a defect a reader with no memory of the move is the only party positioned to catch. R2 and R3 both have real Worker 2 work and run the full unmodified chain.

## Baseline-dirty out-of-scope files

Workers neither edit nor revert these, and never `git checkout` them (`AGENTS.md` rule 34):

- `to-many-search-optimizer-reproduction.md` — deleted in the working tree by a concurrent session. Not this cycle's file and not referenced by spec-044.
- **Eight package source / test files went dirty mid-cycle, during item R2's final verification** (mtimes 11:57-12:07 on 2026-07-31, still advancing while that pass ran): `django_strawberry_framework/consumers.py`, `views.py`, `utils/sessions.py`, `_request_body.py`, `auth/mutations.py`, `tests/auth/test_mutations.py`, `tests/test_routers.py`, `tests/test_views.py`. This is the **spec-046 transport / auth surface** — a concurrent session's live work, not this cycle's. Attribution is positive rather than inferred: **no residual item issues a `.py` write at all** (every item's writable list is spec / rationale / artifact / memory only), and `tests/test_routers.py`'s mtime post-dates the artifact section that had already recorded the dirty list as unchanged. Never edit, never revert (`AGENTS.md` rule 34).

  **Baseline exception for the final test-run gate, recorded here because `BUILD.md` `## Final test-run gate` requires it in the plan's preamble to be honoured:** `uv run pytest --no-cov`, `uv run ruff format --check .`, `uv run ruff check .`, and `git diff --check` all read the whole tree, so they will see this churn. A failure attributable to any of the eight files above — or to a `.py` file this cycle never wrote — does **not** block `final-accepted` and does **not** route back through a residual item's loop. It is a concurrent session's in-progress work, reported to the maintainer, and mid-edit source is expected to be transiently red. The gate still reports each command's real result; the exception governs what the result *blocks*, never whether it is recorded honestly.

- `docs/feedback.md` — **appeared dirty mid-cycle, during item R1**, and belongs to the preserved spec-046 cycle rather than to spec-044 (`AGENTS.md` rule 34: concurrent work, ignore as out-of-scope; never auto-revert). Added here at the moment of discovery so no later pass mistakes it for this cycle's output. Worker 1 reported it without touching it, which is the correct handling.

## Concurrent-writable tracked binary / generated files

Churn in these is not proof a worker caused it (`BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`). All four are **clean at baseline**, so no concurrent card-wrap is in flight; item R3 legitimately diverges the first three:

- `examples/fakeshop/db.sqlite3` — the maintainer runs parallel sessions against this file. R3 writes exactly one row (`SpecDoc.path` for card 44). Compare `iterdump()` semantics, never file bytes.
- `KANBAN.md`, `KANBAN.html` — regenerated from that DB in R3.
- `docs/GLOSSARY.md` — DB-rendered; **no residual item is expected to change it.** A diff here means drift to investigate, not build output.

## Build-wide context flags

- **The joint `0.0.14` cut is applied and released.** No residual item touches the version quintet; a diff to `pyproject.toml`, `__init__.py`, `tests/base/test_init.py`, the GLOSSARY package-version line, or `uv.lock` is out of scope for every item.
- **No source or test file changes in this cycle.** Package source, `tests/`, and `examples/` code are read-only throughout. R2 may edit a docstring only if its audit finds a factually-false one, and that routes through Worker 2.
- **`CHANGELOG.md` is closed.** The spec's Slice-3 grant was spent on the shipped `## [0.0.14]` section. `AGENTS.md` rule 21 governs again: no residual item edits it. A stale spec-044 path found there is reported to the maintainer, never edited (`docs/SPECS/NEXT.md` Step 8 action 7).
- **Generated docs are DB-backed.** `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md` render from `examples/fakeshop/db.sqlite3`. Edit the DB through the Django ORM (so `post_save` writes the `UUIDModel` side-row), then regenerate. Never hand-edit the rendered file.
- **The spec archive is expected by a downstream spec.** `docs/spec-050-debug_extraction-0_0_19.md` line 127 already reads ``docs/spec-044-debug_extension-0_0_14.md`` "(by then archived) is history — untouched", so R3 satisfies a stated downstream assumption rather than inventing a move. `BUILD.md` `### Spec stays at its working location` also requires the move be plan-declared as a Worker-1-owned final-verification step, which the R3 entry below does.
- **Only the maintainer commits.** No worker commits, and none creates or switches a branch.

## Worker-0-verified facts, passed into dispatch so no worker re-derives them

`worker-0.md` `## Closing out a kanban card` requires the live DB references be verified before a card/glossary edit is planned, because plan and spec text can carry stale ones. Read-only queries, run 2026-07-31:

- `Card.objects.get(number=44)` → `card_id` `DONE-044-0.0.14`, `status.key` `done`, `target_version.number` `0.0.14`, title `Response-extensions debug middleware`. The card is **already Done**; no status flip is in scope, and the 2026-07-30 card renumber left 044 untouched (it rotated 045-068 only).
- `SpecDoc` for card 44 → name `spec-044-debug_extension-0_0_14`, url `https://github.com/riodw/django-strawberry-framework/blob/main/docs/spec-044-debug_extension-0_0_14.md`. R3 repoints it to `docs/SPECS/...`; the `name` does not change.
  - **Corrected during R3's build pass, and this plan had it wrong.** The writable column is **`SpecDoc.path`** (repo-relative, e.g. `docs/spec-044-debug_extension-0_0_14.md`); **`SpecDoc.url` is a read-only `@property`** deriving `f"{SPEC_URL_PREFIX}/{self.path}"` (`examples/fakeshop/apps/kanban/models.py::SpecDoc`, migration `0009_specdoc_path.py`), so assigning to it raises `AttributeError: property 'url' of 'SpecDoc' object has no setter`. Worker 2 hit that, wrote `sd.path`, and classified it small drift rather than structural: same row, same contract, same ORM mechanism, byte-identical resulting `url`. **The same error is in `docs/SPECS/NEXT.md` Step 8's copy-paste worked example at four sites** (`:268-274`, `:280`, `:337`, `:338`) plus `worker-0.md` `## Closing out a kanban card` step 2 — both are standing docs outside every residual item's writable set, so they reach the maintainer through the deferred-work catalog. The next spec author runs that broken example verbatim.
- `card.glossary_links.count()` → 42, and `check_spec_glossary.py` reports 42 terms. The DONE-card invariants (`SpecDoc` + at least one `CardGlossaryTerm`) already hold, so no bootstrap step is needed.
- Spec byte count before R1: **205,905 bytes** (`docs/spec-044-debug_extension-0_0_14.md`). Worker 1 reports the after-count for the R1 artifact.

### Every reference TO spec-044 that R3 must rewrite (verified by grep, 2026-07-31)

| Location | Current text | Class |
|---|---|---|
| `KANBAN.md:100`, `KANBAN.md:1516` (+ `KANBAN.html`) | `docs/spec-044-debug_extension-0_0_14.md` | **Generated** — repoint `SpecDoc.path` in the DB, then regenerate. Never hand-edit. |
| `docs/spec-050-debug_extraction-0_0_19.md:554` | `[spec-044]: spec-044-debug_extension-0_0_14.md` | Reference definition from a `docs/` sibling → becomes `SPECS/spec-044-...` |
| `docs/spec-050-debug_extraction-0_0_19.md:127`, `:472` | prose ``docs/spec-044-debug_extension-0_0_14.md`` | Inline code-span prose path, not a link → update the path |
| `docs/dry/export_dry_review.py:30` | `--context docs/spec-044-debug_extension-0_0_14.md` | Module-docstring example invocation → update the path |
| `docs/spec-044-...md:1314` (inside the moved file) | ``This spec lives at `docs/spec-044-debug_extension-0_0_14.md` `` | Self-reference **inside** the spec → becomes `docs/SPECS/spec-044-...` |
| `docs/spec-044-...md:724` (inside the moved file) | ``docs/spec-044-debug_extension-0_0_14-terms.csv`` | Companion CSV moves too, so this stays a sibling — **verify, do not rewrite** |

No hit in `CHANGELOG.md`, `README.md`, `GOAL.md`, `TODAY.md`, `AGENTS.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, or `docs/README.md`. The sweep is re-run by the owning item, not trusted from this table.

**The dangerous direction is the one this table cannot show:** every relative link *inside* the moved files is wrong by one `../` level the instant the move lands, and the visible diff is only a rename (`docs/SPECS/NEXT.md` Step 8, direction 2). The spec's bottom block carries ~70 definitions across `<!-- Root -->`, `<!-- docs/ -->`, `<!-- docs/SPECS/ -->`, `<!-- django_strawberry_framework/ -->`, `<!-- tests/ -->`, `<!-- examples/ -->`, `<!-- scripts/ -->`, `<!-- .venv/ -->`, and `<!-- External -->`. Three groups invert rather than deepen: `docs/` siblings gain a `../` (`GLOSSARY.md` → `../GLOSSARY.md`), `[next]: SPECS/NEXT.md` **shortens** to `NEXT.md`, and the four `[spec-038]` / `[spec-041]` / `[spec-042]` / `[spec-043]` definitions **shorten** from `SPECS/spec-...` to `spec-...` as they become siblings. The R1 rationale file inherits the same obligation for whatever definitions it carries.

### R3 carries one deliberate transient state — Worker 3 is told, so it is not a finding

`BUILD.md` `### Spec stays at its working location` puts the mechanical move in **Worker 1's final verification**, after the review. Worker 2's inbound rewrites therefore land pointing at `docs/SPECS/spec-044-debug_extension-0_0_14.md` while the file is still at `docs/spec-044-debug_extension-0_0_14.md`, so at review time those rewritten links **do not resolve yet, by design**. Worker 3 reviews them against the post-move path and reports a wrong *target*, never the not-yet-moved file. Worker 1's final verification performs the move and is the pass that confirms every link resolves.

## Artifact list

- `docs/builder/bld-044-r1-rationale_move.md`
- `docs/builder/bld-044-r2-doc_completion.md`
- `docs/builder/bld-044-r3-spec_archive.md`
- `docs/builder/bld-044-final.md`

No `bld-integration.md`-equivalent: a cross-slice integration pass exists to find duplication across slices that landed source, and this cycle lands none. Its live obligations are folded into the R3 review and the final gate — the staged-anchor sweep (`BUILD.md` `## Cross-slice integration pass` step 6) runs in R2, and the cross-artifact read runs in the final gate.

## Checklist

- [x] R1: Spec rationale extraction into `docs/spec-044-debug_extension-0_0_14-rationale.md` (Worker 1 performs the move; Worker 3 audits it; Worker 1 final-verifies) -> `docs/builder/bld-044-r1-rationale_move.md`
- [x] R2: Finish the documentation — spec opener realigned to shipped tense, plus a full audit of the spec's `## Doc updates` and `## Definition of done` against HEAD with any drift fixed, and the `TODO(spec-044` / `TODO-ALPHA-044` staged-anchor sweep -> `docs/builder/bld-044-r2-doc_completion.md`
- [x] R3: Archive the spec to `docs/SPECS/` — three files moved, all three cross-reference directions swept, `SpecDoc.path` repointed in the DB, `KANBAN.md` / `KANBAN.html` regenerated. **Worker 1 owns the mechanical move at final verification** (`BUILD.md` `### Spec stays at its working location`); Worker 2 owns the inbound rewrites and the DB/regenerate work and never moves or edits the spec -> `docs/builder/bld-044-r3-spec_archive.md`
- [x] Final test-run gate -> `docs/builder/bld-044-final.md`

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
