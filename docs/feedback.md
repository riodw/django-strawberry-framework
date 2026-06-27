# Review — `spec-039-serializer_mutations-0_0_13.md`

Reviewer pass against the package source, the cited precedents (spec-035/036/037/038),
the upstream graphene-django reference, and the example app. Date: 2026-06-26.

## Verdict

This is a strong, implementation-ready spec. Its central thesis — *"reuse, byte-identical,
the spec-036 contracts and the spec-038 precedents; the only new machinery is the
serializer converter + pipeline + the DRF soft-dep"* — **holds up under verification**.
I checked the concrete reuse claims against real code and the precedents against the prior
specs; almost everything is confirmed exactly (see below). The findings that follow are
mostly refinements. **Two (P1) are correctness gaps worth resolving before Slice 2/3
land**; the rest are clarity/robustness improvements.

## What I verified (and it checks out)

The reuse premise is not hand-waving — these were confirmed at the `file:line` level:

- **The `DjangoMutation` seam set** (`_resolve_model` / `_validate_meta` / `build_input` /
  `input_type_name` / `input_module_path` / `resolve_sync` / `resolve_async`) exists exactly
  as named (`mutations/sets.py`), and `_resolve_model`'s docstring really does name the
  *"0.0.13 serializer flavor (`Meta.serializer_class.Meta.model`)"*. The base `_validate_meta`
  raises when `_resolve_model` returns `None` (`sets.py:505-509`) — so the
  `ModelSerializer`-required contract comes for free.
- **The `038`-generalized `DjangoMutationField`** is genuinely duck-typed
  (`_has_mutation_protocol`, not `issubclass`) and dispatches via `mutation_cls.resolve_sync/async`
  + `input_type_name(meta)` + `input_module_path` (`mutations/fields.py:89-118, 184, 226-233`).
  The "no factory edit needed" claim is real.
- **Every promoted helper the resolver plans to call exists in `mutations/resolvers.py`**:
  `locate_instance`, `coerce_lookup_id`, `authorize_or_raise`, `refetch_optimized`,
  `build_payload`, `not_found_error`, `save_or_field_errors`, plus `_decode_relation_id_set`
  / `_raw_pk_relation_error`. `save_or_field_errors` does return `list[FieldError] | None`
  and **discards** its callable's return value (`resolvers.py:1150-1166`) — confirming the
  value-preserving-closure design in Decision 8 is necessary, not gold-plating.
  `refetch_optimized` re-fetches by pk *without* the visibility filter, as Decision 9 claims.
- **The `forms/` twin is real and tight**: `_run_modelform_pipeline_sync` runs
  locate→authorize→decode with the verbatim *"Authorize BEFORE decoding relations"* comment
  (`forms/resolvers.py:490-492`); `_visible_related_object`, `_cached_build_form_input`,
  `guard_create_required_fields`, `clear_form_input_namespace`, the `data=`/`files=` split,
  and the `_reconstruct_partial_data` update reconstruction all exist as described. The
  spec's "DRF diverges by using `partial=True` instead of reconstruction" contrast is
  accurate.
- **The finalizer / registry / utils plumbing** is all present: the pre-bind ledger reset
  block (`finalizer.py:771-776`), the *"ModelForm flavor rides bind_mutations yet writes the
  FORM ledger"* comment (`761-763`), `TypeRegistry.clear()`'s `_clear_if_importable(...)`
  co-clear rows (`registry.py:525-547`), `request_from_info(info, *, family_label=...)` with
  dual `info.context.request` / bare-`HttpRequest` resolution (`utils/permissions.py:74-96`),
  and `materialize_generated_input_class`'s collision raise (`utils/inputs.py:201-205`).
- **`__init__.py` is eager-import + explicit `__all__` with no existing `__getattr__`**, and
  `__version__ == "0.0.12"` — so the root `__getattr__` lazy-export plan (Decision 12) is the
  right shape and is genuinely net-new.
- **The example substrate exists**: `Item` has the `unique_item_per_category` constraint over
  `(category, name)`, the `attachment` FileField, `is_private`, and `category` FK
  (`products/models.py`); `products/serializers.py` does **not** exist yet; the multipart
  `/graphql/` precedent in `test_uploads_api.py` (operations/map form fields) is real; and the
  README "Coverage rule." live-first mandate is verbatim at `test_query/README.md:7`.
