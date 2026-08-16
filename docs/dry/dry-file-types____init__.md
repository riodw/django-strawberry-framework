# DRY review: `django_strawberry_framework/types/__init__.py`

Status: verified

## System trace

The target is the `types/` subpackage public facade (~35 lines). It owns one rule:
which names are the curated `django_strawberry_framework.types` consumer surface.
That rule is stated once as three eager re-exports (`DjangoType` from `.base`,
`finalize_django_types` from `.finalizer`, `SyncMisuseError` from `.relay`) backed
1:1 by `__all__`. The module defines no functions, classes, registries, caches, or
lifecycle callbacks.

Docstring also records (a) that the seven sibling modules are an internal layout,
(b) that the same three names are also on the package root, and (c) the one-way
`types` → `optimizer` import-direction rule (with the sanctioned
`optimizer/walker.py` lazy leaf exception). Those are navigation / coupling
invariants, not a second export table.

Connected surfaces traced (siblings still open — evidence only, not absorbed):

- `types/base.py` — defines `DjangoType` (and private helpers such as
  `_is_relay_shaped`).
- `types/finalizer.py` — defines `finalize_django_types` and the once-only
  finalization gate.
- `types/relay.py` — owns Relay Node install helpers; re-exports
  `SyncMisuseError` via the redundant-alias form
  (`from ..utils.querysets import SyncMisuseError as SyncMisuseError`) so
  `from …types.relay import SyncMisuseError` and this facade stay stable after
  the class moved to `utils/querysets.py`.
- Package root `__init__.py` — `from .types import DjangoType, SyncMisuseError,
  finalize_django_types` and lists all three in root `__all__`. Intentional
  dual-path facade (already judged the same way in the root DRY item).
- `permissions.py` — separate `SyncMisuseError` re-export from
  `utils.querysets` for the cascade error surface
  (`from django_strawberry_framework.permissions import SyncMisuseError`).
  Does not feed the types facade or the root `__all__` row for that name.
- `utils/querysets.py` — true definition site of `SyncMisuseError`.
  `utils/__init__.py` deliberately does **not** re-export it (private-ish utils
  package; public paths are types / root / permissions).
- In-package consumer of this facade: `list_field.py` imports `DjangoType` via
  `from .types import DjangoType` while taking `SyncMisuseError` from the true
  owner (`utils.querysets`) — correct split of public type vs shared error.
- External consumers (fakeshop schemas, nearly all package tests) prefer the
  package-root path. No production/test site uses
  `from django_strawberry_framework.types import DjangoType|…` as a three-name
  import; the dotted path is the documented alternate and the import gate for
  the root facade.

Item-scoped baseline
`git diff a17f85ea2f624fe30eb4cf714b0ae75e6cbcc929 --
django_strawberry_framework/types/__init__.py` was empty at review start and
remains empty after this pass (artifact-only).

## Verification

Searches / checks:

- Repo-wide `from django_strawberry_framework.types import`,
  `SyncMisuseError` re-export sites, and `finalize_django_types` import paths.
- Compared every subpackage `__init__.py` export shape: eager re-export +
  `__all__` is the shared packaging idiom (`forms/`, `mutations/`, `optimizer/`,
  `extensions/`, …), not a shared changeable policy object.
- Runtime identity probe (`uv run python`):
  - `dsf.DjangoType is types.DjangoType is types.base.DjangoType`
  - `dsf.finalize_django_types is types.finalize_django_types is
    types.finalizer.finalize_django_types`
  - `dsf.SyncMisuseError is types.SyncMisuseError is types.relay.SyncMisuseError
    is utils.querysets.SyncMisuseError is permissions.SyncMisuseError`
  - `types.__all__` is exactly the three curated names; each root binding is
    identity-equal to the types binding.
- Confirmed `types/relay.py` has no `class SyncMisuseError` body — alias only.

Strongest rejected candidates:

1. **Collapse dual root + `types` export of the three names into one path.**
   Disproved: distinct product contracts. Root is the default recipe; this file
   is the dotted-path convenience surface and the single import site the root
   uses to bind those three names. Identity checks prove both paths converge on
   the defining objects. Collapsing either path would break a documented dual
   surface (same judgment as root / `forms/__init__` DRY items). Not duplicated
   behavior — duplicated *names* at supported boundaries.

2. **Import `SyncMisuseError` in this `__init__` directly from
   `utils.querysets` instead of via `.relay`.** Disproved as a consolidation:
   within `types/`, the alias already has one owner (`types/relay.py`). Routing
   the facade through that alias keeps a single types-package binding site for
   the historical Relay public path and this `__all__` entry. Importing from
   `utils` here *and* keeping the relay alias would create two alias statements
   inside `types/` with nothing gained. Removing the relay alias would break
   `from …types.relay import SyncMisuseError` (still used by several tests).

