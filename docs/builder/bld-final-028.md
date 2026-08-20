# Build: Final test-run gate — orders / 0.0.8 (028)

Spec reference: `docs/SPECS/spec-028-orders-0_0_8.md` (the shipped-state record; lines 1-8 are its opener / `Status:` / Owner / Predecessors block) and its rationale companion `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md`
Status: final-accepted

## Plan (Worker 1)

### Worker-1-only artifact shape

The final test-run gate has no Worker 2 build pass and no Worker 3 review pass, so this artifact carries a
`## Plan (Worker 1)` block and a `## Final verification (Worker 1)` block and no others. That is the same
adaptation [`bld-integration-028.md`][bld-integration] made, on the same authority: [`ARTIFACT.md`][artifact]
governs the `Status:` line and the named sections each worker writes, and [`BUILD.md`][build]
`## Final test-run gate` assigns this pass to Worker 1 alone.

### What this gate is, in one paragraph

Four things and nothing else: the full `pytest` sweep with coverage opted out, Django's own consistency
checks against the example project, the read-only lint / format / diff gate, and the floor-verification
backstop. It does not re-review the cycle. It does not edit its own subject: all four slices and the
integration pass closed `final-accepted`, and a gate that edits what it measures is not a gate. A failure
here routes back through the owning slice's loop with `Status: revision-needed`, never a fix in this pass.

### Required reading walked

The `yes` cells in the Worker 1 column of [`BUILD.md`][build]'s Required-reading table, walked as a column
rather than from memory: [`AGENTS.md`][agents], [`START.md`][start], [`BUILD.md`][build] (whole heading list
plus `## Final test-run gate`, `## Floor verification`, `## Coverage is the maintainer's gate, not a
worker's tool`, `## Claims are proven mechanically, never accepted on prose`, `## Hot-path budget`,
`## Cross-slice integration pass`, `## Required plan structure`, `## Spec reconciliation`),
[`ARTIFACT.md`][artifact], [`worker-1.md`][worker-1], [`GOAL.md`][goal], [`docs/GLOSSARY.md`][glossary]
(Index plus the five Ordering entries), [`CHANGELOG.md`][changelog] (the `0.0.8` section end-to-end plus a
`^## ` heading scan), the active spec, the rationale companion, and the active build plan
[`build-028-orders-0_0_8.md`][build-028].

Plus the catalog's source material — all five completed artifacts, each read in full and in order, and each
`final-accepted`: [`bld-slice-1-028`][bld-slice-1] (255 lines), [`bld-slice-2-028`][bld-slice-2] (3,430),
[`bld-slice-3-028`][bld-slice-3] (441), [`bld-slice-4-028`][bld-slice-4] (608),
[`bld-integration-028`][bld-integration] (494). My own memory file
`docs/builder/worker-memory/worker-1-028.md` was read first, as its 32-line consolidated state; no other
worker's memory file was opened.

### Spec status-line re-verification (this spawn)

Per [`worker-1.md`][worker-1] `## Spec status-line re-verification (every Worker 1 spawn)`. Spec lines 1-8
still read as a shipped-state record and this pass falsifies nothing in them: the opener names
`DONE-028-0.0.8` and the `0.0.8` version boundary, the `Status:` line names the five `orders/` modules, the
finalizer phase-2.5 binding, the `ALLOWED_META_KEYS` promotion, the fakeshop wiring and the two test homes,
and the rationale-companion pointer added by Slice 1 resolves on disk. Two moving-file claims re-read at
source rather than carried: [`CHANGELOG.md`][changelog] carries the Ordering `### Added` bullet and the
`Meta.orderset_class` promotion `### Changed` bullet under `## [0.0.8] - 2026-06-03`, with no `[Unreleased]`
heading anywhere in the file; [`docs/GLOSSARY.md`][glossary]'s Index reads `shipped (0.0.8)` for all five
Ordering symbols. **No spec edit this pass, and none owed** — see
`### Spec changes made (Worker 1 only)`.

### Gate checklist

This artifact has no spec slice and no dispatched findings, so the position [`ARTIFACT.md`][artifact] gives
to `### Spec slice checklist (verbatim)` carries the gate's own commands instead, under the same
tick-and-audit discipline: a box is `- [x]` only when its command actually ran in this pass and its result
is recorded verbatim below.

- [x] `uv run pytest --no-cov` — full sweep across all three test trees
- [x] `uv run python examples/fakeshop/manage.py check`
- [x] `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`
- [x] `uv run ruff format --check .`
- [x] `uv run ruff check .`
- [x] `git diff --check`
- [x] Floor verification — confirm the plan's declared scope was honored
- [x] `### Deferred work catalog` written, the next spec author's reading list

---

## Final verification (Worker 1)

### Summary

