# Rationale: spec-017 — Deferred scalar conversions (reasons and rejected alternatives)

Companion to [`spec-017-deferred_scalars-0_0_6.md`][spec-017]. The spec states the contract; this file records why each Decision is shaped the way it is and which alternatives it rejected.

## Decision 1 — `BigInt` wire format and target fields

- **Decimal string on the wire.** GraphQL's `Int` is signed 32-bit, so an `int`-annotated value past `2**31 - 1` fails with `Int cannot represent non 32-bit signed integer value` before it reaches a client; JavaScript's 53-bit precision limit is the secondary reason. A decimal string survives both.
- **`parse_value=int` rejected.** `int(True) == 1`, `int(False) == 0` and `int(1.9) == 1`; the last is a silent truncation. The parser therefore checks `bool` before `int` (`bool` subclasses `int`) and rejects `float` outright.
- **`serialize=str` rejected.** It stringifies `True`, `1.9`, `Decimal(...)` and arbitrary objects, so a schema could emit values its own parser rejects. Parser and serializer are strict symmetrically because `BigInt` is a public scalar.
- **A permissive regex or plain `int(str)` rejected.** The regex `^(0|-?[1-9][0-9]*)$` is deliberately narrower than `int(str)`: `"1_000"` (PEP 515), `"+1"`, `"01"`, `"-0"` and Unicode decimal digits raise. Predictability over leniency.
- **Subclass normalization.** `int.__int__`, `str.__str__` and `int.__repr__` read the base slots, so a hostile `int` / `str` subclass can neither change the accepted value nor replace the scalar's error contract; error text goes through `_safe_arg_repr` / `_safe_type_name` for the same reason.
- **Int64 range enforcement rejected.** `BigInt` is arbitrary-precision; a hard 64-bit cap is a separate concern a consumer can enforce in a resolver or `clean`. A `BigInt64` variant stays out of scope.
- **`BigAutoField` stays `int`.** PK wire-format stability; the consumer recourse for a PK past `2**31` is the annotation override of `DONE-019-0.0.6`.

## Decision 2 — `ArrayField` dimensionality cap and outer-`choices` rejection

- **Multi-dimensional `ArrayField` rejected as scope.** A nested array raises `ConfigurationError`.
- **Outer `choices` rejected, not ignored.** Outer-array `choices` have no unambiguous GraphQL shape; loud over silent. Element-level enums come from `choices` on `base_field`, which the recursive `convert_scalar` call handles.
- **The recursion is left `force_nullable`-unset.** `Meta.nullable_overrides` / `Meta.required_overrides` describe the outer column; threading the override into `base_field` would silently change element nullability.
- **Guarded metadata readers.** `_field_label` / `_field_has_choices` keep a hostile field descriptor's exception from escaping as anything other than `ConfigurationError`.

## Decision 3 — `JSONField` target type

`strawberry.scalars.JSON` is Strawberry's own arbitrary-JSON scalar; no package scalar is needed.

## Decision 4 — soft import via module-level sentinels

- **No postgres driver in dev dependencies.** The package must import cleanly without one, so the postgres-only classes are soft-imported into sentinels.
- **Not registered in `SCALAR_MAP`.** The sentinel branches run *before* the `scalar_for_field` MRO walk, so a `models.Field` test double cannot match a parent entry by accident.
- **One optional-import owner.** `django_strawberry_framework/utils/imports.py::import_attr_if_importable` is stricter than a hand-rolled `try` / `except ImportError`: an importable-but-incomplete `django.contrib.postgres.fields` raises `AttributeError` instead of degrading to `None`, and its branches are tested once, at the helper.

## Decision 5 — `HStoreField` wire shape

- **`JSON`, not `dict[str, str | None]`.** Strawberry rejects the dict annotation.
- **No dedicated `HStore` scalar.** Rejected as scope; `HStoreField` and `JSONField` are therefore indistinguishable at the GraphQL type level, an accepted cost.
- **Outer `choices` rejected.** Consistent with Decision 2; Django accepts `choices` on an `HStoreField` for form widgets only and never enforces it at the column, so honoring it silently would mislead.

## Decision 6 — `BigInt` public-export status and registration contract

- **Off Strawberry's deprecated path.** Passing a class or `NewType` to `strawberry.scalar(...)` emits a `DeprecationWarning` that would reach every consumer importing the package and break imports under `-W error::DeprecationWarning`. A bare `NewType` plus a `name=`-only `ScalarDefinition` registered through `strawberry_config()` emits nothing, so nothing needs suppressing.
- **Inert without the config.** A `BigInt` annotation in a schema built without `config=strawberry_config()` fails with `Unexpected type '...BigInt'` rather than silently resolving to something else.
- **No `extra_extensions=` on the factory.** Strawberry extensions belong to `strawberry.Schema(..., extensions=[...])`, not to `StrawberryConfig`.

## Decision 7 — test strategy

- **Subprocess, not `importlib.reload`, for the warning-free import.** `importlib.reload(django_strawberry_framework)` does not reload submodules, so `scalars.py`'s definition line never re-executes and a reload-based test observes zero warnings whether or not the definition is on the deprecated path: it cannot fail.
- **Fake field doubles over a postgres driver.** `_FakeArrayField` / `_FakeHStoreField` plus a monkey-patched sentinel reach the branches on SQLite; the real-class tests run only where `django.contrib.postgres.fields` imports.
- **`managed = False`.** The synthetic models have no migrated table; the flag records that and forces direct instantiation instead of `objects.create()`.
- **No `isinstance` assertion on Strawberry's scalar wrapper in the import smoke test.** The wrapper type is an undocumented Strawberry internal, and `BigInt` is a bare `NewType` anyway; schema-execution tests give the stronger signal.
- **Live tier first.** Every parse / serialize case a request can express is pinned over `/graphql/` against the `apps.scalars` specimens; the package tier keeps only Python-object inputs no request can carry.

## Decision 8 — `SCALAR_MAP` value type

`BigInt` and `strawberry.scalars.JSON` are `NewType`-backed, not plain `type`s, so the map's value type is a type form.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-017]: ../spec-017-deferred_scalars-0_0_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
