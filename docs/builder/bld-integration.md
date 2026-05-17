# Build: Cross-slice integration pass

Spec reference: `docs/SPECS/spec-deferred_scalars.md` (archived during Slice 6 final verification; pre-archive line cites in Slices 1-5 artifacts remain historically valid).
Status: final-accepted

## Analysis (Worker 1, integration pass)

### Inputs walked

Per BUILD.md "Cross-slice integration pass", every prior artifact was read in slice order before analysis:

- `docs/builder/bld-slice-1-bigint_scalar.md` — `final-accepted`. DRY findings: deferred `_make_one_field_schema(model_cls, field_name)` extraction (5 trio sites at S1 close), `"test_bigint"` literal (5x), `"4611686018427387904"` literal (2x). All marked integration-pass candidates.
- `docs/builder/bld-slice-2-jsonfield.md` — `final-accepted`. DRY findings: trio-pattern count climbed to 8; `"test_jsonfield"` 3x added to running `app_label` total; flagged `strawberry.scalars.JSON` as a future two-site reference (Slice 2 = `SCALAR_MAP` row; Slice 4 = sentinel branch return).
- `docs/builder/bld-slice-3-arrayfield.md` — `final-accepted`. DRY findings: `_resolve_array_field` flagged as half of a near-twin pair with the (then-future) `_resolve_hstore_field`; `_ARRAY_FIELD_CLS` half of a future sentinel pair; trio count up to ~17; `"test_arrayfield"` ~9x. One Low (`convert_scalar` docstring drift) was deferred to Slice 4 and resolved there.
- `docs/builder/bld-slice-4-hstorefield.md` — `final-accepted`. DRY findings landed the second halves of every pair flagged in Slice 3: `_resolve_array_field` / `_resolve_hstore_field` near-twin pair (`converters.py:65-75` vs `:78-88`); `_ARRAY_FIELD_CLS` / `_HSTORE_FIELD_CLS` adjacent sentinels (`converters.py:91-92`); parallel-but-different `convert_scalar` branches (`converters.py:147-160` vs `:165-174`); shared `ConfigurationError` outer-`choices` rejection template wording at three sites; `app_label` literal density at ~28-29 occurrences; trio-pattern count at ~24 sites; `_FakeArrayField` / `_FakeHStoreField` test doubles deliberately structurally distinct.
- `docs/builder/bld-slice-5-version_bump.md` — `final-accepted`. Zero new logic; mechanical literal quintet. Worker 3's DRY findings: "No DRY findings. Slice 5 ships zero logic." Integration pass inherits no new watchpoints from Slice 5.
- `docs/builder/bld-slice-6-docs_archive.md` — `final-accepted`. Prose + KANBAN + CHANGELOG + spec archival; zero `.py` source changes. Worker 3 verified verbatim drop-ins with `diff`; Worker 1 performed the strip + `git mv` archival as final-verification spec edits. Integration pass inherits no new watchpoints from Slice 6.

Five accepted carry-forward DRY watchpoints from the per-slice `What looks solid` / `DRY findings` / `Notes for Worker 1` sections, all explicitly deferred-to-integration-pass:

1. `_resolve_array_field` / `_resolve_hstore_field` near-twin helper pair.
2. `_ARRAY_FIELD_CLS` / `_HSTORE_FIELD_CLS` adjacent module-level sentinel pair.
3. Parallel `convert_scalar` sentinel branches for ArrayField and HStoreField.
4. Outer-`choices` `ConfigurationError` rejection-message template across ArrayField + HStoreField branches.
5. `_make_one_field_schema(model_cls, field_name)` test-helper extraction at the synthetic-model + `DjangoType` + `Query` trio.

Plus one threshold watchpoint:

6. `app_label` literal density across `tests/types/test_converters.py`.

### Static helper invocations (this pass)

All four shadow overviews were regenerated against post-Slice-6 source on 2026-05-17 from this Worker 1 integration-pass spawn:

- `uv run python scripts/review_inspect.py django_strawberry_framework/scalars.py --output-dir docs/builder/shadow`
- `uv run python scripts/review_inspect.py django_strawberry_framework/types/converters.py --output-dir docs/builder/shadow`
- `uv run python scripts/review_inspect.py tests/test_scalars.py --output-dir docs/builder/shadow`
- `uv run python scripts/review_inspect.py tests/types/test_converters.py --output-dir docs/builder/shadow`

