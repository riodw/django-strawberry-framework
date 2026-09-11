# Build: cross-slice integration pass — `040` retrospective reconciliation cycle

Spec reference: `docs/SPECS/spec-040-auth_mutations-0_0_13.md` (whole document, read
end to end as one document — the pass's central instrument) plus its companion
`docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`
Status: final-accepted

Worker-1-only pass under [`BUILD.md`][build-md] `## Cross-slice integration pass`.
It edits the spec and its companion (custodian work, done here) and **dispatches one
consolidation loop** for two intra-file `.py` duplications it may not implement
itself, which is why the status is `revision-needed` rather than `final-accepted`:
the pass's own rule is "record them, ask Worker 0 to dispatch Worker 2 and Worker 3,
then re-run the integration pass."

Line numbers in this artifact are pin-at-write-time navigational hints (per-cycle
scratchpad; raw `path:NN` is permitted here and nowhere else).

---

## Required reading, and the glob hazard that had to be worked around

[`BUILD.md`][build-md] `## Cross-slice integration pass` step 1 names
`docs/builder/bld-slice-*.md`. That glob matches the **concurrently active
`spec-050` cycle's** five artifacts and **none** of this cycle's, which are
`bld-040-slice-<N>-*.md`. A literal reading would have produced a confident, clean
sweep of the wrong build. The six artifacts below were read in slice order, by name,
from the build plan's `## Artifact list`:

1. `docs/builder/bld-040-slice-1-rationale_extraction.md`
2. `docs/builder/bld-040-slice-2-audit_substrate_login_logout.md`
3. `docs/builder/bld-040-slice-3-audit_register_current_user.md`
4. `docs/builder/bld-040-slice-4-audit_obligations_edges_tests.md`
5. `docs/builder/bld-040-slice-5-later_spec_reconciliation.md`
6. `docs/builder/bld-040-slice-6-code_remediation.md`

Also read: [`AGENTS.md`][agents], [`START.md`][start], [`BUILD.md`][build-md],
[`ARTIFACT.md`][artifact-md], [`worker-1.md`][worker-1], the build plan
[`build-040-auth_mutations-0_0_13.md`][build-040] including its `## Slice log
(Worker 0)`, the spec and its rationale companion end to end, and both of this
role's memory files (`worker-1-040.md`, `worker-1-040-codefix.md`). No other
worker's memory file was opened.

---

## The divergence inventory (the pass's central deliverable)

Five slices edited one spec and one companion, sequentially and then in two
concurrent cohorts, each grading a different section. The failure mode that produces
is a document whose homes disagree, and this cycle had already produced two instances
before this pass (Decisions 5 / 7 on a shared classification, caught by Slice 5; the
retired `D-N3` reason clause alive in Decision 6's body, caught by Slice 6's second
closing pass). [`BUILD.md`][build-md] `### Five homes per contract` names the
instrument no single slice runs. This is that run.

**Method.** Enumerate every contract stated in more than one home; read the homes
against each other rather than each against the code; and separately grade the
**absence** of a member from an enumeration, since a `rg` sweep finds a false sentence
and only a home-by-home walk finds a missing one. Then sweep the spec against every
`**No longer claims:**` bullet the companion records — a retraction is a mechanical
statement of what the spec may no longer say, so it is the cheapest instrument in the
pass and the one that found the headline defect.

### Contracts that live in more than one home

| # | Contract | Homes | Verdict |
|---|---|---|---|
| C1 | Account-control columns are kept off the register input | `## Goals` 4 · `### Decision 6` · `### Decision 8` · `## Edge cases` · `## Test plan` · `## Definition of done` 4 | **DISAGREE — 3 of 6 stated the retired absolute claim.** Fixed (edits 1-3) |
| C2 | `SyncMisuseError` is never defined or re-spelled in `auth/` | `### Decision 10` · `## Helper-reuse obligations` `D18 / D19` | **DISAGREE — the two homes asserted opposite things.** Fixed (edit 4) |
| C3 | Which transports each surface accepts, and how each refusal is stated | `### Decision 11` (the 5x3 table) · `### Error shapes` · `## Edge cases` ×3 · `## Out of scope` · `## Non-goals` · `## Borrowing posture` · Decisions 2 / 4 / 5 / 7 (pointers) | **ONE MEMBER MISSING from `### Error shapes`.** Fixed (edit 6); every pointer re-verified to resolve to something true |
| C4 | The card's own id | opening line (`DONE-040-0.0.13`) · `### Decision 1` (`WIP-ALPHA-040-0.0.13`) | **DISAGREE — one document, one card, two ids.** Fixed (edit 5) |
| C5 | What the glossary / `docs/TREE.md` carry today | header line 103 · `## Key glossary references` ×2 · "Project conventions to follow" | **DISAGREE — the header stated the shipped fact, three orientation bullets still promised it as future work.** Fixed (edits 7-9) |
| C6 | The phase-2.5 bind order | `## Current state` · `### Decision 8` · `### Decision 9` · `## Slice checklist` · `## Definition of done` 2 · `## Implementation plan` | AGREE — all six spell `pre-bind reset -> bind_auth_mutations() -> bind_mutations() -> bind_form_mutations()` |
| C7 | The AllowAny default, and that no `AllowAny` class exists | `## Key glossary references` · `## Goals` 3 · `### Decision 5` · `### Decision 6` · `### Decision 7` · `## Definition of done` 2 | AGREE |
| C8 | `login.node` / `me` are raw, unplanned instances and strictness-visible | `## User-facing API` · `### Decision 5` · `### Decision 7` · `### Decision 8` · `## Edge cases` · `## Test plan` · `## Out of scope` | AGREE across all seven |
| C9 | `logout`'s `ok` derives from the ONE shared anonymity definition | `## User-facing API` · `### Decision 5` step 5 · `### Decision 7` · `## Edge cases` | AGREE (Slice 5's cross-slice correction to Decision 5 closed the last gap) |
| C10 | The conflict / cache key is the normalized `permission_classes` alone | `### Decision 6` · `## Edge cases` ×2 · `## Test plan` · `## Definition of done` 2 | AGREE |
| C11 | The declaration ledger is full-clear-only; the emit ledgers are pre-bind | `## Current state` · `### Decision 9` · `## Helper-reuse obligations` `D15` · `## Edge cases` · `## Test plan` · `## Definition of done` 2 | AGREE |
| C12 | `register`'s password error keys to `password`, never via the generic mapper | `### Decision 6` · `## Helper-reuse obligations` `D8` / `D-N2` · `## Edge cases` · `## Test plan` · `### Error shapes` | AGREE |

Twelve contracts with two or more homes; **five disagreed**, and all five are
repaired below. The seven that agree are listed rather than omitted, because a
cross-check that reports only its hits is indistinguishable from one that ran on
nothing.

### The five divergences, stated

#### D1 — the retired privilege claim was live at three homes (C1)

The companion records, under Decision 6:

> **No longer claims:** that privilege escalation is unreachable by structure alone
> and needs no policy check

Slice 3 retired it from Decision 6 and Slice 6 found it still standing in Decision
6's own body. It was **also** standing at three further homes, none of which any
slice's scope covered:

- **`## Goals` item 4** — "privilege-bearing columns (`is_staff`, `is_superuser`,
  `groups`, `user_permissions`) are structurally unreachable". Two defects in one
  sentence: the retracted absolute claim, **and** an enumeration short by a member —
  `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS` holds
  **five** names, and `is_active` is the missing one. That is the identical omission
  Slice 3 recorded against `docs/GLOSSARY.md` as finding **F1**, sitting in the spec
  itself and unnoticed.
- **`### Decision 8`** — "The register input side is safe by construction (privilege
  columns structurally unreachable, Decision 6)". A pointer that restates the retired
  reason of the thing it points at.
- **`## Definition of done` item 4** — "privilege columns structurally absent". Slice
  4 graded this row `DoD.4b` as `CONFORMS`, with the note that "the sentence states
  only its structural half, already corrected at its Decision home". That grading is
  what let it survive: a Definition-of-done item is a **completion claim**, so a
  half-true one is a false completion claim in exactly the way Slice 4's own item-7
  tense finding was.

**Instrument note, because it nearly hid this.** `rg -n 'structurally unreachable'`
over the spec returns **2** hits — Decision 6 and Decision 8. `## Goals` item 4 was
invisible to it because the phrase **wraps across two source lines**
(`… are structurally` / `unreachable; the password …`). The population is only
recoverable by normalizing whitespace across the whole file first
(`re.sub(r"\s+", " ", text).count(...)` → **3**). This is `START.md`'s "citation
wrapped across two lines invisible" hazard applied to a claim rather than a citation,
and a per-line grep here reports two thirds of a population as the whole of it.

#### D2 — Decision 10 and the `D18 / D19` obligation asserted opposite things (C2)

