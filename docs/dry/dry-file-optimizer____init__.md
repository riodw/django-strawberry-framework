# DRY review: `django_strawberry_framework/optimizer/__init__.py`

Status: verified

## System trace

The target is the `optimizer` subpackage surface: module docstring, two eager
re-exports (`DjangoOptimizerExtension` from `extension.py`, `logger` from the
package root), and `__all__ = ("DjangoOptimizerExtension", "logger")`. It
defines no planning, caching, or fetch policy.

Owned responsibility:

- advertise the subpackage as the home of selection-driven queryset planning;
- make `from django_strawberry_framework.optimizer import DjangoOptimizerExtension`
  the canonical subpackage import (root also re-exports that name as the
  default N+1 recipe);
- re-export the single package `logger` so the
  `"django_strawberry_framework"` literal stays in one source location and
  intra-subpackage modules can use `from . import logger`;
- keep internal planner symbols (`OptimizationPlan`, `plan_optimizations`,
  etc.) on their dotted module paths — not consumer-facing API.

Connected behavior examined:

- Package root `__init__.py` — declares the canonical `logger`; eagerly
  imports `DjangoOptimizerExtension` from this module and `OptimizerHint`
  from `optimizer.hints` (bypassing this `__init__`); root `__all__` includes
  the extension and hint but not `logger` (LOGGING key is still public by
  name).
- `optimizer/extension.py` — owns `DjangoOptimizerExtension` and related
  apply/cache seams; `from . import logger`. Sibling file item still open.
- `optimizer/walker.py` — owns `plan_optimizations` / relation planning;
  `from . import logger`. Sibling file item still open.
- `optimizer/nested_planner.py` — also `from . import logger` (connected
  evidence only; not a plan item). Same re-export contract as the other
  siblings.
- Cross-package logger consumers: `types/resolvers.py` and
  `types/finalizer.py` import `logger` via this re-export; `extensions/debug.py`
  imports `from .. import logger` directly (no optimizer dependency).
- Consumers of the extension: root `__init__`, `docs/README.md`, glossary,
  fakeshop schemas/tests — root import path is the documented consumer
  surface; subpackage path remains the load-bearing re-export root uses.
- Tests pinning the re-export identity:
  `tests/base/test_init.py::test_optimizer_subpackage_reexports_top_level_logger`,
  plus optimizer extension/walker tests that bind caplog to the re-exported
  logger.
- Baseline `git diff 839667537562aaf6b001e2ddd3dd4e1637490e30 -- …/optimizer/__init__.py`
  was empty before this pass; working-tree edit is docstring-only (see
  Implementation).

## Verification

Searches:

- `from . import logger` / `from .. import logger` / `getLogger("django_strawberry_framework")`
  — one `getLogger` site (package root); optimizer re-exports; debug uses root;
  three optimizer siblings + two `types/` modules use the optimizer handle.
- `DjangoOptimizerExtension` import sites — production consumers hit root or
  this re-export; internals and focused tests also import the leaf
  `optimizer.extension` module for private helpers.
- Package `__init__.py` export postures — root (eager default recipe),
  `extensions/` / `auth/` (eager opt-in, root-clean), `middleware/` (empty
  soft-dep marker). Optimizer matches the root-eager hard-dep pattern, not
  the opt-in or soft-empty patterns.
- Scratch identity check (`uv run python -c …`):
  `django_strawberry_framework.logger is optimizer.logger is
  extension.logger is walker.logger is nested_planner.logger is
  extensions.debug.logger` — all `True`.

Rejected / deferred candidates (tried to disprove shared ownership):

1. **Widen this `__init__` into the full inward-facing optimizer contract
   (`_context` names, `resolver_key`, `FieldMeta`, `OptimizerHint`,
   connection-facing symbols).** Deferred: that packaging seam is a deliberate
   future boundary (versioned design), not present-day duplicated policy this
   DRY item can consolidate without inventing the import-linter contract that
   makes the widening load-bearing. Leaf imports remain correct until that
   seam lands. Sibling file/folder items still own those modules.
2. **Re-export `OptimizerHint` here so root can
   `from .optimizer import DjangoOptimizerExtension, OptimizerHint`.**
   Disproved for this pass: consumers already take the hint from the package
   root; internals correctly import `optimizer.hints`. Adding the name to
   this `__all__` widens the subpackage surface without a single change axis
   today (same deferral as (1)).
3. **Retarget `types/resolvers.py` / `types/finalizer.py` to
   `from .. import logger`.** Disproved as a consolidation: those modules
   already depend on optimizer private/public symbols; using the subpackage
   logger handle is coherent. `extensions/debug.py` correctly uses root
   because it must not pull the optimizer. Two import paths, one logger
   object — not two logger policies.
4. **Drop the logger re-export; have siblings import from the package root.**
   Disproved: would demote a production contract to test-only and break the
   documented `from . import logger` intra-subpackage handle plus the pinned
   `optimizer import logger` identity test.
