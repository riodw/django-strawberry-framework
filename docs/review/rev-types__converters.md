# Review: `django_strawberry_framework/types/converters.py`

Status: verified

## DRY analysis

- **Existing patterns reused.** `convert_scalar` calls `ConfigurationError` from `..exceptions:1-15` (the canonical error type — see `rev-exceptions.md`); `_resolve_array_field`/`_resolve_hstore_field` follow the soft-import + module-level sentinel idiom that mirrors `scalars.py:91-102`'s `with warnings.catch_warnings()` posture of paying the import-time cost once and caching the result. `convert_choices_to_enum` uses `pascal_case` from `..utils.strings:46` for the enum name, and threads the `(model, field_name)` cache through `registry.get_enum`/`register_enum` at `registry.py:352-387`. `resolved_relation_annotation` and `convert_relation` delegate cardinality classification to `FieldMeta.from_django_field` (`optimizer/field_meta.py:113-170`) + the canonical `relation_kind` / `is_many_side_relation_kind` helpers in `utils/relations.py:39-70`, so the relation-shape rule is single-sited. `PendingRelationAnnotation` is the sentinel sourced from `types/relations.py:46-47`; `finalize_django_types()` at `types/finalizer.py:130-133` re-uses `resolved_relation_annotation` to write back the resolved annotation, which keeps the production rewrite-path and the public `convert_relation` test surface in sync.
- **New helpers a fix might justify.** None warranted at file scope today. The `_resolve_array_field` / `_resolve_hstore_field` pair is the only candidate — a generic `_resolve_postgres_field("ArrayField") | None` would centralize the soft-import body — but two call sites with two literal names is not yet a bar-clearing duplication, and the explicit pair gives test-side `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", ...)` a stable name to bind. Re-evaluate when the third postgres-soft-import lands (no current spec home).
- **Duplication risk in the current file.** The repeated-literal scanner reports zero hits ≥ 8 chars; the `f"{field.model.__name__}.{field.name}"` prefix repeats four times in error messages (lines 150, 154, 168, 188-189, 250, 264, 288-289) but each substring is locally formatted into a longer custom message and tests grep on the message body, so collapsing through a shared `_field_label(field)` helper would inflate the diff without changing the consumer-visible shape — flag at the folder pass alongside the three sibling formatters (`_format_unknown_fields_error` / `_format_unresolved_targets_error` / `_format_ambiguity_error`) carried forward from `rev-types__base.md`. Two near-copies inside this file: (1) lines 152-157 vs lines 166-172 both gate `field.choices` and raise a near-parallel ConfigurationError; the bodies differ enough that collapsing through a shared helper would lose the per-branch wording. (2) The `field.null` post-widening pattern (`return result | None if field.null else result` at line 160, `return py_type | None if field.null else py_type` at line 174, `if field.null: py_type = py_type | None` at line 194-195) appears three times in `convert_scalar`; collapsing is not worth the readability hit because the surrounding context differs (recursive inner, sentinel return, MRO-walked py_type), and the imperative form at 194 is structurally required because it follows the choice substitution at 192-193.

## High:

None.

## Medium:

### `convert_relation` is dead code in the production pipeline and silently bypasses the multi-type / primary contract

