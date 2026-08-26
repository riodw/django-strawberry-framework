# Build: Slice 4 — live HTTP coverage on a Relay-Node-shaped fakeshop type + public-export promotion

Spec reference: `docs/SPECS/spec-030-connection_field-0_0_9.md` (Slice checklist :76-:79; Decision 7 :356-:372; Decision 14 :431-:439; Test plan Slice 4 :510-:521; Edge cases :457-:475; DoD item 7 :584)
Status: final-accepted

**Closure path: procedural closure via spec reconciliation (`Status: final-accepted`), no Worker 2/3 dispatch.** Every Slice 4 sub-check is satisfied by the shipped state at `HEAD`; the CODE GAP list is empty; the divergences found are all SPEC DRIFT plus one shipped-contract-with-no-spec-sentence, and Worker 1 reconciled all of them in this pass. Nothing is owed to a file this cycle may write.

## Working-tree baseline re-read (`git status --short`, start and end of pass)

The build plan's baseline list **grew again**: beyond the plan's snapshot, `tests/forms/test_converter.py`, `tests/forms/test_inputs.py`, `tests/forms/test_sets.py`, and `tests/test_views.py` are now dirty from the concurrent session, and `tests/mutations/test_operations.py` remains untracked. All of it is out of scope (`AGENTS.md` rule 34) — neither edited nor reverted.

**`django_strawberry_framework/__init__.py` is a Slice 4 surface AND concurrent-owned.** Audited read-only. Its working-copy diff against `HEAD` is **three added comment lines only** — the single-source-of-the-release note above `__version__`:

```shell
git show HEAD:django_strawberry_framework/__init__.py > <scratch outside repo>/init_HEAD.py
diff <scratch>/init_HEAD.py django_strawberry_framework/__init__.py
# 57a58,60  > (three comment lines)
git diff --stat -- django_strawberry_framework/__init__.py   # 1 file changed, 3 insertions(+)
```

No import line, no `__all__` entry, no re-export changed. **Both the committed and the working version export `DjangoConnection` / `DjangoConnectionField`**, so every claim below about the public surface is true of both and needs no version qualifier. No gap in `__init__.py` was found, so nothing is escalated to the maintainer on that file.

`uv run` worked all pass (the concurrent `tool.hatch.version` migration named in the plan has settled); no `.venv/bin/python` fallback was needed.

`.py` files written by this pass: **none**. `git status --short` shows exactly one file modified by me (`docs/SPECS/spec-030-connection_field-0_0_9.md`) plus the untracked companion I own and this artifact.

## Plan (Worker 1)

### Spec status-line re-verification

Read `:1`-`:11` (title, shipped line, `Status:`, Key glossary references opening). The `Status:` line's Slice 4 clause reads "Slice 4 (live HTTP coverage on a Relay-Node-shaped fakeshop type **and** the public-export promotion)" — accurate against `HEAD` and against this slice's audit. The header's `Shipped in 0.0.9` / `released under the CHANGELOG.md ## [0.0.9] heading` claims are Slice 5's audit surface, not falsified by anything here. **No status-line edit owed by this slice.**

### DRY analysis

**Helper inventory checked.** Not applicable in the write sense — this pass adds no code and no test, so no helper is proposed. The whole-package inventory was still refreshed to place the audited behavior, grepped (not read end to end) for the shapes this slice needs: `total_count`, `should_include`, `direct_child_selected`, `connection_total_count_selected`, `_connection_field_requested`. Relevant candidates found and read: `connection.py::_total_count_requested`, `connection.py::_has_next_page_requested`, `optimizer/selections.py::should_include`, `::direct_child_selected`, `::connection_total_count_selected`. The finding this produced is in the audit below (sub-check 3d).

- **Existing patterns reused.** The reconciliation reuses the three grading tests Slices 1-3 established (`## Current state` licence in all three of its cases; the `## Out of scope` / `## Non-goals` state-vs-scope test; the two-disjoint-instrument population sweep) rather than deriving new ones. Applied explicitly below.
- **New helpers justified.** None. One throwaway markdown link/anchor checker under the scratchpad **outside the repo**, verified on a known-good file before use (below).
- **Duplication risk avoided.** The directive-gating sentence this pass adds could have been spelled once per selection-gating mention (8 sites). It is stated where the gate's semantics are defined (Decision 4 clause (b)) and where the case is enumerated (`## Edge cases`), with the checklist and Test-plan rows carrying only the live pin — see the population table for the sites deliberately left alone and why.

### Boundary count

Zero new boundaries: no code change. No failability proof is owed (`BUILD.md` `### What needs a proof, and what does not` — a doc-only pass introduces no guard). No slice split considered; a spec-only reconciliation is one coherent unit.

### Hot-path declaration

**`none`.** Stated explicitly per the build plan's conditional declaration: this pass lands no change inside `connection.py::_pipeline_sync` / `::_pipeline_async` / `::_finalize_queryset` or `optimizer/extension.py::apply_connection_optimization`, and no `.py` change at all.

### Floor-verification scope

**`none`.** Stated explicitly: no `.py` change lands under `connection.py`, `types/`, `optimizer/`, or `examples/fakeshop/**`, so nothing touches the Strawberry schema-construction seam. The floor (Django 5.2.16 / Python 3.10 / strawberry-graphql 0.316.0, per `BUILD.md` `## Floor verification`) is not exercised by a markdown edit; the shared `.venv` was not mutated and no floor venv was built.

### Slice 4's contract, audited against `HEAD`

Every citation is symbol-qualified except inside this per-cycle scratchpad, where raw `path:NN` is licensed.

**Sub-check 1 — the public-export promotion.** SATISFIED. `django_strawberry_framework/__init__.py` carries `from .connection import DjangoConnection, DjangoConnectionField` (`:17`) and both names in `__all__` (`:129`-`:130`), at `HEAD` and in the working copy alike (byte-diff above). The tested-usage discipline Decision 14 names is satisfied within the slice: `examples/fakeshop/apps/library/schema.py` imports both from the top-level package (`:16`-`:17`), not from `django_strawberry_framework.connection`.

