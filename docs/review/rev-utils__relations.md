# Review: `django_strawberry_framework/utils/relations.py`

Status: verified

## DRY analysis

- None — this module IS the single-source-of-truth for relation-shape classification, and the maintainer's DRY cycle landed the consolidation. `relation_kind`, `is_many_side_relation_kind`, `is_forward_many_to_many`, `instance_accessor`, `has_composite_pk`, the `RelationKind` `TypeAlias`, and the `MANY_SIDE_RELATION_KINDS` frozenset are each declared exactly once here and imported (never re-spelled) by every consumer: optimizer (`walker.py:22`, `field_meta.py:27-30`, `plans.py:45`), types (`finalizer.py:65`, `relations.py:24`, `resolvers.py:50`, `base.py:1606`), filters (`sets.py:60`), orders (`sets.py:49`), mutations (`inputs.py:56`, `resolvers.py:95`), the management command (`inspect_django_type.py`), and the `utils/__init__.py:29` re-export. Re-consolidating a consolidation point is net-negative.

## High:

None.

## Medium:

None.

## Low:

### `instance_accessor` is consumed across folders but is not in `utils/__init__.py.__all__`

`instance_accessor` is a public-shaped helper imported by three subsystems
(`types/finalizer.py:490`, `types/resolvers.py:328`, `optimizer/walker.py:566,713,1448`,
and `optimizer/field_meta.py:228`), yet `utils/__init__.py.__all__` re-exports only
`RelationKind` / `is_many_side_relation_kind` / `relation_kind` and omits it. This is a
deliberate, internally-consistent choice — every consumer imports `instance_accessor`
directly from `..utils.relations`, and the `utils` package docstring's `relations` bullet
(`utils/__init__.py:7-8`) also lists only the three re-exported symbols, so there is no
drift between the `__all__`, the docstring, and the call sites. The asymmetry is harmless
today.

Forward-looking, deferred: if a future cross-folder consumer starts importing
`instance_accessor` via the `utils` package root (rather than the `.relations`
submodule) — the way the other three relation symbols are imported — promote
`instance_accessor` into `utils/__init__.py.__all__` and the package docstring's
`relations` bullet in the same change so the public surface stays coherent. No action
now: the current "submodule-direct for `instance_accessor`, package-root for the other
three" split is consistent across all call sites and both doc surfaces.

### Final `return field.name` is the only undefaulted reflective read

`instance_accessor`'s first two tiers use `getattr(field, ..., None)` and gate on
`is not None`; the third tier is a bare `field.name` with a `# type: ignore[attr-defined]`
(`relations.py:143`). For the documented inputs (FieldMeta with `accessor_name`, raw
reverse descriptor with `get_accessor_name`, forward field / test double with `name`)
this is correct and fails loudly — a shape lacking all three attributes raises
`AttributeError` at the call site rather than returning a wrong accessor silently. That
loud-failure-at-call-site is the right contract for an internal helper whose every caller
hands in a real Django field or `FieldMeta`; do not soften it to a defaulted `getattr`.
No action; recorded for completeness.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is the canonical owner; it reuses nothing because everyone reuses it. `is_many_side_relation_kind` (`relations.py:83-85`) wraps the single `MANY_SIDE_RELATION_KINDS` frozenset (`relations.py:17-19`) so the `{"many", "reverse_many_to_one"}` set is spelled exactly once and the membership call sites (`field_meta.py:141`, `walker.py:143,733`, `filters/sets.py:621`, `orders/sets.py:83`, `types/resolvers.py:242`) stay literal-free. The DRY cycle's two added predicates confirm the single-source pattern at source: `is_forward_many_to_many` (`:88`) is imported only by the two mutation surfaces its docstring names — `mutations/inputs.py:189` (`_select_editable_fields`) and `mutations/resolvers.py:301` (`_index_relation_fields`); `has_composite_pk` (`:146`) is imported only by `field_meta.py:224` (the `fk_id_elision_eligible` conjunct), and the walker's raw-field elision fallback (`optimizer/walker.py::_can_elide_fk_id`, `:870`) now routes through `FieldMeta._from_field_shape` rather than re-spelling the predicate, so both elision deciders converge on this one composite-PK guard and cannot disagree.
- **New helpers considered.** None warranted. The `_RelationFieldLike` Protocol (`relations.py:22-35`) already factors the four-flag read contract into one documented shape; the `getattr(..., False)` defenses in `relation_kind` are intentionally retained alongside the narrower annotation (the docstring states this explicitly). Splitting `relation_kind` into per-shape predicates would invert single-dispatch into more surface.
- **Duplication risk in the current file.** The repeated kind literals flagged by the static helper (`reverse_many_to_one` ×3, `auto_created` ×3, `reverse_one_to_one` ×2, `forward_single` ×2, `many_to_many` ×2) are `RelationKind` `Literal` members and Django flag names appearing in the alias declaration (`:10-15`), the classifier branches (`:72-80`), and the `MANY_SIDE_RELATION_KINDS` membership set (`:17-19`) — they are the enumerated vocabulary itself, not dispatch keys that could be hoisted. Hoisting Django's own attribute name `auto_created` into a constant would obscure, not clarify; the token strings are deliberately spelled in all three spots so the `Literal` ↔ branch ↔ frozenset correspondence stays auditable.

