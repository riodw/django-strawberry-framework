# Build: Round 1 — Rationale extraction + spec/code reconciliation

Spec reference: `docs/spec-045-visibility_boundary-0_0_14.md` (whole file; every one of its
eight `### Decision N` sections plus `## Current state`, `## Non-goals`, `## Error shapes`,
`## Test plan`, `## Doc updates`, `## Risks and open questions`, `## Out of scope`)
Build plan: `docs/builder/build-045-visibility_boundary-0_0_14.md`, round R1
Status: revision-needed

## Round preamble

This is a **review round** in the `BUILD.md` `## Review rounds` sense: the input is
already-built, already-committed work, not a slice from the spec's `## Slice checklist`.
There is no maintainer review document for this round. The spec's one documentation slice
already shipped (card `DONE-045-0.0.14`, `KANBAN.md` renders it in Done, all five authored
glossary terms exist, the terms CSV is on disk). What was missing is the closeout: the
rationale companion had never been written, and the spec had not been reconciled against
the code as it stands after the post-`0.0.14` hardening.

**Worker 0's pre-dispatch verification, carried into this artifact per the plan's
`## Worker-0 pre-dispatch verification`:** all 40 symbols the spec's eight decisions cite
as enforcing symbols, and all 9 test names it cites as pinning tests, were verified present
at HEAD before dispatch — 38 in `django_strawberry_framework/utils/querysets.py`
(`SyncMisuseError`, `_BOUND_VALUE_NORMALIZERS`, `_bake_deferred_filter_or_defect`,
`_base_table_defect`, `_combined_query_table_defect`, `_concrete_or_none`,
`_deferred_value_defect`, `_direct_rhs_defect`, `_expr_graph_defect`,
`_expr_sequence_defect`, `_is_reconstructable_node`, `_join_defect`,
`_lookup_operands_defect`, `_node_metadata_defect`, `_normalized_bound_value`,
`_normalized_visibility_result`, `_prepared_visibility_source`, `_query_ast_defect`,
`_query_container_defect`, `_query_genuineness_defect`, `_raw_sql_sequence_defect`,
`_rebuild_query_payloads`, `_rebuilt_prefetch_or_defect`, `_reconstructed_value`,
`_reconstruction_defect`, `_rhs_hook_defect`, `_seal_or_defect`,
`_sealed_prefetch_related_lookups`, `_select_related_defect`, `_shadow_defect`,
`_static_attr_present`, `_template_params_defect`, `_type_is_genuinely_django`,
`_visibility_result_error`, `_where_tree_defect`, `apply_type_visibility_async`,
`apply_type_visibility_sync`, `reject_async_in_sync_context`), plus
`exceptions.py::ConfigurationError`, `optimizer/walker.py::_build_child_queryset`, and
`optimizer/nested_fetch.py::unwindowable_child_queryset_reason`. This round's job was the
semantic level: does each cited symbol enforce what the sentence says it enforces.

**Round-level declarations (from the plan, unchanged):**

- Ownership partition: `none; sequential rounds`. R1 owns exactly four files —
  `docs/spec-045-visibility_boundary-0_0_14-rationale.md` (new),
  `docs/spec-045-visibility_boundary-0_0_14.md` (Worker 1 is the only role permitted to
  edit it), `docs/builder/bld-045-r1-rationale_reconciliation.md`, and
  `docs/builder/worker-memory/worker-1.md`.
- Hot-path declaration: `none`. This round changes no runtime code, so no before/after
  number is owed.