**Sub-check 2 — the root `DjangoConnectionField(GenreType)` on the `library` `Query`.** SATISFIED, and **reachable through the composed live schema, not merely declared.**

- `examples/fakeshop/apps/library/schema.py::GenreType.Meta` declares `interfaces = (relay.Node, Named)`, `filterset_class = filters_genre.GenreFilter`, `orderset_class = orders_genre.GenreOrder`, and `connection = {"total_count": True}` (`:228`-`:235`).
- `examples/fakeshop/apps/library/schema.py::Query.all_library_genres_connection` is `DjangoConnection[GenreType] = DjangoConnectionField(GenreType)` (`:566`), annotated with the comment naming `spec-030 / Decision 14` and the public-surface import.
- Composition: `examples/fakeshop/config/schema.py::Query` inherits `LibraryQuery` first, and `schema = DjangoSchema(query=Query, …)` is what `config.urls` serves. Reachability is proven by execution, not by reading the inheritance list — the six focused live runs below drive `allLibraryGenresConnection` over `/graphql/` and pass.

**Which library connection fields are `030`'s, and which are a later card's.** Attributed with `git log --oneline --reverse -S<symbol> -- examples/fakeshop/apps/library/schema.py`, first-introducing commit:

| Field | First commit | Owner |
|---|---|---|
| `all_library_genres_connection` | `8cac3495` "Finish spec-030-connection_field-0_0_9.md" | **`030`'s own — the Slice 4 surface** |
| `all_library_issues_connection` | `51421e54` "feat(relay): keyset value-encoded cursors via Meta.cursor_field (idea #3 / BACKLOG-39)" | the `0.0.14` keyset work |
| `all_library_periodicals_connection` | `51421e54` (same) | the `0.0.14` keyset work (its nested `issuesConnection` windows) |
| `all_library_loans_connection` (behind `FAKESHOP_TEST_LOAN_CONNECTION`, default OFF) | `027e653c` "Add shared relation fixture models and tests for composite primary keys" | later; the row-preserving-predicate acceptance surface |

Same for the three `Meta.connection = {"total_count": True}` opt-ins in that module: `GenreType` (`:235`) is `030`'s; `LoanType` (`:116`, inside the flag block) and `IssueType` (`:360`) are the later cards'. **No later card's field is claimed as `030`'s anywhere in this artifact or in the reconciled spec.**

**Sub-check 3 — the five live HTTP tests.** All five exist under their exact spec names AND assert the five contracted properties. Each was read against the spec sentence rather than grepped, and each was attributed: all five landed in `8cac3495`, `030`'s own build commit.

| Spec row | Shipped test | What it actually pins |
|---|---|---|
| (a) round-trip | `test_genre_connection_full_round_trip` (`test_library_api.py:2762`) | Two POSTs. Page 1 `filter: {name: {iContains: "a"}} orderBy: [{name: ASC}] first: 2` → `names == ["Alpha","Banana"]` (ordering), `hasNextPage is True`, a non-empty string `endCursor`, `totalCount == 4` with the docstring stating why 4 is distinguishing (grand total 5, page size 2). Page 2 uses the page-1 `endCursor` as `after:` → `["Delta","Gamma"]`, `isdisjoint` against page 1 (no overlap), `hasNextPage is False`, `totalCount == 4` again. `"errors" not in payload` on both. Also decodes each `node.id` as a model-label GlobalID. **All four contracted properties + no-errors pinned.** |
| (b) `first` + `last` | `test_genre_connection_first_and_last_rejected` (`:3338`) | `status_code == 200` AND `"errors" in payload` AND `"mutually exclusive" in messages` — i.e. the package guard surfaces as a GraphQL error on a 200, not an HTTP failure. Cites `connection.py::_guard_first_and_last`. |
| (c) `first: 0` | `test_genre_connection_first_zero_empty_edges` (`:3364`) | `edges == []`, `pageInfo.hasNextPage is True`, `pageInfo.endCursor is None`, and `totalCount == 3` — the pre-slice count is unaffected by the zero window. Pins the *real* `ListConnection` 0.316.0 shape rather than an assumed one. |
| (d) `totalCount` omitted | `test_genre_connection_total_count_omitted_no_count` (`:3400`) | **Pins the load-bearing property, not observability.** `assert not any("COUNT(" in query["sql"].upper() for query in captured.captured_queries)` under `CaptureQueriesContext(connection)` — real SQL, not a wire-shape inference — plus `"totalCount" not in conn` and correct edges. |
| (e) two aliases | `test_genre_connection_two_aliases_independent_total_counts` (`:3715`) | One request, `matchA` (`iContains "a"`) and `matchZ` (`iContains "z"`) → `3` and `1`. Docstring names the per-instance-attribute contract vs an `info.context` stash (Decision 4). |

**No test in the set asserts observability where the load-bearing property was available.** The one row where that risk was live — (d) — is the one that captures SQL. The `BUILD.md` companion warning (a sidecar `filter:` / `orderBy:` argument silently routing a selection to a fallback and making a fast-path test pin the fallback) does not apply to (d): its query carries **no** `filter:` and **no** `orderBy:`, only `first: 2`, so it cannot be routed anywhere but the path it claims.

