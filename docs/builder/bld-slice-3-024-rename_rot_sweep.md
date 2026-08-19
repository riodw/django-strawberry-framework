# Build: Slice 3 — Rename-rot sweep and citation repair

Spec reference: `docs/SPECS/spec-024-django_trac_37064_hardening-0_0_7.md` (a card-snapshot stub; the
cycle rewrites it in Slice 2). Authorising plan clause:
`docs/builder/build-024-django_trac_37064_hardening-0_0_7.md` `## Artifact list` — "A code-repair
artifact `docs/builder/bld-slice-3-024-<slug>.md` is added to this list if and only if Slice 1
surfaces a real code gap."
Status: final-accepted

## Plan (Worker 2, written in lieu of a Worker 1 planning pass)

Slice 1 skipped its planning pass by the plan's recorded dispatch deviation, and the repair cohort it
licenses inherits that shape. The plan section below is therefore authored by the builder before the
build, per this cycle's dispatch instruction; Worker 3 reviews it alongside the diff.

### The defect, as Slice 1a recorded it

`django_strawberry_framework/_strawberry_patches.py` cites
`_django_patches._UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` in its module docstring. That symbol
does not exist. Commit `eb2a1764` ("feat(patches): supersede both audited upstream teardown bodies")
replaced the single pinned upstream body with a tuple of audited bodies and renamed the constant,
without the `::OldName` grep sweep `AGENTS.md` rule 27 requires in the same change ("renaming a
symbol means grep-sweep `::OldName` in the same change"). This slice repairs that violation.

Severity: **Low** by `docs/builder/BUILD.md` `## Severity definitions` — "comments or docstrings
stale or wrong but not load-bearing". Nothing executable reads the cited name.

### DRY analysis

- No logic is added, moved, or shared. The change is docstring text.
- The reusable asset produced here is the **instrument**, not code: two mechanical resolvers
  (retired-name extraction from the surface's own history; unresolved-citation detection over
  comments and docstrings) are recorded under `### Rename-rot population` so a later cycle can re-run
  them rather than re-derive them.
- No duplication is introduced: the repaired sentence cites one symbol at one site.

### Implementation steps

1. Derive the retired-name population from the code's history rather than from the dispatch's sample
   list (`django_strawberry_framework/_django_patches.py`,
   `django_strawberry_framework/testing/_wrap.py` and their pre-rename `test/` twins, plus
   `apps.py` and the three test modules): AST-parse every historical revision, union every name ever
   defined, subtract every name defined anywhere at HEAD.
2. Sweep the `.py` corpus (`django_strawberry_framework/`, `tests/`, and `examples/` + `scripts/` as
   evidence) for each retired name, counting **occurrences**, not matching lines.
3. Run a second, independent instrument that does not depend on the candidate list at all: resolve
   every `module.Symbol` and `path.py::Symbol` citation appearing in a comment or docstring across
   the package and test trees against the definitions that actually exist at HEAD.
4. Repair each confirmed in-scope rot so the citation names a symbol that exists **and** the
   surrounding sentence stays true. Read `_django_patches.py` to choose the target: more than one
   candidate exists after `eb2a1764`, and the one carrying the reimplementer's-contract idea is the
   one to name.
5. Record every out-of-scope surface (standing docs, non-024 modules) as a deferred item instead of
   fixing it, per the cycle's maintainer scope restriction.

### Test additions / updates

None, and none are owed. This slice changes no executable line, so there is no behaviour to pin. The
focused scope below is run as a regression check that the docstring edit did not break import or
collection, not as new coverage.

### Implementation discretion items

- Whether to upgrade the citation's **form** from the module-dotted `_django_patches._SYMBOL` spelling
  to the `path::QualifiedName` form `AGENTS.md` rule 27 prefers. Decided: keep the existing form. The
  defect is the name, not the spelling, and the surrounding paragraph uses the module-dotted form
  consistently; a form change would broaden the diff without repairing anything.

### Dispatched findings checklist

- [x] Repair `_strawberry_patches.py`'s citation of the symbol `eb2a1764` renamed away, so the
      citation resolves and the sentence stays true (do not delete the cross-reference, do not weaken
      the claim).
- [x] Sweep the whole retired-name population, derived from the code's own history rather than from
      the dispatch's sample list, across every `.py` file under `django_strawberry_framework/` and
      `tests/`.
- [x] State every count as a measured occurrence count.
- [x] Run the formatters and classify the resulting `git status --short` churn.
- [x] Run the focused scope and record pass/fail.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short`. Exactly one tracked file changed by this pass:

- `django_strawberry_framework/_strawberry_patches.py` — module docstring only. One token replaced:
  `_django_patches._UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` ->
  `_django_patches._AUDITED_REMOVE_DATABASES_FAILURES_SOURCES`. Full diff is 1 line changed,
  1 inserted / 1 deleted.

Also created by this pass: this artifact, and an appended entry in the gitignored
`docs/builder/worker-memory/worker-2-024.md`.

Every other entry in `git status --short` is on the plan's baseline-dirty list or is another cycle's
untracked artifact; the before-and-after listings are byte-identical (see `### Validation run`).

#### Choosing the target symbol

`eb2a1764` replaced one pinned body with a set, so the rename left four candidates in
`_django_patches.py`:

| Candidate | Why not / why yes |
|---|---|
| `_CLASS_ATTRIBUTE_REMOVE_DATABASES_FAILURES_SOURCE` | One member of the audited set (Django 5.2.16-6.0.x). Naming it would make the cited contract narrower than it is. |
| `_CONNECTION_FEATURE_REMOVE_DATABASES_FAILURES_SOURCE` | The other member (Django 6.1). Same objection. |
| `_validated_remove_databases_failures_source` | Module-level mutable state holding whichever body `apply()` validated at runtime. It is a *result* of the contract, not the contract. |
| `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` | **Chosen.** It is the constant `_django_patches::_validate_upstream_shape` pins, and the constant whose own leading comment states the reimplementer's contract verbatim: "Because :func:`_patched_remove_databases_failures` REIMPLEMENTS upstream's whole loop instead of wrapping and delegating to it, an upstream body change does not flow through the patch the way it does for the delegating siblings (``_cross_web_patches``/``_strawberry_patches``). ``_validate_upstream_shape`` therefore pins these sources". `_django_patches::_validate_upstream_shape`'s docstring names the same idea — "The body pin is the reimplementer's equivalent of the sibling patches' delegation" — and `_strawberry_patches::_validate_upstream_shape`'s docstring already calls it "the ``_django_patches`` precedent". |

Target resolution, measured after the edit: `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` occurs
**5** times in `django_strawberry_framework/_django_patches.py`
(`grep -o '_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES' django_strawberry_framework/_django_patches.py | wc -l`),
of which one is its definition at
`django_strawberry_framework/_django_patches.py #"_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES: tuple[str, ...] = ("`.

The repaired sentence, unchanged apart from the token:

> Because the shield is a *reimplementation* rather than a delegating wrapper,
> ``_validate_upstream_shape`` pins the superseded upstream body source (the reimplementer's contract
> established by ``_django_patches._AUDITED_REMOVE_DATABASES_FAILURES_SOURCES``) so an upstream body
> change fails loudly at ``apply()`` time instead of being silently superseded.

The claim survives the repair intact: `_strawberry_patches` still pins exactly one superseded body
(`_UPSTREAM_PARSE_QUERY_PARAMS_SOURCE`), and the precedent it credits is still `_django_patches`'s
body pin — which is now a set of two audited bodies rather than one. Nothing was deleted or weakened.

### Rename-rot population

Two independent instruments were run. The first takes the dispatch's sample as a *starting* list and
replaces it with a measured population; the second does not consult any candidate list at all, so a
name nobody thought to list is still caught.

#### Instrument 1 — retired-name extraction from the surface's own history

Method: `git log --format=%H --all --` over card 024's surface files
(`_django_patches.py`, `testing/_wrap.py`, `testing/__init__.py`, their pre-rename
`django_strawberry_framework/test/` twins, `apps.py`, `tests/test_django_patches.py`,
`tests/testing/test_wrap.py` and its `tests/test/` twin, `tests/test_apps.py`) yields **61**
revisions. Each revision of each path is AST-parsed and every `FunctionDef` / `AsyncFunctionDef` /
`ClassDef` / `Assign` / `AnnAssign` target name collected: **126** distinct names ever defined.
Subtracting every name defined anywhere in the HEAD `.py` corpus
(`django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`) leaves **9** retired names.

That is the population. The dispatch's sample named 3 of the 9 (`_PATCH_APPLIED`,
`_missing_symbol_logged`, `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE`) plus the package-path rename;
6 were found only by the extraction.

