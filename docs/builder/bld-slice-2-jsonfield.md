# Build: Slice 2 — `JSONField` mapping

Spec reference: `docs/spec-deferred_scalars.md` (Slice checklist lines 139-145, Decision 3 line 523, Decision 7 / Schema test fixture pattern lines 594-705, Decision 8 lines 708-710, User-facing API lines 712-729, Test plan categories 6-8 lines 786-794, Slice 2 description line 739-741)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - `SCALAR_MAP` flat-dict pattern at `django_strawberry_framework/types/converters.py:41-69`. The Slice 1 changes already widened the dict's declared value type to `dict[type[models.Field], Any]` (line 41) and inserted `models.BigIntegerField: BigInt` and `models.PositiveBigIntegerField: BigInt` as non-`type` `Any` values, so `strawberry.scalars.JSON` (also a `NewType`-backed scalar wrapper, not a plain `type`) slots in as one more `Any`-typed row without further annotation work.
  - `convert_scalar` MRO walk + null-widening branch in `converters.py:72-119`. Adding `models.JSONField: strawberry.scalars.JSON` to `SCALAR_MAP` automatically inherits both the MRO subclass-resolution walk (lines 105-108) and the `T | None` widening (lines 117-118) for free — no new branching logic, no `convert_scalar` change. This is the same shape Slice 1 used for the `BigIntegerField` / `PositiveBigIntegerField` rows.
  - Test-isolation autouse fixture `_isolate_registry` at `tests/types/test_converters.py:37-47`. Per Decision 7's "Schema test fixture pattern" preamble (spec lines 637-639), new tests added inside `test_converters.py` inherit this autouse fixture automatically; no `conftest.py` work is required.
  - In-function model declaration pattern established by Slice 1's BigInt tests at `tests/types/test_converters.py:449-699`. Each test declares its own `class _Owner(models.Model): ... class Meta: managed = False; app_label = "..."`, declares the matching `DjangoType`, calls `finalize_django_types()`, builds the schema, and asserts. Slice 2 follows this verbatim — three tests, each declaring its own one-field synthetic model + `DjangoType` + `Query` resolver.
  - Introspection helpers `_walk_introspected_type` and `_introspect_field_type` at `tests/types/test_converters.py:420-446` (added by Slice 1). They walk the GraphQL introspection chain to the terminal `SCALAR { name: "..." }` regardless of nullability wrapping (`NON_NULL` → ...). Slice 2's introspection-shape tests reuse them unchanged: `JSON!` is `NON_NULL → SCALAR { name: "JSON" }` (same two-level chain as `BigInt!`); nullable `JSON` is the bare terminal payload (same shape as nullable `BigInt`). The 3-level `ofType` nesting Slice 1's helper supports is enough — Slice 2 does not need Slice 3's deeper `list[T]` nesting.
  - `schema.execute_sync` wire-level round-trip pattern at `tests/types/test_converters.py:573-599` (Slice 1's `test_bigint_serializes_query_result_as_string_via_schema_execution`). The dict round-trip test for JSON follows the same shape: build a resolver returning a hand-built Python `dict`, execute `{ owner { jsonField } }`, assert `result.data == {"owner": {"jsonField": {...}}}`. `strawberry.scalars.JSON`'s serializer is the identity for JSON-compatible Python values, so the dict appears verbatim in `result.data`.
  - `strawberry.scalars.JSON` import path. Strawberry exposes `JSON` at `strawberry.scalars.JSON` (verified by Slice 1's spec context references and the spec's Decision 3 at line 523). It does not need a separate top-level import in `converters.py` — `import strawberry` is already at `converters.py:23`, so `strawberry.scalars.JSON` is accessible as a dotted attribute.

- **New helpers justified.**
  - **None.** Slice 2 adds exactly one row to `SCALAR_MAP` and three tests; no helper is justified. The MRO walk + null widening + (irrelevant for JSON) choice substitution branch already cover the dispatch. The three tests reuse Slice 1's `_introspect_field_type` / `_walk_introspected_type` helpers verbatim — no new test helper either.
  - **Justification for not extracting a `_make_one_field_schema(model_cls, field_name)` helper here.** Worker 3's Slice 1 review (`docs/builder/bld-slice-1-bigint_scalar.md` "DRY findings" section) flagged this as a deferred candidate if Slices 2-4 repeat the synthetic-model + `DjangoType` + `Query` trio shape. Slice 2 adds three tests with this shape, but extracting now is premature — the helper would need to parameterize the resolver's return value (dict vs. `None` vs. nested-shape) and the introspected type name (`JSON` vs. `JSON | None`), and that parameter surface only becomes visible once Slices 3 and 4 also land their fake-sentinel-driven tests. The integration pass is the natural moment to hoist the helper if Slices 3 and 4 follow the same shape. Recording the watchpoint here so the integration-pass plan can pick it up cleanly.

- **Duplication risk avoided.**
  - **Risk #1: a separate `JSONField` import or alias.** `strawberry.scalars.JSON` is already accessible via the existing `import strawberry` at `converters.py:23`. Adding `from strawberry.scalars import JSON` would shadow the consumer-facing dotted access path (which is the form the spec at line 523 and the User-facing API table at line 720 both name) and add a second name for the same scalar. Do NOT add the alias; reference `strawberry.scalars.JSON` directly inside the `SCALAR_MAP` literal.
  - **Risk #2: structurally duplicating the future Slice 4 `HStoreField` mapping.** Slice 4 maps `HStoreField` to `strawberry.scalars.JSON` as well, but via a *sentinel-guarded `convert_scalar` branch* (Decision 5, spec lines 550-571) — not via `SCALAR_MAP`. The duplication is "same target scalar, different dispatch path" — Slice 2 hits the `SCALAR_MAP` walk, Slice 4 hits an explicit `isinstance(field, _HSTORE_FIELD_CLS)` branch that runs *before* the MRO walk (spec line 555 "after the ArrayField branch, before the SCALAR_MAP walk"). The target literal `strawberry.scalars.JSON` ends up appearing in two physically distinct sites in `converters.py` after Slice 4. **Flag this as the integration-pass DRY watchpoint**: if both sites reference the same value, the integration pass should evaluate whether a module-level `_JSON_SCALAR = strawberry.scalars.JSON` constant tightens the file. Probably not — the two sites have different surrounding context (a dict value vs. a branch return), and a one-liner alias for a two-call-site reference is over-DRY. Recording so Slice 4's planning pass and the integration pass can revisit deliberately. (Slice 2's lighter precursor here lands the *first* of the two sites; Slice 4's plan will own the de-dup decision once the second site lands.)
  - **Risk #3: re-implementing the introspection chain walk inline in the new tests.** Slice 1 already factored `_walk_introspected_type` and `_introspect_field_type`. Slice 2's introspection-shape tests (`test_json_field_maps_to_json_scalar_in_schema`, `test_json_field_nullable_in_schema`) must reuse these helpers — Worker 2 must not re-inline the chain literal inside the new tests. Recording so Worker 2 picks up the helpers when planning the assertion shape.
  - **Risk #4: duplicating Slice 1's BigInt synthetic-model app_label.** Slice 1 uses `app_label = "test_bigint"` (5x repetition flagged in Worker 3's Slice 1 DRY findings). Slice 2's three tests need a distinct `app_label` so the synthetic-app namespaces don't collide (Django's app registry tracks `(app_label, model_name)` pairs; using `"test_bigint"` for a JSON-field model would cohabit with the BigInt fixture models in the same synthetic app, which is benign but obscures the test's intent). Use `app_label = "test_jsonfield"` — distinct, grep-discoverable, and parallel to Slice 1's convention. Worker 3's Slice 1 finding noted that if Slices 2-4 add similar 5x patterns, a module-level constants block becomes warranted; with 3 tests in Slice 2 the count stays small, but Slices 3 and 4 (each with a similar fake-sentinel suite) may push the literal count past the threshold. Recording so the integration pass can decide.

- **Static helper observations** (from `docs/builder/shadow/django_strawberry_framework__types__converters.overview.md`, regenerated against post-Slice-1 source):
  - `SCALAR_MAP` is at the lines 41-69 control-flow site; the BigInt-related TODO is gone (Slice 1 removed it). Two TODO comments remain: line 33 (ArrayField, Slice 3) and line 37 (JSONField and HStoreField, Slices 2 + 4). Slice 2 must drop the `JSONField` half of the line-37 TODO without disturbing the `HStoreField` half — the spec at line 141 names this surgical edit.
  - `convert_scalar` is 48 lines / 5 branches — unchanged from Slice 1's post-state. Slice 2 does not touch `convert_scalar`'s body.
  - `Repeated string literals` section is `None.` — no cross-file literal DRY signal. The integration pass will reassess after all four converter-touching slices land.
  - `Imports` section shows `from ..scalars import BigInt` at line 29 (Slice 1). No new import is needed for Slice 2 — `strawberry.scalars.JSON` is reached via the existing `import strawberry` at line 23.
  - **Cross-slice DRY note for Slice 4's planner.** Slice 2 (this slice) is the *lighter precursor* of Slice 4's `strawberry.scalars.JSON` mapping. Both target the same scalar; Slice 2 dispatches via `SCALAR_MAP`, Slice 4 dispatches via a sentinel-guarded branch in `convert_scalar`. After Slice 4 lands, `strawberry.scalars.JSON` will appear at two distinct call sites in `converters.py` — one as a dict value, one as a branch return. The integration pass should evaluate whether a module-level alias tightens the file or just adds an indirection step. Recording this here as Slice 2's DRY-analysis output so Slice 4's planner can pick it up (e.g., consider whether Slice 4 should de-dup by adding an alias at the same change, or whether the integration pass owns it).

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written.

1. **Extend `SCALAR_MAP` in `django_strawberry_framework/types/converters.py`** (`converters.py:41-69`).
   - Add `models.JSONField: strawberry.scalars.JSON,` as a new row.
   - Placement: anywhere within the dict; suggested position is after `models.DurationField: datetime.timedelta,` (line 64) and before `models.UUIDField: uuid.UUID,` (line 65) so the new "container-shaped" type lands away from the integer / boolean / float cluster (lines 52-59) and the date-time cluster (lines 61-64). Implementer's discretion on exact line — the dict is unordered for runtime purposes; readability is the constraint.
   - No annotation widening needed; Slice 1 already widened the dict to `dict[type[models.Field], Any]` (line 41). `strawberry.scalars.JSON` is a `NewType`-backed scalar wrapper, not a plain `type`, so it slots in under the `Any` value-type without further work.
   - No new import needed. `strawberry.scalars.JSON` is reached via the existing `import strawberry` at `converters.py:23`. Do NOT add `from strawberry.scalars import JSON` — see DRY Risk #1.

2. **Drop the `JSONField` half of the JSON / HStore TODO comment** at `converters.py:37-39`. The current three-line TODO reads:
   ```python
   # TODO(future): handle ``JSONField`` and ``HStoreField`` via Strawberry's
   # JSON scalar (``strawberry.scalars.JSON``). Both columns deserialize to
   # native Python dict / list shapes; the GraphQL schema sees them as ``JSON``.
   ```
   After Slice 2, the comment must still anchor the **HStoreField** deferral (Slice 4's TODO site per `AGENTS.md` "Design docs and TODO anchors"). Rewrite the comment to reference only `HStoreField`; suggested replacement (implementer's discretion on exact wording):
   ```python
   # TODO(future): handle ``HStoreField`` via Strawberry's JSON scalar
   # (``strawberry.scalars.JSON``) under a sentinel-guarded branch (postgres-
   # contrib soft-required). See ``docs/spec-deferred_scalars.md`` Slice 4.
   ```
   Do NOT remove the `ArrayField` TODO at `converters.py:33-35` — that is Slice 3.
   Do NOT collapse the whole JSON/HStore TODO away — the HStoreField half must remain anchored at its current source site so Slice 4's planner has a grep target.

3. **Verify (in Worker 2's diff and Worker 3's review) that no other line in `converters.py` is touched.** The Slice 2 contract is exactly +1 `SCALAR_MAP` row and one TODO comment rewrite. The `convert_scalar` body, the `convert_choices_to_enum` body, the `resolved_relation_annotation` / `convert_relation` bodies, and the imports block are all out of scope.

4. **Extend `tests/types/test_converters.py`** with the three new tests at the file's end (after the existing BigInt section at lines 408-699). Mirror the BigInt section's pattern: a section banner comment introducing the JSONField group, then the three tests in declaration order. The autouse `_isolate_registry` fixture at lines 37-47 already covers per-test registry cleanup; the new tests inherit automatically.
   - Add a section banner comment block similar to the BigInt section at lines 408-417, naming `app_label = "test_jsonfield"` so future readers know where to look. Implementer's discretion on exact wording.

5. **Test #1: `test_json_field_maps_to_json_scalar_in_schema`** — pins the introspection shape `JSON!` for a non-null `JSONField`.
   - Declare `class JsonOwner(models.Model): data = models.JSONField(); class Meta: managed = False; app_label = "test_jsonfield"`.
   - Declare `class JsonOwnerType(DjangoType): class Meta: model = JsonOwner; fields = ("data",)`.
   - Call `finalize_django_types()`.
   - Build a `@strawberry.type class Query` exposing the type via a `@strawberry.field` resolver returning `JsonOwner(data={"k": "v"})` (or any JSON-compatible dict).
   - `schema = strawberry.Schema(query=Query)`.
   - Use `_introspect_field_type(schema, "JsonOwnerType", "data")` to retrieve the introspected `type` payload.
   - Assert `type_payload["kind"] == "NON_NULL"` (top wrapper), then `terminal = _walk_introspected_type(type_payload)` and `terminal["kind"] == "SCALAR"`, `terminal["name"] == "JSON"`.
   - This mirrors `test_big_integer_field_maps_to_bigint_in_schema` at lines 449-478 verbatim except for the field type and the expected scalar name.

6. **Test #2: `test_json_field_nullable_in_schema`** — pins the introspection shape `JSON` (nullable) for `JSONField(null=True)`.
   - Same scaffold as Test #1 but the model uses `data = models.JSONField(null=True)` and a distinct class name (e.g., `JsonNullableOwner` / `JsonNullableOwnerType`) so the schema's `__type` lookup resolves cleanly. (See Worker 2's Slice 1 build-report `### Implementation notes` for why distinct PascalCase class names matter under the shared `app_label`.)
   - Resolver may return `JsonNullableOwner(data=None)`.
   - Assert `type_payload == {"kind": "SCALAR", "name": "JSON", "ofType": None}` (no `NON_NULL` wrapper). This mirrors `test_big_integer_field_nullable_in_schema` at lines 481-507 verbatim except for the field type and scalar name.
   - Alternative assertion shape (implementer's discretion): walk via `_walk_introspected_type` and assert `terminal["kind"] == "SCALAR"`, `terminal["name"] == "JSON"`. Either shape is acceptable; the dict-equality form is slightly tighter and matches the BigInt nullable test's style.

7. **Test #3: `test_json_field_round_trips_dict_via_schema_execution`** — pins the wire-level dict round-trip via `schema.execute_sync`.
   - Declare a third synthetic model and `DjangoType` pair (distinct class names again, e.g., `JsonRoundTripOwner` / `JsonRoundTripOwnerType`).
   - Resolver returns `JsonRoundTripOwner(data={"k1": "v1", "k2": 2, "k3": [1, 2, 3], "k4": None})` — a JSON-shaped Python value exercising strings, ints, lists, and `None`. The shape choice pins that `strawberry.scalars.JSON` is the identity serializer for JSON-compatible Python values; it doesn't probe the corners (those are Strawberry's contract, not the package's), it just confirms the end-to-end wiring.
   - Execute `result = schema.execute_sync("{ owner { data } }")`.
   - Assert `result.errors is None` and `result.data == {"owner": {"data": {"k1": "v1", "k2": 2, "k3": [1, 2, 3], "k4": None}}}`.
   - This mirrors `test_bigint_serializes_query_result_as_string_via_schema_execution` at lines 573-599 with the JSON dict as the resolver return shape. The "GraphQL field-name camelCase translation" Worker 2 flagged in Slice 1 does not apply here — `data` is a single word, so it appears as `data` in the schema.

### Test additions / updates

All three tests are spec-required (spec lines 142-145); no temp/scratch tests anticipated.

- **`tests/types/test_converters.py` (extended)**: 3 schema-execution tests appended after the existing BigInt section (currently ending at line 699). Assertion shapes:
  - Schema-shape introspection tests (#1, #2): reuse `_introspect_field_type` / `_walk_introspected_type`; assert on terminal `kind` and `name` (`"SCALAR"` and `"JSON"`); for non-null, additionally assert top-level `kind == "NON_NULL"`.
  - Wire-level dict round-trip test (#3): assert `result.errors is None` and dict-equality on `result.data`.
  - All three use the in-function model declaration pattern with `managed = False; app_label = "test_jsonfield"`.

- **No temp/scratch tests anticipated.** The three spec-named tests live as permanent tests. Worker 3 may probe with temp tests under `docs/builder/temp-tests/slice-2-jsonfield/` if introspection chain shape proves surprising for a Strawberry version difference, but no temp tests are pre-flagged here.

- **No changes to `tests/test_scalars.py`.** That file is `BigInt`-specific (the `_parse_bigint` / `_serialize_bigint` strict-parser / strict-serializer + deprecation-suppression coverage); JSONField has no package-defined parser/serializer to test (Strawberry's `strawberry.scalars.JSON` is upstream).

- **No changes to `tests/base/test_init.py`.** Slice 2 adds no public symbol — `strawberry.scalars.JSON` is accessed via dotted attribute and is not re-exported from `django_strawberry_framework.__all__`. The `BigInt`-augmented `__all__` set from Slice 1 stays exactly the same.

### Implementation discretion items

- **Row placement of `models.JSONField: strawberry.scalars.JSON,` inside `SCALAR_MAP`**: Worker 2 picks the position that reads cleanest with the surrounding rows. Suggested position is after the datetime cluster (line 64) and before `UUIDField` (line 65); other reasonable positions include end-of-dict (after `ImageField` at line 68) or grouped with `BinaryField` at line 66 (both "non-scalar-shaped" container columns). The dict is unordered at runtime; readability is the only constraint.

- **Exact wording of the rewritten TODO comment** at `converters.py:37-39`. The constraint is that the rewritten comment must still anchor the HStoreField deferral (per `AGENTS.md` "Design docs and TODO anchors" — the TODO comment names the active design doc and slice). The suggested replacement in Implementation Steps #2 is a starting point; Worker 2 may rephrase for clarity. Do not remove the comment block entirely.

- **Synthetic-model class naming scheme** for the three tests. Worker 2 may use `JsonOwner` / `JsonNullableOwner` / `JsonRoundTripOwner` (suggested) or a different scheme — the constraint is distinct PascalCase model + DjangoType class names per test under the shared `app_label = "test_jsonfield"`. See Worker 2's Slice 1 build-report `### Implementation notes` for the rationale (introspection-by-GraphQL-type-name resolves cleanly when class names are distinct).

- **`app_label` choice**: `"test_jsonfield"` is suggested as the natural parallel to Slice 1's `"test_bigint"`. Worker 2 may pick a more specific value (e.g., `"test_scalars_jsonfield"`) if it improves grep-discoverability. The constraint is that it must not collide with `"test_choice_enums"` or `"test_bigint"`.

- **Dict shape for the round-trip test (#3)**: the suggested shape `{"k1": "v1", "k2": 2, "k3": [1, 2, 3], "k4": None}` exercises strings, ints, lists, and `None`. Worker 2 may pick a different JSON-shaped value (e.g., a nested dict, a single-key dict, an empty dict) — the spec name says "round_trips_dict" so the test must use a dict value at the top, but the contents are at the implementer's discretion. The shape choice should be readable and exercise at least two value-shape kinds so the test pins more than the trivial `{}` case.

- **Section banner comment wording** for the new JSONField group at the bottom of `tests/types/test_converters.py`. Worker 2 picks the wording; the constraint is that it parallels the BigInt section banner at lines 408-417 (a brief explainer naming the `app_label` and the in-function-model pattern).

- **Test #2 assertion shape** (`type_payload == {...}` dict-equality vs. walk-and-assert). Either is acceptable per Implementation Steps #6. Worker 2 picks based on which form reads more directly. Slice 1's BigInt nullable test at line 507 uses dict-equality (`assert type_payload == {"kind": "SCALAR", "name": "BigInt", "ofType": None}`); mirroring that style is the closest fit.

Items NOT delegated (architectural; resolvable from spec or escalated if not):

- The `SCALAR_MAP` row contents (`models.JSONField: strawberry.scalars.JSON`) — pinned by Decision 3 (spec line 523) and Slice 2 checklist (spec line 140), no discretion.
- The three test names (`test_json_field_maps_to_json_scalar_in_schema`, `test_json_field_nullable_in_schema`, `test_json_field_round_trips_dict_via_schema_execution`) — pinned by Slice 2 checklist (spec lines 143-145), no discretion.
- The TODO-comment scope (drop JSONField half only; preserve HStoreField half) — pinned by Slice 2 checklist (spec line 141) and Slice 4 contract (spec line 173), no discretion.
- The "no new public export" contract — pinned by Slice 2's narrow checklist (spec lines 139-145) and the absence of any `__all__` change in the Slice 2 deliverables, no discretion. Worker 3 must verify via the public-surface check that `django_strawberry_framework/__init__.py` and `tests/base/test_init.py` are not modified in Slice 2's diff.

### Notes for Worker 1 (final-verification self-handoff)

- Re-verify during final verification that no row beyond `models.JSONField: strawberry.scalars.JSON` was added to `SCALAR_MAP`. The Slice 2 contract is exactly +1 dict row.
- Re-verify that the `ArrayField` TODO at `converters.py:33-35` is **untouched** and that the JSONField/HStoreField TODO at `converters.py:37-39` retains its HStoreField anchor. If Worker 2's diff removes either the ArrayField TODO or both halves of the JSON/HStore TODO, that is plan-vs-implementation drift and must be rejected.
- Re-verify that `django_strawberry_framework/__init__.py` and `tests/base/test_init.py` are **not** in the diff. Slice 2 adds no public symbol; both files should be untouched.
- Spec status line (`Status: draft (revision 10, post-feedback2 re-review)`) re-verification: still accurate at planning time. Archival lifecycle is Slice 6's job, not Slice 2's.
- Cross-slice carry-forward to Slice 4 planning: `strawberry.scalars.JSON` will appear at a second call site in `converters.py` after Slice 4 lands (as the branch return inside the sentinel-guarded HStoreField branch). The integration pass should evaluate whether to introduce a module-level `_JSON_SCALAR = strawberry.scalars.JSON` alias. Slice 2 is the lighter precursor — the alias decision can wait for the integration pass after both sites exist. Worker 1 (this same planner role, on its next spawn) should pick this up when planning Slice 4.
- Cross-slice carry-forward to integration-pass planning: Worker 3's Slice 1 review flagged `_make_one_field_schema(model_cls, field_name)` as a deferred helper candidate. Slice 2 adds 3 more uses of the synthetic-model + `DjangoType` + `Query` trio shape (now 4 + 3 = 7 instances if I'm counting Slice 1's introspection-shape subset correctly). If Slices 3 and 4 add another ~6-10 instances of the same shape, the integration pass should plan the helper extraction. Recording the count progression so the integration-pass plan has a concrete trigger.
- Cross-slice carry-forward: Slice 1's review flagged the `app_label` literal repetition (`"test_bigint"` 5x). Slice 2 adds `"test_jsonfield"` 3x. With Slices 3 and 4 likely adding similar patterns, the total literal count across slices will approach ~20. The integration pass should evaluate whether a module-level constants block (`_BIGINT_APP_LABEL = "test_bigint"`, `_JSON_APP_LABEL = "test_jsonfield"`, etc.) is justified or whether per-test inline literals stay clearer. Recording so the integration-pass plan has the data.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/converters.py` — added the `models.JSONField: strawberry.scalars.JSON,` row to `SCALAR_MAP` (placed between `DurationField` and `UUIDField` per the plan's suggested position) and rewrote the JSON/HStore TODO comment to preserve only the `HStoreField` half pointing at Slice 4. No other lines touched; the `ArrayField` TODO above is unchanged. No new import added — `strawberry.scalars.JSON` is reached via the existing `import strawberry` at line 23.
- `tests/types/test_converters.py` — appended a new section (banner comment + three tests) after the BigInt section. Reuses Slice 1's `_introspect_field_type` / `_walk_introspected_type` helpers verbatim; each test declares its own synthetic model + `DjangoType` + `Query` resolver inside the test body with `managed = False` and `app_label = "test_jsonfield"`.

### Tests added or updated

- `tests/types/test_converters.py::test_json_field_maps_to_json_scalar_in_schema` — pins `JSONField` → `JSON!` introspection shape (`NON_NULL` wrapper around terminal `SCALAR { name: "JSON" }`).
- `tests/types/test_converters.py::test_json_field_nullable_in_schema` — pins `JSONField(null=True)` → bare `SCALAR { name: "JSON", ofType: None }` (no `NON_NULL` wrapper).
- `tests/types/test_converters.py::test_json_field_round_trips_dict_via_schema_execution` — pins wire-level round-trip via `schema.execute_sync("{ owner { data } }")` for a dict carrying string / int / list / `None` values; asserts `result.errors is None` and dict-equality on `result.data`.

### Validation run

- `uv run ruff format .` — pass (99 files left unchanged; standing `COM812`-with-formatter warning is unchanged from prior slices).
- `uv run ruff check --fix .` — pass (All checks passed).
- `uv run pytest tests/types/test_converters.py -k "json_field" -v` — 3 passed, 25 deselected. (Coverage table printed because `pyproject.toml` configures `pytest-cov` to load automatically; no explicit `--cov*` flag was passed. The focused run was only used to confirm pass/fail of the three new tests.)

### Implementation notes

- **JSONField row placement**: chose the plan's suggested position (after `DurationField`, before `UUIDField`) so the "container-shaped" scalar lands away from both the integer cluster and the date-time cluster. Functionally arbitrary; readability is the only constraint.
- **TODO comment wording**: used the plan's suggested replacement verbatim — names `HStoreField`, names the sentinel-guarded dispatch path, and cites `docs/spec-deferred_scalars.md` Slice 4. Keeps the comment grep-discoverable for Slice 4's planner.
- **Test #2 assertion shape**: chose the dict-equality form (`type_payload == {"kind": "SCALAR", "name": "JSON", "ofType": None}`) to mirror Slice 1's `test_big_integer_field_nullable_in_schema` style verbatim. The walk-and-assert alternative was equally valid per the plan.
- **Test #3 dict shape**: used the plan's suggested `{"k1": "v1", "k2": 2, "k3": [1, 2, 3], "k4": None}` — covers strings, ints, lists, and `None` in one assertion. Bound the payload to a local variable and referenced it on both the resolver-return side and the assertion side so the test's data flow reads from one source of truth.
- **No new public export**: `strawberry.scalars.JSON` is accessed via dotted attribute and is not re-exported from `django_strawberry_framework.__all__`. `django_strawberry_framework/__init__.py` and `tests/base/test_init.py` are not in the diff.

### Notes for Worker 3

- No shadow file was generated or read during this pass — the plan's static-helper observations were sufficient; the change is a +1 dict row + a TODO comment rewrite plus three small tests, well under the 30-line threshold for fresh helper-invocation in a single file.
- Diff scope: exactly one row added to `SCALAR_MAP`, one TODO block reworded (3 lines → 3 lines), and one new test section (banner + 3 tests reusing Slice 1's helpers). No other source or test file is touched.
- `app_label = "test_jsonfield"` is reused 3x across the new tests (parallel to Slice 1's `"test_bigint"` 5x repetition). Worker 3's Slice 1 DRY watchpoint on this literal carries forward — if Slices 3 and 4 add similar patterns, the integration pass can decide whether a constants block is warranted.

### Notes for Worker 1 (spec reconciliation)

- No spec gap or drift surfaced. The plan was followed exactly: one `SCALAR_MAP` row, one surgical TODO edit (HStoreField half preserved), and three tests with the plan's named identifiers reusing the Slice 1 helpers.
- Cross-slice carry-forward to Slice 4 planning is unchanged: `strawberry.scalars.JSON` now appears at one site in `converters.py`; Slice 4 will introduce the second site as a sentinel-guarded branch return. The integration pass owns the de-dup-vs-leave-inline decision.
- Cross-slice carry-forward to integration-pass planning is unchanged: the synthetic-model + `DjangoType` + `Query` trio pattern is now used at 7+ sites across Slices 1 and 2 in `tests/types/test_converters.py`. The `_make_one_field_schema(...)` helper extraction watchpoint Worker 3 flagged in Slice 1 stays open for the integration pass.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **No new in-slice DRY violations.** Slice 2's three tests reuse Slice 1's `_introspect_field_type` and `_walk_introspected_type` helpers verbatim (no re-inlined chain walk), reach `strawberry.scalars.JSON` via the existing `import strawberry` (no aliased `from strawberry.scalars import JSON` shadow), and slot a single row into `SCALAR_MAP` rather than introducing a second dispatch path. The `Repeated string literals` section of the post-Slice-2 converters overview is still `None.`, and the test-file overview surfaces no Slice-2-only literal above 3 occurrences.
- **Carry-forward watchpoints for the integration pass** (not Slice-2 findings; recorded so Worker 1 has the running tally before Slices 3 and 4 land):
  - `app_label` literal pattern is now `"test_bigint"` 5x + `"test_jsonfield"` 3x = 8 occurrences across Slices 1-2 in `tests/types/test_converters.py`. Slice 3 (`_FakeArrayField`) and Slice 4 (`_FakeHStoreField`) will each add ~7-10 more occurrences under their own `app_label`s. If the total crosses ~20 instances, the integration pass should evaluate a `_BIGINT_APP_LABEL` / `_JSON_APP_LABEL` / etc. constants block — but per-test inline literals may still read more clearly than a constants block; recording the count for an informed decision.
  - The synthetic-model + `DjangoType` + `Query` resolver pattern now appears at 8 test sites across Slices 1 (5 tests) and 2 (3 tests). Worker 3's Slice 1 review flagged `_make_one_field_schema(model_cls, field_name)` as a deferred helper candidate; the count grew as predicted. Hold the decision for the integration pass — extracting now would force the helper to accept parameters that Slices 3 and 4 may shape differently (sentinel monkey-patch, payload variety, choices on `base_field`).
  - `strawberry.scalars.JSON` now appears at one site in `converters.py:65` (`SCALAR_MAP` row). Slice 4 will introduce a second site (sentinel-guarded branch return for `HStoreField`). The integration pass evaluates whether a module-level `_JSON_SCALAR` alias tightens the file or just adds indirection — two call sites is the minimum threshold where the question is even worth asking, and Slice 4 will own the de-dup decision.

### Public-surface check

- `git diff -- django_strawberry_framework/__init__.py` shows only Slice-1 changes (the `BigInt` import + `__all__` entry); Slice 2 introduces no additional change to that file. The Slice-1 diff was previously `final-accepted`, so the Slice-2 review scope is "no new public-surface change," and that holds.
- `tests/base/test_init.py` is not in Slice 2's diff (the file already carries the Slice-1 `__all__` pin including `"BigInt"`); Slice 2 added no new public symbol. Confirmed against the slice plan's explicit "no `__all__` / no `__init__.py` change" contract (plan section, Implementation discretion items, last bullet).
- Spec authorization: Slice 2's checklist (spec lines 139-145) names exactly `SCALAR_MAP` extension, the TODO trim, and three tests in `tests/types/test_converters.py`. No public-surface addition is authorized or planned for this slice.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **Minimal-surface implementation.** The source diff is precisely +1 `SCALAR_MAP` row (`converters.py:65`) and one TODO-comment rewrite (`converters.py:37-39`) that preserves the `HStoreField` anchor for Slice 4 (`See docs/spec-deferred_scalars.md Slice 4`). The `ArrayField` TODO at `converters.py:33-35` is untouched, the `convert_scalar` body is untouched, no new import was added, and `strawberry.scalars.JSON` is reached via the existing `import strawberry` at `converters.py:23` — exactly the shape the plan specified.
- **Test trio cleanly maps to Decision 3 + Test-plan categories 6-8.** `test_json_field_maps_to_json_scalar_in_schema` pins the `JSON!` introspection shape (category 6 — annotation generation via introspection); `test_json_field_nullable_in_schema` pins the bare `SCALAR { name: "JSON", ofType: None }` shape under `null=True` (category 7 — `null=True` widening); `test_json_field_round_trips_dict_via_schema_execution` pins wire-level dict round-trip with a payload exercising strings, ints, lists, and `None` (category 8 — wire-level `schema.execute_sync` round-trip). All three follow the in-function model declaration + `managed = False` + `app_label = "test_jsonfield"` pattern from Decision 7's spec line 633 / lines 641-646. Helpers reused verbatim from Slice 1 (no re-inlining).
- **Cross-test isolation honored.** Each test declares its own synthetic model (`JsonOwner`, `JsonNullableOwner`, `JsonRoundTripOwner`) with a distinct PascalCase class name so the schema's `__type` lookup resolves cleanly under the shared `app_label`. The autouse `_isolate_registry` fixture from `tests/types/test_converters.py:38-47` covers per-test registry cleanup; new tests inherit automatically (Decision 7's preamble at spec lines 637-639 explicitly names this pattern).
- **Spec gap-finding clean.** Spec-required behaviors for Slice 2: (a) `JSONField → strawberry.scalars.JSON` mapping (Decision 3, spec line 523) — covered by all three tests at the introspection layer. (b) Nullable handling via the `field.null` branch in `convert_scalar` — covered by `test_json_field_nullable_in_schema`. (c) Wire-level identity-serializer behavior — covered by `test_json_field_round_trips_dict_via_schema_execution`. No branch in the diff lacks a corresponding test assertion.

### Temp test verification

No temp tests were created under `docs/builder/temp-tests/slice-2-jsonfield/`. The diff is a single-row `SCALAR_MAP` addition + a TODO-comment trim + three small tests; the spec contract is unambiguous and the tests pin every required behavior. The plan pre-flagged temp-test creation as not anticipated (plan, `### Test additions / updates` section, second bullet); confirmed unnecessary on review.

Focused permanent-test run during review: `uv run pytest tests/types/test_converters.py -k "json_field" -v --no-cov` — 3 passed, 25 deselected. Used only to confirm pass/fail of the three new permanent tests, not for coverage discovery. (Per BUILD.md "Coverage is the maintainer's gate, not a worker's tool," `--no-cov` was added to suppress the auto-loaded coverage plugin; no `--cov*` flag was passed.)

### Notes for Worker 1 (spec reconciliation)

- **No spec edits warranted for Slice 2.** Decision 3 (spec line 523) is one sentence — "Map `models.JSONField` → `strawberry.scalars.JSON`." — and the diff matches verbatim. Decision 8 (spec lines 708-710) on `SCALAR_MAP`'s `Any` value type was already paid down in Slice 1 (final-accepted); Slice 2's row slots in cleanly under that annotation without further widening.
- **Carry-forward for the integration pass / Worker 1 to weigh:**
  - The cross-file repeated literal `strawberry.scalars.JSON` will appear at two sites in `converters.py` after Slice 4 lands (Slice 2's `SCALAR_MAP` row + Slice 4's sentinel-guarded branch return per Decision 5). The integration pass should evaluate whether a module-level `_JSON_SCALAR = strawberry.scalars.JSON` constant tightens the file or whether two call sites for the same upstream symbol is below the de-dup threshold. Recording now so Slice 4's planning pass and the integration pass enter the decision with context.
  - The `app_label` literal count is 8 (5 + 3) after Slice 2; Slices 3 and 4 will likely push it past 20. Worker 1 (integration pass) should reconsider the constants-block question once the final count is known.
  - The synthetic-model + `DjangoType` + `Query` trio test pattern is at 8 sites after Slice 2. The `_make_one_field_schema(...)` helper extraction watchpoint Worker 3 carried over from Slice 1 stays open; defer until Slices 3 and 4 reveal whether the helper signature would need sentinel-monkey-patch / payload-variety / choices-on-base-field parameterization.
- **No plan-vs-implementation drift.** Worker 2's build report names every plan-level discretion item (row placement, TODO wording, test #2 assertion shape, payload contents, section banner wording, model class naming) and the implementations are within the discretion the plan granted.

### Review outcome

`review-accepted`. Every spec-required behavior in Slice 2's checklist (spec lines 139-145) is pinned by a test. No High, Medium, or Low findings to address. DRY watchpoints are deferred to the integration pass with the running counts recorded above. The public-surface, CHANGELOG, and docs/release/KANBAN/archive contracts are all "not modified" as the plan required.

Helper invocations during this review:

- `uv run python scripts/review_inspect.py django_strawberry_framework/types/converters.py --output-dir docs/builder/shadow`
- `uv run python scripts/review_inspect.py tests/types/test_converters.py --output-dir docs/builder/shadow`

Both shadow overviews regenerated against post-Slice-2 source; outputs noted under DRY findings (`Repeated string literals` and `Imports` sections drove the integration-pass watchpoints). Shadow-file line numbers were not cited in review feedback per BUILD.md "Shadow-file line numbers are NOT canonical."

---

## Final verification (Worker 1)

### DRY check across this slice and Slice 1

Read against `docs/builder/bld-slice-1-bigint_scalar.md` (final-accepted) and the current diff for `django_strawberry_framework/types/converters.py` and `tests/types/test_converters.py`.

- **No new in-slice DRY violations introduced by Slice 2.** The single `models.JSONField: strawberry.scalars.JSON,` row slots into the dict that Slice 1 already widened to `dict[type[models.Field], Any]` (`converters.py:41`), with no additional import (reached via the existing `import strawberry` at `converters.py:23`) and no duplicate dispatch path. The three new tests reuse the Slice 1 introspection helpers (`_walk_introspected_type`, `_introspect_field_type`) verbatim and follow the same in-function model + `DjangoType` + `Query` resolver shape, only swapping the synthetic `app_label` from `"test_bigint"` to `"test_jsonfield"` and the model / type identifiers.
- **Cross-slice duplication flagged (deferred to integration pass, per plan).**
  - **`_make_one_field_schema(model_cls, field_name)` trio shape.** The synthetic-model + `DjangoType` + in-function `Query` resolver pattern Worker 3 flagged in Slice 1's DRY findings now appears at 8 sites across `tests/types/test_converters.py` (5 from Slice 1 + 3 from Slice 2). Extracting a helper now would force premature parameterization of resolver return shape (string-serialized BigInt vs. dict-shaped JSON vs. introspection-only vs. boolean error-cases), so I am deferring the decision to the integration pass once Slices 3 and 4 (each with `_FakeArrayField` / `_FakeHStoreField` sentinel-monkey-patch tests of their own) reveal the final parameter surface. Slice-2 finding only — not blocking acceptance.
  - **`strawberry.scalars.JSON` target symbol will appear twice in `converters.py` after Slice 4.** Slice 2 introduces the first call site (`SCALAR_MAP` row at `converters.py:65`); Slice 4 will introduce a second call site as a sentinel-guarded branch return inside `convert_scalar` for `HStoreField` (per Decision 5, spec lines 550-571). Two distinct call sites for the same upstream scalar is the minimum threshold where a module-level `_JSON_SCALAR = strawberry.scalars.JSON` alias is even worth considering — but the two sites have different surrounding context (dict value vs. branch return), so the alias may just add an indirection step rather than tightening the file. Slice 4's planner and the integration pass will own the de-dup-vs-leave-inline decision once both sites exist; recording the watchpoint so Slice 4's plan picks it up cleanly.
  - **`app_label` literal repetition.** Now at 8 occurrences in `tests/types/test_converters.py` (5 × `"test_bigint"` from Slice 1, 3 × `"test_jsonfield"` from Slice 2). Slices 3 and 4 will likely add another ~7-10 each under their own labels, pushing the total past ~20. The integration pass should evaluate whether a module-level constants block (`_BIGINT_APP_LABEL = "test_bigint"`, `_JSON_APP_LABEL = "test_jsonfield"`, etc.) is justified once the final count is known. Not a Slice-2 finding; the per-test inline literal still reads more clearly than a constant at 3 occurrences within Slice 2.

### Existing tests still pass

`uv run pytest tests/test_scalars.py tests/types/test_converters.py tests/base/test_init.py -x --no-cov` — **60 passed, 2 warnings, 0.22s**. All three new Slice-2 tests pass (`test_json_field_maps_to_json_scalar_in_schema`, `test_json_field_nullable_in_schema`, `test_json_field_round_trips_dict_via_schema_execution`); the 10 Slice-1 BigInt schema-execution tests still pass; the 4 `tests/base/test_init.py` tests (including the `__all__` set-equality pin) still pass; and the 28-test `tests/test_scalars.py` BigInt unit suite still passes. The two warnings are the pre-existing `test_choice_enums._owner` re-registration warnings carried forward from Slice 1's final-verification — out of slice scope, noted for the integration pass. No full sweep needed per BUILD.md "Existing tests still pass: `uv run pytest <focused scope>`". `--no-cov` was used to suppress the auto-loaded coverage plugin only; no `--cov*` flag was passed, per BUILD.md "Coverage is the maintainer's gate, not a worker's tool."

### Spec reconciliation

Read Worker 2's `### Notes for Worker 1 (spec reconciliation)` section and Worker 3's `### Notes for Worker 1 (spec reconciliation)` section:

- **Worker 2's notes:** "No spec gap or drift surfaced. The plan was followed exactly: one `SCALAR_MAP` row, one surgical TODO edit (HStoreField half preserved), and three tests with the plan's named identifiers reusing the Slice 1 helpers." Cross-slice carry-forward to Slice 4 / integration pass is unchanged.
- **Worker 3's notes:** "No spec edits warranted for Slice 2. Decision 3 (spec line 523) is one sentence — 'Map `models.JSONField` → `strawberry.scalars.JSON`.' — and the diff matches verbatim." Confirmed no plan-vs-implementation drift; carry-forward items (`_JSON_SCALAR` alias, `app_label` constants, `_make_one_field_schema` helper) are integration-pass material.

**Spec status-line re-verification** (per `docs/builder/worker-1.md` "Spec status-line re-verification (every Worker 1 spawn)"): `docs/spec-deferred_scalars.md` line 4 reads `Status: draft (revision 10, post-feedback2 re-review).` This remains accurate at Slice 2 final-verification time — archival lifecycle is Slice 6's job, not Slice 2's, and the spec is still in draft until Slice 6 archives it. No edit warranted.

**Conclusion:** no spec edit needed for Slice 2.

### Final status

`final-accepted`. The slice delivers the spec's Slice 2 checklist (spec lines 139-145) exactly: one `SCALAR_MAP` row for `models.JSONField → strawberry.scalars.JSON`, the surgical TODO trim that preserves only the `HStoreField` half for Slice 4's anchor, and three schema-execution tests (`test_json_field_maps_to_json_scalar_in_schema`, `test_json_field_nullable_in_schema`, `test_json_field_round_trips_dict_via_schema_execution`). No public-surface change, no `__all__` change, no `convert_scalar` body change, no new imports. Public-surface check, CHANGELOG sanity, and documentation/release sanity are all "not applicable" or "not modified" as the plan required. Focused test run is green. The artifact's top-level `Status:` line is updated to `final-accepted` together with this section.

### Summary

Slice 2 ships the `JSONField → strawberry.scalars.JSON` mapping by adding a single row to `SCALAR_MAP` in `django_strawberry_framework/types/converters.py` (reached via the existing `import strawberry`), rewriting the `JSONField` / `HStoreField` TODO at `converters.py:37-39` to preserve only the `HStoreField` half for Slice 4's anchor, and appending three schema-execution tests to `tests/types/test_converters.py` that pin (1) the non-null `JSON!` introspection shape, (2) the nullable `JSON` (`null=True`) introspection shape, and (3) a wire-level dict round-trip via `schema.execute_sync` covering string / int / list / `None` values. No public-surface change, no new imports, no `convert_scalar` body change. The MRO walk and `T | None` widening at `converters.py:106-119` automatically cover JSONField via the new dict row.

### Spec changes made (Worker 1 only)

None.
