# Build: Slice 3 — `ArrayField` recursion (sentinel-based)

Spec reference: `docs/spec-deferred_scalars.md` (Slice checklist lines 146-167, Decision 2 lines 495-519, Decision 4 lines 525-548, Decision 7 / Schema test fixture pattern lines 594-705, User-facing API lines 712-729, Test plan categories 11-12 + 15-16 + 19 lines 786-805)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - `convert_scalar` body in `django_strawberry_framework/types/converters.py:73-120`. Slice 3 inserts a new sentinel-guarded branch **before** the existing MRO walk (`converters.py:106-109`). The branch must run before the MRO walk because `_FakeArrayField` subclasses `models.Field` — without explicit pre-MRO dispatch, the MRO walk would either miss (no match) or, worse, accidentally match a parent `Field` class if a future `SCALAR_MAP` row covered it. Decision 2 (spec lines 499-515) pins the branch placement; the recursive `convert_scalar(field.base_field, type_name)` call re-enters the same function and naturally inherits choice substitution (`converters.py:116-117`) and `T | None` widening (`converters.py:118-119`) for the inner type. The outer `null` widening then applies to the resulting `list[inner]`.
  - `ConfigurationError` already imported at `converters.py:26` and already used for the unsupported-field message at `converters.py:111-115`. The two new rejection raises (nested `ArrayField`, outer `choices`) reuse the same exception class — **do NOT re-import** and **do NOT introduce a new exception subclass**. The error-message shape mirrors `converters.py:111-115` (names `field.model.__name__` + `field.name`, ends with a consumer-actionable hint).
  - Module-level constant pattern at `converters.py:123-124` (`_NON_IDENT`, `_GRAPHQL_RESERVED_ENUM_VALUES`). The new `_ARRAY_FIELD_CLS` sentinel sits at the same lexical tier as those constants — top-level module assignment, leading-underscore-prefixed, single-source-of-truth for the `convert_scalar` branch's guard. Decision 4 (spec lines 525-548) pins the sentinel shape verbatim.
  - Test-isolation autouse fixture `_isolate_registry` at `tests/types/test_converters.py:37-47` covers per-test registry cleanup for any new `DjangoType` subclasses declared in the new tests; Slice 3's tests inherit automatically (Decision 7 preamble, spec lines 637-639).
  - **Introspection helpers `_walk_introspected_type` / `_introspect_field_type`** at `tests/types/test_converters.py:420-446`. Slice 1's planning carry-forward (worker-memory note dated 2026-05-17) flagged that the 3-level `ofType` nesting these helpers support may need a 4th level for Slice 3's `list[T]` cases. **Re-evaluated against the helper at `tests/types/test_converters.py:434-446`**: the introspection query template (lines 436-439) explicitly nests `ofType { kind name ofType { kind name ofType { kind name } } }` — that is **3 nested `ofType` slots beyond the top-level `type { kind name }`** = **4 wrapping levels total**. Worst-case Slice 3 shape `list[int]` (outer non-null, inner non-null) introspects as `NON_NULL → LIST → NON_NULL → SCALAR { name: "Int" }` = exactly 4 wrapping levels. The `while current.get("ofType") is not None` walk at line 429 terminates at the deepest `SCALAR` (which has no `ofType` payload because the query template ran out of nesting). **The helpers handle Slice 3 unchanged — no extension required.** Reusing them verbatim is the right move; introducing a Slice-3-only deeper helper would fork the file's introspection contract for no benefit. Recording the depth-budget headroom as a watchpoint for any future slice that introduces an `Annotated[list[list[...]], ...]` shape — Slice 3's outer-nested-ArrayField rejection (Decision 2) explicitly bans that case, so the budget is safe within this spec.
  - **In-function model + sentinel-swap pattern** anchored by Decision 7 (spec lines 641-657). Slice 1's BigInt tests at `tests/types/test_converters.py:449-699` and Slice 2's JSON tests at lines 715-804 both use this shape; Slice 3's sentinel-branch tests follow it verbatim with the added `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` step **before the `DjangoType` declaration** (per spec lines 635 and 651).
  - **Synthetic-model `Meta` convention** (`managed = False; app_label = "..."` per Decision 7 / spec line 633). Slice 3 declares `app_label = "test_arrayfield"` for its synthetic models; distinct from `"test_bigint"` (5 sites, Slice 1), `"test_jsonfield"` (3 sites, Slice 2), and `"test_choice_enums"` (the session-scoped fixture). Worker 1's running count after Slice 3 lands becomes 5 + 3 + ~9 = ~17 `app_label` literal occurrences across `tests/types/test_converters.py` — flagged for integration-pass evaluation but not a Slice-3 finding.

- **New helpers justified.**
  - **`_resolve_array_field() -> type[models.Field] | None`** in `django_strawberry_framework/types/converters.py`. Single responsibility: encapsulate the soft-import of `django.contrib.postgres.fields.ArrayField` so the dev environment (no postgres driver) does not raise at module load. The helper's body is a four-line `try / except ImportError / return None / return ArrayField` per Decision 4 (spec lines 527-533). It is called exactly once at module load (`_ARRAY_FIELD_CLS = _resolve_array_field()`) and exists as a separate function rather than an inline `try / except` so the helper-resolver tests (spec lines 155-156: `test_resolve_array_field_returns_class_when_postgres_fields_importable` / `test_resolve_array_field_returns_none_when_postgres_fields_unimportable`) can exercise both branches via `sys.modules` manipulation (Decision 7 example at spec lines 661-676). Without the helper as a named function, the `None`-branch test would not be reachable (the module-load assignment evaluates exactly once).
  - **Module-level sentinel `_ARRAY_FIELD_CLS: type[models.Field] | None`** at module load. Single responsibility: the cached guard value for the `convert_scalar` `isinstance` branch. Reads in `convert_scalar` are O(1); the sentinel value is set once at module import and treated as immutable in production. Tests swap it via `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` (spec line 152, Decision 7 line 635); the patch reverts on teardown, so production code paths see the resolved value.
  - **`_FakeArrayField(models.Field)` test double** in `tests/types/test_converters.py`. Single responsibility: a class the test can pass `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` against so the sentinel branch dispatches without requiring `django.contrib.postgres`. Decision 7 spec lines 603-619 pin the shape verbatim: subclasses `models.Field`, accepts `base_field` in `__init__`, propagates `base_field.set_attributes_from_name(name)` and `base_field.model = cls` in `contribute_to_class` so `convert_scalar`'s recursive call into `field.base_field` finds the metadata it needs (`field.model.__name__`, `field.name`, `field.choices`, `field.null`) when building error messages and enum names.
  - **Cross-slice DRY claim — `_resolve_array_field` + `_resolve_hstore_field` are a near-copy pair.** Per the task brief, the spec's Decision 4 (lines 525-548) shows them as two separate, parallel `try / from django.contrib.postgres.fields import X / except ImportError / return None / return X` helpers — that is the spec's commitment. **Plan deliberately defers consolidation to the integration pass.** Reasons: (a) the function bodies differ in exactly one identifier (`ArrayField` vs `HStoreField`); a `_resolve_postgres_field(name: str)` factory would either pass the name as a string (ugly indirection at the call site and breaks IDE go-to-definition) or use `getattr(module, name)` (pushes the import-attribute lookup into a runtime branch); (b) Slice 4 has not yet been planned — pre-empting its plan to insert a shared helper here would force Slice 4 to inherit a shape Slice 4's planner had no chance to evaluate; (c) the integration pass owns cross-slice DRY consolidation per BUILD.md ("Cross-slice integration pass"). **The integration pass should evaluate** whether to extract a helper after both sites exist, but Slice 3 plans for the spec-pinned two-helper shape. Flagged here explicitly.

- **Duplication risk avoided.**
  - **Risk #1: collapsing the `_ARRAY_FIELD_CLS` and `_HSTORE_FIELD_CLS` sentinels into one tuple at Slice 3 time.** Don't. Slice 3 introduces only `_ARRAY_FIELD_CLS`; Slice 4 introduces `_HSTORE_FIELD_CLS`. The two sentinels are read by **different branches** in `convert_scalar` with **different post-isinstance behavior** (ArrayField recurses through `base_field`; HStoreField returns `JSON` with no recursion — see Decision 5, spec lines 553-571). A combined `_POSTGRES_FIELD_CLASSES = (...)` constant would force every `isinstance(field, ...)` call to dispatch on a tuple and lose the named contract for each branch. The named-sentinel-per-branch shape is the right grain.
  - **Risk #2: inlining the `try / except ImportError` directly at module scope without a named helper.** Module-scope `try: from django.contrib.postgres.fields import ArrayField; except ImportError: ArrayField = None` would work, but the `None`-branch test (spec line 156) can only be exercised via `sys.modules` manipulation **before the module loads**. Wrapping in a named function makes both branches testable via `sys.modules[...] = None` (forces `ImportError`) and `sys.modules[...] = fake_module` (returns the test double) — the helper-resolver tests (Decision 7 lines 661-676) require this shape.
  - **Risk #3: `_FakeArrayField` re-implementing Django's full `ArrayField` semantics.** Don't. `_FakeArrayField` is a test double **only** for the dispatch contract: subclass `models.Field`, hold a `base_field`, propagate metadata so `convert_scalar`'s recursive call works. No serialization, no validation, no `db_type` — Django's system checks do not fire on bare `models.Field` subclasses regardless of `managed` (per Decision 7 L2 fix, spec line 633). Resist the urge to add `db_type` or `from_db_value`; the spec contract is the dispatch surface only.
  - **Risk #4: re-implementing the introspection chain walk inside the new Slice 3 tests.** Reuse `_walk_introspected_type` / `_introspect_field_type` from `tests/types/test_converters.py:420-446` verbatim. Per the depth-budget analysis above, the existing helpers cover `list[T]`'s 4-wrapping-level case. Re-inlining would duplicate the chain literal and obscure that the same helper covers BigInt, JSON, and now `list[T]`. Recording so Worker 2 picks up the existing helpers when writing the introspection assertions.
  - **Risk #5: duplicating Slice 2's `strawberry.scalars.JSON` import handling.** Not applicable to Slice 3 (Slice 3's target inner types are arbitrary scalars from `SCALAR_MAP`, not `strawberry.scalars.JSON`). Recording the non-issue so the integration pass doesn't conflate Slice 3 with Slice 4's `JSON` site.
  - **Risk #6: the synthetic-model + `DjangoType` + `Query` trio test pattern.** This pattern now appears at 8 sites across Slices 1 (5 tests) and 2 (3 tests); Slice 3 adds another ~6-8 sentinel-branch tests of the same shape (plus 2 helper-resolver tests that **don't** declare a `DjangoType` — they only exercise `_resolve_array_field`). The total after Slice 3 reaches ~14-16 sites of the trio shape. Worker 3's Slice 1 review flagged `_make_one_field_schema(model_cls, field_name)` as a deferred helper candidate; the count is approaching the threshold where extraction is worthwhile, but Slice 4's sentinel-monkey-patch / outer-`choices` rejection / `base_field`-unsupported-type tests will add their own parameter-surface considerations. **Continuing to defer the helper extraction to the integration pass** per Slice 2's carry-forward — Slice 3 must not extract it unilaterally because Slice 4 hasn't been planned yet and the helper signature would have to anticipate Slice 4's needs.