Sweep command, run once per name (occurrences, not matching lines):

```shell
grep -rho --include='*.py' "<name>" django_strawberry_framework tests examples scripts | wc -l
```

| Retired name | `.py` occurrences | Disposition |
|---|---|---|
| `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` | 1 | **FIXED** — the confirmed defect, `_strawberry_patches.py` module docstring. |
| `_PATCH_APPLIED` | 0 | Not present. |
| `_missing_symbol_logged` | 0 in `.py` | Not present in code. 2 occurrences repo-wide, both in `docs/dry/dry-0_0_11.md` — a per-cycle DRY scratchpad, exempt from the symbol convention by `START.md` "Temp artifact conventions" and out of this cycle's scope. Recorded, not fixed. |
| `_unpatched` | 0 as a whole token | The unfiltered substring grep returns 6 hits, every one of them inside a live longer name (`test_unpatched_remove_databases_failures_crashes_on_non_wrapper`, `upstream_unpatched`, `package_unpatched`). Word-boundary count `grep -rnoE '\b_unpatched\b'` = **0**. A substring grep is not a citation count. |
| `sentinel_wrapper` | 0 | Not present. |
| `skip_records` | 0 | Not present. |
| `test_apply_logs_missing_symbol_notice_only_once` | 0 | Not present. |
| `test_apply_no_ops_when_database_failure_symbol_missing` | 0 | Not present (superseded by `..._fails_loudly_...` at `8e86e777`, per Slice 1a). |
| `test_patch_is_installed_on_transaction_test_case` | 0 | Not present. |

Package-path rename `django_strawberry_framework/test/` -> `testing/` (`e145ba36`):

```shell
git grep -ohE 'django_strawberry_framework/test/|django_strawberry_framework\.test\b|tests/test/' -- . | wc -l
```

**0** occurrences in any `.py` file. 9 occurrences repo-wide: 6 in `KANBAN.html`, 2 in `KANBAN.md`,
and the `examples/fakeshop/db.sqlite3` rows that generate both. All are **not rot** — the two KANBAN
rows read
`` `django_strawberry_framework/test/__init__.py` (historical) `` and
`` `django_strawberry_framework/test/_wrap.py` (historical) ``, which is the board's deliberate
`TrackedPath.is_current=False` spelling for a path a card touched before it moved. Verified by reading
`KANBAN.md #"#### Package files"` under the card-024 entry. No edit owed anywhere.

#### Instrument 2 — unresolved-citation detection, no candidate list

Method: tokenize + AST-parse every `.py` file under `django_strawberry_framework/` and `tests/`,
extract every comment and every module/class/function docstring, then resolve each citation of the
forms `module.Symbol` and `path.py::Symbol` against the set of names actually defined at HEAD. This
instrument has no input from the dispatch or from instrument 1.

Result over the card-024 surface: exactly **one** unresolved private-symbol citation,
`_django_patches._UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE`, at
`django_strawberry_framework/_strawberry_patches.py` module docstring. The two instruments agree, and
the agreement is what makes the population claim a measurement rather than a sample.

