# DRY review: `django_strawberry_framework/__init__.py`

Status: verified

## System trace

The package root owns four things: (1) the canonical package logger
(`logging.getLogger("django_strawberry_framework")`), declared here so the consumer-visible
`LOGGING` key literal lives in exactly one source location (`optimizer/__init__.py` re-exports it;
grep confirmed no other `getLogger` call exists in the package); (2) the eager public re-export
surface (`__all__`, 38 names, each pinned by identity/membership in `tests/base/test_init.py`);
(3) the release literal `__version__ = "0.0.14"`; and (4) the DRF soft-dependency export policy --
`_DRF_SOFT_EXPORTS` plus PEP 562 `__getattr__` resolving seven DRF-dependent names lazily through
the shared guard `rest_framework/require_drf()` (which itself delegates to
`utils/imports.py::require_optional_module`, as do `require_channels` and
`require_debug_toolbar`). Consumers are every importer of the root package (tests, fakeshop,
docs); the packaging metadata in `pyproject.toml` was a second declaration of fact (3).

## Verification

- **Cross-flavor policy mirroring — searched.** The lazy-export/soft-guard policy is the target's
  one cross-module surface. Searched all PEP 562 module `__getattr__` implementations:
  `routers.py:528` resolves one name through `_build_router_class()` behind `require_channels()`;
  the root resolves seven names through a name-map dict behind `require_drf()`. Different guards,
  different shapes, independent domains; a generic lazy-export helper would couple DRF and channels
  policy into one module. Rejected. The three soft-dependency guards already share their primitive
  (`require_optional_module`), so the mirroring that matters is consolidated.
- **Sync and async twins — ruled inapplicable.** The target declares no async surface; the
  sync/async pair `apply_cascade_permissions` / `aapply_cascade_permissions` passes through as a
  pure re-export of code owned by `permissions.py`.
- **Derived rather than repeated knowledge — searched, CONFIRMED finding.** Grep for the release
  literal found `[project] version` in `pyproject.toml:4` equal to `__version__` here: one fact,
  two declarations, policed by `tests/base/test_init.py::test_version_parity_with_pyproject` (plus
  the dev-group `tomli` pin existing largely for it) and by `scripts/bug_hunt.py::_package_release`,
  which read both sources and raised on mismatch (with two regexes and a tomllib-free fallback
  existing only to serve that cross-check). Also verified the logger-name literal has exactly one
  source, and `__all__` duplicates only the import list by design.
- **Inverse and round-trip pairs — ruled inapplicable.** The `__getattr__` maps name → object one
  way at access time; nothing in the target encodes a grammar that another site decodes.
- **Contracts restated in another medium — searched.** The `__all__` tuple is restated verbatim in
  `test_public_api_surface_is_pinned` and the logger name in `test_logger_name_is_django_strawberry_framework`
  -- intentional test pins per DRY.md ground rules, preserved. The soft-export contract is restated
  in `rest_framework/__init__.py`'s docstring and enforced by `tests/rest_framework/test_soft_dependency.py`
  -- prose describing an enforced invariant, not an implementation to merge.

Single-edit-site tests:

1. Posited change "cut release 0.0.15": forced sites were this file's `__version__`, pyproject
   `[project].version`, plus the parity test and bug-hunt cross-check that exist only because there
   were two declarations. Declaration count came back **two** → duplication (now consolidated to
   **one**; the posited change now touches only this file).
2. Posited change "add an eighth DRF soft export": forced sites = one row in `_DRF_SOFT_EXPORTS`
   (+ the parametrized soft-dependency tests pick it up automatically). Count **one** → the lazy
   export map is correctly single-owned.
3. Posited change "rename the package logger": forced sites = one (`getLogger` call here); the test
   pin follows deliberately. Count **one**.

Rejected candidates worth keeping separate: explicit `__all__` vs deriving it from the import list
(the pinned literal IS the surface contract; derivation would weaken the pin); routers/root
`__getattr__` unification (couples independent domains).

## Opportunities

### Single-source the release literal via hatchling dynamic version

- **Repeated responsibility:** the current release version, declared once as runtime
  `__version__` and once as packaging metadata `[project].version`, with lockstep policed by a
  parity test, a script cross-check, and repository law.
- **Sites:** `django_strawberry_framework/__init__.py` (`__version__`),
  `pyproject.toml` `[project].version`, `tests/base/test_init.py::test_version_parity_with_pyproject`,
  `scripts/bug_hunt.py::_pyproject_version` + `_package_release` + two parse regexes +
  the `tomllib` import fallback, `tests/test_bug_hunt.py` (mismatch/fallback coverage),
  `AGENTS.md` bump-together rule.
- **Evidence:** change "cut 0.0.15" forced two declaration sites plus machinery whose sole purpose
  was keeping them equal. Same fact, same change axis; textual form differs but responsibility is
  identical.
- **Owner:** the package init literal -- hatchling natively derives packaging metadata from it via
  `[tool.hatch.version]`.
- **Consolidation:** removed `[project].version`, added `dynamic = ["version"]` +
  `[tool.hatch.version] path = "django_strawberry_framework/__init__.py"`; deleted the parity test;
  deleted `scripts/bug_hunt.py::_pyproject_version`, its regexes, its tomllib fallback, and the
  mismatch branch (`_package_release` now reads the one source); deleted the corresponding
  `tests/test_bug_hunt.py` cases and stale pyproject fixtures; rewrote the `AGENTS.md` rule to
  name the single source; regenerated `uv.lock`; updated the `tomli` dev-pin comment (still needed
  by `scripts/check_trailing_commas.py`).
