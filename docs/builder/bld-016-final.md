# Build: Final test-run gate — spec-016 residual-completion cycle

Spec reference: [`docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md`][spec-016]
Rationale companion: [`docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md`][spec-016-rationale]
Build plan: [`docs/builder/build-016-fieldmeta_consolidation-0_0_6.md`][build-016]
Status: final-accepted

**The gate closes the cycle with two escalations to the maintainer, neither attributable to this cycle's diff.** One `pytest` row fails and three whitespace errors trip `git diff HEAD --check`; both are concurrent sessions' uncommitted work, proved mechanically below, and neither is worker-verifiable at HEAD ([`docs/builder/BUILD.md`][build] `## Claims are proven mechanically, never accepted on prose`).

This artifact also discharges [`docs/builder/BUILD.md`][build] `## Cross-slice integration pass` **step 1** (every closed artifact read in full) and **step 6** (the staged-anchor sweep), which the build plan's `## Artifact list` folded into this gate in place of a `bld-integration.md`.

---

## Certification and tree state

Certified **per file blob**, never by commit hash and never by tree object — the corrected method rule R2's second final-verification pass established after the commit hash rotted five times and the tree object four times inside this one cycle while `walker.py`'s blob never moved.

| Fact | Value |
|---|---|
| `git rev-parse HEAD` | `fa248bdf064b3dca52c1e591b6c6444b041bb65f` |
| `git rev-parse HEAD:django_strawberry_framework/optimizer/walker.py` | `1030b037b2db85290eeb45bde92c55b865cf6f42` |
| `git rev-parse HEAD:docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` | `56326e7937883c9acb1f4229bd43f83d57eec2db` |
| `git status --porcelain \| wc -l` at gate open | 34 |
| `git status --porcelain \| wc -l` after the sweep and command run | 42 |
| `git status --porcelain \| wc -l` at gate close | **49** |
| `git diff --cached --name-only \| wc -l` | 32, unchanged throughout |

`1030b037` is the same blob the R2 plan, both build passes, both reviews, and both final-verification passes measured — six commits and four tree objects deep. Every reading any pass of this cycle took is still valid against the files this gate read.

`git stash`, `git checkout`, `git restore`, `git worktree` used **nowhere** in this pass. Every `HEAD` reading went through `git show HEAD:<path>` into a scratch path **outside** the repository, `git rev-parse`, `git grep … HEAD`, or `git diff HEAD`. The index was not touched: no `git add`, no `git reset`, no unstage.

### The tree drifted by FOURTEEN paths DURING this gate, and two of them are spec-016 reader sites

Recorded because it bounds what the sweep proves. At gate open the tree carried 34 dirty paths; 42 after the commands had run; **49** by the time this artifact was written. Every arrival is a concurrent session's and none is this cycle's.

**Eight arrived while the gate ran its commands**, all unstaged (` M`):

`django_strawberry_framework/rest_framework/inputs.py`, `rest_framework/resolvers.py`, **`types/base.py`**, **`types/finalizer.py`**, `utils/inputs.py`, `tests/rest_framework/test_resolvers.py`, `tests/types/test_base.py`, `tests/types/test_finalizer.py`.

**Six more arrived while this artifact was being written**, all untracked and outside the index — a concurrent review cycle still emitting: `docs/review/rev-rest_framework.md`, `rev-rest_framework__hook_context.md`, `rev-rest_framework__inputs.md`, `rev-rest_framework__resolvers.md`, `rev-rest_framework__serializer_converter.md`, `rev-rest_framework__sets.md`. (The 49th path is this artifact.)

`types/base.py` and `types/finalizer.py` are **two of the seven reader sites the reconciled spec names** (V1 and V2). They were clean when R1 verified them and are dirty now. That does not falsify V1/V2: both were verified **read-only against `HEAD`** via `git show HEAD:<path>`, which is exactly why the discipline exists. But it does mean **the `pytest` sweep below ran against a tree that has since changed**, and the maintainer's own clean-HEAD run is the authority on the suite, not this one.

---

## Gate commands, in the order [`docs/builder/BUILD.md`][build] `## Final test-run gate` gives them

### 1. Full sweep — `uv run pytest --no-cov`

```shell
uv run pytest --no-cov
```

**FAIL — 1 failed, 6130 passed, 40 skipped in 91.07s.** Run to completion across all three test trees, not narrowed. `--no-cov` is the only coverage-shaped flag used; no `--cov*` flag was passed in this or any pass of this cycle, and no line coverage was inspected or asserted ([`docs/builder/BUILD.md`][build] `## Coverage is the maintainer's gate, not a worker's tool`).

The single failing node id:

```
tests/test_sets_mixins.py::test_permission_facade_methods_are_single_sourced_on_the_mixin
```

```
[gw6] darwin -- Python 3.14.2 .venv/bin/python

    def test_permission_facade_methods_are_single_sourced_on_the_mixin():
        for name in _SHARED_PERMISSION_METHODS:
            mixin_fn = _unbound(ActiveInputPermissionMixin, name)
            assert _unbound(FilterSet, name) is mixin_fn
>           assert _unbound(OrderSet, name) is mixin_fn
E           AssertionError: assert <function OrderSet._run_permission_checks at 0x10aa65a60>
E                              is <function ActiveInputPermissionMixin._run_permission_checks at 0x109fcd590>
tests/test_sets_mixins.py:36: AssertionError
```

Collection / setup errors: **0**.

#### Attribution — mechanical, and it is not this cycle's

The question [`docs/builder/BUILD.md`][build] requires: is the failing test, or the code under it, in this cycle's diff?

| Check | Measurement | Verdict |
|---|---|---|
| Is [`tests/test_sets_mixins.py`][test-sets-mixins] in this cycle's diff? | `git status --porcelain -- tests/test_sets_mixins.py` prints **nothing**; blob `a23010320ccb8ccd49c1fda44d1833c93758a866` | **No** — clean at `HEAD`, untouched by any round |
| Is the code under it in this cycle's diff? | this cycle's diff is five Markdown paths plus one docstring hunk in [`optimizer/walker.py`][walker]; `orders/sets.py` appears in no round's writable set | **No** |
| Is [`django_strawberry_framework/orders/sets.py`][orders-sets] dirty? | `M ` (staged by the concurrent sweep), `git diff HEAD --numstat` -> **+46/-4** | **Yes — a concurrent session's** |
| Does `HEAD`'s `orders/sets.py` define `_run_permission_checks`? | `git show HEAD:django_strawberry_framework/orders/sets.py \| grep -n "_run_permission_checks"` -> `:15` (a docstring mention), `:435`, `:447`, `:462` (all **call sites**), and **no `def`** | **No `def` at `HEAD`** |
| Does the worktree copy define it? | `grep -n "_run_permission_checks" django_strawberry_framework/orders/sets.py` -> `:292` **`def _run_permission_checks(`** plus `:303` `super()._run_permission_checks(` | **Yes — a new override, uncommitted** |