The same run surfaced **7 unresolved citations outside card 024's surface** (see
`### Notes for Worker 1 (spec reconciliation)`). Those are a different card's rename rot; per the
dispatch's do-not-touch clause they are recorded, not fixed. Third-party citations
(`django/...`, `strawberry/...`, `strawberry_django/...`, `django_graphene_filters/...`,
`graphene_django/...`) resolve to no in-repo file by construction and are not rot; deliberate
family-prefix citations with a trailing underscore (`tests/types/test_resolvers.py::test_check_n1_`,
`tests/optimizer/test_extension.py::test_strictness_raise_`) are likewise not rot.

#### Post-fix measurement

```shell
grep -rho --exclude-dir=.git --exclude-dir=__pycache__ '_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE' . | wc -l
```

**6** occurrences remain, in **3** files, all of them per-cycle `docs/builder/` scratchpads that quote
the defect as evidence and all of them on this cycle's do-not-touch list:
`bld-slice-1a-024-planned_vs_head.md` (3), `bld-slice-1b-024-divergence_and_floor.md` (2),
`build-024-django_trac_37064_hardening-0_0_7.md` (1).

Occurrences in `.py` files anywhere in the tree: **0**
(`grep -rho --include='*.py' '_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE' django_strawberry_framework tests examples scripts | wc -l`).
Occurrences in git-tracked non-scratchpad files: **0**
(`git grep -oh '_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE' -- . ':!docs/builder' | wc -l`).

### Tests added or updated

None. This slice changes no executable line; there is no behaviour to pin and nothing that could
regress an assertion. Adding a test that greps a docstring would pin the prose, not a contract.

### Validation run

- `uv run ruff format .` — pass. Reported `424 files left unchanged`. **Nothing was reformatted**, mine
  or anyone else's. (The run also prints the standing `COM812` formatter-conflict warning, which is
  pre-existing configuration noise, not a result of this pass.)
- `uv run ruff check --fix .` — pass, `All checks passed!`. No fixes applied.
- `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/_strawberry_patches.py`
  — pass, silent (ASCII-only and layout rules hold; the replacement token is ASCII).
- `git status --short` before and after both ruff invocations — **byte-identical listings**, 31 entries
  each (32 once this artifact was written). The only slice-intended tracked entry is
  `M django_strawberry_framework/_strawberry_patches.py`. Every other entry is either on the plan's
  `### Baseline-dirty, out-of-scope` list or is an untracked artifact of the 023 cycle / this cycle's
  own earlier slices. Nothing was reverted; nothing needed to be. This is the "report anything the
  repo-wide `ruff format .` touched that is not yours" obligation discharged with a null result.
- Focused scope, run as instructed:
  `uv run pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py tests/test_strawberry_patches.py --no-cov`
  — **pass, 91 passed in 1.69s**, 0 failures, 0 errors, 0 collection errors. No coverage-shaped flag
  other than the mandatory `--no-cov`.

### Failability proofs

`None; this pass introduced no new boundary.` This slice edits docstring text only — no guard, gate,
rejection path, or invariant is added, moved, or altered, which is exactly the
"renamed symbols, relocated bodies, added annotations, doc edits" exemption in `docs/builder/BUILD.md`
`### What needs a proof, and what does not`. The proof obligation that *does* apply here is the
stated-count rule in `## Claims are proven mechanically, never accepted on prose`, discharged under
`### Rename-rot population`: every number above was measured with the shortest distinctive token, as
an occurrence count, at the moment it was written.

### Hot-path budget

`Not applicable; plan declares no hot path.` The build plan's `## Declarations` sets the hot-path
declaration to `none` for the whole cycle, and a docstring carries no runtime cost in any case.

### Floor verification

`Not applicable; plan declares floor-verification scope none for this slice.` The plan assigns the
cycle's single floor run to Slice 1b, which ran it (Django 5.2.16 / Python 3.10 /
strawberry-graphql 0.316.0, 36 passed). A docstring carries no runtime behaviour to verify at the
floor, so re-running it here would measure nothing this slice changed.

### Implementation notes

- **One token, not a reflow.** The replacement is 43 characters against the old 42, so the docstring
  line grows by one character and stays well inside the 100-character limit. Rewrapping the paragraph
  would have made the diff unreadable for no gain, and `ruff format` does not touch docstring prose.
- **The citation form was left as-is** (see `### Implementation discretion items`). `AGENTS.md` rule 27
  prefers `path::QualifiedName`; this paragraph and its neighbours in the same docstring use the
  module-dotted spelling for cross-module constants, and the defect under repair is the name.
- **Singular vs. plural reads correctly after the swap.** "pins the superseded upstream body source"
  refers to `_strawberry_patches`' own single pinned body; the parenthetical credits the precedent,
  which is now a set. No grammatical fix was needed and none was made.

### Notes for Worker 3

- The whole diff is one line inside a module docstring. `scripts/review_inspect.py` was **not** run and
  the skip is recorded here per `docs/builder/BUILD.md` `### When to run the helper during build`: the
  pass adds zero lines of logic to any file, so the helper's AST overview would be identical
  before and after. Re-running it would produce a shadow file that differs from HEAD's in no section.
- The two sweep instruments are described by method in `### Rename-rot population` rather than left
  as scripts on disk; both are short enough to re-derive, and neither belongs in the tree. Scratch
  path used: `/tmp/dsf-024-s3/` (outside the repo, per `docs/builder/BUILD.md`). No file was written
  under `docs/builder/temp-tests/024-slice3/`.
- Worth an independent re-derivation: the claim that the retired-name **population** is 9, not the
  4 the dispatch sampled. The command sequence is given in full above.

### Notes for Worker 1 (spec reconciliation)

**What the rewritten spec and its rationale companion must say about this repair.**

