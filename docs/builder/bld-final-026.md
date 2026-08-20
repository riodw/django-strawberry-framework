# Build: Final test-run gate (026)

Spec reference: `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` (whole file; 21,567 bytes, unchanged by this pass)
Status: final-accepted

Worker 1 alone, per `docs/builder/build-026-scalar_conversion_fakeshop-0_0_7.md` `Ownership partition: none`. This is the last pass of the cycle. `docs/builder/bld-integration-026.md` closed `final-accepted` and is the contract this gate audits.

**Closeout is deliberately not part of this pass**, excluded by the maintainer's dispatch: no closeout retrospective, no edit to `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, or any `docs/builder/worker-*.md` role file, no KANBAN / GLOSSARY / CHANGELOG movement, no card wrap, no `-terms.csv` edit. A later reader should read those absences as scope, not omission.

---

## Plan (Worker 1)

### DRY analysis

- **What is reused.** Every instrument this pass runs is one the cycle already established: occurrence counting via `grep -o | wc -l` (never `grep -c`), read-only HEAD reference via `git show HEAD:<path>` into a scratch path outside the repo, and the D2/D3 rule that a claim quantifying over something outside its own file is the defect. No new instrument was invented except one, justified below.
- **What is new and why.** A docstring-stripped **AST identity comparison** against HEAD, because the whole cycle rests on the claim "zero executable lines changed" and until this pass that claim was supported only by reading the diff. Reading a four-hunk diff and concluding "all prose" is the same shape of unmeasured claim the cycle spent three slices retiring. The comparison decides it mechanically and it is what grounds both the floor-scope confirmation and the pytest decision below.
- **Duplication risk avoided.** This artifact states no number as contract that the spec or the rationale owns. Where a figure appears in both, the spec or rationale owns it and this file names the instrument that re-derived it.

### Implementation steps

1. Run the lint / format / diff gate, all read-only, never `--fix`.
2. Run `check_trailing_commas.py --check` three ways — repo-wide, over every tracked candidate, over this cycle's own diff.
3. Run `check_spec_glossary.py --spec <spec-026>`.
4. Decide `pytest` / `manage.py check` / `makemigrations --check --dry-run` against the governing authority and record the decision with that authority.
5. Confirm the plan's `Floor-verification scope: none` against the landed diff.
6. Re-derive every deferred-catalog locator from scratch, and every spec claim cheaply re-derivable, measuring each number as it is written.
7. Separate what the cycle **decided** from what it **deferred**.

### Test additions / updates

None, and none possible: the cycle writes no Python statement. See `### The pytest / manage.py decision` for why no suite was run and on whose authority.

### Implementation discretion items

None. There is no second worker to delegate to.

### Dispatched findings checklist

Not a review round. The boxes are this gate's own obligations from `docs/builder/BUILD.md` `## Final test-run gate` and `## Floor verification`, plus the deliverable the dispatch names, decomposed so the audit at the close has something to audit.

- [x] `uv run ruff format --check .` — read-only, no `--fix`
- [x] `uv run ruff check .` — read-only, no `--fix`
- [x] `git diff --check`
- [x] `uv run python scripts/check_trailing_commas.py --check` repo-wide, plus the two scoped runs the dispatch requires
- [x] `uv run python scripts/check_spec_glossary.py --spec <spec-026>`
- [x] `pytest` / `manage.py check` / `makemigrations --check --dry-run` — decided, with the authority recorded, and neither silently skipped nor silently run
- [x] Floor-verification scope `none` confirmed against the landed diff, not accepted from the plan
- [x] The cycle's `.py` diff proved to change zero executable lines, mechanically
- [x] Every deferred-catalog locator re-derived from scratch
- [x] Every per-slice and integration artifact walked for deferred items
- [x] Decided-not-deferred items recorded separately from deferred ones
- [x] Spec and rationale re-swept for census, history narration, links, anchors and citations after the integration pass's six edits

---

## Final verification (Worker 1)

Every number below was measured in this pass. Nothing is inherited from the build plan, from a slice artifact, from `bld-integration-026.md`, or from my own memory file — including numbers those sources and this pass agree on.

### Gate results

