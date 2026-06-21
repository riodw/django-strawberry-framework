# Review: `django_strawberry_framework/orders/base.py`

Status: verified

## DRY analysis

- None — `RelatedOrder` is already the maximally-DRY shape: a 4-line parameterization (`_target_attr` / `_owner_attr` + thin family-named `bind_orderset` / `.orderset` wrappers) over the shared `RelatedSetTargetMixin` single-sited by the 0.0.9 DRY pass (`sets_mixins.py:142-187`, `docs/feedback.md` Major 3). The filter twin `RelatedFilter` (`filters/base.py:370-470`) is the symmetric consumer of the same mixin. The only cross-file commonality (the two families' family-named wrapper methods) is the deliberate "keep family-named public surface" decision documented in `RelatedSetTargetMixin`'s docstring (`sets_mixins.py:162-165`); folding the wrappers away would erase the public `bind_orderset` / `.orderset` API the consumer surface promises. The filter/order family-wrapper-vs-mixin relationship is a cross-folder observation owned by the project pass (`rev-django_strawberry_framework.md`), not a local defect — note, do not force-merge.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `RelatedOrder` (`orders/base.py:30-86`) subclasses the shared `RelatedSetTargetMixin` (`sets_mixins.py:142-187`) and exposes only the two parameterization class attrs (`_target_attr = "_orderset"`, `_owner_attr = "bound_orderset"`, `orders/base.py:52-53`) plus three thin wrappers (`bind_orderset` → `_bind_owner`; `.orderset` getter → `_resolved_target`; `.orderset` setter → `_set_target`). String/callable resolution is delegated to `LazyRelatedClassMixin.resolve_lazy_class` via the mixin. No machinery is re-implemented locally.
- **Duplication risk in the current file.** The byte-parallel structure with `RelatedFilter` (`filters/base.py:370-470`) is intentional sibling design, explicitly called out by both files' parameterization comments (`orders/base.py:48-51`, `filters/base.py:389-392`) and by the mixin docstring. The wrappers are the family-named public surface (`bind_orderset` vs `bind_filterset`, `.orderset` vs `.filterset`); they are not duplicated logic — each is a one-line delegate to the shared mixin. Correct to keep.

(The "New helpers considered." bullet is dropped: the file contains no logic to factor — every method is already a one-line delegate to the canonical mixin, so there is no candidate helper to evaluate.)

### Other positives

- **Single-symbol public surface.** Collapses the cookbook's `BaseRelatedOrder` + `RelatedOrder` pair into one consumer-facing class per spec-028 Decision 2; matches the filter side's spec-027 Decision 2 shape. Exported via `orders/__init__.py:91` (`"RelatedOrder"` in `__all__`).
- **Neutral-module import discipline.** Imports `RelatedSetTargetMixin` from the package-root `sets_mixins` via sibling import (`orders/base.py:27`), deliberately NOT through `filters.base` (which would load the entire filter subsystem to build orders, and re-couple sibling Layer-3 packages) — rationale documented in the module docstring per spec-028 Revision 4 H1. No ORM markers, no executable code at module level, no reflective access, no import-time side effects (static overview: 0 ORM markers, 0 calls of interest, 0 control-flow hotspots).
- **Ergonomic relaxation documented.** `field_name` is optional positional (`orders/base.py:55`) where the cookbook makes it required; the module docstring (`orders/base.py:12-16`) explains this is purely ergonomic since `OrderSet.Meta.fields` always supplies it — honest about the divergence from the source port.
- **Idempotent bind contract.** `bind_orderset` is a no-op on re-bind (via `_bind_owner`'s `hasattr` guard, `sets_mixins.py:171-174`), mirroring the filter twin's documented idempotency contract so `OrderSetMetaclass.__new__` can rebind every related order without clobbering a deliberate override; strict cross-owner mismatch is deferred to finalize per the mixin design.
- **GLOSSARY accurate.** The `RelatedOrder` entry (`docs/GLOSSARY.md:1053-1061`) matches the implementation exactly: three target-acceptance shapes (target class, absolute import path, unqualified same-module name), sibling import from `sets_mixins.LazyRelatedClassMixin` ("not `filters.base` as named in earlier revisions"), and the lazy unqualified-name resolution (import_string first, owner-`__module__` fallback, raw `ImportError` propagation with no `ConfigurationError` rewrap at this layer — rewrap happens a layer up at `finalize_django_types()`). The `check_*_permission` / position-side-channel / six-member `Ordering` enum / NULLS-positioning prose lives under the `OrderSet` (`docs/GLOSSARY.md:965-973`) and `Ordering` (`docs/GLOSSARY.md:961-963`) entries — correctly scoped to `orders/sets.py` / `orders/inputs.py`, not this file. No drift.

### Summary

`orders/base.py` is a clean, minimal, unchanged-since-baseline file: empty `git diff 8edb7f75 -- orders/base.py` AND empty `git diff HEAD -- orders/base.py` confirm zero this-cycle edits (last commit touching it is `edab6806`, the 0.0.9-era DRY pass — predates the per-cycle baseline). The static overview confirms 5 symbols, 0 ORM markers, 0 calls of interest, 0 repeated literals, 0 control-flow hotspots, 0 TODOs. `RelatedOrder` is a thin parameterization over the canonical `RelatedSetTargetMixin`, the symmetric twin of `RelatedFilter`, with all shared machinery already single-sited in `sets_mixins.py`. The prompt's order-subsystem review-focus items (OrderSet base behavior, `Ordering` enum + NULLS positioning, `check_*_permission` gates) live in `orders/sets.py` / `orders/inputs.py`, not base.py — base.py contains only the `RelatedOrder` traversal primitive. No High / Medium / Low findings; DRY is correctly None at file scope. Qualifies as a no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; "289 files left unchanged" (only the pre-existing COM812-vs-formatter config warning).
- `uv run ruff check --fix .` — pass; "All checks passed!".

### Notes for Worker 3
- Shadow used: `docs/shadow/django_strawberry_framework__orders__base.overview.md` (plan-time `--all` sweep; source timestamp not newer, not regenerated). Shadow accurate: 5 symbols, 0 ORM markers, 0 calls of interest, 0 repeated literals, 0 control-flow hotspots.
- No High / no behavior-changing Medium / no Low findings — nothing to reject or carry forward.
- No GLOSSARY-only fix in scope — `RelatedOrder` GLOSSARY entry (`docs/GLOSSARY.md:1053-1061`) verified accurate against implementation, no edit needed.
- Baseline `8edb7f75f839deb861ca36c777b4fba3a4a6928b`; `orders/base.py` has empty `git diff <baseline>` AND empty `git diff HEAD`. Any concurrent dirty files are out-of-scope maintainer work per AGENTS.md #34; none touch `orders/base.py`.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits warranted. The module docstring, class docstring, the four method docstrings, and the `RelatedSetTargetMixin`-parameterization comment block (`orders/base.py:48-51`) are all accurate, non-restating, and correctly cross-reference the filter twin and the governing spec decisions. No TODO anchors present (0 per shadow). No stale spec references.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source edits in this cycle (no-source-edit cycle); AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" and the active plan (`docs/review/review-0_0_11.md`) is silent on changelog edits for review cycles. Nothing to record.

---

## Verification (Worker 3)

### Zero-edit proof (shape #5)
- `git diff 8edb7f75 -- orders/base.py` empty AND `git diff HEAD -- orders/base.py` empty. Owned-paths `--stat 8edb7f75 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty — no sibling-cycle attribution needed this cycle. Last commit touching base.py is `edab6806` (0.0.9-era DRY pass), predates baseline. Confirmed.
- Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern." — present on Fix report, Comment/docstring pass, Changelog disposition.

### Logic verification outcome
No High / Medium / Low findings to address — genuine no-source-edit cycle. Independently confirmed the `What looks solid` claims against live source:
- **Three target shapes + raw-ImportError propagation pinned in `tests/orders/test_base.py`.** Class ref → `test_related_order_accepts_class_reference` (`.orderset is AOrder`); absolute import path → `test_related_order_accepts_absolute_import_path_string`; unqualified same-module name → `test_related_order_accepts_unqualified_name_in_same_module` (via `bound_orderset.__module__` fallback); raw `ImportError` propagation → `test_related_order_unresolved_target_raises_importerror_through_lazy_mixin` (`pytest.raises(ImportError)`, docstring confirms finalizer rewraps a layer up — not at this layer); idempotent bind → `test_related_order_bind_orderset_is_idempotent`; setter → `test_related_order_orderset_setter_assigns_underscore_orderset`.
- **Sibling import lineage.** `orders/base.py #"from ..sets_mixins import RelatedSetTargetMixin"` (line 27) — NOT through `filters.base`. `RelatedSetTargetMixin(LazyRelatedClassMixin)` at `sets_mixins.py::RelatedSetTargetMixin`. Pinned by `test_related_order_imports_lazy_mixin_from_sets_mixins_not_filters_base` (asserts `mixin.__module__ == "django_strawberry_framework.sets_mixins"`).
- **Raw ImportError vs finalize-time ConfigurationError rewrap.** `sets_mixins.py::LazyRelatedClassMixin.resolve_lazy_class` tries `import_string` first; on `ImportError` with truthy `bound_class` prefixes `bound_class.__module__` and retries; with falsy `bound_class` re-`raise`s the raw ImportError. No `ConfigurationError` rewrap at this layer — rewrap is a layer up at `finalize_django_types()`, exactly as the GLOSSARY prose and the test docstring state.

### GLOSSARY accuracy (#5 vs missed #4)
`docs/GLOSSARY.md` `## RelatedOrder` entry matches implementation: three acceptance shapes, sibling import from `sets_mixins.LazyRelatedClassMixin` ("not `filters.base` as named in earlier revisions"), import_string-first / module-prefix-fallback / raw-ImportError-propagation-with-no-ConfigurationError-rewrap, finalize-time rewrap a layer up. `git diff 8edb7f75 -- docs/GLOSSARY.md` empty → GLOSSARY untouched this cycle; entry is correct against live source, so genuine #5, not a missed #4 (no GLOSSARY-only fix present, which would be disqualifying). The `check_*_permission` / position-side-channel prose under this entry is OrderSet-apply-pipeline scope, correctly cross-referenced, not a base.py drift.

### DRY findings disposition
DRY-None correct at file scope. `RelatedOrder` is a 4-line parameterization (`_target_attr`/`_owner_attr` + thin `bind_orderset`/`.orderset` wrappers) over the canonical `RelatedSetTargetMixin` single-sited in `sets_mixins.py`. The family-named wrappers are the deliberate public surface (documented in the mixin docstring), not duplicated logic. Cross-folder filter/order family-wrapper symmetry forwarded to the project pass (`rev-django_strawberry_framework.md`) — not a local defect.

### Temp test verification
- None used. The permanent suite (`tests/orders/test_base.py`) already pins every claimed behavior positive and negative.

### Changelog disposition
`git diff -- CHANGELOG.md` empty. "Not warranted" cites BOTH AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND active-plan (`review-0_0_11.md`) silence. Internal-only framing matches actual diff scope (zero source edits). Accepted.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `orders/base.py` checklist box in `docs/review/review-0_0_11.md`.

---

## Iteration log

(none)
