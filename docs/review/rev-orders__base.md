# Review: `django_strawberry_framework/orders/base.py`

Status: verified

## DRY analysis

- Defer until an `AggregateSet` `RelatedAggregate` (the third member of the related-set family) lands; `RelatedOrder` (`orders/base.py:30-86`) and `RelatedFilter` (`filters/base.py:370-470`) are already collapsed onto the shared `RelatedSetTargetMixin` (`sets_mixins.py:142-187`) — both contribute only the two parameterization slots (`_target_attr`/`_owner_attr`) plus three family-named thin wrappers (`bind_<x>` → `_bind_owner`, `.<x>` getter → `_resolved_target`, `.<x>` setter → `_set_target`). The wrappers are NOT extractable today: the family-named public surface (`bind_orderset`/`bind_filterset`, `.orderset`/`.filterset`) is the addressable contract consumers and the metaclasses use, and a generic `bind_target`/`.target` would hide it. The 0.0.9 DRY pass (docs/feedback.md Major 3) already pulled the shared machinery into the mixin; the only remaining family-named-wrapper near-copy is intentional addressability, not duplication. Re-triage if a third family member arrives with the identical wrapper trio — at that point a class-decorator or `__init_subclass__` that synthesizes the three family-named wrappers from `_target_attr`/`_owner_attr` becomes net-positive.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** Lazy target resolution (class passthrough / absolute import path / unqualified-name module fallback) is wholly delegated to `RelatedSetTargetMixin._resolved_target` → `LazyRelatedClassMixin.resolve_lazy_class` (`sets_mixins.py:113-138, 176-183`); `bind_orderset` delegates to `_bind_owner` (`sets_mixins.py:171-174`); the `orderset` setter delegates to `_set_target` (`sets_mixins.py:185-187`). The file declares no resolution logic of its own — it is pure parameterization (`_target_attr = "_orderset"`, `_owner_attr = "bound_orderset"`) plus three thin wrappers. This is the post-0.0.9-DRY-pass shape and matches the filter twin `RelatedFilter` byte-for-byte in structure.
- **New helpers considered.** A generic family-wrapper synthesizer was evaluated and deferred (see `## DRY analysis`) — net-negative at two members because it would erase the family-named public surface that is the consumer/metaclass contract.
- **Duplication risk in the current file.** The `orderset`/`filterset` wrapper trio mirrored against `filters/base.py` is intentional sibling design: family-named addressability over shared machinery, the same calibration carried for the order/filter twins across this package. No repeated string-keyed dispatch or literals (shadow overview: 0 repeated literals, 0 ORM markers, 0 calls of interest).

### Other positives

- **Lazy resolution correctness.** The three documented acceptance shapes (class, absolute import path, unqualified-name-against-owner-module) map exactly onto `resolve_lazy_class` (`sets_mixins.py:129-139`): `isinstance(class_ref, str)` → `import_string`, fallback prefixes `bound_class.__module__` only when `bound_class` is truthy else re-raises the raw `ImportError`; the `callable and not isinstance(..., type)` branch handles zero-arg factories; bare class falls through unchanged. All four paths are pinned by `tests/orders/test_base.py` — class ref (`:32-35`), absolute path (`:38-49`), unqualified fallback (`:52-63`), and the unresolvable-string raw-`ImportError` propagation that the finalizer rewrap depends on (`:66-79`).
- **Idempotent bind.** `bind_orderset` → `_bind_owner` uses a `hasattr(self, self._owner_attr)` guard (`sets_mixins.py:173`) so a second (possibly divergent) bind is a no-op; the `OrderSetMetaclass` can rebind on every subclass creation without clobbering a deliberate override. Pinned by `test_related_order_bind_orderset_is_idempotent` (`tests/orders/test_base.py:82-87`), which asserts the first binding survives a second call with a different class.
- **Resolve-once re-store.** The `orderset` property re-stores the resolved class through `_set_target` (`sets_mixins.py:182`) so subsequent access is a plain attribute read; the setter seam is pinned independently by `test_related_order_orderset_setter_assigns_underscore_orderset` (`tests/orders/test_base.py:185-196`).
- **Import discipline.** Single first-party import is the sibling `from ..sets_mixins import RelatedSetTargetMixin` (`base.py:27`) — the neutral shared module per spec-028 Revision 4 H1, deliberately NOT through `filters.base` (which would drag the entire filter subsystem into the order import graph and re-couple the Layer-3 packages). Pinned by `test_related_order_imports_lazy_mixin_from_sets_mixins_not_filters_base` (`tests/orders/test_base.py:90-100`). No Django/ORM import, no import-time side effect, no circular-import risk.
- **Optional `field_name` documented.** The module docstring (`base.py:12-16`) explicitly records the deliberate divergence from the cookbook's required-positional `field_name` — relaxed to optional so the metaclass collection step can mutate it, ergonomic-only because the `OrderSet.Meta.fields` surface always supplies one explicitly.

### Summary

`RelatedOrder` is a clean, minimal parameterization of the shared `RelatedSetTargetMixin`: two slot names plus three family-named thin wrappers, with all lazy-resolution, bind-idempotency, and re-store logic living in `sets_mixins.py`. No High, no Medium, no Low. Logic verified at source against the shared mixin and confirmed exhaustively test-pinned (`tests/orders/test_base.py`). The `RelatedOrder` GLOSSARY entry (`docs/GLOSSARY.md:1000-1008`) was corrected in a prior cycle and is now accurate — it states the raw `ImportError` propagates (the resolver does not rewrap, and names only the single attempted path) with the `ConfigurationError` rewrap happening a layer up at finalize time; the parallel `RelatedFilter` entry (`:990-998`) matches. No GLOSSARY drift to fix. No source, test, or GLOSSARY edit warranted — this qualifies as a shape #5 no-source-edit cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format django_strawberry_framework/orders/base.py` — 1 file left unchanged.
- `uv run ruff check django_strawberry_framework/orders/base.py` — All checks passed.