The mechanism is therefore exact and needs no inference. At `HEAD`, `OrderSet` inherits `_run_permission_checks` from `ActiveInputPermissionMixin`, so `_unbound(OrderSet, name) is mixin_fn` holds and the row passes. A concurrent session's **uncommitted** edit adds an `OrderSet._run_permission_checks` override at `orders/sets.py:292`, which makes `_unbound(OrderSet, ...)` resolve to the subclass function instead of the mixin's — falsifying a single-source assertion in a test file that is clean at `HEAD`. `_run_permission_checks` is the **last** of the seven names in `_SHARED_PERMISSION_METHODS`, and the six before it still pass, which is why exactly one assertion fails.

**Classification: a concurrent-session condition, not pre-existing at `HEAD` and not this cycle's.** Per [`docs/builder/BUILD.md`][build] `## Claims are proven mechanically, never accepted on prose`, a failing test is **not worker-verifiable at all** — reproducing it needs the whole tree at `HEAD`, and this tree carries three sessions' work. Recorded with the evidence above (failing node id, traceback, `HEAD` content obtained read-only, and the diff-membership answer for both the test and the code) and **escalated to the maintainer**, the only party who can run a clean `HEAD` tree.

**Nothing was fixed, reverted, or staged.** [`django_strawberry_framework/orders/sets.py`][orders-sets] is in the build plan's `## Baseline-dirty out-of-scope files` (`orders/sets.py`, modified) and [`tests/test_sets_mixins.py`][test-sets-mixins] is in no round's writable set. Fixing another session's in-flight refactor, or reverting it to make the row green, is the forbidden action here — not the diligent one.

**Why this does not force `revision-needed`.** This cycle's whole diff is five Markdown files plus one function-docstring hunk whose four executable statements, signature, and return annotation are proved byte-identical to `HEAD` by AST below. There is no mechanism by which it could change any assertion's pass/fail, and the failing row's cause is identified in another session's uncommitted source. Routing this back through R2's loop would dispatch a builder at a file no round may open.

### 2. Django's own consistency checks against the example project

```shell
uv run python examples/fakeshop/manage.py check
uv run python examples/fakeshop/manage.py makemigrations --check --dry-run
```

| Command | Output | Exit | Result |
|---|---|---|---|
| `manage.py check` | `System check identified no issues (0 silenced).` | 0 | **PASS** |
| `manage.py makemigrations --check --dry-run` | `No changes detected` | 0 | **PASS** |

No model / admin / url-config drift.

### 3. Read-only lint / format / diff gate — never `--fix`

```shell
uv run ruff format --check .
uv run ruff check .
git diff HEAD --check
```

| Command | Output | Exit | Result |
|---|---|---|---|
| `uv run ruff format --check .` | `423 files already formatted` | 0 | **PASS** |
| `uv run ruff check .` | `All checks passed!` | 0 | **PASS** |
| `git diff HEAD --check` | 3 whitespace errors, listed below | **2** | **FAIL — concurrent session's, covered by a recorded baseline exception** |

`ruff format --check` also emits the standing `COM812`-conflicts-with-the-formatter warning. That is pre-existing repository configuration, not this cycle's diff, and it does not affect the exit code.

**`git diff HEAD --check`, not the bare `git diff --check`**, because a concurrent session's `add -A`-shaped sweep holds 32 paths in the index; the bare form sees only the worktree half and would report a staged file as clean. This is the cycle's own carried lesson, established at R2's first final verification and confirmed on a re-pass, where the bare form hid an earlier pass's whole hunk.

The three errors:

```
docs/review/rev-middleware.md:111: new blank line at EOF.
docs/review/rev-middleware__debug_toolbar.md:115: new blank line at EOF.
docs/review/rev-middleware__request_body.md:61: new blank line at EOF.
```

**All three are in `docs/review/`, all three are a concurrent session's review-cycle output, and all three are doubly out of bounds.** They are enumerated in the build plan's `## Baseline-dirty out-of-scope files` ("Another session's review cycle, untracked: ~29 `docs/review/rev-*.md` files"), which is the pre-flight baseline exception [`docs/builder/worker-1.md`][worker-1] `## Final test-run gate` requires for a lint/diff failure not to block `final-accepted`; and [`AGENTS.md`][agents] rule 22 forbids bulk-deleting or bulk-overwriting anything under `docs/review/`. No round in this cycle wrote a `docs/review/` path, so this is not tool-induced drift a slice's Worker 2 should have owned, and there is no owning slice loop to route it back through. **Not edited, not reverted, not staged.** Escalated with the `pytest` row.

Every file this cycle wrote passes the stricter gate the pre-commit `source-layout` hook runs:

```shell
uv run python scripts/check_trailing_commas.py --check \
  docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md \
  docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md \
  docs/builder/build-016-fieldmeta_consolidation-0_0_6.md \
  docs/builder/bld-016-r1-rationale_and_spec_reconciliation.md \
  docs/builder/bld-016-r2-walker_source_reference_fix.md \
  docs/builder/bld-016-r3-doc_completion_archive_audit.md
```

exit **0**.

### 4. Floor verification

**No floor-verification scope was declared for any round in this cycle, and the declaration was honored.** The build plan's preamble reads `Floor-verification scope: **none.** No round touches a Django / Strawberry / channels integration seam.` Re-checked against what actually landed rather than accepted from the declaration: R1 and R3 wrote Markdown only, and R2's sole source change is a **function docstring** whose executable body is proved byte-identical to `HEAD` below. None of [`docs/builder/BUILD.md`][build] `### When it is required`'s seams — request/response handling, view or ASGI plumbing, upload or body parsing, session/auth, queryset or expression compilation, schema and type construction against Strawberry internals, consumer or middleware wiring — is touched by a comment.

**No floor venv was built and nothing was installed into the shared `.venv`.** Building a Python 3.10 environment to re-run tests against an unchanged bytecode-identical module would measure nothing; the declaration is `none` because the change cannot have a version-sensitive effect, not because a run was inconvenient.

Floor facts, **quoted** from [`docs/builder/BUILD.md`][build] `## Floor verification` so nothing here is restated from memory: the supported floor is Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**, and **the shared `.venv` is not the floor**. No `.venv` version is stated anywhere in this artifact; the sweep's own traceback header reports the interpreter it ran on (`Python 3.14.2`) and that reading is quoted from the run rather than asserted.

