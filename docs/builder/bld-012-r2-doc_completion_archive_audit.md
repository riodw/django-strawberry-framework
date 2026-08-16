# Build: Item R2 — documentation completion and archive audit (spec-012)

Spec reference: `docs/SPECS/spec-012-version_release_alignment-0_0_4.md` (whole file, 57 lines) and
`docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-rationale.md` (whole file, 434 lines after
this pass; 364 before)
Plan reference: `docs/builder/build-012-version_release_alignment-0_0_4.md` `### R2 findings` (F9-F12)
Predecessor artifact: `docs/builder/bld-012-r1-rationale_and_spec_reconciliation.md` (`final-accepted`)
Status: final-accepted

A **combined plan + build + final-verification pass performed by Worker 1 alone**, authorized by the
plan's `## Dispatch record` row for R2: the findings live inside the spec and its companions, and no
source or test is in the writable set. `### Isolation is non-waivable` binds a pass that writes code;
this one writes Markdown only. The row's escape hatch — "unless it turns up a durable-doc or DB
edit" — **did not fire**: no `KANBAN.md` card-body edit and no kanban-DB edit is owed, and the
reasoning is in `### 5. The card body`, reached independently of R1's conclusion.

**`HEAD` moved under this pass.** The plan and R1 both measured at `5851bb59`; a concurrent session
committed `c2b8622d` ("docs(types): correct the loaded_attr attribution…") before this pass started,
and that commit also **deleted `docs/builder/bld-011-r*.md`** — the staged deletions the plan
recorded are now landed. Every figure below is measured at `c2b8622d`, and the two figures that
depend on the release history were re-derived rather than carried from R1.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable in the code sense, and recorded rather than skipped:
  this item's writable set is four Markdown paths, so `worker-1.md` `### Package-wide helper
  inventory before helper planning` has no candidate surface. The documentary equivalent was run —
  R1's closed artifact, both files it wrote, the terms CSV, and the precedent pass
  (`bld-011-r2-doc_completion_archive_audit.md`, recoverable at `2b7e5b16` since `c2b8622d` deleted
  it) were read in full before any check was designed.
- **Existing patterns reused.** The audit method is the precedent pass's, not a new one: every path
  is disk-checked from the **writing file's own directory**; the masked-rot probe is a probe for
  duplicated *names* rather than for missing paths; the terms-CSV constraints are read out of
  `import_spec_terms.py` rather than assumed; the DB is read from a **scratchpad copy**. The F9
  rationale entry follows the file's existing entry structure verbatim (*Nothing moved* / the change
  and its cause / *The alternatives rejected* / *Claim the spec may not make*).
- **Duplication risk avoided.** Three. (a) The F9 entry does **not** restate the `## What the card
  actually did` history R1 already recorded; it cross-references the byte-identity finding and adds
  only what is new. (b) It does not re-argue the `[backlog]` deferral R1 decided. (c) It quotes **no**
  version of `CHANGELOG.md`'s `## Versioning` section into the spec — quoting a thrice-revised
  section into a file nothing re-renders is the `## Card snapshot` mistake in a new place, and that
  reasoning is written into the entry as a rejected alternative rather than left implicit.
- **New shared shape justified.** None. The deliverables are the F9 rationale entry and this artifact.

### Implementation steps

1. Re-derive F9 from the blobs — the header at `231911a8`, the `27ed0b30` diff, and the **current**
   shape of `## Versioning` — never from the dispatch's account of any of them.
2. Disk-check every link definition in both files from the file's own directory, and run the
   masked-rot probe on names rather than paths.
3. Verify the scaffold mechanically (ten headers, order, alphabetical within group) and measure
   unused / undefined definitions with code spans stripped.
4. Run `check_spec_glossary.py` and `check_trailing_commas.py --check` on both files.
5. Verify the terms CSV against `import_spec_terms`'s **enforced** constraints, read from the command
   source, and confirm the DB agrees — from a read-only copy. Run `--check` only after proving from
   the source that it writes nothing.
6. Re-derive F12's population by token occurrence, and settle the renumber question the `[spec-011]`
   cluster raises.
7. Judge the `DONE-012-0.0.4` card body independently of R1's conclusion, against `231911a8`'s actual
   diff and against the board's own register.
