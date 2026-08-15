# Build: Final test-run gate — spec-006 residual cycle

Spec reference: `docs/SPECS/spec-006-public_surface-0_0_3.md` (whole file, already archived) plus its companion `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md`
Build plan: `docs/builder/build-006-public_surface-0_0_3.md`
Status: final-accepted

**Shape note.** This is the cycle-closing gate, not a slice. `ARTIFACT.md`'s `## Plan (Worker 1)` / `## Build report (Worker 2)` / `## Review (Worker 3)` sequence has no subject: there is no slice to plan, no builder to dispatch, and no diff for a reviewer that the three per-item artifacts have not already reviewed and accepted. The sections below are the ones `BUILD.md` `## Final test-run gate` and `worker-1.md` `## Final test-run gate` require — every command with its real result, the floor-verification confirmation, the `### Deferred work catalog` (Worker 1 is its only author), plus the cross-artifact read this cycle substitutes for the integration pass the plan deliberately omits, a final integrity re-derivation, and the maintainer's commit brief.

**What this pass did to the tree.** It created this one file. It ran the gate commands, the read-only integrity checks, and read-only `git` / `grep` / ORM measurements. No spec, no rationale, no artifact of a closed item, no DB, no rendered doc, no source, no test was written. No `git checkout` / `restore` / `stash` / `worktree`, no branch, no commit, no `pytest --cov*`, no `ruff --fix`.

**HEAD, re-derived rather than trusted.** `git rev-parse --short HEAD` -> **`947f7494`**, unmoved from the plan's, R1's, R2's and R3's readings.

---

## Gate run (Worker 1)

Every command below was run in the order `BUILD.md` `## Final test-run gate` gives, in the shared `.venv`, from the repository root. Output is quoted, not paraphrased.

### 1. Full sweep — `uv run pytest --no-cov`

```text
================= 5640 passed, 40 skipped in 150.14s (0:02:30) =================
```

**PASS**, exit 0. All three test trees (`tests/`, `examples/fakeshop/apps/*/tests/`, `examples/fakeshop/test_query/` and `examples/fakeshop/tests/`) in one sweep. `--no-cov` is the only coverage-shaped flag used, and it is required because `pytest.ini`'s `addopts` auto-applies `--cov`; no line-coverage figure was inspected or asserted (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`).

### 2. Django's own consistency checks against the example project

```text
$ uv run python examples/fakeshop/manage.py check
System check identified no issues (0 silenced).
exit=0

$ uv run python examples/fakeshop/manage.py makemigrations --check --dry-run
No changes detected
exit=0
```

**PASS**, both. No model / admin / url-config drift, and no unmade migration — which matters this cycle only as a backstop, since no item touched a model.

### 3. The lint / format / diff gate — read-only, never `--fix`

```text
$ uv run ruff format --check .
warning: The following rule may cause conflicts when used with the formatter: `COM812`. ...
418 files already formatted
exit=0

$ uv run ruff check .
All checks passed!
exit=0

$ git diff --check
exit=0
```

**PASS**, all three. The `COM812` line is ruff's standing configuration warning, present on every invocation in this repo and not a finding. `git diff --check` is silent, so there is **no whitespace error and no conflict marker anywhere in the tree** — including in the six source/test/review files two other sessions are mid-flight in, and including in this cycle's own four durable files.

### 4. Floor verification

**No floor-verification scope declared.** The plan declares floor-verification scope **none** for every residual item, and I confirm the declaration rather than repeating it: no item touches a Django / Strawberry / channels integration seam — request/response handling, view or ASGI plumbing, upload or body parsing, session/auth surface, queryset or expression compilation, schema or type construction, consumer or middleware wiring. The cycle's whole write set is two archived specs, two archived rationale companions, the kanban/glossary DB, and three script-rendered documents. `git diff --numstat -- '*.py'` lists **five** files and every one is the concurrent transport session's (`django_strawberry_framework/_boundary_ordering.py`, `_cross_web_patches.py`, `middleware/request_body.py`, `tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py`); `git status --porcelain` carries **no** untracked `.py` file. **No floor venv was built and the shared `.venv` was not mutated** — a floor run with no seam to exercise would be theatre, and `worker-1.md` reserves `revision-needed` for a *declared* scope nobody ran, which is not this case.

### Failure attribution — none owed, and why the mechanism is recorded anyway

**Every command in the gate passed, so the plan's baseline exception (`## Baseline-dirty out-of-scope files`, "Baseline exception for the final test-run gate") was not exercised.** It is recorded here that it was available and unused, because the honest statement of a green gate against a tree three other sessions are writing is *not* "the exception carried us" — it is that nothing failed. Nothing was reported to the maintainer as a failure, because there was no failure to report.

The attribution rule the exception would have applied, stated mechanically so a later reader can check that I did not need it: this cycle's writable set was exactly `docs/SPECS/spec-006-public_surface-0_0_3.md`, `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md`, `docs/SPECS/spec-002-optimizer-0_0_2.md` and `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` (retirement sites only), `examples/fakeshop/db.sqlite3` plus the three rendered docs (`docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`), the four `bld-006-*` artifacts, the plan, and the four namespaced memory files. **No `.py` file, in any pass** — so a `ruff` or `pytest` failure in a `.py` file would have been outside that set by construction, provable by naming the file rather than by asserting the attribution. A `git diff --check` hit inside one of this cycle's own files would have been this cycle's and would have blocked.

**One non-blocking finding for the maintainer, re-derived rather than inherited from R3's hand-off.** An *unscoped* `uv run python scripts/check_trailing_commas.py --check` reports:

```text
.claude/projects/-Users-riordenweber-projects-django-strawberry-framework/memory/one-spec-owns-each-feature.md:20: should carry the canonical LINK-DEFINITIONS footer scaffold (all category markers)

1 layout violation(s); run with --fix to resolve
```

`git check-ignore -v` on that path returns `.gitignore:170:.claude/`, so it is a **git-ignored** agent-memory file, not a repository document. It is not in the gate's command list and is not fixed here; it was not read for content beyond the tool's own message. The scoped run over this cycle's four durable files is green (below).

> **CORRECTED after `final-accepted` — see `## Post-acceptance correction` at the foot of this file.** This paragraph originally read "belonging to another session" and "not this cycle's". **Both are false: the file is this cycle's own**, written by Worker 0 at 10:19 to record the maintainer's single-ownership law. The finding's disposition — non-blocking, no action owed, cannot reach a commit — is unchanged and was never contingent on whose file it is.

---

## Cross-artifact read

This stands in for the cross-slice integration pass the plan deliberately omits (`## Artifact list`: "a cross-slice integration pass exists to find duplication across slices that landed source, and this cycle lands none"). The staged-anchor sweep — the one live obligation of that pass — ran in R3 and is re-run below. What is left is composition: do the three items' outputs form one coherent result, and does any of them contradict another.

**Required reading discharged.** All three prior artifacts of this cycle were read in order — `bld-006-r1-rationale_move.md` (1,328 lines, four passes: Worker 1 move, Worker 3 review `revision-needed`, Worker 1 apply-changes, Worker 3 pass 2 accept, Worker 1 final `final-accepted`), `bld-006-r2-spec_reconciliation.md` (1,538 lines, Worker 1 move, Worker 3 review with a Medium and three Lows, Worker 1 apply-changes, Worker 3 pass 2 `review-accepted` with the `__version__` Low escalated, Worker 1 `final-accepted`), and `bld-006-r3-doc_completion_archive.md` (1,146 lines, the full unmodified chain: Worker 1 plan, Worker 2 ORM writes and regenerates, Worker 3 review with an escalated Medium and two Lows, Worker 1 `final-accepted`). All three carry `Status: final-accepted` and all three checkboxes are `- [x]` in the plan.

**1. The rationale R1 created is the one R2 appended to and R3 audited — one file, three strata, append-only after R1.** Re-derived from the file's heading structure rather than from the artifacts' claims:

| Stratum | Sections on disk now | Owner |
|---|---|---|
| R1's move | `## How to read this file`, `## Provenance of this record`, `## Entries keyed to the spec` (3 keyed entries), `## Standing note — the rules outlived their instruments` | R1 |
| R2's reconciliation | `## Reconciliation against the shipped package` (13 `###` entries, including `### The coordinated retirement of spec-002's `## Visibility status``), `## Documented is not the same as exported` (2 entries, R2's own review-driven append) | R2 |
| R3's finding | `## A rule stated over an artifact nobody measured` (2 entries: the `:17` amendment and `### The shape behind three corrections, named once`) | R3's final verification |

The byte chain reconciles end to end: R1 created it at 228 lines / 15,449 bytes and left it at 233 / 15,935 after its apply-changes pass; R2 appended to 734 lines; R3's final verification appended to **801 lines / 57,777 bytes**, which is what `wc -c -l` reads on disk now. No stratum edits a prior one, which is `worker-1.md` rule 4's append-only discipline, and each later stratum keys its entries to the *renamed* spec headings R2 produced rather than to R1's pre-reconciliation ones — the composition test that a stale key would fail.

**2. The spec chain composes, and every heading the later strata key to exists.** `docs/SPECS/spec-006-public_surface-0_0_3.md` is **168 lines / 15,806 bytes** on disk. R1 left it at 177 / 11,019; R2 rewrote it (`git diff --numstat` against HEAD: `52 62`) to 168 / 15,661; R3's final verification made one in-place sentence replacement at `:17` (168 lines before and after, +145 bytes) -> 15,806. Its heading set now reads `## Problem statement`, `## Where the public surface is defined`, `## Goal`, `## Non-goals`, `## Topics`, `### Top-level re-export rule`, `#### Decision for 0.0.3`, `### When a subsystem is top-level vs subpackage-only`, `### How status is published`, `### Status-marker vocabulary`, `### Alpha signaling rules`, `### What a subsystem spec owes these rules`, `## Coordination with other specs`, `## References` — i.e. R1's `## Open questions` removal, R2's three renames (`## Current state` -> `## Where the public surface is defined`, `### docs/README.md structure` -> `### How status is published`, `### When to amend this spec` -> `### What a subsystem spec owes these rules`) and nothing else. **No contradiction:** the rationale's keyed entries name both the old and new titles where a rename happened, and the H1 companion pointer at `:3` still resolves to a definition that exists on disk.

**3. The retirement R2 performed is the one R3's card prose discharges.** Both halves re-derived:

- **R2's half.** `git diff --numstat`: `docs/SPECS/spec-002-optimizer-0_0_2.md` is `0 3` (the `## Visibility status` heading, its sentence, the blank) and `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` is `57 3` (the `#visibility-status` definition removed, the sentence at `:261`/`:263` re-pointed at `## Shipped slices`, and the appended `## The discharged deferral — Visibility status retired by the spec-006 cycle` at `:503`).
- **R3's half.** The rendered `KANBAN.md:319` now opens "`docs/SPECS/spec-002-optimizer-0_0_2.md` carries no status-shaped section any more" and states the retirement as **done** by the spec-006 residual cycle, names both retired spec-006 bullets, records that the companion no longer defines `#visibility-status`, and points at the discharge record. `KANBAN.md:322` records the "do not sweep up spec-006's two sites" instruction as spent.