- **Static helper observations** (from `docs/builder/shadow/django_strawberry_framework__types__converters.overview.md`, regenerated against post-Slice-2 source on 2026-05-17):
  - `convert_scalar` is currently 48 lines / 5 branches (control-flow hotspots section). Slice 3 inserts a new sentinel-guarded branch with nested rejection logic (`nested ArrayField` + outer `choices`) plus the recursive `convert_scalar(field.base_field, type_name)` call plus the outer null-widening. Expected post-Slice-3 shape: **~62-65 lines / 7-8 branches** — still well within typical-function bounds but pushes `convert_scalar` deeper into hotspot territory. Worker 3 should expect this shift and not flag it as a Medium finding unless the actual line count exceeds 80 or the branch count exceeds 10.
  - Two TODO comments remain at lines 33 (ArrayField, Slice 3 target) and line 37 (HStoreField, Slice 4 target). Slice 3 removes **only** the line-33 ArrayField TODO (lines 33-35, the 3-line block). The line-37 HStoreField TODO stays anchored for Slice 4. Worker 2 must NOT touch the line-37 TODO.
  - `Repeated string literals` section is still `None.` post-Slice-2 — confirming no pre-existing cross-file literal pressure. Slice 3's new error-message string literals (`"Nested ArrayField on ..."`, `"... declares choices on the outer field..."`) are spec-pinned in Decision 2 (spec lines 502-511); each appears once in `converters.py` and once as a test assertion `match=` substring, so no DRY pressure beyond two sites.
  - `Calls of interest` post-Slice-3 will gain at least one new `isinstance()` call (the sentinel-guard `isinstance(field, _ARRAY_FIELD_CLS)` and the nested-array check `isinstance(field.base_field, _ARRAY_FIELD_CLS)`); these are the typical-shape-contract-bug sites BUILD.md warns about. Worker 3 should verify both `isinstance` calls dispatch on the **module-level sentinel**, not a hardcoded reference to `_FakeArrayField` (which would break the production path).

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written.

1. **Add `_resolve_array_field()` helper to `django_strawberry_framework/types/converters.py`**. Place it **immediately after the `SCALAR_MAP` definition** (current `converters.py:70`) and **before** `convert_scalar` (current `converters.py:73`), so it sits at the module-helper tier near the consts. Verbatim shape per Decision 4 (spec lines 527-533):
   ```python
   def _resolve_array_field() -> type[models.Field] | None:
       try:
           from django.contrib.postgres.fields import ArrayField
       except ImportError:
           return None
       return ArrayField
   ```
   Implementer's discretion on docstring wording; one short sentence anchoring the helper's responsibility ("Soft-import postgres `ArrayField`; returns ``None`` if `django.contrib.postgres.fields` is unavailable.") is sufficient.

2. **Add the module-level sentinel `_ARRAY_FIELD_CLS`** immediately after the helper, before `convert_scalar`:
   ```python
   _ARRAY_FIELD_CLS: type[models.Field] | None = _resolve_array_field()
   ```
   Annotation is `type[models.Field] | None` per Decision 4 (spec line 544). The leading underscore marks the sentinel as module-private so a future `from .converters import *` (none exists today) would not leak it. The post-isinstance `field` argument in the branch retains its `models.Field` type narrowing for downstream calls.

3. **Add the `ArrayField` sentinel branch to `convert_scalar`** (current `converters.py:73-120`). Place the new branch **immediately inside `convert_scalar`'s body, before the MRO walk at the current `converters.py:106-109`**. The branch must run before the MRO walk so a `_FakeArrayField(models.Field)` test double does not accidentally match a parent `Field` row in `SCALAR_MAP` (none exists today, but the spec contract pins the ordering — Decision 2 line 500 says "before the SCALAR_MAP walk"). Verbatim shape per Decision 2 (spec lines 500-515):
   ```python
   if _ARRAY_FIELD_CLS is not None and isinstance(field, _ARRAY_FIELD_CLS):
       if isinstance(field.base_field, _ARRAY_FIELD_CLS):
           raise ConfigurationError(
               f"Nested ArrayField on {field.model.__name__}.{field.name} is not supported.",
           )
       if field.choices:
           raise ConfigurationError(
               f"ArrayField on {field.model.__name__}.{field.name} declares choices on the outer "
               f"field; outer-array choices are ambiguous at the GraphQL boundary. Declare choices "
               f"on base_field for element-level enum, or use FilterSet.",
           )
       inner = convert_scalar(field.base_field, type_name)
       result = list[inner]
       return result | None if field.null else result
   ```
   Key contract points (Decision 2):
   - The outer guard `_ARRAY_FIELD_CLS is not None and isinstance(field, _ARRAY_FIELD_CLS)` is the single-line short-circuit per spec line 501. No redundant inner `_ARRAY_FIELD_CLS is not None` check (spec revision 6 explicitly removed it).
   - **Nested rejection comes before outer-choices rejection** so a `_FakeArrayField(_FakeArrayField(IntegerField()))` configuration surfaces the nested error message, not the outer-choices one. Spec Decision 2 lines 502-505 pin this order.
   - **Outer `choices` rejection's error message must name `base_field` and `FilterSet` as the consumer recourse** per spec lines 507-510. The exact wording is spec-pinned; do not paraphrase the recourse hint.
   - The recursive call uses `convert_scalar(field.base_field, type_name)` — passes the same `type_name` so a nested choice on `base_field` builds `<TypeName><FieldName>Enum` correctly. (Per Decision 2 spec line 516-517, the recursive call re-enters the existing `if field.choices` branch on the inner type and produces `list[<TypeName><FieldName>Enum]` automatically.)
   - **`list[inner]` is a runtime expression** (subscripting `list` with the resolved inner type). Python 3.9+ supports `list[T]` as a generic alias. The package's `pyproject.toml` already pins `>=3.10` (verified via Slice 1's review), so the syntax is safe.
   - The outer-`null` widening `return result | None if field.null else result` uses Python 3.10+ `|`-style union (Decision 7 / Risks line 824 confirms compatibility). This **does not** call `convert_scalar`'s existing tail `if field.null: py_type = py_type | None` branch (the function returns early); the branch must handle outer-null widening itself for the `list[T]` shape.
   - **DRY claim about the outer-null widening duplicating the tail `if field.null` branch.** This duplication is intentional: the early-return branch must compute `result = list[inner]` from the recursive inner type **and then** widen — there's no clean way to fall through to the tail without re-running the MRO walk on `field` (which would mis-match `_FakeArrayField` against `_ARRAY_FIELD_CLS`'s MRO descendants or fail to find a match). Two lines duplicated; not a DRY violation worth a helper. Worker 3 should not flag this.

4. **Remove the `ArrayField` TODO comment** at `converters.py:33-35` (the 3-line block per the shadow overview line 69, comments lines 73-75). Do NOT remove lines 37-39 (the `HStoreField` TODO) — that is Slice 4. Worker 1's final verification will reject if the HStoreField TODO is accidentally touched.

5. **No new imports** in `converters.py`. `ConfigurationError` is already imported (`converters.py:26`), `models` is already imported (`converters.py:24`), and the `Any` type is already imported (`converters.py:21`) for the `_ARRAY_FIELD_CLS` annotation's `models.Field` reference. The new sentinel branch references `_ARRAY_FIELD_CLS` (module-local) and `field.base_field` / `field.model` / `field.name` / `field.choices` / `field.null` (attributes Django provides on a real `ArrayField` and `_FakeArrayField` propagates via `contribute_to_class`).

6. **Verify (in Worker 2's diff and Worker 3's review) that no other line in `converters.py` is touched.** Slice 3 contract:
   - +1 helper function (`_resolve_array_field`)
   - +1 module-level sentinel assignment (`_ARRAY_FIELD_CLS`)
   - +1 new branch inside `convert_scalar`'s body (the ArrayField sentinel branch)
   - −1 TODO comment block (the ArrayField TODO at lines 33-35)
   - No changes to `SCALAR_MAP`, `convert_choices_to_enum`, `_sanitize_member_name`, `resolved_relation_annotation`, or `convert_relation`.

