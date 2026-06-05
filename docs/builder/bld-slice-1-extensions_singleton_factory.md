# Build: Slice 1 — migrate `extensions=` construction sites to the singleton-factory form

Spec reference: `docs/spec-029-consumer_dx_cleanup-0_0_9.md` (lines 101-107 Slice-1 checklist; Decision 3 lines 327-357; User-facing API lines 206-231; Doc updates "Slice 1"; DoD items 2-4)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - The migration target form is *already shipped in three places* and is the single canonical shape to copy verbatim — do not invent a variant. The TODO scaffolds the maintainer placed are the authoritative templates:
    - Module-level singleton + factory: `examples/fakeshop/config/schema.py:33-40` (TODO pseudo), `docs/README.md:52-56` (TODO pseudo), `docs/GLOSSARY.md:358-364` (TODO pseudo). All three spell `_optimizer = DjangoOptimizerExtension()` then `extensions=[lambda: _optimizer]`.
    - Function-local form (test files): `tests/optimizer/test_extension.py:34-39` (module-top TODO), `tests/optimizer/test_field_meta.py:10`, `tests/optimizer/test_relay_id_projection.py:14`, `tests/test_list_field.py:41`, `tests/types/test_generic_foreign_key.py:13`, `examples/fakeshop/test_query/test_multi_db.py:32` — all spell `schema = strawberry.Schema(..., extensions=[lambda: ext])` keeping the function-local `ext`.
  - The behavior-preserving guarantee (one shared instance per process) means the existing optimizer suite (`tests/optimizer/test_extension.py` etc.) IS the regression guard; no new behavioral test is added beyond the one no-warning assertion (spec Test plan "Slice 1").
- **New helpers justified.** None. Slice 1 is a mechanical per-construction-site rewrite of an existing call expression (`extensions=[<instance-or-class>]` → `extensions=[lambda: <instance>]`); it adds no function, class, module, or constant. Extracting any shared helper (e.g. a `make_optimizer_factory()`) would be premature and would obscure the per-site lifetime/strictness semantics the spec deliberately keeps explicit per site (Decision 3 "Granularity is per construction site, not per file"). The condition that would later justify a helper: if a consumer-facing API were added to construct the factory (out of scope; the spec rejects it).
- **Duplication risk avoided.** The naive implementation could (a) introduce a single module-level `_optimizer` shared across the ~41 schema builds in `tests/optimizer/test_extension.py`, which would *pollute the per-test `cache_info()` counters* and break the `strictness="raise"` site in `test_relay_id_projection.py`; the plan prevents this by keeping each test's **function-local** `ext` and wrapping only the call site (`extensions=[lambda: ext]`). It could also (b) collapse the two distinct directions of the same lambda body into a copy-paste constant; that risk does not arise because each `lambda` closes over a *different* per-site instance, so there is no literal to extract. The repeated literal `extensions=[lambda: ext]` across test sites is the intended, readable, per-site shape — not a DRY defect (it is the upstream-recommended callable form applied uniformly).

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against current source before editing (this is a planning-pass snapshot of 2026-06-05).

