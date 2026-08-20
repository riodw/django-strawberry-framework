# Build: Catalog-discharge cohort F — orphaned review-round ids + the hyphenated `Decision-N` spelling (027)

Spec reference: `docs/SPECS/spec-027-filters-0_0_8.md` (`### Decision 3`, `### Decision 4`, `### Decision 8`, `### Decision 9`, `### Decision 11` — the five contracts this cohort cites on `filters/` surfaces). The pass also resolves against `spec-015`, `spec-028`, `spec-030`, `spec-032`, `spec-033`, `spec-034`, `spec-037`, `spec-038`, `spec-039`, `spec-040`, and `spec-043`; every one is cited by card plus Decision number (or by a spec-internal item id that was measured present in that card), never by line.
Status: final-accepted

## Plan (Worker 1)

### Planning lives in `build-027-filters-0_0_8.md`

This cohort has no Worker 1 planning pass of its own. Its contract is Worker 0's dispatch brief plus:

- [`build-027-filters-0_0_8.md`][plan] `### Two unmeasured in-fence classes surfaced by cohort C` — the dispatch.
- [`bld-slice-8-027-decision_attribution.md`][slice8] — the block-scoped census method and the evidentiary bar for attribution, adopted here. Its scripts were **not** reused; every instrument in this pass was written fresh into a cohort-private scratch subdirectory.

**Writable set (declared by the dispatch):** any `.py` under `django_strawberry_framework/`, `tests/`, `examples/` **except** `orders/base.py`, `orders/inputs.py`, `types/base.py`, `tests/orders/test_inputs.py`, `tests/test_registry.py`, `examples/fakeshop/apps/library/orders.py`, `examples/fakeshop/test_query/test_library_api.py`, `tests/test_relay_connection.py`, `examples/fakeshop/apps/kanban/schema.py` — plus the rule that anything **dirty and not this pass's own edit** is skipped. Both fences were honoured; see `### Files skipped because they were dirty or fenced`.

### DRY analysis

Not applicable as a helper-planning gate, on the ground Slices 1-4 and cohort C recorded: [`BUILD.md`][build] gates *helper planning*, and this pass proposes no helper, shared constant, validation branch, or test helper. The diff contains **no executable statement** (proved mechanically under `### Executable-token identity proof`).

Two DRY observations the pass acted on, both de-duplications of *vocabulary*:

- **The hyphenated `Decision-N` and the spaced `Decision N` are one concept with two spellings.** Every repaired site was normalized to the spaced form, so the tree now carries one canonical spelling at every site that names a card. 78 hyphenated occurrences before, 39 after; the 39 removed became spaced occurrences (`Decision N` rose 1189 -> 1230, of which +39 is this pass and the rest is arithmetic on the same rows).
- **The mirrored-pair spelling was reused, not invented.** `sets_mixins.py`'s `ActiveInputPermissionMixin` is shared by `FilterSet` and `OrderSet`, so it takes `spec-027 / spec-028 Decision 8` — the same shape cohort C used for the shared `utils/inputs.py` substrate, whose own precedent is `utils/inputs.py` line 1297. Picking one card would have been wrong for half the callers.

### Dispatched findings checklist

Built from Worker 0's `### Two unmeasured in-fence classes surfaced by cohort C`.

- [x] Class 1 — review-round ids in code that the rationale extraction orphaned: population re-derived, block-scoped, repo-wide over `.py`
- [x] Class 2 — the hyphenated `Decision-N` spelling no census in this cycle has covered: population re-derived, block-scoped, repo-wide over `.py`
- [x] Spelling set derived from the corpus rather than assumed, and stated
- [x] For every class-1 hit, resolution checked in the named spec **and** its rationale companion; ids resolving in neither reported separately
- [x] Every repair carries measured evidence of its owner; every unestablishable site left alone and recorded

---

## Build report (Worker 2)

### The spelling set, derived from the corpus

Derived by scanning every comment run and docstring in `django_strawberry_framework/`, `tests/`, `examples/` for short-form-id shapes (`(H|M|L|G|AR|SR|R|F|D|P|C|Q)-?\d+`) and for every `Decision`-adjacent form, then reading each family's occurrences. Neither number in the dispatch survived unchanged.

**Class 2 — the `Decision` concept has five spellings in `.py`, not one:**

| Spelling | occurrences (before) | block-orphans (before) |
|---|---|---|
| `Decision N` (spaced, canonical) | 1189 | 260 |
| `Decision-N` (hyphenated — **this cohort's dispatch**) | 78 | 50 |
| `DN` short form (`D6`, `D16`, `D3`) | 36 | 3 |
| `Decision\n<N>` (wrapped across a line break) | 7 | 1 |
| `Spec Decision N` | 1 | 0 |

**Class 1 — review-round ids have six spellings, and two of them are the bulk:**

| Spelling | occurrences (before) | block-orphans (before) |
|---|---|---|
| `Finding N` | 19 | 10 |
| `Revision N` | 18 | 7 |
| `M<n>` (`M1`, `M2`, `M3`, `M3-1`) | 16 | 6 |
| `H<n>` (`H1`, `H3`, `H4`, `H5`) | 9 | 5 |
| `L<n>` (`L3-1`, and a URL `#L45` / `#L52` that is instrument noise) | 3 | 0 |
| `SR-<n>` | 2 | 0 |
| `round-N`, `revN`, `AR-H<n>` | **0** | 0 |

Two dispatch-relevant facts fall straight out of the spelling table:

- **`round-N` and `finding N` (lowercase) do not exist in `.py` at all.** The dispatch named them as members; the corpus spells the same concept `Finding N` (capitalized, 19 occurrences) and `Revision N` (18). A sweep keyed on the dispatch's vocabulary would have returned 0 and reported the class closed.
- **`H1` is not the dominant member.** The dispatch's worked example (`spec-027`'s `H1`) has **9** `H<n>` siblings repo-wide; `Finding N` and `Revision N` together are **37** occurrences, twice the H/M/L families combined.

Also derived, and load-bearing for class 1: **rationale companions exist for `spec-001`-`spec-028` and `spec-044`-`spec-048` only** (`ls docs/SPECS/appx/*-rationale.md`). Specs `029`-`043` and `049`+ have **no** companion, so a review-round id that fails to resolve in one of those specs was never *moved* — it never existed there. That splits class 1 into two populations with different repairs, and the dispatch's third method requirement is what surfaced it.

### Class-2 census: hyphenated `Decision-N`, block-scoped

Instrument: `<scratchpad>/cohortF-027/census_f027.py`. A BLOCK is one whole docstring (statement-position `STRING`) or one whole contiguous run of `COMMENT` tokens; a reference is an ORPHAN only when no `spec-NNN` appears anywhere in that block. The line-scoped column exists only to quantify the instrument shape the dispatch's figures came from.

**The dispatch's figure was right for the package and wrong for the fence.** `grep -rnE 'Decision-[0-9]' django_strawberry_framework/ --include='*.py'` returns **39**, reproducing the brief exactly. But the dispatch's writable set is `django_strawberry_framework/` **plus `tests/` plus `examples/`**, and over that fence the same census returns **78** — exactly double. The unmeasured population was twice the size the brief named, and the missing half is entirely in the test and example trees.

