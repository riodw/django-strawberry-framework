# Build: Cross-slice integration pass — 029 (consumer_dx_cleanup / 0.0.9)

Spec reference: `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` (whole file) and its companion
`docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` (whole file)
Status: final-accepted

This is a Worker-1-only pass (`BUILD.md` `## Cross-slice integration pass`). There is no Worker 2 and
no Worker 3 dispatch: the pass's writable surface is the two spec-family files plus a non-executable
edit to one `.py`, and `## Spec reconciliation` makes Worker 1 the only role permitted to mutate the
first two. Both the plan and the record of what was performed are below.

---

## Plan (Worker 1)

### Scope declarations

- **Hot-path declaration: `none`.** Two documentation files and one `.py` comment; zero executable
  lines change, proved rather than asserted (`### The executable bytes are unchanged`).
- **Floor-verification scope: `none`.** No Django / Strawberry / channels seam is touched. A comment
  and two prose files cannot diverge across framework or interpreter versions.
- **Failability proofs: `none` — the dismissal is recorded, not manufactured.** `BUILD.md`
  `### What needs a proof, and what does not` scopes the obligation to a **new boundary, guard, gate,
  or rejection path a slice introduces**. This pass introduces none: it corrects prose and one comment
  describing boundaries that already exist and are already pinned. Manufacturing a proof for a comment
  is the ritual that makes the real ones unaffordable. The obligation this pass *does* owe is the
  inverse one (`## Claims are proven mechanically, never accepted on prose`, third shape), and it is
  discharged below with all five control rows.
- **Coverage:** no `--cov*` flag in any command of this pass. No `pytest` was run — see
  `### Why no test was run`.

### DRY analysis

**Helper inventory checked — for the whole package.** Reused the inventory refreshed at Slice 4's
planning pass (`docs/shadow/helper-inventory.md`, 217,615 bytes over
`django_strawberry_framework/`), and it is current: `django_strawberry_framework/`'s executable bytes
are unchanged since it was generated, which the AST identity proof below establishes for the one
package file this cycle touched and `git status --porcelain -- django_strawberry_framework/` (one
entry, `types/base.py`) establishes for the rest. Shapes searched: `selected_meta`, `unknown_fields`,
`validate.*targets`, `normalize_sequence`, `optimizer_hints`. Relevant candidate found and judged:
`types/base.py::_validate_optimizer_hints` — see `### DRY: the one recorded, not-dispatched candidate`.

- **Existing patterns reused.** The `_validate_meta` comment correction reuses the shipped order
  vocabulary already carried by four other surfaces (three spec statements, the repaired docstring),
  word for word, so the agreement is checkable by `grep -cF` rather than by impression. The companion
  correction reuses that file's own plain-`code-span` convention for `types/base.py::symbol` (its
  `:242` and `:244` bullets), so no link definition is added and no ordering question arises.
- **New helpers justified.** None. Two documentation files and one comment.
- **Duplication risk avoided.** The dominant one here is **fixing a site instead of a population**.
  Every one of this pass's three edits was preceded by a population enumeration on a vocabulary
  disjoint from the one the finding was handed down in, and one of the three enumerations grew the
  population by a site nobody had named (`### Obligation 2`).

### Required reading, performed

`AGENTS.md`, `START.md`, `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`,
`docs/builder/worker-1.md`, `docs/builder/worker-memory/worker-1.md`, `GOAL.md` (read for this
cycle's surfaces: `:157`/`:161` carry the singleton-factory form, `:513` the `extensions=` migration
recipe — nothing this cycle falsifies), `docs/GLOSSARY.md` (the three entries this card owns, read in
full: `## Meta.nullable_overrides`, `## Meta.required_overrides`, `## Schema introspection management
command`), `CHANGELOG.md` (the `0.0.9` block and the `0.0.7` entries Slice 2 routed), the active spec,
the rationale companion, `docs/builder/build-029-consumer_dx_cleanup-0_0_9.md`, and — per
`## Cross-slice integration pass` step 1, with no "as needed" — **all four** prior artifacts in slice
order: `bld-slice-1-029-rationale_extraction.md` (862 lines),
`bld-slice-2-029-extensions_forbidden_form_repair.md` (2,674),
`bld-slice-3-029-spec_reconciliation.md` (1,785),
`bld-slice-4-029-docstring_rot_repair.md` (1,661).

Not read, per `worker-1.md` `## Required reading` "Forbidden reads": `worker-0.md`, `worker-2.md`,
`worker-3.md` memory files.

### Spec status-line re-verification (every Worker 1 spawn)

`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:1-11` re-read in full. The title, the shipped-in
banner, `Status: **SHIPPED (0.0.9)**`, the Owner line, the `Predecessors:` line, and the line-11
rationale-companion pointer all still describe the build's current state; the companion the pointer
names exists and resolves. **No status line was falsified by this pass and none was edited.**

### Implementation steps

1. Re-derive the companion `:245` population on a vocabulary disjoint from Slice 3's and Slice 4's,
   with a liveness control, before touching a byte.
2. Re-derive `_validate_meta`'s third enumeration and its claimed uniqueness structurally, and confirm
   the agreeing fourth site.
3. Re-verify all six rows of Slice 4's `### Docstring-to-spec agreement map` against the current bytes
   of both files, **raw and whitespace-flattened**.
4. Make the three edits; re-prove executable-byte identity by AST comparison with all four control
   rows; re-run every gate.
5. Walk the four artifacts' `What looks solid` / `DRY findings` / `### Notes for Worker 1` sections and
   assemble the deferred-work catalog raw material.

### Implementation discretion items

None. This pass has no second worker to delegate a choice to.

### Dispatched findings checklist

The integration pass has no spec `## Slice checklist`, so `BUILD.md` `### Dispatched findings
checklist` applies. One box per routed obligation plus the standard `## Cross-slice integration pass`
checks. Boxes are audited under `### Checklist audit`.

- [x] **O1** — the companion `:245` trailing parenthetical is false on disk and is corrected; the
      population is **enumerated**, not fixed as a list of sites, and is not re-inflated.
- [x] **O2** — `types/base.py::_validate_meta`'s third enumeration is corrected to the shipped order;
      its uniqueness and the agreeing fourth site are confirmed before the edit; executable-byte
      identity is re-proved by AST comparison with its controls.
- [x] **O3** — row A1's changed citation string resolves at exactly one occurrence on each side, and
      the retired spelling resolves nowhere on either.
- [x] All four `bld-*.md` artifacts read in slice order; every `What looks solid` / `DRY findings` /
      `### Notes for Worker 1` section walked for deferred follow-up.
- [x] The static inspection helper ran, or was explicitly skipped with a recorded reason, for every
      Python file with review-worthy logic this cycle touched.
- [x] **Repeated string literals** compared across every shadow overview for cross-file DRY candidates.
- [x] **Imports** compared across every shadow overview for dependency direction and boundary crossings.
- [x] The recorded-and-not-dispatched `_validate_optimizer_hints` DRY candidate is judged — this cycle
      or the catalog — with the reason recorded.
- [x] Tree-wide staged-anchor sweep for `TODO(spec-029` / `TODO-(ALPHA|BETA|STABLE)-029`, on a
      control re-derived by this pass rather than inherited.
- [x] Cross-slice coherence between spec, companion and source re-verified against **current** bytes.
- [x] Whether comments now tell one coherent story across everything this cycle touched.
- [x] Deferred-work catalog raw material assembled, with the two closures phrased as closures.

