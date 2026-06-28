# Build: Slice 0 — Pre-Slice-1 dependency gate (F11): verify + pin the DRF floor, wire the soft dev dependency

Spec reference: `docs/spec-039-serializer_mutations-0_0_13.md` (Slice checklist Slice 0: lines 597-623; governing sections: Decision 12 lines 2475-2591, Decision 14 lines 2654-2685, Doc updates "Pre-Slice-1 gate" bullet lines 3312-3320, Risks "DRF version floor" lines 3414-3443, Definition of done items 7-8 lines 3635-3677)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - The **dev-group soft-dependency floor shape** is already established by `pillow>=10.0.0` and `faker>=33.0.0` in `pyproject.toml` `[dependency-groups].dev` (lines 41-54). The spec's Decision 12 (lines 2535-2537, 2577-2580) names the `spec-037` `pillow` precedent explicitly: a soft runtime dep kept OUT of `[project].dependencies`, added to the dev group so the suite covers the otherwise-uncovered path under `fail_under = 100`. Slice 0 adds one more dev-group row in that exact form; no new pattern.
  - The **targeted `ignore::` convention** is already documented in `pytest.ini` (lines 16-21): `filterwarnings = error` with an explicit comment sanctioning "targeted `ignore::` lines below ONLY for warnings originating in third-party packages we cannot fix; never blanket-ignore." Slice 0 reuses that exact comment-anchored convention if (and only if) the verified DRF release still emits a residual warning under the matrix.
  - The **staged `TODO(spec-039 Slice 0)` anchor** already sits in `pyproject.toml` at the dev-group site (lines 44-47). Worker 2 replaces that anchor with the real `djangorestframework` row in the same change that lands the row (AGENTS.md "staged-but-not-implemented slices get a source-site TODO comment … removed in the same change that ships the slice"). This is the discharge site — no new anchor is created.
  - The `[[package]] name = "django-strawberry-framework"` block in `uv.lock` (lines 216-258) already carries a `[package.dev-dependencies] dev` list (lines 228-238) and a `[package.metadata.requires-dev] dev` list (lines 248-258). `uv lock` after the manifest edit appends the `djangorestframework` entry to both in the established alphabetical-ish ordering and adds DRF's own `[[package]]` stanza; this is mechanical lock regen, not hand-authoring.
- **New helpers justified.** **None for the shipped package.** Slice 0 introduces no `django_strawberry_framework/` code — the `require_drf()` guard and its single install-hint string are authored in **Slice 2** (the stub `django_strawberry_framework/rest_framework/__init__.py` already carries a `TODO(spec-039 Slice 2)` anchor naming exactly that work; verified lines 3-20). The only candidate "new file" is the optional `scripts/check_drf_floor.py` probe — and the plan recommends NOT shipping it (see "Floor-check form" below); the floor is verified by a documented `uv` command sweep recorded in this artifact + the PR description instead, so no script is added.
- **Duplication risk avoided.** The floor number (`djangorestframework>=<floor>`) must live in **three places that must agree** (spec lines 612-617, 3435-3436): (1) the `[dependency-groups].dev` pin in `pyproject.toml`, (2) the `require_drf()` guard's install hint, and (3) a one-line note in the spec's `## Risks and open questions`. **Slice 0 owns only (1) and (3); (2) is authored in Slice 2.** The duplication risk is a drifted floor across these sites; the plan prevents it by recording the exact pinned floor in this artifact and in the spec Risks note now, and flagging the cross-slice obligation (below) so Slice 2's hint cannot diverge. No other site may restate the floor.

### Recommended floor and its justification

**Recommended pinned floor: `djangorestframework>=3.17.0`.**

The spec's binding constraint is explicit (Risks lines 3414-3443, Decision 12 lines 2547-2555): the floor is gated NOT by serializer-API availability but by a **matrix-wide warning-free import under `pytest.ini`'s `filterwarnings = error`**, across the `.github/workflows/django.yml` matrix (verified lines 50-71: Django 5.2.0 → 5.2.\* → 6.0.\* → `latest` on Python 3.10 → 3.14). The decisive cell is **(Django 6.0 / `latest`, Python 3.14)** — DRF's Django support lags Django, so a 6.0-clean release had to be confirmed to exist before pinning.

Verified at plan time (2026-06-27, web sources below):
- **DRF 3.17.0** (released 2026-03-18) is the **first** release to "Add Django 6.0 support" AND "Add support for Python 3.14" (DRF release notes). It also drops Python 3.9 and the deprecated `coreapi` support, so the floor is clean of those removed paths.
- **DRF 3.17.1** (released 2026-03-24) is the latest patch — a single `HTMLFormRenderer` empty-datetime bugfix, no matrix-relevant change.
- Releases ≤ 3.16.x (3.16.1, 2025-08-06) predate Django 6.0 support and would fail the 6.0/`latest` matrix cells at import/`-W error` time.

So `>=3.17.0` is the lowest release that clears the binding matrix constraint, matching the house convention of pinning the **lowest supporting version** (cf. `pillow>=10.0.0`, `Django>=5.2`) rather than the latest patch. Worker 2 MUST still *prove* (not assume) the matrix-wide warning-free import at the gate via the command sweep below and record the result; if that sweep surfaces a residual DRF-origin warning under any cell, Worker 2 adds the single targeted `ignore::` line to `pytest.ini` (never blanket) and records which warning + which cell drove it. If the sweep shows no compatible release clears 6.0/`latest`/3.14, the card **blocks at the gate** (spec lines 616-617, 3442-3443) — escalate to Worker 0 / maintainer rather than proceeding to Slice 1.

