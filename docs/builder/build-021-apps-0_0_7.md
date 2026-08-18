# Package build plan: apps / 0.0.7 (021) — residual-completion cycle

Spec source: `docs/SPECS/spec-021-apps-0_0_7.md` (already archived; the card shipped in `0.0.7` on 2026-05-27)
Target release: `0.0.7` (shipped; the package is at `0.0.14`)
Build rule: one cohort at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every cohort must justify shared/duplicated patterns before merging.
Pre-flight: passed on 2026-08-18; baseline: two concurrent-session paths dirty (below); cleanup: **no artifact deletion performed** — see "Pre-flight exception".

## Cycle shape: this is a review round, not a fresh build

`docs/builder/BUILD.md` `## Review rounds` is the governing shape. The three spec slices shipped in `0.0.7`; their code is on `main`. The input to this cycle is **Worker 0's own verification of the spec against `HEAD`**, recorded verbatim under `## Verified findings` below, standing in for a maintainer review document. Two obligations the original cycle never discharged drive it:

1. `docs/builder/BUILD.md` `## Spec rationale extraction` — the pre-flight step-7 rationale MOVE never ran for this spec. `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` does not exist, and the spec still carries its whole deliberative layer.
2. `docs/builder/BUILD.md` `## Spec reconciliation` — the spec's Decision 4 was falsified inside its own release by a sibling card and was never reconciled.

The maintainer's standing instruction for this cycle, recorded here because it decides F1's resolution direction: **the spec states the current contract; how it got there goes in the rationale file.** No escalation is therefore open on F1.

### Pre-flight exception (step 3 deliberately not performed)

`docs/builder/BUILD.md` pre-flight step 3 resets prior-cycle `build-*.md` / `bld-*.md`. It was **not** run, for two reasons, and `worker-0.md` names artifact deletion "the one irreversible pre-flight mistake":

- A round's pre-flight explicitly skips the reset (`BUILD.md` `### Cohorting, naming, and closure`, "Pre-flight for a round").
- A concurrent session is actively moving prior-cycle artifacts: `docs/builder/build-020-list_field-0_0_7.md` is staged deleted with an untracked copy at `docs/builder/DONE/build-020-list_field-0_0_7.md`. `AGENTS.md` rule 34 forbids touching it.

Verified instead, as the round's pre-flight requires: none of this cycle's four artifact paths already exists.

### Baseline-dirty, out-of-scope (never edit, never revert — `AGENTS.md` rule 34)

