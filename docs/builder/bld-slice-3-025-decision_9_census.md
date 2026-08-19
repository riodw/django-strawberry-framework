# Build: Slice 3 — Decision 9 census repair (D14)

Spec reference: `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` (Decision 9, Risks)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Reuse.** No code pattern is in play; this slice writes Markdown only. The reuse that matters is the *result* Slice 2 established and recorded as this cycle's durable lesson: an enumeration whose owner is elsewhere goes stale, so the document states the rule and names the owner. Applied here rather than re-derived. The rule's owner already exists in the spec — Decision 5 (`### Decision 5 — Migration posture: hard break in alpha`) says the registration is owed by any schema that resolves `BigInt`, and DoD 6a already says "the migration rule applies wherever a case lives" — so Decision 9 cites it instead of restating it.
- **Duplication risk this slice creates.** One: a replacement census. "The two schema-construction sites" would be true today and false on the next harness module, reproducing D14 exactly. Avoided by identifying the card's target by **role** (the schema the project serves at `/graphql/`) and delegating the general question to Decision 5.
- **New helper justified.** None. No `.py` file is touched, so no `ruff` run.

### Implementation steps

1. Re-derive every item of the dispatched evidence from source and git, including the ones stated as already verified.
2. Repair the three spec sentences: Decision 9 paragraph 1, Decision 9 paragraph 2's closing clause, the Risks live-tier bullet.
3. Sweep the spec for the same claim spelled other ways — negatively (`sole`, `only`, `one place`, `happens once`) **and positively** (`every app schema.py`, `none constructs`), the spec-026 lesson.
4. Append `### D14` to the rationale's divergence record on the established entry shape; update Decision 9's `### Changes this Decision underwent`, `### Claims this Decision may no longer make`, and its `Contract that stays:` line.
5. Adjudicate the four count sites individually. Never blanket-bump.
6. Add a `## Verification performed by the Decision 9 census repair (Slice 3)` section — an append-only file cannot have two sections meaning "this pass".
7. Gates: `check_spec_glossary`, `check_trailing_commas --check`, the anchor / reference / link-convention sweep on both files, substring citations checked in the **cited** file.

### Test additions / updates

None. This slice touches no `.py` file and changes no executable line.

### Implementation discretion items

None delegated — Worker 1 is the sole writing role in this cycle.

### Dispatched findings checklist

- [x] D14 — the three Decision 9 / Risks census sentences repaired without a replacement census
- [x] D14 — rationale entry appended on the established shape, keyed to the spec headings it touches
- [x] Decision 9's `### Changes this Decision underwent` gains the post-ship bullet pointing at D14
- [x] Decision 9's `### Claims this Decision may no longer make` gains the census claim
- [x] Decision 9's `Contract that stays:` line judged against D14 (it did **not** survive verbatim — see below)
- [x] The four count sites adjudicated individually, reasoning recorded
- [x] Gates run with real output recorded

---

## Build report (Worker 2)

Not applicable: no code change is owed, so Worker 2 was never dispatched. Worker 1 performed the Markdown edits directly; `### Spec changes made (Worker 1 only)` is the report of what landed.

---

## Review (Worker 3)

Not applicable — no builder diff exists. Every check a review pass would own was run in `## Final verification (Worker 1)`, against source rather than against this pass's own prose.

---

## Final verification (Worker 1)

Read-only work only. No `git stash`, `checkout`, `restore`, `worktree`, branch, or commit at any point — concurrent cycles (`spec-021`/`022`/`026`, plus the maintainer) are live on this tree.

### 1. Evidence re-derived, with the commands that produced it

Nothing below was taken from the dispatch on prose.