| File | occ | **B-orphan** | L-bare | L false positives |
|---|---|---|---|---|
| `django_strawberry_framework/filters/sets.py` | 7 | **3** | 7 | 4 |
| `django_strawberry_framework/optimizer/nested_fetch.py` | 4 | **3** | 4 | 1 |
| `django_strawberry_framework/optimizer/nested_planner.py` | 4 | **2** | 4 | 2 |
| `django_strawberry_framework/filters/__init__.py` | 3 | **3** | 3 | 0 |
| `django_strawberry_framework/mutations/sets.py` | 3 | **2** | 3 | 1 |
| `django_strawberry_framework/sets_mixins.py` | 2 | **2** | 2 | 0 |
| `django_strawberry_framework/utils/connections.py` | 2 | **0** | 1 | 1 |
| `auth/mutations.py`, `connection.py`, `filters/inputs.py`, `optimizer/lateral_fetch.py`, `optimizer/walker.py`, `testing/client.py`, `types/base.py` | 1 each | **1** each | 1 each | 0 |
| `orders/inputs.py`, `orders/sets.py`, `rest_framework/sets.py`, `types/definition.py`, `types/relay.py`, `utils/inputs.py`, `mutations/__init__.py` | 1 each | **0** each | 0-1 | 0-1 |
| `tests/optimizer/test_walker.py` | 7 | **6** | 7 | 1 |
| `tests/filters/test_inputs.py` | 4 | **3** | 4 | 1 |
| `tests/filters/test_sets.py` | 3 | **3** | 3 | 0 |
| `tests/test_relay_connection.py` | 3 | **3** | 3 | 0 |
| `tests/mutations/test_sets.py` | 2 | **2** | 2 | 0 |
| `tests/types/test_base.py` | 2 | **1** | 1 | 0 |
| `tests/types/test_definition_relations.py` | 2 | **2** | 2 | 0 |
| `tests/auth/test_queries.py`, `tests/mutations/test_resolvers.py`, `tests/test_scalars.py`, `tests/test_sets_mixins.py` | 1 each | **1** each | 1 each | 0 |
| `tests/optimizer/test_extension.py`, `tests/types/test_relay_interfaces.py` | 1 each | **0** each | 0-1 | 0-1 |
| `examples/fakeshop/test_query/test_library_api.py` | 3 | **3** | 3 | 0 |
| `examples/fakeshop/apps/library/filters_genre.py` | 1 | **1** | 1 | 0 |
| `examples/fakeshop/apps/products/serializers.py` | 2 | **0** | 1 | 1 |
| `examples/fakeshop/test_query/test_products_api.py` | 2 | **0** | 0 | 0 |
| `examples/fakeshop/apps/library/serializers.py`, `examples/fakeshop/apps/products/forms.py` | 1 each | **0** each | 0-1 | 0-1 |
| **TOTAL** | **78** | **50** | **70** | **20** |

**Line-scoped false-positive rate on this population: 20 of 70 = 29%.** Lower than the 61% cohort C measured on the spaced spelling, and the reason is structural: the hyphenated form clusters in module docstrings and short comment runs where the card, when present, is on the *same* line rather than an adjacent one. **The line instrument missed 0 orphans here** (no hyphenated reference is itself wrapped across a break), which is the one respect in which the shape was not misleading — and it is why the two instruments must both be run rather than one being assumed worse.

After this pass: **39 occurrences, 11 block-orphans**, every remaining one either fenced or measurably unestablishable (`### Sites left UNRESOLVED` and `### Files skipped`).

### Class-1 census: review-round ids, block-scoped, and where each id actually lives

67 occurrences, **28 block-orphans**, 40 line-bare. Block scoping earned its keep twice over on this class, in both directions:

- It **excluded** two whole false populations a text grep returns: `tests/rest_framework/test_inputs.py`'s `class H1(serializers.Serializer)` / `class H2(...)` (executable code, not prose) and `examples/.../test_library_api.py`'s `note="L1"` / `"L2"` / `"L3"` fixture strings. A line-scoped `grep -n '\bH1\b'` reports all six as hits.
- It **included** `_strawberry_patches.py:218`'s `#L45` — a GitHub permalink line anchor inside a module docstring. That one is genuine instrument noise, recorded here rather than silently dropped, and it is not a member of the class.

**Resolution, per the dispatch's third method requirement.** For every id: check the named (or candidate) spec, then that spec's `-rationale.md` companion.

| Id | Sites | In the spec | In its rationale companion | Verdict |
|---|---|---|---|---|
| `M1` (transport) | `tests/test_views.py:2144` | `spec-046`: **0** | `spec-046-...-rationale.md`: **4** | **Class-1 proper — orphaned by the rationale move.** Re-measured after `spec-046` went dirty mid-pass: still 0 / 4 |
| `M1` (connection) | `connection.py:1139`, `:1356`, `tests/test_relay_connection.py:1965` | `spec-030`: **2** ("Escalated from Slice 1 review M1") | no companion exists | Resolves; the defect is only the missing card |
| `Revision 7 P1` / `P2` | `tests/test_relay_node_field.py:678`, `:1218` | `spec-032`: **3** / **7** | no companion exists | Resolves; missing card |
| `Revision 3` | `tests/test_permissions.py:1906` | `spec-034`: **1** | no companion exists | Resolves; missing card |
| `M3` | `forms/inputs.py:355`, `mutations/inputs.py:325`, 4 sites in `rest_framework/` | `spec-039`: **5** | no companion exists | Resolves; missing card |
| `H3` | `rest_framework/inputs.py:1250` (+ 2 in-block) | `spec-039`: **7**, subjects mismatch | no companion exists | Unresolvable — cohort C's finding, re-confirmed |
| `H5` | `serializer_converter.py:476`, `:482`, `:984` | `spec-039`: **0** bare (**1** as `AR-H5`, itself a pointer to `spec-036`) | no companion exists | Unresolvable — cohort C's finding, re-confirmed |
| `H4` | `rest_framework/resolvers.py:38` | `spec-039`: **0** | no companion exists | **Resolves in NEITHER** |
| `SR-3` | `serializer_converter.py:442`, `tests/rest_framework/test_converter.py:184` | `spec-039`: **0** | no companion exists | **Resolves in NEITHER** |
| `H1` | `types/base.py:526` | candidates: `017`(2) `021`(1) `028`(2) `034`(5) `039`(1) | `027`(27) `028`(14) `020`(29) `019`(11) `021`(11) and more | Fenced file; **owner not established** |
| `Finding 1`-`Finding 5` | **19 occurrences** in `tests/forms/test_sets.py`, `tests/forms/test_resolvers.py`, `tests/mutations/test_resolvers.py`, `tests/rest_framework/test_sets.py` | `spec-038`: **0** (`grep -ci finding` -> **0**); `spec-036`: **0**; `spec-039`: **0** | none of the three has a companion | **Resolves in NEITHER — the largest single class-1 population** |
| `L3-1`, `M3-1` | `mutations/inputs.py:470`, `:486`, `mutations/resolvers.py:621`, `mutations/sets.py:1179` | `spec-036`: `L3` **0**; `M3` **7**, all of them `AR-M3` on a different subject | no companion exists | **Resolves in NEITHER**, with a live wrong candidate |

**The one measured instance of the dispatch's own hypothesis.** Exactly **one** class-1 site in the writable set is orphaned in the way the dispatch describes — an id that resolved inside its spec until a rationale extraction moved it out: `tests/test_views.py:2144`'s `M1`, whose `spec-046` count is 0 in the spec and 4 in `docs/SPECS/appx/spec-046-transport_security-0_0_14-rationale.md` (`- **Change record — the round-2 adversarial review (M1).**`). Cohort C's `orders/factories.py:9` was the other. So the class the dispatch opened is **real and rare — 2 sites repo-wide** — while the class it did not name, *review-round ids that resolve in no document at all*, is **26 occurrences** (19 `Finding N` + 4 `L3-1`/`M3-1` + `H4` + `SR-3` x2). That inversion is this cohort's headline measurement.

### Sites repaired, with the evidence that established each owner

47 edits across 26 files. Owners were established by reading the cited Decision and confirming it states what the comment claims; where a sibling card carried an identically-numbered Decision, the alternative was **disproved by measurement** rather than the winner being asserted.

#### `spec-033 Decision 6` — 12 sites (the optimizer fallback-shape family)

`optimizer/lateral_fetch.py:47`, `optimizer/nested_fetch.py:94`, `:101`, `:256`, `optimizer/nested_planner.py:1372`, `:1452`, `optimizer/walker.py:578`, `tests/optimizer/test_walker.py:3583`, `:4948`, `:5061`, `:5405`, `:5467`.

`docs/SPECS/spec-033-connection_optimizer-0_0_9.md` `### Decision 6 — Fallback shapes: sidecar input, divergent aliases, hints, and scalar-only connections` is the owner, by heading and by body: the code's claims are its members (sidecar, `OptimizerHint.SKIP`, DISTINCT, malformed slice, unwindowable partition), and "leaves the selection UNPLANNED ... stays visible to strictness" is the Decision's own discipline.

- **Disproof of the two live alternatives.** `grep -c '^### Decision ' docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` -> **9**, and its `### Decision 6` is `G3 — registry-only fragment type-condition narrowing`: a real document with a real Decision 6 about something else. `spec-003` and `spec-004` — the other optimizer cards — have **0** `### Decision ` headings at all (spec-004 numbers its items `B1`-`B8`), so neither can own a Decision 6.
- **In-file corroboration, unedited by this pass.** `nested_fetch.py`'s module docstring already pairs `spec-033` with `Decision-6 fallback shapes` (line 7, block-resolved); `nested_planner.py:846` / `:1114`, `utils/connections.py:76`, `tests/optimizer/test_extension.py:4957` and `tests/optimizer/test_walker.py:3419` do the same. `tests/optimizer/test_walker.py` names `spec-033` **17** times.

#### `spec-033 Decision 4` — 1 site