1. **Where it lives** — the spec's account of `_strawberry_patches`' `parse_query_params` shield, and
   the rationale companion's entry for the body-pin decision.
   **Current wording:** the spec is still the 1.5KB stub, so there is no passage to quote; Slice 2
   authors this section from scratch.
   **Recommended replacement:** the spec states the contract as
   "`_strawberry_patches::_validate_upstream_shape` pins the single upstream `parse_query_params`
   body it supersedes, following the reimplementer's-contract precedent
   `_django_patches::_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` establishes: a module that
   reimplements an upstream body validates that body, because no upstream change flows through a
   reimplementation the way it flows through a delegation." The spec must name the **plural, audited**
   constant — the single-body form it superseded is a retired claim and belongs only in the rationale
   file's change record.

2. **Where it lives** — the rationale companion's "changes this decision has undergone" entry for the
   body pin.
   **Current wording:** none authored yet.
   **Recommended replacement:** record that the pin shipped at `0d655bde` as a single pinned body
   `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE`, was widened at `eb2a1764` into the two-member
   audited set `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES` when the Django 6.1 connection-feature
   shape had to be supported alongside the 5.2.16-6.0.x class-attribute shape, and that the sibling
   module's cross-reference to it was not swept at that commit — repaired in this cycle's Slice 3.
   The claim "the patch pins **the** superseded upstream body" is a **retired claim**: it pins a
   *set*, and widening the set is an audit, not a version bump.

3. **A standing rule this defect is evidence for, worth one line in the rationale file:** `eb2a1764`
   satisfied every gate this process has — tests green, ruff clean, review passed — and still left a
   dangling cross-module citation, because **no gate in the build resolves a citation.** The two
   instruments in `### Rename-rot population` are cheap and mechanical; a later cycle that wants the
   `AGENTS.md` rule 27 sweep enforced rather than remembered has the method written down here.

**Out-of-scope surfaces where the same class of rot survives — for the deferred-work catalog.**

Each is a citation in a `.py` docstring or comment naming a symbol that does not exist at HEAD. None
is on card 024's surface, so none was touched. Counts are occurrences, measured while writing this.

- `django_strawberry_framework/utils/relations.py #"mutations/inputs.py::_select_editable_fields"` —
  1 occurrence. `_select_editable_fields` has **never** been defined anywhere in the history
  (`git log -S'def _select_editable_fields'` returns no commit). A never-true citation, introduced at
  `662b408e`.
- `django_strawberry_framework/utils/relations.py #"mutations/resolvers.py::_index_relation_fields"` —
  1 occurrence. Same shape: never defined, introduced at `662b408e`.
- `django_strawberry_framework/utils/querysets.py #"mutations/resolvers.py::_raw_pk_relation_error"` —
  1 occurrence in the package (3 repo-wide; the other 2 are bare-name mentions in
  `examples/fakeshop/test_query/test_library_api.py` docstrings). Defined once, removed at `e9c13f55`
  ("Share batched relation-id decode, IntegrityError envelope, and serializer entries") without the
  sweep.
- `django_strawberry_framework/utils/querysets.py #"mutations/resolvers.py::_relation_membership_error"`
  — 2 occurrences. Same commit, same omission.
- `django_strawberry_framework/utils/querysets.py #"forms/resolvers.py::_visible_related_object"` —
  1 occurrence. The symbol **exists**, but in a different module:
  `django_strawberry_framework/types/resolvers.py::_visible_related_object`. A wrong-module citation,
  which resolves for a human reader and not for a tool.
- `django_strawberry_framework/consumers.py #"auth/mutations.py::logout"` — 1 occurrence. The symbol is
  `logout_mutation`; `auth/mutations.py` defines no bare `logout`. (Two sibling citations at the same
  file, `auth/mutations.py::_channels_http_login_establish` and
  `auth/mutations.py::_authenticated_actor_or_none`, both resolve.)
- `tests/test_list_field.py #"tests/optimizer/test_extension.py::test_optimizer_elides_forward_fk_id_only_selection"`
  — 2 occurrences. The test was renamed to
  `test_optimizer_elides_forward_fk_id_only_selection_plan_shape` (and gained a per-alias sibling);
  neither citation was swept.

**Standing-doc surfaces:** none owed for card 024's retired names. The
`django_strawberry_framework/test/` path in `KANBAN.md` / `KANBAN.html` is the board's deliberate
`(historical)` spelling and is correct as it stands; `docs/GLOSSARY.md`, `docs/TREE.md`,
`docs/README.md`, `CHANGELOG.md` and `BACKLOG.md` carry **0** occurrences of any of the 9 retired
names. The only non-`.py` hits are 2 in `docs/dry/dry-0_0_11.md`, a closed DRY cycle's scratchpad,
exempt from the symbol convention by `START.md`.

**One defect found in the writable file that is deliberately NOT repaired here.** The
`_strawberry_patches.py` module docstring's `Three lifecycles, and one that left` section opens with a
duplicated, truncated sentence fragment — the clause "independent upstream *bugs* that do not retire
together:" appears once as a dangling opener and again inside the complete sentence that follows
(`django_strawberry_framework/_strawberry_patches.py #"Three lifecycles, and one that left"`). It is a
copy-paste artifact, not rename rot, so repairing it would broaden this slice past its contract
(`worker-2.md` `## Scope`, "make unrelated cleanup"). Worker 1 should route it — it is a one-line
deletion of the dangling fragment and belongs to whichever pass next owns that docstring.

---

## Review (Worker 3)

Scope of this pass: the one-line working-tree diff in
`django_strawberry_framework/_strawberry_patches.py`, the build report's population claim, and the
deferred out-of-scope catalog. `bld-slice-1a-024-*.md` and `bld-slice-1b-024-*.md` were **not read** —
a concurrent Worker 3 pass owns both. Where a count below involves those two files it was obtained by
`grep -o … | wc -l` (token counting only, no content read).

Read-only HEAD reference used throughout, per `docs/builder/BUILD.md`
`## Claims are proven mechanically, never accepted on prose`, into a scratch path **outside** the repo:

```shell
S=/private/tmp/claude-501/.../scratchpad/s3rev
git show HEAD:django_strawberry_framework/_strawberry_patches.py > $S/head_strawberry_patches.py
diff $S/head_strawberry_patches.py django_strawberry_framework/_strawberry_patches.py
# 180c180
# < ``_django_patches._UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE``) so an
# ---
# > ``_django_patches._AUDITED_REMOVE_DATABASES_FAILURES_SOURCES``) so an
```

No `git stash` / `git checkout` / `git restore` / `git worktree` was used at any point.

### High:

None.

### Medium:

None.

### Low:

#### Deferred catalog entry for the renamed optimizer test undercounts its population

`### Notes for Worker 1 (spec reconciliation)`, out-of-scope bullet 7, states
`tests/test_list_field.py #"…::test_optimizer_elides_forward_fk_id_only_selection"` — **2 occurrences**.
Measured repo-wide there are **3, in 2 files**:

```shell
grep -rno 'tests/optimizer/test_extension.py::test_optimizer_elides_forward_fk_id_only_selection' \
    --include='*.py' django_strawberry_framework tests examples
# tests/test_list_field.py:1316
# tests/test_list_field.py:1328
# examples/fakeshop/test_query/test_scalars_api.py:839
```

The instrument is not wrong — instrument 2's declared corpus is `django_strawberry_framework/` and
`tests/`, so `examples/` was outside it by construction. The defect is that this bullet reports its
narrower number without saying so while **sibling bullets in the same list disclose repo-wide counts**
(`_raw_pk_relation_error` — "1 occurrence in the package (3 repo-wide …)"). A reader of the
deferred-work catalog takes the list as one population and would repair 2 sites of 3. The symbol itself
is confirmed retired: `tests/optimizer/test_extension.py` defines only
`…_plan_shape` and `…_for_each_alias_plan_shape`, neither of which the citations name.

**Disposition — recorded, slice not held.** The corrected measurement is now on disk in this artifact,
which is the same place Worker 1 reads the note from, so bouncing the diff to Worker 2 would buy
nothing the next reader does not already have. Worker 1 carries **3 occurrences in 2 files
(`tests/test_list_field.py` x2, `examples/fakeshop/test_query/test_scalars_api.py` x1)** into
`bld-final-024.md`'s `### Deferred work catalog`.

#### The post-fix per-file breakdown is already stale and is not stable

`### Post-fix measurement` attributes the 6 surviving scratchpad occurrences as
`bld-slice-1a (3)`, `bld-slice-1b (2)`, `build-024 (1)`. Re-measured during this review:
1a = **4**, 1b = 2, build-024 = 1, and this artifact itself now carries 9.

This is almost certainly **not** a builder mis-count: a concurrent Worker 3 pass owns 1a and was
appending to it while this review ran, so the file is a moving target and the delta is unattributable
either way. Recorded so no later pass treats the breakdown as a measurement of anything durable.
**Non-load-bearing**: the two counts that carry the claim both re-derive exactly (below).

#### The "126 names ever defined" intermediate figure is instrument-dependent

An independent AST walk over the same surface-file list returned **61 revisions** (matches) but
**133** distinct names ever defined and **10** retired, against the report's 126 / 9. The single extra
is `TransactionTestCase`, a historical assignment target that is a live Django import at HEAD — a
name-collection-rule artifact, not package rot, and correctly absent from the builder's table. The
**load-bearing** set is identical: all 9 names the report lists are in my retired set, and no
package-relevant name appears in mine that is missing from the report's. The 61 and the 9 re-derive;
the 126 does not without the exact `Assign`-target rule, which the report does not state.

### DRY findings

None owed by the diff: the pass adds, moves, and shares no logic — one token in a module docstring.

One observation, endorsing rather than duplicating the builder's own
`### Notes for Worker 1` item 3: **no gate in this process resolves a citation**, and the citation
resolver was hand-rebuilt for this cycle and left as prose rather than committed. `scripts/` already
carries the precedent for mechanizing a `BUILD.md` loop (`scripts/prove_failability.py`). Whether a
`scripts/`-resident citation resolver should exist is a **contract-level** call and therefore the
maintainer's (`worker-3.md` `### The existence challenge`); it is routed below, not decided here, and
the slice is not held on it.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` — **empty**. `__all__` and the re-export list are
unchanged. No public export added, removed, or renamed; the diff does not reach a public surface at all.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. (Confirmed against `git status --short`: the only
dirty `.py` file is the target, and `CHANGELOG.md`'s dirtiness is on the plan's baseline-dirty list and
predates this pass.)

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The one adjacent claim that
*would* have touched them was checked anyway, because a false "nothing owed here" is the expensive
direction:

```shell
git grep -ohE 'django_strawberry_framework/test/|django_strawberry_framework\.test\b|tests/test/' -- . | wc -l   # 9
grep -rhoE --include='*.py' '…same pattern…' django_strawberry_framework tests examples scripts | wc -l          # 0
git grep -lE '…same pattern…' -- .   # KANBAN.html, KANBAN.md, examples/fakeshop/db.sqlite3
grep -n 'django_strawberry_framework/test/' KANBAN.md
# 3920:- `django_strawberry_framework/test/__init__.py` (historical)
# 3921:- `django_strawberry_framework/test/_wrap.py` (historical)
```

Confirmed: the board's `(historical)` spelling (`TrackedPath.is_current=False`), correct as it stands,
nothing owed. The builder's "no standing-doc surface owes anything for card 024's retired names" holds.

### Failability proofs — audit and independent re-run set

**Re-run set: empty, and legal.** `docs/builder/BUILD.md` `### What needs a proof, and what does not`
exempts "renamed symbols, relocated bodies, added annotations, **doc edits**"; the diff is one docstring
token and introduces no boundary, guard, gate, or rejection path, so no proof meets
`worker-3.md`'s mandatory floor and there is nothing to re-run. The build report's
`None; this pass introduced no new boundary.` is correct and is **accepted as recorded**. Demanding a
proof here would be a defect in the review, not in the build.

