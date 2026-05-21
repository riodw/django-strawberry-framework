````text
# Build: Slice 1 — Module + `AppConfig` subclass

Spec reference: `docs/spec-017-apps-0_0_7.md` (Slice 1 sub-bullets at lines 55-63; Decisions 1 / 2 / 3 / 4 / 5 / 8)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.** The spec's [Borrowing posture](../spec-017-apps-0_0_7.md#borrowing-posture) section pins the shape to crib: `strawberry_django/apps.py` at `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/apps.py` ships a four-line `AppConfig` subclass with two attributes (`name`, `verbose_name`). Slice 1 borrows this **behavioral** shape verbatim and adds the two docstrings the upstream omits (`D100` / `D101`-forced — see Borrowing posture's "two forced divergences" sentence and Decision 2's docstring pinning at `docs/spec-017-apps-0_0_7.md:226-238`). The existing on-disk staged-stub module `django_strawberry_framework/apps.py:1-49` already contains the canonical pseudo-block under the spec citation and the forbidden-attribute catalog — Slice 1 replaces the stub with the implementation block the stub previewed; the stub's prose is the one source of truth for what Slice 1 ships, so the implementer should not re-derive the shape from the spec from scratch.
- **New helpers justified.** None. The class is two attribute assignments plus two docstrings; no shared helper or module-level constant is justified at this surface. There are no existing helpers in the package to reuse either — `django_strawberry_framework/` ships `__init__.py`, `apps.py` (staged stub), `conf.py`, `exceptions.py`, `list_field.py`, `registry.py`, `scalars.py`, and the `optimizer/` / `types/` / `utils/` subpackages, none of which have an `AppConfig`-adjacent helper to call.
- **Duplication risk avoided.** Two specific risks the naive implementation could introduce, and how the plan blocks them:
  1. **Re-stating `"django_strawberry_framework"` in multiple sites.** The `name` attribute is the one canonical declaration of the package's Django app-label string in the package's source. The string already exists in `django_strawberry_framework/__init__.py:16` (`logging.getLogger("django_strawberry_framework")`) as a logger name; do NOT factor either site through a shared module constant — the logger name is a consumer-facing key in Django's `LOGGING` dict (per the comment at `__init__.py:10-15`) and the AppConfig's `name` is a Django app-loader key. Two different consumer contracts that happen to share a string is not duplication to consolidate; treating it as such would couple a logger-name change to an AppConfig-rename, which is wrong (the package directory would have to move too). Worker 2 should write the string literally in both sites.
  2. **A `ready()` body sneaking in via "future flexibility."** The Risks section at `docs/spec-017-apps-0_0_7.md:435` and Decision 4 at `docs/spec-017-apps-0_0_7.md:272-289` both forbid a `pass`-bodied `ready()` placeholder. The negative-shape test landing in Slice 2 catches this, but Worker 2 must not preempt that test by adding a placeholder `ready()` "for documentation." The class body is exactly the two attribute assignments and a class docstring — no more.

### Implementation steps

Line numbers below are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written.