7. **Add the `_FakeArrayField` test double to `tests/types/test_converters.py`**. Place it at module scope (so all tests can reference it without per-test redeclaration) near the top of the file's test-helper region — implementer's discretion on exact line; suggested placement: immediately after the `_introspect_field_type` helper at the current `tests/types/test_converters.py:434-446` so the test doubles sit alongside the test helpers. Verbatim per Decision 7 (spec lines 603-619):
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
   ```
   Implementer's discretion on the trailing-comma style for the `**kwargs` argument; the rest of the body is spec-pinned. The class name `_FakeArrayField` (leading-underscore-prefixed) matches Decision 7's verbatim example.

8. **Add an import for the `converters` module** at the top of `tests/types/test_converters.py` so tests can call `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)`. Suggested placement: alongside the existing `from django_strawberry_framework.types.converters import (...)` at `tests/types/test_converters.py:30-34`. Add `from django_strawberry_framework.types import converters` on a new line (preserving the existing `_sanitize_member_name`, `convert_choices_to_enum`, `convert_scalar` import) so both the module reference and the symbol references coexist. Implementer's discretion on whether to import the module or use `import django_strawberry_framework.types.converters as converters` — equivalent at runtime; the former is the more common idiom in the existing test file.

9. **Add a section banner comment** marking the start of the Slice-3 test region. Place it after the existing JSONField section (which ends at `tests/types/test_converters.py:804`) and before the new tests. Suggested wording (parallel to the BigInt section at lines 408-417 and the JSONField section at lines 702-712):
   ```python
   # ---------------------------------------------------------------------------
   # ArrayField -> list[T] sentinel-guarded recursion (Slice 3)
   #
   # Synthetic models live under ``app_label = "test_arrayfield"`` so they do
   # not collide with the prior synthetic apps (``test_bigint``, ``test_jsonfield``,
   # ``test_choice_enums``). Sentinel-branch tests monkey-patch
   # ``converters._ARRAY_FIELD_CLS = _FakeArrayField`` BEFORE declaring the
   # ``DjangoType`` (Decision 7 spec line 635). Helper-resolver tests use
   # ``sys.modules`` manipulation per Decision 7 spec lines 661-676.
   # ---------------------------------------------------------------------------
   ```

10. **Write the 9 Slice-3 tests in `tests/types/test_converters.py`** per the spec checklist (spec lines 154-167). Order suggestion: helper-resolver tests first (no `DjangoType` declaration; easiest to read), then sentinel-branch tests in the order the spec lists them. Each sentinel-branch test follows the in-function pattern (spec lines 648-657):

    **Helper-resolver coverage** (spec lines 155-156):
    - `test_resolve_array_field_returns_class_when_postgres_fields_importable(monkeypatch)` — use the spec's example shape at lines 662-668 verbatim:
      ```python
      import sys
      import types as _types
      fake = _types.ModuleType("django.contrib.postgres.fields")
      fake.ArrayField = _FakeArrayField
      monkeypatch.setitem(sys.modules, "django.contrib.postgres.fields", fake)
      from django_strawberry_framework.types.converters import _resolve_array_field
      assert _resolve_array_field() is _FakeArrayField
      ```
      The local re-import is intentional — the test must call the helper after the `sys.modules` patch is in place. The import is cheap (already cached for the module path; only the inner `from django.contrib.postgres.fields import ArrayField` re-runs against the patched `sys.modules`).
    - `test_resolve_array_field_returns_none_when_postgres_fields_unimportable(monkeypatch)` — use the spec's example shape at lines 672-676 verbatim:
      ```python
      import sys
      monkeypatch.setitem(sys.modules, "django.contrib.postgres.fields", None)
      from django_strawberry_framework.types.converters import _resolve_array_field
      assert _resolve_array_field() is None
      ```
      `sys.modules[name] = None` forces the next `import name` to raise `ImportError` (documented Python behavior per spec Risks line 825).

    **Sentinel-branch coverage** (spec lines 158-166):
    - `test_array_field_of_int_maps_to_list_int_via_fake_sentinel(monkeypatch)` — declare `ArrayIntOwner(models.Model)` with `arr = _FakeArrayField(models.IntegerField())`; monkey-patch `converters._ARRAY_FIELD_CLS = _FakeArrayField`; declare `DjangoType`; `finalize_django_types()`; build schema; introspect `arr` field; walk `kind/ofType` chain; assert terminal `SCALAR { name: "Int" }` and the outer wrapping is `NON_NULL → LIST → NON_NULL` (4 wrapping levels — exactly what `_walk_introspected_type` walks). The test pins both the `list[T]` shape generation and the `inner=int` substitution through the recursive `convert_scalar` call.
    - `test_array_field_of_char_maps_to_list_str_via_fake_sentinel(monkeypatch)` — same scaffold with `_FakeArrayField(models.CharField(max_length=20))`; assert terminal `SCALAR { name: "String" }` (Strawberry's name for `str`).
    - `test_array_field_nullable_inner_via_fake_sentinel(monkeypatch)` — `_FakeArrayField(models.IntegerField(null=True))`; assert introspection chain is `NON_NULL → LIST → SCALAR { name: "Int" }` (3 wrapping levels — inner null=True drops the inner `NON_NULL`). Pins that the recursive `convert_scalar` call applies inner-null widening before the outer `list[T]` wrap.
    - `test_array_field_outer_nullable_via_fake_sentinel(monkeypatch)` — `_FakeArrayField(models.IntegerField(), null=True)`; assert introspection chain is `LIST → NON_NULL → SCALAR { name: "Int" }` (3 wrapping levels — outer null=True drops the outer `NON_NULL`). Pins that the outer `field.null` branch widens correctly.
    - `test_array_field_multidim_rejected_via_fake_sentinel(monkeypatch)` — `_FakeArrayField(_FakeArrayField(models.IntegerField()))`; assert `pytest.raises(ConfigurationError, match="Nested ArrayField on ...")` during `DjangoType` declaration (the nested rejection fires inside `convert_scalar` at type-creation time). Pins Decision 2's nested-array rejection.
    - `test_array_field_choices_inner_via_fake_sentinel(monkeypatch)` — `_FakeArrayField(models.CharField(max_length=5, choices=[("A", "A"), ("B", "B")]))`; declare `DjangoType`; finalize; introspect; assert the inner type is an enum scalar (terminal `kind: "ENUM"`, `name: <something>Enum`). Pins Decision 2's "choice handling on `base_field` is inherited automatically" claim (spec lines 516-517). The exact enum name depends on the `DjangoType`'s class name and the field name per `convert_choices_to_enum`'s `f"{type_name}{pascal_case(field.name)}Enum"`; the test asserts on the enum being generated, not the exact name, unless the implementer wants to also pin the name.
    - `test_array_field_outer_choices_rejected_via_fake_sentinel(monkeypatch)` — `_FakeArrayField(models.IntegerField(), choices=[(1, "one"), (2, "two")])`; assert `pytest.raises(ConfigurationError, match="declares choices on the outer")` during `DjangoType` declaration. Pins Decision 2's outer-`choices` rejection.
    - `test_array_field_base_field_unsupported_type_raises(monkeypatch)` — `_FakeArrayField(<unsupported field type>)`; assert `pytest.raises(ConfigurationError, match="Unsupported Django field type")` during `DjangoType` declaration. Pins that the recursive `convert_scalar` call surfaces the existing unsupported-field error for the inner base_field. Implementer's discretion on which unsupported field type to use — Slice 1 has a precedent at `tests/types/test_converters.py:397-405` with a bare `models.Field` subclass; reuse that idiom (declare a tiny `class _Weird(models.Field): pass` inside the test). The `match=` assertion confirms the inner error message — important because the same `ConfigurationError` class wraps three distinct messages in this slice.
    - `test_array_field_sentinel_none_path(monkeypatch)` — monkey-patch `converters._ARRAY_FIELD_CLS = None`; declare a `DjangoType` with a synthetic field type that **would** be caught by the sentinel branch if it were active — but with `_ARRAY_FIELD_CLS = None`, the guard short-circuits (`None is not None` → False) and the field falls through to the MRO walk. The fall-through hits the unsupported-field error (because `_FakeArrayField` is not in `SCALAR_MAP`). Assert `pytest.raises(ConfigurationError, match="Unsupported Django field type")`. Pins that the **short-circuit guard works** — without this test, a future refactor that flipped the guard's `not None` check could break silently. **Recipe note**: even with the patched-to-`None` sentinel, the `_FakeArrayField(...)` instance still needs a valid `base_field` so `__init__` doesn't crash; pass a minimal `models.IntegerField()` even though the recursive call never fires.

    **Optional gated test** (spec line 167):
    - `test_real_array_field_compatible_with_strawberry` — use `pytest.importorskip("django.contrib.postgres.fields")` at the top of the test; declare a `DjangoType` with `ArrayField(IntegerField())` on a `managed = False` model; call `finalize_django_types()`; introspect the schema via `__type`; walk the introspection `kind / ofType` chain explicitly per spec lines 165-167; assert the chain is `NON_NULL → LIST → NON_NULL → SCALAR { name: "Int" }`. **No sentinel monkey-patch** — this test exercises the live `_ARRAY_FIELD_CLS` value (which is the real `ArrayField` class on a postgres-equipped env, or `None` on a dev env where `importorskip` skips the test). The test confirms the sentinel-branch code path works end-to-end against Django's real `ArrayField` when postgres-contrib is available; it is the regression catcher for any refactor of the sentinel branch that accidentally diverges from real `ArrayField` semantics.

11. **Verify (in Worker 2's diff and Worker 3's review) that no source-tree file outside `django_strawberry_framework/types/converters.py` and `tests/types/test_converters.py` is touched.** Specifically, **do not** modify:
    - `django_strawberry_framework/__init__.py` (no new public symbol in Slice 3)
    - `tests/base/test_init.py` (no `__all__` change)
    - `django_strawberry_framework/scalars.py` (Slice 1 territory)
    - `examples/fakeshop/...` (no example-app integration in Slice 3; the spec defers fakeshop integration to Slice 6's `TODAY.md` text edits, not a code change)
    - `CHANGELOG.md` (Slice 6 territory)
    - `docs/FEATURES.md` (Slice 6 territory)
    - The HStoreField TODO at `converters.py:37-39` (Slice 4 anchor)

### Test additions / updates

All 9 tests (+1 optional gated) are spec-required; no temp/scratch tests anticipated. Summary by file:

- **`tests/types/test_converters.py` (extended)**: 9 mandatory tests + 1 optional `pytest.importorskip`-gated test appended after the existing JSONField section (currently ending at line 804). Categories:
  - **Helper-resolver coverage** (2 tests): `sys.modules`-patch shape per Decision 7 example. Assertion shapes: `_resolve_array_field() is _FakeArrayField` (positive) / `_resolve_array_field() is None` (negative). No `DjangoType` declaration; no schema build.
  - **Sentinel-branch coverage** (7 tests): in-function model + `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` + `DjangoType` + `finalize_django_types()` + schema build + introspection assertion (or `pytest.raises` for the rejection tests). Assertion shapes:
    - **Shape introspection tests** (4 tests: `_of_int`, `_of_char`, `_nullable_inner`, `_outer_nullable`): reuse `_introspect_field_type` / `_walk_introspected_type`; assert on the wrapping-level shape (`NON_NULL → LIST → NON_NULL → SCALAR` for the non-null case, three-level variants for the null cases) and the terminal `kind` + `name`.
    - **Rejection tests** (2 tests: `_multidim_rejected`, `_outer_choices_rejected`): `pytest.raises(ConfigurationError, match="...")` during `DjangoType` declaration. Use the exact spec-pinned message-substring shape (`"Nested ArrayField on"` / `"declares choices on the outer"`).
    - **`_choices_inner` test**: assert the inner type is an enum (`terminal["kind"] == "ENUM"`) — pins Decision 2 lines 516-517's "inherits automatically" claim.
    - **`_base_field_unsupported_type_raises`**: `pytest.raises(ConfigurationError, match="Unsupported Django field type")` — pins that the inner recursion surfaces the existing unsupported-field error.
    - **`_sentinel_none_path`**: monkey-patch `_ARRAY_FIELD_CLS = None`; `pytest.raises(ConfigurationError, match="Unsupported Django field type")` — pins the short-circuit guard.
  - **Optional gated test** (1 test): `pytest.importorskip("django.contrib.postgres.fields")` at the top; the dev env skips this test (no postgres driver); CI with postgres-contrib available runs it. Pins the live-`ArrayField` compatibility contract.

- **No changes to `tests/test_scalars.py`** — that file is `BigInt`-specific; `ArrayField` has no scalar wire-format concern (it's an annotation transformer, not a scalar definition).

- **No changes to `tests/base/test_init.py`** — Slice 3 adds no public symbol. The `__all__` set stays exactly the same as after Slice 1.

- **No temp/scratch tests anticipated.** The 9 spec-named tests are permanent. Worker 3 may probe with temp tests under `docs/builder/temp-tests/slice-3-arrayfield/` if the sentinel-branch dispatch surfaces an unexpected behavior (e.g., a Strawberry version that handles `list[T] | None` differently), but no temp tests are pre-flagged here.

### Implementation discretion items

- **`_resolve_array_field` docstring wording**: one short sentence anchoring the helper's responsibility. The spec doesn't pin exact wording.

- **`_ARRAY_FIELD_CLS` placement relative to `convert_scalar`**: the helper + sentinel sit between `SCALAR_MAP` (line 41-70) and `convert_scalar` (line 73). Implementer's discretion on whether to add a blank-line separator beyond what Python conventions / ruff format dictates.

- **`_FakeArrayField` placement in `tests/types/test_converters.py`**: suggested next to the introspection helpers at lines 420-446 (the file's test-helper region). Worker 2 may place it elsewhere if the read order is clearer (e.g., immediately before the Slice-3 section banner). The constraint is that all Slice-3 tests can reference it without re-declaration.

- **`converters` module import in the test file**: `from django_strawberry_framework.types import converters` is the suggested form; `import django_strawberry_framework.types.converters as converters` is equivalent. Worker 2 picks the form that reads more naturally with the existing import block.

- **Synthetic-model class naming**: distinct PascalCase names per test (parallel to Slice 1's per-test-distinct naming pattern documented in Slice 1's "Implementation notes"). Suggested names: `ArrayIntOwner` / `ArrayCharOwner` / `ArrayNullableInnerOwner` / `ArrayOuterNullableOwner` / `ArrayMultidimOwner` / `ArrayChoicesInnerOwner` / `ArrayOuterChoicesOwner` / `ArrayUnsupportedBaseOwner` / `ArraySentinelNoneOwner`. Worker 2 may pick a different scheme — the constraint is that under the shared `app_label = "test_arrayfield"`, the synthetic models do not clash with each other or with prior slices' synthetic models (each `_isolate_registry` teardown clears the package registry but Django's app registry keeps model classes — Slice 1's "Implementation notes" pins this; per-test distinct class names solve it).

- **`app_label` choice**: `"test_arrayfield"` is suggested as the natural parallel to Slice 1's `"test_bigint"` and Slice 2's `"test_jsonfield"`. Worker 2 may pick a more specific value (e.g., `"test_scalars_arrayfield"`) if it improves grep-discoverability. The constraint is that it must not collide with prior `app_label` literals.

- **`test_array_field_choices_inner_via_fake_sentinel` assertion shape**: whether to also pin the exact enum name (`"<TypeName><FieldName>Enum"`) or only assert `terminal["kind"] == "ENUM"`. The spec checklist names only that the test exists (spec line 162); pinning the enum kind is the minimum spec contract. Worker 2 may add the exact-name assertion if it improves the test's diagnostic value.

- **`test_array_field_base_field_unsupported_type_raises` choice of unsupported field type**: declare a tiny `class _Weird(models.Field): pass` inside the test (idiom precedent at `tests/types/test_converters.py:397-405`). Worker 2 may pick a different shape (e.g., a class declared at module scope) if the read order is clearer.

- **`test_array_field_sentinel_none_path` shape**: the test must monkey-patch `_ARRAY_FIELD_CLS = None`, then trigger `convert_scalar` on something that **would** have matched the sentinel if it were active. The synthetic shape is implementer's discretion; suggested: declare a `_FakeArrayField(models.IntegerField())` instance and pass it through the `DjangoType` declaration. With `_ARRAY_FIELD_CLS = None`, the `isinstance(field, _ARRAY_FIELD_CLS)` call would TypeError; the short-circuit `_ARRAY_FIELD_CLS is not None and ...` prevents that. The test asserts the short-circuit works by asserting the MRO walk's unsupported-field error fires instead.

- **Optional `test_real_array_field_compatible_with_strawberry` inclusion**: the spec checklist says "Optional gated test" (spec line 167). Worker 2 SHOULD include it because the spec defines a test name and shape; "optional" refers to "may be skipped in the dev env" (via `pytest.importorskip`), not "may be omitted from the test file". Implementer's discretion only on the inner field type (suggested: `IntegerField()`).

- **Trailing-comma style on `**kwargs` in `_FakeArrayField.__init__` and `contribute_to_class`**: the spec lines 612-619 use no trailing comma on `**kwargs`. Ruff's COM812 rule may have an opinion. Implementer's discretion; verify with `uv run ruff format` after writing.

Items NOT delegated (architectural; resolvable from spec or escalated if not):

- The `_resolve_array_field` body shape (`try / except ImportError / return None / return ArrayField`) — pinned by Decision 4 spec lines 527-533, no discretion.
- The `_ARRAY_FIELD_CLS = _resolve_array_field()` assignment shape — pinned by Decision 4 spec line 544, no discretion.
- The `convert_scalar` ArrayField-branch body — pinned by Decision 2 spec lines 500-515, no discretion. (Worker 2 may inline-format differently per ruff, but the logical shape is fixed: outer guard, nested check, choices check, recursive call, list-wrap, null-widen.)
- The branch placement (before MRO walk in `convert_scalar`) — pinned by Decision 2 spec line 500, no discretion.
- The error-message wording for nested-ArrayField and outer-choices rejection — pinned by Decision 2 spec lines 503-510, no discretion. (The spec's exact phrasing is the consumer-visible contract; Worker 2 must not paraphrase.)
- The `_FakeArrayField` test-double shape (subclass `models.Field`, `__init__` accepting `base_field`, `contribute_to_class` propagating metadata) — pinned by Decision 7 spec lines 603-619, no discretion.
- The `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` shape — pinned by Decision 7 spec line 635 and slice checklist line 152, no discretion.
- The `sys.modules` manipulation pattern for the helper-resolver tests — pinned by Decision 7 spec lines 661-676, no discretion.
- The 9 test names and the 1 optional gated test name — pinned by the spec checklist lines 154-167, no discretion.
- Keeping the HStoreField TODO at `converters.py:37-39` untouched — pinned by Slice 4's contract.

### Notes for Worker 1 (final-verification self-handoff)

- **Re-verify during final verification** that:
  - `_resolve_array_field` exists exactly once in `converters.py` (no parallel `_resolve_hstore_field` introduced — that is Slice 4).
  - `_ARRAY_FIELD_CLS` is the only new module-level constant in `converters.py` (no parallel `_HSTORE_FIELD_CLS`).
  - The `convert_scalar` body has exactly one new branch (the `_ARRAY_FIELD_CLS`-guarded one); the `_HSTORE_FIELD_CLS` branch is NOT pre-emptively added.
  - The HStoreField TODO at `converters.py:37-39` is untouched. If Worker 2's diff removes it, that is plan-vs-implementation drift and must be rejected.
  - `django_strawberry_framework/__init__.py` and `tests/base/test_init.py` are **not** in the diff (no public-surface change).
  - The `_FakeArrayField` test double is **not** a parallel `_FakeHStoreField` — that is Slice 4.

- **Spec status line re-verification**: `docs/spec-deferred_scalars.md` line 4 reads `Status: draft (revision 10, post-feedback2 re-review).` Still accurate at Slice 3 planning time; archival lifecycle is Slice 6's job.

- **Cross-slice carry-forward to Slice 4 planning**:
  - The sentinel-resolver pair (`_resolve_array_field` from Slice 3 + `_resolve_hstore_field` from Slice 4) is a deliberate near-copy pair per spec Decision 4. **The integration pass should evaluate consolidation; Slice 4 should NOT consolidate at slice time.** Slice 4's planning will see Slice 3's shape already in place and may be tempted to extract a helper factory `_resolve_postgres_field(name: str) -> type[models.Field] | None`; resist that temptation in Slice 4 and let the integration pass own it.
  - The `convert_scalar` branch pattern (`isinstance` guard + post-isinstance behavior) is similarly a near-copy between Slice 3 (recurses through `base_field`) and Slice 4 (returns `JSON` directly with no recursion). The post-isinstance bodies are structurally different; **the integration pass should NOT extract a shared helper for the branches themselves** — they share posture, not logic. Slice 4 plans for the spec-pinned distinct-branch shape.
  - The `_FakeArrayField` / `_FakeHStoreField` test-double idiom is shared (Decision 7); Slice 4 introduces `_FakeHStoreField` at the same module scope position. No DRY consolidation between them — they have different `__init__` signatures and `contribute_to_class` bodies (HStoreField has no `base_field` to propagate).

- **Cross-slice carry-forward to integration-pass planning**:
  - The synthetic-model + `DjangoType` + `Query` trio test pattern will reach ~14-16 sites after Slice 3 (8 from Slices 1-2 + ~6-8 from Slice 3's sentinel-branch tests). Slice 4 will push it past 20. The `_make_one_field_schema(...)` helper extraction watchpoint Worker 3 carried forward from Slice 1 stays open; defer to the integration pass.
  - The `app_label` literal count reaches ~17 after Slice 3 (5 `"test_bigint"` + 3 `"test_jsonfield"` + ~9 `"test_arrayfield"`). The integration-pass constants-block decision is still pending.
  - The two pre-existing `test_choice_enums._owner` re-registration warnings (carried from Slice 1) remain out of scope. The integration pass should consider a cleanup if a warnings-clean summary matters.
  - **Static-helper observation**: post-Slice-3 `convert_scalar` will likely grow to ~62-65 lines / 7-8 branches (from the current 48 / 5). Worker 3 should expect this shift and not flag it as Medium unless line count exceeds 80 or branch count exceeds 10.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/converters.py` — added `_resolve_array_field()` soft-import helper and the module-level `_ARRAY_FIELD_CLS` sentinel between `SCALAR_MAP` and `convert_scalar`; inserted the spec-pinned ArrayField sentinel branch (outer guard, nested rejection, outer-`choices` rejection, recursive call into `base_field`, `list[inner]` construction, outer-null widening) at the head of `convert_scalar`'s body — runs before the MRO walk per Decision 2 line 500. Dropped the line-33 ArrayField TODO comment block; preserved the HStoreField TODO at the lines now numbered 33-35 for Slice 4.