The source carve-out was **not** exercised: no production file was mutated by this pass. The working
tree carries exactly one dirty `.py` file (`M django_strawberry_framework/_strawberry_patches.py`,
the builder's), and no `ACTIVE-MUTATION.json` marker exists.

What replaces the proof, per the same section, is the mechanical re-derivation below.

### Claim verification (re-derived vs. accepted)

**Re-derived independently — these are measurements I made, not the report's:**

1. **The replacement symbol exists and resolves.**
   `grep -o '_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES' django_strawberry_framework/_django_patches.py | wc -l`
   -> **5**, matching the report exactly; the definition is
   `django_strawberry_framework/_django_patches.py #"_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES: tuple[str, ...] = ("`.

2. **The chosen candidate is the right one — argument checked against source, not accepted.**
   `_django_patches::_validate_upstream_shape #"if source not in _AUDITED_REMOVE_DATABASES_FAILURES_SOURCES:"`
   is the membership test, so the audited tuple is literally the constant that function pins; the two
   per-shape members are only its elements (naming either would narrow the cited contract to one Django
   shape), and `_validated_remove_databases_failures_source` is module-level runtime state assigned in
   `_django_patches::apply #"_validated_remove_databases_failures_source = source"` — a *result*, and
   naming it would make the sentence false, since a runtime variable establishes no contract. The
   reimplementer's-contract prose sits in the tuple's own leading comment
   (`_django_patches.py #"WIDENING THIS SET IS AN AUDIT, NOT A VERSION BUMP"` and the paragraph above
   it) and is echoed in `_django_patches::_validate_upstream_shape`'s docstring. **No candidate makes
   the sentence truer.** The one arguable alternative — citing the *function* rather than the constant —
   was rejected on inspection: the original citation occupied a constant-shaped grammatical slot, so
   constant-to-constant is the faithful minimal repair, and
   `_strawberry_patches::_validate_upstream_shape`'s own docstring already credits the module by name
   ("the ``_django_patches`` precedent").

3. **The citing sentence survives the substitution — whole paragraph read, not just the changed line.**
   The subject of "pins the superseded upstream body source" is `_strawberry_patches`' own
   `_validate_upstream_shape`, which pins exactly one body:
   `_strawberry_patches.py #"if source != _UPSTREAM_PARSE_QUERY_PARAMS_SOURCE:"` — a scalar `!=`, not a
   membership test. The new referent appears only inside the parenthetical crediting the precedent, so
   the sentence's singular claim is unaffected by the precedent now being a two-member set, and
   "fails loudly at ``apply()`` time" remains true of the subject
   (`_strawberry_patches::apply` calls `_validate_upstream_shape`, which `raise RuntimeError`s). The
   surrounding paragraph's other cross-module citations (`views.py::_RequestBodyBoundaryMixin.parse_json`,
   `views.py::_RawBodyRequestAdapter`, `_cross_web_patches`) all still resolve. **This is the specific
   place a citation repair goes subtly false and it does not.**

4. **The population claim.** Independent AST walk (`git log --format=%H --all --` per surface path,
   `ast.parse` each revision, union `FunctionDef`/`AsyncFunctionDef`/`ClassDef`/`Assign`/`AnnAssign`
   targets, subtract every name defined anywhere in the HEAD `.py` corpus): **61 revisions** (matches),
   10 retired names = the report's 9 plus `TransactionTestCase` (see Low 3). Every one of the report's
   9 is confirmed **genuinely retired** — present in some historical revision, absent from every HEAD
   definition. Per-name citation counts re-measured, substring **and** whole-token:

   | Retired name | substring `.py` | `\b`-token `.py` | agrees with report |
   |---|---|---|---|
   | `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` | 0 | 0 | yes (was 1, now fixed) |
   | `_PATCH_APPLIED` | 0 | 0 | yes |
   | `_missing_symbol_logged` | 0 | 0 | yes |
   | `_unpatched` | **6** | **0** | yes |
   | `sentinel_wrapper` | 0 | 0 | yes |
   | `skip_records` | 0 | 0 | yes |
   | `test_apply_logs_missing_symbol_notice_only_once` | 0 | 0 | yes |
   | `test_apply_no_ops_when_database_failure_symbol_missing` | 0 | 0 | yes |
   | `test_patch_is_installed_on_transaction_test_case` | 0 | 0 | yes |

5. **The headline "exactly one retired name had a live citation" — confirmed** by the table above:
   `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` is the only row with a non-zero whole-token count before
   the repair, and it is now 0 in `.py` and 0 in every git-tracked non-scratchpad file
   (`git grep -oh '…' -- . ':!docs/builder' | wc -l` -> **0**).

6. **The `_unpatched` measurement trap — confirmed exactly as reported.** 6 substring hits, 0
   whole-token, every hit inside a live longer name:
   `tests/test_django_patches.py::test_unpatched_remove_databases_failures_crashes_on_non_wrapper` (2),
   `examples/fakeshop/test_query/test_transport_api.py #"upstream_unpatched"` (2) and
   `#"package_unpatched"` (2). A substring grep is not a citation count, and the report says so.

7. **The un-swept rename is card 024's own**, verified at the commit rather than taken on the plan's
   word: `eb2a1764` (2026-08-06, "feat(patches): supersede both audited upstream teardown bodies")
   touches only `_django_patches.py` and `tests/test_django_patches.py`; the old name goes 3 -> 0 in
   `_django_patches.py` across it, while `_strawberry_patches.py` still carried its 1 citation at that
   same commit and was not in the diff. `AGENTS.md` rule 27's same-change sweep obligation was violated
   there, so the repair is 024's to make.

8. **My own resolver is failable**, which is the only reason its clean result means anything. Run against
   the pristine HEAD copy it flags
   `UNRESOLVED dotted: _django_patches._UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE`; run against the
   working tree it reports nothing across the whole card-024 surface
   (`_django_patches.py`, `_strawberry_patches.py`, `testing/_wrap.py`, `testing/__init__.py`, `apps.py`,
   and the four test modules). Instrument 2's "exactly one unresolved citation on the 024 surface, now
   zero" reproduces.

