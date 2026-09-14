# Build: Round cohort `047-reconcile` — spec + rationale reconciliation

Spec reference: [`docs/SPECS/spec-047-resource_policy-0_0_14.md`][spec-047] (whole file)
Rationale companion: [`docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`][spec-047-rationale]
Build plan: [`docs/builder/build-047-resource_policy-0_0_14.md`][build-047]
Status: final-accepted

## Plan (Worker 1)

### Round shape and declarations, copied from the build plan

- **Cycle kind:** reconciliation round over already-shipped work. No spec slice, so
  `### Spec slice checklist (verbatim)` is replaced by `### Dispatched findings checklist`
  ([`BUILD.md`][build] `### Dispatched findings checklist`).
- **Dispatch shape:** the build plan's `## Dispatch shape for a spec-only round (declared
  deviation)` puts the plan and the authoring in this one Worker 1 pass, because the round
  changes no source and Worker 1 is the only role permitted to edit a spec. Worker 3 still
  reviews a diff it did not write, so isolation is kept.
- **Ownership partition:** single cohort `047-reconcile`, owning exactly
  `docs/SPECS/spec-047-resource_policy-0_0_14.md`,
  `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`,
  `docs/builder/bld-047-reconcile.md`, and
  `docs/builder/worker-memory/047-worker-1.md`. No other cohort exists, so no file is
  contended and no shared shape needs assigning.
- **Hot-path declaration:** none. The cohort edits no executable code.
- **Floor-verification scope:** none. No Django / Strawberry / channels integration seam is
  touched by a documentation-only cohort. Floor facts, copied from [`BUILD.md`][build]
  `## Floor verification` because Decision 13 reasons about version-dependent upstream
  behavior: the supported floor is Django **5.2.16** on Python **3.10** with
  strawberry-graphql **0.316.0**. No floor venv is built; this pass runs no tests.
- **Boundary count:** zero. The round adds no guard, cap, rejection path, or validation
  branch, so `### Slice splitting`'s boundary trigger is answered at zero and the cohort is
  one unit.
- **Grading surface:** `HEAD`, never the working tree — and **`HEAD` moved during this pass**.
  It was `91c2d880` when the pass opened and `d727a256` when it closed; the concurrent session
  committed its spec-050 work mid-pass (`d727a256`, "judge the offset guard on the order Django
  compiles, and close a source its own deadline rejects"), which touched
  `django_strawberry_framework/resource_policy.py`,
  `django_strawberry_framework/list_field.py`, `tests/test_resource_policy.py` and
  `tests/test_list_field.py` — four of the files this pass grades against, one of which it
  publishes a count from. **Everything was re-measured against `d727a256`**: the tree was
  re-extracted read-only, byte identity with `git show d727a256:<path>` re-proved by `shasum`
  for all twelve files read, both test-count instruments re-run, and all 26 `path::Symbol`
  citations re-resolved. Every figure in this artifact and in the two documents is a `d727a256`
  reading. No `git stash` / `checkout --` / `restore` / `worktree` was run at any point.

### DRY analysis

- **Helper inventory checked.** Refreshed **for the whole package** twice this pass — the
  `worker-1.md` `### Package-wide helper inventory before helper planning` AST script, run
  first at `91c2d880` and re-run at `d727a256` after the concurrent commit landed. **2,081
  lines** over `django_strawberry_framework/` at `d727a256`, written to the session scratchpad
  (never `docs/shadow/`, whose four subfolders each have one owning generator). Shapes
  searched: `bound`, `narrow`, `min`, `reject`, `policy`, `deadline`, `clear_`, plus the seven
  symbol names this round's findings turn on — 176 matching lines, opened selectively rather
  than read end to end. Relevant candidates found and **cited in the spec rather than
  authored**: `resource_policy.py::effective_bound`, `::_raw_list_bound`,
  `::_require_positive_int`, `::validate_trusted_flag`, `utils/policies.py::resolve_policy`,
  `utils/context.py::restored_context_keys`, `utils/errors.py::coded_error_extensions`. The
  re-run's one net new symbol (`resource_policy.py::_cleanup_rejected_async_iterable`, added
  by `d727a256`) belongs to spec-050's async-cleanup contract and changes nothing this round
  states.
- **Existing patterns reused.** The prose patterns the pair already owns: the spec's numbered
  `### Decision N` shape with a one-line `[rationale]` pointer per decision, and the
  rationale's `## Change record` entry shape (bold verdict clause, the round or commit that
  caused it, then "a claim the spec may no longer make" where one exists). The new register is
  a new section in that file rather than a new file.
- **New helpers justified.** None. This round writes no code and proposes no new helper,
  constant, validation branch, coercion utility, or test helper. The build plan's
  `## Determination: no code cohort is opened` is the standing answer: every confirmed finding
  is a spec description that drifted, not an unimplemented contract.
- **Duplication risk avoided.** Two, both specific to a spec/rationale pair:
  1. **The same correction stated in both files.** The division is the round's whole point —
     the spec states the corrected contract with no history, the rationale carries what
     changed and why. Every finding below is therefore assigned to exactly one file, or split
     with the *contract* half in the spec and the *chronology* half in the rationale, and the
     plan says which.
  2. **A second copy of the post-release change register.** The register lives in the build
     plan, which closes with the cycle. It is written into the rationale's `## Change record`
     once — the durable home — and is not restated in the spec, this artifact, or the memory
     file.

### Implementation steps

Paths are the two writable documents; the anchors are pin-at-write-time and were verified
against the current files before each edit.

1. `docs/SPECS/spec-047-resource_policy-0_0_14.md` — **Version boundary** preamble and
   **Decision 12**: restate the version fact so it is true at any later date (finding C).
2. Spec **bounds table**: re-word the `max_list_rows` and `max_scalar_bytes` rows. No default
   is re-valued — the table reconciles 20/20 against the shipped dataclass.
3. Spec **User-facing API → The rejection**: record `detail` and `__reduce__` as part of the
   exception's shape, keeping the wire envelope as it actually is (`bound` / `limit` /
   `charged`; `detail` rides in the message, not in `extensions`) (finding L).
4. Spec **Decision 2**: replace "the end-of-operation clear" with the snapshot-and-restore
   the extension actually performs, naming `utils/context.py::restored_context_keys` and the
   public `MISSING` sentinel, and state the nested-operation guarantee (findings J, O-1).
5. Spec **Decision 3**: add the two hardening facts that are contract — the shared
   `_STRUCTURAL_DELIMITER_PAIRS` bracket families, and that a non-`str` query is declined
   rather than handed to the lexer (register `2d94b89e`, `a8f31a2d`).
6. Spec **Decision 4**: add operation variable defaults as the fourth value source (finding H);
   replace the "classified by TYPE, never by argument name" enumeration with the shipped
   ladder, bind spec first (finding O-2).
7. Spec **Decision 6**: state the two-colored seam (`bounded_rows` + `bounded_rows_async`),
   the shared `_raw_list_bound` body, the `offset` / `requested_limit` coordinates, and what
   `max_list_rows` now promises (findings F, register `89ee8ac5`, `ddd5dbb9`/`841e56d6`).
8. Spec **Decision 7**: one `resolve_connection`, not two entry points; the deleted
   `_resolve_connection_fast_path` citation removed; the plan-time window's own narrowing and
   the single over-cap error owner (findings B, register `292c7411`, `de2601e9`, `03538f36`).
9. Spec **Decision 9**: re-enumerate the deadline seams against `HEAD` (findings A, B); add
   the finiteness domain and the fail-closed hostile-stash behavior (register `dc00f4a6`,
   `a8f31a2d`).
10. Spec **Decision 10**: the widening test is exactly `True`, and `validate_trusted_flag` is
    the constructor-site half (finding Q / register `aadca5a2`).
11. Spec **Decision 11**: the extensions container is not consulted through `__bool__`, and
    the payload is built by `utils/errors.py::coded_error_extensions`
    (register `18550f5d`, `a8f31a2d`).
12. Spec **Decision 13**: drop the falsified `_run_plain_form_pipeline_sync` exclusion and
    re-count the boundaries it opens with (finding O-5).
13. Spec **Implementation plan**: name `bounded_rows_async`, `validate_trusted_flag`,
    `DST_RESOURCE_DEADLINE` on the module's delivered surface (finding G), and add the
    shared-module note for `utils/policies.py`, `utils/errors.py` and `utils/inputs.py`
    (findings K, O-8).
14. Spec **Helper-reuse obligations (DRY)**: re-write the `effective_bound` and
    `_ValueBudget._reject` obligations so each states the rule that actually holds
    (findings O-3, O-4).
15. Spec **Edge cases**: the sixth unmeasurable-upload spelling, the scalar-where-a-list
    coercion's real charge, and the bytes-like scalar (register `ba15c767`, `597dbbb4`).
16. Spec **Test plan**: re-derive both counts, define the unit at the point of publication,
    move the malformed-document pair to the tier that owns it, and narrow the two overstated
    assertion claims (findings N, O-6, O-7).
17. `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` — re-point the stranded
    `[spec-047-d13]` link definition at Decision 13's current heading (finding D).
18. Rationale — replace both citations of the deleted per-cycle artifact with the one
    `git show` pointer the build plan proved sufficient (finding E).
19. Rationale — append `### The post-release change register` to `## Change record`: the
    21 commits, what each did to the 047 surface, and every claim the spec may no longer
    make. Extend the keyed decision entries the spec edits falsify.
20. Verify: `check_spec_glossary.py` exits 0; every in-page anchor resolves; every
    reference-style link has a definition and every definition a use; the 10 canonical group
    headers in order in both files; every `path::Symbol` and `path #"substring"` citation
    resolves at `HEAD`; `git status --short` shows only the four writable paths.

### Test additions / updates

None; this round changes no tests.

### Implementation discretion items

- **Where a two-halved finding's split falls.** For a finding whose contract half and
  chronology half are both worth keeping (F, H, J, O-2), the exact sentence boundary between
  spec and rationale is the author's, provided the spec carries no chronology and the
  rationale names the decision by heading. Assessed: the division rule is fixed by the
  maintainer and by [`BUILD.md`][build] `## Spec rationale extraction`; only the wording is
  discretionary.
- **Ordering inside the new register.** Commit order versus decision order. Assessed as
  presentational: the register is keyed to decisions either way, which is what makes it
  lookup-able.

### Dispatched findings checklist

One box per finding dispatched to this cohort, quoting the finding as
[`docs/builder/build-047-resource_policy-0_0_14.md`][build-047] states it, with the
symbol-qualified path Worker 0 recorded.

- [x] **A.** "Decision 9 names a mutation deadline seam that no longer exists." — at `HEAD`
      `django_strawberry_framework/mutations/resolvers.py` carries one `check_deadline(info)`,
      in `mutations/resolvers.py::run_write_pipeline_sync`; commit `6013cda6` folded delete
      onto the shared skeleton, so `mutations/resolvers.py::_run_delete` inherits the seam
      instead of owning a second one.
- [x] **B.** "Decision 9 and Decision 7 name `connection.py::_resolve_connection_fast_path`,
      which was deleted." — at `HEAD` the check sits in
      `django_strawberry_framework/connection.py::DjangoConnection.resolve_connection`, and
      there is one `resolve_connection` definition rather than the two entry points
      Decision 7 describes.
- [x] **C.** "Decision 12's present-tense version claim is false at `HEAD`." —
      `django_strawberry_framework/__init__.py::__version__` reads `0.0.15`. The conclusion
      (this card takes no bump) holds; the observation is restated so it is true at any later
      date.
- [x] **D.** "The rationale's `[spec-047-d13]` link definition is a stranded anchor." — it
      targeted `#decision-13--three-bounds-this-policy-still-owes-and-three-exclusions-that-are-audited-rather-than-forgotten`;
      Decision 13's heading is now "What this policy does not bound, and why each boundary is
      deliberate".
- [x] **E.** "The rationale cites a deleted per-cycle artifact twice." —
      `docs/builder/bld-047-remediation.md` does not exist at `HEAD`; one pointer discharges
      it, `git show 99696bac^:docs/builder/bld-047-remediation.md`.
- [x] **F.** "The raw-list seam has an async twin the spec does not know about." —
      `django_strawberry_framework/resource_policy.py::bounded_rows_async` is in the module's
      own `__all__` at `HEAD`, and `list_field.py` / `types/resolvers.py` await it on their
      async paths.
- [x] **G.** "The module's public surface has grown three names the spec never lists." —
      `django_strawberry_framework/resource_policy.py` `__all__` carries 16 entries at `HEAD`,
      adding `bounded_rows_async`, `validate_trusted_flag`, `DST_RESOURCE_DEADLINE`. None is a
      root package export.
- [x] **H.** "Variable DEFAULTS are charged, and the spec describes a walk that ignores them."
      — `django_strawberry_framework/extensions/resource_policy.py::charge_document` folds
      each operation's variable-definition defaults into the per-operation variable map before
      argument values are charged (commit `597dbbb4`).
- [x] **I.** "Bytes-like scalars are charged against `max_scalar_bytes`." —
      `extensions/resource_policy.py::_ValueBudget._charge_leaf` charges `nbytes` (falling
      back to `len`) for `bytes` / `bytearray` / `memoryview`.
- [x] **J.** "A nested schema operation now RESTORES the outer policy context." —
      `extensions/resource_policy.py::DjangoResourcePolicyExtension.on_operation` brackets the
      operation with `utils/context.py::restored_context_keys` over both keys (commit
      `ba15c767`).
- [x] **K.** "The shared precedence ladder moved to `utils/policies.py::resolve_policy`." —
      `resource_policy.py::resolve_resource_policy` survives under its spec-named name and
      delegates; the same commit folded the positive-integer rule into
      `resource_policy.py::_require_positive_int` and the deadline-plus-bound seam into
      `resource_policy.py::_raw_list_bound`.
- [x] **L.** "`ResourceLimitExceeded` gained a `detail` field and `__reduce__`." —
      `resource_policy.py::ResourceLimitExceeded.__reduce__` at `HEAD`; the wire `extensions`
      payload is still `bound` / `limit` / `charged`, built by
      `utils/errors.py::coded_error_extensions`.
- [x] **S-1.** Not a build-plan finding; found by this pass's own status-line re-verification
      (`worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`). The spec
      named its sibling card **twice** as `WIP-ALPHA-049-0.0.14`; the board reads
      `DONE-049-0.0.14`. Both repointed. The id is live forward-reference prose, not a
      quotation and not a lifecycle-transition sentence, so a prefix flip is the whole fix.
      This is outside the population of the board's own archived-spec card-id sweep, which
      globs `spec-03[4-9]` — no overlap, nothing double-owned.
- [x] **M.** "Not a finding — a decoy to pre-empt." `TODO-BETA-047-0.1.2` in
      `examples/fakeshop/apps/products/schema.py` and in
      `docs/SPECS/spec-060-search_fields-0_1_2.md` is the old numbering of a different,
      unshipped search card. Discharged by leaving both untouched; confirmed in
      `git status --short`.
- [x] **N.** "Both published test-row counts are large undercounts." — re-derived at `HEAD`
      this pass with both instruments; the unit is now defined where the numbers are
      published.
- [x] **O-1.** "`clear_resource_context` is exported, spec-named, and called by nothing in the
      package." — `grep -rn --include='*.py' clear_resource_context` over the `HEAD`
      extraction hits `resource_policy.py`'s definition and export plus
      `tests/test_resource_policy.py` only. Decision 2's "end-of-operation clear" described the
      retired mechanism.
- [x] **O-2.** "The value walker has a third classification signal above the type rule and the
      one `ids` name rule" — the owning mutation's bind-time `_input_field_specs`, read through
      `extensions/resource_policy.py::_mutation_input_specs` / `::_nested_specs_map`, is what
      recognizes a raw-pk relation list typed `[Int!]` as relation ids.
- [x] **O-3.** "`effective_bound` is not the only narrowing site":
      `extensions/resource_policy.py::_page_bound` open-codes `min(value, policy.max_page_size)`.
      DRY obligation 3 as written was false.
- [x] **O-4.** "`_ValueBudget._reject` is not the only rejection constructor in the walker":
      two `ResourceLimitExceeded(...)` constructions sit in
      `extensions/resource_policy.py::_ValueBudget._charge_upload`'s unmeasurable-size
      branches, and three more in `::_DocumentBudget.charge_selection` /
      `::_DocumentBudget.charge_collection`. DRY obligation 5 as written was false.
- [x] **O-5.** "Decision 13's second audited exclusion is falsified."
      `forms/resolvers.py::_run_plain_form_pipeline_sync` no longer exists; both form flavors
      share `forms/resolvers.py::_run_form_pipeline_sync`, which calls
      `mutations/resolvers.py::run_write_pipeline_sync` unconditionally.
- [x] **O-6.** "The Test plan misfiles the malformed-document pair." — they are live rows, and
      `tests/test_resource_policy.py`'s module docstring says so.
- [x] **O-7.** "Two Test-plan assertion claims overstate." — "each asserting the exact charge"
      is true of only one of the two connection-shape rows; "node ids under, at, and over" is
      two rows, not three.
- [x] **O-8.** "Three modules the shipped surface depends on are absent from the
      Implementation plan": `utils/policies.py`, `utils/errors.py::coded_error_extensions`,
      `utils/inputs.py::RELATION_MULTI`.
- [x] **R-1.** Register `292c7411` / `03538f36`: "`derive_connection_window_bounds` now
      narrows through `resolve_relay_max_results` before building the slice metadata. **At the
      release the policy ceiling reached the offset window unclamped**"; and
      `utils/connections.py::assert_relay_pagination_bound` gives the over-cap error one owner.
      Bears on D7.
- [x] **R-2.** Register `18550f5d`: "`_with_resource_policy_extension` stopped normalizing
      `extensions` through truthiness ... the class-or-instance test became
      `_extension_entry_matches`." Bears on D11.
- [x] **R-3.** Register `ba15c767` (ii) and (iii): the scalar-where-a-list-is-declared
      coercion now actually charges a container plus one depth level, and an upload whose
      `size` **raises on access** is a sixth unmeasurable spelling. Bears on D4, Edge cases.
- [x] **R-4.** Register `2d94b89e` and `a8f31a2d` (ii): `_STRUCTURAL_DELIMITER_PAIRS`
      single-sources the three bracket families, and
      `extensions/resource_policy.py::scan_document_text` declines a non-`str` query. Bears on
      D3.
- [x] **R-5.** Register `dc00f4a6`: a **finiteness** check on `execution_deadline_seconds`
      (`inf` was previously accepted), and `ResourcePolicy.narrowed()` compares normalized
      values. Bears on D9, D10.
- [x] **R-6.** Register `a8f31a2d` (iv) and (vi): `resource_policy.py::check_deadline` fails
      closed on a hostile stashed deadline, and `resource_policy.py::bounded_rows` catches
      `KeyError` beside `TypeError`. Bears on D9.
- [x] **R-7.** Register `89ee8ac5`: "`max_list_rows` changed meaning to an accepted-coordinate
      and returned-row ceiling, explicitly disclaiming the 'rows evaluated' promise", and
      `bounded_rows` / `bounded_rows_async` gained `offset` / `requested_limit`. Bears on D6
      and the bounds table.
- [x] **R-8.** Register `aadca5a2`: "`effective_bound`'s widening test changed from
      `if trusted:` to `if trusted is True:`", with the constructor-site
      `resource_policy.py::validate_trusted_flag`. Bears on D10.
- [x] **R-9.** Register `ddd5dbb9` / `841e56d6`: "The generated many-side relation resolver
      bounds at four sites now (two sync, two async), all after per-relation visibility."
      Bears on D6.
- [x] **R-10.** Register, bounds table: "**Two bounds-table rows need re-wording, and no row
      needs re-valuing.**" Both re-worded; the table re-checked 20/20 against the shipped
      `ResourcePolicy` dataclass this pass.
