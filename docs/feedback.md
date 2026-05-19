# Review: `spec-015-consumer_overrides_scalar-0_0_6.md` (revision 5)

Reviewer: rigorous pass against the current on-disk tree (`django_strawberry_framework/types/base.py`, `types/definition.py`, `types/converters.py`, `tests/types/*.py`, `docs/FEATURES.md`, `KANBAN.md`).

**Headline:** the symmetric-collection contract (Decision 1 + Decision 2 + Decision 3) is sound and well-grounded in the on-disk code. The four-corner override matrix is the right shape. **Two concerns warrant attention before implementation begins**: one HIGH (a real correctness bug in the `_id_annotation_is_relay_node_id` fail-soft path that surfaces in mixed direct/stringified annotation classes), and one MEDIUM (the rev4 M1 assigned-`id` ban removes the only path consumers have to attach field-level GraphQL metadata to the Relay-supplied `id` field, with no acknowledged escape hatch). The rest is mostly nits — dead code in the pseudocode, minor wording inconsistencies, and Worker-1-picks-during-planning options that compound into ambiguity.

## H1 — fail-soft helper falsely rejects valid `relay.NodeID[int]` when an unrelated annotation fails to resolve

**Severity:** HIGH (false-positive rejection of the advertised escape hatch).

**Location:** Decision 7's `_id_annotation_is_relay_node_id` pseudocode at [spec-015:447-454](spec-015-consumer_overrides_scalar-0_0_6.md), and the corresponding prose at [:485](spec-015-consumer_overrides_scalar-0_0_6.md).

**Bug.** The fail-soft path assumes the `NameError` / `AttributeError` raised by `typing.get_type_hints(cls, include_extras=True)` originated from the `id` annotation. In reality, `get_type_hints` evaluates **every** annotation on `cls` (and walks the MRO). A single unresolved string annotation **anywhere on the class** trips the exception — even when the `id` annotation itself is a directly-resolved `relay.NodeID[int]` object. The fail-soft branch then inspects `cls.__annotations__["id"]`, finds it is the resolved `Annotated[int, NodeIDPrivate]` object (not a string), `isinstance(raw, str)` is False, and the helper returns False. The H1 guard then **rejects the valid escape hatch** with the "use `relay.NodeID[...]`" error — i.e., it tells the consumer to do exactly what they already did.

**Reproducer (confirmed locally with the on-disk `strawberry.relay`):**

```python
import typing
import strawberry.relay as r

class C:
    id: r.NodeID[int]            # directly resolved
    other: "MissingType"         # stringified, unresolved
try:
    typing.get_type_hints(C, include_extras=True)
except NameError as e:
    print("NameError:", e)                 # name 'MissingType' is not defined
    raw = C.__annotations__["id"]
    print("raw:", raw)                     # typing.Annotated[int, <NodeIDPrivate>]
    print("isinstance(raw, str):", isinstance(raw, str))   # False
```

A consumer who declares `id: relay.NodeID[int]` on a Relay-Node-shaped `DjangoType` alongside any forward-referenced relation annotation (a common case — e.g., `items: list["AdminItemType"]`) hits the bug. The rev5 fail-soft window is described as "the consumer wrote a NodeID-shaped **string** that does not resolve" but the scoping predicate (`isinstance(raw, str) and "NodeID[" in raw`) silently rejects every directly-resolved object, regardless of whether it is a valid `NodeID` marker.

**Fix (minimum).** In the fail-soft branch, fall back to the resolved-object inspection path when `raw` is not a string:

```python
def _id_annotation_is_relay_node_id(cls):
    try:
        hints = typing.get_type_hints(cls, include_extras=True)
    except (NameError, AttributeError):
        raw = cls.__annotations__.get("id")
        if isinstance(raw, str):
            return "NodeID[" in raw
        return _has_node_id_marker(raw)   # raw is the already-resolved annotation
    id_hint = hints.get("id")
    if id_hint is None:
        return False
    return _has_node_id_marker(id_hint)
```