9. **Validation run re-run, not accepted.**
   `uv run pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py tests/test_strawberry_patches.py --no-cov`
   -> **91 passed in 1.69s**, 0 failures, 0 collection errors — identical to the record.
   `uv run ruff format --check django_strawberry_framework/_strawberry_patches.py` -> `1 file already
   formatted`; `uv run ruff check <same>` -> `All checks passed!` (both read-only, never `--fix`; the
   `COM812` line is the standing pre-existing configuration warning). No coverage-shaped flag other than
   the mandatory `--no-cov` was used anywhere in this pass.

**Accepted on the builder's record, not re-derived:** the exact `126` intermediate (see Low 3); the
Slice 1b floor run's 36-passed figure (another cohort's artifact, deliberately unread); the internal
per-file attribution of the 6 surviving scratchpad occurrences (see Low 2 — measured, but against a
file a concurrent pass is actively writing).

### Out-of-scope deferrals — sampled, and the deferral graded

**Sampled 7 of 7 (all of them), and all 7 are real.** The two most expensive to be wrong about are the
"never defined anywhere in history" pair, so those were checked against all history, not just HEAD:

```shell
git log --all --oneline -S'def _select_editable_fields' -- '*.py' | wc -l   # 0
git log --all --oneline -S'def _index_relation_fields'  -- '*.py' | wc -l   # 0
```

Zero commits ever introduced either `def`; the only `-S` hits on the bare token are the commits that
introduced the *citations*. Both citations are live at HEAD
(`django_strawberry_framework/utils/relations.py:537` and `:538`), so both are never-true citations
exactly as described. The remaining five likewise confirmed: `_raw_pk_relation_error` and
`_relation_membership_error` were defined and removed at `e9c13f55` (citations survive at
`utils/querysets.py:3052`, `:3106`, `:3129`); `_visible_related_object` exists but at
`django_strawberry_framework/types/resolvers.py:378`, not the cited `forms/resolvers.py`
(`utils/querysets.py:3148`); `auth/mutations.py` defines `logout_mutation` at :876 and no bare `logout`
(`consumers.py:200`); and the optimizer-test citation is stale as described (with the count correction
in Low 1). **No deferred item is fictional** — none would send the next author chasing something that
does not exist.

**The deferral is correct, not a dodge.** Three independent reasons, and the third is the one that
matters:

- Every one of the 7 is another card's rename. `AGENTS.md` rule 27 binds the sweep to *the change that
  renames the symbol*, so the owner of each repair is the card whose rename or deletion caused it —
  `662b408e`, `e9c13f55`, and the optimizer-test rename — not 024.
- The slice's own contract (`build-024…md` `## Checklist`, Slice 3) is scoped to "every symbol/path
  **024** renamed or deleted". Repairing the other 7 would tick no box in the dispatched findings
  checklist.
- The cycle's maintainer-set scope being "spec files and `.py` files only" is what makes this a genuine
  *deferral* rather than a dropped item: these are all `.py` files, so they are **eligible** work that a
  future cycle can pick up from the catalog — unlike the `CHANGELOG.md` / `docs/GLOSSARY.md` /
  `docs/TREE.md` items the plan already routed there, which the scope excludes outright. Fixing them
  here would also break the isolation the process exists for: seven unrelated repairs would land under a
  card that did not cause them and be reviewed as though 024's rename had.

### What looks solid

- **The repair is minimal and provably total.** One token, one line, byte-diffed against pristine HEAD;
  no reflow, no form change, no adjacent "while I'm here" edit. The candidate table is the strongest
  part of the build report — it names why each of the four post-`eb2a1764` candidates loses, and the
  reasoning survives independent checking against source.
- **The report distinguishes occurrences from matching lines everywhere it counts**, and the
  `_unpatched` entry goes further by naming the trap explicitly (6 substring, 0 whole-token, every hit
  inside a live longer name) rather than silently reporting the smaller number. That is the exact
  failure mode `BUILD.md` `## Claims are proven mechanically` warns about, caught and documented by the
  builder before review.
- **Two instruments, one of them candidate-list-free.** The population claim is not a sample dressed as
  a measurement: instrument 2 takes no input from the dispatch or from instrument 1, and the two agree.
  Both reproduce.
- **The in-file defect the builder declined to fix is real and correctly declined.**
  `django_strawberry_framework/_strawberry_patches.py #"Three lifecycles, and one that left"` does carry
  a dangling duplicated fragment — the clause `independent upstream *bugs* that do not retire together:`
  stands alone immediately before the complete sentence containing it. Verified present at HEAD (it is
  not in the diff), so it is pre-existing, it is a copy-paste artifact rather than rename rot, and
  repairing it would have broadened the slice past its contract. Recording it and routing it is the
  right call.
- **`scripts/review_inspect.py` skip is correct and correctly recorded** on both sides: the pass adds
  zero lines of logic, touches no file under `optimizer/` or `types/`, and adds no new `.py` file, so
  none of `BUILD.md` `### When to run the helper during build`'s Worker 3 triggers fires. Skipped here
  for the same reason, recorded per `worker-3.md` `## Static helper use`.

### Temp test verification

- No temp test was written under `docs/builder/temp-tests/024-slice3-review/`, and none is owed: the
  diff changes no executable line, so there is no behaviour a temp test could distinguish.
- The two re-derivation instruments (historical-AST retired-name extraction; citation resolver) ran from
  a scratch path **outside the repository** and wrote nothing into the tree. Disposition: discarded with
  the pass; the method is recorded above and in the build report so a later cycle can rebuild them.

### Notes for Worker 1 (spec reconciliation)

1. **Carry the corrected count into `bld-final-024.md`'s `### Deferred work catalog`.** The stale
   optimizer-test citation is **3 occurrences in 2 files**, not 2 in 1 —
   `tests/test_list_field.py:1316`, `:1328`, and
   `examples/fakeshop/test_query/test_scalars_api.py:839`. The other six out-of-scope bullets'
   counts were re-measured and are correct as written.

