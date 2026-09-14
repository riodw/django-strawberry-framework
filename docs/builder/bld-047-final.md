# Build: Final gate — spec-047 reconciliation round

Spec reference: [`docs/SPECS/spec-047-resource_policy-0_0_14.md`][spec-047] (whole file)
Rationale companion: [`docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`][spec-047-rationale]
Build plan: [`docs/builder/build-047-resource_policy-0_0_14.md`][build-047]
Cohort artifact: [`docs/builder/bld-047-reconcile.md`][bld-047-reconcile]
Status: final-accepted

## Plan (Worker 1)

This is the round's closing gate, authored by Worker 1 as
[`worker-1.md`][worker-1] `## Final test-run gate` requires. The round had a single cohort, so
the cross-slice integration pass has no second cohort to integrate against and the cohort's own
`## Final verification (Worker 1)` discharged the per-slice safety net; `bld-047-integration.md`
was never planned and is not owed. This pass runs the gates and writes the
`### Deferred work catalog`.

### DRY analysis

- **Helper inventory checked.** Not re-refreshed for this pass, and it is current: the
  package-wide AST inventory was run twice during the authoring pass — at `91c2d880` and again
  at `d727a256` after the concurrent commit landed — and `git rev-parse --short HEAD` is still
  `d727a256`, so there has been no diff under `django_strawberry_framework/` since. Shapes
  searched then: `bound`, `narrow`, `min`, `reject`, `policy`, `deadline`, `clear_`, plus the
  seven symbol names the round's findings turn on.
- **Existing patterns reused.** The gate reuses the cohort artifact's own verification
  instruments rather than inventing new ones — the `ast`-based citation resolver, the GitHub
  slug re-derivation, the reference-link use/definition differencer. Each was re-run
  independently here rather than quoted.
- **New helpers justified.** None. The gate writes no code and proposes no helper.
- **Duplication risk avoided.** One: this artifact restating the cohort artifact's findings. It
  does not. It records which gate commands ran, what they returned, what was NOT run and why,
  and the deferred-work catalog — which is this file's alone
  ([`worker-1.md`][worker-1] `## Final test-run gate`, "Worker 1 is its only author").

### Implementation steps

Not applicable; the gate runs commands and records results. It edits no source, no spec and no
prior artifact.

### Test additions / updates

None; this round changes no tests and the gate adds none.

### Implementation discretion items

None. The plan's `## Final-gate exception, recorded in advance` decides which commands run and
which do not; nothing in this pass was left to the author's choice.

---

## Final test-run gate

Grading surface: `HEAD` = `d727a256`, read at the start and at the end of this pass. No
`git stash` / `checkout --` / `restore` / `worktree` was run.

### The suite, `manage.py check`, and `makemigrations --check --dry-run` were NOT run

**This is the pre-flight baseline exception the build plan recorded in advance**
([`docs/builder/build-047-resource_policy-0_0_14.md`][build-047]
`## Final-gate exception, recorded in advance`), and it is a statement about what those
instruments can measure here rather than a waiver.

- **This round changed no `.py` file.** Verified at gate time, not assumed: over this cohort's
  own paths `git diff --name-only` yields exactly the two spec documents, and
  `git diff -- django_strawberry_framework/__init__.py` is empty. `pytest`,
  `manage.py check` and `makemigrations --check --dry-run` all measure executable state this
  cohort did not touch.
- **The tree is not this round's to measure.** `git status --short` at the close of this gate
  carries **14 modified paths and 3 untracked**; the 3 untracked and 2 of the 14 modified are
  this cycle's own (the two spec documents, this artifact, the cohort artifact, and Worker 0's
  build plan). The other **twelve** modified paths are the concurrent spec-050 session's live,
  in-flight work — `django_strawberry_framework/list_field.py`,
  `django_strawberry_framework/resource_policy.py`, `tests/test_connection.py`,
  `tests/test_list_field.py`, `tests/test_resource_policy.py`,
  `examples/fakeshop/test_query/test_list_field_api.py`,
  `examples/fakeshop/test_query/test_list_field_async_api.py`,
  `examples/fakeshop/test_query/README.md`, that cycle's own spec, its build plan, its own
  `docs/builder/bld-final.md`, and one maintainer review input. A suite run here would be
  grading **their** mid-flight state.
  Green would be a pass this round did not earn; red would almost certainly be their
  in-progress refactor, and either reading would be attributed to this cycle by a later reader.
  That is the self-falsifying-instrument shape: a measurement whose subject is not the thing it
  will be quoted about.