Environment note (verified): the project venv currently has **no `rest_framework` installed** (`ModuleNotFoundError`) and runs **Python 3.14.2**, so this gate is genuinely net-new wiring and the local sweep cell for (Python 3.14) runs against the dev env once DRF is synced.

### Floor-check form — recommendation: option (b), documented `uv` command sweep (NOT a shipped probe script)

The spec offers two acceptance-artifact forms (lines 605-617): **(a)** ship `scripts/check_drf_floor.py` that imports `rest_framework` under `-W error` and asserts installed version `>=` floor, runnable per matrix node; or **(b)** a documented sequence of explicit `uv` commands across the Python × Django cells recorded in the Slice 0 PR description.

**Recommend (b).** Rationale:
- The binding property is **matrix-wide** warning-free import — a property the spec itself says "the suite cannot prove … from inside one interpreter" (lines 605-607). Option (a)'s probe, run in the normal `pytest` env, proves only the *single* installed-node case; it becomes a matrix-wide proof **only if it is actually invoked on every matrix node**, which requires adding a CI step to `django.yml`. That CI edit is **outside Slice 0's declared file scope** (`pyproject.toml` + `uv.lock` + `pytest.ini` per the Doc-updates bullet, lines 3312-3320) and would expand the gate.
- A shipped `scripts/check_drf_floor.py` is itself package surface that must stay `ruff`-clean and warning-clean forever, and (if it ever runs under the suite) is subject to the `fail_under = 100` gate — added maintenance cost for a one-time gate check.
- Option (b) directly proves the binding constraint as a one-time acceptance act: `uv run --python <py> --with 'django==<ver>' python -W error -c "import rest_framework"` across the decisive cells, with the transcript recorded in this artifact's build report and the PR description. It needs no new shipped file and no CI plumbing.

Concrete sweep Worker 2 should run and record (decisive cells first; full matrix in the PR):
- `(3.14, Django 6.0/latest)` — the binding cell: `uv run --python 3.14 --with 'djangorestframework>=3.17.0' --with 'Django>=6.0' python -W error -c "import rest_framework; print(rest_framework.VERSION)"`
- `(3.10, Django 5.2.0)` — the floor cell: `uv run --python 3.10 --with 'djangorestframework>=3.17.0' --with 'Django==5.2.0' python -W error -c "import rest_framework; print(rest_framework.VERSION)"`
- intermediate cells (3.11/3.12/3.13 × 5.2.\*/6.0.\*) as the PR matrix record.
- Plus, in the synced dev env, the running-warning-free check beyond bare import is earned by the Slice 1-3 suite under `pytest.ini`'s `filterwarnings = error` (that is the "run warning-free", not just "import warning-free", half).

Worker 2 has genuine discretion to ALSO add option (a)'s script as a belt-and-suspenders supplement IF the maintainer later wants a per-node CI probe — but it is NOT required by this plan and is NOT sufficient alone; if added, it must be warning-clean and the floor constant in it must read from / agree with the `pyproject.toml` pin, never restate a fourth independent copy. Default: do not ship it.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against current source before editing.

1. **`pyproject.toml` — add the dev-group DRF row, removing the staged anchor.** In `[dependency-groups].dev` (lines 41-54), replace the four-line `TODO(spec-039 Slice 0)` comment block (lines 44-47) with a single `"djangorestframework>=3.17.0",` row, placed in the existing dev list. Keep it in `[dependency-groups].dev` ONLY — it must NOT be added to `[project].dependencies` (lines 28-33). Honor the trailing-comma layout (`scripts/check_trailing_commas.py`: the dev list is already multi-line one-item-per-line). **No edit to `[project].version` (line 4, stays `0.0.12`).**
2. **`uv.lock` — regenerate to match.** Run `uv lock` (NOT `uv lock --upgrade`) so it adds only the `djangorestframework` entry (and DRF's transitive deps, if any) to the `[package.dev-dependencies] dev` (lines 228-238) and `[package.metadata.requires-dev] dev` (lines 248-258) lists plus a new `[[package]] name = "djangorestframework"` stanza, while leaving the `django-strawberry-framework` package's own `version = "0.0.12"` entry (line 218) untouched. Verify post-regen: `grep -n 'version = "0.0.12"' uv.lock` still shows the package line unchanged, and `grep -n djangorestframework uv.lock` now resolves. If `uv lock` rewrites unrelated locked versions (a drifting transitive bump), that is out of Slice 0's scope — flag it; do not hand-edit the lock to suppress it.
3. **`pytest.ini` — add a targeted DRF-origin `ignore::` ONLY if the verified release needs one.** Under the `filterwarnings = error` block (lines 20-21), append a single targeted `ignore::<WarningClass>:<module-regex>` line beneath the existing third-party-ignore comment (lines 16-19) IF and ONLY IF the command sweep / a dev-env `pytest` run surfaces a residual DRF-origin warning the floor still emits under the matrix. **Default expectation: none is needed** (3.17.0 explicitly added 6.0 + 3.14 support and dropped the deprecated paths). If one is needed, it must name the exact warning class + the `rest_framework` module origin (never a blanket `ignore::DeprecationWarning`), and the build report must record which cell drove it. Do not add a speculative ignore.
4. **Spec `## Risks and open questions` — record the exact pinned floor (Worker 1, spec-custody edit).** The "DRF version floor" item (lines 3414-3443) currently describes the verification procedure but does not state the chosen number. As the spec custodian, Worker 1 (this planning pass OR final verification) appends a one-line note pinning `djangorestframework>=3.17.0` (first release with Django 6.0 + Python 3.14 support; 3.17.0 released 2026-03-18) as the third of the three-places-that-must-agree. **NOTE:** per `worker-1.md` Scope, Worker 1 edits the spec only when the build proves it needs it; this floor record is mandated by the spec's own Slice 0 contract (lines 612-616: "recorded in three places that must agree … a one-line note in Risks"), so it is an in-contract spec edit, recorded under `### Spec changes made (Worker 1 only)`. **Defer the actual spec edit to final verification** (after Worker 2's sweep confirms 3.17.0 clears the matrix), so the recorded number reflects a proven floor, not a planning-time prediction. If Worker 2's sweep forces a higher floor, the Risks note records that proven number instead.