| Claim | Command | Result |
|---|---|---|
| `strategy_schemas.py` constructs a schema with `config=strawberry_config()` | read `examples/fakeshop/strategy_schemas.py` | `build_strategy_schema` returns `strawberry.Schema(query=query_cls, config=strawberry_config(), extensions=extensions)`, the call broken across four lines |
| it is a shared non-test builder | read its module docstring | "Importable from both test tiers AND the benchmark scripts", naming `tests/test_lateral_pg_parity.py` and `scripts/bench_nested_fetch.py` |
| the file is post-ship | `git log --diff-filter=A -- examples/fakeshop/strategy_schemas.py` | one adding commit, `8fe01840`, 2026-07-07, "refactor: Consolidate the optimizer's duplicated contracts (DRY pass on the fetch-strategy arc)" |
| the ship commit precedes it | `git merge-base --is-ancestor b1a6d01f 8fe01840` | exit **0** — `b1a6d01f` IS an ancestor, so the census was true when written |
| non-test schema-construction sites in fakeshop | `grep -rn --include='*.py' -E '(strawberry\.Schema\|DjangoSchema)\(' examples/ scripts/ tests/ django_strawberry_framework/` | exactly **two**: `examples/fakeshop/config/schema.py` (`schema = DjangoSchema(`) and `examples/fakeshop/strategy_schemas.py` (`return strawberry.Schema(`) |
| the four `django_strawberry_framework/` hits are docstring examples | opened each | `extensions/debug.py`, `extensions/resource_policy.py`, `optimizer/extension.py` module docstring, `optimizer/extension.py` class docstring — all inside `::` fenced docstring prose. `schema.py`'s hit is the `class DjangoSchema(strawberry.Schema):` definition, not a construction |
| `config/schema.py`'s second match is a comment | `grep -nE '(DjangoSchema\|strawberry\.Schema)\(' examples/fakeshop/config/schema.py` | two hits: a comment ("Finalization must precede ``strawberry.Schema(...)``") and the real `schema = DjangoSchema(` binding |
| the baseline `## Current state` framing sentence is present | read `## Current state` | "Every bullet below is a statement about that starting surface, not about the shipped result." — present, but it scopes the bullet in **time**, not by tier, so it does not rescue the bullet's census (edit 4, section 3) |
| schema-construction sites at the pre-ship baseline | `git grep -nE '(strawberry\.Schema\|DjangoSchema)\(' b1a6d01f^ -- examples/fakeshop` | **two** code sites — `config/schema.py:26` and `test_query/test_multi_db.py:142` — plus a `test_query/README.md` prose mention. So "sole schema-construction site" is false of the baseline surface too, true only as "sole non-test" |

### 2. The no-code-gap claim, and where the dispatch's version of it was imprecise

**There is no code gap.** No fakeshop schema resolves `BigInt` without the registration. But the dispatch's phrasing of that — "Every post-ship fakeshop schema-construction site already passes `config=strawberry_config()` — `strategy_schemas.py` and the five `test_query/` modules that build schemas" — is wrong in two ways, and the load-bearing conclusion survives both.

- **The module population is nine, not six.** Seven `test_query/` modules build schemas (`test_debug_extension_api`, `test_error_policy_api`, `test_multi_db`, `test_optimizer_auto_api`, `test_products_visibility_api`, `test_resource_policy_api`, `test_transport_api`), plus two under `apps/library/tests/` (`test_generic_connection`, `test_generic_connection_sharded`), plus `strategy_schemas.py`.
- **Two of them build schemas with no `config=strawberry_config` at all.** `test_query/test_products_visibility_api.py` has seven builds and zero; `test_query/test_transport_api.py` has two builds and one. Both files are post-ship (added `841e56d6` 2026-08-18 and `537e4951` 2026-07-25).

Neither resolves `BigInt`, which is why there is still no gap: `test_products_visibility_api.py` builds over `apps.products.models` `Category`/`Item` only, and `apps/products/models.py` contains no `Big` at all; `test_transport_api.py`'s `_SETUP_PROBE_SCHEMA` is over a pure-Strawberry `_SetupProbeQuery` with no Django model. **That is Decision 5's rule holding as stated — the registration is owed by a schema that resolves `BigInt`, not by every schema** — and it is a stronger statement of the finding than "every site passes it", so the rewrite was pointed at the rule rather than at a compliance census.

**One instrument trap, this cycle's recurring kind.** My first count used `config=strawberry_config()` with the empty parens and reported **0** for `test_query/test_optimizer_auto_api.py`. The file passes `config=strawberry_config(extra_scalar_map={BombValue: bomb_scalar})`. Re-taken on `config=strawberry_config` the count is 1. A population's vocabulary is not the population.

### 3. Spec edits

All to `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`.

**Decision 9, paragraph 1.** Before: "... [`examples/fakeshop/config/schema.py`][schema], **the project's sole schema-construction site**. This card's edit there is exactly two lines ...". After: "... [`examples/fakeshop/config/schema.py`][schema], **the schema the project serves at `/graphql/`**. That is the site this card's contract names — not a count of the project's schema-construction calls. Which *other* schemas anywhere must carry the registration is owned by [Decision 5](#decision-5--migration-posture-hard-break-in-alpha)'s rule, which applies wherever a `BigInt`-resolving schema is built, and by the code that builds it. This card's edit at the served schema is exactly two lines ...". Reason: identify the target by role, delegate the general question to the rule's existing owner, and refuse a replacement count. The two-line narrowing Slice 2 landed for D9 (import + `config=`; constructor class / roots / `extensions=` are other cards') is carried through untouched.