- **Proof:** scratch experiment under `docs/dry/temp-tests/dry-file-__init__/`: `uv build --sdist
  --wheel` produced PKG-INFO and wheel METADATA both reading `Version: 0.0.14` with no static
  pyproject version present (artifacts removed after recording). Permanent behavior coverage:
  `tests/base/test_init.py::test_version` still pins the literal; `tests/test_bug_hunt.py` retains
  generator tests driven solely from the package init, including
  `test_target_release_overrides_the_package_version`. Hatchling rejects a future static+dynamic
  collision at build time, so drift back to two declarations fails loudly.
- **Risks / non-goals:** `KANBAN.md:356` and the version-quintet card text reference the old rule
  31 wording, the deleted mismatch branch, and the deleted test name -- board text is maintainer
  flow territory and left untouched for the completing pass. Deferred: full pytest run (not
  authorized this cycle). Concurrent dirty files (`exceptions.py`, `scalars.py`, several filter/
  schema tests, `spec-030` doc) were left untouched.

## Implementation (Worker 1)

Tracked edits: `django_strawberry_framework/__init__.py`, `pyproject.toml`, `uv.lock`,
`AGENTS.md`, `scripts/bug_hunt.py`, `tests/base/test_init.py`, `tests/test_bug_hunt.py`.
After edits: `uv run ruff format .` (429 files unchanged) and `uv run ruff check --fix .` (all
checks passed); `scripts/check_trailing_commas.py --check` clean. Orphan sweep for
`_pyproject_version` / `test_version_parity_with_pyproject` came back empty outside KANBAN.md.

## Judgment

The file's real surface is deliberate surface control: one logger literal, a pinned export list,
and a lazily guarded soft-dependency map, each already single-owned except the release literal,
whose second declaration had quietly grown a policing apparatus across tests, scripts, and
repository law. That apparatus is gone; the fact now has exactly one home and one edit site.

## Independent verification (Worker 2)

Re-traced from the baseline diff (`git diff 37b1111` scoped to the seven recorded files) and the
current sources. The `__init__.py` change is comment-only — the `__version__` literal itself
pre-existed; every behavioral edit lives in pyproject/scripts/tests/law as claimed.

Executable probes (scratch under `docs/dry/temp-tests/dry-file-__init__/`, removed after
recording):

- `uv build --sdist --wheel` with no static `[project] version` present: sdist PKG-INFO and wheel
  METADATA both read `Version: 0.0.14` — hatchling derivation works today, not just in theory.
- Bump probe: set `__version__ = "0.0.15"` temporarily → `uv lock --check` exits 0 (the lock's
  root entry records no version at all since this cycle, so it cannot drift), then restored
  byte-exact (sha256 identical before/after).

Orphan sweeps (repo-wide git grep): `_pyproject_version`,
`test_version_parity_with_pyproject`, `"version mismatch"`, `"bump them together"`, and both
deleted regex names survive only in sealed history (`docs/builder/DONE/build-012-version_release_alignment-0_0_4.md`)
and the binary fakeshop db — no live code, test, script, workflow, or pre-commit reference.
`tomli`/`tomllib` consumers are now exactly `scripts/check_trailing_commas.py` (reads
`[tool.ruff] line-length`, not version), so the rewritten dev-pin comment is accurate. All four
workflows and `.pre-commit-config.yaml` trigger on or lint pyproject but never parse a static
version; there is no publish workflow. `docs/dry/export_dry_review.py` requires an explicit
`--target-release` and reads no version source; the two shadow generators read none either.

Single-edit-site recount with my own posited change ("cut 0.0.16"): forced declaration sites = one
(the init literal); pyproject inert (`dynamic = ["version"]`), lock proven inert by the bump probe.
Remaining movers are governed non-declaration state the artifact correctly excludes from the
declaration count: the deliberate `test_version` literal pin in `tests/base/test_init.py` and the
glossary package-version line, both moved by repo-law joint-cut rules. Counts 2 and 3 hold:
`tests/rest_framework/test_soft_dependency.py` parametrizes over `_DRF_SOFT_EXPORTS` twice, so an
eighth soft export self-covers (count one); exactly one `getLogger` call exists in the package with
the optimizer re-export pinned by identity. Matrix re-discharged against the real surface: all five
axes re-checked independently; `routers.py::DjangoGraphQLProtocolRouter.__getattr__` confirmed a
different guard, shape, and domain than the root name-map, so the unification rejection stands.

Non-blocking observation for the completing pass: the deferred-medium risk note under-names its
members. Beyond KANBAN card text (line 356 cites the deleted `#"bump them together"` branch and the
deleted test name; line 4308 lists a five-site quintet), `docs/GLOSSARY.md`'s Joint version cut
entry still instructs moving `[project].version` in pyproject.toml and the uv.lock root version
entry — neither exists anymore. Both documents are rendered from maintainer-owned app data
(`scripts/build_glossary_md.py` over the glossary app DB), so their rewrite belongs to the
completing pass that owns the next joint cut (card 051, `0.0.15`); nothing executable reads either.
Recorded here so that pass cannot miss them; not a defect in this consolidation.

Judgment upheld: verified.
