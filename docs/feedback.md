# Review feedback - `docs/spec-020-scalar_map_helper-0_0_7.md`

Scope: reviewed `docs/spec-020-scalar_map_helper-0_0_7.md` and its companion terms CSV against the current package code, current KANBAN/CHANGELOG state, and Strawberry's installed `StrawberryConfig.scalar_map` behavior.

Sanity checks that passed:

- The proposed bare `NewType("BigInt", int)` plus `StrawberryConfig(scalar_map={BigInt: scalar_def})` path works in the installed Strawberry version: a minimal schema parsed and serialized `"9223372036854775807"` successfully.
- `strawberry.scalar(name="BigInt", serialize=..., parse_value=...)` returns a `ScalarDefinition` without emitting the current `Passing a class to strawberry.scalar()` deprecation warning.
- `scripts/check_spec_glossary.py --spec docs/spec-020-scalar_map_helper-0_0_7.md` exits successfully for the current CSV, but see M1 below: the CSV is still under-populated relative to the spec-builder rule.

## Blockers

### B1. Existing converter-backed `BigInt` schema tests are not migrated

Files: `docs/spec-020-scalar_map_helper-0_0_7.md` sections "Slice 2: Tests", "Decision 7", and "Test plan"; existing impacted tests in `tests/types/test_converters.py` under the "BigInt scalar - schema-execution field-mapping tests" section.

The spec treats the break as mostly "consumers using `BigInt` directly", then adds two new `tests/test_scalars.py` integration tests with `config=strawberry_config()`. That misses the current converter-backed surface: `BigIntegerField` and `PositiveBigIntegerField` already map to `BigInt` through `SCALAR_MAP`, and `tests/types/test_converters.py` currently has multiple `strawberry.Schema(query=Query)` calls for those model-field paths.

Once `BigInt` becomes a bare `NewType`, those existing tests will need `config=strawberry_config()` too. More importantly, real consumers with `DjangoType` fields backed by `BigIntegerField` / `PositiveBigIntegerField` need the migration even if they never import or annotate `BigInt` directly.

Root fix: broaden the migration language from "direct `BigInt` users" to "any schema that can contain package-defined scalars, including converter-generated `BigInt` fields", and add a Slice 2 task to update the existing BigInt schema-construction sites in `tests/types/test_converters.py` to use `strawberry_config()`. The CHANGELOG and GLOSSARY migration snippets should say the same thing.

### B2. The Definition of Done tells workers to run pytest, contradicting AGENTS.md

File: `docs/spec-020-scalar_map_helper-0_0_7.md` Definition of done item containing `uv run pytest --no-cov`.

The repo instruction says "Do not run pytest after edits; run only when explicitly asked." The spec repeats that convention near the top, but the final DoD still requires `uv run pytest --no-cov`. A builder following the spec would violate the repo workflow.

Root fix: remove pytest from the worker-local DoD and say local validation is `uv run ruff format .` plus `uv run ruff check --fix .`; pytest is run only if the maintainer explicitly asks or by CI. If you want the intended command documented for maintainers, phrase it as optional/maintainer-invoked, not as a worker completion gate.

## High-severity issues

### H1. Release bookkeeping says both "post-0.0.7 Unreleased" and `DONE-...-0.0.7`

Files: `docs/spec-020-scalar_map_helper-0_0_7.md` Decision 8, Slice 5, Risks, and Definition of done.

The spec correctly observes that `0.0.7` is already cut and that this card's changelog entries belong under `[Unreleased]`. But it still instructs the KANBAN move to `DONE-NNN-0.0.7` and keeps the active filename/version posture as `0_0_7`.

That makes the release ledger internally inconsistent: the card would be recorded as shipped in `0.0.7` while the actual user-facing release entry is waiting for the next patch. KANBAN's own convention says the card version tag encodes the shipment it belongs to.

Root fix: choose one posture before implementation. The cleanest one is to retag this card/spec to `0.0.8` now (`WIP-ALPHA-020-0.0.8`, `spec-020-scalar_map_helper-0_0_8.md`, future `DONE-020-0.0.8`) while still leaving the actual version bump to the future cut. If you intentionally keep the historical `0.0.7` filename, then the spec should not instruct a `DONE-...-0.0.7` card for a post-cut change.

