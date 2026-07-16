# DRY review: `django_strawberry_framework/rest_framework/__init__.py`

Status: verified

## System trace

The target (~61 lines) is the soft-dependency gate for the entire
`rest_framework/` package. It owns three things and nothing else:

- `_DRF_INSTALL_HINT` — the single install-hint string naming the verified floor
  `djangorestframework>=3.17.0` (place 2 of the three-places-that-must-agree);
- `require_drf()` — the named DRF guard, a thin wrapper over
  `utils/imports.py::require_optional_module("rest_framework", install_hint=…)`;
- module-body `require_drf()` — so
  `import django_strawberry_framework.rest_framework` (and every submodule under
  it) raises that hint when DRF is absent, before any sibling that does
  `from rest_framework import …` can load.

Connected behavior examined:

- **Raising primitive.** `utils/imports.py::require_optional_module` is already
  the single optional-import owner (no memoization, chained `ImportError`, no
  `feature_label`). The target delegates; it does not re-implement import
  handling.
- **Soft-dep siblings (different opt-in postures, same primitive):**
  - `routers.py::require_channels` — module import stays clean; PEP 562
    `__getattr__` fires the guard on symbol access;
  - `middleware/debug_toolbar.py::require_debug_toolbar` — leaf-import gate
    (Django `MIDDLEWARE` `import_string`), plus a second `INSTALLED_APPS` gate
    unique to that leaf;
  - `keyset.py` — call-site `require_optional_module` for `cryptography` under
    `Meta.cursor_field` (no named `require_*` wrapper; feature-gated, not a
    package opt-in).
- **Root lazy exports.** `django_strawberry_framework/__init__.py::__getattr__`
  resolves `_DRF_SOFT_EXPORTS` by importing this package (which runs the
  import-time guard) then calling `require_drf()` again so a later eviction of
  `rest_framework` still re-hits the guard without memoizing into root globals
  (Decision 12).
- **Sibling RF modules (evidence only; still open plan items).** `sets.py`,
  `inputs.py`, `resolvers.py`, `serializer_converter.py` import DRF at module
  top and rely on this package `__init__` for the absent path.
  `hook_context.py` defines frozen dataclasses with no DRF import, but is still
  behind this gate because root soft-exports and package import both route
  through it — product boundary of the serializer surface, not a second guard.
- **Tests.** `tests/rest_framework/test_soft_dependency.py` pins
  `_HINT_SUBSTRING = "djangorestframework>=3.17.0"`, simulates absence via
  `tests/_soft_dependency.py::simulated_absence`, and covers package import,
  `sets` import, every root soft export, star-import F1, and non-memoization.
  Shared absence helper already consolidates the eviction discipline across DRF /
  channels / toolbar suites.
- **Baseline.** `git diff e21508c27e4e21603f2f0ee92da5bc9e52c73b9d -- …/rest_framework/__init__.py`
  is empty; working tree matches baseline for this file.

## Verification

Searches (package + tests):

- `require_drf` / `_DRF_INSTALL_HINT` / `djangorestframework>=3.17.0` —
  production hint single-sited here; pyproject `[dependency-groups].dev` pin and
  test `_HINT_SUBSTRING` are the intentional other two places; root
  `__getattr__` and soft-dep tests are the consumers.
- `require_optional_module` — four production call sites wrapping or using the
  primitive (`require_drf`, `require_channels`, `require_debug_toolbar`,
  keyset cryptography). No fifth hand-rolled `try/importlib` raise-with-hint
  pattern for DRF.
- `from rest_framework` / `import rest_framework` under
  `django_strawberry_framework/rest_framework/` — only in sibling modules after
  this gate; none in `hook_context.py`.
- Soft-dep posture comparison with `middleware/` (clean package marker + leaf
  gate) and `routers.py` (lazy symbol gate) — same raising primitive, different
  opt-in boundaries by design.

Disproved / rejected candidates (strongest first):

1. **Further collapse `require_drf` / `require_channels` /
   `require_debug_toolbar` into a shared factory beyond
   `require_optional_module`.** The raising policy already has one owner. Each
   wrapper's job is naming the feature, owning the hint string, and fixing the
   opt-in posture (package-import vs leaf-import vs `__getattr__`). A
   meta-factory would hide those posture differences behind flags and fight
   `utils/imports.py::require_optional_module`'s explicit "no `feature_label`"
   contract. **Rejected.**

