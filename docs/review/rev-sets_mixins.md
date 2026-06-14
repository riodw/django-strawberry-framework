# Review: `django_strawberry_framework/sets_mixins.py`

Status: verified

## DRY analysis

- None — this module IS the 0.0.9 DRY consolidation product (`docs/feedback.md` Major 3). The four shared mechanisms — `ClassBasedTypeNameMixin.type_name_for`, `RelatedSetTargetMixin` (owner-bind + lazy-target), `collect_related_declarations`, `expanded_once`, and `SetLifecycleAttrs` — each single-site logic that previously existed as byte-parallel copies across the filter and order families. Both consuming families now delegate through these symbols: `filters/sets.py:177-184` + `filters/base.py:370-470`; `orders/sets.py:111-118` + `orders/base.py:30-86`. Each consumer carries only family-named thin wrappers (`bind_filterset`/`bind_orderset`, the `.filterset`/`.orderset` properties) plus per-family attr-name parameterization (`_target_attr`/`_owner_attr`, the `SetLifecycleAttrs` slot names). The repeated `"InputType"` literal (lines 73-74) is a defaulted class attribute the subclass overrides independently, not a duplicated dispatch key — correct as-is. No further consolidation is available inside this file; folding the family-named wrappers into the mixin would erase the family-named public surface the package deliberately preserves (`RelatedSetTargetMixin` docstring, lines 162-165).

## High:

None.

## Medium:

None.

## Low:

### GLOSSARY prose attributes the `ConfigurationError`-naming-both-attempts contract to the shared mixin (cross-file follow-up)

`docs/GLOSSARY.md` `RelatedOrder` entry describes the unqualified-name fallback as resolving through `sets_mixins.LazyRelatedClassMixin` and "fail loud with a `ConfigurationError` naming both attempts if neither resolves." `sets_mixins.py` itself does NOT do this: `resolve_lazy_class` (`django_strawberry_framework/sets_mixins.py::LazyRelatedClassMixin.resolve_lazy_class`, lines 129-136) propagates the raw `ImportError` from the second `import_string` attempt unchanged, and its own docstring (lines 119-128) accurately documents that propagation. The `ConfigurationError` rewrap happens one layer up at finalize time (`django_strawberry_framework/types/finalizer.py::_bind_ordersets` subpass 2, lines 1253-1256), and that rewrap preserves the original via `__cause__`/`repr` but the consumer-visible message names only the second (module-prefixed) attempt's path, not both. The mixin's local docstring is correct; the GLOSSARY sentence over-claims the error shape and mis-locates which layer raises `ConfigurationError`. This is a GLOSSARY-prose nuance about the *finalizer/RelatedOrder* layer, not a defect in `sets_mixins.py`, so it requires no edit to the target file. Defer to the orders folder pass or a GLOSSARY-accuracy sweep; tighten the GLOSSARY sentence to "propagates an `ImportError` that the finalizer rewraps as `ConfigurationError`, naming the resolved path it attempted." Recorded here as the cross-file forward; verbatim replacement text preserved for whichever pass picks it up.

## What looks solid

### DRY recap

- **Existing patterns reused.** Reuses `exceptions.ConfigurationError` (line 48) for the empty-pascal guard and `utils.strings.pascal_case` (line 49) in place of the cookbook's `stringcase.pascalcase`, keeping the package's single naming-normalization helper authoritative. `RelatedSetTargetMixin` extends `LazyRelatedClassMixin` (line 142) so the string/callable resolution body is shared, not re-copied. Both families consume `SetLifecycleAttrs.binding_attrs` through `utils/inputs.py::clear_generated_input_namespace` (`utils/inputs.py:265`), so registry-reset attr names cannot drift from the expansion-cache attr names.
- **New helpers considered.** Folding the family-named wrappers (`bind_filterset`/`bind_orderset`, the `.filterset`/`.orderset` getters+setters at `filters/base.py:421-470`, `orders/base.py:61-86`) into `RelatedSetTargetMixin` was considered and correctly rejected: the package deliberately keeps the family-named public surface (mixin docstring lines 162-165), and the wrappers are one-liners over `_bind_owner`/`_resolved_target`/`_set_target`. No further helper is warranted at this granularity.
- **Duplication risk in the current file.** The two `"InputType"` literals (lines 73-74, flagged by the shadow repeated-literal scan) are intentional defaulted class attributes, not a duplicated dispatch key; `FilterSet` overrides `_field_type_suffix` to `"FilterInputType"` while `OrderSet` keeps both defaults — the values must be independently overridable, so a shared constant would be wrong.

### Other positives