- **The absence must NOT be read as a pass.** No claim is made here about the suite, about
  `manage.py check`, or about `makemigrations`. **The spec-050 cycle owes its own final gate
  over the code**, and its own `docs/builder/bld-final.md` is the file that carries it.
- **No repo-wide write-mode invocation was made either**, for the same reason:
  `ruff format .` / `ruff check --fix .` and a bare `check_trailing_commas.py` (whose default is
  a repo-wide auto-fix) would all rewrite that session's tracked and untracked files.
- **No `--cov*` flag was used anywhere in this round**, in any pass.

### Gates that CAN see this cohort's change — all run here, all pass

Worker 0 had already run three of these; each was re-run in this pass rather than quoted.

| # | Command / sweep | Result |
|---|---|---|
| 1 | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-047-resource_policy-0_0_14.md` | **pass** — `OK: 34 terms - all have glossary entries and at least one spec link.`, exit 0 |
| 2 | `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-047-resource_policy-0_0_14.md docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` | **pass**, exit 0. Explicit paths only — never repo-wide |
| 3 | `git diff --check -- docs/SPECS/spec-047-resource_policy-0_0_14.md docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` | **pass** — no whitespace error, no conflict marker, exit 0 |
| 4 | In-page anchors, re-slugged from each file's own headings under the GitHub rules in [`START.md`][start] | **pass** — spec 37 headings / 37 distinct slugs / 22 uses over 14 distinct, **0 dangling**; rationale 30 / 30 / 12 uses over 3 distinct, **0 dangling** |
| 5 | Reference-style links: every `][label]` use against every definition | **pass** — spec **40 / 40**, rationale **17 / 17**, artifact **5 / 5**; 0 undefined and 0 unused in all three |
| 6 | Every link definition's path resolved on disk **from its own file's directory** | **pass** — 0 missing, including the rationale's climb two levels out of `docs/SPECS/appx/` |
| 7 | The 10 canonical group headers, compared against [`START.md`][start]'s ordered list as a sequence | **pass** — present and in order in all three bottom blocks |
| 8 | Cross-file `#anchor` fragments re-slugged against the target file's real headings | **pass** — spec **34, 0 dangling**; rationale **14, 0 dangling** |
| 9 | `path::Symbol` citation sweep, resolved by `ast` parse of a read-only `HEAD` extraction (never by grep, so a name appearing only in a comment or docstring cannot pass) | **pass** — spec **36 citations, 36 resolve**; rationale **11 citations, 3 unresolved and all three expected** |
| 10 | `path #"substring"` citations | **pass** — spec 1, matching **exactly one** source line; rationale 0 |
| 11 | The three deliberately-dead pointers behind gate 9 | **pass** — `git show de2601e9^:django_strawberry_framework/connection.py` carries `_resolve_connection_fast_path` (4 hits); `git show 6013cda6^:django_strawberry_framework/forms/resolvers.py` carries `_run_plain_form_pipeline_sync` (2 hits); `git show 99696bac^:docs/builder/bld-047-remediation.md` returns 5,262 bytes while the path is absent at `HEAD` |
| 12 | Staged-anchor sweep, `grep -rEn 'TODO\(spec-047\|TODO-(ALPHA\|BETA\|STABLE)-047' .` excluding `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` | **pass** — no anchor naming card 047's own work survives anywhere; see the catalog's decoy entry for the 16 `TODO-BETA-047-0.1.2` hits, which are a different card |

The `HEAD` extraction behind gates 9-11 is a read-only `git archive HEAD | tar -x`, with byte
identity against `git show HEAD:<path>` proved by `shasum` for `resource_policy.py`,
`list_field.py`, `connection.py`, `utils/connections.py` and `extensions/resource_policy.py`.
`scripts/check_citations.py` is `path::Symbol`-only and does not gate `docs/` prose, so gates
9-11 are the substitute for a gate that does not exist — and the reason they matter is that a
rotted citation in a shipped spec is exactly what started this round.