- **`## Helper-reuse obligations (DRY)` `D18 / D19`** (Slice 4's restatement): "It
  never defines or re-defines `SyncMisuseError`; the guards that raise it are reused
  by call, so `auth/` **neither imports nor re-spells it**. Both hold **vacuously
  today**."
- **`### Decision 10`** (untouched by any slice): "`SyncMisuseError` **is imported
  from its public path** (`django_strawberry_framework` / `.types`), never redefined
  in `auth/` (the D19 reuse directive)."

One contract, two homes, contradictory. Settled against source rather than by
preference: `rg -n 'SyncMisuseError' django_strawberry_framework/auth/` returns **2
hits, both docstring mentions**; `rg -c 'import.*SyncMisuseError'
django_strawberry_framework/auth/` returns **0**. The obligations home is right and
the Decision is false — which is why Slice 4 restated `D19` as a prohibition in the
first place ("asserting an import that does not exist, inviting a later audit to
record a violation where there is none"). Slice 4 fixed the obligation and never
swept for the Decision that the obligation cross-references. This is the `D-N3`
shape exactly, one Decision over.

Neither sentence is wrong on its own page; each is wrong only against the other.

#### D3 — `### Error shapes` carried two of the three transport refusals (C3)

Slice 5 added the two WebSocket refusal rows (its row `S.5`, an omission it found by
grading the absence). The table now maps every documented failure to where it lands
**except** the third refusal Decision 11's own support matrix enumerates: `login` /
`logout` with no session on the path. That is the one a misconfigured deployment
actually hits, it has a home in `## Edge cases` and in Decision 11's table, and the
table that exists to be the single map omitted it. Added.

#### D4 — the spec named its own card by two different ids (C4)

Line 3 opens `Shipped in 0.0.13 (card DONE-040-0.0.13)`; `### Decision 1` derived
`NNN` `from WIP-ALPHA-040-0.0.13`. Both carry the same `kanban` label, so both land in
`KANBAN.md`, where only `DONE-040-0.0.13` exists. This is the clean prefix-flip class
(c) the `KANBAN.md` catalogue of this defect defines and that Slice 4 applied to the
`041` / `043` citations in `## Out of scope`; the derivation itself is unchanged,
because the card's **number** is what is stable and its prefix is what rots.

The other four `WIP-ALPHA-040-0.0.13` occurrences are **decided non-edits**, recorded
under `### Decided non-edits` below.

#### D5 — three orientation bullets still described the pre-cut tree (C5)

Slice 2's edit 1 corrected the spec's header line because "the present-tense claim was
false on its own date": the GLOSSARY now reads `shipped (0.0.13)`. Three parallel
sites in `## Key glossary references` / "Project conventions to follow" were not swept
and still promised the same work as future:

- the `Auth mutations` bullet — "Slice 3 flips the entry to `shipped (0.0.13)`",
  directly against the header nine lines above it;
- the `SerializerMutation` bullet — "Slice 3 flips its GLOSSARY status";
- the `docs/TREE.md` bullet — "the target layout does **not** yet reserve
  `django_strawberry_framework/auth/` for this card … Slice 3 fixes".

All three were verified landed by Slice 3's read-only audit at `3a294082`. Unlike
`## Current state`, which opens "A true description of the repo as this spec is
authored" and is therefore a dated observation that stands
([`BUILD.md`][build-md] ``### `## Current state`: observations stand, predictions do
not``), this section carries no vintage header, so a present-tense claim in it is read
as current. `START.md`'s "partial claim fix = dominant residual defect", one more time.

### The spec never narrates its own history — one residue found

`## Spec rationale extraction` requires the spec to read as a clean current contract.
Sweep of the whole document for chronology vocabulary: `Revision` **0**, `as of` **0**,
`previously` **0**, `amendment` **0**, `retract` **0**, `Build note` **0**, `review
round` **0**, `Worker <n>` **0** — Slice 1's cut holds.

**One survivor, in a vocabulary that sweep could not see.** `### Decision 8`:
"Were the auth bind ordered after it **(as an earlier draft had it)**, the generic
error would always pre-empt …". A chronology attribution of exactly the class Slice 1
deleted 38 of, spelled without the `Revision-N` token its sweep keyed on — the
positive-vocabulary-census hazard. The counterfactual reasoning it introduces is
implementation-relevant and stays; the four-word attribution is deleted.

### Spec ↔ companion agreement

- **Every companion entry names a Decision that still exists under that heading and
  anchor.** Checked mechanically, not by eye: the 12 `### Decision N — …` headings in
  the spec and the 12 `## Decision N — …` headings in the companion were extracted and
  compared as strings — **12 / 12 identical, 0 mismatches**. This matters because
  Slice 5 renamed two headings (Decisions 2 and 11) and a mirrored heading is the one
  thing a renamer forgets.
- **No spec sentence contradicts a retraction the companion records.** All **12**
  `**No longer claims:**` bullets were extracted and each swept against the spec. One
  produced hits (D1 above, three sites); the other eleven produced none. The sweeps
  that returned zero: `excluded_input_fields` (0), `_bind_mutation` (0),
  `three-module` (0), `Channels-agnostic` (0), `AllowAny class` (0 as an existence
  claim), "only auth-specific" as the two-step enumeration (0), "actor it returns is
  always `request.user`" (0), the `mutations/` home for the boundary primitive (0),
  `before_bind=True` on the declaration ledger (0).
- **No spec sentence contradicts the shipped code as Slice 6 left it.** The comment
  text changed twice during that slice; both changed texts were read against the spec
  in this pass. The `D-N3` comment's scope clause and bridging clause match
  `## Helper-reuse obligations` `D-N3` and the **Custom user models** edge case;
  `grep -rn 'no relation input' django_strawberry_framework/` returns **1** hit and it
  is the scoped one. The `TG-1` docstring's corrected claim matches the `## Test plan`
  row's "**finalizes** (or builds a schema)" parenthetical, which makes no
  independence claim. No spec edit is owed by either.

---

## Spec changes made (Worker 1 only)

All in `docs/SPECS/spec-040-auth_mutations-0_0_13.md` unless stated; every "why" is
appended to `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md` under the
owning Decision's `### Changes this Decision underwent` or under
`## Spec sections outside the Decisions — changes they underwent`. Changes are cited
by content, not by pre-edit line number.

| # | Site | Change | Divergence |
|---|---|---|---|
| 1 | `## Goals` item 4 | The absolute "structurally unreachable" claim replaced by Decision 6's two layers, and the protected set corrected from four names to five (`is_active` added) | D1 |
| 2 | `### Decision 8`, the read-surface caution's lead-in | "safe by construction (privilege columns structurally unreachable, Decision 6)" → "guarded on the way in (account-control columns kept off the generated input by Decision 6's two layers)" | D1 |
| 3 | `## Definition of done` item 4 | "privilege columns structurally absent" → "account-control columns kept off the generated input by Decision 6's two layers" | D1 |
| 4 | `### Decision 10`, the closing clause | The false "`SyncMisuseError` **is imported** from its public path" replaced by the prohibition in the obligations list's own words (never defined, never re-spelled, neither imported nor re-spelled because the guards are reused by call, vacuous today); the adjacent `D18` clause re-tagged "prohibition" so both homes share one vocabulary | D2 |
| 5 | `### Decision 1` | `WIP-ALPHA-040-0.0.13` → `DONE-040-0.0.13` | D4 |
| 6 | `### Error shapes` | New row: `login` / `logout` with no session middleware on the path → the prologue's pre-check `ConfigurationError`, with `register` / `me` named as unaffected | D3 |
| 7 | `## Key glossary references`, the `Auth mutations` bullet | "Slice 3 flips the entry to `shipped (0.0.13)`" → the glossary carries it as shipped | D5 |
| 8 | `## Key glossary references`, the `SerializerMutation` bullet | "Slice 3 flips its GLOSSARY status" → its status reads `shipped (0.0.13)`, flipped by this card's Slice 3 | D5 |
| 9 | "Project conventions to follow", the `docs/TREE.md` bullet | The "does not yet reserve `auth/`" claim → the layout carries the `auth/` rows, with the original gap kept as the reason the `Risks` pointer exists | D5 |
| 10 | `### Decision 8`, the bind-ordering paragraph | "(as an earlier draft had it)" deleted; the counterfactual reasoning kept | self-history |

**No link definition was added to or removed from the spec**, and no `-terms.csv` row
was falsified by any of the ten edits — `check_spec_glossary.py` re-run after them
reports the same `OK: 30 terms`, with every term keeping at least one surviving link.
The CSV is therefore untouched, as the writable-list condition requires.

**Companion additions** (append-only, nothing rewritten or deleted): post-ship bullets
plus a `**No longer claims:**` bullet under Decisions 1, 8 and 10; one **new**
`### [`## Goals`]` sub-section under `## Spec sections outside the Decisions`, keyed by
spec heading and anchor like its siblings; appended bullets under the existing
`### [`## Key glossary references`]`, `### [`### Error shapes`]` and
`### [`## Definition of done`]` sub-sections — the last of which also marks Slice 4's
`D-N3` code-gap observation **discharged** by Slice 6, so a reader does not take a
dated observation for a live one. The section's lead-in now names this pass alongside
Slices 4 and 5, and one link definition (`[bld-040-integration]`) was added under
`<!-- docs/builder/ -->`, alphabetical within its group.

### Repair to another slice's artifact (the one authorized exception)

`docs/builder/bld-040-slice-1-rationale_extraction.md`'s `[spec-040-d11]` definition
pointed at the **retired** Decision 11 anchor
(`#decision-11--session-transport-constraints-…-the-channels-fallback-is-not-borrowed`),
which Slice 5's rename stranded. Re-pointed to the live anchor
(`#decision-11--transport-contract-classify-first-refuse-a-transport-that-cannot-honour-the-surface-truthfully`).

**The surrounding prose was deliberately not touched.** It records what Slice 1 read
at the time ("Decision 11 states the Channels fallback is **not** borrowed") and is
the dated record of a finding Slice 5 then discharged; retargeting the pointer is the
`START.md` "retarget standing pointer" half of the remedy, and rewriting the
observation would destroy the record the artifact exists to be. A reader who follows
the link now lands on a Decision that visibly says the opposite, which is the correct
outcome for a finding that was closed.

---

## Cross-slice checks

### 1. Static inspection helper — ran or explicitly skipped, per file

Slice 6 is the only slice that touched `.py`. Six files:

| File | Disposition | Graded |
|---|---|---|
| `tests/auth/test_mutations.py` | **RAN** (`docs/shadow/tests__auth__test_mutations.overview.md`, present on disk) | Required: `+247 / -42`, over the 50-lines-outside-the-package trigger |
| `tests/auth/test_queries.py` | **RAN** (`docs/shadow/tests__auth__test_queries.overview.md`) | Required: `+86 / -7`, same trigger |
| `django_strawberry_framework/auth/mutations.py` | **SKIPPED**, reason recorded | **Accepted** |
| `django_strawberry_framework/mutations/sets.py` | **SKIPPED**, reason recorded | **Accepted** |
| `django_strawberry_framework/mutations/resolvers.py` | **SKIPPED**, reason recorded | **Accepted** |
| `examples/fakeshop/test_query/test_auth_api.py` | **SKIPPED**, reason recorded | **Accepted** |

**Grading the skip.** The recorded reason is "their entire contribution is comment and
docstring text, proved AST-identical, so there is no review-worthy logic for an AST
overview to report." That is **stronger than the rule requires** and is the right
shape: [`BUILD.md`][build-md] `### When to run the helper during build` licenses a
skip for a file whose disposition is "no review-worthy logic" with a short reason,
and this one does not assert the disposition — it proves it, by AST identity with
docstrings stripped against `git show HEAD:<path>`, with a positive control
(`X_CONTROL = 1` prints `DIFFERENT`, exit 1) confirming the instrument can fail. An
AST overview of a file whose executable tokens are unchanged would reproduce the
prior one byte for byte.

Two further checks the skip depends on, both confirmed by me: no touched file sits
under `optimizer/` or `types/` in the permanent diff (the two `types/` files carried
transient proof mutations only and are byte-clean — `git diff --stat --
django_strawberry_framework/types/` is empty), and the production diff adds **zero**
lines of logic, so the 30-lines-in-package trigger cannot fire either. **The skip is
accepted on all four files.**

Worker 1's planning-side obligation was also met: the package-wide helper inventory
was refreshed to `docs/shadow/helper-inventory-040-slice-6.md` (2,070 lines over every
`django_strawberry_framework/**/*.py`), present on disk.

### 2. Repeated string literals across shadow overviews

A thin section, and it is thin for a real reason rather than an unrun one: Slice 6
added no production logic at all, so there is no package-side literal to compare. The
comparison is over the two test overviews plus the pre-flight
`django_strawberry_framework__auth__queries.overview.md`.

**Literals appearing in two or more overviews:**

| Literal | Counts | Disposition |
|---|---|---|
| `pw-9x-strong` | 14x (`test_mutations`) / 9x (`test_queries`) | **Considered and declined.** Pre-existing at HEAD (12 / 8) — this build added 2 and 1. Its only cross-file home is `tests/auth/_helpers.py`, which this pass rules not to open (below), so hoisting it would mean opening that file for a test password literal. Recorded rather than silently omitted |
| `/graphql/`, `username`, `password` | 9x/14x, 31x/12x, 21x/- | Not candidates: GraphQL field names and a request path, which a constant would obscure rather than centralize |

**Literals repeated *within* one file, which is where the signal actually landed:**

- `SessionMiddleware` **2x** and `AuthMiddlewareStack` **2x** in
  `tests/auth/test_mutations.py` — the duplicated sessionless assertion block. **In
  the consolidation loop below.**
- `mutation{ logout{ ok errors{ field } } }` **2x** in the same file —
  `_LOGOUT_Q` and `_CH_LOGOUT`, byte-identical. **In the loop below.**

The `## Repeated string literals` section earned its keep here: it independently
surfaced both items Worker 3 raised from reading, which is the corroboration
[`BUILD.md`][build-md] calls it "essential at the cross-slice integration pass" for.

### 3. Imports — one-way dependency direction

Compared across the overviews' `## Imports` sections and then verified against source,
because this direction is a **shipped contract** (Decision 3's structural opt-in),
not a stylistic preference:

- **Nothing under `django_strawberry_framework/` outside `auth/` imports `auth`.**
  `rg -n 'from \.\.?auth|from django_strawberry_framework\.auth|import auth\b'`
  filtered to non-`auth/` files returns exactly **one** hit, and it is a **docstring
  line** in `utils/sessions.py` explaining why `from .auth.sessions import
  session_store_class` was *not* done. Zero executable hits.
- **`auth/` imports only downward.** `auth/mutations.py` → `..exceptions`,
  `..mutations.{fields,inputs,sets}`, `..registry`, `..utils.{directives,permissions,querysets,sessions}`,
  `. sessions`. `auth/queries.py` → `..mutations.fields`, `..registry`,
  `..utils.{inputs,permissions}`, `.mutations`, `..mutations.resolvers`. No
  root-into-subpackage import, no sibling reaching outside the documented boundary.
- **Test side:** both test modules import the package and `tests.auth._helpers`; no
  package module imports a test module. One-way.

The direction holds, and `TG-1` now pins it — before this cycle, swapping the
finalizer's `loaded_attr` reach for a plain import broke **zero** rows.

### 4. The rest of the pass's check list

- **Duplicated helpers across slices:** none possible and none found. Slices 1-5 are
  Worker-1-only prose passes over two Markdown files; Slice 6 is the cycle's only
  source-bearing slice, so there is no prior accepted slice carrying a helper this one
  could duplicate. Confirmed rather than assumed — the five closed artifacts record
  zero `.py` edits between them.
- **Inconsistent naming or error handling between slices:** none. Within the one
  source slice the new names are parallel by construction
  (`test_sessionless_{login,logout}_raises_the_configuration_error_naming_both_middlewares`;
  `test_an_unplanned_relation_under_{me,login_node}_is_strictness_visible`), the
  `optimizer=` seam is spelled identically in both files, and the two
  `_declare_group_type` copies are byte-identical.
- **Repeated ORM / queryset patterns:** none introduced; the slice adds no ORM.
- **Misplaced responsibilities between modules:** none. The three production files
  received docstring or comment text only; no body moved, proved by AST identity.
- **Missing or too-broad exports:** `git diff -- django_strawberry_framework/__init__.py`
  is **empty** — no change to `__all__` or the re-export list, which is what Decision 3
  requires.
- **Do the comments tell one coherent story across the new code?** Read end to end as
  one diff, and yes. All five stranded `Revision N` attributions are gone — three
  deleted where the surrounding clause already carried the reason, two retargeted to
  the Decision that owns the claim (`Revision 5` → Decision 6, which owns `D-N2`'s
  direct `field_error("password", …)` keying; `Revision 4` → Decision 8, which the
  production code already cites for that same half). Both removed symbols are restated
  by their live names, and I re-derived the sharpest of the five substitutions at
  source rather than accepting it: `mutations/sets.py::bind_write_declarations` (line
  1670) is indeed what calls `mutation_cls.build_input(meta, object_type)` (line 1711),
  so `build_input`'s docstring now names its real caller. `D-N3`'s comment carries the
  scope clause and the bridging clause. **Process-provenance sweep over all six files:
  0 hits** for worker / slice / round / `Revision N` / `TG-`/`CG-` / `bld-` / "as of
  0.0." — with the instrument controlled, since the same sweep repo-wide returns 10
  hits in the two populations this cycle declared out of scope.

---

## Staged-anchor sweep (step 6)

```shell
$ rg -n 'TODO\(spec-040' . --glob '!KANBAN.md' --glob '!KANBAN.html' --glob '!BACKLOG.md'
docs/builder/bld-040-slice-4-audit_obligations_edges_tests.md:357   (prose: the row quoting the rule)
docs/SPECS/spec-040-auth_mutations-0_0_13.md:1881                   (prose: the rule itself, in `## Implementation plan`)
docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md:1180    (prose: a bullet recording an anchor's discharge)
-> 3 hits

$ rg -n 'TODO-(ALPHA|BETA|STABLE)-040' . --glob '!KANBAN.md' --glob '!KANBAN.html' --glob '!BACKLOG.md'
docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md:1371    (prose)
docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md:307     (prose, another spec's companion)
-> 2 hits
```

**Population size: 5. All five are Markdown prose *about* the anchor discipline or
recording an anchor's discharge; zero are staged anchors in source, tests, or code
comments.** Nothing is owed and nothing routes back to a slice.

**The instrument ran** — which is the half that makes the count evidence. Controls, on
the same invocation shape: `rg -n 'TODO\(spec-' …` (no number) returns **152** hits and
`rg -n 'TODO-(ALPHA|BETA|STABLE)-' …` returns **471**, so the patterns match this
corpus and the narrow results are measurements rather than a sweep that ran on nothing
or a zsh glob that aborted (`START.md` `## Instruments that lie`). Every glob is
quoted.

---

## DRY: the deferred-follow-up walk, and the rulings

[`BUILD.md`][build-md] step 5 walks every accepted artifact's `What looks solid`,
`DRY findings` and `Notes for Worker 1` sections. The inherited list, enumerated at
the top of Slice 6's artifact and in its closing `### What the integration pass
inherits from this slice`, is discharged item by item below — enumerate-and-tick over
the source's own numbering, per `START.md`'s harvesting rule.

### Ruling 1 — `tests/auth/_helpers.py` is NOT opened

Three of the inherited items hinge on this, and both Slice 6's Worker 1 and Worker 3
recorded the condition explicitly rather than guessing it, which is why it can be
decided cleanly now. **Decided: do not open it.** The reasoning, stated so it is not
re-fought:

1. **The duplication it would remove is deliberate and self-documenting.** Both
   `_declare_group_type` copies carry the same docstring stating why they are not
   shared: "Declared beside `_declare_user_type` rather than shared with
   `tests/auth/test_{mutations,queries}.py`: the two modules already carry their own
   `_declare_user_type` copies so each file's registrations stay readable inside the
   per-test cleared registry." Hoisting `_declare_group_type` **alone** is strictly
   worse than either consistent choice — a file would then declare its user type
   locally and its group type remotely — and hoisting the `_declare_user_type` pair
   with it is a larger refactor of pre-existing code that each copy's `fields=`
   docstring specializes per file.
2. **`_helpers.py`'s existing contract is narrower than "shared auth-test code".** Its
   own docstring scopes it to "plain (non-fixture) helpers": `_drain_until`, an event
   loop barrier, and `_session_request`, a request builder. Both are pure callables
   with no global side effect. `_declare_*` helpers **mutate the process-global type
   registry** and are read back through each module's own autouse `_isolate_registry`
   fixture. Moving registry-mutating declarations into a module whose stated job is
   plain callables widens that contract for a ten-line saving.
3. **The repo has a recorded precedent for the per-file copy**, cited by the Slice 6
   plan before the code was written: `tests/test_permissions.py` #"Re-declared locally,
   matching its sibling hooks above rather than sharing one".
4. **It is outside the cycle's scope fence and buys nothing the cycle was
   commissioned for.** The maintainer's fence is spec files and `.py` files *when the
   audit proves a code gap*. `_helpers.py` was in no cohort's writable list, the one
   code gap is closed, and opening it would start a Worker 2 + Worker 3 loop over a
   file with four readers (including `tests/utils/test_sessions.py`, outside
   `tests/auth/` entirely) for a stylistic consolidation with no behavioural value, in
   a tree a concurrent session is writing.

**Consequence, per the condition Slice 6 and Worker 3 both recorded:** the cross-file
`_declare_group_type` / `_declare_user_type` pairs stand as accepted duplication —
the plan named them in advance with a reason that is still true and was verified true
at source by this pass — and the **two intra-file items collapse to file-local
helpers**, which cohort B owns outright. That is the loop dispatched below.

### Ruling 2 — one consolidation loop, over one file

Dispatched to Worker 0 for Worker 2 + Worker 3, all inside
`tests/auth/test_mutations.py`, which is already on cohort B's writable list. Each
candidate's readers were grepped first, per [`worker-1.md`][worker-1] `## Integration
pass` — none is dead code; all three are live duplication.

- **DRY-1 (Medium) — the `PrivilegeRequiredUser` body and its rejection regex, twice.**
  `::test_derive_register_fields_rejects_privilege_fields` (~`:1218-1234`) and
  `::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call`
  (~`:1247-1267`) carry byte-identical nine-line model bodies and a byte-identical
  six-line `pytest.raises(ConfigurationError, match=…)` regex. Verified still identical
  at source this pass (`diff` of each pair's region is empty). The **regex** is the
  load-bearing half and is a `## Severity definitions` Medium on its face — "repeated
  literal / key / tuple that should be a named constant": a reworded production message
  costs a two-site sweep inside one file, and the message it mirrors
  (`::derive_register_fields`'s "cannot auto-expose protected user field(s)") is
  exactly the kind of text a later cycle rewords.
  **Shape:** a file-local `_PROTECTED_FIELD_REJECT` regex constant read by both rows,
  and a `_privilege_required_user()` factory returning a freshly declared model with
  `_unique_app_label()` — a factory rather than a shared class, because Django's app
  registry requires distinct classes.
  **Do not weaken either row.** The two rows pin different things (the helper, and the
  factory call) and their docstrings say so; the consolidation is of their setup, never
  of their assertions.
- **DRY-2 (Medium) — the sessionless `ConfigurationError` assertion block, twice.**
  `~:938-948` and `~:958-968` repeat the same four assertions (`isinstance(…,
  ConfigurationError)`, `"SessionMiddleware"`, `"AuthMiddlewareStack"`, `"session" in
  message.lower()`). Independently corroborated by the static helper's repeated-literal
  section (both middleware names at `2x`).
  **Shape:** a file-local `_assert_sessionless_configuration_error(res)` helper, leaving
  the two rows' only visible difference the thing that actually differs — the query
  (`_LOGIN_Q` vs `_LOGOUT_Q`).
- **DRY-3 (Low, pre-existing at HEAD) — `_CH_LOGOUT` duplicates `_LOGOUT_Q`
  byte-for-byte.** `:2510` and `:300`, both
  `"mutation{ logout{ ok errors{ field } } }"`. Readers grepped: `_LOGOUT_Q` has 11,
  `_CH_LOGOUT` has 3 — live duplication, not dead code. Folded into this loop because
  it is a one-line deletion plus three call-site renames **in the file the loop already
  opens**; leaving it guarantees the next cycle re-raises it. Worker 2 may decline it
  with a recorded reason if the Channels-section separation turns out to be load-bearing
  in a way nothing in the file states today.

**Scope fence for the loop.** `tests/auth/test_mutations.py` only. No production
change, no assertion weakened, no node id renamed — the four recorded failability
node-id sets must survive verbatim, so Worker 2 confirms by collection
(`--collect-only`) rather than inferring it, and re-runs
`scripts/prove_failability.py` entries 1 and 3 (whose failing rows live in the edited
regions) while leaving 2 and 4 alone. No `--cov*` flag; ruff scoped to the one file,
never `.`.

### Ruling 3 — the four-way subprocess idiom is NOT consolidated in this cycle

`tests/auth/test_mutations.py`, `tests/auth/test_sessions.py`,
`tests/base/test_init.py`, `tests/rest_framework/test_soft_dependency.py` each spell
`subprocess.run([sys.executable, "-c", …])` inline. Slice 6 already collapsed the two
copies **inside its own file** into `::_auth_free_subprocess`, which is the part it
owned and which removed a near-copy rather than adding one.

The remaining consolidation is **not** unblocked by Ruling 1: two of the four copies
live outside `tests/auth/` entirely, so `tests/auth/_helpers.py` could not host the
shared helper even if it were opened. A home for it is a repo-level `tests/` decision
— which conftest, what the contract is for a soft-dependency probe versus an
import-isolation probe — that belongs to a DRY cycle over the whole test tree, not to
a `spec-040` reconciliation cycle. → `### Deferred work catalog`.

### The inherited list, ticked

| # | Inherited item (source) | Disposition |
|---|---|---|
| 1 | Duplicated `PrivilegeRequiredUser` + rejection regex (Slice 6 W3 `DRY findings`; Slice 6 W1 pass-2 item 1) | **DRY-1**, dispatched |
| 2 | Duplicated sessionless assertion block (same) | **DRY-2**, dispatched |
| 3 | Cross-file `_declare_group_type` pair + the pre-existing `_declare_user_type` pair (Slice 6 plan `### DRY analysis`; W1 pass-2 item 3) | **Accepted duplication, closed.** Ruling 1 |
| 4 | Four-way subprocess idiom (Slice 6 plan `### Out-of-scope observations`; W1 pass-2 item 4) | **Deferred.** Ruling 3 |
| 5 | Pre-existing `_CH_LOGOUT` / `_LOGOUT_Q` duplicate (Slice 6 W3 `DRY findings`; W1 pass-2 item 5) | **DRY-3**, folded into the loop |
| 6 | `spec-042 Revision N` citations in `tests/middleware/test_debug_toolbar.py`; the bug-hunt round-provenance comment in `tests/auth/test_sessions.py` (W1 pass-2 item 6) | **For the maintainer.** Out of this cycle's population by spec and by file ownership; re-measured this pass at **5** and **1** hits respectively. → catalog |
| 7a | `bld-040-slice-1`'s link to the retired Decision 11 anchor (Worker 0's list; Slice 5; W1 pass-2 item 7) | **Repaired** — see `### Repair to another slice's artifact` |
| 7b | Slice 4's two un-edited `WIP-ALPHA-040-0.0.13` sites (same) | **One repaired (D4), one a decided non-edit** — below |
| 8 | Line 888's `<fill in …>` tool boilerplate inside Slice 6's pass-1 `### Failability proofs` block (W1 pass-2 item 8) | **Left.** [`ARTIFACT.md`][artifact-md] forbids editing a prior entry; there are no unfilled placeholders. → catalog, as a note for the maintainer |
| 9 | Slice 3's `F1` (`docs/GLOSSARY.md` privilege framing) and Slice 4's `F4` | **For the maintainer**, and this pass **sharpens it**: the same defect was in `## Goals` item 4 of the spec (D1). The glossary fix is now known to be a two-line change — the framing **and** `is_active` → catalog |
| 10 | Slice 3's `F2` / `F3` | **Closed by Slice 6**, re-verified this pass: `rg -n --glob '*.py' 'spec-040 Revision\|Revision-7 reload' .` → 0; `rg -n --glob '*.py' '_bind_mutation\|_bind_form_mutation' .` → only two `tests/mutations/test_sets.py` **test names** naming the live `bind_mutation_outputs` |

### Decided non-edits

Recorded so the absence of an edit is a decision rather than an omission.

- **Four surviving `WIP-ALPHA-040-0.0.13` occurrences, deliberately kept.**
  - `:59`, `:496`, `:1842` are **verbatim quotations of `spec-039`'s own text** (its
    status block and its Decision 14 / F8). Rewriting text inside a quotation would
    falsify the quotation and strand `spec-039`'s record; Slice 4 ruled the same way.
  - `:403`, the `## Slice checklist` Slice-3 card-wrap sub-bullet
    ("`WIP-ALPHA-040-0.0.13` → Done with the next `DONE-040-0.0.13` id"), is the
    lifecycle-**transition** class where neither prefix alone is true and a flip
    produces nonsense ("`DONE-…` → Done with the next `DONE-…` id"). Slice 4 named
    de-tensing as the fix and left it outside its fence. **I decline to de-tense it,
    on a ground Slice 4 did not have:** the blockquote immediately above that checklist
    declares the boxes "preserved as-authored and … intentionally not toggled", so the
    section is explicitly historical planning text, and the sub-bullet is a truthful
    description of the transition Slice 3 performed. Editing it would contradict the
    document's own stated convention to fix a sentence that is not false. Closed, not
    carried forward.
- **`## Current state`'s pre-cut observations stay.** Its "No `auth/` module exists",
  "The version line reads `0.0.12`" and "The fakeshop example … has no auth surface"
  bullets are all falsified by the tree today, and all three stand: the section opens
  "A true description of the repo as this spec is authored", which dates them, and
  [`BUILD.md`][build-md] ``### `## Current state`: observations stand, predictions do
  not`` is explicit. Graded clause by clause for a prediction riding along with an
  observation; none carries one. **This is precisely the distinction that made D5 an
  edit** — `## Key glossary references` carries no such header.
- **`## Slice checklist` / `## Implementation plan` / `## Doc updates` stay in the
  planning voice.** They are the card's plan, preserved; the shipped contract lives in
  the Decisions, the edge cases, the test plan and the DoD, which is where every D1-D5
  repair landed.
- **The companion's three duplicate heading slugs** (`justification-moved-from-the-spec`,
  `alternatives-considered-and-rejected`, `changes-this-decision-underwent`, one per
  Decision) are **not** a defect: they are per-Decision sub-headings, no in-page link
  targets any of them (all **77** in-page anchor uses resolve), and GitHub
  disambiguates repeats with a numeric suffix.

---

## Verification

Every figure below was measured as it was written.

### Gates

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md
OK: 30 terms - all have glossary entries and at least one spec link.
(exit 0)

$ uv run python scripts/check_citations.py --check
OK: 979 citations resolve (814 in 442 .py files, 165 in KANBAN.md).
(exit 0)
```

`check_citations.py` runs **whole-tree**, so that figure covers the repository and not
just this pass's files — including the concurrent `spec-050` session's dirty `.py`
files. Nothing in it is attributable to this cycle or to that one: it is green, and it
is the same 979 Slice 6 recorded, so no citation moved between that slice and this
pass.

### Anchors and the markdown link convention

Verified with a slug function implementing `START.md`'s GitHub rule (lowercase, drop
backticks, strip non-word except hyphens, each space to its own hyphen), fenced blocks
and code spans stripped first — never by eye.

| File | Headings | In-page anchor uses | Unresolved | Ref uses / defs | Undefined | Unused | Def paths missing |
|---|---|---|---|---|---|---|---|
| `docs/SPECS/spec-040-auth_mutations-0_0_13.md` | 34 | 165 | **0** | 421 / 96 | 0 | 0 | 0 |
| `docs/SPECS/appx/…-rationale.md` | 66 | 77 | **0** | 125 / 60 | 0 | 0 | 0 |
| `docs/builder/bld-040-slice-1-rationale_extraction.md` | 17 | 0 | **0** | 21 / 9 | 0 | 0 | 0 |

All ten canonical group headers present, in `START.md` order, in all three files;
every definition path resolved on disk **from its own file's directory**; new
definitions alphabetical within their group. Separately, every reference definition
carrying a cross-file anchor was resolved against the target file's real headings:
**80 checked, 0 unresolved** — which is what catches a rename like Slice 5's.

**Instrument note, recorded because it twice reported a false alarm.** My first
code-span filter was `` `[^`]*` ``, which does not see a **double-backtick** span; my
second did not see a **single-backtick span wrapped across a source line**. Both
blind spots made the Slice-1 artifact report an undefined label and an unresolved
anchor that do not exist — the artifact's quotation of the spec's old
`Risks` in-page link, and its quotation of the per-Decision pointer template naming
`rationale-dN`, are both *inside* code spans. The failures
were in the safe direction (false alarm, not false clean) and both were run down to
source before being reported rather than written up. The final instrument is
controlled: a copy of the spec with one bogus label and one bogus anchor appended
reports `undefined: ['no-such-label']` and `unresolved: ['no-such-heading']`, so the
zeros above are measurements and not an instrument that cannot fail.

### Pre-commit, over every file this pass wrote

```shell
$ uvx pre-commit run --files docs/SPECS/spec-040-auth_mutations-0_0_13.md \
      docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md \
      docs/builder/bld-040-integration.md \
      docs/builder/bld-040-slice-1-rationale_extraction.md
kanban tracked path constants ................ Passed
source layout (py trailing commas + ascii-only; md link-def scaffold; ...) Passed
ruff format .................................. (no files to check) Skipped
ruff check ................................... (no files to check) Skipped
kanban anchors collision-free ................ Passed
citations resolve (AGENTS.md rule 27) ........ Passed
```

Run twice, **with no rewrite on either run** — the `source-layout` hook, which is the
one that owns the `.md` link-definition scaffold, left all four files byte-identical
both times, so the scaffold they were written with is already the shape it enforces.
The two `Skipped` lines are genuine: this pass writes no `.py`, and every path above
was passed **explicitly** rather than through a shell variable, which is the condition
under which a `(no files to check) Skipped` is a fact rather than the zsh
word-splitting artifact Slice 6's build report caught (`START.md` `## Instruments that
lie`). `source-layout` ran on all four and passed, which is the positive half of that
reading.

### Focused tests

```shell
$ uv run pytest tests/auth/ examples/fakeshop/test_query/test_auth_api.py --no-cov -q
216 passed in 9.16s
```

216 = the 195 + 21 every pass of Slice 6 recorded. No `--cov*` flag anywhere
([`BUILD.md`][build-md] `## Coverage is the maintainer's gate, not a worker's tool`);
`--no-cov` because `pytest.ini` auto-applies `--cov`. Nothing failed, so no attribution
question against the concurrent session arose.

### Tree state

- `git diff --stat` over the build's six files: **365 insertions / 72 deletions** —
  byte-for-byte the figure Worker 3 and Worker 1 both recorded at the close of Slice 6,
  so nothing moved between that slice and this pass.
- `git diff --stat -- django_strawberry_framework/types/` is **empty** and
  `find . -name 'ACTIVE-MUTATION.json'` returns nothing: both transient failability
  mutations are gone, confirmed by me rather than read from a report.
- `git diff -- django_strawberry_framework/__init__.py` is **empty**.

### Working-tree note (stop-and-report, no action taken)

`git status --short` shows this pass's own three files plus a set this pass did not
write and did not touch: the concurrent `spec-050` session's
`django_strawberry_framework/{list_field,orders/sets,utils/querysets}.py`,
`docs/GLOSSARY.md`, `docs/feedback.md`,
`docs/spec-050-list_field_arguments-0_0_15.md`, `docs/builder/bld-final.md`,
`docs/builder/bld-slice-3-sql_and_unit_contracts.md`,
`examples/fakeshop/db.sqlite3`, `examples/fakeshop/test_query/test_list_field_*.py`,
`test_multi_db.py`, `tests/orders/test_sets.py`, `tests/test_list_field.py`,
`tests/utils/test_querysets.py`; plus cohort B's six files, still dirty from Slice 6.
**Nothing was reverted, checked out, stashed, or tidied** ([`AGENTS.md`][agents] rule
34). No `git stash` / `checkout` / `restore` / `worktree` was used anywhere in this
pass; every read-only HEAD reference went through `git show HEAD:<path>` into a scratch
path outside the repository.

---

## Everything that must reach the final gate's `### Deferred work catalog`

One bullet each, with its source artifact section and the reason it is deferred.

1. **The four-way subprocess-isolation idiom** — `tests/auth/test_mutations.py`,
   `tests/auth/test_sessions.py`, `tests/base/test_init.py`,
   `tests/rest_framework/test_soft_dependency.py`. Source: Slice 6 plan
   `### Out-of-scope observations`, Slice 6 W1 pass-2 item 4. Deferred because two of
   the four copies sit outside `tests/auth/`, so the shared home is a repo-level
   `tests/` decision belonging to a DRY cycle. This build already collapsed the two
   copies inside its own file.
2. **`docs/GLOSSARY.md`'s `## Auth mutations` entry, findings `F1` / `F4`, sharpened.**
   Source: Slice 3 `### Notes for Worker 1` F1, Slice 4 F4, and D1 of this pass. The
   entry repeats the retired structural-only framing **and** omits `is_active` from the
   refused list. Now known to be exactly the defect this pass fixed in `## Goals` item
   4, so the fix is a two-part DB edit + `scripts/build_glossary_md.py`. Out of this
   cycle's scope fence (the glossary is DB-backed and out-of-scope for edits) — for the
   maintainer.
3. **`spec-042 Revision N` citations in `tests/middleware/test_debug_toolbar.py`** — 5
   hits, re-measured this pass. Source: Slice 6 plan `### Out-of-scope observations`.
   Same defect class as `F2`, a different spec's population and a different owner. For
   the maintainer.
4. **The bug-hunt round-provenance comment in `tests/auth/test_sessions.py`** — 1 hit
   (`# Revision guards: … (hunt 0_0_14 rev)`). Source: same. `START.md` `## Style Rio
   cares about` bans round provenance in code; the file was on no cohort's writable
   list and cites no spec, so it is outside `F2`'s population. For the maintainer.
5. **`Revision N P<n>` citations in `examples/fakeshop/test_query/test_library_api.py`**
   — 5 hits. Source: Slice 6 plan `### Out-of-scope observations`. That file belongs to
   the **concurrently active `spec-050` cycle** and must not be touched by this one.
6. **Slice 6's artifact line 888 carries `scripts/prove_failability.py`'s own
   `<fill in …>` boilerplate line** inside a prior `### Failability proofs` entry.
   Source: Slice 6 W1 pass-1 and pass-2. There are no unfilled placeholders; it is the
   tool's explanatory line, and [`ARTIFACT.md`][artifact-md] forbids editing a prior
   entry, so it stays. Cosmetic, for the maintainer's awareness only.
7. **DoD item 6's coverage clause remains structurally unverifiable by any worker.**
   Source: Slice 4 `### Spec changes made`, the one un-ticked box of that slice. Its
   other half (`D-N3`'s source comment) is now **discharged** by Slice 6 and by this
   pass's companion edit; the coverage half is the maintainer's gate by construction
   ([`BUILD.md`][build-md] `## Coverage is the maintainer's gate, not a worker's tool`).
8. **The `_declare_group_type` / `_declare_user_type` per-file pairs are accepted, not
   deferred** — listed here only so the final gate does not re-open them. Ruling 1
   above is the decided answer, and the condition that would change it (a third caller,
   or a decision to widen `_helpers.py`'s contract to registry-mutating declarations)
   is recorded with it.

---

## Summary

The pass read the six `bld-040-slice-*` artifacts by name — the `BUILD.md` glob would
have swept the concurrent `spec-050` cycle instead — and then read `spec-040` end to
end as one document, which is the instrument no slice runs.

**Twelve contracts live in more than one home; five of them disagreed.** The headline
is that the claim Slice 3 retired from Decision 6 and Slice 6 then caught still live in
Decision 6's own body was **also** live at three further homes — `## Goals` item 4,
`### Decision 8` and `## Definition of done` item 4 — and that `## Goals` additionally
named four of the five protected columns, the same omission Slice 3 filed against the
glossary as `F1`. A per-line `rg` could not see it: the phrase wraps across two source
lines, and only a whitespace-normalized sweep recovers the third of the population it
hides. Second: `### Decision 10` asserted that `auth/` **imports** `SyncMisuseError`
while the `D18 / D19` obligation it cross-references asserted that it **does not** —
settled against source (zero imports, two docstring mentions), and the obligation was
right. Neither sentence is wrong on its own page.

Ten spec edits and their companion entries close all five divergences, plus the one
chronology attribution Slice 1's `Revision-N`-keyed sweep could not see. The
markdown-link, anchor and glossary gates are green and their instruments controlled;
`check_citations.py` is green whole-tree at the same 979 the prior slice measured; the
staged-anchor sweep finds **5 prose hits and zero staged anchors**, with a live
positive control behind the count.

`tests/auth/_helpers.py` is **not** opened, decided on four grounds and not on effort,
and the consequence is dispatched rather than deferred: **one consolidation loop over
`tests/auth/test_mutations.py`** for two intra-file near-copies plus a pre-existing
byte-identical query constant, all of which fail the single-edit-site test inside one
file the loop already opens. The cross-file `_declare_group_type` pair is closed as
accepted duplication with the reason verified at source. The status is
`revision-needed` for that loop alone; nothing in the spec, the companion or the
shipped code is left inconsistent.

---

## Build report (Worker 2)

The consolidation loop `### Ruling 2` dispatched, run in full. Three consolidations,
all inside `tests/auth/test_mutations.py`; no other file opened. `tests/auth/_helpers.py`
and `tests/auth/conftest.py` were **not** opened, in either sense - not edited and not
read. `### Ruling 1` is taken as settled, and nothing in the three items reached for a
second file, so the stop-and-report condition never fired.

### Files touched

Grounded in `git status --short`, not memory.

- `tests/auth/test_mutations.py` - the three consolidations below. Already dirty from
  Slice 6 before this pass; this pass adds to that same working-tree change.
- `docs/builder/bld-040-integration.md` - this build report appended, `Status:` set to
  `built`. No prior entry edited.
- `docs/builder/worker-memory/worker-2-040.md` - one appended memory entry (gitignored
  at `.gitignore:188`, so it does not appear in `git status`).
- `docs/builder/temp-tests/040-integration/{proofs.json,proof-report.md}` - the proof
  manifest and the tool's report (gitignored at `.gitignore:192`).

Nothing else in `git status --short` is attributable to this pass; see
`### Working-tree note` below.

### Tests added or updated

No row added, no row removed, no row renamed. Three shared seams extracted from rows that
already existed:

- `tests/auth/test_mutations.py::_PROTECTED_FIELD_REJECT` - **DRY-1**, the regex half. The
  `register_mutation() cannot auto-expose protected user field(s) ['is_staff'] ...
  PrivilegeRequiredUser` pattern, previously spelled byte-identically inside both
  `pytest.raises(match=...)` calls, is now one constant read by both.
- `tests/auth/test_mutations.py::_privilege_required_user` - **DRY-1**, the model half. A
  factory returning a freshly declared `PrivilegeRequiredUser` with its own
  `_unique_app_label()`, replacing the two byte-identical nine-line inline class bodies.
- `tests/auth/test_mutations.py::_assert_sessionless_configuration_error` - **DRY-2**. The
  assertion block (`res.errors is not None`, `isinstance(..., ConfigurationError)`,
  `"SessionMiddleware" in message`, `"AuthMiddlewareStack" in message`,
  `"session" in message.lower()`) previously repeated verbatim in both sessionless rows.
- **DRY-3** - `_CH_LOGOUT` deleted; its three readers now read `_LOGOUT_Q`, the constant it
  duplicated byte-for-byte. **Taken, not declined:** nothing in the file states the
  Channels-section separation is load-bearing, and its two siblings do not establish one
  either - `_CH_LOGIN` genuinely differs from `_LOGIN_Q` (both operands as variables, no
  `messages` selection) and `_CH_ME` has no non-Channels twin, so the `_CH_` prefix marks a
  *different document*, which `_CH_LOGOUT` was not. The section's header comment now names
  `_LOGOUT_Q` as the document those rows send, so the removal leaves the section readable
  instead of silently cross-referencing.

**Before / after shape, per item.**

| Item | Before | After |
|---|---|---|
| DRY-1 | 2 x 9-line inline `PrivilegeRequiredUser` body + 2 x 6-line `match=` regex, byte-identical | 1 factory + 1 named regex constant; each row is `with pytest.raises(ConfigurationError, match=_PROTECTED_FIELD_REJECT):` over its own subject |
| DRY-2 | 2 x 6-line assertion block, byte-identical | 1 helper; each row ends `_assert_sessionless_configuration_error(res)`, leaving the rows' only visible difference the query (`_LOGIN_Q` vs `_LOGOUT_Q`) |
| DRY-3 | Two definitions of one string: `_CH_LOGOUT` (3 readers) and `_LOGOUT_Q` (11) | One definition, 14 readers |

**No assertion weakened.** The three extractions are of setup and assertion *material*,
never of the assertions themselves:

- `_assert_sessionless_configuration_error` asserts **exactly** the conditions the two
  blocks asserted, in the same order, on the same values - the `ConfigurationError` class
  check and both middleware names included. That is what keeps the two rows distinguishing
  the shipped `require_session` contract from the superseded raw-`AttributeError` path: an
  `AttributeError` fails `isinstance(..., ConfigurationError)`, and Django's own message
  names neither `SessionMiddleware` nor `AuthMiddlewareStack`. The helper's docstring
  states that, so the reason a bare `"session"` substring is not sufficient survives the
  extraction rather than being stranded in the two row docstrings.
- `_PROTECTED_FIELD_REJECT` is the two regexes' shared bytes with nothing dropped,
  including the `.*PrivilegeRequiredUser` tail that pins *which* model the production
  message names.
- Both DRY-1 rows keep their own docstrings and their own subjects
  (`derive_register_fields(...)` versus `register_mutation()` under the monkeypatched
  `get_user_model`) - the difference their docstrings say they pin.

Mechanical corroboration rather than prose: both DRY-1 rows and both DRY-2 rows are still
in the failing set of their boundary's mutant, at the same scope, with the same node ids
(`### Failability proofs` below).

### Validation run

```shell
$ uv run ruff format tests/auth/test_mutations.py
1 file left unchanged

$ uv run ruff check --fix tests/auth/test_mutations.py
All checks passed!
```

Both scoped to the one file, **never `.`**, and both paths typed literally - never through
a shell variable (`START.md` `## Instruments that lie`; the hazard Slice 6's build report
caught, where `ruff format $FILES` errored as one path while `pre-commit --files $FILES`
printed `Skipped (no files to check)`).

`git status --short` was run after both ruff invocations; every entry is classified under
`### Working-tree note` below.

Focused tests, no `--cov*` flag anywhere (`--no-cov` because `pytest.ini` auto-applies
`--cov`):

```shell
$ uv run pytest tests/auth/ --no-cov
195 passed in 4.65s

$ uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov
21 passed in 8.58s
```

195 + 21 = **216**, the figure every pass of Slice 6 and the integration pass recorded.

Pre-commit, over every file this pass wrote, paths passed explicitly:

```shell
$ uvx pre-commit run --files tests/auth/test_mutations.py \
      docs/builder/bld-040-integration.md \
      docs/builder/worker-memory/worker-2-040.md
kanban tracked path constants ................ Passed
source layout (py trailing commas + ascii-only; md link-def scaffold; ...) Passed
ruff format .................................. Passed
ruff check ................................... Passed
kanban anchors collision-free ................ Passed
citations resolve (AGENTS.md rule 27) ........ Passed
```

Re-run until it rewrote nothing: run 1 rewrote nothing and run 2 rewrote nothing, all
three files byte-identical across both runs. The `ruff format` / `ruff check` lines read
`Passed`, not `Skipped (no files to check)` - this pass writes a `.py`, so those hooks
genuinely had input.

### Failability proofs

**None; this pass introduced no new boundary.** Every change is an extraction of existing
test material inside one test file; no production line moved, and nothing added here says
"no".

The evidence that the four existing proofs still hold is a **node-id set comparison**, run
as two independent instruments.

**1. Collected-node-id set, before and after, compared as sets.**

```shell
$ uv run pytest tests/auth/test_mutations.py --collect-only -q -q --no-cov \
      -p no:cacheprovider | grep '::' | sort > <scratch>/nodeids-before.txt   # 116 ids
# ... the three consolidations, then ruff ...
$ uv run pytest tests/auth/test_mutations.py --collect-only -q -q --no-cov \
      -p no:cacheprovider | grep '::' | sort > <scratch>/nodeids-after.txt    # 116 ids
$ diff <scratch>/nodeids-before.txt <scratch>/nodeids-after.txt
(no output; exit 0)
```

`diff` over the two sorted id lists is the set comparison - **empty**, so the collected set
is identical id for id, not merely equal in cardinality. No test function renamed, no
`ids=` touched, no parametrization added or removed, no two rows merged: the empty `diff`
proves it rather than claiming it. The 116 figures are `wc -l` of each file.

`-q -q` rather than `-q` because `pytest.ini`'s `addopts` carries `-v`: a single `-q` nets
to verbosity 0, which prints `<Function ...>` tree lines containing no `::`, so a
`grep '::'` over that output yields an empty file - and two empty files diff clean. The
116-line counts on both sides are the control that the grep saw anything at all.

**2. The two boundaries whose failing rows live in the edited regions, re-proved.**
`### Ruling 2`'s scope fence directs entries **1** (`::_transport_prologue`, whose rows are
the DRY-2 pair) and **3** (`::_REGISTER_PROTECTED_FIELDS`, whose rows are the DRY-1 pair)
to be re-run and **2** and **4** to be left alone. Entries 2 and 4 were left alone; nothing
in this pass touches their rows or their production sites.

```shell
$ uv run python scripts/prove_failability.py \
      docs/builder/temp-tests/040-integration/proofs.json \
      --scratch-root <scratchpad>/failability-040-integration \
      --output docs/builder/temp-tests/040-integration/proof-report.md
EXIT=0
```

The manifest holds Slice 6's two entries copied verbatim - a **new manifest** rather than
`--only` over Slice 6's, so the emitted report is a complete record of what it claims and
is not labelled PARTIAL, and Slice 6's own manifest is untouched. Scratch root outside the
repository; one mutation live at a time, restored in the tool's `finally` and proved by
`filecmp.cmp(shallow=False)` plus SHA-256 against the pre-mutation copy; `git` never
invoked.

| # | Boundary | Mutation applied | Rows | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/auth/mutations.py::_transport_prologue` | `session = sessions.require_session(request, transport)` -> `session = getattr(request, "session", None)`, so login/logout no longer reject a sessionless request | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/auth/` | `filecmp.cmp(shallow=False)` True; sha256 `ad6a3f7efea49aab...` == `ad6a3f7efea49aab...` |
| 2 | `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS` | the protected-field frozenset emptied to `frozenset()`, so the intersection never matches and `::derive_register_fields` never raises | **2** | 0 | same | `filecmp.cmp(shallow=False)` True; sha256 `ad6a3f7efea49aab...` == `ad6a3f7efea49aab...` |

Failing node ids (the count is the `len()` of each list):

1. `django_strawberry_framework/auth/mutations.py::_transport_prologue`
   - `tests/auth/test_mutations.py::test_sessionless_login_raises_the_configuration_error_naming_both_middlewares`
   - `tests/auth/test_mutations.py::test_sessionless_logout_raises_the_configuration_error_naming_both_middlewares`
   - pytest summary `2 failed, 193 passed`, exit code 1; pre-mutation state of that same
     scope `195 passed`, exit code 0, so **0** pre-existing failing rows differenced out;
     collection/setup errors **0**.
2. `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS`
   - `tests/auth/test_mutations.py::test_derive_register_fields_rejects_privilege_fields`
   - `tests/auth/test_mutations.py::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call`
   - pytest summary `2 failed, 193 passed`, exit code 1; pre-mutation state `195 passed`,
     exit code 0, **0** differenced out; collection/setup errors **0**.

**Both sets are identical, id for id, to Slice 6's `### Failability proofs` entries 1 and
3** - which is why they were re-run rather than reasoned about. The consolidation moved the
material those four rows use, and an extraction that quietly stopped exercising the
boundary would show here as a shrunk failing set while still collecting 116 ids and still
passing green. It did not. No zero-row entry, so no `why 0` judgement is owed; 2 rows
clears the 0-or-1 weakly-pinned rule for both.

**No mutation is live across this `Status:` transition.** Post-proof anchor re-check, run
after the tool finished, by me rather than read out of its report:

```shell
$ grep -c 'session = sessions.require_session(request, transport)' \
      django_strawberry_framework/auth/mutations.py    -> 1
$ grep -c '_REGISTER_PROTECTED_FIELDS = frozenset($' \
      django_strawberry_framework/auth/mutations.py    -> 1
$ find . -name 'ACTIVE-MUTATION.json'                  -> (nothing)
```

`django_strawberry_framework/auth/mutations.py` is dirty against HEAD - it already was,
from Slice 6's comment and docstring edits, and **this pass did not edit it**. Its restore
is proved against the tool's pre-mutation copy, the correct reference in a legitimately
dirty tree; an empty `git diff` is unachievable here and forcing one would destroy Slice
6's work ([`BUILD.md`][build-md] `## Failability proofs`).

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **`_privilege_required_user()` is a factory, not a module-level class.** The two rows
  need two distinct Django model classes: one shared class would be re-registered on the
  second row under one `app_label`. The factory calls `_unique_app_label()` per call, the
  idiom every other inline model in this file already uses.
- **The factory's inner class keeps the name `PrivilegeRequiredUser` verbatim** because
  `_PROTECTED_FIELD_REJECT`'s `.*PrivilegeRequiredUser` tail matches on it. Renaming the
  class would silently stop the regex from pinning which model the production message
  names, and the assertion would still pass on the class-name-free prefix. The factory
  docstring says so, at the site where a rename would be attempted.
- **The regex constant sits with the register-rider section, not the module's constant
  block.** Both readers are in that section; putting it beside `_LOGIN_Q` would place it
  900 lines from either use for no gain.
- **`_assert_sessionless_configuration_error` takes the `ExecutionResult`, not the
  message.** Taking the message would push `res.errors is not None` and the
  `isinstance(..., ConfigurationError)` check back out to both call sites - half the
  duplication, and the half carrying the class check. Precedent in this file:
  `::_assert_login_fully_compensated` likewise takes the `request` and unwraps it itself.
- **The two sessionless rows keep their own docstrings unchanged.** The login row's
  docstring already explained why a bare `"session"` substring distinguishes nothing; that
  reasoning now also sits in the helper, where the assertions live. Rewriting the row
  docstrings was not required by the ruling and would be churn in a file three prior passes
  have pinned text in.
- **DRY-3's deleted constant is replaced by a comment, not by nothing.** The Channels
  section's header comment now states that its logout rows send `_LOGOUT_Q`, so a reader
  arriving at `_ch_post(router, _LOGOUT_Q, ...)` does not have to grep 2,200 lines back to
  find where the document is defined.

### Notes for Worker 3

- **The instrument that matters here is the collect-only set diff, and it has a trap.**
  `pytest.ini`'s `addopts` carries `-v`, so `--collect-only -q` nets to verbosity 0 and
  prints `<Function ...>` tree lines with no `::` in them; a `grep '::'` over that yields an
  empty file, and two empty files diff clean - a self-falsifying instrument that reads
  exactly like a passing set comparison. `-q -q` is what makes it print node ids, and the
  116-line counts on both sides are the control.
- Entries **2** (`types/finalizer.py::finalize_django_types`) and **4**
  (`types/resolvers.py::_check_n1`) were deliberately not re-run, per `### Ruling 2`. Their
  rows - `::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[finalize]`
  and `[schema]`, `::test_an_unplanned_relation_under_login_node_is_strictness_visible`, and
  `tests/auth/test_queries.py::test_an_unplanned_relation_under_me_is_strictness_visible` -
  are covered by the collect-only set diff, so their node ids are proved unchanged even
  though their mutants were not re-run.
- No shadow file and no `scripts/review_inspect.py` run was used in this pass.

### Notes for Worker 1 (spec reconciliation)

No spec gap, conflict or unstated assumption surfaced. This pass touches one test file and
no spec surface; `docs/SPECS/spec-040-auth_mutations-0_0_13.md` was read as required reading
only, read-only.

One item is worth a line wherever the cycle's dispositions are recorded, since
`### Ruling 2` left it to the builder: **DRY-3 was taken, not declined**, and the ground is
a finding rather than a preference - the `_CH_` prefix in this file marks a different
GraphQL document, which `_CH_LOGOUT` was not, so the naming convention was never what
justified the duplicate.

### Working-tree note (stop-and-report, no action taken)

`git status --short` after both ruff invocations lists, beyond this pass's own
`tests/auth/test_mutations.py` and `docs/builder/bld-040-integration.md`: cohort B's Slice 6
files still dirty (`django_strawberry_framework/auth/mutations.py`,
`django_strawberry_framework/mutations/{resolvers,sets}.py`,
`docs/SPECS/spec-040-auth_mutations-0_0_13.md`, `tests/auth/test_queries.py`,
`examples/fakeshop/test_query/test_auth_api.py`, and this cycle's untracked
`docs/builder/bld-040-*`, `docs/builder/build-040-*` and
`docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`), plus the concurrent
`spec-050` session's `django_strawberry_framework/{list_field.py,orders/sets.py,
utils/querysets.py}`, `docs/GLOSSARY.md`, `docs/feedback.md`,
`docs/spec-050-list_field_arguments-0_0_15.md`, `docs/builder/bld-final.md`,
`docs/builder/bld-slice-3-sql_and_unit_contracts.md`, `examples/fakeshop/db.sqlite3`,
`examples/fakeshop/test_query/test_list_field_api.py`,
`examples/fakeshop/test_query/test_list_field_async_api.py`,
`examples/fakeshop/test_query/test_multi_db.py`, `tests/orders/test_sets.py`,
`tests/test_list_field.py` and `tests/utils/test_querysets.py`.

**Nothing was reverted, checked out, stashed or tidied** ([`AGENTS.md`][agents] rule 34). No
`git stash` / `checkout` / `restore` / `worktree` anywhere in this pass. Both ruff runs were
scoped to the single file, which is what kept the churn from existing.

### Nothing left undone

All three dispatched consolidations landed. No item was deferred, declined or partially
applied, and no consolidation required a file outside `tests/auth/test_mutations.py`.

---

## Review (Worker 3)

Reviewing the consolidation loop `### Ruling 2` dispatched, not Slice 6's rows. Slice 6 is
closed (`final-accepted`, reviewed twice), so the navigational filter is Worker 2's
`### Files touched` / `### Tests added or updated` against the cumulative working-tree diff
of `tests/auth/test_mutations.py` ([`worker-3.md`][worker-3] `## Review job`, the
cumulative-diff trap). Line numbers here are pin-at-write-time hints (per-cycle scratchpad).

### Failability re-run pre-registration (recorded BEFORE the mutations were made)

[`worker-3.md`][worker-3] `### Reading is necessary, not sufficient` requires the mutation to
be recorded in this artifact before it is applied. Two boundaries sit inside the mandatory
floor **and** inside this diff's blast radius, so both are re-run; the other two recorded
boundaries were not touched by this pass and `### Ruling 2` directs they be left alone.

1. `django_strawberry_framework/auth/mutations.py::_transport_prologue` — replace
   `    session = sessions.require_session(request, transport)` with
   `    session = getattr(request, "session", None)`, so a sessionless login/logout is no
   longer refused. Scope as Worker 2 and Slice 6 recorded it: `tests/auth/`.
2. `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS` — replace the
   five-name frozenset with `frozenset()`, so the intersection never matches and
   `::derive_register_fields` never raises. Scope: `tests/auth/`.

Applied one at a time via `scripts/prove_failability.py` (which enforces the anchor check
before the pre-mutation copy), from my own manifest
`docs/builder/temp-tests/040-integration/w3-proofs.json` — Worker 2's manifest left untouched
— with the scratch root outside the repository. Restores proved by byte comparison. No
`git checkout` / `stash` / `restore` anywhere in this pass.
### Failability re-run results

Both boundaries re-run at the scope Worker 2 and Slice 6 recorded (`tests/auth/`), one at a
time, through `scripts/prove_failability.py`. Manifest
`docs/builder/temp-tests/040-integration/w3-proofs.json`, report
`docs/builder/temp-tests/040-integration/w3-proof-report.md`, scratch root outside the repo.
`EXIT=0`.

Pre-mutation anchor check, run by me before the tool and again after it finished:

```shell
$ grep -c '    session = sessions.require_session(request, transport)' \
      django_strawberry_framework/auth/mutations.py           -> 1   (before and after)
$ grep -c '_REGISTER_PROTECTED_FIELDS = frozenset($' \
      django_strawberry_framework/auth/mutations.py           -> 1   (before and after)
$ grep -c 'session = getattr(request, "session", None)' ...   -> 0   (mutant absent after)
$ grep -c '_REGISTER_PROTECTED_FIELDS = frozenset()' ...      -> 0   (mutant absent after)
$ find . -name 'ACTIVE-MUTATION.json'                         -> (nothing, before and after)
```

| # | Boundary | Rows | Errors | Pre-mutation baseline | Restore |
|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/auth/mutations.py::_transport_prologue` | **2** | 0 | `195 passed`, exit 0; 0 differenced out | `filecmp.cmp(shallow=False)` True; sha256 `ad6a3f7efea49aab...` == `ad6a3f7efea49aab...` |
| 2 | `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS` | **2** | 0 | `195 passed`, exit 0; 0 differenced out | `filecmp.cmp(shallow=False)` True; sha256 `ad6a3f7efea49aab...` == `ad6a3f7efea49aab...` |

Failing node ids, mine, listed so the count is `len()` rather than asserted:

1. `::_transport_prologue` — `tests/auth/test_mutations.py::test_sessionless_login_raises_the_configuration_error_naming_both_middlewares`,
   `tests/auth/test_mutations.py::test_sessionless_logout_raises_the_configuration_error_naming_both_middlewares`.
   Mutant summary `2 failed, 193 passed`, exit 1.
2. `::_REGISTER_PROTECTED_FIELDS` — `tests/auth/test_mutations.py::test_derive_register_fields_rejects_privilege_fields`,
   `tests/auth/test_mutations.py::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call`.
   Mutant summary `2 failed, 193 passed`, exit 1.

**Both sets match Worker 2's record and Slice 6's entries 1 and 3 id for id** — three
measurements, one set each. No zero-row entry, so no `why 0` judgement is owed; 2 rows clears
the 0-or-1 weakly-pinned rule for both.

**Where the second pair of eyes landed.** Re-run: `::_transport_prologue` and
`::_REGISTER_PROTECTED_FIELDS`. Accepted on Worker 2's record and Slice 6's, deliberately not
re-run: `django_strawberry_framework/types/finalizer.py::finalize_django_types` and
`django_strawberry_framework/types/resolvers.py::_check_n1`. Grounds for the split: this pass
edits only the four rows that the first two boundaries' mutants fail, so those two are the only
ones whose failing sets this diff could have shrunk; the other two are named in `### Ruling 2`'s
fence and their rows are untouched, and I re-measured `finalizer.py` myself one pass ago
(Slice 6 pass 2) at the same scope with the same set.

After both proofs, `django_strawberry_framework/auth/mutations.py` is **executable-token
identical to HEAD** — comments and docstrings stripped, ASTs compared — so the restore is
complete and Slice 6's edits to that file remain comment-only:

```shell
$ python - <<'PY'   # strip docstrings, compare ast.dump
AST (docstrings stripped) HEAD == worktree: True
PY
$ shasum -a 256 django_strawberry_framework/auth/mutations.py
ad6a3f7efea49aab50858adf5a7c1da075bd3ab4d93385cd83b1292885e3cbe0
```

### Node ids: my own derivation, with a control that shows the instrument can fail

Worker 2's 116-before / 116-after / empty-`diff` is not accepted on its face. Re-derived here
three ways; the first is the control the trap demands.

**Control — the instrument can fail.** `pytest.ini`'s `addopts` carries `-v`, so:

```shell
$ uv run pytest tests/auth/test_mutations.py --collect-only -q -q --no-cov \
      -p no:cacheprovider | grep '::' | sort | wc -l   -> 116
$ uv run pytest tests/auth/test_mutations.py --collect-only -q   --no-cov \
      -p no:cacheprovider | grep '::' | sort | wc -l   ->   0
```

The single-`-q` form yields **0** lines, exactly as Worker 2's `### Notes for Worker 3` warned.
Two such files would `diff` clean. My set comparison is therefore run on an instrument I have
watched produce an empty result under the wrong flag, and the 116 is its control.

**Second instrument — AST-derived ids, independent of pytest.** Parsing the file and
enumerating module-level `test_*` functions plus explicit `ids=` lists gives 102 entries; the
pytest set is 116. The whole 14-id difference is three parametrizations with **auto-generated**
ids my parser does not synthesize
(`::test_hostile_is_authenticated_value_truthiness_collapses_to_anonymous` 5,
`::test_register_write_step_non_str_password_defense_in_depth` 7,
`::test_storable_weird_credentials_reach_the_backend_unchanged` 5 — 17 pytest ids for 3 AST
entries). All three predate this build. Modulo that known limitation the two instruments agree
member for member.

**The "before" side, attributed rather than borrowed.** The same AST derivation over
`git show HEAD:tests/auth/test_mutations.py` (written to a scratch path outside the repo) and
over the worktree differs by exactly five ids, and every one is a documented **Slice 6**
addition, not a consolidation effect:

```text
+ test_an_unplanned_relation_under_login_node_is_strictness_visible          (Slice 6 TG-3)
+ test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[finalize]  (TG-1)
+ test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[schema]    (TG-1)
+ test_register_mutation_rejects_a_protected_required_field_at_the_factory_call     (TG-2)
- test_sessionless_request_surfaces_djangos_own_error                        (TG-0 rename)
+ test_sessionless_login_raises_the_configuration_error_naming_both_middlewares     (TG-0)
+ test_sessionless_logout_raises_the_configuration_error_naming_both_middlewares    (TG-0)
```

Nothing in that delta is unattributable, so the consolidation renamed, added, merged and
removed **no** node id. This is a stronger statement than an empty before/after `diff`: a
before/after `diff` shows the set did not move, this shows every way it moved since HEAD has a
named owner that is not this pass.

### Did any assertion weaken? — the first question, answered mechanically

**DRY-2, `::_assert_sessionless_configuration_error` (`tests/auth/test_mutations.py:922-934`).**
The helper carries five assertions in the original order: `res.errors is not None`,
`isinstance(res.errors[0].original_error, ConfigurationError)`, `"SessionMiddleware" in message`,
`"AuthMiddlewareStack" in message`, `"session" in message.lower()`. That is the closed set both
pre-consolidation blocks carried, per two independent records written **before** the
consolidation: Slice 6's plan row for `TG-0` (`bld-040-slice-6-code_remediation.md:352`) and
its build report (`:703-709`), and `### Ruling 2`'s own re-verification at source. Nothing
dropped, nothing widened, nothing reordered.

The mechanical half is the `::_transport_prologue` mutant, and it is the decisive one for the
`TG-0` question. With `require_session` replaced by a `getattr` default, a sessionless request
walks into Django's own `login()` and earns the raw `AttributeError` — the **superseded** path.
Both rows fail under that mutant, which is only possible because the class check survived the
extraction; a helper that had kept only the `"session"` substring would hold under the raw
`AttributeError` too and the mutant would have shown **0** rows. It showed 2, the same 2. The
defect the slice was dispatched to remove has not been reinstated.

**DRY-1, `_PROTECTED_FIELD_REJECT` (`:1199-1202`).** Proved byte-identical to the regex that
stood at HEAD, `.*PrivilegeRequiredUser` tail included, by pulling both out of the AST rather
than by eye:

```text
HEAD  ::test_derive_register_fields_rejects_privilege_fields, inline match=:
  "register_mutation\\(\\) cannot auto-expose protected user field\\(s\\) \\['is_staff'\\].*PrivilegeRequiredUser"
NOW   _PROTECTED_FIELD_REJECT:
  "register_mutation\\(\\) cannot auto-expose protected user field\\(s\\) \\['is_staff'\\].*PrivilegeRequiredUser"
BYTE-IDENTICAL: True
```

The **second** regex — Slice 6's, on the factory-call row — has no HEAD version to diff against,
so its byte-identity rests on the two pre-consolidation records that assert it (Slice 6's own
`DRY findings` at `:1271-1279` and `### Ruling 2`, which re-`diff`ed the pair at source and got
an empty result). Stated plainly because it is the one link in this chain I could not
re-derive. It is not load-bearing on the weakening question, though, and here is why: the tail
is asserted through `re.search` on **both** rows, both rows pass, and the second row reaches the
message through `register_mutation()` rather than the helper — so the shared constant is proved
live, with its tail, on both production paths by the passing rows themselves. A silently weaker
constant could not do that.

The model half is equally mechanical: the factory's inner `PrivilegeRequiredUser`
(`:1213-1223`) is **AST-identical** to HEAD's inline class body — same fields, same
`USERNAME_FIELD`, same `REQUIRED_FIELDS` tuple, same `Meta.app_label = _unique_app_label()`.

**DRY-3.** No assertion involved; the three rows send the identical byte string they sent
before (`_CH_LOGOUT` and `_LOGOUT_Q` were the same literal). Confirmed by the executable-literal
census below: `mutation{ logout{ ok errors{ field } } }` now appears **1x** where it appeared
2x.

### Is DRY-3 correct rather than merely tidy? — the claim checked at source

Worker 2 took DRY-3 on the ground that the `_CH_` prefix marks a *different document*. Verified
member by member against the file, not against the report:

| Constant | Non-`_CH_` twin | Verdict |
|---|---|---|
| `_CH_LOGIN` (`:1995`) | `_LOGIN_Q` (`:296`) | **Genuinely different.** `_CH_LOGIN` parameterizes BOTH operands (`$u`, `$p`) and selects `errors{ field }`; `_LOGIN_Q` hardcodes `username: "probe"` and selects `errors{ field messages }`. Two documents. |
| `_CH_ME` (`:1999`) | none | No twin exists; `{ me{ username } }` has no non-`_CH_` spelling anywhere in the file. |
| `_CH_LOGOUT` (deleted, was `:2510`) | `_LOGOUT_Q` (`:300`) | **Byte-identical.** The convention never justified it. |

So the convention survives in the two cases that carry it and was vacuous in the one deleted.
The merge erases no distinction.

All three former readers are Channels-path rows for which `_LOGOUT_Q` is the right document:
`:2808` and `:2830` post it through `_ch_post` (Channels HTTP round trip, and the anonymous
residue flush), `:2889` sends it through `_ws_run` on a real WebSocket communicator. All three
assert the same `logout { ok errors }` envelope `_LOGOUT_Q` selects. The transports differ; the
document does not — which is what Worker 2's replacement comment at `:2511-2512` now says, and
it sits at the head of the `Logout durable and fail-closed on every supported transport`
section (`:2498-2907`), which **contains all three readers**, so no reader is left
cross-referencing a comment it is not under.

### High:

None.

### Medium:

None.

### Low:

#### L1 — the `_LOGOUT_Q` reader tally is off by one in both the ruling and the build report

`### Ruling 2` records `_LOGOUT_Q` at **11** readers and the build report's before/after table
carries `11` -> `14`. Re-derived from the AST (Load-context `Name` nodes only, so the
definition and the new `:2511` comment mention are excluded): **12** before, **15** after.

```shell
$ grep -c '_LOGOUT_Q' tests/auth/test_mutations.py            -> 17   (matching LINES)
$ python -c '... ast Name/Load count ...'                     -> 15   (readers)
```

The gap is the `grep`-lines-versus-occurrences trap [`BUILD.md`][build-md] `## Claims are proven
mechanically` names explicitly. **Low, not Medium:** the number is a supporting tally whose only
job was to establish "live duplication, not dead code", and that conclusion is identical at 12.
Nothing downstream reads the figure. **Recommended:** correct the two figures if the artifact is
revised for any other reason; not worth a re-loop on its own. Recorded rather than waved through
because a stated count that is off by one reads as measured to every later pass.

#### L2 — row 1 now declares its subject INSIDE the `pytest.raises` block; row 2 does not

`:1251-1253`:

```python
def test_derive_register_fields_rejects_privilege_fields():
    """A custom model cannot turn ``is_staff`` into public registration input."""
    with pytest.raises(ConfigurationError, match=_PROTECTED_FIELD_REJECT):
        derive_register_fields(_privilege_required_user())
```

Before the consolidation the model was declared above the `with`; now the factory call sits
inside it, so the context manager covers setup as well as the call under test. Its sibling
`::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call` (`:1265-1270`)
keeps the two-statement shape. The risk is small — `_PROTECTED_FIELD_REJECT` is specific enough
that nothing a Django model declaration can raise would satisfy it, and `_unique_app_label()`
rules out a re-registration error — so this is clarity, not a live hole. **Recommended:**
`model = _privilege_required_user()` on its own line, matching the sibling row, so the two
consolidated rows read the same way and the `raises` block scopes to the call it names.

#### L3 — garbled clause in the factory docstring

`:1210`: "each call needs its own ``_unique_app_label()`` so Django's app registry does not
re-register warn". A word is missing; as written the clause does not parse. **Recommended:**
"so Django's app registry does not warn about a re-registered model". Docstring only, not
load-bearing.

### DRY findings

- **The three extractions are correct DRY, and each is the most readable reusable shape rather
  than the most abstract.** `_PROTECTED_FIELD_REJECT` is a named constant for a repeated literal
  — the exact remedy [`BUILD.md`][build-md] `## Severity definitions` puts at Medium when it is
  *missing*. `_privilege_required_user()` had to be a factory, not a shared class, and the
  reason is in its docstring at the site where someone would try to flatten it.
  `_assert_sessionless_configuration_error` takes the `ExecutionResult`, not the message, which
  keeps the `isinstance` check — the half that carries the contract — inside the helper instead
  of pushing it back to both call sites.
- **Existence challenge, raised on all three.** All three should exist; none is an indirection
  layer. `_PROTECTED_FIELD_REJECT`: delete it and a reword of the production message is a
  two-site sweep in a 3,159-line file, with a silent-pass failure mode (a regex that no longer
  matches its tail still matches its prefix). `_privilege_required_user()`: delete it and 18
  lines of byte-identical model declaration come back; its two callers are real and its body
  cannot be shared as a class. `_assert_sessionless_configuration_error`: delete it and the
  `TG-0` distinguishing set is restated twice, which is how a later editor weakens one copy and
  not the other — the precise defect `TG-0` was dispatched to remove. A two-reader constant and
  a two-caller helper are the floor for extraction, not the ceiling, and I am recording the
  answer rather than assuming it. **No escalation to the maintainer is owed:** nothing here is
  a contract-level call.
- **No fail-open shape in any of the three.** `_assert_sessionless_configuration_error` uses an
  explicit `is not None` rather than a truthiness test (an empty `errors` list would reach
  `res.errors[0]` and raise loudly, not pass), has no `try`/`except` around any check, and no
  `getattr` default. `_privilege_required_user()` takes no argument and supplies no default.
  `_PROTECTED_FIELD_REJECT` is a literal. Nothing in the diff computes an input to a limit, a
  size, or a permission decision.
- **Residual, accepted:** the "a bare ``session`` substring distinguishes nothing" rationale
  now appears in both the helper docstring (`:925-928`) and the login row's docstring
  (`:944-946`), near-verbatim. Worker 2 recorded the reason for leaving the row docstrings
  alone (churn in a file three prior passes pinned text in), and I accept it — the two
  statements are about different things (why the helper asserts what it asserts; why the row
  exists), and collapsing them would strand the row's own justification. Recorded so the
  absence of a change is a decision.
- **Executable-literal census, after** (`scripts/review_inspect.py tests/auth/test_mutations.py
  --output-dir docs/shadow`, run by me; Worker 2 recorded no helper run this pass). The three
  literals the loop was dispatched to collapse are each at **1x** now:
  `SessionMiddleware` 1x, `AuthMiddlewareStack` 1x,
  `mutation{ logout{ ok errors{ field } } }` 1x — against Slice 6's recorded `2x` for the
  middleware pair. No new repeated literal was introduced by the extractions; the overview's
  repeat list is the file's pre-existing fixture vocabulary (`username` 30x, `password` 21x,
  `pw-9x-strong` 11x).
- **No cross-cohort duplication check is owed.** This loop ran one cohort over one file.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**: `__all__` and the re-export
list are unchanged. This pass touches one test file and adds no public export.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### Confirming the fence held

- `tests/auth/_helpers.py` and `tests/auth/conftest.py` — `git diff --stat` against HEAD is
  empty for both, and both carry an mtime of `2026-07-20`, months before this cycle. Neither
  was edited; Worker 2 also states neither was read, and nothing in the diff could have come
  from either.
- **No production source changed by this pass.**
  `django_strawberry_framework/auth/mutations.py` is dirty against HEAD from Slice 6 but is
  **executable-token identical to HEAD** (AST compared with docstrings stripped), so Slice 6's
  edits to it are comment/docstring-only and this pass added none; its sha256 after my two
  proofs equals the pre-mutation reference in both proof records.
- **Nothing outside `tests/auth/test_mutations.py`.** Files with an mtime after the pass began
  (`03:00`) are: `tests/auth/test_mutations.py` (this pass), `docs/builder/bld-040-integration.md`
  (this build report and this review), `django_strawberry_framework/auth/mutations.py` (the
  mutate-and-restore cycles, proved byte-restored), the two gitignored worker-memory files, and
  `docs/builder/build-040-auth_mutations-0_0_13.md` (Worker 0's slice log, not this pass).
  Everything else in `git status --short` is Slice 6's or the concurrent `spec-050` session's,
  matching Worker 2's `### Working-tree note`. **Nothing was reverted, checked out, stashed or
  tidied** ([`AGENTS.md`][agents] rule 34); no `git checkout` / `stash` / `restore` / `worktree`
  ran in this pass.

### What looks solid

- The three consolidations are exactly what `### Ruling 2` dispatched, and DRY-3 — the one item
  the ruling left to the builder's judgement — was taken on a ground that survives checking at
  source rather than on preference.
- Worker 2's `### Notes for Worker 3` names the trap in its own instrument and hands over the
  control that detects it. That is what let me reproduce the failure mode (`-q` -> 0 lines)
  instead of discovering it the expensive way.
- The factory docstring puts the "the class name is load-bearing" warning at the exact site
  where a future rename would be attempted, rather than beside the regex that depends on it.
- Both DRY-1 rows keep their own docstrings and their own subjects; the consolidation is of
  setup and assertion *material*, never of what each row pins.
- Focused runs reproduce the expected figures: `uv run pytest tests/auth/ --no-cov` -> **195
  passed**; `uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov` -> **21
  passed**. Read-only lint, scoped to the one file: `ruff format --check` -> `1 file already
  formatted`; `ruff check` -> `All checks passed!`. No `--cov*` flag anywhere in this pass.

### Temp test verification

- No temp test was needed: every question this review had to settle was answerable by a
  mechanical comparison (AST identity, an executable-literal census, a collect-only set with a
  control) or by the two failability re-runs, which are stronger evidence than a new row would
  have been.
- Files written under `docs/builder/temp-tests/040-integration/`: `w3-proofs.json` (my own copy
  of the manifest — Worker 2's `proofs.json` and `proof-report.md` left untouched) and
  `w3-proof-report.md` (the tool's report for my run). Both gitignored; disposition: cycle
  scratch, cleared with the cycle.
- Scratch outside the repo (HEAD copies, AST id lists, the proof scratch root) is in the
  session scratchpad, not in the tree.

### Notes for Worker 1 (spec reconciliation)

- No spec gap, conflict or unstated assumption surfaced. This pass touches one test file; the
  spec was read read-only.
- The three Low findings above are all inside `tests/auth/test_mutations.py` and none blocks
  acceptance. L2 and L3 are one-line edits a re-loop could take cheaply if one happens for
  another reason; L1 is an artifact-prose correction, not a code change.
- One item for the record wherever the cycle's dispositions land: **DRY-3 was taken, not
  declined**, and the ground is a finding — the `_CH_` prefix marks a different GraphQL
  document in the two cases that survive and marked nothing in the one deleted. Verified at
  source by this review, not accepted from the build report.

### Review outcome

`review-accepted`. No High and no Medium finding. Three Low findings, each recorded with a
recommended change and none blocking: L1 an off-by-one tally in artifact prose, L2 a
`pytest.raises` block that now scopes over its own setup in one of two sibling rows, L3 a
garbled docstring clause. No assertion weakened — proved by the `::_transport_prologue` mutant
still failing the same two rows, by the byte-identity of `_PROTECTED_FIELD_REJECT` against
HEAD's regex, and by the AST identity of the factory's model body against HEAD's. Node ids
unchanged, derived independently with a control that produced an empty set under the wrong
flag. Both mandatory-floor boundaries in this diff's blast radius re-run at the recorded scope;
both sets match Worker 2's and Slice 6's id for id. The fence held.


---

## Final verification (Worker 1)

Second run of the cross-slice integration pass, after the consolidation loop
`### Ruling 2` dispatched. The tree it grades is the consolidated one: Worker 2's
three extractions in `tests/auth/test_mutations.py`, Worker 3's review, and the ten
spec edits this artifact's first half made. No prior entry in this artifact was
edited ([`ARTIFACT.md`][artifact-md]); everything below is new text.

Spec status-line re-verification, run first as every Worker 1 spawn owes: the spec
opens `Shipped in 0.0.13 (card DONE-040-0.0.13)` and the companion's lead-in names
the spec by its live path. Neither is falsified by the loop. **No status-line edit
owed, and no spec or companion edit is owed by this pass** — the loop touched one
test file and no spec surface, which the sweeps below re-derive rather than accept
from Worker 2's and Worker 3's `### Notes for Worker 1`.

---

### 1. Disposition of Worker 3's three Low findings

#### L1 — the `_LOGOUT_Q` reader tally. Upheld, corrected here, and its stated cause corrected too

**The figure recorded in `### Ruling 2` and in the `### Build report (Worker 2)`
before/after table is `11` -> `14`. It is wrong. The true figure is `12` -> `15`.**
Both numbers are stated here because a later reader may not edit either prior entry
and must not be left choosing between them.

Re-derived by me, two instruments, neither of them a line count:

```shell
$ grep -o '_LOGOUT_Q' tests/auth/test_mutations.py | wc -l     -> 17   (occurrences)
$ grep -c  '_LOGOUT_Q' tests/auth/test_mutations.py            -> 17   (matching lines)
$ python - <<'PY'   # ast.Name in Load context only
   readers = 15   at 584 594 602 685 846 856 894 973 1084 1181 2572 2585 2808 2830 2889
   stores  =  1   at 300
PY
```

17 occurrences = 15 readers + the definition (`:300`) + the section header comment
Worker 2 added (`:2511`, a mention, not a read). **15 readers after.** The loop
repointed exactly three former `_CH_LOGOUT` readers (`:2808`, `:2830`, `:2889`), so
**12 before**.

**Worker 3's number is right and its stated mechanism is wrong, so the mechanism is
corrected here as well.** L1 attributes the gap to "the `grep`-lines-versus-occurrences
trap". That trap is not what happened, and this file cannot exhibit it: the maximum
occurrences of `_LOGOUT_Q` on any one line is **1**, at HEAD and now, so a line census
and an occurrence census are numerically identical here (both 17). The `17` -> `15`
delta Worker 3 displays is the definition plus a comment mention — not two occurrences
sharing a line.

The real cause is a **wrong population**, which is the `START.md` "count right in every
digit, wrong in SUBJECT" shape rather than the grep-lines shape:

```shell
$ git show HEAD:tests/auth/test_mutations.py > <scratch outside repo>/test_mutations.py
$ python - # same AST census over that file
   HEAD _LOGOUT_Q readers = 11 ;  HEAD _CH_LOGOUT readers = 3
```

**`11` is the count at HEAD.** Slice 6 added one `_LOGOUT_Q` reader before the loop ran
— `::test_sessionless_logout_raises_the_configuration_error_naming_both_middlewares`
(`:973`), one of the two rows that replaced HEAD's single
`::test_sessionless_request_surfaces_djangos_own_error` under `TG-0`. So `11` describes
the pre-Slice-6 tree while the sentence carrying it describes the tree the loop was
about to edit. In a cycle whose whole subject is a spec measured against the wrong
vintage of its own tree, that is the cycle's own defect class turning up in its
instrumentation.

Grade unchanged at **Low**, on Worker 3's own ground: the tally's only job was to
establish "live duplication, not dead code", and that conclusion is identical at 11, 12
or 15. Nothing downstream reads the figure. It is discharged here rather than routed —
correcting artifact prose is Worker 1's work and needs no builder.

#### L2 — the factory call inside `pytest.raises`. Routed to a Worker 2 pass

`tests/auth/test_mutations.py::test_derive_register_fields_rejects_privilege_fields`
calls `_privilege_required_user()` inside its `pytest.raises` block; its sibling
`::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call`
declares its subject on its own line first.

**Does the placement change what the row proves?** Partly, and the honest answer is
narrower than "no". A failure *in the factory* would satisfy the assertion **if** it
raised a `ConfigurationError` whose message matched `_PROTECTED_FIELD_REJECT`. Checked
rather than asserted: the factory's only non-declarative call is
`::_unique_app_label`, whose body is `return f"test_auth_mutations__{next(_app_label_counter)}"`
— it cannot raise `ConfigurationError`, and a Django model-declaration failure raises
`ImproperlyConfigured` / `RuntimeError`, which fails the `isinstance` half of
`pytest.raises` and surfaces as a failing row, not a passing one. So there is **no live
hole today**, exactly as Worker 3 graded it.

That is a statement about today's factory body, not about the row. What the shape costs
is that the row stops being able to tell a factory failure from the rejection it names,
and the guarantee that it cannot rests on a helper someone else may change. Its sibling
row, written in the same pass for the same contract, already carries the shape that does
not rest on anything.

**Routed, not accepted, and the ground is ownership rather than severity.** The
placement is not pre-existing: the consolidation loop created it when the inline model
body became a factory call. A defect this build introduced is this build's to fix
in-loop ([`BUILD.md`][build-md] `### Test staleness a focused run cannot see`;
[`AGENTS.md`][agents] on never deferring the real fix), and it is a one-line edit in a
file this cycle owns.

#### L3 — the garbled factory docstring clause. Routed to the same pass

`tests/auth/test_mutations.py::_privilege_required_user`'s docstring reads "so Django's
app registry does not re-register warn". The clause does not parse. It is shipped text,
written by this build's own consolidation loop, and it sits in the docstring whose job
is to stop a future editor flattening the factory into a shared class — the one sentence
in the extraction that exists to be read before a change. A garbled sentence there
degrades the thing it was written to protect.

**Routed** on the same ground as L2. Grade stays **Low**; the routing is about who owns
the defect, not about how bad it is.

#### The routed pass, pinned verbatim

Two one-line edits, both in `tests/auth/test_mutations.py`, both cohort B's file. The
replacement text is given character-exact so the builder has nothing to re-invent —
that is what made the Slice 6 re-loop land character-identical, and it is the only
reason a Low is worth a loop at all.

**Edit 1 (L3).** In `::_privilege_required_user`'s docstring, replace exactly:

```text
    ``_unique_app_label()`` so Django's app registry does not re-register warn, and
```

with exactly:

```text
    ``_unique_app_label()`` so Django's app registry does not warn about a
    re-registered model, and
```

**Edit 2 (L2).** In `::test_derive_register_fields_rejects_privilege_fields`, replace
exactly:

```python
    with pytest.raises(ConfigurationError, match=_PROTECTED_FIELD_REJECT):
        derive_register_fields(_privilege_required_user())
```

with exactly:

```python
    model = _privilege_required_user()
    with pytest.raises(ConfigurationError, match=_PROTECTED_FIELD_REJECT):
        derive_register_fields(model)
```

**Fence and obligations for that pass.** `tests/auth/test_mutations.py` only; no
production change; no assertion weakened; no node id added, removed or renamed. Neither
edit can move a failing set — Edit 1 is a docstring, Edit 2 moves one statement out of a
context manager — but "cannot" is a prediction, so the pass re-runs
`scripts/prove_failability.py` entry **3**
(`django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS`, whose two
failing rows are exactly the two DRY-1 rows, one of them the row Edit 2 touches) at the
recorded scope `tests/auth/`, and confirms the collected node-id set with
`--collect-only -q -q` (**not** a single `-q`; `pytest.ini`'s `addopts` carries `-v`, so
one `-q` nets to verbosity 0 and prints no `::`, and two empty files diff clean).
Entries 1, 2 and 4 are left alone. Ruff scoped to the one file, never `.`; no `--cov*`
flag.

---

### 2. The integration checks, re-run against the consolidated tree

#### 2a. No new duplication, inconsistent naming, or misplaced responsibility

The loop added three shapes, not two — a constant and two callables — and deleted one
constant. Graded individually:

| Shape | Duplication | Naming | Responsibility |
|---|---|---|---|
| `_PROTECTED_FIELD_REJECT` | The literal it mirrors, `django_strawberry_framework/auth/mutations.py #"cannot auto-expose protected user field(s)"`, has **1** production site and now **1** test site. A test regex mirroring a production message is the pinning, not a duplicate of it | file-local `_UPPER` constant, the file's own convention | sits with its two readers in the register-rider section |
| `_privilege_required_user` | `rg -c` over `tests/`, `examples/`, `django_strawberry_framework/`: **1 file**. No sibling anywhere | reads as the file's other private factories (`_login_logout_schema`, `_auth_free_subprocess`); deliberately **not** `_declare_*`, which in this file means "mutates the process-global type registry" — this one declares a plain Django model | local to the two rows that read it |
| `_assert_sessionless_configuration_error` | **1 file**. The only other `AuthMiddlewareStack` assertions in the tree are `tests/test_routers.py`'s layer-order rows, a different contract | sits beside `::_assert_login_fully_compensated`, the file's existing `_assert_*` helper, and takes the same shape (the result object, not the message) | local |
| `_CH_LOGOUT` (deleted) | **0** occurrences remain in any `.py`; all surviving mentions are per-cycle `bld-040-*.md` prose | — | — |

No cross-file near-copy was introduced, and no responsibility moved between modules: the
three production files this cycle touched are **executable-token identical to HEAD**
(§3).

#### 2b. The spec still matches the code; no citation points at anything the loop moved

Three sweeps, each with the population stated.

**The spec and companion cite no symbol the loop touched.** Sweeping both files for
`test_mutations.py` / `test_queries.py` / `_CH_LOGOUT` / `_LOGOUT_Q` /
`PrivilegeRequiredUser` / `_privilege_required_user` / `_PROTECTED_FIELD_REJECT` /
`_assert_sessionless_*`: six hits, all bare **file-path** mentions in `## Slice checklist`
/ `## Test plan` prose, **zero** naming a symbol. The spec's entire `::test_` citation
population is **two distinct names**, `::test_all_four_failure_classes_share_one_byte_identical_envelope`
and `::test_version`; both resolve at source (`tests/auth/test_mutations.py:2434`,
`tests/base/test_init.py:18`) and neither was touched. **The consolidation renamed
nothing the spec cites.**

**`path::Symbol` citations, whole-tree, by the gate:**

```shell
$ uv run python scripts/check_citations.py --check
OK: 979 citations resolve (814 in 442 .py files, 165 in KANBAN.md).   (exit 0)
```

The same **979** the first integration run and Slice 6 both recorded, so no citation
moved across the loop. The figure is whole-tree and therefore includes the concurrent
`spec-050` session's dirty `.py` files; it is green, so nothing in it is attributable to
either cycle. Note what it does **not** read: `docs/` markdown is outside its corpus
(`814 .py` + `165 KANBAN.md` accounts for all 979), which is the whole reason for the
next sweep.

**`#"substring"` citations, swept separately because no gate sees them.** The tree-wide
population of `#"` citations is **1,650**. Filtered to those whose target is one of this
cycle's six touched files (pattern `<path>(::Symbol)? #"`), every hit lands in a
per-cycle `bld-040-*.md` artifact — none in the spec, the companion, a standing doc,
`KANBAN.md`, or any `.py`. Instrument controlled: the same pattern shape against
`utils/querysets.py` returns hits in six files, so it matches this corpus. Of the hits,
the two that quote text still under contract both resolve —
`auth/mutations.py::_transport_prologue #"session = sessions.require_session(request, transport)"`
(`grep -c` -> 1) and
`::test_register_factory_recache_and_reregister_on_every_call #"rider.__name__ == "Register""`.
**None targets a region the loop edited** (`_CH_LOGOUT`'s definition, the two model
bodies, the two regexes, the two assertion blocks).

**Stranded names, swept by hand.** `_CH_LOGOUT`: 16 hits, all `bld-040-*.md` / the build
plan, all dated records of the finding, and [`ARTIFACT.md`][artifact-md] forbids editing
a prior entry. `::test_sessionless_request_surfaces_djangos_own_error` (the `TG-0`
rename): 11 hits, same populations, same disposition. Control: the surviving name
`::test_sessionless_logout_raises_the_configuration_error_naming_both_middlewares`
returns hits in three files including the source, so the instrument reads this corpus.

#### 2c. The divergence inventory still holds, and the ten edits introduced no sixth

[`BUILD.md`][build-md]'s rule is that a reconciliation pass owes the divergence
inventory, not the consistency of its own discharging text. Re-run whitespace-normalized
over the whole file, since a per-line `rg` is what nearly hid D1 the first time:

| Divergence | Re-check | Result |
|---|---|---|
| **D1** | `"structurally unreachable"` normalized census, spec | **1** (was 3) |
| | `"structurally absent"`, `"safe by construction"`, `"privilege columns structurally"` | **0 / 0 / 0** |
| | the protected set, every enumeration | **3 enumerations, all five-membered and identical in membership**; `_REGISTER_PROTECTED_FIELDS` at source is exactly `groups / is_active / is_staff / is_superuser / user_permissions` |
| **D2** | `"is imported from its public path"` | **0** |
| | `"neither imports nor re-spells"` | **2** — Decision 10 and the `D18 / D19` obligation, now one vocabulary |
| | settled against source | `rg SyncMisuseError django_strawberry_framework/auth/` -> **2, both docstrings**; `import.*SyncMisuseError` -> **0** |
| **D3** | `### Error shapes` third refusal row | present |
| **D4** | `DONE-040-0.0.13` / `WIP-ALPHA-040-0.0.13` | **5 / 4** — the four are the recorded `### Decided non-edits` |
| **D5** | `"Slice 3 flips"`, `"not yet reserve"` | **0 / 0** |
| self-history | `Revision `, `as of `, `previously`, `amendment`, `review round`, `retract`, `as an earlier draft had it` | **0** on all seven |

**The one surviving `structurally unreachable` is not a sixth divergence, and it was run
down to source rather than counted.** It sits inside Decision 6's corrected two-layer
statement — "*for the stock user model* the narrowed set simply never names
`is_staff` / `is_superuser` / `is_active` / `groups` / `user_permissions`, so privilege
escalation is structurally unreachable" — immediately followed by the custom-model layer.
The companion's retraction is against the **unqualified** claim ("unreachable by
structure alone and needs no policy check"); the scoped form with both layers is the
contract Slices 3 and 6 converged on and the one Slice 6 pinned into shipped source. A
sweep that deleted this occurrence too would have retired the true sentence along with
the false ones.

**Retractions re-swept.** The companion now records **16** `**No longer claims:**`
bullets, up from the 12 the first run swept — this pass's own three Decision additions
plus the new `## Goals` sub-section. All 16 re-swept against the spec: the three new ones
are the D1 / D4 / self-history retirements just re-verified above at 0, and the original
twelve are unchanged. **No spec sentence contradicts any retraction.**

**No sixth divergence from the ten edits.** The edits touched `## Goals` 4, Decisions 1 /
8 ×2 / 10, `### Error shapes`, `## Key glossary references` ×2, "Project conventions to
follow", `## Definition of done` 4. Each is a member of an already-enumerated contract
(C1, C4, C2, C3, C5), and the contracts they belong to are the ones re-checked row by row
above. The seven agreeing contracts (C6-C12) were not re-walked: no edit touched a home
of any of them, which is checkable from the edit table rather than asserted.

#### 2d. Staged-anchor sweep, with its control

```shell
$ rg -n 'TODO\(spec-040' . --glob '!KANBAN.md' --glob '!KANBAN.html' --glob '!BACKLOG.md'
docs/builder/bld-040-slice-4-audit_obligations_edges_tests.md:357   (prose: the row quoting the rule)
docs/SPECS/spec-040-auth_mutations-0_0_13.md:1887                   (prose: the rule itself)
docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md:1202    (prose: an anchor's discharge)
-> 3

$ rg -n 'TODO-(ALPHA|BETA|STABLE)-040' . --glob '!KANBAN.md' --glob '!KANBAN.html' --glob '!BACKLOG.md'
docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md:1409    (prose)
docs/SPECS/appx/spec-038-form_mutations-0_0_12-rationale.md:307     (prose, another spec's companion)
-> 2
```

**Population 5, all Markdown prose, zero staged anchors.** The three line numbers inside
the spec and companion moved since the first run (`1881`->`1887`, `1180`->`1202`,
`1371`->`1409`) because this pass's own ten edits shifted them — the hits are the same
three sites, which is why the sweep is reported by content and not by line.

**Restricted to source, the direct measurement rather than an inference:**

```shell
$ rg -n --glob '*.py' 'TODO\(spec-040|TODO-(ALPHA|BETA|STABLE)-040' .
(no output)  -> 0 staged anchors in any .py in the tree
```

**Controls, same invocation shape, proving the patterns match this corpus rather than
failing open:** `TODO\(spec-` -> **152**, `TODO-(ALPHA|BETA|STABLE)-` -> **471**. Every
glob quoted; no shell variable anywhere in the sweep (`START.md` `## Instruments that
lie`, zsh word-splitting).

---

### 3. The failability records survived the consolidation

**Complete: four boundaries, four records, every field [`BUILD.md`][build-md]
`### What gets recorded` requires.** Slice 6's `### Failability proofs` carries, per
entry, the symbol-qualified boundary, the exact mutation, the scope as run, the failing
node ids **listed**, collection/setup errors (**0** on all four), the pre-mutation
baseline of that same scope (`195 passed`, exit 0, so 0 rows differenced out), and the
revert proved by `filecmp.cmp(shallow=False)` plus SHA-256. All four fail **2** rows —
above the 0-or-1 weakly-pinned floor, so no `why 0` judgement is owed by any of them.

**Four independent measurements of the two boundaries in this diff's blast radius, all
matching id for id:** Slice 6 entries 1 and 3, Worker 2's re-run this loop, and Worker
3's independent re-run from its own manifest. `::_transport_prologue` -> the two
`test_sessionless_{login,logout}_raises_the_configuration_error_naming_both_middlewares`
rows; `::_REGISTER_PROTECTED_FIELDS` -> `::test_derive_register_fields_rejects_privilege_fields`
and `::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call`.
Entries 2 (`types/finalizer.py::finalize_django_types`) and 4
(`types/resolvers.py::_check_n1`) were untouched by this diff and their rows' node ids
are covered by the collect-only set comparison.

**That the sets match is the load-bearing check, not a formality.** An extraction that
quietly stopped exercising a boundary would still collect 116 ids and still pass green;
it would show only as a shrunk failing set. Both sets held at 2.

**No live mutation survives anywhere.** Confirmed by me, not read from a report:

```shell
$ git diff --stat -- django_strawberry_framework/
  auth/mutations.py 15 +-   mutations/resolvers.py 12 +-   mutations/sets.py 14 +-
  list_field.py / orders/sets.py / utils/querysets.py  <- the concurrent spec-050 session's
$ git diff --stat -- django_strawberry_framework/types/          -> empty
$ git diff --stat -- django_strawberry_framework/__init__.py     -> empty
$ find . -name 'ACTIVE-MUTATION.json'                            -> nothing
$ grep -c '    session = sessions.require_session(request, transport)' …auth/mutations.py -> 1
$ grep -c '_REGISTER_PROTECTED_FIELDS = frozenset($'              …auth/mutations.py -> 1
$ grep -c 'session = getattr(request, "session", None)'           …auth/mutations.py -> 0
$ grep -c '_REGISTER_PROTECTED_FIELDS = frozenset()'              …auth/mutations.py -> 0
```

Both anchors back to exactly 1 and both mutant spellings absent — the negative and the
positive half, because an anchor at 1 alone would also read clean if a *different*
mutation were live.

**`auth/mutations.py` executable-token identical to HEAD**, and so are the other two
production files this cycle touched. Run by me with docstrings stripped and ASTs
compared, with a positive control so the instrument is known to be able to report a
difference:

```text
django_strawberry_framework/auth/mutations.py        AST(docstrings stripped) HEAD == worktree -> True
django_strawberry_framework/mutations/resolvers.py   -> True
django_strawberry_framework/mutations/sets.py        -> True
CONTROL (one executable token appended to the HEAD text)  -> False
```

So every restore is complete and Slice 6's production edits remain comment- and
docstring-only, which is the inverse proof those comment-only findings owe in place of a
failability proof.

---

### 4. What the final gate inherits — `### Deferred work catalog`

The first run listed eight. All eight re-confirmed against the tree; **two carried
figures that were wrong and are corrected here**; one entry is added by the
consolidation loop. Each entry carries its source artifact section, the spec line
licensing it where one exists, and a one-line description, as
[`BUILD.md`][build-md] `## Final test-run gate` requires of a gate-usable catalog.

1. **The subprocess-isolation idiom — `subprocess.run([sys.executable, "-c", …])`,
   spelled inline in eight test files.** Source: Slice 6 plan
   `### Out-of-scope observations`; Slice 6 W1 pass-2 item 4; `### Ruling 3` of this
   artifact. No licensing spec line — it is out-of-spec DRY. **Correction: the recorded
   "four-way" figure is an undercount.** AST census over `tests/` and `examples/` for
   `subprocess.run` whose first argument mentions `sys.executable`: **7 files, 7 call
   sites**, plus `tests/base/test_init.py`, which builds the list into a `cmd` variable
   first and so is invisible to that census (found by grep) — **8 files, 8 call sites**:
   `tests/auth/test_mutations.py`, `tests/auth/test_sessions.py`, `tests/base/test_init.py`,
   `tests/filters/test_finalizer.py`, `tests/filters/test_sets.py`,
   `tests/orders/test_inputs.py`, `tests/rest_framework/test_soft_dependency.py`,
   `tests/test_scalars.py`. The correction strengthens the deferral rather than weakening
   it: at eight files across five directories the shared home is unambiguously a
   repo-level `tests/` decision (which conftest; what the contract is for a
   soft-dependency probe versus an import-isolation probe versus a warnings probe, since
   `tests/test_scalars.py` passes `-W error::DeprecationWarning`), which belongs to a DRY
   cycle over the whole test tree. This build already collapsed the two copies inside its
   own file into `::_auth_free_subprocess`.
2. **`docs/GLOSSARY.md`'s auth-mutations entry repeats the exact defect this cycle fixed
   in the spec.** Source: Slice 3 `### Notes for Worker 1` F1; Slice 4 F4; **D1** of this
   artifact. Re-read at source this pass — `docs/GLOSSARY.md:329` states "the privilege
   columns (`is_staff` / `is_superuser` / `groups` / `user_permissions`) are unreachable
   by construction": the retired absolute framing **and** the four-of-five enumeration,
   `is_active` missing. Now known to be a two-part fix identical to spec edit 1, applied
   to the `GlossaryTerm` body via the ORM then `scripts/build_glossary_md.py` — the
   glossary is DB-backed and outside this cycle's scope fence, and the file is currently
   dirty from the concurrent `spec-050` session. **For the maintainer.**
3. **`spec-042 Revision N` citations in `tests/middleware/test_debug_toolbar.py` — 5
   occurrences** (`:21`, `:111`, `:475`, `:509`, `:523`), re-measured this pass. Source:
   Slice 6 plan `### Out-of-scope observations`. Same defect class as `F2` (a label
   vocabulary a rationale extraction stranded), a different spec's population and a
   different owner. **For the maintainer.**
4. **Bug-hunt round provenance in `tests/auth/test_sessions.py` — 2 occurrences, not 1.**
   Source: same. **Correction:** the first run recorded 1 hit (`:720`, "Revision guards:
   … (hunt 0_0_14 rev)"); an occurrence census of the distinctive token `hunt 0_0_14`
   returns **2** — `:465` "Exception containment: hostile scope / session / lock (hunt
   0_0_14)" is the second. `START.md` `## Style Rio cares about` bans round provenance in
   code; the file was on no cohort's writable list and cites no spec, so both sit outside
   `F2`'s population. **For the maintainer.** This is the `START.md` "partial claim fix =
   dominant residual defect" shape: a one-site figure for a two-site population would
   have closed the finding with half of it live.
5. **`Revision N P<n>` citations in `examples/fakeshop/test_query/test_library_api.py` —
   5 occurrences**, re-measured. Source: Slice 6 plan `### Out-of-scope observations`.
   That file belongs to the **concurrently active `spec-050` cycle** and must not be
   touched by this one (`AGENTS.md` rule 34). **For the maintainer / that cycle.**
6. **`docs/builder/bld-040-slice-6-code_remediation.md:888` carries
   `scripts/prove_failability.py`'s own `<fill in …>` explanatory line** inside a prior
   `### Failability proofs` block. Source: Slice 6 W1 pass-1 and pass-2. There are no
   unfilled placeholders; [`ARTIFACT.md`][artifact-md] forbids editing a prior entry, so
   it stays. Cosmetic; **for the maintainer's awareness only.**
7. **`## Definition of done` item 6's coverage clause is structurally unverifiable by any
   worker.** Source: Slice 4 `### Spec changes made`, the one un-ticked box of that slice.
   Licensing line: [`BUILD.md`][build-md] `## Coverage is the maintainer's gate, not a
   worker's tool`. Its other half (`D-N3`'s source comment) is **discharged** — by Slice
   6's pinned comment and by this artifact's companion edit marking the observation
   closed. **The coverage half is the maintainer's gate by construction.**
8. **The `_declare_group_type` / `_declare_user_type` per-file pairs are accepted, not
   deferred.** Source: `### Ruling 1`. Listed only so the gate does not re-open them. The
   condition that would change the answer is recorded with the ruling: a third caller, or
   a decision to widen `tests/auth/_helpers.py`'s stated "plain (non-fixture) helpers"
   contract to registry-mutating declarations. Re-verified at source this pass: neither
   `_helpers.py` nor `conftest.py` is dirty.
9. **NEW — two prior entries in this artifact carry the `_LOGOUT_Q` tally as `11` -> `14`;
   the correct figure is `12` -> `15`.** Source: `### Ruling 2`, the
   `### Build report (Worker 2)` before/after table, Worker 3's `L1`, and §1 of this
   section. Licensing line: [`ARTIFACT.md`][artifact-md] "never edit prior entries", which
   is why the correction lives here rather than at the two sites. Nothing downstream reads
   the figure, and the conclusion it supported ("live duplication, not dead code") is
   identical at either number. **Recorded so the gate does not have to adjudicate between
   the two sites**, and so a later reader takes the correction rather than the first
   figure it meets.

The `DRY-3` disposition is **not** a deferral and is recorded here instead so the gate
does not inherit it as open: `### Ruling 2` left the call to Worker 2, Worker 2 **took**
it, and Worker 3 verified the ground at source member by member (`_CH_LOGIN` genuinely
differs from `_LOGIN_Q`; `_CH_ME` has no twin; `_CH_LOGOUT` was byte-identical, so the
`_CH_` convention never justified it). Closed.

---

### Verification, this pass

Every figure above was measured as it was written.

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md
OK: 30 terms - all have glossary entries and at least one spec link.        (exit 0)

$ uv run python scripts/check_citations.py --check
OK: 979 citations resolve (814 in 442 .py files, 165 in KANBAN.md).         (exit 0)

$ uv run pytest tests/auth/ examples/fakeshop/test_query/test_auth_api.py --no-cov -q
216 passed in 9.19s
```

`check_citations.py` runs whole-tree and so covers the concurrent `spec-050` session's
dirty `.py` files as well as this cycle's. It is green, and it is the same **979** Slice
6 and the first integration run both recorded, so **nothing in it is attributable to
either cycle**. 216 = the 195 + 21 every pass since Slice 6 has recorded. No `--cov*`
flag anywhere; `--no-cov` because `pytest.ini` auto-applies `--cov`.

**Anchors and the markdown link convention**, verified with a slug function implementing
`START.md`'s GitHub rule, fenced blocks and code spans stripped first (double-backtick
spans and line-wrapped spans both handled — the two blind spots that produced the first
run's false alarms), never by eye:

| File | Headings | In-page uses | Unresolved | Ref labels used / defined | Undefined | Unused | Def paths missing | Ten group headers, in order |
|---|---|---|---|---|---|---|---|---|
| `docs/SPECS/spec-040-auth_mutations-0_0_13.md` | 34 | 165 | **0** | 96 / 96 | 0 | 0 | 0 | yes |
| `docs/SPECS/appx/…-rationale.md` | 66 | 77 | **0** | 60 / 60 | 0 | 0 | 0 | yes |
| `docs/builder/bld-040-integration.md` | 69 | 0 | **0** | 7 / 7 | 0 | 0 | 0 | yes |

Every definition path resolved on disk **from its own file's directory**, and every
definition carrying a cross-file anchor was resolved against the target file's real
headings — **0 bad**. Instrument controlled: a copy of the spec with one bogus label and
one bogus in-page anchor appended reports `undefined: ['no-such-label']` and
`unresolved: ['no-such-heading']`, so the zeros are measurements and not an instrument
that cannot fail.

**Pre-commit, over the one file this pass wrote**, path passed explicitly rather than
through a shell variable:

```shell
$ uvx pre-commit run --files docs/builder/bld-040-integration.md
kanban tracked path constants ................ Passed
source layout (py trailing commas + ascii-only; md link-def scaffold; ...) Passed
ruff format .................................. (no files to check) Skipped
ruff check ................................... (no files to check) Skipped
kanban anchors collision-free ................ Passed
citations resolve (AGENTS.md rule 27) ........ Passed
```

Run twice, **no rewrite on either run** — the `source-layout` hook, which owns the `.md`
link-definition scaffold, left the file byte-identical both times. The two `Skipped`
lines are genuine (this pass writes no `.py`) and are a fact rather than the zsh
word-splitting artifact, because the path was typed literally.

**Working-tree note (stop-and-report, no action taken).** `git status --short`, read at
the end of this pass rather than from a snapshot taken at its start, shows this pass's one
file plus the cycle's own dirty set and the concurrent `spec-050` session's
(`django_strawberry_framework/{list_field,orders/sets,utils/querysets}.py`,
`docs/GLOSSARY.md`, `docs/feedback.md`, `docs/spec-050-list_field_arguments-0_0_15.md`,
`docs/builder/bld-final.md`, `docs/builder/bld-slice-3-sql_and_unit_contracts.md`,
`examples/fakeshop/db.sqlite3`, `examples/fakeshop/test_query/test_list_field_api.py`,
`test_list_field_async_api.py`, `test_multi_db.py`, `tests/orders/test_sets.py`,
`tests/test_list_field.py`, `tests/utils/test_querysets.py`).

**That set is not the one this session opened with, which is why it is stated as measured
rather than carried.** Four entries dirty at session start —
`django_strawberry_framework/_strawberry_patches.py`,
`django_strawberry_framework/resource_policy.py`, `tests/test_graphql_core_patches.py`,
and an untracked `docs/builder/bld-003-final.md` — are clean now: the concurrent session
committed or discarded them mid-pass. Nothing of this cycle's moved. A baseline-dirty list
is a dated observation like any other, and reprinting the opening snapshot would have
published a false present-tense one. **Nothing was reverted, checked out,
stashed or tidied** ([`AGENTS.md`][agents] rule 34). No `git stash` / `checkout` /
`restore` / `worktree` ran in this pass; the one read-only HEAD reference
(`git show HEAD:tests/auth/test_mutations.py`, for L1's population attribution) went to a
scratch path outside the repository.

---

### Final status

`revision-needed`, for two pinned one-line edits in `tests/auth/test_mutations.py` and
nothing else.

Everything the pass was re-run to check is clean. The three shapes the consolidation
added introduce no duplication, no naming inconsistency and no misplaced responsibility;
the spec and its companion cite no symbol the loop touched and the loop renamed nothing
either cites; `check_citations.py` is green whole-tree at the unchanged **979** and the
ungated `#"substring"` population carries no citation into an edited region; the five
divergences stay closed, the sixteen retractions stay unsweepable against the spec, and
the ten edits introduced no sixth divergence; the staged-anchor sweep reads **5 prose
hits and 0 in source**, behind live controls; all four failability records are
field-complete at 2 rows each with four matching measurements of the two in this diff's
blast radius; no mutation is live and all three touched production files are
executable-token identical to HEAD.

What blocks `final-accepted` is narrow and is not a judgement about severity. Worker 3
graded L2 and L3 Low and non-blocking, and on severity it is right. **They are routed
because this build's own consolidation loop introduced both**, in a file this cycle
owns, and a defect the build creates is the build's to fix in-loop rather than hand
onward ([`AGENTS.md`][agents]; [`BUILD.md`][build-md] `### Test staleness a focused run
cannot see`). L1 needed no builder and is discharged above — with its stated **cause**
corrected as well as its figure, since "the grep-lines trap" is not what happened and a
later reader would otherwise inherit a wrong lesson along with a right number.

After that pass returns, this artifact needs a third Worker 1 close covering only the
two edits, entry 3's re-run, and the collected-node-id set.

---

## Build report (Worker 2, pass 2)

The routed pass of `### The routed pass, pinned verbatim`: two one-line edits in
`tests/auth/test_mutations.py` (L2 and L3), applied from the pinned replacement text
character-exact. No other file was opened - `tests/auth/_helpers.py` and
`tests/auth/conftest.py` were neither read nor edited, no production source was changed
permanently, and no node id was added, removed or renamed. No prior entry in this
artifact was edited ([`ARTIFACT.md`][artifact-md] `## Re-pass sections`); everything
below is new text at top level.

### Files touched

Grounded in `git status --short`, not memory.

- `tests/auth/test_mutations.py` - the two pinned edits below. Already dirty from Slice 6
  and from the consolidation loop before this pass; this pass adds to that same
  working-tree change.
- `docs/builder/bld-040-integration.md` - this build report appended, `Status:` set to
  `built`.
- `docs/builder/worker-memory/worker-2-040.md` - one appended memory entry (gitignored, so
  it does not appear in `git status`).
- `docs/builder/temp-tests/040-integration/{proofs-pass-2.json,proof-report-pass-2.md}` -
  this pass's own manifest and the tool's report, written as a **new** manifest rather
  than `--only` over the prior pass's, so the emitted block is a complete record and not
  a `PARTIAL RECORD` (gitignored).

`django_strawberry_framework/auth/mutations.py` was mutated **transiently** for the
failability re-run and restored inside this pass; it carries no net change from this
pass (`### Failability proofs`).

### Tests added or updated

No row added, no row removed, no row renamed; no assertion weakened. Two shape-only
edits, both applied verbatim from the pinned text:

- **Edit 2 (L2)** - `tests/auth/test_mutations.py::test_derive_register_fields_rejects_privilege_fields`
  now binds `model = _privilege_required_user()` on its own line and the `pytest.raises`
  block contains only `derive_register_fields(model)`. The row's subject and its
  `match=_PROTECTED_FIELD_REJECT` assertion are untouched; what changes is that a
  failure *inside the factory* can no longer be absorbed by the `raises` block, which is
  the shape its sibling
  `::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call`
  already carried.
- **Edit 1 (L3)** - `tests/auth/test_mutations.py::_privilege_required_user`'s docstring
  clause now reads "so Django's app registry does not warn about a re-registered model",
  replacing the ungrammatical "does not re-register warn". Docstring text only.

Both were applied as the **exact** pinned strings, including the pinned line break after
"re-registered model, and" and the pinned local name `model` (the sibling row spells its
own local `user_model`; re-wording either to match the other is the paraphrase class
`### The routed pass, pinned verbatim` exists to prevent, and my own memory file records
it as the defect shape from the Slice 6 re-loop). `ruff format` left the file unchanged,
so no reflow moved the pinned bytes.

### Validation run

```shell
$ uv run ruff format tests/auth/test_mutations.py
1 file left unchanged                                          # exit 0

$ uv run ruff check --fix tests/auth/test_mutations.py
All checks passed!                                             # exit 0
```

`git status --short` after both ruff invocations - classified in full, nothing reverted,
nothing tidied ([`AGENTS.md`][agents] rule 34):

| File(s) | Attribution |
|---|---|
| `tests/auth/test_mutations.py` | **this pass** (on top of Slice 6 + the consolidation loop) |
| `docs/builder/bld-040-integration.md` | **this pass** (untracked; this report + `Status:`) |
| `django_strawberry_framework/{auth/mutations,mutations/sets,mutations/resolvers}.py`, `tests/auth/test_queries.py`, `examples/fakeshop/test_query/test_auth_api.py`, `docs/SPECS/spec-040-*`, the untracked `bld-040-*` / `build-040-*` / `…-rationale.md` | this **cycle**, from earlier slices; not re-touched here |
| `django_strawberry_framework/{list_field,orders/sets,utils/querysets}.py`, `docs/GLOSSARY.md`, `docs/feedback.md`, `docs/spec-050-*`, `docs/builder/bld-final.md`, `docs/builder/bld-slice-3-sql_and_unit_contracts.md`, `examples/fakeshop/db.sqlite3`, `examples/fakeshop/test_query/test_list_field_api.py`, `test_list_field_async_api.py`, `test_multi_db.py`, `tests/orders/test_sets.py`, `tests/test_list_field.py`, `tests/utils/test_querysets.py` | the **concurrent `spec-050` session**. Untouched, unreverted, unstashed |

The concurrent set is not identical to the one `### Working-tree note` recorded earlier
in this artifact - `test_list_field_async_api.py` is dirty now and
`_strawberry_patches.py` / `tests/test_graphql_core_patches.py` are no longer - which is
that session's file set moving under a running pass, exactly as the dispatch warned. No
file of theirs was written by me.

Node ids, collected before and after the two edits - `-q -q`, never a single `-q`
([`BUILD.md`][build-md]; the trap is recorded in my memory file and was hit twice in this
cycle):

```shell
$ uv run pytest tests/auth/ --no-cov --collect-only -q -q -p no:cacheprovider \
      | grep '::' | sort > collect-{before,after}.ids     # run either side of the edits

before: 195 id lines (out of 197 raw output lines)
after:  195 id lines (out of 197 raw output lines)
$ diff collect-before.ids collect-after.ids   -> no output, exit 0   (SET IDENTICAL)
```

**The line count is the control that proves the instrument ran:** 195 non-empty id lines
on each side, not two empty files diffing clean. Second control, that the comparison can
fail: deleting one line from the "after" file makes the same `diff` exit **1**.

Focused tests, both as the dispatch specified, no `--cov*` flag anywhere:

```shell
$ uv run pytest tests/auth/ --no-cov                                   -> 195 passed in 4.56s
$ uv run pytest examples/fakeshop/test_query/test_auth_api.py --no-cov ->  21 passed in 8.64s
```

195 and 21 are the figures every pass of Slice 6 and the first integration run recorded;
this pass moved neither.

Pre-commit, over the three files this pass writes, every path passed **explicitly**:

```shell
$ uvx pre-commit run --files tests/auth/test_mutations.py \
      docs/builder/bld-040-integration.md \
      docs/builder/worker-memory/worker-2-040.md
kanban tracked path constants ................ Passed
source layout (py trailing commas + ascii-only; md link-def scaffold; ...) Passed
ruff format .................................. Passed
ruff check ................................... Passed
kanban anchors collision-free ................ Passed
citations resolve (AGENTS.md rule 27) ........ Passed
```

**Run twice, no rewrite on either run** - the `md5` of `tests/auth/test_mutations.py` and
of this artifact is identical before and after the second run, which is the evidence that
`source-layout` (the hook that rewrote on its first run in Slice 6) left both files alone
rather than the run being skipped. No `Skipped (no files to check)` line appears: the
`.py` and `.md` hooks each had real input.

### Failability proofs

**No new boundary introduced by this pass.** The entry below is the **re-run** of entry
3 that `### The routed pass, pinned verbatim` requires, because Edit 2 moves a statement
inside one of the two rows that entry's failing set names. Entries 1, 2 and 4 are
untouched by this diff and were not re-run. Manifest:
`docs/builder/temp-tests/040-integration/proofs-pass-2.json` (a complete one-entry
manifest, not `--only` over a prior one, so the emitted report is a full record).
Scratch root, outside the repository:
`/private/tmp/claude-501/…/scratchpad/failability-pass-2`.

- `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS` - mutation
  applied: `_REGISTER_PROTECTED_FIELDS = frozenset({"groups", "is_active", "is_staff",
  "is_superuser", "user_permissions"},)` -> `_REGISTER_PROTECTED_FIELDS = frozenset()`,
  so the intersection never matches and `::derive_register_fields` never raises; scope as
  run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE
  tests/auth/`; pre-mutation state of that scope: `195 passed` (pytest exit code 0), 0
  pre-existing failing rows differenced out; failing node ids:
  `tests/auth/test_mutations.py::test_derive_register_fields_rejects_privilege_fields`,
  `tests/auth/test_mutations.py::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call`;
  collection/setup errors: **0**; revert proved by byte-comparison:
  `filecmp.cmp(shallow=False) True; sha256 ad6a3f7efea49aab… == ad6a3f7efea49aab…` against
  the pre-mutation copy.

**Acceptance, against the unchanged rule.** 2 failing node ids (the `len()` of the list
above, not an asserted count), 0 collection/setup errors, mutant exit 1 and baseline exit
0 - and the **dispatched row is itself in the failing set**:
`::test_derive_register_fields_rejects_privilege_fields` is the row Edit 2 changed. Not
weakly pinned; no zero-row entry, so no **why 0** judgement is owed.

**The failing set is identical to Slice 6's record.** Compared as a set, not as a count
([`BUILD.md`][build-md] `### What gets recorded`): `bld-040-slice-6-code_remediation.md`
`### Failability proofs` entry 3 lists exactly these two ids, in this order, at this same
scope, with the same `2` / `0` figures and the same baseline `195 passed`. Edit 2 moved a
call out of a `raises` block inside one of them and the set did not move.

**Transient-mutation conditions, each met.** One mutation live at a time; restored inside
this pass by the tool's `finally`, with the restore proved by `filecmp` plus SHA-256
before this report was written; no mutation live across the `Status:` transition;
`find . -name 'ACTIVE-MUTATION.json'` returns **nothing**. The shared file is left as the
concurrent session found it.

**Net-zero on the mutated production file, proved rather than asserted.**
`django_strawberry_framework/auth/mutations.py` is byte-restored per the tool's
comparison, and independently: its diff against HEAD is still Slice 6's comment-only
`11 insertions / 4 deletions`, and

```shell
$ git show HEAD:django_strawberry_framework/auth/mutations.py > <scratch outside repo>
$ uv run python docs/builder/temp-tests/040-slice-6/ast_identity.py <scratch> \
      django_strawberry_framework/auth/mutations.py
IDENTICAL                                                            # exit 0
# positive control (the instrument can fail): the same comparison against a copy with
# `X_CONTROL = 1` appended prints DIFFERENT, exit 1.
```

`git diff --stat -- django_strawberry_framework/` is **not** empty and cannot be: it
carries Slice 6's three comment-only files and the concurrent `spec-050` session's three
production files. The check that is actually available to a worker here is the one run
above - byte-identical restore, AST identity against HEAD for the mutated file, and no
surviving marker - and it is the check the dispatch's condition is for. Stated plainly
rather than reported as a clean empty diff it is not.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **The pinned line break in Edit 1 was kept.** The replacement leaves the docstring's
  third line short ("re-registered model, and") followed by the untouched
  "the class name is load-bearing …" line. Re-wrapping the paragraph would read better
  and would change bytes the pin did not authorize, so it was not done; `ruff format`
  does not reflow docstrings, and it confirmed the file unchanged after the edits.
- **Edit 2's local is `model`, not `user_model`.** The sibling row uses `user_model`
  because it also feeds a `monkeypatch.setattr`; the pinned text for this row says
  `model` and that is what landed. Naming symmetry between the two rows was not pursued -
  it is not what L2 is about, and it is not in the pinned text.
- **A new manifest rather than `--only`.** `--help` states that `--only` labels its report
  `PARTIAL RECORD`; a one-entry manifest for the one entry this pass owes produces a
  complete block instead, and the entry's fields are copied verbatim from the prior
  manifest so the comparison against Slice 6's record is of the same mutation.

### Notes for Worker 3

- Both edits are the pinned text verbatim; the diff for this pass is three added lines and
  two removed, all in `tests/auth/test_mutations.py`. `git diff` on that file also carries
  Slice 6's and the consolidation loop's work, which this pass did not touch.
- The re-run entry is reproducible as recorded: same manifest path, same scope string. A
  re-run at any other scope produces a different set and is not a comparison against
  Slice 6's record.
- No shadow file was generated or read this pass; the static helper's triggers do not fire
  (two changed lines of test text, no production logic).

### Notes for Worker 1 (spec reconciliation)

None. Neither edit touches a contract the spec states: Edit 1 is docstring prose inside a
test helper and Edit 2 rearranges two statements inside one row without changing its
subject, its assertion, or its node id. No spec amendment is owed by this pass, and
nothing in the diff falsifies a `-terms.csv` row or a citation.

### Working-tree note (stop-and-report, no action taken)

`git status --short` carries the concurrent `spec-050` session's files listed in the
table above, plus this cycle's earlier-slice files. **Nothing was reverted, checked out,
stashed or tidied.** No `git stash` / `checkout` / `restore` / `worktree` was run
anywhere in this pass; the one read-only HEAD reference
(`git show HEAD:django_strawberry_framework/auth/mutations.py`, for the AST-identity
control) went to a scratch path outside the repository. Every ruff and pre-commit
invocation named its paths **explicitly**, never `.` and never through a shell variable.

---

## Review (Worker 3, pass 2)

Re-review of the routed pass `### The routed pass, pinned verbatim` dispatched: two
one-line edits in `tests/auth/test_mutations.py` (L2 and L3 from `## Review (Worker 3)`).
The delta and its blast radius are the subject; Slice 6's rows and the consolidation are
closed work, reviewed twice and once respectively, and are not re-reviewed here
([`worker-3.md`][worker-3] `## Review job`, the cumulative-diff trap — the navigational
filter is Worker 2's `### Files touched` for **this** pass). Line numbers are
pin-at-write-time hints (per-cycle scratchpad).

No prior entry in this artifact was edited ([`ARTIFACT.md`][artifact-md]
`## Re-pass sections`); this section is new text at top level, placed before the single
bottom link-definition block the markdown convention requires.

### Failability re-run pre-registration (recorded BEFORE the mutation was made)

[`worker-3.md`][worker-3] `### Reading is necessary, not sufficient` requires the mutation
to be recorded here before it is applied. **One** boundary is re-run this pass:

1. `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS` — replace
   the five-name frozenset with `frozenset()`, so the intersection never matches and
   `::derive_register_fields` never raises. Scope as Slice 6 and both Worker 2 passes
   recorded it: `tests/auth/`.

That is entry **3** of `bld-040-slice-6-code_remediation.md` `### Failability proofs`. It
sits inside the mandatory floor (2 rows ≤ 3) **and** one of its two failing rows,
`::test_derive_register_fields_rejects_privilege_fields`, is the row Edit 2 rewrote, so it
is the one boundary in the floor whose reach this diff could have moved. Entries 1, 2 and
4 are untouched by this diff and are deliberately **not** re-run, per the dispatch and
`### The routed pass, pinned verbatim`.

Applied through `scripts/prove_failability.py`, which enforces the loop order including
the anchor check before the pre-mutation copy, from my own manifest
`docs/builder/temp-tests/040-integration/w3-proofs-pass-2.json` — Worker 2's
`proofs-pass-2.json` left untouched — with the scratch root **outside** the repository.
Restore proved by byte comparison against my own pre-mutation copy. No `git checkout` /
`stash` / `restore` / `worktree` anywhere in this pass.

Pre-mutation state of the target, recorded before the manifest was written:

```shell
$ shasum -a 256 django_strawberry_framework/auth/mutations.py
ad6a3f7efea49aab50858adf5a7c1da075bd3ab4d93385cd83b1292885e3cbe0
$ git show HEAD:django_strawberry_framework/auth/mutations.py > <scratch outside repo>
$ uv run python docs/builder/temp-tests/040-slice-6/ast_identity.py <scratch> \
      django_strawberry_framework/auth/mutations.py
IDENTICAL                                                              # exit 0
# positive control: the same comparison against that copy with `X_CONTROL = 1` appended
# prints DIFFERENT, exit 1 — the instrument can distinguish.
$ find . -name 'ACTIVE-MUTATION.json' -not -path './.git/*'   -> (nothing)
```

### Failability re-run results

Run through `scripts/prove_failability.py` (which enforces the loop order, the anchor check
first), manifest `docs/builder/temp-tests/040-integration/w3-proofs-pass-2.json`, report
`docs/builder/temp-tests/040-integration/w3-proof-report-pass-2.md`, scratch root outside the
repository. Anchor check run standalone first (`--check-anchors-only`) and again by the tool:
**matches exactly once** both times.

| # | Boundary | Rows | Errors | Pre-mutation baseline | Mutant | Restore |
|---|---|---|---|---|---|---|
| 3 | `django_strawberry_framework/auth/mutations.py::_REGISTER_PROTECTED_FIELDS` | **2** | 0 | `195 passed`, exit 0; 0 rows differenced out | `2 failed, 193 passed`, exit 1 | `filecmp.cmp(shallow=False)` True; sha256 `ad6a3f7efea49aab…` == `ad6a3f7efea49aab…` |

Failing node ids, mine, listed so the count is `len()` rather than asserted:

- `tests/auth/test_mutations.py::test_derive_register_fields_rejects_privilege_fields`
- `tests/auth/test_mutations.py::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call`

**Compared as sets, mechanically, not by eye.** My ids, Worker 2's pass-2 ids and Slice 6's
entry-3 ids were each extracted to a file and `diff`ed:

```shell
$ diff ids-w3-pass2.txt ids-w2-pass2.txt    -> no output, exit 0
$ diff ids-w3-pass2.txt ids-slice6.txt      -> no output, exit 0
# control, that the comparison can fail:
$ diff ids-w3-pass2.txt <(tail -1 ids-w3-pass2.txt) >/dev/null   -> exit 1
```

**Four measurements of this boundary now agree id for id** — Slice 6's, my integration pass-1
re-run, Worker 2's pass-2 re-run, and this one — at one scope, `tests/auth/`. 2 rows clears the
0-or-1 weakly-pinned rule; 0 collection/setup errors, so the count is a valid count; no zero-row
entry, so no `why 0` judgement is owed. **The row Edit 2 rewrote is itself in the failing set**,
which is the point of re-running this entry rather than trusting the prediction that a statement
move cannot shift a failing set.

Post-proof state of the target, each item re-checked by me after the tool finished:

```shell
$ grep -c '_REGISTER_PROTECTED_FIELDS = frozenset($'  …/auth/mutations.py   -> 1   (anchor back)
$ grep -c '_REGISTER_PROTECTED_FIELDS = frozenset()'  …/auth/mutations.py   -> 0   (mutant gone)
$ find . -name 'ACTIVE-MUTATION.json' -not -path './.git/*'                 -> (nothing)
$ cmp <my pre-mutation copy, outside the repo> django_strawberry_framework/auth/mutations.py
                                                                            -> exit 0
$ shasum -a 256 django_strawberry_framework/auth/mutations.py
ad6a3f7efea49aab50858adf5a7c1da075bd3ab4d93385cd83b1292885e3cbe0   (== the pre-mutation value
                                                                    recorded above, and ==
                                                                    Worker 2's restore hash)
$ uv run python docs/builder/temp-tests/040-slice-6/ast_identity.py <HEAD copy> \
      django_strawberry_framework/auth/mutations.py                         -> IDENTICAL
```

**The invariant applied is the mutated file's, not the directory's.**
`git diff --stat -- django_strawberry_framework/` is not empty and cannot be — it legitimately
carries Slice 6's three comment-only files and the concurrent `spec-050` session's production
edits — so a fence phrased against that directory is unsatisfiable on this tree and would be
either a false clean or a false alarm. The satisfiable invariant is the one above: the mutated
file byte-identical to my own pre-mutation copy, and no `ACTIVE-MUTATION.json` surviving.
Worker 2 states the same thing in its `### Failability proofs`; I re-derived it rather than
accepting it.

**Where the second pair of eyes landed.** Re-run by me this pass: entry 3,
`::_REGISTER_PROTECTED_FIELDS`. Accepted on record and deliberately **not** re-run: entries 1
(`::_transport_prologue`), 2 (`types/finalizer.py::finalize_django_types`) and 4
(`types/resolvers.py::_check_n1`). Grounds: this diff changes two lines inside one row, and
that row belongs to entry 3 alone; entry 1's two rows, entry 2's two ids and entry 4's two rows
are untouched text, and I re-measured entries 1 and 3 myself one pass ago and entry 2 the pass
before that. Re-measuring untouched boundaries is noise; skipping the touched one would have
left the pinning of the edited row asserted rather than shown.

### The two edits, compared character for character

Both pinned blocks were extracted from `### The routed pass, pinned verbatim` by fence position
(not retyped), both landed blocks were extracted from the source by AST (docstring of
`::_privilege_required_user`, statement span of
`::test_derive_register_fields_rejects_privilege_fields` after its docstring), and the pairs were
`diff`ed as files:

```shell
$ diff pin1.txt landed1.txt   -> no output, exit 0     # Edit 1 (L3), docstring clause
$ diff pin2.txt landed2.txt   -> no output, exit 0     # Edit 2 (L2), statement split
# control, that the comparison can fail:
$ diff pin1.txt landed2.txt >/dev/null                 -> exit 1
```

Both are **character-identical to the pin**, including Edit 1's pinned line break after
"re-registered model, and" and Edit 2's pinned local name `model`. The superseded text is gone
from the file, not merely added around: `grep -n 'not re-register warn'` and
`grep -n 'derive_register_fields(_privilege_required_user())'` each return **0** matches.

**The `model` / `user_model` question — Worker 2's call was right.** Landing the pin verbatim is
what makes the comparison above possible at all: once a builder harmonizes a name the pin did not
authorize, a reviewer can no longer distinguish "improved it" from "paraphrased it", and
paraphrase is the defect class this cycle's routing exists to prevent (`### The routed pass,
pinned verbatim` says so in its own first paragraph). Deviating would also have been a silent
widening of a Low-fix pass's mandate. It does leave a small inconsistency, recorded as **L4**
below rather than waved through, and the inconsistency is the **pin's**, not the builder's.

### L2 did not change what the row proves — the narrowing, shown rather than argued

Shape, read off the AST rather than by eye:

```text
::test_derive_register_fields_rejects_privilege_fields  body = [docstring, Assign, With]
    outside the block : model = _privilege_required_user()
    inside the block  : derive_register_fields(model)          (exactly 1 statement)
    raises args       : pytest.raises(ConfigurationError, match=_PROTECTED_FIELD_REJECT)
::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call  (sibling)
    inside the block  : register_mutation()                    (exactly 1 statement)
    raises args       : pytest.raises(ConfigurationError, match=_PROTECTED_FIELD_REJECT)
```

The `raises` arguments are untouched and identical to the sibling's, the block now contains
exactly the call the row names, and the only statement that moved out is the factory binding —
setup, whose failure is now an error rather than a candidate satisfier. **Nothing else in the
row runs outside the assertion's protection**, because there is nothing else in the row.

That the move **narrows** what can satisfy the assertion is demonstrated by a temp probe
(`docs/builder/temp-tests/040-integration/w3_pass2_shape_narrowing.py`, 2 rows, both pass)
rather than asserted: against a factory that itself raises the row's exception type with a
matching message, the pre-edit shape is **green while the subject never runs**, and the landed
shape lets that same failure escape. Worker 1's live-hole analysis is unaffected and I reach the
same answer — `::_unique_app_label` returns an f-string and cannot raise `ConfigurationError`,
and a Django model-declaration failure is `ImproperlyConfigured` / `RuntimeError`, which fails
the `isinstance` half — so there was no live hole before and there is none now. What changed is
that the guarantee no longer rests on a helper body someone else may edit.

The failability half agrees: the row still fails when the boundary is removed, and it fails with
the boundary's own signature (`DID NOT RAISE` on a call that no longer raises), not incidentally
— the mutant's failing set is the same two rows it was at Slice 6.

### Node ids: re-derived, with the control the trap demands

```shell
$ uv run pytest tests/auth/ --no-cov --collect-only -q -q -p no:cacheprovider \
      | grep '::' | sort | wc -l          -> 195      (raw output: 197 lines)
$ uv run pytest tests/auth/ --no-cov --collect-only -q   -p no:cacheprovider \
      | grep '::' | sort | wc -l          ->   0      (raw output: 216 lines)
$ diff <that empty file> <another empty file>          -> exit 0   (two empty files diff clean)
```

**The control is the second line, and it is the fourth time in this cycle the single-`-q` form
has had to be shown rather than described.** `pytest.ini`'s `addopts` carries `-v`; one `-q`
nets to verbosity 0 and prints tree lines containing no `::`, so the grep writes an empty file
and the comparison passes while measuring nothing. My 195 is the figure from the instrument I
have just watched fail, and 195 id lines out of 197 raw lines is the evidence the file is not
empty. It matches Worker 2's 195/197 exactly.

**The "before" side, re-derived rather than borrowed.** Worker 2's before-file is not in the
tree and no copy of the pre-pass file exists, so I reconstructed it: the two pinned replacements
reversed in a scratch copy outside the repo (each `new` text asserted to occur **exactly once**
before replacing), then node ids AST-derived from both sides.

```shell
$ diff ast-before.ids ast-after.ids          -> no output, exit 0   (75 ids each side)
$ diff ast-before.ids <ast-after minus one>  -> exit 1              (the control)
```

No id added, removed or renamed — which is what the shapes predict: Edit 1 is inside a docstring
of a non-`test_` helper and Edit 2 adds an assignment inside an existing function body.

**What the reconstruction cannot prove, stated plainly.** It is built by reversing exactly the
two edits, so it could not reveal a *third* change made in the same pass. That question is
answered instead by four invariants recorded **before** this pass and re-derived by me now, all
unmoved:

| Invariant | Recorded before this pass | Re-derived now |
|---|---|---|
| file length | 3,159 lines (`## Review (Worker 3)` `### DRY findings`) | reconstruction **3,159**; worktree 3,161 (+2, both hunks) |
| `--collect-only -q -q` on the file | 116 (`## Review (Worker 3)`) | **116** |
| `_LOGOUT_Q` readers, AST Load-context | 15 (`### 1. Disposition …`, Worker 1) | **15** (1 store, at `:300`) |
| executable-literal census | `SessionMiddleware` 1x, `AuthMiddlewareStack` 1x, `mutation{ logout{ ok errors{ field } } }` 1x | **1x / 1x / 1x** |

Together with `195 passed` / `21 passed` and the unmoved failing set, that is a converging set of
pre-pass figures; none of them moved, and a third edit would have had to miss all of them.

### High:

None.

### Medium:

None.

### Low:

#### L4 — the pinned local `model` diverges from the file's own `user_model`

`tests/auth/test_mutations.py:1253` binds `model`; the file's three other user-model locals are
`user_model` (`:881`, `:950`, and the sibling row at `:1269`), and the production parameter the
value is passed to is also `user_model`
(`django_strawberry_framework/auth/mutations.py::derive_register_fields`). So the landed name is
1-of-4 against a settled local convention.

**Origin is the pin, not the builder.** `### The routed pass, pinned verbatim` spells the local
`model`; Worker 2 landed the pin character-exact and recorded the choice and its reason in
`### Implementation notes`. That was the right call — see above.

**Recorded and intentionally not routed.** Severity is Low and the fix is a two-token rename in
a file that three passes have now pinned text in; a fourth loop to harmonize a local name costs
more than it returns, and the shape defect L2 named is fully closed either way. **Recommended:**
if a loop over this file happens for any other reason, rename to `user_model`; otherwise leave
it. Recorded rather than waved through so the divergence is a decision with a reason rather than
an oversight a later reader has to re-litigate.

#### L5 — the build report's line tally for its own diff is 4 added, not 3

`## Build report (Worker 2, pass 2)` `### Notes for Worker 3` states "the diff for this pass is
three added lines and two removed". Re-derived against the reconstruction: **4 added, 2
removed**, net +2 (Edit 1: 1 line -> 2; Edit 2: 2 lines -> 3), and the file grew 3,159 -> 3,161,
which is the same +2 measured a second way.

```shell
$ diff pre-edit.py tests/auth/test_mutations.py | grep -c '^>'   -> 4
$ diff pre-edit.py tests/auth/test_mutations.py | grep -c '^<'   -> 2
```

**Low.** The tally's job was to say "two one-line edits and nothing else", and that conclusion is
unchanged and independently established above. Nothing downstream reads the figure. It is
recorded because a stated count reads as measured to every later pass
([`BUILD.md`][build-md] `## Claims are proven mechanically, never accepted on prose`) — the same
genus as pass 1's L1, in the same artifact, which is worth Worker 1 noticing as a pattern rather
than as two isolated slips. **Recommended:** correct the figure if the artifact is revised for
another reason; no loop on its own.

### DRY findings

- **No new duplication.** The diff introduces one local binding and rewords one docstring
  clause. It creates no literal, no helper, no branch and no parallel data flow. The executable
  literal census over the file is unchanged from pass 1 (table above), and
  `scripts/review_inspect.py` was **not** run this pass — its triggers do not fire for two lines
  of test text with no production logic, which is Worker 2's stated reason and I reach the same
  one. Recorded as a skip with its reason, per [`worker-3.md`][worker-3] `## Static helper use`.
- **No existence challenge is raised.** The pass adds no abstraction — no helper, registry,
  token or indirection layer. The three extractions the consolidation loop added were challenged
  and answered in `## Review (Worker 3)` `### DRY findings`; nothing in this diff reopens that.
- **Edit 2 removes a small near-copy divergence rather than adding one.** The two DRY-1 rows now
  carry the same two-statement shape and the same `raises` arguments; before it, one of them
  differed from its sibling in a way a reader had to notice. The residual difference is the local
  **name** only, which is L4.
- **No fail-open shape.** The diff computes no input to a limit, a size, a permission decision or
  a rejection: it is one assignment of a factory return and one docstring clause. No clamp, no
  `getattr` default, no `or` fallback, no bare `except`, no truthiness test on an absent-able
  value. The boundary the rows pin is production-side and unchanged, and its mutant still fails
  the same two rows.
- **No cross-cohort duplication check is owed.** One cohort, one file, two lines.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** (exit 0, no output; the file
is not in `git status --short`): `__all__` and the re-export list are unchanged. This pass edits
two lines of one test file and adds no public export.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### Confirming the fence held

- **`tests/auth/_helpers.py` and `tests/auth/conftest.py` were not edited.**
  `git diff --stat` against HEAD is empty for both, and both carry an mtime of `2026-07-20`,
  seven weeks before this cycle opened. That they were not *read* is not worker-verifiable; what
  is verifiable is that nothing in the diff could have come from either, since the landed text is
  character-identical to the pin.
- **Nothing outside `tests/auth/test_mutations.py` changed, except the transient mutation.**
  Worker 2's pass ran between `03:40` and `03:44`; the only files with an mtime in that window
  are `tests/auth/test_mutations.py` (`03:40:47`), `django_strawberry_framework/auth/mutations.py`
  (`03:41:25`, the proof's restore — byte-proved, AST-identical to HEAD, sha256 unchanged) and
  this artifact (`03:43:59`). Everything else dirty in `git status --short` carries an mtime of
  `03:34` or earlier and belongs to Slice 6, the earlier integration pass, or the concurrent
  `spec-050` session. `docs/builder/build-040-auth_mutations-0_0_13.md` (`03:44:39`) is
  Worker 0's slice log, not this pass.
- **The concurrent session's files were not touched by me.** Its set has moved again since
  Worker 2's table — `resource_policy.py`, `_strawberry_patches.py` and
  `tests/test_graphql_core_patches.py` are clean now, and `mutations/sets.py`,
  `mutations/resolvers.py` and `docs/GLOSSARY.md` are dirty — which is that session's work
  proceeding, not this pass's. **Nothing was reverted, checked out, stashed or tidied**
  ([`AGENTS.md`][agents] rule 34). No `git stash` / `checkout` / `restore` / `worktree` ran
  anywhere in this pass; the one `git show HEAD:…` reference went to a scratch path outside the
  repository.
- **Every ruff invocation named its path explicitly, never `.`:**
  `uv run ruff format --check tests/auth/test_mutations.py` -> `1 file already formatted`;
  `uv run ruff check tests/auth/test_mutations.py` -> `All checks passed!`. Read-only forms, so
  nothing of the concurrent session's could be rewritten even by accident.
- **No `--cov*` flag anywhere in this pass**, in my runs or in the tool's.

### What looks solid

- Both edits are the pin, byte for byte, including the awkward line break Edit 1 leaves behind.
  Worker 2 recorded *why* it did not tidy that break and why it did not harmonize the local name;
  both are the same discipline, and both are right.
- The re-run entry is reproducible exactly as recorded: same manifest fields, same scope string,
  same set. Copying the entry's fields verbatim from the prior manifest rather than reaching for
  `--only` is what makes the comparison a comparison of the same mutation.
- Worker 2 states the directory-level diff check is **not** available on this tree and says what
  it ran instead, rather than reporting a clean empty diff it could not have obtained. That is
  the correct handling of an unsatisfiable fence.
- Focused runs unchanged: `tests/auth/` **195 passed**,
  `examples/fakeshop/test_query/test_auth_api.py` **21 passed**.

### Temp test verification

- `docs/builder/temp-tests/040-integration/w3_pass2_shape_narrowing.py` — 2 rows, both pass.
  Written to make L2's "the move narrows what can satisfy the assertion" mechanical instead of
  argued: it shows the pre-edit shape passing while its subject never runs, and the landed shape
  letting that same setup failure escape. It models the shapes, not the production boundary, so
  it catches no bug and is **not** promoted: the real boundary is already pinned by the two rows
  entry 3's mutant fails. **Disposition:** cycle scratch, gitignored, cleared with the cycle.
- Also written: `w3-proofs-pass-2.json` (my manifest) and `w3-proof-report-pass-2.md` (the tool's
  report). Worker 2's `proofs-pass-2.json` / `proof-report-pass-2.md` and my own pass-1
  `w3-proofs.json` / `w3-proof-report.md` were left untouched. All gitignored
  (`.gitignore:192`).
- Scratch outside the repo (the HEAD copy, the reconstruction, the id lists, the proof's pristine
  copy) is in the session scratchpad, not in the tree.

### Notes for Worker 1 (spec reconciliation)

- No spec gap, conflict or unstated assumption surfaced; this pass edits two lines of one test
  file and read the spec not at all.
- **L4 and L5 are recorded with rejection reasons and neither is routed.** L4 is the pin's own
  `model` / `user_model` divergence — if the third Worker 1 close wants naming symmetry it is a
  two-token rename, but it needs a loop and I do not think it earns one. L5 is a prose tally in
  `## Build report (Worker 2, pass 2)`, discharged the way L1 was: correctable by Worker 1
  without a builder.
- **Pattern worth one line in the close:** L1 and L5 are the same defect shape — a stated count
  in this artifact's prose that nobody measured as they wrote it — and they are two passes apart
  in one artifact. Both were caught by re-derivation and neither changed a conclusion, which is
  the good case; the figure that matters is that it is two for two.

### Review outcome

`review-accepted`. No High and no Medium finding. Two Lows, both recorded with an intentional
rejection reason and neither blocking: L4 the pinned local name's divergence from the file's
`user_model` convention, L5 an off-by-one line tally in build-report prose. Both edits are
character-identical to Worker 1's pinned text, proved by `diff` against extracted blocks with a
control that shows the comparison can fail. Entry 3 re-run by me at the recorded scope
(`tests/auth/`): 2 rows, 0 collection/setup errors, baseline `195 passed`, and the failing set
identical id for id to Worker 2's pass-2 record and to Slice 6's — four agreeing measurements.
Restore proved by byte comparison against my own pre-mutation copy outside the repo, with the
anchor back, the mutant absent and no `ACTIVE-MUTATION.json` surviving. Node ids unchanged, 195
of 197 raw lines under `-q -q`, with the single-`-q` trap reproduced as the control. The fence
held.

---

## Final verification (Worker 1, pass 2)

Third and closing Worker 1 pass over this artifact, covering the routed pass of
`### The routed pass, pinned verbatim` (Edits 1 and 2), Worker 3's two Low findings
from it, and the four confirmations the integration pass owes before the gate. No
prior entry in this artifact was edited ([`ARTIFACT.md`][artifact-md]
`## Re-pass sections`); everything below is new text, placed before the single bottom
link-definition block.

Spec status-line re-verification, run first as every Worker 1 spawn owes: the spec
still opens `Shipped in 0.0.13 (card DONE-040-0.0.13)` and the companion's lead-in
names the spec by its live path. The routed pass touched one test file and no spec
surface, re-derived below rather than accepted from either worker's
`### Notes for Worker 1`. **No spec or companion edit is owed by this pass**, and none
was made.

Every figure below was measured as it was written. Where a figure corrects a prior
entry, both the wrong and the right one are stated, because no later reader may edit
either site and none should be left adjudicating.

---

### 1. Disposition of Worker 3's two Low findings

#### L4 — the pinned local `model` against the file's `user_model`. Accepted; the divergence stands, and the defect is the pin's

Re-derived at source rather than accepted from the review:

```shell
$ grep -n '\buser_model\b' tests/auth/test_mutations.py
881:    user_model = get_user_model()          # async login row
950:    user_model = get_user_model()          # sync login row
1269:    user_model = _privilege_required_user()   # the sibling DRY-1 row
$ grep -n '^\s*model = ' tests/auth/test_mutations.py     -> 1253   (the landed pin)
$ grep -n 'def derive_register_fields' django_strawberry_framework/auth/mutations.py
1032:def derive_register_fields(user_model: type) -> tuple[str, ...]:
```

Three local bindings plus the production parameter the value is passed to spell it
`user_model`; the landed local is `model`. Worker 3's figure holds: 1-of-4.

**Worker 2's call was right, and so is Worker 3's grounds for filing this against the
pin rather than the builder.** Landing a pin character-exact is what makes the
comparison possible at all — once a builder harmonizes a token the pin did not
authorize, no later pass can distinguish "improved it" from "paraphrased it", and
paraphrase is the class the pinning discipline exists to prevent. A pass dispatched to
make two Low edits does not get to widen its own mandate on the way through. **The
divergence is mine**: I wrote `model` into the pin in this artifact's
`### The routed pass, pinned verbatim` and recorded no reason for the name. That is
worth saying plainly, because an unattributed naming defect in shipped test code reads
as the builder's.

**Decided: accepted, not routed.** The ground is not severity — all of L2, L3 and L4
are Low, and severity is not what routed the first two:

- **L2 and L3 were defects of content; L4 is not.** L2 changed what its row could
  prove (the `pytest.raises` block scoped over its own setup) and L3 left a sentence
  that does not parse in the one docstring written to stop a future editor flattening
  the factory. L4 changes nothing a row proves and nothing a reader can misread: the
  local is bound and read two lines apart inside one function body, and its only
  consumer is the call on the next line. My own standing rule — route a Low by who
  owns the defect, not by how bad it is — presupposes a defect in what the code does
  or says. A local's name diverging from a sibling's is a convention divergence, and
  its remedy is symmetry, not correctness.
- **The cost is not the two tokens.** It is a fifth pass over a file four passes have
  now pinned text in, carrying the same obligations each time: a re-run of
  `scripts/prove_failability.py` entry 3 (the renamed local sits inside
  `::test_derive_register_fields_rejects_privilege_fields`, one of that entry's two
  failing rows), a collected-node-id comparison, scoped ruff, a two-run pre-commit —
  in a tree a concurrent session is writing. [`AGENTS.md`][agents]'s ban on
  defer-the-real-fix sequencing governs a real fix deferred for speed, a test-only
  patch over wrong production code, or a `pragma: no cover` workaround. A local name
  is none of those.
- **Recorded with its condition, as `### Ruling 1` recorded its own.** If any later
  pass opens `tests/auth/test_mutations.py` for another reason, rename `model` →
  `user_model` at `:1253`. That lands in the catalog below so the next reader inherits
  a decision with a reason rather than an oversight to re-litigate.

**The lesson the pin itself owes**, since it is the part that generalizes: a
character-exact pin fixes *every* token in it, including the ones the finding is not
about, so a pin owes the same convention check the code it replaces would get. This
one did not get it.

#### L5 — the build report's line tally. Upheld, corrected here

**`## Build report (Worker 2, pass 2)` `### Notes for Worker 3` states "the diff for
this pass is three added lines and two removed". It is wrong. The true figure is 4
added and 2 removed.** Both are stated here because no later reader may edit that
entry.

Re-derived by me, with my own reconstruction rather than Worker 3's:

```shell
# reconstruction: each pinned replacement reversed in a scratch copy OUTSIDE the repo,
# each `new` text asserted to occur exactly once first (new1 1, new2 1; old1 0, old2 0)
$ diff <scratch>/pre-edit-w1.py tests/auth/test_mutations.py | grep -c '^>'   -> 4
$ diff <scratch>/pre-edit-w1.py tests/auth/test_mutations.py | grep -c '^<'   -> 2
$ wc -l  reconstruction 3,159   worktree 3,161                                -> net +2
# control, that the comparison can fail / can pass:
$ diff <a copy of the worktree file> tests/auth/test_mutations.py             -> exit 0
```

The per-edit accounting says why 4 is the number rather than 3: **each edit replaces
one line with two**, so each contributes 1 removed and 2 added — Edit 1's docstring
clause (`… does not re-register warn, and` → two lines) and Edit 2's
`derive_register_fields(_privilege_required_user())` (→ `model = …` plus
`derive_register_fields(model)`). Counting the *net* new lines gives +2; counting
Edit 2's two new lines plus Edit 1's one net line gives the stated 3. The figure Worker
3 published, 4 / 2, is the one a `diff` produces.

**Not routed.** Correcting artifact prose is Worker 1's work and needs no builder, and
the conclusion the tally supported — "two one-line edits and nothing else" — is
independently established three other ways in this artifact and holds unchanged.

---

### 2. Three unmeasured counts in one cycle's own prose — and a fourth thing this pass found

The recurrence is the finding, so it is stated as a population rather than as three
anecdotes. Every one was caught by a **later pass re-deriving the number**; none was
caught by reading.

| # | Stated | True | Instrument that was wrong | Where |
|---|---|---|---|---|
| 1 | `_LOGOUT_Q` readers `11` -> `14` | `12` -> `15` | right arithmetic, **wrong population** — measured at HEAD while the sentence described the post-Slice-6 worktree the loop was about to edit | `### Ruling 2`; `## Build report (Worker 2)`; corrected in `### 1. Disposition …` of pass 1 |
| 2 | the subprocess idiom is a "four-way" duplication | **8 files, 8 call sites** | a census whose first-argument match cannot see a call built into a variable first | Slice 6 plan; `### Ruling 3`; corrected in pass 1's catalog, re-measured again this pass |
| 3 | "three added lines and two removed" | **4 added, 2 removed** | a net-line count published as a diff count | `## Build report (Worker 2, pass 2)`; corrected in `#### L5` above |

**A fourth, not a count but the same family, and the only one with a consequence.**
`## Review (Worker 3, pass 2)` `### Confirming the fence held` attributes
`django_strawberry_framework/mutations/sets.py` and
`django_strawberry_framework/mutations/resolvers.py` to the concurrent `spec-050`
session. **They are this cycle's** — Slice 6's `F3` fixes — and their entire diff says
so:

```shell
$ git diff -- django_strawberry_framework/mutations/sets.py       # 7 +, 7 -
  -  The overridable input-materialization seam ``_bind_mutation`` calls at
  +  The overridable input-materialization seam ``bind_write_declarations`` calls at
  -    - model-backed (``_bind_mutation``): …   -> ``bind_mutations``
  -    - model-less (``_bind_form_mutation``): … -> ``bind_form_mutations``
$ git diff -- django_strawberry_framework/mutations/resolvers.py  # 6 +, 6 -
  -  … silently drop it from the exclude calculation - the spec-040 Revision-7 marker fix
  +  … silently drop it from the exclude calculation).
```

Both are the `F2` / `F3` sweep this cycle was commissioned to do. The correction
matters where the three counts do not: **a maintainer reading that paragraph to decide
what to stage would leave the `F3` fix out of this cycle's commit.** Attributions for
the commit come from `### 7. What the maintainer is being handed` below, which is
derived from diff content rather than from "files my pass touched"
([`START.md`][start] `## Concurrent sessions`).

**What the recurrence means for the artifacts the maintainer is about to read.**

- **All three counts share one shape: a supporting tally attached to a conclusion that
  holds at any value** — "live duplication, not dead code", "the shared home is a
  repo-level decision", "two one-line edits and nothing else". That is exactly why
  they were not measured (nothing downstream forces them to be right) and exactly why
  they are the ones that reach a maintainer unchallenged. Every **load-bearing** figure
  in this cycle was re-derived by two or more passes and all of them held: the four
  failability row counts and their node-id sets, the 979 citations, the 216 rows, the
  30 glossary terms, the 12 / 12 Decision headings, the 16 retractions, the five-member
  protected set, the staged-anchor population.
- **So [`BUILD.md`][build-md] `## Claims are proven mechanically, never accepted on
  prose` is right and is not self-enforcing.** Three for three in one cycle, in an
  artifact whose every pass had read that section. What enforced it was never care; it
  was a second pass re-deriving the figure **with its population named**. The
  prescribed fix — "measure as you write the number" — is the one that failed each
  time, because the writer in each case believed the number had already been measured
  (it had — of a different tree, a different population, or a different quantity).
- **Practical instruction for the maintainer, and the reason this section exists:**
  treat any number in this cycle's `bld-040-*.md` prose as an estimate **unless the
  sentence carrying it also names its instrument and its population.** The figures that
  do carry both are the ones in `### 4` and `### 6` below, and in the failability
  records. **Nothing shipped rests on any of the three wrong numbers** — all three sat
  in per-cycle scratch prose, and all three conclusions survive unchanged at the true
  figures.
- One process observation, recorded rather than acted on because a worker may not edit
  a workflow doc mid-cycle and the corpus ratchet governs any such edit: this cycle's
  evidence is that the stated-count rule needs a **mechanical** trigger the way a
  failability proof has one, not a stronger exhortation. That is the maintainer's call
  at closeout, not mine.

---

### 3. Every finding from both review rounds is closed

| Finding | Round | Disposition | Verified here |
|---|---|---|---|
| **DRY-1** — duplicated `PrivilegeRequiredUser` body + rejection regex | `### Ruling 2` | Landed (`_privilege_required_user`, `_PROTECTED_FIELD_REJECT`), reviewed | Both symbols present; the two DRY-1 rows are the failing set of entry 3's mutant, unchanged |
| **DRY-2** — duplicated sessionless assertion block | `### Ruling 2` | Landed (`_assert_sessionless_configuration_error`), reviewed | The two DRY-2 rows are entry 1's failing set, unchanged |
| **DRY-3** — `_CH_LOGOUT` byte-identical to `_LOGOUT_Q` | `### Ruling 2`, left to the builder | **Taken**, ground verified at source by Worker 3 member by member | `_CH_LOGOUT` occurrences in `tests/auth/test_mutations.py`: **0**; `_LOGOUT_Q` 1 store + 15 readers |
| **L1** — `_LOGOUT_Q` tally | W3 pass 1 | Corrected by me in pass 1, figure **and** stated cause | Re-measured this pass: 15 readers at `:584 :594 :602 :685 :846 :856 :894 :973 :1084 :1181 :2574 :2587 :2810 :2832 :2891`, 1 store at `:300`, 17 raw occurrences |
| **L2** — `raises` block over its own setup | W3 pass 1 | Routed; landed character-exact | `derive_register_fields(_privilege_required_user())` -> **0** occurrences; the row is `[docstring, Assign, With]` |
| **L3** — garbled factory docstring clause | W3 pass 1 | Routed; landed character-exact | `not re-register warn` -> **0** occurrences in `.py` |
| **L4** — `model` / `user_model` | W3 pass 2 | **Accepted** with a recorded condition (§1) | — |
| **L5** — line tally | W3 pass 2 | **Upheld and corrected** (§1) | 4 / 2, re-derived |

No High and no Medium finding was raised in either round. Nothing is left open, and
nothing is routed onward except by the recorded decisions in `### 6`.

---

### 4. The divergence inventory still holds after the two one-line edits

Re-run whitespace-normalized over the whole file, because a per-line `rg` is what
nearly hid `D1` the first time.

| Divergence | Re-check | Result |
|---|---|---|
| **D1** | `"structurally unreachable"`, normalized, spec | **1** — the scoped survivor inside Decision 6's two-layer statement, not a sixth divergence |
| | `"structurally absent"` / `"safe by construction"` / `"privilege columns structurally"` | **0 / 0 / 0** |
| | the protected set at source | `_REGISTER_PROTECTED_FIELDS` = `groups, is_active, is_staff, is_superuser, user_permissions` — **five**, matching every spec enumeration |
| **D2** | `"is imported from its public path"` | **0** |
| | `"neither imports nor re-spells"` | **2** — Decision 10 and the `D18 / D19` obligation, one vocabulary |
| **D3** | `### Error shapes` third refusal row | present |
| **D4** | `DONE-040-0.0.13` / `WIP-ALPHA-040-0.0.13` | **5 / 4** — the four are the recorded `### Decided non-edits` |
| **D5** | `"Slice 3 flips"` / `"not yet reserve"` | **0 / 0** |
| self-history | `Revision `, `as of `, `previously`, `amendment`, `review round`, `retract`, `Worker `, `as an earlier draft had it` | **0** on all eight |

Control on the same instrument: `"Decision 6"` normalized over the same file returns
**31**, so the census reads this corpus rather than failing open.

**Spec ↔ companion still agree.** The 12 `### Decision N — …` headings in the spec and
the 12 `## Decision N — …` headings in the companion were extracted and compared **as
sets**: identical, 0 in either direction; a control that truncates one spec heading
makes the comparison fail. The companion carries **16** `**No longer claims:**`
bullets, the same 16 pass 1 swept, and no spec sentence contradicts one.

**Nothing the routed pass touched is cited by either document.** Sweeping the spec and
the companion for `_privilege_required_user`, `_PROTECTED_FIELD_REJECT`,
`_assert_sessionless_configuration_error`, `_CH_LOGOUT`, `_LOGOUT_Q`: **0 each**;
control, `derive_register_fields` in the same two files: **15**. The `#"substring"`
citation population targeting `tests/auth/test_mutations.py` is three hits, all in
per-cycle `bld-040-*.md` prose, and the one that quotes text still under contract
(`::test_register_factory_recache_and_reregister_on_every_call #"rider.__name__ ==
"Register""`) resolves at source (`grep -c` -> 1). **No citation points into either
edited region.**

**Staged anchors, with the control.**

```shell
$ rg -n 'TODO\(spec-040' . --glob '!KANBAN.md' --glob '!KANBAN.html' --glob '!BACKLOG.md'      -> 3
$ rg -n 'TODO-(ALPHA|BETA|STABLE)-040' . <same globs>                                          -> 2
$ rg -n --glob '*.py' 'TODO\(spec-040|TODO-(ALPHA|BETA|STABLE)-040' .                          -> 0
controls: TODO\(spec-  -> 164      TODO-(ALPHA|BETA|STABLE)-  -> 540
```

**Population 5, all Markdown prose about the anchor discipline; 0 staged anchors in
any `.py`.** The two control figures are **not** the 152 / 471 pass 1 recorded, and
that is not drift in this cycle: they are whole-tree counts of a population the
concurrent `spec-050` session and this cycle's own artifacts are both growing, so they
are a dated observation by construction. They do the one job a control has — prove the
pattern matches this corpus — at either value, which is why the control is stated as a
reading rather than pinned as a figure.

---

### 5. The failability records are complete, and no live mutation survives

**Four boundaries, four records, every field [`BUILD.md`][build-md]
`### What gets recorded` requires** — the symbol-qualified boundary, the exact
mutation, the scope as run, the failing node ids **listed**, collection/setup errors
(**0** on all four), the pre-mutation baseline of the same scope (`195 passed`, exit 0,
0 rows differenced out), and the revert proved by `filecmp.cmp(shallow=False)` plus
SHA-256. All four fail **2** rows, so none is weakly pinned and none owes a **why 0**.

**Entry 3 now stands on four agreeing measurements** — Slice 6's, my pass-1 re-run,
Worker 2's pass-2 re-run, Worker 3's pass-2 re-run — all at one scope (`tests/auth/`)
and identical id for id. Entry 1 stands on three; entries 2 and 4 on their recorded
runs, untouched by either loop.

**The eight rows the four records name are all live in the collected set**, which is a
stronger statement than "the node-id set did not move" and is the one that matters
after two loops edited the file:

```shell
$ uv run pytest tests/auth/ --no-cov --collect-only -q -q -p no:cacheprovider \
      | grep '::' | sort   -> 195 ids
  PRESENT  ::test_sessionless_login_raises_the_configuration_error_naming_both_middlewares
  PRESENT  ::test_sessionless_logout_raises_the_configuration_error_naming_both_middlewares
  PRESENT  ::test_derive_register_fields_rejects_privilege_fields
  PRESENT  ::test_register_mutation_rejects_a_protected_required_field_at_the_factory_call
  PRESENT  ::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[finalize]
  PRESENT  ::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem[schema]
  PRESENT  ::test_an_unplanned_relation_under_login_node_is_strictness_visible
  PRESENT  tests/auth/test_queries.py::test_an_unplanned_relation_under_me_is_strictness_visible
# controls, both halves:
$ … --collect-only -q  (single -q)  | grep '::' | wc -l   -> 0    (the trap, reproduced)
$ ::test_sessionless_request_surfaces_djangos_own_error in the set?  -> ABSENT (TG-0's rename)
```

**No live mutation, verified by me rather than read from a report**, and with both
halves — an anchor back at 1 alone would also read clean if a *different* mutation
were live:

```shell
$ find . -name 'ACTIVE-MUTATION.json' -not -path './.git/*'                     -> nothing
$ grep -c '    session = sessions.require_session(request, transport)'  …auth/mutations.py -> 1
$ grep -c '_REGISTER_PROTECTED_FIELDS = frozenset($'                    …auth/mutations.py -> 1
$ grep -c 'session = getattr(request, "session", None)'                 …auth/mutations.py -> 0
$ grep -c '_REGISTER_PROTECTED_FIELDS = frozenset()'                    …auth/mutations.py -> 0
```

**The invariant applied is the mutated file's, not the directory's**, for the reason
recorded twice already in this cycle: `git diff --stat --
django_strawberry_framework/` cannot be empty on this tree (it legitimately carries
Slice 6's three comment-only files and the concurrent session's three production
files), so a fence phrased against the directory is unsatisfiable and would be either
a false clean or a false alarm. The satisfiable invariant, re-derived here with a
positive control:

```text
django_strawberry_framework/auth/mutations.py        AST(docstrings stripped) HEAD == worktree -> True
django_strawberry_framework/mutations/resolvers.py                                             -> True
django_strawberry_framework/mutations/sets.py                                                  -> True
CONTROL (one executable token appended to the HEAD text)                                       -> False
```

All three production files this cycle touched are executable-token identical to HEAD,
so every restore is complete **and** this cycle's production edits remain comment- and
docstring-only — the inverse proof those comment-only findings owe in place of a
failability proof.

---

### 6. The `### Deferred work catalog` input, final

The gate's author writes the catalog into `bld-040-final.md` from this list. Pass 1
listed nine; every one is re-confirmed here, each figure re-measured at this pass, and
three entries are added by the second loop. **Block A is deferred work. Block B is
closed with a recorded decision or is a correction of record — the gate carries these
so it does not re-open or re-adjudicate them.**

#### A. Deferred

1. **The subprocess-isolation idiom — `subprocess.run([sys.executable, "-c", …])`
   spelled inline in 8 test files, 8 call sites.** Source: Slice 6 plan
   `### Out-of-scope observations`; Slice 6 W1 pass-2 item 4; `### Ruling 3`. No
   licensing spec line — out-of-spec DRY. Re-measured this pass over `tests/` and
   `examples/`: `tests/auth/test_mutations.py`, `tests/auth/test_sessions.py`,
   `tests/base/test_init.py`, `tests/filters/test_finalizer.py`,
   `tests/filters/test_sets.py`, `tests/orders/test_inputs.py`,
   `tests/rest_framework/test_soft_dependency.py`, `tests/test_scalars.py` — 1 call
   site each; control, files using `subprocess.run(` at all: **10**, the two extras
   (`tests/test_bug_hunt.py`, `tests/test_ci_governance.py`) not spawning an
   interpreter. Deferred because five directories are involved and the shared home is a
   repo-level `tests/` decision (which conftest; what the contract is for a
   soft-dependency probe versus an import-isolation probe versus a warnings probe) that
   belongs to a DRY cycle over the whole test tree. This build already collapsed the two
   copies inside its own file into `::_auth_free_subprocess`.
2. **`docs/GLOSSARY.md`'s auth entry repeats the exact defect this cycle fixed in the
   spec.** Source: Slice 3 `### Notes for Worker 1` `F1`; Slice 4 `F4`; **D1** of this
   artifact. Licensing line: the plan's `### Scope fence (maintainer-set)`, which puts
   `docs/GLOSSARY.md` out of scope. Re-read at source this pass — `docs/GLOSSARY.md:329`
   still states "the privilege columns (`is_staff` / `is_superuser` / `groups` /
   `user_permissions`) are unreachable by construction": the retired absolute framing
   **and** the four-of-five enumeration, `is_active` absent. The fix is the two-part one
   spec edit 1 made, applied to the `GlossaryTerm` body via the ORM then
   `scripts/build_glossary_md.py`. **Note for whoever takes it:** the file is dirty
   right now from the concurrent `spec-050` session with **one** unrelated hunk (the
   `apps.py` entry's three-appliers -> four-appliers rewrite), so the glossary edit lands
   **on top** of that, never by regenerating over it. **For the maintainer.**
3. **`spec-042 Revision N` citations in `tests/middleware/test_debug_toolbar.py` — 5
   occurrences**, at `:21 :111 :475 :509 :523`, re-measured this pass as occurrences.
   Source: Slice 6 plan `### Out-of-scope observations`. Same defect class as `F2` (a
   label vocabulary a rationale extraction stranded), a different spec's population and
   a different owner. **For the maintainer.**
4. **Bug-hunt round provenance in `tests/auth/test_sessions.py` — 2 occurrences**, at
   `:465` and `:720`, re-measured. Source: same. [`START.md`][start] `## Style Rio cares
   about` bans round provenance in code; the file was on no cohort's writable list and
   cites no spec, so both sit outside `F2`'s population. Pass 1 corrected the inherited
   figure from 1 to 2 — the `START.md` "partial claim fix = dominant residual defect"
   shape, where a one-site figure would have closed the finding with half of it live.
   **For the maintainer.**
5. **`Revision N P<n>` citations in
   `examples/fakeshop/test_query/test_library_api.py` — 5 occurrences**, at `:2749
   :3830 :3885 :4026 :4041`, re-measured. Source: Slice 6 plan `### Out-of-scope
   observations`. That file belongs to the **concurrently active `spec-050` cycle** and
   must not be touched by this one ([`AGENTS.md`][agents] rule 34). **For the
   maintainer / that cycle.**
6. **`## Definition of done` item 6's coverage clause is structurally unverifiable by
   any worker.** Source: Slice 4 `### Spec changes made`, the one un-ticked box of that
   slice. Licensing line: [`BUILD.md`][build-md] `## Coverage is the maintainer's gate,
   not a worker's tool`. Its other half (`D-N3`'s source comment) is **discharged**, by
   Slice 6's pinned comment and by this artifact's companion edit marking the
   observation closed. The coverage half is the maintainer's gate by construction.
7. **Cosmetic, unfixable in place:
   `docs/builder/bld-040-slice-6-code_remediation.md:888` carries
   `scripts/prove_failability.py`'s own `<fill in …>` explanatory line** inside a prior
   `### Failability proofs` block. Source: Slice 6 W1 passes 1 and 2. Re-read this pass:
   it is the tool's instruction sentence, and the file carries **no** unfilled
   placeholder (`why 0:` is answered on every entry — no entry is zero-row).
   [`ARTIFACT.md`][artifact-md] forbids editing a prior entry, so it stays. **For the
   maintainer's awareness only.**

#### B. Closed with a recorded decision, or a correction of record — do not re-open

8. **The `_declare_group_type` / `_declare_user_type` per-file pairs are accepted
   duplication, not deferred.** Source: `### Ruling 1`, four recorded grounds. The
   condition that would change the answer is recorded with it: a third caller, or a
   decision to widen `tests/auth/_helpers.py`'s stated "plain (non-fixture) helpers"
   contract to registry-mutating declarations. Re-verified this pass: neither
   `_helpers.py` nor `conftest.py` is dirty.
9. **The `_LOGOUT_Q` tally: two prior entries in this artifact carry `11` -> `14`; the
   correct figure is `12` -> `15`.** Sources: `### Ruling 2`, the `## Build report
   (Worker 2)` before/after table, W3 `L1`, and pass 1's `### 1. Disposition …`.
   Licensing line: [`ARTIFACT.md`][artifact-md] "never edit prior entries". `11` is the
   count at HEAD; Slice 6 added one reader before the loop ran. Re-measured this pass:
   15 readers, 1 store.
10. **NEW — the line tally: `## Build report (Worker 2, pass 2)` `### Notes for Worker
    3` carries "three added lines and two removed"; the correct figure is 4 added and 2
    removed.** Sources: that section, W3 `L5`, and `#### L5` above. Same licensing line
    as entry 9. Nothing downstream reads the figure.
11. **NEW — the working-tree attribution in `## Review (Worker 3, pass 2)`
    `### Confirming the fence held` is wrong for two files.**
    `django_strawberry_framework/mutations/sets.py` and
    `django_strawberry_framework/mutations/resolvers.py` are attributed there to the
    concurrent `spec-050` session; they are **this cycle's** Slice 6 `F3` docstring
    fixes, proved by their diff content in `### 2` above. Same licensing line as entry
    9. **This is the one correction with a consequence for the commit** — the staging
    list is `### 7` below, not that paragraph.
12. **NEW — `tests/auth/test_mutations.py:1253` binds `model` where the file's other
    three user-model locals and the production parameter spell it `user_model`
    (`L4`).** Accepted by `#### L4` above, with its origin (this artifact's own pinned
    text) and its condition recorded: **if any later pass opens this file for another
    reason, rename it to `user_model`.** Not deferred work in its own right — no loop is
    owed for it.

---

### 7. What the maintainer is being handed

The cycle's fence was spec files and `.py` files. Nothing outside it was written, and
every attribution below is by **diff content**, not by "files a pass touched".

**Tracked, modified — 7 files, 391 insertions / 94 deletions:**

| File | Ins / Del | The change, in one line |
|---|---|---|
| `docs/SPECS/spec-040-auth_mutations-0_0_13.md` | 693 / 876 | The reconciliation: the deliberative layer cut to the companion, all 12 Decisions re-graded against shipped code, and the five cross-home divergences (`D1`-`D5`) closed |
| `django_strawberry_framework/auth/mutations.py` | 11 / 4 | Comment and docstring only — `CG-1`'s scoped `D-N3` comment plus the `F2` citation restatements; executable-token identical to HEAD |
| `django_strawberry_framework/mutations/resolvers.py` | 6 / 6 | Docstring only — `F2` (`spec-040 Revision-7 marker fix` attribution removed) and `F3` (`_bind_mutation` / `_bind_form_mutation` -> the live `bind_mutations` / `bind_form_mutations`) |
| `django_strawberry_framework/mutations/sets.py` | 7 / 7 | Docstring only — the same `F3` rename sweep plus `build_input`'s real caller, `bind_write_declarations` |
| `tests/auth/test_mutations.py` | 275 / 64 | The four `TEST-GAP` closures (`TG-0`-`TG-3`), the three DRY consolidations, and the two pinned Low edits |
| `tests/auth/test_queries.py` | 86 / 7 | `TG-3`'s `me` twin: a `groups`-exposing `_declare_user_type` seam, a `Group` type, and the strictness-visible unplanned-relation row |
| `examples/fakeshop/test_query/test_auth_api.py` | 6 / 6 | Docstring only — two `F2` citation restatements (`Revision 5` -> `Decision 6`; the `Revision 7 #3` attribution dropped, the invariant kept) |

**Untracked, new — the companion and the cycle's artifacts:**

- `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md` — 1,949 lines / 138,852
  B. The deliberative layer this spec never had, keyed decision by decision, with 16
  `**No longer claims:**` retractions. **Tracked-and-committed material, not scratch**
  ([`worker-1.md`][worker-1] `### Performing the rationale move`, rule 5).
- `docs/builder/build-040-auth_mutations-0_0_13.md` — the plan, 514 lines.
- `docs/builder/bld-040-slice-1…6` and `docs/builder/bld-040-integration.md` — the seven
  per-cycle artifacts; `bld-040-final.md` is the gate's, still to be written.

**Not this cycle's, and untouched by it** — the concurrent `spec-050` session's
`django_strawberry_framework/{list_field,orders/sets,utils/querysets}.py`,
`docs/GLOSSARY.md`, `docs/feedback.md`, `docs/spec-050-list_field_arguments-0_0_15.md`,
`docs/builder/bld-final.md`, `docs/builder/bld-slice-3-sql_and_unit_contracts.md`,
`examples/fakeshop/db.sqlite3`,
`examples/fakeshop/test_query/{test_list_field_api,test_list_field_async_api,test_multi_db}.py`,
`tests/orders/test_sets.py`, `tests/test_list_field.py`,
`tests/utils/test_querysets.py`. That set has moved three times during this artifact's
passes, which is why it is stated as measured at the end of this pass rather than
carried from the opening snapshot. **Nothing of theirs was reverted, checked out,
stashed or tidied** ([`AGENTS.md`][agents] rule 34).

**The shape of what shipped, for the commit message's benefit:** one archived spec
reconciled with the code that shipped it, its rationale companion created, **zero**
production behaviour changed (all three package files are executable-token identical to
HEAD), and seven new collected test node ids closing the four test gaps the audit
found — the only real source work the audit produced, since across the cycle's
**327** audited rows there was exactly **one** code gap and it was a missing source
comment. (327 re-derived from the four matrices rather than carried: Slice 2's 63 +
Slice 3's 91 + Slice 4's 122 + Slice 5's 51; the single `CODE-GAP` is Slice 4's.)

That figure, measured rather than carried: AST-derived module-level `test_*` functions
in `git show HEAD:<path>` against the worktree give `tests/auth/test_mutations.py`
97 -> 101 and `tests/auth/test_queries.py` 21 -> 22 — **six new functions and one
retired** (`TG-0`'s single `::test_sessionless_request_surfaces_djangos_own_error`
split into the `login` and `logout` pair), which is **seven** node ids once
`::test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem`'s
`[finalize]` / `[schema]` parametrization is counted, against one retired.

---

### 8. Verification, this pass

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md
OK: 30 terms - all have glossary entries and at least one spec link.        (exit 0)

$ uv run python scripts/check_citations.py --check
OK: 979 citations resolve (814 in 442 .py files, 165 in KANBAN.md).         (exit 0)

$ uv run pytest tests/auth/ examples/fakeshop/test_query/test_auth_api.py --no-cov -q
216 passed in 9.26s
```

`check_citations.py` runs whole-tree and so reads the concurrent session's dirty `.py`
files too; it is green at the same **979** Slice 6, the first integration run and pass 1
all recorded, so no citation moved. 216 = the 195 + 21 every pass since Slice 6 has
recorded. No `--cov*` flag anywhere; `--no-cov` because `pytest.ini` auto-applies
`--cov`.

**Anchors and the markdown link convention**, with a slug function implementing
[`START.md`][start]'s GitHub rule, headings taken from outside fenced blocks and code
spans stripped for the link census (double-backtick and line-wrapped spans both
handled):

| File | Headings | In-page uses | Unresolved | Ref uses / defs | Undefined | Unused | Def paths missing | Cross-file def anchors bad | Ten group headers, in order |
|---|---|---|---|---|---|---|---|---|---|
| `docs/SPECS/spec-040-auth_mutations-0_0_13.md` | 34 | 165 | **0** | 422 / 96 | 0 | 0 | 0 | 0 | yes |
| `docs/SPECS/appx/…-rationale.md` | 66 | 77 | **0** | 125 / 60 | 0 | 0 | 0 | 0 | yes |
| `docs/builder/bld-040-integration.md` | 128 | 0 | **0** | 64 / 7 | 0 | 0 | 0 | 0 | yes |

Instrument controlled: a copy of the spec with one bogus label and one bogus in-page
anchor appended reports `undefined: ['no-such-label']` and
`unresolved: ['no-such-heading']`, so the zeros are measurements. The artifact row is
its **post-write** state, re-measured after this section was inserted: a live count of
a population the pass is itself editing is the self-falsifying-instrument shape, and
the pre-write reading (114 headings, 50 reference uses) is stale by construction.
**Two further instrument notes, because both were false alarms I ran down to source
before writing anything.**
Taking headings from the code-span-stripped text makes every backticked Decision
heading slug wrong and reported **9 unresolved anchors that do not exist** — the
GitHub rule drops the backticks and keeps their contents, so heading slugs must come
from the raw line. And matching the ten group headers anywhere in the file rather than
inside the bottom block reported this artifact's scaffold out of order, because its own
prose quotes `<!-- docs/builder/ -->`. Both failures were in the safe direction; the
figures above are from the corrected instrument. The artifact's 128 headings against
pass 1's 69 is not drift either: pass 1 measured before the pass-2 build report, the
pass-2 review and this section were appended. Its repeated slugs (`### Files touched` ×2, `### Notes for Worker
1 (spec reconciliation)` ×4, and so on) are the template's per-pass sections, and the
file makes **0** in-page anchor uses, so nothing resolves through them.

**Pre-commit, over both files this pass writes** (the artifact and this role's
gitignored memory file), every path passed explicitly rather than through a shell
variable:

```shell
$ uvx pre-commit run --files docs/builder/bld-040-integration.md \
      docs/builder/worker-memory/worker-1-040.md
kanban tracked path constants ................ Passed
source layout (py trailing commas + ascii-only; md link-def scaffold; ...) Passed
ruff format .................................. (no files to check) Skipped
ruff check ................................... (no files to check) Skipped
kanban anchors collision-free ................ Passed
citations resolve (AGENTS.md rule 27) ........ Passed
```

Run twice with **no rewrite on either run** — the `source-layout` hook, which owns the
`.md` link-definition scaffold, left both files byte-identical across the two runs
(`md5` compared, not asserted). The two `Skipped` lines are genuine, since this pass writes no
`.py`, and they are a fact rather than the zsh word-splitting artifact because the path
was typed literally ([`START.md`][start] `## Instruments that lie`).

**Working-tree note (stop-and-report, no action taken).** `git status --short`, read at
the end of this pass, is the set enumerated in `### 7`. **Nothing was reverted, checked
out, stashed or tidied.** No `git stash` / `checkout` / `restore` / `worktree` ran
anywhere in this pass; every read-only HEAD reference (`git show HEAD:<path>` for the
three AST-identity comparisons) went to a scratch path outside the repository, and every
ruff-adjacent invocation named its paths explicitly, never `.`.

---

### Final status

`final-accepted`.

Both routed edits landed character-exact and are proved so; the three dispatched
consolidations and all five Low findings are closed — three of the Lows by a landed
fix, two by a correction of record made here. The divergence inventory holds after the loop: **1** scoped
survivor of `D1`'s retired claim and **0** on every other retired form, the protected
set five-membered everywhere, spec and companion agreeing 12 / 12 on Decision headings
and 16 / 16 on retractions, no citation into an edited region, `check_citations.py`
green whole-tree at the unchanged **979**, and **0** staged anchors in any `.py` behind
live controls. All four failability records are field-complete at 2 rows with 0
collection errors, entry 3 on four agreeing measurements, and all eight rows they name
are live in the collected set; no mutation survives and all three touched production
files are executable-token identical to HEAD. `check_spec_glossary.py` exits 0 at 30
terms; the focused suite is 216 passed; pre-commit passes with no rewrite on a second
run.

What the maintainer should read before committing is `### 7`, and then `### 2`: three
stated counts in this cycle's own prose were wrong and a fourth statement misattributed
two of this cycle's files to the concurrent session. Every one was caught by a later
pass re-deriving it, none changed a conclusion, and none touched the spec, the
companion or the shipped code — but the staging list in `### 7` is the one derived from
diff content, and it is the one to commit from.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[artifact-md]: ARTIFACT.md
[build-040]: build-040-auth_mutations-0_0_13.md
[build-md]: BUILD.md
[worker-1]: worker-1.md
[worker-3]: worker-3.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