**Decision 9, paragraph 2, closing clause.** Before: "... for the same structural reason: **schema construction happens once, in `config/schema.py`**." After: "... for the same structural reason: **an app `schema.py` contributes a `Query` root and leaves construction to whatever composes it**." Reason: the false unqualified generalization is replaced by what is actually structural about an app `schema.py`. The preceding sentence — neither per-app schema constructs a schema, each declares a `@strawberry.type class Query` only — is kept verbatim.

**Risks, live-tier bullet.** Before: "Slice 3 migrates **the one** fakeshop schema-construction call; ...". After: "Slice 3 migrates **the construction call for the schema fakeshop serves at `/graphql/`**; ...". Reason: only the census goes. The bullet's content — the fakeshop models carry `BigIntegerField` / `PositiveBigIntegerField` columns, a live `/graphql/` query resolves `BigInt` through `config=strawberry_config()` end to end, and that live tier is where a registration regression surfaces first — is unchanged.

**`## Current state`, the `config/schema.py` bullet — a FOURTH edit, added after Worker 0 lifted the fence.** Before: "constructs the project schema — **the project's sole schema-construction site** — with no `config=` argument." After: "constructs **the schema the project serves at `/graphql/`** — **its sole non-test schema-construction site** — with no `config=` argument."

Proof, re-derived myself: `git grep -nE '(strawberry\.Schema|DjangoSchema)\(' b1a6d01f^ -- examples/fakeshop` returns `config/schema.py:26` **and** `test_query/test_multi_db.py:142` (plus a `test_query/README.md` prose mention). So the claim is false of its own baseline surface, not only of `HEAD`. I originally left it on the brief's instruction and recorded the counter-evidence under `### Notes for Worker 1`; Worker 0 read the counter-evidence, withdrew the fence, and the repair landed here. **The framing sentence does not rescue it**, which is the part I had wrong: "Every bullet below is a statement about that starting surface, not about the shipped result" scopes the bullet in **time**, and time is not the axis this claim is false on — tier is.

Repaired on a different axis from the other three, deliberately. This is the one surface whose job *is* to state a census — `## Current state` enumerates the baseline so each Slice checklist item names what it replaces — so the census stays and gains the tier qualifier it always needed. The `0.0.6` baseline is immutable, so a count of it cannot rot; that is what makes a census safe here and unsafe in a Decision. It also now names the site by the same role phrase Decision 9 uses, so the two agree instead of appearing to contradict each other 270 lines apart. `grep -c 'serves at `/graphql/`'` reports **3** — this bullet, Decision 9, and the Risks bullet.

**No `strategy_schemas.py` citation was added to the spec, and no link definition with it.** Judged against the rot risk the brief names: naming a second site in a contract document re-creates exactly what D10 established the rule against, and the file is a harness module this card does not own. The rationale's D14 entry names it, which is the change record's job. `[strategy-schemas]` was therefore added to the **rationale's** `<!-- examples/ -->` group only, alongside `[schema]` and `[test-scalars-api]`, and is used.

**Nothing else in the spec needed editing, and both alternative spellings were checked.**

