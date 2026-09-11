# Package build plan: serializer_mutations / 0.0.13 (039) — residual-reconciliation cycle

Spec source: `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` (archived; shipped in `0.0.13`)
Companion CSV: `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-terms.csv`
Companion rationale: `docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md` (**does not exist — Slice 0 creates it**)
Target release: `0.0.13` (already cut; no version edit lands in this cycle)
Date created: 2026-09-04
Build rule: one slice at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.

**The ten per-cycle `bld-039-*` artifacts this file cites were deleted when the cycle
closed.** Only this file and the build plan were kept. Every citation below to
`bld-039-slice-0-rationale_extraction.md`, `bld-039-audit-1-converter_and_inputs.md`,
`bld-039-audit-2-sets_and_bind.md`, `bld-039-audit-3-resolvers_and_live.md`,
`bld-039-audit-4-decisions_rev6_dod.md`, `bld-039-slice-2a-contract_fold_in.md`,
`bld-039-slice-2b-label_strip_and_citers.md`, `bld-039-slice-2c-rev6_retirement.md`,
`bld-039-slice-3-code_gaps.md` or `bld-039-integration.md` - including its raw `:NN` line
numbers - resolves against commit `d401343c`, which is the last commit that carried them:
`git show d401343c:docs/builder/<name>`.

## What this cycle is

`spec-039` shipped. Its implementation is committed and live; its `-rationale.md`
sibling was never written, and the spec has not been reconciled against what the
tree actually holds. This cycle is the **residual-reconciliation** shape the
`spec-037` and `spec-038` cycles already ran (`docs/builder/DONE/build-038-form_mutations-0_0_12.md`):

1. **Write the missing rationale companion** — the deliberative layer moved out of
   the spec, keyed to the Decision it belongs to (`docs/builder/BUILD.md`
   `## Spec rationale extraction`).
2. **Audit every spec contract row against `HEAD`** — did anything the spec planned
   get skipped, dropped, or silently built differently? Grade every row.
