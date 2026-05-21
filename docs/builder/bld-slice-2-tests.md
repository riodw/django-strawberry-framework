````text
# Build: Slice 2 — Tests

Spec reference: `docs/spec-017-apps-0_0_7.md` (Slice 2 sub-bullets at lines 64-66; Test plan at lines 374-396; Decisions 2 / 4 / 5 / 8)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.** The spec's [Test plan](../spec-017-apps-0_0_7.md#test-plan) pins the contract — the spec's "follows the convention" pointer at `docs/spec-017-apps-0_0_7.md:99` names `tests/test_list_field.py` as the existing model for a flat single-file Layer-3 module's test home, and `docs/TREE.md:453` enshrines the `tests/test_<module>.py` rule. The staged-stub at `tests/test_apps.py:1-108` (AGENTS.md line 26 TODO-anchored Pseudo block — analogous to how `django_strawberry_framework/apps.py` existed pre-Slice 1) already contains: (a) the 5-test plan in prose with per-test contract pins (lines 7-63), (b) the spec-citation rationale (Decisions 1 / 2 / 4 / 5 / 8), (c) the canonical pseudo-block for all 5 tests at lines 77-108, and (d) the key→Decision map at lines 99-104. The stub's prose IS the contract; Worker 2 implements what the stub previews rather than re-deriving the test shapes from the spec. The implementer should also skim the docstring of `tests/test_list_field.py:1-58` for the "what to put in a flat single-file test module's docstring" tone — Worker 2's test-module docstring should follow a similar shape (spec citation + plan summary) but may be much shorter (5 tests vs. 22).
- **New helpers justified.** None. The 5 tests are short and direct; no shared fixture, helper function, or module-level constant is justified. The repeated string `"django_strawberry_framework"` appears 3 times across the planned tests (the `name` value pinned in `test_pins_name_and_verbose_name`, the registry-lookup key in `test_resolves_through_django_app_registry`, and the import path in the top-level `from django_strawberry_framework.apps import ...`). Each occurrence pins a distinct contract — extracting to a module-level constant `APP_LABEL = "django_strawberry_framework"` would couple the three pins together and obscure the failure mode (a regression that changed only the registry lookup key but not the `name` attribute would still pass the consolidated constant assertion). Worker 2 should write the string inline at each pin site; see also the Slice 1 DRY analysis (`docs/builder/bld-slice-1-module_appconfig.md` lines 13-15) for the parallel reasoning against factoring the `name` literal across `apps.py:9` and `__init__.py:16`.
- **Duplication risk avoided.** Four specific risks the naive implementation could introduce, and how the plan blocks them:
  1. **`pytest.mark.parametrize` fan-out on the negative-shape test.** The Implementation-plan table at `docs/spec-017-apps-0_0_7.md:356` AND DoD item 4 at `docs/spec-017-apps-0_0_7.md:457` both say "5 tests"; `pytest.mark.parametrize` over the four-key forbidden set would yield 4 separate pytest items for that one test name, collecting to 8 items total (4 positive + 4 parametrized) instead of 5. Rev4 Informational #2 (recorded in the spec at line 25) explicitly pins the single-test loop idiom for this reason. Worker 2 implements ONE `def test_…` function with a `for key, why in forbidden.items(): assert key not in DjangoStrawberryFrameworkConfig.__dict__, …` loop body — NOT `@pytest.mark.parametrize`. The stub's pseudo-block at `tests/test_apps.py:98-108` already shows the loop form; mirror that shape verbatim.
  2. **Accidentally tightening the iteration set to include `__doc__`.** Spec lines 66 and 391 are both explicit that the implicit `__doc__` key (populated by the class docstring `D101` requires per rev3 H1) is **intentionally NOT** in the four-key forbidden set — "no extra AppConfig attributes" means no extra **behavioral** class attributes, and documentation is not behavior. Adding `"__doc__"` to the iterated set would fail the test as soon as it runs (the class docstring populates `__doc__`), AND would silently invert the spec's documentation-vs-behavior distinction. Worker 2 ships the four-key set exactly: `{"ready", "label", "default_auto_field", "default"}` — no more, no less.
  3. **Asserting on the inherited `AppConfig` base attributes.** The `__dict__` discriminator catches additions on the subclass only; inherited attributes (e.g., `AppConfig.path`, `AppConfig.models_module`) live on the base class and are NOT in `DjangoStrawberryFrameworkConfig.__dict__`. Worker 2 must use `__dict__` (not `dir()` and not `hasattr()`) so the negative test catches subclass-body additions without false-positiving on the inherited surface. The stub's pseudo-block at line 106 already uses `__dict__`; mirror it.
  4. **Re-stating the four-key forbidden set in multiple test sites.** If Worker 2 later inlines a smoke-check of "no `ready()`" in some other test, the second iteration would duplicate the contract. The plan's single source of truth is the consolidated test; do NOT scatter `assert "ready" not in __dict__` lines across other tests. The 4 positive tests assert what IS present; the 1 negative test asserts what is NOT — symmetric and non-overlapping.

### Implementation steps

Line numbers below are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written.