### Other positives

- **Classification correctness verified branch-by-branch against Django descriptor flags.** Forward `ManyToManyField` (`many_to_many=True`) → `"many"` (`:72-73`). Reverse FK `ManyToOneRel` (`one_to_many=True` + `auto_created=True`) → `"reverse_many_to_one"` (`:74-76`). Reverse `OneToOneRel` (`one_to_one=True` + `auto_created=True`) → `"reverse_one_to_one"` (`:78-79`). Forward `ForeignKey` and forward `OneToOneField` (`auto_created=False`) both fall through to `"forward_single"` (`:80`). Reverse M2M `ManyToManyRel` (`many_to_many=True` + `auto_created=True`) short-circuits on the first branch → `"many"` (cardinality-correct). The defensive `one_to_many=True` + no `auto_created` → `"many"` mapping (`:77`) is unreachable from stock Django but explicitly test-pinned.
- **`is_forward_many_to_many` predicate is sound.** `many_to_many=True AND (concrete=True OR NOT auto_created)` admits a forward `ManyToManyField` (concrete / not auto-created) and excludes the reverse `ManyToManyRel` accessor (auto-created, not concrete) — the distinction `relation_kind` cannot make since both map to `"many"`. The `getattr(..., False)` defaults match `relation_kind`'s read contract.
- **TYPE_CHECKING pragma is legitimate, not a coverage dodge.** `if TYPE_CHECKING:` (`:7`) is `False` under the test runner, so `from django.db import models` (`:8`) is genuinely unreachable at runtime; `# pragma: no cover` is correct per AGENTS.md #12. The sole runtime reference to `models` is the `type[models.Model]` annotation in `has_composite_pk` (`:146`), which `from __future__ import annotations` (`:3`) keeps as an unevaluated string — so the deferred import is never needed at runtime and the pragma covers no live executable code.
- **`has_composite_pk` fails closed for FK-id elision.** Reads `_meta.pk_fields` defensively (`getattr(..., None)`, `:159`); returns `True` only for a multi-field pk tuple (`len(...) > 1`, `:160`) — exactly the shape that would make single-column FK-id elision compare mismatched shapes and surface wrong data.
- **Every branch has a dedicated unit test.** `tests/utils/test_relations.py` pins all five `relation_kind` outcomes (incl. the defensive `one_to_many`-without-`auto_created` fallback at `:35` and the forward-O2O-vs-reverse-O2O split), the `RelationKind` `Literal` membership, the `utils.__init__` re-export identity, the `is_many_side_relation_kind` truth table incl. `None` (`:77`), and all three `instance_accessor` tiers (precomputed slot wins `:124`, reverse `get_accessor_name` `:107`, forward `name` fallback `:118`).
- **`instance_accessor` docstring is exceptionally precise** about the Round-4 S3 reverse-relation `name` vs `get_accessor_name()` split (query name `"book"` vs instance attr `"book_set"`), why fakeshop fixtures masked it, and the three-tier read order matching the two field shapes the package passes around. The optimizer (`walker.py:545`) and `field_meta.py:108` cross-reference this helper as the authority for the instance-vs-key vocabulary distinction.
- **Pure-stdlib runtime imports** (`typing` only at module scope; Django deferred under TYPE_CHECKING). Zero import-time side effects, no circular-import risk. The Protocol is structural so the module never imports Django's `ForeignObjectRel` / `ManyToOneRel` concrete types.
- **No GLOSSARY drift.** `docs/GLOSSARY.md` carries no entries for any of this module's symbols (`relation_kind` / `RelationKind` / `is_many_side_relation_kind` / `is_forward_many_to_many` / `instance_accessor` / `has_composite_pk` / `MANY_SIDE_RELATION_KINDS`); they are internal helpers (the three `utils/__init__.py` re-exports carry no symbol-level GLOSSARY entry), so absence is correct and there is nothing to keep in sync.

