# Build plan: spec-047 reconciliation — execution resource policy (047)

Spec source: [`docs/SPECS/spec-047-resource_policy-0_0_14.md`][spec-047]
Rationale companion: [`docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`][spec-047-rationale]
Target release: `0.0.14` (shipped; card `DONE-047-0.0.14`)
Date created: 2026-09-13
Cycle kind: **reconciliation round** over already-shipped work, dispatched under
[`docs/builder/BUILD.md`][build] `## Review rounds`. The maintainer's instruction is the
round's input: reconcile the spec with what actually landed, confirm nothing the spec
planned was skipped in the code, and record every post-release change — corrections and
later-feature refactors alike — in the **rationale** companion, never in the spec.

Build rule: one cohort at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every pass must justify shared/duplicated patterns before merging.

## Scope fence (maintainer-set)

- **Spec files and `.py` source only.** No `KANBAN.md` / `docs/GLOSSARY.md` / `docs/TREE.md`
  fold-in, no DB edits, no regenerates, no closeout agentflow edits to
  [`BUILD.md`][build] or the `worker-*.md` role files.
- **Every file this cycle creates carries `047` in its name.**
- The spec is **already archived** at `docs/SPECS/` with its companions under
  `docs/SPECS/appx/`. The archival step the maintainer's brief names is therefore already
  discharged; this cycle edits the spec in place and does not move it. Recorded here so a
  later reader does not re-derive the move.

## Pre-flight

`Pre-flight: passed on 2026-09-13 with two recorded round deviations; baseline: dirty with a
concurrent session's spec-050 work; cleanup: deliberately not performed.`

| Step | Outcome |
|---|---|
| 1. Working-tree baseline explicit | Dirty. See baseline-dirty list below. Maintainer instruction: *"Ignore others concurrent work."* |
| 2. `scripts/review_inspect.py` smoke | Passed — `uv run python scripts/review_inspect.py django_strawberry_framework/resource_policy.py --output-dir docs/shadow --stdout` emitted a full overview. |
| 3. Build-artifact reset | **Deliberately skipped — round rule.** [`BUILD.md`][build] `### Cohorting, naming, and closure` ("Pre-flight for a round") exempts a round from the reset. Independently required here: `docs/builder/build-050-list_field_arguments-0_0_15.md` and its `bld-*.md` artifacts belong to a **live concurrent cycle that still owes its final gate**. Verified that no path this cycle creates already exists. |
| 4. `.gitignore` lists the scratch paths | Passed — `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/` all listed. |
| 5. Scratch directories cleared | **Deliberately skipped.** Clearing `docs/builder/worker-memory/` and `docs/builder/temp-tests/` would destroy the live spec-050 cycle's scratch. This cycle's memory files are namespaced `047-worker-<N>.md` instead, so they cannot collide. |
| 6. Spec-doc consistency check | Passed — `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-047-resource_policy-0_0_14.md` → `OK: 34 terms`. |
| 7. Spec rationale extracted | **Already present** at `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` (19,262 bytes), written by a prior closeout pass. This round EXTENDS it rather than creating it; see the cohort scope. |

### Baseline moved mid-round: `91c2d880` → `d727a256`

**Recorded rather than rewritten, because the list below is what the authoring pass was
dispatched against.** The concurrent spec-050 session **committed** its work as `d727a256`
part-way through Worker 1's pass, so all eight files below are now clean at `HEAD` and
`git status --short` shows only this cycle's own files. Two consequences, both handled:

- The authoring pass re-extracted `HEAD`, re-proved byte identity, and re-derived every
  published figure against `d727a256`. Worker 0 independently re-measured the two test
  counts at the new `HEAD`: **117 functions / 185 node ids** package, **56 / 56** live —
  matching what the spec now publishes.
- **A count over a population another cycle is actively extending is a moving target.** The
  package tier read 113 functions at dispatch and 117 at return, from four rows the
  concurrent commit added. The spec therefore publishes both counts as **floors** with the
  unit named, which is the only durable form; a later reader measuring a larger number
  learns the file grew rather than that the plan is wrong.

The list is kept verbatim below as the dispatch-time baseline.

Workers neither edit nor revert these. They were a concurrent session's uncommitted spec-050
work at dispatch time (`AGENTS.md` rule 34).

- `django_strawberry_framework/list_field.py`
- `django_strawberry_framework/resource_policy.py`
- `docs/feedback.md`
- `examples/fakeshop/test_query/test_list_field_api.py`
- `examples/fakeshop/test_query/test_list_field_async_api.py`
- `tests/test_connection.py`
- `tests/test_list_field.py`
- `tests/test_resource_policy.py`

