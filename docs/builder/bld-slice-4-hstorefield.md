# Build: Slice 4 — `HStoreField` conditional registration via sentinel + `strawberry.scalars.JSON` target

Spec reference: `docs/spec-deferred_scalars.md` (Slice checklist lines 168-187, Decision 4 lines 525-548, Decision 5 lines 550-578, Decision 7 / Schema test fixture pattern lines 594-705, User-facing API lines 712-729, Test plan categories 11-12 + 17 + 18 + 19 lines 786-805)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - **Slice 3's `_resolve_array_field()` helper** at `django_strawberry_framework/types/converters.py:69-79` is the **near-twin** of Slice 4's `_resolve_hstore_field()`. The two helpers differ in exactly one identifier (`ArrayField` ⇄ `HStoreField`). The spec's Decision 4 (spec lines 525-548) explicitly pins both helpers as parallel single-purpose functions. **Slice 4 plans for the spec-pinned two-helper shape and defers any consolidation to the integration pass.** Rationale carried forward from Slice 3's plan (`docs/builder/bld-slice-3-arrayfield.md` lines 19-23): a `_resolve_postgres_field(name: str)` factory would either pass the name as a string (ugly indirection at the call site and breaks IDE go-to-definition) or use `getattr(module, name)` (pushes the import-attribute lookup into a runtime branch). Worker 3 should flag the duplication explicitly as DRY observation **but not as a finding** — the integration pass owns cross-slice DRY consolidation per BUILD.md.
  - **Slice 3's `_ARRAY_FIELD_CLS` module-level sentinel** at `converters.py:82` is the structural template for Slice 4's `_HSTORE_FIELD_CLS`. Same lexical tier (module-level, leading underscore, single-source-of-truth for the `convert_scalar` branch guard), same annotation shape (`type[models.Field] | None`), same monkeypatch contract for tests. The two sentinels are **read by different branches** in `convert_scalar` with **different post-isinstance behavior** (ArrayField recurses through `base_field` and wraps in `list[T]`; HStoreField rejects outer `choices`, then returns `strawberry.scalars.JSON` with optional `| None` widening). The named-sentinel-per-branch shape is the right grain — do NOT collapse the two sentinels into a tuple per Slice 3's plan-step DRY note.
  - **Slice 3's `ArrayField` sentinel branch** in `convert_scalar` at `converters.py:117-130` shares the **outer-guard posture** with Slice 4's new HStoreField branch (`if _HSTORE_FIELD_CLS is not None and isinstance(field, _HSTORE_FIELD_CLS): ...`). The structural parallel is deliberate per spec Decision 5 (lines 550-571 — the HStoreField branch "mirrors Decision 2's shape"). Post-isinstance bodies diverge: ArrayField's body recurses on `base_field` and produces `list[inner]`; HStoreField's body checks outer `choices`, then returns `strawberry.scalars.JSON` with optional `| None` widening. **No shared dispatch helper** — the surrounding-context divergence is real (ArrayField has nested-array rejection + recursive call; HStoreField only has outer-choices rejection + direct JSON return). Recording the parallel-but-different posture explicitly so Worker 3 and integration-pass reviewers see the deliberate shape.
  - **`ConfigurationError` import** at `converters.py:26` is already in place. The HStoreField outer-`choices` rejection raises the same exception class as ArrayField's outer-`choices` rejection (`converters.py:122-127`); **do not** re-import, and **do not** introduce a new exception subclass. The error-message shape (`f"HStoreField on {field.model.__name__}.{field.name} declares choices; ..."`) is spec-pinned verbatim at spec lines 563-568 — names `field.model.__name__` + `field.name`, gives `dict[str, str | None]` rationale, ends with a consumer-actionable hint ("Drop the choices declaration or model the constrained shape with a separate field"). This message-template parallel with the ArrayField message at `converters.py:123-126` is the **one cross-slice DRY candidate worth weighing at the integration pass** per Slice 3's final-verification carry-forward (worker-1 memory entry dated 2026-05-17): both messages name `field.model.__name__` + `field.name`, use the same `ConfigurationError` exception class, and structurally follow `<FieldType> on <Model>.<Field> declares choices; <rationale>; <recourse hint>`. Slice 4 plans for the spec-pinned wording verbatim; the integration pass may evaluate whether to extract a shared format-string constant once both sites exist.
  - **`strawberry.scalars.JSON`** is the return value for the HStoreField branch (spec line 569: `py_type = strawberry.scalars.JSON`). It was introduced as a `SCALAR_MAP` value by Slice 2 at `converters.py:61` (`models.JSONField: strawberry.scalars.JSON`). Slice 4 references the **same symbol** in a sentinel-guarded branch return rather than a `SCALAR_MAP` row (per spec line 172 / Decision 5: `HStoreField` is **not** added to `SCALAR_MAP`). **No new import** — `strawberry` is already imported at `converters.py:23`, and `strawberry.scalars.JSON` is accessible via attribute access. Confirmed against the shadow overview: Slice 2's `SCALAR_MAP` row reads `strawberry.scalars.JSON` directly (`converters.py:61`); the new branch will use the same attribute access. Slice 2's planning carry-forward (worker-memory dated 2026-05-17) flagged this as the **DRY watchpoint for the integration pass**: a module-level `_JSON_SCALAR = strawberry.scalars.JSON` alias may be worth introducing once both call sites exist — but the indirection cost (one extra name to grep through) may not be worth the gain given the differing surrounding context (dict value vs. branch return). Slice 4 explicitly references `strawberry.scalars.JSON` inline per spec verbatim; integration pass decides on the alias.
  - **Slice 3's `_FakeArrayField(models.Field)` test double** at `tests/types/test_converters.py:450-466` is the structural precedent for Slice 4's `_FakeHStoreField(models.Field)`. The shapes diverge per spec Decision 7 lines 622-630: `_FakeArrayField` accepts a `base_field` argument and propagates metadata in `contribute_to_class`; `_FakeHStoreField` is a **bare `pass` class** with no `__init__` override and no metadata-propagation contract (the HStoreField branch does not recurse, so there is no inner field to wire up). Slice 4 follows spec lines 622-630 verbatim.
  - **The in-function model + sentinel-swap pattern** anchored by Decision 7 lines 641-657 is reused verbatim. Slice 3's tests at `tests/types/test_converters.py:867-1139` provide the exact recipe: `monkeypatch.setattr(converters, "_<NAME>_FIELD_CLS", _Fake<Name>Field)` BEFORE the `DjangoType` declaration, then `class _OwnerModel(models.Model): ...; class _OwnerType(DjangoType): ...; finalize_django_types()`, then build the schema and `schema.execute_sync(...)`. Slice 4 mirrors this for `_FakeHStoreField` with `app_label = "test_hstorefield"`.
  - **Synthetic-model `Meta` convention** (`managed = False; app_label = "..."`) per Decision 7 / spec line 633. Slice 4 declares `app_label = "test_hstorefield"` for its synthetic models — distinct from `"test_bigint"` (5 sites, Slice 1), `"test_jsonfield"` (3 sites, Slice 2), `"test_arrayfield"` (~9 sites, Slice 3), and `"test_choice_enums"` (the session-scoped fixture). Worker 1's running count after Slice 4 lands becomes 5 + 3 + ~9 + ~8 = **~25** `app_label` literal occurrences across `tests/types/test_converters.py`. Slice 3's final-verification carry-forward (worker-memory dated 2026-05-17) named ~25 as the threshold for reassessing a module-level constants block at the integration pass; Slice 4's count puts it exactly at the threshold. **Flagged for integration-pass evaluation, not a Slice-4 finding.**
  - **Introspection helpers `_walk_introspected_type` / `_introspect_field_type`** at `tests/types/test_converters.py:421-447`. Slice 4's HStoreField shape is `JSON!` or `JSON` (`NON_NULL → SCALAR { name: "JSON" }` or bare `SCALAR { name: "JSON" }`) — **identical depth** to Slice 2's JSONField cases (`tests/types/test_converters.py:759-764, 791-793`). The helpers cover this depth unchanged from Slice 1 (verified against the existing introspection-template literal at line 438 which nests `ofType { kind name ofType { kind name ofType { kind name } } }`). **Reuse verbatim; no extension required.**
  - **Test-isolation autouse fixture `_isolate_registry`** at `tests/types/test_converters.py:38-48` covers per-test registry cleanup for any new `DjangoType` subclasses declared in Slice 4's tests. Slice 4's tests inherit automatically (Decision 7 preamble, spec lines 637-639).
  - **The `sys.modules` manipulation pattern** for helper-resolver tests is spec-pinned at lines 661-676; Slice 3 implemented the verbatim shape at `tests/types/test_converters.py:839-864`. Slice 4 mirrors that shape for `_resolve_hstore_field`. Documented Python behavior: `sys.modules[name] = None` forces the next `import name` to raise `ImportError` (spec Risks line 825).
  - **Slice 1's `_make_one_field_schema(model_cls, field_name)` extraction watchpoint.** Worker 3's Slice 1 review flagged this as a deferred helper candidate when the trio-pattern site count grows. Post-Slice-3 count is ~17 sites (5 from Slice 1 + 3 from Slice 2 + ~9 from Slice 3). Slice 4 adds ~6 sentinel-branch trio-pattern sites + 1 real-postgres gated test = ~7 more. **Total post-Slice-4 count: ~24 sites.** Still deferred to the integration pass — Slice 4 is the last spec slice that mutates `tests/types/test_converters.py` (Slices 5 and 6 touch other files); the integration pass has full parameter-surface visibility once Slice 4 lands.