`convert_relation` is the public entry point named in the module docstring (`converters.py:7`) and re-exported via `types/__init__.py:6`, but the production pipeline at `_build_annotations` (`types/base.py:810-821`) never calls it — every relation auto-synthesizes through `PendingRelationAnnotation` and is resolved at finalize time by `resolved_relation_annotation` (`types/finalizer.py:130-133`). The only consumers of `convert_relation` are two tests at `tests/types/test_base.py:695-700,734-751`. The deferred-resolution path was added by spec-014 (the H1 always-defer rule comment at `base.py:800-809` calls out the import-order trap closure). `convert_relation` at lines 312-350 still uses the EAGER `registry.get(target_model)` shape — for a model with two registered `DjangoType`s and a declared primary, this returns the primary, which matches `_build_annotations`' new behavior; but for a model with two registered types and no primary, `convert_relation` SILENTLY returns whichever happened to register first (per `registry.get`'s single-type fallback), where the production pipeline would surface `_audit_primary_ambiguity` at finalize. The public surface is therefore an attractive nuisance: a consumer who imports `convert_relation` to wire a custom resolver gets a multi-type-resolution behavior that disagrees with the rest of the package and never sees the audit. Two recommended changes, either one acceptable: (a) drop `convert_relation` from the module and the `types/__init__` re-export, update the two tests to call `resolved_relation_annotation(field, registry.get(target_model))` directly, and rewrite the module docstring at lines 1-13 to enumerate the actual public surface (`convert_scalar`, `convert_choices_to_enum`, `resolved_relation_annotation`, `SCALAR_MAP`); or (b) keep `convert_relation` but route it through the same multi-type / primary disambiguation the production pipeline uses (call `_audit_primary_ambiguity` or surface a typed `ConfigurationError` when `registry.models_with_multiple_types()` includes the target and no primary is declared). Path (a) is simpler and matches what the actual call graph already does.

```django_strawberry_framework/types/converters.py:312:350
def convert_relation(field: models.Field) -> Any:
    """Map a Django relation field to its target ``DjangoType``.
    ...
    """
    target_model = field.related_model
    target_type = registry.get(target_model)
    if target_type is None:
        return PendingRelationAnnotation
    return resolved_relation_annotation(
        field,
        target_type,
        field_meta=FieldMeta.from_django_field(field),
    )
```

Test expectation: if path (a) is taken, the two tests at `tests/types/test_base.py:695-700,734-751` migrate to call `resolved_relation_annotation` directly against a `registry.get(target_model)`-supplied target. If path (b) is taken, add a new test pinning the multi-type-no-primary surface that `convert_relation` raises (or audits) rather than silently returning the first-registered type.

### `SCALAR_MAP` is typed as a mutable `dict` and is public, but rebinding rules are undocumented and asymmetric with `registry.register_enum`'s strict re-registration guard

`SCALAR_MAP: dict[type[models.Field], Any]` at line 33 is module-level public state. The module docstring (lines 1-13) does not mention it; the `convert_scalar` error message at lines 187-191 instructs consumers to "Add an entry to SCALAR_MAP or exclude this field via Meta.exclude". Two real consumer paths follow from that instruction: (i) consumer registers a third-party field class (the documented extension point); (ii) test code monkey-patches a deletion at `tests/types/test_base.py:599` (`monkeypatch.delitem(converters.SCALAR_MAP, models.TextField)`). The current shape supports both, but the contract is unwritten: is overwrite allowed? When does the package read it (every `convert_scalar` call)? Is it safe to mutate after `finalize_django_types()`? Compare with `registry.register_enum` at `registry.py:352-379` — same shape (module-singleton dict keyed by Django-side object) but with an explicit `_check_mutable()` guard, an "already registered as <X>" rejection, and a no-op re-registration of the same class. The asymmetry is a maintainer trap: a consumer who writes `SCALAR_MAP[MoneyField] = decimal.Decimal` in two modules silently overwrites; the same consumer doing `registry.register_enum(...)` from two modules would get a typed error. Recommend either (a) document `SCALAR_MAP` as a write-once-per-key contract in the module docstring and add an `add_scalar(field_cls, py_type)` helper that delegates to `SCALAR_MAP[field_cls] = py_type` with a same-class no-op + different-class rejection, or (b) keep `SCALAR_MAP` plain but note explicitly in the module docstring that it is a mutable public extension point with last-write-wins semantics and is read on every `convert_scalar` call (so post-finalize mutations are visible). The MRO walk at lines 182-185 already supports the canonical extension path (subclass-of-supported-field), so the documented extension story should foreground subclassing first and `SCALAR_MAP[...] = ...` only for non-subclass cases.

```django_strawberry_framework/types/converters.py:33:62
SCALAR_MAP: dict[type[models.Field], Any] = {
    models.AutoField: int,
    ...
    models.BigIntegerField: BigInt,
    ...
    models.PositiveBigIntegerField: BigInt,
    ...
}
```