So R2's action and R3's board prose describe the same event with no drift: the section is gone, the citations are gone, the deferral that guarded it is discharged in the same board item that used to carry it. **The retirement census is in `## Final integrity re-derivation` below.**

**4. No item's output contradicts another's, checked in the three places it could.** (a) R2 renamed `### docs/README.md structure`, the section R1 cut a paragraph from — and R1's keyed entry names that section by its pre-rename title while R2's names both, so neither is stranded. (b) R2 escalated `__version__`'s marker-less bullet as a fifth roster site with a conditional route; R3 took the first branch (link it to `#joint-version-cut`, an existing anchor whose body names `__version__`), which is exactly the branch R2's instruction licensed, and did **not** author a new entry — so nothing went onto card 052 for it. (c) R3's `:17` amendment narrows a sentence **R2 wrote** in the same cycle; R2's rationale entry for that sentence and R3's appended entry sit in different `##` sections, the earlier one untouched, and the later one states the measurement (14 of 48 bullets) that falsified the earlier wording. That is a correction recorded as a correction, not a contradiction left standing.

**5. Every obligation one item pointed at the next was discharged in a durable file, not left in a scratchpad.** This is the composition test that matters most, because a per-cycle artifact closes with its cycle and anything left only there is lost. R1 pointed four obligations at R2 and R2 discharged all four: (i) the single-ownership provenance R1's box 8 cited but never wrote — now in spec-006's rationale preamble, quoting both retired bullets; (ii) D6's retraction proper — now under that entry's *Claims the spec no longer makes*, which is what makes R1's deliberately quotation-free standing-note bullet survive R2's rewrite of `:44`; (iii) the D8 present-tense Low, resolved by R1's own preferred branch (note the restatement in R2's D8 entry, do **not** reopen R1's paragraph in an append-only file); (iv) re-derive every `docs/README.md` claim at write time, which R2 did and then closed permanently by removing the structural claim. R2 in turn pointed five numbered inheritances at R3 (`### Hand-off to R3`) and R3 discharged all five, including the `__version__` site R2 added beyond the plan's four. **Nothing was handed forward and dropped.**

**6. There is no source-level duplication to hunt, and that is a property of the cycle rather than an omission.** No item wrote a `.py` file; `scripts/review_inspect.py` was legitimately never run (`BUILD.md` `### When to run the helper during build` gates it on `.py` files added or changed) and `docs/shadow/` was never written, each recorded as an explicit skip with its reason by all three items. The cross-artifact DRY question that *does* exist here — one fact told twice across a spec and its rationale companion — was measured at every item: R1 drove its non-scaffold 8-word shingle overlap to 0 after a Worker 3 finding, R2 re-derived 3 shingles at n=8 all inside an obligatory heading citation, and R3 added no new duplication. One accepted residue survives, L2, catalogued below as deliberately not-yet-fixable.

---

## Final integrity re-derivation

Cheap, and worth repeating once more at the close: every one of these is the last thing standing between a green cycle and a broken card-wrap chain, a dangling anchor, or a retirement that did not hold.

```text
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-006-public_surface-0_0_3.md
OK: 7 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md
OK: 3 terms - all have glossary entries and at least one spec link.
exit=0

$ uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
exit=0

$ uv run python scripts/check_trailing_commas.py --check \
    docs/SPECS/spec-006-public_surface-0_0_3.md \
    docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md \
    docs/SPECS/spec-002-optimizer-0_0_2.md \
    docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md
exit=0
```

All four green. `check_spec_glossary` on spec-006 is character-identical to the pre-flight baseline the plan recorded at step 6, so the 7-anchor constraint held through three passes of rewriting — including R3's `:17` edit, which is why running it after that edit was the point rather than a formality. The `import_spec_terms` form is the **read-only** `--check`; no DB write happened in this pass.

**The retirement holds, with every survivor in a licensed class.** `grep -rni 'visibility.status' --include='*.md' .`, counted as **occurrences per file** and not as matching lines:

| Occurrences | File | Class |
|---|---|---|
| 0 | `docs/SPECS/spec-006-public_surface-0_0_3.md` | **the retirement itself** — both citing bullets gone |
| 0 | `docs/SPECS/spec-002-optimizer-0_0_2.md` | **the retirement itself** — the section gone |
| 11 | `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` | licensed: the append-only discharge record and the prior cycle's history *about* the removal |
| 7 | `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` | licensed: this cycle's own record of why the copy was requested and then retired |
| 4 | `KANBAN.md` | licensed: R3's discharge prose on card `TODO-ALPHA-052-0.1.0` (rows 8 and 9) |
| 1 | `docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md` | licensed: the plan's row 10 — a verbatim quotation of a historical instruction, explicitly not a reference |
| 25 / 16 / 15 / 7 | `bld-006-r2`, `bld-006-r3`, `build-006-…`, `bld-006-r1` | licensed: this cycle's own per-cycle scratchpads |
| 5 / 1 / 1 | `build-002-…`, `build-003-…`, `bld-003-final.md` | licensed: closed cycles' artifacts, never edited |
| 1 / 1 | `build-007-…`, `bld-007-r1-…` | the concurrent spec-007 cycle's, not this cycle's to touch |

**And no live anchor survives.** `grep -rno '#visibility-status' --include='*.md' .` finds 9 occurrences: 8 inside `bld-006-*` / `build-006-*` scratchpads, and **1** in `KANBAN.md:319` — inside the sentence that *states the definition no longer exists*. There is **no `[spec-002-visibility]` link definition and no in-page anchor to that slug anywhere durable**, which is the check that a retired heading did not leave a broken link behind.