Focused run, all six rows (the five plus Decision 11's live pin), `uv run pytest <node ids> --no-cov -q`: **6 passed in 14.72s** (8 xdist workers). Recorded per `BUILD.md`'s hazard note: a passing focused run is not proof the full parallel suite passes; the final gate owns that.

**Sub-check 4 — every Test-plan name verified by reading the body, not the name.** Done in the table above. This is the first slice of the cycle where no named test was missing and none had an inverted assertion. Two shipped tests in that live block are *not* in the Test plan, and they split:

- `test_genre_connection_total_count_skip_include_no_count` (`:3434`, commit `9e864f59` "Finish REVIEW of 0.0.9") — **`030`'s own contract, and the spec never stated it.** See the finding below.
- `test_anonymous_inline_fragment_under_connection_field_resolves` (`:3530`, same commit) — not `030`'s contract. Its own docstring calls it a regression for an **optimizer-folder High**; the connection field is the reproducer, the fix is in the selection walker. Recorded, not folded into `030`.

Everything else in that block belongs elsewhere and is attributed rather than claimed: `test_genre_connection_flat_leaf_*` / `_expanded_origin_pagination_` / `_nested_spelling_` / `_no_match_is_empty` (`8af55482`, the row-preserving-predicate work), `test_first_overrun` / `test_stale_after_cursor_no_error` / the backward-pagination rows (`18567c63`, the `spec-032` cursor-contract conformance matrix the block comment itself names), `test_library_genres_connection_pages_by_to_many_aggregate` (`0b914487`). `test_genre_connection_order_by_to_many_no_node_multiplication` (`e2b5b10b`, "spec-030 review round") **is** `030`'s and is already homed by Slice 3 in Decision 11's `Aggregate-ordering coexistence` paragraph — its citation from the spec resolves at `HEAD` and the test passes.

**Sub-check 5 — the Test-plan tail check re-run at `HEAD`.** The spec asks: "a new reachable root field changes the registered-type count and the full SDL. Confirm no existing `test_query/` test snapshots the whole SDL or asserts a registered-type count." **It HOLDS.** Four instruments over `examples/fakeshop/test_query/`:

1. `as_str|print_schema|str(schema)|registered_types|len(registry|type_count|as_sdl` → **0 hits.**
2. `sdl|SDL|__schema|introspect` → hits exist, all narrow. Every one read.
3. `type_map|_schema\.|schema\._` → 3 comment/docstring hits (one explicitly says the assertion is "through real introspection rather than `schema._schema.type_map`") plus one `cache_info()` hits/misses assertion in `test_optimizer_auto_api.py`, which counts schema-install cache events, not types.
4. `__schema` alone → `{ __schema { queryType { name } } }` (a name read), an introspection **refusal** row, and one resource-policy cost row asserting `charged > MAX_COST` (an inequality, so more types can only strengthen it).

The two candidates that could plausibly have broken were read in full and are membership assertions, not snapshots: `test_library_api.py:3301` builds a `set` of `Query` field names and asserts `"allLibraryLoans" in` / `"allLibraryLoansConnection" not in`, never an equality against the full field set. No whole-SDL snapshot and no registered-type count exists in the tier.

### CODE GAP list

**Empty.** No sub-check is unsatisfied, narrowed, or silently dropped in shipped code. No gap exists in `django_strawberry_framework/__init__.py` either, so nothing is escalated to the maintainer as a concurrent-owned write.

### Spec slice checklist (verbatim)

Quoted as the spec states them. **This cycle's inversion:** a box is ticked because the SHIPPED state satisfies it, not because a builder implemented it this pass.

- [x] Promote `DjangoConnectionField` / `DjangoConnection` to the [`django_strawberry_framework/__init__.py`][package-init] public surface **in this slice**, alongside the live usage that proves the public shape (per [Decision 14](#decision-14--connectionpy-module-and-the-public-export-gate)).
- [x] Add a root `DjangoConnectionField` over the [`library`][fakeshop-library-schema] `GenreType` (already Relay-Node-shaped with both [`Meta.filterset_class`][glossary-metafilterset_class] and [`Meta.orderset_class`][glossary-metaorderset_class] declared) with `Meta.connection = {"total_count": True}`, exposed on the `library` `Query` via [`DjangoConnectionField(GenreType)`][connection], imported from the public surface.
- [x] Live HTTP tests in [`examples/fakeshop/test_query/test_library_api.py`][fakeshop-test-library]: (a) a full round-trip requesting `edges { node { id name } } pageInfo { hasNextPage endCursor } totalCount` with `filter:` + `orderBy:` + `first:` + `after:` asserting correct pagination, ordering, and `totalCount` on the unpaginated post-filter set; (b) the `first` + `last` `GraphQLError` path; (c) a `first: 0` empty-edges + `pageInfo` shape; (d) a query that omits `totalCount` and asserts the response is correct without a count (the selection-gating contract); (e) two aliases of the connection with different `filter:` values asserting independent `totalCount`s (the per-instance-count contract).

Plus the Test-plan tail check, quoted and audited as a fourth box:

- [x] A check before declaring the suite undisturbed: a new reachable root field changes the registered-type count and the full SDL. Confirm no existing `test_query/` test snapshots the whole SDL or asserts a registered-type count; re-run the check at implementation time.

All four ticked; **no deferral reason is owed.** Box 3's (d) clause is ticked on the strength of the shipped test being *stronger* than the sentence — the sentence's own hedge is reconciled below rather than tolerated.

### Implementation steps

None. No `.py` file is written this pass; the work is the audit plus the spec reconciliation in `### Spec changes made (Worker 1 only)`.

### Test additions / updates

None owed. Every contracted test exists and pins its contract. No temp test was needed: the contract questions were all answerable by reading the shipped tests against the spec plus one focused execution.

### Implementation discretion items

None — nothing is delegated, because no builder is dispatched.

---

## Final verification (Worker 1)

### Populations swept, instruments used, and counts

Every number is re-derivable by running the named token against the named file. Counts are **occurrences** (`grep -o … | wc -l` / `grep -c` where the token cannot repeat on a line), never matching lines, so a claim wrapped across two lines cannot hide. Both instruments per population run over the raw file, so **headings and fenced code blocks are included** (Slice 2's two blind spots).

| Population | Instrument A | Instrument B, disjoint | Union of sites | Disposition |
|---|---|---|---|---|
| The **public-export** claim | the ref-id `package-init` — **11** occ (`:3`, `:77`, `:88`, `:102`, `:120`, `:427`, `:435`, `:450`, `:584`, `:590`, `:698`-the-def) | the concept words, which carry no ref-id: `public surface` / `public-export` / `public export` / `Public exports` / `__init__.py` — **28** occ over `:5`, `:35`, `:76`, `:77`, `:78`, `:102`, `:431`, `:435`, `:450`, `:512`, `:582`, `:584`, `:650`, `:667`, `:698` | **9 claim sites** (`:5`, `:35`, `:76`, `:77`, `:435`, `:450`, `:512`, `:582`, `:584`) + `:102` the licensed observation. Instrument A alone misses `:5`, `:35`, `:76`, `:78`, `:512`, `:582`; instrument B alone misses `:120`, `:427`, `:590` (version-boundary sites, correctly not part of this claim) | **all 9 TRUE at `HEAD`** — nothing edited. The export landed exactly as contracted |
| The **`docs/TREE.md` `[alpha]` slot** state claim | `\[alpha\]` — **5** occ pre-edit (`:53`, `:83`, `:102`, `:433`, `:530`) | the state vocabulary with no bracket in it: `reserve` / `target layout` / `target package layout` / `planned tag` — hits `:41`, `:53`, `:69`, `:71`, `:83`, `:102`, `:127`, `:433`, `:530` (the `:41`/`:69`/`:71`/`:127` hits are `reserves the seam` / unrelated) | **2 drift sites** (`:53`, `:433`) + **2 Slice-5 instructions** (`:83`, `:530`) + **1 licensed observation** (`:102`) | 2 rewritten (S2, S3). `\[alpha\]` = **3** occ post-edit, exactly the 2 instructions and the 1 observation; `already reserves` / `reserves the .connection.py` = **0** |
| The **module-layout / fork** prediction | `relay\.py` — **3** occ (`:104`, `:437`, `:700`-the-def) | the layout vocabulary that never names the file: `relay/` / `one module` / `fork` / `subpackage` / `flat module` — **4** sites (`:53`, `:54`, `:433`, `:437`) | **1 drift site** (`:437`); `:54` graded stay, `:53`/`:433` folded into the `[alpha]` population, `:104` is a Slice-1-graded `Current state` bullet | 1 rewritten (S4) + 1 new link def (S5). `lands in a separate` = **0**, `forks into a` = **0** |
| The **selection-gating** contract, swept for the directive half | `@skip` / `@include` / `directive` — **2** occ pre-edit, BOTH the `directives=()` factory kwarg (`:67`, `:336`), i.e. **zero** sites about directive-resolved selection | the gate's own vocabulary: `selection-gat` / `counted only when` / `counted-only-when-selected` / `when the query omits` / `selection-gated` — **8** sites (`:62`, `:65`, `:116`, `:247`, `:313`, `:463`, `:517`, `:570`) | **0 spec sites carried the shipped property**; 4 chosen as its home (`:79`, `:313`, `:463`, `:517`+new row) | 4 sites written (S6-S9). `directive-resolved` = **2**, `@skip` = **4** post-edit |
| The **"where observable" hedge** | `where observable` — **1** occ (`:517`) | the hedge's inverse, the unhedged twin: `no count query runs` — `:247`, `:463` | **1 site**, with 2 already-unhedged siblings proving the hedge was the outlier | rewritten (S8). `where observable` = **0** |

**Where the instruments mattered, and how each failed.** Row 2: an `\[alpha\]`-keyed sweep finds all five sites but cannot grade any of them — the three dispositions (drift / Slice-5 instruction / licensed observation) are invisible to the token and only readable in the sentence, which is the recurring shape behind "a population is not a disposition". Row 3: `relay\.py` is blind to `:53` and `:433`, which make a module-layout claim without naming the file; the layout-vocabulary instrument is blind to `:104`, which names the file for an unrelated reason. Row 4 is the important one: **the only instrument a reader would reach for first — grepping `@skip` / `directive` — returns two hits that are both a false positive** (`directives=()`, the factory's pass-through kwarg), so a sweep that stopped at "2 occurrences, both accounted for" would have concluded the property was already documented. The population was established from the other direction, by finding where the gate is *defined* and reading what it says.

**One instrument was verified before it was trusted.** The markdown link/anchor checker (throwaway, in the scratchpad **outside the repo**) was first run on `START.md`, where it reports exactly 5 problems, all five inside that file's own documented convention examples (`[text][ref-id]` three times, `](#decision-N)` and `](#some-heading)`) — the known-good signature. Only then was its clean result on the spec believed. Slice 3's lesson applied without re-deriving it.

### The `## Current state` licence, applied explicitly — all three cases

Slices 1-3 established three cases. **All three appear in this slice, which is why each is named separately.** Both bullets in this slice's scope were re-derived at the spec's authoring commit `eaaf1385` ("Create spec-030-connection_field-0_0_9.md"), read-only via `git show eaaf1385:<path>` into a scratch path outside the repo — never by analogy with a sibling sentence.

- **Case 1 — a dated observation that is TRUE: `:102`, left exactly as written.** Three clauses, each verified at `eaaf1385`: `git show eaaf1385:django_strawberry_framework/connection.py` → **ABSENT**; `git show eaaf1385:docs/TREE.md | grep connection` → line 266 reads `connection.py  # [alpha] DjangoConnectionField (Relay)`, so the layout did reserve the slot then; and `__all__` at that commit is exactly `BigInt, DjangoListField, DjangoOptimizerExtension, DjangoType, OptimizerHint, SyncMisuseError, __version__, auto, finalize_django_types, strawberry_config` — the spec's enumeration, complete and with nothing extra, and neither connection symbol present. **Slice 3 handed `:102` forward saying it "belongs to Slice 4 and was graded there"; it had not been graded anywhere** (`grep ':102'` over all three prior artifacts returns nothing). A handoff's claim about its own prior grading is a claim like any other — the third instance this cycle of a handed-forward inventory being wrong about itself.
- **Case 1 again — `:110`, left exactly as written.** At `eaaf1385`, `GenreType.Meta` was `interfaces = (relay.Node,)` with `filterset_class = filters_genre.GenreFilter` and `orderset_class = orders_genre.GenreOrder`, and `config/schema.py` already carried `_optimizer = DjangoOptimizerExtension()` with `extensions=[lambda: _optimizer]` and `config=strawberry_config()`. Every clause true of the repo it describes. `GenreType.Meta.interfaces` is `(relay.Node, Named)` today and `Meta.connection` now sits beside the sidecars — later additions that do not touch a sentence about that date.
- **Case 2 — a prediction the build falsified: none in this slice's scope.** Named explicitly rather than left silent: `:102` and `:110` are the only `Current state` bullets Slice 4 owns, and both are pure observation.
- **Case 3 — a true prediction whose enduring implication later work falsified: Decision 14's fork conditional (`:437`), outside `## Current state`.** The case Slice 3 discovered recurs here on a Decision rather than a `Current state` bullet, which is worth naming: the licence is not what made it drift, the falsified *implication* is. Reconciled as S4.

### The `## Out of scope` / `## Non-goals` test, applied explicitly

**The test: does the sentence assert an artifact's STATE, or what this card does not build?** State claims drift when falsified; scope claims stay, because `030`'s scope is fixed history no later card can change. Applied to every candidate in this slice's scope:

- **Decision 14's fork conditional (`:437`) — a STATE claim wearing a scope claim's clothes, so it drifted.** "If the combined connection + Root-Node surface grows past ~one module, it forks into a `relay/` subpackage at that time" reads as scope, but its antecedent asserts a measurable state — that the surface is still within about one module. Measured at `HEAD`: `connection.py` 2,077 lines, `relay.py` 603, `keyset.py` 654 — three flat modules, ~3.3k lines, and no `relay/` subpackage. The antecedent is long satisfied and the consequent never happened, so the sentence now reads as an unmet restructuring obligation that `docs/TREE.md`'s recorded flat layout contradicts and that the card's own ticked DoD box in [`KANBAN.md`][kanban] (`:3482`, "Decide whether full Relay support belongs here or a separate `relay/` subpackage") says was already decided. **Rewritten to the scope boundary it was really expressing** (S4), keeping the `START.md` pointer as the standing advice it is rather than a pending trigger. Deleting it would have lost a real boundary; leaving it would have had a reader open the package, count three modules, and conclude the spec is wrong.
- **Decision 14's first two clauses (`:437`, same sentence) — scope, TRUE, kept in substance.** `connection.py` for the connection surface and a separate `relay.py` for the Root-Node surface under `032` came true exactly: `django_strawberry_framework/relay.py` carries `DjangoNodeField` / `DjangoNodesField` and cites `spec-032` Decisions 3/4/5/11 in its own module docstring. Only the future tense ("lands in") became wrong, and the rewrite states it as the shipped layout.
- **`## Out of scope` (`:547`-`:559`) — every bullet a scope statement, ALL UNCHANGED.** `Root node(id:) / nodes(ids:) … DjangoNodeField / DjangoNodesField — the Full Relay story (DONE-032-0.0.9)` names an owner, not a status, and remains true even though `032` shipped: the surface is still not `030`'s. Same for the `Meta.cursor_field` / keyset bullet (`:555`) — Slice 1 already graded the Decision-9-side deferral, and the Out-of-scope twin asserts ownership rather than an unshipped state. Editing either would be churn.
- **`## Non-goals` (`:122`-`:134`) — no Slice-4-owned bullet.** The connection-planning non-goal was reconciled by Slice 3; nothing in the section makes a public-export or live-coverage claim.
- **The Slice-4 checklist's `(already Relay-Node-shaped …)` parenthetical (`:78`) — kept.** A checklist item describes the work, and the parenthetical was true of the host it named; the shipped-spec convention keeps checklist boxes unticked with `Status:` as the source of truth, so a checklist sentence is not read as a present-tense state claim.
- **The Test-plan tail check (`:520`-`:521`) — kept, and deliberately.** "Confirm no existing `test_query/` test snapshots the whole SDL … re-run the check at implementation time" is a procedure the build discharged, not a state claim and not chronology about how the spec changed. It states a true fact (a new reachable root field moves the SDL and the type count) plus the check that fact demands. Rewriting it would trade a discharged instruction for churn; **auditing it and reporting that it holds is the deliverable, not editing it.**

### Spec changes made (Worker 1 only)

Line numbers are **post-edit**. Cause for every entry: this slice's audit, `docs/builder/build-030-connection_field-0_0_9.md` Slice 4. Every "what changed and why" went to `docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md`; the spec carries only the corrected contract, present tense, no amendment block, no chronology, no "(the review round's PN)" parenthetical.

**S1 — nothing.** The `Status:` line and header needed no edit; recorded so the per-spawn re-verification is visible rather than assumed.

**S2 — the `docs/TREE.md` Key-glossary bullet.** 1 site (`:53`). "(the target layout already reserves the `connection.py [alpha]` slot)" → the module "is the flat module … listed there under the on-disk package layout". Present-tense truth; the reservation was consumed by the build and the tag by Slice 5.

**S3 — Decision 14, paragraph 1.** 1 site (`:433`). Same stale parenthetical, same fix: "listed under the on-disk package layout in `docs/TREE.md`". **S2 and S3 moved in one change on purpose** — they are structurally identical sentences 380 lines apart, and fixing one and not the other is exactly the partial-claim-fix defect this cycle keeps finding.

**S4 — Decision 14, paragraph 3 (the module-layout decision).** 1 site (`:437`). The DoD question and its answer are restated as the shipped flat pair — `connection.py` plus the separate flat `relay.py` owned by `DONE-032-0.0.9` — and the fork conditional becomes the scope boundary it was expressing: whether the Relay surface later consolidates into a `relay/` subpackage is a package-layout decision no slice of this card makes, and `docs/TREE.md` records the layout on disk. The `START.md` fork-when-it-grows citation survives as standing advice, which keeps the `:54` Key-glossary pointer at it honest and is why `:54` needed no edit.

**S5 — one new link definition.** `[relay-root]: ../../django_strawberry_framework/relay.py`, under the existing `<!-- django_strawberry_framework/ -->` group in alphabetical order (between `relay` and `resolvers`). Net-new because the spec previously named the Root-Node module only as bare text; `[relay]` was already taken by `types/relay.py` and must not be reused. Disk-exists-checked.

**S6 — Decision 4, clause (b): the selection gate is directive-resolved.** 1 site (`:313`). "counts only when `totalCount` is selected in the query" gains "— selection is **directive-resolved**, so a `@skip(if: true)` / `@include(if: false)` on the field, or on the fragment wrapping it, suppresses the count exactly as omitting the field does". **This is the inverse-audit finding: a shipped contract with zero spec sentences.** `connection.py::_total_count_requested` delegates to `optimizer/selections.py::connection_total_count_selected`, whose walk is gated on `optimizer/selections.py::should_include`; the live pin is `test_genre_connection_total_count_skip_include_no_count`, from commit `9e864f59` — the `0.0.9` review round the rationale companion's `## Provenance of this record` already identifies as unrecorded. Decision 4 is Slice 1's, and Slice 1's audit is closed; this pass touches it anyway because the property IS the selection-gating contract that Slice 4's own sub-check (d) pins live, and no later slice will run over it. Recorded here so the cross-Decision touch is visible rather than silent.

**S7 — the `## Edge cases` `totalCount`-not-selected bullet.** 1 site (`:463`). Gains the directive case with its mechanism named — Strawberry's converted selections carry the field with its already-resolved directive arguments rather than dropping the node, so the predicate applies the include gate itself. That clause stays in the spec under `worker-1.md`'s implementation-relevant-rationale carve-out: a reader who does not know it will write the name-only predicate and reintroduce the bug. "Pinned by a Slice 4 live test" → "live tests" (plural), which is now true.

**S8 — the Slice-4 Test plan: 1 row rewritten, 1 added.** 2 rows (`:517`-`:518`). The `test_genre_connection_total_count_omitted_no_count` row loses the "where observable" hedge and states the assertion the shipped test makes — no `COUNT(` SQL at all, asserted over the captured queries rather than inferred from the wire shape. **The hedge was the one thing in this slice's contract that would have licensed a weaker test than the one that shipped**, and `BUILD.md` `### Query-shape tests must pin the load-bearing property, not observability` is the rule it sat against. The new row names `test_genre_connection_total_count_skip_include_no_count` with all four of its shapes, the `@skip(if: false)` keep-resolving control included — a control that did not run reads identically to a passing proof, so the row says the control exists.

**S9 — the Slice-4 checklist, sub-check (d).** 1 site (`:79`). "asserts the response is correct without a count" → "asserts the response is correct with no count query issued, plus the directive-excluded spelling of the same gate (`@skip` / `@include` on the field or its fragment wrapper) with a keep-resolving control". S6-S9 are the complete four-site population for the directive property; the other four selection-gating sites (`:62`, `:65`, `:116`, `:247`, `:570`) say "selection-gated" / "counted only when selected" / "when the query omits `totalCount`", none of which contradicts directive resolution, so spelling it at each would be churn rather than completeness. Named here so the choice is a decision and not an omission.

**Not changed, deliberately.** `:102` and `:110` (`## Current state`, licence case 1, both re-derived at `eaaf1385`). `:54` (the `START.md` advice pointer — the advice it quotes is verbatim-true of `START.md` and S4 keeps the citation alive). `:83` and `:530` (Slice-5 `[alpha]` instructions describing landed work; Slice 5 owns them and is audit-only). `:520`-`:521` (the discharged Test-plan tail check — see the scope test above). `:247` (User-facing API's "when the query omits `totalCount`, no count query runs" — illustrative doc, not contradicted). DoD item 7 (`:585`) — it enumerates "the `totalCount`-omitted no-count path" and defers to the Test plan, which now carries both rows, so it needs no second edit. The implementation-plan estimate row (`:450`, "~6" against 5 named tests) — the table is explicitly labeled as estimates, and the shipped count is 6 anyway once the directive row is counted. Nothing in Decisions 1-3, 5-13, or the Slice-1/2/3/5 checklist, Test plan, and DoD text.

### Rationale companion appends (Worker 1 only)

Append-only, each under the Decision whose contract it belongs to, using the file's documented `**Post-ship:**` bullet convention. No moved text was rewritten.

- **Decision 4 — 2 new `**Post-ship:**` bullets**, placed before the existing `P3b` provenance bullet so the section reads contract-then-provenance:
  - The directive-resolved gate: what "selected" was written to mean, what Strawberry's `convert_selections` actually hands the predicate, the concrete failure the name-only predicate would cause (a spurious `COUNT`, and on a non-`QuerySet` consumer-resolver return a spurious Decision 7 raise for a field the client excluded), the shipped delegation chain that shares one implementation with the plan-time `connection_count_required` predicate so the two cannot drift, the unrecorded `0.0.9` review round that is why no revision entry carries it, the four spec sites that now state it, and **the claim the Decision may no longer make** — that field presence in the document is what the gate reads.
  - The "where observable" hedge: that the row's own discharging test falsified it in the strict direction, cited to the `BUILD.md` rule the hedge sat against, and that the row now matches the unhedged `## Edge cases` twin it always sat beside.
- **Decision 14 — 2 new `**Post-ship:**` bullets** after the Revision 2 P2 entry:
  - The module-layout prediction: which clauses came true and read true today (with `relay.py`'s own docstring as the evidence), the measured line counts that satisfy the fork antecedent, the ticked DoD box that shows the question was already decided, why leaving it reads as an unmet obligation and deleting it would lose a real boundary, and the naming of this as the third grading case recurring outside `## Current state`.
  - The `[alpha]`-slot state claim: that two Decision-14-owned sentences asserted a `docs/TREE.md` state Slice 5 itself removed, what they say now, and the distinction an `[alpha]`-keyed sweep structurally cannot make between the three surviving mentions (instruction / instruction / licensed observation).
- **2 new link definitions** in the companion: `[relay-root]` under `<!-- django_strawberry_framework/ -->` and `[spec-030-key-glossary]` under `<!-- docs/SPECS/ -->`, both alphabetical, both resolving (the second's `#key-glossary-references` anchor exists in the spec).

### Postcondition proofs

- **Glossary gate:** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-030-connection_field-0_0_9.md` → `OK: 50 terms - all have glossary entries and at least one spec link.` Same before and after every edit.
- **Link / anchor integrity, instrument verified on `START.md` first** (see above). Spec: 110 defs, 109 used, `unused=['goal']` — the pre-existing orphan Slice 3 named, unchanged by this pass — and **no dangling in-page anchor, no undefined ref-id, no missing def target, no dangling def anchor.** Companion: 58 defs, 58 used, zero unused, zero problems.
- **Sweep postconditions** (all re-derivable): `where observable` = 0; `already reserves` / `reserves the .connection.py` = 0; `lands in a separate` = 0; `forks into a` = 0; `\[alpha\]` = 3 (the two Slice-5 instructions + the licensed observation); `directive-resolved` = 2; `@skip` = 4.
- **`.py` surface byte-unchanged by this pass.** `git status --short` lists exactly one modified file attributable to me (`docs/SPECS/spec-030-connection_field-0_0_9.md`) plus the untracked companion and this artifact; every dirty `.py` is in the concurrent session's baseline set, which grew by four `tests/` files during the pass and was neither edited nor reverted.
- **Focused tests:** `uv run pytest examples/fakeshop/test_query/test_library_api.py::{the five contracted rows + test_genre_connection_order_by_to_many_no_node_multiplication} --no-cov -q` → **6 passed**; `…::test_genre_connection_total_count_skip_include_no_count --no-cov -q` → **1 passed**. No `--cov*` flag was used in any invocation this pass.
- **Spec size:** 135,375 B → **136,865 B** (+1,490). Companion: 81,517 B → **86,773 B** (+5,256). The spec grew by four contract sentences and one link def; the explanation of all of it is in the companion, which is where the maintainer's split puts it.

### Public-surface check

In scope for this slice and filled rather than deleted, since `django_strawberry_framework/__init__.py` is Slice 4's own surface.

`git diff -- django_strawberry_framework/__init__.py` **does change the file**, and the change is **not** this cycle's: three added comment lines describing the single-source-of-the-release literal, verified by byte-diff against `git show HEAD:` (above). `__all__` and the re-export list are **identical** between `HEAD` and the working copy. The presence of `DjangoConnection` / `DjangoConnectionField` in both is authorized by the active spec — Slice 4 checklist sub-check 1 (`:77`), Decision 14 (`:435`), and DoD item 7 (`:585`) all require exactly this promotion in this slice. This pass added no public export and removed none.

### Documentation / release sanity

In scope (the slice's surface includes doc-adjacent and public-surface claims) and filled rather than deleted. This pass modified only the spec and its rationale companion; no `KANBAN.md`, `CHANGELOG.md`, `docs/GLOSSARY.md`, `docs/TREE.md`, `TODAY.md`, `README.md`, or `docs/README.md` edit was made — all fenced out of this cycle.

- **Version strings / statuses / card IDs.** The spec's `Status: **SHIPPED (0.0.9)**`, the `DONE-030-0.0.9` card id, and the sibling ids `DONE-031/032/033-0.0.9` + `DONE-029-0.0.9` match the shipped state; nothing this pass wrote asserts a version or status.
- **No KANBAN movement**, no spec archival (the spec is already at `docs/SPECS/` with companions in `docs/SPECS/appx/`), and no CHANGELOG touch — so those clauses are vacuous by construction, stated rather than skipped.
- **Links introduced by this pass point at existing files.** `[relay-root]` resolves to `django_strawberry_framework/relay.py` (exists, 603 lines) from both the spec (`../../`) and the companion (`../../../`); `[spec-030-key-glossary]` resolves to `../spec-030-connection_field-0_0_9.md#key-glossary-references`, whose heading exists. Both disk-exists-checked and confirmed by the anchor checker.
- **No verbatim spec text was copied into another file** by this pass, so the character-for-character `diff` obligation does not arise. The checklist quotations in `### Spec slice checklist (verbatim)` above are copied from the spec **as it stood at the start of this pass** — deliberately, since S9 edited sub-check (d) after the box was quoted, and the audit's job is to record the contract it audited.
- **No obsolete "coming soon" / "planned" / old-version wording remains in what this pass touched.** Verified: `planned for \`0.0.9\`` occurs 6 times, every one about `030`'s own three glossary entries or inside `:102`'s licensed observation — the count and the reasoning Slice 3 established, unchanged by this pass.
- **No script-rendered doc was regenerated**, and no module docstring was touched, so the staging-language clause does not apply. Recorded because the fence forbids the `docs/TREE.md` regenerate that a non-fenced cycle would owe here.

**One documentation divergence found and RECORDED for the maintainer, not edited** (Slice 5 is audit-only and owns `docs/GLOSSARY.md`): the glossary's `DjangoConnection` / `DjangoConnectionField` / `Meta.connection` entries describe `totalCount` as selection-gated but nowhere mention that selection is **directive-resolved**. `grep -inE '@skip|@include|directive-resolv' docs/GLOSSARY.md` returns exactly one hit, `:1498`, which is the optimizer plan-cache key entry and unrelated. The spec now states the property in four places; the glossary does not state it at all.

### Summary

Slice 4's contract is satisfied at `HEAD` in full. `DjangoConnection` / `DjangoConnectionField` are on the public surface in both the committed and the concurrently-dirtied `__init__.py`; the root `DjangoConnectionField(GenreType)` is declared on the `library` `Query` from the public-surface import and is **reachable through the composed live `/graphql/` schema, proven by execution rather than by reading the inheritance chain**; all five contracted live tests exist under their exact spec names, all five landed in `030`'s own build commit `8cac3495`, and all five assert the properties the spec contracts. Sub-check (d) — the one row where an observability-only assertion was the live risk — pins the load-bearing property, asserting over `CaptureQueriesContext` that no `COUNT(` SQL is issued, on a query carrying neither `filter:` nor `orderBy:` so it cannot be routed to a fallback. The Test-plan tail check holds: four instruments confirm no `test_query/` test snapshots the whole SDL or asserts a registered-type count, and the two membership-assertion candidates were read in full.

**CODE GAP list: empty. No gap in concurrent-owned `__init__.py`, so nothing escalated on that file.** Nine reconciliation items landed in the spec: two structurally identical stale `docs/TREE.md` `[alpha]`-slot claims 380 lines apart, Decision 14's fork conditional, one new link definition, the directive-resolved selection gate at its four sites, and the "where observable" hedge — each with its explanation in the companion and none of it in the spec.

**The finding worth carrying out of this slice** is the inverse-audit one, in its sharpest form yet: the directive-resolved selection gate is shipped, live-pinned, and had **zero** spec sentences — and the natural instrument for finding that (`grep '@skip\|directive'`) returns two hits that are *both* the factory's unrelated `directives=()` kwarg. An instrument that returns hits you can explain reads exactly like an instrument that found the population.

### Spec changes made (Worker 1 only) — deferral reasons for unticked boxes

None deferred. All four boxes in `### Spec slice checklist (verbatim)` are ticked because the shipped state satisfies them, and no box carries a struck or replaced clause (unlike Slice 3's box 1). Sub-check (d) is the only box whose *sentence* changed in this pass, and it changed because the shipped test exceeded it — a spec correction, not work owed to a future slice.

### Handed forward to Slice 5 and the integration pass

Verified at `HEAD` by this pass and **deliberately not fixed**.

**Both of this slice's own populations are CLOSED in the spec.** The public-export population needed no edit at all (9 claim sites, all true), and the `[alpha]`, module-layout, directive-gating, and hedge populations are each fully reconciled with their postcondition counts recorded. No later slice inherits any part of them.

**To Slice 5 (audit-only under the cycle's scope fence):**

- **New from this pass:** `docs/GLOSSARY.md`'s three `030` entries describe selection-gating without the directive-resolved property the spec now states in four places. Record only; the fence forbids the edit.
- **New from this pass:** the two surviving `[alpha]` mentions (`:83` checklist, `:530` `## Doc updates`) instruct Slice 5 to "drop its `[alpha]` planned tag" from `docs/TREE.md`. That work is done — `grep -in alpha docs/TREE.md` returns **zero** hits — so Slice 5's audit of those two rows should come back satisfied, not open.
- Carried forward unchanged from Slices 1-3: no `Meta.cursor_field` glossary heading while two entry bodies reference it; no `CHANGELOG.md` entry for the keyset-cursor feature; the already-sliced-`QuerySet` `GraphQLError` is shipped public behavior with no `CHANGELOG.md` entry and no glossary mention; and Slice 3's note that `030`'s own three glossary entries already read `shipped (0.0.9)` with the post-`033` cooperation-point wording, so they must be audited against Slice 3's rewritten S16 instruction rather than the old one.
- **A path claim the whole spec makes and no slice has graded — measured, not asserted.** `docs/spec-030` occurs **7** times, over **5** lines: `:87` (Slice-5 checklist, KANBAN spec-reference bullet), `:285` (**Decision 1**, `The spec file lives at …`), `:536` (the `## Doc updates` twin of `:87`), `:567` (DoD item 1, ×3), `:590` (DoD item 9). A disjoint instrument — `docs/spec-[a-z0-9]*` tokenized and counted — finds the same 5 lines plus the 2 `docs/spec-connection` occurrences (`:285`, `:536`) that name the pre-canonical filename the card body once used, which is a different claim in the same sentences. The file actually lives at `docs/SPECS/spec-030-connection_field-0_0_9.md` with companions in `docs/SPECS/appx/`, a path the spec spells correctly only **2** times (`grep -c 'docs/SPECS/'`). The reference-style *definitions* all resolve; only inline prose paths are stale. `:285` is the sharpest — a Decision asserting where the file lives, in the present tense, wrongly. Not folded into Slice 4: it is a doc-state population spanning Decision 1, the Slice-5 checklist, `## Doc updates`, and two DoD items, none of which is a Slice-4 surface, and `:87`/`:536` are a matched pair that must move together or reproduce the partial-fix defect.

**To the integration pass:**

- `test_anonymous_inline_fragment_under_connection_field_resolves` (`test_library_api.py:3530`, commit `9e864f59`) is a shipped regression pin in `030`'s live block whose subject is an **optimizer selection-walker** High, not a `030` contract. It is correctly absent from `spec-030` and should stay absent; named so a later sweep of that block does not adopt it into `030`.
- **A third instance of the card-less / spec-less provenance pattern Slices 2 and 3 flagged.** Slice 2 found `connection.py::_guard_source_not_pre_sliced` from a card-less commit; Slice 3 found `a3f84ea9` closing a spec-stated bound with no card. This slice found a `030` contract property — the directive-resolved gate — reaching the shipped package through `9e864f59` "Finish REVIEW of 0.0.9", a round the spec's own revision history does not record and whose finding labels the rationale companion already had to home. Three instances, all in seams `030` owns, all invisible to any spec-side instrument. If the integration pass runs one cross-cutting check, `git log -S` over each Decision-4 / Decision-7 / Decision-11 symbol for commits naming no card is the shape that finds them.
- The `DONE-032-0.0.9` parity-table row (`:150`) — Slice 3's handoff, still open, and now with a second reason to look: this slice verified that `032`'s `relay.py` surface is real and shipped, so the row's `planned` status word is confirmed wrong. Fixing it still needs someone who has audited `032`, which no `030` slice has.
- `:557` "**Auto-trigger of `finalize_django_types()`** — deferred to `032`" — carried from Slices 1-3, still unaudited. This slice noticed but did not verify that `examples/fakeshop/config/schema.py` calls `finalize_django_types()` explicitly at `HEAD`, which is consistent with the deferral never having been taken up; that is an observation, not the audit.
- The unused `[goal]` link definition in the spec — pre-existing, harmless, named again so a later sweep does not attribute it to this pass.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary-metafilterset_class]: ../GLOSSARY.md#metafilterset_class
[glossary-metaorderset_class]: ../GLOSSARY.md#metaorderset_class

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[package-init]: ../../django_strawberry_framework/__init__.py

<!-- tests/ -->

<!-- examples/ -->
[fakeshop-library-schema]: ../../examples/fakeshop/apps/library/schema.py
[fakeshop-test-library]: ../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