### Cross-slice dependency to flag (do not implement in Slice 0)

- **The three-places-that-must-agree floor spans Slice 0 and Slice 2.** Slice 0 owns place (1) `pyproject.toml` pin and place (3) spec Risks note. Place (2) — the `require_drf()` guard's **install hint** — is authored in **Slice 2** (`django_strawberry_framework/rest_framework/__init__.py`; the stub's `TODO(spec-039 Slice 2)` anchor names it, verified). **Slice 2's install hint must name the SAME floor (`djangorestframework>=3.17.0`) Slice 0 pins.** Worker 0 must carry this constraint into the Slice 2 dispatch; Worker 1's Slice 2 planning pass must cite this artifact's recorded floor so the hint cannot drift. Slice 0 must NOT author `require_drf()` or any install-hint string.

### Test additions / updates

- **No package tests in Slice 0.** Decision 12 (lines 2556-2571) places the DRF-absent import-guard test in **Slice 2** (it asserts the install-hint message on all three raising entry points and is gated on `require_drf()` existing). Slice 0 ships no `django_strawberry_framework/` code, so there is nothing for a package test to exercise — adding one here would have no system under test.
- **The acceptance artifact is the floor-check, not a pytest assertion** (spec lines 605-607). It is the `uv` command sweep transcript recorded in this artifact's `## Build report (Worker 2)` and the PR description — explicitly NOT a normal pytest assertion (the suite cannot prove a matrix-wide warning-free import from one interpreter). Worker 3 verifies the transcript exists and that the recorded floor matches the `pyproject.toml` pin; Worker 1 audits the three-places agreement at final verification.
- **Coverage rule (BUILD.md):** no `pytest --cov*` invocation is planned for this slice. If a dev-env smoke `pytest` is run to confirm DRF imports warning-free under `filterwarnings = error`, it uses `--no-cov` (the only permitted coverage-shaped flag) and is a smoke check, not a coverage gate.

### Implementation discretion items

- **The precise position of the `"djangorestframework>=3.17.0",` row within the existing `[dependency-groups].dev` list** (e.g. alphabetical vs. grouped-by-purpose). The list is not strictly alphabetical today (`faker`, `pillow`, then the `pytest*` cluster), so Worker 2 may place the DRF row wherever reads best as long as it stays inside `[dependency-groups].dev` and the trailing-comma layout holds. Assessed: a stylistic ordering choice with no behavioral effect.
- **Whether to run the full `.github/workflows/django.yml` matrix sweep locally vs. recording the decisive cells locally + the remaining cells as a documented PR-matrix table.** Either satisfies the spec's option (b) "documented sequence … recorded in the PR description." Assessed: Worker 2's discretion on sweep breadth, provided the binding cell (Python 3.14 × Django 6.0/latest) and the floor cell (Python 3.10 × Django 5.2.0) are both proven warning-free and recorded.

### Spec slice checklist (verbatim)