Test expectation: if (a) is taken, add a test pinning `add_scalar` same-class no-op + different-class rejection, mirroring `tests/test_registry.py`'s enum-registration tests. If (b) is taken, no test change required; the docstring claim is grep-pinned by `tests/base/test_conf.py`-style module-docstring assertions if the codebase has any (none today for converters.py specifically).

## Low:

### Module docstring under-counts the file's public surface

The docstring at lines 1-13 advertises "Two halves: `convert_scalar(field, type_name)` and `convert_relation(field)`", but the file also exports `convert_choices_to_enum`, `resolved_relation_annotation`, `SCALAR_MAP`, and the sentinel-guarded `_ARRAY_FIELD_CLS` / `_HSTORE_FIELD_CLS` module-level state plus their `_resolve_*` helpers (test code at `tests/types/test_converters.py:880,915,953,1023,1042,1069,1107,1131,1158,1255,1288,1323,1358,1394,1418` monkey-patches the underscore-prefixed sentinels, so they are private-by-convention but test-public). Rewrite to enumerate the four public functions plus `SCALAR_MAP` as the documented extension point, and split the "two halves" framing into scalar / choice / relation. The current framing makes `convert_choices_to_enum` look like an internal helper, which the test file at `tests/types/test_converters.py:33` contradicts by importing it directly.

```django_strawberry_framework/types/converters.py:01:13
"""Convert Django model fields to Strawberry-compatible Python types.

Two halves:

- ``convert_scalar(field, type_name)`` — scalar columns
  ...
- ``convert_relation(field)`` — FK / OneToOne / reverse / M2M, returning
  ...
"""
```

### `convert_relation` redundantly pre-computes `field_meta` that `resolved_relation_annotation` would build by default

`resolved_relation_annotation`'s signature at lines 297-302 already defaults `field_meta=None` and constructs `FieldMeta.from_django_field(field)` on `None` at line 304. `convert_relation` at line 349 passes `field_meta=FieldMeta.from_django_field(field)` explicitly, duplicating the construction. The redundancy is harmless today (one extra `FieldMeta.from_django_field` build per `convert_relation` call), but it makes a future maintainer think the explicit thread is load-bearing — for example, when the next consumer-API change asks "where does `convert_relation` get the FieldMeta from?" the answer is "twice, once explicitly here and once by default in the helper." Either drop the `field_meta=...` keyword from line 349 (let the helper default kick in) or document at line 348 why the explicit thread exists. If the Medium finding "convert_relation is dead code" lands as path (a), this finding goes away with it.

```django_strawberry_framework/types/converters.py:342:350
target_model = field.related_model
target_type = registry.get(target_model)
if target_type is None:
    return PendingRelationAnnotation
return resolved_relation_annotation(
    field,
    target_type,
    field_meta=FieldMeta.from_django_field(field),
)
```

### `convert_choices_to_enum` walks the choices list twice (grouped-form detection + member build), one pass over the materialized list would suffice

Lines 254-268 iterate `choices` to detect Django's grouped-choices form; lines 277-282 iterate `choices` again to build `members`. Both passes are O(n) and the choice list is small in practice, so this is purely a style nit, but the two passes pre-date the collision-detection rewrite at lines 276-290 and could be folded into a single pass: per-row, raise on grouped-form on the first iteration, then add to members + track collisions. Collapse only if the loop body stays readable. The current shape is grep-friendly (grouped-form rejection is its own loop block), so leave the form alone unless the next change to this function would naturally fold it.

```django_strawberry_framework/types/converters.py:254:282
for _value, label in choices:
    # grouped-form detection
    if isinstance(label, (list, tuple)):
        raise ConfigurationError(...)

cached = registry.get_enum(field.model, field.name)
if cached is not None:
    return cached

enum_name = f"{type_name}{pascal_case(field.name)}Enum"
members: dict[str, Any] = {}
collisions: dict[str, list[Any]] = {}
for value, _label in choices:
    member = _sanitize_member_name(value)
    if member in members:
        collisions.setdefault(member, [members[member]]).append(value)
    else:
        members[member] = value
```