- Floor-verification scope: `none`. This round touches no Django / Strawberry / channels
  integration seam. (The floor itself is stated only in `BUILD.md` `## Floor
  verification`; nothing here restates the shared `.venv`'s versions.)
- Failability proofs: none owed. This round introduces no boundary, guard, gate, or
  rejection path — `BUILD.md` `### What needs a proof, and what does not` scopes the
  obligation to new boundaries, and doc edits need none.

---

## Plan (Worker 1)

### Why no Worker 2 pass was dispatched

The writable surface of this round is the spec and its rationale companion — both
custodian-owned, per `BUILD.md` `## Spec reconciliation` ("Only Worker 1 may mutate
`docs/spec-<NNN>-<topic>-<0_0_X>.md`") and `worker-1.md` `### Performing the rationale
move` ("Worker 1 is the only role that performs the move") — plus this artifact. There is
no source or test edit in this round's ownership, so there is nothing a builder could
implement: a Worker 2 dispatch would have had an empty diff. Worker 1 therefore writes both
the `## Plan (Worker 1)` section and the `## Final verification (Worker 1)` section, and
sets `Status: review-accepted` so Worker 0 can dispatch Worker 3 for the independent audit.
`BUILD.md` `### Isolation is non-waivable` is not weakened: it forbids the agent that wrote
code from also approving it, and Worker 3's audit is exactly the pass that has not been
skipped. `final-accepted` is not set here; Worker 1 returns for final verification after
Worker 3.

### DRY analysis

**Helper inventory checked.** Not applicable as a code-helper question — this round adds no
Python. The equivalent duplication question for a documentation round is *where does each
claim live*, and it was answered by reading the whole surface: the spec, the rationale
companion (new), the five authored `docs/GLOSSARY.md` bodies, the module docstring and
per-symbol docstrings in `django_strawberry_framework/utils/querysets.py`, and the
`KANBAN.md` card body. Shapes searched for: every claim about what the seal preserves,
drops, retains, rebuilds, or rejects.

- **Existing patterns reused.** The rationale companion follows the shape `BUILD.md`
  `## Spec rationale extraction` prescribes for the reader (per-decision entries keyed by
  heading and anchor, each carrying rejected alternatives, change history, and claims no
  longer permitted) rather than inventing a layout. The precedent artifact
  `docs/builder/bld-044-r1-rationale_move.md` covers the same round type for card 044.
- **New shared shape justified.** One: the rationale companion itself, whose single
  responsibility is to be the deliberative layer keyed to this spec. Its call sites are
  the spec's eight `**Deliberation.**` pointers.
- **Duplication risk avoided.** The obvious naive shape is to *copy* deliberation into the
  companion and leave it in the spec, which is exactly what `## Spec rationale extraction`
  forbids ("a cut-and-paste, not a copy"). Every passage that moved was cut. The second
  risk is restating the code's docstrings in the spec; the spec states the contract and
  cites the enforcing symbol instead, and the rationale cites the docstring as a source
  rather than reproducing it.
- **Deliberate non-duplication of a live gap.** The `Value.value` retention finding below
  is stated once as normative contract in the spec (`## Constraints on the supported query
  surface` and Decision 8's retention set), once as history in the rationale, and once as
  a routed finding here. Those are three different jobs, not three copies.

### Implementation steps

1. Read the whole spec, then read `django_strawberry_framework/utils/querysets.py` — its
   module docstring and every symbol the spec cites — and `tests/utils/test_querysets.py`
   for the test names that pin each claim.
2. Recover the deliberation from primary sources. `git show <commit>:docs/feedback.md` and
   `git show 60998b17:get_queryset-visibility-boundary-plan.md` into the scratchpad
   **outside the repo**, never `git stash` / `git checkout` (`BUILD.md` `## Claims are
   proven mechanically`, and this tree carries concurrent sessions). Commits read in order:
   `1dd9273a`, `60998b17`, `49b66922`, `8af55482`, `bbd216fc`, `dfa86f90`, `ff65666d`,
   `5a74d803`, `471d4c6b`.
3. Author `docs/spec-045-visibility_boundary-0_0_14-rationale.md`: a provenance section
   distinguishing moved from reconstructed text, a round chronology, one entry per spec
   decision keyed by heading and anchor, and one section for deliberation belonging to no
   single decision.
4. Reconcile the spec decision by decision against the code at HEAD. Correct what is
   wrong, stale, or describes a contract the code no longer offers; move the chronology
   and the rejected alternatives out; state the corrected contract directly with no
   amendment block, retraction paragraph, or "as of round N" hedge.
5. Keep every decision number and heading, so the dozens of in-source `spec-045 Decision N`
   citations and the spec's own in-page anchors stay valid.
6. Verify: `scripts/check_trailing_commas.py --check` on all three markdown files,
   `scripts/check_spec_glossary.py --spec` on the spec at exit 0, every in-page anchor and
   every reference-style definition resolved mechanically, every link-def target checked to
   exist on disk.
7. Record every spec edit, every mismatch found, and every suspected code defect here.

Line numbers are deliberately absent from these steps: the spec is addressed by section
heading, which survives an edit that shifts lines.

### Test additions / updates

None. This round writes no test and runs no `pytest` (`AGENTS.md`: run only when
explicitly asked; the dispatch forbade it for this pass). The verification this round owes
is documentary and mechanical, and is recorded under `## Final verification (Worker 1)`.
Every test name the spec cites was checked to exist as a `def` in its file — that is a
grep, not a run.

### Implementation discretion items

None. There is one implementer and one reviewer for this round and no delegated choice.

### Dispatched findings checklist

This round has no maintainer review document, so its checklist is the closeout obligation
the dispatch names, quoted, one box per item.

- [x] "the rationale companion was never written" — author
      `docs/spec-045-visibility_boundary-0_0_14-rationale.md` as the deliberative layer
      keyed to the spec, per `BUILD.md` `## Spec rationale extraction`.
- [x] "where the spec currently carries deliberation that belongs in the rationale … you
      move that text out per the ordinary rule: cut-and-paste, not copy." Moved: eight
      `**Alternative rejected.**` blocks, six `**Why.**` blocks, Decision 8's
      `**Residuals this decision subsumes.**` block, the whole
      `## Risks and open questions` narration, and the chronology clauses in the opener,
      `## Non-goals`, and `## Out of scope`.
- [x] "Record precisely what you moved versus what you reconstructed" — recorded in the
      rationale's `## Provenance of this record` (per-passage `(moved from the spec)` /
      `(reconstructed)` marks) and enumerated under
      `### Moved versus reconstructed ledger` below.
- [x] "The spec must come out reading as a clean current contract" — every hedge the
      dispatch names is gone: "*Resolved after `0.0.14`*", "flagged by this card as the
      future root fix and since adopted", "supersedes the prove-then-retain limitation
      Decision 2 shipped with", "Decision 8 was added after the `0.0.14` cut".
- [x] Decision 2: "a decision that still describes the retained graph as the end state is
      a spec-vs-code mismatch to fix."
- [x] Decision 3: confirm `_known_related_objects` "deliberately dropped" and
      `_result_cache` never copied, against `_seal_or_defect`.
- [x] Decision 5 / `## Error shapes`: "confirm each code exists, that the order is the
      code's real order, and that the consumer-facing wording column matches the actual
      message text."
- [x] Decision 8: "confirm `_normalized_bound_value` / `_BOUND_VALUE_NORMALIZERS` /
      `_direct_rhs_defect` / `_rhs_hook_defect` actually close them, and that no docstring
      or spec sentence still claims immutability the implementation does not provide."
- [x] "Verify the spec carries no surviving version of that false claim" (the historical
      docstring falsely claiming the sealed predicate could not be mutated post-seal).
- [x] "`## Current state`, `## Non-goals`, `## Risks and open questions`, and
      `## Out of scope` … Bring them to the present contract."
- [x] "`## Test plan` / `## Doc updates` / `## Definition of done`: … does the cited symbol
      enforce what the sentence says it enforces?"
- [x] Conventions: reference-style links with the ten canonical group headers, no raw
      `path:NN` outside this artifact, `check_trailing_commas.py --check` clean,
      `check_spec_glossary.py` at exit 0, no `pytest`, no commit, no branch, no stash.

---

## Final verification (Worker 1)

### Summary

R1 authored the spec's missing deliberative layer and reconciled the spec against the
boundary as it stands at HEAD. The rationale companion is 35,970 bytes with **8**
per-decision entries (one per spec decision; `grep -c '^## Decision '` on the file) plus a
provenance section, a round chronology, and one section for deliberation belonging to no
single decision. The spec went from 35,349 bytes at HEAD to 39,669: it *grew* despite the
extraction, because the reconciliation added normative contract the spec had been missing
(three properties of the AST walk, the retained-`QuerySet`-state gate, the
prohibited-kwargs gate, the exhaustive retention set) while cutting deliberation. The
`BUILD.md` corpus ratchet governs the six builder workflow files and not a spec, so the
growth needs no retirement.

Nine of the round's mismatches are corrections of fact rather than tidying. The one that
matters most is Decision 8's residual-subsumption claim, which was false and is now
stated accurately, and which surfaced a live retention gap in the code recorded under
`### Notes for Worker 1 (spec reconciliation)`.

### Verification commands run

- `uv run python scripts/check_trailing_commas.py --check
  docs/spec-045-visibility_boundary-0_0_14.md
  docs/spec-045-visibility_boundary-0_0_14-rationale.md` — pass, exit 0.
- `uv run python scripts/check_spec_glossary.py --spec
  docs/spec-045-visibility_boundary-0_0_14.md` — pass, exit 0, "9 terms - all have glossary
  entries and at least one spec link."
- `uv run python scripts/check_spec_glossary.py --spec
  docs/spec-045-visibility_boundary-0_0_14-rationale.md` — exit 2, `missing file:
  docs/spec-045-visibility_boundary-0_0_14-rationale-terms.csv`. Expected and correct: the
  script is a spec checker and derives a companion CSV path from the file's stem; a
  rationale file is not a spec and has no terms CSV. Not a finding.
- A one-off AST-free slug check (script written to the scratchpad, not the repo): every
  in-page `](#…)` anchor in the spec resolves to a heading in the spec (0 unresolved);
  every `#fragment` in the rationale's link definitions that targets the spec resolves to a
  spec heading (0 unresolved); 0 unused link definitions in either file. Every link-def
  target was then checked to exist on disk (`GLOSSARY.md`, the spec,
  `../django_strawberry_framework/utils/querysets.py`,
  `../django_strawberry_framework/optimizer/walker.py`,
  `../tests/utils/test_querysets.py`, `../django_strawberry_framework/exceptions.py`,
  `../django_strawberry_framework/optimizer/nested_fetch.py`, and the four other test
  paths).
- No `pytest`, no `--cov*` flag, no `git stash` / `git checkout` / `git restore` /
  `git worktree`, no commit, no branch. Historical evidence was read with
  `git show <commit>:<path>` redirected into the session scratchpad **outside** the
  repository.
- One read-only Django probe was run to settle the `Value.value` question mechanically
  (below). It is a `uv run python` script in the scratchpad, not a test, and it mutates
  nothing.
- `git status --short` after every write: exactly the three files this round owns appear
  (`docs/spec-045-visibility_boundary-0_0_14.md` modified;
  `docs/spec-045-visibility_boundary-0_0_14-rationale.md` and this artifact untracked),
  plus `docs/builder/build-045-visibility_boundary-0_0_14.md` untracked (Worker 0's plan,
  not yet committed).

### Concurrent-session churn observed (not this round's, not reverted)

The plan recorded a clean baseline. Mid-round, `docs/feedback.md` appeared as `M` with
112 insertions and 104 deletions. This round never opened it for writing. Its new content
is a fresh adversarial review of **spec-046 transport security** — a different card
entirely — so it is a concurrent maintainer session's work under `AGENTS.md` rule 34:
recorded, treated as out of scope, and **not reverted**. No later pass should read its churn
as this cycle's output. (`docs/feedback.md` is also on the plan's do-not-touch list.)

### Moved versus reconstructed ledger

**Moved out of the spec** (cut, and now in the rationale companion):

| Spec text moved | Now in the rationale under |
|---|---|
| Decision 1 `**Why.**` + `**Alternative rejected.**` (class-level method inventory, zero-SQL probes) | Decision 1, Alternatives rejected |
| Decision 2 `**Why.**` + `**Alternative rejected.**` (`__module__` strings, "is `clone` dispatch-free?") | Decision 2, Alternatives rejected |
| Decision 3 `**Why.**` + `**Alternative rejected.**` (identity is not immutability) — the normative half was kept in the spec as a contract sentence | Decision 3, Alternatives rejected |
| Decision 4 `**Why.**` + `**Alternative rejected.**` (copy the consumer `Prefetch`) | Decision 4, Alternatives rejected |
| Decision 5 `**Why.**` + `**Alternative rejected.**` (base-table-gated `Query.model`) | Decision 5, Alternatives rejected |
| Decision 6 `**Why.**` + `**Alternative rejected.**` (propagate backend exceptions) | Decision 6, Alternatives rejected |
| Decision 7 `**Alternative rejected.**` (joint-cut owner) | Decision 7, Alternatives rejected |
| Decision 8 `**Why.**` (unbounded walk expansion, latency, whack-a-mole), `**Residuals this decision subsumes.**`, `**Alternative rejected.**` | Decision 8, Alternatives rejected + Claims it may no longer make |
| Decision 8's "flagged by this card as the future root fix and since adopted" clause | Decision 8, Changes the decision has undergone |
| `## Risks and open questions` bullet 1 in full (the "*Resolved after `0.0.14`*" narration) | `## Deliberation that belonged to no single decision` |
| `## Risks and open questions` bullet 2's "Preferred answer / fallback" deliberation — the constraint itself stayed, relocated to `## Constraints on the supported query surface` | Decision 2, Alternatives rejected (the allowlist) |
| The opener's round chronology ("Successive adversarial review rounds closed their P1/P2 correctness findings on 2026-07-20 … Decision 8 was added after the `0.0.14` cut … supersedes the prove-then-retain limitation Decision 2 shipped with") | `## Round chronology` and Decision 2, Claims it may no longer make |
| `## Non-goals` "No new abstraction adopted here" bullet and `## Out of scope` bullet 1, both narrating flagged-then-adopted | `## Deliberation that belonged to no single decision` |

**Reconstructed** (never previously written down anywhere durable; rebuilt from the
sources named in each entry): the whole `## Round chronology` table and its two
load-bearing notes; the round-3 "do not fix only the literal `chain` name" required-fix
wording behind Decision 1's structural rule; Decision 1's `_queryset_state_defect` change;
Decision 2's three later-round property additions (expression-owned state, container
payloads, cycles) and the raw-SQL round; Decision 3's rejected
unoverridden-default-hook narrowing and the reason `_known_related_objects` is dropped;
Decision 4's rejected `queryset is not None`-only rebuild and the symmetric unrouted-parent
rule; Decision 5's rejected duck-typed `_concrete_or_none` and the floor-compatibility
change; Decision 6's rejected per-code exception taxonomy and the `render_error` seam
reasoning; Decision 8's rejected `clone()` / `copy()` / `deepcopy` rebuild strategies, the
rejected exact-type bound-value rule with the 830-row live tier as its fail-close canary,
the rejected `get_source_expressions()` operand discovery, and the fact that the
four-finding round had already named canonical reconstruction as the stronger fix.