### Summary

`utils/relations.py` is in clean shape and is the single-home relation-shape classifier consumed by the optimizer, types, filters, orders, and mutations subsystems. The maintainer's DRY-cycle additions — `has_composite_pk`, the forward-M2M predicate `is_forward_many_to_many`, and `RelationKind`/`relation_kind` — are each defined once and confirmed at source to be consumed by exactly the named call sites with no re-spelling: both FK-id-elision deciders (`field_meta.py:224` directly, `walker.py:870` via `FieldMeta._from_field_shape`) converge on the single `has_composite_pk` guard, and both editable-M2M mutation surfaces (`inputs.py:189`, `resolvers.py:301`) converge on `is_forward_many_to_many`, so neither can drift. The `relation_kind` four-shape dispatch is order-correct and exhaustively branch-pinned by `tests/utils/test_relations.py`. The `# pragma: no cover` on the TYPE_CHECKING import is a genuinely unreachable line (runtime-false guard, deferred annotation under `from __future__ import annotations`), not a coverage workaround. No High or Medium findings; two forward-looking Lows recorded with explicit triggers, neither actionable now. The per-cycle (`a48c9104`) and HEAD diffs are both empty — the DRY work is cumulative in HEAD — so this is a no-source-edit cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — `289 files left unchanged` (no changes).
- `uv run ruff check --fix .` — `All checks passed!` (no changes).