`tests/optimizer/test_walker.py:4329`, `the Decision-4 ``to_attr``-isolation edge case`.

`spec-033` `### Decision 4 — Windowed-prefetch planning under a package-reserved ``to_attr``` carries a bullet spelled **`- **``to_attr`` isolation**:** verbatim, and its body is the exact-match/absorption reasoning the test asserts ("two `Prefetch`es on one accessor with different querysets"). Disproof: `spec-035` Decision 4 is `G2 — operation-type gating of ``.only()```; `spec-036` Decision 4 is `Module and test locations`.

#### `spec-027 Decision 4` — 6 sites (the owner-aware conditional)

`filters/sets.py:1504`, `tests/filters/test_sets.py:5`, `:431`, `tests/types/test_definition_relations.py:6`, `:499`, `examples/fakeshop/apps/library/filters_genre.py:21`.

`spec-027` `### Decision 4 — Upstream-primitives parity floor` **is** the owner-aware conditional, despite the heading naming the parity floor — its body carries `**Owner awareness.**`, `**Where the conditional runs.**`, `FilterSet.filter_for_field(cls, field, field_name, lookup_expr)`, `filter_for_lookup`, and **4** occurrences of `related_target_for`. Reading the heading alone would have rejected this attribution; reading the body establishes it.

- **Disproof of the mirror.** `spec-028` `### Decision 4` is also titled `Upstream-primitives parity floor`, so the number and the title both match — and `grep -c 'filter_for_field'` over its body (lines 399-433) returns **0**. The orders mirror cannot own a `filter_for_field` conditional.
- **In-file corroboration.** `filters/sets.py`'s module docstring already carries `Decision-4 owner-aware Relay-vs-scalar conditional` inside a block naming `spec-027` twice; `tests/types/test_definition_relations.py` names **no** spec anywhere, which is why both of its sites were orphans.

#### `spec-027 Decision 8` — 4 sites (the apply pipeline)

`filters/sets.py:2074`, `:2906`, `tests/filters/test_sets.py:6`, and the shared-facade pair below.

`spec-027` `### Decision 8 — Relation-permission cascade + ``get_queryset`` cooperation` owns `**Recommended internal decomposition.**` (the five named helpers `apply_sync` / `apply_async` decompose into), the sentence `"the apply pipeline" refers to the shared algorithm run by both`, and a numbered 9-step list whose **step 8** is `The instance's ``.qs`` property runs ``cls.filter_queryset(self, queryset)```. `filters/sets.py:2906`'s claim is `Decision-8 step 8`, on `filter_queryset` — the step matches by number *and* by body.

#### `spec-027 / spec-028 Decision 8` — 3 sites (the shared permission facade)

`sets_mixins.py:16`, `:422`, `tests/test_sets_mixins.py:3`.

`ActiveInputPermissionMixin` is, by its own docstring, `shared by ``FilterSet`` and ``OrderSet```, and both cards' Decision 8 own their half of it: `spec-027` Decision 8's helper list contains `_run_permission_checks(input_value, request)`; `spec-028` Decision 8's step 6 is `**The apply pipeline calls the classmethod ``cls._run_permission_checks(input_value, request)``**` with an explicit `mirroring the filter side's ``_run_permission_checks``` cross-reference. Naming one card would have been wrong for half the callers, so the mirrored-pair spelling was used — the same shape, and for the same reason, as cohort C's `utils/inputs.py` repairs, whose precedent is `utils/inputs.py` line 1297.

`orders/sets.py:113` already attributes the *order-side* use as `spec-028` in-block; that site is block-resolved and was not touched.

#### `spec-027 Decision 11` — 3 sites, and `spec-027 Decision 9` — 2 sites

`filters/__init__.py:4`, `:39`, `:80`; `filters/inputs.py:148`, `tests/filters/test_inputs.py:1336` / `:1377`.

The strongest structural evidence in the pass: **`orders/` is a line-by-line mirror of `filters/`, and the concurrent `spec-028` session had already repaired the orders half.** `orders/__init__.py:5` / `:32` / `:77` read `spec-028 Decision 11 consumer helper` / `Ledger of ``OrderSet``s referenced through the spec-028 Decision 11` / `spec-028 Decision 11 consumer-helper body shared with ``filters/__init__.py::filter_input_type```; the filters sites this pass repaired are the same three sentences with `Filter` for `Order`. Likewise `orders/inputs.py:134-144` is the same comment as `filters/inputs.py:139-155` and names `spec-028 Decision 9`. Headings confirm: `spec-027 ### Decision 11 — ``filter_input_type(FilterSet)`` consumer helper` and `### Decision 9 — Input-class namespace vs ``TypeRegistry`` and lifecycle`, against `spec-028`'s identically-shaped `order_input_type` / Decision 9 pair.

#### `spec-027 Decision 3` — 1 site

`tests/filters/test_inputs.py:83`, `Pin the Decision-3 Layer-5 table verbatim`, on `test_lookup_name_map_full_table_matches_spec`.

`spec-027` `### Decision 3 — Six-layer lazy-resolution pipeline` carries `**Layer 5 — BFS schema build with module-global materialization**` and, inside the same Decision, `Per-lookup field names are pinned through a ``LOOKUP_NAME_MAP`` constant in ``inputs.py``` plus `Both the factory ... and the runtime input-data normalizer ... consult ``LOOKUP_NAME_MAP```. The test pins that table.

**Recorded because it is a near-miss on a known trap:** the integration cohort's *partition correction 2* found `filters/inputs.py`'s `spec-027 Decision 3 Layer 5` citation to be **wrong** — but that site was about `LOOKUP_PREFIXES` / `construct_search`, which Decision 3 does not contain (Decision 2 does). `LOOKUP_NAME_MAP` **is** in Decision 3. Same file, same spelling, opposite verdict; the two were separated by measuring the cited symbol rather than the cited number.

#### `spec-030` — 3 sites (the connection field)

| Site | Was | Now | Evidence |
|---|---|---|---|
| `connection.py:1172` | `Adds the Decision-3 ``first`` + ``last`` guard` | `spec-030 Decision 3` | `spec-030 ### Decision 3 — Build on Strawberry's native Relay machinery, but own the ``first`` + ``last`` guard` — heading match, verbatim |
| `connection.py:1139` | `a spurious M1-guard raise` | `a spurious spec-030 Decision 7 guard raise` | `spec-030` line 556 states the non-queryset-`totalCount` `GraphQLError` and closes `Pinned by a Slice 2 test (escalated from Slice 1 review M1)`, binding it to `[Decision 7](#decision-7--composition-pipeline-...)` |
| `connection.py:1356` | `the connection field's M1 rule raises` | `... spec-030 Decision 7 rule raises` | same, plus `spec-030` line 583: `the ``totalCount``-over-non-queryset half of the Decision 7 consumer-resolver contract` |

Repairing `M1` to the **Decision** rather than to `spec-030 M1` follows the dispatch's fifth method requirement: the review round is how the contract came to be, the Decision is the contract. The 1172 repair also de-orphans the block's second, spaced `(Decision 4)` reference at line 1178 as a side effect.

#### `spec-040` — 2 sites (auth mutations)

| Site | Claim | Owner | Evidence |
|---|---|---|---|
| `auth/mutations.py:1144` | `the Decision-8 register-arm validation` still covers a re-recorded rider | `spec-040 Decision 8` | `### Decision 8 — The user model's primary ``DjangoType`` is required, validated at bind`; `register_mutation()` is named in its first sentence and `register-arm` appears **6** times in the spec, including `the second finalize still fires the register-arm` |
| `tests/auth/test_queries.py:264` | `The Decision-10 async-gate fix` forces the lazy user inside the one boundary | `spec-040 Decision 10` | `### Decision 10 — Sync + async: session work through one ``sync_to_async(thread_sensitive=True)`` boundary`, whose body reads `**The permission gate runs inside the same boundary on the async path** ... (the P2 async-gate fix)` — the code's exact phrase. **Disproof:** the file's only spec references are two `spec-041`s, and `spec-041 ### Decision 10` is `Version bumps are owned by the joint 0.0.14 cut` |

#### `spec-043 Decision 5`, `spec-037 Decision 5`, `spec-015 Decision 4`, `spec-038 Decision 13` — 4 sites