**A. Package test files — function-local `lambda: <instance>` per construction site (keep each site's existing `ext`/instance):**

1. `tests/optimizer/test_extension.py` — the bulk of the work; **42 active construction sites** (the file has 43 `extensions=[` matches; one at line 2881 is inside a *docstring*, see Implementation discretion item 1). Wrap each, by category:
   - **Anonymous-instance sites** (17): lines 214, 261, 313, 370, 402, 429, 455, 650, 687, 1974, 2017, 2053, 2235, 2460, 2493, 2767, 2804 — each is `extensions=[DjangoOptimizerExtension()]`. Hoist the instance to a function-local `ext = DjangoOptimizerExtension()` (mirroring the named sites) immediately before the `strawberry.Schema(...)` call and rewrite to `extensions=[lambda: ext]`. (A function may already define `ext` elsewhere; reuse it if it is the same intended instance, otherwise name uniquely — Implementation discretion item 2.)
   - **Named `[ext]` sites** (22): lines 131, 169, 745, 782, 814, 865, 961, 1000, 1034, 1253, 1284, 1326, 1366, 1547, 1590, 1635, 2102, 2187, 2544, 2595, 2657, 2949 — already hold a function-local `ext` (sometimes `ext = DjangoOptimizerExtension(strictness=...)`). Rewrite `extensions=[ext]` → `extensions=[lambda: ext]`. Do NOT change the `ext` construction; the `cache_info()`/`_plan_cache` assertions (e.g. line 136 `assert ext.cache_info().misses == 1`) keep referencing the same function-local instance, which the closure still shares per request.
   - **`_CaptureExt()` subclass sites** (2): lines 2717 and 2849, each `extensions=[_CaptureExt()]` where `_CaptureExt(DjangoOptimizerExtension)` is a function-local subclass (defined at 2704 and 2836). Hoist to `capture_ext = _CaptureExt()` and rewrite to `extensions=[lambda: capture_ext]` (a `DjangoOptimizerExtension()`-literal grep misses these — the forbidden-form gate names `[_CaptureExt()]` explicitly).
   - Remove the module-top TODO scaffold comment at lines 34-39 in the same change (staging note: source TODO anchors are removed when the slice ships; keep the file `ERA001`-clean).
2. `tests/optimizer/test_relay_id_projection.py` — 3 active sites: line 56 `extensions=[DjangoOptimizerExtension()]`, line 85 `extensions=[DjangoOptimizerExtension(strictness="raise")]`, line 162 `extensions=[DjangoOptimizerExtension()]`. Hoist each to a function-local `ext = DjangoOptimizerExtension(...)` (the strictness site keeps `strictness="raise"`) and wrap `extensions=[lambda: ext]`. A single module-level instance cannot carry two strictness values, so these stay per-site. Remove the line-14 TODO comment.
3. `tests/optimizer/test_field_meta.py` — 1 active site: line 323 `extensions=[DjangoOptimizerExtension()]` → function-local `ext` + `extensions=[lambda: ext]`. Remove the line-10 TODO comment.
4. `tests/test_list_field.py` — 2 active sites: lines 758, 891, both `extensions=[DjangoOptimizerExtension()]` → function-local `ext` + `extensions=[lambda: ext]`. Remove the line-41 TODO comment.
5. `tests/types/test_generic_foreign_key.py` — 1 active site: line 107 `extensions=[DjangoOptimizerExtension()]` → function-local `ext` + `extensions=[lambda: ext]`. Remove the line-13 TODO comment.

**B. Example test (live HTTP) — function-local:**

6. `examples/fakeshop/test_query/test_multi_db.py` — 1 active site: line 150 `extensions=[DjangoOptimizerExtension()]`. This sits inside a schema-building helper that stashes the schema in `_current["schema"]` (TODO pseudo at line 32 spells `extensions=[lambda: optimizer]`). Hoist the instance to a local (`optimizer = DjangoOptimizerExtension()`) and wrap `extensions=[lambda: optimizer]`. Remove the line-32 TODO comment. Verify the helper's per-call lifecycle is preserved (each call builds a fresh schema/instance — matches the prior behavior).

**C. Example schema — module-level singleton (one schema per module):**

7. `examples/fakeshop/config/schema.py` — line 44 is the bare class form `extensions=[DjangoOptimizerExtension]` (a cold-cache regression under 0.316.0). Replace the TODO block (lines 33-40) + the construction with:
   ```python
   _optimizer = DjangoOptimizerExtension()
   schema = strawberry.Schema(
       query=Query,
       config=strawberry_config(),
       extensions=[lambda: _optimizer],
   )
   ```
   `_optimizer` is module-level here (genuinely one schema per module). Keep `config=strawberry_config()`. Remove the TODO scaffold comment.

**D. Standing docs — module-level singleton form + one-line rationale:**

8. `docs/README.md` — 3 snippet sites plus 2 TODO blocks:
   - Lines 45-49 (quick-start `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`): rewrite to `_optimizer = DjangoOptimizerExtension()` + `extensions=[lambda: _optimizer]`; remove the TODO at lines 51-57; add the one-line note "module-level singleton wrapped in a factory — preserves the instance-bound [Plan cache][...], no deprecation warning".
   - Line 148 (Recommended) and line 159 (Wrong order): rewrite both to the singleton-factory form; remove the TODO at lines 150-154. The "Wrong order" snippet keeps its ordering-bug point — only the `extensions=` form changes.
   - Use the existing reference-style `[Plan cache][...]` link id already present in `docs/README.md` if one exists; otherwise add a def under `<!-- docs/ -->` per the START.md link convention. (Discretion item 3.)
9. `docs/GLOSSARY.md` — 4 code-fence snippet sites + 1 inline-prose site + 1 TODO block:
   - Line 355 (`DjangoOptimizerExtension` entry opt-in snippet) → singleton-factory; remove the TODO at lines 358-364 and fold its "Rewrite this snippet and the other schema-construction snippets in this file" instruction into the rewrite of all of them.
   - Line 500 (`finalize_django_types` entry snippet) → singleton-factory.
   - Lines 1104 (`strawberry_config` entry snippet, the multi-line `extensions=[DjangoOptimizerExtension()],`) → singleton-factory.
   - Line 185 (inline prose: "`strawberry.Schema(query=Query, config=strawberry_config(), extensions=[DjangoOptimizerExtension()])`" in the `BigInt scalar` entry): rewrite the inline example to the singleton-factory form for consistency (prose, not test-breaking, but the forbidden-form grep would otherwise flag `extensions=[DjangoOptimizerExtension()]` here). Confirm the surrounding sentence still reads correctly after the form change.
   - Add the one-line rationale note where a snippet introduces the form (the `DjangoOptimizerExtension` entry is the natural home; the others may just show the form).
10. `examples/fakeshop/test_query/README.md` — line 15 prose ("...constructs `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])`") and line 21 (already shows `extensions=[lambda: _optimizer]`): rewrite the line-15 prose to describe the singleton-factory form so it matches the line-21 example and `config/schema.py`. Prose only; keep it consistent with the migrated `config/schema.py`.

**E. North-star recipe — add the optimizer it currently omits:**

11. `GOAL.md` — the astronomy `schema.py` block currently ends `schema = strawberry.Schema(query=Query, config=strawberry_config())` with **no `extensions=`** (line ~163), preceded by a TODO at lines 155-162 that already spells the target. Replace the TODO + bare construction with `_optimizer = DjangoOptimizerExtension()` then `schema = strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])`, and add `DjangoOptimizerExtension` to the `from django_strawberry_framework import (...)` block at the top of the snippet (it currently imports `DjangoType, DjangoNodeField, DjangoConnection, DjangoConnectionField, apply_cascade_permissions, finalize_django_types, strawberry_config` — note several of those are not-yet-shipped aspirational symbols, so this is illustrative consumer code, not executed; matching that, just add the symbol to the import list). Remove the TODO scaffold comment.

**F. `TODAY.md` — bare class → singleton-factory:**

12. `TODAY.md` — line 109 `extensions=[DjangoOptimizerExtension],` (bare class) inside a snippet, preceded by a TODO at lines ~104 already spelling the target. Rewrite to the module-level singleton-factory form and remove the TODO scaffold.

**G. CHANGELOG bullet (under `[Unreleased]`, no version heading):**

13. `CHANGELOG.md` — under the existing `[Unreleased]` section (line 19), add a `### Changed` bullet (create the `### Changed` subheading under `[Unreleased]` if not present; today `[Unreleased]` holds only a TODO scaffold comment at lines 21-29). Canonical wording from Doc updates "Slice 1" / DoD item 4:
   > Migrated `extensions=[DjangoOptimizerExtension()]` to the module-level-singleton factory form (`extensions=[lambda: _optimizer]`): preserves the instance-bound plan cache and removes Strawberry 0.316.0's instance-form `DeprecationWarning`.

   Do NOT promote a `0.0.9` release heading (Decision 11 / build-plan version-bump-owner flag). The `[Unreleased]` TODO scaffold comment at lines 21-29 names Slices 1-3; leave the Slice 2 / Slice 3 lines of that scaffold in place (they are removed by their own slices) — or, if cleaner, convert only the Slice-1 line into the real bullet. (Discretion item 4.)

**H. Forbidden-form gate (verification, performed by Worker 2 at end of build / Worker 3 at review):**

14. After all rewrites, `rg 'extensions=\[DjangoOptimizerExtension\(\)\]|extensions=\[DjangoOptimizerExtension\]|extensions=\[ext\]|extensions=\[_CaptureExt\(\)\]|lambda: DjangoOptimizerExtension\(\)'` over active source + standing docs (i.e. excluding `docs/SPECS/`, `CHANGELOG.md` historical entries, and this spec's own quoted examples) must return **zero hits**. The broad `rg 'extensions=\['` audit confirms every construction site was visited. NB: the docstring at `tests/optimizer/test_extension.py:2881` contains the literal `extensions=[DjangoOptimizerExtension]` as prose — see Implementation discretion item 1 for its disposition.

### Test additions / updates

- **Regression guard (no new test, must keep passing):** the entire optimizer suite — `tests/optimizer/test_extension.py` (incl. every `cache_info()` / `_plan_cache` assertion), `tests/optimizer/test_relay_id_projection.py`, `tests/optimizer/test_field_meta.py`, `tests/test_list_field.py`, `tests/types/test_generic_foreign_key.py` — exercises the Plan cache through the now-`lambda`-wrapped shared instance and must pass unchanged. The migration is behavior-preserving (one shared instance per process via the closure, exactly as the bare instance was). Worker 3 may run focused tests from these files (no `--cov*` flags) to confirm the cache assertions still hold.
- **One new assertion (no-warning), package-internal.** Add a focused test (Worker 2's discretion on file placement: a new small test in `tests/optimizer/test_extension.py` is the natural home alongside the other extension-construction tests) that:
  - constructs ONE migrated schema (`_optimizer = DjangoOptimizerExtension(); strawberry.Schema(query=..., extensions=[lambda: _optimizer])`) inside `warnings.catch_warnings(record=True)` with `warnings.simplefilter("always")` set inside the context (so a previously-emitted-and-deduped `DeprecationWarning` cannot produce a false green), and
  - asserts no `DeprecationWarning` mentioning an extension instance is in the recorded list.
  - Assertion shape: filter recorded warnings to `DeprecationWarning` whose message mentions passing an extension instance; assert that filtered list is empty. Mirrors the deprecation-hygiene posture of `tests/test_scalars.py` (which runs a subprocess under `-W error::DeprecationWarning`).
  - This test pins DoD item 4's "the instance-form `DeprecationWarning` is gone."
- **Live HTTP:** `examples/fakeshop/test_query/test_multi_db.py` continues to exercise the migrated helper under `FAKESHOP_SHARDED=1`; no new live test for Slice 1.
- **Temp/scratch tests:** none needed. A throwaway "does the instance form warn under 0.316.0?" probe (to confirm the baseline the no-warning test guards) may be run ad hoc by Worker 2/3 under `docs/builder/temp-tests/slice-1/` and discarded; note any such file for Worker 3.

### Implementation discretion items

These are points Worker 1 has assessed and decided belong to Worker 2's discretion — equivalent-shape or local-naming choices, not architecture.

1. **The `test_extension.py:2881` docstring literal.** The string `strawberry.Schema(..., extensions=[DjangoOptimizerExtension])` appears inside the docstring of `test_extension_accepts_strawberry_execution_context_kwarg` as *prose explaining why the class form is instantiated with `execution_context=`*. It is NOT a construction site (it is a docstring, and the form it discusses — passing the class — is the legitimate Strawberry-internal behavior that test asserts). The forbidden-form grep in step 14 will flag it. **Decision: this docstring is active source and the spec's forbidden-form gate says only "this spec's quoted examples + historical prose" may survive — so reword the docstring** so it no longer contains the bare-class `extensions=[...]` literal (e.g. describe it as "Strawberry instantiates an extension *class* with `execution_context=...`" without the `extensions=[DjangoOptimizerExtension]` snippet, or escape it so the grep does not match). Worker 2 picks the exact rewording; the constraint is: the test's behavior and intent are unchanged, and the forbidden-form grep returns zero. (Flagged to Worker 3 to confirm the reword did not weaken the test's documented rationale.)
2. **Local instance variable naming when hoisting anonymous sites.** Where an anonymous `DjangoOptimizerExtension()` is hoisted to a local, the name (`ext`, `optimizer`, etc.) and exact placement (immediately before the `Schema(...)` call) are Worker 2's choice, provided the closure captures the intended instance and any existing same-function `ext` is not accidentally shadowed/reused incorrectly.
3. **`[Plan cache]` reference-link id in docs.** Whether to reuse an existing ref-id or add a new def under the `<!-- docs/ -->` group for the one-line rationale note is Worker 2's choice, subject to the START.md reference-style link convention (no inline `](path)` for cross-file links).
4. **CHANGELOG `[Unreleased]` scaffold handling.** Whether to convert only the Slice-1 line of the existing `[Unreleased]` TODO scaffold comment into the real `### Changed` bullet, or add the bullet alongside the (Slice 2/3) scaffold lines, is Worker 2's choice — the binding constraints are: a real `### Changed` bullet lands; no `0.0.9` release heading is promoted; the Slice 2 / Slice 3 anchors are not deleted by this slice.

**Static inspection helper (`scripts/review_inspect.py`): explicit skip.** Per BUILD.md "When to run the helper during build", Worker 1 must run it when the plan *adds logic* to an existing `.py` file ≥150 source lines, or to any file under the package `optimizer/` / `types/` directories. Slice 1 adds **no logic**: it rewrites existing `extensions=[<instance-or-class>]` call expressions to `extensions=[lambda: <instance>]` (a mechanical form change), removes TODO scaffold comments, adds one short no-warning test, and edits docs. The `.py` files touched live under `tests/optimizer/`, `tests/`, `tests/types/`, and `examples/fakeshop/` — none under the *package* `django_strawberry_framework/optimizer/` or `django_strawberry_framework/types/`. No package source `.py` file is modified by Slice 1. Helper run skipped; reason recorded here. (Worker 3's review rule keys on "adds 30+ lines of new logic to a package file" / "new `.py` file" / "touches package `optimizer/` or `types/`" — none apply; Worker 3 may likewise skip with reason.)

### Spec slice checklist (verbatim)

- [ ] Slice 1: migrate `extensions=` construction sites to the singleton-factory form (per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form))
  - [ ] Rewrite **every** instance-form `extensions=` entry — anonymous `[DjangoOptimizerExtension()]`, **named** (`ext = DjangoOptimizerExtension(); extensions=[ext]`), and the bare class `[DjangoOptimizerExtension]` — to a factory over a singleton **scoped to that construction site**: `extensions=[lambda: <instance>]`. This preserves the instance-bound [Plan cache][glossary-plan-cache] (same instance per request under 0.316.0's `get_extensions`) AND drops the `Schema.__init__` instance-form `DeprecationWarning`. Do NOT use the bare class or a constructing-`lambda` `lambda: DjangoOptimizerExtension()` (re-instantiated per request → cold cache, both modes, and a cache-hit-test failure).
  - [ ] Code sites — **per construction site, not per file** (per [Decision 3](#decision-3--slice-1-adopts-the-singleton-factory-extensions-form)); audit the whole set with `rg 'extensions=\[' <files>` (≈48 entries across the 5 package test files), wrapping **every** entry — anonymous, named `ext`, `strictness=`, bare class, and the two `_CaptureExt()` **subclass** instances in [`tests/optimizer/test_extension.py`][test-extension] (a `DjangoOptimizerExtension()`-literal grep misses these): in [`tests/optimizer/test_extension.py`][test-extension] (41) the cache tests keep their **function-local** `ext` and wrap it `extensions=[lambda: ext]` (a shared module-level instance would pollute per-test `cache_info()` counters); [`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection] (3) keeps each site's instance including the `strictness="raise"` one (one module-level instance cannot carry two strictness values); same per-site wrap for [`tests/optimizer/test_field_meta.py`][test-field-meta] (1) / [`tests/test_list_field.py`][test-list-field] (2) / [`tests/types/test_generic_foreign_key.py`][test-generic-fk] (1) / [`examples/fakeshop/test_query/test_multi_db.py`][fakeshop-test-multi-db] (1). The example schema [`examples/fakeshop/config/schema.py`][fakeshop-config-schema] (currently the bare class — a cold-cache regression under 0.316.0) and [`TODAY.md`][today] (class form) have one schema per module, so a module-level `_optimizer` is right there.
  - [ ] Consumer-doc snippets: rewrite the `extensions=[DjangoOptimizerExtension()]` schema-construction snippets in [`docs/README.md`][docs-readme] and [`docs/GLOSSARY.md`][glossary] to the module-level-singleton factory form (one schema per snippet), with a one-line "module-level singleton wrapped in a factory — preserves the instance-bound [Plan cache][glossary-plan-cache], no deprecation warning" note. Migrate the [`examples/fakeshop/test_query/README.md`][fakeshop-test-query-readme] prose snippet too (prose, not test-breaking, but kept consistent).
  - [ ] Bring the [`GOAL.md`][goal] astronomy schema into the sweep: it currently constructs `strawberry.Schema(query=Query, config=strawberry_config())` (the [`strawberry_config`][glossary-strawberry-config] scalar-map factory) with **no** `extensions=` at all, so the north-star recipe omits a foundation feature this Strawberry port adds over the old Graphene package — Slice 1 adds `DjangoOptimizerExtension` via the singleton-factory (`_optimizer = DjangoOptimizerExtension(); … extensions=[lambda: _optimizer]`) so the feature-complete example shows the optimized boundary the [`DjangoConnectionField`][glossary-djangoconnectionfield] / Relay cards inherit by default.
  - [ ] **Post-migration forbidden-form gate:** after the rewrite, a grep for the **exact forbidden forms** finds zero hits in active source/docs — `extensions=[DjangoOptimizerExtension()]`, `extensions=[DjangoOptimizerExtension]`, `extensions=[ext]`, `extensions=[_CaptureExt()]`, and `lambda: DjangoOptimizerExtension()`. (The broad `rg 'extensions=\['` audit finds construction *sites*; this forbidden-form grep catches the exact regressions Slice 1 removes.) The only surviving instance-form occurrences are this spec's own quoted examples and historical CHANGELOG / archived-spec prose.
  - [ ] [`CHANGELOG.md`][changelog]: append a `### Changed` bullet under `[Unreleased]` recording the migration to the singleton-factory `extensions=` form (preserves the plan cache, removes Strawberry's instance-form `DeprecationWarning`). No version-heading promotion (per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut)).

---

## Build report (Worker 2)

### Files touched

Package test files (function-local `lambda: <instance>` per construction site):
- `tests/optimizer/test_extension.py` — wrapped all 42 active construction sites: 22 named `extensions=[ext]` → `extensions=[lambda: ext]`; 17 anonymous `extensions=[DjangoOptimizerExtension()]` hoisted to a function-local `ext = DjangoOptimizerExtension()` + `extensions=[lambda: ext]`; 2 `_CaptureExt()` subclass sites hoisted to `capture_ext = _CaptureExt()` + `extensions=[lambda: capture_ext]`. Removed the module-top TODO scaffold (was lines 34-39). Reworded the `test_extension_accepts_strawberry_execution_context_kwarg` docstring (was line 2881) so it no longer contains the bare-class `extensions=[DjangoOptimizerExtension]` literal (discretion item 1) — intent unchanged. Added `import warnings` to the stdlib import block. Added the new no-warning test (see below).
- `tests/optimizer/test_relay_id_projection.py` — 3 sites hoisted to function-local `ext` (the `strictness="raise"` site keeps its kwarg) + `extensions=[lambda: ext]`. Removed the TODO scaffold (was lines 11-14).
- `tests/optimizer/test_field_meta.py` — 1 site (line 323) hoisted to function-local `ext` + `extensions=[lambda: ext]`. Removed the TODO scaffold (was lines 7-10).
- `tests/test_list_field.py` — 2 sites (758, 891) hoisted to function-local `ext` + `extensions=[lambda: ext]`. Removed the TODO scaffold (was lines 38-41).
- `tests/types/test_generic_foreign_key.py` — 1 site (107) hoisted to function-local `ext` + `extensions=[lambda: ext]`. Removed the TODO scaffold (was lines 10-13).

Example test (live HTTP) — function-local:
- `examples/fakeshop/test_query/test_multi_db.py` — the schema-building helper's site hoisted to a local `optimizer = DjangoOptimizerExtension()` + `extensions=[lambda: optimizer]`; per-call fresh-schema lifecycle preserved (the local is rebuilt each fixture call). Removed the TODO scaffold (was lines 29-32).

Example schema — module-level singleton (one schema per module):
- `examples/fakeshop/config/schema.py` — replaced the bare-class `extensions=[DjangoOptimizerExtension]` (a cold-cache regression under 0.316.0) and the TODO scaffold with a module-level `_optimizer = DjangoOptimizerExtension()` + `extensions=[lambda: _optimizer]`, plus a 4-line rationale comment. `config=strawberry_config()` kept.

Standing docs — module-level singleton form + rationale:
- `docs/README.md` — quick-start snippet → singleton-factory + one-line `[Plan cache][glossary-plan-cache]` rationale note (removed the TODO); recommended + wrong-order snippets → singleton-factory (removed the TODO); added `[glossary-plan-cache]: GLOSSARY.md#plan-cache` ref-def under `<!-- docs/ -->` (discretion item 3 — new ref-id, alphabetical).
- `docs/GLOSSARY.md` — `DjangoOptimizerExtension` entry snippet → singleton-factory + rationale note (the natural home), removed its TODO; `finalize_django_types` entry snippet → singleton-factory; `strawberry_config` entry multi-line snippet → singleton-factory; `BigInt scalar` inline-prose example → `extensions=[lambda: _optimizer]` with a pointer to the `DjangoOptimizerExtension` entry.
- `examples/fakeshop/test_query/README.md` — line-15 prose rewritten to the singleton-factory form (matches `config/schema.py`); removed the TODO scaffold.

North-star recipe + capability snapshot:
- `GOAL.md` — added `DjangoOptimizerExtension` to the snippet's `from django_strawberry_framework import (...)` block; replaced the bare `strawberry.Schema(query=Query, config=strawberry_config())` (no `extensions=`) + TODO with `_optimizer = DjangoOptimizerExtension()` + the multi-line singleton-factory construction.
- `TODAY.md` — bare-class snippet → module-level singleton-factory (removed TODO); reworded the trailing prose ("the optimizer is added as the `DjangoOptimizerExtension` class (Strawberry instantiates it)") to describe the singleton-factory form, which was stale after the migration.

Package source (NOT in the plan's audit — see Notes for Worker 1):
- `django_strawberry_framework/optimizer/extension.py` — the module docstring example (was line 5-8) and the class docstring example (was line 451-457, including the `# instance!` comment and "Pass an **instance** (not the bare class)" guidance) both contained the now-deprecated instance form. Rewrote both to the singleton-factory form and updated the guidance prose. Docstring-only, behavior-preserving. These two occurrences were caught by step-14's forbidden-form gate ("zero hits in active source") but were not listed in the plan's audit (steps 1-13). Flagged to Worker 1.

CHANGELOG:
- `CHANGELOG.md` — added a `### Changed` heading + bullet under `[Unreleased]` with the canonical Slice-1 wording; converted the Slice-1 line out of the `[Unreleased]` TODO scaffold and left the Slice 2/3 scaffold lines intact under a `TODO(spec-029 Slices 2-3)` comment (discretion item 4). No `0.0.9` release heading promoted.

### Tests added or updated

- `tests/optimizer/test_extension.py::test_singleton_factory_extensions_form_emits_no_deprecation_warning` — NEW. Constructs one migrated schema (`_optimizer = DjangoOptimizerExtension(); strawberry.Schema(query=Query, extensions=[lambda: _optimizer])`) inside `warnings.catch_warnings(record=True)` with `warnings.simplefilter("always")` set inside the context; asserts no recorded `DeprecationWarning` whose message mentions an extension instance. Pins DoD item 4 ("the instance-form `DeprecationWarning` is gone"). Filter keys on Strawberry 0.316.0's exact message ("Passing an extension instance to `extensions=[...]` is deprecated…" — verified in `.venv/.../strawberry/schema/schema.py` lines 270-280).
- Regression guard (no new test): every migrated `cache_info()` / `_plan_cache` / `strictness=` assertion still references the function-local instance the closure shares per request — confirmed passing (see Validation run).

### Validation run

- `uv run ruff format .` — pass ("231 files left unchanged"; my edits already matched formatter style). The `COM812`-formatter-conflict warning is pre-existing config noise, not introduced by this slice.
- `uv run ruff check --fix .` — pass ("All checks passed!"). No fixes applied.
- `uv run python scripts/check_trailing_commas.py --check` — exit 0 (trailing-comma layout intact across the hoisted multi-line constructions).
- `git status --short` after both ruff invocations:
  - 14 modified files — ALL slice-intended (the 14 listed in `### Files touched`; appear in this diff).
  - `D docs/builder/build-028-orders-0_0_8.md` — NOT my churn; this is Worker 0's pre-flight cleanup (recorded in the build plan preamble: "deleted `docs/builder/build-028-orders-0_0_8.md`"). Left as-is.
  - `?? docs/builder/bld-slice-1-extensions_singleton_factory.md`, `?? docs/builder/build-029-consumer_dx_cleanup-0_0_9.md` — NOT my churn; build-cycle scaffolding created by Worker 0/1. Left as-is.
  - No unrelated tool churn to revert.
- Focused tests run (no `--cov*`):
  - `pytest --no-cov tests/optimizer/test_extension.py::test_singleton_factory_extensions_form_emits_no_deprecation_warning` → 1 passed.
  - `pytest --no-cov` over `tests/optimizer/test_extension.py tests/test_list_field.py tests/optimizer/test_field_meta.py tests/optimizer/test_relay_id_projection.py` → 150 passed (confirms the `lambda:` wrap preserved per-test cache counters and the `strictness=` site).
  - `pytest --no-cov` over the GFK file + the relay no-lazy-load + the plan-cache-origin test → 6 passed.
- Forbidden-form grep (`extensions=[DjangoOptimizerExtension()]` / `[DjangoOptimizerExtension]` / `[ext]` / `[_CaptureExt()]` / `lambda: DjangoOptimizerExtension()`) over all git-tracked files excluding `docs/SPECS/`, `docs/spec-029-…`, `CHANGELOG.md`, `KANBAN.*`, `docs/builder/`: **ZERO HITS**. Package source (`django_strawberry_framework/`) re-checked separately: **ZERO HITS**. The only surviving instance-form literals are in `KANBAN.md` (the Slice-1 card body — Slice-4 owns), the spec's own quoted examples, `docs/SPECS/` archived specs, and `CHANGELOG.md` historical entries — all permitted by the gate.

### Implementation notes

- **Anonymous-site hoist name = `ext`.** Mirrors the named sites in the same files (discretion item 2); verified none of the 17 anonymous-site functions already define `ext` before the schema line, so no collision/shadowing. Placement is immediately before the `strawberry.Schema(...)` call (after `finalize_django_types()`).
- **`_CaptureExt()` hoist name = `capture_ext`** (distinct from `ext`) so the closure unambiguously captures the subclass instance.
- **`test_multi_db.py` local = `optimizer`** — followed the TODO scaffold's chosen name; the local is per-fixture-call so each schema build gets a fresh instance, matching prior behavior.
- **Bulk rewrite of `test_extension.py` was scripted** (a one-shot Python string-replace over the 42 uniform sites + scaffold removal + docstring reword), then verified by re-grep and a 150-test focused run. The remaining files were hand-edited (few sites, non-uniform indent).
- **No-warning test filter** keys on `issubclass(category, DeprecationWarning) and "instance" in str(message)` — narrow enough to ignore any unrelated `DeprecationWarning` but matches Strawberry's "extension instance" wording.
- **`docs/GLOSSARY.md` inline-prose `BigInt` example** uses `extensions=[lambda: _optimizer]` inline (can't show the two-line `_optimizer = …` definition inline) with a parenthetical pointer to the `DjangoOptimizerExtension` entry where the singleton is established — keeps the forbidden-form grep clean while staying readable.

### Notes for Worker 3

- No shadow file used (static-inspection helper skipped per the plan's recorded skip — Slice 1 adds no package logic; the one package-source file touched, `extension.py`, received docstring-only edits, no logic).
- Please confirm the `test_extension.py:~2890` docstring reword (discretion item 1) did not weaken the documented rationale of `test_extension_accepts_strawberry_execution_context_kwarg` — the test still asserts the class accepts `execution_context=None`; only the prose changed.
- The `extension.py` docstring edits are the one deviation from the plan's file list — see Notes for Worker 1; they are docstring-only and serve the forbidden-form gate.

### Notes for Worker 1 (spec reconciliation)

- **Plan-vs-implementation drift (small, mechanically obvious) — package-source docstrings.** The plan's audit (Implementation steps A–F) listed only the 5 package *test* files, the example schema/test, the docs, `GOAL.md`, and `TODAY.md` — it did NOT list `django_strawberry_framework/optimizer/extension.py`. But the plan's step-14 forbidden-form gate requires **zero hits in active source**, and `extension.py` carried two instance-form literals in docstrings (module docstring + class docstring, the latter with `# instance!` and "Pass an **instance** (not the bare class)" guidance that is now stale/deprecated). I rewrote both docstrings to the singleton-factory form (docstring-only, behavior-preserving) so the gate passes and the package's own documented guidance no longer recommends the deprecated form. This is within the slice's contract (modernize off the instance form everywhere it appears in active source) and small enough to judge from the diff. If Worker 1 prefers these docstrings stay out of Slice 1, the alternative is to defer them to a follow-up — but leaving deprecated-form guidance in the canonical class docstring while the rest of the repo migrates would be incoherent. Flagged for the spec/plan reconciliation decision.

---

## Review (Worker 3)

Reviewed Worker 2's working-tree diff (14 slice-intended files) against the spec (Slice 1 checklist lines 101-107, Decision 3 lines 327-357, DoD items 2-4, Doc updates "Slice 1") and the plan. The migration is a clean, behavior-preserving per-construction-site rewrite. No High or Medium findings. One Low note and one drift item escalated to Worker 1 (the only thing the diff cannot self-justify).

### High:

None.

### Low:

#### Late-binding closure over a re-assigned `ext` in `test_optimize_handles_empty_field_nodes`

`tests/optimizer/test_extension.py:651-655`. The hoisted `ext = DjangoOptimizerExtension()` (651) is captured by `extensions=[lambda: ext]` (652), then `ext` is immediately re-assigned to a fresh instance (655) used to drive `ext._optimize(...)` directly. Because the lambda is a late-binding closure over the function-local `ext`, the schema's extension factory would return the *second* instance — but this test never calls `schema.execute_sync()` (it only reads `schema._schema.type_map` and drives `_optimize` on the second `ext`), so the factory is never invoked and behavior is unchanged. The hoisted line at 651 is now effectively dead (the schema is built only for its type map). This mirrors the pre-existing shape (the original built `extensions=[DjangoOptimizerExtension()]` here purely for the type map), so the rewrite preserved intent. Not worth changing for Slice 1; noting for awareness. Confirmed passing in the focused run below.

### DRY findings

- No DRY defect. The repeated `extensions=[lambda: ext]` / `extensions=[lambda: _optimizer]` literal across sites is the intended, upstream-recommended per-site callable form, not an extractable duplicate: each `lambda` closes over a *different* per-site instance (function-local `ext` / `capture_ext` where a test asserts `cache_info()`, module-level `_optimizer` where there is one schema per module). Extracting a `make_optimizer_factory()` helper would obscure the per-site lifetime/strictness semantics Decision 3 deliberately keeps explicit and is correctly rejected by the plan's DRY analysis.
- Singleton-factory pattern applied consistently: function-local in all 5 package test files + the `test_multi_db.py` per-fixture helper (preserves per-test/per-call cache counters and the `strictness="raise"` site); module-level `_optimizer` in `config/schema.py`, the docs snippets, `GOAL.md`, and `TODAY.md` (one schema per module). The `strictness=` kwarg is preserved per-site (`test_relay_id_projection.py` keeps its `strictness="raise"` instance; the three `strictness=` sites in `test_extension.py` keep their function-local `ext`). The two `_CaptureExt()` subclass sites were hoisted to `capture_ext` and wrapped — exactly the sites a literal grep would miss.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty — `__all__` and the re-export list are unchanged. No new public exports. Consistent with the slice being a form-only migration (no new symbol). Authorized: the spec adds no public surface in Slice 1.

### CHANGELOG sanity

- The slice touches `CHANGELOG.md`. The new bullet is at line 22 under `## [Unreleased]` (line 19) → `### Changed` (line 21). NOT under a promoted release heading; the next heading down is the pre-existing `## [0.0.8] - 2026-06-03` (line 32). Correct per Decision 11 / the build-plan version-bump-owner flag.
- No version-line change: `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, and `uv.lock` are all clean (`git status --short` shows none modified). The build plan flags the deliberate `[Unreleased]` + unchanged version as expected, not drift — confirmed.
- Wording is character-for-character identical to the spec's canonical phrasing (Doc updates line 629 / DoD item 4), verified via `diff`. The `### Changed` heading is the spec-authorized one for Slice 1. Nothing over/understated — "preserves the instance-bound plan cache and removes Strawberry 0.316.0's instance-form `DeprecationWarning`" exactly matches the shipped behavior (verified by the temp probe below).
- The Slice 2/3 `TODO(spec-029 Slices 2-3)` scaffold comment was retained (discretion item 4) so the later slices' anchors survive; correct.

### Documentation / release sanity

- **`docs/README.md`** — quick-start, recommended, and wrong-order snippets all migrated to `_optimizer = DjangoOptimizerExtension()` + `extensions=[lambda: _optimizer]`; the wrong-order snippet keeps its ordering-bug point (only the `extensions=` form changed). The one-line rationale note uses reference-style `[Plan cache][glossary-plan-cache]`; the new ref-def `[glossary-plan-cache]: GLOSSARY.md#plan-cache` was added under the `<!-- docs/ -->` group, alphabetically between `[glossary-orderset]` and `[glossary-relay-node-integration]`, per the START.md link convention. The `#plan-cache` anchor resolves (`## Plan cache` exists at `docs/GLOSSARY.md:844`).
- **`docs/GLOSSARY.md`** — `DjangoOptimizerExtension` entry (the natural home, with the rationale note), `finalize_django_types` entry, and `strawberry_config` entry snippets all migrated; the `BigInt scalar` inline-prose example uses `extensions=[lambda: _optimizer]` with a parenthetical pointer to the `DjangoOptimizerExtension` entry. In-file `(#plan-cache)` / `(#djangooptimizerextension)` uses correctly stay inline (in-page anchors are exempt from reference-style per START.md). The entry's TODO scaffold was removed.
- **`examples/fakeshop/config/schema.py`** — bare class form (a 0.316.0 cold-cache regression) replaced with module-level `_optimizer` + `extensions=[lambda: _optimizer]` and a 4-line rationale comment; `config=strawberry_config()` kept.
- **`examples/fakeshop/test_query/README.md`** — line-15 prose rewritten to the singleton-factory form, now consistent with `config/schema.py` and the line-17 example; TODO scaffold removed.
- **`GOAL.md`** — astronomy schema gains `DjangoOptimizerExtension` (added to the illustrative `from django_strawberry_framework import (...)` block, fitting the existing `Django*` grouping) and the singleton-factory construction replaces the bare `strawberry.Schema(query=Query, config=strawberry_config())` (no `extensions=`). Aspirational snippet (several imported symbols are not-yet-shipped), so the import addition needs no executability — correct per discretion.
- **`TODAY.md`** — bare class snippet migrated; the trailing prose ("added as the `DjangoOptimizerExtension` class (Strawberry instantiates it)") was correctly rewritten to describe the singleton-factory form, which would otherwise be stale.
- No stale instance-form guidance remains in any slice-touched file (grep for `Pass an **instance**` / `# instance!` / "instantiates it" → zero). All `TODO(spec-029 Slice 1)` anchors removed (grep → zero outside the spec/archive/builder). The CHANGELOG `[0.0.8]` heading and version metadata are untouched.

### What looks solid

- The forbidden-form gate holds. My own `rg` over active Python + standing-doc markdown (excluding `docs/SPECS/`, `docs/spec-029-*`, `CHANGELOG.md`, `KANBAN.md`, `docs/builder/`) for `extensions=[DjangoOptimizerExtension()]` / `[DjangoOptimizerExtension]` / `[ext]` / `[_CaptureExt()]` / `lambda: DjangoOptimizerExtension()` returns **zero hits**. The only surviving instance/class-form literals are in `KANBAN.md` (the Slice-1 card body — Slice 4 owns its cleanup) and `docs/builder/` scaffolding — both permitted by the gate. `BACKLOG.md` has two *multi-line, multi-extension* aspirational snippets (`DjangoComplexityExtension`, `DjangoDoSExtension`) that the single-element forbidden-form grep does not match and that are out of the spec's migration scope and the slice's file list — correctly untouched.
- The new no-warning test is meaningful, not vacuous. A temp probe (below) confirmed under the locked Strawberry 0.316.0 that the instance form DOES emit an instance-mentioning `DeprecationWarning` (the baseline the test guards) while the singleton-factory form does NOT — so `test_singleton_factory_extensions_form_emits_no_deprecation_warning` would fail if the migration regressed. The `simplefilter("always")`-inside-the-context guard against dedup false-greens is present, and the filter (`issubclass(category, DeprecationWarning) and "instance" in str(message)`) is appropriately narrow.
- Behavior-preservation is real: cache-info / strictness regression tests pass with the function-local `ext` still shared per request through the closure (focused run below).
- Discretion item 1 (the `test_extension_accepts_strawberry_execution_context_kwarg` docstring reword) preserved the test's documented rationale — the prose still explains that Strawberry instantiates a *registered class* with `execution_context=...`, the test body (`DjangoOptimizerExtension(execution_context=None); assert ext.strictness == "off"`) is unchanged, and the forbidden-form literal is gone.

### Temp test verification

- `docs/builder/temp-tests/slice-1/test_warning_probe.py` (created during review) — two assertions: (a) the instance form `extensions=[DjangoOptimizerExtension()]` DOES emit an instance-form `DeprecationWarning` under 0.316.0, proving the new test's baseline is real; (b) the singleton-factory form does NOT warn. Both passed (`pytest --no-cov`, no coverage flags). **Disposition: deleted.** The behavior it proves is already pinned by the permanent `test_singleton_factory_extensions_form_emits_no_deprecation_warning`; the probe only existed to confirm that permanent test is not vacuously green, which it confirmed. No promotion needed.
- Focused regression run (`pytest --no-cov`, no coverage flags): `test_singleton_factory_extensions_form_emits_no_deprecation_warning`, `test_cache_hit_on_repeated_query`, `test_cache_differentiates_queries`, `test_cache_eviction_removes_old_entries`, `test_extension_accepts_strawberry_execution_context_kwarg`, `test_relay_id_does_not_trigger_lazy_load`, `test_optimize_handles_empty_field_nodes` → all 7 passed.

### Static helper

Ran `scripts/review_inspect.py django_strawberry_framework/optimizer/extension.py --output-dir docs/shadow --outline-only --stdout`. Rationale: the slice touches a package-source `.py` file under `optimizer/` (`extension.py`), which is a literal trigger for the Worker 3 "touches an existing `.py` file under `optimizer/`" rule, so I ran it rather than relying on the plan's skip (the plan's skip reasoning — "no package source `.py` file is modified" — was made before Worker 2's in-scope `extension.py` docstring edit). The overview confirms the change is docstring-only: every changed line falls inside the module docstring `::` block (lines ~3-8) and the class docstring `::` block (lines ~451-460); `git diff --function-context` shows no executable line touched; net +8/-4, all prose. The helper's control-flow hotspots and the single ORM marker (`line 585: QuerySet`) are all pre-existing logic, none in the changed regions. So the file is a genuine "no review-worthy logic" disposition — the helper run is on record and confirms no logic was introduced. For the 6 non-package test/example `.py` files and the docs, the plan's skip stands (no package logic, < the line thresholds, no new `.py` file) — they are mechanical call-expression rewrites.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: `django_strawberry_framework/optimizer/extension.py` docstring migration is in-scope for Slice 1, but the plan's audit (Implementation steps A-F) did not name it.** Worker 2 flagged this as plan-vs-implementation drift. My verdict: **touching `extension.py` was correct and in-scope, not over-reach.** Reasoning: (1) the change is strictly docstring-only (module + class docstring `::` blocks), behavior-preserving, verified by `git diff --function-context` and the static helper — it adds zero logic, so it does not change the slice's "form-only migration" character; (2) the spec's own forbidden-form gate (Slice 1 checklist line 106, DoD item 4) requires "zero hits in active source" for `extensions=[DjangoOptimizerExtension()]`, and `extension.py` carried exactly that literal in both docstrings plus stale `# instance!` / "Pass an **instance** (not the bare class)" guidance — leaving it would have *failed the gate* and left the package's own canonical class docstring recommending the deprecated form while the rest of the repo migrated, which is incoherent; (3) Decision 3 (lines 337-342) frames the migration as "every instance-form `extensions=[<instance>]` entry … everywhere it appears in active source," which the docstring example is. **Recommendation for Worker 1: accept the `extension.py` edit as a correct realization of the spec's forbidden-form-gate contract, and optionally add `django_strawberry_framework/optimizer/extension.py` to the spec's Slice-1 affected-files list / Doc updates so the audit and the implementation agree** (a one-line spec reconciliation under `### Spec changes made`). Either way the diff is correct as shipped; this is a spec/plan-text accuracy reconciliation, not a code change. Resolution paths: (a) accept silently as within the form-only contract; (b) add the file to the spec's Slice-1 file list for audit/implementation parity. I recommend (b) for the audit trail.
- The cross-slice deferral (`test_inspect_reads_resolved_annotation_not_field_null`) is a Slice 2/3 concern; nothing in Slice 1 touches it.

### Review outcome

`review-accepted`. No High or Medium findings. The single Low note (late-binding closure in a test that never executes the schema) is intentionally not blocking — behavior is unchanged and it mirrors the pre-existing shape. The one Medium-or-higher-class item (the `extension.py` plan-vs-audit drift) is **not a defect** — the edit is correct and in-scope — and is transparently escalated to Worker 1 above under an `Escalated:` prefix as a spec-text reconciliation (whether to add `extension.py` to the spec's Slice-1 file list), which needs spec context Worker 2/Worker 3 cannot decide unilaterally. Every spec Slice-1 sub-check is reflected in the diff; the forbidden-form gate, public-surface check, CHANGELOG sanity, and doc/release sanity all pass; the no-warning test is non-vacuous and the cache regression tests hold.

---

## Final verification (Worker 1)

Read the full artifact (Plan + Worker 2 build report + Worker 3 review incl. the `Escalated:` note), the working-tree diff for all 14 slice-intended files, the spec Slice-1 checklist / Decision 3 / Current state / Doc updates / DoD items 2-4, and my own memory file. Verified against the live working tree on 2026-06-05.

### Spec slice checklist

Walked each `- [ ]` in the Plan's `### Spec slice checklist (verbatim)` against the diff. **Every box landed (`- [x]`).** Verdict per box:

- **[x] Slice 1 parent — migrate `extensions=` to the singleton-factory form.** Landed end-to-end (sub-checks below).
- **[x] Rewrite every instance-form entry → `extensions=[lambda: <instance>]`.** 65 migrated `extensions=[lambda: …]` sites across active source/docs (`rg 'extensions=\[lambda:'`); the bare class / constructing-`lambda` forms are absent. Anonymous, named `ext`, `strictness=`, bare class, and the two `_CaptureExt()` subclass sites are all wrapped per the build report.
- **[x] Code sites — per construction site, not per file.** All 5 package test files (`test_extension.py` 42 sites incl. the two `_CaptureExt()`, `test_relay_id_projection.py` 3 incl. the `strictness="raise"` site, `test_field_meta.py` 1, `test_list_field.py` 2, `test_generic_foreign_key.py` 1) keep their function-local instance and wrap it; `test_multi_db.py` per-fixture local; `config/schema.py` + `TODAY.md` module-level `_optimizer` (one schema per module). Focused regression run (313 tests incl. every `cache_info()` / `_plan_cache` / `strictness=` assertion) passes — confirms the closure shares one instance per request exactly as the bare instance did.
- **[x] Consumer-doc snippets (`docs/README.md`, `docs/GLOSSARY.md`, `test_query/README.md`).** All migrated to the module-level-singleton factory form with the one-line plan-cache / no-warning rationale note; the `[glossary-plan-cache]` ref-def was added per the START.md link convention (verified by Worker 3).
- **[x] `GOAL.md` astronomy schema gains the optimizer.** `DjangoOptimizerExtension` added to the illustrative import block; the bare `strawberry.Schema(query=Query, config=strawberry_config())` (no `extensions=`) replaced with `_optimizer = DjangoOptimizerExtension()` + `extensions=[lambda: _optimizer]`.
- **[x] Post-migration forbidden-form gate — zero hits.** Re-ran the gate myself: `rg 'extensions=\[DjangoOptimizerExtension\(\)\]|extensions=\[DjangoOptimizerExtension\]|extensions=\[ext\]|extensions=\[_CaptureExt\(\)\]|lambda: DjangoOptimizerExtension\(\)'` over active source/docs (excluding `docs/SPECS/`, `docs/spec-029-*`, `CHANGELOG.md`, `KANBAN.*`, `docs/builder/`) → **ZERO HITS.** The three remaining `extensions=[` occurrences (`scalars.py:107`, `extension.py:489`, `test_extension.py:2906`) are all `extensions=[...]` prose/docstring placeholders, not construction sites or forbidden forms.
- **[x] `CHANGELOG.md` `### Changed` bullet under `[Unreleased]`.** Present at line 22 under `## [Unreleased]` → `### Changed`; wording matches the spec's canonical phrasing; no `0.0.9` release heading promoted; Slice 2/3 TODO scaffold retained.

No box is deferred and no box is silently un-ticked, so the slice is not `revision-needed` on checklist grounds.

### DRY check

No prior accepted slices exist (Slice 1 is the first). Intra-slice: confirmed Worker 3's DRY finding — the repeated `extensions=[lambda: ext]` / `extensions=[lambda: _optimizer]` literal is the intended per-site callable form, not an extractable duplicate (each `lambda` closes over a *different* per-site instance whose lifetime/strictness the spec deliberately keeps explicit — Decision 3). Extracting a `make_optimizer_factory()` helper is correctly rejected. No new duplication introduced.

### Existing tests still pass

- `uv run pytest tests/optimizer tests/test_list_field.py tests/types/test_generic_foreign_key.py -q --no-cov` → **313 passed** (focused scope: the optimizer suite is the behavior-preserving regression guard per the plan, plus the two directly-touched non-optimizer test files). `--no-cov` used because `pytest.ini` auto-applies `--cov`; no other coverage flag used; coverage not inspected.
- `uv run pytest tests/optimizer/test_extension.py::test_singleton_factory_extensions_form_emits_no_deprecation_warning --no-cov` → **1 passed** (the new no-warning assertion pinning DoD item 4).

### Build-wide context flags

- **No version-file edits.** `git diff --stat -- pyproject.toml django_strawberry_framework/__init__.py tests/base/test_init.py uv.lock` → empty. The `0.0.9` bump remains owned by the joint cut (Decision 11).
- **CHANGELOG bullet under `[Unreleased]`.** Confirmed above; the deliberate `[Unreleased]` + unchanged version is expected, not drift.
- **Out-of-scope working-tree entries.** `D docs/builder/build-028-orders-0_0_8.md` is Worker 0's recorded pre-flight cleanup; the two `?? docs/builder/*029*` files are this build's scaffolding. Neither is Slice-1 churn; left untouched.

### Spec reconciliation — escalated `extension.py` item: DECIDED, spec edited

Worker 3 escalated whether `django_strawberry_framework/optimizer/extension.py` (a package source file Worker 2 touched for docstring-only `extensions=` example migration, not named in the spec's Slice-1 file list) should be added to that list.

**Decision: edit the spec to record the file.** The spec is internally in tension: the Slice-1 forbidden-form gate (Slice-1 checklist line 106, DoD item 4 line 682) requires "zero hits **in active source/docs**" for the instance/class forms, and `extension.py` is active source carrying exactly those literals in its module + class docstrings — so the gate *mandated* the edit. But the Slice-1 affected-files enumeration (Current state line 149, Doc-updates table line 537) did not name the file, leaving the audit list and the gate contract disagreeing. I edited the Doc-updates Slice-1 row (line 537) to add the file (see `### Spec changes made` below) so the audit and the implementation agree.

This does **not** trigger a Worker 2 re-pass: the edit is a spec-text accuracy reconciliation only. I independently verified the `extension.py` change is strictly docstring-only (module docstring lines 2-8, class docstring lines 449-460; `git diff` shows no executable line touched, the stale `# instance!` / "Pass an **instance**" guidance correctly modernized) — it is behavior-preserving and does not alter the slice's "form-only migration" contract that Worker 2 implemented against. A docstring-list spec note is not a contract change.

### Summary

Slice 1 is a clean, behavior-preserving per-construction-site migration of every instance/class-form `extensions=[…]` entry to the singleton-factory form `extensions=[lambda: <instance>]` across the 5 package test files, the live-HTTP multi-db test, the example `config/schema.py`, the consumer docs (`README`/`GLOSSARY`/`test_query README`), `GOAL.md` (which gains the optimizer it previously omitted), and `TODAY.md`; plus a docstring-only modernization of the package's own `optimizer/extension.py` examples. The form preserves the instance-bound Plan cache (one shared instance per request under Strawberry 0.316.0's `get_extensions`) and drops the instance-form `DeprecationWarning`, pinned by one new non-vacuous no-warning test. A `### Changed` CHANGELOG bullet lands under `[Unreleased]` with no version bump. All 7 verbatim spec sub-checks landed; focused regression scope (313 + 1 tests) passes; no DRY defect; no version-file edits. Status set to `final-accepted`.

### Spec changes made (Worker 1 only)

- **`docs/spec-029-consumer_dx_cleanup-0_0_9.md` line 537 (Doc updates → Slice-1 "Files touched" row).** Slice that triggered: Slice 1 (this final-verification pass, resolving Worker 3's `Escalated:` item). Added `[`django_strawberry_framework/optimizer/extension.py`][optimizer-extension]` (with a "docstring-only — the module + class docstring `extensions=` examples carry the forbidden instance/class form the forbidden-form gate requires zero of in active source" qualifier) to the Slice-1 file list. **Reason:** the spec's forbidden-form gate (Slice-1 checklist line 106 / DoD item 4) requires zero instance/class-form hits in *active source*, which forced the docstring edit, but the Slice-1 file enumeration omitted the file — the edit makes the audit list and the gate contract agree. The `[optimizer-extension]` reference def already exists (line 788); no new link def added; `check_spec_glossary.py` re-run clean (41 terms, exit 0). No other spec edit; the status/header lines (1-5) already describe Slice 1 as the singleton-factory migration and no slice has shipped yet, so no header edit was needed.