**Deleted rather than moved** (`worker-1.md` rule 2 — prose the current decisions have
falsified belongs in neither file): Decision 8's claim that the `Value.value` residual is
"closed by normalization"; its summary clause "no bound parameter whose methods are not the
interpreter's own"; and the spec's assertion that
`django_strawberry_framework/utils/querysets.py` "is at 100% coverage", which no worker may
measure (`BUILD.md` `## Coverage is the maintainer's gate`) and which was therefore an
unverifiable number in a contract. The gate itself is stated instead. The rationale records
*that* the residual claim was withdrawn and why, which is history, not a false sentence.

### Spec changes made (Worker 1 only)

Every edit below is to `docs/spec-045-visibility_boundary-0_0_14.md`, triggered by round
R1. Sections are named rather than line-numbered because several edits shifted lines.

1. **Opener.** Cited: "Successive adversarial review rounds closed their P1/P2 correctness
   findings on 2026-07-20 … Decision 8 was added after the `0.0.14` cut … which supersedes
   the prove-then-retain limitation Decision 2 shipped with." Reason: a contract that
   narrates its own chronology forces the reader to reconstruct what is currently true;
   moved to the rationale and replaced with a pointer to it.
2. **`Status:` line.** Cited: "shipped in `0.0.14` (commit `60998b17`); this card records
   the governing artifacts." Reason: the artifacts now describe the boundary *including*
   its post-`0.0.14` hardening, which the old line did not say. Re-verified per
   `worker-1.md` `## Spec status-line re-verification`.
3. **`## Current state`, bullet 1.** Cited: "is at 100% coverage under the
   `fail_under = 100` gate." Reason: an unverifiable measured number — no worker may run
   coverage. Restated as the gate the module sits inside.
4. **`## Current state`, bullet 2.** Reason: the bullet described the rebuild and stopped;
   canonical reconstruction is part of what the boundary now guarantees, so it is named
   with a pointer to Decision 8.
5. **`## Non-goals`.** Cited: "No new abstraction adopted here. Canonical reconstruction …
   is flagged by this card as the future root fix, not adopted by it. It has since landed."
   Reason: a non-goal written in the future tense about work that has landed. Removed; the
   framing is in the rationale.
6. **`## Architectural decisions` preamble.** Reason: added that decision numbers are cited
   in-source as `spec-045 Decision N`, so renumbering is a package-wide rename. Measured
   while writing, counting occurrences rather than matching lines
   (`grep -rEo "spec-045[^ ]* Decision [0-9]+" --include="*.py" . | wc -l`): **41**
   decision-numbered citations across three files — 36 in
   `django_strawberry_framework/utils/querysets.py`, 4 in `tests/utils/test_querysets.py`,
   1 in `django_strawberry_framework/optimizer/walker.py`. (Bare `spec-045` path or
   document mentions in `.py` files total 46 across six files, the extra three being
   `tests/test_list_field.py`, `tests/test_relay_node_field.py`, and
   `tests/test_connection.py`.) This is the standing reason the reconciliation renumbered
   and retitled nothing.
7. **Decision 1.** Removed the `**Why.**` and `**Alternative rejected.**` blocks; added the
   retained-`QuerySet`-state contract (`_db` / `_hints` / `_fields` / `_sticky_filter` /
   `_for_write` pinned to exact shapes, `_hints` copied into a fresh dict) and
   `::_queryset_state_defect` to the enforcing symbols; added the `**Deliberation.**`
   pointer. Reason: the decision claimed non-dispatching *extraction* and was read as
   covering the whole seal, which the four-finding round disproved — reading state without
   dispatch is not using it without dispatch.
8. **Decision 2, opening.** Reason: the decision described prove-then-clone as the end
   state. Post-`dfa86f90` the clone is followed by canonical reconstruction, so the proof
   is now stated as a *precondition* of the clone with a pointer to Decision 8. This is
   the spec-vs-code mismatch the dispatch flagged as most likely.
9. **Decision 2, clause (b).** Reason: `tests/utils/test_querysets.py`
   `::test_query_shadow_defect_is_name_agnostic` cites "spec-045 Decision 2" for the quoted
   phrase "do not fix only the literal `chain` name", which the spec did not contain in any
   form. The structural, never-a-blacklist rule is now stated explicitly so the test's
   citation resolves to a real spec claim. See the Low finding below for the residue.
10. **Decision 2, new three-property block + `extra` mapping clause.** Reason: three
    contract properties the spec did not carry at all — expression-owned state proven
    before the accessor that reads it runs, retained containers proven by payload and not
    only by type and key, and a reference cycle rejected rather than accepted as a shared
    diamond. All three are enforced at HEAD and all three came from the four-finding round.
11. **Decision 2, enforcing symbols.** Reason: the list named `_raw_sql_sequence_defect`
    but not the two symbols that actually validate raw-SQL payloads
    (`_raw_sql_node_defect`, `_raw_sql_params_defect`), and named none of
    `_template_params_defect`, `_expression_state_defect`, `_query_payload_defect`,
    `_genuine_node_defect`, `_container_defect`, `_GraphWalk`, `_WalkState`,
    `_walk_short_circuit`. All verified present at HEAD; all added. Two pinning tests added
    to the tests list.
12. **Decision 3.** Removed the `**Why.**` and `**Alternative rejected.**` blocks, keeping
    their normative half ("object identity is not immutability") as a contract sentence;
    added the `**Deliberation.**` pointer. Verified against `_seal_or_defect`: the rebuild
    sets `_iterable_class`, `_fields`, `_prefetch_related_lookups`, `_sticky_filter`,
    `_for_write` and nothing else — neither `_result_cache` nor `_known_related_objects` is
    copied. Both runners carry the "No identity fast path" comment and call
    `_normalized_visibility_result` unconditionally. **The decision was accurate; no
    correction was needed.**