| Site | Was | Now | Evidence, including the disproof |
|---|---|---|---|
| `testing/client.py:197` | `-> Decision-5 guard (an EXPLICIT raise, not a bare ``assert``, so it survives ``python -O``)` | `spec-043 Decision 5` | `spec-043` line 1218 states `the ``assert_no_errors`` gate is package code: it is implemented as an explicit` ... `survives ``python -O`` (which strips ``assert``s)`. Line 1218 falls between `### Decision 5` (1148) and `### Decision 6` (1250), so the sentence is *inside* Decision 5 |
| `tests/test_scalars.py:612` | `the load-bearing Decision-5 pin: ``Upload`` rides Strawberry's ``DEFAULT_SCALAR_REGISTRY``` | `spec-037 Decision 5` | `spec-037 ### Decision 5 — Re-export ``Upload`` rather than register it`. **Disproof of every other scalar card:** `spec-017` D5 is `HStoreField wire shape`, `spec-025` D5 is `Migration posture: hard break in alpha`, `spec-026` D5 is `Superseded package tests are deleted in the same cut` |
| `tests/types/test_base.py:716` | `The ``_validate_interfaces`` Decision-4 validator is the full shipped contract` | `spec-015 Decision 4` | `spec-015 ### Decision 4: validation` — `gains an interface validator that runs when ``interfaces`` is declared`, and `spec-015` line 115 names `types/base.py::_validate_interfaces` as the validator. **Disproof:** `spec-032` D4 is `DjangoNodeField / DjangoNodesField`, and `spec-005` — the only other spec mentioning `_validate_interfaces` — has **0** `### Decision ` headings |
| `tests/mutations/test_sets.py:1528` | `` `make_meta_validating_metaclass` is the Decision-13 twin of `make_declaration_registry` `` | `spec-038 Decision 13` | `spec-038` line 1813, inside `### Decision 13 — Finalization seam: reuse the mutation phase-2.5 bind` (1767, next Decision later), introduces `into a small ``make_declaration_registry(label)`` helper`. **Disproof of all three siblings:** `spec-036` D13 is `Version bumps are owned by the joint 0.0.11 cut`; `spec-039` D13 is `Live coverage: products grows a ``ModelSerializer`` mutation`; `spec-040` has **12** Decisions and `spec-051` has **12**, so neither has a Decision 13 |

The `spec-038 Decision 13` attribution is the **weakest of the pass and is flagged as such**: the cited Decision owns `make_declaration_registry`, the *sibling* of the symbol under test, not `make_meta_validating_metaclass` itself — which appears in **no** spec (`grep -rl make_meta_validating_metaclass docs/SPECS/` -> nothing). The reference is a "twin-of" pointer, so the target is correct for what the sentence says and would be wrong if read as "the Decision that specifies this function". Corroborated only circumstantially, by `tests/mutations/test_sets.py:1372` already citing `(spec-038 / DoD item 6)` for the same generalization.

#### `spec-039 M3` — 2 sites (a cross-flavor id kept, card added)

`forms/inputs.py:355` (`unlike serializer M3, which raises`) and `mutations/inputs.py:325` (`M3 raises before calling this`).

`spec-039` carries **5** `M3` occurrences and its subject is exactly the code's claim: `- **Relation target with no registered primary ``DjangoType`` (M3).** A serializer relation ...`, plus `` `ConfigurationError` (M3) ``. The id was **kept** and only the card prefixed, following cohort C's precedent for `M3` / `P1.7` / `P2.7`: it resolves in the named card, so a reader can grep it. Consistent with the three `spec-039 M3` sites cohort C left in `serializer_converter.py`.

#### `spec-032 Revision 7 P1` / `P2` — 2 sites (card added, id kept)

`tests/test_relay_node_field.py:678`, `:1218`.

The strongest single attribution in the pass, because **the spec's own test-plan entry for this very test cites the same id**: `spec-032` line 563 reads `` `test_node_sync_async_get_queryset_raises_sync_misuse` — the SyncMisuseError pass-through, **discriminatingly** asserting ... (Revision 7 P2 — the catch-convert boundary scopes the decode call only) ``, which is the docstring's sentence. `P2` is defined at spec-032 line 16 under Revision 7: `**P2 — ``SyncMisuseError`` IS-A ``ConfigurationError``, so a wide catch-convert would mislabel it.** For `P1`, line 356: `**Declare the id argument as ``relay.GlobalID``** ... Rejected (Revision 7 P1): Strawberry's ``convert_argument`` runs ``GlobalID.from_id(value)`` during argument conversion` — the comment's exact reason. The file's module docstring already names `spec-032`, so the card was known; only the two mid-file sites were card-less.

#### `spec-034 Decision 9` — 1 site, review-round id DROPPED

`tests/test_permissions.py:1906`: `(Decision 9, Revision 3)` -> `(spec-034 Decision 9)`.

Both ids resolve in `spec-034`, and both name the same thing: `### Decision 9 — ``fields=`` scoping validates loudly with ``ConfigurationError``` states `A bare string is rejected first, before any name lookup: ``isinstance(fields, str)`` raises`, and Revision 3's entry reads `the one net-new item — a bare-string guard on ``fields=`` (``isinstance(fields, str)`` rejected up front)`. The Decision is the contract; the Revision is how it arrived. Dropping `, Revision 3` also kept the line at **93** characters — inserting the card *and* keeping the id would have made it **105**, past the 99 limit, and the only alternative would have been a reflow. Rule and length agreed.

#### A dead review-round id deleted — 1 site

`tests/test_views.py:2144`: `(plus the alias matrix below, and the M1 row for the masking direction)` -> `(plus the alias matrix below, and the masking-direction row)`.

Deleted rather than re-pointed, on three independently measured grounds:

1. **It resolves in no spec.** `spec-046`: **0** occurrences of `M1`; `docs/SPECS/appx/spec-046-transport_security-0_0_14-rationale.md`: **4**, all of them build provenance (`bld-review-2-w3_review.md M1 caught it`). Re-measured after `spec-046` went dirty mid-pass: unchanged.
2. **The row it points at is already named two lines below.** Line 2146 spells `..._does_not_mask_a_middleware_set_request_encoding` — the test at line 2285. The id added nothing a reader could not already follow.
3. **The invariant survives the deletion intact.** `spec-046 ### Decision 17` requirement 1 states `the declaration must never be allowed to mask that`, so "the masking-direction row" *is* the contract's own vocabulary. Citing `spec-046 Decision 17` there was the alternative and was rejected as noise: the sentence is an index of sibling test rows, not a contract statement.

### Sites left UNRESOLVED, and why

Reporting these accurately is the outcome the dispatch asked for. Each was investigated and **not** touched.

| Site | Reference | Measurement | Why left |
|---|---|---|---|
| `tests/mutations/test_resolvers.py:641` | `the id type-check / Decision-10 visibility contract` | `spec-036 ### Decision 10 — Permission composition: ``update`` / ``delete`` lookups run through the target ``get_queryset``` — and every one of the spec's **8** internal `Decision 10` cross-references scopes it to the update/delete **row** lookup (line 62: `` `update` / `delete` lookups run through `target_type.get_queryset(...)` for **visibility only** ``). The code's claim is a **create**-path *relation id* (`categoryId` naming a hidden `Category`) | A live wrong candidate with an adjacent subject. `spec-036` D10 is about which rows a caller may target; the code is about which relation ids a caller may attach. Attributing would send the reader to a real Decision that says something else — the failure mode the dispatch's fourth requirement names |
| `tests/mutations/test_sets.py:849` | `the id type-check and the Decision-10 visibility contract` | same measurement | same |
| `rest_framework/inputs.py:1250` | `H3` | `spec-039`: **7** `H3`, subject is the actor / permission seam / `partial` + authorized-actor `context["request"]`; the code claims `GraphQL cannot express DRF ``required=True``` | Cohort C investigated and left it; re-measured, verdict unchanged. Also a cohort-C-owned file, dirty at this pass's baseline |
| `serializer_converter.py:476`, `:482`, `:984` | `H5` | `spec-039`: **0** bare `H5`; its single `H5` is `(``spec-036`` AR-H5)`, a pointer outward. `spec-036`: 7, `spec-038`: 2, subjects do not match the `PrimaryKeyRelatedField`-only claim | Cohort C's finding, re-confirmed. Cohort-C-owned file, dirty at baseline |
| `rest_framework/resolvers.py:38` | `spec-039 H4` | `spec-039`: **0**; no `spec-039` rationale companion exists, so it was never moved out either | Card named, label resolves nowhere; which item it meant is not derivable. Cohort C's finding |
| `serializer_converter.py:442`, `tests/rest_framework/test_converter.py:184` | `spec-039 SR-3` | `grep -rl -- "SR-3" docs/SPECS/` -> nothing | Names nothing in any spec. `test_converter.py` is **not** dirty and **not** fenced, so this pass could have edited it — and deliberately did not: the repair would be inventing a substitute, which the dispatch forbids |
| **19 occurrences** of `Finding 1`-`Finding 5` in `tests/forms/test_sets.py` (4), `tests/forms/test_resolvers.py` (9), `tests/mutations/test_resolvers.py` (3), `tests/rest_framework/test_sets.py` (1), plus 2 in-block siblings | `Finding N`, 9 of them spelled `` (``spec-038-form_mutations-0_0_12`` Finding N) `` | `grep -ci finding docs/SPECS/spec-038-form_mutations-0_0_12.md` -> **0**. Same for `spec-036` and `spec-039`. None of the three has a rationale companion. `grep -rloE '\bFinding [0-9]+' --include='*.md'` over the repo returns only `BACKLOG.md`, one `docs/dry/` file, and four `docs/builder/` artifacts — **no spec** | The numbering exists in no document, so no item can be established. The nine carded sites are the "worse than bare" shape — they name a real card and a non-existent item — and the right repair (delete the dead id) is a judgement about 19 sites in 4 files across three other cards' surfaces, larger than this cohort's dispatch. Routed, not guessed |
| `mutations/inputs.py:470`, `:486`, `mutations/resolvers.py:621`, `mutations/sets.py:1179` | `spec-036 L3-1` / `spec-036 M3-1` | `spec-036`: `L3` -> **0**; `M3` -> **7**, and all seven are `AR-M3` about the `"__all__"` sentinel, not the FK-to-field-name reversal the code claims. `spec-036`'s own revision log names its tag families as `Major-` / `Medium-` (Rev 2), `AR-H#` / `AR-M#` / `Low-1` (Rev 3), `CR-#` (Rev 4), `DRY-#` (Rev 5), plus an earlier `P1` / `P2` pass — **`L3-1` and `M3-1` match none of them** | Card named, label resolves nowhere, and a live wrong candidate (`AR-M3`) sits one hyphen away. `mutations/inputs.py` was writable; left untouched deliberately |
| `rest_framework/sets.py:685` | `the overridable Decision-7 hook` | Block-resolved (the same docstring names `spec-039 Decision 7` nine lines down); line is already **91** characters | Not an orphan, so outside the repair rule — and cohort C recorded the same length verdict. Also dirty at baseline |