- `tests/types/test_converters.py` — added `from django_strawberry_framework.types import converters` import; added the `_FakeArrayField(models.Field)` test double immediately after `_introspect_field_type`; appended the Slice-3 section banner and 11 new tests (2 helper-resolver, 8 sentinel-branch / rejection, 1 optional gated test).

### Tests added or updated

- `tests/types/test_converters.py::test_resolve_array_field_returns_class_when_postgres_fields_importable` — pins the positive helper branch via `sys.modules` patch.
- `tests/types/test_converters.py::test_resolve_array_field_returns_none_when_postgres_fields_unimportable` — pins the `ImportError` helper branch via `sys.modules[name] = None`.
- `tests/types/test_converters.py::test_array_field_of_int_maps_to_list_int_via_fake_sentinel` — pins `ArrayField(IntegerField())` -> `list[int]` (NON_NULL -> LIST -> NON_NULL -> Int).
- `tests/types/test_converters.py::test_array_field_of_char_maps_to_list_str_via_fake_sentinel` — pins `ArrayField(CharField(...))` -> `list[str]` (terminal SCALAR name "String").
- `tests/types/test_converters.py::test_array_field_nullable_inner_via_fake_sentinel` — pins `null=True` on `base_field` drops the inner NON_NULL.
- `tests/types/test_converters.py::test_array_field_outer_nullable_via_fake_sentinel` — pins outer `null=True` drops the outer NON_NULL.
- `tests/types/test_converters.py::test_array_field_multidim_rejected_via_fake_sentinel` — pins Decision 2's nested-ArrayField `ConfigurationError`.
- `tests/types/test_converters.py::test_array_field_choices_inner_via_fake_sentinel` — pins inner-`choices` -> `list[<TypeName><FieldName>Enum]` via recursive call.
- `tests/types/test_converters.py::test_array_field_outer_choices_rejected_via_fake_sentinel` — pins Decision 2's outer-`choices` `ConfigurationError`.
- `tests/types/test_converters.py::test_array_field_base_field_unsupported_type_raises` — pins that unsupported `base_field` surfaces the existing `Unsupported Django field type` error.
- `tests/types/test_converters.py::test_array_field_sentinel_none_path` — pins the short-circuit `_ARRAY_FIELD_CLS is not None` guard via a `None`-patched sentinel.
- `tests/types/test_converters.py::test_real_array_field_compatible_with_strawberry` — gated by `pytest.importorskip("django.contrib.postgres.fields")`; runs end-to-end with the real `ArrayField` class when postgres-contrib is available.

