# Build: Cohort B — raw `path:NN` line references in code comments (027)

Spec reference: `docs/SPECS/spec-027-filters-0_0_8.md` — this cohort discharges `AGENTS.md` rule 27's line-number prohibition over cohort B's declared file partition, per `docs/builder/build-027-filters-0_0_8.md` `### Catalog-discharge cohorts (added 2026-08-20, post-commit 8a9840dc)` (catalog item 6's three uncarded halves, item 4's `orders/sets.py` sites, item 7's mutations / forms half, item 8 scoped to this cohort's own files). The repaired citations resolve into `docs/SPECS/spec-036-mutations-0_0_11.md`, `docs/SPECS/spec-038-form_mutations-0_0_12.md`, `docs/SPECS/spec-028-orders-0_0_8.md`, `django_strawberry_framework/relay.py`, and the external `django-graphene-filters` cookbook.
Status: final-accepted

## Plan (Worker 1)

### Planning lives in the dispatch brief

This cohort has no Worker 1 planning pass of its own. The contract is `docs/builder/build-027-filters-0_0_8.md` `### Catalog-discharge cohorts` (the cohort-B row of the partition table, plus the `### Re-derived populations, for the record` paragraph) and the Worker 0 dispatch brief. `docs/builder/bld-slice-4-027-broken_substring_citations.md` is the format precedent, including its executable-token-identity instrument, which this pass reproduces and re-challenges.

**Ownership partition (declared, disjoint):** `django_strawberry_framework/orders/sets.py`, `django_strawberry_framework/mutations/{fields,resolvers,inputs,sets}.py`, `django_strawberry_framework/forms/inputs.py`, `examples/fakeshop/test_query/test_products_api.py`. Explicitly NOT this cohort's: `orders/inputs.py`, `orders/base.py` (held by a concurrent spec-028 session; `AGENTS.md` rule 34).

Section placement follows `docs/builder/ARTIFACT.md`.

### DRY analysis

Not applicable and deliberately skipped, on the ground `docs/builder/BUILD.md` `### Package-wide helper inventory before helper planning` sets: that rule gates *helper planning*, and this pass proposes no helper, shared constant, validation branch, or test helper. The diff contains no executable statement (proved mechanically below).

The one duplication this pass **did** find and did resolve is a duplication of *prose*, not of code: `mutations/fields.py` and `mutations/resolvers.py::coerce_lookup_id` carried the same two-sentence claim with the same broken reference, a copied pair. Both were repaired to the identical replacement text so the pair stays consistent — the reason the dispatch brief flagged them as one item. They are deliberately **not** collapsed into one site: a module docstring and a function docstring serve different readers, and neither can cite the other's prose.

### Spec slice checklist (verbatim)

Built from the dispatch brief's site table, one box per site, plus the two census-added classes and the cookbook durability decision. Boxes marked **(census-added)** are sites this pass found that the brief's table did not enumerate; the brief instructed a census rather than treating its table as complete.

- [x] `orders/sets.py` #"the cookbook lines 30-38 behavior" | ref into the external upstream cookbook, not this repo
- [x] `orders/sets.py` #"(cookbook lines 265-285)" | same
- [x] `orders/sets.py` #"(cookbook lines 115-170)" | same
- [x] (census-added) `orders/sets.py` #"Cookbook line 279-280" | same class, a fourth cookbook site the brief's table omitted
- [x] `mutations/fields.py` #"(``relay.py`` line 287)" | ref into this repo
- [x] `mutations/resolvers.py` #"(``relay.py`` line 287)" | same, identical wording — the copied pair, repaired consistently
- [x] `test_products_api.py` #"identical to the `036` model-driven path (line 388)" | bare in-file ref
- [x] `test_products_api.py` #"identical to the `036` anonymous denial (line 458)" | bare
- [x] `test_products_api.py` #"(mirror line 493)" | bare
- [x] `test_products_api.py` #"(mirror line 528)" | bare, and ALREADY ROTTED onto the wrong test
- [x] `test_products_api.py` #"(mirror line 694)" | bare, and ALREADY ROTTED onto the wrong test
- [x] (census-added) `mutations/sets.py` #"Decision 6 line 334" | raw spec line number
- [x] (census-added) `mutations/sets.py` #"Edge cases line 509" (two sites) | raw spec line number, ALREADY ROTTED by 6 lines onto an unrelated bullet
- [x] (census-added) `mutations/sets.py` #"Decision 6 line 336" | raw spec line number, ALREADY ROTTED by 2 lines onto the wrong paragraph
- [x] Item 4 in `orders/sets.py` (`Spec Decision N` with no card named, lines 19 / 318 / 461) — **NOT built by this pass; already discharged in the working tree by the concurrent spec-028 session.** Verified present, left alone (`AGENTS.md` rule 34). See `### Notes for Worker 1 (spec reconciliation)`.
- [x] (census-added) Item 4's equivalent in `mutations/` — six genuinely uncarded `Decision N` sites, two of which resolved to a DIFFERENT spec than the nearest named one
- [x] Item 8 (build-process provenance) scoped to this cohort's own files — three `finding-#1` sites, resolving to nothing anywhere in the repo
- [x] Cookbook durability decision recorded (`### Implementation notes`)
- [x] Wrapped-`#"` census over this cohort's files returns **0**

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --porcelain`, not memory. Five of the seven partition files changed; two are clean because the census found no defect in them.

- `django_strawberry_framework/orders/sets.py` — four cookbook sites. **This file is concurrently held**: the spec-028 session took it mid-pass and its four `Spec Decision N` / `Spec DoD` hunks are in the tree alongside mine. Verified both sessions' hunks coexist after my edits (`grep -c "spec-028 DoD 4(c)"` -> 2, and my two new cookbook symbol citations present).
- `django_strawberry_framework/mutations/fields.py` — one site, the module docstring's `relay.py line 287`.
- `django_strawberry_framework/mutations/resolvers.py` — five sites: the `relay.py line 287` twin in `coerce_lookup_id`, two uncarded `Decision 9` refs (module docstring + `refetch_optimized`), two uncarded `Decision 15` refs collapsed into one carded mention in `authorize_or_raise`, and the `finding-#1` provenance in `_invalid_lookup_id_error`.
- `django_strawberry_framework/mutations/sets.py` — seven sites: four raw spec line numbers (`Decision 6 line 334`, `Edge cases line 509` x2, `Decision 6 line 336`) and three uncarded `Decision N` refs (`make_declaration_registry`, `DjangoMutation.check_permission`, `_validate_relation_override_types`).
- `examples/fakeshop/test_query/test_products_api.py` — seven sites: the five bare mirror line refs and two `finding-#1` provenance mentions.
- `django_strawberry_framework/mutations/inputs.py` — **NOT modified.** Censused; zero line refs, zero uncarded `Decision N`, zero build provenance.
- `django_strawberry_framework/forms/inputs.py` — **NOT modified.** Censused; its one bare `Decision 7 P2` at line 93 is a line-wrap continuation of `(spec-038` on the preceding line, so it is already carded and is not a member of the class.

