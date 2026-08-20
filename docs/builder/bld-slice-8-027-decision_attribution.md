# Build: Catalog-discharge cohort C — card-less `Decision N` attribution (027)

Spec reference: `docs/SPECS/spec-027-filters-0_0_8.md` (`### Decision 9`, `### Decision 11` — the two mirrored contracts this cohort cites in the shared `utils/inputs.py` substrate). The cohort's repairs also resolve against `docs/SPECS/spec-028-orders-0_0_8.md`, `spec-030-connection_field-0_0_9.md`, `spec-033-connection_optimizer-0_0_9.md`, and `spec-039-serializer_mutations-0_0_13.md`; every one is cited by heading and Decision number, never by line.
Status: final-accepted

## Plan (Worker 1)

### Planning lives in `build-027-filters-0_0_8.md`

This cohort has no Worker 1 planning pass of its own. The contract is Worker 0's dispatch brief plus:

- [`build-027-filters-0_0_8.md`][plan] `### Catalog-discharge cohorts (added 2026-08-20, post-commit 8a9840dc)` — the four-cohort file partition and cohort C's row.
- [`bld-slice-4-027-broken_substring_citations.md`][slice4] — the format precedent for a comment/docstring-only pass, including the executable-token-identity instrument this pass reproduces and extends.

**Ownership partition (cohort C, declared):** `django_strawberry_framework/rest_framework/{sets,resolvers,inputs,serializer_converter}.py`, `django_strawberry_framework/orders/{__init__,factories}.py`, `django_strawberry_framework/optimizer/extension.py`, `django_strawberry_framework/utils/inputs.py`. Cohorts A, B, and D ran concurrently on disjoint files. A **fourth** writer — the concurrent `spec-028` session — took three of cohort C's eight files mid-pass; see `### Ownership collision with the concurrent spec-028 session`.

### DRY analysis

Not applicable and deliberately skipped, on the ground Slices 1-4 recorded: [`BUILD.md`][build] gates *helper planning*, and this pass proposes no helper, shared constant, validation branch, or test helper. The diff contains no executable statement (proved mechanically under `### Executable-token identity proof`).

One DRY observation the pass did act on, and it is a **de-duplication of vocabulary, not of code**: the tree had **four** spellings of the same reference — `Decision N`, `Decision-N`, `Spec Decision N`, and `D8` — plus a newline-wrapped `Decision\n11`. A census keyed on any one spelling is not a population. The instrument in `### Per-file census` matches all of them; the spelling variance is why Worker 0's inherited figures were wrong in both directions.

### Dispatched findings checklist

Built from Worker 0's cohort-C row. Boxes 1-3 are the dispatched text; box 4 is the provenance sweep the dispatch scoped to this cohort's own files.

- [x] Catalog item 4's `rest_framework/` + `orders/` sites — `Decision N` / `Spec Decision N` cited without naming which spec
- [x] Catalog item 5 (all) — `optimizer/extension.py` and `utils/inputs.py` bare `Decision N`
- [x] Catalog item 7's `rest_framework/` half — a reference naming a real spec section but no card
- [x] Catalog item 8, scoped to this cohort's own files — unambiguous build-process provenance (review-round ids, slice/pass/cycle names)

---

## Build report (Worker 2)

### Ownership collision with the concurrent spec-028 session

**Recorded first because it invalidates `HEAD` as this pass's sole baseline.** At the moment this pass began, `git status --porcelain` showed all eight cohort-C files clean at `HEAD`. Minutes later, three of them were dirty and **not by this pass**:

| File | What the 028 session did | Overlap with this pass |
|---|---|---|
| `orders/__init__.py` | line 60 `Spec Decision 5` -> `spec-028 Decision 5` | none; this pass edited lines 5, 32, 77 |
| `orders/factories.py` | line 103 `Spec Decision 8` -> `spec-028 Decision 8` | none; this pass edited line 9 |
| `utils/inputs.py` | lines 1708, 1733 `Spec Decision 8` -> `spec-028 Decision 8` | none; this pass edited lines 400, 1441 |

It is **the same defect class** this cohort was dispatched to close, arriving from a different session. Nothing was reverted (`AGENTS.md` rule 34). No `git stash` / `checkout` / `restore` / `worktree` was used anywhere in this pass. Both the collision and the disjointness are measured, not asserted: the census at `HEAD` and the census at the pre-my-pass working tree (`### Per-file census`) differ by exactly those three orphans, and the two-baseline token proof separates this pass's contribution from theirs.

**Consequence for Worker 0:** cohort C's declared partition is no longer disjoint from the concurrent 028 session on these three paths. The maintainer will receive a mixed diff on them. Also flagged: `django_strawberry_framework/orders/sets.py` appears in **both** cohort B's declared partition and the 028 session's dirty set.

### Per-file census

**This is a census, not the brief's figures.** Two instruments over the same eight files, so the difference is itself a measurement. Script: `<scratchpad>/cohortC-027/census.py` (private subdirectory — see `### Notes for Worker 3`).

- **L (line-scoped)** — an occurrence is "bare" iff no `spec-NNN` appears on the **same line**. This is the instrument shape the dispatch brief's figures came from. It manufactures adjacent-line false positives and is blind to a reference wrapped across a newline.
- **B (block-scoped)** — tokenize, take each docstring and each contiguous comment run **whole**, and report ORPHAN only when no `spec-NNN` appears anywhere in that block. Immune to both failure modes by construction.