### Validation run

- `uv run ruff format .` — pass (no files reformatted; warning about COM812 conflict is the standing pre-existing warning).
- `uv run ruff check --fix .` — pass (all checks passed).
- No focused `pytest` runs performed; artifact did not require them, and per `START.md` the worker stops at formatting/lint.

### Implementation notes

- Verbatim shape from spec Decision 2 lines 500-515. Ruff format added trailing commas inside each `ConfigurationError(...)` call (consistent with the existing `Unsupported Django field type` raise at the same module) — no semantic change.
- `_FakeArrayField` placed immediately after the `_introspect_field_type` helper rather than directly above the Slice-3 banner, matching the plan's suggested test-helper region placement so all sections (Slice 1 / Slice 2 / Slice 3 / any future slice) can reference it without re-declaration.
- The `converters` module import is added as a single `from django_strawberry_framework.types import converters` line beneath the existing symbol-import group rather than collapsing it into the existing `from .converters import (...)` tuple — keeps the module-reference vs. symbol-reference distinction obvious to readers.
- Synthetic test models use distinct PascalCase names per test (e.g. `ArrayIntOwner`, `ArrayMultidimOwner`) sharing `app_label = "test_arrayfield"`, mirroring Slice 1's BigInt naming convention.
- `test_array_field_choices_inner_via_fake_sentinel` asserts only on the terminal `kind == "ENUM"` (not the exact enum name) — the spec checklist line 162 names the test but does not pin the name; the kind assertion is the minimum spec contract and reads cleanly.
- `test_array_field_base_field_unsupported_type_raises` declares the unsupported `_Weird(models.Field)` subclass inside the test (idiom precedent at `tests/types/test_converters.py:394-405` for the existing `_UnsupportedField` test).
- `test_array_field_sentinel_none_path` keeps the `_FakeArrayField(models.IntegerField())` instance well-formed (real `base_field` argument) even though the recursive call never fires under the `None`-patched sentinel — pre-empts any future `__init__`-time validation surprises.

### Notes for Worker 3

- No shadow file was used during implementation; the plan's static-helper observations (post-Slice-3 `convert_scalar` expected ~62-65 lines / 7-8 branches) are the planner's projection. Actual post-implementation: `convert_scalar` ranges from line 85 to ~155 in the new source, with the new branch adding ~14 lines and four new conditionals (outer guard + nested check + choices check + outer-null ternary). Worker 3 can re-run the helper if precise line/branch metrics are wanted.
- The `class ArrayMultidimOwnerType(DjangoType)` declarations inside `pytest.raises` blocks deliberately have no body other than `Meta` — `DjangoType.__init_subclass__` raises during the `class` statement itself, so the test never observes a fully-constructed class.
- The new `from django_strawberry_framework.types import converters` import is the only addition to the import block; the existing `_sanitize_member_name` / `convert_choices_to_enum` / `convert_scalar` group is preserved verbatim.
- `_FakeArrayField` is reusable by Slice 4 callers, but Slice 4 will add its own `_FakeHStoreField` (different `__init__` signature and `contribute_to_class` body per Decision 7 spec lines 622-630), so no cross-slice extraction is appropriate here.

### Notes for Worker 1 (spec reconciliation)

- No spec drift surfaced during implementation. The verbatim code blocks in Decision 2 (lines 500-515) and Decision 4 (lines 527-533, 544) landed exactly as specified, modulo ruff's trailing-comma additions inside the multi-arg `ConfigurationError(...)` calls (already the file's house style — see the pre-existing `Unsupported Django field type` raise).
- The HStoreField TODO at the now-renumbered `converters.py:33-35` (was `:37-39` pre-Slice-3 because the ArrayField TODO above it consumed 3 lines + a blank line) is untouched; Slice 4's anchor is intact.
- `_ARRAY_FIELD_CLS` is the only new module-level constant in `converters.py`. No parallel `_HSTORE_FIELD_CLS` was pre-emptively added.
- `django_strawberry_framework/__init__.py` and `tests/base/test_init.py` are not in the diff — no public-surface change.

---

## Review (Worker 3)

Static helper rerun against post-Slice-3 source on 2026-05-17:

- `uv run python scripts/review_inspect.py django_strawberry_framework/types/converters.py --output-dir docs/builder/shadow` — overview at `docs/builder/shadow/django_strawberry_framework__types__converters.overview.md`.
- `uv run python scripts/review_inspect.py tests/types/test_converters.py --output-dir docs/builder/shadow` — overview at `docs/builder/shadow/tests__types__test_converters.overview.md`.

Slice-3-only files inspected via `git diff` and the artifact's "Files touched": `django_strawberry_framework/types/converters.py` (only the helper + sentinel + new branch — the `BigInt` import, the two `SCALAR_MAP` `BigInt` rows, the `JSONField` row, the `dict[..., Any]` widening, and the multi-TODO trim are all Slices 1-2 baseline already-accepted by prior reviews) and `tests/types/test_converters.py` (only the Slice-3 banner + 12 new tests beginning at the post-Slice-2 region; `_FakeArrayField` and `_walk_introspected_type` / `_introspect_field_type` are Slice 1 baseline; `BigInt` / `finalize_django_types` / `converters` imports landed in earlier slices).