3. **Treat `permissions.py`'s `SyncMisuseError` re-export as duplication this
   file should absorb or delete.** Disproved: different consumer domain
   (cascade visibility error surface vs type-system / Relay dotted path). Both
   are redundant-alias re-exports of the same `utils.querysets` class;
   permissions does not participate in this `__all__` or in root's types-sourced
   binding. Ownership of that alias stays with the permissions item / folder
   pass — not absorbed here.

4. **Shared `build_public_exports()` helper across subpackage `__init__`
   files.** Disproved: packaging idiom, not one responsibility that must change
   together. A helper would obscure the import/`__all__` 1:1 correspondence for
   zero behavioral gain (`DRY.md`: do not optimize for fewer lines when
   ownership is obscured).

5. **Widen `__all__` to expose converters / definition / relay helpers /
   `apply_interfaces` / `decode_global_id`.** Disproved: intentional
   encapsulation. The docstring names those as internal dotted-submodule paths.
   Widening would duplicate the curated-surface decision the root already makes
   (root pulls file/image converter types from `.types.converters` directly, not
   through this facade). Sibling file items own those modules.

6. **Docstring tension ("canonical" dotted path vs "also at package root").**
   Wording polish only; both paths are supported and identity-pinned. Not a
   duplicated responsibility and not edited here.

No permanent production edit. No pytest (deferred to maintainer / final gate).
No ruff run (no `.py` edit).

## Opportunities

None — the target is already the single authoritative public export of the three
type-system consumer names under `django_strawberry_framework.types`. Behavior
lives in `base` / `finalizer` / `utils.querysets` (via the `relay` alias);
this file only curates the dotted path. Dual root re-export and the
permissions-local `SyncMisuseError` alias are intentional boundary aliases, not
parallel implementations.

## Judgment

Proved zero-edit. Thin, correctly bounded package marker; consolidations that
looked available were dual-path convenience or cross-item alias sites that
should change on different axes. Item-scoped diff vs
`a17f85ea2f624fe30eb4cf714b0ae75e6cbcc929` is empty for
`django_strawberry_framework/types/__init__.py` (and this pass adds only
`docs/dry/dry-file-types____init__.md`). Plan checkbox left for Worker 2.
Ready for W2.

## Independent verification (Worker 2)

Re-traced present-day `types/__init__.py` end-to-end against package root,
`types/relay.py`, `permissions.py`, `utils/querysets.py`, `utils/__init__.py`,
and `list_field.py`. Confirmed
`git diff a17f85ea2f624fe30eb4cf714b0ae75e6cbcc929 --
django_strawberry_framework/types/__init__.py` is empty. Runtime identity probe
re-run: root / `types` / defining modules / permissions all `is`-equal for the
three curated names; `types.__all__` is exactly those three.

Challenges to Worker 1 rejected candidates (source evidence):

1. **Collapse dual root + `types` exports.** Root binds via
   `from .types import DjangoType, SyncMisuseError, finalize_django_types`
   (`django_strawberry_framework/__init__.py`). Docstring and root `__all__`
   both advertise the dual path. Identity equality means one object, two
   supported import sites — not two implementations. Same packaging idiom as
   `forms/__init__.py`. Rejection stands.

2. **Route facade `SyncMisuseError` from `utils.querysets` instead of
   `.relay`.** `types/relay.py` is the sole types-package alias
   (`from ..utils.querysets import SyncMisuseError as SyncMisuseError`) and
   documents that it exists so both `…types.relay` and this facade stay
   stable. Five test modules still import from `types.relay`. A direct
   `utils` import here would duplicate the alias inside `types/` or orphan
   the relay path. Rejection stands.

3. **Absorb / delete `permissions.py`'s `SyncMisuseError` re-export.**
   Permissions aliases from `utils.querysets` for
   `from django_strawberry_framework.permissions import SyncMisuseError`
   (used by `tests/test_permissions.py`). Different consumer domain from the
   type-system / Relay dotted path; does not feed this `__all__` or the
   root-via-types binding. Ownership stays with permissions. Rejection stands.

Independent consolidation search: only one `class SyncMisuseError` body
(`utils/querysets.py`); `utils/__init__.py` deliberately omits it; no
production site uses `from django_strawberry_framework.types import
DjangoType|SyncMisuseError|finalize_django_types` (root + `list_field`'s
`from .types import DjangoType` are the real consumers of this facade). No
missed shared responsibility this file should own. Zero-edit verified.
