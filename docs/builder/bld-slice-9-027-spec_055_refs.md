# Build: Slice 9 — Catalog item 11: `spec-055`'s references to this card

Spec reference: `docs/SPECS/spec-027-filters-0_0_8.md` (Decision 2, lines 379-403; Decision 3, lines 404-481 — both at `HEAD`), discharged in `docs/SPECS/spec-055-search_fields-0_1_2.md`
Status: final-accepted

Cohort D of the catalog-discharge cohorts in `docs/builder/build-027-filters-0_0_8.md` `### Catalog-discharge cohorts (added 2026-08-20, post-commit 8a9840dc)`. Declared file partition: `docs/SPECS/spec-055-search_fields-0_1_2.md` only, plus this artifact. Catalog item 11 from `docs/builder/bld-final-027.md:108`.

`spec-055` was clean at `HEAD` before this pass (`git diff HEAD --stat` empty), so `HEAD` is the pre-pass baseline for every before-text below.

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked.** Not applicable — this pass touches no `.py` file and proposes no helper, constant, validation branch, or test helper. The whole diff is prose inside one spec.

- **Existing patterns reused.** The corrected attribution reuses the exact phrasing the cohort's `.py` repairs settled on: `django_strawberry_framework/filters/inputs.py` #"spec-027 Decision 2" (above `LOOKUP_PREFIXES`) and `django_strawberry_framework/filters/sets.py` #"landed with spec-027" (inside the staged anchor). Three sites now say the same thing in the same words.
- **New helpers justified.** None.
- **Duplication risk avoided.** `spec-055` states the same attribution twice (opener line 29, `## Current state` line 195). A one-site fix would have left the file self-contradicting; both are corrected in the same pass.

### Implementation steps

1. Re-derive the Decision-range measurement against `git show HEAD:docs/SPECS/spec-027-filters-0_0_8.md` (below) rather than transcribing Worker 0's claim.
2. Read the real staged anchor at `django_strawberry_framework/filters/sets.py` #"TODO(spec-055 Slice 1)" and its enclosing symbol.
3. Correct the two `Decision 3 Layer 5` attributions and the quoted `TODO(...)` anchor.
4. Sweep `spec-055` for further `spec-027` references, bare `Decision N` attributions, `#"substring"` citations, and link-definition health.

### Test additions / updates

None. No `.py` file, no test, and no runtime behavior is in this partition.

### Implementation discretion items

None.

### Dispatched findings checklist

- [x] Line 29's `spec-027 Decision 3 Layer 5` attribution corrected to the measured owner.
- [x] Line 195's identical attribution corrected the same way.
- [x] Line 200's quoted `TODO(...)` anchor made to match the anchor that exists in `filters/sets.py` at `HEAD`.
- [x] Full sweep for further wrong `spec-027` references, bare `Decision N` attributions, and moved `#"substring"` citation targets.
- [x] `[spec-027]` link definition checked for correct filename and for use.

---

## Build report (Worker 2 role, performed by Worker 1 under the cohort-D partition)

### Files touched

- `docs/SPECS/spec-055-search_fields-0_1_2.md` — four prose corrections (three dispatched, one surfaced by the mandated sweep). Net -1 line.

No other path in the writable set changed; nothing outside it was opened for writing.

### The Decision 2 vs Decision 3 measurement

Measured against `git show HEAD:docs/SPECS/spec-027-filters-0_0_8.md` (the spec is committed at `8a9840dc` and clean, so `HEAD` and the working tree agree).

Heading line numbers, located by `grep -n '^### Decision '`:

| Heading | Line | Range measured |
| --- | --- | --- |
| `### Decision 2 — Subpackage layout and public export surface` | 379 | 379-403 |
| `### Decision 3 — Six-layer lazy-resolution pipeline` | 404 | 404-481 |
| `### Decision 4 — Upstream-primitives parity floor` | 482 | (range terminator for Decision 3) |

Occurrence counts inside each range, by `sed -n '<range>p' | grep -o 'construct_search\|LOOKUP_PREFIXES'`:

| Range | `construct_search` | `LOOKUP_PREFIXES` | Total |
| --- | --- | --- | --- |
| Decision 2, 379-403 | 1 | 1 | **2** |
| Decision 3, 404-481 | 0 | 0 | **0** |

