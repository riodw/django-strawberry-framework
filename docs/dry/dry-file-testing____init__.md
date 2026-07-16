# DRY review: `django_strawberry_framework/testing/__init__.py`

Status: verified

## System trace

`testing/__init__.py` is the consumer entry point for the testing subpackage.
It owns exactly one responsibility: the curated public re-export surface
(docstring catalog + explicit imports + alphabetical `__all__`). It defines
no functions, classes, settings readers, or lifecycle helpers.

Re-exported symbols (7), 1:1 with `__all__`:

- From `testing/client.py`: `AsyncTestClient`, `GraphQLTestCase`,
  `GraphQLTestMixin`, `GraphQLTransactionTestCase`, `Response`, `TestClient`.
- From `testing/_wrap.py`: `safe_wrap_connection_method`.

Deliberately excluded from this file (docstring + CHANGELOG + glossary +
spec-032 DoD): `global_id_for` / `decode_global_id` live only at
`django_strawberry_framework.testing.relay` so
`import django_strawberry_framework.testing` stays light (no `types`-package
import cost for suites that never mint Relay ids).

Connected behavior examined:

- `testing/client.py` — owns HTTP client / mixin / Response implementation,
  endpoint precedence (`conf.testing_endpoint_setting`), and its own leaf
  `__all__` (the six client names). Sibling file item still open; traced only
  as the re-export target.
- `testing/_wrap.py` — owns wrap-time Trac #37064 cooperative wrap; imports
  `_is_database_failure` from `_django_patches` (predicate already single-
  sited). Sibling file item still open.
- `testing/relay.py` — owns mint/decode helpers; not imported here by design.
  Sibling file item still open.
- Package root `__init__.py` — no `testing` import or root export (pinned by
  `tests/testing/test_client.py::test_export_surface_is_the_testing_root_not_the_package_root`).
- Consumers: live `/graphql/` suites under `examples/fakeshop/test_query/`
  (`TestClient` via package root or `graphql_client.py`), package tests under
  `tests/testing/` (root re-export + leaf `testing.relay` / wrap paths), and
  mutation/form resolver tests importing `testing.relay.global_id_for` only.
- Standing docs (`docs/GLOSSARY.md` testing-symbols block, `docs/TREE.md`
  folder line, `docs/README.md`) document the same root-vs-relay split the
  docstring states.

Baseline `git diff ef12a374e470a4c73a31b77445b1c346ae1b8c7b --
django_strawberry_framework/testing/__init__.py` is empty; working tree
matches the item baseline for this file.

## Verification

Searches and checks:

- Import graph for `django_strawberry_framework.testing` /
  `testing.client` / `testing._wrap` / `testing.relay` — production and live
  consumers hit the subpackage root for the six client names +
  `safe_wrap_connection_method`; Relay helpers always use the submodule path;
  no production bypass of the root for the seven public names.
- AST check: import names ↔ `__all__` are identical sets; `__all__` is
  alphabetical.
- Sibling subpackage `__init__.py` shapes (`auth/`, `extensions/`, `utils/`,
  `filters/`, `orders/`, `mutations/`, `forms/`, `optimizer/`, `types/`) —
  same docstring + explicit re-export + `__all__` idiom; `extensions/__init__.py`
  already names this file as a canonical instance of that shape.
- Absolute vs relative import style (`from django_strawberry_framework.testing…`
  here and in `extensions/`, vs `from .…` in `auth/` / `utils/`) — packaging
  spelling only; no shared mutable rule.
- Dual `__all__` on `client.py` vs this file — leaf lists the six client
  names; this file adds `safe_wrap_connection_method`. Normal Python surface
  declaration, not duplicated policy (same judgment as
  `dry-file-extensions____init__.md`).

Rejected / deferred candidates (tried to disprove shared ownership):

1. **Shared “eager re-export `__init__` helper” across auth/utils/extensions/
   testing.** Disproved: sites share a packaging idiom, not a change axis. A
   helper would add indirection without consolidating a rule (DRY.md warns
   against this). Same rejection already verified for auth/extensions.

2. **Re-export `global_id_for` / `decode_global_id` from this `__init__`.**
   Disproved: intentional non-export for import-cost + DoD submodule path.
   Re-exporting would couple every `testing` importer to `types` and erase
   the documented light-import contract.

3. **Collapse dual `__all__` / move leaf `__all__` ownership solely here.**
   Disproved: `client.py` remains a valid leaf import path for internals and
   white-box access; its `__all__` is the leaf surface. This file’s `__all__`
   is the subpackage public surface (six + wrap). Not one ownership that
   drifted into two.

