# Review — `docs/spec-036-mutations-0_0_11.md` (mutations foundation)

Reviewer pass: 2026-06-17. Rigorous review of the `DjangoMutation` write-side foundation spec, verified against the live checkout (`products/models.py`, `list_field.py`, `connection.py`, `utils/typing.py`, `registry.py`, `types/finalizer.py`), the board (`KANBAN.md`), Django 5.2 `full_clean()` semantics, **`GOAL.md` (north star)**, and the **`django-graphene-filters` cookbook `recipes/schema.py`** (the GOAL's stated working reference). Suite not run (no-pytest-after-edits rule); design/correctness review of the plan.

## Verdict

Strong, well-structured spec — version boundary and downstream-card assignments are **correct** against the re-sequenced KANBAN, the async-helper names it cites are **real and used as described**, the G2-handoff discharge is sound, and it handles the card's own stale citations gracefully. The borrowing posture is exactly right.

The `GOAL.md` + cookbook cross-reference **did not overturn any finding — it reinforced three and added one** (Medium-5). The single substantive *correction* is to **Medium-1**: `GOAL.md` success-criterion 4 ("the same hook covers reads **and writes**") means my earlier "re-fetch without visibility" recommendation is not a free choice — it's a genuine tension the spec must own. Details below.

## GOAL.md + cookbook cross-reference (what changed)

- **The cookbook is read-only — no mutation precedent.** `recipes/schema.py` has object-type nodes + filter/order/aggregate/fieldset/search/cascade sidecars and a `Query`, but **no `Mutation`, no form/serializer mutation, no `ErrorType`**. So "cookbook parity" (GOAL.md "Target examples") is a **read-side** goal; the mutation card draws parity from `strawberry-graphql-django` + `graphene-django`'s `rest_framework`/`forms` modules, exactly as the spec's Borrowing posture states. **No cookbook mutation pattern was missed or contradicted** — confirmed, not a finding.
- **GOAL success-criterion 6 + 7 confirm the spec's frame.** Crit-6 ("write mutations declaratively from `ModelForm`, `ModelSerializer`, or auto-generated `Input` types — one shared `errors: list[FieldError]` envelope across every flavor") is exactly the freeze-the-envelope + model-driven-foundation move the spec makes. The spec is on-mission.
- **Reinforcement (Major-1).** GOAL's north-star `Galaxy`/`CelestialBody` models use the *identical* `description = TextField(blank=True, default="")` and `is_private = BooleanField(default=False)` shape as products `Item`. The over-strict "every editable field required" rule would wrongly force `description`/`isPrivate` required on the **canonical north-star app**, not just products — so Major-1 is pervasive, not a fakeshop quirk.
- **Reinforcement + concrete case (Medium-4).** The cookbook's `ValueNode` deliberately **excludes `description` from its read `fields`** ("not included for permissions testing"), and GOAL's nodes use `fields = "__all__"` (which includes read-only `created_date`/`updated_date`). Both make the read-selection-≠-write-input gap concrete: a write input must *exclude* read-only fields the read type *includes*, and may need to *include* an editable field (`description`) the read type *excludes*. The spec's "input derives from the primary `DjangoType` field selection" can't be taken literally.
- **Correction (Medium-1).** GOAL crit-4 ("the same hook covers reads and writes") + the cookbook's `get_queryset` (which filters `is_private=False` for non-privileged users) make the create-an-invisible-row paradox concrete and non-trivial — see revised Medium-1.
- **New (Medium-5).** GOAL's only shown mutation surface — `class CreateCategory(DjangoMutation): class Meta: serializer_class = CategorySerializer` — has **no `Meta.model`**. The spec's foundation hard-requires `Meta.model`. Forward-compat seam, see Medium-5.
- **Major-3 is unconstrained by GOAL.** GOAL never shows the `DjangoMutationField` / `<Mutation>.Payload` exposure surface (its mutation example is just the class). So switching the showcase to the workable surface violates nothing in GOAL — it's the spec's own invention to get right.

## Major-1 — "every editable field required" is too coarse; the example SDL is wrong (reinforced by GOAL)

**Where:** Decision 6 ("`<Model>Input` — every **editable** field required"); the User-facing API SDL.

`products/models.py::Item` has `description = TextField(blank=True, default="")` and `is_private = BooleanField(default=False)`; **GOAL's `Galaxy`/`CelestialBody` use the identical shape.** The spec's headline `ItemInput` renders both required:

```graphql
input ItemInput {
  name: String!
  description: String!   # WRONG — blank=True, default="" → should be optional
  categoryId: GlobalID!
  isPrivate: Boolean!    # WRONG — default=False → should be optional
}
```

A client creating an `Item` would be forced to send `description`/`isPrivate` even though Django supplies both — over-strict and divergent from DRF (`required=False` from `default`/`blank`/`null`) and strawberry-django. The headline example demonstrates the bug, and because the *north-star* models share the shape, an `astronomy`-app port would hit it too.

**Fix:** required only when no `default`, not `null=True`, and (text fields) not `blank=True`; else optional even in the create `Input`. Update the SDL to `description: String` / `isPrivate: Boolean`. (`PartialInput` already all-optional.) `name`/`categoryId` stay required — correctly, because they have no default and are non-null.

## Major-2 — the unique-constraint create error is a `full_clean()` `ValidationError`, not an `IntegrityError`

**Where:** Decision 8 step 3 ("catches `IntegrityError` and maps it to the constraint's fields"); Edge cases ("a duplicate `(category, name)` create raises `IntegrityError` at `save()`").

`Item`'s uniqueness is a named `UniqueConstraint` in `Meta.constraints`; floor is `Django>=5.2`. `Model.full_clean()` → `validate_unique()` validates `Meta.constraints` `UniqueConstraint`s (since 4.1), so on the spec's own pipeline (step 3 `full_clean()` *before* step 4 `save()`) a duplicate is caught as a **`ValidationError`** with clean field mapping — never reaching `save()`/`IntegrityError` on the normal path. `IntegrityError` only fires on a concurrent race.

**Threefold:** (1) mechanism mis-described (clean error is from `validate_unique`, not `IntegrityError` parsing); (2) `IntegrityError`→field mapping is backend-specific/fragile; (3) **100% coverage trap** — the Slice 4 live "unique-constraint error envelope" test exercises the `ValidationError` path, leaving the `IntegrityError` branch uncovered → `fail_under = 100` forces a mocked-`save()` race or the branch shouldn't exist.

**Fix:** make `full_clean()`/`validate_unique()` the primary unique path (clean `ValidationError` → envelope); treat `IntegrityError` as a documented best-effort **race fallback** (covered via a mocked `save()`, with a backend-dependence note). Fix the edge-case wording.

## Major-3 — the headline `CreateItem.Payload` annotation can't exist when `class Mutation` is imported

**Where:** User-facing API (`create_item: CreateItem.Payload = DjangoMutationField(CreateItem)`); Decision 12 (payload materialized at finalization phase 2.5); Risks (acknowledged).

`@strawberry.type class Mutation` runs at import and evaluates annotations eagerly, but `<Name>Payload` is materialized at `finalize_django_types()` phase 2.5 (later). So `CreateItem.Payload` is not a concrete attribute when `create_item: CreateItem.Payload` is evaluated → `AttributeError` at import. Unlike `DjangoConnection[GenreType]` (references a class that exists at import), this references a generated attribute that genuinely can't exist at class-creation (the payload wraps a `DjangoType` that may not be finalized — definition-order independence). The spec flags this only in Risks; the **showcase** depends on the branch the spec says may be unworkable. **GOAL does not show this exposure surface at all**, so the spec is free to pick the workable one.

**Fix:** resolve in a Decision, not Risks. Either (a) the metaclass installs `CreateItem.Payload` at class-creation as a `strawberry.lazy`/forward-ref placeholder that resolves at schema build (show that), or (b) commit to a `.field()` classmethod accessor (`create_item = CreateItem.field()`) in the showcase. Pin before Slice 1 — input/payload timing depends on it.

## Medium-1 — post-write re-fetch visibility (corrected: GOAL crit-4 makes this a real tension)

Decision 10 routes the **update/delete lookup** through `get_queryset` (correct, no-leak). Decision 9's **post-write re-fetch** is silent on whether it also passes through `get_queryset`.

The cross-reference sharpens this into a genuine tension, not a free choice:
- **GOAL success-criterion 4** says "row, field, and cascade permissions … the **same hook covers reads and writes**" — which argues the re-fetch *should* run through `get_queryset` for consistency.
- But the cookbook/GOAL/products `get_queryset` filters `is_private=False` for non-privileged users. With **no create authorization in `0.0.11`** (Decision 10 / Risks defer it), a non-staff caller can create an `is_private=True` row; re-fetching it through `get_queryset` returns **nothing → a null payload object after a successful write**. So "same hook covers writes" + "no create gate" produces a confusing success-with-null-object.

**Fix (pin explicitly):** decide and document the post-write re-fetch visibility. The defensible resolution: re-fetch the just-written row **by pk without the visibility filter** (the actor created/updated it; round-tripping their own write is not an existence leak) — but note this is a *deliberate exception* to GOAL crit-4's "same hook covers writes," and say so, because the literal reading of crit-4 would null the payload. Either way it's a security/UX boundary the spec currently leaves open.

## Medium-2 — the delete payload can't be "planned against the in-memory snapshot"

Decision 8 step 5 / Edge cases: delete returns the pre-delete snapshot and "the response selection is **planned** against the in-memory snapshot." The optimizer plans *querysets*, not single instances. The located row (step 2, `get_queryset(...).get(pk=...)`) carries **no** response-selection relations, so a delete payload selecting a relation (`deleteItem { item { category { name } } }`) lazy-loads per relation (N+1) after `delete()`, or fails if the related row is also cascade-deleted. **Fix:** either optimizer-re-fetch the row *with* its response-selection relations *before* `delete()` (then delete, then return the loaded snapshot), or document that delete-payload relation selections lazy-load and aren't planned. The current wording describes something mechanically impossible.

## Medium-3 — partial-update `full_clean()` scope

Decision 8 step 3 calls `full_clean()` on update; for a `PartialInput` it validates the **whole** instance, surfacing `FieldError`s on fields the client never sent (DRF's `partial=True` validates only provided fields). Pin: validate-whole-instance (stricter, can surprise) vs `full_clean(exclude=<unprovided>)` (DRF-aligned). Interacts with the `UNSET`/`null`/value tri-state.

## Medium-4 — input field set vs the `DjangoType` selection (reinforced + made concrete)

Decision 6 says the input derives from "`Meta.model` and the model's primary `DjangoType` field selection," and Slice 2/Decision 5 add optional `Meta.fields`/`exclude` on the **mutation**. The cross-reference shows the read-selection and the write-input set genuinely differ in **both directions**:
- **Read includes, write must exclude:** GOAL/cookbook use `fields = "__all__"`, which includes read-only `created_date`/`updated_date` (`auto_now`/`editable=False`) — those must never be in the write input.
- **Read excludes, write may include:** the cookbook's `ValueNode` deliberately omits `description` from its read `fields`; `description` is an editable column. Should the write input expose `description` (editable model field) or hide it (follow the read selection)? Hiding it makes the field unwritable through GraphQL; exposing it lets a write surface set a column the read surface hides.

**Fix:** pin the input field set precisely — is it (a) all editable model fields, (b) editable ∩ the `DjangoType` selection, or (c) editable ∩ the mutation's own `Meta.fields`/`exclude`? — and resolve the read-hides/write-exposes case (Medium-4's sharpest edge). "Derives from the `DjangoType` field selection" cannot be taken literally given read-only fields are in that selection.

## Medium-5 — foundation requires `Meta.model`, but GOAL's serializer-flavor mutation omits it (NEW, forward-compat)

GOAL's only shown mutation surface is `class CreateCategory(DjangoMutation): class Meta: serializer_class = CategorySerializer` — **no `Meta.model`** (the model comes from the serializer's own `Meta.model`). The spec's foundation (Decision 5/Slice 2) hard-requires `Meta.model` (`missing model → ConfigurationError`), and the form (`038`) / serializer (`039`) flavors **subclass this base** (Decision 2 / Borrowing posture) and inherit its metaclass validation. So the foundation's `model`-required rule, as written, would reject GOAL's canonical serializer-flavor declaration.