### Notes for Worker 3
- No High / Medium / Low findings; the single DRY analysis bullet is defer-with-trigger (third related-set family member with the identical wrapper trio), no action this cycle.
- No GLOSSARY-only fix in scope. The `RelatedOrder` GLOSSARY entry (`docs/GLOSSARY.md:1000-1008`) and the parallel `RelatedFilter` entry (`:990-998`) were verified accurate against live source (`sets_mixins.py::LazyRelatedClassMixin.resolve_lazy_class`); the "naming both attempts" over-claim was fixed in a prior cycle and was NOT re-flagged.
- Logic verified at source against the shared `RelatedSetTargetMixin` (`sets_mixins.py:142-187`); all four lazy-resolution shapes plus bind-idempotency and the setter seam are test-pinned in `tests/orders/test_base.py`.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits warranted: the module and method docstrings accurately describe the delegation to the shared mixin, the three target-acceptance shapes, the bind idempotency contract, and the deliberate optional-`field_name` divergence; the parameterization comment (`base.py:48-51`) correctly names the filter twin's slots. No version-pinned label rot (spec-028 references are stable design-doc anchors, not release-version pins).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this cycle (review-only), and per AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"; the active plan (`docs/review/review-0_0_9.md`) is silent on any changelog entry for this item.

---

## Verification (Worker 3)

### Logic verification outcome
No High / Medium / Low findings to verify. Independently confirmed `RelatedOrder` is pure parameterization of the shared `RelatedSetTargetMixin` (no orders-local logic defect): source read shows only `_target_attr = "_orderset"` / `_owner_attr = "bound_orderset"` plus three family-named thin wrappers (`bind_orderset` → `_bind_owner`, `.orderset` getter → `_resolved_target`, `.orderset` setter → `_set_target`), with zero resolution/bind logic of its own. All lazy-resolution + bind-idempotency + re-store logic lives in `sets_mixins.py` (`RelatedSetTargetMixin._bind_owner`/`_resolved_target`/`_set_target` → `LazyRelatedClassMixin.resolve_lazy_class`). Drove all four target-acceptance shapes LIVE under `config.settings` (one probe): class-ref passthrough, absolute import path, unqualified-name fallback against owner module, and the unresolvable-string raw-`ImportError` propagation (confirmed NO `ConfigurationError` rewrap at this layer); plus bind idempotency (first divergent bind survives), resolve-once re-store (`_orderset` re-stored after first access), and the setter seam. All cited pins grep-match `tests/orders/test_base.py` (`:32/:38/:52/:66/:82/:90/:185`).

### DRY findings disposition
Single DRY bullet is defer-with-trigger (third related-set family member arriving with the identical wrapper trio → synthesize via class-decorator/`__init_subclass__`). Correctly not actioned: the family-named public surface (`bind_orderset`/`.orderset`) is the addressable consumer/metaclass contract, and a generic `bind_target`/`.target` would hide it; net-negative at two members. Carried forward.

### Temp test verification
None used. Live verification done via an ephemeral `uv run python` probe (not written to disk).

### GLOSSARY
Per dispatch: confirmed the `RelatedOrder` GLOSSARY entry (`docs/GLOSSARY.md` `## RelatedOrder`) was already corrected in a prior cycle — it states the raw `ImportError` propagates unchanged (resolver does not rewrap, names only the single attempted path), the finalize-time `ConfigurationError` rewrap is a layer up, and the sibling import is from `sets_mixins` not `filters.base`. The "naming both attempts" over-claim is gone. Parallel `RelatedFilter` entry matches. Not re-flagged.

### Shape #5 (no-source-edit) checks
1. `git diff --stat 0872a20 -- django_strawberry_framework/orders/base.py` empty (orders/base.py byte-unchanged from baseline; not present in `git status`). `sets_mixins.py` (the shared mixin this cycle parameterizes, read-only) also byte-clean — its plan box is `[x]` at review-0_0_9.md:77.
2. All three Worker 2 sections start with `Filled by Worker 1 per no-source-edit cycle pattern.`
3. No Low findings; the lone DRY bullet carries verbatim defer-with-trigger phrasing. No GLOSSARY-only fix in scope.
4. Changelog `Not warranted` with both citations (AGENTS.md + active-plan silence); `git diff -- CHANGELOG.md` empty.
5. `uv run ruff format --check` + `uv run ruff check` on orders/base.py both clean (COM812 conflict warning is the standing notice).

Sibling attribution: the wider dirty paths (conf/connection/exceptions/filters.factories/filters.sets/list_field/inspect_django_type/optimizer.extension/optimizer.selections/optimizer.walker + GLOSSARY + the test files) all attribute to CLOSED sibling cycles (verified, `[x]`); `feedback2.md`/`feedback3.md` deletes are AGENTS.md #33 concurrent-maintainer work; `examples/fakeshop/db.sqlite3` is a generated test artifact. None touch `orders/base.py` or `sets_mixins.py` → the cycle's "Files touched: None" holds.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.

---

## Iteration log

(none)
