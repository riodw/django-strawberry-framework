# Alpha review feedback

## 0.0.3 release polish
Purpose: capture the small, low-risk finishing work completed before bundling the current DjangoType + optimizer milestone as `0.0.3`. Larger feature work moves to `0.0.4` instead of expanding this release.
Status: completed for 0.0.3 release prep on 2026-05-05; formatting, lint, tests, and build passed.

## Completed before 0.0.3
### 1. Bump version metadata everywhere
Scope:

- `pyproject.toml`
- `django_strawberry_framework/__init__.py`
- `tests/base/test_init.py`
- `uv.lock`

Starting state:

- Package version was still `0.0.2`.
- The version test still expected `0.0.2`.
- The lockfile still recorded the editable package as `0.0.2`.

Completed state:

- `pyproject.toml` uses `version = "0.0.3"`.
- `django_strawberry_framework/__init__.py` uses `__version__ = "0.0.3"`.
- `tests/base/test_init.py` expects `0.0.3`.
- `uv lock` has been run so `uv.lock` reflects `0.0.3`.
- Version values match exactly.

### 2. Promote changelog entries into a 0.0.3 release section
Scope:

- `CHANGELOG.md`

Starting state:

- `[Unreleased]` included only part of the optimizer work that had landed.
- It mentioned B1, B3, B4, B5, B7, and O5, but did not clearly summarize the full 0.0.3 milestone.

Completed state:

- The optimizer-related `[Unreleased]` material is now a dated `[0.0.3]` section.
- The section summarizes the Layer 2 optimizer milestone accurately.
- `[Unreleased]` remains present and reserved for future changes.
- No Layer 3 features are described as shipped.

Items represented:

- O3 root-gated optimizer hook.
- O4 nested prefetch chains and same-query recursion.
- O5 `only()` projection.
- O6 custom `get_queryset` downgrade to `Prefetch`.
- B1 AST-cached plans.
- B2 FK-id elision.
- B3 N+1 detection strictness.
- B4 `Meta.optimizer_hints`.
- B5 context plan introspection.
- B6 schema-build-time audit.
- B7 precomputed field metadata.
- B8 queryset diffing.
- Fragment-spread directive cache-key fix.
- Multi-operation document cache-key fix.
- `OptimizerHint` top-level export.
- `registry.iter_types()` public iterator.

### 3. Fix stale public-surface spec text
Scope:

- `docs/spec-public_surface.md`

Starting state:

- The spec still said the 0.0.3 decision was to drop `DjangoOptimizerExtension` from top-level exports because the optimizer was not effective end-to-end.
- That was no longer true: the optimizer is shipped, tested, and exported.

Completed state:

- `docs/spec-public_surface.md` no longer contradicts `django_strawberry_framework/__init__.py`.
- `DjangoOptimizerExtension` remains top-level-exported.
- `OptimizerHint` is top-level-exported.
- The optimizer is marked shipped because O1-O6 and B1-B8 are implemented and covered.
- The top-level re-export rule remains intact; only the stale 0.0.3 application of the rule changed.

### 4. Fix stale optimizer status in docs README tree
Scope:

- `docs/README.md`

Starting state:

- The folder-layout tree still described `optimizer/` as `O1–O3/O5–O6 + B1–B7 shipped`.
- Current source/tests supported `O1–O6 + B1–B8 shipped`.

Completed state:

- The optimizer tree comment now says `O1–O6 + B1–B8 shipped`.
- `docs/README.md` status language matches `docs/spec-optimizer.md`, `docs/spec-optimizer_beyond.md`, and source.

### 5. Remove stale O6 skipped placeholder
Scope:

- `tests/types/test_base.py`

Starting state:

- `test_optimizer_downgrades_to_prefetch_when_target_has_custom_get_queryset` was still skipped with the reason `Slice 6: optimizer downgrade-to-Prefetch rule pending`.
- O6 was implemented and covered in `tests/optimizer/test_extension.py`.

Completed state:

- The stale skipped placeholder was deleted.
- The real O6 tests remain in `tests/optimizer/`, the correct package-test location for optimizer behavior.
- No skipped test claims O6 is pending.
- Valid future skips for M2M and definition-order independence remain, with current reasons.

### 6. Keep historical cache-key review notes only if marked implemented
Scope:

- `docs/alpha-review-feedback.md`

Completed state:

- This file is focused on the current 0.0.3 fine-touches checklist.
- It does not imply that fixed cache-key bugs are still open.
- If old cache-key review content is restored as history later, it should include a status note that both issues are implemented and retained only as regression-test rationale.

### 7. Run release validation
Scope:

- local validation commands

Completed commands:

- `uv run ruff format .`
- `uv run ruff check --fix .`
- `uv run pytest`
- `rm -rf dist/`
- `uv build`

Completed state:

- Formatting passes.
- Lint passes.
- Full test suite passes with 100% package coverage.
- Build succeeds and produces fresh 0.0.3 artifacts.

## Defer to 0.0.4
These are real backlog items, but they should not block the 0.0.3 release:

- definition-order independence / `registry.lazy_ref`
- multiple `DjangoType`s per model / `Meta.primary`
- consumer override semantics
- Relay / `Meta.interfaces`
- deferred scalar conversions (`BigIntegerField`, `ArrayField`, `JSONField`, `HStoreField`)
- real M2M fixture/test coverage
- filters
- orders
- aggregates
- `FieldSet`
- `DjangoConnectionField`
- permissions
- fakeshop schema activation

## Release framing
Recommended positioning for `0.0.3`:

- `0.0.3` is the “DjangoType + optimizer foundation is real” release.
- It ships the completed Layer 2 optimizer milestone cleanly.
- It does not absorb new Layer 3 feature work.
- `0.0.4` begins the next product-surface phase after this release is tagged.