Every other modified path in `git status --porcelain` belongs to a concurrent session: cohort A (`consumers.py`, `routers.py`, `filters/factories.py`, `types/finalizer.py`, `types/relay.py`), cohort C (`optimizer/extension.py`, `utils/inputs.py`, `orders/__init__.py`, `orders/factories.py`, `rest_framework/resolvers.py`), cohort D (`docs/SPECS/spec-055-search_fields-0_1_2.md`), the spec-028 session (`orders/base.py`, `orders/inputs.py`, `types/base.py`, `docs/SPECS/spec-028-orders-0_0_8.md`, `examples/fakeshop/apps/library/orders.py`, `examples/fakeshop/test_query/test_library_api.py`, `tests/orders/*`, `tests/test_registry.py`), and Worker 0 (`docs/builder/build-027-filters-0_0_8.md`). None was touched by this pass and none was reverted.

### Per-site before / after, and what each line number resolved to

#### The cookbook refs — `orders/sets.py`

The cookbook is `~/projects/django-graphene-filters/django_graphene_filters/`, an external checkout named as the canonical working reference by `START.md` and by `docs/SPECS/spec-028-orders-0_0_8.md`. All four sites target `orderset.py`, which is 285 lines long — consistent with the `265-285` range.

| Site | Before | Resolved to (read at the cited lines) | After |
|---|---|---|---|
| `OrderSetMetaclass.__new__` | `the cookbook lines 30-38 behavior` | `orderset.py` 30-38 is the inherited-then-override `related_orders` merge inside `OrderSetMetaclass.__new__` | `the behavior of` / `` ``django_graphene_filters/orderset.py::OrderSetMetaclass.__new__`` `` |
| `OrderSet.get_fields` docstring | `(cookbook lines 265-285)` | `orderset.py` 265-285 is `AdvancedOrderSet.get_fields` in full | parenthetical **deleted** — the preceding line already carried `` ``django_graphene_filters/orderset.py::AdvancedOrderSet.get_fields`` ``, so the line number was a redundant restatement of a citation that was already durable |
| `OrderSet._expand_meta_fields` | `Cookbook line 279-280: "Works for both dict (iterates keys) and list/tuple (iterates values)."` | the quoted text is the comment on line **278**; 279-280 is the `for k in meta_fields:` loop it describes | `` ``django_graphene_filters/orderset.py::AdvancedOrderSet.get_fields`` `` `#"Works for both dict (iterates keys)"` plus the same explanation in prose |
| `OrderSet.get_flat_orders` docstring | `(cookbook lines 115-170)` | `orderset.py` 115-170 is `AdvancedOrderSet.get_flat_orders` in full | parenthetical **deleted**, same reason as the `265-285` site |

**Already-rotted number found:** the `line 279-280` site attributes a verbatim quote to two lines that do not contain it (it is on 278). Mild, but it is the class decaying in place.

#### The `relay.py line 287` pair — `mutations/fields.py` and `mutations/resolvers.py`

