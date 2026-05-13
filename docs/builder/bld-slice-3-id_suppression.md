# Build: Slice 3 — id suppression

Spec reference: `docs/spec-relay_interfaces.md` (lines 35-40 Slice 3 checklist; lines 278-287 Decision 2 id handling; lines 333-342 Decision 5 lifecycle and ordering — id suppression happens at `__init_subclass__` collection time, base injection at finalization time; lines 352-361 Decision 7 optimizer / projection invariants — `DjangoTypeDefinition.field_map` keeps every selected Django field including the pk regardless of whether the Strawberry `id` annotation was suppressed; lines 438-441 implementation-plan step 3; lines 481-482 test plan entries `test_relay_node_strips_django_id_annotation` and `test_non_relay_type_keeps_id_int`)
Status: final-accepted

## Plan (Worker 1)

### DRY analysis

- **Existing patterns reused.**
  - The TODO anchor at `django_strawberry_framework/types/base.py:574-577` (the three-line `# TODO(0.0.5 relay interfaces; ...)` block inside `_build_annotations`'s scalar branch) names the **exact** insertion site for Slice 3: "when `relay.Node` is declared in `Meta.interfaces`, suppress the synthesized Django `id` annotation while preserving the pk field in `DjangoTypeDefinition.field_map` for optimizer use." Slice 3 replaces the anchor with the suppression check in the same change (per `AGENTS.md` line 10: anchors are paired with the code that ships the slice and are removed in that same change). The other Slice 4 TODO anchors in `types/relay.py:9-24` remain untouched.
  - `_build_annotations` is called from exactly one site, `DjangoType.__init_subclass__` at `django_strawberry_framework/types/base.py:116-121`. The call already passes `cls`, `fields`, `source_model=meta.model`, and `consumer_authored_fields=consumer_authored_fields` as kwargs. The validated `interfaces` tuple is in scope at line 95 (`interfaces = _validate_meta(meta)`), which executes **before** `_build_annotations` is called. The cleanest data flow is to add one more kwarg — `interfaces: tuple[type, ...] = ()` — to `_build_annotations`, threading the already-validated tuple straight through. This matches the same pattern `consumer_authored_fields` uses (validated/derived once in `__init_subclass__`, then passed by kwarg) and avoids the function re-reading `Meta` or `cls.__django_strawberry_definition__` (which is not even set yet at the time `_build_annotations` runs — the definition is constructed at lines 122-138 **after** `_build_annotations` returns at lines 116-121).
  - `convert_scalar(field, cls.__name__)` (`django_strawberry_framework/types/converters.py`) is the existing call that produces `id: int!` for `AutoField` / `BigAutoField` / `SmallAutoField` (per spec line 118; this is the SCALAR_MAP path at `converters.py:49-116`). Slice 3 does **not** modify `convert_scalar`; it simply skips the `annotations[field.name] = convert_scalar(field, cls.__name__)` assignment for the pk field when `relay.Node` is among the interfaces. The selected-field list (`fields`) is unchanged — `FieldMeta` and `DjangoTypeDefinition.field_map` continue to see the pk, satisfying Decision 7 (spec line 361: "the field map is the optimizer's source of truth; suppression happens later in the data flow, in `_build_annotations`").
  - The Slice 1 carry-forward in `docs/builder/worker-memory/worker-1.md:14-17` already pinned the source-of-truth rule: "Source of truth for 'is `relay.Node` declared?' is `definition.interfaces`, never re-read from `Meta`. Slice 3's `id` suppression in `_build_annotations` should ask `relay.Node in interfaces` against the validated tuple." Slice 3's implementation follows that pin: the validated `interfaces` tuple flows in via the new kwarg; the function never reads `Meta` or `definition.interfaces` directly.
  - The Slice 2 carry-forward in `docs/builder/worker-memory/worker-1.md:33` reinforces the same rule for Slice 3 specifically: "Slice 3 (`id` suppression): the source of truth for 'is `relay.Node` declared?' is still `definition.interfaces`, not `Meta`. Slice 3's `_build_annotations` change should test `relay.Node in definition.interfaces` (or use the validated tuple flowing through `_validate_meta`'s return), not re-read `Meta`." The plan picks the second option (use the validated tuple) because `definition` is not yet constructed when `_build_annotations` runs.
  - The `_select_fields` walk and the `field.is_relation` / `field.name in consumer_authored_fields` short-circuits in `_build_annotations` (lines 549-573) stay unchanged. The suppression is one additional branch in the scalar arm, immediately before the `convert_scalar(...)` call — the same site the existing TODO anchor names.
  - The test scaffolding pattern for bypassing `DEFERRED_META_KEYS` is established in `tests/types/test_relay_interfaces.py:14-35`: import `from strawberry import relay`, declare a `_meta(**attrs)` helper that builds a throw-away `Meta` class against a fakeshop model (`Category`), and call the unit-level helper directly (Slice 1 used `_validate_interfaces(meta)`; Slice 3 will use `_build_annotations(cls, fields, ...)` directly). The autouse `_isolate_registry` fixture at `tests/types/test_relay_interfaces.py:24-29` already clears the registry between tests. Slice 3 appends its tests under a new `# Slice 3 — id suppression` divider; the fixture re-use is automatic.
  - The non-relay control test mirrors the existing implicit baseline: every passing test in `tests/types/test_base.py` that synthesizes a `DjangoType` against `Category` today produces `id: int` in `cls.__annotations__`. The Slice 3 control test `test_non_relay_type_keeps_id_int` pins this regression guard explicitly so a future drift (e.g. an accidental suppression for all types) is caught.

- **New helpers justified.**
  - **No new module, no new function, no new helper.** Slice 3 is the smallest of the five slices: one new kwarg on `_build_annotations`, one new branch in the scalar arm, and the TODO-anchor removal. Justification for not introducing an `implements_relay_node(type_cls)` helper from `types/relay.py` (per spec line 388-389): (a) The spec's "Internal helper surface" at lines 384-397 lists `implements_relay_node` as a **Slice 4** responsibility, not Slice 3. (b) At Slice 3's call site, the check is `relay.Node in interfaces` against a **tuple of validated interface classes**, not against `cls.__mro__`. Slice 4's `implements_relay_node(type_cls)` is the MRO-based check (`issubclass(type_cls, relay.Node)`) used after `cls.__bases__` mutation; the two questions are structurally different. Hoisting a shared helper now would either need to take both shapes (tuple + class) or force one shape into the other; neither pays for itself at one call site. (c) The carry-forward from Slice 2's review (worker-1 memory line 34: "Slice 4 (`install_relay_node_resolvers`): keep the `__func__` identity discriminator distinct from Slice 2's `__dict__` membership discriminator. They answer structurally different questions; collapsing them into a generic override-detector is a DRY false positive.") sets the precedent: Slice 3's tuple-membership check and Slice 4's MRO-issubclass check answer structurally different questions and should remain separate.
  - **No new module-level constant for the `"id"` literal.** The Django primary-key field's name is `"id"` for `AutoField` / `BigAutoField` / `SmallAutoField` (Django uses this attname by convention; per `model._meta.pk.name == "id"` for an auto pk). Slice 3 needs to compare `field.name` against the pk's name. The cleanest source of truth is `source_model._meta.pk.name` (which is already accessible because `source_model` is already a kwarg in `_build_annotations`), not a hard-coded `"id"` literal. This handles the case where a consumer model uses a non-default pk attname (e.g. `primary_key=True` on a `UUIDField` named `uuid`), in which case the pk's GraphQL annotation is the consumer's named scalar, not a synthesized `id: int`. Per Decision 2 (spec line 285): "the per-type opt-in keeps the contract local to the class declaration"; the contract is "suppress the **primary key's** synthesized scalar annotation when `relay.Node` is declared", and the primary key's attname is what `_meta.pk.name` returns. Using `_meta.pk.name` also matches Decision 7's "primary-key attname" language (spec lines 355-357) without forcing a separate constant.
  - **`relay.Node` lookup.** The check is `relay.Node in interfaces`. The plan imports `from strawberry import relay` at the top of `types/base.py` (no `from strawberry import relay` exists in the package source today; the only mention is the user-visible string `"strawberry.relay interface classes."` at line 347). Justification: (a) the import is a single-line addition next to the existing `from strawberry.types.field import StrawberryField` at line 29; (b) `from strawberry import relay` is the canonical spelling matching the spec's user-facing API at spec line 188 (`interfaces = (relay.Node,)`); (c) Slice 4's `apply_interfaces` / `implements_relay_node` will also need `relay.Node`, so the import is a forward investment.

- **Duplication risk avoided.**
  - **Risk 1: re-reading `Meta.interfaces` inside `_build_annotations` instead of accepting the validated tuple.** The naive shape would be `getattr(meta, "interfaces", None)` inside `_build_annotations`, which would (a) duplicate the read site Slice 1 already centralized in `_validate_interfaces`, (b) bypass the Slice 1 normalization (single-class -> tuple, missing-comma spelling), and (c) ignore the spec's Decision 2 (spec line 287) which ties the suppression decision to the validated value, not the raw `Meta` value. The plan avoids this by adding `interfaces: tuple[type, ...] = ()` as a kwarg and passing the already-validated `interfaces` variable from `__init_subclass__` (line 95) through to `_build_annotations` (lines 116-121).
  - **Risk 2: scattering the `relay.Node in interfaces` check across slices.** Slice 3 owns the suppression decision at collection-time (`_build_annotations`); Slice 4 will own the base-injection / resolver-injection decisions at finalization-time (`apply_interfaces` / `install_relay_node_resolvers`). Both ask "is `relay.Node` declared?" but at different lifecycle phases (collection vs. finalization). The plan keeps each slice's check local to its own data flow: Slice 3 checks `relay.Node in interfaces` against the kwarg tuple, Slice 4 will check `issubclass(cls, relay.Node)` against the post-mutation MRO. No shared `implements_relay_node` helper is hoisted in Slice 3 because Slice 4's check is structurally different (per Risk 5 below).
  - **Risk 3: hard-coding the `"id"` string literal.** The risk is two-fold: (a) a future maintainer might write `if field.name == "id" and relay.Node in interfaces: continue`, hard-coding the assumption that the Django pk attname is always `"id"`. This breaks for consumer models using `UUIDField(primary_key=True, db_column="uuid")` or similar. (b) The repeated-string-literal review pass would flag `"id"` if the suppression logic added another such literal. The plan avoids both by reading `source_model._meta.pk.name` once at the top of `_build_annotations` (alongside the existing `field` walk) and comparing `field.name == pk_attname`. The `pk_attname` lookup is a Django-standard idiom and already used elsewhere in the package's tests.
  - **Risk 4: suppressing scalar fields that are not the primary key.** The naive shape would be `if relay.Node in interfaces and field.name == "id"` without checking that `"id"` is actually the primary key. The plan compares `field.name == source_model._meta.pk.name` so only the actual pk field is suppressed. For models where the pk is renamed (e.g. `class Category(models.Model): uuid = models.UUIDField(primary_key=True)`), the suppression targets `field.name == "uuid"`. This matches Decision 2's "the Django `id` column itself is still selected for ORM/optimizer purposes" — the suppression is at the **annotation** layer, on the **primary-key field**, not on a literal field named `"id"`.
  - **Risk 5: pre-empting Slice 4's `implements_relay_node` helper.** The spec's "Internal helper surface" at lines 384-397 names `implements_relay_node(type_cls)` as Slice 4's responsibility, defined as "Return whether `type_cls` is a subclass of `strawberry.relay.Node`." That's an MRO check, post-base-injection. Slice 3's check is a tuple-membership check, pre-base-injection. The plan does **not** introduce a `implements_relay_node` helper in Slice 3 (defer to Slice 4); does **not** introduce a `interfaces_have_relay_node(interfaces)` helper (no second call site exists in Slice 3); and does **not** reach into `types/relay.py` (which is reserved for the Slice 4 helper surface). Worker 2 must not preempt Slice 4's helper.
  - **Risk 6: changing the order of operations in `__init_subclass__`.** The current order (lines 95-138) is: validate Meta → select fields → validate hints → build field_map → derive consumer-authored fields → build annotations → construct definition → register → mutate `cls.__annotations__` → assign `__django_strawberry_definition__` → install `is_type_of` → mirror optimizer state. Slice 3 does **not** reorder; it only threads the existing `interfaces` value (already captured at line 95) into the existing `_build_annotations` call at line 116. The plan must not move the `_validate_meta` call, the `_build_annotations` call, or the `DjangoTypeDefinition` construction relative to each other. Worker 2 must preserve the existing order.
  - **Risk 7: consumer-authored override interaction.** If a consumer writes `id: strawberry.ID = strawberry.field(...)` (or any other consumer-annotated `id` field) AND declares `relay.Node` in interfaces, the consumer's annotation lands via the `cls.__annotations__ = {**synthesized, **consumer_annotations}` merge at `types/base.py:142`. The suppression in `_build_annotations` only removes `id` from the `synthesized` dict; the consumer's `id` annotation in `consumer_annotations` is preserved by the merge. This is consistent with the spec line 282: "If the consumer includes `"id"` in `Meta.fields` while declaring `relay.Node`, the slice does not raise — the field is simply not generated on the GraphQL side." Spec line 348 also confirms: "Annotations and fields the interface itself declares (e.g. `Node._id`) are owned by the interface. Consumers must not shadow them on the `DjangoType` subclass; doing so will produce a Strawberry-level error at decoration time, which the spec leaves to Strawberry rather than re-implementing." Slice 3 therefore does **not** add a consumer-override check — Strawberry handles the consumer-shadowing case at decoration time. Worker 2 must not add an extra guard here.
  - **Patterns expected to recur in later slices.** (1) Slice 4's `apply_interfaces` reads from `definition.interfaces` (the same Slice-1-populated tuple); Slice 3's `_build_annotations` reads from the kwarg-threaded `interfaces`. Both read the **same validated source**, just at different lifecycle stages. The single-source-of-truth pattern Slice 1 established is honored. (2) Slice 3's "tuple-membership check pre-base-injection" vs. Slice 4's "MRO-issubclass check post-base-injection" is the second structural split between slices (the first was Slice 2's `__dict__` membership vs. Slice 4's `__func__` identity). Worker 1 carries the carry-forward: at integration pass, confirm both pairs of discriminators remain independent and Slice 4 has not collapsed any into generic helpers.
  - **Repeated string literal scan.** The shadow overview for `django_strawberry_framework/types/base.py` (regenerated for Slice 3 planning) reports under "Repeated string literals": `4x optimizer_hints`, `2x interfaces`, `2x description`. None are introduced by Slice 3; `"id"` is **not** in the repeated-literals list. The plan deliberately avoids introducing an `"id"` literal by reading `source_model._meta.pk.name` instead.

### Implementation steps

1. **Add the `from strawberry import relay` import** at `django_strawberry_framework/types/base.py:30` (immediately after the existing `from strawberry.types.field import StrawberryField` at line 29). The new import is alphabetically ordered among Strawberry imports; no other `strawberry.*` imports exist in this file. Justification: the suppression check at `_build_annotations` is `relay.Node in interfaces`, which requires the `relay` symbol in module scope. The import sits with the other Strawberry imports rather than down in the package's local `from .relay import install_is_type_of` block at line 40 to keep the upstream / first-party separation clean (the local `.relay` module is the package's `types/relay.py`, not `strawberry.relay`). No `from __future__ import annotations` exists at the top of this file (per inspection), so the import lands in the regular import block.