8. Write the F9 entry into the rationale, then this artifact, then the memory entry.

### Test additions / updates

None, and none is possible: this item lands no code. `AGENTS.md` rule 15 applies, the plan declares
hot-path `none` and floor-verification scope `none`, and the final gate owns the suite. No `pytest`
was run and no `--cov*` flag was used anywhere.

### Implementation discretion items

- Where the F9 entry keys. Decided at plan time: to **`## Scope`**, not to a new spec heading and not
  to `## Scope` 2 as an amendment of it. F9's subject is the frame around every one of the five
  surfaces, not a property of the changelog bullet alone, and `worker-1.md` requires an entry keyed
  to a removed or non-existent heading to anchor a surviving section — `## Scope` is the section it
  bears on.
- Whether the rationale's `## How to read this file` roadmap is amended. Decided: **yes, minimally.**
  It stated the deliverable as "a single structural fault"; after F9 there are two, and a stale
  roadmap in the one file this pass owns is a defect, not a stylistic preference. One bullet changed;
  no entry rewritten. `BUILD.md`'s append-only rule governs the entries, and none was edited.

### Dispatched findings checklist

- [x] **F9** — the release policy `0.0.4` was cut under was rewritten a week later. Re-derived from
      the blobs and written into the rationale as a keyed entry. See `### 1. F9`.
- [x] **F10** — the archive move is done; what R2 owes is the audit and the companion's own link
      hygiene. Audited; see `### 2. Archive audit`. 21 definitions across the two files, 21 resolve.
- [x] **F11** — the card's glossary anchor resolves and its rendered status matches the board; the
      terms CSV is importable, not merely green under the lenient gate. Re-derived; see
      `### 3. Glossary anchor and terms-CSV importability`.
- [x] **F12** — no `[spec-012]` ref-id ambiguity. Re-derived, and the plan's wording **no longer
      reproduces** while its substance does. See `### 4. F12`.
- [x] **F8 (carried from R1)** — the unused `[backlog]` definition confirmed still present, still
      unused, and still explained in the rationale. See `### 6. F8 confirmed`.

---

## Final verification (Worker 1)

### 1. F9 — the release policy, re-derived from the blobs

Every element was measured; nothing was accepted from the dispatch or from the plan.