1. **Replace the staged-stub module body in `django_strawberry_framework/apps.py:1-53`.** The file already exists as a TODO-anchored Pseudo block under the AGENTS.md line 26 staged-slice convention (the spec at `docs/spec-017-apps-0_0_7.md:95` documents this — the `[alpha]` tag at `docs/TREE.md:236` means "lands before `0.1.0`"; Slice 3 removes the tag once the implementation lands). Worker 2 rewrites the entire file: the new module docstring (one line; `D100`-forced per rev4 L3), a single `from django.apps import AppConfig` import, and the `DjangoStrawberryFrameworkConfig(AppConfig)` class body with a one-line class docstring (`D101`-forced per rev3 H1), `name = "django_strawberry_framework"`, and `verbose_name = "Django Strawberry Framework"`. Delete the entire pseudo-block prose currently at lines 14-48 and the TODO anchor at lines 51-53 — once the implementation lands, the staged-stub framing is no longer correct (the spec at `apps.py:48` says "When the TODO below disappears, Slice 1 has shipped"; deleting the TODO IS the act that flips the file from staged-stub to shipped).
2. **Confirm `name`'s value matches the existing `INSTALLED_APPS` entry.** `examples/fakeshop/config/settings.py:48` already declares `"django_strawberry_framework"`; the `name = "django_strawberry_framework"` line must match that string character-for-character so Django's implicit single-AppConfig discovery resolves the consumer's entry to the explicit class (per Decision 7 at `docs/spec-017-apps-0_0_7.md:318-331` — fakeshop settings is NOT modified, so the explicit class must match the consumer string).
3. **Class docstring exact wording is at Worker 2's discretion** within the constraint that it satisfies `D101` (one-line summary of the class's purpose; pydocstyle's google convention per `pyproject.toml`'s `[tool.ruff.lint.pydocstyle] convention = "google"` accepts a single summary line). The spec's suggested wording at `docs/spec-017-apps-0_0_7.md:61` (`"""Register django-strawberry-framework with Django's app loader."""`) is a strong default; Worker 2 may match it verbatim or paraphrase. Same applies to the module docstring per `docs/spec-017-apps-0_0_7.md:60` — the spec's example wording is a default, not a contract. See [Implementation discretion items](#implementation-discretion-items).
4. **Do not modify `django_strawberry_framework/__init__.py`.** Per [Decision 3](../spec-017-apps-0_0_7.md#decision-3--no-public-export) at `docs/spec-017-apps-0_0_7.md:257-270`. The Public-surface check during Slice 1 review (per BUILD.md `### Public-surface check`) confirms `git diff -- django_strawberry_framework/__init__.py` is empty.
5. **Do not modify `examples/fakeshop/config/settings.py`.** Per [Decision 7](../spec-017-apps-0_0_7.md#decision-7--no-fakeshop-installed_apps-entry-change) at `docs/spec-017-apps-0_0_7.md:318-331`. The existing `"django_strawberry_framework"` entry continues to work through Django's implicit single-AppConfig discovery, now resolving to the explicit class once `apps.py` lands.
6. **Run the per-pass gate.** `uv run ruff format .` and `uv run ruff check --fix .` (per BUILD.md `### Validation run`). After running, `git status --short` and confirm only `django_strawberry_framework/apps.py` (and the artifact, which Worker 2 also writes to) appears in the diff — any other file that surfaces is unrelated tool churn Worker 2 owns reverting per BUILD.md line 248 ("Tool-induced drift is Worker 2's responsibility to own at this boundary").

### Test additions / updates

- **No tests in Slice 1.** Tests land in Slice 2 (`tests/test_apps.py` — see `docs/spec-017-apps-0_0_7.md:64-66` and the [Test plan](../spec-017-apps-0_0_7.md#test-plan) section at lines 374-396). Do NOT pull tests forward; the [Implementation plan](../spec-017-apps-0_0_7.md#implementation-plan) at `docs/spec-017-apps-0_0_7.md:351-361` explicitly pins "0 (tests land in Slice 2)" for Slice 1 and notes "Slice 2 depends on Slice 1 (the class must exist before tests can import it)." Worker 2 finishes Slice 1 with the class in place but no test file.
- **Temp / scratch tests for development.** Worker 2 may, optionally, run an ad-hoc `python -c "from django_strawberry_framework.apps import DjangoStrawberryFrameworkConfig; print(DjangoStrawberryFrameworkConfig.name, DjangoStrawberryFrameworkConfig.verbose_name)"` to sanity-check the import works after the rewrite; this is NOT a committed test and does not require a `docs/builder/temp-tests/` artifact (the spec's negative-shape contract is exercised by Slice 2, and a pure-class-definition module does not have non-obvious failure modes Slice 1 would benefit from temp-testing).

### Implementation discretion items

Items where Worker 1 has assessed and decided the choice belongs to Worker 2 (per BUILD.md "Implementation discretion items" — only stylistic / equivalent-shape preferences, never architectural questions):

- **Exact one-line wording of the module docstring** as long as it satisfies `D100` (any non-empty single-line summary of the module's purpose under the pydocstyle google convention). The spec's example at `docs/spec-017-apps-0_0_7.md:60` (`"""Django AppConfig — registers the package with Django's app loader so consumers can list it in INSTALLED_APPS and Django's check / signal hooks resolve against it."""`) is a strong default; Worker 2 may use it verbatim, shorten it (e.g., `"""Django AppConfig for django-strawberry-framework."""`), or paraphrase. The contract is one line + `D100` passes; the prose is Worker 2's call.
- **Exact one-line wording of the class docstring** as long as it satisfies `D101`. Same posture: `docs/spec-017-apps-0_0_7.md:61` suggests `"""Register django-strawberry-framework with Django's app loader."""`; Worker 2 may match or paraphrase. The contract is one line + `D101` passes.
- **Whether the module docstring uses a `Django AppConfig — ...` em-dash lead-in or a plain sentence.** Both pass `D100`. The existing staged-stub at `apps.py:1` uses the em-dash form; matching that is the lower-friction default but not required.
- **Order of `name` and `verbose_name` attribute assignments inside the class body.** Both are class-level constants with no inter-attribute dependency; either order is valid. The spec at `docs/spec-017-apps-0_0_7.md:57-59` lists `name` first and `verbose_name` second, which matches the upstream `strawberry_django/apps.py` shape — this is the strong default but not mandatory.