### Floor verification

**No floor-verification scope declared.** The build plan declares
`Floor-verification scope: none` and the cohort artifact repeats it, and the declaration is
correct by construction: a documentation-only cohort touches no Django / Strawberry / channels
integration seam. **No floor venv was built, and the shared `.venv` was not mutated by any pass
of this round.** Floor facts, copied from [`BUILD.md`][build] `## Floor verification` because
Decision 13 reasons about version-dependent upstream behavior: the supported floor is Django
**5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**.

### Hot-path budget

**Not applicable; the plan declares no hot path**, and the declaration is correct by
construction — the cohort edits no executable code, so no number could differ before and after.

### Failability proofs

**None owed; this round introduced no new boundary.** Boundary count for the whole round is
zero: no guard, cap, rejection path or validation branch was added, which is also why
[`BUILD.md`][build] `### Slice splitting`'s boundary trigger is answered at zero and the round
is one unit.

### What this round changed, and what was committed

**Files this round changed — four, of which two are tracked source edits:**

| Path | State | Owner |
|---|---|---|
| `docs/SPECS/spec-047-resource_policy-0_0_14.md` | modified, 63,529 → 80,550 bytes | cohort `047-reconcile` |
| `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` | modified, 19,262 → 41,243 bytes | cohort `047-reconcile` |
| `docs/builder/bld-047-reconcile.md` | new, untracked | cohort `047-reconcile` |
| `docs/builder/bld-047-final.md` | new, untracked | this gate |

`docs/builder/build-047-resource_policy-0_0_14.md` also shows untracked. It is Worker 0's plan
for this cycle and belongs to the same commit, but it is not a worker's output.
`docs/builder/worker-memory/047-worker-1.md` sits under a `.gitignore`d path and is never
committed.

**NOTHING WAS COMMITTED.** No pass of this round ran `git commit`, created a branch, switched a
branch, amended, or rewrote history. Only the maintainer commits.

**No code cohort was opened, and the one-line reason is a measurement rather than a judgement:**
the bounds table reconciled **20/20** against the shipped `ResourcePolicy` dataclass with no
default re-valued, every symbol the Implementation plan names resolved at `HEAD` in the file the
table claims except `connection.py::_resolve_connection_fast_path` which a later refactor
deleted while preserving its behavior exactly, and no spec-named test was missing — so nothing
the spec planned was skipped in the code. Every confirmed finding was a spec description that had
drifted or a post-release change the spec never recorded. `docs/builder/bld-047-code.md` was
therefore never created, and the plan's single-cohort ownership partition stands as declared.

**`HEAD` moved mid-round: `91c2d880` → `d727a256`.** The concurrent spec-050 session committed
its work as `d727a256` part-way through the authoring pass, touching four of the files this
round grades against — `django_strawberry_framework/resource_policy.py`,
`django_strawberry_framework/list_field.py`, `tests/test_resource_policy.py` and
`tests/test_list_field.py` — one of which the spec publishes a count from. Everything was
re-measured afterwards. **Every published figure in the spec, the rationale, the cohort artifact
and this file is a `d727a256` reading**, and `HEAD` was still `d727a256` at the close of this
gate. The build plan's baseline-dirty list is consequently stale as a *dirty* list: those files
are committed now. That is recorded rather than rewritten, because the list is what the
authoring pass was dispatched against.

**Two of the round's published test counts are floors, not fixed totals.** The package tier read
**113** functions when this round opened and **117** when it closed, because the concurrent cycle
landed four rows mid-pass. Both readings were correct; neither is durable. The spec therefore
publishes **117 rows / 185 node ids** package and **56 / 56** live as floors with the unit
defined at the point of publication. A later reader measuring more has learned the file grew, not
that the plan is wrong.

### Deferred work catalog

