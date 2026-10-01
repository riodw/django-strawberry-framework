# Rationale: spec-025 — Warning-free scalar registration via `StrawberryConfig.scalar_map`

Deliberative companion to [`spec-025-scalar_map_helper-0_0_7.md`][spec-025]. The spec states the contract; this file holds why each of its nine Decisions is shaped the way it is, the alternatives each rejected, and the reasons behind the spec's `Explicitly do not borrow` refusals.

## Decision 1 — Spec filename and canonical naming

Spec text: [Decision 1][spec-025-d1].

### Justification

- The structured `spec-<NNN>-<topic>-<X_Y_Z>.md` convention pinned in [`docs/SPECS/NEXT.md`][next] Step 6 bakes the card number and target patch into the filename, so archived specs sort with their cohort under `docs/SPECS/`.
- This Decision is enforcement, not innovation: it applies the convention every structured spec follows.

### Alternatives considered (and rejected)

- **An unnumbered `docs/spec-scalar_map_helper.md`.** Rejected: diverges from the structured naming convention and would sort apart from its numbered cohort.
- **A longer topic slug like `strawberry_config_factory`.** Rejected: longer than necessary; `scalar_map_helper` already names the architectural intent.

## Decision 2 — Helper API shape and module location

Spec text: [Decision 2][spec-025-d2].

### Justification

- **Factory over static constant.** A factory returns a fresh `StrawberryConfig` per call, so two schemas (e.g. a main schema and an admin-tools schema) get independent instances and one's mutations cannot leak to the other. A module-level `STRAWBERRY_CONFIG: StrawberryConfig` would share mutable state across every call site.
- **Factory over class wrapper.** Wrapping the schema constructor (e.g. `dst.Schema(query=..., ...)`) shadows the upstream symbol and hides composition. The factory returns a `StrawberryConfig` the consumer composes into their own schema call — the same posture as `DjangoOptimizerExtension` being composed via `extensions=[...]`.
- **`**config_kwargs` passthrough for non-scalar `StrawberryConfig` fields.** Strawberry's [`StrawberryConfig`][config] has many fields beyond `scalar_map`; `scalar_map` is the only one the helper has an opinion on. Forwarding every other kwarg verbatim gives consumers one call carrying both the package scalars and their tuning (`strawberry_config(auto_camel_case=False, relay_max_results=200)`). The helper does not enumerate the upstream kwargs because Strawberry owns that set and it drifts across releases; unknown kwargs surface as upstream's own `TypeError`.
- **`scalar_map=` rejected as a kwarg.** Letting it through would bypass the [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions) collision policy the helper exists to centralize ([Error shapes][spec-025-error-shapes]).
- **Keyword-only `extra_scalar_map`.** With a `**config_kwargs` passthrough, a positional argument would be ambiguous between "scalar map" and "first `StrawberryConfig` argument"; the leading `*,` removes the ambiguity by construction.
- **`extra_extensions=` deliberately omitted.** Strawberry extensions go to the schema constructor's `extensions=`, not into `StrawberryConfig`. Real demand for extension bundling would ship as a separate helper (e.g. `schema_kwargs(...)` returning `{"config": ..., "extensions": [...]}`) rather than overloading this one.
- **Module location: [`scalars.py`][scalars], not a new `config.py`.** Cohesion: the scalar definitions and the map that registers them live in one module, and the factory body is too small to earn its own. A `config.py` would also sit ambiguously beside the existing [`conf.py`][conf] (the `DJANGO_STRAWBERRY_FRAMEWORK` settings reader). The `Upload` re-export lives in the same module with no map entry, so the module holds every public scalar without file proliferation.
- **Type signature.** `Mapping[object, ScalarDefinition] | None` on `extra_scalar_map` matches Strawberry's own `StrawberryConfig.scalar_map: Mapping[object, ScalarDefinition]` ([`.venv/lib/python3.14/site-packages/strawberry/schema/config.py #"scalar_map: Mapping[object, ScalarDefinition]"`][config]); `object` keeps the key type as broad as Strawberry's contract. `**config_kwargs: Any` keeps the passthrough type-broad on purpose, so the helper does not duplicate Strawberry's per-kwarg types.

### Alternatives considered (and rejected)