13. **Decision 4.** Removed the `**Why.**` and `**Alternative rejected.**` blocks; added
    the `**Deliberation.**` pointer. Verified against `_rebuilt_prefetch_or_defect`,
    `_sealed_prefetch_related_lookups`, and `_seal_or_defect` #"effective_alias": accurate
    as written, including the `require_shared_alias` symmetry when the outer alias is
    `None`. **No correction was needed.**
14. **Decision 5.** Removed the `**Why.**` and `**Alternative rejected.**` blocks; added
    the `**Deliberation.**` pointer; added two contract clauses the spec was missing —
    `_concrete_or_none` requires an actual Django model *class* before reading metadata
    (the four-finding round's fix; duck-typing `_meta.concrete_model` let malformed state be
    installed as `sealed.model`), and the deferred-filter bake rejects the
    `models.Q.__init__` internals Django itself prohibits (`_connector` / `_negated`), with
    the Django 5.2-floor import guard that makes the gate behave identically at the floor.
    Added the two `_concrete_or_none` cases to the pinning-test list.
15. **Decision 6 + `## Error shapes` intro.** Removed the `**Why.**` and
    `**Alternative rejected.**` blocks; added the `**Deliberation.**` pointer; **stated the
    one documented exception to the canonical evaluation order.** Reason: the spec asserted
    the order `type -> table -> untrusted -> sliced -> projection -> alias` flatly, while
    `_seal_or_defect`'s own docstring and body run the outer exact-`sql.Query` `untrusted`
    check *before* the combinator table walk, because the walk reads query attributes
    through ordinary attribute access and only a proven-genuine `sql.Query` may be walked.
    All six codes verified to exist and each default message in `_visibility_result_error`
    verified to contain the spec's wording-column phrase verbatim.
16. **Decision 7.** Removed the `**Alternative rejected.**` block; added the pointer. No
    factual change.
17. **Decision 8, body.** Cited and removed: "flagged by this card as the future root fix
    and since adopted"; "So the sealed query carries no consumer-owned AST, no
    consumer-owned container, and no bound parameter whose methods are not the interpreter's
    own"; the whole `**Residuals this decision subsumes.**` block; `**Why.**`;
    `**Alternative rejected.**`. Replaced by: the reconstruction mechanism stated in the
    present tense (including `object.__new__`, the identity memo, and the explicit
    refusal of `clone()` / `copy()` / `deepcopy`); an **exhaustive four-item list of what
    the sealed query still shares with the candidate**, whose fourth item is the
    `Value.value` retention below; an explicit note that a direct `Lookup` right-hand side
    is *not* in that list because it is validated and then normalized; and the measured
    cost as a `**Cost.**` line rather than as an argument. Reason: the removed residual
    claim was **false** (see the finding below), and the summary clause it supported was
    false with it.
18. **`## Test plan`, last bullet.** Cited: "at 100% under `fail_under = 100`." Same reason
    as edit 3.
19. **`## Doc updates`.** Reason: the doc set named one companion; there are now two. The
    rationale companion is named and linked.
20. **`## Risks and open questions` → `## Constraints on the supported query surface`.**
    Reason: the section narrated a resolved architectural argument in the past-with-hedge
    tense and framed a deliberate constraint as an open question. The two normative
    constraints stayed and were restated as constraints; a third was added for the
    `Value.value` retention; the argument moved to the rationale.
21. **`## Out of scope`.** Reason: bullet 1 narrated flagged-then-adopted work and asserted
    the bound-parameter residuals were closed. Replaced by the two things genuinely out of
    scope: any behavior change (this is a documentation card) and the future vetted-
    expression allowlist, explicitly noted as carried by no card.
22. **`## Slice checklist` and `## Definition of done`.** Reason: both named only the
    `*-terms.csv` companion. Both now name `*-rationale.md` too. Boxes stay `- [ ]` — the
    `Status:` line is the completion source of truth under the shipped-spec convention this
    spec states, so ticking them would contradict the spec's own rule.
23. **`<!-- LINK DEFINITIONS -->`.** Added `[rationale]`, and alphabetized the `docs/`,
    `django_strawberry_framework/`, and `tests/` groups, none of which was in order.
    Reason: `START.md` "Markdown link convention" requires alphabetical defs within each
    group; the pre-existing disorder would have been carried into R3's move.

Deferral reasons for boxes left `- [ ]` in `### Dispatched findings checklist`: none —
every box is `- [x]`.

### Spec slice checklist audit

Not applicable: this is a review round, so the Plan carries a
`### Dispatched findings checklist` in that position instead. Every box in it is `- [x]`
and each tick is evidenced by a numbered entry under
`### Spec changes made (Worker 1 only)` or by the rationale companion on disk.

### DRY check across this round

No duplication introduced. The one claim that appears in more than one place — the
`Value.value` retention — appears once as contract, once as history, and once as a routed
finding, which are three different jobs. No text was copied between the spec and the
rationale; every passage listed as moved was cut from the spec (verifiable against
`git show HEAD:docs/spec-045-visibility_boundary-0_0_14.md`).

### Notes for Worker 1 (spec reconciliation)

Two items for Worker 0 to route. Neither was fixed here: this round is read-only on source
and tests.

**Finding 1 (route to the maintainer; contract-level, not a worker's call).
`Value.value` is neither validated by the graph walk nor normalized by reconstruction, so
an arbitrary consumer object in that slot is retained in the sealed query by identity.**

- Symbol-qualified paths: `django_strawberry_framework/utils/querysets.py::_expr_graph_defect`
  (walks a genuine node's children via `get_source_expressions()`, which a `Value` answers
  with an empty list, so the `value` slot is never reached);
  `django_strawberry_framework/utils/querysets.py::_reconstructed_value` #"if not
  _is_reconstructable_node(value_type)" (routes a non-node, non-container value to
  normalization); `django_strawberry_framework/utils/querysets.py::_normalized_bound_value`
  #"if not issubclass(value_type, enum.Enum)" (returns a value descending from no
  plain-data base **unchanged**).
- Evidence, mechanical. A read-only probe run against HEAD sealed
  `Category.objects.filter(is_private=False).annotate(probe=Value(<arbitrary object>))`
  through `_seal_or_defect(qs, Category, None)` and printed:

  ```text
  defect: None
  annotation type: Value
  value is the SAME object: True
  value type: Hostile
  ```

  So the seal admits the object and the sealed query holds the consumer's instance by
  identity — the object is mutable through the consumer's retained reference after the seal
  returns, which is the ownership class `dfa86f90` set out to close generically.
- Why it is a contract-level question and not a defect a worker fixes. Decision 8's stated
  threat model puts "a consumer who deliberately crafts an object to reach a Django or
  database-adapter dispatch site" out of scope, and binding a non-plain-data object into a
  `Value` is exactly that; the value is bound as a `%s` parameter, so it cannot alter SQL
  structure. **But** the boundary applies its own admitted-bound-value rule
  inconsistently: `_direct_rhs_defect` rejects precisely this shape for a `Lookup`'s
  right-hand side — an object defining an attribute hook of its own, or descending from no
  plain-data base — and the same reasoning applies verbatim to `Value.value`, which Django
  also binds as `%s`. Whether the boundary should route an expression's own plain-data
  payload through `_direct_rhs_defect` (and then `_normalized_bound_value`), or whether the
  asymmetry is deliberate under the threat model, turns on which contract the package
  should offer. That is `BUILD.md` `### Contract-level findings are escalated as maintainer
  decisions`, not a builder's call.
- What this round did about it. The spec no longer claims the residual is closed. Decision
  8 now lists the retention exhaustively and names this slot; `## Constraints on the
  supported query surface` records it as a deliberate, bounded constraint; the rationale
  records the withdrawn claim and the probe. Nothing is soft-pedalled and nothing is
  silently closed. If the maintainer decides the asymmetry should go, the fix is a code
  change with its own failability proof, and Decision 8's retention list is the sentence
  that changes with it.