| Command | Exit | Output |
| --- | --- | --- |
| `uv run ruff format --check .` | **0** | `424 files already formatted` (plus the standing `COM812`-vs-formatter advisory warning, which is configuration, not a finding) |
| `uv run ruff check .` | **0** | `All checks passed!` |
| `git diff --check` | **0** | no output — no whitespace error, no conflict marker anywhere in the tree |
| `uv run python scripts/check_trailing_commas.py --check` (repo-wide) | **0** | no output |
| `uv run python scripts/check_trailing_commas.py --check $(git ls-files '*.md' '*.py' '*.csv')` — 855 paths | **0** | no output |
| `uv run python scripts/check_trailing_commas.py --check` over this cycle's own diff (the two `.py` files, the spec, the rationale) | **0** | covered by both runs above; the four paths are all inside the 855 |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` | **0** | `OK: 3 terms - all have glossary entries and at least one spec link.` |

**The dispatch's anticipated `check_trailing_commas` failure did not occur, and that is a measurement rather than luck.** The checker's directory walk does not consult `.gitignore`, so a repo-wide run can go red on an untracked, git-ignored non-repository file. Here the repo-wide run exits 0 with no output, so there is nothing to attribute. The two scoped runs were still executed as the dispatch requires, because they are the runs that actually cover the work: repo-wide green could in principle mask nothing here, but the scoped runs are the ones whose population is this cycle's, and both are green independently.

All three of `ruff format --check`, `ruff check`, and `git diff --check` cover the whole tree, so they cover the three baseline-dirty `.py` files belonging to concurrent sessions (`django_strawberry_framework/_strawberry_patches.py`, `django_strawberry_framework/optimizer/hints.py`, `tests/optimizer/test_hints.py`). All three gates are green, so **no gate failure needed attribution to a concurrent session**, and nothing was fixed or reverted in any of them.

### The cycle's landed diff, measured

`git diff HEAD --numstat` over the two `.py` files:

| File | Added | Removed |
| --- | --- | --- |
| `examples/fakeshop/apps/scalars/models.py` | 8 | 6 |
| `examples/fakeshop/test_query/test_scalars_api.py` | 10 | 11 |
| **total** | **18** | **17** |

`git diff HEAD … | grep -c '^@@'` -> **4** hunks. The build plan's and the integration pass's `18 / 17 / 4` all reproduce exactly.

Markdown side: the spec is `177` added / `30` removed (`git diff HEAD --numstat`), 3,593 bytes at HEAD -> **21,567** on disk; the rationale is untracked at **36,728** bytes. Both figures reproduce the integration pass's edit-5 table, so that table is still current at the close of the cycle — which is the specific rot it was fixed for.

### Zero executable lines changed — proved mechanically, not read off the diff

The claim the whole cycle's declarations rest on. Reading four hunks and concluding "all prose" is a judgement; this is a measurement. For each file, HEAD was obtained read-only (`git show HEAD:<path>` into a scratch path **outside** the repo — no `git stash`, `checkout`, `restore`, or `worktree` anywhere in this pass), both versions were parsed with `ast`, **every docstring was stripped** from every module, class, and function node, and the two `ast.dump` strings were compared:

```text
models.head.py       vs examples/fakeshop/apps/scalars/models.py       : IDENTICAL
tests.head.py        vs examples/fakeshop/test_query/test_scalars_api.py: IDENTICAL
```

Comments are absent from the AST by construction and docstrings were removed explicitly, so an identical dump means **every executable construct in both files is unchanged from HEAD**: no statement, no expression, no field declaration, no argument, no decorator, no import. Three consequences, each load-bearing below:

- Model field declarations are executable AST, so **migration state cannot have drifted** — `makemigrations --check` cannot have a different answer than it has at HEAD.
- No Django, Strawberry, or channels API surface is touched, which is the floor-scope question.
- Both files parse, so the one thing a prose-only `.py` diff can actually break — a docstring that no longer terminates — is disproved as a side effect of the comparison succeeding.

### The pytest / manage.py decision

**Decision: `uv run pytest --no-cov`, `examples/fakeshop/manage.py check`, and `makemigrations --check --dry-run` were all NOT run.** Recorded here with authority rather than silently skipped, and no run was silently performed either. No `pytest` invocation of any form was issued in this pass; no `--cov`, `--cov-report`, or `--cov-config` flag was passed anywhere in this cycle.

**Authority.** Three documents govern and they agree:

- `AGENTS.md` #"No pytest after edits" — "No pytest after edits; run only when explicitly asked (then `uv run pytest`)". The dispatch asked me to *decide*, not to run.
- `START.md` "Workflow rules they've set" — "After edits: `uv run ruff format .` … then stop. No `pytest`. No `manage.py check`. No `uv build`." This names `manage.py check` explicitly, not only `pytest`.
- `docs/builder/worker-1.md:13` — "If any instruction conflicts with `AGENTS.md` or `START.md`, follow `AGENTS.md` and `START.md`." `docs/builder/BUILD.md` `## Final test-run gate` is the conflicting instruction, and it loses.

