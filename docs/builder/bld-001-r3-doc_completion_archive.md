# Build: R3 — Documentation completion and archive audit for spec-001

Spec reference: `docs/SPECS/spec-001-django_types-0_0_1.md` (whole file; 44,596 bytes measured at this
pass's open, `wc -c`) plus its companions `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`
(62,465 bytes) and `docs/SPECS/appx/spec-001-django_types-0_0_1-terms.csv`
Build plan: `docs/builder/build-001-django_types-0_0_1.md` (residual item R3)
Status: final-accepted

**R3 runs the full unmodified chain.** Unlike R1 and R2 — which the build plan's Deviation 3 collapses
to Worker 1 + Worker 3 because their whole deliverable is spec mutation — R3 has real Worker 2 work
(durable consumer-facing docs, and DB-plus-regenerate work if the audit finds drift in a generated
doc). So `Status: planned` here means **dispatch Worker 2**, and the chain is
Worker 1 (plan) -> Worker 2 (build) -> **Worker 1 (spec-002 pointer pass)** -> Worker 3 (review) ->
Worker 1 (final verification). The interstitial Worker 1 pass is declared in
`### Ownership partition inside R3` below, before dispatch, so Worker 0 dispatches it rather than
improvising it and so Worker 3 reviews one combined diff.

---

## Plan (Worker 1)

### Spec status-line re-verification

Re-read `docs/SPECS/spec-001-django_types-0_0_1.md` lines 1-12 at this pass's open. Confirmed for the
fourth time in this cycle: **there is no status/header block.** Line 1 is `# Spec: DjangoType
Foundation`, line 2 blank, line 3 `## Problem statement`, line 7 `## Prior art` (R2's retitle). There
is no target-release, status, owner, or predecessor line for this build to have falsified, and R3
deletes no predecessor doc a header could point at. No edit owed.

Two consequences for R3 specifically, both stated so no later pass re-derives them:

- The spec is **not** in R3's Worker 2 write set at all, so the 21-anchor constraint is only re-owed if
  a Worker 1 pass edits spec-001 for some reason it does not currently have.
- R2's `## Prior art` retitle is cited by the rationale's `#prior-art` in-page anchor. Nothing in R3
  may reword that heading.

### Measured baseline at this pass's open

Every number below was produced by the command beside it, at planning time, and is a baseline for
Worker 2 to re-derive rather than inherit.

| Fact | Value | Command |
|---|---|---|
| HEAD | `fdfb711f` | `git rev-parse --short HEAD` |
| `check_spec_glossary.py --spec …spec-001…` | `OK: 21 terms …`, exit 0 | as written |
| `import_spec_terms --check` | `OK: 49 done cards have glossary links.`, exit 0 | as written |
| Terms CSV | 21 data rows, **21 distinct anchors**, no duplicate anchor | `csv.DictReader` over the CSV |
| Spec anchor budget | 21 distinct anchors / 22 body links (`configurationerror` the only double) | `grep -o '\]\[glossary-[a-z0-9_-]*\]' … \| sort \| uniq -c` |
| `Card.objects.get(number=1)` | `DONE-001-0.0.1`, `done`, `0.0.1`, `DjangoType core foundation` | fakeshop ORM, read-only |
| `SpecDoc.path` for card 1 | `docs/SPECS/spec-001-django_types-0_0_1.md`, exists on disk | fakeshop ORM, read-only |
| `card.glossary_links.count()` | 21 | fakeshop ORM, read-only |
| `docs/TREE.md` | up to date | `uv run python scripts/build_tree_md.py --check` |
| Spec + rationale link defs | 22/22 and 18/18 used, 0 undefined, 0 orphan, 0 broken on-disk paths, 0 inline cross-file links | scratch script over both files |
| `SCALAR_MAP` | **26 entries**; no `DurationField`, no `BinaryField` | `ast` walk of `types/converters.py` |
| `FIELD_OUTPUT_TYPE_MAP` | 2 entries (`ImageField`, `FileField`) | same walk |
| Staged anchors | **1 occurrence**, and it is this plan's own checklist line | `grep -rEn 'TODO\(spec-001\|TODO-(ALPHA\|BETA\|STABLE)-001' .` |

### Working-tree baseline, re-measured (concurrent session)

`git status --porcelain` at this pass's open — **the set moved again since R2 closed** (`SECURITY.md`
and `uv.lock` are back, `docs/spec-049-…` is still there):

```
 M KANBAN.html          <- concurrent (spec-049 card wrap)
 M KANBAN.md            <- concurrent (spec-049 card wrap)
 M SECURITY.md          <- concurrent
 M TODAY.md             <- concurrent, ONE line (see attribution below)
 M docs/GLOSSARY.md     <- concurrent (spec-049 card wrap)
 M docs/spec-049-dependency_ci_hardening-0_0_14.md   <- concurrent
 M examples/fakeshop/db.sqlite3                      <- concurrent
 M uv.lock                                           <- concurrent
 M docs/SPECS/spec-001-django_types-0_0_1.md         <- THIS CYCLE (R1 + R2)
?? docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md   <- THIS CYCLE (R1 + R2)
?? docs/builder/bld-001-r1-rationale_move.md                  <- THIS CYCLE
?? docs/builder/bld-001-r2-spec_reconciliation.md             <- THIS CYCLE
?? docs/builder/build-001-django_types-0_0_1.md               <- THIS CYCLE
```

**Semantic attribution performed at plan time, not inferred** (`BUILD.md` `### Tracked binary /
generated files: churn and concurrent-writer handling`, `AGENTS.md` rule 34). Nothing below is
reverted, and Worker 2 re-measures `git status` at its own open because this set has moved five times
in this cycle:

- `docs/GLOSSARY.md` — `git diff` is **exactly +2 lines**, both inside the `Hard dependency` entry,
  about the declared Django / Strawberry version floors. That is the spec-049 dependency-floor surface.
  **Not spec-001 drift.**
- `KANBAN.md` — `git diff --stat` is `78 insertions / 66 deletions`; the head of the diff is
  `Last refreshed: 2026-08-06 -> 2026-08-07` and `48 of 67 cards done -> 49 of 67`. That is the
  `DONE-049-0.0.14` card wrap. **Not spec-001 drift.**
- `TODAY.md` — `git diff --stat` is **one line changed**, at line 381, rewording the Channels-router
  bullet's card reference from `065` to `DONE-046`. That is the concurrent session's renumber cleanup.
  **The `## Package scalar conversions` region R3 must fix is untouched by it** — proven positively:
  `git show HEAD:TODAY.md | grep -n 'DurationField\|BinaryField'` returns lines **157** and **162**,
  identical to the working copy. So Worker 2's edit there lands on tracked content the concurrent
  session is not writing, and produces a mixed diff the maintainer reconciles at commit.
- `KANBAN.html`, `SECURITY.md`, `uv.lock`, `docs/spec-049-…`, `examples/fakeshop/db.sqlite3` — the same
  concurrent cycle. R3 writes none of them unless the audit finds real DB-backed drift (below).

**R3 may not read a dirty generated doc as evidence of spec-001 drift**, and may not verify any
DB-backed work of its own by "`git diff` is clean". The verification for that case is named in step 7.

### What R3 is, restated from the maintainer's framing

*"When finished the documentation needs to be finished and then the spec needs to be archived."* The
archive **already landed** before this cycle opened, and every leg of it re-verified green at plan time
(table above): the spec is at `docs/SPECS/`, the terms CSV and R1's new rationale at `docs/SPECS/appx/`,
`SpecDoc.path` already reads the archived path, both `KANBAN.md` references already resolve, and every
link definition inside both moved files resolves at its archived depth. **R3 is therefore a
documentation-completion and archive-audit item, not a move.** It fixes what it finds.

The single highest-value axis is not the archive at all. R2 corrected consumer-visible facts *in the
spec*; the question nobody in this cycle has asked is whether the same facts are wrong **where a
consumer actually reads them**. Plan-time verification says they are, in two places (Findings F1 and
F2 below), and both are files no pass in this cycle has checked.

### Findings already verified at plan time — Worker 2 fixes these, it does not re-discover them

Worker 2 still re-derives each against source (`BUILD.md` `## Claims are proven mechanically`), but the
sweep that found them has run, so the build pass starts from a real target rather than an open question.

#### F1 — `TODAY.md` promises two scalar conversions the package refuses

`TODAY.md` `## Package scalar conversions`:

- Line 157: ``- `DateTimeField` / `DateField` / `TimeField` / `DurationField` -> Python-native time
  types  *(products: `created_date` / `updated_date`)*``
- Line 162: ``- `BinaryField` -> `bytes` ``

Both are false at HEAD. `django_strawberry_framework/types/converters.py::SCALAR_MAP` has **26 entries**
(`ast` walk) and neither `models.DurationField` nor `models.BinaryField` is among them; both raise the
unsupported-field-type `ConfigurationError`. The module's own docstring states it
(`types/converters.py` #"Notably absent from the default map"), `docs/GLOSSARY.md` states it correctly
at its `Scalar field conversion` entry, `CHANGELOG.md` records the removal as a breaking change, and
`tests/types/test_converters.py::test_convert_scalar_duration_field_raises_unsupported` /
`::test_convert_scalar_binary_field_raises_unsupported` pin it. This is the exact fact R2 corrected in
the spec as drift row D17 and every pass in this item has seconded — five times before this plan.

`TODAY.md` is a **consumer-facing capability snapshot and is not generated**, so this is a direct file
edit, and it is **in R3's scope**, not a maintainer follow-up: the file is tracked, the region is not
what the concurrent session is writing (attribution above), and R2's handoff assigned the check here by
name. The correction must not merely delete the two promises — a consumer whose model declares one of
these columns needs to know it raises and what the documented plug is, which is what the glossary entry
and the converter docstring already say and what the spec now says.

#### F2 — `docs/README.md` lists `binary` among the shipped scalar conversions

`docs/README.md` `## Today and coming next`, the `**Shipped today** (`0.0.14`)` list, line 99:

> `- scalar conversion (text, integer, boolean, float, decimal, date/time, UUID, binary, choice enums; …)`

`binary` is the same falsified promise as F1, in the package's primary consumer-facing documentation
entry point. `docs/README.md` is hand-authored (not one of the three DB-rendered docs) and is **clean in
`git status`**, so Worker 2 edits it directly with no attribution hazard. `README.md` at the repo root
carries **zero** `Duration` / `Binary` occurrences (measured), and `GOAL.md` carries zero, so neither is
implicated by this finding — which is itself a result to record, not an absence to leave unstated.

### Ownership partition inside R3

The build plan declares `Ownership partition: none; sequential residual items` for the cycle. **Within
R3 there is a role partition that is not a cohort partition**, and it is load-bearing because R3 is the
first residual item with a real Worker 2:

**Worker 2 owns (and Worker 2 must never edit a spec file):**

- `TODAY.md` — F1.
- `docs/README.md` — F2 and the rest of the durable-doc audit's findings in that file.
- `README.md`, `GOAL.md` — audit; edit only if the sweep finds a falsified spec-001-surface claim.
- The **read-only** verification legs: the three-direction archive sweep, the terms-CSV /
  `SpecDoc.path` / `glossary_links` checks, both constraint commands, and the staged-anchor sweep.
- **DB-backed work, if and only if the audit finds real drift** in `docs/GLOSSARY.md`, `KANBAN.md`, or
  `KANBAN.html`: an ORM edit against `examples/fakeshop/db.sqlite3` followed by a regenerate. Never a
  hand-edit of the rendered file (`BUILD.md` `### Generated docs are DB-backed`).
- `docs/TREE.md`: never hand-edited. If `--check` reports drift, the fix is the **feeding module
  docstring** plus a regenerate, in the same change (`START.md` "Rendered docs — fix the source, not
  the file"). A docstring edit is the one package-source touch R3 may make, and only for a factually
  false or staging-language docstring — the build plan's build-wide context flags authorize exactly
  that and nothing wider.

**A Worker 1 pass owns (Worker 2 may not touch these under any finding):**

- `docs/SPECS/spec-002-optimizer-0_0_2.md` — obligations C1/C2/C3 below. `spec-002` is a **spec file**;
  `BUILD.md` `## Spec reconciliation` and `worker-1.md` `## Scope` make Worker 1 the only role that may
  mutate one. This is the assignment that gets mis-routed if it is not stated, precisely *because* R3
  has a real Worker 2.
- `docs/SPECS/spec-001-django_types-0_0_1.md` and
  `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` — not expected to change in R3 at all, but
  if the audit turns up something that must, it is a Worker 1 edit and re-owes both constraint commands.

**When the Worker 1 pass happens:** Worker 0 dispatches it **after** Worker 2 sets `Status: built` and
**before** Worker 3's review. Worker 1 appends a `## Spec-002 pointer pass (Worker 1)` section to this
artifact, ticks boxes C1-C3, records its edits under `### Spec changes made (Worker 1 only)`, and leaves
`Status: built` untouched so Worker 3 reviews one combined R3 diff. Doing it at final verification
instead would leave the spec edit unreviewed; doing it before the build pass would split the review the
other way.

### DRY analysis

**Helper inventory checked.** Refreshed **for the whole package** at this pass, not scoped to `utils/`:
the `worker-1.md` `### Package-wide helper inventory before helper planning` AST command was re-run over
`django_strawberry_framework/` on 2026-08-06, emitting **1,782 lines** to `docs/shadow/helper-inventory.md`
(gitignored). Shapes searched, per the rule's "grep it for the shapes this slice needs": `scalar`,
`duration`, `binary`, `convert`, `doc`. The relevant hits are all *readers* of the single source of
truth rather than candidates for a new helper — `forms/converter.py::_scalar_from_model_field` ("Map a
Django model field to its scalar via the shared `SCALAR_MAP` lookup"),
`management/commands/inspect_django_type.py::_matched_scalar_key` ("Name the `SCALAR_MAP` entry (the MRO
ancestor) that fired"), and the `Command._scalar_row` / `_render_strawberry_type` rendering pair. **No
new helper is in prospect and none is justified**: R3 writes no `.py` file and plans none. The inventory
still ran rather than being skipped, for one reason worth stating — it is what establishes that
`SCALAR_MAP` is the package's *single* scalar-mapping source, which is the fact the doc corrections are
measured against. Had a second, divergent map existed, F1 and F2 would have been ambiguous instead of
settled.

- **Existing patterns reused.** Three, none of them code:
  1. The **`SCALAR_MAP`-as-single-source** rule above. Every doc statement about a scalar mapping is
     re-derived from `django_strawberry_framework/types/converters.py::SCALAR_MAP` and
     `::FIELD_OUTPUT_TYPE_MAP` by `ast`, never from another document. Doc-to-doc copying is exactly how
     `TODAY.md` and `docs/README.md` came to disagree with the package in the first place.
  2. The **wording already in the two correct documents.** `docs/GLOSSARY.md`'s `Scalar field
     conversion` entry and `types/converters.py`'s module docstring both already state the
     `DurationField` / `BinaryField` absence *and* the documented plug
     (`SCALAR_MAP[BinaryField] = strawberry.scalars.Base64`, a consumer-defined scalar for duration).
     `TODAY.md` and `docs/README.md` adopt that framing rather than inventing a third phrasing.
  3. The **reference-style link convention** (`START.md` "Markdown link convention") for any new
     cross-file link, with the 10 canonical group headers already present in both target files.
- **New helpers justified.** None — no source, no test, no script. R2's final verification catalogued a
  *sixth* hand-written link/anchor checker as a standing cost and ruled promoting one to `scripts/` new
  scope and a maintainer call. R3 does not open it either. Worker 2 may write a throwaway checker under
  `docs/builder/temp-tests/` (gitignored) and must not add one to `scripts/`.
- **Duplication risk avoided.** Three, all real here:
  1. **Re-stating the spec's contract in a durable doc.** `TODAY.md` and `docs/README.md` are capability
     snapshots, not contract documents. The correction states the shipped behavior and, where a reader
     needs the full rule, points at `docs/GLOSSARY.md`'s existing anchor — never a second copy of the
     spec's scalar table, which would be the same failure one generation later.
  2. **A fourth copy of the `DurationField` / `BinaryField` explanation.** It is currently in the
     converter docstring, the glossary entry, `CHANGELOG.md`, and the spec. `TODAY.md` and
     `docs/README.md` get the *fact plus a pointer*, not the reasoning.
  3. **Hand-editing a generated doc.** A `docs/GLOSSARY.md` / `KANBAN.md` / `KANBAN.html` /
     `docs/TREE.md` fix that is not an ORM-or-docstring edit plus a regenerate is a duplication of the
     generator's output that the next render silently deletes.

### Implementation steps

Pin-at-write-time. Line numbers are from the working tree at this pass's open and must be re-verified —
the concurrent session is writing `TODAY.md`.

1. **Re-measure `git status --porcelain` and re-attribute** before touching anything. The set has moved
   five times in this cycle. Record what came back; do not quote this plan's snapshot as current.
2. **Re-derive F1 and F2 against source**, not against this plan: `ast`-walk
   `django_strawberry_framework/types/converters.py::SCALAR_MAP` and `::FIELD_OUTPUT_TYPE_MAP` and list
   the entries. State the entry count you measured.
3. **Fix `TODAY.md` `## Package scalar conversions`** (F1): line 157's `DurationField` term and line
   162's whole `BinaryField` bullet. Land the shipped fact — both are absent from the default map and
   raise `ConfigurationError` — with the documented consumer plug, in the framing
   `docs/GLOSSARY.md`'s `Scalar field conversion` entry already uses. Do not touch line 381 or any other
   region of the file.
4. **Fix `docs/README.md` line 99** (F2): remove `binary` from the shipped scalar-conversion list and,
   if the entry warrants it, say where the absence is documented. Keep the sentence's existing shape;
   this is a correction, not a rewrite.
5. **Sweep `TODAY.md`, `docs/README.md`, `README.md`, and `GOAL.md` for every other spec-001-surface
   claim R2 falsified** — the D1-D18 set is the checklist, and the shortest distinctive token is the
   search unit, not a long phrase (`BUILD.md` `## Claims are proven mechanically`). Named starting
   points, each re-derived against the symbol given: flat module layout `types.py` / `converters.py` /
   `optimizer.py` (D1, vs the `types/` and `optimizer/` packages); `lazy_ref` on the registry (D2, vs
   `registry.py::TypeRegistry`); definition-order dependence (D3, vs
   `registry.py::TypeRegistry.add_pending_relation` and `types/finalizer.py::finalize_django_types`);
   `filterset_class` / `orderset_class` as deferred keys (D4, vs `types/base.py::DEFERRED_META_KEYS`);
   `Meta.interfaces` unwired (D5, vs `types/relay.py::apply_interfaces`); one-type-per-model registration
   (D6, vs `registry.py::TypeRegistry.register`); `FileField` / `ImageField` -> `str` on the read side
   (D8, vs `types/converters.py::FIELD_OUTPUT_TYPE_MAP`); `PositiveBigIntegerField` -> `int` (D16, vs
   `SCALAR_MAP`). Report the sweep's result **including the zeros** — an unstated absence is
   indistinguishable from an unrun check.
6. **Audit `docs/TREE.md`.** Run `uv run python scripts/build_tree_md.py --check` and record the output
   (it read `up to date` at plan time). If it drifts, or if a spec-001-surface module docstring carries
   staging language (`planned`, `Slice N`, `TODO(`) that renders shipped behavior as unbuilt, fix the
   **docstring** and regenerate in the same change (`ARTIFACT.md` `### Documentation / release sanity`,
   last bullet). Never hand-edit the rendered tail.
7. **Audit the two DB-backed surfaces for the spec-001 record.** Read-only first:
   - `docs/GLOSSARY.md` — confirm each of the 21 anchors in
     `docs/SPECS/appx/spec-001-django_types-0_0_1-terms.csv` resolves to a real `## ` heading and that
     the entry describes shipped behavior. `check_spec_glossary.py` proves the *heading exists*, not
     that the prose is true; the second half is a read.
   - `KANBAN.md` card `DONE-001-0.0.1` (rendered at `KANBAN.md` line ~4901) — its `#### Scope`,
     `#### Package files` (three rows carry the `(historical)` marker, i.e. `TrackedPath.is_current =
     False`), `#### Files likely touched`, `#### Decision`, and `#### Note` blocks against the shipped
     foundation and against R2's corrected spec.

   **If either needs a change, it is an ORM edit plus a regenerate**, applied **on top** of the
   concurrent session's DB state without reverting it, and verified by **two consecutive regenerates
   producing byte-identical output** plus a spot-check of the changed rows — never by "`git diff` is
   clean", which the concurrent card wrap has already made meaningless here. Hand the mixed diff to the
   maintainer. If neither needs a change, say so explicitly and record what was read.
8. **Re-run the three-direction archive sweep** (`docs/SPECS/NEXT.md` Step 8; the build plan's
   `### Every reference TO spec-001` table is a **verification list, not a rewrite list**, and is
   re-derived rather than trusted):
   - *Direction 1, references TO spec-001.* `grep -rn 'spec-001'` across the repo excluding `.git`,
     `dist`, and the per-cycle scratch dirs. Plan-time result, for Worker 2 to reproduce or correct:
     `KANBAN.md:146` and `:4908` (generated, both resolving to `docs/SPECS/spec-001-django_types-0_0_1.md`);
     `docs/SPECS/spec-002-optimizer-0_0_2.md:9`, `:56`, `:57`, `:80`;
     `docs/SPECS/spec-005-django_type_contract-0_0_3.md:5`, `:107`, `:109`, `:122`;
     `docs/SPECS/spec-006-public_surface-0_0_3.md:134`;
     `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md:6`, `:86`, `:436`, `:598`, `:645`, and the
     reference definition at `:1830`. Every sibling-spec hit is a bare filename or an inline code span
     resolving within `docs/SPECS/`; `spec-037:1830` is the only actual link definition and it resolves.
     Zero hits in `README.md`, `GOAL.md`, `TODAY.md`, `AGENTS.md`, `docs/GLOSSARY.md`, `docs/TREE.md`,
     `docs/README.md`, `CHANGELOG.md`.
   - *Direction 2, references INSIDE the moved files.* Both spec-001 and its rationale sit deeper than
     `docs/`, so every relative target is depth-sensitive. Plan-time result: spec **22 defs / 22 used**,
     rationale **18 / 18**, 0 undefined, 0 orphaned, **0 broken on-disk paths** (each normalized-joined
     from its own file's directory and `os.path.exists`-checked), 0 inline cross-file links outside code
     fences. Re-derive; do not inherit.
   - *Direction 3, the companions.* Confirm `…-terms.csv` and `…-rationale.md` are both at
     `docs/SPECS/appx/`, that no spec-001 file or companion is stranded at the `docs/` root, and that
     the spec's own reference to its companions carries the `appx/` prefix.
9. **Verify the terms-CSV / kanban chain.** Confirm the CSV is **one row per anchor** (plan-time: 21 data
   rows, 21 distinct anchors, zero duplicates — `check_spec_glossary.py` tolerates many terms per anchor
   but `import_spec_terms` requires anchor uniqueness), that `SpecDoc.path` for card 1 reads
   `docs/SPECS/spec-001-django_types-0_0_1.md` and that the file exists on disk, and that
   `card.glossary_links.count()` is 21. Then run both constraint commands and quote them:

   ```
   uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
   uv run python examples/fakeshop/manage.py import_spec_terms --check
   ```

   **Both must exit 0.** The done-card number is **not** the gate — it read `48` when the build plan was
   written and `49` now, moved by the concurrent session's `DONE-049-0.0.14` wrap. Quote what comes back.
10. **Run the staged-anchor sweep** (`BUILD.md` `## Cross-slice integration pass` step 6, folded into R3
    by the build plan's artifact list):

    ```
    grep -rEn 'TODO\(spec-001|TODO-(ALPHA|BETA|STABLE)-001' .
    ```

    excluding `KANBAN.md` / `KANBAN.html` / `BACKLOG.md`, where `TODO-<MILESTONE>-<NNN>` legitimately
    names an unshipped board card. Plan-time result: **1 occurrence**, and it is
    `docs/builder/build-001-django_types-0_0_1.md`'s own checklist line describing this sweep — a
    per-cycle artifact, not shipped source. Zero anchors in package source, tests, or `examples/`. Report
    the occurrence count you measure, not matching lines.
11. **Format and validate.** `uv run python scripts/check_trailing_commas.py --check <the .md files this
    pass touched>` and `git diff --check` over the same set. No `ruff` unless a `.py` docstring was
    edited under step 6, in which case `uv run ruff format` and `uv run ruff check --fix` scoped to that
    file only — never `.`, which would sweep the concurrent session's files.
12. **(Worker 1 pass, after `built`.)** Discharge the two open `spec-002` obligations — see
    `### The spec-002 obligations, quoted` below.

### The spec-002 obligations, quoted

Carried verbatim from `bld-001-r2-spec_reconciliation.md` `### Notes for Worker 1 (spec reconciliation)`
item 1, re-confirmed open at this pass (`git status` carries no `spec-002` entry; both lines re-read on
disk). **These belong to R3's Worker 1 pass, never its Worker 2.**

- **`docs/SPECS/spec-002-optimizer-0_0_2.md:9`**, `## Problem statement`, first sentence:
  *"`spec-001-django_types-0_0_1.md` predicted that the optimizer half of its scope would eventually
  warrant its own document; running the early DjangoType slice tests confirmed it."* The prediction it
  cites is spec-001's own cut-line paragraph, which **R1 moved**. It now lives only in
  `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`, under
  ``### Whole-document scope — the optimizer was bundled deliberately (former `## Scope creep into the N+1 problem`)``,
  in the paragraph *"The cut line the spec named for itself, and then took"*.
- **`docs/SPECS/spec-002-optimizer-0_0_2.md:80`**, `## References`, last bullet: *"The visibility-leak /
  `Prefetch` downgrade discussion that motivated bundling the optimizer with
  `spec-001-django_types-0_0_1.md` originally: issue #572 and PR #583 on
  `strawberry-graphql/strawberry-django`."* The bundling discussion is in the same rationale entry, under
  *"Alternative rejected — two specs in lockstep"*.
- **Minimum discharge for both is a pointer naming the rationale file, never new narration.** Neither
  reference is wrong *about spec-001*; both are wrong about **where the cited text lives**. Rewriting the
  surrounding prose is out of scope. `spec-002` uses inline code spans for spec filenames and the
  rationale is a sibling one directory down, so the pointer resolves as `appx/spec-001-django_types-0_0_1-rationale.md`.
- **The third, related obligation is CLOSED. Do not re-open it as a rule-stating duty.** Worker 3's
  Medium 2 in R2 found that two lifted optimizer rules (the O5 `only()` reason and O6's every-branch
  visibility clause) were stated nowhere; **R2 pass 2 restored both as contract in spec-001's
  `## N+1 strategy`**, re-derived against `optimizer/walker.py` rather than restored verbatim, and R2's
  final verification confirmed them present. What remains is *optional*: a **recording** that the prose
  lift happened, whose natural site is spec-002's own
  ``## Coordination with `spec-001-django_types-0_0_1.md`` heading (line 56). Since the Worker 1 pass is
  opening that file anyway, folding it in there is cheaper than a fourth pass — but it is a recording,
  not a rule, and it is the one box in this artifact that may legitimately close as "assessed, not
  needed" with that assessment written down.
- **Binding constraint for any later cycle:** if a future cycle re-homes those two rules into `spec-002`,
  it must re-home the **PR #583 carve-out** with them and delete all three from spec-001 in the same
  change. Those three are one decision; splitting them recreates the duplication R2 exists to remove.
  Durable record: the rationale's ``### `## N+1 strategy``` entry, in bold.
- Also checked and **not** affected: `spec-002:56` (the coordination heading) and `:57` (*"Slices 4-6 are
  superseded by this optimizer spec family"*), which point at spec-001's surviving slice list —
  `## Suggested implementation slices` still exists and still says exactly that, deliberately (R1 decided
  it; R2 did not re-open it). No third dangling reference exists.

### Test additions / updates

**None, and none possible.** R3 writes no `.py` file except, conditionally, a single module docstring
under step 6 — and a docstring change is covered by the existing `build_tree_md.py --check` render gate,
not by a new test. The executable checks standing in for tests are:

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md` (exit 0)
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` (exit 0)
- `uv run python scripts/build_tree_md.py --check`
- `uv run python scripts/check_trailing_commas.py --check <touched .md files>`
- `git diff --check`
- the two-consecutive-regenerate byte-stability check, **only if** a DB-backed doc is written

Temp-test opportunity for Worker 3: the link / anchor / on-disk-path checker this cycle has now
hand-written six times belongs under `docs/builder/temp-tests/r3-spec001/` (gitignored). R2's final
verification already catalogued promoting it to `scripts/` as new scope and a maintainer call; R3 does
not open that.

### Implementation discretion items

Assessed and delegated to Worker 2 — each is a shape choice between equally valid options, not an
architectural question:

- **The exact wording of the `TODAY.md` and `docs/README.md` corrections.** The constraint is fixed (the
  fact plus a pointer, in the framing `docs/GLOSSARY.md`'s `Scalar field conversion` entry already uses,
  never a fourth copy of the reasoning); the sentence is Worker 2's.
- **Whether `TODAY.md`'s two stale bullets become one combined "absent from the default map" line or stay
  as an edited line 157 plus a rewritten line 162.** Both preserve the fact and the list's shape.
- **Whether `docs/README.md` line 99 names the absence inline or leaves it to the glossary pointer** —
  the surrounding entry is already long and either reads correctly.
- **The order of the read-only verification legs** (steps 5-10). They are independent.
- **The scratch-checker's implementation** for step 8's direction-2 leg, provided it renders
  reference-link markup **before** slugging a heading — `scripts/check_spec_glossary.py::github_anchor`
  fed a raw reference-link heading returns a false negative
  (`## [Scalar field conversion][glossary-scalar-field-conversion]` ->
  `scalar-field-conversionglossary-scalar-field-conversion`). Three consecutive passes in this cycle
  copied the broken method before it was caught. The function is unchanged, so the trap is live.

Not delegated, and stated so no pass improvises: **which role edits which file** (`### Ownership
partition inside R3`), and **whether a generated doc is fixed by hand** (never).

### Boundary count, hot path, floor verification, failability

Answered here so no later pass has to guess, per `worker-1.md` `### Boundary count is a split trigger`
and `### Hot-path declaration`:

- **New runtime boundaries added by R3: zero.** R3 adds no guard, cap, rejection path, or validation
  branch — it edits Markdown and, conditionally, one module docstring and one set of DB rows. The
  slice-splitting question therefore does not arise, and **`### Failability proofs` will legally be
  empty**: the correct entry is `None; this pass introduced no new boundary.` Worker 2 keeps the heading
  and writes that line rather than omitting the section or inventing a proof.
- **Hot path: none.** The build plan declares `Hot-path declaration: none` for the whole cycle and R3
  changes nothing that runs per request, per resolver, per row, per connection, or per outbound message.
  Worker 2 writes `Not applicable; plan declares no hot path.`
- **Floor verification: none.** The build plan declares `Floor-verification scope: none`; R3 touches no
  Django / Strawberry / channels integration seam. Worker 2 writes `Not applicable; plan declares
  floor-verification scope none.`

### Dispatched findings checklist

R3 is neither a spec slice (spec-001's slices shipped at `0.0.1`) nor a review round, so there is no
`## Slice checklist` to copy verbatim. Per `BUILD.md` `### Dispatched findings checklist`, that is the
named substitute in this position. One box per audit obligation. **Boxes stay `- [ ]` at planning.**
Worker 2 ticks **only** what lands in its own diff; the C-boxes are the Worker 1 pass's to tick; a
verification obligation with a clean result is discharged by recording the measurement in the build
report and ticking the box. Worker 3 walks the list; Worker 1 re-audits every tick at final verification.

**A — durable-doc audit (Worker 2)**

- [x] **A1** — *"`DateTimeField` / `DateField` / `TimeField` / `DurationField` -> Python-native time
      types"* and *"`BinaryField` -> `bytes`"* are false at HEAD; both column types raise
      `ConfigurationError`. Fix `TODAY.md` `## Package scalar conversions` (lines 157, 162) against
      `django_strawberry_framework/types/converters.py::SCALAR_MAP` and the module docstring
      #"Notably absent from the default map".
- [x] **A2** — *"scalar conversion (text, integer, boolean, float, decimal, date/time, UUID, **binary**,
      choice enums; …)"* lists a conversion the package refuses. Fix `docs/README.md`
      `## Today and coming next`, the `**Shipped today**` list (line 99), against the same symbols.
- [x] **A3** — every remaining scalar / file-output claim in `TODAY.md` `## Package scalar conversions`
      and `docs/README.md`'s shipped list re-derived against
      `django_strawberry_framework/types/converters.py::SCALAR_MAP` (26 entries) and
      `::FIELD_OUTPUT_TYPE_MAP` (2 entries), with the measured entry counts stated and the zeros reported.
- [x] **A4** — `TODAY.md`, `docs/README.md`, `README.md`, `GOAL.md` swept for every other
      spec-001-surface claim R2's drift rows falsified (D1-D18), each re-derived against the symbol
      named in `### Implementation steps` step 5, not against this plan. Absences reported explicitly.
- [x] **A5** — `docs/TREE.md` re-verified with `uv run python scripts/build_tree_md.py --check`
      (`up to date` at plan time). Any drift fixed at the feeding module docstring plus a regenerate in
      the same change (`scripts/build_tree_md.py`), never by hand-editing the rendered tail.
- [x] **A6** — `docs/GLOSSARY.md` audited for the spec-001 surface: each of the 21 anchors in
      `docs/SPECS/appx/spec-001-django_types-0_0_1-terms.csv` resolves to a real `## ` heading **and**
      the entry describes shipped behavior. Any fix is an ORM edit against
      `examples/fakeshop/db.sqlite3` plus `scripts/build_glossary_md.py`, applied on top of the
      concurrent state, verified by two-consecutive-regenerate byte-stability.
- [x] **A7** — `KANBAN.md` card `DONE-001-0.0.1` audited (`#### Scope`, `#### Package files` and its
      three `(historical)` rows, `#### Files likely touched`, `#### Decision`, `#### Note`) against the
      shipped foundation and R2's corrected spec. Any fix is an ORM edit plus
      `scripts/build_kanban_md.py` + `scripts/build_kanban_html.py`, same verification rule.

**B — archive audit, all three cross-reference directions (Worker 2, read-only unless a fix is needed)**

- [x] **B1** — *direction 1, references TO spec-001*: the sweep re-run rather than trusted from the build
      plan's table, covering `KANBAN.md`, `docs/SPECS/spec-002-optimizer-0_0_2.md`,
      `docs/SPECS/spec-005-django_type_contract-0_0_3.md`,
      `docs/SPECS/spec-006-public_surface-0_0_3.md`,
      `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md`, and the confirmed-zero set
      (`README.md`, `GOAL.md`, `TODAY.md`, `AGENTS.md`, `docs/GLOSSARY.md`, `docs/TREE.md`,
      `docs/README.md`, `CHANGELOG.md`).
- [x] **B2** — *direction 2, references INSIDE the moved files whose relative depth changed*: every link
      definition in `docs/SPECS/spec-001-django_types-0_0_1.md` and
      `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` resolved on disk from its own file's
      directory, with undefined / orphan refs and inline cross-file links both zero.
- [x] **B3** — *direction 3, the companions*: `docs/SPECS/appx/spec-001-django_types-0_0_1-terms.csv` and
      `…-rationale.md` both at `docs/SPECS/appx/`, nothing spec-001-related stranded at the `docs/` root,
      and the spec's own companion reference carrying the `appx/` prefix (`AGENTS.md` rule 26).
- [x] **B4** — the terms CSV is **one row per anchor** (21 rows / 21 distinct anchors at plan time) and
      importable: `scripts/check_spec_glossary.py --spec …spec-001…` and
      `examples/fakeshop/manage.py import_spec_terms --check` both quoted and both exit 0. The done-card
      number is not the gate.
- [x] **B5** — `SpecDoc.path` for card 1 reads `docs/SPECS/spec-001-django_types-0_0_1.md` and the file
      exists on disk; `Card.objects.get(number=1)` is `DONE-001-0.0.1` / `done` / `0.0.1`;
      `card.glossary_links.count()` is 21. (`SpecDoc.url` is a read-only `@property` deriving from
      `path` — assigning to it raises.)

**C — the two open `spec-002` obligations (Worker 1 pass only; Worker 2 must not touch this file)**

- [x] **C1** — `docs/SPECS/spec-002-optimizer-0_0_2.md:9`: *"`spec-001-django_types-0_0_1.md` predicted
      that the optimizer half of its scope would eventually warrant its own document; running the early
      DjangoType slice tests confirmed it."* The cited prediction now lives only in
      `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`. Minimum discharge: a pointer naming the
      rationale file. Never new narration.
- [x] **C2** — `docs/SPECS/spec-002-optimizer-0_0_2.md:80`: *"The visibility-leak / `Prefetch` downgrade
      discussion that motivated bundling the optimizer with `spec-001-django_types-0_0_1.md` originally:
      issue #572 and PR #583 on `strawberry-graphql/strawberry-django`."* Same rationale entry, same
      minimum discharge.
- [x] **C3** — the optional *recording* that R2's prose lift happened, at
      ``docs/SPECS/spec-002-optimizer-0_0_2.md`` `## Coordination with `spec-001-django_types-0_0_1.md``
      (line 56). **This is a recording, not a rule-stating duty — the two lifted optimizer rules are
      already contract in spec-001's `## N+1 strategy` and that obligation is CLOSED.** May close as
      "assessed, not needed" provided the assessment is written down.

**D — staged-anchor sweep (Worker 2)**

- [x] **D1** — `grep -rEn 'TODO\(spec-001|TODO-(ALPHA|BETA|STABLE)-001' .` run over the tree, excluding
      `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` where `TODO-<MILESTONE>-<NNN>` legitimately names an
      unshipped board card (`BUILD.md` `## Cross-slice integration pass` step 6). Occurrences counted,
      not matching lines. Plan-time result: 1, and it is
      `docs/builder/build-001-django_types-0_0_1.md`'s own description of this sweep — a per-cycle
      artifact, not shipped source. Any anchor found in package source, tests, or `examples/` is
      `revision-needed`.

### Notes for Worker 2

- **You may not edit any spec file.** `docs/SPECS/spec-002-optimizer-0_0_2.md`,
  `docs/SPECS/spec-001-django_types-0_0_1.md`, and
  `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` are all Worker 1's. If your audit finds
  something wrong in one, record it under `### Notes for Worker 1 (spec reconciliation)` — that is the
  hand-over, and this cycle has already watched an unowned recommendation die in an artifact.
- **Never `git checkout`, `git restore`, or `git stash` anything.** The tree carries a concurrent
  session's uncommitted work across eight paths. Unexpected churn is a stop-and-report, never a tidy-up.
- **Scope every write-mode tool run to your own files.** `uv run ruff format .` would sweep the
  concurrent session's work; the same goes for `check_trailing_commas.py` without an explicit file list.
- **Count occurrences of the shortest distinctive token, never matching lines, and measure as you write
  the number.** This cycle has lost ten asserted counts across R1 and R2 to re-derivation; it is its
  dominant practice failure and several of the losses sat beside the lesson they illustrated.
- The `## Prior art` heading in spec-001 and the `## [Scalar field conversion][glossary-…]` heading are
  both cited by in-page anchors elsewhere. Nothing in R3 rewords either.

### Notes for Worker 3

- **The sharpest question for this round is completeness, not correctness.** R3's fixes are small and
  mechanically checkable; what it can silently get wrong is *stopping too early*. Re-run the sweeps
  yourself — particularly A4 (the D1-D18 sweep across four consumer-facing docs) and B1 — and treat a
  reported absence with no stated command as an unrun check.
- **Re-derive F1 and F2 from source.** `ast`-walk `SCALAR_MAP` yourself; do not accept "26 entries, no
  `DurationField`" from this plan or from the build report.
- **Attribution before conclusion, in both directions.** A generated-doc diff is most likely the
  concurrent spec-049 session's; a `TODAY.md` diff at line 381 certainly is. Conversely, a *missing*
  correction cannot be excused as concurrent-session territory — lines 157/162 are tracked content the
  concurrent diff does not touch, proven against `git show HEAD:TODAY.md`.
- If Worker 2 wrote any DB-backed doc, the acceptance evidence is **two consecutive regenerates producing
  byte-identical output plus spot-checks**, never a clean `git diff`.

### Notes for Worker 1 (spec reconciliation)

Carried into R3's final verification and the final gate.

1. **The Worker 1 spec-002 pass is a dispatch obligation, not a final-verification chore.** It runs
   between `built` and the review. If Worker 0 dispatched Worker 3 without it, the C-boxes are un-ticked
   and unreviewed and the item is `revision-needed`.
2. **The anchor constraint is unchanged and re-measured at this pass: 21 distinct anchors / 22 body
   links**, `configurationerror` the only anchor with two. R3 touches no spec-001 prose by its own scope;
   any spec-001 or rationale edit made for any reason re-owes both constraint commands.
3. **`import_spec_terms --check` reads `OK: 49 done cards`, exit 0.** The number moves with the
   concurrent session. **Exit 0 is the contract.**
4. **For the final gate's `### Deferred work catalog`**, two items are already on record from R2 and are
   not R3's to close: the optimizer-hint test-surface gap (no permanent test pins that
   `OptimizerHint.prefetch(obj)` bypasses `utils/querysets.py::apply_type_visibility_sync` when the
   target type declares a custom `get_queryset`), and the promotion of a shared link/anchor/overlap
   checker to `scripts/`. Both are out of this cycle's write set and are maintainer calls.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` re-measured after the last edit (not from memory). Two files in the
working tree are this pass's:

- `TODAY.md` — F1. Three hunks, all inside `## Package scalar conversions` and its link-definition
  block: (a) `DurationField` removed from the date/datetime/time bullet; (b) the `` `BinaryField` ->
  `bytes` `` bullet replaced by an **Absent from the default map** bullet naming both column types,
  the `ConfigurationError` they raise at type creation, the three consumer recourses, and a pointer
  to the glossary entry; (c) one new reference-link definition,
  `[glossary-scalar-field-conversion]: docs/GLOSSARY.md#scalar-field-conversion`, inserted
  alphabetically under `<!-- docs/ -->`.
- `docs/README.md` — F2. Two hunks: (a) `binary` removed from the `**Shipped today**` scalar-conversion
  list at `## Today and coming next`, with a `;`-delimited clause added in the entry's existing
  register naming both absences and pointing at the same glossary anchor; (b) the matching
  `[glossary-scalar-field-conversion]: GLOSSARY.md#scalar-field-conversion` definition, alphabetically
  placed.

**No other file was written by this pass.** In particular: no spec file, no rationale companion, no
`.py`, no test, no DB, and none of the three DB-rendered docs — the A5/A6/A7 audits came back clean, so
no ORM edit or regenerate was owed (evidence below).

`git status --short` at the close of this pass, classified:

```
 M TODAY.md          <- THIS PASS (plus the concurrent line-381 hunk, untouched)
 M docs/README.md    <- THIS PASS
 M KANBAN.html       <- concurrent (spec-049 card wrap)
 M KANBAN.md         <- concurrent (spec-049 card wrap)
 M SECURITY.md       <- concurrent
 M docs/GLOSSARY.md  <- concurrent (spec-049 card wrap)
 M docs/spec-049-dependency_ci_hardening-0_0_14.md   <- concurrent
 M examples/fakeshop/db.sqlite3                      <- concurrent
 M uv.lock                                           <- concurrent
 M docs/SPECS/spec-001-django_types-0_0_1.md         <- THIS CYCLE (R1 + R2)
?? docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md   <- THIS CYCLE (R1 + R2)
?? docs/builder/bld-001-r1-rationale_move.md                  <- THIS CYCLE
?? docs/builder/bld-001-r2-spec_reconciliation.md             <- THIS CYCLE
?? docs/builder/build-001-django_types-0_0_1.md               <- THIS CYCLE
?? docs/builder/bld-001-r3-doc_completion_archive.md          <- THIS CYCLE (this file)
```

The set is **unchanged from the plan's snapshot in membership**, with the two additions being this
pass's own. Nothing unexpected appeared; nothing was reverted, checked out, restored, or stashed.

`TODAY.md` attribution re-derived at this pass's open rather than inherited:

```
git diff --stat -- TODAY.md   ->  1 file changed, 1 insertion(+), 1 deletion(-)   [before my edits]
git show HEAD:TODAY.md | grep -n 'DurationField\|BinaryField'  ->  157, 162
grep -n 'DurationField\|BinaryField' TODAY.md                  ->  157, 162
```

The one concurrent hunk is at line 381 (`065` -> `DONE-046` in the Channels-router bullet). My region
was byte-identical to HEAD before I wrote it, so the two edits do not overlap. After my edits the stat
reads `7 ++++---` = 4 insertions / 3 deletions, which decomposes as my 2 replacements (2+/2-) plus my
1 added link definition (1+) plus the concurrent hunk (1+/1-). Measured, not inferred.

### Tests added or updated

None, and none possible — this pass writes no `.py` file. The plan's `### Test additions / updates`
names the executable checks that stand in; all of them ran and are quoted under `### Validation run`.
The two permanent tests that already pin F1's contract were confirmed present and are the reason no
new test is owed:

- `tests/types/test_converters.py::test_convert_scalar_duration_field_raises_unsupported`
- `tests/types/test_converters.py::test_convert_scalar_binary_field_raises_unsupported`

### Validation run

No `.py` file was touched, so **no `ruff` invocation was owed or made** (plan step 11). The markdown
gates were run scoped to this pass's own two files, never `.`:

```
uv run python scripts/check_trailing_commas.py --check TODAY.md docs/README.md   -> exit 0
git diff --check -- TODAY.md docs/README.md                                      -> exit 0
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
    -> "OK: 21 terms - all have glossary entries and at least one spec link."    -> exit 0
uv run python examples/fakeshop/manage.py import_spec_terms --check
    -> "OK: 49 done cards have glossary links."                                  -> exit 0
uv run python scripts/build_tree_md.py --check
    -> ".../docs/TREE.md is up to date."                                         -> exit 0
git status --short                                                               -> classified above
```

`import_spec_terms --check` reads **49** done cards, matching the plan's re-measurement and not the
build plan's older `48`; the number moves with the concurrent session and **exit 0 is the gate**.

No `pytest` run: the plan authorizes none, this pass adds no boundary, and no model field set or wire
shape changed, so the test-staleness sweep is not triggered either.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Audit results (the read-only verification legs)

Every count below was produced by the command beside it **as the number was written**, per the plan's
`### Notes for Worker 2` fourth bullet. Counts are of the shortest distinctive token, never of matching
lines. HEAD at this pass: `fdfb711f`.

**F1 / F2 re-derived against source, not against the plan (plan step 2).**

An `ast` walk of `django_strawberry_framework/types/converters.py` over both module-level dict
assignments (they are `AnnAssign`, so a plain `ast.Assign` walk misses them — worth knowing for the
reviewer re-deriving this):

- `SCALAR_MAP` — **26 entries**, listed in source order: `AutoField`/`BigAutoField`/`SmallAutoField`
  -> `int`; `CharField`/`TextField`/`SlugField`/`EmailField`/`URLField`/`GenericIPAddressField`/
  `FilePathField` -> `str`; `IntegerField`/`SmallIntegerField`/`PositiveIntegerField`/
  `PositiveSmallIntegerField` -> `int`; `BigIntegerField`/`PositiveBigIntegerField` -> `BigInt`;
  `BooleanField` -> `bool`; `FloatField` -> `float`; `DecimalField` -> `decimal.Decimal`;
  `DateField`/`DateTimeField`/`TimeField` -> `datetime.date`/`datetime.datetime`/`datetime.time`;
  `JSONField` -> `strawberry.scalars.JSON`; `UUIDField` -> `uuid.UUID`; `FileField`/`ImageField`
  -> `str`. **Neither `models.DurationField` nor `models.BinaryField` appears.**
- `FIELD_OUTPUT_TYPE_MAP` — **2 entries**: `ImageField -> DjangoImageType`, `FileField ->
  DjangoFileType` (image before file, so the MRO walk hits the subclass first).

Static absence is not the same as a raise, so the raise was **executed**, not read:

```
DurationField RAISES ConfigurationError: Unsupported Django field type 'DurationField' on
  <unbound>.x. Add an entry to SCALAR_MAP or exclude this field via Meta.exclude.
BinaryField   RAISES ConfigurationError: Unsupported Django field type 'BinaryField' on
  <unbound>.x. Add an entry to SCALAR_MAP or exclude this field via Meta.exclude.
```

(via `types/converters.py::scalar_for_field`, the single MRO-walk lookup shared by `convert_scalar`
and the filter-input converter, under `DJANGO_SETTINGS_MODULE=config.settings` with
`examples/fakeshop` on `sys.path`.) F1 and F2 are therefore established independently of the plan, of
R2's drift row D17, and of the module docstring. The docstring's own
#"Notably absent from the default map" paragraph and `docs/GLOSSARY.md`'s `Scalar field conversion`
entry agree with the measurement, which is why the corrections adopt their framing rather than a third.

**A3 — the remaining scalar / file-output claims.** Every other bullet in `TODAY.md`
`## Package scalar conversions` and every scalar claim in `docs/README.md`'s `**Shipped today**` list
was re-derived against the two maps above. **All hold**, including the two most likely to have rotted:

- `PositiveBigIntegerField -> BigInt` (R2's drift row D16, wrong *in the spec*): `TODAY.md:158` and
  `docs/README.md:100` both already read `BigInt`. **4 occurrences** of the token
  `PositiveBigIntegerField` across the four consumer docs (`TODAY.md` x2 — the conversion bullet and
  the `0.0.9` GlobalID break note that cites it as precedent; `docs/README.md` x2, both on line 100);
  zero of them say `int`.
- `FileField` / `ImageField` read output (D8): `TODAY.md:163` and `docs/README.md:99` both describe the
  structured `DjangoFileType` / `DjangoImageType` objects via `FIELD_OUTPUT_TYPE_MAP` with the filter /
  scalar-input value staying `str` — exactly the three-way split the two maps encode.
- PostgreSQL `ArrayField` -> `list[T]` and `HStoreField` -> JSON, both described as *soft-registered*:
  confirmed against the `_ARRAY_FIELD_CLS` / `_HSTORE_FIELD_CLS` sentinels (both from
  `utils/imports.py::import_attr_if_importable`) and `convert_scalar`'s step-0b dispatch, which runs
  **before** the MRO walk. Correct as written.

**One completeness observation, not a defect and not fixed:** `TODAY.md`'s list names 9 of `SCALAR_MAP`'s
26 keys explicitly and generalizes the rest — `SlugField` / `EmailField` / `URLField` /
`GenericIPAddressField` / `FilePathField` and `SmallAutoField` / `SmallIntegerField` /
`PositiveIntegerField` / `PositiveSmallIntegerField` carry entries the document does not name. The
document says the package "converts these model fields", not "only these", and the first three are
`CharField` subclasses the MRO walk would cover regardless. No claim is falsified, so no edit was made;
recorded because an unstated absence is indistinguishable from an unrun check.

**A4 — the D1-D18 sweep across `TODAY.md`, `docs/README.md`, `README.md`, `GOAL.md`.** Shortest
distinctive token per row, occurrences counted. **The zeros are results, not silence.**

| Row | Token searched | Occurrences across the 4 docs | Verdict |
|---|---|---|---|
| D1 (flat module layout) | `types.py`, `converters.py`, `optimizer.py`, `registry.py` | **0 / 0 / 0 / 0** | no doc asserts the retired flat layout |
| D2 (`lazy_ref` on the registry) | `lazy_ref` | **0** | clean |
| D3 (definition-order dependence) | `add_pending_relation` | **0**; `docs/README.md:104` states *"definition-order-independent relation finalization via `finalize_django_types()`"* | correct, matches `registry.py::TypeRegistry.add_pending_relation` + `types/finalizer.py::finalize_django_types` |
| D4 (`filterset_class` / `orderset_class` deferred) | `DEFERRED_META_KEYS` | **1**, at `docs/README.md:115`, reading *"`Meta.orderset_class` consumer wiring (promoted out of `DEFERRED_META_KEYS`)"* | correct — AST of `types/base.py` gives `DEFERRED_META_KEYS = frozenset({'aggregate_class','fields_class','search_fields'})` and `ALLOWED_META_KEYS` (17 keys) contains both `filterset_class` and `orderset_class` |
| D5 (`Meta.interfaces` unwired) | `install_is_type_of` | **0**; `TODAY.md:169` and `docs/README.md:102` both present `Meta.interfaces = (relay.Node,)` as shipped | correct against `types/relay.py::apply_interfaces` |
| D6 (one type per model) | `primary` | `docs/README.md:110` documents `Meta.primary` multi-type opt-in as shipped | correct against `registry.py::TypeRegistry.register` |
| D8 (file/image `-> str` on read) | see A3 above | — | correct |
| D10 (spec-named test modules) | `test_django_types`, `test_optimizer.py`, `test_choice_enums` | **0 / 0 / 0** | clean |
| D11 (`examples/fakeshop/fakeshop/`) | `fakeshop/fakeshop` | **0** | clean |
| D13 (no fakeshop M2M) | `ManyToMany` | `TODAY.md:182` reads *"Products' graph is FK-only; `OneToOneField` and `ManyToManyField` conversions are package capabilities covered by the package test suite"* | correct — `examples/fakeshop/apps/library/models.py:94` (`alt_branches`) and `:144` (`genres`) are the M2M fixtures, and 10 files under `tests/` reference them, so the sentence is true as scoped to *products* |
| D14 (commented-out example schema) | — | `TODAY.md:27` and its whole `## What's in products/schema.py today` section describe a live wired schema | correct |
| D16 | `PositiveBigIntegerField` | **4**, all `BigInt` | correct |
| D17 | `Duration` / `Binary` | **fixed by this pass** — see below | corrected |
| D18 (Property's relation set) | `Property.entries` | `TODAY.md:174` names `Category.items` / `Category.properties` / `Item.entries` / **`Property.entries`** | correct — carries D18's corrected fact already |

D7, D9, D12, D15 concern spec-internal prose with no consumer-doc counterpart; nothing in the four docs
asserts them, so there is nothing to falsify.

**The `Duration` / `Binary` occurrence census, measured after the edits** (case-sensitive, per token):

| Token | `README.md` | `GOAL.md` | `TODAY.md` | `docs/README.md` |
|---|---|---|---|---|
| `Duration` | 0 | 0 | 1 | 1 |
| `Binary` | 0 | 0 | 2 | 1 |
| `duration` | 0 | 0 | 0 | 0 |
| `binary` | 0 | 0 | 1 | 0 |

`README.md` and `GOAL.md` carry **zero occurrences of any of the four tokens**, so the plan's
"neither is implicated" holds and neither file was edited. Every remaining occurrence is inside one of
this pass's two corrections (`TODAY.md`: `DurationField` + `BinaryField` + `SCALAR_MAP[BinaryField]` +
"plug for binary"; `docs/README.md`: `DurationField` + `BinaryField`), each now asserting the
**absence**, not a conversion.

**A5 — `docs/TREE.md`.** `uv run python scripts/build_tree_md.py --check` -> `...docs/TREE.md is up to
date.`, exit 0. No drift, therefore no docstring edit and no regenerate. The one package-source touch
R3 was conditionally authorized to make was not owed and was not made.

**A6 — `docs/GLOSSARY.md` for the spec-001 surface.** `check_spec_glossary.py` proves the headings
exist; the second half (does the entry describe shipped behavior?) is a read, and it was done. All
**21** CSV anchors resolved against the file's `## ` headings by an independent slugger that renders
reference-link and inline-link markup *before* slugging — the trap the plan flags in
`check_spec_glossary.py::github_anchor`, which three prior passes copied. **0 unresolved.** The 21
entries' `**Status:**` lines:

- 18 shipped: `apply_cascade_permissions` (`0.0.10`), `bigint-scalar` (`0.0.6`), `configurationerror`
  (`0.0.1`), `definition-order-independence` (`0.0.4`), `djangoconnectionfield` (`0.0.9`),
  `djangooptimizerextension` (`0.0.2`), `djangotype` (`0.0.5`), `filterset` (`0.0.8`),
  `metadescription`, `metaexclude`, `metafields`, `metainterfaces` (`0.0.5`), `metamodel`, `metaname`,
  `only-projection` (`0.0.2`), `orderset` (`0.0.8`), `relay-node-integration` (`0.0.5`),
  `scalar-field-conversion` (`0.0.1`+).
- 3 planned, and each planned status is **corroborated by source**, not accepted: `aggregateset`
  (planned `0.1.3`) and `per-field-permission-hooks` (planned `0.1.1`, hosted on `FieldSet` via
  `Meta.fields_class`) both rest on keys that are still in `DEFERRED_META_KEYS`
  (`aggregate_class`, `fields_class`); `metachoice_enum_names` (planned `0.1.4`) rests on
  `choice_enum_names`, which is in neither `ALLOWED_META_KEYS` nor `DEFERRED_META_KEYS` and so is
  rejected by the `unknown` branch of `types/base.py`'s Meta validation.

`Scalar field conversion` — the entry both corrections now point at — was read end to end and states
the `DurationField` / `BinaryField` absence and both plugs correctly. **No drift found, so no ORM edit,
no `build_glossary_md.py` run, and no two-regenerate check was owed.** `docs/GLOSSARY.md` is dirty in
the tree from the concurrent session's `Hard dependency` version-floor edit; it was read, not written.

**A7 — `KANBAN.md` card `DONE-001-0.0.1`.** Read at `KANBAN.md:4901-4988`. Every block audited against
source:

- `#### Scope` — the 8 bullets (`DjangoType` base, Meta validation, scalar conversion, relation
  conversion, choice enums, type registry, relation resolvers, `get_queryset` hook +
  `has_custom_get_queryset`) all name shipped surface. Holds.
- `#### Package files` — 7 rows. The 4 linked rows (`__init__.py`, `conf.py`, `exceptions.py`,
  `registry.py`) all exist on disk; the 3 `(historical)` rows (`converters.py`, `optimizer.py`,
  `types.py` at the package root, i.e. `TrackedPath.is_current = False`) are all **absent** from disk,
  which is exactly what the marker asserts and exactly R2's drift row D1. Holds.
- `#### Files likely touched` — all 6 (`types/base.py`, `types/converters.py`, `types/resolvers.py`,
  `tests/types/test_base.py`, `tests/types/test_converters.py`, `tests/types/test_resolvers.py`) exist.
  Holds.
- `#### Decision` — *"Deferred Meta keys are rejected, not silently accepted."* Verified at
  `types/base.py` #"Meta keys not supported yet", which raises `ConfigurationError` on
  `declared & DEFERRED_META_KEYS`. Holds.
- `#### Note` and `#### Card references` — the `DONE-010-0.0.4` definition-order pointer resolves.
  Holds.
- `#### Glossary terms` — the same 21 terms as the CSV, same statuses as A6.

**No drift found, so no ORM edit, no `build_kanban_md.py` / `build_kanban_html.py` run, and no
two-regenerate check was owed.** `KANBAN.md` / `KANBAN.html` are dirty from the concurrent
`DONE-049-0.0.14` card wrap; they were read, not written.

**B1 — direction 1, references TO spec-001.** Re-run rather than trusted. Occurrences of the token
`spec-001`, counted per file across the whole tree (excluding `.git`, `dist`, `node_modules`, `.venv`,
`docs/shadow`):

| File | Occurrences | Note |
|---|---|---|
| `KANBAN.md` | 4 | 2 links at `:146` and `:4908`, each contributing link text + path; both resolve to `docs/SPECS/spec-001-django_types-0_0_1.md` (generated) |
| `KANBAN.html` | 3 | same two card links, in the generated data block |
| `docs/SPECS/spec-001-django_types-0_0_1.md` | 8 | self |
| `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` | 70 | self |
| `docs/SPECS/spec-002-optimizer-0_0_2.md` | 5 | `:9`, `:56`, `:57`, `:80` — bare filenames in code spans, resolving within `docs/SPECS/` |
| `docs/SPECS/spec-005-django_type_contract-0_0_3.md` | 4 | `:5`, `:107`, `:109`, `:122` — same shape |
| `docs/SPECS/spec-006-public_surface-0_0_3.md` | 1 | `:134` — same shape |
| `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` | 10 | `:6`, `:86`, `:436`, `:598`, `:645` + the **only real link definition**, `[spec-001]: spec-001-django_types-0_0_1.md` at `:1830`, which resolves from `docs/SPECS/` |
| this cycle's own artifacts (`bld-001-r1/r2/r3`, `build-001-…`) | 70 / 161 / 63 / 27 | per-cycle scratch, not shipped source |

**The confirmed-zero set is genuinely zero and was measured, not assumed**: `README.md`, `GOAL.md`,
`TODAY.md`, `AGENTS.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/README.md`, and `CHANGELOG.md` do
not appear in the per-file occurrence listing at all. Every reference outside the spec family is a
generated kanban link or a sibling-spec filename; **no reference is broken and none needed rewriting.**

**B2 — direction 2, references INSIDE the moved files.** A scratch checker (written to the session
scratchpad, **not** to `scripts/`, per the plan's DRY ruling) that strips fenced blocks and code spans,
then normalizes every definition path against its own file's directory and `os.path.exists`-checks it:

| File | defs | used refs | undefined | orphan | broken on disk | inline cross-file links |
|---|---|---|---|---|---|---|
| `docs/SPECS/spec-001-django_types-0_0_1.md` | 22 | 22 | 0 | 0 | **0** | 0 |
| `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` | 18 | 18 | 0 | 0 | **0** | 0 |
| `TODAY.md` (after this pass) | 25 | 25 | 0 | 0 | **0** | 0 |
| `docs/README.md` (after this pass) | 36 | 36 | 0 | 0 | **0** | 0 |

The 22/22 and 18/18 reproduce the plan's numbers independently. The last two rows are this pass's own
files, each carrying **+1** definition from this pass, both disk-exists-checked as `START.md` requires,
both placed alphabetically inside the existing `<!-- docs/ -->` group, and both files already carry all
10 canonical group headers.

**B3 — direction 3, the companions.** `ls docs/SPECS/appx/` returns exactly
`spec-001-django_types-0_0_1-rationale.md` and `spec-001-django_types-0_0_1-terms.csv`; `ls docs/` has
**no** spec-001-named entry, so nothing is stranded at the `docs/` root. The spec's own companion
reference carries the prefix: `[spec-001-rationale]: appx/spec-001-django_types-0_0_1-rationale.md` at
`docs/SPECS/spec-001-django_types-0_0_1.md:494`, used by 6 in-body `[rationale file][spec-001-rationale]`
links. `AGENTS.md` rule 26 satisfied.

**B4 — the terms-CSV / import chain.** `csv.DictReader` over
`docs/SPECS/appx/spec-001-django_types-0_0_1-terms.csv`: fieldnames `term, anchor, notes`; **21 data
rows, 21 distinct anchors, 0 duplicates** — the uniqueness `import_spec_terms` requires (and which
`check_spec_glossary.py` alone would not catch, since it tolerates many terms per anchor). Both
constraint commands quoted above, both exit 0. The spec's anchor budget re-measured for the record:
**21 distinct anchors / 22 body links**, `configurationerror` the only anchor used twice — unchanged,
as expected from a pass that edits no spec.

**B5 — the kanban record.** Read-only through the fakeshop ORM:

```
Card.objects.get(number=1)  -> card_id DONE-001-0.0.1 | status Done | target_version 0.0.1 (alpha)
                             | title "DjangoType core foundation"
card.glossary_links.count() -> 21
card.spec.path              -> docs/SPECS/spec-001-django_types-0_0_1.md   (exists on disk: True)
card.spec.url               -> https://github.com/riodw/django-strawberry-framework/blob/main/
                               docs/SPECS/spec-001-django_types-0_0_1.md   (derived, read-only)
```

`status` and `target_version` render as `Done` and `0.0.1 (alpha)` — display forms of the plan's `done`
/ `0.0.1`, not a divergence. The archived path is already what the DB holds; nothing to write.

**D1 — staged-anchor sweep.**

```
grep -rEn 'TODO\(spec-001|TODO-(ALPHA|BETA|STABLE)-001' . \
  --exclude-dir=.git --exclude-dir=dist --exclude-dir=node_modules \
  --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md
```

**2 occurrences**, both on a single line — `docs/builder/build-001-django_types-0_0_1.md:187`, the R3
checklist line that *describes this sweep* and names both patterns in one sentence. The plan predicted
"1 occurrence" at the same site; the honest reading is 2 occurrences / 1 matching line / 1 file, which
is why the plan insists on counting occurrences rather than lines — this is the same discrepancy in
miniature. **Zero anchors in package source, in `tests/`, or in `examples/`**, so the
`revision-needed` trigger does not fire.

### Implementation notes

- **Two separate bullets, not one merged line, in `TODAY.md`** (the plan's second discretion item).
  `DurationField` was struck from the date/time bullet rather than the bullet being rewritten, because
  the three surviving field types genuinely do convert and the bullet carries a products anchor
  (`created_date` / `updated_date`) that stays true. The `BinaryField` bullet's slot was reused for a
  single **Absent from the default map** bullet covering both types — one negative statement in the
  list beats two, and reusing the slot keeps the list's order and the section's shape.
- **The correction states the fact plus a pointer, never the reasoning** (the plan's duplication risk 2).
  The *why* — no first-party Strawberry scalar — is one clause; the *consumer plug* is named because
  a reader whose model has one of these columns needs it to act; everything past that is left to
  `docs/GLOSSARY.md#scalar-field-conversion`. There is deliberately no fourth copy of the converter
  docstring's, the glossary's, `CHANGELOG.md`'s, and the spec's shared explanation.
- **Three recourses named, in the order the package offers them**: register a `SCALAR_MAP` entry, a
  consumer annotation override, or `Meta.exclude`. The first and third come from the runtime error
  message itself (`types/converters.py::scalar_for_field`); the second from
  `docs/GLOSSARY.md`'s `Scalar field override semantics`, which records that an unsupported scalar is
  overrideable and calls `Meta.exclude` and annotation override "parallel consumer recourses". Naming
  only the `SCALAR_MAP` plug would have understated the surface.
- **`docs/README.md` keeps its sentence's shape** (the plan's third discretion item, resolved toward
  naming the absence inline). The entry is one long parenthetical already structured as
  `<scalar list>; <file/image detail>`; the correction removes `binary` from the list and inserts one
  more `;`-delimited clause using the same separator the entry already uses, rather than restructuring
  it. Naming the absence beat leaving it to the pointer because the deleted word is the exact word a
  future editor would re-add from memory.
- **Both files get a real reference-style link, not an inline one.** `START.md`'s convention is not
  optional for a new cross-file link, and both files already had the `<!-- docs/ -->` group; the ref-id
  `glossary-scalar-field-conversion` matches each file's existing `glossary-<anchor>` naming, and the
  two definitions differ only in relative depth (`docs/GLOSSARY.md#…` from the root,
  `GLOSSARY.md#…` from `docs/`) — the exact reason the convention exists.
- **The B2 checker renders link markup before slugging.** The plan flags that feeding a reference-style
  heading to `check_spec_glossary.py::github_anchor` yields a false negative
  (`## [Scalar field conversion][glossary-…]` -> `scalar-field-conversionglossary-scalar-field-conversion`),
  and that three consecutive passes in this cycle copied the broken method. The scratch slugger strips
  `[text][ref]` and `[text](url)` to `text` first. It lives in the session scratchpad and is **not**
  added to `scripts/` — promoting it is the maintainer call R2 already catalogued.
- **An `ast.Assign` walk of `converters.py` returns nothing for either map.** Both are annotated
  (`SCALAR_MAP: dict[type[models.Field], Any] = {...}`), so they are `ast.AnnAssign` nodes. A reviewer
  re-deriving the 26/2 counts with the obvious walk will measure zero and conclude the maps are absent;
  they are not.

### Notes for Worker 3

- **Where to start.** The plan says the sharp risk here is stopping too early, not getting the two
  edits wrong. The two edits are four hunks and read in a minute; the audit legs are the body of the
  work. Every leg above quotes the command that produced it — a result with no command is the thing to
  push back on, and I have tried to leave none.
- **Re-derive 26 and 2 yourself** — and use `ast.AnnAssign`, or you will measure zero (see the last
  implementation note). Then re-run the raise: static absence from a dict and a `ConfigurationError`
  at type creation are two claims, and only the second is what `TODAY.md` and `docs/README.md` now
  assert.
- **`TODAY.md` attribution.** The file carries a concurrent hunk at line 381 (`065` -> `DONE-046`),
  which is not mine and must not be reverted or reviewed as this pass's. My three hunks are at 157,
  162, and the `<!-- docs/ -->` link-definition group. `git show HEAD:TODAY.md` proves 157/162 were
  byte-identical to HEAD before I wrote them.
- **No DB-backed doc was written**, so there is no two-consecutive-regenerate evidence to check — the
  correct question is whether A6 and A7 should have found drift, not whether the regenerate was
  verified. `docs/GLOSSARY.md`, `KANBAN.md`, and `KANBAN.html` are dirty from the concurrent spec-049
  card wrap; I read them and wrote none of them.
- **The C-boxes are deliberately open.** C1/C2/C3 belong to the interstitial Worker 1 pass that runs
  after this `built` and before your review. If they are still `- [ ]` when you review, the dispatch
  was skipped, which the plan's `### Notes for Worker 1` item 1 calls `revision-needed` — that is a
  dispatch defect, not a build defect.
- **A candidate temp test**, if you want one under `docs/builder/temp-tests/r3-spec001/`: the B2 checker.
  Its one non-obvious requirement is the markup-before-slug ordering above.

### Notes for Worker 1 (spec reconciliation)

**No spec edit is requested by this pass**, and no drift was found that a spec edit would answer. Four
things to carry forward:

1. **The two `spec-002` obligations (C1, C2) are still open and untouched**, as the ownership partition
   requires — `docs/SPECS/spec-002-optimizer-0_0_2.md:9` and `:80` still cite text that R1 moved into
   `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`. Re-confirmed open at this pass: neither
   line changed on disk, and `git status` still carries no `spec-002` entry. C3 remains the optional
   recording. I did not read the rationale file (`BUILD.md` `### Who reads it, and when` — Worker 2
   never does), so I can confirm the two `spec-002` lines are as quoted but not that the rationale
   headings named in the plan are still spelled that way; that check is yours.
2. **`TODAY.md`'s scalar list is a documented subset, not an enumeration.** It names 9 of `SCALAR_MAP`'s
   26 keys and generalizes the rest (detail under A3 above). This is not drift and I made no edit, but
   it is the kind of thing a later pass may read as an omission and "fix" into a 26-row table, which
   would recreate exactly the doc-to-doc duplication the plan's DRY analysis rules out. If it should be
   settled either way, the natural site is the section's own lead-in sentence at `TODAY.md:152`, not
   the spec.
3. **The staged-anchor sweep measures 2 occurrences, where the plan predicted 1** — same file, same
   line (`docs/builder/build-001-django_types-0_0_1.md:187`), which names both patterns in one
   sentence. Nothing is wrong in the tree; the delta is line-vs-occurrence counting, which is this
   cycle's named practice failure appearing once more inside the check written to catch it. Worth a
   line in the final gate's record, since the build plan's own checklist text is the sole matching site
   and a future cycle re-running this sweep will hit the same off-by-one.
4. **Nothing for the deferred-work catalog from this pass.** The two items R2 already put on record
   (the `OptimizerHint.prefetch` visibility test-surface gap, and promoting a shared link/anchor checker
   to `scripts/`) are unchanged by R3; I hand-wrote the checker a seventh time into scratch rather than
   opening that call, as the plan directs.

---

## Spec-002 pointer pass (Worker 1)

The interstitial pass `### Ownership partition inside R3` scheduled: dispatched after Worker 2 set
`built`, before Worker 3's review, so the review covers one combined R3 diff. Scope is boxes **C1-C3**
and nothing else. **`Status:` stays `built`** — this pass performs no transition.

`docs/SPECS/spec-002-optimizer-0_0_2.md` is a spec file, so `BUILD.md` `## Spec reconciliation` and
`worker-1.md` `## Scope` make it Worker 1's alone; that is the whole reason this pass exists as a
separate dispatch rather than as part of Worker 2's.

### Working-tree baseline, re-measured at this pass's open

HEAD is still `fdfb711f`. `git status --porcelain`, classified — **the set moved again** (`docs/README.md`
is now dirty because it is Worker 2's own F2 edit, and `docs/SPECS/spec-002-…` is dirty only after my
edit; `SECURITY.md`, `TODAY.md`, `uv.lock`, `docs/GLOSSARY.md`, `KANBAN.*`, `docs/spec-049-…`, the
sqlite db are the concurrent session's, unchanged in membership from the build report):

```
 M KANBAN.html          <- concurrent
 M KANBAN.md            <- concurrent
 M SECURITY.md          <- concurrent
 M TODAY.md             <- R3 Worker 2 (F1) + the concurrent line-381 hunk
 M docs/GLOSSARY.md     <- concurrent
 M docs/README.md       <- R3 Worker 2 (F2)
 M docs/SPECS/spec-001-django_types-0_0_1.md          <- THIS CYCLE (R1 + R2), not this pass
 M docs/SPECS/spec-002-optimizer-0_0_2.md             <- THIS PASS
 M docs/spec-049-dependency_ci_hardening-0_0_14.md    <- concurrent
 M examples/fakeshop/db.sqlite3                       <- concurrent
 M uv.lock                                            <- concurrent
?? docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md   <- THIS CYCLE (R1 + R2), not this pass
?? docs/builder/bld-001-r1/r2/r3…, build-001-…                <- THIS CYCLE
```

Nothing was reverted, checked out, restored, or stashed. **This pass wrote exactly one tracked file**,
`docs/SPECS/spec-002-optimizer-0_0_2.md`, plus this artifact and `worker-memory/worker-1.md`.

### Both references verified before editing, not accepted from the hand-off

`BUILD.md` `## Claims are proven mechanically, never accepted on prose` applies to a handed-down finding
exactly as to a fresh one. R2's hand-off and this plan both assert that lines 9 and 80 dangle. **One
does. One does not**, and the second is a finding to record rather than an edit to make.

**C1 — line 9 genuinely dangles.** The reference promises that *spec-001* predicted the split. Token
occurrences in `docs/SPECS/spec-001-django_types-0_0_1.md`, counted with
`grep -o "<token>" <file> | wc -l`:

| Token | spec-001 | rationale |
|---|---|---|
| `cut line` | **0** | 3 |
| `natural cut` | **0** | 1 |
| `ever split` | **0** | 1 |
| `lockstep` | **0** | 2 |
| `broken-by-default` | **0** | — |

The predicting paragraph is at `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md:94`,
*"The cut line the spec named for itself, and then took."*, inside the entry
`### Whole-document scope — the optimizer was bundled deliberately (former `## Scope creep into the N+1 problem`)`
(rationale `:64`) — exactly where the plan said it would be, re-read on disk rather than inherited. The
rationale's `## Provenance of this record` lists the whole of `## Scope creep into the N+1 problem`
under **Moved**, which is the second, independent confirmation that the paragraph left the spec.

What spec-001 still carries is the *outcome*, never the prediction: `:414` (Slices 4-6 "are owned by
`spec-002-optimizer-0_0_2.md`") and `:418` ("Why the optimizer slices moved … are in the
[rationale file][spec-001-rationale]"). A reader can reach the prediction in two hops via `:418`, which
mitigates the defect but does not discharge it — the reference says spec-001 *predicted* it, and a
reader landing there finds no prediction. **Edited.**

**C2 — line 80 resolves; no edit made.** The bullet reads: *"The visibility-leak / `Prefetch` downgrade
discussion that motivated bundling the optimizer with `spec-001-django_types-0_0_1.md` originally: issue
#572 and PR #583 on `strawberry-graphql/strawberry-django`."* Three measurements, any one of which is
sufficient:

1. **The bullet names its own referent, and it is not spec-001.** It is a `## References` entry whose
   cited source is issue #572 / PR #583 upstream. Following it leads to GitHub, not into spec-001.
2. **R1 did not move that discussion.** The rationale's `## Provenance of this record` (rationale `:54-60`)
   lists, under **"Deliberately left in the spec by this pass"**, *"the `## N+1 strategy` section,
   including its per-slice implementation paragraphs and the PR #583 derivation"* — and calls that
   paragraph "the load-bearing 'why'". The carve-out is the reason it stayed.
3. **It is still in spec-001 at HEAD-of-worktree.** `572` occurs **2** times and `583` occurs **2** times,
   at `:351` (the derivation: *"FK joins bypass per-type visibility filtering and leak rows"*) and `:464`
   (spec-001's own `## References` bullet).

Counter-reading, stated so a later pass does not re-open it: one could read *"that motivated bundling"*
as pointing at the bundling **argument**, which is in the rationale at `:87`
(*"Alternative rejected — two specs in lockstep"*). It loses because the clause is a descriptor of the
discussion, not a locator — the bullet's only locator is the issue and PR — and because adding a
rationale pointer there would make spec-002's `## References` carry a route into spec-001's deliberation
about its own scope, which is precisely the narration `BUILD.md` `## Spec rationale extraction` forbids a
spec from acquiring. **Discharged as verified-resolves; the box is ticked because the obligation
(verify, fix if broken) is complete, not because an edit landed.**

**C3 — confirmed closed; the optional recording assessed and declined.** The recorded state re-verified
rather than accepted: R2's `### Notes for Worker 1 (spec reconciliation)` item 1 fourth bullet
(`bld-001-r2-spec_reconciliation.md:2976-2980`) reads *"The third obligation is CLOSED and R3 must not
re-open it as a rule-stating duty. Both optimizer rules R2 lifted are now contract in spec-001's
`## N+1 strategy`."* Both are present and were read this pass:

- the O5 reason at `docs/SPECS/spec-001-django_types-0_0_1.md:349` — a projection over a joined relation
  must carry the source row's local FK column, or Django defers the joined attributes and reintroduces
  the N+1;
- the O6 clause at `:357` — the target type's `get_queryset` is applied to the child queryset of **every
  `Prefetch` the planner builds**, the downgrade closing the one branch that has no child queryset.

What remained was optional: a *recording* that the prose lift happened, at spec-002's
`## Coordination with `spec-001-django_types-0_0_1.md`` heading. **Assessed, and not written**, for two
reasons that are the same reason:

- It would be a history, not a contract. That heading currently states the division of labour
  normatively ("Slices 4-6 are superseded by this optimizer spec family. The type-system pieces still
  belong in `spec-001-django_types-0_0_1.md`; the optimizer consumes them here."), and a sentence
  recording that a prior pass moved prose between documents adds no normative content while making
  spec-002 the first spec in the family to narrate its own maintenance.
- It is out of the discharge this pass was given. The plan's own minimum for C1/C2 is *a pointer, never
  new narration*; a C3 recording is narration by construction, and the plan explicitly authorizes closing
  it as "assessed, not needed" provided the assessment is written down. This is that assessment.

The binding constraint the recording was standing in for is already durable and was re-confirmed present
this pass: if a later cycle re-homes the two rules into spec-002 it must re-home the PR #583 carve-out
with them and delete all three from spec-001 in the same change, recorded in bold in the rationale's
``### `## N+1 strategy``` entry.

### The edit

One insertion, in `## Problem statement`, second sentence:

> That prediction is recorded in `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`.

**Register matched to the file's one existing instance of this shape**, the O4 extraction at
`docs/SPECS/spec-002-optimizer-0_0_2.md:6` — *"The O4 design record remains in
`docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md`; …"* — same "the record lives at
`<repo-root-relative path>`" construction, in an inline code span, in the spec's own flat declarative
voice. It states where the record is and stops; it does not say the text moved, when, or why.

**Markdown link convention — determined by reading spec-002's block, not by default.** `START.md`'s
reference-style rule governs markdown *links*; a code-span path is not a link. Measured in spec-002:
**8** spec-filename references (`:6`, `:9` x2 including mine, `:54`, `:56`, `:57` x2, `:80`), **all** of
them inline code spans; **3** reference-style link uses, all three resolving to `../GLOSSARY.md#…`;
**0** inline cross-file links. The `<!-- docs/SPECS/ -->` group is empty and stays empty. Adding a link
definition would have made mine the only linked sibling reference in the file — the opposite of "match
how it already spells its sibling references". **The `<!-- LINK DEFINITIONS -->` block is byte-unchanged**
and all 10 canonical group headers remain present, in order.

The path was disk-exists-checked from the repo root (`test -f … -> EXISTS`), and its 56 characters were
measured, not typed from memory.

**Byte proof that the diff is exactly this one insertion.** `wc -c` on spec-002: **7,214 -> 7,305**,
delta **+91**. The inserted string measures **91** characters
(`python3 -c "print(len(s))"` on the literal, leading space and trailing period included: 1 + 31 + 1 + 56
+ 1 + 1). The two numbers were produced independently and agree, which pins "one insertion, nothing else
touched" without relying on reading the diff. `git diff --stat` concurs: `1 insertion(+), 1 deletion(-)`
on one line.

### Validation run

Every command scoped to this pass's own file; never `.`, which would sweep the concurrent session's work.

```
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md
    BEFORE -> "OK: 3 terms - all have glossary entries and at least one spec link."   exit 0
    AFTER  -> "OK: 3 terms - all have glossary entries and at least one spec link."   exit 0
uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-002-optimizer-0_0_2.md   exit 0
git diff --check -- docs/SPECS/spec-002-optimizer-0_0_2.md                                      exit 0
```

Both readings of `check_spec_glossary.py` on spec-002 are quoted because constraint 5 of this pass is
that a **new inline term reference can break a spec whose terms are checked**. The insertion deliberately
introduces no project-specific term — it names a file path and nothing else — so the term count is
unchanged at 3 (`only-projection`, `djangotype`, `djangooptimizerextension`).

**No `.py` file was touched, so no `ruff` invocation was owed or made.** No `pytest`, with or without
`--cov*`.

**`docs/SPECS/spec-001-django_types-0_0_1.md` and its rationale were NOT edited by this pass** — proven,
not asserted: `git status --porcelain` still shows spec-001 as ` M` from R1+R2 and the rationale as `??`,
and this pass's only `Edit` call targeted spec-002. Constraint 4's re-run is therefore not owed. Both
commands were nonetheless run as confirmations, and the anchor budget re-measured:

```
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
    -> "OK: 21 terms - all have glossary entries and at least one spec link."   exit 0
uv run python examples/fakeshop/manage.py import_spec_terms --check
    -> "OK: 49 done cards have glossary links."                                  exit 0
spec-001 anchor budget -> 21 distinct anchors / 22 body links, `configurationerror` the only double
```

`49` is the concurrent session's `DONE-049-0.0.14` wrap, unchanged from the build report; **exit 0 is the
gate, the number is not.**

### Rule 27

The inserted sentence names a file, not a source symbol, so no symbol qualification applies; it adds no
`path:NN`. Raw `path:NN` in this artifact is permitted (`AGENTS.md` rule 27: per-cycle `docs/builder/bld-*.md`).

One **pre-existing** rule-27 violation was observed in spec-002 and deliberately not fixed — see
`### Notes for Worker 1 (spec reconciliation)` below.

### Spec changes made (Worker 1 only)

| Spec | Line | Change | Reason | Triggered by |
|---|---|---|---|---|
| `docs/SPECS/spec-002-optimizer-0_0_2.md` | 9 (`## Problem statement`) | One sentence inserted after the first: ``That prediction is recorded in `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`.`` | The cited prediction left spec-001 in item R1 and now exists only in the rationale companion (0 occurrences of `cut line` / `natural cut` / `ever split` in spec-001; the paragraph is at rationale `:94`). A pointer restores resolution at the minimum authorized size. | R3, box C1 |

**No other spec change.** C2 required none (the reference resolves — evidence above); C3's optional
recording was assessed and declined as narration. `docs/SPECS/spec-001-django_types-0_0_1.md` and
`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` were read this pass and written by no part of
it.

### Notes for Worker 3

- **Re-derive C2's verdict rather than accepting it** — it is the one place this pass departs from both
  the hand-off and the plan. The three measurements are `grep -o '572' docs/SPECS/spec-001-…md | wc -l`
  (2), the same for `583` (2), and the rationale's `## Provenance of this record` bullet beginning
  *"Deliberately left in the spec by this pass"*. If you read line 80 as pointing at the **bundling
  argument** rather than at issue #572 / PR #583, say so — that is the live disagreement, and the
  counter-reading is stated above so you can attack it directly rather than reconstruct it.
- **The C3 box is ticked with no diff behind it.** That is deliberate and authorized by the plan's own
  wording (*"May close as 'assessed, not needed' provided the assessment is written down"*). Check the
  assessment, not for an edit.
- **Check the register, not just the resolution.** The failure mode this pass most plausibly commits is
  narration creeping in under the cover of a pointer. The test: does the new sentence tell a reader that
  something *moved*? It should say only where the record is.
- **The link-convention call is a judgement worth auditing.** I read "match how it already spells its
  sibling references" as governing, measured 8 code spans / 0 inline links / 3 reference links all to
  the glossary, and added no link definition. If you conclude a new cross-file reference owes a
  reference-style link regardless of the file's existing spelling, that is a Low finding with a one-line
  fix (`[spec-001-rationale]: appx/spec-001-django_types-0_0_1-rationale.md` under `<!-- docs/SPECS/ -->`),
  not a re-plan.
- **`spec-002`'s `check_spec_glossary` reading is quoted before and after** because a spec whose terms are
  checked can be broken by an inline term; re-run it if you doubt the 3.

### Notes for Worker 1 (spec reconciliation)

Carried into R3's final verification and the final gate.

1. **A pre-existing `AGENTS.md` rule-27 violation sits in `spec-002` and this pass did not fix it.**
   `docs/SPECS/spec-002-optimizer-0_0_2.md:72` (`## References`) carries a raw line-range reference:
   ``graphene-django relation resolver wrap: `/Users/…/site-packages/graphene_django/converter.py:308-471`.``
   Confirmed **pre-existing at HEAD** (`git show HEAD:docs/SPECS/spec-002-optimizer-0_0_2.md | grep -n`
   returns the identical line 72), so it is not this cycle's regression. Not fixed because (a) this pass's
   authorized discharge is the C-boxes and a pointer, and rewriting a `## References` bullet is the
   surrounding-prose rewrite R2 ruled out of scope; (b) the symbol-qualified replacement names a symbol in
   an **upstream** package outside this repo, so deriving it is real work with a real chance of naming the
   wrong symbol — this cycle's catalogued failure mode. **Owner: a future spec-002 cycle's Worker 1, or a
   maintainer call.** Recorded here rather than left unowned, because this cycle has already watched one
   unowned recommendation die in an artifact.
2. **C2 closed as verified-resolves, against the hand-off's assertion.** If final verification re-derives
   it the other way, the remedy is one sentence in the same shape as C1's, not a re-plan. The evidence
   chain is in this section; the rationale's provenance bullet is the strongest single link, because it
   records the carve-out as a **decision** rather than an accident.
3. **The anchor budget is untouched and re-measured: 21 distinct / 22 body links**, `configurationerror`
   the only double. This pass edited no spec-001 prose, so the constraint was never at risk; the number is
   recorded so the final gate need not re-derive it.
4. **Nothing new for the deferred-work catalog** beyond item 1 above. R2's two catalogued items (the
   `OptimizerHint.prefetch` visibility test-surface gap, and promoting a shared link/anchor checker to
   `scripts/`) are unchanged by this pass.

---

## Review (Worker 3)

Fresh spawn. Reviewed **one combined R3 diff** — Worker 2's `TODAY.md` + `docs/README.md` corrections and
the interstitial Worker 1 pass's one-sentence `spec-002` insertion — obtained with
`git diff -- TODAY.md docs/README.md docs/SPECS/spec-002-optimizer-0_0_2.md` plus the untracked-file
listing, never from the build report's account of itself.

`git status --short` re-measured at this pass's open. **Membership is unchanged** from the Worker 1
pass's snapshot: ` M KANBAN.html`, `KANBAN.md`, `SECURITY.md`, `TODAY.md`, `docs/GLOSSARY.md`,
`docs/README.md`, `docs/SPECS/spec-001-…`, `docs/SPECS/spec-002-…`, `docs/spec-049-…`,
`examples/fakeshop/db.sqlite3`, `uv.lock`; `??` the rationale companion and the four cycle artifacts.
Nothing was reverted, checked out, restored, or stashed by this review, and nothing outside the
declared write set changed under it.

**Every number below is my own measurement**, produced by the command quoted beside it, at the moment it
was written. This cycle's named practice failure is re-derivation loss, so no count is inherited from
the plan or the build report — including the ones they got right.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

#### The `SCALAR_MAP[BinaryField] = strawberry.scalars.Base64` plug literal now has five homes

The plan's `### DRY analysis` duplication risk 2 fixed the constraint: `TODAY.md` and `docs/README.md`
get *the fact plus a pointer*, **not the reasoning**, so that the explanation does not acquire a fourth
copy. Measured against the delivered text, `TODAY.md:162` carries the fact **and** the reason **and**
the full recourse set **and** the plug literal:

```TODAY.md:162
- **Absent from the default map:** `DurationField` and `BinaryField` — a column of either type raises
  `ConfigurationError` at type creation, because Strawberry ships no first-party scalar for
  `datetime.timedelta` or `bytes`. The consumer recourses are registering one
  (`SCALAR_MAP[BinaryField] = strawberry.scalars.Base64` is the conventional plug for binary), a
  consumer annotation override, or `Meta.exclude`. …
```

Occurrence census of the shortest distinctive token `strawberry.scalars.Base64`
(`grep -rn 'strawberry.scalars.Base64' .`, cycle artifacts and `.venv` excluded) — **5 shipped sites**:
`django_strawberry_framework/types/converters.py` (module docstring), `docs/GLOSSARY.md`
(`## Scalar field conversion`), `CHANGELOG.md:202`, `docs/SPECS/spec-001-django_types-0_0_1.md:176`,
and now `TODAY.md:162`. `tests/types/test_converters.py:594` is a sixth, as a test docstring.

Maximal-shared-shingle scan against the two documents the plan named as the framing source (normalized,
punctuation stripped, code-span backticks preserved; script at
`docs/builder/temp-tests/r3-spec001/shingle.py`):

| Source | vs `spec-001:176` | vs `docs/GLOSSARY.md` entry |
|---|---|---|
| `TODAY.md:162` | **9 words** — *"Strawberry ships no first party scalar for `datetime.timedelta` or"* | 6 words |
| `docs/README.md:99` | **10 words** — *"`DurationField` and `BinaryField` are deliberately absent from the default map"* | 5 words |

So this is **not** a verbatim lift — the longest shared run is 10 words and each sentence is
independently written. It is a *content* duplication: the same three facts (absence, reason, plug
literal) restated at a fifth site, which is the failure mode the plan named and the one that put
`TODAY.md` and `docs/README.md` out of step with the package in the first place. If the conventional
plug ever changes, five files change.

**Recorded, not held.** Worker 2 did not do this silently: `### Implementation notes` bullet 2 states
the deviation and its reason (*"the consumer plug is named because a reader whose model has one of these
columns needs it to act"*), and the plan's own `### Implementation discretion items` delegates the exact
wording to Worker 2. That is a defensible call, not an unrecorded one, and `docs/README.md:99` — which
names the absence and delegates the plug entirely to the glossary pointer — is the shape the constraint
described. This therefore routes to **Worker 1's final verification** as the deferred DRY follow-up
`worker-3.md` `### Acceptance gate` permits, not to a Worker 2 re-pass. The cheapest resolution, if
Worker 1 wants one, is striking the parenthetical plug literal from `TODAY.md:162` and letting the
glossary pointer already in the same bullet carry it; that is a one-clause edit in Worker 2's write set
and re-owes no constraint command.

**No other duplication was introduced.** Neither file gained a scalar table, and neither restates the
spec's contract — both point at `docs/GLOSSARY.md#scalar-field-conversion` instead, which is duplication
risk 1 correctly avoided.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list are
unchanged. No `.py` file appears in the diff at all, so no public surface moved.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md`. Proven, not assumed: `git diff --stat -- CHANGELOG.md`
returns empty.

### Documentation / release sanity

This item touches docs only, so `ARTIFACT.md` `### Documentation / release sanity` applies in full.

- **Version strings.** `docs/README.md`'s `**Shipped today** (`0.0.14`)` heading matches
  `pyproject.toml` `version = "0.0.14"` and `django_strawberry_framework/__init__.py`
  `__version__ = "0.0.14"`. The slice changes no version string.
- **Shipped/planned status.** The corrected bullets assert an **absence** at `0.0.14`, which is what
  `CHANGELOG.md:202` records as the breaking change that removed both mappings. No status drift.
- **No obsolete "coming soon" / "planned" / old-version wording** survives in the regions the item
  deliberately updated. Measured across the four consumer docs, per token, occurrences not lines:

  | Token | `README.md` | `GOAL.md` | `TODAY.md` | `docs/README.md` |
  |---|---|---|---|---|
  | `Duration` | 0 | 0 | 1 | 1 |
  | `Binary` | 0 | 0 | 2 | 1 |
  | `duration` | 0 | 0 | 0 | 0 |
  | `binary` | 0 | 0 | 1 | 0 |
  | `timedelta` | 0 | 0 | 1 | 2 |
  | `bytes` | 0 | 0 | 1 | 11 |

  This reproduces the build report's census exactly and extends it by two tokens. Every surviving
  `Duration` / `Binary` occurrence is inside one of this pass's two corrections and asserts the absence.
  `docs/README.md`'s 2 `timedelta` and 11 `bytes` hits were each read: the `timedelta` pair is
  `:477` / `:483` (a Channels `connection_init_wait_timeout` code sample) and the `bytes` hits are the
  keyset-cursor, `max_request_body_bytes`, upload-budget and `UploadMetadata` surfaces — **none is a
  scalar-conversion claim**, so none is falsified.
- **Links introduced by the slice point at existing files.** Independently re-derived with a checker
  written for this review (`docs/builder/temp-tests/r3-spec001/link_scaffold.py`) that strips fences and
  code spans, normalizes each definition path against its own file's directory, and `os.path.exists`-checks it:

  | File | defs | used | undefined | orphan | broken on disk | 10 headers in order | alphabetical within group | inline cross-file links |
  |---|---|---|---|---|---|---|---|---|
  | `TODAY.md` | 25 | 25 | 0 | 0 | **0** | yes | yes | 0 |
  | `docs/README.md` | 36 | 36 | 0 | 0 | **0** | yes | yes | 0 |
  | `docs/SPECS/spec-002-optimizer-0_0_2.md` | 3 | 3 | 0 | 0 | **0** | yes | yes | 0 |
  | `docs/SPECS/spec-001-django_types-0_0_1.md` | 22 | 22 | 0 | 0 | **0** | yes | yes | 0 |
  | `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` | 18 | 18 | 0 | 0 | **0** | yes | yes | 0 |

  The 25/25 and 36/36 rows include this pass's `+1` definition each; the 22/22 and 18/18 rows reproduce
  the plan's and build report's numbers from a second implementation. **The anchor half was checked
  separately**, because a definition can resolve to a real file and a dead fragment:
  `grep -c '^## Scalar field conversion$' docs/GLOSSARY.md` -> **1**, so `#scalar-field-conversion` is
  unambiguous (no GitHub `-1` suffix) and both new definitions land.
- **Archival record preserved.** No file moved in R3; B1-B3's three-direction sweep is a verification of
  an archive that landed before this cycle. Re-checked independently below.
- **Verbatim-copy check.** Not applicable — the slice copies no text from the spec. The shingle scan
  above is the positive evidence: 9- and 10-word maxima are independent authorship, not a drop-in.
- **Script-rendered docs.** `uv run python scripts/build_tree_md.py --check` ->
  `.../docs/TREE.md is up to date.`, exit 0. `grep -n -iE 'scalar_map|duration|binary' docs/TREE.md` ->
  **0 hits**, so no feeding module docstring renders a falsified scalar claim, and the conditional
  docstring-plus-regenerate obligation was correctly not owed.
- **Generated docs were read, not written.** `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html` are dirty
  from the concurrent `DONE-049-0.0.14` wrap and carry no hunk from this item — re-derived, not accepted:
  `grep -rn 'DurationField|BinaryField'` across the tree returns `docs/GLOSSARY.md:1763` and `:1765`
  only, both pre-existing and both **correct** (they already state the absence and both plugs), and
  **zero** hits in `KANBAN.md` / `KANBAN.html`. So A6/A7's "no drift, no ORM edit" conclusion is right,
  and there is correctly no two-consecutive-regenerate evidence to audit.

### Substantive claim re-derived from source (axis 1)

**`SCALAR_MAP` and `FIELD_OUTPUT_TYPE_MAP`.** `ast`-walked myself
(`docs/builder/temp-tests/r3-spec001/derive_maps.py`), handling `ast.AnnAssign` **and** `ast.Assign` so
the walk cannot silently measure zero — both maps are `AnnAssign`, exactly as the build report's last
implementation note warns:

- `SCALAR_MAP` -> **26 entries**, enumerated. `DurationField` present: **False**. `BinaryField` present:
  **False**.
- `FIELD_OUTPUT_TYPE_MAP` -> **2 entries** (`ImageField -> DjangoImageType` before
  `FileField -> DjangoFileType`).

**The raise was executed, and at a stronger scope than the build report's.** Worker 2 drove
`types/converters.py::scalar_for_field` on unbound field instances. The documents claim a raise **at type
creation**, so I built two real `DjangoType` subclasses over models declaring the columns
(`docs/builder/temp-tests/r3-spec001/prove_raise.py`, `DJANGO_SETTINGS_MODULE=config.settings`):

```
DurationField: ConfigurationError at TYPE CREATION -> Unsupported Django field type 'DurationField' on
  DurModel.dur. Add an entry to SCALAR_MAP or exclude this field via Meta.exclude.
BinaryField:   ConfigurationError at TYPE CREATION -> Unsupported Django field type 'BinaryField' on
  BinModel.blob. Add an entry to SCALAR_MAP or exclude this field via Meta.exclude.
```

Both documents' exact claim — *raises `ConfigurationError` at type creation* — is therefore established
at the scope the sentence asserts, not one layer below it.

**The reason clause holds, and it is the one thing in this diff most likely to read as false.**
`TODAY.md:162` says *"Strawberry ships no first-party scalar for `datetime.timedelta` or `bytes`"* and
then names `strawberry.scalars.Base64` — which is first-party and is
`NewType("Base64", bytes)`. That looks self-refuting, so I measured Strawberry's default registry rather
than arguing about it:

```
from strawberry.schema.types.scalar import DEFAULT_SCALAR_REGISTRY
-> NoneType, None, str, int, float, bool, strawberry.scalars.ID, uuid.UUID,
   strawberry.file_uploads.scalars.Upload, datetime.date, datetime.datetime, datetime.time,
   decimal.Decimal, strawberry.scalars.JSON, strawberry.scalars.Base16, Base32, Base64
```

Neither `bytes` nor `datetime.timedelta` is registered; `Base16` / `Base32` / `Base64` are three distinct
`NewType`s over `bytes`, so there is no scalar a bare `bytes` annotation resolves to and no single
encoding the package could pick on the consumer's behalf. **The clause is true as written**, it matches
the identical wording already at `types/converters.py` (module docstring), `docs/GLOSSARY.md`, and
`docs/SPECS/spec-001-django_types-0_0_1.md:176`, and it is recorded here so a later pass does not
"correct" it into a falsehood.

**No overstatement in the other direction.** Both corrections name a recourse: `TODAY.md` names three
(register a `SCALAR_MAP` entry, a consumer annotation override, `Meta.exclude`) and `docs/README.md`
names one plus the glossary pointer. Each of the three is real — the first and third are quoted in the
runtime error message above, and the annotation-override path is
`docs/GLOSSARY.md` `## Scalar field override semantics` #"parallel consumer recourses". Neither document
implies the column type is unusable.

### Sibling sweep, run independently (axis 3)

Not scoped to the build report's file list. `grep -rn -E 'DurationField|BinaryField'` over the whole tree
(`.git`, `.venv`, `node_modules`, `dist`, `docs/shadow`, `__pycache__` excluded), cycle artifacts and
closed-cycle scratch set aside, with every shipped hit read:

| Site | Verdict |
|---|---|
| `TODAY.md:162`, `docs/README.md:99` | this pass's corrections |
| `docs/GLOSSARY.md:1763`, `:1765` | already correct; **no ORM edit owed** |
| `CHANGELOG.md:202` | records the removal as the `0.0.14`-era breaking change; correct |
| `docs/SPECS/spec-001-…:176`, `appx/…-rationale.md:472`, `:490-491` | R2's corrected text; correct |
| `docs/SPECS/spec-037-…:581` | *"`DurationField` / `BinaryField` and other unmapped scalars. They remain…"*; correct, and out of R3's write set |
| `django_strawberry_framework/types/converters.py:53-57` | the module docstring; correct |
| `tests/types/test_converters.py:566-598` | the two pinning tests; present |
| `docs/SPECS/spec-039-…`, `rest_framework/serializer_converter.py`, `tests/rest_framework/test_converter.py` | DRF **serializer** `DurationField` -> `str`, a different subsystem's deliberate mapping; not falsified |
| `django_strawberry_framework/optimizer/lateral_fetch.py:116`, `:122` | `_ARRAY_BINDABLE_PARENT_FIELD_TYPES`, a psycopg parameter-adaptation set keyed by field-class *name*; not a conversion claim |
| `django_strawberry_framework/filters/sets.py:330` | `models.DurationField: {"filter_class": DurationFilter}` in `_PUBLIC_PACKAGE_FILTER_DEFAULTS` — a deliberate mirror of django-filter's table, correct **and** consistent: it becomes reachable precisely when a consumer registers the `SCALAR_MAP` entry the docs now tell them to. **Examined and not a defect**; recorded so a later sweep does not re-flag it |
| `examples/` | **zero** hits — no example model declares either column, so no live surface contradicts the docs |

**Widened past those two tokens**, since a general claim can be falsified without naming them: greps for
`"__all__"` / `every (model )?(column|field)` / `all (model )?fields` across `README.md`, `GOAL.md`,
`TODAY.md`, `docs/README.md` return only `Meta.fields = "__all__"` code samples and the
`FilterSet` / `OrderSet` `"__all__"` shorthand bullets — no document claims every Django column
converts. `examples/fakeshop/test_query/README.md` was read end to end for scalar-conversion claims:
it describes suites and behaviors, states none.

**`README.md` and `GOAL.md` are genuinely zero** on all six tokens (table under Documentation / release
sanity), so leaving both unedited is the right result and not a stopped-early sweep.

### The `spec-002` pointer pass (axis 4)

**C1 — accepted.** The dangle is real and I re-derived it rather than accepting the count table:
`grep -o` occurrence counts give `cut line` **0** in spec-001 / **3** in the rationale, `natural cut`
**0** / **1**, `ever split` **0** / **1**, `lockstep` **0** / **2**. The predicting paragraph is at
`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md:94` (*"The cut line the spec named for itself,
and then took."*, quoting *"If this document is ever split, the optimizer is the natural cut line"*)
inside the entry at `:64`. So a reader following `spec-002:9` to spec-001 finds no prediction.

*Is it a pointer rather than narration?* Yes. The sentence is
``That prediction is recorded in `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`.`` — it names
a location and stops. It does not say the text moved, when, why, or by which pass, which is the exact
test the pass set itself. *Is it in `spec-002`'s register?* Yes, and the precedent is one line above it:
`spec-002:6` reads ``The O4 design record remains in `docs/SPECS/spec-003-…md`; keep detailed O4
rationale there…`` — same "the record lives at `<repo-root-relative path>`" construction, same inline
code span, same flat declarative voice. The full path (rather than `spec-002`'s usual bare sibling
filename) is correct here because the target is one directory deeper.

*The link-convention judgement is right.* `START.md`'s reference-style rule governs markdown **links**;
a code-span path is not one. Re-measured in `spec-002`: **8** spec-filename references, **all** inline
code spans; **3** reference-style link uses, all to `../GLOSSARY.md#…`; **0** inline cross-file links.
My scaffold checker confirms the `<!-- LINK DEFINITIONS -->` block is intact with 3 defs / 3 uses / 0
broken and all 10 group headers present in order. Adding a definition would have made this the file's
only linked sibling reference. No finding.

*Byte proof re-derived independently:* `git show HEAD:… | wc -c` -> **7214**, worktree -> **7305**,
delta **+91**; `len()` of the inserted literal (leading space, trailing period) -> **91**. `git diff
--stat` -> 1 insertion / 1 deletion on one line. Any unreported second edit to this file would have to
net exactly zero bytes. The path was disk-exists-checked (`test -f` -> EXISTS).

**C2 — the no-edit conclusion is sound; I attacked the counter-reading and it loses.** `spec-002:80` is
a `## References` bullet, and I read all five bullets in that section: every one is an *external source
locator* (an upstream file path, three GitHub URLs). The clause *"that motivated bundling the optimizer
with `spec-001-django_types-0_0_1.md` originally"* is a descriptor of **which** upstream discussion is
meant; the bullet's locator is *"issue #572 and PR #583"*. Following it leads to GitHub, so nothing
dangles into spec-001. Two independent confirmations, both re-derived as **occurrence** counts (`grep -o
… | wc -l`, not `grep -c`): `572` occurs **2** times and `583` **2** times in
`docs/SPECS/spec-001-django_types-0_0_1.md` — at `:351` (the derivation) and `:464` (spec-001's own
`## References`) — so **even the counter-reading resolves**, because the PR #583 derivation never left
the spec; and the rationale's `## Provenance of this record` lists that derivation under *"Deliberately
left in the spec by this pass"*, making the carve-out a recorded decision rather than an oversight.
This is **not** a dangling reference talked out of existence: the discharge is falsifiable and it
survived the falsification attempt.

**C3 — the declination is defensible.** The plan authorized closing it as *"assessed, not needed"*
provided the assessment is written down, and it is. The substance checks out too: the obligation it
stood in for is genuinely closed — both lifted rules are contract in spec-001 (`:349`, the local-FK-column
`only()` reason; `:357`, *"applied to the child queryset of every `Prefetch` the planner builds"*), both
re-read on disk this pass. A C3 recording would have been a history sentence in a normative heading, and
the plan's own minimum for this cycle is *a pointer, never new narration*. Declining it is consistent
with the same rule that shaped C1. No finding.

### Dispatched findings checklist — all 16 boxes walked

Every box is `- [x]`. Each tick was audited against the diff or against a recorded measurement I
re-derived; a verification-only box is legitimately ticked on a recorded result.

| Box | Tick justified? | My re-derivation |
|---|---|---|
| A1 | yes — in the diff | `TODAY.md:157` `DurationField` struck; `:162` bullet replaced. Both hunks present |
| A2 | yes — in the diff | `docs/README.md:99` `binary` removed, absence clause added |
| A3 | yes — recorded | 26 / 2 entry counts re-derived by my own `ast` walk; `PositiveBigIntegerField -> BigInt` confirmed at `TODAY.md:158` and `docs/README.md:100` |
| A4 | yes — recorded | D-row sweep re-run and widened (above). Spot-check of the most argumentative row: `DEFERRED_META_KEYS` is exactly `{aggregate_class, fields_class, search_fields}` and `ALLOWED_META_KEYS` has **17** members including `filterset_class` and `orderset_class` — the build report's D4 numbers are exact |
| A5 | yes — verification-only | `build_tree_md.py --check` exit 0, re-run |
| A6 | yes — verification-only | 21 CSV anchors; `check_spec_glossary.py` exit 0; `docs/GLOSSARY.md` scalar entry read and correct |
| A7 | yes — verification-only | `KANBAN.md` carries **0** `DurationField` / `BinaryField` occurrences; card block spot-checked |
| B1 | yes — recorded | `spec-001` reference sweep re-run; confirmed-zero set genuinely zero |
| B2 | yes — recorded | reproduced independently: 22/22 and 18/18, 0 broken (table above) |
| B3 | yes — recorded | `docs/SPECS/appx/` holds exactly the rationale + terms CSV; the spec's companion ref carries the `appx/` prefix; nothing stranded at `docs/` |
| B4 | yes — recorded | both constraint commands re-run: `OK: 21 terms …` exit 0, `OK: 49 done cards …` exit 0 |
| B5 | yes — recorded | `SpecDoc.path` / card identity, quoted read-only in the build report; consistent with the on-disk archived path |
| C1 | yes — in the diff | one insertion, byte-proved |
| C2 | yes — obligation was *verify, fix if broken* | verified resolves; counter-reading attacked and rejected |
| C3 | yes — plan authorizes "assessed, not needed" | assessment present and substantively correct |
| D1 | yes — recorded | **2 occurrences** re-derived (`grep -rEo … | wc -l`), both on `docs/builder/build-001-django_types-0_0_1.md:187`. Zero in package source, `tests/`, `examples/` |

**No box is ticked without a matching implementation or recorded result, and none is silently
un-addressed.** Worth naming: the build report **corrected the plan's own predicted count** from 1 to 2
on D1 rather than inheriting it, and my independent run agrees at 2. That is the cycle's named practice
failure being caught by the discipline written to catch it, not another instance of it.

### Constraint commands and standing invariants

All re-run by me, at this pass:

```
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
    -> OK: 21 terms - all have glossary entries and at least one spec link.      exit 0
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md
    -> OK: 3 terms - all have glossary entries and at least one spec link.       exit 0
uv run python examples/fakeshop/manage.py import_spec_terms --check
    -> OK: 49 done cards have glossary links.                                    exit 0
uv run python scripts/build_tree_md.py --check                                   exit 0
uv run python scripts/check_trailing_commas.py --check TODAY.md docs/README.md \
    docs/SPECS/spec-002-optimizer-0_0_2.md                                       exit 0
git diff --check -- <the same three files>                                       exit 0
```

**Exit 0 is the gate; `49` is the concurrent session's number and is not.**

**Anchor budget unchanged at 21 distinct / 22 body links**, re-derived with
`grep -o '\]\[glossary-[a-z0-9_-]*\]' … | sort | uniq -c`: `configurationerror` is the only anchor used
twice; every other one of the 21 is single-linked. This is the population re-derived, not the two
members an artifact named.

**`AGENTS.md` rule 27 in the spec files.** A raw `path:NN` regex over `spec-001`, `spec-002`, and the
rationale returns exactly **one** hit: the pre-existing
`docs/SPECS/spec-002-optimizer-0_0_2.md:72` upstream `graphene_django/converter.py:308-471` reference,
confirmed identical at HEAD. **Not this cycle's regression, not fixed here**, carried to the deferred
catalog below. The inserted C1 sentence names a file, not a symbol, and adds no `path:NN`. Clean.

### Failability proofs

`None; this pass introduced no new boundary.` — audited and **correct**. The diff adds no guard, cap,
gate, rejection path, or validation branch; it is three markdown edits. `### Failability proofs` is
legally empty, the mandatory re-run floor is arithmetic on an empty set, and **my independent re-run set
is therefore legally empty**. Hot path and floor verification are both `Not applicable` per the plan's
explicit declarations; their absence is not a finding.

### Static helper use

`scripts/review_inspect.py` **skipped**. Reason: `BUILD.md` `### When to run the helper during build`
triggers Worker 3 on a new `.py` file, a touched file under `optimizer/` or `types/`, or 30+/50+ new
logic lines — **no `.py` file is in this item's writable set and none appears in the diff**, so no
trigger fires and there is no repeated-literal or import-boundary evidence to gather. No shadow file was
used or needed.

### What looks solid

- **The two corrections are true at HEAD at the scope they assert**, and the raise was proved at *type
  creation* rather than at the converter helper — a stronger scope than the build report's own proof.
- **The `ast.AnnAssign` warning in `### Implementation notes` is load-bearing and paid off.** A plain
  `ast.Assign` walk of `converters.py` returns nothing for either map; a reviewer taking the obvious
  route would have measured zero and concluded the maps were absent. Flagging it is exactly what the
  Notes-for-Worker-3 section is for.
- **Attribution was done in both directions and holds.** `TODAY.md`'s line-381 hunk (`065` ->
  `DONE-046`) is the concurrent renumber cleanup and was correctly neither reverted nor claimed; the
  157/162 region was proved byte-identical to HEAD before the write. No generated doc was hand-edited,
  and the three dirty generated docs carry zero hits for this item's tokens.
- **The register reads as though it had always been there.** `TODAY.md`'s section already carries
  non-conversion entries (`null=True` -> `T | None`, the Relay `GlobalID` line), so a bolded negative
  bullet does not break the list's established shape, and reusing the `BinaryField` slot preserves the
  ordering. `docs/README.md`'s clause uses the `;` separator the long parenthetical already uses.
- **Both new link definitions are real reference-style links in the right group at the right relative
  depth**, and the two differ only by depth — the convention doing the job it exists for.
- **`README.md` and `GOAL.md` were left alone on measured zeros**, and the zeros were reported rather
  than left as silence.
- **The `spec-002` pass verified a handed-down finding instead of executing it**, and split it 1-edits /
  1-resolves. That is `BUILD.md` `## Claims are proven mechanically` applied to the direction it is
  easiest to skip.

### Temp test verification

Four scratch scripts under `docs/builder/temp-tests/r3-spec001/` (gitignored — confirmed by
`git check-ignore -v`, matching `.gitignore:192 docs/builder/temp-tests/`):

- `derive_maps.py` — `ast` walk over `converters.py` handling `AnnAssign` **and** `Assign`; produced the
  26 / 2 counts and the two absence booleans.
- `prove_raise.py` — builds real `DjangoType` subclasses over `DurationField` / `BinaryField` models;
  produced the type-creation `ConfigurationError` transcript.
- `link_scaffold.py` — independent second implementation of the defs/uses/undefined/orphan/on-disk/
  group-order/alphabetical/inline-link checker. Written fresh rather than copied, so agreeing numbers
  from two implementations are what make 22/22 and 18/18 mean anything.
- `shingle.py` — maximal-shared-shingle scan behind the DRY finding.

**Disposition: none promoted.** No temp test caught a behavior bug — the two permanent tests
(`tests/types/test_converters.py::test_convert_scalar_duration_field_raises_unsupported` and
`::test_convert_scalar_binary_field_raises_unsupported`) already pin the contract, and were confirmed
present. `link_scaffold.py` is the seventh hand-written instance of the same checker in this cycle;
promoting it to `scripts/` remains R2's catalogued maintainer call and this review does not open it.

### Notes for Worker 1 (spec reconciliation)

1. **The DRY finding above is yours to weigh at final verification.** Recorded as a deferred follow-up
   rather than held at `revision-needed`, per `worker-3.md` `### Acceptance gate`. The resolution paths
   are (a) accept as shipped — the plug literal is what a consumer needs to act and `TODAY.md` is the
   capability snapshot they read first; or (b) strike the `SCALAR_MAP[BinaryField] =
   strawberry.scalars.Base64` parenthetical from `TODAY.md:162` and let the glossary pointer already in
   that bullet carry it, a one-clause edit in Worker 2's write set that re-owes no constraint command.
   Either way the count is the fact: **5 shipped sites** for that literal today.
2. **For the final gate's `### Deferred work catalog`, two items carried forward, neither this item's to
   close:**
   - A live bug in `scripts/check_spec_glossary.py::github_anchor` — it slugs heading text without first
     rendering link markup, so a heading that is itself a reference link
     (`## [Scalar field conversion][glossary-scalar-field-conversion]`) slugs to
     `scalar-field-conversionglossary-scalar-field-conversion` and yields a **false negative**. Four
     passes in this cycle have now had to route around it with a private slugger, mine included. Fixing
     it is a `scripts/` change outside this cycle's write set.
   - The pre-existing `AGENTS.md` rule-27 raw `path:NN` at `docs/SPECS/spec-002-optimizer-0_0_2.md:72`,
     naming an out-of-repo upstream file. Confirmed pre-existing at HEAD and correctly not fixed here;
     the symbol-qualified replacement would name a symbol in a package outside this repo.
3. **Examined and explicitly not a defect, recorded so a later sweep does not re-flag it:**
   `django_strawberry_framework/filters/sets.py` `_PUBLIC_PACKAGE_FILTER_DEFAULTS` maps
   `models.DurationField -> DurationFilter`. That looks like it contradicts the new doc text, and it does
   not: the row is a deliberate mirror of django-filter's own table and becomes reachable exactly when a
   consumer registers the `SCALAR_MAP[DurationField]` entry the corrected docs tell them to register.
   No package-source defect was found by this review, so nothing is recorded here under that heading.
4. **`TODAY.md`'s scalar list is a documented subset, and I second the build report's non-edit.** It
   names 9 of `SCALAR_MAP`'s 26 keys and generalizes the rest; the lead-in at `TODAY.md:152` says the
   package "converts these model fields", not "only these". Expanding it into a 26-row table would
   recreate precisely the doc-to-doc duplication the plan's DRY analysis rules out. Left as is.
5. **The anchor budget is untouched and re-measured by me: 21 distinct / 22 body links**, so the final
   gate need not re-derive it.

### Review outcome

`review-accepted`.

Every claim the two documents now make is true at HEAD, measured against source rather than against the
plan or the build report: 26 `SCALAR_MAP` entries with both column types absent, a `ConfigurationError`
raised at type creation for each, a reason clause that survives a check of Strawberry's default scalar
registry, and named recourses that are all real. The sweep did not stop early — `README.md` and `GOAL.md`
are genuinely zero, `docs/GLOSSARY.md` was already correct so no ORM edit was owed, no package docstring
or generated doc states a falsified conversion claim, and the widened search for general
"every-column-converts" claims found none. All 16 checklist boxes are ticked with matching
implementations or re-derived results. The `spec-002` pass fixed one genuine dangle with a pointer in the
file's own register and correctly declined to invent a second, and its no-edit verdict survived a
deliberate attempt to break it.

**One DRY finding is escalated to Worker 1's final verification** rather than held: the plug literal now
has five shipped homes, which the plan's duplication risk 2 aimed to prevent — but Worker 2 recorded the
deviation and its reason, the plan delegated the wording, and the pointer that makes the duplication
optional is present in both files. No High, Medium, or Low finding remains open.

Status set to `review-accepted`.

---

## Final verification (Worker 1)

Fresh spawn; the artifacts are the contract. Read end to end: this artifact (plan, build report, the
interstitial spec-002 pass, Worker 3's review), `bld-001-r1-rationale_move.md` and
`bld-001-r2-spec_reconciliation.md` in full, the build plan, both specs, the rationale companion, and
the standing corpus. **Every number below was produced by the command beside it at the moment it was
written** — this cycle's named practice failure is re-derivation loss, and ten counts were lost to it
across R1 and R2, so nothing here is inherited from the plan, the build report, or the review,
including the numbers they got right.

### Working-tree baseline, re-measured at this pass's open

HEAD is still `fdfb711f`. `git status --porcelain` returns **16 paths — 11 modified, 5 untracked**:

```
 M KANBAN.html          <- concurrent (spec-049 card wrap)
 M KANBAN.md            <- concurrent (spec-049 card wrap)
 M SECURITY.md          <- concurrent
 M TODAY.md             <- R3 Worker 2 (F1) + THIS PASS (the DRY strike) + the concurrent line-381 hunk
 M docs/GLOSSARY.md     <- concurrent (spec-049 card wrap)
 M docs/README.md       <- R3 Worker 2 (F2)
 M docs/SPECS/spec-001-django_types-0_0_1.md          <- THIS CYCLE (R1 + R2), untouched by R3
 M docs/SPECS/spec-002-optimizer-0_0_2.md             <- R3 Worker 1 (C1)
 M docs/spec-049-dependency_ci_hardening-0_0_14.md    <- concurrent
 M examples/fakeshop/db.sqlite3                       <- concurrent
 M uv.lock                                            <- concurrent
?? docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md   <- THIS CYCLE (R1 + R2)
?? docs/builder/bld-001-r1-rationale_move.md                  <- THIS CYCLE
?? docs/builder/bld-001-r2-spec_reconciliation.md             <- THIS CYCLE
?? docs/builder/bld-001-r3-doc_completion_archive.md          <- THIS CYCLE (this file)
?? docs/builder/build-001-django_types-0_0_1.md               <- THIS CYCLE
```

**Membership is byte-for-byte the set Worker 3 measured.** Nothing was reverted, checked out,
restored, or stashed by this pass. This pass wrote exactly three files: `TODAY.md` (one clause
deleted), this artifact, and `docs/builder/worker-memory/worker-1.md`.

### Spec status-line re-verification — both specs

`worker-1.md` `## Spec status-line re-verification` runs on every spawn, and this pass touched
spec-002, so both files were re-read at the top.

- **`docs/SPECS/spec-001-django_types-0_0_1.md`** — confirmed for the **fifth** time in this cycle:
  **there is no status/header block.** Line 1 `# Spec: DjangoType Foundation`, line 2 blank, line 3
  `## Problem statement`, line 7 `## Prior art` (R2's retitle, cited by the rationale's `#prior-art`
  in-page anchor and therefore unrewordable). No target-release, status, owner, or predecessor line
  exists for this build to have falsified, and R3 deleted no predecessor doc a header could point at.
  **No edit owed.**
- **`docs/SPECS/spec-002-optimizer-0_0_2.md`** — same finding, re-derived rather than assumed by
  analogy. Line 1 `# Spec: Optimizer & Reverse-Relation Resolution`, line 2 blank, line 3 `## Purpose`,
  line 4 the purpose sentence, line 6 the O4 extraction pointer, line 8 `## Problem statement`.
  **No status/target-release/owner/predecessor block.** The C1 insertion landed at line 9, inside the
  body, and falsifies nothing above it.

  The file does carry two **status-shaped sections** — `## Current state` (`:16`, *"The foundation
  optimizer architecture has shipped"*, listing O1-O6) and `## Visibility status` (`:63`, *"O1 through
  O6 have shipped. The optimizer is public via `DjangoOptimizerExtension`"*). Both were checked against
  HEAD rather than waved through, because R2's own lesson is that a section whose name is a standing
  promise rots silently: `django_strawberry_framework/__init__.py:32` imports `DjangoOptimizerExtension`
  and `:142` re-exports it in `__all__`, `django_strawberry_framework/optimizer/walker.py` exists, and
  spec-002's own `## Implementation checklist` carries all six `- [x]`. **Both accurate; no edit owed.**
  Recorded rather than left silent so a later pass does not re-derive it — and noted as *out of this
  item's scope to retitle* even if a future cycle judges `## Current state` the same standing-promise
  shape R2 retired from spec-001.

### The escalated DRY finding — decided, and taken here

Worker 3 escalated one DRY finding rather than holding the item, offering two resolutions. **Decision:
apply the strike, and take it in this pass rather than routing it to Worker 2.**

**The measurement first, re-derived, because the finding is a count.** The expression
`SCALAR_MAP[BinaryField] = strawberry.scalars.Base64` occurred at **6 shipped sites** before this edit
(`grep -rno`, `.git` / `.venv` / `dist` / `node_modules` / `__pycache__` and the per-cycle
`docs/builder/` artifacts excluded):

| Site | Role |
|---|---|
| `django_strawberry_framework/types/converters.py:57` | the module docstring — **the source of truth** |
| `docs/GLOSSARY.md:1765` | the capability catalog's `Scalar field conversion` entry |
| `CHANGELOG.md:202` | the `0.0.14` breaking-change record — frozen by `AGENTS.md` rule 21 |
| `docs/SPECS/spec-001-django_types-0_0_1.md:176` | the contract |
| `tests/types/test_converters.py:594` | the docstring of the test that pins the raise |
| `TODAY.md:162` | **this cycle's addition** |

(The bare token `strawberry.scalars.Base64` measures **7** occurrences across those 6 files —
`converters.py` carries two, the prose mention at `:56` and the assignment at `:57`. Worker 3's "five
shipped sites" counted the five non-test documents; both readings are right about different
populations, which is why the population is named here rather than the number alone.)

**Why apply rather than accept.** Three reasons, in order of weight:

1. **The plan fixed the constraint and Worker 2's discretion did not extend to it.** `### DRY analysis`
   duplication risk 2 named this exact outcome — *"A fourth copy of the `DurationField` / `BinaryField`
   explanation … `TODAY.md` and `docs/README.md` get the *fact plus a pointer*, not the reasoning"* —
   and `### Implementation discretion items` delegated **the wording**, not whether the reasoning gets
   another copy. A delegated sentence is not a delegated constraint.
2. **The bullet's own sibling took the constrained shape.** `docs/README.md:99`, written in the same
   pass for the same fact, names the absence and delegates the plug entirely to the glossary pointer.
   Two sibling corrections disagreeing about the same fact's shape is the doc-to-doc divergence this
   item exists to close, one generation earlier.
3. **The parenthetical served half the bullet's readers.** The bullet covers two column types; there is
   no plug literal for `DurationField` (the documented recourse is a consumer-defined scalar), so the
   reader with a duration column had to follow the glossary pointer regardless. The literal bought
   actionability for the binary case only, at the price of a sixth copy of a code-shaped literal that
   changes whenever the convention does.

**Why take it here rather than route it to a Worker 2 pass.** `worker-1.md` `## Scope` forbids Worker 1
*implementing Worker 3 findings*, and that rule is real: it keeps the QA role from becoming the fixer
of unreviewed code. Three things make this the case it does not govern, and the dispatch authorized
`TODAY.md` for exactly this clause:

- It is a **deletion inside a hunk Worker 3 already read and accepted**, not new text. Worker 3 quoted
  the bullet in full, named the clause, and pre-approved the shape (*"a one-clause edit in Worker 2's
  write set that re-owes no constraint command"*). The only thing unreviewed is that the deletion is
  the deletion it claims to be — which is mechanically provable, and proved below.
- The alternative is a Worker 2 apply-changes pass plus a Worker 3 re-review plus a second Worker 1
  final verification, for one parenthetical. `AGENTS.md` rule 5 forbids defer-the-real-fix sequencing;
  a three-spawn loop to delete 92 characters is the sequencing, not the fix.
- The failure modes a review would catch here are all mechanical — unbalanced markup, a dangling
  antecedent, a broken link — and all three gates were re-run after the edit.

**The edit, byte-proved.** Deleted exactly
`` (`SCALAR_MAP[BinaryField] = strawberry.scalars.Base64` is the conventional plug for binary)``,
**92 characters**, from `TODAY.md:162`. Two independent measurements agree:

```
len(deleted literal)                      -> 92
len(prior line) - len(current line)        -> 496 - 404 = 92
reinserting the literal reproduces the prior line byte-for-byte -> True
```

`git diff --stat -- TODAY.md` still reads `4 insertions / 3 deletions` — unchanged from the build
report, i.e. the edit modified an already-modified line rather than opening a new hunk, so the
concurrent session's line-381 hunk is untouched. The resulting bullet:

```TODAY.md:162
- **Absent from the default map:** `DurationField` and `BinaryField` — a column of either type raises
  `ConfigurationError` at type creation, because Strawberry ships no first-party scalar for
  `datetime.timedelta` or `bytes`. The consumer recourses are registering one, a consumer annotation
  override, or `Meta.exclude`. See [`docs/GLOSSARY.md#scalar-field-conversion`][glossary-scalar-field-conversion].
```

All three recourses survive; only the plug literal went. Post-edit census: **5 shipped sites**, and the
one removed is the one the plan said should carry a pointer instead.

**The one-clause reason clause deliberately stays.** *"because Strawberry ships no first-party scalar
for `datetime.timedelta` or `bytes`"* is a fact about upstream, not a maintenance-coupled literal;
Worker 3 measured its longest shared run at 9 words against `spec-001:176`, i.e. independent
authorship. Removing it would leave the bullet asserting a refusal with no reason at all, which is the
shape a future editor "corrects" by re-adding the mapping. Recorded so a later pass does not strike it.

### Dispatched findings checklist — all 16 boxes re-audited

Walked every box against the working-tree diff and my own re-derivations, not against the build
report's or the review's account of them. **All 16 are `- [x]`; none is over-ticked, none is
under-ticked, no box changed state this pass, and no box is left `- [ ]`, so no deferral reason is
owed under `### Spec changes made (Worker 1 only)`.**

| Box | Verdict | My independent evidence |
|---|---|---|
| A1 | **landed** | `git diff -- TODAY.md`: `:157` `DurationField` struck from the date/time bullet; `:162` bullet replaced. Both hunks in the diff |
| A2 | **landed** | `git diff -- docs/README.md`: `binary` removed from the `**Shipped today**` list at `:99`, absence clause + glossary pointer added |
| A3 | **recorded result, verified** | own `ast` walk handling `AnnAssign`: `SCALAR_MAP` **26 entries**, `DurationField` present `False`, `BinaryField` present `False`; `FIELD_OUTPUT_TYPE_MAP` **2 entries** (`models.ImageField`, `models.FileField`, image first) |
| A4 | **recorded result, verified** | spot-checked the two most argumentative rows: `DEFERRED_META_KEYS` is exactly `{aggregate_class, fields_class, search_fields}` (**3**) and `ALLOWED_META_KEYS` has **17** members including both `filterset_class` and `orderset_class` (D4); `PositiveBigIntegerField -> BigInt`, no `int`, in both corrected docs (D16) |
| A5 | **verification-only** | `uv run python scripts/build_tree_md.py --check` -> `docs/TREE.md is up to date.`, exit 0, re-run this pass. No docstring edit owed; none made |
| A6 | **verification-only** | all **21** terms-CSV anchors resolved against `docs/GLOSSARY.md`'s **147** `## ` headings by my own slugger that renders link markup **before** slugging; **0 unresolved** |
| A7 | **verification-only** | `KANBAN.md:4901-4988` re-read. The **3** `(historical)` package-file rows (`converters.py`, `optimizer.py`, `types.py` at the package root) are all **absent on disk** — exactly what the marker asserts and exactly D1; the 4 linked rows and all 6 `#### Files likely touched` entries exist; `#### Decision` (*"Deferred Meta keys are rejected"*) verified against `types/base.py`; `#### Glossary terms` is the same 21 |
| B1 | **recorded result, verified + corrected** | own per-file occurrence sweep of the token `spec-001`. **`docs/SPECS/spec-002-…` now measures 6, not the build report's 5** — C1's inserted sentence names the rationale *filename*, which contains the token. Not a defect; the delta is this pass's own edit. Other files: `KANBAN.md` 4, `KANBAN.html` 3, `spec-005` 4, `spec-006` 1, `spec-037` 10, spec-001 8 (self), rationale 70 (self). **Confirmed-zero set measured file by file and genuinely 0 across all 8** (`README.md`, `GOAL.md`, `TODAY.md`, `AGENTS.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/README.md`, `CHANGELOG.md`) |
| B2 | **recorded result, verified** | third independent implementation of the scaffold checker: spec-001 **22 defs / 22 used**, rationale **18 / 18**, spec-002 **3 / 3**, `TODAY.md` **25 / 25**, `docs/README.md` **36 / 36**; **0 undefined, 0 orphan, 0 inline cross-file links** everywhere; **0 broken on-disk targets** (my checker additionally flagged 3 `https://` defs in `docs/README.md` as "not on disk" — an artefact of my own URL handling, not a defect, and named here so it is not mistaken for one later) |
| B3 | **verification-only** | `ls docs/SPECS/appx/` returns exactly the rationale and the terms CSV; `ls docs/ \| grep spec-001` returns nothing, so nothing is stranded at the `docs/` root; the spec's companion definition carries the `appx/` prefix (`AGENTS.md` rule 26) |
| B4 | **verification-only** | `csv.DictReader`: fieldnames `term, anchor, notes`; **21 data rows, 21 distinct anchors, 0 duplicates** — the uniqueness `import_spec_terms` requires. Both constraint commands re-run and quoted below, both exit 0 |
| B5 | **verification-only** | fakeshop ORM, read-only: `Card.objects.get(number=1)` -> `DONE-001-0.0.1` / `Done` / `0.0.1 (alpha)` / *DjangoType core foundation*; `glossary_links` **21**; `spec.path` `docs/SPECS/spec-001-django_types-0_0_1.md`, **exists on disk `True`** |
| C1 | **landed** | in the diff, one sentence at `:9`. Dangle re-confirmed independently: `cut line` / `natural cut` / `ever split` measure **0** occurrences in spec-001 |
| C2 | **obligation was *verify, fix if broken*; verified resolves** | re-derived rather than accepted: `572` occurs **2** times and `583` **2** times in spec-001 (`:351` the derivation, `:464` its own `## References`), so the cited discussion never left the spec and even the counter-reading resolves. The rationale's `## Provenance of this record` records the carve-out as a **decision** |
| C3 | **plan authorizes "assessed, not needed"; assessment present and correct** | both lifted rules re-read on disk: the O5 local-FK-column reason at spec-001 `:349` and the O6 clause *"applied to the child queryset of **every `Prefetch` the planner builds**"* at `:357`. The obligation the recording stood in for is genuinely closed |
| D1 | **recorded result, verified** | `grep -rEno` -> **2 occurrences**, both on `docs/builder/build-001-django_types-0_0_1.md:187`, which names both patterns in one sentence. **Zero in package source, `tests/`, or `examples/`**, so the `revision-needed` trigger does not fire |

Two notes worth carrying rather than burying. **B1's 5 -> 6 is the checklist working**: a verification
count measured before an interstitial edit and re-measured after it *should* move, and a pass that
inherited the number would have reported a stale one as current. And **D1's 2-vs-1** — the build report
corrected the plan's own predicted count and my run agrees at 2 — is this cycle's dominant failure mode
being caught by the discipline written to catch it, in the check written to catch it.

### Constraint commands, re-run after this pass's edit

```
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md
    -> OK: 21 terms - all have glossary entries and at least one spec link.      exit 0
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md
    -> OK: 3 terms - all have glossary entries and at least one spec link.       exit 0
uv run python examples/fakeshop/manage.py import_spec_terms --check
    -> OK: 49 done cards have glossary links.                                    exit 0
uv run python scripts/build_tree_md.py --check
    -> .../docs/TREE.md is up to date.                                           exit 0
uv run python scripts/check_trailing_commas.py --check TODAY.md                  exit 0
git diff --check -- TODAY.md                                                     exit 0
```

**Exit 0 is the gate. `49` is the concurrent session's `DONE-049-0.0.14` wrap and is not.** No `.py`
file was touched by this pass, so no `ruff` invocation was owed or made; no `pytest`, with or without
`--cov*`.

**Anchor budget re-derived, not inherited** (`grep -o '\]\[glossary-[a-z0-9_-]*\]' … | sort | uniq -c`):
**21 distinct anchors / 22 body links**, `configurationerror` the only anchor linked twice, every other
one of the 21 single-linked. Unchanged, as expected from a cycle whose R3 edits no spec-001 prose.
Byte counts at close: spec-001 **44,596**, rationale **62,465**, spec-002 **7,305**, `TODAY.md`
**42,512** (HEAD **42,080**).

### Did the item deliver what the maintainer asked?

The brief: *"the documentation needs to be finished and then the spec needs to be archived."*

**The documentation is finished, on the spec-001 surface, and the last two consumer-visible falsehoods
were in files no earlier pass in this cycle had opened.** Evidence:

- The spec itself is the deliverable of R1 (deliberation moved to a keyed companion; `52,341 -> 42,483`
  bytes at R1's close, `44,596` now) and R2 (18 drift rows reconciled plus an end-to-end read that
  found a cross-section contradiction no drift row could name).
- The **consumer-facing** layer is R3's, and it was wrong in two places: `TODAY.md` promised
  `DurationField -> Python-native time types` and `BinaryField -> bytes`, and `docs/README.md` listed
  `binary` among shipped scalar conversions. Both are false at HEAD — `SCALAR_MAP` has **26** entries
  and neither column type is among them; the raise was executed at **type creation**, the scope the
  sentences assert. Both fixed.
- The sweep did not stop at the two known rows: the D1-D18 set was re-run across `TODAY.md`,
  `docs/README.md`, `README.md`, and `GOAL.md` with the **zeros reported as results**, and a widened
  search for general *"every column converts"* claims found none. `README.md` and `GOAL.md` are
  genuinely zero on every token and were correctly left unedited.
- The three generated docs were **read, not written**, and correctly so: `docs/GLOSSARY.md`'s scalar
  entry already stated the absence and both plugs, `KANBAN.md`'s card carries zero
  `DurationField` / `BinaryField` occurrences, `docs/TREE.md --check` is clean and renders no scalar
  claim at all. No ORM edit was owed, so no two-consecutive-regenerate evidence exists to audit — the
  correct question was whether A6/A7 *should* have found drift, and independently they should not.

**The boundary of that claim, stated rather than implied:** "finished" means the spec-001 surface as
enumerated by R2's drift rows plus the scalar / file-output / relation claims in the four consumer
docs. This item did not re-audit documentation unrelated to spec-001, and does not assert it is
correct.

**The archive is complete in all three cross-reference directions, in the kanban DB, and in the
terms-CSV chain** — and it landed *before* this cycle opened, so R3 verified rather than performed it.
Each leg re-derived by me this pass, not accepted:

| Leg | Result |
|---|---|
| Direction 1 — references **TO** spec-001 | every hit outside the spec family is a generated kanban link (`KANBAN.md` 4 occurrences at `:146` / `:4908`, `KANBAN.html` 3) or a sibling-spec filename resolving inside `docs/SPECS/`; the only real link definition is `spec-037:1830` and it resolves. The 8-file confirmed-zero set is measured zero |
| Direction 2 — references **INSIDE** the moved files | spec-001 22/22 and rationale 18/18 link definitions, 0 undefined, 0 orphan, **0 broken on disk** at their archived depth |
| Direction 3 — the **companions** | `…-terms.csv` and `…-rationale.md` both at `docs/SPECS/appx/`; nothing spec-001-related stranded at `docs/`; the spec's own companion reference carries the `appx/` prefix |
| Kanban DB | `SpecDoc.path` already reads the archived path and the file exists; card is `DONE-001-0.0.1` / `Done` / `0.0.1`; `glossary_links` 21 |
| Terms-CSV chain | 21 rows / 21 distinct anchors / 0 duplicates; `check_spec_glossary` and `import_spec_terms --check` both exit 0 |

One asymmetry worth naming: `AGENTS.md` rule 26 says the archive move is performed by *the next spec's
author* running `docs/SPECS/NEXT.md` Step 8, so the move predates this cycle by construction. What this
cycle owed the archive was the **companion** rule 26 also names — the `-rationale.md` sitting beside the
`-terms.csv` in `appx/` — and R1 produced it directly at the archived location rather than at `docs/`
and moved after. The archive is complete in the sense the rule defines, and it is complete *because* R1
wrote the missing companion, not merely because the earlier move happened to be right.

### DRY check against prior accepted items

No new duplication beyond the finding resolved above, and the resolution reduced the count from 6 sites
to 5. Neither corrected document gained a scalar table or a restatement of the spec's contract; both
point at `docs/GLOSSARY.md#scalar-field-conversion`, which is duplication risk 1 correctly avoided. The
C1 insertion adds a pointer, not a second copy of the prediction.

**One live duplication is deliberately not resolved and must not be re-flagged:** the two lifted
optimizer rules in spec-001's `## N+1 strategy` sit beside the PR #583 carve-out that is their reason.
Those three are one decision (rationale, `### `## N+1 strategy`` entry, in bold, re-confirmed present
this pass at `:710-715`). Splitting them is the failure; the binding constraint is in the catalog below.

### Failability proofs / hot path / floor verification

- **Failability proofs.** `None; this pass introduced no new boundary.` Audited and correct for the
  whole of R3: the item's entire diff is Markdown. My own pass deletes 92 characters of prose. The
  mandatory re-run floor is arithmetic on an empty set.
- **Hot-path budget.** `Not applicable; plan declares no hot path.` The build plan declares
  `Hot-path declaration: none` cycle-wide and R3 changes nothing that runs per request, resolver, row,
  connection, or outbound message.
- **Floor verification.** `Not applicable; plan declares floor-verification scope none.` No Django /
  Strawberry / channels integration seam is touched. The final gate's confirmation duty for this cycle
  is satisfied by the plan's declaration, and `bld-001-final.md` writes
  `No floor-verification scope declared.`

### Deferred work catalog — handoff to `bld-001-final.md`

`BUILD.md` `## Final test-run gate` makes Worker 1 the only author of `### Deferred work catalog` and
requires it to be built by walking every artifact's spec-reconciliation and notes sections. R3 is the
last item-level pass, so the cycle's deferrals are consolidated here and the gate may lift them
wholesale. **Every item below was re-verified as still true at this pass, by the command quoted** —
a catalogued deferral inherited without re-checking is how a closed item gets carried forward as open.

1. **Live bug: `scripts/check_spec_glossary.py::github_anchor` slugs heading text without rendering
   link markup first.** *Source: R2 `### Notes for Worker 1` item 8; R3 plan `### Implementation
   discretion items`; R3 review `### Notes for Worker 1` item 2.* **Re-verified by execution this
   pass**, not by reading: `github_anchor("[Scalar field conversion][glossary-scalar-field-conversion]")`
   returns `scalar-field-conversionglossary-scalar-field-conversion` — the brackets are stripped as
   non-word characters instead of the link being rendered — where the correct slug is
   `scalar-field-conversion`. **Scope, measured so the priority is not overstated:** `docs/GLOSSARY.md`
   carries **0** headings with link markup, so the shipped `check_spec_glossary` run is *unaffected
   today*; **7** headings across `docs/SPECS/` do carry it, `docs/SPECS/spec-001-django_types-0_0_1.md:142`
   among them, so any tool reusing the function to slug a **spec** heading gets a false negative. The
   fix is two lines (render `[text][ref]` and `[text](url)` to `text` before slugging). No spec line
   licenses the deferral; it is out of the cycle's write set because `scripts/` is. **Owner: maintainer.**
2. **Promote one corrected link / anchor / overlap checker into `scripts/`.** *Source: R1
   `### Notes for Worker 1` item 11 (the shingle/overlap scanner); R2 item 4 (the link-scaffold
   checker); R3 review `### Temp test verification`.* Every pass in this cycle wrote its own private
   implementation — including this one — and the two artifacts that tried to number the instances
   disagree, which is itself the argument: the recurring cost is the re-implementation, not the count.
   Item 1 above is the concrete defect that repetition has been routing around, so the two are one
   piece of work. The checker every spec-plus-rationale pair now owes: link scaffold (defs / uses /
   undefined / orphan), the 10 canonical group headers in positional order, alphabetical order within
   group, on-disk resolution of every def target with the fragment stripped **and URLs excluded**,
   in-page anchors on a slugger that renders link markup before slugging, an inline-cross-file-link
   sweep, a rule-27 raw-`path:NN` sweep, and a maximal-shared-shingle scan (the only thing that turns
   *"it was a move, not a copy"* into a measurement). **Owner: maintainer** — new scope, not this
   cycle's.
3. **Pre-existing `AGENTS.md` rule-27 violation: raw `path:NN` at
   `docs/SPECS/spec-002-optimizer-0_0_2.md:72`.** *Source: R3 spec-002 pass `### Notes for Worker 1`
   item 1; R3 review `### Notes for Worker 1` item 2.* The `## References` bullet reads
   ``graphene-django relation resolver wrap: `/Users/…/site-packages/graphene_django/converter.py:308-471`.``
   **Re-verified identical at HEAD this pass** (`git show HEAD:… | sed -n '72p'`), so it is not this
   cycle's regression. Not fixed because the symbol-qualified replacement names a symbol in an
   **upstream package outside this repo**, so deriving it is real work with a real chance of naming the
   wrong symbol — this cycle's catalogued failure mode. **Owner: a future spec-002 cycle's Worker 1, or
   the maintainer.**
4. **Test-surface gap: nothing pins `OptimizerHint.prefetch(obj)`'s interaction with a custom
   `get_queryset`.** *Source: R2 `### Notes for Worker 1` item 3.* **Re-verified this pass:**
   `tests/optimizer/test_hints.py` contains **0** occurrences of `get_queryset`, and
   `django_strawberry_framework/optimizer/hints.py:198` defines `prefetch(cls, obj: Prefetch)`. The
   behaviour is **deliberate** — a consumer-supplied `Prefetch` is used verbatim, so the hinted child
   queryset bypasses `utils/querysets.py::apply_type_visibility_sync`
   (`optimizer/walker.py::_apply_hint` #"Consumer-supplied Prefetch objects commonly close over") — and
   it is unpinned **in either direction**, which is precisely why it is cheap insurance: an unpinned
   deliberate divergence on a data-isolation path is indistinguishable from a bug to the next reader.
   Licensed by the build plan's build-wide context flag *"No source or test file changes in this
   cycle"*; Worker 3's evidence is `docs/builder/temp-tests/r2b2-spec001/test_hint_visibility.py`
   (gitignored, two rows, one a positive control). **Owner: the next optimizer cycle, or a maintainer
   call — never a spec-001 item.**
5. **Binding constraint on any later cycle that re-homes the two lifted optimizer rules into
   `spec-002`.** *Source: R1 `### Notes for Worker 1` item 4; R2 item 1's last bullet; R3 spec-002 pass.*
   The O5 `only()` reason (spec-001 `:349`) and the O6 every-`Prefetch` visibility clause (`:357`) sit
   beside the PR #583 carve-out (`:351`) that is their reason. **Those three are one decision:** a cycle
   moving them must re-home the carve-out with them and delete all three from spec-001 **in the same
   change**, or the duplication R2 exists to remove comes straight back. Durable record, re-confirmed
   present this pass, at rationale `:710-715` in bold. **Owner: whoever opens the next spec-002 cycle.**
6. **Drift row D13 — the cycle's one checklist box that closed `- [ ]`, and no work is owed.**
   *Source: R2 `### Spec changes made (Worker 1 only)` and its checklist audit.* The row's contract —
   that the spec no longer claims fakeshop declares no M2M field — was discharged by **R1's rationale
   move**, not by R2's diff, so the box records what actually happened rather than claiming a diff it
   did not have. The durable reason is in the rationale's `### Drift rows that changed nothing, and
   why` (`:852-859`), **re-confirmed present this pass**, carrying the HEAD evidence
   (`library.Book.genres` / `alt_branches`, `tests/types/test_definition_relations.py`). Listed here so
   a later reader does not mistake an open box for open work. **No owner; closed.**
   *(Rows D1-D12 and D14-D18 all landed corrections; R3's own 16 boxes are all `- [x]`.)*
7. **`TODAY.md`'s scalar list is a documented subset, deliberately.** *Source: R3 build report
   `### Notes for Worker 1` item 2; R3 review item 4.* It names 9 of `SCALAR_MAP`'s 26 keys and
   generalizes the rest; the lead-in at `TODAY.md:152` says the package *"converts these model fields"*,
   not *"only these"*. **Not drift and not an omission.** Expanding it into a 26-row table would recreate
   exactly the doc-to-doc duplication that put `TODAY.md` out of step with the package in the first
   place. If a later cycle wants it settled either way, the site is that lead-in sentence, never the
   spec. **Recorded so it is not "fixed".**
8. **Examined and explicitly not a defect:** `django_strawberry_framework/filters/sets.py:330`
   `_PUBLIC_PACKAGE_FILTER_DEFAULTS` maps `models.DurationField -> DurationFilter`, which reads as
   contradicting the corrected docs and does not: the row is a deliberate mirror of django-filter's own
   table and becomes reachable exactly when a consumer registers the `SCALAR_MAP[DurationField]` entry
   the corrected docs tell them to register. *Source: R3 review `### Sibling sweep`.* **Recorded so a
   later sweep does not re-flag it.**
9. **Process lesson for whoever reconciles the next spec, carried because it cost a defect to learn.**
   A reconciliation organized by **claim** cannot see a contradiction between two **sections** — it
   belongs to no drift row, no finding, and no diff hunk — and neither can a review auditing the same
   fragments. **Read the whole document once, in order, at the end.** R2's gate did, in one pass, and
   found a defect three builds and three reviews had each looked straight past, in text they had
   themselves written. *Source: R2 `### Notes for Worker 1` item 9.* Belongs to closeout rather than to
   a future card, and is recorded here because closeout reads this file.

*(Two items earlier artifacts flagged are **not** carried, deliberately: the anchor budget and the
`import_spec_terms` done-card number are standing facts re-measured every pass, not deferred work.)*

### Summary

R3 is accepted. The item's own axis turned out not to be the archive — every archive leg was already
green when R3 planned and is green again now, re-derived here in all three cross-reference directions
plus the kanban DB and the terms-CSV chain — but the **consumer-facing** documentation, which no
earlier pass in this cycle had opened, was promising two scalar conversions the package refuses. Both
are corrected at the scope the sentences assert: a `ConfigurationError` at **type creation**, proved by
building real `DjangoType` subclasses, not merely by a missing dict key. The interstitial Worker 1 pass
fixed one genuine dangling reference in `spec-002` with a pointer in that file's own register and
correctly declined to invent a second, its no-edit verdict on `:80` surviving a deliberate attempt to
break it here as well as in review.

The one escalated DRY finding is resolved by applying it: the `SCALAR_MAP[BinaryField] =
strawberry.scalars.Base64` plug literal went from **6 shipped sites to 5**, and the site removed is the
one the plan had already ruled should carry a pointer instead. The deletion is byte-proved at 92
characters and re-owed no constraint command; all six gates are green after it.

All **16** checklist boxes are `- [x]` with matching implementations or re-derived results, none
over-ticked, none under-ticked, none left open, so no deferral reason is owed. Both specs' opening
lines were re-read: neither carries a status/header block, and spec-002's two status-shaped sections
were checked against HEAD rather than assumed. Nine deferrals are consolidated above for the final
gate, each re-verified as still true rather than inherited — including the `github_anchor` bug, which
this pass reproduced by execution and scoped honestly (0 affected GLOSSARY headings today, 7 affected
spec headings).

One measurement worth carrying past this cycle: the staged-anchor sweep returns **2 occurrences on 1
matching line**, because the build plan's own checklist text at
`docs/builder/build-001-django_types-0_0_1.md:187` names both patterns in one sentence. The plan
predicted 1, the build report corrected it to 2, and my run agrees at 2 — the cycle's dominant failure
mode caught by the check written to catch it. A future cycle re-running this sweep against its own plan
will hit the same off-by-one.

### Spec changes made (Worker 1 only)

**No spec file was edited by this pass.** `docs/SPECS/spec-001-django_types-0_0_1.md`,
`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`, and
`docs/SPECS/spec-002-optimizer-0_0_2.md` were all read this pass and written by none of it — proven,
not asserted: `git status --porcelain` shows spec-001 as ` M` from R1+R2 and the rationale as `??`,
spec-002 as ` M` from the interstitial C1 pass, and this pass's only `Edit` call targeted `TODAY.md`.
No spec-001 anchor was at risk; both constraint commands were re-run regardless and are quoted above.

**The one file this pass wrote, recorded here because this is the section a later reader searches:**

| File | Line | Change | Reason | Triggered by |
|---|---|---|---|---|
| `TODAY.md` | 162 (`## Package scalar conversions`) | Deleted the 92-character parenthetical `` (`SCALAR_MAP[BinaryField] = strawberry.scalars.Base64` is the conventional plug for binary)``; the three consumer recourses and the glossary pointer are unchanged | The plan's `### DRY analysis` duplication risk 2 forbade a further copy of the `DurationField` / `BinaryField` reasoning in this file; the literal had reached **6** shipped sites and the bullet's own sibling correction in `docs/README.md` had taken the constrained shape. Byte-proved: 92 characters, reinsertion reproduces the prior line exactly | R3, Worker 3's escalated DRY finding |

**Checklist boxes left open, with deferral reasons: none.** All 16 boxes in
`### Dispatched findings checklist` are `- [x]` and every tick was audited against the diff or against
a measurement re-derived in this section.

### Final verification outcome

`final-accepted`.

Item R3 is complete, and with it the spec-001 residual cycle's three items. Worker 0 may mark the
plan's R3 box and dispatch the final test-run gate, which reads `### Deferred work catalog` above and
writes `No floor-verification scope declared.` per the build plan's declaration.