1. **Replace the staged-stub test module body in `tests/test_apps.py:1-108`.** The file already exists as a TODO-anchored Pseudo block under the AGENTS.md line 26 staged-slice convention (the stub at `tests/test_apps.py:1-71` contains the prose plan with per-test contract pins; the TODO anchor at lines 73-75; the canonical pseudo-block for all 5 tests at lines 77-108). Worker 2 rewrites the entire file: a one-line module docstring (e.g., `"""Tests for ``django_strawberry_framework.apps`` — Django AppConfig."""`) — required by ruff's `D100` rule (the same gate that forced the `apps.py` module docstring per Slice 1); the `import django.apps` import and the `from django_strawberry_framework.apps import DjangoStrawberryFrameworkConfig` import; and the 5 test functions matching the pseudo-block at lines 77-108. Delete the entire pseudo-block prose at lines 7-63, the bottom TODO anchor at lines 73-75, and the pseudo-block at lines 77-108 — once the implementation lands, the staged-stub framing is no longer correct (per the stub's own line 70: "When the TODO below disappears, Slice 2 has shipped"; deleting the TODO IS the act that flips the file from staged-stub to shipped).
2. **Test function names** (pinned by the spec at `docs/spec-017-apps-0_0_7.md:384-391` and the stub at `tests/test_apps.py:9-46`):
   - `test_djangostrawberryframeworkconfig_importable_from_apps_module`
   - `test_djangostrawberryframeworkconfig_is_appconfig_subclass`
   - `test_djangostrawberryframeworkconfig_pins_name_and_verbose_name`
   - `test_djangostrawberryframeworkconfig_resolves_through_django_app_registry`
   - `test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`
   No renaming; the spec, the stub, and the failure-mode descriptions (e.g., DoD item 4 at spec line 457) all reference these exact names.
3. **Test body shapes** (the stub's pseudo-block at `tests/test_apps.py:77-108` is canonical; the spec's Test plan at `docs/spec-017-apps-0_0_7.md:382-391` is the prose contract):
   - **`test_djangostrawberryframeworkconfig_importable_from_apps_module`** — the top-level `from django_strawberry_framework.apps import DjangoStrawberryFrameworkConfig` is the assertion (if it fails, pytest collection fails). The test body can be the minimal `assert DjangoStrawberryFrameworkConfig is not None` per the stub at line 85 to give the test something to do at call time.
   - **`test_djangostrawberryframeworkconfig_is_appconfig_subclass`** — `assert issubclass(DjangoStrawberryFrameworkConfig, django.apps.AppConfig)`. Note `django.apps.AppConfig` (not `django.apps.config.AppConfig` via direct submodule import) so the test would fail if a refactor accidentally inherits from the implementation class.
   - **`test_djangostrawberryframeworkconfig_pins_name_and_verbose_name`** — two attribute equality asserts; `name == "django_strawberry_framework"` and `verbose_name == "Django Strawberry Framework"`. Per Decision 2 at spec lines 226-249; the strings MUST match `django_strawberry_framework/apps.py:9-10` character-for-character.
   - **`test_djangostrawberryframeworkconfig_resolves_through_django_app_registry`** — `config = django.apps.apps.get_app_config("django_strawberry_framework"); assert isinstance(config, DjangoStrawberryFrameworkConfig)`. This is the load-bearing assertion that Django's app loader actually picked up the explicit class (rather than the implicit fallback that synthesizes a class with `name = "django_strawberry_framework"` but is NOT an instance of the explicit `DjangoStrawberryFrameworkConfig`). Without this test, the explicit AppConfig could silently fail to register and the implicit one could stand in unnoticed.
   - **`test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`** — a single test function with a plain `for` loop (NOT `@pytest.mark.parametrize`; see DRY risk #1 above). The body iterates the four-key forbidden mapping and asserts each key is absent from `DjangoStrawberryFrameworkConfig.__dict__`. The key→Decision map is pinned in the stub at lines 99-104 and reproduced here for Worker 2 to encode verbatim:
     ```text
     forbidden = {
         "ready": "Decision 4 (no AppConfig.ready() body in 0.0.7)",
         "label": "Decision 2 (default last-segment label is already unique)",
         "default_auto_field": "Decision 5 (package ships zero Django models)",
         "default": "Decision 8 (no `default` attribute at any value, rev4 L4)",
     }
     for key, why in forbidden.items():
         assert key not in DjangoStrawberryFrameworkConfig.__dict__, (
             f"{key!r} is forbidden on DjangoStrawberryFrameworkConfig: {why}"
         )
     ```
     The fail message names the offending key AND the Decision that forbids it per the spec's "fail message naming the offending key and the Decision that forbids it" instruction at `docs/spec-017-apps-0_0_7.md:391`. The iterated set is exactly the four keys above — `__doc__` is intentionally excluded per DRY risk #2 / spec lines 66 and 391.
4. **No `@pytest.mark.django_db` decorator on any test.** The 5 tests do not exercise the Django ORM; they only exercise (a) Python-level class introspection (`__dict__`, `issubclass`, attribute access) and (b) Django's app-registry, which `pytest-django` populates once per session via `django.setup()` (driven by `pytest.ini`'s `DJANGO_SETTINGS_MODULE = config.settings` line and the on-pythonpath `examples/fakeshop/config/settings.py`). The registry is populated before any test in the suite runs; no per-test database transaction is required. Compare `tests/test_list_field.py` which DOES use `@pytest.mark.django_db` on its model-touching tests — Slice 2 does NOT, because no test reads or writes a Django model.
5. **No autouse `_isolate_global_registry` fixture.** `tests/test_list_field.py:60-70` defines this fixture because its tests declare ephemeral `DjangoType` subclasses at function scope and would otherwise leak into the package's global type registry. Slice 2's tests touch only `django.apps.apps` (Django's app registry, NOT `django_strawberry_framework.registry`'s type registry); no fixture is needed. Do NOT copy that fixture into `tests/test_apps.py` defensively — extra fixtures the tests do not use are noise.
6. **No fakeshop / example-project test.** Per the spec at `docs/spec-017-apps-0_0_7.md:393-395` and Decision 7's rejection of an `examples/fakeshop/tests/test_apps.py` mirror at lines 328-331. The system-under-test is the package's AppConfig; the package-internal `tests/` tree is the canonical home (AGENTS.md line 6). The existing fakeshop live `/graphql/` HTTP tests already exercise the package end-to-end through `INSTALLED_APPS`; the registry-pickup test in step 3 above is the direct contract pin for the AppConfig surface.
7. **Run the per-pass gate.** `uv run ruff format .` and `uv run ruff check --fix .` (per BUILD.md `### Validation run`). After running, `git status --short` and confirm only `tests/test_apps.py` (and the artifact, which Worker 2 also writes to) appears in the diff — any other file that surfaces is unrelated tool churn Worker 2 owns reverting per BUILD.md line 248 ("Tool-induced drift is Worker 2's responsibility to own at this boundary"). Worker 2 may, optionally, run `uv run pytest --no-cov tests/test_apps.py -x -q` to confirm the 5 tests pass — focused, no coverage flags per BUILD.md line 100 ("the only permitted coverage-shaped flag" is `--no-cov`).