**And independently of precedence, a run would not be evidence about this cycle.** This half stands on its own; if the precedence reading were wrong, the decision would not change.

- The `.py` diff is **AST-identical to HEAD** once docstrings are stripped (proof above). `pytest` executes executable constructs and `makemigrations --check` reads model field declarations; both are exactly what the comparison proves unchanged. There is no mechanism by which either command could return a different answer because of this cycle.
- The tree is dirty with two concurrent sessions' uncommitted work, including three `.py` files on the plan's baseline-dirty list (`_strawberry_patches.py`, `optimizer/hints.py`, `tests/optimizer/test_hints.py`). A green sweep here would be a measurement of **HEAD plus two other sessions' in-flight edits**, recorded in this cycle's closing artifact as though it were this cycle's evidence. That is worse than no measurement: it launders someone else's state into my record. A red sweep would be theirs, attributable but not actionable by me — the plan already forbids fixing or reverting those files.
- `pytest.ini:13` is `addopts = -v -n auto --dist loadscope --cov --cov-report=term-missing`, so a plain `uv run pytest` here is a coverage run and forbidden outright; `--no-cov` would have been the only permitted form had a run been warranted.
- The one executable risk a prose-only `.py` diff carries — an unterminated docstring making a module unimportable — is already disproved by both files parsing under `ast.parse`. The focused live module was additionally run three times during Slice 2 (`29 passed`, `--no-cov`), before the diff reached its current form; that is recorded as history, not offered as this gate's evidence.

**The full sweep is the maintainer's**, together with the `fail_under = 100` coverage gate that `docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool` assigns to CI. Nothing in this cycle changes what either would measure.

### Floor verification

**Scope `none`, confirmed against the landed diff rather than accepted from the plan.** No floor venv was built, and building one for a prose diff would have been the wrong call.

`docs/builder/BUILD.md` `## Floor verification` is the single canonical statement of the floor versions and this artifact deliberately does not restate a floor number, from memory or from any other document. Its `### When it is required` list is the test: request/response handling, view or ASGI plumbing, upload or body parsing, the session/auth surface, queryset or expression compilation, schema and type construction against Strawberry internals, consumer or middleware wiring.

The confirmation is the AST-identity proof above, which is stronger than a seam-by-seam grep: **not one executable construct in the cycle's `.py` diff differs from HEAD**, so no import, no Django/Strawberry/channels call, no model field declaration, and no version-sensitive construct changed — there is no seam for a floor run to exercise. The other three files in the cycle's diff are Markdown and execute nothing on any interpreter. The plan's declaration named no owning pass because there is no run to own, so there is no planned floor verification that went unrun, which is the failure mode this gate is the backstop for.

### Spec and rationale re-swept after the integration pass's six edits

The integration pass made six edits and re-gated after each. Re-swept here independently, because a pass's own post-edit sweep is a claim like any other.

| Check | Spec | Rationale |
| --- | --- | --- |
| link definitions | 26 | 19 |
| distinct reference-style uses | 26 | 19 |
| total use sites | 59 | 37 |
| unused definitions | 0 | 0 |
| dangling uses | 0 | 0 |
| definition paths missing on disk | 0 | 0 |
| broken cross-file `#fragment` | 0 | **1** — `[spec-026-other]`'s `#other`, the deliberate retirement covered by `## Key forwarding` |
| unresolved in-page `](#…)` anchors | 0 | 0 |
| all 10 canonical group headers, present and in order | yes (lines 167-211) | yes (lines 393-430) |

Reproduces the integration pass's table exactly, including that the `#other` fragment is the only unresolved one in either file.

**And my own instrument indicted the file before it indicted itself — again.** The first run reported three broken fragments in the spec and three in the rationale, plus nine unresolved in-page anchors. All nine were my slugger: it collapsed runs of whitespace (`re.sub(r"\s+", "-")`) where GitHub replaces each whitespace character individually, so a heading with an em dash — which GitHub strips, leaving two spaces and therefore two hyphens — slugged to one hyphen. One character in the instrument, six false "broken link" findings. My memory already carries this trap in its underscore form; this is a **new instance of the same class in a different character**, and the standing rule held: a home-grown slugger indicts the file first.

