# Review feedback - `docs/spec-020-scalar_map_helper-0_0_7.md`

Scope: full re-review of the updated scalar-map helper spec and companion terms CSV. H1 is treated as an accepted maintainer hold. H2's production API direction is now sound: `strawberry_config(*, extra_scalar_map=None, **config_kwargs)` with `scalar_map=` rejection gives custom-config consumers a real supported migration path without exposing `_PACKAGE_SCALAR_MAP`.

Validation checks run during review:

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-020-scalar_map_helper-0_0_7.md` -> `OK: 16 terms`.
- Probe against installed Strawberry confirmed `StrawberryConfig(auto_camel_case=False)` stores the observable value on `name_converter.auto_camel_case`, while `cfg.auto_camel_case` remains `None`.
- No pytest was run.

## Blockers

### B1. The `auto_camel_case` passthrough test asserts the wrong field

File: `docs/spec-020-scalar_map_helper-0_0_7.md` Test plan, `test_strawberry_config_forwards_auto_camel_case_kwarg`.

The spec says to call `strawberry_config(auto_camel_case=False)` and assert `result.auto_camel_case is False`, then call `strawberry_config()` and assert `result.auto_camel_case is True`. That will fail with the installed Strawberry version. `auto_camel_case` is a dataclass `InitVar`, so it is not stored as normal instance state; `StrawberryConfig.__post_init__` applies it to `result.name_converter.auto_camel_case`.

Root fix: change the test contract to assert `result.name_converter.auto_camel_case is False` for the override and `strawberry_config().name_converter.auto_camel_case is True` for the default. The production helper shape does not need to change.

## Medium-severity issues

### M1. Decision 7 still has the old test-count summary

File: `docs/spec-020-scalar_map_helper-0_0_7.md` Decision 7.

The Slice checklist, Implementation plan, Test plan, and DoD now correctly say thirteen factory tests plus two integration tests. Decision 7 still says "eight new factory tests + two integration tests = ten new pytest items". That stale summary is easy for a worker to copy as the source of truth.

Root fix: update Decision 7 to "thirteen factory tests (eight scalar-map + five `**config_kwargs` passthrough) + two integration tests = fifteen new pytest items."

### M2. The `scalar_map=` rejection test references an unimported private definition

File: `docs/spec-020-scalar_map_helper-0_0_7.md` Test plan, `test_strawberry_config_rejects_scalar_map_kwarg`.

The test sketch calls `strawberry_config(scalar_map={BigInt: _BIGINT_SCALAR_DEFINITION})`, but the pinned import block does not import `_BIGINT_SCALAR_DEFINITION`. More importantly, the test does not need that private object; the branch being tested is structural ownership of the `scalar_map` kwarg, independent of the value.

Root fix: use only public/local values in the sketch, e.g. `strawberry_config(scalar_map={})`, `strawberry_config(scalar_map=None)`, and optionally `strawberry_config(scalar_map={BigInt: alt_def})` where `alt_def = strawberry.scalar(name="AltBigInt", serialize=str, parse_value=int)` is declared locally.

### M3. `strawberry_config` is intentionally absent from the terms CSV, but the spec never schedules adding it

Files: `docs/spec-020-scalar_map_helper-0_0_7.md`; `docs/spec-020-scalar_map_helper-0_0_7-terms.csv`.

The note explaining why `strawberry_config` is absent before Slice 4 is reasonable: the glossary entry does not exist yet, so the checker would fail today. But Slice 4 creates the glossary entry, and the spec does not include a matching instruction to add `strawberry_config,strawberry_config,...` to the terms CSV afterward. DoD item 1 says the CSV anchors every project-specific term; that will not be true at completion unless the CSV is updated in the docs slice.

Root fix: add a Slice 4 / DoD bullet saying that once `docs/GLOSSARY.md#strawberry_config` exists, the terms CSV gains a `strawberry_config` row and the glossary checker is re-run. Keep `StrawberryConfig` out of the CSV because it is upstream, not a package glossary term.

## Low-severity issues

### L1. `[Unreleased]` Added wording assumes a subsection that does not exist today

File: `docs/spec-020-scalar_map_helper-0_0_7.md` Slice 5 / Doc updates for `CHANGELOG.md`.

The current `[Unreleased]` block has `### Changed` and `### Fixed`, but no `### Added`. The spec says to append to the existing `[Unreleased] ### Added` subsection, while it correctly says to add `### Removed` if absent.

Root fix: use the same wording for Added: "add the subsection if absent." This prevents a worker from searching for a heading that is not there.

### L2. H1 remains a deliberate process exception

File: `docs/spec-020-scalar_map_helper-0_0_7.md` Decision 8 / Slice 5.

Keeping the `0.0.7` card/spec suffix while writing release notes under `[Unreleased]` is still a bookkeeping exception. Since this is intentional, no further change is required for this review. The least ambiguous future wording would label the frontmatter as "card tag/provenance" rather than "target release," but that is optional if you want H1 held as-is.