`tests/base/test_init.py` is the only other file the build touched; per Slice 5's plan it received a one-literal `__version__` swap with no review-worthy logic. Skip with reason: **`tests/base/test_init.py` carries only line-pin updates (`__version__` literal + `__all__` set membership across Slices 1 and 5); no new control flow, no new symbols, no new branches.** Helper would produce no actionable cross-slice signal.

### Repeated-string-literal comparison across overviews

Pulled the `Repeated string literals` section from each post-Slice-6 overview:

- `django_strawberry_framework__scalars.overview.md` — `None.`
- `django_strawberry_framework__types__converters.overview.md` — `None.`
- `tests__test_scalars.overview.md` — `2x -9223372036854775808`, `2x 9223372036854775807` (int64-min and int64-max string forms; appear once on the parser side, once on the serializer side per `tests/test_scalars.py:36-43, 110-117`).
- `tests__types__test_converters.overview.md` — `15x NON_NULL`, `10x test_arrayfield`, `9x _ARRAY_FIELD_CLS`, `8x django.contrib.postgres.fields`, `7x test_hstorefield`, `6x FixtureType`, `6x _HSTORE_FIELD_CLS`, `5x test_bigint`, `4x test_choice_enums`, `4x Unsupported Django field type`, `4x { owner { data } }`, `3x archived`, `3x first-name`, `3x MEMBER_true`, `3x nullable_status`, `3x sanitize to the same enum member`, `3x OwnerType`, `3x test_jsonfield`, `2x Archived`, `2x MEMBER_FALSE`, `2x MEMBER_null`, `2x MEMBER___private`, `2x 4611686018427387904`.

**No cross-file repeated literal** — every literal flagged 2x+ is single-file (either inside `tests/types/test_converters.py` or inside `tests/test_scalars.py`). The shared contract symbol `Unsupported Django field type` appears 4x in `tests/types/test_converters.py` (assertion `match=` substrings) and exactly 1x in `django_strawberry_framework/types/converters.py` (the spec-pinned error message). That cross-file pair is the expected test-vs-source contract assertion, not duplication.

The within-file literal density of `_ARRAY_FIELD_CLS` (9x) and `_HSTORE_FIELD_CLS` (6x) in the test file is the spec-pinned `monkeypatch.setattr(converters, "_<NAME>_FIELD_CLS", ...)` recipe (Decision 7, spec line 635). Slice 3 + Slice 4 reviewers explicitly rejected extracting a `_patch_array_sentinel(monkeypatch, value)` helper because the literal **is** the load-bearing contract surface (it pins the BEFORE-DjangoType ordering and the exact module attribute name).

### Imports-direction comparison across overviews

Pulled the `Imports` section from each post-Slice-6 overview:

- `django_strawberry_framework/scalars.py` (lines 13-17) — standard library + Strawberry only. **No first-party import.** Module is leaf — `scalars.py` does not import from `types/`, `optimizer/`, `registry`, `conf`, or `exceptions`.
- `django_strawberry_framework/types/converters.py` (lines 15-31, plus soft-imports at lines 72 + 85) — standard library, Strawberry, Django, then four first-party imports: `..exceptions.ConfigurationError`, `..optimizer.field_meta.FieldMeta`, `..registry.registry`, `..scalars.BigInt`, `..utils.strings.pascal_case`, `.relations.PendingRelationAnnotation`. The soft-imports `django.contrib.postgres.fields.ArrayField` (line 72) and `django.contrib.postgres.fields.HStoreField` (line 85) live inside `_resolve_array_field` / `_resolve_hstore_field` function bodies — they are not module-load imports.
- `tests/test_scalars.py` (lines 10-16, plus a lazy `from django_strawberry_framework import BigInt` at line 219 inside `test_bigint_is_importable_from_top_level`) — clean test-side import shape; one first-party import for the parser/serializer + one lazy public-surface re-import for the smoke test.
- `tests/types/test_converters.py` (lines 21-31 module-level plus six inline test-local imports at lines 855, 861, 871, 874, 1208, 1214, 1224, 1227) — module-level imports the test surface; the inline imports are the `sys.modules`-manipulation helper-resolver tests' re-imports of `_resolve_array_field` / `_resolve_hstore_field` (Decision 7 spec lines 661-676; the re-imports must run after the `sys.modules` patch, so they cannot be hoisted).

