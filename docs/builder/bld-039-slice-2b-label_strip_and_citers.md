# Build: Slice 2b — strip the process-label vocabulary; re-point headings and anchors; sweep the `.py` citers

Spec reference: `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` (whole document)
Companion: `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md`
Status: final-accepted

**This pass was resumed after an interrupted run.** The prior Worker 1 invocation died to
an API error part-way through and wrote no artifact; the working-tree diff was the only
record of how far it got. It had completed the `.py` citer sweep across fifteen files and
had not touched the spec — the label population still measured its pre-strip figure when
this pass started. Per `docs/builder/BUILD.md` `### Recovery from interrupted subagent
runs` this is the **same** pass, not a pass 2: the prior run's work was kept, verified,
and completed rather than redone.

This is a combined **Plan + Final-verification** pass under `docs/builder/BUILD.md`
`### Procedural-closure slices` — a spec-and-comment-only change with no builder, on the
maintainer's instruction recorded in `docs/builder/build-039-serializer_mutations-0_0_13.md`
`## Slice 2 split, and why`.

## Spec status-line re-verification

Read `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` lines 1-62. `Status: **SHIPPED
(`0.0.13`)**`, the `DONE-039-0.0.13` card pointer, the five-slice completion claim and the
joint-cut deferral all still describe the tree. No status-line edit owed this pass.

---

## Plan (Worker 1)

### What the diff showed was already done

Attributed by diff content, not by "files this task touches" (`START.md` "Concurrent
sessions"). The prior run had stripped label and severity provenance from the comments of
**fifteen** `.py` files, restating each removed clause in plain words:

`forms/{inputs,resolvers,sets}.py`, `mutations/{inputs,resolvers,sets}.py`,
`rest_framework/{__init__,inputs,serializer_converter,sets}.py`, `utils/inputs.py`,
`utils/querysets.py`, `examples/fakeshop/apps/library/{serializers,schema}.py`,
`examples/fakeshop/test_query/test_library_api.py`,
`tests/rest_framework/{test_converter,test_sets}.py`, and the comment lines of
`rest_framework/resolvers.py`.

It had also discharged **two of the three code-comment fixes** Slice 2a recorded for this
pass (verified below). The spec itself was untouched.

### What this pass had left to do

1. Strip the label vocabulary from the spec — body labels, three heading labels,
   review-round attribution.
2. Re-derive the `.py` citer population independently and finish/verify the sweep.
3. Verify Slice 2a's three code-comment fixes.
4. Re-resolve every `path::Symbol` citation in the spec and the companion.
5. Own the inverse proof the comment-only edits owe.

### Spec slice checklist (verbatim)

This slice has no `## Slice checklist` sub-bullets in the spec — it is a residual-cycle
sub-slice whose contract is the plan's own checklist row. The row, verbatim from
`docs/builder/build-039-serializer_mutations-0_0_13.md`:

- [x] Slice 2b: strip the process-label vocabulary; re-point headings and anchors; sweep the 21 `.py` citers -> `docs/builder/bld-039-slice-2b-label_strip_and_citers.md`

---

## Final verification (Worker 1)

### The population, per instrument

**Every figure below names the instrument that produced it.** Three published figures for
this population already disagreed before this pass ran (165, 175, 186), and the artifact
that dispatched it warned that neither of the surviving two was authoritative. All three
were instruments rather than measurements.

| # | Instrument | Pre-strip | Post-strip |
|---|---|---|---|
| A | `(?:^\|[^A-Za-z0-9_])((?:P\|F\|M\|H\|D)[0-9]+(?:[.-][0-9A-Za-z]+)?)` — Worker 0's published glob, left-bounded only | **186** occurrences / 37 distinct | **10** |
| B | `(?<![A-Za-z0-9_])((?:P\|F\|M\|H\|D)[0-9]+(?:[.-][0-9A-Za-z]+)?)(?![A-Za-z0-9_])` — the same vocabulary, bounded on **both** sides | **177** occurrences / 37 distinct | **1** |
| C | `(?<![A-Za-z])(High\|Medium\|Low\|Critical)(?![A-Za-z])` — bare severity words used as review labels | **2** | **1** |
| D | `rev[0-9]+` / `review follow-on` / `review <label>` — round attribution | **73** (`rev6` 63, `rev2` 6, `review P1` 2, `review follow-on` 1, `review P2` 1) | **62**, all `rev6` |
| E | shape-based, code spans and fenced blocks stripped: `(?<![A-Za-z0-9_])([A-Z][A-Za-z]{0,3}-?[0-9]+(?:[.\-][0-9A-Za-z]+)?)(?![A-Za-z0-9_])` — a **negative**-vocabulary sweep that assumes no letter prefix | **190** / 39 distinct | **14** / 3 |

**Instrument A over-counts by nine, and that is the measurement lesson.** A is bounded on
the left only, so it matches the `M2` inside `M2M` — and the spec says `M2M` nine times.
`186 = 177 real labels + 9 M2M`, proved by counting A-hits immediately followed by a letter
(9, all `M2`) against `grep -c M2M` (9). The distinct-token set is 37 under both instruments
because `M2` is *also* a real label twice, which is exactly why a count alone could not
separate them.

**The true pre-strip population is 177 occurrences over 37 distinct tokens (instrument B),
plus one `Medium-7` severity label (instrument C) that no `P|F|M|H|D`-shaped glob can see —
178 in total.**

**Post-strip residue, enumerated:**

- instrument A's 10 = the 9 `M2M` false positives + the one `H5` below;
- instrument B's 1 and instrument E's `H5` = the spec's `spec-036 AR-H5` citation — a
  **foreign-spec** label, kept under the same rule the dispatch gave for `G2`;
- instrument C's 1 = `` `036` Medium-1 `` — also foreign-spec, kept;
- instrument E's 14 = `G2` ×12 (`spec-035`'s goal vocabulary, cited from here) + `H5` ×1 +
  `ISO-8601-ish` ×1, which is not a label at all;
