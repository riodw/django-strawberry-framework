# Package build plan: upload_file_image_mapping / 0.0.11 (037)

Spec source: `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` (ARCHIVED — the spec shipped in `0.0.11` and was moved to `docs/SPECS/` by a later spec's NEXT.md Step 8 sweep; it is the cycle's contract in place)
Target release: `0.0.11` (shipped; the on-disk package is `0.0.15`)
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Ownership partition: none; sequential slices.
Hot-path declaration: none. No slice in this cycle adds runtime cost — the cycle's writable surface is the spec, its new rationale companion, and (only if a conformance gap is proven) package `.py` source.
Floor-verification scope: none by default. No slice is planned to change a Django / Strawberry integration seam; if Slice 2 proves a code gap and a builder lands source, Worker 1 re-declares the scope in that slice's artifact before the final gate.
Pre-flight: passed with recorded deviations on 2026-09-01 (see `## Pre-flight record`).

> **Cycle artifacts retired.** The six per-round `bld-037-*.md` artifacts this plan names were
> deleted when the cycle closed; only this plan and the final report
> `docs/builder/bld-037-final.md` survive on disk. All six read `Status: final-accepted` before
> deletion and every one is recoverable in full from the cycle's commit:
> `git show f9ae3f93:<path>`. Treat every retired `bld-037-*.md` path below as
> **commit-resolvable rather than disk-resolvable** -- they are retired records, not dead links.
> The retired six are `bld-037-slice-0-rationale_extraction.md`,
> `bld-037-slice-1-code_conformance.md`, `bld-037-slice-2-spec_reconciliation.md`,
> `bld-037-integration.md`, `bld-037-review-1-residue_repair_spec.md` and
> `bld-037-review-1-residue_repair_source.md`. The cycle-scoped worker-memory files are
> git-ignored scratch and were not preserved.

## Cycle shape: a residual-reconciliation cycle, not a feature build

`spec-037` is **shipped**. Its four slices were built and final-accepted at `0.0.11`
(commits `15a258b2`, `aec1bd4e`, `66d01b4a`, `4dca5ec9`, archived by `7c7dbcce` /
`0f8d3d86`). This cycle discharges the two obligations that were never closed:

1. The spec has a `…-terms.csv` companion at `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-terms.csv`
   but **no `…-rationale.md` sibling**. `docs/builder/BUILD.md` `## Spec rationale extraction`
   makes that file the first substantive action of every build; `spec-037` predates the
   rule's enforcement. Slice 0 closes the gap, matching the shape of the `034` / `035` / `036`
   companions.
2. Nobody has checked the shipped spec against `HEAD`. Two later cards changed the surface
   `spec-037` describes, and neither edited the spec. The spec is therefore a false
   description of the code in at least the `path` subfield, and possibly elsewhere.

The cycle's question is the maintainer's, stated as three tests every finding is graded against:

- **Was anything in the spec never built?** A Decision, a Slice-checklist sub-check, or a
  Definition-of-done item with no counterpart in `django_strawberry_framework/` is a
  **dropped feature** and the code is what changes.
- **Did the code deviate from the spec at ship time?** The spec is the contract; a divergence
  the build introduced is graded on which one is right, and the losing side changes.
- **Did a later card change the contract deliberately?** Then the code stands and the **spec
  is rewritten to state the shipped contract directly** — no amendment block, no "as of
  spec-048" hedge (`BUILD.md` `## Spec rationale extraction`: the spec is a contract, not a
  changelog). *What* changed, *why*, and *what it replaced* land in the rationale companion
  as a `**Post-ship:**` bullet under the owning Decision.

**Scope fence (maintainer-set, this cycle only).** The writable surface is **spec files and
package `.py` source**. No closeout-agentflow edits: `docs/GLOSSARY.md`, `KANBAN.md`,
`KANBAN.html`, `docs/TREE.md`, `CHANGELOG.md`, `TODAY.md`, `README.md`, `GOAL.md`, the kanban
DB and `docs/builder/BUILD.md` / `worker-*.md` are **out of scope** and no worker touches them.
No closeout retrospective runs. Every artifact this cycle creates carries `037` in its filename.