Other sweeps re-run over the final text:

- **`#"substring"` citations:** two, both `#"Test through real usage, prefer the example project"`, and that string occurs in `AGENTS.md` exactly **1** time (`grep -o … | wc -l`), so both resolve uniquely.
- **History narration:** `grep -inE 'previously|used to|no longer|formerly|as of |amend|retract|rev-[0-9]|round [0-9]|earlier version'` -> **1** hit, the header block's companion-pointer sentence, which describes what the rationale *contains*. Confirms the integration pass's one-hit reading and confirms that **Slice 3's audit table is the wrong one** where it says the grep returns 0.
- **Census sweep, both polarities:** **35** occurrences, decomposing as `every` 13 (12 + 1 capitalized), `each` 13 (11 + 2), `all` 5, `only` 4, and zero each of `sole` / `no other` / `the one` / `always`. Reproduces the integration pass's 35 and its decomposition exactly, and again confirms Slice 3's audit table ("21 hits read") is the contradicted half.
- **A fourth sweep vocabulary, run because the cycle's own history says a vocabulary list always has a next gap.** Probed `never` / `nothing else` / `no example` / `exclusiv*` / `lacks` / `unlike` / `elsewhere` / `apart from` / `besides` / `the example tree` / `tree-wide` / `repository-wide` / `unique` / `nowhere` / `first`. Nine hits, every one read in context, **zero census defects**:

| Site | Reading |
| --- | --- |
| `## Non-goals` item 3, "the example tree does carry write surface elsewhere" | an **existential**, not an exclusivity claim. Falsified only by removal, never by growth in another app — the opposite failure mode from a census. True at HEAD (`products/schema.py::DeleteItem`). |
| `## Non-goals` item 1, "neither can be exercised from a live fakeshop request at all" | scoped to two named PostgreSQL-only field types against a SQLite backend. Closed, named population. |
| Decision 2, "No assertion in this card is made against a locally constructed schema" | universal over the card's own nine tests, a closed population named in the sentence. Checked: the live module's only `execute_sync` token is a prose mention inside a docstring (line 757) describing a *package* test; the module issues real requests through `graphql_client.post_graphql`. Holds. |
| `### No example-app test tier for this card`, "the live tier is the correct and only home" | universal over the card's own assertions. Same closed population. |
| four `first` hits | all `live-first` (the repository's coverage posture) or "Skim these entries first". Not censuses. |

**No spec or rationale edit is owed by this gate.** Nothing in any sweep came back false.

### Contract claims re-derived at HEAD

Re-measured here rather than carried from the integration pass, including the ones we agree on.

| Claim | Instrument | Result |
| --- | --- | --- |
| `SCALAR_MAP` has 26 rows; 16 collapse to `int`/`str`; 10 do not | `len()` and the non-`(int, str)` subset | **26 / 16 / 10**, and the ten are `BigIntegerField`, `PositiveBigIntegerField`, `BooleanField`, `FloatField`, `DecimalField`, `DateField`, `DateTimeField`, `TimeField`, `JSONField`, `UUIDField` — exactly the ten the spec names. The spec's "twenty shapes" is these ten in two shapes each. |
| the pair shares one identical set of **eleven** column names, every one required on one side and `null=True` on the other | AST parse of both classes, comparing declared-field sets | **11** shared names; **all 11** non-null in `ScalarSpecimen`; **all 11** `null=True` in `NullableScalarSpecimen`. `ScalarSpecimen` declares 13 fields (the 11 plus `parent` and `tag`), `NullableScalarSpecimen` 12 (the 11 plus `partner`). Exact. |
| `on_delete=models.SET_NULL` in example models | `grep -o … \| wc -l` | **4** — `kanban/models.py:843`, `:995`, `scalars/models.py:133`, `:180` |
| the scalars app declares three FKs, two of them cross-model | `grep -n 'ForeignKey'` plus each target | `parent` (`"self"`, intra-model), `tag` -> `ScalarSpecimenTag`, `partner` -> `ScalarSpecimen`. **Two cross-model.** |
| D11 — the card retired **six** package tests, each with a synthetic `managed = False` owner | `git show a5c89c98 -- tests/types/test_converters.py` (read-only) | **6** deleted `def test_` and **6** deleted `managed = False`, named exactly as the spec's `## Test plan` names them: three `big_integer`/`positive_big_integer`, three `json_field` |
| D5 — the ship module carried **nine** tests, HEAD carries 29 | `git show 2701eb88:<path>` and HEAD, `grep -o '^def test_' \| wc -l` | **9** and **29** |
| the spec carries none of the retired claims | `grep -o … \| wc -l`, four phrases | `only cross-model FK in the scalars app` **0**, `no other example app` **0**, `only \`SET_NULL\` ondelete in the example tree` **0**, `otherwise lacks` **0** |
| the header block's status and target release | `KANBAN.md` card row | `DONE-026-0.0.7` present at `:121` (and in the `0.0.7` seven-card summary at `:62`, and as the Done-column card at `:3814`). `Target release: 0.0.7` and `Status: shipped (0.0.7, 2026-05-27); archived.` both consistent. **No status-line edit owed.** |

One claim this gate **cannot** verify and says so rather than passing it, unchanged from the integration pass: Decision 5's "Package coverage of the underlying rows stays at 100% through the live tests." Every `--cov*` flag is forbidden to every worker pass, so the number is not measurable here. It restates the standing `fail_under = 100` gate rather than asserting a new measurement. Recorded, not graded.

### High:

None.

### Medium:

None.

### Low:

#### A corpus total that includes the cycle's own artifacts is not stable across passes

Deferred item 1's file count was **6** when Slice 3 measured it and is **7** now:

```shell
grep -rln 'only cross-model FK in the scalars app' --exclude-dir=.git .
# KANBAN.md, KANBAN.html,
# docs/SPECS/appx/spec-026-…-rationale.md,
# docs/builder/bld-slice-2-026-…md, bld-slice-3-026-…md,
# bld-integration-026.md, build-026-…md
```

Slice 3's six was correct at Slice 3's moment; the integration pass restated the six and described its composition as "the rationale and three `026` builder artifacts", which was true only for the instant before it wrote its own two copies of the phrase. Neither is a defect worth charging to either pass — the total is a **moving** quantity, because every pass that writes about a retired claim adds a site. **The catalog below therefore states the live sites and their per-file occurrence counts, and states no corpus total**, which is the only form a later reader can re-derive and get the same answer. Every load-bearing figure is unchanged: two live sites, one occurrence each.

#### Slice 3's audit table contradicts its own body twice — confirmed by independent measurement, still not rewritten

Its `### Spec slice checklist audit` says the census sweep read "21 hits" (its own body section says 35) and that the narration grep returned "0 hits" (its own body says one that stays). Measured independently in this pass: **35** and **1**. The body is right in both, the table wrong in both. Recorded, not fixed, for the reason the integration pass gave and this gate agrees with: an accepted artifact is the record of work already done. The corrected figures now live in two later artifacts, so no reader reaches the table without also reaching a correction.

### DRY findings

- **No repeated literal, key, tuple shape, helper, or export anywhere in the cycle.** The AST-identity proof is the strongest possible form of this: the diff adds no Python symbol of any kind, so the usual subjects have no population.
- **The two prose-DRY calls the integration pass decided are re-affirmed, not re-litigated.** The one substantive spec-vs-rationale 9-gram (the `tests/` coverage boundary in `## Non-goals` item 1 and rationale `D6`) stays with the spec as owner; the 19 spec-vs-`.py` 7-grams stay split as they are. The load-bearing property was measured, not asserted: **no shared run carries a number.** Every one is a structural fact about two named models, verifiable from those models, so the two copies cannot drift into disagreeing the way `SET_NULL`-is-4-not-1 did. That is the whole test, and it is why "the same sentence in two places" is not automatically a finding.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` -> empty. No slice of this cycle opened any file under `django_strawberry_framework/`; `__all__` is unchanged. The spec's Decision 6 and definition-of-done item 12 ("no package source change") are backed by the integration pass's per-commit `--name-only` measurement over all four card commits, re-affirmed here by the empty diff.

### CHANGELOG sanity

Not applicable; no slice of this cycle modified `CHANGELOG.md`. It is on the build plan's baseline-dirty do-not-edit list, and two of its claims about this card are fenced catalog items below.

### Documentation / release sanity

- Spec header block re-verified against `KANBAN.md` this pass (table above). No status-line edit owed.
- `## Slice checklist` boxes are all `- [ ]` and correctly so: on an archived Done card the `Status:` line is the source of truth and the boxes stay unticked.
- No KANBAN movement, no `docs/GLOSSARY.md` edit, no `-terms.csv` edit, no `docs/TREE.md` regenerate. The maintainer's spec-and-`.py` scope fence held through the whole cycle.
- No script-rendered doc was touched, so the staging-language rule has no subject.
- `check_spec_glossary` green on the unchanged three-term CSV; the spec's three `docs/GLOSSARY.md` anchor citations (`#bigint-scalar`, `#djangotype`, `#finalize_django_types`) all resolve today and are the one generated-file citation class with a standing mechanical guard in pre-commit and CI.

### Temp test verification

- Temp test files used: **none**. `docs/builder/temp-tests/` carries nothing for this cycle.
- Disposition: not applicable. Every question in this pass is whether a written claim is true of the tree, which is answered by measuring the tree.

### Deferred work catalog

The next spec author's reading list. Walked from every per-slice artifact's `What looks solid`, `DRY findings`, `Notes for Worker 1 (spec reconciliation)`, and per-slice deferred sections, plus `bld-integration-026.md`'s consolidated catalog. **Every locator below was re-derived in this pass from an unscoped grep** — a catalog is a claim, and this cycle has already had four inherited claims overturned by the pass that checked them.

Slice 2 catalogued two items, then three; Slice 3 catalogued five; the integration pass consolidated to three. **Three live items**, and this pass confirms all three, with one merge and one drop upheld.

All three are in `KANBAN.md`, `KANBAN.html`, or `CHANGELOG.md`. **Why no slice of this cycle closed any of them — three independent fences, each sufficient on its own:**

1. All three files are on the build plan's `### Baseline-dirty out-of-scope files (never edit, never revert)` list, and were dirty with concurrent sessions' work throughout.
2. The maintainer's scope fence limits this cycle to spec files and `.py` files.
3. **`KANBAN.md` and `KANBAN.html` are generated from `examples/fakeshop/db.sqlite3` and are never hand-edited.** They render from the fakeshop kanban app's DB via `scripts/build_kanban_md.py`; a hand edit is clobbered by the next render. Whoever closes items 1 and 2 **edits the DB and regenerates**. `KANBAN.html` needs one extra care: its Vue shell is hand-maintained and only its data block regenerates. `CHANGELOG.md` is not generated, but `AGENTS.md` "No CHANGELOG.md updates unless told" governs it and its entry here is a historical ship record.

---

1. **`KANBAN.md` and `KANBAN.html` carry the retired two-false-clause sentence verbatim.**
   - Source: `bld-slice-2-026-stale_invariant_comments.md` `### Notes for Worker 1 (spec reconciliation)` (pass 1) and `### Deferred work catalog, for the final gate`; `bld-slice-3-026-spec_reconstruction.md` `### Deferred work` item 1 (which found the `KANBAN.html` half by dropping the grep's path list); `bld-integration-026.md` `### Deferred work catalog, consolidated` item 1.
   - Licensing spec line: none — the spec no longer contains the sentence at all (`grep -o` -> **0**), so nothing in the spec licenses or references the parallel copies. The fences are the build plan's baseline-dirty list and the maintainer's scope fence, not a spec deferral.
   - Live sites, re-derived: `KANBAN.md:3846` (**1** occurrence) and `KANBAN.html` (**1**). The sentence ends "the only `SET_NULL` ondelete in the example tree, and the only cross-model FK in the scalars app". Both clauses are false at HEAD: `on_delete=models.SET_NULL` occurs **4** times in `examples/fakeshop/apps/*/models.py`, and the scalars app declares **two** cross-model FKs (`tag` -> `ScalarSpecimenTag`, `partner` -> `ScalarSpecimen`). Every other file matching the phrase is this cycle's own record quoting it as retired.

2. **`KANBAN.md`, `KANBAN.html`, and `CHANGELOG.md` each carry `D4`'s retired exclusivity shape.**
   - Source: `bld-slice-2-026-…md` `### Notes for Worker 1` (pass 1) and its catalog item 2; `bld-slice-3-026-…md` `### Deferred work` items 2 **and** 4 (split across two entries, which is what let item 2's "no third site anywhere" stand while item 4 named the third site); merged by `bld-integration-026.md` item 2. **The merge is upheld** — one claim in three files is one item.
   - Licensing spec line: none in the deferral sense; the spec's own copy was replaced, and the rationale's `D4` records the measured claim that replaced it.
   - Live sites, re-derived with `grep -o 'no other example app' <file> | wc -l`: `KANBAN.md:3847` (**1**), `KANBAN.html` (**1**), `CHANGELOG.md:175` (**1**). `KANBAN.md`'s reads "upstream code paths **no other example app reaches**" followed by five paths; `CHANGELOG.md`'s reads "surfaces **no other example app** touches" followed by four. Four of the five were already reached by `apps/library` at the ship commit (8 models, 7 sibling `DjangoType` classes, a 7-`CreateModel` initial migration), and the fifth, `SET_NULL` ondelete behavior, is false at HEAD by the four-occurrence measurement above.

3. **`CHANGELOG.md`'s entry for this card undercounts twice, and one omission produced both.**
   - Source: `bld-slice-3-026-…md` `### Deferred work` item 3 (new in that pass; `D11` appears in no earlier catalog); `bld-integration-026.md` item 3.
   - Licensing spec line: the spec's `## Test plan` deletion list and definition-of-done item 9 both state the correct figures, so the spec is right and the changelog diverges from it. The divergence is licensed as deferred only by the fences above.
   - Live site, re-derived: `CHANGELOG.md:175`, one paragraph carrying both errors. It says "Three tests in `tests/types/test_converters.py` … are removed" and names exactly the three `big_integer` / `positive_big_integer` ones; `a5c89c98` removed **six**, the missing three being `test_json_field_maps_to_json_scalar_in_schema`, `test_json_field_nullable_in_schema`, and `test_json_field_round_trips_dict_via_schema_execution`. The same paragraph says "eight tests" (`grep -o 'eight tests' CHANGELOG.md | wc -l` -> **1**) where the ship module carried **nine**. The omitted ninth test is `test_scalar_specimen_introspects_json_scalar_in_both_shapes` — **the JSON introspection test whose three retired JSON counterparts are the three the changelog also lost.** One JSON-shaped omission, two wrong numbers.

**Dropped from the catalog, upheld as dropped so it is not re-opened:** `docs/TREE.md`'s one-line description of `test_scalars_api.py` ("scalar wire formats, filtering, relations, and optimizer behavior"). Re-read this pass. It accurately describes the module's HEAD surface and says nothing false about this card. Slice 3 already marked it "not deferred work"; it is not an item and needs no owner.

### Decided rather than deferred

Recorded distinctly from the catalog above, because a question examined and closed needs no future owner, and mixing the two inflates the catalog. Nothing below is deferred work.

- **The escalated Medium: `apps/scalars/models.py` module docstring #"covered transitively by every other example app" is TRUE at HEAD.** Escalated by Worker 3 in Slice 2 pass 1 as a fifth census the plan's scope sweep missed. Decided by Worker 1's pass-1 final verification, re-verified independently by Worker 3 in pass 2, and re-affirmed by the integration pass — resolution path (c), recorded out of scope with the fence stated. **Why it is not a defect:** Worker 3 measured model *ownership* (`apps/accounts` is an installed example app with no `models.py`) against a sentence whose subject is converter-row *coverage*, and `transitively` is the sentence's own word for exactly that gap. Closed. Not to be re-opened.
- **Slice 3's audit-table self-contradictions are recorded, not rewritten.** Both were confirmed by independent measurement in this pass (35 and 1) and both stay as written. An accepted artifact is the record of work already done; the corrected numbers live in `bld-integration-026.md` and here.
- **The rationale's append-only rule got exactly one recorded exception, and it is decided.** The integration pass's edit 3 replaced `D1`'s false `docs/SPECS/` census in place rather than appending a correction, on the narrowest possible scope and flagged for this gate to see rather than discover. Upheld: the rule protects an entry's *argument*, no argument changed, and shipping a false census inside the file whose subject is false censuses is the one outcome the rule cannot be read to license.
- **The rationale quotes Decision headings with an ASCII hyphen where the spec uses an em dash.** Cosmetic; every anchor resolves (verified in this pass's link table). Not edited, for the append-only reason.
- **The spec-vs-`.py` prose overlap stays as it is, and Slice 3's stated prevention is recorded as not having held.** Slice 3's DRY analysis said "the spec must not carry a second copy of that sentence"; its landed diff does carry the causal clause. Decided: no edit. `worker-1.md`'s implementation-relevant carve-out keeps the "why" that changes how a thing is built in the spec, and the `.py` comment states the same invariant at the code. Recorded so a later pass does not read the prevention as proven.
- **The one substantive spec-vs-rationale overlap has a named owner: the spec.** `## Non-goals` item 1's `tests/` coverage boundary is normative and the rationale's `D6` copy sits inside the argument for it. Kept, owner named.
- **Decision 5's 100%-coverage sentence is recorded, not graded.** Not measurable by any worker pass; the maintainer's CI gate owns it.
- **Floor verification: nothing to run, decided against building a venv.** See `### Floor verification`.

### Summary

The gate is green end to end. `ruff format --check`, `ruff check`, `git diff --check`, `check_trailing_commas --check` (repo-wide and over all 855 tracked candidates), and `check_spec_glossary` all exit 0; the anticipated `.gitignore`-blind checker failure did not occur, so nothing needed attributing to a concurrent session, and nothing was fixed or reverted in any baseline-dirty file. `pytest`, `manage.py check`, and `makemigrations --check --dry-run` were decided against and not run, on `AGENTS.md` and `START.md` authority over `BUILD.md`'s gate per `worker-1.md:13`, and independently because the cycle's `.py` diff is **AST-identical to HEAD once docstrings are stripped** — so neither command could answer differently for this cycle, while a run would have recorded two concurrent sessions' uncommitted work as this cycle's evidence. That same proof is what confirms the plan's `Floor-verification scope: none`: with no executable construct changed, there is no integration seam for a floor run to exercise.

No spec or rationale edit is owed. Every claim the integration pass fixed was re-swept here and holds: 26/26 and 19/19 link definitions with the single deliberate `#other` retirement, one history-narration hit, 35 census occurrences all over closed named populations, and a **fourth** sweep vocabulary — run because this cycle's own history says a vocabulary list always has a next gap — returning nine hits and zero defects. The `SCALAR_MAP` 26/16/10, the pair's eleven identical columns all-required-versus-all-nullable, the four `SET_NULL` occurrences, the two cross-model FKs, `D11`'s six retired tests and `D5`'s nine-versus-29 were each re-derived at HEAD rather than inherited.

Two Lows, both about instruments rather than the work. My own link-checker produced six false "broken fragment" findings from one character — collapsing whitespace where GitHub does not — a new instance of the standing home-grown-slugger trap in a different character. And deferred item 1's file count moved from 6 to 7 because the corpus includes the cycle's own artifacts, so the catalog below states live sites and per-file occurrences and no corpus total.

Three deferred items carried, all fenced three ways over, all in `KANBAN.md` / `KANBAN.html` / `CHANGELOG.md` — the first two DB-rendered, so whoever closes them edits `examples/fakeshop/db.sqlite3` and regenerates. Eight items are recorded as **decided rather than deferred**, so the next spec author's reading list is three items long and not eleven.

### Spec changes made (Worker 1 only)

**None.** No edit to `docs/SPECS/spec-026-scalar_conversion_fakeshop-0_0_7.md` or `docs/SPECS/appx/spec-026-scalar_conversion_fakeshop-0_0_7-rationale.md` in this pass, and none owed. Recorded rather than left blank, because "no edit" is a finding here: the census sweep in both polarities plus a fourth vocabulary, the history-narration sweep, the link/anchor/citation resolution over both files, and the contract re-derivation at HEAD all came back clean over the text the integration pass left. The spec's `## Slice checklist` boxes stay `- [ ]` per the archived-Done-card rule, with the `Status:` line as source of truth; both were re-verified against `KANBAN.md` this pass.

Files written by this pass: `docs/builder/bld-final-026.md` and `docs/builder/worker-memory/worker-1-026.md`. No `.py` file, no spec file, no `-terms.csv`, no generated doc, and no baseline-dirty or concurrent-session file was opened for writing. No `git stash`, `git checkout`, `git restore`, or `git worktree` was used anywhere; every HEAD reference was `git show HEAD:<path>` into a scratch path outside the repo. Nothing was committed and no branch was created or switched.

### Outcome

`final-accepted`. Twelve checklist boxes, twelve ticks, each evidenced above. Every gate command green with its exit status recorded. Floor-verification scope `none` confirmed against the landed diff by mechanical proof rather than accepted from the plan. The `pytest` / `manage.py` decision recorded with its authority and with an independent evidentiary argument that reaches the same answer. High: none. Medium: none. Low: two, both about this pass's own instruments, both recorded. Deferred work catalog: three items, every locator re-derived unscoped, each with its source artifact section, its licensing status, and the three fences that kept it out of this cycle. Eight decided-not-deferred items recorded separately. No `.py` change surfaced, so no slice re-loop is required and nothing routes back.

Closeout is not part of this pass and was not performed.

Status: final-accepted

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