Both Decision-2 occurrences are on line 387, the `inputs.py` bullet of the subpackage-layout enumeration, which names `construct_search` and `LOOKUP_PREFIXES` ("the `^` / `=` / `@` / `$` search prefixes") as that module's contents. This reproduces the count `docs/builder/build-027-filters-0_0_8.md` `*Partition correction 2, 2026-08-19:*` recorded for the `filters/inputs.py` repair — same ranges, same 2-vs-0.

**What Decision 3's Layer 5 actually is**, read rather than assumed: "Layer 5 — BFS schema build with module-global materialization (Strawberry-adapted)", the port of `django_graphene_filters/filter_arguments_factory.py::FilterArgumentsFactory._ensure_built` plus the module-path-only lazy forward reference. It is the only one of the six layers that is Strawberry-adapted, which is plausibly why it attracted the misattribution; it has nothing to do with search prefixes. Decision 3 mentions neither symbol anywhere in its 78 lines.

Elsewhere in `spec-027` the two symbols appear at lines 26, 64, 102, 162, 387, 795, 806, 829, 856, 950, 951, 959, 977 — glossary references, the slice checklist, the borrowing posture, the test plan, the DoD. None of those sites is inside Decision 3 either.

### The real `TODO(...)` anchor at `HEAD`

`grep -n 'TODO(' django_strawberry_framework/filters/sets.py` returns exactly one hit, identical in the working tree and at `HEAD` (line 1369 in both):

```
# TODO(spec-055 Slice 1): Meta.search_fields - wire
# `construct_search(all_filters)` from
# `django_strawberry_framework.filters.inputs.LOOKUP_PREFIXES` here.
# The prefix map and `construct_search` landed with spec-027
# Decision 2; spec-055 owns the consumer surface.
```

So `spec-055`'s quotation was wrong twice over: the anchor names `spec-055 Slice 1`, not `spec-027-filters-0_0_8`, and it has never carried the `card 0.1.2` suffix the spec attributed to it. The anchor itself carries the corrected `Decision 2` attribution, so the spec was contradicting the very comment it quoted.

Enclosing symbol, resolved by AST: the comment sits at line 1369 inside `django_strawberry_framework/filters/sets.py::FilterSet.get_filters` (1267-1410), specifically in its nested `_build` closure (1305-1396). `spec-055`'s containing reference `filters/sets.py::FilterSet.get_filters` is therefore correct and is left as written.

### Edits, exact before and after

**Edit 1 — opener, line 29.**

Before:

```
`construct_search` (landed by spec-027 Decision 3 Layer 5 under a broad
future-search reservation that Slice 1 retargets to card 056) and the
```

After:

```
`construct_search` (landed by spec-027 Decision 2 under a broad
future-search reservation that Slice 1 retargets to card 056) and the
```

**Edit 2 — `## Current state`, line 195.**

Before:

```
  landed with spec-027 Decision 3 Layer 5 under a broad future-search
  reservation. Canonical card 055 subsequently narrowed this card to basic
```

After:

```
  landed with spec-027 Decision 2 under a broad future-search
  reservation. Canonical card 055 subsequently narrowed this card to basic
```

**Edit 3 — `## Current state`, lines 199-202, the quoted anchor.**

Before:

```
- `filters/sets.py::FilterSet.get_filters` carries a
  `TODO(spec-027-filters-0_0_8 Meta.search_fields card 0.1.2)` comment at
  the point where prefix translation was originally imagined to wire in.
  This spec supersedes that placement
  ([Decision 1](#decision-1--search-support-lives-in-filterssearchpy-not-inside-filterset));
  Slice 1 removes the TODO.
```

After:

```
- `filters/sets.py::FilterSet.get_filters` carries a
  `TODO(spec-055 Slice 1)` comment directing prefix translation to wire in
  there. This spec supersedes that placement
  ([Decision 1](#decision-1--search-support-lives-in-filterssearchpy-not-inside-filterset));
  Slice 1 removes the TODO.
```

The sentence stays true of the corrected quotation: the anchor asks for the wiring at that point, `### Decision 1 — Search support lives in filters/search.py, not inside FilterSet` rejects that placement, and Slice 1 removes the comment rather than implementing it there. The "originally imagined" clause went with the replacement because a spec's `## Current state` describes what the tree holds, and the anchor now names this spec's own Slice 1.

**Edit 4 — `### Decision 8`, line 827. Surfaced by the mandated sweep, NOT dispatched. See the flag below.**

Before:

```
same reading spec-053 Decision 8 pinned for `fields_class`, and 057's own
title ("Layer 3 Meta key promotion") describes the sweep, not ownership of
```

After:

```
same reading spec-054 Decision 8 pinned for `fields_class`, and 058's own
title ("Layer 3 Meta key promotion") describes the sweep, not ownership of
```

### The full sweep for additional bad references

Every item below is a measurement, not an inspection-by-eye.

**1. All `027` occurrences in `spec-055`** (`grep -n 'spec-027\|027'`): five sites — lines 26, 29, 195, 200, 1719. Line 26's `DONE-027-0.0.8` card id is correct (`KANBAN.md:63` confirms the Filtering subsystem shipped as `DONE-027-0.0.8`); the middle three are the dispatched defects; line 1719 is the link definition covered below. **No sixth `spec-027` reference exists.**

**2. `#"substring"` citations into `spec-027`** (`grep -n '#"'`): **zero hits in the entire file.** `spec-055` carries no `#"substring"` citation of any kind, into any file, so the rationale extraction to `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` broke nothing here. That is the one vector this repo has no instrument for — `scripts/check_citations.py` resolves `path::Symbol` only and excludes `docs/` — and it is empty by measurement rather than by assumption.

**3. Bare `Decision N` / `Layer N` attributions** (all 60+ occurrences enumerated by script, then filtered to those not resolving to an in-page `[Decision N](#decision-N--…)` link):

- The large majority are bare in-document references to `spec-055`'s own Decisions 1-14 — the file's house style throughout `## Edge cases`, `## Test plan`, `## Risks`, and the DoD. Correct as written; untouched.
- **`spec-030 Decision 6`** at lines 348 and 543-544, both glossed "the synthesized resolver signature IS the SDL contract". Verified: `docs/SPECS/spec-030-connection_field-0_0_9.md:393` is `### Decision 6 — Sidecar-derived arguments via a synthesized resolver signature`. **Correct, both sites.**
- **`spec-053 Decision 8`** at line 827, glossed as the reading "pinned for `fields_class`". **FALSE.** `docs/SPECS/spec-053-graph_substrate-0_1_1.md:847` is `### Decision 8 — FieldDependencyPlan normalizes Meta.depends_on`; `grep -n fields_class` over that whole spec returns two hits, a glossary link and its definition, and no decision. The `fields_class` promotion decision is `docs/SPECS/spec-054-fieldset-0_1_1.md:570` `### Decision 8 — Meta.fields_class promotes in this card` — same decision number, off-by-one spec, the signature of the 2026-07-30 card renumber. Corrected in edit 4.
- **`057`** in the same sentence, glossed by title as "Layer 3 Meta key promotion". **FALSE.** `KANBAN.md:835` gives `TODO-BETA-058-0.1.3 - Layer 3 Meta key promotion`; `KANBAN.md:766` gives `TODO-BETA-057-0.1.3 - Aggregation subsystem`. The same sentence's two preceding clauses already say `TODO-BETA-058-0.1.3` twice, so the paragraph contradicted itself. Corrected in edit 4.
- Corroboration for edit 4 from inside the file: `## Risks and open questions` line 1560 already reads "exactly as it was for `fields_class` in spec-054". The spec's two halves disagreed; they now agree, and the surviving half is the one the KANBAN and both sibling specs support.
- `TODO-BETA-054-0.1.1` at line 831 (the other `DEFERRED_META_KEYS` member's card) is correct: 054 is the `FieldSet` / `Meta.fields_class` card.
- `spec-043` at line 1286 (`TestClient` helpers) names no decision; the file exists. Correct.

**4. Quoted code strings in the neighborhood of the dispatched sites**, checked because a quotation of code is the defect class of edit 3:

- `connection.py::_synthesized_signature` docstring's "The `search:` argument is NOT generated (search is `0.1.2`)", quoted at lines 31-32 and again at 546-547. **Present at `HEAD`**, at `django_strawberry_framework/connection.py` lines 1694-1695, inside `_synthesized_signature` (1682-1744). The spec renders the source's RST double backticks as single backticks, which is the file's normal convention. Correct; untouched.
- `types/base.py::DEFERRED_META_KEYS` "contains `{"aggregate_class", "fields_class", "search_fields"}`" (line 187). Verified against `git show HEAD:django_strawberry_framework/types/base.py` lines 65-67 — exactly those three, in that order. Correct. (The working-tree copy is the spec-028 session's, not read for this claim.)
- `exceptions.py` "names `search_fields` in its reserved-key docstring" (line 191). Verified: `django_strawberry_framework/exceptions.py:209`. Correct.
- `filters/inputs.py::LOOKUP_PREFIXES` prefix map "`^` -> `istartswith`, `=` -> `iexact`, `@` -> `search`, `$` -> `iregex`" (lines 193-194). Matches `spec-027:162` and the live constant. Correct.

**5. Link-definition health** (script-checked, whole file): 34 definitions, 0 undefined uses, **3 orphan definitions** — `[spec-027]` (line 1719), `[spec-030]` (1720), `[spec-043]` (1721). Each resolves to a file that exists on disk: `docs/SPECS/spec-027-filters-0_0_8.md`, `spec-030-connection_field-0_0_9.md`, `spec-043-test_client-0_0_14.md`. So the `[spec-027]` definition's **filename is right and it is unused**. See the deliberate non-repair below.

### Deliberately left alone, with reasons

- **The three orphan link definitions** (`[spec-027]`, `[spec-030]`, `[spec-043]`). All three siblings are mentioned in `spec-055` as plain prose ("spec-027 Decision 2", "spec-030 Decision 6", "spec-043 `TestClient`"), never as markdown links — a consistent file-wide pattern with three matching unused definitions. Consuming only `[spec-027]` would leave one of three same-shaped references marked up differently from its siblings, and converting all three is link-style editing of a document whose design is out of this cohort's scope. The definitions are harmless: every path resolves, `check_trailing_commas.py --check` passes, and no gate flags an unused definition. Reported rather than repaired.
- **"Slice 1 retargets the stale reservation wording"** (line 198) and **"under a broad future-search reservation that Slice 1 retargets to card 056"** (lines 29-30). Still true at `HEAD`: `filters/inputs.py` #"spec-027 Decision 2" reserves the prefix map "for the future `Meta.search_fields` card", i.e. card 055, while `### Decision 5 — Card 055 is icontains-only; shortcut prefixes fail loudly` gives the shortcut prefixes to card 056. The reservation's wording is genuinely still Slice 1's to retarget; only its Decision attribution was wrong.
- **`spec-055`'s own bare `Decision N` self-references.** In-document, correct, and the file's established style.
- **Everything about `spec-055`'s design** — the fourteen decisions, slice plan, test plan, risks. Untouched.

### Validation run

- `uv run python scripts/check_citations.py` -> `OK: 772 citations resolve (695 in 422 .py files, 77 in KANBAN.md).`
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-055-search_fields-0_1_2.md` -> `OK: 25 terms - all have glossary entries and at least one spec link.` (exit 0)
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-055-search_fields-0_1_2.md` -> exit 0, no output.
- No `ruff` run: no `.py` file in this partition.
- No `pytest`: `AGENTS.md` L15, and nothing executable changed.

`git status --porcelain` classification — the only path changed by this cohort is `docs/SPECS/spec-055-search_fields-0_1_2.md`:

| Path | Owner |
| --- | --- |
| `docs/SPECS/spec-055-search_fields-0_1_2.md` | **this cohort** |
| `django_strawberry_framework/consumers.py`, `routers.py`, `filters/factories.py`, `types/finalizer.py`, `types/relay.py` | cohort A (`bld-slice-6-027-wrapped_citations.md`) |
| `django_strawberry_framework/orders/sets.py` | cohort B (`bld-slice-7-027-raw_line_refs.md`) |
| `django_strawberry_framework/utils/inputs.py`, `orders/__init__.py`, `orders/factories.py` | cohort C (`bld-slice-8-027-decision_attribution.md`) |
| `django_strawberry_framework/types/base.py`, `orders/base.py`, `orders/inputs.py`, `tests/test_registry.py`, `tests/orders/*.py`, `examples/fakeshop/apps/library/orders.py`, `examples/fakeshop/test_query/test_library_api.py`, `docs/SPECS/spec-028-orders-0_0_8.md`, `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md`, `docs/builder/bld-slice-{1,2}-028-*.md`, `docs/builder/build-028-orders-0_0_8.md` | concurrent spec-028 session (`AGENTS.md` rule 34 — not read for writing, not reverted) |
| `docs/builder/build-027-filters-0_0_8.md` | Worker 0 |

`django_strawberry_framework/filters/inputs.py`, dirty in the session-start snapshot, reads clean now; its cohort landed. Not touched here either way.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; prose-only, no executable change.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- The corrected attribution is written as `spec-027 Decision 2` with no substring citation. `Decision 2`'s heading is unique in `spec-027` and the two symbol occurrences both sit in it, so a `#"substring"` suffix would add a second thing to keep true without adding precision — and a substring citation into a spec is exactly what the rationale extraction has already broken once in this cycle. Rule 27's `path #"unique substring"` form applies to source refs; this is a spec-to-spec decision cross-reference, the form `spec-055` already uses for `spec-030` and the form `filters/inputs.py` and `filters/sets.py` now use for the same fact.
- No citation added by this pass wraps a line: the longest addition is `` `TODO(spec-055 Slice 1)` comment directing prefix translation to wire in``, one line, no `#"` anywhere.
- Present tense throughout; no edit references this cycle, this slice, a finding, or a prior state of the text.

### Notes for Worker 1 (spec reconciliation)

**Escalated: edit 4 is outside the dispatched three.** The brief scoped catalog item 11 to the three `spec-027` references and told me to sweep for bare `Decision N` attributions "by measurement rather than assumption". The sweep measured two more false sibling attributions in one sentence of `### Decision 8` — `spec-053 Decision 8` for `spec-054 Decision 8`, and card `057` for card `058` — in the same file, of the same class (a wrong Decision number attributed to the wrong sibling spec), in the same propagation-source document, and contradicted by the file's own `## Risks` entry twelve hundred lines later. I fixed them in the same pass rather than reporting a partial claim fix. Worker 0 should confirm the widening; the four-line diff for edit 4 is isolated and reverts cleanly on its own if the partition is meant to be read strictly.

Neither `spec-053` nor `spec-054` nor `KANBAN.md` was written; the measurement is read-only against them.

---

## Final verification (Worker 1)

- Dispatched findings checklist: all five boxes `- [x]`; each contract landed in the diff above.
- DRY check: no duplication introduced; the two sibling statements of the same attribution were corrected together, and the wording matches the two `.py` sites the cohort's earlier passes repaired.
- Gates: `check_citations.py`, `check_spec_glossary.py`, `check_trailing_commas.py --check` all pass, recorded verbatim above.
- Spec reconciliation: the four corrections ARE the reconciliation; no further `spec-055` edit is owed by this cohort.
- Status-line re-verification: `spec-055` line 34 `Status: **PLANNED — no slice built yet.**` is still accurate — no slice of card 055 has been built, and this pass changes no slice state. The `0.1.2` joint-cut header (lines 1-7) and the `DONE-027-0.0.8` / `DONE-030-0.0.9` dependency line (26-27) are all still true at `HEAD`.
- Final status: `built` — cohort D's own verification is complete, but the `Status:` line above stays `built` for Worker 0's review of the edit-4 widening.

### Summary

Four prose corrections in `docs/SPECS/spec-055-search_fields-0_1_2.md`, the document the next author of this subsystem copies from. The `construct_search` / `LOOKUP_PREFIXES` attribution now names `spec-027` Decision 2 at both sites where `spec-055` states it (measured: 2 occurrences inside Decision 2's lines 379-403, 0 inside Decision 3's 404-481). The quoted staged anchor now matches the one comment that exists in `filters/sets.py`, `TODO(spec-055 Slice 1)`, dropping an id that named the wrong card and a `card 0.1.2` suffix the comment never carried. A sweep-surfaced fifth and sixth defect in one `### Decision 8` sentence — `spec-053` for `spec-054`, card `057` for card `058` — is corrected in the same pass and flagged as a widening. `spec-055` carries no `#"substring"` citation anywhere, so the rationale extraction broke nothing in it.

### Spec changes made (Worker 1 only)

- `docs/SPECS/spec-055-search_fields-0_1_2.md:29` — `Decision 3 Layer 5` -> `Decision 2`. Catalog item 11; the attribution is false by the 2-vs-0 range measurement above.
- `docs/SPECS/spec-055-search_fields-0_1_2.md:195` — same correction at the `## Current state` restatement; a one-site fix would leave the file self-contradicting.
- `docs/SPECS/spec-055-search_fields-0_1_2.md:199-201` — quoted anchor `TODO(spec-027-filters-0_0_8 Meta.search_fields card 0.1.2)` -> `TODO(spec-055 Slice 1)`, matching `django_strawberry_framework/filters/sets.py` #"TODO(spec-055 Slice 1)" at `HEAD`; the trailing clause reworded to present tense against the corrected quotation. Net -1 line.
- `docs/SPECS/spec-055-search_fields-0_1_2.md:827` — `spec-053 Decision 8` -> `spec-054 Decision 8` and `057's own title` -> `058's own title`. Surfaced by the mandated sweep, outside the dispatched three, escalated above.

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