### Files skipped because they were dirty or fenced

`git status --porcelain` was taken at pass start (`<scratchpad>/cohortF-027/status-before-027.txt`, 41 rows) and re-checked immediately before writing; all 26 target files were clean at that moment, and a `diff -rq` of the pre-pass copies against `git show HEAD:` copies confirmed **all 26 were byte-identical to `HEAD`** — this pass's baseline and `HEAD` coincide, unlike cohort C's.

| Path | Owner | Orphans it carries | Attribution established for the handoff |
|---|---|---|---|
| `django_strawberry_framework/types/base.py` | fenced by the dispatch (and dirty) | `:990` `Decision-8 remediation tail shared by all six named rejections`; `:526` `the H1 collision guard` | `:990` -> **`spec-032 Decision 8`**, whose heading is `The six schema-validation diagnostics` — "all six named rejections" is that Decision's own subject. `:526`'s `H1` — owner **not** established |
| `tests/test_relay_connection.py` | fenced (cohort E took it mid-cycle) | `:1038`, `:1081`, `:2865` `Decision-6 fallback`; `:1965` `the M1 non-queryset ``GraphQLError``` | `Decision-6` -> **`spec-033 Decision 6`**, same evidence as the 12 repaired here. `M1` -> **`spec-030 Decision 7`**, same evidence as `connection.py:1139` / `:1356` |
| `examples/fakeshop/test_query/test_library_api.py` | fenced | `:3880`, `:5120` `Decision-5 failure families` / `headline contract`; `:4043` `Decision-12 nested visibility bonus`; `:3753` `Revision 2 P1`, `:3808` `Revision 6 P3`, `:3949` / `:3964` `Revision 7 P1` / `P2` | `Decision-5` -> **`spec-032 Decision 5`** (`Null for invisible rows, GraphQLError for malformed ids` — the docstrings' exact claim). The four `Revision` ids all resolve in `spec-032` (`Revision 2`: 17, `Revision 6`: 3, `Revision 7`: 16); `Decision-12` **not** established |
| `django_strawberry_framework/mutations/sets.py` | dirty at baseline (cohort B) | `:594`, `:937` `the Decision-13 twin of ``make_declaration_registry``` | -> **`spec-038 Decision 13`**, the same evidence and the same recorded weakness as `tests/mutations/test_sets.py:1528` |
| `rest_framework/{inputs,serializer_converter,resolvers,sets}.py` | dirty at baseline (cohort C) | the `H3` / `H5` / `H4` / `SR-3` / `Decision-7` sites above | Already adjudicated by cohort C; this pass re-measured every one and reached the same verdict |
| `orders/base.py`, `orders/inputs.py`, `tests/orders/test_inputs.py`, `tests/test_registry.py`, `examples/fakeshop/apps/library/orders.py`, `examples/fakeshop/apps/kanban/schema.py` | fenced by the dispatch | none of either class | — |

**Churn that appeared mid-pass and was left alone (`AGENTS.md` rule 34).** Between the baseline snapshot and the final `git status`, another session took `docs/SPECS/spec-{037,039,040,041,045,046}-*.md`, `docs/SPECS/appx/spec-{001,009,015}-*-rationale.md`, and cohort E published `docs/builder/bld-slice-10-027-wrapped_citations_outside_package.md`. Nothing was reverted. Because five of those specs are ones this pass cites, **every citation added by this pass was re-verified against the current working tree after the churn** — 19 `### Decision N` headings each resolving to exactly 1 heading, plus `spec-039 M3` (5), `spec-032 Revision 7 P1` (3) and `P2` (7). All resolve.

### Files touched

Grounded in `git status --porcelain` and in a `diff` of each file against the pre-pass copy held outside the repo. 26 files, 47 edits, **no line added or removed in any of them** — every edit is a same-line substitution, so no reflow occurred anywhere and no citation could be split across a break.

- `django_strawberry_framework/optimizer/nested_fetch.py` — 3 sites -> `spec-033 Decision 6`
- `django_strawberry_framework/optimizer/nested_planner.py` — 2 sites -> `spec-033 Decision 6`
- `django_strawberry_framework/optimizer/lateral_fetch.py`, `optimizer/walker.py` — 1 site each -> `spec-033 Decision 6`
- `django_strawberry_framework/filters/sets.py` — 3 sites -> `spec-027 Decision 4` / `Decision 8` x2
- `django_strawberry_framework/filters/__init__.py` — 3 sites -> `spec-027 Decision 11`
- `django_strawberry_framework/filters/inputs.py` — 1 site -> `spec-027 Decision 9`
- `django_strawberry_framework/sets_mixins.py` — 2 sites -> `spec-027 / spec-028 Decision 8`
- `django_strawberry_framework/connection.py` — 3 sites -> `spec-030 Decision 3` x1, `spec-030 Decision 7` x2 (both `M1`)
- `django_strawberry_framework/auth/mutations.py` — 1 site -> `spec-040 Decision 8`
- `django_strawberry_framework/testing/client.py` — 1 site -> `spec-043 Decision 5`
- `django_strawberry_framework/forms/inputs.py`, `mutations/inputs.py` — 1 site each -> `spec-039 M3`
- `tests/optimizer/test_walker.py` — 6 sites (5 -> `spec-033 Decision 6`, 1 -> `spec-033 Decision 4`)
- `tests/filters/test_sets.py` — 3 sites -> `spec-027 Decision 4` x2, `Decision 8` x1
- `tests/filters/test_inputs.py` — 3 sites -> `spec-027 Decision 3` x1, `Decision 9` x2
- `tests/types/test_definition_relations.py` — 2 sites -> `spec-027 Decision 4`
- `tests/types/test_base.py` — 1 site -> `spec-015 Decision 4`
- `tests/mutations/test_sets.py` — 1 site -> `spec-038 Decision 13`
- `tests/auth/test_queries.py` — 1 site -> `spec-040 Decision 10`
- `tests/test_scalars.py` — 1 site -> `spec-037 Decision 5`
- `tests/test_sets_mixins.py` — 1 site -> `spec-027 / spec-028 Decision 8`
- `tests/test_permissions.py` — 1 site -> `spec-034 Decision 9`, `Revision 3` dropped
- `tests/test_relay_node_field.py` — 2 sites -> `spec-032 Revision 7 P1` / `P2`
- `tests/test_views.py` — 1 site, dead `M1` deleted
- `examples/fakeshop/apps/library/filters_genre.py` — 1 site -> `spec-027 Decision 4`
- `docs/builder/bld-slice-11-027-orphaned_round_ids_and_hyphenated_decisions.md` — this artifact

### Tests added or updated

None. This pass adds no executable statement and no contract; there is nothing new for a test to pin. The existing suite is the regression check and was run.

### Validation run

Every command from the repository root. No `--cov*` flag anywhere in this pass.

| Check | Command | Result |
|---|---|---|
| Format (scoped, never `.`) | `uv run ruff format <the 26 files>` | `26 files left unchanged`, exit 0 |
| Lint (scoped) | `uv run ruff check --fix <the same 26>` | `All checks passed!`, exit 0 |
| Source layout / ASCII-only / trailing commas | `uv run python scripts/check_trailing_commas.py --check <the same 26>` | exit 0 |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md).` exit 0 |
| Pre-commit (all 5 hooks) | `uvx pre-commit run --files <the same 26>` | kanban-constants, source-layout, ruff-format, ruff-check, citations — **all Passed** |
| Focused tests | `uv run pytest tests examples/fakeshop/apps/library examples/fakeshop/test_query/test_library_api.py --no-cov -q` | **5472 passed, 39 skipped in 44.89s** |
| Line-length postcondition | `<scratchpad>/cohortF-027/edits_f027.py --check` | 47 rewritten lines, longest **98** (`connection.py:1356`), **0** over 99, **0** line-count changes |
| Wrapped-citation postcondition | own scan of the 26 touched files | **0** `#"` without a closing `"` on the same line — and **0** at `HEAD`, so none was introduced and none pre-existed |

