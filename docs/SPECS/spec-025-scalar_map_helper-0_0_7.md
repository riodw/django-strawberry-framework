# Spec: Warning-free scalar registration via `StrawberryConfig.scalar_map`

Target release: `0.0.7` (the [`KANBAN.md`][kanban] card `DONE-025-0.0.7`; one card of the joint `0.0.7` cut, see [Decision 8](#decision-8--version-posture-this-card-ships-inside-the-007-cut)).
Status: shipped (`0.0.7`). The spec describes the scalar-registration contract as the code carries it; each Decision's justification and rejected alternatives live in [`spec-025-scalar_map_helper-0_0_7-rationale.md`][spec-025-rationale].
Owner: package maintainer.
Predecessors: [`docs/SPECS/spec-017-deferred_scalars-0_0_6.md`][spec-017] Decision 1 (the `BigInt` wire format and target fields) and Decision 6 (the `BigInt` public-export and registration contract); [`docs/GLOSSARY.md`][glossary] entries [`BigInt scalar`][glossary-bigint-scalar] and [`Specialized scalar conversions`][glossary-specialized-scalar-conversions].

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first:

- [`BigInt scalar`][glossary-bigint-scalar] — the scalar this spec registers through `StrawberryConfig.scalar_map`. Its wire format (decimal string via `_serialize_bigint`), strict parser (`^(0|-?[1-9][0-9]*)$` via `_parse_bigint`) and target Django fields (`BigIntegerField`, `PositiveBigIntegerField`) are spec-017's; this spec owns the registration mechanism, not the scalar's semantics.
- [`Specialized scalar conversions`][glossary-specialized-scalar-conversions] — pins `BigIntegerField → BigInt` and `PositiveBigIntegerField → BigInt` in [`django_strawberry_framework/types/converters.py::SCALAR_MAP`][converters], which names the `BigInt` symbol directly.
- [`Scalar field conversion`][glossary-scalar-field-conversion] — the broader scalar-mapping contract; `BigInt` is one entry in that family.
- [`Upload scalar`][glossary-upload-scalar] — the package's other public scalar. It is Strawberry's own `NewType("Upload", bytes)`, already present in Strawberry's `DEFAULT_SCALAR_REGISTRY`, so it is re-exported with **no** `_PACKAGE_SCALAR_MAP` entry and resolves in a schema built with no package config at all — the deliberate contrast with the package-custom `BigInt`, which is absent from that registry and must be bound through `strawberry_config()`.
- [`DjangoType`][glossary-djangotype] — consumer-facing types reach `BigInt` through the converter table.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — framing only; the documented schema call puts `config=strawberry_config()` and `extensions=[...]` side by side.
- [`ConfigurationError`][glossary-configurationerror] — not raised by the helper; [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions) uses `ValueError` because every rejection is a consumer-input mistake at helper-call time.
- [`finalize_django_types`][glossary-finalize-django-types] — `config=strawberry_config()` leaves the finalization-then-construction order intact.

Project conventions: the live-HTTP-priority rule at [`AGENTS.md #"any line reachable via a real GraphQL query against fakeshop"`][agents] (governs where `BigInt` round-trip coverage lives, [Decision 7](#decision-7--test-placement-and-shape)); the settings-keys rule at [`AGENTS.md #"Add a settings key only when the feature that needs it lands"`][agents] (governs the auto-discovery non-goal).

## Slice checklist

- [ ] Slice 1: Helper module + `BigInt` definition
  - [ ] [`django_strawberry_framework/scalars.py`][scalars]: `BigInt` is a bare `NewType("BigInt", int)`; `_BIGINT_SCALAR_DEFINITION: ScalarDefinition` is built via the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload (the `cls is None and name is not None` branch at [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`][scalar], which returns a `ScalarDefinition` without emitting `DeprecationWarning`); `_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition]` maps the `BigInt` `NewType` to that definition; the public [`django_strawberry_framework/scalars.py::strawberry_config`][scalars] factory and the private [`django_strawberry_framework/scalars.py::_safe_scalar_map_key_label`][scalars] collision-key labeller per [Decision 2](#decision-2--helper-api-shape-and-module-location) and [Decision 3](#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition). The module carries no `warnings` import and no suppression block ([Decision 6](#decision-6--no-warning-suppression-at-the-definition-site)).
    - Module surface: imports `Mapping`, `StrawberryConfig` (`strawberry.schema.config`), `ScalarDefinition` (`strawberry.types.scalar`) and `_safe_arg_repr` / `_safe_type_name` from [`django_strawberry_framework/exceptions.py`][exceptions]. The module declares an `__all__`; this spec's names in it are `"BigInt"` and `"strawberry_config"`.
  - [ ] [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init]: re-exports `strawberry_config` on the [`django_strawberry_framework/__init__.py #"from .scalars import BigInt"`][django-strawberry-framework-init] line beside `BigInt`; both are in the package `__all__`, where `"strawberry_config"` is the **last** element (see [Edge cases](#edge-cases-and-constraints) for the sort rule).
- [ ] Slice 2: Tests
  - [ ] [`tests/test_scalars.py`][test-scalars]: the `strawberry_config()` factory sections ("scalar-map tests" and "`**config_kwargs` passthrough tests") carry the tests named in the [Test plan](#test-plan), one pytest item each.
  - [ ] [`tests/test_scalars.py`][test-scalars]: `test_package_import_does_not_emit_strawberry_deprecation_warning` runs `python -W error::DeprecationWarning -c "import django_strawberry_framework"` in a subprocess and pins the clean import ([Decision 6](#decision-6--no-warning-suppression-at-the-definition-site)).
  - [ ] [`tests/base/test_init.py`][test-init]: `test_public_api_surface_is_pinned` pins `__all__` as an exact tuple, ending in `"strawberry_config"`.
  - [ ] [`tests/types/test_converters.py`][test-converters]: every schema in the file that resolves to `BigInt` is built with `config=strawberry_config()` (the BigInt section's `test_bigint_in_input_position_with_null_via_schema_execution` and `test_bigint_resolver_returning_bool_raises_via_schema_execution`), and `strawberry_config` is in the file's `from django_strawberry_framework import (...)` block. `test_big_auto_field_still_maps_to_int` sits under the same banner and passes no `config=`: `BigAutoField` resolves to upstream `Int`, never `BigInt`. Which `BigInt` cases live in this package file and which live in live `/graphql/` coverage is owned by the live-coverage rule at [`AGENTS.md #"any line reachable via a real GraphQL query against fakeshop"`][agents]; the migration rule of [Decision 5](#decision-5--migration-posture-hard-break-in-alpha) applies wherever a case lives.
  - [ ] [`tests/test_scalars.py`][test-scalars] module docstring: names the live modules that own wire-reachable `BigInt` parse / serialize ([`examples/fakeshop/test_query/test_scalars_api.py`][test-scalars-api]) and lists `strawberry_config()` construction among what stays in-process.
- [ ] Slice 3: Example-app migration
  - [ ] [`examples/fakeshop/config/schema.py`][schema]: the schema the project serves at `/graphql/` passes [`examples/fakeshop/config/schema.py #"config=strawberry_config(),"`][schema], with `strawberry_config` on the file's `from django_strawberry_framework import (...)` block. The constructor class, the roots and the `extensions=` entry are other cards' business per [Decision 9](#decision-9--example-app-migration-scope).
  - [ ] Per-app `examples/fakeshop/apps/*/schema.py` modules ([`library`][schema-library], [`products`][schema-products] and the rest): no edit. Each declares a `Query` root and constructs no schema; their `BigIntegerField` / `PositiveBigIntegerField` columns reach `BigInt` through [`django_strawberry_framework/types/converters.py #"models.BigIntegerField: BigInt,"`][converters], and the registration rides the project-level construction.
- [ ] Slice 4: Docs
  - [ ] [`docs/README.md`][readme]: the [Quick start][readme-quick-start] and [Schema setup][readme-schema-setup] blocks import `strawberry_config` and pass `config=strawberry_config()`. Blocks that declare types without constructing a schema (the [Relay Node][readme-relay-node] example among them) have no `config=` to carry.
  - [ ] [`docs/GLOSSARY.md`][glossary] (rendered from the glossary DB): the [`strawberry_config`][glossary-strawberry-config] entry; the [`BigInt scalar`][glossary-bigint-scalar] entry's registration paragraph; the [Public exports][glossary-public-exports] bullet and the [Index][glossary-index] row (`shipped (0.0.7)`).
  - [ ] [`GOAL.md`][goal]: the [`schema.py`][goal-schemapy] showcase imports `strawberry_config` and passes `config=strawberry_config()`. The per-stack diff blocks under [Migration shape][goal-migration-shape] show minimal `Meta`-shape diffs and carry no `config=`.
  - [ ] [`TODAY.md`][today]: the `config/schema.py` block under [What you can build today][today-what-you-can-build-today] imports `strawberry_config` and passes `config=strawberry_config()`.
  - [ ] [`docs/TREE.md`][tree]: no structural row; it is rendered by [`scripts/build_tree_md.py`][build-tree] from module docstrings, so the `scalars.py` line follows that module's docstring.
  - [ ] [`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv`][spec-025-terms] anchors the spec's project terms, including `strawberry_config`; [`scripts/check_spec_glossary.py`][check-spec-glossary] passes on it.
- [ ] Slice 5: KANBAN + CHANGELOG
  - [ ] [`KANBAN.md`][kanban]: the card is in the Done column as `DONE-025-0.0.7` and names this spec by its structured filename.
  - [ ] [`CHANGELOG.md`][changelog]: the shared `## [0.0.7] - 2026-05-27` section carries this card's `### Added` bullet (the `strawberry_config` factory), `### Changed` bullet (the breaking registration move, with its before/after diff) and `### Removed` bullet (the suppression block); `[0.0.6]` carries no "tracked as a follow-up" note for it.

## Problem statement

Strawberry deprecates the class-direct `strawberry.scalar(<class-or-NewType>, ...)` path: the `wrap()` body at [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"def wrap(cls: _T) -> ScalarWrapper"`][scalar] emits `DeprecationWarning("Passing a class to strawberry.scalar() is deprecated. Use StrawberryConfig.scalar_map instead for better type checking support. ...")`. A package-custom scalar defined that way either leaks the warning into every consumer's import or has to suppress it at the definition site, and every further package-custom scalar would face the same choice.

The package therefore defines `BigInt` on Strawberry's recommended path — a bare `NewType` plus a `ScalarDefinition` produced by the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload — and has consumers compose a package-provided `StrawberryConfig` into their schema call. There is no suppression, and a package-custom scalar binds through one registration point without any change to the helper's API.

## Goals

1. `BigInt` is registered through Strawberry's `StrawberryConfig.scalar_map` path.
2. One registration point serves any package-custom scalar, so a later scalar needs no change to `strawberry_config(...)`.
3. The consumer cost is one argument per schema construction — `config=strawberry_config()` — with no annotation-site changes.
4. The package import is warning-free by construction, not by suppression.

## Non-goals

- Composing Strawberry extensions through this helper. `extensions=` belongs on the schema constructor, not on `StrawberryConfig`, and the signature has no `extra_extensions=` parameter — see [Decision 2](#decision-2--helper-api-shape-and-module-location). Demand for an extension-bundling helper would ship as a separate symbol rather than overloading `strawberry_config`.
- Auto-discovery of the package config through a Django settings key (e.g. `STRAWBERRY_CONFIG_FACTORY`). Consumers pass `config=strawberry_config()` explicitly; per the settings-keys rule at [`AGENTS.md #"Add a settings key only when the feature that needs it lands"`][agents], no such key exists.
- Registering [`Upload`][glossary-upload-scalar]. Strawberry's own `DEFAULT_SCALAR_REGISTRY` carries it, so it needs no `_PACKAGE_SCALAR_MAP` entry and resolves in any schema, config or not. A package-**custom** scalar binds by gaining an entry; either way `strawberry_config(...)` is untouched.
- A `dst.Schema(...)` wrapper around the schema constructor, or a public `SCALAR_MAP` constant consumers splat into their own `StrawberryConfig(scalar_map={...})`. Both rejected per [Decision 2](#decision-2--helper-api-shape-and-module-location).
- Editing the converter table at [`django_strawberry_framework/types/converters.py::SCALAR_MAP`][converters]; its `BigInt` entries name the symbol directly, so the registration path needs no table change.
- Renaming `BigInt`. Its GraphQL name and Python identifier are both `BigInt`.

## Borrowing posture

No upstream precedent exists at the helper-API level. The `StrawberryConfig.scalar_map` registration *mechanism* is the upstream pattern adopted; the package-side factory wrapping it is new.

### From `strawberry-django` — no precedent to borrow

`/Users/riordenweber/projects/strawberry-django-main/strawberry_django/` references neither `StrawberryConfig` nor `scalar_map`. It defines no package-custom scalar — it maps `BigIntegerField` / `PositiveBigIntegerField` to `int` and reuses Strawberry's own `Upload` — so it has no registration helper to model on.

### From `graphene-django` — no precedent to borrow

`graphene-django` (`/Users/riordenweber/projects/django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/`) uses Graphene's `Scalar` subclass mechanism; there is no `StrawberryConfig` analogue.

### Explicitly do not borrow

A `dst.Schema(...)` wrapper pre-populating `config=`, a public `SCALAR_MAP` constant consumers spread into their own `StrawberryConfig`, and a module-level `STRAWBERRY_DEFAULT_CONFIG` instance are refused; each reason is in [`spec-025-scalar_map_helper-0_0_7-rationale.md`][spec-025-rationale] [Borrowing posture][rationale-borrowing].

## User-facing API

One symbol: `strawberry_config(*, extra_scalar_map=None, **config_kwargs) -> StrawberryConfig`, defined in [`django_strawberry_framework/scalars.py`][scalars] and re-exported from `django_strawberry_framework`. `extra_scalar_map` is keyword-only; every other keyword argument is forwarded to the upstream [`StrawberryConfig(...)`][config] constructor unchanged.

### Default usage — package scalars only

```python path=null start=null
import strawberry

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    finalize_django_types,
    strawberry_config,
)

# ... import every module that declares DjangoType subclasses ...

finalize_django_types()

_optimizer = DjangoOptimizerExtension()
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(),
    extensions=[lambda: _optimizer],
)
```

`DjangoSchema(...)` takes the same `config=` argument. The optimizer entry is a module-level singleton wrapped in a factory (the documented shape) and is orthogonal to this spec, which owns `config=` alone.

The returned `StrawberryConfig.scalar_map` carries one entry, `{BigInt: <BigInt ScalarDefinition>}`. Strawberry consults it at schema-construction time to resolve `BigInt` annotations anywhere in the schema; the consumer writes `id: BigInt` or `@strawberry.field def big_id(self) -> BigInt: ...` as plain annotations.

### Composing with consumer-defined scalars

```python path=null start=null
from typing import NewType
import strawberry
from django_strawberry_framework import strawberry_config

MyULID = NewType("MyULID", str)
_MY_ULID_DEF = strawberry.scalar(name="MyULID", serialize=str, parse_value=str)

schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(extra_scalar_map={MyULID: _MY_ULID_DEF}),
)
```

The factory merges `extra_scalar_map` over the package's defaults. A key already in `_PACKAGE_SCALAR_MAP` raises `ValueError` naming the colliding keys and the recourse (register the consumer scalar under a different `NewType` / class) — see [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions).

### Composing with custom `StrawberryConfig` options

Every other [`StrawberryConfig`][config] field (`auto_camel_case`, `name_converter`, `default_resolver`, `relay_max_results`, `relay_use_legacy_global_id`, `disable_field_suggestions`, `info_class`, `enable_experimental_incremental_execution`, `batching_config`) is passed directly to `strawberry_config(...)`:

```python path=null start=null
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(auto_camel_case=False, relay_max_results=200),
    extensions=[lambda: _optimizer],
)
```

The two paths combine on one call:

```python path=null start=null
schema = strawberry.Schema(
    query=Query,
    config=strawberry_config(
        extra_scalar_map={MyULID: _MY_ULID_DEF},
        relay_max_results=200,
    ),
)
```

The one field the helper does NOT forward is `scalar_map`: the helper owns it, and passing `scalar_map=` raises `ValueError` (see [Error shapes](#error-shapes)) so the [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions) collision policy cannot be bypassed.

### Error shapes

- `strawberry_config(extra_scalar_map={BigInt: <some other ScalarDefinition>})` → `ValueError("strawberry_config(extra_scalar_map=...) cannot redeclare package-defined scalars: BigInt. Define a Strawberry custom scalar of a different NewType / class to register under a separate key.")`.
- `strawberry_config(scalar_map=...)` → `ValueError("strawberry_config() owns scalar_map; pass consumer scalars with extra_scalar_map=...")`, for any value including `{}` and `None`: the kwarg name is owned by the helper, not the value.
- `strawberry_config(extra_scalar_map=<a mapping that raises while being read, or whose keys raise while being hashed or compared>)` → `ValueError("strawberry_config(extra_scalar_map=...) must be materializable with keys that hash and compare safely; got <safe repr>.")`, chained `from` whatever the consumer code raised. The guard spans materialization, the collision intersection and the merge — every operation that dispatches into consumer key code — and catches `BaseException`, so a consumer object can never substitute its own exception for the factory's.
- `strawberry_config(extra_scalar_map={"not a NewType or class": <ScalarDefinition>})` → no validation; Strawberry's `scalar_map` contract accepts any key (`Mapping[object, ScalarDefinition]` at [`.venv/lib/python3.14/site-packages/strawberry/schema/config.py #"scalar_map: Mapping[object, ScalarDefinition]"`][config]), and the factory does not guess what "any type" excludes.
- `strawberry_config(unknown_kwarg=True)` → no helper-level validation; upstream `StrawberryConfig(...)` raises its own `TypeError`. The supported kwarg set is Strawberry's and would drift if the helper listed it.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The spec's canonical name is the structured `spec-025-scalar_map_helper-0_0_7.md`. The **filename** is canonical, the **directory** is not: a reference points at whichever path the file has — `docs/SPECS/` with its `-terms.csv` and `-rationale.md` companions under `docs/SPECS/appx/` — and an archive pass rewrites every reference in one sweep.

Rationale: [Decision 1][rationale-d1].

### Decision 2 — Helper API shape and module location

The helper is a **factory function**, `def strawberry_config(*, extra_scalar_map: Mapping[object, ScalarDefinition] | None = None, **config_kwargs: Any) -> StrawberryConfig`. `extra_scalar_map` is keyword-only (the leading `*,`); `**config_kwargs` is forwarded to upstream [`StrawberryConfig(...)`][config] unchanged, except `scalar_map=`, which raises `ValueError` because the helper owns that field. It lives in [`django_strawberry_framework/scalars.py`][scalars], beside the `BigInt` definition it composes, and is re-exported as `from django_strawberry_framework import strawberry_config`. Each call returns a fresh `StrawberryConfig` with a fresh `scalar_map` dict.

Rationale: [Decision 2][rationale-d2].

### Decision 3 — `BigInt` redefinition as bare `NewType` + `ScalarDefinition`

`BigInt` is a bare `NewType("BigInt", int)`. Its `ScalarDefinition` is built via the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload — the `cls is None and name is not None` branch at [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`][scalar] — which returns a `ScalarDefinition` without entering the warning-emitting `wrap()` body.

Shape of [`django_strawberry_framework/scalars.py`][scalars] (comments and docstrings elided):

```python path=null start=null
def _parse_bigint(value: object) -> int: ...      # int.__int__ / str.__str__ normalization
def _serialize_bigint(value: object) -> str: ...  # int.__repr__ normalization

BigInt = NewType("BigInt", int)

_BIGINT_SCALAR_DEFINITION: ScalarDefinition = strawberry.scalar(
    name="BigInt",
    serialize=_serialize_bigint,
    parse_value=_parse_bigint,
)

_PACKAGE_SCALAR_MAP: dict[object, ScalarDefinition] = {
    BigInt: _BIGINT_SCALAR_DEFINITION,
}


def strawberry_config(
    *,
    extra_scalar_map: Mapping[object, ScalarDefinition] | None = None,
    **config_kwargs: Any,
) -> StrawberryConfig:
    if "scalar_map" in config_kwargs:
        raise ValueError(
            "strawberry_config() owns scalar_map; pass consumer scalars with extra_scalar_map=...",
        )
    try:
        extra: dict[object, ScalarDefinition] = (
            {} if extra_scalar_map is None else dict(extra_scalar_map)
        )
        collisions = _PACKAGE_SCALAR_MAP.keys() & extra.keys()
        merged: dict[object, ScalarDefinition] = dict(_PACKAGE_SCALAR_MAP)
        merged.update(extra)
    except BaseException as exc:
        raise ValueError(
            "strawberry_config(extra_scalar_map=...) must be materializable with "
            f"keys that hash and compare safely; got {_safe_arg_repr(extra_scalar_map)}.",
        ) from exc
    if collisions:
        raise ValueError(
            "strawberry_config(extra_scalar_map=...) cannot redeclare package-defined scalars: "
            f"{', '.join(sorted(_safe_scalar_map_key_label(k) for k in collisions))}. "
            "Define a Strawberry custom scalar of a different NewType / class "
            "to register under a separate key.",
        )
    return StrawberryConfig(scalar_map=merged, **config_kwargs)


def _safe_scalar_map_key_label(key: object) -> str:
    try:
        name = getattr(key, "__name__", None)
    except BaseException:
        name = None
    if isinstance(name, str):
        return str.__str__(name)
    return _safe_arg_repr(key)
```

Three properties of that body are contract, not incidental spelling:

- **Absent is distinguished from empty by an explicit `is None` test**, never by truthiness: `if extra_scalar_map` would let a consumer mapping's `__bool__` decide which branch runs.
- **Every dispatch into consumer key code is guarded** — materialization, the key-set intersection and the merge (which re-hash and, on a hash collision with a package key, compare the consumer's keys) — and the guard raises the factory's own `ValueError` chained from the original.
- **Collision keys are labelled through `_safe_scalar_map_key_label`**, which tolerates a `__name__` that raises, rejects a non-`str` `__name__`, and reads a `str`-subclass `__name__` through the base `str` slot so the subclass's `__str__` / `__format__` / `__lt__` never run while the message is assembled.

Rationale: [Decision 3][rationale-d3].

### Decision 4 — Conflict resolution for `extra_scalar_map` collisions

A consumer `extra_scalar_map` key already present in `_PACKAGE_SCALAR_MAP` makes `strawberry_config(...)` raise `ValueError("strawberry_config(extra_scalar_map=...) cannot redeclare package-defined scalars: <names>. Define a Strawberry custom scalar of a different NewType / class to register under a separate key.")` — a hard error, with no override path.

`ValueError` is the factory's **only** rejection class: the collision, the owned `scalar_map=` kwarg, and a mapping or key that raises inside the guarded region. The guard is what makes that uniformity a contract — consumer key code is contained rather than allowed to replace the factory's exception. [`ConfigurationError`][glossary-configurationerror] is deliberately not used: each rejection is a consumer-input mistake at helper-call time, not a `DjangoType`-creation or finalization error. The messages are enumerated in [Error shapes](#error-shapes).

Rationale: [Decision 4][rationale-d4].

### Decision 5 — Migration posture: hard break in alpha

Any schema that resolves to `BigInt` — through a direct annotation OR through a [`DjangoType`][glossary-djangotype] field backed by `BigIntegerField` / `PositiveBigIntegerField` via the [`Specialized scalar conversions`][glossary-specialized-scalar-conversions] converter table — must be constructed with `config=strawberry_config()`. Without it, schema construction fails with Strawberry's `TypeError` ending `Unexpected type 'django_strawberry_framework.scalars.BigInt'`. There is no deprecation window and no shim re-registering `BigInt` through the class-direct path. The surface is broader than "code that names `BigInt`": the converter table names it for every `DjangoType` with those columns. A schema that resolves no `BigInt` owes no `config=`.

Rationale: [Decision 5][rationale-d5].

### Decision 6 — No warning suppression at the definition site

[`django_strawberry_framework/scalars.py`][scalars] imports no `warnings` and suppresses nothing: the no-warning overload of [Decision 3](#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition) never enters the deprecation path, so the package import is clean by construction. `test_package_import_does_not_emit_strawberry_deprecation_warning` pins that under `-W error::DeprecationWarning`.

Rationale: [Decision 6][rationale-d6].

### Decision 7 — Test placement and shape

The factory's tests live in [`tests/test_scalars.py`][test-scalars], the package-test partner of [`django_strawberry_framework/scalars.py`][scalars]; there is no `tests/test_config.py`. One pytest item per test, no `pytest.mark.parametrize` fan-out. The file is shared with the other scalars' tests, so its total item count is not this spec's to pin — only the named items in the [Test plan](#test-plan) are.

The `BigInt` round trip through a `strawberry_config()`-registered schema is pinned live, per the live-HTTP-priority rule: fakeshop's served schema passes `config=strawberry_config()` and [`examples/fakeshop/test_query/test_scalars_api.py`][test-scalars-api] queries its `BigIntegerField` / `PositiveBigIntegerField` columns over `/graphql/` in both directions. What stays in-process is what no request can express: factory construction, merge, collision and passthrough behavior, and hostile consumer objects. The `BigInt`-resolving schemas left in [`tests/types/test_converters.py`][test-converters] also build through `config=strawberry_config()`, so a registration-layer regression surfaces in both tiers.

Rationale: [Decision 7][rationale-d7].

### Decision 8 — Version posture: this card ships inside the `0.0.7` cut

`DONE-025-0.0.7` is one card of the joint `0.0.7` cut that [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] [Decision 9][spec-023-decision-9] states. Its `CHANGELOG.md` entries append to the shared `## [0.0.7] - 2026-05-27` section: one `### Added` bullet for the factory, one `### Changed` bullet for the breaking registration move, one `### Removed` bullet for the suppression block.

The version bump that closes the cut belongs to the last card to ship in it, NOT to this card. This card touches neither `__version__` at [`django_strawberry_framework/__init__.py #"__version__ = "`][django-strawberry-framework-init] (the single version source) nor the pinned assertion at [`tests/base/test_init.py #"def test_version"`][test-init].

Rationale: [Decision 8][rationale-d8].

### Decision 9 — Example-app migration scope

The fakeshop edit is [`examples/fakeshop/config/schema.py`][schema], the schema the project serves at `/graphql/`: `strawberry_config` on the `from django_strawberry_framework import (...)` block and `config=strawberry_config()` on the constructor call. That names a role, not a count of the project's schema-construction calls; which other schemas carry the registration is owned by [Decision 5](#decision-5--migration-posture-hard-break-in-alpha)'s rule. The constructor class, the roots and the `extensions=` entry are other cards' business.

The per-app `schema.py` modules ([`library`][schema-library], [`products`][schema-products] and the rest) need no edit: each declares a `@strawberry.type class Query` and leaves construction to whatever composes it.

Rationale: [Decision 9][rationale-d9].

## Implementation plan

| Slice | Files |
| --- | --- |
| 1 — Helper module + `BigInt` definition | [`django_strawberry_framework/scalars.py`][scalars], [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] |
| 2 — Tests | [`tests/test_scalars.py`][test-scalars], [`tests/base/test_init.py`][test-init], [`tests/types/test_converters.py`][test-converters] |
| 3 — Example-app migration | [`examples/fakeshop/config/schema.py`][schema] |
| 4 — Docs | [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`GOAL.md`][goal], [`TODAY.md`][today], [`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv`][spec-025-terms] |
| 5 — KANBAN + CHANGELOG | [`KANBAN.md`][kanban], [`CHANGELOG.md`][changelog] |

## Edge cases and constraints

- **Strawberry floor carries the no-warning overload.** The `cls is None and name is not None` branch at [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`][scalar] exists across the range [`pyproject.toml #"strawberry-graphql>="`][pyproject] declares; that declared constraint, not any resolved version, is the contract that guarantees it.
- **`BigInt` is not isinstance-checkable.** `isinstance(x, BigInt)` raises `TypeError` because a `NewType` is not a type; the package does not document `BigInt` as isinstance-checkable.
- **The returned `scalar_map` is a fresh `dict`.** The field type accepts any `Mapping`; the factory builds a new `dict(_PACKAGE_SCALAR_MAP)` and merges the materialized extra map into it, so neither the package map nor the caller's mapping is shared with the result.
- **Independent return value semantics.** Each call returns a new `StrawberryConfig` with a new `scalar_map` dict; mutating one call's result (`config.scalar_map[X] = ...`) does not leak into the next. Pinned by `test_strawberry_config_independent_call_returns_independent_instance`.
- **`extra_scalar_map={}` and `extra_scalar_map=None` produce the same `scalar_map`, but not by the same route.** Absence is decided by `is None`; an empty mapping is materialized into an empty `dict`. The equivalence is an outcome, never a truthiness test. Pinned by `test_strawberry_config_accepts_none_extra_scalar_map` and `test_strawberry_config_accepts_empty_extra_scalar_map`.
- **Consumer key code is contained.** `dict(extra_scalar_map)` runs consumer `keys()` / `__iter__` / `__getitem__` / `__hash__`; the intersection and the merge re-run `__hash__` and, on a hash collision with a package key, `__eq__`. All of it sits inside the `BaseException` guard and surfaces as the factory's `ValueError` chained from the original. Pinned by `test_strawberry_config_rejects_unmaterializable_extra_scalar_map` and `test_strawberry_config_hostile_key_eq_raising_is_contained`.
- **`extra_scalar_map` mutation post-call.** The factory copies the caller's mapping, so neither the call nor a later mutation of that mapping touches the other side. Pinned by `test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict`.
- **`**config_kwargs` passthrough semantics.** Every kwarg other than `scalar_map` is forwarded verbatim — no translation, no defaults, no validation; a typo (`relay_max_resluts=200`) surfaces as upstream's own `TypeError`. Pinned by `test_strawberry_config_forwards_auto_camel_case_kwarg`, `test_strawberry_config_forwards_relay_max_results_kwarg`, `test_strawberry_config_combines_extra_scalar_map_and_config_kwargs` and `test_strawberry_config_unknown_kwarg_raises_typeerror_from_upstream`.
- **Underscore-prefixed `StrawberryConfig` kwargs pass through unchanged.** `StrawberryConfig` declares `_unsafe_disable_same_type_validation: bool = False` ([`.venv/lib/python3.14/site-packages/strawberry/schema/config.py #"_unsafe_disable_same_type_validation"`][config]) as a real `__init__` kwarg; the helper does not special-case it.
- **`scalar_map=` is rejected even when empty.** `strawberry_config(scalar_map={})` and `strawberry_config(scalar_map=None)` both raise `ValueError`. Pinned by `test_strawberry_config_rejects_scalar_map_kwarg`.
- **Keyword-only invocation.** `strawberry_config({BigInt: alt_def})` raises `TypeError` from Python itself because the signature begins with `*,`; no dedicated test.
- **The name-only overload does not default `parse_value`.** On the `cls is None and name is not None` overload, omitting `parse_value=` leaves `ScalarDefinition.parse_value = None` (only the class-passing overload defaults it to `cls`). The helper does not validate consumer `ScalarDefinition`s (Strawberry owns that contract); consumers building their own definitions on this overload pass `parse_value=` explicitly.
- **Collision-error message stability.** The message names each colliding key through `_safe_scalar_map_key_label`: the key's `__name__` when it is a `str` (the `NewType` and class cases, read through the base `str` slot), otherwise `_safe_arg_repr`. A key may have no `__name__`, a `__name__` descriptor that raises, a non-`str` `__name__`, or a `str`-subclass `__name__` with hostile dunders; none may turn the collision rejection into a different error. The `NewType`-keyed format is pinned by `test_strawberry_config_collision_with_package_scalar_raises_value_error`; the hostile-metadata paths by `test_strawberry_config_collision_message_survives_hostile_key`, `test_scalar_collision_label_falls_back_when_class_name_metadata_is_unreadable` and `test_safe_scalar_map_key_label_normalizes_str_subclass_name`.
- **`__all__` ordering.** The package `__all__` is sorted isort-style (ruff `RUF022`): SCREAMING_SNAKE_CASE names, then CamelCase, then the rest, each group in ASCII order. `"strawberry_config"` is the last element because `s` sorts after every other lowercase initial the tuple carries. The exact tuple is pinned by `test_public_api_surface_is_pinned` in [`tests/base/test_init.py`][test-init], which is where to read it.
- **Coverage at 100%.** Every branch of `strawberry_config` and `_safe_scalar_map_key_label` is covered by the [Test plan](#test-plan) items; there is no uncoverable branch, and [`pyproject.toml`][pyproject] `[tool.coverage.report] fail_under = 100` gates it.

## Test plan

Package tests live in [`tests/test_scalars.py`][test-scalars] per [Decision 7](#decision-7--test-placement-and-shape); system-under-test is [`django_strawberry_framework/scalars.py::strawberry_config`][scalars] and the `BigInt` registration shape. One pytest item per test.

### `tests/test_scalars.py` — `strawberry_config()` factory, scalar-map tests

- `test_strawberry_config_returns_strawberry_config_instance` — `isinstance(strawberry_config(), StrawberryConfig)`. Pins [Decision 2](#decision-2--helper-api-shape-and-module-location)'s return type.
- `test_strawberry_config_default_scalar_map_includes_bigint` — `BigInt in result.scalar_map`, the value is a `ScalarDefinition`, and its `name == "BigInt"`. Pins [Decision 3](#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition).
- `test_strawberry_config_accepts_none_extra_scalar_map` — `extra_scalar_map=None` yields `len(result.scalar_map) == 1` with `BigInt` present.
- `test_strawberry_config_accepts_empty_extra_scalar_map` — `extra_scalar_map={}` yields the same.
- `test_strawberry_config_rejects_unmaterializable_extra_scalar_map` — a `Mapping` whose `__getitem__` and `__repr__` raise; asserts `ValueError` matching `"must be materializable.*unprintable _BrokenMapping"`.
- `test_strawberry_config_merges_extra_scalar_map` — `CustomScalar = NewType("CustomScalar", str)` with a `strawberry.scalar(name="CustomScalar", ...)` definition; asserts two entries, both keys present, and the consumer definition stored by identity.
- `test_strawberry_config_extra_scalar_map_does_not_mutate_caller_dict` — the caller's dict equals its pre-call copy.
- `test_scalar_collision_label_falls_back_when_class_name_metadata_is_unreadable` — a class whose metaclass raises on `__name__` is labelled by its guarded repr.
- `test_strawberry_config_collision_with_package_scalar_raises_value_error` — `extra_scalar_map={BigInt: alt_def}` raises `ValueError` whose message contains `"BigInt"` and `"cannot redeclare"`. Pins [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions).
- `test_strawberry_config_collision_message_survives_hostile_key` — a key hashing and comparing equal to `BigInt` with a raising `__repr__`: the label is `"<unprintable _HostileKey>"` and the factory still raises the collision `ValueError`.
- `test_strawberry_config_hostile_key_eq_raising_is_contained` — a key hashing like `BigInt` whose `__eq__` raises: `ValueError` matching `"must be materializable"`, message containing `"hash and compare safely"`, `RuntimeError` as `__cause__`.
- `test_safe_scalar_map_key_label_normalizes_str_subclass_name` — a `str`-subclass `__name__` with raising `__str__` / `__format__` / `__lt__` comes back as a plain `str` that sorts and joins safely.
- `test_strawberry_config_independent_call_returns_independent_instance` — two calls give distinct configs and distinct `scalar_map` dicts; mutating one leaves the other unchanged.

### `tests/test_scalars.py` — `**config_kwargs` passthrough tests

- `test_strawberry_config_forwards_auto_camel_case_kwarg` — `strawberry_config(auto_camel_case=False).name_converter.auto_camel_case is False`, and the default is `True`. The assertion reads `name_converter.auto_camel_case` because `auto_camel_case` is declared as a dataclass `InitVar` on `StrawberryConfig`; `__post_init__` applies it to the name converter.
- `test_strawberry_config_forwards_relay_max_results_kwarg` — `relay_max_results=200` lands on the result (an integer field, structurally distinct from the bool flag).
- `test_strawberry_config_combines_extra_scalar_map_and_config_kwargs` — `extra_scalar_map=` and `relay_max_results=200` on one call; both apply.
- `test_strawberry_config_rejects_scalar_map_kwarg` — `scalar_map={}` raises `ValueError` naming `"scalar_map"` and `"extra_scalar_map"`; `scalar_map=None` and a populated `scalar_map={BigInt: alt_def}` raise too. Pins [Error shapes](#error-shapes).
- `test_strawberry_config_unknown_kwarg_raises_typeerror_from_upstream` — an unknown kwarg raises `TypeError`; the message is not asserted (it is upstream's wording).

### `tests/test_scalars.py` — import surface

- `test_package_import_does_not_emit_strawberry_deprecation_warning` — the `-W error::DeprecationWarning` subprocess import exits 0. Pins [Decision 6](#decision-6--no-warning-suppression-at-the-definition-site).
- `test_bigint_is_importable_from_top_level` — `from django_strawberry_framework import BigInt` resolves.

### Live tier — the registered round trip

In [`examples/fakeshop/test_query/test_scalars_api.py`][test-scalars-api], over the served schema built with `config=strawberry_config()`: `test_scalar_specimen_every_field_wire_format_over_http` pins outbound decimal-string serialization for both `BigInt` columns, and `test_scalar_specimen_bigint_input_decimal_string_argument_over_http` pins the inbound decimal-string parse.

### Other files

- [`tests/base/test_init.py`][test-init] `test_public_api_surface_is_pinned` — exact `__all__` tuple, `"strawberry_config"` last.
- [`tests/types/test_converters.py`][test-converters] — `test_bigint_in_input_position_with_null_via_schema_execution` and `test_bigint_resolver_returning_bool_raises_via_schema_execution` build with `config=strawberry_config()`; `test_big_auto_field_still_maps_to_int` builds without it.

## Doc updates

- [`docs/GLOSSARY.md`][glossary] (rendered from the glossary DB; edit the DB, then regenerate):
  - [`strawberry_config`][glossary-strawberry-config] entry, `shipped (0.0.7)`: the factory, its `extra_scalar_map=` composition, the `**config_kwargs` passthrough, the `scalar_map=` and collision `ValueError`s, and the fresh-instance-per-call guarantee.
  - [`BigInt scalar`][glossary-bigint-scalar] entry: a paragraph saying consumers register `BigInt` via `strawberry_config` on their schema call, direct annotations are unchanged, and the requirement covers converter-backed `BigIntegerField` / `PositiveBigIntegerField` fields.
  - [Public exports][glossary-public-exports] bullet and [Index][glossary-index] row for `strawberry_config`.
- [`docs/README.md`][readme]: the [Quick start][readme-quick-start] and [Schema setup][readme-schema-setup] blocks import `strawberry_config` and pass `config=strawberry_config()`.
- [`GOAL.md`][goal]: the [`schema.py`][goal-schemapy] showcase imports `strawberry_config` and passes `config=strawberry_config()`; the [Migration shape][goal-migration-shape] per-stack diffs do not.
- [`TODAY.md`][today]: the `config/schema.py` block under [What you can build today][today-what-you-can-build-today] imports `strawberry_config` and passes `config=strawberry_config()`.
- [`docs/TREE.md`][tree]: no structural row; [`scripts/build_tree_md.py`][build-tree] renders the `scalars.py` line from the module docstring.
- [`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv`][spec-025-terms]: one row per project term this spec links, `strawberry_config` included; `StrawberryConfig` (upstream) is not a package glossary term and has no row.
- [`KANBAN.md`][kanban] (DB-rendered): the `DONE-025-0.0.7` card in the Done column, naming this spec by its structured filename.
- [`CHANGELOG.md`][changelog]: the `## [0.0.7] - 2026-05-27` `### Added` / `### Changed` / `### Removed` bullets per [Decision 8](#decision-8--version-posture-this-card-ships-inside-the-007-cut).

## Risks and open questions

Each item names a live constraint the contract depends on.

- **Strawberry's no-warning overload is the documented, recommended path.** [`strawberry.scalar(name=..., serialize=..., parse_value=...)`](https://strawberry.rocks) returning a `ScalarDefinition` is what Strawberry's own deprecation message points consumers at.
- **`isinstance(value, BigInt)` is not supported by `NewType`.**
- **`extra_scalar_map` collisions with later package-defined scalars.** A key becomes collision-prone only when it enters `_PACKAGE_SCALAR_MAP`, and only a scalar the package must *register* ever does: a scalar Strawberry's `DEFAULT_SCALAR_REGISTRY` already carries (`Upload`) needs no entry and can never collide. The map holds exactly `{BigInt: ...}`. A later package-custom scalar grows it, and a consumer who had registered their own definition under that key then hits the [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions) hard error — the intended loud failure, and the reason the map's contents are part of the helper's documented contract.
- **Strawberry version pin compatibility.** The declared constraint at [`pyproject.toml #"strawberry-graphql>="`][pyproject] — not any one resolved version — guarantees the `cls is None and name is not None` overload; [`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`][scalar] confirms the resolved top of the range. Only an upstream removal could lose it, and that breaks the package import loudly.
- **The registration path is exercised over a real request, not only in-process.** The schema fakeshop serves at `/graphql/` passes `config=strawberry_config()` and resolves `BigIntegerField` / `PositiveBigIntegerField` columns as `BigInt`; that live tier is where a registration regression surfaces first.
- **Suppression-free import regression detection.** `test_package_import_does_not_emit_strawberry_deprecation_warning` at [`tests/test_scalars.py #"test_package_import_does_not_emit_strawberry_deprecation_warning"`][test-scalars] uses a `-W error::DeprecationWarning` subprocess, so a reintroduced deprecation along the registration path fails CI.

## Out of scope (explicitly tracked elsewhere)

- Composing Strawberry extensions through this helper; `extensions=` belongs on the schema constructor. No card.
- Auto-discovery of the package config via a Django settings key; no feature needs it.
- [`Upload`][glossary-upload-scalar]: shipped by `DONE-037-0.0.11`; it needs no `_PACKAGE_SCALAR_MAP` entry and no change to this helper.
- A `dst.Schema(...)` wrapper, or a public `SCALAR_MAP` re-export of the package map. Excluded by [Decision 2](#decision-2--helper-api-shape-and-module-location).
- Editing the converter table at [`django_strawberry_framework/types/converters.py::SCALAR_MAP`][converters].
- Renaming or aliasing `BigInt`.

## Definition of done

1. [`docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`][spec-025] (this document) carries the structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming), with [`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv`][spec-025-terms] anchoring every project-specific term the spec links to its [`docs/GLOSSARY.md`][glossary] heading (per [`docs/SPECS/NEXT.md`][next] Step 7).
2. [`django_strawberry_framework/scalars.py`][scalars] defines `BigInt = NewType("BigInt", int)`, `_BIGINT_SCALAR_DEFINITION` via `strawberry.scalar(name="BigInt", serialize=_serialize_bigint, parse_value=_parse_bigint)`, `_PACKAGE_SCALAR_MAP = {BigInt: _BIGINT_SCALAR_DEFINITION}`, and `strawberry_config(*, extra_scalar_map: Mapping[object, ScalarDefinition] | None = None, **config_kwargs: Any) -> StrawberryConfig` per [Decision 2](#decision-2--helper-api-shape-and-module-location) and [Decision 3](#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition): `scalar_map=` rejected with `ValueError`, absence decided by `is None`, every dispatch into consumer key code guarded so the factory's `ValueError` cannot be displaced (per [Error shapes](#error-shapes)), and collision keys labelled through `_safe_scalar_map_key_label`. The module imports no `warnings` and suppresses nothing ([Decision 6](#decision-6--no-warning-suppression-at-the-definition-site)). `_parse_bigint` and `_serialize_bigint` keep spec-017's **wire format** — decimal string in, decimal string out — while normalizing hostile `int` / `str` subclasses through the base descriptors.
3. [`django_strawberry_framework/__init__.py`][django-strawberry-framework-init] re-exports `strawberry_config` beside `BigInt` from `.scalars`, and `"strawberry_config"` is the **last** element of `__all__`.
4. [`tests/test_scalars.py`][test-scalars] carries every test named under the two `strawberry_config()` factory headings of the [Test plan](#test-plan), one pytest item each, no `pytest.mark.parametrize` fan-out.
5. [`tests/test_scalars.py`][test-scalars] `test_package_import_does_not_emit_strawberry_deprecation_warning` passes: the import is clean under `-W error::DeprecationWarning` per [Decision 6](#decision-6--no-warning-suppression-at-the-definition-site).
6. [`tests/base/test_init.py`][test-init] `test_public_api_surface_is_pinned` ends the pinned `__all__` tuple with `"strawberry_config"`.
6a. [`tests/types/test_converters.py`][test-converters]: every schema that resolves to `BigInt` is built with `config=strawberry_config()`, and `strawberry_config` is on the file's package import block; `test_big_auto_field_still_maps_to_int` resolves upstream `Int` and passes no `config=`. Which `BigInt` cases live in this file rather than in live `/graphql/` coverage is owned by the live-coverage rule.
6b. [`tests/test_scalars.py`][test-scalars] module docstring names the live modules that own wire-reachable `BigInt` behavior and lists `strawberry_config()` construction among what stays in-process.
6c. [`examples/fakeshop/test_query/test_scalars_api.py`][test-scalars-api] pins the `BigInt` round trip over `/graphql/` through the served `config=strawberry_config()` schema in both directions (the [Test plan](#test-plan) live-tier items).
7. [`examples/fakeshop/config/schema.py`][schema] carries `strawberry_config` on its package import block and `config=strawberry_config()` on the served schema's constructor call per [Decision 9](#decision-9--example-app-migration-scope).
8. No `examples/fakeshop/apps/*/schema.py` module ([`library`][schema-library], [`products`][schema-products] and the rest) constructs a schema, so none carries a `config=`.
9. [`docs/GLOSSARY.md`][glossary] carries the [`strawberry_config`][glossary-strawberry-config] entry, the [`BigInt scalar`][glossary-bigint-scalar] registration paragraph, and `strawberry_config` in the `Public exports` list and the `Index` table, per [Doc updates](#doc-updates).
9a. [`docs/SPECS/appx/spec-025-scalar_map_helper-0_0_7-terms.csv`][spec-025-terms] carries a `strawberry_config,strawberry_config,...` row, and [`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`][check-spec-glossary] exits 0.
10. The [Quick start][readme-quick-start] and [Schema setup][readme-schema-setup] blocks in [`docs/README.md`][readme] carry `config=strawberry_config()` with `strawberry_config` on their import line.
11. [`GOAL.md`][goal]'s [`schema.py`][goal-schemapy] showcase imports `strawberry_config` and passes `config=strawberry_config()`.
12. [`TODAY.md`][today]'s `config/schema.py` block under [What you can build today][today-what-you-can-build-today] imports `strawberry_config` and passes `config=strawberry_config()`.
13. This spec adds no module under `django_strawberry_framework/` and no file under `tests/`, so it owes [`docs/TREE.md`][tree] no structural row; the `scalars.py` line follows the module docstring through the renderer.
14. This spec changes no consumer-facing primitive name, so it owes the root [`README.md`][readme-repo] no walkthrough change; [`docs/README.md`][readme]'s Quick start is the schema-setup walkthrough.
15. [`KANBAN.md`][kanban] records `DONE-025-0.0.7` in the Done column, naming this spec by its structured filename per [Decision 1](#decision-1--spec-filename-and-canonical-naming).
16. [`CHANGELOG.md`][changelog]'s `## [0.0.7] - 2026-05-27` section carries this card's `### Added`, `### Changed` (breaking-change wording with the before/after diff) and `### Removed` bullets in the shared subsections.
17. The version bump is not this card's per [Decision 8](#decision-8--version-posture-this-card-ships-inside-the-007-cut).
18. This spec contributes exactly one name to the package `__all__` beyond spec-017's `BigInt`: `strawberry_config`.
19. Package coverage stays at 100% (`pyproject.toml [tool.coverage.report] fail_under = 100`), gated by CI.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[goal]: ../../GOAL.md
[goal-migration-shape]: ../../GOAL.md#migration-shape
[goal-schemapy]: ../../GOAL.md#schemapy
[kanban]: ../../KANBAN.md
[pyproject]: ../../pyproject.toml
[readme-repo]: ../../README.md
[today]: ../../TODAY.md
[today-what-you-can-build-today]: ../../TODAY.md#what-you-can-build-today

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[glossary-bigint-scalar]: ../GLOSSARY.md#bigint-scalar
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-index]: ../GLOSSARY.md#index
[glossary-public-exports]: ../GLOSSARY.md#public-exports
[glossary-scalar-field-conversion]: ../GLOSSARY.md#scalar-field-conversion
[glossary-specialized-scalar-conversions]: ../GLOSSARY.md#specialized-scalar-conversions
[glossary-strawberry-config]: ../GLOSSARY.md#strawberry_config
[glossary-upload-scalar]: ../GLOSSARY.md#upload-scalar
[readme]: ../README.md
[readme-quick-start]: ../README.md#quick-start
[readme-relay-node]: ../README.md#relay-node
[readme-schema-setup]: ../README.md#schema-setup
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[next]: NEXT.md
[rationale-borrowing]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#borrowing-posture--explicitly-do-not-borrow
[rationale-d1]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d2]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-2--helper-api-shape-and-module-location
[rationale-d3]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition
[rationale-d4]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-4--conflict-resolution-for-extra_scalar_map-collisions
[rationale-d5]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-5--migration-posture-hard-break-in-alpha
[rationale-d6]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-6--no-warning-suppression-at-the-definition-site
[rationale-d7]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-7--test-placement-and-shape
[rationale-d8]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-8--version-posture-this-card-ships-inside-the-007-cut
[rationale-d9]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md#decision-9--example-app-migration-scope
[spec-017]: spec-017-deferred_scalars-0_0_6.md
[spec-023]: spec-023-multi_db-0_0_7.md
[spec-023-decision-9]: spec-023-multi_db-0_0_7.md#decision-9--joint-007-cut
[spec-025]: spec-025-scalar_map_helper-0_0_7.md
[spec-025-rationale]: appx/spec-025-scalar_map_helper-0_0_7-rationale.md
[spec-025-terms]: appx/spec-025-scalar_map_helper-0_0_7-terms.csv

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[converters]: ../../django_strawberry_framework/types/converters.py
[django-strawberry-framework-init]: ../../django_strawberry_framework/__init__.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[scalars]: ../../django_strawberry_framework/scalars.py

<!-- tests/ -->
[test-converters]: ../../tests/types/test_converters.py
[test-init]: ../../tests/base/test_init.py
[test-scalars]: ../../tests/test_scalars.py

<!-- examples/ -->
[schema]: ../../examples/fakeshop/config/schema.py
[schema-library]: ../../examples/fakeshop/apps/library/schema.py
[schema-products]: ../../examples/fakeshop/apps/products/schema.py
[test-scalars-api]: ../../examples/fakeshop/test_query/test_scalars_api.py

<!-- scripts/ -->
[build-tree]: ../../scripts/build_tree_md.py
[check-spec-glossary]: ../../scripts/check_spec_glossary.py

<!-- .venv/ -->
[config]: ../../.venv/lib/python3.14/site-packages/strawberry/schema/config.py
[scalar]: ../../.venv/lib/python3.14/site-packages/strawberry/types/scalar.py

<!-- External -->