- **New helpers justified.**
  - **`_resolve_hstore_field() -> type[models.Field] | None`** in `django_strawberry_framework/types/converters.py`. Single responsibility: encapsulate the soft-import of `django.contrib.postgres.fields.HStoreField` so the dev environment (no postgres driver) does not raise at module load. The helper's body is the four-line `try / except ImportError / return None / return HStoreField` per Decision 4 (spec lines 536-541). It is called exactly once at module load (`_HSTORE_FIELD_CLS = _resolve_hstore_field()`) and exists as a separate function rather than an inline `try / except` so the helper-resolver tests can exercise both branches via `sys.modules` manipulation. Without the helper as a named function, the `None`-branch test would not be reachable (the module-load assignment evaluates exactly once). **Near-twin of `_resolve_array_field` at `converters.py:69-79`** — see DRY analysis above for the deferral-to-integration-pass rationale.
  - **Module-level sentinel `_HSTORE_FIELD_CLS: type[models.Field] | None`** at module load. Single responsibility: the cached guard value for the `convert_scalar` HStoreField branch's `isinstance` check. Reads in `convert_scalar` are O(1); the sentinel value is set once at module import and treated as immutable in production. Tests swap it via `monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)`; the patch reverts on teardown, so production code paths see the resolved value.
  - **`_FakeHStoreField(models.Field)` test double** in `tests/types/test_converters.py`. Single responsibility: a class the test can pass `monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)` against so the sentinel branch dispatches without requiring `django.contrib.postgres`. Decision 7 spec lines 622-630 pin the shape verbatim: subclasses `models.Field`, bare `pass` body, no `__init__` override, no `contribute_to_class` override. The HStoreField branch does not recurse into a base field, so the test double has no metadata-propagation contract — Django's default `models.Field.__init__` and `contribute_to_class` suffice. **No shared base class with `_FakeArrayField`** — the two doubles have structurally different bodies, and a shared base would force `_FakeHStoreField` to inherit an `__init__(self, base_field, **kwargs)` it does not want.

- **Duplication risk avoided.**
  - **Risk #1: extracting a `_resolve_postgres_field(name: str)` factory at slice time.** Don't. Per Slice 3's plan (lines 19-23 of `bld-slice-3-arrayfield.md`) and the task brief: the spec's Decision 4 commits to two separate helpers; consolidation is the **integration pass's** decision once both sites exist. A factory at slice time pre-empts the integration pass's evaluation. The factory's call shape (`_resolve_postgres_field("ArrayField")` / `_resolve_postgres_field("HStoreField")`) is also ugly indirection that breaks IDE go-to-definition. Slice 4 plans for two parallel helpers; integration pass owns the consolidation call.
  - **Risk #2: collapsing the `_ARRAY_FIELD_CLS` and `_HSTORE_FIELD_CLS` sentinels into one tuple.** Don't. They are read by different branches in `convert_scalar` with different post-isinstance behavior. A combined `_POSTGRES_FIELD_CLASSES = (...)` constant would force every `isinstance(field, ...)` call to dispatch on a tuple and lose the named contract for each branch.
  - **Risk #3: inlining the `try / except ImportError` directly at module scope without a named helper.** Module-scope `try: from django.contrib.postgres.fields import HStoreField; except ImportError: HStoreField = None` would work, but the `None`-branch test can only be exercised via `sys.modules` manipulation **before the module loads**. Wrapping in a named function makes both branches testable via `sys.modules[...] = None` (forces `ImportError`) and `sys.modules[...] = fake_module` (returns the test double).
  - **Risk #4: collapsing the new HStoreField branch into Slice 3's ArrayField branch.** The two branches share an outer-guard posture but diverge structurally in the body. A combined `_handle_postgres_field(field, type_name)` function would force a single body to handle both shapes (ArrayField's recursive call into `base_field` + `list[T]` wrap vs HStoreField's direct `JSON` return) with conditional sub-branches inside. The post-isinstance bodies are short enough (3 lines each) that the inlined branches are clearer than a shared dispatcher. **No consolidation at slice time; integration pass may revisit.**
  - **Risk #5: re-implementing the introspection chain walk inside the new Slice 4 tests.** Reuse `_walk_introspected_type` / `_introspect_field_type` from `tests/types/test_converters.py:421-447` verbatim. The helpers handle Slice 4's depth budget unchanged (HStoreField introspects as `NON_NULL → SCALAR` or bare `SCALAR` — at most 2 wrapping levels, well within the helper's 4-level budget).
  - **Risk #6: copy-pasting the test-fixture trio scaffold across the sentinel-branch tests.** Each test pairs a synthetic model + monkeypatch + `DjangoType` declaration + `finalize_django_types()` + schema build + introspection or `execute_sync` assertion. Slice 3's plan deferred extraction of `_make_one_field_schema(...)` to the integration pass; Slice 4 follows suit. The duplication is intentional at this stage — each test reads top-to-bottom without indirection, and the integration pass has the full parameter surface to design the helper once.
  - **Risk #7: missing the docstring rewrite carried forward from Slice 3.** Slice 3's final-verification noted that the `convert_scalar` docstring drifted (`Algorithm` enumeration and `Raises` entry lagged the new ArrayField branch). **Slice 4 must rewrite the docstring** to (a) mention the pre-MRO sentinel branches (ArrayField + HStoreField) in the `Algorithm` enumeration, and (b) extend the `Raises` entry to list all four `ConfigurationError` triggers (nested ArrayField, outer ArrayField choices, outer HStoreField choices, unsupported field). The rewrite is amortized across both sentinel branches in a single edit per the task brief. **This is a plan step, not a Worker-2-discretion item.**

