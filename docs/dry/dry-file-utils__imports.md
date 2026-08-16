# DRY review: `django_strawberry_framework/utils/imports.py`

Status: verified

## System trace

Owner of the package's four optional-/deferred-import primitives:

1. **`import_attr_if_importable`** — best-effort `import_module` + fail-loud
   `getattr`; `None` on `ImportError` only. Callers: `registry._clear_if_importable`
   (per-type connection-cache eviction), `types/converters` postgres
   `ArrayField`/`HStoreField`, and (after this item) `optimizer/nested_planner`
   `BTreeIndex`.
2. **`loaded_attr`** — already-in-`sys.modules` only; never imports. Sole
   production caller: `types/finalizer` auth bind (`bind_auth_mutations`) so an
   auth-free process never pays the auth import.
3. **`import_attr`** — strict `getattr(import_module(...), ...)`. Sole production
   caller: `mutations/sets.resolver_seams` (function-local resolver-module cycle
   guard for generated `resolve_sync`/`resolve_async`).
4. **`require_optional_module`** — raise `ImportError(install_hint)` chained from
   the original. Thin feature wrappers own hint strings:
   `routers.require_channels`, `auth/sessions.require_channels` (distinct
   Channels hint), `rest_framework.require_drf`,
   `middleware/debug_toolbar.require_debug_toolbar`, `keyset` cryptography load.

Connected surfaces examined: `utils/inputs._safe_import` (attr-lenient wrapper),
package-root `__getattr__` (DRF soft exports after `require_drf`), auth/forms
function-local `from ..mutations import resolvers` cycle guards, patch modules'
import-time soft sentinels, `management/commands/_imports` CommandError
translation, `sets_mixins.resolve_lazy_class` / Django `import_string`,
`utils/querysets` Django-version `PROHIBITED_FILTER_KWARGS` fallback,
`routers._build_router_class` post-guard broken-install reframes.

Item-scoped baseline `9f33db5d20200f0fba17cce2a02e43578d8c38d0` started empty
for the target; this item's tracked edits are listed under Implementation.

## Verification

- Grep of the four symbols, `importlib`/`sys.modules`/`except ImportError`, and
  `INSTALL_HINT` / `require_*` confirmed every production consumer of the
  primitives and every leftover soft-import shape.
- `_clear_if_loaded` is gone from `registry.py`; only a stale docstring /
  finalizer comment still named it (ownership drift, not a live second site).
- Probe: `import_attr_if_importable("django.contrib.postgres.indexes",
  "BTreeIndex")` is identity-equal to the real `BTreeIndex` when postgres is
  present; a `sys.modules[...] = None` sentinel returns `None` (same
  test-isolation shape the helpers already document).
- No pytest run (deferred per cycle policy). Permanent pin added under
  `tests/optimizer/test_nested_index_advisory.py`.

Strongest rejected candidates:

- **`_safe_import` → collapse into `import_attr_if_importable`.** Wrapper
  deliberately swallows `AttributeError` (attr-lenient lifecycle clear);
  primitive fails loud on missing attr. Documented + tested divergence;
  promoting lenience into the owner (or a mode flag) would blur the package
  default.
- **Dual `require_channels` (routers vs auth/sessions).** Same primitive, two
  feature-owned install hints by design (`require_optional_module` forbids a
  shared `feature_label`; hints stay at the feature owner).
- **Patch soft-imports (`_cross_web_patches` / `_strawberry_patches` /
  `_django_patches`).** Import-time `from X import Y` → module sentinel:
  missing *name* is `ImportError` (soft), not the primitive's loud
  `AttributeError`; strawberry patch fails *atomically* across two packages.
  Different contract from optional-attr soft-import.
- **Auth / forms function-local `from ..mutations import resolvers`.** Whole-
  module cycle guards needing multiple symbols — not the attr-lookup seam
  `import_attr` owns (`resolver_seams` already uses that).
- **Root `__getattr__` `import_module` after `require_drf`.** Optional policy
  already single-sited at `require_drf`; leftover load is package-relative
  deferred import, not a fourth optional-import pattern.
- **`routers._build_router_class` try/except after `require_channels`.**
  Present-but-broken install reframes (`_CHANNELS_BROKEN_HINT` /
  `_STRAWBERRY_CHANNELS_BROKEN_HINT`), deliberately distinct from absence
  install hints.
- **`querysets.PROHIBITED_FILTER_KWARGS` try/except.** Django-version compat
  constant, not an optional dependency.
- **`management/commands/_imports` / `import_string`.** CLI `CommandError`
  translation and dotted-path consumer resolution — different owners.

## Opportunities

### 1. nested_planner `BTreeIndex` soft-import → `import_attr_if_importable`

- **Repeated responsibility:** optional `django.contrib.postgres` symbol →
  `None` when unimportable, fail loud when the module loads but the class is
  missing (same policy as `types/converters` Array/HStore).
- **Sites:** `optimizer/nested_planner.py` (inline `try`/`except Exception`);
  already-canonical `types/converters.py`.
- **Evidence:** same optional postgres contrib; prior `except Exception` was
  broader than package policy and duplicated the soft-import shape outside the
  owner named by the module docstring.
- **Owner:** `utils/imports.py::import_attr_if_importable`.
- **Consolidation:** replace the inline try/except with
  `import_attr_if_importable("django.contrib.postgres.indexes", "BTreeIndex")`.
- **Proof:** `test_btree_index_soft_import_uses_shared_optional_import_owner`
  (identity vs helper + real `BTreeIndex` + `_BTREE_INDEX_TYPES` membership).
  Existing advisory BTreeIndex matrix still covers behavior.