2. **The builder's three spec/rationale recommendations are endorsed unchanged.** The rewritten spec
   must name the plural audited constant; "the patch pins **the** superseded upstream body" is a retired
   claim belonging only in the rationale file's change record; and the `0d655bde` -> `eb2a1764`
   widening is an audit, not a version bump — that phrasing is verbatim in the constant's own leading
   comment and should survive into the rationale entry.

3. **`Escalated:` — should a citation resolver exist in `scripts/`?** Contract-level, therefore the
   maintainer's call (`worker-3.md` `### The existence challenge`), raised because this cycle produced
   evidence rather than on a schedule: `eb2a1764` passed tests, ruff, and review and still shipped a
   dangling cross-module citation, because **no gate in this process resolves one**. `AGENTS.md` rule 27
   is currently enforced by memory. Resolution paths, for the maintainer to pick between:
   (a) commit the resolver as `scripts/check_citations.py` and add it to the pre-commit hooks, making
   the rule mechanical the way `check_trailing_commas.py` and `check_spec_glossary.py` already are —
   note `scripts/` sits outside the coverage gate, so this adds no coverage obligation;
   (b) commit it as a worker-invoked helper only, no hook, cheaper but still opt-in;
   (c) leave it as prose in the artifacts and accept per-cycle re-derivation. The 7 out-of-scope
   findings above are the standing cost of (c) — three separate cards' renames, none swept.

4. **Not a spec matter, but it needs an owner:** the duplicated docstring fragment at
   `django_strawberry_framework/_strawberry_patches.py #"Three lifecycles, and one that left"` (a
   one-line deletion). It is in this cycle's writable `.py` scope but outside this slice's contract, so
   it needs routing to whichever pass next owns that docstring rather than being lost between the two.

### Review outcome

`review-accepted`.

Every box in `### Dispatched findings checklist` was walked and each is landed in the diff or in the
report: the citation is repaired and resolves; the population was derived from history and re-derives
independently; counts are occurrence counts (two corrections in the notes section, both Low, neither
touching the diff); formatters ran clean with the churn correctly classified as another cycle's; and
the focused scope reproduces at 91 passed. No High and no Medium finding. The three Low findings are
recorded with their dispositions above — the one that is actionable is a number Worker 1 needs, and
that number is now on disk in this artifact, which is where Worker 1 reads it from, so holding the diff
at `revision-needed` over it would buy the next reader nothing. No boundary in the diff meets the
mandatory re-run floor, so the empty re-run set is legal; the source carve-out was not exercised and the
tree carries no mutation.

---

## Final verification (Worker 1)

Slice contract, from the build plan's `## Checklist`: repair the one in-scope `.py` defect card 024's own
rename caused, plus the full population sweep for every symbol or path 024 renamed or deleted. Delivered.

**`### Dispatched findings checklist` audited box by box against evidence, not against the report.**

1. *Repair the citation.* **Landed.** `git diff HEAD -- django_strawberry_framework/_strawberry_patches.py`
   is one changed line, `_UPSTREAM_REMOVE_DATABASES_FAILURES_SOURCE` -> `_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES`,
   with the surrounding sentence untouched. The replacement resolves at
   `django_strawberry_framework/_django_patches.py #"_AUDITED_REMOVE_DATABASES_FAILURES_SOURCES: tuple[str, ...] = ("`,
   and the crediting sentence stays true because `_strawberry_patches` still pins exactly one superseded
   body of its own. Tick upheld.
2. *Sweep the whole retired-name population.* **Landed.** All nine retired names re-measured at close,
   whole-token, occurrences not matching lines, over `django_strawberry_framework/`, `tests/`, `examples/`,
   and `scripts/`: every one returns **0**. `_unpatched` returns 0 whole-token against 6 substring hits, so
   the trap the report names reproduces. Tick upheld.
3. *State every count as a measured occurrence count.* **Landed**, with the reviewer's two corrections
   recorded on disk rather than argued away. Tick upheld.
4. *Run the formatters and classify the churn.* **Landed**; the one dirty `.py` in the tree is this slice's
   own, and nothing was reverted. Tick upheld.
5. *Run the focused scope and record pass/fail.* **Landed and re-run by this pass:**
   `uv run pytest tests/test_django_patches.py tests/testing/test_wrap.py tests/test_apps.py
   tests/test_strawberry_patches.py --no-cov -q` -> **91 passed**, 0 failures, 0 collection errors. No
   `--cov*` flag. Tick upheld.

**Findings routed rather than dropped.**

- The reviewer's Low 1 count correction is carried into the Slice 2 artifact's deferred-work catalog as
  **3 occurrences in 2 files**, re-derived at close rather than copied — and the re-derivation found one more
  thing worth carrying: a substring sweep on that citation returns **4** hits, because the fourth cites the
  live `…_for_each_alias_plan_shape` name and is not rot. Anchoring the sweep at the identifier's end is
  what separates them.
- The escalation "no gate in this process resolves a symbol citation" is a maintainer decision and is
  recorded in the Slice 2 artifact's catalog with its three resolution paths intact. Not decided here; not
  decidable by any worker.
- The duplicated docstring fragment at
  `django_strawberry_framework/_strawberry_patches.py #"Three lifecycles, and one that left"` is confirmed
  present at HEAD and is routed to the same catalog. Declining it was correct: it is a copy-paste artifact
  rather than rename rot, and repairing it here would have broadened the slice past its contract.
- The builder's three spec/rationale recommendations were all honoured. The rewritten spec names the plural
  audited constant; "the patch pins **the** superseded upstream body" appears only in the rationale's
  retired-claims list; and the `WIDENING THIS SET IS AN AUDIT, NOT A VERSION BUMP` phrasing survives verbatim
  in both the spec's Decision 5 and the rationale's change record for it.

Status: final-accepted.