### High:

None.

### Medium:

None.

### Low:

#### `convert_scalar` docstring drift on the Raises and Algorithm sections

The new ArrayField sentinel branch landed at `converters.py:117-130` (the first executable block of `convert_scalar`'s body). The function's docstring at `converters.py:88-110` was not updated:

- The "Algorithm" enumeration (lines 88-94) still reads as a three-step list (MRO walk -> choices -> null widening) and does not mention the pre-MRO ArrayField branch that now runs first.
- The "Raises" entry (lines 106-109) lists two `ConfigurationError` triggers (no SCALAR_MAP match; grouped choices via `convert_choices_to_enum`) and omits the two new triggers (`Nested ArrayField on ...`, `... declares choices on the outer ...`).

Severity: Low — the inline comment at lines 111-116 covers the branch's design intent, and the source above it documents the new behavior, so a reader is not actively misled. But the canonical contract surface (the docstring) now lags the function body. Recommended fix: add a step `0` to the Algorithm list ("If `_ARRAY_FIELD_CLS` is set and `field` is an `ArrayField`, recurse on `base_field`, reject nested arrays and outer `choices`, and widen the resulting `list[T]` if `field.null`.") and append the two new `ConfigurationError` triggers to the Raises entry. The plan deliberately treated docstring touch-ups as implementer discretion and Worker 2 chose the inline-comment-only path; calling this Low rather than Medium because the spec did not pin a docstring rewrite and the comment-block-above-branch shape is internally consistent with the file's idiom. Worker 1 may resolve at final verification or defer to Slice 4 (which will add another sentinel branch and re-open the same docstring).

```django_strawberry_framework/types/converters.py:88
"""Map a Django scalar field to a Python / Strawberry type.

Algorithm:

1. Walk ``type(field).__mro__`` until a supported Django field class is
   found in ``SCALAR_MAP``; raise ``ConfigurationError`` if unsupported.
2. If the field declares ``choices``, replace the scalar type with a
   generated ``Enum`` via ``convert_choices_to_enum(field, type_name)``.
3. If the field is nullable, widen to ``T | None``.

Order matters: choices replaces ``py_type`` *before* null widening so
nullable choice fields end up as ``EnumType | None``, not
``(str | None)`` collapsed away.
```

### DRY findings

- **Deferred per plan: `_resolve_array_field` / `_resolve_hstore_field` near-copy.** The plan's DRY analysis explicitly defers consolidation to the integration pass (spec Decision 4 commits to two separate helpers; the bodies differ in exactly one identifier). After Slice 4 lands, the integration pass should evaluate whether `_resolve_postgres_field(name: str)` factory or a `_resolve_postgres_attr(attr_name)` shape is warranted — but only after both call sites exist. Recorded here as a flag, not a finding, per the spec/plan's explicit deferral language. The integration pass owns the call.
- **Deferred per plan: outer-`isinstance` guard pattern between `_ARRAY_FIELD_CLS` and the upcoming `_HSTORE_FIELD_CLS` branch.** The dispatch shape (`if _X_FIELD_CLS is not None and isinstance(field, _X_FIELD_CLS):`) and the outer-`choices` rejection-with-`ConfigurationError` posture will be near-copied by Slice 4. The post-isinstance bodies are different (ArrayField recurses; HStoreField returns `JSON` directly), so a shared helper across the two branches is not the right shape. Worker 3's view: keep the named-sentinel-per-branch grain, and at integration evaluate only whether the *outer-`choices` rejection message templates* share enough phrasing to warrant a shared format string. Recorded as a flag for the integration pass.
- **`app_label = "test_arrayfield"` literal appears 10x in `tests/types/test_converters.py` (per the static helper's Repeated string literals section).** Pre-Slice-3 the file had 5x `"test_bigint"` + 3x `"test_jsonfield"`; post-Slice-3 the total `app_label` literal density is ~18 sites. Worker 1's prior cross-slice carry-forward (worker-memory note line 11) already flagged the threshold; Slice 4 will push past 20. Recorded here as the same deferred follow-up; not a Slice-3 finding because pulling out a constants block at Slice 3 would force Slice 4 to inherit a shape it had no input on, which is the same anti-pattern the plan called out for `_resolve_*_field`.
- **`_ARRAY_FIELD_CLS` literal appears 9x in `tests/types/test_converters.py`** — every sentinel-branch test calls `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", ...)`. Spec Decision 7 spec line 635 pins this shape verbatim; pulling out a helper `_patch_array_sentinel(monkeypatch, value=_FakeArrayField)` would hide the spec-pinned step and obscure the BEFORE-DjangoType ordering requirement. Worker 3 explicitly rejects extracting a helper here; the repetition is the contract surface.
- **No DRY violation in the `convert_scalar` early-return null-widen (line 130) duplicating the tail `if field.null` branch (lines 150-151).** The plan flagged this proactively; the duplication is intentional because the early-return must compute `result = list[inner]` from the recursive call and widen there, not fall through to the tail (which would re-run the MRO walk against `_FakeArrayField` and either mis-match or fail to find a row). Two lines duplicated; not worth a helper.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` shows the `BigInt` re-export — but that addition belongs to Slice 1 (per the build artifact `docs/builder/bld-slice-1-bigint_scalar.md`, where Decision 6 / spec lines 580-583 / spec line 199 pin `BigInt` as the new public export). Slice 3's plan steps 6 and 11 explicitly forbid touching `__init__.py`; the Slice 3 contract is "no new public exports". Confirmed: Slice 3's diff against `__init__.py` is the empty set after isolating Slice-1-already-accepted changes. `__all__` unchanged by Slice 3.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **Decision 2 verbatim adherence is exact.** The branch at `converters.py:117-130` matches the spec block (Decision 2 lines 500-514) line-for-line, modulo ruff-format-added trailing commas inside multi-arg `ConfigurationError(...)` calls (which the existing `Unsupported Django field type` raise at `converters.py:142-147` already uses, so the post-Slice-3 file is internally consistent). Walked the four required ordering points: (1) outer-guard short-circuit `_ARRAY_FIELD_CLS is not None and isinstance(field, _ARRAY_FIELD_CLS)` at line 117, (2) nested-array rejection BEFORE outer-`choices` rejection (lines 118-127), (3) recursive `convert_scalar(field.base_field, type_name)` at line 128 (threads `type_name` so the inner enum name builds correctly per spec line 517), (4) outer-null widening at line 130 (`return result | None if field.null else result`, ternary form per the spec). The branch placement BEFORE the MRO walk at lines 131-141 satisfies spec line 500.
- **Decision 4 sentinel pattern is exact.** `_resolve_array_field()` at `converters.py:69-79` is the spec-verbatim four-line `try / except ImportError / return None / return ArrayField`. The module-level `_ARRAY_FIELD_CLS: type[models.Field] | None = _resolve_array_field()` at line 82 matches spec line 544 character-for-character, including the type annotation. Both `isinstance()` calls in `convert_scalar` (line 117 + line 118) dispatch on the module-level sentinel, not a hardcoded `_FakeArrayField` reference — confirmed via the static helper's Calls of interest section. The named-function shape (vs. inline `try / except` at module scope) is the necessary precondition for the `test_resolve_array_field_returns_none_when_postgres_fields_unimportable` test (the `sys.modules[name] = None` patch needs a function call to re-evaluate; a single module-load `try / except` would lock in the dev-env result and the negative branch would be unreachable).
- **Test fixture pattern adheres to Decision 7 ordering.** Every sentinel-branch test follows the sequence: `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)` -> model declaration -> `DjangoType` declaration (the dispatch-triggering step). Walked all 9 sentinel-branch tests at `tests/types/test_converters.py:867-1139` and confirmed the monkeypatch line is the first executable statement in every test body, BEFORE either the model class or the `DjangoType` class. The dispatch correctly reads `converters._ARRAY_FIELD_CLS` dynamically at `convert_scalar` call-time (module-level attribute access, not a cached local), so monkeypatch's setattr is the right primitive — confirmed by reading the post-edit `convert_scalar` body.
- **Multi-dim rejection test exercises the nested-fake shape and asserts at type declaration time.** `test_array_field_multidim_rejected_via_fake_sentinel` at lines 1010-1026: `_FakeArrayField(_FakeArrayField(models.IntegerField()))` is declared on the model, then the `DjangoType` declaration is wrapped in `pytest.raises(ConfigurationError, match="Nested ArrayField on")`. The model class declaration itself does not raise (only the `DjangoType` triggers `convert_scalar`); the test correctly observes the rejection at type-creation time, which is the spec contract. The `match=` substring pins Decision 2's exact-phrasing rejection message.
- **`base_field`-unsupported propagation surfaces the existing `Unsupported Django field type` error code path.** `test_array_field_base_field_unsupported_type_raises` at lines 1094-1115 declares an in-test `_Weird(models.Field)` subclass (idiom precedent at `tests/types/test_converters.py:394-396` with `_UnsupportedField`) and asserts `match="Unsupported Django field type"`. The recursive `convert_scalar(field.base_field, type_name)` at converters.py:128 reaches the MRO walk on the inner `_Weird` field; the walk hits the no-match `if py_type is None:` branch at line 142 and raises with the existing error. The test confirms code-path reuse rather than introducing a new error code for the inner case.
- **`_FakeArrayField` metadata propagation matches Decision 7 verbatim.** `_FakeArrayField.contribute_to_class` at `tests/types/test_converters.py:463-466` calls `super().contribute_to_class(cls, name, **kwargs)` then `self.base_field.set_attributes_from_name(name)` and `self.base_field.model = cls`. This propagates `name` and `model` to the inner `base_field` so the recursive `convert_scalar` call finds `field.model.__name__` and `field.name` when building the enum name in `convert_choices_to_enum` (verified by the `test_array_field_choices_inner_via_fake_sentinel` test passing the schema-build step). The `__init__` signature `(self, base_field, **kwargs)` correctly forwards `choices=...` and `null=...` to `models.Field.__init__` via `super().__init__(**kwargs)` — confirmed by `test_array_field_outer_nullable_via_fake_sentinel` (`null=True`) and `test_array_field_outer_choices_rejected_via_fake_sentinel` (`choices=[...]`).
- **Real-ArrayField gated test walks the `kind / ofType` chain explicitly per the spec note.** `test_real_array_field_compatible_with_strawberry` at lines 1142-1176 uses `pytest.importorskip("django.contrib.postgres.fields")` and exercises the live `_ARRAY_FIELD_CLS` (the real `ArrayField` class) end-to-end. The introspection navigation walks `type_payload["kind"]` -> `["ofType"]["kind"]` -> `["ofType"]["ofType"]["kind"]` -> `_walk_introspected_type(...)` for the terminal, asserting the `NON_NULL -> LIST -> NON_NULL -> SCALAR { name: "Int" }` chain per spec line 167. Does NOT rely on `field.type.name` (which would be `None` for wrapping types per spec line 167's parenthetical).
- **Sentinel-`None` short-circuit is pinned.** `test_array_field_sentinel_none_path` at lines 1118-1139 monkeypatches `converters._ARRAY_FIELD_CLS = None` and declares a `DjangoType` with a `_FakeArrayField` field; the test asserts `match="Unsupported Django field type"`, confirming the guard `_ARRAY_FIELD_CLS is not None and isinstance(...)` short-circuits before `isinstance(field, None)` would raise `TypeError`. Without this test, a future refactor that flipped the guard's `is not None` check (e.g. to `_ARRAY_FIELD_CLS and isinstance(...)`) would break silently — Python's `None` is falsy so the boolean short-circuit would still hold, but the test as written is the regression catcher for the exact spec-pinned guard shape.
- **The static helper's Repeated string literals section confirms no cross-file literal duplication regression.** The literals it surfaces (`NON_NULL`, `_ARRAY_FIELD_CLS`, `test_arrayfield`, `django.contrib.postgres.fields`, `Unsupported Django field type`) are all within `tests/types/test_converters.py` and are the spec-contract literals every test is required to assert on. The single `Unsupported Django field type` cross-file echo (one site in `converters.py`, one in tests) is the matching contract assertion. No cross-module literal leakage.

### Temp test verification

- No temp test files used during review. The 12 permanent tests in `tests/types/test_converters.py` (9 mandatory sentinel-branch + 2 helper-resolver + 1 optional gated) cover every spec-required branch and every new conditional in the diff. Confirmed by walking each spec-pinned behavior against an asserting test name (see "What looks solid" above).
- Disposition: N/A — none created.

### Notes for Worker 1 (spec reconciliation)

- **Spec drift: none.** The verbatim spec blocks in Decision 2 (lines 500-515) and Decision 4 (lines 527-533, 544) landed exactly as specified. The only deviation from the spec listing is ruff-format-added trailing commas inside the multi-arg `ConfigurationError(...)` calls, which match the file's pre-existing house style at the `Unsupported Django field type` raise.
- **Docstring follow-up candidate.** The Low finding above (Algorithm + Raises sections of `convert_scalar` lag behind the function body) is a docstring-only edit. Worker 1 may resolve at this slice's final verification, defer to Slice 4 (which will add the `_HSTORE_FIELD_CLS` branch and re-open the same docstring), or defer to the integration pass. Recommendation: defer to Slice 4 to amortize the docstring rewrite cost — pulling it into Slice 3 makes Slice 4 re-edit the same section. Recording so Worker 1 can decide explicitly rather than implicitly inherit.
- **Cross-slice carry-forward to Slice 4 planning (mirroring Worker 1's own note at the plan's end).** The DRY-watch items below ARE NOT Slice 3 findings; they are observations for the integration pass:
  - `_resolve_array_field` / `_resolve_hstore_field` will be parallel helpers post-Slice-4. Spec Decision 4 commits to the two-helper shape; integration pass owns the consolidation evaluation after both sites exist.
  - The outer-`choices` rejection message templates in `_ARRAY_FIELD_CLS` and `_HSTORE_FIELD_CLS` branches will both name `field.model.__name__` and `field.name` and use `ConfigurationError`. The post-rejection shape will differ (ArrayField recurses; HStoreField returns `JSON`), so a shared dispatch helper is not the right shape — but the *error-message-format* may consolidate.
  - The synthetic-model + `DjangoType` + `Query` schema-execution pattern now appears at ~17 sites (5 BigInt + 3 JSON + 9 ArrayField). Slice 4 will push past 20. The `_make_one_field_schema(...)` extraction watchpoint Worker 3 has carried from Slice 1 / 2 stays open; defer to the integration pass.
  - The `app_label` literal count is ~18 post-Slice-3. Worker 1 may want to evaluate a `app_labels.py` constants module at integration — but only if Slice 4's additions push the count to a clear extraction threshold (~25+).
- **Plan-vs-implementation drift check (re-verified per Worker 1's own checklist at plan lines 240-246).** Walked each item:
  - `_resolve_array_field` exists exactly once. No `_resolve_hstore_field` parallel introduced. Confirmed via `git diff` and the static helper's Symbols section.
  - `_ARRAY_FIELD_CLS` is the only new module-level constant. No `_HSTORE_FIELD_CLS` parallel. Confirmed.
  - `convert_scalar` has exactly one new branch (lines 117-130). No `_HSTORE_FIELD_CLS`-guarded branch pre-emptively added. Confirmed.
  - HStoreField TODO at `converters.py:33-35` (now renumbered post-Slice-3 because the ArrayField TODO above it was removed) is untouched. Confirmed via the static helper's TODO comments section.
  - `django_strawberry_framework/__init__.py` is NOT in Slice 3's slice diff (the `BigInt` change is Slice 1's baseline). `tests/base/test_init.py` similarly NOT in Slice 3's slice diff. Confirmed.
  - `_FakeArrayField` is present; no `_FakeHStoreField` parallel. Confirmed.

### Review outcome

`review-accepted` — every High/Medium finding is `None.`; the single Low (docstring drift on `convert_scalar`'s Algorithm + Raises sections) is intentionally rejected with a recorded reason (the inline comment block at converters.py:111-116 covers the design intent; the cost of touching the docstring twice across Slices 3 + 4 outweighs the polish, and the recommended consolidation is deferred to Slice 4 or the integration pass). DRY findings are all explicit deferred-to-integration-pass observations per the plan's own DRY analysis. Public surface unchanged by Slice 3. CHANGELOG and docs/release surfaces not touched. Top-level `Status:` set to `review-accepted`.

---

## Final verification (Worker 1)

### DRY check across this slice and prior accepted slices (Slices 1-2)

Walked the three near-copy patterns the task brief flagged, plus the full set of DRY observations Workers 2 and 3 recorded in this artifact and the carry-forwards from Slice 1 / Slice 2.

- **Test helpers `_make_one_field_schema` / `_introspect_field_type` / `_walk_introspected_type`.** `_introspect_field_type` and `_walk_introspected_type` already exist as **shared** helpers in `tests/types/test_converters.py:419-446`; Slice 3 reuses them verbatim (no inline reimplementation, no per-test duplication of the introspection-chain literal). Confirmed by walking each of the 8 introspection-using Slice-3 tests in the diff — every one calls `_introspect_field_type(schema, ...)` and then `_walk_introspected_type(...)` rather than open-coding the `__type { fields { ... ofType { ... } } }` query string. `_make_one_field_schema` does **not** exist yet — the synthetic-model + `DjangoType` + `Query` trio remains open-coded across Slices 1 (5 sites), 2 (3 sites), and 3 (~9 sites = ~17 total). Worker 3 of Slice 1 flagged this as a deferred-helper candidate, Worker 1 of Slice 2 carried it forward, and Worker 1 of Slice 3's planning pass explicitly resisted unilateral extraction because Slice 4 has not yet been planned. **Verdict: defer to integration pass.** Slice 4 will add another ~6-8 trio sites and finalize the parameter surface (sentinel monkey-patching, choice handling on `base_field`, outer-`choices` rejection, sentinel-`None` path); the helper signature is only knowable once that surface is visible. No new `revision-needed` finding here — the spec/plan deferred consolidation, and the slice honors the deferral. This is exactly the cross-slice DRY watchpoint the integration pass owns per `docs/builder/BUILD.md` "Cross-slice integration pass" / "comparing the Repeated string literals sections".

- **`_resolve_array_field` will be near-twin to `_resolve_hstore_field` once Slice 4 lands.** Confirmed by reading Decision 4 (spec lines 525-548): the spec commits to **two parallel four-line `try / except ImportError / return None / return X` helpers** — that is the contract Slice 3 implements and Slice 4 will mirror. The bodies will differ in exactly one identifier (`ArrayField` vs `HStoreField`). A `_resolve_postgres_field(name: str)` factory has two anti-shapes (string-name indirection breaks IDE go-to-definition; `getattr(module, name)` pushes the import-attribute lookup into a runtime branch); the named-helper-per-attribute shape is the right grain for module-load-time soft imports. **Verdict: defer to integration pass.** The integration pass should re-evaluate whether the post-Slice-4 redundancy crosses an extraction threshold (e.g., a third postgres soft-import surface in a future spec), but Slice 3 cannot consolidate before Slice 4 exists, and Slice 4 will be planned against the spec's two-helper shape. Plan's `New helpers justified` bullet on the `_resolve_array_field` / `_resolve_hstore_field` near-copy pair (lines 23-24 of the plan) is the binding rationale; final verification confirms the posture.

- **Sentinel-guarded `convert_scalar` branch shape will repeat in Slice 4 (HStoreField).** Confirmed by reading Decision 2 (lines 499-515) and Decision 5 (lines 552-571) side by side. The two branches share **posture** — outer guard `if _<X>_FIELD_CLS is not None and isinstance(field, _<X>_FIELD_CLS):` + outer-`choices` rejection with `ConfigurationError` + outer `field.null` widening. The **post-isinstance bodies diverge structurally**: ArrayField rejects nested arrays, recurses through `base_field` to compute `inner = convert_scalar(field.base_field, type_name)`, then constructs `list[inner]`; HStoreField has no nested-rejection and no recursion — it returns `strawberry.scalars.JSON` directly. Extracting a shared dispatch helper would force one of three anti-shapes: (a) a callback parameter pattern that obscures both call sites' post-isinstance behaviour, (b) inlining HStoreField's logic via an `if branch_returns_directly: ... else: recurse` switch, (c) splitting the shared posture into a partial helper that callers must compose with their own bodies (no clean signature). **Verdict: defer to integration pass.** The two branches should remain as named branches in `convert_scalar`'s body; the only DRY consolidation worth weighing at integration is whether the **outer-`choices` error message templates** (each `f"..." {field.model.__name__}.{field.name} declares choices..."`) share enough phrasing to warrant a shared format-string constant. That decision is integration-pass-owned because Slice 3 has only one such message; Slice 4 adds the second.

- **`app_label` literal repetition.** Worker 3's static-helper rerun confirmed `app_label = "test_arrayfield"` appears ~10x in `tests/types/test_converters.py`; combined with `"test_bigint"` (5x, Slice 1) and `"test_jsonfield"` (3x, Slice 2), the file is at ~18 `app_label` literal sites post-Slice-3. Slice 4 will push past 20. **Verdict: defer to integration pass.** A constants-block extraction (`_APP_LABEL_ARRAY = "test_arrayfield"`, etc.) would only be worth the indirection cost once the count crosses a clear extraction threshold (typically ~25+ sites or a clear grouping benefit). Slice 4's additions will surface whether the threshold lands; Slice 3 must not pre-empt the decision.

- **`_FakeArrayField` reusability vs Slice 4's `_FakeHStoreField`.** Worker 2 and Worker 3 both flagged that the test doubles share the `models.Field` subclassing idiom but have structurally distinct bodies (`_FakeArrayField` takes `base_field` and propagates metadata via `contribute_to_class`; `_FakeHStoreField` per spec lines 622-630 is a bare pass-class with no `base_field`). **Verdict: no consolidation candidate.** The two fakes serve different dispatch surfaces with different metadata requirements; extracting a shared base class would add complexity without removing duplication.

- **Two-line outer-`null` widening duplicating the tail `if field.null` branch inside `convert_scalar`.** Worker 1 of Slice 3's planning pass and Worker 3 of Slice 3's review both flagged the intentional two-line duplication (the early-return branch must compute `result = list[inner]` from the recursive call and widen there, not fall through to the tail which would re-run the MRO walk against `_FakeArrayField`). **Verdict: no consolidation candidate** — the duplication is structurally necessary; extracting it would require routing the MRO-walk result through the same widening path, which doesn't work for the early-return shape. Spec Decision 2 line 514 pins the `return result | None if field.null else result` shape verbatim.

**Cross-slice duplication audit verdict: no new revision-needed finding.** Every duplication observation either (a) was explicitly deferred to the integration pass by the plan and spec (`_resolve_*_field` pair, `convert_scalar` sentinel-branch posture, `app_label` literal density, trio-pattern extraction) or (b) is structurally necessary and pinned by spec language (the two-line outer-null widening, the differing test-double bodies). Slice 3 honors every deferral and introduces no DRY violation that the plan did not anticipate.

### Existing tests still pass

Ran `uv run pytest tests/test_scalars.py tests/types/test_converters.py tests/base/test_init.py -x` (no `--cov*` flags supplied). Result: **71 passed, 1 skipped, 2 warnings in 0.36s**.

- The 1 skip is `test_real_array_field_compatible_with_strawberry`, the `pytest.importorskip("django.contrib.postgres.fields")`-gated test on a dev environment without postgres-contrib installed. Spec line 167 explicitly permits this skip on environments missing the postgres driver.
- The 2 warnings are the pre-existing `test_choice_enums._owner` re-registration RuntimeWarnings carried from before this build began; Slice 1 Worker 1 / Worker 3 noted them as out-of-slice scope and Slice 2 / Slice 3 inherit the same posture. Slice 4 / integration pass may revisit for a warnings-clean summary.
- Coverage banner appeared in the output (pyproject.toml's default coverage config attaches to every pytest invocation), but I did not pass any `--cov*` flags and did not act on the coverage report per the "Coverage is the maintainer's gate, not a worker's tool" rule. The only signal weighed for this gate is the `71 passed, 1 skipped` test outcome.

### Spec reconciliation

Re-read Worker 2's `Notes for Worker 1 (spec reconciliation)` (artifact lines 308-313) and Worker 3's `Notes for Worker 1 (spec reconciliation)` (artifact lines 398-413). Walked each item against the active spec.

- **Worker 2: "No spec drift surfaced during implementation."** Confirmed against Decision 2 (spec lines 495-519) and Decision 4 (spec lines 525-548). Verbatim shapes landed exactly as the spec blocks specify, modulo ruff-format-added trailing commas inside the multi-arg `ConfigurationError(...)` calls — the file's pre-existing house style at the `Unsupported Django field type` raise already uses the same trailing-comma form, so the post-Slice-3 file is internally consistent. **No spec edit needed.**
- **Worker 2: HStoreField TODO untouched.** Confirmed by reading the post-Slice-3 `converters.py` TODO block — only the HStoreField TODO remains at `converters.py:32-34` (the ArrayField TODO above it was removed; the original line numbers shifted). Slice 4's anchor is intact. **No spec edit needed.**
- **Worker 2: `_ARRAY_FIELD_CLS` is the only new module-level constant; no `_HSTORE_FIELD_CLS` parallel.** Confirmed via the diff's symbol additions. **No spec edit needed.**
- **Worker 2: `__init__.py` and `tests/base/test_init.py` not in Slice 3's slice diff (the visible diff against those files belongs to Slice 1's already-accepted baseline).** Confirmed by `git diff` isolation. **No spec edit needed.**

- **Worker 3 Low: `convert_scalar` docstring drift on Algorithm + Raises sections.** Worker 3 recommended deferring the docstring rewrite to Slice 4 (which will add a second sentinel branch and re-open the same docstring) to amortize the touch cost. Reading the spec: Decision 2 (lines 499-515) pins the **branch body** verbatim but is **silent on docstring updates**; Decision 5 (lines 555-571) similarly pins the HStoreField branch body but says nothing about docstring shape. The spec does not require a docstring rewrite at Slice 3 time. The task brief asked Worker 1 to "confirm that posture or edit the spec if the deferral is muddled." **Posture confirmed; no spec edit needed.** Reasons:
  - The spec is not muddled on this point — it is intentionally silent. Docstring shape is implementer's discretion when the spec doesn't pin it.
  - Slice 4 will modify `convert_scalar`'s body again (adding the `_HSTORE_FIELD_CLS`-guarded branch); rewriting the Algorithm + Raises sections at Slice 3 time would require a second rewrite at Slice 4 to add the HStoreField triggers. Amortizing the rewrite to Slice 4 is the structurally efficient call.
  - Inline comments at `converters.py:111-116` document the new branch's design intent at the call site. A reader landing in `convert_scalar`'s body is not actively misled — the inline block carries the design rationale even while the docstring lags.
  - This is recorded in Slice 3's artifact (Worker 3's Low + Worker 3's Notes for Worker 1) so Slice 4's planner inherits the deferred-docstring TODO as a slice contract obligation. Slice 4 Worker 1 must add a step that rewrites the Algorithm enumeration to include both new branches (step 0 ArrayField + step 0a HStoreField, or a re-shaped two-bullet preface) and updates the Raises entry to list all four new triggers (nested ArrayField, outer ArrayField choices, outer HStoreField choices). The Slice 4 planning pass owns the docstring-rewrite scope.

- **Cross-slice DRY notes Worker 3 carried for integration pass.** Already addressed in the DRY check above. No spec edit triggered by any of them; the spec/plan deferrals are honored.

- **Spec status line re-verification.** Read `docs/spec-deferred_scalars.md:1-7` at the start of this pass: `Status: draft (revision 10, post-feedback2 re-review).` Predecessor and card-line references still accurate. Slice 3 ships per the slice checklist; no slices have been archived yet (archival is Slice 6). **No spec edit needed.**

**Spec reconciliation outcome: no spec edit triggered by Slice 3.** Worker 2 and Worker 3 both reported zero spec drift; the docstring deferral is consistent with the spec's silence on docstring shape; the cross-slice DRY observations are integration-pass-owned per existing spec/plan language.

### Final status

`final-accepted` — set on the artifact's top-level `Status:` line. Every planned implementation step landed in the diff; every spec-pinned test name is present; the public surface is unchanged by Slice 3 (the `BigInt` re-export in `__init__.py` belongs to Slice 1's already-accepted baseline); no new DRY violations vs. Slices 1-2 surfaced; existing tests pass; no spec edit needed.