2. **Add the `interfaces: tuple[type, ...] = ()` kwarg to `_build_annotations`** at `django_strawberry_framework/types/base.py:519-525` (the function signature). The new kwarg is positional-keyword (after the existing `*` separator at line 522) with a default of `()` so any future caller — and the existing unit tests in `tests/types/test_base.py` that exercise `_build_annotations` indirectly through `__init_subclass__` — sees `0.0.4`-identical behavior when the kwarg is omitted. Place the kwarg adjacent to the existing `consumer_authored_fields` kwarg at line 524 so the `Meta`-derived block stays together. The trailing-comma convention applies (per `AGENTS.md` line 23 and `START.md` line 30).

   Updated signature shape:

   ```
   def _build_annotations(
       cls: type,
       fields: tuple[Any, ...],
       *,
       source_model: type[models.Model],
       consumer_authored_fields: frozenset[str] = frozenset(),
       interfaces: tuple[type, ...] = (),
   ) -> tuple[dict[str, Any], list[PendingRelation]]:
   ```

3. **Update the `_build_annotations` docstring** at `django_strawberry_framework/types/base.py:526-546` to document the new kwarg and the suppression behavior. Add to the Args section: `interfaces: The validated Meta.interfaces tuple. When relay.Node is among them, the primary-key field's synthesized scalar annotation is suppressed so Strawberry's interface-supplied id: GlobalID! is not shadowed.` Add a one-sentence note to the function-level docstring: "When relay.Node appears in interfaces, the primary-key field's synthesized annotation is dropped from the returned dict; the field stays in `fields` so the optimizer's field map continues to see it as a connector column (spec Decision 7, line 361)."