**Two further re-derivations, because the amended `:17` and the plan's own gate rest on them.** `docs/GLOSSARY.md` `## Public exports` carries **48** bullets and **0** with no link at all — so the sentence R3 amended is satisfied by the document, and is falsifiable (a bullet reaching nothing fails it, which is precisely the `__version__` state R2 escalated one pass ago). Against the package: `len(__all__)` is **37**, **0** entries fail `hasattr`, **0** `__all__` names lack a bullet, and the 11 bullet names outside `__all__` are the subpackage groups plus `SerializerMutation`, exactly as the section's four-group shape predicts.

**Staged anchors.** `grep -rEn 'TODO\(spec-006|TODO-(ALPHA|BETA|STABLE)-006' .` — every hit is inside this cycle's own `build-006-*` / `bld-006-*` artifacts quoting the pattern; **zero** in package source, in any test tree, in `KANBAN.md` / `KANBAN.html` / `BACKLOG.md`, or in any standing doc. Card 006 is `DONE-006-0.0.3`, so no `TODO-ALPHA-006` form should exist and none does. `BUILD.md` `## Cross-slice integration pass` step 6 is discharged.

**Not swept into another session's commit.** Proven with `git log --stat` over this cycle's paths, never `git status` alone: the newest commit touching `docs/SPECS/spec-006-public_surface-0_0_3.md`, `docs/SPECS/spec-002-optimizer-0_0_2.md`, either rationale, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, or `examples/fakeshop/db.sqlite3` is **`947f7494`** ("retarget cards 050 and 051 onto 0.0.15", 2026-08-10), which predates this cycle. Every write is still uncommitted and attributable, and the per-path diff shape matches R3's record exactly: `KANBAN.html 1 1`, `KANBAN.md 4 4`, `docs/GLOSSARY.md 5 1`, `spec-002 0 3`, `spec-002 rationale 57 3`, `spec-006 52 62`. `docs/SPECS/appx/spec-006-public_surface-0_0_3-terms.csv` is absent from `git status` and must stay so.

---

### Deferred work catalog

The next spec author's reading list. Walked from every per-item artifact's spec-reconciliation notes, `### Notes for Worker 1`, `### Notes for Worker 3`, `### What looks solid`, `### DRY findings`, and severity sections, plus R3's `### Hand-off to the final gate`. Worker 1 is this section's only author.

**Owned by card `TODO-ALPHA-052-0.1.0` (the alpha documentation-completeness card)**

- **The ASCII-hyphen citation in `CardItem` pk 1260** — *source:* `bld-006-r3-doc_completion_archive.md` `### The two Lows — settled` (L1), first raised in that artifact's `#### L1` and `### Notes for Worker 1 (spec reconciliation)` item 2. *Licence:* "DEFERRED, not routed, with two named targets in priority order … the defect degrades a citation rather than falsifying a claim, no reader is lost (the stem is unique and greppable)". The board item quotes the spec-002 companion's discharge heading with an ASCII hyphen where the heading on disk carries an em dash, so the quoted string greps to **0** (re-derived this pass: the heading is at `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md:503` with the em dash, and `KANBAN.md:319` renders the hyphen form). **Targets, in order: (1) the maintainer at commit** — in `CardItem` pk 1260's `text`, replace `` `## The discharged deferral - Visibility status retired by the spec-006 cycle` `` with `` `## The discharged deferral` ``, via the ORM with `.save()` and never a queryset `.update()`, then regenerate `KANBAN.md` and `KANBAN.html`; **(2) failing that, card 052's five-site sweep**, which already owns this exact `CardItem`.
- **The `DjangoSchema` bullet is a fourth site for its two linked entries' construction-time fact** — *source:* `bld-006-r3` `### DRY findings` / `#### L2`, confirmed at `### The two Lows — settled` (L2). *Licence:* "the structural fix is already card 052's … **Do not 'fix' this before the entry exists**", because trimming now "would leave the name a gloss that documents nothing and two foreign anchors with no stated relevance, which is strictly worse than the duplication". Owed: author the `DjangoSchema` glossary entry, after which the bullet collapses to one line and the duplication disappears rather than being cut.
- **Entry granularity for `DjangoSchema` and `DjangoMutationExecutionContext`** — *source:* the plan's `### Maintainer decision 2` WIDENED block, carried in `bld-006-r3` `### Hand-off to the final gate`. *Licence:* "Whether `DjangoSchema` earns a **full glossary entry** with its own anchor stays card 052's decision — it is an editorial call about entry granularity, not a contract violation." The question is recorded on `CardItem` pk 1240 and was deliberately **narrowed, never closed**; `is_complete` is ticked on none of the three rewritten items.
- **Group listings for `views`, `routers`, and `middleware.debug_toolbar` in `## Public exports`** — *source:* the plan's `### Maintainer decision 2` `CORRECTION`, restated as R2's hand-off item 4 and again in `bld-006-r3` `### Hand-off to the final gate`. *Licence:* "The three families the section omits … are **NOT in scope here** … Adding those groups is a glossary-completeness call of the same family as the `DjangoSchema`-entry question, so it goes to card 052's list, not to R3." Each family already has its own glossary entry; only the group listing is absent, and the section's four groups are correct as they stand.
- **Card 052's sweep is five sites, not four** — *source:* R2's `### Hand-off to R3` item 2 and `bld-006-r3` `### Hand-off to the final gate`. *Licence:* "`bld-003-final.md` item 7 records `KANBAN.md:314` as a fifth card-052-adjacent site the plan's table omits. Not this cycle's to write beyond noting it." R3 has since rewritten that line for a different reason (the pk 1240 clause its own glossary write falsified), which does not discharge the fifth-site note.

**Owned by the maintainer**