**Dependency direction is one-way and clean:**

- `scalars.py` → no first-party deps (leaf).
- `types/converters.py` → `..scalars` (consumes `BigInt`), plus `..exceptions`, `..optimizer.field_meta`, `..registry`, `..utils.strings`, `.relations`. No cycle.
- Tests → first-party package; never the reverse.

No sibling has started importing across a documented boundary. The boundary `scalars.py` is a leaf module is preserved — `types/converters.py` consumes `BigInt` but `scalars.py` does not consume from `types/`.

### Carry-forward DRY watchpoint verdicts (post-walk)

#### 1. `_resolve_array_field` / `_resolve_hstore_field` near-twin helper pair

**Sites:** `django_strawberry_framework/types/converters.py:65-75` (Array) and `:78-88` (HStore). Bodies differ in exactly one identifier (`ArrayField` ⇄ `HStoreField`) plus the docstring symbol.

**Spec posture:** Decision 4 (spec lines 525-548) commits to two parallel single-purpose helpers.

**Consolidation candidates evaluated:**

- **`_resolve_postgres_field(name: str)` string-name factory.** Call sites become `_resolve_postgres_field("ArrayField")` / `_resolve_postgres_field("HStoreField")`. Loses IDE go-to-definition on the symbol name; the string-name argument is a runtime indirection that pushes the import-attribute lookup into a branch. Slice 3 + Slice 4 planners both explicitly rejected this shape.
- **`_resolve_postgres_attr(attr_name: str)` getattr-based factory.** Same drawback as the string-name factory plus an extra `getattr(module, name)` call inside the `try` block. Strictly worse.
- **A class-based registry `{"ArrayField": _resolve_array_field, ...}`.** Adds indirection for no reuse gain; the helpers are already named at module top-level and reading sequentially top-to-bottom.

**Verdict: keep two parallel helpers as the spec pinned.** The duplication is two near-identical four-line functions where the duplication is the name being soft-imported. A consolidation would either hide the symbol behind a string indirection (worse for IDE navigation, worse for static-analysis tools, worse for grep) or introduce a registry that adds indirection for zero reuse gain. The named-per-field shape is the right grain.

**Future trigger that would re-open this:** if a third postgres-field soft-import lands (e.g., a future `RangeField` or `CITextField` spec), the count crosses the threshold where a factory becomes worth its indirection cost. At two, it doesn't.

#### 2. `_ARRAY_FIELD_CLS` / `_HSTORE_FIELD_CLS` adjacent module-level sentinel pair

**Sites:** `converters.py:91-92`. Same annotation (`type[models.Field] | None`), same assignment shape, adjacent lines.

**Spec posture:** Decision 4 (spec lines 525-548) commits to two named sentinels, read by different branches in `convert_scalar` with different post-isinstance behavior.

**Consolidation candidates evaluated:**

- **Combined `_POSTGRES_FIELD_CLASSES: tuple[type[models.Field] | None, type[models.Field] | None] = (...)` constant.** Forces every `isinstance(field, ...)` call to dispatch on a tuple and loses the named contract for each branch. The two sentinels are read at different positions in `convert_scalar`: `_ARRAY_FIELD_CLS` is checked first (line 147) and recurses on `base_field`; `_HSTORE_FIELD_CLS` is checked second (line 165) and returns `JSON` directly. A tuple-form check `isinstance(field, _POSTGRES_FIELD_CLASSES)` would either need a post-`isinstance` branch on `which sentinel matched`, defeating the purpose, or lose the branch-specific behavior entirely.
- **`dict` of `{name: cls}` form.** Same problem; the dispatch order is part of the contract and a dict doesn't preserve it cleanly.

**Verdict: keep two named sentinels as the spec pinned.** The named-sentinel-per-branch shape is load-bearing — Slice 3's `test_array_field_sentinel_none_path` and Slice 4's `test_hstore_field_sentinel_none_path` pin that exact attribute name as the monkey-patch contract. Renaming or merging would force the test recipe (Decision 7 spec line 635) to change too.

#### 3. Parallel `convert_scalar` sentinel branches for ArrayField and HStoreField

