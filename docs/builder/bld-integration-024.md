# Build: Cross-slice integration pass (card `DONE-024-0.0.7`)

Spec reference: `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` and its companion
`docs/SPECS/appx/spec-024-django_trac_37064_hardening-0_0_7-rationale.md`
Status: final-accepted

HEAD at this pass: `ddf8bbaf` ("finish 23"), read at pass start with `git log -1`, not inherited from
any artifact. Every count below was measured while it was being written.

This cycle's product is **two documents plus a one-line docstring repair**, not a subsystem, so
`docs/builder/BUILD.md` `## Cross-slice integration pass` is followed with its shadow-overview steps
adapted rather than skipped silently — each adaptation is recorded with its reason.

## 1. Every artifact read, in slice order

All four read in full, including every review and re-review section, per the section's "No 'as
needed'" rule.

| Artifact | `Status:` at this pass |
|---|---|
| `docs/builder/bld-slice-1a-024-planned_vs_head.md` | `final-accepted` |
| `docs/builder/bld-slice-1b-024-divergence_and_floor.md` | `final-accepted` |
| `docs/builder/bld-slice-3-024-rename_rot_sweep.md` | `final-accepted` |
| `docs/builder/bld-slice-2-024-spec_reconciliation.md` | `final-accepted` (set by this cycle's Slice 2 final verification, immediately before this pass) |

## 2. Static inspection — recorded skip, not a silent omission

`scripts/review_inspect.py` is **not owed by this cycle and was not re-run at this pass.** The
section's step 2 asks that it ran or was explicitly skipped with a recorded reason, "for every Python
file with review-worthy logic the build touched". This build touched exactly one Python file:

```shell
git diff HEAD --name-only -- '*.py'
# django_strawberry_framework/_strawberry_patches.py     <- this cycle's, Slice 3
# django_strawberry_framework/optimizer/hints.py         <- a concurrent cycle's
# examples/fakeshop/apps/scalars/models.py               <- a concurrent cycle's
# examples/fakeshop/test_query/test_scalars_api.py       <- a concurrent cycle's
# tests/optimizer/test_hints.py                          <- a concurrent cycle's
```

Four of the five are a concurrent session's uncommitted work and are not this build's diff
(`AGENTS.md` rule 34); the list grew by two during this pass, which is normal on this tree and is
why it is quoted as read rather than inherited.

and the change to it is **one line inside a module docstring** — a citation repaired from
`_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` to `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES`. No
logic was added to any file, so `docs/builder/BUILD.md` `### When to run the helper during build`'s
trigger (a plan that *adds logic* to an existing 150+ line file, or to anything under `optimizer/` or
`types/`) is not met. The build plan's own pre-flight step 2 records the helper running clean over
`django_strawberry_framework/_django_patches.py` at cycle start, which is the file the cycle is
*about*; nothing since has changed it.

**Skip reason, stated once so it is auditable:** a docstring citation repair introduces no branch,
no boundary, and no call, so an AST/text inspection of the file has nothing new to report.

## 3. Steps 3 and 4 — shadow overviews: adapted, with the substitute performed

Steps 3 (compare **Repeated string literals** across every shadow overview) and 4 (compare
**Imports** across them) both presuppose per-slice shadow overviews of changed Python modules. This
cycle produced none, because no slice changed Python logic: three of its four slices are read-only
audits and the fourth is the one-line docstring repair. Running `review_inspect.py` over the six
unchanged surface files to manufacture overviews would compare a file against itself.

**The substitute, performed:** the DRY / consistency scan below is run over the corpus this cycle
actually produced — the two permanent documents and the four artifacts — which is where duplication
and drift can exist here. Recorded as an adaptation rather than a pass.

## 4. DRY / consistency scan across the two permanent documents and the four artifacts

### 4a. Does the spec restate the deliberation the rationale owns?

**No.** Measured over the spec as it stands, occurrences not matching lines, whole tokens:

| Probe | Spec |
|---|---|
| backticked 8-hex commit tokens | **0** distinct (27 in the rationale) |
| `originally` / `as of` / `revision history` / `amendment` | **0** |
| `_PATCH_APPLIED`, `_missing_symbol_logged`, and the two retired test names | **0** each (all four live only in the rationale) |
| `Alternatives considered` / `rejected alternative` headings | **0** (11 such sections in the rationale) |

Every spec Decision closes with a one-line `Rationale companion — …: [Decision N][rationale-dN]`
pointer instead of carrying the deliberation. That is the `spec-023` house shape and it is applied
uniformly across all eleven.

### 4b. Does the rationale restate the contract the spec owns?

**No, with three deliberate mechanism overlaps, each reviewed and each kept.** The rationale states
no `Pinned by …` test list, no error-shape table, no `## Definition of done`, no API signature and no
worked consumer example — those exist only in the spec. Three mechanisms are stated on both sides:

1. **The `hasattr` discriminator's feature-list mechanism** (spec `### Decision 5`, rationale
   `## Decision 5` `### Derivation`). Kept on both sides deliberately, and Slice 1b asked for exactly
   this: the spec states it as a **prohibition on a future implementation** ("never `hasattr(cls, …)`
   … the `hasattr` form looks more robust and is not"), the rationale states it as **the reason a
   shipped feature was renamed a bug ten days later**. A contributor reaching for the "simplification"
   reads the spec; a reader asking why reads the rationale. Removing either half loses a different
   reader.
2. **The reimplement-vs-delegate consequence** (spec `### Decision 3` closing paragraph, rationale
   `## Decision 3` first rejected alternative). Same split: contract ("a future contributor who
   removes the pin must first make the patch delegate") vs. the rejection and its standing cost.
3. **The non-interpolating `TypeError`** (spec `### Decision 8`, rationale `## Decision 8` third
   rejected alternative). Contract plus one-clause reason vs. the shipped-then-reversed history.

**Drift risk named rather than waved through:** these three are the only sentences in the corpus that
could drift apart, and all three are anchored to the same source text — the mechanism lives in
`django_strawberry_framework/_django_patches.py`'s own comments and docstrings, which both documents
cite rather than paraphrase. That is the reason to keep them, and it is recorded here so a later
reader knows the overlap was measured and decided, not missed.

### 4c. Naming and terminology, spec vs. rationale

Swept the vocabulary that could plausibly diverge. Every pair agrees:

| Term | Spec | Rationale |
|---|---|---|
| the two halves | "unwrap-time half" / "wrap-time half" | same |
| the pinned constant | `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` (plural, current) | same; the retired singular appears only inside a retired-claim bullet |
| the gate | `APPLY_UPSTREAM_PATCHES`, "escape hatch", "opt-out" | same |
| the widening rule | `WIDENING THIS SET IS AN AUDIT, NOT A VERSION BUMP` | verbatim identical, and identical to the source comment |
| the import path | `django_strawberry_framework.testing` | same; `….test` appears only as a retired claim |
| the three stamped names | 2 attribute-name constants + 1 owner **value** | same distinction, same words |

### 4d. Facts stated twice that could drift apart — enumerated and reconciled

Four, all consistent at this pass:

- **The audited-set size and its Django ranges.** Spec `### Decision 5` table (`5.2.16` - `6.0.x`;
  `6.1`) and rationale `## Decision 5` `### Derivation`. Agree.
- **31 owned / 36 run scope.** Spec `## Test plan` (twice) and `## Definition of done` item 9;
  rationale does not restate either number. Re-derived at this pass: `tests/test_apps.py` holds
  **5** tests at `300e2811^` and **8** at HEAD, `tests/test_django_patches.py` **21**,
  `tests/testing/test_wrap.py` **7**; 21 + 7 + 3 = **31**, 21 + 7 + 8 = **36**. Both reproduce.
- **The 21-commit surface population, 6 in-tag / 15 post-tag.** Rationale `## Change record`
  preamble and its table; the spec states no population. The table has 21 rows, of which 6 read
  `in 0.0.7` and 15 read `post-tag` — re-counted at this pass from the file, and the split sums.
- **The floor triple.** Spec `### Floor verification` (Django `5.2.16` / Python `3.10` /
  strawberry-graphql `0.316.0`) and rationale `## Verified against the shipped code`. Both agree with
  `docs/builder/BUILD.md` `## Floor verification`, the single canonical statement, which is where
  this pass read them from.

### 4e. Claims in one artifact that contradict a claim in another

One found, already reconciled on disk before this pass; recorded because the reconciliation is the
finding:

- **`docs/TREE.md`'s summary-line population.** `bld-slice-1b` states **two** module summary lines;
  `bld-slice-2`'s catalog item 3 states **six distinct lines / twelve occurrences** and says in place
  that it re-derived rather than copied. Re-derived independently at this pass by extracting each
  module's own docstring first line with `ast.get_docstring` and counting its occurrences in
  `docs/TREE.md`: `_django_patches.py` 2, `apps.py` 2, `testing/_wrap.py` 2, `tests/test_apps.py` 2,
  `tests/test_django_patches.py` 2, `tests/testing/test_wrap.py` 2 = **6 lines, 12 occurrences**.
  Slice 2's figure is correct and 1b's is superseded. Provenance also confirmed: `4a25bf42` sets the
  three package modules' first lines and `7c2a63ed` the three test modules'.

That contradiction is what exposed the one spec defect this pass fixed (below).

No other cross-artifact contradiction found. Specifically checked and consistent: the change-record
start point (1a's baseline reading is recorded as *rejected*, not asserted, everywhere it appears
after Slice 2's decision); the retired-name population (nine names, all at 0 whole-token occurrences,
agreed by Slice 3 and its review); the `12 -> 13` vs `13 -> 13` progression correction (agreed by 1a,
1b, and the rationale); and the `1,618`-byte stub figure (agreed everywhere; `1,536` survives only
inside the finding that raised it).

### Spec changes made (Worker 1 only)

**One edit, to `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md`.** Cause: scan item 4e.

The spec stated the `docs/TREE.md` regenerate obligation over **three** modules —
`_django_patches.py`, `apps.py`, `testing/_wrap.py` — at two sites: the `## Key glossary references`
project-conventions bullet for `docs/TREE.md`, and the `## Edge cases and constraints` bullet
"**`docs/TREE.md` is a downstream consumer**". The measurement in 4e shows **six** of this card's own
surface modules feed `docs/TREE.md`, the other three being `tests/test_django_patches.py`,
`tests/testing/test_wrap.py`, and `tests/test_apps.py`. A docstring edit to any of those three
strands the rendered doc exactly as an edit to the package three does, so the obligation as written
was true but incomplete about the card's own surface. Both sites now name all six.

This is **distinct from deferred-catalog item 3**, which is about *stale summary lines already in
`docs/TREE.md`* and remains deferred (`docs/TREE.md` is outside this cycle's maintainer-set scope).
This edit changes only what the spec *states as an obligation* about the card's own modules, which is
squarely spec surface and squarely Worker 1's.

Gates re-run after the edit: `check_spec_glossary.py --spec …spec-024…` -> `OK: 2 terms`, exit 0;
`check_trailing_commas.py --check` over both permanent files -> exit 0, silent; `git diff --check --
docs/SPECS/` -> clean. No link def added or removed, so the def block is untouched and still
0-undefined / 0-unused.

## 5. Staged-anchor sweep (step 6), run verbatim

```shell
grep -rEn 'TODO\(spec-024|TODO-(ALPHA|BETA|STABLE)-024' .
```

Excluding `.git/` and the three board files the section exempts (`KANBAN.md`, `KANBAN.html`,
`BACKLOG.md`, where `TODO-<MILESTONE>-<NNN>` legitimately names unshipped cards — measured at **0**
hits there anyway), the sweep returns **exactly one hit**:

```
examples/fakeshop/test_query/test_kanban_api.py:1268:    "cardId": "TODO-ALPHA-024-0.0.8",
```

**Not a staged anchor; no work is owed.** Read in context: it is an expected-value string inside a
GraphQL response assertion in `test_ready_cards_includes_an_unblocked_todo_card`, checking a
**fictional seeded board** built by that module's `_seed_board()` helper. The sibling row in the same
literal is `"DONE-021-0.0.8"`, and the card titles are "Filtering subsystem" and
"DjangoConnectionField" at version `0.0.8` — a synthetic fixture exercising the example kanban app's
`isReady` / `isBlocked` computation, unrelated to card `DONE-024-0.0.7` (which shipped at `0.0.7`).
The token collides with the sweep's pattern because the sweep matches any `024`, which is the correct
instrument; the triage is reading the site.

**No `TODO(spec-024 slice N)` anchor exists anywhere in the tree.** Nothing to discharge, nothing to
route back to a slice.

## 6. Deferred follow-up in the artifacts that should land here rather than in the catalog

Walked all four artifacts' `What looks solid`, `DRY findings`, and `Notes for Worker 1` sections.
Everything found is one of: already landed, correctly catalog-bound, or a maintainer decision.

- **Landed, verified at this pass:** 1a's item 7 plural correction, item 9's no-count `__all__`
  instruction, the L1 wording replacement, and the `1,618` figure (all four honoured in the rewritten
  spec); 1b's nine `**Facts for the spec**` and its non-transferable-`path:NN` instruction (the spec
  carries **0** raw `path:NN`, measured); Slice 3's three spec/rationale recommendations (plural
  constant named in the spec, singular "the superseded body" confined to the rationale's retired
  claims, `WIDENING THIS SET IS AN AUDIT, NOT A VERSION BUMP` verbatim in both).
- **Correctly catalog-bound, not landable here:** every item in `bld-final-024.md`'s
  `### Deferred work catalog`. Each is outside this cycle's maintainer-set scope (spec files and
  `.py` only) or outside card 024's ownership; none is a cross-slice DRY defect this pass could close.