**Both numbers are ROTTED, and both point at unrelated text.** `django_strawberry_framework/relay.py` line 287 reads

```
    ``_resolve_real_pk`` (pinned to ``using`` when supplied): unlike the READ node field - which filters
```

— a sentence inside `decode_model_global_id`'s docstring about WRITE-side pk resolution. It says nothing about the `node(id: ID!)` argument signature the two citing sentences claim it does. (`types/relay.py` line 287 is a blank line inside `_resolve_id_default`'s docstring, so neither `relay.py` spelling resolves.)

The real target is `relay.py::DjangoNodeField`, whose docstring opens "Factory for the root ``node(id: ID!)`` Relay refetch field." and whose nested `_resolve` declares `id: strawberry.ID` under the comment "``id`` is the Relay-spec signature (``node(id: ID!)``) - the builtin shadow is deliberate."

Both sites are now `` (``relay.py::DjangoNodeField`` #"is the Relay-spec signature") ``. The substring occurs exactly **1** time in `relay.py`. The pair is byte-identical in the repaired clause, so a future reword of one is visibly a divergence from the other.

#### The `test_products_api.py` mirror refs — cited by test name

These are same-file references into the file's `036` mirror block. All five are cited by function name now; the numbers resolved as follows.

| Site | Before | Line NNN actually lands in | The test the prose means | Verdict |
|---|---|---|---|---|
| `test_create_item_via_form_unique_constraint_envelope_uses_all_sentinel` | `(line 388)` | body of `test_create_item_unique_constraint_envelope_uses_all_sentinel` (def 368) | same | number lands inside the right test, but not at it |
| `test_create_item_via_form_anonymous_is_denied_top_level_error_no_write` | `(line 458)` | body of `test_create_item_anonymous_is_denied_top_level_error_no_write` (def 439) | same | same |
| `test_create_item_via_form_missing_model_perm_is_denied_no_write` | `(mirror line 493)` | body of `test_create_item_missing_model_perm_is_denied_no_write` (def 474) | same | same |
| `test_update_item_via_form_visibility_scoped_hidden_private_row_is_not_found` | `(mirror line 528)` | body of `test_create_item_login_bracket_via_test_client` (def 509) | `test_visibility_scoped_update_delete_hidden_private_row_is_not_found` (def 588) | **ROTTED onto an unrelated test** |
| `test_create_item_via_form_relation_id_for_hidden_category_is_field_error` | `(mirror line 694)` | body of `test_update_item_wrong_type_global_id_on_id_is_field_error` (def 676) | `test_create_item_relation_id_for_hidden_category_is_field_error` (def 753) | **ROTTED onto an unrelated test** |

**Two of five are already rotted onto the wrong test**, and a reader following them lands on a login-bracket test and a wrong-type-GlobalID test respectively — neither of which is the mirror the prose describes. Per the brief, these were **not** renumbered: the line number is the defect. Each is now `` `test_products_api.py::test_<name>` ``, which the citation gate resolves (the five are part of the +7 count rise below).

#### The raw spec line numbers — `mutations/sets.py` (census-added)

| Site | Before | spec-036 line NNN actually is | The paragraph the prose means | After |
|---|---|---|---|---|
| `_shape_build_cache` comment | `spec-036 Decision 6 line 334` | 334 = `**Field set (Medium-4 ...)**` | 336 = `**Type identity and naming (AR-H1 / AR-M6).**`, which carries the `(model, operation kind, frozenset(effective field names))` tuple the sentence quotes | `spec-036 Decision 6 #"Type identity and naming"` |
| `_shape_build_cache` comment | `spec-036 Edge cases line 509` | 509 = the **Delete snapshot** bullet | 515 = `**Two mutations over one model share input types — for the same shape.**` | `spec-036 Edge cases #"Two mutations over one model"` |
| `_materialize_input_for` comment | `spec-036 Edge cases line 509` | same | same | same |
| `_validate_input_class` docstring | `spec-036 Decision 6 line 336` | 336 = `**Type identity and naming**` | 338 = `**Custom inputs follow the generated field-naming scheme (AR-M2).**`, which is what check 2 enforces | `spec-036 Decision 6 #"Custom inputs follow the generated field-naming scheme"` |

**Three of four are already rotted** — `Edge cases line 509` by six lines onto a bullet about delete snapshots (twice), and `Decision 6 line 336` by two lines onto the wrong paragraph of the same Decision. Every replacement substring occurs exactly **1** time in `docs/SPECS/spec-036-mutations-0_0_11.md`, measured with `grep -cF`.

#### Uncarded `Decision N` — `mutations/` (census-added)

`grep -E '(Spec|spec)?[ -]?Decision [0-9]+'` over the five package files in this partition returned 24 occurrences. Most are line-wrap continuations of a citation that names the spec on the preceding line (e.g. `(spec-036` / `Decision 14)`) and are therefore already carded — not members. Six are genuinely uncarded:

| Site | Before | Owner, established by measurement | After |
|---|---|---|---|
| `resolvers.py` module docstring | `(Decision 9 comes for free)` | `spec-036` D9 = "Optimizer composition and the `spec-035` G2 live-test handoff". **The nearest named spec on the same line is `spec-035`, whose D9 is "Version bumps are owned by the joint `0.0.10` cut"** — a reader following the nearest antecedent lands on version bumps | `spec-036 Decision 9` |
| `resolvers.py::refetch_optimized` | `- Decision 9 comes for free.` | same, and the same misleading `spec-035` antecedent two lines above | `spec-036 Decision 9` |
| `resolvers.py::authorize_or_raise` summary | `(Decision 15)` | `spec-036` D15 = "Write authorization: a DRF-shaped `check_permission` / `Meta.permission_classes` seam"; the module docstring already spells it `spec-036 Decision 15` | dropped from the summary line (it would exceed the 110 grace), carded once in the body instead of twice bare |
| `resolvers.py::authorize_or_raise` body | `- Decision 15)` | same | `the spec-036 Decision 15 authorization-failure surface` |
| `sets.py::make_declaration_registry` | `the over-consolidation trap Decision 13 names` | **`spec-038` D13** ("Finalization seam ... It gets its **own** explicit machinery ... the two ledgers stay disjoint"). `spec-036` D13 is "Version bumps are owned by the joint `0.0.11` cut", and `spec-036` IS the nearest named spec in this docstring — so the bare form pointed a reader at version bumps. The same file already cites `spec-038 Decision 13` for `make_declaration_registry` 85 lines lower | `spec-038 Decision 13` |
| `sets.py::DjangoMutation.check_permission` | `is synchronous (Decision 15)` | `spec-036` D15, per the preceding sentence's `spec-036 Decision 8 step 3 / Decision 15` | `spec-036 Decision 15` |
| `sets.py::_validate_relation_override_types` summary | `(Decision 10)` | `spec-036` D10, per the body's own `spec-036 Decision 10` two lines down | `spec-036 Decision 10` |

Not treated: `sets.py::_validate_relation_override_types`' `ConfigurationError` message contains `"Decision 10)"` as the continuation of an f-string whose previous fragment ends `(spec-036 `. That is an **executable string literal**, not a comment. Editing it is an executable-token change and a behavior change; out of scope by the pass's hard constraint. It is also already carded across the two fragments, so it is not a defect.

#### Build-process provenance — `finding-#1`

`grep -rn "finding-#1"` over the whole repo (excluding `.venv`, `.git`) returns exactly **3** hits, all in this partition, and **no** document anywhere defines `finding-#1`. It is a dead review-finding id from a build cycle whose record no longer exists — unambiguous build-process provenance under the dispatch brief's definition. All three now carry the surviving invariant with `spec-036 Decision 10` alone:

- `resolvers.py::_invalid_lookup_id_error` — `(spec-036 Decision 10 / finding-#1)` -> `(spec-036 Decision 10)`
- `test_products_api.py::test_update_item_wrong_type_global_id_on_id_is_field_error` — `(spec-036 Decision 10 / finding-#1 hardening)` -> `(spec-036 Decision 10)`
- `test_products_api.py::test_delete_item_wrong_type_global_id_on_id_is_field_error` — same

**Deliberately kept, not provenance:** `AR-H4`, `AR-M1`, `AR-M6`, `Major-1`, `Medium-4`, `CR-6`, `P1`, `P2`. Each was checked against its owning spec and resolves there (`AR-H4` 15 hits, `AR-M6` 13, `AR-M1` 10, `Medium-4` 5, `Major-1` 4, `CR-6` 2 in `spec-036`; `P1` 37 / `P2` 45 in `spec-038`, and 63 / 48 in `spec-039`). These are spec-internal finding labels a reader can look up, not build-round ids. That distinction is what separates them from `finding-#1`.

### Tests added or updated

None. This pass adds no executable statement and no contract; there is nothing new for a test to pin. The existing suites are the regression check and were run (`### Validation run`). The live `/graphql/` suite was run because it is one of the two files edited, not because a new assertion needed proving.

### Validation run

Every command run from the repository root. No `--cov*` flag was used anywhere.

| Check | Command | Result |
|---|---|---|
| Format (scoped, never `.`) | `uv run ruff format <the 7 partition files>` | `7 files left unchanged`, exit 0 |
| Lint (scoped) | `uv run ruff check --fix <the same 7>` | `All checks passed!`, exit 0 |
| Source layout / ASCII-only / commas | `uv run python scripts/check_trailing_commas.py --check` | exit 0 |
| Citation gate, before | `uv run python scripts/check_citations.py` | `OK: 772 citations resolve (695 in 422 .py files, 77 in KANBAN.md).` exit 0 |
| Citation gate, after | `uv run python scripts/check_citations.py` | `OK: 779 citations resolve (702 in 422 .py files, 77 in KANBAN.md).` exit 0 — **+7, nothing dropped** |
| Pre-commit hooks | `uvx pre-commit run --files <the same 7>` | 5 hooks, all `Passed` (kanban tracked path constants; source layout; ruff format; ruff check; citations resolve) |
| Churn classification | `git status --porcelain` before and after | see `### Files touched`; nothing unexpected, nothing reverted |
| Focused tests (incl. the live suite) | `uv run pytest examples/fakeshop/test_query/test_products_api.py tests/mutations tests/forms tests/orders --no-cov -q` | **756 passed in 33.96s** |

**Why the count rises by exactly 7, derived rather than asserted.** `scripts/check_citations.py` matches only `CITATION_RE = ([\w][\w./]*\.py)::([A-Za-z_][\w.]*)` and `continue`s any path under `UPSTREAM_PREFIXES`, which includes `django_graphene_filters/`. So of this pass's new references: the 5 `test_products_api.py::test_*` and the 2 `relay.py::DjangoNodeField` are counted (+7); the 2 new `django_graphene_filters/orderset.py::…` citations are recognized-but-skipped (+0); and `#"substring"` forms and `spec-NNN Decision N` forms are not citations to this gate at all (+0). 5 + 2 = 7, and 772 + 7 = 779. The two cookbook parentheticals this pass **deleted** sat next to citations it left in place, so nothing went to zero.

**Focused-scope choice.** `tests/mutations`, `tests/forms`, and `tests/orders` are the package mirrors of the four edited package modules; `examples/fakeshop/test_query/test_products_api.py` is the live `/graphql/` surface and is itself edited. It is included because the dispatch brief requires it, and because it is the file whose docstrings this pass rewrote — the one place a stray executable edit would show as a failure rather than as a diff.

#### Comment-and-docstring-only proof (executable-token identity)

Claimed mechanically per `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`. No `git checkout` / `git stash` / `git restore` / `git worktree` and no `git add` was used; three cohorts plus a spec-028 session are writing this tree.

The instrument tokenizes with `tokenize`, drops `COMMENT` / `NL` / `ENCODING`, drops every **statement-position** `STRING` (a docstring), keeps every non-statement-position string literal, and compares the remaining `(type, string)` sequence. It lives at `<scratchpad>/cohortB-027/tokid.py` (sha256 `bf22e10bdc42a92c8379731542317ab08a4179fead18a8e89e2e41784b707bca`).

**Two baselines, because `HEAD` is not "before this pass" for one file.** `orders/sets.py` already carried the spec-028 session's four hunks when this pass began. Both comparisons were run:

| File | vs `git show HEAD:<path>` | vs the pre-pass working-tree copy | Token count |
|---|---|---|---|
| `django_strawberry_framework/orders/sets.py` | IDENTICAL | IDENTICAL | 1286 |
| `django_strawberry_framework/mutations/fields.py` | IDENTICAL | (same as HEAD) | 835 |
| `django_strawberry_framework/mutations/resolvers.py` | IDENTICAL | (same as HEAD) | 3661 |
| `django_strawberry_framework/mutations/inputs.py` | IDENTICAL | (same as HEAD) | 2928 |
| `django_strawberry_framework/mutations/sets.py` | IDENTICAL | (same as HEAD) | 4514 |
| `django_strawberry_framework/forms/inputs.py` | IDENTICAL | (same as HEAD) | 1919 |
| `examples/fakeshop/test_query/test_products_api.py` | IDENTICAL | (same as HEAD) | 18581 |

The `orders/sets.py` HEAD comparison is the stronger of its two rows: it proves **both** sessions' edits to that file are jointly comment-only.

#### Challenge set: the verdicts were asserted before they were read

Eight mutations of one 58-token fixture. The expected verdict for each was written down before the instrument was run (`ASSERTED BEFORE READING: c1 c2 c3 DIFFERENT | c4 c5 IDENTICAL | c6 c7 c8 DIFFERENT | self IDENTICAL`). All eight matched.

| Case | Mutation | Asserted | Measured |
|---|---|---|---|
| c1 | operator flip, `if a > b:` -> `if a < b:` | DIFFERENT | DIFFERENT — divergence at index 40, `(55, '>')` -> `(55, '<')` |
| c2 | inserted statement, `total += 1` | DIFFERENT | DIFFERENT — 58 -> 62 tokens, divergence at index 38 |
| c3 | deleted statement, `total = a + b` removed | DIFFERENT | DIFFERENT — 58 -> 52 tokens, divergence at index 32 |
| c4 | docstring rewrite (module + function, two paragraphs) | IDENTICAL | IDENTICAL, 58 |
| c5 | comment rewrite (a citation appended) | IDENTICAL | IDENTICAL, 58 |
| c6 | **non-statement-position string inside a call** — `import_module("…forms.inputs")` -> `"…mutations.inputs"` | DIFFERENT | DIFFERENT — divergence at index 25 on the STRING token |
| c7 | non-statement-position string, a GraphQL query literal, `{ item { name } }` -> `{ item { id } }` | DIFFERENT | DIFFERENT — divergence at index 30 |
| c8 | non-statement-position string as a module-constant RHS | DIFFERENT | DIFFERENT — divergence at index 6 |
| self | file against itself | IDENTICAL | IDENTICAL, 58 |

c6 is the case the brief named as where a naive instrument silently passes a real change: a module-path string inside a call is not a docstring, and dropping every `STRING` token would have reported IDENTICAL. c7 and c8 extend the same probe to a query literal and to a module-level constant. The instrument distinguishes statement position from expression position, so all three land.

#### Wrapped-`#"` census (the mandatory post-condition)

A per-line scan flagging every `#"` with no closing `"` on the same line:

| Scope | Wrapped citations |
|---|---|
| each of this cohort's 7 files, individually | **0** |
| every `.py` file under `django_strawberry_framework/` | **0** |

The package-wide figure is 0 because cohort A discharged item 1 Form A's six sites; it is recorded here as an independent re-derivation of their result, not as this cohort's work. This pass introduced no wrapped citation: the three new `#"…"` forms (`#"is the Relay-spec signature"` x2 and `#"Works for both dict (iterates keys)"`) and the four new spec substrings all open and close on one line, and each was placed with that constraint driving the wrap point (the `Edge cases` substring was shortened from `Two mutations over one model share input types` to `Two mutations over one model` — still 1 hit — specifically so the whole reference fits one line).

#### Scratchpad-collision re-verification

Worker 0 reported that the shared scratchpad had silently overwritten one cohort's script. Actions taken and their outcome:

- **Integrity check of what had already been used.** This cohort's instrument was named `w2_token_identity_027.py` and its baselines lived under `head/` and `prepass/` with single-underscore path-flattened names; cohort A's copies in those same directories used double-underscore names, so no name collided. The instrument's contents were read in full and are byte-for-byte what this pass wrote. The pre-pass `orders/sets.py` copy was checked for the discriminating property that proves it is genuinely pre-pass: it carries the spec-028 session's hunks (`spec-028 DoD 4(c)` -> 2 hits) and **not** this pass's (`OrderSetMetaclass.__new__` -> 0 hits).
- **Moved to `<scratchpad>/cohortB-027/`**, instrument and baselines both.
- **Re-took every `HEAD` baseline** with `git show`, which is reproducible regardless of what happened in the scratchpad.
- **Re-ran the full challenge set from a freshly written fixture**, verdicts asserted before reading, and **re-ran the seven-file identity proof** with the verified instrument against the fresh baselines.

**No recorded figure changed.** The re-derived token counts (1286 / 835 / 3661 / 2928 / 4514 / 1919 / 18581) and all nine challenge verdicts are identical to the first run. The citation-gate counts, the comma gate, the pre-commit run, and the test run all come from repo scripts rather than the scratchpad and were unaffected; the citation gate and the test run were nonetheless re-run after the last docstring edit and returned 779 and 756-passed again.

### Failability proofs

None; this pass introduced no new boundary.

Discharged mechanically rather than on prose: the executable-token identity table shows the diff contains no statement, branch, guard, comparison, or raise for the mandatory floor to select.

### Hot-path budget

Not applicable; plan declares no hot path (`build-027-filters-0_0_8.md` `Hot-path declaration: none`).

### Floor verification

Not applicable; plan declares floor-verification scope none (`build-027-filters-0_0_8.md` `Floor-verification scope: none`).

### Implementation notes

- **The cookbook durability question: the reference IS fully durable, and the sanctioned form was already in the file.** The cookbook is not vendored — it is an external checkout at `~/projects/django-graphene-filters/`. But `scripts/check_citations.py` carries `django_graphene_filters/` in `UPSTREAM_PREFIXES` precisely so that `django_graphene_filters/orderset.py::AdvancedOrderSet.get_flat_orders` is a **recognized** citation form: the gate parses it, classifies it as upstream, and skips resolution rather than failing it. `docs/SPECS/spec-028-orders-0_0_8.md` uses that exact spelling throughout. And two of the four sites already carried the symbol citation on the line above the line number, so the line numbers were redundant, not load-bearing. Verdict: **no undurable reference in this cohort**, and no finding to record on that axis. The remaining fragility is different in kind and worth naming: an upstream symbol *rename* in a tree this repo does not own is invisible to every gate here. That is a property of citing an external tree at all, not of the form chosen, and the symbol form is strictly better than the line form under it (a rename is at least greppable; a line shift is not).
- **Two cookbook parentheticals were deleted rather than rewritten.** At `OrderSet.get_fields` and `OrderSet.get_flat_orders` the preceding line already read `` ``django_graphene_filters/orderset.py::AdvancedOrderSet.<method>`` ``. Replacing `(cookbook lines 265-285)` with a second spelling of the same target would have said it twice. Deleting the parenthetical leaves the durable citation as the only reference. The cost is a short residual line (`with the same two-condition cache write`, `with two adaptations:`); see the minimal-edit note below.
- **Minimal-edit discipline over tidiness, and why.** Four repaired sites leave a shorter-than-usual line rather than reflowing the surrounding paragraph. This follows the precedent `bld-slice-4-027-broken_substring_citations.md` recorded for the same reason: re-wrapping a comment this pass is not otherwise editing is exactly the mechanism that splits a citation across a line break, which is the defect class the cycle has already hit three times. Where a reflow was unavoidable (because the repaired reference no longer fit), it was bounded to the two or three lines of the same sentence and the wrapped-`#"` census was re-run afterwards. `orders/sets.py` got the strictest treatment of all: it is concurrently held, so every edit there was a single-hunk exact-string replacement, which is also what let both sessions' hunks coexist.
- **`Decision 15` was collapsed from two bare mentions to one carded mention** in `resolvers.py::authorize_or_raise`. The summary line was already ~103 characters; prefixing `spec-036` would have pushed it past the 110 E501 grace, and splitting the summary into a new paragraph would have added prose this pass has no mandate to add. The body sentence — which is where a reader actually needs the pointer — now carries `the spec-036 Decision 15 authorization-failure surface`. Net: one resolvable reference replaces two unresolvable ones.
- **Substring length was chosen against measured uniqueness, not by eye.** Every replacement substring was counted with `grep -cF` against its target spec before it was written: `Type identity and naming` 1, `Custom inputs follow the generated field-naming scheme` 1, `Two mutations over one model` 1, `is the Relay-spec signature` 1 (in `relay.py`), `Works for both dict (iterates keys)` 1 (in the cookbook's `orderset.py`).
- **Same-file test citations are spelled with the file name, not bare `::name`.** `test_products_api.py::test_x` is what `check_citations.py` can resolve (`candidate_paths` tries the citing file's own directory first) and it is the form the file already used once, at `test_uploads_api.py::test_multipart_create_uploads_real_files_over_http`. A bare `::test_x` matches no gate pattern.

### Notes for Worker 3

- **`orders/sets.py` is a shared file and the diff shows two sessions' work.** The four `Spec Decision N` / `Spec DoD 4(c)` -> `spec-028 …` hunks are the concurrent spec-028 session's, not this pass's; the four cookbook hunks are this pass's. `git diff HEAD -- django_strawberry_framework/orders/sets.py` shows both interleaved. Do not read the 028 hunks as this cohort's over-reach, and do not read this cohort's checklist tick on item 4 as a claim to have built them — the box is ticked because the contract landed in the tree, with the builder named.
- **The dispatch brief's site table was a sample, not a census, in this partition too.** It enumerated 10 sites; the census found 15 raw line refs (4 cookbook, not 3; plus 4 raw spec line numbers in `mutations/sets.py` the table did not mention), 6 genuinely uncarded `Decision N` sites in `mutations/`, and 3 dead `finding-#1` provenance mentions. The instrument that finds the spec-line-number class is `grep -rniE '\b(line|lines|ln)[ .:#]?[0-9]{1,4}\b'` — note that a sweep for `path:NN` colon syntax returns **0** in this partition, so the colon form alone would have found nothing at all.
- **Five of the fifteen line numbers were already rotted, and two of those five point at a materially wrong target.** The full accounting is in `### Per-site before / after`. The two worst are `test_products_api.py`'s `(mirror line 528)` and `(mirror line 694)`, each landing on an unrelated test. That is the class actively decaying, not hypothetically.
- **Two uncarded `Decision N` sites resolved to a different spec than their nearest named antecedent** — `resolvers.py`'s two `Decision 9` refs sit beside `spec-035` but mean `spec-036`, and `sets.py::make_declaration_registry`'s `Decision 13` sits inside a `spec-036`-naming docstring but means `spec-038`. In both cases the spec the reader would infer has a **Version bumps** decision at that number. A reviewer re-deriving these should read the decision headings, not the proximity.
- **One `Decision 10)` fragment in `mutations/sets.py` was deliberately left alone**: it is the continuation of a `ConfigurationError` f-string, i.e. executable, and it is already carded across its two fragments. `grep` for bare `Decision N` will surface it; it is not a miss.
- No shadow file was used. `scripts/review_inspect.py` was **skipped**: this pass adds no logic, and the helper's `<stem>.stripped.py` replaces every comment and string-literal token with `...`, so its output is byte-identical before and after. The token-identity table is the mechanical evidence for that skip. Same recorded skip and reason as Slices 2 and 4.

### Notes for Worker 1 (spec reconciliation)

Five items. None requires a `spec-027` edit; four concern surfaces fenced from this cohort and one is an artifact correction this pass may not make in place.

- **`docs/builder/build-027-filters-0_0_8.md`, `### Re-derived populations, for the record`, the sentence beginning "Item 6 uncarded:".**
  - Current wording: "Item 6 uncarded: `orders/sets.py` **94, 179, 312** (cookbook ranges), `mutations/fields.py:32` and `mutations/resolvers.py:1150` (both `` (``relay.py`` line 287) ``), `test_products_api.py` **2948, 2984, 3015, 3051, 3098**."
  - Recommended replacement: "Item 6 uncarded, re-censused by cohort B: `orders/sets.py` **94, 179, 256, 312** (four cookbook refs, not three — `256` spells it `Cookbook line 279-280`), `mutations/fields.py:32` and `mutations/resolvers.py:1150` (both `` (``relay.py`` line 287) ``, and the number is ROTTED — `relay.py:287` is inside `decode_model_global_id`'s docstring, not the node field), `mutations/sets.py` **503, 508, 671, 1339** (raw *spec* line numbers: `Decision 6 line 334`, `Edge cases line 509` x2, `Decision 6 line 336`; three of the four are rotted), `test_products_api.py` **2948, 2984, 3015, 3051, 3098** (of which `3051` and `3098` are rotted onto the wrong test). Total **15**, not 10."
  - Reason: the enumerated 10 was a sample. The undercount is systematic, not incidental: the brief's own instrument searched for the phrase `line NNN` next to a *path*, and the `mutations/sets.py` class spells it next to a *spec Decision* instead. A worker re-running the brief's spelling reproduces the blind spot.
- **`docs/builder/build-027-filters-0_0_8.md`, the cohort-B row of the `### Catalog-discharge cohorts` partition table.**
  - Current wording: the row lists `orders/sets.py` in cohort B's partition and lists "4's `orders/sets.py` sites" among its catalog items, while the paragraph above fences only `orders/base.py` and `orders/inputs.py` as spec-028-held.
  - Recommended replacement: add to the blocked-by-concurrent-work paragraph: "`orders/sets.py` went baseline-dirty **after** dispatch — the spec-028 session took it and discharged item 4's three `Spec Decision N` sites plus a fourth `Spec DoD 4(c)` site there. Cohort B's cookbook sites in the same file were built anyway, on distinct lines, by exact-string replacement; both sessions' hunks coexist in the tree. Item 4's `orders/sets.py` half is discharged, by the 028 session."
  - Reason: the partition was declared disjoint and is not, for one file. The collision was benign here — different lines, different defect class, no revert — but the plan currently records cohort B as the owner of work another session did, which is the kind of mis-attributed ownership a later audit cannot reconstruct.
- **`django_strawberry_framework/relay.py`, `DjangoNodeField`'s `_resolve` — a naming hazard, not a defect.**
  - Current situation: the package contains **two** modules a reader can call `relay.py` — `django_strawberry_framework/relay.py` (which defines `DjangoNodeField`) and `django_strawberry_framework/types/relay.py` (which does not). The rotted `(``relay.py`` line 287)` pair was ambiguous on both axes at once: wrong number, and a basename that resolves to two files. `scripts/check_citations.py` accepts a bare basename and resolves it against several roots, so `relay.py::DjangoNodeField` passes today.
  - Recommendation: no edit requested in this cohort. Recorded because the next worker to cite either module by basename is one rename away from a silent mis-resolution, and because it explains why this pass's replacement names a **symbol** rather than the path alone.
- **Three dead `finding-#1` references were removed, and nothing in the repo defines the term.**
  - Current wording (before this pass): `resolvers.py::_invalid_lookup_id_error` and two `test_products_api.py` tests carried `(spec-036 Decision 10 / finding-#1)`.
  - Recommendation: no spec edit. Recorded so that if `spec-036` is ever reconciled and a reviewer looks for the finding this hardening answered, the answer is that the id resolved nowhere in the tree at the time it was removed and the surviving contract is `spec-036` Decision 10 (which does carry the wrong-model / pre-lookup-rejection contract — verified by reading it).
- **`docs/SPECS/spec-036-mutations-0_0_11.md` needs no change, but its `## Edge cases and constraints` section is a citation magnet with no stable anchor.** Four references in this partition pointed into it, all by line number, and two of the six lines between the cited number and the real bullet are other bullets. The repaired form cites a bolded bullet lead-in (`#"Two mutations over one model"`), which is stable under a reword of the bullet's body but not under a reword of its lead-in. If Worker 1 is editing that section for any other reason, the four citing sites are `mutations/sets.py` (`_shape_build_cache` comment x1, `_materialize_input_for` comment x1) and `_validate_input_class` / the `Decision 6` pair.

### Deliberately not done

- **`mutations/inputs.py` and `forms/inputs.py`: no edit.** Censused for all three classes; clean. `forms/inputs.py:93`'s bare `Decision 7 P2` is a line-wrap continuation of `(spec-038` and is already carded.
- **The `ConfigurationError` f-string fragment in `mutations/sets.py::_validate_relation_override_types`.** Executable; out of scope by the pass's hard constraint; already carded across fragments.
- **"The headline slice invariant" in `test_products_api.py::test_create_item_via_form_relation_id_for_hidden_category_is_field_error`.** Names a *spec* slice, which `AGENTS.md` rule 26 sanctions as a concept, and does not name a build round or pass. Item 8 is scoped to *unambiguous* build provenance, and this is ambiguous. Left, and recorded rather than guessed.
- **The short residual lines left by four repairs.** Reflowing them means re-wrapping comments this pass is not otherwise editing. See `### Implementation notes`.
- **Item 4's `orders/sets.py` sites.** Already discharged in the tree by the concurrent spec-028 session; verified present, not duplicated, not reverted.
- **Cohort A's / C's / D's files.** Not touched, not read for defects beyond the one package-wide wrapped-`#"` census reported above as an independent re-derivation.

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