---

## Report of work performed (Worker 1)

### Instruments, and the controls that licensed each reading

Six readings this pass depends on would have been indistinguishable from a passing proof had the
instrument been broken. Each was controlled before it was believed, and **one of mine died silently
and was caught by its own oddity rather than by its output.**

1. **Deferred-docstring-claim sweep** (O1). Three instruments over the spec + companion, none keyed on
   the known site's wording: (a) artefact-noun x not-done-verb sentence co-occurrence, my own two word
   lists; (b) every parenthetical span of 40+ characters, filtered the same way; (c) symbol-anchored —
   any sentence naming `_selected_meta_targets` / `_validate_nullability_override_targets` /
   `types/base.py` together with a state word. Controls: positive (artefact noun alone) → **8** hits,
   negative (fabricated token) → **0**.
2. **Structural rule-order enumerator** (O2). `ast` + `tokenize` over **every** `.py` in
   `django_strawberry_framework/`, yielding every comment *run* and every docstring node — **3,074
   blocks** — then filtering to blocks naming both `relation` and a Relay-pk spelling and reporting
   their relative order. Keyed on the two concept words' **relative position**, which shares no
   vocabulary with Slice 4's rule-token-threshold and symbol-name passes.
3. **Agreement-map resolver** (O3). Occurrence counts **raw and whitespace-flattened**, separately.
   The flattened arm is not decoration: five of the six source-side rows read `raw=0` because docstring
   prose wraps, and a single-line `grep -cF` would have reported the agreement map broken. Controls:
   positive `Decision 8` → 11 / `def _selected_meta_targets` → 1, negative fabricated token → 0/0.
4. **Delimited-enumeration sweep** (coherence). Only spans where three or more of the five rule names
   appear separated by `/`, `->` or `,` — i.e. an actual list, not prose that happens to contain the
   words. Run over the spec, the companion, `types/base.py`,
   `management/commands/inspect_django_type.py`, and then tree-wide over all 693 corpus files.
5. **Link / anchor / definition validator.** Slug function keeps `_` (a `\w` character GitHub keeps) —
   the trap that killed three instruments earlier in this cycle. Controlled by injecting two faults
   into an in-memory copy of the companion (a definition pointed at a non-existent file, a fabricated
   in-page anchor): **both fired**, plus two collateral reports, against `0 problems` on the live files.
6. **Citation-breakage sweep.** Every `#"..."` citation in the
   `git ls-files --cached --others --exclude-standard` corpus (693 files, **717 distinct citations**),
   extracted from both raw and flattened text so a wrapped citation cannot read as absent, resolved
   against the post-edit files. Liveness control: **57** citations resolve into post-edit
   `types/base.py`, so a zero elsewhere is a measurement.

**My own dead instrument, disclosed.** My first attempt to run the five AST identity rows drove them
from a shell loop with the four anchor symbols in a variable. **zsh does not word-split an unquoted
variable**, so every row received one argument and died in `argv` unpacking. Four of the five rows
printed a traceback and would have been obvious; the fifth, the anchor control, printed exactly the
`ABORT: anchor ... absent` line it is supposed to print, so a reader skimming for "the control fired"
would have read a non-run as a pass. It is the same hazard Slice 2's Worker 3 hit (`--numstat` through
an unquoted `$FILES` returning a clean zero) and the same hazard Slice 4's Worker 2 hit (four anchors
shell-quoted into one argument aborting all five rows). Third instance in one cycle, same shell, same
mechanism. The rows below are the corrected re-run with each anchor passed as a separate argument.

### Obligation 1 — the companion `:245` trailing parenthetical

**The claim, re-derived before acting.** `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md`
`## Decision 8`, the final bullet (**"Claim this Decision may no longer make: that the rejection order
is unknown, excluded, consumer-authored, relation, Relay-pk."**), ended with:

> (The helper's own docstring still lists the three per-name rules in the rev1 order; that is a
> source-comment defect outside this cycle's editable surface and is routed to the final gate's
> deferred catalog.)

All three clauses are false **on disk**, not prospectively. Verified at source rather than inherited:
`types/base.py::_validate_nullability_override_targets`'s docstring reads
`Check order: unknown -> excluded -> consumer-authored -> Relay-pk -> relation.` (1 occurrence,
flattened), so it no longer lists the rev1 order; the maintainer's fence for this cycle is spec files
and `.py` files, so the defect was inside the editable surface; and Slice 4 repaired it rather than
deferring it.

**The population is ONE sentence, enumerated on my own vocabulary and not re-inflated.** Instrument 1
above, three disjoint filters, over both files:

| Filter | Hits | Where |
|---|---|---|
| artefact-noun x not-done-verb, sentence-scoped | **2** | companion `:245`; spec `:562` |
| parentheticals of 40+ chars, same filter | **1** | companion `:245` |
| symbol-anchored x state word | **4** | spec `:9`, `:69`, `:97`, `:569` |

Read individually: spec `:562` is Definition-of-done item 5 stating that the command *ships with* a
module and class docstring — it makes no defect claim. The four symbol-anchored spec hits are
`ALLOWED_META_KEYS` / `DEFERRED_META_KEYS` set listings and the `Predecessors:` line; none asserts a
docstring defect. **Every filter lands on companion `:245` and nothing else.** Nothing anywhere
asserts the `_selected_meta_targets` caller-count defect at all, because companion `:244` already
names `Meta.filesystem_path_fields` as "the third caller" — confirmed by reading it, not inferred.

That reproduces Slice 3's final-verification count on a fourth vocabulary. The build plan's "at least
two passages" framing stays superseded and **was not re-inflated**.

**The correction.** The parenthetical is replaced by a clause stating the current truth on the same
sentence, so the bullet still says what claim the Decision may no longer make and now also says which
surfaces carry the shipped order:

> The spec lists the shipped order, and so do the two source sites that state it:
> `types/base.py::_validate_nullability_override_targets`'s docstring, which also carries the reason
> Relay-pk precedes relation, and `types/base.py::_validate_meta`'s target-check comment.

Written in the companion's own plain-code-span convention for `types/base.py::symbol` (matching its
`:242` and `:244` bullets), so no link definition is added and the within-group sort is untouched.
Delta **+26 bytes**, arithmetic exact: the removed span is 241 bytes, the added 267.

**Who quoted the retired text, measured before the edit.** Flattened containment over all 693 corpus
files, each of the three clauses separately: the only live surface is the companion itself. Every
other holder is a `docs/builder/` per-cycle scratchpad — `build-029-…md` and the four slice artifacts
— exempt under `START.md` "Temp artifact conventions" and closed to this pass in any case.

### Obligation 2 — `types/base.py::_validate_meta`'s third enumeration

**Confirmed at source before editing.** The site is
`django_strawberry_framework/types/base.py::_validate_meta`
#"(unknown / excluded / consumer-authored / relation / Relay-pk) need the". It is introduced by
"Target existence / scope checks", not by "Check order:", so it enumerates a **set** and **is not
false** — this is a coherence fix, exactly as routed.

**The uniqueness claim, re-derived structurally on my own instrument.** Instrument 2 above scanned
**3,074** comment runs and docstring nodes across all of `django_strawberry_framework/` and found
**5** blocks naming both `relation` and a Relay-pk spelling. Read individually:

| Site | Order | Reading |
|---|---|---|
| `management/commands/inspect_django_type.py::_resolve_row` #"A Relay-Node-suppressed pk wins over everything" | Relay first | **the agreeing fourth site**, confirmed: it documents the same relation-pk-on-a-Relay-type case with the same `OneToOneField(primary_key=True)` example |
| `optimizer/walker.py::_walk_selections` | relation first | different subject entirely — nested relation targets in the selection tree; asserts no precedence |
| `types/base.py::_validate_meta` (comment) | relation first | **the target** |
| `types/base.py::_selected_meta_targets` (docstring) | "non-relation" first | the per-name **union across three callers**, not one caller's order; `non-relation` is `_validate_relation_shape_targets`'s reject, a different rule from nullability's relation reject |
| `types/base.py::_validate_nullability_override_targets` (docstring) | Relay first | the repaired site |

So `_validate_meta`'s comment is the only remaining site **in the package** stating one validator's
per-name rules with relation before Relay-pk, and the fourth site agrees with the shipped order. Both
handed-down claims confirmed, on an instrument that shares no vocabulary with the two that produced
them.

**The edit**, Worker 2's recommended replacement text verbatim, a two-word swap with no line
re-wrapped:

```
-    # than in the target-validator. Target existence / scope checks
-    # (unknown / excluded / consumer-authored / relation / Relay-pk) need the
+    # (unknown / excluded / consumer-authored / Relay-pk / relation) need the
     # selected fields and run later in ``_validate_nullability_override_targets``.
```

**One scope note, recorded rather than glossed.** The prompt's writable list scopes this file to
"docstrings only", and this site is a `#` comment, not a docstring. It is named explicitly as the
obligation, quoted by its substring, and it is strictly *less* executable than a docstring — a comment
is invisible to the parser, where a docstring is at least an AST node. The constraint's purpose is
that no executable byte moves, and that is proved below rather than argued.

**And the population was wider than the module.** Extending instrument 4 tree-wide surfaced a site
nobody had named — see `### The cross-surface site the module-scoped sweeps could not see`.

### Obligation 3 — row A1's citation string, and the whole agreement map

Slice 4's final verification swapped `whose value is` -> `that targets` on both surfaces, so row A1's
citation string changed. **All six rows re-verified against the current bytes of both files**, raw and
flattened, because both files moved after the map was written:

| Row | Spec side | Source side |
|---|---|---|
| **A1** #"Every `Meta` key that targets a set of field names on the type validates through it" | **1** | **1** (raw 0 — the docstring wraps) |
| A1 anchor paragraph #"That unknown/excluded half is shared, not per-key." | **1** | — |
| A2 #"each caller keeps only its own per-name rules" / the five-entry per-name list | **1** | **1** |
| A3 the three-Decision citation | — | **1** |
| B1 DoD item 11 / Slice-checklist bullet / Decision 8 stage 2 | **1 / 1 / 1** | **1** (the docstring's `Check order:` line) |
| B2 #"It is checked **before** the relation rule, so a name that is both" | **1** | **1** (the reason clause) |
| B3 the `Raises:` enumeration order | (B1's order) | **1** |
| **retired** #"whose value is a set of field names" | **0** | **0** |

**Row A1 resolves at exactly one occurrence on each side and the retired spelling resolves on
neither.** Obligation discharged.

### The cross-surface site the module-scoped sweeps could not see

Slice 4's two enumerations were scoped to `django_strawberry_framework/` and answered a question about
the **module**. Running instrument 4 across the spec, the companion and the source found a **spec**
site of the same shape that no pass had named:

`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` `## Implementation plan`, the Slice-3 row's
test-count cell: *"unknown / excluded / consumer-authored / relation / Relay-pk reject; both-sets
collision reject"*. Like `_validate_meta`'s comment it enumerates a **set** (the test population), so
it is **not false** — and like it, it was the last site in its own file reading relation-before-Relay-pk
while three other enumerations in the same file read the other way. Same grade, same fix: a
same-length two-word swap, **+0 bytes**.

After it, the delimited-enumeration sweep over the two spec-family files and the two source files
returns **two** relation-first spans, both correct as written: companion `:245`'s deliberate quotation
of the retired claim (a bullet whose whole job is to name the order that may no longer be claimed),
and `_selected_meta_targets`'s three-caller union list.

**Tree-wide, the population is five live sites and this cycle's fence reaches two of them.** Measured
over all 693 corpus files, excluding the `docs/builder/` per-cycle scratchpads:

| Site | Disposition |
|---|---|
| `types/base.py::_validate_meta` comment | **fixed here** |
| `docs/SPECS/spec-029-…md` `## Implementation plan` Slice-3 cell | **fixed here** |
| companion `:245` | correct as written — it quotes the retired claim by design |
| `CHANGELOG.md:101` | out of fence -> catalog |
| `docs/GLOSSARY.md:1360` | out of fence, DB-generated -> catalog |
| `docs/README.md:120` | out of fence -> catalog |

All three out-of-fence sites read "unknown / excluded / consumer-authored / relation /
Relay-suppressed-pk **targets** … raise `ConfigurationError`" — a rejected-target **set**, so none is
false. They are the same coherence cohort and they belong in the catalog, not in a fence exception.

### A second stated population that does not re-derive: "the CSV is the only stale surface"

Slice 3's review and its `### DRY findings` record that
`docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-terms.csv` rows 44-45 are the last surface
carrying C1's retired *scalar-only* scope claim, on the ground that `docs/GLOSSARY.md` is already
correct. `docs/GLOSSARY.md` **is** correct (both override headings say "**non-relation** field
names"), and the conclusion drawn from it is still wrong: sweeping the whole corpus for the claim
rather than for the surfaces the finding named returns **three** live carriers, not one.

| Site | Text | Status |
|---|---|---|
| terms CSV `:44`, `:45` | "forcing a **scalar** field nullable … **scalar-only**"; "forcing a **scalar** field required" | known catalog item |
| `CHANGELOG.md:101` | "decouple a **scalar field's** GraphQL nullability …"; "**scalar-only**, and the override flips a choice field's generated enum nullability for free" | **new** |
| `docs/SPECS/spec-034-permissions-0_0_10.md:419` | "`Meta.nullable_overrides` is **scalar-only** (spec-029 Decision 10)" | **new**, and it is a cross-spec citation into a Decision this cycle renamed and restated |

The companion's three `scalar-only` occurrences (`:42`, `:284`, `:375`) are **correct as chronology** —
`:284` says in terms that the scope fixed for the shipping cut *was* scalar columns only and that at
`0.0.9` this was an accurate word; `:375` is inside the verbatim-moved Risks body quoting the rev1
preferred answer. A rationale file recording what a Decision used to say is doing its job.

`spec-034:419` is the one worth reading twice: its **conclusion** still holds — a non-nullable forward
FK cannot be forced nullable, because relation targets are still rejected — but the reason it cites is
a claim spec-029 Decision 10 no longer makes. All three sites are outside this cycle's fence
(`CHANGELOG.md` and any other spec are explicitly not to be touched; the CSV likewise). Routed, not
fixed, and Slice 3's narrower claim is corrected here as a superseding measurement rather than by
editing a closed artifact (`ARTIFACT.md` `## Re-pass sections`).

### The executable bytes are unchanged

The claim this pass owes (`BUILD.md` `## Claims are proven mechanically, never accepted on prose`,
"relocated, promoted, or carried over unchanged"). Instrument: an `ast.dump(include_attributes=False)`
comparison with docstrings stripped, written to a scratch path **outside** the repository, four
anchors passed as four separate arguments. Reference obtained read-only via
`git show HEAD:django_strawberry_framework/types/base.py`; no `git stash` / `checkout` / `restore` /
`worktree` at any point. Both control copies were rebuilt from **this pass's own post-edit file**, with
each substitution asserted to match exactly once and to change the file.

| Row | Candidate | Expected | Measured |
|---|---|---|---|
| **R0 — the claim** | pristine HEAD vs the post-edit working file | exit 0 IDENTICAL | **exit 0**, `sha256=8382eb52608bb1a0`, 118,250 chars |
| **R0b — this pass's own delta** | pre-edit disk (Slice 4's output) vs post-edit | exit 0 IDENTICAL | **exit 0**, same hash both sides |
| R1 identity | HEAD vs HEAD | exit 0 | **exit 0**, `sha256=8382eb52608bb1a0` |
| R2 **negative control** | HEAD vs a **further** docstring-only reword built from the post-edit file | exit 0 (the stripper is live) | **exit 0**, same hash |
| R3 **positive control** | HEAD vs the `relay_pk_name` / `is_relation` branch swap — the forbidden "fix the code to match the comment" | exit 1 DIFFERENT | **exit 1**, `sha256=5c5fed398dfc819e`, first divergence at char 96,924 (`If(test=Compare(left=Name(id='name'…comparators=[Name(id='relay_pk_name'` vs `If(test=Attribute(value=Subscript(value=Name(id='selected_by_name'`) |
| R4 anchor control | HEAD vs post-edit, bogus anchor | exit 2 ABORT | **exit 2**, `ABORT: anchor '_no_such_symbol_xyz' absent from reference dump` |

My independently-built branch swap reproduces Worker 2's and Worker 3's hash (`5c5fed398dfc819e`) and
divergence offset exactly, so four independently-constructed mutations are the same mutation.

**Length remains non-distinguishing, now in four serializations.** My swapped copy is **94,225 bytes
and 1,953 lines** — byte-identical *and* line-identical to the post-edit file — and its AST dump is
118,250 chars, the same count as the identical file's. `wc -c`, `wc -l`, an `ast.dump` char count and
(per Worker 3's pass) a token-stream length all pass the forbidden fix. Only the hash separates them.

**The forbidden fix was not taken.** Read at source: the loop in
`types/base.py::_validate_nullability_override_targets` still runs
`name in consumer_authored_fields` -> `name == relay_pk_name` -> `selected_by_name[name].is_relation`,
and the corrected comment now describes that order.

### Cross-slice coherence: spec, companion, and source now tell one story

This cycle corrected the same subject in three places across two slices, and the prompt's check is
whether they agree against **current** bytes. They do, and the agreement is mechanical:

- **Order.** Three spec statements (DoD item 11, the Slice-3 checklist bullet, Decision 8 stage 2),
  the repaired docstring's `Check order:` line, its `Raises:` clause, `_validate_meta`'s comment (this
  pass), and the `## Implementation plan` cell (this pass) all read
  `unknown -> excluded -> consumer-authored -> Relay-pk -> relation`. `inspect_django_type::_resolve_row`
  independently documents the same precedence. Nine surfaces, one order.
- **Reason.** Spec Decision 8 failure-mode rule 4 and the repaired docstring both give the *why*
  (a relation pk on a Relay-shaped type is reported with the Relay reason), so the order is
  non-arbitrary on both surfaces and a future reader cannot "tidy" it back from either one.
- **Scope predicate.** Row A1's phrase is now identical on both surfaces after Slice 4's L2 swap, and
  the retired spelling resolves nowhere on either.
- **The one deliberate disagreement** is companion `:245`, which must state the wrong order because
  its job is to name the claim the Decision may no longer make. Recorded so a future sweep does not
  "fix" it.

### Static inspection helper: confirmed for every Python file with review-worthy logic

`BUILD.md` step 2. Re-derived rather than accepted: the cycle's `.py` surface and its per-file
changed-line counts, from `git diff --numstat HEAD`.

| File | +/- | Helper | Basis |
|---|---|---|---|
| `django_strawberry_framework/types/base.py` | 14 / 11 | **ran** (Slice 4 plan + review; re-run by this pass) | under `types/`, a mandatory trigger |
| `tests/test_ci_governance.py` | 590 / 8 | **ran** (Worker 3, all four passes) | 50+ new lines outside the package |
| `tests/test_relay_connection.py` | 28 / 10 | skipped, reason recorded | outside the package, 28 added < the 50-line trigger |
| `tests/optimizer/test_extension.py` | 14 / 7 | skipped, reason recorded | the `optimizer/` trigger targets `django_strawberry_framework/optimizer/`, not a test directory of the same name |
| `tests/types/test_resolvers.py` | 2 / 1 | skipped, reason recorded | same, for `types/` |
| `examples/fakeshop/strategy_schemas.py` | 7 / 4 | skipped, reason recorded | under both thresholds |
| `examples/fakeshop/test_query/test_products_visibility_api.py` | 4 / 2 | skipped | under both thresholds |
| `tests/mutations/test_resolvers.py` | 4 / 2 | skipped | under both thresholds |
| `tests/forms/test_resolvers.py` | 2 / 1 | skipped | under both thresholds |
| `tests/mutations/test_write_transaction.py` | 2 / 1 | skipped | under both thresholds |

Every file is either covered by a run or by a recorded skip, and every skip's **conclusion** re-derives.
**One skip's stated reason does not**, and is recorded rather than routed: Slice 2's Worker 3 wrote
"The other six files are 2-8 changed lines each, all under both thresholds", but
`tests/test_relay_connection.py` is 28 added lines, not 2-8. The disposition is unaffected — 28 is
still under the 50-line trigger for a file outside `django_strawberry_framework/` — so the skip is
correct and the sentence describing it is not. No trigger fires and there is nothing to re-run.

`tests/mutations/test_operations.py` is the concurrent session's untracked file and is not this
cycle's surface.

### Repeated string literals, across every shadow overview

`BUILD.md` step 3. `docs/shadow/` holds exactly two overviews, one per file with review-worthy logic
(`django_strawberry_framework__types__base.overview.md`, regenerated by this pass;
`tests__test_ci_governance.overview.md`). Compared in full:

| `types/base.py` | `tests/test_ci_governance.py` |
|---|---|
| 4x `connection` / `filesystem_path_fields` / `optimizer_hints` / `total_count`; 3x `filterset_class` / `nullable_overrides` / `orderset_class` / `relation_shapes` / `required_overrides`, two long error strings; 2x `cursor_field` / `description` / `globalid_strategy` / `interfaces` and three message fragments | 4x `conftest.py`; 2x `permissions` / `contents` / `constructing lambda` / `bare class in a sequence` / `only-this-module` / `expected` / `/anything.py` / `planted_schema.py` |

**No literal appears in both. There is no cross-file DRY candidate on this axis.** Nor could this
cycle have created one: `types/base.py`'s executable bytes are HEAD-identical (R0), so every literal
in its column is pre-existing and was walked by Slice 4's review; the governance module's nine were
read individually by Worker 3 in passes 2, 3 and 4 and correctly left duplicated (in each case sharing
the literal through a constant would make the assertion restate the code it checks).

### Imports, across every shadow overview

`BUILD.md` step 4. `types/base.py` imports standard library, `django.db.models`, four `strawberry`
symbols, and ten `..`-relative package modules (`exceptions`, `optimizer.field_meta`,
`optimizer.hints`, `registry`, `utils.strings`, `utils.typing`, `.converters`, `.definition`,
`.relations`, `.relay`) plus three deliberate in-function imports (`filters.sets`, `orders.sets`,
`keyset`) that dodge the `types -> {filters,orders} -> types` load cycle. **Dependency direction is
one-way and unchanged by this cycle** — the import list is inside the executable bytes R0 proves
identical to HEAD.

`tests/test_ci_governance.py` carries **one** cross-folder import,
`from scripts.check_citations import SOURCE_TREES, iter_python_sources`, under a ten-line comment
naming the coupling. It joins four pre-existing `tests/ -> scripts/` imports, so it is not a new
structural boundary crossing. The two files import nothing from each other.

### DRY: the one recorded, not-dispatched candidate — judged

Slice 4's `### Notes for Worker 1` item 21 records `types/base.py::_validate_optimizer_hints` as a DRY
candidate: it performs its own unknown-name and not-in-selected-set checks inline instead of routing
through `_selected_meta_targets`, sharing only `_format_unknown_fields_error`. **Confirmed at source
before judging**, and confirmed live rather than dead: `_validate_optimizer_hints` has one caller
(`_validate_meta`), `_selected_meta_targets` has three, so neither is dead code and the
delete-and-trim answer does not apply.

**Ruling: the catalog, not this cycle — and it is a decided answer, not a default deferral.**

- **The shapes are not near-copies.** `_selected_meta_targets` derives its excluded set from *all*
  selected fields and reports through a caller-supplied `excluded_error` callable;
  `_validate_optimizer_hints` derives its from **selected relation names only**
  (`{f.name for f in fields if f.is_relation}`) and reports both errors through
  `_format_unknown_fields_error`. It also validates values (`OptimizerHint` instances) and returns
  nothing, where the seam returns `(selected_by_name, sorted_targets)` for the caller to iterate.
- **The common piece is already extracted.** `_format_unknown_fields_error` is what the two genuinely
  share, and they both call it. What remains is two short call sites of a shared formatter — the
  DRY-correct shape, not a violation.
- **Consolidating would widen the seam for one non-conforming caller**, parameterizing both the
  selected-name predicate and the error path, which trades a real duplication for a real abstraction
  cost.
- **The difference is load-bearing evidence.** It is precisely the measurement that made Slice 4's L2
  ruling non-arbitrary — no short, exact, non-enumerative predicate characterizes the seam's
  membership, because membership is defined by the call graph. Erasing the difference would delete the
  evidence for a settled ruling.
- **And it is out of this pass's reach in any case.** It is a pre-existing executable shape, untouched
  by this cycle's diff, and an executable consolidation is a code change beyond a comment — which
  routes to Worker 0 as a finding, never a self-made edit.

No other cross-slice duplication was found. Slices 1 and 3 touched only `docs/SPECS/**`, Slice 2 only
tests plus one example module, Slice 4 only docstrings, so the slices share no code surface at all;
the only shared *subject* is the override-validation seam, and that is the coherence check above.

### Staged-anchor sweep, on a control this pass re-derived

`grep -rEn 'TODO\(spec-029|TODO-(ALPHA|BETA|STABLE)-029' .`, excluding `KANBAN.md`, `KANBAN.html`,
`BACKLOG.md`, `.git` and `.venv`: **no live anchor.** Every hit is prose *about* the scaffold — the
spec's `## Implementation scaffolding & staging notes`, the companion's rev7 record and its
`### Documentation-coherence passes` entry, two sibling rationale companions' superseded-card
corrections (`spec-021`, `spec-022`, which discuss the pre-renumber `TODO-ALPHA-029` id), an archived
`docs/builder/DONE/` artifact, and the four slice artifacts' own records of this sweep.

**Two controls, both fired, neither inherited.** Relaxing the first arm to `TODO\(spec-[0-9]{3}` over
`.py` returns live anchors at `tests/test_connection.py:1592` (spec-033),
`tests/optimizer/test_walker.py:4888` and `tests/optimizer/test_extension.py:5342` (spec-035),
`tests/test_permissions.py:43` and `tests/mutations/__init__.py:3` (spec-036),
`django_strawberry_framework/filters/sets.py:1367` (spec-055) and two in
`django_strawberry_framework/optimizer/walker.py`. Relaxing the second arm to
`TODO-(ALPHA|BETA|STABLE)-[0-9]{3}` outside the three excluded board files returns hits in `TODAY.md`
and `tests/test_build_tree_md.py`. **So the zero for `029` is a measurement, not a dead regex.**

### Citation-breakage sweep

Instrument 6. **Exactly one** `#"..."` citation stops resolving because of this pass:
`#"(unknown / excluded / consumer-authored / relation / Relay-pk) need the"`, cited only in
`docs/builder/bld-slice-4-029-docstring_rot_repair.md` — the closed slice artifact that quoted the
defect it routed here. It is a per-cycle scratchpad, exempt under `START.md` "Temp artifact
conventions", and it is not this pass's to edit. The companion parenthetical was likewise cited only
by that artifact (twice), and the spec cell string was never cited at all. Liveness control: **57**
citations resolve into post-edit `types/base.py`.

`check_citations.py` reports `789 citations resolve` unchanged, which is the expected reading — it
scans `.py` files and `KANBAN.md` only, so it cannot see any of the above. That blind spot is a
standing catalog item.

### Why no test was run

No `pytest` invocation was made, and this is a decision rather than an omission. The pass's whole
`.py` delta is one comment; R0/R0b prove the executable bytes identical to both HEAD and Slice 4's
output, so no test could distinguish before from after. `AGENTS.md` rule 15 forbids `pytest` after
edits unless asked, and the full sweep is the final gate's, which runs after this pass. No `--cov*`
flag was used anywhere.

### Gates, re-run after the last edit

| Check | Result |
|---|---|
| `uv run ruff format django_strawberry_framework/types/base.py` | `1 file left unchanged` |
| `uv run ruff check --fix django_strawberry_framework/types/base.py` | `All checks passed!` |
| `uv run ruff format --check .` | **pass** — `429 files already formatted` |
| `uv run ruff check .` | **pass** — `All checks passed!` |
| `uv run python scripts/check_trailing_commas.py --check` | **pass** — exit 0, no output |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` | **pass** — `OK: 44 terms - all have glossary entries and at least one spec link.` |
| `uv run python scripts/check_citations.py` | **pass** — `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md).` |
| `git diff --check` | **pass** — exit 0 |
| non-ASCII bytes in `types/base.py` | **0**, by byte scan over all 94,225 bytes (not a grep) |
| lines over 99 / 110 in `types/base.py` | **18 / 1 at HEAD, 18 / 1 now** — none introduced |
| link / anchor / definition validator, both spec-family files | spec **113 defs / 483 uses / 40 headings**, companion **61 / 90 / 24** — `0 problems` each; 0 undefined uses, 0 unused defs, 0 unresolved in-page anchors, every def path disk-exists. Control fired |

**Write-mode ruff was scoped to this pass's own file, not run as `.`** — `ARTIFACT.md`
`### Validation run` requires it and a concurrent session's uncommitted work is live in this tree. The
deviation costs nothing here: the read-only repo-wide `ruff format --check .` reports all 429 files
already formatted, so a repo-wide write-mode run would have been a no-op.

Per Worker 3's control earlier in this cycle, `check_trailing_commas.py --check` validates the ten
canonical group headers and the scaffold but **not** the within-group sort. This pass added **no link
definition** to either file, so the block is byte-identical to the one Slice 3's review measured and no
ordering question arises.

### Churn attribution

By the build plan's ownership table, never by `git status`. This pass wrote exactly three files:
`django_strawberry_framework/types/base.py`, `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`,
`docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md`, plus this artifact and
`docs/builder/worker-memory/worker-1.md`. Everything else dirty is a prior slice's
(`docs/SPECS/appx/spec-004-…-rationale.md`, the eight Slice-2 `.py` files, `tests/test_ci_governance.py`)
or the concurrent session's (`docs/review/review-0_0_14.md`, four `docs/review/rev-*.md`,
`tests/mutations/test_operations.py`). **Nothing was reverted or tidied.**

Absent from the diff and verified clean: `docs/TREE.md`, `KANBAN.md`, `KANBAN.html`,
`docs/GLOSSARY.md`, `CHANGELOG.md`, `pyproject.toml`, `uv.lock`,
`docs/SPECS/appx/spec-029-…-terms.csv`, `examples/fakeshop/db.sqlite3`, `scripts/`, `.github/`.

`docs/TREE.md` is stale at HEAD and it is **not** this cycle's: copied to a scratch path outside the
repo and rendered there (`--md <scratch>`, so the tracked file was never written), the delta is exactly
two lines — `test_operations.py  # Tests for canonical mutation operation descriptors (operations.py).`
at `:515` and `:745` — both for the concurrent session's untracked module.
`git status --porcelain -- docs/TREE.md` is empty.

### Byte counts, measured, and the deltas decompose

| File | Before this pass | After | Delta | Lines |
|---|---|---|---|---|
| `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` | 153,973 | **153,973** | **0** | 717 -> 717 |
| `docs/SPECS/appx/spec-029-…-rationale.md` | 77,006 | **77,032** | **+26** | 459 -> 459 |
| `django_strawberry_framework/types/base.py` | 94,225 | **94,225** | **0** | 1,953 -> 1,953 |

Both zero deltas are same-length two-word swaps (`relation / Relay-pk` and `Relay-pk / relation` are
both 19 characters), which is stated rather than left to look like an unedited file. The companion's
+26 sums exactly: the removed span is 241 bytes, the added 267. Every "before" figure was re-measured
on disk at pass start and matches the prior pass's recorded close, so the records join with no
unverified hop. The spec's HEAD figure is unchanged at **170,042**
(`git show HEAD:<spec> | wc -c`), so the net against HEAD is **16,069**; the companion does not exist
at HEAD, as every prior pass recorded.

### Checklist audit

All twelve `### Dispatched findings checklist` boxes are `- [x]` and each was proved in this pass, not
inherited. No box is left `- [ ]`, so no deferral reason is owed under `### Spec changes made`.
O1/O2/O3 are audited in their own sections above; the nine standing checks each have a measurement
section of their own.

---

## Final verification (Worker 1)

### Failability and fail-open confirmations

- **The record exists for every new boundary this cycle introduced, and this pass introduced none.**
  Confirmed present across the cycle: Slice 1 recorded the dismissal in four passes with its
  `BUILD.md` citation; Slice 2 carries **thirteen** proof entries across four build reports (classifier
  arms 4/5 then 5/6, corpus spine 7, `_sweep_corpus` 2, reporter seam 2, oracle guard 4, the oracle's
  two mutations 2/2, the region contradictor 5, narrowings A/B 3/4) plus one end-to-end control
  correctly labelled a control, every entry carrying the mutation, the scope as run, the pre-mutation
  state, the failing node ids **listed**, collection/setup errors **separately at 0**, and a
  byte-compared revert — with **no zero-row entry anywhere**, so no `why 0` is owed; Slices 3 and 4
  recorded the dismissal with the same citation in every pass. My duty is confirming the record, and
  I have not written a fifth.
- **No fail-open shape landed.** Re-read rather than inferred from a green run. This pass's own diff
  contains no executable line at all (R0), so it can introduce none. The cycle's one executable
  addition, the governance pin, was read for the catalogued shapes at Slice 2's final verification and
  the reading still holds against the shipped bytes: `_committable_python_files` is fail-closed on a
  missing `git` and on a non-zero exit, and its empty-but-exit-0 answer is refused by
  `_unreported_required_files`; `_forbidden_optimizer_entries` calls `ast.parse` with **no**
  `try` / `except SyntaxError`, so an unparseable file errors its row rather than being silently
  skipped — the obvious fail-open in a source sweep, and it is absent.
- **No mutation is live.** `git status --porcelain -- scripts/ .github/ django_strawberry_framework/`
  shows only `types/base.py`; `scripts/check_citations.py` is absent from the diff entirely; R0 proves
  the one touched package file executably equals HEAD, which no live code mutation could survive. No
  scratch artifact of this pass sits inside the repository.

### Relocation / promotion claims, re-proved rather than accepted

`worker-1.md` `### Verifying relocation / promotion claims` — run the proof yourself. The cycle makes
three such claims and all three re-derive here:

- **Slice 1's "it is a MOVE, not a copy".** `Justification:` reads **0** in the spec against **12**
  `### Justification (moved from the spec)` headings in the companion; `Alternatives considered` **0**
  against **12**; `**Revision ` **0** in the spec.
- **Slice 2's "no assertion was weakened".** The eight migrated files' `--numstat` still totals
  **63 added / 28 removed = 91 changed lines**, the figure every prior pass measured, and the
  forbidden-form population re-derives at **0** across the gate's own corpus.
- **Slice 4's "zero executable-line changes".** R0 and R0b above, on a third independent
  implementation of the instrument, with all four control rows fired.

### Summary

The integration pass is clean and discharges all three routed obligations.

**O1** — companion `:245`'s trailing parenthetical was false on disk in all three clauses and is
corrected. The population was re-derived on three filters of my own vocabulary against a fired
liveness control and is **one sentence**, exactly as Slice 3's final verification measured on three
other vocabularies; the build plan's superseded "at least two passages" framing was **not**
re-inflated, and companion `:244` already names the third caller so nothing asserts the
`_selected_meta_targets` defect anywhere.

**O2** — `types/base.py::_validate_meta`'s third enumeration now reads the shipped order. Its
uniqueness was re-confirmed by a structural scan of **3,074** comment runs and docstring nodes across
the whole package, on a vocabulary keyed on the two concept words' relative position rather than on
either prior instrument, and the agreeing fourth site in `inspect_django_type::_resolve_row` was read
and confirmed. Executable-byte identity is re-proved against pristine HEAD **and** against Slice 4's
output, with the forbidden branch swap as the positive control — which is byte-, line- and AST-char-
identical in length to the correct file and separated only by hash.

**O3** — row A1's changed citation resolves at exactly one occurrence on each side, the retired
spelling on neither, and all six agreement-map rows re-verified against the files' current bytes, raw
and flattened.

Beyond the three, the pass found and fixed **one site no module-scoped sweep could see** — the spec's
`## Implementation plan` Slice-3 cell, the same shape as O2 one surface over — and corrected **two
stated populations that did not re-derive**: the relation-before-Relay-pk enumeration is five live
sites tree-wide, not one, and the retired *scalar-only* scope claim survives on three live surfaces,
not just the terms CSV. All the residue is outside the maintainer's fence and is routed to the catalog
below, in each case with the site, the text, and why it is not false.

**No cross-slice defect needs a code change beyond a comment**, so no consolidation loop through
Workers 2 and 3 is requested, and every gate is green.

### Final status

`final-accepted`.

### Spec changes made (Worker 1 only)

Cited by heading. Line numbers move; the anchors below are quoted substrings.

| File / heading | Change | Reason | Obligation |
|---|---|---|---|
| `docs/SPECS/appx/spec-029-…-rationale.md` `## Decision 8`, the **"Claim this Decision may no longer make …"** bullet (`:245`) | the trailing parenthetical routing the docstring defect to the deferred catalog is replaced by a clause naming the two source sites that state the shipped order | All three clauses were false **on disk**: the docstring no longer lists the rev1 order, the defect was inside the maintainer's spec-files-and-`.py`-files fence, and Slice 4 repaired it rather than deferring it. Population enumerated on three disjoint filters first: one sentence | **O1** |
| `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` `## Implementation plan`, the Slice-3 row's test-count cell | `unknown / excluded / consumer-authored / relation / Relay-pk reject` -> `… / Relay-pk / relation reject` | Not false — it enumerates the test population, a set — but it was the last enumeration in the spec reading relation-before-Relay-pk while three others in the same file read the other way. Same coherence grade as O2, one surface over, and no pass had named it because both Slice-4 enumerations were scoped to the package | cross-surface, found by this pass |
| `django_strawberry_framework/types/base.py::_validate_meta` #"(unknown / excluded / consumer-authored / relation / Relay-pk) need the" | the two-word swap to the shipped order, Worker 2's recommended replacement text verbatim | Not false (it is introduced by "Target existence / scope checks", so it enumerates a set) but the only remaining site in the package listing relation before Relay-pk. **This is a `#` comment, not a docstring** — recorded explicitly, with executable-byte identity re-proved by AST comparison rather than argued | **O2** |

**Status-line re-verification.** Performed at pass start; nothing falsified, nothing edited.

**Deferred boxes.** None. Every box in `### Dispatched findings checklist` is `- [x]`.

---

## Raw material for the final gate's `### Deferred work catalog`

Assembled per the artifact contract by walking every per-slice artifact's `What looks solid`,
`DRY findings` and `### Notes for Worker 1 (spec reconciliation)` sections, plus the build plan's
section D. `bld-final-029.md` is the catalog's only author; this section is its input, and Worker 1
there should re-derive any figure it quotes.

### Closures — work this cycle DID, which must not be written as deferred

`BUILD.md`'s catalog is for work deferred. A catalog entry that defers work the cycle actually did is
the same false-description defect this cycle exists to repair, so these three are stated as closures:

- **CLOSED by Slice 4 — `types/base.py::_selected_meta_targets` named 2 of its 3 callers.** Repaired,
  and repaired by *deleting* the caller enumeration rather than extending it: the docstring now states
  the seam's contract ("every `Meta` key that targets a set of field names on the type"), which cannot
  rot when a fourth key lands. Source: `bld-slice-4-…md` plan Decision 1.
- **CLOSED by Slice 4 — `types/base.py::_validate_nullability_override_targets`'s stated check order
  contradicted its own loop.** Repaired, with the reason clause added so the order is non-arbitrary,
  and the `Raises:` enumeration brought into the same order. Source: `bld-slice-4-…md` Defects 2 / 2b.
- **CLOSED by this integration pass — `types/base.py::_validate_meta`'s third enumeration**, and the
  spec's `## Implementation plan` cell that shared its shape. Both were coherence fixes, not
  falsehoods. Source: `### Spec changes made (Worker 1 only)` above.

One record correction the catalog should carry if it quotes Slice 4's citation figures: the citations
broken by that slice's diff are **one** (`#"The first half shared by"`) plus **one** from its final
verification (the retired `#"Every `Meta` key whose value is a set of field names …"` phrase), not the
"2 distinct" its first build report stated — and both live only inside that slice's own artifact.
This pass broke a third, likewise only in that artifact.

### Deferred — outside the maintainer's spec-files-and-`.py`-files fence

- **`docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-terms.csv` rows 44-45 still carry the retired
  scalar-only scope claim.** Row 44 twice ("forcing a **scalar** field nullable", "**scalar-only**,
  validated at type creation") and describes the apply mechanism as "via the `convert_scalar`
  `force_nullable` tri-state", the narrow half of what C2 widened; row 45 once ("forcing a **scalar**
  field required"). Source: `bld-slice-3-…md` `### DRY findings` and `### Notes for Worker 1` item 3.
  Licensing: the cycle's fence excludes the CSV explicitly.
- **`CHANGELOG.md:101` carries the same retired claim** — "decouple a **scalar field's** GraphQL
  nullability" and "**scalar-only**". *New in this pass;* it corrects Slice 3's recorded conclusion
  that the CSV is "the only stale surface left anywhere". Licensing: `AGENTS.md` rule 21 plus the
  maintainer fence keep `CHANGELOG.md` closed to this cycle.
- **`docs/SPECS/spec-034-permissions-0_0_10.md:419` says "`Meta.nullable_overrides` is scalar-only
  (spec-029 Decision 10)"** — a cross-spec citation into a Decision this cycle renamed
  (`Scalar-only scope` -> `Non-relation scope`) and restated. *New in this pass.* Its **conclusion**
  still holds (a non-nullable forward FK cannot be forced nullable, because relation targets are still
  rejected); only its cited reason is retired. Licensing: any other spec is out of fence.
- **Three standing docs enumerate the per-name rejection rules in the pre-repair order** —
  `CHANGELOG.md:101`, `docs/GLOSSARY.md:1360`, `docs/README.md:120`, each reading
  "unknown / excluded / consumer-authored / relation / Relay-suppressed-pk targets … raise
  `ConfigurationError`". *New in this pass.* **None is false** (each enumerates a rejected-target set,
  not an order), so this is the same coherence grade as the two sites fixed here. `docs/GLOSSARY.md` is
  DB-generated: the fix is an ORM edit plus a regenerate, never a hand-edit.
- **`KANBAN.md`'s `DONE-029` card body is stale in two ways.** `:3597` still names the **rejected**
  migration targets (`extensions=[DjangoOptimizerExtension]` class / `lambda: DjangoOptimizerExtension()`
  factory) as Slice 1's goal, both resolved *against* the card by Decision 3; `:3598` and `:3604` name
  the non-existent `examples/fakeshop/tests/test_commands.py` as Slice 2's test home, where the shipped
  tests are `examples/fakeshop/tests/test_inspect_django_type.py` and
  `tests/management/test_inspect_django_type.py`. DB-backed. Source: build plan section D; Slice 2's
  carry-forward.
- **`KANBAN.md:366` already carries an open, unrelated item** against `docs/GLOSSARY.md`'s
  `## Schema introspection management command` entry (it states no selector-rejection contract at all,
  while its sibling `## Schema export management command` does), filed by the `spec-022` residual
  cycle. Note it so this cycle is not read as having missed it; **do not duplicate the filing.**
- **`CHANGELOG.md:173`, `:184`, `:186`** carry `0.0.7`-era consumer snippets showing the deprecated
  instance form `extensions=[DjangoOptimizerExtension()]`. `:109` correctly *describes* the `0.0.9`
  migration and is fine as history. Source: Slice 2.
- **`tests/test_ci_governance.py`'s first docstring line under-describes the module** now that it
  carries a first-party-source pin ("Governance tests for the CI workflow definitions."). Rewriting it
  requires regenerating `docs/TREE.md`, where it renders at `:455` and `:681`, and CI runs
  `build_tree_md.py --check`. Recommended replacement recorded in Slice 2's Amendment 1. Licensing:
  `docs/TREE.md` is outside the fence.
- **`docs/TREE.md` is stale at HEAD by exactly two lines** (`:515`, `:745`), both for the concurrent
  session's untracked `tests/mutations/test_operations.py`. Re-verified read-only in this pass against
  a scratch copy. **Not this cycle's and not to be fixed here.**
- **`docs/bug_hunt/temp-tests/resolvers_async_parity/` holds four forbidden-form entries** (two bare
  class in `test_connection_and_mutation_async.py:206`/`:271`, two constructing lambdas in
  `test_async_probes.py:264`/`:294`). Gitignored scratch, outside the pin's corpus **by design** — a
  pin walking the filesystem indiscriminately would pass in CI and fail on a developer machine. Listed
  so its exclusion is not mistaken for a miss.
- **`docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md:239` carries a real
  `path #"substring"` citation that no longer resolves** —
  `docs/SPECS/spec-029-…md #"P1.1 — stale extension-lifecycle model"`. Slice 1's move relocated that
  string into the companion; the `spec-004` *companion*'s prose citation was repaired in-cycle under
  Worker 0's re-partition, but this archived per-cycle artifact was deliberately not. No gate sees it.
- **`docs/GLOSSARY.md`'s introspection entry owes three selector rejections, not two** — the
  `KANBAN.md:366` item above; kept as a separate line because the catalog reader will look for it by
  this description.

### Deferred — test coverage and instrument integrity

- **The Relay-pk-before-relation precedence is a shipped contract pinned by no test (Slice 4, L3).**
  Spec `## Decision 8` failure-mode rule 4 states it, the repaired docstring states it, the code holds
  it, and no fixture pairs a relation pk with a Relay-shaped type and an override, so no row fails if
  the precedence is lost. **Owed row:** a test naming such a pk in `nullable_overrides` and asserting
  the **Relay** message rather than the relation one. The fixture pattern already exists at
  `tests/optimizer/test_walker.py::test_plan_relay_id_projects_attname_when_pk_is_relation`
  (`OneToOneField(..., primary_key=True)`) and the assertion neighbourhood is
  `tests/types/test_base.py::test_override_relay_suppressed_pk_raises`. **Explicitly not
  harness-impossible.** Licensing: the gap is **pre-existing at HEAD** and no slice of this cycle
  introduced a boundary, so neither `BUILD.md` `### Acceptance rule: weakly pinned is revision-needed`
  nor `### Harness-impossible interleavings` applies — it is a catalog item, not `revision-needed`.
  `fail_under = 100` structurally cannot see it: both guards' statements are covered; what is unpinned
  is which wins when both are true.
- **ACCEPTED RESIDUAL, maintainer-facing — `tests/test_ci_governance.py` #"CORPUS_REGIONS = (" is
  unpinned.** Narrowing it fails **0** rows, and a same-arity substitution fails 0 rows while leaving
  the collected row count unchanged. Accepted as terminal by Slice 2's second final verification on a
  criterion that is structural and mechanically checkable: the constant has exactly one reader, that
  reader is a `parametrize` position, and no surviving assertion reads it as data — so narrowing it
  deletes rows rather than leaving a live boundary enforcing less, and no fix exists that is not
  subject to the identical edit. **The maintainer may overturn this**; the change would be inside
  `tests/test_ci_governance.py` and would inline the tuple into the decorator, which moves the
  narrowing target rather than removing it.
- **`types/base.py::_format_unknown_fields_error` enumerates its callers** and is currently complete
  and correct (`Meta.fields`, `Meta.exclude`, `Meta.optimizer_hints`, `nullable_overrides`,
  `required_overrides`, `filesystem_path_fields`, `relation_shapes`). It carries the same rot risk
  Slice 4's Decision 1 removed from `_selected_meta_targets`, and the argument for replacing it with a
  contract statement is already made there. Left alone deliberately.
- **`types/base.py::_validate_optimizer_hints` duplicates the unknown/excluded shape.** Judged in this
  pass and **declined for this cycle with the reason recorded** (`### DRY: the one recorded,
  not-dispatched candidate`): the shapes are not near-copies, the genuinely common piece is already
  extracted as `_format_unknown_fields_error`, consolidating would widen the seam for one
  non-conforming caller, and the difference is the measurement that makes Slice 4's L2 ruling
  non-arbitrary. Candidate for a future spec's DRY pass, not a residue of this one.

### Deferred — process and tooling blind spots

- **No gate validates a `path::Symbol` citation inside a `.md` file.** `scripts/check_citations.py`
  reports `712 in 426 .py files, 77 in KANBAN.md`; `docs/` is out of scope by design. The spec's ~25
  and the companion's ~6 `path::Symbol` citations are checked by a reviewer or by nobody, and a symbol
  rename breaks them silently exactly as the `#"substring"` class does. Open since Slice 3's first
  review. **This pass depended on that blind spot three times** — the O1 parenthetical, the O2 comment
  and the A1 phrase are all prose or comments no gate can see.
- **The `## Current state` observation-vs-prediction rule's generalization is unrouted.** Slice 3
  established that a vintage-framed section's licence covers dated **observations** of the pre-build
  repo and not **predictions** about what the build would do, and gave it a durable home in the
  companion's `### Documentation-coherence passes`. The rule is not spec-029-specific: any spec with a
  vintage-framed section meets it. `BUILD.md` / `worker-1.md` are outside this cycle's fence and are
  corpus-ratchet-bound, so this is a **maintainer proposal that must name the bytes it retires**, not a
  worker edit.
- **The underscore-stripping slugger trap killed three instruments in this cycle**, each author
  reaching for the same `` [`*_~] `` character class independently. `_` is a `\w` character GitHub's
  slugger keeps. It does not transmit by being written down — it transmits by a positive control on an
  **underscore-bearing** anchor. Worth one line wherever anchor-checking is described.
- **The zsh no-word-splitting trap killed a fourth**, this pass's included: Slice 2's Worker 3 lost a
  `--numstat` measurement to an unquoted `$FILES`, Slice 4's Worker 2 aborted all five identity rows by
  shell-quoting four anchors into one argument, and this pass drove the same five rows from a `for`
  loop whose `set -- $row` did not split. In every case a non-run read like a result. Pass path lists
  and anchors as explicit separate arguments, never through a variable.
- **`docs/builder/build-029-consumer_dx_cleanup-0_0_9.md`'s section C under-describes the cycle.** It
  lists nine divergences; Slice 3 discharged eleven, its final verification added a twelfth site, and
  this pass added a thirteenth. Worker 0's file; the artifacts are the complete record.
- **Slice 2's static-helper skip reason is imprecise for one file.** Worker 3 wrote "The other six
  files are 2-8 changed lines each"; `tests/test_relay_connection.py` is **28** added lines. The skip's
  conclusion re-derives (28 is under the 50-line trigger for a file outside the package), so no trigger
  fires and nothing needs re-running — only the sentence is wrong.
- **`tests/test_ci_governance.py`'s census fires on any untracked-but-not-ignored `.py` outside the
  corpus.** That is the gate doing its job, but in a repo worked by concurrent sessions one session's
  stray root-level `.py` can red another's suite. Recorded so the behavior is a decided answer rather
  than a surprise.

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