### Summary

Slice 3 ships the sentinel-guarded `ArrayField` → `list[T]` recursion in `convert_scalar`. Adds `_resolve_array_field()` soft-import helper and the `_ARRAY_FIELD_CLS` module-level sentinel between `SCALAR_MAP` and `convert_scalar`. Inserts a new branch in `convert_scalar` that runs before the MRO walk, recurses through `field.base_field` for the inner type, rejects nested `ArrayField` and outer `choices` with `ConfigurationError`, and widens the outer `list[T]` if `field.null` is True. Drops the ArrayField TODO comment; preserves the HStoreField TODO for Slice 4. Adds `_FakeArrayField(models.Field)` test double and the `converters` module import in `tests/types/test_converters.py`. Adds 11 tests covering helper-resolver behavior (positive and `ImportError` branches via `sys.modules` manipulation), sentinel-branch shape introspection (4 wrapping-level variants), nested-array and outer-`choices` rejections, choice handling on `base_field` via recursive inheritance, unsupported `base_field` propagation, the sentinel-`None` short-circuit guard, and one `pytest.importorskip`-gated end-to-end test against the real `ArrayField`. No public-surface change; no CHANGELOG / docs / release / KANBAN edits (all Slice 6 territory).

### Spec changes made (Worker 1 only)

None.
