# Review: `django_strawberry_framework/types/relations.py`

Status: verified

## DRY analysis

- Existing patterns reused: `PendingRelation.relation_kind` reuses the shared `RelationKind` alias from `django_strawberry_framework/utils/relations.py:7-12`; records are built by `_record_pending_relation()` in `django_strawberry_framework/types/base.py:651-680`; finalization consumes the record fields in `django_strawberry_framework/types/finalizer.py:61-85`; registry removal consumes the records through `TypeRegistry.discard_pending()` in `django_strawberry_framework/registry.py:185-196`.
- New helpers a fix might justify: none. The only fix-worthy drift is contract cleanup around whether `PendingRelation` itself needs a hashability probe; no new helper would serve more than this dataclass.
- Duplication risk in the current file: `django_strawberry_framework/types/relations.py:16-19` and `django_strawberry_framework/types/relations.py:30-38` duplicate an obsolete `discard_pending()` hashability contract that has drifted from the identity-based implementation in `django_strawberry_framework/registry.py:185-196`.

## High:

None.

## Medium:

None.

## Low:

### Stale hashability contract remains on `PendingRelation`

`PendingRelation` still documents and enforces hashability because `TypeRegistry.discard_pending()` supposedly builds `set(resolved)`, but the registry now removes pending records by `id()` and explicitly avoids coupling to `PendingRelation` equality or hash semantics. That leaves a dead defensive check in the dataclass and stale comments/docstrings that point future maintainers at the wrong lifecycle contract. Remove the `__post_init__` hash probe and update the dataclass documentation, or otherwise re-align this file with the current identity-based registry contract.

```django_strawberry_framework/types/relations.py:16:38
    Fields must remain hashable because ``TypeRegistry.discard_pending()`` builds
    ``set(resolved)`` when removing records after successful finalization. The
    ``__post_init__`` hash probe surfaces a non-hashable ``django_field`` at the
    registration call site rather than deep inside finalization.
...
    def __post_init__(self) -> None:
        """Probe ``django_field`` hashability so non-hashable surrogates fail here.
...
        hash(self.django_field)
```

## What looks solid

- The mandatory static helper was run for this types file: `python scripts/review_inspect.py django_strawberry_framework/types/relations.py --output-dir docs/review/shadow --stdout`.
- The pending relation record is a narrow frozen dataclass, and all production fields are populated by a single builder in `types/base.py`.
- `PendingRelationAnnotation` has one clear job: fail with a useful `repr()` if finalization is skipped before Strawberry schema construction.
- The helper overview reported no control-flow hotspots, calls of interest, TODOs, or repeated string literals in this file.

### Summary