**Finding 2 (Low; route to a pass that owns `tests/`). A test docstring quotes text the
spec does not contain.** `tests/utils/test_querysets.py::test_query_shadow_defect_is_name_agnostic`
reads `Proves the fix is structural (spec-045 Decision 2: "do not fix only the literal
``chain`` name")`. That phrase is the third-round review's required-fix wording, not spec
prose; a reader following the citation into Decision 2 could not find it. This round
narrowed the gap from the spec side by stating the structural, never-a-blacklist rule
explicitly in Decision 2 (edit 9), so the citation now resolves to a real claim, but the
quotation marks still attribute a sentence to the spec that the spec does not carry.
The faithful fix is in the test docstring (drop the quotation marks, or quote the spec's
own wording), which is outside this round's ownership.

### Items deliberately left to a later round

- **R2 (documentation completion).** Two glossary bodies state the contract as it stood
  before canonical reconstruction and are reconciliation findings in their own right:
  `docs/GLOSSARY.md` "Prove-then-clone AST trust" describes prove-before-clone with no
  mention of what follows the clone, and "Sealed execution queryset" says "a fresh
  `QuerySet` is constructed from the validated `sql.Query`" with no mention of
  reconstruction. Both are generated from the fakeshop glossary DB, so the fix is an ORM
  edit plus a regenerate — R2's surface, explicitly not R1's.
- **R2.** `KANBAN.md`'s card body for `DONE-045-0.0.14` carries the withdrawn claim twice,
  in prose more explicit than the spec's was. Its `#### Decision` block says "the sealed
  query is a framework-owned rebuild with **every bound value normalized to an exact inert
  copy**", and its `#### Note` block says Decision 8 "**closes the two bound-parameter
  residuals (`Lookup.rhs`, `Value.value`)** rather than carrying them to a further card".
  Finding 1 above disproves the `Value.value` half of both. Both are DB-generated prose, so
  the fix is an ORM edit plus a byte-clean regenerate of `KANBAN.md` / `KANBAN.html` — R2's
  surface.
- **R2.** The card's `#### Definition of done` says the spec was authored "with its
  companion *-terms.csv"; the spec's own `## Slice checklist` and
  `## Definition of done` now name both companions (edit 22). Re-sync the card body so the
  two do not diverge. The card's `#### Note` also carries the "Post-ship: Decision 8 added
  after the 0.0.14 cut" chronology the spec has just shed; whether a kanban card may narrate
  chronology where a spec may not is R2's call, but it should be a decision rather than an
  oversight.
- **R3 (spec archive).** The module docstring of
  `django_strawberry_framework/utils/querysets.py` cites
  `docs/spec-045-visibility_boundary-0_0_14.md #"## Architectural decisions"` by path. The
  archive move must re-point it, and the 41 in-source `spec-045 … Decision N` citations
  (plus the 46 bare `spec-045` mentions in `.py` files, and the `KANBAN.md` /
  `docs/GLOSSARY.md` mentions) must be checked to still resolve. Flagged here so R3 does
  not have to rediscover it.
- **Not this cycle.** The build plan's R1 description says "nine adversarial review rounds"
  produced the current contract. Only five rounds plus one root fix are sourceable from
  the commit record, and only the first three are indexed anywhere; the rationale's
  `## Round chronology` says so plainly rather than adopting the nine. If the maintainer
  knows of four further rounds, the chronology should gain them; nothing in the tree
  supports them today.

### Final status

`review-accepted`. Worker 3's independent audit runs next; Worker 1 returns for final
verification afterwards and only then may set `final-accepted`.

---

## Review (Worker 3)

Scope reviewed: the whole R1 diff (working tree vs HEAD) — `docs/spec-045-visibility_boundary-0_0_14.md`
(modified), `docs/spec-045-visibility_boundary-0_0_14-rationale.md` (new), this artifact
(new). `docs/builder/build-045-visibility_boundary-0_0_14.md` is Worker 0's plan and is not
under review. `docs/feedback.md` is dirty from a concurrent maintainer session (confirmed
by its content: a spec-046 transport review), was neither opened for writing nor reverted,
and is not read as this round's output (`AGENTS.md` rule 34).

**Round declarations independently verified against the diff, not accepted on prose.**
`git diff --stat` and `git status --short` show the diff touches only `.md` files: no
`.py`, no test, no `docs/GLOSSARY.md`, no `KANBAN.md` / `KANBAN.html`, no
`examples/fakeshop/db.sqlite3`, no `*-terms.csv`, nothing under `docs/SPECS/`, no
`CHANGELOG.md` (`git diff --stat -- django_strawberry_framework tests examples scripts
docs/GLOSSARY.md KANBAN.md KANBAN.html docs/SPECS docs/spec-045-visibility_boundary-0_0_14-terms.csv
CHANGELOG.md` prints nothing). So: no boundary, guard, gate, or rejection path is
introduced and **no failability proof is owed**; no runtime code changes and **no
hot-path number is owed**; no Django / Strawberry / channels integration seam is touched
and **floor-verification scope is genuinely `none`**. `scripts/review_inspect.py` was
**skipped, with reason**: the round adds and touches no `.py` file, so no case in
`BUILD.md` `### When to run the helper during build` fires.

**"No Worker 2 pass" confirmed.** The artifact's stated reason (the round's whole writable
surface is custodian-owned: the spec, the rationale companion, this artifact) matches the
diff exactly — there is no file in the diff a builder is permitted to write. Reviewing this
as a Worker-1-authored pass with an independent Worker-3 audit does not weaken
`BUILD.md` `### Isolation is non-waivable`.

### High:

#### Decision 8's exhaustive-retention preamble asserts "no consumer-owned mutable container", which the boundary does not hold

`docs/spec-045-visibility_boundary-0_0_14.md` #"What the sealed query still shares with the
candidate, exhaustively." (Decision 8) opens with:

```docs/spec-045-visibility_boundary-0_0_14.md:488
**What the sealed query still shares with the candidate, exhaustively.** The
sealed query holds no consumer-owned AST node and no consumer-owned mutable
container. What it shares is:
```

The second clause is false, and the list's own fourth bullet is what falsifies it: the
retained bound-value slot is retained *whole*, so anything in it — a mutable container
subclass included — survives by identity. Verified mechanically with a read-only probe
against HEAD (`docs/builder/temp-tests/r1/probe_mutable_container_retention.py`, no source
mutation, nothing written outside `temp-tests/`):

```text
list-subclass payload -> defect: None
  same object: True type: HostileList
  post-seal mutation visible in sealed query: [1, 2, 3, 99]
plain-dict payload -> defect: None
  same object: False type: dict
```

The reading behind it: `::_expr_graph_defect` reaches a `Value` node, validates it as
genuine, checks only `_EXPRESSION_SEQUENCE_STATE_ATTRS`
(`source_expressions` / `cases` / `targets` / `sources`) in
`::_expression_state_defect`, then iterates `get_source_expressions()`, which a `Value`
answers with `[]` — so the `value` slot is never validated. At reconstruction,
`::_reconstructed_value` rebuilds a payload only when it is `None`, in `_RETAINED_TYPES`,
an exact `tuple` / `frozenset` / `list` / `dict` / `set` / `bytearray`, or an
`::_is_reconstructable_node`; a `list` **subclass** is none of those, so it falls through
to `::_normalized_bound_value`, which returns unchanged anything descending from no
`_BOUND_VALUE_NORMALIZERS` base and not an `enum.Enum`. A consumer-owned mutable container
therefore reaches the sealed query by reference and stays writable through the consumer's
retained handle after the seal returns.

Why it matters at High: this is the one sentence in the spec that tells a future reader
what the seal's ownership guarantee actually is, and it is the sentence a later round will
cite when deciding whether a newly reported retention is already covered. It is wrong
about a data-isolation boundary in exactly the direction that reads as safer than the code.
The code behavior is bounded by Decision 8's own threat model (a crafted object), so this
is a documentation defect, not a code defect the round owes a fix for.

Recommended change: narrow the preamble so the exception is stated where the claim is —
e.g. "The sealed query holds no consumer-owned AST node, and every mutable container
reachable through the validated query state is rebuilt. The one exception is the retained
bound-value slot below, which is retained whole, a container subclass included." No test
expectation: no behavior changes.

### Medium:

#### `(moved from the spec)` markings do not hold in either direction for four passages

`docs/spec-045-visibility_boundary-0_0_14-rationale.md` #"Provenance of this record" defines
*moved* as "text cut out of the spec in this pass". Verified against
`git show HEAD:docs/spec-045-visibility_boundary-0_0_14.md` (read into the session
scratchpad outside the repo, then `diff` / `grep` — no `git stash` / `checkout` /
`restore` / `worktree`). Four markings fail:

- Decision 5, *"Testing `_iterable_class` membership with `in` on a frozenset"* — marked
  *(moved from the spec)*. Nothing was cut: HEAD's only text on this is the contract clause
  `"never `in` on a frozenset which would hash the candidate"`, and that clause is **still
  in the current spec** at Decision 5. The `__hash__` / `__eq__` / metaclass reasoning the
  rationale gives never existed in the spec at all (`grep -n 'hash\|metaclass'` on the HEAD
  spec returns only the surviving clause and two unrelated lines). So this passage is
  reconstructed, and the spec kept its normative half.
- Decision 5, *"Resolving a pending `_deferred_filter` through Django's `QuerySet.query`
  getter"* — marked *(moved from the spec)*. `_filter_or_exclude_inplace` and
  `QuerySet.query` appear nowhere in the HEAD spec; the wording tracks
  `::_bake_deferred_filter_or_defect`'s docstring. Reconstructed.
- Decision 8, *"Retaining an admitted plain-data subclass by reference, since it defines no
  attribute hook"* — marked *(moved from the spec)*. `attribute hook` and `__conform__` are
  absent from the HEAD spec; HEAD's nearest text ("read through the base type's own
  descriptors so no subclass override runs during normalization") was **kept**, not cut.
  Reconstructed.
- Decision 1, *"Keeping the class-level method inventory and returning the consumer
  object"* — marked *(moved from the spec)*, and the HEAD `**Alternative rejected.**` block
  it replaces was indeed cut; but its distinctive sentence is still in the spec, nearly
  word for word, in `## Problem statement` ("an instance-shadowed `.all()`, a replaced
  instance-level `Query.chain`, and subclass `.filter()` / `_values` / `.first()` /
  `.__aiter__()` … erased the visibility predicate or returned synthetic rows *after* a
  class-level inventory had accepted the object"). By the file's own definition that makes
  it a copy, not a move.

Why it matters: the provenance ledger exists so a later auditor can re-derive what left the
spec. A marking that says *moved* where the text was reconstructed sends that auditor
looking for a cut that never happened, and a marking that says *moved* where the spec kept
the sentence hides a duplication. Recommended change: re-mark the first three
*(reconstructed)*, and for Decision 1 either mark the overlap explicitly (e.g.
*(moved from the spec; the `## Problem statement` narration of the same probes stays there)*)
or drop the duplicated sentence from the rationale and cite the Problem statement. The
`### Moved versus reconstructed ledger` above carries the same four mislabels and needs the
same correction.

#### The retained slot is named "an expression's own plain-data payload" in two places, but nothing proves it is plain data

`docs/spec-045-visibility_boundary-0_0_14.md` #"an expression's own plain-data payload,
`Value.value` being the instance" (Decision 8, fourth retention bullet) and
#"**One bound-value slot is retained rather than normalized**" (`## Constraints on the
supported query surface`, third bullet) both call the slot "an expression's own plain-data
payload". The whole point of the withdrawn claim is that this slot is reached by **no**
proof: `::_expr_graph_defect` never walks it and `::_normalized_bound_value` returns
anything without a plain-data base unchanged. Both probes above bound an object with no
plain-data ancestry at all (`Hostile`, `HostileList`) and the seal admitted them. Calling
the slot "plain-data" imports a guarantee from `::_direct_rhs_defect`, which is the rule
that specifically does **not** apply here — and Decision 8's next paragraph says so
explicitly, which makes the two readings contradict inside one decision.

Recommended change: name it for what it is in both places — "an expression's own bound-value
payload, unvalidated by the graph walk and unnormalized by reconstruction". The bullet's
following sentences already state that correctly; only the label is wrong.

### Low:

#### Chronology surviving in the spec

The four hedges the dispatch named are gone (`grep` for "Resolved after", "since adopted",
"supersedes", "was added after the `0.0.14` cut" returns nothing). Reporting what a full
chronology grep (`grep -nEi 'since |after the|previously|no longer|used to|formerly|resolved|
superseded|as of|round|was added|earlier|originally|has landed|already |post-`?0\.0\.14|
amend|retract'`) still surfaces, split by whether R1 introduced it:

*Pre-existing at HEAD, untouched by this round:*

- `## Problem statement` in full — narrates the pre-fix method-inventory design and the
  review that displaced it. Defensible as a problem statement; noted because it is what
  makes the Decision 1 sentence below readable.
- Decision 1 #"The boundary no longer validates a finite inventory of method overrides" —
  retraction-shaped: the reader must know what it once validated.
- Decision 3 #"Both runners previously skipped result normalization when the hook returned
  the exact source object it received. That fast path is gone" — same shape.

*Introduced by this round:*

- `Status:` line #"which describe the boundary as it now stands including its
  post-`0.0.14` hardening".
- Decision 2's `**Deliberation.**` pointer #"the three later rounds that added the
  properties above" — a round-count reference inside the spec.
- Decision 8's `**Deliberation.**` pointer #"the rejected revert of the post-`0.0.14`
  hardening".