- **Precedents**: spec-036 Decision 13 (joint 0.0.11 cut), the frozen FieldError naming the
  downstream 0.0.12/0.0.13 reusers, Decision 15 write-auth split, the Medium-1
  re-fetch-without-visibility exception; spec-037's Pillow-as-dev-dep decision
  (`spec-037:1605-1616` — this citation is sound); spec-038 Decision 4/6 and the three-axis
  `DjangoMutationField` generalization; spec-035's G2 `.only()`-suppression gate — all confirmed.
- `FormInputFieldSpec` is a real symbol (imported in `tests/forms/test_converter.py`), so the
  "the `038` `FormInputFieldSpec` analog" framing is accurate against code even though spec-038
  prose doesn't name it.

The upstream graphene-django reference also matches: `convert_serializer_field(field, is_input=True)`
+ the `@register(serializers.Field) → String` singledispatch catch-all, and
`SerializerMutation(ClientIDMutation)` with `SerializerMutationOptions` carrying
`model_operations` / `lookup_field` / `optional_fields` + `get_serializer_kwargs`. The
"borrow the capability, reject the `MutationOptions` surface" posture is faithful.

---

## P1 — Resolve before building

### 1. DRF must survive the *entire* CI matrix under `filterwarnings = error`

This is the biggest practical risk and the spec under-weights it. `pyproject.toml` declares
`requires-python = ">=3.10,<4.0"` and classifiers for **Django 5.2 and 6.0**, and the CI
matrix (`django.yml`) actually runs **Django 5.2.0 → 5.2.* → 6.0.* → latest on Python
3.10 → 3.14**. `pytest.ini` sets `filterwarnings = error`. So adding
`djangorestframework` to the dev group means **DRF must import and run *warning-free* across
that whole matrix** — any `DeprecationWarning`/`RemovedInDjango*Warning` DRF emits under
Django 6.0 or Python 3.14 becomes a hard collection/test failure. This is *exactly* the
failure mode that just bit `forms.URLField()` (the `assume_scheme` fix): a third-party-adjacent
deprecation turned fatal by `-W error`.

The spec's "DRF version floor" open question (Risks) frames this only around
`api_settings.NON_FIELD_ERRORS_KEY` availability and guesses `>=3.15`. The *binding*
constraints are different and stronger:
- DRF's Django-version support **lags** Django releases; confirm a DRF release exists that
  officially supports **Django 6.0 and Python 3.14** before pinning a floor. If none does
  yet, the Django-6.0/`latest` matrix nodes will fail at `uv sync` / import time.
- Even with a compatible release, budget for a targeted `filterwarnings` `ignore::` line for
  any DRF-origin deprecation you cannot fix (the spec's own pytest.ini comment already
  sanctions this for "warnings originating in third-party packages we cannot fix"). Name that
  possibility in Decision 12 / the floor question rather than discovering it in CI.

Recommendation: turn the "DRF floor" open question into a concrete pre-Slice-1 check —
*"verify DRF X.Y imports warning-free on (py3.14, Django 6.0/latest); record the exact floor
and any required `ignore::` entry."*

### 2. The finalizer's serializer-ledger clear must be import-guarded — as written it would break DRF-absent schema builds

Decision 6 / Slice 2 says `clear_serializer_input_namespace()` *"joins that same pre-bind
[reset] block"* alongside `clear_mutation_input_namespace()` / `clear_form_input_namespace()`,
which the finalizer calls **directly** (`finalizer.py:771-776`). But those two modules are
always importable; `rest_framework/inputs.py` lives **behind the DRF soft-import guard**.
`finalize_django_types()` runs on *every* schema build — including for read-side / model /
form consumers who never install DRF (Goal 6: "the package imports without DRF"). A direct
`from .rest_framework.inputs import clear_serializer_input_namespace` in the pre-bind block
would raise `ImportError` and **break schema construction for everyone without DRF**.

Note the asymmetry the spec already encodes: place #2 (`TypeRegistry.clear()`) correctly uses
`_clear_if_importable(...)`. Place #1 (the finalizer) is described as a peer of the *direct*
mutation/form calls. It must use the same importable-guard (or a try/except) — which is also
semantically correct: when DRF is absent, no `SerializerMutation` can be declared, so the
serializer ledger is necessarily empty and a no-op clear is right. Please state the guarded
call explicitly in Slice 2 so an implementer doesn't mirror the (unguarded) mutation/form
clears literally.

---

## P2 — Should resolve in the spec

### 3. `serializer.save()` can raise `ValidationError`, not only `IntegrityError`