**At the cut.** `git show 231911a8:CHANGELOG.md` — the header is two lines: "The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)," / "and this project adheres to [Semantic
Versioning](https://semver.org/spec/v2.0.0.html)." So `0.0.4` was cut under a header asserting strict
SemVer adherence.

**The commit that changed it.** `27ed0b30439a32f90195b4ec8dc9642e866045d9`, "update plan;",
**2026-05-15** — seven days after `231911a8` (2026-05-08). `--stat`: `CHANGELOG.md` only, **14
insertions, 3 deletions**. It deleted the SemVer clause (the header became "The format is based on
[Keep a Changelog]…**.**") and inserted a `## Versioning` section of five milestone rows, the first of
which read "**Pre-alpha (`0.0.x`)** — … Strict [Semantic Versioning](…) does **not** apply here." It
also rewrote the file's closing line from "Pre-alpha; the public API is unstable until `0.1.0`" to a
pointer at the new section.

**The current shape, measured at `c2b8622d` rather than restated from `27ed0b30`.** The alpha row's
substantive claim is unchanged. Three presentational things moved:

| Element | At `27ed0b30` | At `c2b8622d` | Commit |
|---|---|---|---|
| first row label | `**Pre-alpha (`0.0.x`)**` | `**Alpha (`0.0.x`)**` | `2bd7cb84`, 2026-05-16 (`-S` on the literal) |
| last row label | `**Post-stable (`1.x.y`)**` | `**Stable (`1.x.y`)**` | same |
| milestone card refs | literal ids `BETA-033-0.1.0`, `STABLE-042-1.0.0`, inline `](KANBAN.md)` links | reference-style links to board cards **052** and **067** | board renumber + link-convention sweep |
| `## [Unreleased]` | present | **absent from the file** | `24d11143`, 2026-06-16 ("Release 0.0.10") |

This is why the entry records the *fact of the frame moving* rather than quoting any one version of
the section: the section has been revised at least three times since it replaced the SemVer line.

**The finding's sharpest point, which the plan did not state.** Every one of these edits sits
**above** the release entries. The `## [0.0.4]`-to-`## [0.0.3]` block is untouched by all of them —
re-extracted at this pass from `git show 231911a8:CHANGELOG.md` and from the working tree, **2,621
bytes each**, `diff` exit 0, so V3 reproduces at the new `HEAD` as well. The spec's live guarantee
"no later commit rewrites it" therefore holds **and is blind to F9**: byte-identity of an entry says
nothing about the policy the entry was written under. That blindness is the argument for writing the
fact down.

**Where it landed, and why nothing in the spec changed.** A new entry, `### `## Scope` — the release
policy `0.0.4` was cut under was rewritten a week later`, keyed to `[Scope][spec-012-scope]`, placed
after the two `## Scope` entries and before `## Other`. It carries the file's existing structure and
four rejected alternatives — stating the change in `## Scope` (chronology, which `BUILD.md`
`## Spec rationale extraction` forbids a spec); adding a standing "not a SemVer release" sentence to
the spec (a per-release file restating a repo-wide policy is the `## Card snapshot` duplication
again, and the three revisions above show it would drift the same way); treating it as out of scope
because no surface moved (a release-*alignment* reader is exactly the reader who asks what the
version number meant); and annotating `CHANGELOG.md`'s `0.0.4` entry (`AGENTS.md` rule 21 closes the
file, and it would break the byte-identity the spec guarantees). The claim recorded as one the spec
**may not make** is that `0.0.4` was, or is, a Semantic Versioning release.

`## How to read this file`'s roadmap bullet was amended in the same pass from "a single structural
fault" to two findings, so the file's own map is not stale. No existing entry was edited —
`worker-1.md` `### Performing the rationale move` rule 4 keeps the entries append-only.

### 2. Archive audit of the spec and its companion

**Every link definition resolves from the file's own directory** — checked by `[ -e ]` after `cd`
into the defining file's directory, fragment stripped, and each target then normalized through
`realpath` and compared against intent.

| File | Definitions | Result |
|---|---|---|
| `docs/SPECS/spec-012-version_release_alignment-0_0_4.md` | 9 | all resolve from `docs/SPECS/` |
| `docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-rationale.md` | 13 (12 + `[changelog]`, added this pass) | all resolve from `docs/SPECS/appx/` |

The depths differ as they must: the spec reaches the root with `../../` and `docs/` with `../`; the
companion, one level deeper, uses `../../../` and `../../` and reaches the spec with `../`.

**The masked-rot trap: probed on names, and this cluster has no instance of it.** A depth error is
invisible to an existence check only when a same-named file sits at the shallower depth, so the probe
is for duplicated basenames across the tree:

- `BACKLOG.md`, `KANBAN.md`, `CHANGELOG.md`, `pyproject.toml`, `uv.lock` — **one occurrence each**,
  all at the repository root. No shallower twin exists to mask a wrong depth.
- `GLOSSARY.md` — one occurrence, `docs/GLOSSARY.md`.
- `README.md` — **five occurrences**, including the root/`docs/` pair that is the canonical trap.
  **Neither file links to a README at all**, so the one masking pair in the repository cannot fire
  here.
- `worker-0.md` / `worker-1.md` — **four occurrences each** (`docs/dry/`, `docs/review/`,
  `docs/builder/`, `docs/builder/worker-memory/`). These are duplicated *names*, but they differ in
  their **parent directory**, not in depth: a depth error from `docs/SPECS/appx/` varies the `../`
  count while keeping the `builder/` segment, and every such variant (`../builder/…`,
  `../../../../builder/…`) is a path that does not exist. The duplication is therefore unmaskable in
  this direction, and the two definitions were confirmed to resolve to `docs/builder/`.
- `__init__.py` / `test_init.py` — the spec's two source definitions resolve to
  `django_strawberry_framework/__init__.py` and `tests/base/test_init.py`. A shallower variant would
  be `docs/django_strawberry_framework/…`, which does not exist.

**Dotted-version anchors: no exposure.** The trap is that `0.0.7`-style headings slug to `007`, not
`0_0_7`. Every anchor either file carries is `#card-snapshot`, `#scope`, or `#djangotype` — none
version-dotted, so no slug can be mis-derived. All three resolve: `## Card snapshot` (spec line 9),
`## Scope` (spec line 14), and `## `DjangoType`` in the **committed** `docs/GLOSSARY.md` (line 765,
read via `git show HEAD:` since the working copy is a concurrent session's).

**Scaffold, mechanically checked.** Both files carry the single `<!-- LINK DEFINITIONS -->` delimiter
and all ten canonical group headers in `START.md`'s exact order (compared against the literal list).
Alphabetical within every group, including after `[changelog]` was inserted between `[backlog]` and
`[kanban]`. Subdirectory rule respected: the companion's `docs/SPECS/appx/` definitions sit under
`<!-- docs/SPECS/ -->`; no eleventh header invented. No inline `](path)` cross-file link in either
body. No fenced code block in either file, so the four-backtick drop-in hazard does not arise.

**Unused / undefined definitions, measured with code spans stripped** (the known trap: `KANBAN.md`
appears three times in the companion but always inside a code span, so a naive sweep would call
`[kanban]` used):

- Spec: 9 defs, **1 unused** (`[backlog]`), 0 undefined.
- Companion: 13 defs, **2 unused** (`[backlog]`, `[kanban]`), 0 undefined. `[changelog]` is used by
  the F9 entry, which is why it was added.

**Checker runs, both after the F9 edit.**

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-012-version_release_alignment-0_0_4.md`
  -> `OK: 1 terms - all have glossary entries and at least one spec link.` **exit 0**
- `uv run python scripts/check_trailing_commas.py --check <spec> <companion>` -> **exit 0**

**F10 therefore reproduces**: the move is done and correct, and the companion R1 created is clean at
its own depth.

### 3. Glossary anchor and terms-CSV importability (F11)

**The CSV.** `docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-terms.csv` — the header
`term,anchor,notes` and **one** row: `DjangoType,djangotype,Backfilled for DONE-card glossary linkage
from the shipped release-alignment stub.` One row, one anchor, so the unique constraint
`check_spec_glossary` cannot see is satisfied trivially.

**Constraints read from the source, not assumed** —
`examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py::Command._load_rows` and
`::Command._assert_plan_matches_db`:

- **Anchor uniqueness** (`CommandError(f"Duplicate glossary anchor …")`) — one anchor. This is the
  constraint the lenient authoring gate tolerates: `check_spec_glossary` is anchor-keyed and accepts
  a many-term-to-one-anchor grammar that `_load_rows` rejects.
- **Header keys** — `DictReader` reads `term` / `anchor` / `notes`; all three present and non-blank
  (a blank `term` or `anchor` is skipped, and skipping the only row would trip `No terms loaded`).
- **`GlossaryTerm` must exist** (`Missing GlossaryTerm anchor`) — `glossary_glossaryterm` carries
  `anchor='djangotype'`, id 460, `status_text = shipped (`0.0.5`)`.
- **Path resolution** — `_resolve_spec_path` raises on an ambiguous basename. `kanban_specdoc` row 35
  already stores the **archived** path `docs/SPECS/spec-012-version_release_alignment-0_0_4.md`, so
  the basename fallback is never reached.
- **Companion location** — `_terms_path` prefers a sibling `…-terms.csv` beside the spec and falls
  back to `appx/`. No sibling exists at `docs/SPECS/`, so the `appx/` copy is the one that loads.
  (History: the CSV was moved into `appx/` at `40e4754a`, 2026-07-31.)
- **The DB already matches**, so an import would be a no-op rather than a repair:
  `glossary_glossaryspecmention` for the archived spec path is `order 0 | DjangoType | djangotype`,
  and `kanban_cardglossaryterm` for card 12 is `order 0 | DjangoType | djangotype`. Those are exactly
  the two lists `_assert_plan_matches_db` compares.

**`import_spec_terms --check` was run, and is green at baseline.** It was first proved read-only by
reading `handle()`: the `--check` branch calls `_assert_plan_matches_db` and **returns before** the
`transaction.atomic()` write block. Result:

```
uv run python examples/fakeshop/manage.py import_spec_terms --check
OK: 49 done cards have glossary links.
```

**The baseline failure the dispatch anticipated did not occur.** The concern was an earlier done card
whose stored mention path still points at a pre-archive `docs/` location; all 49 pass, so no such
card exists at `c2b8622d` and nothing needs distinguishing from this card's state. The plain
`import_spec_terms` was **not** run.

**The rendered status matches the board.** `KANBAN.md`'s `DONE-012-0.0.4` `#### Glossary terms` table
renders `[`DjangoType`](docs/GLOSSARY.md#djangotype) | shipped (`0.0.5`)`; the committed
`docs/GLOSSARY.md:767` reads `**Status:** shipped (`0.0.5`).`; the DB's `status_text` is the same
string. Three surfaces agree. **F11 reproduces in full.**

### 4. F12 — the `spec-012` reference population, re-derived

Measured by counting **occurrences of the token `spec-012`** across every tracked file plus this
cycle's untracked artifacts (not by counting matching lines):

| File | Occ. | Sense |
|---|---|---|
| `docs/builder/bld-012-r1-…md` | 24 | this cycle |
| `docs/builder/build-012-…md` | 22 | this cycle |
| `docs/SPECS/appx/spec-012-…-rationale.md` | 22 | this card |
| `KANBAN.md` | 6 | this card (card 12's `Spec:` row and index row; the residual-stub and unused-def backlog bullets on card 052) |
| `KANBAN.html` | 5 | this card (the same card body inside the data block) |
| `docs/SPECS/spec-012-…md` | 3 | itself |
| `docs/builder/bld-011-final.md` | 2 | this card (`[backlog]` population; boilerplate-preamble population) |
| `docs/SPECS/appx/spec-011-…-rationale.md` | 2 | this card (same two populations) |
| `docs/builder/DONE/build-007-…md` | 1 | this card (a byte-count comparison) |

**Every occurrence means this card.** Zero occur in package source or tests.

**The renumber question the `[spec-011]` cluster raises is settled, not assumed.** `spec-011` is
ambiguous because the number was reused across the 2026-06-01 renumber. `git log --all
--diff-filter=A -- '*spec-012*'` returns exactly **two** paths ever added — this spec and its terms
CSV — and the only rename in the file's history is the CSV's move into `appx/` at `40e4754a`. The
number has never named anything else, so F12's substance is **provable**, not merely unobserved.

**The plan's wording no longer reproduces, and this cycle is the cause.** F12 says "no file defines a
`[spec-012]` ref-id at all". At `c2b8622d` four are defined: `[spec-012-rationale]` in the spec, and
`[spec-012]` / `[spec-012-card-snapshot]` / `[spec-012-scope]` in the companion — **all four written
by R1**, all defined and used within this cycle's own two files, all pointing at this card's spec.
The claim was true when the plan was written and was falsified by R1's own deliverable. The finding's
substance — no ambiguity, nothing to fix, nothing to defer — is unaffected. **Surfaced for Worker 0**;
the plan is Worker 0's file and was not edited.

### 5. The card body — verified independently, and no edit is owed

`KANBAN.md`'s `DONE-012-0.0.4` card was read end to end and judged against `231911a8`'s actual diff
rather than against R1's conclusion.

**The tense question is real and the answer is still "no edit".** The card's `#### Scope` bullet 1 is
the F6 sentence verbatim — "Package metadata, runtime version, lockfile, tests, and changelog now
agree on `0.0.4`" — and read as a standing claim it is false at `c2b8622d`, where the five surfaces
agree on `0.0.14`. Three measurements settle it against editing:

1. **The register is the board's, not this card's.** 23 card bullets across `KANBAN.md` use the same
   present-tense "now" for a completed change. Most remain true because their subject does not move
   (`now use real models`, `now fail with explicit `ConfigurationError``); card 12's is distinctive
   only in that its subject is a value *designed* to move — which is precisely the observation R1
   moved into the **spec**, where a contract is read as standing, and which does not transfer to a
   board row that is read as a work record.
2. **The board states the rule explicitly, about a `0.0.4` card, in its own text.** Card
   `TODO-ALPHA-052-0.1.0` carries: the `0.0.4` onboarding-docs card's board claim "was true when it
   was written and describes neither property now. **That row is correct history on a Done card and
   is NOT to be edited**, which is precisely why the live decision needs a home here." That is the
   same shape as this bullet, decided the same way, on the neighbouring card of the same release.
3. **The card is version-stamped.** Its id, its title, and its `Spec:` row all carry `0.0.4`, so the
   bullet's scope is fixed by its container in a way the spec's `## Scope` was not.

**Contrast with the precedent, which is why this is not inconsistency.** The spec-011 R2 pass *did*
report two card-body defects — but neither was a tense: one was a claim that a test placeholder
*stands* when the placeholder had been retired (0 occurrences tree-wide), and the other was a
literal duplicate row inside `#### Scope`. Card 12 has neither. Its `#### Scope` bullets are two,
distinct, and describe what the cut achieved.

**`#### Files likely touched` is a planning-time prediction and is not falsified.** It names
`pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `uv.lock`,
`CHANGELOG.md`; `git show --stat 231911a8` reports **two** files, `CHANGELOG.md` (31) and `KANBAN.md`
(147). The field's own name says "likely", so the mismatch is the field working as designed, and the
other four surfaces genuinely carry the version string — they were simply aligned a day earlier at
`118f71a1`. This is F7, and F7's remedy was the **spec's** re-framing, which R1 shipped. Adding
`KANBAN.md` to the board's prediction list would be editing history to match an outcome.

**Nothing else in the card body is falsified.** `Labels: `internal`, `release`, `versioning`` is
correct at `c2b8622d` (the spec's stale copy was the defect, and R1 deleted the copy); the two
`#### Note` rows are board triage; the glossary table matches three surfaces (section 3).

**Conclusion: no `KANBAN.md` card-body edit and no kanban-DB edit is owed.** R1's conclusion
reproduces. No DB write of any kind was made; `KANBAN.md`, `KANBAN.html`, and
`examples/fakeshop/db.sqlite3` were read only, the last through a scratchpad copy queried with
`sqlite3 -readonly`.

### 6. F8 confirmed — recorded, still not fixed

`[backlog]: ../../BACKLOG.md` is still defined in the spec's `<!-- Root -->` group and still unused
(1 occurrence in the file, the definition). The rationale still carries the dedicated entry
`### The `[backlog]` link definition — recorded, not fixed` explaining why, and citing the board's
71-definition / 23-file population and `worker-0.md` `## Closing out a kanban card`. Neither was
touched.

**The companion contributes two more to that population** — `[backlog]` and `[kanban]`, both unused,
the same pair the spec-011 companion carries, inherited from the shared rationale template. Left in
place for the identical reason: removing them would make this cycle's file the single exception in a
23-file pattern. Carried to the deferred-work catalog rather than fixed.

### 7. Spec status-line re-verification

`worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`. Spec lines 1-7 re-read at
this spawn: the title, the `Target release: `0.0.4`` line naming card `DONE-012-0.0.4`, `Status:
shipped — canonical spec stub created to keep the Kanban DB one-to-one spec invariant intact.`,
`Owner: package maintainer.`, and the pointer paragraph naming the rationale companion. **All still
describe the build's current state**, and the pointer's target exists and is the file this pass
extended. Nothing falsified; no edit.

### 8. Deferred-work items for `bld-012-final.md`

Assembled so the final gate walks them in one read. The first two are R1's, carried forward verbatim
in substance; the last two are this pass's.

- **V5 — the `pyproject.toml` <-> `__init__.py` pairing has no executable pin.** `AGENTS.md` rule 31
  states it in prose; `tests/base/test_init.py::test_version` asserts a literal and never reads
  `pyproject.toml`. Not a spec-012 defect — the card promised agreement at one release and delivered
  it — and deliberately not written into the spec as an enforcement claim. Source:
  `bld-012-r1-…md` `### Re-derivation of the plan's measurements` (V5).
- **F8 — unused `[backlog]` link definitions.** One in the spec, plus `[backlog]` and `[kanban]` in
  the companion; three of the 71 unused definitions across 23 files the board's checker card owns as
  a single sweep. Left in place. Source: this artifact, `### 6. F8 confirmed`.
- **F9's onward reader problem, recorded not carded.** `CHANGELOG.md`'s `0.0.4` entry — and every
  other pre-`27ed0b30` entry — was written under a policy the file no longer states, and nothing in
  the file marks where the policy changed. The rationale now records it for spec-012; the general
  case (whether `## Versioning` should say from which release the milestone cadence applies) is a
  `CHANGELOG.md` decision, and `AGENTS.md` rule 21 closes that file to a build cycle. Card
  `TODO-ALPHA-052-0.1.0` already owns the CHANGELOG promotion question and is the natural home.
- **F12's wording drift in the plan.** "No file defines a `[spec-012]` ref-id at all" was falsified by
  R1's own companion; four are now defined, all unambiguous. Recorded so the final gate does not
  re-copy the plan's sentence. Source: this artifact, `### 4. F12`.

### Verification commands run

- per-definition `[ -e ]` disk check after `cd` into each file's own directory, plus `realpath`
  normalization -> **21/21 resolve** (9 spec + 12 companion, pre-`[changelog]`; 22/22 after)
- basename-duplication probe over the tree for all ten distinct link targets -> masking pairs
  identified and each shown unable to fire
- Python re-derivation of the scaffold and of unused/undefined definitions, **code spans stripped**
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-012-…md` -> `OK: 1 terms`,
  exit 0 (run again after the F9 edit)
- `uv run python scripts/check_trailing_commas.py --check <spec> <companion>` -> exit 0 (likewise)
- `git show 231911a8:CHANGELOG.md`, `git show 27ed0b30 -- CHANGELOG.md`, `git log -S` on the
  `## Versioning` row labels and on `## [Unreleased]`
- `awk` extraction + `wc -c` + `diff` of the `## [0.0.4]`-to-`## [0.0.3]` block, old vs. new ->
  2,621 bytes each, identical
- `git show --stat 231911a8`; `git log --all --diff-filter=A|R -- '*spec-012*'`
- `sqlite3 -readonly` against a **scratchpad copy** of `examples/fakeshop/db.sqlite3`
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> `OK: 49 done cards`,
  after proving from `handle()` that `--check` returns before the write block
- token-occurrence sweep for `spec-012` over `git ls-files` + untracked cycle artifacts
- `grep -rn 'TODO(spec-012' .` -> **0**
- **No `pytest` run**, no `--cov*` flag, no `scripts/build_glossary_md.py`, no
  `scripts/build_kanban_md.py`, no DB write.

### Working-tree discipline

This pass wrote exactly two tracked-visible paths — the companion
(`docs/SPECS/appx/spec-012-version_release_alignment-0_0_4-rationale.md`, still `??`, created by R1)
and this artifact — plus the gitignored memory file. The spec was **not** opened for writing.

`git status --porcelain | wc -l` reads **104** at this pass, against R1's 102 and the plan's 93 — the
moving baseline the plan warns about, and the reason no pass quotes a number forward. **Not one
baseline-dirty path was edited, reverted, staged, `git checkout`-ed, or stashed.** `docs/GLOSSARY.md`
was read only, and only through `git show HEAD:` for the load-bearing check;
`scripts/build_glossary_md.py` was not run. `docs/SPECS/spec-009-*` and its companion were not
opened. `docs/review/**` was not touched (`AGENTS.md` rule 22). The build plan was not edited — both
corrections are surfaced below for Worker 0. R1's closed artifact was read only. All history reads
went through `git show <rev>:<path>` into the session scratchpad, outside the repository.

The plan's note that `docs/builder/bld-011-r*.md` are staged deletions is now historical: `c2b8622d`
landed them. The precedent artifact was read at `2b7e5b16`.

### Summary

The archive is clean and the audit found no defect in either file. All 21 link definitions resolved
from their own directories at two different depths; the masked-rot trap was probed on names rather
than paths and shown unable to fire in this cluster (the one masking pair in the repository,
`README.md` at two depths, is linked by neither file; the four-way `worker-*.md` duplication differs
by parent directory, not depth); no anchor is version-dotted, so the `007`-slug trap has no purchase;
both checkers exit 0; and the terms CSV is importable against the constraints read out of
`import_spec_terms` itself, with the DB already matching row for row and `--check` green across all
**49** done cards — the baseline failure the dispatch warned about did not occur.

F9 is written into the rationale as a `## Scope`-keyed entry with four rejected alternatives. Its
sharpest measured point is one the plan did not state: the policy rewrite at `27ed0b30` sits entirely
**above** the release entries, so the `0.0.4` block stays byte-identical (2,621 bytes, `diff` clean,
re-verified at the new `HEAD`) and the spec's "no later commit rewrites it" guarantee is true **and
blind to F9** — which is the argument for the entry existing. The `## Versioning` section has itself
been revised at least three times since, so the entry records that the frame moved rather than
quoting any one version of it into a file nothing re-renders.

**No `KANBAN.md` card-body edit and no kanban-DB edit is owed**, verified independently of R1: the
card's present-tense `#### Scope` bullet is the board's normal register for a Done card (23 such
bullets), the board states in its own text that such a row is "correct history on a Done card and is
NOT to be edited", and the card is version-stamped in its id, title, and `Spec:` row. That is a
different shape from the spec-011 card defects, which were a retired-placeholder claim and a literal
duplicate row. `#### Files likely touched` is a planning-time prediction, not falsified by
`231911a8`'s two-file diff.

F12's substance holds and is now provable rather than merely unobserved — the number `spec-012` has
never named any other file — but the plan's wording was falsified by R1's own companion, and that is
recorded for Worker 0 rather than left to propagate.

### Spec changes made (Worker 1 only)

**None.** The spec was not opened for writing. The audit found no broken link, no scaffold violation,
no stale status line, and no claim in it that does not hold, so `worker-1.md` `## Spec custody`'s
threshold ("only when the build proves it incomplete, internally inconsistent, or inaccurate") was
not met. R1's reconciliation was not re-litigated.

Two changes were made to the rationale companion, which this item owns:

| Companion line(s) | Change | Reason | Trigger |
|---|---|---|---|
| after `### `## Scope` 2` (new entry, ~65 lines) | **Added** the keyed entry `### `## Scope` — the release policy `0.0.4` was cut under was rewritten a week later`, with the blob-derived history, the current measured shape, the byte-identity interaction, four rejected alternatives, and the claim the spec may not make. | The policy frame around the spec's whole subject moved seven days after the cut; `BUILD.md` `## Spec rationale extraction` puts the change record here and keeps the spec stating only what holds. | F9 |
| `## How to read this file`, the `**The substance is therefore the change record.**` bullet | **Amended** "a single structural fault" to name both findings. | The roadmap became stale the moment F9 landed, and a stale map in the file this item owns is a defect. One bullet; no entry edited (append-only rule preserved). | F9 |
| link block, `<!-- Root -->` | Gained `[changelog]: ../../../CHANGELOG.md`, inserted alphabetically between `[backlog]` and `[kanban]`. | The F9 entry cites `CHANGELOG.md` as a cross-file link. | F9 |

The companion went 364 lines / 23,818 bytes -> **434 lines / 28,943 bytes**.

### Notes for Worker 0

- **`HEAD` moved to `c2b8622d`** before this pass began, and that commit landed the
  `docs/builder/bld-011-r*.md` deletions the plan recorded as staged. The plan's baseline section is
  correct as written ("the list is moving"); no edit is proposed, only the note.
- **F12's wording is falsified by R1's own deliverable**: "no file defines a `[spec-012]` ref-id at
  all" is no longer true — four are defined, all by R1, all unambiguous. The finding's substance is
  unaffected. The plan is Worker 0's file and was not edited.
- **F9 was under-stated in the plan** in one respect worth recording: the plan frames it as a policy
  change adjacent to the spec's subject. The measured relationship is sharper — the change is
  invisible to the byte-identity guarantee the spec now makes, because it lives above the entries.
  Also, the `## Versioning` section has been revised at least three times since `27ed0b30`, which is
  itself the argument against quoting it.
- **No re-partition is needed.** R2's dispatch-row escape hatch did not fire: no durable-doc and no
  DB edit is owed, so no Worker 2 pass is required and the cycle proceeds to the final gate.

### Final status

`final-accepted`. R2 is complete: the archive audit passed on every check with no defect found, the
terms CSV is importable and the DB already agrees, F9 is recorded in the rationale where `BUILD.md`
puts it, the card body was judged independently and needs no edit, and both plan figures that did not
reproduce are surfaced for Worker 0 rather than silently corrected.

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