---

## Cross-slice integration obligations, folded in

### Step 1 — every closed artifact read in full

Discharged. Read end to end, in round order, with no "as needed": [`bld-016-r1-rationale_and_spec_reconciliation.md`][bld-r1] (187 lines), [`bld-016-r2-walker_source_reference_fix.md`][bld-r2] (1,290 lines, all four passes: plan, build, review, final verification, plus build report pass 2, review pass 2, final verification pass 2), and [`bld-016-r3-doc_completion_archive_audit.md`][bld-r3] (212 lines). Also the build plan, the reconciled spec, and the rationale companion.

Nothing in the three artifacts is unresolved against this tree. Every `- [x]` in R2's `### Dispatched findings checklist` was audited at that round's own final verification and both ticks re-confirmed on the re-pass; R1's and R3's procedural-closure rounds carry no un-ticked box. **No `- [ ]` box remains anywhere in this cycle**, so no deferral reason is owed under [`docs/builder/worker-1.md`][worker-1] `## Final verification job` step 3.

**No cross-round DRY surface exists to consolidate**, and this is a measured answer rather than an empty section: R1 and R3 wrote Markdown, R2's hunk contains no executable token, so there is no helper, constant, repeated literal, or parallel data flow anywhere in the cycle's diff. The one cross-round shape is the **sentence pair** — [`optimizer/walker.py::_resolve_field_map`][walker]'s `DUAL CONTRACT` paragraph and the spec's first bounded-exception bullet — and it is consolidated the only way prose can be. Verified here rather than accepted: the two texts are clause-for-clause paraphrases of each other, both derived from one measurement, with their shared explanation living once, in the companion. Read side by side:

- docstring: "``name`` and ``is_relation`` are guaranteed on both shapes (``field_meta.py::_DjangoFieldLike``) and are read directly; any other attribute is read directly only where both shapes carry it, and a ``FieldMeta``-only attribute must never be read off this map without a ``getattr(..., default)``. That rule, not a blanket ``getattr`` discipline, is what lets the two shapes coexist safely."
- spec bullet: "`name` and `is_relation` are guaranteed on both shapes (`optimizer/field_meta.py::_DjangoFieldLike`) and are read directly; any other attribute is read directly only where both shapes carry it, and a `FieldMeta`-only attribute must never be read off that map without a `getattr(..., default)`. That rule, not a blanket `getattr` discipline, is what makes the two shapes safe to coexist."

The only differences are each file's own reference convention (walker.py's `optimizer/`-sibling shorthand versus the spec's root-relative form) and one verb order. The pair reads as one contract. `scripts/review_inspect.py`'s shadow comparison is **not** run for the repeated-literal and imports sections: its stripper replaces every string-literal token including docstrings with `...`, so its output is structurally blind to this cycle's entire change surface — proved rather than asserted, `grep -c 'DUAL CONTRACT' docs/shadow/django_strawberry_framework__optimizer__walker.stripped.py` -> `0`.

### Step 6 — staged-anchor sweep

```shell
grep -rEn 'TODO\(spec-016|TODO-(ALPHA|BETA|STABLE)-016' . \
  --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md --exclude='*.sqlite3' -I
```

**One hit, and it is not an anchor.** [`docs/builder/build-016-fieldmeta_consolidation-0_0_6.md`][build-016]`:117` contains the two patterns inside this cycle's own prose *describing* the sweep. No staged anchor exists in any shipped source, test, or comment. Narrowed to the trees that could carry one:

```shell
grep -rEn 'TODO\(spec-016|TODO-(ALPHA|BETA|STABLE)-016' \
  django_strawberry_framework/ tests/ examples/ scripts/ -I
```

exit **1** — nothing. `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` are excluded, where `TODO-<MILESTONE>-<NNN>` legitimately names unshipped board cards.

**The card's own historical anchors are gone**, which is the spec's `### Mirror retirement` closing sentence made checkable:

```shell
grep -rn 'TODO(spec-fieldmeta-ssot)\|TODO(spec-fieldmeta-mirror-retirement)\|spec-fieldmeta' \
  django_strawberry_framework/ tests/ examples/ scripts/ -I
```

exit **1** — no occurrence of either anchor, or of the bare `spec-fieldmeta` token, anywhere in source, tests, the example project, or `scripts/`. `walker.py`'s two `TODO(spec-035)` anchors belong to another card and are present and untouched.

---

## Independent verification at the gate

Nothing below is carried on trust from a round artifact. Where a re-measurement disagrees with what an artifact recorded, the disagreement is named.

### The one source change: no executable statement moved — proved by AST

Stronger than reading the diff, because a reflow is exactly what fools a visual diff read. `HEAD`'s blob was extracted read-only via `git show HEAD:django_strawberry_framework/optimizer/walker.py` into a scratch path **outside** the repository, both copies were parsed, and `_resolve_field_map` was unparsed from each:

| Property | `HEAD` (blob `1030b037`) | working tree | identical |
|---|---|---|---|
| non-docstring statements | 4 | 4 | **yes** |
| signature | `model: type[models.Model], *, source_type: type \| None = None` | same | **yes** |
| return annotation | `tuple[type \| None, Any \| None, dict[str, Any]]` | same | **yes** |
| statement 1 | `type_cls = source_type if source_type is not None else registry.get(model)` | same | **yes** |
| statement 2 | `definition = registry.get_definition(type_cls) if type_cls is not None else None` | same | **yes** |
| statement 3 | `field_map = definition.field_map if definition is not None else {f.name: f for f in model._meta.get_fields()}` | same | **yes** |
| statement 4 | `return (type_cls, definition, field_map)` | same | **yes** |

`git diff HEAD -U0 -- django_strawberry_framework/optimizer/walker.py` filtered to `^[+-]` yields **only docstring prose** — 8 lines removed, 13 added, one hunk. No `if`, no comparison, no `raise`, no error message, no default argument, **no expression at all**.

Consequently, and confirming both of [`docs/builder/worker-1.md`][worker-1] `### Failability and fail-open checks`' obligations: **boundary count is zero**, so no failability proof is owed and none is missing; and **no fail-open shape** — clamp, `getattr` default, `or` fallback, bare `except`, truthiness test on an absent-capable value — can be introduced by a hunk carrying no executable token. This is the **fourth** independent AST confirmation in the cycle and it agrees with the three before it. No mutation exists anywhere in the tree; no `ACTIVE-MUTATION.json` file exists.

### Spec-side gates

