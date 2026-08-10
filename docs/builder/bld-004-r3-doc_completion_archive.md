# Build: R3 — Finish the documentation and audit the archive (spec-004)

Spec reference: `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` (whole file, read-only in this item; 236 lines / 36,223 bytes, byte-stable since R2's pass-2 apply)
Rationale file: `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` (read-only in this item; 1,309 lines / 94,318 bytes)
Status: final-accepted

**Why this is not a procedural closure.** The dispatch anticipated one: the build plan's `## Worker-0-verified facts` records card 4 as `DONE-004-0.0.3`, `SpecDoc.path` already archived, ten glossary links matching the terms CSV exactly, `import_spec_terms --check` green, and every entry `shipped`. **Every one of those re-derived clean.** But the durable-doc audit — the half the plan recorded as "already correct — verify, do not assume" — found **two false-at-HEAD statements about the B1–B8 surface in `docs/GLOSSARY.md`**, both rendered faithfully from `examples/fakeshop/db.sqlite3` and therefore fixable only by a DB edit plus a regenerate. That is builder work (`BUILD.md` `### Generated docs are DB-backed`), and this item's dispatch forbids Worker 1 from performing it. So `Status: planned`, which Worker 0 reads as "dispatch Worker 2" under the unmodified chain `### Deviation 2` reserves for an R3 that has real Worker 2 work.

**Nothing was edited by this pass.** No spec, no rationale, no sibling, no source, no test, no CSV, no DB, no generated doc. The only file this pass wrote is itself.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Refreshed for the **whole package** this pass — the `worker-1.md` `### Package-wide helper inventory before helper planning` AST script, run over `django_strawberry_framework/` with its output directed to this session's scratchpad **outside the repository** rather than to `docs/shadow/`, because `docs/shadow/` is not in this item's writable set. 1,782 lines. Shapes searched: `check_schema`, `glossary`, `render`, `regenerate`. The only relevant hit is the boundary under audit itself — `DjangoOptimizerExtension.check_schema(schema) — Audit schema-reachable types for unoptimized relations.` Every `Render` hit is unrelated (error-message formatting, keyset SQL, lateral SQL, the `inspect_django_type` table). **No glossary- or markdown-rendering helper exists inside the package**: the three renderers live in `scripts/` (`build_glossary_md.py`, `build_kanban_md.py`, `build_kanban_html.py`), outside the coverage gate. No new helper is proposed and none is warranted; the condition that would change the answer is a *second* durable-doc surface needing the same DB-text-then-regenerate treatment in one pass, which one edit to one `GlossaryTerm.body` does not create.
- **Existing patterns reused.** The whole remedy is an existing pattern: `worker-0.md` `## Closing out a kanban card` and `BUILD.md` `### Generated docs are DB-backed: edit the DB, then regenerate`. Worker 2 edits `GlossaryTerm.body` through the Django ORM (never raw SQL — a raw insert skips the `post_save` side-row the render reads), then runs `scripts/build_glossary_md.py`. No new mechanism.
- **New helpers justified.** None. This item adds no function, class, constant, validation branch, or coercion utility, in the package or anywhere else.
- **Duplication risk avoided.** One, and it is why finding **F2** is scoped the way it is below. The naive fix for F2 would copy `docs/README.md`'s `## Nested connection indexing` prose into the `OptimizerHint` glossary entry, putting the strategy contract in two durable files that then drift apart — exactly the failure `docs/SPECS/spec-002-optimizer-0_0_2.md` #"each own the surface they added" exists to prevent, and the same shape R2 spent two apply passes removing from the spec. The prescribed fix therefore adds **one bullet naming the member and pointing at the section that owns it**, and narrows one false exhaustive clause. It states no backend, no selection rule, and no precedence rule.
- **Against R1's and R2's output.** R3 writes neither durable file, so no overlap is possible. This artifact restates no R1 or R2 finding as its own; the 18-item handoff is dispositioned by reference in `### 5.` below, with each disposition re-derived rather than copied.

### Boundary count, and the split question answered

**Zero new boundaries.** This item introduces no guard, gate, cap, rejection path, or validation branch — it corrects two sentences in a generated document's source of truth. `BUILD.md` `## Failability proofs` scopes the obligation to new boundaries, so none is owed and Worker 2's `### Failability proofs` subsection reads `None; this pass introduced no new boundary.`

**One unit, not two.** F1 and F2 are two sentences in **one file**, reached through **one mechanism** (an ORM edit to a `GlossaryTerm.body`), verified by **one regenerate** and **one set of four `--check` runs**. Splitting them would double the DB-write / regenerate / re-verify cycle to buy nothing; the diff is under ten lines and neither finding's fix constrains the other's. Answered in writing per `BUILD.md` `### Slice splitting`.

### Implementation steps

Line numbers are pin-at-write-time navigational hints, taken at `HEAD` `ff03c137` with the working tree as recorded in `### Working-tree state`. Verify against current content before editing — a concurrent session is active on this tree and on this DB.

1. **F1 — `check_schema` is a static method, not a classmethod.** In `examples/fakeshop/db.sqlite3`, via the Django ORM from the repository root:

   ```
   uv run python examples/fakeshop/manage.py shell -c "..."
   from apps.glossary.models import GlossaryTerm
   t = GlossaryTerm.objects.get(anchor='djangooptimizerextension')
   ```

   In `t.body` — **32 lines; the target is line 30**, the entry's last prose line, two lines above the closing `**See also:**` line — replace the single occurrence of the token `Classmethod` with `Static method`. The whole line reads, before:

   > ``Constructor accepts a `strictness` argument — see [Strictness mode](#strictness-mode). Classmethod [`check_schema`](#schema-audit) audits schema-reachable `DjangoType`s.``

   and after:

   > ``Constructor accepts a `strictness` argument — see [Strictness mode](#strictness-mode). Static method [`check_schema`](#schema-audit) audits schema-reachable `DjangoType`s.``

   Then `t.save()`. **`Classmethod` occurs exactly once in that body** (`t.body.count('Classmethod')` -> `1`, `t.body.lower().count('classmethod')` -> `1`), so a token replacement cannot over-reach. Nothing else in the body changes; the inline link target `#schema-audit` is unchanged and already resolves.

2. **F2 — the `OptimizerHint` entry enumerates four modes as exhaustive; five ship.** `GlossaryTerm.objects.get(anchor='optimizerhint')`. Two edits inside `body`:

   - Under `Supported modes:`, **append a fifth bullet after** the `OptimizerHint.prefetch(Prefetch(...))` bullet:

     > ``- `OptimizerHint.strategy(...)` — select the nested-connection fetch backend for one Relay connection field. The backends and their selection rules are documented under "Nested connection indexing" in `docs/README.md`.``

   - In the `Validation:` paragraph, the clause ``The factories (`SKIP`, `select_related()`, `prefetch_related()`, `prefetch(Prefetch(...))`) are the documented consumer API`` presents four as the whole consumer API. Add `strategy(...)` to that parenthesis. **Leave the following clause — "the same four shapes are the only ones the walker dispatches" — factually intact**, because it is *true*: `nested_strategy` is read by `optimizer/nested_planner.py`, not by `optimizer/walker.py`. Reword it only enough that "four" still refers to the walker-dispatched set and not to the factory list it now no longer matches (e.g. "…and the four cardinality shapes above are the only ones the walker dispatches"). **Do not** import backend names, precedence rules, or the extension-wide default into this entry — `docs/README.md` owns them (see `### DRY analysis`).

   Then `t.save()`.

3. **Regenerate the one generated doc the DB edit feeds**, from the repository root:

   ```
   uv run python scripts/build_glossary_md.py
   ```

   Never hand-edit `docs/GLOSSARY.md`; the next render reverts a hand-edit.

4. **Prove the write landed and nothing else moved.** Run all four freshness checks; all four must exit 0:

   ```
   uv run python scripts/build_glossary_md.py --check
   uv run python scripts/build_kanban_md.py --check
   uv run python scripts/build_kanban_html.py --check
   uv run python scripts/build_tree_md.py --check
   ```

   Then `git status --short` and confirm the **only** additions to the list in `### Working-tree state` below are `docs/GLOSSARY.md` and `examples/fakeshop/db.sqlite3`. `KANBAN.md` and `KANBAN.html` must **not** appear: card 4's glossary table renders each term's status, not its body, and neither finding touches a status. If either appears, stop and report — do not revert it (`AGENTS.md` rule 34), and attribute it by `iterdump()` set-difference before treating it as this item's output.

5. **Re-run the chain the edit could break**, and quote each result verbatim in the build report:

   ```
   uv run python examples/fakeshop/manage.py import_spec_terms --check
   uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
   uv run python scripts/check_trailing_commas.py --check docs/GLOSSARY.md docs/builder/bld-004-r3-doc_completion_archive.md
   ```

   `import_spec_terms --check` must still print `OK: 49 done cards have glossary links.` — **the read-only `--check` form only; the plain sync form writes the DB.** `check_spec_glossary.py` must still print `OK: 10 terms - all have glossary entries and at least one spec link.`: both edited anchors (`djangooptimizerextension`, `optimizerhint`) are among spec-004's ten, and each is carried by exactly one spec link, so a broken anchor breaks card 4's wrap chain. Neither edit renames an anchor or a heading, so both should be untouched — **prove it, do not assume it.**

6. **Do not touch anything else.** No spec, no rationale, no sibling spec, no source, no test, no `CHANGELOG.md`, no terms CSV, no `docs/TREE.md`, no `KANBAN.md` / `KANBAN.html`. The three deferred sibling-staleness items in `### Notes for Worker 1 (spec reconciliation)` are **not** this pass's to fix.

### Test additions / updates

**None, and none is owed.** This cycle changes no code (`## Build-wide context flags`), and `docs/GLOSSARY.md` is a rendered document with no test tier of its own — its correctness gate is the four `--check` renders plus `import_spec_terms --check`, all of which step 4 and step 5 run. No temp test is appropriate: there is nothing to demonstrate that a `--check` exit code does not already prove. Worker 2 runs **no** `pytest` (`AGENTS.md` rule 15; the full sweep is the final gate's job) and **no** `ruff` (no Python file changes). No `--cov*` flag anywhere.

### Implementation discretion items

Assessed and decided as Worker 2's:

- **The exact wording of F2's fifth bullet and of the narrowed exhaustive clause.** The content is fixed above (name the member, point at `docs/README.md`'s section, keep the walker claim true, import no backend rules); the sentence shape is Worker 2's, subject to matching the entry's existing bullet register.
- **Whether the two `GlossaryTerm` edits happen in one `manage.py shell -c` invocation or two.** No difference in outcome.
- **`Static method` vs `A static method`** at the head of F1's sentence. Either is house-consistent; `Static method` is the minimal token swap and preserves the sentence's existing rhythm.

Not discretionary, and not delegated: **which** clause is corrected in F2. The false claim is the *exhaustive framing of the factory list*, not the walker-dispatch count. Flattening both into "five shapes the walker dispatches" would replace a true statement with a false one.

### Dispatched findings checklist

Spec-004 has no `## Slice checklist`, and this is not a review round, so per `worker-1.md` planning step 8 and `BUILD.md` `### Dispatched findings checklist` the boxes below stand in that position: one per required change, one per audit obligation this item owes, one per handoff item that needed live re-derivation. **Worker 2 ticks only a box whose work actually landed in its diff**; Worker 1 audits every tick at final verification. Boxes marked **(W1, done)** were discharged by this planning pass and are already ticked with their evidence in the audit report below — Worker 2 neither re-runs nor re-ticks them.

**Required changes (Worker 2):**

- [x] F1 — `docs/GLOSSARY.md` #"Classmethod [`check_schema`]" corrected to a static method at its DB source (`GlossaryTerm(anchor='djangooptimizerextension').body`), and the doc regenerated
- [x] F2 — `GlossaryTerm(anchor='optimizerhint').body` gains the fifth `OptimizerHint.strategy(...)` mode and drops the false exhaustive framing of the factory list, without importing the nested-connection backend rules `docs/README.md` owns
- [x] `scripts/build_glossary_md.py` run, and all four generated-doc `--check`s exit 0 afterwards
- [x] `git status --short` shows exactly two additions (`docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3`) against the recorded baseline, and `KANBAN.md` / `KANBAN.html` are unchanged
- [x] `import_spec_terms --check` (read-only form) re-run **after** the DB write and still `OK: 49 done cards have glossary links.`
- [x] `check_spec_glossary.py` re-run and still `OK: 10 terms - all have glossary entries and at least one spec link.`
- [x] `check_trailing_commas.py --check` green on `docs/GLOSSARY.md` and on this artifact

**Audit obligations (Worker 1, discharged this pass):**

- [x] **(W1, done)** Durable-doc audit — `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `KANBAN.md` read against the B1–B8 surface at HEAD (`### 1.`)
- [x] **(W1, done)** Archive completeness, inbound direction — every reference TO spec-004 re-swept, not trusted from the plan's table (`### 2a.`)
- [x] **(W1, done)** Archive completeness, outbound direction — every link definition in the spec and the rationale resolved on disk, anchors included (`### 2b.`)
- [x] **(W1, done)** Archive completeness, companion depth — the rationale's `docs/SPECS/appx/` relative depth verified per group (`### 2c.`)
- [x] **(W1, done)** `SpecDoc.path` read live from the DB and confirmed archived (`### 3.`)
- [x] **(W1, done)** Terms CSV confirmed one row per anchor, ten anchors, matching card 4's ten glossary links exactly (`### 3.`)
- [x] **(W1, done)** Staged-anchor sweep re-run and every hit attributed (`### 4.`)
- [x] **(W1, done)** All 18 R3 handoff items dispositioned, each re-derived live (`### 5.`)
- [x] **(W1, done)** `examples/fakeshop/db.sqlite3` attributed by `iterdump()` set-difference against a read-only HEAD copy, never by file bytes (`### Working-tree state`)

---

## Audit report (Worker 1)

`BUILD.md` `## Claims are proven mechanically` governs every count here: each was produced by running the command and pasting its output **after** the last edit to this file, never quoted from the build plan or from R1/R2. Where a figure disagrees with the plan, the disagreement is stated rather than smoothed.

**`HEAD` re-derived, not quoted:** `git rev-parse HEAD` -> `ff03c1372365edcad488ff4671389d88ae145276` (`ff03c137`). **Nothing of this cycle was swept:** `git log -1 --format='%h %s' -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> `20a9752f docs(spec-003): reconcile the O4 spec with HEAD and extract its rationale`, i.e. still the spec-003 cycle's one-clause B4 rider, exactly as required. The check used `git log`, never `git status` alone. No `git stash`, `git checkout`, `git restore`, or `git worktree` was run in this pass.

### 1. Durable-doc audit — do the durable docs describe the B1–B8 surface as shipped?

**Method.** Each of the four docs was read against source at HEAD rather than against the spec, because the spec is R2's output and grading a doc against another document proves only that two documents agree. Where the spec is cited it is as a third witness.

#### `docs/TREE.md` — clean

`uv run python scripts/build_tree_md.py --check` -> `docs/TREE.md is up to date.` exit 0. The `optimizer/` block (`:249`, mirrored at `:373`) lists fourteen modules, each with a current one-line docstring summary: `extension.py`, `field_meta.py`, `hints.py`, `plans.py`, `walker.py`, `_context.py` and the eight later-spec modules. **No staging language** — no "planned", no "Slice N", no `TODO(` — anywhere in the optimizer blocks, which is the `ARTIFACT.md` `### Documentation / release sanity` check for a script-rendered doc. The test-tree blocks at `:515` / `:736` name `test_extension.py`, `test_hints.py`, `test_field_meta.py`, `test_plans.py`, `test_walker.py`, i.e. every B-slice's test module. **No change owed.**

#### `KANBAN.md` — clean

`uv run python scripts/build_kanban_md.py --check` -> `KANBAN.md is up to date.` exit 0; `uv run python scripts/build_kanban_html.py --check` -> `KANBAN.html is up to date.` exit 0. Card 4 renders at `:4887`-`:4960` and every claim in it holds at HEAD: the `Spec:` row (`:4894`) points at the archived path, the ten-row glossary table matches the terms CSV anchor for anchor, the eight `Scope` rows name B1–B8 correctly, and the two `Note` rows the plan flagged as ahead-of-spec (`:4953` subtree-aware reconciliation, `:4954` the historical fragment-spread / multi-operation cache-key fixes) both still read correctly. `:143` is the index row, `:2771` is `spec-035`'s card citing spec-004 B8 and the B1 printed-AST key — correct as written.

**One observation, not a required change.** Card 4's B1 `Scope` row reads "plan cache keyed by selected operation AST, directive variables, model, and root runtime path" — **four** components, where the reconciled spec `### B1` `:19`-`:25` and `optimizer/extension.py::DjangoOptimizerExtension._build_cache_key` both carry **five** (the resolver's origin Strawberry type is the fifth). The row is not *wrong*; it is a Done card's record of declared scope, and the `origin` component arrived with `docs/SPECS/spec-018-meta_primary-0_0_6.md`, three releases after this card shipped. A `Scope` row is a historical statement, the spec is the contract, and rewriting board history to match a later spec is the opposite of what a card records. **Deferred, not fixed** — recorded in `### Notes for Worker 1 (spec reconciliation)` so the final gate's catalog carries it.

#### `docs/README.md` — clean on the B1–B8 surface

`docs/README.md` is hand-authored, not rendered. Its optimizer coverage is the `DjangoOptimizerExtension` bullet under `## Today and coming next` and the `## Nested connection indexing` section at `:175`. The bullet names plan caching, FK-id elision for `{ relation { id } }`, the `get_queryset` -> `Prefetch` downgrade, and strictness mode (`off` / `warn` / `raise`), then hands the rest to `docs/GLOSSARY.md` — all four correct at HEAD. `## Nested connection indexing` `:177`-`:189` documents `OptimizerHint.strategy(...)` in full, with a worked `Meta.optimizer_hints` example. **No `check_schema` claim anywhere in the file** (`grep -rn 'check_schema' docs/*.md TODAY.md README.md GOAL.md KANBAN.md` returns hits only in `docs/GLOSSARY.md` `:745` / `:1799` and `KANBAN.md` `:4280`, the last a bare file-path row).

**One observation, not a required change.** The `## Today and coming next` summary bullet reads "`OptimizerHint` — per-relation overrides (`SKIP`, `select_related`, `prefetch_related`, custom `Prefetch`)", omitting `strategy`. Unlike F2 this is **not** a false exhaustive claim: it is a one-line summary in a shipped-feature list, it asserts no completeness, and the same file documents `strategy` in full 55 lines later. Adding the token would make the two durable docs read alike and costs one word — **recommended, non-blocking, and explicitly deferrable.** Recorded in `### Notes for Worker 1 (spec reconciliation)`; if Worker 0 folds it into Worker 2's dispatch it is a `docs/README.md` edit, not a DB edit.

#### `docs/GLOSSARY.md` — TWO false-at-HEAD statements about the B1–B8 surface

`uv run python scripts/build_glossary_md.py --check` -> `docs/GLOSSARY.md is up to date.` exit 0, so both statements below are **faithful renders of the DB**, not hand-edit drift, and both must be fixed at the DB.

Everything else in the entry set is correct. All ten of card 4's anchors resolve, and the B-owned entries carry the right shipped versions and the right bodies: `FK-id elision` (`:946`, `shipped (0.0.3)`) states all four fallbacks and the branch isolation; `Meta.optimizer_hints` (`:1281`, `0.0.3`); `Plan cache` (`:1479`, `0.0.3`) names **all five** key components including the origin type and the root runtime path, plus the `0.0.9` nested-vs-root pagination refinement; `Queryset diffing` (`:1528`, `0.0.3`) states consumer-wins, subtree-aware reconciliation, plain-string absorption and the `only()` cooperation rule; `Schema audit` (`:1795`, `0.0.3`) states the union and interface descent and the `(source_model, field_name)` dedupe; `Strictness mode` (`:1942`, `0.0.3`) states all three levels and the lazy-load-only firing rule; `DjangoOptimizerExtension` (`:712`) carries the module-level-singleton-factory guidance `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` Decision 3 owns. **That is the B1–B8 surface described as shipped**, and it is why the two findings below are precise rather than sweeping.

**F1 — `check_schema` is called a classmethod; it ships as a static method.**

`docs/GLOSSARY.md` `:745`, the last prose line of the `DjangoOptimizerExtension` entry (`:712`-`:748`), immediately above its `**See also:**` line:

> ``Constructor accepts a `strictness` argument — see [Strictness mode](#strictness-mode). Classmethod [`check_schema`](#schema-audit) audits schema-reachable `DjangoType`s.``

At HEAD, `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.check_schema` is decorated `@staticmethod` and takes no `cls`:

```
1247-    @staticmethod
1248:    def check_schema(schema: Any) -> list[str]:
```

**Provenance, re-derived rather than assumed.** `git log -S'@classmethod' -- django_strawberry_framework/optimizer/extension.py` returns two commits; the older, `f18c1fed`, carries the word only inside spec-004's **pseudo-code comment** (`#   @classmethod` / `#   def check_schema(cls, schema):`), and by `f83bb71b` (2026-05-20) the shipped decorator is already `@staticmethod`. So the glossary inherited the spec's *proposal* and was never corrected when the implementation diverged — precisely the defect class R2's finding **H3** fixed inside the spec, leaving the glossary as the last durable carrier. The reconciled spec `### B6` `**Public API.**` `:127` now reads "is a static method", so **the durable doc currently contradicts both the source and the spec** on a B6 contract statement. The rationale already records the correction twice (`:730`, `:1142`), so the record is right and only the glossary is wrong.

**Scope of the fix.** `grep -rniE 'classmethod[^.]{0,40}check_schema|check_schema[^.]{0,40}classmethod'` over `*.md` / `*.py` / `*.html` returns **one durable-doc hit** — this one. The other hits are the rationale's two records of the correction and two per-cycle scratchpad lines. `Classmethod` occurs **exactly once** in the `GlossaryTerm(anchor='djangooptimizerextension')` body (32 lines), so the edit is a single unambiguous token swap. The `Schema audit` entry (`:1799`) states no method kind and needs nothing.

**F2 — the `OptimizerHint` entry enumerates four modes as the whole consumer API; five ship.**

`docs/GLOSSARY.md` `:1390`, the `OptimizerHint` entry (`shipped (0.0.3)`), lists under `Supported modes:` exactly four bullets — `SKIP`, `select_related()`, `prefetch_related()`, `prefetch(Prefetch(...))` — and its `Validation:` paragraph then says:

> ``The factories (`SKIP`, `select_related()`, `prefetch_related()`, `prefetch(Prefetch(...))`) are the documented consumer API; direct construction is supported but the same four shapes are the only ones the walker dispatches…``

At HEAD a **fifth** factory ships: `django_strawberry_framework/optimizer/hints.py::OptimizerHint.strategy` (`:174`), setting the `nested_strategy` field (`:105`), validated in `__post_init__` (`:155`-`:167`) through `optimizer/nested_fetch.py::resolve_strategy` and rejected outright in combination with `SKIP` / `force_select` / `force_prefetch`. It is **documented consumer API**: `docs/README.md` `:177`-`:189` teaches it under `## Nested connection indexing` with a worked example. So the clause "the factories … are the documented consumer API" is false as an enumeration.

**The half that is TRUE and must not be "fixed".** `nested_strategy` is read by `django_strawberry_framework/optimizer/nested_planner.py` (`:191`, `:1452`), **not** by `optimizer/walker.py`. So "the same four shapes are the only ones the walker dispatches" is accurate, and collapsing the two clauses into "five shapes the walker dispatches" would trade a true statement for a false one. This is why the prescribed fix in `### Implementation steps` step 2 corrects the factory enumeration and leaves the walker-dispatch count alone.

**Why this is in R3's charter even though `strategy` is not 0.0.3 surface.** The member arrived with the nested-connection work (`docs/SPECS/spec-033-connection_optimizer-0_0_9.md` / `spec-046`), so on a version reading it is not B1–B8. But the entry it lives in **is** B4's durable home — `OptimizerHint` is one of card 4's ten glossary anchors, and the reconciled spec `### B4` `:97` now names `strategy(...)` as a fifth member with a pointer to the section that owns the backends. The glossary is the one durable doc that contradicts that, and it does so by presenting an incomplete list as complete. This glossary already carries later-version refinements inside `shipped (0.0.x)` entries as a matter of house pattern (`only() projection` `:1380` carries `0.0.10` and `0.0.11` amendments; `Strictness mode` `:1942` carries a `0.0.9` one), so the entry's `0.0.3` status line is no argument against the addition.

**If Worker 0 judges F2 outside R3's charter it defers cleanly** to the final gate's catalog under the same owner as the `docs/README.md` observation. F1 does not: it is a false statement about a B6 contract in the durable doc R3 is chartered to audit.

### 2. Archive completeness — all three cross-reference directions

#### 2a. Inbound — every reference TO spec-004

Re-swept rather than read off the plan's `### Every reference TO spec-004` table. **The decisive result is negative and exhaustive:** `grep -rn 'docs/spec-004' .` returns **no match anywhere in the tree**, so not one reference points at the pre-archive location. Every path-form reference resolves to `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`, which exists.

Population, measured two ways. `grep -rl 'spec-004-optimizer_beyond-0_0_3' .` -> **19 files** (the filename form). `grep -rl 'spec-004' .` -> **22 files** (the bare token, which also takes prose mentions). The 22 partition as: the two files under audit; **eleven durable inbound** — `KANBAN.md`, `KANBAN.html`, `docs/SPECS/spec-002-optimizer-0_0_2.md`, `spec-003-optimizer_nested_prefetch_chains-0_0_2.md`, `spec-029-consumer_dx_cleanup-0_0_9.md`, `spec-033-connection_optimizer-0_0_9.md`, `spec-035-optimizer_hardening-0_0_10.md`, `docs/SPECS/appx/spec-002-…-rationale.md`, `appx/spec-003-…-rationale.md`, `appx/spec-005-django_type_contract-0_0_3-rationale.md`, `whitepaper.md`; and **nine per-cycle scratchpads** under `docs/builder/`.

Every durable inbound reference was **read in place**, not counted:

- `spec-002` `:6` — "each own the surface they added". Correct, and it is the clause that scoped R2's anti-absorption rule. Load-bearing; unchanged.
- `spec-003` `:11` — "treats O4 as the last foundation slice", naming B1/B7/B3/B4/B5/B2/B6. Correct, and reconciled by its own cycle.
- `spec-029` — 3 filename-form hits (`:15`, `:331`, plus the `[spec-004]` definition at `:771`) recording that spec-004's extension-lifecycle model is stale. **Correct, and it is D5's authority**; the direction of correction runs toward spec-004, never the reverse. Its own separate staleness is deferred item 4 below.
- `spec-033` `:9` and `spec-035` `:9`, `:104`, `:121`, `:178`, `:423` — predecessor citations of the B1 cache key, B3 strictness, and B8's consumer-wins drop. All correct as written and consistent with the reconciled spec, including `spec-035` `:104` crediting the consumer-wins stance **back** to spec-004 B8, which is what R2's own correction rests on.
- `appx/spec-002-…-rationale.md` `:40`, `:157`, `:199`, `:244`, `:248` and `appx/spec-003-…-rationale.md` `:333`, `:352`, `:356`, `:382`, `:1017` — the prior rationales' accounts of the optimizer-family split and of the discharged B4 rider. Correct as history. `appx/spec-003` `:356` confirms the `## B4 … Depends on.` rider is discharged, which the spec's current `:111` bears out — it ends "composes naturally with O4 (nested chains) and O6 (downgrade rule)", with no "once those land".
- `whitepaper.md` `:115` — an essay citing "the spec-004 printed-AST cache key". Accurate against HEAD; out of scope (not a standing doc, in no writable list). Note only, as the plan directed.
- **New since the plan's table:** `docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md` `:100`, `:295` — the concurrent card-005 cycle citing "the maintainer decision recorded on the spec-004 cycle" about problem-statement competitive argument. Bare cycle mentions, no path, correct as written, out of scope. Recorded so the next pass does not read it as new rot.

#### 2b. Outbound — spec-004's own links, and the rationale's

Verified with a parser written for this pass (partitions at `<!-- LINK DEFINITIONS -->`, strips code spans before scanning uses, normalizes each target against the **source file's own directory**, slugs every heading in the target file **keeping `_`**, and checks each anchor against that set). Handoff item 18's standing hazard was live in the predicted place and keeping `_` resolves it.

- Spec: **11 definitions / 11 used / 0 undefined / 0 unused.**
- Rationale: **24 definitions / 24 used / 0 undefined / 0 unused.**
- **35/35 targets exist on disk and every anchored target's heading resolves**, `../GLOSSARY.md#metaoptimizer_hints` included.

This is re-derived on disk this pass, not inherited from R2 — the plan's `### Fourth change` warns that R1's reading has an expiry because the concurrent renumber moved files eight of the rationale's sibling links point at. Those eight resolve.

#### 2c. Companion depth — the rationale sits two levels below `docs/`

Correct per group, and verified by the disk-exists check above rather than by inspection alone. From `docs/SPECS/appx/`: `<!-- Root -->` uses `../../../GOAL.md`; `<!-- docs/ -->` uses `../../README.md` and `../../GLOSSARY.md`; `<!-- docs/SPECS/ -->` uses `../spec-NNN-….md` for the eleven archived siblings and **bare filenames** for the two `appx/` companions (`spec-002-…-rationale.md`, `spec-003-…-rationale.md`) — which is `START.md`'s closed-list rule, a subdirectory sharing its parent's group rather than earning an eleventh header; `<!-- docs/builder/ -->` uses `../../builder/BUILD.md` and `../../builder/worker-1.md`. All ten canonical group headers are present and in order; `check_trailing_commas.py --check` exit 0 on both files confirms the scaffold.

### 3. `SpecDoc.path`, and the terms-CSV chain

Read live from `examples/fakeshop/db.sqlite3` through the ORM, not from the rendered board:

- `Card.objects.get(number=4)` -> `card_id` **`DONE-004-0.0.3`**, `status.key` **`done`**, `target_version.number` **`0.0.3`**, title **`Optimizer beyond slices B1-B8`**.
- `SpecDoc` for card 4 -> name `spec-004-optimizer_beyond-0_0_3`, **`path` = `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`** — already archived, no repoint owed. `url` derives from it read-only (`…/blob/main/docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`), confirming the property tracks `path`.
- `card.glossary_links.count()` -> **10**, and the ten anchors are `configurationerror`, `djangooptimizerextension`, `djangotype`, `fk-id-elision`, `metaexclude`, `metafields`, `metaoptimizer_hints`, `only-projection`, `optimizerhint`, `queryset-diffing` — **exactly the ten in `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-terms.csv`**, whose ten data rows carry **one row per anchor with no anchor repeated**, which is what `import_spec_terms` requires and what a green `check_spec_glossary` alone does not prove. **All ten terms carry `GlossaryStatus: Shipped`.**
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> **`OK: 49 done cards have glossary links.`** exit 0. Read-only `--check` form only; the writing form was not invoked in this pass.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **`OK: 10 terms - all have glossary entries and at least one spec link.`** exit 0, character-identical to the pre-flight baseline.

**One correction to the plan's `## Worker-0-verified facts`, stated rather than smoothed.** It reads "the **five** B-owned entries are all `shipped (0.0.3)`" and then names **six** (`FK-id elision`, `Meta.optimizer_hints`, `Plan cache`, `Queryset diffing`, `Schema audit`, `Strictness mode`). Measured this pass, the correct figure is **seven** — those six plus `OptimizerHint` (`:1390`, `shipped (0.0.3)`). The conclusion the sentence supports is unaffected: every B-owned entry is `shipped (0.0.3)`, and the glossary needs no status flip. The numeral is in Worker 0's file and this pass does not edit it; it is recorded here so the final gate does not re-derive a third figure.

### 4. Staged-anchor sweep

`BUILD.md` `## Cross-slice integration pass` step 6, folded into R3 because this cycle has no integration pass.

`grep -rEn 'TODO\(spec-004|TODO-(ALPHA|BETA|STABLE)-004' .` -> **3 hits, all in this cycle's own per-cycle scratchpads, all of them the grep pattern itself quoted in prose describing the sweep:**

- `docs/builder/build-004-optimizer_beyond-0_0_3.md:29` and `:343` — the plan's R3 scope paragraph and its checklist row.
- `docs/builder/bld-004-r2-spec_reconciliation.md:3889` — R2's "what I did not do, because it is R3's" paragraph.

**Zero hits outside `docs/builder/`.** The same sweep filtered to exclude that directory returns nothing: no source, no test, no example, no standing doc, and none in the spec or the rationale. So **no staged anchor exists anywhere in shipped material**, and the obligation is discharged.

**This is why the figure differs from the plan's "zero hits anywhere" baseline, and the difference is not drift.** That baseline was taken at pre-flight, which by `BUILD.md` `## Pre-flight checks` **gates plan creation** — the plan did not yet exist, and neither did R2's artifact. All three hits are text this cycle wrote about the sweep. Stating the raw number and then attributing it is the honest form; reporting "zero" would require silently excluding the files that make it non-zero.

**The `B1`–`B8` provenance markers in package source were NOT swept**, per `AGENTS.md` rule 27's KEEP list and the plan's explicit instruction. Re-measured for the record: `grep -roE '\bB[1-8]\b'` over `django_strawberry_framework/optimizer/` plus `types/resolvers.py` -> **21 occurrences across 4 files** (`extension.py` 7, `plans.py` 7, `types/resolvers.py` 5, `walker.py` 2), which reproduces the plan's `B1 ×4, B2 ×1, B3 ×4, B5 ×1, B8 ×11` = 21. These are spec-Decision pointers, not staged anchors.

### 5. The 18-item R3 handoff — every item dispositioned

The list is `docs/builder/bld-004-r2-spec_reconciliation.md` `## Review (Worker 3, pass 4)` `### Notes for Worker 1 (spec reconciliation)`. Each item was re-derived live at this tree state rather than graded against R2's own audit of it.

| # | Disposition | Re-derived this pass |
|---|---|---|
| 1 | **Verified-and-clean.** No open finding to inherit | R2 closed `final-accepted` with pass 4 filing nothing; nothing routed to R3 as an unaddressed finding |
| 2 | **Deferred** — `check_optimizer` management command + custom-resolver detection, never built, **no card exists** | `grep -c check_optimizer` over the spec -> **0**; `django_strawberry_framework/management/commands/` ships `export_schema.py` and `inspect_django_type.py` only |
| 3 | **Deferred** — the `_record_relation_access`-before-elision ordering invariant has no automated guard | `walker.py::_record_relation_access` is defined at `:826` and called at `:722`, `:786`, `:1004` with no assertion on the ordering. A source change, out of scope for a documentation cycle |
| 4 | **Deferred, and now WIDER than recorded** — see below the table | The "locked `0.316.0`" phrasing is still live in `spec-029` at **10 occurrences across 8 lines** (`:24`, `:25`, `:43`, `:133`, `:150` ×2, `:329`, `:331` ×2, `:653`) |
| 5 | **Deferred** — the `spec-003` pair's wrong `spec-035` plan-immutability attribution, seven sites | `spec-003` `:30` #"finalized at handoff" still present; `grep -n '\]\[spec-035\]\|spec-035-optimizer'` over its companion -> `:253`, `:521`, `:598`, `:604`, `:855`, `:952` + the `:1050` definition. 1 + 6 = **7**. Both files untouched here |
| 6 | **Deferred** — three B7 test names still spell the retired `_optimizer_field_map` | `tests/optimizer/test_field_meta.py:322`, `:339`, `:362`. Carded on `TODO-ALPHA-052-0.1.0`; no test file is writable here |
| 7 | **Verified-and-clean; both populations reproduce exactly** | `grep -o 'docs/SPECS/spec-0[0-9][0-9]' \| sort \| uniq -c` -> **21 occurrences across 10 siblings** (spec-033 ×5, spec-035 ×4, spec-003 ×3, spec-002 ×2, spec-018 ×2, spec-015 / 023 / 029 / 032 / 047 ×1). Wider filename-form population -> **17 lines / 23 occurrences**. **The cross-reference sweep did NOT convert any of them to reference-style links**, as the item instructs |
| 8 | **Verified-and-clean** | `grep -c 'Proposed improvements'` over the spec -> **0**; the six `##` headings are `Problem statement`, `Current state`, `The eight improvements`, `Non-goals`, `References`, `Implementation checklist`. `grep -rln 'spec-004-optimizer_beyond-0_0_3.md#' --include='*.md' .` -> **3 files, all this cycle's own** (the rationale and the two `bld-004-*` artifacts). No external consumer links a spec-004 heading anchor |
| 9 | **Verified-and-clean; left alone deliberately** | `#proposed-improvements` occurs **17 times** in `bld-004-r1-rationale_move.md` and **0 times** in the durable rationale. A closed per-cycle scratchpad, exempt from the symbol-path rule and regenerated next cycle. Not read as live rot |
| 10 | **Verified-and-clean; every reading re-run, none quoted** | 35/35 link targets and anchors (`### 2b.`); `import_spec_terms --check` green **and** re-run at this tree state; ten anchors single-carrier via `check_spec_glossary`; `db.sqlite3` attributed by `iterdump()` set-difference (`### Working-tree state`) |
| 11 | **Verified, and CHANGED** — the list is now **13** entries, not 14 | `docs/builder/bld-003-final.md` has been **restored to disk** by something outside this cycle and is byte-identical to HEAD. See `### Working-tree state` |
| 12 | **Verified-and-clean** | The rationale's `## How to read this file` bullet defines **both** block kinds, names which section carries which, points at the `**On the label.**` preamble, and forbids levelling either spelling to the other. Line-initial counts unchanged: **10** modal / **12** factual |
| 13 | **Verified-and-clean; the two provenance holes are still deliberate and still true** | `grep -rn '_assert_under_construction' docs/SPECS/` hits **spec-004 and its own rationale only** — no sibling spec has claimed the plan-immutability enforcement since R2 closed |
| 14 | **Verified-and-clean** | `HEAD` is `ff03c1372365edcad488ff4671389d88ae145276`, unchanged across R2's final verification and this pass. `git log -1` over the spec still returns `20a9752f` |
| 15 | **Verified-and-clean (CLOSED)** | The build plan's `**Re-measured 2026-08-08 after R2's pass-3 review**` paragraph carries the eight rows (D7, D9, D13, D15, D17, D20, D25, D26) plus "Do not read the numeral as settled". Nothing further owed |
| 16 | **Verified-and-clean (CLOSED); not re-opened** | Four independent passes reached the same disposition on the `### B1` `**Directive-variable extraction.**` DRY residue. **This pass produced no new evidence and did not re-open it**, which is what the item asks |
| 17 | **Verified-and-clean; this pass adds no correctness finding** | Everything read at source this pass — `check_schema`'s `@staticmethod`, `OptimizerHint.strategy` / `nested_strategy` and its `__post_init__` rejections, `_record_relation_access`'s call sites, `_build_cache_key`'s five components — behaves as the reconciled spec states. **No defect in shipped optimizer code**, so nothing is escalated under `## Build-wide context flags`' read-only-audit rule. The two findings above are **documentation** defects, not code defects |
| 18 | **Verified-and-clean; the hazard reproduced and was handled** | My parser keeps `_` when slugging and resolves `../GLOSSARY.md#metaoptimizer_hints`. A slugger that strips `_` would have reported a real, four-passes-verified anchor as broken. The rule held: suspect the checker first |

**Item 4 is wider than recorded, in a second and distinct way.** Beyond the "locked" phrasing, `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` `:331` states *"`pyproject.toml` pins `>=0.262.0`; `uv.lock` resolves `0.316.0`"*. Measured at HEAD: `pyproject.toml:36` reads **`"strawberry-graphql>=0.316.0"`**, and the shared `.venv` resolves **`0.323.2`** (`uv pip list`, read rather than remembered per `BUILD.md` `## Floor verification`). So both halves of that parenthetical are now false, and `0.316.0` is the **declared floor**, not a lock — which is the same defect the item already names, one layer deeper. `spec-029` is a read-only sibling with no declared exception in this cycle (`## Build-wide context flags`), so this is **recorded, not fixed**, and it strengthens the item's ask that whoever tightens the phrasing decide for every site at once. **Do not let a future pass fix the `>=0.262.0` figure alone and consider item 4 closed** — the two are one edit.

### Working-tree state — re-derived, reported, not reverted

`git status --short` -> **13 entries**, one fewer than R2's fourteen:

```
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
 M docs/SPECS/spec-005-django_type_contract-0_0_3.md
 D docs/builder/bld-003-r1-rationale_move.md
 D docs/builder/bld-003-r2-spec_reconciliation.md
 D docs/builder/bld-003-r3-doc_completion_archive.md
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/bld-004-r2-spec_reconciliation.md
?? docs/builder/bld-005-r1-rationale_move.md
?? docs/builder/bld-005-r2-spec_reconciliation.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
?? docs/builder/build-005-django_type_contract-0_0_3.md
```

**The change, and it revises the build plan's `### Fifth change`.** `docs/builder/bld-003-final.md` is **back on disk** — present, `32,693` bytes, mtime today 12:04 — and **byte-identical to HEAD** (`git diff --stat -- docs/builder/bld-003-final.md` -> empty, so it no longer appears in `git status` at all). **This pass did not restore it**; `docs/builder/bld-003-*` is in no writable set here, and restoring it would need the `git checkout` `AGENTS.md` rule 34 bans while concurrent sessions are writing. The likeliest actor is the concurrent card-005 cycle, whose own R3 dispatch would cite it as the catalog shape. **The other three `bld-003-*.md` deletions persist and were not restored** — still the maintainer's call per `### Fifth change`. Worker 0 should amend that section to read *three* deletions, not four.

**`examples/fakeshop/db.sqlite3` is clean, and that is proven semantically rather than assumed from `git status`.** The HEAD blob was extracted read-only with `git show HEAD:examples/fakeshop/db.sqlite3` into a scratch path **outside the repository**, then compared two ways: `md5` **`649edeea56b8821dd1e80ec43bc330d1`** on both sides, and `sqlite3.iterdump()` **9,806 statements on each side, 0 added, 0 removed**. No concurrent kanban write is pending. `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md`, `django_strawberry_framework/`, `tests/`, `examples/`, `scripts/`, and `CHANGELOG.md` are all clean, and all four generated docs pass `--check` against that DB — which is the stronger evidence the plan asks for, since a clean `git diff` on a generated doc proves nothing about whether it matches its source.

**This is the state Worker 2 must diff against**, plus one entry this pass itself adds: `?? docs/builder/bld-004-r3-doc_completion_archive.md`, making **14** by the time Worker 2 is dispatched. After Worker 2's pass the list should gain exactly `docs/GLOSSARY.md` and `examples/fakeshop/db.sqlite3` and nothing else — **16** entries. Anything further is a concurrent session's and is reported, never reverted.

### Validation run — every command run in this pass, output pasted, nothing quoted

- `git rev-parse HEAD` -> `ff03c1372365edcad488ff4671389d88ae145276`.
- `git log -1 --format='%h %s' -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> `20a9752f docs(spec-003): reconcile the O4 spec with HEAD and extract its rationale`.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **`OK: 10 terms - all have glossary entries and at least one spec link.`** exit 0.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` -> exit 0, both.
- `uv run python scripts/check_trailing_commas.py --check docs/builder/bld-004-r3-doc_completion_archive.md` -> exit 0, re-run **after** the last edit to this file.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> **`OK: 49 done cards have glossary links.`** exit 0. **Read-only `--check` form only.**
- `uv run python scripts/build_glossary_md.py --check` -> `docs/GLOSSARY.md is up to date.` exit 0.
- `uv run python scripts/build_kanban_md.py --check` -> `KANBAN.md is up to date.` exit 0.
- `uv run python scripts/build_kanban_html.py --check` -> `KANBAN.html is up to date.` exit 0.
- `uv run python scripts/build_tree_md.py --check` -> `docs/TREE.md is up to date.` exit 0.
- `grep -rEn 'TODO\(spec-004|TODO-(ALPHA|BETA|STABLE)-004' .` -> 3 hits, all attributed in `### 4.`; the same sweep excluding `docs/builder/` -> **no match**.
- `grep -rn 'docs/spec-004' .` -> **no match** (no reference to the pre-archive path).
- **`AGENTS.md` rule 27:** `grep -nE '[a-zA-Z_/]+\.(py|md):[0-9]+'` -> **no match** in the spec and **no match** in the rationale.
- **Zero fenced code blocks:** `grep -c '^```'` -> **0** in the spec, **0** in the rationale.
- **Counts, all re-derived after the last edit.** Spec **236 lines / 36,223 bytes**; rationale **1,309 / 94,318**; spec link defs **11/11 used**; rationale **24/24**; **35/35** targets and anchors resolve; terms CSV **10 data rows / 10 distinct anchors**; card 4 glossary links **10**; `B1`–`B8` source markers **21 across 4 files**; working tree **13 entries**; `db.sqlite3` iterdump **9,806 = 9,806**.
- No `pytest` (`AGENTS.md` rule 15; this cycle changes no code, and the full sweep is the final gate's). No `ruff` (this pass wrote no Python). **No `--cov*` flag in any command.** No `git stash` / `checkout` / `restore` / `worktree`. No branch created or switched. Nothing committed.

### Notes for Worker 1 (spec reconciliation)

**Every item R3 defers, with its reason and where it is recorded**, so the final gate can key its `### Deferred work catalog` by item rather than by artifact. The shape follows `git show HEAD:docs/builder/bld-003-final.md`'s catalog. **Nothing here is stranded**: `BUILD.md` `## Final test-run gate` makes the catalog's author walk every artifact's `Notes for Worker 1` **and** `What looks solid`, and this section is the former.

**Carried forward from R2's handoff (each re-derived live this pass; see `### 5.` for the evidence):**

1. **`check_optimizer` management command + custom-resolver detection** — named as B6 follow-up work at `0.0.3`, never built, **no card names either**. Dropped from the spec by R2 and recorded in the rationale. `inspect_django_type` (`spec-029`) answers a different question and is explicitly not a substitute. *Source: R2 handoff item 2.*
2. **The `_record_relation_access`-before-elision ordering invariant has no automated guard** in `walker.py::_plan_select_relation`. Adding one is a source change; a documentation cycle cannot. The spec points at `spec-003` for the rule and its cost. *Source: R2 handoff item 3; originally the spec-003 cycle's audit.*
3. **`spec-029`'s "locked `0.316.0`" phrasing — and its `pyproject.toml` figure.** `0.316.0` is the **declared floor** (`pyproject.toml:36` `strawberry-graphql>=0.316.0`), not a lock, and `.venv` resolves `0.323.2`. Live at **10 occurrences across 8 lines**. **Widened this pass:** `spec-029:331`'s parenthetical *"`pyproject.toml` pins `>=0.262.0`; `uv.lock` resolves `0.316.0`"* is false in **both** halves. Read-only sibling, no declared exception. **Whoever fixes it must decide for all sites at once — fixing the `>=0.262.0` figure alone does not close this.** *Source: R1 handoff item 17 -> R2 handoff item 4, widened in `### 5.`*
4. **The `spec-003` pair's wrong `spec-035` plan-immutability attribution — seven sites, enumerated and re-derived.** `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` #"finalized at handoff" plus six body citations in its companion (`:253`, `:521`, `:598`, `:604`, `:855`, `:952`; only `:521`'s projection-gate item is sound). Both read-only here. The enumeration lives in the **durable** rationale, not only in an artifact. *Source: R2 handoff item 5.*
5. **Three B7 test names still spell the retired `_optimizer_field_map`** (`tests/optimizer/test_field_meta.py` `::test_optimizer_field_map_populated`, `::test_optimizer_field_map_contains_relations`, `::test_optimizer_field_map_respects_fields_filter`). Live code, already carded on `TODO-ALPHA-052-0.1.0`. *Source: R2 handoff item 6.*
6. **`## Non-goals` claims Layer-3 features "have their own specs" while aggregates has none.** Filters / orders / permissions have specs; aggregates does not, and `START.md` records it as an unwritten beta-line item. The normative half — *this spec does not cover them* — is true, and R2 declined to land an unreviewed contract edit after a byte-stable round. It **discharges itself** when the aggregates spec lands. *Source: R2's `### The two residues Worker 3 recorded rather than filed`, item 1.*

**New, raised by R3's own audit:**

7. **`KANBAN.md` card 4's B1 `Scope` row names four cache-key components; five ship.** The resolver's origin Strawberry type is missing; it arrived with `spec-018`, three releases after this card. A `Scope` row is a Done card's record of declared scope, not a live contract, and the spec plus the `Plan cache` glossary entry both carry all five correctly. **Deferred rather than fixed**: rewriting board history to match a later spec is not what a card records, and the reader who needs the current key has two correct sources. Whoever disagrees should note the fix is a `CardItem.text` DB edit plus a `build_kanban_md.py` / `build_kanban_html.py` regenerate. *Source: `### 1.`, `KANBAN.md` audit.*
8. **`docs/README.md`'s `## Today and coming next` `OptimizerHint` bullet omits `strategy`.** Unlike F2 it asserts no completeness and the same file documents `strategy` in full at `:177`. **Recommended, non-blocking, explicitly deferrable** — a one-token addition to a hand-authored durable doc that would make the two durable docs read alike. If Worker 0 folds it into Worker 2's dispatch it is a `docs/README.md` edit, not a DB edit; if not, the catalog carries it. *Source: `### 1.`, `docs/README.md` audit.*
9. **If Worker 0 rules F2 outside R3's charter, it defers here** with the same owner as item 8 — the nested-connection strategy documentation surface. **F1 does not defer**: it is a false statement about a B6 contract in the durable doc R3 is chartered to audit, and it is the only durable carrier left of a claim R2 already corrected in the spec.

**Two corrections to prior cycle files, stated here rather than by editing them.** Both are Worker 0's files or a closed scratchpad; neither changes a conclusion.

- **The build plan's `### Fifth change` should read three deleted `bld-003-*.md` artifacts, not four.** `docs/builder/bld-003-final.md` is restored and byte-identical to HEAD; the other three deletions persist. *Evidence in `### Working-tree state`.*
- **The build plan's `## Worker-0-verified facts` says "the five B-owned entries" and then names six; the measured figure is seven** (the six named plus `OptimizerHint`). The conclusion — every B-owned entry is `shipped (0.0.3)`, no status flip owed — is unaffected. *Evidence in `### 3.`*

**One standing lesson worth carrying past this cycle.** The plan recorded the durable docs as "already correct — verify, do not assume", and the phrase earned its keep: three of the four were clean, and the fourth carried a wrong method kind that had survived from spec-004's original pseudo-code through eleven releases, three prior residual cycles, and R2's own H3 correction of the *same* claim in the *same* words one document over. **A defect corrected in a spec is not corrected in the docs that copied the spec**, and the only thing that finds the copy is reading the durable doc against source rather than against the spec.

---

## Build report (Worker 2)

Two false statements in `docs/GLOSSARY.md` corrected at their DB source and the doc regenerated. No code, no test, no spec, no sibling, no `KANBAN.*`, no `docs/README.md`, no terms CSV, no `docs/TREE.md`. Every number below was produced by running the command in this pass and pasting its output; nothing is quoted from the Plan or from the build plan.

### Files touched

Grounded in `git status --short`, run after the last edit of this pass.

- `examples/fakeshop/db.sqlite3` — two `GlossaryTerm.body` values rewritten through the Django ORM (`manage.py shell`), never raw SQL. `GlossaryTerm(anchor='djangooptimizerextension')` (F1) and `GlossaryTerm(anchor='optimizerhint')` (F2). No other row, table, app, or card touched — proved by `iterdump()` set-difference below, not by inspection.
- `docs/GLOSSARY.md` — **regenerated output only**, `uv run python scripts/build_glossary_md.py`. Not hand-edited at any point.
- `docs/builder/bld-004-r3-doc_completion_archive.md` — this build report appended, `Status:` set to `built`, and the seven `### Dispatched findings checklist` **Required changes (Worker 2)** boxes ticked. The nine `**(W1, done)**` audit boxes were neither re-run nor re-ticked, per the Plan. No prior section edited.

`docs/builder/worker-memory/worker-2.md` was also appended to; it is gitignored and so does not appear in `git status`.

**F1, as landed.** `GlossaryTerm(anchor='djangooptimizerextension').body`, line 30 of 32 — the entry's last prose line, two lines above `**See also:**`:

```
- ... Classmethod [`check_schema`](#schema-audit) audits schema-reachable `DjangoType`s.
+ ... Static method [`check_schema`](#schema-audit) audits schema-reachable `DjangoType`s.
```

The pre-edit occurrence count was asserted **in the edit script itself, before the write**: `t.body.count('Classmethod')` -> `1`, matching the Plan. The script also asserted the whole carrier sentence was present verbatim before replacing it, and asserted `count('Classmethod') == 0` / `count('Static method [\`check_schema\`]') == 1` after. A failed assertion would have aborted before `t.save()`. Line count unchanged at 32; the `#schema-audit` link target untouched.

**F2, as landed.** `GlossaryTerm(anchor='optimizerhint').body`, 21 lines -> 23. Two edits, both asserted-before-write the same way.

A fifth `Supported modes:` bullet after the `prefetch(Prefetch(...))` bullet:

```
+ - `OptimizerHint.strategy(...)` — select the nested-connection fetch backend for one Relay
+   connection field; the backends and their selection rules are documented under
+   "Nested connection indexing" in `docs/README.md`.
```

(one physical line in the body; wrapped here for reading). It names the member and points at the section that owns it. It states **no** backend name, **no** selection rule, **no** precedence rule, and **no** extension-wide default — the DRY constraint the Plan's `### DRY analysis` sets, so `docs/README.md` stays the single home for that contract.

And, in the `Validation:` paragraph, `strategy(...)` added to the factory parenthesis with the walker-dispatch clause re-anchored:

```
- `prefetch(Prefetch(...))`) are the documented consumer API; direct
- construction is supported but the same four shapes are the only ones the
- walker dispatches, and any other combination — ...
+ `prefetch(Prefetch(...))`, `strategy(...)`) are the documented consumer API;
+ direct construction is supported but the first four shapes are the only ones
+ the walker dispatches, and any other combination — ...
```

**The trap was handled as the Plan requires: the walker-dispatch claim survives as a true claim.** "the same four shapes" was re-anchored to "the first four shapes", so "four" now refers to the four bullets ahead of `strategy(...)` rather than to a factory list that no longer has four members. It was **not** collapsed into "five shapes the walker dispatches", which would have traded a true statement for a false one. Verified at source rather than accepted from the Plan — see `### Validation run`.

### Tests added or updated

None; this cycle changes no code and the correction is DB content, not behavior.

### Validation run

No `ruff format` and no `ruff check --fix` are owed or were run: this pass wrote no `.py` file (the two ORM edit scripts live in this session's scratchpad **outside the repository** and are not part of the tree). No `pytest` (`AGENTS.md` rule 15; the full sweep is the final gate's). **No `--cov*` flag in any command.** No `git stash` / `checkout` / `restore` / `worktree`. No branch created or switched. Nothing committed.

**Source verification behind both findings — re-derived at HEAD `ff03c1372365edcad488ff4671389d88ae145276`, not taken from the Plan.**

- F1: `grep -n -B2 "def check_schema" django_strawberry_framework/optimizer/extension.py` -> `1247-    @staticmethod` / `1248:    def check_schema(schema: Any) -> list[str]:`. A static method, so `Classmethod` was false.
- F2, the false half: `django_strawberry_framework/optimizer/hints.py::OptimizerHint.strategy` at `:174`, returning `cls(nested_strategy=name)` at `:185`; the `nested_strategy` field at `:105`. A fifth factory ships. `docs/README.md` `## Nested connection indexing` documents it with a worked `Meta.optimizer_hints` example and states its precedence over the extension-wide default, so it is documented consumer API.
- F2, the TRUE half that had to survive: `grep -rn "nested_strategy" django_strawberry_framework/` -> hits in **`optimizer/extension.py` (3), `optimizer/hints.py` (7), `optimizer/nested_fetch.py` (1), `optimizer/nested_planner.py` (4)** and **zero in `optimizer/walker.py`**. Independently, `optimizer/walker.py::_apply_hint` dispatches exactly four shapes and no more — `hint_is_skip(hint)` (`:957`), `hint.prefetch_obj is not None` (`:959`), `hint.force_select` (`:1027`), `hint.force_prefetch` (`:1049`). So "the ... four shapes are the only ones the walker dispatches" is accurate and was preserved.

**Baseline taken BEFORE any DB edit**, so a file-only staged difference could be told from real DB drift. The Plan's figures were re-derived rather than trusted, and both reproduced exactly:

- `git rev-parse HEAD` -> `ff03c1372365edcad488ff4671389d88ae145276` (`ff03c137`, unchanged from the Plan).
- `uv run python scripts/build_glossary_md.py --check` -> `docs/GLOSSARY.md is up to date.` exit 0. So the file matched the DB before this pass, and every byte of the diff below is this pass's.
- `git status --short` -> **14** entries, exactly the Plan's 13 plus `?? docs/builder/bld-004-r3-doc_completion_archive.md`.
- `examples/fakeshop/db.sqlite3` vs a read-only `git show HEAD:examples/fakeshop/db.sqlite3` copy taken into a scratch path **outside the repository**, compared by `sqlite3.iterdump()` semantics and never by file bytes: **9,806 statements each side, 0 added, 0 removed.** No concurrent write was pending when this pass began.

**After the DB edits.**

- `uv run python scripts/build_glossary_md.py` -> `Wrote 142 terms, 146 category memberships, 1042 spec mentions across 49 specs to docs/GLOSSARY.md`, exit 0.
- **Two-consecutive-regenerate byte stability**, the check the Plan and `BUILD.md` `### Tracked binary / generated files` require in place of "`git diff` is clean": ran `build_glossary_md.py` a second time and compared `md5` of the output. Run 1 `e62be86ba4c853cd61a95e97055d9f51`; run 2 `e62be86ba4c853cd61a95e97055d9f51`; `cmp` exit 0. **Byte-stable.**
- All four generated-doc freshness checks, all exit 0: `build_glossary_md.py --check` -> `docs/GLOSSARY.md is up to date.`; `build_kanban_md.py --check` -> `KANBAN.md is up to date.`; `build_kanban_html.py --check` -> `KANBAN.html is up to date.`; `build_tree_md.py --check` -> `docs/TREE.md is up to date.`
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> **`OK: 49 done cards have glossary links.`** exit 0, re-run **after** the DB write. **Read-only `--check` form only; the writing sync form was never invoked in this pass.**
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **`OK: 10 terms - all have glossary entries and at least one spec link.`** exit 0. Both edited anchors (`djangooptimizerextension`, `optimizerhint`) are among spec-004's ten single-carrier anchors; neither edit renamed an anchor or a heading, and this run proves it rather than assuming it.
- `uv run python examples/fakeshop/manage.py check` -> `System check identified no issues (0 silenced).` exit 0.
- `uv run python scripts/check_trailing_commas.py --check docs/GLOSSARY.md docs/builder/bld-004-r3-doc_completion_archive.md` -> exit 0, both. Re-run after the last edit to this artifact.

**`git diff docs/GLOSSARY.md` shows exactly the two corrections and nothing else** — `1 file changed, 8 insertions(+), 6 deletions(-)` across two hunks, `@@ -742,7 +742,7 @@` (F1, one line) and `@@ -1399,16 +1399,18 @@` (F2, the bullet plus the re-wrapped `Validation:` paragraph). No third hunk, no unrelated term, no status-line change, no ordering change.

**The DB write is attributed semantically, not from `git status`.** `iterdump()` against the same read-only HEAD copy, re-run after the edits: **9,806 statements each side** (unchanged, since both edits are updates rather than inserts), set-difference **2 added / 2 removed, all four in `glossary_glossaryterm` and nowhere else.** Zero statements in the delta touch any `kanban_*` table, which is the independent reason `KANBAN.md` and `KANBAN.html` stayed `--check`-clean and absent from `git status`.

**`git status --short` after the pass — 16 entries, exactly the Plan's predicted 14 + 2, with no third addition:**

```
 M docs/GLOSSARY.md
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
 M docs/SPECS/spec-005-django_type_contract-0_0_3.md
 D docs/builder/bld-003-r1-rationale_move.md
 D docs/builder/bld-003-r2-spec_reconciliation.md
 D docs/builder/bld-003-r3-doc_completion_archive.md
 M examples/fakeshop/db.sqlite3
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/bld-004-r2-spec_reconciliation.md
?? docs/builder/bld-004-r3-doc_completion_archive.md
?? docs/builder/bld-005-r1-rationale_move.md
?? docs/builder/bld-005-r2-spec_reconciliation.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
?? docs/builder/build-005-django_type_contract-0_0_3.md
```

Every one of the two additions (`docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3`) is slice-intended and appears in `### Files touched`. **Nothing else moved, so there is no stop-and-report and nothing was reverted.** The three `bld-003-*.md` deletions persist untouched and were **not** restored — still the maintainer's call. `bld-003-final.md` remains on disk and byte-identical to HEAD, as the Plan's `### Working-tree state` records. `docs/SPECS/spec-005-*` and the `bld-005-*` / `build-005-*` files are the concurrent card-005 cycle's; none was read for content, edited, or reverted.

### Failability proofs

None; this pass introduced no new boundary.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope none.

### Implementation notes

- **`Static method` over `A static method`.** The Plan left this to discretion. `Static method` is the minimal token swap: the sentence's rhythm, length, and the following `[`check_schema`](#schema-audit)` link are all unchanged, so the F1 diff is one word wide and a reviewer can grade it without re-reading the paragraph.
- **`the first four shapes` over the Plan's suggested `the four cardinality shapes above`.** Both re-anchor "four" to the walker-dispatched set, which is what the Plan requires; `cardinality shapes` is the less accurate of the two, because only `select_related()` and `prefetch_related()` are cardinality overrides — `SKIP` is an exclusion and `prefetch(Prefetch(...))` supplies an object. `the first four` is exact against the bullet order immediately above and against the factory parenthesis in the same sentence, and it needs no new vocabulary. The Plan's text was offered as `e.g.`, and wording inside the fixed content was explicitly discretionary.
- **One `manage.py shell` invocation per logical edit, three in total** (F1 + F2's two edits in one script; then one refinement script for the clause wording above; then read-back). The Plan left the batching to discretion. Every script asserted its target substring was present **exactly once before writing** and asserted the post-condition after, so a drifted body would have aborted before `t.save()` rather than producing a partial or over-reaching write. That is the same discipline `BUILD.md`'s failability loop applies to its anchor check, borrowed here because a `str.replace` on a concurrently-writable row is the same hazard shape.
- **The ORM path was used as the Plan directs, and the `post_save` side-row it cites is the kanban app's, not the glossary's.** Recorded because a later pass should not infer a glossary side row that does not exist: `grep -rn "post_save" examples/fakeshop --include="*.py"` puts every receiver in `examples/fakeshop/apps/kanban/signals.py`, and the glossary app registers none. The `iterdump()` delta confirms it — 2 added / 2 removed, all in `glossary_glossaryterm`, no side table moved. The ORM was still the right instrument (it is what the Plan and `BUILD.md` prescribe, and it is what keeps a future glossary receiver from being bypassed); this note only prevents a false expectation of a third changed row.
- **The fifth bullet points at `docs/README.md` rather than at the sibling glossary entry, deliberately.** `docs/GLOSSARY.md` `## Connection-aware optimizer planning` also describes the three backends, and an in-page `[...](#connection-aware-optimizer-planning)` link would have been the more house-typical form. It was not used, for two reasons: the Plan names `docs/README.md` `## Nested connection indexing` as the owning section, and that sibling entry's own strategy sentence is itself stale (see `### Notes for Worker 1`), so pointing a correction at it would route the reader to a second incomplete statement. Naming `docs/README.md` in prose is house-consistent — `docs/GLOSSARY.md` already does it in the `DjangoASGIRouter`, version-quintet, and request-body-cap entries.

### Notes for Worker 3

- **The one place this pass went past the Plan's letter, flagged so it is reviewed and not skimmed.** The Plan's F2 step 2 names two edits: add `strategy(...)` to the factory parenthesis, and re-anchor the walker-dispatch clause. This pass made a **third, one-clause** change in the same sentence: the `any other combination — …` rejection enumeration gained `` or `nested_strategy=` set with `skip=True`, `prefetch_obj=`, or `force_select=True` ``. The reason is that the enumeration is the *same* exhaustive-list defect F2 exists to close, one clause further on: adding a fifth factory adds a fifth flag, so leaving the rejection list at four would have closed the defect in one sentence and re-opened a smaller copy of it in the next. It imports no backend name, no selection rule, and no precedence rule, so it stays inside the Plan's DRY constraint. Graded against `worker-2.md` `## Plan-vs-implementation drift` it is small, mechanically obvious, and evaluable from the diff alone — but it is the item to check first.
  - **Verify it at source, not against this report.** `django_strawberry_framework/optimizer/hints.py::OptimizerHint.__post_init__` `:155`-`:164`: `if self.nested_strategy is not None:` rejects `self.skip or self.prefetch_obj is not None or self.force_select`. **`force_prefetch` is deliberately NOT in that list** — the code comment at `:156`-`:158` says it is "redundant-but-harmless and stays allowed" — which is why the new clause names three flags and not four. Getting that wrong in the other direction (writing "any of the four") would have been a fresh false statement.
- **The `Supported modes:` bullet is one physical line** in `GlossaryTerm.body`, matching bullets 5-8, while the `Validation:` paragraph is hard-wrapped at ~76 columns, matching its existing shape. That is why the F2 hunk shows more moved lines than changed words: the paragraph re-wrapped when `strategy(...)` was inserted. Reading the rendered `docs/GLOSSARY.md` `## OptimizerHint` entry rather than the raw hunk is the faster check of what actually changed.
- **No `scripts/review_inspect.py` run and no shadow file used** — this pass wrote no Python and read source only through `grep` and `Read`, both cited inline in `### Validation run`.
- **The DB is concurrently writable and was clean at this pass's start** (`iterdump()` 9,806 = 9,806, 0/0 against HEAD). If it is dirty by the time this review runs, the delta is a concurrent session's: this pass's own contribution is exactly 2 `glossary_glossaryterm` rows, and it is separable by set-difference. Do not `git checkout` the DB or `docs/GLOSSARY.md` under any finding.

### Notes for Worker 1 (spec reconciliation)

**No spec amendment is owed by this pass**, and none is proposed. The reconciled spec already carries both corrected contracts: `### B6` `**Public API.**` reads "is a static method", and `### B4` already lists `OptimizerHint.strategy(...)` as a fifth member with a pointer to the section that owns the backends. This pass brought the durable doc *to* the spec; it found nothing in the spec to change.

Three items for the final gate's `### Deferred work catalog`. None is this pass's to fix — the first two are outside the writable set, the third is a Plan-letter deviation already recorded above and is raised here only because `### Notes for Worker 1` is the louder of the two channels.

1. **NEW — `docs/GLOSSARY.md` `## Connection-aware optimizer planning` now carries the same incompleteness F2 just closed, one entry over.** Its third paragraph opens *"The nested fetch strategy is fixed per `DjangoOptimizerExtension` instance: `"windowed"` is the default, `"lateral"` … and `"auto"` …"*. **"fixed per instance" is no longer true**: `docs/README.md` `## Nested connection indexing` states that `OptimizerHint.strategy(...)` "overrides the nested-connection fetch backend for **one** Relay connection field, taking precedence over the extension-wide default", and `optimizer/hints.py::OptimizerHint.strategy` ships it. So the extension-wide setting is the **default**, not a fixed value. This was found while siting F2's pointer and is **not** in this item's writable set — the dispatch scopes Worker 2 to F1 and F2, and the entry is not one of card 4's ten anchors. Recommended fix, when someone is chartered for it: a `GlossaryTerm(anchor='connection-aware-optimizer-planning')` ORM edit changing "is fixed per `DjangoOptimizerExtension` instance" to "defaults per `DjangoOptimizerExtension` instance, overridable per connection field by [`OptimizerHint`](#optimizerhint)`.strategy(...)`", plus a regenerate. **It is the same defect class as F1 and F2 and the same class R3's standing lesson names** — a claim that was true when written and was never re-taken after a later slice extended the surface.
2. **CARRIED, unfixed — `docs/README.md`'s `## Today and coming next` `OptimizerHint` bullet still omits `strategy`** (the Plan's `### Notes for Worker 1` item 8). **Worker 0 did not fold it into this dispatch**: `docs/README.md` is on this pass's explicit do-not-touch list, so the item defers exactly as the Plan's item 8 anticipated. Noted here so the catalog does not have to re-derive whether it was silently picked up — it was not. It remains non-blocking (that bullet asserts no completeness, and the same file documents `strategy` in full 55 lines later), and it is now the **only** durable-doc surface left where `strategy` is absent from an `OptimizerHint` member list.
3. **Plan-letter deviation, for the audit trail.** The one-clause extension of F2's rejection enumeration, detailed in `### Notes for Worker 3`. Recorded under both headings because `worker-2.md` `## Plan-vs-implementation drift` routes small mechanically-obvious drift to this section as the louder signal: Worker 1 may keep it as landed or ask for it to be reverted to the Plan's exact two-edit scope, and either outcome is a two-line ORM edit plus a regenerate. It changes no contract the spec states.

**One observation on the Plan's own numbers, all of which reproduced.** Every figure this pass re-derived matched the Plan exactly: `Classmethod` count 1, `HEAD` `ff03c137`, the 13-entry working tree, `iterdump()` 9,806 = 9,806 with 0 added / 0 removed, `import_spec_terms --check` at 49 cards, `check_spec_glossary` at 10 terms, and the predicted post-pass total of 16 `git status` entries. Nothing in the Plan needed correcting, which is worth stating explicitly: the Plan's `### 3.` already corrected two of Worker 0's counts, so a silent re-derivation here would have left a reader unsure whether the third pass agreed.

---

## Review (Worker 3)

Every figure below was produced by running the command in this pass and reading its output. Nothing is quoted from the Plan or from the Build report; where a number matches theirs it is because it re-derived, and where I checked a claim at source I read the source rather than the report's account of it. `HEAD` re-derived: `git rev-parse HEAD` -> `ff03c1372365edcad488ff4671389d88ae145276`. `git log -1 --format='%h %s' -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> `20a9752f docs(spec-003): reconcile the O4 spec with HEAD and extract its rationale` — unchanged, so nothing of this cycle has been swept into a commit. No `git stash` / `checkout` / `restore` / `worktree`, no branch created or switched, nothing committed, no `--cov*` flag, no `pytest`.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **The pass added a pointer, not a fourth copy — which is the right shape, and it is why the one real duplication is a deferral rather than a finding.** The nested-connection strategy contract now has three durable carriers: `docs/README.md` `## Nested connection indexing` (`:175`-`:189`, authoritative — states the member, the backends, and precedence over the extension-wide default, with a worked `Meta.optimizer_hints` example), `docs/GLOSSARY.md` `## Connection-aware optimizer planning` (`:382`, a **second full description** of the three backends), and now `docs/GLOSSARY.md` `## OptimizerHint` (`:1402`, a one-line pointer that names the member and states no backend, no selection rule, no precedence rule). Read the new bullet against the Plan's `### DRY analysis` constraint and it holds exactly: it imports nothing from `docs/README.md`. **The drift the constraint exists to prevent already happened in the second carrier** — `## Connection-aware optimizer planning`'s third paragraph opens "The nested fetch strategy is fixed per `DjangoOptimizerExtension` instance", which `OptimizerHint.strategy(...)` falsifies. Verified live at `docs/GLOSSARY.md:390` this pass. That entry is not one of card 4's ten anchors and is outside this item's writable set, so it is carried in `### Notes for Worker 1` item 1, not filed here.
- **The choice to point at `docs/README.md` rather than at the in-page `#connection-aware-optimizer-planning` sibling is right, and the report's stated reason survives checking.** An in-page anchor is the more house-typical form, but it would have routed a reader correcting one incomplete statement into a second one. Naming `docs/README.md` in prose is house-consistent: `docs/GLOSSARY.md` already does it at `:610` (`DjangoASGIRouter` migration note), `:1059` (the version quintet), and `:1678` (the request-body cap). Three precedents, re-derived by `grep -n 'docs/README\.md' docs/GLOSSARY.md`.
- No repeated literal, no near-copy, no new helper, no new indirection. The diff adds no function, class, constant, or branch anywhere. **No existence challenge is raised**: this pass creates no abstraction to challenge.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list are unchanged; no public export was added, removed, or renamed. Consistent with the cycle-wide flag that this cycle changes no code.

Confirmed independently that **no package source, test, or example source file changed**: `git status --short -- django_strawberry_framework/ tests/ examples/fakeshop/apps/ examples/fakeshop/test_query/ examples/fakeshop/tests/ scripts/` -> **empty**.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

**Applies** — the diff is a generated durable doc plus its DB source. Both changed entries were read end to end in the rendered file.

- **The change genuinely came from the DB, proven three ways rather than assumed.** (a) `scripts/build_glossary_md.py --check` -> `docs/GLOSSARY.md is up to date.` exit 0, so the file matches what the DB renders. (b) **Two-consecutive-regenerate byte stability:** `md5` of `docs/GLOSSARY.md` before any run `e62be86ba4c853cd61a95e97055d9f51`; after a first `build_glossary_md.py` run, identical; after a second, identical. `git diff --stat` unchanged at `8 insertions(+), 6 deletions(-)` after both runs. A hand-edit would have been reverted by the first regenerate. (c) I diffed the two `GlossaryTerm.body` values **at the DB row level** (read-only, `mode=ro`) against a `git show HEAD:` copy, and the body-level unified diff is **character-for-character the same two corrections** the rendered file shows. The only other column that moved on either row is `updated_date`; `title`, `anchor`, `status_text`, `entry_order`, `index_order`, and `status_id` are all unchanged, which is why no status line, ordering, or index row moved.
- **DB attribution is semantic, not by file bytes.** `git show HEAD:examples/fakeshop/db.sqlite3` into a scratch path **outside the repository**, then `sqlite3.iterdump()` on both: **9,806 statements each side; multiset difference 2 added / 2 removed, all four `INSERT INTO "glossary_glossaryterm"`, rows `id=459` (`djangooptimizerextension`) and `id=487` (`optimizerhint`)**. **Zero statements in the delta touch any `kanban_*` table**, any other app's table, or any schema statement. That is the independent reason `KANBAN.md` and `KANBAN.html` stayed `--check`-clean and absent from `git status`, and it is re-derived here rather than accepted, since a card-005 cycle is running concurrently on this same DB. Worker 2's figures reproduced exactly.
- **All four generated-doc `--check` renders exit 0**: `build_glossary_md.py --check` -> `docs/GLOSSARY.md is up to date.`; `build_kanban_md.py --check` -> `KANBAN.md is up to date.`; `build_kanban_html.py --check` -> `KANBAN.html is up to date.`; `build_tree_md.py --check` -> `docs/TREE.md is up to date.`
- **The chain the edit could break is intact.** `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> **`OK: 49 done cards have glossary links.`** exit 0 — **read-only `--check` form only; the writing sync form was not invoked in this pass.** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **`OK: 10 terms - all have glossary entries and at least one spec link.`** exit 0. Both edited anchors are among spec-004's ten single-carrier anchors, so a renamed anchor or heading would have broken card 4's wrap chain here; neither edit renamed either. `uv run python examples/fakeshop/manage.py check` -> `System check identified no issues (0 silenced).` exit 0. `uv run python scripts/check_trailing_commas.py --check docs/GLOSSARY.md docs/builder/bld-004-r3-doc_completion_archive.md` -> exit 0, both, re-run after the last edit to this artifact.
- **Version strings and statuses.** Neither entry's `**Status:**` line moved: `DjangoOptimizerExtension` stays `shipped (0.0.2)`, `OptimizerHint` stays `shipped (0.0.3)`. Correct — `strategy(...)` arrived with the nested-connection work, and this glossary's house pattern already carries later-version refinements inside a `shipped (0.0.x)` entry (`only() projection` carries `0.0.10`/`0.0.11`; `Strictness mode` carries `0.0.9`). Adding a version marker to a mode bullet would have been the drift, not the fix.
- **Links introduced point at existing targets.** The new bullet introduces **no markdown link** — `docs/README.md` sits in a code span, matching the three precedents above — so there is no new link to rot. `## Nested connection indexing` exists at `docs/README.md:175`, so the prose pointer resolves. Every pre-existing in-page anchor in both edited entries still resolves: `#schema-audit` -> `:1797`, `#configurationerror` -> `:365`, `#metaoptimizer_hints` -> `:1281`, `#optimizerhint` -> `:1390`, `#djangooptimizerextension` -> `:712`.
- **No staging language introduced**, and none present: the diff adds no "planned", "coming soon", "Slice N", or `TODO(`. The script-rendered-doc docstring clause of this check does not bite — `docs/GLOSSARY.md` renders from the DB, not from module docstrings, and `docs/TREE.md` (which does) is untouched and `--check`-clean.
- **No KANBAN movement, no archival, no verbatim spec drop-in** in this diff, so those clauses are not engaged.

### What looks solid

**F1 — graded at source, not against the report. Correct.**

`django_strawberry_framework/optimizer/extension.py` `:1247`-`:1248` reads `@staticmethod` / `def check_schema(schema: Any) -> list[str]:` — no `cls`, no `self`. So `Classmethod` was false and `Static method` is true. The rendered line now reads "Constructor accepts a `strictness` argument — see [Strictness mode](#strictness-mode). Static method [`check_schema`](#schema-audit) audits schema-reachable `DjangoType`s." One token, the link target untouched, the body still 32 lines, the sentence's rhythm preserved. `Static method` over `A static method` was the discretionary call and it is the better one for exactly the reason recorded: the diff is one word wide and gradeable without re-reading the paragraph.

**F2 — both halves re-derived independently. Correct, and the trap was not walked into.**

- *The false half.* `optimizer/hints.py::OptimizerHint.strategy` is a `@classmethod` returning `cls(nested_strategy=name)`, with `nested_strategy: StrategySelection | None = None` as a declared dataclass field. A fifth factory ships. `docs/README.md` `:177` teaches it with a worked `Meta.optimizer_hints` example and states its precedence over the extension-wide default, so "documented consumer API" enumerating four was false. The fifth bullet closes it, names the member, and states **no** backend name, **no** selection rule, **no** precedence rule, and **no** extension-wide default — the DRY constraint held.
- *The true half that had to survive.* `grep -rn "nested_strategy" django_strawberry_framework/` -> `extension.py` 3, `hints.py` 7, `nested_fetch.py` 1, `nested_planner.py` 4, and **`grep -c "nested_strategy" django_strawberry_framework/optimizer/walker.py` -> `0`**. Independently, I read `walker.py::_apply_hint` in full: it dispatches `hint_is_skip(hint)`, `hint.prefetch_obj is not None`, `hint.force_select`, `hint.force_prefetch`, then `return False` for the empty no-op form. **Four shapes and no more.** So "the ... four shapes are the only ones the walker dispatches" is true and had to be preserved.
- *The re-anchoring is exact in both readings.* "the **first** four shapes" resolves against the factory parenthesis immediately preceding it (`SKIP`, `select_related()`, `prefetch_related()`, `prefetch(Prefetch(...))`, then `strategy(...)`) **and** against the bullet order immediately above, and both orderings give the same four. Those four map onto exactly the four flags `_apply_hint` branches on. `the first four` over the Plan's suggested `the four cardinality shapes above` is the better call and the recorded reason is right: `SKIP` is an exclusion and `prefetch(Prefetch(...))` supplies an object, so only two of the four are cardinality overrides — the Plan's phrasing would have introduced a new inaccuracy while fixing an old one. This is the finding most easily "fixed" into a new falsehood and it was not.

**The deviation from the Plan's letter — graded, and it was right.**

The Plan's step 2 names two edits; the pass made a third, one-clause edit extending the `any other combination — …` rejection enumeration with `` `nested_strategy=` set with `skip=True`, `prefetch_obj=`, or `force_select=True` ``. Verified at source: `optimizer/hints.py::OptimizerHint.__post_init__` guards `if self.nested_strategy is not None:` then rejects `if self.skip or self.prefetch_obj is not None or self.force_select:` — **three** operands, in that order, matching the clause token for token. `force_prefetch` is deliberately absent, and the guard's own comment says so in as many words ("``force_prefetch`` is redundant-but-harmless and stays allowed"), as does the raised message ("force_prefetch is redundant but allowed"). Writing "any of the four" would have been a fresh false statement; the pass wrote three.

Three reasons the deviation is right rather than tolerated. It is the **same defect one clause later** — a fifth factory adds a fifth flag, so closing an incomplete enumeration in one sentence while leaving an incomplete enumeration in the next is not a fix, and the reasoning generalizes rather than being a one-off convenience. It stays **inside** the Plan's binding constraint: no backend, no selection rule, no precedence rule crosses over from `docs/README.md`. And it was **flagged rather than hidden**, in both `### Notes for Worker 3` and `### Notes for Worker 1`, with the source citation a reviewer needs to check it — which is what `worker-2.md` `## Plan-vs-implementation drift` asks of small, mechanically-obvious drift. Had it been made silently, the missing `force_prefetch` would have read as an oversight rather than a decision.

**Failability proofs, hot-path, floor — the three declarations verified rather than accepted.**

`### Failability proofs` reads `None; this pass introduced no new boundary.` **True.** The diff contains zero lines of code: no guard, gate, cap, rejection path, coercion, or validation branch is added anywhere. The boundary vocabulary in the changed prose *describes* an existing `__post_init__` guard shipped long before this cycle; describing a boundary is not introducing one. So the re-run floor computes to an **empty re-run set, and legally so** — `worker-3.md`'s floor admits an empty set exactly when the diff introduces no boundary meeting it. There is nothing here I accepted on Worker 2's record instead of re-running; there was nothing to re-run. `### Hot-path budget` and `### Floor verification` correctly read not-applicable and match the Plan's declarations (`none` for both), so no number is owed.

**Working-tree state, re-derived.**

`git status --short` -> **16 entries**, exactly the two additions (`M docs/GLOSSARY.md`, `M examples/fakeshop/db.sqlite3`) against the Plan's 14. **No unexpected file, and none appeared during this review** — re-run at the end of the pass and still 16, with `docs/GLOSSARY.md` still at md5 `e62be86ba4c853cd61a95e97055d9f51`. `docs/SPECS/spec-005-django_type_contract-0_0_3.md` and the `bld-005-*` / `build-005-*` / `appx/spec-005-*` entries are the concurrent card-005 cycle's; none was read for content, edited, or reverted here.

**`docs/builder/bld-003-final.md` — confirmed restored, and the remaining three were left alone.** The file is on disk (32,693 bytes, mtime today 12:04), `git diff --stat -- docs/builder/bld-003-final.md` is empty, and it does not appear in `git status` at all — so it is byte-identical to `HEAD`, restored by something outside this cycle. `git status --short -- docs/builder/ | grep '^ D'` -> **three** deletions (`bld-003-r1-rationale_move.md`, `bld-003-r2-spec_reconciliation.md`, `bld-003-r3-doc_completion_archive.md`). **The build plan's `### Fifth change` should read three, not four.** I did **not** restore the remaining three, as instructed; they stay the maintainer's call.

**Worker 1's audit half — both reported divergences re-derived, and both are honest.**

1. **The staged-anchor sweep really is 3 hits, and really is zero outside `docs/builder/`.** `grep -rEn 'TODO\(spec-004|TODO-(ALPHA|BETA|STABLE)-004' .` -> `docs/builder/build-004-optimizer_beyond-0_0_3.md:29`, `:343`, and `docs/builder/bld-004-r2-spec_reconciliation.md:3889` — all three are this cycle's own scratchpads **quoting the grep pattern in prose describing the sweep**, not staged anchors. The same sweep with `--exclude-dir=docs/builder` returns **no match** (exit 1): no source, no test, no example, no standing doc, nothing in the spec or the rationale. Reporting the raw 3 and then attributing it, rather than reporting a filtered zero, is the right form — the plan's "zero hits anywhere" baseline was taken before the files that make it non-zero existed, so the divergence is not drift.
2. **"Five B-owned entries" naming six is wrong, and seven is the right figure.** Measured directly against the DB rather than by re-reading the rendered doc: `select title, anchor, status_text from glossary_glossaryterm where status_text like '%0.0.3%'` -> **exactly 7 rows** — `fk-id-elision`, `metaoptimizer_hints`, `optimizerhint`, `plan-cache`, `queryset-diffing`, `schema-audit`, `strictness-mode`, every one `shipped (0.0.3)`. The build plan's `:158` says "five" and then lists six; the omitted seventh is `OptimizerHint`, which is precisely the entry F2 corrects. The conclusion the sentence carries — every B-owned entry is `shipped (0.0.3)`, no status flip owed — is unaffected. Both divergences were surfaced rather than smoothed, which is the behaviour the artifact contract wants.

**Two residues I examined and deliberately did not file**, recorded here with the standard I judged them against — no wrong action is available to a reader who follows the sentence's own imperative, and nothing durable depends on either.

- *"`skip=True` with any of the three other flags"* survives unchanged in the edited sentence, and `OptimizerHint` now has four fields other than `skip`. On the pass's own stated standard ("a fifth factory adds a fifth flag") this reads at first like a smaller copy of the defect left behind. It is not: "the three other flags" is an accurate description of the `skip` **rejection branch**, whose operands are exactly `force_select`, `force_prefetch`, `prefetch_obj` — and `skip` combined with `nested_strategy` is rejected by a different branch and is explicitly enumerated two clauses later in the same sentence. So the enumeration remains exhaustive over rejections, and a reader asking "may I combine `skip=True` with `strategy(...)`?" gets the right answer from the sentence. A one-word loosening to "the other flags" would read marginally better; it is wording I would have chosen differently, not a defect.
- *The `resolve_strategy` name validation is not enumerated.* `__post_init__` also routes `nested_strategy` through `optimizer/nested_fetch.py::resolve_strategy`, so a typo'd strategy name raises `ConfigurationError` at build time, and the sentence does not say so — while the parallel `prefetch_obj` type check ("a `prefetch_obj=` value that is not a `django.db.models.Prefetch` instance") *is* named. The asymmetry is pre-existing in shape: the sentence's own scope statement is "rejects **conflicting flag combinations**", a value-type check is already an over-inclusion, and the omission cannot mislead — nothing in the entry claims strategy names are unvalidated, and `OptimizerHint.strategy`'s own docstring plus `docs/README.md` both say they are. Not filed.

**Two process notes that held up.** The `post_save` observation in `### Implementation notes` is correct and worth having recorded — `grep -rn "post_save" examples/fakeshop --include="*.py"` puts every receiver in the **kanban** app (`signals.py` ×6 plus factories, models, two migrations, three test modules) and **none** in the glossary app, so a later pass will not go hunting for a glossary side row that does not exist. And asserting the target substring's presence and its occurrence count **inside the edit script before `t.save()`** is the right discipline for a `str.replace` against a concurrently-writable row: a drifted body aborts rather than producing a partial or over-reaching write.

### Temp test verification

- **No temp tests were created**, and `docs/builder/temp-tests/r3/` was not used. Nothing in this diff is behavioral: the correctness gate for a rendered document is the four `--check` renders plus `import_spec_terms --check` and `check_spec_glossary.py`, all of which I re-ran, plus the two-consecutive-regenerate byte-stability check and the DB-level row diff. A temp test could demonstrate nothing those exit codes and that row diff do not already prove.
- **No `scripts/review_inspect.py` run and no shadow file used.** Recorded per `worker-3.md` `## Static helper use`: the diff contains no Python, so there is no control flow to shadow and no repeated-literal or import-boundary evidence to gather. Source was read directly (`extension.py`, `hints.py`, `walker.py`) and every reading is cited above.
- **No `pytest`** (`AGENTS.md` rule 15; the full sweep is the final gate's, and it runs immediately after this item closes). **No `--cov*` flag in any command.**

### Notes for Worker 1 (spec reconciliation)

**No spec amendment is owed and none is proposed.** I re-read both contract statements in the reconciled spec against what landed: `### B6` `**Public API.**` already reads "is a static method", and `### B4` already names `OptimizerHint.strategy(...)` as a fifth member with a pointer to the section that owns the backends. This pass brought the durable doc *to* the spec. Nothing in the spec needs to move.

**Consolidated deferred-work catalog — every item this cycle produced that R3 carries.** This is the input to the final gate's `### Deferred work catalog`, and it is the last pass before it, so nothing below lives only in a closed section. Items 1-6 are Worker 1's carry-forward from R2's handoff (each re-derived live in the Audit report's `### 5.`); items 7-8 are Worker 1's own new findings; item 9 is Worker 2's new one; item 10 is Worker 1's item 9, now **discharged** and recorded so the catalog does not re-open it. Where I re-derived a figure myself this pass, that is stated.

1. **`check_optimizer` management command + custom-resolver detection** — named as B6 follow-up at `0.0.3`, never built, and **no card names either**. Dropped from the spec by R2, recorded in the rationale. `inspect_django_type` (`spec-029`) answers a different question and is explicitly not a substitute. *Reason deferred: unbuilt feature work, no card. Recorded in: this artifact's `### 5.` row 2 and Plan `### Notes for Worker 1` item 1; originally R2 handoff item 2.*
2. **The `_record_relation_access`-before-elision ordering invariant has no automated guard** in `walker.py::_plan_select_relation`. *Reason deferred: adding one is a source change and this cycle changes no code. Recorded in: `### 5.` row 3 and Plan item 2; originally the spec-003 cycle's audit via R2 handoff item 3.*
3. **`spec-029`'s "locked `0.316.0`" phrasing, and its `pyproject.toml` figure — one edit, not two.** Re-derived myself this pass: `pyproject.toml:36` reads **`"strawberry-graphql>=0.316.0"`**, `uv.lock` resolves **`0.323.2`**, and the shared `.venv` has `strawberry-graphql 0.323.2`. So `spec-029:331`'s parenthetical *"`pyproject.toml` pins `>=0.262.0`; `uv.lock` resolves `0.316.0`"* is false in **both** halves, and `:653`'s *"The package's `>=0.262.0` floor is open-ended"* is false in its figure while true in its point. The "locked" phrasing itself is live across **8 lines** (`:24`, `:25`, `:43`, `:133`, `:150`, `:329`, `:331`, `:653`); `0.316.0` appears **36 times across 25 lines** in that file, so the tightening job is wider than the "locked" sites alone. **Whoever fixes it must decide for every site at once — correcting the `>=0.262.0` figure alone does not close this.** *Reason deferred: read-only sibling spec, no declared exception in this cycle. Recorded in: `### 5.` row 4 and its follow-on paragraph, Plan item 3; originally R1 handoff item 17 -> R2 handoff item 4.*
4. **The `spec-003` pair's wrong `spec-035` plan-immutability attribution — seven sites, enumerated.** `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md` #"finalized at handoff" plus six body citations in its companion (`:253`, `:521`, `:598`, `:604`, `:855`, `:952`); only `:521`'s projection-gate item is sound. The enumeration lives in the **durable** rationale, not only in a scratchpad. *Reason deferred: both files read-only here. Recorded in: `### 5.` row 5 and Plan item 4; originally R2 handoff item 5.*
5. **Three B7 test names still spell the retired `_optimizer_field_map`.** Re-derived: `tests/optimizer/test_field_meta.py:322` `::test_optimizer_field_map_populated`, `:339` `::test_optimizer_field_map_contains_relations`, `:362` `::test_optimizer_field_map_respects_fields_filter`. *Reason deferred: live test code, outside this cycle's writable set; already carded on `TODO-ALPHA-052-0.1.0`. Recorded in: `### 5.` row 6 and Plan item 5; originally R2 handoff item 6.*
6. **The spec's `## Non-goals` claims Layer-3 features "have their own specs" while aggregates has none.** The normative half — this spec does not cover them — is true. *Reason deferred: R2 declined to land an unreviewed contract edit after a byte-stable round, and the claim **discharges itself** when the aggregates spec lands. Recorded in: Plan item 6; originally R2's `### The two residues Worker 3 recorded rather than filed`, item 1.*
7. **`KANBAN.md` card 4's B1 `Scope` row names four cache-key components; five ship.** Confirmed live at `KANBAN.md:4925` ("plan cache keyed by selected operation AST, directive variables, model, and root runtime path"); the resolver's origin Strawberry type is the missing fifth and arrived with `spec-018`, three releases after this card. *Reason deferred: a `Scope` row is a Done card's record of **declared scope**, not a live contract, and the spec plus the `Plan cache` glossary entry both carry all five correctly — rewriting board history to match a later spec is not what a card records. I agree with the disposition. Whoever disagrees should note the fix is a `CardItem.text` ORM edit plus a `build_kanban_md.py` / `build_kanban_html.py` regenerate. Recorded in: `### 1.` KANBAN audit and Plan item 7.*
8. **`docs/README.md`'s `## Today and coming next` `OptimizerHint` bullet omits `strategy`.** Confirmed live at `docs/README.md:108`: "`OptimizerHint` — per-relation overrides (`SKIP`, `select_related`, `prefetch_related`, custom `Prefetch`)". Unlike F2 this asserts no completeness, and the same file documents `strategy` in full 67 lines later. **Worker 0 did not fold it into this dispatch** — `docs/README.md` is on the do-not-touch list and `git status` confirms it is untouched — so it defers exactly as the Plan anticipated. After F2, this is the **only** durable-doc surface left where `strategy` is absent from an `OptimizerHint` member list. *Reason deferred: outside the writable set; non-blocking. Recorded in: `### 1.` README audit, Plan item 8, and Worker 2's `### Notes for Worker 1` item 2.*
9. **NEW (Worker 2's) — `docs/GLOSSARY.md` `## Connection-aware optimizer planning` carries the same incompleteness F2 just closed, one entry over.** Verified live at `docs/GLOSSARY.md:390`: "The nested fetch strategy is **fixed per** [`DjangoOptimizerExtension`](#djangooptimizerextension) **instance**: `"windowed"` is the default, `"lateral"` … and `"auto"` …". `OptimizerHint.strategy(...)` ships a per-connection-field override taking precedence over the extension-wide setting (`optimizer/hints.py::OptimizerHint.strategy`; `docs/README.md:177`), so the extension-wide value is the **default**, not a fixed value. *Reason deferred: the entry is not one of card 4's ten anchors and the dispatch scopes Worker 2 to F1 and F2, so it is outside this item's writable set. The fix is a `GlossaryTerm(anchor='connection-aware-optimizer-planning')` ORM edit plus a regenerate. Recorded in: Worker 2's `### Notes for Worker 1` item 1, and in my `### DRY findings` above as the live half of the three-carrier duplication. **Same defect class as F1 and F2** — a claim true when written, never re-taken after a later slice extended the surface.*
10. **DISCHARGED, not deferred — the Plan's item 9** ("if Worker 0 rules F2 outside R3's charter, it defers here"). Worker 0 dispatched F2, it landed, and it is graded correct above. The catalog should carry this as closed so a reader of the Plan's `### Notes for Worker 1` does not re-open it.

**One deviation for the audit trail, already graded.** Worker 2's `### Notes for Worker 1` item 3 raises the one-clause extension of F2's rejection enumeration for Worker 1 to keep or revert. **My recommendation is keep**, for the three reasons in `### What looks solid`: it closes the same defect one clause later, it stays inside the Plan's DRY constraint, and its three-flag scope is exact against `__post_init__` (`force_prefetch` deliberately excluded). Reverting it would re-open a smaller copy of the defect this item exists to close. Either way it is a two-line ORM edit plus a regenerate, and it changes no contract the spec states.

**Two corrections to prior cycle files, both confirmed by me and neither changing a conclusion.** These are Worker 0's file, so they are stated here rather than edited: the build plan's `### Fifth change` should read **three** deleted `bld-003-*.md` artifacts, not four (`bld-003-final.md` is restored and byte-identical to `HEAD`); and its `## Worker-0-verified facts` `:158` should read **seven** B-owned `shipped (0.0.3)` entries, not "five" followed by a list of six.

### Review outcome

`review-accepted`, with **zero findings at every severity** and nothing escalated.

**The deliverable is complete**, and final verification is confirming this: two false-at-HEAD statements in `docs/GLOSSARY.md` about the B1-B8 surface, both corrected at their DB source and rendered, with the true clause adjacent to the second one preserved as true. Every one of the seven `### Dispatched findings checklist` **Required changes (Worker 2)** boxes is ticked with work that actually landed — I walked all seven and re-derived each independently: F1 and F2 against source, the regenerate against a two-run md5, the `git status` shape against a live run, and the three chain commands against their own output. The nine `**(W1, done)**` audit boxes were correctly neither re-run nor re-ticked by Worker 2, and I re-derived the two Worker 1 dispositions the dispatch singled out; both hold. The three declarations (`### Failability proofs` `None`, hot-path not applicable, floor not applicable) are true rather than merely asserted, so the empty re-run set is legal.

What remains is a **ten-item deferred catalog**, consolidated above with each item's reason and its recording site, of which one is discharged and nine are live. None blocks this item: six are outside the writable set, one is a source change, one discharges itself when a future spec lands, and one is a deliberate refusal to rewrite board history. Two residues I judged and declined to file are named in `### What looks solid` with the standard I judged them against.


---

## Final verification (Worker 1)

I have no memory of the planning pass that opens this artifact; this file and the working-tree diff
are the record, and both were read end to end before anything below was run. Every figure here was
produced by running the command in **this** pass and reading its output. Nothing is quoted from the
Plan, the Build report, or the Review — where a number matches theirs it is because it re-derived.

**Re-derived first, because everything else is relative to it.** `git rev-parse HEAD` ->
`ff03c1372365edcad488ff4671389d88ae145276`, unchanged across all three passes.
`git log -1 --format='%h %s' -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` ->
`20a9752f docs(spec-003): reconcile the O4 spec with HEAD and extract its rationale` — still the
spec-003 cycle's one-clause B4 rider, so nothing of this cycle has been swept into a commit by the
concurrent card-005 session. Checked with `git log`, never with `git status` alone. No `git stash`,
`git checkout`, `git restore`, or `git worktree` was run. No branch created or switched. Nothing
committed. No `pytest`. No `--cov*` flag in any command.

**Spec status-line re-verification** (`worker-1.md` `## Spec status-line re-verification`, owed every
Worker 1 spawn): spec-004 carries **no** `Status:` / owner / target-release / predecessor header
block — `:1` is the title, `:3` the companion-pointer paragraph, `:5` `## Problem statement`. There
is no status line for this build to have falsified, so no header edit was owed and none was made.
The `:3` pointer describes the move accurately and its `[spec-004-rationale]` target resolves.

### The checklist audit — all sixteen boxes settled against the file, not against the record

`ARTIFACT.md` makes this the pass that grades the ticks. **All sixteen boxes are `- [x]`, every one
correctly. No box was un-ticked, none was ticked, and none is left `- [ ]`, so no deferral reason is
owed under `### Spec changes made (Worker 1 only)`.** Each of the seven Worker 2 boxes was
re-derived independently below; the nine `**(W1, done)**` audit boxes were re-run rather than read.

**Required changes (Worker 2) — seven boxes, seven landed.**

1. **F1.** `docs/GLOSSARY.md` `:745` now reads *"… Static method [`check_schema`](#schema-audit)
   audits schema-reachable `DjangoType`s."* Graded against source, not against the report:
   `grep -n -B2 "def check_schema" django_strawberry_framework/optimizer/extension.py` ->
   `1247-    @staticmethod` / `1248:    def check_schema(schema: Any) -> list[str]:`. No `cls`. The
   `#schema-audit` target still resolves (`:1797`), and `Classmethod` no longer occurs in the file.
2. **F2.** The rendered `## OptimizerHint` entry carries a fifth `Supported modes:` bullet naming
   `OptimizerHint.strategy(...)` and pointing at `## Nested connection indexing` in `docs/README.md`
   — **no backend name, no selection rule, no precedence rule, no extension-wide default**, which is
   the Plan's DRY constraint. The factory parenthesis now lists five; the walker clause reads "the
   **first** four shapes are the only ones the walker dispatches". Both halves checked at source:
   `grep -c "nested_strategy" django_strawberry_framework/optimizer/walker.py` -> **0**, and
   `walker.py::_apply_hint` branches on exactly four shapes — `hint_is_skip(hint)` (`:957`),
   `hint.prefetch_obj is not None` (`:959`), `hint.force_select` (`:1027`), `hint.force_prefetch`
   (`:1049`) — then `return False` (`:1064`). So the surviving clause is **true**, and the trap the
   Plan named was not walked into. The one-clause deviation is graded separately below.
3. **Regenerate + four `--check`s.** Re-run this pass, all exit 0: `build_glossary_md.py --check` ->
   `docs/GLOSSARY.md is up to date.`; `build_kanban_md.py --check` -> `KANBAN.md is up to date.`;
   `build_kanban_html.py --check` -> `KANBAN.html is up to date.`; `build_tree_md.py --check` ->
   `docs/TREE.md is up to date.`
4. **`git status --short` shape.** **16 entries**, exactly the Plan's 14 plus `M docs/GLOSSARY.md`
   and `M examples/fakeshop/db.sqlite3`. `KANBAN.md` and `KANBAN.html` appear nowhere and are
   `--check`-clean. Nothing new appeared during this pass; nothing was reverted.
5. **`import_spec_terms --check`** -> **`OK: 49 done cards have glossary links.`** exit 0.
   **Read-only `--check` form only; the writing sync form was not invoked in this pass.**
6. **`check_spec_glossary.py --spec`** -> **`OK: 10 terms - all have glossary entries and at least
   one spec link.`** exit 0.
7. **`check_trailing_commas.py --check`** exit 0 on the spec, the rationale, `docs/GLOSSARY.md`, and
   this artifact — re-run after the last edit to this file.

**Audit obligations (Worker 1) — nine boxes, all re-run rather than accepted.**

- **Durable-doc audit.** The two findings the planning pass raised are the two that landed; the other
  three docs re-check clean by their own `--check` renders (box 3 above), and `docs/README.md`
  `## Nested connection indexing` `:175` still owns the strategy contract in full.
- **Archive completeness, all three directions.** Outbound re-derived with a parser written for this
  pass (partitions at `<!-- LINK DEFINITIONS -->`, strips code spans before scanning uses, resolves
  each target against the **source file's own directory**, slugs headings **keeping `_`**): spec
  **11 defs / 11 used / 0 undefined / 0 unused**; rationale **24 / 24 / 0 / 0**; **35/35 targets
  exist on disk and every anchored target's heading resolves**. Reproduces the planning pass exactly,
  and handoff item 18's slugger hazard reproduced and was handled the same way. Inbound:
  `grep -rn --exclude-dir=docs/builder 'docs/spec-004' .` -> **no match**, so not one durable
  reference points at the pre-archive location. Companion depth is confirmed by the same disk-exists
  check plus `check_trailing_commas --check` exit 0 on both files.
- **`SpecDoc.path` and the terms-CSV chain**, read live through the ORM rather than off the rendered
  board: `Card.objects.get(number=4)` -> `card_id` **`DONE-004-0.0.3`**, `status.key` **`done`**,
  `target_version.number` **`0.0.3`**, title **`Optimizer beyond slices B1-B8`**; the card's
  `SpecDoc.path` is **`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`**, already archived;
  `card.glossary_links.count()` -> **10**, and the ten anchors are character-for-character the ten
  data rows of `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-terms.csv` (**10 rows / 10 distinct
  anchors**, no anchor repeated, which is what `import_spec_terms` requires and a green
  `check_spec_glossary` alone does not prove). All ten terms carry glossary status **`Shipped`**.
- **Staged-anchor sweep**, `worker-1.md` `## Final verification job` step 6, re-run here as the
  doc-completion item's own obligation and not on the planning pass's word:
  `grep -rEn 'TODO\(spec-004|TODO-(ALPHA|BETA|STABLE)-004' .` -> **3 hits**
  (`docs/builder/build-004-optimizer_beyond-0_0_3.md:29`, `:343`,
  `docs/builder/bld-004-r2-spec_reconciliation.md:3889`), **all three the grep pattern itself quoted
  in prose describing the sweep**. The same sweep with `--exclude-dir=docs/builder` returns **no
  match** (exit 1): no source, no test, no example, no standing doc, nothing in the spec or the
  rationale. **No staged anchor exists in shipped material**, so nothing survives to the integration
  backstop and no `revision-needed` is owed on this ground.
- **The 18-item handoff and the `iterdump()` attribution** are re-derived under their own headings
  below.

### The two corrections hold, and `docs/GLOSSARY.md` is genuinely regenerated output

Re-derived rather than read off Worker 3's acceptance, per `worker-1.md`
`### Verifying relocation / promotion claims`.

**Two-consecutive-regenerate byte stability, with a pre-run baseline so a hand-edit could not hide.**
`md5` of `docs/GLOSSARY.md` **before any run this pass**: `e62be86ba4c853cd61a95e97055d9f51`. After
`uv run python scripts/build_glossary_md.py` (run 1, `Wrote 142 terms, 146 category memberships, 1042
spec mentions across 49 specs`): **`e62be86ba4c853cd61a95e97055d9f51`**. After a second run:
**`e62be86ba4c853cd61a95e97055d9f51`**. `build_glossary_md.py --check` -> `docs/GLOSSARY.md is up to
date.` exit 0, and `git diff --stat -- docs/GLOSSARY.md` is still `1 file changed, 8 insertions(+), 6
deletions(-)` afterwards. **The pre-run md5 is the load-bearing one**: a hand-edit would have been
overwritten by run 1 and the md5 would have moved. It did not, so the file on disk is exactly what
the DB renders.

**The DB delta attributed semantically, never by file bytes** — required here because a card-005
cycle is writing this same DB concurrently. `git show HEAD:examples/fakeshop/db.sqlite3` into a
scratch path **outside the repository**, then `sqlite3.iterdump()` on both sides opened `mode=ro`:
**9,806 statements each side; multiset difference 2 added / 2 removed, all four
`INSERT INTO "glossary_glossaryterm"`, rows `id=459` and `id=487`.** **Zero statements in the delta
touch any `kanban_*` table**, any other app's table, or any schema statement — which is the
independent reason `KANBAN.md` / `KANBAN.html` stayed `--check`-clean and absent from `git status`,
and it is why "the DB is dirty" is not evidence of anything this cycle must answer for beyond those
two rows. Two rows, two findings; no third row moved.

**The one-clause deviation from the Plan's letter: KEPT.** Worker 2's `### Notes for Worker 1` item 3
leaves the decision here. The rejection enumeration gained `` `nested_strategy=` set with
`skip=True`, `prefetch_obj=`, or `force_select=True` ``. Read at source rather than accepted:
`optimizer/hints.py::OptimizerHint.__post_init__` `:155` guards `if self.nested_strategy is not
None:` and `:159` rejects `if self.skip or self.prefetch_obj is not None or self.force_select:` —
**three** operands, in that order, with `force_prefetch` deliberately excluded and the code comment
at `:156`-`:158` saying so ("``force_prefetch`` is redundant-but-harmless and stays allowed"). The
clause matches the guard operand for operand. Keeping it is right for the reason Worker 2 gave and
Worker 3 confirmed: a fifth factory adds a fifth flag, so closing an incomplete enumeration in one
sentence while leaving one in the next is not a fix. It imports no backend rule, so the DRY
constraint holds. **Reverting it would re-open a smaller copy of the defect F2 exists to close.**

### DRY check across R3 and the two closed items

- **Against R1 and R2 — no overlap is possible and none exists.** R1 wrote the rationale, R2 wrote
  the spec, R3 wrote neither. `git diff --stat -- docs/SPECS/` this pass shows the spec modified
  only by R2's uncommitted work (`236 lines / 36,223 bytes`, byte-stable since R2 closed — measured,
  and matching this artifact's own header) and the rationale untracked at `1,309 / 94,318`. R3's own
  diff is `docs/GLOSSARY.md` plus two DB rows. Three items, three disjoint surfaces.
- **The fix is a pointer, not a fourth copy.** The nested-connection strategy contract has three
  durable carriers; the new bullet adds no backend, no selection rule, no precedence rule, so it is
  a reference rather than a transplant. The live duplication is in the *second* carrier
  (`docs/GLOSSARY.md` `## Connection-aware optimizer planning` `:390`, "fixed per … instance"), which
  is outside this item's writable set and is catalog item 9. **Correctly deferred, not filed** — the
  entry is not one of card 4's ten anchors and the dispatch scoped Worker 2 to F1 and F2.
- **No repeated literal, no near-copy, no new helper, no new indirection.** The diff adds no
  function, class, constant, or branch anywhere; `git diff -- django_strawberry_framework/` is empty.
- **One structural restatement, and it is the artifact's designed shape rather than a DRY defect.**
  The deferred list appears three times in this file — the Plan's `### Notes for Worker 1` (9 items),
  Worker 2's (3 items, one new), and Worker 3's consolidated `### Notes for Worker 1` (10). Each is a
  superset naming its provenance, and `ARTIFACT.md` `## Re-pass sections` forbids editing a prior
  entry, so consolidation forward is the only available shape. **The gate must key off Worker 3's
  ten-item list — the last one — never the Plan's nine**, or it drops Worker 2's item 9.

### Failability, fail-open, hot-path, floor — the four declarations verified rather than accepted

`### Failability proofs` reads `None; this pass introduced no new boundary.` **True, and mechanically
so:** `git diff -- django_strawberry_framework/ tests/` is empty, so no guard, gate, cap, rejection
path, coercion, or validation branch was added anywhere. The boundary vocabulary in the changed prose
*describes* a `__post_init__` guard that shipped long before this cycle; describing a boundary is not
introducing one. **No fail-open shape could have landed**, because no expression did — I read the
whole diff, and it is markdown plus two DB text columns. Hot-path and floor correctly read not
applicable and match the plan declarations (`none` for both), so no number and no isolated-venv run
is owed to the final gate on this item's behalf.

### Existing tests still pass — stated in the only honest form for a no-code cycle

`git diff --stat -- django_strawberry_framework/ tests/ examples/` ->
`examples/fakeshop/db.sqlite3 | Bin 5050368 -> 5050368 bytes` and nothing else: **no package source,
no test, and no example source file changed in this cycle**, and the one entry is the DB write R3
legitimately made, already attributed row-by-row above. `uv run python examples/fakeshop/manage.py
check` -> **`System check identified no issues (0 silenced).`** exit 0. **No `pytest` was run and
none is owed here** — `AGENTS.md` rule 15 and `BUILD.md` `## Final test-run gate`, which owns the
full sweep and runs immediately after this pass. No `--cov*` flag.

### Spec reconciliation — no Worker 1 spec edit is owed, and none was made

Nothing R3 surfaced requires one. The reconciled spec already carries both corrected contracts —
`### B6` `**Public API.**` reads "is a static method", and `### B4` already names
`OptimizerHint.strategy(...)` as a fifth member with a pointer to the section that owns the backends.
**R3 brought the durable doc *to* the spec; it found nothing in the spec to change**, and both
Worker 2 and Worker 3 reached the same conclusion independently. The spec has been byte-stable since
R2 closed and re-measures at **236 lines / 36,223 bytes**; reopening it needs a real defect, and
there is none. `AGENTS.md` rule 27 holds on both durable files (`grep -nE
'[a-zA-Z_/]+\.(py|md):[0-9]+'` -> no match in either) and both still carry **0** fenced code blocks.

### The ten-item catalog audited as the gate's input — nine live, one discharged, and ONE MISSING

Worker 3's consolidated `### Notes for Worker 1` is the deliverable the maintainer asked for by name,
and this is the last pass before the gate reads it. **Every one of the ten was re-derived live this
pass**, not graded against Worker 3's account of it:

| # | Live re-derivation | Verdict |
|---|---|---|
| 1 | `grep -c check_optimizer` over the spec -> **0**; `management/commands/` ships `export_schema.py` and `inspect_django_type.py` only | Open, real |
| 2 | `walker.py::_record_relation_access` defined `:826`, called `:722` / `:786` / `:1004`, no ordering assertion | Open, real |
| 3 | `pyproject.toml:36` -> `"strawberry-graphql>=0.316.0"`; `grep -c '0.316.0'` over `spec-029` -> **25 lines**; `grep -c locked` -> **8 lines** | Open, real, correctly scoped as ONE edit |
| 4 | `spec-003` #"finalized at handoff" present; six companion citations plus the definition | Open, real |
| 5 | `tests/optimizer/test_field_meta.py` `:322` / `:339` / `:362`, all three names live | Open, real, already carded |
| 6 | Spec `:181` "those have their own specs"; aggregates has no spec on disk | Open, self-discharging |
| 7 | `KANBAN.md:4925` names four cache-key components | Open, deliberate refusal |
| 8 | `docs/README.md:108` omits `strategy` | Open, non-blocking |
| 9 | `docs/GLOSSARY.md:390` "The nested fetch strategy is **fixed per** … instance" | Open, real |
| 10 | F2 was dispatched, landed, and is graded correct | **DISCHARGED — unambiguously marked, not re-openable** |

**Every open item names real, still-open work, each carries its reason and its recording site, and
item 10's discharge is unmistakable.** The catalog is accurate. It is not quite complete.

**MISSING — one item this cycle deferred that lives ONLY in a closed artifact.** `bld-004-r1` is
closed, and its final verification records a precision note against the **durable** rationale that
R2 never picked up and that no later list carries:

> `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` #"The same characterization was in
> the spec's own pointer text" asserts the characterization was in *"the companion-pointer paragraph
> and the eight per-slice pointers"*. Measured this pass: there are indeed **eight** per-slice
> pointers (spec `:41`, `:63`, `:81`, `:109`, `:119`, `:139`, `:151`, `:171`), but **B8's (`:171`)
> opens "The ordering argument that put this slice last" and never carried the characterization** —
> so it was in **seven** of the eight. The same paragraph's closing clause ("`### B5`'s and
> `### B7`'s pointers now open 'The opening argument' where **the others** still open 'The
> competitive argument'") is imprecise in the same direction: five of the remaining six do, and B8
> does not.

R1 recorded it, declined to fix it at its own final gate for the reason I would give here, and handed
it to R2 as *"R2 can tighten it in one clause if it opens that paragraph."* **R2 did not open that
paragraph** — `grep -n "771\|per-slice pointers"` over `bld-004-r2` returns nothing, and R2's
18-item handoff has no row for it — so it was never carried forward, and R3 could not have known to
carry it: R3's input was R2's handoff, not R1's artifact. **This is exactly the failure the
"nothing lives only in a closed artifact" rule exists to catch, and it is a rule-shaped miss rather
than anyone's error.** It belongs in the gate's catalog as an eleventh item:

> **11. The rationale's `**The win.**` account overstates the pointer population by one.** Durable
> file, tracked and committed alongside the spec. The characterization was in seven of the eight
> per-slice pointers, not eight; five of the remaining six still open "The competitive argument", not
> all of them. *Reason deferred: the rationale has been byte-stable since R2 closed, and landing
> unreviewed prose in a durable file at a final gate is the trade `worker-1.md` and R1's own final
> verification both refuse — no reader reaches a wrong action from the sentence, and its operative
> instruction (do not level the deliberate B5/B7 asymmetry back) is unaffected. Recorded in:
> `bld-004-r1-rationale_move.md` `## Final verification (Worker 1)` #"One precision note on the
> durable paragraph that carries item 20", and now here. Fix it in one clause whenever a chartered
> pass next opens that paragraph — it is the same "state the population beside any universal" class
> the cycle hit six times.*

**I did not fix it**, and that is a decision rather than an omission: it is not required to accept
R3, the file is byte-stable, and my own carry-forward from R2 is *"do not land an unreviewed contract
edit at final verification after a byte-stable round — prefer `final-accepted` and route."*

**Accounted for and correctly absent, so the gate does not hunt for them.** R2's final verification
names five items it examined and deliberately did **not** file. Four are settled rather than
deferred: `## Current state`'s "effective end-to-end" (HEAD's own unfalsifiable wording), `### B7`'s
"Benchmark (optional)" (marked optional, never a delivery claim), the rationale's `## How to read
this file` bullet 8 (scoped to the extraction pass by its own first three words), and the
`34`-where-it-is-`35` numeral (a per-cycle scratchpad figure, correctly routed nowhere). The fifth,
the `## Non-goals` aggregates clause, **is** a deferral and **is** carried, as catalog item 6. **The
gap was item 11 and nothing else.**

### The three corrections to the build plan, confirmed for Worker 0 — the plan is not mine to edit

`docs/builder/build-004-optimizer_beyond-0_0_3.md` is Worker 0's file. All three corrections
re-derived independently this pass and all three hold:

1. **`## Worker-0-verified facts` `:158` says "the five B-owned entries" and then names six; the
   measured figure is seven.** Queried against the DB rather than the rendered doc:
   `select anchor, status_text from glossary_glossaryterm where status_text like '%0.0.3%'` ->
   **exactly 7 rows** — `fk-id-elision`, `metaoptimizer_hints`, `optimizerhint`, `plan-cache`,
   `queryset-diffing`, `schema-audit`, `strictness-mode`, every one `shipped (`0.0.3`)`. The omitted
   seventh is `OptimizerHint`, which is precisely the entry F2 corrects. **The conclusion the
   sentence carries — every B-owned entry is `shipped (0.0.3)`, no status flip owed — is unaffected.**
2. **`:160`'s staged-anchor baseline reads "zero hits anywhere"; the real result is 3, all
   attributable.** Re-run above. The baseline was taken at pre-flight, which `BUILD.md`
   `## Pre-flight checks` places *before* plan creation — so the plan and R2's artifact, the files
   that make it non-zero, did not yet exist. **Stating the raw 3 and attributing it is the honest
   form**; a filtered "zero" would require silently excluding files. The obligation is discharged
   either way: zero hits outside `docs/builder/`.
3. **`### Fifth change` `:212` says four deleted `bld-003-*.md` artifacts; it is three.**
   `docs/builder/bld-003-final.md` is on disk (32,693 bytes) and byte-identical to `HEAD` — it does
   not appear in `git status` at all — restored by something outside this cycle.
   `git status --short -- docs/builder/ | grep '^ D'` -> **three**. **The other three deletions
   persist and were NOT restored**; they remain the maintainer's call, and restoring them would need
   the `git checkout` `AGENTS.md` rule 34 forbids while concurrent sessions are writing.

### One observation on this artifact's own prose, non-blocking and not corrected

The Plan's `### 2a.` and `### Validation run` state that `grep -rn 'docs/spec-004' .` returns "no
match anywhere in the tree". Re-run now it returns **2 hits — both lines of this artifact quoting the
command itself**, the same self-reference the staged-anchor sweep handled explicitly and honestly two
sections later. The substantive claim is unaffected and re-proved above:
`grep -rn --exclude-dir=docs/builder 'docs/spec-004' .` -> **no match**, so not one durable reference
points at the pre-archive path. `ARTIFACT.md` forbids editing a prior entry, so the correction lives
here rather than there; it changes no conclusion.

### Working-tree state — re-derived, reported, not reverted

`git status --short` -> **16 entries**, byte-for-byte the list Worker 2 and Worker 3 recorded, and
unchanged from the start of this pass to its end:

```
 M docs/GLOSSARY.md
 M docs/SPECS/spec-004-optimizer_beyond-0_0_3.md
 M docs/SPECS/spec-005-django_type_contract-0_0_3.md
 D docs/builder/bld-003-r1-rationale_move.md
 D docs/builder/bld-003-r2-spec_reconciliation.md
 D docs/builder/bld-003-r3-doc_completion_archive.md
 M examples/fakeshop/db.sqlite3
?? docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md
?? docs/SPECS/appx/spec-005-django_type_contract-0_0_3-rationale.md
?? docs/builder/bld-004-r1-rationale_move.md
?? docs/builder/bld-004-r2-spec_reconciliation.md
?? docs/builder/bld-004-r3-doc_completion_archive.md
?? docs/builder/bld-005-r1-rationale_move.md
?? docs/builder/bld-005-r2-spec_reconciliation.md
?? docs/builder/build-004-optimizer_beyond-0_0_3.md
?? docs/builder/build-005-django_type_contract-0_0_3.md
```

**No new dirty entry appeared and none cleared during this pass.** `docs/SPECS/spec-005-*`, the
`bld-005-*` / `build-005-*` files, and `appx/spec-005-*` are the concurrent card-005 cycle's; none
was read for content, edited, or reverted. `docs/builder/worker-memory/worker-1.md` was appended to
and correctly does not appear — that directory is gitignored.

### Validation run — every command run in this pass, output pasted, nothing quoted

- `git rev-parse HEAD` -> `ff03c1372365edcad488ff4671389d88ae145276`.
- `git log -1 --format='%h %s' -- docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> `20a9752f docs(spec-003): reconcile the O4 spec with HEAD and extract its rationale`.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-004-optimizer_beyond-0_0_3.md` -> **`OK: 10 terms - all have glossary entries and at least one spec link.`** exit 0.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-004-optimizer_beyond-0_0_3.md docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md docs/GLOSSARY.md docs/builder/bld-004-r3-doc_completion_archive.md` -> exit 0, all four; re-run after the last edit to this file.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` -> **`OK: 49 done cards have glossary links.`** exit 0. **Read-only `--check` form only.**
- `uv run python examples/fakeshop/manage.py check` -> **`System check identified no issues (0 silenced).`** exit 0.
- `uv run python scripts/build_glossary_md.py` x2 -> `Wrote 142 terms, 146 category memberships, 1042 spec mentions across 49 specs`; md5 `e62be86ba4c853cd61a95e97055d9f51` before, after run 1, and after run 2. **Byte-stable.**
- `uv run python scripts/build_glossary_md.py --check` / `build_kanban_md.py --check` / `build_kanban_html.py --check` / `build_tree_md.py --check` -> `is up to date.` exit 0, all four.
- `git diff --stat -- django_strawberry_framework/ tests/ examples/` -> `examples/fakeshop/db.sqlite3 | Bin 5050368 -> 5050368 bytes` only.
- `sqlite3.iterdump()` vs `git show HEAD:examples/fakeshop/db.sqlite3` in a scratch path outside the repo -> **9,806 = 9,806; 2 added / 2 removed, all `glossary_glossaryterm`, ids 459 and 487; zero `kanban_*`**.
- `grep -rEn 'TODO\(spec-004|TODO-(ALPHA|BETA|STABLE)-004' .` -> 3 hits, all attributed; with `--exclude-dir=docs/builder` -> **no match**.
- `grep -rn --exclude-dir=docs/builder 'docs/spec-004' .` -> **no match**.
- Link parser -> spec **11/11**, rationale **24/24**, **35/35** targets and anchors resolve.
- Counts re-derived after the last edit: spec **236 lines / 36,223 bytes**; rationale **1,309 / 94,318**; terms CSV **10 rows / 10 distinct anchors**; card 4 glossary links **10**; B-owned `shipped (0.0.3)` entries **7**; per-slice rationale pointers **8**; working tree **16 entries**.
- No `pytest`. No `--cov*` flag. No `ruff` (this pass wrote no Python). No `git stash` / `checkout` / `restore` / `worktree`. No branch created or switched. Nothing committed.

### Summary

R3 shipped what its charter names: the durable docs audited against **source** rather than against
the spec, and the two false-at-HEAD statements that audit found in `docs/GLOSSARY.md` corrected at
their DB source and rendered. `check_schema` is no longer called a classmethod — a word that survived
from spec-004's original pseudo-code through eleven releases, three residual cycles, and R2's own
correction of the same claim in the same words one document over — and the `OptimizerHint` entry no
longer presents four factories as the whole consumer API while five ship, with the adjacent
walker-dispatch claim preserved as **true** rather than collapsed into a convenient falsehood.

The archive audit re-derived clean in all three cross-reference directions (**35/35** links and
anchors, no reference to the pre-archive path), the kanban chain re-derived clean
(`DONE-004-0.0.3`, `SpecDoc.path` archived, ten CSV anchors == ten card links, all `Shipped`), and
the staged-anchor sweep is discharged with zero hits in shipped material. All sixteen checklist boxes
landed. No code, test, or example source changed. No spec edit was owed and none was made.

**`final-accepted`.** Worker 3 filed nothing at any severity, every claim I could re-derive
re-derived, and the one thing I found — the missing eleventh catalog item — is a gap in the **gate's
input**, not a defect in R3's contract, and it is closed by recording it here. The gate's
`### Deferred work catalog` should carry **eleven** items: Worker 3's ten (nine live, one discharged)
plus item 11 above, and it should key off Worker 3's consolidated list rather than the Plan's nine.
The standing lesson this item bought is worth the cycle: **a defect corrected in a spec is not
corrected in the docs that copied the spec, and the only thing that finds the copy is reading the
durable doc against source.**

### Spec changes made (Worker 1 only)

**None. No spec was changed in R3, by me or by anyone.** `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`
has been byte-stable since R2's pass-2 apply and re-measures at **236 lines / 36,223 bytes**; its last
commit is still `20a9752f`. The spec's edits belong to **R1** (the rationale extraction) and **R2**
(the spec-versus-HEAD reconciliation) and are recorded in full in those two items' closed artifacts,
`docs/builder/bld-004-r1-rationale_move.md` and `docs/builder/bld-004-r2-spec_reconciliation.md`,
each under its own `### Spec changes made (Worker 1 only)`. Nothing R3 surfaced requires reopening
the spec: both contracts R3's findings touch are already stated correctly there.

`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` was also not changed, deliberately —
see the eleventh catalog item above for the one imprecision I found in it and the reason it is routed
rather than fixed.

**No deferral reason is owed under this heading for a checklist box**, because no box is left
`- [ ]`: all sixteen are ticked and all sixteen were audited as landed.