3. **Reconcile the spec to what landed.** Where later work corrected or superseded a
   contract, the spec states the **corrected contract directly**, with no chronology
   (`docs/builder/BUILD.md` `## Spec rationale extraction`, "the spec never narrates
   its own history"). **Every explanation of a change — what changed, why, what it
   replaced — goes in the rationale file, never in the spec.**
4. **Fix the code** only where the audit proves a planned behavior never landed.

**Maintainer-set fence for this cycle: spec files and `.py` files ONLY.**
No `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `docs/TREE.md` / `TODAY.md` /
`README.md` / `docs/README.md` / `CHANGELOG.md` / `GOAL.md` edits, no kanban-DB
writes, no closeout agentflow edits, no `docs/builder/BUILD.md` or `worker-*.md`
edits. The spec is **already archived** at `docs/SPECS/`; no move is owed.

**Every file this cycle creates carries `039` in its name** (maintainer instruction).

## Pre-flight

Pre-flight: passed on 2026-09-04.

- **1. Working-tree baseline.** `git status --short` → `M docs/feedback.md` only.
  Baseline-dirty, out of scope: workers neither edit nor revert it, and per
  `AGENTS.md` it is never named in code, commits, or the board.
- **2. `scripts/review_inspect.py`** smoke-ran clean against
  `django_strawberry_framework/rest_framework/hook_context.py`.
- **3. Build-artifact reset — DELIBERATELY SKIPPED,** under the
  `docs/builder/BUILD.md` `### Cohorting, naming, and closure` round exception. The
  `docs/builder/bld-slice-*.md`, `bld-integration.md`, `bld-final.md`, and
  `build-050-list_field_arguments-0_0_15.md` files on disk are the **live `spec-050`
  cycle's** tracked artifacts — concurrent work (`AGENTS.md` rule 34). Deleting them
  is the one irreversible pre-flight mistake. Verified instead: no `docs/builder/*039*`
  path exists. This cycle's `039`-stamped names cannot collide with them.
- **4. `.gitignore`** lists `docs/builder/worker-memory/`, `docs/shadow/`, and
  `docs/builder/temp-tests/`.
- **5. Scratch clear — SCOPED, not global,** for the same concurrency reason. This
  cycle writes `docs/builder/worker-memory/039-worker-<N>.md` and
  `docs/builder/temp-tests/039-<slice>/`; it never touches the unprefixed paths.
- **6. Spec-doc consistency.**
  `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-039-serializer_mutations-0_0_13.md`
  → `OK: 38 terms`.
- **7. Spec rationale extraction** — **owed by Slice 0 of this cycle**; it is the
  cycle's own first deliverable rather than a precondition, because writing it *is*
  the work. No audit slice dispatches until Slice 0 is `final-accepted`.

## Baseline-dirty, out-of-scope files

- `docs/feedback.md` — maintainer review input. Never edit, never revert, never name.
- Everything under `docs/builder/` that does **not** carry `039` in its name —
  the concurrent `spec-050` cycle. Read-only at most.

## Build-wide declarations

- **Ownership partition.** The four audit passes (Slices 1a–1d) are **read-only**:
  each writes exactly one artifact and no source. Their artifacts are disjoint by
  construction, so they dispatch **concurrently**. Every other slice is sequential.
  - Slice 1a → `docs/builder/bld-039-audit-1-converter_and_inputs.md`
  - Slice 1b → `docs/builder/bld-039-audit-2-sets_and_bind.md`
  - Slice 1c → `docs/builder/bld-039-audit-3-resolvers_and_live.md`
  - Slice 1d → `docs/builder/bld-039-audit-4-decisions_rev6_dod.md`
  - Slices 0, 2, 3, 4, integration, final → sole owner, sequential.
- **Hot-path declaration.** `none` for Slices 0–1d (no executable change). Slice 3
  is declared hot-path **only if** an audit finding requires a change on the
  serializer resolver's per-request path; the plan is amended at that point.
- **Floor-verification scope.** `none` for Slices 0–2 (docs and comment-only edits
  touch no framework seam). Slice 3, if it lands, re-declares: any change inside
  `rest_framework/resolvers.py` or `rest_framework/sets.py` touches the DRF /
  Strawberry integration seam and owes a focused floor run at the floor recorded in
  `docs/builder/BUILD.md` `## Floor verification` — Django 5.2.16, Python 3.10,
  strawberry-graphql 0.316.0.

## Known hazard carried into this cycle

`spec-039` carries **202 process labels** (`P1.1`…`P3`, `F1`…`F11`, `M1`…`M4`,
`H2`) in its prose. Every prior residual cycle stripped that vocabulary from its
spec (030, 036, 037, 038 all carry zero), and `AGENTS.md` bans process provenance
from standing prose. **Stripping a label vocabulary is a RENAME that strands every
citer, and no gate in this repo can see it** — `scripts/check_citations.py` is
`path::Symbol`-only. Population at plan time: **159** `spec-039` mentions across
`.py` files, of which **16** carry a label token. Because this cycle's fence
already includes `.py` files, the strip and the citer sweep land **in the same
cycle** (Slice 2), never split across cycles.

## Worker-0 pre-dispatch verification for Slice 2 (measured 2026-09-04, post-Slice-0)

`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before
dispatching` applies: the label strip is dispatched against a measured population.

**Spec side.** Instrument: `(^|[^A-Za-z0-9_])(P|F|M|H|D)[0-9]+([.-][0-9A-Za-z]+)?` over
the post-Slice-0 spec. **175 occurrences over 37 distinct tokens** (`P1`, `P1.1`-`P1.7`,
`P2`, `P2.1`-`P2.7`, `P3`, `F1`-`F11`, `M1`-`M5`, `H2`, `H3`, `H5`, `H6`). Worker 1
measured 165 with a right-word-boundary instrument. **Neither number is authoritative;
re-derive.** The instruments disagree because a right word boundary cannot see `P1.6`
inside `(P1.6, M4)`. Publish no figure from one glob.

Three sub-populations behave differently and must not be swept as one:

1. **Body labels** - `(**P1.4**)`, `(M3)`, `(**F10**)` inline in prose. Delete the token;
   **keep the clause it justified**. `START.md` "Style Rio cares about": removed
   attribution carried the WHY, so restate it as one plain clause from the code.
2. **Heading labels** - `### Promotions to single-site now (P1 - third-copy forks)`,
   `### Single-siting that prevents drift (P2)`, `### Small reuses to pin; deliberately
   not applicable (P3)`. Editing these **changes the GitHub anchor slug** and strands
   every in-page `](#...)` link plus the reuse table's row keys. Re-point in the same pass.
3. **Review-round attribution** - `rev2 P2`, `review P1`, `review follow-on P2`. Worker
   and round provenance, banned outright by `AGENTS.md` and `START.md`.

**Not in the population: `G2`.** 11 occurrences, and it is `spec-036`'s label cited from
here - a foreign-spec citation, not this spec's own vocabulary. It stays.

**`.py` side - 21 citing lines across 8 files** (instrument: per-line `spec-039` plus a
label match, widened by a +/-3-line context window, since a citation wrapped across two
lines is invisible to a per-line grep): `forms/inputs.py` (3), `mutations/inputs.py` (2),
`rest_framework/inputs.py` (5), `rest_framework/resolvers.py` (4),
`rest_framework/serializer_converter.py` (3), `rest_framework/sets.py` (3),
`utils/inputs.py` (1). 36 `.py` files mention `spec-039` in total; the rest are bare
`spec-NNN` provenance pointers, which `AGENTS.md` explicitly keeps. **Only the labelled
ones rot,** and each carries a substantive clause, so each is a rewrite, never a deletion.

## Audit rollup (Slices 1a-1d, all four `review-accepted` 2026-09-04)

| Cohort | Rows | BUILT-CONFORMANT | SPEC-STALE | DEVIATED | SUPERSEDED | PARTIAL | DROPPED |
|---|---|---|---|---|---|---|---|
| 1a converter + inputs | 71 | 61 | 9 | 0 | 0 | - | **1** |
| 1b base + bind + export | 92 | 80 | 9 | 0 | 3 | - | 0 |
| 1c resolver + live surface | 50 | 33 | 8 | 3 | 3 | 3 | 0 |
| 1d Decisions + rev6 + DoD | 105 | 90 | 10 | 0 | 5 | - | 0 |
| **total** | **318** | **264** | **36** | **3** | **11** | **3** | **1** |

**The cycle's headline answer: nothing planned was skipped in the code.** One row of 318
was never built, and it is a guard rather than a feature - the Slice-1 DRY import ratchet.
Every other divergence is the spec describing the tree wrongly, which is a spec edit.

## Worker-0 verification of every code-bearing finding

`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before
dispatching`. A reviewer's prescribed remedy is a hypothesis; four findings were checked
at HEAD and one was re-graded down.

1. **CONFIRMED - the DRY import ratchet was never written** (1a, Medium). No test under
   `tests/rest_framework/` asserts an import or identity obligation; no `scripts/` guard
   names `rest_framework`. The **contract it protects holds** - the promoted symbols have
   0 definitions under `rest_framework/` - so this is a ratchet to add, not a repair, and
   identity (`a is b`) beats a grep, which a same-named local satisfies. **Worker 1's
   planning pass corrected the symbol list this section first carried:** three of the six
   names are bound in neither target module, so a ratchet built from them would
   `AttributeError` on correct code. The manifest to build from is Worker 1's measured
   18 identity rows + 2 `__code__` rows, not any list in the spec or this plan.
2. **CONFIRMED - the G2 "no `.only(...)`" claim has never been tested** (1c, High). In
   `examples/fakeshop/test_query/test_products_api.py` the comment
   #"G2 NO `.only(...)` projection" is followed by an assertion that queries
   `models.Item.objects.values_list` **afresh**; it never reads the captured SQL and
   passes with the projection gate either way. The two absolute query-count assertions
   beside it (2 and 3) DO distinguish batching. The form flavor holds the correct shape at
   `tests/forms/test_resolvers.py` #"plan.only_fields == ()".
3. **CONFIRMED - a fail-open guard** (1c, Medium).
   `rest_framework/resolvers.py::_assert_field_agreement` does
   `getattr(mutation_cls, "_mutation_meta", None)` then returns on `None`, skipping the
   requiredness and annotation-drift arms, while the same module dereferences
   `mutation_cls._mutation_meta.<attr>` **unguarded at four other sites**. Worker 1's
   planning pass then proved the attribute **cannot legitimately be absent** three
   independent ways, so the fix is `raise`, not `return` - and it takes the two sibling
   `getattr` defaults on the same four lines with it, since fixing one spelling and
   leaving two is precisely what `### Fail-open shapes` warns against.
4. **RE-GRADED DOWN to Low - the request-identity guard is half-pinned, not unpinned**
   (1d). The **rejection** arm is pinned by `tests/rest_framework/test_resolvers.py`
   #"a DIFFERENT request object", and the `write_alias` twin by its own conflicting-alias
   row. Only the **tolerance** arm - a hook echoing the framework's own request object
   must be permitted - has no row. A missing assertion over correct behavior on a
   non-rejection path: Low, not Medium.

## Dispatch-order amendment: Slice 3 runs BEFORE Slice 2

- **They collide on one file.** Slice 2's citation sweep edits comments in
  `rest_framework/resolvers.py`; Slice 3's fail-open fix edits its body.
  `docs/builder/BUILD.md` `### Parallel cohorts under a declared ownership partition`:
  one shared file serializes two cohorts, whatever the overlap's size.
- **The spec should describe a settled tree.** Writing the corrected contract first and
  then changing the guard would re-stale the spec inside the same cycle.

Ownership: **sequential, sole owner each.** Slice 3 owns `rest_framework/resolvers.py`
and every test file it touches; Slice 2 owns the spec, the rationale companion, and the
comment lines in the eight citing `.py` files - taking `resolvers.py` only after Slice 3
is `final-accepted`.

## Grading vocabulary (Slices 1a–1d)

Every spec contract row is graded exactly one of:

- **BUILT-CONFORMANT** — the spec says it, `HEAD` does it, cited by
  `path::QualifiedName`.
- **SPEC-STALE** — behavior is correct at `HEAD`, the spec's description of it is
  not. Spec edit owed (Slice 2); no code change.
- **DEVIATED** — built, but differently from the spec, deliberately. Spec edit owed
  **plus** a rationale entry naming what changed and why.
- **SUPERSEDED** — a later card / hardening pass replaced the contract. Same
  obligation as DEVIATED, plus the superseding card named.
- **DROPPED** — planned, never built, nothing supersedes it. **This is the finding
  the cycle exists to catch.** Escalates to a Slice 3 code pass.

A row graded anything but BUILT-CONFORMANT with no cited evidence is not a grade.

## Artifact list

- `docs/builder/bld-039-slice-0-rationale_extraction.md`
- `docs/builder/bld-039-audit-1-converter_and_inputs.md`
- `docs/builder/bld-039-audit-2-sets_and_bind.md`
- `docs/builder/bld-039-audit-3-resolvers_and_live.md`
- `docs/builder/bld-039-audit-4-decisions_rev6_dod.md`
- `docs/builder/bld-039-slice-2a-contract_fold_in.md`
- `docs/builder/bld-039-slice-2b-label_strip_and_citers.md`
- `docs/builder/bld-039-slice-2c-rev6_retirement.md`
- `docs/builder/bld-039-slice-3-code_gaps.md`
- `docs/builder/bld-039-integration.md`
- `docs/builder/bld-039-final.md`

## Checklist

- [x] Slice 0: write the rationale companion; move the spec's deliberative layer out -> `docs/builder/bld-039-slice-0-rationale_extraction.md`
- [x] Slice 1a: audit Slice 1 contracts (serializer converter + generated inputs) -> `docs/builder/bld-039-audit-1-converter_and_inputs.md`
- [x] Slice 1b: audit Slice 2 contracts (`SerializerMutation` base, `Meta`, bind, clear seam, root export) -> `docs/builder/bld-039-audit-2-sets_and_bind.md`
- [x] Slice 1c: audit Slice 3 contracts (resolver pipeline + products live surface + test placement) -> `docs/builder/bld-039-audit-3-resolvers_and_live.md`
- [x] Slice 1d: audit Decisions 1-14, Round-6 items #1-#17, Edge cases, Test plan, Definition of done -> `docs/builder/bld-039-audit-4-decisions_rev6_dod.md`
- [x] Slice 2a: fold the shipped contract into the Decisions; discharge every SPEC-STALE / DEVIATED / SUPERSEDED row and the eight Slice-3 deferrals -> `docs/builder/bld-039-slice-2a-contract_fold_in.md`
- [x] Slice 2b: strip the process-label vocabulary; re-point headings and anchors; sweep the `.py` citers -> `docs/builder/bld-039-slice-2b-label_strip_and_citers.md`
- [x] Slice 2c: retire the `rev6` round vocabulary (deferred out of 2b, same rule, own anchor risk) -> `docs/builder/bld-039-slice-2c-rev6_retirement.md`
- [x] Slice 3: close every DROPPED row in code -> `docs/builder/bld-039-slice-3-code_gaps.md`
- [x] Cross-slice integration pass -> `docs/builder/bld-039-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-039-final.md`

## Slice 2 split, and why

`docs/builder/BUILD.md` `### Slice splitting`: the unsplit Slice 2 is two unrelated
diffs sharing a file. **2a** rewrites contracts - the 178-line hardening blockquote
folded into Decisions 7/8/12, 36 SPEC-STALE rows, 3 DEVIATED, 11 SUPERSEDED, and the
eight deferrals Slice 3's final verification handed forward. **2b** is a mechanical
vocabulary strip whose risk is entirely different: it renames three headings (changing
their GitHub anchor slugs), and it edits 21 comment lines across 8 shipped `.py` files.
Reviewing them as one diff would bury each in the other.

**Worker 1 runs both alone**, on the maintainer's instruction that a spec-only change
needs no builder. 2b's `.py` edits are comment-only, so that pass owes the **inverse
proof** a comment-only edit always owes: AST identity with docstrings stripped, against
a **pre-edit** copy of each file. `git show HEAD:` is not the reference for
`rest_framework/resolvers.py` - Slice 3 changed its body, and that change is not yet
committed.

## Census correction from Slice 2b (supersedes this plan's own figure)

The **186** occurrences this plan recorded for Slice 2b were **9 too many**: the
instrument's right edge was unbounded, so `M2` matched inside `M2M`, which the spec
says nine times. The true pre-strip population was **177 occurrences over 37 tokens,
plus one `Medium-7`** that no `P|F|M|H|D` glob can see - 178. Slice 2b measured with
five independent instruments and reported which produced each figure.

The same glob under-counted the `.py` side: it missed `Md1`-`Md7`, `M1a`, `SR-3`,
`H4`, `D8`, and the bare severity words `High` / `Medium`. The real sweep was **15**
files, not the 8 this plan named.

Both errors are the same defect - a **positive-vocabulary census misses whatever it was
not written to see** - and both were caught only by a second instrument. No figure in
this cycle is published from one glob.

## Slice 2c, and why the deferral could not stand

Slice 2b retired spec-039's severity and promotion vocabulary but left **`rev6`**:
62 occurrences in the spec, 18 in the companion, and 17 `### rev6 #N` headings.
`rev6` is review-round attribution, banned by the same `AGENTS.md` and `START.md`
clause that licensed the rest of the strip - so leaving it is the
`START.md` #"Partial claim fix" hazard, where one spelling is fixed and the parallel
site stays live until the cycle reopens. 2b deferred it only because its own dispatch
scoped headings to three and retiring `rev6` re-keys `## Round-6 improvements`, an
anchor both files link. That is a reason for its own pass, not for leaving it.