4. **Collapse docstring catalog with `client.py` / `_wrap.py` / `relay.py` /
   glossary.** Disproved for this file: the module docstring is the local
   export index (what is/isn’t re-exported and why). Leaf modules own full
   contracts; standing docs document the public path. Not production-code
   duplication this owner can consolidate.

5. **Normalize absolute imports to relative (`from ._wrap` / `from .client`).**
   Rejected as cosmetic consistency, not DRY. Behavior and ownership
   unchanged; concurrent style already mixes absolute (`extensions`) and
   relative (`auth`, `utils`) without a package-wide mandated spelling.

6. **Root-export `TestClient` / testing surface from package root.**
   Disproved: spec-043 Decision 4 / test 14 — testing stays off the root so
   the consumer test utilities remain a structural opt-in.

7. **Trac #37064 framing duplicated across `__init__` / `_wrap` /
   `_django_patches`.** Deferred to sibling `_wrap.py` / `_django_patches`
   items (and the testing folder pass): the predicate is already single-
   sited at `_is_database_failure`; this file only indexes the public wrap
   helper and points at the patch module. No wrap/unwrap policy body lives
   here to consolidate.

No scratch experiment required: pure re-export; import graph + export 1:1 +
sibling `__init__` contracts suffice. Permanent export coverage already lives
in `tests/testing/test_client.py` (root `__all__` + no package-root export);
live HTTP usage of `TestClient` is already earned under
`examples/fakeshop/test_query/`.

## Opportunities

None — the file is the single authoritative public export table for the seven
root testing names, correctly excludes Relay helpers, and owns no second copy
of client / wrap / Relay behavior. Sibling `client.py`, `_wrap.py`, `relay.py`,
and folder `testing/` remain the places for implementation and package-
integration DRY work.

## Judgment

Zero-edit review. Thin, correctly bounded package marker; no consolidation
this file owns. Ready for Worker 2.

## Implementation (Worker 1)

No tracked source edits. Item-scoped diff vs `ITEM_BASELINE`
(`ef12a374e470a4c73a31b77445b1c346ae1b8c7b`) remains empty for the target.
Artifact only. No ruff (no code edits). No changelog. Plan checkbox left
unchecked for Worker 2.

## Independent verification (Worker 2)

Re-traced `testing/__init__.py` as the curated subpackage public surface only
(docstring catalog + eager re-exports + alphabetical `__all__`). Confirmed
item-scoped baseline diff is empty; AST import names ≡ `__all__` (7 names);
no local function/class definitions.

Import/consumer graph independently checked:

- Live `/graphql/` and package tests import the six client names +
  `safe_wrap_connection_method` from `django_strawberry_framework.testing`.
- Relay helpers always use `testing.relay` (mutations/forms/rest_framework
  resolvers, `tests/testing/test_relay.py`, live library API).
- No production bypass inventing a second export table; leaf
  `testing.client` remains an internal/white-box path only.
- Package root still omits testing (pinned by
  `tests/testing/test_client.py::test_export_surface_is_the_testing_root_not_the_package_root`).

Disposed rejected / deferred candidates (agreement with Worker 1):

1. Shared eager-re-export `__init__` helper across auth/utils/extensions/
   testing — packaging idiom, not a shared change axis; helper would add
   indirection without owning a rule (`DRY.md`).
2. Re-export `global_id_for` / `decode_global_id` here — intentional
   light-import + DoD submodule path; would pull `types` into every
   `testing` import.
3. Collapse dual `__all__` with `client.py` — leaf surface (six) vs
   subpackage surface (six + wrap); not drifted ownership of one policy.
4. Collapse docstring catalog with leaf modules / glossary — local export
   index vs full contracts / standing docs; not production duplication this
   file owns.
5. Absolute → relative import spelling — cosmetic; package already mixes
   absolute (`extensions`) and relative (`auth` / `utils`).
6. Root-export testing names — blocked by spec-043 Decision 4 / test 14.
7. Trac #37064 framing across `__init__` / `_wrap` / `_django_patches` —
   deferred correctly to sibling `_wrap.py` / `_django_patches` and the
   testing folder pass; this file only indexes the public wrap helper.
   Predicate already single-sited at `_is_database_failure`.

No missed second owner of the seven root names. No consolidation this file
owns. Zero-edit judgment stands.

Concurrent WIP preserved: target source untouched; wide dirty tree outside
this item left alone; no commit; no full pytest.