| Check | Command | Result |
|---|---|---|
| Glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-016-…md` | `OK: 2 terms - all have glossary entries and at least one spec link.` exit **0** |
| Markdown scaffold | `uv run python scripts/check_trailing_commas.py --check` on all six of this cycle's files | exit **0** |
| TREE render | `uv run python scripts/build_tree_md.py --check` | `docs/TREE.md is up to date.` exit **0** |
| Link defs, spec | disk-exists loop over every `^[ref]: path` | **5/5** resolve |
| Link defs, companion | same loop | **16/16** resolve |
| Group headers | all ten canonical headers, in canonical order | **yes**, both files |
| Cross-file anchors | the companion's 8 `#anchor` defs against the spec's rendered heading slugs | **8/8** resolve |
| In-page anchor | the companion's one `](#…)` against its own heading slugs | resolves — see the method note below |
| `#"substring"` citations | **line-wise** `grep -cF` for all 11 citations in the spec and the companion, each in its named file | **11/11 at exactly 1 occurrence** |

`docs/TREE.md` needs no regenerate and none was run: the renderer reads **module** docstrings and R2 changed a **function** docstring, leaving `walker.py`'s module docstring untouched. `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, and `examples/fakeshop/db.sqlite3` are all **clean** and none is in any round's writable set.

**Method note, because my own first checker reproduced the exact defect R3 recorded.** The companion's one in-page anchor is `#bounded-exceptions--the-dual-contract-was-stated-on-a-false-premise-in-both-files`, pointing at a heading that opens with a backtick-wrapped `` `### Bounded exceptions` ``. My first slug implementation lowercased and trimmed **before** stripping punctuation, which left a leading space where the backtick and hashes had been and produced a spurious leading hyphen — reporting a correct anchor as DANGLING. Stripping punctuation first, then trimming, then replacing each space with a hyphen (without collapsing runs, which is what preserves the double hyphen) resolves it against the real heading. R3 hit the same failure mode from the other direction and its lesson generalizes further than it stated it: **never derive a slug by eye *or* by an unverified reimplementation — check the checker against a heading you know resolves.**

### V1-V11 spot re-verification

Sampled at the gate rather than accepted, on the claims a later change could most plausibly have falsified:

| # | Claim | Measurement at this tree |
|---|---|---|
| V8 | no class-attribute mirror exists as declaration or read | `grep -rn "_optimizer_field_map" django_strawberry_framework/ tests/ examples/ scripts/ --include='*.py'` -> exit **1**, no match |
| V9 | no `TODO(spec-fieldmeta-*)` anchor remains | exit **1** across all four trees (step 6 above) |
| F8 | the cross-reference is fixed and no third spelling exists | `grep -rn "optimizer/resolvers" django_strawberry_framework/` -> exit **1**; the reference reads `types/resolvers.py::_field_meta_for_resolver` |
| — | the docstring/spec pair is consistent | read side by side above; clause-for-clause paraphrases |

`types/base.py` (V1) and `types/finalizer.py` (V2) are now dirty with a concurrent session's work and were therefore **not** re-read in the worktree; R1's read-only `HEAD` verification stands and is the correct instrument, which is the whole point of the discipline.

### Board and DB figures, re-derived read-only

[`examples/fakeshop/db.sqlite3`][db] was **clean** before this pass, opened read-only through the ORM, and **clean** after — verified both times with `git status --porcelain -- examples/fakeshop/db.sqlite3`, which printed nothing. No DB write, none owed.

| Figure R3 recorded | Re-derived here | Agrees |
|---|---|---|
| 49 `done` cards | 49 | **yes** |
| `verified_upstream` `CardItem` rows across done cards: 96, of which 82 incomplete / 14 complete | 96 / 82 / 14 | **yes** |
| Card 16 `status.key == "done"`, `milestone.key == "alpha"` | `done`, `alpha` | **yes** |
| 26 `CardItem` rows over five sections | 26 — `scope` 13, `files_touched` 5, `note` 5, `why_it_matters` 2, `verified_upstream` 1 | **yes** |
| the single incomplete row is the `verified_upstream` one | the only `is_complete=False` row's section is `verified_upstream` | **yes** |
| `SpecDoc` present and its path matches disk | `spec-016-fieldmeta_consolidation-0_0_6` -> `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` | **yes** |
| exactly two `CardGlossaryTerm` links, matching the two-row CSV | `djangotype`, `relation-handling`; CSV rows `DjangoType,djangotype` and `relation shape,relation-handling` | **yes** |

Every F10 figure holds on re-derivation, including the 82/96 board-convention count that is what turns card 16's one incomplete row from a defect into convention.

### The orphan `[backlog]` def class, re-derived

R3 ruled keep on population grounds and named the population. Re-measured at the gate rather than copied: sweeping `docs/SPECS/spec-0*.md` for files that **define** `[backlog]` with **zero** `][backlog]` body uses returns **eight** — `spec-011`, `spec-012`, `spec-013`, `spec-016`, `spec-024`, `spec-026`, `spec-036`, `spec-054` — and **seven** further specs define **and use** it. R3's figures reproduce exactly. The def resolves on disk (5/5 above) and the scaffold checker is green either way, so keeping costs nothing mechanically and dropping it in one of eight would create the divergence removal was meant to prevent.

---

## The cycle's own diff, path by path

Sizes and deltas **re-derived at gate time**, not carried from any artifact. Commands: `git status --porcelain`, `git diff HEAD --numstat`, `wc -c`.

| Status | Path | vs `HEAD` | Bytes |
|---|---|---|---|
| `MM` | [`django_strawberry_framework/optimizer/walker.py`][walker] | +13 / -8 | 65,309 |
| `MM` | [`docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md`][spec-016] | +50 / -38 | 9,559 |
| `AM` | [`docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md`][spec-016-rationale] | +601 / -0 (new) | 41,926 |
| `AM` | [`docs/builder/build-016-fieldmeta_consolidation-0_0_6.md`][build-016] | +128 / -0 (new) | 25,998 |
| `A ` | [`docs/builder/bld-016-r1-rationale_and_spec_reconciliation.md`][bld-r1] | +187 / -0 (new) | 31,347 |
| `AM` | [`docs/builder/bld-016-r2-walker_source_reference_fix.md`][bld-r2] | +1290 / -0 (new) | 199,188 |
| `??` | [`docs/builder/bld-016-r3-doc_completion_archive_audit.md`][bld-r3] | untracked, not staged | 36,782 |
| — | `docs/builder/bld-016-final.md` (this file) | untracked, not staged | new |

Reading the status codes, which is the whole point of listing them: `MM` = staged **and** further modified; `AM` = added to the index and further modified; `A ` = staged, index equal to worktree; `??` = untracked and **not** in the index. So the concurrent sweep caught the first six paths and missed R3's artifact and this one, purely because they were written after it ran.