**Sites:** `converters.py:147-160` (ArrayField, 14 lines) vs `:165-174` (HStoreField, 10 lines).

**Shared posture:** outer guard `if _<NAME>_FIELD_CLS is not None and isinstance(field, _<NAME>_FIELD_CLS):`, outer-`choices` rejection raising `ConfigurationError` naming `field.model.__name__` + `field.name`, outer-null widening via `return result | None if field.null else result`.

**Divergent post-isinstance bodies:** ArrayField rejects nested arrays then recurses via `convert_scalar(field.base_field, type_name)` and wraps the inner result in `list[...]`. HStoreField has no nested check and no recursion; returns `strawberry.scalars.JSON` directly.

**Spec posture:** Decision 5 (spec lines 552-571) says the HStoreField branch "mirrors Decision 2's shape" — the parallel-but-different is deliberate.

**Consolidation candidates evaluated:**

- **`_handle_postgres_field(field, type_name)` shared dispatcher.** Would force conditional sub-branches inside the body for the divergent post-isinstance work (nested-array check vs none; recursion vs direct JSON return). Net result: a longer single function with `if isinstance(field, _ARRAY_FIELD_CLS): ...; elif isinstance(field, _HSTORE_FIELD_CLS): ...` that hides the per-branch shape behind a dispatcher whose body is just the two original branches glued together.
- **`_postgres_branch_guard(field, sentinel)` returning bool.** Saves one line per call site (`if _postgres_branch_guard(field, _ARRAY_FIELD_CLS): ...`) but doesn't address the post-isinstance work, which is where the lines live.
- **Two helper functions `_handle_array_field(field, type_name)` / `_handle_hstore_field(field)` returning the resulting type.** Mechanically clean but reduces `convert_scalar`'s body to two `if ... return _handle_...(...)` lines — moving 24 lines of inline branches into two named helpers. Trade-off: the function's `Algorithm` docstring step 0 still must describe both branches; the inline bodies are short enough (10 + 14 lines) to read top-to-bottom; the helpers would be one-call-site each.

**Verdict: keep the inline branches as the spec pinned.** Bodies are ≤14 lines each, the spec's Decision 5 explicitly mirrors Decision 2's shape (parallel-but-different is the contract), and the inline branches read top-to-bottom without indirection. Worker 3 of Slice 4 wrote: "Worker 3's view: keep the named-sentinel-per-branch grain." That conclusion holds at integration time. Pulling the bodies into helper functions would add indirection for two one-call-site helpers; the gain is negligible against the cost of forcing a future reader to chase three names (`convert_scalar` + `_handle_array_field` + `_handle_hstore_field`) to read the dispatch.

#### 4. Outer-`choices` `ConfigurationError` rejection-message template

**Sites:** `converters.py:153-157` (ArrayField), `:167-172` (HStoreField). Plus the existing `:181-187` unsupported-field error message (pre-existing, not slice-introduced). All three name `field.model.__name__` + `field.name` and follow `<FieldType> on <Model>.<Field> <reason>; <rationale>; <recourse>`.

**Spec posture:** Decision 2 (spec lines 503-511) and Decision 5 (spec lines 563-568) pin the wording verbatim. The rationale text differs by field type (ArrayField: "outer-array choices are ambiguous"; HStoreField: "HStore stores a `dict[str, str | None]` with no enum-able shape"); the recourse hint differs by field type (ArrayField: "Declare choices on base_field for element-level enum, or use FilterSet"; HStoreField: "Drop the choices declaration or model the constrained shape with a separate field").

**Consolidation candidates evaluated:**

- **Shared `_OUTER_CHOICES_REJECTION_TEMPLATE = "{field_type} on {model}.{field} declares choices; {rationale}; {recourse}."` format string.** Each call site provides `field_type`, `rationale`, `recourse` as kwargs. Saves ~3 lines net across the two branches but requires inlining the spec-verbatim rationale + recourse text at the call site anyway, since those strings are spec-pinned. Net result: the template constant abstracts the wrapping shape (`"{field_type} on {model}.{field} declares choices; ...; ..."`) but the inside-template wording is still spec-verbatim at each site.
- **Two-arg helper `_outer_choices_rejection(field_type: str, field: models.Field, rationale: str, recourse: str)` raising `ConfigurationError`.** Encapsulates the `field.model.__name__` + `field.name` formatting. Each call site becomes a one-line raise. Saves ~5 lines net but pulls four arguments out of the call site — the `field_type` label, the rationale, the recourse, and the field.