4. **Inside `_build_annotations`, derive the suppression decision once at the top of the function** (before the `for field in fields:` loop at line 549). Compute:

   ```
   suppress_pk_annotation = relay.Node in interfaces
   pk_attname = source_model._meta.pk.name if suppress_pk_annotation else None
   ```

   The `pk_attname` lookup is gated behind `suppress_pk_annotation` so non-Relay types (the common case, `0.0.4`-identical) do not incur the `_meta.pk.name` access. Justification: keeping the lookup local to the suppression case avoids any per-field branch overhead on the non-Relay path and signals intent ("`pk_attname` is only meaningful when suppression is on"). Placement: the two lines land between the existing `annotations: dict[str, Any] = {}` (line 547) and `pending: list[PendingRelation] = []` (line 548), or alternately just before the `for field in fields:` loop at line 549. Either is acceptable; recommended placement is immediately before the loop so the "where do I make the decision once" line and the "where do I use the decision per-field" line are visually adjacent.

5. **Inside the scalar arm of `_build_annotations`'s field loop** (the `else:` branch at line 566), add the suppression check **after** the existing `consumer_authored_fields` short-circuit (line 567-573) and **before** the `annotations[field.name] = convert_scalar(field, cls.__name__)` line (currently line 578, which is the same line the TODO anchor at lines 574-577 sits above). The new branch:

   ```
   if suppress_pk_annotation and field.name == pk_attname:
       continue
   ```

   The `continue` skips appending the synthesized scalar annotation; the field stays in `fields` so `_select_fields`'s contract and the downstream `field_map` / `selected_fields` consumers see the pk unchanged.

   Replace the three-line `# TODO(0.0.5 relay interfaces; ...)` block at lines 574-577 with this branch. The comment is removed in the same change (per `AGENTS.md` line 10).

   The final shape of the scalar branch in `_build_annotations` reads:

   ```
   else:
       if field.name in consumer_authored_fields:
           # A consumer-assigned ``StrawberryField`` (or annotation) on a
           # scalar column wins ...
           continue
       if suppress_pk_annotation and field.name == pk_attname:
           continue
       annotations[field.name] = convert_scalar(field, cls.__name__)
   ```

6. **Update the single call site in `DjangoType.__init_subclass__`** at `django_strawberry_framework/types/base.py:116-121`. Append the new kwarg `interfaces=interfaces` (the variable captured at line 95 from `_validate_meta`). Updated call shape:

   ```
   synthesized, pending = _build_annotations(
       cls,
       fields,
       source_model=meta.model,
       consumer_authored_fields=consumer_authored_fields,
       interfaces=interfaces,
   )
   ```

   The trailing-comma convention applies.

7. **Do not touch the `_select_fields` walk or the `DjangoTypeDefinition` construction.** Per Decision 7 (spec line 361), `DjangoTypeDefinition.field_map` keeps every selected Django field including the pk regardless of whether the Strawberry `id` annotation was suppressed. The `field_map` at `__init_subclass__:99` is built from `fields` (the full selection from `_select_fields`); Slice 3 does not modify that. The `selected_fields=tuple(fields)` and `field_map=field_map` kwargs at lines 129-130 are unchanged. The optimizer's view of the pk column is unaffected — verified by inspection: `FieldMeta.from_django_field(f)` in the comprehension at line 99 sees every selected field, including the auto-pk, exactly as it does in `0.0.4`.

