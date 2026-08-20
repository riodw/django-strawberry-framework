# Build: Cross-slice integration pass — filters / 0.0.8 (027)

Spec reference: `docs/SPECS/spec-027-filters-0_0_8.md` (whole file; this pass edited seven sites across `## Slice checklist`, `## Non-goals`, `## Borrowing posture`, `## Architectural decisions`, `## Doc updates`, and `## Risks and open questions`)
Status: final-accepted

## Plan (Worker 1)

### Worker-1-only artifact shape

The integration pass is Worker 1's by [`BUILD.md`][build] `## Cross-slice integration pass` ("Worker 1 runs the integration pass and produces `docs/builder/bld-integration.md`"). It carries a combined Plan + Final-verification block, like this cycle's Slices 1 and 3, because the only two files it may write are the spec and its rationale — Worker-1-exclusive surfaces per [`BUILD.md`][build] `## Spec reconciliation` and the `## Required reading per worker` matrix. Code findings are routed to Worker 0, not fixed here.

Artifact path is `bld-integration-027.md` rather than `bld-integration.md`, per the build plan's recorded pre-flight deviation: three concurrent sessions' `bld-*.md` artifacts are live on this tree and were not reset, so this cycle suffixes every artifact with `-027`.

### Spec status-line re-verification (Worker 1, every spawn)