- **1a item 22** (the planning documents' dead `django_strawberry_framework/test/…` and `tests/test/…`
  paths must not be inherited into spec text) is **discharged, not deferred**: the spec's only
  occurrence of the `….test` path is the settled-contract sentence in Decision 9 saying the path is
  never that, and the rationale's only occurrences are inside retired-claim bullets. Verified whole-token
  at this pass.
- **Slice 3's `Escalated:`** (no gate resolves a symbol citation) is contract-level and no worker's
  call; it stays in the catalog with its three paths intact, as `docs/builder/BUILD.md`
  `### Contract-level findings are escalated as maintainer decisions before dispatch` requires.

## Integration findings

**None requiring a builder.** No duplicated helper (no helper exists), no inconsistent naming or error
handling between slices, no repeated ORM/queryset pattern, no misplaced responsibility between
modules, no export change (`git diff HEAD -- django_strawberry_framework/__init__.py` is empty), and
no repeated literal or key introduced by this cycle. The one cross-artifact inconsistency found
(4e) was a superseded count, and the one spec defect it exposed is fixed above under Worker 1's own
spec-reconciliation authority rather than dispatched — it is a two-clause edit to a document only
Worker 1 may write, with no code, test, or contract consequence.

## DRY findings

None. The two permanent documents partition cleanly into contract and deliberation, with the three
mechanism overlaps of 4b reviewed and deliberately kept.

Status: final-accepted.

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