**Citation-gate contribution, measured per file rather than inferred from the global delta.** `path::Symbol` and `#"` counts for each of the 26 files, `HEAD` vs worktree: `auth/mutations.py` 1/0, `connection.py` 11/0, `filters/__init__.py` 1/0, `filters/inputs.py` 10/0, `filters/sets.py` 11/0, `forms/inputs.py` 12/0, `mutations/inputs.py` 7/0, `optimizer/lateral_fetch.py` 6/0, `optimizer/nested_fetch.py` 7/0, `optimizer/nested_planner.py` 10/0, `optimizer/walker.py` 7/0, `sets_mixins.py` 9/0, `testing/client.py` 0/0, `filters_genre.py` 0/0, `tests/auth/test_queries.py` 0/0, `tests/filters/test_inputs.py` 1/0, `tests/filters/test_sets.py` 0/0, `tests/mutations/test_sets.py` 2/0, `tests/optimizer/test_walker.py` 4/0, `tests/test_permissions.py` 5/0, `tests/test_relay_node_field.py` 0/1, `tests/test_scalars.py` 0/3, `tests/test_sets_mixins.py` 0/0, `tests/test_views.py` 3/0, `tests/types/test_base.py` 1/0, `tests/types/test_definition_relations.py` 0/0 — **every one identical before and after.** This pass therefore contributes **0** to the global count. It stood at 779 when cohort C measured it and at 782 now; the +3 is other cohorts' and is not claimed here. The count could not have risen from this pass in any case: `check_citations.py` resolves `path::Symbol` only, which is exactly why no gate in this repo can see either of the two classes this cohort censused.

**Focused-scope justification.** The 13 package modules touched span eight subsystems — `optimizer/` (4 modules), `filters/` (3), `connection.py`, `sets_mixins.py` (shared by the filter *and* order families), `auth/`, `testing/`, `forms/`, `mutations/` — and the 12 touched test files sit across `tests/optimizer`, `tests/filters`, `tests/types`, `tests/mutations`, `tests/auth`, and the `tests/` root. No proper subset of `tests/` covers that, so the whole package tree is the honest scope. `examples/fakeshop/apps/library/filters_genre.py` is a fakeshop app module consumed by the library live suite, which adds `examples/fakeshop/apps/library` and `examples/fakeshop/test_query/test_library_api.py`; the latter is fenced from editing but reading and running it is not restricted. The run is a pure regression check — the diff contains no executable token, proved below — so a failure would have meant a mistake in the instrument, not in a contract.

#### Churn classification, every path in `git status --porcelain`

| Owner | Paths |
|---|---|
| **This pass (cohort F)** | the 26 files in `### Files touched`, plus this artifact |
| Cohort A (`bld-slice-6-027-*`) | `consumers.py`, `routers.py`, `filters/factories.py`, `types/finalizer.py`, `types/relay.py` |
| Cohort B (`bld-slice-7-027-*`) | `mutations/{fields,resolvers,sets}.py`, `examples/fakeshop/test_query/test_products_api.py` |
| Cohort C (`bld-slice-8-027-*`) | `optimizer/extension.py`, `orders/{__init__,factories}.py`, `rest_framework/{resolvers,serializer_converter,sets}.py`, `utils/inputs.py` |
| Cohort D (`bld-slice-9-027-*`) | `docs/SPECS/spec-055-search_fields-0_1_2.md` |
| Cohort E (`bld-slice-10-027-*`) | `examples/fakeshop/apps/kanban/schema.py`, `tests/test_relay_connection.py` |
| Concurrent `spec-028` session | `orders/{base,inputs,sets}.py`, `types/base.py`, `docs/SPECS/spec-028-orders-0_0_8.md`, its rationale companion, `examples/fakeshop/apps/library/orders.py`, `examples/fakeshop/test_query/test_library_api.py`, `tests/orders/*`, `tests/test_registry.py`, `bld-slice-{1,2}-028-*.md`, `build-028-*.md` |
| Another concurrent session, appeared mid-pass | `docs/SPECS/spec-{037,039,040,041,045,046}-*.md`, `docs/SPECS/appx/spec-{001,009,015}-*-rationale.md` |
| Worker 0 | `docs/builder/build-027-filters-0_0_8.md` |

No path is claimed by this pass and another owner. Nothing was reverted; no `git stash` / `checkout` / `restore` / `worktree` was used anywhere in this pass.

### Executable-token identity proof

Instrument: `<scratchpad>/cohortF-027/tokid_f027.py`, written fresh in a cohort-private subdirectory. It tokenizes with `tokenize`, drops `COMMENT` / `NL` / `NEWLINE` / `INDENT` / `DEDENT` / `ENCODING` / `ENDMARKER` and every **statement-position** `STRING` (a `STRING` preceded by `NEWLINE`/`INDENT`/`DEDENT`/`ENCODING`/`NL` and followed by `NEWLINE`), and compares the remaining `(type, string)` **sequence element-wise**. Every **other** string literal is KEPT — a module path inside a call, a dict key, an annotated-assignment value — which is the case a naive instrument drops and thereby passes.

One baseline suffices, and that is itself a measurement: `diff -rq` of the 26 pre-pass copies against the 26 `git show HEAD:` copies reported no differences, so `HEAD` **is** this pass's baseline for every file.

| File | vs `git show HEAD:<path>` | exec tokens |
|---|---|---|
| `django_strawberry_framework/auth/mutations.py` | IDENTICAL | 3126 |
| `django_strawberry_framework/connection.py` | IDENTICAL | 5088 |
| `django_strawberry_framework/filters/__init__.py` | IDENTICAL | 183 |
| `django_strawberry_framework/filters/inputs.py` | IDENTICAL | 2759 |
| `django_strawberry_framework/filters/sets.py` | IDENTICAL | 7348 |
| `django_strawberry_framework/forms/inputs.py` | IDENTICAL | 1718 |
| `django_strawberry_framework/mutations/inputs.py` | IDENTICAL | 2555 |
| `django_strawberry_framework/optimizer/lateral_fetch.py` | IDENTICAL | 4079 |
| `django_strawberry_framework/optimizer/nested_fetch.py` | IDENTICAL | 886 |
| `django_strawberry_framework/optimizer/nested_planner.py` | IDENTICAL | 4053 |
| `django_strawberry_framework/optimizer/walker.py` | IDENTICAL | 4509 |
| `django_strawberry_framework/sets_mixins.py` | IDENTICAL | 1472 |
| `django_strawberry_framework/testing/client.py` | IDENTICAL | 1483 |
| `examples/fakeshop/apps/library/filters_genre.py` | IDENTICAL | 67 |
| `tests/auth/test_queries.py` | IDENTICAL | 1424 |
| `tests/filters/test_inputs.py` | IDENTICAL | 5894 |
| `tests/filters/test_sets.py` | IDENTICAL | 35233 |
| `tests/mutations/test_sets.py` | IDENTICAL | 5617 |
| `tests/optimizer/test_walker.py` | IDENTICAL | 21135 |
| `tests/test_permissions.py` | IDENTICAL | 12030 |
| `tests/test_relay_node_field.py` | IDENTICAL | 6482 |
| `tests/test_scalars.py` | IDENTICAL | 2036 |
| `tests/test_sets_mixins.py` | IDENTICAL | 245 |
| `tests/test_views.py` | IDENTICAL | 10959 |
| `tests/types/test_base.py` | IDENTICAL | 7905 |
| `tests/types/test_definition_relations.py` | IDENTICAL | 2076 |

