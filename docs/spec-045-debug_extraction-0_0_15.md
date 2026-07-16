# Spec: Extract `DjangoDebugExtension` into the standalone `django-strawberry-debug` package — the framework keeps a `[debug]` extra and a guarded re-export

Planned for `0.0.15` (card `TODO-ALPHA-045-0.0.15`); **this card is the only
card at `0.0.15` and owns the version bump**
([Decision 7](#decision-7--lone-card-at-0015--slice-3-owns-the-version-cut)).
This card moves the
[`DjangoDebugExtension`][glossary-djangodebugextension] — the
[response-extensions debug middleware][glossary-response-extensions-debug-middleware]
shipped by card `044` — out of this distribution and into a **brand-new
standalone package, `django-strawberry-debug`**, published from its own
repository. The framework keeps two things: a
`pip install django-strawberry-framework[debug]` packaging extra that pins
the new package, and a [soft-dependency][glossary-soft-dependency]-guarded
re-export in `extensions/__init__.py` so the shipped import path
`from django_strawberry_framework.extensions import DjangoDebugExtension`
keeps working byte-for-byte.

Why extraction is right **here** when the package-split investigation
(card `046`, the boundary+DRY card) rejected splitting the optimizer: the
verdicts flow from the same evidence standard, applied to opposite facts.
The optimizer is bidirectionally fused to the type system; the debug
extension's entire import surface is stdlib + Django + graphql-core +
Strawberry **plus exactly one package symbol (the root `logger`)**, nothing
in the package imports it back, and it works against ANY
`strawberry-graphql` + Django schema — no
`DjangoType`, no registry, no optimizer required. It is the one part of the
codebase with a genuine standalone audience, and the maintainer's sequencing
decision places this card **before** the DRY card so the extraction shrinks
that card's surface (`extensions/` becomes a soft-dep leaf like
`rest_framework/` before the import-linter contracts are written).

Status: **PLANNED — no slice built yet.**
Three slices: Slice 1 (**the new package**: repo scaffold, verbatim code
move with the logger swap, self-contained test harness, CI, publish
`0.1.0`), Slice 2 (**the framework seam**: delete `extensions/debug.py` and
its package-tier suite, rewrite `extensions/__init__.py` as the guarded
lazy re-export, add the `[debug]` extra, re-shape the live tier), Slice 3
(**docs fold-in + the `0.0.15` version cut + card wrap**).

Permission caveat: `AGENTS.md` prohibits `CHANGELOG.md` edits without
explicit permission; this spec's Slice 3 grants that permission for the
`0.0.15` release entry, and no earlier slice touches it.

---

## Key glossary references

Terms this spec relies on (statuses per [`docs/GLOSSARY.md`][glossary]):

- [`DjangoDebugExtension`][glossary-djangodebugextension],
  [Response-extensions debug middleware][glossary-response-extensions-debug-middleware],
  [Debug SQL row][glossary-debug-sql-row],
  [Debug exception row][glossary-debug-exception-row] — the feature and wire
  contract that move, unchanged, to the new package.
- [Django debug-cursor capture][glossary-django-debug-cursor-capture],
  [Async SQL-capture boundary][glossary-async-sql-capture-boundary],
  [Per-operation extension isolation][glossary-per-operation-extension-isolation],
  [Strawberry extension lifecycle][glossary-strawberry-extension-lifecycle] —
  the mechanism contracts the new package's README and tests carry forward.
- [Developer-only debug posture][glossary-developer-only-debug-posture] —
  the security posture the new package's README must restate verbatim.
- [Debug-toolbar middleware][glossary-debug-toolbar-middleware] — the
  server-side sibling that STAYS in this package (it wraps this package's
  GraphQL view plumbing; it is not generic).
- [Soft dependency][glossary-soft-dependency],
  [Hard dependency][glossary-hard-dependency],
  [`require_optional_module`][glossary-require_optional_module],
  [PEP 562 lazy export][glossary-pep-562-lazy-export] — the seam shape
  `extensions/__init__.py` adopts.
- [Probe URLconf][glossary-probe-urlconf] — the live-tier scaffold Slice 2
  slims to a single re-export proof.
- [`TestClient`][glossary-testclient] — drives the remaining live-tier test.
- [Graphene debug migration][glossary-graphene-debug-migration] — the parity
  story, which now points migrants at the extra instead of a bundled module.
- [Joint version cut][glossary-joint-version-cut],
  [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the
  release and test disciplines Slices 2–3 follow.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — the
  composability partner; the both-extensions-on-one-schema proof moves to
  the framework's remaining live test.

## Slice checklist

Each top-level item maps to one commit / PR (Slice 1's commits land in the
new repository; Slices 2–3 land here).

- [ ] **Slice 1 — `django-strawberry-debug` exists and is published**
  - [ ] New repository (`riodw/django-strawberry-debug`): `pyproject.toml`
        (name `django-strawberry-debug`, version `0.1.0`, deps
        `Django>=5.2` + `strawberry-graphql>=0.316.0` with the
        per-operation-isolation floor comment carried over verbatim; **no
        dependency on `django-strawberry-framework`**), MIT license, `src/`
        layout (`django_strawberry_debug/__init__.py` re-exporting
        `DjangoDebugExtension`), README ported from spec-044's user-facing
        API: opt-in shape, wire contract tables, security caveats, the
        graphene wire-name narrowing table, the async boundary.
  - [ ] `debug.py` moved **verbatim** except the single logger swap
        ([Decision 3](#decision-3--the-logger-swap-is-the-only-code-change)).
  - [ ] `tests/test_debug.py` moved with a self-contained harness (minimal
        `settings` + models; no fakeshop) — same assertions, new fixtures
        ([Decision 5](#decision-5--test-relocation-package-tier-moves-live-tier-shrinks-to-the-seam)).
  - [ ] CI: lint + test matrix (py3.10–3.14 × supported Django/Strawberry
        floors), publish workflow; `0.1.0` on PyPI.
- [ ] **Slice 2 — the framework seam**
  - [ ] Delete `django_strawberry_framework/extensions/debug.py` and
        `tests/extensions/test_debug.py`; sweep all three test trees for
        orphan imports.
  - [ ] Rewrite `extensions/__init__.py` as the
        [`require_optional_module`][glossary-require_optional_module]-guarded
        [PEP 562 lazy export][glossary-pep-562-lazy-export] of
        `DjangoDebugExtension` from `django_strawberry_debug`
        ([Decision 4](#decision-4--the-framework-seam-debug-extra--guarded-re-export)).
  - [ ] `[project.optional-dependencies] debug = ["django-strawberry-debug>=0.1.0"]`;
        dev group gains the same pin so the suite tests the present-path.
  - [ ] Absence test on the `sys.modules[name] = None` sentinel shape
        (`tests/_soft_dependency.py`); one live-tier re-export +
        optimizer-composability proof retained; the rest of
        `examples/fakeshop/test_query/test_debug_extension_api.py` and its
        [probe URLconf][glossary-probe-urlconf] scaffold retire with the
        moved suite ([Decision 5](#decision-5--test-relocation-package-tier-moves-live-tier-shrinks-to-the-seam)).
  - [ ] Coverage gate `fail_under = 100` re-verified after the deletion.
- [ ] **Slice 3 — Docs fold-in + `0.0.15` cut + card wrap**
  - [ ] GLOSSARY updates via the glossary DB + re-render (never hand-edit):
        `DjangoDebugExtension`-family entries point at the new package +
        extra; `README.md` feature list and install section likewise;
        `docs/TREE.md` regen; `docs/dry/dry-file-extensions__debug.md`
        retired. `docs/spec-044-debug_extension-0_0_14.md` (by then
        archived) is history — untouched.
  - [ ] The version quintet: `pyproject.toml` `[project].version`,
        `django_strawberry_framework/__init__.py::__version__`,
        `tests/base/test_init.py`, the GLOSSARY package-version row, the
        root package entry in `uv.lock`.
  - [ ] `CHANGELOG.md` `0.0.15` entry (permission granted by this slice).
  - [ ] Card flip to Done + `KANBAN.md`/`KANBAN.html` regeneration from the
        DB; `import_spec_terms` run.

## Problem statement

Card `044` built the package's in-response debug surface as
`extensions/debug.py` — 472 lines of implementation held to the
[developer-only debug posture][glossary-developer-only-debug-posture], plus
a 1,019-line package-tier suite and a live tier riding a dedicated
[probe URLconf][glossary-probe-urlconf]. A dead-weight review then
established three facts about it: **nothing in the package imports it**
(it is deliberately absent from the root `__all__`); **fakeshop deliberately
does not enable it**; and — unlike every other subsystem — **it imports
nothing from the package** except the root `logger`. It is a zero-coupling
leaf with a genuine standalone audience: any `strawberry-graphql` + Django
project can use it, framework or not. Carrying it inside this distribution
buys the framework's users nothing they wouldn't get from an extra, while
costing this package ~1,900 lines of weight the maintainer is actively
trying to shed. Extraction — rejected for the optimizer on coupling
evidence — is exactly right for this module, on the same evidence standard.

## Current state

- `django_strawberry_framework/extensions/` contains exactly two files:
  `debug.py` (the extension) and `__init__.py` (a 20-line eager re-export
  whose docstring already pins the "not part of the default recipe"
  posture).
- `debug.py`'s imports: `threading`, `traceback`, `contextlib`,
  `dataclasses`, `typing`, `django.db.connections`, `graphql`,
  `strawberry.extensions.SchemaExtension`, and `from .. import logger`.
  Verified: no registry, no `DjangoType`, no optimizer, no `utils`.
- Tests: `tests/extensions/test_debug.py` (1,019 lines, package tier) and
  `examples/fakeshop/test_query/test_debug_extension_api.py` (356 lines,
  live tier over the probe URLconf, driven by
  [`TestClient`][glossary-testclient]).
- The `strawberry-graphql>=0.316.0` floor lives in `[project].dependencies`
  with spec-044 Decision 6's
  [per-operation extension isolation][glossary-per-operation-extension-isolation]
  rationale comment.
- Card `WIP-ALPHA-044-0.0.14` is mid-flight and owns the `0.0.14`
  [joint version cut][glossary-joint-version-cut]; this card is sequenced
  strictly behind it ([Risks](#risks-and-open-questions)).
- The boundary+DRY card (`TODO-ALPHA-046-0.0.16`) is sequenced behind THIS
  card and writes its import-linter `extensions/`-leaf contract against the
  post-extraction tree.

## Goals

- `django-strawberry-debug 0.1.0` exists on PyPI: same class, same wire
  contract ([Debug SQL row][glossary-debug-sql-row] /
  [Debug exception row][glossary-debug-exception-row]), same
  [capture mechanism][glossary-django-debug-cursor-capture], same
  documented [async boundary][glossary-async-sql-capture-boundary] — usable
  by any Strawberry+Django project with no framework involvement.
- This package sheds `extensions/debug.py` and its package-tier suite
  (~1,500 lines) while `pip install django-strawberry-framework[debug]`
  and the shipped import path both keep working — **zero breakage** for
  anything `0.0.14` shipped.
- The [graphene debug migration][glossary-graphene-debug-migration] story
  survives intact: migrants install the extra instead of getting the module
  bundled.
- The DRY card inherits a smaller surface: `extensions/` is a soft-dep leaf
  before its boundary contracts are authored.

## Non-goals

- **No behavior changes to the extension.** The wire contract, capture
  mechanics, posture, and error shapes move verbatim; the logger swap is
  the only code change ([Decision 3](#decision-3--the-logger-swap-is-the-only-code-change)).
- **No new capability.** No async SQL-capture work, no knobs, no redaction
  hooks — the spec-044 follow-on list transfers to the new repo's issue
  tracker, not this card.
- **No floor changes.** `strawberry-graphql>=0.316.0` STAYS in this
  package's `[project].dependencies`
  ([Decision 6](#decision-6--the-strawberry-floor-stays-in-the-framework)).
- **No deprecation machinery.** The guarded re-export preserves the only
  import path `0.0.14` shipped; there is nothing to deprecate at 0.0.x.
- **The [Debug-toolbar middleware][glossary-debug-toolbar-middleware] does
  not move.** It wraps this package's GraphQL view plumbing and is not
  generic; it stays exactly where card `042` shipped it.
- **No uv-workspace / monorepo arrangement.** Maintainer-selected: a
  brand-new standalone repository.

## Borrowing posture

- The new package borrows FROM this package: `debug.py` and its suite move
  verbatim (authorship continuity; the spec-044 decisions remain the design
  record and the new README cites them by content, not by link).
- The seam shape is borrowed from this package's own `rest_framework/`
  discipline: import-time innocence, a
  [`require_optional_module`][glossary-require_optional_module] guard with
  an install hint naming the extra, and the
  [PEP 562 lazy export][glossary-pep-562-lazy-export] pattern already used
  where a subpackage must not import its soft dependency eagerly.
- Nothing is borrowed from graphene-django beyond what `debug.py` already
  embodies; the new README carries spec-044's wire-name narrowing table so
  the [graphene debug migration][glossary-graphene-debug-migration] contract
  stays documented next to the code that honors it.

## User-facing API

New (this package):

```
pip install django-strawberry-framework[debug]
```

Unchanged (both of these work exactly as `0.0.14` documented, when the
extra — or the new package directly — is installed):

```python
from django_strawberry_framework.extensions import DjangoDebugExtension
# or, framework-independent:
from django_strawberry_debug import DjangoDebugExtension

schema = strawberry.Schema(query=Query, extensions=[DjangoDebugExtension])
```

Absence behavior (extra not installed): importing the name raises the
standard [`require_optional_module`][glossary-require_optional_module]
error naming the module and the install hint
(`pip install django-strawberry-framework[debug]`), the same shape every
other soft-dependency seam ships.

## Architectural decisions

### Decision 1 — Extraction, not the in-tree leaf: the split test applied to opposite facts

**Decision**: `DjangoDebugExtension` leaves this distribution for a
standalone package.

**Evidence** (the same standard that rejected the optimizer split): (a) the
import surface is stdlib + Django + graphql-core + Strawberry + one root
`logger` symbol — no type-system contract, no registry, no optimizer; (b)
reverse coupling is zero — no package module imports `extensions/`; (c) the
standalone audience is real: the feature answers "what SQL did this
operation run" for ANY Strawberry+Django schema, and neither
graphene-parity nor framework machinery is needed to use it; (d) the
maintainer's fatigue is per-distribution weight, and this is the only
module where extraction sheds weight without cutting a live seam.

**Alternative rejected**: keeping it as the in-tree leaf (the position this
spec's earlier analysis recommended) — it achieves isolation but not
weight-shedding, and the maintainer's directive is to shed.

### Decision 2 — The name is `django-strawberry-debug`; earned by generality

**Decision**: PyPI name `django-strawberry-debug`, import package
`django_strawberry_debug`.

**Rationale**: the maintainer's naming rule for the extraction — the
generic `django-strawberry-*` family name only if the package works beyond
this framework; `django-strawberry-framework-debug` if proprietary. The
import-surface proof in Decision 1 settles it: the extension is verified
framework-independent, so the generic name is earned. The name deliberately
mirrors this package's family prefix (it is the maintainer's package, not a
`strawberry-graphql-django` ecosystem artifact).

### Decision 3 — The logger swap is the only code change

**Decision**: `debug.py` moves verbatim except its single package import:
`from .. import logger` becomes a module-level
`logger = logging.getLogger("django_strawberry_debug")`.

**Rationale**: byte-level continuity is the cheapest correctness argument —
the 1,019-line suite moves with the code, and every assertion that passes
over the moved pair proves the move changed nothing. Any refactor beyond
the logger line would forfeit that proof and belongs (if ever) to the new
repo's own lifecycle.

### Decision 4 — The framework seam: `[debug]` extra + guarded re-export

**Decision**: `extensions/__init__.py` is rewritten from an eager
re-export into the soft-dependency shape: a
[PEP 562 lazy export][glossary-pep-562-lazy-export] `__getattr__` that
resolves `DjangoDebugExtension` through
[`require_optional_module`][glossary-require_optional_module]`("django_strawberry_debug", ...)`
with an install hint naming the `[debug]` extra. The extra pins
`django-strawberry-debug>=0.1.0`.

**Rationale**: the `0.0.14` release documented exactly one import path for
the extension; preserving it byte-for-byte makes the extraction invisible
to consumers who install the extra. The lazy shape (not an eager
try/except) keeps `import django_strawberry_framework.extensions`
innocent when the soft dependency is absent — the same discipline as
`rest_framework/`.

**Alternatives rejected**: extra-only with the import path dropped
(gratuitous breakage of a shipped path); pure removal with a README
pointer (loses the [graphene debug migration][glossary-graphene-debug-migration]
one-liner and the discoverability of the extra).

**Note on the DRY card**: this card adds only the `debug` extra. The DRY
card's WP-A extras (`drf`, `channels`, `keyset-encryption`,
`debug-toolbar`) land later and inherit the established pattern; its
import-linter contract treats `extensions/` as a soft-dep leaf exactly
like `rest_framework/`.

### Decision 5 — Test relocation: package tier moves, live tier shrinks to the seam

**Decision**: `tests/extensions/test_debug.py` moves to the new repository
with a self-contained harness (minimal Django settings + throwaway models —
no fakeshop). In this package, the debug behavior tests are **not**
replaced: what remains is (a) a soft-dep absence test on the
`sys.modules["django_strawberry_debug"] = None` sentinel shape shared via
`tests/_soft_dependency.py`, and (b) ONE live-tier test in
`examples/fakeshop/test_query/` proving the re-export path end-to-end with
the extra installed — a request over a [probe URLconf][glossary-probe-urlconf]
schema carrying `DjangoDebugExtension` (imported through
`django_strawberry_framework.extensions`) alongside
[`DjangoOptimizerExtension`][glossary-djangooptimizerextension], asserting
the `debug` key arrives and the composability contract holds. The remaining
355 lines of `test_debug_extension_api.py` retire with the moved suite.

**Rationale**: the behavior is now the new package's contract to test; this
package's contract is the seam. Keeping behavior stand-ins here would
violate the retire-the-stand-in discipline the
[live-first coverage mandate][glossary-live-first-coverage-mandate] already
enforces. Coverage: `fail_under = 100` is re-verified after the deletion —
the rewritten `extensions/__init__.py` is fully covered by the absence
sentinel test plus the present-path live test (the dev group installs the
new package, so the present path runs in CI).

### Decision 6 — The strawberry floor stays in the framework

**Decision**: `strawberry-graphql>=0.316.0` remains in this package's
`[project].dependencies`, comment intact. The new package declares the same
floor independently.

**Rationale**: spec-044 Decision 6 raised the floor for
[per-operation extension isolation][glossary-per-operation-extension-isolation]
— a release-wide engine-lifecycle correctness property affecting every
consumer schema **whether or not any debug extension is enabled** (the old
floor shared extension instances and engine-owned execution contexts across
concurrent sync requests). It was never debug-only; it does not travel with
the feature.

### Decision 7 — Lone card at `0.0.15` — Slice 3 owns the version cut

Per the Step 3 scan, this card is the **only** non-Done card at `0.0.15`
(the `0.0.14` line belongs to the in-flight `044`
[joint version cut][glossary-joint-version-cut]; `0.0.16` belongs to the
boundary+DRY card). So this spec mirrors the lone-card shape (spec-038
Decision 14, spec-044 Decision 12): Slice 3 carries the version quintet
(`pyproject.toml` `[project].version`,
`django_strawberry_framework/__init__.py::__version__`,
`tests/base/test_init.py`, the GLOSSARY package-version row, the root
package entry in `uv.lock`), the release-status doc moves, and the
`CHANGELOG.md` entry. No earlier slice moves any of the quintet.

### Decision 8 — TODO anchors stage the unbuilt slices

Per the repo's staging discipline, staged-but-unbuilt slices carry
`TODO(spec-045 Slice N)` source anchors at the sites they will change
(`extensions/__init__.py`, `extensions/debug.py`, `pyproject.toml`'s
optional-dependencies block), removed in the change that ships the slice.
Caveat: the version-quintet sites currently carry `TODO(spec-044 Slice 3)`
anchors owned by the in-flight `0.0.14` cut; this card adds its Slice 3
anchors **only after** spec-044's cut lands and removes them
([Risks](#risks-and-open-questions)).

## Implementation plan

| Slice | Where | Work | Est. delta (this repo) | Risk profile |
|---|---|---|---|---|
| 1 | new repo | scaffold + verbatim move + logger swap + harness + CI + publish `0.1.0` | 0 (additive elsewhere) | LOW — verbatim move, proven suite |
| 2 | this repo | delete `debug.py` + package suite; guarded re-export; `[debug]` extra; absence + seam tests; probe slim | ~−1,850 lines | LOW-MED — coverage re-verify, orphan-import sweep |
| 3 | this repo | docs fold-in + `0.0.15` quintet + card wrap | docs only | mechanical breadth |

Sequencing inside the card is strict: Slice 2 must not land until Slice 1's
`0.1.0` is installable (the dev group and the `[debug]` extra both pin it);
"new package published" precedes "framework deletion".

## Helper-reuse obligations (DRY)

- The guard is [`require_optional_module`][glossary-require_optional_module]
  — no bespoke try/except import machinery.
- The absence test rides the shared `tests/_soft_dependency.py`
  None-sentinel helper — no new absence-simulation shape.
- The live-tier test drives HTTP via [`TestClient`][glossary-testclient] and
  reuses the existing probe-URLconf pattern rather than inventing a new
  harness.
- The new repo's harness is intentionally NOT shared with this repo — a
  cross-repo test dependency would recreate the coupling this card removes.

## Edge cases and constraints

- **Import-time innocence**: after Slice 2,
  `import django_strawberry_framework.extensions` must succeed with the
  soft dependency absent; only attribute access raises. The absence test
  pins this.
- **`__all__` and introspection**: the rewritten `__init__.py` keeps
  `__all__ = ["DjangoDebugExtension"]` and a module `__dir__` so tooling
  sees the name without importing the soft dependency (the established
  PEP 562 shape).
- **Logger continuity**: the moved module logs under
  `"django_strawberry_debug"`, not the framework's logger namespace — the
  new README documents the logger name; nothing in this repo asserted on
  the old namespace (verified: the suite does not pin logger identity).
- **Concurrent sessions**: card `044` is mid-flight ON this feature.
  Slice 1's verbatim move copies the file **as `0.0.14` ships it** — if
  `044` amends `debug.py` before this card executes, the move re-snapshots;
  this spec's line counts are descriptive, not contractual.
- **ASCII-only in `.py`**; trailing-comma layout; ruff format+check after
  every edit; `::QualifiedName` doc references swept when
  `extensions/debug.py` disappears (GLOSSARY/TREE/dry-file docs, Slice 3).

## Test plan

- **New repo (Slice 1)**: the moved 1,019-line suite green on the
  self-contained harness across the CI matrix; the suite IS the proof the
  move preserved behavior ([Decision 3](#decision-3--the-logger-swap-is-the-only-code-change)).
- **This repo (Slice 2)**:
  - absence: sentinel-shape test — attribute access raises the
    install-hint error; module import stays innocent.
  - presence (live tier): one request over the probe schema with both
    extensions; asserts the `debug` key, a
    [Debug SQL row][glossary-debug-sql-row] from the optimized plan, and
    the import path `django_strawberry_framework.extensions`.
  - the full suite green under `fail_under = 100` after the deletion
    (maintainer-invoked gates only, per `AGENTS.md`). Baseline caveat: the
    suite currently carries concurrent-work failures; reconcile with the
    maintainer before gating.
- **Extras**: an isolated-venv install (never the shared `.venv`) of
  `django-strawberry-framework[debug]` resolves the new package and the
  import path works.

## Doc updates

- Slice 1 (new repo): README (opt-in, wire contract, security caveats,
  graphene narrowing table, async boundary, logger name), CHANGELOG `0.1.0`.
- Slice 3 (this repo, the release-status set): `docs/GLOSSARY.md` via the
  glossary DB + re-render (the `DjangoDebugExtension` family entries point
  at the new package + extra; package-version row), `README.md` (feature
  list + install), `docs/README.md`, `docs/TREE.md` regen
  (`extensions/` subtree shrinks to the seam), `TODAY.md`,
  `docs/dry/dry-file-extensions__debug.md` retired,
  `KANBAN.md`/`KANBAN.html` (DB + regen), `CHANGELOG.md` (permission
  granted by this slice). `docs/spec-044-debug_extension-0_0_14.md` stays
  untouched as history.

## Risks and open questions

- **Sequencing behind `044`**: the extension must ship at `0.0.14` before
  it is extracted (extraction of an unreleased feature would rewrite `044`
  mid-flight instead). This card starts only after the `0.0.14` cut lands.
  Preferred answer: hold the whole card, not just Slice 3, behind the cut.
- **Two-repo release choreography**: the framework's `[debug]` pin and the
  new package's version now move independently. Preferred answer: the pin
  stays a floor (`>=0.1.0`) and only rises when the framework's seam test
  actually needs a newer contract; no lockstep releases.
- **New-repo CI baseline**: the framework must not point at a package whose
  own CI is red. Slice 1's definition of done includes a green matrix
  before PyPI publish; Slice 2 is gated on the published artifact.
- **Cross-repo drift**: the wire contract now lives in two docs (the new
  README and this repo's glossary pointers). Preferred answer: the new
  README is authoritative; this repo's glossary entries describe the seam
  and link out, never restating row schemas.

## Out of scope (explicitly tracked elsewhere)

- The boundary+DRY card (`TODO-ALPHA-046-0.0.16`) — depends on this card;
  its contracts are written against the post-extraction tree.
- The spec-044 follow-on list (async SQL capture, knobs, redaction) — moves
  to the new repository's tracker.
- Extraction of any other module — `inspect_django_type` was evaluated in
  the same review and **kept** (agent-facing diagnostic value); the
  [Debug-toolbar middleware][glossary-debug-toolbar-middleware] is
  framework-coupled and stays.

## Definition of done

- [ ] `django-strawberry-debug 0.1.0` on PyPI: verbatim-moved `debug.py`
      (logger swap only), moved suite green on its own harness, CI matrix
      green, README carrying the posture + wire contract + async boundary.
- [ ] This repo: `extensions/debug.py` and `tests/extensions/test_debug.py`
      deleted; `extensions/__init__.py` is the guarded lazy re-export;
      `[debug]` extra + dev-group pin added; absence sentinel test + one
      live seam/composability test in place; probe scaffold slimmed.
- [ ] `pip install django-strawberry-framework[debug]` resolves in an
      isolated venv and
      `from django_strawberry_framework.extensions import DjangoDebugExtension`
      works; with the extra absent, the import-innocence + install-hint
      contract holds.
- [ ] Full suite green under `fail_under = 100` after the deletion.
- [ ] Slice 3 shipped: version quintet at `0.0.15`, GLOSSARY flips,
      `CHANGELOG.md` entry, card flipped Done, `KANBAN.md`/`KANBAN.html`
      regenerated from the DB, `import_spec_terms` green.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[kanban]: ../KANBAN.md

<!-- docs/ -->
[glossary]: GLOSSARY.md
[glossary-djangodebugextension]: GLOSSARY.md#djangodebugextension
[glossary-response-extensions-debug-middleware]: GLOSSARY.md#response-extensions-debug-middleware
[glossary-debug-sql-row]: GLOSSARY.md#debug-sql-row
[glossary-debug-exception-row]: GLOSSARY.md#debug-exception-row
[glossary-django-debug-cursor-capture]: GLOSSARY.md#django-debug-cursor-capture
[glossary-async-sql-capture-boundary]: GLOSSARY.md#async-sql-capture-boundary
[glossary-per-operation-extension-isolation]: GLOSSARY.md#per-operation-extension-isolation
[glossary-strawberry-extension-lifecycle]: GLOSSARY.md#strawberry-extension-lifecycle
[glossary-developer-only-debug-posture]: GLOSSARY.md#developer-only-debug-posture
[glossary-debug-toolbar-middleware]: GLOSSARY.md#debug-toolbar-middleware
[glossary-soft-dependency]: GLOSSARY.md#soft-dependency
[glossary-hard-dependency]: GLOSSARY.md#hard-dependency
[glossary-require_optional_module]: GLOSSARY.md#require_optional_module
[glossary-pep-562-lazy-export]: GLOSSARY.md#pep-562-lazy-export
[glossary-probe-urlconf]: GLOSSARY.md#probe-urlconf
[glossary-testclient]: GLOSSARY.md#testclient
[glossary-graphene-debug-migration]: GLOSSARY.md#graphene-debug-migration
[glossary-joint-version-cut]: GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: GLOSSARY.md#live-first-coverage-mandate
[glossary-djangooptimizerextension]: GLOSSARY.md#djangooptimizerextension

<!-- docs/SPECS/ -->
[spec-038]: SPECS/spec-038-auth_mutations-0_0_13.md
[spec-044]: spec-044-debug_extension-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[pypi-django-strawberry-debug]: https://pypi.org/project/django-strawberry-debug/
