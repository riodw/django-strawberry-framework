# Build: Catalog-discharge cohort I — the three bare `Decision N` concentrations (027)

Spec reference: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (`Revision 3` finding (4), the doc-reference-hygiene contract this cohort's Task 2 enforces). The pass's repairs also resolve against `docs/SPECS/spec-015-relay_interfaces-0_0_5.md`, `spec-030-connection_field-0_0_9.md`, `spec-034-permissions-0_0_10.md`, `spec-035-optimizer_hardening-0_0_10.md`, `spec-041-channels_router-0_0_14.md`, and `spec-046-transport_security-0_0_14.md`; every one is cited by card and Decision number, never by line.
Status: final-accepted

## Plan (Worker 1)

### Planning lives in `build-027-filters-0_0_8.md`

This cohort has no Worker 1 planning pass of its own. The contract is Worker 0's dispatch brief plus:

- [`build-027-filters-0_0_8.md`][plan] `### The largest remaining in-fence population, and Worker 0's stopping decision` — the three dispatched concentrations and the Task 2 routing note.
- [`bld-slice-8-027-decision_attribution.md`][slice8] (cohort C) and [`bld-slice-11-027-orphaned_round_ids_and_hyphenated_decisions.md`][slice11] (cohort F) — the block-scoped census method and the evidentiary bar this pass adopts. Their scripts were not reused; every instrument here was written fresh.

**Ownership partition (cohort I, declared):** `tests/test_routers.py`, `django_strawberry_framework/connection.py`, `tests/test_permissions.py`, `tests/optimizer/test_walker.py`, and this artifact. Nothing else.

### DRY analysis

Not applicable as a helper question and deliberately skipped, on the ground Slices 1-4 and cohorts C and F recorded: [`BUILD.md`][build] gates *helper planning*, and this pass proposes no helper, shared constant, validation branch, or test helper. The diff contains no executable statement (proved mechanically under `### Executable-token identity proof`).

Two DRY observations the pass did act on, both de-duplications of **vocabulary**, not of code:

- The tree spells the *spec id* two ways. `tests/test_routers.py` carries **21** occurrences of capitalized `Spec-046` alongside **17** of lowercase `spec-046`. Every block-scoped census in this cycle — cohort C's, cohort F's, and Worker 0's — matched `spec-NNN` case-sensitively, so a block whose only card id is capitalized reads as an orphan. That is the single largest error in the dispatched figures (see `### Per-file census`).
- The one deliberate mixed-spelling residue is recorded rather than left to be found: this pass did **not** normalize `Spec-046` to `spec-046`, because that is 21 lines of pure spelling churn on a file whose citations already resolve for a human reader. It is reported as a new class instead.

### Dispatched findings checklist

Built from Worker 0's cohort-I dispatch. Boxes 1-3 are Task 1; box 4 is Task 2; box 5 is the provenance sweep the dispatch scoped to this cohort's own files.

- [x] Re-derive the census over the three dispatched concentrations, block-scoped, with the line-scoped figure and false-positive rate alongside
- [x] Establish the owning card for every block-orphan by measurement, preferring disproof to resemblance
- [x] Leave unestablishable sites alone and record them
- [x] Task 2 — `tests/optimizer/test_walker.py:2426` / `:2455`: drop the `Revision 3` tail, keep the verified spec-and-Decision citation
- [x] Census `tests/optimizer/test_walker.py` for other review-round ids and treat them the same way
- [x] Task 3 (Worker 0, mid-pass) — `django_strawberry_framework/connection.py:1885`'s stale `WIP-ALPHA-033-0.0.9` card id, and the spec-033 quotation ordering constraint

---

## Build report (Worker 2)

### Baselines, taken before anything was read

`HEAD` is **not** this pass's baseline for three of the four files. Cohort F had already edited `connection.py`, `tests/test_permissions.py`, and `tests/optimizer/test_walker.py`; only `tests/test_routers.py` was byte-identical to `HEAD`.

| File | prepass vs `git show HEAD:` | What cohort F had already closed there |
|---|---|---|
| `tests/test_routers.py` | IDENTICAL | nothing |
| `django_strawberry_framework/connection.py` | DIFFERS | 2 block-orphans (`M1` -> `spec-030 Decision 7` x2) |
| `tests/test_permissions.py` | DIFFERS | 1 block-orphan (`spec-034 Decision 9`, `Revision 3` dropped) |
| `tests/optimizer/test_walker.py` | DIFFERS | 6 block-orphans (the hyphenated `Decision-N` family) |

Pre-pass copies were taken outside the repository before any edit (`<scratchpad>/cohortI-027/prepass-027/`) alongside `git show HEAD:` copies (`head-027/`), and every measurement below names which baseline it is against. Nothing was reverted, stashed, checked out, or restored at any point.

**Churn during the pass: none.** `git status --porcelain` was captured at pass start (`status-before-027.txt`, 81 rows) and again at the end (`status-after-027.txt`). The only differences are three rows: `tests/test_routers.py` becoming ` M` and this artifact appearing, both this pass's own work, plus cohort H publishing `bld-slice-13-027-shipped_card_spec_staleness.md`. A `diff` of each of the four files against its pre-pass copy immediately before writing confirmed no other session had touched them.

### The spelling set, derived from the corpus

Derived by scanning every docstring and every contiguous comment run in the four files for `Decision`-adjacent forms and short-form ids, then reading each family's occurrences. Confirmed in these files rather than assumed from the dispatch.

**The `Decision` concept, over the 146 pre-pass occurrences in this partition:**

| Spelling | occurrences | block-orphans | where |
|---|---|---|---|
| `Decision N` (spaced, canonical) | 142 | 55 | all four files |
| `DN` short form | 2 | 1 | `test_routers.py:3015` (`Helper-reuse D3`, orphan), `test_walker.py:4143` (`D1`, resolved) |
| `Decision\n<N>` (wrapped across a line break) | 1 | **0** | `test_routers.py:1647` |
| `Decision-N` (hyphenated) | 1 | 0 | `test_walker.py:3419` (resolved; the rest of this family was cohort F's) |
| `Spec Decision N` | 0 | 0 | absent from this partition |

**A sixth spelling, of the spec id rather than of `Decision`, and it is the one that matters here.** `Spec-NNN` with a capital S: **21** occurrences in `tests/test_routers.py`, **52** repo-wide across the 425 tracked `.py` files, **174** in `docs/`. Every `Decision`-census instrument in this cycle matched `spec-NNN` case-sensitively, so any block whose only card id is capitalized is reported as an orphan by all of them. This is a fifth distinct instrument error in measuring this cycle's citation populations, after package-only globbing, the first-`#"`-occurrence bug, and cohort G's two membership errors.

**The dispatch's own worked example is refuted by it.** The brief singles out `tests/test_routers.py:1647` as "a newline-wrapped `Decision` / `19`" block-orphan and as "exactly such a wrapped case". The wrap is real — `Decision` ends line 1647 and `19` opens 1648 — but the enclosing docstring's summary line reads `"""Spec-046 row 28: injection opts out of revalidation, not of the wrappers.`, so the block **names its card** and the reference is not an orphan. My instrument finds the wrap (it joins comment runs and docstrings whole, blanking each comment's leading `#` so a reference can span the break) and still grades the site resolved.

### Per-file census

Three instruments over the same four files, so each difference is itself a measurement. Script: `<scratchpad>/cohortI-027/census_i027.py` (and its `census_i027_ci.py` sibling, identical but for one `re.IGNORECASE`).

- **L (line-scoped)** — an occurrence is "bare" iff no `spec-NNN` appears on the **same line**. The instrument shape the dispatched figures came from.
- **B-cs (block-scoped, case-sensitive `spec-NNN`)** — whole docstrings and whole contiguous comment runs as the unit; the shape cohorts C and F used.
- **B-ci (block-scoped, case-insensitive)** — the same, with `Spec-NNN` counted as a card id. **This is the census this pass acted on.**

Measured at the pre-pass working tree (i.e. after cohort F's edits):

| File | occurrences | L-bare | B-cs orphan | **B-ci orphan** | L false positives (vs B-ci) | L misses |
|---|---|---|---|---|---|---|
| `tests/test_routers.py` | 47 | 34 | 27 | **14** | 20 | 0 |
| `django_strawberry_framework/connection.py` | 42 | 31 | 20 | **20** | 11 | 0 |
| `tests/test_permissions.py` | 21 | 20 | 19 | **19** | 1 | 0 |
| `tests/optimizer/test_walker.py` | 36 | 4 | 3 | **3** | 1 | 0 |
| **TOTAL** | **146** | **89** | **69** | **56** | **33** | **0** |

**Line-scoped false-positive rate on this population: 33 of 89 = 37%** — a third independent measurement of that instrument shape's error rate, after cohort C's 61% and cohort F's 29%. Every one of the 33 is the adjacent-line or wrapped-citation shape.

**Where the dispatched figures were wrong.**

- **`tests/test_routers.py`: 14 block-orphans, not 26 (or 27).** The brief's "26 plus a newline-wrapped `Decision` / `19` at 1647" reproduces my case-sensitive column exactly (27), so the arithmetic was right and the instrument was not. **13 of the 27 sit in blocks whose only card id is the capitalized `Spec-046`** (lines 1388, 1420, 1463, 1465, 1647, 1682, 1867, 1896, 2068, 2074, 2909, 3021, plus the wrapped 1647 pair counted once each). The wrapped site the brief nominated is one of the 13.
- **`connection.py`: 20, exactly as dispatched.** Both instruments agree; there is no capitalized `Spec-NNN` in this file.
- **`tests/test_permissions.py`: 19, exactly as dispatched.**
- **`tests/optimizer/test_walker.py`: 3 block-orphans, a population the dispatch did not name at all.** The brief routed this file for Task 2 only. Censusing it while in it — which the dispatch asked for on review-round ids — surfaced three genuine `Decision N` orphans as well.

So the dispatched 65 (26 + 20 + 19) is **56** under the corrected instrument, and the fourth file adds 3, for **56 block-orphans in the partition**.

**Fence-wide consequence, measured over all 425 tracked `.py` files.** Post-pass, spaced `Decision N` stands at **1225 occurrences, 189 block-orphans case-insensitive / 203 case-sensitive**. Adding back this pass's 54 spaced closures gives a pre-pass fence figure of **243 case-insensitive / 257 case-sensitive** — and 257 is precisely the number the dispatch carries from cohort F. **The fence-wide 257 is the case-sensitive figure; the real one is 243**, and 13 of the 14-site difference is in this cohort's own `tests/test_routers.py`. The remaining inflation is in `tests/types/test_base.py` (11 -> 9), which is outside this partition.

**After this pass: 146 occurrences, 1 block-orphan across the four files** (`tests/test_permissions.py:2069`, length-blocked — see `### Sites left UNRESOLVED`). The 13 case-sensitive residues in `test_routers.py` are unchanged and are not repairs; they are enumerated above so a reviewer re-running a case-sensitive census does not read them as missed work.

### Sites repaired, with the evidence that established each owner

55 edits across the four files: 54 citation attributions plus Task 3's card-id repair. Owners were established by reading the cited Decision and confirming it states what the comment claims; where a sibling card carries an identically-numbered Decision, the alternative is **disproved by measurement** rather than the winner asserted. Rows marked **disproof** rest on a count or a heading that makes the competing candidate impossible, not on a subject match.

#### `tests/test_routers.py` — 14 sites across two cards

The file is dual-card by its own module docstring: "Both dependency states are exercised (spec-041 Decision 8, as amended by spec-046 Decision 2)". Both cards are live candidates for every site, which is why each row names its disproof.

| Line | Was | Now | Evidence |
|---|---|---|---|
| 1490 | `(Decision 3)` | `(spec-041 Decision 3)` | `spec-041 ### Decision 3 — The symbol is DjangoGraphQLProtocolRouter` states it verbatim: "**The submodule declares `__all__ = ("DjangoGraphQLProtocolRouter",)`.** ... Pinning `__all__` to the one public symbol keeps the module's star surface clean". The assertion under the comment is `routers_module.__all__ == ("DjangoGraphQLProtocolRouter",)`. **Disproof of the sibling:** `spec-046 ### Decision 3` is "`django_application` is required; omission fails at construction with no compatibility fallback" — a different subject entirely |
| 2974 | `(Decision 3)` | `(spec-041 Decision 3)` | Same Decision, same paragraph of it: "makes `from ...routers import *` **opt into the router**: `import *` calls `__getattr__`, which runs `require_channels()`". The comment reads "`__all__` names the lazy symbol, so `import *` reaches for it and fires the guard" |
| 3015 | `(Helper-reuse D3)` | `(spec-041 Helper-reuse D3)` | `spec-041` `## Helper-reuse obligations (DRY)` line 1583: "- [ ] **D3** — the guard has **no memoization** and the `__getattr__` caches only ...". The comment reads "No stale negative caching (Helper-reuse D3)". `spec-041` uses this exact spelling itself at lines 199 and 375. **Disproof:** `grep -E '\bD3\b' spec-046-transport_security-0_0_14.md` returns **0** |
| 1991 | `(Decision 12)` | `(spec-046 Decision 12)` | `spec-046 ### Decision 12 — Maximum connection lifetime is documented and seamed, not silently enforced`. The docstring reads "it imposes no ceiling for the same reason it imposes no maximum connection lifetime (Decision 12)". **Disproof:** `grep -cE '^### Decision ' spec-041-channels_router-0_0_14.md` returns **11** — spec-041 has no Decision 12 |
| 2241, 2269, 2446, 2862 | `Decision 19` | `spec-046 Decision 19` | `spec-046 ### Decision 19 — A Django-backed WebSocket Host boundary, beside Channels' Origin check`, whose body carries each site's claim: "projects the handshake's Host-related metadata into a minimal Django `HttpRequest` and calls the public `request.get_host()`. The package parses and matches no hostnames itself" (2241's oracle-not-reimplementation claim); the plain-`HttpRequest` projection asymmetry (2269); "**Host and Origin stay two separate checks** ... Passing one must never substitute for passing the other" (2446); and the wrapper ordering outside `AuthMiddlewareStack` (2862). **Disproof, and it is decisive repo-wide:** `spec-046` is the **only** spec in `docs/SPECS/` with 19 or more `### Decision` headings (19; the next highest is `spec-036` at 15). No other document can own a `Decision 19` |
| 3997, 4057, 4107 | `Decision 16` | `spec-046 Decision 16` | `spec-046 ### Decision 16 — Revocation is connection-scoped and gated at the WebSocket adapter's outbound frame seam` carries all three claims: the per-connection actor lease and its blast radius, the window at the frame checkpoint, and "The gated frame types are deliberately `next` ... `ka` and every other connection-control frame delegate to upstream unchanged". **Disproof:** same census — only `spec-046` reaches 16 |
| 3952, 3963 | `Decision 11` | `spec-046 Decision 11` | `spec-046 ### Decision 11`'s body states 3952's claim verbatim: "There is no artificial minimum interval, no second setting, and **no background task**, and an idle authenticated socket performs **zero** database reads — freshness is spent at event boundaries, not on a timer". 3963's "which Decision 11 rejects" points at that same sentence. **Disproof:** `spec-041 ### Decision 11` is "The package request contract works under Channels: `request_from_info()` learns the Channels context shape" — not a revalidation contract |
| 3877 | `Decision 11` | `spec-046 Decision 11` | **Weakest attribution in this pass; the card is certain and the Decision number is the author's.** The docstring reads "Decision 11, the lease held through the send". A per-decision-block scan of `spec-046` for `lease` puts **17** of its 18 architectural-decision occurrences under `### Decision 16` and **0** under `### Decision 11`; the lease is D16's subject. D11 is still navigable to it — D11's default consumer "revalidates the session actor at both of [Decision 16]'s checkpoints" — so `spec-046` is right either way, and renumbering 11 -> 16 is a substantive claim about the author's intent that this pass declined to make. Flagged under `### Notes for Worker 1` |

#### `django_strawberry_framework/connection.py` — 17 sites across two cards with colliding Decision numbers

**This file is the adjacent-wrong-candidate trap in its purest form.** Its module docstring pins `Spec: docs/SPECS/spec-030-connection_field-0_0_9.md`, and it also carries 8 `spec-033` references. `spec-030` and `spec-033` **both** have Decisions 3-10, on different subjects, and both are plausible in this module. Every row below therefore names which card and disproves the other.

| Line | Reference | Now | Evidence, and the disproof of the sibling |
|---|---|---|---|
| 134 | `Decision 4` | `spec-030 Decision 4` | `spec-030` line 19: "**P2 — `totalCount` selection-gated and carried on the connection instance.** [Decision 4] now counts only when the `totalCount` field is selected ... and attaches the count to the connection **instance** via the `resolve_connection` override". The comment defines `_TOTAL_COUNT_ATTR` as the "field name carried on the connection instance" under "the selection-gating contract". **Disproof:** `spec-033 ### Decision 4` is windowed-prefetch planning under a reserved `to_attr` |
| 1096 | `Decision 3` | `spec-030 Decision 3` | `spec-030 ### Decision 3 — Build on Strawberry's native Relay machinery, but own the `first` + `last` guard`. The docstring: "The package's own pagination guard (Decision 3): Strawberry's `SliceMetadata.from_arguments` applies `first` then `last` without a mutual-exclusivity check". **Disproof:** `spec-033 ### Decision 3` is "Walker recognition is definition-metadata-driven, not name-pattern guessing" |
| 1349 | `Decision 4` | `spec-030 Decision 4` | Same Decision as 134; the function generates the `<TypeName>Connection` carrying `totalCount`, which is that Decision's heading ("`DjangoConnection[T]` base plus per-target concrete connection classes") |
| 1434 | `Decision 5` | `spec-030 Decision 5` | `spec-030` line 77 makes this cross-reference itself: "Cache keyed on `target_type` (one connection shape per node type — no per-field override, per [Decision 5](#decision-5--factory-function-mechanism-meta-only-derivation)". The docstring is word-for-word that clause |
| 2023 | `Decision 5` | `spec-030 Decision 5` | `spec-030 ### Decision 5 — Factory-function mechanism, Meta-only derivation`; the docstring opens "Meta-only derivation (Decision 5)". Heading-level match |
| 1382 | `Decision 7` | `spec-030 Decision 7` | `spec-030 ### Decision 7`'s consumer-`resolver=` paragraph: "**selecting `totalCount` against a consumer-resolver return that is not a `QuerySet` raises a clear package `GraphQLError`** ... This is symmetric with the sidecar-input rule above". The docstring says "symmetric with the sidecar-input rule in `_post_process_consumer_*`". **Disproof:** `spec-033 ### Decision 7` is plan-cache key hygiene |
| 1472 | `Decision 7` | `spec-030 Decision 7` | The other half of the same paragraph: "a non-queryset iterable (list / generator) may be paginated only when **no** `filter:` / `orderBy:` input is supplied" |
| 1617 | `Decision 7 / Decision 10` | `spec-030 Decision 7 / Decision 10` | D7 is the composition pipeline the function runs (steps 2-6 named in order in both); D10 is "Sync + async resolver paths reuse the Relay-foundation helpers" |
| 1685 | `Decision 6` | `spec-030 Decision 6` | `spec-030 ### Decision 6 — Sidecar-derived arguments via a synthesized resolver signature`. **Disproof:** `spec-033 ### Decision 6` is "Fallback shapes: sidecar input, divergent aliases, hints, and scalar-only connections"; `spec-032 ### Decision 6` is relation-as-Connection synthesis |
| 2029 | `Decision 6 / Decision 7` | `spec-030 Decision 6 / Decision 7` | Same pair; the site is in a second paragraph of the same docstring as 2023, separated by a body break, with `spec-033` D6/D7 live as wrong candidates — cohort C's R3 shape |
| 1410 | `Decision 10` | `spec-030 Decision 10` | `spec-030 ### Decision 10` closes its first paragraph "(the unawaited coroutine is closed before the raise)" — the exact discipline the comment mirrors. `grep -rn "close-before-raise" docs/SPECS/` returns **0**, so the phrase itself resolves nowhere and the contract had to be found by content |
| 1752 | `Decision 10` | `spec-030 Decision 10` | Its bolded paragraph: "**Dispatch shape — the connection field is dispatch-frozen at build time, NOT per-call.**" The docstring: "Sync-vs-async dispatch is committed per-construction (Decision 10)" |
| 234 | `Decision 5` | `spec-033 Decision 5` | `spec-033 ### Decision 5 — Connection-class fast path with annotation-presence detection and a per-parent fallback` names `_WindowedConnectionRows` explicitly and describes exactly this marker's `rows` / `fallback` pair. **Disproof:** `spec-030 ### Decision 5` is the factory-function mechanism — nothing about windowed prefetch rows |
| 312 | `Decision 5` | `spec-033 Decision 5` | The same Decision's bullet list *is* the "single edge / cursor / `pageInfo` / `totalCount` derivation" this docstring names |
| 1204 | `Decision 5` | `spec-033 Decision 5` | "`connection.py::DjangoConnection.resolve_connection` and the generated `<TypeName>Connection.resolve_connection` path detect `_WindowedConnectionRows` after the existing `first`+`last` guard and before delegating to Strawberry's list slicing. The fast path builds the Relay object there" |
| 1229 | `Decision 5` | `spec-033 Decision 5` | The same Decision's `totalCount` bullet: "the generated total-count connection path must branch before `_guard_total_count_countable` / `.count()` so the marker is treated as an annotated optimized source". Verbatim. A second-paragraph site with `spec-030` D5 live as the wrong candidate, so it is attributed rather than left to the block |
| 637 | `Decision 4 / Decision 5` | `spec-033 Decision 4 / Decision 5` | `spec-033 ### Decision 4`'s bullet is titled "**Deterministic order (a cursor-parity invariant, not a tidiness refactor)**" and states "if the plan-time window order and the resolve-time order ever diverge ... the window's row numbers stop agreeing with the pipeline's offset cursors". The docstring names "the cursor-parity invariant's resolve-time half". D5 is the consuming fast path |

#### `tests/test_permissions.py` — 18 sites, all `spec-034`

The file's home card is stated in its own module docstring ("Coverage homes for the cascade contract (spec-034)"), and cohort F left `spec-034 Decision 9` at line 1906 as the in-file precedent this pass matched. Every site was still checked against `spec-034`'s Decision text individually.

| Lines | Reference | Owner | Evidence |
|---|---|---|---|
| 172 | `Decision 5 / 9 / 10` | `spec-034 Decision 5 / 9 / 10` | `### Decision 5 — The cascade walk: call-time model-graph walk, registry primary lookup, `has_custom_get_queryset()` gate, subquery intersection`; the section header it annotates is "Cascade foundation" |
| 829, 857 | `Decision 8` | `spec-034 Decision 8` | `### Decision 8 — Multi-DB pinning: `.using(queryset.db)` — the resolved alias, not `_db``. Both sites say "the caller's *resolved* alias — `queryset.db` ... not the private `_db`". Heading-level verbatim |
| 938, 975 | `Decision 6` | `spec-034 Decision 6` | `### Decision 6 — Hidden-FK semantics: row exclusion is the cascade contract; resolver-level nulling stays the relation contract`. The two docstrings pin row exclusion and hidden-vs-missing indistinguishability |
| 1855, 1871 | `Decision 9` | `spec-034 Decision 9` | `### Decision 9 — `fields=` scoping validates loudly with `ConfigurationError``. Both tests assert a `ConfigurationError` naming field / model / cascadable set. Corroborated by the same file's line 1906, already `spec-034 Decision 9` |
| 2007, 2038 | `Decision 10` | `spec-034 Decision 10` | `### Decision 10 — Sync/async contract: `SyncMisuseError` on async hooks from the sync walk; the async variant wraps the walk in `sync_to_async``. Both halves appear, one per site |
| 2344, 2352, 2412 | `Decision 7` | `spec-034 Decision 7` | `### Decision 7 — Cascade performance: lazy subquery composition — zero added round-trips`. All three sites say "zero round-trips" / "adds zero round-trips" |
| 2427 | `Decision 12 / Edge case "FK-id elision interaction"` | `spec-034 Decision 12 / ...` | `spec-034` line 427: "- **FK-id elision interaction** — elision already falls back when a target hook must run ...; cascading targets therefore never elide. No change; pinned." The cited edge case exists under that exact name, so the whole parenthetical resolves once the card is named |
| 2513, 2603, 2653, 2687 | `Decision 11` (2513 also 12) | `spec-034 Decision 11` | `### Decision 11 — The existing `check_<field>_permission` filter/order gates survive unchanged`, whose body states 2687's claim verbatim: "A denial therefore cannot leak hidden-row existence: the error fires on *input shape* alone, identically whether hidden rows exist or not" |
| 2739 | `Decision 12` | `spec-034 Decision 12` | `### Decision 12 — Connection / node / list composition is contract-pinning, not new code`, whose body owns the nested-relation `Prefetch`-downgrade transitivity the docstring pins |

**Disproof for the whole file, run once rather than per row:** the two candidate siblings a reader might reach for are `spec-045-visibility_boundary-0_0_14.md` (visibility, the same seam) and `spec-036-mutations-0_0_11.md` (cited once in this file at line 43). `grep -cE '^### Decision ' spec-045-...md` returns **8**, so spec-045 cannot own Decisions 9, 10, 11, or 12 at all, and its D5-D8 are queryset-shape rejections / typed error contract / no version bump / threat model — none of which any site claims. `spec-036`'s D5-D12 are the mutation surface (`DjangoMutation`, `FieldError`, resolver pipeline, primary-type resolution); no subject overlaps.

#### `tests/optimizer/test_walker.py` — 3 attribution sites

| Line | Reference | Now | Evidence |
|---|---|---|---|
| 235 | `Decision 7` | `spec-015 Decision 7` | `spec-015-relay_interfaces-0_0_5.md ### Decision 7: optimizer and projection invariants` is the only Decision in the repo that owns this claim, and its body cites the test's own symbols: "**Primary-key projection.** ... the optimizer's `only()` projection must include the concrete primary-key attname. Reference: `walker.py::_walk_selections` ... Strawberry resolves Relay `id` via `_resolve_id_default`, which reads `root.__dict__[attname]` first". **Disproof of the file's two dominant cards:** `spec-033 ### Decision 7` is plan-cache key hygiene; `spec-035 ### Decision 7` is "G3 — narrow, do not multi-plan". Neither concerns pk projection or lazy loads |
| 4871 | `Decision 5` | `spec-035 Decision 5` | `spec-035 ### Decision 5 — G2 — FK-id elision stays enabled under non-`QUERY` operations`. The docstring: "elision stays recorded under a mutation (elision stays enabled - it is operation-independent)". Heading-level verbatim. **Disproof:** `spec-033 ### Decision 5` is the connection fast path; `spec-036 ### Decision 5` is the public mutation surface |
| 4898 | `Decision 9` | `spec-033 Decision 9` | `spec-033 ### Decision 9 — The `edges { node }` selection helpers consolidate into the walker` — literally a helper move, and its body says "`extension.py` imports them from the walker", which is why the no-regression pin lives in `test_extension.py` as the comment states. **Disproof:** `spec-035 ### Decision 9` is "Version bumps are owned by the joint `0.0.10` cut" and cannot be a helper move |

### Task 2 — the two sites contradicting a contract on their own card's spec

**The contract, read at source before acting.** `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` line 15, `Revision 3`, finding (4): "**doc-reference hygiene** — a production or test comment on this card's surface cites a spec, a card, or a symbol path, never a per-cycle review artifact, a review-round or finding id (`Revision N`, `P<n>`), or a build-plan step ([`AGENTS.md`][agents])." The same line closes "Findings 1-3 are behavior corrections; **4 is a comment-hygiene contract**." It says what the dispatch says it says, and it is normative.

Both cited Decisions were verified to exist and to state the claim before the tail was dropped.

| Line | Was | Now | Verification |
|---|---|---|---|
| 2426 | `(spec-033 Decision 11, cursor-parity / Revision 3)` | `(spec-033 Decision 11, cursor-parity)` | `spec-033 ### Decision 11 — Module and test-file locations` exists. The citation is the one **the spec itself makes** for this contract: `### Decision 4`'s cursor-parity bullet reads "the effective ordering ... hoisted to [`plans.py`][plans] ([Decision 11](#decision-11--module-and-test-file-locations))". So `Decision 11, cursor-parity` names the hoist location for the cursor-parity rule, which is exactly what the test pins (a non-pk `Meta.ordering` column propagating to the prefetch queryset's own `ORDER BY`) |
| 2455 | `(spec-033 Decision 6 / Revision 3)` | `(spec-033 Decision 6)` | `spec-033 ### Decision 6 — Fallback shapes: sidecar input, divergent aliases, hints, and scalar-only connections`, whose closing paragraph states the test's claim: "`pageInfo`-only and `totalCount`-only selections are **planned**, not fallbacks ... with no node-child scalars to narrow to, the window is projected to the minimal pk / connector / deterministic-order columns rather than the full row" |

Nothing was substituted for the dropped id. Both citations already carried everything a reader can use, and both lines got shorter (72 -> 59 and 64 -> 51 characters).

**Census of other review-round ids in `tests/optimizer/test_walker.py`.** `grep -nE '\b(Revision|Finding|Round|Pass|Slice)[ -]?[0-9]+|\bP[0-9]\b|\b[HML][0-9](-[0-9])?\b|\bAR-[HML][0-9]+|\bSR-[0-9]+|\bCR-[0-9]+|\bDRY-[0-9]+'` returns exactly **three** lines: 2426, 2455, and 4888. The third is `# TODO(spec-035 Slice 3): add G3 walker narrowing pins here.` and is **deliberately kept** — `AGENTS.md` mandates that form for a staged-but-unbuilt slice ("staged-but-unbuilt slices get a source-site `# TODO(spec-NNN slice N): ...` naming the doc and slice"), so it is a sanctioned anchor, not build provenance. The population is closed at 0 unsanctioned ids.

### Task 3 — the stale `WIP-ALPHA-033-0.0.9` card id, and the spec-033 quotation ordering constraint

Dispatched by Worker 0 mid-pass, in a file this cohort already owned. Both of Worker 0's factual claims were re-derived rather than accepted, and one of its two numbers is off.

**The card id.** `django_strawberry_framework/connection.py:1885` read `` reachable as the cooperation seam ``WIP-ALPHA-033-0.0.9``'s ``.

- `grep -oE '(WIP|TODO|DONE)-[A-Z]*-?033-[0-9_.]+' KANBAN.md | sort | uniq -c` returns **`15 DONE-033-0.0.9`** and nothing else. Worker 0's dispatch said 11; the measured count is 15. **No `WIP-` or `TODO-` spelling for card 033 survives anywhere in `KANBAN.md`.**
- The 2026-07-30 renumber is accounted for: the current spelling was read off `KANBAN.md` itself rather than assumed to be `DONE-` plus the same number. A broader `grep -noE '[A-Z]+-[A-Z]*-?033[^ ]*' KANBAN.md` returns only `DONE-033-0.0.9` forms, so no other id spelling for that card exists on the board.

Repaired to `` ``DONE-033-0.0.9``'s ``. The line **shrank** from 63 to 58 characters (`WIP-ALPHA-033-0.0.9` is 19 characters, `DONE-033-0.0.9` is 14), so there was no line-limit pressure and no reflow. Applied through the same batch instrument, with the anchor `` ``WIP-ALPHA-033-0.0.9``'s `` asserted to occur exactly once in the file before anything was written.

**Cohort H's quotation claim is CORRECT, and the ordering constraint is real.** `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` **line 106** (in `## Current state`, the `- **Nested connections are unplanned and per-parent.**` bullet) quotes this docstring verbatim. The exact quoted string, for the spec side to match against:

```
its docstring documents both the seam ("the cooperation seam `WIP-ALPHA-033-0.0.9`'s window-pagination planning will use")
```

**Sequencing, stated explicitly as Worker 0 asked.** This `.py` edit has landed **first**. The spec-side quotation at `spec-033` line 106 must now follow it, and `spec-033` is **not** in this cohort's writable set — it was not touched, and a Worker 1 cohort owns it.

**A second staleness in the same quotation, which the dispatch did not name.** The spec quotes the comment as `"... window-pagination planning **will use**"`; the live comment says `"... window-pagination planning **uses**"`. So the quotation was **already** inexact before this pass, on tense as well as on the card id: the comment was moved to present tense when the card shipped and the spec's quotation never followed. The spec-side repair therefore has two words to change, not one. Recorded under `### Notes for Worker 1`.

**A sibling site outside this cohort's writable set, left alone.** `grep -rn 'WIP-ALPHA-033' --include='*.py' .` returns **two** rows: `connection.py:1885` (repaired) and `django_strawberry_framework/types/finalizer.py:660` — `` connection pipeline is ``WIP-ALPHA-033-0.0.9``'s scope. ``. Same defect, same measurement, same repair; `types/finalizer.py` is fenced from this cohort and is dirty at this pass's baseline (cohort A's partition). Reported, not touched.

The five `docs/SPECS/spec-{030,031,032,033,034}-*.md` files that also carry `WIP-ALPHA-033-0.0.9` are a **different** class and were deliberately not examined further: in a spec's revision log ("Revision 1 — initial draft authored from the `WIP-ALPHA-033-0.0.9` card body") the pre-ship id is the historically correct one. Only the line-106 quotation is a staleness, because it quotes live source.

### Sites left UNRESOLVED, and why

Reporting these accurately is the outcome the dispatch asked for. Each was investigated and **not** touched.

| Site | Reference | Measurement | Why left |
|---|---|---|---|
| `tests/test_permissions.py:2069` | `(Decision 10)` | Owner **is** established — `spec-034 Decision 10`, on the same evidence as its siblings at 2007 and 2038, which this pass repaired. The blocker is purely mechanical: the line is a one-line docstring already **103** characters long, and the 9-character insert takes it to **112**, past the `max-line-length = 110` ceiling `pyproject.toml` declares. The block is a single line, so there is no body line to attach the card to, and splitting the docstring into summary-plus-body would add lines and restructure prose this pass is not otherwise editing | Reflow is the mechanism that splits a citation across lines, which is the defect cohorts A, E, G and Slice 4 exist to repair. Cohort C left `rest_framework/sets.py:685` and cohort F left the `Revision 3` tail at `test_permissions.py:1906` for the same reason. A reader is two tests away from `spec-034 Decision 10` at line 2038 |

**One deliberate non-repair that is not an unresolved site.** `tests/test_routers.py:3877`'s `Decision 11` is attributed (`spec-046` is certain and measured) but its **number** is likely the author's slip — the lease it names is `spec-046 Decision 16`'s subject, measured at 17 of 18 `lease` occurrences under D16 and 0 under D11. Renumbering is a claim about intent, not a citation repair, so it is escalated rather than made. Recorded in the repair table and again under `### Notes for Worker 1`.

**One population deliberately not swept.** The 21 capitalized `Spec-046` occurrences in `tests/test_routers.py` were left as they are. They resolve for a human reader; normalizing them is 21 lines of spelling churn; and the instrument fix belongs in the census tooling, not in the prose. The class is reported under `### Notes for Worker 1` with its repo-wide measurement.

### Files touched

Grounded in `git status --porcelain` and in a `diff` of each file against a pre-pass copy held outside the repository. Changed-line counts are from that diff; every file's total line count is byte-for-byte unchanged.

- `tests/test_routers.py` — 14 sites (2 -> `spec-041 Decision 3`, 1 -> `spec-041 Helper-reuse D3`, 1 -> `spec-046 Decision 12`, 4 -> `spec-046 Decision 19`, 3 -> `spec-046 Decision 11`, 3 -> `spec-046 Decision 16`). 14 changed lines, 5679 total, unchanged.
- `django_strawberry_framework/connection.py` — 18 sites: 17 attributions (12 -> `spec-030`, 5 -> `spec-033`) plus Task 3's `WIP-ALPHA-033-0.0.9` -> `DONE-033-0.0.9` at line 1885. 18 changed lines, 2063 total, unchanged.
- `tests/test_permissions.py` — 18 sites, all -> `spec-034`. 18 changed lines, 2782 total, unchanged.
- `tests/optimizer/test_walker.py` — 5 sites (3 attributions -> `spec-015` / `spec-035` / `spec-033`; 2 `Revision 3` tails dropped per Task 2). 5 changed lines, 5634 total, unchanged.
- `docs/builder/bld-slice-14-027-decision_n_concentrations.md` — this artifact.

### Tests added or updated

None. This pass adds no executable statement and no contract; there is nothing new for a test to pin. The existing suite is the regression check and was run.

### Validation run

Every command from the repository root. No `--cov*` flag anywhere in this pass.

| Check | Command | Result |
|---|---|---|
| Format (scoped, never `.`) | `uv run ruff format <the 4 files>` | `4 files left unchanged`, exit 0 |
| Lint (scoped) | `uv run ruff check --fix <the same 4 files>` | `All checks passed!`, exit 0 |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check <the 4 files>` | exit 0 |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md).` exit 0 |
| Pre-commit (all 5 hooks) | `uvx pre-commit run --files <the 4 files>` | kanban-constants, source-layout, ruff-format, ruff-check, citations — **all Passed** |
| Focused tests | `uv run pytest tests/test_routers.py tests/test_permissions.py tests/optimizer tests/test_connection.py --no-cov -q` | **1092 passed, 1 skipped in 10.04s** (re-run after Task 3) |
| Wrapped-citation postcondition | `<scratchpad>/cohortI-027/wrapcheck_i027.py` over the 4 files | **0** unclosed `#"` after, and **0** over the pre-pass copies, so none was introduced and none pre-existed |

**Citation-gate contribution: zero, measured per file rather than inferred from the global count.** 782 is the count both before and after this pass; cohort C recorded 779, and the rise since is other cohorts' work. The mechanical check that *this* pass added and removed no gated reference is a per-file count against the pre-pass copies:

| File | `path::Symbol` before / after | `#"` before / after |
|---|---|---|
| `tests/test_routers.py` | 10 / 10 | 4 / 4 |
| `django_strawberry_framework/connection.py` | 11 / 11 | 0 / 0 |
| `tests/test_permissions.py` | 5 / 5 | 0 / 0 |
| `tests/optimizer/test_walker.py` | 4 / 4 | 0 / 0 |

Every one SAME. The count did not rise because this pass adds `spec-NNN Decision N` prose references, which `check_citations.py` does not resolve — it is `path::Symbol`-only, which is exactly why no instrument ever saw this defect class.

**The wrapcheck scans every `#"` on each line, not the first.** The `test_routers.py` line at 2862 carries a `#"before authentication"` citation immediately after the opening `"""`, and this pass extended that same line; a first-occurrence-only instrument is the bug that made a Worker 0 census miss a real site, so the loop advances past each match rather than breaking.

**Focused-scope justification.** `tests/test_routers.py` and `tests/test_permissions.py` are the direct mirrors of two touched files. `connection.py` is imported by the whole Relay surface, so `tests/optimizer` (the walker's windowed-prefetch consumers), `tests/test_connection.py`, and `tests/optimizer/test_walker.py` itself are all in scope; `tests/optimizer` was run whole rather than file-by-file for that reason.

#### Churn classification, every path in `git status --porcelain`

| Owner | Paths |
|---|---|
| **This pass (cohort I)** | `tests/test_routers.py`, `django_strawberry_framework/connection.py`*, `tests/test_permissions.py`*, `tests/optimizer/test_walker.py`*, and this artifact |
| Cohort F (`bld-slice-11-027-...`) | 26 `.py` files including the three starred above, + its artifact |
| Cohorts A / B / C / E / G | `consumers.py`, `routers.py`, `filters/*`, `types/*`, `mutations/*`, `orders/*`, `rest_framework/*`, `optimizer/extension.py`, `utils/inputs.py`, `docs/SPECS/spec-{033,037,039,040,041,045,046,055}*.md`, `docs/SPECS/appx/spec-{001,009,015}-*-rationale.md`, + their artifacts |
| Concurrent spec-028 session | `orders/*`, `types/base.py`, `docs/SPECS/spec-028-*.md` + its rationale, `examples/fakeshop/apps/library/orders.py`, `examples/fakeshop/test_query/test_library_api.py`, `tests/orders/*`, `bld-slice-{1,2}-028-*.md`, `build-028-*.md` |
| Worker 0 | `docs/builder/build-027-filters-0_0_8.md` |

\* mixed with cohort F's hunks, on distinct lines. Nothing was reverted, and `git status` gained exactly one row during this pass (`tests/test_routers.py`), so no concurrent session moved anything into or out of this partition mid-pass.

### Executable-token identity proof

Instrument: `<scratchpad>/cohortI-027/tokid_i027.py`, written fresh in a cohort-private subdirectory. It tokenizes with `tokenize`, drops `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` / `ENCODING` / `ENDMARKER` and every **statement-position** `STRING` (a `STRING` preceded by `NEWLINE`/`INDENT`/`DEDENT`/`ENCODING`/`NL` and followed by `NEWLINE`), and compares the remaining `(type, string)` **sequence element-wise**, reporting the first divergent index. Every **other** string literal is KEPT — an assignment RHS, a dict key, a call argument — which is the case a naive instrument drops and thereby passes.

**Two baselines, because `HEAD` is not "before this pass" for three of the four files.** Both were run, and they agree — which is itself a measurement: cohort F's edits to those three files also changed no executable token.

| File | vs pre-pass worktree copy | vs `git show HEAD:<path>` | exec tokens |
|---|---|---|---|
| `tests/test_routers.py` | IDENTICAL | IDENTICAL | 18091 |
| `django_strawberry_framework/connection.py` | IDENTICAL | IDENTICAL | 5088 |
| `tests/test_permissions.py` | IDENTICAL | IDENTICAL | 12030 |
| `tests/optimizer/test_walker.py` | IDENTICAL | IDENTICAL | 21135 |

`0 DIFFERENT` across all four, against both baselines. Re-run **after** `ruff format` / `ruff check --fix`, so the verdicts describe the tree as it stands.

#### Challenge set — six mutations plus a control, landing asserted before the verdict was read

Asserted in the script's own `ASSERTED` dict, written before the run: `C0 IDENTICAL | C1 DIFFERENT | C2 DIFFERENT | C3 DIFFERENT | C4 IDENTICAL | C5 IDENTICAL | C6 DIFFERENT`. Reference file: `django_strawberry_framework/connection.py` at `HEAD` (5088 exec tokens), except C5, which is anchored on the post-pass comment text this cohort wrote.

| Case | Mutation | Asserted | Verdict | tokens | First divergence |
|---|---|---|---|---|---|
| C0 control | byte-identical copy | IDENTICAL | **IDENTICAL** | 5088 vs 5088 | — |
| C1 operator flip | `if resolver is None:` -> `is not None:` | DIFFERENT | **DIFFERENT** | 5088 vs 5089 | token 4667 `(NAME,'None')` != `(NAME,'not')` |
| C2 inserted statement | `_unused = 0` after `cached = _connection_type_cache.get(target_type)` | DIFFERENT | **DIFFERENT** | 5088 vs 5091 | token 3701 `(NAME,'if')` != `(NAME,'_unused')` |
| C3 deleted statement | that `cached = ...` line removed | DIFFERENT | **DIFFERENT** | 5088 vs 5080 | token 3693 `(NAME,'cached')` != `(NAME,'if')` |
| C4 docstring rewrite | `_connection_type_for`'s summary line replaced wholesale | IDENTICAL | **IDENTICAL** | 5088 vs 5088 | — |
| C5 comment rewrite | this pass's own repaired comment at line 134 replaced wholesale | IDENTICAL | **IDENTICAL** | 5088 vs 5088 | — |
| **C6 non-statement string** | `_TOTAL_COUNT_ATTR = "_django_total_count"` -> `"_django_total_count_EVIL"` | DIFFERENT | **DIFFERENT** | **5088 vs 5088** | token 280 `(STRING,'"_django_total_count"')` != `(STRING,'"_django_total_count_EVIL"')` |

All seven matched. **C6 is the case that earns the table its shape: the token counts are equal, 5088 vs 5088.** A count-only or length-only instrument passes it silently; only the element-wise sequence comparison catches it. That is why every row reports a verdict rather than only a count, and why "token count unchanged" is not a token-identity claim. C5 is deliberately anchored on this pass's *own* output, so the instrument is shown blind to the exact class of edit the pass makes.

**The anchor discipline held.** Every anchor was asserted to occur **exactly once** in its base text, with all assertions run **before** any mutant file was written, so a missing or ambiguous anchor aborts the run having produced nothing. Every mutant was written under `<scratchpad>/cohortI-027/challenge-027/`, **outside** the repository; no tracked file was ever mutated, so no revert was needed and none is claimed.

**The apply instrument carries the same discipline.** `edits_i027.py` validates all 54 attribution edits before writing any (and `edits2_i027.py`, the same code with a one-row edit list, validated Task 3's): each requires its anchor to occur exactly once on the pinned line, that whole line to occur exactly once in the file, the rewritten line to fit the file's declared cap, and every file's line count to be unchanged. A single failure refuses the whole batch. Each dry run printed its validated edits with their resulting lengths; only then was `--apply` passed. This is what makes "no line added or removed" mechanical rather than reviewed.

### Failability proofs

None; this pass introduced no new boundary.

Discharged mechanically rather than on prose: the executable-token identity table shows the diff contains no statement, branch, guard, comparison, or raise for the mandatory floor to select.

### Hot-path budget

Not applicable; the plan declares no hot path. `connection.py` does carry hot paths, but this pass changes no executable token on it (proved above), so there is no cost to measure.

### Floor verification

Not applicable; the plan declares floor-verification scope none. No slice in this cycle changes an executable statement.

### Implementation notes

- **The repair predicate is block-orphan under a case-INSENSITIVE card match.** Both halves are load-bearing. Repairing all 89 line-bare hits would have inserted a card next to a card already there 33 times; repairing the 69 case-sensitive block-orphans would have inserted `spec-046` into 13 blocks whose summary line already reads `Spec-046`. The 56 case-insensitive orphans are the set where no reader could resolve the reference, in either spelling.
- **Line-length caps are per file, and declared rather than assumed.** `connection.py` is package source, where `E501` is active with a 110 grace over the 99 formatter target; its longest rewritten line is **92**, so the house limit is not approached. The three test files have `E501` **ignored outright** in `pyproject.toml` (`"tests/**/*.py" = [... "E501" ...]`), and each already carried lines past 99 before this pass (2 / 5 / 4 respectively, up to 113), so their cap was set at the 110 `max-line-length` names. Six rewritten test lines land in 100-109: `test_permissions.py` 829 (96 -> 105), 1855 (100 -> 109), 1871 (99 -> 108), 2038 (93 -> 102), 2653 (100 -> 109), 2739 (93 -> 102). Enumerated here rather than left to be noticed in the diff. The one candidate that would have exceeded 110 was refused by the instrument and is the pass's single unresolved site.
- **No reflow anywhere, and no word order changed.** Every one of the 55 edits is a same-line substitution. 52 insert a `spec-NNN` before an existing `Decision N` / `D3`; 2 delete a `Revision 3` tail; 1 replaces a card id with a shorter one. No comment or docstring was re-wrapped, so this pass cannot have created a wrapped citation — and the postcondition census confirms 0.
- **The `DN` spelling was preserved where it names a non-Decision item.** `test_routers.py:3015`'s `Helper-reuse D3` was repaired to `spec-041 Helper-reuse D3` rather than normalized to `Decision 3`, because `D3` there is an item id in `spec-041`'s `## Helper-reuse obligations (DRY)` section, not a Decision — and `spec-041` uses that exact spelling itself twice. Normalizing it would have pointed at a real Decision 3 that says something else.
- **Where two Decision numbers share one line, the card goes in once.** `connection.py:637` (`Decision 4 / Decision 5`), `:1617` and `:2029` (`Decision 7 / Decision 10`, `Decision 6 / Decision 7`), `test_permissions.py:172` (`Decision 5 / 9 / 10`) and `:2513` (`Decision 11 / 12`) each read `spec-NNN Decision A / Decision B` now. Repeating the card would be noise on a line that already resolves.
- **Two second-paragraph sites inside an already-attributed docstring were attributed anyway** (`connection.py:1229` and `:2029`), because the sibling card carries an identically-numbered Decision on a different subject in both cases — cohort C's R3 shape, fired on measured ambiguity rather than on style.

### Notes for Worker 3

- **Instruments are all under `<scratchpad>/cohortI-027/`** and every filename carries `027`: `census_i027.py`, `census_i027_ci.py`, `edits_i027.py`, `tokid_i027.py`, `wrapcheck_i027.py`, `challenge_i027.py`, plus `head-027/`, `prepass-027/`, `challenge-027/`, `census-worktree-027.json`, `census-worktree-ci-027.json`, `census-head-027.json`, `census-after-027.json`, `fence-cs-027.json`, `fence-ci-027.json`, `status-before-027.txt`, `status-after-027.txt`, `files-027.txt`, `orphans-027.txt`, `orphans-ci-027.txt`. **Read before executing**; the scratchpad root is shared and collisions are confirmed. Nothing in this artifact rests on a shared-root script.
- **The part most worth auditing is the case-sensitivity finding, because it moves a fence-wide number.** If `Spec-NNN` is *not* a legitimate spelling of a card id, then 13 sites in `tests/test_routers.py` are genuine orphans this pass left, and the fence-wide figure really is 257 rather than 243. The measurement is `grep -c 'Spec-046' tests/test_routers.py` -> 21 and the sample block at line 1642 (`"""Spec-046 row 28: ...`); please re-derive rather than accept it.
- **The weakest attribution is `tests/test_routers.py:3877`** — see the repair table and the escalation below. Reverting that one edit is a single-line change and the other 54 are independent of it.
- **`HEAD` is not this pass's baseline for three of the four files.** Re-run token identity against **both**; the `prepass-027/` copies are what isolate this pass from cohort F's.
- **`connection.py` is the file where a wrong attribution was easiest to make**, because `spec-030` and `spec-033` both carry Decisions 3-10 and both are cited in the module. Twelve sites went to `spec-030` and five to `spec-033`; each row's disproof column is the thing to check, not the subject match.
- No shadow file was used. `scripts/review_inspect.py` was **skipped** for all four files: this pass adds no logic, and the helper's `<stem>.stripped.py` replaces every comment and string-literal token with `...`, so its output is byte-identical before and after. The token-identity table is the mechanical evidence for the skip — the same recorded skip and reason Slices 2 and 4 and cohorts C and F carried.

### Notes for Worker 1 (spec reconciliation)

Seven items. None is a `spec-027` edit; all concern surfaces fenced from this cohort, other cards' documents, instrument policy, or decisions only the custodian can take.

- **A sixth citation spelling nobody has censused: capitalized `Spec-NNN`. It inflates every block-scoped orphan figure this cycle has produced.**
  - Where it lives: `examples/fakeshop/test_query/test_library_api.py` (23), `tests/test_routers.py` (21), `tests/types/test_base.py` (2), and one each in `tests/types/test_definition_order.py`, `tests/orders/test_composition.py`, `django_strawberry_framework/utils/inputs.py`, `django_strawberry_framework/testing/client.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/consumers.py` — **52** repo-wide in `.py`, plus **174** in `docs/`.
  - Recommended action: no spec edit and no prose sweep. Record in `build-027-filters-0_0_8.md` that **any** census of a `spec-NNN`-adjacency population must match the card id case-insensitively, and correct the fence-wide spaced-`Decision N` block-orphan figure from **257 to 243**. The two files whose figures move are `tests/test_routers.py` (27 -> 14, closed by this pass) and `tests/types/test_base.py` (11 -> 9, outside this partition and dirty at this pass's baseline).
  - Reason: cohort C's, cohort F's and Worker 0's instruments all matched `spec-NNN` case-sensitively. The class is invisible to every one of them, and it produced 13 false orphans in this cohort's own dispatch — including the wrapped site at `test_routers.py:1647` that the brief nominated as a worked example.
- **`tests/test_routers.py:3877` cites `Decision 11` for a contract `spec-046` states under `Decision 16`.**
  - Current wording: `"""spec-046 Decision 11, the lease held through the send: the sibling race.`
  - Recommended replacement: `"""spec-046 Decision 16, the lease held through the send: the sibling race.` — **if** the custodian agrees the sentence means the lease mechanism rather than the revalidating-default consumer that D11 introduces.
  - Reason: a per-decision-block scan of `spec-046` puts **17** of its 18 architectural-decision `lease` occurrences under `### Decision 16` and **0** under `### Decision 11`. This pass added the card (certain) and declined the renumber (a claim about intent), because a confidently wrong number inside a correctly named card is the same defect class this cycle keeps closing.
- **`spec-046 ### Decision 12`'s heading and `### Decision 11`'s body overlap on the revalidation-window ceiling, which is why `test_routers.py:1991` needed a disproof rather than a lookup.**
  - Current situation: the "no upper bound, for the same reason it imposes no maximum connection lifetime" argument is written inside **Decision 11**'s body (spec lines 1638-1641), while the maximum-connection-lifetime contract it points at is **Decision 12**. A reader of D12 does not find the window rule; a reader of D11 does not find the lifetime rule.
  - Recommended action: no wording change required. Record the cross-reference so a future comment author in `tests/test_routers.py` does not read `Decision 12` as a mis-citation.
  - Reason: the site was resolvable only by ruling out `spec-041` on a heading count (11 decisions), not by finding the claim under the cited number.
- **`spec-030` and `spec-033` share Decision numbers 3-10 with different subjects, and `connection.py` cites both.**
  - Current situation: `spec-030` D3/D4/D5/D6/D7/D10 are the connection field's guard / base class / factory / synthesized signature / composition pipeline / dispatch shape; `spec-033` D3/D4/D5/D6/D7 are walker recognition / windowed-prefetch planning / the fast path / fallback shapes / plan-cache hygiene. `connection.py`'s module docstring names `spec-030` as the file's spec and carries 8 `spec-033` references in its body.
  - Recommended action: no spec edit. Record the collision so future comment authors in `connection.py` always spell the card, the way `spec-038`/`spec-039`'s collision was recorded by cohort C.
  - Reason: 17 sites in one file were ambiguous by construction, and two of them (`:1229`, `:2029`) sit in docstrings whose *other* paragraph names the other card.
- **`spec-033`'s `Revision 3` finding (4) is a normative contract stated only inside a revision-log line, which is where a reader is least likely to find it.**
  - Current wording, line 15: "(4) **doc-reference hygiene** — a production or test comment on this card's surface cites a spec, a card, or a symbol path, never a per-cycle review artifact, a review-round or finding id (`Revision N`, `P<n>`), or a build-plan step ([`AGENTS.md`][agents])."
  - Recommended replacement: leave the revision-log sentence and add one line under `## Helper-reuse obligations (DRY)` or `## Edge cases and constraints` restating the contract as a standing rule, so it is discoverable without reading the revision log — e.g. "**Comment-reference hygiene (standing).** Comments on this card's surface cite a spec, a card, or a `path::Symbol`; never a review-round id, a `Revision N` / `P<n>` tag, or a build-plan step."
  - Reason: the two sites this pass repaired were on the contract's **own card's** test surface and had survived since Revision 3. A contract nobody finds is a contract nobody keeps. Cohort G established that the same spec's Revision-3 hygiene claim was already asserting completed work that was measurably incomplete; this is the structural reason.
- **`spec-033` line 106 quotes `connection.py`'s docstring, and the quotation is stale in two words, not one.**
  - Current wording, `spec-033` `## Current state`, the `- **Nested connections are unplanned and per-parent.**` bullet: "its docstring documents both the seam (\"the cooperation seam `WIP-ALPHA-033-0.0.9`'s window-pagination planning **will use**\")".
  - Recommended replacement: "its docstring documents both the seam (\"the cooperation seam `DONE-033-0.0.9`'s window-pagination planning **uses**\")".
  - Reason: **the `.py` side has already landed** (`### Task 3`), so the spec side must follow. The card id is stale (`KANBAN.md` carries `DONE-033-0.0.9` 15 times and no `WIP-`/`TODO-` spelling for 033 at all), and the tense was **already** stale before this pass — the comment says "uses", the quotation says "will use". `spec-033` is not in this cohort's writable set and was not touched. The sibling `.py` site at `django_strawberry_framework/types/finalizer.py:660` carries the identical stale id and is fenced from this cohort.
- **`grep -rn "close-before-raise" docs/SPECS/` returns 0, while `connection.py` cites "the close-before-raise discipline" by name.**
  - Where it lives: `django_strawberry_framework/connection.py`, the `_attach_count_async` comment, now reading "Await-before-raise (mirrors the close-before-raise discipline in `utils/querysets.py::apply_type_visibility_sync`, spec-030 Decision 10)".
  - Recommended action: no code change — the `path::Symbol` half resolves and the card is now named. If the custodian wants the phrase to resolve in prose, `spec-030 ### Decision 10`'s parenthetical "(the unawaited coroutine is closed before the raise)" is where a named form would go.
  - Reason: the contract is real and stated; only the coined phrase is unresolvable. Flagged because the site was attributed on content rather than on the phrase, and a future reader grepping the phrase finds nothing.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: ../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[build]: BUILD.md
[plan]: build-027-filters-0_0_8.md
[slice11]: bld-slice-11-027-orphaned_round_ids_and_hyphenated_decisions.md
[slice8]: bld-slice-8-027-decision_attribution.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
