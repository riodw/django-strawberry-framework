# Build: Catalog cohort E — wrapped `#"substring"` citations OUTSIDE the package (027)

Spec reference: `docs/SPECS/spec-027-filters-0_0_8.md` owns the catalog this cohort discharges (item 1 Form A, the two sites outside the package fence), but neither repaired citation points at spec-027. Both name `django_strawberry_framework/optimizer/walker.py`, whose contract is `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` — `### Decision 8 — strictness-mode wiring for connection paths` (the resolver-key parity the `tests/test_relay_connection.py` site asserts) and `### Decision 6 — fallback shapes: sidecar input, divergent aliases, hints, and scalar-only connections` (the unresolved-field skip the `examples/fakeshop/apps/kanban/schema.py` site cites). The item-8 removals discharge the same spec's `## Revision history` Revision 3 finding (4), "production/test comments no longer cite the per-cycle review artifact".
Status: final-accepted

## Plan (Worker 1)

### Planning lives in the build plan; this cohort had no Worker 1 pass

The contract is [`build-027-filters-0_0_8.md`][plan] `### Catalog-discharge cohorts (added 2026-08-20, post-commit 8a9840dc)`, extended by the maintainer's cohort-E dispatch: item 1 Form A's **two sites outside the package**, which the catalog's package-only census could not see, plus item 8 scoped to this cohort's own two files. Worker 2 re-derived the population and chose the repair text per site; the fence came from the dispatch.

**Ownership partition (declared, disjoint):** `tests/test_relay_connection.py`, `examples/fakeshop/apps/kanban/schema.py`, plus this artifact. Cohorts A (complete), B, C and D and an unrelated spec-028 session ran concurrently; nothing outside the partition was written or reverted.

**The `### Dispatched sites checklist` below was authored by Worker 2**, because the cohort has no Worker 1 planning pass to author it. Flagged for Worker 1's audit: the boxes quote the dispatch's own site table plus the item-8 scoping, and every tick is re-derivable from `### Per-site determinations` and `### Item 8`.

### DRY analysis

Not applicable, stated plainly rather than skipped silently: the diff contains no executable statement, no helper, no constant, no branch, and no test. There is nothing to share, extract, or de-duplicate — `### Executable-token identity` is the mechanical proof of that, not a claim.

One near-duplication was considered and deliberately left alone. Both repaired citations name the same file (`walker.py` in the test, `optimizer/walker.py` in the example) and the two spellings are **not** unified. Unifying them would be cleanup outside the slice, and both resolve: `scripts/check_citations.py::candidate_paths` resolves a citation's file half through a suffix index, and `walker.py` is a unique suffix in the corpus (`tests/optimizer/test_walker.py` contributes the suffixes `test_walker.py`, `optimizer/test_walker.py`, `tests/optimizer/test_walker.py` — never `walker.py`). Each file keeps its own established idiom.

### Dispatched sites checklist

