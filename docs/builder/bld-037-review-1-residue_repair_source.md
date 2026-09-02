# Build: Review round 1, cohort B — residue repair (source)

Spec reference: `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` (read-only this cohort; Worker 1 owns both spec files concurrently in cohort A)
Status: final-accepted

Cycle: `docs/builder/build-037-upload_file_image_mapping-0_0_11.md` `## Review round 1 — residue repair (maintainer-dispatched, 2026-09-02)`. Governed by `docs/builder/BUILD.md` `## Review rounds`; this is cohort **B** of the round's two-cohort ownership partition, carrying finding **R3** and no other.

Owned files (the entire cohort): `examples/fakeshop/apps/products/schema.py`, `examples/fakeshop/test_query/test_products_api.py`. Neither appears in cohort A.

Raw `path:NN` references appear below under `AGENTS.md` rule 27's per-cycle-artifact carve-out; symbol-qualified anchors are given wherever the symbol is stable.

---

## Plan (Worker 1)

**Cohort B has no Worker 1 planning pass.** The maintainer's standing carve-out for this round gave cohort A to Worker 1 alone and cohort B straight to Worker 2 build + Worker 3 review (`build-037-*.md` `### Findings dispatched`, ownership-partition table). This section therefore transcribes the dispatch contract rather than an authored plan; it is Worker 0's dispatch text, restated so Worker 3 can review against a written contract. No architectural call was made here.

### DRY analysis

Not applicable. The pass changes two card-id tokens inside prose; it adds no code, no helper, no literal, and no test.

### Implementation steps

1. Verify both ground-truth `KANBAN.md` headings before editing anything.
2. `examples/fakeshop/apps/products/schema.py` — in `Query`'s class docstring, `TODO-BETA-062-0.1.5` -> `TODO-BETA-066-0.1.5`. Nothing else on the line.
3. `examples/fakeshop/test_query/test_products_api.py` — in the module-level `#` comment above the cascade-permission block, the same single-token replacement.
4. Leave every other card id in `schema.py` untouched, and prove the count did not move.

### Test additions / updates

None. Both sentences are prose; no assertion exists to add or re-pin.

### Implementation discretion items

None. The replacement token is fixed by `KANBAN.md`, and the dispatch forbids rewording, reflowing, re-tensing and any added explanation.

### Dispatched findings checklist

- [x] **R3 — the same card rot in two `.py` comments.** `examples/fakeshop/apps/products/schema.py #"Still deferred to"` (`schema.py::Query` docstring, `schema.py:238`) and `examples/fakeshop/test_query/test_products_api.py #"those stay TODO-BETA-066-0.1.5"` (`test_products_api.py:2253`). Comment-only; owes the inverse proof that no behavior moved.

---

## Build report (Worker 2)

### Ground truth re-verified before editing

Both `KANBAN.md` headings read at their current lines, unedited:

```KANBAN.md:1157
### [TODO-BETA-062-0.1.3 - Aggregation subsystem](KANBAN.html#aggregation_subsystem)
```

```KANBAN.md:1430
### [TODO-BETA-066-0.1.5 - Fakeshop GraphQL schema activation](KANBAN.html#fakeshop_graphql_schema_activation)
```

So `TODO-BETA-062-0.1.5` was wrong in **subject, number and version simultaneously**: `062` is now the Aggregation subsystem at `0.1.3`, and the fakeshop-activation card is `066` at `0.1.5`.

**Renumber, not a lifecycle flip.** `KANBAN.md:1432` reads `- Status: To Do` under the `066` heading, so any `DONE-` prefix would be false. Card `066`'s planning note and Scope name exactly what the two comments defer — "the Relay `node` / `nodes` root entry points plus the connection `totalCount` opt-in" (`KANBAN.md` `#"The remaining unclaimed activation is the Relay"`) — which is what makes the referent live and the present tense correct at both sites.

### Files touched

- `examples/fakeshop/apps/products/schema.py` — one token in `Query`'s class docstring: `TODO-BETA-062-0.1.5` -> `TODO-BETA-066-0.1.5`.
- `examples/fakeshop/test_query/test_products_api.py` — one token in a module-level `#` comment: same replacement.

Grounded in `git status --short -- <the two paths>`, which lists exactly these two and nothing else.

### The diff, in full

```examples/fakeshop/apps/products/schema.py:238
-    Still deferred to `TODO-BETA-062-0.1.5` (the fakeshop-activation card): the
+    Still deferred to `TODO-BETA-066-0.1.5` (the fakeshop-activation card): the
```

```examples/fakeshop/test_query/test_products_api.py:2253
-# node(id:) / nodes(ids:) entry points (those stay TODO-BETA-062-0.1.5).
+# node(id:) / nodes(ids:) entry points (those stay TODO-BETA-066-0.1.5).
```

One line per file, one token per line. No rewording, no reflow, no re-tensing, no added explanation, and no provenance note — `AGENTS.md`-adjacent standing rule "no process provenance in code": both sentences now read as though they had always said `066`.

### Tests added or updated

None. Prose-only change.

### Instrument failability, then the counts

Every count is an **occurrence** count (`grep -oF <token> <file> | wc -l`), never a line count — a line count under-reports any wrapped token. The file population was iterated from a zsh **array** with `${#F[@]}` printed (`population size: 2`); `for f in $FILES` does not word-split in zsh and would have run one bogus iteration.

Each instrument is shown non-zero **before** the edit, so its post-edit zero is a measurement rather than a vacuous pass:

| Instrument | `schema.py` before | after | `test_products_api.py` before | after |
|---|---|---|---|---|
| `TODO-BETA-062-0.1.5` | 1 | 0 | 1 | 0 |
| `TODO-BETA-066-0.1.5` | 0 | 1 | 0 | 1 |

The `066` row is the inverse instrument: it starts at 0 and ends at 1, so the disappearance of `062` is proved to be a replacement and not a deletion.

Repo-wide, `.py` only: `grep -rlF 'TODO-BETA-062-0.1.5' --include='*.py' .` listed exactly these two files before the edit and lists **none** after. The `.py` population of that token is now empty tree-wide.

### Not widened: the 18 card ids left alone

`schema.py` carries 18 further rotted ids owned by `KANBAN.md` card `TODO-ALPHA-056-0.0.17` and coupled to a maintainer ruling not yet taken. Counted before and after, in the same file:

| Card id | before | after |
|---|---|---|
| `TODO-BETA-046-0.1.1` | 7 | 7 |
| `TODO-BETA-047-0.1.2` | 5 | 5 |
| `TODO-BETA-049-0.1.3` | 6 | 6 |

18 before, 18 after; no count moved. None of the three tokens appears in either diff hunk above.

### Inverse proof 1 — byte level

Both owned files were **byte-identical to `HEAD`** at pass start, so `HEAD` is a valid baseline and the diff below is entirely mine:

- `git show HEAD:examples/fakeshop/apps/products/schema.py > <scratch>/head-037-schema.py; diff <scratch>/head-037-schema.py examples/fakeshop/apps/products/schema.py` -> no output (identical) at pass start.
- same for `test_products_api.py` -> no output (identical) at pass start.
- `git status --short -- <the two paths>` -> empty at pass start.

**No pre-existing dirt on either owned file.** (The tree at large carries ~100 baseline-dirty paths from concurrent sessions; none of them is one of my two, and none was read for writing, edited, reverted or tidied — `AGENTS.md` rule 34.)

After the edit, against the same `HEAD` copies, `diff -u` returns exactly one hunk per file, each a single `-`/`+` line pair — the two hunks quoted in `### The diff, in full` and nothing else. A second diff against a pre-edit copy taken aside (`<scratch>/pre-037-*.py`) returns the identical single-line change per file (`238c238`, `2253c2253`), which isolates my delta independently of `HEAD`.

`uv run ruff format` and `uv run ruff check --fix`, scoped to the two paths by explicit array, then re-diffed against the pre-edit copies: **still exactly those two lines**, so the formatter introduced no churn of its own. `uv run python scripts/check_trailing_commas.py --check <the two paths>` exits 0, which is also the ASCII-only gate; `LC_ALL=C grep -n '[^ -~\t]'` reports **0** non-ASCII lines in each file.

### Inverse proof 2 — semantic inertness

Not asserted; measured three ways.

**AST identity.** `ast.dump(ast.parse(...))`, `HEAD` versus working, per file:

| File | plain AST identical | docstring-blanked AST identical | docstrings that differ |
|---|---|---|---|
| `schema.py` | **False** | **True** | `ClassDef:Query` (exactly one) |
| `test_products_api.py` | **True** | **True** | none |

`test_products_api.py`'s plain AST is byte-for-byte identical under `ast.dump`, which is the definition of comment-only. `schema.py`'s executable AST is identical once docstrings are blanked, and the enumeration of every `Module`/`ClassDef`/`FunctionDef` docstring names exactly **one** changed docstring, `Query`'s — so no other docstring and no executable token moved.

**The instrument's controls.** A blanked-AST comparison that cannot fail proves nothing, so three controls were run against the working file:

- perturb one executable token (`all_categories:` -> `all_categories_X:`) -> blanked AST **DIFFERS** in both files. The instrument can see code.
- perturb one comment character -> plain AST **IDENTICAL** in `test_products_api.py`. Comments are genuinely outside the AST.
- perturb the docstring (`Still deferred to` -> `Still deferred TO`) -> plain AST **DIFFERS**, blanked AST **IDENTICAL**. The docstring enumeration can see a docstring edit, which is what makes "exactly one docstring differs" a measurement.

**Does anything read the edited text at runtime?**

