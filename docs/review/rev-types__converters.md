# Review: `django_strawberry_framework/types/converters.py`

## High:

### Subclass dispatch via exact-type lookup misses Django model field subclasses

`convert_scalar` uses `SCALAR_MAP.get(type(field))`, which is exact-type matching. Any consumer-defined subclass of a supported field (e.g. a project-local `class TrimmedCharField(models.CharField)`, or third-party packages like `django-encrypted-fields` / `django-money` field subclasses that ultimately are still char/decimal columns) will raise `ConfigurationError("Unsupported Django field type ...")` even though the column maps cleanly to the parent's scalar. This is a correctness/API-contract issue: subclassing is the normal Django extension path, and Django's own `SlugField`/`EmailField`/`URLField` happen to be listed explicitly here precisely because the lookup is exact. The recommended change is to walk `type(field).__mro__` and return the first hit (or invert via `isinstance` against the map keys ordered by MRO specificity). Pair the change with a unit test that registers a `CharField` subclass and asserts it resolves to `str` (and, if `null`/`choices` are set, the same widening/enum path applies).

```django_strawberry_framework/types/converters.py:105:111
    py_type = SCALAR_MAP.get(type(field))
    if py_type is None:
        raise ConfigurationError(
            f"Unsupported Django field type {type(field).__name__!r} on "
            f"{field.model.__name__}.{field.name}. Add an entry to "
            "SCALAR_MAP or exclude this field via Meta.exclude.",
        )
```

## Medium:

### `convert_choices_to_enum` is a 69-line / 8-branch hotspot doing four jobs

The helper validates flat-vs-grouped form, validates non-empty, caches, computes the enum name, sanitises and collides member names, builds and decorates the `Enum`, and registers it. The control-flow hotspot surfaced by the static helper at line 141 means each of those jobs needs explicit per-branch coverage; today the public surface gives them only incidental coverage via `DjangoType` end-to-end paths. Calibration carried forward from optimizer/walker.py: branchy helpers with multiple independent failure modes need *named* behavioural tests per branch (empty-choices, grouped-choices, cache-hit, name-collision, integer-choices producing `MEMBER_<digit>`, keyword-collision producing leading underscore, sibling type after first wins). The structural recommendation is to split the helper into `_validate_choices`, `_build_members`, and a thin `convert_choices_to_enum` orchestrator; that also makes the collision-aggregation branch reachable without standing up a full type.

```django_strawberry_framework/types/converters.py:141:209
def convert_choices_to_enum(field: models.Field, type_name: str) -> type[Enum]:
    ...
    choices = list(field.choices or [])
    ...
    for _value, label in choices:
        if isinstance(label, (list, tuple)):
            ...
    cached = registry.get_enum(field.model, field.name)
    ...
    enum_name = f"{type_name}{pascal_case(field.name)}Enum"
    ...
    for value, _label in choices:
        member = _sanitize_member_name(value)
        if member in members:
            collisions.setdefault(member, [members[member]]).append(value)
        ...
    if collisions:
        ...
    enum_cls = Enum(enum_name, members)
    enum_cls = strawberry.enum(enum_cls)
    registry.register_enum(field.model, field.name, enum_cls)
```

### Enum cache key ignores `type_name`, so cross-type members can clash silently

`registry.get_enum(field.model, field.name)` caches by `(model, field_name)`. The docstring acknowledges this and says "the first `DjangoType` to read a given `(model, field_name)` wins the enum's GraphQL name; sibling types pointing at the same column receive the cached enum unchanged." That is a deliberate design call, but the enum *name* is computed from `type_name` (`f"{type_name}{pascal_case(field.name)}Enum"`), so the GraphQL surface depends on import order. If `ItemType` is imported first you get `ItemStatusEnum`; if `ItemAdminType` is imported first you get `ItemAdminStatusEnum` and every consumer of `Item` thereafter receives that name. This is an ordering-dependent schema name with no enforcement. Either tighten the cache key to `(model, field_name, type_name)` (which costs an enum per consumer type), or strip `type_name` from the name (`f"{model.__name__}{pascal_case(field.name)}Enum"`) so the cache key and the schema name are derived from the same inputs. Option B matches the documented "first writer wins" intent. Pair the fix with a test exercising two `DjangoType`s referencing the same choice column and asserting a stable schema name regardless of import order.

```django_strawberry_framework/types/converters.py:185:209
    cached = registry.get_enum(field.model, field.name)
    if cached is not None:
        return cached

    enum_name = f"{type_name}{pascal_case(field.name)}Enum"
    ...
    registry.register_enum(field.model, field.name, enum_cls)
    return enum_cls
```

### `resolved_relation_annotation` uses `getattr(field, "null", False)` while every other branch trusts `field.null`

