# Build: Cross-slice integration pass (026)

Spec reference: `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` (whole file; 21,324 bytes at the start of this pass, 21,567 at its close)
Status: final-accepted

Worker 1 alone, per `docs/builder/build-026-scalar_conversion_fakeshop-0_0_7.md` `Ownership partition: none`. No `.py` change surfaced, so no consolidation loop through Workers 2 and 3 is required.

Build-plan declarations, re-verified against the cycle's landed diff rather than accepted from the plan:

- **Ownership partition:** none. Three sequential slices, one cohort.
- **Hot-path declaration:** none. The cycle's whole diff is 18 added / 17 removed prose lines in two `.py` files (zero executable) plus three Markdown files.
- **Floor-verification scope:** none. No import, no Django / Strawberry / channels API, no version-sensitive construct anywhere in the cycle's diff.
- **Failability proofs:** `None; this cycle introduced no new boundary.` Nothing in the diff branches, guards, gates, or rejects.
- **Boundary count: 0.** Split question answered without a split.

---

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked.** Not applicable in the package sense, and recorded rather than silently skipped. No slice of this cycle wrote a Python statement, so the package-wide AST inventory (`worker-1.md` `### Package-wide helper inventory before helper planning`) has no candidate shape to match against. Shapes searched for instead, in the surfaces this cycle *did* write: a measurement stated at two sites that could disagree, a claim the spec and the rationale both assert, and a locator cited from more than one file. Results under `### DRY findings — prose`.

- **Existing patterns reused.** The pass reuses three instruments the cycle already established rather than inventing new ones: occurrence counting via `grep -o | wc -l` (never `grep -c`), the fixed-width-digit-placeholder technique for any byte count this artifact or the rationale states, and the D2/D3 rule — replace a census with a locally verifiable statement, never with a fresh census.
- **New helpers justified.** None.
- **Duplication risk avoided.** This artifact states no number that the spec or the rationale also states as contract; where a number appears in both, the spec or rationale owns it and this file cites the instrument. The one exception is deliberate: the spec's closing byte count (21,567) appears both in the rationale's provenance table and in this artifact's header line, because the header is this pass's own before/after and was measured here.

### Implementation steps

1. Read every prior `026` artifact in slice order, in full (`BUILD.md` `## Cross-slice integration pass` step 1, no "as needed").
2. Record the static-inspection disposition for every `.py` file the build touched (steps 2-4), with the actual **Repeated string literals** and **Imports** content rather than a bare skip.
3. Sweep the tree for this build's staged anchors (step 6).
4. Walk every accepted artifact's `What looks solid`, `DRY findings`, and `Notes for Worker 1` for deferred follow-up landing here (step 5).
5. Re-derive every claim the prior passes made — the MOVE, the keying, the history-narration sweep, both census polarities, D11, D12, every link definition and `#"substring"` citation — measuring each number as it is written.
6. Fix what the pass finds in the two files Worker 1 is custodian of; record each edit.
7. Re-run the gates and consolidate the deferred-work catalog for the final gate.

### Test additions / updates

None, and none possible. The cycle writes no Python. `AGENTS.md` #"No pytest after edits" applies and no test run is owed by this pass; the focused live module was run three times during Slice 2 (`29 passed`, `--no-cov`, no `--cov*` flag) and both edited modules were proved to still parse by `py_compile`. The full sweep belongs to `bld-final-026.md`.

### Implementation discretion items

None. There is no second worker to delegate to.

### Dispatched findings checklist

This is not a review round and `spec-026` had no `## Slice checklist` when the cycle opened, so the boxes below are the six mandatory preconditions of `BUILD.md` `## Cross-slice integration pass` plus the verification obligations the dispatch adds, decomposed so the audit at the close has something to audit.

- [x] Precondition 1 — every prior `bld-slice-*-026` artifact read in slice order, in full, including all six sections of Slice 2
- [x] Precondition 2 — static-inspection disposition recorded for every `.py` file the build touched
- [x] Precondition 3 — **Repeated string literals** compared across every shadow overview
- [x] Precondition 4 — **Imports** compared across every shadow overview
- [x] Precondition 5 — every accepted artifact's `What looks solid` / `DRY findings` / `Notes for Worker 1` walked for deferred follow-up
- [x] Precondition 6 — staged-anchor sweep for `TODO(spec-026` / `TODO-<MILESTONE>-026`, board files excluded
- [x] The rationale MOVE is real — overlap between spec and rationale measured, not asserted
- [x] The rationale is keyed to the spec — every entry's heading and anchor resolves, and `## Key forwarding` covers every stale key
- [x] The spec narrates no history — sweep re-run over the final spec text
- [x] Census claims re-measured in **both** polarities across the spec and the rationale
- [x] D11 (six retired package tests) verified against git read-only
- [x] D12 (four-commit footprint) verified against git read-only
- [x] Every link definition resolves on disk from its own file's directory; no dangling, no unused, no broken cross-file `#fragment` except the one deliberate retirement; every `#"substring"` citation matches its target exactly once
- [x] Citations into generated files (`KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`) identified and their guard named
- [x] Cross-slice prose DRY scan across the artifacts, the spec, and the rationale, with an owner decided per finding
- [x] Gates green: `check_spec_glossary.py`, `check_trailing_commas.py --check`, `git diff --check`

---

## Final verification (Worker 1)

Every number below was measured in this pass. Nothing is inherited from the build plan, from any slice artifact, or from my own memory file — including numbers those sources and this pass agree on.