**Test coverage gap.** The rev5 Slice 1 cluster pins `test_consumer_id_unresolved_non_nodeid_string_on_relay_node_type_raises` and `test_consumer_id_string_relay_nodeid_annotation_on_relay_node_type_is_accepted`, but does **not** pin the failure-mode above: a directly-resolved `id: relay.NodeID[int]` alongside an unrelated unresolved annotation. Add one accept test, e.g. `test_consumer_id_resolved_relay_nodeid_with_unresolved_sibling_annotation_is_accepted`, that declares both `id: relay.NodeID[int]` (direct) and `items: "AdminItemType"` (forward) on a Relay-Node-shaped type and asserts class creation succeeds. Without this test, the H1 bug ships silently.

## M1 — rev4 M1's blanket assigned-`id` ban removes the only field-metadata path for the Relay-supplied `id`

**Severity:** MEDIUM (intentional behavior reduction with no documented escape).

**Location:** Decision 7's assigned-side reject branch at [spec-015:398-405](spec-015-consumer_overrides_scalar-0_0_6.md), the test `test_consumer_id_assigned_strawberry_field_on_relay_node_type_raises` at [:76](spec-015-consumer_overrides_scalar-0_0_6.md), and the `Changed` CHANGELOG entry at [:188](spec-015-consumer_overrides_scalar-0_0_6.md).

**Gap.** The spec's two named alternatives for the assigned-`id` ban are:

- `@classmethod resolve_id` — Strawberry's hook for **custom id resolution**.
- `id: relay.NodeID[<pk_type>]` — annotation for **custom pk source / id shape**.

Neither route attaches **GraphQL field-level metadata** (`description=`, `deprecation_reason=`, `directives=`) to the `id` field. Today (pre-spec), a consumer can write `id = strawberry.field(description="Stable per-row identifier")` — Strawberry accepts it because the field type matches `Node.id: ID!`. Post-spec, that pattern raises `ConfigurationError` and the consumer is told to use `resolve_id` (which is a method, not field metadata) or `relay.NodeID[<pk_type>]` (which also has no `description=` slot).

Two paths forward:

1. **Acknowledge the loss explicitly.** Update the assigned-side error message to point at a workaround — e.g., redefine as a sibling field (`display_id: ID`) carrying the description, and leave the Relay-supplied `id` undecorated. Add a sentence to the `Scalar field override semantics` FEATURES.md entry (Slice 5) noting that field-level metadata on the Relay-supplied `id` is not configurable in `0.0.6` and the workaround is a sibling field. This is the smaller-touch path.
2. **Loosen the ban.** Inspect the assigned `StrawberryField`'s `base_resolver` and `type_annotation` — accept assignments that have no resolver (metadata-only) or whose resolver returns `relay.GlobalID` / `strawberry.ID`. Reject only resolver overrides returning a non-`ID`-compatible type. This preserves the metadata route at the cost of guard complexity.

Rev4 M1's stated rationale ("consistency with the annotation-side guard's framing") is real, but the annotation-side guard has an escape hatch (`relay.NodeID[...]`) and the assigned-side guard does not. The asymmetry should be either closed or named.

## M2 — dead `and` clause in the Decision 7 pseudocode

**Severity:** MEDIUM-LOW (misleading; readers may infer both predicates are load-bearing).

**Location:** Decision 7 pseudocode at [spec-015:414-423](spec-015-consumer_overrides_scalar-0_0_6.md):

```python
if has_id_annotation or has_id_assignment:
    if has_id_assignment:
        raise ConfigurationError(...)   # returns
    if has_id_annotation and _id_annotation_is_relay_node_id(cls):
        pass
    else:
        raise ConfigurationError(...)
```