## Pre-flight record

Run 2026-09-01 against `docs/builder/worker-0.md` `## Pre-flight procedure`.

| Step | Result |
| --- | --- |
| 1. Working-tree baseline explicit | **Deviation recorded, not resolved.** 103 paths dirty at start, none this cycle's. See `## Baseline-dirty out-of-scope files`. |
| 2. `scripts/review_inspect.py` runs | Pass. `uv run python scripts/review_inspect.py django_strawberry_framework/types/converters.py --output-dir docs/shadow` exit 0, both output files written. |
| 3. Build artifacts reset | **Deviation.** No `build-037-*` / `bld-037-*` path exists (all seven verified free before creation). `docs/builder/bld-003-final.md` is a **committed** artifact of the immediately-preceding `spec-003` cycle (commit `20a9752f`) and was **left in place** — deleting a committed record of another cycle is the one irreversible pre-flight mistake the step warns about, and this tree carries concurrent sessions. |
| 4. `.gitignore` lists the scratch paths | Pass. `docs/builder/worker-memory/`, `docs/shadow/`, `docs/builder/temp-tests/` all listed. |
| 5. Scratch directories cleared | **Deviation, deliberate.** Not cleared. `docs/shadow/` and `docs/builder/worker-memory/` carry the `035` / `036` cycles' output and this tree is under concurrent work (`AGENTS.md` rule 34). Memory files are append-only and carry their own consolidation rule; `docs/shadow/` is regenerable per file on demand. Workers are told in-dispatch that memory predates this cycle. |
| 6. Spec-doc consistency check | Pass. `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` → `OK: 20 terms - all have glossary entries and at least one spec link.` |
| 7. Spec rationale extracted | **Open — this is Slice 0.** The whole reason the cycle exists. No later slice dispatches until Slice 0 is `final-accepted`. |

## Baseline-dirty out-of-scope files

103 paths were already modified or untracked when this cycle began, from a concurrent session
(the shape — `django_strawberry_framework/utils/*`, a new untracked
`django_strawberry_framework/utils/canonical.py`, and matching `tests/utils/*` — reads as a
boundary/DRY consolidation pass). **No worker edits or reverts any of them**, and no worker
treats their churn as this cycle's output. The full list is `git status --short` at cycle start;
the shape is:

- 55 modified files under `django_strawberry_framework/` (incl. `mutations/inputs.py`,
  `mutations/resolvers.py`, `rest_framework/inputs.py`, `forms/inputs.py` — files this cycle
  READS for conformance and must therefore diff against `git show HEAD:<path>` rather than
  assume the working copy is `HEAD`).
- 4 modified docs (`README.md`, `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`) —
  out of scope by the fence above as well as by rule 34.
- 42 modified test files across `tests/` and `examples/fakeshop/`.
- 2 untracked: `django_strawberry_framework/utils/canonical.py`,
  `docs/bug_hunt/bug_hunt-0_0_15.md`.

**The list is dated, and the population grew while this cycle ran.** The final gate measured
**114** such paths, three of them new since cycle start (`GOAL.md`, `docs/feedback2.md` — empty at
`HEAD` and filled to 276 lines by a concurrent bug-hunt session at 19:48, before this cycle's first
write — and one example/test file). None is this cycle's. The count above is the cycle-start
observation and stands as one; the fence it expresses covers whatever the concurrent session owns
at the moment a worker reads it, not a frozen list.

**Consequence for conformance grading.** `django_strawberry_framework/types/converters.py`,
`types/resolvers.py`, `types/finalizer.py`, `types/base.py` and `scalars.py` are **clean** at
baseline, so the read side and the scalar re-export are gradeable against the working copy
directly. `mutations/inputs.py` and `mutations/resolvers.py` are **dirty**, so any conformance
claim about them is stated against `git show HEAD:<path>` into a scratch path outside the repo,
with the command quoted (`BUILD.md` `## Claims are proven mechanically, never accepted on prose`).

## Worker-0 verification pass (findings carried into dispatch)