5. **Move canonical `getLogger(...)` into `optimizer/`.** Disproved: root owns
   the LOGGING-config key and must declare the logger before subpackage
   imports; inverting ownership recreates the dual-literal risk the re-export
   exists to prevent.
6. **Shared “eager re-export `__init__` helper” across packages.** Disproved:
   packaging idiom, not a mutable rule with one change axis.
7. **Empty this `__init__` like `middleware/`.** Disproved: hard dependency and
   root-eager default recipe; emptying would break the documented import and
   root re-export.
8. **Collapse docstring / glossary / README optimizer import examples.**
   Disproved for this file: standing docs document the public import; the
   module docstring states the local re-export contract.

## Opportunities

1. **Repeated responsibility:** accurate inventory of production modules that
   depend on this module's `logger` re-export (the load-bearing consumer set
   the docstring claims).
   - **Sites:** module docstring vs `extension.py` / `walker.py` /
     `nested_planner.py` (`from . import logger`).
   - **Evidence:** identity check shows all three siblings bind the same
     re-exported logger; the docstring previously named only two, so the
     contract text understated a real production consumer
     (`nested_planner.py`, traced as connected evidence only).
   - **Owner:** this module's docstring (the re-export's contract narration).
   - **Consolidation:** name all three sibling consumers; no symbol or
     `__all__` change.
   - **Proof:** existing
     `tests/base/test_init.py::test_optimizer_subpackage_reexports_top_level_logger`
     plus the scratch identity check; no new permanent test required for a
     docstring inventory fix.
   - **Risks / non-goals:** does not invent a plan item for
     `nested_planner.py`; does not widen inward-facing re-exports; does not
     retarget cross-package logger imports.

## Judgment

This `__init__` is a thin, intentional dual re-export: consumer-facing
`DjangoOptimizerExtension` plus the single package logger for intra-subpackage
use. No policy duplication lives here; the only warranted change was docstring
accuracy about who depends on the logger re-export. Broader surface promotion
belongs to a future packaging boundary, not this file's DRY pass.

## Implementation (Worker 1)

- **Owner chosen:** `optimizer/__init__.py` module docstring.
- **Migrated:** docstring consumer inventory now lists `extension.py`,
  `walker.py`, and `nested_planner.py`; wording adjusted from “both” to
  “those” production siblings.
- **Kept separate:** `__all__` still only `DjangoOptimizerExtension` and
  `logger`; no inward-API widening; no caller retargets; sibling optimizer
  modules untouched.
- **Validation:** scratch logger-identity check (all import paths identical);
  `uv run ruff format .` and `uv run ruff check --fix .` after the edit.
- **Rejected findings:** items 1–8 in Verification — strongest deferred is
  inward-facing API promotion; strongest rejected is dropping or relocating
  the logger re-export.
- **Changelog:** no — docstring accuracy only; not a user-visible behavior
  change. Maintainer authorization required before any CHANGELOG edit.

## Independent verification (Worker 2)

Re-traced the target as a dual re-export only (no planning/caching/fetch
policy). Item-scoped diff vs `839667537562aaf6b001e2ddd3dd4e1637490e30` is
docstring-only; `__all__` and import lines unchanged.

**Docstring consolidation challenged.** Production `from . import logger`
sites under `optimizer/` are exactly `extension.py`, `walker.py`, and
`nested_planner.py` — no fourth sibling. The post-fix inventory matches.
Cross-package `types/resolvers.py` / `types/finalizer.py`
(`from ..optimizer import logger`) also bind the re-export; omitting them
from the sibling-scoped docstring is correct (different import form; artifact
rejected retarget already). The “would break those siblings, not just the
tests” contrast remains accurate for the intra-subpackage contract it
documents.

**Export surface confirmed.** `__all__ = ("DjangoOptimizerExtension",
"logger")`. Scratch identity: root / optimizer / extension / walker /
nested_planner / debug loggers are one object; root
`DjangoOptimizerExtension` is the class from this re-export;
`OptimizerHint` is root-exported from `optimizer.hints` and absent from this
package attribute set. Internal planner symbols stay on dotted paths.

**Deferred / rejected challenged.** (1)–(2) inward/`OptimizerHint` widening
still invent a packaging seam without a present change axis. (3) types/
logger paths stay coherent with their optimizer dependency; debug correctly
avoids the subpackage. (4)–(5) dropping or relocating `getLogger` would
undo the single-literal contract. (6)–(8) packaging idiom / hard-dep /
standing-doc narration — not mutable shared policy. No missed consolidation
on this thin surface; sibling module DRY stays on open plan items.

**Proof reused.** `tests/base/test_init.py::test_optimizer_subpackage_reexports_top_level_logger`
plus fresh identity scratch (all `True`). No production edits by Worker 2.