- [x] Slice 0 (pre-Slice-1 dependency gate, **F11**): verify + pin the DRF floor **before**
  any converter code, since Slice 1–3 tests import DRF.
  - [x] **Verify the floor:** confirm a `djangorestframework` release that imports and runs
    **warning-free** across the [`django.yml`][django-workflow] CI matrix (Python
    3.10 → 3.14 × Django 5.2 → 6.0 / `latest`) under [`pytest.ini`][pytest-ini]'s
    `filterwarnings = error` (DRF's Django support lags Django, so a 6.0 / `latest`-clean
    release must be confirmed to exist), and record the **exact pinned floor**
    ([Risks](#risks-and-open-questions)).
  - [x] **The floor check is an explicit acceptance artifact, not a normal pytest
    assertion** (the suite cannot prove a *matrix-wide* warning-free import from inside one
    interpreter). The artifact is one of: (a) a short probe script
    (`scripts/check_drf_floor.py`) that imports `rest_framework` under `-W error` and asserts
    the installed version `>=` the recorded floor, runnable on each matrix node; **or** (b) a
    documented sequence of explicit `uv` commands (e.g.
    `uv run --python 3.14 --with 'django>=6.0' python -W error -c "import rest_framework"`
    across the Python × Django cells) recorded in the Slice 0 PR description. The **chosen
    floor is recorded in three places that must agree**: the `[dependency-groups].dev`
    `djangorestframework>=<floor>` pin in [`pyproject.toml`][pyproject], the
    `require_drf()` guard's **install hint**, and a one-line note in
    [Risks](#risks-and-open-questions). If no compatible release exists, the card **blocks at
    the gate**, not mid-Slice-1.
  - [x] **Wire the dev dependency:** add `djangorestframework` to
    `[dependency-groups].dev` (NOT `[project].dependencies` — it stays a soft runtime dep)
    in [`pyproject.toml`][pyproject], regenerate `uv.lock` (`uv lock`), and add any
    **targeted DRF-origin `ignore::` line** to [`pytest.ini`][pytest-ini] the verified
    release still needs — all **before** Slice 1. **No package-version edits** (stays
    `0.0.12`, [Decision 14](#decision-14--version-bumps-are-owned-by-the-joint-0013-cut)).

### Notes for Worker 1 (spec reconciliation)

- **Floor record is an in-contract spec edit, deferred to final verification.** The spec's Slice 0 contract mandates recording the chosen floor as "a one-line note in Risks" (lines 612-616), but the Risks "DRF version floor" item (lines 3414-3443) as written describes only the *procedure*, not a number. Worker 1 will append `djangorestframework>=3.17.0` there at final verification once Worker 2's sweep proves it clears the matrix — recorded under `### Spec changes made (Worker 1 only)`. This is not a spec gap/conflict, just the contract's own deferred fill-in; flagged here so it is not forgotten.
- **No spec conflict found for Slice 0.** The Slice 0 bullet, Decision 12, Decision 14, the Doc-updates "Pre-Slice-1 gate" bullet, the Risks "DRF version floor" item, and DoD items 7-8 are mutually consistent on: dev-group-only, `uv.lock` regen (DRF entries only), package version stays `0.0.12`, no `CHANGELOG.md` edit in this card, and the floor gated on the matrix-wide warning-free import. Nothing required reconciliation at planning time.
- **Status-line re-verification (per `worker-1.md`).** The spec header lines (1-5) describe the card as the in-progress `039` build; no slice has shipped yet at Slice 0 planning, so the header is accurate. No header edit needed this pass.

---

## Build report (Worker 2)

### Files touched

- `pyproject.toml` — `[dependency-groups].dev`: replaced the four-line `TODO(spec-039 Slice 0)`
  comment block with a single `"djangorestframework>=3.17.0",` row, placed alphabetically at
  the head of the dev list (before `faker`/`pillow` — the plan grants ordering discretion;
  `djangorestframework` sorts first). The staged anchor is fully discharged (deleted; the row
  is self-documenting so no non-TODO provenance comment was added). NOT added to
  `[project].dependencies` (stays a soft runtime dep). `[project].version` untouched (`0.0.12`).
- `uv.lock` — regenerated via `uv lock` (NOT `--upgrade`). Diff is DRF-only: `djangorestframework`
  added to `[package.dev-dependencies] dev` and `[package.metadata.requires-dev] dev`
  (`specifier = ">=3.17.0"`), plus a new `[[package]] name = "djangorestframework"
  version = "3.17.1"` stanza. DRF's only declared dep is `django` (already locked) — no new
  transitive packages. The `django-strawberry-framework` package `version = "0.0.12"` entry
  (line 218) is unchanged. No unrelated locked versions drifted.

### Tests added or updated

- **None.** Per the plan (Decision 12, spec lines 2556-2571), Slice 0 ships no
  `django_strawberry_framework/` code, so there is no system under test for a package test. The
  DRF-absent import-guard test is Slice 2 (gated on `require_drf()` existing). The Slice 0
  acceptance artifact is the floor-check sweep transcript below — explicitly NOT a pytest
  assertion (the suite cannot prove a matrix-wide warning-free import from one interpreter).

### Validation run

- `uv run ruff format .` — **pass** (294 files left unchanged). The `COM812 may cause conflicts`
  line is the repo's standing config warning that prints on every run, not a failure.
- `uv run ruff check --fix .` — **pass** ("All checks passed!").
- `git status --short` after both ruff invocations — modified files and classification:
  - `pyproject.toml` (M) — **slice-intended** (DRF dev-group row); appears in Files touched.
  - `uv.lock` (M) — **slice-intended** (DRF lock entries); appears in Files touched.
  - `docs/feedback.md` (M) — baseline-dirty out-of-scope (build plan + dispatch say leave as-is;
    concurrent maintainer work per `AGENTS.md` #34). Not touched, not reverted.
  - `docs/builder/bld-slice-0-drf_dependency_gate.md` (??) — this artifact (Worker 1 created it;
    Worker 2 appends this report + ticks the checklist).
  - `docs/builder/build-039-serializer_mutations-0_0_13.md` (??) — Worker 0's build plan
    (created at pre-flight).
  - 8× deleted `docs/builder/bld-*` / `build-038-*` (D) — prior-038-cycle artifacts removed by
    pre-flight (documented in the build plan's Pre-flight outcome). Predate this pass; not my
    tool churn to revert.
  - No unrelated tool churn introduced by this pass. My slice diff is exactly `pyproject.toml`
    + `uv.lock`.
- Focused tests run — none required as a gate. A `pytest --no-cov --co -q tests/base/` collection
  smoke confirmed collection still works after the dev-group add + venv restore (25 tests
  collected). No `--cov*` flag used anywhere in this pass.

### DRF floor verification sweep (the acceptance artifact — option b)

All cells run with `python -W error` (mirrors `pytest.ini` `filterwarnings = error`). Each cell
imports `rest_framework` AND `django` warning-free. The decisive cells (binding + floor) were run
against the project resolver; the intermediate cells used `uv run --isolated` to avoid further
mutating the project `.venv` (per Worker 2 memory: never thrash the shared `.venv` for matrix
testing). Every cell resolved DRF to **3.17.1** (latest patch satisfying `>=3.17.0`).

| Python | Django constraint | Resolved DRF / Django | Result |
|---|---|---|---|
| 3.14 | `Django==6.0` (binding cell) | 3.17.1 / 6.0 | PASS (warning-free) |
| 3.10 | `Django==5.2.0` (floor cell) | 3.17.1 / 5.2 | PASS (warning-free) |
| 3.11 | `Django==5.2.*` | 3.17.1 / 5.2.15 | PASS (warning-free) |
| 3.12 | `Django==5.2.*` | 3.17.1 / 5.2.15 | PASS (warning-free) |
| 3.13 | `Django==5.2.*` | 3.17.1 / 5.2.15 | PASS (warning-free) |
| 3.12 | `Django==6.0.*` | 3.17.1 / 6.0.6 | PASS (warning-free) |
| 3.13 | `Django==6.0.*` | 3.17.1 / 6.0.6 | PASS (warning-free) |
| 3.14 | `Django==6.0.*` | 3.17.1 / 6.0.6 | PASS (warning-free) |
| 3.14 | `Django` (latest) | 3.17.1 / 6.0.6 | PASS (warning-free) |

Exact commands (binding + floor cells, run against the project resolver):

```shell
uv run --python 3.14 --with 'djangorestframework>=3.17.0' --with 'Django==6.0' \
  python -W error -c "import rest_framework; import django; print(rest_framework.VERSION, django.get_version())"
uv run --python 3.10 --with 'djangorestframework>=3.17.0' --with 'Django==5.2.0' \
  python -W error -c "import rest_framework; import django; print(rest_framework.VERSION, django.get_version())"
```

Intermediate cells (isolated, one representative shown; Python/Django varied per row above):

```shell
uv run --isolated --python 3.14 --with 'djangorestframework>=3.17.0' --with 'Django==6.0.*' \
  python -W error -c "import rest_framework, django; print(rest_framework.VERSION, django.get_version())"
```

No cell errored; no cell emitted a warning under `-W error`. The floor `djangorestframework>=3.17.0`
clears the entire `django.yml` CI matrix (Python 3.10→3.14 × Django 5.2→6.0/`latest`). The card does
NOT block at the gate.

### pytest.ini ignore line

**No ignore line needed.** Every matrix cell imports warning-free under `-W error`, so `pytest.ini`
stays untouched (no speculative ignore added, per the plan and `pytest.ini`'s "never blanket-ignore"
convention). DRF 3.17.0 explicitly added Django 6.0 + Python 3.14 support and dropped the deprecated
`coreapi`/`py3.9` paths, which is why the import is clean across the matrix.

### Implementation notes

- **DRF row placed alphabetically (head of dev list).** The plan flagged this as discretion;
  `djangorestframework` sorts before `faker`, so the head of the existing multi-line list reads
  cleanest and keeps the trailing-comma layout intact (`scripts/check_trailing_commas.py`: the
  dev list is already one-item-per-line, threshold 4).
- **`uv lock` resolved DRF to 3.17.1, not 3.17.0.** `>=3.17.0` correctly floats to the latest
  satisfying patch (3.17.1, the `HTMLFormRenderer` empty-datetime bugfix). The *pin* stays
  `>=3.17.0` (the lowest supporting release, per the house "lowest supporting version" convention);
  the *locked* version is 3.17.1. This matches the plan: pin the floor, lock the latest patch.
- **Soft-dependency contract verified beyond the pin.** Confirmed `import django_strawberry_framework`
  does NOT pull `rest_framework` into `sys.modules` (checked under `-W error`), so DRF stays a soft
  dep even though it is now installed in the venv via the dev group. DRF-in-venv is correct and
  required (Slice 1–3 suites import it); soft means "not eagerly imported by the package," which holds.
- **Project `.venv` restored to Python 3.14.2.** The floor cell (`--python 3.10`) recreated the
  project `.venv` at 3.10.19 (a known `uv run --python` side effect). Restored via
  `uv sync --python 3.14`; confirmed `uv run python --version` → 3.14.2 and collection still works.
  `.venv` is gitignored so this churn is invisible to git.

### Notes for Worker 3

- No `django_strawberry_framework/` source changed — `scripts/review_inspect.py` is not applicable
  to this slice (no new/edited `.py` logic file). No shadow files used.
- The slice diff is exactly two files: `pyproject.toml` (one dev-group row, anchor discharged) and
  `uv.lock` (DRF-only regen). Public surface (`django_strawberry_framework/__init__.py`) is
  unchanged — `SerializerMutation` is not exported until Slice 2.
- The acceptance artifact for this slice is the sweep transcript above, not a pytest test (by
  design — spec lines 605-607). Verify the recorded floor (`>=3.17.0`) matches the `pyproject.toml`
  pin and that the `uv.lock` package-version entry is still `0.0.12`.
- The `TODO(spec-039 Slice 2)` anchor in `django_strawberry_framework/rest_framework/__init__.py`
  is intentionally left intact (it names Slice 2 work — `require_drf()` + the install hint). Not
  mine to discharge.

### Notes for Worker 1 (spec reconciliation)

- **Floor proven: `djangorestframework>=3.17.0` clears the full matrix warning-free** (all 9
  CI-matrix cells PASS under `-W error`; resolved DRF 3.17.1 / Django 5.2→6.0). This confirms the
  number the plan deferred to your final-verification spec edit: append `djangorestframework>=3.17.0`
  (first release with Django 6.0 + Python 3.14 support, released 2026-03-18) to the spec's Risks
  "DRF version floor" item as place (3) of the three-places-that-must-agree, recorded under
  `### Spec changes made (Worker 1 only)`. No higher floor was forced.
- **Cross-slice obligation reminder (unchanged from plan).** Place (2) — the `require_drf()` install
  hint — is authored in Slice 2 and must name the SAME floor `djangorestframework>=3.17.0`. Slice 0
  owns place (1) `pyproject.toml` (landed) and place (3) spec Risks (your final-verification edit).
- No spec gap or conflict surfaced during the build. The slice landed exactly as planned.

---

## Review (Worker 3)

Config-only slice. Worker 2's diff is exactly two files (`pyproject.toml`, `uv.lock`), matching
the contract. I reviewed the working-tree diff (authoritative), the spec slice checklist, Decision
12, Decision 14, and DoD items 7-8. I ignored the out-of-scope churn the dispatch named: the deleted
`bld-*` / `build-038-*` files and new `build-039-*` / `bld-slice-0-*` files (pre-flight cycle reset),
and `M docs/feedback.md` (baseline-dirty, concurrent maintainer work per `AGENTS.md` #34).

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- No live duplication introduced. The "three places that must agree" floor (`>=3.17.0`) is the one
  DRY hazard this slice could create; Slice 0 correctly authored only place (1) — the
  `pyproject.toml` dev-group pin. Place (2) (`require_drf()` install hint) is Slice 2 and place (3)
  (spec Risks note) is deferred to Worker 1 final verification, so no second copy exists yet to drift
  against. The cross-slice obligation is already flagged for Slice 2 in `### Notes for Worker 1`.
- The DRF row reuses the established dev-group soft-dependency shape (`pillow>=10.0.0`,
  `faker>=33.0.0`) verbatim — no new pattern.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — `__all__` and the re-export
list are unchanged. `SerializerMutation` is not exported until Slice 2 (Decision 12 keeps it out of
`__all__` while DRF is soft, resolved lazily via root `__getattr__`). No public-surface drift.
Confirmed `require_drf()` is NOT authored this slice: `grep -rn 'def require_drf'
django_strawberry_framework/` returns nothing; the only `require_drf` mentions are pre-existing
Slice 2 staging comments in `__init__.py` (line 47) and `rest_framework/__init__.py` (line 7), and
neither file appears in this slice's diff (verified `git diff` on both is empty).

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md. (`git diff --stat -- CHANGELOG.md` is empty.)

### Documentation / release sanity

`pyproject.toml` is release metadata. Confirmed:
- `[project].version` stays `0.0.12` (line 4) — no released-feature overclaim.
- DRF is in `[dependency-groups].dev` only (`"djangorestframework>=3.17.0",` at the head of the dev
  list), NOT in `[project].dependencies` (lines 27-33 carry only `Django>=5.2`,
  `strawberry-graphql>=0.262.0`, `django-filter>=25.2`, `wrapt>=2.0.1`). Soft-dependency contract
  intact.
- **No version bump anywhere** (Decision 14): `[project].version` = `0.0.12`, `__version__`
  (`__init__.py:37`) = `0.0.12`, `tests/base/test_init.py:19` asserts `0.0.12`, and the `uv.lock`
  `[[package]] name = "django-strawberry-framework"` `version` entry (line 218) = `0.0.12`. All four
  agree.
- `uv.lock` diff is DRF-only (15 insertions): `djangorestframework` added to
  `[package.dev-dependencies] dev` and `[package.metadata.requires-dev] dev` (`specifier =
  ">=3.17.0"`), plus a new `[[package]] djangorestframework version = "3.17.1"` stanza whose only
  transitive dep is `django` (already locked — no new transitive packages). No unrelated locked
  versions drifted. The pin floats to the latest satisfying patch (3.17.1) while the *pin* stays
  `>=3.17.0` (house "lowest supporting version" convention) — coherent.
- The staged `TODO(spec-039 Slice 0)` anchor in `pyproject.toml` is fully discharged
  (`grep -rn 'TODO(spec-039 Slice 0'` across `.toml`/`.py`/`.ini` returns nothing). The row is
  self-documenting, so no replacement provenance comment is needed (matches AGENTS.md "removed in the
  same change that ships the slice").
- The spec's Risks "DRF version floor" note is correctly **not** edited this slice
  (`git diff -- docs/spec-039-...md` is empty); per the plan it is deferred to Worker 1's final
  verification, which records the proven `>=3.17.0` floor.

### Spec slice checklist walk

The Plan's `### Spec slice checklist (verbatim)` copies the spec's Slice 0 boxes character-for-
character (verified against spec lines 597-623). All four boxes are ticked `- [x]` by Worker 2;
each has matching implementation in the diff or the recorded acceptance artifact:
- **Verify the floor** (`- [x]`): the DRF floor verification sweep (build report) records all 9
  CI-matrix cells (Python 3.10→3.14 × Django 5.2→6.0/`latest`) importing `rest_framework` + `django`
  warning-free under `python -W error`, resolving DRF 3.17.1. The recorded floor is the exact pinned
  floor. Matches.
- **Floor check is an acceptance artifact** (`- [x]`): Worker 2 chose option (b) — the documented
  `uv` command sweep recorded in the build report (the spec-sanctioned alternative to shipping
  `scripts/check_drf_floor.py`). No probe script shipped (correct — option (a) is not required and
  would expand package surface). The chosen floor is recorded in place (1) `pyproject.toml`; places
  (2) and (3) are correctly deferred to Slice 2 and Worker 1. Matches.
- **Wire the dev dependency** (`- [x]`): DRF added to `[dependency-groups].dev` (not
  `[project].dependencies`), `uv.lock` regenerated (`uv lock`, DRF-only), no `pytest.ini` ignore line
  added (none needed — every cell imports warning-free), version stays `0.0.12`. Matches.

No over-ticked box (every `- [x]` has matching implementation); no silently un-addressed `- [ ]`.

### Static inspection helper

Skipped. Reason: config-only slice, no Python logic added (the diff is `pyproject.toml` + `uv.lock`
only; no new or edited `.py` logic file). Per `BUILD.md` "Static inspection helper" this is the
documented skip case.

### What looks solid

- Diff is minimal and exactly the contract: two files, no scope creep.
- Soft-dependency contract verified at runtime: `import django_strawberry_framework` succeeds and
  does NOT pull `rest_framework` into `sys.modules` (Worker 3 re-ran:
  `import sys, django_strawberry_framework as d; print(d.__version__, 'rest_framework' in
  sys.modules)` → `0.0.12 False`).
- Version invariant held across all four places (pyproject, `__init__.py`, `test_init.py`, `uv.lock`
  package entry).
- The `pytest.ini` "never blanket-ignore" convention was honored by adding nothing — the verified
  release needs no ignore, so the file is correctly untouched.
- Floor justification (3.17.0 = first DRF with Django 6.0 + Python 3.14 support, drops the deprecated
  `coreapi`/py3.9 paths) is coherent and matches the lowest-supporting-version house convention.

### Temp test verification

No temp tests created. Slice 0 has no system under test (no `django_strawberry_framework/` code); the
acceptance artifact is the documented sweep transcript, not a pytest assertion. Verification was a
diff/grep inspection plus the single soft-dep import sanity above.

### Notes for Worker 1 (spec reconciliation)

- **Floor record still pending (in-contract, deferred):** Worker 1 must append
  `djangorestframework>=3.17.0` to the spec's Risks "DRF version floor" item at final verification
  (place (3) of the three-places-that-must-agree). The build report proves the number; the spec edit
  is the remaining contract fill-in. Not a finding — flagged so it is not forgotten.
- **Cross-slice obligation for Slice 2:** the `require_drf()` install hint (place (2)) must name the
  SAME floor `djangorestframework>=3.17.0`. Carry into the Slice 2 dispatch.

### Review outcome

`review-accepted`. No High/Medium/Low findings. Every spec slice sub-check is reflected in the diff
or the recorded acceptance artifact; the version invariant, soft-dependency contract, public surface,
and DRY constraints all hold. The only outstanding items are the spec Risks floor record (deferred to
Worker 1 by plan) and the Slice 2 install-hint floor agreement (cross-slice obligation) — neither
blocks acceptance of this slice.

---

## Final verification (Worker 1)

Config-only slice. I re-audited the slice against the authoritative working-tree diff
(`git diff -- pyproject.toml pytest.ini uv.lock`), re-ran the focused version test without
coverage flags, discharged the one in-contract spec edit the Slice 0 contract deferred to this
pass, and confirmed the no-version-bump and anchor-discharge invariants.

### 1. Spec slice checklist audit (re-audited every `- [x]` against the diff)

I am no longer the original ticker — Worker 2 ticked all four boxes during the build. Re-audited
each against the diff / recorded acceptance artifact:

- **Slice 0 parent box** (`- [x]`): the gate landed before any converter code (no
  `django_strawberry_framework/` source touched; diff is `pyproject.toml` + `uv.lock` only).
  Confirmed. Stays `- [x]`.
- **Verify the floor** (`- [x]`): the build report's DRF floor verification sweep records all 9
  `django.yml` CI-matrix cells (Python 3.10→3.14 × Django 5.2→6.0 / `latest`) importing
  `rest_framework` + `django` warning-free under `python -W error`, resolving DRF 3.17.1, and the
  exact pinned floor (`>=3.17.0`) is recorded. The acceptance artifact is the sweep transcript, not
  a pytest assertion (spec lines 605-607 — the suite cannot prove a matrix-wide warning-free import
  from one interpreter). Implementation present. Stays `- [x]`.
- **Floor check is an acceptance artifact** (`- [x]`): Worker 2 chose option (b) — the documented
  `uv` command sweep recorded in the build report (the spec-sanctioned alternative to shipping
  `scripts/check_drf_floor.py`); no probe script shipped (correct — option (a) would expand package
  surface and is not required). Place (1) of the three-places floor (`pyproject.toml` dev-group pin)
  is present in the diff; places (2) Slice 2 install hint and (3) spec Risks note were correctly
  deferred — place (3) is discharged by this final-verification pass (item 4 below). Stays `- [x]`.
- **Wire the dev dependency** (`- [x]`): the diff adds `"djangorestframework>=3.17.0",` to
  `[dependency-groups].dev` (NOT `[project].dependencies` — verified `[project].dependencies` still
  carries only `Django`, `strawberry-graphql`, `django-filter`, `wrapt`), regenerates `uv.lock`
  (DRF-only: `djangorestframework` added to `[package.dev-dependencies] dev` + `[package.metadata.requires-dev] dev`
  with `specifier = ">=3.17.0"`, plus a new `[[package]] djangorestframework version = "3.17.1"`
  stanza whose only transitive dep is `django`, already locked — no unrelated locked versions
  drifted), and adds **no** `pytest.ini` ignore line (`git diff -- pytest.ini` is empty — none
  needed, every cell imports warning-free). Package version stays `0.0.12` (Decision 14). Implementation
  present. Stays `- [x]`.

No over-ticked box (every `- [x]` has matching implementation in the diff or the recorded
acceptance artifact); no silently un-ticked `- [ ]` remains.

### 2. DRY check

No new duplication. The "three places that must agree" floor (`>=3.17.0`) is the only DRY hazard
this slice could create; Slice 0 authored only place (1) (`pyproject.toml` dev-group pin). Place (2)
(`require_drf()` install hint) is Slice 2; place (3) (spec Risks note) is discharged by this pass —
both now name the same floor, so no drift exists. The DRF dev-group row reuses the established
soft-dependency shape (`pillow>=10.0.0`, `faker>=33.0.0`) verbatim — no new pattern.

### 3. Existing tests still pass (focused scope, no coverage flags)

`uv run pytest tests/base/test_init.py --no-cov` → **5 passed in 1.25s** (Python 3.14.2, Django
6.0.5). `tests/base/test_init.py::test_version` asserts `__version__ == "0.0.12"` and passed,
proving no accidental version bump. The explicit `--no-cov` was used (required because `pytest.ini`
auto-applies `--cov`); no `--cov*` flag was used anywhere this pass.

No-version-bump invariant confirmed across all four places (Decision 14):
`pyproject.toml:4` = `0.0.12`, `django_strawberry_framework/__init__.py:37` = `0.0.12`,
`tests/base/test_init.py:19` asserts `0.0.12`, and the `uv.lock`
`[[package]] name = "django-strawberry-framework"` entry = `0.0.12` (unchanged).

Anchor discharge confirmed: `grep -rEn 'TODO\(spec-039 Slice 0' .` across `.toml`/`.py`/`.ini`
returns nothing — the staged anchor is fully discharged, removed in the same change that shipped the
row (AGENTS.md convention). The `TODO(spec-039 Slice 2)` anchor in
`django_strawberry_framework/rest_framework/__init__.py` is correctly left intact (names Slice 2
work — not this slice's to discharge).

### 4. Spec reconciliation — REQUIRED in-contract spec edit (discharged)

Made the mandated floor-record edit (see `### Spec changes made (Worker 1 only)` below). The spec
Risks "DRF version floor" item now records the proven floor `djangorestframework>=3.17.0` as place 3
of the three-places-that-must-agree. The spec-glossary consistency check
(`uv run python scripts/check_spec_glossary.py --spec docs/spec-039-serializer_mutations-0_0_13.md`)
exits 0 after the edit, and the link references I used (`[django-workflow]`, `[pyproject]`) resolve.

Status-line re-verification (per `worker-1.md`): the spec header lines (1-5) describe the `039` build
as in progress; Slice 0 is the first slice and ships no public surface, so the header remains
accurate. No header edit needed.

### 5. Final status

`final-accepted`. The diff matches the contract exactly (two files), every spec slice sub-check is
reflected in the diff or the recorded acceptance artifact, the version invariant holds across all
four places, the soft-dependency contract and public surface are intact, the staged Slice 0 anchor is
discharged, and the mandated spec floor-record edit is made.

### Summary

Slice 0 ships the F11 pre-Slice-1 DRF dependency gate as a config-only change: `pyproject.toml` adds
`"djangorestframework>=3.17.0"` to `[dependency-groups].dev` (soft runtime dep — not in
`[project].dependencies`), `uv.lock` is regenerated with the DRF-only entry (locked 3.17.1), and no
`pytest.ini` ignore line was needed because the floor imports warning-free across all 9 CI-matrix
cells under `-W error`. No package code, no tests, no version bump. The proven floor is now recorded
in the spec Risks note (place 3 of the three-places-that-must-agree).

### Spec changes made (Worker 1 only)

- `docs/spec-039-serializer_mutations-0_0_13.md` lines 3444-3450 (within the
  `## Risks and open questions` "DRF version floor" item, ::"Risks and open questions"
  #"Recorded floor (Slice 0, verified)") — **appended** a recorded-floor note pinning
  `djangorestframework>=3.17.0` (first release with Django 6.0 + Python 3.14 support, released
  2026-03-18, resolves to 3.17.1; proven warning-free across all 9 `django.yml` matrix cells under
  `-W error` with no `ignore::` line needed), and naming it place 3 of the three-places-that-must-agree
  (place 1 = the `pyproject.toml` dev-group pin, landed; place 2 = the Slice 2 `require_drf()` install
  hint, which must name the same floor). **Reason:** the Slice 0 contract (spec lines 612-616) mandates
  recording the chosen floor as a one-line note in Risks; the item as written described only the
  verification procedure, not a number. This was deliberately deferred from planning to final
  verification so the recorded number reflects Worker 2's proven sweep, not a planning-time
  prediction. Triggered by Slice 0. Spec-glossary check passes (exit 0) post-edit.