Items NOT in Worker 2's discretion (these are spec-pinned and any deviation requires a Worker 1 spec edit through `### Spec changes made (Worker 1 only)`):

- The attribute values themselves: `name = "django_strawberry_framework"` and `verbose_name = "Django Strawberry Framework"` are pinned in Decision 2 and the spec's `Test plan` (Slice 2's `test_djangostrawberryframeworkconfig_pins_name_and_verbose_name` asserts both).
- The class name `DjangoStrawberryFrameworkConfig` (pinned in Decision 2 / Slice 1 checklist).
- The module path `django_strawberry_framework/apps.py` (pinned in Decision 1).
- The absence of `ready()`, `label`, `default_auto_field`, and `default` (any value) on the class body (Decisions 2 / 4 / 5 / 8; pinned by the Slice 2 consolidated negative-shape test).
- The absence of a re-export from `django_strawberry_framework/__init__.py` (Decision 3).

### `scripts/review_inspect.py` disposition for Slice 1

Per BUILD.md "When to run the helper during build" at lines 398-411:

- **Worker 1 (this pass).** Helper NOT run. The spec / staged-stub already pins the implementation shape to ~6 source lines; Worker 1 has no logic to plan beyond placing two attribute assignments and two docstrings. The 150-line-and-150-line-of-logic trigger for Worker 1 (BUILD.md line 401) does not apply — no existing file at 150+ lines is touched.
- **Worker 3 (review pass).** Helper **skipped with reason**. BUILD.md line 406 says Worker 3 must run the helper when a slice adds a new `.py` file "unless it is a pure-class-definition module (only `class` declarations with docstrings, no logic)." Slice 1 ships exactly that shape: one `class DjangoStrawberryFrameworkConfig(AppConfig)` declaration with a class docstring, two class-level constant assignments, a module docstring, and a single import — no `def` bodies, no control flow, no branches, no `getattr` / reflection, no Django ORM markers, no calls of interest. The "pure-class-definition module" exception applies. Worker 3 records the skip in the review section per BUILD.md line 411: "Helper skipped: pure-class-definition module per BUILD.md line 406 — `DjangoStrawberryFrameworkConfig` is one class with two class-level attribute assignments and two docstrings; no logic." Note for ambiguity: `django_strawberry_framework/apps.py` exists today as a 53-line docstring-only staged stub; Worker 3 reviews the **rewritten** file (~10 lines per Implementation plan's `+10 / -0` estimate at `docs/spec-017-apps-0_0_7.md:355`), which is what the "pure-class-definition module" judgment applies to. The pre-rewrite stub's 49-line docstring is not the file under review.
- **Worker 2.** Per BUILD.md line 413, Worker 2 may re-run the helper when refreshed output would help implementation; for a two-attribute class this is unnecessary. No expectation either way; if Worker 2 does run it, the resulting `docs/shadow/apps.*` files are scratch and not committed.

### Spec slice checklist (verbatim)

The spec's Slice 1 nested sub-bullets from `## Slice checklist` at `docs/spec-017-apps-0_0_7.md:55-63`, copied verbatim as `- [ ]` boxes. Worker 1 ticks each `- [x]` during final verification as the contract lands. An unticked box at final verification is either deferred with a one-line reason under `### Spec changes made (Worker 1 only)` or the slice goes `revision-needed`. Worker 3 walks this list during review; a sub-check that appears silently un-addressed in the diff is a Medium finding per BUILD.md line 382.

- [x] New flat module `django_strawberry_framework/apps.py` (placement decision: see [Decision 1](#decision-1--module-location--public-export)) housing `DjangoStrawberryFrameworkConfig`.
- [x] Implement `DjangoStrawberryFrameworkConfig(AppConfig)` with exactly **two class-level behavioral attributes** plus **two docstrings** (rev4 L2 — clarified from rev3's "four pieces of state" framing, which conflated module-scope and class-scope artifacts and undercut the documentation-vs-behavior distinction the negative-shape test relies on; the docstrings are documentation, not class state):
  - `name = "django_strawberry_framework"` — Django app-label source; matches the package directory name so `django.apps.apps.get_app_config(...)` resolves through the same string consumers type into `INSTALLED_APPS`.
  - `verbose_name = "Django Strawberry Framework"` — display name in the Django admin's "Sites" / "Apps" listings; matches the `README.md` title.
  - module docstring (one line) naming the module's purpose, e.g. `"""Django AppConfig — registers the package with Django's app loader so consumers can list it in INSTALLED_APPS and Django's check / signal hooks resolve against it."""` at the top of `apps.py`. **Required by ruff's `D100` rule** (rev4 L3 — `D100` "Missing docstring in public module" is in `pyproject.toml`'s `[tool.ruff.lint] select = [..., "D", ...]` and NOT in the `ignore` list; the per-file-ignores at `pyproject.toml:100-107` do not exempt `django_strawberry_framework/apps.py`). Do NOT suppress with `# noqa: D100` — the docstring IS the root-cause fix per [`AGENTS.md`](../AGENTS.md) line 4.
  - class docstring (one line) naming the class's purpose, e.g. `"""Register django-strawberry-framework with Django's app loader."""` directly under the `class DjangoStrawberryFrameworkConfig(AppConfig):` line. **Required by ruff's `D101` rule** (rev3 H1 — symmetric with `D100`; `D101` "Missing docstring in public class" is also in `select` and not ignored). Do NOT suppress with `# noqa: D101` — same root-cause posture as `D100`.
- [x] Do NOT implement `ready()` (per [Decision 4](#decision-4--no-readyhook-in-0_0_7)); do NOT set `default_auto_field` (per [Decision 5](#decision-5--no-default_auto_field-and-no-models)); do NOT set `label` (per [Decision 2](#decision-2--name--label--verbose_name-pinning)); do NOT set `default` at any value — neither `default = True` nor `default = False` — per [Decision 8](#decision-8--no-default-attribute) (rev6 L1 — added to close the rev4 L4 propagation gap; the consolidated negative-shape test in Slice 2 catches `default` at any value, but this checklist sub-bullet — which Worker 0 copies verbatim into the build artifact per [`docs/builder/BUILD.md`](builder/BUILD.md) line 225 — must name the forbiddance directly so Worker 2 sees it when reading top-down).
- [x] Do NOT re-export `DjangoStrawberryFrameworkConfig` from `django_strawberry_framework/__init__.py` (per [Decision 3](#decision-3--no-public-export)). The class is accessible at `django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig` for consumers who want to name it explicitly in `INSTALLED_APPS`, but Django's implicit single-AppConfig discovery means consumers writing `"django_strawberry_framework"` in `INSTALLED_APPS` get the explicit config without naming it.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/apps.py` — rewrote in place from the 53-line TODO-anchored Pseudo stub to the shipped 10-line shape Worker 1's plan pinned: one-line module docstring (D100-forced), `from django.apps import AppConfig`, `class DjangoStrawberryFrameworkConfig(AppConfig)` with a one-line class docstring (D101-forced), `name = "django_strawberry_framework"`, and `verbose_name = "Django Strawberry Framework"`.  Deleted the entire pseudo block (old lines 14-48) and the TODO anchor (old lines 51-53) per the stub's own line 48 ("When the TODO below disappears, Slice 1 has shipped").  Net diff: `+6 / -49` per `git diff --stat`.

### Tests added or updated

- None; tests land in Slice 2 per spec (`docs/spec-017-apps-0_0_7.md:64-66` Slice 2 checklist; Worker 1 plan's `### Test additions / updates` section pins "0 (tests land in Slice 2)").

### Validation run

- `uv run ruff format .` — **pass** (`105 files left unchanged`; the formatter-vs-COM812 warning is the standing repo-wide notice, not a Slice-1-introduced issue).
- `uv run ruff check --fix .` — **pass** (`All checks passed!`).  No autofixes applied to any file; D100 and D101 both satisfied by the docstrings rather than via `# noqa` suppression per rev3 H1 / rev4 L3 and AGENTS.md line 4.
- `git status --short` after both ruff invocations:
  - ` M django_strawberry_framework/apps.py` — **slice-intended** (the rewrite; appears in `### Files touched`).
  - ` D docs/builder/bld-*.md` (8 entries) and ` D docs/builder/build-016-list_field-0_0_7.md` — **pre-existing baseline**, not Slice-1-introduced.  Recorded as the in-progress build baseline at task start per AGENTS.md line 31 (the prior-build artifacts deleted during the 017 pre-flight cleanup); not reverted because they are not tool churn from this pass.
  - `?? docs/builder/bld-slice-1-module_appconfig.md` — the active artifact this report is being appended to; **slice-intended** (Worker 1 authored the plan section, Worker 2 appends this build report).
  - `?? docs/builder/build-017-apps-0_0_7.md` — the active build plan; **pre-existing baseline** from the 017 pre-flight, not Slice-1-introduced.
- No focused `pytest` run — Worker 1's plan explicitly did not request one (the optional ad-hoc import sanity-check from `### Test additions / updates` was not executed; the rewrite is mechanical enough that the Slice 2 test landing will exercise import correctness).

### Implementation notes

- **Module docstring shape**: chose the spec's em-dash form (`"""Django AppConfig — registers django-strawberry-framework with Django's app loader."""`) per Worker 1's `### Implementation discretion items` "lower-friction default."  Trimmed the spec's example one-liner from `"""Django AppConfig — registers the package with Django's app loader so consumers can list it in INSTALLED_APPS and Django's check / signal hooks resolve against it."""` to the shorter form — both satisfy `D100` under the google pydocstyle convention, and the shorter line stays under the 110-character line limit (AGENTS.md line 16) without wrapping.  The longer spec example was 167 characters and would have wrapped or violated the limit.
- **Class docstring**: used the spec's suggested wording verbatim (`"""Register django-strawberry-framework with Django's app loader."""`) per `docs/spec-017-apps-0_0_7.md:61`.
- **Import style**: single `from django.apps import AppConfig` matching the upstream `strawberry_django/apps.py` shape verbatim per the Borrowing posture's "AppConfig subclass with two attributes" bullet.  No `import django.apps` / `django.apps.AppConfig` alternative; the upstream form is shorter and is what the spec's Borrowing posture pinned.
- **Blank-line layout**: PEP 8 standard — one blank line between the module docstring and the import, two blank lines between the import and the class, one blank line between the class docstring and the first attribute assignment.  Ruff format confirmed this is the canonical shape (no rewrites on the format pass).
- **Attribute order**: `name` first, `verbose_name` second per the spec's listing at `docs/spec-017-apps-0_0_7.md:57-59` and the upstream `strawberry_django/apps.py` shape.
- **No `default` attribute / no `ready()` / no `label` / no `default_auto_field`**: class body is exactly the two attribute assignments per Decisions 2 / 4 / 5 / 8.  The Slice 2 consolidated negative-shape test will pin this.

### Notes for Worker 3

- This is a **rewrite-in-place** that removed the TODO-anchored Pseudo stub the staged-slice convention (AGENTS.md line 26) put on disk; the file is not new.  Worker 3 reviewing `git diff -- django_strawberry_framework/apps.py` will see the deleted 49-line docstring as the dominant signal — that deletion IS the slice landing per the stub's own line 48 prose, not a regression to flag.
- Helper-skip disposition: Worker 1's `### scripts/review_inspect.py disposition for Slice 1` already recorded the planned skip ("pure-class-definition module per BUILD.md line 406 — `DjangoStrawberryFrameworkConfig` is one class with two class-level attribute assignments and two docstrings; no logic").  The rewritten 10-line file matches that judgment: one class, two attribute assignments, two docstrings, one import, no `def` bodies, no control flow, no reflection, no ORM markers.  Worker 3 should record the skip with the same reason per BUILD.md line 411.
- `django_strawberry_framework/__init__.py` was not modified (Decision 3); `git diff -- django_strawberry_framework/__init__.py` is empty per BUILD.md's `### Public-surface check`.
- `examples/fakeshop/config/settings.py` was not modified (Decision 7); the existing `"django_strawberry_framework"` entry in `INSTALLED_APPS` now resolves to the explicit `DjangoStrawberryFrameworkConfig` through Django's implicit single-AppConfig discovery.
- No `pytest` or focused-test run this pass — Slice 1 ships the class without tests; Slice 2 is the test landing.

### Notes for Worker 1 (spec reconciliation)

None.  The spec, the plan, and the implementation are mutually consistent; no spec gap, conflict, or unstated assumption surfaced during the rewrite.  The only discretion items exercised were the two docstring wordings (both within the discretion Worker 1's plan explicitly authorized) and the blank-line layout (canonical PEP 8 / ruff format default).

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- No new duplication. The class is two attribute assignments + two docstrings + one import; nothing to consolidate. The plan's pre-flagged non-duplication of `"django_strawberry_framework"` between `apps.py:9` (`name` attribute, Django app-label key) and `django_strawberry_framework/__init__.py:16` (`logging.getLogger("django_strawberry_framework")`, consumer logger-name key) is the correct call — two distinct consumer contracts happen to share a string but factoring through a module constant would couple a logger rename to an AppConfig rename, which is wrong. Confirmed against the diff: no module-constant extraction was attempted, and none should be.
- The class docstring at `apps.py:7` (`"""Register django-strawberry-framework with Django's app loader."""`) and the module docstring at `apps.py:1` (`"""Django AppConfig — registers django-strawberry-framework with Django's app loader."""`) overlap semantically but say different things — the module docstring names the module's purpose, the class docstring names the class's purpose. The overlap is intrinsic to `D100`/`D101` both firing on a one-class module; not a DRY defect.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` produces empty output. `__all__` (lines 28-37) and the re-export list (lines 18-24) are unchanged. Confirmed per Decision 3 / DoD item 2 / DoD item 12 / Slice 1 checklist sub-bullet "Do NOT re-export `DjangoStrawberryFrameworkConfig` from `django_strawberry_framework/__init__.py`."

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- Diff matches the plan's `+10 / -0` line-delta target almost exactly (actual `+6 / -49` reflecting the staged-stub deletion; the `-49` is the stub teardown the stub's own line 48 prose authorized and is not a regression).
- Module docstring trim from the spec's 167-character example to the 91-character shipped form is the right call — both satisfy `D100`, and the shipped form stays under the 110-character `AGENTS.md` line 16 ceiling without wrapping; Worker 2 surfaced the trim and its reason in `### Implementation notes` so the choice is auditable.
- Class docstring uses the spec's suggested wording verbatim (`docs/spec-017-apps-0_0_7.md:61`); no rephrasing, no `# noqa: D101` suppression — the root-cause docstring per rev3 H1 / AGENTS.md line 4.
- Import shape `from django.apps import AppConfig` matches the upstream `strawberry_django/apps.py` exactly per the Borrowing posture; class name `DjangoStrawberryFrameworkConfig` matches the spec's pinning; attribute order (`name` then `verbose_name`) matches the spec's listing at `docs/spec-017-apps-0_0_7.md:57-59`.
- Class body contains exactly the two behavioral attribute assignments at `apps.py:9-10`; no `ready()`, no `label`, no `default_auto_field`, no `default`. The Slice 2 consolidated negative-shape test (`test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`) will pin this; nothing in the Slice 1 diff would make that test fail.
- `examples/fakeshop/config/settings.py:48` (`"django_strawberry_framework"` in `INSTALLED_APPS`) is unchanged per Decision 7; `git status --short` confirms only `django_strawberry_framework/apps.py` and the two pre-existing baseline untracked builder files appear, with no settings drift.
- `uv run ruff format --check django_strawberry_framework/apps.py` reports `1 file already formatted`; `uv run ruff check django_strawberry_framework/apps.py` reports `All checks passed!` (read-only verification, no `--fix` invoked, per BUILD.md Worker 3 forbidden-actions list).

### Spec slice checklist verification (verbatim boxes against the diff)

Walked all four `- [ ]` items in the Plan's `### Spec slice checklist (verbatim)`:

- "New flat module `django_strawberry_framework/apps.py` ... housing `DjangoStrawberryFrameworkConfig`." — addressed at `apps.py:6` (`class DjangoStrawberryFrameworkConfig(AppConfig):`); the file is in the spec-pinned flat-root location per Decision 1.
- "Implement `DjangoStrawberryFrameworkConfig(AppConfig)` with exactly two class-level behavioral attributes plus two docstrings" — addressed at `apps.py:1` (module docstring, `D100`-satisfying), `apps.py:7` (class docstring, `D101`-satisfying), `apps.py:9` (`name = "django_strawberry_framework"`), `apps.py:10` (`verbose_name = "Django Strawberry Framework"`). String values match the spec character-for-character; both docstrings are one-line per the checklist; neither uses `# noqa` suppression per rev3 H1 / rev4 L3.
- "Do NOT implement `ready()`; do NOT set `default_auto_field`; do NOT set `label`; do NOT set `default` at any value" — addressed: `apps.py` ends at line 10; no method definitions, no further attribute assignments. The class body is exactly the two attributes.
- "Do NOT re-export `DjangoStrawberryFrameworkConfig` from `django_strawberry_framework/__init__.py`." — addressed: `git diff -- django_strawberry_framework/__init__.py` is empty.

No silently un-addressed sub-checks.

### Static-helper disposition

Helper skipped per BUILD.md line 406. Independently confirmed against the diff: post-rewrite `django_strawberry_framework/apps.py` contains one import (line 3), one `class` declaration (line 6), one class docstring (line 7), two class-level attribute assignments (lines 9-10), and one module docstring (line 1). No `def` bodies, no control flow, no `if`/`for`/`try`/`while`, no `getattr`/`hasattr`/`isinstance`/`setattr` reflection, no Django ORM markers (`QuerySet`, `select_related`, `_meta`, `get_queryset`, etc.), no `OptimizationPlan` / `DjangoType` / registry markers. This is a pure-class-definition module; the helper would add zero signal. Skip-and-record per BUILD.md line 411 with reason: "pure-class-definition module per BUILD.md line 406 — `DjangoStrawberryFrameworkConfig` is one class with two class-level attribute assignments and two docstrings; no logic." Worker 1's plan pre-recorded the same disposition under `### scripts/review_inspect.py disposition for Slice 1`; Worker 3's independent inspection confirms it.

### Temp test verification

None; no temp tests used. Slice 1 is a pure-class-definition rewrite with no non-obvious failure modes; the Slice 2 test landing will exercise import correctness, attribute values, subclass relationship, registry pickup, and the consolidated negative-shape contract. A temp test now would duplicate Slice 2.

### Notes for Worker 1 (spec reconciliation)

None.

### Review outcome

`review-accepted`. Every spec slice checklist sub-bullet is reflected in the diff. No High, Medium, or Low findings. DRY is clean (no duplication risk introduced; the two pre-flagged non-duplication calls were both respected). Public surface (`__init__.py`, `__all__`) is untouched per Decision 3. Static helper correctly skipped as pure-class-definition per BUILD.md line 406. Status updated to `review-accepted`.

---

## Final verification (Worker 1)

### Spec slice checklist (verbatim) — final walk against the diff

All four `- [ ]` boxes in the Plan's `### Spec slice checklist (verbatim)` ticked in place; each confirmed against `git diff -- django_strawberry_framework/apps.py` and a fresh read of the post-rewrite file:

- "New flat module `django_strawberry_framework/apps.py` ... housing `DjangoStrawberryFrameworkConfig`." — landed at `apps.py:6` (`class DjangoStrawberryFrameworkConfig(AppConfig):`). Flat root location per Decision 1; no nested subpackage was introduced.
- "Implement `DjangoStrawberryFrameworkConfig(AppConfig)` with exactly **two class-level behavioral attributes** plus **two docstrings**." — landed: module docstring at `apps.py:1` (`"""Django AppConfig — registers django-strawberry-framework with Django's app loader."""`, D100-satisfying, no `# noqa`); class docstring at `apps.py:7` (`"""Register django-strawberry-framework with Django's app loader."""`, D101-satisfying, no `# noqa`); `name = "django_strawberry_framework"` at `apps.py:9`; `verbose_name = "Django Strawberry Framework"` at `apps.py:10`. Both attribute values match the spec character-for-character (verified against Decision 2 at `docs/spec-017-apps-0_0_7.md:226-238` and the consumer-string match in `examples/fakeshop/config/settings.py:48`).
- "Do NOT implement `ready()`; do NOT set `default_auto_field`; do NOT set `label`; do NOT set `default` at any value." — landed: file terminates at line 10. No `def` bodies, no further attribute assignments. Class body is exactly the two pinned attributes. The Slice 2 consolidated negative-shape test (`test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`) will assert this contract against the runtime `__dict__`; the Slice 1 diff supplies the shape the test will then pin.
- "Do NOT re-export `DjangoStrawberryFrameworkConfig` from `django_strawberry_framework/__init__.py`." — `git diff -- django_strawberry_framework/__init__.py` produces empty output; `__all__` (lines 28-37) and the re-export block (lines 18-24) are byte-identical to baseline.

No silently un-ticked boxes; no deferrals required.

### DRY check across this slice and prior accepted slices

Prior accepted slice set is **empty** (Slice 1 is the first slice of build-017; the pre-flight cleanup deleted all prior-build artifacts on 2026-05-21 per the build plan preamble). Cross-slice DRY scan therefore reduces to scanning Slice 1 against the existing committed package surface.

Scan of the post-rewrite `django_strawberry_framework/apps.py` (10 lines: module docstring, blank, import, two blanks, class declaration, class docstring, blank, two attribute assignments, trailing newline) against the rest of `django_strawberry_framework/`:

- `name = "django_strawberry_framework"` at `apps.py:9` shares the literal string with `logging.getLogger("django_strawberry_framework")` at `__init__.py:16`. Worker 1's plan pre-flagged this as deliberate non-duplication (the two strings are unrelated consumer contracts — a Django app-label vs a logger-name key — that happen to collide; consolidating through a module constant would wrongly couple a logger rename to an AppConfig rename). Worker 3's `### DRY findings` reached the same conclusion. Confirmed in the final-verification scan: no module-constant extraction was attempted, none should be.
- The class docstring at `apps.py:7` and module docstring at `apps.py:1` overlap semantically (both name the AppConfig's purpose). The overlap is intrinsic to `D100`/`D101` both firing on a one-class module; not a DRY defect, not consolidatable without violating one of the two pydocstyle rules the rev3 H1 / rev4 L3 spec edits made load-bearing.
- No other package module ships an `AppConfig`; no helper, registry, or shared constant in `conf.py` / `exceptions.py` / `registry.py` / `scalars.py` / `list_field.py` / `optimizer/` / `types/` / `utils/` reaches into the Django app-loader surface. Slice 1 is correctly siloed.

No new duplication introduced. Nothing to consolidate.

### Existing tests still pass

Ran the focused init-pin suite first to confirm the public-surface contract is intact, then the full package test tree to confirm the import surface is unbroken:

- `uv run pytest --no-cov tests/base/test_init.py -x -q` — **pass** (4 passed in 0.06s). Confirms `__all__`, `__version__`, and the public re-exports are byte-identical to baseline; Slice 1's no-public-surface contract (Decision 3, DoD item 12) is intact.
- `uv run pytest --no-cov tests/ -x -q` — **pass** (685 passed, 2 skipped, 4 warnings in 14.49s). The 2 skips are the pre-existing `tests/types/test_converters.py` skips unrelated to this slice. The 4 warnings are the pre-existing `Model 'test_choice_enums._owner' was already registered` model-reload notices, also unrelated to this slice. No new failures, no new warnings introduced by `apps.py`.

The `--no-cov` flag is mandatory per BUILD.md line 109 (the only permitted coverage-shaped flag) because `pytest.ini`'s `addopts` auto-applies `--cov`; coverage enforcement is CI's gate, not this pass's.

### Spec reconciliation

Walked Worker 2's `### Notes for Worker 1 (spec reconciliation)` section (says `None.`) and Worker 3's same-named section (says `None.`). Neither worker surfaced a spec gap, conflict, or unstated assumption. Independently re-read the spec's status / header lines (`docs/spec-017-apps-0_0_7.md:1-6`) on this spawn per the "Spec status-line re-verification" rule in `docs/builder/worker-1.md` lines 40-48: `Status: draft (revision 6, post-rev5 build-readiness audit)` is still accurate — Slice 1 has shipped but Slices 2 / 3 have not, so the spec remains in draft for the active build cycle. No status edit needed.

### Final status

`final-accepted`. Every spec slice checklist sub-bullet ticked in the Plan section; no DRY drift against the (empty) prior-slice set or the existing package surface; package test suite passes intact (685 passed, 2 skipped); no spec reconciliation required. Artifact `Status:` updated to `final-accepted`.

### Summary

Slice 1 shipped `django_strawberry_framework/apps.py` in its final 10-line shape: a one-line `D100`-satisfying module docstring, a single `from django.apps import AppConfig` import, and the `DjangoStrawberryFrameworkConfig(AppConfig)` class with a one-line `D101`-satisfying class docstring, `name = "django_strawberry_framework"`, and `verbose_name = "Django Strawberry Framework"`. The TODO-anchored Pseudo stub the staged-slice convention (AGENTS.md line 26) put on disk was deleted in the same change — its line 48 prose explicitly authorized that teardown as the act flipping the file from staged-stub to shipped. No `ready()`, no `label`, no `default_auto_field`, no `default` (any value); no re-export from `django_strawberry_framework/__init__.py`; no fakeshop `INSTALLED_APPS` edit. Slice 2 (the consolidated negative-shape and four positive tests) will pin the shipped contract.

### Spec changes made (Worker 1 only)

None.
````