Two byte counts differ from what an earlier round recorded, both expected and both explained by R3's own edits landing after R1 measured: the spec is **9,559** bytes here against R1's recorded 9,162 (R3 replaced the bounded-exceptions bullet whole), and the companion is **41,926** against R1's 36,128 (R3 added an entry, struck through one bullet, and symbol-qualified nine refs). Neither is drift.

`docs/builder/worker-memory/spec-016-worker-*.md` are gitignored (`.gitignore:188`) and appear in no listing.

### Baseline-dirty and concurrent paths — explicitly NOT this cycle's

**41 of the 49 dirty paths are three concurrent sessions' work.** Every one falls inside a bucket the build plan's `## Baseline-dirty out-of-scope files` declared, plus [`django_strawberry_framework/connection.py`][connection] which arrived mid-cycle and the fourteen that arrived during this gate. **Not one was edited, reverted, staged, or `git checkout`ed by any pass of this cycle.**

- **Package source (11):** `connection.py`, `mutations/resolvers.py`, `orders/inputs.py`, [`orders/sets.py`][orders-sets], `relay.py`, `rest_framework/inputs.py`, `rest_framework/resolvers.py`, `templates/django_strawberry_framework/debug_toolbar.html`, `types/base.py`, `types/finalizer.py`, `utils/inputs.py`.
- **Tests (9):** `tests/middleware/test_debug_toolbar.py`, `tests/mutations/test_resolvers.py`, `tests/orders/test_inputs.py`, `tests/orders/test_sets.py`, `tests/rest_framework/test_resolvers.py`, `tests/types/test_base.py`, `tests/types/test_finalizer.py`, `examples/fakeshop/test_query/test_multi_db.py`, `examples/fakeshop/test_query/test_optimizer_auto_api.py`.
- **Another session's review cycle (21):** 14 untracked-then-staged `docs/review/rev-*.md` files, 6 still-untracked `rev-rest_framework*.md` files that arrived during this gate, and a modified `docs/review/review-0_0_14.md`. Three of the 14 carry the `git diff HEAD --check` whitespace errors. [`AGENTS.md`][agents] rule 22 protects all of them.

**A falling dirty count is not evidence of a revert.** The count moved 50 -> 52 -> 58 -> 36 -> 33 -> 34 -> 42 -> 49 across this cycle; every fall was a concurrent session committing (`6b42c8d2`, `76fdeac3`, `fa248bdf`), never a revert by any worker. **The count is a moving figure about other sessions' work and no later pass should quote it forward** — it is recorded here only as this gate's own measurement, with the timestamp of each reading.

`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` — the four concurrent-writable tracked generated files — are all **clean**, which is also the evidence that no concurrent card-wrap is mid-flight.

---

## NOTE FOR THE MAINTAINER: the index holds this cycle's output mixed with two other sessions' WIP

**Committing the index as it stands would ship mixed work under one message.** `git diff --cached --name-only` reports **32 staged paths** — a blanket `add -A`-shaped sweep, not a targeted stage. It has caught:

- **this cycle's output** — the spec (`MM`), the companion (`AM`), the build plan (`AM`), R1's artifact (`A `), R2's artifact (`AM`), and the `walker.py` docstring hunk (`MM`);
- **two other sessions' WIP** — `mutations/resolvers.py`, `orders/inputs.py`, `orders/sets.py`, `relay.py`, `debug_toolbar.html`, 14 `docs/review/rev-*.md` files, `docs/review/review-0_0_14.md`, and six test files.

**No worker in this cycle ran `git add`.** The stage is not this build's, and the index was **not touched** by this pass: no `git add`, no `git reset`, no `git restore --staged`, no unstage. Unstaging is outside every worker's writable set and would mutate another session's index state.

Two consequences worth naming:

1. **A `git commit` right now produces one commit describing whichever work its message names, containing all three sessions'.** The specific hazard for this cycle is that the reconciled spec and the `walker.py` docstring — the pair R2 and R3 deliberately kept together so they reach the maintainer in one commit — would land inside a message about someone else's refactor.
2. **R3's artifact and this one are `??`, not staged**, so a commit of the index as-is would ship five of the cycle's seven paths and leave the two artifacts that record the cycle's closure behind.

The cycle's seven paths, for a targeted stage:

```
django_strawberry_framework/optimizer/walker.py
docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md
docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md
docs/builder/build-016-fieldmeta_consolidation-0_0_6.md
docs/builder/bld-016-r1-rationale_and_spec_reconciliation.md
docs/builder/bld-016-r2-walker_source_reference_fix.md
docs/builder/bld-016-r3-doc_completion_archive_audit.md
docs/builder/bld-016-final.md
```

---

## Close-out: the cycle against the maintainer's three obligations

### 1. Nothing was skipped in the code

**Verified, not assumed, and one defect found and fixed.** All eleven claims spec-016 makes about shipped source were measured against `HEAD` read-only — V1-V11 at plan time, every one of them independently re-measured at R1's final verification, and the highest-risk ones re-sampled again at this gate. The canonical `FieldMeta` read is present at all seven reader sites; the two class-attribute mirrors are gone as declarations **and** as reads across the package, tests, the example project, and `scripts/`; all eight `TODO(spec-fieldmeta-*)` anchors are removed; `FieldMeta` carries the cardinality API its consumers read and its two properties now delegate to the shared classifiers in `utils/relations.py`; and no second field-metadata store was reintroduced anywhere.

**No skipped feature and no correctness defect in shipped behavior.** Exactly one source-level defect existed — F8, a docstring cross-reference in [`optimizer/walker.py::_resolve_field_map`][walker] pointing at `optimizer/resolvers.py`, **a module that has never existed** — and it was the one cross-reference tying the two halves of this card's single-source surface together. R2 fixed it to `types/resolvers.py::_field_meta_for_resolver`, converging on the spelling two already-correct sites use rather than inventing a third, and the fix is proved: zero occurrences of the never-existent module in package source, two occurrences of the symbol reference in `.py`, one spelling.

**R2's review also surfaced a second, deeper defect in the same paragraph, and it was fixed rather than accepted.** The docstring's untouched half asserted that `getattr(..., default)` access is "the ONLY reason the two coexist safely" — false as an absolute, since **10 plain non-`getattr` reads** of field-map values exist in the walker. What made it this cycle's to fix rather than pre-existing drift it could disclaim: R2's own new sentence leaned on the false contrast for its meaning, so the round *extended* the drift instead of merely inheriting it. The paragraph now states the rule the file actually obeys, and the decisive proof is the **negative** check rather than the population count — not one of `FieldMeta`'s ten `FieldMeta`-only attributes is read off a map value anywhere, and `attname` is `getattr`-defended at all three of its sites. The measurement converged across four independent derivations (8, then 10, 10, 10 with identical rows), and the two occurrences the first derivation missed were found only by resolving a differently-named parameter back to its call site and by counting occurrences rather than lines.