**Every gate command passes. `Status: final-accepted`.** The suite is green on the first and only full sweep
of the cycle (6,179 passed, 40 skipped, exit 0), both Django consistency checks are clean, and all three
lint / format / diff checks are clean, so no pre-flight baseline exception is needed and none was recorded.
Floor verification was declared `none` by the plan and correctly not run; the declaration and its absence
are both stated below rather than silently omitted. The routed deferred-work population is transcribed for
the next spec author (31 raw items into 27 labelled entries, four absorptions named), and the cycle's
dispatch question is answered in one line: **nothing was skipped in the code.**

### The gate, command by command

| # | Command | Result | Exit |
| --- | --- | --- | --- |
| 1 | `uv run pytest --no-cov` | `6179 passed, 40 skipped in 70.01s (0:01:10)` | **0 — PASS** |
| 2 | `uv run python examples/fakeshop/manage.py check` | `System check identified no issues (0 silenced).` | **0 — PASS** |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | `No changes detected` | **0 — PASS** |
| 4 | `uv run ruff format --check .` | `425 files already formatted` | **0 — PASS** |
| 5 | `uv run ruff check .` | `All checks passed!` | **0 — PASS** |
| 6 | `git diff --check` | no output | **0 — PASS** |
| 6b | `git diff --cached --check` | no output | **0 — PASS** (supplement: the tree carries one staged rename, which the unstaged form cannot see) |

Notes on three of the readings, so a later reader does not mistake either for a finding:

- **`--no-cov` is the only coverage-shaped flag used, and no other appears anywhere in this pass.** It is
  required because `pytest.ini`'s `addopts` auto-applies `--cov`, and plain `uv run pytest` is therefore a
  coverage run, which [`BUILD.md`][build] `## Coverage is the maintainer's gate, not a worker's tool`
  forbids to every worker pass including this one. **No line-coverage figure was inspected, computed, or
  asserted** — the only `pytest`-side requirement is that the suite passes, and it does. The rule has no
  carve-outs.
- **This is the cycle's first full sweep, by design.** [`AGENTS.md`][agents] #"No pytest after edits" defers
  it to exactly here; every earlier pass ran focused or collect-only scopes.