This file is structurally small and mostly sound. The only confirmed issue is contract drift: `PendingRelation` still carries a hashability requirement from an older registry removal strategy, while the current registry uses identity-based pending removal.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/types/relations.py` — removed the obsolete `PendingRelation.__post_init__`
  hashability probe and rewrote the dataclass docstring to describe identity-based pending-record removal.
- `docs/review/rev-types__relations.md` — recorded Worker 2 fix status and validation results.
- `docs/review/worker-memory/worker-2.md` — appended the Worker 2 cycle note.

### Tests added or updated

- None. This Low finding removes stale internal enforcement and documentation for a registry contract that no
  production call path still uses; no user-facing behavior or edge-case branch needed a new test.

### Validation run

- `uv run ruff format .` — pass; latest run reported `2 files reformatted, 94 files left unchanged`.
- `uv run ruff check --fix .` — fail on pre-existing/out-of-scope lint in
  `django_strawberry_framework/optimizer/_context.py` (`N806`) and untracked `scratch_context.py` (`D100`,
  `D101`, `ANN204`, `D105`, `ANN001`). No in-scope `types/relations.py` issue was reported.
- `uv run ruff check django_strawberry_framework/types/relations.py` — pass.
- `uv run ruff format --check django_strawberry_framework/types/relations.py` — pass.
- Focused tests were not run; this was a stale internal guard/docstring cleanup with no remaining behavior
  change to pin.

### Notes for Worker 3

- The dataclass remains frozen because pending relation records are still immutable lifecycle records; the fix only
  removes the obsolete coupling to dataclass hash semantics.
- Comment/docstring disposition: completed in the source change. The stale hashability comments were removed and
  the dataclass docstring now matches `TypeRegistry.discard_pending()` identity-based removal.
- Changelog disposition: not warranted. This is internal contract cleanup for a Low maintainability finding, not a
  consumer-visible behavior change. `CHANGELOG.md` was not edited and was not authorized for this pass.
- Repo-wide Ruff check is currently blocked by out-of-scope dirty/untracked files (`optimizer/_context.py` and
  `scratch_context.py`). Additional out-of-scope optimizer test changes appeared in the shared workspace during
  this pass; I left them untouched.

---

## Verification (Worker 3)

### Logic verification outcome

Revision needed. The source change correctly removes the stale `PendingRelation.__post_init__` hashability
probe and the source docstring now matches `TypeRegistry.discard_pending()`'s identity-based removal contract.
However, the permanent test suite still contains `tests/test_registry.py::test_pending_relation_rejects_non_hashable_django_field`,
whose docstring and assertion require the obsolete `__post_init__` / `set(resolved)` behavior. The focused test
now fails because `PendingRelation(...)` no longer raises for a non-hashable `django_field`.

Worker 2 should update or remove that stale test in the permanent suite. Prefer pinning the current contract:
`discard_pending()` should be able to remove the exact `PendingRelation` instance even when `django_field` is
non-hashable, because removal is by `id()` and should not hash the record. No source rework is needed unless
Worker 2 decides the old hashability contract was actually intended to remain.

### DRY findings disposition

No new DRY issue found in `django_strawberry_framework/types/relations.py`. The required source-side cleanup
stays localized to the dataclass contract. The outstanding issue is stale permanent test coverage, not duplicated
source logic.

### Temp test verification

- No temp test file created.

### Verification outcome

- `uv run ruff check django_strawberry_framework/types/relations.py` — pass.
- `uv run ruff format --check django_strawberry_framework/types/relations.py` — pass.
- `uv run pytest tests/test_registry.py::test_pending_relation_rejects_non_hashable_django_field -q` — fail as
  expected for this revision request; the test still expects `TypeError` from the removed `__post_init__` probe.
- Repo-wide Ruff was not rerun because Worker 2 documented unrelated lint blockers in
  `django_strawberry_framework/optimizer/_context.py` and untracked `scratch_context.py`; current `git status`
  still shows out-of-scope dirty/untracked files.

---

## Revision fix report (Worker 2)

### Files touched

- `tests/test_registry.py` — replaced the stale hashability-rejection test with
  `test_discard_pending_tolerates_non_hashable_django_field`, which constructs a `PendingRelation` carrying a
  non-hashable `django_field`, registers it, and proves `TypeRegistry.discard_pending()` removes it by identity.
- `docs/review/rev-types__relations.md` — set status back to `fix-implemented` and recorded this revision follow-up.
- `docs/review/worker-memory/worker-2.md` — appended the Worker 2 revision note.

### Tests added or updated

- `tests/test_registry.py::test_discard_pending_tolerates_non_hashable_django_field` — pins the current contract
  that `PendingRelation` construction and pending removal tolerate non-hashable `django_field` values because
  removal uses `id()` rather than record hash/equality.

### Validation run

- `uv run pytest tests/test_registry.py::test_discard_pending_uses_identity_match_with_real_pending_relation tests/test_registry.py::test_discard_pending_tolerates_non_hashable_django_field --no-cov` — pass, 2 passed.
- `uv run ruff check --fix tests/test_registry.py django_strawberry_framework/types/relations.py` — pass.
- `uv run ruff format tests/test_registry.py django_strawberry_framework/types/relations.py` — pass, 2 files left unchanged.
- `uv run ruff format --check tests/test_registry.py django_strawberry_framework/types/relations.py docs/review/rev-types__relations.md docs/review/worker-memory/worker-2.md` — failed because Ruff Markdown formatting is experimental and requires preview mode; the two Python files were already formatted. Scoped Python format was rerun successfully afterward.
- Repo-wide `uv run ruff check --fix .` and `uv run ruff format .` were not rerun in this revision pass because the shared workspace still contains unrelated dirty/untracked files outside Worker 2's ownership. Scoped commands were used for the touched Python files.

### Notes for Worker 3

- Source fix was not rolled back. `PendingRelation` remains aligned with identity-based `discard_pending()`.
- Comment/docstring disposition: no additional source comments or docstrings changed in this revision. The previous source docstring already describes identity-based removal, and the stale permanent test docstring was replaced.
- Changelog disposition: not warranted and not authorized for this revision. The change pins an internal registry contract in tests; `CHANGELOG.md` was not edited.

---

## Re-verification (Worker 3)

### Logic verification outcome

Accepted. The Low finding is fixed: `PendingRelation` no longer carries the obsolete `__post_init__`
hashability probe, and its docstring now matches `TypeRegistry.discard_pending()` identity-based removal.
`discard_pending()` builds an `id()` set from resolved records, so the source and docs now agree on identity
rather than equality/hash semantics.

The permanent stale test was replaced with
`tests/test_registry.py::test_discard_pending_tolerates_non_hashable_django_field`, which constructs a
non-hashable `django_field`, registers the exact pending record, and proves `discard_pending()` removes it
without hashing the record. The existing identity test still pins that equal-by-value records are not both
discarded.

### DRY findings disposition

No additional DRY issue found. The cleanup stays localized to the pending relation record contract and reuses
the existing registry removal path rather than introducing parallel pending-record handling.

### Comment/docstring and changelog disposition

Accepted. The stale hashability source docstring and stale test docstring were replaced with current-contract
language. Worker 2's changelog disposition is complete: this is internal contract cleanup and test coverage,
so `CHANGELOG.md` was intentionally left unchanged.

### Temp test verification

- No temp test file created.

### Verification outcome

- `uv run pytest tests/test_registry.py::test_discard_pending_uses_identity_match_with_real_pending_relation tests/test_registry.py::test_discard_pending_tolerates_non_hashable_django_field --no-cov` — pass, 2 passed.
- `uv run ruff check --fix django_strawberry_framework/types/relations.py tests/test_registry.py` — pass.
- `uv run ruff format --check django_strawberry_framework/types/relations.py tests/test_registry.py` — pass, 2 files already formatted.