### `convert_scalar` reassigns `py_type` in HStoreField branch but the variable is only declared at line 175 (after the branch returns)

At line 173, `py_type = strawberry.scalars.JSON` runs inside the `_HSTORE_FIELD_CLS` branch, which is BEFORE the `py_type: Any = None` declaration at line 175. The HStore branch returns immediately at line 174, so this is harmless (the post-branch `py_type` declaration only matters on the MRO-walk path), but a reader scanning top-down sees a local-without-annotation reassigned before its annotated declaration. Move `py_type: Any = None` to line 174 (above the ArrayField sentinel) or drop the annotation entirely (the type-checker will infer `Any` from the dict lookup). Pure readability nit, no behavioral change.

```django_strawberry_framework/types/converters.py:165:185
if _HSTORE_FIELD_CLS is not None and isinstance(field, _HSTORE_FIELD_CLS):
    if field.choices:
        raise ConfigurationError(...)
    py_type = strawberry.scalars.JSON
    return py_type | None if field.null else py_type
py_type: Any = None
# Walk the field's MRO ...
for klass in type(field).__mro__:
    if klass in SCALAR_MAP:
        py_type = SCALAR_MAP[klass]
        break
```

### `_NON_IDENT` / `_GRAPHQL_RESERVED_ENUM_VALUES` module-level singletons sit BELOW `convert_scalar` and ABOVE `_sanitize_member_name`

Lines 199-200 define module-level constants used only by `_sanitize_member_name` at line 203. The ordering puts the constants after `convert_scalar`'s docstring continuation, breaking the "module constants at the top, then helpers, then public functions" convention that `SCALAR_MAP` at line 33 follows. Move the two constants up next to `SCALAR_MAP` (or down into `_sanitize_member_name`'s body if they are truly private to that helper — they are, since they have leading underscores and zero other call sites). Pure file-layout nit.

```django_strawberry_framework/types/converters.py:199:223
_NON_IDENT = re.compile(r"\W+", flags=re.ASCII)
_GRAPHQL_RESERVED_ENUM_VALUES = frozenset({"false", "null", "true"})


def _sanitize_member_name(value: Any) -> str:
    ...
```

## What looks solid

- The static helper ran cleanly (351 lines, two hotspots at `convert_scalar` and `convert_choices_to_enum`, both adequately documented; zero repeated literals ≥ 8 chars; zero TODOs). Both hotspots are well-pinned: `tests/types/test_converters.py` covers every branch (ArrayField nested/outer-choices/inner-null/outer-null/unsupported-base/sentinel-none, HStoreField outer-choices/sentinel-none, BigInt mapping for `BigIntegerField` + `PositiveBigIntegerField`, JSON for `JSONField`, choice grouped-form/collision/keyword-prefix-collision/reserved-name-collision/null-widening, MRO subclass resolution with and without null).
- `SCALAR_MAP` ordering is correct: `AutoField` / `BigAutoField` / `SmallAutoField` precede the generic `IntegerField` family (test pins `BigAutoField` -> `int` at `test_big_auto_field_still_maps_to_int`), and the `BigIntegerField` / `PositiveBigIntegerField` rows at lines 45 and 49 map to `BigInt` per the spec-015 carry-forward from `rev-scalars.md`. Verified `BigInt` is imported once from `..scalars` at line 29 and consumed at exactly these two rows — no parallel `strawberry.scalar(...)` calls leaked into this module.
- Sentinel-guarded `ArrayField` / `HStoreField` dispatch runs BEFORE the MRO walk at lines 147,165 — the comment block at 141-146 explicitly calls out the test-double bypass risk that the ordering defends against. The `_ARRAY_FIELD_CLS is not None` short-circuit pattern at 147,165 is symmetric and pinned by `test_array_field_sentinel_none_path` / `test_hstore_field_sentinel_none_path`.
- Choice-substitution-then-null-widening ordering at lines 192-195 is the load-bearing invariant that `test_choice_field_with_null_widens_to_enum_or_none` pins; the docstring at 113-115 explicitly calls out the ordering rationale. Same "structural ordering + test pinning" pattern carried forward from prior cycles (`_context.py`'s narrow-exception pin, `hints.py`'s sentinel-identity pin, `plans.py`'s tuple-swap on `finalize()`).
- `_sanitize_member_name` rules are layered defensively (digit-prefix → keyword-prefix → reserved-value / introspection-prefix) with the GraphQL-reserved set at line 200 already in casefold form; the `_value, label` choice unpacking at lines 254-268 detects grouped-form by inspecting `label` (not `value`), and the comment block at 255-261 calls out exactly why that's the load-bearing distinction.
- The `resolved_relation_annotation` helper at lines 297-309 is the canonical single-sited cardinality renderer reused by both `convert_relation` and `types/finalizer.py:130-133`'s post-resolution annotation rewrite, so the relation-shape rule has one truth path.

### Summary

351-line converter module owning Django-scalar / choice-enum / relation-cardinality conversion. The static helper ran clean (zero repeated literals ≥ 8, two hotspots both branch-pinned by `tests/types/test_converters.py`). 0 High / 2 Medium / 5 Low. The Mediums cluster on contract drift between this file's public surface and the rest of the package: `convert_relation` is dead code in the production pipeline (every relation defers through `PendingRelationAnnotation` since spec-014's always-defer rewrite at `base.py:800-809`) yet remains test-exercised and re-exported, and `SCALAR_MAP` is a mutable public extension point with no documented rebinding rules where the sibling `registry.register_enum` enforces strict guards. The five Lows are layout / docstring / file-ordering nits. SCALAR_MAP's `BigInt` rows at lines 45,49 match the spec-015 carry-forward from `rev-scalars.md`. Folder-pass DRY follow-ups recorded inline (per-field error-prefix formatter family alongside the three existing `_format_*` siblings).