- [x] **R-11.** Register, rationale: "**311 commits** separate the release `567cc6d0` from
      `HEAD` ... Each is a rationale entry this round owes." The register is written into the
      rationale's `## Change record`.

---

## Authoring report (Worker 1)

### Files touched

- `docs/SPECS/spec-047-resource_policy-0_0_14.md` — every drifted statement rewritten to
  state the corrected contract directly. No amendment block, no "as of", no "previously", no
  retraction paragraph: the spec reads as though it had been right from the start. Sections
  changed: the Version boundary preamble; the bounds table (two rows re-worded, no default
  re-valued); the rejection envelope; Decisions 2, 3, 4, 6, 7, 9, 10, 11, 12, 13; the
  Implementation plan; the Helper-reuse obligations; Edge cases; the Test plan.
- `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` — the stranded
  `[spec-047-d13]` definition re-pointed; both citations of the deleted per-cycle artifact
  replaced with the one `git show` pointer; a new `### The post-release change register`
  appended to `## Change record`; the keyed decision entries the spec edits touched extended,
  and new entries added for the decisions that had none.
- `docs/builder/bld-047-reconcile.md` — this artifact.
- `docs/builder/worker-memory/047-worker-1.md` — one appended entry.

**Byte counts.**

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-047-resource_policy-0_0_14.md` | 63,529 | 78,775 | +15,246 |
| `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` | 19,262 | 40,070 | +20,808 |

The spec grew rather than shrank. That is the round's shape: no deliberation moved out of it,
and several decisions gained the clauses that make a stale enumeration true — the ladder in
Decision 4, the two colors in Decision 6, the re-enumerated seams in Decision 9. The one
deletion is Decision 13's falsified audited exclusion.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-047-resource_policy-0_0_14.md`
  — **pass**, `OK: 34 terms` (unchanged from the pre-flight reading, so no term lost its only
  link).
- `uv run python scripts/check_trailing_commas.py --check <the three markdown paths>` —
  **pass**, exit 0. Explicit paths, never a bare invocation: this script's default is a
  repo-wide auto-fix, which would rewrite the concurrent session's files.
- **In-page anchors.** Every `](#...)` target re-derived to a GitHub slug from each file's own
  headings and compared — spec **13 distinct, 13 resolved, 0 dangling**; rationale **3
  distinct, 3 resolved, 0 dangling**; this artifact **0**. This is the check Decision 13's
  heading rename failed at the release, which is what stranded the rationale's
  `[spec-047-d13]`.
- **Reference-style links, all three files.** Every `][label]` use has a definition and every
  definition has a use — spec **40 / 40**, rationale **17 / 17**, artifact **4 / 4**, with
  0 undefined and 0 unused in each. All three bottom blocks carry the 10 canonical group
  headers in the `START.md` order. Every definition's path resolves on disk, checked from each
  file's own directory rather than from the repository root — the rationale sits in
  `docs/SPECS/appx/`, so its relative paths climb two levels, and a same-named file one level
  up would otherwise mask the depth.
- **Citations.** Every citation written or kept in the spec resolves at `d727a256`:
  **26 qualified `path::Symbol`, 26 resolved**; **3 bare `::Symbol` continuation forms**
  (`::_nested_specs_map`, `::_DocumentBudget`, `::derive_keyset_window_bounds`), all resolved
  against the package; and **1 `path #"substring"` citation**
  (`extensions/resource_policy.py #"_STRUCTURAL_DELIMITER_PAIRS: tuple"`), matching **exactly
  one** source line. Resolution was by `ast` parse of the extracted tree, not by grep, so a
  name appearing only in a comment or docstring cannot pass. The rationale names two symbols
  that deliberately do NOT resolve — `connection.py::_resolve_connection_fast_path` and
  `forms/resolvers.py::_run_plain_form_pipeline_sync` — which is the point of the entries that
  carry them; each is marked "no longer exists at any current revision" and carries the
  `git show <death commit>^:<path>` pointer that reaches it.
  `scripts/check_citations.py` does not gate `docs/` prose, which is exactly why
  `_resolve_connection_fast_path` rotted unnoticed; this sweep is the substitute for the
  missing gate and is recorded so the next pass repeats it rather than trusting the hook.
