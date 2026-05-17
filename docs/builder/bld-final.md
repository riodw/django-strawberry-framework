# Build: Final test-run gate

Spec reference: `docs/SPECS/spec-deferred_scalars.md` (archived during Slice 6 final verification).
Status: final-accepted

## Test runs

### Full pytest sweep

Command:

```
uv run pytest --no-cov
```

`--no-cov` disables the auto-loaded `pytest-cov` flags pulled in by `pytest.ini` `addopts` (`--cov --cov-report=term-missing`). It is structurally distinct from passing a `--cov*` flag — it suppresses the auto-coverage plugin so this gate stays inside the BUILD.md "Coverage is the maintainer's gate, not a worker's tool" contract. Worker 1 invoked the same `--no-cov` pattern during the per-slice final-verification passes (per `worker-1.md` memory note); no coverage data was inspected.

Summary: **629 passed, 3 skipped, 3 warnings in 25.69s.**

All three test trees were swept (`tests/` package tests, `examples/fakeshop/tests/` non-HTTP example-project tests, `examples/fakeshop/test_query/` live `/graphql` HTTP tests) per `AGENTS.md` "Test placement is mandatory" — `pytest.ini`'s `testpaths` covers all three roots, and the run touched files in each.

The three skipped tests are the spec-declared optional gated tests:

- `test_real_array_field_compatible_with_strawberry` (Slice 3, `pytest.importorskip("django.contrib.postgres.fields")`)
- `test_real_hstore_field_compatible_with_strawberry` (Slice 4, `pytest.importorskip("django.contrib.postgres.fields")`)
- One pre-existing skip outside this build's authored surface.

The three warnings:

- One `UserWarning` from `examples/fakeshop/tests/test_commands.py::test_seed_shards_command_runs_when_shard_alias_present` — Django's `Overriding setting DATABASES can lead to unexpected behavior` notice; pre-existing, unrelated to this build.
- Two `RuntimeWarning`s about `test_choice_enums._owner` model re-registration, fired by `test_convert_scalar_subclass_with_null_widens_through_mro_resolution` and `test_convert_scalar_unknown_field_type_still_raises`. These predate the `deferred_scalars` build cycle (recorded in every per-slice artifact's "Notes for Worker 1" section as carry-through pre-existing warnings) and are out of scope for the final gate.

Pass/fail: **pass.**

### Django consistency checks

#### `manage.py check`

Command:

```
uv run python examples/fakeshop/manage.py check
```

Summary: `System check identified no issues (0 silenced).`

Pass/fail: **pass.**

#### `manage.py makemigrations --check --dry-run`

Command:

```
uv run python examples/fakeshop/manage.py makemigrations --check --dry-run
```

Summary: `No changes detected`.

Pass/fail: **pass.** Model state is migration-consistent without producing migration files. The build cycle added no Django model fields to the example project — the new postgres-soft scalar branches (`ArrayField`, `HStoreField`) are exercised via synthetic `managed = False; app_label = "tests"` model doubles inside the test surface only, so no migration drift is possible.

## CHANGELOG sanity

The build added user-visible behavior and Slice 6 carried the spec-authorized CHANGELOG edit (spec lines 324-328 grant CHANGELOG permission, overriding `AGENTS.md`'s default prohibition). Walked `CHANGELOG.md` end-to-end against shipped state:

- The new entries land under `## [Unreleased]` (not `## [0.0.6]`). Per the spec / Slice 6 plan, `[Unreleased]` is only promoted to `[0.0.6]` at PyPI publish (Definition-of-done; a maintainer-owned step). Correct posture for a worker-side gate.
- Version line consistency: `pyproject.toml:4` and `django_strawberry_framework/__init__.py:25` both read `0.0.6`. The atomic version-bump quintet (Slice 5) is intact post-build.
- Authorized sub-headings present: `### Added`, `### Changed`, `### Notes`. No unauthorized `### Fixed` / `### Removed` / `### Deprecated` / `### Security` headings appear under `[Unreleased]`.
- `### Added` enumerates exactly the four shipped behaviors the spec named: `BigInt` public scalar export (with the strict regex + serializer rules summarized), `JSONField → strawberry.scalars.JSON`, `HStoreField → strawberry.scalars.JSON` (soft-registered framing explicit), and `ArrayField` recursion with the `ConfigurationError` rejection for nested arrays and outer `choices` on both `ArrayField` and `HStoreField`. Matches spec line 324-326.
- `### Changed` correctly flags `PositiveBigIntegerField` as a **breaking wire-format change** and names the new shape (decimal strings on the wire, not JSON integers). Matches spec line 326.
- `### Notes` is verbatim from spec lines 327-328 (suppression at definition site, `StrawberryConfig.scalar_map` follow-up referenced, real public-API change framing preserved).
- The pre-existing `[0.0.5]` and earlier blocks are untouched.

Verdict: **CHANGELOG reflects shipped state correctly.** No over- or under-statement against the actual build, no obsolete `[Unreleased]` cruft inherited from a prior cycle, no unauthorized headings.

## Deferred work catalog

Walked every per-slice and integration artifact's `### Notes for Worker 1 (spec reconciliation)` and `### What looks solid` sections (per BUILD.md "Final test-run gate") and the active spec's `## Non-goals` and `## Out of scope` sections to surface every item explicitly deferred to a future slice, future spec, or maintainer follow-up. One bullet per deferral; spec lines cite the **archived** path `docs/SPECS/spec-deferred_scalars.md`.

- **`TODO-ALPHA-045-0.0.7` — Warning-free scalar registration via `StrawberryConfig.scalar_map`.** Source: `bld-slice-6-docs_archive.md` "Documentation / release sanity" + spec lines 247-253 (Decision 4 framing), spec lines 488-501 (Decision 6 follow-up contract), spec line 728 (Out of scope), spec lines 723-725 (Risks). License: spec lines 488-501. Description: migrate `BigInt` from the current `strawberry.scalar(NewType, ...)`-with-suppressed-deprecation shape to a `StrawberryConfig.scalar_map`-based design via a package-provided `strawberry_config(...)` factory. The card is now live in `KANBAN.md` at NNN 045 and is a **real public-API migration** (consumers using `BigInt` directly will merge the package-provided `StrawberryConfig` into their `strawberry.Schema(...)` call).

- **`BigAutoField` scalar-override recourse.** Source: `bld-slice-1-bigint_scalar.md` "What looks solid" + spec line 401 (Decision 1 target-fields list), spec line 670 (Edge cases), spec line 726 (Risks "BigAutoField deliberately deferred"), spec line 746 (Out of scope). License: spec line 401 + spec line 726. Description: `BigAutoField` stays mapped to `int` for PK wire-format stability; consumer recourse for the `2**31` boundary on autoincrement PKs is gated behind `TODO-ALPHA-015-0.0.6 — Scalar field override semantics`, which lands the `Meta.scalar_overrides` (or equivalent) hook. No current-day recourse.

- **Multi-dimensional `ArrayField` support.** Source: `bld-slice-3-arrayfield.md` "What looks solid" + spec line 279 (Non-goals), spec line 675 (Edge cases), spec line 732 (Risks "Multi-dimensional ArrayField"), spec line 743 (Out of scope). License: spec line 279 + spec line 732. Description: `ArrayField(ArrayField(...))` is rejected with `ConfigurationError` at type creation. Lift the cap in a future card if real-world demand surfaces; the rejection branch is the loud-over-silent posture the package prefers.

- **Dedicated `HStore` scalar.** Source: `bld-slice-4-hstorefield.md` "What looks solid" + spec line 281 (Non-goals), spec line 728 (Risks "HStoreField and JSONField share JSON"), spec line 744 (Out of scope). License: spec line 281 + spec line 728. Description: both `JSONField` and `HStoreField` map to `strawberry.scalars.JSON`. Schema clients cannot distinguish them at the GraphQL type level. A future dedicated `HStore` scalar is possible if the contract drifts apart enough to matter; out of scope for this card.

- **`BigInt64`-bounded variant of `BigInt`.** Source: spec line 730 (Risks "BigInt arbitrary precision"), spec line 748 (Out of scope). License: spec lines 285-286 + spec line 730. Description: `BigInt` is technically arbitrary-precision (Python `int` plus regex-validated decimal strings, no upper bound check) — it accepts values past `2**63 - 1` even though the Django source columns top out there. If a real consumer needs a hard 64-bit cap, a follow-up card can add `BigInt64` or similar.

- **`PositiveBigIntegerField` wire-format breaking-change override.** Source: `bld-slice-1-bigint_scalar.md` + spec line 671 (Edge cases), spec line 726 (Risks "PositiveBigIntegerField wire-format change"). License: spec line 671 + spec line 726. Description: `PositiveBigIntegerField` mapping switched from `int` to `BigInt` as a breaking wire-format change in this build (decimal strings on the wire). Acceptable in alpha; documented in `CHANGELOG.md` under `### Changed`. Consumer override recourse (to keep the legacy `int` shape on a specific field) waits for `TODO-ALPHA-015-0.0.6 — Scalar field override semantics`.

- **`tests/types/test_converters.py` size growth follow-up.** Source: spec line 737 (Risks). License: spec line 737. Description: this build added ~28 tests (~700 lines) to `tests/types/test_converters.py`, bringing the file to roughly ~1100 lines after Slice 4. If the file later exceeds ~1500 lines, a follow-up should extend `docs/TREE.md`'s mirror rule with a concern-specific test-file convention (e.g., `tests/types/test_converters_scalars.py`). No action required at this build; recorded as a maintainer follow-up trigger.

- **`tests/types/test_converters.py` pre-existing `_owner` re-registration warnings.** Source: `bld-slice-1-bigint_scalar.md` "Notes for Worker 1 (spec reconciliation)" + `bld-integration.md` "Deferred follow-ups walked from prior artifacts". License: none (predates this build cycle). Description: two `RuntimeWarning`s about `test_choice_enums._owner` model re-registration fire on every focused-test run and again under the full sweep above. Predate the `deferred_scalars` build; out of scope for any of its six slices. Recorded so a future test-housekeeping pass has a fix candidate; not blocking.

## Final verification (Worker 1)

### Summary

The `deferred_scalars` (`0.0.6`) build cycle completed Slices 1-6 plus the cross-slice integration pass; all artifacts reached `final-accepted` with zero unresolved findings. This gate ran the three required commands against the post-integration tree and recorded:

- `uv run pytest --no-cov` — 629 passed, 3 skipped, 3 warnings.
- `uv run python examples/fakeshop/manage.py check` — 0 issues.
- `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — no changes detected.

CHANGELOG entry under `[Unreleased]` matches shipped state across `### Added`, `### Changed`, and `### Notes`, with no unauthorized headings and no over- or under-statement against the diff. The deferred-work catalog enumerates eight items: the `TODO-ALPHA-045-0.0.7` warning-free-scalar-registration follow-up, the `BigAutoField` and `PositiveBigIntegerField` overrides gated behind `TODO-ALPHA-015-0.0.6`, the multi-dimensional `ArrayField` cap, the dedicated `HStore` scalar, the `BigInt64`-bounded variant, the test-file size-growth follow-up trigger, and the pre-existing `_owner` re-registration warnings.

The gate closes the `deferred_scalars` build cycle. Worker 0 marks the final checklist box and proceeds to closeout.

Status: **final-accepted.**