## Fix report (Worker 2)

Logic pass (2026-05-20).

### Files touched

- `django_strawberry_framework/types/converters.py`:
  - **M1 path (a)**: deleted `convert_relation` (former lines 312-350). Removed the now-unused `from .relations import PendingRelationAnnotation` import; `registry` import stays (still used by `convert_choices_to_enum` for the enum cache).
  - **L4**: dropped the `py_type: Any = None` annotation at former line 175 → `py_type = None`. The type-checker infers `Any` from `SCALAR_MAP`'s value type; the HStore branch above returns early so the local lifetime only matters on the MRO-walk path that follows.
  - **L5**: moved `_NON_IDENT` / `_GRAPHQL_RESERVED_ENUM_VALUES` (former lines 199-200) to module-constant position immediately after `SCALAR_MAP`, keeping the "module constants → soft-import resolvers → public functions" ordering convention.

- `django_strawberry_framework/types/__init__.py`: not edited. `convert_relation` was never in `__all__`; the docstring mention of it as an "internal helper... reachable via dotted submodule paths" is a comment-pass concern.

- `tests/types/test_base.py`:
  - Replaced `convert_relation` import with `resolved_relation_annotation`.
  - **Dropped** `test_convert_relation_returns_pending_annotation_for_unregistered_target` (former lines 695-699): this test only pinned `convert_relation`'s registry-miss → `PendingRelationAnnotation` fallback, which is not a documented production code path. The production semantic (annotation set to `PendingRelationAnnotation` when target unregistered → `ConfigurationError` at finalize) is already pinned by `test_relation_unregistered_target_raises` at lines 676-692 immediately above. `resolved_relation_annotation` has no equivalent registry-miss branch — it expects a non-None `target_type` — so a direct migration of this test is not possible.
  - Migrated `test_convert_relation_nullable_fk_widens_to_optional` (former lines 734-751) → `test_resolved_relation_annotation_nullable_fk_widens_to_optional`. The call site now reads `resolved_relation_annotation(item_category, CategoryType)` and the docstring updated to describe the new path. Behavioral assertion unchanged: nullable forward FK widens to `T | None`.

### Tests added / updated

No new tests. Two existing tests migrated (one dropped as redundant, one re-pointed to `resolved_relation_annotation`). The dropped test is covered by the existing finalize-time test immediately above it.

### Validation