### 2. The spec states the current contract, with no chronology

**Verified against the file, not asserted.** The spec was reconciled from a 4,558-byte card-snapshot stub into a 9,559-byte current contract. Nowhere does it narrate its own history: it carries no amendment block, no retraction paragraph, no "as of round N" hedge, and no "now" / "no longer" construction. Every invariant is stated in the present tense as though it had been right from the start.

What that took: all seven source references symbol-qualified under [`AGENTS.md`][agents] rule 27 (an archived spec is a standing doc, not a per-cycle scratchpad); the **three** reader sites that no longer existed under the names the stub gave them re-pointed at `HEAD` — one of which was stale **on the day the card shipped**, having been copied verbatim from a pre-implementation proposal that the implementation commit itself superseded; the audit method given the class it belongs to; the two **bounded exceptions** to the single-source rule stated as design rather than left reachable only by grep, which is what turned an unresolvable audit into a checkable one; a new `### Out of scope` drawing the line between reading shape from a `FieldMeta` (this card's contract) and calling the shared classifier on a raw descriptor (never in scope), so a reader who greps the classifier and finds seven live raw-field call sites does not conclude the consolidation was undone; the complete two-commit `## Change population` including the source module the stub's file list omitted and the six test files it omitted; and the correction of a sentence — "Existing tests pass without modification" — that its own commit falsified when it was written.

The counterfactual preamble instructing a future implementer to expand the stub, and the one-word `## Planning note`, are gone.

### 3. The explanation lives in the rationale companion

**Created at 41,926 bytes**, keyed to the spec by heading and reference-style anchor, nine entries plus a reconciliation record. It states in bold in its own first section that it is a **reconstruction from history, not a [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` move** — there was no deliberative layer in a card snapshot to cut — and names its four recovery sources. It separates what genuinely **moved** out of the spec from what was **added** and what was **deleted outright** as falsified. It records rejected alternatives one per entry, the claims the spec may no longer make, and the settled arguments it **cites rather than retells** so the repository does not end up with four divergent versions of one stub-shape argument.

The three commit-level facts the plan had wrong were corrected in the process and are recorded there: the card shipped **two** commits rather than one, `_resolve_optimizer_hints` was created by the implementation commit itself rather than extracted later, and the helper deletion and the upstream move of the canonical read are one commit five days after the card shipped.

**All eight cross-file anchors from the companion into the spec resolve, all sixteen link defs disk-exist, and all eleven `#"substring"` citations across the pair grep to exactly one line.**

---

## Deferred work catalog

The next spec author's reading list, assembled from the three closed artifacts' spec-reconciliation notes and `What looks solid` / `Notes for Worker 1` sections. **Every item was re-verified at this gate rather than copied**, and two came back materially different. **None is a defect in shipped behavior**, and none was fixed by this cycle.

1. **A test comment names a symbol deleted five days after the card shipped.** [`tests/test_registry.py`][test-registry] #"``FieldMeta.from_django_field`` and ``_record_pending_relation``" — the helper was deleted at `f83bb71b` and the canonical read is now `types/base.py::_build_annotations`. Source: R1 `### Out-of-scope residue found while verifying`, R2 catalog item 1, R3 note 1. Licensing clause: none in the spec; tests are outside every round's writable set this cycle by the build plan's `## Do not touch`. **Re-verified: still present at `:504`, file clean.**

2. **The [`CHANGELOG.md`][changelog] cluster — six elements wide on one line.** Cited by substring per rule 27: [`CHANGELOG.md`][changelog] #"Consolidated field metadata onto". Source: plan F12, widened at R1, widened again at R3. Licensing clause: [`AGENTS.md`][agents] rule 21 forbids `CHANGELOG.md` edits unless told — **a maintainer decision, not a worker's**. **Re-verified element by element, each at exactly one occurrence:** (a) the pre-renumber card id `012-fieldmeta_single_source_of_truth_consolidation_and_mirror_retirement-0.0.6` as the link **text**, written by the board-graduation commit before the renumber; (b) `_record_pending_relation`, deleted; (c) `resolved_relation_annotation` named as the `types/` reader, true but the canonical read moved upstream; (d) `walker._walk_selections`, now `_resolve_optimizer_hints`; (e) `extension.check_schema`, bare where the symbol carries its class; (f) **four dotted `module.symbol` forms** — `walker._resolve_field_map`, `walker._walk_selections`, `extension._collect_schema_reachable_types`, `extension.check_schema` — where rule 27 requires `path/file.py::QualifiedName`. **The link *target* is acquitted and stays acquitted:** the `KANBAN.md#…` anchor resolves, so only the text is stale. File clean.

3. **A dotted source reference in [`django_strawberry_framework/registry.py`][registry].** #"``types.converters.resolved_relation_annotation`` for relation" where rule 27 requires `types/converters.py::resolved_relation_annotation`. One of this card's own symbols (V2). Source: R2 plan note 2, catalog item 3. Licensing clause: none; outside every round's writable set. **Re-verified: present at `:6`, file clean.**

4. **A mixed slash-and-dot reference in [`django_strawberry_framework/types/converters.py`][converters].** #"``Meta.required_overrides`` by ``types/base._build_annotations``" where rule 27 requires `types/base.py::_build_annotations`. V1's canonical read site. Source: R2 plan note 3, catalog item 4. Same class, same licensing. **Re-verified: present at `:409`, file clean.**

5. **A dotted reference inside the file R2 owned, deliberately left.** [`django_strawberry_framework/optimizer/walker.py`][walker] #"``utils.relations.instance_accessor``". Source: R2 plan note 4, catalog item 5. Licensing: `instance_accessor` is not a spec-016 symbol, so fixing it is scope creep into another card — a decided non-edit, not an omission. **Re-verified: present at `:775`.**

6. **A bare cross-module symbol with no path at all.** [`django_strawberry_framework/optimizer/field_meta.py`][field-meta] #"field shapes on the resolver path (``_field_meta_for_resolver``)". The bare-symbol edge of item 7's convention, found at R2's second final verification after three prior censuses missed it. Source: R2 catalog item 12, R3 note 12. Pre-existing at `HEAD`, file clean, outside every round's writable set. **Re-verified: present at `:310`.**

7. **The bare-basename cross-folder shorthand convention — ACQUITTED as house style, but the population and the acquittal's stated ground are BOTH wrong in the artifacts.** This is the item that changed most on re-derivation, and it matters because a future sweep leaning on the recorded version would acquit a genuinely misdirecting reference.

   - R2 and R3 both record it as **"~12 sites"**. Re-measured over all `` `basename.py::Symbol` `` occurrences in package source, classified by whether the target is a sibling of the citing file and whether the basename is unique: the class is **56 cross-folder occurrences whose basename is unique package-wide** (the genuinely acquitted set), plus **98 same-folder occurrences** that are unambiguous by proximity and were never the question. "~12" understates the acquitted class by more than four times.
   - The acquittal's **stated ground** — "each resolves because the basename is unique package-wide" — **is not true of the whole class.** **12 cross-folder occurrences cite a basename that is genuinely ambiguous *within the package*:** `relay.py` x7 (three paths — root, `types/`, `testing/`) at `extensions/resource_policy.py:103`, `mutations/fields.py:4`, `:24`, `mutations/resolvers.py:1206`, `:1223`, `utils/querysets.py:268`, `utils/write_values.py:97`; and `resource_policy.py` x5 (two paths — root, `extensions/`) at `types/base.py:110`, `types/resolvers.py:311`, `:361`, `utils/connections.py:684`, `utils/context.py:124`. These are **exactly F8's ambiguity class** — the property that made `resolvers.py` (four paths) a defect rather than a shorthand — and they are un-acquitted.
   - **One recorded "acquitted site" is not an instance of the convention at all.** R2's list includes `filters/inputs.py:738`; re-reading it, the reference is `` ``connection_field.py::_get_trimmed_filterset_class`` `` and **no `connection_field.py` exists anywhere in the repository**. The surrounding comment says "**Upstream** achieves this with a throwaway trimmed-subclass", so it names *strawberry-graphql-django's* module, not this package's. It is an external reference, correct as prose, and mis-classified as house-style shorthand.

   None of the 12 ambiguous occurrences involves a spec-016 symbol, so none is this cycle's to fix and none is a behavior defect. **Recorded so a later sweep neither "fixes" one acquitted instance and fractures the convention, nor acquits an ambiguous one on a ground that does not hold for it.** R2's own new citation `field_meta.py::_DjangoFieldLike` is a correct use: `find django_strawberry_framework -name field_meta.py` returns exactly one path, an `optimizer/` sibling of `walker.py`.

8. **An archived citation left stale by design, with an executable re-point target recorded.** [`docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md`][done-004]`:257`'s D23 row cites `walker.py` #"ONLY reason the two coexist safely" — the exact clause R2's reword deleted. Source: R2's pass-1 ruling, Worker 0's superseding disposition, R2 catalog item 10 as amended, R3 note 7. **Licensing: a Worker 0 decision on the merits, not a deferral by omission** — the row is a closed cycle's record of what the source said *at that cycle*, and rewriting a historical quotation to track a later reword falsifies the record it exists to preserve. **Re-verified: the citation is present at `:257`, the file is clean and untouched, and the recorded re-point target is executable** — `grep -c 'lets the two shapes coexist' django_strawberry_framework/optimizer/walker.py` -> **1**. The longer form first recorded (`…coexist safely`) greps to **0** because the cycle's own reflow moved it across a line break; the corrected single-line form is what a maintainer reversing the disposition would paste.

9. **The dual contract's exit condition — when it lands, DELETE rather than re-point.** When the registry-coverage gate lands, `_resolve_field_map`'s unregistered-model fallback disappears, the dual contract ends, and **the cross-reference, the whole `DUAL CONTRACT` paragraph, and the spec's first bounded exception should all be deleted**, not re-pointed. Source: R2's existence challenge, answered independently at plan time, by Worker 3 in both reviews, and at both final verifications. Licensing clause: the exit condition is named in the source itself — [`optimizer/walker.py::_resolve_field_map`][walker] #"registry-coverage gate lands" (**re-verified: greps to 1**). The rationale companion's recorded rejected alternative — make the walker's fallback build `FieldMeta` and delete the resolver fallbacks — **stays rejected**. No refactor is proposed by any round, and the question was asked four times rather than passed over in silence.

10. **The orphan `[backlog]` link def is a repo-wide class of EIGHT archived specs, ruled keep.** Source: R1 discretion item, R3 F9, R3 note 13. Licensing clause: none in the spec; a custodian ruling recorded in the companion's `### The `[backlog]` link definition — recorded, not fixed`. **Re-verified at this gate: eight specs define it with zero body uses (`spec-011`, `012`, `013`, `016`, `024`, `026`, `036`, `054`) and seven others define and use it.** A sweep that drops it must drop all eight in one change; dropping one creates the divergence removal was meant to prevent. The scaffold checker's `orphan` concept means "a def outside a category group", not "a def with no reader", so keeping costs nothing mechanically.

11. **The companion keeps 13 raw `path:NN` refs as a DECIDED exception to rule 27's letter.** Every one sits inside a passage explicitly scoped to a named historical commit (`de35a622` / `de35a622^`). Source: R3 spec-change row 6 and its `—` row, note 14. Licensing clause: a custodian ruling on the ground that a line number inside an immutable commit **cannot drift** — which is the drift rule 27 exists to prevent — and that `path::QualifiedName` cannot cite a shape the commit deleted, so converting them would be *less* accurate. The **nine at-`HEAD`** refs were symbol-qualified. **Recorded explicitly so a future mechanical sweep does not break the record**; four sibling companions carry the same shape (`spec-010` x2, `spec-012` x8, `spec-014` x37, `spec-016` x13) and the other eighteen carry none.

12. **`verified_upstream` `CardItem` rows are incomplete on 82 of 96 rows across the 49 done cards.** Source: R3 F10, note 15. Licensing clause: none — a board-convention measurement, not a deferral. **Re-derived exactly at this gate (49 / 96 / 82 / 14).** Recorded because F10's four-section enumeration invited the wrong conclusion about card 16's single incomplete row, and because **any future "every card item is complete" invariant must exclude this section or it will fail on almost every done card.**

13. **F11 is DECIDED not owed, not deferred: the card's 26 `CardItem` bodies are not restated.** Source: plan F11, R3 F11, note 16. Licensing clause: a custodian ruling on the merits — **a card body is the board's record of what the card said when it was written; the spec is the contract that must be checkable against `HEAD`.** The argument that fixed the spec (an unauditable contract must be fixed) does not transfer to a historical record. DB churn is the second reason and could not have carried the ruling alone. Had it been owed, the change was 18 `CardItem.text` rows on `Card(number=16)` plus three doc regenerates. **The flip condition is recorded in the companion:** if a card body ever became the only statement of a contract, or if the board began rendering card bodies as current source references.

14. **The Step 3c reference-resolution loop resolves only package-root-relative and `optimizer/`-sibling paths.** So it reports `types/`-relative shorthand (`finalizer.py`) as unresolved forever. Source: R2 build report, both reviews, both final verifications, catalog item 7, R3 note 8. Licensing: a plan-text defect Worker 1 corrected in place at R2's second final verification. **Any reuse must either add a `types/` candidate root (all seven rows then resolve) or name the expected row explicitly, or it reads a correct file as defective every time.**

15. **`scripts/review_inspect.py`'s output is structurally blind to a docstring change.** It replaces every string-literal token **including docstrings** with `...`, so a clean shadow overview is not evidence about a docstring diff. Source: R2 plan, build report, Worker 3's proof (`grep -c 'DUAL CONTRACT'` on the stripped file -> `0`), catalog item 8, R3 note 9. Licensing: none needed — a tool limitation, recorded so a future gate does not read a clean overview as a proof.

16. **`git diff -- <path>` reports a STAGED file as clean, and on a re-pass hides the earlier pass's half.** Source: R2's first final verification, R2 pass-2 note 4, R3 note 11. Licensing: none needed. **Always `git diff HEAD -- <path>`.** This gate used it for every diff, including `git diff HEAD --check` in place of the bare form the process text names — which is how the three `docs/review/` whitespace errors were seen at all.

17. **A `#"substring"` citation breaks on reflow as well as on reword, so the sweep is a LINE-WISE grep run as pre- AND postcondition — against the text you yourself wrote.** Source: R2's second final verification (two citations the ruling itself broke), R3's `### Verification runs` (a third, in R3's own new write). Licensing: a standing method rule, not a deferral. **This gate re-ran it: 11/11 citations at exactly one occurrence.** The gate found the same failure mode in a fourth guise — an unverified slug reimplementation reporting a correct anchor as dangling — recorded under `### Spec-side gates`.

18. **A concurrent session has staged this cycle's entire output together with two other sessions' WIP.** Source: R2's first final verification, both later passes, R3's `### Certification and baseline`, note 11. Licensing: **maintainer-facing; no worker may unstage it.** See the prominent note above. **Re-verified at this gate: 32 staged paths; R3's artifact and this one are `??` and outside the index.**

---

## Spec changes made (Worker 1 only)

**None.** The spec was read at this gate — its status/header lines (title; `Target release: 0.0.6 (per KANBAN.md card DONE-016-0.0.6)`; `Status: shipped.`; `Owner: package maintainer.`; the one-line rationale-companion pointer) still describe the build's current state, and this gate falsifies nothing in the body. No reference to a predecessor doc this build deleted survives.

The gate found **no factual error** in the spec or the companion, which is the only condition that would license reopening a pair R3 closed. The two spec-side facts this gate re-derived differently from a *round artifact* — the bare-basename population and its acquittal ground (catalog item 7) — are recorded in the **artifact** catalog and are not spec claims: the spec says nothing about that convention, and the companion's statement of it is scoped to the artifacts' own deliberation. Correcting a catalog entry is this gate's job; a spec edit would be scope creep.

`docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-terms.csv` — **not edited.** The reconciled body links exactly the two anchors the CSV carries, one row per anchor, and `check_spec_glossary.py` exits 0, which is the gate.

---

## Final status

`final-accepted`.

The gate ran every command in [`docs/builder/BUILD.md`][build] `## Final test-run gate` in the order given, plus the two integration-pass obligations the build plan folded in. Django's consistency checks, `ruff format --check`, `ruff check`, the scaffold check, `check_spec_glossary.py`, and `build_tree_md.py --check` all pass. The staged-anchor sweep is clean in every tree and the card's two historical anchors are gone from source. The floor-verification declaration of `none` was honored and is correct against what landed: the cycle's only source change is a function docstring whose four executable statements, signature, and return annotation are proved byte-identical to `HEAD` by AST — a fourth independent confirmation.

**Two failures are escalated to the maintainer and neither is attributable to this cycle.** One `pytest` row, `tests/test_sets_mixins.py::test_permission_facade_methods_are_single_sourced_on_the_mixin`, fails because a concurrent session's **uncommitted** `orders/sets.py` adds an `OrderSet._run_permission_checks` override that does not exist at `HEAD`, breaking a single-source assertion in a test file that is clean at `HEAD` — proved by blob, by `def`-presence at `HEAD` versus the worktree, and by diff membership. Three `git diff HEAD --check` whitespace errors sit in a concurrent session's `docs/review/rev-*.md` files, which the build plan's baseline-dirty list declares out of scope and [`AGENTS.md`][agents] rule 22 protects. A failing test is not worker-verifiable at all; recording the evidence and escalating discharges the obligation, and neither condition can be caused by five Markdown files and a comment. **The maintainer owns both, and owns the clean-`HEAD` run that is the authority on the suite** — the more so because the tree gained eight more concurrent paths, two of them spec-016 reader sites, *during* this gate.

The cycle delivered all three obligations. Nothing was skipped in the code: V1-V11 verified read-only rather than assumed, with one real defect found (a cross-reference to a module that never existed) and a second, deeper one surfaced by review and fixed rather than accepted (a false absolute in the one paragraph a consumer is instructed to obey, which this cycle's own first fix had extended). The spec now states the current contract with no chronology, its seven references symbol-qualified, its three stale reader sites re-pointed, its two bounded exceptions stated as design, and its false test claim corrected. And the explanation lives in a 42KB rationale companion keyed to the spec by heading and anchor, honest in its own provenance section that it is a reconstruction rather than a move.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-016]: ../SPECS/spec-016-fieldmeta_consolidation-0_0_6.md
[spec-016-rationale]: ../SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md

<!-- docs/builder/ -->
[bld-r1]: bld-016-r1-rationale_and_spec_reconciliation.md
[bld-r2]: bld-016-r2-walker_source_reference_fix.md
[bld-r3]: bld-016-r3-doc_completion_archive_audit.md
[build]: BUILD.md
[build-016]: build-016-fieldmeta_consolidation-0_0_6.md
[done-004]: DONE/build-004-optimizer_beyond-0_0_3.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[converters]: ../../django_strawberry_framework/types/converters.py
[field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-registry]: ../../tests/test_registry.py
[test-sets-mixins]: ../../tests/test_sets_mixins.py

<!-- examples/ -->
[db]: ../../examples/fakeshop/db.sqlite3

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