### Notes for Worker 3
- No-source-edit cycle (shape #5): `git diff a48c9104887438ca73a15c86d693b872112ee795 -- django_strawberry_framework/utils/relations.py` and `git diff HEAD -- django_strawberry_framework/utils/relations.py` are both empty; the DRY-cycle predicates (`has_composite_pk`, `is_forward_many_to_many`, `RelationKind`/`relation_kind` single-siting) are cumulative in HEAD.
- Both Lows are forward-looking with explicit triggers and require no action this cycle:
  - **`instance_accessor` not in `__all__`** — deferred; trigger = a cross-folder consumer imports it via the `utils` package root instead of the `.relations` submodule. Current submodule-direct import is consistent across all consumers and both doc surfaces.
  - **Bare `return field.name` final tier** — no action; the loud `AttributeError`-at-call-site is the correct contract for this internal helper.
- No GLOSSARY-only fix in scope: `docs/GLOSSARY.md` carries zero entries for any of this module's symbols (all internal; the three `utils/__init__.py` re-exports carry no symbol-level GLOSSARY entry — absence is correct).
- Pragma confirmed legitimate (TYPE_CHECKING-only import, runtime-false, deferred annotation); DRY predicates confirmed single-sourced and correct at every cited call site.
- Dirty files at review time (`docs/feedback2.md`, `docs/review/rev-utils__permissions.md`, `docs/review/rev-utils__querysets.md`, `docs/review/review-0_0_11.md`) are out-of-scope per AGENTS.md #34; source/tests untouched.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits. The module docstring, the `_RelationFieldLike` contract docstring, the `relation_kind` branch-by-branch docstring (incl. the defensive-fallback test-pin reference), the `is_forward_many_to_many` docstring (the two named mutation surfaces verified at source), the `has_composite_pk` docstring (both named elision deciders verified at source), the `instance_accessor` three-tier docstring, and the two inline annotations (`# pragma: no cover`, `# type: ignore[attr-defined]`) are all accurate against the current implementation and the live Django descriptor semantics. No stale TODOs, no spec-anchor drift.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source, test, or doc edits this cycle (review-only, empty diff). Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md` (silent on changelog entries for review cycles), no changelog entry is warranted.

---

## Verification (Worker 3)

### Logic verification outcome
No-source-edit (shape #5) cycle verifying the maintainer's DRY-cycle additions, cumulative in HEAD. Zero-edit proof clean on all axes: `git diff a48c9104887438ca73a15c86d693b872112ee795 -- django_strawberry_framework/utils/relations.py` empty, `git diff HEAD -- …relations.py` empty, owned-paths stat (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) empty, `git diff -- CHANGELOG.md` empty. Dirty tree is `docs/feedback2.md` + four `docs/review/` artifacts only — no tracked source/test path touched, no sibling attribution needed. All three Worker 2 sections carry the `Filled by Worker 1 per no-source-edit cycle pattern.` gate line.

High / Medium: `None.` independently confirmed — there is no actionable finding suppressed below severity. The two Lows are both genuinely forward-looking with explicit triggers:
- **`instance_accessor` not in `__all__`** — confirmed at source: `utils/__init__.py:33-37 __all__ = ("RelationKind", "is_many_side_relation_kind", "relation_kind")` omits `instance_accessor`, and the package docstring `relations` bullet (`utils/__init__.py:7-8`) lists the same three. `grep -rn "has_composite_pk\|is_forward_many_to_many"` shows every cross-folder consumer imports via the `..utils.relations` submodule, not the package root — so the split is consistent across all call sites and both doc surfaces. Trigger (package-root import of `instance_accessor`) unfired. Forward-looking, no action.
- **Bare `return field.name` final tier** (`relations.py:143`) — loud `AttributeError`-at-call-site is the correct internal-helper contract; recorded for completeness, no action.

Spot-checks of the `What looks solid` claims:
- **`relation_kind` classification** (`:72-80`) verified branch-by-branch: `many_to_many`→`"many"`; `one_to_many`+`auto_created`→`"reverse_many_to_one"` else defensive `"many"`; `one_to_one`+`auto_created`→`"reverse_one_to_one"`; else `"forward_single"`. Order is correct (forward M2M and reverse M2M both short-circuit on the first branch). All five outcomes pinned in `tests/utils/test_relations.py` incl. the defensive `one_to_many`-without-`auto_created` fallback (`test_relation_kind_classifies_one_to_many_as_many`, test:35) and the forward-O2O-vs-reverse-O2O split.
- **`is_forward_many_to_many`** (`:106-108`) = `bool(many_to_many) AND (bool(concrete) OR NOT auto_created)` — admits forward `ManyToManyField` (concrete / not auto-created), excludes the reverse `ManyToManyRel` accessor (auto-created, not concrete). `getattr(..., False)` defaults match `relation_kind`'s read contract. Consumed by EXACTLY the two named mutation surfaces: `mutations/inputs.py:189` (`_select_editable_fields`) and `mutations/resolvers.py:301` (`_index_relation_fields`) — grep-confirmed, no third call site, no re-spelling.
- **`has_composite_pk` single-sourced and convergent** — `grep -rn has_composite_pk` returns 1 def (`relations.py:146`) + 1 consumer (`field_meta.py:224`, the `fk_id_elision_eligible` conjunct). The walker's raw-field elision fallback (`optimizer/walker.py:870`) routes through `FieldMeta._from_field_shape(field, is_relation=True).fk_id_elision_eligible` rather than re-spelling the predicate, so both elision deciders converge on this one guard. Confirmed no None-deref: `field_meta.py:218` `related_model is not None` precedes `:224 not has_composite_pk(related_model)` in the same conjunction, and `has_composite_pk` itself reads `getattr(model._meta, "pk_fields", None)` defensively, returning `True` only for a multi-field tuple (`len(...) > 1`).
- **TYPE_CHECKING pragma** (`:7-8`) genuinely unreachable, not a coverage dodge: `if TYPE_CHECKING:` is `False` at runtime, and `from __future__ import annotations` (`:3`) keeps the sole runtime reference (`type[models.Model]` annotation at `:146`) an unevaluated string, so the deferred `from django.db import models` import is never needed at runtime. `# pragma: no cover` covers no live executable code — correct per AGENTS.md #12.

### DRY findings disposition
DRY-None genuine: this module IS the single-source-of-truth relation-shape classifier. Confirmed both DRY-cycle predicates single-sourced — `has_composite_pk` (1 def / 1 consumer) and `is_forward_many_to_many` (1 def / 2 named consumers) — with no straggler re-spelling at any call site. Nothing forwarded.

### Temp test verification
None — no temp tests created; existing-test cycle, not this cycle's scope to add tests.

### Changelog disposition
`Not warranted` accepted: `git diff -- CHANGELOG.md` empty; disposition cites BOTH `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization. Internal-only framing matches the empty diff scope.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `utils/relations.py` checklist box in `docs/review/review-0_0_11.md`.