Walked both the authoring and the review passes' `### Notes for Worker 1 (spec reconciliation)`
and `### What looks solid` sections, plus the build plan's scope fence. **Five items are routed
forward and every one names an owner** ([`START.md`][start], "Item routed forward w/o NAMED owner
dies"). Four further items are recorded as closed so no later pass re-derives them.

1. **The `Joint version cut` note in
   `docs/SPECS/appx/spec-047-resource_policy-0_0_14-terms.csv` is falsified and still reads it.**
   Line 30 is `Joint version cut,joint-version-cut,the rule this card is NOT subject to`. Both
   this spec's Decision 12 and its rationale now say the card **is** subject to that rule, so the
   cell contradicts the two documents beside it.
   **Owner: board card `TODO-ALPHA-056-0.0.17` ("Alpha documentation-debt discharge")**, live on
   [`KANBAN.md`][kanban] as both an index row and a card heading, whose ruling item
   `KANBAN.md #"contract text that needs a gate or scratch that must stop asserting statuses"`
   already owns the general question — it matches **exactly one** line and its body records that
   `scripts/check_spec_glossary.py::load_terms` reads `term,anchor` only.
   **Why this cohort could not close it:** the CSV is outside the cohort's declared writable set
   (the ownership partition names the spec, the rationale, this cohort's artifact and its memory
   file, and nothing else), and the `notes` column is **ungated** — `check_spec_glossary.py`
   compares term and anchor only, which is why gate 1 above returns `OK: 34 terms` over a false
   cell and why that green is not evidence about it. `git status --short` on that path is empty:
   untouched.
2. **`clear_resource_context` is a public export of
   `django_strawberry_framework/resource_policy.py` with zero package callers.**
   `grep -rn --include='*.py'` returns four lines at `HEAD`: its definition, its `__all__` entry
   (it is one of the module's 16 names), and an import plus one call in
   `tests/test_resource_policy.py`. The extension now brackets each operation with
   `utils/context.py::restored_context_keys`, which restores a pre-existing outer value instead
   of clearing, so nothing in the package reaches the clear any more.
   **Owner: the maintainer.** Whether to retire a name on a module's published `__all__` is a
   **contract-level** question, not a worker's ([`BUILD.md`][build]
   `### Contract-level findings are escalated as maintainer decisions before dispatch`). It is
   recorded as fact in the rationale and is **not** asserted as a defect against the spec as it
   now reads — the Implementation plan's Slice 1 row is a true statement of what that slice
   landed, and it is load-bearing for the 14 + 2 = 16 arithmetic.
3. **The `KANBAN.md` / `docs/GLOSSARY.md` / `docs/TREE.md` fold-in was deferred by the
   maintainer-set scope fence, not declined by this round.** The build plan's `## Scope fence
   (maintainer-set)` reads "Spec files and `.py` source only. No `KANBAN.md` /
   `docs/GLOSSARY.md` / `docs/TREE.md` fold-in, no DB edits, no regenerates." Recorded here so a
   later reader does not read the round's silence as a judgement that nothing was owed.
   **Owner: the maintainer**, who set the fence and is the only party who can move it.
   **Risk measured rather than assumed:** a sweep of all three rendered surfaces (7,132 lines
   read; positive control `max_list_rows` returns 7 hits, so the instrument is reading them) for
   this round's retired absolutes — `end-of-operation clear`, `single place a non-Relay`,
   `only raw-list bound`, `may evaluate`, `_resolve_connection_fast_path`,
   `_run_plain_form_pipeline_sync`, `only narrowing rule`, `only rejection constructor` —
   returns **zero** occurrences. So no rendered surface currently states a claim this round
   retired. That is a targeted sweep of eight known-retired spellings, **not** a full
   reconciliation of the three surfaces against the corrected spec, and it does not discharge
   the item.
4. **`TODO-BETA-047-0.1.2` survives at 16 sites and is NOT this card's anchor.** It is the old
   numbering of a different, unshipped **search** card, in
   `docs/SPECS/spec-020-list_field-0_0_7.md`,
   `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md`,
   `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md`,
   `docs/SPECS/spec-060-search_fields-0_1_2.md` and
   `examples/fakeshop/apps/products/schema.py`.
   **Owner: `docs/SPECS/spec-060-search_fields-0_1_2.md`'s own Slice 4 row**, which names
   "fix stale `TODO-BETA-047` comment IDs → this card" as slice scope; the products-schema half
   is additionally carried by `TODO-ALPHA-056-0.0.17`'s archived-spec card-id clause. The build
   plan pre-empted it as a decoy and this round deliberately touched none of it —
   `git status --short` carries neither path.
5. **The build plan's own post-release-register prose says "21 touch the spec-047 surface" while
   its table carries 19 in 15 rows.** The `21` was a `91c2d880` measurement; the table is the
   corrected one. The plan is a per-cycle file that closes with the cycle and is untracked today.
   **Owner: Worker 0 at closeout, or the maintainer at commit** — whoever stages
   `docs/builder/build-047-resource_policy-0_0_14.md`. Worker 1 does not edit the build plan
   ([`worker-1.md`][worker-1] `## Scope`). Re-derived here: the table carries **15 rows** and
   **19 distinct shas**, and `git merge-base --is-ancestor` puts all 19 in `567cc6d0..HEAD`.

**Recorded as closed, so no later pass re-derives them:**

- **The register's `19` criterion** — escalated to final verification by Worker 3 and
  **discharged there**, in the rationale. The criterion now reads "read against this contract"
  and states the **15 / 4** split with the rows each occupies. See
  [`bld-047-reconcile.md`][bld-047-reconcile] `### Spec changes made (Worker 1 only)`.
- **The pass-2 report's self-reported artifact link figure, "4 / 4"** — the figure is **5 / 5**,
  re-measured independently at final verification. Recorded, never edited:
  [`ARTIFACT.md`][artifact] `## Re-pass sections` forbids editing a prior entry. Nothing is
  broken and the figure reaches no shipped document.
- **`### Implementation steps` step 19's "the 21 commits"** — the register carries 19.
  Rejected as an edit for the same reason (it sits in `## Plan (Worker 1)`, a prior entry); the
  correction is on the record in the pass-2 report and was verified by pass 2's reviewer.
- **`### Dispatched findings checklist` R-6's citation of `a8f31a2d` "(iv) and (vi)"** — **not**
  an error. It quotes the build plan verbatim, whose own sub-item labels for that commit run
  (i)(ii)(iii)(iv)(vi)(vii), skipping (v); the rationale renumbers them contiguously. Leaving it
  is correct — changing it would have made the box stop quoting its source.
- **The spec's `## Current state` section and the rationale's
  `#### Public symbols the spec did not name` heading** — both deliberately left alone, each
  re-read clause by clause twice by two different reviewers. `## Current state` is
  observation-only under [`BUILD.md`][build] `### ``## Current state``: observations stand,
  predictions do not`; the rationale heading is a past-tense register observation whose
  re-tensing would make the register narrate this round instead of the post-release change it
  exists to describe.

### Summary

The round closes `final-accepted`. It reconciled spec-047 and its rationale companion with what
actually shipped and with the post-release change the spec had never recorded: 34 dispatched
findings, one Medium and nine Low review findings, across two authoring passes and two
independent reviews. It changed no `.py` file and opened no code cohort. Twelve gates ran and
all twelve pass; three gates were deliberately not run and their absence is recorded as an
absence, not a pass. Five items are routed forward, each on a named owner.

### Final status

`final-accepted`.

---

## Gate re-run at 63a132be

Recorded 2026-09-14 by Worker 1 after the pass-3 cycle on
[`bld-047-reconcile.md`][bld-047-reconcile] closed `final-accepted`. `HEAD` = `63a132be` at the
start and at the end of this re-run. No prior section of this file is edited; this section
supersedes `### The suite, manage.py check, and makemigrations --check --dry-run were NOT run`
above for the reason that section itself gave — **the advance exception's second leg is gone.**

**Precondition, verified before anything ran:** `git status --short | grep -cE '\.py$'` → **0**.
The concurrent spec-050 session has committed; the dirty set is documentation, `KANBAN.md` /
`KANBAN.html` / `examples/fakeshop/db.sqlite3` (Worker 0's fence-change rows) and the other
session's staged `docs/builder/` moves. The suite therefore measures `HEAD` and nothing else, and
it ran. This round still changed no `.py`, so a red row would have been graded as `HEAD`'s own
state (test named, owning spec named) and would block nothing this cycle authored; none appeared.

| # | Command, verbatim | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov -q` | **pass** — `7796 passed, 40 skipped in 646.78s (0:10:46)`, exit 0; 0 `FAILED` / `ERROR` lines |
| 2 | `uv run python examples/fakeshop/manage.py check` | **pass** — `System check identified no issues (0 silenced).`, exit 0 |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **pass** — `No changes detected`, exit 0 |
| 4 | `uv run ruff check django_strawberry_framework tests examples` | **pass** — `All checks passed!`, exit 0 |
| 5 | `uv run ruff format --check django_strawberry_framework tests examples` | **pass** — `418 files already formatted`, exit 0 (the standing `COM812` formatter-conflict warning only) |
| 6 | `git diff --check` (whole tree) | **pass**, exit 0 |
| 7 | `git diff --check -- docs/SPECS/spec-047-resource_policy-0_0_14.md docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` | **pass**, exit 0 |
| 8 | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-047-resource_policy-0_0_14.md` | **pass** — `OK: 34 terms`, exit 0 |
| 9 | `uv run python scripts/check_trailing_commas.py --check <spec> <rationale> <both bld-047-*.md>` | **pass**, exit 0 (both artifacts report themselves excluded from the source-layout rules) |
| 10 | `path::Symbol` citations by `ast` against the `63a132be` extraction | **pass** — spec **44 / 44** (32 distinct); rationale **13**, 3 unresolved and all three expected (`connection.py::_resolve_connection_fast_path` ×2, `forms/resolvers.py::_run_plain_form_pipeline_sync`); this file 3, 1 unresolved and expected (the same dead symbol, quoted beside its pointer) |
| 11 | `path #"substring"` citations | **pass** — spec 1, matching exactly one line; rationale 0 |
| 12 | Reference-style links, used vs defined, fenced blocks stripped | **pass** — spec **40 / 40**, rationale **17 / 17**, cohort artifact **5 / 5**, this file **9 / 9**; `used-but-undefined: none`, `defined-but-unused: none` in each; every definition path on disk from its own file's directory |
| 13 | 10 canonical group headers, in-page anchors, cross-file `#anchor` fragments | **pass** — headers present and in `START.md` order in all four files, one link-definitions block each; in-page spec 14 / rationale 3, 0 dangling; cross-file 0 dangling |
| 14 | History sweep over the spec, extended with `now shared|itself moved|would have been the first` | **pass** — 1 line (`:540`, the pre-existing contract sentence); `grep -cE '\b[0-9a-f]{8}\b'` over the spec → 0 |

No `--cov*` flag was used anywhere. No write-mode `ruff` or `check_trailing_commas` invocation
was made. **Nothing was committed.**

### Floor verification, hot-path, failability

Unchanged from the sections above: no scope declared, none applicable, none owed. The round
still edits no executable code.

### Deferred work catalog — addendum

The five catalog items above keep their descriptions; their owners moved under the build plan's
`### Fence change (maintainer, 2026-09-14)`, which routed them onto the board as `CardItem` rows:

1. terms-CSV `Joint version cut` cell → card **`056`**, scope row.
2. `clear_resource_context` public export with zero package callers → card **`053`**, scope row;
   the retirement ruling is recorded as owed, not taken.
3. `docs/GLOSSARY.md` / `KANBAN.md` / `docs/TREE.md` fold-in → card **`056`**, scope row plus its
   existing definition-of-done regenerate line.
4. `TODO-BETA-047-0.1.2` decoy → unchanged (`spec-060` Slice 4 row; `056` for the products-schema
   half).
5. the build plan's stale "21" → **discharged in the plan**: its register prose now reads
   "**15 rows naming 19 distinct commits**" (the count as of `d727a256`; the rationale's own
   register, which is the durable home, carries 16 rows / 20 at `63a132be`).

### Final status

`final-accepted` — now with the suite, `manage.py check` and `makemigrations --check --dry-run`
run rather than recorded as absent.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../../KANBAN.md
[start]: ../../START.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-047]: ../SPECS/spec-047-resource_policy-0_0_14.md
[spec-047-rationale]: ../SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md

<!-- docs/builder/ -->
[artifact]: ARTIFACT.md
[bld-047-reconcile]: bld-047-reconcile.md
[build]: BUILD.md
[build-047]: build-047-resource_policy-0_0_14.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