By the time control reaches the second `if`, the assigned-branch has already raised — so `has_id_assignment` is `False` and (since the outer guard's `or` required at least one) `has_id_annotation` must be `True`. The `has_id_annotation and` conjunction is dead. Trim to `if _id_annotation_is_relay_node_id(cls): pass else: raise ...`, or drop the conditional entirely and inline the rejection path.

This is cosmetic but Worker 1 will copy the pseudocode mechanically; carrying dead predicates into production code adds drift surface.

## M3 — `id: None` corner case is mis-described in rev4 M2

**Severity:** MEDIUM-LOW (the fix is correct; the rationale is wrong).

**Location:** Revision-history entry rev4 M2 at [spec-015:25](spec-015-consumer_overrides_scalar-0_0_6.md) and Decision 7's `has_id_annotation = "id" in cls.__annotations__` comment at [:388](spec-015-consumer_overrides_scalar-0_0_6.md).

**Issue.** The rev4 M2 entry claims `cls.__annotations__["id"]` is "literally `None`" for `id: None`. Python's annotation grammar evaluates `None` to the `NoneType` class object (`type(None)`), not the literal `None` value. `cls.__annotations__["id"] is None` is `False` for an `id: None` annotation; it is the class `<class 'NoneType'>`. The actual case where `cls.__annotations__["id"] is None` would be `id: None = None` with a default — and that's an assignment, caught by the assigned branch.

The **fix** the spec lands (use `"id" in cls.__annotations__` for key-presence) is still correct — there are legitimately other corner cases (deferred string evaluation, manually-set `__annotations__`) where value-truthiness is the wrong predicate. But the **rationale** rev4 M2 names is mechanically inaccurate. Suggest rewriting to: "Use key-presence rather than value-truthiness so any consumer-authored `id` annotation (including unusual ones like `id: None`, `id: Literal[None]`, or strings that evaluate to false-y types) is detected at class-creation time."

## M4 — inheritance gap: inherited `id` annotation slips past the guard

**Severity:** MEDIUM-LOW (contract gap; no test pinning intended behavior).

**Location:** Edge-cases section at [spec-015:540](spec-015-consumer_overrides_scalar-0_0_6.md).

The spec correctly notes that inherited annotations on a base class are not in `cls.__annotations__` (matching the existing relation-annotation behavior). For Decision 7's H1 guard, this means: a `class BaseDjangoType(DjangoType): id: int` (or any non-`NodeID` annotation) followed by `class ChildDjangoType(BaseDjangoType): class Meta: model = Foo; interfaces = (relay.Node,)` slips past `"id" in cls.__annotations__` on the **child**, the H1 guard does not fire, and Strawberry's downstream `ValueError` at `strawberry.Schema(...)` is exactly the failure mode H1 exists to replace. The base's `__init_subclass__` also won't fire the guard if `BaseDjangoType` has no `Meta`.

The spec's call ("matches the existing per-subclass declaration contract") is reasonable, but the corner case should be (a) explicitly named in the FEATURES.md `Scalar field override semantics` entry and (b) pinned by one test asserting the documented behavior, e.g., `test_inherited_id_annotation_on_relay_node_subclass_is_not_caught_by_guard` — the assertion would be that **Strawberry's** `ValueError` is the (acknowledged) failure mode in this corner. Without the test, future code changes to the guard could accidentally start walking the MRO and the spec wouldn't catch the regression.

## L1 — Worker-1-picks-during-planning options compound into ambiguity

**Severity:** LOW.

The spec defers four micro-decisions to "Worker 1 picks during planning":

1. M2 placement for `test_annotation_override_of_arrayfield_with_nested_array_is_allowed` ([:73](spec-015-consumer_overrides_scalar-0_0_6.md)) — `tests/types/test_converters.py` vs. `tests/types/test_definition_order.py`.
2. Recipe for `test_consumer_non_id_scalar_override_on_relay_node_type_is_accepted` ([:80](spec-015-consumer_overrides_scalar-0_0_6.md)) — `description: int` vs. monkeypatched `code = CharField(primary_key=True)`.
3. Recipe for `test_consumer_id_string_relay_nodeid_annotation_on_relay_node_type_is_accepted` ([:79](spec-015-consumer_overrides_scalar-0_0_6.md)) — explicit string annotation vs. test-module `from __future__ import annotations`.
4. Skipped-test resolution in Slice 2 ([:83](spec-015-consumer_overrides_scalar-0_0_6.md)) — delete vs. unskip-and-keep as smoke test.

Each individually is fine; collectively they multiply the implementation surface. Recommend taking a definitive stance in each case (the spec already names recommendations — promote them to defaults rather than options). The "spec is neutral on the wording polish" instances should similarly be either prescribed or removed.

## L2 — `+95/-1` Slice 1 line-delta estimate appears too low

**Severity:** LOW (estimate drift; not a correctness issue).

The implementation-plan table at [:527](spec-015-consumer_overrides_scalar-0_0_6.md) lists `+95/-1` for Slice 1, claiming 13 tests + the `_id_annotation_is_relay_node_id` helper + new comprehension + new dataclass field. A realistic count:

- New comprehension in `__init_subclass__`: ~4 lines.
- Plumb-through to `DjangoTypeDefinition` call site: ~1 line.
- New `DjangoTypeDefinition` field + line re-order: ~5 lines.
- H1 Relay guard inline in `__init_subclass__`: ~25-30 lines (predicate + two raise branches + comments).
- `_id_annotation_is_relay_node_id` helper + `_has_node_id_marker` helper: ~30-40 lines (with the rev5 fail-soft, plus the H1-fix branch this review recommends).
- 13 tests at ~10-15 lines each: ~130-180 lines.

Production: ~65-80. Tests: ~130-180. Total: ~195-260. The `+95/-1` estimate looks like an unrevised carryover from a smaller-scoped earlier revision. The summary paragraph at [:533](spec-015-consumer_overrides_scalar-0_0_6.md) reads "~170 lines added" which is closer but still likely low after the H1-fix tweak. Recommend re-estimating in a final pass; if the worker is using the table as a sanity-check threshold, the current number invites premature alarm.

## L3 — Revision-history overload obscures the actual decisions

**Severity:** LOW (presentation).

The five-revision iterative review pass is genuinely useful — it surfaced H1 (Relay guard), H2 (converter-bypass contract), rev3's pk-name vs. GraphQL-name narrowing, rev4's class-creation-time vs. finalize-time question, and rev5's fail-soft scoping. But the revision-history block now spans [:9-31](spec-015-consumer_overrides_scalar-0_0_6.md) (23 lines of dense rationale), and each subsequent section carries inline rev-N callouts ("rev4 M1", "rev5 M1", "rev4 H1 …") that interleave with the actual contract. A reader new to the card has to parse the debate transcript to extract the decision.

Recommend a final compaction pass before implementation begins: collapse the rev-history to a 5-line summary (one line per revision: the highest-severity issue resolved), and remove the inline rev-N callouts from Decision/checklist text. The detail belongs in git history or an appendix; the spec body should read as a clean design doc. (This is taste — but the spec already runs 590 lines and is, in places, harder to read than the underlying code.)

## L4 — Decision 7a's choice-enum cache behavior change has no dedicated test

**Severity:** LOW (test gap).

Decision 7a at [:509](spec-015-consumer_overrides_scalar-0_0_6.md) names a real cross-type behavior change: "Two `DjangoType`s on the same model where one overrides and one does not will get the fresh enum from the non-overriding type alone; pre-spec they would have shared whichever loaded first." This is a behavior change that the `test_annotation_override_of_grouped_choices_field_is_allowed` test pins **only** in the single-type case (it asserts `registry.get_enum(model, "status")` is `None` after one overriding type).

A cross-type test isn't in the cluster. Two-type scenarios are common in `DjangoType` usage (the whole `Meta.primary` shipped card is about this). Recommend adding `test_annotation_override_does_not_populate_shared_enum_cache_for_co_resident_types`: declare two `DjangoType`s on the same model with the same `choices=` field, one with an override annotation and one without, and assert that `registry.get_enum(model, field_name)` returns the enum generated by the non-overriding type (and that the overriding type's introspected GraphQL field uses the consumer's annotation, not the cached enum). This pins the bypass at the cache-interaction layer, not just the call-site layer.

## L5 — Cross-references to `FEATURES.md:386-388` and the `_introspect_field_type` line are stable but worth pinning

**Severity:** LOW (verification).

Spot-checked the on-disk tree:

- `FEATURES.md` line 386-388 — "Current alpha constraints" list. Today the list has one bullet (relation cardinality validation deferral). Slice 5's check ("verify nothing scalar-shaped is in there to drop") is accurate. ✓
- `tests/types/test_converters.py:434` for `_introspect_field_type` — confirmed. ✓
- `tests/types/test_converters.py:1021` for the nested-array rejection — the actual `test_array_field_multidim_rejected_via_fake_sentinel` test is near line 1020-1037. ✓
- `tests/types/test_relay_interfaces.py:240` for `test_composite_pk_with_explicit_node_id_annotation_is_accepted` — confirmed. ✓
- `types/base.py:609` for the `suppress_pk_annotation` predicate — confirmed (the H1 guard reuses this `any(issubclass(i, relay.Node) for i in interfaces) or issubclass(cls, relay.Node)` shape, which is the right move). ✓
- `types/base.py:472` for `_select_fields` — confirmed. ✓

Most line numbers will drift slightly after Slice 1 lands (the new comprehension shifts subsequent code down). The spec already names "(post-Slice-1)" in several pseudocode blocks; recommend a final pass naming "(pre-Slice-1)" for every line-number reference that names current state, so post-implementation readers can match against the right snapshot.

## L6 — Two minor wording inconsistencies in the rev5 KANBAN body

**Severity:** LOW (cosmetic).

The verbatim KANBAN body at [:108-182](spec-015-consumer_overrides_scalar-0_0_6.md) mixes tense:

- "`DjangoType.__init_subclass__` collects ..." (present, describes shipped contract)
- "The previously-skipped `test_consumer_annotation_overrides_synthesized` lands as ..." (present, describes implementation action)
- "100% coverage across `tests/types/test_definition_order.py` ..." (post-action present)

Strawberry's `WIP-ALPHA-XXX → DONE-XXX` convention treats KANBAN entries as past-tense "shipped" descriptions. Recommend a sweep to past-tense ("collected", "landed", "covers") for consistency with the rest of `KANBAN.md`'s `DONE-*` entries. Worker 1 will copy this verbatim; the inconsistency lands in `KANBAN.md`.

## Strengths worth preserving

To balance the criticism — the spec gets a lot right and the review-driven evolution shows:

- **Symmetric four-corner matrix** (Decision 1 + 3) is the right shape. The two-comprehension form at [:281-283](spec-015-consumer_overrides_scalar-0_0_6.md) keeps the code parallel to the existing relation-collection one line above; the bucket-loop alternative would have lost that symmetry.
- **Decision 7a's explicit converter-bypass contract** is a meaningful design call that previous revisions of the spec missed (it was rev2's H2 fix). The framing — "override is escape, not augmentation" — captures the contract cleanly, and aligning with the existing relation-annotation override path's `convert_relation` bypass is the right consistency argument.
- **H1 guard's narrowing** (rev3 — key off GraphQL field name `"id"`, not the model's pk name) is a careful precision call. Without it, the guard would have rejected non-`id` primary-key overrides (`code: str` on a `code = CharField(primary_key=True)` model) — a corner case rev2 missed.
- **`typing.get_type_hints(cls, include_extras=True)` over raw `typing.get_args`** (rev4 H1) is correct. The PEP 563 / `from __future__ import annotations` interaction is real and the rev1/rev2 approach would have rejected the documented escape hatch in stringified form.
- **Explicit Choice-enum cache behavior change** (Decision 7a, [:509](spec-015-consumer_overrides_scalar-0_0_6.md)) — flagging this rather than burying it is the right call, even if (per L4) the test cluster doesn't pin it directly.
- **Slice 4's explicit "verify by grep before editing"** clause for the version-bump quintet handles the multi-card-per-version concurrency cleanly.