- **Risks / non-goals:** absence path that previously swallowed any `Exception`
  now only soft-fails on `ImportError` (aligned with converters); a broken
  postgres.indexes module missing `BTreeIndex` fails loud — intentional.

### 2. Stale `_clear_if_loaded` ownership docs

- **Repeated responsibility:** none (docs only) — incorrect call-site map for
  `loaded_attr`.
- **Sites:** `utils/imports.py` module docstring; `types/finalizer.py` comment.
- **Evidence:** symbol absent from `registry.py`; sole live `loaded_attr` caller
  is finalizer auth bind.
- **Owner:** this module's docstring (and the finalizer comment that pointed at
  the dead symbol).
- **Consolidation:** rewrite the docstring call-site list; drop the dead
  `_clear_if_loaded` reference from the finalizer comment.
- **Proof:** grep `_clear_if_loaded` under `django_strawberry_framework/` is empty
  after the edit.
- **Risks / non-goals:** no behavior change.

## Judgment

One real leftover optional-import policy site (`nested_planner` BTreeIndex)
moved onto the owner; ownership docs corrected. The four primitives already
partition the package's import policies cleanly; remaining try/except ImportError
shapes are intentional distinct contracts (patches, version-compat, broken-install
reframes, CLI CommandError, cycle-guard module imports).

## Implementation (Worker 1)

- Migrated `optimizer/nested_planner.py` `_PostgresBTreeIndex` onto
  `import_attr_if_importable`.
- Updated `utils/imports.py` module docstring call-site map; fixed finalizer
  comment.
- Permanent test:
  `tests/optimizer/test_nested_index_advisory.py::test_btree_index_soft_import_uses_shared_optional_import_owner`.
- Docstring touch: `tests/utils/test_imports.py`.
- `uv run ruff format .` + `uv run ruff check --fix .` clean.
- Deferred pytest (cycle policy). Changelog: no (internal DRY; no public API).

Item-scoped diff vs `9f33db5d20200f0fba17cce2a02e43578d8c38d0`:
`utils/imports.py`, `optimizer/nested_planner.py`, `types/finalizer.py`,
`tests/optimizer/test_nested_index_advisory.py`, `tests/utils/test_imports.py`,
plus this artifact.

Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced the four primitives end-to-end against present-day source (not the
diff alone). Call-site map matches the updated docstring:

- ``import_attr_if_importable`` → ``registry._clear_if_importable``,
  ``types/converters`` Array/HStore, ``optimizer/nested_planner`` BTreeIndex,
  and ``utils/inputs._safe_import`` (wrapper).
- ``loaded_attr`` → sole production caller ``types/finalizer`` auth bind.
- ``import_attr`` → sole production caller ``mutations/sets.resolver_seams``.
- ``require_optional_module`` → ``routers.require_channels``,
  ``auth/sessions.require_channels``, ``rest_framework.require_drf``,
  ``middleware/debug_toolbar.require_debug_toolbar``, ``keyset`` cryptography.

**Consolidation challenged.** Prior nested_planner shape was
``try: from ... import BTreeIndex except Exception`` — broader than package
policy and outside the owner converters already use. Present binding is
identity-equal to ``import_attr_if_importable("django.contrib.postgres.indexes",
"BTreeIndex")`` and to real ``BTreeIndex`` (probe). Soft ``ImportError`` /
loud missing-attr contracts match converters. No other
``django.contrib.postgres`` soft-import left outside the owner.
``_clear_if_loaded`` is absent under ``django_strawberry_framework/``; docstring
+ finalizer comment no longer name it.

**Rejected candidates challenged (kept separate with evidence):**

- ``_safe_import``: tested attr-lenience (``AttributeError`` → ``None``) vs
  primitive's loud ``AttributeError`` — collapse would blur the package
  default; wrapper is correct.
- Dual ``require_channels``: distinct feature-owned hints
  (router vs auth-session wording); primitive forbids shared
  ``feature_label`` by design.
- Patch soft-imports: import-time name soft-fail + atomic multi-package
  sentinel (``_strawberry_patches``) — not optional-attr soft-import.
- Auth function-local ``from ..mutations import resolvers``: whole-module
  cycle guards needing many symbols; forms already use ``resolver_seams`` /
  ``import_attr`` (artifact's "auth/forms" label is slightly loose; rejection
  still holds for the auth sites).
- Root ``__getattr__``: optional policy already at ``require_drf``; leftover
  is package-relative deferred load after the guard.
- ``routers._build_router_class`` post-guard try/except: broken-install
  reframes (``_CHANNELS_BROKEN_HINT`` /
  ``_STRAWBERRY_CHANNELS_BROKEN_HINT``), not absence.
- ``PROHIBITED_FILTER_KWARGS``: Django-version compat constant.
- ``management/commands/_imports`` / ``import_string``: CLI ``CommandError``
  and dotted-path resolution — different owners.

**Missed consolidations.** Independent ``except ImportError`` /
``importlib`` / ``sys.modules`` sweep found no further optional-attr soft-import
that shares the primitive contract. Finalizer expansion ``ImportError`` →
``ConfigurationError`` is finalize error translation, not an import helper.

**Scoped diff.** Vs ``9f33db5d20200f0fba17cce2a02e43578d8c38d0`` only the five
claimed paths (+ this artifact): ``utils/imports.py``,
``optimizer/nested_planner.py``, ``types/finalizer.py``,
``tests/optimizer/test_nested_index_advisory.py``,
``tests/utils/test_imports.py``. No concurrent absorption.

**Proof.** Permanent pin
``test_btree_index_soft_import_uses_shared_optional_import_owner`` asserts
identity with the shared helper and real ``BTreeIndex`` (file already imports
postgres indexes for the advisory matrix). Pytest deferred per cycle policy.

Verdict: verified. Plan checkbox marked.