- **Test-row counts, re-measured as written, then re-measured again** (the instruments and
  figures behind the Test plan's two numbers):
  - Instrument 1, `grep -cE '^(async )?def test'` over the extracted tree —
    `tests/test_resource_policy.py` **117**,
    `examples/fakeshop/test_query/test_resource_policy_api.py` **56**.
  - Instrument 2, an `ast` parse counting module-level `test*` functions and multiplying every
    `@pytest.mark.parametrize` argvalues cardinality (stacked decorators multiply) —
    **117 functions → 185 node ids** package, **56 → 56** live, with
    `unresolved_parametrize = 0` on both, so no cardinality was guessed. The two instruments
    agree exactly on the function counts; the node-id figure differs only by the
    transparently computed expansion.
  - **The first measurement of this pass read 113 / 180**, at `91c2d880`. The concurrent
    session's `d727a256` added four async-cleanup rows to the package file while this pass was
    running. Both readings were correct and neither is durable, which is why the spec now
    publishes both counts as **floors** with the unit named: a later reader who measures a
    larger number learns the file grew, not that the plan is wrong. This is the whole reason
    the count is re-derived rather than copied — the build plan's own figure was already one
    revision stale by the time it was read.
  - Byte identity with `git show d727a256:<path>` was re-proved by `shasum` for both files
    before either instrument ran.
- **Bounds table re-checked 20/20** at `d727a256`, mechanically: the spec's table rows were
  parsed and differenced against `resource_policy.py::ResourcePolicy`'s 20 `AnnAssign` field
  defaults. **0 in code without a row, 0 in a row without the code, 0 value mismatches.** No
  default is re-valued in this pass.
- **`resource_policy.py` `__all__` re-counted: 16 entries**, the three the spec never listed
  (`bounded_rows_async`, `validate_trusted_flag`, `DST_RESOURCE_DEADLINE`) now named in the
  Implementation plan.
- `git status --short` — **clean of anything this cohort does not own.** Two modified
  (`docs/SPECS/spec-047-resource_policy-0_0_14.md`,
  `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`), one untracked
  (`docs/builder/bld-047-reconcile.md`); the memory file is under a `.gitignore`d path.
  `docs/builder/build-047-resource_policy-0_0_14.md` also shows untracked — it is Worker 0's
  plan for this cycle, not this pass's output and not this pass's to stage.
  **The build plan's baseline-dirty list is now stale, and that is a finding rather than a
  problem**: all seven of those files were committed by the concurrent session in `d727a256`,
  so they no longer appear dirty. This pass edited none of them at any point, before or after
  that commit.
- **`ruff` and `pytest` deliberately not run.** This pass changes no `.py` file, so
  `uv run ruff format` / `check` have nothing in scope; a repo-wide write-mode run would
  rewrite the concurrent session's files, which is the churn the scoping rule exists to stop.
  No pass in this round runs `pytest`, with or without a coverage flag.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **Where each finding's two halves landed.** The rule applied throughout: the spec states
  what the code does now, in the present tense, with no trace of what it used to do; the
  rationale states what changed, which commit changed it, why, what the claim used to be, and
  what the spec may no longer say. Findings F, H, J, O-2 and the `max_list_rows` meaning
  change are split that way; C, D, E, N are single-file.
- **`clear_resource_context` kept in the Implementation plan.** It is still defined and still
  exported, so the slice-1 delivery row is accurate as a statement of what shipped. What was
  false was Decision 2's claim that an end-of-operation *clear* is the lifecycle mechanism.
  Decision 2 now states the snapshot-and-restore, and the rationale records that the package
  itself no longer calls the clear — only `tests/test_resource_policy.py` does. Deleting the
  export would be a code change, which this round's determination forbids.
- **Decision 13's boundary count re-derived by enumeration, not by arithmetic.** The decision
  opened with "six boundaries ... three audited exclusions". One audited exclusion is
  falsified and removed, so the enumeration is now five and two. The numbers were re-counted
  from the surviving bolded entries rather than decremented.
- **The two re-worded DRY obligations state a rule, not an exception list.** "`effective_bound`
  is the only narrowing rule" was false because `_page_bound` narrows too; the repair is to say
  what each rule governs (a field's declared maximum against the request policy, versus a
  document's literal page argument against the ceiling) rather than to append "except".
  `_ValueBudget._reject` gets the same treatment: it owns every *threshold* rejection, and the
  direct constructions beside it reject on an unmeasurable input, where there is no charge to
  compare.
- **`max_scalar_bytes`'s row keeps the text/number carve-out.** Widening it to bytes-like
  values does not widen it to numbers: Edge cases still says a large numeric literal is
  refused by CPython's `sys.get_int_max_str_digits`, as a malformed-input failure rather than
  a typed resource rejection. That distinction is contract and survived the re-wording intact.
- **The sibling card id was repointed, and the surrounding population deliberately was not.**
  `WIP-ALPHA-049-0.0.14` → `DONE-049-0.0.14` at both of its sites. The board carries a large
  open item for card-id rot across archived specs, but its declared population is the
  `spec-03[4-9]` pair tree; spec-047 is not in it, so this is a repair of this spec's own two
  sites rather than a bite out of somebody else's sweep. Its taxonomy still applied: both
  sites are plain live pointers, so both are clean prefix flips — no quotation was rewritten
  and no lifecycle-transition sentence was de-tensed, because this spec has neither.
- **spec-050's list-argument surface is named in prose, not linked.** It owns
  `DjangoListField`'s `offset` / `limit` arguments and `ListArgumentError`; spec-047 owns only
  what `max_list_rows` promises. The file is the live concurrent cycle's and sits at the
  `docs/` top level until the next spec's archival sweep moves it, so a reference-style link
  into it would be a link this round cannot keep resolving. Naming it without a link says the
  true thing and strands nothing.

### Notes for Worker 3

- **Grade against `HEAD`, and re-check which `HEAD`.** `HEAD` moved from `91c2d880` to
  `d727a256` while this pass ran, and the commit that moved it touched four of the files this
  pass grades against. Every figure here is a `d727a256` reading, re-taken after the move. The
  build plan's baseline-dirty list is stale as a result — those files are committed now, not
  dirty — so do not read a clean `git status` as evidence that this pass touched them. Read
  from a read-only extraction whose byte identity you prove with `shasum`, and never run
  `git stash`, `git checkout --`, `git restore`, or `git worktree` in this tree.
- **The decoy.** A repo-wide `grep 047` hits `TODO-BETA-047-0.1.2` in
  `examples/fakeshop/apps/products/schema.py` and `docs/SPECS/spec-060-search_fields-0_1_2.md`.
  Old numbering of a different, unshipped search card; `spec-060`'s own slice table owns the
  fix. Out of scope, deliberately untouched.
- **The one check the hooks cannot run for you.** `scripts/check_citations.py` is
  `path::Symbol`-only and skips `docs/` prose entirely, so no gate will catch a rotted
  citation in either file. If you re-verify one thing mechanically, re-verify the citation
  sweep — the finding that started this round (`_resolve_connection_fast_path`) is exactly
  what that gap lets through.
- **Counts are the other thing worth re-deriving**, and one of them already moved once
  inside this pass. The published counts in this diff are the Test plan's two row figures
  (published as floors, with the unit named), Decision 13's "five boundaries / two audited
  exclusions", the bounds table's 20 rows, and the register's 312 / 48 / 19 commit figures.
  Each was measured as written and each is re-measurable from the instruments recorded above.
  If you re-measure the package tier and get more than 117, that is the file growing, which
  is what the floor framing is for — not a defect.

### Notes for Worker 1 (spec reconciliation)

Carried into final verification:

1. **`docs/SPECS/appx/spec-047-resource_policy-0_0_14-terms.csv` carries a falsified note and
   is outside this cohort's writable set.** Its `Joint version cut` row reads
   `the rule this card is NOT subject to`; the spec and the rationale both say the card **is**
   subject to it. The `notes` column is ungated — `check_spec_glossary.py` compares term and
   anchor only — so nothing will fail on it. Not fixed here because the file is not writable
   by this cohort's partition. A one-word edit by the maintainer, or a second cohort.
2. **`clear_resource_context` is a public export with no package caller.** Recorded in the
   rationale as fact. Whether it should be retired is a contract-level question — it is on the
   module's `__all__` — and therefore the maintainer's, not a worker's. Not a defect against
   the spec as it now reads.
3. **The spec's `## Current state` section was left alone.** Its vintage framing licenses
   dated observations of the pre-build repo, and every clause in it is an observation rather
   than a prediction — the rule in [`BUILD.md`][build], "observations stand, predictions do
   not". Nothing in it is a completion claim, so nothing in it is a stale figure.

---

## Review (Worker 3)

Reading surface: a read-only `git archive HEAD | tar -x` extraction at `d727a256`, byte
identity with `git show d727a256:<path>` proved by `shasum` for every package file quoted
below. No `git stash` / `checkout --` / `restore` / `worktree` was run. `HEAD` was
`d727a256` at the start and at the end of this pass.

### High:

None.

### Medium:

#### Decision 7 names an over-cap owner that the offset window does not use

`docs/SPECS/spec-047-resource_policy-0_0_14.md:228` (Decision 7, "The offset window narrows
through the same seam") closes with:

```docs/SPECS/spec-047-resource_policy-0_0_14.md:228
The over-cap rejection those windows raise has one owner,
`utils/connections.py::assert_relay_pagination_bound`, so the offset and keyset forks
cannot answer the same over-cap request with different errors.
```

"Those windows" are `derive_connection_window_bounds` and `derive_keyset_window_bounds`.
At `d727a256` the offset one **never calls** `assert_relay_pagination_bound`: the symbol
appears in `utils/connections.py` only at its own definition and inside
`::derive_keyset_window_bounds`, plus one call in `connection.py::_resolve_keyset_connection`
— both keyset sites. The offset window's over-cap error comes from Strawberry's
`SliceMetadata.from_arguments`, which `derive_connection_window_bounds` calls immediately
after resolving the cap. The helper's own docstring says so in as many words: it is "The ONE
spelling of the Relay `first` / `last` bound check **the keyset fork cannot run through**
`SliceMetadata.from_arguments`", and it names its two consumers as the keyset window
derivation and the keyset slicer.

Why it matters: this is precisely the defect class the round exists to remove — a decision
naming a seam that does not hold at `HEAD`, in the same decision whose previous citation
(`connection.py::_resolve_connection_fast_path`) rotted undetected for the same reason. The
consequence clause is still true, but for a different mechanism: parity holds because
`assert_relay_pagination_bound` is hand-written to reproduce `SliceMetadata`'s two messages,
not because one owner serves both forks. A reader who acts on the sentence as written will
look for a call that is not there.

Recommended change: state the mechanism the code has — the two keyset sites share
`assert_relay_pagination_bound`, which is written to `SliceMetadata`-parity messages so the
keyset fork cannot answer an over-cap request differently from the offset fork, which gets
that rejection from `SliceMetadata.from_arguments` itself. No test expectation: no behavior
changes.

### Low:

#### The register's "four sites (two sync, two async)" does not re-derive

`docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` — the `ddd5dbb9`, `841e56d6`
register row says "The generated many-side relation resolver bounds at four sites now (two
sync, two async)". Re-measured at `d727a256` by an `ast` walk over
`django_strawberry_framework/types/resolvers.py`: **five** `bounded_rows` /
`bounded_rows_async` calls — sync at `types/resolvers.py::_visible_many_rows` and at both
`bounded_rows(source, info)` returns of the generated many resolver, async at
`::_visible_many_rows` and at the unprefetched async return — i.e. three sync and two async,
reached through four branching returns, two of which route via `_visible_many_rows`. The
figure is inherited verbatim from the build plan, so the round republished it without
re-deriving it. Recommended change: state the count with its unit (branching returns, or
call sites) or drop the number and name the branches, per the round's own rule that a count
published without its unit gets replaced by a third figure.

#### The register's `48` is not re-derivable from the population it states

The register's scope-and-method paragraph says 48 of the 312 post-release commits "touch one
of the twelve package modules this spec names (its Implementation plan's, plus
`forms/resolvers.py` from Decision 13)". The Implementation plan names **sixteen** package
modules, and `git rev-list --count 567cc6d0..d727a256 -- <those sixteen + forms/resolvers.py>`
is **62**. `48` reconciles only against a specific eleven-module subset (dropping
`optimizer/_context.py`, `extensions/__init__.py`, `__init__.py`, `types/base.py`,
`types/finalizer.py`) plus `forms/resolvers.py`. `312` and `19` both re-derive exactly
(`git rev-list --count 567cc6d0..HEAD` = 312; the table carries 19 commits in 15 rows, and
`git merge-base --is-ancestor 567cc6d0 <sha>` exits 0 for all 19). Recommended change: list
the twelve paths, or drop the figure — the register already says it is the one that does not
matter.

#### The Implementation plan's Slice 1 row now claims two post-release symbols as slice deltas

The row's `Delta` cell gained `validate_trusted_flag` and `bounded_rows_async`. Neither
existed at the release: `git show 567cc6d0:django_strawberry_framework/resource_policy.py |
grep -c` returns `0` for both, and the rationale's own register dates them to `dc00f4a6` and
`aadca5a2`. `DST_RESOURCE_DEADLINE` is fine — it is at the release (5 hits). The
`## Slice checklist` home still describes Slice 1 without them, so the two homes disagree
about what Slice 1 landed. The cell now enumerates all sixteen `__all__` entries, which reads
as "the module's delivered surface" rather than "this slice's delta"; if that is the intent
the column says otherwise. Recommended change: either move the two post-release names into
the `**Shared modules this surface consumes rather than owns**` note's shape (a surface note,
not a slice row), or say in the row that it enumerates the module's current surface.

#### One Test-plan clause claims more than its row asserts

The package-tier paragraph says "the snapshot round trip that hands an outer operation its
keys back — **including on the path where the document scan rejects**". The rejection-path
row is `tests/test_resource_policy.py::test_the_context_is_cleared_even_when_the_document_scan_rejects`,
which starts from an empty context and asserts `DST_RESOURCE_POLICY not in context` — it
pins the ABSENT-key half of `utils/context.py::restored_context_keys` (restore-to-cleared),
not the hands-back-a-prior-value half. The two rows that pin the hand-back
(`::test_nested_sync_schema_restores_the_outer_policy_and_deadline` and its async twin) run
on the non-rejecting path. Recommended change: split the clause — the round trip is pinned
on the normal path and its `finally` is pinned on the scan-rejection path — or add the
missing row as a follow-up. This is the same overstatement class finding O-7 corrected two
of.

#### Decision 3 states a transport guarantee the source denies

The new bullet ends "The transports type-check the query themselves; this scan declines
rather than depending on them to."
`extensions/resource_policy.py::scan_document_text`'s docstring says only the two HTTP views
do: "the WebSocket path performs no such check, so the decline is the scanner's own contract
rather than a transport's favor." The load-bearing half of the sentence is right; the
premise is not. Recommended change: "both HTTP transports type-check the query; the WebSocket
path does not, so the decline is this scan's own contract."

#### A count with no stated population survives in a sentence this pass rewrote

Decision 6's "A non-positive `max_rows` raises at the line that constructed the field,
matching the four target guards already there" — the pass extended this sentence with the
`validate_trusted_flag` clause but left "the four target guards" naming no population a
reader can count. Pre-existing and not a dispatched finding, but the sentence is now this
pass's. Recommended change: name what the four are, or cite the contract by content per
`START.md` "Cite contract by CONTENT, never ordinal".

#### Two internal figures in this artifact's plan section are stale against the register

`### Implementation steps` step 19 says the register carries "the 21 commits"; the register
as written carries 19 (the build plan's 21 was measured at `91c2d880`). `### Dispatched
findings checklist` R-6 cites `a8f31a2d` "(iv) and (vi)" for the fail-closed deadline and the
`KeyError` fallback; the rationale renumbers that commit's sub-items and they are (iv) and
(v) there. Neither reaches a shipped document. Recommended change: leave the checklist
quotations as the build plan stated them (that is the contract) and correct step 19's figure.

### DRY findings

- **No duplication introduced across the pair.** Every correction lands in exactly one file
  or is split contract-half / chronology-half as the plan declared. Swept the spec for the
  retired absolutes and the retired citations: `single place`, `only raw-list`, `entry
  points`, `_resolve_connection_fast_path`, `_run_plain_form_pipeline_sync`, `end-of-operation
  clear`, `35 rows`, `79 rows`, `six boundaries`, `three exclusions` — zero hits in the spec
  except the two rewritten DRY obligations that now state a rule instead of an absolute.
- **The rationale's two indexes are not a near-copy.** `#### What changed, by commit` is keyed
  by commit; `#### Claims the spec may no longer make` is keyed by decision, which
  [`BUILD.md`][build] `## Spec rationale extraction` requires per decision ("any claim the
  decision once made and may no longer make"). Different keys, both mandated; not a
  consolidation target.
- **The two re-written DRY obligations state rules, not exception lists, and both are
  complete.** Re-derived: `grep 'min('` across `django_strawberry_framework/` filtered to
  policy/bound vocabulary returns exactly two narrowing sites against a policy value —
  `resource_policy.py::effective_bound` and `extensions/resource_policy.py::_page_bound` —
  which is what obligation 3 now names. For obligation 5, an `ast` walk counting
  `ResourceLimitExceeded(` constructions by owner returns: `_ValueBudget._reject` 1,
  `_ValueBudget._charge_upload` 2, `_DocumentBudget.charge_selection` 2,
  `_DocumentBudget.charge_collection` 1 (three in `_DocumentBudget`, which is what the
  rewrite says — the build plan's "two more" was the undercount), plus two in
  `scan_document_text`, which is the pre-parse scan and outside the value walker the
  obligation scopes itself to.
- **Existence challenge: none raised.** The round authored no helper, constant, registry or
  indirection layer. `clear_resource_context` is the one live existence question and it is a
  contract-level call already routed to the maintainer (see `### Notes for Worker 1`).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — zero lines of diff.
`__all__` and the re-export list are untouched. Independently: `git diff --name-only | grep
-c '\.py$'` returns **0**, so the round changed no executable code at all, which is what its
plan and the build plan's `## Determination: no code cohort is opened` declared. The three
names the spec never listed (`bounded_rows_async`, `validate_trusted_flag`,
`DST_RESOURCE_DEADLINE`) are module-level entries in `resource_policy.py`'s own `__all__`
(re-counted: **16** entries) and none is a root package export, so no `__init__.py` pin
moves.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applicable — the cohort is documentation-only.

- **Version strings and card ids.** `WIP-ALPHA-049-0.0.14` → `DONE-049-0.0.14` at both of its
  sites (preamble and `## Out of scope`); `KANBAN.md` carries `DONE-049-0.0.14` in the index
  row and the card heading, so the flip matches the board. Decision 12 and the Version
  boundary preamble no longer read the quintet in the present tense; `__version__` at
  `d727a256` is `0.0.15` and the spec no longer asserts otherwise anywhere.
- **Links and anchors, both files, checked from each file's own directory.** Spec: 37
  headings, 13 distinct in-page anchors, **0 dangling**; 40 reference uses / 40 definitions,
  0 undefined, 0 unused. Rationale: 30 headings, 3 distinct in-page anchors, **0 dangling**;
  17 / 17, 0 undefined, 0 unused. Every definition path exists on disk (the rationale's climb
  two levels out of `docs/SPECS/appx/`), and every cross-file `#anchor` re-slugs to a real
  heading under GitHub's rules — **including the repaired `[spec-047-d13]`**, which now
  targets `#decision-13--what-this-policy-does-not-bound-and-why-each-boundary-is-deliberate`
  and resolves. Both bottom blocks carry the 10 canonical group headers in `START.md` order.
- **The retired per-cycle artifact's pointer holds.** `docs/builder/bld-047-remediation.md` is
  absent at `HEAD` (`git cat-file -e` fails) and `git show
  99696bac^:docs/builder/bld-047-remediation.md` returns 5,262 bytes. The one-pointer claim
  checks out: `diff <(git show 567cc6d0:<path>) <(git show 99696bac^:<path>)` is empty, so
  there is no second stale copy to reach for. Both prior citations of the dead path are gone.
- **The two deliberately-unresolvable symbols.** The rationale's
  `connection.py::_resolve_connection_fast_path` and
  `forms/resolvers.py::_run_plain_form_pipeline_sync` are the only two of its 8 qualified
  citations that do not resolve, both marked "no longer exists at any current revision" and
  both reachable: `git show de2601e9^:.../connection.py` carries the first (4 hits) and
  `git show 6013cda6^:.../forms/resolvers.py` the second (2 hits).
- **Glossary gate.** `uv run python scripts/check_spec_glossary.py --spec
  docs/SPECS/spec-047-resource_policy-0_0_14.md` → `OK: 34 terms`, exit 0. Unchanged from
  pre-flight, so no term lost its only link.
- **No staged anchors, no obsolete staging language.** `TODO(spec-047` and
  `TODO-ALPHA-047` return nothing in either file; `TODO-BETA-047-0.1.2` in
  `examples/fakeshop/apps/products/schema.py` and `docs/SPECS/spec-060-...` is the decoy the
  plan pre-empted and is untouched (`git status --short` confirms).
- **`scripts/review_inspect.py` skipped, with reason.** The round adds no `.py` file, touches
  no file under `optimizer/` or `types/`, and adds zero lines of logic anywhere —
  [`BUILD.md`][build] `### When to run the helper during build` triggers on none of its three
  Worker-3 conditions. Every source claim below was read from the `HEAD` extraction directly.

### What looks solid

- **No history leaked into the spec.** This was the round's central risk and it holds. A
  polarity sweep for `previously`, `as of`, `no longer`, `used to`, `formerly`, `at the
  release`, `post-release`, `since the release`, `now (returns|narrows|is|reads|does|says)`,
  `remediation round`, `review round`, `reconcil`, `amendment`, `retract`, `originally`,
  `earlier version`, `has since`, `changed meaning`, `this round`, `this pass` over the whole
  spec returns **three** lines, all pre-existing context in this diff: "opting in no longer
  opts out of the cap" (a contract sentence), "the reconciled synthesis docstring" (a slice
  delta), and Decision 12's one-line `[rationale]` pointer, which is exactly `worker-1.md`
  "Rules for the move" rule 1. Every clause the pass added states the current contract in the
  present tense. The +15KB is contract: the Decision 4 ladder, the Decision 6 two-color seam
  and coordinate ceiling, the Decision 9 re-enumeration and finiteness domain, the Decision 10
  widening test, the Decision 2 snapshot-restore. Nothing a reader must apply a chronology to.
- **Every re-written statement I re-derived is true at `d727a256`.** Decision 9's four seams
  are exactly the four `check_deadline` call sites: an `ast` resolution of every call's
  enclosing symbol returns `resource_policy.py::_raw_list_bound`,
  `connection.py::DjangoConnection.resolve_connection`, `relay.py::DjangoNodeField._resolve` /
  `::DjangoNodesField._resolve`, and `mutations/resolvers.py::run_write_pipeline_sync` — and
  nothing in `utils/connections.py`, which is what both Decision 9 and Decision 13's surviving
  audited exclusion claim. Decision 7's "there is ONE `resolve_connection`" holds (`grep 'def
  resolve_connection'` returns one hit) and the flag is `_resolves_total_count`; the clamp is
  resolved at the top, before `_guard_first_and_last`, and the deadline check after it, which
  is how Decisions 7 and 9 describe the same head without contradicting each other. Decision
  2's snapshot-and-restore, the `MISSING` sentinel's public export, both keys, and the
  exception path are all in `restored_context_keys` and `on_operation` as written. Decision
  4's five-rung ladder is `_charge_list_family`'s branch order rung for rung, and
  `charge_document` folds variable-definition defaults into the per-operation map with a
  supplied variable winning. Decision 6's two colors both route through `_raw_list_bound`, the
  `KeyError`-beside-`TypeError` fallback is there, and `bounded_rows`'s own docstring makes
  the accepted-coordinate-not-rows-scanned promise the spec now makes. Decision 10's `trusted
  is True`, `validate_trusted_flag` at the same construction line as
  `validate_collection_bound` (`list_field.py:1118` / `:1119`), and `narrowed()` building the
  candidate before comparing are all as described. Decision 9's deadline domain is `None` or
  a finite positive number with `bool` refused and a hostile comparison classified out of the
  domain, which is `_is_valid_deadline` exactly.
- **The bounds table reconciles 20/20, independently re-measured.** An `ast` parse of
  `ResourcePolicy`'s `AnnAssign` defaults differenced against the table's parsed rows:
  20 fields, 20 rows, none in code without a row, none in a row without the code, and no
  value mismatch other than the two byte bounds the table renders as `10 MiB` / `25 MiB` for
  `10 * 1024 * 1024` / `25 * 1024 * 1024`. Both re-worded rows describe the shipped behavior:
  `max_list_rows`'s coordinate-and-returned-row wording matches `bounded_rows`'s docstring
  verbatim in substance, and `max_scalar_bytes`'s text-or-bytes-like wording matches
  `_ValueBudget._charge_leaf`'s two branches (`len(value.encode("utf-8", …))` for `str`,
  `getattr(value, "nbytes", len(value))` for `bytes` / `bytearray` / `memoryview`).
- **Both counts re-derive, and the unit is stated where they are published.** Instrument 1,
  `grep -cE '^(async )?def test'` over the `HEAD` extraction: **117** package, **56** live —
  matching. Instrument 2, my own `ast` parse (written independently of the one the authoring
  report describes) counting module-level `test*` functions and multiplying stacked
  `@pytest.mark.parametrize` argvalues cardinalities: **117 → 185** package, **56 → 56** live,
  `unresolved_parametrize = 0` on both, and **0 class-based test methods** in either file, so
  neither instrument is blind to a `Test*` class. The Test plan defines a row as one test
  function at the point of publication, names the node-id expansion beside it, and frames both
  as floors — which is the only durable form for a population another cycle is extending.
- **Decision 13's arithmetic re-counted by enumeration.** The section's bolded entries are
  three `Not this layer —` boundaries and two `Audited exclusion —` boundaries; the opener's
  "five boundaries … Three … two" matches the members, not a decrement.
- **The three spot-checked Test-plan additions all have real rows.** The variable-default pair
  (`::test_variable_default_value_in_operation_header_is_rejected_when_omitted` and
  `::…_ignored_when_overridden`), all five bind-spec relation rows the new live bullet
  describes, and the package tier's `bounded_rows_async` shapes, trusted-flag rows, non-`str`
  query row, delimiter-family rows and pickle row. The two O-7 corrections check out: the
  node-id rows are `_at_the_bound_` and `_over_the_bound_` with no "under" row, and the two
  connection-shape rows are exactly as re-worded — one asserts `charged == 10_100`, the other
  asserts no rejection at a `max_collection_cost=50` a real connection page would exceed. The
  O-6 correction checks out too: both malformed rows are in the live file, and
  `tests/test_resource_policy.py`'s module docstring says the pair "lives in the live suite".
- **The citation sweep the hooks cannot run.** All **26** `path::Symbol` citations in the spec
  resolve by `ast` parse of the extraction (not grep, so a name that appears only in a comment
  or docstring cannot pass); the single `path #"substring"` citation
  (`extensions/resource_policy.py #"_STRUCTURAL_DELIMITER_PAIRS: tuple"`) matches **exactly
  one** source line; the three bare `::Symbol` continuation forms (`::_nested_specs_map`,
  `::_DocumentBudget`, `::derive_keyset_window_bounds`) all resolve against the modules their
  sentences name.
- **The declarations hold.** No new boundary, so no failability proof is owed and the artifact
  says so rather than inventing entries; no executable code, so the hot-path declaration of
  `none` is correct by construction; no framework seam, so floor-verification `none` is
  correct and no floor venv was built. No `pytest` was run in this pass, with or without a
  coverage flag.

### Temp test verification

None created. `docs/builder/temp-tests/047/` was not used: every question this review raised
was answerable by reading the `HEAD` extraction or by a read-only `git` / `ast` measurement,
and the round ships no behavior a temp test could exercise. Disposition: nothing to promote.

### Notes for Worker 1 (spec reconciliation)

1. **The Medium is one sentence and it is yours to write.** This round has no Worker 2, so
   `revision-needed` routes back to a Worker 1 corrective authoring pass. Decision 7's last
   sentence in "The offset window narrows through the same seam" is the whole of it.
2. **The two items the prior pass could not close are recorded accurately and are genuinely
   out of scope.** Verified both: `docs/SPECS/appx/spec-047-resource_policy-0_0_14-terms.csv`
   line 30 reads `Joint version cut,joint-version-cut,the rule this card is NOT subject to`,
   which both documents now contradict, and the file is not in this cohort's partition;
   `check_spec_glossary.py` compares term and anchor only, so it passed at `OK: 34 terms` with
   that cell false. And `clear_resource_context` is defined at
   `resource_policy.py::clear_resource_context`, is entry 10 of that module's 16-name
   `__all__`, and its only callers anywhere in the tree are
   `tests/test_resource_policy.py`'s import and one call — a contract-level retirement
   question, correctly the maintainer's. Neither was touched.
3. **Escalated: the Slice-1 delta row's new names** (Low, above). The choice between "this row
   lists Slice 1's delta" and "this row lists the module's current surface" is a spec-shape
   call, not a fact. Resolution paths: (a) move `bounded_rows_async` /
   `validate_trusted_flag` out of the Slice 1 row into a surface note beside the shared-modules
   note; (b) re-label the cell as the module's delivered surface, which is what its sixteen
   names already are; (c) leave it and accept that the Slice checklist home reads differently.
4. **`## Current state` really is observation-only.** Re-read clause by clause against
   [`BUILD.md`][build]'s "observations stand, predictions do not" rule: four
   "shipped before this card" bullets and one "not shipped, and what this card adds"
   paragraph, all dated observations of the pre-build repo, none a completion claim. The
   pass's decision to leave it is right.
5. **The register's two soft figures** (the `48` and the "four sites") are both Low and both
   inherited from the build plan rather than authored here. Worth fixing in the same pass as
   the Medium, since the round's own lesson is that a number republished without re-derivation
   is how the first one rotted.

### Review outcome

`revision-needed`. One Medium — Decision 7 names `utils/connections.py::assert_relay_pagination_bound`
as the owner of an over-cap rejection the offset window does not route through it — and seven
Low findings, none of which has a recorded rejection reason. The Medium is the round's own
defect class (a decision citing a seam that does not hold at `HEAD`) reproduced in the
decision that carried the citation which started the round, so it is not waved through. The
work is otherwise sound: no history leaked into the spec, every other re-written statement
re-derives at `d727a256`, both published counts re-derive under two instruments with the unit
stated, all 26 spec citations and every link and anchor in both files resolve, and the bounds
table reconciles 20/20.

---

## Authoring report (Worker 1, pass 2)

Corrective authoring pass. This round has no Worker 2, so `revision-needed` routed back to
Worker 1. Grading surface: `HEAD` = `d727a256` at the start and at the end of this pass —
unchanged from the pass Worker 3 reviewed. Every source claim below was read from a
read-only `git archive HEAD | tar -x` extraction in the session scratchpad. No `git stash` /
`checkout --` / `restore` / `worktree` was run.

### Files touched

- `docs/SPECS/spec-047-resource_policy-0_0_14.md` — the Medium plus four of the Lows.
- `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` — three register
  corrections.
- `docs/builder/bld-047-reconcile.md` — this section and the `Status:` line only. No prior
  entry was edited ([`ARTIFACT.md`][artifact] `## Re-pass sections`).
- `docs/builder/worker-memory/047-worker-1.md` — one appended entry.

**Byte counts, this pass.**

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-047-resource_policy-0_0_14.md` | 78,775 | 80,550 | +1,775 |
| `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` | 40,070 | 40,726 | +656 |

Cumulative across both passes: spec 63,529 → 80,550; rationale 19,262 → 40,726.

### Mid-flight correction carried into this pass

**The build plan seeded two of the findings, and Worker 0 corrected the plan before this
pass ran** (recorded here per `worker-0.md` "Mid-flight instructions are mirrored into the
artifact"). Both rows of
[`docs/builder/build-047-resource_policy-0_0_14.md`][build-047]'s post-release register now
carry the corrected facts and state what they previously claimed:

- the `03538f36` row previously read "shared by both window derivations";
- the `ddd5dbb9` / `841e56d6` row previously read "four sites (two sync, two async)".

So the two `### Dispatched findings checklist` boxes that quote those rows — **R-1** and
**R-9** — quote the plan text as it stood at planning. They are prior entries and were not
edited; the corrected plan rows are what this pass discharged them against, and the
rationale register now states the corrected facts. Both were re-derived here from source
rather than carried from either version of the plan.

### Findings discharged

**Medium — Decision 7 named an over-cap owner the offset window does not use.** Fixed in
the spec. Re-derived at `d727a256` before writing: an `ast` walk resolving every
`assert_relay_pagination_bound` call to its enclosing symbol returns exactly two, both
keyset — `utils/connections.py::derive_keyset_window_bounds` and
`connection.py::_resolve_keyset_connection`.
`utils/connections.py::derive_connection_window_bounds` does not call it; it calls
`SliceMetadata.from_arguments` on the line after `resolve_relay_max_results(info,
max_results)`. The helper's own docstring says it is the spelling "the keyset fork cannot run
through `SliceMetadata.from_arguments`" and names those same two consumers. The paragraph was
not deleted — its surrounding claim (the policy ceiling reaches the offset window through
`resolve_relay_max_results`) is true and load-bearing, and was independently re-confirmed.
The replacement states the mechanism the code has: two forks, two sources of the rejection,
parity by message-mirroring, and the maintenance consequence (a message change must be made
in both places). The sentence that named one owner is gone.

**Low — the register's "four sites (two sync, two async)".** Fixed in the rationale.
`grep -nE 'bounded_rows(_async)?\(' django_strawberry_framework/types/resolvers.py` returns
**five** lines — `bounded_rows` at three and `bounded_rows_async` at two. The row now states
five with the unit ("call sites in `types/resolvers.py`") and carries the command that
produces it.

**Low — the register's `48` did not re-derive from the population it named.** Fixed in the
rationale. Re-measured: the population is **seventeen** package modules — the sixteen
distinct package `.py` paths in the Implementation plan table plus `forms/resolvers.py` from
Decision 13 — and `git rev-list --count 567cc6d0..d727a256 -- <those seventeen>` is **62**.
The register now names both the size and the composition of the population beside the figure.
Instrument note: the first run of that command returned `0` because the path list was held in
a plain zsh variable, which does not word-split — `START.md` "Instruments that lie". It was
re-run with a shell array and the per-path counts printed (they sum to 62 only because no
commit in the range touches two of the seventeen; the range count, not the sum, is the
figure). The other two figures re-derive unchanged: `git rev-list --count 567cc6d0..d727a256`
is **312**, and the table carries **19** commits in **15** rows.

**Low — the Implementation plan's Slice 1 row claimed two post-release symbols as slice
deltas.** Fixed in the spec, taking Worker 3's resolution path (a). Verified first:
`git show 567cc6d0:django_strawberry_framework/resource_policy.py | grep -c` returns `0` for
both `validate_trusted_flag` and `bounded_rows_async`, and `5` for `DST_RESOURCE_DEADLINE`,
which therefore stays in the row. Both names moved out of the `Delta` cell into a new surface
note beside the `**Shared modules this surface consumes rather than owns**` note, each tied
to the decision that owns it. The arithmetic now closes: the Slice 1 cell names 14 of
`resource_policy.py`'s `__all__` entries, the note names the other 2, and the module's
`__all__` is 16 (re-counted this pass by `ast`). The `## Slice checklist` home was left
untouched and the two homes no longer disagree.

**Low — one Test-plan clause claimed more than its row asserts.** Fixed in the spec. Read the
row: `tests/test_resource_policy.py` #"assert DST_RESOURCE_POLICY not in context" starts from
an empty `context = {}` and asserts absence after the scan rejects — the restore-to-cleared
half. The hand-back half is pinned by
`::test_nested_sync_schema_restores_the_outer_policy_and_deadline` and its async twin, both on
the non-rejecting path. The clause is now split, naming which path pins which half.

**Low — Decision 3 stated a transport guarantee the source denies.** Fixed in the spec.
`extensions/resource_policy.py::scan_document_text`'s docstring: "The transports that
type-check the query before the extension runs (both HTTP views) make this unreachable there;
the WebSocket path performs no such check, so the decline is the scanner's own contract rather
than a transport's favor." The spec now says the same thing.

**Low — a count with no stated population in a sentence this pass rewrote.** Fixed in the
spec. Measured rather than assumed: `list_field.py::_validate_djangotype_target` raises
`ConfigurationError` at exactly four points — target is not a class, does not subclass
`DjangoType`, its definition is not the one the registry holds for it, and a supplied resolver
is not callable. The figure was right; the population was unnamed. Decision 6 now names the
four by content and cites the symbol that runs them, per `START.md` "Cite contract by CONTENT,
never ordinal".

### Findings intentionally rejected, with the reason

**Low — two internal figures in this artifact's `## Plan (Worker 1)` section.** Both
**rejected as edits**, recorded here instead.

- The rule forbids it. [`ARTIFACT.md`][artifact] `## Re-pass sections`: "never edit prior
  entries", and this pass's dispatch repeats it. `### Implementation steps` and
  `### Dispatched findings checklist` are the prior pass's record.
- Neither figure reaches a shipped document, which Worker 3 also observed.
- The corrections, for the record: `### Implementation steps` step 19 says the register
  carries "the 21 commits"; it carries **19** (the build plan's 21 was a `91c2d880`
  measurement). And R-6's citation of `a8f31a2d` "(iv) and (vi)" is **not** an error — it
  quotes the build plan verbatim, whose own sub-item labels for that commit run
  (i)(ii)(iii)(iv)(vi)(vii), skipping (v); the rationale renumbers them contiguously (i)–(vi).
  Worker 3's recommendation was to leave the checklist quotations as the plan stated them, and
  that is what happened.

### Carried items — left open on purpose, both now homed

1. **`docs/SPECS/appx/spec-047-resource_policy-0_0_14-terms.csv`'s `Joint version cut` note.**
   Still reads `the rule this card is NOT subject to`, which both documents contradict. Out of
   this cohort's writable set and deliberately untouched. **Owner: board card
   `TODO-ALPHA-056-0.0.17` ("Alpha documentation-debt discharge")**, which carries an explicit
   ruling item — `KANBAN.md` #"contract text that needs a gate or scratch that must stop
   asserting statuses" — on whether that column is contract text needing a gate. The item already
   records that `scripts/check_spec_glossary.py::load_terms` reads `term,anchor` only, which is
   why this cell passed a green gate. Homed rather than orphaned, per `START.md` "Item routed
   forward w/o NAMED owner dies".
2. **`clear_resource_context` is a public export with no package caller.** Whether to retire it
   is contract-level — it is on the module's `__all__` — and therefore the maintainer's, not a
   worker's ([`BUILD.md`][build] `### Contract-level findings are escalated as maintainer
   decisions before dispatch`). Recorded as fact in the rationale; not a defect against the
   spec as it now reads.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-047-resource_policy-0_0_14.md`
  — **pass**, `OK: 34 terms`, exit 0. Unchanged across this pass, so no term lost its only
  link.
- `uv run python scripts/check_trailing_commas.py --check <the three markdown paths>` —
  **pass**, exit 0 (the artifact reports itself excluded from the source-layout rules).
  Explicit paths only; this script's bare default is a repo-wide auto-fix that would rewrite
  the concurrent session's files.
- **In-page anchors**, re-derived to GitHub slugs from each file's own headings: spec
  **14 distinct, 0 dangling** (13 before this pass; the new Implementation-plan surface note
  adds a Decision 10 link); rationale **3 distinct, 0 dangling**; artifact **0**.
- **Reference-style links**, all three files, every `][label]` use against every definition:
  spec **40 / 40**, rationale **17 / 17**, artifact **4 / 4**; 0 undefined and 0 unused in
  each. All three bottom blocks carry the 10 canonical group headers in the `START.md` order
  (compared against the ordered list, not spot-checked). Every definition path resolves on
  disk **from its own file's directory** — the rationale's climb two levels out of
  `docs/SPECS/appx/`.
- **Cross-file `#anchor` fragments** re-slugged against the target file's real headings:
  spec **34, 0 dangling**; rationale **14, 0 dangling** (the `[spec-047-d*]` family into the
  spec, and the glossary anchors).
- **Citations, re-swept whole-file rather than only over the lines this pass touched.**
  Resolution by `ast` parse of the `HEAD` extraction, never by grep, so a name appearing only
  in a comment or docstring cannot pass. Spec: **36 backtick-delimited `path::Symbol`
  citations, 0 unresolved** — the unit is the regex's population, which counts the dotted
  `path::Class.method` form as one citation, so it is a wider count than the prior pass's 26
  and not a disagreement with it. One `path #"substring"` citation
  (`extensions/resource_policy.py #"_STRUCTURAL_DELIMITER_PAIRS: tuple"`), matching **exactly
  one** source line. Rationale: **11 qualified citations, 3 unresolved**, all expected — two
  spellings of `connection.py::_resolve_connection_fast_path` and one of
  `forms/resolvers.py::_run_plain_form_pipeline_sync`, each marked "no longer exists at any
  current revision" beside the `git show <death commit>^:<path>` pointer that reaches it. The
  four symbols this pass newly cites or re-cites all resolve:
  `utils/connections.py::assert_relay_pagination_bound`, `::derive_keyset_window_bounds`,
  `connection.py::_resolve_keyset_connection`,
  `list_field.py::_validate_djangotype_target`. `scripts/check_citations.py` does not gate
  `docs/` prose, so this sweep is the substitute for the missing gate.
- `git status --short` — **clean of anything this cohort does not own.** Modified:
  `docs/SPECS/spec-047-resource_policy-0_0_14.md`,
  `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`. Untracked:
  `docs/builder/bld-047-reconcile.md` and `docs/builder/build-047-resource_policy-0_0_14.md`
  (Worker 0's plan, not this pass's output). The memory file is under a `.gitignore`d path.
  **Eleven further paths are dirty, all the concurrent spec-050 session's, and the set GREW
  while this pass ran** — reported, never reverted (`AGENTS.md` rule 34). At the start of the
  pass it was six: `django_strawberry_framework/list_field.py`,
  `django_strawberry_framework/resource_policy.py`, `tests/test_list_field.py`,
  `tests/test_resource_policy.py`,
  `examples/fakeshop/test_query/test_list_field_api.py`, and one maintainer review input. At
  the end it is eleven, adding `tests/test_connection.py`,
  `examples/fakeshop/test_query/test_list_field_async_api.py`,
  `examples/fakeshop/test_query/README.md`, `docs/spec-050-list_field_arguments-0_0_15.md` and
  `docs/builder/build-050-list_field_arguments-0_0_15.md` — every one of them a file this
  cohort's partition explicitly excludes, and the last two the concurrent cycle's own spec and
  plan. **This pass edited none of them at any point**, ran no write-mode tool over them, and
  reverted nothing. The growth is visible here rather than silent because the dispatch's
  clean-`git status` expectation is what it falsifies: the expectation was written against a
  six-path baseline that the concurrent cycle has since moved.
- **No `.py` file was touched**, so `ruff` had nothing in scope; a repo-wide write-mode run
  would rewrite the concurrent session's files. No `pytest` was run in this pass, with or
  without a coverage flag.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none. No floor venv was built.

### Implementation notes

- **The Medium's replacement is longer than what it replaced, on purpose.** The false sentence
  was short because it asserted a single owner; the true arrangement is two mechanisms held to
  one vocabulary, and a reader who is only told "they agree" cannot maintain it. The paragraph
  therefore states where each fork's rejection comes from and what a message change costs. That
  is contract, not chronology: no commit, no "previously", nothing a reader must date.
- **The Slice 1 repair was a move, not a deletion.** Finding G's obligation — that the spec name
  the three public symbols it never listed — is still discharged; the two post-release names
  simply sit in a surface note instead of in a column whose header says `Delta`. The note states
  a present-tense fact about the module's `__all__` and cites the decisions that own each name,
  so it carries no chronology.
- **Every number this pass wrote was measured as it was written, and each names its
  population**: five `bounded_rows` / `bounded_rows_async` call sites in one named file; 62
  commits over a seventeen-module population whose composition is stated; four guards in one
  named symbol, enumerated by content rather than counted; 16 `__all__` entries split 14 + 2
  between the row and the note.
- **No claim was carried from the build plan.** The plan's corrected rows and this pass's
  independent re-derivation agree, which is recorded as agreement rather than treated as one
  measurement.

### Notes for Worker 3

- **Re-derive the Medium from source, not from this report.** The instrument that settles it is
  an `ast` resolution of every `assert_relay_pagination_bound` call to its enclosing symbol; a
  bare `grep` returns the import line and the definition line too, which is how the claim reads
  as broader than it is.
- **Four counts are published in this diff**, each with its population named: five call sites
  (`types/resolvers.py`), 62 commits (the seventeen named modules), four constructor-site guards
  (`list_field.py::_validate_djangotype_target`), 16 `__all__` entries split 14 + 2. The
  Test plan's two row figures and Decision 13's five/two are unchanged from the pass you already
  re-derived.
- **Two Lows were rejected rather than fixed**, both in `## Plan (Worker 1)`, because editing a
  prior entry is forbidden. The corrections are recorded above; step 19's "21" should read 19,
  and R-6's "(iv) and (vi)" is a faithful quotation of the build plan and is not an error.
- **The one thing no hook checks** is still the citation sweep over `docs/` prose. It was re-run
  whole-file this pass rather than over the touched lines, because a paragraph rewrite can strand
  a citation two paragraphs away.

### Notes for Worker 1 (spec reconciliation)

Carried into final verification:

1. Both carried items above are homed and neither is closable by a worker. Item 1's owner is
   `TODO-ALPHA-056-0.0.17`; item 2 is a maintainer contract call.
2. The rationale's `#### Public symbols the spec did not name` heading is a past-tense register
   observation and stays accurate as such: the spec now names all of those symbols, which is
   what the register's own entries record. Left alone deliberately — re-tensing it would make
   the register narrate this round instead of the post-release change it exists to describe.
3. `## Current state` was left alone again, for the reason the prior pass recorded and Worker 3
   re-verified clause by clause.


---

## Review (Worker 3, pass 2)

Fresh reviewer; did not write the pass-1 review and did not write the prose graded here.
Reading surface: a read-only `git archive HEAD | tar -x` extraction at `d727a256`, byte
identity with `git show HEAD:<path>` re-proved by `shasum` for every package file quoted
below. `HEAD` was `d727a256` at the start and at the end of this pass — unchanged from the
pass under review. No `git stash` / `checkout --` / `restore` / `worktree` was run, and no
`.py` file was read in the working tree.

Every figure below was re-derived from source at `HEAD` rather than read out of the pass-2
report. Where the report names an instrument, a second independent one was run beside it.

### High:

None.

### Medium:

None.

**The pass-1 Medium is discharged, and every clause of its replacement re-derives.** Decision 7
`docs/SPECS/spec-047-resource_policy-0_0_14.md:618-629` now makes five separate factual claims;
all five were measured, not read:

1. *The offset fork takes its over-cap error from `SliceMetadata.from_arguments`.* An `ast` walk
   resolving every call in `utils/connections.py` and `connection.py` to its enclosing symbol
   returns exactly one `SliceMetadata.from_arguments` invocation in the whole package —
   `utils/connections.py::derive_connection_window_bounds`, at line 662.
2. *Which `derive_connection_window_bounds` calls immediately after resolving the cap.* Literal:
   `resolve_relay_max_results` at `utils/connections.py:661`, `SliceMetadata.from_arguments` at
   `:662`, consecutive statements.
3. *The keyset fork routes every over-cap check through `assert_relay_pagination_bound` at two
   sites.* The same `ast` walk returns exactly two calls, both keyset —
   `utils/connections.py::derive_keyset_window_bounds` (`:795`) and
   `connection.py::_resolve_keyset_connection` (`:1009`). Neither keyset site calls
   `from_arguments`; a text grep adds only the import and the definition, which is the noise the
   pass-2 note warned about and is why the resolution was done by `ast`.
4. *Parity rests on message-mirroring.* This was the new factual claim the fix introduced and it
   is the one I graded hardest. `utils/connections.py::assert_relay_pagination_bound` raises
   `ValueError(f"Argument '{argument}' must be a non-negative integer.")` and
   `ValueError(f"Argument '{argument}' cannot be higher than {cap}.")`. Strawberry's
   `strawberry/relay/utils.py:153,157,163,167` raises
   `ValueError("Argument 'first' must be a non-negative integer.")` and
   `ValueError(f"Argument 'first' cannot be higher than {max_results}.")`, and the `'last'`
   twins. Same exception class, same two texts character for character once `argument` and `cap`
   are bound, and the helper's `if not isinstance(value, int): return` reproduces
   `SliceMetadata`'s own `isinstance(..., int)` gate. "Exactly" holds. The parity is additionally
   pinned in the tree by `tests/utils/test_connections.py::test_assert_relay_pagination_bound_matches_slice_metadata_text`,
   which matches both literal strings — so a message drift on either side has a row that fails.
5. *"A keyset cursor is not an offset, so that engine cannot be run over one."* The helper's own
   docstring gives that as its reason for existing and names the same two consumers.

The paragraph also states a maintenance consequence (a message change must be made in both
places) that follows from 4 and is not a separate claim. No chronology, no commit, nothing a
reader must date. Both surviving statements of this fact — the spec at `:618` and the rationale's
`03538f36` register row — were swept and they agree; there is no third, stale copy.

### Low:

#### The register's `19` counts four commits its own table says bear on nothing

`docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` — the scope-and-method paragraph
says **19** of the 62 "change what the contract says", and names the table below as those 19. The
table's last row is `4c483b6b`, `d3b91c8d`, `9a9f970c`, `4d98ad98` — "spec-050 review fixes and
scaffolding; `_close_async_iterator` gained a `caller` label" — whose **Bears on** cell is `—`.
By the register's own key, four of the 19 bear on no part of this contract, so either the figure
is 15 or the criterion is wider than "change what the contract says".

Verified the row is legitimately inside the 62: all four commits touch `list_field.py`,
`resource_policy.py` or `connection.py`, which are in the seventeen-module population
(`git show --stat <sha> -- django_strawberry_framework/`). So the row belongs in the population;
what does not follow is its membership in the narrower figure.

This is pass-1 text, not pass-2's, and it is a scope-wording call on a document only Worker 1 may
edit. Recommended change is Worker 1's pick between: say "19 are read against the contract, four
of them to record that they changed nothing in it", or drop the four-commit row to 15 and account
for the remaining four in the 62 sentence. No test expectation; no behavior.

#### The pass-2 report's own link-definition figure for this artifact is off by one

`### Validation run` reports "artifact **4 / 4**" reference-style links. Re-measured:
`docs/builder/bld-047-reconcile.md` carries **5** definitions (`[spec-047]`,
`[spec-047-rationale]`, `[artifact]`, `[build]`, `[build-047]`) and **5** distinct uses, 0
undefined and 0 unused. `[artifact]` is the one the pass added for its own `ARTIFACT.md`
citations, which is almost certainly when the count was taken. Nothing is broken — every link
resolves, and the figure reaches no shipped document — but the round's standing lesson is that a
number republished without re-derivation is how the first defect got here, and this one is in the
same pass that wrote the lesson down.

**Disposition: recorded, not edited.** `ARTIFACT.md` `## Re-pass sections` forbids editing a
prior entry, and `## Authoring report (Worker 1, pass 2)` is one. The correction stands here:
the artifact's figure is 5 / 5, not 4 / 4. Same disposition pass 2 itself took for the two plan
figures, and graded as right below.

### The two intentionally-rejected Lows: disposition correct, corrections accurate

**Rejecting them as edits is right.** `### Implementation steps` step 19 and
`### Dispatched findings checklist` R-6 both live in `## Plan (Worker 1)`, a prior entry.
`ARTIFACT.md` `## Re-pass sections` says "never edit prior entries" without a carve-out, neither
figure reaches a shipped document, and the artifact is the linear record of what each pass
believed. Recording the correction in the pass that found it is the shape the contract wants.

**Correction 1 — step 19's "21 commits" should read 19 — is accurate.** Parsed the rationale's
register table: 15 rows carrying 19 backticked shas, 19 distinct. Every one is in range
(`git merge-base --is-ancestor 567cc6d0 <sha>` and `<sha> d727a256` both exit 0 for all 19). The
build plan's own `## Post-release change register` prose says "21 touch the spec-047 surface"
while its own table carries the same 19 in the same 15 rows, so `21` is falsified by the plan
against itself — which is what the pass-2 report says.

**Correction 2 — R-6's "(iv) and (vi)" is a faithful quotation, not an error — is also
accurate, and I checked the plan rather than the claim.**
`docs/builder/build-047-resource_policy-0_0_14.md:256` labels the `a8f31a2d` row
`(i) (ii) (iii) (iv) (vi) (vii)` — it skips `(v)`. The rationale's own `a8f31a2d` row renumbers
contiguously `(i)`-`(vi)`, so the same two sub-items are `(iv)` and `(v)` there. R-6 quotes the
plan, which is the contract the checklist box is written against; leaving it is correct and
changing it would have made the box stop quoting its source.

### Whole-document integrity, re-run over both files end to end

Not a spot-check of the touched lines: every instrument below ran over the whole file, because a
paragraph rewrite strands citations and anchors elsewhere.

- **In-page anchors**, re-slugged from each file's own headings under the GitHub rules in
  `START.md`: spec **37 headings, 37 distinct slugs (no collisions), 22 anchor uses over 14
  distinct, 0 dangling**; rationale **30 / 30, 12 uses over 3 distinct, 0 dangling**; artifact
  0 in-page uses (its 8 duplicate heading slugs are the mandated re-pass shape and nothing
  targets them).
- **Reference-style links**, every `][label]` against every definition: spec **81 uses / 40
  distinct / 40 definitions**, rationale **50 / 17 / 17**, artifact **15 / 5 / 5** — 0 undefined
  and 0 unused in all three.
- **The 10 canonical group headers** compared against `START.md`'s ordered list as a sequence,
  not spot-checked: present and in order in all three bottom blocks.
- **Relative paths resolved from each file's own directory**, including the rationale's climb two
  levels out of `docs/SPECS/appx/`: every definition path exists on disk.
- **Cross-file `#anchor` fragments** re-slugged against the target file's real headings: spec
  **34, 0 dangling**; rationale **14, 0 dangling**.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-047-resource_policy-0_0_14.md`
  → `OK: 34 terms`, **exit 0**.
- `uv run python scripts/check_trailing_commas.py --check <the three markdown paths>` → exit 0
  (explicit paths only — this script's bare default is a repo-wide auto-fix that would rewrite
  the concurrent session's files).

### Citations re-verified, whole-file

`scripts/check_citations.py` does not gate `docs/` prose, so this sweep is the substitute.
Resolution by `ast` parse of the `HEAD` extraction, never by grep, so a name appearing only in a
comment or docstring cannot pass.

- **Spec: 36 backtick-delimited `path::Symbol` citations (28 distinct), 0 unresolved.** The
  36 reconciles with pass 1's 26 as the pass-2 report says — the wider regex counts the dotted
  `path::Class.method` form and repeated citations of the same symbol. Cross-checked that the
  backticked population is the whole population: an unanchored sweep for `*.py::Symbol` anywhere
  in the file also returns 36, so no citation lives outside a code span.
- **One `path #"substring"` citation**, `extensions/resource_policy.py #"_STRUCTURAL_DELIMITER_PAIRS: tuple"`,
  matching **exactly one** source line (`:103`).
- **Rationale: 11 qualified citations (10 distinct), 3 occurrences unresolved, all expected** —
  two of `connection.py::_resolve_connection_fast_path`, one of
  `forms/resolvers.py::_run_plain_form_pipeline_sync`. **The pointers hold**, which is what makes
  them legal rather than rot: `git show de2601e9^:django_strawberry_framework/connection.py`
  carries the first (4 hits) and `git show 6013cda6^:django_strawberry_framework/forms/resolvers.py`
  the second (2 hits). The third dead-artifact pointer holds too —
  `docs/builder/bld-047-remediation.md` is absent at `HEAD` (`git cat-file -e` fails) and
  `git show 99696bac^:<path>` returns 5,262 bytes.
- **The four symbols this pass newly cites all resolve**:
  `utils/connections.py::assert_relay_pagination_bound`, `::derive_keyset_window_bounds`,
  `connection.py::_resolve_keyset_connection`, `list_field.py::_validate_djangotype_target`.

### Every count pass 2 changed, re-derived

Each measured with an instrument chosen independently of the one the report names.

- **Five `bounded_rows` / `bounded_rows_async` call sites in `types/resolvers.py`, three sync and
  two async.** Two instruments agree. `grep -nE 'bounded_rows(_async)?\('` returns `:426 :431
  :565 :580 :584`. An `ast` walk resolving each call to its enclosing symbol returns
  `_visible_many_rows._resolve` (async), `_visible_many_rows` (sync),
  `_make_relation_resolver.many_resolver` (sync), `...many_resolver._resolve` (async),
  `...many_resolver` (sync) — 3 sync, 2 async, 5 total. The register now states the number with
  its unit and its command, which is the repair the Low asked for. The spec's own prose beside it
  ("the prefetched path and the manager path, in both colors") publishes no figure and is
  accurate against those five branches, so the two files do not now disagree.
- **62 over a seventeen-module population.** Re-derived the population from the spec rather than
  from the report: the Implementation plan table names **16** distinct package `.py` paths, plus
  `forms/resolvers.py` from Decision 13 = **17**. With the paths in a shell **array**,
  `git rev-list --count 567cc6d0..d727a256 -- "${P[@]}"` is **62**, and
  `git rev-list --count 567cc6d0..d727a256` is **312**. Both figures and the composition
  re-derive. (The report's note about a plain zsh variable returning `0` reproduces: that is the
  instrument-lies trap, and naming it beside the figure is correct.)
- **16 `__all__` entries, split 14 + 2.** `ast` parse of `resource_policy.py`'s `__all__`: 16
  names. Parsed the Slice 1 `Delta` cell mechanically for backticked identifiers: **14**, all 16
  accounted for, and the exact set difference is `{bounded_rows_async, validate_trusted_flag}` —
  precisely the two the new surface note carries. The partition is exact and disjoint, with no
  name in the row that is not in `__all__`. The release-era check holds too:
  `git show 567cc6d0:...resource_policy.py | grep -c` is `0` for both moved names and `5` for
  `DST_RESOURCE_DEADLINE`, which correctly stayed in the row.
- **Four constructor-site guards**, now named by content rather than counted.
  `list_field.py::_validate_djangotype_target` raises `ConfigurationError` at exactly four points
  (`:139`, `:143`, `:158`, `:163`) and they are, in order, the four the spec now enumerates: the
  target is a class, it subclasses `DjangoType`, its definition is the one the registry holds for
  it, and a supplied resolver is callable. Co-location holds — `validate_collection_bound`
  (`:1118`), `validate_trusted_flag` (`:1119`) and `_validate_djangotype_target` (`:1124`) are all
  inside the same `DjangoListField` constructor.
- **The counts pass 2 did not change were re-derived anyway**, because a count can rot under an
  edit elsewhere. Test rows, two instruments each: `grep -cE '^(async )?def test'` gives **117**
  package / **56** live; an independent `ast` parse multiplying stacked `parametrize` argvalues
  gives **117 → 185** and **56 → 56**, with `unresolved_parametrize = 0` and **0 `Test*` classes**
  in either file, so neither instrument is blind to a class-based row. Bounds table: an `ast`
  diff of `ResourcePolicy`'s `AnnAssign` defaults against the parsed table rows gives **20 fields,
  20 rows**, no field without a row, no row without a field, and the only value differences are
  the two `10 MiB` / `25 MiB` renderings of `10 * 1024 * 1024` / `25 * 1024 * 1024`. Decision 13:
  three `Not this layer —` plus two `Audited exclusion —` members = the five its opener claims.

### No history leaked into the spec

Polarity sweep over the whole spec for `previously`, `as of`, `no longer`, `used to`, `formerly`,
`at the release`, `post-release`, `since the release`, `now (returns|narrows|is|reads|does|says|actually)`,
`remediation round`, `review round`, `reconcil`, `amendment`, `retract`, `originally`,
`earlier version`, `has since`, `changed meaning`, `this round`, `this pass`, `before this card`,
`was measured`, `historically`, `at the time` returns **four** lines, and all four are the same
pre-existing set pass 1 cleared: `:149` `## Current state`'s dated pre-build observation, `:540` a
contract sentence ("opting in no longer opts out of the cap"), `:792` Decision 12's one-line
`[rationale]` pointer — the single licensed form — and `:892` a slice delta naming a docstring.
Nothing pass 2 wrote is on that list. No amendment block: a heading sweep for
`amend|change record|correction|revision|errata|history|update log` over the spec returns zero,
and the spec's 33 section headings are the same contract shape as before. The register, the
chronology and the commit shas stay in the rationale, where they belong.

### The five homes still agree

Pass 2 touched Decision 3, Decision 6, Decision 7, the Implementation plan and the Test plan.
Walked each of the five homes for every one of those:

- **Decision 7 (over-cap).** No `## Edge cases` entry touches the over-cap owner; the Test plan's
  connection rows assert refusal, not error ownership; `## Definition of done` says "the
  connection cap seam"; `## Slice checklist` Slice 3 says "the policy ceiling over
  `relay_max_results`". A whole-file sweep for `assert_relay_pagination_bound|SliceMetadata|
  over-cap|one owner` returns exactly one statement in the spec and one in the rationale, and
  they agree. No stale second copy anywhere.
- **Decision 6 / the Slice 1 move.** This was the home most at risk, because the pass moved two
  names between two homes. The `## Slice checklist` Slice 1 entry names `ResourcePolicy`,
  `DEFAULT_RESOURCE_POLICY`, `ResourceLimitExceeded`, `resolve_resource_policy`, the context
  helpers, `effective_bound`, `bounded_rows`, `check_deadline` — and **not**
  `bounded_rows_async` or `validate_trusted_flag`. That is now consistent with the Implementation
  plan row, which is the disagreement pass 1 found and pass 2 closed. `## Definition of done`'s
  `DjangoListField` item ("a narrowing `max_rows` and an explicit trusted widening; a non-positive
  value fails at construction") matches Decision 6's rewritten constructor sentence. The bounds
  table's `max_list_rows` row ("rows a raw (non-Relay) list field returns and ... the skip
  coordinate it accepts") matches Decision 6's coordinate-and-result ceiling.
- **Decision 3 (non-`str` decline).** `## Definition of done` charges tokens and depth before the
  parse; the Test plan carries "on a non-`str` query it declines rather than lexes"; no Edge case
  contradicts. The rewritten clause now matches
  `extensions/resource_policy.py::scan_document_text`'s docstring in substance — both HTTP views
  type-check, the WebSocket path does not, the decline is the scanner's own contract.
- **The Test-plan split.** Read the three rows rather than the claim.
  `tests/test_resource_policy.py::test_the_context_is_cleared_even_when_the_document_scan_rejects`
  starts from `context = {}` and asserts `DST_RESOURCE_POLICY not in context` after the scan
  raises — the restore-to-cleared half, exactly as the split now says.
  `::test_nested_sync_schema_restores_the_outer_policy_and_deadline` (`:405`) and its async twin
  (`:439`) are the hand-back half on the non-rejecting path. The clause no longer claims more
  than its rows assert.
- **Findings G / K / L / O-8 survived the pass-2 edits.** Re-checked that every public symbol the
  round undertook to name is still named in the spec after the Slice 1 move:
  `bounded_rows_async` (4), `validate_trusted_flag` (3), `DST_RESOURCE_DEADLINE` (2),
  `__reduce__` (1), `detail` (2), `MISSING` (1), `restored_context_keys` (1), `resolve_policy`
  (1), `RELATION_MULTI` (2), `coded_error_extensions` (2). The move relocated, it did not drop.
- **`clear_resource_context`'s one surviving spec mention is the Slice 1 `Delta` cell**, which is
  a true statement about what Slice 1 landed and is load-bearing for the 14 + 2 = 16 arithmetic.
  Decision 2 no longer describes it as part of the operation lifecycle, which is finding O-1's
  contract.

### Both carried items are recorded accurately, with live owners

Neither was touched, and neither is closable by a worker. Verified both rather than accepting the
record:

1. **The terms-CSV `notes` cell.** `docs/SPECS/appx/spec-047-resource_policy-0_0_14-terms.csv`
   line 30 reads `Joint version cut,joint-version-cut,the rule this card is NOT subject to`,
   which Decision 12 now contradicts directly ("Under the joint version cut rule the release
   wording belongs to the **last** card of a shared line to land"). `git status --short` on that
   path is empty — untouched, and outside the cohort's partition. The named owner is live:
   `TODO-ALPHA-056-0.0.17` appears on `KANBAN.md` in the index row and as a card heading, and the
   artifact's citation `KANBAN.md #"contract text that needs a gate or scratch that must stop
   asserting statuses"` matches **exactly one** line (`KANBAN.md:615`), whose body does carry the
   ruling item and does record that `check_spec_glossary.py::load_terms` reads `term,anchor` only.
   That is why the gate passed green over a false cell, and it is why `OK: 34 terms` above is not
   evidence about this cell.
2. **`clear_resource_context`.** `grep -rn --include='*.py'` over the `HEAD` extraction returns
   four lines: its definition (`resource_policy.py:407`), its `__all__` entry (`:75`), and an
   import plus one call in `tests/test_resource_policy.py`. Zero package callers, on the module's
   public surface — a contract-level retirement question and correctly the maintainer's. Recorded
   as fact in the rationale, and not asserted as a defect against the spec as it now reads.

### DRY findings

- **No duplication introduced by the pass-2 edits.** The Medium's replacement paragraph states the
  mechanism once in the spec; the rationale's `03538f36` row states the chronology once. The
  Implementation plan's new surface note does not restate the shared-modules note beside it — one
  names modules the surface consumes, the other names two symbols the surface owns that no slice
  row carries. Different content, adjacent placement, no near-copy.
- **The Slice 1 repair was a move, and I verified it as one**, per the relocation-claim rule: the
  two names are absent from the `Delta` cell and present in the note, `__all__` is still fully
  covered at 14 + 2, and the `## Slice checklist` home was genuinely left alone (it never named
  them).
- **The two re-written DRY obligations still state rules, not exception lists**, and still hold
  after this pass. Obligation 3's claim that `effective_bound` and
  `extensions/resource_policy.py::_page_bound` are the two narrowing sites re-checks; obligation
  5's `_ValueBudget._reject`-plus-different-rule framing re-checks. Obligation 4
  (`resolve_relay_max_results` is the only connection-cap resolution, shared by the plan-time and
  resolve-time halves) is the one Decision 7's rewrite could have falsified, so I re-derived it:
  four call sites (`derive_connection_window_bounds`, `derive_keyset_window_bounds`,
  `DjangoConnection.resolve_connection`, `_resolve_keyset_connection`), and the plan-time walker
  reaches the same seam through `optimizer/nested_planner.py:851` / `:913` calling
  `derive_connection_window_bounds`. The body ends `return effective_bound(policy_from_info(info).max_page_size, cap)`,
  which is the `min(...)` Decision 7 opens with. Unfalsified.
- **Existence challenge: none raised.** The pass authored no helper, constant, registry or
  indirection layer. `clear_resource_context` remains the one live existence question and it is
  already routed to the maintainer as a contract-level call; raising it again here would be
  re-litigating a settled routing.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — zero lines. `__all__` and
the re-export list are untouched. Independently: the cohort's own paths in `git status --short`
are exactly `docs/SPECS/spec-047-resource_policy-0_0_14.md`,
`docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`, and the two untracked
`docs/builder/` files — no `.py` among them. The two names the pass moved
(`bounded_rows_async`, `validate_trusted_flag`) are entries in `resource_policy.py`'s own
`__all__` (re-counted by `ast`: **16**), and neither is a root package export, so the note added
to the Implementation plan pins nothing new on `__init__.py`.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applicable — the cohort is documentation-only.

- **Version strings and card ids.** `__version__` at `d727a256` is `0.0.15`; the spec asserts the
  current version nowhere, and states the version fact in the date-independent form ("The version
  quintet reached `0.0.14` ahead of this card's first slice"), so finding C stays discharged.
  Every card id cited in the spec resolves on the board: `DONE-047-0.0.14` (3 hits),
  `DONE-048-0.0.14` (2), `DONE-049-0.0.14` (2), `TODO-ALPHA-051-0.0.15` (9). The S-1 prefix flip
  holds — no `WIP-ALPHA-049` spelling survives anywhere in the spec.
- **The decoy stayed a decoy.** `TODO-BETA-047-0.1.2` in
  `examples/fakeshop/apps/products/schema.py` and `docs/SPECS/spec-060-search_fields-0_1_2.md` is
  untouched; neither path appears in `git status --short`.
- **No staging language.** `TODO(spec-047` and `TODO-ALPHA-047` return nothing in either file.
- **Concurrent-session files, reported not touched.** The dirty set has grown again since the
  pass-2 report: **14 tracked modified paths plus 2 untracked**, where that report recorded 11
  plus 2. The new ones (`tests/test_connection.py` was already there; now also
  `docs/builder/bld-final.md`, a maintainer review input, and
  `docs/builder/build-050-list_field_arguments-0_0_15.md` moved from untracked to modified) are
  the concurrent spec-050 session's. **This review read the two documents it grades in the working
  tree and every `.py` file from the `HEAD` extraction; it wrote to this artifact and nothing
  else**, ran no write-mode tool over any path, and reverted nothing (`AGENTS.md` rule 34). The
  growth is reported here because a dispatch-time `git status` expectation that the pass did not
  falsify is worth distinguishing from one it did.
- **`scripts/review_inspect.py` skipped, with reason.** The round adds no `.py` file, touches no
  file under `optimizer/` or `types/`, and adds zero lines of logic — `BUILD.md`
  `### When to run the helper during build` triggers on none of its three Worker-3 conditions.
  Every source claim above was read from the `HEAD` extraction directly.

### What looks solid

- **The Medium was fixed by stating the mechanism, not by deleting the sentence.** The surrounding
  claim that survived (the policy ceiling reaches the offset window through
  `resolve_relay_max_results`) is true and load-bearing, and the replacement is longer because the
  true arrangement is two mechanisms held to one vocabulary. A reader who acts on the new
  paragraph will find every call it names.
- **The new claim the fix introduced was the right one to introduce, and it is independently
  pinned.** Message-mirroring is the kind of parity that rots silently — but the tree already
  carries a row asserting both literal strings, so the spec is describing a guarantee the suite
  defends rather than an observation someone made once.
- **Every repaired count now carries its population or its unit**, which is the repair the Lows
  asked for and not merely a corrected digit: five call sites *in a named file*, 62 commits over a
  *stated seventeen-module composition*, four guards *enumerated by content* rather than counted,
  16 `__all__` entries *split 14 + 2* so the arithmetic closes visibly.
- **The pass reports its own instrument failure.** The zsh-variable word-splitting note beside the
  62 is the instrument-lies discipline applied to the pass's own work, which is the hard half.
- **Nothing elsewhere was falsified by the corrections**, which was the re-review's real job: the
  five homes agree, all 36 spec citations and every link and anchor in both files still resolve,
  the bounds table still reconciles 20/20, both test counts still re-derive under two instruments,
  and the four DRY obligations survive Decision 7's rewrite.
- **The declarations hold and the artifact says so rather than inventing entries.** No new
  boundary, so no failability proof is owed (`### Failability proofs` reads
  "None; this pass introduced no new boundary."); no executable code, so the hot-path declaration
  of `none` is correct by construction; no framework seam, so floor-verification `none` is correct
  and no floor venv was built. No `pytest` was run in this pass, with or without a coverage flag,
  and no repo-wide write-mode `ruff` or `check_trailing_commas` invocation was made.

### Temp test verification

None created. `docs/builder/temp-tests/047/` was not used: every question this re-review raised
was answerable by reading the `HEAD` extraction or by a read-only `git` / `ast` measurement, and
the round ships no behavior a temp test could exercise. Disposition: nothing to promote.

### Notes for Worker 1 (spec reconciliation)

1. **Escalated: the register's `19`** (Low, above). Whether that figure means "changed the
   contract" or "were read against the contract" is a scope-wording call on a document only
   Worker 1 may edit, not a fact. Resolution paths: (a) widen the sentence to say four of the 19
   are recorded as changing nothing in this contract; (b) narrow the figure to 15 and account for
   the four in the 62 sentence; (c) leave it and accept that one row's `Bears on` cell reads
   against the figure's stated criterion. Nothing downstream depends on the number.
2. **The artifact's own link figure is 5 / 5, not 4 / 4** (Low, above). Correction recorded here
   rather than edited into the prior entry, for the same reason pass 2 gave. Nothing to fix in a
   shipped document.
3. **Both carried items are homed on live owners and were verified, not accepted.** Item 1's owner
   card and its exact ruling bullet exist on the board; item 2's zero-package-caller claim
   re-derives at `HEAD`. Neither is closable by a worker and neither was touched.
4. **The rationale's `#### Public symbols the spec did not name` heading.** I reached the same
   conclusion the pass did, independently: it is a register observation of the population found,
   the spec now names all ten of those symbols (verified above), and re-tensing it would make the
   register narrate this round rather than the post-release change it exists to describe. Leave it.
5. **`## Current state` re-read once more and it is still observation-only.** Four dated
   "shipped before this card" bullets and one "not shipped, and what this card adds" paragraph,
   no completion claim. Leaving it was right both times.

### Review outcome

`review-accepted`. The pass-1 Medium is discharged and every clause of its replacement — including
the new message-parity claim the fix introduced, which I graded character-for-character against
Strawberry's own source — re-derives at `d727a256`. All seven Lows are discharged or rejected with
a correct and verified reason; the two rejections are the right disposition and both recorded
corrections check out against the build plan. Every count the pass published was re-derived from
source, most under a second instrument, and each now carries its population or its unit. No history
leaked into the spec, the five homes agree on every statement the pass moved, and all 36 spec
citations, both files' links and anchors, the 20/20 bounds table and both test counts still hold
after the edits.

Two Lows are raised here and neither blocks: the register's `19` counts four commits its own table
says bear on nothing (escalated to Worker 1, who owns the document), and the pass-2 report's
self-reported link figure for this artifact is 5 / 5 rather than 4 / 4 (recorded, not edited —
prior entries are not editable). Neither reaches a shipped document and neither falsifies anything
a reader would act on.

---

## Final verification (Worker 1)

Fresh spawn; final-verification pass after Worker 3 set `review-accepted` on pass 2. Grading
surface: `HEAD` = `d727a256`, unchanged from both reviewed passes — `git rev-parse --short HEAD`
at the start and at the end of this pass. Every source claim below was read from a read-only
`git archive HEAD | tar -x` extraction in the session scratchpad whose byte identity with
`git show HEAD:<path>` was proved by `shasum` for each of the five package files quoted. No
`git stash` / `checkout --` / `restore` / `worktree` was run, and nothing outside this cohort's
four writable paths was written.

### Dispatched findings checklist audit

**34 boxes, all `- [x]`, all confirmed against the diff. No over-tick, no un-ticked box, so no
deferral reason is owed for any of them.** The audit instrument was the checklist parsed
mechanically (`34` ticked, `0` open) and then each box read against
`git diff -U2 --` over the two owned documents, rather than against either report's account of
what it did. Grouped by where the contract landed:

- **A, B, O-5** — Decision 9's seam list is re-enumerated to the four `check_deadline` sites and
  the one write skeleton; `connection.py::_resolve_connection_fast_path` is gone from the spec
  and `connection.py::DjangoConnection.resolve_connection` stands in both Decisions 7 and 9;
  Decision 13's falsified audited exclusion is deleted and its opener reads five / two.
- **C, S-1** — the version fact is stated date-independently in the Version-boundary preamble
  and in Decision 12; `WIP-ALPHA-049-0.0.14` → `DONE-049-0.0.14` at both of its sites.
- **D, E** — the `[spec-047-d13]` definition now targets
  `#decision-13--what-this-policy-does-not-bound-and-why-each-boundary-is-deliberate` and
  resolves (re-slugged this pass); the deleted per-cycle artifact is cited exactly once, and
  that one occurrence is inside the `git show 99696bac^:…` pointer rather than as a live path.
- **F, G, K, O-8, R-7, R-9** — Decision 6 states the two-colored seam and the shared
  `resource_policy.py::_raw_list_bound`; the Implementation plan names `bounded_rows_async`,
  `validate_trusted_flag` and `DST_RESOURCE_DEADLINE`, and adds the shared-modules note for
  `utils/policies.py::resolve_policy`, `utils/errors.py::coded_error_extensions` and
  `utils/inputs.py::RELATION_MULTI`.
- **H, I, J, O-1, O-2, R-3, R-4, R-5, R-6, R-8** — the fourth value source, the bytes-like
  scalar, the snapshot-and-restore, the bind-spec ladder, the sixth unmeasurable spelling, the
  delimiter table and the non-`str` decline, the finiteness domain, the fail-closed hostile
  stash and the `KeyError` fallback, and the exact-`True` widening test are each present in the
  decision the checklist assigns them to.
- **L, R-2, R-10** — `detail` / `__reduce__` in the rejection section; the truthiness and
  `coded_error_extensions` clauses in Decision 11; the two re-worded bounds rows.
- **M** — discharged by non-action: `git status --short` carries neither
  `examples/fakeshop/apps/products/schema.py` nor `docs/SPECS/spec-060-search_fields-0_1_2.md`.
- **N, O-3, O-4, O-6, O-7** — both counts published as floors with the unit defined at the point
  of publication; both DRY obligations state a rule rather than an absolute; the malformed pair
  sits in the live tier; the two overstated assertion claims are narrowed.
- **R-1, R-11** — Decision 7's offset-window narrowing and the corrected over-cap paragraph; the
  register written into the rationale's `## Change record`.

`## Review-round custody`'s extra final-verification check: **each builder's on-disk
required-amendment list was discharged.** This round had one builder (Worker 1 itself, under the
plan's declared dispatch shape), so the list is the two `### Notes for Worker 1 (spec
reconciliation)` blocks. Every item in them is either implemented in the diff, decided and
recorded, or carried with a named owner in `bld-047-final.md`'s `### Deferred work catalog`.

### Worker 3's two pass-2 Lows, both escalated here

**Low 1 — the register's `19` counted four commits its own table says bear on nothing.
Discharged by fixing the criterion and the figure, in the rationale.** The arithmetic was never
wrong; the stated criterion did not fit four of the members. Re-derived as it was written, by
parsing the register's own table rather than by reading either report:

- the table carries **15 rows** and **19 backticked shas, 19 distinct**;
- **one** row — `4c483b6b`, `d3b91c8d`, `9a9f970c`, `4d98ad98` — has an empty **Bears on** cell,
  and it carries **4** of the 19;
- the other **14** rows carry the other **15**.

Population named: the 19 are the commits in `567cc6d0..d727a256` that were read against this
contract, drawn from the **62** that touch the **seventeen** package modules the spec names (the
16 distinct package `.py` paths in its Implementation plan table plus `forms/resolvers.py` from
Decision 13). Both surrounding figures re-derive independently this pass:
`git rev-list --count 567cc6d0..HEAD` is **312**; with the seventeen paths in a shell **array**
(never a plain variable — `START.md` "Instruments that lie"),
`git rev-list --count 567cc6d0..HEAD -- "${P[@]}"` is **62**, and all seventeen exist on disk.
All 19 shas were re-confirmed in range: `git merge-base --is-ancestor 567cc6d0 <sha>` and
`<sha> HEAD` both exit 0 for every one. The four were confirmed to belong in the 62 rather than
to be strays — `git show --stat <sha> -- django_strawberry_framework/` shows each touching
`list_field.py`, `resource_policy.py` or `connection.py`.

The choice among the three paths Worker 3 offered was **(a), widened criterion**, not (b),
dropping the row to 15. Dropping it would delete the one measurement in the register that says
what did **not** change on a surface the register is otherwise a list of changes to — the same
thing `#### What did NOT change, measured rather than assumed` exists to preserve one heading
further down. The scope-and-method paragraph now says the 19 were **read against** the contract,
states the **15 / 4** split with the rows each occupies, says why the four are carried, and
names the empty **Bears on** cell as the finding rather than an unfinished entry. It also moves
"the figure that matters" from the 19 to the **15**, since that is now the one a later reader
should re-derive.

**Low 2 — the pass-2 report's self-reported artifact link count reads "4 / 4" where it is
5 / 5. Correction recorded here, not edited.** `ARTIFACT.md` `## Re-pass sections` forbids
editing a prior entry and `## Authoring report (Worker 1, pass 2)` is one; this is the same
disposition pass 2 took for the two plan figures and pass 2's reviewer took for this one.
Re-measured independently this pass over the whole file with fenced blocks stripped:
`docs/builder/bld-047-reconcile.md` carries **5** reference-style definitions — `[spec-047]`,
`[spec-047-rationale]`, `[artifact]`, `[build]`, `[build-047]` — and **5** distinct real uses,
0 undefined and 0 unused. **For the record: the figure is 5 / 5.** Nothing is broken and the
figure reaches no shipped document. One instrument note worth carrying: a naive `\]\[(...)\]`
sweep over this artifact also matches the literal `][label]` that its own validation prose
writes when describing the check, so the raw regex reports a sixth, undefined label. The
population is 5; the sixth is the artifact describing the instrument, not using it.

### No fail-open shape, and no relocation or promotion claim to prove

**This round moved no code, so both checks are answered by measurement rather than left blank.**
`git diff --name-only` over the cohort's own paths yields exactly
`docs/SPECS/spec-047-resource_policy-0_0_14.md` and
`docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` — no `.py` file among them, and
`git diff -- django_strawberry_framework/__init__.py` is empty.

- **Fail-open shapes.** None can have landed: a fail-open shape is an expression in executable
  code, and this cohort added, removed and changed zero lines of it. The prose *describing*
  fail-open behavior was read for the inverse defect — a spec sentence that describes a guard as
  permissive where the code fails closed — and all three such sentences state the closed answer:
  Decision 9's "a stashed value whose own comparison raises … takes the rejection path", Edge
  cases' six unmeasurable-upload spellings all "*rejected*, not charged as zero bytes", and
  Decision 10's `trusted is True`. Each matches the source at `HEAD`.
- **Relocation / promotion claims.** The one relocation claim in this cycle is internal to the
  documents — pass 2 moved `bounded_rows_async` and `validate_trusted_flag` out of the
  Implementation plan's Slice 1 `Delta` cell into a surface note. Re-proved here as a move, not
  a drop: `resource_policy.py`'s `__all__` parses to **16** names at `HEAD`; the Slice 1 cell
  names **14** of them; the surface note names the other **2**; the set difference is exactly
  `{bounded_rows_async, validate_trusted_flag}`, and no name appears in both or in neither. No
  code body was relocated, promoted, or carried over, so `## Claims are proven mechanically`'s
  token-identity procedure has no subject this round.

### Spec status-line re-verification

Performed per `worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)` and
**no edit is owed**:

- Title and target line (`:1`, `:3`) — `Targeted at 0.0.14 (card DONE-047-0.0.14)`. The board
  carries `DONE-047-0.0.14` (3 occurrences in `KANBAN.md`), so the card id and lifecycle agree.
- Predecessor / sibling line (`:7-9`) — `spec-046` exists at `docs/SPECS/`; `DONE-048-0.0.14`
  (2 hits) and `DONE-049-0.0.14` (2 hits) both resolve on the board, the second being the S-1
  repair. No predecessor doc this build deleted is referenced.
- `Status:` line (`:26`) — "**SHIPPED — all five slices are built and released.**" Still true
  and not falsified by this round, which shipped no slice and changed no source.
- Companion pointer (`:11-12`) — the rationale file exists at the path given.
- A staleness sweep over both files for `not yet shipped`, `remains to be`, `will ship`,
  `is in flight` and `WIP-ALPHA` returns **one** line, the rationale's own record that
  `WIP-ALPHA-049-0.0.14` was retired — a register entry about the repair, not a live claim.

### DRY check across this cohort and the prior passes

No new duplication. This pass wrote one paragraph, in one file, and both halves of the
"is there a second copy?" question were measured rather than assumed:

- **The retired criterion has no surviving site.** `grep -c 'change what the contract says'`
  returns **1** in the rationale — the scope paragraph this pass rewrote — and **0** in the
  spec. There is no second statement of the figure to fall out of step with it.
- **The commit chronology still lives only in the rationale.** `grep -oE '\b[0-9a-f]{8}\b'` over
  the spec returns **zero** matches of any kind, backticked or bare, so the spec carries no sha
  at all. That is the division the round was dispatched to hold, and this pass did not erode it.

### Existing tests

**None run, deliberately, and the absence is not a pass.** The plan's
`## Final-gate exception, recorded in advance` governs; `docs/builder/bld-047-final.md` records
which commands were not run, why, and who owes them. The plan's declarations are all `none`
(ownership partition single-cohort, hot path none, floor-verification scope none), and each is
correct by construction for a cohort that edits no executable code.

### Staged-anchor sweep

`grep -rEn 'TODO\(spec-047|TODO-(ALPHA|BETA|STABLE)-047' .` over the tree, excluding
`KANBAN.md` / `KANBAN.html` / `BACKLOG.md` where a board id is legitimate:

- `TODO(spec-047` — **2** hits, both inside this artifact's own prose *describing* the sweep.
- `TODO-ALPHA-047` / `TODO-BETA-047` bare — **3** hits, all likewise this artifact's prose.
- `TODO-BETA-047-0.1.2` — **16** hits in `docs/SPECS/spec-020-list_field-0_0_7.md`,
  `docs/SPECS/appx/spec-020-list_field-0_0_7-rationale.md`,
  `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md`,
  `docs/SPECS/spec-060-search_fields-0_1_2.md` and
  `examples/fakeshop/apps/products/schema.py`. This is the decoy the plan pre-empted: the old
  numbering of a different, unshipped **search** card, not a staged anchor for card 047's work.
  It has a live named owner and is re-verified as owned below.

**Neither owned file carries a staged anchor** (`grep -cE` returns 0 in both). Nothing this
build shipped left an anchor behind, because this build shipped no source.

### Summary

The round reconciled `docs/SPECS/spec-047-resource_policy-0_0_14.md` and its rationale companion
with what actually shipped and with the post-release change the spec had never recorded. Across
two authoring passes and two reviews it discharged all 34 dispatched findings, one Medium and
nine Low review findings, and it opened no code cohort — the bounds table reconciles 20/20, every
Implementation-plan symbol resolves at `HEAD` except one a later refactor deleted while keeping
its behavior, and no spec-named test is missing, so nothing the spec planned was skipped in the
code. The spec grew 63,529 → 80,550 bytes and the rationale 19,262 → 41,243, all of it contract
in the spec and all of it chronology in the rationale. This pass added the last of it: the
register's scope criterion now fits its own membership.

### Spec changes made (Worker 1 only)

- `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` lines 167-185, the post-release
  register's **Scope and method** paragraph. Triggered by Worker 3's pass-2 Low escalated to
  final verification: the paragraph claimed 19 commits "change what the contract says" while its
  own table's last row carries four with an empty **Bears on** cell. Reason: the register must
  be self-consistent about what its own figure counts. The criterion is widened to "read against
  this contract", the **15 / 4** split is stated with the rows each occupies, the empty
  **Bears on** cell is named as the finding rather than an omission, and the figure a later
  reader should re-derive moves from the 19 to the 15. Every figure in the paragraph — 312, 62,
  seventeen, 19, 15, 14 rows, 4 — was re-measured while this sentence was being written.
  Rationale 40,726 → 41,243 bytes (+517).
- No change to `docs/SPECS/spec-047-resource_policy-0_0_14.md`. Final verification found nothing
  in it to reconcile; its status and header lines are current and its 36 citations, 14 in-page
  anchors and 40 reference links all resolve at `HEAD`.

### Final verification gates run

| Gate | Result |
|---|---|
| `check_spec_glossary.py --spec docs/SPECS/spec-047-resource_policy-0_0_14.md` | `OK: 34 terms`, exit 0 |
| `check_trailing_commas.py --check <the two files by explicit path>` | exit 0 |
| `git diff --check -- <the two files>` | clean, exit 0 |
| In-page anchors, re-slugged from each file's own headings | spec 37 headings / 37 distinct slugs / 22 uses over 14 distinct, **0 dangling**; rationale 30 / 30 / 12 over 3, **0 dangling** |
| Reference-style links | spec **40 / 40**, rationale **17 / 17**; 0 undefined, 0 unused; every definition path resolves on disk from its own file's directory |
| 10 canonical group headers | present and in `START.md` order in both bottom blocks, compared as a sequence |
| Cross-file `#anchor` fragments | spec **34, 0 dangling**; rationale **14, 0 dangling** |
| `path::Symbol` citations, resolved by `ast` against the `HEAD` extraction | spec **36 / 36 resolve**; rationale **11 citations, 3 unresolved, all three expected** and each carrying a working `git show <death commit>^:<path>` pointer (4, 2 and 5,262 bytes respectively) |
| `path #"substring"` citations | spec 1, matching **exactly one** source line; rationale 0 |
| `git status --short` | this cohort owns exactly the 2 modified spec files plus 2 untracked `docs/builder/` files; 12 further dirty paths are the concurrent spec-050 session's, untouched and unreverted |

### Final status

`final-accepted`.

---

## Authoring report (Worker 1, pass 3)

Round 2 authoring pass, dispatched from the build plan's `## Round 2: HEAD moved past the gate`
for findings **P** and **Q**. Grading surface: `HEAD` = `63a132be` at the start and at the end of
this pass (`git rev-parse --short HEAD`, both times). Every source claim below was read from a
read-only `git archive HEAD | tar -x` extraction in the session scratchpad, byte identity with
`git show HEAD:<path>` proved by `shasum` for `tests/test_resource_policy.py`,
`examples/fakeshop/test_query/test_resource_policy_api.py`,
`django_strawberry_framework/resource_policy.py` and `django_strawberry_framework/list_field.py`
before any instrument ran. No `git stash` / `checkout --` / `restore` / `worktree` was run, and
nothing outside this cohort's four writable paths was written. No prior section of this artifact
was edited; this section and the `Status:` line are the whole of the change here.

### Dispatched findings checklist (pass 3)

- [x] **P-1 — Decision 6, the `max_list_rows is a coordinate-and-result ceiling` paragraph.**
      `#"The seam accepts `offset` and `requested_limit` client coordinates"` is gone. The
      paragraph now states the `63a132be` contract: the exported
      `resource_policy.py::bounded_rows` / `::bounded_rows_async` carry no client window
      (`def bounded_rows(result, info, declared=None, *, trusted=False)`); the coordinate pair
      lives on the package-private `::_windowed_rows` / `::_windowed_rows_async`, which
      `list_field.py` calls directly; the exported pair delegates windowless;
      `::_raw_list_bound` is the one place any of the four derives a limit;
      `list_field.py::_normalize_list_arguments` is the sole owner of the ceiling check and its
      typed, argument-named rejection. spec-047's ownership claim kept (the ceiling is 047's; the
      arguments and their rejection are 050's). Vocabulary aligned with spec-050 Decision 5
      ("coordinate-bearing seam is package-private", "the body ... run, not a second bound")
      without copying its paragraph.
- [x] **P-2 — `## Helper-reuse obligations (DRY)`, the `bounded_rows` / `bounded_rows_async`
      row.** True at `HEAD` by stating what each rule governs: the exported pair governs what a
      direct caller can get, the private pair governs what a validated window can get,
      `_raw_list_bound` governs the limit both are held to. No exception appended.
- [x] **P-3 — `## Test plan`, the `bounded_rows_async pinned separately` sentence.** Each
      scenario now sits on the function that receives it, attributed by an `ast` map of every
      test function to the seam names it calls (see `### Verification run`): the exported pair's
      refusal row `tests/test_resource_policy.py::test_the_exported_raw_list_bound_takes_no_client_window`
      (both colors × both coordinates); `bounded_rows_async` keeps "the iterator closed after the
      effective prefix" and "a cleanup failure that must not mask the source error"; "a zero
      window that never advances the source" and "offset arithmetic" move to
      `_windowed_rows` / `_windowed_rows_async`, which are the only functions any `offset=` /
      `requested_limit=` call in that file targets.
- [x] **P-3 floor — package-tier floor raised `117 rows / 185 node ids` → `120 / 191`.**
      Measured myself, two instruments, at `63a132be`. Decided to raise rather than leave: the
      rewritten sentence names the refusal row, and that row is one of the three `63a132be`
      added — a floor left at 117 would predate the row published beside it.
- [x] **P-4 — sweep of the rest of the spec** (`grep -nE 'offset|requested_limit|window|skip'`),
      every hit graded. The bounds-table `max_list_rows` cell stays (the ceiling is unchanged;
      only the receiving function moved); the Decision 7 / Decision 13 `window` hits are
      connection-window arithmetic, unrelated; the `@skip` hits are directive prose. **One
      further site the grep vocabulary cannot see, found by reading:** Decision 6's opener said
      "Both are shared by the root `DjangoListField` and by the generated many-side relation
      resolver", and "both colors call it" of `_raw_list_bound`. At `HEAD` `list_field.py` calls
      `_windowed_rows` / `_windowed_rows_async` directly and never the exported names; both
      sentences now say so ("enters the same seam one level down"; "every function on the seam
      reaches it").
- [x] **Q-1 — register row `63a132be`** added to `### The post-release change register` in the
      table's column shape, placed before the four-commit last row so the "last row changes
      nothing" sentence stays true. Content: (i) the coordinates off the export onto the private
      pair, `_raw_list_bound` unchanged, `_normalize_list_arguments` owns the check, and the claim
      the spec may no longer make; (ii) `_attach_cleanup_note` / `_is_cleanup_diagnostic`, an
      `Exception` demoted to a `__notes__` entry, a `BaseException` such as
      `asyncio.CancelledError` propagating from both async cleanup seams, spec-050 Decisions 5
      and 8 owning that text and spec-047's test-plan phrase staying true. Class `correction`
      (the `aadca5a2` precedent: a spec-050 commit that changed what an 047 primitive does).
      Bears on D6, DRY, Test plan.
- [x] **Q-2 — register criterion and counts re-derived after the row landed.** 313 / 63 /
      seventeen / 20 read / 16 rows / "Sixteen of them, in the table's first 15 rows" / four in
      the last row / "the **16** is the figure that matters". The two other `d727a256` vintage
      stamps in the file (`## How to read this file`, `## Provenance of this record`) moved to
      `63a132be` with the figure they carry, so the register names one revision.
- [x] **Q-3 — `### Decision 6` narrative.** The history paragraph stays; one successor sentence
      added (`63a132be` moved the coordinates below the export) and the sha named in the commit
      list, which now closes with "the three claims the decision may no longer make" — the
      third being the new `#### Claims the spec may no longer make` bullet for "The seam accepts
      `offset` and `requested_limit` client coordinates".
- [x] **Q-4 — row `89ee8ac5` untouched.** `git diff` over the rationale shows no hunk on it.

### Files touched

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-047-resource_policy-0_0_14.md` | 80,550 | 82,445 | +1,895 |
| `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` | 41,243 | 43,172 | +1,929 |
| `docs/builder/bld-047-reconcile.md` | 126,243 | 142,968 | this section + `Status:` |
| `docs/builder/worker-memory/047-worker-1.md` | 6,468 | 8,129 | one appended entry |

Cumulative across the round: spec 63,529 → 82,445; rationale 19,262 → 43,172.

### Spec changes made (Worker 1 only)

One line per change, location cited by a substring that occurs once in the file at the time of
writing.

- Spec, Decision 6 opener, `#"enters the same seam one level down"` — the root list field calls
  the private windowed pair, not the exported names; the opener said both callers shared the
  exported pair. Finding P (site found by reading, outside the grep vocabulary).
- Spec, Decision 6, `#"every function on the seam reaches it and none computes"` — "both colors
  call it" was false of the exported pair at `HEAD`, which reaches `_raw_list_bound` through the
  private pair. Finding P.
- Spec, Decision 6, `#"The exported pair carries no client window"` — the whole
  coordinate-and-result paragraph restated for the `63a132be` contract. Finding P.
- Spec, DRY row, `#"Each rule governs one thing"` — the "only raw-list bound" obligation made
  true by saying what each of the three rules governs. Finding P.
- Spec, Test plan, `#"120 rows / 191 node ids"` — floor raised to the `63a132be` measurement.
  Finding P.
- Spec, Test plan, `#"refusing `offset` and `requested_limit` in both colors"` — each named
  scenario attributed to the function that receives it; the exported pair's refusal row named.
  Finding P.
- Rationale, `## How to read this file`, `#"313 commits of later change"` — vintage stamp moved
  from `d727a256` to `63a132be` with its figure. Finding Q.
- Rationale, `## Provenance of this record`, `#"read against the source at `63a132be`"` — same.
  Finding Q.
- Rationale, `### The post-release change register`, `#"Measured at `63a132be`"` — the scope
  paragraph's 313 / 63 / 20 / 16 rows / 16-and-4 split re-derived. Finding Q.
- Rationale, register table, `#"| `63a132be` |"` — the new row. Finding Q.
- Rationale, `#### Claims the spec may no longer make`, `#"The exported pair accepts neither"` —
  the third Decision 6 retired claim. Finding Q.
- Rationale, `### Decision 6` entry, `#"then moved the coordinates below the export"` — the
  successor sentence and the sha in the commit list. Finding Q.

### Verification run

Every command as run, with the figure it returned.

- `git rev-parse --short HEAD` → `63a132be` at the start; `63a132be` at the end.
- `git archive HEAD | tar -x -C <scratchpad>/head`, then `shasum <scratchpad>/head/<p>` against
  `git show HEAD:<p> | shasum` for the four package / test files named above → `IDENTICAL` ×4.
- `grep -cE '^(async )?def test'` over the extraction →
  `tests/test_resource_policy.py` **120**, `examples/fakeshop/test_query/test_resource_policy_api.py` **56**.
- `ast` parse counting module-level `test*` functions and multiplying every stacked
  `@pytest.mark.parametrize` argvalues cardinality → **120 functions → 191 node ids** package,
  **56 → 56** live, `unresolved_parametrize = 0` and `Test_classes = 0` on both. The two
  instruments agree on the function counts.
- The same `ast` walk mapping each package test function to the seam names it calls
  (`bounded_rows`, `bounded_rows_async`, `_windowed_rows`, `_windowed_rows_async`) → every
  function that passes `offset=` or `requested_limit=` calls only the private pair
  (`::test_bounded_rows_slices_with_offset_and_requested_limit`,
  `::test_bounded_rows_zero_window_does_not_advance_generator`,
  `::test_bounded_rows_async_slices_with_offset_and_requested_limit`,
  `::test_bounded_rows_async_zero_window_closes_without_next`,
  `::test_bounded_rows_async_positive_offset_arithmetic`, the two exact-consumption rows, the
  24-case window matrix); the exported names take a coordinate in exactly one function,
  `::test_the_exported_raw_list_bound_takes_no_client_window` (×4 node ids), which asserts the
  refusal. "Closed after the effective prefix" and "cleanup failure must not mask" call
  `bounded_rows_async` with no window.
- `diff` of the `^(async )?def test` name lists between `git show d727a256:` and `git show HEAD:`
  of the package file → **3 added**: `test_bounded_rows_async_lets_a_cancellation_during_cleanup_reach_the_task`,
  `test_cleanup_rejected_async_iterable_lets_a_cancelled_acquisition_through`,
  `test_the_exported_raw_list_bound_takes_no_client_window`. 117 + 3 = 120; 185 + 1 + 1 + 4 = 191.
- `git rev-list --count 567cc6d0..63a132be` → **313**; with the seventeen module paths in a shell
  **array** (`"${P[@]}"`, population printed as 17, every path present on disk) → **63**; at
  `d727a256` the same two commands give 312 / 62. `git merge-base --is-ancestor 567cc6d0 63a132be`
  → exit 0. `git show --stat 63a132be -- <the seventeen>` → `list_field.py`, `resource_policy.py`.
- Register table parsed mechanically after the edit → **16 rows / 20 backticked shas / 20
  distinct / 1 row with an empty Bears-on cell, carrying 4**; `git merge-base --is-ancestor
  567cc6d0 <sha>` and `<sha> HEAD` exit 0 for all 20.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-047-resource_policy-0_0_14.md`
  → `OK: 34 terms`, exit 0.
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale>` → exit 0;
  re-run with this artifact added after this section was written → see the end of this list.
- `git diff --check -- <spec> <rationale>` → exit 0.
- Citation sweep by `ast` against the extraction (a symbol appearing only in a comment or
  docstring cannot pass): spec **44 `path::Symbol` citations (32 distinct), 0 unresolved** — the
  five this pass added or re-cited (`resource_policy.py::_windowed_rows`,
  `::_windowed_rows_async`, `list_field.py::_normalize_list_arguments`,
  `tests/test_resource_policy.py::test_the_exported_raw_list_bound_takes_no_client_window`,
  `resource_policy.py::_raw_list_bound`) all resolve; spec `#"substring"` citations **1**,
  matching **exactly one** line. Rationale **13 (11 distinct), 3 unresolved, all three
  expected** (two of `connection.py::_resolve_connection_fast_path`, one of
  `forms/resolvers.py::_run_plain_form_pipeline_sync`, each beside its `git show <death
  commit>^:<path>` pointer); the two new `list_field.py::_normalize_list_arguments` citations
  resolve; rationale `#"substring"` citations 0.
- Reference-style links, every `][label]` use (fenced blocks stripped) against every definition:
  spec **40 / 40**, rationale **17 / 17** — `used-but-undefined: none`,
  `defined-but-unused: none` in both; every definition path exists on disk from its own file's
  directory; the 10 canonical group headers present and in `START.md` order in both bottom
  blocks (compared as a sequence); alphabetical within group, 0 violations.
- In-page anchors re-slugged from each file's own headings: spec **14 distinct, 0 dangling**;
  rationale **3, 0 dangling**. Cross-file `#anchor` fragments against the target's headings:
  **0 dangling** in both.
- `grep -cE '\b[0-9a-f]{8}\b'` over the spec → **0**: the spec carries no sha.
- History-leak sweep over the spec (`previously|as of |no longer|used to|formerly|at the
  release|post-release|since the release|has since|changed meaning|this round|this pass|came
  off|moved (the|onto|below)`) → **1** line, `:540` "opting in no longer opts out of the cap",
  the pre-existing contract sentence both prior reviews cleared.
- `git status --short` → this cohort owns exactly the two modified spec files plus the untracked
  `docs/builder/bld-047-reconcile.md`; `docs/builder/build-047-resource_policy-0_0_14.md` and
  `docs/builder/bld-047-final.md` are Worker 0's; `KANBAN.md`, `KANBAN.html` and
  `examples/fakeshop/db.sqlite3` went dirty during this pass — Worker 0's fence-change board
  rows, per the plan's `### Fence change`, not this pass's output; the remaining dirty and
  staged paths are the concurrent spec-050 session's. Nothing outside the four writable paths
  was written; nothing was reverted.
- `ruff` and `pytest` not run: no `.py` file changed.
- After this section was appended: `uv run python scripts/check_trailing_commas.py --check`
  over the spec, the rationale and this artifact → exit 0; this artifact's reference links
  **5 / 5**, `used-but-undefined: none`, `defined-but-unused: none`; `wc -c` gives the last two
  `After` figures in `### Files touched`.

### Notes for Worker 3

- **Re-derive the attribution map from source, not from this report.** The instrument that
  settles P-3 is an `ast` walk mapping each test function in `tests/test_resource_policy.py` to
  the seam names it calls; a text grep for `bounded_rows` also matches the private pair by
  substring and the test names, which all start `test_bounded_rows_...` whichever seam they hit.
- **The floor was raised, deliberately.** 120 / 191 is a `63a132be` reading under two
  instruments. If you measure more, the file grew; if you measure less, `HEAD` moved backwards
  and everything here needs re-grading.
- **One P site is outside the dispatch's grep vocabulary** (Decision 6's opener: who calls the
  exported pair). Grade it against `grep -nE '_windowed_rows|bounded_rows' django_strawberry_framework/list_field.py django_strawberry_framework/types/resolvers.py`:
  `list_field.py` calls only the private pair; `types/resolvers.py` calls only the exported pair.
- **The new register row is classed `correction`, not `later feature`.** The precedent is the
  `aadca5a2` row, also spec-050's, also a change to what an 047 primitive does. If you read the
  class the other way, the disagreement is about the taxonomy's third definition ("a different
  card extending a surface this one owns"), not about the facts in the row.
- **Pre-existing >100-char lines** at spec `:1`, `:293`, `:834`, `:929` and rationale `:1` are
  not this pass's; the one this pass created (Decision 6, `:559`) was rewrapped.
- **`KANBAN.md` / `KANBAN.html` / `db.sqlite3` churn is Worker 0's**, from the fence change in
  the plan. Do not attribute it to this pass; do not revert it.

---

## Review (Worker 3, pass 3)

Fresh reviewer; did not write the pass-3 prose or either prior review. Reading surface: a
read-only `git archive HEAD | tar -x` extraction at `63a132be` under the session scratchpad's
`047/head`, byte identity with `git show HEAD:<path>` proved by `shasum` for
`resource_policy.py`, `list_field.py`, `types/resolvers.py`, `tests/test_resource_policy.py`
and `test_query/test_resource_policy_api.py` (`IDENTICAL` ×5). `HEAD` was `63a132be` at the
start and at the end of this pass. No `git stash` / `checkout --` / `restore` / `worktree` was
run; no `.py` file was read from the working tree. Every figure below was re-derived from source
or from the two documents, never read out of the pass-3 report; where the report names an
instrument, an independently written one was run beside it.

### High:

None.

### Medium:

None.

### Low:

#### Decision 2 carries a build-history narrative that three polarity sweeps never covered

`docs/SPECS/spec-047-resource_policy-0_0_14.md:380-383` (Decision 2):

```docs/SPECS/spec-047-resource_policy-0_0_14.md:380
The shape-agnostic read / write / delete dispatch itself moved to `utils/context.py` and is
now shared by both subsystems. It handled four context shapes (`None`, object, `dict`,
frozen) and was already the single place a new shape would land; a second copy in
`resource_policy.py` would have been the first duplicate of it.
```

"moved to … and is now shared … would have been the first duplicate" is chronology and
deliberation, not contract; the contract form is one sentence ("the shape-agnostic dispatch
lives in `utils/context.py` and is shared by both subsystems"), and the rest is a rationale
entry. **Pre-existing at `HEAD`** (`git show HEAD:<spec> | grep -n 'dispatch itself moved'` →
`:360`), so it is not pass 3's and not a dispatched finding — it is the dispatch's "sweep the
spec for history vocabulary and grade any hit", and it is a hit every sweep in this round
missed because none of the three published polarity lists carried `moved` or `now shared`.
Recommended change: one sentence, contract form, in the spec; the "would have been the first
duplicate" clause to the rationale's Decision 2 entry. No test expectation.

#### The pass-3 report's enumeration of coordinate-passing tests names 8 of 12

`### Verification run`, the `ast` attribution bullet: "every function that passes `offset=` or
`requested_limit=` calls only the private pair (…five names…, the two exact-consumption rows,
the 24-case window matrix)". The **claim is true** — an independent `ast` walk over
`tests/test_resource_policy.py` at `63a132be` finds **12** test functions passing either
keyword, every one to `_windowed_rows` / `_windowed_rows_async` only, and the exported names
receive a coordinate in exactly one function (the refusal row, via a `**{coordinate: 10}`
splat). The parenthetical reads as that population and lists 8: it omits
`::test_bounded_rows_slices_unsliceable_iterable_with_offset_and_requested_limit`,
`::test_bounded_rows_declined_sync_cleanup_resumable`,
`::test_bounded_rows_async_keeps_the_deadline_primary_when_the_close_fails` and
`::test_bounded_rows_shared_policy_seams_spy`. Reaches no shipped document; recorded because
an enumeration presented beside a universal claim is read as its population.

#### The pass-3 report's long-line inventory omits a Decision 6 line this round created

`### Notes for Worker 3` says the pre-existing `>100`-char lines are spec `:1`, `:293`,
`:834`, `:929` and rationale `:1`, and that "the one this pass created (Decision 6, `:559`)
was rewrapped". `awk 'length>100'` over the spec also returns `:560` (**104**, Decision 6
prose: "an async-only iterable cannot be sliced or consumed synchronously — …"), which is
**absent at `HEAD`** (`git show HEAD:<spec> | grep -c 'consumed synchronously'` → 0), plus the
unwrappable table rows `:271`, `:283`, `:893-905`. Whether `:560` is pass 1's or pass 3's
reflow, the inventory is incomplete. `.md` line length is ungated (ruff excludes markdown,
`check_trailing_commas` checks scaffold only), so nothing fails; report-only.

### Every factual claim pass 3 introduced, graded against `63a132be`

- **Signatures.** `ast` of `resource_policy.py`: `bounded_rows(result, info, declared=None, *,
  trusted=False)` (`:545`), `bounded_rows_async(result, info, declared=None, *, trusted=False)`
  (`:764`, async); `_windowed_rows` (`:484`) and `_windowed_rows_async` (`:684`) carry `offset`,
  `requested_limit`, `trusted`. The spec's quoted signature at `:565` is character-exact. Both
  private names are absent from the 16-entry `__all__` (parsed; the 16 are unchanged).
- **Who calls what**, by `ast` resolution of every call to its enclosing symbol (a grep also
  returns the import and the definition):
  `list_field.py` → `_windowed_rows` ×5 (`:960`, `:989`, `:1013`, `:1042` in the two
  `_execute_queryset_pipeline_*` bodies, `:1295` in `DjangoListField._wrap`) and
  `_windowed_rows_async` ×1 (`:1197`, `DjangoListField._resolve_async_iterable`), **never** the
  exported pair; `types/resolvers.py` → `bounded_rows` ×3 (`:431`, `:565`, `:584`) and
  `bounded_rows_async` ×2 (`:426`, `:580`), **never** the private pair. Decision 6's opener
  (relation resolver calls the exported pair; the root list field "enters the same seam one
  level down") and the report's note are both exactly this.
- **`_raw_list_bound` is the only derivation.** Its callers are `_windowed_rows` (`:512`) and
  `_windowed_rows_async` (`:717`) and nothing else; `bounded_rows` (`:579`) and
  `bounded_rows_async` (`:797`) reach it by delegating windowless; `_windowed_rows_async` falls
  back to `_windowed_rows` for a non-async-only iterable (`:708`). "every function on the seam
  reaches it and none computes a limit of its own" holds for all four. The `63a132be` hunk
  begins at `def bounded_rows` → `def _windowed_rows`; `_raw_list_bound`'s body is context, not
  change, so "unchanged as the single derivation" holds.
- **Coordinates never bypass the normalizer.** All four `list_field.py` coordinate-bearing
  calls pass `offset=args_record.offset, requested_limit=args_record.limit`, and `args_record`
  is the return of `_normalize_list_arguments` (`list_field.py:719`, its only call site).
  `grep -rn over_ceiling django_strawberry_framework/` hits `list_field.py` only (`:73`,
  `:244`, `:458`, `:487`); `_normalize_list_arguments` checks the offset against
  `policy.max_list_rows` (`:437`, `:454`) and the limit against
  `effective_bound(policy.max_list_rows, …)` (`:464`, `:483`). "Sole owner of the ceiling
  check" and the bounds-table cell's "skip coordinate it accepts" both hold. The one other
  `max_list_rows` read outside the module, `extensions/resource_policy.py:800`, is the
  document walk's collection charge, not a coordinate check.
- **The refusal row.** `tests/test_resource_policy.py:625-652`: stacked
  `parametrize("color", ["sync","async"])` × `parametrize("coordinate", ["offset",
  "requested_limit"])` = **4 node ids**; each arm `pytest.raises(TypeError)` on the exported
  name with the coordinate, then asserts the windowless call returns `[0, 1]` under
  `max_list_rows=2`. "Both colors × both coordinates, `TypeError` from the signature" is exact.
- **Test-plan attribution, by `ast` map.** "closed after the effective prefix" →
  `::test_bounded_rows_async_closes_after_the_effective_prefix` calls `bounded_rows_async`, no
  window; "cleanup failure that must not mask" →
  `::test_bounded_rows_async_preserves_source_errors_when_cleanup_fails`, same; "zero window
  that never advances" → `::test_bounded_rows_zero_window_does_not_advance_generator`
  (`_windowed_rows`) and `::test_bounded_rows_async_zero_window_closes_without_next`
  (`_windowed_rows_async`); "offset arithmetic" →
  `::test_bounded_rows_async_positive_offset_arithmetic` (`_windowed_rows_async`); "on a
  non-subscriptable iterable and under a trusted widening" →
  `::test_bounded_rows_bounds_a_non_subscriptable_iterable` /
  `::test_bounded_rows_honours_a_trusted_widening` (`bounded_rows`). Each scenario sits on the
  function that receives it.
- **The floor, two instruments.** `grep -cE '^(async )?def test'` → **120** package, **56**
  live. Independent `ast` parse, module-level `test*` functions × stacked `parametrize`
  argvalue cardinalities → **120 → 191**, **56 → 56**, `unresolved_parametrize = 0`,
  `Test*` classes 0 in both files. `diff` of the `def test` name lists `d727a256` → `HEAD`:
  exactly three added (`…lets_a_cancellation_during_cleanup_reach_the_task` ×1,
  `…lets_a_cancelled_acquisition_through` ×1, `…takes_no_client_window` ×4), so 117 + 3 = 120
  and 185 + 6 = 191 close. The spec publishes `120 rows / 191 node ids` once (`:1073`), unit
  defined at `:1022`, framed as a floor.
- **The register.** Parsed mechanically: **16 rows, 20 backticked shas, 20 distinct**; every
  sha passes `git merge-base --is-ancestor 567cc6d0 <sha>` and `<sha> HEAD`; **one** row has an
  empty **Bears on** cell and carries 4 (`4c483b6b`, `d3b91c8d`, `9a9f970c`, `4d98ad98`); the
  `63a132be` row is the 15th, class `correction`, `Bears on` = D6 / DRY / Test plan, so "Sixteen
  of them, in the table's first 15 rows" and "the **16** is the figure that matters" are both
  arithmetic on the table as written. `git rev-list --count 567cc6d0..63a132be` → **313**.
  **63 re-derives only over the population the paragraph states**: the sixteen package `.py`
  paths in the Implementation plan's table rows (`:891-905`, three `tests/` rows excluded)
  plus `forms/resolvers.py`, in a shell array → **63** at `63a132be`, **62** at `d727a256`. A
  first attempt that swapped `conf.py` / `schema.py` for the shared-modules note's
  `utils/policies.py` / `utils/errors.py` / `utils/inputs.py` returned **69 / 68** — the
  paragraph's composition sentence is what makes the figure re-derivable, and it is correct.
- **The two-halves claim.** `git show 63a132be -- django_strawberry_framework/resource_policy.py`:
  `_is_cleanup_diagnostic` is `isinstance(error, Exception)`; `_close_async_iterator` re-raises
  when `primary_error is None or not _is_cleanup_diagnostic(close_error)`, and
  `_cleanup_rejected_async_iterable` re-raises `if not _is_cleanup_diagnostic(aiter_err)` before
  attaching — both async cleanup seams, `Exception` demoted to a `__notes__` entry via
  `_attach_cleanup_note`, anything else propagating. The row's (ii) is exact. Its ownership
  claim checks too: spec-050 `:963-970` (delegation, exported pair "read through this
  delegation") is under **Decision 5**, and `:1253-1259` ("a cleanup `Exception` is demoted to
  a note … a `BaseException` that is not an `Exception` is … a control signal … Both cleanup
  seams share the one rule") is under **Decision 8**; the `CancelledError` mention at `:1586`
  is spec-050's Edge cases restating Decision 8, not a third owner.
- **Vintage stamps.** `313` appears in `## How to read this file` (`:26`) and the scope
  paragraph (`:168`); `63a132be` in `## Provenance of this record` (`:56`); no `d727a256`
  survives in the rationale's scope, provenance or how-to-read passages.

### Spec/rationale division

- `grep -cE '\b[0-9a-f]{8}\b'` over the spec → **0**; no sha, backticked or bare.
- History sweep over the whole spec with a wider list than any prior pass's (`previously`,
  `as of`, `no longer`, `used to`, `formerly`, `at the release`, `post-release`, `since the
  release`, `has since`, `changed meaning`, `this round`, `this pass`, `came off`, `moved
  (the|onto|below)`, bare `now`, `gained`, `moved`, `retired`, `successor`, `later commit`,
  either sha) → six lines: `:22` and `:1136` (contract / roadmap uses of "now" and
  "successor"), `:538`/`:540` (the contract sentence every pass cleared), and `:380-381` (the
  Low above, pre-existing at `HEAD`). **Nothing pass 3 wrote is on the list.** The new Decision 6
  paragraph, the DRY row and the Test-plan sentence are present tense throughout; the
  chronology (`89ee8ac5` gained, `63a132be` took off) sits only in the rationale's register row,
  its `#### Claims the spec may no longer make` bullet, and the `### Decision 6` entry.
- The `offset|requested_limit|window|skip|coordinate` sweep the dispatch asked for: 44 hits,
  every one graded. `:152` (Current state, window planner), `:271` (bounds-table cell, still
  true — see the normalizer check above), `:449` / `:1039` / `:1012` (`@skip` directive prose
  and "is skipped"), `:552-584` and `:937-946` and `:1085-1090` (the three pass-3 sites, graded
  above), `:615-637` / `:692` / `:849-851` / `:956` (Decision 7 and Decision 13 connection-window
  arithmetic, unrelated to the raw-list seam). No site says the exported pair takes a
  coordinate; no site says the root list field calls the exported pair.

### DRY findings

- **No duplication across the pair.** The corrected contract is stated once in the spec
  (Decision 6) and pointed to from the DRY row and the Test plan by different content (rule,
  then which rows pin it); the chronology is stated once in the register row, once as a retired
  claim, once as a one-sentence successor in the `### Decision 6` entry — three keys
  (commit / retired claim / decision), each mandated by `BUILD.md` `## Spec rationale
  extraction`.
- **No verbatim lift from spec-050.** Every sentence of the new Decision 6 paragraph
  (`:564-581`), keyed by its first 60 characters, is absent from
  `docs/spec-050-list_field_arguments-0_0_15.md`; the shared vocabulary ("coordinate-bearing
  seam is package-private", "not a second bound") is two phrases, not a paragraph, and spec-050
  stays named in prose rather than linked, as the pass-1 note decided.
- **The DRY row states rules, not an exception list.** "`bounded_rows` / `bounded_rows_async`
  are the only raw-list bound, read through their delegation" is followed by what each of the
  three rules governs and three prohibitions (no local limit, no per-color limit, no unchecked
  coordinate to the private pair). Each prohibition is enforceable and true at `HEAD` — the
  private pair has exactly one external caller file and every coordinate it receives is a
  normalizer output. No "except" clause was appended.
- **Existence challenge: none raised.** The round authored no helper. The new private pair is
  spec-050's code, not this round's, and its existence is argued in `63a132be`'s own message
  and in spec-050 Decision 5; re-raising it here would be re-litigating a settled contract call.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` → **0 lines**. `git status --short` lists
**no** `.py` file at all, so the round changed no executable code. `resource_policy.py`'s own
`__all__` parses to the same **16** names at `63a132be`; `_windowed_rows` /
`_windowed_rows_async` are not in it, which is the contract the pass documents.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Applicable — the cohort is documentation-only.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-047-resource_policy-0_0_14.md`
  → `OK: 34 terms`, exit 0.
- `uv run python scripts/check_trailing_commas.py --check <spec> <rationale> <this artifact>`
  → exit 0 (explicit paths only). `git diff --check -- <spec> <rationale>` → exit 0.
- **Citations, whole-file, by `ast` against the extraction.** Spec **44 `path::Symbol`
  occurrences, 32 distinct, 0 unresolved** — the report's figures exactly; the five it names
  as new or re-cited all resolve. Spec `#"substring"` citations **1**
  (`extensions/resource_policy.py #"_STRUCTURAL_DELIMITER_PAIRS: tuple"`), matching **exactly
  one** line. Rationale **13 occurrences, 11 distinct, 3 unresolved** = two qualified
  `connection.py::_resolve_connection_fast_path` + one
  `forms/resolvers.py::_run_plain_form_pipeline_sync`, each beside its `git show <death
  commit>^:<path>` pointer; the two new `list_field.py::_normalize_list_arguments` citations
  resolve (`list_field.py:389`). Rationale `#"substring"` citations 0.
- **Links.** Spec **40 uses / 40 definitions**, rationale **17 / 17**, this artifact **5 / 5**:
  `used-but-undefined: none`, `defined-but-unused: none`, no duplicate definitions, in all
  three. One `<!-- LINK DEFINITIONS -->` block per file; the 10 canonical group headers present
  and in `START.md` order in all three (compared as a sequence); alphabetical within every
  group, 0 violations; every definition path exists on disk from its own file's directory
  (the rationale's climb two levels out of `docs/SPECS/appx/`).
- **Anchors.** In-page: spec **14 distinct, 0 dangling**; rationale **3, 0 dangling**.
  Cross-file `#fragment` definitions re-slugged against the target's headings: 0 dangling in
  both.
- **Sizes.** `wc -c`: spec **82,445**, rationale **43,172**, this artifact **142,968** before
  this section — the report's three `After` figures exactly.
- **Concurrent-session files, reported not touched.** `git status --short` carries `KANBAN.md`,
  `KANBAN.html`, `examples/fakeshop/db.sqlite3` (Worker 0's fence-change rows), staged
  deletions and one addition under `docs/builder/` plus `docs/review/rev-050-*` and a
  maintainer review input (the concurrent spec-050 session's). This review wrote to this
  artifact and its own memory file and nothing else; nothing was reverted. The decoy
  (`products/schema.py`, `spec-060`) is absent from `git status`.
- **`scripts/review_inspect.py` skipped, with reason.** No `.py` file added or touched; none of
  `BUILD.md` `### When to run the helper during build`'s three Worker-3 triggers fires.

### What looks solid

- **Finding P was closed by naming the mechanism at every one of its three homes plus the one
  the grep could not see.** The opener, the "one seam" paragraph, the coordinate paragraph, the
  DRY row and the Test-plan sentence now describe one arrangement — exported pair windowless,
  private pair windowed, one derivation, one normalizer — and every call, signature and row
  they name exists at `63a132be` exactly as described. The bounds-table cell was correctly left
  alone: the ceiling did not move, the receiving function did.
- **Finding Q landed with its arithmetic re-closed.** The new row's placement keeps the "last
  row changes nothing" sentence true; the 313 / 63 / 20 / 16 rows / 16 + 4 split all re-derive
  from the table and from `git`; the class is defensible under the register's own taxonomy
  (`63a132be` changed what the code does, so `correction`, on the `aadca5a2` precedent), and
  the taxonomy's three definitions are stated beside it for a reader who would class it
  otherwise.
- **The floor was raised for the right reason and measured, not decremented.** Publishing a row
  the floor predates would have been the plan-figure defect class; 120 / 191 is a `63a132be`
  reading under two instruments and its delta from 117 / 185 is exactly the three added
  functions.
- **The pass reports its own reading conditions** — which `HEAD`, which files proved identical,
  which dirty paths are whose — and names the instrument that settles each claim (the `ast`
  attribution map, the shell array), so every figure here was re-derivable without reading the
  report's conclusions.

### Temp test verification

None created. `docs/builder/temp-tests/047/` was not used: every question was answerable by an
`ast` / `grep` / `git` measurement over the `HEAD` extraction, and the round ships no behavior
a temp test could exercise. Disposition: nothing to promote.

### Notes for Worker 1 (spec reconciliation)

1. **Escalated: Decision 2's `:380-383` narrative** (Low, above). Pre-existing at `HEAD`, so a
   Worker 1 call on whether this round's division rule reaches a passage it was not dispatched
   against. Resolution paths: (a) one contract sentence in the spec, the deliberation to the
   rationale's Decision 2 entry, same shape as every other pass-1 split; (b) leave it and
   record here that the round's sweeps did not cover `moved` / `now shared`, so a later sweep
   adds them. Nothing downstream cites the passage.
2. **Two report-only Lows** (the 8-of-12 enumeration, the long-line inventory) reach no shipped
   document; recorded, not editable, per `ARTIFACT.md` `## Re-pass sections`.
3. **Accepted on the record rather than re-derived**, named so the second pair of eyes is
   visible: Q-4 ("row `89ee8ac5` untouched") is indistinguishable in a cumulative diff where the
   whole register is an addition — the row's text matches what the pass-2 review quoted, which
   is the available evidence; and the artifact's `Before 126,243` byte figure has no
   re-measurable source.
4. **Carried items unchanged.** The terms-CSV `notes` cell and `clear_resource_context` remain
   homed as the final-verification pass recorded; nothing in pass 3 touches either.

### Review outcome

`review-accepted`. Findings P and Q are discharged and every factual claim pass 3 introduced —
the windowless export signature, the private pair, the call-site partition between
`list_field.py` and `types/resolvers.py`, `_raw_list_bound` as the only derivation,
`_normalize_list_arguments` as the ceiling check's only owner, the 2 × 2 `TypeError` refusal
row, each Test-plan scenario's receiving function, the 120 / 191 floor and its +3 / +6 delta,
and the register's 16 rows / 20 shas / 313 / 63 / `correction` / two-halves cleanup claim —
re-derives at `63a132be` from source under an independent instrument. No sha and no chronology
entered the spec; the DRY row states rules rather than an appended exception; all 44 spec
citations, both files' links, headers and anchors, and the three gates hold. Three Lows, none
blocking: one pre-existing history passage in Decision 2 escalated to Worker 1, and two
figures in the pass-3 report that reach no shipped document.

---

## Final verification (Worker 1, pass 3)

Fresh spawn after Worker 3 set `review-accepted` on pass 3. `HEAD` = `63a132be` at the start and
at the end of this pass (`git rev-parse --short HEAD`, both times). Read from the same read-only
`git archive HEAD | tar -x` extraction pass 3 proved identical; no `git stash` / `checkout --` /
`restore` / `worktree` was run; nothing outside this cohort's writable paths was written. No
prior section of this artifact was edited.

### Dispatched findings checklist (pass 3) audit

**9 boxes, all `- [x]`, all confirmed. No over-tick, no open box, no deferral owed.** The audit
instrument was `git diff HEAD --` over the two owned documents, parsed into its `+` and `-`
lines and searched for each box's landed contract — never the pass-3 report's account of itself:

- **P-1** — `+` carries `The exported pair carries no client window` and
  `list_field.py::_normalize_list_arguments` is the sole owner`; the spec has **0** occurrences
  of `The seam accepts` (the rationale has **1**, the retired-claim quotation, which is where it
  belongs).
- **P-2** — `+` carries the DRY row's `Each rule governs one thing` clause.
- **P-3** — `+` carries the refusal-row citation and `zero window that never advances the source`.
- **P-3 floor** — `+` carries `120 rows / 191 node ids`; the spec has **0** `117 rows`.
- **P-4** — `+` carries `enters the same seam one level down`; the spec has **0**
  `Both are shared by the root`.
- **Q-1** — `+` carries the `| `63a132be` | spec-050. (i)` row including the
  `_is_cleanup_diagnostic` half.
- **Q-2** — `+` carries `Measured at `63a132be``, `gives **313**`, `**63** of which`,
  `**20** of those`, `grouped into 16 rows`, `Sixteen of them, in the table's first 15 rows`, and
  both moved vintage stamps.
- **Q-3** — `+` carries `then moved the coordinates below the export` and
  `The exported pair accepts neither`.
- **Q-4** — the `89ee8ac5` row is not in `-`. **Instrument limit, stated rather than hidden**
  (Worker 3's note 3): passes 1-3 are all uncommitted, so `git diff HEAD` cannot show a
  pass-to-pass change — `HEAD`'s rationale has **0** register rows at all, and the same is why
  the pre-pass-3 sentences (`Both are shared by the root`, `117 rows`, the coordinate sentence)
  appear in neither `+` nor `-`. The row was compared against the build plan's `89ee8ac5` row
  instead: identical except the **Bears on** cell (`D6, bounds table` here; the plan adds
  `field-bound API`), and that difference is pass 1's authoring — the pass-3 dispatch's Edit
  set touched the `aadca5a2` and four-commit rows around it and not this one.

### Worker 3's three pass-3 Lows

- **Low 1 — Decision 2's build-history sentence. Fixed in the spec, history moved to the
  rationale.** Pre-existing at `HEAD` (`git show HEAD:<spec> | grep -c 'dispatch itself moved'`
  = 1), inside the fence, so the round's division rule reaches it. The spec now reads
  `#"The shape-agnostic read / write / delete dispatch lives in `utils/context.py`"` — present
  tense, the four shapes and the single-landing-place claim kept as contract, and the licensed
  one-line `[rationale]` pointer. Both kept claims re-verified at `63a132be`:
  `utils/context.py`'s module docstring enumerates `None`, object, `dict` and a frozen object;
  `resource_policy.py` and `optimizer/_context.py` both import `clear_context_key` /
  `get_context_value` / `stash_on_context` from it and the optimizer re-exports them in its own
  `__all__`. The "moved ... would have been the first duplicate" derivation was **not** already
  in the rationale's `### Decision 2` entry (it carried only the alternatives and the
  post-release pointer); it is there now as *Moved — why the context dispatch is shared rather
  than copied*. A history sweep extended with `now shared|itself moved|would have been the
  first` over the whole spec returns **1** line, `:540`, the pre-existing contract sentence.
- **Low 2 — the pass-3 report's 8-of-12 enumeration.** Report-only; the claim was true and the
  parenthetical undercounted its population. Recorded, not edited (`ARTIFACT.md`
  `## Re-pass sections`). For the record the four omitted are
  `::test_bounded_rows_slices_unsliceable_iterable_with_offset_and_requested_limit`,
  `::test_bounded_rows_declined_sync_cleanup_resumable`,
  `::test_bounded_rows_async_keeps_the_deadline_primary_when_the_close_fails`,
  `::test_bounded_rows_shared_policy_seams_spy` — all `_windowed_rows*` callers, which is the
  claim.
- **Low 3 — the long-line inventory omitted spec `:560`.** Report-only; recorded, not edited.
  That line is pass 1's Decision 6 reflow, not pass 3's; `.md` line length is ungated.

### DRY check across this cohort and the prior passes

No new duplication. The Decision 2 repair states the contract once in the spec and the
derivation once in the rationale (`grep -c 'would have been the first duplicate'` → spec **0**,
rationale **1**). The spec still carries no sha (`grep -cE '\b[0-9a-f]{8}\b'` → **0**).

### Existing tests — the gate ran

The plan's `### Dispatch (pass 3 ...)` step 3 lifts the advance exception's second leg:
`git status --short` carries **no dirty `.py`** (count 0), so the suite measures `HEAD` and
nothing else. `uv run pytest --no-cov -q` → **7796 passed, 40 skipped in 646.78s**, exit 0. The
full command table, with every other gate, is in `docs/builder/bld-047-final.md`
`## Gate re-run at 63a132be`. No `--cov*` flag was used.

### Spec status-line re-verification

No edit owed: `:1` / `:3` `DONE-047-0.0.14` matches the board; `:26` `Status: SHIPPED` is not
falsified by a round that shipped no slice; `:7-9` and `:11-12` resolve.

### Summary

Round 2 closes `final-accepted`. Findings P and Q are discharged and every box audited against
the diff; the one escalated Low was a pre-existing chronology sentence in Decision 2, now a
present-tense contract in the spec with its derivation in the rationale; the two report-only
Lows are recorded. The real gate ran this time and is green. Spec 63,529 → 82,415 across the
round; rationale 19,262 → 43,791.

### Spec changes made (Worker 1 only)

- `docs/SPECS/spec-047-resource_policy-0_0_14.md`, Decision 2,
  `#"The shape-agnostic read / write / delete dispatch lives in"` — replaced the "itself moved
  to ... is now shared ... would have been the first duplicate" narrative with the present-tense
  contract plus a one-line rationale pointer. Triggered by Worker 3's pass-3 Low 1. Reason: the
  spec never narrates its own history (`BUILD.md` `## Spec rationale extraction`). Spec
  82,445 → 82,415 (−30).
- `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md`, `### Decision 2`,
  `#"why the context dispatch is shared rather than copied"` — the derivation the spec dropped,
  as a *Moved* paragraph. Same trigger. Rationale 43,172 → 43,791 (+619).

### Final status

`final-accepted`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-047]: ../SPECS/spec-047-resource_policy-0_0_14.md
[spec-047-rationale]: ../SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md

<!-- docs/builder/ -->
[artifact]: ARTIFACT.md
[build]: BUILD.md
[build-047]: build-047-resource_policy-0_0_14.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
