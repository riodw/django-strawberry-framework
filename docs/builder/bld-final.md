# Build: Final test-run gate — spec-015 (consumer_overrides_scalar / 0.0.6)

Spec reference: `docs/spec-015-consumer_overrides_scalar-0_0_6.md`
Status: final-accepted

## Pytest gate

- Command: `uv run pytest --no-cov`
- Result: PASS — `707 passed, 2 skipped, 3 warnings in 25.33s`
- Notes:
  - The 2 skipped tests are pre-existing `tests/types/test_converters.py` skips (unchanged across this build's slices; flagged in Worker 1 memory entries from Slice 1 / Slice 3 / Slice 5 final-verification passes).
  - The 3 warnings are pre-existing and not introduced by this build: (1) `examples/fakeshop/tests/test_commands.py::test_seed_shards_command_runs_when_shard_alias_present` "Overriding setting DATABASES" `UserWarning`; (2-3) `tests/types/test_converters.py::test_convert_scalar_subclass_with_null_widens_through_mro_resolution` and `::test_convert_scalar_unknown_field_type_still_raises` "Model 'test_choice_enums._owner' was already registered" `RuntimeWarning` from Django's model-registry plumbing.
  - Full sweep across all three test trees (`tests/`, `examples/fakeshop/tests/`, `examples/fakeshop/test_query/`) per `pytest.ini`'s `testpaths`.

## Django consistency checks

- `uv run python examples/fakeshop/manage.py check` — PASS (`System check identified no issues (0 silenced).`)
- `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — PASS (`No changes detected`)

## Lint / format / diff gate

- `uv run ruff format --check .` — PASS (`100 files already formatted`; ruff's pre-existing `COM812`-vs-formatter warning is not a failure)
- `uv run ruff check .` — PASS (`All checks passed!`)
- `git diff --check` — PASS (exit 0; no whitespace errors or conflict markers anywhere in the working tree)

## CHANGELOG contract

Worker 3 (Slice 5 review) confirmed verbatim character-for-character transcription of the five `[Unreleased]` entries against `docs/spec-015-consumer_overrides_scalar-0_0_6.md` lines 267-271. Worker 1 (Slice 5 final-verification) re-verified the same. Final confirmation here:

- **Added (×3)**: annotation-only scalar overrides, `DjangoTypeDefinition.consumer_annotated_scalar_fields`, and the H1 Relay `id` collision guard `ConfigurationError`. All three are licensed by spec Slice 5 sub-checkbox `CHANGELOG.md` (spec lines 266-271): "permission granted by this spec, overriding [`AGENTS.md`](../AGENTS.md)'s default prohibition".
- **Changed (×2)**: the converter-bypass contract for overridden scalar fields, and the uniform rejection of `id = <StrawberryField>` assignments on Relay-Node-shaped types. Both `Changed` entries are spec-authorized.
- No other CHANGELOG sections (`Removed`, `Fixed`, `Deprecated`, `Notes`) were modified by this build.

The CHANGELOG entries are coherent with what shipped: Slice 1 lands the collection, the H1 guard, the H2 bypass; Slice 5 carries the entries verbatim. No drift between the documented contract and the implementation.

## Deferred work catalog

Walking every per-slice and integration artifact's spec-reconciliation notes and `What looks solid` / `Notes for Worker 1` sections:

- **`_introspect_field_type` test-helper promotion to `tests/types/conftest.py`** — `bld-slice-1-annotation_scalar_overrides.md` Worker 3 review "Notes for Worker 1 (spec reconciliation)" (Slice 1 review pass) and `bld-integration.md` "DRY scan" / "Decision" sections. No spec line licenses this as a deferral; recorded as an intentional integration-pass deferral after Worker 1 and Worker 3 concurred. **Description**: four near-copies of the introspection-query pattern (`__type(name: "...") { fields { name type { kind name ofType { kind name } } } }`) in `tests/types/test_definition_order.py:413`, `:518-521`, `:685`, `:775` overlap with the `_introspect_field_type` helper at `tests/types/test_converters.py:434`. Promotion candidate for a future test-infrastructure card if more callers surface; the four sites have legitimate single-type-vs-alias-multi-type variation so a shared helper would need parametrization.

- **Inline test-model `Meta` convention alignment across test files** — `bld-slice-1-annotation_scalar_overrides.md` Worker 3 review (Low finding flagged stylistic-only) and `bld-integration.md` "DRY scan" / "Decision" sections. No spec line licenses this. **Description**: Slice 1 added three inline `models.Model` declarations in `tests/types/test_definition_order.py` (`UnsupportedFieldOwner`, `GroupedChoiceOwner`, `CoResidentChoiceOwner`) that set `app_label` only; the sibling pattern in `tests/types/test_converters.py` uses `app_label + managed = False`. Stylistic-only drift with no functional impact under the test runner. Worth folding into a future test-tree-wide cleanup card if one ships.

- **`Meta.field_overrides = {...}` declarative override API** — spec line 347 ("No new `Meta.field_overrides = {...}` API ... A future card may add a declarative override key if the assigned / annotation routes prove insufficient for some real consumer use case; that lives outside `0.0.6`"). **Description**: explicitly non-goal'd by this card. The annotation-only + assigned-`strawberry.field` four-corner matrix is sufficient to close the contract gap; the declarative override key remains a candidate for a future spec if real consumer use cases surface that the assigned / annotation routes cannot satisfy.

- **Annotation / field-type compatibility pre-check** — spec line 348 ("No annotation/field-type compatibility pre-check ... Runtime serialization errors at query time are the consumer-visible failure mode and are intentional"). **Description**: the package does not assert that the consumer's annotation is type-compatible with the Django column (`description: int` against a `CharField` is the consumer's responsibility). Intentional non-goal; runtime serialization errors at query time are the consumer-visible failure mode and are by design. Out of scope for `0.0.6`.

- **Field-level GraphQL metadata on the Relay-supplied `id` field** — spec line 254-259 (in the KANBAN body's "Design notes carried into `0.0.6`") and CHANGELOG `Changed` entry. **Description**: the rev6 M1 + rev7 M2 assigned-`id` ban removes the only path for attaching `description` / `deprecation_reason` / `directives` to the Relay-supplied `id` field. The documented workaround is a resolver-backed sibling field (`@strawberry.field(description="…") def display_id(self) -> strawberry.ID: return str(self.pk)`); direct field-level metadata on the Relay-supplied `id` is not configurable in `0.0.6`. Recorded as an intentional design trade-off, not a deferral to a specific future spec.

- **Sentinel-value / `Skip`-typed annotation shape for opt-out** — spec line 349 ("No new opt-out / removal API. The `Meta.exclude` path that shipped in `0.0.1` already covers 'drop the field entirely'. This card does not add a sentinel-value or `Skip`-typed annotation shape (e.g., `description: None` or `description: strawberry.SKIP`) — the design space is not justified by any pending consumer use case"). **Description**: intentional non-goal; `Meta.exclude` remains the canonical opt-out path. Out of scope for `0.0.6`.

- **Parallel field metadata API via annotation-only syntax** — spec line 350 ("No new field metadata API. Description / deprecation / default routing already work via the assigned `strawberry.field(...)` path ... This card adds no parallel route through annotation-only syntax"). **Description**: intentional non-goal. Description / deprecation / default routing stays on the assigned-`strawberry.field(...)` path.

- **Inherited consumer annotations on subclasses** — spec line 736 (Edge cases / "Inheritance"). **Description**: inherited consumer annotations on a base `DjangoType` subclass are NOT in the subclass's own `cls.__annotations__` (Python's standard per-class annotations-dict behavior). The collection at `__init_subclass__` misses inherited overrides — this matches the existing relation-annotation behavior, no asymmetry to fix. Recorded as documented contract (not a deferral). For Relay-Node-shaped subclasses, pk-suppression silently handles the inherited `id: int` case (rev7 M1, pinned by `test_inherited_id_annotation_on_relay_node_subclass_is_handled_by_pk_suppression`).

- **Optional `test_consumer_id_assigned_strawberry_field_on_direct_relay_node_subclass_raises` companion** — spec line 109 (Slice 1 spec-checklist note for the rev8 H1 direct-inheritance reject test). **Description**: the assigned-`id` reject path is not parametrized over the direct-inheritance shape; "Worker 1 may add a `test_consumer_id_assigned_strawberry_field_on_direct_relay_node_subclass_raises` companion if planning surfaces value but the spec doesn't mandate it." Slice 1 Worker 1 did not add the optional companion; the high-value pin (annotation-side) is in place via the rev8 H1 test.

- **HStoreField choices, outer `ArrayField` choices, and null-widening converter-bypass regressions** — spec line 715 ("Worker 1 may add additional regressions for `HStoreField` choices, outer `ArrayField` choices, and the null-widening path if planning surfaces a use case; the four listed cover the contract surface"). **Description**: optional additional bypass regression tests not landed in Slice 1; the four mandatory tests (unsupported field type, grouped choices, nested `ArrayField`, cross-type enum cache) cover the contract surface per the spec's explicit "four cover the contract surface" framing.

- **Spec archival to `docs/SPECS/`** — spec line 272 (Slice 5 sub-check) and BUILD.md "Specs stay at their working location after closeout". **Description**: opt-in spec archival to `docs/SPECS/spec-015-consumer_overrides_scalar-0_0_6.md` is the maintainer's call; the Definition of done does not gate on it. The spec stays at its working location.

## Final verification (Worker 1)

All five gate commands passed cleanly:

1. `uv run pytest --no-cov` → 707 passed / 2 skipped (pre-existing skips unrelated to this build).
2. `uv run python examples/fakeshop/manage.py check` → clean.
3. `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` → no changes.
4. `uv run ruff format --check .` → 100 files already formatted.
5. `uv run ruff check .` → all checks passed.
6. `git diff --check` → exit 0 (no whitespace damage or conflict markers).

CHANGELOG entries match spec authorization verbatim across the five new `[Unreleased]` bullets (3 `Added`, 2 `Changed`). No drift between shipped behavior and the documented contract.

Deferred work catalog walks all six artifacts; ten items recorded with citations. Three are integration-pass deferrals (two stylistic / one test-helper consolidation), six are intentional spec-level non-goals already declared in the spec body, and one is a maintainer-discretion lifecycle step (spec archival).

**Final status: `final-accepted`.** All gates green; no failures to route through an owning slice loop.
