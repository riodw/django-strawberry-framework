# Review: `django_strawberry_framework/types/converters.py`

Status: verified

## DRY analysis

- Existing patterns reused: scalar conversion is centralized behind `SCALAR_MAP` and one `convert_scalar` MRO walk in `django_strawberry_framework/types/converters.py:49-126`; choice enum reuse goes through the shared registry cache in `django_strawberry_framework/types/converters.py:195-218` and `django_strawberry_framework/registry.py:44-102`; generated enum type names already reuse `pascal_case` from `django_strawberry_framework/utils/strings.py:46-60`. Relation annotation shape is shared by collection and finalization through `resolved_relation_annotation` in `django_strawberry_framework/types/base.py:609-614` and `django_strawberry_framework/types/finalizer.py:79-84`.
- New helpers a fix might justify: a GraphQL enum member-name normalizer with the single responsibility "turn an arbitrary Django choice value into a GraphQL-safe, non-reserved enum value name, or raise `ConfigurationError` when deterministic sanitization collides." It would serve `_sanitize_member_name` immediately and future `BACKLOG-007` explicit choice-enum naming if explicit enum member names are added.
- Duplication risk in the current file: relation cardinality/nullability is still re-derived in `resolved_relation_annotation` via `relation_kind(field)` plus raw `getattr(field, "null", False)` in `django_strawberry_framework/types/converters.py:222-234`, while `FieldMeta` documents itself as the canonical SSoT in `django_strawberry_framework/optimizer/field_meta.py:1-17` and `KANBAN.md:885-910` tracks the three anchored reader sites. Repeated string literals: none surfaced by `scripts/review_inspect.py`.

## High:

### Choice enum member sanitization is not GraphQL-safe

`_sanitize_member_name` only targets Python identifiers. That still lets valid Django choice values become Strawberry enum members that GraphQL rejects later during schema construction: non-ASCII word characters survive `\W+`, GraphQL-reserved enum values `"true"`, `"false"`, and `"null"` are not rewritten, and values that sanitize to names beginning with `"__"` hit GraphQL's introspection-name ban. This is a consumer-facing crash path for ordinary `choices` data even though the converter is supposed to generate Strawberry-compatible enums. Make the sanitizer enforce GraphQL enum-value constraints, keep collision detection after final sanitization, and add tests that build a small schema for reserved/non-ASCII/double-underscore choice values rather than only checking Python identifier validity.

```django_strawberry_framework/types/converters.py:129:148
_NON_IDENT = re.compile(r"\W+")


def _sanitize_member_name(value: Any) -> str:
    """Produce a valid Python identifier from a Django choice value.
...
    sanitized = _NON_IDENT.sub("_", str(value))
    if not sanitized or sanitized[0].isdigit():
        sanitized = f"MEMBER_{sanitized}"
    if keyword.iskeyword(sanitized):
        sanitized = f"_{sanitized}"
    return sanitized
```

```django_strawberry_framework/types/converters.py:199:218
    enum_name = f"{type_name}{pascal_case(field.name)}Enum"
    members: dict[str, Any] = {}
    collisions: dict[str, list[Any]] = {}
    for value, _label in choices:
        member = _sanitize_member_name(value)
...
    enum_cls = Enum(enum_name, members)  # type: ignore[arg-type]
    enum_cls = strawberry.enum(enum_cls)
    registry.register_enum(field.model, field.name, enum_cls)
    return enum_cls
```

## Medium:

None.

## Low:

### Converter docstrings still describe pre-fix Python-only naming and exact-type lookup

The `convert_scalar` docstring says the algorithm looks up `type(field)` in `SCALAR_MAP`, but the implementation now deliberately walks the field MRO so supported Django field subclasses work. `_sanitize_member_name` says it produces a valid Python identifier, which is narrower than the needed Strawberry/GraphQL enum-value contract. Update these docstrings after the logic fix so the public converter behavior and sanitizer constraints match the implementation.

```django_strawberry_framework/types/converters.py:80:103
    """Map a Django scalar field to a Python / Strawberry type.

    Algorithm:

    1. Look up ``type(field)`` in ``SCALAR_MAP``; raise ``ConfigurationError``
       if unsupported.
```