- [x] `tests/test_relay_connection.py:2591` `` (``walker.py::_plan_connection_relation`` #"resolver_key(type_cls, `` — wrapped
- [x] `examples/fakeshop/apps/kanban/schema.py:359` `` # property and skips it before the hint dispatch (``optimizer/walker.py`` #"if `` — wrapped
- [x] Re-derive the full repo-wide census over `tests/`, `examples/`, `scripts/` and everything else carrying `.py` outside the package; report the real number rather than assuming two is complete
- [x] Item 8, scoped to these two files only: unambiguous build-process provenance in comments (review-round ids, slice/pass names, cycle names)
- [x] Postcondition measured, not assumed: the census returns **0** in this cohort's files after editing, with a control run proving the instrument still finds the originals

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --porcelain` and in `git diff` against `git show HEAD:<path>` copies held outside the repo. `git diff --stat` reads **16 insertions, 16 deletions** across the two files; every hunk is comment or docstring text.

- `tests/test_relay_connection.py` — six hunks. One repairs the wrapped citation in `test_strictness_silent_when_planned`'s docstring (retargeted symbol, truncated substring, reflowed onto one line). Five discharge item 8: `test_generated_name_graphql_camel_collision_raises`, `test_relation_connection_stale_after_no_error`, `test_relation_connection_has_next_page_when_edges_unrequested`, `test_fast_path_non_pk_ordering_applies_explicit_deterministic_order_by`, `test_strictness_silent_no_optimizer` (the sixth provenance id sat inside the citation hunk, so it rides there).
- `examples/fakeshop/apps/kanban/schema.py` — one hunk in `CardType`'s `LIMITATION` comment block: the bare-path citation promoted to `path::Symbol`, its substring retargeted (it resolved to **3**, not 1), and the whole `#"..."` reflowed onto one line.

**Everything else in `git status --porcelain`, classified. Nothing was touched or reverted.** The before/after status files differ by exactly three lines: this cohort's two files, and cohort C's artifact appearing.

| Path(s) | Owner |
|---|---|
| `tests/test_relay_connection.py`, `examples/fakeshop/apps/kanban/schema.py`, this artifact | **this cohort** |
| `django_strawberry_framework/consumers.py`, `routers.py`, `filters/factories.py`, `types/finalizer.py`, `types/relay.py`, `docs/builder/bld-slice-6-027-wrapped_citations.md` | cohort A (complete before this pass began) |
| `mutations/fields.py`, `mutations/resolvers.py`, `mutations/sets.py`, `orders/sets.py`, `examples/fakeshop/test_query/test_products_api.py`, `docs/builder/bld-slice-7-027-raw_line_refs.md` | cohort B |
| `orders/__init__.py`, `orders/factories.py`, `utils/inputs.py`, `optimizer/extension.py`, `rest_framework/{resolvers,sets,serializer_converter}.py`, `docs/builder/bld-slice-8-027-decision_attribution.md` | cohort C (its artifact appeared mid-pass) |
| `docs/SPECS/spec-055-search_fields-0_1_2.md`, `docs/builder/bld-slice-9-027-spec_055_refs.md` | cohort D |
| `docs/builder/build-027-filters-0_0_8.md` | Worker 0 |
| `orders/base.py`, `orders/inputs.py`, `types/base.py`, `docs/SPECS/spec-028-orders-0_0_8.md`, `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md`, `docs/builder/bld-slice-{1,2}-028-*`, `build-028-*`, `examples/fakeshop/apps/library/orders.py`, `examples/fakeshop/test_query/test_library_api.py`, `tests/orders/*`, `tests/test_registry.py` | the concurrent spec-028 session, baseline-dirty per the plan's declaration and `AGENTS.md` rule 34 |

Both of this cohort's files were **clean against `HEAD`** when the pass began (`cmp` against `git show HEAD:<path>`, two for two), so one baseline suffices and every proof below is against `HEAD` directly.

### Tests added or updated

None. The diff adds no executable statement and no contract, so there is nothing new for a test to pin. The existing suite is the regression check and was run (`### Validation run`).

### The repo-wide census, and its real number

The catalog recorded item 1 Form A as **six sites, package-wide**. That figure is correct for the package and incomplete for the repo, because the census that produced it globbed `django_strawberry_framework/**/*.py` only. The identical per-line census extended to **every tracked `.py` file in the repo** returns **8**.

| Scope | Files | Wrapped citations |
|---|---|---|
| `django_strawberry_framework/` (the catalog's scope) at `HEAD` | 108 | **6** — cohort A's, all repaired before this pass began |
| **Every tracked `.py` file** at `HEAD` (`git archive HEAD` into a scratch tree) | **425** | **8** |
| The 8 minus the package's 6 — this cohort's population | 2 | **2** |

So **two is complete for `.py`**, and it was measured rather than accepted: nothing under `scripts/`, `examples/fakeshop/` outside the one kanban file, `line_count.py`, the migration trees, or the app test trees carries a wrapped citation. There are also **no `.pyi` files** in the repo (`git ls-files '*.pyi'` → 0), so the `.py` glob is the whole Python surface.

**A population the dispatch did not name, recorded rather than repaired: 26 wrapped citations in tracked `.md`.** Same instrument, `git ls-files '*.md'` (394 files): 14 in `docs/SPECS/`, 5 in `docs/SPECS/appx/`, 6 in `docs/builder/`, 1 in `docs/builder/DONE/`. These are out of this cohort's fence (spec files belong to their own cards, `bld-*.md` are per-cycle artifacts that close with their cycle) and out of the gate's fence too — `scripts/check_citations.py`'s module docstring states "`docs/` is deliberately out of scope". One of the 26 is a false positive of a new flavour worth naming: `docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md` line 883 carries `` git grep 'spec-<NNN> #"' `` — a **grep pattern for this very defect class**, not a citation. Routed to `### Notes for Worker 1`.

#### The instrument, and the two false-positive flavours it is built to survive

Per-line scan of each file; an occurrence is the two-character sequence `#"`; an occurrence is WRAPPED when no `"` appears after it on the same line. Line-scoped **on purpose** — that is exactly the blindness being measured, since `scripts/check_citations.py`'s `CITATION_RE` matches `path::Symbol` within one line and never looks at `#"` at all.

Classification order is load-bearing and was corrected mid-pass after a first version misfiled a real citation:

1. **Closed on the same line → fine.** This test runs *first*, because a citation opened after `(` is still a citation. A version that filtered on the preceding character first misfiled `django_strawberry_framework/consumers.py:1367` (`(#"join(value) for name")`) as a false positive when it is a perfectly closed citation.
2. **Unclosed, and the character before the `#` is not whitespace → string-literal false positive.** A rule-27 citation always has whitespace (or nothing) before its `#`. This excludes both flavours in one rule: `"#"` (preceded by `"`) and `"##"` (preceded by `#`) — and the second is why the naive filter reports `scripts/build_kanban_md.py:307` twice, once in each bucket. Four such literals exist repo-wide (`line_count.py:63`, `scripts/build_kanban_md.py:307`, `scripts/prove_failability.py:500` and `:501`).
3. **Otherwise → WRAPPED.**

The instrument deliberately flags a `#"` at the *start* of a comment line, which a resolver that strips leading `#` markers misses. Script under this session's private scratchpad subdirectory, outside the repo.

### Per-site determinations

Every substring was re-derived against the named target at its current state, **before** editing, with `grep -oF <substring> <target> | wc -l` — occurrences, not matching lines. Neither site was a plain "resolves, reflow only": one was **mis-paired** and one was **non-unique**, and both defects were invisible for the same reason the wrap is.

| # | Site | Cited at `HEAD` | Hits | Determination | After |
|---|---|---|---|---|---|
| 1 | `tests/test_relay_connection.py::test_strictness_silent_when_planned` | `walker.py::_plan_connection_relation` + `#"resolver_key(type_cls, relation_field_name, runtime_path)"` | **1** | **mis-paired** — the substring resolves uniquely but lies in a DIFFERENT symbol | `` ``walker.py::_resolver_identities_for #"resolver_key(type_cls, relation_field_name"`` ``, **1** hit, substring inside the named symbol |
| 2 | `examples/fakeshop/apps/kanban/schema.py` `CardType` `LIMITATION` block | `optimizer/walker.py` (bare path, no symbol) + `#"if django_field is None"` | **3** | **non-unique**, and the wrong rule-27 form for a line inside a function | `` ``optimizer/walker.py::_walk_selections #"snake_case(sel.name), None"`` ``, **1** hit |

#### Site 1 — the substring resolves, but not inside the symbol the citation names

`resolver_key(type_cls, relation_field_name, runtime_path)` occurs exactly **once** in `django_strawberry_framework/optimizer/walker.py`, so a hit-count check alone would have graded this "resolves — reflow only". It does not resolve where the citation says it does. The one occurrence is inside the docstring of `_resolver_identities_for`; `_plan_connection_relation` is a fourteen-line delegator whose entire docstring is "Delegate one normalized nested connection and atomically merge its result." and which never spells the key shape at all — it passes `resolver_identities_for=_resolver_identities_for` down to `_plan_nested_connection_relation`. `path::QualifiedName #"unique substring"` names a line **inside** that symbol, so the pairing was false.

Retargeting to `_resolver_identities_for` is not a loss of the connection-specific claim, because that is precisely what its docstring documents: it is "Shared by the list-relation walk (`_walk_selections`, keyed on the Django field name) and the nested-connection planner (`_plan_connection_relation`, keyed on `relation_field_name` ...)". The docstring text now keeps `_plan_connection_relation` as the caller ("reached from ``_plan_connection_relation``"), so no information left the file — it moved out of the citation, where it was wrong, into the prose, where it is right.

**The substring is truncated, and the truncation was forced by the one-line requirement.** Measured, not guessed: with the file's own citation idiom (the whole `path::Symbol #"substring"` inside one double-backtick span, the precedent this file already sets at `` (``connection.py::_consume_fallback #"return _attach_count_async("``) ``), the full 56-character shape lands the line at **106** columns. Three candidates were measured for uniqueness in `walker.py`:

| candidate | length | hits | verdict |
|---|---|---|---|
| `resolver_key(type_cls, relation_field_name, runtime_path)` | 56 | **1** | unique, but 106 columns — rejected |
| `resolver_key(type_cls, relation_field_name` | 41 | **1** | **chosen**, 91 columns |
| `resolver_key(type_cls,` | 22 | **2** | fails uniqueness — rejected on measurement |

Two shapes that would have fit were rejected on principle rather than length. Splitting the path onto one line and the `#"..."` onto the next fits trivially and is **the defect itself, relocated** — a line-scoped instrument would then see the path on one line and the substring on another. Dropping the substring entirely and citing `walker.py::_resolver_identities_for` alone also fits, and was the closer call: the prose two lines above already quotes the full shape verbatim, so the substring is partly redundant. It was kept because a substring pins a *sentence* and a symbol pins only a *function*, and a reword inside a 30-line docstring is exactly what the next cycle needs to be able to detect.

E501 is *not* the constraint here and is not being leaned on: `pyproject.toml` `[tool.ruff.lint.per-file-ignores]` disables E501 for both `tests/**/*.py` and `examples/**/*.py`, and `scripts/check_trailing_commas.py` uses `line_length()` only to decide whether a *construct* fits inline, never to flag a comment. The 99-column target is the surrounding idiom, honoured deliberately — this file already carries three lines past it (up to 113), and adding a fourth to carry a citation would make the citation the file's widest line.

#### Site 2 — three hits, and the wrong rule-27 form

`if django_field is None` occurs **3** times in `walker.py` (lines 509, 1136, and inside `if django_field is None or django_field.is_relation:` at 1155), so rule 27's uniqueness fails. The two bare occurrences are also **byte-identical lines at identical indentation**, which means no extension *within the line* can ever separate them — the usual "extend until unique" remedy is unavailable here, not merely unattractive.

Separately, the citation used the module-level form (`path #"substring"`) for a line that is inside a function, so it named no symbol and the gate had nothing to resolve.

The site the comment actually means was traced, not inferred. The kanban `dependencies` / `dependents` fields are Card **properties**: `field_map` has no key for them, `_field_by_graphql_name` returns `None`, and `_walk_selections` line 507 leaves `django_field` as `None` — after which the `if django_field is None:` branch falls through to its `continue`, while the hint dispatch (`hint = hints_map.get(django_name)`) sits ~45 lines further down. So the skip does precede the hint dispatch, exactly as the comment claims, and `_walk_selections` is the symbol.

Two unique anchors were available and both measured **1** hit:

| candidate | length | hits | verdict |
|---|---|---|---|
| `snake_case(sel.name), None` | 26 | **1** | **chosen** — the code that leaves `django_field` unresolved |
| `Neither namespace matched` | 25 | **1** | rejected: it is a *comment* in the target, so it rots under any rewording of `walker.py`'s own comments |
| `django_name, django_field = snake_case(sel.name), None` | 53 | **1** | rejected on width — 106 columns |

Preferring executable text over comment text as an anchor is the general lesson here: a citation into a comment is a citation into the most-edited lines in the file.

### Item 8 — build-process provenance in these two files: population **6**, all in the test file

Cohort A measured 0 in its five files and the dispatch warned against forcing a finding. This cohort measured **6**, and every one is on the standing ban list rather than a judgement call. Three greps over both files (dispatch vocabulary, narration vocabulary, artifact-path vocabulary) plus a targeted sweep for severity labels and round ids:

| # | Site | At `HEAD` | Class | After |
|---|---|---|---|---|
| 1 | `test_generated_name_graphql_camel_collision_raises` | `(Revision 3 P3)` | review-round id + severity/finding label | dropped |
| 2 | `test_relation_connection_stale_after_no_error` | `(Revision 2 P1)` | same | dropped |
| 3 | `test_relation_connection_has_next_page_when_edges_unrequested` | `Revision 6 P3:` leading the summary | same | replaced by the claim it labelled |
| 4 | `test_fast_path_non_pk_ordering_applies_explicit_deterministic_order_by` | `(the deterministic regression, Revision 3)` | review-round id | `(the deterministic-order regression)` |
| 5 | `test_strictness_silent_no_optimizer` | `Implementation step 5`, `pre-card behavior` | build-plan step id; planning residue | restated as the invariant |
| 6 | `test_strictness_silent_when_planned` | `Implementation step 2` | build-plan step id | dropped (rides the citation hunk) |

`examples/fakeshop/apps/kanban/schema.py`: **0**. Nothing was rewritten there.

**Why these six are unambiguous, established by measurement before editing.** `Implementation step N` resolves to nothing in any spec: grepping `.py` and `.md` repo-wide for the phrase, excluding `docs/builder/bld-*` / `build-*` / `DONE/`, returns exactly these two test-file sites plus `docs/builder/ARTIFACT.md:31` `### Implementation steps` and `docs/builder/worker-1.md:41`. It cites a **build-artifact template section**, so a reader of the published package cannot resolve it at all. `Revision N` *is* real spec vocabulary — `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` `## Revision history` runs Revision 1 through 5 — but none of the four sites names a card, so "Revision 3" is unresolvable in the same way, and `P1` / `P3` are per-round finding labels that appear nowhere in spec-033 (`grep -E '\bP[0-9]\b'` returns one line, and it is spec-033 citing *spec-032*'s Revision 6 P2, with the card named). Spec-033's own Revision 3 finding (4) is "**doc-reference hygiene** — production/test comments no longer cite the per-cycle review artifact", so this discharge finishes a job that card started and left partly undone.

**Three candidate classes were examined and deliberately kept**, because the fence is "unambiguous build-provenance only" and each of these is contract vocabulary a reader can resolve:

- **`workstream B` / `workstream C` / `workstream D`** (8 occurrences in the test file). Not a review round, slice, pass, or cycle: these are the optimizer's own topic codes, cross-referenced from live package source (`optimizer/walker.py` names "connection window rigor, workstream D - the strawberry-django #697 bug class" in the very branch site 2 now cites). Cross-referenced rule names are on the standing KEEP list. They do resolve nowhere in `docs/` — routed to `### Notes for Worker 1` rather than deleted here, because deleting a vocabulary the package's own comments use would leave the package half-consistent.
- **`the M1 non-queryset GraphQLError`** (1 occurrence). A cross-referenced rule name, and verified as such rather than assumed: `django_strawberry_framework/connection.py` line 1356 says "the connection field's M1 rule raises a ``GraphQLError``" and line 1139 "a spurious M1-guard raise". Two modules share the name, so it is a contract pointer.
- **Contrast and behaviour-change prose** — `historically fell back per-parent`, `used to pass through unflipped`, `The walker no longer plans the shape`, `what the fix uniquely adds`, `the regression signal`, `Byte parity with the`. The dispatch states contrast prose is not a member, and each of these states a *behaviour*, which is what a test docstring is for.

`spec-033 Decision 4 step f / Decision 8` was likewise kept: a spec Decision pointer with the card named is the canonical KEEP case.

### Validation run

Every command from the repository root. `pre-commit` is not on `PATH`; the config header names `uvx`. No `--cov*` flag was used anywhere.

| Check | Command | Result |
|---|---|---|
| Format (scoped, never `.`) | `uv run ruff format tests/test_relay_connection.py examples/fakeshop/apps/kanban/schema.py` | `2 files left unchanged` |
| Lint (scoped) | `uv run ruff check --fix <the same two>` | `All checks passed!`, exit **0** |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check <the same two>` | silent, exit **0** |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 780 citations resolve (703 in 422 .py files, 77 in KANBAN.md).` exit **0** |
| Hooks | `uvx pre-commit run --files <the same two>` | all five hooks **Passed** (kanban tracked path constants; source layout; ruff format; ruff check; citations resolve) |
| Churn classification | `git status --porcelain` before and after, diffed | three added lines: this cohort's two files + cohort C's artifact. Nothing else, nothing reverted |
| Focused tests | `uv run pytest tests/test_relay_connection.py examples/fakeshop/test_query/test_kanban_api.py examples/fakeshop/test_query/test_kanban_mutations_api.py examples/fakeshop/apps/kanban/tests examples/fakeshop/tests/test_inspect_django_type.py --no-cov -q` | **320 passed in 18.17s** |
| Line width | `awk 'length>99'` over the edited regions | widest line written is **91** (the site-1 citation); site 2's widest is **84** |

**On the citation gate's count, and this cohort's own contribution to it.** 780 / 703 is 8 higher than the 772 / 695 cohort A recorded, and the global delta cannot be attributed by subtraction while four cohorts write the same tree. Measured directly instead, per file against `git show HEAD:<path>`:

| File | `path::Symbol` at `HEAD` | now | `#"` at `HEAD` | now |
|---|---|---|---|---|
| `tests/test_relay_connection.py` | 6 | **6** | 2 | **2** |
| `examples/fakeshop/apps/kanban/schema.py` | 1 | **2** | 1 | **1** |

This cohort's contribution is therefore **exactly +1** `path::Symbol` and **0** `#"` — the +1 being site 2's promotion from a bare `path` citation the gate could not see to a `path::Symbol` it can. Site 1's symbol changed identity without changing the count. The other +7 belong to the three concurrent cohorts.

**Focused-scope justification, from the importing surface.** `grep -rln` over `tests/` and `examples/` for `kanban.schema` / `apps.kanban.schema` names four consumers: `examples/fakeshop/config/schema.py`, `examples/fakeshop/schema_reload.py`, `examples/fakeshop/tests/test_inspect_django_type.py`, and `examples/fakeshop/test_query/test_kanban_api.py`. The scope above takes the two live kanban surfaces, the whole `examples/fakeshop/apps/kanban/tests/` package, the type-introspection consumer, and the edited test file itself. It deliberately excludes `tests/orders/`, `tests/test_registry.py`, `examples/fakeshop/test_query/test_library_api.py` and `test_products_api.py`: all four are baseline-dirty with concurrent sessions' work, so a failure there would be unattributable, and nothing in this diff touches an order, registry, library or products surface. The recurring fakeshop schema-registry cross-test pollution is why the kanban live tests were run together with the introspection consumer rather than singly.

### Census, precondition, postcondition, and control

| Run | Scope | Wrapped citations |
|---|---|---|
| Precondition, every tracked `.py` at `HEAD` | `git archive HEAD` scratch tree, 425 files | **8** — the 6 the catalog tabled, plus this cohort's 2 |
| Precondition, working tree before any edit | repo, 565 `.py` files | **2** — cohort A's 6 already repaired |
| Postcondition, this cohort's files alone | 2 files | **0** |
| Postcondition, repo-wide | 565 `.py` files | **0** |
| **Control** | the two `git show HEAD:` copies, re-scanned in the same run after the edits | **2** — the instrument still finds both originals |

The control row is the point: a postcondition of 0 from an instrument that has silently stopped matching is worthless, so the same script was pointed at the pristine copies afterwards. **This pass's own reflow created no new wrapped citation** — that is the repo-wide 0, measured, not assumed. The 565-vs-425 file-count gap is untracked build detritus (`__pycache__`-adjacent scratch and `.venv`-excluded paths are skipped; the remainder are untracked local files), and it only ever *adds* candidate files, so it cannot hide a wrapped citation in a tracked one.

### Post-edit resolution sweep

Every citation in the two files, re-resolved by occurrence count against the target its own text names.

| File | `path::Symbol` | resolving | `#"` | resolving to exactly 1 | wrapped |
|---|---|---|---|---|---|
| `tests/test_relay_connection.py` | 6 | 6 | 2 | 2 | 0 |
| `examples/fakeshop/apps/kanban/schema.py` | 2 | 2 | 1 | 1 | 0 |

The untouched `#"` citation in the test file was checked rather than assumed: `` (``connection.py::_consume_fallback #"return _attach_count_async("``) `` at line 2017 — `_consume_fallback` is defined at `connection.py` line 715 and `return _attach_count_async(` occurs **1** time in that file. It is also the idiom precedent site 1's repair follows.

### Failability proofs

None; this pass introduced no new boundary.

Discharged mechanically rather than on prose: the executable-token identity below shows the diff contains no statement, branch, guard, comparison, or `raise` for the mandatory floor to select.

### Executable-token identity, and the challenge set that earns it

Instrument written for this cohort, not reused: `tokenize` each file; drop `COMMENT`, `NL`, `NEWLINE`, `INDENT`, `DEDENT`, `ENCODING`, `ENDMARKER`; drop every `STRING` token lying inside a **statement-position** string expression, located by `ast` as a bare `ast.Expr` whose value is a `str` constant and dropped across the whole `Expr` span so implicit concatenation is covered; compare the remaining `(type, string)` sequences. A `STRING` in any other position — a call argument, an assignment RHS, a dict key or value, a decorator argument — is **kept**. No `git checkout` / `git stash` / `git restore` / `git worktree` was used.

| File | Verdict vs `HEAD` | Exec tokens |
|---|---|---|
| `tests/test_relay_connection.py` | **IDENTICAL** | 11990 |
| `examples/fakeshop/apps/kanban/schema.py` | **IDENTICAL** | 5654 |

**Challenge set.** Six mutations, each applied to a copy held outside the repo (so no mutation ever sat in a tree four other sessions are writing), each anchor asserted unique and each mutation's landing confirmed by byte comparison before the instrument ran, and each **expected verdict written into the harness source before the verdict was read**.

| Case | Mutation | Asserted | Measured |
|---|---|---|---|
| 1 — operator flip | test file, `"Unplanned N+1" in m]) == 1` -> `>= 1` | DIVERGENT | **DIVERGENT**, index 5500: `(OP, '>=')` != `(OP, '==')` |
| 2 — inserted statement | `schema.py` + `_CHALLENGE_E_INSERTED = 1` above `class CardType` | DIVERGENT | **DIVERGENT**, index 785 |
| 3 — deleted statement | `schema.py` - `filterset_class = filters.CardFilter` | DIVERGENT | **DIVERGENT**, index 886: `'orderset_class'` != `'filterset_class'` |
| 4 — docstring rewrite | `schema.py` module docstring replaced wholesale | IDENTICAL | **IDENTICAL** |
| 5 — comment rewrite | `schema.py` `LIMITATION` comment line replaced wholesale | IDENTICAL | **IDENTICAL** |
| 6 — **non-statement-position string** | `schema.py` `optimizer_hints` key `"items"` -> `"itemsX"` | DIVERGENT | **DIVERGENT**, index 899: `'"itemsX"'` != `'"items"'` |

Six for six. Case 6 is the silent hole: an `optimizer_hints` key is validated against `model._meta.get_fields()` at class-build time (the very mechanism site 2's comment cites), so changing it is a real behaviour change — and a filter that drops *every* `STRING` reports it as identical. Cases 4 and 5 are what stop the instrument from being vacuously strict. The pair is why the verdict table above is evidence rather than an assertion.

### Hot-path budget

Not applicable; the plan declares no hot path, and executable-token identity means nothing executes differently.

### Floor verification

Not applicable; the plan declares floor-verification scope none, and a comment-only diff touches no Django / Strawberry / channels seam.

### Implementation notes

- **A hit count of 1 is not proof a citation resolves.** Site 1's substring occurred exactly once and the citation was still false, because the occurrence was in a different symbol than the one named. `path::Symbol #"substring"` carries two claims and the count only checks one; the second — *is the substring inside that symbol* — has to be checked by locating the hit's enclosing `def`. This is the determination class neither the catalog nor cohort A's three-outcome scheme (resolves / zero-hit / multi-hit) has a slot for, and it is invisible to every instrument in the repo.
- **Two byte-identical lines cannot be separated by extending the substring.** Site 2's `if django_field is None:` appears at the same indentation twice, so "extend until unique" was structurally unavailable and a *different* anchor was mandatory. Worth recording because the dispatch's remedy list reads as though extension always works.
- **Prefer executable text over comment text as an anchor.** Both of site 2's unique candidates resolved once; the code line was chosen because a citation into a comment is a citation into the file's most-edited lines.
- **The citation goes inside one backtick span, matching each file's own idiom.** `tests/test_relay_connection.py` already writes `` (``connection.py::_consume_fallback #"return _attach_count_async("``) ``, so both repairs use that shape. It is also shorter than backticking the path separately, which is what let site 1 fit under 99 columns at all.
- **The one-line requirement is what bounds the substring, and it was allowed to bind.** Site 1's ideal 56-character anchor was truncated to 41 rather than split across lines or pushed to 106 columns. Splitting is the defect relocated; widening makes the citation the file's widest line. Both alternatives were rejected explicitly rather than by default.
- **Reflow was minimal but unavoidable.** A wrapped citation cannot be repaired without moving a line break, so each hunk re-wraps only its own paragraph. The item-8 hunks needed no reflow except where dropping a label left a short line (case 3), and case 5's rewrite restates the invariant with the same claim ("byte-identically to a tree with no optimizer installed") that `pre-card behavior` was carrying loosely.

### Notes for Worker 3

- **The scratchpad is shared and a filename collision has already destroyed one cohort's instrument.** Everything here lives under a private `cohortE-027/` subdirectory with `027` in every filename. A reviewer re-running any cohort's script by filename should assume the name may hold another cohort's content, and re-derive rather than re-run.
- **The census instrument's classification order was corrected mid-pass**, and the reason is recorded above: testing the preceding character before testing closure misfiles `consumers.py:1367` — a real, correctly-closed citation opened after `(` — as a string literal. Any re-implementation should check closure first.
- **The 425-vs-565 file counts are both correct and mean different things.** 425 is tracked `.py` at `HEAD` (via `git archive`); 565 is what a filesystem walk of the working tree sees. Both censuses are reported so neither number has to be trusted alone.
- No shadow file was used. `scripts/review_inspect.py` was **skipped**: this pass adds no logic, and the helper's `<stem>.stripped.py` replaces every comment and string-literal token with `...`, so its output is provably invariant under this diff — the executable-token identity table is the mechanical evidence for the skip.
- **This artifact itself scores 4 on the markdown census, and all four are deliberate.** Two are the `### Dispatched sites checklist` boxes quoting the broken citations verbatim (the box text is fixed by the dispatch and must not be "fixed"), and two are quotations of the `` git grep 'spec-<NNN> #"' `` pattern, whose trailing quote-inside-quote is the same false-positive shape. The `.md` figure of 26 reported above was measured over the tree **before** this artifact existed; re-running that census now returns 30, and the four extra are these. Nothing here is a live citation.
- The item-8 population here is **6**, against cohort A's 0 over five package files. The asymmetry is real and not an over-reach: a test file's docstrings are where review-round labels accumulate, because each round adds a test and labels it with its own id. A reviewer auditing the fence should check the three KEEP classes named under `### Item 8` rather than the count.

### Notes for Worker 1 (spec reconciliation)

No spec-027 edit is needed for anything this pass landed. Four items concern surfaces fenced from this cohort.

- **`docs/SPECS/spec-033-connection_optimizer-0_0_9.md`, `## Revision history`, the Revision 3 bullet's finding (4).**
  - Current wording: "(4) **doc-reference hygiene** — production/test comments no longer cite the per-cycle review artifact ([`AGENTS.md`][agents])."
  - Recommended replacement: "(4) **doc-reference hygiene** — production/test comments no longer cite the per-cycle review artifact ([`AGENTS.md`][agents]). The narrower per-round *labels* (`Revision N`, `P<n>`) survived that sweep inside `tests/test_relay_connection.py` docstrings and were removed later; a comment names a spec Decision or nothing."
  - Reason: the finding claims a hygiene sweep that this pass found incomplete in the very file spec-033 nominates as its relation-connection surface — four `Revision N P<n>` labels and two `Implementation step N` references were still live at `HEAD`. Recording it stops the same claim being read next cycle as evidence the class is closed. `spec-033` is another card's spec, so this is recorded rather than edited.
- **`docs/SPECS/spec-033-connection_optimizer-0_0_9.md`, wherever the workstream partition is named** — and it is named nowhere.
  - Current wording: none. `grep -ci workstream` over the spec returns **0**, and `grep -rln 'workstream C' docs/` returns nothing at all.
  - Recommended replacement: a sentence under `### Decision 6` or the spec's own scope section naming the four workstreams (A-D) and what each covers, so the eight `workstream B/C/D` references in `tests/test_relay_connection.py` and the `workstream D` reference in `django_strawberry_framework/optimizer/walker.py` resolve to a contract.
  - Reason: this cohort **kept** that vocabulary, on the standing rule that a cross-referenced rule name is a contract pointer rather than provenance — live package source uses it, so deleting it from the tests alone would leave the package half-consistent. But it resolves to no document, which is the condition that turns a rule name into provenance. Either the spec names the partition or a later cycle retires the vocabulary; this cohort cannot decide that for another card.
- **`docs/SPECS/appx/spec-015-relay_interfaces-0_0_5-rationale.md`, the section prescribing the grep sweep, line 883.**
  - Current wording: `` `git grep 'spec-<NNN> #"'` before and after any reconciliation pass. ``
  - Recommended replacement: keep the command, and add: "That pattern is line-scoped, so it cannot see a citation whose `#\"` opens on one line and closes on the next — the defect class that cost this cycle eight repairs. Sweep for an *unclosed* `#\"` as well."
  - Reason: the prescribed instrument has exactly the blind spot the sweep exists to close, and this is the third measurement of this population to come in wrong. It is also (harmlessly) one of the 26 wrapped-citation hits in tracked markdown, because the pattern itself is an unclosed `#"`.
- **The 26 wrapped citations in tracked `.md`**, enumerated under `### The repo-wide census`: 14 in `docs/SPECS/`, 5 in `docs/SPECS/appx/`, 6 in `docs/builder/`, 1 in `docs/builder/DONE/`. Concentrated in `spec-040` (5) and `spec-037` (3). Not repaired: `docs/` is outside this cohort's fence and outside `scripts/check_citations.py`'s scope by its own design statement. Flagged because the `.py` half of this population is now 0, which makes the markdown half the whole of what remains.

### Deliberately not done

- **No repair outside the two-file partition.** The 26 markdown sites and the four `#"` string-literal false positives are recorded with their locations, not touched.
- **No unification of the two `walker.py` path spellings** (`walker.py` in the test, `optimizer/walker.py` in the example). Both resolve through the gate's suffix index; unifying them is cleanup outside the slice. Recorded under `### DRY analysis` with the resolution evidence.
- **No item-8 rewrite in `examples/fakeshop/apps/kanban/schema.py`**, because the measured population there is 0.
- **No removal of `workstream B/C/D`, `M1`, `spec-033 Decision 4 step f`, or the contrast prose**, each rejected with a stated reason and a measurement rather than passed over silently. The workstream question is routed to `### Notes for Worker 1` because it spans a fence this cohort cannot cross.
- **No `spec-033` or `spec-015`-companion edit.** Both are other cards' surfaces; routed with quoted current wording and recommended replacements.
- **No `--cov*` run, no `pytest` beyond the justified focused scope, no repo-wide `ruff` write mode, and no `git stash` / `checkout` / `restore` / `worktree` / `add` / `commit`.**

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: ../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[plan]: build-027-filters-0_0_8.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