- **Site 1 is a class docstring**, not a module or function docstring: `ast.get_docstring` attributes it to `ClassDef Query` in `examples/fakeshop/apps/products/schema.py::Query`.
- **`strawberry` does not turn a class docstring into a GraphQL description.** `grep -rn "__doc__" .venv/.../site-packages/strawberry/` returns three hits, all unrelated (a `DirectiveValue` assignment and the `input_mutation` extension's synthesized input description); no type-construction path reads `cls.__doc__`. Measured end to end rather than inferred: building the real aggregate schema (`config.schema.schema`, SDL length 278165) gives `"Still deferred to" in sdl` -> **False**, `"TODO-BETA" in sdl` -> **False**, `"cookbook mirror" in sdl` -> **False**, and `schema._schema.query_type.description` -> **None**, while `Query.__doc__` is non-empty. The docstring is on the class and absent from the wire surface.
- **No doctest collection.** `--doctest-modules` appears nowhere: `pytest.ini` `addopts` is `-v -n auto --dist loadscope --cov --cov-report=term-missing`, and `grep -rn doctest pyproject.toml pytest.ini setup.cfg` matches nothing (`setup.cfg` does not exist).
- **No docstring reader touches it.** Repo-wide `grep -rn "__doc__"` outside `.venv` hits only `scripts/*.py` argparse `description=__doc__` (their own module docstrings) and three package-internal uses (`filters/sets.py` comment prose, `auth/mutations.py` building a synthesized `__doc__`, `utils/strings.py` `assigned=(...)` for `functools.wraps`) — none reads `apps.products.schema.Query.__doc__`. `grep -rn "\bhelp("` outside `.venv`: no hits.
- **`docs/TREE.md` is unaffected.** `scripts/build_tree_md.py::python_docstring` parses with `ast.get_docstring(module)` — module docstrings only. The docstring enumeration above shows no `Module` docstring changed in either file, so the render cannot move. (`docs/TREE.md` is fenced off this cycle and was not touched.)
- **Site 2 is a real comment.** `tokenize` reports the token at `(2253, 0)` as `COMMENT`; it is not inside a string literal. Consistent with the plain-AST identity above.
- **No test asserts on either text.** `grep -rn "Still deferred to" --include='*.py' --include='*.md' .` (excluding `.venv`) -> the single site itself. `grep -rn "those stay TODO-BETA"` -> the single site itself. Nothing else in the tree, code or docs, quotes either sentence.

Verdict: **no behavior moved.** One class docstring's prose changed; the executable AST, the GraphQL SDL, the doctest surface (there is none) and the rendered docs are provably unchanged.

### Validation run

- `uv run ruff format examples/fakeshop/apps/products/schema.py examples/fakeshop/test_query/test_products_api.py` — pass (`2 files left unchanged`; the printed `COM812` note is the standing repo-wide formatter/lint-rule advisory, not a finding).
- `uv run ruff check --fix <the same two paths>` — pass (`All checks passed!`).
- `uv run python scripts/check_trailing_commas.py --check <the same two paths>` — exit 0 (this is also the ASCII-only gate).
- `git status --short -- <the same two paths>` after both ruff invocations — `M` on exactly those two, both in `### Files touched`. Nothing else. Neither ruff invocation was run on `.`, so no file outside the cohort could churn.
- Focused test run, no `--cov*` flag: `uv run pytest examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products --no-cov -q` -> **`192 passed in 36.28s`** (8 workers, 192 items collected). **Zero failures, so no attribution is owed**: none of the four known pre-existing failures (`tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key`, `tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration`, two rows in `tests/test_sets_mixins.py`) lies inside this scope, and none appeared.

### Failability proofs

`None; this pass introduced no new boundary.` The pass adds no guard, gate, rejection path or test. The two inverse proofs above carry their own controls, which is the analogous discipline for an "unchanged" claim: the executable-token control makes the AST instrument failable, and the pre-edit non-zero grep counts make each zero failable.

### Hot-path budget

`Not applicable; plan declares no hot path.` The pass adds no runtime code, no per-request or per-resolver work, no lock and no serialization point.

### Floor verification

`Owned by the final gate per the plan's declaration.` A prose-only change cannot be version-sensitive, and no dependency surface is touched. `/tmp/dsf-floor-037` was not built or mutated this pass, and the shared `.venv` was not installed into.

### Implementation notes

- **Replacement bound by content, not by the dispatch's line numbers.** Both sites were located by their unique substrings (`Still deferred to \`TODO-BETA-062-0.1.5\``, `those stay TODO-BETA-062-0.1.5`) and each substring's uniqueness confirmed before the edit. The predicted lines (238, 2253) happened to be right, but the anchor is what made the edit safe.
- **Occurrence counts, never line counts.** Both tokens sit whole on one line today, but a line-oriented count is fail-open on any grammar that can wrap, and it prints a clean pass when it under-reports. `grep -oF` throughout.
- **Neither site was re-tensed.** "Still deferred to" and "those stay" are present tense against a `Status: To Do` card, so both sentences remain true as written once the numeral is right. Re-tensing would have been the error.

### Notes for Worker 3

- The whole cohort is two single-token replacements; the fastest complete review is `diff` against `git show HEAD:<path>` for both files, which yields exactly the two hunks quoted above.
- **Re-run scope for the inverse proof:** plain `ast.dump` equality is the correct instrument for `test_products_api.py` and legitimately **fails** for `schema.py`, because site 1 is a class docstring. For `schema.py`, use the docstring-blanked variant **plus** the docstring enumeration (which must name exactly `ClassDef:Query`); do not read the plain-AST `False` as a defect.
- Both owned files were clean at `HEAD` at pass start, so no dirt attribution is owed on this cohort. The tree's other ~100 dirty paths are concurrent work and untouched.
- The 18 `046`/`047`/`049` ids in `schema.py` are deliberately unchanged (owned by `TODO-ALPHA-056-0.0.17`); their 7/5/6 split is verifiable with the same `grep -oF` instruments.
- No shadow file, no `scripts/review_inspect.py`, no temp test was used.

### Notes for Worker 1 (spec reconciliation)

**No spec amendment is owed by this cohort, and none was authored.** Both spec files (`docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` and `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md`) were opened **read-only** and are cohort A's; the round's R1 covers their five `062` sites. Neither file appears in `git status --short` for this pass.

One item for the custodian's awareness, not an amendment to cohort A's text:

- **The `.py` half of the `062` -> `066` renumber is now closed, tree-wide.** After this pass, `grep -rlF 'TODO-BETA-062-0.1.5' --include='*.py' .` returns nothing. If any spec or companion sentence describes the source-side sites as outstanding, it is now false; the spec-side sites (R1) are the only remaining members of that population.

---

## Review (Worker 3)

Every claim below was **re-derived**, not read off the build report. Where my instrument differs from
Worker 2's, mine is stated. Two claims I could not re-derive at all are named as such.

### High:

None.

### Medium:

#### M1 — `### Notes for Worker 1` states a population closed that measurement says is open by 34 occurrences

`docs/builder/bld-037-review-1-residue_repair_source.md:198` (the build report's own prose, not the diff):

```docs/builder/bld-037-review-1-residue_repair_source.md:198
... the spec-side sites (R1) are the only remaining members of that population.
```

**False by measurement.** `TODO-BETA-062-0.1.5` still occurs **34 times across 8 spec-surface files**,
none of them R1's pair, every one a live forward reference to the fakeshop-activation card:

| File | occurrences |
|---|---|
| `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md` | 11 |
| `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | 6 |
| `docs/SPECS/spec-032-full_relay-0_0_9.md` | 5 |
| `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` | 4 |
| `docs/SPECS/spec-041-channels_router-0_0_14.md` | 3 |
| `docs/SPECS/spec-030-connection_field-0_0_9.md` | 2 |
| `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` | 2 |
| `docs/SPECS/spec-044-debug_extension-0_0_14.md` | 1 |

Instrument: `for f in $(grep -rIlF 'TODO-BETA-062-0.1.5' . --exclude-dir=.venv --exclude-dir=.git); do
grep -oF 'TODO-BETA-062-0.1.5' "$f" | wc -l; done` — occurrence counts, not line counts. Tree-wide total
`58`; subtracting the 15 inside per-cycle `docs/builder/` artifacts and the 9 behind the maintainer's
fence (`TODAY.md` 3, `KANBAN.md` 3, `KANBAN.html` 3) leaves these 34.

I read every one of the 34. They are not historical records of a past id — they are live deferral
prose: `spec-030:84`/`:532` DoD items ("lit up at fakeshop activation per `TODO-BETA-062-0.1.5`"),
`spec-032:542` and `spec-033:127`/`:236`/`:524` ("retains the products `node` / `nodes` entry points
and the `totalCount` opt-in", "the rest of the fakeshop products / Relay activation"),
`spec-041`/`042`/`044` ("the natural host", "if the maintainer wants it"), and the two rationale
companions' rejected-alternative and ownership-overlap bullets. Same subject, same defect as R1 and R3,
stale by the same +6.

**Why it matters, and why it is not a nit.** The sentence is addressed to the custodian, who reads it at
final verification. As written it licenses declaring the `062` -> `066` renumber closed once R1 lands.
It is already stale in the other direction too: `spec-037` and its companion now measure `062=0`
/ `066=2` and `066=3` respectively, so cohort A has closed R1 and the sentence's own named remainder is
empty while 34 occurrences it does not name survive. This is `BUILD.md` `## Claims are proven
mechanically` "a **stated count**" verbatim — a number that "reads as measured and every later pass
treats it as measured" — and the falsity direction is fail-open.

`R3` itself is unaffected: the two-token diff is correct and complete, and the `.py`-scoped half of the
claim (`grep --include='*.py'` returns nothing) is true — see "What looks solid".

**Recommended change.** Restate the bullet as what it actually measured — the `.py` population — and
replace the "only remaining members" clause with the measured spec-surface residue above. Routing, not
fixing: the 34 sites are archived specs and companions, outside this round's two cohorts. `KANBAN.md`
card `TODO-ALPHA-056-0.0.17` already owns this exact population at its
`#"Swept 2026-08-07: all 32 occurrences of the dead card id"` row — that 2026-08-07 sweep is what wrote
`062` into "seven archived specs" in the first place, and **that row's own sentence is now stale by the
same +6**. Escalated to Worker 1 below for the ownership call.

No test is owed: the sentence is artifact prose.

### Low:

#### L1 — the round's dispatch instrument under-reports its own population by construction

Not a defect in this cohort's diff; recorded because it is why M1 was available to find. Worker 0's
pre-dispatch pass corrected card `056`'s instrument for one blind spot — `grep ... docs/SPECS/spec-03[4-9]*.md`
"never scans `docs/SPECS/appx/`" (`build-037-*.md:251-253`). That correction is right and incomplete:
the same glob also never scans `spec-030`, `spec-032`, `spec-033`, `spec-041`, `spec-042` or `spec-044`,
where **21 of the 34** occurrences live, with **13 more** in the two `appx/` companions. A
`spec-03[4-9]` glob cannot see a population the 2026-08-07 sweep deliberately wrote across ten files.
Recommended change: none in this cohort. Worth carrying to whichever pass closes card `056`'s row — the
instrument wants to be the bare token over the whole tree, then partitioned, exactly as M1 measures it.

### DRY findings

None. The diff is two lines, one token each. No helper, no constant, no test, no duplication was added,
and none is owed: a card-id renumber inside prose has no logic to share. I considered and rejected the
existence challenge on the obvious candidate — a shared "current card id" constant the two comments
could import — because a `#` comment cannot read a constant, and a docstring that interpolated one
would put a runtime dependency behind a sentence. Two literals in two comments is the correct shape.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` — **empty**. `__all__` and the re-export list are
unchanged. The cohort touches no package source at all.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

`Not applicable; slice did not modify CHANGELOG.md.`

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

`Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.` Confirmed rather than
asserted: `git status --short` for this cohort lists exactly the two `.py` paths, and neither
`KANBAN.md`, `TODAY.md`, `CHANGELOG.md`, `docs/GLOSSARY.md` nor `docs/TREE.md` appears. `KANBAN.md` was
opened read-only for the ground-truth check below. The 34 archived-spec sites in M1 are **reported, not
touched** — they are behind this round's fence.

### What looks solid

**Ground truth, read independently from `KANBAN.md`.**

- `KANBAN.md:1157` = `### [TODO-BETA-062-0.1.3 - Aggregation subsystem]`; `:1430` =
  `### [TODO-BETA-066-0.1.5 - Fakeshop GraphQL schema activation]`; `:1432` = `- Status: To Do`. The old
  id was wrong in subject, number and version simultaneously, and a `DONE-` prefix would be false. The
  renumber, not a lifecycle flip, is the right shape.
- **Card `066`'s scope really is the referent both comments name.** Its `#### Planning note` reads "The
  remaining unclaimed activation is the Relay `node` / `nodes` root entry points plus the connection
  `totalCount` opt-in"; `#### Scope` bullet 2 and DoD items 1-2 restate it. Both comments defer exactly
  the root `node(id:)` / `nodes(ids:)` entry points and the `Meta.connection` (`totalCount`) opt-in.
  Referent confirmed live.
- **Card `062` is not the referent.** Its body never mentions `node(id:)` or `nodes(ids:)`. Its single
  `totalCount` occurrence is an adjacent-optimizer-seam bullet about parallelising
  `connection.py::_attach_count_sync` against the page slice — a package-internal perf investigation,
  not the fakeshop opt-in. Pointing at `062` was wrong; pointing at `066` is right.

**The edit is exactly two tokens.** `git show HEAD:<path>` into a scratch path outside the repo, then
`diff -u`, per file: **one hunk each, one `-`/`+` line pair each, one token changed on each**. No
rewording, no reflow, no re-tensing, no whitespace change, no provenance note. Both sentences read as
though they had always said `066` — `AGENTS.md`'s no-process-provenance rule is satisfied, and the
present tense ("Still deferred to", "those stay") stays true against a `Status: To Do` card.

**A stronger no-collateral instrument than the build report's, same verdict.** Rather than counting the
three named tokens, I censused **every** card id in `schema.py` on both sides
(`grep -oE '(TODO|DONE|WIP)-[A-Z]*-?[0-9]+[A-Za-z0-9._-]*' | sort | uniq -c`):

```
HEAD     1 DONE-027-0.0.8; 1 DONE-028-0.0.8; 1 DONE-030-0.0.9; 1 DONE-034-0.0.10;
         7 TODO-BETA-046-0.1.1; 5 TODO-BETA-047-0.1.2; 6 TODO-BETA-049-0.1.3; 1 TODO-BETA-062-0.1.5
WORKING  1 DONE-027-0.0.8; 1 DONE-028-0.0.8; 1 DONE-030-0.0.9; 1 DONE-034-0.0.10;
         7 TODO-BETA-046-0.1.1; 5 TODO-BETA-047-0.1.2; 6 TODO-BETA-049-0.1.3; 1 TODO-BETA-066-0.1.5
```

The two multisets differ in exactly one entry. The 18 deliberately-untouched ids hold at 7/5/6 = **18
before, 18 after**, and they sit on lines 22, 23, 36, 37, 85, 86, 87, 125, 126, 127, 163, 164, 165, 189,
200, 201, 202 — none inside either hunk (238, 2253). The four `DONE-` ids are proved untouched too,
which the three-token instrument could not have shown.

**Site classification, by `tokenize` rather than by eye.** `test_products_api.py` line 2253 yields
`COMMENT (2253, 0)` — a real comment, not text inside a string. `schema.py` line 238 falls inside a
single `STRING` token spanning `(223, 4)`-`(241, 7)`, which is `ClassDef Query`'s docstring (the class
starts at line 222). Both the build report's classifications hold.

**The inverse proof, re-run with its own controls.** `ast.dump` comparison, `HEAD` vs working:

| File | plain AST identical | docstring-blanked AST identical | docstring key sets equal | changed docstrings |
|---|---|---|---|---|
| `schema.py` | False | **True** | True | `['ClassDef:Query:222']` |
| `test_products_api.py` | **True** | True | True | `[]` |

Reproduces the build report exactly, including the legitimate plain-AST `False` on `schema.py`. Four
controls, each run against a **scratch copy** so the review needed no source carve-out at all:

| Control | expectation | result |
|---|---|---|
| perturb an executable token in `schema.py` (`all_categories` -> `all_categories_XX`) | blanked AST differs | **DIFFERS** |
| perturb only the `#` comment in `test_products_api.py` | plain AST identical | **IDENTICAL** |
| perturb an executable token in `test_products_api.py` (`def test_` -> `def test_XX_`) | plain AST differs, key sets diverge | **DIFFERS**, key sets `False` |
| perturb the `Query` docstring further (`Still deferred to` -> `Still deferred TO`) | plain differs, blanked identical, names `ClassDef:Query` | **exactly that** |

The instrument sees code in both files and sees a docstring edit, so "blanked-identical, exactly one
changed docstring" is a measurement in both directions and not a vacuous pass.

**Angle (a): does anything but Strawberry's description path read a *class* docstring? Closed, with a
failable control.** I did not re-run the build report's `.venv` `__doc__` grep; I replaced it with a
direct measurement of the property that grep was standing in for.

- The edited class is genuinely **live** in the aggregate schema, so the SDL measurement below cannot be
  vacuous: `apps.products.schema.Query in config.schema.Query.__mro__` -> `True`, and all four root
  fields `allCategories` / `allItems` / `allProperties` / `allEntries` are present in the printed SDL.
- Building the real aggregate schema and printing it: SDL length **278165** (matches the build report
  digit for digit); `"Still deferred to" in sdl` -> **False**; `"TODO-BETA" in sdl` -> **False**;
  `"066-0.1.5" in sdl` -> **False**; `"cookbook mirror" in sdl` -> **False**;
  `schema._schema.query_type.description` -> **None** while `Query.__doc__` is non-empty and still
  contains the edited sentence.
- Widened past the root type: of **794** entries in `schema._schema.type_map`, exactly **2** carry a
  multi-line (docstring-shaped) description, and both are GraphQL introspection built-ins (`__Type`,
  `__Directive`). No first-party type in the whole schema has a docstring-derived description.
- **The control that makes those Falses failable.** A throwaway `@strawberry.type` class with the
  docstring `"""SENTINEL-DOCSTRING-TEXT."""` -> `"SENTINEL-DOCSTRING-TEXT" in print_schema(...)` =
  **False** (Strawberry does not promote `__doc__`, measured rather than inferred), while
  `@strawberry.type(description="SENTINEL-EXPLICIT-DESC")` -> **True** (the SDL instrument does surface
  descriptions, so a `False` above is evidence and not blindness).
- No other reader exists. `grep -rIn '__doc__' --include='*.py' . --exclude-dir=.venv` returns 8 hits:
  five `argparse(description=__doc__)` in `scripts/` (their own module docstrings), a comment in
  `filters/sets.py`, a synthesized `__doc__` built in `auth/mutations.py`, and `utils/strings.py`'s
  `functools.wraps` `assigned=` tuple. None reaches `apps.products.schema.Query.__doc__`.
  `inspect.getdoc`, `pydoc` and `help(` have **zero** hits outside `.venv`. No `description=` anywhere in
  `django_strawberry_framework/` is sourced from a docstring.
- `ast.get_docstring` has three readers: `scripts/build_tree_md.py:163` (`ast.get_docstring(module)`,
  module only — and the docstring key-set comparison above shows no `Module` docstring changed, so the
  `docs/TREE.md` render cannot move), plus `scripts/review_inspect.py` and `docs/dry/export_dry_review.py`,
  both per-cycle shadow generators whose output is regenerable and carries none of this text.
- No doctest surface: `pytest.ini` `addopts` is verbatim `-v -n auto --dist loadscope --cov
  --cov-report=term-missing`, `grep -rn doctest pyproject.toml pytest.ini` matches nothing, and
  `setup.cfg` does not exist.

**Angle (b): committed SDL / snapshot artifacts. None exist.** `git ls-files | grep -iE
'\.(graphql|gql|sdl|graphqls)$'` -> **no tracked files**. `git ls-files | grep -iE
'snapshot|golden|schema\.(json|txt)|__snapshots__'` -> one hit,
`scripts/review_historical_package_snapshot_at_commit.py`, a generator rather than an artifact. The
`export_schema` command renders SDL on demand; `tests/management/test_export_schema.py` asserts
stdout == `--path` bytes == `print_schema(schema)`, a three-way self-consistency contract with no
committed golden to drift against. Decisive cross-check: `grep -rIn 'Still deferred to'` over the whole
tree returns **the source site itself plus this artifact, and nothing else** — no derived, generated or
committed file anywhere embeds the edited sentence.

**Population, re-derived with three instruments, not one.**

- Versioned, `.py`-scoped: `grep -rIlF 'TODO-BETA-062-0.1.5' --include='*.py' . --exclude-dir=.venv` ->
  **0 files**.
- **Version-less** (the instrument the build report did not run):
  `grep -rIlE 'TODO-BETA-062' --include='*.py' . --exclude-dir=.venv` -> **0 files**. No `062` spelling
  of any version survives in `.py` anywhere.
- Spelling census tree-wide: `grep -rIohE 'TODO-BETA-062[A-Za-z0-9._-]*' | sort | uniq -c` -> **58**
  `TODO-BETA-062-0.1.5`, **39** `TODO-BETA-062-0.1.3` (correct — the Aggregation card), **3** bare
  `TODO-BETA-062` (all three inside per-cycle `docs/builder/bld-037-*.md` artifacts). No stale
  intermediate spelling exists.
- The replacement's own population: `TODO-BETA-066-0.1.5` occurs in `.py` at exactly **2** sites,
  `schema.py:238` and `test_products_api.py:2253`, and nowhere else in any `.py`. Replacement, not
  deletion, proved from the destination side.
- Beyond `.py`: **nothing in `scripts/` or `examples/` outside the two edited files** carries any `062`
  spelling. The non-`.py` residue is the 34 spec-surface occurrences of M1 plus 9 behind the fence
  (`TODAY.md` 3, `KANBAN.md` 3, `KANBAN.html` 3) and 15 in per-cycle builder artifacts.

**Gates and formatting.** `scripts/check_trailing_commas.py --check` on both paths -> exit **0** (this
is also the ASCII-only gate); `LC_ALL=C grep -c '[^ -~\t]'` -> **0** and **0**. `git status --short` for
the two paths lists ` M` on exactly those two and nothing else, so neither scoped ruff run churned a
file outside the cohort.

**Failability proofs.** `None; this pass introduced no new boundary.` is the correct entry and I audited
it as such: the diff adds no guard, gate, rejection path or conditional, so nothing in it meets
`BUILD.md` `### What needs a proof`. My mandatory re-run floor is therefore **empty and legally empty**
— `worker-3.md`: "An **empty re-run set is legal only when the diff introduces no boundary that meets
the floor.**" What I re-ran instead is the analogous control set for an *unchanged*-claim: the four AST
controls and the two SDL sentinel controls above, all of which the build report owed and all of which
reproduce. **No boundary was accepted on Worker 2's record**, because none exists.

**Hot-path budget / floor verification.** `Not applicable` and `Owned by the final gate` are both
correct. The pass adds no runtime code, no per-request work, no lock, and touches no dependency
surface.

**Tests.** Verbatim, my own run of the recorded scope:

```
uv run pytest examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products --no-cov -q
============================= 192 passed in 36.67s =============================
```

192 items, 8 workers, zero failures, zero collection errors — the build report's `192 passed in 36.28s`
reproduces row-for-row. **No attribution is owed**: none of the four known concurrent-session failures
(`tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key`,
`tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration`,
two rows in `tests/test_sets_mixins.py`) lies in this scope and none appeared.

I also ran the three files outside the recorded scope that import `apps.products.schema` and **rebuild a
schema from it** — the closest thing in the tree to an introspection-sensitive consumer, and the rows
most able to see a description change if one existed:

```
uv run pytest examples/fakeshop/test_query/test_debug_extension_api.py examples/fakeshop/test_query/test_products_visibility_api.py tests/mutations/test_inputs.py --no-cov -q
============================== 88 passed in 6.69s ==============================
```

**Scope discipline.** Two files, two lines, no new file, no test, no helper. `### Files touched` matches
the diff exactly. Nothing outside the cohort was written. I read both spec files **read-only** and wrote
neither; cohort A's concurrent work on them is visible (`spec-037` now measures `062=0` / `066=2`) and I
left it alone.

### Temp test verification

None. No temp test under `docs/builder/temp-tests/` was created or needed. Every instrument was a
read-only measurement or a comparison between two **scratch copies outside the repository**, so
Worker 3's source carve-out was never exercised — no production file was mutated at any point in this
review, and no revert was owed. `scripts/review_inspect.py` was **not run**: its value is control-flow
shadowing and repeated-literal evidence, and a two-token prose diff offers neither; the repeated-literal
half is discharged by the card-id census above. `scripts/prove_failability.py` was not run because the
diff introduces no boundary. No shadow file was used.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: who owns the 34 remaining `TODO-BETA-062-0.1.5` occurrences in archived specs and
  companions?** (M1's table.) They are behind this round's fence and this cohort neither fixed nor may
  fix them. Resolution paths: **(a)** fold them into `KANBAN.md` card `TODO-ALPHA-056-0.0.17`'s existing
  `#"Swept 2026-08-07: all 32 occurrences of the dead card id"` row, which created this population and
  whose own sentence is now stale by the same +6 — the cheapest home, and the row already claims the
  ten-file population; **(b)** card them separately as a `062` -> `066` tree sweep, on the grounds that
  `056` is already overloaded and this population is mechanically uniform; **(c)** rule that archived
  specs preserve their as-shipped ids and close the population at the live surfaces only — rejected on
  the evidence, since the 2026-08-07 sweep itself rewrote the id across seven archived specs, so the
  standing convention is to sweep them. Whichever path is taken, the count wants re-deriving with the
  bare-token instrument over the whole tree at that time, not with a `spec-03[4-9]` glob (L1).
- **`spec-037` and its companion now measure `062=0`.** Cohort A has closed R1: `spec-037` reads
  `066` twice, the companion three times, and neither carries `062` any more. Worth confirming at final
  verification, since the build report's custodian note was written while they still did.
- No spec amendment is owed by this cohort and none was authored. Both spec files were read-only here.

### Review outcome

`revision-needed`.

The dispatched work — finding **R3** — is **correct, complete and minimal**, and I would accept the diff
unchanged: two tokens, provably no collateral, provably semantically inert, 192 rows green. Nothing in
the source needs to change.

What blocks acceptance is **M1**, an unresolved Medium in the build report's own prose with no recorded
rejection reason (`worker-3.md` `### Acceptance gate`). The escalation carve-out does not cover it: the
correction is a one-bullet restatement of a claim to the scope it actually measured, needing no spec
context Worker 2 lacks. Only the *routing* of the 34-occurrence residue needs Worker 1, and that is
escalated above independently.

Re-pass scope for Worker 2: rewrite `### Notes for Worker 1 (spec reconciliation)`'s single bullet so it
claims the `.py` population it measured and names the measured spec-surface residue. **Do not touch the
diff, and do not touch the 34 sites** — they are behind the fence.

---

## Build report (Worker 2, pass 2)

Scope of this pass: **M1 and L1 only, both confined to this artifact's prose.** The diff Worker 3
accepted unchanged was not reopened; no `.py` file was edited, read for writing, or re-formatted.

### Why this is an appended correction and not a rewrite of line 198

Worker 3's re-pass instruction says "rewrite" the pass-1 bullet. `docs/builder/ARTIFACT.md`
`## Re-pass sections` and `worker-2.md` `## Scope` both forbid editing a prior artifact section
("append a new build report instead"), and a review's prescribed fix is a hypothesis, not an
instruction (`BUILD.md` `## Review rounds`). The substance of M1 — the custodian must not read a false
population claim as measured — is discharged by **withdrawing the sentence here, quoted verbatim, and
restating it**: this section is the last Worker 2 text in the artifact, so it is what the custodian
reads at final verification. Pass 1's `### Notes for Worker 1 (spec reconciliation)` stands on disk as
the record of what was claimed, with its third sentence withdrawn below.

### Files touched

- `docs/builder/bld-037-review-1-residue_repair_source.md` — this section only (append-only).
- `docs/builder/worker-memory/worker-2.md` — one appended memory entry.

Grounded in `git status --short` plus `git check-ignore -v`, not memory: the artifact shows as `??`
(new, never tracked) and the memory file is ignored by `.gitignore:188`, so a status listing alone
cannot see it. The two already-accepted `.py` paths are unchanged from pass 1 (see
`### Inverse proof — the diff did not move`).

### The instrument, and its failability, before any count

Every figure below is an **occurrence** count taken by reading each file's bytes and calling
`bytes.count(b'TODO-BETA-062-0.1.5')` inside a `uv run python - <<'PY'` heredoc. Three properties make
it a measurement rather than a reading:

- **The population is enumerated and its size printed.** The file list is
  `git ls-files -co --exclude-standard` — **720 paths**, tracked plus untracked, ignored files excluded
  — iterated in Python, never `for f in $FILES` in zsh (which does not word-split and would run one
  bogus iteration to a clean-looking zero). The spec-surface sub-population is an explicit 8-element
  list with `len()` printed.
- **Occurrences, not lines.** Over the same 8 files the byte instrument returns **34** while the
  line-oriented `git grep -cF` returns **26**. The 8 lost occurrences sit in three files that name the
  card more than once on a line: `appx/spec-033-…-rationale.md` 11-on-5 (−6),
  `appx/spec-032-…-rationale.md` 2-on-1 (−1), `spec-032-full_relay-0_0_9.md` 5-on-4 (−1). A line count
  under-reports this population by 8 (24%), so it would have produced a plausible, checkable, wrong
  number.
- **It is shown non-zero where a non-zero is expected, and sensitive in both directions**, so a zero
  from it is evidence:

| Control | expectation | result |
|---|---|---|
| count over `docs/SPECS/spec-030-connection_field-0_0_9.md` (known carrier) | non-zero | **2** |
| same file copied to scratch with one occurrence planted | 3 | **3** |
| same file copied to scratch with the token replaced by `066` | 0, and `066` = 2 | **0 / 2** |
| a token that cannot exist (`TODO-BETA-062-0.1.5Z`) over all 720 paths | 0 | **0** |

Both mutated copies live outside the repository (`<scratch>/ctl-037-*.md`); no tracked file was written
to obtain any control.

### Re-derived: the spec-surface population of `TODO-BETA-062-0.1.5`

Re-derived from the tree, not copied from the review. A tree-wide total is **not** a stable figure while
this section is being written — the artifact quotes the token, so the number moves as the prose grows
(it read 76 across 17 files before this section existed and 83 across 17 after). Two figures below it
are stable and are the ones to carry: the per-cycle `docs/builder/` artifacts (5 files, this one among
them) are excluded as scratch, leaving **45 occurrences across 12 surfaces**, of which four are behind
the maintainer's fence (`TODAY.md` 3, `KANBAN.md` 2, `KANBAN.html` 2, `examples/fakeshop/db.sqlite3` 4 —
that last a raw-byte hit inside the board DB). What remains is the spec surface:

| File | occurrences |
|---|---|
| `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md` | 11 |
| `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | 6 |
| `docs/SPECS/spec-032-full_relay-0_0_9.md` | 5 |
| `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` | 4 |
| `docs/SPECS/spec-041-channels_router-0_0_14.md` | 3 |
| `docs/SPECS/spec-030-connection_field-0_0_9.md` | 2 |
| `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` | 2 |
| `docs/SPECS/spec-044-debug_extension-0_0_14.md` | 1 |
| **total, 8 files** | **34** |

Independently re-derived and identical to Worker 3's table, file for file and digit for digit. **All 34
are reported, not touched** — none of the eight files appears in `git status --short` for this pass, and
the round's fence puts them outside both cohorts.

### The `.py` population, re-measured

- `TODO-BETA-062-0.1.5` in `*.py`, over the same 720-path enumeration: **0 occurrences, 0 files.**
- The version-less spelling `TODO-BETA-062` in `*.py`: **0.**
- `TODO-BETA-066-0.1.5` in `*.py`: **2 occurrences**, `examples/fakeshop/apps/products/schema.py` and
  `examples/fakeshop/test_query/test_products_api.py` — the two accepted sites, proving replacement
  from the destination side.

### Inverse proof — the diff did not move

`git show HEAD:<path>` into a scratch copy, then `diff -u`, per owned file:

| File | hunks | `-` lines | `+` lines |
|---|---|---|---|
| `examples/fakeshop/apps/products/schema.py` | 1 | 1 | 1 |
| `examples/fakeshop/test_query/test_products_api.py` | 1 | 1 | 1 |

Byte-for-byte the two hunks pass 1 quoted and Worker 3 accepted, and nothing else. Neither file was
opened for writing this pass.

### Tests added or updated

None. The pass changes artifact prose only.

### Validation run

- `uv run ruff format` / `uv run ruff check --fix` — **not run, and not owed**: this pass touched no
  `.py` file. Running either would have written outside the pass's own files on a concurrently-dirty
  tree.
- `uv run python scripts/check_trailing_commas.py --check docs/builder/bld-037-review-1-residue_repair_source.md docs/builder/worker-memory/worker-2.md` — exit 0, with the gate reporting both paths **"excluded from the source-layout rules -- not checked"**: per-cycle `bld-*.md` and `worker-memory/` are outside the `.md` scaffold corpus, so the 0 is an exemption rather than a pass, and is recorded as such. `LC_ALL=C grep -c '[^ -~\t]'` on both -> **0** non-ASCII lines anyway (that rule is `.py`-only).
- `git status --short` after the edits, restricted to this pass's four paths — ` M` on the two `.py`
  paths accepted in pass 1 (unchanged content, see the hunk table above), `??` on this artifact (a new
  per-cycle file, never yet tracked), and nothing for `docs/builder/worker-memory/worker-2.md`, which
  `.gitignore:188` excludes as scratch. Nothing else is under this pass's authorship; the tree's other
  baseline-dirty paths are concurrent sessions' work, untouched and unread for writing.
- Focused test run, no `--cov*` flag, re-run at the recorded scope:
  `uv run pytest examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products --no-cov -q`
  -> **`192 passed in 36.12s`**. Third consecutive 192-row green (build pass, review pass, this pass);
  zero failures and zero collection errors, so **no attribution is owed** — none of the four known
  pre-existing failures from concurrent sessions
  (`tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key`,
  `tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration`,
  two rows in `tests/test_sets_mixins.py`) lies in this scope, and none appeared.

### Failability proofs

`None; this pass introduced no new boundary.` The pass adds no guard, gate, rejection path or test —
it edits prose in this artifact. The analogous discipline for a claim-correction pass is the
four-control instrument table in `### The instrument, and its failability, before any count`, which
makes every zero and every count above failable.

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Owned by the final gate per the plan's declaration.` No dependency surface, no runtime code, no venv
built or mutated this pass.

### Implementation notes

- **The corrected bullet claims scope, not closure.** The defect in pass 1's sentence was not a wrong
  number; it was a `.py`-scoped instrument's result promoted into a tree-wide claim about a population
  the instrument could not see (`START.md` "Instruments that lie": *a count can be right in every digit
  and wrong in its subject*). The replacement therefore states the run scope and the owned population
  as two separate sentences, and names no population as closed beyond the one it measured.
- **L1, recorded as an instrument lesson.** A `docs/SPECS/spec-03[4-9]*.md` glob cannot see this
  population by construction. Measured against my own census: of the 34 spec-surface occurrences,
  **21 sit in `spec-030` / `spec-032` / `spec-033` / `spec-041` / `spec-042` / `spec-044`** (outside the
  `03[4-9]` numeral range) and **13 sit in two `docs/SPECS/appx/` companions** (outside the directory) —
  the two blind spots overlap, so `spec-033` + its companion alone account for 17. **Zero of the 34 are
  inside the glob.** The generalisable lesson: a filename-shaped glob encodes a hypothesis about where a
  population lives, and a sweep that wrote across ten files falsifies it; sweep the bare token over an
  enumerated whole-tree file list first, then partition the hits by surface. The board-side correction
  to card `TODO-ALPHA-056-0.0.17`'s instrument is not this cohort's to make and was not made.
- **`grep -c` is the wrong reflex for this token specifically.** 34 occurrences on 26 lines is not a
  hypothetical hazard here; two of the eight files are prose that names the card twice in one sentence.

### Notes for Worker 3

- Nothing in the diff changed. The whole pass is this section plus one memory entry; the fastest
  complete re-review is the four-row control table and the 8-row census table above, both reproducible
  from an enumerated file list in one heredoc.
- The census counts **bytes in files**, so `examples/fakeshop/db.sqlite3` shows up (4) as a raw-byte
  hit inside the board DB rather than as prose. It is behind the fence and is excluded from the 34.
- `KANBAN.md` and `KANBAN.html` each measure **2** here where Worker 3's review measured 3. The board is
  a concurrently-written surface and its card `056` row was rewritten between the two measurements; both
  readings are behind the fence, neither is this cohort's to reconcile, and neither enters the 34.

### Notes for Worker 1 (spec reconciliation)

**No spec amendment is owed by this cohort, and none was authored.** Unchanged from pass 1: both
`spec-037` files were opened read-only and are cohort A's; neither appears in `git status --short` for
either pass.

**Withdrawn — pass 1's third sentence in this section.** `ARTIFACT.md` forbids editing a prior report,
so the sentence stands there and is retired here. It read, verbatim:

> If any spec or companion sentence describes the source-side sites as outstanding, it is now false; the
> spec-side sites (R1) are the only remaining members of that population.

The clause after the semicolon is **false by measurement** and was never measured: the instrument behind
it was `.py`-scoped (`grep -rlF ... --include='*.py'`) and the claim it was offered for was tree-wide.
Replaced by:

- **The `.py` population of `TODO-BETA-062-0.1.5` was exactly the two sites R3 names, and it is now
  empty.** Re-measured over an enumerated 720-path file list: `0` occurrences of the token and `0` of
  the version-less `TODO-BETA-062` in any `.py` file tree-wide, with `TODO-BETA-066-0.1.5` occurring in
  `.py` at exactly the 2 replaced sites. That is the whole of what this cohort measured and the whole of
  what it claims.
- **The id survives outside `.py`, and this cohort does not own it.** `TODO-BETA-062-0.1.5` still occurs
  **34 times across 8 spec-surface files** — the table under `### Re-derived: the spec-surface population
  of TODO-BETA-062-0.1.5` above, all archived specs and `appx/` companions, none of them R1's pair, all
  behind this round's fence and reported rather than touched. **Do not read this cohort as closing the
  `062` -> `066` renumber**; it closed the `.py` half of it.
- **R1's own remainder is separately confirmed empty.** Verified here rather than assumed:
  `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` measures `062-0.1.5 = 0` and
  `066-0.1.5 = 2`; its `appx/` companion measures `062-0.1.5 = 0` and `066-0.1.5 = 3`. Cohort A's five
  sites are closed, which is why the withdrawn sentence's named remainder was empty at the same moment
  34 occurrences it did not name survived — the falsity direction was fail-open.
- **Owner of the 34, for the routing call Worker 3 escalated.** `KANBAN.md` card
  `TODO-ALPHA-056-0.0.17` carries this population on its `#"Swept 2026-08-07"` scope row, whose text now
  names the discharge by this round and re-measures the surviving population at 48 occurrences across 13
  surfaces. That row is the named owner; **the board was not edited by this cohort** and its figure is
  cited as the board's, not re-derived as mine — my own whole-tree census, taken today and excluding
  per-cycle builder artifacts, is 45 occurrences across 12 surfaces, the difference sitting entirely in
  the concurrently-written board surfaces the row counts itself (`KANBAN.md`, `KANBAN.html`,
  `db.sqlite3`). Reconciling the two is the board's to do, not this cohort's.

---

## Review (Worker 3, pass 2)

**Accepted.** M1 is discharged. Every number in the withdrawal was re-derived here with a third
instrument, not audited against pass 2's narration, and every one reproduces. One new **Low** (L2) is
recorded with its rejection reason; nothing blocks.

### The append-vs-rewrite question, decided

My pass-1 re-pass scope said "rewrite" the bullet. Worker 2 declined and appended. **Worker 2's reading
of the corpus is correct, and appending is also sufficient here.** I read both rules myself rather than
taking the citation:

- `docs/builder/ARTIFACT.md` `## Re-pass sections` — "The artifact reads as a linear pass / review /
  pass / review sequence; **never edit prior entries.**"
- `docs/builder/worker-2.md` `## Scope`, "Worker 2 must not" — "edit the active spec, Worker 0/1/3
  memory, **or prior artifact sections (append a new build report instead)**."

Both are unconditional and neither carves out a correction. A prescribed fix is a hypothesis, not an
instruction (`BUILD.md` `## Review rounds`), and mine named a mechanism the corpus forbids; the finding
was the false claim, and Worker 2 discharged the finding by the means available to it. **I do not
overturn a correct reading of the corpus because a rewrite would be tidier** — and the tidier move is
worse than that here, because it would have erased the evidence that a `.py`-scoped instrument's result
was promoted into a tree-wide claim, which is the whole lesson.

On sufficiency, which is the real question. The concern is a reader who stops at line 198 and carries a
falsehood. Four things close it, and the fourth is the load-bearing one:

1. The withdrawal quotes the retired sentence **verbatim**, so the falsehood is discoverable from its own
   text: `grep -n 'only remaining members of that population'` on this artifact returns the original site
   **and** the block-quote inside the withdrawal. A reader who arrives at line 198 by search arrives at
   both.
2. It lands in the **same named section** the falsehood lives in — pass 1 `### Notes for Worker 1 (spec
   reconciliation)` is retired by pass 2 `### Notes for Worker 1 (spec reconciliation)`. A custodian
   reading the sections addressed to it reads the later one by construction, not by luck.
3. The `Status:` chain is what the custodian follows (`ARTIFACT.md` `## Status field ownership`), and it
   routes through every pass in order. `built` after a `revision-needed` means a later build report
   exists; stopping at the first one is not a supported read of this file.
4. **No worker can add a forward pointer at line 198.** Worker 2 is barred by its own `## Scope`;
   Worker 3 may edit this artifact "appending review sections only" (`worker-3.md` `## Scope`);
   Worker 1 owns the plan and final sections, not another worker's build report. So a forward pointer is
   a **maintainer** edit or nothing. Requiring one would make the finding unclosable by any worker, which
   is the signal that the corpus considers the append the closure. If the maintainer wants belt and
   braces at the original site, the maintainer is the only party who can add it; I do not think it is
   owed.

Two independent checks that the append actually functions as the closure: **the withdrawal is not buried
in an unread part of the file** (it is the last section of the artifact, above only the link-definition
block), and **it does not merely soften the sentence** — it names the clause, calls it false by
measurement, and states what was measured in its place. A withdrawal that restated the claim more
carefully without retiring it would have left M1 open; this one retires it.

### High:

None.

### Medium:

None. **M1 is discharged** (below). No new Medium.

#### M1 — discharged: the withdrawal states the truth, re-derived here

Every corrected claim, re-measured by me with an instrument that is neither pass 1's (`grep -oF` per
file off a `grep -rIlF` list) nor pass 2's (`bytes.count` over `git ls-files -co`): **`re.finditer` over
each file's bytes, iterated across an `os.walk` enumeration of the whole tree** (`.git`, `.venv`,
`__pycache__`, the tool caches excluded). The walk is a deliberate **superset** of `git ls-files` —
**1019 walked paths vs 720 git-listed** — so it independently validates the enumeration rather than
inheriting its blind spot, and it is what surfaces the three ignored files (`worker-memory/worker-1.md`,
`worker-memory/worker-2.md`, one `docs/shadow/` overview) that `git ls-files -co --exclude-standard`
cannot see. Occurrences, never lines, throughout.