### H2. `strawberry_config()` does not compose with existing `StrawberryConfig` options

File: `docs/spec-020-scalar_map_helper-0_0_7.md` Decision 2, especially the `extra_scalar_map=` discussion.

The spec says consumers who want `auto_camel_case=False` or `relay_max_results=200` can "construct their own `StrawberryConfig(...)` and merge the package's `scalar_map` via `extra_scalar_map=`". That is not a usable API as written. `extra_scalar_map` is an input to `strawberry_config()`; it does not expose the package scalar map for a separately constructed config, and `_PACKAGE_SCALAR_MAP` is intentionally private.

This matters because existing consumers may already pass a custom `config=StrawberryConfig(...)`. Their migration is not the advertised one-line `config=strawberry_config()` change; they must either mutate the returned config object after construction or reach into private state.

Root fix: either expand the helper to accept pass-through `StrawberryConfig` kwargs while still owning `scalar_map`, or explicitly document and test a supported composition pattern. The higher-quality API is a keyword-only helper such as `strawberry_config(*, extra_scalar_map=None, **config_kwargs)` that rejects a raw `scalar_map=` kwarg and forwards the rest to `StrawberryConfig(...)`.

## Medium-severity issues

### M1. The terms CSV passes the checker but is under-populated

Files: `docs/spec-020-scalar_map_helper-0_0_7-terms.csv`; `docs/spec-020-scalar_map_helper-0_0_7.md` throughout.

The checker reports `OK: 14 terms`, but the CSV omits several project-specific or newly introduced terms the spec relies on: `strawberry_config`, `StrawberryConfig`, `DjangoFileType`, `DjangoImageType`, and the Upload-card references are the obvious examples. The builder flow explicitly says the CSV should be over-zealous because under-population is invisible to the checker.

Root fix: add rows for the omitted terms. For the brand-new `strawberry_config` glossary entry, either add the glossary entry before re-running the checker or call out the temporary missing-entry state explicitly in the spec until the docs slice lands.

### M2. `Upload` is repeatedly tied to the wrong KANBAN card

Files: `docs/spec-020-scalar_map_helper-0_0_7.md` sections "Problem statement", "Goals", "Non-goals", "Decision 2", "Risks", and "Out of scope".

The spec says `Upload` is `TODO-ALPHA-027`, but current `KANBAN.md` has `TODO-ALPHA-027-0.0.11` as "Mutations + auto-generated Input types" and `TODO-ALPHA-028-0.0.11` as "Upload scalar and file / image field mapping". The existing `django_strawberry_framework/scalars.py` docstring also points Upload at `TODO-ALPHA-028`.

Root fix: update the spec's Upload references to `TODO-ALPHA-028-0.0.11`. If the WIP card body is stale, call that out once rather than copying the stale ID through the spec.

## Low-severity issues

### L1. The proposed test import block includes an unused `Mapping`

File: `docs/spec-020-scalar_map_helper-0_0_7.md` "Test plan" imports block.

The described tests do not use `Mapping`, so `uv run ruff check --fix .` will remove it. Drop it from the pinned import snippet or add an assertion that actually uses it.

### L2. `tests/test_scalars.py` module docstring will become stale

File: `docs/spec-020-scalar_map_helper-0_0_7.md` "Test plan"; existing docstring in `tests/test_scalars.py`.

`tests/test_scalars.py` currently says schema-execution behavior lives in `tests/types/test_converters.py`. The spec moves two schema-execution tests into `tests/test_scalars.py` but does not instruct updating that docstring. Add a small test-slice bullet to update the docstring so the test layout remains self-describing.

### L3. The spec uses many standing-doc line-number references

File: `docs/spec-020-scalar_map_helper-0_0_7.md` throughout.

The spec repeatedly uses prose references like "line 26", "lines 18-49", and "line 21" in a standing design doc. The repo convention asks standing docs to prefer symbol-qualified paths or unique-substring anchors instead of raw line numbers. Convert these to section/symbol references or `path #"unique substring"` style references so they survive ordinary doc edits.