Lines 1-9 of `docs/SPECS/spec-027-filters-0_0_8.md` read at the start of this pass. `Status:` now reads `shipped (`0.0.8`)` with the card id and what is on disk — Slice 3's replacement of the build-progress log, and accurate. `Target release`, `Owner`, and the rationale-companion pointer all resolve. `Predecessors` no longer carries the falsified `planned for 0.0.8` glossary claim. **No status-line edit owed by this pass.**

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately skipped, on the same ground Slices 1 and 3 recorded: [`BUILD.md`][build] `### Package-wide helper inventory before helper planning` gates *helper planning*, and this pass proposes no helper, shared constant, validation branch, coercion utility, or test helper. No `.py` file is in this pass's writable list.
- **Existing patterns reused.** The count-asserted batch replacement (apply only when the occurrence count matches an expected count; write nothing on any mismatch) is Slice 1's and Slice 3's instrument, reused verbatim for this pass's seven spec edits. The rationale entry's `**Claim retracted.**` shape is the file's own established form.
- **New helpers justified.** None.
- **Duplication risk avoided.** The characteristic failure of an integration pass is re-fixing what a slice already fixed under a slightly different spelling, leaving two statements of one contract. Prevented by re-deriving every finding against the files as they stand now rather than against the slice artifacts' descriptions of them — which is how the two false zero-claims in `### Corrections to this cycle's own recorded claims` surfaced.

### The six preconditions, and how each was satisfied

| # | Precondition ([`BUILD.md`][build] `## Cross-slice integration pass`) | How it was satisfied |
|---|---|---|
| 1 | Read every prior `bld-slice-*-027-*.md` in slice order | All three read end to end in order: `bld-slice-1-027-rationale_extraction.md` (165 lines), `bld-slice-2-027-citation_and_provenance_rot.md` (882 lines, including both Worker 2 build reports and the Worker 3 review), `bld-slice-3-027-spec_reconciliation.md` (252 lines). Not sampled — the Slice-2 per-site tables are what made the citation re-verification below possible. |
| 2 | `scripts/review_inspect.py` ran, or its skip is recorded, for every `.py` file with review-worthy logic the build touched | **Record verified on disk, not assumed.** `bld-slice-2-027-…md` `### scripts/review_inspect.py — recorded skip` states the skip and its reason ("This slice adds no logic to any `.py` file"; the helper's `<stem>.stripped.py` replaces every comment and string-literal token with `...`, so its output is identical before and after). Worker 3's `### scripts/review_inspect.py` section confirms the skip **against the actual diff** rather than against the plan. Slices 1 and 3 touch no `.py` file at all. |
| 3 | Compare **Repeated string literals** across every shadow overview | **Vacuous, with the reason stated rather than the step omitted.** `docs/shadow/` holds exactly one overview belonging to this build — `django_strawberry_framework__filters__factories.overview.md`, Worker 0's pre-flight step-2 smoke run. (The two `scalars` overviews are the concurrent `spec-026` session's and are not this build's output.) A cross-file literal comparison needs two overviews from one build; with one, there is no pair. Its section reads `- 2x `filterset``, a single-file repeat, not a cross-slice candidate. The deeper reason the step is empty: **the build added no executable statement, so no literal entered the tree.** |
| 4 | Compare **Imports** across every shadow overview for one-way dependency direction | Same population, same reason. The one overview's imports are `..utils.inputs` (the shared substrate, strictly below `filters/`), `.inputs`, and `.sets` (siblings) — one-way, no sibling reaching outside the documented boundary. No import statement changed anywhere in the build, so the direction at close is the direction at `HEAD`. |
| 5 | Walk every accepted artifact's `What looks solid` / `DRY findings` for deferred follow-up | Slice 2 is the only slice with Worker 3 sections. Its `### DRY findings` records `None against this diff` plus "two adjacent duplication classes … pre-existing at `HEAD` and outside every dispatched population", routed to `### Notes for Worker 1`; its `### What looks solid` records no deferral. Both routed classes are re-derived in `### Deferred work catalog (re-derived)` below, items 3 and 4. |
| 6 | Sweep the whole tree for staged anchors naming this build's spec **or** card, `027` and pre-renumber `021` alike | Run; **it is not clean, and two prior artifacts recorded that it was.** Full result and disposition in `### Staged-anchor sweep` below. |

### What this pass actually checked

The generic cross-slice list ([`BUILD.md`][build] `## Cross-slice integration pass`, second paragraph) mostly cannot bite a build that changed no executable statement: no helper was written, so none can be duplicated; no export moved; no ORM pattern was added; no literal entered the tree. The one item on that list with live risk here is **"whether comments now tell one coherent story across the new code"** — and it is where every finding below came from.

The cross-slice risk this cycle actually carries is a **citation whose target one slice moved and another slice rewrote**. Slice 2 rewrote `.py` comments that cite the spec; Slice 1 had already cut text out of the spec and Slice 3 then rewrote what remained. Each slice verified its own half:

- Slice 1 verified in-page anchors, cross-file anchors, link definitions, and the glossary gate — **all spec-internal or spec-to-rationale**.
- Slice 2 verified its `spec-027 Decision N` targets against the spec *as it stood mid-cycle*, and `check_citations.py` for the `path::Symbol` form.
- Slice 3 verified spec-named **test functions** and spec-named **package symbols**.

**No pass resolved a `#"unique substring"` citation from a `.py` file into the spec.** That form is gated by nothing — `scripts/check_citations.py` resolves `path::Symbol` only, and its docstring puts `docs/` deliberately out of scope. It is also the form most sensitive to exactly what this cycle did: a move deletes the target, a reword changes it, and a reflow breaks it without changing a word.

---

## Final verification (Worker 1)

- Cross-slice DRY: no new duplication. The three slices' file sets are disjoint (Slice 1: 2 `.md`; Slice 2: 19 `.py`; Slice 3: the same 2 `.md`). The live coupling is citation direction, checked below in both directions.
- Existing tests still pass: not run. This pass changes no executable statement; the gates below are what it can falsify. Slice 2's focused scope was run three times in-cycle (`1084 passed`, by Worker 2 twice and Worker 3 once) and again by Slice 2's final verification after its own edit.
- Spec reconciliation: performed as part of this pass, recorded under `### Spec changes made (Worker 1 only)`.
- Final status: `final-accepted`. The one code-side finding is routed to Worker 0 as a follow-up rather than blocking, for the reason stated in `### Why this is `final-accepted` and not `revision-needed``.

### Citation audit: `.py` -> spec, every occurrence

The instrument: for every `.py` file outside `.venv`, strip each line's leading `#` (so a citation wrapped inside a comment block reads as one string — Slice 2's own hard-won lesson), flatten whitespace, extract every `#"…"` citation whose preceding context names `spec-027`, and resolve the substring against the spec **with backticks normalized out of both sides**.

**The backtick normalization is not a detail.** Without it the instrument reports two additional failures in `filters/factories.py` that are not failures at all: those citations spell the identifiers in double backticks (`` ``FilterSet`` ``) where the spec uses single ones. A checker for this form that compares raw text manufactures findings. Indicting the instrument before the corpus caught it here, as it has in three prior passes of this cycle.

**Population: 13 citations. 10 resolve. 3 do not, and all three broke in this cycle.**