| Withdrawal's claim | re-derived here | verdict |
|---|---|---|
| `TODO-BETA-062-0.1.5` in `.py`, tree-wide | **0 occurrences, 0 files** (582 `.py` walked) | holds |
| version-less `TODO-BETA-062` in `.py` | **0 occurrences, 0 files** | holds |
| `TODO-BETA-066-0.1.5` in `.py` | **2 occurrences, 2 files** — `apps/products/schema.py` 1, `test_query/test_products_api.py` 1 | holds |
| `spec-037` spec: `062-0.1.5` / `066-0.1.5` | **0 / 2** (bare `062` also 0) | holds |
| `spec-037` companion: `062-0.1.5` / `066-0.1.5` | **0 / 3** (bare `062` also 0) | holds |
| 34 occurrences across 8 spec-surface files | **34 across 8**, file for file and digit for digit | holds |
| `git grep -cF` under-reports the same 8 by 8 | **26 matching lines vs 34 occurrences; delta 8** | holds |
| the per-file line deficits | `appx/spec-033-rationale` 11-on-5 (**-6**), `spec-032` 5-on-4 (**-1**), `appx/spec-032-rationale` 2-on-1 (**-1**); every other file 0 | holds |

The 8-file table reproduces exactly: `appx/spec-033-…-rationale` 11, `spec-033` 6, `spec-032` 5,
`spec-042` 4, `spec-041` 3, `spec-030` 2, `appx/spec-032-…-rationale` 2, `spec-044` 1.

