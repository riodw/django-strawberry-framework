# DRY review: `django_strawberry_framework/__init__.py`

Status: verified

## System trace

The target is the package facade. It owns four connected contracts: the canonical package logger
created before optimizer imports to avoid the package/subpackage cycle; eager aliases for the
always-available public schema-building surface; the runtime `__version__`; and the
`_DRF_SOFT_EXPORTS`/`__getattr__` boundary that resolves five DRF-backed names without importing DRF
for a normal package or star import.

The trace followed each eager alias to its defining module and subpackage facade, the logger through
`optimizer/__init__.py` and its consumers, the version through `pyproject.toml`,
`tests/base/test_init.py`, `uv.lock`, and standing release documentation, and the lazy names through
`rest_framework/__init__.py`, their source modules, and
`tests/rest_framework/test_soft_dependency.py`. Root imports in examples and standing docs consume
the facade rather than reimplementing its behavior. Opt-in auth, testing, router, and extension
surfaces intentionally remain subpackage-only.

## Verification

- Read the complete target and connected current source/tests/docs; repository searches excluded
  historical specs and review artifacts from evidence.
- `git diff bdf3f44b63ac9144c5b4de109abdb03dc374c0f0` was empty for
  `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `pyproject.toml`, and
  `uv.lock`, and the target has no worktree edit. The new plan and this artifact are excluded from
  that item-scoped comparison.
- An isolated `uv run python` present-path probe proved the runtime and project versions both equal
  `0.0.13`; `__all__` has no duplicates and every name resolves; star import binds exactly
  `__all__`; every lazy DRF name resolves to its source object, remains outside `__all__`, and is
  not memoized in package globals.
- A second isolated probe evicted DRF modules and installed the standard absence sentinel. Every
  lazy DRF name raised the shared install-hint `ImportError`, while package star import still
  succeeded and bound none of those names.
- No pytest suite was run: this is not the final gate, and repository policy reserves pytest for an
  explicit test request.

Strongest rejected candidates:

- The literal `__all__` tuple repeated in `tests/base/test_init.py` is an independent regression
  oracle, not duplicated production ownership. Deriving the expected tuple from the target would
  make the surface-pinning test unable to detect accidental widening or removal.
- The version quintet repeats one release value across packaging metadata, runtime metadata, a test
  oracle, the lockfile, and rendered standing documentation, but those are separate externally
  consumed representations moved atomically by the joint-cut workflow. A runtime helper cannot own
  build metadata or lockfile state, and deriving the test from either side would weaken drift
  detection.
- The root and `routers.py` both use PEP 562, but their contracts intentionally diverge. Root DRF
  names are excluded from star import and never memoized; the router name is included in submodule
  star import and its constructed class is cached. A generic helper would need policy switches for
  the behavior that each owning module currently states directly.
- Eager root aliases repeat names found in subpackage `__all__` declarations but not implementations.
  The package facade and narrower dotted-path facades are distinct supported import paths, and
  identity checks confirm they converge on the defining objects. Moving definitions into the root
  would invert the import graph and increase coupling.

## Opportunities

None — the apparent repetitions are boundary declarations or independent drift detectors, while
the actual implementation responsibilities are already single-sited: logger creation in the root,
DRF import failure policy in `require_drf()`/`require_optional_module()`, lazy dispatch in
`_DRF_SOFT_EXPORTS`, and every exported object's behavior in its defining module.

## Judgment

No tracked consolidation is warranted. The current facade preserves import-cycle ordering,
soft-dependency isolation, supported import identities, and release drift detection without
duplicating behavior. This is a proved zero-edit result; Worker 3 should independently verify it.

## Independent verification (Worker 3)

Verified independently against baseline `bdf3f44b63ac9144c5b4de109abdb03dc374c0f0`.
The item-scoped diff is empty across the complete target and every traced eager definition,
subpackage facade, logger consumer, lazy DRF target, shared optional-import guard, facade test, and
version representation. Current-source AST searches found one implementation for each root symbol,
only the root and `routers.py` as module-level PEP 562 owners, and the exact root `__all__` tuple
only at its production declaration and the independent assertion in `tests/base/test_init.py`.

Fresh present- and absent-DRF interpreter probes passed. All 24 eager aliases resolve by identity
to their imported objects; all five lazy aliases resolve by identity, remain outside `__all__`, and
are not memoized; star import binds exactly the 25 `__all__` names. With DRF absent, every lazy name
raises the shared `djangorestframework>=3.17.0` hint, star import stays successful, and an unrelated
miss remains `AttributeError`. The runtime, project metadata, test oracle, glossary joint-cut rule,
and lockfile all still agree on `0.0.13`.

The rejected candidates remain correctly rejected. The repeated `__all__` tuple and version value
are independent drift detectors or externally consumed release representations, so deriving either
oracle would weaken verification. The two PEP 562 sites do not share a contract: root DRF dispatch
is non-caching and star-excluded, while the router builds and caches a class deliberately included
in submodule star import. Eager root and subpackage names are supported boundary aliases converging
on single definitions, not parallel implementations; moving behavior into the root would invert
ownership. The repeated key/source-attribute spelling inside `_DRF_SOFT_EXPORTS` likewise names two
potentially distinct namespaces in the canonical dispatch table and is not a second behavior owner.

No missed consolidation, stale representation, or bypass was found. No pytest suite was run because
repository policy reserves it for an explicit request; the read-only static and isolated runtime
checks above are sufficient for this zero-edit item.