- **`ruff format --check .` emits a standing configuration warning**, that `COM812` may conflict with the
  formatter. It is a pre-existing property of `pyproject.toml`'s lint selection, not output of this cycle,
  and the command still exits 0 with every file already formatted. Not a gate failure and not this cycle's
  to change (the maintainer's scope fence excludes `pyproject.toml`).

### Floor verification

**The plan declares floor-verification scope `none`** ([`build-028-orders-0_0_8.md`][build-028] preamble
line 9: *"Floor-verification scope: none. No slice touches a Django / Strawberry / channels integration seam
— no slice changes an executable statement."*). **So no floor venv was built, no floor run was owed, and
none was run.** Stated explicitly because [`BUILD.md`][build] `## Floor verification` makes this gate the
backstop that confirms floor verification happened: a reader who finds no floor run here must be able to
tell a declaration from a miss. This is the declaration.

The declaration is sound on its own terms rather than accepted as prose: the cycle changed **zero executable
statements** across all sixteen authorized paths, re-derived at the integration pass on two independently
written instruments against two reference points — **64 readings, 0 mismatches** — so there is no
version-sensitive behavior for a floor run to exercise.

The canonical floor, **for the record only** and taken from [`BUILD.md`][build] `## Floor verification`
rather than from memory: Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**. **The
shared `.venv` was not mutated, and no version of anything in it is stated anywhere in this artifact** — a
`.venv` version claim would have to be read with `uv pip list` and cited, and this pass had no reason to
make one.

### Boundary count, hot path, failability

- **Boundary count: zero, across the whole cycle.** Every `.py` edit in all four slices is comment or
  docstring text. **So no failability proof is owed anywhere — by entitlement, not by omission.** A boundary
  is an executable expression; the cycle's executable token stream is identical to its reference points at
  every path. A reader who finds no `### Failability proofs` section in a slice artifact is looking at an
  entitlement, not a gap. No fail-open shape can have landed for the same structural reason.
- **Hot path: none owed.** Nothing this cycle touched runs per request, per resolver, per row, per
  connection, or per outbound message — the plan declared `none` and no pass flagged otherwise. No number is
  missing.
- **This gate itself adds none of the above**: it writes two Markdown files.

### The cycle's answer to the question it was dispatched for

**Nothing was skipped in the code.** `DONE-028-0.0.8` shipped the whole ordering subsystem and the surface
has since *grown*, not shrunk — a fifteenth live order test, two more fakeshop ordersets, path
pre-validation, and an async-gate rejection all post-date the spec. Worker 0's pre-dispatch verification
checked every contract-bearing claim against HEAD before the plan was written, and **Slice 3 independently
found no code finding** while looking for one specifically: every spec/HEAD divergence resolves as HEAD
being stricter (`getattr(f, "column", None) is not None` over `hasattr`; `startswith("ASC")` over substring
membership; `classify_path` pre-validation the spec promised none of; the async-gate rejection closing an
authorization bypass), single-sited (the six relocated mechanisms, `build_lazy_input_annotation`,
`_bind_sidecar_sets`, `run_in_one_sync_boundary`, the registration seam), or a later card's deliberate
correction (the row-preserving `Min`/`Max` aggregate, `queryset.model`, the deleted cookbook-compat
delegate). The subsystem's *description* was the only thing wrong, and that is what this cycle repaired.

**Two exceptions, both re-derived by this pass rather than accepted from a prior artifact:**

1. **`OrderSet.check_permissions` was deliberately deleted post-ship** in `9e864f59` ("Finish REVIEW of
   0.0.9"), which rewrote the module docstring in the same diff. `grep -rn 'def check_permissions'
   --include='*.py' django_strawberry_framework/` returns exactly one hit package-wide,
   `django_strawberry_framework/filters/sets.py:2714`, the filter-side sibling. The order-side method is
   gone by intent.
2. **`ORDER_BY_ARG` was never shipped**, because nothing needs it — Strawberry derives `orderBy` from the
   resolver's `order_by` parameter. `git log --oneline -S'ORDER_BY_ARG' --all -- '*.py'` returns **no
   commits**, and the constant has **0** occurrences in the live non-`.venv` tree.

### The two pre-flight deviations, and why they were right

Recorded in the plan's `## Pre-flight outcome and deviations` and re-stated here because the maintainer reads
this file first. **Neither is a lint exception** — the plan records no lint, format, or `git diff` baseline
exception of any kind, and none was needed: all three checks exit 0 above.

1. **Step 3 (artifact reset): old `bld-*.md` / `build-*.md` were NOT deleted.** The prior `spec-027`
   cycle's artifacts were untracked and uncommitted at pre-flight, so deleting them destroys the only copy
   — which [`worker-0.md`][worker-0] names as the one irreversible pre-flight mistake. This cycle used
   `-028`-suffixed artifact paths instead, all six verified absent before creation.
2. **Step 5 (scratch cleared): scratch was NOT cleared**, same reason — `worker-memory/worker-{0,1,2,3}-{025,026,027}.md` are three cycles' notebooks. This cycle used
   `worker-<N>-028.md` files.

Both calls have since been vindicated by events: the `spec-027` record was committed during this cycle
(`8a9840dc`, `8bab7ea8`, `5447c9eb`), and all 18 of its artifacts are now tracked. Deleting them at
pre-flight would have destroyed them.

### Working-tree state after the gate, and the `db.sqlite3` question

HEAD is unchanged at `5447c9eb`. `git status --short` after the full sweep shows **16 paths**: 8 modified
(7 `.py` plus the spec), 1 staged rename (`docs/builder/build-027-filters-0_0_8.md` ->
`docs/builder/DONE/build-027-filters-0_0_8.md`, another session's), and 7 untracked (the rationale companion
plus this cycle's six artifacts, this file making seven).

**`examples/fakeshop/db.sqlite3` is NOT dirty after the full `pytest` run.** The plan lists it, along with
`KANBAN.md`, `KANBAN.html` and `docs/GLOSSARY.md`, as a concurrent-writable tracked generated file this
cycle plans no edit to, and it was flagged as expected churn from this run. It did not churn: `git status
--short` does not list it and `git diff --stat HEAD -- examples/fakeshop/db.sqlite3` is empty. **Nothing was
reverted and nothing was staged** — recorded so the maintainer knows the clean reading is a measurement, not
an omission. The other three generated files are likewise unchanged.

No `.py` file, no spec file, and no fenced file was edited by this pass. No commit, no branch, no amend, no
`git stash` / `checkout` / `restore` / `worktree`.

### Deferred work catalog

The next spec author's reading list, required by [`BUILD.md`][build] `## Final test-run gate`. Walked from
every per-slice and integration artifact's spec-reconciliation notes and `What looks solid` /
`Notes for Worker 1` sections. `No deferred work; the build delivered the spec end-to-end.` is **not** the
case here.

**On the count, stated so it is re-derivable rather than inherited.** [`bld-integration-028`][bld-integration]
`### Deferred-work consolidation, re-confirmed and extended to 30 items` reports **30**, arrived at as 25
routed (16 from Slice 2's second final verification + 9 from Slice 3) + 5 added by the Slice-4 cohort. That
figure excludes the integration pass's **own** added item (F3 below) and does not net the merges the same
table declares. Counting the integration item, the raw routed population is **31**. Transcribed below they
consolidate into **27 labelled entries**, after four declared absorptions listed at the end of this catalog
— counted mechanically off this file's own bullets, not asserted. Slice 1 routed **0** items of its own: all
seventeen of its `### Notes for Worker 1` entries were handed to Slice 3, which discharged D3-D16 in the
spec. Every number quoted inside a bullet is that bullet's source artifact's measurement, not a re-derivation
by this pass, except where marked.

**Two cross-cycle maintainer decisions — the items only the maintainer can settle.**

- **A1 (S2-12, merging S3-8) — which cycle owns the four files both cycles claimed, and whether Slice 2's
  cookbook-citation carve-out survives.** Source: [`bld-slice-2-028`][bld-slice-2] item 12 (Ruling 15),
  [`bld-slice-3-028`][bld-slice-3] note 8, restated at [`bld-integration-028`][bld-integration] S2-12. The
  four contested paths are `django_strawberry_framework/orders/sets.py`, `orders/__init__.py`,
  `orders/factories.py`, and `utils/inputs.py`. **The other cycle overtook 4 of Slice 2's 6 cookbook-ref
  sites and its own artifact ticks them**, which is what makes the carve-out a decision rather than an
  observation. **Now CLOSED as a live event** — both cycles' work is committed or accounted for, all 18
  `027` artifacts are tracked, and nothing was lost in either direction — so what remains is the ownership
  ruling and the lesson, not a risk. No spec line licenses it; it is a process decision.
- **A2 (S2-13) — three `spec-028` hunks sit in committed history under `spec-027` commit messages that do
  not mention them.** Source: [`bld-slice-2-028`][bld-slice-2] item 13, scope corrected at
  [`bld-integration-028`][bld-integration] S2-13. `8a9840dc`, `8bab7ea8` and `5447c9eb` between them carry
  Slice-2 hunks in **11** of the sixteen authorized paths, and **2 paths are MIXED** — `tests/test_registry.py`
  and `examples/fakeshop/test_query/test_library_api.py` carry earlier passes committed and later passes
  dirty, so `git diff HEAD -- <path>` under-reads them one way and `git diff 5c6fdd71 HEAD` the other.
  **Read the current file for any present-state claim.** Nothing was amended, re-staged, or force-pushed by
  any worker, and nothing needs to be; the maintainer needs to know it at handoff.

**The instrument card — the single highest-value item here.**

- **B1 (S2-2, absorbing S3-6 and Slice-4 item 3, and carrying E5 as a clause) — the
  `scripts/check_citations.py` gate extension, now five clauses.** Sources:
  [`bld-slice-2-028`][bld-slice-2] items 2 and 5,
  [`bld-slice-3-028`][bld-slice-3] note 6, [`bld-slice-4-028`][bld-slice-4] item 3, restated at
  [`bld-integration-028`][bld-integration] S2-2 / S3-6. The gate resolves `path::Symbol` only, with `docs/`
  out of scope, so it **cannot see**:
  1. a broken `spec-NNN <Heading>` citation at all — the `Decision N` / `DoD N` / `test plan` /
     `Edge cases` class, which is the population Slice 3 had to protect by hand;
  2. a citation wrapped across two source lines — the `path::Symbol` + `#"substring"` join, where a
     flattened *per-form* probe reads both halves as intact, so the newline must sit **inside** the pattern;
  3. a citation split mid-path-segment at a `/`;
  4. a **case** variant — `Spec-028` versus `spec-028`. The bare `[Ss]pec (Decision|DoD|Edge) N` class is
     **5** case-insensitively against **1** under a capital-only pattern;
  5. a citation wrapped inside a `#` comment, where the continuation `#` lands between the halves and
     defeats a plain `\s+` flatten — the flattening probe must collapse `\n[ \t]*#?[ \t]*`. **Measured
     tree-wide at 15 sites** a plain flatten cannot see (58 wrapped-qualifier sites join-aware versus 43
     plain).

  **This cycle paid for that blind spot ten separate times.** The strongest single datapoint is
  cross-cycle: the *other* cycle's `bld-slice-7-027-raw_line_refs.md:214` certifies "no wrapped citation
  introduced" over a hunk that is itself a wrapped join. A working prototype exists — the integration pass
  built and ran a resolver over all 579 non-`.venv` `.py` files on three provably-different instruments,
  reading **87** heading-bearing citations and **0** unresolved — so the card can cite a run, not a design.
- **B2 (S2-4) — `bld-slice-7-027-raw_line_refs.md:214`'s false certification**, the site named above. Source:
  [`bld-slice-2-028`][bld-slice-2] item 4 (Ruling 11), confirmed present by two instruments at
  [`bld-integration-028`][bld-integration] S2-4. Another cycle's artifact: no worker of this cycle may edit
  it, and the correction is the maintainer's to make there.
- **B3 (S2-3, extended by Slice-4 item 4) — the standing instrument lessons.** Source:
  [`bld-slice-2-028`][bld-slice-2] item 3 (Ruling 13), [`bld-slice-4-028`][bld-slice-4] item 4, extended at
  [`bld-integration-028`][bld-integration] S2-3. Four ways to write a check that cannot fail: **`\s`
  crosses a newline**, so `\s`-vs-flattened is one instrument written twice (use `[ \t]+` for the
  line-scoped half); **`grep -c` counts lines, not occurrences**; **`endswith("")` is True for every
  string**; and the control-hygiene clause — **a BSD-`sed` control that silently applied nothing made two
  independent identity instruments both report `SAME`, because a control that did not run reads identically
  to a passing proof.** Every transient control must assert its own mutation landed before its reading is
  believed. Cheap to state, expensive to relearn.

**The anchor-vs-distance ruling — stated as a test rather than a judgement so it cannot be re-fought.**

- **C1 (Slice-4 item 5) — the deferral of `tests/orders/test_finalizer.py:432` and
  `django_strawberry_framework/utils/inputs.py:1300`, with its measurement attached.** Source:
  [`bld-slice-4-028`][bld-slice-4] item 5, confirmed and refined at [`bld-integration-028`][bld-integration]
  `### The escalation the cohort's review raised`. **The ruling: a bare `Decision N` is a defect when nothing
  a reader passes on the way to it establishes the spec, and anaphora when something does.** Distance is not
  the discriminator — 320 lines of *file* is not 320 lines of *reading order* when the antecedent is the
  module docstring. The measurement, so the next reader re-derives the number and not the ruling: **442**
  line-scoped unprefixed `Decision N` / `DoD N` occurrences in package + tests + examples `.py` (a
  repo-wide convention, not a defect population); **384** once the 58 wrapped spec-qualified citations are
  credited; **16** in files carrying no `spec-NNN` anchor anywhere, and **none of the 16 is in the orders
  family**; the family's own count is **2**, both in `tests/orders/test_finalizer.py`, a file carrying 3
  `spec-028` anchors including two in its module docstring — so both are distant in-file anaphora, which the
  test acquits. (`443` if a prior review cycle's `docs/review/temp-tests/` scratchpad is included: a corpus
  difference, not a digit.)
- **C2 (Slice-4 item 1) — `tests/orders/test_inputs.py:516`'s `per spec-028` names no Decision** where the
  content it asserts is Decision 9's parking clause. Source: [`bld-slice-4-028`][bld-slice-4] item 1. Not a
  bare `Decision N`, so it sat outside the dispatched class; qualifying it would have taken the file's
  `Decision N` total 3 -> 4, the exact reading the qualified-not-added proof exists to detect. A one-word
  change for whichever future pass owns the `spec-NNN`-without-a-Decision class.
- **C3 (Slice-4 item 2) — the four lowercase `spec Decision N` sites naming other cards' decisions**:
  `django_strawberry_framework/filters/factories.py:143`, `django_strawberry_framework/list_field.py:192`,
  `tests/test_list_field.py:206`, `tests/types/test_resolvers.py:785`, plus the capital-`Spec` `spec-015`
  site at `tests/types/test_relay_interfaces.py:371` which carries its own spec id and is correct. Source:
  [`bld-slice-4-028`][bld-slice-4] item 2. **None is in the orders family**; respelling any would be a
  worker asserting another card's contract. Pairs with B1 — the clause that resolves `spec-NNN Decision N`
  is the clause that flags a `spec Decision N` naming no spec.

**The DRY item, and the one card inside it worth actioning first.**

- **D1 (S2-9) — the DRY existence challenge, both halves, deferred with its ground recorded.** Source:
  [`bld-slice-2-028`][bld-slice-2] item 9 (Ruling 7), re-checked at [`bld-integration-028`][bld-integration]
  S2-9 / P5, and explicitly declined for reopening by [`bld-slice-4-028`][bld-slice-4]. Rows 1-2 (diamond
  dedup and clear-namespace tolerance, each pinned three times over one single-sited `utils/`
  implementation that already carries a family-neutral pin) are a **contract-level maintainer decision**
  whose higher-quality fix is a **deletion** of the two family copies, precedent D13; `worker-3.md` reserves
  the delete call. **`OrderSet._apply_orderings`'s two guards, each pinned twice over one helper through
  `apply_sync` and `apply_async`, belong in the SAME look** — same family, not a separate item (Worker 3's
  observation, and it merges here rather than standing alone).
  **The row worth actioning first is a card in its own right: `django_strawberry_framework/utils/strings.py::graphql_camel_name`
  #"if not core:" has NO family-neutral pin, and its only coverage rides two family aliases.** Inlining or
  renaming either alias silently retires the last pin while `fail_under = 100` stays green, because the
  other copy still executes the line. The fix is cheap and runs opposite to rows 1-2: add the `""` / `"_"` /
  `"__"` rows to `tests/utils/test_strings.py` beside the existing `pascal_case("")` / `pascal_case("_")`
  pair. **The whole of D1 was deferred because every resolution changes executable statements and would
  forfeit this cycle's zero-boundary entitlement**, which four passes and seven instruments rest on.
- **D2 (S2-10) — the promotable `_safe_import` pins.** Source: [`bld-slice-2-028`][bld-slice-2] item 10
  (Ruling 14). A `tests/utils/` row asserting `_safe_import` returns `None` for a **cold submodule of a
  poisoned package**, plus a row asserting `clear_generated_input_namespace` makes **exactly two** calls.
  The invariant is currently *described* accurately and measured green in all four warm/cold x family
  states; the card is to *pin* it. New executable statements, so it forfeits the entitlement either way.

**Residue inventories — populations, not vocabularies.**

- **E1 (S2-7) — the tree-wide raw-line-citation residue, inventory corrected in BOTH directions.** Source:
  [`bld-slice-2-028`][bld-slice-2] item 7, re-measured at [`bld-integration-028`][bld-integration] S2-7.
  `django_strawberry_framework/mutations/{resolvers,fields,sets}.py` and
  `examples/fakeshop/test_query/test_products_api.py` now read **0**, discharged by the concurrent cohort.
  The surviving genuine first-party residue is **10 line-scoped / 12 flattened across four files**:
  `django_strawberry_framework/optimizer/walker.py` 1, `tests/optimizer/test_walker.py` 3,
  `tests/optimizer/test_extension.py` 3 + 1 wrapped, `tests/mutations/test_sets.py` 3 + 1 wrapped — all
  naming `spec-035` / `spec-036`. **Two hits in the tree-wide 14/16 are not citations and must not be
  chased**: `scripts/check_trailing_commas.py:910` (prose about the script's own reporting) and
  `tests/test_export_dry_review.py:153` (`"line 1"` as assert-string fixture data).
- **E2 (S2-11) — out-of-family review-item ids: the catalog names 3 of 54.** Source:
  [`bld-slice-2-028`][bld-slice-2] item 11, population measured at [`bld-integration-028`][bld-integration]
  S2-11. `django_strawberry_framework/utils/inputs.py` carries `spec-039 P2` and `spec-040 D6` (3
  occurrences) — but the defect class measured tree-wide is **52 line-scoped / 54 flattened across 24
  files**, naming ten other cards (`spec-035`, `036`, `039`, `040`, `041`, `044`, `048`, `051`), heaviest at
  `auth/mutations.py` 6, `mutations/inputs.py` 6, `rest_framework/inputs.py` 4, with **2 wrapped**
  (`mutations/resolvers.py`, `rest_framework/resolvers.py`) so the class carries the wrap defect too. Left
  because each is a claim about a card this cycle never verified.
- **E3 (S2-1) — two upstream-cookbook line refs left with reason.** Source:
  [`bld-slice-2-028`][bld-slice-2] item 1 (Ruling 2), both confirmed byte-identical at
  [`bld-integration-028`][bld-integration] S2-1: `tests/orders/test_sets.py:169` #"per cookbook line 280"
  and `tests/orders/test_factories.py:251` #"cookbook lines 124-130". Rule 27's remedy is
  `path::QualifiedName`, the target is an unvendored, unpinned third-party checkout, and
  `check_citations.py` is first-party-only — so a rewrite buys a citation the gate still cannot resolve
  whose truth depends on an external version. **Do not re-open without pinning the cookbook.** Corrected
  from "six" to "two": the other four were converted by the concurrent cohort.
- **E4 (S2-6) — two third-party-target wrapped joins deliberately left.** Source:
  [`bld-slice-2-028`][bld-slice-2] item 6. `examples/fakeshop/test_query/test_library_api.py:8014` (Django's
  `related_descriptors.py::_filter_prefetch_queryset`, pre-existing) and
  `django_strawberry_framework/orders/sets.py:258` (the cookbook, and the other cycle's live hunk). Both
  cite trees `check_citations.py` is not fail-closed on.
- **E5 (S2-5) — the split-path wrap at `examples/fakeshop/test_query/test_products_api.py:3334`** (`` `tests/rest_framework/ `` / newline / `` test_resolvers.py` ``), the third wrap grammar. Source:
  [`bld-slice-2-028`][bld-slice-2] item 5 (Ruling 12), confirmed at that exact line by
  [`bld-integration-028`][bld-integration] S2-5. It keeps its own entry because it is a distinct site, and
  it is **also folded into B1 as clause 3** — the grammar it demonstrates is what the gate must learn.

**Documentation and record items, all outside this cycle's scope fence.**

- **F1 (S3-1) — `KANBAN.md`'s `DONE-028-0.0.8` body still carries four retired claims** (`check_permissions`
  in the apply-pipeline sentence, "exactly 14 live HTTP tests", "reverse-FK with
  denormalized-multiplicity-pinned", the pre-archive `docs/spec-028-orders-0_0_8.md` path) plus two
  `per <ID> of rev3` breadcrumbs the spec no longer carries. Source: [`bld-slice-3-028`][bld-slice-3] note 1.
  The spec's quoted copy is corrected, so the two now differ deliberately. `KANBAN.md` is DB-generated:
  the fix is a kanban DB edit plus a `scripts/build_kanban_md.py` regenerate. **Fold into the sweep already
  carded at `KANBAN.md:357`** rather than opening a new item.
- **F2 (S3-2) — `docs/GLOSSARY.md`'s `## OrderSet` entry carries no position-side-channel note** where its
  `## RelatedOrder` sibling does. Source: [`bld-slice-3-028`][bld-slice-3] note 2, asymmetry confirmed at
  HEAD by reading both entries at [`bld-integration-028`][bld-integration] S3-2. DB edit plus re-render; a
  maintainer call, not a defect.
- **F3 (integration pass's own addition) — `docs/GLOSSARY.md`'s `## RelatedOrder` entry narrates its own
  history**: *"the neutral shared module per the package's set-family discipline, **not `filters.base` as
  named in earlier revisions**"*. Source: [`bld-integration-028`][bld-integration]
  `### Consolidated deferred-work inputs`, re-read at source in its Pass 2 and still present. That is the
  shape [`BUILD.md`][build] `## Spec rationale extraction` forbids in a spec, appearing in a generated
  standing doc instead. `docs/GLOSSARY.md` is DB-generated and fenced this cycle, so out of scope to edit;
  the fix is a glossary-DB edit plus a re-render, and it **belongs beside F2**, which touches the same entry
  pair.
- **F4 (S3-3) — `docs/TREE.md` omits `__init__.py` by renderer design**, so every spec claiming "five
  files" for a five-module subpackage disagrees with the rendered tree by one. Source:
  [`bld-slice-3-028`][bld-slice-3] note 3. A convention mismatch that recurs on every subpackage card, not
  a `spec-028` defect; worth one line in [`BUILD.md`][build]'s doc-wrap guidance so the next spec author
  states the count the tree will actually show.
- **F5 (S3-4) — `spec-028`'s two orphaned `0.0.9` deferrals**, already carded at `KANBAN.md:357` and
  re-verified live. Source: [`bld-slice-3-028`][bld-slice-3] note 4. The `DjangoListField`
  `orderBy`-argument deferral **re-derives as still true at HEAD** (`list_field.py`'s `_default` and all
  three `_wrap` variants take `(root, info)` only, so no arbitrary resolver argument survives); the
  position-side-channel leak-closing design is the second. Both need the card-or-drop adjudication the board
  item names.
- **F6 (S3-5) — `[relay]` is a defined-but-unused link definition in the spec**, and was so at HEAD before
  Slice 1 (verified: not an orphan the rationale move created). Source: [`bld-slice-3-028`][bld-slice-3]
  note 5, [`bld-slice-1-028`][bld-slice-1] note 15. A one-line decision for whoever next opens the file:
  either Decision 7's import-cycle discussion links `types/relay.py`, or the definition goes.
- **F7 (S3-7) — two `spec-028` statements about `0.0.9` are defensible in either voice, and Slice 3 changed
  neither.** Source: [`bld-slice-3-028`][bld-slice-3] note 7. Decision 12 describes
  `connection.py::_synthesized_signature` / `::_pipeline_sync` / `::_pipeline_async` in the present tense
  (correct — the connection field shipped as `DONE-030-0.0.9`), while the Non-goals block still frames the
  connection field as future work scoped out of *this card* (also correct). A maintainer may prefer Non-goals
  to say "shipped later in `0.0.9`". A voice choice, not a false claim.
- **F8 (S3-9) — no code finding surfaced, and it was looked for specifically.** Source:
  [`bld-slice-3-028`][bld-slice-3] note 9; the integration pass independently found none either. **A
  negative result worth keeping**, because an unrecorded negative is a finding the next pass re-opens. The
  detail is in `### The cycle's answer to the question it was dispatched for` above.
- **F9 (S2-8) — the two-of-four `except ImportError` twins in `tests/test_registry.py`.** Source:
  [`bld-slice-2-028`][bld-slice-2] item 8. After C6c the file carries two accurate twins and two —
  `::test_clear_tolerates_unimportable_connection_submodule` and
  `::test_clear_tolerates_unimportable_relay_module` — still on the original false premise, fenced to
  `spec-030-connection_field-0_0_9` P3b and `spec-032` Decision 8. Both proved byte-identical against both
  baselines. A maintainer decision, because respelling either asserts another card's contract.
- **F10 (S2-14) — a banner count is unmaintained by construction.** Source:
  [`bld-slice-2-028`][bld-slice-2] item 14. Slice 2's step 19 made C5's banner accurate, named and
  derivable, not *durable*. The alternative, if the maintainer prefers it: drop the count and let the banner
  name only the contract.
- **F11 (S2-15) — three plan-text defects, unfixed because their files are fenced or not this role's.**
  Source: [`bld-slice-2-028`][bld-slice-2] item 15, third added at
  [`bld-integration-028`][bld-integration] S2-15. (i) The plan misquotes [`BUILD.md`][build]
  `### When to run the helper during build` for Worker 3, adding a logic-added qualifier the rule does not
  have — which would license a real skip in a future cycle whose `types/` edit *does* add logic. (ii) The
  plan's `### Partition correction 1` measurements are superseded by Rulings 2 and 3. (iii) The dispatch
  brief's committed/dirty split is wrong in three ways (see A2).
- **F12 (S2-16, superseding S3-6's scope half) — the protect-list inheritance for the next reconciliation
  cycle, with the corrected population.** Source: [`bld-slice-2-028`][bld-slice-2] item 16 (Rulings 9-10),
  superseded and re-measured at [`bld-integration-028`][bld-integration] S2-16 and its resolver re-run.
  **87** heading-bearing citations (64 `Decision N` + 20 `test plan` + 2 `DoD N` + 1 `Edge cases`), against
  **108** total `spec-028` tokens of which 21 are bare and carry no heading — *"106 citations" was a token
  count where the resolvable population was 85*, before this cycle's two repairs moved both. Anchors:
  `### Decision N`, `## Test plan`, `## Definition of done` (there is **no** `### DoD` heading), and
  `## Edge cases and constraints`. **The census must be case-insensitive** (B1 clause 4). Re-measure at
  entry; read no number out of an artifact.

**The four absorptions, named so the 31 -> 27 arithmetic reads.**

- **S3-6 -> B1.** Slice 3's gate clause (resolve `spec-NNN <Heading>` against the named spec's heading list)
  is the same card as S2-2, and the prototype now exists.
- **S3-8 -> A1.** Slice 3's "cross-cohort seam widened" is S2-12's event at an earlier reading; both are now
  closed as live events.
- **Slice-4 item 3 -> B1 clause 5.** The `#`-comment flattening requirement is a clause of the same gate
  card, not a card of its own.
- **Slice-4 item 4 -> B3.** The control-hygiene rule is one of the standing instrument lessons, and belongs
  beside the three that share its shape.

### DRY check across this pass and prior accepted slices

**No new duplication, and structurally none possible** — this pass writes two Markdown files and changes no
executable statement, so there is no helper, constant, branch, or literal to consolidate. One cross-cycle
asymmetry recorded at the integration pass is re-stated here so no later sweep "fixes" it:
`django_strawberry_framework/utils/inputs.py` deliberately carries **two** attribution conventions — the
dual-family `spec-027 / spec-028 Decision N` (the concurrent cohort's, lines 6, 75, 400, 1297, 1441) and the
single-family `spec-028 Decision 8` (Slice 2's C12, lines 1708 and 1733). The difference is semantically
load-bearing: 1708 and 1733 state a contract the order family has and the filter family does not, so adding
`spec-027` there would make both sentences false. A uniformity sweep would break them.

### Spec changes made (Worker 1 only)

**None, and none owed.** `docs/SPECS/spec-028-orders-0_0_8.md` and
`docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md` both closed `final-accepted` at Slice 3 and are
read-only to this gate; the maintainer's scope fence and this pass's writable set (this file plus
`docs/builder/worker-memory/worker-1-028.md`) both exclude them. Per-spawn status-line re-verification is
recorded under `### Spec status-line re-verification (this spawn)`; every claim in lines 1-8 was checked
against HEAD and holds. Nothing this pass measured is a spec defect.

**Deferral reasons for boxes left `- [ ]`: none.** All eight boxes in `### Gate checklist` are `- [x]` and
each names the command that ran and the result recorded above. The catalog above discharges
[`worker-1.md`][worker-1] `## Final verification job` step 3's deferral obligation for the cycle as a whole:
every slice artifact closed with all its own boxes ticked (Slice 1's spec edits, Slice 2's 22, Slice 3's
101 replacements, Slice 4's 2, the integration pass's 11), so nothing is silently un-ticked anywhere in the
cycle.

### Final status

`final-accepted`.

All six gate commands pass, plus the staged-diff supplement: **6,179 passed / 40 skipped / exit 0** on the
cycle's only full sweep, both Django consistency checks clean, `ruff format --check .` and `ruff check .`
and `git diff --check` all clean, so no baseline exception is invoked and none exists in the plan. **Floor
verification: scope `none` as declared, so no floor venv was built and no floor run was owed** — a
declaration, not a miss, and sound because the cycle changed zero executable statements. **Boundary count
zero across the whole cycle, so no failability proof is owed anywhere by entitlement rather than
omission**; hot-path number none owed; `examples/fakeshop/db.sqlite3` did not churn and was neither
reverted nor staged.

The cycle's dispatch question is answered: **nothing was skipped in the code.** The ordering subsystem
shipped in full and then grew, with exactly two evidenced exceptions — `OrderSet.check_permissions`
deliberately deleted post-ship in `9e864f59`, and `ORDER_BY_ARG` never shipped because nothing needs it,
both re-derived by this pass. What this cycle repaired was the subsystem's *description*: a rationale
companion created where the archive's last gap was, a spec rewritten from a seven-revision chronology into a
current contract, and the citation rot in sixteen `.py` paths retired without changing a single executable
statement.

The deferred-work catalog transcribes the whole routed population — **31 raw items into 27 labelled
entries**, four absorptions named — each with its source artifact section and, where one exists, the
measurement that makes it re-derivable. **The build is closed and hands off to the maintainer for review and
commit.**

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[goal]: ../../GOAL.md
[start]: ../../START.md

<!-- docs/ -->
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[artifact]: ARTIFACT.md
[bld-integration]: bld-integration-028.md
[bld-slice-1]: bld-slice-1-028-rationale_extraction.md
[bld-slice-2]: bld-slice-2-028-citation_and_provenance_rot.md
[bld-slice-3]: bld-slice-3-028-spec_reconciliation.md
[bld-slice-4]: bld-slice-4-028-decision_citation_consistency.md
[build]: BUILD.md
[build-028]: build-028-orders-0_0_8.md
[worker-0]: worker-0.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