**Instrument failability, before any zero was trusted.** Four controls, every mutated copy written to a
scratch path **outside the repository**; no tracked file was written and Worker 3's source carve-out was
never exercised:

| Control | expectation | result |
|---|---|---|
| a random impossible token (`TODO-BETA-062-0.1.5-<random hex>`) over all 1019 walked paths | 0 | **0** |
| `docs/SPECS/spec-030-connection_field-0_0_9.md`, known carrier | non-zero | **2** |
| same file copied to scratch with one occurrence planted | 3 | **3** |
| same file copied to scratch with the token replaced by `066` | `062`=0, `066`=2 | **0 / 2** |
| a scratch **`.py`** file carrying the token, read by the `.py`-scoped sweep | 1 | **1** |

The last one is the one the `.py` zeros rest on: a `.py`-scoped instrument returning 0 is only evidence
if that same instrument returns 1 on a `.py` file that does carry the token. It does.

**Instrument note, not a finding.** Pass 2's own impossible-token control uses `TODO-BETA-062-0.1.5Z`
and reports 0 over 720 paths. That token is now quoted in this artifact, so re-running that exact control
today returns **1**. Worker 2's run was valid when made (the section did not yet exist), and this is the
same self-reference hazard pass 2 correctly flagged for the tree-wide total — but a control token
published in the artifact it defends stops being impossible, so the next pass needs a fresh one. Recorded
because it generalises; it grades nothing in this cohort.

