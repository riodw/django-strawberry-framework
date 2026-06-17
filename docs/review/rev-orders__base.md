# Review: `django_strawberry_framework/orders/base.py`

Status: verified

## DRY analysis

- None — `RelatedOrder` is already the maximally-DRY shape: it is a 4-line parameterization (`_target_attr` / `_owner_attr` + thin family-named `bind_orderset` / `.orderset` wrappers) over the shared `RelatedSetTargetMixin` single-sited by the 0.0.9 DRY pass (`sets_mixins.py:142-187`, `docs/feedback.md` Major 3). The filter twin `RelatedFilter` (`filters/base.py:370-470`) is the symmetric consumer of the same mixin. The only cross-file commonality (the two families' wrapper methods) is the deliberate "keep family-named public surface" decision documented in `RelatedSetTargetMixin`'s docstring (`sets_mixins.py:162-165`); folding the wrappers away would erase the public `bind_orderset` / `.orderset` API the consumer surface promises. The filter/order family-wrapper-vs-mixin relationship is a cross-folder observation owned by the project pass (`rev-django_strawberry_framework.md`), not a local defect — note, do not force-merge.

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

- **Single-symbol public surface.** Collapses the cookbook's `BaseRelatedOrder` + `RelatedOrder` pair into one consumer-facing class per spec-028 Decision 2; matches the filter side's spec-027 Decision 2 shape.
- **Neutral-module import discipline.** Imports `RelatedSetTargetMixin` from the package-root `sets_mixins` via sibling import (`orders/base.py:27`), deliberately NOT through `filters.base` (which would load the entire filter subsystem to build orders, and re-couple sibling Layer-3 packages) — rationale documented in the module docstring per spec-028 Revision 4 H1. No ORM markers, no executable code at module level, no reflective access, no import-time side effects.
- **Ergonomic relaxation documented.** `field_name` is optional positional (`orders/base.py:55`) where the cookbook makes it required; the module docstring (`orders/base.py:12-16`) explains this is purely ergonomic since `OrderSet.Meta.fields` always supplies it — honest about the divergence from the source port.
- **Idempotent bind contract.** `bind_orderset` is a no-op on re-bind (via `_bind_owner`'s `hasattr` guard, `sets_mixins.py:171-174`), mirroring the filter twin's documented idempotency contract so `OrderSetMetaclass.__new__` can rebind every related order without clobbering a deliberate override; strict cross-owner mismatch is deferred to finalize per the mixin design.
- **GLOSSARY accurate.** The `RelatedOrder` entry (`docs/GLOSSARY.md:1028-1036`) matches the implementation exactly: three target-acceptance shapes, sibling import from `sets_mixins.LazyRelatedClassMixin`, and the lazy unqualified-name resolution (import_string first, owner-`__module__` fallback, raw `ImportError` propagation with no `ConfigurationError` rewrap at this layer). The `check_*_permission` / six-member `Ordering` enum / NULLS-positioning prose lives under the `OrderSet` and `Ordering` entries (`docs/GLOSSARY.md:944`, `1032-1034`) — correctly scoped to `orders/sets.py` / `orders/inputs.py`, not this file. No drift.

### Summary

`orders/base.py` is a clean, minimal, unchanged-since-baseline file: empty `git log 14910230..HEAD` and empty `git diff HEAD` confirm it was untouched by the spec-035 / commit-79b74b46 bursts (the dirty tree is concurrent maintainer work, out of scope per AGENTS.md #33). The static overview confirms 5 symbols, 0 ORM markers, 0 calls of interest, 0 repeated literals, 0 control-flow hotspots. `RelatedOrder` is a thin parameterization over the canonical `RelatedSetTargetMixin`, the symmetric twin of `RelatedFilter`, with all shared machinery already single-sited in `sets_mixins.py`. The prompt's order-subsystem review-focus items (OrderSet base behavior, `Ordering` enum + NULLS positioning, `check_*_permission` gates) live in `orders/sets.py` / `orders/inputs.py`, not base.py — base.py contains only the `RelatedOrder` traversal primitive. No High / Medium / Low findings; DRY is correctly None at file scope. Qualifies as a no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 270 files left unchanged (only the pre-existing COM812-vs-formatter config warning).
- `uv run ruff check --fix .` — pass; all checks passed.

### Notes for Worker 3
- Shadow used: `docs/shadow/django_strawberry_framework__orders__base.overview.md` (plan-time `--all` sweep; source timestamp not newer, not regenerated). Shadow accurate: 5 symbols, 0 ORM markers, 0 calls of interest, 0 repeated literals.
- No High / no behavior-changing Medium / no Low findings — nothing to reject or carry forward.
- No GLOSSARY-only fix in scope — `RelatedOrder` GLOSSARY entry (`docs/GLOSSARY.md:1028-1036`) verified accurate against implementation, no edit needed.
- Baseline HEAD; orders/base.py has empty `git log 14910230..HEAD` and empty `git diff HEAD`. Concurrent dirty files (management/, optimizer/selections.py, filters review docs, fakeshop examples) are out-of-scope maintainer work per AGENTS.md #33; none touch orders/base.py.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits warranted. The module docstring, class docstring, the four method docstrings, and the `RelatedSetTargetMixin`-parameterization comment block (`orders/base.py:48-51`) are all accurate, non-restating, and correctly cross-reference the filter twin and the governing spec decisions. No TODO anchors present (0 per shadow). No stale spec references.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source edits in this cycle (no-source-edit cycle); AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" and the active plan (`docs/review/review-0_0_10.md`) is silent on changelog edits for review cycles. Nothing to record.

---

## Verification (Worker 3)

### Logic verification outcome

No High / Medium / Low findings to address — terminal-verify of a no-source-edit cycle (shape #5). `RelatedOrder` (`orders/base.py::RelatedOrder`) verified to correctly parameterize the shared `RelatedSetTargetMixin`:

- The two parameterization class attrs (`_target_attr = "_orderset"`, `_owner_attr = "bound_orderset"`, `orders/base.py:52-53`) match the slot names the mixin's `_bind_owner` / `_resolved_target` / `_set_target` read (`sets_mixins.py:171-187`) and the names documented in the mixin docstring (`sets_mixins.py:156-160`).
- All three public methods are thin one-line delegates with no re-implemented machinery: `bind_orderset` → `_bind_owner` (`orders/base.py:70`), `.orderset` getter → `_resolved_target` (`:82`), `.orderset` setter → `_set_target` (`:86`). String/callable resolution is delegated to `LazyRelatedClassMixin.resolve_lazy_class` via `_resolved_target` (`sets_mixins.py:178-182`). No missed logic.
- Twin symmetry confirmed against `RelatedFilter` (`filters/base.py:393-394` uses `("_filterset", "bound_filterset")`; cross-comments at `orders/base.py:50-51` and `filters/base.py:391-392` reference each other correctly). No behavioral divergence that would matter at this layer: the filter side's extra `lookups=` rejection / explicit-queryset tracking and the finalize-time strict cross-owner mismatch are filter-specific (it also subclasses `ModelChoiceFilter`), while the order docstring (`orders/base.py:18-20`) is honest that the order side has no operator-bag / form-cleaning per spec-028 Decision 8. The shared idempotent-bind + lazy-resolve seam is single-sited and identical for both families via the mixin.

### DRY findings disposition

DRY None at file scope is correct. The only cross-file commonality (the two families' family-named wrappers) is the deliberate "keep family-named public surface" decision documented in `RelatedSetTargetMixin`'s docstring (`sets_mixins.py:162-165`); folding it away would erase the public `bind_orderset` / `.orderset` API. Correctly carried forward as a project-pass observation (`rev-django_strawberry_framework.md`), not force-merged.

### Temp test verification

- None used — no behavioral claim required a temp test; the parameterization correctness is provable by reading the mixin's slot-name reads against the subclass's attr values, and the file is unchanged since baseline.
- Disposition: n/a.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `orders/base.py` checklist box.

Shape #5 gate confirmation:
1. `git diff HEAD -- django_strawberry_framework/orders/base.py` empty; `git log 14910230..HEAD -- django_strawberry_framework/orders/base.py` empty — zero this-cycle edits.
2. Both Worker 2 sections (`## Fix report`, `## Comment/docstring pass`, `## Changelog disposition`) carry `Filled by Worker 1 per no-source-edit cycle pattern.`
3. No Lows present — verbatim-trigger / GLOSSARY-only-disqualifier rules vacuously satisfied; no GLOSSARY-only fix in scope.
4. Changelog `Not warranted` cites BOTH AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's (`docs/review/review-0_0_10.md`) silence; `git diff -- CHANGELOG.md` empty. Internal-only framing matches the (empty) diff scope.
5. `uv run ruff format .` / `uv run ruff check --fix .` recorded clean by Worker 2.

Shadow (`docs/shadow/django_strawberry_framework__orders__base.overview.md`) matches source: 5 symbols, 0 ORM markers, 0 calls of interest, 0 TODOs, 0 repeated string literals.

---

## Iteration log

(none)