**Verdict: keep the inline `raise ConfigurationError(...)` blocks as the spec pinned.** The template-shape consolidation saves at most ~3 lines and forces a level of indirection between the spec-verbatim wording and the source site. Two sites is below the threshold where a shared format constant pays for itself — the cost is one more named symbol to grep through, the benefit is three lines. The spec explicitly pinned both wordings verbatim; adding a template would require either inlining the spec wording at the call site (no DRY win) or paraphrasing it (a spec contract violation). Worker 1 of Slice 4 plan and Worker 3 of Slice 4 review both reached the same conclusion: defer; likely keep verbatim.

**Future trigger that would re-open this:** if a third sentinel-guarded postgres branch introduces a third near-template outer-choices rejection, the count crosses the threshold. At two, the gain is below the indirection cost.

#### 5. `_make_one_field_schema(model_cls, field_name)` test-helper extraction

**Sites:** `tests/types/test_converters.py`. The synthetic-model + `DjangoType` + in-function `Query` resolver pattern now appears at ~24 sites: 5 BigInt schema-execution tests (S1) + 3 JSONField tests (S2) + 9 ArrayField sentinel-branch tests including 1 gated (S3) + 7 HStoreField sentinel-branch tests including 1 gated (S4). Each test pairs:

1. (Sentinel branch tests only:) `monkeypatch.setattr(converters, "_<NAME>_FIELD_CLS", _Fake<Name>Field)`.
2. Synthetic Django model declaration with `class Meta: managed = False; app_label = "<slice-label>"`.
3. `DjangoType` declaration over the synthetic model.
4. `finalize_django_types()` invocation.
5. `@strawberry.type class Query` with a `@strawberry.field` resolver returning a synthetic instance.
6. `schema = strawberry.Schema(query=Query)`.
7. Assertion: introspection via `_introspect_field_type` / `_walk_introspected_type`, or `schema.execute_sync` round-trip, or `pytest.raises(ConfigurationError, match=...)`.

The parameter surface across all sites is **wider** than `(model_cls, field_name)`:

- **Whether a sentinel monkey-patch fires before steps 2-6.** Sentinel-branch tests need it; BigInt / JSONField / "real-postgres" gated tests don't.
- **Resolver return shape varies.** Some return a hand-built dict (`{"k1": "v1"}`), some return an instance with a single field (`Owner(big_int_field=2**62)`), some don't run a resolver (introspection-only tests), some return `None` (nullable cases).
- **Assertion shape varies.** Some `_introspect_field_type` introspection only; some `schema.execute_sync` round-trip; some `pytest.raises` at `DjangoType` declaration; some `pytest.raises` at schema execution.
- **`app_label` varies per slice** (`test_bigint`, `test_jsonfield`, `test_arrayfield`, `test_hstorefield`).
- **Whether `DjangoType` declaration is wrapped in `pytest.raises`.** Rejection tests wrap the declaration itself; introspection / round-trip tests don't.

**Consolidation candidates evaluated:**

- **`_make_one_field_schema(model_cls, *, resolver=None)` helper returning a built `Schema`.** Tests provide the model class + an optional resolver lambda; the helper builds the `Query` type and the schema. Three problems: (a) the model class must be declared per test (can't be a helper argument because it carries the `app_label` + `Meta` + the field declaration that's the subject of the test), so callers still write 6-7 lines of model boilerplate; (b) rejection tests need to wrap the `DjangoType` declaration itself in `pytest.raises`, which the helper can't host; (c) the introspection-only branch and the round-trip branch want different post-build steps. A helper would shrink ~5 of those 24 sites and leave the rest unchanged.
- **`_build_schema_for_django_type(django_type_cls)` lower-level helper.** Each test still declares its own model + `DjangoType`, then passes the type class to the helper. Saves the `@strawberry.type class Query: @strawberry.field def owner(self) -> ...: return ...` block, ~5 lines per call site. Multiplied across 24 sites, that's ~120 lines saved — meaningful.
- **`make_schema_with_owner_query(django_type_cls, value)` higher-level helper.** Builds the schema and the resolver returning `value`. Caller writes ~3 lines (model + DjangoType + helper invocation + assertion). The signature must thread the resolver value through `@strawberry.field`'s `info`-less call shape, and rejection-tests at `DjangoType` declaration time would still bypass the helper.