None of the three new ones makes the reader reconstruct the contract — the contract is
stated in the present tense and these are pointers into the rationale — so this is Low
rather than a blocker. But `BUILD.md` `## Spec rationale extraction` asks for "nothing a
reader must apply a chronology to", and "the three later rounds" is a round index in the
spec. Recommended change: reword the two pointers without the chronology ("the later
property additions", "the rejected revert of the hardening"), and decide deliberately
whether the two pre-existing retraction-shaped sentences stay.

#### "Verbatim" is overstated for two rows of the `## Error shapes` wording column

`### Spec changes made (Worker 1 only)` edit 15 states "each default message in
`_visibility_result_error` verified to contain the spec's wording-column phrase verbatim".
Re-derived against `django_strawberry_framework/utils/querysets.py::_visibility_result_error`:
`type`, `table`, `untrusted` and `sliced` do contain their phrase verbatim; two do not.

- `projection` — spec: "composes over `<Model>` model rows, not a `.values()` projection";
  code: `"composes over {model.__name__} model rows, not a .values() / .values_list() (or
  custom-iterable) projection"`. The phrase is not contiguous in the message.
- `alias` — spec: "cannot re-route a pinned resolution; remove the `.using(...)` call";
  code: `"a visibility hook cannot re-route a pinned resolution. Remove the .using(...)
  call."` (sentence break, not a semicolon).

Both are semantically right, so the table is fine; the *claim* about it is what fails
`BUILD.md` `## Claims are proven mechanically, never accepted on prose`. Recommended change:
either soften the artifact's wording to "each phrase verified present or faithfully
abridged, with `projection` / `alias` abridged", or align the two table cells with the
message text.

#### `spec-045 Decision N` is the form of 38 of 41 in-source citations, not all of them

`docs/spec-045-visibility_boundary-0_0_14.md` #"cite them in the form `spec-045 Decision N`"
and the rationale's #"normalized every in-code review citation to the form `spec-045
Decision N`". Re-derived (occurrences, not matching lines, per `BUILD.md`
`## Claims are proven mechanically`): `grep -rEo "spec-045 Decision [0-9]+" --include="*.py" .`
= **38**; `grep -rEo "spec-045-visibility_boundary-0_0_14[^ ]* Decision [0-9]+"` = **3**, at
`django_strawberry_framework/optimizer/walker.py:383`,
`django_strawberry_framework/utils/querysets.py:2663`, and
`django_strawberry_framework/utils/querysets.py:2844`. 38 + 3 = the 41 the artifact states,
so the total is right and only the "every … in the form" phrasing is loose.

This is load-bearing for R3: those three citations embed the spec **filename**, so the
archive move must re-point them. `### Items deliberately left to a later round` flags only
the module docstring's path citation. Recommended change: say "38 in the short form
`spec-045 Decision N` plus 3 carrying the full filename", and add the three sites to the R3
note.

#### The `064` -> `045` renumber is unsourced in the chronology

`docs/spec-045-visibility_boundary-0_0_14-rationale.md` #"The comment-hygiene sweep of
2026-07-30 (`ff65666d`, `5a74d803`, `471d4c6b`) normalized every in-code review citation to
the form `spec-045 Decision N`". `git show ff65666d -- django_strawberry_framework/utils/querysets.py`
already emits `spec-045-…`, because the number itself was changed one commit earlier by
**`97dc05d7`** ("refactor(kanban): renumber cards so Done cards stay contiguous", 064 ->
045). That commit is not named anywhere in either file. Nothing stated is false; the
sourcing is incomplete on the one fact a reader chasing "why 045?" needs. Recommended
change: name `97dc05d7` in `## Round chronology` note 2.

### DRY findings

- **The rationale re-narrates three mechanisms the spec now states, at roughly 60% textual
  overlap.** `docs/spec-045-visibility_boundary-0_0_14.md` Decision 2's new three-property
  block (#"Expression-owned state is proven before the accessor that reads it runs",
  #"Retained containers are proven by payload", #"A reference cycle is untrusted state")
  and `docs/spec-045-visibility_boundary-0_0_14-rationale.md` Decision 2's *Four-finding
  round, `bbd216fc`* bullets carry the same three narrations: `Case.get_source_expressions()`
  expanding `[*self.cases, self.default]` so a `list` subclass runs its iterator during the
  proof; an `int` subclass in `alias_refcount` having its arithmetic invoked by downstream
  `.filter()` composition and rewriting the accepted `where` tree; the three-state walk
  distinguishing a cycle from a shared diamond. The rationale's genuinely non-duplicative
  content is the *round attribution* and the *why a narrower reading does not supply it*;
  the mechanism belongs to the spec. Recommended change: compress each rationale bullet to
  its attribution plus its deliberative delta and point at the spec property by name. Low
  severity — this is prose, and the rationale is not read on the hot path of implementation
   — but it is the same failure mode `## Spec rationale extraction` warns about, inverted.
- No other duplication found. The `Value.value` retention genuinely appears in three
  different jobs (spec contract, rationale history, routed finding), as the artifact's own
  DRY note argues.

### Existence challenge

Not raised. The rationale companion is mandated by `BUILD.md` `## Spec rationale
extraction`, and it earns its bytes: eight decision-keyed entries, every one naming its
decision by heading **and** a resolving anchor, carrying rejected alternatives with the
reason each lost, per-round change history, and a `Claims it may no longer make` section
that is where the withdrawn `Value.value` claim is recorded. Deleting it would put the
deliberation back in the contract. The DRY finding above is a trimming recommendation, not
a deletion candidate.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` — empty (0 lines). `__all__` and the
re-export list are unchanged. No source file is in the diff at all.

### CHANGELOG sanity

Not applicable; slice did not modify `CHANGELOG.md` (confirmed by `git diff --stat --
CHANGELOG.md`, empty).

### Documentation / release sanity

The round modifies documentation surfaces, so this applies.

- **Mechanical checks re-run rather than trusted.**
  `uv run python scripts/check_trailing_commas.py --check docs/spec-045-visibility_boundary-0_0_14.md
  docs/spec-045-visibility_boundary-0_0_14-rationale.md docs/builder/bld-045-r1-rationale_reconciliation.md`
  — exit **0**.
  `uv run python scripts/check_spec_glossary.py --spec docs/spec-045-visibility_boundary-0_0_14.md`
  — exit **0**, "OK: 9 terms - all have glossary entries and at least one spec link."
- **Byte counts re-derived**, since the artifact states them: HEAD spec 35,349; current
  spec 39,669; rationale 35,970 (`wc -c`). All three match the artifact exactly.
- **Link conventions, checked independently.** Both `.md` files carry one
  `<!-- LINK DEFINITIONS -->` block with all ten canonical group headers in the fixed
  `START.md` order; every def is alphabetical within its group; every def target exists on
  disk at the path claimed from that file's directory; **no unused defs**; every in-page
  `](#…)` anchor in the spec resolves to a spec heading; every `#fragment` in the
  rationale's defs resolves — 8/8 spec-decision anchors and 2/2 `GLOSSARY.md` anchors —
  and each of the eight literal `(`#decision-N--…`)` strings printed in the rationale's
  prose resolves too. `grep -cE '[\w/]+\.py:[0-9]+'` on both files: **0** raw `path:NN`
  refs (the form appears only in this artifact, which is licensed).
- **Decision headings preserved.** All eight `### Decision N — …` headings survive the
  reconciliation unrenamed, so the 41 in-source `spec-045 … Decision N` citations and the
  spec's own in-page anchors still resolve. This is the right call and the reason is
  correctly recorded.
- Card IDs, version strings and shipped statuses in the spec are unchanged and consistent
  with `DONE-045-0.0.14` / `0.0.14`. No KANBAN movement, no archival, no script-rendered
  doc regenerated in this round — all correctly deferred to R2 / R3.

### What looks solid

- **The withdrawn `Value.value` claim is right, and I reached the same conclusion
  independently.** See `### Temp test verification` for the reading and the probe. Deleting
  the "closed by normalization" claim rather than moving it is the correct disposition under
  `worker-1.md` rule 2: a falsified sentence belongs in neither file, and recording *that*
  it was withdrawn (rationale Decision 8, `Claims it may no longer make`) is history.
- **The `## Error shapes` ordering exception is real and correctly located.**
  `::_seal_or_defect` runs `type` (`isinstance` gate) -> `table` (`_concrete_or_none(qmodel)`
  on the public model) -> `untrusted` (`type(query) is not sql.Query`) -> the walk, whose
  `table` therefore lands *after* an `untrusted` — exactly the stated exception, and the
  symbol's own docstring states it in the same terms. **No second exception exists**: I
  checked the one candidate, a child `alias` defect escaping early from
  `::_sealed_prefetch_related_lookups`, and it is re-coded as `untrusted` before it leaves
  (`f"{cls_name} prefetch {lookup!r} queryset cannot be sealed ({code}: {detail})"`), so
  `sliced` / `projection` / `alias` still run in the declared order on the outer query.
- **The new normative contract added to the spec is accurate line by line where I checked
  it semantically** (list below), including the two clauses that are easiest to get subtly
  wrong: `::_concrete_or_none`'s class-ness-before-metadata order, and
  `::_queryset_state_defect`'s per-field exact shapes, which match the spec's new Decision 1
  paragraph field for field.
- **Sourcing discipline is honest in both directions.** Every commit the rationale cites
  does what it is said to do (checked below), and the refusal of the plan's "nine
  adversarial review rounds" is a real refusal, not a hedge: `git log --follow` over
  `django_strawberry_framework/utils/querysets.py` since 2026-07-15 lists exactly
  `1dd9273a`, `60998b17`, `49b66922`, `8af55482`, `97dc05d7`, `ff65666d`, `5a74d803`,
  `471d4c6b`, `bbd216fc`, `dfa86f90` — **no sourced round is silently dropped**, and no
  round index is invented. The correction was also written back into the build plan's R1
  description rather than left as a stale number.
- The `Value.value` finding is routed to the maintainer as contract-level rather than
  quietly fixed or quietly dropped, with the asymmetry against `::_direct_rhs_defect` named.
  That is the right routing.

**Spec claims verified semantically** (read the implementation, not just the symbol name):
`::_visibility_result_error` (all six codes and all six wording cells);
`::_seal_or_defect` (the whole defect ordering, the retained-state copy-forward set, the
`_hints` fresh-dict copy, the `require_shared_alias` symmetry including the `None`-outer
case, `is_sliced` / `_DJANGO_ITERABLE_CLASSES` identity membership);
`::_queryset_state_defect`; `::_concrete_or_none`; `::_base_table_defect` (alias-map read,
not the poisonable `base_table` cache); `::_query_container_defect` +
`::_query_payload_defect` (every one of the five payload shapes Decision 2 now lists);
`::_template_params_defect`; `::_expression_state_defect` +
`_EXPRESSION_SEQUENCE_STATE_ATTRS`; `::_GraphWalk` / `::_WalkState` /
`::_walk_short_circuit` (three-state cycle rejection); `::_expr_graph_defect`;
`::_lookup_operands_defect` / `::_direct_rhs_defect` / `::_rhs_hook_defect` /
`::_static_attr_present`; `::_normalized_bound_value` + `_BOUND_VALUE_NORMALIZERS`;
`::_reconstructed_value`; `::_reconstruction_defect`; `::_bake_deferred_filter_or_defect`
plus the guarded `PROHIBITED_FILTER_KWARGS` import; `::_sealed_prefetch_related_lookups` /
`::_rebuilt_prefetch_or_defect`; `::apply_type_visibility_sync` /
`::apply_type_visibility_async` (both "No identity fast path" comments, the unconditional
`::_normalized_visibility_result` call, the nested-awaitable rejection);
`exceptions.py::ConfigurationError` / `::SyncMisuseError`.

**Sampled at existence / citation level only** (not re-read semantically):
`optimizer/walker.py::_build_child_queryset` and
`optimizer/nested_fetch.py::unwindowable_child_queryset_reason` (the `allow_sliced`
threading), and the nine cited test names — all nine confirmed present as `def`s
(`tests/utils/test_querysets.py` x8 plus
`tests/test_connection.py::test_connection_query_chain_shadow_hook_is_sealed`), but their
bodies were not read.

**Commit sourcing spot-checked** (`git show --stat`, message bodies, and the
`utils/querysets.py` hunk where relevant): `1dd9273a` (2026-07-17, touches
`connection.py` / `permissions.py` / `querysets.py` and *creates*
`get_queryset-visibility-boundary-plan.md`, the "retained root note" — consistent with the
first-round attribution); `80527a36` (2026-07-17, does **not** touch
`django_strawberry_framework/utils/querysets.py`, only `tests/utils/test_querysets.py` and
optimizer tests — the rationale's correction of the root note's attribution is right);
`60998b17`; `49b66922` (its message carries the 99.95% coverage note and "per maintainer
direction" verbatim, which is where the rationale's sentence comes from — a sourced
historical fact, not a worker-measured number); `8af55482` (its 11-line `querysets.py` hunk
is exactly the guarded `PROHIBITED_FILTER_KWARGS` import the rationale attributes to it);
`bbd216fc`; `dfa86f90` (its message carries the 830-row live tier, the 1.7x / 2.3x cost, the
`extra`-mapping finding and the `get_source_expressions()` operand change — every one of the
rationale's attributions to it); `ff65666d` / `5a74d803` / `471d4c6b`; `6a86d21f`
(the 0.0.14 joint cut).

### Temp test verification

- `docs/builder/temp-tests/r1/probe_value_retention.py` — read-only probe (no source
  mutation; the Worker 3 source carve-out was **not** used, so no revert is owed). Run as
  `DJANGO_SETTINGS_MODULE=config.settings PYTHONPATH=examples/fakeshop uv run python …`:

  ```text
  defect: None
  annotation type: Value
  annotation node is the SAME object: False
  value is the SAME object: True
  value type: Hostile
  ```

  **My independent conclusion on the withdrawn claim: Worker 1's deletion is correct.** An
  opaque object bound as `Value(<obj>)` survives the seal by reference. The reading:
  `::_expr_graph_defect` proves the `Value` node genuine, runs
  `::_expression_state_defect` over `_EXPRESSION_SEQUENCE_STATE_ATTRS` only — `value` is
  not in that tuple — and then, because `Value` is not a `Lookup`, iterates
  `get_source_expressions()`, which for a `Value` is empty, so the `value` slot is never
  walked. Reconstruction then rebuilds the `Value` node itself (the probe shows the node is
  a fresh object) but routes the payload to `::_normalized_bound_value`, whose `for … else`
  falls through `_BOUND_VALUE_NORMALIZERS` and the `enum.Enum` arm and `return value`
  unchanged for anything descending from no plain-data base. `::_direct_rhs_defect` — the
  rule that *would* have rejected this shape — is reached only from
  `::_lookup_operands_defect`, i.e. only for a `Lookup` right-hand side, which is exactly
  the asymmetry the routed Finding 1 names. So the residual is live, and the spec is right
  to state the retention instead of claiming it closed.
- `docs/builder/temp-tests/r1/probe_mutable_container_retention.py` — the extension of that
  probe that produced the High finding above (a `list` subclass in the same slot is
  retained by identity and post-seal mutation is visible in the sealed query; a plain
  `dict` in the same slot is correctly rebuilt).
- Disposition: both kept as temp probes only, under `docs/builder/temp-tests/r1/`
  (gitignored). Neither is promoted: neither catches a code defect this round owes — the
  behavior is inside Decision 8's declared threat model and Finding 1 already routes the
  contract question to the maintainer — and the first probe merely reproduces what Worker 1
  already recorded. If the maintainer resolves Finding 1 by closing the asymmetry, the
  second probe is the shape the permanent test should take, and that pass owes its own
  failability proof.

### Notes for Worker 1 (spec reconciliation)

- **High, spec edit required.** Decision 8's exhaustive-retention preamble
  (`docs/spec-045-visibility_boundary-0_0_14.md` #"The sealed query holds no consumer-owned
  AST node and no consumer-owned mutable container") must be narrowed; see the High finding
  for the probe, the reading, and a suggested wording.
- **Medium, spec edit required.** Rename the retained slot in both places it is described
  (Decision 8's fourth retention bullet and `## Constraints on the supported query surface`
  bullet 3): it is not "plain-data", nothing proves it is.
- **Medium, rationale edit required.** Re-mark the four provenance failures listed under
  Medium, in the rationale's per-passage marks **and** in this artifact's
  `### Moved versus reconstructed ledger`.
- **Low, your call.** The three new chronology references this round introduced into the
  spec, and whether the two pre-existing retraction-shaped sentences (Decision 1, Decision
  3) stay. Both readings are defensible; a decision beats an oversight.
- **Low, artifact edit.** Soften the "verbatim" claim in edit 15, or align the `projection`
  / `alias` table cells with the message text.
- **Low, hand to R3.** Add the three filename-bearing citations
  (`optimizer/walker.py:383`, `utils/querysets.py:2663`, `utils/querysets.py:2844`) to
  `### Items deliberately left to a later round`, and correct "in the form `spec-045
  Decision N`" to 38 short + 3 long.
- **Low, sourcing.** Name `97dc05d7` (the 064 -> 045 renumber) in the rationale's
  `## Round chronology` note 2.
- **Escalated (contract-level; agreeing with the round's own routing).** Finding 1's
  `Value.value` asymmetry against `::_direct_rhs_defect` is a maintainer decision, not a
  worker's. My probe confirms it and additionally shows the retention is not limited to
  opaque scalars — a **mutable container subclass** reaches the sealed query the same way,
  which strengthens the case for routing an expression's own payload through
  `::_direct_rhs_defect` + `::_normalized_bound_value`. Resolution paths: (a) route the
  payload through the direct-lookup rule, a code change owing its own failability proof;
  (b) accept the asymmetry as deliberate under the threat model and leave the spec's
  (corrected) retention statement as the record. Either way Decision 8's retention
  paragraph is the sentence that moves.
- **Not a finding, recorded.** The rationale states the module "sat at 99.95%" during the
  raw-SQL round. That is a historical fact quoted from `49b66922`'s own commit message, not
  a worker measurement, so it does not collide with `BUILD.md` `## Coverage is the
  maintainer's gate` the way the spec's removed "is at 100% coverage" did. I verified the
  message; no change needed.

### Review outcome

`revision-needed`. Unresolved findings: one High (Decision 8's "no consumer-owned mutable
container" preamble is false, proven by probe), two Medium (four `(moved from the spec)`
provenance markings do not hold; the retained slot is mislabelled "plain-data" in two
places), and five Low (surviving/newly-introduced chronology; the overstated "verbatim"
wording claim; the 38-vs-41 citation-form claim plus the three filename-bearing citations
R3 must re-point; the unsourced `97dc05d7` renumber) plus one DRY finding (the rationale
re-narrates three Decision 2 mechanisms the spec now states). Nothing outside R1's declared
ownership was written, no boundary or runtime code is in the diff, and every mechanical
gate the round claimed was re-run and passed.