**Fix:** design the base `Meta` validation so a flavor subclass can supply the model differently — require `Meta.model` **only when** no `serializer_class`/`form_class` is present (or let the flavor derive and inject `model` before the base validates). Flag it now as a forward-compat seam so `039` doesn't have to re-open the base's metaclass. (The spec freezes the `FieldError` envelope for the flavors; it should equally ensure the `Meta`-validation contract doesn't paint them into a corner.)

## Minor

- **`input_class` validation wording.** "not a **registered** input → `ConfigurationError`" — a consumer's hand-written `input_class` isn't "registered" anywhere; state the real criterion (a `@strawberry.input`-decorated type) and unify with "generated-input-compatible Strawberry input."
- **"module-for-module" overstatement.** `mutations/` (`inputs/sets/resolvers/fields`) is a four-module split *in the spirit* of `filters/`/`orders/` (`base/factories/inputs/sets`), not module-for-module identical.
- **README roadmap drift (Slice 5 watch-out).** The spec correctly follows the re-sequenced KANBAN (form `038-0.0.12`, DRF `039-0.0.13`, auth `040-0.0.13`), but `README.md` still says "Mutations are on the roadmap (`0.0.11`) … including a DRF-serializer flavor" and lumps form/DRF/auth into `0.0.11`. Slice 5's README edit must reconcile that drift.
- **Auth card number.** Risks reads "DRF-serializer / **auth** (`039`, `0.0.13`)," but auth is `040-0.0.13`; `039` is DRF-serializer. Version right, card number conflated. Trivial.

## Verified accurate (checked, no action)

- **Cookbook has no mutations** — `recipes/schema.py` is read-only, so the spec sources mutation parity correctly (strawberry-django / graphene-django), and "cookbook parity" (GOAL Target examples) is a read-side goal the mutation card doesn't touch.
- **GOAL success-criteria 6/7 alignment** — the FieldError-across-flavors + auto-generated-Input + migrate-from-four-stacks criteria are exactly what the freeze-the-envelope + model-driven foundation rests on.
- **Version boundary + downstream-card versions** match KANBAN (`038-0.0.12`, `039-0.0.13`, `040-0.0.13`; 036/037 share the `0.0.11` joint cut).
- **Async-helper names** — `utils/typing.py::is_async_callable` (construction-time) + `strawberry.utils.inspect.in_async_context` (runtime) are exactly the `list_field.py` asymmetry; Decision 8 is precise.
- **G2 handoff discharge** is real (spec-035's Slice 2 hands it forward) and Slice 4 discharges it correctly.
- **Permission composition / no-existence-leak** (Decision 10) and **primary-type resolution** (Decision 11, `registry.get(model)`) match shipped contracts; the cookbook/GOAL `get_queryset` shape is the one the update/delete lookup composes with.
- **No `DEFERRED_META_KEYS` change** (Decision 12) is correct.
- **Card-citation handling** — the spec catches and resolves the card's stale `031/032/033` envelope-reuser typo.

## Bottom line

Build-ready once the three Majors are folded in (Major-1 required-ness vs defaults — visible in the example SDL *and* the north-star models; Major-2 unique via `full_clean`, not `IntegrityError`; Major-3 payload-annotation timing — move the showcase to the workable surface) and the five Mediums are pinned (re-fetch visibility *with the GOAL crit-4 tension owned*; delete-payload relations; partial `full_clean` scope; input-field-set vs read-selection; and the new Medium-5 forward-compat so the `039`/`038` serializer/form flavors can omit `Meta.model`). The cross-reference confirms the spec is on-mission against GOAL and invents no surface the cookbook contradicts; the gaps are about *what the generator emits* and *what the resolver does at the edges* — the right things to nail before the flavor cards subclass this base.