- `docs/builder/build-020-list_field-0_0_7.md` (staged deleted by a concurrent session)
- `docs/builder/DONE/build-020-list_field-0_0_7.md` (untracked, concurrent session)
- `docs/builder/bld-003-final.md` (tracked leftover from the spec-003 residual cycle; not this cycle's)

### Concurrent-writable tracked binary / generated files

Churn in these is **not** presumed to be this cycle's output (`BUILD.md` `### Tracked binary / generated files`): `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`. R2 legitimately diverges all four; verify by two-consecutive-regenerate byte-stability, never by "`git diff` is clean". The maintainer runs parallel sessions against this same DB.

## Pre-flight record

| Step | Result |
|---|---|
| 1 working-tree baseline | Two concurrent paths dirty (above); nothing else. |
| 2 `scripts/review_inspect.py` | Not run — no cohort adds or edits package `.py`. `BUILD.md` `### When to run the helper` scopes it to source logic; recorded skip. |
| 3 artifact reset | Deliberately skipped; see exception above. Confirmed the four new paths are free. |
| 4 `.gitignore` scratch paths | `docs/shadow/`, `docs/builder/worker-memory/`, `docs/builder/temp-tests/` all listed. |
| 5 scratch cleared | All three empty; the four worker-memory files exist and are 0 bytes. |
| 6 `check_spec_glossary` | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-021-apps-0_0_7.md` → `OK: 12 terms`, exit 0. |
| 7 rationale extracted | **NOT DONE — it is this cycle's R1.** |

## Verified findings

Worker 0 read the current source behind every finding before writing this plan (`BUILD.md` `### Worker 0 verifies every finding against source before dispatching`). Each carries whether the condition holds at `HEAD` and the symbol-qualified evidence.

**Three counts in the first writing of this section were wrong** — R1 measured them and Worker 0 re-derived each with the command now cited inline (test functions 7 → **8**; `Justification:` blocks 7 → **8**; `Alternatives considered` lists 6 → **7**). None changed a finding's direction. Recorded rather than silently patched, because `BUILD.md` `## Claims are proven mechanically, never accepted on prose` is explicit that a count asserted in the same breath as the lesson it illustrates is routinely wrong: every one of these was read off the file instead of measured against it.

### F1 — HOLDS. Decision 4 ("No `ready()` hook in `0.0.7`") is falsified by the shipped code

- **Spec claim:** `### Decision 4 — No ready() hook in 0.0.7` — "`DjangoStrawberryFrameworkConfig.__dict__` MUST NOT contain a `ready` key." Propagated to the Slice 1 checklist "Do NOT implement `ready()`", the Slice 2 negative-shape sub-bullet, `## Test plan`, `## Edge cases and constraints` ("Because this card defines no `ready()`…"), `## Risks and open questions` ("Future-card `ready()` body adoption"), `## Goals` item 3, `## Non-goals` item 1, `## Borrowing posture` ("No `ready()`"), and Definition of done items 1 and 6.
- **`HEAD`:** `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` exists and dispatches three appliers — `_django_patches.apply()`, `_strawberry_patches.apply()`, `_cross_web_patches.apply()` — all gated by the `APPLY_UPSTREAM_PATCHES` setting (`django_strawberry_framework/conf.py #"APPLY_UPSTREAM_PATCHES_KEY"`).
- **Provenance:** `300e2811` "Ship Django Trac #37064 fix as package-level AppConfig.ready() patch" — sibling card `DONE-024-0.0.7`, the **same `0.0.7` release**; hardened by `7014125a`; broadened to the Strawberry and `cross_web` appliers by `c7cb5f5c`; dispatch pinned by `136c5476`.
- **Not a code defect.** The later contract is the correct one. Resolution: R1 rewrites the spec to state it directly, with the chronology in the rationale file.

### F2 — HOLDS. The pinned test surface is stale (5 tests / four forbidden keys)

- **Spec claim:** `## Implementation plan` table and Definition of done item 4 say **5** tests; `## Test plan` and the Slice 2 checklist pin the forbidden-key set as `{"ready", "label", "default_auto_field", "default"}`.
- **`HEAD` `tests/test_apps.py`:** **8** test functions (`grep -c '^def test_' tests/test_apps.py` → 8; Worker 0's first statement said 7, from reading rather than measuring — R1 caught it and Worker 0 re-derived). The forbidden set is three keys — `label`, `default_auto_field`, `default`; `"ready"` was removed with an in-file comment naming the supersession. Three tests exist that the spec does not describe: `tests/test_apps.py::test_djangostrawberryframeworkconfig_defines_ready_for_django_patches`, `::test_ready_dispatches_all_three_patch_appliers_and_refires_safely`, `::test_ready_reinstalls_patches_after_their_modules_reload`.
- Consequence of F1; same resolution.

### F3 — HOLDS. Spec status line says `draft`

`Status: draft (revision 6, post-rev5 build-readiness audit).` on a card that shipped in `0.0.7` and whose spec is archived under `docs/SPECS/`.

### F4 — HOLDS. Renumber residue in the spec's own references

- `docs/SPECS/spec-021-apps-0_0_7.md` link definition `[spec-016]: spec-020-list_field-0_0_7.md` — the ref-id names the pre-renumber number while its target is the post-renumber filename; the body then reads "[`spec-016`][spec-016] Decision 10" in six places while the `Predecessors:` line names `spec-020`.
- `## Risks and open questions` "Last-card-to-ship version bump policy" names "the four remaining `0.0.7` WIP cards (017, 018, 019, 045)" — pre-renumber ids, while `### Decision 6` in the same spec names the post-renumber `DONE-022/023/025`.

### F5 — HOLDS. `docs/GLOSSARY.md` `## Django AppConfig` under-describes the shipped `ready()`

The entry says the `ready()` body "imports `django_strawberry_framework._django_patches` and calls `apply()`" — one of the **three** appliers `ready()` actually dispatches. No other glossary entry covers the Strawberry / `cross_web` dispatch. **DB-backed** (`GlossaryTerm.body`); fix is an ORM edit + regenerate, never a hand-edit.

### F6 — HOLDS. `KANBAN.md` card `DONE-021-0.0.7` `#### Note` is false for the shipped `0.0.7`

Reads "tiny `AppConfig` (two class attributes, no `ready()` body in 0.0.7) + tests". The `ready()` body shipped **in `0.0.7`** (F1's provenance), and `CHANGELOG.md`'s own `[0.0.7]` entry for this card already says so. **DB-backed** (`CardItem.text`).

### F7 — HOLDS. The rationale file does not exist

`docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` is absent while all 25 sibling specs have one. The spec still carries a 23-bullet inline `Revision history`, a `Justification:` block under **all eight** Decisions, an `Alternatives considered (and rejected):` list under **seven** (Decision 5 has none), a four-item `## Risks and open questions`, and **53** `(revN Xn)` attribution parentheticals through the checklist, decisions, edge cases, test plan, doc updates and DoD.

### F8 — HOLDS. `tests/test_apps.py` carries a stale, renumbered, self-narrating provenance comment

Surfaced by R1's Worker 3 pass, verified by Worker 0 against source. `tests/test_apps.py #"no ready() body in"` reads `# modules' ``apply()`` calls. The spec-017 "no ready() body in 0.0.7" stance is deliberately superseded by …`. Three defects in one comment:

- **Wrong spec.** `spec-017` is this card's **pre-renumber** number. Post-renumber `docs/SPECS/spec-017-deferred_scalars-0_0_6.md` is an unrelated `0.0.6` spec, so the pointer now resolves to the wrong document. This card is `spec-021`.
- **Falsified referent.** After R1, `docs/SPECS/spec-021-apps-0_0_7.md` no longer carries a "no `ready()` body" stance at all, so the comment describes a document that no longer says it.
- **Process provenance in code.** `AGENTS.md` and this repo's standing rule: a comment states the **invariant**, never how the change came to be. A spec Decision *pointer* is on the keep list; a narration of what a spec used to say and what superseded it is not.

Dispatched to R2 (the only cohort with a Worker 2). Comment text only — no assertion, no test body, no package source.

### F9 — DOES NOT HOLD. `CHANGELOG.md`'s `[0.0.7]` entry naming one applier is correct as history

R1 deferred this as a defect ("the `[0.0.7]` entry still says `ready()` calls **one** applier where three ship"). Worker 0 verified it before letting it reach a builder, and **it is not a defect** — it is the release-boundary rule doing its job:

**Read releases off the TAGS, never off `pyproject.toml` at the work commit.** `pyproject.toml` at a work commit still holds the **previous** release's number, because the bump lands at the cut. Worker 0's first writing of this table annotated that trap correctly on the `300e2811` row and then fell into it on the `c7cb5f5c` row one line down; R2's Worker 3 caught it. The version column below is therefore the **shipping tag**, derived from tag content:

| commit | subject | shipped in | evidence |
|---|---|---|---|
| `300e2811` | Ship Django Trac #37064 fix as package-level `AppConfig.ready()` patch | **`0.0.7`** | `git show 0.0.7:django_strawberry_framework/apps.py` carries `ready()` with the single `_django_patches` applier (`pyproject.toml` at the commit reads `0.0.6`) |
| `c7cb5f5c` | Patch upstream non-UTF-8 request-body 500 in Strawberry and `cross_web` | **`0.0.11`** | `git show 0.0.10:…/apps.py` → one applier; `git show 0.0.11:…/apps.py` → three (`apply_django` / `apply_strawberry` / `apply_cross_web`). `pyproject.toml` at the commit reads `0.0.10` |
| `136c5476` | apps: pin `ready()` patch dispatch with a package test | `0.0.14` | `pyproject.toml` at the commit reads `0.0.13` |

So the `0.0.7` release tag **does** carry the `ready()` body, with the single Django applier and no other; the Strawberry and `cross_web` appliers arrived at `0.0.11`. `CHANGELOG.md`'s `[0.0.7]` entry therefore describes `0.0.7` accurately, and "correcting" it would falsify the changelog. `AGENTS.md` rule 21 would have forbidden the edit anyway; this is the independent reason.

**Do not verify this with `git merge-base --is-ancestor`.** Worker 0 tried it and got `NO` for `c7cb5f5c` against *both* the `0.0.10` and `0.0.11` tags — concurrent sessions rewrite this branch's history, so a commit hash from `git log` need not be an ancestor of the tag whose content it is plainly in. Tag **content** is the reliable instrument here; ancestry is not.

**Dropped from R2's scope. No builder is dispatched at it.** Recorded rather than quietly discarded, per `BUILD.md` `### Worker 0 verifies every finding against source before dispatching` — a finding that does not hold still says the round's model of the code was off somewhere.

This is also the discriminator that makes **F5 and F6 real**: `docs/GLOSSARY.md` describes the package's **current** state, so naming one applier where three dispatch is stale; and `KANBAN.md`'s card note claims "no `ready()` body in `0.0.7`" where the `0.0.7` tag itself contains one.

### Findings that do NOT hold — nothing was skipped in the code

Reported rather than dropped, per `BUILD.md`. Every remaining Definition-of-done item holds at `HEAD`:

- DoD 1 — `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig` carries `name = "django_strawberry_framework"`, `verbose_name = "Django Strawberry Framework"`, a module docstring, a class docstring, and no `label` / `default_auto_field` / `default`. Only the `ready()` clause is superseded (F1).
- DoD 2, 3, 12 — `grep` over `django_strawberry_framework/__init__.py` finds no `apps` / `AppConfig` / `DjangoStrawberryFrameworkConfig` reference; `__all__` is unwidened; zero new public exports.
- DoD 5 — `examples/fakeshop/config/settings.py` still declares the bare `"django_strawberry_framework"` entry (line 71).
- DoD 7 — the live `/graphql/` suite runs against the explicit AppConfig unchanged.
- DoD 9 (partly) — `docs/GLOSSARY.md` index row reads `shipped (0.0.7)`; `docs/README.md` carries the AppConfig bullet; the `Coming in 0.1.0` section is gone entirely (later cards); `docs/TREE.md` lists `apps.py` and `tests/test_apps.py` in the current layouts with `ready()`-aware descriptions; `CHANGELOG.md` `[0.0.7] ### Added` carries the entry. Only the two DB-backed bodies drift (F5, F6).
- DoD 10 — `KANBAN.md` carries `DONE-021-0.0.7` in Done with its spec link. Only the `#### Note` text drifts (F6).
- DoD 11 — the version bump is not in this card's diff.

**Conclusion: no code was skipped, dropped, or deviated. No cohort in this cycle writes package source or tests.**

## Declarations

- **Ownership partition** — two cohorts, dispatched **sequentially** (R2's glossary body must describe the contract R1 reconciles):
  - **R1** — `docs/SPECS/spec-021-apps-0_0_7.md`, `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md`, `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md`.
  - **R2** — `examples/fakeshop/db.sqlite3`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `tests/test_apps.py`, `docs/builder/bld-review-2-db_backed_doc_reconciliation.md`.
  - No file appears in both. No cohort writes `django_strawberry_framework/` or `examples/fakeshop/apps/`.

  **`tests/test_apps.py` was folded into R2 after R1's review** (`BUILD.md` `### Parallel cohorts under a declared ownership partition`, "If a collision surfaces mid-flight … Worker 0 … records the correction in the plan"). R1's Worker 3 pass surfaced F8 below, a one-line stale provenance reference inside this card's own test file. Only Worker 2 may write a test file, and R2 is the only cohort with a Worker 2. The plan's "no cohort writes source or tests" statement is superseded for this one comment line; no assertion, no test body, and no package source changes anywhere in this cycle.
- **Hot-path declaration** — none. No cohort touches executable package code.
- **Floor-verification scope** — none. No cohort touches a Django / Strawberry / channels integration seam (`BUILD.md` `### When it is required`).

### R1's worker sequence is Worker 1 → Worker 3 → Worker 1, with no Worker 2

Declared explicitly because it departs from `## Spec-per-cycle dispatch`'s default, and the departure is **forced by the role contracts**, not a convenience:

- `BUILD.md` `## Spec reconciliation` — only Worker 1 may mutate the spec.
- The Required-reading matrix — Worker 2 **never** reads the rationale file, and the rationale move is its authorship.

So R1's build phase is Worker 1's by definition. `### Isolation is non-waivable` is preserved intact: the agent that writes R1 is not the agent that reviews it — Worker 3 reviews, and a **fresh** Worker 1 invocation performs final verification. R2 runs the ordinary Worker 1 → 2 → 3 → 1 chain.

## Artifact list

- `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md`
- `docs/builder/bld-review-2-db_backed_doc_reconciliation.md`
- `docs/builder/bld-integration.md`
- `docs/builder/bld-final.md`

## Checklist

- [x] R1: Rationale extraction + spec reconciliation (F1-F4, F7) -> `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md`
- [x] R2: DB-backed doc reconciliation + stale test-comment provenance (F5, F6, F8) -> `docs/builder/bld-review-2-db_backed_doc_reconciliation.md`
- [x] Cross-cohort integration pass -> `docs/builder/bld-integration.md`
- [x] Final test-run gate -> `docs/builder/bld-final.md`

**Cycle closed. Worker 0 hands off to the maintainer for review and commit** (`BUILD.md` `## Slice handoff`). Closeout does not begin until the maintainer has committed and supplied the commit range.

Worker 0 independently re-derived the gate's one baseline exception before ticking this box: `tests/utils/test_write_values.py::test_form_and_serializer_decode_walks_share_field_handlers` fails against `django_strawberry_framework/mutations/resolvers.py`, and **both files were already dirty at this cycle's session-start baseline** — neither is in this cycle's file set, and this cycle wrote no package source at all. This cycle's only `.py` diff is `tests/test_apps.py` (`git diff --stat` → 1 file, 6 insertions / 7 deletions, one comment hunk), which runs 8 passed. The failure is a concurrent session's in-flight refactor; `AGENTS.md` rule 34 forbids touching it.

The maintainer paused the cycle after R2 reached `final-accepted` and resumed it at the integration pass. Nothing was mid-flight across the pause: both cohorts were closed, no failability mutation was live in the tree, and no artifact sat in a non-terminal `Status:`.

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