- instrument D's 62 = the `rev6` vocabulary, **deferred with a named owner** (below).

**`spec-039`'s own label vocabulary measures 0 by every instrument.** Retirement is proved
by re-measurement, not asserted.

### The wider-vocabulary correction to Worker 0's 37-token census

Worker 0's `.py`-side census was 21 label-carrying comment lines across 8 files, derived
from the `(P|F|M|H|D)[0-9]+` glob. **The prior run found a wider vocabulary than that glob
was written to see**, and stripped it: `Md1`, `Md2`, `Md3`, `Md4`, `Md5`, `Md7`, `M1a`,
`SR-3`, `H4`, `D8`, and the bare severity words `High` and `Medium` used as review labels —
across **fifteen** files, the example project and the package test trees included, not
eight. A positive-vocabulary census misses whatever it was not written to see
(`START.md` "Instruments that lie"). This pass re-derived it with two independent
instruments before concluding anything.

**Independent corroboration that the wider vocabulary was the right population:**
`KANBAN.md` card item at line 375 carries a `spec-039` inventory measured by the
**spec-038** residual cycle on 2026-09-03 — `Md1`×3, `Md2`×3, `Md3`×2, `Md4`×2, `Md5`×1,
`Md7`×3, `M1a`×4, `H4`×1 = **19 sites in 10 package modules**. Every one of those 19 is
gone. That board item is now discharged; see `### Notes for Worker 1`, item 1 — the kanban
DB is outside this cycle's fence.

### The `.py` citer sweep, re-derived and verified

Population scanned: **442 `.py` files** under `django_strawberry_framework/`, `tests/`,
`examples/`, `scripts/`.

