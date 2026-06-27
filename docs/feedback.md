# Review — `spec-039-serializer_mutations-0_0_13.md` (pass 2: GOAL.md + reference cross-reference)

Focused deep-dive cross-referencing the spec against [`GOAL.md`](../GOAL.md) (the north
star + the seven success criteria) and the working reference,
`django-graphene-filters` — including its `cookbook` (`recipes/schema.py`) and the
graphene-django `rest_framework` subpackage it leans on. Date: 2026-06-26.

(The prior pass verified the spec's "byte-identical reuse" claims against the package
source; that all checked out. This pass asks a different question: **does the serializer
flavor, as specced, actually land where GOAL.md and the reference point?**)

## Bottom line

The spec is **substantively aligned** with GOAL.md — it closes the one open piece of
success-criterion 6, and on relation handling it is *more* faithful to GOAL than the
reference itself. But the spec's **public surface contradicts GOAL.md's own
success-criterion-6 example on two axes** (the base class and `operation`), and the
Slice-4 GOAL.md edit doesn't reconcile them — so GOAL.md would be left depicting an API
that doesn't run. That reconciliation (P1) is the headline of this pass.

---

## Where the spec lands GOAL.md squarely (confirmed alignment)

These are not findings — they're the load-bearing alignments, recorded so the
divergences below are read in context.

- **It closes success-criterion 6.** GOAL.md line 511 is explicit: of the three named
  write flavors (`Input` / `ModelForm` / `ModelSerializer`), *"only the `ModelSerializer`
  (`0.0.13`) flavor still lands later."* This card is that flavor. Reusing the frozen
  `errors: list[FieldError]` envelope (verified byte-identical last pass) directly
  satisfies crit-6's *"one shared `errors` envelope across every flavor"*, and the
  `FileField` / `ImageField` → `Upload` mapping satisfies the crit-6 `Upload` clause.
- **It exceeds the reference on relation fidelity — and that serves a GOAL non-goal.**
  GOAL.md's non-goals (line 525) forbid *"a system that silently weakens rich relations
  into generic placeholders."* graphene-django's own converter does exactly that: it has
  **no** `PrimaryKeyRelatedField` registration, so related fields fall through the
  `serializers.Field → graphene.String` catch-all and degrade to bare strings
  (confirmed in `serializer_converter.py`). The spec's **fail-loud converter** with
  explicit `PrimaryKeyRelatedField → target GlobalID/raw-pk` and `ManyRelatedField →
  list[<id>]` mapping (Decision 7) is *strictly more faithful to GOAL than the upstream
  it borrows from*. Right call — and worth stating in the spec that diverging from
  graphene here is mandated by the GOAL non-goal, not just stylistic.
- **`get_queryset` covers reads *and* writes (crit 4).** Crit 4 wants *"the same hook
  covers reads and writes."* The spec routes both the `update` locate and the relation
  decode through `get_queryset` (the visibility hook), so the read-side rule governs the
  write path — a hidden row is not-found, a hidden relation target is a field error. The
  additive write-*authorization* layer (`DjangoModelPermission`, "can-view ≠ can-write",
  Decision 11) is GOAL's "layered permissions," not a contradiction. Clean alignment.
- **The example-app work matches GOAL's "Target examples."** GOAL line 533 says fakeshop
  should grow *"`ModelSerializer`-driven mutations; image-upload mutations."* Slice 3 adds
  `ItemSerializer` + serializer create/update to `products` and the multipart
  `Upload → Item.attachment` path. (Auth mutations, also listed there, are correctly the
  sibling `040` card.)

---

## P1 — The spec's surface contradicts GOAL.md's crit-6 example; reconcile it

GOAL.md's "Coming from DRF + `django-filter`" section is the canonical depiction of this
flavor. Its example (lines 490–494) is:

```python
# Coming in 0.0.13 — the DRF-serializer flavor on the same base:
class CreateCategoryFromSerializer(DjangoMutation):
    class Meta:
        serializer_class = CategorySerializer
```

The spec's user-facing API (Decision 3, lines 984–993) is instead:

```python
class CreateItemViaSerializer(SerializerMutation):
    class Meta:
        serializer_class = ItemSerializer
        operation = "create"
```

Two concrete divergences fall out, and **Slice 4's GOAL.md edit currently only says
"crit 6 now ships" — it does not touch this code sample**, so GOAL.md would keep
advertising a declaration that fails validation under the shipped package.

### (a) Base class: GOAL says `DjangoMutation` "on the same base"; the spec ships `SerializerMutation`