- **Five committed `docs/review/rev-*.md` files deleted by another session** — *source:* the plan's `### Second growth, recorded at the close of R1's apply-changes pass`, re-reported in `bld-006-r1` and `bld-006-r2` `### Concurrent work — reported, not touched` and in `bld-006-r3` `### Hand-off to the final gate`. *Licence:* "`AGENTS.md` rule 22 names `docs/review/`'s `rev-*.md` as committed source of truth and prescribes `git checkout HEAD -- docs/review/` as the restore — but rule 34 forbids reverting concurrent work without explicit authorization … **Worker 0 escalates it to the maintainer; no worker touches `docs/review/`.**" Content is safe at `947f7494`. Re-measured this pass: `rev-_django_patches.md`, `rev-_strawberry_patches.md`, `rev-apps.md`, `rev-conf.md` are still `D`, and `rev-_cross_web_patches.md` is now `M` where it was `D`. Untouched by this cycle in every pass.
- **The L1 one-character DB fix**, as target 1 above — the DB write and the commit are already the maintainer's, which is what makes it the cheapest correct route.
- **~~A git-ignored `.claude/` agent-memory file fails an unscoped `check_trailing_commas --check`~~ — WITHDRAWN as a maintainer item; see `## Post-acceptance correction`.** The finding is real and its disposition never changed (git-ignored, unreachable by the `source-layout` pre-commit hook, which receives staged paths only; not in the gate's command list; no action owed). What was wrong is the attribution this row inherited from `bld-006-r3:1070` — *"another session's agent-memory file"* — and repeated. **The file is this cycle's own**, `.claude/…/memory/one-spec-owns-each-feature.md`, written by Worker 0 to record the maintainer's single-ownership law. Nothing here needs the maintainer, so the maintainer-owned count in `### Review outcome` below drops from three to two.

**Owned by Worker 0 (the plan is Worker 0's file; workers do not edit it)**

- **Four defects in the plan's own evidence formulas, all found at build time with the implemented behavior correct in every case** — *source:* `bld-006-r3` `### Notes for Worker 1 (spec reconciliation)` items 1-4, adopted as corrections at that artifact's `### The 'Dispatched findings checklist' — independent audit of all 12 boxes`. *Licence:* "All four are defects in evidence formulas I wrote; the implemented behavior is right in every case." They are: (1) box D2's `git diff … is empty` formula, **unsatisfiable** from the moment R2 legitimately rewrote the spec (`52 62`), with the mtime substitute recorded; (2) the row-8 dash, which is L1 above; (3) the `experimental` / `aspirational` occurrence counts, `0/0/0/0` across `docs/README.md` / `docs/TREE.md` / `docs/GLOSSARY.md` / root `README.md` but **1 each** in `KANBAN.md`, both prose and neither a marker; (4) `CardItem.order` versus rendered ordinal — `order` 1 / 8 / 11 render as the 1st / 6th / 9th `#### Scope` bullets because the sequence is sparse.
- **Growth events 4-7 to append to the plan's baseline-dirty list** — *source:* `bld-006-r2` `### Concurrent work — reported, not touched` (event 4: `bld-007-r2-spec_reconciliation.md`), `bld-006-r3` `### Notes for Worker 1` item 5(b) (`bld-007-r3-doc_completion_archive.md`) and `#### Addendum to '### Validation run' — a FIFTH growth event` (`_cross_web_patches.py`), plus `### Hand-off to the final gate`. *Licence:* "reported by three passes, reverted by none"; the plan's own instruction is that "workers **report it and never revert it**, and Worker 0 appends it here rather than a worker editing the plan." **An eighth event is added by this gate, same disposition:** `docs/builder/bld-007-r2-spec_reconciliation.md` and `docs/builder/bld-007-r3-doc_completion_archive.md` are both present untracked (the concurrent spec-007 cycle is now at its own R3), `docs/review/rev-_boundary_ordering.md` and `docs/review/review-0_0_14.md` remain untracked, and `docs/review/rev-_cross_web_patches.md` has moved `D` -> `M`. HEAD is still `947f7494`. Nothing read, nothing reverted, nothing checked out.
- **A standing-doc candidate: the duplicate-check tokenizer rule** — *source:* `bld-006-r1-rationale_move.md` `### Notes for Worker 1 (spec reconciliation)` (pass 2) and again at that artifact's final verification. *Licence:* "a phrase-shaped duplicate check must tokenize on word characters and case-fold, because Markdown emphasis and punctuation sit *inside* the window and shift token positions without changing the words … **worth carrying past this cycle**", routed as "worth **Worker 0 or the maintainer** considering for `worker-1.md` `### Performing the rationale move`". The cycle's own evidence for it: R1's first measurement failed **open**, reporting 0 where a word-character tokenizer finds 3. Nothing in a per-cycle scratchpad outlives the cycle, so the rule needs a durable home or it is re-learned.
- **The spec/rationale-versus-sibling-companion shingle overlap, flagged non-blocking** — *source:* `bld-006-r1` final verification, restated in R2's `### DRY check across R1's and R2's output`. *Licence:* R1 measured 245 total / 180 non-scaffold 8-word shingles against the sibling rationale companions, accepted them as **house template** rather than copied content, and "flagged non-blocking for the maintainer … since R2 appends to this same file under the same template", instructing R2 "**Do not treat the number as a finding**". R2's own re-derivation confirmed the direction: 182 shingles for the 006/002 pair against a **247** control for 006/005, i.e. *less* coupled than the control. No action owed unless the maintainer wants the template's shared vocabulary reduced.
- **Scratchpad record corrections carried by R2's final verification** — *source:* `bld-006-r2` `### Spec changes made (Worker 1 only)`, "Record corrections, none of them durable-file defects and none warranting a re-pass": D9's box citing a non-existent `GlossaryDocument` model where the row is `apps.kanban.models.BoardDoc` with `namespace='glossary'`; the n=6 shingle residue being 23 rather than 26; a `KANBAN.md` survivor tally that counted matching lines (2) rather than occurrences (6); and two immaterial line ranges. *Licence:* "confined to this scratchpad … Box stays ticked." No durable file is affected and no target beyond the record itself is owed — catalogued so the class (**right substance, loose citation**, five instances in this one cycle) is not lost with the scratchpads.

**Owned by the concurrent spec-007 residual cycle, and deliberately not touched**

- **Every undischargeable `docs/README.md` obligation spec-006 carried (drift rows D3, D5, D8, D17)** — *source:* the plan's `### First growth` and `### Verified spec-versus-HEAD drift` "Owner of the move" column; R1 and R2 both re-report it under `### Notes for Worker 1 (spec reconciliation)`. *Licence:* "`spec-007` is the named owner of drift rows **D3, D5, D8, and D17** … **Direction of correction still runs toward spec-006.** If R2 finds spec-007 (or its cycle's in-flight edits) made stale by an R2 edit, it records the item for the maintainer and does **not** edit it." R2 reconciled spec-006's side by restating each obligation over the locus that actually exists (`docs/GLOSSARY.md` and `docs/TREE.md`), re-measuring every `docs/README.md` claim at its own writing time and then eliminating the exposure by *removing* the structural claim rather than restating it; the README-side surface remains that cycle's. No path of that cycle was written here.
- **`docs/README.md`'s `**Shipped today**` section-scope version stamp, recorded as a known non-conformance** — *source:* `bld-006-r2-spec_reconciliation.md` `#### ':89's "prose does not repeat the markers" is stated absolutely, and `docs/README.md` repeats one at section scope'` (Worker 3 Low 3), settled at `### Low 3 — ':89' settled as a rule, and written as one`. *Licence:* the review's own disposition — "Either settle it as a rule (and record `docs/README.md`'s `**Shipped today**` section stamp as a known non-conformance owned by `spec-007`) or narrow the sentence"; R2 took the first branch, and its pass-2 review confirmed the settled rule "leaves `docs/README.md`'s `**Shipped today**` stamp conforming, so **no non-conformance is exported into the concurrent cycle's file**". Recorded so the spec-007 cycle inherits the reading rather than re-deriving it.

Nothing in this catalog is a defect in a durable file this cycle owns, which is why none of it blocks `final-accepted`: the two Lows are settled with named targets in priority order, the remaining card-052 items are editorial-granularity calls a beta-line card owns, the plan and role-file items are Worker 0's surface, and the `docs/review/` deletions and the concurrent cycles are other sessions' work under `AGENTS.md` rule 34. **No temp test awaits promotion or deletion in any item** — R1 and R3 created none, and R2's `docs/builder/temp-tests/r2/shingle.py` is a git-ignored scratch instrument its own review recorded as "kept as a temp file only … Nothing to promote."

---

## The maintainer's commit brief

This cycle's diff is **mixed with three other sessions' work** and the maintainer commits it.

**Stage explicitly, path by path. `git add -A` must not be used** — one line: `START.md` "Concurrent sessions" ("Stage explicitly (`git add <path>`), never `git add -A` — you'd sweep the other session's WIP into your commit").

**This cycle's paths — the complete set, and nothing outside it:**

- `docs/SPECS/spec-006-public_surface-0_0_3.md` (`M`, `52 62`) and `docs/SPECS/appx/spec-006-public_surface-0_0_3-rationale.md` (`??`, new, 801 lines) — R1's move, R2's reconciliation, R3's `:17` amendment and companion entry.
- `docs/SPECS/spec-002-optimizer-0_0_2.md` (`M`, `0 3`) and `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` (`M`, `57 3`) — the coordinated retirement and its append-only discharge record. Retirement sites only.
- `examples/fakeshop/db.sqlite3` (`M`) — R3's four rows: `BoardDoc` pk 41 (five `## Public exports` bullet lines) and `CardItem` pks 1240 / 1260 / 1270 on card `TODO-ALPHA-052-0.1.0`, plus a `modified`-timestamp touch on 2,084 rows across `glossary_glossaryspecmention` and `kanban_cardglossaryterm` from the writing `import_spec_terms`. No table gained or lost a row and no concurrent writer's row is in the diff. **Compare `iterdump()` semantics, never file bytes, and never round-trip a dump through `executescript` to compare it — that fabricates differences.**
- `docs/GLOSSARY.md` (`M`, `5 1`), `KANBAN.md` (`M`, `4 4`), `KANBAN.html` (`M`, `1 1`) — **generated**, see the note below.
- `docs/builder/build-006-public_surface-0_0_3.md` and the four `docs/builder/bld-006-*.md` artifacts (`??`) — this cycle's plan and records, including this file.

**`docs/GLOSSARY.md`, `KANBAN.md`, and `KANBAN.html` are generated and their DB source is in the same diff, so they commit together.** Committing the DB without the rendered docs (or the reverse) leaves the tree in a state where the next `--check` run fails; `START.md` "Rendered docs — fix the source, not the file" and `AGENTS.md` #"GLOSSARY.md is DB-generated" are the standing rules, and all three files were produced by their renderers and proved byte-stable across two consecutive regenerates plus a hand-edit test. **Never hand-edit any of the three.**

**Paths that are NOT this cycle's — do not stage them, do not revert them, do not `git checkout` them:**

- Source and tests, a transport / boundary-ordering session's: `django_strawberry_framework/_boundary_ordering.py`, `django_strawberry_framework/_cross_web_patches.py`, `django_strawberry_framework/middleware/request_body.py`, `tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py`.
- `docs/review/`: `rev-_django_patches.md`, `rev-_strawberry_patches.md`, `rev-apps.md`, `rev-conf.md` (`D`, committed files deleted by another session), `rev-_cross_web_patches.md` (`M`, was `D`), and untracked `rev-_boundary_ordering.md` and `review-0_0_14.md`. Escalated to you at the cycle's second growth event; no worker touched any of them.
- The concurrent spec-007 residual cycle: `docs/SPECS/spec-007-onboarding_docs_spec_consolidation-0_0_4.md` (`M`), `docs/SPECS/appx/spec-007-…-rationale.md` (`??`), `docs/builder/build-007-…md` and `docs/builder/bld-007-r1/r2/r3-*.md` (`??`).
- Part of `KANBAN.md`: **the split is exact.** Four changed lines — `:248` is the concurrent card-wrap's (a card item about a `convert_relation` comment in `tests/types/test_base.py`, a different card and a different subject), and `:314` / `:319` / `:322` are this cycle's three `CardItem` rewrites. The two sets are **disjoint**, established from both directions by R3 and re-confirmed here. `docs/GLOSSARY.md` needs no such argument: it was clean at R3's start, so its whole diff is this cycle's.
- `docs/SPECS/appx/spec-006-public_surface-0_0_3-terms.csv` is byte-unchanged, absent from `git status`, and must stay so — its 7 anchor rows are what `import_spec_terms` rebuilds card `DONE-006-0.0.3`'s glossary links from.

**One optional one-character fix you may want to fold in at commit**, L1 in the catalog above: in `CardItem` pk 1260's `text`, `` `## The discharged deferral - Visibility status retired by the spec-006 cycle` `` -> `` `## The discharged deferral` ``, then regenerate `KANBAN.md` and `KANBAN.html`. If you decline it, card `TODO-ALPHA-052-0.1.0` already owns that `CardItem`.

**Nothing was reverted, restored, stashed, or checked out in any pass of this cycle, and no worker committed or branched.**

---

### Summary

The gate is green on every command: `uv run pytest --no-cov` at **5640 passed, 40 skipped**, both Django consistency checks clean, `ruff format --check` / `ruff check` / `git diff --check` all silent. Floor verification is `none` by plan declaration and confirmed — no residual item touches a Django / Strawberry / channels seam, and no `.py` file was writable in any pass. The plan's baseline exception was available and **not needed**, which is the honest close: nothing failed, so nothing was attributed away.

The three items compose. R1 created the rationale companion and drove its overlap with the spec to zero; R2 appended thirteen keyed reconciliation entries, rewrote the spec around the four claims HEAD falsified, renamed three sections, and performed the coordinated retirement of `spec-002`'s `## Visibility status` across every inbound site in one change; R3 closed the last documented-surface gap the spec's own gate creates (five `## Public exports` bullets, so all 37 `__all__` names satisfy condition 3 for the first time), discharged the retirement's two board sites, corrected the one board claim its own write falsified, and left the archive verified rather than moved. Re-derived at the close: 7 glossary anchors intact and all sole carriers, 49 done cards' glossary links intact, spec-002 down to **0** occurrences of the retired heading with every survivor in a licensed class and no live anchor anywhere, 48 glossary bullets with **0** unlinked, 37 `__all__` entries all resolving and all bulleted, and zero staged anchors outside this cycle's own scratchpads. `git log --stat` over the cycle's paths returns `947f7494` as the newest commit touching any of them, so nothing was swept into another session's commit.

**Status: `final-accepted`.** Every catalogued deferral is outside this cycle's durable files: five items on card `TODO-ALPHA-052-0.1.0` (two of them the settled Lows, three of them editorial-granularity calls), three for the maintainer, five for Worker 0's own plan and role-file surface, and two owned by the concurrent spec-007 cycle. Not one is a defect in the spec, either rationale, the DB, or a rendered doc, which is why none of them blocks.

### Spec changes made (Worker 1 only)

**None.** The gate found no defect in the spec, either rationale, any artifact of a closed item, the plan, the DB, or any rendered doc. Per `worker-1.md` `## Spec status-line re-verification`, the spec's first lines were re-read at this spawn's own reading time: line 1 is the title, there is no `Status:` / target-release / owner / predecessor header block and never was, `## Problem statement` opens at `:5`, and `grep -nE 'not yet|remains to be|will be shipped'` over the file returns no match — so no header claim is falsified by the build and no edit was owed. The H1 companion pointer at `:3` resolves to a file that exists on disk.

### Review outcome

`final-accepted`.

## Post-acceptance correction (Worker 0, 2026-08-14, after hand-off)

**The correction.** Two places in this file said the git-ignored `.claude/` memory file that fails an unscoped `check_trailing_commas --check` belonged to **another session**. It does not. It is `.claude/projects/-Users-riordenweber-projects-django-strawberry-framework/memory/one-spec-owns-each-feature.md`, written by **Worker 0 in this cycle** at `10:19` to record the maintainer's single-ownership law — the same law `build-006-…md` `## The single-ownership law` quotes and Maintainer decision 1 executes. Both sites are now marked in place, and the catalog row is withdrawn as a maintainer item: **`### Deferred work catalog`'s maintainer-owned count is two, not three.**

**How it happened, since the mechanism is the reusable part.** R3 ran the checker *unscoped* on its own initiative — the plan authorizes a scoped run over the files a pass writes, and its scoped run was green (`exit 0`, quoted above). The unscoped run returned exit 1 on a path under `.claude/`, and R3's rules say report-never-tidy, so it reported. In reporting it, R3 inferred ownership from the path's directory rather than deriving it (`bld-006-r3:1070`), and this gate carried the inference forward under its own "re-derived rather than inherited from R3's hand-off" heading — which is the sharper failure: the *finding* was re-derived (the tool output is reproduced verbatim, and it reproduces today), the *attribution clause attached to it* was not. **This is a sixth instance of the class the plan's `### Corrections to Worker 0's own instruments` names "right substance, loose citation", and the first where the loose half sat inside a sentence claiming re-derivation.** The countermeasure that section states covers it exactly: re-derive the citation, not just the substance — and "re-derived" as a label must scope to every clause it stands over, not to the headline measurement alone.

**What is left standing deliberately.** `bld-006-r3-doc_completion_archive.md:1070` is **not edited**: it is a closed item's artifact and this gate's own `### Spec changes made (Worker 1 only)` records that no artifact of a closed item was written. It is named here so a reader who greps the origin finds the correction, which is the same shape the cycle used for R2's superseded `:17` wording — the earlier record stands as what that pass believed, the later section carries the fact.

**The one durable observation the finding actually supports**, which the withdrawn row buried under a false attribution: **an unscoped `scripts/check_trailing_commas.py --check` walks git-ignored paths, so any agent scratch under `.claude/` makes a tree-wide run exit 1 on a file no commit can contain.** Re-derived this pass: the run still reports exactly `1 layout violation(s)` and still exits `1`, while `.pre-commit-config.yaml`'s `source-layout` hook is unaffected by construction because pre-commit passes it staged paths and this path can never be staged. No repository file is implicated. Options, none urgent and none taken here: leave it and only ever run the checker scoped (the pre-commit hook is the real gate); or teach the walker to skip git-ignored paths via `git check-ignore`, which is a `scripts/` change and therefore a card, not a drive-by. **Recorded rather than routed** — it is a papercut for a future agent reading a red exit as a defect, not work this cycle owes anyone.

**Status is unchanged: `final-accepted`.** No gate result, no measurement, and no other catalog row is affected; this correction removes an obligation rather than adding one.

## Catalog routing, enacted on the board (Worker 0, 2026-08-14, after hand-off)

`### Deferred work catalog` above lists each deferral with an owner. The owners are now **written onto the owning card** rather than living only in this artifact, which closes the gap the catalog's own preamble names — a per-cycle artifact closes with its cycle, and a routing recorded only here is lost with it. All writes were ORM `.save()` on `TODO-ALPHA-052-0.1.0`, followed by both renderers; `docs/GLOSSARY.md` is byte-identical and was not regenerated into a change.

| Catalog item | Enacted as | Row |
|---|---|---|
| `DjangoSchema` fourth site; entry granularity; the `views` / `routers` / `middleware.debug_toolbar` group listings | one appended passage on the card's existing glossary-completeness bullet, keeping all three as the editorial calls they are | `CardItem` pk **1240**, 671 → 1,551 bytes |
| The duplicate-check tokenizer rule; the shingle-overlap control number | **defect (e)** on the card's spec/rationale-consistency-checker bullet, beside slugger defects (a)-(d), plus the control-pair requirement | pk **1259**, 2,022 → 3,164 bytes |
| The four plan evidence-formula defects; the four scratchpad record corrections | **measurement (c)** on the card's builder-corpus bullet, stated as the *right substance, loose citation* class with the re-derivation-scope countermeasure | pk **1325**, 1,253 → 2,709 bytes |
| L1 — the ASCII-hyphen citation | **fixed, not deferred.** The quoted heading is now the stem `` `## The discharged deferral` ``, which greps to the file on disk | pk **1260**, one string replaced |
| The unscoped `check_trailing_commas` walk (as corrected above) | a **new scope bullet**, filed with the card's other doc-tooling script defects | pk **1340**, `order` 23, new |

**Two catalog rows are withdrawn as discharged rather than routed**, both verified at this pass rather than assumed: the `docs/README.md` obligations (D3/D5/D8/D17) — `grep` confirms no `## Current surface` and no `## Package architecture` heading exists, spec-006's side was closed by R2 removing the structural claim, and `bld-007-final.md` reads `Status: final-accepted`, so no cycle is left holding them; and the `**Shipped today**` section-scope stamp — `docs/README.md:97` reads ``**Shipped today** (`0.0.14`)``, which conforms under the rule R2 settled, so there was never a non-conformance to export.

**One row is deliberately left uncarded: the five committed `docs/review/rev-*.md`.** It is a git decision on another session's working tree, not a unit of work — `KANBAN.md`'s only `docs/review` mention (`:375`) is an unrelated deliberate-no-op note — and carding it would invite a future sweep to "fix" it with exactly the `git checkout` both `AGENTS.md` rule 34 and this cycle refused. It stays the maintainer's, with the file list as updated in `### Fourth through ninth growth events` of the plan.

**Verification of the writes.** `iterdump()` semantic diff, never file bytes: exactly four `kanban_carditem` rows modified (1240, 1259, 1260, 1325), one created (1340) with its `kanban_uuidmodel` side-row present — which is the proof the `post_save` hook fired and therefore that no queryset `.update()` was used — and the `sqlite_sequence` bump, `+2` rows net. **No concurrent writer's row is in the diff.** `KANBAN.md` shows exactly five changed/added lines (`:314`, `:318`, `:319`, `:329`, `:334`) and `KANBAN.html` one (`:97`, the embedded data block); both proved byte-stable across two consecutive regenerates. `import_spec_terms --check` → `OK: 49 done cards have glossary links.`; `check_spec_glossary` on spec-006 → `OK: 7 terms`; `check_trailing_commas --check KANBAN.md docs/GLOSSARY.md` → exit 0. `is_complete` remains `False` on all five rows; no card was moved and no status flipped.

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
