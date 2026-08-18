# Build: final test-run gate — spec-020 (`DjangoListField`) residual closeout

Spec reference: `docs/SPECS/spec-020-list_field-0_0_7.md` (whole file; residual closeout, not a slice)
Rationale companion: `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md`
Build plan: `docs/builder/build-020-list_field-0_0_7.md`
Rounds: `docs/builder/bld-review-1-spec020_reconciliation.md` (`final-accepted`), `docs/builder/bld-review-2-docs_completion.md` (`final-accepted`)
Integration pass: `docs/builder/bld-020-integration.md` (`final-accepted`)
Status: final-accepted

The integration pass ran first, in this same Worker 1 spawn, and was closed before this artifact was opened (`docs/builder/build-020-list_field-0_0_7.md` `## Integration pass and final gate run in one Worker 1 spawn`). This gate is the backstop confirming it happened: `bld-020-integration.md` carries all six required pre-writing dispositions, the staged-anchor sweep with its command and output, and the cross-round DRY scan.

## What this cycle's diff is, because it decides every attribution below

**No source file and no test file was modified by any pass in this cycle.** Re-derived here rather than accepted from either round: `git diff HEAD --name-only` restricted to this cycle's ownership returns `README.md`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3`, `docs/SPECS/spec-020-list_field-0_0_7.md`, `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md`, plus the untracked `docs/builder/bld-*.md` artifacts and the build plan. Zero `.py` paths.

The working tree is legitimately dirty with a **concurrent maintainer session** — 93 `git status --short` entries at the time of this gate, spanning `django_strawberry_framework/**`, `tests/**`, several `docs/SPECS/**` files, every untracked `docs/review/rev-*.md`, `examples/fakeshop/apps/kanban/constants.py`, and the untracked `examples/fakeshop/test_query/test_products_visibility_api.py`; the two spec files are additionally **staged** by that session. The build plan's enumeration is a pre-flight snapshot rather than a closed set and the count has drifted (106 at pre-flight, 105 mid-cycle, **93** now), exactly as the plan warns. Nothing in that set was edited or reverted by any pass, and no `git stash` / `checkout` / `restore` / `worktree` was used anywhere in this cycle; every HEAD reference was taken read-only with `git show HEAD:<path>` into a scratch path outside the repository.

Consequently: **every gate below passed, so no failure needed attributing.** The rule was nonetheless the one held ready — a code-level failure in this tree would be the concurrent session's, recorded with evidence and escalated rather than fixed or reverted (`AGENTS.md` rule 34, `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`, "Pre-existing at HEAD").

## Gate results

Every command run from the repository root in the shared `.venv`, in the order `docs/builder/BUILD.md` `## Final test-run gate` gives.

| # | Command | Result | Evidence |
|---|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** | `6170 passed, 40 skipped in 73.67s`, exit **0**. Full sweep across all three test trees. No `--cov*` flag was used in this pass or any pass this cycle; `--no-cov` is required because `pytest.ini`'s `addopts` auto-applies `--cov`. **No coverage figure was inspected or asserted** (`docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** | `System check identified no issues (0 silenced).`, exit **0**. |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** | `No changes detected`, exit **0**. Expected: this cycle changed one `glossary_glossaryterm` **row**, no model. |
| 4 | `uv run ruff format --check .` | **PASS** | exit **0**, `424 files already formatted`. Read-only; never `--fix`. (Ruff also emits its standing `COM812`-conflicts warning, which is configuration advice, not a failure — the exit code is 0.) |
| 5 | `uv run ruff check .` | **PASS** | exit **0**, `All checks passed!`. Read-only; never `--fix`. |
| 6 | `git diff --check` | **PASS** | exit **0**, no output. No whitespace error and no conflict marker anywhere in the tree, the concurrent session's files included. |
| 7 | Floor verification | **`none` — nothing to run** | See `### Floor verification` below. |

Supporting doc gates, re-run here because this cycle wrote to the surfaces they govern:

| Command | Result |
|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-020-list_field-0_0_7.md` | exit **0** — `OK: 24 terms - all have glossary entries and at least one spec link.` |
| `uv run python scripts/build_glossary_md.py --check` | exit **0** — "is up to date". The rendered `docs/GLOSSARY.md` provably agrees with the DB, so R2's regenerate is intact and no hand-edit slipped in afterwards. |
| `uv run python scripts/build_kanban_md.py --check` | exit **0**. Neither kanban script was run in write mode by any pass. |
| `uv run python scripts/check_trailing_commas.py --check` scoped to this cycle's files (`README.md`, `docs/GLOSSARY.md`, both spec-side files, this artifact and `bld-020-integration.md`) | exit **0** |
| `uv run python scripts/check_trailing_commas.py --check` repo-wide | exit **1** — **baseline exception 1**, below |
| `uv run python scripts/build_tree_md.py --check` | exit **1** — **baseline exception 2**, below |

Byte counts of the two files under custody, re-measured with `wc -c` (never `len(str)`, which counts characters): `docs/SPECS/spec-020-list_field-0_0_7.md` **100,566**; `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md` **109,687**. Both match R1's final-verification record exactly, confirming neither the integration pass nor this gate disturbed them.

### Floor verification

**No floor-verification scope was declared, and none is owed.** The build plan declares `Floor-verification scope: none` for the whole cycle, and both rounds restated it per-round with their reasons. Confirmed independently rather than accepted: no round touches a Django / Strawberry / channels integration seam — no request/response handling, no view or ASGI plumbing, no body or upload parsing, no session/auth surface, no queryset or expression compilation, no schema or type construction against Strawberry internals, no consumer or middleware wiring. `docs/builder/BUILD.md` `## Floor verification` -> `### When it is required` names "docs, KANBAN / glossary regeneration" as exactly the `none` case, which is this cycle in full.

**No floor venv was built**, and the shared `.venv` was not mutated, installed into, or downgraded by any pass. There is no unrun floor claim for this gate to inherit, so nothing here is closed on an unverified floor.

### The two recorded baseline gate exceptions

Both are pre-existing, both were verified by Worker 0 and recorded in the build plan's preamble before this gate ran, and **neither is caused by anything this cycle wrote**. `docs/builder/BUILD.md` `## Final test-run gate` licenses passing on a lint/doc gate failure exactly when a pre-flight baseline exception was recorded in the plan's preamble, and both were. Re-derived here rather than read from the record.

1. **Repo-wide `uv run python scripts/check_trailing_commas.py --check` exits 1.** The single reported file is `.claude/projects/-Users-riordenweber-projects-django-strawberry-framework/memory/one-spec-owns-each-feature.md`, an **untracked, gitignored agent-memory artifact** (`.gitignore` ignores `.claude/`) — not repository content. The checker's traversal reaches it only because `.claude/` sits inside the working directory. Unrelated to this cycle, not fixed here. Scoped to every file this cycle writes the same check exits **0** (re-run above).

2. **`uv run python scripts/build_tree_md.py --check` reports `docs/TREE.md is not up to date`.** `docs/TREE.md` is **clean** in `git status --short` and no pass this cycle wrote it. `build_tree_md.py` renders from module docstrings, so the failure is docstring-driven and both DBs are irrelevant to it. The three delta lines are entirely the concurrent maintainer session's baseline-dirty work: two identical lines (emitted once per layout section) from the modified `django_strawberry_framework/utils/converters.py` module docstring, and one added line for the untracked `examples/fakeshop/test_query/test_products_visibility_api.py`. **`docs/TREE.md` was deliberately NOT regenerated** — doing so would publish another session's half-landed surface, which `START.md` "Rendered docs" forbids and `AGENTS.md` rule 34 makes out of scope. R2's plan expected exit 0 for this gate; that expectation was wrong, Worker 2 caught it, Worker 3 and R2's final verification each confirmed it independently, and Worker 0 folded it into the plan preamble as "Baseline gate exception 2".

**One label correction that travels with exception 2**, established by R2's final verification and re-confirmed here so the next cycle does not inherit it inverted: the *on-disk* `converters.py` docstring (the concurrent session's uncommitted edit) reads "write-field and filter-input converters", which is what the renderer emits; `docs/TREE.md`'s committed line reads "form + serializer converters", matching the HEAD docstring. R2's build report states the pair the other way round. Cause, count, attribution and disposition were all correct; only the two labels were swapped.

## Round and integration acceptance, confirmed