`0 DIFFERENT` across all 26. Re-run **after** `ruff format` / `ruff check --fix`, so the verdicts describe the tree as it stands.

#### Challenge set — six mutations plus a control, landing asserted before the verdict was read

Asserted in the script's own `ASSERTED` dict, written before the run: `C0 IDENTICAL | C1 DIFFERENT | C2 DIFFERENT | C3 DIFFERENT | C4 IDENTICAL | C5 IDENTICAL | C6 DIFFERENT`. Reference file for every case: `sets_mixins.py` at `HEAD` (1472 exec tokens).

| Case | Mutation | Asserted | Verdict | tokens | First divergence |
|---|---|---|---|---|---|
| C0 control | byte-identical copy | IDENTICAL | **IDENTICAL** | 1472 vs 1472 | — |
| C1 operator flip | `if field_path is None:` -> `is not None:` | DIFFERENT | **DIFFERENT** | 1472 vs 1473 | token 109 `(NAME,'None')` != `(NAME,'not')` |
| C2 inserted statement | `_unused = 0` after `cfg = cls._permission` | DIFFERENT | **DIFFERENT** | 1472 vs 1475 | token 1023 `(NAME,'return')` != `(NAME,'_unused')` |
| C3 deleted statement | `cfg = cls._permission` removed | DIFFERENT | **DIFFERENT** | 1472 vs 1467 | token 1018 `(NAME,'cfg')` != `(NAME,'return')` |
| C4 docstring rewrite | module docstring replaced wholesale | IDENTICAL | **IDENTICAL** | 1472 vs 1472 | — |
| C5 comment rewrite | a full comment line replaced | IDENTICAL | **IDENTICAL** | 1472 vs 1472 | — |
| **C6 non-statement string** | `_root_type_suffix: str = "InputType"` -> `"InputTypeEVIL"` | DIFFERENT | **DIFFERENT** | **1472 vs 1472** | token 82 `(STRING,'"InputType"')` != `(STRING,'"InputTypeEVIL"')` |

All seven matched. **C6 is the case that earns the table its shape: the token counts are equal, 1472 vs 1472.** A count-only or length-only instrument passes it silently; only the element-wise sequence comparison catches it. That is why every row above reports a verdict and not merely a count, and why "token count unchanged" is not a token-identity claim.

**The anchor discipline held.** Every anchor was asserted to occur **exactly once** before use, with the assertion placed *before* any mutant file was written, so a missing anchor aborts the run having produced nothing. Every mutant was written under `<scratchpad>/cohortF-027/challenge-027/`, **outside** the repository; no tracked file was ever mutated, so no revert was needed and none is claimed.

### Failability proofs

None; this pass introduced no new boundary.

Discharged mechanically rather than on prose: the executable-token identity table shows the diff contains no statement, branch, guard, comparison, or raise for the mandatory floor to select.

### Hot-path budget

Not applicable; the plan declares no hot path. `optimizer/nested_planner.py`, `optimizer/walker.py`, `connection.py` and `filters/sets.py` do carry hot paths, but this pass changes no executable token on any of them (proved above), so there is no cost to measure.

### Floor verification

Not applicable; the plan declares floor-verification scope none. No slice in this cycle changes an executable statement.

### Implementation notes