### Test additions / updates

- **`tests/test_apps.py` (new — staged stub rewrite).** 5 tests total: 4 positive + 1 consolidated negative-shape. Function names and contract shapes pinned in [Implementation steps](#implementation-steps) above. The file replaces the existing 108-line TODO-anchored Pseudo stub; the net diff is approximately `+50 / -108` after the rewrite (stub teardown dominates the line count; the rewritten file is short).
- **No changes to `tests/base/test_init.py`.** Per Decision 3 at `docs/spec-017-apps-0_0_7.md:257-270` and DoD item 3 at `docs/spec-017-apps-0_0_7.md:456`. The `__all__` assertion at `tests/base/test_init.py:35-44` is byte-identical to baseline after Slice 2.
- **No changes to other test files.** Slice 2 lands one new test module and touches nothing else. No regression-fix piggyback opportunities; the staged-stub teardown IS the slice.
- **Temp / scratch tests for development.** None required. The 5 tests in Slice 2 collectively exercise every line of `django_strawberry_framework/apps.py`: import (line 3) + class declaration (line 6) + class docstring (line 7) + `name` (line 9) + `verbose_name` (line 10) + module docstring (line 1) are all referenced by the 4 positive tests, and the consolidated negative-shape test exercises the class-body shape directly via `__dict__`. Worker 2 may optionally run `uv run pytest --no-cov tests/test_apps.py -x -q` after the rewrite as a sanity check; not committed as a temp test.

### Implementation discretion items

Items where Worker 1 has assessed and decided the choice belongs to Worker 2 (per BUILD.md "Implementation discretion items" — only stylistic / equivalent-shape preferences, never architectural questions):

- **Forbidden-set container shape.** Python sets are unordered for iteration; the stub at `tests/test_apps.py:99-104` uses a `dict` (key → reason) so the fail message can include the Decision citation. Worker 2 may keep the `dict` shape (recommended — gives the test fail message the per-key Decision string for free) OR substitute a `tuple` / `frozenset` of `(key, reason)` pairs / a literal set with a parallel lookup. The contract is "iterate the four keys and assert each is absent with a Decision-citing fail message"; the container shape is stylistic. The `dict` form is the lowest-friction default because the stub already uses it.
- **Test-module docstring wording.** The stub's docstring at `tests/test_apps.py:1-71` is a 71-line plan-document docstring; the rewritten Slice-2 file does NOT need to keep that prose (the spec, the build artifact, and this plan are the durable record). Worker 2 ships a one-line `D100`-satisfying module docstring — wording is at Worker 2's discretion. Suggested defaults: `"""Tests for ``django_strawberry_framework.apps`` — Django AppConfig."""` (em-dash style matching the lead-in shape of `tests/test_list_field.py:1`'s docstring) or `"""Tests for the Django AppConfig at ``django_strawberry_framework.apps``."""` (descriptive style). Either passes `D100`.
- **Whether to add per-test docstrings.** The stub's pseudo-block at lines 83-108 has no per-test docstrings; the test function names are descriptive enough. The repo's pydocstyle gate (`pyproject.toml [tool.ruff.lint.per-file-ignores]` at lines 100-107) exempts `tests/*` from the `D` family per the standard test-file allowance — Worker 2 may add per-test docstrings for clarity (descriptive of the contract pin) or omit them (rely on the function name to convey intent). The lower-friction default is to omit; the higher-clarity default is to add one-line docstrings explaining what each test pins. Either is correct.
- **Import grouping order.** Two imports needed: `import django.apps` (stdlib-after-third-party — `django.apps` is a Django module so it lands in the third-party / external group) and `from django_strawberry_framework.apps import DjangoStrawberryFrameworkConfig` (first-party `django_strawberry_framework` group). Ruff's isort config (`pyproject.toml [tool.ruff.lint.isort]`) will sort these into the canonical order on the format pass; Worker 2 may write them in any order before running `uv run ruff format .` (the format pass will normalize).
- **`pytest.fixture` shape.** None needed (see Implementation step 5). If Worker 2 has a strong reason to add one (e.g., a fixture that re-reads `django.apps.apps.get_app_config(...)` once and shares it across the 4 positive tests), the choice is at their discretion — but the 5 tests are already trivially fast (no DB, no ORM, no schema construction), and the test isolation benefit of fresh per-test lookups outweighs the duplication-avoidance benefit. Default: no fixture.

Items NOT in Worker 2's discretion (these are spec-pinned and any deviation requires a Worker 1 spec edit through `### Spec changes made (Worker 1 only)`):

- The 5 test function names (pinned in Slice 2 checklist at spec lines 64-66 and Test plan at lines 384-391).
- The iterated forbidden-key set `{"ready", "label", "default_auto_field", "default"}` — exactly these four keys, no more (no `__doc__`), no fewer (Decisions 2 / 4 / 5 / 8 each forbid one of these).
- The single-pytest-item idiom for the negative-shape test (plain loop, NOT `pytest.mark.parametrize`; per rev4 Informational #2 / spec line 25).
- The `__dict__` discriminator (NOT `dir()` / `hasattr()` / `getattr()`) for the negative-shape test, per spec line 391.
- The fail message naming the offending key AND the Decision that forbids it, per spec line 391.
- The `name` / `verbose_name` attribute values pinned in `test_pins_name_and_verbose_name` (`"django_strawberry_framework"` / `"Django Strawberry Framework"`); per Decision 2.
- The lookup string `"django_strawberry_framework"` for `django.apps.apps.get_app_config(...)` (per Decisions 2 / 7).

### `scripts/review_inspect.py` disposition for Slice 2

Per BUILD.md "When to run the helper during build" at lines 398-411:

- **Worker 1 (this pass).** Helper NOT run. The spec / staged-stub already pins the test shape; Worker 1 has no logic to plan beyond placing 5 short test functions. The 150-line-and-150-line-of-logic trigger for Worker 1 at BUILD.md line 401 does not apply — the planned file is short and lives outside `django_strawberry_framework/`.
- **Worker 3 (review pass).** Helper **skipped with reason**. BUILD.md lines 406-409 lay out the new-file / size triggers; for files OUTSIDE `django_strawberry_framework/`, the trigger is "50 or more lines of new logic" (BUILD.md line 409). The planned `tests/test_apps.py` rewrite is approximately `+50 / -108` per the spec's Implementation-plan table at `docs/spec-017-apps-0_0_7.md:356` (estimated `+60 / -0` for the new shape; the stub-deletion adds the `-108`). Most of the `+50` is test scaffolding (imports, function `def` lines, asserts, fail-message f-strings) — NOT "logic" in the helper's sense (no control flow beyond a single 4-iteration `for` loop, no reflection beyond `__dict__` membership checks, no Django ORM markers, no `getattr` / `hasattr` patterns). The file consists of 4 trivially-shaped positive tests (one assertion each or two for `pins_name_and_verbose_name`) and 1 negative-shape test with a plain `for` loop. Worker 3 records the skip per BUILD.md line 411: "Helper skipped: test module with ~50 lines of scaffolding (4 positive tests + 1 loop-based negative test); the 50-line-of-logic trigger at BUILD.md line 409 measures logic, not scaffold lines — the file has no control flow beyond a 4-iteration `for` loop, no reflection beyond `__dict__` membership checks, no Django ORM markers, and no calls of interest." If Worker 2's implementation surprises and adds non-trivial logic (e.g., a conftest fixture, a parametrized helper, custom assertion machinery), Worker 3 reassesses and runs the helper.
- **Worker 2.** Per BUILD.md line 413, Worker 2 may re-run the helper when refreshed output would help implementation; for 5 short test functions this is unnecessary. No expectation either way; if Worker 2 does run it, the resulting `docs/shadow/test_apps.*` files are scratch and not committed.

### Pre-existing test-runner configuration relied on by Slice 2

- **`pytest-django` and `django.setup()`.** `pytest.ini` at `pytest.ini:2` declares `DJANGO_SETTINGS_MODULE = config.settings`, which `pytest-django` reads to call `django.setup()` once per session before any test runs. `django.setup()` populates `django.apps.apps` with every `AppConfig` named in `INSTALLED_APPS`. Slice 2's `test_djangostrawberryframeworkconfig_resolves_through_django_app_registry` relies on this — `examples/fakeshop/config/settings.py:48` already declares `"django_strawberry_framework"` in `INSTALLED_APPS`, and once Slice 1's `apps.py` is on disk (which it is, per `docs/builder/bld-slice-1-module_appconfig.md` status `final-accepted`), Django's implicit single-AppConfig discovery resolves the consumer string to `DjangoStrawberryFrameworkConfig`. No new conftest, no new fixture, no `pytest.ini` edit needed; the pre-existing setup carries Slice 2.
- **`pythonpath = examples/fakeshop`.** `pytest.ini:3` ensures `config.settings` resolves to `examples/fakeshop/config/settings.py`. Slice 2 does not need to know this beyond confirming it is in place.
- **No root `conftest.py`.** Confirmed via `ls /Users/riordenweber/projects/django-strawberry-framework/conftest.py` — does not exist. Slice 2 does not need to add one; the per-tree fixtures in `tests/`, `tests/types/`, `tests/optimizer/`, etc. are self-contained.

### Spec slice checklist (verbatim)

The spec's Slice 2 nested sub-bullets from `## Slice checklist` at `docs/spec-017-apps-0_0_7.md:64-66`, copied verbatim as `- [ ]` boxes. Worker 1 ticks each `- [x]` during final verification as the contract lands. An unticked box at final verification is either deferred with a one-line reason under `### Spec changes made (Worker 1 only)` or the slice goes `revision-needed`. Worker 3 walks this list during review; a sub-check that appears silently un-addressed in the diff is a Medium finding per BUILD.md line 382.

- [x] Slice 2: Tests
- [x] New test module `tests/test_apps.py` covering the four contracts pinned in [Test plan](#test-plan): importable from `django_strawberry_framework.apps`, subclass of `django.apps.AppConfig`, `name` / `verbose_name` attribute values, and Django registry pickup (`django.apps.apps.get_app_config("django_strawberry_framework")` returns an instance of `DjangoStrawberryFrameworkConfig`).
- [x] One **consolidated** negative-shape test (rev2 H2): assert that `DjangoStrawberryFrameworkConfig.__dict__` contains none of the four **behavioral** keys this spec forbids — `"ready"` (per [Decision 4](#decision-4--no-readyhook-in-0_0_7)), `"label"` (per [Decision 2](#decision-2--name--label--verbose_name-pinning)), `"default_auto_field"` (per [Decision 5](#decision-5--no-default_auto_field-and-no-models)), and `"default"` (per [Decision 8](#decision-8--no-default-attribute)). Mechanism: a single test function (one pytest item, NOT a `pytest.mark.parametrize` four-way fan-out — pinning this here so the "5 tests" count in [Implementation plan](#implementation-plan) and [Definition of done](#definition-of-done) matches pytest's collection output) that loops over `{"ready", "label", "default_auto_field", "default"}` and asserts `key not in DjangoStrawberryFrameworkConfig.__dict__` for each, with a fail message naming the offending key and the Decision that forbids it. Checks the class body explicitly, not the inherited base attributes which are always present. **The implicit `__doc__` key (populated by the class docstring required per rev3 H1) is NOT in the forbidden set** — "no extra AppConfig attributes" means no extra **behavioral** class attributes, not "no class docstring"; `__doc__` is documentation, not behavior, and is mandated by ruff's `D101`. If a future card relaxes any of the four forbidden keys, that card's spec updates this test in the same slice. Folding all four forbidden keys into one test (rather than four separate tests) keeps Slice 2's count compact and means the test name (`test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes`) names the contract — "exactly the two behavioral attributes pinned in Decision 2 plus the class / module docstrings required by D101; nothing more" — instead of the failure mode.

---

## Build report (Worker 2)

### Files touched

- `tests/test_apps.py` — rewrote in place from the 108-line TODO-anchored Pseudo stub (AGENTS.md line 26 convention) to the 37-line shipped shape: one-line `D100` module docstring, `import django.apps`, `from django_strawberry_framework.apps import DjangoStrawberryFrameworkConfig`, the four positive tests, and the one consolidated negative-shape test with the four-key forbidden `dict` and inline `for`-loop. Net `+37 / -108`. Deleted the entire prose plan (lines 1-71 of the stub), the TODO anchor (lines 73-75), and the pseudo-block (lines 77-108) per Implementation step 1.

### Tests added or updated

- `tests/test_apps.py::test_djangostrawberryframeworkconfig_importable_from_apps_module` — pins the import path `django_strawberry_framework.apps.DjangoStrawberryFrameworkConfig` (Decision 1); the top-level `from … import …` is the load-bearing assertion (collection-time), with a body `assert … is not None` so the test has a runtime to record.
- `tests/test_apps.py::test_djangostrawberryframeworkconfig_is_appconfig_subclass` — pins `issubclass(…, django.apps.AppConfig)`; uses `django.apps.AppConfig` (not the `django.apps.config.AppConfig` submodule path) so an accidental rebase onto the implementation class fails the test.
- `tests/test_apps.py::test_djangostrawberryframeworkconfig_pins_name_and_verbose_name` — pins both attribute values verbatim per Decision 2: `name == "django_strawberry_framework"` and `verbose_name == "Django Strawberry Framework"`.
- `tests/test_apps.py::test_djangostrawberryframeworkconfig_resolves_through_django_app_registry` — pins `django.apps.apps.get_app_config("django_strawberry_framework")` returns an instance of `DjangoStrawberryFrameworkConfig`; load-bearing end-to-end check that the explicit AppConfig actually registered (rather than the implicit fallback Django synthesized pre-Slice-1 standing in unnoticed).
- `tests/test_apps.py::test_djangostrawberryframeworkconfig_defines_no_extra_appconfig_attributes` — single pytest item with an inline `for` loop over the four-key `dict` `{"ready": "Decision 4 …", "label": "Decision 2 …", "default_auto_field": "Decision 5 …", "default": "Decision 8 …"}`; each iteration asserts `key not in DjangoStrawberryFrameworkConfig.__dict__` with a fail message of the form `f"{key!r} is forbidden on DjangoStrawberryFrameworkConfig: {why}"`. The `__doc__` key is intentionally excluded per spec lines 66 / 391.

### Validation run

- `uv run ruff format .` — pass (`105 files left unchanged`).
- `uv run ruff check --fix .` — pass (`All checks passed!`); no autofixes applied.
- `git status --short` after both ruff invocations:
  - ` M django_strawberry_framework/apps.py` — pre-existing post-Slice-1 baseline (not yet committed; AGENTS.md line 31). Not touched by this pass.
  - ` M tests/test_apps.py` — slice-intended; appears in `### Files touched` above.
  - `?? docs/builder/bld-slice-1-module_appconfig.md`, `?? docs/builder/bld-slice-2-tests.md`, `?? docs/builder/build-017-apps-0_0_7.md` — pre-existing build artifacts (not yet committed; baseline at task start).
  - Classification: zero unrelated tool churn; no `git checkout` reverts needed.
- `uv run pytest --no-cov tests/test_apps.py -v` — pass (5 items collected, 5 passed in 0.05s). Confirms the spec's "5 tests" count matches pytest's collection output (single negative-shape function with inline loop, NOT `pytest.mark.parametrize` per rev4 Informational #2 / spec line 25). Coverage-shaped flag used: `--no-cov` only (per BUILD.md line 100).

### Implementation notes

- **Forbidden-set container shape: `dict[str, str]`.** Worker 1's plan flagged this as Implementation discretion (`### Implementation discretion items` → "Forbidden-set container shape"); shipped the `dict` form the staged stub previewed because it gives the test fail message the per-key Decision string for free without a parallel lookup. Alternative `tuple[tuple[str, str], ...]` / `frozenset` shapes would have required a second structure for the reasons, or lost the reasons entirely.
- **Test-module docstring wording: short em-dash one-liner.** Discretionary per Worker 1's plan; chose `"""Tests for ``django_strawberry_framework.apps`` — Django AppConfig."""` (matches the em-dash lead-in of `tests/test_list_field.py:1` and the Slice-1 `apps.py` module docstring style). 67 characters; well inside the 110 cap (AGENTS.md line 16); satisfies `D100`.
- **No per-test docstrings.** Discretionary per Worker 1's plan; the test function names are descriptive enough (each one names the subject, the verb, and the contract pinned), and the negative-shape test's body has an inline comment-equivalent via the `forbidden` dict values. The `tests/*` per-file-ignore for the `D` family (pyproject.toml lines 100-107) means omitting docstrings is gate-clean; chose the lower-friction default to keep the file scan-readable at 37 lines.
- **Single inline comment in `test_djangostrawberryframeworkconfig_importable_from_apps_module`.** Two-line `#` comment explaining that the top-level import is the actual assertion (so a future reader doesn't see `assert … is not None` and wonder why it isn't testing something meatier). The body `assert` exists to give the test a runtime body so pytest records a real pass/fail.
- **Imports written in the order Worker 1's plan suggested would be normalized.** Wrote `import django.apps` before `from django_strawberry_framework.apps import …`; ruff's isort config did not apply any reordering (third-party `django` import → first-party `django_strawberry_framework` import is already the canonical order). No format-pass churn.

### Notes for Worker 3

- Shadow-file inspection skipped per Worker 1's plan disposition at `bld-slice-2-tests.md` lines 83-88 (`scripts/review_inspect.py` disposition for Slice 2) — the file is 37 lines of trivially-shaped test scaffolding with one 4-iteration `for` loop; no control-flow hotspots, no Django ORM markers, no reflective-access patterns beyond `__dict__` membership. If you see something that surprises you on read, run the helper against `tests/test_apps.py` and reassess.
- The pre-existing `git status` baseline (Slice-1 `apps.py` modification and the three build-artifact untracked files) is the post-Slice-1 state at task start, not Slice-2 churn. Slice 2's actual diff is `tests/test_apps.py` only.
- The five tests cover every behavioral surface of `django_strawberry_framework/apps.py`: importability + class definition (positive test 1), MRO (positive test 2), `name` and `verbose_name` (positive test 3), Django registry resolution end-to-end (positive test 4), and the four-key forbidden-attribute pins (negative test). The class docstring (`__doc__`) is covered indirectly — the negative test would fail if it weren't present (because adding `"__doc__"` to the forbidden set would catch the docstring), and excluding `__doc__` from the set is the spec's explicit "documentation is not behavior" choice (lines 66, 391). Worker 1 will tick the verbatim spec slice checklist boxes during final verification; the contract for both boxes is satisfied.

### Notes for Worker 1 (spec reconciliation)

No spec gaps, conflicts, or unstated assumptions surfaced during implementation. The staged stub's pseudo-block at the pre-edit `tests/test_apps.py:77-108` was a direct preview of the shipped shape; the spec's Test plan (lines 374-396), Slice 2 checklist (lines 64-66), and Decisions 2 / 4 / 5 / 8 were internally consistent; no spec edit needed.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- Worker 1's plan flagged the deliberate 3x repetition of the `"django_strawberry_framework"` literal across `tests/test_apps.py` — confirmed in the diff at three distinct pin sites: line 5 (`from django_strawberry_framework.apps import …`, the import-path pin for Decision 1), line 19 (`DjangoStrawberryFrameworkConfig.name == "django_strawberry_framework"`, the `name` attribute pin for Decision 2), and line 24 (`django.apps.apps.get_app_config("django_strawberry_framework")`, the registry-lookup pin for the Decision 7 / Edge-cases registry contract). Each repetition pins a distinct contract; extracting to a module-level `APP_LABEL` constant would couple the three pins and let a regression that broke only one contract pass under the consolidated assertion. The call is correct as-is; no consolidation warranted. Parallel reasoning is recorded at Slice 1 DRY findings (`docs/builder/bld-slice-1-module_appconfig.md`) for the symmetric `apps.py:9` / `__init__.py:16` literal.
- No other repeated literals, near-copies, or parallel data flows in the diff. The four-key forbidden `dict` is the single source of truth for the negative-shape contract; no `assert "ready" not in __dict__` lines are scattered across other tests.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty. `__all__` and the re-export list are unchanged, as Decision 3 / DoD item 3 / Slice 1 checklist's "Do NOT re-export" pin require. The Slice-2 diff is contained entirely within `tests/test_apps.py`.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- Test count matches spec exactly. `uv run pytest --no-cov tests/test_apps.py --collect-only -q` reports `5 tests collected`; one item per `def test_…`, no `pytest.mark.parametrize` fan-out on the negative-shape test (the spec's rev4 Informational #2 pin at spec line 25 and the "5 tests" count in DoD item 4 / Implementation-plan table are both honored).
- Forbidden-key iteration set is exactly the four behavioral keys spec line 66 names: `{"ready", "label", "default_auto_field", "default"}` (test lines 30-33). The implicit `__doc__` key is correctly absent from the iteration set; the class docstring required by `D101` (per rev3 H1) lives at `apps.py:7` and is exempt under the spec's "documentation is not behavior" framing at spec lines 66 / 391.
- Each forbidden-key entry maps to its enforcing Decision in the `dict` values (`"Decision 4 …"`, `"Decision 2 …"`, `"Decision 5 …"`, `"Decision 8 …"`), and the fail message at test lines 36-38 interpolates both `{key!r}` and `{why}` per the spec's "fail message naming the offending key and the Decision that forbids it" requirement at spec line 391. A bare key-only message would have been a Medium finding; the f-string carries the Decision citation.
- `__dict__` discriminator (test line 36) is correct — inherited base attributes from `django.apps.AppConfig` are NOT in the subclass's `__dict__`, so the loop catches only class-body additions without false-positiving on the inherited surface. `dir()` / `hasattr()` would have produced false positives; the diff uses `__dict__`.
- Registry-pickup test (line 23-25) uses the canonical lookup string `"django_strawberry_framework"` (Decision 7 / Decision 2). No `"dsf"`-style shortcut.
- Subclass test (line 14-15) uses `issubclass(…, django.apps.AppConfig)` against the canonical `django.apps.AppConfig` attribute path, not direct identity (`is AppConfig`) and not the `django.apps.config.AppConfig` submodule path — both alternative shapes would have been findings; the diff uses the correct one.
- `tests/test_apps.py::test_djangostrawberryframeworkconfig_resolves_through_django_app_registry` returns a real `DjangoStrawberryFrameworkConfig` instance (confirmed via focused `uv run pytest --no-cov tests/test_apps.py -v` — all 5 pass), proving Django's app loader resolves the explicit class rather than the implicit pre-Slice-1 fallback.
- Imports are minimal and correctly ordered (`import django.apps`, then `from django_strawberry_framework.apps import DjangoStrawberryFrameworkConfig`); no unused imports, no `pytest` import, no `pytest.mark.django_db` decorator (none of the 5 tests touch the ORM).
- `tests/base/test_init.py:35-44`'s `__all__` assertion is byte-identical to baseline; no public-surface drift.
- Helper disposition: skip is appropriate. The shipped file is 39 lines of trivially-shaped test scaffolding (4 one-liner positive tests + 1 negative-shape test with a 4-iteration `for` loop). No control-flow hotspots, no Django ORM markers, no reflective-access patterns beyond `__dict__` membership, no calls of interest. The "50 or more lines of new logic" threshold for files outside `django_strawberry_framework/` at BUILD.md line 409 does not trip — even counting generously, the file is below threshold and the content is scaffold, not logic. Worker 1's pre-recorded skip and Worker 2's confirmation both align.
- Spec slice checklist walk: both `- [ ]` boxes Worker 0 will copy into `### Spec slice checklist (verbatim)` are addressed by the diff. Box 1 ("New test module … covering the four contracts") — pinned by the 4 positive tests at test lines 8-25. Box 2 ("One consolidated negative-shape test") — pinned by test lines 28-38 with the four-key `dict`, plain `for` loop, `__dict__` discriminator, and Decision-naming fail message. Zero silently un-addressed sub-checks.
- Ruff gates clean: `uv run ruff format --check tests/test_apps.py` returns `1 file already formatted`; `uv run ruff check tests/test_apps.py` returns `All checks passed!` (no `D100` violation despite the test-file `D`-family per-file-ignore — the module docstring is present anyway and reads coherently).

### Temp test verification

None; no temp tests used. The shipped 5 tests collectively pin every contract in the Slice 2 checklist and the spec's Test plan; no edge case surfaced during review that required throwaway exploration.

### Notes for Worker 1 (spec reconciliation)

None. The diff matches the plan exactly; no spec ambiguity, no implementation drift, no follow-up slice candidate surfaced.

### Review outcome

`review-accepted`. All spec-required behaviors are reflected in the diff; both spec slice checklist boxes are addressed; the 5-test count matches pytest's collection output; public surface is unchanged; the forbidden-key set, `__dict__` discriminator, fail-message shape, registry-lookup string, and subclass assertion all match the spec's explicit pins; no High / Medium / Low findings.

---

## Final verification (Worker 1)

- **Spec slice checklist (verbatim).** Both `- [ ]` boxes in the Plan's `### Spec slice checklist (verbatim)` ticked `- [x]` against the diff. Box 1 ("New test module `tests/test_apps.py` covering the four contracts") — `tests/test_apps.py:8-25` ships all four positive tests: `importable_from_apps_module` (lines 8-11), `is_appconfig_subclass` (lines 14-15), `pins_name_and_verbose_name` (lines 18-20), and `resolves_through_django_app_registry` (lines 23-25). Box 2 ("One consolidated negative-shape test") — `tests/test_apps.py:28-38` ships the single consolidated test with the four-key forbidden `dict` `{"ready", "label", "default_auto_field", "default"}`, an inline `for` loop (NOT `pytest.mark.parametrize` — confirmed via the `--collect-only -q` count of 5 items, not 8), the `__dict__` discriminator, and a fail message of the form `f"{key!r} is forbidden on DjangoStrawberryFrameworkConfig: {why}"` that names both the offending key AND the Decision that forbids it per spec line 391. `__doc__` is correctly absent from the iterated set (documentation is not behavior per spec lines 66 / 391). No silently un-ticked boxes.
- **DRY check across this slice and prior accepted slices.** Slice 1 (`final-accepted`) is the only prior accepted slice. The deliberate 3x repetition of the `"django_strawberry_framework"` literal across `tests/test_apps.py:5` (import path), `:19` (`name` attribute pin), and `:24` (registry lookup key) was analyzed in Worker 1's Slice 2 plan (DRY analysis "New helpers justified" — None) and in Worker 3's review (DRY findings); each occurrence pins a distinct contract (import path / Decision-2 `name` value / Decision-7 registry lookup), so extraction to a module-level `APP_LABEL` constant would couple three independent contracts and obscure failure modes. Parallel non-consolidation reasoning lives at `docs/builder/bld-slice-1-module_appconfig.md` for the symmetric `apps.py:9` / `__init__.py:16` literal. The cross-slice scan surfaces no new duplication beyond this previously-accepted deliberate repetition. No new helpers, no near-copies between modules, no repeated string/key/tuple literals that should be consolidated.
- **Existing tests still pass.** Ran `uv run pytest --no-cov tests/ -x -q` (full `tests/` tree per BUILD.md "Existing tests still pass"; `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` per BUILD.md line 109). Result: `690 passed, 2 skipped, 4 warnings in 14.59s`. The 2 skips are pre-existing (`test_converters.py` parametrized cases). Focused `uv run pytest --no-cov tests/test_apps.py -v` confirms `5 passed in 0.05s` — the spec's "5 tests" count matches pytest's collection output exactly (rev4 Informational #2 honored). No regressions in any other test tree.
- **Spec reconciliation.** Worker 2's `### Notes for Worker 1 (spec reconciliation)` and Worker 3's `### Notes for Worker 1 (spec reconciliation)` both write `None` / "no spec ambiguity surfaced." Re-verified spec status/header lines at `docs/spec-017-apps-0_0_7.md:1-6` per Worker 1's per-spawn re-verification rule — `Status: draft (revision 6, post-rev5 build-readiness audit)` remains accurate (Slice 3 has not shipped, so the spec is still mid-build). No spec edit needed during this final-verification pass.
- **Final status.** `final-accepted`. The artifact `Status:` line is set accordingly.

### Summary

Slice 2 shipped `tests/test_apps.py` rewriting the 108-line TODO-anchored Pseudo stub in place to a 38-line file with 5 tests (4 positive: importable / subclass / `name` + `verbose_name` / registry pickup; 1 consolidated negative-shape covering the four forbidden behavioral keys `{"ready", "label", "default_auto_field", "default"}` via a single pytest item with a plain `for` loop and `__dict__` discriminator, fail messages naming both the offending key and the enforcing Decision). All 5 pass; the full `tests/` tree passes (690/692 with 2 pre-existing skips). Public surface unchanged; no spec edit needed; no DRY findings beyond the previously-accepted deliberate non-consolidation of the `"django_strawberry_framework"` literal.

### Spec changes made (Worker 1 only)

None.
````
