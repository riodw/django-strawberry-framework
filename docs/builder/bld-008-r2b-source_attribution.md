# Build: R2b — source attribution and the finalize-first remedy

Spec reference: `docs/SPECS/spec-008-definition_order_independence-0_0_4.md`; the authorizing scope is
`docs/builder/build-008-definition_order_independence-0_0_4.md` `#### Maintainer decision 4` and
`#### Maintainer decision 8`, and the contract the message fix must match is
`docs/SPECS/spec-010-foundation-0_0_4.md #"No shipped helper auto-triggers finalization"`.
Status: final-accepted

R2b is the cycle's **only source-code diff** and runs the full unmodified worker chain
(Worker 1 plans -> Worker 2 builds -> Worker 3 reviews -> Worker 1 final-verifies).
`BUILD.md` `### Isolation is non-waivable` applies with no deviation.

## Plan (Worker 1)

### Baseline

Re-verified at the start of this pass, not carried from R2:

- `git status --short django_strawberry_framework/types/relations.py django_strawberry_framework/types/base.py django_strawberry_framework/testing/relay.py`
  -> **0 lines of output** (unit: porcelain status lines). All three files are clean at HEAD; R2b
  starts from an unmodified baseline, exactly as R2's note 1 recorded.
- `git status --short | wc -l` -> **43 entries** (unit: porcelain status lines), all attributable to
  concurrent sessions, including six transport-surface source files. **Never edit, never revert.**
- `uv run python scripts/review_inspect.py <file> --output-dir docs/shadow` run for all three files:
  exit 0 each. Required by `BUILD.md` `### When to run the helper during build` for any file under
  `types/`; run here even though the plan adds no logic, so the obligation is discharged rather than
  argued about.

### DRY analysis

**Helper inventory checked.** Refreshed package-wide (`django_strawberry_framework/`, not just
`utils/`) with the `worker-1.md` `### Package-wide helper inventory before helper planning` AST
command into `docs/shadow/helper-inventory.md` — **1,783 lines** (unit: inventory lines,
`wc -l docs/shadow/helper-inventory.md`). Shapes searched: `message`, `error`, `remedy`, `finalize`,
`attribution`, `comment`. Relevant candidates: **none**. Cross-checked against the only shared
error-fragment constants in this area —
`grep -rn "not finalized\|finalize_django_types() first\|_RELAY_NODE_GATE_LEAD =\|_RELAY_NODE_GATE_INHERIT_TAIL =" django_strawberry_framework/`
-> 4 hits: `types/base.py:119` / `:125` (the two Relay-Node gate fragments `testing/relay.py` already
imports), `filters/base.py:614` (a different message, different subject), and the target line itself
at `testing/relay.py:72`.

- **Existing patterns reused.** None needed. The two comment sites are prose; the message site is an
  inline f-string literal inside an existing `raise ConfigurationError(...)`.
- **New helpers justified.** **None.** The finalize-first remedy text has exactly **one** call site.
  A module constant for a single use is premature, and `types/base.py`'s two exported fragments exist
  only because `testing/relay.py` and `types/base.py` must emit the *same* Relay-Node gate text.
  **Condition that would change the answer:** a second site emitting a finalize-first remedy (a
  second helper in `testing/`, or the finalizer echoing it) — then extract one constant beside
  `_RELAY_NODE_GATE_LEAD` and import it, rather than copying the sentence.
- **Duplication risk avoided.** One risk, and the plan forecloses it: restating the always-defer
  invariant in `types/relations.py`'s docstring would duplicate the contract
  `types/base.py::_build_annotations` already states in full. The replacement text below names the
  *consequence* (the trap is closed) in one clause and leaves the mechanism where it lives.

### The attribution determination (do not re-derive; verify before writing)

Both comments credit `spec-014-testing_shift-0_0_4.md`, which owns neither object. Two different
specs are the correct owners, and **which one depends on what each sentence describes**.

Evidence, disk-verified this pass:

| Fact | Owner | Evidence |
|---|---|---|
| The `PendingRelation` dataclass and the registry methods that hold it | **spec-010** | `docs/SPECS/spec-010-foundation-0_0_4.md #"### \`PendingRelation\`"` (`:134-146`) defines the frozen dataclass field-by-field and states "Lives at `django_strawberry_framework/types/relations.py` (new)"; `#"### \`TypeRegistry\` extensions"` (`:148-168`) adds `add_pending_relation` / `iter_pending_relations`. The sentinel appears in spec-010's collection pseudocode as `_PendingRelationAnnotation` (`:263`). |
| The always-defer rule, and the closing of the import-order trap | **spec-018** | `docs/SPECS/spec-018-meta_primary-0_0_6.md` **H1** (`:13`) states it verbatim: "That misses the import-order trap where a *single* secondary type registers first ... Fix: **defer all relation annotations to finalization** regardless of registry state." Restated at `:137`, `:297`, `:525`. |
| Neither belongs to spec-014 | — | `grep -roF "import-order trap" docs/SPECS/ \| wc -l` -> **5 occurrences** (unit: occurrences, not lines — both counts agree at 5 here, `grep -rn ... \| wc -l` also 5), and `grep -rlF` shows they sit in **exactly one file**, `spec-018` (`:13`, `:137`, `:212`, `:297`, `:525`). `spec-010` never uses the phrase; `spec-014` never uses it. |

**The determination.**

- **`types/relations.py` module docstring -> spec-010, with one clause crediting spec-018.** The
  sentence's grammatical head is *the two scaffolding objects*, which are spec-010's deliverable —
  but its trailing modifier claims those objects *close the import-order trap*, and that is false as
  written: spec-018's H1 exists precisely because spec-010's eager-bind-or-defer shape **missed** the
  trap. Re-crediting the whole sentence to spec-010 would fix the pointer and keep a wrong claim.
  The replacement therefore splits the sentence: the objects are spec-010's, and routing every
  auto-synthesized relation through them *unconditionally* — spec-018's rule — is what closes the
  trap.
- **`types/base.py::_build_annotations` -> spec-018, single-token change.** That comment describes
  the removal of the eager-bind branch and names the trap directly. It is spec-018's H1 fix end to
  end; no other fact is entangled in it.

### Exact replacement text (Worker 2 implements, does not invent)

**Site 1 — `django_strawberry_framework/types/relations.py` module docstring.**

Replace exactly this (currently the docstring's second paragraph opening, through the words that
begin the following sentence):

```text
This module owns the two scaffolding objects that close the import-order trap
addressed by spec-014: ``PendingRelation`` (a frozen dataclass capturing a
relation field whose target ``DjangoType`` was not yet registered at collection
time) and ``PendingRelationAnnotation`` (the sentinel installed in
``cls.__annotations__`` until the target type registers). The producer is
```

with exactly this:

```text
This module owns the two scaffolding objects that carry a relation from
collection to finalization (spec-010): ``PendingRelation`` (a frozen dataclass
capturing a relation field whose target ``DjangoType`` was not yet registered
at collection time) and ``PendingRelationAnnotation`` (the sentinel installed
in ``cls.__annotations__`` until the target type registers). Routing every
auto-synthesized relation through them unconditionally is what closes the
import-order trap (spec-018). The producer is
```

Everything after `The producer is` is unchanged. Longest new line is 78 characters; ASCII only.

**Site 2 — `django_strawberry_framework/types/base.py::_build_annotations`.**

Replace exactly this line (12-space indent, the closing line of the always-defer comment block):

```text
            # the primary (the import-order trap closed by spec-014).
```

with exactly this:

```text
            # the primary (the import-order trap closed by spec-018).
```

One token. No other line in that comment block changes.

**Site 3 — `django_strawberry_framework/testing/relay.py::global_id_for`, the unfinalized branch.**

Replace exactly this:

```text
            "call finalize_django_types() (or build the schema) first - the "
            "GlobalID strategy is stamped at finalization.",
```

with exactly this:

```text
            "call finalize_django_types() first (directly, or by importing a "
            "schema module that calls it) - the GlobalID strategy is stamped "
            "at finalization.",
```

The preceding f-string line (`f"global_id_for: {definition.graphql_type_name} is not finalized; "`)
is **unchanged**.