**Verdict: keep inline. The "trio pattern" is a misnomer — it's actually a 4-7-step recipe whose midpoints diverge.** The helper that would shrink the most call sites (`_build_schema_for_django_type`) would still leave the 24 model declarations and 24 `DjangoType` declarations inline (each is per-test). It saves only the inner `Query` definition. Each test currently reads top-to-bottom in 25-35 lines; extracting the helper would shorten each by 4-6 lines but require the reader to dereference the helper to see what happened. The introspection helpers (`_introspect_field_type`, `_walk_introspected_type`) are extracted because they replace a multi-line GraphQL introspection query literal + a 7-line chain walk with one call — the gain is concentrated. The trio-pattern's gain per call site is diffuse: the lines saved are the most-readable lines (the `@strawberry.type class Query` and `@strawberry.field def owner` definitions are mechanically obvious; the test-specific lines — the model fields, the `DjangoType.Meta.fields`, the assertion target — are not).

**Worker 3 of Slice 4** reached the same conclusion: "The duplication is intentional at this stage; each test reads top-to-bottom without indirection." With full post-Slice-6 parameter-surface visibility, the conclusion holds. The helper that would actually pay for itself (a `_build_schema_for_django_type(django_type_cls)` that takes a class and returns a schema, leaving the resolver responsibility to the caller) shrinks each site by 4-6 lines but doesn't subsume any of the test-specific lines. The net readability gain is below the indirection cost.

**Future trigger that would re-open this:** if a future slice adds another ~10 sentinel-branch tests of the same shape (e.g., a `RangeField` slice), the count crosses ~35 and the diffuse gain accumulates. At 24, it doesn't.

#### 6. `app_label` literal density across `tests/types/test_converters.py`

**Counts (post-Slice-6, per the regenerated shadow):** `"test_arrayfield"` 10x, `"test_hstorefield"` 7x, `"test_bigint"` 5x, `"test_choice_enums"` 4x, `"test_jsonfield"` 3x. **Total: 29 occurrences across 5 labels.**

**Spec posture:** Decision 7 (spec lines 641-646) names per-slice unique `app_label`s as the convention. No upstream rule pins whether to use literals or constants.

**Consolidation candidates evaluated:**

- **Module-level constants block (`_APP_LABEL_BIGINT = "test_bigint"`, etc.).** Replaces the literal at every model-declaration site with the constant name. Saves zero characters at each site (the name is roughly the same length as the literal) but routes the lookup through one canonical definition. Slight grep-discoverability win: searching for `_APP_LABEL_BIGINT` finds the definition + the usages; searching for `"test_bigint"` already does the same.
- **Per-test inline literals (current shape).** Each model declaration reads top-to-bottom with the `app_label` adjacent to the model field declarations.

**Verdict: keep inline literals.** Constants would route the lookup through one canonical name but at no readability gain at the call site (each model declaration is already a 5-7-line block where the `app_label` is one line of context). The 29-occurrence count looks high but it's spread across 5 distinct labels (one per slice) — each label appears at most 10 times, which is the BigInt-era + sentinel-branch-test scale. The literal value is grep-discoverable; the test-helper pattern already groups tests by section banner so a reader scanning the file finds the per-slice cluster by the banner, not by the `app_label` value.

**Future trigger that would re-open this:** if a single `app_label` value approaches ~20 occurrences within one slice's cluster, or if a sixth label is added by a future slice pushing the total past ~40, the gain accumulates. At 29 across 5 labels, the gain is below the indirection cost.

### Cross-cutting concerns checklist (BUILD.md "The integration pass itself should check")

