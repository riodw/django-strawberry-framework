# Build: Slice 2c — retire the `rev6` round vocabulary; re-key the section, its seventeen headings, and every ordinal citer

Spec reference: `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` (whole document)
Companion: `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md`
Status: final-accepted

This is a combined **Plan + Final-verification** pass under `docs/builder/BUILD.md`
`### Procedural-closure slices` — a spec-only change with no builder, on the maintainer's
instruction recorded in `docs/builder/build-039-serializer_mutations-0_0_13.md`
`## Slice 2 split, and why` and `## Slice 2c, and why the deferral could not stand`.

Slice 2b retired `spec-039`'s severity and promotion vocabulary and **deferred `rev6` with
a named owner**. This pass discharges that deferral. `rev6` is review-round attribution,
banned from standing prose by `AGENTS.md` and `START.md` "Style Rio cares about" under the
same clause that licensed 2b's strip; leaving it was the `START.md` #"Partial claim fix"
hazard.

## Spec status-line re-verification

Read `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` lines 1-48. The opener's shipped
claim (`0.0.13`, card `DONE-039-0.0.13`), the predecessor pointers to `036` / `038`,
and the `0.0.13` joint-cut version boundary all still describe the tree. **No status-line
edit owed this pass.** One head-opener inconsistency was found that is *not* a status line
and not this slice's — see `### Notes for Worker 1`, item 3.

---

## Plan (Worker 1)

### What this pass had to do