```django_strawberry_framework/types/converters.py:132:142
def _sanitize_member_name(value: Any) -> str:
    """Produce a valid Python identifier from a Django choice value.
...
    collides with a Python keyword. Sanitization is a function of the raw
    value, not the label, so schema member names stay stable when consumers
    edit human-readable labels.
```

## What looks solid

- The mandatory static helper was run for this types file: `python scripts/review_inspect.py django_strawberry_framework/types/converters.py --output-dir docs/review/shadow --stdout`.
- Unsupported scalar field types raise `ConfigurationError` before annotation synthesis can leak a raw lookup error in `django_strawberry_framework/types/converters.py:116-121`.
- Supported Django field subclasses resolve through the MRO walk in `django_strawberry_framework/types/converters.py:105-115`, and current coverage pins both non-null and nullable subclass paths in `tests/types/test_converters.py:280-343`.
- Choice enum reuse is keyed by `(model, field_name)` and does not recreate enum classes after the first successful conversion in `django_strawberry_framework/types/converters.py:195-218`.
- Grouped choices, empty choices, and sanitized-name collisions already raise typed `ConfigurationError` errors in `django_strawberry_framework/types/converters.py:172-193` and `django_strawberry_framework/types/converters.py:200-215`.
- The `TODO(spec-fieldmeta-ssot)` anchor in `resolved_relation_annotation` matches the accepted `types/base.py` and optimizer folder-pass follow-up rather than being a local one-off defect.

### Summary