### Precondition 2, 3 and 4 — the static inspection helper: recorded skip, with the data

`scripts/review_inspect.py` was **not run on a code diff by any slice of this cycle**, and that is the correct disposition rather than a gap. The helper's output is repeated-literal, ORM-marker, control-flow and import evidence over Python constructs; the cycle's `.py` diff contains **18 added and 17 removed lines, zero of them executable** (measured this pass: `git diff HEAD -- examples/fakeshop/apps/scalars/models.py examples/fakeshop/test_query/test_scalars_api.py` -> 4 hunks, and every added line is inside a docstring or a `#` comment; Slice 2's pass-2 verification says 5, and 4 is the measured figure). Slices 2 and 3 each recorded the skip with this reason in their own `### DRY findings`; this pass confirms it against the diff rather than accepting it.

Two overviews nonetheless exist under `docs/shadow/`, so preconditions 3 and 4 are answered with content rather than an absence:

| Overview | **Repeated string literals** | **Imports** |
| --- | --- | --- |
| `examples__fakeshop__apps__scalars__models.overview.md` (pre-flight step-2 smoke run on the one `.py` file this cycle edited) | **None.** | `from decimal import Decimal`; `from django.db import models`. Two imports, no cross-folder import, one-way direction holds. |
| `django_strawberry_framework__scalars.overview.md` | **None.** | stdlib + `strawberry` + one local `from .exceptions import …`. Belongs to the concurrent `025` cycle's surface, not this one; recorded because it is in the folder, and it introduces no boundary crossing either. |

**Cross-file literal candidates: zero.** A literal must appear in two or more overviews to be one, and both overviews report `None`. `examples/fakeshop/test_query/test_scalars_api.py`, the cycle's second edited file, has no overview and needs none: its diff is four prose passages and `BUILD.md` `### When to run the helper during build` scopes the obligation to added *logic*.

### Precondition 6 — staged-anchor sweep

```shell
grep -rEn 'TODO\(spec-026|TODO-(ALPHA|BETA|STABLE)-026' . --exclude-dir=.git \
  --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md
```

**Three hits, zero of them anchors.** All three are this cycle's own artifacts quoting the sweep command in prose (`bld-slice-2-026-…md` twice, `bld-slice-3-026-…md` once). No shipped source, test, comment, spec, or standing doc carries an anchor naming this spec or card. Including the board files raises the total to the same three, so no unshipped board card is being masked either.

### Precondition 5 — deferred follow-up walked across every accepted artifact

Every `What looks solid`, `DRY findings`, and `Notes for Worker 1` section of the three slice artifacts was read. Disposition of each open item:

| Source | Item | Disposition in this pass |
| --- | --- | --- |
| Slice 2, `### Notes for Worker 1` (Worker 3, pass 1) | Escalated Medium: `apps/scalars/models.py` module docstring #"covered transitively by every other example app" | **Closed before this pass and not re-opened.** Worker 1's pass-1 final verification measured it TRUE at HEAD app by app, and Worker 3 re-verified independently in pass 2. Resolution path (c) — recorded out of scope with the fence stated — is what landed. Nothing owed here. |
| Slice 2, `### Notes for Worker 1` (Worker 3, pass 2) | Correct the 13-of-14 column count when the final gate quotes it | **Discharged.** Worker 1's pass-2 corrected it in place to 12 of 13 with an inline pointer. Not restated as a number by this pass or by the spec, so there is nothing left to quote wrongly. |
| Slice 2, `### Carried to Slice 3` items 1-3 | Two false clauses in one spec sentence; scope any "no delete mutation" claim to the app; sweep both polarities | **All three discharged by Slice 3 and re-verified here.** `git grep -F 'only cross-model FK in the scalars app' docs/SPECS/` -> 0; `git grep -F 'only \`SET_NULL\` ondelete in the example tree' docs/SPECS/` -> 0. The spec's `## Non-goals` item 3 is app-scoped by name. The both-polarity sweep is re-run below — and it needed a **third** polarity. |
| Slice 3, `### Deferred work` items 1-5 | `KANBAN.md` / `KANBAN.html` / `CHANGELOG.md` parallel sites | **Re-derived, consolidated, and carried to the final gate** under `### Deferred work catalog, consolidated`. One of the five was not deferred work at all and one contained a falsified population statement; both are corrected there. |
| Slice 1, `### Notes for the spec-reconstruction slice` | Dangling `[example-schema]` / `[settings]` uses; unused `[backlog]` definition | **Discharged by Slice 3 and re-verified here:** 26 definitions in the spec, 26 uses, zero unused, zero dangling, every path resolves on disk. |

### The rationale MOVE is real — measured, not asserted

Two independent instruments, both run in this pass over both files with the link-definition blocks and fenced code stripped:

| Instrument | Result |
| --- | --- |
| exact-sentence intersection (sentences >= 60 characters) | spec **114**, rationale **187**, shared **0** |
| 9-gram token intersection | **20** shared 9-grams |

The 20 nine-grams are not duplicated content. Nineteen are the spec's own title, four Decision headings quoted as the rationale's keys, and the peer-standard companion-pointer sentence — exactly the "short quoted mechanism names" and "a fragment the rationale needs verbatim" the dispatch anticipates. Exactly **one** is substantive prose and it is recorded as a DRY finding below. Slice 1's move proof re-run at HEAD independently: `grep -c "no other example app reaches"` -> **0** in the spec, **4** in the rationale; `grep -c 'two-\`CreateModel\`'` and `grep -c 'SET_NULL\` ondelete behavior'` -> **0** in the spec.

**The +75-byte reading is still honest, and it was still being mis-framed.** The arithmetic holds (3,593 -> 3,668, and 3,668 - 3,593 = 75, re-derived from `git show HEAD:<spec> | wc -c` and the Slice-1 figure), and the growth is correctly attributed to the pointer plus its link definition exceeding the one clause available on a 3.6KB stub. What was no longer honest was the **table**: its `After` column still read 3,668 / 17,340 after the reconstruction took the two files to five and twice their size, so a reader at HEAD took a Slice-1 measurement for a current one. Fixed as edit 5 below.

### The rationale is keyed to the spec — every key resolved

Eight `**Keys to:**` lines, one per entry plus the forwarding table's own. Resolved mechanically against the spec's 21 headings using GitHub slug rules (backticks and `*` stripped, underscores **kept** — the trap my memory records: a home-grown slugger that strips `_` as an emphasis marker indicts the file first):

| Keyed to | Resolves |
| --- | --- |
| `## Other` (D4, D5) | **No** — deliberate, and covered |
| whole file (D1, `## Key forwarding`) | n/a |
| `### Decision 3 …` (D2/D3) | yes |
| `## Non-goals` (D6) | yes |
| `### Decision 5 …` + `## Test plan` (D11) | yes |
| `## Slice checklist` + `## Doc updates` (D12) | yes |

**`## Key forwarding` covers every stale key, not just the one.** Measured rather than assumed: `grep -n 'spec-026-other'` returns **four** lines — two `**Keys to:**` lines (D4, D5), the forwarding table's own explanation, and the link definition. The `#other` fragment is the **only** unresolved fragment in either file, and the table's two rows are exactly D4 and D5. Every entry appended after the table keys to a heading that exists. Both of the table's named destinations were checked against the spec: `### Decision 1 — Paired models, not one model with paired columns` and the nine-test subsection of `## Test plan` both exist.

One cosmetic mismatch, decided and not edited: the `**Keys to:**` lines and the forwarding table quote the Decision headings with an ASCII hyphen (`### Decision 3 - The two relation shapes…`) where the spec's headings carry an em dash. The link anchors resolve, so no reader is misdirected; editing it would revise an entry the rationale's append-only rule protects, for no reader benefit.

### The spec narrates no history — sweep re-run

```shell
grep -inE 'previously|used to|no longer|formerly|as of |amend|retract|rev-[0-9]|round [0-9]|earlier version' \
  docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md
```

**One hit**, and it stays: the header block's companion-pointer sentence, which is the peer-standard form `spec-021` and `spec-013` both carry and which describes what the rationale *contains*. Re-run after this pass's four spec edits -> still one hit; none of my edits reintroduced a chronology, which is the failure Slice 3 recorded catching twice inside the very pointer lines the move rule requires.

**Slice 3's audit table is wrong about its own result here** (`### Spec slice checklist audit`, box 11: "the narration grep -> 0 hits"), while its `### History-narration check` section four screens earlier correctly says the rerun returns one hit that stays. One is the right answer. Artifact-internal, recorded under `### Low:` rather than fixed — a prior artifact is the accepted record of work already done.

### Census claims re-measured — and the sweep needed a THIRD polarity

Both polarities first, over the final spec, counting occurrences and not matching lines:

```shell
grep -ioE '\bonly\b|\bsole\b|\bno other\b|\bthe one\b|\bevery\b|\ball\b|\beach\b|\balways\b' <spec> | wc -l
# 35   (only 4, every 13, all 5, each 13, and zero each of sole / no other / the one / always)
```

**35, and Slice 3's 35 is correct** — the decomposition above reproduces it exactly. (Its own audit table says "21 hits read"; 35 is the measured figure. Second internal contradiction in the same table, recorded below.) Every one read in context. No hit quantifies over the example tree, the repository, or "no other example app"; the surviving universals quantify over the ten non-trivial `SCALAR_MAP` rows, the columns one named model declares, or the nine tests one named module carried at ship — each a closed population named in its own sentence.

**And a census survived both polarities anyway.** `## Goals` item 4 read:

> Two relation shapes **the fakeshop otherwise lacks** are exercised under the optimizer: an intra-model self-FK with its reverse accessor, and a nullable cross-model FK whose detach is observable.

Neither vocabulary reaches "otherwise lacks". It is a tree-wide census, it was true at the ship commit, and it is **false at HEAD in both halves**:

| Claimed shape | Measured at HEAD | Instrument |
| --- | --- | --- |
| intra-model self-FK with a reverse accessor | `apps/kanban/models.py::Decision.supersedes` -> `"self"`, `related_name="superseded_by_set"`, and **both** sides are selected in `apps/kanban/schema.py`'s `Meta.fields`, so it is planned by the optimizer exactly as `ScalarSpecimen.parent` is. `apps/glossary` additionally carries a self-M2M (`GlossaryTerm.related_terms`). | `grep -n '"self"' examples/fakeshop/apps/*/models.py` -> 3 hits: `glossary`, `kanban`, `scalars` |
| nullable cross-model FK | `apps/kanban/models.py::CardItem.verified_by` -> `Actor`, nullable, `SET_NULL` | the four-`SET_NULL` measurement below |
| the same at the ship commit | **true then** — only `scalars` carried a `"self"` FK; `library` and `products` carried none | `git show 2701eb88:…/models.py \| grep -c '"self"'` -> 0, 0, 1 |

This is the third consecutive pass of this cycle in which a census defect turned on the **vocabulary of the sweep rather than its diligence**: Slice 2's plan swept negative vocabulary only and a positive universal reached review as an escalation; Slice 3 added the positive vocabulary and its own sweep caught two universals it had just written; this pass added a third vocabulary and found one both had passed over. Fixed as edit 2 below.

Over the rationale: 84 occurrences of the same two vocabularies. Every census-shaped sentence is either a quotation of a dead claim, an explicit falsification of one, or the entry's own measured replacement claim. The one live census the rationale asserts is D4's replacement, and it was re-derived here by re-running the AST script the file publishes for exactly that purpose:

| D4 replacement claim | Re-derived this pass | Matches |
| --- | --- | --- |
| example models carrying concrete columns | **48** | yes |
| all-nullable models among them | exactly one, `scalars.NullableScalarSpecimen` | yes |
| identical-column-set pairs | **6**, of which the `scalars.ScalarSpecimen` <-> `scalars.NullableScalarSpecimen` pair (11 columns) is the only all-non-null / all-nullable one | yes, and the "five other pairs are all-non-null on both sides" clause holds for all five |

### D11 verified against git, read-only

```shell
git show a5c89c98 -- tests/types/test_converters.py | grep '^-def test_'   # -> 6
git show a5c89c98 -- tests/types/test_converters.py | grep -c '^-.*managed = False'   # -> 6
```

**Six** deleted test functions, named exactly as the spec's `## Test plan` deletion list names them, and **six** deleted `managed = False` lines — so Decision 5's "each stood up a synthetic `managed = False` owner model" is measured, not assumed. All six are absent at HEAD (`grep -c "def <name>" tests/types/test_converters.py` -> 0, six times). `CHANGELOG.md` names three; that undercount is a fenced catalog item, not a spec defect. **D11 confirmed; the spec states six and six is right.**

### D12 verified against git, read-only

`git log --grep 'DONE-048' --format='%h %ad %s'` -> **eight** commits, all 2026-05-27. Each classifying sentence re-read in this pass rather than taken from D12's table:

| Commit | Time | Classifying sentence, read this pass | Verdict |
| --- | --- | --- | --- |
| `cae2d5a3` | 17:27:11 | `Part of DONE-048-0.0.7.` | card |
| `2701eb88` | 17:27:26 | `Part of DONE-048-0.0.7.` | card |
| `a5c89c98` | 17:27:42 | "Two related cleanups in tests/types/test_converters.py that fell out **of the DONE-048 converter-coverage audit**" | card |
| `45a8f301` | 17:27:57 | "closes the standing-docs hygiene piece of DONE-048-0.0.7" | card |
| `b148fde7` | 17:56:07 | "Audit followup batch 2"; 231 added lines in `test_scalars_api.py` (`git show --numstat`) | not the card |
| `0b91a123`, `5addc067`, `72f6cd9b` | later | each dates itself against the card ("after the DONE-048 audit migrations", "post-DONE-048") | not the card |

`git show --stat --format= --name-only <c> | grep -c '^django_strawberry_framework/'` -> **0** for each of the four, so Decision 6 and definition-of-done item 12 are measurements. **D12 confirmed: four commits.** Its "29 minutes later" for `b148fde7` was checked rather than waved through — 17:27:26 to 17:56:07 is 28 min 41 s, which rounds to 29 against the substrate commit. Correct as written.

**D12 also falsifies a line of the spec that D12 itself did not reach.** The four commits map onto the reconstructed spec's three slices as 1:1, 1:1, and 2:1 — `a5c89c98` (the retirement) and `45a8f301` (`CHANGELOG.md` / `KANBAN.md` / `TODAY.md` / `docs/TREE.md`, confirmed by `--name-only`) are both Slice 3. The `## Slice checklist` preamble said "Each top-level item maps to one commit." Fixed as edit 1 below.

### Link definitions and `#"substring"` citations — both files, resolved from each file's own directory

| Check | Spec | Rationale |
| --- | --- | --- |
| definitions | 26 | 19 |
| reference-style uses | 26 | 19 |
| unused definitions | 0 | 0 |
| dangling uses | 0 | 0 |
| definition paths missing on disk | 0 | 0 |
| broken cross-file `#fragment` | 0 | **1** — `[spec-026-other]`'s `#other`, deliberate and covered by `## Key forwarding` |
| in-page `](#…)` anchors that do not resolve | 0 | 0 |
| all 10 canonical group headers present, in order | yes | yes |

`#"substring"` citations: **two**, both in the spec, both `[`AGENTS.md`][agents] #"Test through real usage, prefer the example project"`. The target string occurs in `AGENTS.md` exactly **once** (`grep -c` -> 1), so both citations resolve uniquely. The four `path::Symbol` citations were resolved too: `converters.py::convert_scalar`, `library/schema.py::PatronType`, `test_scalars_api.py::test_scalars_set_null_ondelete_detaches_partner_in_http_query`, and `test_library_api.py::test_library_patron_bigint_lifetime_fines_over_http` all exist.

**Citations into generated files, flagged as the dispatch requires.** The spec carries **three** anchor citations into the DB-rendered `docs/GLOSSARY.md`: `#bigint-scalar`, `#djangotype`, `#finalize_django_types`. All three resolve today. All three would die on a regenerate that moved a heading, with no edit to the spec — but this is the one such case with a standing mechanical guard: `scripts/check_spec_glossary.py` exists to catch exactly it, is green on this spec (`OK: 3 terms - all have glossary entries and at least one spec link.`, exit 0), and runs in pre-commit and CI. Recorded as guarded rather than as a finding. Neither file carries a citation into `KANBAN.md` or `KANBAN.html` with a fragment; both cite them whole, which no regenerate can break.

### Contract re-derivation — every remaining spec claim measured at HEAD

| Spec claim | Measured this pass | Result |
| --- | --- | --- |
| `SCALAR_MAP` has twenty-six rows; sixteen collapse to `int`/`str`; ten do not | `len(SCALAR_MAP)`, and the non-`(int, str)` subset, under `config.settings` | **26 / 16 / 10**, and the ten named in the spec are exactly the ten measured |
| `ScalarSpecimen` selects every converted column plus `parent`, `children`, `nullable_partners` | `Meta.fields` parsed | 16 entries = 15 card-era + `tag` (a later card's) |
| `NullableScalarSpecimenType` selects every converted column | same | 13 entries |
| the nine named live tests exist at HEAD and at ship | `grep -c '^def <name>'` on the file and on `2701eb88`, nine times each | 1 at HEAD and 1 at ship for all nine; ship module total **9**, HEAD total **29** |
| Decision 4's boundary values | `grep` in both live modules | `_SIGNED_BIG = 9223372036854775000`; `2**53 + 12345` in `test_library_api.py` |
| `Patron.lifetime_fines_cents`, selected in `PatronType` | `library/models.py`, `library/schema.py` | `BigIntegerField(default=0)`; in `Meta.fields`; also in `Meta.exclude` of the redacted sibling type, which the card does not claim |
| `apps/scalars/tests/` ships empty | `git ls-tree -r 2701eb88 …/tests/` | exactly `__init__.py`. `test_models.py` arrived 2026-05-29 on `9ade8c98`, a different card. Ship-tense claim, true. |
| every later-growth surface named in `## Card snapshot` exists | `grep` per symbol | `ScalarSpecimenTag`, `Base36Field`, `OverrideSpecimen`, `MediaSpecimen`, `filters.py`, `orders.py`, `forms.py`, `Mutation` with exactly its two create fields, and `"tag"` in `ScalarSpecimenType.Meta.fields` — all present |
| the four standing docs carry the card (DoD 13) | `grep` per file | `CHANGELOG.md:175`, `KANBAN.md:121` (and the `0.0.7` summary at `:62`), `docs/TREE.md` (the app at `:884`, the live module at `:653`), `TODAY.md:374` |
| `## Non-goals` item 2's "already read over HTTP wherever the other example apps select one" | six installed example apps, each with its own live `test_query/` module selecting trivial-collapse columns | holds at app granularity; read and kept |
| `SET_NULL` occurrences in example models | `grep -o … \| wc -l`, never `grep -c` | **4** at HEAD, **1** at `2701eb88` |
| `apps/scalars` initial migration | `grep -c` | **5** `CreateModel` + **1** `AddField` at HEAD, **2** at ship |
| D4's ship-time comparison set | `git show 2701eb88:…` | `library` 8 models / 7 `CreateModel` / 7 sibling `DjangoType`s + `Query`; `products` 4 models / 4 `DjangoType`s + `Query`; apps present: `library`, `products`, `scalars` |
| structural counts the rationale states about the spec | `grep -c` on the finished spec | 10 top-level sections, 6 Decisions (vs `spec-021`'s 8), 5 goals, 5 non-goals, 3 slices, 9 enumerated tests, 13 definition-of-done items — every one matches |

One claim this pass **cannot** verify and says so rather than passing it: Decision 5's "Package coverage of the underlying rows stays at 100% through the live tests." Worker 1 is forbidden any `--cov*` flag in any pass, so the number is not measurable here. It restates the standing `fail_under = 100` gate rather than asserting a new measurement, and the maintainer's gate owns it. Recorded, not graded.

### High:

None.

### Medium:

#### `## Goals` item 4 carried a tree-wide census that both prior sweep vocabularies missed

Measured false at HEAD in both halves (table under `### Census claims re-measured` above), true at the ship commit. Same defect class the cycle retired from three `.py` sites, from the spec's Decision 3, and from `## Other`; it survived because "otherwise lacks" is neither `only`/`sole`/`no other` nor `every`/`all`/`each`. **Fixed this pass** (edit 2).

#### Rationale `D1` asserted a census over `docs/SPECS/` that is false, inherited unmeasured from the build plan

`D1` read: "It was the only file in the `015`+ builder-format era with no `## Architectural decisions`". Measured this pass across the 42 specs numbered `015` and up:

```shell
# at HEAD
NO ## Architectural decisions: spec-016-fieldmeta_consolidation-0_0_6.md
                               spec-024-django_trac_37064_hardening-0_0_7.md
                               spec-026-scalar_conversion_fakeshop-0_0_7.md
# on disk now
NO ## Architectural decisions: spec-016-fieldmeta_consolidation-0_0_6.md   (9,103 bytes)
```

**Three at HEAD, not one**, and `spec-016` still lacks the heading on disk. `spec-024` was itself a `## Card snapshot` / `## Planning note` / `## Other` stub at HEAD — structurally identical to `026`'s — and lost that shape only because the concurrent `024` session reconstructed it uncommitted. The claim traces to the build plan's `D1` ("`026` is the only file after `014` with zero `## Architectural decisions`") and was carried into the rationale without re-derivation, which is the one thing the rationale's own `## Entry shape` section forbids. **Fixed this pass** (edit 3), by the rule the cycle established rather than by a corrected census: the sentence's job is that the stub had no auditable contract, which needs no population at all.

#### Rationale `## Ship provenance` contradicted `D12` in the same file

Its opening sentence said the card "shipped in the joint `0.0.7` cut across two commits" above a two-row table, while `D12` twenty-three screens later says four and lists them. A reader of the framing section got a false count with no signal that a later entry overturns it — the half-reconciled shape the cycle's own standard calls worse than an uncorrected one. **Fixed this pass** (edit 4).

#### The `## Slice checklist` preamble said each top-level item maps to one commit

False for Slice 3, which is `a5c89c98` plus `45a8f301` (file lists confirmed by `--name-only`). The line is the peer convention lifted from `spec-021` and `spec-023`, where it happens to be true; here `D12`'s own arithmetic — four commits, three slices — falsifies it, and no pass had put the two together. **Fixed this pass** (edit 1).

### Low:

#### Decision 3 cited a later card's test as the card's live pin, unmarked

`test_scalars_set_null_ondelete_detaches_partner_in_http_query` is absent from `2701eb88`'s module (`grep -c` -> 0) and was added by `c43e443e`, "Closes carry-forward item #2 from the audit-followup top-5" — not one of the card's four commits, and never naming `DONE-048`. It is correctly named as where the behavior is pinned **at HEAD**, but the sentence read as though the card delivered it, while the spec's own `## Test plan` and definition-of-done item 9 list nine tests that exclude it. **Fixed this pass** (edit 6) with one clause, in the same voice `## Card snapshot` already uses to attribute later growth. Incidental provenance, not a spec claim: `c43e443e` is also the origin of both `test_scalars_api.py` passages Slice 2 retired.

#### The rationale's byte table read as current after the reconstruction

`3,668` / `17,340` under a column headed `After` described a state two passes stale. **Fixed this pass** (edit 5): the columns are now `Before the move` / `After the move` / `At the integration pass`, with the third column measured here by the file's own fixed-width-placeholder technique.

#### The rationale asserted the spec's `## Other` section in the present tense

Line 29 read "The spec's `## Other` list **is** a near-verbatim lift…" after Slice 3 dissolved the section. **Fixed this pass** in the same edit as the commit count (edit 4), pointing at `## Key forwarding`.

#### Slice 3's artifact carries two contradictions with its own body, neither previously checked

Its `### Spec slice checklist audit` says the census sweep read "21 hits" (its `### Both-polarity census sweep` section says 35; **35** is the measured figure) and that "the narration grep -> 0 hits" (its `### History-narration check` says one hit that stays; **one** is right). Both are artifact-internal. Recorded and not fixed: an accepted artifact is the record of work already done, and this artifact is where the corrected numbers now live for the final gate.

#### The rationale quotes Decision headings with a hyphen where the spec uses an em dash

Cosmetic; every anchor resolves. Not edited, for the append-only reason.

### DRY findings — prose

The dispatch's target, and the cycle's characteristic defect: one claim written once and copied, then rotting in every copy.

- **Spec vs rationale: one substantive overlap, owner decided.** Of 20 shared 9-grams, exactly one is prose rather than a title, a heading quoted as a key, or the peer-standard companion sentence: **"their coverage stays in `tests/` against package-internal fixtures"**, in the spec's `## Non-goals` item 1 and in the rationale's `D6`. **The spec owns it** — it is normative, it is the card's scope boundary, and `D6`'s whole subject is that the boundary was missing from the spec. The rationale's copy sits inside the argument for that non-goal and carries no number, so the two cannot disagree numerically; a future edit to either leaves the other true. Kept, recorded, owner named.
- **Spec vs the two Slice-2 `.py` files: 19 shared 7-grams, and Slice 3's own DRY promise is not quite kept.** Slice 3's `### DRY analysis` stated "The spec must not carry a second copy of that sentence." Its landed diff does carry the causal clause: the spec's Decision 3 says "`SET_NULL` rather than `CASCADE` because every field `NullableScalarSpecimen` declares is nullable: losing the target must clear `partner_id` and leave the mirror row in place", and `models.py`'s `partner` comment says "`SET_NULL` rather than `CASCADE` because every field this model declares is `null=True`: losing the target must clear the FK, never delete the mirror row." The other substantive runs are "nullable cross-model FK to `ScalarSpecimen` (`on_delete=SET_NULL`)", "both are PostgreSQL-only and the fakeshop runs on SQLite", "recursive `select_related` / `prefetch_related` planning against a model whose relation target is itself", and "serializes as JSON `null` when the column is `NULL`". **Decided: no edit, and the split as it stands is right.** `worker-1.md`'s implementation-relevant carve-out keeps the "why" that changes how a thing is built in the spec, so the spec cannot drop the causal clause; the `.py` comment states the same invariant at the code, which is its job. Load-bearing distinction: **no overlap carries a measurement.** Every shared run is a structural fact about two named models, verifiable from those models, so neither copy can drift into disagreeing with the other the way `SET_NULL`-is-4-not-1 did. What is recorded is that Slice 3's stated prevention did not hold, so the next pass does not read it as proven.
- **No repeated literal, key, tuple shape, helper, or export anywhere in the cycle.** The diff adds no Python symbol of any kind, so the usual subjects have none. Both shadow overviews report `Repeated string literals: None`.
- **Locators cited from more than one file: checked, and one was wrong.** Slice 3's catalog item 2 states of the `D4` shape "exactly two lines, one in each file, and no third site anywhere" — from a grep scoped to `KANBAN.md CHANGELOG.md`, and its own item 4 adds `KANBAN.html`. A grep's file list is not a population; fourth recurrence of that trap in this cycle. Re-derived unscoped below.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` -> empty. No file under `django_strawberry_framework/` was opened by any slice of this cycle, `__all__` is unchanged, and the spec's Decision 6 and definition-of-done item 12 are backed by the four-commit `--name-only` measurement above rather than by assumption.

### CHANGELOG sanity

Not applicable; no slice of this cycle modified `CHANGELOG.md`. It is on the build plan's baseline-dirty do-not-edit list, and two of its claims about this card are fenced catalog items below.

### Documentation / release sanity

- The spec's header block re-verified per `worker-1.md` `## Spec status-line re-verification`, this pass: `Target release: 0.0.7 (per KANBAN.md card DONE-026-0.0.7)` — confirmed against `KANBAN.md:121` and the `0.0.7` summary at `:62`. `Status: shipped (0.0.7, 2026-05-27); archived. Card DONE-026-0.0.7.` — consistent with all four card commits being dated 2026-05-27. **No status-line edit owed.**
- `## Slice checklist` boxes are all `- [ ]` and correctly so: on an archived Done card the `Status:` line is the source of truth and the boxes stay unticked.
- No KANBAN movement, no `docs/GLOSSARY.md` edit, no `-terms.csv` edit, no `docs/TREE.md` regenerate. The maintainer's spec-and-`.py` scope fence held; `check_spec_glossary` is green on the unchanged three-term CSV.
- No script-rendered doc was touched, so the staging-language rule has no subject.

### Temp test verification

- Temp test files used: **none**. `docs/builder/temp-tests/` carries nothing for this cycle.
- Disposition: not applicable. Every question in this pass is whether a written claim is true of the tree, which is answered by measuring the tree.

### Gate results

| Command | Result |
| --- | --- |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-026-…md` | `OK: 3 terms - all have glossary entries and at least one spec link.` exit **0** (re-run after every edit) |
| `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` | exit **0**, `--check` deliberately (the default auto-fixes) |
| `git diff --check` | exit **0** |
| link definitions, both files, disk-checked from each file's own directory | all resolve |
| `git status --short` | my writes are **exactly** the two spec-side files. `examples/fakeshop/apps/scalars/models.py` and `test_query/test_scalars_api.py` carry Slice 2's landed uncommitted work, untouched and unreverted; every other modified or untracked path is the baseline-dirty out-of-scope list or the concurrent `024` / `025` sessions', including two that have grown since Slice 3's snapshot (`docs/SPECS/spec-025-…md` and `docs/SPECS/appx/spec-024-…-rationale.md`). Observed, not touched. |

No `pytest` run in this pass, with or without a `--cov*` flag. The full sweep is the final gate's.

### Spec changes made (Worker 1 only)

Six edits, four to the spec and two to the rationale. Nothing else in either file was touched.

1. **`docs/SPECS/spec-026-…md`, `## Slice checklist` preamble.** `Each top-level item maps to one commit.` -> `Slices 1 and 2 each map to one commit. Slice 3 maps to two: the package-test retirement and the standing-docs wrap land separately.` Reason: false as written — `D12`'s four commits across three slices means Slice 3 is `a5c89c98` plus `45a8f301`, confirmed by each commit's `--name-only`. Triggered by this pass's `D12` re-derivation.
2. **`docs/SPECS/spec-026-…md`, `## Goals` item 4.** The tree-wide census `Two relation shapes the fakeshop otherwise lacks are exercised under the optimizer: an intra-model self-FK with its reverse accessor, and a nullable cross-model FK whose detach is observable.` -> `Two relation shapes on the coverage models are exercised under the optimizer: ScalarSpecimen.parent, an intra-model self-FK with its reverse children accessor, and NullableScalarSpecimen.partner, a nullable cross-model FK whose detach is observable over HTTP.` Reason: false at HEAD in both halves (`apps/kanban::Decision.supersedes` and `apps/kanban::CardItem.verified_by`), true at ship. Replaced with a statement nothing outside `apps/scalars` can falsify, per the rule `D2`/`D3` established. Triggered by this pass's third-polarity sweep.
3. **`docs/SPECS/appx/spec-026-…-rationale.md`, `D1`, `### The state being replaced`.** `It was the only file in the 015+ builder-format era with no ## Architectural decisions, and it had no ## Slice checklist, ## Test plan, ## Doc updates, or ## Definition of done either.` -> `It carried no ## Architectural decisions, and no ## Slice checklist, ## Test plan, ## Doc updates, or ## Definition of done either.` Reason: the census is false (three specs lacked the heading at HEAD; `spec-016` still does on disk) and was inherited from the build plan unmeasured. **This is a deliberate, recorded exception to the rationale's append-only rule** (`worker-1.md` `### Performing the rationale move` rule 4), taken on the narrowest possible scope: the rule protects an entry's *argument* from being re-litigated under a new address, and no argument changed — the entry's point is that the stub had no auditable contract, which the replacement states without quantifying over any population. Shipping a false census inside the file whose subject is false censuses is the one outcome the rule cannot be read to license. Flagged here so the final gate sees the exception rather than discovering it.
4. **`docs/SPECS/appx/spec-026-…-rationale.md`, `## Ship provenance`.** Framing sentence corrected from two commits to **four**, naming `a5c89c98` and `45a8f301` beside the two-row `Part of`-formula table and pointing at `D12` for the classification rule; the following paragraph's present-tense assertion of the spec's `## Other` section rewritten to name the section as dissolved and point at `## Key forwarding`. Reason: `D12`, in the same file, falsified both; a framing section left contradicting an entry gives the reader two answers and no verdict. Front matter, not an entry's argument.
5. **`docs/SPECS/appx/spec-026-…-rationale.md`, `## Provenance of this record` byte table.** Columns relabelled `Before the move` / `After the move` / `At the integration pass`, a third column added carrying **21,567** and **36,728**, and the surrounding sentence scoped so the move's own figures are not read as current. Both new figures were produced by the file's own technique — table written with fixed-width digit placeholders, `wc -c` run, equal-width digits substituted — so the substitution cannot move the number it reports. Reason: the `After` column described a state two passes stale. The `+75` claim and its explanation are untouched and re-verified correct.
6. **`docs/SPECS/spec-026-…md`, Decision 3, final clause.** Appended `, which belongs to a later card and is not among this card's nine tests below` to the sentence naming the live pin. Reason: the test postdates the card (`c43e443e`), is absent from `2701eb88`'s module, and is excluded from the spec's own nine-test plan and definition-of-done item 9; unmarked, the citation implied the card shipped it. Phrased in the voice `## Card snapshot` already uses to attribute later growth, so no history is narrated.

Both files were re-gated after every edit; the census, history-narration, link, anchor and citation sweeps were all re-run over the final text and are the figures reported above.

### Deferred work catalog, consolidated for the final gate

Slice 3 catalogued five items; re-derived here unscoped, because a catalog is a claim. **Three live items**, one duplicate merged, one non-item dropped.

1. **`KANBAN.md` and `KANBAN.html` carry the retired two-false-clause sentence verbatim.** `grep -rln 'only cross-model FK in the scalars app' --exclude-dir=.git .` -> six files: `KANBAN.md` (1 occurrence), `KANBAN.html` (1), and four that are this cycle's own record (the rationale quoting it as a retired claim, and three `026` builder artifacts). **The spec copy is gone.** Both clauses are false at HEAD — four `SET_NULL` occurrences in example models, and two cross-model FKs in the scalars app. **Fenced three ways and closable by no slice of this cycle:** both files are on the build plan's baseline-dirty do-not-edit list; the maintainer's scope fence limits the cycle to spec and `.py` files; and both are DB-rendered, so a fix is a fakeshop kanban DB edit plus `scripts/build_kanban_md.py`, never a hand edit (`KANBAN.html`'s Vue shell is additionally hand-maintained and only its data block regenerates).
2. **`KANBAN.md`, `KANBAN.html` and `CHANGELOG.md` each carry `D4`'s retired shape.** `grep -o 'no other example app' <file> | wc -l` -> **1** in each of the three; the unscoped `grep -rln` finds no fourth live site. This merges Slice 3's items 2 and 4, whose split is what let item 2's "no third site anywhere" stand while item 4 named the third site. Same three fences; the `CHANGELOG` line is additionally a historical ship record.
3. **`CHANGELOG.md`'s entry for this card undercounts twice.** It names **three** retired package tests where `a5c89c98` retired **six** (`D11`), and describes the live surface as "eight tests" where nine shipped (`D5`) — both re-measured in this pass (`grep -o 'eight tests' CHANGELOG.md | wc -l` -> 1; the three `BigInt` names present, the three `JSON` names absent). Same fences. **One omission produced both**: the test the spec's enumeration lost is the test whose three retirements the changelog lost.

Dropped from the catalog, recorded so it is not re-opened: `docs/TREE.md`'s one-line description of `test_scalars_api.py` ("scalar wire formats, filtering, relations, and optimizer behavior"). Re-read this pass — it describes the module's HEAD surface accurately and says nothing false about this card. Slice 3 already marked it "not deferred work"; it is not an item.

### Summary

The integration pass found the cycle's three slices delivered what they claimed and re-derived every claim they made: the MOVE is real (zero shared sentences between spec and rationale, 20 shared 9-grams all accounted for), the rationale is fully keyed with `## Key forwarding` covering both stale keys and no others, the spec narrates no history, `D11`'s six retired tests and `D12`'s four-commit footprint both hold against git, and every link definition, in-page anchor, cross-file fragment and `#"substring"` citation resolves except the one deliberately retired `#other`.

Four claims did not survive re-derivation, and every one is the cycle's own signature defect turned on text the cycle itself wrote: a tree-wide census in `## Goals` item 4 that both prior sweep vocabularies structurally could not reach; a census in rationale `D1` inherited unmeasured from the build plan and false three ways over; a `## Ship provenance` framing section still saying two commits while `D12` says four in the same file; and a `## Slice checklist` preamble promising one commit per slice that `D12`'s own arithmetic refutes. All four are fixed, plus a Decision 3 citation that credited the card with a later card's test and a byte table that read as current two passes after it was measured. No finding needed a `.py` change; no consolidation loop is required.

### Outcome

`final-accepted`. Sixteen checklist boxes, sixteen ticks, each evidenced above. Six spec-side edits, all recorded, one of them a deliberate and flagged exception to the rationale's append-only rule. Gates green: `check_spec_glossary` exit 0, `check_trailing_commas --check` exit 0, `git diff --check` exit 0, every link path disk-checked. Ownership-partition, hot-path, floor-verification and failability declarations all `none` and all re-verified against the landed diff. Three deferred items carried to the final gate, all fenced, with two of Slice 3's five merged or dropped after re-derivation. Two spec-side files written; no `.py` file, no `-terms.csv`, no generated doc, no baseline-dirty or concurrent-session file opened for writing.

Status: final-accepted

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