- **Instrument 1** (Worker 0's): a line containing `spec-039`, widened by a ±3-line window,
  matched against the `P|F|M|H|D` glob. **1 hit**, and it is the `M2M` false positive in
  `utils/querysets.py` #"and the serializer M2M". Zero real hits.
- **Instrument 2** (independent, wider): every **comment token and every docstring line**
  extracted structurally (`tokenize` for comments, `ast` for docstrings — not a line grep),
  matched against `(P|F|M|H|D|Md|SR|AR|G)[0-9]+` plus `Md<n>` / `SR-<n>` / `rev<n>` /
  `High|Medium|Low|Critical`. **152 hits in 50 files**; restricted to the **37** `.py` files
  that mention `spec-039`, **0**. Every one of the 152 belongs to another spec's vocabulary
  (`spec-035` `G1`/`G2`/`G3`, `spec-036` `M3-1`/`AR-H3`, `spec-040` `D<n>`, `spec-030`
  `P1-B`, `spec-033` `P2-3`), is a ruff rule code (`F401`/`F403`/`F822`), or is not a label
  (`U+D800`).

Both instruments agree: **0 residual `spec-039` label tokens in `.py` source.** The bare
`spec-NNN` provenance pointers stay, as `AGENTS.md` keeps them.

### The three heading slugs

Computed by the `START.md` "Markdown link convention" rule — lowercase, drop backticks,
strip non-word except hyphens, each surviving space becomes its own hyphen, an em/en dash
becoming a double hyphen. The slug function was validated first against the spec's and the
companion's **38** existing in-page anchors, all of which it resolved.

| Heading | Old slug | New slug |
|---|---|---|
| `Promotions to single-site now (P1 — third-copy forks)` → `Promotions to single-site now (third-copy forks)` | `#promotions-to-single-site-now-p1--third-copy-forks` | `#promotions-to-single-site-now-third-copy-forks` |
| `Single-siting that prevents drift (P2)` → `Single-siting that prevents drift` | `#single-siting-that-prevents-drift-p2` | `#single-siting-that-prevents-drift` |
| `Small reuses to pin; deliberately not applicable (P3)` → `Small reuses to pin; deliberately not applicable` | `#small-reuses-to-pin-deliberately-not-applicable-p3` | `#small-reuses-to-pin-deliberately-not-applicable` |

**Every reference re-pointed: there were none.** A repo-wide sweep of every tracked `.md`
for the three **old** slugs returned **0 hits** — none in the spec, none in the companion,
none anywhere else. The rename stranded nothing, and that is a measurement, not an
assumption. Verified after the rename: 20 in-page anchors in the spec and 18 in the
companion, **0 dangling** in either direction, and **0 dangling** cross-file anchors into
either file from any tracked `.md`.

**What did need re-pointing was the table's key column and its prose citers.** The
promotion table keyed its rows on the tier ordinals themselves, so the ordinals were
replaced with content names — `START.md`'s rule that a contract is cited by content and a
heading rewrite strands every ordinal:

`P1.1` → **Relation-decode core** · `P1.2` → **Non-delete operation set** · `P1.3` →
**Shape-build cache** · `P1.4` → **Converter dispatch skeleton** · `P1.5` → **Sync
write-pipeline skeleton** · `P1.6` → **Subsystem-clear registration seam** · `P1.7` →
**Build / stash / name seam**. The `P2.1`-`P2.7` bullets keep their own titles with the
ordinal prefix dropped. Six references in the companion that navigated to those rows by
ordinal were re-pointed to the content names in the same pass.

### Two foreign-spec citers the strip stranded, repaired in the same pass

`START.md`: "Rationale move breaks citations in OTHER specs while links still resolve: grep
`spec-<NNN>` across `docs/` before, repair same pass." Two archived specs cited
`spec-039`'s retired vocabulary and would have been left dangling:

- `docs/SPECS/spec-041-channels_router-0_0_14.md` #"release-vs-implementation-docs split" —
  was `(`spec-039`'s F8 discipline)`.
- `docs/SPECS/spec-040-auth_mutations-0_0_13.md` #"owning-module invariant" — was
  the reference-style `spec-039` link followed by a bare `F10`.

Both are one-line, content-preserving repairs inside the cycle's spec-files fence. Post-fix
sweep of `docs/` for `spec-039` adjacent to any label token: **0** (excluding this cycle's
own `bld-039*` / `build-039*` records, the retired `docs/builder/DONE/` artifacts, and
regenerable `docs/shadow/` output).

### `path::Symbol` citations in the spec and the companion

`scripts/check_citations.py` reads `.py` files and `KANBAN.md` only, so it sees **none** of
a spec's citations. An AST resolver over `django_strawberry_framework/`, `tests/`,
`examples/` and `scripts/` was run over both files.

Slice 2a reported fixing 9 of 43 and left the section reading as though all were resolved.
Re-run this pass, **four** were still unresolved in the spec and one in the companion — and
**two of the five were the resolver's own blind spot, not rot**:

- `mutations/sets.py::_shape_build_cache` and `forms/sets.py::_form_shape_build_cache`
  resolve; both are bound by **tuple unpacking**
  (`_shape_build_cache, clear_mutation_shape_build_cache = make_shape_build_cache()`), which
  the first resolver pass did not walk. The instrument was fixed and re-run.
  *A resolver that cannot see a binding form reports its blind spot as a defect.*
- `mutations/sets.py::_VALID_OPERATIONS` → **`mutations/operations.py::_VALID_OPERATIONS`**
  (2 sites). It is imported into `mutations/sets.py`, not defined there, and `AGENTS.md`
  requires the defining module.
- `mutations/resolvers.py::validation_error_to_field_errors` →
  **`utils/errors.py::validation_error_to_field_errors`** (3 sites). Same cause.
- companion `forms/sets.py::_VALID_FORM_OPERATIONS` — the symbol was deleted by the very
  promotion the sentence describes. De-`::`-ed to "the form flavor's private
  `_VALID_FORM_OPERATIONS`", which is what the sentence actually asserts.

Post-fix: **43 distinct citations in the spec, 0 unresolved; 13 in the companion, 0
unresolved.**

### Slice 2a's three code-comment fixes

| # | 2a's note | Status |
|---|---|---|
| 1 | `rest_framework/inputs.py` #"The row is a static STRING pair, so" asserts the superseded row shape | **Done by the prior run, verified.** Now #"The registration passes the executable callback under a stable ``owner``", which agrees with `registry.py::register_subsystem_clear(clear, *, owner, before_bind=False)` and its string rejection. |
| 2 | `rest_framework/__init__.py` "place 3 is the spec **Risks** note" is wrong twice | **Done by the prior run, verified.** Now "place 3 is the spec-039 soft-dependency Decision" — stated by content rather than by ordinal, and correct: `### Decision 12` states `djangorestframework>=3.17.0`, matching `pyproject.toml` #"djangorestframework>=3.17.0" and the guard's own hint. All three places re-read this pass and confirmed to agree. |
| 3 | the label-carrying `spec-039` comment lines and the three headings | **Done this pass**, measured above. |

Four ragged comment wraps the prior run left mid-edit were re-flowed
(`rest_framework/{__init__,sets,inputs}.py`, `forms/inputs.py`), plus one paragraph the
prior run had joined onto a preceding line in the spec's Slice-2 DRY bullet.

### The inverse proof: docstring-stripped AST identity, per file

A comment-only edit owes the inverse of a normal proof — evidence that **nothing executable
changed**. Instrument: parse, delete every module / class / function docstring node,
`ast.unparse`, `sha256`. Reference for a pure file is `git show HEAD:<path>` (`git stash` /
`checkout` / `restore` / `worktree` are banned on this tree).

**The control that proves the instrument can fail.** A docstring-stripped digest cannot be
moved by a docstring-only edit, so a passing comparison proves nothing until the instrument
is shown to fire. Run **per file**, on disk, not in memory: rename the file's first
top-level `def`/`class` (append `_w1probe`), re-digest, restore the original bytes,
byte-compare by `sha256`. **The control fired on all 18 files and the restore was
byte-identical on all 18** — a control in one file says nothing about the other seventeen.

| File | HEAD digest | worktree digest | verdict |
|---|---|---|---|
| `django_strawberry_framework/forms/inputs.py` | `4deb2bc25dea3dd6` | `4deb2bc25dea3dd6` | identical |
| `django_strawberry_framework/forms/resolvers.py` | `8dc5d1bfbec6339e` | `8dc5d1bfbec6339e` | identical |
| `django_strawberry_framework/forms/sets.py` | `cc49fd2cf0ba6891` | `cc49fd2cf0ba6891` | identical |
| `django_strawberry_framework/mutations/inputs.py` | `b3f7834f633dc892` | `b3f7834f633dc892` | identical |
| `django_strawberry_framework/mutations/resolvers.py` | `383e05d245c03f64` | `383e05d245c03f64` | identical |
| `django_strawberry_framework/mutations/sets.py` | `dda7b1ebbca18787` | `dda7b1ebbca18787` | identical |
| `django_strawberry_framework/rest_framework/__init__.py` | `b018691cbe949958` | `b018691cbe949958` | identical |
| `django_strawberry_framework/rest_framework/inputs.py` | `95d9f71cf730828a` | `95d9f71cf730828a` | identical |
| `django_strawberry_framework/rest_framework/resolvers.py` | `24d82cf349fa4ffa` | `909694e2dc340b08` | **MIXED** — enumerated below |
| `django_strawberry_framework/rest_framework/serializer_converter.py` | `558749f580425756` | `558749f580425756` | identical |
| `django_strawberry_framework/rest_framework/sets.py` | `f0eb4387b06f654a` | `f0eb4387b06f654a` | identical |
| `django_strawberry_framework/utils/inputs.py` | `b0231575fceb9bcb` | `b0231575fceb9bcb` | identical |
| `django_strawberry_framework/utils/querysets.py` | `c9521a81f0c56a06` | `d90ff6f72fdc1718` | **MIXED** — enumerated below |
| `examples/fakeshop/apps/library/schema.py` | `23a0ffac18080f12` | `23a0ffac18080f12` | identical |
| `examples/fakeshop/apps/library/serializers.py` | `4b31f547608ccf93` | `4b31f547608ccf93` | identical |
| `examples/fakeshop/test_query/test_library_api.py` | `a414c9371f692fa8` | `a414c9371f692fa8` | identical |
| `tests/rest_framework/test_converter.py` | `0da32492c4d4b437` | `0da32492c4d4b437` | identical |
| `tests/rest_framework/test_sets.py` | `50baf9a46efc511a` | `50baf9a46efc511a` | identical |

**The two MIXED files: `HEAD` is not the comment-only reference.** For these, the proof is
the docstring-stripped AST **delta**, enumerated independently and shown to contain only
the concurrent session's and Slice 3's executable changes:

- **`rest_framework/resolvers.py` — one hunk, entirely Slice 3's fail-open fix** in
  `_assert_field_agreement`: `return` on a missing `_mutation_meta` becomes a
  `ConfigurationError` raise, and the two sibling `getattr(meta, …, default)` reads become
  direct `meta.operation` / `meta.optional_fields` reads. That is exactly the change this
  cycle's `bld-039-slice-3-code_gaps.md` accepted; nothing else appears in the delta.
- **`utils/querysets.py` — four sites, all the concurrent session's `unevaluated` →
  `evaluated` defect-code rename**: the code tuple in `_validate_post_orderset_result`, the
  `_seal_or_defect` return, and the two message-dict keys in `_visibility_result_error` /
  `_prepared_visibility_source`. No other executable difference. This pass's own edit to the
  file is the single docstring line in `sync_pipeline_recourse`, and it is absent from the
  delta — which is the point.

`examples/fakeshop/test_query/test_products_api.py`,
`tests/rest_framework/test_resolvers.py` and `tests/rest_framework/test_dry_import_ratchet.py`
are Slice 3's accepted work and were **not** touched by this pass; `list_field.py`,
`orders/sets.py`, `tests/orders/test_sets.py`, `tests/utils/test_querysets.py`,
`resource_policy.py`, `_strawberry_patches.py` and `docs/feedback.md` are the concurrent
`spec-050` session's (`AGENTS.md` rule 34) — neither edited nor reverted.

### Gate results

| Gate | Command | Result |
|---|---|---|
| ruff format | `uv run ruff format <the 18 .py files>` (scoped, never `.`) | **pass** — `18 files left unchanged` |
| ruff check | `uv run ruff check --fix <the same 18>` | **pass** — `All checks passed!` |
| source layout | `uv run python scripts/check_trailing_commas.py <the 18 .py files> <spec> <companion>` (explicit paths) | **pass** — `Fixed 0 file(s).` |
| source layout, foreign-citer repairs | `… scripts/check_trailing_commas.py docs/SPECS/spec-040-… docs/SPECS/spec-041-…` | **pass** — `Fixed 0 file(s).` |
| spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-039-serializer_mutations-0_0_13.md` | **pass** — `OK: 38 terms` (unchanged) |
| citations | `uv run python scripts/check_citations.py --check` | **pass** — `OK: 963 citations resolve (808 in 442 .py files, 155 in KANBAN.md)` — unchanged, no reduction |

Checks the gates cannot perform, run by hand and reported above: the spec-side
`path::Symbol` AST resolution (43 / 0 unresolved, companion 13 / 0), the in-page and
cross-file anchor audit (0 dangling either direction, both files), and the link-definition
audit in **both** directions — spec 115 defs / 115 uses, companion 60 defs / 60 uses, 0
undefined refs, 0 orphan definitions, all ten canonical group headers present and in order
in both files, every definition target existing on disk.

Line length: no line this pass wrote exceeds the graced 110; ASCII-only holds across all 18
`.py` files (checked with `LC_ALL=C grep` for any byte outside printable ASCII plus tab).
Staged-anchor sweep for `TODO(spec-039` / `TODO-ALPHA-039`: no live anchor in source — the
only hits are prose describing the convention.

Spec `316,338 B` → **`315,306 B`** (3,950 lines). Companion `122,960 B` → **`125,139 B`**.

### Summary

`spec-039`'s process-label vocabulary is retired, measured to 0 by five instruments, with
the foreign-spec labels the dispatch carved out (`G2`, `AR-H5`, `036 Medium-1`) left in
place. Every clause a deleted label justified was restated in plain words from the code
rather than trimmed; the promotion table is keyed on content names instead of tier
ordinals. Three headings were renamed and their slug changes measured against a repo-wide
sweep that found no inbound reference to strand; two archived sibling specs that *did* cite
the retired vocabulary were repaired in the same pass. The `.py` citer sweep is complete and
verified at 0 by two independent instruments across 442 files, and the comment-only edits
carry a per-file docstring-stripped AST-identity proof whose control was shown to fire on
every file.

### Spec changes made (Worker 1 only)

All edits are to `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` unless noted.

| # | Region | Change | Reason |
|---|---|---|---|
| 1 | document head, `## Goals`, `## Slice checklist` Slices 0-4 | Deleted 178 body-label tokens inline in prose, restating the clause each carried. Examples: `(**P1.4**)` after the fail-loud dispatch clause deleted (the clause already names the skeleton and its home); `**P1.4**'s four dispatch-skeleton symbols` → `the four dispatch-skeleton symbols`; `(M5)` after "avoid third copies" deleted; `(**F9**)` after the `validate()`-not-`HiddenField` rule deleted. | `AGENTS.md` / `START.md` "Style Rio cares about" bans process provenance from standing prose. |
| 2 | `## Slice checklist` → Slice 2 clear-seam block | `(P1.6, F10, M4 — NOT two hand-edits)` → `— NOT two hand-edits`; the import-timing bullet's `(F10)` dropped. The mandatory-seam and fail-loud-on-rename clauses are stated directly. | Same. |
| 3 | `## Slice checklist` → Slice 2 `**DRY / reuse**` | Labels removed **and** the paragraph re-split: Slice 2a had joined "The serializer's genuinely-new `_validate_meta` logic…" onto the end of the preceding line behind five spaces. | Same edit region; a mid-line paragraph join is a wrap defect, not content. |
| 4 | `### Cross-flavor reuse and DRY obligations` → the three sub-headings | `### Promotions to single-site now (P1 — third-copy forks)` → `(third-copy forks)`; `### Single-siting that prevents drift (P2)` → no suffix; `### Small reuses to pin; deliberately not applicable (P3)` → no suffix. Slugs and the zero-inbound-reference sweep recorded above. | Same. |
| 5 | the promotion table | Key column renamed from `#` to `Promotion`, and each row's ordinal replaced by a content name (list above). The four in-cell ordinal cross-references (`the waste P1.7 names`, the `P1.3` / `P2.1` / `P1.7` layering note, `(**P2.1**) rides with it`, `(**F10**)`) restated by content. | `START.md`: cite a contract by content, never ordinal — a heading rewrite strands every ordinal. |
| 6 | `### Single-siting that prevents drift` bullets | `- **P2.1 — unify the field-spec…**` → `- **Unify the field-spec…**`, and the six siblings likewise; the two cross-references between them (`the shared **P1.2** set`, `see **P2.7**`, `companion to P2.5`) restated by content. | Same. |
| 7 | `### Single-siting that prevents drift` → constructor-hook bullet | `H3 invariants` → `framework-owned invariants`; `(spec-039 Medium-7 — the dead-hook removal)` → `the hook is not the place for them`. | The only severity-ordinal label in the spec's own voice; instrument C is the only thing that sees it. |
| 8 | `### Decision 4` shared-helper homes, `### Decision 6`, `### Decision 7`, `### Decision 8`, `### Decision 10`, `### Decision 12`, `## Edge cases`, `## Test plan`, `## Doc updates`, `## Definition of done`, `## Implementation plan` table, `### Import manifest` table, `## Round-6 improvements` bodies | Same strip, clause-preserving, across every remaining site. | Same. |
| 9 | `### rev6 #6`, `### rev6 #10`, `### rev6 #3`, `### rev6 #17` | Round attribution removed: `(rev6 rev2 P2: …)`, `(**rev2 P2**)` ×3, `(**rev2 P1**: …)`, `(review P1)` ×2, `(review follow-on P2)`, `(review P2 — …)`, `(H6)`. Each clause survives; the `rev2 P1` one was rewritten from a chronology ("the earlier reassignment erased…") into the standing reason ("a reassignment would erase…"). | `AGENTS.md` bans review-round/worker attribution outright; a sentence that only made sense as history was rewritten, not trimmed. |
| 10 | `### Decision 8` step 3, `## Edge cases`, `### Single-siting…` | `mutations/resolvers.py::validation_error_to_field_errors` → `utils/errors.py::validation_error_to_field_errors` (3 sites). | The symbol is defined in `utils/errors.py` and only imported into `mutations/resolvers.py`; `AGENTS.md` requires the defining module. Ungated — `check_citations.py` does not read specs. |
| 11 | `### Decision 10`, promotion table | `mutations/sets.py::_VALID_OPERATIONS` → `mutations/operations.py::_VALID_OPERATIONS` (2 sites). | Same. |
| 12 | `docs/SPECS/spec-040-auth_mutations-0_0_13.md` #"owning-module invariant" | Dropped the stranded `F10`. | A foreign citer of the retired vocabulary; `START.md` requires the repair in the same pass. |
| 13 | `docs/SPECS/spec-041-channels_router-0_0_14.md` #"release-vs-implementation-docs split" | The bare `F8` replaced by the named discipline, keeping the existing reference-style link to `spec-039`. | Same. |

### Rationale companion changes (Worker 1 only)

`docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md`. The file is
append-only for new deliberation, but a sentence the pass falsified may not stand
(`docs/builder/BUILD.md` `## Spec rationale extraction` rule 2).

- **Six ordinal references into the spec's promotion table re-pointed** to the new content
  names (`[P1.5][spec-039-dry]` → the sync-write-pipeline-skeleton link, `the **P1.6** table
  cell`, `the **P1.5** table cell`, `what P1.5 was for`, `**P1.2**'s promotion`, `the P1.2
  table cell`).
- **`forms/sets.py::_VALID_FORM_OPERATIONS` de-`::`-ed** — the sentence's own point is that
  the symbol no longer exists, so the `path::Symbol` form was wrong to use.
- **The "Slice 2 obligation — the 202 process labels" bullet rewritten** into the record of
  what actually happened: the three disagreeing published figures and why they disagreed,
  the measured 177 + 1, and the foreign-spec carve-outs. Its closing claim ("The
  **process-label vocabulary** is deliberately still there") was false the moment the strip
  landed.
- **A new bullet on the three heading renames** — old and new headings, the zero-inbound
  sweep, and why the table key column moved to content names.
- **The `rev6` bullet re-headed "Still owed"** and given its measured figures (62 in the
  spec, 18 here) plus the reason it is not folded into the label strip.
- **The closing "On that vocabulary" bullet rewritten** into the wider-vocabulary
  correction: the dispatched 21-line / 8-file census versus the measured 15 files and the
  `Md<n>` / `SR-3` / `D8` / `High` / `Medium` tokens the dispatching glob could not see.
- One link definition added (`spec-035`), in its canonical group header and alphabetical
  within it.

The companion **keeps** its own label vocabulary (69 occurrences). That is deliberate and
matches every prior cycle: measured at `HEAD`, the rationale companions of `spec-030` (35),
`spec-036` (55) and `spec-038` (17) all retain theirs. The rationale file is the dated
record of what a review round found, which is exactly the carve-out `AGENTS.md` draws
around standing prose.

### Notes for Worker 1 (spec reconciliation)

Each item has a named owner. Nothing is routed forward unowned.

**For the maintainer / a follow-on pass — outside this cycle's fence:**

1. **`KANBAN.md` card item at line 375 is discharged and the board does not know it.** It
   inventories 19 `spec-039` stranded-ordinal sites in 10 package modules, measured by the
   spec-038 residual cycle on 2026-09-03, and routes them to a work-package batch. All 19
   are gone. The item also asserts "`spec-039` … has no rationale companion", which Slice 0
   falsified. The kanban DB is outside this cycle's maintainer-set fence
   (`docs/builder/build-039-serializer_mutations-0_0_13.md` `## What this cycle is`), so no
   edit was made. **Owner: the maintainer, or whichever card owns the WP batch.**
2. **The published claim that motivated this pass is false.** The build plan's `## Known
   hazard carried into this cycle` says "Every prior residual cycle stripped that vocabulary
   from its spec (030, 036, 037, 038 all carry zero)". Measured at `HEAD` with instrument B
   over `docs/SPECS/`: `spec-030` **0**, `spec-038` **7** (all foreign `G2`), `spec-037`
   **2** (`P0`) — but **`spec-036` carries 146** (`G2` 31 plus `H1`-`H5` / `M1`-`M7`, which
   are severity-ordinal review labels in its own voice). `spec-039` was **not** the last one
   holding them. **Owner: the maintainer** — whether `spec-036` gets the same strip is a
   scope question, not a custodial one.

**For a follow-on `039` pass (Worker 0 to dispatch):**

3. **The `### rev6 #N` heading vocabulary — 17 headings, 62 occurrences in the spec and 18
   in the companion.** It is review-round attribution in exactly the sense `AGENTS.md` and
   `START.md` ban, and Slice 0 logged it as a Slice-2 obligation. It was **not** folded into
   this pass: the dispatch scoped the heading work to exactly three headings, and retiring
   `rev6` re-keys a whole section — the `## Round-6 improvements (better-than-graphene-django)`
   heading is itself round provenance and is the anchor **both** files link to
   (`[rationale-rev6]`, `#round-6-improvements-better-than-graphene-django`), so the rename
   would strand a live cross-file anchor that the three-heading rename did not. Doing it
   unbidden inside a pass with no reviewer would be the "while I'm here" this repo
   explicitly refuses. Measured and left; it is the last banned vocabulary in the spec.

**Carried unchanged from Slice 2a, still open — re-read this pass and not re-raised:**

4. Escalations A (should the DRY import ratchet hold the spec's named promotions or the
   whole measured shared substrate, and should it cover the forms flavor), B (the
   `isinstance` tightening on the tolerated `_mutation_meta` shape), and C (`HEAD` is red
   from `spec-050` at `4c483b6b` in four modules this cycle does not touch, so
   `bld-039-final.md` cannot record a green full sweep). **Owner: the maintainer.**
5. The two `rest_framework/inputs.py` duplications, the `f"SerializerMutation {…}: "`
   message-prefix duplication in `rest_framework/resolvers.py`, and the
   `tests/rest_framework/test_dry_import_ratchet.py` docstring wrap. **Owner: the
   cross-slice integration pass / `bld-039-final.md`'s deferred-work catalog.**
6. The DRY existence challenge on `mutations/sets.py::cached_build_input`. **Owner: the
   integration pass.** No change either way this pass.

**No executable change was made, and none is owed.** No comment stripped this pass turned
out to describe a real defect; the two that described a superseded contract
(`rest_framework/inputs.py`'s clear-row shape and `rest_framework/__init__.py`'s
three-places note) were comment-only corrections, verified against `HEAD` above.

### Final status

`final-accepted`. The strip is complete and re-measured to 0 by five instruments; every
citer is repaired, in the spec, in the companion, in the fifteen `.py` files and in the two
sibling specs; the inverse proof holds per file with a control shown to fire per file; all
gates pass with `check_citations` and `check_spec_glossary` unchanged.

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