- **Duplicated helpers across slices.** Walked above for `_resolve_*_field`, sentinels, `convert_scalar` branches, `_make_one_field_schema`. No new duplication beyond the explicitly-deferred-and-evaluated set. Verdict: no action.
- **Inconsistent naming or error handling between slices.** ArrayField + HStoreField branches both use `ConfigurationError` with the spec-verbatim wording; both name `field.model.__name__` + `field.name`; both end with a consumer-actionable recourse hint. The MRO walk's `Unsupported Django field type` error pre-existed Slices 1-4 and is referenced consistently from each new sentinel-branch sentinel-none-path test. Naming convention `_<NAME>_FIELD_CLS` is parallel; helper names `_resolve_<name>_field` are parallel; test names `test_<field>_<scenario>_via_fake_sentinel` are parallel. Verdict: clean.
- **Repeated ORM/queryset patterns that should be centralized.** No new ORM/queryset patterns introduced — Slices 1-6 add converter dispatch + tests; they do not touch queryset construction or `select_related` / `prefetch_related` chains. Verdict: not applicable.
- **Misplaced responsibilities between modules touched by different slices.** `scalars.py` is a leaf module (defines `BigInt`); `types/converters.py` consumes it via `from ..scalars import BigInt`. The dispatch logic (MRO walk + sentinel branches + null widening + choice substitution) lives entirely in `types/converters.py`; the strict parser / serializer / wire format lives in `scalars.py`. No responsibility leak: the converter does not parse / serialize, and the scalar does not dispatch / soft-import. Verdict: clean.
- **Missing or too-broad exports introduced by the build.** Slice 1 added exactly `"BigInt"` to `__all__` (alphabetized first). Slices 2-6 added zero public exports. `strawberry.scalars.JSON` (used at `SCALAR_MAP` row + HStoreField branch return) is accessed via dotted attribute on the existing `import strawberry`, not re-exported. The helpers `_resolve_array_field` / `_resolve_hstore_field` and sentinels `_ARRAY_FIELD_CLS` / `_HSTORE_FIELD_CLS` are module-private (leading-underscore). `_parse_bigint` / `_serialize_bigint` in `scalars.py` are module-private. Verdict: no surface leak; the spec's pinned `__all__` tuple (spec lines 78-87) is the canonical contract and matches the live surface exactly.
- **Repeated string literals / dictionary keys / tuple shapes across slices.** Walked above. No cross-file literal that warrants centralization. `Unsupported Django field type` is the one cross-file test-vs-source contract assertion and stays inline by design.
- **Whether comments now tell one coherent story across the new code.** Spot-walked the comment blocks:
  - `scalars.py:79-90` — anchors the suppression rationale and points at `TODO-ALPHA-045-0.0.7` for the warning-free migration path.
  - `converters.py:141-146` — describes the ArrayField sentinel branch's pre-MRO-walk ordering rationale and the recursion-into-`base_field` flow.
  - `converters.py:161-164` — describes the HStoreField sentinel branch's parallel posture to ArrayField, plus the no-recursion direct-JSON-return divergence.
  - `converters.py:176-181` — describes the MRO walk's purpose and the consumer-subclass scenario it serves (unchanged from pre-Slice-3 except for renumbering).
  - `tests/types/test_converters.py:103-105` / `:265-268` / `:338-340` / `:409-418` / `:734-` / `:840-` / `:1189-` — section banners group tests by subsystem (choice enums / direct unit helper coverage / MRO subclass resolution / BigInt / JSON / ArrayField / HStoreField); each banner names the slice and the `app_label` convention.

  The comments collectively tell a coherent story: the new dispatch surface (sentinel branches + MRO walk) is documented inline at the source site; the test file's section banners narrate the per-slice scope. No stale comments, no contradiction between comments and behavior. Verdict: coherent.

### Deferred follow-ups walked from prior artifacts

Per BUILD.md "Walk every accepted slice artifact's `What looks solid` and `DRY findings` sections to catch any deferred follow-up that should land in this pass":

- **Slice 1 — Worker 3's Low #1** (parser-negative `match=` substrings): explicitly optional polish; the diversity of inputs across 11 negative tests triangulates the reject paths. **Not actioned at integration; remains optional polish.**
- **Slice 1 — Worker 3's Low #2** (reject-at-schema-boundary inbound tests assert only `len(result.errors) > 0`): explicitly optional polish per the plan's discretion item. Worker 2 chose the asymmetric shape (outbound asserts substring, inbound asserts non-empty). **Not actioned at integration.**
- **Slice 3 — Worker 3's Low** (`convert_scalar` docstring drift): explicitly deferred to Slice 4 and resolved there (Worker 2 of Slice 4 rewrote the Algorithm + Raises sections per the plan's step 4). **Resolved; no integration action.**
- **Slice 1 — Notes for Worker 1 (GraphQL camelCase translation)**: Strawberry's documented default; not a spec gap. Worker 1 of Slice 1 final-verification decided no anchoring in the spec needed. **No integration action.**
- **Two pre-existing `test_choice_enums._owner` re-registration `RuntimeWarning`s.** Carry through all six slices as 2x warnings on every focused-test run. Not introduced by Slices 1-6; predate this build cycle. Out of scope for the integration pass (the build did not author the `_owner` re-registration shape). **Recorded for the maintainer; no integration action.**