- `uv run ruff format .` — pass (100 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).
- `uv run pytest tests/types/test_base.py tests/types/test_converters.py -x` — 111 passed, 2 skipped. `types/converters.py` shows 100% line coverage in the focused run; overall TOTAL is 50.68% because only the two focused test files ran (expected, the package-wide 100% gate is exercised by CI).

### Notes for Worker 3

- **L1 (module docstring rewrite)** and **M2 (SCALAR_MAP rebinding-rule documentation)** are deferred to the comment pass per the original artifact + this turn's prompt. The current module docstring still says "Two halves: `convert_scalar` and `convert_relation`" — that wording is intentionally untouched in this logic pass.
- **L2 (redundant `field_meta` pre-compute in `convert_relation`)** dissolved with M1: `convert_relation` is gone, so the redundancy can't recur.
- **L3 (two-pass walk in `convert_choices_to_enum`)** carries the artifact's explicit "defer — current shape is grep-friendly" decision. No change.
- **Stale references to `convert_relation` outside scope**: `registry.py:6` (module docstring "Used by: types.converters.convert_relation for relation resolution"), `types/__init__.py:6` (subpackage docstring mention as an internal helper), `tests/optimizer/test_extension.py:1859,1960` (two stale comment references inside test fixtures), `AGENTS.md:8` ("converters.py owns convert_scalar, convert_choices_to_enum, convert_relation"), and `docs/TREE.md:204,247,336`. These are all docstring / comment / outside-scope mentions; none affect production behavior. `registry.py` and `types/__init__.py` were reviewed in prior cycles — flag for either the folder pass (types/) or the project pass to scrub at that level. The `AGENTS.md` line and `docs/TREE.md` lines are maintainer-edited surfaces.
- **`types/__init__.py:__all__`** was already `("DjangoType", "finalize_django_types")` before this pass — `convert_relation` was never publicly re-exported, despite the original artifact M1 framing. The original prompt's "remove from `__all__` and re-export line" step was therefore a no-op; only the docstring mention remains, and that lands in the comment pass.
- **No top-level `django_strawberry_framework/__init__.py` re-export of `convert_relation`** — verified via grep. The removal is contained.

---

## Verification (Worker 3)

Logic pass (2026-05-20).

### Logic verification outcome

- **High:** None — accepted.
- **M1 (`convert_relation` is dead code):** accepted. `convert_relation` deleted from `types/converters.py` (only remaining mention is the module docstring at line 7, deferred to comment pass). The `from .relations import PendingRelationAnnotation` import was removed. `types/__init__.py.__all__` was already `("DjangoType", "finalize_django_types")` — no live re-export removed. Grep across `django_strawberry_framework/`, `tests/`, `examples/` confirms no remaining LIVE imports of `convert_relation`; the five remaining mentions (`registry.py:6`, `types/__init__.py:6`, `types/converters.py:7`, `tests/types/test_base.py:435`, `tests/optimizer/test_extension.py:1859,1960`) are all docstring or comment text. Tests at `tests/types/test_base.py`: the dropped registry-miss test is structurally covered by `test_relation_unregistered_target_raises` at lines 676-692 (production finalize-time path); the nullable-FK test was re-pointed to `resolved_relation_annotation(item_category, CategoryType)` at line 743 with the consumer-supplied target type, exercising the equivalent cardinality-rendering path. Migration matches the artifact path (a) recommendation.
- **M2 (`SCALAR_MAP` rebinding-rule documentation):** accepted as deferred to comment pass per Worker 2's notes.
- **L1 (module docstring under-counts surface):** accepted as deferred to comment pass.
- **L2 (`convert_relation` redundant `field_meta` pre-compute):** accepted as dissolved with M1.
- **L3 (two-pass walk in `convert_choices_to_enum`):** accepted as deferred per the artifact's own "current shape is grep-friendly" decision.
- **L4 (HStore branch reassigns `py_type` before declaration):** accepted. Line 177 now reads `py_type = None` (annotation dropped); the HStore branch above at line 175 returns early, so the readability nit is resolved without a behavioral change.
- **L5 (module-constants ordering):** accepted. `_NON_IDENT` and `_GRAPHQL_RESERVED_ENUM_VALUES` now live at lines 63-64, immediately after `SCALAR_MAP` and before the soft-import resolvers, restoring the "module constants → soft-import resolvers → public functions" ordering convention.

