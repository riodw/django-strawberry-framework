# DRY review: `django_strawberry_framework/extensions/__init__.py`

Status: verified

## System trace

The target is the `extensions` subpackage public surface: module docstring, one
eager re-export of `DjangoDebugExtension` from `extensions.debug`, and
`__all__ = ["DjangoDebugExtension"]`. It defines no functions, classes, or
policy helpers.

Owned responsibility:

- advertise the subpackage as the home of specialized, opt-in Strawberry
  `SchemaExtension`s;
- make `from django_strawberry_framework.extensions import DjangoDebugExtension`
  the canonical consumer import;
- keep that symbol off the package root (root TODO + docstring: root surface is
  the always-on schema-building API; the dotted subpackage path is the opt-in
  signal).

Connected behavior examined:

- `extensions/debug.py` — owns capture, payload shape, lifecycle, security
  posture, and the class implementation. Sibling file item still open; traced
  only as the re-export target.
- Package root `__init__.py` — eagerly exports `DjangoOptimizerExtension` (default
  recipe) and deliberately does **not** import or root-export
  `DjangoDebugExtension`. Soft-dep names use PEP 562 `__getattr__` +
  `_DRF_SOFT_EXPORTS`; that machinery is for optional DRF, not for this hard-dep
  extension.
- Sibling hard-dep opt-in markers: `auth/__init__.py` (eager re-export +
  `__all__`, root stays clean), `utils/__init__.py` / `testing/__init__.py`
  (same eager shape). Soft-dep contrast: `middleware/__init__.py` is an
  import-clean empty marker so walkers never pull django-debug-toolbar.
- Consumers: `examples/fakeshop/test_query/test_debug_extension_api.py`,
  `test_multi_db.py`, `tests/extensions/test_debug.py`, and standing docs
  (`docs/README.md`, glossary) all use the subpackage import path. Leaf
  `extensions.debug` imports remain available for internal/test access.
- Baseline `git diff df8a14de6db4ea626843e88584e568019021cc7e -- …/extensions/__init__.py`
  is empty; working tree matches HEAD for this file.

## Verification

Searches:

- `DjangoDebugExtension` / `django_strawberry_framework.extensions` across the
  repo — every production and live-test consumer hits the subpackage re-export;
  no second public factory or alternate export table.
- Package `__init__.py` files for `__getattr__`, eager `__all__`, and
  soft-dependency empty markers — three distinct export postures, each tied to
  a different dependency story (hard eager, soft lazy, soft empty).
- Concept search for parallel “opt-in SchemaExtension package surface” —
  optimizer is root-exported because it is the default N+1 recipe; debug is
  subpackage-only because it is developer-only and off by default. Same
  Strawberry extension base class does not imply the same public placement.

Rejected / deferred candidates (tried to disprove shared ownership):

1. **Unify with `middleware/__init__.py` (empty marker).** Disproved: middleware
   must stay import-clean for an optional django-debug-toolbar dependency;
   `extensions.debug` has no soft dependency and every consumer import is a hard
   dependency. Emptying this `__init__` would break the documented canonical
   import and force every caller onto the leaf path for the wrong reason.
2. **Root-export `DjangoDebugExtension` beside `DjangoOptimizerExtension`.**
   Disproved: different product contracts. Optimizer is always-on schema
   infrastructure; debug is an opt-in development surface whose presence on the
   root would erase the structural opt-in. Root comment already defers any
   root-surface change to a joint version cut — ownership stays at this
   subpackage.
3. **Shared “eager re-export `__init__` helper” across auth/utils/testing/
   extensions.** Disproved: the sites share a packaging idiom, not a mutable
   rule. A helper would add indirection without a single change axis.
4. **Collapse docstring / README / glossary import examples into one site.**
   Disproved for this file: standing docs must document the public import;
   module docstring states the local export contract. Not a production-code
   duplication this owner can consolidate.
5. **Behavior / coordinator / payload logic living in `__init__.py`.** Absent —
   all of that stays in `debug.py`. Folder integration and the `debug.py` file
   pass own any cross-module policy questions.

No scratch experiment required: the file is a pure re-export; import graph and
sibling `__init__` contracts are sufficient.

## Opportunities

None — the target is already the single authoritative public export of
`DjangoDebugExtension` under `django_strawberry_framework.extensions`. It
correctly uses the hard-dep eager re-export shape, correctly refuses root
re-export and soft-dep lazy machinery, and owns no second copy of debug
behavior. Sibling `debug.py` and folder `extensions/` remain the places for
implementation and package-integration DRY work.

## Judgment

Zero-edit. Thin, correctly bounded package marker; no consolidation this file
owns. Ready for Worker 2.

## Implementation (Worker 1)

No tracked source edits. Item-scoped diff vs `ITEM_BASELINE` remains empty for
the target. Artifact only.

## Independent verification (Worker 2)

Scoped diff vs `ITEM_BASELINE`
(`df8a14de6db4ea626843e88584e568019021cc7e`) is empty; working tree matches
baseline byte-for-byte for
`django_strawberry_framework/extensions/__init__.py`.

Re-trace: target owns only the hard-dep eager public surface (docstring +
re-export + `__all__`). Class body, capture, payload, and security policy live
in `extensions/debug.py`. Package root exports `DjangoOptimizerExtension` and
explicitly refuses this symbol (TODO + `tests/base/test_init.py` root-`__all__`
pin). Live and package consumers import
`from django_strawberry_framework.extensions import DjangoDebugExtension`;
leaf `extensions.debug` imports appear only for internal/test module access.
No second factory, alternate export table, or soft-dep lazy path for this
symbol.

Challenged rejected candidates — all hold:

1. **Unify with empty `middleware/__init__.py`.** Still wrong: middleware stays
   import-clean for optional django-debug-toolbar; this package has no soft
   dependency. Emptying it would break the documented canonical import.
2. **Root-export beside optimizer.** Still wrong: optimizer is default recipe;
   debug is structural opt-in. Root placement would erase that signal.
3. **Shared eager-re-export helper across auth/utils/testing/extensions.**
   Still wrong: shared packaging idiom, not a shared mutable rule. Sibling
   `__init__` files already differ in import style and symbol sets; a helper
   adds indirection without a change axis.
4. **Collapse docstring / standing-doc import examples.** Still out of scope
   for this file: docs document the public path; the module docstring states
   the local export contract.
5. **Policy living in `__init__.py`.** Still absent.

Independent search for missed consolidation: dual `__all__` on package vs
leaf is normal Python surface declaration, not duplicated policy; no bypass
import in production consumers; no competing registry or settings key for this
export. Zero-edit judgment stands.

**Disposition:** verified. Plan item checked.