`BUILD.md` `### Worker 0 verifies every finding against source before dispatching` — every
finding below was read out of source before this plan was written, so no worker re-derives it.
Each is a **verified observation**, not an instruction: the grading is Worker 1's.

**Built and conformant (no code change owed).**

- `types/converters.py::_safe_file_attr` exists under exactly the spec's name, with the spec's
  narrow catch list `(ValueError, OSError, NotImplementedError)`, and its docstring records the
  `SuspiciousFileOperation` propagation carve-out Decision 4 pinned.
- `types/converters.py::FIELD_OUTPUT_TYPE_MAP` exists with `models.ImageField` listed **before**
  `models.FileField`, and `SCALAR_MAP` still carries `models.FileField: str` /
  `models.ImageField: str` — the Decision 3 split shipped intact.
- `types/converters.py::_field_output_type_for` is the single MRO-walk site, shared by
  `convert_field_output`, `resolvers._attach_file_resolvers` and
  `base._validate_filesystem_path_targets`.
- `types/converters.py::convert_field_output` applies the default-nullable rule as
  `True if force_nullable is None else force_nullable`, so `Meta.required_overrides` is the
  documented opt-in to the non-null shape.
- `types/resolvers.py::_attach_file_resolvers` takes `skip_field_names` and is called from
  `types/finalizer.py` with `definition.consumer_authored_fields` — the deliberately broader
  skip Decision 3 required — in the same loop body as `_attach_relation_resolvers`
  (which gets `consumer_assigned_relation_fields`), before the later interface-injection loop.
- `types/resolvers.py::_make_file_resolver` returns `value if value else None` and carries no
  `try/except`, exactly the parent-level-only nullability Decision 4 specified.
- `scalars.py` re-exports `Upload` **and** `UploadDefinition` from
  `strawberry.file_uploads.scalars`, keeps `Upload` out of `_PACKAGE_SCALAR_MAP`, and its
  docstring names `spec-037`. The stale `TODO-ALPHA-035-0.0.11` reference the spec's Risks
  section flagged is **gone** — zero package-wide occurrences.
- `mutations/inputs.py::model_column_write_kind` returns `FILE` for
  `(models.FileField, models.ImageField)`; `model_column_write_annotation` returns `Upload` for
  that kind; `model_column_input_annotation` sets `python_attr = field.name` (never
  `<name>_id`). No `NotImplementedError` seam survives, and the override-skip loop carries no
  file carve-out — the `036` CR-6 exception is lifted as Decision 6 required.
- `mutations/resolvers.py` routes `FILE: scalar_handler`, so an uploaded file rides the generic
  scalar path into `model(**attrs)` / `setattr` and an explicit `null` on a `null=False` file
  column still reaches `_explicit_null_error`. Decision 6's "verify, do not add a branch"
  instruction was followed: no file-specific assignment branch exists.
- `__init__.py` exports `Upload`, `DjangoFileType`, `DjangoImageType` and lists all three in
  `__all__`.
- `pyproject.toml` declares `pillow>=10.0.0` in the `dev` dependency group — the Risks section's
  *preferred* answer, not its fallback.

**Deviations from the spec, verified at source, for Worker 1 to grade.**

- **D1 — `path` is no longer a `DjangoFileType` subfield.** `spec-048` (commit `567cc6d0`) removed
  `path` from the default output and moved
  it behind `Meta.filesystem_path_fields`, which swaps the column onto the new
  `DjangoFilePathType` / `DjangoImagePathType`. The spec claims the four-field default shape at
  roughly twenty sites (`grep -n '`path`'` reports 19 lines carrying a code-span `path`, several
  of which are unaffected prose). This is the third grading case — a deliberate later change —
  so the code stands and the spec is rewritten.
- **D2 — two more root exports exist than Decision 7's "three net-new".**
  `__init__.py` also exports `DjangoFilePathType` / `DjangoImagePathType`, from the same
  `spec-048` commit. Decision 7's own count is still true *of this card*; whether the surface
  sentence may now say "three" unqualified is Worker 1's call.
- **D3 — `convert_field_output` grew a fourth parameter.** Its shipped signature is
  `(field, type_name, *, force_nullable=None, expose_filesystem_path=False)`; the spec names the
  three-parameter form in the Slice checklist, Decision 3 and the Definition of done.