The pipeline (Decision 8 step 6) wraps `save()` solely in the `036`
`save_or_field_errors` *IntegrityError → envelope* mapper. But DRF explicitly supports raising
`serializers.ValidationError` from a custom `create()` / `update()` / `save()` (and a
model-level `ValidationError` can surface there too). As written, such an error escapes as a
**top-level `GraphQLError`**, contradicting the spec's own "validation → FieldError envelope,
not GraphQLError" contract (Error shapes). Decide explicitly: either (a) catch a save-time
`ValidationError` and route it through the recursive flattener (the consistent choice), or
(b) declare save-time `ValidationError` out of contract and say so. Right now it's silent.

### 4. The `get_serializer_for_schema()` loud-rejection trigger is mis-located

Decision 7 says the default reads `serializer_class().fields`, but rejects with
`ConfigurationError` *"if no-arg construction raises."* Construction of a `ModelSerializer()`
with no args **does not raise** — DRF builds `.fields` lazily on first access (or in a custom
`get_fields()` that reads `self.context`). The failure for a context-requiring serializer
surfaces at **`.fields` access**, not at `serializer_class()`. Tighten the wording so the
guard wraps the `.fields` materialization (and a hook that returns a request-shaped field
set), otherwise the "rejected loudly" path won't actually trigger for the serializers it's
meant to catch.

### 5. The carried-but-unexercised `is_input` parameter vs `fail_under = 100`

Decision 7 says `convert_serializer_field` carries an `is_input` parameter "for graphene
parity / forward use, but `is_input=False` … is not exercised." Under `fail_under = 100`
(`pyproject.toml:175`), any **branch** keyed on `is_input` that the tests don't drive is an
uncovered line → gate failure. Clarify that `is_input` is *accepted-and-ignored* with **no
dead branch** (fine for coverage), or commit to testing `is_input=False`. A parameter that is
merely threaded is OK; a `if not is_input:` branch is not.

### 6. `UniqueTogetherValidator` + `partial=True` is DRF-version-sensitive

The headline live test asserts the unique-together constraint fires when **only `name`**
changes on an `update` (Decision 13 / Test plan). That depends on DRF's
`UniqueTogetherValidator.filter_queryset` **backfilling the unchanged `category`** from
`serializer.instance` during a partial update. Current DRF does this, but it's precisely the
kind of version-dependent semantics the DRF-floor question (P1 #1) should pin — if the
installed DRF's partial backfill differs, that assertion changes meaning. Tie this test's
expectation to the verified DRF floor and add a one-line note that the partial unique-together
fire is a DRF behavior, not a package one.

---

## P3 — Nits / clarity

7. **Stale "Slice 5" reference.** Revision 4 collapsed the plan to four slices, but the Doc
   updates section (line ~2243) still says CHANGELOG *"carries the bullets only when the Slice
   **5** maintainer prompt explicitly requests it."* Line ~2495 correctly says Slice 4. Fix the
   2243 occurrence.

8. **Two `Meta.fields` namespaces.** The mutation's `Meta.fields` / `Meta.exclude` narrows the
   *input surface*; the serializer's own `Meta.fields` defines *validation*. A DRF migrant may
   expect the mutation key to also restrict what the serializer validates. One explicit
   sentence ("narrows the GraphQL input, not the serializer's validation field set") would
   prevent confusion. Relatedly, state that `Meta.optional_fields` is a **no-op on `update`**
   (the PartialInput is already all-optional), so a consumer setting it there isn't surprised.

9. **`rest_framework/` subpackage name collides with DRF's own top-level `rest_framework`
   package.** This is the root cause of the two-namespace `sys.modules` eviction dance in the
   absent-path test (Decision 12). The spec justifies the name (card + graphene-django parity)
   and handles the eviction correctly — just worth one sentence noting the test-complexity cost
   is a direct consequence of the name, so a future reader understands why both `rest_framework*`
   *and* `django_strawberry_framework.rest_framework*` must be evicted.

10. **`ListField` child scope.** `ListField → list[child]` is listed as supported, but the
    spec doesn't bound what `child` may be. A scalar child (`list[int]`) is clear; a `ListField`
    whose child is a relation or nested serializer is ambiguous against the
    rejected-nested-serializer rule. One line scoping it to scalar children (and what happens
    otherwise) closes the gap.

---

## Closing

The spec is unusually disciplined — the four-revision history shows the hard problems
(authorize-before-decode ordering, descriptor identity over name-only keys, the
value-preserving save, retry-idempotent ledger clears, the soft-dep non-memoization) were
already found and resolved correctly. P1 #1 (DRF × the Django-6.0/py3.14 matrix under
`-W error`) and P1 #2 (the unguarded finalizer clear) are the two I'd want decided before
code lands; the P2 items are contract-completeness gaps; P3 is polish.