- `type_name_for` (lines 76-99) handles root (`field_path is None`) and `LOOKUP_SEP`-nested paths in one implementation, and the empty-pascal guard (lines 93-98) closes a real collision class — `""`/`"_"`/`"__"` field names would otherwise collapse the per-field type name onto the root type name; raising `ConfigurationError` at the call site with the offending `field_path!r` and a remediation sentence is the right fail-loud shape. Both consumers exercise both branches (`filters/inputs.py:199` root, `filters/inputs.py:707` per-field).
- `expanded_once` (lines 231-275) reads the cache via `cls.__dict__.get` (NOT `getattr`), correctly preventing a subclass from inheriting a parent's completed expansion cache via MRO and preventing an in-flight class (the metaclass runs `super().__new__` → `get_filters` before stamping `related_filters`) from serving a half-built result. The `on_reentry` seam is parameterized so the filter side gets its self-referential-cycle fallback (`filters/sets.py:373` passes `get_base`) while the order side passes `None` (`orders/sets.py:220-225`) because its expansion never re-enters — a clean way to share the skeleton without forcing the order side to carry a dead branch. The reentry guard is reset in a `finally` on every path including the cache-write path.
- `is not None` cache sentinel (line 267) is correct: an empty `OrderedDict` is a legitimate cached expansion result (a model with no filters/fields) and is returned from cache rather than re-built, while the unset slot (`None`) and the "conditions-not-met, don't cache" path both re-run `build()`. The single-threaded contract is documented explicitly (lines 260-264) with a clear "do not introduce a `threading.local` here without a real consumer call path" guard against speculative complexity.
- `_bind_owner` idempotency (lines 171-174) keys off `hasattr(self, self._owner_attr)`; confirmed neither `RelatedFilter` nor `RelatedOrder` declares a class-level `bound_filterset`/`bound_orderset` default (grep), so the first bind wins and a second divergent bind is a silent no-op by design — strict cross-owner mismatch is deferred to finalize (`filters/base.py:428-451` documents this; `types/finalizer.py::_bind_filterset_owner`).
- `collect_related_declarations` (lines 190-228) correctly branches its MRO policy: `inherit_from_bases=False` for the filter side (where `django_filters`' metaclass has already MRO-merged `declared_filters`, so only the `isinstance` filter runs) and `True` for the order side (plain `type` metaclass, so it copies each base's `collection_attr` in reversed-MRO order before the class body's own items override). Both consumers' call sites (`filters/sets.py:177-184`, `orders/sets.py:111-118`) match this contract and document the choice inline.
- `SetLifecycleAttrs` is `@dataclass(frozen=True)` and exposes `binding_attrs` as the single `(owner, cache, guard)` tuple the registry-reset consumes (`utils/inputs.py:265`). Both families declare exactly one `_lifecycle` instance (`filters/sets.py:246`, `orders/sets.py:171`) with the same `owner="_owner_definition"` slot and family-specific cache/guard slots — the descriptor is the one place the attr names live instead of re-spelled tuples.
- `__all__` (lines 301-308) matches the module's public symbols; the module docstring (lines 1-36) is honest about what is deliberately NOT ported yet (`get_concrete_field_names`, the two factory mixins) and why (the 100%-coverage gate would flag them as dead) — the right call per `AGENTS.md` "add the surface when its consumer lands." Card IDs in the docstring (`WIP-ALPHA-028-0.0.8`) and the subpackage spelling (`fieldsets`) are current, resolving the prior-cycle (0.0.7) Lows.

### Summary

`sets_mixins.py` is the 0.0.9 DRY-pass consolidation home for the set-family declaration/expansion lifecycle, and it holds up cleanly under logic review. The cache/guard semantics in `expanded_once` correctly defend against MRO inheritance, in-flight half-builds, and self-referential cycles; `type_name_for`'s empty-pascal guard closes a real type-name-collision class; `collect_related_declarations` selects the right MRO-merge policy per family; and `SetLifecycleAttrs` single-sites the lifecycle attr names. Both the filter and order families consume every shared symbol consistently through family-named thin wrappers, confirming the abstraction is used as designed rather than worked around. No High or Medium findings. The single Low is a cross-file GLOSSARY-prose accuracy nit about `RelatedOrder`'s error shape that mis-attributes the `ConfigurationError` rewrap to this module and over-claims "naming both attempts"; it is deferred to the orders folder pass and requires no edit to `sets_mixins.py`. The module's own docstrings are accurate.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (265 files left unchanged; the standing COM812-vs-formatter config warning is unrelated to this cycle and produced no edit).
- `uv run ruff check --fix .` — pass (All checks passed!).

### Notes for Worker 3
- No High; no behaviour-changing Medium. Single Low is a cross-file GLOSSARY-prose follow-up forwarded to the orders folder pass / a GLOSSARY-accuracy sweep — it requires no edit to `sets_mixins.py` and no in-cycle GLOSSARY edit, so shape #5 (no-source-edit) applies cleanly.
- No GLOSSARY-only fix in scope: the one GLOSSARY-touching follow-up is deferred (not a same-cycle edit), so it does not pull this cycle into shape #4.
- Low disposition: the `RelatedOrder` GLOSSARY sentence over-claims that `LazyRelatedClassMixin` raises `ConfigurationError` "naming both attempts." The mixin propagates a raw `ImportError` (its own docstring is correct); the `ConfigurationError` rewrap lives in `types/finalizer.py::_bind_ordersets` and names only the resolved path. Forwarded with verbatim replacement text in the artifact's `## Low:` body for whichever pass picks it up. No source/test/GLOSSARY edit this cycle.
- No shadow file regenerated; the plan-time overview at `docs/shadow/django_strawberry_framework__sets_mixins.overview.md` matched current source (12 symbols, the four 0.0.9 DRY mechanisms present).

---

## Verification (Worker 3)

### Logic verification outcome

Shape #5 (no-source-edit) terminal verification. Independently confirmed:

- **Baseline diff empty.** `git diff 0872a20f -- django_strawberry_framework/sets_mixins.py` empty; `git diff --stat 0872a20f -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty. Dirty tracked files are only the cycle's `rev-*.md` artifacts plus deleted root `feedback2.md`/`feedback3.md` (AGENTS.md #33 concurrent-maintainer work, untouched).
- **No High / no Medium** — confirmed by inspection; the module is the 0.0.9 DRY-consolidation home.
- **DRY "none" claim verified.** Both consuming families delegate through every shared symbol: `RelatedSetTargetMixin` (`filters/base.py:370` `RelatedFilter`, `orders/base.py:30` `RelatedOrder`, each with family-named thin wrappers `bind_filterset`/`.filterset` and `bind_orderset`/`.orderset` over `_bind_owner`/`_resolved_target`/`_set_target`); `ClassBasedTypeNameMixin`, `SetLifecycleAttrs`, `collect_related_declarations`, `expanded_once` all imported and used by `filters/sets.py` and `orders/sets.py`. `binding_attrs` consumed at `utils/inputs.py:265`. No further consolidation available without erasing the deliberately-preserved family-named public surface.
- **`expanded_once` on_reentry parameterization verified live in source:** filter side passes `on_reentry=get_base` (`filters/sets.py:373`), order side omits it (`orders/sets.py:225`) — matches the "order expansion never re-enters `get_fields`" claim.
- **The two `"InputType"` literals (lines 73-74) are not a duplicated dispatch key:** `FilterSet` overrides `_field_type_suffix = "FilterInputType"` (`filters/sets.py:292`) and keeps the default root suffix; `OrderSet` overrides neither (`orders/sets.py:140`). Values must be independently overridable — a shared constant would be wrong. Confirmed.

**Lone Low — verified correctly deferred, NOT a `sets_mixins.py` defect, NOT an in-cycle GLOSSARY fix.** Reproduced the crux live (temp probe under `docs/review/temp-tests/sets_mixins/`, since deleted): `LazyRelatedClassMixin.resolve_lazy_class("NoSuchClassXYZ", None)` raises a raw `ImportError` ("doesn't look like a module path") unchanged; with a truthy bound owner whose `__module__` is unresolvable, it raises a `ModuleNotFoundError` (an `ImportError` subclass) naming ONLY the second module-prefixed attempt ("No module named 'some'"), never a `ConfigurationError`. The mixin's own docstring (lines 119-128) is accurate. The `ConfigurationError` rewrap lives one layer up in the finalizer (`types/finalizer.py::_finalize_set_family` subpass 2, line 1201) embedding `{exc}` — which carries only the resolved path, not both attempts. The GLOSSARY `RelatedOrder` (line 1004) and `RelatedFilter` (line 994) entries' "fail loud with a `ConfigurationError` naming both attempts" is over-claimed standing prose about the finalizer/RelatedOrder layer; it correctly requires no edit to `sets_mixins.py` and is not a same-cycle GLOSSARY edit. Shape #5 holds. Deferral to the orders folder pass / a GLOSSARY-accuracy sweep is correct, with verbatim replacement text preserved in the `## Low:` body.

### DRY findings disposition

DRY analysis = "None" (this module IS the consolidation product). Verified the claim by confirming both families consume every shared symbol and no further intra-file consolidation is available. Carried forward: nothing.

### Temp test verification

- Temp test: `docs/review/temp-tests/sets_mixins/probe.py` (gitignored), driving `resolve_lazy_class` in both the falsy-owner and truthy-owner-both-attempts-fail directions.
- Disposition: deleted after use. Behavior is already correct in source and accurately documented by the local docstring; no new permanent test warranted (no-source-edit cycle, no defect surfaced).

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `sets_mixins.py` checklist box.

Additional shape #5 checks: each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.`; the lone Low carries verbatim forwarded replacement text (no GLOSSARY-only same-cycle fix); changelog `Not warranted` cites both `AGENTS.md` and the active plan's silence with an empty `git diff -- CHANGELOG.md`; `uv run ruff format --check` reports the file already formatted and `uv run ruff check` reports all checks passed (the COM812 warning is the standing config warning, not a finding).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits — the module's own docstrings are accurate (the prior-cycle 0.0.7 Lows on card-ID, subpackage spelling, "Verbatim port" claim, and the `bound_class is None` fold-back are all already resolved in current source). The single Low is cross-file GLOSSARY prose, not a `sets_mixins.py` comment edit.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

`Not warranted`. No source, test, or behaviour change this cycle — internal-only review with one deferred cross-file documentation follow-up. Per `AGENTS.md` ("Do not update `CHANGELOG.md` unless explicitly instructed") and the active plan `docs/review/review-0_0_9.md`'s silence on changelog authorisation for this cycle, no `CHANGELOG.md` edit is warranted.

---

## Iteration log

(none yet)