2. **Unify this package's import-time gate with `routers.py`'s lazy PEP 562
   posture (or with `middleware/`'s clean-package + leaf gate).** Contracts
   differ: consumers may `import …rest_framework` / submodule paths and must get
   the hint immediately; Channels stays off until `asgi.py` reaches the router
   symbol; toolbar stays off until Django resolves the leaf `MIDDLEWARE` path.
   Forcing one posture would break at least one public import contract.
   **Rejected.**

3. **Collapse the three-places floor (`pyproject` pin, `_DRF_INSTALL_HINT`,
   test `_HINT_SUBSTRING`) into one imported constant.** The drift-catch
   discipline is intentional — re-typing the floor in the test and pin catches
   silent hint edits. Consolidating would defeat the detector.
   **Rejected.**

4. **Treat root `__getattr__`'s second `require_drf()` as redundant with the
   import-time call.** After the package is loaded, eviction of third-party
   `rest_framework` must still raise on the next soft-export access;
   import-time runs only once per package load. Non-memoizing re-fire is the
   Decision 12 contract pinned by
   `test_successful_lookup_does_not_memoize`. Ownership of that second call
   sits on the root `__init__` item, not here. **Rejected** (for this target).

5. **Exempt `hook_context.py` from the package gate because it has no DRF
   import.** Soft-exporting `SerializerHookContext` / `UploadMetadata` without
   DRF would split the serializer surface's absent-DRF contract (root lookup
   vs package import vs submodule import). Not duplication of a guard — one
   gate covering the whole package surface. Sibling file item may revisit
   content; the gate ownership stays here. **Rejected.**

6. **Add a named `require_cryptography` in keyset (or move keyset onto a
   `require_*` wrapper pattern "for symmetry").** keyset's call-site use of the
   shared primitive is the correct shape for a feature-gated optional import;
   inventing a wrapper for symmetry would add ceremony without a second call
   site. Out of this target's ownership. **Deferred** to `keyset` / project
   pass if anyone proposes it.

No scratch experiment needed: contracts are covered by
`tests/rest_framework/test_soft_dependency.py` and the shared absence helper;
static ownership of the hint + thin wrapper is unambiguous from source.

## Opportunities

None — the target already single-sites the DRF install hint and delegates the
raising import to `utils/imports.py::require_optional_module`. Soft-dep siblings
share that primitive while intentionally keeping distinct opt-in postures and
feature-owned hint strings. No production edit preserves behavior better than
the current ownership.

## Judgment

Zero-edit. This file is the DRF soft-dep feature owner in the intended thin-
wrapper shape; further consolidation would either move hint ownership away from
the feature, hide opt-in posture differences, or defeat intentional drift
checks. Item-scoped diff vs `ITEM_BASELINE` remains empty. Ready for Worker 2.

## Independent verification (Worker 2)

Scoped diff vs `ITEM_BASELINE`
(`e21508c27e4e21603f2f0ee92da5bc9e52c73b9d`) is empty for
`django_strawberry_framework/rest_framework/__init__.py`.

Re-traced ownership: `_DRF_INSTALL_HINT` + `require_drf()` →
`utils/imports.py::require_optional_module`, module-body gate, root
`__getattr__` / `_DRF_SOFT_EXPORTS` consumers, sibling top-level
`from rest_framework import …` modules (inputs/sets/resolvers/serializer_converter),
DRF-free `hook_context.py` still behind the package gate, and
`tests/rest_framework/test_soft_dependency.py` + shared
`tests/_soft_dependency.py::simulated_absence`. Production hint string is
single-sited; no fifth hand-rolled DRF `try/importlib` raise-with-hint.

Challenged rejected candidates — all stand:

1. **Meta-factory over `require_drf` / `require_channels` /
   `require_debug_toolbar`.** Same primitive already owns raising policy;
   wrappers only name the feature, own the hint, and fix opt-in posture.
   A factory with posture flags would fight the no-`feature_label` contract.
   **Upheld.**
2. **Unify import-time / PEP 562 / clean-package+leaf postures.** Public
   contracts differ (package import must hint immediately; Channels waits for
   symbol access; toolbar waits for leaf `MIDDLEWARE` import). **Upheld.**
3. **Collapse floor literals into one imported constant.** Drift-catch
   requires re-typed sites. Labeling note only: the DRF
   three-places-that-must-agree are pyproject pin, `_DRF_INSTALL_HINT`, and
   spec-039 Risks (not the test `_HINT_SUBSTRING`); the test substring is the
   separate re-typed detector of place 2's floor. Consolidation remains wrong
   either way. **Upheld** (substance).
4. **Drop root `__getattr__`'s second `require_drf()`.** Needed after
   eviction once the package is already loaded (Decision 12 /
   `test_successful_lookup_does_not_memoize`). Owner is root `__init__`, not
   this file. **Upheld.**
5. **Exempt `hook_context` from the package gate.** Soft-exporting frozen
   hook types without DRF would split the serializer-surface absent-DRF
   contract. **Upheld.**
6. **`require_cryptography` symmetry in keyset.** Feature-gated call-site use
   of the primitive is correct; out of this target's ownership. **Upheld**
   (deferred).

Missed-consolidation search: no alternate DRF install-hint owner; submodule
import always loads this parent first so the gate is not bypassable; converters
soft-import (`return None`) is a different contract from this raising guard.
No production edit improves DRY here.

Outcome: **verified** zero-edit.