## Recommended next steps

In priority order:

1. **Fix H1** before any worker starts implementing. The fix is a four-line change in `_id_annotation_is_relay_node_id` plus one new accept test. Without it the headline escape hatch fails for a realistic class shape.
2. **Resolve M1** — either acknowledge the metadata-route loss in the FEATURES.md update + assigned-side error message, or loosen the ban to allow metadata-only assignments. Pick one and commit.
3. **Pseudocode hygiene** — trim the dead `and` in Decision 7, rewrite the rev4 M2 rationale, and (optional) compact the revision-history.
4. **Test cluster** — add the H1-fix accept test (`...with_unresolved_sibling_annotation...`), the inheritance edge-case test from M4, and the L4 cross-type enum-cache test. New total: 16, not 13.
5. **Final estimate pass** — re-estimate Slice 1's `+95/-1` line delta with the H1-fix code and the additional tests; today's number looks low by ~100 lines.
6. **Worker-1 micro-decisions** — promote the recommended option in each "Worker 1 picks" branch to the default, and demote the alternatives to "if there's a good reason, …". Stop running options.

The headline shape of the card is right and the code-side changes are small. The bulk of the risk is in the H1 guard's detection helper and the assigned-`id` ban's UX surface; nailing those two before Worker 1 starts will keep the implementation pass clean.
