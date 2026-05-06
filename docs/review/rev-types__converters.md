# Review: `django_strawberry_framework/types/converters.py`

## High:

None.

## Medium:

### `_sanitize_member_name` collisions silently drop enum members

`convert_choices_to_enum` builds the enum via:

```
members = {_sanitize_member_name(value): value for value, _label in choices}
enum_cls = Enum(enum_name, members)
```

If two distinct choice values sanitize to the same Python identifier (e.g., `"a-b"` and `"a_b"` both become `"a_b"`; or `"1"` and `"_1"` both become `"MEMBER_1"`), the dict comprehension silently keeps the *last* one and drops the earlier value. The generated GraphQL enum then has fewer members than the source `choices` declared, and a query selecting the dropped value returns a coercion error at runtime — long after schema build.

Recommended: detect collisions while building the dict and raise `ConfigurationError` with the model, the field, the colliding values, and the shared sanitized name. The check is a four-line addition; tests should pin both a value-vs-value collision and a member-vs-keyword-prefix collision (e.g., `"if"` collides with `"_if"` if a sibling raw value is `"_if"`).

```django_strawberry_framework/types/converters.py:187:189
enum_name = f"{type_name}{pascal_case(field.name)}Enum"
members = {_sanitize_member_name(value): value for value, _label in choices}
enum_cls = Enum(enum_name, members)  # type: ignore[arg-type]
```

## Low:

### `field.choices or []` misses Django's `Choices`-class form before iteration

`convert_choices_to_enum` reads `field.choices or []` once. Django's `IntegerChoices` / `TextChoices` produce `field.choices` as a list of `(value, label)` tuples already, so this is correct. But the current code path tests `isinstance(label, (list, tuple))` to detect grouped form, which only fires when the consumer passes Django's grouped form `(group_label, [(value, label), ...])`. Both behaviours are honored; the fragility is purely defensive — if Django ever surfaces a third shape (e.g., `Choices` enum subclass instances directly), this code would attempt to iterate it and likely fail with an opaque error. Comment polish — defer.

```django_strawberry_framework/types/converters.py:160:181
choices = list(field.choices or [])
if not choices:
    raise ConfigurationError(...)
for _value, label in choices:
    if isinstance(label, (list, tuple)):
        raise ConfigurationError(...)
```

### `convert_relation` does not surface a hint about `lazy_ref` for cycles

When a `DjangoType` is not yet registered, the error message tells the consumer to declare related types in dependency order, but does not mention that `registry.lazy_ref` is reserved for the future definition-order-independence slice. Consumers debugging a registration ordering issue may not realise the limitation is tracked work. One-line addition to the error message ("Definition-order independence is tracked as future work; see `registry.lazy_ref`."). Comment polish — defer.

```django_strawberry_framework/types/converters.py:229:234
raise ConfigurationError(
    f"DjangoType for {target_model.__name__} is not yet registered. "
    "Declare it before any DjangoType that references it via FK / OneToOne / M2M, "
    "or before any DjangoType whose model is referenced by it via a reverse rel.",
)
```

### Module-level `SCALAR_MAP` is documented as a closed dict but is mutable

`SCALAR_MAP` is a plain `dict` at module level, so a consumer can monkey-patch it (`SCALAR_MAP[CustomField] = MyType`). The docstring above the map and the field-by-field TODOs read as if the map is a closed contract, but Python does not enforce that. Consider freezing via `types.MappingProxyType(SCALAR_MAP)` exposed under a different name and keep the mutable internal dict private. Trade-off: makes future plug-in-style extensibility harder. Note for future spec only.

```django_strawberry_framework/types/converters.py:47:74
SCALAR_MAP: dict[type[models.Field], type] = {
    models.AutoField: int,
    ...
}
```

## What looks solid

- Two clearly-separated halves: scalar conversion (with `SCALAR_MAP` lookup, choice-enum branch, and null widening) and relation conversion (with the documented cardinality table).
- Order in `convert_scalar` is correct and explicitly justified: choices replaces `py_type` *before* null widening so nullable choice fields end up as `EnumType | None`, not collapsed.
- Future-spec gaps (`BigIntegerField` → `BigInt` scalar, `ArrayField`, `JSONField` / `HStoreField`) are anchored as `# TODO(future)` comments at the top of the file with the exact build recipe — that matches AGENTS.md's deferred-work pattern.
- `_sanitize_member_name` is conservative and stable: sanitizes from the raw value (not the human label), so label edits do not churn schema member names. Keyword collision is handled via the underscore-prefix path.
- `convert_choices_to_enum` uses the registry's enum cache to share enum classes across `DjangoType`s pointing at the same column, which the registry review just hardened with a same-class-is-idempotent guard.
- `convert_relation` cardinality table documents every shape (forward FK, forward OneToOne, reverse OneToOne, reverse FK, M2M) and the implementation matches the table line-for-line. Reverse OneToOne is conceptually nullable and the implementation reflects that with the `is_reverse and field.one_to_one` branch.
- Error messages name the model, the field, and the offending value so consumers can navigate from a stack trace back to the line in their `Meta`.
- 32% line coverage in this file's own tests; full coverage via integration tests across the suite.

---

### Summary:

The file is the package's type-system bridge between Django and Strawberry, and the two halves are tight and well-documented. The one Medium item is a real silent-data-loss bug: when two distinct choice values sanitize to the same Python identifier, the enum-builder dict drops the earlier value with no warning. Add a collision check and a test pinning both shapes (value-vs-value and member-vs-keyword-prefix). Low items are defensive polish on choice-shape detection, registration-error hint text, and the `SCALAR_MAP` mutability note.

---

### Worker 3 verification

- Medium fix: `convert_choices_to_enum` now builds the member dict with explicit collision detection. Each sanitized name is checked against the running dict; collisions accumulate the original raw values and a single `ConfigurationError` enumerates every member that received conflicting values, naming the model, the field, and the offending raw values.
- Test added: `test_convert_choices_to_enum_raises_on_sanitized_member_collision` in `tests/types/test_converters.py` constructs a value-vs-value collision (`"a-b"` vs `"a_b"`) and pins the new error message.
- Low items: not addressed in this cycle. The `field.choices` shape detection, the registration-error hint, and the `SCALAR_MAP` immutability note are all monitor-only follow-ups; none was a priority next to the silent-data-loss Medium.
- Validation: `uv run ruff format` and `uv run ruff check` clean; `uv run pytest -q` -> 353 passed, 4 skipped, 100% coverage (one new test in `tests/types/test_converters.py`).
- CHANGELOG: not updated. Defensive guard for a previously-silent corruption path; AGENTS.md forbids changelog edits without explicit instruction.
- Scope: changes confined to `django_strawberry_framework/types/converters.py` and `tests/types/test_converters.py`.
- Checkbox in `docs/review/review-0_0_3.md`: marked `- [x]`.