Vocabulary matched: `Decision N`, `Decision-N`, `Spec Decision N`, and the newline-wrapped form (`Decision[-\s]+\d+` over block text).

| File | occurrences | L-bare | **B-orphan** | L false positives |
|---|---|---|---|---|
| `rest_framework/sets.py` | 20 | 14 | **0** | 14 |
| `rest_framework/resolvers.py` | 6 | 5 | **1** | 4 |
| `rest_framework/inputs.py` | 9 | 1 | **0** | 1 |
| `rest_framework/serializer_converter.py` | 8 | 2 | **0** | 2 |
| `orders/__init__.py` | 5 | 4 | **2** | 2 |
| `orders/factories.py` | 5 | 2 | **1** | 1 |
| `optimizer/extension.py` | 20 | 12 | **10** | 2 |
| `utils/inputs.py` | 7 | 6 | **4** | 2 |
| **TOTAL at `HEAD`** | **80** | **46** | **18** | **28** |

**28 of the 46 line-scoped "bare" hits — 61% — are false positives**, and every one is the adjacent-line or wrapped-citation shape Worker 0's mid-pass correction warned about. The block instrument produced none of them.

Same census at the **pre-my-pass working tree** (i.e. after the 028 session's three repairs): 80 occurrences, 42 L-bare, **15 B-orphan**. The three-orphan delta is exactly `orders/factories.py:103` and `utils/inputs.py:1708` / `:1733`.

**Where the brief's figures were wrong, in both directions:**

- `optimizer/extension.py`: the brief said "**10** bare `Decision N`" while listing **eleven** line numbers (133, 216, 226, 265, 325, 671, 701, 991, 1081, 1443, 1499). The measured orphan count is **10** — and the set is not the brief's. `1081` and `1499` are *not* orphans (their blocks name a spec) but are repaired anyway under a different rule; `1124` is an orphan the brief never listed, because the reference is **wrapped** as `Decision\n        11` and no line-scoped instrument can see it. Net: the brief's list is off by one in the count, and wrong on three of eleven members.
- `utils/inputs.py`: the brief said "**3** (1300, 1708, 1733)". The measured orphan set at `HEAD` is **4** and it is a **different set**: {400, 1441, 1708, 1733}. `1300` is *not* an orphan — it sits in the block that carries the existing `(spec-027 / spec-028 Decision 9)` precedent. `400` and `1441` were invisible to the brief because they use the **hyphenated** `Decision-9` / `Decision-11` spelling.
- `rest_framework/sets.py` and `resolvers.py`: the brief expected "substantially more than the catalog's enumeration". Measured: `sets.py` has **20** occurrences and **zero** orphans; `resolvers.py` has **6** and **one**. The apparent mass is the false-positive class.

**After this pass: 81 occurrences, 0 block-orphans across all eight files.** (81 not 80 because repairing `resolvers.py`'s `D8` spelling to `Decision 8` adds one occurrence of the canonical form.)

### Sites repaired, with the evidence that established each owner

Owners were established by reading the cited Decision and confirming it states the thing the comment claims — never by matching the number. **Rule applied:** repair iff (R1) the enclosing block names no spec, (R2) the block names only a spec that *cannot* own the cited Decision, or (R3) the site is separated from its block's attribution by a genuine body paragraph break **and** a sibling spec named in that block carries an identically-numbered Decision on the identical subject. A docstring's mandatory summary/body blank line is **not** a paragraph break under R3.

#### `optimizer/extension.py` — 7 sites -> `spec-033 Decision 7`

Lines 133, 216, 226, 265, 325, 701, 1443. All R1 (orphan).

`docs/SPECS/spec-033-connection_optimizer-0_0_9.md` `### Decision 7 — Plan-cache key hygiene: nested pagination variables hash, root pagination arguments do not` is the owner, and its bullets state each cited claim verbatim: "the collector tracks depth at the spread site, not raw fragment-definition nesting" (the line-216 claim), "under-collection serves wrong data" (line 226), "any non-root field's pagination-named variable is collected" (line 325), and the `first`/`last`/`before`/`after` non-root variable rule (line 133's `_PAGINATION_ARG_NAMES`). No competing candidate: `grep "under-collection would serve wrong data\|depth at the spread SITE"` over `docs/SPECS/` returns spec-033 and spec-004 only, and spec-004 has no Decision 7 on this subject.

**One in-site correction, stated rather than buried.** Line 226 quoted the spec as `"under-collection would serve wrong data"`. The spec says `"under-collection serves wrong data"`. Since the citation now names a card, the quote has to resolve, so it was corrected to the spec's wording in the same edit. This is the only place this pass changed prose beyond inserting a card id or deleting a process-provenance clause.

#### `optimizer/extension.py` — 5 sites -> `spec-030 Decision 11`

Lines 671, 991, 1124 (wrapped), plus 1081 and 1499.

`docs/SPECS/spec-030-connection_field-0_0_9.md` `### Decision 11 — The connection field owns its optimizer cooperation point` is the owner. Its text: "extract the plan-application logic from `DjangoOptimizerExtension._optimize` into a reusable internal helper (e.g. `apply_connection_optimization(...)`)" — line 1124's exact claim; and "Extracting a shared helper ... keeps the middleware and the connection field on one plan-application implementation" — line 1081's exact claim. The `_active_optimizer` publication seam (lines 671, 991) is the same cooperation point, corroborated by `spec-033` line 105, which describes it and states "**This card does not re-ship any of it**".

- **Line 1081 is R2, and the measurement is decisive.** Its block names `spec-035` (line 1069, `G1, spec-035 Decision 3`). `grep "^### Decision" docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` returns **9** decisions — there is no spec-035 Decision 11, so the in-block spec cannot be the owner. This is the case where an in-block attribution is worse than a bare number: it sends the reader to a real document that stops at 9.
- **Line 1499 is R2.** The reference sat immediately before `(spec-036 Decision 9)` on the next line, so a reader naturally binds `Decision 11` to spec-036 — which has a Decision 11 ("Primary-type resolution"), about something else entirely.
- **Line 1124 was wrapped** (`(Decision\n11)`). Repaired to a single unbroken `(spec-030 Decision 11)` by moving three words across two line boundaries; word order is unchanged.

#### `rest_framework/resolvers.py` — 6 sites -> `spec-039 Decision 7 / 8 / 9`

Line 226 (R1, orphan); lines 23, 47, 59, 93 (R3); line 834 (R1, the `D8` spelling).

`docs/SPECS/spec-039-serializer_mutations-0_0_13.md` numbering was confirmed decision-by-decision against every claim: D7 "Serializer-field -> Strawberry input mapping", D8 "Resolver pipeline: instantiate -> `is_valid()` -> ... -> payload", D9 "Optimizer composition: the `ModelSerializer` payload re-fetch rides the `spec-036` G2 path".

**Why R3 fires here rather than being style.** `spec-038-form_mutations-0_0_12.md` carries Decisions 7, 8, 9, 10, and 11 with **identically-named subjects** — D8 is "Resolver pipeline: instantiate -> `is_valid()` -> `form.errors` -> `save()` -> optimizer re-fetch -> payload", D9 is "Optimizer composition: the `ModelForm` payload re-fetch rides the `spec-036` G2 path`". The module docstring names ``038`` repeatedly as the sibling flavor. So a bare `Decision 8` eighty lines below the docstring's `spec-039` has a **live wrong candidate**, not merely an unknown one. That is a measured ambiguity, not a preference.

Line 834 read `(the spec D8 step-4 hook)` — a third spelling. `D8` occurs **0** times in spec-039, spec-038, and spec-036, so the label itself resolves nowhere; `spec-039` Decision 8's numbered step **4** is "**Construct** the serializer via the overridable `get_serializer_kwargs`", which is exactly this function. Repaired to `spec-039 Decision 8 step-4`.

#### `rest_framework/resolvers.py` line 55 — a dangling `Decision` with no number

Read `(the config-assessment grep-guard, Decision; the strategy is resolved once at finalization ...)`. The trailing `Decision;` names nothing. `grep -rc "onfig-assessment grep-guard" docs/SPECS/*.md` returns exactly **one** file, `spec-039`, at line 1232, where it is a **Slice 3 checklist item** — "**Config-assessment grep-guard (query-path strategy).** A relation `GlobalID` is decoded against the target type's **recorded** `effective_globalid_strategy`" — not a Decision at all. Repaired to `(the spec-039 config-assessment grep-guard; ...)`: the card is named, and the word that pointed at a non-existent Decision is gone.

#### `rest_framework/sets.py` — 5 sites

| Line | Was | Now | Rule / evidence |
|---|---|---|---|
| 19 | `(Decision 6 / Decision 10 / Decision 11)` | `(spec-039 Decision 6 / Decision 10 / Decision 11)` | R3; spec-038 D6/D10/D11 share the subjects |
| 35 | `(Decision 12)` | `(spec-039 Decision 12)` | R3; 30 lines and two paragraph breaks from its attribution |
| 487 | `the ``036`` write-auth seam, Decision 11)` | `... spec-039 Decision 11)` | R3; spec-038 D11 is also "reuse the `036` seam" |
| 564 | `above (P2.7)` | `above (spec-039 P2.7)` | real spec item, no card: `P2.7` occurs **9** times in spec-039, **0** in spec-038 / spec-036 |
| 743 | `**P1.7 reuse is partial here**` | `**spec-039 P1.7 reuse is partial here**` | `P1.7` occurs **8** times in spec-039, **0** in spec-038 / spec-036 |

Line 751's second `P1.7` is a back-reference inside the paragraph line 743 opens, so it resolves once 743 is attributed; left alone deliberately.

#### `rest_framework/serializer_converter.py` — 2 sites -> `spec-039 M3`

Lines 740 and 992, both R1. `M3` occurs **5** times in spec-039 and its subject matches exactly: line 593 "**(M3)** a serializer relation target", line 2138 "`ConfigurationError` (M3)", line 3190 "**Relation target with no registered primary `DjangoType` (M3).**". Corroborated by the module's own correctly-attributed sibling at line 708, `(spec-039 Decision 7 / M3)` — the dispatch brief's evidence path #2. Line 996's second `M3` is in the same comment block as 992 and resolves once 992 is attributed.

#### `orders/__init__.py` — 3 sites -> `spec-028 Decision 11`

Lines 5 (R3), 32 and 77 (R1). `docs/SPECS/spec-028-orders-0_0_8.md` `### Decision 11 — `order_input_type(OrderSet)` consumer helper` is the owner; the two orphaned comments describe the `_helper_referenced_ordersets` ledger and the `order_input_type` body, which is that Decision's subject. The hyphenated `Decision-11` spelling was normalized to `Decision 11`.

#### `utils/inputs.py` — 2 sites, the shared-substrate case the brief flagged

| Line | Was | Now | Why both cards |
|---|---|---|---|
| 400 | `The heavy Decision-9 sibling of ``make_input_namespace``` | `The heavy spec-027 / spec-028 Decision 9 sibling ...` | the docstring's own next sentence says "**Filter and order** `inputs` modules grew the same four-part shape" |
| 1441 | `The Decision-11 consumer-helper body shared by` | `The spec-027 / spec-028 Decision 11 consumer-helper body shared by` | the docstring's own next two lines name `filters/__init__.py::filter_input_type` **and** `orders/__init__.py::order_input_type` |

The two specs deliberately mirror: `spec-027 ### Decision 9 — Input-class namespace vs `TypeRegistry` and lifecycle` / `spec-028 ### Decision 9 — Input-class namespace vs `TypeRegistry` and lifecycle` (identical headings), and `spec-027 ### Decision 11 — `filter_input_type(FilterSet)` consumer helper` / `spec-028 ### Decision 11 — `order_input_type(OrderSet)` consumer helper`. Picking one would have been wrong for half the callers.

**The `spec-027 / spec-028 Decision 9` spelling is the tree's existing precedent, not an invention.** It is at `utils/inputs.py` line 1297, inside `materialize_generated_input_class`'s docstring, 100+ lines above the site this pass repaired — the same file, unedited by this pass. Matched exactly.

#### `orders/factories.py` line 9 — a review-round id that this cycle's own Slice 1 broke

Read `(mirror of ``filters/factories.py``'s Layer 5 + Decision 4 H1)`. Measured:

- `grep -c "H1" docs/SPECS/spec-027-filters-0_0_8.md` -> **0**.
- `grep -c "H1" docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` -> **27**, including "Moved `FILTER_DEFAULTS` from `factories.py` to a class attribute on `FilterSet` (in `sets.py`) **per H1**".
- `spec-028`'s two `H1` mentions are about a different subject (nested `RelatedFilter` visibility re-derivation).

So `H1` is a **review-round finding id** that this cycle's Slice 1 moved out of the spec into the rationale companion — build-process provenance that now resolves in no spec at all. The surviving contract is in `spec-027 ### Decision 4 — Upstream-primitives parity floor`, which states it directly: "The `FILTER_DEFAULTS` map is a **class attribute on the package `FilterSet`** (not a factory-side parallel map)" and "`FilterArgumentsFactory._ensure_built` derives the Strawberry input field type **from the resolved filter instances** ... NOT from a parallel `FILTER_DEFAULTS` lookup" — precisely the invariant the order-side sentence mirrors. Repaired to `spec-027 Decision 4`; the review-round id is dropped.

### Build-process provenance removed — `rest_framework/resolvers.py`, 11 sites

`grep -c "hardening pass" django_strawberry_framework/rest_framework/resolvers.py` -> **11** before, **0** after. Lines 423, 789, 1317, 1406, 1450, 1891, 1964, 2098, 2141, 2153, 2197. Each was a parenthetical `(the hardening pass)` / `(hardening pass)`; each was deleted and nothing else on the line changed.

Two independent reasons, both measured:

1. **It is a pass name.** `AGENTS.md` and this repo's standing posture are that a comment states the invariant, never how the change came to be. Every one of the eleven sentences states its invariant unchanged without the clause.
2. **It does not resolve, and the nearest thing that does resolve is a different event.** `grep -c "hardening pass" docs/SPECS/spec-039-serializer_mutations-0_0_13.md` -> **0**; spec-039 calls its own event "**the 2026-07-15 hardening revision**". Meanwhile `spec-033` uses the phrase "the post-`032` hardening pass" for an entirely unrelated optimizer change. A reader grepping `hardening pass` lands on the wrong subsystem.

No spec id was substituted in: these are spec-039 modules whose docstrings already say `spec-039`, so inserting it eleven more times would be noise, and the underlying contracts (`get_serializer_save_kwargs`, the relation-intent ledger, `get_serializer_injected_data`) are all in spec-039 already.

### Sites left UNRESOLVED, and why

Reporting these accurately is the successful outcome the dispatch asked for. Each was investigated and **not** touched.

| Site | Reference | Measurement | Why left |
|---|---|---|---|
| `rest_framework/serializer_converter.py:442` | `spec-039 Decision 7 / SR-3` | `grep -rl -- "SR-3" docs/` returns **only** a `docs/shadow/` file derived from this source. **0** hits anywhere in `docs/SPECS/`. | `SR-3` names nothing in any spec, and nothing establishes what it was meant to be. Naming a plausible substitute would be the confidently-wrong repair the dispatch forbids. Same class as Slice 4's `Implementation discretion item`. |
| `rest_framework/resolvers.py:38` | `spec-039 H4` | `grep -c "H4" docs/SPECS/spec-039-*.md` -> **0**. `H4` exists in spec-028, spec-036, spec-038. There is no `spec-039` rationale companion (`docs/SPECS/appx/` has only `spec-039-...-terms.csv`), so it was not moved either. | The card is named but the label resolves nowhere in it. Which item it meant is not derivable. |
| `rest_framework/sets.py:490` | `the form flavor's validate-then-store-raw precedent, D1` | `grep -cE '\bD1\b'` -> **0** in spec-039, spec-038, spec-036. | `D1` read as "Decision 1" fits nothing: spec-038 Decision 1 is "Spec filename and canonical naming". No candidate. |
| `rest_framework/inputs.py:1250` and `:1193` | `H3` | `H3` occurs **7** times in spec-039 and **19** in spec-036. spec-039's H3 is about the actor not drifting from the permission seam / `partial` + authorized-actor `context["request"]`; the code's claim is "GraphQL cannot express DRF `required=True`". **Subjects do not match.** | Two live candidates and neither subject matches. Attributing would send the reader to a real Decision that says something else. |
| `rest_framework/serializer_converter.py:476, 482, 984` | `H5` | `H5` occurs **1** time in spec-039 — and that one occurrence is itself a pointer *outward*: "([`spec-036`][spec-036] AR-H5)". spec-036 has 7, spec-038 has 2. | spec-039 does not own an `H5`; the DRF-specific claim (`PrimaryKeyRelatedField` only) does not read as spec-036's. Unresolvable. |
| `rest_framework/sets.py:685` | `the overridable Decision-7 hook` | Block-resolved (the same docstring names `spec-039 Decision 7` nine lines down, line 694). | Not an orphan, so out of the repair rule — and the line is already **91** characters, so a 9-character insert would breach the 99 limit and force a reflow of a docstring summary this pass is not otherwise editing. Reflow is the mechanism that splits citations across lines. |

### The 14 remaining line-scoped "bare" hits — every one a false positive

Listed so a reviewer re-running a line-scoped grep does not read them as missed work. All are block-resolved:

- Wrapped across a line break, card on the previous line: `serializer_converter.py:442` (`spec-039` ends line 441), `:708` (line 707), `sets.py:555` (line 554), `sets.py:860` (line 859).
- Back-reference inside a paragraph this pass attributed at its opening: `sets.py:27`, `:30`, `:467`, `:474`, `inputs.py:27`.
- Card named earlier in the same contiguous comment run: `sets.py:14`, `:113`.
- Block names the mirrored pair: `utils/inputs.py:19`, `:1300`.
- Length-blocked, recorded above: `sets.py:685`.

### Files touched

Grounded in `git status --porcelain`, and in a `diff` of each file against a pre-pass copy held outside the repo. **7 of the 8** owned files were edited; `rest_framework/inputs.py` was deliberately not (its only candidate sites are the unresolvable `H3` pair).

- `django_strawberry_framework/optimizer/extension.py` — 12 sites: 7 -> `spec-033 Decision 7`, 5 -> `spec-030 Decision 11`, one of which was unwrapped from a line break; plus the line-226 quote corrected to the spec's wording.
- `django_strawberry_framework/rest_framework/resolvers.py` — 6 attribution sites, 1 dangling-`Decision` repair, 1 `D8`-spelling repair, and 11 `(the hardening pass)` deletions.
- `django_strawberry_framework/rest_framework/sets.py` — 5 sites (3 `Decision N`, `P2.7`, `P1.7`).
- `django_strawberry_framework/rest_framework/serializer_converter.py` — 2 `M3` sites.
- `django_strawberry_framework/orders/__init__.py` — 3 `Decision-11` sites.
- `django_strawberry_framework/orders/factories.py` — 1 site (`Decision 4 H1` -> `spec-027 Decision 4`).
- `django_strawberry_framework/utils/inputs.py` — 2 sites, both to the mirrored `spec-027 / spec-028` form.
- `docs/builder/bld-slice-8-027-decision_attribution.md` — this artifact.

### Tests added or updated

None. This pass adds no executable statement and no contract; there is nothing new for a test to pin. The existing suite is the regression check and was run.

### Validation run

Every command from the repository root. No `--cov*` flag anywhere in this pass.

| Check | Command | Result |
|---|---|---|
| Format (scoped, never `.`) | `uv run ruff format <the 8 files>` | `8 files left unchanged`, exit 0 |
| Lint (scoped) | `uv run ruff check --fix <the 8 files>` | `All checks passed!`, exit 0 |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check` | exit 0 |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 779 citations resolve (702 in 422 .py files, 77 in KANBAN.md).` exit 0 |
| Pre-commit (all 5 hooks) | `uvx pre-commit run --files <the 8 files>` | kanban-constants, source-layout, ruff-format, ruff-check, citations — **all Passed** |
| Format check (read-only, repo-wide) | `uv run ruff format --check .` | `425 files already formatted` |
| Focused tests | `uv run pytest tests/rest_framework tests/optimizer tests/orders tests/filters tests/forms tests/mutations tests/utils tests/test_connection.py tests/test_relay_connection.py tests/test_list_field.py tests/test_registry.py examples/fakeshop/test_query/test_products_api.py --no-cov -q` | **3421 passed in 36.03s** |
| Wrapped-citation postcondition | `<scratchpad>/cohortC-027/wrapcheck.py` over the 8 files | **0** unclosed `#"` — and **0** at `HEAD`, so none was introduced and none pre-existed |

**Citation-gate count did not drop, and this pass did not move it.** 779 is the count both before and after; Slice 4 recorded 740, and the rise since is other cohorts' work. The mechanical check that *this* pass added and removed no `path::Symbol` reference is a per-file count against the pre-pass copies: `sets.py` 4/4, `resolvers.py` 8/8, `inputs.py` 13/13, `serializer_converter.py` 10/10, `orders/__init__.py` 1/1, `orders/factories.py` 8/8, `extension.py` 3/3, `utils/inputs.py` 18/18 — every one SAME. The count did not rise because this pass adds `spec-NNN Decision N` prose references, which `check_citations.py` does not resolve; it is `path::Symbol`-only, which is exactly why no instrument saw this defect class.

**Focused-scope justification.** `grep -rln` over `tests/` and `examples/` for `utils.inputs`, `rest_framework`, `optimizer.extension`, `apply_connection_optimization`, and `order_input_type` names the importing surface. `utils/inputs.py` is live shared substrate for **five** families (filter, order, mutation, form, DRF), so all five package mirrors are in scope: `tests/utils`, `tests/filters`, `tests/orders`, `tests/mutations`, `tests/forms`, `tests/rest_framework`. `optimizer/extension.py` adds `tests/optimizer`, `tests/test_connection.py`, `tests/test_relay_connection.py`, `tests/test_list_field.py`, and the live `/graphql/` optimizer-dogfooding surface `test_products_api.py`. `tests/test_registry.py` covers the `registry.clear()` lifecycle that drives the namespace clears in `utils/inputs.py`.

#### Churn classification, every path in `git status --porcelain`

| Owner | Paths |
|---|---|
| **This pass (cohort C)** | `optimizer/extension.py`, `orders/__init__.py`, `orders/factories.py`*, `rest_framework/{resolvers,serializer_converter,sets}.py`, `utils/inputs.py`*, and this artifact |
| Cohort A (`bld-slice-6-027-wrapped_citations.md`) | `consumers.py`, `routers.py`, `filters/factories.py`, `types/finalizer.py`, `types/relay.py`, + its artifact |
| Cohort B (`bld-slice-7-027-raw_line_refs.md`) | `mutations/{fields,resolvers,sets}.py`, `orders/sets.py`, `examples/fakeshop/test_query/test_products_api.py` |
| Cohort D | `docs/SPECS/spec-055-search_fields-0_1_2.md`, + its artifact |
| Concurrent spec-028 session | `orders/base.py`, `orders/inputs.py`, `orders/sets.py`, `types/base.py`, `docs/SPECS/spec-028-orders-0_0_8.md`, `docs/SPECS/appx/spec-028-...-rationale.md`, `examples/fakeshop/apps/library/orders.py`, `examples/fakeshop/test_query/test_library_api.py`, `tests/orders/*`, `tests/test_registry.py`, `bld-slice-{1,2}-028-*.md`, `build-028-*.md` |
| Worker 0 | `docs/builder/build-027-filters-0_0_8.md` |

\* mixed with the concurrent 028 session's hunks — see `### Ownership collision with the concurrent spec-028 session`. `orders/sets.py` is claimed by **both** cohort B and the 028 session. Nothing was reverted.

### Executable-token identity proof

Claimed mechanically per [`BUILD.md`][build] `## Claims are proven mechanically, never accepted on prose`. Instrument: `<scratchpad>/cohortC-027/tokid.py`, written fresh in a private subdirectory after Worker 0's collision warning.

It tokenizes with `tokenize`, drops `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` / `ENCODING` / `ENDMARKER` and every **statement-position** `STRING` (a docstring — a `STRING` whose token is preceded by `NEWLINE`/`INDENT`/`DEDENT`/`ENCODING`/`NL` and followed by `NEWLINE`), and compares the remaining `(type, string)` **sequence**. Every **other** string literal is KEPT — a module path inside a call, a dict key, an error message — which is the case a naive instrument drops and thereby passes a real change.

**Two baselines, because `HEAD` is not "before this pass"** for three of the eight files (the 028 session's hunks landed in between).

| File | vs `git show HEAD:<path>` | vs pre-my-pass worktree copy | exec tokens |
|---|---|---|---|
| `rest_framework/sets.py` | IDENTICAL | IDENTICAL | 2141 |
| `rest_framework/resolvers.py` | IDENTICAL | IDENTICAL | 7726 |
| `rest_framework/inputs.py` | IDENTICAL | IDENTICAL | 4631 |
| `rest_framework/serializer_converter.py` | IDENTICAL | IDENTICAL | 3017 |
| `orders/__init__.py` | IDENTICAL | IDENTICAL | 136 |
| `orders/factories.py` | IDENTICAL | IDENTICAL | 218 |
| `optimizer/extension.py` | IDENTICAL | IDENTICAL | 3755 |
| `utils/inputs.py` | IDENTICAL | IDENTICAL | 5397 |

Re-run **after** `ruff format` / `ruff check --fix`, so the verdicts describe the tree as it stands.

#### Challenge set — six mutations plus a control, landing asserted before the verdict was read

Asserted, in writing, before running: `C0 IDENTICAL | C1 DIFFERENT | C2 DIFFERENT | C3 DIFFERENT | C4 IDENTICAL | C5 IDENTICAL | C6 DIFFERENT`.

| Case | Mutation | Reference | Asserted | Verdict | First divergence |
|---|---|---|---|---|---|
| C0 control | byte-identical copy | `utils/inputs.py` @ HEAD | IDENTICAL | **IDENTICAL** (5397) | — |
| C1 operator flip | `if model is None:` -> `if model is not None:` | same | DIFFERENT | **DIFFERENT** (5397 vs 5398) | token 2279 `(NAME,'None')` != `(NAME,'not')` |
| C2 inserted statement | `_unused = 0` after `field_specs: ... = {}` | same | DIFFERENT | **DIFFERENT** (5397 vs 5400) | token 982 `(NAME,'def')` != `(NAME,'_unused')` |
| C3 deleted statement | the `field_specs: ... = {}` line removed | same | DIFFERENT | **DIFFERENT** (5397 vs 5381) | token 966 `(NAME,'field_specs')` != `(NAME,'def')` |
| C4 docstring rewrite | one-line docstring replaced wholesale | same | IDENTICAL | **IDENTICAL** (5397) | — |
| C5 comment rewrite | a full comment line replaced | same | IDENTICAL | **IDENTICAL** (5397) | — |
| **C6 non-statement string** | `"django_strawberry_framework_active_optimizer"` -> `"..._EVIL_optimizer"` inside a `ContextVar(...)` call | `optimizer/extension.py` @ HEAD | DIFFERENT | **DIFFERENT** | token 1665 `(STRING,'"..._active_optimizer"')` != `(STRING,'"..._EVIL_optimizer"')` |

All seven matched. **C6 is the case the dispatch flagged, and it earns its place for a reason the table makes visible: the token COUNTS are equal, 3755 vs 3755.** A count-only or length-only instrument passes C6 silently; only the element-wise sequence comparison catches it. This is why the table above reports a verdict per file rather than only a count, and why a "token count unchanged" claim is not a token-identity claim.

**The anchor discipline held, and it fired.** A first attempt aborted on `assert src.count("if module is None:") >= 1` — the anchor did not exist in that file — and wrote **no mutant at all**, so no half-mutated file ever reached the tree. Every anchor in the final run was asserted to match **exactly once** before use. Every mutant was written to a scratch path **outside** the repository; no mutation was ever applied to a tracked file, so no revert was needed and none is claimed.

### Answers to Worker 0's two mid-pass questions

- **Did the scratchpad collision affect any recorded measurement? No.** My first-draft instruments (`census_027.py`, `blocks_027.py`) did sit in the shared root under generic names. Every number in this artifact was re-derived by instruments written fresh into `<scratchpad>/cohortC-027/`, and every baseline was re-taken there (`tree-head/` from `git show HEAD:`, `tree-prepass/` from copies under a cohort-unique `c8-` prefix). I had independently noticed the collision earlier: my first `prepass/` copy directory came back holding **other cohorts' files** (`consumers.py`, `routers.py`, `filters_factories.py`, `types_relay.py`), which is what prompted the rename before any measurement was recorded. Nothing in this artifact rests on a shared-root script.
- **How many census hits were adjacent-line false positives? 28 of 46 at `HEAD` (61%).** Per file: `sets.py` 14, `resolvers.py` 4, `inputs.py` 1, `serializer_converter.py` 2, `orders/__init__.py` 2, `orders/factories.py` 1, `extension.py` 2, `utils/inputs.py` 2. My census never had the defect: it is block-scoped, taking whole docstrings and whole contiguous comment runs, so an adjacent-line or wrapped card id is inside the unit of measurement by construction. The line-scoped column exists in the census table **only** to quantify the false-positive rate of the instrument shape the brief used. And the same blindness cuts the other way: the line-scoped instrument **missed** three genuine orphans the block instrument found — `extension.py:1124` (wrapped) and `utils/inputs.py:400` / `:1441` (hyphenated spelling).

### Failability proofs

None; this pass introduced no new boundary.

Discharged mechanically rather than on prose: the executable-token identity table shows the diff contains no statement, branch, guard, comparison, or raise for the mandatory floor to select.

### Hot-path budget

Not applicable; the plan declares no hot path. `optimizer/extension.py` and `utils/inputs.py` do carry hot paths, but this pass changes no executable token on them (proved above), so there is no cost to measure.

### Floor verification

Not applicable; the plan declares floor-verification scope none. No slice changes an executable statement.

### Implementation notes

- **The repair rule is stated as R1/R2/R3 because "bare" is not a well-defined predicate.** A `Decision N` inside a docstring whose first line says `spec-039` resolves for a reader; one in a mid-function comment does not. Repairing all 80 occurrences would have added ~60 redundant card ids; repairing only line-scoped hits would have added ids next to ids already there. R1/R2/R3 are the smallest rule set that repairs every genuinely unresolvable site and no already-resolving one, and each clause has a mechanical trigger.
- **R2 exists because an in-block attribution can be worse than none.** `extension.py:1081` is the proof: its block named `spec-035`, which has only 9 Decisions. A reader following it lands on a real document that stops short — strictly worse than a bare number, which at least signals "look this up".
- **Hyphenated `Decision-N` was normalized to `Decision N`** at all five sites, so the tree now has one spelling for the canonical form. The `Spec Decision N` spelling is gone from these files (the 028 session closed its three; none remained in the other five).
- **Minimal-edit discipline, with one deliberate exception.** Every repair is a same-line insertion except `extension.py:1124` and `utils/inputs.py:400`, where the citation would otherwise have straddled a line break or left a two-word orphan line. Both reflowed the **minimum** number of lines (3 and 5) and changed no word order. Reflow is the mechanism that splits a citation across lines, which is the defect Slice 4 and cohort A exist to repair, so it was used only where not reflowing would have created that exact defect.
- **The `(the hardening pass)` deletions leave two short comment lines** (`resolvers.py:2098`, `:2197`). Re-wrapping them would have reflowed comments this pass is not otherwise editing; left ragged on purpose.

### Notes for Worker 3

- **Do not re-run any instrument from the scratchpad root.** Cohort C's are all under `<scratchpad>/cohortC-027/`: `census.py`, `wrapcheck.py`, `tokid.py`, `challenge/`, `tree-head/`, `tree-prepass/`. Read before executing; the root is shared and collisions are confirmed.
- **`HEAD` is not this pass's baseline for three files.** `orders/__init__.py`, `orders/factories.py`, and `utils/inputs.py` carry the concurrent 028 session's hunks too. Re-run token identity against **both** baselines; the `tree-prepass/` copies are what isolate this pass.
- **The unresolved list is the part most worth auditing.** Six sites were investigated and left alone (`SR-3`, `spec-039 H4`, `D1`, `H3` x2, `H5` x3, plus the length-blocked `sets.py:685`). If any of them is in fact establishable, that is a finding — but the measurement for each is quoted, so please re-derive rather than assuming.
- **One prose change beyond attribution:** `extension.py:226`'s quoted spec phrase was corrected from `"under-collection would serve wrong data"` to `"under-collection serves wrong data"`, which is what `spec-033` Decision 7 says. Rationale in the repair table; flagging it explicitly so it does not read as scope creep discovered in the diff.
- No shadow file was used. `scripts/review_inspect.py` was **skipped** for all eight files: this pass adds no logic, and the helper's `<stem>.stripped.py` replaces every comment and string-literal token with `...`, so its output is byte-identical before and after. The token-identity table is the mechanical evidence for the skip — the same recorded skip and reason Slices 2 and 4 carried.

### Notes for Worker 1 (spec reconciliation)

Five items. None is a `spec-027` edit; all concern surfaces fenced from this cohort or decisions only the custodian can take.

- **`docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` — the rationale move broke in-code `H1`-style references, and `orders/factories.py` was one.**
  - Current situation: `grep -c "H1" docs/SPECS/spec-027-filters-0_0_8.md` -> **0**; `grep -c "H1" docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` -> **27**. Slice 1 moved every review-round attribution (`per H1 of the adversarial review`, `per H3 of the feedback`, ...) out of the spec.
  - Recommended action: sweep `django_strawberry_framework/` for in-code references to `spec-027` review-round ids (`H1`-`H4`, `M1`-`M6`, `L1`-`L2`) that Slice 1 orphaned. This cohort found and repaired **one** (`orders/factories.py:9`), inside its own fence. The population outside cohort C's eight files is unmeasured and this cohort must not widen into it.
  - Reason: a review-round id is build-process provenance by nature, so the right repair is to name the surviving contract (a Decision) rather than to re-point at the rationale file. `orders/factories.py:9` shows the shape.
- **`docs/SPECS/spec-039-serializer_mutations-0_0_13.md` — `SR-3` and `H4` are cited in shipped source and exist in no spec.**
  - Current wording, `rest_framework/serializer_converter.py`: "`is_input` is the graphene-django ... parity parameter - **accepted-and-ignored** (spec-039 Decision 7 / **SR-3**)". And `rest_framework/resolvers.py`: "or `field.queryset.model` for a serializer-only relation - **spec-039 H4**".
  - Recommended replacement: for `SR-3`, `(spec-039 Decision 7)` alone if Decision 7 carries the accepted-and-ignored `is_input` contract; for `H4`, `(spec-039 Decision 7)` alone if Decision 7 carries the `related_model`-resolved-at-build contract. Either way the unresolvable label is dropped, not re-pointed.
  - Reason: `grep -rl -- "SR-3" docs/SPECS/` -> nothing; `grep -c "H4" docs/SPECS/spec-039-*.md` -> **0**. spec-039 has **no** rationale companion (only `spec-039-...-terms.csv` in `docs/SPECS/appx/`), so these were not moved out — they never existed in the spec. Deciding which Decision absorbs them is a custodian call, not a builder's, so this cohort left both sites untouched.
- **`spec-039` vs `spec-038`: the two specs share Decision numbers 7-11 with identical subjects, and the code cross-references both.**
  - Current situation: spec-038 D7/D8/D9/D10/D11 and spec-039 D7/D8/D9/D10/D11 are near-verbatim mirrors ("Resolver pipeline: instantiate -> `is_valid()` -> ... -> payload", "Optimizer composition: ... rides the `spec-036` G2 path", "Write authorization: reuse the `036` seam").
  - Recommended action: no spec edit. Record the collision so future comment authors in `forms/` and `rest_framework/` know a bare `Decision 8` is ambiguous there by construction, and always spell the card.
  - Reason: this is why R3 fired on seven sites that a naive reading would call "already attributed in-block".
- **`optimizer/extension.py`'s `Decision 11` references belong to `spec-030`, not to the spec its neighbouring text names.**
  - Current situation: `spec-035` has 9 Decisions and `spec-036`'s Decision 11 is "Primary-type resolution"; the plan-cache-sharing / `apply_connection_optimization` contract is `spec-030 ### Decision 11`. Five sites in one file read as spec-035's or spec-036's before this pass.
  - Recommended action: no spec edit; the repair is in the code. Recorded because `spec-033` line 105 describes the same seam as landing "in the post-`032` hardening pass", which is the sentence that makes a reader look for the decision in the wrong card.
- **`docs/README.md` and `docs/GLOSSARY.md` carry the `get_serializer_save_kwargs` / relation-intent-ledger surface this pass de-provenanced.**
  - Current situation: `grep -rln "get_serializer_save_kwargs\|relation-intent ledger" docs/` returns `docs/GLOSSARY.md` and `docs/README.md` alongside `spec-039`. This pass did not check whether either narrates "the hardening pass".
  - Recommended action: sweep both for the phrase at doc-wrap. `docs/GLOSSARY.md` is DB-generated (edit the DB, re-render), so it is not a hand edit.
  - Reason: both are outside cohort C's fence, and `grep -c "hardening pass"` was measured only over the eight owned files.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[build]: BUILD.md
[plan]: build-027-filters-0_0_8.md
[slice4]: bld-slice-4-027-broken_substring_citations.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