- **D4 — `Meta` gained a key this card said it would not add.** Decision 8 is titled
  "No new `Meta` key, no new setting"; `filesystem_path_fields` is now in
  `types/base.py::ALLOWED_META_KEYS`. The Decision's claim was true of `037` and is false as a
  standing statement about the surface.
- **D5 — Decision 9 carries a `> **Superseded (post-ship, …)**` block.** A live fakeshop
  file/image surface (`MediaSpecimen`, `test_query/test_uploads_api.py`) landed in commit
  `4dca5ec9`, and the spec records it as a chronology block quoting its own retracted text.
  `BUILD.md` `## Spec rationale extraction` forbids exactly that shape: the Decision states the
  current contract directly, and the supersession narrative moves to the rationale companion.
- **D6 — `## Out of scope` still defers the live fakeshop upload surface** to
  `TODO-BETA-062-0.1.5`, contradicting D5's own supersession block four hundred lines earlier.
  The spec contradicts itself at `HEAD`.
- **D7 — the deliberative layer has never been extracted.** Nine `Justification:` blocks, nine
  `Alternatives considered (and rejected):` blocks, a seven-item `## Risks and open questions`
  body written as preferred-answer/fallback pairs, and an inline
  `Revision history (kept inline so the spec is self-contained):` block are all still in the
  spec. Slice 0 moves them; the counts here are Worker 0's grep and Worker 1 re-measures.
- **D8 — path and placeholder rot in the Definition of done.** DoD item 1 names the pre-archive
  `docs/spec-037-…` path and a `check_spec_glossary` invocation against it; DoD item 6 carries a
  literal `DONE-NNN-0.0.11` placeholder instead of `DONE-037-0.0.11`; Decision 1 states the spec
  "lives at `docs/spec-037-…`". All four are false at `HEAD`.

**Not a finding.** `__version__` is `0.0.15`, four patch releases past this card's `0.0.11`
target. Decision 10 and DoD item 7 describe a cut that **happened**; a shipped-version statement
about the release this card closed is not stale, and no worker "updates" it to `0.0.15`.

## Contract-level escalations

`BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch`.
Two questions in this cycle turn on which contract the package should offer rather than on a
defect, and both were settled by the maintainer's own framing of the task:

- **Does a later card's deliberate change make the code wrong, or the spec stale?** Settled:
  the spec is updated to match, and the explanation goes to the rationale companion, never into
  the spec. Rejected alternative: leave the spec as the historical `0.0.11` record and let the
  glossary carry the current shape — rejected because a spec that describes a shape the code has
  not had since `0.0.14` is read as a contract and mis-teaches every future reader.
- **May this cycle change package source?** Settled: yes, but only to close a **proven** gap
  between the spec and the code — a feature planned and never built, or built wrong. Rejected
  alternative: treat the cycle as spec-only and route every code finding to a follow-up card —
  rejected because a dropped feature is exactly what the cycle exists to find.

## Artifact list

- `docs/builder/bld-037-slice-0-rationale_extraction.md`
- `docs/builder/bld-037-slice-1-code_conformance.md`
- `docs/builder/bld-037-slice-2-spec_reconciliation.md`
- `docs/builder/bld-037-integration.md`
- `docs/builder/bld-037-final.md`

## Checklist

- [x] Slice 0: extract the deliberative layer into `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md` (pre-flight step 7; Worker 1 procedural pass, no source diff) -> `docs/builder/bld-037-slice-0-rationale_extraction.md`
- [x] Slice 1: code conformance — grade every Decision and Definition-of-done item against `HEAD` source and tests; dispatch Worker 2 / Worker 3 only if a real gap is proven -> `docs/builder/bld-037-slice-1-code_conformance.md`
- [x] Slice 2: spec reconciliation — rewrite every stale contract statement to the shipped shape, and record what changed and why as `**Post-ship:**` bullets in the rationale companion -> `docs/builder/bld-037-slice-2-spec_reconciliation.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-037-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-037-final.md`