| Site | Citation | State |
|---|---|---|
| `django_strawberry_framework/filters/base.py::GlobalIDFilter` (the decode helper's docstring) | `spec-027 #"accept both raw"` | **Broken.** Resolves into `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md`, not the spec. |
| `django_strawberry_framework/filters/base.py::GlobalIDFilter` (the class docstring) | `spec-027 #"accept both raw"` | **Broken**, same target. |
| `django_strawberry_framework/types/finalizer.py::_bind_filterset_owner` | `spec-027 Decision 6 #"Partial-finalize lifecycle"` | **Broken.** Also resolves into the rationale. |
| `filters/base.py` x4, `filters/factories.py` x2, `types/finalizer.py` x4 | `#"Bind the owner."`, `#"rebuild ORM paths"`, `#"filter expects <expected> but received <actual>"`, `#"validates every element of the list independently"`, `` #"Auto-generation of ``FilterSet`` from ``Meta.fields``" `` x2, `#"owning `FilterSet`'s target `DjangoType`"` x2, `#"Relation traversal under"` | Resolve. |

**Cause, both cases: Slice 1's move, working exactly as designed.**

- `accept both raw` existed at `HEAD` in exactly one place — the `rev-8` revision-history bullet `M6 — Strawberry-specific GlobalIDFilter. The ported … now: (a) accept both raw `str` and …`. That block left the spec whole. The contract itself survives, in Decision 4's Strawberry-specific `GlobalIDFilter` block, spelled `Accepts both raw `str` and `strawberry.relay.GlobalID` objects`. **The citation was pinned to the narration rather than to the contract, so the move that was supposed to happen is what broke it.**
- `Partial-finalize lifecycle` was a bullet inside Decision 6's `Justification:` block — moved by definition. The surviving statement of the same contract is Decision 9's `**Partial-finalize recovery.**` bullet.

Recommended repairs (Worker 0's to dispatch; this pass may not touch `.py`):

- both `base.py` sites -> `spec-027 #"Accepts both raw"` (verified: 1 occurrence in the spec, in Decision 4);
- `finalizer.py::_bind_filterset_owner` -> `(supports partial-finalize recovery per spec-027 Decision 9)`, **dropping the substring**. `Partial-finalize recovery` occurs twice in the spec (Decision 9 and Decision 11), so it is not the unique substring rule 27 requires, and the Decision reference alone resolves for a reader.

### Citation audit: `.py` -> spec, the `Decision N` form

Every `spec-027 Decision N` reference in the tree was re-resolved against the spec **at its current state**, because Slice 3 rewrote Decisions 1 / 2 / 3 / 6 / 8 / 9 / 10 / 12 after Slice 2's targets were confirmed. The two with real exposure:

- **Decision 9 — rewritten from the cycle-safe local import to the `register_subsystem_clear` seam.** Seven sites cite it (`filters/inputs.py` x4, `filters/factories.py`, `utils/inputs.py`, `tests/orders/test_composition.py`) plus `tests/filters/test_finalizer.py`'s module docstring, whose sentence is the sharpest test: "`registry.clear()` runs without `ImportError` when the filters package was never imported (subprocess test pins the cycle-safe contract per spec-027 Decision 9)". **It holds.** The rewritten Decision 9 still states the cycle-safe contract — "only an imported owner can register, so a consumer who never imports `filters` has nothing to clear and `registry.clear()` does no work" — and the subprocess test is real (`tests/filters/test_finalizer.py` imports `subprocess` and runs one). The mechanism named in the spec changed; the property the comment claims did not.
- **Decision 8 — its step list was rewritten (steps 3 and 5 among them).** Four sites cite `Decision 8 step 3` (`filters/sets.py`, `types/finalizer.py` x2, `tests/filters/test_finalizer.py`). **All hold**: step 3 is still `**Nested `RelatedFilter` visibility scoping**`, and the spec's own new Subpass-2.5 paragraph cites the same step for the same contract.

Decision 3 Layer 2 and Layer 5, Decision 4, Decision 5, Decision 6, and Decision 7 all still exist and still state what their citing sentences claim; Decision 3 Layer 2 is the site Slice 2's final verification already retargeted, and the retarget still reads true after Slice 3's rewrite.

### Citation audit: spec / rationale -> everything else

The mirror direction, run because the spec cites standing docs by the same ungated form. One finding, and it is a self-contradiction inside the spec:

**Five spec sites cited `GOAL.md #"The existing django_filters.FilterSet plugs into Meta.filterset_class directly"`. `GOAL.md` has not said that since this card's own Slice 5 rewrote it** — the rewrite the spec's `## Doc updates` bullet ordered, whose replacement wording the spec quotes in full. So the spec ordered the sentence's removal in two places and cited it as `GOAL.md`'s live promise in three others (`## Non-goals`, `## Borrowing posture`, `## Risks and open questions`). Fixed here; see `### Spec changes made (Worker 1 only)` items 3-7. `AGENTS.md #"Test placement:"`, `AGENTS.md #"No CHANGELOG.md updates unless told"`, `KANBAN.md #"### In progress"`, `pyproject.toml #"django-filter>=25.2"`, `pyproject.toml #"version ="`, and `django_strawberry_framework/__init__.py #"__version__ ="` all resolve.

### Staged-anchor sweep

Run for both spellings and both card ids, `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` excluded:

```shell
grep -rEn 'TODO\(spec-027|TODO-(ALPHA|BETA|STABLE)-027' .
grep -rEn 'TODO\(spec-021|TODO-(ALPHA|BETA|STABLE)-021' .
```

- The `021` sweep returns **nothing**. Slice 2 retired the card's pre-renumber id from the whole `.py` surface, and no `TODO-…-021` form ever existed.
- The `027` sweep returns **five hits**: one in shipped source, two in other cards' archived specs, and two in this cycle's own artifacts.

| Hit | Disposition |
|---|---|
| `django_strawberry_framework/filters/sets.py::FilterSet.get_filters` #"TODO(spec-027-filters-0_0_8 Meta.search_fields)" | **Stays.** [`BUILD.md`][build] step 6 requires discharge of an anchor whose work **has landed**. This one stages `Meta.search_fields`, which has not shipped — it is in `DEFERRED_META_KEYS` at `HEAD` — and `docs/SPECS/spec-055-search_fields-0_1_2.md` names this exact comment and states "Slice 1 removes the TODO". The anchor names a shipped spec but stages unshipped work owned by an open card; removing it here would delete a live pointer that card depends on. **Two mismatches recorded for the catalog** rather than fixed: `spec-055` quotes the anchor as `TODO(spec-027-filters-0_0_8 Meta.search_fields card 0.1.2)` and the real comment carries no `card 0.1.2` suffix; and the anchor's spec id would be more useful naming the card that will ship it. `spec-055` is another card's spec and outside this cycle's fence. |
| `docs/SPECS/spec-031-globalid_encoding-0_0_9.md:25` | Prose recording that spec-031 **deleted** a `TODO(spec-027 Slice 1)` anchor from `types/relay.py`. A historical record of a discharge, not an anchor. Not a finding. |
| `docs/SPECS/spec-034-permissions-0_0_10.md:14` | Prose recording that a claimed stale `TODO-ALPHA-027-0.0.10` marker did not exist. Not an anchor. Not a finding. |
| `docs/builder/bld-slice-2-027-…md:845`, `bld-slice-3-027-…md:170` | The two false zero-claims. See below. |

### Corrections to this cycle's own recorded claims

Recorded here because a worker never edits a prior slice's artifact, and because a false zero propagates: the final gate reads these artifacts.

1. **Both Slice 2 and Slice 3 recorded that `grep -rn 'TODO(spec-027' .` "returns nothing outside this cycle's own artifacts".** It returns five hits, one of them in shipped package source (`filters/sets.py`), which contains the literal `TODO(spec-027` and cannot have been missed by the command as written. The claim is false in both artifacts; the anchor's **disposition** is nevertheless "stays", so nothing is owed to the tree — what is owed is the correction, because the next reader would otherwise inherit a zero for a population of one. Neither slice was the doc-wrap slice, so neither's obligation was to remove it; the obligation both discharged wrongly was to *report* it.
2. **Slice 3's `tests/filters/` census closed to "consistent across all three".** A fourth surface states the same enumeration — the `## Doc updates` `docs/TREE.md` bullet — and omitted the `fixtures/` sub-package that the other three and `docs/TREE.md` itself carry. This is the positively-spelled-census trap in its **population-selection** form: the census was true over the three sites the finding named and false over the sites that state the claim. Fixed here (item 1 below).
3. **Slice 3's deferred item 1 flagged its own sibling population as unaudited** ("I read four names off a `grep` and did not audit whether all four describe the retired shape"). Audited here: **all four do**, and `django_strawberry_framework/registry.py` contains zero `except ImportError` guards. Detail in the catalog.

### Verification performed by this pass

| Check | Command / instrument | Result |
|---|---|---|
| Glossary gate | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-027-filters-0_0_8.md` | `OK: 48 terms - all have glossary entries and at least one spec link.` exit 0 |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 740 citations resolve (665 in 422 .py files, 75 in KANBAN.md).` exit 0 — identical to Slices 2 and 3, so this pass added and removed no `path::Symbol` citation |
| Markdown scaffold (`source-layout` hook's checker) | `uv run python scripts/check_trailing_commas.py --check` on both `.md` files | exit 0 |
| Spec in-page anchors | slug-and-resolve over headings + `<a id=…>`, fenced code stripped | **162 refs, 0 dangling** |
| Rationale in-page anchors | same | **68 refs, 0 dangling** |
| Spec -> rationale cross-file fragments | resolve each `#fragment` against the rationale's anchors | 12 defs, **0 dangling** |
| Rationale -> spec cross-file fragments | resolve each `#fragment` against the spec's anchors | 21 defs, **0 dangling** |
| Link definitions, both files | used-vs-defined both ways + on-disk existence of every def target | no undefined, no unused, no broken path |
| Decision-heading parity | every `## Decision N —` heading in the rationale vs every `### Decision N —` heading in the spec | **12 / 12 identical text** — the rationale's `**Anchor keying**` claim holds |
| Spec-named test functions vs the tree | every `test_[a-z0-9_]+` token in the spec vs every `def test_…` in the tree | **88 names, 0 missing** (the one non-match is `test_query`, the directory name). The rationale's 16 non-matching names are all inside its retired-name mapping table and the moved revision history — the record of names that were replaced, which is what that table is for |
| `.py` -> spec substring citations | flatten + `#`-strip + backtick-normalize, resolve against the spec | **13 citations, 10 resolve, 3 do not** (the finding above) |
| `.md` -> other-file substring citations | same instrument over the spec and rationale | 1 broken (`GOAL.md`, fixed here); `AGENTS.md`, `KANBAN.md`, `pyproject.toml`, `__init__.py` all resolve |
| Scope fence | `git status --short -- docs/SPECS docs/builder` | the only files this pass modified are `docs/SPECS/spec-027-filters-0_0_8.md` and `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md`; all `spec-024*` / `spec-026*` / `build-025*` / `bld-*-025*` / `bld-*-026*` churn is the concurrent sessions', untouched |
| `.py` diff | `git diff --stat -- '*.py'` for this pass | empty |

### Byte and line counts

| File | Before this pass | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-027-filters-0_0_8.md` | 255,077 bytes / 1,113 lines | 254,798 bytes / 1,113 lines | -279 bytes / 0 lines |
| `docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` | 139,535 bytes / 730 lines | 143,887 bytes / 756 lines | +4,352 bytes / +26 lines |

Cycle-wide for the spec: 324,436 (`HEAD`) -> 254,798 (-69,638). The corpus ratchet in [`BUILD.md`][build] `## The corpus ratchet` binds edits to the six workflow documents; this pass touches none of them.

### Failability, fail-open, and floor confirmations

- **Failability record.** `None; this pass introduced no new boundary.` — discharged mechanically, not on prose: `git diff --stat -- '*.py'` is empty for this pass and both writable files are `.md`, so the diff contains no statement, branch, guard, comparison, or raise for the mandatory floor to select. Slices 1 and 3 discharged it the same way; Slice 2's `None; …` entry was audited by Worker 3 against an executable-token identity proof for all 19 files and re-audited by Slice 2's final verification.
- **No fail-open shape landed.** Same proof — no build pass in this cycle contains an expression.
- **Floor verification: none owed by any pass in this cycle, and this artifact records that literal rather than leaving it blank.** The build plan's preamble declares `Floor-verification scope: none`. **No slice in this cycle touches a Django / Strawberry / channels integration seam, because no slice changes an executable statement.** The final gate inherits this declaration rather than a blank.
- **Hot-path budget.** `Not applicable; the build plan declares no hot path.` Nothing in this cycle runs per request, per resolver, per row, per connection, or per outbound message — nothing in it runs at all.

### Why this is `final-accepted` and not `revision-needed`

One code-side finding survives (the three broken substring citations). [`BUILD.md`][build] `## Cross-slice integration pass` says a finding is recorded and routed to Worker 0 for a Worker 2 / Worker 3 consolidation loop; it does not require the integration artifact itself to sit at `revision-needed` while that loop runs, and `revision-needed` set here would route to Worker 2 against *this* artifact, which owns no `.py` file. The finding is therefore **routed to Worker 0 as a consolidation loop over `filters/base.py` and `types/finalizer.py`** — two files, three comment-text edits, the same shape and the same ownership as Slice 2. If Worker 0 dispatches it, this pass re-runs afterwards, per `## Integration pass` in [`worker-1.md`][worker-1]. If the maintainer prefers to close the cycle and card it, the catalog entry below carries everything a later card needs, and no shipped behavior is affected either way: a broken comment citation misleads a reader and nothing else.

Severity: **Medium** — `AGENTS.md` rule 27's second half (a citation must resolve) is exactly what this violates, and the same defect class in its card-id spelling is what Slice 2 was dispatched to fix. Not High: no contract, test, or behavior is wrong.

### Deferred work catalog (re-derived)

Every item re-derived against the tree during this pass. Where a number differs from the artifact that handed it forward, the corrected figure and its cause are stated. **This list is a claim; the final gate's `### Deferred work catalog` should re-derive anything it acts on.**

1. **Three broken `#"substring"` citations into the spec** — `filters/base.py` x2 (`#"accept both raw"`), `types/finalizer.py::_bind_filterset_owner` (`spec-027 Decision 6 #"Partial-finalize lifecycle"`). Cause and recommended replacement text in `### Citation audit: .py -> spec, every occurrence`. **Routed to Worker 0 this pass**; if not dispatched, it is the catalog's first item.
2. **`tests/test_registry.py::test_clear_tolerates_unimportable_filter_submodules` and its three siblings all describe a mechanism that does not exist.** Slice 3 flagged the filter one and left the sibling population unaudited. Audited here: `django_strawberry_framework/registry.py` contains **zero** `except ImportError` occurrences and its `clear()` replays `iter_subsystem_clears()`. All four docstrings describe the retired shape — `test_clear_tolerates_unimportable_filter_submodules` ("Both `except ImportError` guards in `clear()`", "cycle-safe local imports"), `…_order_submodules` (names spec-028), `…_connection_submodule` (names spec-030), `…_relay_module` (names spec-032). **The population is four, one per subsystem; only the filter one belongs to this card.** Each test still proves something real — poisoning `sys.modules` leaves the registry's own clear undisturbed — so this is docstring rot, not a dead test.
3. **The PEP-563 deferred-annotation path for `filter_input_type` has no test.** Confirmed: `test_filter_input_type_under_future_annotations` returns zero hits tree-wide, and the spec now says so in the `## Test plan`. The eager path is covered by two package tests plus the six live fakeshop resolver annotations, and the repeat-safety property PEP 563 depends on is pinned by `test_filter_input_type_is_idempotent_under_repeated_calls`. A coverage boundary, not an untested contract.
4. **History-narrating prose in `.py` comments — a real class whose population is instrument-dependent and must not be carded as a number.** Three instruments over the same 19 files now disagree: Worker 3 measured ~65 across 15 files, Slice 2's Worker 1 measured 54 across 11, this pass's token sweep measures **46 across 11**. All three include legitimate contrast prose (a test docstring saying what a fixture is NOT is not build provenance). The confirmed exemplar all three agree on: `django_strawberry_framework/filters/inputs.py::_encode_global_id_input` #"The previous implementation eagerly decoded the object", three lines below a citation Slice 2 rewrote. **Card the class with the exemplar and an audit step, never a count.**
5. **Bare `Decision N` references naming no card — 83 occurrences across 13 of the 19 files.** Re-derived exactly (Slice 2 measured 83 and did not state the file count). The defect is **card attribution, not count**: most belong to other cards (`test_library_api.py` ~19 are the Relay-connection card's, `test_products_api.py` ~11 the mutations / optimizer cards', `tests/types/test_base.py` ~13 spec-028's and spec-032's), so the population cannot be swept by number — only resolved site by site against the card whose file it sits in. Two confirmed-ambiguous sites: `django_strawberry_framework/utils/inputs.py` x2 `no operator bag, Spec Decision 8`, in the shared substrate, both meaning **spec-028**'s Decision 8.
6. **Five raw spec-line refs in `examples/fakeshop/test_query/test_products_api.py`**, at lines 2948 / 2984 / 3015 / 3051 / 3098 — re-derived, all five present. They name spec-036 (mutations) and sit in that file's `036` mirror block, so they were correctly untouched under the card-not-directory scope boundary. They belong in the catalog because they survive every future sweep of a file this build edited.
7. **The same defect class in other cards' trees.** Re-derived over the package modules Slice 2's out-of-scope table named: **13 raw line refs** — `orders/inputs.py` 2, `orders/sets.py` 4, `mutations/resolvers.py` 1, `mutations/sets.py` 4, `_strawberry_patches.py` 2 — plus review-finding ids in `orders/factories.py`, `types/base.py`, `forms/inputs.py`, `mutations/inputs.py` and `rest_framework/*.py`. The id half's count is instrument-dependent for the same reason as item 4; the class is confirmed by reading, and every one belongs to another card.
8. **The staged anchor `TODO(spec-027-filters-0_0_8 Meta.search_fields)` in `filters/sets.py::FilterSet.get_filters`** — stays, owned by `spec-055`'s Slice 1 (see `### Staged-anchor sweep`). Two mismatches recorded: `spec-055` quotes the anchor with a `card 0.1.2` suffix the real comment does not carry, and the anchor names a shipped spec rather than the open card that will ship the work.
9. **The `## Non-goals` auto-generation sentence is already carded — do not re-derive it as new rot.** Verified on the board: `KANBAN.md` `TODO-ALPHA-051-0.0.15` carries the WP-D contract question that gates it ("BOTH dynamic-set factories are production-unconsumed … and `spec-027`'s auto-generation" sentence). The sentence predicts implicit generation lands with `DjangoConnectionField` in `0.0.9`; the connection field shipped and the auto-generation did not (`filters/factories.py` records that Layer 6 still has no source consumer). Acting on it here would pre-empt a decision this cycle does not own.
10. **`README.md` is missing `filter_input_type`** — a genuine, undischarged `## Doc updates` obligation. The spec's `README.md` bullet requires `FilterSet` / `RelatedFilter` / `filter_input_type` / `Meta.filterset_class` in the shipped-symbol list, and argues explicitly why the helper belongs there. `README.md` carries the other three at its `0.0.8` line and **zero occurrences of `filter_input_type`**. `README.md` is fenced this cycle, so this is recorded, not fixed.
11. **The rest of the `## Doc updates` obligations are discharged — the surface Slice 3 declared unexamined is now examined.** Read read-only (all these docs are fenced for editing, not for reading): `docs/GLOSSARY.md` carries `**Status:** shipped (`0.0.8`)` for all four entries, the index row for `filter_input_type`, and all four under the Filtering category; `docs/TREE.md` carries `filters/` on-disk plus the mirrored `tests/filters/` tree including `fixtures/filtersets.py`; `docs/README.md` lists the filtering subsystem as new in `0.0.8`; `TODAY.md` carries the filtering capability and the fakeshop surfaces; `KANBAN.md` carries `DONE-027-0.0.8` in the Done column and the WIP/DONE spec map, and its `### In progress` block no longer names the card; `CHANGELOG.md` carries both the `### Added` filtering entry and the `### Changed` `Meta.filterset_class` entry; `GOAL.md`'s migration narrative carries the replacement wording the spec specified verbatim. **Item 10 is the single gap**, and it is the reason the read was worth doing: an unexamined surface is not a green one.
12. **`[fakeshop-test-library-reload]` resolves to two different files across the pair, deliberately.** The spec's def points at `conftest.py` (Slice 3's fix); the rationale's still points at `test_library_api.py`, because its only use is the verbatim rev7 entry whose subject is the claim naming that file. Recorded in the rationale so a future sweep reads it as a decision rather than as an unfinished fix.

### Summary

The integration pass found the seam none of the three slices owned: a `#"unique substring"` citation from a `.py` file into the spec, gated by nothing, and pointed at text Slice 1 moved out. Three such citations broke this cycle — two in `filters/base.py` naming a revision-history bullet that left the spec whole, one in `types/finalizer.py` naming a Decision-6 justification bullet — and are routed to Worker 0 with their replacement text. Every `spec-027 Decision N` citation was re-resolved against the spec **after** Slice 3's rewrite, including the two Decisions Slice 3 rewrote most (8 and 9); all hold. The mirror direction found the spec citing a `GOAL.md` sentence that this card's own Slice 5 had removed, cited as live in three places while two other places ordered its removal; all five sites now cite the section heading and the three present-tense sentences state what `GOAL.md` says. Two prior artifacts recorded a staged-anchor sweep as clean when it returns a hit in shipped source, and Slice 3's `tests/filters/` census closed over three of four surfaces — both corrected, neither fixable in the artifacts that carry them. Twelve deferred items were re-derived; four had wrong or unaudited populations, and one (`README.md` missing `filter_input_type`) is a real undischarged doc obligation found only by reading the surface the prior slice declared unexamined.

### Spec changes made (Worker 1 only)

Every edit is to `docs/SPECS/spec-027-filters-0_0_8.md` unless stated. Cited by content, not line number. Each was applied by a count-asserted replacement that writes nothing on a mismatch.

1. **`## Doc updates`, the `docs/TREE.md` bullet** -> the mirrored `tests/filters/` enumeration gained the `fixtures/` sub-package. Reason: three other spec surfaces (Decision 12, the `## Test plan` heading paragraph, DoD item 11) name it, `docs/TREE.md` lists it, and `tests/filters/fixtures/filtersets.py` is on disk. This is the fourth surface Slice 3's "consistent across all three" census did not cover.
2. **`## Architectural decisions`, the `_apply_related_constraints` scope anchor** -> `<a id="h4-related-queryset-boundary-scope">` renamed to `<a id="related-queryset-boundary-scope">`. Reason: the `h4-` prefix is a review-round finding id, the vocabulary Slice 1 moved out of the prose but could not see inside an HTML attribute. Nothing in the repo references either id (verified repo-wide, the content-named sibling `sync-async-api-split` included), so the rename breaks nothing.
3. **`## Borrowing posture`** -> the `GOAL.md` citation repointed to `#"Coming from DRF + django-filter"` and the sentence restated as the promise `GOAL.md` actually makes (a one-line parent-class swap). Reason: the quoted wording has not been in `GOAL.md` since this card's Slice 5 replaced it.
4. **`## Non-goals`, the `Meta.filterset_class = MyDjangoFilter` bullet** -> same citation repoint; "direct-reuse promise" -> "migration promise". Reason: same.
5. **`## Risks and open questions`, the same bullet's forward-looking twin** -> same citation repoint; "(the wording itself) is honored as …" -> a direct statement of what `GOAL.md` says. Reason: same.
6. **`## Slice checklist`, the Slice-5 `GOAL.md` bullet** -> same citation repoint, and "currently anchored at" -> "anchored at". Reason: the rewrite it ordered has landed, so "currently" was false; the old wording stays quoted **in the bullet's own prose** because it is the subject of the instruction.
7. **`## Doc updates`, the `GOAL.md` bullet** -> same citation repoint. Reason and disposition as item 6.

**`docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md`** gained `## Integration pass — cross-slice reconciliation` (four entries: the `GOAL.md` citation retraction, the `h4-` anchor, the fourth `tests/filters/` surface with the population-selection form of the census trap, and the backtick-normalization lesson that stopped two false findings), plus three corrections to text falsified by Slice 3 having acted: the header paragraph's future-tense hand-off to Slice 3, the `## Handed to Slice 3` section's missing discharge note, and a note on the deliberate two-target `[fakeshop-test-library-reload]` divergence.

### Notes for Worker 0 (routed findings)

**One consolidation loop, if the maintainer wants it before the final gate.** Cohort: `django_strawberry_framework/filters/base.py` and `django_strawberry_framework/types/finalizer.py`, three comment-text edits, no executable statement. Replacement text is decided and recorded in `### Citation audit: .py -> spec, every occurrence` — Worker 2 chooses nothing. Worker 3's re-review should re-run the executable-token identity proof for the two files (Slice 2's instrument) and re-resolve all 13 substring citations with backticks normalized. This pass re-runs afterwards.

Everything else is catalog, not a loop.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[build]: BUILD.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