### DRY findings disposition

The dead `convert_relation` path that diverged from the production multi-type / primary contract is removed; the two migrated tests now use the canonical `resolved_relation_annotation` helper with a consumer-supplied target type, so the relation-shape rule has a single truth path through the file. Folder-pass DRY follow-ups (per-field error-prefix formatter family alongside `_format_*` siblings; deferred AGENTS.md / TREE.md docstring scrubs of `convert_relation`) are recorded for the `types/` folder pass. Accepted.

### Temp test verification

None.

### Verification outcome

`logic accepted; awaiting comment pass`. Top-level `Status:` is intentionally NOT advanced; Worker 2 is next for the comment pass (M2 SCALAR_MAP rebinding-rule docs, L1 module docstring rewrite, plus the docstring-only `convert_relation` mention at line 7 and the cross-file stale references at `registry.py:6` / `types/__init__.py:6` which the artifact notes are out-of-scope for this file but tagged for folder/project pass).

---

## Comment/docstring pass

Comment + changelog pass (2026-05-20, Worker 2).

### Files touched

- `django_strawberry_framework/types/converters.py:1-29` — module docstring rewritten. Removed the obsolete "Two halves: ``convert_scalar`` and ``convert_relation``" framing. New docstring enumerates the actual public surface (`convert_scalar`, `convert_choices_to_enum`, `resolved_relation_annotation`, `SCALAR_MAP`) and documents `SCALAR_MAP` as a mutable, last-write-wins module-level mapping read on every `convert_scalar` call (so post-`finalize_django_types()` mutations stay visible). The extension-point note foregrounds **subclassing a supported field** (the MRO walk picks up subclasses automatically) and frames `SCALAR_MAP[FieldCls] = py_type` as the non-subclass hook. Crossreferences `convert_choices_to_enum` (called from `convert_scalar` when `field.choices` is set) and `resolved_relation_annotation` (reused by `types/finalizer.py`'s deferred-resolution path). Closes **L1** (module-docstring under-counts public surface) and **M2** (SCALAR_MAP rebinding-rule documentation).
- No other docstring edits required:
  - `convert_scalar`'s docstring at lines 113-158 — already accurate post-cleanup; the consumer-facing instruction "Add an entry to ``SCALAR_MAP`` or exclude this field via ``Meta.exclude``" inside the `ConfigurationError` at lines 206-209 is a fallthrough message (MRO walk has already failed to find a parent), so the subclass-first framing in the module docstring is the right place for that guidance — leaving the error string untouched (no test substring breakage, no consumer-facing wording regression).
  - `convert_choices_to_enum`'s docstring at lines 242-261 — accurately describes the post-cleanup behavior (grouped-form rejection, cache check, name compute, member sanitization, enum decoration, registry cache).
  - `resolved_relation_annotation`'s docstring at line 319 — already terse and accurate; never referenced `convert_relation`.

### Deferred items recorded

- **L3** (two-pass walk in `convert_choices_to_enum`): deferred per the original artifact's "current shape is grep-friendly" decision. No change.

### Validation

- `uv run ruff format .` — pass (100 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).
- pytest not run (per `AGENTS.md` rule: formatting only after edits).

### Notes for Worker 3

- The cross-file stale `convert_relation` references at `registry.py:6` (module docstring "Used by: types.converters.convert_relation for relation resolution"), `types/__init__.py:6` (subpackage docstring "Internal helpers (..., ``convert_relation``, ...)"), `tests/optimizer/test_extension.py:1859,1960` (comment text inside test fixtures), `AGENTS.md:8`, and `docs/TREE.md:204,247,336` are outside this file's scope. Two are in already-`verified` per-file artifacts (`registry.py`, `types/__init__.py` is folder-pass surface); `AGENTS.md` and `docs/TREE.md` are maintainer-edited surfaces; the test_extension.py comment text was reviewed in a prior cycle. Tagged for the `types/` folder pass and/or the project pass to scrub coherently.

---

## Changelog disposition

Changelog disposition (2026-05-20, Worker 2).

### Warranted?

**Warranted — deferred to maintainer.** The `convert_relation` removal IS a public-API change: the function was importable as `from django_strawberry_framework.types.converters import convert_relation` (the module-level binding was deleted in this cycle's logic pass). A consumer who had wired the helper into a custom resolver, a test scaffold, or a docs example will see an `ImportError` on the next upgrade. The dotted-submodule import path was the actually-reachable surface; `types/__init__.py.__all__` never re-exported the symbol, but the dotted path was documented as reachable in `types/__init__.py`'s subpackage docstring at line 6 ("Internal helpers (..., ``convert_relation``, ...) stay reachable via their dotted submodule paths") and in `AGENTS.md:8` ("converters.py owns convert_scalar, convert_choices_to_enum, convert_relation"). So the import-breakage is real, even if no `__all__` entry advertised it.

### Reason

The function was effectively dead in the production pipeline since spec-014's always-defer rewrite at `base.py:800-809` (the logic pass artifact records that the only call sites were two tests at `tests/types/test_base.py:695-700,734-751`; the production pipeline routes every relation through `PendingRelationAnnotation` and resolves at finalize-time via `resolved_relation_annotation`). Worker 1 also flagged that `convert_relation`'s eager `registry.get(target_model)` shape silently bypassed the multi-type / primary disambiguation that the production pipeline applies, so a consumer wiring the helper into a custom resolver would have gotten a behavior divergent from the rest of the package. Both reasons argued for removal — but the import-path break is consumer-visible regardless of how dead the code was in practice.

### Suggested entry text (for the maintainer to lift verbatim at release time)

`### Removed`

- **Breaking:** `django_strawberry_framework.types.converters.convert_relation` removed. The function silently bypassed the multi-type / primary disambiguation that the production pipeline applies (it called `registry.get(target_model)` eagerly without `_audit_primary_ambiguity`, so a model with two registered `DjangoType`s and no declared primary returned whichever happened to register first). The deferred-resolution path through `_build_annotations` -> `PendingRelationAnnotation` -> `resolved_relation_annotation` is the supported surface. Migrate `convert_relation(field)` callers to `resolved_relation_annotation(field, registry.get(field.related_model))` if the target model is already finalized.

### What was done

No `CHANGELOG.md` edit. Deferred to maintainer per `AGENTS.md` line 12 ("Do not update CHANGELOG.md unless explicitly instructed") + active plan silence on a changelog pass for this file. The suggested entry above is recorded verbatim so the maintainer can lift it at release time. Same shape as the `plans.py` (consumer-`.only()`) and `walker.py` (typed-error contract change) cycles documented in `worker-memory/worker-2.md`.

### Out-of-scope stale references

Five non-source surfaces still mention `convert_relation` and will need a coherent scrub: `registry.py:6` (module docstring), `types/__init__.py:6` (subpackage docstring), `tests/optimizer/test_extension.py:1859,1960` (fixture comment text), `AGENTS.md:8` (package layout sentence), and `docs/TREE.md:204,247,336` (three tree-comment lines). None affects production behavior; flagged for the `types/` folder pass and the project pass to handle at the appropriate scope. `AGENTS.md` and `docs/TREE.md` are maintainer-edited surfaces.

### Validation

- `uv run ruff format .` — pass.
- `uv run ruff check --fix .` — pass.

---

## Iteration log

## Verification (Worker 3, pass 2)

Comment + changelog pass (2026-05-20).

- **Comment verification outcome:** Module docstring rewritten; SCALAR_MAP documented as extension point; `convert_relation` no longer referenced. Accepted.
- **Changelog verification outcome:** Warranted-but-deferred is the right disposition for a public API removal in a pre-alpha package; suggested entry text preserved for the maintainer. Accepted.
- **Verification outcome:** `cycle accepted; verified`. Top-level `Status:` advanced to `verified`; checklist box in `docs/review/review-0_0_6.md` marked.