## Review round 1 — residue repair (maintainer-dispatched, 2026-09-02)

Input: the maintainer's request to verify the post-final residue table and enact
it. Not a spec slice; `docs/builder/BUILD.md` `## Review rounds` governs. The
maintainer widened the standing fence to permit board-DB edits; the fence
otherwise holds (spec files and `.py` source only, no closeout agentflow edits,
every created filename carries `037`).

**Ownership partition — two provably disjoint cohorts, dispatched concurrently.**

| Cohort | Files | Worker(s) | Findings |
|---|---|---|---|
| A | `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md`, `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md` | Worker 1 alone (maintainer's standing carve-out: a spec-only change needs no builder) | R1, R2 |
| B | `examples/fakeshop/apps/products/schema.py`, `examples/fakeshop/test_query/test_products_api.py` | Worker 2 build, Worker 3 review | R3 |

No file appears in both cohorts.

### Findings dispatched

- **R1 — `TODO-BETA-062-0.1.5` names the wrong card, 5 sites.** The 2026-08-29
  board inserts moved the fakeshop-activation card to `TODO-BETA-066-0.1.5`
  (`KANBAN.md` heading `### [TODO-BETA-066-0.1.5 - Fakeshop GraphQL schema activation]`);
  `TODO-BETA-062-0.1.3` is now the Aggregation subsystem. Wrong in subject,
  number and version at once. Sites: spec 1132, 1461; companion 652, 670, 695.
  A renumber, never a lifecycle flip — `TODO-BETA-066-0.1.5` is still To Do.
- **R2 — Decision 5 claims a package-root export that does not exist, 1 site.**
  Spec 991-992 says `scalars.py` "(and the package root, `__init__.py`)"
  re-export `Upload` "(and `UploadDefinition`)".
  `grep -c 'UploadDefinition' django_strawberry_framework/__init__.py` -> 0.
  `scalars.py` does export both. Slice 1 graded D-5 BUILT-CONFORMANT citing
  `scalars.py` only and never tested the `__init__.py` half.
- **R3 — the same card rot in two `.py` comments.** `apps/products/schema.py:238`
  and `test_query/test_products_api.py:2253`. Comment-only; owes the inverse
  proof that no behavior moved.

### Verification of the dispatched findings (Worker 0, before dispatch)

Every finding re-measured against the working tree on 2026-09-02, not carried
from the final artifact. Two census corrections came out of reading
`KANBAN.md` card `TODO-ALPHA-056-0.0.17`'s row on this population: its
instrument is `grep ... docs/SPECS/spec-03[4-9]*.md`, which **never scans
`docs/SPECS/appx/`**, so the companion's 3 `062` sites and 2 of the 3 dangling
rule-27 citations are invisible to it. Its recorded counts (3 `062` sites in
spec-037; the dangling citations all spec-side) are therefore low, and the
Slice-0 rationale move is what moved them.

### Not dispatched, and why

- **The 3 dangling rule-27 citations** (spec 459, companion 544 and 826) stay on
  `TODO-ALPHA-056-0.0.17`, which already owns the class-wide maintainer ruling
  and states the spec-side and source-side halves cannot be split. Its ledger row
  needs the count re-derived against `appx/` at that card's close.
- **The file-column read-side `Meta.exclude` test** homes on
  `TODO-ALPHA-054-0.0.16`, whose scope migrates the file family onto bundle
  entries and deletes the hard-coded branches; its byte-identity DoD needs the
  exclusion path pinned before that refactor, not after.
- **`bld-037-final.md` deferred items 2 and 3** are struck by measurement, not
  carded: `docs/GLOSSARY.md` is already correct for `DjangoFileType`,
  `DjangoImageType`, `Meta.required_overrides`, `DjangoFilePathType` and
  `DjangoImagePathType`, and `docs/TREE.md` carries only module one-liners.
  Correcting the catalog's "nobody has checked" wording is a `bld-*.md` edit and
  outside the maintainer's fence.

### Round checklist

- [x] Cohort A -> `docs/builder/bld-037-review-1-residue_repair_spec.md`
- [x] Cohort B -> `docs/builder/bld-037-review-1-residue_repair_source.md`

### Board-DB enactment (Worker 0, under the maintainer's explicit grant)

The maintainer widened the fence to permit board-DB edits, so the two routed
items were homed rather than left as prose. Edits made by ORM inside one
`transaction.atomic()` each, then `KANBAN.md` / `KANBAN.html` re-rendered from
the DB (never hand-edited).

**Card `TODO-ALPHA-054-0.0.16` — Pluggable field-conversion registry.** New
`scope` item at order 6, plus a `related` `CardReference` to `DONE-037-0.0.11`
carrying the amendment source. Homes the file-column read-side `Meta.exclude`
row there rather than on `TODO-BETA-072-0.1.8`, because 054 is the card that
**invalidates the grading which licensed the gap**: spec-037 graded the missing
row Low on the ground that exclusion is name-keyed and shares the scalar path in
`types/base.py::_select_fields`, and 054's own scope deletes the hard-coded
`FIELD_OUTPUT_TYPE_MAP` / `resolvers._attach_file_resolvers` special cases and
resolves the file family through a bundle entry — which un-shares exactly that
path. Landing the row before the migration is what makes 054's
`#"Fakeshop SDL byte-identity test"` DoD item measure the file family; landing it
after, it can only confirm whatever the refactor produced.

**Card `TODO-ALPHA-056-0.0.17` — Alpha documentation-debt discharge.** Two
`scope` items amended.

- Order 6 (`#"Swept 2026-08-07"`), 363 -> 1,435 chars. De-tensed rather than
  flipped: the bullet records what that sweep wrote, so a flip would falsify a
  real record. What it now also states is that **the sweep's own stated
  justification is false of the card it names** — it cites "062 is the natural
  host - its scope (node / nodes, `totalCount`, the subscription surface)", and
  the 2026-08-29 inserts moved that scope to `TODO-BETA-066-0.1.5` while the
  numeral stayed on the Aggregation subsystem. Carries the 48-occurrence
  surviving population and the 7 occurrences this round discharged.
- Order 59 (the `spec-034`..`039` card-id census), 7,149 -> 11,201 chars. Three
  corrections and one new instrument finding, every figure re-derived on
  2026-09-02 rather than carried:
  - the 3 `062` sites it claims in spec-037 were **5** (2 spec + 3 companion,
    the companion's share created by the Slice-0 rationale move), all now
    discharged;
  - its source-side clause's single `.py` site was **2** — it missed
    `test_query/test_products_api.py`;
  - its dangling-anchor sub-population is recorded as 5 spec-side sites and
    measures **4**, 2 of them companion-side, of which only **2** are true
    rule-27 `path #"substring"` citations. The maintainer ruling is still owed;
    its population is 2, not 5.
  - **The census is blind to the id it owns, in two independent ways.** Its
    instrument `grep ... docs/SPECS/spec-03[4-9]*.md` expands to six files:
    `appx/` costs it 13 of the 48 occurrences and the `[4-9]` range costs it a
    further 21, so 34 of 48 sit under `docs/SPECS/` and the glob reaches none.
    Re-run verbatim the glob returns **43** occurrences of the whole `TODO-*`
    population, not the recorded 75, with a further 33 in `appx/` — so the total
    holds only when both are summed and the recorded per-spec distribution is
    dead in every cell for a spec whose companion exists. On the `062` id
    specifically it returns **0** against a live population of **48**: a census
    reporting zero on a 48-occurrence population reads exactly like a finished
    sweep. Converged on independently by this round's dispatcher and its
    reviewer, agreeing at 48 and at 34.

**The coupling card 056 warns about was satisfied, not broken.** That card holds
that renumbering the source without the specs falsifies the leave-verbatim
rulings and renumbering the specs without the source strips their justification.
This round did both halves in one pass under a disjoint partition, and proved
first that no spec quotes the changed marker text: `Still deferred to`,
`fakeshop-activation card): the`, `those stay TODO-BETA` and
`node(id:) / nodes(ids:) entry points` each return **zero** files under
`docs/SPECS/`. The 18 rotted `046` / `047` / `049` ids in `apps/products/schema.py`
were counted 18 before and 18 after and remain card 056's, still coupled to its
unrendered ruling.

**Gates after the board edits.** `scripts/check_kanban_anchors.py` OK (76 card
anchors unique, no collision with 146 glossary anchors, no duplicate id);
`build_kanban_md.py --check` and `build_kanban_html.py --check` both exit 0;
`build_kanban_tracked_path_constants.py --check` exit 0;
`scripts/check_citations.py` OK at 942 citations, `KANBAN.md` rising 160 -> 161
as the new card-054 rule-27 citation resolved. The `KANBAN.md` diff is **6 lines**
— 2 added on card 054, 2 replaced on card 056 — so the render carried no
collateral from the concurrently-dirty tree.

### Round 1 outcome

Both cohorts `final-accepted`. Cohort A closed R1 (5 card-id renumbers) and R2
(Decision 5's false package-root claim) plus one defect R1's own fifth edit
created; cohort B closed R3 (2 comment renumbers) through build -> review ->
revision -> re-review -> final verification, with the reviewer's M1 discharged by
an appended withdrawal rather than a rewrite.

**Why the append was accepted over the prescribed rewrite.** `ARTIFACT.md`
`## Re-pass sections` and `worker-2.md` `## Scope` forbid editing a prior build
report unconditionally, and **no role at all** may place a forward pointer at the
original site — Worker 2 is barred by Scope, Worker 3 may append review sections
only, Worker 1 owns the plan and final sections rather than another worker's
report. Requiring a pointer would make the finding unclosable by any worker,
which is the signal the corpus treats the append as the closure. The rewrite
would also have destroyed the evidence that a `.py`-scoped instrument's result
had been promoted to a tree-wide claim, which is the transferable lesson.

### Three self-falsifying-instrument defects this round produced and caught

Recorded because all three are the same shape and the shape recurs: **an
instrument or a count that the act of writing it down invalidates.**

1. **A row stating a live count of a population it is itself editing.** Card
   056's amendment first recorded "48 occurrences across 13 surfaces", measured
   minutes before that same write cut the board-side share, and it summed the
   board DB against its own `KANBAN.md` / `KANBAN.html` renders — three surfaces
   carrying one fact. Corrected to **39 across 10**, dated, with the recording
   surface's own rows excluded from the sweepable total.
2. **A negative control token written into an artifact.** Worker 2's impossible
   token `TODO-BETA-062-0.1.5Z` is now quoted in cohort B's artifact, so
   re-running that exact control returns 1, not 0. Worker 1 hit the same trap in
   its own draft and withheld its randomized literal. Randomize per run; never
   publish the token.
3. **A `#"substring"` citation addressed by line number.** The companion's
   `#"Future scalars ..."` citation moved 826 -> 841 when this round appended a
   bullet above it. Now addressed by content on card 056.

### Board-side corrections after Worker 1's final verification

Both of Worker 1's Low findings enacted on card `TODO-ALPHA-056-0.0.17`:

- **The board-side share is 6 live, not the byte census's 8.** `strings
  db.sqlite3 | grep -c` returns **4** where the ORM returns **2** — rewriting
  those rows left superseded text in freelist pages no query reaches. The row now
  says to count board-side occurrences by ORM against `CardItem.text`, never by
  scanning the SQLite file. Worker 1's digit was right about bytes and the row's
  6 was right about data; the row now carries both and the reason they differ.
- **The two dangling rule-27 citations are addressed by content**, with the
  826 -> 841 shift named as the reason.

`scripts/check_citations.py` held at 942 / 161 across these edits, correctly:
it resolves `<path>.py::<Symbol>` and puts `docs/` deliberately out of scope, so
the two `docs/SPECS/*.md #"substring"` citations added to card 056 are invisible
to it — the same gap that leaves the dangling citations ungated, now demonstrated
rather than asserted. `check_kanban_anchors.py` OK; both renderers `--check`
exit 0; the `KANBAN.md` diff stands at **6 lines** across the whole round.

### Round checklist

- [x] Round 1 closed; both artifacts `final-accepted`; handed to the maintainer.