### Low:

#### L1 — recorded, and its quantification is exact

Pass 2 carries L1 under `### Implementation notes` ("**L1, recorded as an instrument lesson**"), where
the custodian reads it, and my own pass-1 `### Low:` entry stands above. Both are reachable from
sections my role's output points at. The quantification re-derived mechanically against the live glob:

- `glob('docs/SPECS/spec-03[4-9]*.md')` matches **6** files; **none** carries the token. **0 of the 34
  sit inside card 056's instrument.**
- **21** sit outside the `03[4-9]` numeral range (`spec-030` 2, `spec-032` 5, `spec-033` 6, `spec-041` 3,
  `spec-042` 4, `spec-044` 1).
- **13** sit in `docs/SPECS/appx/` (11 + 2), outside the directory.
- 0 + 21 + 13 = **34**. Every figure pass 2 states is right, including the overlap remark that
  `spec-033` plus its companion alone account for **17**.

#### L2 — the board figure cited for card 056 is superseded: 48/13 is retired, the row now reads 39/10

`docs/builder/bld-037-review-1-residue_repair_source.md:730-733` cites card `TODO-ALPHA-056-0.0.17`'s
scope row as re-measuring the surviving population at "48 occurrences across 13 surfaces". Read
read-only today, that row instead reads **`39 occurrences across 10 surfaces`**, and says of its own
predecessor: the 48/13 figure "was measured minutes before this same amendment cut the board-side share",
so "a row stating a live count of a population it is itself editing falsifies itself on write".