- Negative vocabulary: `grep -nE 'sole |only schema|one place|happens once|single schema|the one fakeshop|one schema-construction|construction site'` returns six other hits, all correct. Slice 3's checklist bullet "(the file's sole one)" is scoped to `config/schema.py`, which has exactly one construction call. The `GOAL.md` "one place where a consumer's right shape example lives" hits (two) are about `GOAL.md`, not fakeshop. `## Current state`'s bullet was repaired in this slice (edit 4 above). Line 90's "`config=strawberry_config()` added once per schema" is the per-schema rule. Line 331's converter-test sites claim is true.
- Positive vocabulary, the spec-026 lesson: DoD item 8 says "every app `schema.py` added since ... none constructs a schema". Verified over the app tree's own closed set — all six `examples/fakeshop/apps/*/schema.py` modules (`accounts`, `glossary`, `kanban`, `library`, `products`, `scalars`) declare a `@strawberry.type class Query` and `grep -nE '(DjangoSchema|strawberry\.Schema)\('` over all six returns nothing. True, and it is what licenses my paragraph-2 generalization.

### 4. Rationale edits

All to `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md`.

| Change | Reason |
|---|---|
| new `### D14 — fakeshop gained a second schema-construction site`, appended after D13 on the established shape: `Spec surfaces:` line, the claim, what is true, the attribution commit, then `**Resolved in the spec (Slice 3) ...**` | the record's contract; D9 and D10 are its two closest models |
| D14 states that this is **drift** — the reasoning was right and the tree moved — and that the migration rule propagated to `strategy_schemas.py` unprompted six weeks later, which is evidence **for** the Decision | required by the dispatch and true: the compliance was nobody's assignment |
| `## Decision 9`, `### Changes this Decision underwent` — new post-ship bullet: the tree grew a second non-test site, so the Decision's identification-by-count became identification-by-role; the conclusion did not change. Points at `[D14]` | `BUILD.md` requires the rationale to carry every change a Decision underwent |
| `## Decision 9`, `### Claims this Decision may no longer make` — new bullet naming both retired sentences, and stating what the Decision **may** still say (the card's edit is that one served schema — a statement about its own scope) | a retraction that does not draw the line invites over-correction |
| `## Decision 9` opener, `Contract that stays:` — **did not survive verbatim.** Before: "the fakeshop migration is exactly one schema-construction site, [`config/schema.py`][schema]". After: "the card's fakeshop migration is the one schema the project serves at `/graphql/`, [`config/schema.py`][schema], and nothing else", plus one clause saying it is stated as this card's scope rather than as a project census | the substance survives (the card migrated exactly one site) but the phrasing is the retired census's phrasing, and it sat two subsections above a line saying the Decision may no longer make it |
| `## Post-ship divergence record` heading `(D1-D13)` -> `(D1-D14)`; opener "Thirteen places" -> "Fourteen places"; one sentence naming D14 as drift worth separating (the tree grew a counted surface while the rule propagated to it unprompted); one paragraph recording that the catalog was assembled in two passes and that the boundary matters when reading any count in the file | the heading and opener describe the **record**, which now holds fourteen |
| the heading's slug moved with it: `#post-ship-divergence-record-d1-d13` -> `#...-d1-d14` at both use sites (the header paragraph and `## Provenance of this record`) | renaming a heading moves its slug — the cycle's own recorded lesson |
| new `## Verification performed by the Decision 9 census repair (Slice 3)` section | Slice 2's rule: an append-only file cannot have two sections meaning "this pass" |
| `[strategy-schemas]: ../../../examples/fakeshop/strategy_schemas.py` added to `<!-- examples/ -->`, alphabetical between `[schema]` and `[test-scalars-api]` | D14 cites it; the def is used |

### 5. The count adjudication (dispatch section 3), site by site

Adding a fourteenth entry does not make every "thirteen" wrong. Each site was decided on its own subject.

| Site | Subject of the count | Verdict |
|---|---|---|
| `## Post-ship divergence record (D1-D13)` heading + "Thirteen places where ..." | **the record**, which now holds fourteen entries | **CHANGED** to fourteen, and the slug moved at both use sites |
| the record's "**Nothing was skipped in the code**" sentence | whether any entry is a build gap | **UNCHANGED.** It reads "every entry below is post-ship drift, not a build gap" — a universal that D14 satisfies. D14's own no-code-gap evidence is a different kind (a later file complying with the rule unprompted) and is stated in the entry, where it belongs |
| the record's "Two entries — D3 and D5 — record reasoning that was **wrong in mechanism** ...; the rest are drift" | which entries are mechanism errors | **UNCHANGED.** D14 is drift, so it joins "the rest". Bumping "two" to three would have been a false claim: D14's reasoning was correct |
| `## Provenance of this record` — "the thirteen divergences **it acted on** are recorded below" | **Slice 2's action** | **thirteen KEPT.** Slice 2 did not act on D14. One clause appended so a reader who follows the link and meets fourteen entries is not misled: Slice 3 added the fourteenth, found after the final gate, and the record holds fourteen while Slice 2's figure stays thirteen |
| `## Verification performed by the spec reconciliation (Slice 2)` — "All thirteen divergences discharged in the spec; each `### D<n>` entry above closes ..." | **Slice 2's pass** | **thirteen KEPT**, but the second half was over-reaching once a fourteenth entry existed: "each `### D<n>` entry above" would have claimed authorship of D14's closing paragraph. Narrowed to "each of those thirteen `### D<n>` entries", with a parenthetical assigning D14 to Slice 3 |
| the spec's five occurrences of "thirteen" (Slice checklist, Decision 7 body, the implementation-plan table, the Test-plan heading, the quoted CHANGELOG body) | **the thirteen factory tests** in `tests/test_scalars.py` | **UNTOUCHED.** Same digit, different population. This is the cycle's dominant defect in its purest form, and a blanket sweep on the token `thirteen` would have produced five false claims in the spec |
| new cross-link ids | — | none added to the spec. In the rationale, D14 is reached by `#d14--fakeshop-gained-a-second-schema-construction-site` from three places (the record opener, `### Changes this Decision underwent`, `### Claims this Decision may no longer make`) and reaches the spec by the existing `[spec-025-d9]` / `[spec-025-risks]` / `[spec-025-slice-checklist]` / `[spec-025-dod]` defs. All resolve — see the sweep below |

`docs/builder/bld-slice-1-025-rationale_authoring.md` and `docs/builder/bld-slice-2-025-spec_reconciliation.md` were read and **not written**. They record passes that genuinely handled thirteen.

### 6. Gates, with real output

| Gate | Command | Result |
|---|---|---|
| glossary | `python3 scripts/check_spec_glossary.py --spec docs/SPECS/spec-025-scalar_map_helper-0_0_7.md --terms docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv` | `OK: 17 terms - all have glossary entries and at least one spec link.` exit **0**. Same before and after this pass — the count DoD item 9a pins, so no DoD edit is owed |
| source layout | `python3 scripts/check_trailing_commas.py --check docs/SPECS/spec-025-scalar_map_helper-0_0_7.md docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md` | exit **0**, no output. Same before and after |
| whitespace | trailing-whitespace / tab scan, both files | **0** lines in either |
| `pytest` | not run | **This slice changes no executable line** — no `.py` file is touched — so no test run is owed. Stated rather than skipped silently. No `--cov*` flag was used anywhere in this pass; no `--no-cov` either, nothing being run |
| `ruff` | not run | no `.py` file touched |

### 7. Anchors, references, and the link convention

Instrument: a sweep that strips fenced blocks and inline code spans before matching, resolves in-page anchors against each file's own computed heading slugs, and disk-exists-checks every link definition plus its `#fragment` against the **target** file's real headings.

| Check | Spec | Rationale |
|---|---|---|
| `<!-- LINK DEFINITIONS -->` delimiters | 1 | 1 |
| duplicate heading slugs | none | the 4 pre-existing per-Decision subsection slugs (structural, not introduced here) |
| in-page anchor uses | 82 | 65 |
| unresolved in-page anchors | **6 distinct / 9 uses** — the same quoted-`docs/GLOSSARY.md` set Slice 2 recorded as correct-as-written (`bigint-scalar`, `upload-scalar`, `specialized-scalar-conversions`, `strawberry_config`, `djangotype`, `djangooptimizerextension`). None introduced or moved by this pass | **0** — so `#d14--…`, `#post-ship-divergence-record-d1-d14`, `#decision-5--migration-posture-hard-break-in-alpha`, `#provenance-of-this-record` and `#verification-performed-by-the-spec-reconciliation-slice-2` all resolve |
| `used-not-defined` | `[]` | `[]` |
| `defined-not-used` | `[]` | `[]` — `[strategy-schemas]` is used |
| bad definition targets (missing file or dead `#fragment`) | **0** | **0** |
| inline cross-file links (convention forbids) | **0** | **0** |
| non-ASCII | en/em dash, middle dot, arrow — `.md` only, permitted | em dash, ellipsis, arrow — permitted |

The spec's new in-page anchor `](#decision-5--migration-posture-hard-break-in-alpha)` resolves against the spec's own `### Decision 5 — Migration posture: hard break in alpha` heading; it is the same slug the Slice checklist already uses.

**Substring citations.** This pass touched none of the spec's existing `#"..."` anchors and added none to the spec. It added exactly one, in the rationale: a `[schema]`-linked citation anchored at the substring `schema = DjangoSchema(`. Checked **in the cited file**, not the citing one: `grep -F 'schema = DjangoSchema(' examples/fakeshop/config/schema.py` returns the line. It replaced a `line 77` reference I had first written, which would have violated `AGENTS.md` rule 27 in a tracked standing doc.

`strategy_schemas.py`'s construction call carries **no** substring anchor: the call is broken across four lines, so no single-line substring exists — the same trap that killed `#"strawberry.Schema(query=Query"` in Slice 2. D14 says so explicitly rather than quoting a reflowed one-liner as if it were source text.

### 8. Scope compliance

This pass wrote exactly three paths: `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`, `docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-rationale.md`, and this artifact. No `.py` edit, no `-terms.csv` edit, no `KANBAN.md` / `KANBAN.html` / `CHANGELOG.md` / `docs/GLOSSARY.md` / `docs/TREE.md` / `README.md` / `GOAL.md` / `TODAY.md`, no DB write, no closeout agentflow edit. Nothing belonging to the concurrent `spec-021` / `022` / `026` cycles was touched and nothing baseline-dirty was reverted. No commit, no branch, no stash, no checkout / restore / worktree. Every file created carries `025` in its name.

### 9. The end-to-end read

Decision 9 and the Risks bullet were read whole, after the checklist. Both now state what the card does and why, with no count of the tree in either, and no reader has to apply a date or a card to them to learn what is currently true. The spec narrates none of this: it carries no "as of", no "originally", no amendment note, and no mention of `strategy_schemas.py` or `8fe01840`. All of that is in the rationale, which is where a chronology belongs.

One thing the read changed: the `Contract that stays:` line. It was factually fine and stylistically the retired census, and only reading the Decision top-to-bottom made the contradiction with its own `### Claims ... may no longer make` bullet visible.

### Summary

D14 is discharged. Three spec sentences repaired by naming the site's role and the rule's owner rather than by refreshing a count; the rationale gained a `### D14` entry, three Decision-9 subsection updates, a Slice 3 verification section, and one link definition. The four count sites were adjudicated individually: two changed (the record's heading and opener, describing the record), two kept at thirteen with a scoping clause each (Slice 2's action and Slice 2's pass), and the spec's five "thirteen"s left alone because they count factory tests. Gates green. No code gap, verified from the rule's side rather than by a compliance census — which is also where the dispatch's own evidence bullet 4 was imprecise, corrected in section 2 above.

### Spec changes made (Worker 1 only)

Recorded in full in sections 3 and 4. Nothing was deferred from this slice's own scope. Status-line re-verification for this spawn: the spec's header lines (title, `Target release:`, `Status:`, spec-path line) were re-read and none is falsified by this pass — `Target release:` already states the joint `0.0.7` cut as Slice 2 left it, and this pass changes no version, no release, and no file location.

### Notes for Worker 1

Found and deliberately not fixed.

- ~~`## Current state`'s `config/schema.py` bullet~~ — **RESOLVED inside this same slice.** Worker 0 read the counter-evidence recorded here, withdrew the fence, and the repair landed as the fourth edit in section 3. Kept as a struck-through line rather than deleted, because the sequence is the lesson: I accepted a "not a defect, do not touch" instruction while recording, in the same pass, the evidence that refuted it — and filed that evidence as a note instead of raising it as a contradiction. The dispatch asked me to say plainly if any part of the brief was wrong; I did that for its evidence bullet 4 and only half-did it here. **A fence I can disprove is a fence to push back on, not to document.**
- **Two post-ship fakeshop test modules build schemas with no `config=strawberry_config`** — `test_query/test_products_visibility_api.py` (seven builds) and `test_query/test_transport_api.py` (one of two). Not a defect: neither resolves a `BigIntegerField` / `PositiveBigIntegerField`, so Decision 5's rule does not reach them. Recorded so a future sweep for "sites missing the registration" does not rediscover them as one, and because the dispatch's evidence bullet 4 asserted the opposite.
- **The dispatch's module population was six ("`strategy_schemas.py` and the five `test_query/` modules"); it is nine** — seven `test_query/` modules plus two under `apps/library/tests/`. Not actionable in any file; recorded because the figure appears in Worker 0's deferred-work catalog and will be inherited if it is not corrected there.
- **Slice 2's own deferred-work catalog is still open and unchanged by this pass** — the `-terms.csv` `TODO-ALPHA-028-0.0.11` rows, the `TODO-ALPHA-051-0.0.15` KANBAN bullet, the spec's pinned KANBAN Done body not existing in the generated `KANBAN.md`, the quoted `CHANGELOG.md` `### Added` body's missing tooling-appended clause, and the `## [0.0.7]` pre-renumber card labels. All five are outside this slice's fence (`-terms.csv`, `KANBAN`, `CHANGELOG`, DB) and none is a spec-side defect. Re-derive each before homing: a catalog is a claim.

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