| Artifact | `Status:` | Checklist |
|---|---|---|
| `docs/builder/bld-review-1-spec020_reconciliation.md` | `final-accepted` | 14 dispatched findings, all `- [x]`, audited against the spec by a fresh Worker 1; no deferral |
| `docs/builder/bld-review-2-docs_completion.md` | `final-accepted` | 11 dispatched boxes, all `- [x]`, audited against the files by a fresh Worker 1; no deferral |
| `docs/builder/bld-020-integration.md` | `final-accepted` | six pre-writing steps discharged; staged-anchor sweep clean; no consolidation loop required |

Both rounds' builder amendment lists are discharged on disk (`worker-1.md` `## Review-round custody`): R1 had no builder and its own and Worker 3's `### Notes for Worker 1` entries are all resolved or explicitly deferred; R2's builder recorded one amendment (the build-plan `build_tree_md.py` wording), which Worker 0 folded into the plan.

Round-scope declarations, restated once for the cycle and each confirmed rather than inherited: **failability proofs — none owed** (no pass introduced a boundary, guard, gate, or rejection path; the diff carries no executable line, so the population is empty legally, and no fail-open shape could have landed); **hot-path budget — `none`**, nothing runs per request / resolver / row / connection; **`scripts/review_inspect.py` — skipped**, no `.py` file added or modified by any pass; **relocation / promotion claims — none**, no body moved, no helper promoted, nothing claimed byte-identical (the one *test* promotion the cycle documents is a fact about a prior card's shipped tree, and both live tests were verified to exist by name).

## Summary

The residual closeout of `docs/SPECS/spec-020-list_field-0_0_7.md` is complete and the load-bearing result is unchanged from Worker 0's verification pass: **there was no code gap.** Every one of the spec's 20 Definition-of-done items is delivered, several as strict supersets by later cards, and no Worker 2 dispatch against source was required or made.

What the cycle produced:

- **Pre-flight step 7 — the rationale MOVE.** The spec's deliberative layer left `docs/SPECS/spec-020-list_field-0_0_7.md` (151,236 -> 85,576 bytes) for the new `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md`, keyed per Decision and per section.
- **Round 1 — spec reconciliation.** 14 findings landed across two build passes and two Worker 3 reviews. The spec now states only what is true at HEAD: the dead `_apply_get_queryset_*` helpers are gone from all seven sites, the own-class-origin registration guard replaces the insufficient `hasattr` claim, the `functools.partial` "DOES NOT WORK" block that instructed consumers to hand-rewrap a working resolver is **deleted**, the sealed-execution-queryset and cascade contracts reached Decision 3, the async-iterable third arm and the ordering contract were added, and every falsified count was replaced by the contract it stood in for rather than by a re-measured number. Spec 100,566; rationale 109,687.
- **Round 2 — documentation completion.** `README.md` gained its `0.0.7` bullet (`grep -n DjangoListField README.md` returned nothing at HEAD and now returns one line), and the generated `docs/GLOSSARY.md` `DjangoListField` entry gained an `**Async-iterable resolvers.**` paragraph and an `**Ordering.**` paragraph and had one imprecise `ConfigurationError` replaced by a linked `SyncMisuseError` — reached only by an ORM write to one `glossary_glossaryterm` row plus a regenerate, with the `**Row bound**` paragraph proved byte-identical at 779 bytes by three independent passes.
- **Integration pass.** No deletion candidate and no live cross-round duplication; decision (a)'s deferral target re-verified to still carry every deferred clause *after* R2 edited that entry; one new cross-round Low (I1) and one population correction (I2), both catalogued below.

The gate passes on the two recorded baseline exceptions and on nothing else.

### Deferred work catalog

The next reader's list. Every item is stated so it can be acted on without this conversation. **This is not "no deferred work"** — six items are carried, two of them escalated by Worker 0 before any worker was dispatched.

1. **`CHANGELOG.md`'s entire `0.0.7` section labels every card by its pre-renumber number.**
   *Source:* `docs/builder/build-020-list_field-0_0_7.md` `### Escalated to the maintainer — NOT dispatched to any worker`, item 1; re-confirmed untouched by both rounds' `### CHANGELOG sanity` sections and by `bld-020-integration.md`.
   *Spec clause licensing the deferral:* none — this is a Worker 0 escalation under `worker-0.md` "Closing out a kanban card", which forbids partial-fixing a reference that is wrong across multiple surfaces.
   *Description:* the section tracks this card as `016-djangolistfield_non_relay_list-0.0.7` and its siblings as `017-appspy…`, `018-schema_export…`, `019-multi_database…`, `046-django_trac_37064…` (twice), `047-warning_free_scalar…` and `048-scalar_conversion…`. The board numbers are now `020`-`026` after the 2026-07-30 renumber. **Nothing is broken:** the link definitions resolve because `KANBAN.md#djangolistfield_non_relay_list` is slug-based, not number-based. The visible labels are uniformly stale across the whole section, which is precisely the shape the no-partial-fix rule covers — correct all of them in one change or none.

2. **`KANBAN.md`'s `DONE-020-0.0.7` card lists `django_strawberry_framework/apps.py` under `#### Package files`.**
   *Source:* same escalation, item 2.
   *Spec clause:* none; Worker 0 escalation.
   *Description:* `apps.py` is `DONE-021-0.0.7`'s subject, not this card's. The card-files data is DB-backed and replaced **wholesale** by `manage.py import_card_files`, so a hand correction to `KANBAN.md` (or to the row) would be overwritten by the next import. The fix belongs with whoever next re-runs that command, as an input correction rather than an output edit.

3. **The three-surface `orderBy` / pk-tiebreaker precision bundle — take it whole or not at all.**
   *Source:* `bld-review-2-docs_completion.md` Worker 3 `### Low:` items 1-2 and `### Notes for Worker 1` items 1-2; disposed of as **LEAVE** by that round's final verification, dispositions 1-2. Population corrected by `bld-020-integration.md` finding I2.
   *Spec clause:* none licenses the deferral; `docs/builder/worker-1.md` `## Spec custody` **forbids** the spec edit, because the statements are true as conditionals and the spec is therefore neither incomplete, inconsistent, nor inaccurate.
   *Description:* two imprecisions in one sentence. (i) The `orderBy` recourse names an argument `DjangoListField` does not itself wire — the factory's whole signature is `target_type`, `resolver`, `description`, `deprecation_reason`, `directives`, `max_rows`, `trusted_max_rows`, and order arguments are added to both primitives by the Layer-3 specs, which the spec's own next bullet records two lines down. (ii) The comparative "`DjangoConnectionField` appends a pk tiebreaker" is unqualified where the shipped append is conditional — `django_strawberry_framework/connection.py` #"as a terminal tiebreaker UNLESS the effective ordering already ends in a" appends it only when the effective ordering is not already a unique total order (delegated to `django_strawberry_framework/optimizer/plans.py::deterministic_order`), and the keyset branch appends none at all.
   *Population — files, and the sites inside them:* `docs/SPECS/spec-020-list_field-0_0_7.md` at **five** sites, not one (`## Non-goals` #"adds no order tiebreaker"; `## User-facing API` #"**No order guarantee.**"; `### Decision 8`'s `DjangoListField` boundary bullet; its sibling `DjangoConnectionField` bullet, which carries the unqualified comparative; and the asymmetry-is-deliberate bullet — `orderBy` occurs 3 times in the file); `django_strawberry_framework/list_field.py::DjangoListField`'s docstring, one passage carrying both halves; `docs/GLOSSARY.md` `## \`DjangoListField\`` -> `**Ordering.**`, one paragraph carrying both halves.
   *Why it was not fixed:* one of the three files is a `.py` docstring and **this cycle is declared no-source-and-no-test**, so no round in it could execute the whole-population fix; partial is forbidden by the no-partial-fix rule, whole was out of scope. Takeable only by a cycle that owns source — and if taken, all sites move together.

4. **`docs/GLOSSARY.md` `## \`SyncMisuseError\``'s raising-surface list omits `DjangoListField`, and Round 2 made the omission cost a visible reader round trip.**
   *Source:* `bld-review-2-docs_completion.md` Worker 1 plan-time `### Notes for Worker 1` item 2, Worker 3 `### Notes for Worker 1` item 3 (which asked specifically that the catalog record the round-trip cost), and that round's final-verification disposition 3.
   *Spec clause:* none; F14 dispatched three named amendments to the `djangolistfield` entry only.
   *Description:* the `SyncMisuseError` entry's first bullet enumerates the raising surfaces as the Relay Node defaults' `resolve_node` / `resolve_nodes`, the `DjangoConnectionField` sync pipeline, the optimizer's sync prefetch-child build, and the `FilterSet` related-visibility derive — framing all of them as "when `cls.get_queryset` returns a coroutine". `DjangoListField` belongs on that list **twice over**: its sync default resolver reaches the same raise through `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync`, and `django_strawberry_framework/list_field.py::_require_async_iterable_context` raises the same error for a **different** misuse — an async-only iterable met from synchronous execution — which that entry's `get_queryset`-coroutine framing does not describe at all.
   *The cost, recorded because Round 2 increased it:* the `djangolistfield` entry now carries **two** inbound `#syncmisuseerror` links, and the second one (from the new `**Async-iterable resolvers.**` paragraph) sends a reader to an entry that **does not cover the case they arrived from**. The deferral is still correct — widening the entry redefines another term's scope, and its `**Status:** shipped (\`0.0.5\`)` line belongs to a different card — but it is no longer cost-free.
   *Mechanism when taken:* `docs/GLOSSARY.md` is generated. Edit `GlossaryTerm.body` for anchor `syncmisuseerror` through the Django ORM (`.save()`, never raw SQL) and re-run `scripts/build_glossary_md.py`; never hand-edit the rendered file.

5. **The retired `is_async_callable` characterisation survives on two surfaces Round 1 could not reach.** *(New — surfaced by the integration pass as finding I1; see `docs/builder/bld-020-integration.md`.)*
   *Source:* `docs/builder/bld-020-integration.md` `### Finding I1`.
   *Spec clause:* none; the spec is the surface R1 **fixed**, so no spec edit is owed.
   *Description:* R1's M2 established that `django_strawberry_framework/utils/typing.py::is_async_callable` is not a three-shape, one-hop predicate — `::_callable_inspection_target` peels `functools.partial` **and** `staticmethod` in a `while` loop, so it also sees a raw `staticmethod` descriptor and arbitrary nestings of the two, pinned by `tests/test_list_field.py::test_djangolistfield_async_staticmethod_resolver_gets_get_queryset_applied`. R1 rewrote all six spec sites and drove `one-hop` in the spec from 3 to 0. Two sites outside R1's ownership still carry the retired abbreviation: (i) `docs/GLOSSARY.md` `## \`DjangoListField\``'s opening paragraph — "checked on the resolver, on its `__call__` …, and through a **one-hop** `functools.partial`", closed at three shapes, omitting `staticmethod`, and the file's only surviving `one-hop`; (ii) `django_strawberry_framework/list_field.py` #"``__call__``/``functools.partial``-aware superset of" — the inline comment R1's M2 root-cause note named as the vector that propagated the abbreviation into the spec three times.
   *Measured:* `one-hop` occurrences — spec **0**, rationale **0**, `README.md` **0**, `docs/README.md` **0**, `docs/GLOSSARY.md` **1**, `list_field.py` **0**. `staticmethod` occurrences — spec **11**, rationale **8**, `docs/GLOSSARY.md` **0**, `list_field.py` **0**.
   *Why it was not fixed:* one of the two sites is a `.py` comment, so the same no-source / no-partial-fix pair as item 3 applies. Correcting the glossary alone would make the generated consumer catalog disagree with the source comment a maintainer reads while editing the very branch it describes. Low severity — neither site states a false count, both name the correct authority, and `is_async_callable`'s own docstring is complete; the defect is understatement, and its likeliest victim is a maintainer considering a "harmonization", which the spec now guards against explicitly.

6. **Both baseline gate exceptions, so the next cycle does not re-derive them from scratch.**
   *Source:* `docs/builder/build-020-list_field-0_0_7.md` preamble (exception 1 at pre-flight, exception 2 added mid-cycle by R2's build pass and verified by Worker 0); re-derived by both rounds and again by this gate.
   *Spec clause:* none; `docs/builder/BUILD.md` `## Final test-run gate` licenses a gate to pass on a recorded pre-flight baseline exception.
   *Description:* (a) repo-wide `scripts/check_trailing_commas.py --check` exits **1** on `.claude/projects/-Users-riordenweber-projects-django-strawberry-framework/memory/one-spec-owns-each-feature.md`, an untracked, gitignored agent-memory artifact the checker reaches only because `.claude/` sits inside the working directory — not repository content, and scoped to real files the check exits 0. (b) `scripts/build_tree_md.py --check` reports `docs/TREE.md is not up to date` from the concurrent session's dirty `django_strawberry_framework/utils/converters.py` module docstring (rendered twice, once per layout section) plus its untracked `examples/fakeshop/test_query/test_products_visibility_api.py`; `docs/TREE.md` is clean and **must not be regenerated** while that session's work is mid-flight. Both will resolve on their own — (a) when the checker's traversal is scoped or the file is removed, (b) the moment the concurrent session's `converters.py` change lands and `docs/TREE.md` is regenerated with it.

**Closed rather than carried, listed so nobody re-opens them:** the Slice 5 `KANBAN.md #"## Done"` citation (R2's final verification closed it — true as written, and its only consumer, F13, has landed); the build plan's `### Verified NOT a finding` list (`docs/TREE.md`, `GOAL.md`, `docs/README.md`, `TODAY.md`, `CHANGELOG.md`'s `0.0.7` `### Added` entry); every alternative the rationale records as rejected; and the four artifact-record defects the rounds adjudicated in place (R1's two stated-count corrections under N2, R2's inverted `converters.py` labels, and the non-reproducible `iterdump()` line count).

## Things verified this pass and found wrong

Four, none blocking, none re-worked. Recorded because every document in this cycle is fallible and six such defects have already been caught in it.

1. **The build plan's staged-anchor figure is falsified by the cycle that stated it.** `### Code-completeness verification` says the sweep "returns only two prose mentions inside `docs/SPECS/appx/spec-017-deferred_scalars-0_0_6-rationale.md`". Re-derived here: **four** occurrences. The two new ones are this cycle's own artifacts describing the sweep in prose (`spec-020-…-rationale.md:506` and `bld-review-2-docs_completion.md:584`), so they match the pattern by quoting it. The conclusion — no staged anchor survives in shipped source — is unchanged. **The mechanism is worth carrying: a sweep whose vocabulary appears in the prose that records the sweep counts its own record.** Worker 0 owns the plan; reported, not edited.

2. **The dispatch prompt's baseline-dirty figure no longer holds.** It states "roughly 105 `git status --short` entries"; the tree carries **93** at gate time. The build plan already warns that its enumeration is a pre-flight snapshot rather than a closed set and that the count has drifted (106 -> 105); it has now drifted again. Nothing turns on it — the rule is that any file dirty without a worker's edit is out of scope whether or not it is named — but a count in a dispatch prompt is a claim like any other.

3. **Round 2's stated deferral population is three files and five spec sites.** Its final verification routed the `orderBy` / pk-tiebreaker bundle as "one three-surface bundle (spec Boundary line, `::DjangoListField` docstring, glossary `**Ordering.**`)". The file count is right; inside the spec the population is five sites, three of which carry `orderBy`. Corrected in catalog item 3, so a future cycle taking the bundle whole does not fix `### Decision 8` and leave the `## User-facing API` bullet saying the same thing. Same defect class as item 1 above, one level out.

4. **The cross-round divergence neither round could see** — catalog item 5 / integration finding I1. Not an error in either round's own work: R1 fixed every site it owned and measured the fix, and R2 executed the three amendments it was dispatched. The gap is structural, which is why the integration pass exists.

Everything else in the build plan, both round artifacts, the integration artifact and the dispatch prompt verified as written, including: the "no code gap" conclusion and its 20-item verification table; both baseline gate exceptions and their causes; the two maintainer escalations; the two recorded dispatch deviations; the spec's and rationale's byte counts; the `**Row bound**` 779-byte identity's premise; the `#djangolistfield` cross-file fragment still resolving after R2's regenerate; and the spec's status/header lines.

## Final status

`Status: final-accepted`.

Every gate command passed — the full `pytest --no-cov` sweep, both Django consistency checks, all three read-only lint/format/diff commands — with no failure to attribute to either this cycle or the concurrent session. Floor-verification scope is `none` and no floor claim is left unrun. The gate passes on the two recorded baseline exceptions and on nothing else, and neither was caused by, or fixed by, any pass in this cycle. The `### Deferred work catalog` carries six items with their sources, their licensing (or the explicit absence of it), and their measured populations.

Nothing in this cycle is committed. The maintainer reviews the whole build and commits the artifacts, the spec edits, the `README.md` and `docs/GLOSSARY.md` changes, the `examples/fakeshop/db.sqlite3` row, and the completed plan at their discretion — and is the only party who can run a clean HEAD tree, which is why both baseline exceptions are reported rather than resolved here.

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