GOAL's comment is literal — *"on the same base"* — and the model-driven sibling right
above it (`CreateCategory(DjangoMutation)`, lines 484–487) reinforces that GOAL pictures
`DjangoMutation` as the universal base, with `model` vs `serializer_class` selecting the
flavor. The spec instead introduces a dedicated `SerializerMutation(DjangoMutation)` base
(consistent with the form flavor's `DjangoModelFormMutation`).

I think the spec's choice is the **right** one — and the reason is itself a GOAL
argument the spec doesn't make: crit 7 ("migrate … only the import line changes") names
**graphene-django** as a migration source, and a graphene-django consumer *already writes*
`class FooMutation(SerializerMutation): ...`. So exporting `SerializerMutation` lets that
declaration carry over **by name** — strictly better migration ergonomics than GOAL's
`DjangoMutation` shape. But the spec should:
1. Add this to Decision 6's alternatives (it currently weighs "standalone base" vs
   "subclass `DjangoMutation`" but never the GOAL-literal "`DjangoMutation` detects
   `serializer_class`" option — the one GOAL's example actually shows), and justify the
   `SerializerMutation` base partly on the graphene-django migration parity above; and
2. Make the **Slice-4 GOAL.md edit fix the example** to
   `class CreateCategoryFromSerializer(SerializerMutation):` so GOAL.md stops depicting a
   base that won't dispatch.

### (b) `operation`: GOAL omits it, graphene infers it; the spec mandates it

GOAL's serializer example has **no `operation`** key. The reference confirms why: graphene
uses **one** `SerializerMutation` with `model_operations = ["create", "update"]`,
dispatching create-vs-update purely on whether the lookup id is present in the input
(`mutation.py get_serializer_kwargs` — no per-mutation operation discriminator). The spec
rejects `model_operations` (Decision 10) and **requires** an explicit per-mutation
`operation ∈ {create, update}`.

This is a defensible, internally-consistent divergence (uniform with `DjangoMutation` /
`DjangoModelFormMutation`), and the spec *does* record `model_operations` / `lookup_field`
as deliberate non-adoptions in Risks. **But it is the real crit-7 friction point**, not the
base class: a graphene-django serializer-mutation migrant must now (i) add an `operation`
key their old code never had, and (ii) **split one auto-dispatching mutation into two**.
That's a declaration-shape change, not "only the import line changes." Recommend one of:
- **Default `operation = "create"`** when omitted (so GOAL's bare example works verbatim as
  a create, and the common case needs no key) — smallest, most GOAL-faithful fix; or
- keep it mandatory but (1) fix GOAL.md's example to include `operation = "create"`, and
  (2) elevate the Risks "accept `model_operations` as an alias that expands to per-operation
  mutations" fallback to a near-term ergonomic affordance for the graphene migrant.

Either way, GOAL.md and the spec must stop disagreeing in print.

---

## P2 — Reference-parity precision

### 3. "Cookbook parity" does not cover this card — say so

GOAL.md elevates the cookbook as the reference (the bare path at line 3; the "Cookbook
parity" criterion at line 534; "the full cookbook is the proof" at line 534). But
`recipes/schema.py` and the **entire** `django-graphene-filters` repo are **query/filter
-only — zero mutations of any kind** (confirmed by search). So the cookbook is the proof
target for the *read-side sidecars* (filters/orders/aggregates/fieldsets/search), and is
**orthogonal to serializer mutations**. The spec's Predecessors/borrowing sections
correctly point at graphene-django's `rest_framework/` subpackage as the real reference
for this flavor — good — but a one-line note that *the cookbook intentionally has no
mutation surface, so reference parity for this card is measured against graphene-django's
`rest_framework`, not the cookbook* would keep the GOAL narrative honest and forestall a
"why doesn't the cookbook port show this?" question later.

### 4. `get_serializer_kwargs` is a name-borrowed seam, not a signature-compatible one

The parity table calls `get_serializer_kwargs` a *"parity seam."* The name matches, but
the signatures don't: graphene is `get_serializer_kwargs(cls, root, info, **input)`; the
spec is `get_serializer_kwargs(info, *, data, instance=None)`. The spec's is cleaner, but
a graphene-django migrant who **overrides** this hook can't carry the override over
verbatim — another small crit-7 ("Meta mental model carries over") wrinkle. Worth a
sentence flagging the signature change so the parity claim isn't overread.

---

## P3 — Smaller GOAL-consistency notes

5. **The DRF migrant is the one migration that *keeps* the source package — frame it.**
   Crit 7's slogan is *"without bringing the source package along."* For graphene /
   strawberry-django you drop the runtime; for DRF you **keep** `djangorestframework`
   (the `ModelSerializer` is the reused validation engine — GOAL line 469's
   `CategorySerializer` is "no changes"). The spec's soft-dep design models this correctly,
   and GOAL line 496 already supports the framing (*"GraphQL becomes another transport for
   the same business logic"*). A sentence noting that the serializer flavor is the
   deliberate crit-7 exception — source package stays because it's the validation engine,
   not a GraphQL runtime to shed — keeps the migration story coherent.

6. **GOAL's example serializer implies exactly the input the spec produces — confirm it.**
   GOAL's `CategorySerializer(fields=("id","name"))` should yield
   `CategorySerializerInput { name: String! }` (the `id` read-only field dropped). That's
   precisely the spec's read-only-dropped behavior (Decision 7) — a nice consistency point
   to assert explicitly when the GOAL.md example is updated under (a)/(b), so the depicted
   schema and the generated schema visibly match.

---

## Closing

On GOAL substance the spec is on-target: it completes crit-6's three-flavor mutation story,
honors the shared-envelope and `Upload` clauses, keeps `get_queryset` governing reads and
writes (crit 4), and — notably — is *more* faithful to GOAL's "don't weaken relations"
non-goal than the graphene-django reference it borrows from. The gap is presentational but
real: **GOAL.md's crit-6 example and the spec's actual surface diverge on the base class and
on `operation`, and nothing in Slice 4 reconciles them.** Pick the surface (I'd keep
`SerializerMutation` for the graphene-django migrant, and either default `operation` or
require-and-document it), then make the Slice-4 GOAL.md edit update the example so the north
star and the shipped API tell the same story. Everything else here is precision around the
reference: the cookbook is read-only, so graphene-django's `rest_framework` — not the
cookbook — is the parity yardstick for this card.