`types/converters.py` is generally well-contained: scalar mapping, choice enum generation, registry reuse, and pending relation annotation all sit at the right boundary. The review-worthy defect is that the choice-value sanitizer stops at Python identifier rules even though the generated enum must satisfy GraphQL enum-value rules before a consumer schema can build.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/types/converters.py` — changed choice member sanitization to use ASCII-only identifier characters, then guard GraphQL-reserved enum values (`true` / `false` / `null`, case-insensitive) and names beginning with `__` before collision detection.
- `tests/types/test_converters.py` — added schema-building coverage for reserved, non-ASCII, and double-underscore choice values plus a post-GraphQL-sanitization collision regression.

### Tests added or updated

- `tests/types/test_converters.py::test_choice_enum_with_graphql_reserved_and_non_ascii_values_builds_schema` — proves generated enum values for reserved literals, non-ASCII input, and `__` prefixes can build and execute in a Strawberry schema.
- `tests/types/test_converters.py::test_convert_choices_to_enum_raises_on_graphql_safe_name_collision` — proves collision detection runs after the final GraphQL-safe rewrite.

### Validation run

- `uv run ruff format .` — passed, 92 files unchanged.
- `uv run ruff check --fix .` — passed.
- `uv run pytest tests/types/test_converters.py` — assertions passed (`14 passed`) but the focused run failed the expected repo-wide coverage gate (`total of 40 is less than fail-under=100`).
- `uv run pytest tests/types/test_converters.py --no-cov` — passed (`14 passed`, with existing Django model re-registration warnings from local test model definitions).

### Notes for Worker 3

- Static helper output was generated under `docs/review/shadow/django_strawberry_framework__types__converters.*`; artifact line references use original source-file line numbers.
- Low docstring finding intentionally left for the comment/docstring pass after logic verification.

---

## Verification (Worker 3)

### Logic verification outcome

High accepted. `_sanitize_member_name` now normalizes with `re.ASCII`, prefixes digit/empty names, keeps Python keyword handling, and then rewrites GraphQL-reserved enum values (`true`, `false`, `null`, case-insensitive) plus names beginning with `__`. `convert_choices_to_enum` still builds the `members` dict and detects collisions after `_sanitize_member_name`, so post-GraphQL-safe collisions such as `"true"` vs `"MEMBER_true"` raise `ConfigurationError` before schema construction.

Low not yet addressed. The logic is correct, but the comment/docstring lifecycle remains open: `convert_scalar` still documents exact `type(field)` lookup even though the implementation walks the MRO, and `_sanitize_member_name` still describes only a Python-identifier contract instead of the final GraphQL enum-value constraints.

### DRY findings disposition

Accepted for logic. The fix kept the normalization rules centralized in `_sanitize_member_name` and left `convert_choices_to_enum` as the sole collision-detection point after final sanitization. The existing `resolved_relation_annotation` / `FieldMeta` SSoT note remains a carried-forward TODO, not a local blocker for this enum-sanitization fix.

### Temp test verification

- Temp test files used: none.
- Disposition: not needed; Worker 2 promoted the relevant reserved/non-ASCII/`__` and final-name collision coverage directly into `tests/types/test_converters.py`.

### Verification outcome

Logic accepted; awaiting comment pass. Top-level `Status:` remains `fix-implemented`, and the checklist item remains unchecked until comments/docstrings and changelog disposition are complete.

Validation passed:

- `uv run pytest tests/types/test_converters.py --no-cov` — passed (`14 passed`, with existing Django model re-registration warnings).
- `uv run ruff format --check django_strawberry_framework/types/converters.py tests/types/test_converters.py` — passed.
- `uv run ruff check django_strawberry_framework/types/converters.py tests/types/test_converters.py` — passed.

---

## Comment/docstring pass

Completed. Updated `convert_scalar` to document the MRO walk through `type(field).__mro__` instead of exact `type(field)` lookup, including the unsupported-field `ConfigurationError` path. Updated `_sanitize_member_name` to describe the final Strawberry / GraphQL enum-value contract: ASCII-safe identifier normalization, Python keyword handling, reserved enum values, and `__` introspection-name prefix handling.

Validation:

- `uv run ruff format django_strawberry_framework/types/converters.py` — pass.
- `uv run ruff check django_strawberry_framework/types/converters.py` — pass.

---

## Changelog disposition

Warranted. This was a High, user-visible bug fix: consumer Django choice values that were valid enough for Python enum member creation could still generate Strawberry enums rejected by GraphQL schema construction (`true` / `false` / `null`, non-ASCII values, or `__`-prefixed names). The fix changes generated enum member names for those edge cases and prevents a normal schema-build crash path.

No `CHANGELOG.md` edit was made because the active review plan and maintainer instructions did not explicitly authorize editing the changelog.

---

## Verification (Worker 3, pass 2)

### Comment/docstring verification outcome

Comments accepted. `convert_scalar` now documents the final MRO-based scalar lookup and unsupported-field `ConfigurationError` path instead of the stale exact `type(field)` lookup. `_sanitize_member_name` now documents the final Strawberry / GraphQL enum-value contract, including ASCII-safe normalization, Python keyword handling, case-insensitive reserved enum values, and `__` introspection-name prefix handling.

### Verification outcome

Comments accepted; awaiting changelog disposition. Top-level `Status:` remains `fix-implemented`, and the checklist item remains unchecked until Worker 2 records whether `CHANGELOG.md` should be updated or intentionally left unchanged.

---

## Verification (Worker 3, pass 3)

### Changelog verification outcome

Changelog disposition accepted. The bug fix is user-visible and release-note-worthy because invalid generated enum member names could crash Strawberry schema construction for ordinary Django choice values. `CHANGELOG.md` was intentionally left unchanged because maintainer instructions do not authorize changelog edits during this cycle.

### Final verification outcome

Logic, DRY disposition, comments/docstrings, validation, and changelog handling are accepted. No temp tests were used; the schema-build and final-name collision coverage is permanent in `tests/types/test_converters.py`. Cycle accepted; verified.

Validation passed:

- `uv run pytest tests/types/test_converters.py --no-cov` — passed (`14 passed`, with two existing Django model re-registration warnings).
- `uv run ruff format --check django_strawberry_framework/types/converters.py tests/types/test_converters.py` — passed.
- `uv run ruff check django_strawberry_framework/types/converters.py tests/types/test_converters.py` — passed.

---

## Iteration log

Each Worker 2 re-pass appends a `## Fix report (Worker 2, pass <N>)` section here. Each Worker 3 re-verification appends a `## Verification (Worker 3, pass <N>)` section here. Do not edit prior entries; append.