8. **Do not touch `types/relay.py`.** Slice 3 introduces no new helper in `types/relay.py`. The four remaining TODO anchors at `django_strawberry_framework/types/relay.py:9-24` (Slice 4's `apply_interfaces`, `implements_relay_node`, `install_relay_node_resolvers`, the four `_resolve_*_default` defaults) stay untouched. Slice 4 lands those helpers.

9. **Do not touch `DEFERRED_META_KEYS`.** Per the Slice 3 checklist (spec lines 35-40), `"interfaces"` stays in `DEFERRED_META_KEYS` until Slice 5 promotes it. End-to-end `Meta.interfaces` declared on a real `DjangoType` therefore still raises the deferred-key error at `_validate_meta` before reaching `_build_annotations`. Slice 3 unit tests call `_build_annotations` directly (see Test additions below) — the same scaffolding pattern Slice 1 used for `_validate_interfaces`. The TODO anchor at `types/base.py:49-58` (the `DEFERRED_META_KEYS` block comment naming Slice 5's promotion) is untouched.

### Test additions / updates

All Slice 3 tests live in `tests/types/test_relay_interfaces.py`. The new section heading is added below the existing Slice 2 block (the existing file currently ends with `test_consumer_declared_is_type_of_is_preserved` at line 231-254 per inspection):

```
# ---------------------------------------------------------------------------
# Slice 3 — id suppression
# ---------------------------------------------------------------------------
```

The autouse `_isolate_registry` fixture at `tests/types/test_relay_interfaces.py:24-29` is reused (already in scope; pytest applies it module-wide). The `_meta(**attrs)` helper at lines 32-35 is reused where useful (the Slice 3 tests do not need it directly because they call `_build_annotations` with a synthetic `fields` tuple, but the import path is established).

**Test scaffolding pattern.** Slice 1 established the "call the helper directly as a unit" pattern because `"interfaces"` is in `DEFERRED_META_KEYS` and end-to-end `_validate_meta` calls with `Meta.interfaces` declared raise the deferred-key error first. Slice 3 follows the same pattern: the tests call `_build_annotations(...)` directly, passing the `interfaces` kwarg explicitly to simulate the post-validation tuple Slice 1 produces. This is the only viable route until Slice 5 promotes the key; both Slice 1's review and Slice 2's review confirmed this pattern is acceptable and the spec explicitly accommodates it via Decision 5 (spec lines 333-342) splitting suppression at collection-time from base injection at finalization-time.

Helper imports the test module needs (relative to `tests/types/test_relay_interfaces.py:14-21`):

- `from strawberry import relay` — already imported at line 15.
- `from apps.products.models import Category` — already imported at line 14. (Could also import `Item` for a second model, but `Category` suffices.)
- `from django_strawberry_framework.types.base import _build_annotations` — new import for Slice 3, parallel to the existing `from django_strawberry_framework.types.base import _validate_interfaces` at line 20.

Tests (each pinned to `tests/types/test_relay_interfaces.py::<test_name>`):

- `test_relay_node_strips_django_id_annotation` — the canonical spec test (spec line 481 / Slice 3 checklist line 39). Builds the `fields` tuple from `Category._meta.get_fields()` (just like `_select_fields` does for `Meta.fields = "__all__"`), constructs a throw-away host class (`class _Host: pass` — does not subclass `DjangoType` to avoid triggering `__init_subclass__`'s full pipeline, which would re-validate Meta and raise the deferred-key error), and calls `_build_annotations(_Host, fields, source_model=Category, interfaces=(relay.Node,))`. Asserts:

  - `"id" not in synthesized` — the primary-key annotation is absent from the synthesized dict.
  - Every other selected scalar still has an annotation present (`"name" in synthesized`, etc.) so the suppression is **only** at the pk, not at all scalars.
  - The returned `pending` list is unchanged from the `interfaces=()` baseline (suppression is annotation-only, not relation-handling).

  Assertion shape:

  ```python
  def test_relay_node_strips_django_id_annotation():
      fields = tuple(Category._meta.get_fields())

      class _Host:
          pass

      synthesized, pending = _build_annotations(
          _Host,
          fields,
          source_model=Category,
          interfaces=(relay.Node,),
      )
      assert "id" not in synthesized
      assert "name" in synthesized  # control: non-pk scalars are preserved
  ```

  The spec test plan line 481 says "`cls.__annotations__["id"]` is absent after finalization". The exact assertion shape there is "after the full collection pass". The plan's unit-level test asserts on the **return value** of `_build_annotations` (the `synthesized` dict that becomes `cls.__annotations__` via the merge at `types/base.py:142`). The two assertions are equivalent because `synthesized` is the **only** source of synthesized annotations for the pk — the merge `cls.__annotations__ = {**synthesized, **consumer_annotations}` only adds consumer annotations on top, and there is no consumer annotation for `id` in this test. The dispatcher prompt's note "`cls.__annotations__["id"]` is absent after `__init_subclass__` when `relay.Node` is declared" describes the end-state semantics; the unit-level test pins the immediate post-`_build_annotations` state, which is the same state on the no-consumer-shadow path.

- `test_non_relay_type_keeps_id_int` — the regression-guard control test (spec line 482 / Slice 3 checklist line 40). Same setup as `test_relay_node_strips_django_id_annotation` but with `interfaces=()` (the default). Asserts:

  - `"id" in synthesized` — the primary-key annotation is present.
  - The annotation's type is `int` (or `int | None` if the pk is nullable, which it never is for an `AutoField`, but the test is permissive and asserts `int` is the unwrapped origin). For an `AutoField` like `Category.id`, the synthesized annotation should be `int` per `0.0.4` behavior.

  Assertion shape:

  ```python
  def test_non_relay_type_keeps_id_int():
      fields = tuple(Category._meta.get_fields())

      class _Host:
          pass

      synthesized, pending = _build_annotations(
          _Host,
          fields,
          source_model=Category,
          interfaces=(),
      )
      assert "id" in synthesized
      assert synthesized["id"] is int
  ```

  Justification for asserting `synthesized["id"] is int` rather than `synthesized["id"] == int`: `convert_scalar` for `AutoField` returns the bare `int` type per spec line 118 ("every Django auto-id column produces a GraphQL `id: Int!`"). `is int` is the exact identity check and matches the existing `0.0.4` behavior. If Worker 2 finds that `convert_scalar` wraps the result (e.g. via `Annotated[int, ...]` for some Strawberry reason), the assertion should be relaxed to `typing.get_origin(...)` or similar; Worker 2 may tighten or relax this assertion based on what `convert_scalar` actually returns for `AutoField`. The substring-on-Failure shape of pytest's reporting will surface the actual type if the assertion fails.

**Optional supplementary test (worker-2 discretion).** A third test asserting that an non-pk scalar named `"id"` (hypothetically) is not affected would be defensive but is not in the spec's test plan; the plan covers it via the `pk_attname` decision in Implementation step 4 (Slice 3 suppresses only the actual primary-key field, not literal `field.name == "id"`). Worker 2 may add a third test that uses a model with a renamed pk (e.g. a `UUIDField(primary_key=True)`) to cover the non-default-pk case if such a model exists in the fakeshop fixtures. **Recommendation:** skip this test in Slice 3; defer to Slice 4 / 5 once the end-to-end path lights up via key promotion. The Slice 3 spec checklist (line 39-40) names exactly two tests; staying tight matches the slice's small footprint.

**Temp/scratch test candidates for Worker 3.** During review, Worker 3 may write a temp test under `docs/builder/temp-tests/slice-3-id_suppression/` that exercises the consumer-override interaction (Risk 7 in the DRY analysis): declare a `class _Host: __annotations__ = {"id": str}` and call `_build_annotations(_Host, fields, source_model=Category, interfaces=(relay.Node,))`, asserting that the consumer's `id: str` annotation survives the `cls.__annotations__ = {**synthesized, **consumer_annotations}` merge. The unit-level test only verifies the **return value** of `_build_annotations`; the full merge behavior is one layer up in `__init_subclass__`. The merge is unchanged by Slice 3 (Risk 7 documents that the consumer's annotation takes precedence via the existing merge at line 142), so the temp test would pin a behavior that lives outside `_build_annotations` itself. Worker 3 owns the decision on whether to keep this temp test or fold it into a permanent test once Slice 5 promotes the key and the end-to-end path is testable.

**Existing test impact.** Adding the new `interfaces: tuple[type, ...] = ()` kwarg with a default of `()` means existing callers of `_build_annotations` are unaffected. The only caller in `__init_subclass__` gains the explicit `interfaces=interfaces` kwarg, but the value is `()` for every test in `tests/` and `examples/fakeshop/tests/` that does not declare `Meta.interfaces` (which is every test today — `"interfaces"` is still in `DEFERRED_META_KEYS` so consumer test fixtures cannot declare it end-to-end). No existing test changes are required. The relation-conversion tests in `tests/types/test_base.py:462+` ("Slice 3 — relation conversion via _build_annotations" — note: that "Slice 3" naming is incidental from an earlier doc generation, not a reference to this build slice) continue to pass unchanged: they exercise `_build_annotations` indirectly via `DjangoType` subclass declaration, never declare `Meta.interfaces`, and the new kwarg's default is `()`.

### Open questions for Worker 2

1. **`pk_attname` derivation: `source_model._meta.pk.name` vs. `source_model._meta.pk.attname`.** Django distinguishes `name` (the Python attribute the model uses) from `attname` (the database column attribute on instances; for FKs, `attname` is `<name>_id`, but for non-FK pks, `name == attname`). For an `AutoField` primary key like `Category.id`, both `name` and `attname` are `"id"`. The plan uses `source_model._meta.pk.name` to match Django's "field name" convention (which is what `field.name` returns for entries in `fields`). Worker 2 must use **`name`** (not `attname`) so the comparison `field.name == pk_attname` works correctly. If Worker 2 finds a Django version edge case where `name != attname` for a non-FK pk and the wrong choice matters, Worker 2 should flag this back via "Notes for Worker 1 (spec reconciliation)" — but the plan's expectation is that `name` is correct.

2. **`relay.Node` import placement: `from strawberry import relay` vs. `from strawberry.relay import Node`.** The plan recommends `from strawberry import relay` (matching the spec's user-facing API at spec line 188 and the same spelling Slice 1's tests use at `tests/types/test_relay_interfaces.py:15`). The alternative `from strawberry.relay import Node` would let the suppression check read `Node in interfaces` instead of `relay.Node in interfaces`, which is one symbol shorter but couples the source to a less-canonical spelling. Worker 2 should keep `from strawberry import relay`.

3. **`suppress_pk_annotation` and `pk_attname` variable naming.** The plan's local variables are named `suppress_pk_annotation` (bool) and `pk_attname` (str). Worker 2 may shorten to `suppress_id` and `id_attname` (matching the spec's "id suppression" wording in the slice title) if that reads more naturally, or may inline the `relay.Node in interfaces` check directly inside the loop. The plan recommends the named-variable shape for readability and for keeping the once-per-function cost of the `_meta.pk.name` lookup outside the per-field loop. Worker 2 has discretion; the contract is "compute the decision once, apply per-field".

4. **Should Slice 3 add a `pytest.mark.skip` placeholder for any Slice 4 tests now?** No. Unlike Slice 1 (which staged `test_relay_node_with_composite_pk_raises` because that test name appeared under Slice 1's checklist), Slice 3's checklist (spec lines 35-40) names exactly two tests, both of which Slice 3 implements. No deferred-test placeholders are needed.

5. **Should the docstring update for `_build_annotations` cite spec lines or stay narrative?** The plan's recommended docstring update cites Decision 7 line 361 inline. Worker 2 may relax the spec-line reference to a narrative description ("the field stays in `fields` so the optimizer's field map continues to see it as a connector column") if the spec-line reference feels too tightly coupled to a doc that will eventually be archived. Either is acceptable; the existing helper docstrings in this file (e.g. `_validate_interfaces` at lines 286-308) cite spec lines, so for consistency the plan recommends keeping the cite.

6. **Does Slice 3 need to run the static inspection helper as part of the build?** Per `BUILD.md` "When to run the helper during build" — Worker 3 runs the helper because the slice touches `django_strawberry_framework/types/base.py` (under `types/`). Worker 2 may re-run with `--strip-docstrings` if the inline docstring update on `_build_annotations` makes the function harder to read. The plan flags this but does not require it; Worker 2 has discretion.

7. **What if `_meta.pk` is composite (Django 5.2+)?** Per the spec's Decision 2 line 287, composite primary keys are explicitly out of scope and Slice 4 enforces the composite-pk error at Phase 2.5 finalization. Slice 3's `source_model._meta.pk.name` lookup against a composite-pk model would either return a tuple-like name or raise an `AttributeError` depending on Django's internal representation. The plan does **not** add a defensive check here: Slice 4's composite-pk error fires before Slice 3's behavior matters end-to-end (collection time runs first, but suppression on a composite-pk model would only matter once `interfaces` is set, which requires `Meta.interfaces = (relay.Node,)`, which requires the `DEFERRED_META_KEYS` promotion in Slice 5 — by which time Slice 4's check already raises). Worker 2 should not add a composite-pk guard in Slice 3. If a Slice 3 test surprises us by reaching the `_meta.pk` access on a composite-pk model, Worker 2 flags it to Worker 1 via "Notes for Worker 1 (spec reconciliation)" and Worker 1 decides whether to add a defensive check or rely on Slice 4's gate.

---

## Build report (Worker 2)

### Files touched

- `django_strawberry_framework/types/base.py` — added `from strawberry import relay` next to the existing `from strawberry.types.field import StrawberryField` import (Implementation step 1). Added `interfaces: tuple[type, ...] = ()` kwarg to `_build_annotations` after `consumer_authored_fields` (Implementation step 2). Expanded the `_build_annotations` docstring with the new kwarg's contract and a function-level note that the pk annotation is dropped when `relay.Node` is among `interfaces` while the field map still sees the pk (Implementation step 3, citing spec Decision 7 line 361). Computed `suppress_pk_annotation = relay.Node in interfaces` and gated `pk_attname = source_model._meta.pk.name` behind it so non-Relay types do not incur the `_meta.pk.name` access (Implementation step 4). Added the `if suppress_pk_annotation and field.name == pk_attname: continue` branch in the scalar arm immediately before `convert_scalar`; replaced the three-line `# TODO(0.0.5 relay interfaces; ...)` anchor with a short comment naming spec Decision 7 (Implementation step 5). Threaded `interfaces=interfaces` through the single call site in `DjangoType.__init_subclass__` (Implementation step 6). No edits to `_select_fields`, `DjangoTypeDefinition` construction, `types/relay.py`, or `DEFERRED_META_KEYS` (Implementation steps 7-9).

- `tests/types/test_relay_interfaces.py` — extended the existing `from django_strawberry_framework.types.base import _validate_interfaces` import to also pull in `_build_annotations`. Appended a `# Slice 3 — id suppression` divider after `test_consumer_declared_is_type_of_is_preserved` and added the two tests below.

### Tests added or updated

- `tests/types/test_relay_interfaces.py::test_relay_node_strips_django_id_annotation` — pins spec Decision 2 (lines 278-285) at the `_build_annotations` unit boundary. Builds the `fields` tuple from `Category._meta.get_fields()`, calls `_build_annotations(_Host, fields, source_model=Category, interfaces=(relay.Node,))` with a bare `class _Host` (no `DjangoType` subclassing to avoid the deferred-key check), and asserts `"id" not in synthesized` plus `"name" in synthesized` as the non-pk control.
- `tests/types/test_relay_interfaces.py::test_non_relay_type_keeps_id_int` — regression guard for the `interfaces=()` default. Same setup, asserts `"id" in synthesized` and `synthesized["id"] is int`. The bare-`int` identity check is correct: `convert_scalar` walks `type(field).__mro__` for an `AutoField` pk, finds `SCALAR_MAP[models.AutoField] = int`, and returns `int` directly because `field.null` is `False` for an auto pk.

### Validation run

- `uv run ruff format .` — pass (91 files left unchanged). The standard `COM812`-vs-formatter warning is emitted as a notice; it is unchanged from prior slices and not a failure.
- `uv run ruff check --fix .` — pass ("All checks passed!"). No autofixes were needed.
- No `pytest` run (per `START.md` and `AGENTS.md`: Worker 2 runs formatting only).

### Notes for Worker 3

- The new branch lives inside the scalar arm of `_build_annotations`'s field loop, between the existing `consumer_authored_fields` short-circuit and the `convert_scalar(...)` call. The three-line TODO anchor that previously named this seam at the old `types/base.py:574-577` is gone in the same change (per `AGENTS.md` line 10).
- `suppress_pk_annotation` and `pk_attname` are computed once outside the field loop; `pk_attname` is gated to `None` on the non-Relay path so the `_meta.pk.name` access does not run for `0.0.4`-shape types. The per-field branch is a cheap pair of comparisons.
- `relay.Node` is imported at module scope (`from strawberry import relay`), not pulled from `types/relay.py`. The package's `types/relay.py` module is the Slice 2 / Slice 4 helper surface, not a re-export of `strawberry.relay`; mixing the two would couple the data flow.
- The four remaining `# TODO(0.0.5 relay interfaces; ...)` anchors in `django_strawberry_framework/types/relay.py:38-53` are untouched — those are Slice 4's surface.
- `"interfaces"` stays in `DEFERRED_META_KEYS` (no change). Slice 5 promotes it, so end-to-end `Meta.interfaces = (relay.Node,)` declarations still raise the deferred-key error at `_validate_meta` before reaching `_build_annotations`. The two new tests therefore exercise `_build_annotations` directly, matching Slice 1's unit-boundary testing approach.
- Static inspection helper was not re-run during the build pass. `scripts/review_inspect.py` is Worker 3's required pass for this slice (it touches `types/base.py`); Worker 3 runs it with `--output-dir docs/builder/shadow` per `BUILD.md`.
- No shadow file was used during implementation. No new module, no new function, no new constant. The change is +1 import, +1 kwarg, +1 branch in the scalar arm, +1 kwarg-pass at the call site, plus a docstring expansion.
- Risk 7 (consumer-authored `id` override interaction) is unchanged: the consumer's annotation lands via `cls.__annotations__ = {**synthesized, **consumer_annotations}` at `types/base.py:142`. Slice 3 only removes `id` from `synthesized`; the merge preserves consumer overrides. No extra guard added per the plan.

### Notes for Worker 1 (spec reconciliation)

No spec gaps surfaced. The plan named the exact insertion site (`_build_annotations` scalar arm, between the `consumer_authored_fields` short-circuit and the `convert_scalar` call); the spec's Decision 5 (lines 333-342) and Decision 7 (lines 352-361) already pin the collection-time vs. finalization-time split and the field-map invariant respectively. The implementation matches both without ambiguity. The TODO anchor removed in this change (formerly `types/base.py:574-577`) was the one the spec implicitly named at line 342 ("`__init_subclass__` collection ... inside `_build_annotations`"); its disappearance is intentional and tracked here per `AGENTS.md` line 10.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

#### Spec test-plan wording asserts on `cls.__annotations__` rather than `_build_annotations`'s return

Spec line 481 phrases the assertion as "`cls.__annotations__["id"]` is absent after finalization." Worker 2's `test_relay_node_strips_django_id_annotation` pins the equivalent state one layer earlier — the `synthesized` dict returned by `_build_annotations` — because `"interfaces"` is still in `DEFERRED_META_KEYS` and an end-to-end `DjangoType` subclass declaring `Meta.interfaces = (relay.Node,)` raises before reaching `_build_annotations`. The plan's "Test additions" subsection explicitly justifies the unit-level boundary (matches Slice 1's pattern for the same deferred-key reason), and the merge at `django_strawberry_framework/types/base.py:144` (`cls.__annotations__ = {**synthesized, **consumer_annotations}`) is the identity transform for the pk on the no-consumer-shadow path. The two assertions are therefore equivalent for the test's setup.

```django_strawberry_framework/types/base.py:144
cls.__annotations__ = {**synthesized, **consumer_annotations}
```

No change required in Slice 3. Worth a note for Worker 1: Slice 5 (after the key promotion) is the natural site to add a Strawberry-level end-to-end assertion that `cls.__annotations__["id"]` is absent and that the schema emits `id: GlobalID!`. The Slice 5 checklist (spec lines 83-102) does not currently call this out explicitly; the spec's "Schema-construction extensions" entries (`test_definition_order_schema.py`, spec lines 78-80) are scoped under Slice 4, which is closer to the right home. Worker 1 to weigh whether to add a one-line cross-reference in Slice 4 / 5 reminding the author to verify the end-state `cls.__annotations__` shape once the deferred key is promoted.

### DRY findings

- The validated `interfaces` tuple is the single source of truth. `__init_subclass__` captures the return of `_validate_meta` at `django_strawberry_framework/types/base.py:96` and threads it through to both `_build_annotations` (`base.py:122`) and `DjangoTypeDefinition(...)` (`base.py:139`) without re-reading `Meta` or `cls.__django_strawberry_definition__`. Slice 1's carry-forward ("`relay.Node in interfaces` check landing in `_build_annotations` should read the validated tuple, not `Meta`") is honored.
- The `relay.Node in interfaces` check appears exactly once in the package, inside `_build_annotations` at `base.py:569`. No duplication with `types/relay.py` (the Slice 2 / Slice 4 helper surface) and no preemption of Slice 4's `implements_relay_node` MRO-issubclass discriminator — that question is structurally different (tuple membership pre-base-injection vs. MRO post-base-injection) and is correctly left for Slice 4.
- The plan's "no new `"id"` string literal" rule is honored. The pk attname is read from `source_model._meta.pk.name` at `base.py:570`, and the comparison `field.name == pk_attname` at `base.py:596` is robust to non-default pk attnames (e.g. `UUIDField(primary_key=True)` named `uuid`). The shadow overview's `Repeated string literals` section reports `4x optimizer_hints`, `2x interfaces`, `2x description` — `"id"` is not introduced. No new repeated literal was added.
- The new `interfaces: tuple[type, ...] = ()` kwarg mirrors the existing `consumer_authored_fields: frozenset[str] = frozenset()` kwarg pattern (both default to the empty container so `0.0.4` callers see no change). The placement keeps Meta-derived state grouped together in the signature.
- The per-field cost is two cheap comparisons gated behind `suppress_pk_annotation` — `pk_attname = source_model._meta.pk.name if suppress_pk_annotation else None` at `base.py:570` means non-Relay types do not pay for the `_meta.pk.name` access. The decision is computed once outside the loop; the per-field check at `base.py:596` is `bool and str-eq`. Plan implementation step 4's gating intent is reflected verbatim.

### What looks solid

- Spec Decision 2 contract: pk annotation is dropped when `relay.Node` is in `interfaces`; pk field stays in `fields` so `field_map` (built at `base.py:100` from the full `fields` tuple) and `selected_fields=tuple(fields)` (at `base.py:131`) preserve the connector column. `DjangoTypeDefinition` construction is unchanged.
- Spec Decision 5 timing: suppression fires at collection time inside `_build_annotations`, exactly where `cls.__annotations__` is assembled. Base-injection and resolver-injection (Slice 4) remain at finalization time and are not preempted here.
- Spec Decision 7 invariant: `field_map`'s shape is independent of the Strawberry annotation suppression. `FieldMeta.from_django_field(f)` is called on every entry in `fields` regardless of `interfaces`.
- Boundary discipline: no `__bases__` mutation, no `resolve_*` defaults, no composite-pk check, no `"interfaces"` promotion, no doc edits. Only the targeted scalar-arm branch in `_build_annotations` and the import of `relay` were added. The four `# TODO(0.0.5 relay interfaces; ...)` anchors in `types/relay.py:38-53` (Slice 4) remain untouched.
- TODO-anchor hygiene: the three-line `# TODO(0.0.5 relay interfaces; ...)` block formerly at `types/base.py:574-577` is removed in the same change that ships the slice, per `AGENTS.md` line 10. The `DEFERRED_META_KEYS` block comment at `types/base.py:50-59` (which names Slice 5's promotion) is correctly left in place.
- Test scaffolding: both new tests follow Slice 1's unit-boundary pattern. The bare `class _Host: pass` host class is correct — subclassing `DjangoType` would trip `__init_subclass__`'s deferred-key check before reaching `_build_annotations`. The `_isolate_registry` autouse fixture (`tests/types/test_relay_interfaces.py:24-29`) carries through automatically. The new tests sit under a clear `Slice 3 — id suppression` divider.
- `synthesized["id"] is int` assertion: `convert_scalar` for `AutoField` (non-null pk) walks the `type(field).__mro__` lookup, finds `SCALAR_MAP[models.AutoField] = int` at `django_strawberry_framework/types/converters.py:50`, and returns bare `int` without `| None` widening. Identity check is correct.
- Coverage: both branches of the new logic are exercised. `test_relay_node_strips_django_id_annotation` covers the `suppress_pk_annotation=True` + `field.name == pk_attname` path (drop) and the `field.name != pk_attname` path (preserve "name"). `test_non_relay_type_keeps_id_int` covers `suppress_pk_annotation=False` (the gated `pk_attname = None` branch).

### Temp test verification

No temp tests were written. The Risk 7 consumer-override merge interaction described in the plan ("consumer's `id: str` annotation survives the merge at `base.py:144`") lives one layer above `_build_annotations` and is unchanged by this slice; the existing merge behavior is the implicit guarantor. Worker 3 chose not to introduce a temp test for it because the merge is not in Slice 3's diff, and a temp test that only proves un-changed merge behavior would not surface a defect in Slice 3.

### Static helper

Ran `python scripts/review_inspect.py django_strawberry_framework/types/base.py --output-dir docs/builder/shadow`. Shadow file at `docs/builder/shadow/django_strawberry_framework__types__base.overview.md`. Original source-file line numbers used throughout this review section. Findings from the overview:

- `Imports` section: `from strawberry import relay` is correctly grouped with the other Strawberry imports (alphabetical / module-level), not pulled from the package's local `.relay` module. No cross-folder import boundary issues.
- `Symbols` section: `_build_annotations` signature now reports the `interfaces` kwarg in the symbol summary.
- `Control-flow hotspots`: `_build_annotations` is reported at 84 lines / 9 branches — up from the pre-slice baseline by the +1 branch, +1 kwarg, +1 derive-once block. Still well under the 40-line / 8-branch thresholds for a "Medium-tier complexity" hotspot from the standpoint of this slice's added code (the existing function size is the pre-existing reason for hotspot listing; not a Slice 3 concern).
- `Repeated string literals`: no new repeats introduced (`"id"` is absent from the list, confirming the `pk_attname` approach).
- `Calls of interest`: no new reflective access introduced. `source_model._meta.pk.name` is a single attribute walk; it is not flagged.

### Coverage verification

Ran the focused command per BUILD.md:

```
uv run pytest tests/types/test_relay_interfaces.py --cov=django_strawberry_framework.types.base --cov-report=term-missing
```

Both new tests pass (`test_relay_node_strips_django_id_annotation`, `test_non_relay_type_keeps_id_int`). The coverage-failure line is the expected focused-run artifact (full package coverage isn't computed from a single test file). The missing lines reported for `types/base.py` (`574, 576, 587, 595`) are pre-existing relation-arm branches not in Slice 3's scope; the new suppression branch at `base.py:596-602` and the gated `pk_attname` derivation at `base.py:569-570` are exercised by both tests in combination. The full coverage gate runs in Worker 1's final pass; this focused command verified branch reachability for the slice's new code only.

### Notes for Worker 1 (spec reconciliation)

- The spec's test plan at line 481 phrases the assertion as `cls.__annotations__["id"]` at the post-finalization layer; Worker 2 asserts on the immediate `synthesized` return of `_build_annotations`. The two are equivalent on the no-consumer-shadow path used here. When Slice 5 promotes `"interfaces"` out of `DEFERRED_META_KEYS`, a Strawberry-level test that asserts on `cls.__annotations__` and on the emitted `id: GlobalID!` schema field is the natural follow-up. The Slice 4 test list under `tests/types/test_definition_order_schema.py` (spec lines 78-80, "Schema includes `Node` interface and `id: GlobalID!` on Relay-declared types") is the closer site. Worth a one-line cross-reference from Slice 4 / 5 to remind the author to verify the end-state `cls.__annotations__` shape once the deferred-key short-circuit is gone.
- Worth carrying into integration-pass DRY scan (Worker 1): Slice 3's `relay.Node in interfaces` (tuple membership, pre-base-injection) and Slice 4's planned `issubclass(cls, relay.Node)` (MRO check, post-base-injection) answer structurally different questions; the integration pass should confirm these two discriminators stay distinct and are not collapsed into a generic `implements_relay_node` helper. This is the same carry-forward pattern as Slice 2's `__dict__` membership vs. Slice 4's `__func__` identity discriminators.
- No spec edits requested. No spec contract violations observed.

### Review outcome

`review-accepted`. Every spec contract item (Decisions 2, 5, 7) is reflected in the diff; both spec-named tests are present, exercise their respective branches, and pass under focused pytest; the DRY pattern matches Slice 1's single-source-of-truth pin and avoids preempting Slice 4's `implements_relay_node`; no boundary leaks into Slice 4 / 5 territory; the only finding (Low) is a documentation-cross-reference suggestion that does not block this slice.

---

## Final verification (Worker 1)

- **Cross-slice DRY check across Slices 1, 2, and 3.** Confirmed clean.
  - `_validate_meta` (`django_strawberry_framework/types/base.py:363`) remains the single validator entry point. It calls `_validate_interfaces` (`base.py:405`) — the only Slice 1 validator — and returns the normalized `tuple[type, ...]`. No second validator entry point exists.
  - The validated interfaces tuple flows one-way: `_validate_meta` returns it (`base.py:363`) → `__init_subclass__` captures it at `base.py:96` (`interfaces = _validate_meta(meta)`) → it is threaded to both `DjangoTypeDefinition(interfaces=interfaces)` at `base.py:139` (Slice 1's storage) **and** to `_build_annotations(... interfaces=interfaces)` at `base.py:122` (Slice 3's new thread-through). One source, two consumers, no intermediate re-reads.
  - The three discriminators remain structurally distinct: Slice 2's `__dict__` membership check at `django_strawberry_framework/types/relay.py:28` (`"is_type_of" in type_cls.__dict__`) for the `is_type_of` virtual-subclass borrow; Slice 3's tuple-membership check at `base.py:569` (`relay.Node in interfaces`) for the collection-time `id` suppression; and Slice 4's reserved-but-not-yet-implemented `__func__` identity / `issubclass` discriminators (the TODO anchors at `types/relay.py:38-53` still flag those for Slice 4). The three answer structurally different questions (consumer-wrote-it-on-class vs. tuple-pre-base-injection vs. consumer-overrode-an-inherited-default-via-MRO), exactly as Worker 3 flagged and as the carry-forward from Slice 2 pinned. No premature consolidation has happened in Slice 3.
  - `relay.Node in interfaces` appears in exactly one site: `base.py:569`. `grep -rn "Node in interfaces"` across `django_strawberry_framework/` and `tests/` confirms zero duplication. The Slice 3 suppression check is not echoed in `types/relay.py`, in `types/finalizer.py`, or anywhere else.
  - Repeated-literal scan: no new `"id"` string literal introduced (Slice 3 reads `source_model._meta.pk.name` instead, robust to non-default pk attnames such as `UUIDField(primary_key=True)`). Shadow overview for `types/base.py` confirms `"id"` is absent from the "Repeated string literals" section.
- **Existing tests still pass (focused).** `uv run pytest tests/types/ --cov=django_strawberry_framework.types.base --cov=django_strawberry_framework.types.relay --cov-report=term-missing` reports `111 passed, 2 skipped` (skips: the Slice-4 composite-pk placeholder reserved by Slice 1, plus the pre-existing environment-tied skip). Slice 1's validation/storage tests, Slice 2's injection/consumer-preservation tests, and the two new Slice 3 tests (`test_relay_node_strips_django_id_annotation`, `test_non_relay_type_keeps_id_int`) all pass alongside the broader `tests/types/` suite. `types/relay.py` covers 100% (8/8). `types/base.py` covers 97% with missing-line residue at pre-existing sites only (`92, 432, 450-452`) — none of the missing lines are Slice 3 additions; the new branch at `base.py:596-602` and the gated `pk_attname` derivation at `base.py:569-570` are exercised by the two new tests in combination. The 76% total coverage failure printed by the focused command is the expected single-test-tree artifact (per Slice 1/2's final-verification memory), not a Slice 3 regression — the package-level `fail_under = 100` gate runs at build close.
- **Spec reconciliation.** No spec edit needed. Worker 2's "Notes for Worker 1 (spec reconciliation)" records no spec gaps; Worker 3's only Low finding is a cross-reference reminder — that once Slice 5 promotes `"interfaces"` out of `DEFERRED_META_KEYS`, Slice 4's `tests/types/test_definition_order_schema.py` entries (spec lines 78-80, "Schema includes `Node` interface and `id: GlobalID!` on Relay-declared types") are the natural site to verify the **end-state** `cls.__annotations__["id"]` is absent and the schema emits `id: GlobalID!`. This is a Slice 4 / Slice 5 carry-forward, not a Slice 3 spec gap: Slice 3's unit-level assertion on `_build_annotations`'s return value pins the immediate post-collection state on the no-consumer-shadow path, which is equivalent to the spec's `cls.__annotations__["id"]` post-finalization assertion (the merge at `base.py:144` is the identity transform on the pk in this path). The spec line 481 wording already correctly describes the end-state behavior; adding a Slice 3 spec edit to retroactively pin "unit-level vs. end-state" would over-constrain Slice 4 / 5's test sites without surfacing a real gap. Decision 2 / Decision 5 / Decision 7 governance is preserved bit-for-bit: pk annotation suppressed only when `relay.Node` is in `interfaces`, suppression fires at collection time inside `_build_annotations`, and `DjangoTypeDefinition.field_map` keeps every selected Django field including the pk so the optimizer's connector-column view is unchanged.
- **Final status.** `final-accepted`.

### Summary

Slice 3 lands the per-type `id` suppression as a minimal, surgical change: one new import (`from strawberry import relay`), one new kwarg on `_build_annotations` (`interfaces: tuple[type, ...] = ()`), one decision-at-the-top pair (`suppress_pk_annotation = relay.Node in interfaces`; `pk_attname = source_model._meta.pk.name if suppress_pk_annotation else None`), and one new branch in the scalar arm (`if suppress_pk_annotation and field.name == pk_attname: continue`). The validated `interfaces` tuple Slice 1 captures in `__init_subclass__` flows through to `_build_annotations` via the new kwarg — the single source of truth at `definition.interfaces` is honored, and `_build_annotations` never re-reads `Meta`. Reading `source_model._meta.pk.name` rather than hard-coding `"id"` means non-default primary-key attnames (e.g. `UUIDField(primary_key=True)` named `uuid`) are handled correctly without a new string literal. The TODO anchor at `types/base.py:574-577` is removed in the same change that ships the slice; the four Slice 4 anchors in `types/relay.py` and the Slice 5 promotion anchor in `types/base.py` are untouched. `DjangoTypeDefinition.field_map` and `selected_fields` are unchanged — the optimizer's connector-column view of the pk survives end-to-end (Decision 7). Two new tests in `tests/types/test_relay_interfaces.py` pin the contract at the `_build_annotations` unit boundary (the deferred-key short-circuit at `_validate_meta` is what keeps end-to-end Relay declarations from reaching the function until Slice 5 promotes the key): `test_relay_node_strips_django_id_annotation` asserts the pk is dropped when `interfaces=(relay.Node,)` while non-pk scalars (`name`) are preserved; `test_non_relay_type_keeps_id_int` is the regression guard for the `interfaces=()` default. The three discriminators across Slices 2, 3, and the reserved Slice 4 (`__dict__` membership, tuple membership, `__func__` identity) remain structurally distinct — no premature consolidation into a generic helper has happened, and the carry-forward to the integration pass is to confirm Slice 4 honors the same split.

### Spec changes made (Worker 1 only)

No spec edits.

### Final status

`final-accepted`.
