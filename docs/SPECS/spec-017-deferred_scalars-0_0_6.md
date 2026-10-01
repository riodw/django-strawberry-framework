# Spec: Deferred scalar conversions

Target release: `0.0.6`.
Status: shipped in `0.0.6`.
Owner: package maintainer.
Predecessors: [`docs/GLOSSARY.md`][glossary] (entries [Scalar field conversion][glossary-scalar-field-conversion], [Specialized scalar conversions][glossary-specialized-scalar-conversions], [`BigInt` scalar][glossary-bigint-scalar]), [`KANBAN.md`][kanban] card `DONE-017-0.0.6`.
Card line: ["Add `BigInt` scalar with string serialization and `int` parsing. Add `JSONField` mapping to Strawberry JSON. Add `HStoreField` where available. Add `ArrayField` recursion through `field.base_field`. Use synthetic unmanaged test models where fakeshop does not naturally exercise the fields. Keep coverage at 100%."][kanban]

The reasons behind each Decision and the alternatives it rejected live in [`spec-017-deferred_scalars-0_0_6-rationale.md`][spec-017-rationale]. This file states the contract.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first — they anchor the vocabulary used throughout the spec:

- [`DjangoType`][glossary-djangotype] — the base class whose field-conversion table this spec extends.
- [Scalar field conversion][glossary-scalar-field-conversion] — the shipped scalar coverage and the **subclass MRO walk** that the spec's [Edge cases](#edge-cases-and-constraints) section relies on.
- [Specialized scalar conversions][glossary-specialized-scalar-conversions] — the umbrella entry for the mappings this spec owns.
- [`BigInt` scalar][glossary-bigint-scalar] — the public scalar this spec defines.
- [`ConfigurationError`][glossary-configurationerror] — raised for unsupported fields, nested `ArrayField`, and outer `choices` on `ArrayField`.
- [`Meta.exclude`][glossary-metaexclude] — consumer-side recourse named in the existing unsupported-field error message.
- [`finalize_django_types`][glossary-finalize-django-types] — where the annotations land. The [Schema test fixture pattern](#decision-7--test-strategy) requires every test that defines a synthetic `DjangoType` to call this.
- [Choice enum generation][glossary-choice-enum-generation] — `ArrayField(CharField(choices=...))` on the *base field* is the tested edge case; outer `choices` on `ArrayField` is rejected.
- [Scalar field override semantics][glossary-scalar-field-override-semantics] — the sibling `0.0.6` card (`DONE-019-0.0.6`). It supplies the consumer recourse for the `BigAutoField` mapping, which stays `int`.

Project conventions to follow:

- [`AGENTS.md`][agents] — test placement: a line a real fakeshop query reaches is pinned at the live `/graphql/` tier.
- [`CONTRIBUTING.md`][contributing] — 100% coverage gate; the single-sourced version.
- [`KANBAN.md`][kanban] — the `DONE-017-0.0.6` card.
- [`docs/TREE.md`][tree] — package and test layout.

## Slice checklist

Each top-level item maps to one commit in the [Implementation plan](#implementation-plan).

- [ ] Slice 1: `BigInt` scalar + 64-bit integer field mappings
  - [ ] `django_strawberry_framework/scalars.py` defines `_parse_bigint`, `_serialize_bigint`, `BigInt`, `_BIGINT_SCALAR_DEFINITION`, and `_PACKAGE_SCALAR_MAP` per [Decision 1](#decision-1--bigint-wire-format-and-target-fields). Importing `django_strawberry_framework` emits no Strawberry `DeprecationWarning`.
  - [ ] `django_strawberry_framework/__init__.py` re-exports `BigInt` and lists it in `__all__` beside the other root exports (`DjangoType`, [`DjangoOptimizerExtension`][glossary-djangooptimizerextension], [`OptimizerHint`][glossary-optimizerhint], `finalize_django_types`, `strawberry_config`, ...); `tests/base/test_init.py` pins the whole `__all__` tuple.
  - [ ] `SCALAR_MAP` maps `models.BigIntegerField: BigInt` and `models.PositiveBigIntegerField: BigInt`.
  - [ ] `SCALAR_MAP`'s declared value type admits scalar wrappers per [Decision 8](#decision-8--scalar_map-value-type-widening).
  - [ ] Package-tier scalar tests in `tests/test_scalars.py` (only what no GraphQL request can express):
    - Serializer:
      - [ ] `test_bigint_serialize_rejects_bool` — `True` and `False` both raise `TypeError`
      - [ ] `test_bigint_serialize_rejects_float` — `1.9`, `0.0` raise `TypeError`
      - [ ] `test_bigint_serialize_rejects_non_int_types` — `str`, `Decimal`, `None`, custom object all raise `TypeError`
      - [ ] `test_bigint_int_subclasses_are_normalized_before_serialization` — an `int` subclass with hostile `__int__` / `__repr__` / `__str__` parses to a plain `int` and serializes to its canonical decimal string
    - Parser:
      - [ ] `test_bigint_rejects_python_bool` — both `True` and `False`
      - [ ] `test_bigint_rejects_python_float` — `1.9`, `0.0`, `-1.0` (silent-truncation guard: `int(1.9) == 1` would otherwise slip through)
      - [ ] `test_bigint_rejects_none` — unit-level test. Strawberry strips `null` before calling `parse_value` for nullable input positions, so this code path is reachable only through direct calls. Tested for defense in depth so the parser's `None` rejection is not removed as "unreachable".
      - [ ] `test_bigint_rejection_messages_survive_hostile_values` — the `ValueError` text is built from `_safe_arg_repr` / `_safe_type_name`, so an unprintable value cannot replace the parser's error
    - Public-export smoke:
      - [ ] `test_bigint_is_importable_from_top_level` — `from django_strawberry_framework import BigInt`; assert `BigInt is not None`. **Type-shape assertions intentionally avoided**: Strawberry's scalar wrapper types are undocumented internals; the schema-execution tests catch any "BigInt isn't actually usable as a scalar" regression with stronger signal.
    - Warning-free import:
      - [ ] `test_package_import_does_not_emit_strawberry_deprecation_warning` — **subprocess-based** test running `python -W error::DeprecationWarning -c "import django_strawberry_framework"`, asserts `returncode == 0`. See [Decision 7](#decision-7--test-strategy) for the implementation pattern and why `importlib.reload` is *not* used.
  - [ ] Live `/graphql/` tests in `examples/fakeshop/test_query/test_scalars_api.py` (every parse / serialize case a request can express):
    - [ ] `test_scalar_specimen_introspects_bigint_scalar_for_both_fields` — `BigIntegerField` and `PositiveBigIntegerField` each introspect as `BigInt` in both the non-null and nullable shapes
    - [ ] `test_scalar_specimen_every_field_wire_format_over_http` — `BigInt` query results serialize as decimal strings past the JS safe-integer boundary
    - [ ] `test_scalar_specimen_bigint_negative_signed_round_trip` and `test_scalar_specimen_bigint_zero_serializes_as_string` — negative and zero values serialize as decimal strings
    - [ ] `test_scalar_specimen_by_signed_big_accepts_canonical_literals` — int-zero, string-zero, negative string, int64-min and int64-max arguments parse and serialize back as the same decimal string
    - [ ] `test_scalar_specimen_bigint_input_decimal_string_argument_over_http` and `test_scalar_specimen_bigint_input_int_literal_argument_over_http`
    - [ ] `test_filter_specimens_by_bigint_exact_accepts_decimal_string_literal`
    - [ ] `test_filter_specimens_by_bigint_exact_rejects_non_integer_literal` — the input parser rejects `bool` and `float` literals through the live schema path, for both the signed and unsigned `BigInt` fields
    - [ ] `test_filter_specimens_by_bigint_exact_rejects_malformed_decimal_string` — empty, whitespace-padded, non-decimal (`"abc"`, `"1.9"`, `"1e3"`, `"0x10"`), underscore-separated, leading-plus, Unicode-digit, leading-zero, and `"-0"` strings are each refused
    - [ ] `test_scalar_specimen_id_maps_big_auto_pk_to_int` — the `BigAutoField` pk stays `Int`
  - [ ] Package-tier converter tests in `tests/types/test_converters.py` (no fakeshop field reaches them):
    - [ ] `test_big_auto_field_still_maps_to_int`
    - [ ] `test_bigint_in_input_position_with_null_via_schema_execution`
    - [ ] `test_bigint_resolver_returning_bool_raises_via_schema_execution` — `_serialize_bigint` rejects a non-`int` resolver return value at the schema boundary
- [ ] Slice 2: `JSONField` mapping
  - [ ] `SCALAR_MAP` maps `models.JSONField: strawberry.scalars.JSON`
  - [ ] Tests at the live `/graphql/` tier in `examples/fakeshop/test_query/test_scalars_api.py`
    - [ ] `test_scalar_specimen_introspects_json_scalar_in_both_shapes` — `JSONField` introspects as `JSON` in both the non-null and nullable shapes
    - [ ] `test_scalar_specimen_every_field_wire_format_over_http` — a mixed-primitive dict (string, int, list, JSON `null`, nested bool) round-trips verbatim
- [ ] Slice 3: `ArrayField` recursion (sentinel-based)
  - [ ] Module-level sentinel `_ARRAY_FIELD_CLS`, soft-imported through the package's shared optional-import owner per [Decision 4](#decision-4--soft-import-via-module-level-sentinels)
  - [ ] `convert_scalar` branch guarded by `_ARRAY_FIELD_CLS is not None and isinstance(field, _ARRAY_FIELD_CLS)` per [Decision 2](#decision-2--arrayfield-dimensionality-cap-and-outer-choices-rejection)
  - [ ] Outer `choices` and nested `ArrayField` rejected with `ConfigurationError` per [Decision 2](#decision-2--arrayfield-dimensionality-cap-and-outer-choices-rejection)
  - [ ] Fake-field test double `_FakeArrayField(models.Field)` in `tests/types/test_converters.py` per [Decision 7](#decision-7--test-strategy); test models hosting it declare `class Meta: managed = False; app_label = "test_arrayfield"`.
  - [ ] Each `_FakeArrayField`-based test calls `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` *before* declaring the `DjangoType`. (See the [Schema test fixture pattern](#decision-7--test-strategy).)
  - [ ] Tests in `tests/types/test_converters.py`:
    - Soft-import branch coverage: owned by the shared helper's own tests (`tests/utils/test_imports.py`), not duplicated here — see [Decision 4](#decision-4--soft-import-via-module-level-sentinels).
    - Sentinel-branch coverage (via `_FakeArrayField`):
      - [ ] `test_array_field_of_int_maps_to_list_int_via_fake_sentinel`
      - [ ] `test_array_field_of_char_maps_to_list_str_via_fake_sentinel`
      - [ ] `test_array_field_nullable_inner_via_fake_sentinel`
      - [ ] `test_array_field_outer_nullable_via_fake_sentinel`
      - [ ] `test_array_field_multidim_rejected_via_fake_sentinel`
      - [ ] `test_array_field_choices_inner_via_fake_sentinel`
      - [ ] `test_array_field_outer_choices_rejected_via_fake_sentinel`
      - [ ] `test_array_field_base_field_unsupported_type_raises`
      - [ ] `test_array_field_sentinel_none_path`
  - [ ] Optional gated test: `test_real_array_field_compatible_with_strawberry` — `pytest.importorskip("django.contrib.postgres.fields")`; declares a `DjangoType` with `ArrayField(IntegerField())` on a `managed = False` model, calls `finalize_django_types()`, introspects the schema via `__type`, asserts the field type is `[Int!]!`. **Introspection navigation note:** GraphQL introspection returns a nested `kind / ofType` chain (`NON_NULL → LIST → NON_NULL → SCALAR { name: "Int" }` for `[Int!]!`); walk it explicitly rather than asserting on `field.type.name` (which is `None` for wrapping types).
- [ ] Slice 4: `HStoreField` conditional registration via sentinel + `strawberry.scalars.JSON` target
  - [ ] Module-level sentinel `_HSTORE_FIELD_CLS`, soft-imported through the package's shared optional-import owner per [Decision 4](#decision-4--soft-import-via-module-level-sentinels)
  - [ ] `convert_scalar` branch guarded by `_HSTORE_FIELD_CLS is not None and isinstance(field, _HSTORE_FIELD_CLS)` returning `strawberry.scalars.JSON` per [Decision 5](#decision-5--hstorefield-wire-shape)
  - [ ] Outer `choices` on `HStoreField` rejected with `ConfigurationError` per [Decision 5](#decision-5--hstorefield-wire-shape), consistent with the `ArrayField` outer-`choices` rejection in Decision 2
  - [ ] `HStoreField` is **not** in `SCALAR_MAP`
  - [ ] Fake-field test double `_FakeHStoreField(models.Field)` in `tests/types/test_converters.py`; test models hosting it declare `class Meta: managed = False; app_label = "test_hstorefield"`
  - [ ] Each `_FakeHStoreField`-based test calls `monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)` *before* declaring the `DjangoType`.
  - [ ] Tests in `tests/types/test_converters.py`:
    - Soft-import branch coverage: owned by the shared helper's own tests (`tests/utils/test_imports.py`), not duplicated here — see [Decision 4](#decision-4--soft-import-via-module-level-sentinels).
    - Sentinel-branch coverage (via `_FakeHStoreField`):
      - [ ] `test_hstore_field_maps_to_json_scalar_via_fake_sentinel`
      - [ ] `test_hstore_field_nullable_via_fake_sentinel`
      - [ ] `test_hstore_field_resolver_dict_serializes_via_schema_execution` — resolver returns a hand-built `dict` (no DB persistence; SQLite cannot store HStore values); test name clarifies this is a serializer-level test
      - [ ] `test_hstore_field_resolver_dict_with_none_value_via_schema_execution` — resolver returns `{"k1": "v", "k2": None}`; pins that `JSON` accepts `None` values inside the dict (mirrors `HStoreField`'s native `dict[str, str | None]` shape)
      - [ ] `test_hstore_field_outer_choices_rejected_via_fake_sentinel` — declares `_FakeHStoreField(choices=[("a", "A")])`; asserts `ConfigurationError` is raised at type creation
      - [ ] `test_hstore_field_sentinel_none_path` — monkey-patch sentinel to `None`
  - [ ] Optional gated test: `test_real_hstore_field_compatible_with_strawberry` — `pytest.importorskip("django.contrib.postgres.fields")`; declares a `DjangoType` with `HStoreField()` on a `managed = False` model, calls `finalize_django_types()`, introspects the schema, asserts the field type is `JSON!` (introspection chain: `NON_NULL → SCALAR { name: "JSON" }`; walk the `kind / ofType` structure explicitly), **and** exercises a resolver returning `{"k1": "v", "k2": None}` via `schema.execute_sync`, asserting the dict shape including the `None` value is preserved in the response.
- [ ] Slice 5: Version bump to `0.0.6`
  - [ ] `django_strawberry_framework/__init__.py` `__version__` (the single version source; hatchling derives the packaging metadata from it) and the pinned `__version__` assertion in `tests/base/test_init.py` move together.
- [ ] Slice 6: Docs and board
  - [ ] `docs/GLOSSARY.md` (rendered from the fakeshop glossary database by `scripts/build_glossary_md.py`; edit the database, then re-render):
    - [Specialized scalar conversions][glossary-specialized-scalar-conversions] -> `shipped (0.0.6)`, listing `PostgreSQL HStoreField -> strawberry.scalars.JSON` (soft-registered, only when `django.contrib.postgres.fields` imports) and `PositiveBigIntegerField -> BigInt`.
    - [`BigInt` scalar][glossary-bigint-scalar] -> `shipped (0.0.6)`: the decimal-string wire format, the strict parser and serializer of [Decision 1](#decision-1--bigint-wire-format-and-target-fields), and the `strawberry_config()` registration of [Decision 6](#decision-6--bigint-public-export-status-and-registration-contract).
    - [Scalar field conversion][glossary-scalar-field-conversion] -> the new field-type rows and the `PositiveBigIntegerField` row.
    - [Index][glossary-index] -> status badges for the two shipped entries.
    - [Public exports][glossary-public-exports] -> `BigInt`. Importing the package emits no Strawberry deprecation warning.
  - [ ] `docs/TREE.md` lists `django_strawberry_framework/scalars.py` and `tests/test_scalars.py` (rendered from module docstrings by `scripts/build_tree_md.py`).
  - [ ] `TODAY.md` lists the scalars in its capability summary.
  - [ ] `KANBAN.md` carries the shipped `DONE-017-0.0.6` card (rendered from the fakeshop kanban database by `scripts/build_kanban_md.py`). The warning-free `StrawberryConfig.scalar_map` registration this spec's [Decision 6](#decision-6--bigint-public-export-status-and-registration-contract) states shipped as `DONE-025-0.0.7` ([`spec-025-scalar_map_helper-0_0_7.md`][spec-025]).
  - [ ] `CHANGELOG.md` `[0.0.6]`: `Added` `BigInt` (public export), the `JSONField -> JSON` and `HStoreField -> JSON` mappings, `ArrayField` recursion; `Changed` `PositiveBigIntegerField` from `int` to `BigInt` (breaking wire-format change).

## Problem statement

Four Django field types need a mapping in [`docs/GLOSSARY.md`'s Scalar field conversion table][glossary-scalar-field-conversion] that a plain Python scalar cannot give: `BigIntegerField` (and `PositiveBigIntegerField`), `JSONField`, PostgreSQL `ArrayField`, and PostgreSQL `HStoreField`. This spec maps them in `django_strawberry_framework/types/converters.py`.

Five constraints shape the design:

1. **`BigInt` has to survive GraphQL's `Int` boundary.** GraphQL's standard `Int` is **signed 32-bit** (range `-2_147_483_648` to `2_147_483_647`). Executing a query that returns an `int`-annotated field whose value exceeds that range yields a `GraphQLError` with message containing `Int cannot represent non 32-bit signed integer value` (the live error appends the offending value) — before the value reaches a JavaScript client. JavaScript's 53-bit precision limit is the secondary justification.
2. **`ArrayField` and `HStoreField` are PostgreSQL-only.** The default dev environment does not include a postgres driver (only `uv sync --group pg` adds one), so `django.contrib.postgres.fields` fails to import at module load time.
3. **`HStoreField` cannot be expressed as a typed map in GraphQL.** Strawberry rejects `dict[str, str | None]`. The annotation has to go through `strawberry.scalars.JSON`.
4. **Strawberry's `strawberry.scalar(...)` API is in a deprecated state for the "pass a class" pattern.** Both `strawberry.scalar(int, ...)` and `strawberry.scalar(NewType("BigInt", int), ...)` emit `DeprecationWarning: Passing a class to strawberry.scalar() is deprecated. Use StrawberryConfig.scalar_map instead...`. The package must therefore define `BigInt` on the non-deprecated path: a bare `NewType` plus a `ScalarDefinition` built from the `name=`-only `strawberry.scalar(...)` overload, registered through a package-provided `StrawberryConfig`. Importing `django_strawberry_framework` must emit no Strawberry `DeprecationWarning`. See [Decision 1](#decision-1--bigint-wire-format-and-target-fields) and [Decision 6](#decision-6--bigint-public-export-status-and-registration-contract).
5. **Public scalar discipline.** A public scalar needs strict parsing **and** strict serialization. `serialize=str` would accept any object (including `True`, `1.9`, `Decimal(...)`) and silently stringify it — schemas could emit values the parser would reject. `scalars.py` defines both `_parse_bigint` (input) and `_serialize_bigint` (output) with symmetric strictness.

## Goals

- Map `BigIntegerField` → `BigInt` and `PositiveBigIntegerField` → `BigInt`.
- Map `JSONField` → `strawberry.scalars.JSON`.
- Map `ArrayField(base_field)` → `list[converted_base_field_type]`, sentinel-guarded.
- Reject outer `choices` on `ArrayField` and nested `ArrayField` with `ConfigurationError`. Reject outer `choices` on `HStoreField` with `ConfigurationError` (symmetric with the ArrayField rejection — HStore's dict shape has no enum-able GraphQL representation; see [Decision 5](#decision-5--hstorefield-wire-shape)).
- Map `HStoreField` → `strawberry.scalars.JSON`, sentinel-guarded.
- Add `BigInt` to the package's public surface with both strict parser and strict serializer, defined on Strawberry's non-deprecated registration path so the package import emits no `DeprecationWarning`.
- Declare `SCALAR_MAP`'s value type so it admits scalar type forms (Decision 8).
- 100% coverage on the conversion paths.

## Non-goals

- **No new `Meta` key.**
- **No filter / order / aggregate input shapes for the new scalars.**
- **No multi-dimensional `ArrayField` support.**
- **No outer `choices` on `ArrayField` or `HStoreField`.** Both rejected with `ConfigurationError` — declare `choices` on `base_field` for ArrayField element-level enum, or model the constrained shape with a separate field for HStore.
- **No dedicated `HStore` scalar.**
- **No change to `BigAutoField`'s mapping.** Stays `int`; the consumer recourse for a PK past the 32-bit boundary is the annotation override shipped by the sibling card `DONE-019-0.0.6` ([Scalar field override semantics][glossary-scalar-field-override-semantics]).
- **No postgres driver added to dev dependencies.**
- **No consumer-facing schema-configuration surface beyond the `strawberry_config()` factory.** Extension composition, settings-backed auto-discovery of the config, and a deprecation shim for a pre-`scalar_map` `BigInt` spelling are all out of scope; see [`spec-025-scalar_map_helper-0_0_7.md`][spec-025].
- **No int64 range enforcement on `BigInt`.** The scalar is technically arbitrary-precision (Python `int` plus regex-validated decimal strings) — it accepts values past `2**63 - 1` even though the Django source columns top out there. Range enforcement at the scalar level is a separate concern (out of scope; consumers wanting a hard 64-bit cap can validate in their resolver or `clean` method).

## Architectural decisions

### Decision 1 — `BigInt` wire format and target fields

`BigInt` serializes as a **decimal string** at the wire and parses through a strict validator. Definition lives in `django_strawberry_framework/scalars.py`:

```python
# django_strawberry_framework/scalars.py (docstrings and comments trimmed)
_BIGINT_STRING_PATTERN = re.compile(r"^(0|-?[1-9][0-9]*)$")


def _parse_bigint(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("BigInt does not accept boolean values")
    if isinstance(value, int):
        return int.__int__(value)
    if isinstance(value, str):
        plain_value = str.__str__(value)
        if not _BIGINT_STRING_PATTERN.fullmatch(plain_value):
            raise ValueError(
                f"BigInt requires a plain ASCII decimal integer string "
                f"(optional leading minus for non-zero, no leading zeroes, "
                f"no underscores, no plus sign, no Unicode digits); got "
                f"{_safe_arg_repr(value)}",
            )
        return int(plain_value)
    raise ValueError(f"BigInt cannot parse {_safe_type_name(value)}")


def _serialize_bigint(value: object) -> str:
    if isinstance(value, bool):
        raise TypeError(f"BigInt cannot serialize bool value {value!r}")
    if isinstance(value, int):
        return int.__repr__(value)
    raise TypeError(f"BigInt cannot serialize {_safe_type_name(value)}")


BigInt = NewType("BigInt", int)

_BIGINT_SCALAR_DEFINITION: ScalarDefinition = strawberry.scalar(
    name="BigInt",
    serialize=_serialize_bigint,
    parse_value=_parse_bigint,
)

_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition] = {
    BigInt: _BIGINT_SCALAR_DEFINITION,
}
```

`BigInt` is a **bare** `NewType`: passing a class or `NewType` to `strawberry.scalar(...)` emits Strawberry's `Passing a class to strawberry.scalar() is deprecated` warning, so the `ScalarDefinition` is built from the `name=`-only overload and bound to the `NewType` through `_PACKAGE_SCALAR_MAP`, which `strawberry_config()` merges into a consumer's schema config ([Decision 6](#decision-6--bigint-public-export-status-and-registration-contract)).

**Subclass normalization.** The parser returns `int.__int__(value)` and matches `str.__str__(value)`, and the serializer emits `int.__repr__(value)`, so an `int` / `str` subclass's own `__int__` / `__str__` / `__repr__` can neither alter the accepted value nor replace the scalar's error contract. Error text names a value through `exceptions.py`'s `_safe_arg_repr` / `_safe_type_name`, so an unprintable value cannot replace the `ValueError` either.
**Why `BigInt` exists at all:** GraphQL's `Int` is a signed 32-bit scalar. Executing a query that returns an `int`-annotated field whose value exceeds `2**31 - 1` yields a `GraphQLError` with message containing `Int cannot represent non 32-bit signed integer value`.

**The parser must reject rather than coerce.** `bool` is rejected before the `int` check because `bool` subclasses `int`; `float` is rejected outright because `int(1.9) == 1` truncates silently. The regex is deliberately narrower than `int(str)`, so `"1_000"`, `"+1"`, `"01"`, `"-0"`, and Unicode-digit strings raise instead of parsing.

**The serializer must be as strict as the parser.** `_serialize_bigint` raises `TypeError` for any non-`int` resolver return so a schema cannot emit a value its own parser would reject; the GraphQL boundary surfaces that as an error.

**Range:** `BigInt` is technically arbitrary-precision (Python `int` plus regex-validated decimal strings, with no upper bound check). In practice it is *used to map* Django's 64-bit integer fields, so the API table targets `BigIntegerField` and `PositiveBigIntegerField`. Consumers needing a hard 64-bit range cap can validate in their resolver.

Target Django fields:

- `BigIntegerField` → `BigInt`.
- `PositiveBigIntegerField` → `BigInt`. Explicit `SCALAR_MAP` entry for regression protection.
- `BigAutoField` → `int` for PK wire-format stability. The consumer recourse for a PK past the `2**31` boundary is the annotation override shipped by the sibling card `DONE-019-0.0.6` ([Scalar field override semantics][glossary-scalar-field-override-semantics]).

### Decision 2 — `ArrayField` dimensionality cap and outer-`choices` rejection

Reject nested arrays and outer `choices` at type creation with `ConfigurationError`. `ArrayField(IntegerField())` works; `ArrayField(ArrayField(IntegerField()))` and `ArrayField(IntegerField(), choices=[...])` both raise.

```python
# in convert_scalar, before the scalar_for_field SCALAR_MAP walk.
# ``effective_null`` is the tri-state ``force_nullable`` override collapsed to
# one boolean; see the nullability-override note below.
if _ARRAY_FIELD_CLS is not None and isinstance(field, _ARRAY_FIELD_CLS):
    if isinstance(field.base_field, _ARRAY_FIELD_CLS):
        raise ConfigurationError(
            f"Nested ArrayField on {_field_label(field)} is not supported.",
        )
    if _field_has_choices(field):
        raise ConfigurationError(
            f"ArrayField on {_field_label(field)} declares choices on the outer "
            f"field; outer-array choices are ambiguous at the GraphQL boundary. Declare choices "
            f"on base_field for element-level enum, or use FilterSet.",
        )
    inner = convert_scalar(field.base_field, type_name)
    result = GenericAlias(list, (inner,))
    return result | None if effective_null else result
```

`_field_label(field)` and `_field_has_choices(field)` are the module's guarded metadata readers: they render `Model.field` for diagnostics and read the choices flag without letting a hostile field descriptor's exception escape as something other than a `ConfigurationError`. Interpolating `field.model.__name__` / `field.name` directly, or testing `field.choices` as a bare truth value, reintroduces that escape.

**Choice handling on `base_field` is inherited automatically:** the recursive `convert_scalar(field.base_field, type_name)` call re-enters and hits the existing choices branch, producing `list[<TypeName><FieldName>Enum]`. The outer-`choices` rejection only fires for the outer `ArrayField` itself.

`null=True` semantics: outer `null=True` → `list[T] | None`; inner `null=True` → `list[T | None]`; both → `list[T | None] | None`.

**Nullability override.** `convert_scalar` takes a keyword-only `force_nullable: bool | None = None` tri-state (the `Meta.nullable_overrides` / `Meta.required_overrides` seam). It is collapsed once, at the top of the function, into `effective_null = field.null if force_nullable is None else force_nullable` (a field whose `null` read raises surfaces as `ConfigurationError`), and every outer widening site in this Decision and in [Decision 5](#decision-5--hstorefield-wire-shape) reads `effective_null`. The recursive `base_field` call above is deliberately left `force_nullable`-**unset**, so the outer override never reaches the inner element: inner nullability continues to follow `base_field.null`.

### Decision 3 — `JSONField` target type

Map `models.JSONField` → `strawberry.scalars.JSON`.

### Decision 4 — Soft import via module-level sentinels

Both postgres-only field classes are soft-imported once at module load into module-level sentinels, through the package's single optional-import owner (`django_strawberry_framework/utils/imports.py::import_attr_if_importable`) rather than a hand-rolled `try` / `except ImportError` per field:

```python
_ARRAY_FIELD_CLS = cast(
    "type[ArrayField[Never, object]] | None",
    import_attr_if_importable("django.contrib.postgres.fields", "ArrayField"),
)
_HSTORE_FIELD_CLS = cast(
    "type[HStoreField] | None",
    import_attr_if_importable("django.contrib.postgres.fields", "HStoreField"),
)
```

The helper's contract is what the sentinels rely on: `None` when `django.contrib.postgres.fields` is unimportable (so package import still succeeds on a dev environment with no postgres driver), and a loud `AttributeError` if that module *is* importable but lacks the named class — a broken environment that must fail rather than silently degrade into an unregistered field type.

Module-load assignment only exercises one branch per environment, so the importable / unimportable branch pair is covered **once**, at the helper, in `tests/utils/test_imports.py`. This module owns no soft-import branch of its own and must not grow a second copy of that coverage.

### Decision 5 — `HStoreField` wire shape

Map `HStoreField` → `strawberry.scalars.JSON`. Strawberry rejects `dict[str, str | None]` as an annotation. `HStoreField` is **not** added to `SCALAR_MAP`; instead it gets a sentinel-guarded branch in `convert_scalar`, mirroring Decision 2's shape:

```python
# in convert_scalar, after the ArrayField branch, before the scalar_for_field walk:
if _HSTORE_FIELD_CLS is not None and isinstance(field, _HSTORE_FIELD_CLS):
    if _field_has_choices(field):
        raise ConfigurationError(
            f"HStoreField on {_field_label(field)} declares choices; "
            f"HStore stores a dict[str, str | None] with no enum-able shape at the "
            f"GraphQL boundary. Drop the choices declaration or model the constrained "
            f"shape with a separate field.",
        )
    json_type = strawberry.scalars.JSON
    return json_type | None if effective_null else json_type
```

Django accepts `choices` on an `HStoreField` syntactically (for admin / form widget purposes), but the constraint is form-only and is not enforced at the column level — so a silently-ignored declaration would produce a schema emitting values the consumer did not expect. The rejection is symmetric with the `ArrayField` outer-`choices` rejection in [Decision 2](#decision-2--arrayfield-dimensionality-cap-and-outer-choices-rejection) and forces the consumer to model the constrained shape explicitly.

### Decision 6 — `BigInt` public-export status and registration contract

`BigInt` is a public export (`from django_strawberry_framework import BigInt`). [`docs/GLOSSARY.md`'s Public exports][glossary-public-exports] entry carries the symbol, and the pinned `__all__` assertion in `tests/base/test_init.py` includes it.

**Registration contract.** `BigInt` is a bare `NewType("BigInt", int)`. The scalar behavior lives in a separate `ScalarDefinition` bound to that `NewType` through the package scalar map, and a consumer reaches it by passing the package-provided config into their schema:

```python
import strawberry
from django_strawberry_framework import BigInt, strawberry_config

schema = strawberry.Schema(query=Query, config=strawberry_config())
```

A `BigInt` annotation in a schema built **without** `config=strawberry_config()` fails schema construction with `Unexpected type '...BigInt'`. That is the deliberate consequence of staying off Strawberry's deprecated class-direct-to-`scalar()` path: the annotation is inert until the scalar map registers it, rather than silently resolving to something else.

**Import-time warning posture:** importing `django_strawberry_framework` - directly or transitively - emits no Strawberry `DeprecationWarning`, and the package imports cleanly under `-W error::DeprecationWarning`. `test_package_import_does_not_emit_strawberry_deprecation_warning` pins that contract.

The [`strawberry_config`][glossary-strawberry-config] factory's own surface - the keyword-only `extra_scalar_map`, the `ValueError` on a key collision with a package-defined scalar, and the `**config_kwargs` passthrough - is specified by [`spec-025-scalar_map_helper-0_0_7.md`][spec-025], not here. This spec owns only the requirement that `BigInt` resolve through it.

### Decision 7 — Test strategy

**Test file layout** (mirrors [`docs/TREE.md`][tree]):

- `tests/test_scalars.py` — the `BigInt` parser / serializer cases no GraphQL request can express (Python `bool` / `float` / `None`, hostile subclasses, non-`int` serializer inputs), the public-import smoke test, and the warning-free-import regression test. Mirrors the flat `django_strawberry_framework/scalars.py`.
- `tests/types/test_converters.py` — the sentinel-swap field-mapping tests and the package-internal schema-execution tests. Mirrors `django_strawberry_framework/types/converters.py`.
- `examples/fakeshop/test_query/test_scalars_api.py` — the live `/graphql/` tier. Any mapping reachable from a real query against fakeshop is pinned HERE (per [`AGENTS.md`][agents]); the `apps.scalars` app carries the `ScalarSpecimen` / `NullableScalarSpecimen` pair whose `payload` (`JSONField`), `signed_big` (`BigIntegerField`), and `unsigned_big` (`PositiveBigIntegerField`) columns exercise every mapping this spec owns that a SQLite-backed example can reach, including every string-form parse and reject case. `ArrayField` / `HStoreField` are postgres-only and stay at the package tier behind fake sentinels.

**Fake field doubles** (in `tests/types/test_converters.py`):

```python
class _FakeArrayField(models.Field):
    """Test double for ArrayField that does not require django.contrib.postgres.

    Mirrors Django's real ArrayField metadata propagation so base_field has
    model and name attributes when convert_scalar recurses into it. Required
    because convert_choices_to_enum reads field.model.__name__ and field.name
    to build enum_name = f"{type_name}{pascal_case(field.name)}Enum".
    """
    def __init__(self, base_field, **kwargs):
        super().__init__(**kwargs)
        self.base_field = base_field

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        self.base_field.set_attributes_from_name(name)
        self.base_field.model = cls


class _FakeHStoreField(models.Field):
    """Test double for HStoreField that does not require django.contrib.postgres.

    Tests must call
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)
    before declaring a DjangoType using this field; otherwise convert_scalar's
    HStore branch never dispatches.
    """
    pass
```

**Test-model `Meta` requirement**: every test model hosting `_FakeArrayField` or `_FakeHStoreField` declares `class Meta: managed = False` with its section's `app_label` (`"test_arrayfield"`, `"test_hstorefield"`). The `managed = False` flag tells Django the model has no migrated table: no migration is implied, and `MyModel.objects.create(...)` would fail at the database boundary, so test rows are instantiated directly (`MyModel(field=value)`).

**Sentinel-swap requirement**: every `_FakeArrayField` / `_FakeHStoreField`-based test must call `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` (or `_HSTORE_FIELD_CLS`) *before* declaring the `DjangoType`. Without the swap, `convert_scalar` falls through to the unsupported-field `ConfigurationError`.

**Schema test fixture pattern** (the recipe every schema-execution test here follows):

`tests/types/test_converters.py::_isolate_registry` is the module's thin `autouse=True` wrapper around the shared `tests/conftest.py::isolate_global_registry`, which clears the registry and the connection-type cache on entry and exit. The suite-wide autouse `tests/conftest.py::_restore_app_registry` retires every model a test declares, so an in-function model can be re-declared under the same `app_label` without Django's "Model already registered" warning.

The models are declared inside the test function, so each `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` sits beside the `DjangoType` declaration it governs. Every schema-execution test follows this sequence:

1. **Define the synthetic test model** inside the test, with `class Meta: managed = False` and the section's `app_label`.
2. **Apply sentinel monkey-patches** (where relevant) BEFORE declaring the `DjangoType` — `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` etc. The converter's sentinel-guard branch checks the patched value at type-creation time.
3. **Define the `DjangoType` subclass** referencing the synthetic model. This registers it in the pending-types collection.
4. **Call `finalize_django_types()`** to resolve pending relations and apply the `strawberry.type` decoration. This is **mandatory** — without it, the `DjangoType` is not a usable Strawberry type, and `strawberry.Schema(...)` raises.
5. **Build the schema** with a `Query` root that exposes the type (a `@strawberry.field` returning a hand-built instance), passing `config=strawberry_config()` whenever a `BigInt` annotation is involved.
6. **Execute** via `schema.execute_sync("query { ... }")` and assert on `result.data` / `result.errors`.

**Soft-import branch coverage** is NOT written here. Both sentinels resolve through the shared `utils/imports.py::import_attr_if_importable`, whose importable / unimportable / missing-attribute branches are covered once in `tests/utils/test_imports.py` (`sys.modules[name] = None` is the documented way to force the `ImportError` leg). Duplicating that pair against the converter's sentinels would test the helper twice and this module not at all.

**Warning-free-import regression test** (`test_package_import_does_not_emit_strawberry_deprecation_warning`): uses **subprocess isolation** rather than an in-process `importlib.reload`. `importlib.reload(django_strawberry_framework)` does not reload submodules - the reload finds `django_strawberry_framework.scalars` cached in `sys.modules` and never re-executes the scalar-definition line, so a reload-based test observes zero warnings whether or not the definition is on Strawberry's deprecated path, and cannot fail. The robust mechanism:

```python
def test_package_import_does_not_emit_strawberry_deprecation_warning():
    """Pin that the package import surface is clean of Strawberry's
    class-direct-to-scalar() DeprecationWarning. Subprocess isolation avoids
    the importlib.reload-doesn't-reload-submodules trap.

    sys.executable is the venv's Python under `uv run pytest`, so the
    subprocess inherits the editable package install - no PATH / PYTHONPATH
    munging needed.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-W",
            "error::DeprecationWarning",
            "-c",
            "import django_strawberry_framework",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, (
        f"Importing the package under -W error::DeprecationWarning failed:\nstderr: {result.stderr}"
    )
```

Returns exit code 0 while the package's scalar definitions stay off Strawberry's deprecated overloads; returns non-zero the moment one is reintroduced on the import path.

Coverage target: 100%.

### Decision 8 — `SCALAR_MAP` value type widening

`SCALAR_MAP` is declared `dict[type[ConcreteField], TypeForm[object]]`: its values are type forms, not plain `type`s, because `strawberry.scalars.JSON` and `BigInt` are `NewType`-backed scalars.

## User-facing API

The mappings this spec owns in [`docs/GLOSSARY.md`'s Scalar field conversion entry][glossary-scalar-field-conversion]:

| Django field | Generated annotation | Notes |
|---|---|---|
| `BigIntegerField` | `BigInt` | Public scalar; string wire format; strict parser + serializer. |
| `PositiveBigIntegerField` | `BigInt` | An `int` annotation would hit the GraphQL 32-bit `Int` error (message containing `Int cannot represent non 32-bit signed integer value`) past `2**31 - 1`. |
| `JSONField` | `strawberry.scalars.JSON` | |
| `ArrayField(IntegerField())` | `list[int]` | Postgres contrib soft-required. |
| `ArrayField(IntegerField(null=True))` | `list[int \| None]` | |
| `ArrayField(IntegerField(), null=True)` | `list[int] \| None` | |
| `ArrayField(IntegerField(), choices=[...])` | `ConfigurationError` | Outer `choices` rejected. |
| `HStoreField` | `strawberry.scalars.JSON` | Postgres contrib soft-required. |
| `HStoreField(choices=[...])` | `ConfigurationError` | Outer `choices` rejected (symmetric with ArrayField). |
| `BigAutoField` | `int` | Kept for PK wire-format stability. |

`BigInt` is a public export. **Importing the package emits no Strawberry deprecation warning.** A `BigInt` annotation resolves only in a schema built with `config=strawberry_config()`; see [Decision 6](#decision-6--bigint-public-export-status-and-registration-contract).

## Implementation plan

Six slices:

### Slice 1 — `BigInt` scalar + 64-bit integer field mappings

Files: `django_strawberry_framework/scalars.py` (`_parse_bigint`, `_serialize_bigint`, `BigInt`, the scalar definition and the package scalar map), `django_strawberry_framework/__init__.py`, `tests/base/test_init.py` (`__all__` pin), `django_strawberry_framework/types/converters.py` (`SCALAR_MAP` entries), `tests/test_scalars.py`, `tests/types/test_converters.py` and `examples/fakeshop/test_query/test_scalars_api.py`.

### Slice 2 — `JSONField` mapping

Files: `django_strawberry_framework/types/converters.py`, `examples/fakeshop/test_query/test_scalars_api.py`.

### Slice 3 — `ArrayField` recursion (sentinel-based)

Files: `django_strawberry_framework/types/converters.py` (sentinel + branch + outer-`choices` rejection), `tests/types/test_converters.py` (`_FakeArrayField` double + tests).

### Slice 4 — `HStoreField` conditional registration via sentinel

Files: `django_strawberry_framework/types/converters.py` (sentinel + branch returning `JSON`), `tests/types/test_converters.py` (`_FakeHStoreField` double + tests).

### Slice 5 — Version bump

Files: `django_strawberry_framework/__init__.py` (`__version__`), `tests/base/test_init.py`.

### Slice 6 — Docs and board

Files: `docs/GLOSSARY.md`, `docs/TREE.md`, `KANBAN.md` (each re-rendered from its source), `TODAY.md`, `CHANGELOG.md`.

## Edge cases and constraints

- **`BigAutoField` stays mapped to `int`.** A PK past the `2**31` boundary is handled by the consumer annotation override (`DONE-019-0.0.6`).
- **`PositiveBigIntegerField` maps to `BigInt`.** A breaking wire-format change against an `int` mapping, recorded in `CHANGELOG.md` `[0.0.6]`.
- **`PositiveSmallIntegerField` and `PositiveIntegerField` stay `int`.** Ranges fit within GraphQL's 32-bit `Int`.
- **`PositiveBigIntegerField` MRO.** Explicit entry kept for regression protection; the MRO walk would already resolve correctly via `BigIntegerField: BigInt`.
- **`ArrayField` with `choices` on `base_field`** — handled by the recursive `convert_scalar` call.
- **`ArrayField` with `choices` on the outer field** — rejected with `ConfigurationError`.
- **`JSONField` with custom `encoder`.** Annotation is `JSON` regardless.
- **MRO walk for subclasses.** `ArrayField` / `HStoreField` are checked via sentinel guards *before* the `scalar_for_field` MRO walk.
- **`from __future__ import annotations`.** The annotations survive stringified module imports.
- **`SCALAR_MAP` value type.** Per Decision 8.
- **Strict parser tradeoffs.** Regex narrower than `int(str)` — predictability over leniency.
- **Strict serializer tradeoffs.** Resolver returning a non-`int` value raises at the schema boundary instead of silently stringifying. Consumers wanting permissive output can wrap the serializer at their layer; the package surface stays strict.
- **`BigInt` is arbitrary-precision** — see [Decision 1](#decision-1--bigint-wire-format-and-target-fields) for the canonical framing.
- **Custom `from_db_value` on a `BigIntegerField` subclass.** If a consumer subclasses `BigIntegerField` and overrides `from_db_value` to return a non-`int` Python value (e.g. a domain type like a money object), `_serialize_bigint` raises `TypeError` at the schema boundary rather than stringifying the object via `__str__`. Recourse: keep the column type-pure at the GraphQL boundary, or override the scalar annotation on the affected field via [Scalar field override semantics][glossary-scalar-field-override-semantics] (`DONE-019-0.0.6`).

## Test plan

Three test files, all run unconditionally:

- **`tests/test_scalars.py`** — the `BigInt` cases no GraphQL request can express (Python `bool` / `float` / `None` into the parser, non-`int` objects and hostile subclasses into the serializer, unprintable values in error text), the top-level import smoke test, and the warning-free-import test (a subprocess).
- **`tests/types/test_converters.py`** — the sentinel-guarded `ArrayField` / `HStoreField` mappings (postgres-only, unreachable from a real fakeshop query), the `BigAutoField` mapping, the `null` input position, and a resolver returning `bool`, via the [Schema test fixture pattern](#decision-7--test-strategy).
- **`examples/fakeshop/test_query/test_scalars_api.py`** — the live `/graphql/` tier for every case a real fakeshop query reaches: `BigInt` and `JSON` annotation shape via introspection, nullable widening, wire round-trip (including zero, negative, int64-min and int64-max), string-form / int-form argument parsing, and every malformed-string and `bool` / `float` literal rejection.

Per [`AGENTS.md`][agents], any mapping reachable from a real query against fakeshop is pinned at the live tier rather than by a synthetic package-tier substitute.

Test categories:

1. Wire format: decimal-string serialization including `0`, negative values, int64-min, int64-max (live).
2. Strict serializer negative cases: `bool`, `float`, `str`, `Decimal`, `None`, custom object (package); a resolver returning `bool` (package, schema execution).
3. Hostile `int` / `str` subclasses normalized; unprintable values in error text (package).
4. Strict parser positive cases: int and string zero, negative decimal strings, int64-min/max strings, decimal strings past the JS safe integer (live).
5. Strict parser negative cases: `bool` / `float` literals and empty / whitespace-padded / non-decimal / underscore / leading-plus / leading-zero / `-0` / Unicode-digit strings (live); Python `bool`, `float`, `None` (package).
6. Annotation generation and `null=True` widening via schema introspection.
7. `null` in a nullable `BigInt` input position reaches the resolver as `None`.
8. Sentinel branch coverage via fake field classes + monkey-patched sentinels.
9. Soft-import branch coverage — owned by `tests/utils/test_imports.py`, not repeated here ([Decision 4](#decision-4--soft-import-via-module-level-sentinels)).
10. Choice composition on `base_field` of `_FakeArrayField`.
11. Outer-`choices` rejection on `_FakeArrayField` and `_FakeHStoreField`.
12. `base_field`-unsupported-type propagation through the recursive call.
13. Dimensionality rejection.
14. **Warning-free-import regression** — subprocess invocation `python -W error::DeprecationWarning -c "import django_strawberry_framework"` returns exit code 0 (no Strawberry class-direct-to-`scalar()` warning escapes the package import). Subprocess isolation avoids the `importlib.reload`-doesn't-reload-submodules trap; see [Decision 7](#decision-7--test-strategy).
15. HStore-with-`None`-value resolver test.
16. Optional real-postgres compatibility — `pytest.importorskip("django.contrib.postgres.fields")`; ArrayField introspects as `[Int!]!`; HStoreField introspects as `JSON!` AND resolver returning `{"k1": "v", "k2": None}` serializes through `schema.execute_sync` with the dict shape (including the `None`) preserved.

Coverage target: 100%.

## Doc updates

Per the slice checklist's Slice 6. The `KANBAN.md` card body is not reproduced here: `KANBAN.md` is generated from the fakeshop kanban database, and a verbatim copy in the spec would drift against the live card.

## Out of scope (explicitly tracked elsewhere)

- Filter input shapes — [`FilterSet`][glossary-filterset], DONE-027-0.0.8.
- Mutation input types for `BigInt` — [Mutations subsystem][glossary-djangomutation], DONE-036-0.0.11.
- Multi-database routing — [Multi-database cooperation][glossary-multi-database-cooperation], DONE-023-0.0.7.
- Multi-dimensional `ArrayField`.
- Dedicated `HStore` scalar.
- `BigAutoField` → `BigInt`.
- Consumer-facing scalar annotation overrides — DONE-019-0.0.6.
- The `strawberry_config()` factory's own surface (`extra_scalar_map`, collision policy, `**config_kwargs`) — [`spec-025-scalar_map_helper-0_0_7.md`][spec-025], `DONE-025-0.0.7`.
- [`Upload`][glossary-upload-scalar] (`DONE-037-0.0.11`), a re-export of Strawberry's built-in scalar that resolves without a package scalar-map entry.
- `BigInt64`-bounded variant of `BigInt`.

## Definition of done

- All six slices land per the [Slice checklist](#slice-checklist).
- Test suite green, coverage at 100%.
- `SCALAR_MAP`'s value type admits scalar type forms (Decision 8).
- `__version__` and its `tests/base/test_init.py` pin at `0.0.6`.
- `docs/GLOSSARY.md`, `docs/TREE.md`, `TODAY.md`, `CHANGELOG.md`, and `KANBAN.md` (the `DONE-017-0.0.6` body) reflect shipped state.
- `docs/GLOSSARY.md` updated entries: [Specialized scalar conversions][glossary-specialized-scalar-conversions], [`BigInt` scalar][glossary-bigint-scalar], [Scalar field conversion][glossary-scalar-field-conversion], [Index][glossary-index], [Public exports][glossary-public-exports].
- `BigInt` strict parser **and strict serializer** pinned live in `examples/fakeshop/test_query/test_scalars_api.py` for every request-expressible case, and in `tests/test_scalars.py` for the Python-object cases.
- Warning-free import pinned via `test_package_import_does_not_emit_strawberry_deprecation_warning` (subprocess-based).
- `ArrayField` outer-`choices` rejection tested.
- `HStoreField` outer-`choices` rejection tested.
- `BigInt` top-level import smoke-tested (`test_bigint_is_importable_from_top_level`).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[contributing]: ../../CONTRIBUTING.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[glossary-bigint-scalar]: ../GLOSSARY.md#bigint-scalar
[glossary-choice-enum-generation]: ../GLOSSARY.md#choice-enum-generation
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-djangomutation]: ../GLOSSARY.md#djangomutation
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-filterset]: ../GLOSSARY.md#filterset
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-index]: ../GLOSSARY.md#index
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-multi-database-cooperation]: ../GLOSSARY.md#multi-database-cooperation
[glossary-optimizerhint]: ../GLOSSARY.md#optimizerhint
[glossary-public-exports]: ../GLOSSARY.md#public-exports
[glossary-scalar-field-conversion]: ../GLOSSARY.md#scalar-field-conversion
[glossary-scalar-field-override-semantics]: ../GLOSSARY.md#scalar-field-override-semantics
[glossary-specialized-scalar-conversions]: ../GLOSSARY.md#specialized-scalar-conversions
[glossary-strawberry-config]: ../GLOSSARY.md#strawberry_config
[glossary-upload-scalar]: ../GLOSSARY.md#upload-scalar
[glossary]: ../GLOSSARY.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-017-rationale]: appx/spec-017-deferred_scalars-0_0_6-rationale.md
[spec-025]: spec-025-scalar_map_helper-0_0_7.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