### `BigInt` ↔ `strawberry.scalars.JSON` reference-site distribution (single-site evaluation)

Per the task brief's framing on `strawberry.scalars.JSON` cross-slice DRY watchpoint: Slice 2 introduced the first call site (`SCALAR_MAP` row at `converters.py:46`) and Slice 4 introduced the second call site (HStoreField sentinel branch return at `converters.py:173`).

**Sites confirmed via shadow:**

- `converters.py:46` — `models.JSONField: strawberry.scalars.JSON,` (SCALAR_MAP row).
- `converters.py:173` — `py_type = strawberry.scalars.JSON` (HStoreField sentinel branch).

**Consolidation candidate:** module-level alias `_JSON_SCALAR = strawberry.scalars.JSON` at module top + reference at both sites.

**Verdict: keep direct attribute access at both sites.** Two call sites is the minimum threshold where an alias is even worth considering; the indirection cost (one extra name to grep through, one extra read-on-import) is comparable to the two-call-site dedup gain. The two sites have differing surrounding context (dict-value in the dispatch table vs. branch return in `convert_scalar`); the alias would route both through one name but neither site would read shorter. Direct attribute access on `strawberry` (already imported at module top) is the clearer shape.

## Integration verdict

**No actionable cross-slice DRY consolidation.** Every deferred watchpoint walked above resolves to "keep as the spec pinned" with a recorded rationale. The duplication observed is:

- **Intentional and pinned by spec** (the two-parallel-helpers shape for `_resolve_*_field`, the parallel-but-different `convert_scalar` branches, the verbatim outer-`choices` rejection wording).
- **Load-bearing for the test recipe** (the `_<NAME>_FIELD_CLS` monkey-patch literal is the spec-pinned contract surface; the synthetic-model + `DjangoType` + `Query` trio's mid-step divergence makes extraction hide more than it shows).
- **Below the indirection-cost threshold** (`strawberry.scalars.JSON` at two sites, `app_label` literals at 5 distinct labels across 29 occurrences, two near-twin helpers, one shared outer-`choices` template wording).

No cross-cutting concern (inconsistent naming, misplaced responsibility, surface leak, repeated literal warranting centralization, incoherent comment story) surfaced during the walk. The build delivered the spec end-to-end through six slices; each per-slice deferral was either intentional and pinned, or evaluated at integration time against full parameter-surface visibility and judged below the consolidation threshold.

The integration pass therefore introduces no consolidation work and proceeds directly to `final-accepted` without dispatching Worker 2.

### Summary

Build cycle: Slices 1-6 of `deferred_scalars` shipped against `docs/SPECS/spec-deferred_scalars.md` (archived during Slice 6 final verification from `docs/spec-deferred_scalars.md`). Cross-slice integration pass walked all six per-slice artifacts, regenerated four shadow overviews, compared `Repeated string literals` + `Imports` sections, and evaluated six deferred DRY watchpoints + one cross-slice symbol-reference candidate (`strawberry.scalars.JSON`).

**Outcome: no consolidation work warranted.** Every duplication observation either (a) is spec-pinned and load-bearing for the test contract, (b) shares posture but diverges in body in ways that defeat dispatcher extraction, (c) sits below the two-or-three-site indirection-cost threshold, or (d) carries pinned-verbatim spec wording that a shared template would either inline (no DRY win) or paraphrase (a spec violation). One-way dependency direction is clean (`scalars.py` is a leaf; `types/converters.py` consumes it; tests consume the package). No surface leak: `__all__` change is exactly `+"BigInt"` per spec line 78-87 and matches the live surface. Comments tell a coherent story across `scalars.py` + `converters.py` + `tests/types/test_converters.py`.

The build proceeds to the final test-run gate (`docs/builder/bld-final.md`) per BUILD.md.

### Spec changes made (Worker 1 only)

None.