Why this text and not another: the settled contract at
`docs/SPECS/spec-010-foundation-0_0_4.md #"No shipped helper auto-triggers finalization"` (`:65`)
states that `DjangoSchema`, `DjangoConnectionField`, and `DjangoNodeField` do **not** call
`finalize_django_types()` and that **the explicit consumer call is the only trigger**. So "build the
schema" names a non-remedy under its literal reading, and is correct only under the indirect reading
*import a schema module that conventionally calls the finalizer itself* — which
`examples/fakeshop/config/schema.py` does. The replacement keeps that genuine second route and says
what actually makes it work (the import runs somebody's explicit call), so the parenthetical names
two remedies that both work instead of one that does not.

**No spec name goes into the error string.** A spec pointer is for a comment, not for consumer-facing
output; the message names the remedy, the plan records which contract governs it.

### Implementation steps

1. Re-verify all three files are still clean at HEAD before editing
   (`git status --short <the three paths>` -> no output). If any is dirty, **stop and report** — a
   concurrent session has entered R2b's scope; never revert.
2. `django_strawberry_framework/types/relations.py` — apply Site 1 verbatim.
3. `django_strawberry_framework/types/base.py` — apply Site 2 verbatim (the comment block ending
   `#"the import-order trap closed by"` inside `types/base.py::_build_annotations`).
4. `django_strawberry_framework/testing/relay.py` — apply Site 3 verbatim (the `if not
   definition.finalized:` branch of `testing/relay.py::global_id_for`).
5. `uv run ruff format django_strawberry_framework/types/relations.py django_strawberry_framework/types/base.py django_strawberry_framework/testing/relay.py`
   then `uv run ruff check --fix` on the same three paths. **Scoped to these files only, never `.`**
   — 43 baseline-dirty entries are other sessions' work.
6. `uv run python scripts/check_trailing_commas.py --check` on the same three paths (ASCII-only and
   layout rules are `.py`-enforced and are not what `ruff format` checks).
7. `git status --short` after both ruff invocations: exactly these three paths may be newly modified.
   Anything else is a **stop-and-report**, never a revert.
8. Confirm the two surviving assertions still hold (below), then set `Status: built` **on the header
   line**.

Line numbers are deliberately absent from steps 2-4: every site is pinned by a unique substring or a
symbol path per `AGENTS.md` rule 27. Verify each `old_string` matches exactly once before editing.

### Test additions / updates

**No test change is in scope, and this is a measured result, not an assumption.**

Occurrence counts across all three test trees plus the package (unit: **occurrences** of the literal
substring, `grep -roF "<substring>" <tree> | wc -l` — occurrence-counting, not line-counting, because
a line-oriented count would miss a second hit on one line):

| Substring | `tests/` | `examples/fakeshop/apps` | `examples/fakeshop/test_query` | `examples/fakeshop/tests` | `django_strawberry_framework/` |
|---|---|---|---|---|---|
| `or build the schema` | 0 | 0 | 0 | 0 | **1** (the target itself) |
| `is not finalized` | 0 | 0 | 0 | 0 | 1 |
| `stamped at finalization` | 0 | 0 | 0 | 0 | 2 |
| `call finalize_django_types` | 0 | 0 | 0 | 0 | 2 |

**Nothing anywhere in the three test trees pins the changed substring.** That is itself worth
recording: a consumer-visible error string whose remedy clause no test asserts is exactly how a
remedy stays wrong through several releases.

**Two assertions do touch this message and must keep passing unchanged** — both assert only the
`finalize_django_types()` token, which the replacement preserves:

- `tests/testing/test_relay.py::test_global_id_for_unfinalized_raises` — asserts
  `"CategoryNode" in message` and `"finalize_django_types()" in message`.
- `tests/testing/test_relay.py::test_global_id_for_strategy_stamped_but_unfinalized_raises` — same
  two assertions after a Phase-3 failure.

**Constraint for Worker 2:** any wording that drops the literal `finalize_django_types()` from the
message breaks both rows. The prescribed text keeps it.

Focused scope to run (no `--cov*` flags, `BUILD.md` `## Coverage is the maintainer's gate`):

```shell
uv run pytest tests/testing/test_relay.py --no-cov
```

Temp/scratch tests: none appropriate. There is no behavior to demonstrate.

### Failability proofs — decided: NONE required

`BUILD.md` `### What needs a proof, and what does not` scopes the obligation to every **new boundary,
guard, gate, or rejection path** a pass introduces. **R2b introduces none.** Stated explicitly so
Worker 2 and Worker 3 do not improvise:

- Sites 1 and 2 are comment prose. No statement, no expression, no branch.
- Site 3 changes the **literal text of a message inside an already-existing rejection path**. The
  `if not definition.finalized:` gate, its condition, its exception class, and its position relative
  to the strategy read are all untouched. Rewording a boundary's message neither adds a boundary nor
  moves one; the same guard rejects the same inputs before and after.
- No fail-open shape is introduced or touched: no clamp, no `getattr` default, no `or` fallback, no
  bare `except`, no truthiness test on a possibly-absent value, no default reached from incoherent
  input. The diff contains no operator at all.

**Boundary count for the split question (`worker-1.md` `### Boundary count is a split trigger`): 0.**
No split; three edits in three files, each a single site, reviewable as one diff.

Worker 2 writes `None; this pass introduced no new boundary.` under `### Failability proofs` and
keeps the heading. Worker 3 audits that statement against the diff rather than re-deriving it.

### Hot-path budget — declared `none`

The build plan declares `Hot-path declaration: none` cycle-wide, and R2b is the only item that could
have falsified it. It does not:

- Sites 1 and 2 are comments, stripped before execution.
- Site 3's literal is constructed **only on the raise path** of `testing/relay.py::global_id_for`, a
  `testing/` helper for consumer test suites. It runs on no request, no resolver, no row, no
  connection, and no outbound message — and on the error path even there.

Worker 2 writes `Not applicable; plan declares no hot path.`

### Floor verification — declared `none`, **conditionally**, and the condition is stated

The plan declares `Floor-verification scope: none` and rests that declaration on R2b being
comment-and-message-only. `django_strawberry_framework/types/` **is** a Strawberry type-construction
seam and would ordinarily be in floor scope, so the `none` is not free:

- **The condition:** the `none` holds only while the diff changes **no executable line** — that is,
  nothing outside (a) docstring and comment prose and (b) the literal text of the one message inside
  an existing `raise`. No control flow, no condition, no signature, no import, no name. A diff
  meeting that condition behaves identically at Django 5.2.16 / Python 3.10 /
  strawberry-graphql 0.316.0 and at the shared `.venv`'s versions, so a floor run could not
  distinguish pass from fail.
- **The tripwire:** if the delivered diff touches any line outside that description, the `none`
  is falsified. **The item re-loops with floor scope declared** — the focused scope would then be
  `tests/types/test_definition_order.py` and `tests/testing/test_relay.py` at the floor, in an
  isolated scratch venv outside the repo, never the shared `.venv`. Worker 3 verifies the
  comment-and-message-only property as a review duty and records the verification; Worker 1
  re-confirms it at final verification before accepting the `none`.

Worker 2 writes `Not applicable; plan declares floor-verification scope none.`

### Collateral surfaces — checked, all negative

- **`docs/TREE.md` is rendered from module docstrings** and carries only each module's **first**
  docstring line. `relations.py`'s first line ("Pending relation records for
  definition-order-independent ``DjangoType`` finalization.") is **not** in the replacement's range,
  so TREE.md is unaffected. Verified: `grep -n "scaffolding objects" docs/TREE.md` -> **0 matching
  lines**; `grep -c "spec-014" docs/TREE.md` -> **0**. **Do not regenerate TREE.md.**
- **`docs/GLOSSARY.md` and `KANBAN*` are DB-generated and out of scope.** No DB row is read or
  written by this item.
- **`CHANGELOG.md` is closed** (`AGENTS.md` rule 21 and the plan's context flags). No entry.
- **Public surface:** `django_strawberry_framework/__init__.py` is not touched; `__all__` and the
  re-export list are unchanged. `testing/relay.py`'s own `__all__` is above the edit site and
  unchanged.
- **`grep -rn 'spec-014' django_strawberry_framework/` must return 0 hits after the pass** (it
  returns 2 now — the two comment sites). This is the item's mechanical acceptance test.

### Implementation discretion items

Assessed and decided as Worker 2's:

- The **editing mechanism** (one `Edit` per site vs. a single pass per file). The text is fixed; how
  it is applied is not.
- The **order of the three edits**. They are independent; no site consumes another's surface.

Nothing else. The replacement text is fixed by this plan, including punctuation and line wrapping,
because `#### Maintainer decision 4` exists precisely because a confident wrong attribution shipped
once already.

### Spec slice checklist (verbatim)

One box per edit site, quoting the authorizing decision. Boxes stay `- [ ]` at planning; **Worker 2
ticks a box only when that fix actually landed in its diff this pass**; Worker 1 audits every tick at
final verification.

- [x] `types/relations.py` #"addressed by spec-014" — per `#### Maintainer decision 4`: "the two scaffolding objects that close the import-order trap addressed by spec-014: `PendingRelation` ... and `PendingRelationAnnotation`" -> **spec-010** for the scaffolding, **spec-018** for the trap closure, per `### The attribution determination` above.
- [x] `types/base.py::_build_annotations` #"the import-order trap closed by spec-014" — per `#### Maintainer decision 4`: "The earlier eager-bind branch froze the relation against whichever type was already registered ... (the import-order trap closed by spec-014)." -> **spec-018**.
- [x] `django_strawberry_framework/testing/relay.py #"call finalize_django_types() (or build the schema) first"` — per `#### Maintainer decision 8`: "The parenthetical must name a remedy that actually works." Contract cited: `docs/SPECS/spec-010-foundation-0_0_4.md #"No shipped helper auto-triggers finalization"`.

### Scope fence (repeated because it is the whole item)

Writable by Worker 2: **exactly** `django_strawberry_framework/types/relations.py`,
`django_strawberry_framework/types/base.py`, `django_strawberry_framework/testing/relay.py`, and this
artifact. No spec, no rationale, no durable doc, no `KANBAN*`, no DB, no `CHANGELOG.md`, nothing under
`docs/review/` (open maintainer escalation), no other source or test file. No commit, no branch.
`git stash` / `git checkout` / `git restore` / `git worktree` are **banned** — concurrent sessions are
writing this tree; use `git show HEAD:<path> > /tmp/...` for read-only HEAD access.

---

## Build report (Worker 2)

All three sites landed verbatim as the plan prescribed. No wording was invented; no test changed.

### Files touched

Grounded in `git status --short` (below), not memory.

- `django_strawberry_framework/types/relations.py` — module docstring, Site 1. The single sentence
  crediting spec-014 is replaced by two facts: the scaffolding objects carry a relation from
  collection to finalization (**spec-010**), and routing every auto-synthesized relation through them
  *unconditionally* is what closes the import-order trap (**spec-018**). Verbatim from the plan's
  `### Exact replacement text`, 7 new lines. Everything from `The producer is` onward is byte-identical.
- `django_strawberry_framework/types/base.py` — `::_build_annotations`, Site 2. Single-token change
  `spec-014` -> `spec-018` on the comment line #"the import-order trap closed by". No other line in
  that comment block changed.
- `django_strawberry_framework/testing/relay.py` — `::global_id_for`, Site 3, the `if not
  definition.finalized:` branch. The message's remedy clause becomes
  `"call finalize_django_types() first (directly, or by importing a schema module that calls it) - the
  GlobalID strategy is stamped at finalization."`, re-wrapped across three source lines. The preceding
  f-string line is unchanged; the `raise`, its exception class, the gate, and the gate's condition and
  position are all untouched.

### Tests added or updated

**None.** The plan's measurement held on re-derivation: nothing in any test tree pins the changed
substring, and the two rows that assert this message assert only the `finalize_django_types()` token,
which the replacement preserves.

Re-derived occurrence counts (unit: **occurrences** of the literal substring, command
`grep -roF "<substring>" <tree> | wc -l` — occurrence-counting, not line-counting):

| Substring | `tests/` | `examples/fakeshop/apps` | `examples/fakeshop/test_query` | `examples/fakeshop/tests` | `django_strawberry_framework/` |
|---|---|---|---|---|---|
| `or build the schema` | 0 | 0 | 0 | 0 | **0** (was 1 — the site just changed) |
| `is not finalized` | 0 | 0 | 0 | 0 | 1 |
| `stamped at finalization` | 0 | 0 | 0 | 0 | **1** (was 2 — see below) |
| `call finalize_django_types` | 0 | 0 | 0 | 0 | 2 |

**Two package-column deltas, both expected and neither a defect:**

- `or build the schema` 1 -> **0**: that is Site 3 landing. Confirms the old clause is gone package-wide.
- `stamped at finalization` 2 -> **1**: the plan's re-wrap splits that phrase across two adjacent
  string-literal lines (`"...strategy is stamped "` / `"at finalization."`), so the *source* no longer
  carries it contiguously. The **runtime message is unaffected** — adjacent literals concatenate at
  compile time, so the raised text still reads `stamped at finalization`. No test pinned the phrase in
  any tree (all four test-tree columns are 0), so nothing observes the source-level split.

### Validation run

- `uv run ruff format <the three paths>` — **pass**, `3 files left unchanged` (the pre-existing
  `COM812`-vs-formatter warning is repo config, not this diff). Scoped to the three files, never `.`.
- `uv run ruff check --fix <the same three paths>` — **pass**, `All checks passed!`. No fix applied.
- `uv run python scripts/check_trailing_commas.py --check <the same three paths>` — **pass**, no output.
- ASCII-only (`AGENTS.md` rule 17), re-derived: `LC_ALL=C grep -nP '[^\x00-\x7F]' <the three paths> | wc -l`
  -> **0** (unit: matching lines). The prescribed message's `-` is a plain ASCII hyphen; preserved exactly.
- `git status --short` after both ruff invocations, scoped to this item -> **3 lines** (unit: porcelain
  status lines), exactly the three intended paths:

  ```text
   M django_strawberry_framework/testing/relay.py
   M django_strawberry_framework/types/base.py
   M django_strawberry_framework/types/relations.py
  ```

- **Tree-wide churn, reported not reverted.** `git status --short | wc -l` -> **47 entries** (unit:
  porcelain status lines) against the plan's baseline of 43. 43 + 3 (this pass) = 46, so **one further
  entry arrived from a concurrent session mid-pass**; comparing the list against the plan's baseline
  description, the newly-appeared paths are `django_strawberry_framework/conf.py`,
  `docs/SPECS/spec-001-django_types-0_0_1.md`, `docs/SPECS/spec-010-foundation-0_0_4.md`,
  `docs/review/rev-_strawberry_patches.md`, `docs/review/rev-apps.md`, `docs/review/rev-conf.md`,
  `tests/base/test_conf.py`, and `docs/review/rev-_request_body.md`, with some prior entries resolved —
  i.e. more than one file moved in both directions and the net is +1. **None is in R2b's scope, none was
  edited, none was reverted** (`ARTIFACT.md` `### Validation run`: stop-and-report, never a revert).
  `docs/review/` is under the open maintainer escalation and was not touched.

- Focused test run (plan-authorized, no `--cov*` flags):
  `uv run pytest tests/testing/test_relay.py --no-cov -q` -> **10 passed** in 3.67s, 0 failed,
  0 errors, 8 workers. **No assertion broke.** Both rows the plan named
  (`::test_global_id_for_unfinalized_raises`, `::test_global_id_for_strategy_stamped_but_unfinalized_raises`)
  are inside that scope and pass unchanged.

### Failability proofs

`None; this pass introduced no new boundary.`

Audited against the delivered diff rather than asserted from the plan: the diff contains no statement,
no expression, no operator, no branch, no signature, no import, and no name — two comment/docstring
prose edits and the literal text of one message inside an already-existing `raise`. The
`if not definition.finalized:` gate, its condition, its exception class, and its position relative to
the strategy read are byte-identical.

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Not applicable; plan declares floor-verification scope none.`

**The plan's condition on that `none` is verified as met, and this is the tripwire the plan asked to be
checked.** The condition: the `none` holds only while the diff changes **no executable line**. The
delivered `git diff` over the three paths (reproduced in full to the reviewer via
`git diff -- <the three paths>`) consists of exactly:

- `types/relations.py`: 5 docstring lines removed, 7 docstring lines added — all inside the module
  docstring's second paragraph, prose only.
- `types/base.py`: 1 comment line removed, 1 added — `spec-014` -> `spec-018`, one token.
- `testing/relay.py`: 2 string-literal lines removed, 3 added — the message text inside the existing
  `raise ConfigurationError(...)`, nothing else in the call.

No line outside (a) docstring/comment prose and (b) the one message literal is touched, so the
tripwire did **not** fire and the item does not re-loop with floor scope declared.

### Implementation notes

- **Editing mechanism** (plan-delegated discretion): one `Edit` per site, three edits total, each
  `old_string` verified to match exactly once before applying. Chosen over a whole-file rewrite because
  a unique-substring anchor is self-verifying — a mismatch fails loudly rather than silently landing
  the text in the wrong place.
- **Edit order** (plan-delegated discretion): relations.py -> base.py -> relay.py, i.e. the plan's own
  site order. The sites are independent; no site consumes another's surface, so the order carries no
  meaning beyond legibility.
- **Line lengths.** Longest new line across the diff is 78 characters (docstring, `types/relations.py`),
  well inside the 100-char limit; `ruff format` left all three files unchanged, which independently
  confirms no layout rule was crossed.

### Notes for Worker 3

- The mechanical acceptance test the plan recorded, re-derived after the pass:
  `grep -rn 'spec-014' django_strawberry_framework/` -> **no output, exit status 1** (i.e. 0 matching
  lines); `grep -roF 'spec-014' django_strawberry_framework/ | wc -l` -> **0 occurrences**. Baseline
  re-derived at the start of this pass with the same two commands: 2 matching lines / **2 occurrences**,
  at `types/relations.py:4` and `types/base.py:1773`. **2 -> 0 as the plan required.**
- `docs/TREE.md` was **not** regenerated and not touched, per the plan. Re-verified after the edit:
  `grep -n "scaffolding objects" docs/TREE.md` -> **0 matching lines**; `grep -c "spec-014" docs/TREE.md`
  -> **0**. TREE renders only each module's first docstring line, and `relations.py`'s first line
  ("Pending relation records for definition-order-independent ``DjangoType`` finalization.") is outside
  the replacement range and unchanged.
- No shadow file was consulted this pass; Worker 1's plan already ran `scripts/review_inspect.py` over
  all three files and the pass adds no logic for an overview to describe.
- `django_strawberry_framework/__init__.py` is untouched; `testing/relay.py`'s own `__all__` sits above
  the edit site and is unchanged. Public surface: no change.

### Notes for Worker 1 (spec reconciliation)

**No spec amendment is owed by this pass.** No plan-vs-implementation drift of either kind occurred:
the replacement text was fixed by the plan down to punctuation and line wrapping, and it was applied
verbatim at all three sites.

One observation, recorded rather than acted on, because acting would exceed R2b's fence:

- **The corrected remedy clause is still pinned by nothing.** All four substring probes above return 0
  across all three test trees. The two surviving rows assert only the `finalize_django_types()` token,
  so the *parenthetical* — the clause `#### Maintainer decision 8` exists to correct — remains free to
  drift wrong again with a green suite. That is precisely how the original wrong remedy survived to
  this cycle. A row asserting the indirect route ("or by importing a schema module that calls it")
  against `tests/testing/test_relay.py::test_global_id_for_unfinalized_raises` would close it. Adding
  it is out of R2b's scope (the plan declares no test change in scope, and `tests/testing/test_relay.py`
  is writable only if an assertion breaks — none did), so it is surfaced here for Worker 1 to route to
  a future item rather than taken unilaterally.

---

## Review (Worker 3)

Fresh invocation; no in-context memory of the build reasoning. Every number below was re-derived from
disk with its command and unit stated. `git stash` / `git checkout` / `git restore` / `git worktree`
were not used at any point; HEAD was read via `git show HEAD:<path>` and `git grep ... HEAD -- <path>`.

### Attribution verdicts (the item's whole purpose)

**Site 1, `types/relations.py` — both halves CORRECT, and the split is faithful, not over-refined.**

- *Scaffolding objects -> spec-010.* Confirmed against the cited spec's own text, not the plan's
  paraphrase. `docs/SPECS/spec-010-foundation-0_0_4.md #"### \`PendingRelation\`"` opens with
  "Lives at `django_strawberry_framework/types/relations.py` (new)" and defines the frozen dataclass
  field by field; `#"### \`TypeRegistry\` extensions"` adds `add_pending_relation` /
  `iter_pending_relations` / `_pending`; the sentinel appears in spec-010's collection pseudocode as
  `_PendingRelationAnnotation`. spec-010 also states the concept in the docstring's exact words —
  "the same idea (record now, resolve later)" — so "carry a relation from collection to finalization
  (spec-010)" is spec-010's own framing. Command: `grep -n "PendingRelation"
  docs/SPECS/spec-010-foundation-0_0_4.md` -> **11 matching lines** (unit: matching lines).
- *Unconditional routing closes the trap -> spec-018.* Confirmed. `spec-018-meta_primary-0_0_6.md`
  **H1** states the rule and the reason it exists: revision 2's always-defer language, narrowed to
  "always defer **auto-synthesized** relation fields", with the trap named as what the eager path
  missed. Restated at the slice checklist, the changelog block, the shipped-behavior summary, and the
  behavior-change table.
- *The split is faithful.* The HEAD sentence was a compound claim — objects **and** trap closure in
  one clause. Re-crediting the whole sentence to spec-010 would have corrected the pointer while
  preserving a false claim, since spec-018's H1 exists precisely because the spec-010 shape missed the
  trap. Splitting is the minimum change that makes both halves true. It is not over-refined: the new
  second sentence is one clause, adds no mechanism, and does not restate the always-defer contract
  that `types/base.py::_build_annotations` already states in full.

**Site 2, `types/base.py::_build_annotations` — CORRECT.** Read the whole comment block, not the
changed line. It reads "Always defer auto-synthesized relation annotations: the consumer_authored
short-circuit above leaves consumer overrides alone ... The earlier eager-bind branch froze the
relation against whichever type was already registered". That is spec-018 H1 end to end, including
the `if field.name in consumer_authored_fields: continue` short-circuit spec-018 explicitly preserves
and the eager-bind removal spec-018's behavior-change table records. No other spec's fact is
entangled in it, so the single-token change is the right shape.

**spec-014 owns neither — CONFIRMED, four independent probes.**

- `grep -roF "import-order trap" docs/SPECS/ | wc -l` -> **5 occurrences** (unit: occurrences).
  `grep -rlF` -> **exactly one file**, `spec-018`. Per-file re-derivation: spec-018 carries
  **5 occurrences on 5 lines** (units agree here; they need not, which is why both were run).
  spec-010: 0. spec-014: 0.
- `grep -n "PendingRelation" docs/SPECS/spec-014-testing_shift-0_0_4.md` -> **0 matching lines**.
- `grep -nE "relations\.py|always.defer|import.order|_build_annotations"
  docs/SPECS/spec-014-testing_shift-0_0_4.md` -> **0 matching lines**.
- spec-014's own title and problem statement confirm the subject: "IRL API test shift" — moving public
  GraphQL behavior into live example-project API tests. It has no relation-binding deliverable at all.
  Worker 0's independent finding is reproduced exactly.

Verdict: **the replacement attributions are correct at all three halves and the prior attribution was
wrong at both sites.** `grep -oF 'spec-014' django_strawberry_framework/` -> **0 occurrences** now;
`git grep -oF 'spec-014' HEAD -- django_strawberry_framework/ | wc -l` -> **2 occurrences at HEAD**,
on **2 lines** (`types/base.py:1773`, `types/relations.py:4`). Units agree; **2 -> 0** re-derived.

### Does the new error message tell the truth? — YES

The governing contract, read on disk at
`docs/SPECS/spec-010-foundation-0_0_4.md #"No shipped helper auto-triggers finalization"`:
"`DjangoSchema`, `DjangoConnectionField`, and `DjangoNodeField` do not call `finalize_django_types()`;
the explicit consumer call is the only trigger."

The retained indirect route does **not** re-introduce the implication the fix exists to remove, and the
distinction is carried by the wording rather than by charitable reading:

- The old clause was `(or build the schema)`. Under its literal reading, schema construction triggers
  finalization — flatly contradicted by the contract sentence above. It named a non-remedy.
- The new clause is `(directly, or by importing a schema module that calls it)`. Its grammatical
  subject for the triggering act is **the module**, and the verb is **`calls it`** — i.e. the module
  runs somebody's explicit `finalize_django_types()` call at import time. Nothing in it attributes
  finalization to schema construction, to `DjangoSchema`, or to any shipped helper.
- The route is real, not hypothetical. `examples/fakeshop/config/schema.py` calls
  `finalize_django_types()` at module level (`grep -n "finalize_django_types"
  examples/fakeshop/config/schema.py` -> **3 matching lines**, one of them the bare module-level call).
  `README.md` documents the same shape (`grep -rn "finalize_django_types" README.md` -> **2 matching
  lines**: the import and the module-level call). So a consumer who has imported such a module has, in
  fact, already had the explicit call run.

Verdict: **accurate**. The clause states the mechanism that makes the indirect route work rather than
asserting an auto-trigger, and it therefore stays inside spec-010's contract. Both parentheticals now
name remedies that work, which is what `#### Maintainer decision 8` asked for. The message also
correctly carries **no spec name**, per the plan.

### Claim verification — every build-report number re-derived

| Claim | Re-derived | Command / unit | Verdict |
|---|---|---|---|
| `spec-014` 2 -> 0 | HEAD **2 occurrences on 2 lines**; now **0 occurrences**, `grep` exit 1 | `git grep -oF 'spec-014' HEAD -- django_strawberry_framework/ \| wc -l` vs `grep -roF ... \| wc -l`; unit: occurrences, cross-checked against matching lines | **Correct** |
| `or build the schema` 1 -> 0 in package | **0 occurrences** package-wide, **0** in all four test trees | `grep -roF ... \| wc -l`; unit: occurrences | **Correct** |
| `stamped at finalization` 2 -> 1 in package | HEAD **2**, now **1** | same; unit: occurrences | **Correct, and correctly explained** (see next row) |
| `is not finalized` = 1 pkg / 0 tests | **1 / 0 0 0 0** | same | **Correct** |
| `call finalize_django_types` = 2 pkg / 0 tests | **2 / 0 0 0 0** | same | **Correct** |
| No test broke; 10 passed | `uv run pytest tests/testing/test_relay.py --no-cov -q` -> **10 passed** in 3.65s, 0 failed, 0 errors, 8 workers | unit: test rows. No `--cov*` flag used | **Correct, independently re-run** |
| Diff line counts | `relations.py` **+7/-5**, `base.py` **+1/-1**, `relay.py` **+3/-2** | `git diff --numstat -- <the three paths>`; unit: diff lines | **Correct**, matches the build report exactly |
| ASCII-only | **0 matching lines** | `LC_ALL=C grep -nP '[^\x00-\x7F]' <the three paths> \| wc -l` | **Correct** |
| `docs/TREE.md` not regenerated | **0 porcelain status lines**; `grep -c 'spec-014'` -> **0**; `grep -n 'scaffolding objects'` -> **0 matching lines** | `git status --short docs/TREE.md \| wc -l` | **Correct** |
| Tree at 47 entries | **47 porcelain status lines** | `git status --short \| wc -l` | **Correct** |

**The re-derivation delta — runtime message verified INTACT by construction, not by reasoning.**
The build report's explanation (adjacent literals concatenate at compile time) is correct as reasoning,
but reasoning is exactly what this class of change defeats, so I built the runtime value rather than
accepting it. Probe at `docs/builder/temp-tests/spec-008-r2b/probe_message.py` (gitignored): a stub
class carrying a `__django_strawberry_definition__` with `finalized = False` driven through the real
`testing/relay.py::global_id_for`, catching the real `ConfigurationError`. Result:

```text
global_id_for: CategoryNode is not finalized; call finalize_django_types() first (directly, or by importing a schema module that calls it) - the GlobalID strategy is stamped at finalization.
```

- `"stamped at finalization" in msg` -> **True** — the source-level 2 -> 1 does not reach runtime.
- `"importing a schema module that calls it" in msg` -> **True**.
- `"  " in msg` (double space) -> **False**; `msg.isascii()` -> **True**. **No space was dropped and
  none was doubled** at either of the two wrap seams. This is the specific failure the wrap invited.

Worth recording for the next pass: `grep -roF "importing a schema module" django_strawberry_framework/`
-> **0 occurrences**, because that phrase is *also* split across the two literals. The build report
flagged only the `stamped at finalization` split, which is the one its own table probed; the second
split is not a miscount, but it shows the source-vs-runtime divergence this wrap creates is broader
than one phrase. Any future grep-based assertion about this message must run against the runtime
value, not the source.

### Floor-verification tripwire — condition VERIFIED MET, `none` stands

The plan's `none` is conditional on the diff changing no executable line, and `types/` is a Strawberry
type-construction seam that would otherwise be in scope. Verified line by line against
`git diff -- <the three paths>` and `git diff -U0`:

- `types/relations.py`: all 12 changed lines (+7/-5) sit inside the module docstring's **second**
  paragraph. Prose only.
- `types/base.py`: 1 line, inside the `# Always defer auto-synthesized ...` comment block, one token.
- `testing/relay.py`: all 5 changed lines (+3/-2) are string-literal continuation lines inside the
  argument list of the pre-existing `raise ConfigurationError(...)`.

**No statement, operator, branch, signature, import, or name changed.** Specifically checked and found
byte-identical: `if not definition.finalized:` (the gate), its condition, the exception class, its
position relative to the `strategy = definition.effective_globalid_strategy` read, the preceding
f-string line, the module's imports, and `PendingRelation`'s dataclass body. The tripwire did **not**
fire; the item does **not** re-loop with floor scope declared.

### Not-applicable determinations — audited, and I agree

- **Failability proofs: none owed.** Audited against the delivered diff, not the plan's assertion. The
  diff introduces no boundary, guard, gate, or rejection path. Site 3 rewords the text of a message
  inside an already-existing rejection path; the same guard refuses the same inputs before and after,
  which is the `worker-3.md` test for whether a "fix" is a real bound. Nothing was added or moved, so
  there is no boundary to name and no proof to re-run. **Independent re-run set: empty, legally** —
  `worker-3.md`'s mandatory floor permits an empty set only when the diff introduces no boundary
  meeting it, and that condition holds. No source mutation was made; the source carve-out was not
  exercised at any point in this pass.
- **Hot-path budget: `none`.** Site 3's literal is constructed only on the raise path of a `testing/`
  helper for consumer suites. Sites 1 and 2 are stripped before execution.
- **No fail-open shape.** The diff computes no input to a limit, size, permission decision, or
  rejection; it contains no clamp, no `getattr` default, no `or` fallback, no bare `except`, no
  truthiness test. There is no answer to name and refuse.

### Rules sweep across the three files

- **`AGENTS.md` rule 27 (`path::QualifiedName`, never `path:NN`).** Swept the full current text of all
  three files, not just the diff: `grep -nE '[A-Za-z_/]+\.(py|md):[0-9]+' <the three paths> | wc -l`
  -> **0 matching lines**. Same regex over the diff's added lines only -> **0**. The new prose uses
  `types/base.py::_build_annotations` and `types/finalizer.py::finalize_django_types`, which is the
  required form. **Clean.**
- **`AGENTS.md` #"No process provenance in code".** The new prose states invariants only. `spec-010`
  and `spec-018` are spec Decision pointers, explicitly on the KEEP list. Swept the added lines for the
  ban list — severity labels, slice/worker/plan banners, review-doc names, `Test-N` indices, raw spec
  line refs: **0 occurrences of any**. No `R2b`, no `bld-`, no `Maintainer decision`, no round index
  reaches source. **Clean.**
- **ASCII-only (rule 17).** 0 non-ASCII bytes across all three files. The message's `-` is U+002D, a
  plain hyphen, not an en-dash — confirmed in the runtime probe output above.
- **Formatters.** Re-run independently, scoped to the three paths: `ruff format --check` ->
  `3 files already formatted`; `ruff check` -> `All checks passed!`;
  `scripts/check_trailing_commas.py --check` -> no output, **exit 0**.

### Scope confirmation

- `git status --short | wc -l` -> **47 porcelain status lines**, matching the build report. The build
  report's arithmetic (43 baseline + 3 = 46, observed 47, so net +1 with movement in both directions)
  is consistent with what I see; I did not attempt to reconstruct the concurrent sessions' churn beyond
  confirming R2b's three paths are among it.
- **Exactly the three intended source paths carry this item's changes.** No test file was edited:
  `git status --short tests/testing/test_relay.py` -> **0 lines**. `tests/base/test_conf.py` is dirty
  but pairs with the concurrent `django_strawberry_framework/conf.py` session, not this item.
- No spec, no rationale, no durable doc, no `CHANGELOG.md` (`git status --short CHANGELOG.md` -> **0
  lines**) was touched by this pass. `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` /
  `examples/fakeshop/db.sqlite3` are dirty from concurrent sessions and were present in the
  session-start snapshot; no DB was read or written here.
- **Nothing under `docs/review/` was edited or reverted.** Those files carry an open, unresolved
  maintainer escalation and were left exactly as found.
- `docs/TREE.md` was **not** regenerated (0 status lines). Correct: TREE renders only each module's
  first docstring line, and `relations.py`'s first line is byte-identical to HEAD — verified with
  `git show HEAD:django_strawberry_framework/types/relations.py | sed -n '1,2p'` against the working
  copy. The replacement range begins in the second paragraph.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list
are unchanged; no new public export. `testing/relay.py`'s own `__all__` sits above the edit site and is
unchanged.

### CHANGELOG sanity

Not applicable; this slice does not touch `CHANGELOG.md`.

### Documentation and release sanity

Not applicable; this slice touches no durable documentation, no version, and no rendered doc.

### High: None.

### Medium:

**M1 — The corrected remedy parenthetical is pinned by no test in any tree.**

- **Severity:** Medium. **Escalated to Worker 1**, not held.
- **Source:** `django_strawberry_framework/testing/relay.py::global_id_for`, the
  `if not definition.finalized:` branch (the message beginning
  #"call finalize_django_types() first (directly").
- **Re-derived, independently of the build report:**
  `grep -roF "importing a schema module" <each of the four test trees> | wc -l` -> **0 occurrences**
  everywhere; `grep -roF "or build the schema" <same> | wc -l` -> **0** everywhere; `stamped at
  finalization` -> **0** in every test tree. The two surviving rows
  (`tests/testing/test_relay.py::test_global_id_for_unfinalized_raises`,
  `::test_global_id_for_strategy_stamped_but_unfinalized_raises`) assert only
  `"finalize_django_types()" in message` plus the type name.
- **Why it matters:** the parenthetical is the *entire subject* of
  `#### Maintainer decision 8`. It shipped wrong, survived to this cycle with a green suite, and after
  this pass it is still free to drift wrong again with a green suite. The clause the decision exists to
  correct remains the one clause nothing observes. This is not a hypothetical failure mode; it is the
  documented history of this exact string.
- **Recommended change:** one added assertion on the existing row —
  `assert "importing a schema module that calls it" in message` in
  `tests/testing/test_relay.py::test_global_id_for_unfinalized_raises`. No new row, no new fixture.
- **Test expectation:** that assertion fails against HEAD's message and passes against the delivered
  one, which makes it a genuine pin rather than a restatement.
- **Why this is escalated and not a rejection.** I judge the builder's decision to surface rather than
  take it **correct**. The plan fixed the replacement text down to punctuation precisely because a
  confident unilateral judgement shipped wrong once already, and the same plan declared
  `tests/testing/test_relay.py` writable **only if an assertion breaks** — none did. A builder widening
  its own fence on a matter Worker 1 explicitly fenced is the failure mode that discipline prevents.
  On `AGENTS.md` rule 14 ("add tests in the same change as code"): I read the rule as satisfied here in
  its coverage sense — the changed line is a literal already executed by two passing rows, so
  `fail_under = 100` is untouched and no line ships unexercised. What is missing is *pinning*, not
  coverage, and that is a quality gap owned by whoever owns the fence.
- **Resolution paths for Worker 1 to pick between:**
  (a) authorize the one-line assertion inside this cycle as an R2b addendum (cheapest; closes the
  recurrence class in the same change as the fix);
  (b) card it as a follow-up item with the assertion text recorded, accepting one more release window
  in which the clause is unpinned;
  (c) accept the gap as permanent on the grounds that error-message wording is not a contract — which
  I would argue against, since `#### Maintainer decision 8` treats this wording as exactly that.

### Low: None.

The `_PendingRelationAnnotation` / `PendingRelationAnnotation` spelling differs between spec-010's
pseudocode and the shipped symbol. Examined and **not** filed: the docstring credits spec-010 with the
sentinel *concept*, not with the identifier, and the shipped name is what the module exports. Recorded
so the next reader does not re-open it.

### DRY findings: None.

- The finalize-first remedy text has exactly **one** call site
  (`grep -roF "call finalize_django_types" django_strawberry_framework/ | wc -l` -> **2 occurrences**,
  which resolve to the one message plus one unrelated site; the remedy *sentence* is unique). A module
  constant for a single use would be premature, and the existing `_RELAY_NODE_GATE_LEAD` /
  `_RELAY_NODE_GATE_INHERIT_TAIL` pair exists only because two modules must emit the *same* text — not
  the case here. The plan's condition for revisiting (a second site emitting a finalize-first remedy)
  is the right trigger and is correctly recorded.
- **Existence challenge: none raised.** The diff introduces no helper, registry, token, indirection
  layer, or abstraction of any kind. There is nothing whose deletion could be proposed.
- No duplication was created: `types/relations.py`'s new second sentence names the *consequence* in one
  clause and leaves the always-defer mechanism where it lives, in
  `types/base.py::_build_annotations`'s comment block. The two texts do not restate each other.

### What looks solid

- **The attribution split is the right call and is the hard part of this item.** The obvious fix —
  retarget `spec-014` to one correct spec — would have produced a pointer that resolves and a claim
  that is still false. Recognising that the HEAD sentence bundled two facts with two different owners,
  and that spec-018's H1 exists *because* the spec-010 shape missed the trap, is what makes the
  replacement true rather than merely better-cited.
- **The builder flagged the `stamped at finalization` 2 -> 1 delta rather than hiding it.** That is the
  behaviour the re-derivation rule exists to produce; a pass that silently reported "2" would have
  passed a grep audit and been wrong about its own source.
- **Scope discipline under a 47-entry tree.** Three files, three sites, verbatim from the plan, with
  the concurrent churn reported and untouched — including `docs/review/`, which is under open
  escalation.
- **The plan's conditional `none` on floor verification was written as a checkable tripwire with a
  stated re-loop consequence, and the builder actually checked it** instead of restating the
  declaration.

### Temp tests

One, `docs/builder/temp-tests/spec-008-r2b/probe_message.py` (gitignored, confirmed absent from
`git status --short`). It is a **verification probe, not a behavior test**: it drives the real
`global_id_for` rejection path through a stub definition and prints the assembled runtime message.
It caught no bug — the runtime message is intact — so nothing is owed as a promotion. Its subject
matter is, however, exactly what **M1** proposes to pin permanently; if Worker 1 takes path (a), the
permanent assertion supersedes this probe entirely and the probe should not be promoted as-is (it
bypasses the registry rather than exercising a real `DjangoType`).

### Static helper use

`scripts/review_inspect.py` was **not** re-run by this review. Reason recorded per `worker-3.md`
`## Static helper use`: Worker 1's plan already ran it over all three files (exit 0 each), the pass
adds no logic for a control-flow overview to describe, and no repeated-literal or import-boundary
evidence was needed for a DRY finding — because there is no DRY finding. No shadow file was consulted,
so no shadow line number is cited anywhere in this review.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (M1): the corrected remedy parenthetical is pinned by nothing.** Full finding above with
  the re-derived counts and three resolution paths. My recommendation is **(a)** — a one-line assertion
  authorized as an R2b addendum. The gap's whole history is that an unpinned clause drifted wrong and
  stayed wrong; deferring the pin to a future card reproduces the precondition. But the fence is
  Worker 1's, and the builder was right to hand it up rather than widen it.
- **No spec amendment is owed.** Confirmed independently: the delivered text matches the plan's
  `### Exact replacement text` verbatim at all three sites, including line wrapping, so neither
  drift direction occurred.
- **Observation for a future grep-based audit, no action owed now.** Two distinct phrases in the
  `global_id_for` message are now split across adjacent source literals — `stamped at finalization`
  (which the build report flagged) and `importing a schema module` (which it did not probe). Both
  concatenate correctly at runtime, verified by construction. The durable consequence is that any
  future assertion or audit about this message must run against the **runtime value**, not the source
  text; a source grep will return 0 for phrases that are present in the raised string.

### Review outcome

**`review-accepted`**, with **M1 escalated to Worker 1** under `worker-3.md`'s transparent-escalation
allowance — the resolution requires the fence decision, which is spec/plan context Worker 2 cannot
supply, and the finding does not impugn the delivered diff.

Every acceptance-gate item is met: both checklist boxes for the attributions and the box for the
message are reflected in the diff; all three attributions verified correct against the cited specs'
own text; the error message verified truthful against
`docs/SPECS/spec-010-foundation-0_0_4.md #"No shipped helper auto-triggers finalization"`; the
comment-and-message-only property verified, so the floor-verification `none` stands and the item does
not re-loop; every build-report number re-derived with its unit and command; the runtime message
verified intact by construction; no boundary introduced, so the failability re-run floor is met by an
empty set, legally; public-surface check performed and clean; CHANGELOG not applicable.

---

## Final verification (Worker 1) — pass 1

Fresh invocation. Every number below was re-derived from disk this pass with its unit and command; no
figure is carried from the plan, the build report, or the review. `git stash` / `git checkout` /
`git restore` / `git worktree` were not used; HEAD was read via `git show HEAD:<path>`.

**Outcome: `revision-needed`, for one authorized addition only.** The delivered diff is correct and
nothing in it is rejected. `Status: revision-needed` is the routing consequence of my ruling on M1
(below), which changes the fence and therefore needs a builder.

### M1 — DECIDED: authorized. One assertion is added, inside this cycle.

Worker 3's resolution path **(a)**. My reasoning, which is not a restatement of the recommendation:

- **Path (b) — card it as a follow-up — is not available to me.** `AGENTS.md` rule 5 forbids
  defer-the-real-fix sequencing and says in terms that a shortcut "is never viable even with a
  follow-up card". A pin deferred to a future card is exactly that shape.
- **Path (c) — the wording is not a contract — is falsified by the cycle's own record.**
  `#### Maintainer decision 8` exists solely to fix this parenthetical and states "The parenthetical
  must name a remedy that actually works." A maintainer decision that adjudicates a string's wording
  makes that wording a contract by definition. `AGENTS.md` rule 14 ("add tests in the same change as
  code") then applies to it.
- **The failure mode is measured, not hypothetical.** It already happened once to this exact string,
  with a green suite for several releases, and the two surviving rows would keep it green through the
  next drift. Re-derived independently this pass: `grep -roF "importing a schema module" <each of
  tests/, examples/fakeshop/apps, examples/fakeshop/test_query, examples/fakeshop/tests> | wc -l` ->
  **0 occurrences** in every tree (unit: occurrences); `or build the schema` -> **0** in every tree
  and **0** in the package; `stamped at finalization` -> **0** in every test tree.
- **Worker 3's second finding raises the price of not pinning.** Two phrases in this message are now
  split across adjacent source literals, so a *source* grep returns 0 for text that is present at
  runtime. That removes grep as a substitute audit and leaves an assertion as the only instrument
  that can observe this clause at all.
- **The cost side is one line in a file already inside R2b's review chain**, no new row, no new
  fixture, no new import, and no source change. Against that, one more Worker 2 -> Worker 3 ->
  Worker 1 loop is process cost, not risk.
- **The builder and the reviewer were both right to hand it up.** The plan fenced
  `tests/testing/test_relay.py` as writable only if an assertion broke; none did. A builder widening
  its own fence is the failure the isolation discipline prevents. I set the fence, so I amend it —
  explicitly, here, rather than by silence.

**Authorized amendment (required; Worker 2 implements, does not invent).**

Fence amendment: `tests/testing/test_relay.py` becomes writable for **this one insertion and nothing
else**. All other files listed under `### Scope fence` are unchanged; the three source files are
already correct and **must not be touched again**.

Insert exactly this line into `tests/testing/test_relay.py::test_global_id_for_unfinalized_raises`,
immediately after the existing `assert "finalize_django_types()" in message` line (4-space indent):

```text
    assert "first (directly, or by importing a schema module that calls it)" in message
```

- **Why this substring rather than Worker 3's.** Worker 3 proposed
  `"importing a schema module that calls it"`. Mine subsumes it and additionally pins the direct
  route (`directly`) and the placement of `first`, i.e. the whole corrected parenthetical that
  `#### Maintainer decision 8` adjudicates, at no extra cost. Verified this pass by reconstructing
  both message strings: the substring is **absent** from HEAD's message and **present** in the
  delivered one, so it is a genuine pin and not a tautology. Length **87 characters** (unit:
  characters, `len()`), inside the 100 limit; ASCII-only.
- **One row, not two.** `::test_global_id_for_strategy_stamped_but_unfinalized_raises` asserts the
  same literal after a Phase-3 failure; a second copy of the pin would be duplication, and the token
  each row already asserts is what distinguishes the two paths.
- **No other change.** No new test row, no new fixture, no docstring edit, no source edit, no
  `--cov*` flag. Focused scope: `uv run pytest tests/testing/test_relay.py --no-cov`.
- Worker 2 ticks the box below in its pass-2 build report and sets `Status: built` on the header line.

- [x] `tests/testing/test_relay.py::test_global_id_for_unfinalized_raises` — add the one authorized
  assertion above, verbatim, pinning the corrected remedy parenthetical of
  `django_strawberry_framework/testing/relay.py::global_id_for`.

**Routing, stated so Worker 0 dispatches correctly:** `revision-needed` -> **Worker 2** (R2b runs the
full unmodified chain) -> **Worker 3** re-review -> **Worker 1** final verification, pass 2.

### Verification results — Worker 3's claims are claims, and were re-run

- **Runtime message — confirmed by construction, independently of Worker 3's probe.** Drove the real
  `testing/relay.py::global_id_for` rejection path with a stub definition (`finalized = False`) under
  `PYTHONPATH=examples/fakeshop`, from a scratchpad script outside the repo, and read the raised
  `ConfigurationError`. Result, byte for byte:

  ```text
  global_id_for: CategoryNode is not finalized; call finalize_django_types() first (directly, or by importing a schema module that calls it) - the GlobalID strategy is stamped at finalization.
  ```

  `"  " in msg` (double space) -> **False**. `msg.isascii()` -> **True**. `"stamped at finalization"
  in msg` -> **True**; `"importing a schema module that calls it" in msg` -> **True**;
  `"or build the schema" in msg` -> **False**. **No space is dropped or doubled at either wrap seam**,
  which is the specific failure a re-wrapped adjacent-literal string invites. Worker 3's second
  finding is confirmed: `grep -roF "importing a schema module" django_strawberry_framework/ | wc -l`
  -> **0 occurrences** while the phrase is present in the raised string, so both `stamped at
  finalization` and `importing a schema module` are source-invisible.
- **The three attributions — spot-checked against the cited specs' own text, all correct.**
  `grep -cF "PendingRelation" docs/SPECS/spec-010-foundation-0_0_4.md` -> **14 matching lines**
  (unit: matching lines; `git show HEAD:<path> | grep -cF` -> **14** as well, so the concurrent
  session's dirty edit to that file did not move the figure). Worker 3 recorded **11** for the same
  probe; **14** is what the file carries, at HEAD and on disk. The divergence is immaterial to the
  verdict — the attribution rests on the definitions themselves, not on their number — but it is
  recorded rather than smoothed over, and my own first count of this figure was **12**, from counting
  the printed lines of a `head -20` instead of running `grep -c`. That is the twelfth firing of the
  unit trap in this cycle and the second on my own auditing. The matches include `### PendingRelation` at `:134`, the dataclass at `:138`,
  `add_pending_relation` / `iter_pending_relations` at `:167-168`, and `_PendingRelationAnnotation`
  at `:263`. spec-018 **H1** read on disk states the trap and the always-defer fix verbatim.
  spec-014 owns neither: `grep -cF "PendingRelation"` -> **0**, and
  `grep -cE "relations\.py|always.defer|import.order|_build_annotations"` -> **0** (unit: matching
  lines) against `docs/SPECS/spec-014-testing_shift-0_0_4.md`. `grep -roF "import-order trap"
  docs/SPECS/ | wc -l` -> **5 occurrences**; `grep -rlF` -> **exactly one file**, spec-018.
  Site 1's split is the right shape and Site 2's single token is the right shape.
- **`spec-014` 2 -> 0 in the package — confirmed with units.**
  `git grep -oF 'spec-014' HEAD -- django_strawberry_framework/ | wc -l` -> **2 occurrences at HEAD**;
  `grep -roF 'spec-014' django_strawberry_framework/ | wc -l` -> **0 occurrences** now. The item's
  mechanical acceptance test passes.
- **Floor tripwire — condition met, `none` stands.** `git diff --numstat` over the three paths ->
  `relay.py` **+3/-2**, `base.py` **+1/-1**, `relations.py` **+7/-5** (unit: diff lines), matching
  both prior passes. Byte-compared the whole enclosing region of `testing/relay.py` against
  `git show HEAD:` — the **only** difference is the two message-literal lines becoming three.
  `if not definition.finalized:` (the gate), its condition, the `raise ConfigurationError(` call, the
  exception class, the preceding f-string line, the explanatory comment block, and the following
  `strategy = definition.effective_globalid_strategy` read are all **byte-identical**. No executable
  line changed, so the plan's conditional `none` holds and the item does not re-loop with floor scope.
  Note that the authorized M1 amendment adds a test assertion only and does not disturb this.
- **Failability proofs: none owed, confirmed against the diff** — no boundary, guard, gate, or
  rejection path is introduced or moved; the same guard refuses the same inputs before and after. **No
  fail-open shape landed:** read the diff for the catalogued shapes — no clamp, no `getattr` default,
  no `or` fallback, no bare `except`, no truthiness test on a possibly-absent value. The diff contains
  no operator.
- **Hot path: `none`**, confirmed — comments plus one literal on the raise path of a `testing/` helper.
- **Focused tests re-run** (`worker-1.md` step 5, no `--cov*` flag):
  `uv run pytest tests/testing/test_relay.py --no-cov -q` -> **10 passed** in 3.73s, 0 failed,
  0 errors. They run.
- **Scope.** `git status --short | wc -l` -> **47 porcelain status lines**, re-derived this pass; the
  figure matches the build report and review, and none of the concurrent entries was edited or
  reverted. `git status --short tests/testing/test_relay.py | wc -l` -> **0** (the authorized change
  has not been made yet — it is Worker 2's). `git status --short docs/TREE.md | wc -l` -> **0** and
  `grep -c "spec-014" docs/TREE.md` -> **0**. `git diff --stat -- django_strawberry_framework/__init__.py`
  -> **empty**: no public-surface change. Nothing under `docs/review/` was read into scope, edited, or
  reverted.
- **DRY across this item and the prior accepted items: no new duplication.** The remedy sentence has
  one call site; `types/relations.py`'s new second sentence names a consequence and does not restate
  the always-defer mechanism that `types/base.py::_build_annotations` owns. The authorized assertion
  reuses the existing `message` local and adds no helper.

### Spec slice checklist audit

All three boxes in `### Spec slice checklist (verbatim)` are `- [x]`, and **every tick is justified**;
none is over-ticked, none is left open, and no deferral reason is owed.

| Box | Ticked | Landed in the diff | Verdict |
|---|---|---|---|
| `types/relations.py` #"addressed by spec-014" -> spec-010 + spec-018 | `- [x]` | Docstring second paragraph rewritten, +7/-5, split across the two owners | **Correct tick** |
| `types/base.py::_build_annotations` #"the import-order trap closed by spec-014" -> spec-018 | `- [x]` | +1/-1, single token `spec-014` -> `spec-018` | **Correct tick** |
| `testing/relay.py` #"call finalize_django_types() (or build the schema) first" per decision 8 | `- [x]` | +3/-2, the remedy clause replaced verbatim from the plan | **Correct tick** |

The one open box in this cycle is the M1 amendment box under `### M1` above, which is new authorized
work rather than a deferral.

### Spec changes made (Worker 1 only)

**None.** R2b amends no spec, and this is an explicit determination rather than an absent section: the
delivered text matches the plan's `### Exact replacement text` verbatim at all three sites, so neither
drift direction occurred and no spec sentence is falsified by what landed. Spec status/header
re-verification (`worker-1.md` `## Spec status-line re-verification`): spec-008's header lines are
R2's surface, unchanged by this item, and nothing R2b delivered falsifies them. No deferral reason is
owed for any checklist box.

### Summary

R2b corrects two wrong spec attributions in package source (`spec-014` -> `spec-010` + `spec-018` in
`types/relations.py`'s docstring, `spec-014` -> `spec-018` in `types/base.py::_build_annotations`) and
replaces the misleading remedy parenthetical in `testing/relay.py::global_id_for`'s unfinalized-branch
error with one naming two remedies that actually work. Three files, +11/-8 diff lines, no executable
line changed, `spec-014` 2 -> 0 occurrences in the package. Accepted on the merits; held open for one
authorized test assertion pinning the corrected message.

### Notes for Worker 1 (spec reconciliation)

For **R3**, which owns the cycle's deferred-work catalog:

- **R3 does not re-derive the catalog.** The **eight-item** deferred-work catalog is already written
  into R2's artifact (`docs/builder/bld-008-r2-spec_reconciliation.md`, under
  `**For R3's \`### Deferred work catalog\`:**`); R3 points at it. R2b adds
  the entries below to it and nothing else. Structure re-derived this pass so R3 does not mis-scope
  it: **8 numbered deferred-work items**, followed by a separate `**Standing, for whoever runs the
  remaining rounds:**` sub-heading carrying **2** further numbered entries (9 and 10) that are
  process carry-forward, not deferred work — ten numbers, eight catalog items.
- **Catalog item 4 is now discharged.** It reads "`testing/relay.py`'s `(or build the schema)` string
  is DISPATCHED, not deferred." R2b delivered exactly that fix, verified above, so R3 marks it
  closed rather than carrying it forward.
- **M1 is NOT a deferral and must not be catalogued as one.** It was authorized and implemented
  inside this cycle as an R2b addendum. If a future reader looks for it in the catalog, the catalog
  should say where it landed, not carry it as open work.
- **Add: the source-vs-runtime divergence in `testing/relay.py::global_id_for`'s message.** Two
  phrases — `stamped at finalization` and `importing a schema module` — are split across adjacent
  string literals, so a source grep returns 0 for text present in the raised string. Durable
  consequence for any future audit or assertion about this message: **run it against the runtime
  value, not the source text.** No action owed now; the authorized assertion pins the runtime value,
  which is the correct instrument.
- **Add, if the catalog does not already carry it:** `#### Maintainer decision 6`'s deferral —
  spec-009 Layer 3's auto-trigger prose, the D3 falsification one spec further out — is explicitly
  routed to R3's catalog by the build plan and is R3's to confirm present.
- **Not a deferral, recorded so it is not re-opened:** the
  `_PendingRelationAnnotation` / `PendingRelationAnnotation` spelling difference between spec-010's
  pseudocode and the shipped symbol. Examined at review and at final verification; the docstring
  credits spec-010 with the sentinel *concept*, not the identifier, and the shipped name is what the
  module exports. Closed.
- **No spec amendment is owed by R2b**, confirmed independently above. R3 inherits no spec edit from
  this item.

---

## Build report (Worker 2, pass 2)

Fresh invocation with no memory of pass 1; the artifact and the working-tree diff were the contract.
Scope was exactly the one authorized M1 amendment: **one added assertion line in one test file.** The
three R2b source files were **not** touched — `git status --short` below shows them still carrying
pass 1's accepted changes and nothing more, and no `Edit` was applied to any of them this pass.

### Files touched

Grounded in `git status --short`, not memory.

- `tests/testing/test_relay.py` — `::test_global_id_for_unfinalized_raises`, one line inserted
  immediately after the existing `assert "finalize_django_types()" in message`:

  ```python
      assert "first (directly, or by importing a schema module that calls it)" in message
  ```

  The row binds the message to the local **`message`** (`message = str(excinfo.value)`), read from the
  function rather than assumed, so the added line matches the surrounding style exactly. 4-space
  indent, **87 characters** (unit: characters, `awk 'NR==186{print length($0)}'`), ASCII only. No other
  line in the file changed: no new row, no new fixture, no new import, no docstring edit, and
  `::test_global_id_for_strategy_stamped_but_unfinalized_raises` is byte-identical.

### Tests added or updated

- `tests/testing/test_relay.py::test_global_id_for_unfinalized_raises` — now pins the **corrected
  remedy parenthetical** of `django_strawberry_framework/testing/relay.py::global_id_for`'s
  unfinalized branch, not merely the `finalize_django_types()` token. The substring subsumes the
  narrower `importing a schema module that calls it` and additionally pins the **direct** route and
  the placement of `first`, i.e. the whole clause `#### Maintainer decision 8` adjudicates.

### The pin is genuine, and it was verified rather than assumed

The property owed is that the assertion **fails against HEAD's message and passes against the
delivered one**. A source grep cannot establish it: the message is split across adjacent string
literals that concatenate at compile time, so `grep -roF "importing a schema module"
django_strawberry_framework/ | wc -l` -> **0 occurrences** even though the phrase is in the raised
string. Two independent instruments were used instead.

1. **Compile-time-assembled literal, HEAD vs working tree (read-only HEAD, no `git checkout`).**
   `git show HEAD:django_strawberry_framework/testing/relay.py > <scratchpad outside the repo>`, then
   an `ast.parse` walk over every `ast.Raise` in each file collecting `ast.Constant` string values.
   The parser performs the adjacent-literal concatenation, so this reads the **assembled** value, not
   the source text:

   ```text
   HEAD    substring present in a raise literal: False
   WORKING substring present in a raise literal: True
      ->  is not finalized; call finalize_django_types() first (directly, or by importing a schema
          module that calls it) - the GlobalID strategy is stamped at finalization.
   ```

   HEAD's clause, read directly from the same scratch copy
   (`grep -n "call finalize_django_types" <scratch>/relay_head.py`), is
   `"call finalize_django_types() (or build the schema) first - the "` — the substring is **absent**,
   while the row's pre-existing `"finalize_django_types()" in message` assertion **would still pass**
   at HEAD. So the added line, and only the added line, distinguishes the two messages. It is a pin,
   not a tautology.
2. **The real raise path, in the suite.** `tests/testing/test_relay.py::test_global_id_for_unfinalized_raises`
   drives `global_id_for` on an unfinalized Relay-shaped type and asserts against the actual
   `ConfigurationError` text — the runtime value, which is the only instrument that can observe this
   clause at all. It passes (below).

### Validation run

- `uv run ruff format tests/testing/test_relay.py` — **pass**, `1 file left unchanged` (the standing
  `COM812`-vs-formatter warning is repo config, not this diff). Scoped to the one file, never `.`.
- `uv run ruff check --fix tests/testing/test_relay.py` — **pass**, `All checks passed!`. No fix applied.
- `uv run python scripts/check_trailing_commas.py --check tests/testing/test_relay.py` — **pass**,
  no output, **exit 0**.
- ASCII-only (`AGENTS.md` rule 17): `LC_ALL=C grep -nP '[^\x00-\x7F]' tests/testing/test_relay.py | wc -l`
  -> **0** (unit: matching lines). Line length 87 <= 100.
- `git status --short tests/testing/test_relay.py` after both ruff invocations -> **1 line** (unit:
  porcelain status lines): ` M tests/testing/test_relay.py`. Exactly the intended path.
- **The three R2b source files were not re-touched.** They appear in `git status --short` carrying
  pass 1's accepted diff, which is expected and correct; this pass applied no edit to any of them.
- **Tree-wide churn, reported not reverted.** `git status --short | wc -l` -> **48 entries** (unit:
  porcelain status lines) against the 47 recorded at final verification. 47 + 1 (this pass's test
  file) = **48**, so no concurrent session moved during this pass. Every other entry — including the
  six transport-surface source files, `docs/review/rev-*.md` (open maintainer escalation), `KANBAN*`,
  `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3`, and the dirty specs — was left exactly as found.
  Nothing was edited, nothing was reverted (`ARTIFACT.md` `### Validation run`: stop-and-report).
  `git stash` / `git checkout` / `git restore` / `git worktree` were not used at any point.
- Focused test run (no `--cov*` flags, `BUILD.md` `## Coverage is the maintainer's gate`):
  `uv run pytest tests/testing/test_relay.py --no-cov -q` -> **10 passed** in 3.67s, 0 failed,
  0 errors, 8 workers. The amended row is in that scope and passes; the sibling row
  `::test_global_id_for_strategy_stamped_but_unfinalized_raises` is untouched and passes.

### Failability proofs

`None; this pass introduced no new boundary.`

The pass adds a test assertion. No boundary, guard, gate, or rejection path is introduced, moved, or
weakened, and no production file was edited — the diff contains no production line at all. The
`### The pin is genuine` section above is the fail-against-HEAD demonstration the amendment asked for;
it is a pin verification, not a boundary proof, and no source mutation was made to obtain it (the
HEAD comparison is read-only via `git show HEAD:<path>`).

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Floor verification

`Not applicable; plan declares floor-verification scope none.`

The plan's conditional `none` rests on the R2b diff changing no executable line of the package. This
pass adds no package line at all, so the condition is undisturbed and the tripwire did not fire.

### Implementation notes

- **Variable name read, not assumed.** The task text hedged on the binding; the row binds
  `message = str(excinfo.value)` and the two existing assertions read `... in message`, so the added
  line uses `message` and reads as one of three sibling assertions.
- **Placement.** Immediately after the `finalize_django_types()` assertion, as authorized — the two
  read as a progression from "the remedy is named" to "the remedy's routes are named".
- **AST over a runtime probe for the HEAD half.** Reconstructing HEAD's raise required either
  executing HEAD's module (which would mean putting a HEAD copy on the import path, or mutating the
  live file — the latter forbidden by the fence) or reading its assembled literal statically. `ast`
  performs the adjacent-literal concatenation itself, so the static route reads the same value the
  interpreter would build, with no mutation and no import-path surgery. The working-tree half is
  covered by the real raise path in the suite, so both halves rest on assembled values.

### Notes for Worker 3

- The one-line diff is the whole pass: `git diff -- tests/testing/test_relay.py` shows **+1/-0**.
- To re-derive the pin independently without touching the source fence: `git show
  HEAD:django_strawberry_framework/testing/relay.py` into a scratch path outside the repo, then
  `ast.parse` and walk `ast.Raise` -> `ast.Constant` string values. A plain `grep` of either file will
  **not** find the substring, and that is expected, not a defect — two phrases in this message are
  split across adjacent literals (`stamped at finalization` and `importing a schema module`), so the
  source is not a valid instrument for any assertion about this string.
- No shadow file consulted; no `scripts/review_inspect.py` run. The pass adds no logic and touches no
  file under `types/` or `optimizer/`; `BUILD.md` `### When to run the helper during build` does not
  reach a one-line assertion in a test file.
- Public surface: untouched. `git diff -- django_strawberry_framework/__init__.py` is empty; no
  package file was edited this pass.

### Notes for Worker 1 (spec reconciliation)

**No spec amendment is owed by this pass**, and no drift of either kind occurred: the assertion landed
verbatim as `### M1 — DECIDED` prescribed it, including the substring, the indent, and the row it was
inserted into.

- **M1 is now discharged in-cycle.** The clause `#### Maintainer decision 8` adjudicates is pinned by
  a runtime assertion on the real raise path. The recurrence class the finding named — a
  consumer-visible remedy clause that can drift wrong with a green suite — is closed for this string.
  It remains **not** a deferral and must not be catalogued as one by R3; the note already in this
  artifact's final-verification section says where it landed, and this report is that landing.
- **The source-vs-runtime divergence stands as recorded** and is now load-bearing rather than
  observational: the added assertion is the only instrument that observes the parenthetical, because
  a source grep returns 0 for phrases present in the raised string. Any future audit of this message
  must run against the runtime value.

---

## Review (Worker 3, pass 2)

Fresh invocation with no memory of pass 1. Every number below was re-derived from disk this pass with
its unit and the command that produced it; nothing is carried from the plan, either build report, the
prior review, or the final-verification block. `git stash` / `git checkout` / `git restore` /
`git worktree` were not used; HEAD was read only via `git show HEAD:<path>` into a scratchpad outside
the repo.

### Scope of this pass

The diff under re-review is **one added line**. `git diff -U0 -- tests/testing/test_relay.py` produces
exactly one hunk header, `@@ -185,0 +186 @@ def test_global_id_for_unfinalized_raises():`, and
`git diff --numstat` -> **1 added / 0 deleted diff lines**.

The three source files are **not** re-reviewed: they were accepted in pass 1 and Worker 1's amended
fence forbids re-touching them. Confirmed unchanged since acceptance rather than re-read for merit —
`git diff --numstat` over the three paths returns `testing/relay.py` **+3/-2**, `types/base.py`
**+1/-1**, `types/relations.py` **+7/-5** (unit: diff lines), identical to the figures recorded at
pass-1 review and at final verification, and the diff bodies are the plan's
`### Exact replacement text` verbatim at all three sites. No fourth package file entered scope:
`git diff --stat -- django_strawberry_framework/__init__.py` -> **empty**.

### 1. Is the added assertion a genuine pin, or a tautology? — GENUINE PIN

Re-derived by a **different instrument** from Worker 2's and Worker 0's, deliberately: they walked
`ast.Raise` nodes with `ast.parse`; I compiled each file to a **code object** with `compile()` and
recursively collected every `str` in `co_consts` (CPython's compiler performs the adjacent-literal
concatenation during code generation, so this reads the assembled value the interpreter would build,
by a different code path than the AST walk). Command: `git show
HEAD:django_strawberry_framework/testing/relay.py > <scratchpad>/relay_head.py`, then a 14-line probe
over both files. Result (unit: string constants in the module's code objects, **14** in each file):

```text
HEAD  ' is not finalized; call finalize_django_types() (or build the schema) first - the GlobalID strategy is stamped at finalization.'
WORK  ' is not finalized; call finalize_django_types() first (directly, or by importing a schema module that calls it) - the GlobalID strategy is stamped at finalization.'

HEAD  substring "first (directly, or by importing a schema module that calls it)" present: False
WORK  substring "first (directly, or by importing a schema module that calls it)" present: True
```

**The stronger claim — that the added line is the *only* thing distinguishing HEAD's wording from the
delivered one — is verified, not accepted.** The row carries exactly three assertions
(`tests/testing/test_relay.py:184-186`), and I evaluated the two pre-existing ones against HEAD's
assembled constant above:

| Assertion (row line) | Against HEAD's message | Against the delivered message |
|---|---|---|
| `"CategoryNode" in message` (:184) | **passes** — the type name comes from the unchanged f-string prefix `f"global_id_for: {definition.graphql_type_name} is not finalized; "`, which `git diff` shows as a context line, not a changed one | passes |
| `"finalize_django_types()" in message` (:185) | **passes** — HEAD's constant contains `call finalize_django_types() (or build the schema) first` | passes |
| `"first (directly, or by importing a schema module that calls it)" in message` (:186, **added**) | **fails** | passes |

So HEAD's message satisfies the row's entire pre-existing assertion set, and :186 is the sole
discriminator. The row is a regression test for `#### Maintainer decision 8`, not decoration.

Secondary confirmation that the pin observes the *runtime* value and not the source text: `grep -roF
"importing a schema module" django_strawberry_framework/ | wc -l` -> **0 occurrences** while the
phrase is present in the raised string (the unit trap's line-oriented shape, in its purest form — the
grep sees literals, the consumer sees the concatenation). The clause's occurrence count in the four
test trees moved from 0 to **1**: `grep -roF "importing a schema module" tests | wc -l` -> **1
occurrence** (the new assertion), and **0** in each of `examples/fakeshop/apps`,
`examples/fakeshop/test_query`, `examples/fakeshop/tests`. That single occurrence is the whole of M1's
closure and it is measurable.

### 2. Is the substring the right one? — CORRECTLY SCOPED, not over-tight

Worker 1 chose `first (directly, or by importing a schema module that calls it)` over the prior
review's narrower `importing a schema module that calls it`. Judged on the merits:

- **It subsumes the narrower proposal** (the narrower string is a contiguous tail of it) and adds two
  things the narrower one cannot observe: the **direct** route (`directly`), and the **placement of
  `first`** immediately before the parenthetical. Both are part of what
  `#### Maintainer decision 8` fixed — the shipped defect was not only a wrong second route, it was a
  parenthetical positioned as *the* remedy modifier. A pin that omitted `first` would tolerate the
  clause drifting back to a position where it modifies the wrong verb.
- **It is bounded to the adjudicated clause.** It stops at the closing parenthesis and does not reach
  the tail (`- the GlobalID strategy is stamped at finalization.`) or the lead-in (`call
  finalize_django_types() `). Nothing outside decision 8's subject is frozen. Notably it does **not**
  pin the wrap seams: both wrap points in the source literal fall inside the substring's span, so the
  assertion would catch a dropped or doubled space at a seam — the specific failure a re-wrapped
  adjacent-literal string invites — without pinning any text the decision did not adjudicate.
- **Over-tightness assessed against the contract, not against convenience.** A future reword that
  preserves both routes but re-spells the connective (e.g. `either directly or by importing ...`)
  would break this assertion. That is the correct behaviour, not over-tightness: this string's
  documented history is that it drifted wrong and stayed wrong for several releases behind a green
  suite, and the maintainer decision that adjudicates it makes the wording a contract. A reword that
  breaks the row forces the rewriter to re-read decision 8 — which is exactly the instrument M1 asked
  for. The cost of a false break is one line in a file already in the review chain.
- **The narrower alternative would have been the weaker pin** for the same price. No third candidate
  is better: pinning the whole message would freeze text outside the decision's subject; pinning less
  reintroduces the gap.

### 3. Conventions and hygiene — all clean, re-derived

- **Variable name.** The row binds `message = str(excinfo.value)` at `:183` and the two existing
  assertions read `... in message`. The added line uses the same local and the same
  `assert "<literal>" in message` shape, so it reads as the third of three siblings and as a
  progression: the type name, the remedy token, the remedy's routes. `AGENTS.md` "code that reads like
  the surrounding code" is satisfied.
- **Length: 87 characters** (unit: characters, `awk 'NR==186{print length($0)}'`) — the build report's
  claim, re-derived and confirmed. Inside the 100 limit with 13 to spare.
- **ASCII-only:** `LC_ALL=C grep -nP '[^\x00-\x7F]' tests/testing/test_relay.py | wc -l` -> **0
  matching lines**.
- **Trailing-comma / layout:** `uv run python scripts/check_trailing_commas.py --check
  tests/testing/test_relay.py` -> no output, **exit 0**. (A single-line `assert` is not a
  comma-layout construct; the check is run because the rule is file-scoped, not line-scoped.)
- **Lint:** `uv run ruff format --check tests/testing/test_relay.py` -> `1 file already formatted`,
  exit 0 (the `COM812`-vs-formatter warning is repo config and is emitted on every invocation in this
  repo, not by this diff). `uv run ruff check tests/testing/test_relay.py` -> `All checks passed!`,
  exit 0.
- **The sibling row is byte-identical to HEAD.** Not asserted in prose: extracted
  `::test_global_id_for_strategy_stamped_but_unfinalized_raises` from `git show HEAD:` and from disk
  by `def`-boundary slicing and compared the byte strings — **1,499 bytes on both sides, 34 lines,
  equal**. The single-hunk diff header independently corroborates it.
- **Tests:** `uv run pytest tests/testing/test_relay.py --no-cov -q` -> **10 passed** in 3.68s, 0
  failed, 0 errors, 8 workers. No `--cov*` flag was used at any point in this pass.

### 4. Scope confirmation

- `git status --short -- tests/testing/test_relay.py` -> **1 porcelain status line**
  (` M tests/testing/test_relay.py`). The pass's only intended change, and it is a modification of an
  existing row, not a new file.
- `git status --short | wc -l` -> **48 porcelain status lines**, matching the pass-2 build report's
  figure exactly. `tests/base/test_conf.py` and `tests/test_views.py` are both present as ` M` and
  are **baseline-dirty concurrent work**: neither was edited nor reverted, and neither is in this
  item's fence.
- `git status --short -- django_strawberry_framework/` -> **8 entries**: the three R2b files plus five
  transport-surface files (`_boundary_ordering.py`, `_cross_web_patches.py`, `_request_body.py`,
  `conf.py`, `middleware/request_body.py`) belonging to concurrent sessions. Untouched.
- **`docs/review/` was not touched.** It carries 8 dirty entries (5 ` M`, 3 `??`) under the open
  maintainer escalation; none was read into scope, edited, or reverted. Note for the record that its
  composition has *moved* since this cycle's earlier passes (three files that a prior snapshot showed
  as deleted now show as modified) — concurrent-session movement, correctly out of scope, and named
  here only so a later reader does not mistake it for this chain's doing.
- `grep -roF "spec-014" django_strawberry_framework/ | wc -l` -> **0 occurrences**: the item's
  mechanical acceptance test still passes after pass 2, i.e. pass 2 did not disturb pass 1's result.

### 5. Not-applicable determinations — audited, and I agree

- **Failability proofs: none owed.** Audited against the diff rather than the claim. The diff adds one
  `assert` in a test file and contains **no production line**, so it introduces no boundary, guard,
  gate, or rejection path; the mandatory re-run floor (`worker-3.md`, boundaries with a recorded
  failing-row count <= 3, and every security / data-isolation boundary) is met by an **empty set,
  legally**, because the diff introduces no boundary that meets the floor. The one thing that *would*
  have needed proving — that the added row can fail — is proven above by the HEAD-vs-working
  reconstruction, which is the failability question for a test-only diff and was answered without any
  source mutation. Worker 3's source carve-out was not exercised in this pass.
- **Hot-path budget: `none`.** Confirmed: no package line changed, so nothing can have entered a hot
  path. Additionally the message this row observes is constructed only on the raise path of a
  `testing/` helper.
- **Floor verification: `none`.** The plan's `none` is conditional on the diff changing no executable
  line of the package. Re-verified for pass 2 specifically: `git diff --numstat` shows the three
  package paths at the same +3/-2, +1/-1, +7/-5 as at final verification, so pass 2 added no package
  line at all and the tripwire did not fire. The `none` stands and the item does not re-loop.

### 6. Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list
are unchanged. No package file was edited this pass.

### CHANGELOG sanity

Not applicable; the slice does not touch `CHANGELOG.md`.

### Documentation and release sanity

Nothing owed. No module docstring changed this pass, so `docs/TREE.md` is unaffected
(`git status --short -- docs/TREE.md` -> **0 lines**); no DB row was read or written, so
`docs/GLOSSARY.md` and `KANBAN*` are untouched by this chain; no version bump is in scope.

### High: None.

### Medium: None.

M1 from pass 1 is **closed at the root**, not relabelled. The finding asked that the corrected remedy
parenthetical be *pinned* — that some instrument fail when the clause drifts. The input now refused
that was previously accepted: **a `testing/relay.py::global_id_for` unfinalized-branch message whose
remedy parenthetical has drifted away from the two working routes now fails
`tests/testing/test_relay.py::test_global_id_for_unfinalized_raises`, where before this pass it
passed.** That is a real bound, demonstrated against HEAD's own message, not a widened error string or
a renamed probe.

### Low: None.

One observation deliberately **not** filed. The added assertion's substring begins immediately after
the text the preceding assertion pins (`finalize_django_types()` then `first (directly, ...`), so the
two do not jointly pin the single space that joins them. Examined and rejected as a finding: the join
falls inside the unchanged lead-in that both messages share, decision 8 does not adjudicate it, and
collapsing the two assertions into one wider literal would break the deliberate symmetry with
`::test_global_id_for_strategy_stamped_but_unfinalized_raises`, which asserts the same token after a
Phase-3 failure. Recorded so a later reader does not re-open it.

### DRY findings: None.

- **One row, not two, is correct.** Copying the assertion into
  `::test_global_id_for_strategy_stamped_but_unfinalized_raises` would be a second copy of one pin;
  the token each row already shares is what distinguishes the two paths, and the sibling row was
  verified byte-identical.
- **No abstraction was introduced,** so there is nothing whose existence could be challenged: no
  helper, constant, fixture, parametrization, or indirection. A module-level constant for a substring
  used once would be the premature-extraction shape `worker-3.md` warns about.
- No near-copy was created across the four test trees: the clause's occurrence count there is exactly
  **1**.

### What looks solid

- **Worker 2 answered the question the amendment actually posed.** The authorization asked for one
  verbatim line; a minimal pass would have inserted it and reported green. Instead the report carries
  the HEAD-vs-working reconstruction that shows the line *can* fail — which is what separates a pin
  from a restatement, and is the one property a green focused run cannot demonstrate.
- **The instrument choice is right and is explained.** Reconstructing HEAD's raise by executing it
  would have meant either import-path surgery or mutating a fenced live file; reading the assembled
  literal statically avoids both. My independent re-derivation by a different mechanism
  (`compile()` + `co_consts` rather than `ast.parse`) reached the identical strings, which is the
  corroboration that matters.
- **The variable name was read from the row rather than assumed**, and the build report says so. On a
  one-line insertion that is the entire correctness surface of the line's *form*, and it is where a
  hurried pass produces `str(excinfo.value)` inline beside two siblings that use a local.
- **The fence held in both directions.** Worker 2 did not re-touch the three accepted source files
  (verified by diff-figure equality with final verification, not by the report's say-so), and did not
  extend the amendment to the sibling row, the spec, or anything under `docs/review/`.

### Temp tests

One scratch probe, written outside the repo in the session scratchpad (not under
`docs/builder/temp-tests/spec-008-r2b/`, which remains **absent** from `git status --short`). It is a
verification instrument, not a behavior test: it compiles both copies of `testing/relay.py` and prints
the assembled string constants. It caught no bug, so nothing is owed as a promotion — and its subject
matter is already pinned permanently by the very assertion under review, which supersedes it.

### Static helper use

`scripts/review_inspect.py` was **not** run by this pass, and the skip is recorded per `worker-3.md`
`## Static helper use`: the diff is a single assertion in a test file, touching no file under
`types/` or `optimizer/`, adding no logic for a control-flow overview to describe, and no
repeated-literal or import-boundary evidence was needed because there is no DRY finding. No shadow
file was consulted, so no shadow line number is cited anywhere in this review.

### Notes for Worker 1 (spec reconciliation)

- **Nothing escalated.** M1 is discharged in-cycle and no new finding of any severity was opened.
- **No spec amendment is owed.** The assertion landed verbatim as `### M1 — DECIDED` prescribed it —
  substring, indent, and host row all match — so neither drift direction occurred and no spec sentence
  is falsified by what landed.
- **For R3's catalog, unchanged by this pass:** M1 is **not** a deferral and must not be catalogued as
  one; catalog item 4 remains discharged; and the durable carry-forward from this item stands as
  already recorded — any future audit or assertion about `global_id_for`'s unfinalized message must
  run against the **runtime value**, because a source grep returns **0 occurrences** for two phrases
  that are present in the raised string. This pass is the first consumer of that rule and it held.

### Review outcome

**`review-accepted`.** No High, Medium, or Low finding is open, and none was rejected without a
recorded reason.

Acceptance gate, item by item: the single checklist box added by `### M1 — DECIDED` is ticked and the
tick is justified by the diff; the pin was verified genuine by an independent instrument rather than
accepted on the build report's account; the substring is judged correctly scoped to the clause
`#### Maintainer decision 8` adjudicates; the diff introduces no boundary, so the failability re-run
floor is met by an empty set legally and no proof is missing; hot-path budget and floor verification
are `none` with their conditions re-verified against this pass's diff; the public-surface check was
performed and is clean; CHANGELOG is not applicable; the three accepted source files were confirmed
unchanged and were not re-reviewed; scope is exactly one file and the baseline-dirty concurrent work
was neither edited nor reverted; `10 passed`, lint and layout checks exit 0.

---

## Final verification (Worker 1) — pass 2

Fresh invocation. Every figure below carries its unit and the command that produced it and was
re-derived from disk this pass; nothing is carried from the plan, either build report, either review,
or my own pass-1 block. `git stash` / `git checkout` / `git restore` / `git worktree` were not used;
HEAD was read only via `git show HEAD:<path>` into a scratchpad outside the repo.

**Outcome: `final-accepted`.** The substance of this item has been through the full chain twice; this
pass confirms and closes it. The three accepted source edits were not re-reviewed (fence-closed at
pass 1) and M1 was not re-litigated (I authorized it; it landed).

### 1. M1 — discharged exactly as authorized, and it is not a deferral

- **The line.** `sed -n '178,186p' tests/testing/test_relay.py` shows the added assertion as the
  **third** in `::test_global_id_for_unfinalized_raises`, at **line 186**:
  `    assert "first (directly, or by importing a schema module that calls it)" in message`.
  Byte-for-byte the substring `### M1 — DECIDED` authorized, with the authorized 4-space indent.
  **87 characters** (unit: characters, `awk 'NR==186{print length($0)}'`).
- **The row.** `git diff -U0 -- tests/testing/test_relay.py` -> exactly one hunk,
  `@@ -185,0 +186 @@ def test_global_id_for_unfinalized_raises():`, and `git diff --numstat` ->
  **1 added / 0 deleted diff lines** (unit: diff lines). The host row is the one authorized; no other
  line in the file moved.
- **The variable.** The row binds `message = str(excinfo.value)` at `:183` and its two pre-existing
  assertions read `... in message`. The added line uses that same local — read from the row, not
  assumed.
- **Not catalogued as a deferral, anywhere.** R2's catalog (`bld-008-r2-spec_reconciliation.md:2409`)
  predates R2b and contains no R2b-M1 entry; the only mentions of M1 in this artifact after the
  authorization are the three "**not** a deferral / discharged in-cycle" notes (pass-1 final
  verification, pass-2 build report, pass-2 review). It landed in-cycle and the record says where.
  Decision 8's own scope limit anticipated it: "no test change beyond any assertion that pins the
  message text" — the amendment used exactly that carve-out, not a widening of it.

### 2. The pin is genuine — confirmed by a fourth instrument, and the load-bearing claim verified

Three prior derivations agree (Worker 2 `ast.parse`/`ast.Raise`, Worker 0 the same, Worker 3
`compile()` + recursive `co_consts`). Mine is a fourth: an `ast` walk that additionally **reconstructs
the `JoinedStr`**, substituting `CategoryNode` for the `{definition.graphql_type_name}` field, so the
value compared is the whole assembled message the row actually sees — including the f-string prefix
the other three instruments read only as a separate constant. HEAD was materialised read-only via
`git show HEAD:django_strawberry_framework/testing/relay.py > <scratchpad>/relay_head.py`.

```text
HEAD  'global_id_for: CategoryNode is not finalized; call finalize_django_types() (or build the schema) first - the GlobalID strategy is stamped at finalization.'
WORK  'global_id_for: CategoryNode is not finalized; call finalize_django_types() first (directly, or by importing a schema module that calls it) - the GlobalID strategy is stamped at finalization.'
```

**The load-bearing claim — the row's other two assertions both pass against HEAD's message, so `:186`
is the sole discriminator — is CONFIRMED**, evaluated in Python against the reconstructed HEAD string
rather than argued:

| Assertion (row line) | HEAD | Delivered |
|---|---|---|
| `"CategoryNode" in message` (`:184`) | **True** | True |
| `"finalize_django_types()" in message` (`:185`) | **True** | True |
| `"first (directly, or by importing a schema module that calls it)" in message` (`:186`) | **False** | True |

HEAD satisfies the entire pre-existing assertion set; only the added line separates the two messages.
**The row is therefore a regression test for `#### Maintainer decision 8`, not decoration.** Also
re-derived on the delivered string: `"  " in msg` -> **False**, `msg.isascii()` -> **True** — no space
dropped or doubled at either wrap seam.

### 3. Spec slice checklist audit — four boxes, four justified ticks, none open

Derived by grepping the artifact for box lines (unit: **box lines**,
`grep -cE '^\s*- \[x\]'` -> **4**; `grep -cE '^\s*- \[ \]'` -> **0**), then auditing each against the
diff. Note the shape: three boxes sit under `### Spec slice checklist (verbatim)` (`:309-311`) and the
fourth is the M1 amendment box under `### M1 — DECIDED` (`:899`), which is new authorized work rather
than a spec sub-check.

| Box | Landed in the diff | Verdict |
|---|---|---|
| `types/relations.py` #"addressed by spec-014" -> spec-010 + spec-018 | docstring paragraph 2, **+7/-5** | Correct tick |
| `types/base.py::_build_annotations` -> spec-018 | **+1/-1**, one token | Correct tick |
| `testing/relay.py` remedy clause per decision 8 | **+3/-2**, plan text verbatim | Correct tick |
| `tests/testing/test_relay.py::test_global_id_for_unfinalized_raises` — the M1 assertion | **+1/-0** at `:186`, verbatim | Correct tick |

**No over-tick, no landed-but-open box, and no `- [ ]` remains — so no deferral reason is owed.**
Numstat re-derived this pass: `relay.py` 3/2, `base.py` 1/1, `relations.py` 7/5, `test_relay.py` 1/0.

### 4. The three `none` declarations, re-confirmed against the FINAL diff

- **Failability proofs — none owed.** Read the final diff for boundaries, not the claim: the package
  half changes docstring/comment prose and one message literal inside an already-existing
  `raise ConfigurationError(...)`; `if not definition.finalized:`, its condition, the exception class,
  and its position relative to the `strategy = definition.effective_globalid_strategy` read are
  unchanged context lines in `git diff`. The test half adds one `assert`. **Boundary count 0**, so
  the obligation has no subject. **No fail-open shape landed:** no clamp, no `getattr` default, no
  `or` fallback, no bare `except`, no truthiness test on a possibly-absent value — the package diff
  contains no operator at all.
- **Hot path — `none`.** No package line is executed differently. The one changed literal is built
  only on the raise path of a `testing/` helper for consumer suites; the two comment sites are
  stripped before execution.
- **Floor verification — `none`, condition MET.** The plan's `none` is conditional on the diff
  changing no executable package line. Re-verified against the final diff: every changed package line
  is (a) docstring/comment prose or (b) the message literal inside the existing `raise`. The M1
  amendment adds a line to `tests/testing/test_relay.py`, which is **not package source** and cannot
  falsify the condition. The tripwire did **not** fire; the item does not re-loop with floor scope.

### 5. `spec-014` 2 -> 0 in the package, with units

`git grep -oF 'spec-014' HEAD -- django_strawberry_framework/ | wc -l` -> **2 occurrences at HEAD**
(unit: occurrences), on **2 files** (`git grep -lF` -> 2). `grep -roF 'spec-014'
django_strawberry_framework/ | wc -l` -> **0 occurrences** now. The item's mechanical acceptance test
passes, and pass 2 did not disturb it.

### 6. Other verification

- **Focused tests re-run** (`worker-1.md` step 5, no `--cov*` flag):
  `uv run pytest tests/testing/test_relay.py --no-cov -q` -> **10 passed** in 3.72s, 0 failed,
  0 errors, 8 workers. They run.
- **DRY across this item and the prior accepted items: no new duplication.** The remedy sentence has
  one call site; the added assertion reuses the row's existing `message` local and introduces no
  helper, constant, fixture, or parametrization. The clause's occurrence count across the four test
  trees is exactly **1**.
- **Scope.** `git status --short | wc -l` -> **48 porcelain status lines**, re-derived this pass.
  `tests/base/test_conf.py` and `tests/test_views.py` are baseline-dirty concurrent work and were
  neither edited nor reverted; nothing under `docs/review/` was read into scope, edited, or reverted;
  no spec, rationale, durable doc, `KANBAN*`, DB, build plan, or other artifact was written by this
  pass. `git diff -- django_strawberry_framework/__init__.py` -> **empty**: no public-surface change.
- **Spec status-line re-verification** (`worker-1.md` `## Spec status-line re-verification`):
  spec-008's opening lines are a title and the rationale-companion pointer — no status, target-release,
  or predecessor line exists to be falsified, and nothing R2b delivered touches them.

### Spec changes made (Worker 1 only)

**None**, and this is an explicit determination rather than an absent section. R2b amends no spec:
the three source texts landed verbatim from the plan's `### Exact replacement text` and the assertion
landed verbatim from `### M1 — DECIDED`, so neither drift direction occurred; no spec sentence is
falsified by what landed; and spec-008's header lines carry no claim this item touches. **No checklist
box remains `- [ ]`, so no deferral reason is owed here either.**

### Summary

R2b shipped the cycle's only source diff — two corrected spec attributions (`spec-014` -> spec-010 +
spec-018 in `types/relations.py`'s docstring, `spec-014` -> spec-018 in
`types/base.py::_build_annotations`) and a remedy parenthetical in
`testing/relay.py::global_id_for`'s unfinalized branch that now names two routes that actually work —
plus one authorized regression assertion pinning that parenthetical. Four files, **+12/-8 diff lines**
(unit: diff lines, `git diff --numstat` summed over the four paths), no executable package line
changed, `spec-014` 2 -> 0 occurrences in the package.

### Notes for Worker 1 (spec reconciliation)

For **R3**, which owns the cycle's deferred-work catalog:

- **R3 does not re-derive the catalog.** It is already written into R2's artifact
  (`docs/builder/bld-008-r2-spec_reconciliation.md:2409`, under
  `**For R3's \`### Deferred work catalog\`:**`); R3 points at it. Structure re-derived again this
  pass so R3 does not mis-scope it: **8 numbered deferred-work items**, then a separate
  `**Standing, for whoever runs the remaining rounds:**` sub-heading carrying **2** further numbered
  entries (9 and 10) that are process carry-forward, not deferred work — **ten numbers, eight catalog
  items.**
- **Catalog item 4 is discharged.** It reads "`testing/relay.py`'s `(or build the schema)` string is
  DISPATCHED, not deferred." R2b delivered exactly that fix and it is verified twice over; R3 marks it
  closed rather than carrying it forward.
- **M1 is NOT a deferral and must not be catalogued as one.** Authorized and implemented inside this
  cycle as an R2b addendum; it lives at `tests/testing/test_relay.py:186`. If a future reader looks
  for it in the catalog, the catalog says where it landed, not that it is open.
- **Durable carry-forward: the source-vs-runtime divergence in
  `testing/relay.py::global_id_for`'s message.** Two phrases — `stamped at finalization` and
  `importing a schema module` — are split across adjacent string literals, so a source grep returns
  **0 occurrences** for text present in the raised string. **Any future audit or assertion about this
  message runs against the runtime (assembled) value, never the source text.** Four independent
  instruments now rest on that rule (`ast.Raise` walk x2, `compile()` + `co_consts`, and this pass's
  `JoinedStr` reconstruction); the added assertion is the permanent instrument.
- **Add, if the catalog does not already carry it:** `#### Maintainer decision 6`'s deferral —
  spec-009 Layer 3's auto-trigger prose — is explicitly routed to R3's catalog by the build plan and
  is R3's to confirm present.
- **Not a deferral, recorded so it is not re-opened:** the `_PendingRelationAnnotation` /
  `PendingRelationAnnotation` spelling difference between spec-010's pseudocode and the shipped
  symbol. Examined at both reviews and both final verifications; the docstring credits spec-010 with
  the sentinel *concept*, not the identifier. Closed.
- **No spec amendment is owed by R2b.** R3 inherits no spec edit from this item.

**R3's remaining scope**, with what pre-flight already established — R3 re-runs rather than trusting
these, but should not have to discover them:

- The durable-doc audit against the shipped relation graph; the cross-reference sweep in all three
  directions; `SpecDoc.path` / terms-CSV verification; and the `TODO(spec-008` /
  `TODO-<MILESTONE>-008` staged-anchor sweep.
- **The staged-anchor sweep is empty tree-wide** (Worker 0 at pre-flight; re-derived here as a
  by-product: `grep -rn 'TODO(spec-008' .` -> **3 matching lines** and `grep -rn 'TODO-.*-008' .` ->
  **5 matching lines**, all of which are the build plan describing the sweep itself plus one binary
  hit inside `examples/fakeshop/db.sqlite3`. **Zero real anchors.** Unit note for R3: the sweep's own
  documentation matches the sweep's pattern, so the raw hit count is never the anchor count.)
- **Card 8's `SpecDoc.path` already reads the archived path**, and its **ten** glossary links match
  the terms CSV one row per anchor (Worker 0, pre-flight).
- `docs/review/` remains an open, unresolved maintainer escalation and is out of scope for R3 as it
  was for every pass here.