**Consequence for this round: grade spec-047 against `HEAD`, never the working tree.** Two of
those dirty files are spec-047's own. A pristine `HEAD` tree is extracted read-only at
`<scratchpad>/head` (`git archive HEAD | tar -x -C <scratchpad>/head`) and is the reading
surface for every claim about those files. No `git stash` / `checkout` / `restore` /
`worktree` is used anywhere in this cycle.

### Concurrent-writable tracked binary / generated files

`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`,
`docs/TREE.md`. This round's scope fence puts all of them out of scope, so **any churn in
them is somebody else's** and is never this cycle's output.

## Build-wide context flags

- **Version-bump owner:** none. This card shipped at `0.0.14`; `__version__` at `HEAD` reads
  `0.0.15` (spec-050's line). This round takes no bump and edits no version literal.
- **Joint-cut path:** not applicable; the `0.0.14` cut is closed.
- **Coverage:** never run by a worker. `--no-cov` only.

## Declarations

- **Ownership partition:** single cohort, `047-reconcile`. It owns exactly:
  `docs/SPECS/spec-047-resource_policy-0_0_14.md`,
  `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`, and
  `docs/builder/bld-047-reconcile.md`. No other cohort exists, so no file is contended.
  A second cohort is created only if the verification pass promotes a code defect
  (`### Contingency: a code cohort`).
- **Hot-path declaration:** none. The cohort as planned edits no executable code.
- **Floor-verification scope:** none. No Django / Strawberry / channels integration seam is
  touched by a documentation-only cohort.

## Artifact list

- `docs/builder/bld-047-reconcile.md` — the spec + rationale reconciliation cohort. Retired
  from the tree after the round committed; its three passes and two reviews are recoverable
  at `git show c134da8c:docs/builder/bld-047-reconcile.md`.
- `docs/builder/bld-047-final.md` — the round's closing gate.
- (contingent) `docs/builder/bld-047-code.md` — only if a code defect is confirmed.

## Worker-0 verification pass (findings carried into dispatch)

[`BUILD.md`][build] `### Worker 0 verifies every finding against source before dispatching`:
each finding below was read against source before any worker was dispatched. Findings A-C
were verified by Worker 0 directly; the rest come from the three read-only evidence sweeps
and are re-stated here only after Worker 0 confirmed them against `HEAD`.

- **A. Decision 9 names a mutation deadline seam that no longer exists.** The spec says the
  check sits in `mutations/resolvers.py::run_write_pipeline_sync` *and* "the delete branch of
  `_run_pipeline_sync`". At the release commit `567cc6d0` that file carried two
  `check_deadline(info)` calls, in exactly those two functions. At `HEAD` it carries one, in
  `run_write_pipeline_sync` only. Commit `6013cda6` ("Fold delete and plain-form mutations
  onto the shared write skeleton", after the release) folded delete onto the shared skeleton,
  so the delete branch now **inherits** the seam instead of owning a second one. The
  contract is unchanged; the spec's enumeration of where it lives is stale.
- **B. Decision 9 and Decision 7 name `connection.py::_resolve_connection_fast_path`, which
  was deleted.** Commit `de2601e9` ("single-site the connection dispatch") removed it; at
  `HEAD` the deadline check sits directly in `connection.py::DjangoConnection.resolve_connection`,
  and there is now **one** `resolve_connection` definition rather than the two entry points
  Decision 7 describes resolving the cap "once at the top" each.
- **C. Decision 12's present-tense version claim is false at `HEAD`.** It reads "The version
  quintet already reads `0.0.14`". `HEAD`'s `django_strawberry_framework/__init__.py::__version__`
  reads `0.0.15`. The *conclusion* (this card takes no bump) still holds; the observation
  needs to be stated so it is true at any later date.
- **D. The rationale's `[spec-047-d13]` link definition is a stranded anchor.** It targets
  `#decision-13--three-bounds-this-policy-still-owes-and-three-exclusions-that-are-audited-rather-than-forgotten`;
  the spec's Decision 13 heading is now "What this policy does not bound, and why each
  boundary is deliberate". The rationale's own change record documents the rename and the
  link definition was not re-pointed with it.
- **E. The rationale cites a deleted per-cycle artifact twice.**
  `docs/builder/bld-047-remediation.md` is named at two places in the rationale and does not
  exist at `HEAD`: added at `567cc6d0`, deleted at `99696bac` ("clear the closed cycles'
  build artifacts"). One death commit, and the blob is byte-identical at both commits that
  hold it (`shasum` of `git show 567cc6d0:<path>` equals that of `git show 99696bac^:<path>`),
  so **one** pointer discharges it — `git show 99696bac^:docs/builder/bld-047-remediation.md`.
- **F. The raw-list seam has an async twin the spec does not know about.** Decision 6 and
  the DRY obligations both say `resource_policy.py::bounded_rows` is "the single place" /
  "the only raw-list bound". At the release commit `567cc6d0` that was true: `grep -c
  bounded_rows_async` on that revision's `resource_policy.py` returns `0`. At `HEAD` the
  module exports **`bounded_rows_async`** in its own `__all__`, and both
  `list_field.py` and `types/resolvers.py` await it on their async paths. The module
  docstring at `HEAD` now says the two "enforce the same seam". The contract is still one
  seam; the spec names one of its two colors.
- **G. The module's public surface has grown three names the spec never lists.**
  `resource_policy.py::__all__` at `HEAD` carries 16 entries. Beyond the spec's
  Implementation-plan list it adds `bounded_rows_async` (finding F),
  `validate_trusted_flag`, and `DST_RESOURCE_DEADLINE`. None is a root package export, so
  no `__init__.py` `__all__` pin moves.
- **H. Variable DEFAULTS are charged, and the spec describes a walk that ignores them.**
  Commit `597dbbb4` records that `charge_document` "ignored operation variable definitions,
  so a default supplied in the operation rather than the variables map was never charged and
  a document could exceed its bound through defaults alone." Defaults are now folded into the
  per-operation variable map before argument values are charged. Decision 4 enumerates
  literal arguments, variables, and literals with variables spliced in — never the
  definition's own default. A closed bypass the contract does not state.
- **I. Bytes-like scalars are charged against `max_scalar_bytes`.** The same commit added a
  `bytes` / `bytearray` / `memoryview` branch charging `nbytes` (falling back to `len`).
  The bounds table's `max_scalar_bytes` row still reads "UTF-8 bytes in one scalar value",
  which describes the text-only behavior that let a bytes-like value pass free.
- **J. A nested schema operation now RESTORES the outer policy context.** Commit `ba15c767`:
  "the extension wrote its two context keys per operation but never restored what was already
  there, so a nested schema execution left the outer operation's row cap and deadline
  overwritten on the way out." Both keys are snapshotted and restored around each operation.
  Decision 2 describes only the stash and "the end-of-operation clear".
- **K. The shared precedence ladder moved to `utils/policies.py::resolve_policy`.** Commit
  `9894410f` extracted the ladder both schema-construction policies implement;
  `resource_policy.py::resolve_resource_policy` survives under its spec-named name and
  delegates. The same commit folded the positive-integer rule into `_require_positive_int`
  and the deadline-plus-bound seam into `_raw_list_bound`. The DRY obligations list does not
  name `resolve_policy`, so the spec reads as though this card owns a ladder it now shares.
- **L. `ResourceLimitExceeded` gained a `detail` field and `__reduce__`.** Per `597dbbb4`,
  so bound / limit / charge / detail survive pickling. The spec's rejection envelope shows
  `bound`, `limit`, `charged` only.
- **M. Not a finding — a decoy to pre-empt.** A repo-wide `grep 047` hits
  `TODO-BETA-047-0.1.2` in `examples/fakeshop/apps/products/schema.py` and in
  `docs/SPECS/spec-060-search_fields-0_1_2.md`. That is the **old numbering of a different,
  unshipped search card**; `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md`
  already records that it is `TODO-BETA-056-0.1.2` today, and `spec-060`'s own slice table
  owns the comment-id fix. **Out of scope for this round — do not touch it.**
- **N. Both published test-row counts are large undercounts.** The Test plan says the live
  tier has "35 rows" and the package tier "79 rows". **Worker 0 re-derived both at `HEAD`
  with two independent instruments** rather than accepting either sweep's figure — one sweep
  reported 99 for the package tier and was wrong.
  - Instrument 1, `grep -cE '^(async )?def test'`: **113** package, **56** live.
  - Instrument 2, `ast` parse counting module-level `test*` functions and multiplying every
    `@pytest.mark.parametrize` argvalues cardinality (stacked decorators multiply):
    **113 functions → 180 node ids** package, **56 → 56** live, with
    `unresolved_parametrize = 0` on both, so no cardinality was guessed.
  - The two instruments agree exactly on the function counts; the node-id figure differs
    from it only by the transparently-computed parametrize expansion.
  - Both test files are baseline-dirty, so both were read from the `HEAD` extraction, whose
    `shasum` was first proved equal to `git show HEAD:<path>` for each.
  - **A "row" must be defined where the number is published**, or the next reader re-derives
    a third figure. The spec's own Test plan uses "rows" without saying whether a
    parametrized case counts once or per case.
- **O. Evidence-sweep findings folded in.** The remaining confirmed findings from the three
  read-only sweeps are carried into the cohort artifact's `### Dispatched findings checklist`
  by Worker 1's planning pass, each with the symbol-qualified path Worker 0 recorded. The
  substantive ones, all re-checkable from the sweeps' quoted evidence:
  - **`clear_resource_context` is exported, spec-named, and called by nothing in the
    package.** The extension now brackets each operation with
    `utils/context.py::restored_context_keys`, which restores a pre-existing outer value
    instead of clearing. Only `tests/test_resource_policy.py` still calls it. Decision 2's
    "end-of-operation clear" describes the retired mechanism (pairs with finding J).
  - **The value walker has a third classification signal** above the type rule and the one
    `ids` name rule: the owning mutation's bind-time `_input_field_specs`, read through
    `extensions/resource_policy.py::_mutation_input_specs` / `::_nested_specs_map`, which is
    how a raw-pk relation list typed `[Int!]` is recognized as relation ids at all. Decision
    4's enumeration of the classification inputs is incomplete.
  - **`effective_bound` is not the only narrowing site**: `extensions/resource_policy.py::_page_bound`
    open-codes `min(value, policy.max_page_size)`. DRY obligation 3 as written is false.
  - **`_ValueBudget._reject` is not the only rejection constructor in the walker**: two
    `ResourceLimitExceeded(...)` constructions sit in `_ValueBudget._charge_upload`'s
    unmeasurable-size branches, and two more in `_DocumentBudget.charge_selection` /
    `::charge_collection`. DRY obligation 5 as written is false.
  - **Decision 13's second audited exclusion is falsified.**
    `forms/resolvers.py::_run_plain_form_pipeline_sync` no longer exists; both form flavors
    share `_run_form_pipeline_sync`, which calls `run_write_pipeline_sync` unconditionally,
    so the plain form now *does* get the deadline check. The spec's stated reason for
    excluding it no longer describes the shipped arrangement.
  - **The Test plan misfiles the malformed-document pair.** It places them in the package
    tier; they are live rows, and `tests/test_resource_policy.py`'s own module docstring says
    so in as many words.
  - **Two Test-plan assertion claims overstate.** "each asserting the exact charge" is true of
    only one of the two connection-shape rows; "node ids under, at, and over" is two rows,
    not three.
  - **Three modules the shipped surface depends on are absent from the Implementation plan**:
    `utils/policies.py`, `utils/errors.py::coded_error_extensions`, `utils/inputs.py::RELATION_MULTI`.

### Post-release change register (the rationale's missing chapter)

The rationale companion's change record stops at the pre-release remediation round. **312
commits** separate the release `567cc6d0` from `HEAD`; of the 56 touching a spec-047-owned
path, the table below carries **15 rows naming 19 distinct commits**. These are the ones that changed what the contract
says. Each is a rationale entry this round owes, and several are also a spec correction.

| Commit | What it did to the 047 surface | Class | Bears on |
|---|---|---|---|
| `292c7411` | `derive_connection_window_bounds` now narrows through `resolve_relay_max_results` before building the slice metadata. **At the release the policy ceiling reached the offset window unclamped** — a real hole in the shipped ceiling. Also made `utils/context.py::get_context_value` fall through to the default on a hostile descriptor. | correction | D7, Edge cases |
| `6013cda6` | Folded delete + plain form onto `run_write_pipeline_sync`; deleted the delete branch's own `check_deadline`. | refactor | D9, D13 |
| `18550f5d` | `_with_resource_policy_extension` stopped normalizing `extensions` through truthiness, so a `__bool__`-overriding container cannot be consulted before Strawberry sees the entries; the class-or-instance test became `_extension_entry_matches`. | correction | D11 |
| `de2601e9` | Retired `_resolve_connection_fast_path`; the two `resolve_connection` overrides collapsed to one reading `_resolves_total_count`. Behavior preserved exactly. | refactor | D7, D9 |
| `ba15c767` | (i) Replaced the end-of-operation **clear** with a snapshot-and-restore. (ii) Made the scalar-where-a-list-is-declared coercion **actually** charge a container plus one depth level — the Edge case was aspirational before. (iii) An upload whose `size` **raises on access** is now a rejection, a sixth unmeasurable spelling. | correction | D2, D4, Edge cases |
| `597dbbb4` | (i) **Operation variable defaults are charged** — a `$p: Int = 5000` default was a free payload. (ii) Bytes-like scalars charge against `max_scalar_bytes`. (iii) `_charge_list_family` reached only for a real list. (iv) `ResourceLimitExceeded` gained `detail` + `__reduce__`. | correction | D4, D11, bounds table |
| `2d94b89e` | `_STRUCTURAL_DELIMITER_PAIRS` single-sources the three bracket families; the open/close sets derive from it. Zero behavioral change. | refactor | D3 |
| `dc00f4a6` | Added the public **`bounded_rows_async`**; added a **finiteness** check to `execution_deadline_seconds` (`inf` was previously accepted); restructured `narrowed()` to compare normalized values; dropped "and the delete branch" from the seam docstring. | correction | D6, D9, D10 |
| `a8f31a2d` | The largest post-release change. (i) **A mutation's bind-time `RELATION_MULTI` spec now outranks the `ID`-scalar test**, so a raw-pk `[Int!]` relation list is charged as relation ids where the release charged it as a membership list. (ii) `scan_document_text` declines a non-`str` query. (iii) The context round trip moved to `utils/context.py::restored_context_keys` + a public `MISSING`. (iv) `check_deadline` fails closed on a hostile stashed deadline. (vi) `bounded_rows` catches `KeyError` beside `TypeError`. (vii) Extensions built through `utils/errors.py::coded_error_extensions`. | correction | D2, D3, D4, D9, D11 |
| `9894410f` | Precedence ladder extracted to `utils/policies.py::resolve_policy`; `resolve_resource_policy` **kept its name, signature and contract** and delegates. New shared `_require_positive_int` and `_raw_list_bound`. | refactor | D1, DRY |
| `ddd5dbb9`, `841e56d6` | The generated many-side relation resolver bounds at **five** call sites in `types/resolvers.py` — **three** `bounded_rows` and **two** `bounded_rows_async` — all after per-relation visibility. **This row previously read "four sites (two sync, two async)"**, a figure an evidence sweep supplied and Worker 0 carried without re-deriving; `grep -nE 'bounded_rows(_async)?\(' django_strawberry_framework/types/resolvers.py` returns five. | later feature | D6 |
| `03538f36` | `assert_relay_pagination_bound` gives the over-cap error one owner **for the keyset fork only** — its two call sites are `utils/connections.py::derive_keyset_window_bounds` and `connection.py::_resolve_keyset_connection`. The **offset** window's over-cap error still comes from Strawberry's `SliceMetadata.from_arguments`; the helper's own docstring says it exists because "a keyset cursor is not an offset". The two forks agree by message-mirroring, not by a shared owner. **This row previously read "shared by both window derivations", which is false** — Worker 0's own paraphrase of an evidence sweep, corrected here after Worker 3 caught the claim downstream in Decision 7. | refactor | D7 |
| `89ee8ac5` | spec-050. `bounded_rows` / `bounded_rows_async` gained `offset` / `requested_limit`; **`max_list_rows` changed meaning** to an accepted-coordinate and returned-row ceiling, explicitly disclaiming the "rows evaluated" promise; `DjangoListField` publishes `offset` / `limit` / conditional `orderBy`; new public `ListArgumentError`. | later feature | D6, bounds table, field-bound API |
| `aadca5a2` | spec-050. **`effective_bound`'s widening test changed from `if trusted:` to `if trusted is True:`** — the release accepted any truthy value. New constructor-site `validate_trusted_flag`. | correction | D10 |
| `4c483b6b`, `d3b91c8d`, `9a9f970c`, `4d98ad98` | spec-050 review fixes and scaffolding; `_close_async_iterator` gained a `caller` label. | later feature | — |

**Two bounds-table rows need re-wording, and no row needs re-valuing.** `max_list_rows`
("Rows a raw (non-Relay) list field may evaluate") and `max_scalar_bytes` ("UTF-8 bytes in
one scalar value") both describe behavior that has since widened. All 20 defaults are
unchanged.

**Public symbols the spec does not name**, all confirmed at `HEAD`:
`resource_policy.py` — `bounded_rows_async`, `validate_trusted_flag`, `DST_RESOURCE_DEADLINE`,
`ResourceLimitExceeded.detail`, `ResourceLimitExceeded.__reduce__`;
`utils/context.py` — `MISSING`, `restored_context_keys`;
`utils/policies.py` — `resolve_policy`;
`list_field.py` — `ListArgumentError`.

**Decisions that hold unchanged: 1, 3, 5, 8, 11, 12** (12's conclusion holds; its
present-tense version observation does not — finding C).

## Determination: no code cohort is opened

The maintainer's brief asks first whether anything the spec planned was **skipped in the
code**. The verification pass answers no:

- The bounds table reconciles **20/20** against the shipped `ResourcePolicy` dataclass — no
  default changed, no bound missing from the code, no shipped field missing from the table.
- Every symbol the Implementation plan names resolves at `HEAD` in the file the table claims,
  with the single exception of `connection.py::_resolve_connection_fast_path`, which a later
  refactor deleted while keeping its behavior (finding B).
- Every scenario the Test plan names has a real test asserting it; the sweep found **no**
  spec-named test that does not exist.

Every confirmed finding is therefore a **spec description that drifted** or a **post-release
change the spec never recorded** — not an unimplemented contract. Per the maintainer's
decided contract 3, the code is not edited. `docs/builder/bld-047-code.md` is **not** created
and the ownership partition above stands as declared.

### Verification commands behind findings A-M

Read-only; none mutates the tree. The `HEAD` copy is `<scratchpad>/head`.

```shell
git show 567cc6d0:django_strawberry_framework/mutations/resolvers.py | grep -c '^\s*check_deadline(info)'   # 2
grep -c '^\s*check_deadline(info)' <head>/django_strawberry_framework/mutations/resolvers.py                # 1
git log --oneline -S'_resolve_connection_fast_path' -- django_strawberry_framework/connection.py            # de2601e9
git log --oneline -S'check_deadline' -- django_strawberry_framework/mutations/resolvers.py                  # 6013cda6
git merge-base --is-ancestor 567cc6d0 6013cda6                                                              # exit 0
grep -n '__version__' <head>/django_strawberry_framework/__init__.py                                        # "0.0.15"
git show 567cc6d0:django_strawberry_framework/resource_policy.py | grep -c 'bounded_rows_async'             # 0
shasum <(git show 567cc6d0:docs/builder/bld-047-remediation.md) <(git show 99696bac^:docs/builder/bld-047-remediation.md)  # identical
```

### Contract-level questions escalated to the maintainer

[`BUILD.md`][build] `### Contract-level findings are escalated as maintainer decisions before
dispatch`. The maintainer's brief decided all three in advance, and they are recorded here
so the round is not re-fought:

1. **Does a post-release refactor's shape belong in the spec or the rationale?** Decided: the
   spec states the corrected contract directly; *what changed and why* goes in the rationale.
   Rejected alternative — an amendment block in the spec — because the spec is a contract,
   not a changelog ([`BUILD.md`][build] `## Spec rationale extraction`).
2. **Does a later feature's extension of an 047 surface belong in spec-047?** Decided: yes
   where it changes what 047's own contract now says, recorded in the rationale as
   later-feature drift. Rejected alternative — leaving spec-047 frozen at its release shape —
   because the maintainer's brief requires the spec to match what exists.
3. **Is the code authorized to change?** Decided: only on a confirmed defect, and then
   through a separate cohort. Rejected alternative — editing code to match the spec's stale
   prose — because the shipped behavior is correct and the prose is what drifted.

### Contingency: a code cohort

If the verification pass confirms a spec contract that the code does **not** implement — a
skipped feature rather than a stale description — Worker 0 opens
`docs/builder/bld-047-code.md` as a second cohort, and the partition above is re-declared
before dispatch. Its writable set would be the specific package modules named by the
finding; it would never include the baseline-dirty files above. As planned, no such finding
is dispatched.

## Dispatch shape for a spec-only round (declared deviation)

[`BUILD.md`][build] `### Isolation is non-waivable` puts Worker 2 in the build slot and
Worker 3 in the review slot. This round changes **no source**, and Worker 1 is the only role
permitted to edit a spec ([`worker-1.md`][worker-1] `## Spec custody`), so Worker 2 has
nothing it is allowed to do. The maintainer's brief decides this directly: *"if it's just the
spec file that needs to change then worker-1 alone can do that."*

The `Status:` chain and the isolation rule are both kept:

1. **Worker 1 — plan + authoring pass.** Writes `## Plan (Worker 1)` with the
   `### Dispatched findings checklist`, then performs the spec and rationale edits and
   appends `## Authoring report (Worker 1)` in the position the template gives Worker 2's
   build report. Sets `Status: built`.
2. **Worker 3 — review pass.** Reviews the diff. Sets `review-accepted` or `revision-needed`.
   **This is the isolation that matters here**: the reviewer is a fresh agent that did not
   write the prose it is grading.
3. **Worker 1 — final verification.** Audits the checklist ticks, reconciles, sets
   `final-accepted`.

Worker 2 is not dispatched. No pass in this round runs `pytest` with any `--cov*` flag.

## Final-gate exception, recorded in advance

[`BUILD.md`][build] `## Final test-run gate` runs `uv run pytest --no-cov`, the two
`manage.py` consistency checks, and the lint/format/diff gate, and a failure blocks
`final-accepted` **"unless a pre-flight baseline exception was recorded in the plan's
preamble."** This round records one, and it is a statement about what the instrument can
measure rather than a waiver:

- **This round changed no `.py` file.** The full suite, `manage.py check`, and
  `makemigrations --check --dry-run` all measure executable state this cohort did not touch.
- **The tree is not this round's to measure.** The concurrent spec-050 session is writing to
  it live: 12 tracked paths outside this cohort are dirty right now, and that set has grown
  at every pass of this round (6 → 11 → 14 → 12 as it commits and re-dirties). A suite run
  here would be grading **their** in-flight work. Green would be a pass this round did not
  earn; red would almost certainly be their mid-refactor state, and either reading would be
  attributed to this cycle by a later reader. That is the self-falsifying-instrument shape:
  a measurement whose subject is not the thing it will be quoted about.
- **What is run instead**, because it is what can actually see this cohort's change:
  `check_spec_glossary.py` on the spec; `check_trailing_commas.py --check` on the two files
  by explicit path (never repo-wide, which would rewrite the concurrent session's files);
  `git diff --check` scoped to the two files; and the link / anchor / citation integrity
  sweeps. Worker 0 has already run the last three: `check_trailing_commas --check` exit 0 and
  `git diff --check` clean on both files.
- **The maintainer must not read the suite's absence as a pass.** It was not run, and this
  round makes no claim about it. The spec-050 cycle owes its own final gate over the code.

## Round 2: HEAD moved past the gate (`d727a256` → `63a132be`)

Recorded 2026-09-14. `bld-047-final.md` graded `HEAD` = `d727a256`. One commit has landed since,
`63a132be` (spec-050's cancellation / exported-bound fix), and it rewrites two paths in this
cycle's owned set: `django_strawberry_framework/resource_policy.py` (253 lines) and
`tests/test_resource_policy.py` (140 lines). Re-graded against `63a132be`:

| Check | Result at `63a132be` |
|---|---|
| `resource_policy.py::__all__` | 16 names, unchanged. |
| Module docstring (`docs/TREE.md` source) | Unchanged; the diff starts at `_raw_list_bound`. |
| Bounds table 20/20 | Unchanged; no dataclass field moved. |
| Decision 4 bind-time classification | Re-verified: `extensions/resource_policy.py::_ValueBudget #"spec.kind == RELATION_MULTI"` (line 568 today), falling back to the `ID`-scalar rule. |
| Test-plan floors | Package tier now **120 rows / 191 node ids** (floor published 117 / 185); live tier 56 / 56. Floors hold. |
| Decision 6 coordinate seam | **Falsified.** See finding P. |
| Post-release register | **Missing its newest member.** See finding Q. |

Two independent instruments for the counts, as before: `grep -cE '^(async )?def test'` and the
`ast` parametrize multiplier, `unresolved_parametrize = 0` on both files.

### Findings carried into the pass-3 dispatch

- **P — Decision 6 names the wrong seam for the client window.**
  `docs/SPECS/spec-047-resource_policy-0_0_14.md` `#"The seam accepts `offset` and `requested_limit` client coordinates"`
  (Decision 6, the `max_list_rows is a coordinate-and-result ceiling` paragraph). At `63a132be`
  the exported `resource_policy.py::bounded_rows` / `::bounded_rows_async` take **no** window:
  `def bounded_rows(result, info, declared=None, *, trusted=False)`. The coordinate pair lives
  on the package-private `::_windowed_rows` / `::_windowed_rows_async`, which
  `list_field.py` calls directly; the exported pair delegates to them with no window, and
  `::_raw_list_bound` is still the one place either derives a limit. `list_field.py::_normalize_list_arguments`
  is the sole owner of the ceiling check on the coordinates. Pinned by
  `tests/test_resource_policy.py::test_the_exported_raw_list_bound_takes_no_client_window`
  (both colors × both coordinates, `TypeError` from the signature). Three spec sites read
  against this: the Decision 6 paragraph above; the DRY row
  `#"`bounded_rows` / `bounded_rows_async` are the only raw-list bound"` (true only read through
  the delegation — spec-050 Decision 5 already states that reading,
  `docs/spec-050-list_field_arguments-0_0_15.md #"is read through this delegation"`); and the
  test-plan sentence `#"a zero window that never advances it, offset arithmetic"`, whose
  offset rows now exercise `_windowed_rows_async` (every `offset=` call in that test file
  targets the private pair; the exported names appear only in the refusal row).
  **The bounds-table cell is not affected**: `max_list_rows` is still the ceiling the skip
  coordinate is checked against; what moved is which function receives the coordinate.
- **Q — The rationale's post-release change register stops at `d727a256`.**
  `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` `### The post-release change register`
  row `89ee8ac5` records that `bounded_rows` / `bounded_rows_async` *gained* `offset` /
  `requested_limit`; `63a132be` took them off the export again, and the register has no row
  saying so. The same commit added `resource_policy.py::_attach_cleanup_note` and
  `::_is_cleanup_diagnostic`: a cleanup error is demoted to a `__notes__` entry on the primary
  error only when it is an `Exception`; a `BaseException` (`asyncio.CancelledError`) propagates
  from both async cleanup seams. spec-050 Decisions 5 and 8 own that contract's text; spec-047's
  test plan already says `#"a cleanup failure that must not mask the source error"`, which stays
  true. The Decision 6 narrative paragraph (`#"client `offset` / `requested_limit` coordinates, and a narrower promise"`)
  is history and stays; it owes its successor one sentence.

### Fence change (maintainer, 2026-09-14)

"You can make DB edits as needed." The `.py`-and-spec fence stands for the workers; Worker 0
routes the round's deferred items onto the board as `CardItem` rows through
`examples/fakeshop/apps/kanban/services.py::append_card_item`, then regenerates `KANBAN.md` and
`KANBAN.html` with the two builders. Rows added, each to the card's `scope` section:

| Deferred item (`bld-047-final.md` catalog #) | Card | Why that card |
|---|---|---|
| 1 — `spec-047-…-terms.csv` line 30 `Joint version cut` cell | `056` | Its `notes`-column ruling item owns the class; the file was named on no card (`grep -c` = 0). |
| 2 — `clear_resource_context` public export, zero package callers | `053` | Same shape as its `_cascadable_edge_names` bullet; ruling recorded as owed, retirement conditional on it. |
| 3 — `docs/GLOSSARY.md` `## Value-budget walker` states input-type-only classification | `056` | Same shape as its `## Strictness mode` / `## Auth mutations` bullets; DB-generated, re-render. |
| 4 — remaining KANBAN / TREE fold-in | none added | Already `056`'s definition-of-done regenerate line; the `DONE-047` card body and the `DjangoListField` glossary entry were swept for the round's retired claims and carry none. |

### Dispatch (pass 3, same shape as `## Dispatch shape for a spec-only round`)

1. Worker 1 — authoring pass 3 on `bld-047-reconcile.md`: findings P and Q. Appends
   `## Authoring report (Worker 1, pass 3)` carrying its own
   `### Dispatched findings checklist (pass 3)`, because the `## Plan (Worker 1)` section may
   not be edited. Sets `Status: built`.
2. Worker 3 — `## Review (Worker 3, pass 3)`.
3. Worker 1 — `## Final verification (Worker 1, pass 3)`, and a `## Gate re-run at 63a132be`
   section appended to `bld-047-final.md`. **The advance exception's second leg is gone**: the
   concurrent session has committed, and `git status --short` carries no dirty `.py`, so
   `uv run pytest --no-cov` now measures `HEAD` and nothing else. It runs.

## Checklist

- [x] Cohort `047-reconcile`: spec + rationale reconciliation -> `docs/builder/bld-047-reconcile.md`
- [x] Round closing gate -> `docs/builder/bld-047-final.md`
- [x] Round 2 (HEAD `63a132be`): findings P + Q -> `docs/builder/bld-047-reconcile.md` pass 3 (`built` → `review-accepted`, 0 High / 0 Medium / 3 Low, one spec Low fixed at final verification → `final-accepted`); gate re-run -> `docs/builder/bld-047-final.md` `## Gate re-run at 63a132be`: `uv run pytest --no-cov -q` 7796 passed / 40 skipped / 0 failed, `manage.py check` clean, `makemigrations --check --dry-run` no changes, `ruff check` + `ruff format --check` clean, `git diff --check` clean; test-plan floor raised to 120 / 191 (measured, two instruments)
- [x] Round 2: three board rows (`053` scope order 70, `056` scope orders 96 and 97) via `append_card_item`; `KANBAN.md` (+3 lines) / `KANBAN.html` (data block) regenerated; `check_kanban_anchors.py` OK; every `#"substring"` the rows cite resolves to exactly one line in its file, except the `056` ruling-item citation, which matches 3 lines in `KANBAN.md` (the ruling item, its existing spec-025 citer, and the new row) — the same spelling that card already uses, and a generated-target citation of the class `056` itself catalogs


<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-047]: ../SPECS/spec-047-resource_policy-0_0_14.md
[spec-047-rationale]: ../SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md

<!-- docs/builder/ -->
[build]: BUILD.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
