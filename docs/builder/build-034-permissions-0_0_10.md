# Package build plan: permissions / 0.0.10 (034) — residual-reconciliation cycle

Spec source: `docs/SPECS/spec-034-permissions-0_0_10.md` (archived; shipped in `0.0.10` as card `DONE-034-0.0.10`)
Rationale companion: `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` (created by this cycle's Slice 0)
Target release: `0.0.10` (already shipped — this cycle lands **no** version-affecting change)
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Ownership partition: declared per round below (R1's three cohorts are read-only and concurrent; every other pass is sequential and single-cohort).
Hot-path declaration: R1 and R2 land no source and declare none. **R3 declares none** — amended after R1 closed: R3's confirmed scope is a live-test extension in `examples/fakeshop/test_query/test_products_api.py` and lands no production code, so nothing runs per request, per resolver, per row, or per connection that did not run before. Had R3 landed a change inside `permissions.py::apply_cascade_permissions` the declaration would be hot-path (that walk runs inside every cascading `get_queryset`); it does not.
Floor-verification scope: R1/R2 declare `none` (no source, no framework seam). **R3 owns one floor run** — amended after R1 closed: its rows drive live `/graphql/` requests through the Django request/response and schema-construction seam, so the focused scope `examples/fakeshop/test_query/test_products_api.py -k cascade` re-runs in an isolated floor venv at the versions `docs/builder/BUILD.md` `## Floor verification` states canonically, owned by **R3's builder pass**. The final gate is the backstop confirming it happened, not a second owner.

## Cycle shape (why this is not an ordinary spec build)

`spec-034` shipped. Its five slices are `final-accepted` and its card is Done. This cycle is a **residual-reconciliation cycle** in the shape the `033` cycle established, driven by the maintainer's instruction, with three obligations:

1. **The missing rationale companion.** `spec-034` was archived with a `-terms.csv` and no `-rationale.md`. Slice 0 closed that gap.
2. **Conformance: prove nothing planned was skipped in the code.** Every contract the spec states is checked against shipped source and tests at `HEAD`. A contract the spec states and the code does not implement is a code defect and routes to R3. A contract the code implements *differently* because a later card deliberately changed it is a **spec** defect and routes to R2.
3. **Reconciliation: the spec states the current contract.** Where later work corrected or superseded what `034` shipped, the spec is rewritten to state the corrected contract **directly, without chronology**; what changed, when, and why is appended to the rationale companion as a `**Post-ship:**` bullet under the owning Decision.

**Known-live divergence class this cycle exists to resolve.** `django_strawberry_framework/permissions.py`'s module docstring at `HEAD` describes a cascade contract that contradicts the spec on at least five points the spec still states as shipped: cycles now raise a path-rich `ConfigurationError` rather than returning a partially-narrowed queryset; identity-hook targets now compose rather than being skipped; MTI `<parent>_ptr` edges now cascade rather than being excluded; `GenericForeignKey` now fails a full walk closed rather than being silently skipped; the `__isnull` disjunct is now conditional on field nullability. These are deliberate later flips, not regressions — R1 establishes the full population and R2 reconciles the spec to it.

## Maintainer-set scope for this cycle

- **This cycle touches spec files and `.py` source/test files only.** No `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `docs/TREE.md` / `TODAY.md` / `README.md` / `CHANGELOG.md` / `BACKLOG.md` edits, no kanban-DB writes, no doc regeneration, no card movement.
- **No closeout agentflow edits.** `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, and the four `docs/builder/worker-*.md` role files are not edited by this cycle.
- **Every file this cycle creates carries `034` in its name.**
- The spec is already archived at `docs/SPECS/` with its companions at `docs/SPECS/appx/`; the archival obligation is satisfied by verification, not by a move.

## Pre-flight

Pre-flight: run on 2026-08-28 with three recorded deviations, all deliberate; baseline: **dirty with a concurrent session's work** (see below); cleanup: worker-memory seeded empty (4 files), `docs/builder/temp-tests/` already empty, `docs/shadow/` deliberately left populated.

| Step | Outcome |
|---|---|
| 1. Working-tree baseline explicit | **Deviation.** Not clean. The dirty set is a concurrent session's kanban-tooling work; per `AGENTS.md` rule 34 it is recorded as baseline-dirty out-of-scope rather than escalated, and no pass in this cycle edits or reverts any of it. |
| 2. `scripts/review_inspect.py` runs | Passed — smoke run on `django_strawberry_framework/permissions.py --output-dir docs/shadow --stdout` produced a full overview (18 symbols, 6 control-flow hotspots). |
| 3. Build artifacts reset | **Deviation.** No prior `build-034-*` / `bld-034-*` artifact existed, and every path this plan creates was verified absent. `docs/builder/bld-003-final.md` is a *different, committed* cycle's record and was **not** deleted: it is outside this cycle's maintainer-set scope and may belong to a concurrent session. |
| 4. `.gitignore` lists the scratch paths | Passed — `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/` all listed. |
| 5. Scratch directories cleared | **Deviation.** `worker-memory/` created and seeded with four empty files; `temp-tests/` already empty. `docs/shadow/` was left populated: its files are gitignored, regenerable, and overwritten by name, and a concurrent session may be mid-review against them. Any shadow file this cycle relies on is regenerated by the pass that uses it. |
| 6. Spec-doc consistency check | Passed — `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-034-permissions-0_0_10.md` → `OK: 42 terms`, exit 0. Re-run after Slice 0's move: `OK: 42 terms`, exit 0. |
| 7. Spec rationale extracted | **Done and verified** — Slice 0 below. |

### Baseline-dirty out-of-scope files (never edit, never revert)

`BACKLOG.md`, `KANBAN.html`, `KANBAN.md`, `README.md`, `examples/fakeshop/db.sqlite3`, `scripts/_kanban_lib.py`, `scripts/build_kanban_html.py`, `scripts/build_kanban_md.py`, `tests/test_build_kanban_html.py`, and the untracked `0_0_14.md`, `docs/DIVERGENCE.md`. Also out of scope: `docs/builder/bld-003-final.md`.

Two of these are `.py` files (`scripts/build_kanban_*.py`, `tests/test_build_kanban_html.py`) and this cycle's scope is "spec files and `.py` files" — the scope grants no licence over *these* `.py` files. They are another session's kanban-tooling work and stay untouched.

### Tracked binary / generated files that a concurrent writer can rewrite

`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`. All four are already dirty from the concurrent session and **no pass in this cycle writes any of them**, so any churn observed against them during this cycle is by definition not this cycle's output. Never `git checkout` one as "tool drift".

## Slice 0 — spec rationale extraction (pre-flight step 7, closed)

Performed by Worker 1 as a procedural-closure pass before this plan existed. Recorded here because the plan is where the cycle's artifact list lives.

- Created `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` (69,448 bytes, 396 lines).
- Spec `112,241` bytes / 607 lines after, from `145,643` bytes / 674 lines before: **−33,402 bytes**.
- Four routes carried 37,843 bytes of verbatim text out (revision block, 13 `Justification:` + 13 `Alternatives considered` blocks, the `## Risks and open questions` body, four chronology tags), against which the header/pointer framing the move added back nets the −33,402.
- Verified: `check_spec_glossary.py` `OK: 42 terms` exit 0; `check_citations.py` `OK: 857 citations resolve`; link-def scaffold check exit 0 on both files; 0 unresolved anchors and 93/93 + 47/47 ref/def parity.
- Artifact: `docs/builder/bld-034-slice-0-rationale_extraction.md` — `Status: final-accepted`.

## Artifact list

- `docs/builder/bld-034-slice-0-rationale_extraction.md` (created, `final-accepted`)
- `docs/builder/bld-034-review-1a-cascade_module.md`
- `docs/builder/bld-034-review-1b-composition_pins.md`
- `docs/builder/bld-034-review-1c-fakeshop_and_surface.md`
- `docs/builder/bld-034-review-2-spec_reconciliation.md`
- `docs/builder/bld-034-review-3-code_repair.md` — **the condition fired; this artifact is required.** R1a and R1b each returned an empty SKIPPED enumeration, but R1c returned one: finding **B4a**. See `## R1 outcome` below.
- `docs/builder/bld-034-review-4-rationale_correction.md` — **added after the integration pass**, which found the rationale companion asserting a per-model edge memo is *deferred* when `permissions.py::_edge_plan` ships it `@lru_cache`d (finding I1). **I1 is discharged, not deferred**; the integration artifact predates R4 and still files it as open.
- `docs/builder/bld-034-integration.md`
- `docs/builder/bld-034-final.md`

## Ownership partition

**R1 (three cohorts, concurrent).** Every R1 cohort is **read-only over source and tests** — it writes exactly one file, its own artifact — so the partition is trivially disjoint and concurrency is licensed. Each cohort's audit *territory* is declared so the findings partition the way the files would:

| Cohort | Writes | Audit territory (read-only) |
|---|---|---|
| R1a | `docs/builder/bld-034-review-1a-cascade_module.md` | `django_strawberry_framework/permissions.py`, `django_strawberry_framework/__init__.py`, `django_strawberry_framework/utils/querysets.py` (only as the cascade's per-edge hook boundary), `tests/test_permissions.py`, `tests/base/test_init.py`. Spec territory: Slice 1, Decisions 3, 4, 5, 6, 7, 8, 9, 10, the `## User-facing API` + `## Error shapes` sections, and every `## Edge cases and constraints` bullet describing the walk itself. |
| R1b | `docs/builder/bld-034-review-1b-composition_pins.md` | `django_strawberry_framework/optimizer/walker.py`, `optimizer/extension.py`, `connection.py`, `relay.py`, `list_field.py`, `filters/sets.py`, `orders/sets.py`, and `tests/optimizer/test_extension.py`, `tests/test_connection.py`, `tests/test_relay_node_field.py`, `tests/test_list_field.py`, `tests/optimizer/test_multi_db.py`. Spec territory: Slices 2 and 3, Decisions 11 and 12, and the optimizer / strictness / FK-id-elision / plan-cache edge-case bullets. |
| R1c | `docs/builder/bld-034-review-1c-fakeshop_and_surface.md` | `examples/fakeshop/apps/products/schema.py`, `apps/products/services.py`, `apps/products/filters.py`, `examples/fakeshop/test_query/test_products_api.py`, `examples/fakeshop/apps/products/tests/test_schema.py`, and `django_strawberry_framework/types/definition.py` + `types/base.py` (the Decision 2 forward-reserved `fields_class` slot and `DEFERRED_META_KEYS`). Spec territory: Slices 4 and 5, Decisions 1, 2, 13, the `## Definition of done` items, and the `## Test plan`'s Slice 4 list. |

**R2, R3, integration, final gate:** `none; sequential`, one cohort each.

## Checklist

- [x] Slice 0: spec rationale extraction (pre-flight step 7) -> `docs/builder/bld-034-slice-0-rationale_extraction.md`
- [x] R1a: conformance audit — cascade module, public surface, package tests -> `docs/builder/bld-034-review-1a-cascade_module.md`
- [x] R1b: conformance audit — optimizer cooperation and composition pins -> `docs/builder/bld-034-review-1b-composition_pins.md`
- [x] R1c: conformance audit — fakeshop activation, live coverage, deferred surface -> `docs/builder/bld-034-review-1c-fakeshop_and_surface.md`
- [x] R2: spec reconciliation — spec states the current contract; rationale takes the history -> `docs/builder/bld-034-review-2-spec_reconciliation.md`
- [x] R3: code repair — closed the one SKIPPED contract (R1c B4a) -> `docs/builder/bld-034-review-3-code_repair.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-034-integration.md`
- [x] R4: rationale correction — finding I1, the shipped-not-deferred edge memo -> `docs/builder/bld-034-review-4-rationale_correction.md`
- [x] Final test-run gate -> `docs/builder/bld-034-final.md`

## R1 outcome (all three cohorts `review-accepted`)

| Cohort | Rows | CONFORMS | SUPERSEDED | STALE-DESCRIPTION | RENAMED | **SKIPPED** |
|---|---|---|---|---|---|---|
| R1a — cascade module | 88 | 62 | 29 | 11 | — | **0** |
| R1b — composition pins | 38 | 33 | 0 | 5 | 0 | **0** |
| R1c — fakeshop + surface | 59 | 47 | 2 | 5 | 2 | **1** |

(R1a's grades sum above its row count because 13 rows carry more than one grade; each cohort's artifact records the re-derivation.)

**The single SKIPPED contract — R1c finding B4a.** The spec's `## Slice checklist` Slice 4 box 2 and `## Definition of done` item 10 both state the live matrix as *anonymous / per-`view_<model>` / **staff*** across the `Entry -> Item -> Category` chain. `test_cascade_staff_sees_everything` loops only `allCategories` and `allItems`; `EntryType`'s and `PropertyType`'s staff branches are asserted nowhere. Nothing superseded that contract — it was simply not fully landed. **This is the cycle's answer to "was anything skipped in the code", and R3 exists to close it.**

R1c's High finding H1 has the same remedy and is why the gap matters rather than being cosmetic: replacing `EntryType`'s user read with the broken `getattr(info.context, "user", None)` form — the exact regression the spec's `## User-facing API` warns about — fails **0 of 125 rows** across both products test files, against a green baseline with 0 collection errors, while the control (removing `ItemType`'s cascade) fails 11 at the same scope. Weakly pinned, not harness-impossible. Because all three non-staff branches of all four hooks are the same expression, a user-read regression is observable **only** through the staff branch, and on `EntryType` and `PropertyType` nothing exercises it.

**Escalated to the maintainer rather than dispatched (contract-level, per `docs/builder/BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch`).** R1c finding M2: `examples/fakeshop/apps/products/schema.py` carries 18 rotted card ids in comments (`046` x7, `047` x5, `049` x6; live referents `TODO-BETA-055-0.1.1` / `-056-0.1.2` / `-058-0.1.3`), beside one *correct* `TODO-BETA-062-0.1.5` that must not be swept. The file is a `.py` file and therefore inside this cycle's scope, but the fix is **not** dispatched, for the reason `worker-0.md` `## Closing out a kanban card` states: the same rot is homed on `KANBAN.md` with per-site grading that rules four spec sites "leave verbatim" **because the source still reads the old id**. The two halves are coupled, `KANBAN.md` is outside this cycle's maintainer-set scope, and a partial fix that leaves the surfaces disagreeing is worse than uniformly-wrong. It goes to the deferred-work catalog with the coupling stated.

## R2 outcome (`final-accepted`)

34 of 43 dispatched findings discharged; the 9 left open are all outside the round's authority (the frozen card-id sites, the SKIPPED contract R3 owns, and five maintainer escalations), each carrying a one-line reason and a catalog bullet. The spec now states the shipped contract directly — **0 occurrences of `Post-ship`, `Revision `, `as of review`, `later changed`, or `amendment`** anywhere in it — and the history landed in the rationale companion as `**Post-ship:**` bullets under its Decisions plus entries under `## Non-Decision deliberation` (R2 reported these as "14 under 11 Decisions plus 6"; the integration pass re-derived the figures as **19 under 10 Decisions plus 6 = 25** — R2's `11` counted sections rather than Decisions. **R4 then added two bullets, so the figure at `HEAD` is 20 under 10 Decisions plus 7 = 27**, re-measured 2026-08-28 by enumerating every indent-0 `- **Post-ship` line against its enclosing `##` heading; that is the number to cite). Spec 112,241 -> 128,905 bytes; rationale 69,448 -> 93,722. `## Definition of done` item 1's own verification command went from **exit 2 to exit 0** (it named the pre-archive `docs/spec-034-…` path). Gates after the rewrite: `check_spec_glossary` `OK: 42 terms` exit 0, `check_citations --check` `OK: 857 citations resolve` exit 0, scaffold exit 0, 96/96 and 51/51 ref-def parity, 0 unresolved anchors. R2 also performed the Worker 1 final verification the three R1 cohorts were waiting on and set each to `final-accepted`.

Not split, and the reason is the round's own shape: the headline divergence is one contract restated at eight sites in three grammars across five sections, so a section-wise split would guarantee the half-reconciled state `worker-1.md` forbids.

## R3 outcome (`final-accepted` after one revision loop)

Closed the cycle's single SKIPPED contract. `examples/fakeshop/test_query/test_products_api.py` gains `_CASCADE_ROOT_FIELDS` (the four-field matrix named once), a parametrized `test_cascade_staff_sees_everything` (name kept; four node ids where the shipped in-body loop was one), a sibling `test_cascade_staff_sees_private_rows_hidden_from_non_staff`, and the `_cascade_page_gids(model)` helper. Focused `-k cascade`: 6 -> **13 passed**. Diff `+95/-12`, one file, no production code.

**The measurement that matters.** R1c recorded the broken-user-read mutation failing **0 of 125 rows**. After R3 it fails 2 named rows on `EntryType` and 2 on `PropertyType` — and that result was produced **five independent times** (Worker 2 pass 1, Worker 3 pass 1, Worker 1 final pass 1, Worker 2 pass 2, Worker 3 pass 2, Worker 1 final pass 2), always the same node-id sets against an unmoved `132 passed` baseline with 0 collection/setup errors and byte-compared reverts.

One revision loop: Worker 3 escalated a two-site duplicated ORM page-expectation rather than holding it; Worker 1 ran the existence challenge, found no deletion available (T1's `expected` **is** the assertion; T2's window guard stops a pagination failure reading as a permission failure), and ruled consolidate. Worker 3's pass-2 grep confirms removal rather than relocation: `_RELAY_MAX_RESULTS]` returns exactly one line tree-wide. Floor run discharged by the builder pass and **re-run** at pass 2: `/tmp/dsf-floor-034`, Python 3.10.19, django 5.2.16, strawberry-graphql 0.316.0, `-k cascade` -> 13 passed; shared `.venv` untouched.

Three Lows, all prose-only corrections recorded rather than open work: a false stated reason for dropping a `Category`-hardcoded trailer (the drop itself is right), a falsified plan prediction that repeated literals would fall (`pytest.param("x", …, id="x")` writes each name twice), and a false stated obstacle to annotating the helper's parameter.

## Grading rule every R1 cohort applies (so the three partition findings the same way)

Each contract the spec states is graded into exactly one bucket, and the bucket decides where it routes:

- **CONFORMS** — the code implements what the spec states. No action.
- **SKIPPED** — the spec states it, nothing later superseded it, and the code does not implement it. **This is the class the cycle exists to catch.** Routes to **R3** (code repair). Requires the negative to be proven, not assumed: name the symbol or test searched for, the search grammar, and the evidence of absence.
- **SUPERSEDED** — the code implements something else *deliberately*, because a later card, spec, or hardening pass changed the contract. Routes to **R2** (spec reconciliation), and the cohort must name the superseding work (commit, card, spec, or the module comment that records it) so R2 can attribute the `**Post-ship:**` bullet.
- **STALE-DESCRIPTION** — the code is right and the spec's *description* of it is wrong, imprecise, or cites a symbol/path that has since moved. Routes to **R2**.
- **RENAMED** — the spec names a test or symbol that no longer exists under that name but whose contract is pinned under another. Routes to **R2**, carrying the live name.

A count is not a finding: for every population claim ("all 40 named tests exist"), record the enumeration, not the number — `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`. Search the shortest distinctive token and count occurrences, never matching lines; a renamed or reflowed spelling is invisible to a long grep phrase.