- **`django_strawberry_framework/config.py` (new module).** Rejected: ambiguity with [`conf.py`][conf]; two modules differing by two letters invite consumer error.
- **`django_strawberry_framework/__init__.py` only.** Rejected: `__init__.py` is the public-surface manifest (re-exports and `__all__`); the body belongs next to the scalar it composes.
- **`django_strawberry_framework/schema.py` (new module).** Rejected: the name collides conceptually with `strawberry.Schema` and suggests the helper does more than build a `StrawberryConfig`.
- **`strawberry_config(extra_scalar_map=None)` only — no `**config_kwargs`.** Rejected: consumers tuning `auto_camel_case` or `relay_max_results` would have no supported composition path, because `extra_scalar_map=` exists only on the helper and `_PACKAGE_SCALAR_MAP` is private.
- **A public `PACKAGE_SCALAR_MAP` re-export.** Rejected: two parallel public composition paths, the [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions) collision policy pushed onto consumers, and a wider public surface for an audience the passthrough already serves.
- **`strawberry_config(*, scalar_map=None)`.** Rejected: a bare `scalar_map=` implies "replaces the package defaults"; `extra_scalar_map=` states merge-not-replace, and reusing the name the helper rejects inside `**config_kwargs` would be doubly confusing.
- **`strawberry_config(*, replace_scalar_map=None, extra_scalar_map=None)`.** Rejected: a replace mode would let a consumer silently break the `BigIntegerField → BigInt` converter table.

## Decision 3 — `BigInt` redefinition as bare `NewType` + `ScalarDefinition`

Spec text: [Decision 3][spec-025-d3].

### Justification

- The `cls is None and name is not None` branch of `strawberry.scalar(...)` returns a `ScalarDefinition` directly and never enters the deprecation path ([`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"if cls is None and name is not None"`][scalar]); the warning lives only in the `wrap()` body ([`.venv/lib/python3.14/site-packages/strawberry/types/scalar.py #"def wrap(cls: _T) -> ScalarWrapper"`][scalar]) that the class-passing path takes.
- A bare `NewType("BigInt", int)` keeps `BigInt` usable as a direct annotation (`id: BigInt`, `def f(x: BigInt) -> BigInt`), because a `NewType` is a transparent identity at runtime; Strawberry maps it to the registered definition through `StrawberryConfig.scalar_map` at schema construction.
- The wire format is spec-017's and is independent of the wrapping: decimal string in, decimal string out. The function bodies normalize through the base descriptors (`int.__int__`, `str.__str__`, `int.__repr__`) and report rejected inputs through `_safe_arg_repr` / `_safe_type_name`, so a hostile `int` / `str` subclass cannot alter what is accepted or emitted.
- The factory body treats every consumer object as hostile: the absent-versus-empty branch never calls `__bool__`, the guard spans every operation that dispatches into consumer key code, and the collision label never trusts `__name__`. A promised exception boundary that a caller's object can replace with its own exception is not a boundary.

### Alternatives considered (and rejected)

- **Keep `strawberry.scalar(NewType("BigInt", int), ...)` and suppress the warning with `warnings.filterwarnings("ignore", ...)`.** Rejected: suppression defeats the purpose; the package import should be clean by construction.
- **Strawberry's `Annotated[int, strawberry.argument(...)]` shape.** Rejected: `argument(...)` annotates parameters, not types; it does not fit `BigInt`'s role as a type used in annotations.
- **Subclass `int` for `BigInt` and bind the definition to the subclass.** Rejected: a real class is heavier than a `NewType`, and `isinstance` checks against an `int` subclass interact awkwardly with `bool` (itself an `int` subclass) at parse time.

## Decision 4 — Conflict resolution for `extra_scalar_map` collisions

Spec text: [Decision 4][spec-025-d4].

### Justification

- The collision is a consumer-input mistake at helper-call time, not a `DjangoType`-creation or finalization error. `ValueError` is the standard library's "unsuitable argument" exception; [`ConfigurationError`][glossary-configurationerror] signals type-creation / finalization problems, so using it here would blur what that class means.
- Silently overriding the package default would let a consumer re-register `BigInt` to a different definition (e.g. one serializing as a JSON integer), breaking the wire-format contract [`docs/SPECS/spec-017-deferred_scalars-0_0_6.md`][spec-017] Decision 1 pins — doing what the consumer typed while breaking a contract they did not know they were touching.
- Override-with-warning still builds a schema with possibly broken semantics, and the warning is easy to miss. A hard error catches the mistake before schema construction starts.
- The message names the offending keys and the supported recourse (register the consumer scalar under a different `NewType` / class), so the fix is in the error itself.

### Alternatives considered (and rejected)