- **Hyphen normalized to a space at every repaired site, and only there.** The 39 remaining hyphenated occurrences were left alone: 28 of them are block-resolved (their block names a card), so normalizing them would be pure churn on files this pass has no other reason to touch, and 11 are fenced or unestablishable. The mixed spelling inside `filters/sets.py` — a repaired comment now reading `spec-027 Decision 8` six lines below a docstring still reading `Decision-8` — is deliberate on the minimal-diff ground, and recorded here so it does not read as an oversight in the diff.
- **The repair predicate is block-orphan, not line-bare.** Repairing all 70 line-bare hits would have inserted a card next to a card already there 20 times; repairing only the 50 block-orphans inserts one exactly where no reader could resolve the reference. The 20 false positives are enumerated by file in the census table so a reviewer re-running a line-scoped grep does not read them as missed work.
- **`spec-NNN / spec-NNN Decision N` for a shared substrate, not a coin flip.** Used at the three `sets_mixins.py` / `tests/test_sets_mixins.py` sites because the mixin is provably shared and both cards' Decision 8 own a half of it. The alternative — pick the filter card because this is the `027` cycle — would have been wrong for every `OrderSet` caller.
- **A review-round id was kept in three places and dropped in three others, on one rule.** Kept where the id still resolves in the named card *and* the card cites it against the same claim (`spec-039 M3` x2, `spec-032 Revision 7 P1`/`P2`); dropped where the contract has a Decision that states the invariant directly (`spec-030 Decision 7` x2 replacing `M1`, `spec-034 Decision 9` replacing `Decision 9, Revision 3`) or where the id resolves nowhere (`tests/test_views.py`'s `M1`, deleted). The rule is the dispatch's fifth method requirement; the split is where it lands on real sites.
- **No reflow anywhere.** The apply instrument refuses the whole batch if any rewritten line exceeds 99 characters or if any file's line count changes. Longest resulting line: 98 (`connection.py:1356`). Two candidate repairs were shaped by that constraint rather than by preference: `tests/test_permissions.py:1906` would have reached 105 characters had the `Revision 3` id been kept alongside the new card, and `rest_framework/sets.py:685` was left alone for the same reason cohort C left it. Reflow is the mechanism that splits a citation across lines, which is the defect cohorts A, E and Slice 4 exist to repair.
- **Batch application over 47 individual edits.** Each edit is an exact-string substitution asserted to match **exactly once** in its file; a non-unique or absent anchor refuses the entire batch and writes nothing. This is what makes the "no line added or removed" claim mechanical rather than reviewed.

### Notes for Worker 3

- **Instruments are all under `<scratchpad>/cohortF-027/`** and every filename carries `027`: `census_f027.py`, `edits_f027.py`, `tokid_f027.py`, `challenge_f027.py`, plus `head-027/`, `prepass-027/`, `worktree-027/`, `challenge-027/`, `census-worktree-027.json`, `census-after-027.json`, `status-before-027.txt`, `files-027.txt`. **Read before executing**; the scratchpad root is shared and holds ~90 generically-named files from other cohorts, several of which collided earlier in this cycle. Nothing in this artifact rests on a shared-root script.
- **The part most worth auditing is the unresolved list, and specifically the `Finding N` verdict.** 19 occurrences, 9 of them carrying `` (``spec-038-form_mutations-0_0_12`` Finding N) `` as though resolvable, and `grep -ci finding` over `spec-038` returns **0**. If that measurement is wrong, the conclusion inverts; please re-derive rather than accept it. `tests/forms/test_sets.py`, `tests/forms/test_resolvers.py`, `tests/mutations/test_resolvers.py` and `tests/rest_framework/test_sets.py` were all writable and were all left untouched on purpose.
- **The weakest attribution is `spec-038 Decision 13`** at `tests/mutations/test_sets.py:1528`. The cited Decision introduces `make_declaration_registry`; the symbol under test, `make_meta_validating_metaclass`, appears in **no** spec. Correct for what the sentence says ("the Decision-13 twin of `make_declaration_registry`"), wrong if read as "the Decision that specifies this function". If Worker 3 prefers it unresolved, reverting that one edit is a single-line change and the other 46 are independent of it.
- **`spec-027 Decision 4` is titled `Upstream-primitives parity floor`, and six repairs cite it for the owner-aware conditional.** Attributing on the heading alone would reject them; the evidence is in the body (`**Owner awareness.**`, `**Where the conditional runs.**`, `filter_for_field`, 4x `related_target_for`). Flagging it so the heading/subject gap does not read as a mismatch.
- **Two prose changes go beyond inserting a card**, both stated in the repair tables rather than left to be found in the diff: `tests/test_permissions.py:1906` drops `, Revision 3`, and `tests/test_views.py:2144` replaces `the M1 row for the masking direction` with `the masking-direction row`. Every other edit inserts a `spec-NNN` and normalizes a hyphen.
- No shadow file was used. `scripts/review_inspect.py` was **skipped** for all 26 files: this pass adds no logic, and the helper's `<stem>.stripped.py` replaces every comment and string-literal token with `...`, so its output is byte-identical before and after. The token-identity table is the mechanical evidence for the skip — the same recorded skip and reason Slices 2 and 4 and cohort C carried.

### Notes for Worker 1 (spec reconciliation)

Seven items. None is a `spec-027` edit; all concern surfaces fenced from this cohort, other cards' documents, or decisions only the custodian can take.

- **`Finding N` is cited 19 times in shipped test prose and exists in no spec — the largest unresolvable class this cycle has measured.**
  - Where it lives: `tests/forms/test_sets.py` (`:292` in-block, `:372`, `:377`, `:405`, `:551`), `tests/forms/test_resolvers.py` (`:1147`, `:1153`, `:1289`, `:1907`, `:1940`, `:1971`, `:2041`, `:2061`, `:2079`, `:2109`), `tests/mutations/test_resolvers.py` (`:1595`, `:1616`, `:1637`), `tests/rest_framework/test_sets.py` (`:611`).
  - Current wording, `tests/forms/test_resolvers.py:1153`: "validation on a one-field update (``spec-038-form_mutations-0_0_12`` Finding 3)."
  - Recommended replacement: drop the id and keep the card — "validation on a one-field update (``spec-038``)." — at all nine carded sites, and drop the bare id entirely at the ten uncarded ones, since the surrounding sentence already states the invariant in every case.
  - Reason: `grep -ci finding docs/SPECS/spec-038-form_mutations-0_0_12.md` -> **0**; same for `spec-036` and `spec-039`. None of the three has a rationale companion, so the ids were never moved — they never existed in a spec. `grep -rloE '\bFinding [0-9]+' --include='*.md'` over the repo returns no spec at all. Deciding whether the numbering should instead be *restored* into `spec-038` is a custodian call, not a builder's, which is why 19 sites were left untouched.
- **`spec-036 L3-1` / `M3-1` name a tag family `spec-036` does not have, and a wrong candidate sits one hyphen away.**
  - Where it lives: `mutations/inputs.py:470`, `:486`, `mutations/resolvers.py:621`, `mutations/sets.py:1179`.
  - Current wording, `mutations/inputs.py:486`: "Return whether ``field`` is a forward FK / OneToOne with a real DB column (spec-036 L3-1)."
  - Recommended replacement: "(spec-036 Decision 8)" if Decision 8's step-1 relation-decode contract is what carries the forward-FK-with-a-real-column rule; otherwise the card alone, "(spec-036)".
  - Reason: `L3` occurs **0** times in `spec-036`; `M3` occurs **7** times and every one is `AR-M3` about the `"__all__"` sentinel, not the FK-to-field-name reversal the comments claim. `spec-036`'s own revision log lists its tag families as `Major-` / `Medium-`, `AR-H#` / `AR-M#` / `Low-1`, `CR-#`, `DRY-#`, and an earlier `P1` / `P2` pass — `L3-1` and `M3-1` match none.
- **The relation-id visibility contract has no Decision to cite, and `spec-036 Decision 10` is the wrong one.**
  - Where it lives: `tests/mutations/test_resolvers.py:637` / `:641`, `tests/mutations/test_sets.py:849`.
  - Current wording, `tests/mutations/test_resolvers.py:641`: "the override CANNOT bypass the id type-check / Decision-10 visibility contract a raw-pk override would have skipped".
  - Recommended action: no code edit until the custodian names the owner. Either confirm that `spec-036 ### Decision 10` is intended to cover create-path relation-id visibility (in which case its body needs a sentence saying so, since all eight of its internal cross-references scope it to `update` / `delete` **row** lookups), or name the Decision that does and this cohort's successor cites it.
  - Reason: `_relation_visibility_error` is named only in `spec-039` (as `036`'s helper, at P1.1), and `spec-036` Decision 10's body and every cross-reference to it are about row reachability, not relation-id attachment. Attributing on adjacency would have produced exactly the "sends the reader to a real Decision that says something else" defect the dispatch forbids.
- **`auth/mutations.py:1174` cites `D16` and `spec-040` has 12 Decisions.**
  - Current wording: "uses, so \"what counts as a registered primary\" stays single-sited (D16);".
  - Recommended replacement: the card plus the Decision that owns the single-sited primary lookup — `spec-040 Decision 8` reads as the candidate ("The user model's primary `DjangoType` is required, validated at bind") but was **not** confirmed, so the custodian should settle it.
  - Reason: `grep -c '^### Decision ' docs/SPECS/spec-040-auth_mutations-0_0_13.md` -> **12**. `D16` cannot be a `spec-040` Decision, which is the same disproof shape cohort C used on `spec-035 Decision 11`. This is a **third** spelling of the `Decision` concept (`DN` short form, 36 occurrences, 3 block-orphans repo-wide) and is outside this cohort's dispatch; the file was touched for a different site, so the disproof is recorded rather than acted on.
- **The largest unmeasured reference population left in `.py` is the spaced `Decision N`: 1230 occurrences, 257 block-orphans, repo-wide.**
  - Recommended action: scope it by file to future cohorts the way cohort C's partition was scoped. The concentration is `tests/test_routers.py` **26**, `connection.py` **20**, `tests/test_permissions.py` **19**, `examples/.../test_library_api.py` **12**, `tests/types/test_base.py` **11**, `tests/optimizer/test_extension.py` **10**, `tests/test_list_field.py` **10**, `tests/test_views.py` **10**, `tests/types/test_resolvers.py` **9**, `permissions.py` **8**, `tests/test_relay_connection.py` **8**.
  - Reason: cohort C censused this spelling over **8** files and found 18 orphans; the same block-scoped instrument over the whole `.py` fence finds **257**. `tests/test_routers.py` alone also carries the cycle's second known wrapped reference, `Decision\n    19` at line 1647, which no line-scoped instrument can see.
- **`spec-046`'s `M1` is the only class-1 site in this cohort's fence that the rationale extraction genuinely orphaned, which makes the class rarer and the *other* class larger than the dispatch assumed.**
  - Current situation: `spec-046`: 0 occurrences of `M1`; its rationale companion: 4. Together with cohort C's `orders/factories.py:9`, that is **2** sites repo-wide. Meanwhile ids resolving in **no** document total **26** occurrences.
  - Recommended action: no spec edit. Record in the closeout that the rationale-extraction-orphan class is essentially closed at 2 sites, and that the durable class is the never-existed id — because a rationale move is at least *detectable* (grep the companion), whereas an id that was never written down anywhere is only detectable by measuring the spec that the code names.
  - Reason: rationale companions exist for `spec-001`-`028` and `044`-`048` only. Code overwhelmingly cites `029`-`043`, which have no companion, so an unresolvable id in that range was never moved out and cannot be recovered from one.
- **A concurrent session tightened `spec-033`'s comment-hygiene contract mid-pass to forbid review-round ids outright, and two live sites on that card's surface now contradict it.**
  - Where it lives: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`, `Revision history`, Revision 3 item (4). It went dirty *after* this pass's citation verification and reads, in the working tree: "**doc-reference hygiene** — a production or test comment on this card's surface cites a spec, a card, or a symbol path, never a per-cycle review artifact, a review-round or finding id (`Revision N`, `P<n>`), or a build-plan step". At `HEAD` the same item says only "production/test comments no longer cite the per-cycle review artifact".
  - Current wording of the two contradicting sites, `tests/optimizer/test_walker.py:2426` and `:2455`: "own ``ORDER BY`` (spec-033 Decision 11, cursor-parity / Revision 3)." and "column, not the full row (spec-033 Decision 6 / Revision 3)."
  - Recommended replacement: "(spec-033 Decision 11, cursor-parity)" and "(spec-033 Decision 6)" — the Decision in each case already carries the invariant the sentence states, so the id is removable without loss.
  - Reason: the two sites are in a file this pass edited, so the divergence is in this pass's diff neighbourhood and would otherwise read as something this pass introduced. It did not: both predate this pass and are unchanged at `HEAD`. They were **not** repaired, on two grounds — the new contract is another session's uncommitted text and this cohort takes no instruction from it, and `Revision 3` genuinely resolves in `spec-033` (16 `Revision` refs), so both sites are already carded and resolvable and are therefore outside this cohort's repair rule. Worker 1 owns whether the tightened contract is adopted and, if so, the sweep it implies across every `Revision N` / `P<n>` citation on `spec-033`'s surface.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[build]: BUILD.md
[plan]: build-027-filters-0_0_8.md
[slice8]: bld-slice-8-027-decision_attribution.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