The reflective `getattr` shape-guard implies callers may pass relation-like objects that are not Django fields. Either that is part of the documented contract (then `convert_relation`'s `field.related_model` access needs the same guard, and the module docstring should say so), or it is defensive dead code (then drop it for `field.null` and match the rest of the module). This is the same calibration recorded for `field_meta.py` (shape-guard asymmetry between sibling helpers): pick one contract and enforce it consistently. Walker memory carry-forward: per-shape unit coverage of forward FK with `null=True` vs `null=False`, reverse O2O regardless of `null`, and forward O2O with `null=True` should each be named tests so the contract is pinned.

```django_strawberry_framework/types/converters.py:212:219
def resolved_relation_annotation(field: models.Field, target_type: type) -> Any:
    """Return the concrete annotation for ``field`` pointing at ``target_type``."""
    kind = relation_kind(field)
    if kind == "many":
        return list[target_type]
    if kind == "reverse_one_to_one" or getattr(field, "null", False):
        return target_type | None
    return target_type
```

## Low:

### `_NON_IDENT` regex collapses runs of non-identifier characters into a single `_`

`re.compile(r"\W+")` means `"foo--bar"` and `"foo__bar"` and `"foo  bar"` all collide on the sanitised member `"foo_bar"`. The collision-detection branch will catch the clash and raise, which is fine, but a Low-tier polish would be to either document this in the `_sanitize_member_name` docstring or switch to single-character replacement so values that differ by run-length keep distinct sanitised names. Defer to consumer feedback.

```django_strawberry_framework/types/converters.py:119:138
_NON_IDENT = re.compile(r"\W+")


def _sanitize_member_name(value: Any) -> str:
    ...
    sanitized = _NON_IDENT.sub("_", str(value))
    if not sanitized or sanitized[0].isdigit():
        sanitized = f"MEMBER_{sanitized}"
    if keyword.iskeyword(sanitized):
        sanitized = f"_{sanitized}"
    return sanitized
```

### `list(field.choices or [])` repeats the `or {}` / `or ()` defensive-coerce pattern flagged across `conf.py`, `extension.py`, `_context.py`, `plans.py`, `walker.py`, and `base.py`

Carry-forward calibration: this is now a package-wide stance question, not a per-file Low. Recording here for the folder/project pass; the local code reads fine.

```django_strawberry_framework/types/converters.py:162:162
    choices = list(field.choices or [])
```

### Three `TODO(future):` blocks (BigInt / ArrayField / JSON+HStore) have no anchored spec or slice name

`AGENTS.md` requires future-slice anchors to name the active design doc and the slice. These three are open-ended "someone will do this eventually" markers. Either downgrade the wording to a module-level note ("Postgres-specific column types and 64-bit ints are out of scope for the 0.0.x line; see SCALAR_MAP additions") or attach the spec name when one exists.

```django_strawberry_framework/types/converters.py:32:47
# TODO(future): define and export a ``BigInt`` Strawberry scalar so
...
# TODO(future): handle ``ArrayField`` -> ``list[inner_type]`` by
...
# TODO(future): handle ``JSONField`` and ``HStoreField`` via Strawberry's
```

### Error message at line 204 has a double-space before "Rename"

Minor copy polish; either flagged here for the comment pass or rolled into a logic-fix diff.

```django_strawberry_framework/types/converters.py:202:205
        raise ConfigurationError(
            f"{field.model.__name__}.{field.name} choices sanitize to the same enum member: "
            f"{details}.  Rename one side or split into separate fields.",
        )
```

## What looks solid

- Module structure: scalar half and relation half clearly separated, docstrings document the contract, `SCALAR_MAP` is dense and readable.
- Null widening order (choices first, then `T | None`) is deliberate and documented at the point it matters.
- `PendingRelationAnnotation` handoff with the docstring caveat "callers must record a `PendingRelation`" is the right shape for a two-phase registration model.
- The grouped-choices check correctly detects on `label`, not `value`, and the inline comment explains the load-bearing distinction.
- The static helper was run; no repeated string literals surfaced, only one ORM marker (`_meta` in a docstring) and three `getattr`/`isinstance`/`list` reflective calls, each justified.

---

### Summary:

One High (exact-type `SCALAR_MAP` lookup breaks consumer field subclasses), three Mediums (branchy `convert_choices_to_enum` lacks per-branch named tests; enum name depends on first-importer `type_name` while cache key does not; `resolved_relation_annotation` shape-guard asymmetric with the rest of the module). Lows are sanitisation-regex collapse behaviour, recurring `or []` defensive coerce (package-wide stance question), three unanchored future-TODO blocks, and a stray double-space in an error message. Folder-pass follow-ups: confirm `relation_kind` contract aligns with `resolved_relation_annotation`'s `getattr` guard; verify `registry.register_enum`/`get_enum` signature can accept the `(model, field_name, type_name)` triple if Medium #2 is taken; cross-check that `PendingRelationAnnotation` callers in `types/base.py` / `types/relations.py` always record a `PendingRelation`.

## Verification

PASS — 2026-05-11.

- High (exact-type SCALAR_MAP lookup): addressed. `convert_scalar` now walks `type(field).__mro__` and returns the first hit, falling through to the existing `ConfigurationError` only when no ancestor is in `SCALAR_MAP`. Inline comment cites the consumer-subclass extension path as the rationale.
- High test coverage: three new tests in `tests/types/test_converters.py` pin the fix — (1) `CharField` subclass resolves to `str`, (2) `null=True` widening still flows through the MRO-resolved scalar (`str | None`), (3) unsupported field (no SCALAR_MAP ancestor besides `object`) still raises `ConfigurationError`. Negative test guards against the MRO walk silently swallowing the unsupported case.
- Mediums and Lows: all explicitly routed to the folder/project pass or framed as calibration in the artifact body; no source changes expected this cycle. Contract-sanctioned deferral.
- Validation: `uv run pytest tests/types/test_converters.py -q --no-cov` → 12 passed.