- **Silent override.** Rejected: catches no mistakes; the consumer never learns they replaced a package default.
- **Override with `UserWarning`.** Rejected: easy to miss; the schema still ships with overridden semantics.
- **`strawberry_config(extra_scalar_map=..., allow_override=False)`.** Rejected: supports an intentional-override use case that [Decision 2](#decision-2--helper-api-shape-and-module-location)'s no-replace-mode boundary already excludes.

## Decision 5 — Migration posture: hard break in alpha

Spec text: [Decision 5][spec-025-d5].

### Justification

- Matches the `PositiveBigIntegerField` precedent in [`docs/SPECS/spec-017-deferred_scalars-0_0_6.md`][spec-017] Decision 1, which switched that field from `int` to `BigInt` as a breaking change. The package is alpha-quality, and [`docs/GLOSSARY.md`][glossary]'s status legend names `1.0.0` as the API-freeze boundary after which strict semantic versioning applies; before it, hard breaks are the default.
- Long deprecation windows belong after `1.0.0`, not during alpha.
- The consumer migration is one argument: `config=strawberry_config()` on the schema constructor, with the import. The `[0.0.7]` `CHANGELOG.md` `### Changed` bullet carries the before/after.

### Alternatives considered (and rejected)

- **A one-release `DeprecationWarning` from the package.** Rejected: keeps the class-direct path alongside the new one for a release, doubling surface and test load; consumers who ignore deprecation warnings break later anyway.
- **Keep the wrapped `BigInt` and offer `strawberry_config()` as an opt-in no-op.** Rejected: keeps the suppression for another release and defers the cleanup.
- **A `legacy_bigint()` compat helper.** Rejected: every alpha-era compat helper is one more thing to deprecate at `1.0.0`.

## Decision 6 — No warning suppression at the definition site

Spec text: [Decision 6][spec-025-d6].

### Justification

- The name-only `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload ([Decision 3](#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition)) never emits the `DeprecationWarning`, so a suppression would guard nothing.
- A defensive suppression is a documentation hazard: a reader cannot tell "a real deprecation fires here" from dead code. With none, the module's contract is explicit — the import is clean by construction.
- `test_package_import_does_not_emit_strawberry_deprecation_warning` ([`tests/test_scalars.py #"test_package_import_does_not_emit_strawberry_deprecation_warning"`][test-scalars]) imports the package in a `-W error::DeprecationWarning` subprocess, so the contract is enforced whichever mechanism would otherwise produce a warning.

### Alternatives considered (and rejected)

- **Keep a suppression defensively.** Rejected: dead code is a maintenance hazard, and the regression test enforces the contract regardless.
- **Replace the suppression with a comment.** Rejected: a comment pointing at a suppression that does not exist documents nothing.

## Decision 7 — Test placement and shape

Spec text: [Decision 7][spec-025-d7].

### Justification

- The code under test lives in one module, [`django_strawberry_framework/scalars.py`][scalars]; its package-test partner is [`tests/test_scalars.py`][test-scalars]. A `tests/test_config.py` would mirror a `django_strawberry_framework/config.py` that does not exist ([Decision 2](#decision-2--helper-api-shape-and-module-location)).
- The `BigInt` parser / serializer pins and the factory tests share imports and the same `ScalarDefinition` shape, so they belong together.
- The registered round trip is reachable from a real query, so by the live-HTTP-priority rule at [`AGENTS.md #"any line reachable via a real GraphQL query against fakeshop"`][agents] it is pinned live: fakeshop's served schema passes `config=strawberry_config()` and [`examples/fakeshop/test_query/test_scalars_api.py`][test-scalars-api] queries its `BigInt` columns over `/graphql/`. A registration failure would also break every live test that imports the project schema.
- One pytest item per test, without `parametrize`, keeps each named contract one collected node.

### Alternatives considered (and rejected)

- **A new `tests/test_config.py` beside a new `django_strawberry_framework/config.py`.** Rejected per [Decision 2](#decision-2--helper-api-shape-and-module-location).
- **Put the factory tests in `tests/base/test_conf.py`.** Rejected: that file covers the `DJANGO_STRAWBERRY_FRAMEWORK` settings reader; the helper has no settings dependency.

## Decision 8 — Version posture: this card ships inside the `0.0.7` cut

Spec text: [Decision 8][spec-025-d8].

### Justification

- The card is one of the joint `0.0.7` cut, so its `CHANGELOG.md` bullets append to the shared `## [0.0.7] - 2026-05-27` section; a second `[0.0.7]` heading would split the release.
- The bump that closes a joint cut is owned by the last card to land, never by an individual card's slices ([`docs/GLOSSARY.md`][glossary] `## Joint version cut`). Ship order is decided by which card is picked up next, not by topical fit, so pinning the bump to a named card would create a sequencing constraint with no engineering reason.

### Alternatives considered (and rejected)

- **This card owns the bump.** Rejected for the sequencing reason above; same posture as [`docs/SPECS/spec-023-multi_db-0_0_7.md`][spec-023] Decision 9.
- **A separate release-cut card that owns the bump.** Rejected: the last-card-owns-the-bump rule already assigns it without an extra card.

## Decision 9 — Example-app migration scope

Spec text: [Decision 9][spec-025-d9].

### Justification

- The example's migration surface is the schema the project serves at `/graphql/`; touching more than that call is gold-plating.
- Identifying the site by role rather than by a count of the project's construction calls keeps the Decision true as harness modules that build their own schemas come and go; whether those owe the registration is [Decision 5](#decision-5--migration-posture-hard-break-in-alpha)'s rule, applied by whoever builds them.
- Per-app `schema.py` modules contribute a `Query` root and construct nothing, so the registration has no site there.

### Alternatives considered (and rejected)

- **Add a `BigIntegerField` column and a `BigInt` query to fakeshop as part of this card.** Rejected: a model-shape decision, not a registration one; it belongs to the card that owns the example models.
- **Skip the [`examples/fakeshop/config/schema.py`][schema] update.** Rejected: the example project is the primary "what consumer code looks like" surface, and the served schema must carry the registration for its `BigInt` columns to resolve.

## Borrowing posture — explicitly do not borrow

The reasoning for the three shapes the spec's `### Explicitly do not borrow` subsection refuses:

- **A `dst.Schema(query=..., ...)` wrapper that pre-populates `config=`.** Rejected: shadows the upstream schema constructor, hides composition, and leaves every consumer asking what it returns. The package already ships `DjangoOptimizerExtension` as an extension consumers pass explicitly; the same explicit-composition posture extends to `config=`.
- **A static `SCALAR_MAP: dict[object, ScalarDefinition]` re-export consumers spread into their own `StrawberryConfig`.** Rejected: forces every consumer to spell `StrawberryConfig(scalar_map={**SCALAR_MAP, ...})` and makes the collision policy the consumer's responsibility. The factory keeps that policy in one place — see [Decision 4](#decision-4--conflict-resolution-for-extra_scalar_map-collisions).
- **A module-level `STRAWBERRY_DEFAULT_CONFIG: StrawberryConfig` instance.** Rejected: one shared `StrawberryConfig` is shared mutable state across every consumer schema; a mutation to one schema's `scalar_map` would leak to all. This is the same argument [Decision 2](#decision-2--helper-api-shape-and-module-location) makes for a factory.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md

<!-- docs/ -->
[glossary]: ../../GLOSSARY.md
[glossary-configurationerror]: ../../GLOSSARY.md#configurationerror

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[spec-017]: ../spec-017-deferred_scalars-0_0_6.md
[spec-023]: ../spec-023-multi_db-0_0_7.md
[spec-025]: ../spec-025-scalar_map_helper-0_0_7.md
[spec-025-d1]: ../spec-025-scalar_map_helper-0_0_7.md#decision-1--spec-filename-and-canonical-naming
[spec-025-d2]: ../spec-025-scalar_map_helper-0_0_7.md#decision-2--helper-api-shape-and-module-location
[spec-025-d3]: ../spec-025-scalar_map_helper-0_0_7.md#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition
[spec-025-d4]: ../spec-025-scalar_map_helper-0_0_7.md#decision-4--conflict-resolution-for-extra_scalar_map-collisions
[spec-025-d5]: ../spec-025-scalar_map_helper-0_0_7.md#decision-5--migration-posture-hard-break-in-alpha
[spec-025-d6]: ../spec-025-scalar_map_helper-0_0_7.md#decision-6--no-warning-suppression-at-the-definition-site
[spec-025-d7]: ../spec-025-scalar_map_helper-0_0_7.md#decision-7--test-placement-and-shape
[spec-025-d8]: ../spec-025-scalar_map_helper-0_0_7.md#decision-8--version-posture-this-card-ships-inside-the-007-cut
[spec-025-d9]: ../spec-025-scalar_map_helper-0_0_7.md#decision-9--example-app-migration-scope
[spec-025-error-shapes]: ../spec-025-scalar_map_helper-0_0_7.md#error-shapes

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../../django_strawberry_framework/conf.py
[scalars]: ../../../django_strawberry_framework/scalars.py

<!-- tests/ -->
[test-scalars]: ../../../tests/test_scalars.py

<!-- examples/ -->
[schema]: ../../../examples/fakeshop/config/schema.py
[test-scalars-api]: ../../../examples/fakeshop/test_query/test_scalars_api.py

<!-- scripts/ -->

<!-- .venv/ -->
[config]: ../../../.venv/lib/python3.14/site-packages/strawberry/schema/config.py
[scalar]: ../../../.venv/lib/python3.14/site-packages/strawberry/types/scalar.py

<!-- External -->