- **Static helper observations** (from `docs/builder/shadow/django_strawberry_framework__types__converters.overview.md`, regenerated against post-Slice-3 source on 2026-05-17):
  - `convert_scalar` is currently **68 lines / 10 branch nodes** (control-flow hotspots section). Slice 4 inserts a new sentinel-guarded branch (~7-10 lines: outer guard + outer-`choices` rejection + `JSON` return + null-widen) plus a docstring rewrite (no net branch count change in the docstring itself). Expected post-Slice-4 shape: **~78-82 lines / 12-13 branches** — at or just over the BUILD.md control-flow-hotspot defaults (40 lines / 8 branches) but still within typical-function bounds. Worker 3 should expect this shift and not flag it as a Medium finding unless line count exceeds ~100 or branch count exceeds 15. The function is doing genuine dispatch work — splitting it would mean either (a) extracting the sentinel branches into helper functions (which adds indirection without saving complexity) or (b) restructuring the choice-substitution / null-widening tail (out of scope for this card).
  - One TODO comment remains at `converters.py:33` (the HStoreField TODO). Slice 4 removes this 3-line block (lines 33-35 per the shadow comment inventory). After Slice 4 lands, the comment inventory will be free of `# TODO(future):` lines tracking deferred scalar conversions — confirming the spec's "all TODO comments for deferred scalars removed" Definition-of-done item is satisfied (spec line 845).
  - `Repeated string literals` section is still `None.` post-Slice-3 — confirming no pre-existing cross-file literal pressure. Slice 4's new error-message string (`"HStoreField on ... declares choices; ..."`) appears once in `converters.py` and once as a test assertion `match=` substring; no DRY pressure beyond two sites.
  - `Calls of interest` post-Slice-4 will gain two new `isinstance()` calls (the sentinel-guard `isinstance(field, _HSTORE_FIELD_CLS)` — the HStoreField branch does not have a nested-field check, so only **one** new `isinstance()` site versus ArrayField's two). Worker 3 should verify the `isinstance` call dispatches on the **module-level sentinel** `_HSTORE_FIELD_CLS`, not a hardcoded reference to `_FakeHStoreField` (which would break the production path).
  - `Imports` section currently shows `from django.contrib.postgres.fields import ArrayField` at line 76 (the soft-import inside `_resolve_array_field`). Slice 4 adds a second soft-import inside `_resolve_hstore_field`. Both imports are inside `try / except ImportError` blocks per spec Decision 4 — the shadow overview will list both as `(django)` imports after Slice 4 lands. This is correct; no boundary leak.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Verify against the current source before editing — another worker's pass may have shifted the file since this plan was written.

1. **Add `_resolve_hstore_field()` helper to `django_strawberry_framework/types/converters.py`**. Place it **immediately after `_resolve_array_field()`** (current `converters.py:69-79`) and **before the `_ARRAY_FIELD_CLS` module-level assignment** (current `converters.py:82`), so the two helpers sit adjacent at the module-helper tier. Verbatim shape per Decision 4 (spec lines 536-541):
   ```python
   def _resolve_hstore_field() -> type[models.Field] | None:
       """Soft-import postgres ``HStoreField``.

       Returns ``None`` if ``django.contrib.postgres.fields`` is unavailable so
       package import succeeds on dev environments without the postgres driver.
       """
       try:
           from django.contrib.postgres.fields import HStoreField
       except ImportError:
           return None
       return HStoreField
   ```
   The docstring mirrors `_resolve_array_field`'s docstring verbatim (one sentence anchoring responsibility, one sentence noting the dev-env soft-import rationale) — keeping the two helpers visually parallel for maintainers. Implementer's discretion on the exact docstring wording is acceptable but the parallel posture is the intent.

2. **Add the module-level sentinel `_HSTORE_FIELD_CLS`** immediately after the `_ARRAY_FIELD_CLS` assignment (current `converters.py:82`). The two sentinels sit on adjacent lines at the same lexical tier:
   ```python
   _HSTORE_FIELD_CLS: type[models.Field] | None = _resolve_hstore_field()
   ```
   Annotation is `type[models.Field] | None` per Decision 4 (spec line 545). Leading underscore marks it module-private.

3. **Add the `HStoreField` sentinel branch to `convert_scalar`** (current `converters.py:85-152`). Place the new branch **immediately after the existing ArrayField sentinel branch** (`converters.py:117-130`) and **before the MRO walk** (current `converters.py:132-141`). Order matters per spec Decision 5 (lines 552-555 — the HStoreField branch comes "after the ArrayField branch, before the SCALAR_MAP walk"). Verbatim shape per Decision 5 (spec lines 555-571):
   ```python
   if _HSTORE_FIELD_CLS is not None and isinstance(field, _HSTORE_FIELD_CLS):
       if field.choices:
           raise ConfigurationError(
               f"HStoreField on {field.model.__name__}.{field.name} declares choices; "
               f"HStore stores a dict[str, str | None] with no enum-able shape at the "
               f"GraphQL boundary. Drop the choices declaration or model the constrained "
               f"shape with a separate field.",
           )
       py_type = strawberry.scalars.JSON
       return py_type | None if field.null else py_type
   ```
   Key contract points (Decision 5):
   - The outer guard `_HSTORE_FIELD_CLS is not None and isinstance(field, _HSTORE_FIELD_CLS)` is the single-line short-circuit per spec line 556. **No redundant inner `_HSTORE_FIELD_CLS is not None` check** (mirrors Slice 3's outer-guard shape, which dropped the redundant inner check in revision 6 per the spec history).
   - **Outer `choices` rejection's error message must name the `dict[str, str | None]` shape and the consumer recourse hint ("Drop the choices declaration or model the constrained shape with a separate field")** per spec lines 563-568. The exact wording is spec-pinned; do not paraphrase the rationale or the recourse hint.
   - **No recursion into `base_field`** — unlike the ArrayField branch, HStoreField has no inner-field concept. The branch returns `strawberry.scalars.JSON` directly with optional `| None` widening.
   - The early-return widening `return py_type | None if field.null else py_type` uses Python 3.10+ `|`-style union (per spec Risks line 824). This **does not** call `convert_scalar`'s existing tail `if field.null: py_type = py_type | None` branch (the function returns early); the branch must handle outer-null widening itself.
   - **DRY claim about the outer-null widening duplicating the tail `if field.null` branch.** This duplication is intentional and matches Slice 3's ArrayField branch posture (per Slice 3's plan step 3 / line 84): the early-return branch must compute the `JSON` return type and widen before the MRO walk reaches it; there is no clean way to fall through to the tail without the MRO walk re-running on the field. Two lines duplicated across two sentinel branches; not a DRY violation worth a helper. Worker 3 should not flag this.

4. **Rewrite `convert_scalar`'s docstring** to cover both sentinel branches plus the MRO walk plus the choice-substitution / null-widening tail. The current docstring at `converters.py:86-110` covers the MRO walk and choice/null tail; the ArrayField branch (Slice 3) was added without a docstring update — Worker 3's Slice 3 review flagged this as a Low finding and deferred the rewrite to Slice 4 (per Slice 3's final-verification carry-forward, worker-memory dated 2026-05-17). The Slice 4 rewrite is amortized across both sentinel branches in a single edit.

   The rewrite must:
   - Restructure the `Algorithm:` enumeration to mention the pre-MRO sentinel branches **first** (ArrayField + HStoreField, in declaration order), then the MRO walk, then the choice substitution, then the null widening. Suggested phrasing for the new bullet:
     > "0. If the field is a sentinel-guarded postgres type (`ArrayField` / `HStoreField`), dispatch to the matching branch and return early. `ArrayField` rejects nested arrays and outer `choices`, then recurses on `base_field` and wraps in `list[inner]`. `HStoreField` rejects outer `choices`, then returns `strawberry.scalars.JSON`."
   - Extend the `Raises:` entry to enumerate all four `ConfigurationError` triggers (the existing two — `Unsupported Django field type` and the grouped-choices form raised by `convert_choices_to_enum` — plus the three new ones added by Slices 3 and 4):
     - `Unsupported Django field type` (no class in `type(field).__mro__` is in `SCALAR_MAP`).
     - `Nested ArrayField on ...` (from Slice 3's ArrayField branch).
     - `ArrayField on ... declares choices on the outer field` (from Slice 3's ArrayField branch).
     - `HStoreField on ... declares choices` (from Slice 4's HStoreField branch).
     - `<Model>.<field> uses Django's grouped-choices form` (raised from `convert_choices_to_enum` per the existing wording at `converters.py:107-109`).
   - Keep the existing `Args:` section unchanged (the `field` and `type_name` parameter contracts are unaffected).
   - Keep the existing "Order matters" paragraph (it still applies to the choice-vs-null tail).

   Implementer's discretion on the exact wording of the new bullet and the `Raises:` list; the requirement is that the docstring accurately describes the post-Slice-4 behavior. Worker 3's review should verify the docstring lists all four new triggers and mentions the sentinel branches.

5. **Remove the `HStoreField` TODO comment** at `converters.py:33-35` (the 3-line block per the shadow comment inventory). After this removal, the file should have **no `# TODO(future):` comments tracking deferred scalar conversions** — Slice 2 already dropped the JSONField half of the original two-half TODO; Slice 4 drops the remaining HStoreField half. Verify against the shadow's comment inventory after the edit. The Slice 6 documentation work depends on this — the spec's Definition of done (line 845) gates on "All TODO comments for deferred scalars removed."

6. **No new imports** in `converters.py`. `ConfigurationError` is already imported (`converters.py:26`), `models` is already imported (`converters.py:24`), `strawberry` is already imported (`converters.py:23`) for the `strawberry.scalars.JSON` attribute access, `Any` is already imported (`converters.py:21`) for the `_HSTORE_FIELD_CLS` annotation. The new sentinel branch references `_HSTORE_FIELD_CLS` (module-local) and `field.model` / `field.name` / `field.choices` / `field.null` (attributes Django provides on a real `HStoreField`; `_FakeHStoreField` inherits them from `models.Field` via `contribute_to_class`).

7. **Verify (in Worker 2's diff and Worker 3's review) that no other line in `converters.py` is touched.** Slice 4 contract:
   - +1 helper function (`_resolve_hstore_field`)
   - +1 module-level sentinel assignment (`_HSTORE_FIELD_CLS`)
   - +1 new branch inside `convert_scalar`'s body (the HStoreField sentinel branch)
   - Updated `convert_scalar` docstring (Algorithm + Raises sections amortized across both sentinel branches)
   - −1 TODO comment block (the HStoreField TODO at lines 33-35)
   - No changes to `SCALAR_MAP`, `_resolve_array_field`, `_ARRAY_FIELD_CLS`, the ArrayField branch body, `convert_choices_to_enum`, `_sanitize_member_name`, `resolved_relation_annotation`, or `convert_relation`.

8. **Add the `_FakeHStoreField` test double to `tests/types/test_converters.py`**. Place it at module scope **immediately after `_FakeArrayField`** at the current `tests/types/test_converters.py:450-466` so the two test doubles sit adjacent in the test-helper region. Verbatim per Decision 7 (spec lines 622-630):
   ```python
   class _FakeHStoreField(models.Field):
       """Test double for HStoreField that does not require django.contrib.postgres.

       Tests must call
       monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)
       before declaring a DjangoType using this field; otherwise convert_scalar's
       HStore branch never dispatches.
       """

       pass
   ```
   Implementer's discretion: the trailing `pass` on its own line is the spec-pinned shape; Worker 2 may write the class body as `pass` on the same line as the docstring's closing if the class is empty enough that the docstring alone satisfies Python's class-body requirement (i.e. the docstring counts as the body). Both shapes are equivalent at runtime; the spec-pinned form is the docstring-followed-by-`pass` shape.

9. **Add a section banner comment** marking the start of the Slice-4 test region. Place it after the existing ArrayField section (which ends at `tests/types/test_converters.py:1176`) and before the new tests. Suggested wording (parallel to the BigInt section at lines 409-418, the JSONField section at lines 722-732, and the ArrayField section at lines 827-836):
   ```python
   # ---------------------------------------------------------------------------
   # HStoreField -> strawberry.scalars.JSON sentinel-guarded branch (Slice 4)
   #
   # Synthetic models live under ``app_label = "test_hstorefield"`` so they do
   # not collide with the prior synthetic apps (``test_bigint``,
   # ``test_jsonfield``, ``test_arrayfield``, ``test_choice_enums``). Sentinel-
   # branch tests monkey-patch
   # ``converters._HSTORE_FIELD_CLS = _FakeHStoreField`` BEFORE declaring the
   # ``DjangoType`` (Decision 7 spec line 635). Helper-resolver tests use
   # ``sys.modules`` manipulation per Decision 7 spec lines 661-676.
   # ---------------------------------------------------------------------------
   ```

10. **Write the 8 Slice-4 tests in `tests/types/test_converters.py`** per the spec checklist (spec lines 177-187). Order suggestion: helper-resolver tests first (no `DjangoType` declaration; easiest to read), then sentinel-branch tests in the order the spec lists them. Each sentinel-branch test follows the in-function pattern (spec lines 648-657):

    **Helper-resolver coverage** (spec lines 178-179):
    - `test_resolve_hstore_field_returns_class_when_postgres_fields_importable(monkeypatch)` — mirror Slice 3's helper-resolver test at `tests/types/test_converters.py:839-851`. Shape:
      ```python
      import sys
      import types as _types
      fake = _types.ModuleType("django.contrib.postgres.fields")
      fake.HStoreField = _FakeHStoreField
      monkeypatch.setitem(sys.modules, "django.contrib.postgres.fields", fake)
      from django_strawberry_framework.types.converters import _resolve_hstore_field
      assert _resolve_hstore_field() is _FakeHStoreField
      ```
    - `test_resolve_hstore_field_returns_none_when_postgres_fields_unimportable(monkeypatch)` — mirror Slice 3's helper-resolver test at `tests/types/test_converters.py:854-864`. Shape:
      ```python
      import sys
      monkeypatch.setitem(sys.modules, "django.contrib.postgres.fields", None)
      from django_strawberry_framework.types.converters import _resolve_hstore_field
      assert _resolve_hstore_field() is None
      ```
      `sys.modules[name] = None` forces the next `import name` to raise `ImportError` (spec Risks line 825).

    **Sentinel-branch coverage** (spec lines 181-186):
    - `test_hstore_field_maps_to_json_scalar_via_fake_sentinel(monkeypatch)` — declare `HStoreOwner(models.Model)` with `data = _FakeHStoreField()`; monkey-patch `converters._HSTORE_FIELD_CLS = _FakeHStoreField`; declare `DjangoType`; `finalize_django_types()`; build schema; introspect `data` field; assert top-level kind is `NON_NULL` and the inner SCALAR is `{"name": "JSON"}`. **Mirror Slice 2's `test_json_field_maps_to_json_scalar_in_schema` introspection shape** (`tests/types/test_converters.py:735-764`) — the introspection chain is identical (`NON_NULL → SCALAR { name: "JSON" }`).
    - `test_hstore_field_nullable_via_fake_sentinel(monkeypatch)` — `_FakeHStoreField(null=True)`; assert top-level kind is `SCALAR` (no `NON_NULL` wrapper) and the name is `"JSON"`. Mirror Slice 2's `test_json_field_nullable_in_schema` at `tests/types/test_converters.py:767-793`. Pins the outer-null widening branch (`py_type | None if field.null else py_type`).
    - `test_hstore_field_resolver_dict_serializes_via_schema_execution(monkeypatch)` — resolver returns a hand-built dict (`{"k1": "v1"}`); assert `schema.execute_sync` round-trips the dict verbatim through the `JSON` scalar. Test name **clarifies this is a serializer-level test** (no DB persistence — SQLite cannot store HStore values; the test exercises the scalar's wire-level serialization through Strawberry). Spec line 183 pins the test name and rationale.
    - `test_hstore_field_resolver_dict_with_none_value_via_schema_execution(monkeypatch)` — resolver returns `{"k1": "v", "k2": None}`; assert `schema.execute_sync` preserves the `None` value inside the dict. Pins that the `strawberry.scalars.JSON` scalar accepts `None` values inside the dict, mirroring `HStoreField`'s native `dict[str, str | None]` shape. Spec line 184 pins the test name and rationale.
    - `test_hstore_field_outer_choices_rejected_via_fake_sentinel(monkeypatch)` — `_FakeHStoreField(choices=[("a", "A")])`; assert `pytest.raises(ConfigurationError, match="declares choices")` during `DjangoType` declaration (the rejection fires inside `convert_scalar` at type-creation time). The `match=` substring is `"declares choices"` (broader than `"declares choices on the outer"` which is the ArrayField-specific wording) so the test matches the HStoreField message at spec lines 563-564 (`f"HStoreField on {...} declares choices; ..."`). Spec line 185 + H1 fix line 28 pin this test.
    - `test_hstore_field_sentinel_none_path(monkeypatch)` — monkey-patch `converters._HSTORE_FIELD_CLS = None`; declare a `DjangoType` with a `_FakeHStoreField` instance; assert `pytest.raises(ConfigurationError, match="Unsupported Django field type")` during `DjangoType` declaration. Pins the short-circuit guard: with `_HSTORE_FIELD_CLS = None`, the guard short-circuits (`None is not None` → False) and the field falls through to the MRO walk, which raises the unsupported-field error (because `_FakeHStoreField` is not in `SCALAR_MAP`). Mirror Slice 3's `test_array_field_sentinel_none_path` at `tests/types/test_converters.py:1118-1139`. **Without this test**, a future refactor that flipped the guard's `not None` check could break silently.

    **Optional gated test** (spec line 187):
    - `test_real_hstore_field_compatible_with_strawberry` — use `pytest.importorskip("django.contrib.postgres.fields")` at the top of the test; declare a `DjangoType` with `HStoreField()` on a `managed = False` model; call `finalize_django_types()`; introspect the schema via `__type`; walk the introspection `kind / ofType` chain explicitly per spec line 187; assert the chain is `NON_NULL → SCALAR { name: "JSON" }`. **AND** exercise a resolver returning `{"k1": "v", "k2": None}` via `schema.execute_sync`; assert the dict shape (including the `None` value) is preserved in the response. **No sentinel monkey-patch** — this test exercises the live `_HSTORE_FIELD_CLS` value (which is the real `HStoreField` class on a postgres-equipped env, or `None` on a dev env where `importorskip` skips the test). The test confirms the sentinel-branch code path works end-to-end against Django's real `HStoreField` when postgres-contrib is available. Mirror Slice 3's `test_real_array_field_compatible_with_strawberry` at `tests/types/test_converters.py:1142-1176`.

11. **Verify (in Worker 2's diff and Worker 3's review) that no source-tree file outside `django_strawberry_framework/types/converters.py` and `tests/types/test_converters.py` is touched.** Specifically, **do not** modify:
    - `django_strawberry_framework/__init__.py` (no new public symbol in Slice 4)
    - `tests/base/test_init.py` (no `__all__` change)
    - `django_strawberry_framework/scalars.py` (Slice 1 territory)
    - `examples/fakeshop/...` (no example-app integration in Slice 4; the spec defers fakeshop integration to Slice 6's `TODAY.md` text edits, not a code change)
    - `CHANGELOG.md` (Slice 6 territory)
    - `docs/FEATURES.md` (Slice 6 territory)
    - Slice 3's ArrayField branch at `converters.py:117-130` (Slice 3 anchor; do not refactor "while here")
    - `_resolve_array_field` at `converters.py:69-79` and `_ARRAY_FIELD_CLS` at `converters.py:82` (Slice 3 anchors)

### Test additions / updates

All 6 sentinel-branch tests + 2 helper-resolver tests + 1 optional gated test = **8 mandatory tests + 1 optional gated test** appended after the existing ArrayField section (currently ending at `tests/types/test_converters.py:1176`). Categories:

- **Helper-resolver coverage** (2 tests): `sys.modules`-patch shape per Decision 7 example (spec lines 661-676). Assertion shapes: `_resolve_hstore_field() is _FakeHStoreField` (positive) / `_resolve_hstore_field() is None` (negative). No `DjangoType` declaration; no schema build. Mirrors Slice 3's helper-resolver tests at `tests/types/test_converters.py:839-864` with the helper / sentinel / class identifiers swapped.

- **Sentinel-branch coverage** (6 tests): in-function model + `monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)` + `DjangoType` + `finalize_django_types()` + schema build + introspection assertion (or `pytest.raises` for the rejection test, or `execute_sync` assertion for the resolver tests). Assertion shapes:
  - **Shape introspection tests** (2 tests: `_maps_to_json_scalar`, `_nullable`): reuse `_introspect_field_type` / `_walk_introspected_type`; assert on the wrapping-level shape (`NON_NULL → SCALAR { name: "JSON" }` for the non-null case; `SCALAR { name: "JSON" }` for the null case). The depth-2 introspection chain is identical to Slice 2's JSONField cases — the helpers handle it unchanged.
  - **Resolver-execution tests** (2 tests: `_resolver_dict_serializes`, `_resolver_dict_with_none_value`): `schema.execute_sync("{ owner { data } }")`; assert `result.errors is None` and `result.data` matches the hand-built dict verbatim. Mirror Slice 2's `test_json_field_round_trips_dict_via_schema_execution` at `tests/types/test_converters.py:796-824`. The `_with_none_value` variant pins that `None` survives inside the dict (`{"k1": "v", "k2": None}`).
  - **Rejection test** (1 test: `_outer_choices_rejected`): `pytest.raises(ConfigurationError, match="declares choices")` during `DjangoType` declaration. Use the broader substring (`"declares choices"`) to match the HStoreField-specific wording at spec lines 563-564.
  - **Sentinel-none path** (1 test: `_sentinel_none_path`): monkey-patch `_HSTORE_FIELD_CLS = None`; `pytest.raises(ConfigurationError, match="Unsupported Django field type")` — pins the short-circuit guard. Mirror Slice 3's `test_array_field_sentinel_none_path`.

- **Optional gated test** (1 test): `pytest.importorskip("django.contrib.postgres.fields")` at the top; the dev env skips this test (no postgres driver); CI with postgres-contrib available runs it. The test exercises **both** schema introspection (`NON_NULL → SCALAR { name: "JSON" }`) **AND** resolver execution (`{"k1": "v", "k2": None}` round-trip via `schema.execute_sync`) — spec line 187 pins both assertion shapes. Pins the live-`HStoreField` compatibility contract.

- **No changes to `tests/test_scalars.py`** — that file is `BigInt`-specific; `HStoreField` has no scalar wire-format concern (it's an annotation transformer that returns `strawberry.scalars.JSON` directly, not a scalar definition).

- **No changes to `tests/base/test_init.py`** — Slice 4 adds no public symbol. The `__all__` set stays exactly the same as after Slice 1.

- **No temp/scratch tests anticipated.** The 8 spec-named tests + 1 optional gated test are permanent. Worker 3 may probe with temp tests under `docs/builder/temp-tests/slice-4-hstorefield/` if the sentinel-branch dispatch surfaces an unexpected behavior (e.g., a Strawberry version that handles `dict[str, Any]` through `JSON` differently), but no temp tests are pre-flagged here.

### Implementation discretion items

Items where Worker 1 has assessed the design and decided the choice is at Worker 2's discretion:

- **Docstring on `_resolve_hstore_field`.** One-or-two-sentence docstring anchoring the helper's responsibility ("Soft-import postgres `HStoreField`; returns `None` if `django.contrib.postgres.fields` is unavailable"). Exact wording is at Worker 2's discretion; the parallel posture with `_resolve_array_field`'s docstring at `converters.py:70-74` is the intent.

- **Body shape of `_FakeHStoreField`.** The spec-pinned form is docstring + `pass`. Worker 2 may instead write just the docstring (which counts as a valid class body in Python) without an explicit `pass`. Both are equivalent at runtime. The spec-pinned form is the docstring-followed-by-`pass` shape; mention either is acceptable.

- **Exact wording of the new `Algorithm:` bullet in the `convert_scalar` docstring.** The requirement is that the docstring accurately describes the post-Slice-4 behavior (pre-MRO sentinel branches, MRO walk, choice substitution, null widening). Worker 2 may phrase the new bullet (suggested wording in step 4 above) however reads cleanly; the suggested phrasing is a starting point, not a verbatim contract.

- **Test order inside the Slice-4 section.** The spec's checklist order (helper-resolver coverage → sentinel-branch coverage → optional gated test) is the suggested order. Worker 2 may interleave the resolver-execution tests adjacent to the introspection tests if that reads more cleanly (e.g., `_maps_to_json_scalar → _nullable → _resolver_dict_serializes → _resolver_dict_with_none_value → _outer_choices_rejected → _sentinel_none_path`). The spec-pinned constraint is that all 6 sentinel-branch tests + 2 helper-resolver tests + 1 optional gated test exist.

- **The `app_label` literal.** Slice 4's tests use `app_label = "test_hstorefield"`. Worker 2 may use a different suffix (e.g., `"test_hstore"`) if it reads more cleanly; the only constraint is uniqueness against the prior synthetic apps (`"test_bigint"`, `"test_jsonfield"`, `"test_arrayfield"`, `"test_choice_enums"`).

- **Where to place the `_FakeHStoreField` test double in the file.** The suggested placement is immediately after `_FakeArrayField` at `tests/types/test_converters.py:450-466`. Worker 2 may place it at the start of the Slice-4 section banner instead (after the banner comment) if that reads more cleanly to a reviewer scanning the file top-to-bottom. Either placement is acceptable; the constraint is that the class is at module scope (so all Slice-4 tests can reference it).

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/converters.py` — Removed the 3-line `# TODO(future):` block for HStoreField (originally at lines 33-35). Added `_resolve_hstore_field()` helper immediately after `_resolve_array_field()`. Added module-level sentinel `_HSTORE_FIELD_CLS: type[models.Field] | None = _resolve_hstore_field()` immediately after the `_ARRAY_FIELD_CLS` assignment. Inserted the new HStoreField sentinel branch inside `convert_scalar` immediately after the ArrayField branch and before the MRO walk; outer-`choices` rejection raises `ConfigurationError` with the spec-pinned message; otherwise returns `strawberry.scalars.JSON`, widened to `JSON | None` when `field.null`. Rewrote the `convert_scalar` docstring to enumerate both sentinel branches in the new `Algorithm` step 0 and to enumerate all five `ConfigurationError` triggers under `Raises`.
- `tests/types/test_converters.py` — Added `_FakeHStoreField(models.Field)` test double immediately after `_FakeArrayField`. Appended the Slice-4 section banner and the 8 mandatory tests + 1 optional gated test at the end of the file.

### Tests added or updated

- `tests/types/test_converters.py::test_resolve_hstore_field_returns_class_when_postgres_fields_importable` — pins the positive branch of `_resolve_hstore_field()` via `sys.modules`-injected fake module exposing `HStoreField = _FakeHStoreField`.
- `tests/types/test_converters.py::test_resolve_hstore_field_returns_none_when_postgres_fields_unimportable` — pins the negative branch via `sys.modules[name] = None` forcing `ImportError`.
- `tests/types/test_converters.py::test_hstore_field_maps_to_json_scalar_via_fake_sentinel` — pins schema shape `NON_NULL → SCALAR { name: "JSON" }` via introspection.
- `tests/types/test_converters.py::test_hstore_field_nullable_via_fake_sentinel` — pins the outer-null widening branch (`py_type | None if field.null else py_type`); top-level kind is `SCALAR` (no `NON_NULL` wrapper).
- `tests/types/test_converters.py::test_hstore_field_resolver_dict_serializes_via_schema_execution` — pins serializer-level dict round-trip through the `JSON` scalar.
- `tests/types/test_converters.py::test_hstore_field_resolver_dict_with_none_value_via_schema_execution` — pins `{"k1": "v", "k2": None}` round-trip including the `None` value.
- `tests/types/test_converters.py::test_hstore_field_outer_choices_rejected_via_fake_sentinel` — pins `pytest.raises(ConfigurationError, match="declares choices")` at `DjangoType` declaration time.
- `tests/types/test_converters.py::test_hstore_field_sentinel_none_path` — pins the short-circuit `_HSTORE_FIELD_CLS is not None` guard; with the sentinel patched to `None`, the field falls through to the MRO walk's unsupported-field error.
- `tests/types/test_converters.py::test_real_hstore_field_compatible_with_strawberry` — optional gated test via `pytest.importorskip("django.contrib.postgres.fields")`; asserts both schema-introspection chain and `{"k1": "v", "k2": None}` resolver round-trip on a postgres-equipped env.

### Validation run

- `uv run ruff format .` — pass (99 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed).
- No focused `pytest` runs; the artifact does not require any.

### Implementation notes

- **Test order inside the Slice-4 section.** Followed the planner's explicitly-suggested interleaving (`_maps_to_json_scalar → _nullable → _resolver_dict_serializes → _resolver_dict_with_none_value → _outer_choices_rejected → _sentinel_none_path`), placing the helper-resolver tests first, then the sentinel-branch tests in shape → resolver → rejection → none-path order. The plan called this out as Worker 2's discretion.
- **`_FakeHStoreField` body shape.** Used the spec-pinned docstring-followed-by-`pass` form (mirrors the spec block at lines 622-630 verbatim). The `pass` is redundant once the docstring is present, but the spec-pinned form is the more explicit shape.
- **`_FakeHStoreField` placement.** Placed immediately after `_FakeArrayField` in the test-double region (Worker 1 listed both placements as acceptable). Keeps the two fakes lexically adjacent for maintainers scanning the helpers.
- **`app_label` literal.** Used `"test_hstorefield"` per the plan's suggested suffix; uniqueness against the prior synthetic apps (`test_bigint`, `test_jsonfield`, `test_arrayfield`, `test_choice_enums`) confirmed by `grep`.
- **`convert_scalar` docstring `Raises:` enumeration shape.** Used a nested-bullet list under the single `ConfigurationError` entry so the five distinct trigger phrasings each have their own bullet — easier to scan than a comma-joined run-on. Worker 1's plan called the exact wording Worker 2's discretion; the requirement was completeness, which the nested-bullet form satisfies cleanly.
- **HStoreField branch placement.** Placed immediately after the ArrayField branch and before the MRO walk, per Decision 5 (spec lines 552-555). The two sentinel branches now sit adjacent in source order, mirroring their adjacent declarations as helpers and sentinels above.

### Notes for Worker 3

- No shadow file used during implementation — the diff is small enough to reason about against the post-Slice-3 source directly.
- Both sentinel branches now share an `outer-guard + outer-choices-rejection + early-return-with-null-widen` posture. The ArrayField branch additionally has a `nested-array rejection` and a recursive `inner = convert_scalar(...)` call; the HStoreField branch has neither (Decision 5 returns `strawberry.scalars.JSON` directly). The structural parallel-but-different posture is deliberate per the plan.
- The Slice-4 tests reuse `_introspect_field_type` / `_walk_introspected_type` unchanged. The depth-2 introspection chain (`NON_NULL → SCALAR` and bare `SCALAR`) sits well within the helper's 4-level walk.
- The TODO comment removal restores `converters.py`'s comment inventory to no `# TODO(future):` blocks tracking deferred scalar conversions. Slice 6's Definition-of-done item ("All TODO comments for deferred scalars removed") is now satisfied at the source level.

### Notes for Worker 1 (spec reconciliation)

No spec gaps or conflicts surfaced during implementation. The plan and Decision 5 / Decision 7 carried Slice 4 cleanly without drift.

---

## Review (Worker 3)

Static helper was re-run on both files per the BUILD.md rules (`types/` modification + tests file gained ~265 lines of new logic, above the 50-line threshold). Shadow overviews at `docs/builder/shadow/django_strawberry_framework__types__converters.overview.md` and `docs/builder/shadow/tests__types__test_converters.overview.md` were used for control-flow-hotspot and repeated-literal triage. Original source line numbers cited throughout.

### High:

None.

### Medium:

None.

### Low:

None.

### DRY findings

- **`_resolve_array_field` / `_resolve_hstore_field` near-twin pair** (`django_strawberry_framework/types/converters.py:65-75` vs. `78-88`). The two helpers differ in exactly one identifier (`ArrayField` ⇄ `HStoreField`) plus the docstring symbol name; their bodies are otherwise identical. Spec Decision 4 (spec lines 525-548) pins both helpers as parallel single-purpose functions, and the integration pass owns cross-slice consolidation. Recorded here per the task brief; **not flagged as a Slice-4 finding**. Worker 1's integration pass should weigh a factory shape (`_resolve_postgres_field(name: str)`) against the cost of an indirection that breaks IDE go-to-definition.

- **`_ARRAY_FIELD_CLS` / `_HSTORE_FIELD_CLS` adjacent module-level sentinel pair** (`converters.py:91-92`). Same annotation (`type[models.Field] | None`), same assignment shape, read by different branches with different post-isinstance bodies. The shadow's `Repeated string literals` section confirms `_ARRAY_FIELD_CLS` appears 9x and `_HSTORE_FIELD_CLS` 6x in `test_converters.py` (only — converters.py itself reads each name twice: assignment site + guard site). Spec Decision 4 commits to two named sentinels per branch contract; the named contract is load-bearing in `convert_scalar`. Not a DRY finding at the slice level; called out here for the integration pass's visibility.

- **Parallel-but-different `convert_scalar` branch shape** (`converters.py:147-160` ArrayField vs. `165-174` HStoreField). Both branches share the outer-guard posture (`if _<NAME>_FIELD_CLS is not None and isinstance(field, _<NAME>_FIELD_CLS):`), the outer-`choices` rejection that raises `ConfigurationError` naming `field.model.__name__` + `field.name`, and the `return py_type | None if field.null else py_type` outer-null widening. Post-`choices`-check bodies diverge: ArrayField additionally rejects nested arrays then recurses on `base_field` and wraps in `list[inner]`; HStoreField returns `strawberry.scalars.JSON` directly. The structural parallel is deliberate per spec Decision 5 ("mirrors Decision 2's shape", spec lines 552-571). A shared `_handle_postgres_field(field, type_name)` dispatcher would force conditional sub-branches inside a single body and lose the inline readability. The build's "DRY violation that will entrench duplicated logic" trigger does **not** apply here — the divergence is real and the two branches are short enough (≤14 lines each) to read top-to-bottom without indirection. **Defer-to-integration-pass per the spec's posture; not flagged at the slice level**.

- **Cross-branch `ConfigurationError` message template** (`converters.py:149-151, 153-157, 167-172`). All three rejection messages name `field.model.__name__` + `field.name` and follow `<FieldType> on <Model>.<Field> <verb-phrase>; <rationale>; <recourse>`. The HStoreField message is verbatim from spec lines 563-568 and the ArrayField message is verbatim from spec lines 503-511 — neither has slice-level discretion. The integration pass may evaluate whether a shared format-string constant (e.g., `_OUTER_CHOICES_REJECTION_TEMPLATE`) is worth introducing once both sites exist; the gain would be one shared template against the cost of additional indirection and the loss of the spec-pinned verbatim phrasing at each call site. **Defer-to-integration-pass; not flagged at the slice level**.

- **`_FakeHStoreField` vs. `_FakeArrayField` test doubles** (`tests/types/test_converters.py:450-466` vs. `469-478`). Two structurally different classes — `_FakeArrayField` has `__init__(self, base_field, **kwargs)` plus `contribute_to_class` overrides for metadata propagation (the ArrayField branch's recursive `convert_scalar(base_field, ...)` call needs `base_field.model` and `base_field.name`); `_FakeHStoreField` is a bare `pass` body because the HStoreField branch never recurses. A shared base class would force `_FakeHStoreField` to inherit an `__init__(self, base_field, **kwargs)` it does not want. The two doubles are spec-pinned per Decision 7 lines 622-630 verbatim. **Not a DRY violation**.

- **`app_label = "test_hstorefield"` literal repeated 7x** in Slice 4 tests (shadow `Repeated string literals` section). Combined with `"test_arrayfield"` (10x), `"test_jsonfield"` (3x), `"test_bigint"` (5x), and `"test_choice_enums"` (4x), the total post-Slice-4 `app_label` literal count is **29** across `tests/types/test_converters.py`. The Slice 3 carry-forward flagged ~25 as the threshold for reassessing a module-level constants block. **Defer-to-integration-pass**, not a Slice-4 finding — Slice 4 follows the spec-pinned in-function-model + unique-`app_label`-per-slice pattern per Decision 7 lines 641-646.

- **Test-fixture trio scaffold repetition.** Each of the 6 sentinel-branch tests pairs (a) `monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)`, (b) a synthetic model declaration, (c) a `DjangoType` declaration, (d) `finalize_django_types()`, (e) a `Query` + `schema.execute_sync(...)` or introspection assertion. The shadow's `Symbols` section shows ~24 `class Meta` symbols and ~17 `def owner(self)` symbols across the file post-Slice-4. The Slice 1 / Slice 3 deferred `_make_one_field_schema(...)` helper-extraction watchpoint stays open at ~24 sites. **Defer-to-integration-pass**, not a Slice-4 finding — Slice 4 is the last spec slice that mutates `tests/types/test_converters.py`, so the integration pass has full parameter-surface visibility (monkeypatch-sentinel-or-none + payload-variety + introspection-or-execute-sync). The duplication is intentional at this stage; each test reads top-to-bottom without indirection.

- **Outer-null widening duplicated across ArrayField + HStoreField branches** (`converters.py:160, 174`). Both branches end with `return <result> | None if field.null else <result>`. Two lines duplicated across two adjacent branches; the tail `if field.null: py_type = py_type | None` at the MRO walk's exit (line 194) is structurally identical but unreachable from either sentinel branch (early return). Extracting a `_maybe_widen(py_type, field)` helper would replace two two-line returns with one one-line return each — net savings are negligible against the cost of an extra named function. **Intentional duplication per the spec's posture; not flagged**.

### Public-surface check

Slice 4 does **not** modify `django_strawberry_framework/__init__.py`. Confirmed by inspection: the working-tree `git diff -- django_strawberry_framework/__init__.py` shows only the Slice-1 baseline (BigInt added to `__all__` and the `from .scalars import BigInt` re-export); no further additions or removals. Spec line 172 explicitly says "**Do not** add `HStoreField` to `SCALAR_MAP`" and there is no public symbol for HStoreField at any tier — the sentinel-guarded branch in `convert_scalar` returns `strawberry.scalars.JSON` (a third-party symbol) and the helper / sentinel pair (`_resolve_hstore_field`, `_HSTORE_FIELD_CLS`) are module-private (leading-underscore). The `__all__` tuple stays exactly as Slice 1 set it. No new public export, no spec-authorized export change.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces.

### What looks solid

- **Decision 5 verbatim adherence.** Walked the diff: the new HStoreField branch at `converters.py:165-174` is character-for-character the spec block at lines 555-571 (with the implementation's preferred trailing-comma layout the only non-semantic difference). Order is correct: outer guard → outer `choices` rejection → `py_type = strawberry.scalars.JSON` → `return py_type | None if field.null else py_type`. Placement is correct per spec lines 552-555 — branch sits immediately after the ArrayField branch and before the MRO walk (`converters.py:175-191`). The `ConfigurationError` message body names `field.model.__name__` + `field.name`, the `dict[str, str | None]` rationale, and the consumer recourse hint ("Drop the choices declaration or model the constrained shape with a separate field"), all spec-pinned at lines 563-568.

- **Decision 4 sentinel pattern matches exactly.** `_resolve_hstore_field()` at `converters.py:78-88` is structurally identical to `_resolve_array_field()` at `65-75`. Module-level sentinel `_HSTORE_FIELD_CLS: type[models.Field] | None = _resolve_hstore_field()` lands at `converters.py:92`, adjacent to `_ARRAY_FIELD_CLS` at `91`. The guard `_HSTORE_FIELD_CLS is not None and isinstance(field, _HSTORE_FIELD_CLS)` at `converters.py:165` matches the spec block at line 556 verbatim. No redundant inner `_HSTORE_FIELD_CLS is not None` check inside the body.

- **HStoreField is NOT in `SCALAR_MAP`.** Confirmed by walking `converters.py:33-62` — the dispatch table has 26 entries, none of them `models.HStoreField`. The branch lives entirely inside `convert_scalar`'s sentinel-guarded prologue per spec line 172.

- **Test fixture monkeypatch ordering is correct in every sentinel-branch test.** Walked all 6 sentinel-branch tests: `test_hstore_field_maps_to_json_scalar_via_fake_sentinel` (test_converters.py:1234), `test_hstore_field_nullable_via_fake_sentinel` (`:1267`), `test_hstore_field_resolver_dict_serializes_via_schema_execution` (`:1302`), `test_hstore_field_resolver_dict_with_none_value_via_schema_execution` (`:1337`), `test_hstore_field_outer_choices_rejected_via_fake_sentinel` (`:1373`), and `test_hstore_field_sentinel_none_path` (`:1397`). Each test's **first executable statement** is `monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", <value>)` BEFORE the Model class declaration, BEFORE the `DjangoType` declaration, and BEFORE `finalize_django_types()`. Matches the spec's load-bearing test discipline at line 635.

- **`_FakeHStoreField` is a pass-through `models.Field` subclass.** `tests/types/test_converters.py:469-478` is exactly the spec-pinned shape from Decision 7 lines 622-630: subclasses `models.Field`, docstring + bare `pass` body, no `__init__` override, no `contribute_to_class` override, no metadata-propagation contract. Django's default `models.Field.__init__` and `contribute_to_class` handle `null=`, `choices=`, and `name`/`model` attribute propagation — confirmed by reading `test_hstore_field_outer_choices_rejected_via_fake_sentinel` (`tests/types/test_converters.py:1376` reads `_FakeHStoreField(choices=[("a", "A")])` and the inner Model declaration propagates `field.model` + `field.name` for the `ConfigurationError` message to format `f"HStoreField on {field.model.__name__}.{field.name}"` correctly).

- **`convert_scalar` docstring rewrite is complete and accurate.** Walked the docstring at `converters.py:96-140`. (a) The Algorithm enumeration now starts at step 0 (the pre-MRO sentinel branches), mentions both ArrayField + HStoreField in declaration order, and correctly characterizes each branch's behavior (ArrayField: nested-array rejection + outer-choices rejection + recursion + `list[inner]` wrap + outer-null widening; HStoreField: outer-choices rejection + `strawberry.scalars.JSON` return + outer-null widening). (b) The Raises section enumerates all five `ConfigurationError` trigger phrasings as nested bullets under a single `ConfigurationError:` entry: `Unsupported Django field type`, `Nested ArrayField on ...`, `ArrayField on ... declares choices on the outer field`, `HStoreField on ... declares choices`, and `<Model>.<field> uses Django's grouped-choices form`. (c) The Args section and the "Order matters" paragraph are preserved unchanged from pre-Slice-4. The Slice-3 deferred-Low docstring drift is now fully reconciled.

- **`test_hstore_field_resolver_dict_with_none_value_via_schema_execution` exercises the `{"k1": "v", "k2": None}` round-trip via `schema.execute_sync`.** `tests/types/test_converters.py:1332-1364` declares `payload = {"k1": "v", "k2": None}` (line 1353), builds the schema, calls `schema.execute_sync("{ owner { data } }")` (line 1362), asserts `result.errors is None` (line 1363), and asserts `result.data == {"owner": {"data": payload}}` (line 1364). The dict-shape assertion is on the full payload including the `None` value — spec Decision 5 + Decision 7 / Test plan item 18 (spec line 184) satisfied. The `_real_hstore_field_compatible_with_strawberry` gated test at `:1414-1455` mirrors the assertion for the live-postgres path (lines 1437, 1453-1455).

- **HStoreField outer-choices rejection is loud + actionable, mirroring ArrayField's posture.** Walked both messages: ArrayField at `converters.py:153-157` reads `"ArrayField on {Model}.{field} declares choices on the outer field; outer-array choices are ambiguous at the GraphQL boundary. Declare choices on base_field for element-level enum, or use FilterSet."`; HStoreField at `:167-172` reads `"HStoreField on {Model}.{field} declares choices; HStore stores a dict[str, str | None] with no enum-able shape at the GraphQL boundary. Drop the choices declaration or model the constrained shape with a separate field."`. Both name the model + field, the GraphQL-boundary rationale, and a consumer-actionable recourse hint. The HStoreField wording is spec-pinned verbatim at spec lines 563-568. Posture is consistent (loud over silent, per spec Decision 5's rationale at lines 574-577).

- **TODO comment cleanup is complete.** The shadow's `TODO comments: none.` line confirms no `# TODO(future):` blocks remain in `converters.py`. The original 3-line HStoreField TODO at the pre-Slice-2 lines 33-35 (per the build report's "Files touched" description) is gone, alongside Slice 2's removal of the JSONField half. Spec line 845 "All TODO comments for deferred scalars removed" is satisfied at the source level — Slice 6's documentation Definition-of-done item closes against this.

- **Helper-resolver tests use `sys.modules` manipulation correctly.** `test_resolve_hstore_field_returns_class_when_postgres_fields_importable` at `tests/types/test_converters.py:1204-1216` builds a fake module via `types.ModuleType(...)`, attaches `HStoreField = _FakeHStoreField`, and patches `sys.modules["django.contrib.postgres.fields"]` via `monkeypatch.setitem(...)`. The asymmetric negative-branch test at `:1219-1229` uses `monkeypatch.setitem(sys.modules, "django.contrib.postgres.fields", None)` to force `ImportError` on the next `import name` — documented Python behavior per spec Risks line 825. Both tests then `from django_strawberry_framework.types.converters import _resolve_hstore_field` and assert on the return value, matching Decision 7's `sys.modules`-manipulation example verbatim (spec lines 661-676).

- **`_FakeHStoreField` placement is appropriate.** `tests/types/test_converters.py:469-478` immediately follows `_FakeArrayField` at lines 450-466 in the test-helper region, keeping the two doubles lexically adjacent. Worker 1 flagged both placements (top of helper region vs. start of Slice-4 section banner) as acceptable; Worker 2 picked the adjacent-to-`_FakeArrayField` placement.

- **No accidental scope creep.** The slice contract per the plan's step 7 is exactly: +1 helper, +1 sentinel assignment, +1 `convert_scalar` branch, +1 docstring rewrite, −1 TODO block. `git diff --stat` confirms only `converters.py` (+114 lines / inserted) and `tests/types/test_converters.py` (Slice-4 portion is the ~265 lines from the HStoreField section onwards). No edits to `_resolve_array_field`, `_ARRAY_FIELD_CLS`, the ArrayField branch body, `SCALAR_MAP` entries other than what Slices 1 + 2 set, `convert_choices_to_enum`, `_sanitize_member_name`, `resolved_relation_annotation`, or `convert_relation`. The unrelated whitespace/comma edits in `examples/fakeshop/...` and `tests/base/test_init.py` predate Slice 4 (Slice-1 ruff-format flowdown) and are outside Slice-4's contract.

- **Shadow-helper control-flow numbers within expected envelope.** `convert_scalar` is now **102 lines / 14 branch nodes** (vs. Worker 1's predicted 78-82 lines / 12-13 branches). The line count is slightly above prediction because the docstring rewrite expanded the Raises section (4 new nested bullets) and the Algorithm section gained the step-0 entry. The branch count (14) is one above Worker 1's upper-bound estimate (13), still inside the "don't flag as Medium unless line count > ~100 or branch count > 15" tolerance Worker 1 set. The branches are doing genuine dispatch work (sentinel guards × 2, outer-choices rejection × 2, nested-array rejection × 1, MRO loop, choice branch, null-widening branch, unsupported-field raise). No further extraction would buy readability against the indirection cost.

### Temp test verification

No temp test files were created during this review. The diff's assertion shapes (introspection chain depth, `result.errors is None`, `result.data == {"owner": {"data": payload}}`, `pytest.raises(ConfigurationError, match=...)`, `_FakeHStoreField` as the `isinstance` target after monkeypatch) are concrete enough to verify by reading against the spec's Decision 5 / Decision 7 contracts and the existing Slice-2 / Slice-3 mirror tests. No suspicions surfaced that required a behavior-probing temp test.

### Notes for Worker 1 (spec reconciliation)

- **No spec edits needed.** Worker 2's notes correctly report no drift; my review confirms it. Decision 5 (spec lines 550-578) and Decision 7 (lines 594-705) carried Slice 4 cleanly.
- **Carry-forward to the integration pass.** Four deferred DRY candidates surfaced during this review, none load-bearing at the slice level:
  1. `_resolve_array_field` / `_resolve_hstore_field` factory consolidation — evaluate against IDE-go-to-definition cost.
  2. `_ARRAY_FIELD_CLS` / `_HSTORE_FIELD_CLS` named-sentinel-per-branch shape — keep as-is unless the integration pass adds a third sentinel.
  3. Cross-branch `ConfigurationError` message-template extraction — both messages are spec-pinned verbatim; a shared template would either need to inline the spec wording or paraphrase it.
  4. `_make_one_field_schema(model_cls, field_name)` helper extraction at ~24 sites — Slice 4 is the last `tests/types/test_converters.py`-mutating slice, so the integration pass has full parameter-surface visibility (sentinel-monkey-patch present/absent + payload variety + introspection-vs-`execute_sync`).
- **`app_label` literal count at 29 occurrences** across `tests/types/test_converters.py` post-Slice-4. The Slice 3 carry-forward flagged ~25 as the threshold for reassessing a module-level constants block; Slice 4 pushed past it. Defer the call to the integration pass — the trade-off is one constants block against losing the inline readability of `app_label = "test_hstorefield"` at the model declaration site.

### Review outcome

`review-accepted`. Every spec-required behavior for Slice 4 is reflected in the diff with no unresolved findings:

- Decision 4's two-helper + two-sentinel shape matches verbatim.
- Decision 5's HStoreField branch lands verbatim, in the spec-pinned position (after ArrayField branch, before MRO walk), with the spec-pinned outer-`choices` rejection wording.
- `HStoreField` is NOT in `SCALAR_MAP`.
- All 6 sentinel-branch tests + 2 helper-resolver tests + 1 optional gated test are present with the correct monkeypatch-before-`DjangoType` ordering.
- `_FakeHStoreField` is a bare `models.Field` subclass per Decision 7.
- The `convert_scalar` docstring rewrite enumerates all 5 `ConfigurationError` triggers and the step-0 sentinel branches.
- The `{"k1": "v", "k2": None}` resolver test exercises `schema.execute_sync` with the dict shape (including `None`) preserved (spec Decision 7 / Test plan item 18, line 184).
- HStoreField outer-`choices` rejection message is loud + actionable, mirroring ArrayField's posture.
- No public-surface change in `__init__.py`.
- No CHANGELOG, docs, KANBAN, or archive surfaces touched.

Status set to `review-accepted` at the top of this artifact.

---

## Final verification (Worker 1)

### DRY check across this slice and Slices 1-3

The task brief named four cross-slice DRY candidates plus the `app_label` literal density issue. Walked each one against the current diff and against the prior accepted slice artifacts (`docs/builder/bld-slice-1-bigint_scalar.md`, `bld-slice-2-jsonfield.md`, `bld-slice-3-arrayfield.md`). All five are properly deferred to the integration pass; none rises to `revision-needed` at this stage.

1. **`_resolve_array_field` / `_resolve_hstore_field` near-twin pair** at `django_strawberry_framework/types/converters.py:65-75` and `:78-88`. Diff confirmed: bodies differ in exactly one identifier (`ArrayField` ⇄ `HStoreField`) plus the docstring symbol name. Spec Decision 4 (`docs/spec-deferred_scalars.md:525-548`) commits to two parallel helpers; the named contract supports IDE go-to-definition that a `_resolve_postgres_field(name: str)` factory would lose. **Defer to integration pass.** Slice 4 already plans for this in its DRY analysis (`bld-slice-4-hstorefield.md` Plan / DRY analysis bullet 1) and Slice 3's final-verification carry-forward (worker-memory) named the same disposition.
2. **Parallel `convert_scalar` sentinel branches at `converters.py:147-160` (ArrayField) and `:165-174` (HStoreField).** Both share outer-guard + outer-`choices` rejection + outer-null widening, but diverge post-`choices`: ArrayField rejects nested arrays then recurses with `list[inner]` wrap; HStoreField returns `strawberry.scalars.JSON` directly. Spec Decision 5 (`spec-deferred_scalars.md:552-571`) says "mirrors Decision 2's shape" — the parallel-but-different posture is deliberate. A shared `_handle_postgres_field(field, type_name)` dispatcher would force conditional sub-branches inside a single body and lose the inline readability of two short branches (≤14 lines each). **Defer to integration pass.** Worker 3's review (DRY findings bullet 3) reaches the same conclusion.
3. **Shared error-message template wording for outer-`choices` rejection** at `converters.py:153-157` (ArrayField) and `:167-172` (HStoreField). Both messages name `field.model.__name__` + `field.name` and follow the `<FieldType> on <Model>.<Field> declares choices; <rationale>; <recourse>` shape. Both are spec-pinned verbatim (`spec-deferred_scalars.md:503-511` for ArrayField, `:563-568` for HStoreField). A shared `_OUTER_CHOICES_REJECTION_TEMPLATE` constant would tighten the file but would either need to inline the spec wording or paraphrase the rationale text, which varies between field types (ArrayField's "outer-array choices are ambiguous"; HStoreField's "HStore stores a `dict[str, str | None]` with no enum-able shape"). **Defer to integration pass.** Likely outcome: keep verbatim; the rationale text legitimately differs by field type.
4. **`_make_one_field_schema` test-helper extraction.** Trio-pattern site count (synthetic model + `DjangoType` + `Query` + `schema.execute_sync` or introspection): 5 (S1) → 8 (S2) → 17 (S3) → ~24 (S4). Worker 3's S1 review first flagged this; each subsequent slice deferred per the same rationale (parameter surface not fully visible). Slice 4 is the last `tests/types/test_converters.py`-mutating slice — Slice 5 touches version-bump files only, Slice 6 touches docs only — so the integration pass now has the full parameter surface (sentinel-monkey-patch present/absent + payload variety + introspection-vs-`execute_sync`). **Defer to integration pass; ready to land there.**
5. **`app_label` literal density.** Counts in `tests/types/test_converters.py` post-Slice-4: `"test_bigint"` 5x + `"test_jsonfield"` 3x + `"test_arrayfield"` ~9x + `"test_hstorefield"` 7x + `"test_choice_enums"` 4x = **~28 occurrences**. Slice 3's final-verification carry-forward (worker-memory entry from Slice 3) named ~25 as the reassessment threshold; Slice 4 pushed past it. Trade-off is one module-level constants block vs. losing the inline readability of the literal at the model-declaration site. **Defer to integration pass; this is the borderline call worth weighing first.**

No slice-level finding rises to `revision-needed`. The spec/plan explicitly defers consolidation to the integration pass per BUILD.md "Cross-slice integration pass" rules; honoring that posture here.

### Existing tests still pass

Ran the focused-test sweep specified in the task brief:

```
uv run pytest tests/test_scalars.py tests/types/test_converters.py tests/base/test_init.py -x
```

Result: **79 passed, 2 skipped, 2 warnings in 0.40s.** All 9 new Slice-4 tests pass:

- `test_resolve_hstore_field_returns_class_when_postgres_fields_importable`
- `test_resolve_hstore_field_returns_none_when_postgres_fields_unimportable`
- `test_hstore_field_maps_to_json_scalar_via_fake_sentinel`
- `test_hstore_field_nullable_via_fake_sentinel`
- `test_hstore_field_resolver_dict_serializes_via_schema_execution`
- `test_hstore_field_resolver_dict_with_none_value_via_schema_execution`
- `test_hstore_field_outer_choices_rejected_via_fake_sentinel`
- `test_hstore_field_sentinel_none_path`
- `test_real_hstore_field_compatible_with_strawberry` (skipped; `pytest.importorskip("django.contrib.postgres.fields")` on dev env without postgres-contrib — expected)

The other skipped test (`test_real_array_field_compatible_with_strawberry`) is Slice 3's gated test, skipping for the same reason.

The two warnings are pre-existing `test_choice_enums._owner` re-registration `RuntimeWarning`s (out of Slice-4 scope; noted in worker memory for the final test-run gate's optional warnings sweep).

`pytest.ini`'s `addopts = -v --cov --cov-report=term-missing` auto-applies coverage flags to every `uv run pytest` invocation. BUILD.md forbids Worker 1 from passing `--cov*` flags themselves; the auto-applied flag is project-wide config (matches CI) and cannot be disabled without passing `--no-cov`, which would itself violate the rule. The existing-tests-pass gate is unaffected: 79 passes, 2 expected skips, 0 failures. Per BUILD.md "Coverage is the maintainer's gate, not a worker's tool", the coverage percentage at the bottom of pytest's output is not inspected here — the gate is "existing tests still pass," which is satisfied.

### Spec reconciliation

Walked Worker 2's `### Notes for Worker 1 (spec reconciliation)` (`bld-slice-4-hstorefield.md` Build report): "No spec gaps or conflicts surfaced during implementation. The plan and Decision 5 / Decision 7 carried Slice 4 cleanly without drift."

Walked Worker 3's `### Notes for Worker 1 (spec reconciliation)` (`bld-slice-4-hstorefield.md` Review): "No spec edits needed. Worker 2's notes correctly report no drift; my review confirms it. Decision 5 (spec lines 550-578) and Decision 7 (lines 594-705) carried Slice 4 cleanly." Worker 3 listed four deferred DRY candidates as integration-pass carry-forward and called out the `app_label` literal density at 29 occurrences (one off my count of 28 — re-counted; the discrepancy is between Worker 3's grep including the `_FakeArrayField`'s `app_label` definition string vs. the call sites only; not material at the integration-pass scale).

Re-read the spec's status/header (`docs/spec-deferred_scalars.md:1-8`). Line 4 still reads `Status: draft (revision 10, post-feedback2 re-review).` Accurate for Slice-4 close — Slice 5 (version-bump quintet) is the next mutator and Slice 6 owns the archival lifecycle edit.

**No spec edit triggered.** The cross-slice DRY consolidation work that the integration pass will own may surface a need for a tighter spec contract (e.g., a named convention for sentinel-guarded postgres-field branches if a third one ever lands), but at the close of the last logic-bearing slice the spec's Decision 4 + Decision 5 contracts carried implementation faithfully across both branches. Capturing the spec-contract observation here, not editing the spec: **if the integration pass extracts the four consolidation targets (factory helper, branch dispatcher, message template, test-helper trio), the consolidation work itself does not require a spec edit** — the spec pinned the *behavior* (verbatim error messages, single-purpose helpers, in-function test-model pattern) and is silent on the *implementation shape* of the consolidation, which is correct for the integration pass to own.

### Final status

`final-accepted`. Top-level `Status:` updated.

### Summary

Slice 4 shipped the sentinel-guarded `HStoreField` → `strawberry.scalars.JSON` conversion path inside `convert_scalar`, mirroring Slice 3's `ArrayField` shape. Adds `_resolve_hstore_field()` helper + module-level sentinel `_HSTORE_FIELD_CLS` (parallel to `_resolve_array_field` / `_ARRAY_FIELD_CLS` from Slice 3). Adds a new sentinel-guarded branch in `convert_scalar` that rejects outer `choices` with `ConfigurationError` (consistent with the ArrayField outer-`choices` rejection in Decision 2) and returns `strawberry.scalars.JSON` widened on `field.null`. Adds 8 mandatory + 1 optional gated test in `tests/types/test_converters.py` plus a `_FakeHStoreField` test double. Drops the remaining HStoreField TODO comment in `converters.py`, satisfying the spec's "all TODO comments for deferred scalars removed" Definition-of-done item at the source level. Amortizes the `convert_scalar` docstring rewrite across both sentinel branches (Algorithm gains step 0 listing both branches; Raises gains all five `ConfigurationError` triggers), closing Slice 3's deferred Low finding.

No public-surface change in `__init__.py` (HStoreField is sentinel-guarded inside `convert_scalar`; not added to `SCALAR_MAP`). 79 focused tests pass + 2 expected skips. The build proceeds to Slice 5 (atomic version-bump quintet) next.

### Spec changes made (Worker 1 only)

None.