**Rejected as this cohort's to fix, with the reason recorded**, on three grounds: the row is behind the
maintainer's fence and out of both cohorts; Worker 2 cited it explicitly **as the board's, not
re-derived as mine**, which is the correct handling of a concurrently-written surface and is why this is
a superseded citation rather than a false claim; and the row moved after Worker 2 read it. Recorded here
so the custodian carries the live number and does not propagate the retired one.

Worth saying because it is corroboration and not just a correction: **my own census independently
reproduces the board's 39/10 partition** — `docs/SPECS/` **34** in 8 files, `TODAY.md` **3**,
`docs/builder/DONE/build-034-permissions-0_0_10.md` **2**, total **39 across 10**, with the card's own
two self-quoting rows excluded. Two instruments that have never seen each other agree on the partition,
not merely the total.

### DRY findings

None, and none possible: this pass adds no code, no test, no helper and no literal — it appends prose to
one artifact. My pass-1 DRY analysis of the diff (and the recorded rejection of the "shared card-id
constant" existence challenge, on the grounds that a `#` comment cannot read a constant) stands unchanged
and is not re-fought here.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` — **empty** (0 lines). `__all__` and the re-export
list are unchanged. The cohort still touches no package source at all.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

`Not applicable; slice did not modify CHANGELOG.md.`

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

`Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.` Confirmed by measurement,
not by assertion, and attributed rather than assumed:

- **The 34 are untouched.** `git status --short -- docs/SPECS/` lists only the `spec-037` pair (cohort
  A's, `M` on the spec and `??` on its companion). **None of the 8 files carrying the 34 is dirty.**
- **The fenced surfaces are dirty from work that is not this cohort's.** `KANBAN.md` (+4/-2) and
  `KANBAN.html` (+1/-1) change only lines carrying `TODO-BETA-062`/`066` — the board-side card-056
  amendment, out of my fence to verify and not cohort B's. `examples/fakeshop/db.sqlite3` is its binary
  source. `docs/GLOSSARY.md` (+18) and `docs/TREE.md` (+2) carry **zero** changed lines mentioning
  either id, so they are unrelated concurrent work. `CHANGELOG.md` is clean.
- This artifact shows `??` (never tracked); `docs/builder/worker-memory/` is ignored at
  `.gitignore:188`, so neither worker-memory file can appear in a status listing at all.

### What looks solid

**The source diff is still exactly the accepted diff.** Re-derived from scratch, not carried over from
pass 1: `git show HEAD:<path>` into a scratch path outside the repository, then `diff -u` per file.

| File | hunks | `-` lines | `+` lines | tokens changed |
|---|---|---|---|---|
| `examples/fakeshop/apps/products/schema.py` | **1** | **1** | **1** | 1 (`062-0.1.5` -> `066-0.1.5`, line 238) |
| `examples/fakeshop/test_query/test_products_api.py` | **1** | **1** | **1** | 1 (same, line 2253) |

No third hunk, no whitespace change, no reflow, no re-tensing, no provenance note. `git status --short`
on the two paths lists ` M` on exactly those two. `scripts/check_trailing_commas.py --check` on both
exits **0** (the ASCII gate too). Pass 2's claim that it did not reopen the diff holds at the byte level.

**Pass 2's own arithmetic is internally consistent where it can be checked.** Its "45 occurrences across
12 surfaces" is `83 across 17` (the `git ls-files` enumeration, which is what it used) minus the 5
builder artifacts carrying 38. My walk sees `86 across 20` because it additionally reaches three ignored
files. Both readings are correct for their stated populations; the difference is the enumeration, which
is exactly the parameter pass 2 declared.

**The board-surface discrepancy pass 2 flagged is real and benign.** It measured `KANBAN.md` 2 /
`KANBAN.html` 2 where my pass 1 measured 3 / 3, and attributed it to the board being rewritten between
the readings. Confirmed: both now measure **2**, and the card-056 row's own text says the amendment cut
the board-side share. Separately, pass 1's instrument (`grep -rIlF`) skips binary files by construction,
which is why `examples/fakeshop/db.sqlite3` (**4**) appears only in the byte-level censuses. Neither
figure enters the 34, and both are behind the fence.

**Scope discipline.** Two `.py` files unchanged from acceptance, one artifact section appended, one
memory entry. No fenced file was written. No file outside `docs/builder/` was written by me either: every
comparison in this review was between read-only reads or scratch copies outside the repository, so the
source carve-out was never exercised and no revert is owed.

**Failability proofs.** `None; this pass introduced no new boundary.` remains the correct entry and I
audited it as such — a prose-append pass adds no guard, gate, rejection path or conditional, so nothing
meets `BUILD.md` `### What needs a proof`. My mandatory re-run floor is therefore **empty and legally
empty** (`worker-3.md`: "An empty re-run set is legal only when the diff introduces no boundary that
meets the floor"). **No boundary was accepted on Worker 2's record, because none exists.** What I ran in
its place is the analogous control set for a claim-correction pass: the five instrument controls tabled
under M1, all of which are mine and none of which reuses Worker 2's.

**Hot-path budget / floor verification.** `Not applicable; plan declares no hot path.` and `Owned by the
final gate per the plan's declaration.` are both still correct: no runtime code, no per-request work, no
dependency surface.

**Tests.** Verbatim, my own run of the recorded scope:

```
uv run pytest examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products --no-cov -q
============================= 192 passed in 35.85s =============================
```

192 items, 8 workers, **zero failures, zero collection errors** — the fourth consecutive 192-row green
(build pass, review pass 1, build pass 2, this pass). **No attribution is owed**: none of the four known
pre-existing failures owned by concurrent sessions
(`tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key`,
`tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration`,
two rows in `tests/test_sets_mixins.py`) lies inside this scope, and none appeared.

### Temp test verification

None. No temp test under `docs/builder/temp-tests/` was created or needed, and none exists to dispose of.
`scripts/review_inspect.py` was **not run** — its value is control-flow shadowing and repeated-literal
evidence, and a pass that appends prose to an artifact offers neither; the repeated-literal question was
already discharged by pass 1's full card-id multiset census of `schema.py`.
`scripts/prove_failability.py` was not run because the diff introduces no boundary. No shadow file was
used.

### Notes for Worker 1 (spec reconciliation)

- **Carry `39 occurrences across 10 surfaces`, not `48 across 13`** (L2). The artifact's last bullet
  cites the retired figure. The live card-056 row reads 39/10 and my independent census reproduces its
  partition exactly (`docs/SPECS/` 34 in 8 files, `TODAY.md` 3, `docs/builder/DONE/build-034` 2), with
  the card's own two self-quoting rows excluded. Nothing to fix in this cohort; do not propagate 48/13.
- **Escalated, still open and still not this cohort's: who sweeps the 34?** My pass-1 escalation stands
  unchanged — resolution paths (a) fold into card `TODO-ALPHA-056-0.0.17`, (b) card a separate
  `062` -> `066` tree sweep, (c) rule that archived specs keep their as-shipped ids (rejected on the
  evidence: the 2026-08-07 sweep itself rewrote the id across archived specs). The board has since moved
  toward (a) — the row now names this round's discharge and re-measures the remainder — but the routing
  call is the maintainer's, not mine, and I record it as still open rather than as settled by a board
  edit I am fenced out of verifying.
- **Whichever pass closes card 056 must re-derive with the bare token over an enumerated whole-tree file
  list** (L1), never a `spec-03[4-9]` glob: 0 of the 34 are inside that glob. State the enumeration as a
  parameter of the figure — `git ls-files -co` and `os.walk` legitimately disagree by three ignored
  files, and a line-oriented count under-reports this specific population by 8 (24%).
- **`spec-037` and its companion measure `062 = 0`.** Re-confirmed today: the spec reads `066` twice,
  the companion three times, and neither carries any `062` spelling. Cohort A's R1 is closed on disk.
- No spec amendment is owed by this cohort and none was authored. Both spec files were read-only here.

### Review outcome

`review-accepted`.

The dispatched work — finding **R3** — was correct, complete and minimal at pass 1 and is byte-identical
now. **M1 is discharged**: the append is the corpus-correct instrument, the withdrawal names and retires
the false clause rather than softening it, and every claim replacing it is true by my own measurement.
**L1** is recorded where the custodian reads it and its quantification is exact. **L2** is recorded with
its rejection reason and is not this cohort's to fix. No finding survives without a recorded disposition,
and no new Medium or High exists.

---

## Final verification (Worker 1)

Fresh spawn. Every number below was **re-derived as it was written**; nothing is read off the plan, either build report, or either review. This pass wrote exactly two files: this artifact and `docs/builder/worker-memory/worker-1.md`. It edited no `.py` file, no test, no spec, and no board or closeout surface. `git stash` / `git checkout --` / `git restore` were not used at any point, and no `--cov*` flag was passed to anything.

### Spec status-line re-verification (this spawn)

`docs/builder/worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`. Read `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` lines 1-60 in this spawn.

- The header reads `Shipped in 0.0.11 (card DONE-037-0.0.11)` and `Status: **SHIPPED (0.0.11)** ... all four slices final-accepted`. Round 1 changed two spec lines (Decision 5's re-export sentence and two card-id renumbers); neither touches a completion claim, so no status line is falsified.
- No "not yet shipped" / "remains to be" claim survives anywhere in lines 1-60.
- **No reference points at a predecessor doc this cycle retired.** This cycle retired nothing — Slice 0 *created* `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md` rather than deleting a doc. Re-derived rather than assumed: all **73** link definitions in the spec and all **36** in the companion resolve to a file that exists on disk, with `undefined refs = []` and `unused defs = []` in both files (fragments stripped before the disk check — leaving them attached produces 36 false "missing" rows and reads exactly like a regression).
- The header's `mutations/inputs.py::model_column_write_annotation` citation still resolves (`check_citations.py` exit 0 below).

**No status-line edit was owed, and none was made.**

### Dispatched-findings tick audit

One box, `- [x]`, audited against the files rather than against this artifact's prose.

| Box | Contract as dispatched | Landed? | Evidence |
| --- | --- | --- | --- |
| R3 | both `.py` comments renumbered `TODO-BETA-062-0.1.5` -> `TODO-BETA-066-0.1.5`; comment-only, with the inverse proof that no behavior moved | **yes** | `git show HEAD:<path>` into a scratch path outside the repo, then `diff -u`: **one hunk per file, one `-`/`+` pair, one token each** (`schema.py:238`, `test_products_api.py:2253`). Nothing else changed in either file. |

**No over-tick, no under-tick, nothing deferred** — the single box's contract landed in the files, so no deferral reason is owed on a checklist box.

Both of the box's rule-27 citations resolve today: `schema.py #"Still deferred to"` (stable neighbourhood, survives the fix) and `test_products_api.py #"those stay TODO-BETA-066-0.1.5"` (written against the **post**-fix text, so it does not die on the edit it describes). Recorded as an observation, not a finding: quoting the pre-fix token would have been the defect.

### Every claim of the round, re-derived

Occurrences throughout, never lines. The population is an `os.walk` enumeration of the whole tree with `.git` / `.venv` / `__pycache__` / the tool caches excluded, **1019 paths**, size printed. Negative control: a **freshly randomized** token of the shape `TODO-BETA-062-0.1.5-<12 random uppercase alphanumerics>`, generated at run time, returns **0** over all 1019 paths. **Its literal is deliberately not reproduced here.** Pass 2's control `...-0.1.5Z` is quoted in this artifact and now returns **non-zero** (no digit is given: each quotation of it moves the figure, which is the point), and pass 2's own tree-wide total moved the same way as its section grew: a control token published in the artifact it defends stops being impossible, and a count published inside its own population stops being true. Every later pass generates its own.

| Claim | Instrument | Result | Verdict |
| --- | --- | --- | --- |
| `spec-037` spec carries 0 `TODO-BETA-062-0.1.5` | byte count over the walk | **0** | holds |
| `spec-037` spec carries 2 `TODO-BETA-066-0.1.5` | same | **2** | holds |
| companion carries 0 / 3 | same | **0 / 3** | holds |
| `.py` tree carries 0 of the stale id | byte count over **582** walked `.py` files | **0 occurrences, 0 files** | holds |
| `.py` tree carries exactly 2 of the new id | same | **2 occurrences**, `examples/fakeshop/apps/products/schema.py` and `examples/fakeshop/test_query/test_products_api.py` | holds |
| the version-less `TODO-BETA-062` in `.py` | same | **0** | holds |
| `grep -c 'UploadDefinition' django_strawberry_framework/__init__.py` | as written | **0** | holds |
| `scalars.py` exports both | `__all__` read at source | `"Upload"` and `"UploadDefinition"`, both imported from `strawberry.file_uploads.scalars` | holds |
| Decision 5's rewritten sentence matches the source | read spec:991-994 against `__init__.py` / `scalars.py` | "`scalars.py` therefore only **re-exports** `Upload` and its `UploadDefinition` ... and the package root ([`__init__.py`][init]) re-exports `Upload` alone" — true in both halves | holds |
| the 8-file spec-surface residue is 34 | same byte instrument | **34 across 8**, file for file: `appx/spec-033-rationale` 11, `spec-033` 6, `spec-032` 5, `spec-042` 4, `spec-041` 3, `spec-030` 2, `appx/spec-032-rationale` 2, `spec-044` 1 | holds |
| a line count under-reports that population by ~24% | occurrences vs matching lines over the same 8 files | **34 occurrences on 26 lines; deficit 8 = 23.5%** | holds |
| the 18 deliberately-untouched ids in `schema.py` did not move | `grep -oF` against the `HEAD` blob and the working copy | `046` 7/7, `047` 5/5, `049` 6/6 — **18 before, 18 after** | holds |

**The `.py`-scoped zero rests on a positive control**, because a `.py`-scoped instrument returning 0 is only evidence if the same instrument returns 1 on a `.py` file that does carry the token: a scratch `.py` written **outside the repository** carrying the token counts **1**.

**What the walk sees outside this cycle's own scratch, so a later whole-tree census can subtract correctly.** **No tree-wide total is stated here, deliberately**: this artifact quotes the token, so any total including the recording surface moves as this section grows and would falsify itself on write — the same defect that retired the 48/13 figure below. The stable partition of `TODO-BETA-062-0.1.5`, all figures dated **2026-09-02** and **excluding every per-cycle `docs/builder/` artifact and `worker-memory/` file** (self-referential, correctly quoting the finding's own wording, and closing with the cycle):

| Partition | Occurrences | Disposition |
| --- | --- | --- |
| durable non-board surfaces (`docs/SPECS/` 8 files, `TODAY.md`, `docs/builder/DONE/build-034-permissions-0_0_10.md`) | **39** | catalog item 1, owned by card `TODO-ALPHA-056-0.0.17` |
| board surfaces (`examples/fakeshop/db.sqlite3` 4, `KANBAN.md` 2, `KANBAN.html` 2) | **8** | renders of two `CardItem` rows that quote the id inside sentences declaring it stale; fenced, and excluded from the sweepable total |
| `docs/shadow/examples__fakeshop__test_query__test_products_api.overview.md` | **1** | regenerable generator output captured before R3 landed, owned by `scripts/review_inspect.py`; not a surface and not a finding |

### Chronology: the spec still narrates none

The fifteen-shape instrument re-run against whitespace-flattened text with newlines included, case-insensitively, so a phrase wrapped across two lines cannot hide.

- **Spec total: 2**, both `previously`, at **L178** and **L1357** — the identical result Slice 2, the integration pass, the final gate and cohort A each recorded and cleared. Each describes what the shipped *code path* used to do (the write input this card converted from fail-loud to `Upload`), which is contract, not spec self-narration. `as of`, `round `, `used to`, `no longer`, `superseded`, `post-ship` and the other eight are all **0**. **The count has not grown; round 1 introduced no chronology into the spec.**
- Instrument failability, same run: the companion returns **47 occurrences with 14 of the 15 shapes live**. A zero from a mistyped pattern would show as a zero there too.

### Gates, verbatim

```shell
$ uv run python scripts/check_citations.py
OK: 942 citations resolve (781 in 435 .py files, 161 in KANBAN.md).
exit=0
```

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
OK: 20 terms - all have glossary entries and at least one spec link.
exit=0
```

```shell
$ uv run python scripts/check_trailing_commas.py --check \
    examples/fakeshop/apps/products/schema.py \
    examples/fakeshop/test_query/test_products_api.py \
    docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md \
    docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md
exit=0
```

That gate exits 0 silently, which is indistinguishable from an unrun gate, so it was **proved failable** first: a scratch `.py` outside the repository carrying one em dash and an unexploded 5-argument call gives

```
<scratch>/ctl-037-gate.py:1:6: non-ASCII U+2014 '—' not allowed in .py (ASCII + emoji only)
1 non-ASCII char(s) in .py; replace with ASCII (emoji allowed)
exit=1
```

The two `.py` paths alone also exit 0. The two `.md` paths are inside the scaffold corpus (unlike the `bld-*.md` artifacts pass 2 correctly recorded as *excluded*), so their 0 is a pass rather than an exemption.

```shell
$ uv run pytest examples/fakeshop/test_query/test_products_api.py examples/fakeshop/apps/products --no-cov -q
8 workers [192 items]
============================= 192 passed in 35.91s =============================
```

**192 items, 8 workers, zero failures, zero collection errors — the fifth consecutive 192-row green** (build pass, review pass 1, build pass 2, review pass 2, this gate). **No attribution is owed**: none of the four known pre-existing failures owned by a concurrent session (`tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key`, `tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration`, two rows in `tests/test_sets_mixins.py`) lies inside this scope, and none appeared. A count of **192 collected items** is what makes the zero a measurement rather than an empty selection.

### L2, decided: the correction is owed, and this section is where a worker can make it

Worker 3 recorded L2 — pass 2's last bullet cites card `TODO-ALPHA-056-0.0.17` as re-measuring the surviving population at "48 occurrences across 13 surfaces", a figure the board has since retired — and rejected fixing it as out of cohort B's scope. **That rejection is correct and the correction is still owed**, because a retired number left standing in the round's last Worker-2 text is what the next reader carries forward. Three constraints fix where it can go:

- **Not in Worker 2's build report.** `ARTIFACT.md` `## Re-pass sections` and `worker-2.md` `## Scope` forbid editing a prior entry unconditionally, and Worker 3 already established that no worker at all may place a forward pointer at the original site.
- **Not in cohort A's artifact.** Its `### Routed to the maintainer` table carries the same 48/13, and it is `final-accepted`. It was **true on its date** — measured after cohort A's edits and before the board amendment — and reopening a closed artifact to overwrite it would destroy the evidence that a live count of a population the recording surface is itself editing falsifies itself on write. That is the round's most transferable lesson; it survives only if the superseded figure stays on the record with its supersession stated elsewhere.
- **Not on the board.** Fenced, and the row already carries the corrected figure and the reason.

So it lands here, dated, in the section this role owns.

**Carry `39 occurrences across 10 surfaces`, measured 2026-09-02. Do not propagate `48 across 13`.** Re-derived by me over the 1019-path walk, independently of both the board row and Worker 3's census, and reproducing the partition rather than only the total:

| Surface | Occurrences |
| --- | --- |
| `docs/SPECS/` (8 files, the table above) | 34 |
| `TODAY.md` | 3 |
| `docs/builder/DONE/build-034-permissions-0_0_10.md` | 2 |
| **Total, 10 surfaces** | **39** |

Three instruments that have never seen each other — the board row's, Worker 3's `re.finditer` walk, and mine — agree file for file. The 48/13 figure counted nine board-surface occurrences (`KANBAN.md` 3, `KANBAN.html` 3, the DB 3) that are renders of the **same two `CardItem` rows**, which quote the stale id inside sentences declaring it stale; a census summing the DB and both renders triple-counts one fact.

**Any restatement of this count must be dated and must exclude the recording surface's own occurrences.** Mine excludes the board rows and this cycle's own scratch, and states the enumeration (`os.walk`, 1019 paths) as a parameter of the figure.

### Deferred work catalog

`docs/builder/BUILD.md` `## Final test-run gate`. Every artifact of this round — both cohorts' plans, build reports, reviews and re-passes — plus the cycle's own `bld-037-*` artifacts were walked for items explicitly routed forward. **Three items, each with its measurement, its date and a named owning card.**

1. **The `TODO-BETA-062-0.1.5` -> `TODO-BETA-066-0.1.5` renumber survives in 39 occurrences across 10 durable surfaces.** Owner: `KANBAN.md` card **`TODO-ALPHA-056-0.0.17`** (heading at `KANBAN.md:588`, row at `:612`), which already carries the population, the discharge this round made, and the corrected figure. Source: this artifact's `### Notes for Worker 1 (spec reconciliation)` (Worker 2 pass 2) and `### Low: L2` (Worker 3 pass 2); cohort A's `### Routed to the maintainer`. No spec line licenses the deferral — the round's fence does, and 8 of the 10 surfaces are archived specs and `appx/` companions outside both cohorts. Measured 2026-09-02: `docs/SPECS/` 34 in 8 files, `TODAY.md` 3, `docs/builder/DONE/build-034-permissions-0_0_10.md` 2. **Whoever discharges it must sweep the bare token over an enumerated whole-tree file list, counting occurrences**: a `docs/SPECS/spec-03[4-9]*.md` glob matches 6 files and reaches **0 of the 39**, and a line-oriented count under-reports the spec-surface share by 8 (23.5%).

2. **The class-wide maintainer ruling on rule-27 citations that quote a since-deleted source comment. Population 2, not the 5 the card records.** Owner: the maintainer, held on card **`TODO-ALPHA-056-0.0.17`**, whose row already states the corrected population. Source: cohort A's `### Routed to the maintainer` and the build plan's `### Not dispatched, and why`. The two live citations, cited by content because line numbers drift (the card's "companion ~826" is now **841**, moved by cohort A's appended `**Post-ship:**` bullet):
   - `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` — `[mutations/inputs.py][mutations-inputs] #"Upload staged seam (TODO-ALPHA-037-0.0.11)"` (spec:459);
   - `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md` — `[scalars.py][scalars] #"Future scalars (e.g. ``Upload`` per TODO-ALPHA-035-0.0.11) land here."` (companion:841).

   **Both source anchors confirmed gone**, re-derived here: `grep -c 'Upload staged seam' django_strawberry_framework/mutations/inputs.py` -> **0** and `grep -c 'Future scalars' django_strawberry_framework/scalars.py` -> **0**, against a positive control on the same instrument (`grep -c 'models.FileField: str' django_strawberry_framework/types/converters.py` -> **1**), so the zeros are measurements. The other two of the four `#"..."` occurrences in the pair are a plain-prose quotation and a mention of the anchor *as a subject* (companion:558, inside a sentence explaining that it resolves to nothing) — neither is a `path #"substring"` citation and neither is in the ruling's population. **No gate can see any of this**: `check_citations.py` is `path::Symbol`-only with `docs/` out of scope, and it exits 0 while both dangle.

3. **No file-column read-side `Meta.exclude` test, and the grading that licensed the gap expires with card 054's refactor.** Owner: `KANBAN.md` card **`TODO-ALPHA-054-0.0.16` — Pluggable field-conversion registry** (heading at `KANBAN.md:470`, scope row at `:494`, with a `related` reference to `DONE-037-0.0.11` at `:526`). Source: `bld-037-slice-1-code_conformance.md` `### Notes for Worker 1 (spec reconciliation)`, `Not a finding, do not re-raise` item (b), carried into `bld-037-final.md`'s catalog as item 5 and re-homed by this round's board-DB enactment. No spec line licenses it. The Low grading rested on `Meta.exclude` being name-keyed with **no** file branch in `types/base.py::_select_fields`, so excluding a file column takes the scalar path; card 054's own scope deletes the `FIELD_OUTPUT_TYPE_MAP` / `resolvers._attach_file_resolvers` special cases and routes the file family through a bundle entry, which un-shares that path. One row — an excluded file column appears in neither the SDL nor the resolver set — **landing before the migration** is what makes card 054's `#"Fakeshop SDL byte-identity test"` DoD item measure the file family rather than confirm whatever the refactor produced. Both board rows were confirmed present read-only at this gate.

**Closed by measurement, explicitly not deferred — do not re-open.** Recorded so the next author can tell a settled ruling from an open item:

- `bld-037-final.md` deferred items **2 and 3** are **struck**: `docs/GLOSSARY.md` is already correct for `DjangoFileType`, `DjangoImageType`, `Meta.required_overrides`, `DjangoFilePathType` and `DjangoImagePathType`, and `docs/TREE.md` carries only module one-liners. Correcting that catalog's "nobody has checked" wording would be a `bld-*.md` edit on a closed artifact and is outside the fence.
- `bld-037-final.md` deferred item **4** (the build plan's wrong `spec-048` release version) is **closed** — Worker 0 corrected the plan and the final gate verified zero `0.0.17` occurrences in the plan, the spec or the companion.
- `bld-037-final.md` deferred item **1** (four rows failing the full package sweep) is unchanged and remains the maintainer's: it is out of this round's scope entirely, and none of the four lies inside this round's test scope.
- Slice 1's single Low (the third test's annotation assertion overlap) was ruled **keep as-is** at that slice's final verification, with one clause of the finding refuted at source.

### Findings raised by this pass

Two Lows, both behind the maintainer's fence, **reported and not touched**, both owned by whoever closes card `TODO-ALPHA-056-0.0.17`:

- **Low — the board row's own board-side arithmetic reads 6 where the bytes read 8.** Card 056 states the amendment "cut the board-side share from 9 surface-occurrences to 6". Measured by byte count on 2026-09-02: `KANBAN.md` **2**, `KANBAN.html` **2**, `examples/fakeshop/db.sqlite3` **4** = **8**. The row's *point* holds — those are renders of two `CardItem` rows and must not enter the sweepable total — but the DB carries four raw-byte hits for two rows, so the stated 6 is not what the surface measures. It changes nothing about the 39/10 figure, which excludes all of them.
- **Low — the card's `companion ~826` address for the second dangling rule-27 citation is now `841`.** Cohort A's appended `**Post-ship:**` bullet shifted the companion by 16 lines. Cite that citation by content, not by ordinal or line.

Neither is this round's to fix, and neither blocks.

### DRY check across this round and the prior accepted slices

No new duplication, and none possible: this pass writes no `.py` file, no helper, no constant and no test. Cohort B's whole diff is two prose tokens; cohort A's is one rewritten sentence, five renumbers, one corrected framing clause, one appended bullet and one link definition. `git diff -- django_strawberry_framework/__init__.py` is **empty**, so no public export changed. The one duplication risk a residue repair carries — restating the companion's explanation inside the spec — is controlled by the chronology sweep above, and it is clean at 2 pre-existing hits.

### Failability proofs

`None; this pass introduced no new boundary.` This pass lands no runtime code. The proof obligations it *does* carry are the measurements above, and **each carries its own control**, which is what makes a zero mean something:

- the tree-wide census is paired with a **freshly randomized** impossible token over the same 1019 paths (0), because pass 2's published control token is spent;
- the `.py` zero is paired with a scratch `.py` **outside the repository** that does carry the token (1), so a `.py`-scoped instrument's blindness would be visible;
- the `062` sweep is paired with a `066` sweep of the replacement vocabulary (spec 2, companion 3, `.py` 2), so a zero produced by deleting the subject is distinguishable from one produced by fixing it;
- the two dangling-anchor zeros are paired with a live anchor read by the same instrument (`models.FileField: str` -> 1);
- the silent `check_trailing_commas.py --check` exit 0 is paired with a scratch `.py` that makes it exit 1 with a message;
- the chronology sweep is paired with the same fifteen shapes over the companion (47 occurrences, 14 of 15 shapes live);
- the test run's zero failures is paired with its printed **192 collected items**, so an empty selection is distinguishable from a green one.

**No fail-open shape landed.** The round's entire diff is prose: no expression, guard, default or `except` that could silently substitute a permissive answer.

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Owned by the final gate per the plan's declaration`, and there is nothing to run: the round writes no `.py` executable code and touches no dependency surface, so it adds no framework seam and declares floor-verification scope **none**. The cycle's one declared scope was Slice 1's, owned and run by its Worker 2 pass in `/tmp/dsf-floor-037` (Python 3.10.19 / django 5.2.16 / strawberry-graphql 0.316.0, `6 passed`), confirmed at Slice 1's final verification and again at `bld-037-final.md`. This round is not a second owner. The shared `.venv` was not installed into, downgraded or otherwise mutated by this pass.

### Concurrent-session attribution

Many paths are dirty from other sessions; none was edited, reverted, tidied, or run through an auto-fixer. Attributed by **diff content**, never by a file list:

- `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3` — the board-DB enactment made by this round's dispatcher under the maintainer's explicit grant. Read-only here; **not mine to verify or change**.
- `docs/GLOSSARY.md` (+18) and `docs/TREE.md` (+2) — concurrent work. Measured, not assumed: `git diff -- docs/GLOSSARY.md docs/TREE.md | grep -c 'TODO-BETA-062\|TODO-BETA-066'` -> **0**. Neither diff mentions either card id, so neither belongs to this round.
- The two owned `.py` paths show ` M` and carry exactly the two accepted one-token hunks.
- The spec pair now measures **1,666 lines / 104,976 bytes** and **987 lines / 62,268 bytes**, against the final gate's pre-round record of 1,666 / 104,947 and 971 / 61,019 — the growth is exactly cohort A's recorded edits (a same-length renumber x5, one rewritten sentence, one appended bullet, one link definition, one corrected clause), which proves no third party has written either file since.

### Summary

Round 1 renumbered a dead card id at **7 sites** — five in the `spec-037` spec/companion pair (cohort A) and two `.py` comments (cohort B) — and corrected Decision 5's false package-root export claim. Cohort B's single dispatched finding landed as two one-token hunks with a provably inert diff; the tick is correct; the `.py` population of the stale id is **0** tree-wide and the replacement occurs at exactly the **2** replaced sites. All four gates pass, three of them with a control proving they could have failed. The spec still narrates no chronology (2 pre-existing hits, unchanged). The retired 48/13 figure is superseded here by **39 occurrences across 10 surfaces**, dated and excluding the recording surface's own rows, rather than by editing a closed artifact or another worker's report. Three deferred items are homed on named cards; two new Lows are reported behind the fence.

### Spec changes made (Worker 1 only)

**None.** This pass's fence covers `docs/builder/bld-037-review-1-residue_repair_source.md` and `docs/builder/worker-memory/worker-1.md` only, and nothing found here needed a spec edit — cohort A's R1 and R2 are closed on disk and independently re-verified above. **Proved by non-edit rather than asserted:** the spec pair's line and byte counts are unchanged from cohort A's post-edit state (see `### Concurrent-session attribution`).

**No deferral reasons are owed** on a checklist box: the round's one cohort-B box is ticked with its contract landed in the files.

### Final status

`final-accepted`. The dispatched-findings box is audited against the files and correctly ticked; every claim of the round is re-derived here with a printed population and a live control; all four gates pass and the silent one is proved failable; the focused scope is a fifth consecutive `192 passed` with zero failures owed to anyone; the deferred-work catalog is written with three items on named owning cards and four settled items marked do-not-re-open; and Worker 3's open L2 is decided and discharged in the only section a worker may write it. Review round 1 is closed. Worker 0 may tick the build plan's `### Round checklist` cohort-B box.

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