1. Re-derive the `rev6` population in both files with at least two independent instruments
   (2b's report documents a glob under- and over-counting twice in this cycle).
2. Rename the section heading and the seventeen `### rev6 #N` subsection headings, computing
   old and new slugs by the `START.md` "Markdown link convention" rule.
3. Re-point **every** inbound reference — and establish, by measurement rather than
   assumption, what the inbound population actually is.
4. Sweep `docs/` **and** `.py`, not only the two files being edited.
5. Choose a section name that describes what the section *is*, and an ordering a reader can
   navigate and a citer can address.

### DRY analysis

- **Helper inventory checked.** Not applicable and not skipped: this pass writes no code and
  proposes no helper. The package-wide AST inventory would answer a question this slice does
  not ask. The sweep it *does* owe — every `.py` comment and docstring in the package, tests,
  examples and scripts — was run structurally rather than by line grep, below.
- **Existing patterns reused.** The rename method is Slice 2b's, unchanged: compute the slug
  with the `START.md` rule, validate the slug function against the files' own existing
  anchors before trusting it on a new heading, sweep repo-wide for the *old* slug, and re-key
  citers onto content names rather than onto a new ordinal scheme.
- **New helpers justified.** None.
- **Duplication risk avoided.** The naive shape here is a second ordinal scheme — renumbering
  the seventeen items `1..17` in reading order so the existing `#N` citations could be
  "fixed" cheaply. That reproduces the defect one rename later. Rejected; every citer is
  re-keyed onto content instead.

### Test additions / updates

None. No executable change, and no `.py` file is touched (proved below across 442 files by
two independent instruments).

### Spec slice checklist (verbatim)

This slice has no `## Slice checklist` sub-bullets in the spec — it is a residual-cycle
sub-slice whose contract is the build plan's own checklist row, verbatim from
`docs/builder/build-039-serializer_mutations-0_0_13.md`:

- [x] Slice 2c: retire the `rev6` round vocabulary (deferred out of 2b, same rule, own anchor risk) -> `docs/builder/bld-039-slice-2c-rev6_retirement.md`

---

## Final verification (Worker 1)

### The population, per instrument

**Every figure names the instrument that produced it**, and the instruments were run before
any byte was written.

| # | Instrument | Spec, pre | Companion, pre | Spec, post | Companion, post |
|---|---|---|---|---|---|
| A | `grep -o 'rev6' \| wc -l` — **occurrence** count | **62** | **19** | **0** | **2** |
| B | `grep -c 'rev6'` — **line** count (2b's published instrument) | 62 | **18** | 0 | 2 |
| C | `(?i)\brev[0-9]+\b \| \bround[- ]?[0-9]+\b \| \bround\b` — the whole round vocabulary, not just the `rev6` spelling | **67** (62 `rev6` + 3 `Round-6` + 2 `round-6`) | **29** (19 `rev6` + 7 `Round-6` + 3 `round-6`) | **0** | **7**, enumerated below |
| D | heading census, `^### rev6 #` and `^## Round-6` | **17** sub + **1** section | 0 sub + **1** section | **0** + **0** | **0** + **0** |
| E | ordinal census, `(^\|[^A-Za-z0-9_])#[0-9]+` — the citations a heading rewrite actually strands, `rev6` spelling or not | **8** | **13** | **0** | **4**, all quoted |

**Instrument B is 2b's published figure and it is a line count, not a population.** The
companion has **19** occurrences on **18** lines: line 704 carried two
(`` `SerializerFieldConversion` (rev6 #11), `describe_serializer_input` (rev6 #15) ``). This
is `START.md` "Instruments that lie" verbatim — *count occurrences, not lines: two hits on
one line read as one*. The 62/18 pair the dispatch carried forward was one measured figure
and one under-count of a different kind from 2b's `M2M` over-count: same defect class, other
sign, and only a second instrument separates them.

**Instrument E is the one that mattered, and neither the dispatch nor 2b had run it.**
`rev6` was never the whole citer vocabulary. The spec cited its own items by **bare
ordinal** eight times — `the serializer-only enum (#6)`, `the JSON / registry-mapped scalars
(#7 / #11)`, `` `codes` / `path` on `FieldError` (#4 / #13) ``, `agreement guard (#1)` — and
the companion's entire `### Post-ship changes to individual rev6 items` section was **keyed**
on them (`- **#14 — …**`, `- **#12 — …**`, and four more). A `rev6`-only sweep retires the
spelling and leaves twenty-one live ordinals pointing at numbers that no longer exist. All
twenty-one are now content names.

### Retirement, re-measured

**The spec measures 0 by all five instruments.** No `rev6`, no `Round-6`/`round-6`, no
`\bround\b`, no heading, no bare ordinal.

**The companion measures 0 in its own voice.** Its seven survivors are enumerated, and every
one is either inside a marked quotation or a *mention* of the retired token rather than a
*use* of it:

| Line | Token | Why it stands |
|---|---|---|
| 1450 | `rev6` | Inside the blockquoted verbatim preamble — the text Slice 0 **deleted from the spec**, quoted here as the record of it. |
| 1452 | `#17` | Same quotation. |
| 1447 | `round` | My own framing sentence, saying the quotation keeps its round vocabulary and why. |
| 1589 | `round` | Pre-existing: "a dated record of what a review round found rather than standing prose" — the statement of the rationale file's carve-out, not an attribution of any contract. |
| 1600, 1602 (×2) | `round`, `` `Round-6 …` `` | The retirement record naming, in backticks, the heading it retired. 2b's record names its three retired headings the same way. |
| 1615 | `` `rev6 #N` `` | Same record, naming the retired citation form. |
| 1618-1619 | `(#17)`, `` `#1` through `#17` `` | The count bullet, quoting the preamble's own arithmetic — its subject. |

**Why the quotation was not rewritten.** The blockquoted preamble is a record of text this
cycle deleted from the spec; Slice 0's whole deliverable was preserving it. Editing a
quotation to remove the vocabulary that is the reason it was preserved destroys the record
while still claiming to be one. It was **converted to a blockquote** in this pass — it had
been sitting as plain prose in the companion's own voice, asserted as "verbatim" without
being marked as quoted — which is what scopes the two surviving tokens to quoted material
and makes the claim visible instead of asserted. `AGENTS.md` bans process provenance from
**code and standing prose**; the rationale companion is the deliberation record by
construction, and 2b established the same carve-out across four prior specs' companions.

### The section's new name, and why

`## Round-6 improvements (better-than-graphene-django)` → **`## Improvements over
graphene-django's DRF integration`**.

- **It is taken from the section's own opening sentence** — "Seventeen improvements make the
  serializer lane stricter, safer, and more diagnosable *than graphene-django's DRF
  integration*". A name the section already argues for needs no separate justification and
  cannot drift from the body.
- **It says what the section is**, not which review produced it: a set of shipped contracts
  that exceed the package this one is a parity target for.
- `(better-than-graphene-django)` was **not** retired for being provenance — it is content —
  but it was the parenthetical half of a name whose first half was provenance, and it is not
  repo vocabulary. Measured: the phrase appears nowhere outside `spec-039` and this cycle's
  own artifacts, so nothing else was keyed to it.

**Ordering.** The seventeen subsections were already in a deliberately **non-numeric**,
thematic order — input and type construction (converter registry, scalar matrix, generated
enums, type-override policy, SDL metadata), then schema-time and runtime diagnostics
(aggregate diagnostics, agreement guard, golden SDL, debug registry), then the write-time
contracts (row locking, save-kwargs hook, relation validation, injection contract,
fingerprint), then the error envelope (`ErrorDetail.code`, structured `path`), then nested
inputs. The retirement **kept that order** and added one sentence to the preamble naming it,
so the ordering a reader navigates by is now stated rather than implied by numbers that no
longer exist. Each subsection is addressed by its own title; the seventeen titles are
distinct.

### The eighteen heading renames, with slugs

Slugs computed by the `START.md` "Markdown link convention" rule — lowercase, drop
backticks, strip non-word except hyphens, each surviving space its **own** hyphen (so
` — ` yields a double hyphen and `#11` yields `11`). **The slug function was validated
first** against both files' existing in-page anchors: 182 uses / 20 distinct in the spec and
89 / 18 in the companion, **all resolved**, before it was trusted on a new heading.

| # | Old heading | Old slug | New heading | New slug |
|---|---|---|---|---|
| — | `## Round-6 improvements (better-than-graphene-django)` (**spec**) | `#round-6-improvements-better-than-graphene-django` | `## Improvements over graphene-django's DRF integration` | `#improvements-over-graphene-djangos-drf-integration` |
| — | `## Round-6 improvements (better-than-graphene-django)` (**companion**) | `#round-6-improvements-better-than-graphene-django` | `## Improvements over graphene-django's DRF integration` | `#improvements-over-graphene-djangos-drf-integration` |
| 1 | `### rev6 #11 — Public serializer-field converter registry` | `#rev6-11--public-serializer-field-converter-registry` | `### Public serializer-field converter registry` | `#public-serializer-field-converter-registry` |
| 2 | `### rev6 #7 — Expanded DRF scalar capability matrix (no catch-all)` | `#rev6-7--expanded-drf-scalar-capability-matrix-no-catch-all` | `### Expanded DRF scalar capability matrix (no catch-all)` | `#expanded-drf-scalar-capability-matrix-no-catch-all` |
| 3 | `` ### rev6 #6 — Generated enums for serializer-only `ChoiceField` `` | `#rev6-6--generated-enums-for-serializer-only-choicefield` | `` ### Generated enums for serializer-only `ChoiceField` `` | `#generated-enums-for-serializer-only-choicefield` |
| 4 | `### rev6 #8 — Model-backed serializer type-override conflict policy` | `#rev6-8--model-backed-serializer-type-override-conflict-policy` | `### Model-backed serializer type-override conflict policy` | `#model-backed-serializer-type-override-conflict-policy` |
| 5 | `### rev6 #9 — Thread DRF field metadata into the SDL` | `#rev6-9--thread-drf-field-metadata-into-the-sdl` | `### Thread DRF field metadata into the SDL` | `#thread-drf-field-metadata-into-the-sdl` |
| 6 | `### rev6 #5 — Aggregate schema-time diagnostics` | `#rev6-5--aggregate-schema-time-diagnostics` | `### Aggregate schema-time diagnostics` | `#aggregate-schema-time-diagnostics` |
| 7 | `### rev6 #1 — Runtime schema/runtime serializer agreement guard` | `#rev6-1--runtime-schemaruntime-serializer-agreement-guard` | `### Runtime schema/runtime serializer agreement guard` | `#runtime-schemaruntime-serializer-agreement-guard` |
| 8 | `### rev6 #16 — Golden SDL coverage for representative serializer inputs` | `#rev6-16--golden-sdl-coverage-for-representative-serializer-inputs` | `### Golden SDL coverage for representative serializer inputs` | `#golden-sdl-coverage-for-representative-serializer-inputs` |
| 9 | `### rev6 #15 — Schema-shape debug/introspection registry` | `#rev6-15--schema-shape-debugintrospection-registry` | `### Schema-shape debug/introspection registry` | `#schema-shape-debugintrospection-registry` |
| 10 | `` ### rev6 #14 — Row locking for model-backed write mutations (`Meta.select_for_update`) `` | `#rev6-14--row-locking-for-model-backed-write-mutations-metaselect_for_update` | `` ### Row locking for model-backed write mutations (`Meta.select_for_update`) `` | `#row-locking-for-model-backed-write-mutations-metaselect_for_update` |
| 11 | `` ### rev6 #12 — `get_serializer_save_kwargs` (a save-time hook, separate from constructor kwargs) `` | `#rev6-12--get_serializer_save_kwargs-a-save-time-hook-separate-from-constructor-kwargs` | `` ### `get_serializer_save_kwargs` (a save-time hook, separate from constructor kwargs) `` | `#get_serializer_save_kwargs-a-save-time-hook-separate-from-constructor-kwargs` |
| 12 | `### rev6 #3 — Visibility-scoped + query-efficient relation validation` | `#rev6-3--visibility-scoped--query-efficient-relation-validation` | `### Visibility-scoped + query-efficient relation validation` | `#visibility-scoped--query-efficient-relation-validation` |
| 13 | `` ### rev6 #2 — Explicit injection contract (`Meta.injected_fields`) `` | `#rev6-2--explicit-injection-contract-metainjected_fields` | `` ### Explicit injection contract (`Meta.injected_fields`) `` | `#explicit-injection-contract-metainjected_fields` |
| 14 | `` ### rev6 #10 — Fingerprint `get_serializer_for_schema()` for determinism `` | `#rev6-10--fingerprint-get_serializer_for_schema-for-determinism` | `` ### Fingerprint `get_serializer_for_schema()` for determinism `` | `#fingerprint-get_serializer_for_schema-for-determinism` |
| 15 | `` ### rev6 #4 — Preserve DRF `ErrorDetail.code` in the error envelope `` | `#rev6-4--preserve-drf-errordetailcode-in-the-error-envelope` | `` ### Preserve DRF `ErrorDetail.code` in the error envelope `` | `#preserve-drf-errordetailcode-in-the-error-envelope` |
| 16 | `` ### rev6 #13 — Structured error `path` in addition to the dotted `field` `` | `#rev6-13--structured-error-path-in-addition-to-the-dotted-field` | `` ### Structured error `path` in addition to the dotted `field` `` | `#structured-error-path-in-addition-to-the-dotted-field` |
| 17 | `### rev6 #17 — Explicit opt-in nested serializer input support` | `#rev6-17--explicit-opt-in-nested-serializer-input-support` | `### Explicit opt-in nested serializer input support` | `#explicit-opt-in-nested-serializer-input-support` |

One further heading was renamed for the same reason: the companion's
`` ### Post-ship changes to individual `rev6` items (`039` residual reconciliation, 2026-09-05) ``
→ `### Post-ship changes to individual improvement items (…)`. Nothing links
to it in either direction (verified in the anchor audit below).

### Inbound references re-pointed

**Anchors: the seventeen subsection slugs stranded nothing, and that is a measurement.** A
sweep of every tracked file plus every `.md` under `docs/` (excluding regenerable
`docs/shadow/`) for each of the seventeen **old** subsection slugs returned **0 hits**. The
section slug had exactly one live citer:

| Old inbound reference | New |
|---|---|
| spec link definition `[rationale-rev6]: appx/…-rationale.md#round-6-improvements-better-than-graphene-django` | `[rationale-improvements]: appx/…-rationale.md#improvements-over-graphene-djangos-drf-integration` |
| spec body, the one use of that label: `[Round-6 improvements][rationale-rev6].` | `[Improvements over graphene-django's DRF integration][rationale-improvements].` |
| spec body, in-page: `` the fixtures the `## Round-6 improvements` items need `` | `the fixtures the [improvement items](#improvements-over-graphene-djangos-drf-integration) need` |

The label was renamed as well as re-pointed: `rationale-rev6` is itself the retired
vocabulary. It keeps its position in the `<!-- docs/SPECS/ -->` group (between
`rationale-d9` and `rationale-risks` under the file's existing ordering).

**Ordinals: this was the real citer population, and every one is now a content name.**

| Where | Old form | New form |
|---|---|---|
| spec, 45 inline sites | `(rev6 #2)`, `(rev6 #14)`, `(rev6 #4 / #13)`, `, rev6 #3)`, `(rev6 #6; base …)`, … | deleted, keeping the clause — in every one of the 45 the surrounding prose already names the contract by symbol or by `Meta` key, so the parenthetical was pure provenance (`START.md`: removed attribution carried the WHY; restate it, and here it was already stated) |
| spec, 5 sites where the ordinal was doing navigational work | `the rev6 #8 type-override conflict`; `the surfaces the rev6 items … expose`; `descriptions (rev6 #9…)`; `pairs with rev6 #4.`; `agreement guard (#1)` | `the type-override conflict`; `the surfaces those improvements … expose`; `(DRF field metadata is threaded into the SDL…)`; `` pairs with the preserved `ErrorDetail.code` above. ``; `agreement guard` |
| spec, `round-6` prose | `` the `## Round-6 improvements` items need ``; `the round-6 rows need` | the in-page link above; `those improvement rows need` |
| companion, 19 sites | `(rev6 #11)`, `(rev6 #15)`, `(rev6 #17)`, `(rev6 #14)`, `(rev6 #2)`, `(rev6 #9)`, `the rev6 items`, `the round-6 preamble`, `the round-6 items` | deleted or restated by content (`the improvement items`, `the preamble`, `those improvement items`) |
| companion, the post-ship bullet **keys** | `- **#14 — …**`, `- **#12 — …**`, `- **#2 — …**`, `- **#1 — …**`, `- **#3 — …**`, `- **#17 — …**` | `- **Row locking — …**`, `- **The save-time kwargs hook — …**`, `- **The explicit injection contract — …**`, `- **The schema/runtime agreement guard — …**`, `- **Visibility-scoped relation validation — …**`, `- **Opt-in nested serializer inputs — …**` |
| companion, in-bullet ordinals | `` channel (#2) ``; `` `_assert_schema_runtime_agreement` (#1) ``; `` measured from the `### rev6 #` heading list ``; `` `## Round-6 improvements` #4 and #13 `` | the ordinal dropped (the sentence names the contract either side of it); `the section's own `###` heading list`; `` the improvement section's `ErrorDetail.code` and structured-`path` items `` |

**Method, not luck.** Every replacement ran through one script holding an explicit
`(old, new, expected_count)` table that **asserts every site exists at its expected
multiplicity before a single byte is written** and aborts writing nothing otherwise
(`START.md`: "Enumerate, never grep-count, before writing"). It aborted **four** times on
the spec pass — a `#17` group that was 7 sites and not 5, a `, rev6 #7)` that was 1 and not
2, and two patterns whose text was wrapped across a line break where the table assumed one
line. Each was re-measured against the file and the table corrected. Nothing was written
until every count matched.

### The repo-wide sweep, beyond the two files

Population: **every `.md`, `.py`, `.html`, `.csv` and `.txt` in the tree** except `.git`,
`.venv`, `__pycache__`, `dist` and the regenerable `docs/shadow/` — **688 files** for the
substring sweep, **442 `.py` files** for the code sweep.

- **`.py`: zero, by two independent instruments.** Instrument 1, raw text against
  `(?i)\brev\d+\b|\bround[- ]?\d+\b`: **0 files**. Instrument 2, structural — every comment
  token via `tokenize` and every module / class / function docstring via `ast`, not a line
  grep: **0 hits**. A third pass for `spec-039` within 60 characters of a `#N` ordinal:
  **0**. `spec-039`'s round vocabulary never reached the code, so nothing about the rename
  can rot there.
- **`#"substring"` citations into either file: zero, repo-wide.** The first instrument for
  this was wrong and is worth recording: matching any `#"…"` on a line that also mentions
  `spec-039` reported 53 hits, 47 of them "broken" — all false, because a `KANBAN.md` card
  item cites a dozen different documents on one line and the sweep was attributing every
  substring on the line to `spec-039`. Re-run requiring the `spec-039…` path token to
  **immediately precede** the `#"`: **0 citations exist**. A reword-fragile citation into
  either file would have been invisible to `check_citations.py`, which is `path::Symbol`-only
  — and the correct instrument says there are none to break.
- **Sibling and archived specs: zero.** No `.md` outside the two edited files and this
  cycle's own artifacts carries a `rev6`-or-ordinal reference into `spec-039`, with two
  exceptions recorded in `### Notes for Worker 1` (one in `BACKLOG.md`, one in a closed
  audit artifact of this cycle). Every other `rev6` in the tree —
  `spec-019`/`020`/`021`/`027`/`028`/`029` rationale companions, two `docs/builder/DONE/`
  plans, `docs/row-preserving-predicates-part1-plan.md` — is **that document's own** review
  round; each was checked for a `spec-039` mention and all six companions carry **zero**.

### Anchor and link-definition audit, both directions

Run after the rename, over both files:

| Check | Spec | Companion |
|---|---|---|
| in-page `](#…)` anchors resolving | **183 uses / 21 distinct, 0 unresolved** | **89 / 18, 0 unresolved** |
| cross-file anchors into the partner | **16 refs, 0 unresolved** | **18 refs, 0 unresolved** |
| link definitions vs uses | **115 defs / 115 used labels; 0 undefined, 0 orphan** | **60 / 60; 0 undefined, 0 orphan** |
| every definition target exists on disk | **yes** | **yes** |
| ten canonical group headers, present and in order | **yes** | **yes** |
| definition order within group | unchanged by this pass (`rationale-improvements` occupies the exact slot `rationale-rev6` held) | unchanged |

`path::Symbol` citations, resolved by an AST index over `django_strawberry_framework/`,
`tests/`, `examples/` and `scripts/` — the check no gate performs, since
`check_citations.py` reads `.py` and `KANBAN.md` only: **43 distinct in the spec, 0
unresolved; 13 in the companion, 0 unresolved.** Unchanged from 2b; this pass introduced no
symbol rot.

### `.py` files touched, and the inverse proof

**None.** No `.py` file was edited this pass, so no docstring-stripped AST-identity proof is
owed and none is possible — a control cannot fire on a file nobody touched.

What replaces it is the measurement that establishes the premise, and it is the same
two-instrument discipline: the 442-file raw sweep and the 442-file structural
comment-plus-docstring sweep both return **0** round-vocabulary hits, so there was no `.py`
citer to repair. `git status --short` confirms it: of the 46 paths dirty at the end of this
pass, exactly **two** are this pass's —
`docs/SPECS/spec-039-serializer_mutations-0_0_13.md` and
`docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md`. Every other path is a
prior slice's accepted work or the concurrent `spec-050` session's, neither edited nor
reverted (`AGENTS.md` rule 34). The two MIXED files 2b enumerated
(`rest_framework/resolvers.py`, `utils/querysets.py`) were not opened.

### Gate results

| Gate | Command | Result |
|---|---|---|
| source layout | `uv run python scripts/check_trailing_commas.py <spec> <companion>` (explicit paths, never a bare `.`) | **pass** — `Fixed 0 file(s).` |
| spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-039-serializer_mutations-0_0_13.md` | **pass** — `OK: 38 terms` (unchanged) |
| citations | `uv run python scripts/check_citations.py --check` | **pass** — `OK: 963 citations resolve (808 in 442 .py files, 155 in KANBAN.md)` — unchanged, no reduction |
| ruff format / check | not run — **no `.py` file touched** (the scoped-invocation rule has no files to scope to) | n/a |

Checks the gates cannot perform, run by hand and reported above: the anchor audit both
directions, the link-definition audit both directions, the spec-side `path::Symbol` AST
resolution, and the `#"substring"` citer sweep.

Wrap hygiene: six paragraphs the deletions left ragged (a short orphan line mid-paragraph,
or a 120-160-character line where two wrapped fragments joined) were re-flowed to the
files' own ~92-column style. No line this pass wrote exceeds 100 characters except where the
file's existing convention already does (long `](#decision-N--…)` anchors and
symbol-qualified citations, which must not be wrapped).

Spec `315,306 B` / 3,950 lines → **`314,984 B` / 3,952 lines**.
Companion `125,139 B` / 1,747 lines → **`126,064 B` / 1,760 lines**.

### Summary

`spec-039`'s `rev6` round vocabulary is retired. The section is now `## Improvements over
graphene-django's DRF integration`, named from its own opening sentence; the seventeen
subsections keep the content titles they already carried and the thematic order they were
already in, with the ordering now stated in the preamble instead of implied by numbers. The
spec measures **0** by all five instruments; the companion measures 0 in its own voice, with
seven survivors enumerated — two inside a blockquoted verbatim record of text this cycle
deleted from the spec, five naming in backticks what was retired.

The renames stranded no anchor — a repo-wide sweep for all eighteen old slugs found one live
citer, the spec's own link definition, re-pointed and re-labelled in the same pass. What the
rename really stranded was the **ordinals**, and the `rev6` glob could see only two-thirds of
them: twenty-one bare `#N` citations, including the entire key column of the companion's
post-ship section, would have survived a spelling-only strip. All are content names now.

### Spec changes made (Worker 1 only)

`docs/SPECS/spec-039-serializer_mutations-0_0_13.md` unless noted.

| # | Region | Change | Reason |
|---|---|---|---|
| 1 | `## Round-6 improvements (better-than-graphene-django)` heading + preamble | Renamed to `## Improvements over graphene-django's DRF integration`; preamble gained one sentence naming the section's capability ordering, and its closing pointer re-labelled to `[rationale-improvements]`. | `AGENTS.md` / `START.md` ban review-round attribution in standing prose; the section still needs a navigable ordering once the numbers go. |
| 2 | the seventeen `### rev6 #N — <title>` headings | Prefix dropped; each keeps the content title it already carried. Old and new slugs tabled above. | Same. |
| 3 | 45 inline `(rev6 #N)` parentheticals across `## Goals`, `## Slice checklist` Slices 1-4, `## Non-goals`, `## Out of scope`, Decisions 5-10, `## Edge cases`, `## Test plan`, `## Implementation plan`, the promotion table, and the improvement subsections | Deleted, clause preserved. | The clause each justified is already stated by the surrounding prose; the token was pure provenance. |
| 4 | 5 spec sites where the ordinal was navigational, and the 8 bare `#N` ordinals | Restated by content (`the type-override conflict`, `` pairs with the preserved `ErrorDetail.code` above ``, …). | `START.md`: cite a contract by CONTENT, never ordinal — a heading rewrite strands every ordinal. |
| 5 | `## Test plan` "Live means the one aggregate schema" paragraph; Slice-4 DoD row | `` the `## Round-6 improvements` items need `` → an in-page link to the renamed section; `the round-6 rows need` → `those improvement rows need`. | Same rename; an in-page link is a content citation that survives the next one. |
| 6 | link definition block | `[rationale-rev6]` → `[rationale-improvements]`, re-pointed at the new companion anchor, same group and slot. | The label itself was the retired vocabulary. |
| 7 | six paragraphs across the edited regions | Re-flowed after the deletions left ragged wraps. | Wrap defect, not content. |

### Rationale companion changes (Worker 1 only)

`docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md`. Append-only for new
deliberation, but a sentence this pass falsified may not stand
(`docs/builder/BUILD.md` `## Spec rationale extraction` rule 2).

- **Section heading renamed** to match the spec's, and the
  `` ### Post-ship changes to individual `rev6` items `` sub-heading renamed to
  `### Post-ship changes to individual improvement items`.
- **The moved preamble converted to a blockquote**, with the framing sentence rewritten to
  say it is quoted verbatim and why the round vocabulary and ordinals inside it stand. It had
  been plain prose in the companion's own voice, asserted as "verbatim" without being marked
  as a quotation — which is what let a reader take round attribution as the file's own claim.
- **The six post-ship bullet keys re-keyed from ordinals to content names**, and the two
  in-bullet ordinal cross-references (`channel (#2)`,
  `` `_assert_schema_runtime_agreement` (#1) ``) restated by content.
- **Nine inline `(rev6 #N)` citations deleted** across Decisions 5, 6, 7 and 13's post-ship
  notes, clause preserved.
- **The Slice-0 move accounting rewritten** where it described the moved text by its retired
  name (`` **The `## Round-6 improvements` preamble** ``, `` the seventeen `### rev6 #N`
  subsections ``, `` measured from the `### rev6 #` heading list ``) — those sentences named
  headings that no longer exist.
- **The "Still owed — the `### rev6 #N` heading vocabulary" bullet rewritten** into the
  record of the retirement: what was renamed and to what, the measured 62 / 19, why the
  earlier 18 was a line count, the zero-inbound anchor sweep, and the finding that the
  ordinals rather than the anchors were the citer population. Its "Still owed" framing was
  false the moment this pass landed.
- **The count bullet re-titled** from `The Round-6 count is seventeen` to `The improvement
  count is seventeen`, keeping its quotation of the preamble's arithmetic.
- **`Decision 4`'s post-ship note** re-keyed: `` `## Round-6 improvements` #4 and #13 `` →
  `` the improvement section's `ErrorDetail.code` and structured-`path` items ``.

No link definition was added or removed; no companion label changed.

### Notes for Worker 1 (spec reconciliation)

Each item has a named owner. Nothing is routed forward unowned.

**Outside this cycle's fence — record, do not act:**

1. **`BACKLOG.md` line 31 is a live stranded ordinal citer.** It reads
   `` (`mutations/inputs.py::FieldError`, spec-036 Decision 7 + spec-039 rev6 #4/#13) `` —
   the only reference to `spec-039`'s retired numbering anywhere outside the two edited files
   and this cycle's own artifacts. The maintainer's fence for this cycle is **spec files and
   `.py` files only** (`docs/builder/build-039-serializer_mutations-0_0_13.md` `## What this
   cycle is`), and `BACKLOG.md` is neither, so no edit was made. The repair is one
   substitution: `spec-039 rev6 #4/#13` → **`spec-039`'s error-envelope `codes` / `path`
   improvements**. **Owner: the maintainer.** Leaving it is the exact hazard this slice
   exists to close, one document over.
2. **`spec-036` carries 146 own-voice severity-ordinal labels at `HEAD`** — 2b's finding,
   re-carried unchanged because it is still true and still unowned. It falsifies the build
   plan's `## Known hazard carried into this cycle` premise that "030, 036, 037, 038 all
   carry zero". `spec-036` is a different card's spec and outside this fence; whether it gets
   the same strip is a scope question, not a custodial one. **Owner: the maintainer.**
3. **The spec's head opener still says the envelope is reused "byte-identical", and the
   companion records that as falsified.** Line 22 opens "The flavor reuses, **byte-identical**,
   the contracts `spec-036` froze for exactly this", listing the `FieldError` envelope first;
   `## Non-goals` and Decision 2 — amended by Slice 2a — say the envelope is **additive, not
   frozen**, and this card extends it. The companion carries the finding under
   `### Post-ship findings that belong to no single Decision` but the opener was never
   reconciled to it. Found while re-verifying the status lines; it is **not** a status line
   and not this slice's dispatch, and re-opening a `final-accepted` slice's content
   unreviewed is the "while I'm here" this repo refuses. **Owner: the cross-slice integration
   pass** (`docs/builder/bld-039-integration.md`), which owns exactly this class of
   cross-section contradiction.

**Accepted residue, closing with the cycle:**

4. `docs/builder/bld-039-audit-2-sets_and_bind.md:242` cites `` `spec-039` Decision 12 … and
   by rev6 #11 ``, and `bld-039-slice-0` / `bld-039-slice-2b` cite the old section slug.
   These are this cycle's own per-cycle artifacts — exempt from the standing-prose rules and
   never edited after the fact (`START.md` "Per-cycle scratch closes w/ cycle";
   `docs/builder/ARTIFACT.md` "never edit prior entries"). They are records of what the spec
   said when each pass ran, and they close with the cycle. **No action.**

**Carried unchanged from Slices 2a / 2b, re-read this pass and not re-raised:**

5. Escalations A (the DRY import ratchet's scope), B (the `isinstance` tightening) and C
   (`HEAD` is red from `spec-050` at `4c483b6b` in four modules this cycle does not touch, so
   `bld-039-final.md` cannot record a green full sweep). **Owner: the maintainer.**
6. `KANBAN.md`'s discharged 19-site `spec-039` inventory; the two `rest_framework/inputs.py`
   duplications; the `f"SerializerMutation {…}: "` message-prefix duplication in
   `rest_framework/resolvers.py`; the `tests/rest_framework/test_dry_import_ratchet.py`
   docstring wrap; the DRY existence challenge on `mutations/sets.py::cached_build_input`.
   **Owner: the integration pass / `bld-039-final.md`'s deferred-work catalog.**

**No executable change was made, and none is owed.** No `.py` file was opened; the
442-file two-instrument sweep is the evidence that none needed to be.

### Final status

`final-accepted`. The retirement is complete and re-measured to **0** in the spec by five
instruments and to 0-in-its-own-voice in the companion with every survivor enumerated; all
eighteen heading renames are recorded with old and new slugs and their one live inbound
reference re-pointed; the twenty-one ordinal citers the `rev6` glob could not see are re-keyed
onto content names; and every gate passes with `check_spec_glossary` and `check_citations`
unchanged.

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
